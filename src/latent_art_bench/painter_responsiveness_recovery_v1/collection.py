"""Recognize one observed complete proxy 503 without altering retained response bytes.

The coordinator is the frozen v2 coordinator, copied into a new versioned package
only to invoke this narrowly expanded response classifier. Scientific allocation,
rendering parameters, retries, pacing and stop rules remain unchanged.
"""

from __future__ import annotations

import gzip
import math
import shutil
import threading
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from time import monotonic

import httpx

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_distribution_study_v1 import transport as legacy
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_responsiveness_v1.collection import _retry_delay, _slot_outcomes
from latent_art_bench.painter_responsiveness_v2 import collection as base
from latent_art_bench.painter_responsiveness_v2 import common, workflow

PACKAGE = Path("src/latent_art_bench/painter_responsiveness_recovery_v1")
PROTOCOL = Path("studies/painter_responsiveness_recovery_v1/PROTOCOL.md")
POLICY = "exact_proxy_503_text_v1"
EXACT_BODY = (
    b"upstream connect error or disconnect/reset before headers. "
    b"reset reason: connection termination"
)
MAX_RESPONSE, MIN_FREE, RETRY_HTTP = base.MAX_RESPONSE, base.MIN_FREE, base.RETRY_HTTP
_stop_reason, _unresolved_intents = base._stop_reason, base._unresolved_intents


def required_sources():
    return {
        PACKAGE / "collection.py",
        PROTOCOL,
        Path("tests/painter_responsiveness_recovery_v1/test_collection.py"),
    }


def _qualifying_text(row):
    content_type = row.get("response_headers", {}).get("content-type", "")
    return (
        row.get("complete") is True
        and row.get("status_code") == 503
        and row.get("status") == "http_error"
        and content_type.split(";", 1)[0].strip().lower() == "text/plain"
    )


def verify(root, run_id, proxy_root):
    root = Path(root)
    freeze, requests = base.verify(root, run_id, proxy_root)
    recovery = freeze.get("recovery", {})
    predecessor_id = recovery.get("predecessor_run_id")
    if (
        recovery.get("policy") != POLICY
        or not isinstance(predecessor_id, str)
        or predecessor_id == run_id
    ):
        raise ValueError("a disjoint exact-error recovery scope is required")
    prior = common.directory(predecessor_id)
    receipt_path = prior / "collection_receipt.json"
    if recovery.get("predecessor_receipt_path") != str(receipt_path) or hash_file(
        root / receipt_path
    ) != recovery.get("predecessor_receipt_sha256"):
        raise ValueError("recovery predecessor receipt binding changed")
    _, _, _, receipt = workflow.collection_inputs(root, predecessor_id)
    if receipt["status"] != "stopped" or receipt["unresolved_intents"]:
        raise ValueError("only a closed, drained predecessor can authorize this recovery")
    required = required_sources() | {
        prior / name
        for name in (
            "freeze.json",
            "planned_requests.jsonl",
            "collection_receipt.json",
            "generation_events.jsonl",
            "slot_outcomes.jsonl",
            "operator_events.jsonl",
        )
    }
    bound = {Path(row["path"]) for row in freeze["inputs"]}
    if not required.issubset(bound):
        raise ValueError("recovery freeze omits its correction or predecessor evidence")
    committed(root, sorted(required))
    expected = recovery.get("qualifying_error", {})
    matches = [
        row
        for row in events(root / prior / "generation_events.jsonl")
        if row["kind"] == "terminal"
        and row["request_id"] == expected.get("request_id")
        and row["attempt"] == expected.get("attempt")
    ]
    if len(matches) != 1:
        raise ValueError("recovery must identify one exact predecessor error")
    error = matches[0]
    fields = ("request_id", "attempt", "response_path", "response_sha256", "stored_response_sha256")
    if (
        {name: error.get(name) for name in fields} != expected
        or not _qualifying_text(error)
        or error.get("known_error_envelope") is not False
    ):
        raise ValueError("predecessor does not exhibit the declared classifier omission")
    body = workflow._response_entity(root, predecessor_id, error, error["attempt"])
    if body != EXACT_BODY:
        raise ValueError("predecessor error bytes differ from the prospectively fixed rule")
    return freeze, requests


