"""One-shot OAuth collection for the computational-only responsiveness experiment.

Two requests may overlap within a randomized block, with at least five seconds
between starts. This module never sends credentials or contacts a paid route.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import threading
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from time import monotonic

import httpx

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
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
from latent_art_bench.painter_responsiveness_v1.collection import (
    _refusal,
    _retry_delay,
    _slot_outcomes,
)

from . import common

URL = "http://127.0.0.1:10532/v1/images/generations"
MAX_RESPONSE = 64 * 1024**2
MIN_FREE = 1024**3
RETRY_HTTP = frozenset((429, 500, 502, 503, 504))


def required_sources():
    """Inputs which must remain bound before any image request is sent."""
    required = {common.CONFIG}
    required.update(common.PACKAGE / name for name in ("common.py", "collection.py", "workflow.py"))
    required.update(
        Path("src/latent_art_bench") / name
        for name in (
            "io.py",
            "painter_distribution_study_v1/transport.py",
            "painter_feature_generation_v2/artifacts.py",
            "painter_prompt_study_v1/common.py",
            "painter_responsiveness_v1/collection.py",
            "painter_responsiveness_v1/design.py",
        )
    )
    return required


def verify(root, run_id, proxy_root):
    """Require committed sources, an exact inventory, and the inspected loopback proxy."""
    from .workflow import RUNTIME

    root = Path(root)
    directory = common.directory(run_id)
    freeze_path, requests_path = directory / "freeze.json", directory / "planned_requests.jsonl"
    freeze = read_json(root / freeze_path)
    if freeze.get("run_id") != run_id:
        raise ValueError("collection freeze identity differs")
    config = freeze["config"]
    if config != common.configuration(root):
        raise ValueError("collection configuration differs from its frozen source")
    if (
        config["route"] != "oauth_gpt_image_2"
        or config["model"] != "gpt-image-2"
        or config["maximum_in_flight"] not in (1, 2)
        or not math.isfinite(config["minimum_start_interval_seconds"])
        or config["minimum_start_interval_seconds"] < 5
        or config["maximum_attempts_per_slot"] not in (1, 2)
        or config["minimum_delivered_short_side"] != 512
        or not 0 <= config["maximum_technical_retries"] <= 6
        or (config["failure_stop_count"], config["failure_stop_window"]) != (3, 8)
    ):
        raise ValueError("configuration exceeds the fixed OAuth transport contract")
    verify_bindings(root, freeze["inputs"])
    paths = {Path(row["path"]) for row in freeze["inputs"]}
    if not required_sources().issubset(paths):
        raise ValueError("collection freeze must bind all transport and inventory sources")
    committed(root, sorted(paths | {freeze_path, requests_path}))
    commit = freeze.get("recorded_git_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise ValueError("collection freeze requires its source commit")
    environment = freeze.get("environment", {})
    if set(environment) != {"python", *RUNTIME}:
        raise ValueError("collection freeze must bind the complete runtime")
    for name, expected in environment.items():
        actual = platform.python_version() if name == "python" else importlib.metadata.version(name)
        if actual != expected:
            raise ValueError("bound collection runtime changed: " + name)
    if hash_file(root / requests_path) != freeze["requests_sha256"]:
        raise ValueError("planned request bytes changed")
    requests = read_jsonl(root / requests_path)
    if len(requests) != 192 or requests != common.requests(config):
        raise ValueError("planned requests differ from the complete randomized inventory")
    for row in requests:
        if row["payload"] != legacy.payload("oauth_gpt_image_2", row["payload"]["prompt"]):
            raise ValueError("planned payload differs from the fixed rendering contract")
        if row["route"] != "oauth_gpt_image_2":
            raise ValueError("paid routes and provider substitutions are outside this collection")
    if legacy.proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
        raise ValueError("OAuth proxy identity changed")
    return freeze, requests


def _unresolved_intents(root):
    pending = []
    for path in sorted((root / common.MANIFESTS).glob("*/generation_events.jsonl")):
        intents, terminals = set(), set()
        for row in events(path):
            key = row["request_id"], row["attempt"]
            if row["kind"] == "attempt":
                if key in intents or key in terminals:
                    raise ValueError("duplicate request intent")
                intents.add(key)
            elif row["kind"] == "terminal":
                if key not in intents or key in terminals:
                    raise ValueError("unpaired or duplicate terminal")
                terminals.add(key)
            else:
                raise ValueError("undeclared generation event")
        pending.extend((path.parent.name, *key) for key in intents - terminals)
    return sorted(pending)


def _send(root, run_id, request, attempt, client, start_gate):
    started = start_gate()
    identity = dict(
        kind="terminal",
        request_id=request["request_id"],
        attempt=attempt,
        slot_sequence=request["sequence"],
        route=request["route"],
    )
    if started is None:
        return dict(
            identity,
            status="cancelled_before_post",
            status_code=None,
            complete=True,
            cost_usd=0.0,
            post_started=False,
            response_path=None,
            response_sha256=None,
            stored_response_sha256=None,
            observed=None,
            error=None,
            completed_monotonic=monotonic(),
        )
    code, complete, error, headers, chunks, size, retained_size = None, False, None, {}, [], 0, 0
    try:
        with client.stream("POST", URL, json=request["payload"]) as response:
            code = response.status_code
            headers = {
                key: response.headers[key]
                for key in ("content-type", "date", "x-request-id", "retry-after")
                if key in response.headers
            }
            for chunk in response.iter_bytes():
                size += len(chunk)
                kept = chunk[: max(0, MAX_RESPONSE - retained_size)]
                chunks.append(kept)
                retained_size += len(kept)
                if size > MAX_RESPONSE:
                    error = "response_byte_limit"
                    break
            else:
                complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    relative = (
        common.WORKSPACE / run_id / "responses" / f"{request['sequence']:04d}-a{attempt}.json.gz"
    )
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(gzip.compress(body, mtime=0))
        handle.flush()
        os.fsync(handle.fileno())
    observed, known_error = None, False
    status = "http_error" if complete else "outcome_uncertain"
    try:
        value = json.loads(body)
        known_error = isinstance(value, dict) and bool(value.get("error"))
    except (ValueError, UnicodeDecodeError):
        pass
    if complete and _refusal(body):
        status = "refused"
    elif complete and code is not None and 200 <= code < 300:
        try:
            observed = legacy.inspect_response(body)
            # Nonsquare, non-PNG and unrequested quality are retained, not regenerated.
            status = "image_returned" if observed["minimum_512"] else "delivery_below_minimum"
        except Exception as exc:
            status, error = "invalid_response", type(exc).__name__
    return dict(
        identity,
        status=status,
        status_code=code,
        complete=complete,
        error=error,
        cost_usd=legacy.cost_from_response(body, code, False),
        paid=False,
        response_path=str(relative),
        response_sha256=hashlib.sha256(body).hexdigest(),
        stored_response_sha256=hash_file(path),
        received_bytes=size,
        response_bytes=len(body),
        response_headers=headers,
        observed=observed,
        known_error_envelope=known_error,
        post_started=True,
        transport_started_monotonic=started,
        latency_seconds=max(0.0, monotonic() - started),
        completed_monotonic=monotonic(),
    )


def _stop_reason(row, recent, config):
    if row["status"] in ("outcome_uncertain", "invalid_response", "delivery_below_minimum"):
        return "unresolved_delivery"
    if row["status_code"] in (401, 402, 404) or (
        row["status_code"] == 403 and row["status"] != "refused"
    ):
        return "authentication_quota_or_contract_error"
    if sum(status != "image_returned" for status in recent) >= config["failure_stop_count"]:
        return "three_failed_attempts_in_eight_completed"
    return None


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
