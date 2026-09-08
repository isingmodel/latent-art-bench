"""Offline collection tests; no image requests leave httpx.MockTransport."""

import base64
import gzip
import importlib.metadata
import io
import json
import platform
import threading
import time
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    events,
    publish,
)
from latent_art_bench.painter_responsiveness_v2 import collection as c
from latent_art_bench.painter_responsiveness_v2 import common
from latent_art_bench.painter_responsiveness_v2.workflow import RUNTIME

RUN = "prv2-mock"
PROXY = {"recorded_git_commit": "b" * 40, "pid": 123, "files": []}


def image_body(*, dimensions=(512, 512), fmt="PNG", quality="low"):
    buffer = io.BytesIO()
    Image.new("RGB", dimensions, (31, 65, 103)).save(buffer, format=fmt)
    return json.dumps(
        dict(
            data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())],
            quality=quality,
            usage={"cost": 20},
        )
    ).encode()


class Clock:
    def __init__(self):
        self.value, self.lock = 1000.0, threading.Lock()

    def now(self):
        with self.lock:
            return self.value

    def sleep(self, delay):
        with self.lock:
            self.value += delay
        time.sleep(0.00001)


def setup(tmp_path, monkeypatch, *, overrides=None):
    config = read_json(Path(__file__).resolve().parents[2] / common.CONFIG)
    config = dict(config, maximum_in_flight=1)
    config.update(overrides or {})
    paths = c.required_sources()
    for path in paths - {common.CONFIG}:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Synthetic source for an offline transport test.\n")
    publish(tmp_path / common.CONFIG, config)
    requests = common.requests(config)
    directory = tmp_path / common.directory(RUN)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    publish(
        directory / "freeze.json",
        dict(
            run_id=RUN,
            recorded_git_commit="a" * 40,
            inputs=bindings(tmp_path, paths),
            config=config,
            proxy_snapshot=PROXY,
            environment=dict(
                python=platform.python_version(),
                **{name: importlib.metadata.version(name) for name in RUNTIME},
            ),
            requests_sha256=hash_file(directory / "planned_requests.jsonl"),
        ),
    )
    monkeypatch.setattr(c, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(common, "configuration", lambda root: read_json(root / common.CONFIG))
    monkeypatch.setattr(c.legacy, "proxy_snapshot", lambda _: PROXY)
    monkeypatch.setattr(
        c.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 10 * 1024**3})()
    )
    clock = Clock()
    monkeypatch.setattr(c, "monotonic", clock.now)
    return directory, requests, clock


def collect(tmp_path, handler, clock):
    return c.collect(
        tmp_path,
        RUN,
        tmp_path / "mock-proxy",
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
    )


def test_complete_grid_paces_durable_intents_and_preserves_deviating_geometry(
    tmp_path, monkeypatch
):
    directory, requests, clock = setup(tmp_path, monkeypatch)
    calls = []
    body = image_body(dimensions=(640, 512), fmt="JPEG", quality="low")

    def handler(request):
        row = events(directory / "generation_events.jsonl")[-1]
        assert row["kind"] == "attempt" and row["request_id"] == requests[len(calls)]["request_id"]
        assert request.url == c.URL and request.method == "POST"
        assert "Authorization" not in request.headers
        assert json.loads(request.content) == requests[len(calls)]["payload"]
        calls.append(request)
        return httpx.Response(200, content=body)

    receipt = collect(tmp_path, handler, clock)
    assert len(calls) == 192 and receipt["status_counts"] == {"image_returned": 192}
    assert receipt["incremental_api_spend_usd"] == 0 and receipt["paid_requests"] == 0
    rows = events(directory / "generation_events.jsonl")
    starts = [r["transport_started_monotonic"] for r in rows if r["kind"] == "terminal"]
    assert all(b - a >= 5 for a, b in zip(starts, starts[1:]))
    slots = read_jsonl(directory / "slot_outcomes.jsonl")
    assert len(slots) == 192 and all(r["selected_attempt"] == 1 for r in slots)
    for slot in slots:
        path = tmp_path / slot["response_path"]
        assert ":" not in path.name
        assert hash_file(path) == slot["stored_response_sha256"]
        assert gzip.decompress(path.read_bytes()) == body
        assert slot["observed"]["width"] == 640
        assert slot["observed"]["format"] == "JPEG"
        assert slot["observed"]["reported"]["quality"] == "low"
    with pytest.raises(ValueError, match="terminal"):
        collect(tmp_path, handler, clock)


