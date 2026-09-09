"""One-shot mixed-route collection with durable reservations and bounded retries."""

import base64
import gzip
import hashlib
import io
import json
import math
import os
import shutil
import threading
import time
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from decimal import Decimal
from functools import partial
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_distribution_study_v1 import transport as legacy
from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    events,
    publish,
    stage_lock,
)
from latent_art_bench.painter_responsiveness_recovery_v1.collection import EXACT_BODY
from latent_art_bench.painter_responsiveness_v1.collection import _refusal, _retry_delay

from . import common

MAX_RESPONSE = 64 * 1024**2
RETRY_HTTP = (429, 500, 502, 503, 504)


def money(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid nonnegative accounting amount")
    return Decimal(str(value))


def technical_error(body, code, complete, media_type, route):
    if not complete or code not in RETRY_HTTP:
        return False
    if (
        route == "oauth_gpt_image_2"
        and code == 503
        and media_type.split(";", 1)[0].strip().lower() == "text/plain"
        and body == EXACT_BODY
    ):
        return True
    try:
        value = json.loads(body)
        error = value["error"]
        return (
            set(value) == {"error"}
            and isinstance(error, dict)
            and type(error.get("code")) is int
            and error["code"] == code
            and isinstance(error.get("message"), str)
            and bool(error["message"].strip())
        )
    except (ValueError, KeyError, TypeError):
        return False


def budget_state(root, baseline):
    known, reserved, pending, unknown, attempts = Decimal(0), Decimal(0), [], [], 0
    pending_paid = 0
    for path in sorted((root / common.MANIFESTS).glob("*/generation_events.jsonl")):
        intents, terminal = {}, {}
        for row in events(path):
            key = row["request_id"], row["attempt"]
            if row["kind"] == "attempt":
                if key in intents:
                    raise ValueError("duplicate intent")
                intents[key] = row
            elif row["kind"] == "terminal":
                if key not in intents or key in terminal:
                    raise ValueError("unpaired or duplicate terminal")
                terminal[key] = row
            else:
                raise ValueError("unknown collection event")
        attempts += len(intents)
        for key, intent in intents.items():
            row = terminal.get(key)
            paid = intent["paid"]
            if row is None:
                pending.append([path.parent.name, *key])
                if paid:
                    reserved += Decimal(5)
                    pending_paid += 1
            elif row.get("cost_usd") is not None:
                known += money(row["cost_usd"])
            elif paid:
                reserved += Decimal(5)
                if not row.get("recognized_technical_error"):
                    unknown.append([path.parent.name, *key])
    return dict(
        accounted_usd=float(money(baseline) + known + reserved),
        new_reported_usd=float(known),
        new_reserves_usd=float(reserved),
        pending=pending,
        unknown=unknown,
        attempts=attempts,
        pending_paid=pending_paid,
        terminal_reserves_usd=float(reserved - 5 * pending_paid),
    )


def can_admit(budget, paid, ceiling=75):
    return not budget["unknown"] and money(budget["accounted_usd"]) + (
        Decimal(5) if paid else Decimal(0)
    ) <= money(ceiling)


def retry_delay(row):
    return max(60.0, _retry_delay(row))


def can_credit_admit(budget, available):
    required = (
        money(budget["new_reported_usd"])
        + money(budget["terminal_reserves_usd"])
        + Decimal("0.07") * (budget["pending_paid"] + 1)
    )
    return required <= money(available)


class OrderedStartGate:
    """Ticketed admission preserves dispatch order even if workers start out of order."""

    def __init__(self, stop, interval, deadline):
        self.stop, self.interval, self.deadline = stop, interval, deadline
        self.condition = threading.Condition()
        self.next_ticket, self.last_start = 0, -math.inf

    def __call__(self, ticket):
        with self.condition:
            while not self.stop.is_set():
                now = time.monotonic()
                if now >= self.deadline:
                    self.stop.set()
                    self.condition.notify_all()
                    return None
                delay = self.last_start + self.interval - now
                if ticket == self.next_ticket and delay <= 0:
                    self.last_start = now
                    self.next_ticket += 1
                    self.condition.notify_all()
                    return now
                self.condition.wait(min(0.1, max(0.001, delay)) if delay > 0 else 0.1)
        return None


@contextmanager
def stopping_executor(stop):
    executor = ThreadPoolExecutor(max_workers=2)
    try:
        yield executor
    except BaseException:
        stop.set()
        raise
    finally:
        executor.shutdown(wait=True)


def inspect_response(body):
    observed = legacy.inspect_response(body)
    raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
    with Image.open(io.BytesIO(raw)) as im:
        if im.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError("transparent delivered image")
    return observed


def read_credits(secret, *, transport=None):
    with httpx.Client(timeout=30, follow_redirects=False, transport=transport) as client:
        response = client.get(
            "https://openrouter.ai/api/v1/credits", headers={"Authorization": "Bearer " + secret}
        )
    response.raise_for_status()
    value = response.json()["data"]
    total, used = money(value["total_credits"]), money(value["total_usage"])
    if used > total:
        raise ValueError("OpenRouter credit balance is exhausted")
    return dict(
        checked_at_utc=utc_now().isoformat(),
        total_credits=float(total),
        total_usage=float(used),
        available_usd=float(total - used),
    )


def _send(root, run_id, request, attempt, secret, start_gate, *, transport=None):
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
            complete=True,
            status_code=None,
            post_started=False,
            cost_usd=0.0,
            response_path=None,
            observed=None,
        )
    paid = request["route"] == "flux_2_max"
    headers = {"Authorization": "Bearer " + secret} if paid else {}
    url = legacy.OPENROUTER_URL if paid else legacy.OAUTH_URL
    chunks, size, code, complete, error, selected = [], 0, None, False, None, {}
    post_utc = utc_now().isoformat()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(240, connect=20),
            follow_redirects=False,
            transport=transport,
            headers=headers,
        ) as client:
            with client.stream("POST", url, json=request["payload"]) as response:
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
    if paid and (secret.encode() in body or any(secret in v for v in selected.values())):
        body, selected, error, complete = (
            b'{"credential_echo_suppressed":true}',
            {},
            "credential_echo",
            False,
        )
    relative = (
        common.WORKSPACE / run_id / "responses" / f"{request['sequence']:04d}-a{attempt}.json.gz"
    )
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(gzip.compress(body, mtime=0))
        handle.flush()
        os.fsync(handle.fileno())
    recognized = technical_error(
        body, code, complete, selected.get("content-type", ""), request["route"]
    )
    observed = None
    status = "http_error" if complete else "outcome_uncertain"
    if complete and _refusal(body):
        status = "refused"
    elif complete and code is not None and 200 <= code < 300:
        try:
            observed = inspect_response(body)
            status = "image_returned" if observed["minimum_512"] else "unsupported_success"
            if observed["reported"].get("model") not in (None, request["payload"]["model"]):
                status = "unsupported_success"
        except Exception as exc:
            status, error = "unsupported_success", type(exc).__name__
    cost = legacy.cost_from_response(body, code, paid) if complete else (None if paid else 0.0)
    return dict(
        identity,
        status=status,
        status_code=code,
        complete=complete,
        error=error,
        paid=paid,
        cost_usd=cost,
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
    if (
        row.get("paid")
        and row.get("cost_usd") is None
        and not row.get("recognized_technical_error")
    ):
        return "unknown_paid_cost"
    if row.get("cost_usd") is not None and row["cost_usd"] > 5:
        return "request_exceeded_reserved_cost"
    if row.get("status_code") in (401, 402, 404) or (
        row.get("status_code") in (400, 403, 422) and row["status"] != "refused"
    ):
        return "authentication_quota_or_contract_error"
    if sum(s != "image_returned" for s in recent) >= 3:
        return "three_failures_in_latest_eight"
    return None


def collect(root, run_id, proxy_root, *, transport=None, sleep=time.sleep):
    from . import workflow

    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".generation.lock"):
        freeze = workflow.verify(root, run_id)
        workflow.verify_live_metadata(root, freeze, proxy_root, transport=transport)
        requests, config = common.requests(root), freeze["config"]
        directory, workspace = root / common.directory(run_id), root / common.WORKSPACE / run_id
        ledger = directory / "generation_events.jsonl"
        if any(
            (directory / p).exists() for p in ("collection_receipt.json", "generation_events.jsonl")
        ):
            raise ValueError("collection already started or terminal; never resume")
        if workspace.exists():
            raise ValueError("existing workspace blocks one-shot collection")
        baseline = freeze["budget_baseline_usd"]
        initial = budget_state(root, baseline)
        if initial["pending"] or initial["unknown"]:
            raise ValueError("unreconciled namespace accounting blocks collection")
        secret = key_from_env(root)
        credits = read_credits(secret, transport=transport)
        expected = sum(r["route"] == "flux_2_max" for r in requests) * 0.07 + 8 * 0.07
        if credits["available_usd"] < expected:
            raise ValueError(
                "actual OpenRouter credit balance cannot cover the fixed paid allocation"
            )
        publish(
            directory / "credit_preflight.json",
            dict(credits, expected_with_retry_allowance_usd=expected),
        )
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
        start_gate = OrderedStartGate(
            stop, config["minimum_start_interval_seconds"], dispatch_deadline
        )
        recent, terminal, active = deque(maxlen=8), [], {}
        reason, caught = None, None

        def halt(value):
            nonlocal reason
            if reason is None:
                reason = value
                stop.set()
                append_event(directory / "operator_events.jsonl", dict(kind="halt", reason=value))

        def finish(future, queue):
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
                    observed=None,
                    paid=request["route"] == "flux_2_max",
                    cost_usd=None,
                    response_path=None,
                )
            row = append_event(ledger, result)
            terminal.append(row)
            if row.get("post_started", True):
                recent.append(row["status"])
            if value := stop_reason(row, recent):
                halt(value)
            eligible = (
                not reason
                and row["status"] == "http_error"
                and row.get("recognized_technical_error")
                and attempt == 1
                and retries < 8
            )
            if eligible:
                try:
                    delay = retry_delay(row)
                except ValueError:
                    halt("unsupported_retry_delay")
                    return
                retries += 1
                queue.appendleft((request, 2, time.monotonic() + delay))

        try:
            with stopping_executor(stop) as executor:
                blocks = [
                    [r for r in requests if r["block_order"] == i]
                    for i in range(1, max(r["block_order"] for r in requests) + 1)
                ]
                for block in blocks:
                    if reason or stop.is_set():
                        break
                    workflow.verify(root, run_id)
                    if legacy.proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
                        halt("proxy_identity_changed")
                        break
                    queue = deque((r, 1, 0.0) for r in block)
                    while queue or active:
                        if time.monotonic() >= dispatch_deadline:
                            halt("collection_deadline")
                        if stop.is_set() and reason is None:
                            halt("collection_deadline")
                        if (
                            not reason
                            and shutil.disk_usage(root).free < config["minimum_free_bytes"]
                        ):
                            halt("storage_reserve")
                        if (
                            not reason
                            and queue
                            and len(active) < 2
                            and queue[0][2] <= time.monotonic()
                        ):
                            request, attempt, _ = queue[0]
                            paid = request["route"] == "flux_2_max"
                            budget = budget_state(root, baseline)
                            if budget["attempts"] >= config["maximum_attempts"]:
                                halt("attempt_limit")
                            elif not can_admit(budget, paid):
                                if not active:
                                    halt("budget_reserve")
                            elif paid and not can_credit_admit(budget, credits["available_usd"]):
                                if not active:
                                    halt("actual_credit_reserve")
                            else:
                                queue.popleft()
                                append_event(
                                    ledger,
                                    dict(
                                        kind="attempt",
                                        request_id=request["request_id"],
                                        attempt=attempt,
                                        slot_sequence=request["sequence"],
                                        route=request["route"],
                                        paid=paid,
                                        reserved_usd=5 if paid else 0,
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
                                    secret,
                                    partial(start_gate, ticket),
                                    transport=transport,
                                )
                                ticket += 1
                                active[future] = request, attempt
                        if active:
                            completed, _ = wait(active, timeout=0.1, return_when=FIRST_COMPLETED)
                            for future in completed:
                                finish(future, queue)
                        elif reason:
                            break
                        else:
                            sleep(0.1)
                        if reason:
                            queue.clear()
        except BaseException as exc:
            caught = exc
            halt("interrupted_" + type(exc).__name__)
            for future in list(active):
                finish(future, deque())
        finally:
            secret = None
            slots = []
            for request in requests:
                attempts = [r for r in terminal if r["request_id"] == request["request_id"]]
                success = [r for r in attempts if r["status"] == "image_returned"]
                if len(success) > 1:
                    raise ValueError("multiple successful outputs for a slot")
                chosen = success[0] if success else attempts[-1] if attempts else None
                slots.append(
                    dict(
                        request_id=request["request_id"],
                        sequence=request["sequence"],
                        status=chosen["status"] if chosen else "not_attempted_collection_stopped",
                        selected_attempt=chosen["attempt"] if success else None,
                        response_path=chosen.get("response_path") if success else None,
                        response_sha256=chosen.get("response_sha256") if success else None,
                        observed=chosen.get("observed") if success else None,
                    )
                )
            publish(directory / "slot_outcomes.jsonl", slots, lines=True)
            outputs = [
                directory / "generation_events.jsonl",
                directory / "slot_outcomes.jsonl",
                directory / "credit_preflight.json",
            ]
            if (directory / "operator_events.jsonl").exists():
                outputs.append(directory / "operator_events.jsonl")
            elapsed = time.monotonic() - started
            if elapsed > config["maximum_collection_seconds"]:
                reason = reason or "collection_duration_contract_exceeded"
            receipt = dict(
                run_id=run_id,
                status="stopped" if reason else "complete",
                reason=reason,
                ended_at_utc=utc_now().isoformat(),
                elapsed_seconds=elapsed,
                duration_contract_met=elapsed <= config["maximum_collection_seconds"],
                planned=len(requests),
                attempts=len(terminal),
                retries=sum(r["attempt"] == 2 and r.get("post_started", True) for r in terminal),
                retry_decisions=retries,
                retry_intents=sum(r["attempt"] == 2 for r in terminal),
                posted_attempts=sum(r.get("post_started", True) for r in terminal),
                slot_counts=dict(Counter(s["status"] for s in slots)),
                budget=budget_state(root, baseline),
                outputs=[dict(path=str(p.relative_to(root)), sha256=hash_file(p)) for p in outputs],
            )
            publish(directory / "collection_receipt.json", receipt)
        if caught:
            raise caught
        return receipt
