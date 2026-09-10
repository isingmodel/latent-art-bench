"""Bounded concurrent collection, append-only evidence, and offline measurement."""

from __future__ import annotations

import argparse
import base64
import concurrent.futures as futures
import datetime as dt
import gzip
import hashlib
import io
import json
import subprocess
import time
from pathlib import Path

import httpx
import numpy as np
from PIL import Image

from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_feature_generation_v2 import features

from . import study as s


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def append(path, row):
    with Path(path).open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()


def freeze():
    paths = [
        s.ROOT / "studies" / s.NS / "PROTOCOL.md",
        s.REF,
        s.SCALER,
        s.ACQUISITIONS,
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        Path(features.__file__),
        s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/statistics.py",
        s.ROOT / "src/latent_art_bench/painter_distribution_study_v1/discovery.py",
        s.DATA.parent / "accounting_baseline.json",
        s.DATA.parent / "provider_quotes.json",
    ]
    paths += sorted(Path(__file__).parent.glob("*.py"))
    paths += sorted((s.ROOT / "tests" / s.NS).glob("*.py"))
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *[str(p) for p in paths]], cwd=s.ROOT, text=True
    )
    if dirty.strip():
        raise ValueError("commit study inputs before freezing")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=s.ROOT, text=True).strip()
    items = s.assignments()
    s.DATA.mkdir(parents=True, exist_ok=True)
    with (s.DATA / "requests.jsonl").open("x") as stream:
        for r in items:
            stream.write(json.dumps(r, sort_keys=True) + "\n")
    paths.append(s.DATA / "requests.jsonl")
    s.write_new(
        s.DATA / "freeze.json",
        dict(
            run_id=s.RUN,
            recorded_git_commit=commit,
            created_at=now(),
            inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths],
            models=list(s.MODELS),
            maximum_images=1152,
            maximum_retries=24,
            concurrency=3,
            spacing_seconds=5,
            baseline_usd=s.BASELINE,
            ceiling_usd=s.CEILING,
            adapter_commit="d0a390f",
            local_endpoint=s.LOCAL_URL,
        ),
    )
    print("Frozen 1,152 exact requests")


def verify():
    frozen = s.read(s.DATA / "freeze.json")
    for item in frozen["inputs"]:
        if s.sha(s.ROOT / item["path"]) != item["sha256"]:
            raise ValueError("frozen input changed: " + item["path"])
    return frozen


def budget(events):
    """Each paid attempt stays reserved until a known charge settles it."""
    amounts, settled = {}, set()
    for e in events:
        key = e["id"], e["attempt"]
        if e["kind"] == "start":
            if key in amounts:
                raise ValueError("duplicate attempt")
            amounts[key] = s.RESERVE if e["paid"] else 0.0
        elif e["kind"] == "end":
            if key not in amounts or key in settled:
                raise ValueError("end without unique intent")
            settled.add(key)
            if e["cost_usd"] is not None:
                if not np.isfinite(e["cost_usd"]) or e["cost_usd"] < 0:
                    raise ValueError("invalid charge")
                amounts[key] = e["cost_usd"]
    return s.BASELINE + sum(amounts.values())


def inspect(body):
    value = json.loads(body)
    data = value.get("data", [])
    if len(data) != 1 or not isinstance(data[0].get("b64_json"), str):
        raise ValueError("expected one inline base64 image")
    raw = base64.b64decode(data[0]["b64_json"], validate=True)
    with Image.open(io.BytesIO(raw)) as im:
        if im.width * im.height > 20_000_000 or min(im.size) < 512:
            raise ValueError("unsupported image geometry")
        im.verify()
        shape = im.size
    return raw, dict(
        image_sha256=hashlib.sha256(raw).hexdigest(),
        width=shape[0],
        height=shape[1],
        reported={k: value.get(k) for k in ("model", "size", "quality", "output_format")},
    )


