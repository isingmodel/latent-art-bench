"""Single R10 paid FLUX collection with conditional full-grid admission.

Bounded adaptation of the frozen clause-v1 state machine. This namespace never
writes a predecessor path or repairs a predecessor slot.
"""

import gzip
import hashlib
import json
import math
import os
import queue as queues
import shutil
import threading
import time
from collections import Counter, deque
from decimal import Decimal
from functools import partial
from pathlib import Path

import httpx

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_distribution_study_v1 import transport as legacy
from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
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
ROUTE = common.ROUTE
HISTORICAL_ACCOUNTED_USD = 50.7219185


def validate_inventory(requests, config):
    return common.validate_design(requests, config)


def cost_record(body, code, complete):
    """Separate reported charge from the inherited explicit-client-rejection convention."""
    if not complete:
        return None, "unresolved"
    try:
        value = json.loads(body)
    except (ValueError, TypeError):
        return None, "unresolved"
    if not isinstance(value, dict):
        return None, "unresolved"
    usage = value.get("usage")
    supplied = usage.get("cost") if isinstance(usage, dict) else None
    if type(supplied) in (float, int):
        cost = Decimal(str(supplied))
        if cost.is_finite() and cost >= 0:
            return float(cost), "provider_reported"
    error = value.get("error")
    if (
        code in (400, 401, 402, 403, 404, 422, 429)
        and set(value) == {"error"}
        and isinstance(error, dict)
        and isinstance(error.get("message"), str)
        and error["message"].strip()
    ):
        return 0.0, "retained_explicit_client_rejection"
    return None, "unresolved"


def namespace_state(root):
    """Known charges and unreconciled $5 paid liabilities, from durable event chains."""
    intents, terminal = {}, {}
    for path in sorted((Path(root) / common.MANIFESTS).glob("*/generation_events.jsonl")):
        for row in events(path):
            key = (path.parent.name, row["request_id"], row["attempt"])
            if row["route"] != ROUTE or row.get("paid") is not True:
                raise ValueError("unexpected paid route")
            if row["kind"] == "attempt":
                if key in intents or row["reserved_usd"] != 5:
                    raise ValueError("duplicate or altered reservation")
                intents[key] = row
            elif row["kind"] == "terminal":
                if key not in intents or key in terminal:
                    raise ValueError("unpaired terminal")
                terminal[key] = row
            else:
                raise ValueError("unknown ledger event")
    pending = sorted(set(intents) - set(terminal))
    unknown = sorted(k for k, r in terminal.items() if r["cost_usd"] is None)
    known = Decimal("0")
    for row in terminal.values():
        if row["cost_usd"] is not None:
            if type(row["cost_usd"]) not in (int, float):
                raise ValueError("numeric reported charge required")
            cost = Decimal(str(row["cost_usd"]))
            if not cost.is_finite() or cost < 0:
                raise ValueError("invalid retained charge")
            known += cost
    reserve = Decimal(5 * (len(pending) + len(unknown)))
    return dict(
        accounted_usd=float(Decimal("50.7219185") + known + reserve),
        new_reported_usd=float(known),
        new_reserves_usd=float(reserve),
        terminal_reserves_usd=5 * len(unknown),
        pending_paid=len(pending),
        attempts=len(intents),
        settled_attempts=len(terminal),
        pending=[list(k) for k in pending],
        unknown=[list(k) for k in unknown],
    )


def admission(state, config, available):
    """Forecast the still permitted full plan; separately honor $5 in-flight exposure.

    Pending attempts occur once at the planning allowance in the credit forecast.
    Their $5 liabilities are independently enforced against the project ceiling.
    Temporary ceiling pressure waits for a current worker; permanent deficits stop.
    """
    known = Decimal(str(state["new_reported_usd"]))
    unknown = Decimal(str(state["terminal_reserves_usd"]))
    remaining = config["maximum_attempts"] - state["settled_attempts"]
    forecast = known + unknown + Decimal(str(config["planning_attempt_usd"])) * remaining
    if state["unknown"]:
        return "stop_unknown_cost"
    if forecast > Decimal(str(available)) or Decimal("50.7219185") + forecast > Decimal("75"):
        return "stop_remaining_full_grid_budget"
    if Decimal(str(state["accounted_usd"])) + Decimal("5") > Decimal("75"):
        return "wait_in_flight_reserve" if state["pending"] else "stop_project_reserve"
    return "admit"


