import base64
import io
import json
import threading
import time
from collections import Counter
from datetime import datetime

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import collection as c
from latent_art_bench.painter_distribution_study_v1 import parallel_collection as p
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events, publish


def setup(tmp_path, monkeypatch, count=3):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    monkeypatch.setattr(t, "proxy_snapshot", lambda root: {})
    frozen = dict(proxy_source={})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", frozen)
    requests = [
        dict(
            sequence=i * 3 + j,
            request_id=f"slot{i * 3 + j:04d}",
            route=route,
            window=0,
            payload=t.payload(route, "An oil painting of a river."),
        )
        for i in range(count)
        for j, route in enumerate(s.ROUTES)
    ]
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (30, 60, 90)).save(buffer, format="PNG")
    response = dict(
        data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())], usage=dict(cost=0.07)
    )
    return frozen, requests, response


def test_route_workers_overlap_with_staggered_starts_and_atomic_costs(tmp_path, monkeypatch):
    frozen, requests, response = setup(tmp_path, monkeypatch)
    lock, active, peaks, starts = threading.Lock(), Counter(), [], []

    def handler(request):
        route = json.loads(request.content)["model"]
        with lock:
            active[route] += 1
            peaks.append((sum(active.values()), max(active.values())))
            starts.append(time.monotonic())
        time.sleep(0.08)
        with lock:
            active[route] -= 1
        return httpx.Response(200, json=response)

    engine = p.Window(
        tmp_path, frozen, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0.02
    )
    assert engine.run() is None
    assert max(total for total, _ in peaks) == 3
    assert max(per_route for _, per_route in peaks) == 1
    assert min(b - a for a, b in zip(starts, starts[1:])) >= 0.015
    recorded = events(tmp_path / p.DIRECTORY / "generation_events.jsonl")
    attempts = [r for r in recorded if r["kind"] == "attempt"]
    stamps = [datetime.fromisoformat(r["at_utc"]).timestamp() for r in attempts]
    assert min(b - a for a, b in zip(stamps, stamps[1:])) >= 0.02
    assert len(attempts) == 9 and len(engine.known_slots) == 9
    for route in s.ROUTES:
        assert [r["request_id"] for r in attempts if r["route"] == route] == [
            r["request_id"] for r in requests if r["route"] == route
        ]
    budget = t.budget_state(tmp_path)
    assert budget["unresolved"] == budget["uncertain"] == 0
    assert budget["accounted_usd"] == pytest.approx(6 * 0.07)
    # A resumed window reads completed slots without sending any further requests.
    assert (
        p.Window(
            tmp_path, frozen, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0
        ).run()
        is None
    )
    assert len(starts) == 9


def test_parallel_cluster_stop_drains_accepted_calls_without_new_dispatch(tmp_path, monkeypatch):
    frozen, requests, response = setup(tmp_path, monkeypatch, count=5)
    monkeypatch.setattr(c, "retry_delay", lambda row, now: 0)

    def handler(request):
        if json.loads(request.content)["model"] == t.ROUTES[s.ROUTES[0]][0]:
            return httpx.Response(429, json={"error": "rate limited"})
        time.sleep(0.05)
        return httpx.Response(200, json=response)

    engine = p.Window(
        tmp_path, frozen, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0.005
    )
    assert engine.run() == "systematic_failure_cluster"
    stops = events(tmp_path / p.DIRECTORY / "operator_events.jsonl")
    stopped_at = next(r["at_utc"] for r in stops if r["kind"] == "dispatch_halted")
    rows = events(tmp_path / p.DIRECTORY / "generation_events.jsonl")
    assert all(r["at_utc"] <= stopped_at for r in rows if r["kind"] == "attempt")
    assert len([r for r in rows if r["kind"] == "attempt" and r["route"] == s.ROUTES[0]]) == 3
    assert len(list((tmp_path / t.MANIFESTS).glob(p.RUN_ID + "-retry-*/retry_authority.json"))) == 2
    assert t.budget_state(tmp_path)["unresolved"] == 0
    result = p.close(tmp_path, requests, "stopped_for_diagnosis", engine.reason)
    assert result["unresolved_slot_ids"] == []
    assert result["unattempted_slot_ids"]
    assert len([r for r in rows if r["kind"] == "terminal"]) == result["terminal_slots"]


def test_inflight_reservation_prevents_parallel_double_spending(tmp_path, monkeypatch):
    frozen, requests, response = setup(tmp_path, monkeypatch, count=1)
    ledger = tmp_path / t.MANIFESTS / "accounting-fixture" / "generation_events.jsonl"
    append_event(ledger, dict(kind="attempt", request_id="prior", paid=True))
    append_event(
        ledger, dict(kind="terminal", request_id="prior", status="image_returned", cost_usd=69.0)
    )
    calls = []

    def handler(request):
        calls.append(request)
        time.sleep(0.1)
        return httpx.Response(200, json=response)

    engine = p.Window(
        tmp_path, frozen, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0.01
    )
    assert engine.run() == "worker_exception_requires_diagnosis"
    assert len(calls) == 1
    assert t.budget_state(tmp_path)["accounted_usd"] == pytest.approx(69.07)
    assert not engine.active


def test_recorded_halt_survives_restart_without_redispatch(tmp_path, monkeypatch):
    frozen, requests, response = setup(tmp_path, monkeypatch, count=1)
    append_event(
        tmp_path / p.DIRECTORY / "operator_events.jsonl",
        dict(kind="dispatch_halted", reason="systematic_failure_cluster"),
    )

    def forbidden(request):
        pytest.fail("a recorded stop must not dispatch after restart")

    engine = p.Window(
        tmp_path, frozen, requests, tmp_path, transport=httpx.MockTransport(forbidden), interval=0
    )
    assert engine.run() == "systematic_failure_cluster"
    assert t.budget_state(tmp_path)["attempts"] == 0