def post(request, attempt, key):
    paid = request["model"] in s.PROVIDERS
    result = dict(
        kind="end",
        id=request["id"],
        attempt=attempt,
        paid=paid,
        cost_usd=None if paid else 0.0,
        status=None,
        success=False,
        retryable=False,
    )
    path = s.WORK / "responses" / f"{request['id']}-a{attempt}.json.gz"
    body = b""
    try:
        headers = {"Authorization": "Bearer " + key} if paid else {}
        with httpx.Client(timeout=600, follow_redirects=False, trust_env=False) as client:
            with client.stream(
                "POST",
                s.PAID_URL if paid else s.LOCAL_URL,
                json=request["payload"],
                headers=headers,
            ) as response:
                result["status"] = response.status_code
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 64 * 1024**2:
                        raise ValueError("response exceeds 64 MiB")
                    chunks.append(chunk)
                body = b"".join(chunks)
        with path.open("xb") as stream:
            stream.write(gzip.compress(body, mtime=0))
        result.update(
            response_path=str(path.relative_to(s.ROOT)),
            response_sha256=hashlib.sha256(body).hexdigest(),
        )
        data = json.loads(body)
        if paid:
            cost = (data.get("usage") or {}).get("cost")
            if type(cost) in (int, float) and np.isfinite(cost) and cost >= 0:
                result["cost_usd"] = float(cost)
            elif result["status"] in (400, 401, 402, 403, 404, 422, 429) and data.get("error"):
                result["cost_usd"] = 0.0
        if result["status"] == 200:
            raw, metadata = inspect(body)
            reported = metadata["reported"]["model"]
            if reported is not None and reported != request["model"]:
                raise ValueError("returned model differs from request")
            image_path = s.WORK / "images" / f"{request['id']}.png"
            with image_path.open("xb") as stream:
                stream.write(raw)
            result.update(success=True, image_path=str(image_path.relative_to(s.ROOT)), **metadata)
        else:
            result["retryable"] = result["status"] in (429, 500, 502, 503, 504)
            error = data.get("error") or {}
            result["error_code"] = error.get("code") if isinstance(error, dict) else None
            if result["error_code"] in (
                "content_policy_violation",
                "moderation_blocked",
                "safety_violation",
                "image_generation_user_error",
                "invalid_prompt",
            ):
                result["retryable"] = False
    except httpx.TransportError as exc:
        result.update(error_type=type(exc).__name__, retryable=True)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc)[:200])
    result["ended_at"] = now()
    return result


def collect():
    verify()
    if (s.DATA / "collection.json").exists():
        raise ValueError("terminal collection is closed")
    s.WORK.mkdir(parents=True, exist_ok=True)
    lock = s.WORK / "collector.lock"
    with lock.open("x") as stream:
        stream.write(now())
    try:
        _collect()
    finally:
        lock.unlink()


def _collect():
    for name in ("images", "responses"):
        (s.WORK / name).mkdir(exist_ok=True)
    ledger = s.DATA / "attempts.jsonl"
    events = s.rows(ledger) if ledger.exists() else []
    starts = {(e["id"], e["attempt"]) for e in events if e["kind"] == "start"}
    ends = {(e["id"], e["attempt"]) for e in events if e["kind"] == "end"}
    if starts != ends:
        raise ValueError("unsettled attempt after crash: diagnose before resuming")
    requests = s.rows(s.DATA / "requests.jsonl")
    last = {e["id"]: e for e in events if e["kind"] == "end"}
    todo = []
    for r in requests:
        old = last.get(r["id"])
        if old is None:
            todo.append((r, 1, 0.0))
        elif not old["success"] and old["retryable"] and old["attempt"] < 3:
            todo.append((r, old["attempt"] + 1, 0.0))
    key = key_from_env(s.ROOT)
    last_start = 0.0
    consecutive_errors = 0
    paused = None
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        while todo or pending:
            ready = [f for f in pending if f.done()]
            for future in ready:
                request, attempt = pending.pop(future)
                end = future.result()
                append(ledger, end)
                events.append(end)
                last[request["id"]] = end
                consecutive_errors = consecutive_errors + 1 if end["retryable"] else 0
                if end["retryable"] and consecutive_errors >= 3:
                    paused = "three consecutive technical failures; diagnosis required"
                if (
                    end["status"] in (401, 402, 403, 404)
                    or end.get("diagnostic")
                    or (end["cost_usd"] or 0) > s.RESERVE
                ):
                    paused = "request or response contract requires diagnosis"
                retries = sum(e["kind"] == "start" and e["attempt"] > 1 for e in events)
                if end["retryable"] and attempt < 3 and retries < 24:
                    todo.append(
                        (request, attempt + 1, time.monotonic() + (20 if attempt == 1 else 60))
                    )
                if len(last) % 36 == 0 or not end["success"]:
                    print(
                        json.dumps(
                            dict(
                                completed_slots=len(last),
                                successful=sum(e["success"] for e in last.values()),
                                accounted_usd=round(budget(events), 6),
                                last_status=end["status"],
                                paused=paused,
                            )
                        ),
                        flush=True,
                    )
            if paused:
                if pending:
                    time.sleep(0.2)
                    continue
                print(paused, flush=True)
                return
            if todo and len(pending) < 3 and time.monotonic() - last_start >= 5:
                eligible = [
                    i for i, (_, _, ready_at) in enumerate(todo) if ready_at <= time.monotonic()
                ]
                if eligible:
                    index = eligible[0]
                    r, attempt, _ = todo[index]
                    paid = r["model"] in s.PROVIDERS
                    # Pending liabilities already appear in the durable ledger.
                    if paid and budget(events) + s.RESERVE >= s.CEILING:
                        if pending:
                            time.sleep(0.2)
                            continue
                        paused = "spending admission stopped; diagnosis required"
                        continue
                    if (
                        attempt > 1
                        and sum(e["kind"] == "start" and e["attempt"] > 1 for e in events) >= 24
                    ):
                        todo.pop(index)
                        continue
                    todo.pop(index)
                    start = dict(
                        kind="start",
                        id=r["id"],
                        attempt=attempt,
                        paid=paid,
                        started_at=now(),
                        payload_sha256=hashlib.sha256(
                            json.dumps(r["payload"], sort_keys=True).encode()
                        ).hexdigest(),
                    )
                    append(ledger, start)
                    events.append(start)
                    pending[pool.submit(post, r, attempt, key)] = r, attempt
                    last_start = time.monotonic()
            time.sleep(0.2)
    s.write_new(
        s.DATA / "collection.json",
        dict(
            ended_at=now(),
            planned=len(requests),
            successful=sum(e["success"] for e in last.values()),
            attempts=sum(e["kind"] == "start" for e in events),
            accounted_usd=budget(events),
            ledger_sha256=s.sha(ledger),
            outcomes=[
                dict(id=r["id"], **{k: v for k, v in last[r["id"]].items() if k != "id"})
                for r in requests
            ],
            freeze_sha256=s.sha(s.DATA / "freeze.json"),
        ),
    )
    print("Collection terminal; no further requests allowed", flush=True)


