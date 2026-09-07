import base64
import io
import threading
from collections import Counter
from datetime import datetime

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import immediate as p
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events, publish


def response():
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (20, 50, 90)).save(buffer, format="PNG")
    return dict(
        data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())], usage=dict(cost=0.07)
    )


def test_future_due_times_do_not_delay_remaining_batches(tmp_path, monkeypatch):
    requests = [dict(request_id="a", window=4), dict(request_id="b", window=7)]
    freeze = dict(
        window_origin_unix=9999999999,
        window_offsets_hours=[0, 3, 6, 9, 24, 27, 30, 33],
        inter_batch_pause_seconds=5,
    )
    monkeypatch.setattr(p, "verify", lambda root: freeze)
    monkeypatch.setattr(p, "remaining_requests", lambda root: requests)
    sleeps, batches = [], []
    monkeypatch.setattr(p.time, "sleep", sleeps.append)

    class FakeWindow:
        def __init__(self, root, frozen, selected, proxy_root):
            self.selected = selected

        def run(self):
            batches.append([r["window"] for r in self.selected])
            for row in self.selected:
                append_event(tmp_path / p.DIRECTORY / "slot_events.jsonl", row)
            return None

    monkeypatch.setattr(p, "Window", FakeWindow)
    monkeypatch.setattr(
        p, "close", lambda root, rows, status, reason: dict(status=status, reason=reason)
    )
    assert p.run_due(tmp_path, tmp_path) == dict(status="completed", reason=None)
    assert batches == [[4], [7]] and sleeps == [5, 5]
    publish(tmp_path / p.DIRECTORY / "generation_receipt.json", dict(status="completed"))
    with pytest.raises(ValueError, match="permanently terminal"):
        p.run_due(tmp_path, tmp_path)


def test_parallel_routes_stay_staggered_and_preserve_order(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    monkeypatch.setattr(t, "proxy_snapshot", lambda root: {})
    freeze = dict(proxy_source={})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", freeze)
    requests = [
        dict(request_id=f"r{i}-{j}", route=route, window=4, payload=t.payload(route, "Landscape"))
        for i, route in enumerate(s.ROUTES)
        for j in range(2)
    ]
    lock = threading.Lock()
    barrier = threading.Barrier(3)
    active, peaks = Counter(), Counter()
    maximum = 0

    def handler(req):
        nonlocal maximum
        with lock:
            active[req.url.host] += 1
            maximum = max(maximum, sum(active.values()))
        barrier.wait(timeout=5)
        with lock:
            active[req.url.host] -= 1
        return httpx.Response(200, json=response())

    engine = p.Window(
        tmp_path, freeze, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0.01
    )
    assert engine.run() is None
    ledger = events(tmp_path / p.DIRECTORY / "generation_events.jsonl")
    active.clear()
    starts = []
    for row in ledger:
        if row["kind"] == "attempt":
            active[row["route"]] += 1
            peaks[row["route"]] = max(peaks[row["route"]], active[row["route"]])
            starts.append(datetime.fromisoformat(row["at_utc"].replace("Z", "+00:00")).timestamp())
        else:
            active[row["route"]] -= 1
    assert maximum == 3 and set(peaks.values()) == {1}
    assert min(b - a for a, b in zip(starts, starts[1:])) >= 0.009
    for route in s.ROUTES:
        assert [
            r["request_id"] for r in ledger if r["kind"] == "attempt" and r["route"] == route
        ] == [r["request_id"] for r in requests if r["route"] == route]
    assert len(events(tmp_path / p.DIRECTORY / "slot_events.jsonl")) == 6


def test_retry_retains_reserve_and_exact_parent_in_immediate_namespace(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    monkeypatch.setattr(p.previous, "retry_delay", lambda row, now: 0)
    freeze = dict(proxy_source={})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", freeze)
    request = dict(
        request_id="new", route=s.ROUTES[1], window=4, payload=t.payload(s.ROUTES[1], "Landscape")
    )
    calls = []

    def handler(req):
        calls.append(req.content)
        return (
            httpx.Response(502, json={"error": {"message": "Upstream failed", "code": 502}})
            if len(calls) == 1
            else httpx.Response(200, json=response())
        )

    engine = p.Window(
        tmp_path, freeze, [request], tmp_path, transport=httpx.MockTransport(handler), interval=0
    )
    assert engine.run() is None and len(calls) == 2 and calls[0] == calls[1]
    directory = tmp_path / t.MANIFESTS / (p.RUN_ID + "-retry-new")
    authority = read_json(directory / "retry_authority.json")
    assert authority["parent_run_id"] == p.RUN_ID
    budget = p.budget_state(tmp_path)
    assert budget["accounted_usd"] == pytest.approx(5.07)
    assert budget["contingency_reserve_usd"] == 5 and budget["uncertain"] == 0
    assert p.close(tmp_path, [request], "completed", None)["unresolved_slot_ids"] == []
