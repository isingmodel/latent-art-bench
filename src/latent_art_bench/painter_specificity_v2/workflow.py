"""Explicit paid routing with staggered dispatch and graceful diagnostic pauses."""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import gzip
import hashlib
import json
import signal
import subprocess
import time

import httpx
import numpy as np

from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_specificity_v1.workflow import append, inspect, measure_one, now

from . import study as s


def freeze():
    paths = [
        s.ROOT / "studies" / s.NS / "PROTOCOL.md",
        s.ROOT / "studies/painter_specificity_v1/PROTOCOL.md",
        s.ROOT / "studies" / s.NS / "DECISION.md",
        s.REF,
        s.SCALER,
        s.ACQUISITIONS,
        s.DATA.parent / "pilot.jsonl",
        s.DATA.parent / "medium_cost_pilots.jsonl",
        s.DATA.parent.parent / "painter_specificity_v1/provider_quotes.json",
        s.DATA.parent.parent / "painter_specificity_v1/openai_provider_quotes.json",
        s.DATA.parent.parent / "painter_specificity_v1/psv1-20260910/collection.json",
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
    ]
    for namespace in (s.NS, "painter_specificity_v1"):
        paths += sorted((s.ROOT / "src/latent_art_bench" / namespace).glob("*.py"))
        paths += sorted((s.ROOT / "tests" / namespace).glob("*.py"))
    paths += [
        s.ROOT / "src/latent_art_bench" / p
        for p in (
            "painter_feature_generation_v2/features.py",
            "painter_feature_generation_v2/statistics.py",
            "painter_distribution_study_v1/discovery.py",
        )
    ]
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *map(str, paths)], cwd=s.ROOT, text=True
    )
    if dirty.strip():
        raise ValueError("commit inputs before freeze")
    prior = s.read(s.DATA.parent.parent / "painter_specificity_v1/psv1-20260910/collection.json")
    pilots = s.rows(s.DATA.parent / "pilot.jsonl")
    if len(pilots) != 4 or any(r["status"] != 200 for r in pilots):
        raise ValueError("four explicit OpenAI qualification requests required")
    medium = s.rows(s.DATA.parent / "medium_cost_pilots.jsonl")
    if len(medium) != 4 or any(r["status"] != 200 for r in medium):
        raise ValueError("four medium-quality cost probes required")
    baseline = prior["accounted_usd"] + sum(r["cost_usd"] for r in pilots + medium)
    if abs(baseline - s.BASELINE) > 1e-10:
        raise ValueError("accounting baseline changed")
    items = s.assignments()
    s.DATA.mkdir(parents=True, exist_ok=True)
    with (s.DATA / "requests.jsonl").open("x") as stream:
        for r in items:
            stream.write(json.dumps(r, sort_keys=True) + "\n")
    paths.append(s.DATA / "requests.jsonl")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=s.ROOT, text=True).strip()
    s.write_new(
        s.DATA / "freeze.json",
        dict(
            recorded_git_commit=commit,
            created_at=now(),
            run_id=s.RUN,
            baseline_usd=s.BASELINE,
            predecessor_sha256=s.sha(
                s.DATA.parent.parent / "painter_specificity_v1/psv1-20260910/collection.json"
            ),
            inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths],
        ),
    )
    print("Frozen 1,008 requests on explicit model routes")


def verify():
    for record in s.read(s.DATA / "freeze.json")["inputs"]:
        if s.sha(s.ROOT / record["path"]) != record["sha256"]:
            raise ValueError("frozen input changed: " + record["path"])


