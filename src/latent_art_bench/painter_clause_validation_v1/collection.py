"""OAuth-only one-shot collection; real dispatch requires an explicit live flag."""

import gzip
import hashlib
import json
import os
import queue as queues
import shutil
import threading
import time
from collections import Counter, deque
from functools import partial
from pathlib import Path

import httpx

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_distribution_study_v1 import transport as legacy
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    events,
    publish,
    stage_lock,
)
from latent_art_bench.painter_naming_replication_v1.collection import (
    OrderedStartGate,
    inspect_response,
    retry_delay,
    stopping_executor,
    technical_error,
)
from latent_art_bench.painter_responsiveness_v1.collection import _refusal

from . import common

MAX_RESPONSE = 64 * 1024**2
OAUTH_ROUTE = "oauth_gpt_image_2"
HISTORICAL_ACCOUNTED_USD = 50.7219185


def validate_inventory(requests, config):
    if not requests or len(requests) != config["maximum_images"]:
        raise ValueError("complete frozen OAuth allocation required")
    if len({r["request_id"] for r in requests}) != len(requests) or [
        r["sequence"] for r in requests
    ] != list(range(len(requests))):
        raise ValueError("duplicate or reordered request identity")
    if any(
        r["route"] != OAUTH_ROUTE or r["payload"].get("model") != "gpt-image-2" for r in requests
    ):
        raise ValueError("only the fixed OAuth route and model are permitted")
    blocks = []
    for request in requests:
        if not blocks or blocks[-1][0]["block_id"] != request["block_id"]:
            blocks.append([])
        blocks[-1].append(request)
    if len({b[0]["block_id"] for b in blocks}) != len(blocks):
        raise ValueError("request blocks are not contiguous")
    for order, block in enumerate(blocks, 1):
        if any(r["block_order"] != order for r in block) or [
            r["within_block"] for r in block
        ] != list(range(len(block))):
            raise ValueError("invalid frozen block order")
    return blocks


def namespace_state(root):
    """Audit this namespace's attempts without reading any paid account or key."""
    pending, attempts = [], 0
    for path in sorted((Path(root) / common.MANIFESTS).glob("*/generation_events.jsonl")):
        intents, terminals = set(), set()
        for row in events(path):
            key = row["request_id"], row["attempt"]
            if row["route"] != OAUTH_ROUTE or row.get("paid") is not False:
                raise ValueError("non-OAuth or paid event in OAuth-only namespace")
            if row["kind"] == "attempt":
                if key in intents or row["reserved_usd"] != 0:
                    raise ValueError("duplicate or nonzero reservation")
                intents.add(key)
            elif row["kind"] == "terminal":
                if key not in intents or key in terminals or row["cost_usd"] != 0:
                    raise ValueError("unpaired terminal or paid accounting")
                terminals.add(key)
            else:
                raise ValueError("unknown collection event")
        pending.extend([path.parent.name, *key] for key in sorted(intents - terminals))
        attempts += len(intents)
    return dict(
        accounted_usd=HISTORICAL_ACCOUNTED_USD,
        new_reported_usd=0.0,
        new_reserves_usd=0.0,
        attempts=attempts,
        pending=pending,
        subscription_monetary_value=None,
    )


def _send(root, run_id, request, attempt, start_gate, *, transport=None):
    if request["route"] != OAUTH_ROUTE or request["payload"].get("model") != "gpt-image-2":
        raise ValueError("non-OAuth dispatch rejected")
    identity = dict(
        kind="terminal",
        request_id=request["request_id"],
        attempt=attempt,
        slot_sequence=request["sequence"],
        route=OAUTH_ROUTE,
        paid=False,
        cost_usd=0.0,
    )
    started = start_gate()
    if started is None:
        return dict(
            identity,
            status="cancelled_before_post",
            complete=True,
            status_code=None,
            post_started=False,
            response_path=None,
            observed=None,
        )
    chunks, size, code, complete, error, selected = [], 0, None, False, None, {}
    post_utc = utc_now().isoformat()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(240, connect=20), follow_redirects=False, transport=transport
        ) as client:
            with client.stream("POST", legacy.OAUTH_URL, json=request["payload"]) as response:
                code = response.status_code
                selected = {
                    k: response.headers[k]
                    for k in ("content-type", "date", "x-request-id", "retry-after")
                    if k in response.headers
                }
                for chunk in response.iter_bytes():
                    chunks.append(chunk[: max(0, MAX_RESPONSE - size)])
                    size += len(chunk)
                    if size > MAX_RESPONSE:
                        error = "response_byte_limit"
                        break
                else:
                    complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    relative = (
        common.WORKSPACE / run_id / "responses" / (f"{request['sequence']:04d}-a{attempt}.json.gz")
    )
    path = Path(root) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(gzip.compress(body, mtime=0))
        handle.flush()
        os.fsync(handle.fileno())
    recognized = technical_error(
        body, code, complete, selected.get("content-type", ""), OAUTH_ROUTE
    )
    observed = None
    status = "http_error" if complete else "outcome_uncertain"
    if complete and _refusal(body):
        status = "refused"
    elif complete and code is not None and 200 <= code < 300:
        try:
            observed = inspect_response(body)
            status = "image_returned" if observed["minimum_512"] else "unsupported_success"
            if observed["reported"].get("model") not in (None, "gpt-image-2"):
                status = "unsupported_success"
        except Exception as exc:
            status, error = "unsupported_success", type(exc).__name__
    return dict(
        identity,
        status=status,
        status_code=code,
        complete=complete,
        error=error,
        recognized_technical_error=recognized,
        response_path=str(relative),
        response_sha256=hashlib.sha256(body).hexdigest(),
        stored_response_sha256=hash_file(path),
        response_bytes=len(body),
        received_bytes=size,
        response_headers=selected,
        observed=observed,
        post_started=True,
        post_started_at_utc=post_utc,
        transport_started_monotonic=started,
        latency_seconds=time.monotonic() - started,
    )