def test_two_requests_overlap_and_halt_drains_them(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch, overrides={"maximum_in_flight": 2})
    second_entered, lock = threading.Event(), threading.Lock()
    count, active, maximum = 0, 0, 0

    def handler(_):
        nonlocal count, active, maximum
        with lock:
            count += 1
            index = count
            active += 1
            maximum = max(maximum, active)
        if index == 1:
            assert second_entered.wait(3)
        elif index == 2:
            second_entered.set()
        with lock:
            active -= 1
        return httpx.Response(401, json={"error": "unauthorized"})

    receipt = collect(tmp_path, handler, clock)
    assert maximum == 2 and count == 2
    assert receipt["terminal_attempts"] == 2 and receipt["unresolved_intents"] == []
    assert receipt["status_counts"] == {"http_error": 2, "never_started": 190}
    assert len(read_jsonl(directory / "slot_outcomes.jsonl")) == 192


def test_known_error_retries_identical_payload_once_and_records_both(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch)
    payloads = []

    def handler(request):
        payloads.append(request.content)
        if len(payloads) == 1:
            return httpx.Response(503, json={"error": "temporary"})
        if len(payloads) == 2:
            return httpx.Response(200, content=image_body())
        return httpx.Response(401, json={"error": "stop"})

    receipt = collect(tmp_path, handler, clock)
    assert len(payloads) == 3 and payloads[0] == payloads[1]
    assert receipt["technical_retries_dispatched"] == 1
    slots = read_jsonl(directory / "slot_outcomes.jsonl")
    assert slots[0]["attempt_count"] == 2 and slots[0]["selected_attempt"] == 2
    assert [r["status"] for r in slots[0]["attempts"]] == ["http_error", "image_returned"]


@pytest.mark.parametrize("body", [{"error": "safety refusal"}, {"refusal": "declined"}])
def test_refusals_never_retry_and_mass_failures_stop(tmp_path, monkeypatch, body):
    _, _, clock = setup(tmp_path, monkeypatch)
    count = 0

    def handler(_):
        nonlocal count
        count += 1
        return httpx.Response(503, json=body)

    receipt = collect(tmp_path, handler, clock)
    assert count == 3 and receipt["technical_retries_dispatched"] == 0
    assert receipt["stop_reason"] == "three_failed_attempts_in_eight_completed"
    assert receipt["status_counts"] == {"refused": 3, "never_started": 189}


def test_non_json_server_errors_are_not_retry_candidates(tmp_path, monkeypatch):
    _, _, clock = setup(tmp_path, monkeypatch)
    receipt = collect(tmp_path, lambda _: httpx.Response(502, content=b"gateway failed"), clock)
    assert receipt["terminal_attempts"] == 3 and receipt["technical_retries_dispatched"] == 0