def post(r, attempt, key):
    result = dict(
        kind="end",
        id=r["id"],
        attempt=attempt,
        status=None,
        success=False,
        retryable=False,
        cost_usd=None,
    )
    path = s.WORK / "responses" / f"{r['id']}-a{attempt}.json.gz"
    try:
        with httpx.Client(timeout=600, follow_redirects=False, trust_env=False) as client:
            with client.stream(
                "POST", s.URL, json=r["payload"], headers={"Authorization": "Bearer " + key}
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
        value = json.loads(body)
        cost = (value.get("usage") or {}).get("cost")
        if type(cost) in (int, float) and np.isfinite(cost) and cost >= 0:
            result["cost_usd"] = float(cost)
        elif result["status"] in (400, 401, 402, 403, 404, 422, 429) and value.get("error"):
            result["cost_usd"] = 0.0
        if result["status"] == 200:
            raw, metadata = inspect(body)
            model = metadata["reported"]["model"]
            if model is not None and model != r["payload"]["model"]:
                raise ValueError("reported model differs from exact request")
            image_path = s.WORK / "images" / f"{r['id']}.png"
            with image_path.open("xb") as stream:
                stream.write(raw)
            result.update(success=True, image_path=str(image_path.relative_to(s.ROOT)), **metadata)
        else:
            error = value.get("error") or {}
            result["error_code"] = error.get("code") if isinstance(error, dict) else None
            result["retryable"] = result["status"] in (429, 500, 502, 503, 504) and (
                result["error_code"]
                not in (
                    "content_policy_violation",
                    "moderation_blocked",
                    "safety_violation",
                    "image_generation_user_error",
                    "invalid_prompt",
                )
            )
    except httpx.TransportError as exc:
        result.update(retryable=True, error_type=type(exc).__name__)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc)[:200])
    result["ended_at"] = now()
    return result


def collect():
    verify()
    if (s.DATA / "collection.json").exists():
        raise ValueError("terminal collection cannot restart")
    s.WORK.mkdir(parents=True, exist_ok=True)
    lock = s.WORK / "collector.lock"
    with lock.open("x") as stream:
        stream.write(now())
    stopped = []
    previous = signal.signal(signal.SIGINT, lambda *_: stopped.append("operator pause"))
    try:
        collect_loop(stopped)
    finally:
        signal.signal(signal.SIGINT, previous)
        lock.unlink()