def stop_reason(row, recent):
    if row["status"] in ("outcome_uncertain", "unsupported_success"):
        return "uncertain_or_unsupported_delivery"
    if row.get("status_code") in (401, 402, 404) or (
        row.get("status_code") in (400, 403, 422) and row["status"] != "refused"
    ):
        return "authentication_quota_or_contract_error"
    if row["status"] == "http_error" and not row.get("recognized_technical_error"):
        return "unrecognized_backend_error"
    if sum(s != "image_returned" for s in recent) >= 3:
        return "three_failures_in_latest_eight"
    return None


def invalidates_identity(reason):
    return reason in {
        "proxy_identity_changed",
        "authentication_quota_or_contract_error",
        "uncertain_or_unsupported_delivery",
        "unrecognized_backend_error",
    } or (
        isinstance(reason, str)
        and reason.startswith(("interrupted_", "final_identity_check_failed_"))
    )


def collect(root, run_id, proxy_root, *, live=False, transport=None, sleep=time.sleep):
    from . import workflow

    if live is not True and not isinstance(transport, httpx.MockTransport):
        raise ValueError("real OAuth collection requires explicit live=True")
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".generation.lock"):
        freeze = workflow.verify(root, run_id)
        workflow.verify_live_metadata(root, freeze, proxy_root)
        requests, config = common.requests(root), freeze["config"]
        blocks = validate_inventory(requests, config)
        if config["historical_accounted_usd"] != HISTORICAL_ACCOUNTED_USD:
            raise ValueError("historical accounting must remain unchanged")
        directory = root / common.directory(run_id)
        workspace = root / common.WORKSPACE / run_id
        ledger = directory / "generation_events.jsonl"
        if any(
            (directory / p).exists()
            for p in ("collection_receipt.json", "generation_events.jsonl", "slot_outcomes.jsonl")
        ):
            raise ValueError("collection already started or terminal; never resume")
        if workspace.exists():
            raise ValueError("existing workspace blocks one-shot collection")
        initial = namespace_state(root)
        if initial["pending"]:
            raise ValueError("unresolved transport intent blocks collection")
        publish(
            workspace / "collection_started.json",
            dict(
                started_at_utc=utc_now().isoformat(),
                freeze_sha256=hash_file(directory / "freeze.json"),
                one_shot=True,
            ),
        )
        with ledger.open("x", encoding="utf-8") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        started, retries, ticket = time.monotonic(), 0, 0
        stop = threading.Event()
        dispatch_deadline = started + config["maximum_collection_seconds"] - 300
        gate = OrderedStartGate(stop, config["minimum_start_interval_seconds"], dispatch_deadline)
        recent, terminal, active = deque(maxlen=8), [], {}
        completed = queues.Queue()
        reason, caught = None, None
        identity_met = True

        def halt(value):
            nonlocal reason, identity_met
            if identity_met and invalidates_identity(value):
                identity_met = False
                append_event(
                    directory / "operator_events.jsonl",
                    dict(kind="identity_contract_failure", reason=value),
                )
            if reason is None:
                reason = value
                stop.set()
                append_event(directory / "operator_events.jsonl", dict(kind="halt", reason=value))

        def finish(future, waiting):
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
                    route=OAUTH_ROUTE,
                    status="outcome_uncertain",
                    status_code=None,
                    complete=False,
                    error=type(exc).__name__,
                    observed=None,
                    paid=False,
                    cost_usd=0.0,
                    response_path=None,
                )
            row = append_event(ledger, result)
            terminal.append(row)
            if row.get("post_started", True):
                recent.append(row["status"])
            if value := stop_reason(row, recent):
                halt(value)
            if (
                not reason
                and row["status"] == "http_error"
                and row.get("recognized_technical_error")
                and attempt == 1
            ):
                if retries >= config["maximum_technical_retries"]:
                    halt("technical_retry_limit")
                    return
                try:
                    delay = retry_delay(row)
                except ValueError:
                    halt("unsupported_retry_delay")
                    return
                retries += 1
                waiting.appendleft((request, 2, time.monotonic() + delay))

        try:
            with stopping_executor(stop) as executor:
                for block in blocks:
                    if reason or stop.is_set():
                        break
                    workflow.verify(root, run_id)
                    if legacy.proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
                        halt("proxy_identity_changed")
                        break
                    waiting = deque((r, 1, 0.0) for r in block)
                    while waiting or active:
                        if time.monotonic() >= dispatch_deadline or (stop.is_set() and not reason):
                            halt("collection_deadline")
                        if (
                            not reason
                            and shutil.disk_usage(root).free < config["minimum_free_bytes"]
                        ):
                            halt("storage_reserve")
                        if (
                            not reason
                            and waiting
                            and len(active) < config["maximum_in_flight"]
                            and waiting[0][2] <= time.monotonic()
                        ):
                            if ticket >= config["maximum_attempts"]:
                                halt("attempt_limit")
                            else:
                                request, attempt, _ = waiting.popleft()
                                append_event(
                                    ledger,
                                    dict(
                                        kind="attempt",
                                        request_id=request["request_id"],
                                        attempt=attempt,
                                        slot_sequence=request["sequence"],
                                        route=OAUTH_ROUTE,
                                        paid=False,
                                        reserved_usd=0,
                                        dispatch_ticket=ticket,
                                        payload_sha256=hashlib.sha256(
                                            json.dumps(request["payload"], sort_keys=True).encode()
                                        ).hexdigest(),
                                    ),
                                )
                                future = executor.submit(
                                    _send,
                                    root,
                                    run_id,
                                    request,
                                    attempt,
                                    partial(gate, ticket),
                                    transport=transport,
                                )
                                ticket += 1
                                active[future] = request, attempt
                                future.add_done_callback(completed.put)
                        if active:
                            try:
                                finish(completed.get(timeout=0.1), waiting)
                            except queues.Empty:
                                pass
                        elif reason:
                            break
                        else:
                            sleep(0.1)
                        if reason:
                            waiting.clear()
        except BaseException as exc:
            caught = exc
            halt("interrupted_" + type(exc).__name__)
            # stopping_executor has stopped admission and drained every worker.
            while active:
                finish(completed.get(), deque())
        finally:
            final_identity = dict(
                kind="final_identity_check", source_verified=False, proxy_verified=False
            )
            try:
                workflow.verify(root, run_id)
                final_identity["source_verified"] = True
                final_identity["proxy_verified"] = (
                    legacy.proxy_snapshot(proxy_root) == freeze["proxy_snapshot"]
                )
                if not final_identity["proxy_verified"]:
                    halt("proxy_identity_changed")
            except BaseException as exc:
                final_identity["error_type"] = type(exc).__name__
                halt("final_identity_check_failed_" + type(exc).__name__)
                if not isinstance(exc, Exception):
                    caught = caught or exc
            append_event(directory / "operator_events.jsonl", final_identity)
            slots = []
            for request in requests:
                attempts = [r for r in terminal if r["request_id"] == request["request_id"]]
                successes = [r for r in attempts if r["status"] == "image_returned"]
                if len(successes) > 1:
                    raise ValueError("multiple successful outputs for one slot")
                chosen = successes[0] if successes else attempts[-1] if attempts else None
                slots.append(
                    dict(
                        request_id=request["request_id"],
                        sequence=request["sequence"],
                        status=chosen["status"] if chosen else "not_attempted_collection_stopped",
                        selected_attempt=chosen["attempt"] if successes else None,
                        response_path=chosen.get("response_path") if successes else None,
                        response_sha256=chosen.get("response_sha256") if successes else None,
                        observed=chosen.get("observed") if successes else None,
                    )
                )
            publish(directory / "slot_outcomes.jsonl", slots, lines=True)
            outputs = [
                ledger,
                directory / "slot_outcomes.jsonl",
                workspace / "collection_started.json",
            ]
            if (directory / "operator_events.jsonl").exists():
                outputs.append(directory / "operator_events.jsonl")
            elapsed = time.monotonic() - started
            if elapsed > config["maximum_collection_seconds"]:
                reason = reason or "collection_duration_contract_exceeded"
            receipt = dict(
                schema="painter-clause-validation-collection/1",
                run_id=run_id,
                freeze_sha256=hash_file(directory / "freeze.json"),
                status="stopped" if reason else "complete",
                reason=reason,
                ended_at_utc=utc_now().isoformat(),
                elapsed_seconds=elapsed,
                duration_contract_met=elapsed <= config["maximum_collection_seconds"],
                identity_contract_met=identity_met
                and final_identity["source_verified"]
                and final_identity["proxy_verified"],
                planned=len(requests),
                attempts=len(terminal),
                retries=sum(r["attempt"] == 2 and r.get("post_started", True) for r in terminal),
                retry_decisions=retries,
                retry_intents=sum(r["attempt"] == 2 for r in terminal),
                posted_attempts=sum(r.get("post_started", True) for r in terminal),
                slot_counts=dict(Counter(s["status"] for s in slots)),
                budget=namespace_state(root),
                outputs=[dict(path=str(p.relative_to(root)), sha256=hash_file(p)) for p in outputs],
            )
            publish(directory / "collection_receipt.json", receipt)
        if caught:
            raise caught
        return receipt
