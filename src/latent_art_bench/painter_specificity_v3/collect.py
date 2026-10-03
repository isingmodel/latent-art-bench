"""Paid v3 collection: a versioned copy of the September collector, and offline measurement.

The dispatch rules are those of ``painter_specificity_v2.workflow``: at most three requests in
flight, starts at least five seconds apart, a $5 reservation per start until its charge is known,
at most two retries per request (20 s, then 60 s) and 24 in all, a pause on three consecutive
technical failures, a client rejection, a diagnostic or an unknown or excess charge, and a
create-once terminal receipt. What differs: the run, the arms, a ceiling the owner approved in
writing, and a baseline read from the September receipt.
"""

from __future__ import annotations

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

PROTOCOL = s.ROOT / "studies" / s.NS / "PROTOCOL.md"
REFERENCES = s.ROOT / "studies" / s.NS / "REFERENCES.md"
REFERENCE_RUN = s.ROOT / "data/manifests" / s.NS / "refs-20261002"
QUOTES = s.ROOT / "data/manifests" / s.NS / "provider_quotes_20261002.json"
REFUSALS = ("content_policy_violation", "moderation_blocked", "safety_violation",
            "image_generation_user_error", "invalid_prompt")


def inputs() -> list:
    paths = [PROTOCOL, REFERENCES, QUOTES, s.PREDECESSOR, s.PREDECESSOR.with_name("requests.jsonl"),
             s.first.SCALER, s.ROOT / "pyproject.toml", s.ROOT / "uv.lock"]
    paths += [REFERENCE_RUN / n for n in ("features.jsonl", "measurement_receipt.json",
                                          "frame.jsonl", "determination.jsonl")]
    paths += sorted((s.ROOT / "src/latent_art_bench" / s.NS).glob("*.py"))
    paths += sorted((s.ROOT / "tests" / s.NS).glob("*.py"))
    paths += [s.ROOT / "src/latent_art_bench" / p for p in (
        "painter_specificity_v1/study.py", "painter_specificity_v1/workflow.py",
        "painter_specificity_v2/study.py", "painter_feature_generation_v2/features.py",
        "painter_distribution_study_v1/discovery.py")]
    return paths


def freeze(ceiling_usd: float, approval: str) -> dict:
    """Write the request frame and bind every input. Requires committed inputs and approval."""
    if (s.DATA / "freeze.json").exists():
        raise FileExistsError("v3 collection is already frozen")
    if not approval.strip():
        raise ValueError("record the owner's written approval of the protocol and ceiling")
    paths = inputs()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *map(str, paths)], cwd=s.ROOT, text=True)
    if dirty.strip():
        raise ValueError("commit inputs before freeze:\n" + dirty)
    baseline = float(s.read(s.PREDECESSOR)["accounted_usd"])
    expected = s.forecast()["expected_usd"]
    if ceiling_usd <= baseline + s.RESERVE:
        raise ValueError("ceiling admits no request")
    # The owner sets the ceiling. Below the forecast plus reservations the run may stop short;
    # the receipt then records the budget stop and the analysis uses the complete scenes.
    margin = ceiling_usd - (baseline + expected)
    items = s.assignments()
    s.DATA.mkdir(parents=True, exist_ok=True)
    with (s.DATA / "requests.jsonl").open("x") as stream:
        for r in items:
            stream.write(json.dumps(r, sort_keys=True) + "\n")
    paths.append(s.DATA / "requests.jsonl")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=s.ROOT, text=True).strip()
    record = dict(recorded_git_commit=commit, created_at=now(), run_id=s.RUN,
                  baseline_usd=baseline, ceiling_usd=float(ceiling_usd), approval=approval,
                  expected_usd=expected, margin_over_forecast_usd=margin, requests=len(items),
                  predecessor_sha256=s.sha(s.PREDECESSOR),
                  inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths])
    s.write_new(s.DATA / "freeze.json", record)
    return record


def verify() -> dict:
    frozen = s.read(s.DATA / "freeze.json")
    for record in frozen["inputs"]:
        if s.sha(s.ROOT / record["path"]) != record["sha256"]:
            raise ValueError("frozen input changed: " + record["path"])
    return frozen


def post(r: dict, attempt: int, key: str) -> dict:
    result = dict(kind="end", id=r["id"], attempt=attempt, status=None, success=False,
                  retryable=False, cost_usd=None)
    path = s.WORK / "responses" / f"{r['id']}-a{attempt}.json.gz"
    try:
        with httpx.Client(timeout=600, follow_redirects=False, trust_env=False) as client:
            with client.stream("POST", s.URL, json=r["payload"],
                               headers={"Authorization": "Bearer " + key}) as response:
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
        result.update(response_path=str(path.relative_to(s.ROOT)),
                      response_sha256=hashlib.sha256(body).hexdigest())
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
            result.update(success=True, image_path=str(image_path.relative_to(s.ROOT)),
                          **metadata)
        else:
            error = value.get("error") or {}
            result["error_code"] = error.get("code") if isinstance(error, dict) else None
            result["retryable"] = (result["status"] in (429, 500, 502, 503, 504)
                                   and result["error_code"] not in REFUSALS)
    except httpx.TransportError as exc:
        result.update(retryable=True, error_type=type(exc).__name__)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        result.update(error_type=type(exc).__name__, diagnostic=str(exc)[:200])
    result["ended_at"] = now()
    return result