def collect_loop(stopped):
    for name in ("responses", "images"):
        (s.WORK / name).mkdir(exist_ok=True)
    ledger = s.DATA / "attempts.jsonl"
    events = s.rows(ledger) if ledger.exists() else []
    starts = {(e["id"], e["attempt"]) for e in events if e["kind"] == "start"}
    ends = {(e["id"], e["attempt"]) for e in events if e["kind"] == "end"}
    if starts != ends:
        raise ValueError("unsettled crash intent; inspect before resuming")
    all_requests = s.rows(s.DATA / "requests.jsonl")
    last = {e["id"]: e for e in events if e["kind"] == "end"}
    todo = []
    for r in all_requests:
        e = last.get(r["id"])
        if e is None:
            todo.append((r, 1, 0))
        elif e["retryable"] and not e["success"] and e["attempt"] < 3:
            todo.append((r, e["attempt"] + 1, 0))
    key, last_start, errors = key_from_env(s.ROOT), 0, 0
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        while todo or pending:
            for future in [f for f in pending if f.done()]:
                r, attempt = pending.pop(future)
                e = future.result()
                append(ledger, e)
                events.append(e)
                last[r["id"]] = e
                errors = errors + 1 if e["retryable"] else 0
                if (
                    errors >= 3
                    or e.get("diagnostic")
                    or e["status"] in (400, 401, 402, 403, 404, 422)
                ):
                    stopped.append("technical diagnosis required")
                if e["cost_usd"] is None or e["cost_usd"] > s.RESERVE:
                    stopped.append("unknown/excess charge requires diagnosis")
                retries = sum(e["kind"] == "start" and e["attempt"] > 1 for e in events)
                if e["retryable"] and attempt < 3 and retries < 24:
                    todo.append((r, attempt + 1, time.monotonic() + (20 if attempt == 1 else 60)))
                if len(last) % 72 == 0 or not e["success"]:
                    print(
                        json.dumps(
                            dict(
                                slots=len(last),
                                images=sum(e["success"] for e in last.values()),
                                accounted_usd=round(s.accounted(events), 6),
                            )
                        ),
                        flush=True,
                    )
            if (s.WORK / "pause_requested").exists():
                stopped.append("operator pause file")
            if stopped:
                if pending:
                    time.sleep(0.2)
                    continue
                append(
                    s.DATA / "operator_events.jsonl", dict(kind="pause", at=now(), reasons=stopped)
                )
                print("Paused after draining all active requests", flush=True)
                return
            if todo and len(pending) < 3 and time.monotonic() - last_start >= 5:
                ready = [i for i, (_, _, at) in enumerate(todo) if at <= time.monotonic()]
                if ready:
                    i = ready[0]
                    r, attempt, _ = todo[i]
                    if s.accounted(events) + s.RESERVE >= s.CEILING:
                        if pending:
                            time.sleep(0.2)
                            continue
                        stopped.append("budget admission limit")
                        continue
                    if (
                        attempt > 1
                        and sum(e["kind"] == "start" and e["attempt"] > 1 for e in events) >= 24
                    ):
                        todo.pop(i)
                        continue
                    todo.pop(i)
                    e = dict(
                        kind="start",
                        id=r["id"],
                        attempt=attempt,
                        paid=True,
                        started_at=now(),
                        payload_sha256=hashlib.sha256(
                            json.dumps(r["payload"], sort_keys=True).encode()
                        ).hexdigest(),
                    )
                    append(ledger, e)
                    events.append(e)
                    pending[pool.submit(post, r, attempt, key)] = r, attempt
                    last_start = time.monotonic()
            time.sleep(0.2)
    s.write_new(
        s.DATA / "collection.json",
        dict(
            status="completed",
            planned=len(all_requests),
            successful=sum(e["success"] for e in last.values()),
            ended_at=now(),
            attempts=sum(e["kind"] == "start" for e in events),
            accounted_usd=s.accounted(events),
            outcomes=[last[r["id"]] for r in all_requests],
            ledger_sha256=s.sha(ledger),
            freeze_sha256=s.sha(s.DATA / "freeze.json"),
        ),
    )
    print("Collection complete", flush=True)


def measure():
    verify()
    receipt = s.read(s.DATA / "collection.json")
    if (
        receipt["status"] != "completed"
        or s.sha(s.DATA / "attempts.jsonl") != receipt["ledger_sha256"]
    ):
        raise ValueError("collection is not intact and complete")
    with (
        (s.DATA / "measurements.jsonl").open("x") as stream,
        futures.ProcessPoolExecutor(max_workers=4) as pool,
    ):
        for row in pool.map(measure_one, receipt["outcomes"]):
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    lookup = {r["work_id"]: r for r in s.rows(s.ACQUISITIONS)}
    old = s.rows(s.REF)
    items = []
    for r in old:
        original = lookup[r["image_id"]]
        if original["raw_sha256"] != r["raw_sha256"]:
            raise ValueError("reference ancestry mismatch")
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
        for row, original in zip(pool.map(measure_one, items), old):
            if row["status"] == "measured" and not np.allclose(
                row["values"], original["values"], atol=1e-10, rtol=1e-10
            ):
                raise ValueError("reference primary re-extraction differs")
            row["painter_id"] = original["painter_id"]
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    s.write_new(
        s.DATA / "measurement_receipt.json",
        dict(
            ended_at=now(),
            collection_sha256=s.sha(s.DATA / "collection.json"),
            measurements_sha256=s.sha(s.DATA / "measurements.jsonl"),
            reference_windows_sha256=s.sha(s.DATA / "reference_windows.jsonl"),
        ),
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("freeze", "verify", "collect", "measure"))
    args = parser.parse_args()
    globals()[args.action]()


if __name__ == "__main__":
    main()