def _send(root, run_id, request, attempt, client, start_gate):
    result = base._send(root, run_id, request, attempt, client, start_gate)
    if _qualifying_text(result) and result.get("known_error_envelope") is False:
        path = root / result["response_path"]
        if hash_file(path) != result["stored_response_sha256"]:
            raise ValueError("new retained response changed before classification")
        with gzip.open(path, "rb") as handle:
            body = handle.read(len(EXACT_BODY) + 1)
        if body == EXACT_BODY:
            # Compatibility field means a recognized complete error, not necessarily JSON.
            result.update(
                original_known_error_envelope=False,
                known_error_envelope=True,
                retry_qualification=POLICY,
            )
    return result


def collect(root, run_id, proxy_root, *, transport=None, sleep=time.sleep):
    """Collect once and drain in-flight requests after any stop; never reopen a run."""
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".generation.lock"):
        freeze, requests = verify(root, run_id, proxy_root)
        config = freeze["config"]
        directory, workspace = root / common.directory(run_id), root / common.WORKSPACE / run_id
        receipt_path, ledger = (
            directory / "collection_receipt.json",
            directory / "generation_events.jsonl",
        )
        marker = workspace / "collection_started.json"
        if receipt_path.exists():
            raise ValueError("collection is terminal; do not resume or top up")
        if marker.exists() or ledger.exists() or (directory / "slot_outcomes.jsonl").exists():
            raise ValueError("previously started collection cannot redispatch")
        if (workspace / "responses").exists() and any((workspace / "responses").iterdir()):
            raise ValueError("orphan response evidence blocks collection")
        if _unresolved_intents(root):
            raise ValueError("unresolved namespace intents require an explicit successor recovery")
        frozen_bytes = {
            name: hash_file(directory / name) for name in ("freeze.json", "planned_requests.jsonl")
        }
        publish(
            marker,
            dict(
                run_id=run_id,
                started_at_utc=utc_now().isoformat(),
                freeze_sha256=frozen_bytes["freeze.json"],
                policy="one shot; interrupted runs cannot redispatch",
            ),
        )
        queue = deque((request, 1, 0.0) for request in requests)
        active, terminal_rows, recent = {}, [], deque(maxlen=config["failure_stop_window"])
        reason, last_start, retries, caught = None, -math.inf, 0, None
        stopped, transport_lock = threading.Event(), threading.Lock()
        transport_last_start = -math.inf

        def start_gate():
            nonlocal transport_last_start
            with transport_lock:
                while not stopped.is_set():
                    delay = (
                        transport_last_start
                        + config["minimum_start_interval_seconds"]
                        - monotonic()
                    )
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
                append_event(
                    directory / "operator_events.jsonl", dict(kind="dispatch_halted", reason=value)
                )

        def finish(future):
            nonlocal retries
            request, attempt = active.pop(future)
            try:
                result = future.result()
            except BaseException as exc:
                result = dict(
                    kind="terminal",
                    request_id=request["request_id"],
                    attempt=attempt,
                    slot_sequence=request["sequence"],
                    route=request["route"],
                    status="outcome_uncertain",
                    status_code=None,
                    complete=False,
                    error=type(exc).__name__,
                    cost_usd=0.0,
                    response_path=None,
                    response_sha256=None,
                    stored_response_sha256=None,
                    observed=None,
                )
            row = append_event(ledger, result)
            terminal_rows.append(row)
            if row.get("post_started", True):
                recent.append(row["status"])
            stop = _stop_reason(row, recent, config)
            if stop:
                halt(stop)
            eligible = (
                not reason
                and row["complete"]
                and row["status"] == "http_error"
                and row["status_code"] in RETRY_HTTP
                and row.get("known_error_envelope")
                and attempt < config["maximum_attempts_per_slot"]
                and retries < config["maximum_technical_retries"]
            )
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
            for name, expected in frozen_bytes.items():
                if hash_file(directory / name) != expected:
                    raise ValueError("frozen collection bytes changed during execution")
            if legacy.proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
                raise ValueError("OAuth proxy identity changed during execution")
            owned = sorted(
                (run_id, request["request_id"], attempt) for request, attempt in active.values()
            )
            if _unresolved_intents(root) != owned:
                raise ValueError("unowned unresolved intent blocks dispatch")
            if shutil.disk_usage(root).free < MIN_FREE + config["maximum_in_flight"] * MAX_RESPONSE:
                halt("storage_reservation_limit")
            return reason is None

        with httpx.Client(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "LatentArtBench responsiveness research"},
            timeout=httpx.Timeout(240, connect=20),
        ) as client:
            with ThreadPoolExecutor(max_workers=config["maximum_in_flight"]) as executor:
                try:
                    while active or (queue and not reason):
                        completed = [future for future in active if future.done()]
                        completed.sort(
                            key=lambda future: (
                                -math.inf
                                if future.exception() is not None
                                else future.result()["completed_monotonic"]
                            )
                        )
                        for future in completed:
                            finish(future)
                        if reason or not queue:
                            if active:
                                wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        request, attempt, due = queue[0]
                        other_block = any(
                            row["block_id"] != request["block_id"] for row, _ in active.values()
                        )
                        if len(active) >= config["maximum_in_flight"] or other_block:
                            wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            continue
                        delay = (
                            max(due, last_start + config["minimum_start_interval_seconds"])
                            - monotonic()
                        )
                        if delay > 0:
                            sleep(min(delay, 0.1))
                            continue
                        if not guard():
                            continue
                        queue.popleft()
                        append_event(
                            ledger,
                            dict(
                                kind="attempt",
                                request_id=request["request_id"],
                                attempt=attempt,
                                slot_sequence=request["sequence"],
                                route=request["route"],
                                request_sha256=digest(request),
                                payload_sha256=digest(request["payload"]),
                                paid=False,
                                reservation_usd=0.0,
                                admitted_monotonic=monotonic(),
                            ),
                        )
                        last_start = monotonic()
                        future = executor.submit(
                            _send, root, run_id, request, attempt, client, start_gate
                        )
                        active[future] = request, attempt
                except BaseException as exc:
                    caught = exc
                    halt("coordinator_interrupted_" + type(exc).__name__)
                finally:
                    for future in list(active):
                        finish(future)
        intents = [row for row in events(ledger) if row["kind"] == "attempt"]
        slots = _slot_outcomes(requests, terminal_rows, intents)
        publish(directory / "slot_outcomes.jsonl", slots, lines=True)
        receipt = dict(
            schema="painter-responsiveness-collection/2",
            run_id=run_id,
            recorded_git_commit=freeze["recorded_git_commit"],
            freeze_sha256=frozen_bytes["freeze.json"],
            requests_sha256=frozen_bytes["planned_requests.jsonl"],
            status="completed" if reason is None else "stopped",
            stop_reason=reason,
            total_planned=len(requests),
            status_counts=dict(Counter(row["status"] for row in slots)),
            attempt_intents=len(intents),
            terminal_attempts=len(terminal_rows),
            technical_retries_dispatched=sum(
                row["attempt"] > 1 and row.get("post_started", True) for row in terminal_rows
            ),
            incremental_api_spend_usd=0.0,
            paid_requests=0,
            accounting_basis=(
                "OAuth service; zero incremental API charge, not a subscription valuation"
            ),
            generation_events_sha256=hash_file(ledger) if ledger.exists() else None,
            slot_outcomes_sha256=hash_file(directory / "slot_outcomes.jsonl"),
            unresolved_intents=_unresolved_intents(root),
            new_feature_measurements=0,
            terminal=True,
        )
        publish(receipt_path, receipt)
        if caught is not None:
            raise caught
        return receipt
