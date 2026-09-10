"""Scheduled research slots, bounded conditional retry censuses, and failure stops."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import shutil
import time
from collections import Counter
from email.utils import parsedate_to_datetime
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    digest,
    events,
    publish,
    stage_lock,
)

from . import study as s
from . import transport as t

TRANSIENT = {429, 500, 502, 503, 504}


def read_response(root, row):
    path = root / row["response_path"]
    if hash_file(path) != row["retained_sha256"]:
        raise ValueError("retained generation response changed")
    body = gzip.decompress(path.read_bytes())
    import hashlib

    if hashlib.sha256(body).hexdigest() != row["response_sha256"]:
        raise ValueError("decoded generation response changed")
    return body


def retry_eligible(root, row):
    if (
        not row["complete"]
        or row["cost_usd"] is None
        or row["status"] != "http_error"
        or row["status_code"] not in TRANSIENT
    ):
        return False
    try:
        result = json.loads(read_response(root, row))
    except (ValueError, OSError):
        return False
    return isinstance(result, dict) and bool(result.get("error")) and not result.get("data")


def retry_delay(row, now):
    value = row.get("response_headers", {}).get("retry-after")
    if value is None:
        return 60.0
    try:
        delay = float(value)
    except ValueError:
        try:
            delay = parsedate_to_datetime(value).timestamp() - now
        except (ValueError, TypeError, OverflowError):
            raise ValueError("unrecognized Retry-After; investigate before resending") from None
    if not math.isfinite(delay):
        raise ValueError("nonfinite Retry-After")
    return max(60.0, delay)


def failure_cluster(initial_terminals, route):
    failed = [r["status"] != "image_returned" for r in initial_terminals if r["route"] == route]
    return (len(failed) >= 3 and all(failed[-3:])) or (len(failed) >= 20 and sum(failed[-20:]) >= 4)


def stop_reason(row):
    if not row["complete"] or row["status"] == "outcome_uncertain" or row["cost_usd"] is None:
        return "uncertain_outcome_or_charge"
    if row["cost_usd"] > t.REQUEST_RESERVATION:
        return "charge_exceeded_reservation"
    if row["status"] in ("invalid_response", "invalid_geometry"):
        return "unexpected_successful_response"
    if row["status_code"] in (400, 401, 402, 403, 404, 405, 415, 422):
        return "authentication_payment_or_payload_contract"
    if row["status_code"] and 300 <= row["status_code"] < 400:
        return "unexpected_redirect"
    return None


def check_resources(root, request):
    budget = t.budget_state(root)
    paid = t.ROUTES[request["route"]][1] is not None
    if budget["unresolved"] or budget["uncertain"]:
        raise ValueError("unresolved outcome or charge blocks dispatch")
    if budget["attempts"] >= 1050 or (paid and budget["paid_attempts"] >= 612):
        raise ValueError("bounded attempt allocation exhausted")
    if paid and budget["accounted_usd"] + t.REQUEST_RESERVATION > 75:
        raise ValueError("study spending reserve reached")
    if shutil.disk_usage(root).free < t.MIN_FREE + t.MAX_RESPONSE:
        raise OSError("storage reserve reached")
    return paid


def send_once(root, run_id, request, freeze, proxy_root, *, transport=None, sleep=time.sleep):
    ledger = root / t.MANIFESTS / run_id / "generation_events.jsonl"
    rows = events(ledger)
    if any(r["request_id"] == request["request_id"] for r in rows):
        raise ValueError("attempt already exists; never redispatch")
    raw_path = root / t.WORKSPACE / run_id / "responses" / (request["request_id"] + ".json.gz")
    if raw_path.exists():
        raise ValueError("orphan response exists; reconcile before dispatch")
    paid = check_resources(root, request)
    if not paid and t.proxy_snapshot(proxy_root) != freeze["proxy_source"]:
        raise ValueError("OAuth source/listener changed; investigate before dispatch")
    sleep(15)
    append_event(
        ledger,
        dict(
            kind="attempt",
            request_id=request["request_id"],
            route=request["route"],
            paid=paid,
            request_sha256=digest(request),
            reservation_usd=t.REQUEST_RESERVATION if paid else 0.0,
        ),
    )
    result = t._send(root, run_id, request, transport=transport)
    return append_event(ledger, result)


def child_identity(request):
    return s.RUN_ID + "-retry-" + request["request_id"], request["request_id"] + "-retry1"


def retry_count(root):
    return sum(
        sum(r["kind"] == "attempt" for r in events(p))
        for p in (root / t.MANIFESTS).glob(s.RUN_ID + "-retry-*/generation_events.jsonl")
    )


def retry_once(
    root,
    request,
    predecessor,
    freeze,
    proxy_root,
    *,
    transport=None,
    sleep=time.sleep,
    now=time.time,
):
    run_id, request_id = child_identity(request)
    directory = root / t.MANIFESTS / run_id
    authority_path = directory / "retry_authority.json"
    child = dict(request, request_id=request_id, predecessor_request_id=request["request_id"])
    expected = dict(
        run_id=run_id,
        parent_run_id=s.RUN_ID,
        request=child,
        main_freeze_sha256=hash_file(root / s.DIRECTORY / "main_freeze.json"),
        predecessor_terminal=predecessor,
        predecessor_terminal_sha256=predecessor["event_sha256"],
        conditional_rule="MAIN.md and RETRY_AMENDMENT.md, at most one transient retry per slot",
    )
    if not authority_path.exists():
        if retry_count(root) >= 24:
            return None
        if not retry_eligible(root, predecessor):
            raise ValueError("predecessor does not qualify for a technical retry")
        publish(
            authority_path, dict(expected, not_before_unix=now() + retry_delay(predecessor, now()))
        )
    authority = read_json(authority_path)
    if {k: authority[k] for k in expected} != expected:
        raise ValueError("retry authority differs from its predecessor")
    rows = events(directory / "generation_events.jsonl")
    if rows:
        if len(rows) != 2 or rows[-1]["kind"] != "terminal":
            raise ValueError("unresolved child attempt; never retry it again")
        return rows[-1]
    if (directory / "generation_receipt.json").exists():
        raise ValueError("terminal child census cannot be dispatched")
    while now() < authority["not_before_unix"]:
        sleep(min(60, authority["not_before_unix"] - now()))
    result = send_once(root, run_id, child, freeze, proxy_root, transport=transport, sleep=sleep)
    publish(
        directory / "generation_receipt.json",
        dict(
            run_id=run_id,
            status=result["status"],
            request_id=request_id,
            authority_sha256=hash_file(authority_path),
            events_sha256=hash_file(directory / "generation_events.jsonl"),
            parent_terminal_sha256=predecessor["event_sha256"],
        ),
    )
    return result


def close(root, status, reason, requests):
    directory = root / s.DIRECTORY
    rows = events(directory / "slot_events.jsonl")
    complete = {r["request_id"] for r in rows}
    receipt = dict(
        run_id=s.RUN_ID,
        status=status,
        reason=reason,
        slots=len(requests),
        terminal_slots=len(rows),
        dispositions=dict(Counter(r["status"] for r in rows)),
        unattempted_slot_ids=[r["request_id"] for r in requests if r["request_id"] not in complete],
        main_freeze_sha256=hash_file(directory / "main_freeze.json"),
        events_sha256=hash_file(directory / "generation_events.jsonl")
        if (directory / "generation_events.jsonl").exists()
        else None,
        slot_events_sha256=hash_file(directory / "slot_events.jsonl") if rows else None,
        budget=t.budget_state(root),
    )
    publish(directory / "generation_receipt.json", receipt)
    return receipt


def run_due(root, proxy_root, *, transport=None, sleep=time.sleep, now=time.time):
    with stage_lock(root / t.WORKSPACE / ".generation.writer.lock"):
        freeze = s.verify(root)
        directory = root / s.DIRECTORY
        if (directory / "generation_receipt.json").exists():
            raise ValueError("main collection is permanently terminal")
        requests = read_jsonl(directory / "requests.jsonl")
        initial = events(directory / "generation_events.jsonl")
        known = {r["request_id"]: r for r in requests}
        for row in initial:
            if row["request_id"] not in known or (
                row["kind"] == "attempt"
                and row["request_sha256"] != digest(known[row["request_id"]])
            ):
                raise ValueError("main event differs from the frozen request")
        terminals = {r["request_id"]: r for r in initial if r["kind"] == "terminal"}
        slots = events(directory / "slot_events.jsonl")
        if [r["request_id"] for r in slots] != [r["request_id"] for r in requests[: len(slots)]]:
            raise ValueError("slot dispositions are not the frozen prefix")
        for request in requests[len(slots) :]:
            due = (
                freeze["window_origin_unix"]
                + 3600 * freeze["window_offsets_hours"][request["window"]]
            )
            if now() < due:
                return dict(
                    status="waiting",
                    next_window=request["window"],
                    not_before_unix=due,
                    terminal_slots=len(slots),
                    budget=t.budget_state(root),
                )
            row = terminals.get(request["request_id"])
            if row is None:
                row = send_once(
                    root, s.RUN_ID, request, freeze, proxy_root, transport=transport, sleep=sleep
                )
                terminals[request["request_id"]] = row
            reason = stop_reason(row)
            if failure_cluster(list(terminals.values()), request["route"]):
                reason = "systematic_failure_cluster"
            child = None
            if not reason and retry_eligible(root, row):
                child = retry_once(
                    root,
                    request,
                    row,
                    freeze,
                    proxy_root,
                    transport=transport,
                    sleep=sleep,
                    now=now,
                )
                if child:
                    reason = stop_reason(child)
            selected = child if child and child["status"] == "image_returned" else row
            record = append_event(
                directory / "slot_events.jsonl",
                dict(
                    kind="slot_terminal",
                    request_id=request["request_id"],
                    window=request["window"],
                    status=selected["status"],
                    initial_status=row["status"],
                    initial_terminal_sha256=row["event_sha256"],
                    retry_terminal_sha256=child["event_sha256"] if child else None,
                    selected_request_id=selected["request_id"]
                    if selected["status"] == "image_returned"
                    else None,
                    selected_response=selected if selected["status"] == "image_returned" else None,
                ),
            )
            slots.append(record)
            print(
                json.dumps(
                    dict(
                        slot=request["request_id"],
                        window=request["window"],
                        status=record["status"],
                        retried=child is not None,
                    )
                ),
                flush=True,
            )
            if reason:
                return close(root, "stopped_for_diagnosis", reason, requests)
        return close(root, "completed", None, requests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "status"))
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--proxy-root", type=Path, default=Path("../openai-oauth"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "status":
        directory = root / s.DIRECTORY
        result = (
            read_json(directory / "generation_receipt.json")
            if (directory / "generation_receipt.json").exists()
            else dict(
                status="active",
                terminal_slots=len(events(directory / "slot_events.jsonl")),
                budget=t.budget_state(root),
            )
        )
    else:
        while True:
            result = run_due(root, args.proxy_root.resolve())
            if not args.watch or result["status"] != "waiting":
                break
            print(json.dumps(result), flush=True)
            while time.time() < result["not_before_unix"]:
                time.sleep(min(60, result["not_before_unix"] - time.time()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
