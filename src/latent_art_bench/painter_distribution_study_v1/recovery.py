"""Bounded recovery of complete transient failures while retaining missing-cost reserves."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import collection as previous
from . import continuation as predecessor
from . import parallel_collection as first
from . import study as s
from . import transport as t

RUN_ID = "pdsv1-main-recovery-20260907"
DIRECTORY = t.MANIFESTS / RUN_ID
WORKSPACE = t.WORKSPACE / RUN_ID
CONTRACT = Path("studies") / t.NAMESPACE / "TRANSIENT_RECOVERY.md"


COMPONENTS = (first.DIRECTORY, predecessor.DIRECTORY)
RECOVERY_SLOT = "slot0108"


def reserved_failure(root, row):
    if (
        not row.get("complete")
        or row.get("status") != "http_error"
        or row.get("status_code") not in (500, 502, 503, 504)
        or row.get("cost_usd") is not None
        or row.get("route") not in s.ROUTES[:2]
    ):
        return False
    try:
        body = json.loads(previous.read_response(root, row))
    except (ValueError, OSError):
        return False
    if not isinstance(body, dict) or set(body) != {"error"}:
        return False
    error = body["error"]
    return (
        isinstance(error, dict)
        and type(error.get("code")) is int
        and error["code"] == row["status_code"]
        and isinstance(error.get("message"), str)
        and bool(error["message"].strip())
    )


def budget_state(root):
    budget = t.budget_state(root)
    failures, reported = [], 0.0
    for path in sorted((root / t.MANIFESTS).glob("*/generation_events.jsonl")):
        for row in events(path):
            if row["kind"] != "terminal":
                continue
            if row.get("cost_usd") is not None:
                reported += row["cost_usd"]
            elif reserved_failure(root, row):
                failures.append(
                    dict(
                        run_id=path.parent.name,
                        request_id=row["request_id"],
                        reservation_usd=t.REQUEST_RESERVATION,
                        terminal_sha256=row["event_sha256"],
                    )
                )
    budget.update(
        uncertain=budget["uncertain"] - len(failures),
        provider_reported_usd=reported,
        missing_cost_failures=len(failures),
        contingency_reserve_usd=len(failures) * t.REQUEST_RESERVATION,
        reserved_failure_records=failures,
    )
    return budget


def stop_reason(root, row):
    return None if reserved_failure(root, row) else predecessor.stop_reason(root, row)


def retry_eligible(root, row):
    return reserved_failure(root, row) or previous.retry_eligible(root, row)


def remaining_requests(root):
    slots = []
    for directory in COMPONENTS:
        receipt = read_json(root / directory / "generation_receipt.json")
        verify_bindings(root, receipt["outputs"])
        if receipt["status"] != "stopped_for_diagnosis" or receipt["unresolved_slot_ids"]:
            raise ValueError("require closed reconciled predecessor slots")
        slots.extend(events(root / directory / "slot_events.jsonl"))
    known = {row["request_id"] for row in slots}
    if (
        len(slots) != 100
        or len(known) != 100
        or Counter(r["status"] for r in slots) != {"image_returned": 98, "http_error": 2}
    ):
        raise ValueError("predecessor inventory differs from the diagnosed record")
    failures = [
        row
        for directory in COMPONENTS
        for row in events(root / directory / "generation_events.jsonl")
        if row["kind"] == "terminal" and row["status"] != "image_returned"
    ]
    if {row["request_id"] for row in failures} != {"slot0036", RECOVERY_SLOT}:
        raise ValueError("unexpected predecessor failures")
    failed = next(row for row in failures if row["request_id"] == RECOVERY_SLOT)
    if not reserved_failure(root, failed):
        raise ValueError("complete transient-failure contract is not met")
    requests = [
        r
        for r in read_jsonl(root / s.DIRECTORY / "requests.jsonl")
        if r["request_id"] not in known or r["request_id"] == RECOVERY_SLOT
    ]
    if len(requests) != 909:
        raise ValueError("require 908 untouched slots plus one authorized recovery")
    return requests


def source_paths():
    return [
        CONTRACT,
        s.PACKAGE / "recovery.py",
        s.PACKAGE / "recovery_results.py",
        Path("tests") / t.NAMESPACE / "test_recovery.py",
        Path("tests") / t.NAMESPACE / "test_recovery_results.py",
    ] + [
        predecessor.DIRECTORY / name
        for name in (
            "execution_freeze.json",
            "generation_receipt.json",
            "generation_events.jsonl",
            "slot_events.jsonl",
            "operator_events.jsonl",
            "transient_diagnosis.json",
        )
    ]


def prepare(root):
    parent = predecessor.verify(root)
    requests = remaining_requests(root)
    paths = source_paths()
    commit = committed(root, paths)
    freeze = dict(
        run_id=RUN_ID,
        predecessor_id=predecessor.RUN_ID,
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        scientific_freeze_sha256=parent["scientific_freeze_sha256"],
        window_origin_unix=parent["window_origin_unix"],
        window_offsets_hours=parent["window_offsets_hours"],
        maximum_in_flight=3,
        maximum_per_route=1,
        minimum_start_interval_seconds=5,
        content_weights=parent["content_weights"],
        proxy_source=parent["proxy_source"],
        total_slots=len(requests),
        unattempted_original_slots=908,
        cross_census_retry_slot=RECOVERY_SLOT,
        scientific_total_slots=1008,
        request_inventory_sha256=digest(requests),
        budget=budget_state(root),
    )
    publish(root / DIRECTORY / "execution_freeze.json", freeze)
    return {k: v for k, v in freeze.items() if k not in ("inputs", "proxy_source")}


def verify(root):
    predecessor.verify(root)
    freeze = read_json(root / DIRECTORY / "execution_freeze.json")
    verify_bindings(root, freeze["inputs"])
    committed(root, [DIRECTORY / "execution_freeze.json"])
    if freeze["request_inventory_sha256"] != digest(remaining_requests(root)):
        raise ValueError("continuation requests changed")
    if (
        freeze["maximum_in_flight"],
        freeze["maximum_per_route"],
        freeze["minimum_start_interval_seconds"],
    ) != (3, 1, 5):
        raise ValueError("parallel limits changed")
    return freeze


class Window:
    def __init__(self, root, freeze, requests, proxy_root, *, transport=None, interval=5.0):
        self.root, self.freeze, self.requests, self.proxy_root = root, freeze, requests, proxy_root
        self.transport, self.interval = transport, interval
        self.lock, self.stop = threading.RLock(), threading.Event()
        self.active, self.reason, self.last_start = set(), None, -math.inf
        self.directory = root / DIRECTORY
        self.known_slots = {
            r["request_id"]: r for r in events(self.directory / "slot_events.jsonl")
        }
        self.initial = {
            r["request_id"]: r
            for r in (
                [
                    row
                    for directory in COMPONENTS
                    for row in events(root / directory / "generation_events.jsonl")
                ]
                + events(self.directory / "generation_events.jsonl")
            )
            if r["kind"] == "terminal"
        }

    def halt(self, reason):
        if self.reason is None:
            append_event(
                self.directory / "operator_events.jsonl",
                dict(kind="dispatch_halted", reason=reason),
            )
        self.reason = self.reason or reason
        self.stop.set()

    def dispatch(self, run_id, request):
        ledger = self.root / t.MANIFESTS / run_id / "generation_events.jsonl"
        while not self.stop.is_set():
            with self.lock:
                if self.stop.is_set():
                    return None
                delay = self.interval - (time.monotonic() - self.last_start)
                if delay <= 0:
                    if any(r["request_id"] == request["request_id"] for r in events(ledger)):
                        raise ValueError("attempt already exists; no redispatch")
                    raw = (
                        self.root
                        / t.WORKSPACE
                        / run_id
                        / "responses"
                        / (request["request_id"] + ".json.gz")
                    )
                    if raw.exists():
                        raise ValueError("orphan raw response; reconcile before dispatch")
                    budget = budget_state(self.root)
                    paid = t.ROUTES[request["route"]][1] is not None
                    if budget["uncertain"] or budget["unresolved"] != len(self.active):
                        raise ValueError("unowned intent or unknown charge blocks dispatch")
                    if budget["attempts"] >= 1050 or (paid and budget["paid_attempts"] >= 612):
                        raise ValueError("study attempt allocation exhausted")
                    if paid and budget["accounted_usd"] + t.REQUEST_RESERVATION > 75:
                        raise ValueError("study spending reserve reached")
                    if shutil.disk_usage(self.root).free < t.MIN_FREE + t.MAX_RESPONSE:
                        raise OSError("storage reserve reached")
                    if (
                        not paid
                        and t.proxy_snapshot(self.proxy_root) != self.freeze["proxy_source"]
                    ):
                        raise ValueError("OAuth source/listener changed")
                    key = run_id, request["request_id"]
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
                    self.last_start = time.monotonic()
                    self.active.add(key)
                    break
            self.stop.wait(min(1, max(0, delay)))
        else:
            return None
        result = t._send(self.root, run_id, request, transport=self.transport)
        with self.lock:
            row = append_event(ledger, result)
            self.active.remove(key)
            if run_id == RUN_ID:
                self.initial[request["request_id"]] = row
            reason = stop_reason(self.root, row)
            if run_id == RUN_ID and previous.failure_cluster(
                list(self.initial.values()), request["route"]
            ):
                reason = "systematic_failure_cluster"
            if reason:
                self.halt(reason)
            return row

    def retry(self, request, parent):
        run_id = RUN_ID + "-retry-" + request["request_id"]
        child = dict(
            request,
            request_id=request["request_id"] + "-retry1",
            predecessor_request_id=request["request_id"],
        )
        directory = self.root / t.MANIFESTS / run_id
        authority_path = directory / "retry_authority.json"
        expected = dict(
            run_id=run_id,
            request=child,
            parent_run_id=Path(parent["response_path"]).parent.parent.name,
            execution_freeze_sha256=hash_file(self.directory / "execution_freeze.json"),
            predecessor_terminal=parent,
            predecessor_terminal_sha256=parent["event_sha256"],
        )
        with self.lock:
            if not authority_path.exists():
                reserved = list(
                    (self.root / t.MANIFESTS).glob("pdsv1-main*-retry-*/retry_authority.json")
                )
                if self.stop.is_set() or len(reserved) >= 24:
                    return None
                publish(
                    authority_path,
                    dict(
                        expected,
                        not_before_unix=time.time() + previous.retry_delay(parent, time.time()),
                    ),
                )
            authority = read_json(authority_path)
            if {k: authority[k] for k in expected} != expected:
                raise ValueError("retry predecessor binding differs")
            rows = events(directory / "generation_events.jsonl")
            if rows:
                if len(rows) != 2 or rows[-1]["kind"] != "terminal":
                    raise ValueError("unresolved retry; never dispatch twice")
                if not (directory / "generation_receipt.json").exists():
                    publish(
                        directory / "generation_receipt.json",
                        dict(
                            run_id=run_id,
                            status=rows[-1]["status"],
                            authority_sha256=hash_file(authority_path),
                            events_sha256=hash_file(directory / "generation_events.jsonl"),
                        ),
                    )
                return rows[-1]
            if (directory / "generation_receipt.json").exists():
                raise ValueError("retry census is terminal")
        while time.time() < authority["not_before_unix"] and not self.stop.is_set():
            self.stop.wait(min(1, authority["not_before_unix"] - time.time()))
        result = self.dispatch(run_id, child)
        if result:
            with self.lock:
                publish(
                    directory / "generation_receipt.json",
                    dict(
                        run_id=run_id,
                        status=result["status"],
                        authority_sha256=hash_file(authority_path),
                        events_sha256=hash_file(directory / "generation_events.jsonl"),
                    ),
                )
        return result

    def route(self, route, ready_at):
        try:
            while time.monotonic() < ready_at and not self.stop.is_set():
                self.stop.wait(min(1, ready_at - time.monotonic()))
            for request in self.requests:
                if request["route"] != route or request["request_id"] in self.known_slots:
                    continue
                if self.stop.is_set():
                    break
                with self.lock:
                    parent = self.initial.get(request["request_id"])
                if parent is None:
                    parent = self.dispatch(RUN_ID, request)
                if parent is None:
                    break
                with self.lock:
                    reason = stop_reason(self.root, parent)
                    if previous.failure_cluster(list(self.initial.values()), route):
                        reason = "systematic_failure_cluster"
                    if reason:
                        self.halt(reason)
                child = None
                if not self.stop.is_set() and retry_eligible(self.root, parent):
                    child = self.retry(request, parent)
                selected = child if child else parent
                with self.lock:
                    if child and (reason := stop_reason(self.root, child)):
                        self.halt(reason)
                    row = append_event(
                        self.directory / "slot_events.jsonl",
                        dict(
                            kind="slot_terminal",
                            request_id=request["request_id"],
                            window=request["window"],
                            status=selected["status"],
                            initial_status=parent["status"],
                            initial_terminal_sha256=parent["event_sha256"],
                            retry_terminal_sha256=child["event_sha256"] if child else None,
                            selected_request_id=selected["request_id"]
                            if selected["status"] == "image_returned"
                            else None,
                            selected_response=selected
                            if selected["status"] == "image_returned"
                            else None,
                        ),
                    )
                    self.known_slots[request["request_id"]] = row
                    print(
                        json.dumps(
                            dict(
                                slot=request["request_id"],
                                route=route,
                                window=request["window"],
                                status=row["status"],
                                retried=child is not None,
                            )
                        ),
                        flush=True,
                    )
        except Exception as exc:
            with self.lock:
                append_event(
                    self.directory / "operator_events.jsonl",
                    dict(kind="worker_exception", route=route, exception_type=type(exc).__name__),
                )
                self.halt("worker_exception_requires_diagnosis")

    def run(self):
        for row in events(self.directory / "operator_events.jsonl"):
            if row["kind"] == "dispatch_halted":
                self.reason = row["reason"]
                self.stop.set()
                return self.reason
        budget = budget_state(self.root)
        if budget["unresolved"] or budget["uncertain"]:
            raise ValueError("reconcile previous outcomes before starting route workers")
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.route, route, started + i * self.interval)
                for i, route in enumerate(s.ROUTES)
            ]
            for future in futures:
                future.result()
        return self.reason


def close(root, requests, status, reason):
    directory = root / DIRECTORY
    slots = events(directory / "slot_events.jsonl")
    known = {r["request_id"] for r in slots}
    attempted = {
        r["request_id"]
        for r in events(directory / "generation_events.jsonl")
        if r["kind"] == "attempt"
    }
    child_paths = []
    for authority_path in sorted(
        (root / t.MANIFESTS).glob(RUN_ID + "-retry-*/retry_authority.json")
    ):
        child_dir = authority_path.parent
        if not (child_dir / "generation_receipt.json").exists():
            rows = events(child_dir / "generation_events.jsonl")
            child_status = (
                rows[-1]["status"]
                if rows and rows[-1]["kind"] == "terminal"
                else ("outcome_uncertain" if rows else "not_attempted_due_collection_stop")
            )
            publish(
                child_dir / "generation_receipt.json",
                dict(
                    run_id=child_dir.name,
                    status=child_status,
                    authority_sha256=hash_file(authority_path),
                    events_sha256=hash_file(child_dir / "generation_events.jsonl")
                    if rows
                    else None,
                ),
            )
        child_paths.extend(
            file.relative_to(root)
            for file in child_dir.iterdir()
            if file.suffix in (".json", ".jsonl")
        )
    receipt = dict(
        run_id=RUN_ID,
        status=status,
        reason=reason,
        slots=len(requests),
        terminal_slots=len(slots),
        dispositions=dict(Counter(r["status"] for r in slots)),
        unattempted_slot_ids=[
            r["request_id"]
            for r in requests
            if r["request_id"] not in attempted and r["request_id"] not in known
        ],
        unresolved_slot_ids=sorted(attempted - known),
        execution_freeze_sha256=hash_file(directory / "execution_freeze.json"),
        budget=budget_state(root),
        outputs=bindings(
            root, [p.relative_to(root) for p in directory.glob("*_events.jsonl")] + child_paths
        ),
    )
    publish(directory / "generation_receipt.json", receipt)
    return receipt


def run_due(root, proxy_root):
    with stage_lock(root / t.WORKSPACE / ".generation.writer.lock"):
        freeze = verify(root)
        directory = root / DIRECTORY
        if (directory / "generation_receipt.json").exists():
            raise ValueError("parallel census is permanently terminal")
        requests = remaining_requests(root)
        known = {r["request_id"]: r for r in requests}
        for row in events(directory / "generation_events.jsonl"):
            if row["request_id"] not in known or (
                row["kind"] == "attempt"
                and row["request_sha256"] != digest(known[row["request_id"]])
            ):
                raise ValueError("parallel request differs from frozen payload")
        for window in range(8):
            complete = {r["request_id"] for r in events(directory / "slot_events.jsonl")}
            selected = [
                r for r in requests if r["window"] == window and r["request_id"] not in complete
            ]
            if not selected:
                continue
            due = freeze["window_origin_unix"] + 3600 * freeze["window_offsets_hours"][window]
            if time.time() < due:
                return dict(
                    status="waiting",
                    next_window=window,
                    not_before_unix=due,
                    terminal_slots=len(complete),
                    budget=budget_state(root),
                )
            reason = Window(root, freeze, selected, proxy_root).run()
            if reason:
                return close(root, requests, "stopped_for_diagnosis", reason)
        return close(root, requests, "completed", None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check", "run", "status"))
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--proxy-root", type=Path, default=Path("../openai-oauth"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare(root)
    elif args.command == "check":
        result = verify(root)
    elif args.command == "status":
        path = root / DIRECTORY / "generation_receipt.json"
        result = (
            read_json(path)
            if path.exists()
            else dict(
                status="active",
                terminal_slots=len(events(root / DIRECTORY / "slot_events.jsonl")),
                budget=budget_state(root),
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
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("inputs", "proxy_source")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