def measure_one(item):
    row = dict(id=item["id"])
    if not item["success"]:
        return dict(**row, status="unavailable")
    path = s.ROOT / item["image_path"]
    if s.sha(path) != item["image_sha256"]:
        raise ValueError("image changed before measurement")
    try:
        norm = features.normalize(path, short_side=512)
        vector = features.extract(norm.rgb)
        if vector.shape != (31,) or not np.isfinite(vector).all():
            raise ValueError("invalid feature vector")
        height, width = norm.rgb.shape[:2]
        top, left = (height - 512) // 2, (width - 512) // 2
        square = features.extract(norm.rgb[top : top + 512, left : left + 512])
        return dict(
            **row,
            status="measured",
            values=vector.tolist(),
            square_values=square.tolist(),
            image_sha256=item["image_sha256"],
            normalization=norm.metadata,
        )
    except (ValueError, OSError) as exc:
        return dict(**row, status="failed", error_type=type(exc).__name__)


def measure():
    verify()
    receipt = s.read(s.DATA / "collection.json")
    if s.sha(s.DATA / "attempts.jsonl") != receipt["ledger_sha256"]:
        raise ValueError("terminal ledger changed")
    path = s.DATA / "measurements.jsonl"
    with path.open("x") as stream, futures.ProcessPoolExecutor(max_workers=4) as pool:
        for row in pool.map(measure_one, receipt["outcomes"]):
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    references = {r["work_id"]: r for r in s.rows(s.ACQUISITIONS)}
    items = []
    for r in s.rows(s.REF):
        original = references[r["image_id"]]
        if original["raw_sha256"] != r["raw_sha256"]:
            raise ValueError("reference image ancestry differs")
        items.append(
            dict(
                id=r["image_id"],
                success=True,
                image_path=original["raw_path"],
                image_sha256=r["raw_sha256"],
            )
        )
    with (
        (s.DATA / "reference_windows.jsonl").open("x") as stream,
        futures.ProcessPoolExecutor(max_workers=4) as pool,
    ):
        for row, old in zip(pool.map(measure_one, items), s.rows(s.REF)):
            if row["status"] == "measured" and not np.allclose(
                row["values"], old["values"], atol=1e-10, rtol=1e-10
            ):
                raise ValueError("reference primary feature re-extraction differs")
            row["painter_id"] = old["painter_id"]
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    s.write_new(
        s.DATA / "measurement_receipt.json",
        dict(
            collection_sha256=s.sha(s.DATA / "collection.json"),
            measurements_sha256=s.sha(s.DATA / "measurements.jsonl"),
            reference_windows_sha256=s.sha(s.DATA / "reference_windows.jsonl"),
            generated_rows=len(receipt["outcomes"]),
            reference_rows=len(items),
            ended_at=now(),
        ),
    )
    print("Measurement complete")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("freeze", "collect", "measure", "verify"))
    args = parser.parse_args()
    globals()[args.action]()


if __name__ == "__main__":
    main()