def test_partial_delivery_retained_and_never_retried(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch)

    class Broken(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"data":['
            raise httpx.ReadTimeout("synthetic interrupted delivery")

    receipt = collect(tmp_path, lambda _: httpx.Response(200, stream=Broken()), clock)
    assert receipt["stop_reason"] == "unresolved_delivery"
    assert receipt["terminal_attempts"] == 1 and receipt["technical_retries_dispatched"] == 0
    row = [r for r in events(directory / "generation_events.jsonl") if r["kind"] == "terminal"][0]
    assert gzip.decompress((tmp_path / row["response_path"]).read_bytes()) == b'{"data":['
    assert row["cost_usd"] == 0 and row["status"] == "outcome_uncertain"


@pytest.mark.parametrize(
    "case",
    [
        "config",
        "requests",
        "freeze",
        "proxy",
        "source",
        "uncommitted",
        "runtime",
    ],
)
def test_verification_changes_block_before_any_post(tmp_path, monkeypatch, case):
    directory, _, clock = setup(tmp_path, monkeypatch)
    if case in ("requests", "freeze"):
        path = directory / ("planned_requests.jsonl" if case == "requests" else "freeze.json")
        value = path.read_text().replace("prv2", "changed", 1)
        path.write_text(value)
    elif case == "config":
        path = tmp_path / common.CONFIG
        path.write_text(
            path.read_text().replace('"maximum_in_flight": 1', '"maximum_in_flight": 3')
        )
    elif case == "proxy":
        monkeypatch.setattr(c.legacy, "proxy_snapshot", lambda _: dict(PROXY, pid=999))
    elif case == "source":
        (tmp_path / common.PACKAGE / "collection.py").write_text("changed")
    elif case == "runtime":
        path = directory / "freeze.json"
        value = read_json(path)
        value["environment"]["httpx"] = "changed"
        path.write_text(json.dumps(value))
    else:

        def uncommitted(*_):
            raise ValueError("uncommitted freeze")

        monkeypatch.setattr(c, "committed", uncommitted)

    def forbidden(_):
        raise AssertionError("no POST allowed")

    with pytest.raises(ValueError):
        collect(tmp_path, forbidden, clock)


def test_interrupted_marker_is_not_a_resumable_queue(tmp_path, monkeypatch):
    _, _, clock = setup(tmp_path, monkeypatch)
    publish(tmp_path / common.WORKSPACE / RUN / "collection_started.json", {"interrupted": True})
    with pytest.raises(ValueError, match="previously started"):
        collect(tmp_path, lambda _: pytest.fail("no POST allowed"), clock)


def test_six_global_retries_are_not_reset_per_block(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch)
    calls = 0

    def handler(_):
        nonlocal calls
        calls += 1
        intent = events(directory / "generation_events.jsonl")[-1]
        if intent["slot_sequence"] % 4 == 0 and intent["attempt"] == 1:
            return httpx.Response(503, json={"error": "transient"})
        return httpx.Response(200, content=image_body())

    receipt = collect(tmp_path, handler, clock)
    assert receipt["technical_retries_dispatched"] == 6
    assert receipt["attempt_intents"] == 198 and calls == 198
    assert receipt["status_counts"] == {"image_returned": 150, "http_error": 42}


def test_binding_mutation_after_response_stops_next_admission(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch)
    calls = 0

    def handler(_):
        nonlocal calls
        calls += 1
        (tmp_path / common.PACKAGE / "collection.py").write_text("changed after dispatch")
        return httpx.Response(200, content=image_body())

    with pytest.raises(ValueError):
        collect(tmp_path, handler, clock)
    receipt = read_json(directory / "collection_receipt.json")
    assert calls == 1 and receipt["terminal_attempts"] == 1
    assert receipt["status_counts"] == {"image_returned": 1, "never_started": 191}
    assert receipt["stop_reason"] == "coordinator_interrupted_ValueError"


def test_received_entity_is_bounded_even_for_a_large_single_chunk(tmp_path, monkeypatch):
    directory, _, clock = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(c, "MAX_RESPONSE", 64)
    receipt = collect(tmp_path, lambda _: httpx.Response(200, content=b"x" * 1000), clock)
    assert receipt["stop_reason"] == "unresolved_delivery"
    row = [r for r in events(directory / "generation_events.jsonl") if r["kind"] == "terminal"][0]
    assert row["received_bytes"] == 1000 and row["response_bytes"] == 64
    assert gzip.decompress((tmp_path / row["response_path"]).read_bytes()) == b"x" * 64