def eligibility(receipt):
    reasons = []
    if receipt["status"] != "complete":
        reasons.append("collection_stopped")
    if receipt["identity_contract_met"] is not True:
        reasons.append("identity_contract_unverified")
    if receipt["duration_contract_met"] is not True:
        reasons.append("duration_contract_failed")
    if receipt["timing_contract_met"] is not True:
        reasons.append("admission_timing_contract_failed")
    if receipt["planned"] != 240 or receipt["slot_counts"] != {"image_returned": 240}:
        reasons.append("incomplete_delivery_grid")
    if receipt["budget"]["pending"] or receipt["budget"]["unknown"]:
        reasons.append("unresolved_paid_accounting")
    budget = receipt["budget"]
    if Decimal(str(budget["accounted_usd"])) > Decimal("75") or Decimal(
        str(budget["new_reported_usd"])
    ) + Decimal(str(budget["new_reserves_usd"])) > Decimal(receipt["available_at_dispatch_usd"]):
        reasons.append("terminal_budget_exceeded")
    return dict(analysis_eligible=not reasons, analysis_unavailability_reasons=reasons)


def timing_contract(terminals, interval=5):
    if any(type(r.get("post_started", True)) is not bool for r in terminals):
        return False
    posted = [r for r in terminals if r.get("post_started", True)]
    if any(
        type(r.get("transport_started_monotonic")) not in (int, float)
        or type(r.get("latency_seconds")) not in (int, float)
        or not math.isfinite(r["transport_started_monotonic"])
        or not math.isfinite(r["latency_seconds"])
        or r["latency_seconds"] < 0
        for r in posted
    ):
        return False
    posted.sort(key=lambda r: r["transport_started_monotonic"])
    starts = [r["transport_started_monotonic"] for r in posted]
    if any(b - a < interval - 1e-9 for a, b in zip(starts, starts[1:])):
        return False
    return all(
        sum(
            q["transport_started_monotonic"]
            <= r["transport_started_monotonic"]
            < q["transport_started_monotonic"] + q["latency_seconds"]
            for q in posted
        )
        <= 2
        for r in posted
    )


def _send(root, run_id, request, attempt, start_gate, *, secret, transport=None):
    if request["route"] != ROUTE or request["payload"].get("model") != common.MODEL:
        raise ValueError("unqualified FLUX dispatch rejected")
    identity = dict(
        kind="terminal",
        request_id=request["request_id"],
        attempt=attempt,
        slot_sequence=request["sequence"],
        route=ROUTE,
        paid=True,
    )
    started = start_gate()
    if started is None:
        return dict(
            identity,
            status="cancelled_before_post",
            cost_usd=0.0,
            cost_basis="cancelled_before_post",
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
            timeout=httpx.Timeout(240, connect=20),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        ) as client:
            with client.stream(
                "POST",
                legacy.OPENROUTER_URL,
                json=request["payload"],
                headers={"Authorization": "Bearer " + secret},
            ) as response:
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
    recognized = technical_error(body, code, complete, selected.get("content-type", ""), ROUTE)
    observed = None
    status = "http_error" if complete else "outcome_uncertain"
    if complete and _refusal(body):
        status = "refused"
    elif complete and code is not None and 200 <= code < 300:
        try:
            observed = inspect_response(body)
            status = "image_returned" if observed["minimum_512"] else "unsupported_success"
            if observed["reported"].get("model") not in (None, common.MODEL):
                status = "unsupported_success"
        except Exception as exc:
            status, error = "unsupported_success", type(exc).__name__
    cost, basis = cost_record(body, code, complete)
    return dict(
        identity,
        cost_usd=cost,
        cost_basis=basis,
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
        "endpoint_identity_changed",
        "authentication_quota_or_contract_error",
        "uncertain_or_unsupported_delivery",
        "unrecognized_backend_error",
    } or (
        isinstance(reason, str)
        and reason.startswith(("interrupted_", "final_identity_check_failed_"))
    )


