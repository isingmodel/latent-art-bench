"""One-shot, gated image collection with bounded concurrency and durable accounting.

This is prospective transport code. Importing it performs no network or image I/O.
Admission is spaced by at least five seconds; at most two requests are in flight.
A stopped or interrupted run cannot resume, even if its final receipt is absent.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import shutil
import threading
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from pathlib import Path
from time import monotonic

import httpx

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_distribution_study_v1.transport import (
    cost_from_response,
    inspect_response,
)
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import common, design

URL = "https://openrouter.ai/api/v1/images"
MAX_RESPONSE = 64 * 1024**2
MIN_FREE = 1024**3
RETRY_HTTP = {429, 500, 502, 503, 504}
GATE_KEYS = frozenset(common.generation_gate({}, {}, {}, {})["checks"])


def _money(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid nonnegative accounting amount")
    return Decimal(str(value))


def verify_generation(root, run_id):
    """Admit only a committed, fully gated, exactly regenerated 192-slot inventory."""
    directory = common.directory(run_id)
    freeze_path = directory / "generation_freeze.json"
    requests_path = directory / "planned_requests.jsonl"
    freeze = read_json(root / freeze_path)
    if freeze["run_id"] != run_id:
        raise ValueError("generation run identity mismatch")
    gates = freeze.get("gates", {})
    checks = gates.get("checks", {})
    if (gates.get("status") != "ready" or set(checks) != GATE_KEYS
            or not all(value is True for value in checks.values()) or gates.get("missing", [])):
        raise ValueError("all declared generation gates must be ready before collection")
    config = freeze["config"]
    if config != common.configuration(root):
        raise ValueError("generation configuration differs from the committed study configuration")
    if (config["maximum_in_flight"] not in (1, 2)
            or not math.isfinite(config["minimum_start_interval_seconds"])
            or config["minimum_start_interval_seconds"] < 5
            or config["maximum_attempts_per_slot"] not in (1, 2)
            or not 0 <= config["maximum_technical_retries"] <= 6
            or (config["failure_stop_count"], config["failure_stop_window"]) != (3, 8)
            or config["request_reservation_usd"] != 5
            or not 0 < _money(config["maximum_new_spend_usd"]) <= Decimal("20")
            or not 0 < _money(config["overall_spending_ceiling_usd"]) <= Decimal("75")):
        raise ValueError("generation limits exceed the bounded transport policy")
    baseline = _money(freeze["budget_baseline_usd"])
    if baseline >= _money(config["overall_spending_ceiling_usd"]):
        raise ValueError("historical baseline has exhausted the overall spending ceiling")
    source_path = common.directory(freeze["diagnostic_run_id"]) / "freeze.json"
    if hash_file(root / source_path) != freeze["source_freeze_sha256"]:
        raise ValueError("source diagnostic freeze changed")
    source = read_json(root / source_path)
    if source["run_id"] != freeze["diagnostic_run_id"]:
        raise ValueError("source diagnostic identity mismatch")
    verify_bindings(root, source["inputs"])
    verify_bindings(root, freeze["inputs"])
    paths = {Path(row["path"]) for row in freeze["inputs"]}
    required = {common.PACKAGE / "collection.py", common.PACKAGE / "common.py",
                common.PACKAGE / "design.py", common.PACKAGE / "generation_prepare.py",
                common.CONFIG}
    required.update(Path("src/latent_art_bench") / name for name in (
        "io.py", "painter_feature_generation_v2/artifacts.py",
        "painter_distribution_study_v1/transport.py", "painter_distribution_study_v1/discovery.py",
        "painter_prompt_study_v1/common.py",
    ))
    if not required.issubset(paths):
        raise ValueError("generation freeze must bind collector, design and configuration sources")
    committed(root, sorted(paths | {freeze_path, requests_path, source_path}))
    if not isinstance(freeze.get("recorded_git_commit"), str) or not freeze["recorded_git_commit"]:
        raise ValueError("generation freeze lacks its recorded commit")
    if hash_file(root / requests_path) != freeze["requests_sha256"]:
        raise ValueError("planned request bytes changed")
    schedule = design.make_schedule([r["template_id"] for r in config["templates"]],
                                    seed=config["seed"], repetitions=config["repetitions"])
    requests = read_jsonl(root / requests_path)
    if requests != common.requests_from_schedule(schedule, config):
        raise ValueError("planned requests differ from the fixed randomized rendering contract")
    if (config["route"], config["model"], config["provider"]) != (
        "flux_2_max", "black-forest-labs/flux.2-max", "black-forest-labs/us-3"
    ):
        raise ValueError("the frozen responsiveness route has no provider fallback")
    from .generation_prepare import verify_qualification

    verify_qualification(root, freeze)
    return freeze, requests


def _require_live_metadata_age(root, freeze):
    """Freshness limits admission to a new live run, never historical measurement/replay."""
    provider = read_json(root / freeze["provider_preflight_path"])
    try:
        checked = datetime.fromisoformat(provider["checked_at_utc"])
        if checked.tzinfo is None:
            raise ValueError("metadata timestamp lacks a timezone")
        age = (datetime.now(timezone.utc) - checked).total_seconds()
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("provider metadata requires a valid dated preflight") from exc
    if not 0 <= age <= 24 * 3600:
        raise ValueError("provider metadata must be no older than 24 hours "
                         "at live collection start")


def budget_state(root, *, reservation=5.0):
    """Account for every paid intent in this namespace, including prior stopped runs."""
    known, uncertain = Decimal("0"), Decimal("0")
    pending, unknown, attempts, terminal_count = set(), [], 0, 0
    for path in sorted((root / common.MANIFESTS).glob("*/generation_events.jsonl")):
        intents, terminals = {}, {}
        for row in events(path):
            key = (path.parent.name, row["request_id"], row["attempt"])
            if row["kind"] == "attempt":
                if key in intents or key in terminals:
                    raise ValueError("duplicate paid attempt intent")
                if _money(row["reservation_usd"]) != _money(reservation):
                    raise ValueError("paid attempt reservation changed")
                intents[key] = row
            elif row["kind"] == "terminal":
                if key not in intents or key in terminals:
                    raise ValueError("unpaired or duplicate terminal attempt")
                terminals[key] = row
                if row["cost_usd"] is None:
                    uncertain += _money(reservation)
                    unknown.append(key)
                else:
                    known += _money(row["cost_usd"])
            else:
                raise ValueError("undeclared generation ledger event")
        unresolved = set(intents) - set(terminals)
        pending.update(unresolved)
        uncertain += len(unresolved) * _money(reservation)
        attempts += len(intents)
        terminal_count += len(terminals)
    return dict(known_cost_usd=float(known), unknown_or_pending_reservation_usd=float(uncertain),
                accounted_usd=float(known + uncertain), attempts=attempts,
                terminal_attempts=terminal_count, pending=sorted(pending),
                unknown_cost=sorted(unknown))


def _refusal(body):
    try:
        value = json.loads(body)
        error = value.get("error", {})
        text = json.dumps(error).lower()
        return bool(value.get("refusal")) or any(
            word in text for word in
            ("refusal", "refused", "safety", "content_policy", "moderation")
        )
    except (ValueError, AttributeError, TypeError):
        return False


def _send(root, run_id, request, attempt, client, secret, start_gate):
    """Retain the received entity, including failed/partial responses, exactly once."""
    started = start_gate()
    if started is None:
        return dict(kind="terminal", request_id=request["request_id"], attempt=attempt,
                    slot_sequence=request["sequence"], route=request["route"],
                    status="cancelled_before_post", status_code=None, complete=True,
                    cost_usd=0.0, post_started=False, response_path=None, response_sha256=None,
                    stored_response_sha256=None, observed=None, error=None,
                    completed_monotonic=monotonic())
    status_code, complete, error, headers, chunks, size = None, False, None, {}, [], 0
    start = monotonic()
    try:
        with client.stream("POST", URL, json=request["payload"]) as response:
            status_code = response.status_code
            headers = {k: response.headers[k]
                       for k in ("content-type", "date", "x-request-id", "retry-after")
                       if k in response.headers}
            # No chunk-size buffer: a short prefix must survive a subsequent read failure.
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                size += len(chunk)
                if size > MAX_RESPONSE:
                    error = "response_byte_limit"
                    break
            else:
                complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    redacted = bool(secret.encode() in body or any(secret in value for value in headers.values()))
    if redacted:
        body, headers = b'{"credential_echo_suppressed":true}', {}
        complete, error = False, "credential_echo"
    filename = f"{request['sequence']:04d}-a{attempt}.json.gz"
    relative = common.WORKSPACE / run_id / "responses" / filename
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(gzip.compress(body, mtime=0))
        handle.flush()
        os.fsync(handle.fileno())
    cost = cost_from_response(body, status_code, True) if complete else None
    observed = None
    status = "outcome_uncertain" if not complete else "http_error"
    if complete and _refusal(body):
        status = "refused"
    elif complete and status_code is not None and 200 <= status_code < 300:
        try:
            observed = inspect_response(body)
            valid = (observed["minimum_512"] and observed["width"] == observed["height"]
                     and observed["format"] == "PNG")
            status = "image_returned" if valid else "delivery_mismatch"
        except Exception as exc:
            # The bounded response is retained; malformed success is never a retry candidate.
            status, error = "invalid_response", type(exc).__name__
    return dict(kind="terminal", request_id=request["request_id"], attempt=attempt,
                slot_sequence=request["sequence"], route=request["route"], status=status,
                status_code=status_code, complete=complete, error=error, cost_usd=cost,
                response_path=str(relative), response_sha256=hashlib.sha256(body).hexdigest(),
                stored_response_sha256=hash_file(path), received_bytes=size,
                response_bytes=len(body), credential_echo_suppressed=redacted,
                response_headers=headers, observed=observed,
                post_started=True, transport_started_monotonic=started,
                latency_seconds=max(0.0, monotonic() - start), completed_monotonic=monotonic())


def _retry_delay(row):
    value = row.get("response_headers", {}).get("retry-after")
    if value is None:
        return 0.0
    try:
        delay = float(value)
    except (ValueError, TypeError):
        try:
            delay = parsedate_to_datetime(value).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError) as exc:
            raise ValueError("unsupported Retry-After; no automatic retry") from exc
    if not math.isfinite(delay) or delay > 300:
        raise ValueError("Retry-After exceeds the bounded retry window")
    return max(0.0, delay)


def _stop_reason(row, recent, config):
    if row["cost_usd"] is None:
        return "unknown_charge"
    if row["status"] in ("outcome_uncertain", "invalid_response", "delivery_mismatch"):
        return "unresolved_delivery"
    if _money(row["cost_usd"]) > _money(config["request_reservation_usd"]):
        return "reported_cost_exceeds_reservation"
    if row["status_code"] in (401, 402, 404) or (
        row["status_code"] == 403 and row["status"] != "refused"
    ):
        return "provider_auth_budget_or_contract_error"
    if sum(status != "image_returned" for status in recent) >= config["failure_stop_count"]:
        return "three_failed_attempts_in_eight_completed"
    return None


def _slot_outcomes(requests, terminal_rows, intent_rows):
    output = []
    for request in requests:
        rows = sorted((r for r in terminal_rows if r["request_id"] == request["request_id"]),
                      key=lambda r: r["attempt"])
        intents = [r for r in intent_rows if r["request_id"] == request["request_id"]]
        pending = [r for r in intents if not any(t["attempt"] == r["attempt"] for t in rows)]
        posted = [r for r in rows if r.get("post_started", True)]
        selected = next((r for r in rows if r["status"] == "image_returned"), None)
        summary = dict(request_id=request["request_id"], sequence=request["sequence"],
                       status="outcome_unresolved" if pending else selected["status"]
                       if selected else posted[-1]["status"] if posted else "never_started",
                       attempt_count=len(intents),
                       selected_attempt=selected["attempt"] if selected else None,
                       known_cost_usd=float(sum((_money(r["cost_usd"]) for r in rows
                                                if r["cost_usd"] is not None), Decimal("0"))),
                       unknown_cost=bool(pending) or any(r["cost_usd"] is None for r in rows),
                       attempts=[dict(attempt=r["attempt"], status=r["status"],
                                      cost_usd=r["cost_usd"], event_sha256=r["event_sha256"])
                                 for r in rows])
        summary["pending_attempts"] = [dict(attempt=r["attempt"],
                                            intent_event_sha256=r["event_sha256"]) for r in pending]
        for field in ("response_path", "response_sha256", "stored_response_sha256", "observed"):
            summary[field] = selected[field] if selected else None
        summary["selected_terminal_event_sha256"] = selected["event_sha256"] if selected else None
        output.append(summary)
    return output


def collect(root, run_id, *, transport=None, sleep=time.sleep):
    """Execute an admitted run once. MockTransport is the only transport used by tests.

    The baseline is historic pre-responsiveness accounting. All namespace runs
    share the $20 new-spend ceiling. Unknown charges retain their full reservation.
    Reported costs beyond a reservation halt dispatch but cannot undo vendor bills.
    """
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".generation.lock"):
        freeze, requests = verify_generation(root, run_id)
        config = freeze["config"]
        directory, workspace = root / common.directory(run_id), root / common.WORKSPACE / run_id
        receipt_path = directory / "collection_receipt.json"
        ledger = directory / "generation_events.jsonl"
        marker = workspace / "collection_started.json"
        if receipt_path.exists():
            raise ValueError("collection is terminal; do not resume or top up")
        if marker.exists() or ledger.exists() or (directory / "slot_outcomes.jsonl").exists():
            raise ValueError("interrupted or previously started collection cannot redispatch")
        if (workspace / "responses").exists() and any((workspace / "responses").iterdir()):
            raise ValueError("orphan response evidence blocks collection")
        state = budget_state(root)
        if state["pending"] or state["unknown_cost"]:
            raise ValueError("unresolved intent or unknown charge in the responsiveness namespace")
        _require_live_metadata_age(root, freeze)
        for other in (root / common.MANIFESTS).glob("*/generation_freeze.json"):
            if (other.parent / "generation_events.jsonl").exists():
                if read_json(other)["budget_baseline_usd"] != freeze["budget_baseline_usd"]:
                    raise ValueError("historic baseline changed across responsiveness runs")
        secret = key_from_env(root)
        frozen_bytes = dict(generation_freeze=hash_file(directory / "generation_freeze.json"),
                            planned_requests=hash_file(directory / "planned_requests.jsonl"))
        publish(marker, dict(run_id=run_id, started_at_utc=utc_now().isoformat(),
                             generation_freeze_sha256=frozen_bytes["generation_freeze"],
                             policy="one shot; an incomplete run cannot redispatch"))
        queue = deque((request, 1, 0.0) for request in requests)
        active, terminal_rows, recent = {}, [], deque(maxlen=config["failure_stop_window"])
        reason, last_start, retries = None, -math.inf, 0
        caught = None
        stopped, transport_lock = threading.Event(), threading.Lock()
        transport_last_start = -math.inf

        def start_gate():
            nonlocal transport_last_start
            # Enforce pacing at worker invocation too: scheduler/thread delays
            # must not compress a pair of requests admitted five seconds apart.
            with transport_lock:
                while not stopped.is_set():
                    delay = (transport_last_start + config[
                        "minimum_start_interval_seconds"] - monotonic())
                    if delay <= 0:
                        transport_last_start = monotonic()
                        return transport_last_start
                    sleep(min(delay, 0.1))
            return None

        def halt(value):
            nonlocal reason
            if reason is None:
                reason = value
                stopped.set()
                append_event(directory / "operator_events.jsonl",
                             dict(kind="dispatch_halted", reason=value))

        def finish(future):
            nonlocal retries
            request, attempt = active.pop(future)
            try:
                result = future.result()
            except BaseException as exc:
                result = dict(kind="terminal", request_id=request["request_id"], attempt=attempt,
                              slot_sequence=request["sequence"], route=request["route"],
                              status="outcome_uncertain", status_code=None, complete=False,
                              error=type(exc).__name__, cost_usd=None, response_path=None,
                              response_sha256=None, stored_response_sha256=None, observed=None)
            row = append_event(ledger, result)
            terminal_rows.append(row)
            if row.get("post_started", True):
                recent.append(row["status"])
            stop = _stop_reason(row, recent, config)
            if stop:
                halt(stop)
            eligible = (not reason and row["complete"] and row["status"] == "http_error"
                        and row["status_code"] in RETRY_HTTP and row["cost_usd"] is not None
                        and attempt < config["maximum_attempts_per_slot"]
                        and retries < config["maximum_technical_retries"])
            if eligible:
                try:
                    delay = _retry_delay(row)
                except ValueError:
                    halt("unsupported_or_excessive_retry_after")
                else:
                    retries += 1
                    queue.appendleft((request, attempt + 1, monotonic() + delay))

        def guard():
            verify_bindings(root, freeze["inputs"])
            source = root / common.directory(freeze["diagnostic_run_id"]) / "freeze.json"
            if hash_file(source) != freeze["source_freeze_sha256"]:
                raise ValueError("source diagnostic freeze changed during collection")
            verify_bindings(root, read_json(source)["inputs"])
            for name, expected in frozen_bytes.items():
                filename = ("generation_freeze.json" if name == "generation_freeze"
                            else "planned_requests.jsonl")
                if hash_file(directory / filename) != expected:
                    raise ValueError("committed generation bytes changed during collection")
            state = budget_state(root)
            owned = {(run_id, request["request_id"], attempt)
                     for request, attempt in active.values()}
            if set(map(tuple, state["pending"])) != owned or state["unknown_cost"]:
                raise ValueError("unowned or uncertain accounting blocks dispatch")
            reserve = _money(state["accounted_usd"]) + _money(config["request_reservation_usd"])
            if (reserve > _money(config["maximum_new_spend_usd"])
                    or _money(freeze["budget_baseline_usd"]) + reserve
                    > _money(config["overall_spending_ceiling_usd"])):
                if active:
                    return False  # In-flight reservations can be released by known terminal costs.
                halt("spending_reservation_limit")
            if shutil.disk_usage(root).free < MIN_FREE + config["maximum_in_flight"] * MAX_RESPONSE:
                halt("storage_reservation_limit")
            return reason is None

        headers = {"Authorization": "Bearer " + secret,
                   "User-Agent": "LatentArtBench responsiveness research"}
        with httpx.Client(transport=transport, headers=headers, follow_redirects=False,
                          trust_env=False, timeout=httpx.Timeout(240, connect=20)) as client:
            with ThreadPoolExecutor(max_workers=config["maximum_in_flight"]) as executor:
                try:
                    while active or (queue and not reason):
                        completed = [future for future in active if future.done()]
                        completed.sort(key=lambda future: (
                            -math.inf if future.exception() is not None else
                            future.result()["completed_monotonic"]))
                        # One callback coordinator writes terminals and checks all stops
                        # before admitting another request. Already-sent requests are drained.
                        for future in completed:
                            finish(future)
                        if reason:
                            if active:
                                wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        if not queue:
                            if active:
                                wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        request, attempt, due = queue[0]
                        other_block = any(r["block_id"] != request["block_id"]
                                          for r, _ in active.values())
                        if len(active) >= config["maximum_in_flight"] or other_block:
                            wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        delay = max(due, last_start + config[
                            "minimum_start_interval_seconds"]) - monotonic()
                        if delay > 0:
                            sleep(min(delay, 0.1))
                            continue
                        if not guard():
                            if active:
                                wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        queue.popleft()
                        append_event(ledger, dict(
                            kind="attempt", request_id=request["request_id"], attempt=attempt,
                            slot_sequence=request["sequence"], route=request["route"],
                            request_sha256=digest(request),
                            payload_sha256=digest(request["payload"]),
                            reservation_usd=config["request_reservation_usd"],
                            admitted_monotonic=monotonic(),
                        ))
                        last_start = monotonic()
                        future = executor.submit(
                            _send, root, run_id, request, attempt, client, secret, start_gate)
                        active[future] = (request, attempt)
                except BaseException as exc:
                    caught = exc
                    halt("coordinator_interrupted_" + type(exc).__name__)
                finally:
                    # Normal interruptions preserve returned bodies and final accounting.
                    # SIGKILL/power loss leaves the durable marker and pending paid intents.
                    for future in list(active):
                        finish(future)
        intents = [row for row in events(ledger) if row["kind"] == "attempt"]
        slots = _slot_outcomes(requests, terminal_rows, intents)
        publish(directory / "slot_outcomes.jsonl", slots, lines=True)
        state = budget_state(root)
        receipt = dict(
            schema="painter-responsiveness-collection/1", run_id=run_id,
            recorded_git_commit=freeze["recorded_git_commit"],
            generation_freeze_sha256=frozen_bytes["generation_freeze"],
            requests_sha256=frozen_bytes["planned_requests"],
            status="completed" if reason is None else "stopped", stop_reason=reason,
            total_planned=len(requests), status_counts=dict(Counter(r["status"] for r in slots)),
            attempt_intents=len(intents), terminal_attempts=len(terminal_rows),
            technical_retries_dispatched=sum(
                r["attempt"] > 1 and r.get("post_started", True) for r in terminal_rows),
            budget_baseline_usd=freeze["budget_baseline_usd"],
            namespace_budget=state,
            overall_conservative_accounted_usd=(
                freeze["budget_baseline_usd"] + state["accounted_usd"]),
            generation_events_sha256=hash_file(ledger) if ledger.exists() else None,
            slot_outcomes_sha256=hash_file(directory / "slot_outcomes.jsonl"),
            new_feature_measurements=0, terminal=True,
            spending_limit_breached=(state["accounted_usd"] > config["maximum_new_spend_usd"]
                or freeze["budget_baseline_usd"] + state["accounted_usd"]
                > config["overall_spending_ceiling_usd"]),
        )
        publish(receipt_path, receipt)
        if caught is not None:
            raise caught
        return receipt