def collect() -> None:
    frozen = verify()
    if (s.DATA / "collection.json").exists():
        raise ValueError("terminal collection cannot restart")
    s.WORK.mkdir(parents=True, exist_ok=True)
    lock = s.WORK / "collector.lock"
    with lock.open("x") as stream:
        stream.write(now())
    stopped: list[str] = []
    previous = signal.signal(signal.SIGINT, lambda *_: stopped.append("operator pause"))
    try:
        collect_loop(stopped, frozen["baseline_usd"], frozen["ceiling_usd"])
    finally:
        signal.signal(signal.SIGINT, previous)
        lock.unlink()


def collect_loop(stopped: list[str], baseline: float, ceiling: float, post=post) -> None:
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
    key, last_start, errors = key_from_env(s.ROOT), 0.0, 0
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending: dict = {}
        while todo or pending:
            for future in [f for f in pending if f.done()]:
                r, attempt = pending.pop(future)
                e = future.result()
                append(ledger, e)
                events.append(e)
                last[r["id"]] = e
                errors = errors + 1 if e["retryable"] else 0
                if errors >= 3 or e.get("diagnostic") or e["status"] in (400, 401, 402, 403,
                                                                         404, 422):
                    stopped.append("technical diagnosis required")
                if e["cost_usd"] is None or e["cost_usd"] > s.RESERVE:
                    stopped.append("unknown/excess charge requires diagnosis")
                retries = sum(x["kind"] == "start" and x["attempt"] > 1 for x in events)
                if e["retryable"] and attempt < 3 and retries < 24:
                    todo.append((r, attempt + 1, time.monotonic() + (20 if attempt == 1 else 60)))
                if len(last) % 120 == 0 or not e["success"]:
                    print(json.dumps(dict(slots=len(last),
                                          images=sum(x["success"] for x in last.values()),
                                          accounted_usd=round(s.accounted(events, baseline), 6))),
                          flush=True)
            if (s.WORK / "pause_requested").exists():
                stopped.append("operator pause file")
            if stopped:
                if pending:
                    time.sleep(0.2)
                    continue
                append(s.DATA / "operator_events.jsonl",
                       dict(kind="pause", at=now(), reasons=stopped))
                print("Paused after draining all active requests", flush=True)
                return
            if todo and len(pending) < 3 and time.monotonic() - last_start >= 5:
                ready = [i for i, (_, _, at) in enumerate(todo) if at <= time.monotonic()]
                if ready:
                    i = ready[0]
                    r, attempt, _ = todo[i]
                    if s.accounted(events, baseline) + s.RESERVE >= ceiling:
                        if pending:
                            time.sleep(0.2)
                            continue
                        stopped.append("budget admission limit")
                        continue
                    retries = sum(x["kind"] == "start" and x["attempt"] > 1 for x in events)
                    todo.pop(i)
                    if attempt > 1 and retries >= 24:
                        continue
                    e = dict(kind="start", id=r["id"], attempt=attempt, paid=True,
                             started_at=now(),
                             payload_sha256=hashlib.sha256(
                                 json.dumps(r["payload"], sort_keys=True).encode()).hexdigest())
                    append(ledger, e)
                    events.append(e)
                    pending[pool.submit(post, r, attempt, key)] = r, attempt
                    last_start = time.monotonic()
            time.sleep(0.2)
    s.write_new(s.DATA / "collection.json", dict(
        status="completed", planned=len(all_requests),
        successful=sum(e["success"] for e in last.values()), ended_at=now(),
        attempts=sum(e["kind"] == "start" for e in events),
        accounted_usd=s.accounted(events, baseline),
        outcomes=[last[r["id"]] for r in all_requests],
        ledger_sha256=s.sha(ledger), freeze_sha256=s.sha(s.DATA / "freeze.json")))
    print("Collection complete", flush=True)


def measure() -> dict:
    """31 features of every delivered image, full view and central square, as in September."""
    verify()
    receipt = s.read(s.DATA / "collection.json")
    if (s.DATA / "measurements.jsonl").exists():
        raise FileExistsError("measurement is terminal")
    rows = [measure_one(item) for item in receipt["outcomes"]]
    with (s.DATA / "measurements.jsonl").open("x") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    record = dict(created_at=now(), measured=sum(r["status"] == "measured" for r in rows),
                  planned=len(rows), collection_sha256=s.sha(s.DATA / "collection.json"),
                  measurements_sha256=s.sha(s.DATA / "measurements.jsonl"))
    s.write_new(s.DATA / "measurement_receipt.json", record)
    return record