def collect(root, run_id, *, live=False, transport=None, sleep=time.sleep):
    from . import workflow

    if live is not True and not isinstance(transport, httpx.MockTransport):
        raise ValueError("real paid collection requires explicit live=True")
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".generation.lock"):
        freeze = workflow.verify(root, run_id)
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
        if initial["pending"] or initial["unknown"] or initial["attempts"]:
            raise ValueError("unresolved transport intent blocks collection")
        dispatch, available = workflow.dispatch_metadata(root, freeze, transport=transport)
        workflow.verify(root, run_id)
        secret = key_from_env(root)
        publish(
            workspace / "collection_started.json",
            dict(
                started_at_utc=utc_now().isoformat(),
                freeze_sha256=hash_file(directory / "freeze.json"),
                one_shot=True,
                dispatch_metadata_sha256=hash_file(
                    root / common.MANIFESTS / "metadata" / common.DISPATCH_ID / "receipt.json"
                ),
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
                    route=ROUTE,
                    status="outcome_uncertain",
                    status_code=None,
                    complete=False,
                    error=type(exc).__name__,
                    observed=None,
                    paid=True,
                    cost_usd=None,
                    cost_basis="unresolved",
                    response_path=None,
                )
            row = append_event(ledger, result)
            terminal.append(row)
            if row.get("post_started", True):
                recent.append(row["status"])
            if value := stop_reason(row, recent):
                halt(value)
            if row["cost_usd"] is None:
                halt("unknown_paid_cost")
            elif row["cost_usd"] > config["request_reservation_usd"]:
                halt("reported_cost_exceeds_reservation")
            if row["status"] == "refused" or (row["status"] == "http_error" and attempt == 2):
                halt("required_slot_unavailable")
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
                            decision = admission(namespace_state(root), config, available)
                            if decision.startswith("stop_"):
                                halt(decision)
                            elif decision.startswith("wait_"):
                                pass
                            elif ticket >= config["maximum_attempts"]:
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
                                        route=ROUTE,
                                        paid=True,
                                        reserved_usd=5,
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
                                    secret=secret,
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
                kind="final_identity_check", source_verified=False, endpoint_verified=False
            )
            try:
                workflow.verify(root, run_id)
                final_identity["source_verified"] = True
                workflow.verify_dispatch_metadata(root, freeze)
                final_identity["endpoint_verified"] = True
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
                root / common.MANIFESTS / "metadata" / common.DISPATCH_ID / "receipt.json",
                root / common.MANIFESTS / "metadata" / common.DISPATCH_ID / "started.json",
            ]
            if (directory / "operator_events.jsonl").exists():
                outputs.append(directory / "operator_events.jsonl")
            elapsed = time.monotonic() - started
            if elapsed > config["maximum_collection_seconds"]:
                reason = reason or "collection_duration_contract_exceeded"
            receipt = dict(
                schema="painter-map-validation-collection/2",
                run_id=run_id,
                freeze_sha256=hash_file(directory / "freeze.json"),
                status="stopped" if reason else "complete",
                reason=reason,
                ended_at_utc=utc_now().isoformat(),
                elapsed_seconds=elapsed,
                duration_contract_met=elapsed <= config["maximum_collection_seconds"],
                timing_contract_met=timing_contract(terminal),
                available_at_dispatch_usd=str(available),
                identity_contract_met=identity_met
                and final_identity["source_verified"]
                and final_identity["endpoint_verified"],
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
            receipt.update(eligibility(receipt))
            publish(directory / "collection_receipt.json", receipt)
        if caught:
            raise caught
        return receipt
