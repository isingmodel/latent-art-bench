"""Prospective transport tests: every request uses offline httpx.MockTransport."""

import base64
import gzip
import io
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    events,
    publish,
)
from latent_art_bench.painter_responsiveness_v1 import collection as c
from latent_art_bench.painter_responsiveness_v1 import common, design, generation_prepare

RUN = "prv1-mock-collection"
SOURCE = "prv1-mock-diagnostic"


def image_body(cost=0.01, *, size=512):
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), (31, 65, 103)).save(buffer, format="PNG")
    return json.dumps(dict(data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())],
                           usage=dict(cost=cost))).encode()


class Clock:
    def __init__(self):
        self.value = 1000.0
        self.lock = threading.Lock()

    def now(self):
        with self.lock:
            return self.value

    def sleep(self, delay):
        with self.lock:
            self.value += delay
        time.sleep(0.00001)  # Yield the CPU to real worker threads without live pacing delays.


def fixture(tmp_path, monkeypatch, *, run_id=RUN, overrides=None, baseline=45.6819185):
    config = read_json(Path(__file__).resolve().parents[2] / common.CONFIG)
    config = dict(config, maximum_in_flight=1)
    config.update(overrides or {})
    config_path = tmp_path / common.CONFIG
    if config_path.exists():
        config_path.write_text(json.dumps(config))
    else:
        publish(config_path, config)
    required = [common.PACKAGE / f for f in
                ("collection.py", "common.py", "design.py", "generation_prepare.py")]
    required += [Path("src/latent_art_bench") / f for f in (
        "io.py", "painter_feature_generation_v2/artifacts.py",
        "painter_distribution_study_v1/transport.py", "painter_distribution_study_v1/discovery.py",
        "painter_prompt_study_v1/common.py",
    )]
    for path in required:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Synthetic frozen source identity for a MockTransport fixture.\n")
    paths = required + [common.CONFIG]
    source_path = tmp_path / common.directory(SOURCE) / "freeze.json"
    if not source_path.exists():
        publish(source_path, dict(run_id=SOURCE, inputs=[]))
    provider_relative = common.directory(SOURCE) / "provider_preflight.json"
    provider_path = tmp_path / provider_relative
    if not provider_path.exists():
        publish(provider_path, dict(checked_at_utc=datetime.now(timezone.utc).isoformat()))
    paths.append(provider_relative)
    requests = common.requests_from_schedule(design.make_schedule(
        [row["template_id"] for row in config["templates"]], seed=config["seed"]), config)
    directory = tmp_path / common.directory(run_id)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    freeze = dict(run_id=run_id, diagnostic_run_id=SOURCE, recorded_git_commit="a" * 40,
                  inputs=bindings(tmp_path, paths), config=config,
                  requests_sha256=hash_file(directory / "planned_requests.jsonl"),
                  source_freeze_sha256=hash_file(source_path), budget_baseline_usd=baseline,
                  provider_preflight_path=str(provider_relative),
                  gates=dict(status="ready", checks=dict.fromkeys(c.GATE_KEYS, True), missing=[]))
    publish(directory / "generation_freeze.json", freeze)
    monkeypatch.setattr(c, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(generation_prepare, "verify_qualification",
                        lambda root, freeze: read_json(root / freeze["provider_preflight_path"]))
    secret = "sk-or-mock-" + "m" * 30
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=" + secret)
    clock = Clock()
    monkeypatch.setattr(c, "monotonic", clock.now)
    monkeypatch.setattr(c.shutil, "disk_usage",
                        lambda _: type("Disk", (), {"free": 10 * 1024**3})())
    return directory, requests, clock, secret


def terminals(directory):
    return [row for row in events(directory / "generation_events.jsonl")
            if row["kind"] == "terminal"]


def test_full_grid_has_durable_paced_intents_and_verified_raw_selection(tmp_path, monkeypatch):
    directory, requests, clock, secret = fixture(tmp_path, monkeypatch)
    body, calls = image_body(), []

    def handler(request):
        row = events(directory / "generation_events.jsonl")[-1]
        assert row["kind"] == "attempt"
        assert row["request_id"] == requests[len(calls)]["request_id"]
        assert request.url == c.URL and request.method == "POST"
        assert request.headers["Authorization"] == "Bearer " + secret
        calls.append(request)
        return httpx.Response(200, content=body)

    receipt = c.collect(tmp_path, RUN, transport=httpx.MockTransport(handler), sleep=clock.sleep)
    assert receipt["status"] == "completed" and len(calls) == 192
    assert receipt["namespace_budget"]["known_cost_usd"] == pytest.approx(1.92)
    assert receipt["status_counts"] == {"image_returned": 192}
    intents = [r for r in events(directory / "generation_events.jsonl") if r["kind"] == "attempt"]
    assert all(b["admitted_monotonic"] - a["admitted_monotonic"] >= 5
               for a, b in zip(intents, intents[1:]))
    starts = sorted(r["transport_started_monotonic"] for r in terminals(directory))
    assert all(second - first >= 5 for first, second in zip(starts, starts[1:]))
    slots = read_jsonl(directory / "slot_outcomes.jsonl")
    assert len(slots) == 192 and all(r["selected_attempt"] == 1 for r in slots)
    for slot in slots:
        path = tmp_path / slot["response_path"]
        assert ":" not in path.name
        assert hash_file(path) == slot["stored_response_sha256"]
        assert gzip.decompress(path.read_bytes()) == body
        assert slot["observed"]["width"] == 512
    assert secret not in (directory / "generation_events.jsonl").read_text()
    with pytest.raises(ValueError, match="terminal"):
        c.collect(tmp_path, RUN, transport=httpx.MockTransport(handler), sleep=clock.sleep)
    assert len(calls) == 192


def test_two_requests_can_overlap_but_a_tight_reserve_waits_for_resolution(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch, overrides={"maximum_in_flight": 2})
    body = image_body()
    first_entered, second_entered = threading.Event(), threading.Event()
    active, maximum, calls = 0, 0, 0
    lock = threading.Lock()

    def handler(_):
        nonlocal active, maximum, calls
        with lock:
            calls += 1
            index = calls
            active += 1
            maximum = max(maximum, active)
        if index == 1:
            first_entered.set()
            assert second_entered.wait(3)
        elif index == 2:
            assert first_entered.is_set()
            second_entered.set()
        with lock:
            active -= 1
        # The pair has demonstrated overlap; stop further calls with an explicit auth error.
        if index >= 3:
            return httpx.Response(401, json={"error": "mock unauthorized"})
        return httpx.Response(200, content=body)

    receipt = c.collect(tmp_path, RUN, transport=httpx.MockTransport(handler), sleep=clock.sleep)
    assert maximum == 2 and 3 <= calls <= 4
    assert receipt["status"] == "stopped" and receipt["terminal_attempts"] == calls
    assert receipt["namespace_budget"]["pending"] == []


def test_known_technical_error_retries_once_with_identical_payload(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    payloads = []

    def handler(request):
        payloads.append(request.content)
        if len(payloads) == 1:
            return httpx.Response(503, json={"error": "temporary", "usage": {"cost": 0}})
        if len(payloads) == 2:
            return httpx.Response(200, content=image_body())
        return httpx.Response(402, json={"error": "mock exhausted"})

    result = c.collect(tmp_path, RUN, transport=httpx.MockTransport(handler), sleep=clock.sleep)
    rows = terminals(directory)
    assert len(payloads) == 3 and payloads[0] == payloads[1]
    assert rows[0]["request_id"] == rows[1]["request_id"]
    assert [r["attempt"] for r in rows] == [1, 2, 1]
    assert result["technical_retries_dispatched"] == 1
    selected = next(r for r in read_jsonl(directory / "slot_outcomes.jsonl")
                    if r["request_id"] == rows[0]["request_id"])
    assert selected["selected_attempt"] == 2 and selected["attempt_count"] == 2
    assert gzip.decompress((tmp_path / rows[0]["response_path"]).read_bytes()) != image_body()


def test_three_failures_stop_instead_of_retrying_a_broken_contract(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    result = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(
        lambda _: httpx.Response(500, json={"error": "mock", "usage": {"cost": 0}})))
    assert result["stop_reason"] == "three_failed_attempts_in_eight_completed"
    assert result["terminal_attempts"] == 3
    assert result["technical_retries_dispatched"] == 1
    assert result["status_counts"] == {"http_error": 2, "never_started": 190}
    assert len(terminals(directory)) == 3


def test_six_retry_cap_is_global_and_failed_seventh_slot_is_retained(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    fail_sequences = set(range(0, 97, 16))
    body = image_body()

    def handler(_):
        intent = events(directory / "generation_events.jsonl")[-1]
        if intent["slot_sequence"] in fail_sequences and intent["attempt"] == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(200, content=body)

    result = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(handler))
    assert result["status"] == "completed"
    assert result["technical_retries_dispatched"] == 6
    assert result["terminal_attempts"] == 198
    assert result["status_counts"] == {"image_returned": 191, "http_error": 1}


@pytest.mark.parametrize("kind", ("unknown_success_cost", "unknown_error_cost", "url", "geometry"))
def test_uncertain_charge_or_delivery_halts_without_a_retry(tmp_path, monkeypatch, kind):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    responses = {
        "unknown_success_cost": httpx.Response(200, content=image_body(None)),
        "unknown_error_cost": httpx.Response(500, json={"error": "cost unavailable"}),
        "url": httpx.Response(200, json={"data": [{"url": "https://example.com/image"}],
                                         "usage": {"cost": 0.01}}),
        "geometry": httpx.Response(200, content=image_body(size=256)),
    }
    calls = []

    def handler(request):
        calls.append(request)
        return responses[kind]

    result = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(handler))
    assert len(calls) == 1 and result["status"] == "stopped"
    assert result["technical_retries_dispatched"] == 0
    if kind.startswith("unknown"):
        assert result["namespace_budget"]["accounted_usd"] == 5
    assert len(read_jsonl(directory / "slot_outcomes.jsonl")) == 192


def test_refusals_are_not_retried_or_rewritten_into_success(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(400, json={"error": {"code": "content_policy_violation"}})
        return httpx.Response(401, json={"error": "mock unauthorized"})

    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(handler))
    assert len(calls) == 2 and receipt["technical_retries_dispatched"] == 0
    assert [r["status"] for r in terminals(directory)] == ["refused", "http_error"]


class PartialBody(httpx.SyncByteStream):
    def __iter__(self):
        yield b'{"partial":'
        raise httpx.ReadTimeout("synthetic interrupted stream")


def test_partial_bytes_survive_read_failure_and_unknown_cost_reserves_five(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(
        lambda _: httpx.Response(200, stream=PartialBody())))
    terminal = terminals(directory)[0]
    assert terminal["status"] == "outcome_uncertain"
    assert gzip.decompress((tmp_path / terminal["response_path"]).read_bytes()) == b'{"partial":'
    assert receipt["namespace_budget"]["accounted_usd"] == 5
    assert receipt["technical_retries_dispatched"] == 0


def test_temporary_reservations_do_not_prematurely_terminate_a_tight_budget(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch, overrides={
        "maximum_in_flight": 2, "maximum_new_spend_usd": 5.01,
    })
    body = image_body()
    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep,
                        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body)))
    assert receipt["stop_reason"] == "spending_reservation_limit"
    assert receipt["terminal_attempts"] == 2
    assert receipt["namespace_budget"]["accounted_usd"] == pytest.approx(0.02)
    assert len(terminals(directory)) == 2


def test_successor_cannot_reset_the_twenty_dollar_namespace_cap(tmp_path, monkeypatch):
    _, _, clock, _ = fixture(tmp_path, monkeypatch)
    prior = tmp_path / common.directory("prv1-previous")
    publish(prior / "generation_freeze.json", dict(budget_baseline_usd=45.6819185))
    append_event(prior / "generation_events.jsonl", dict(
        kind="attempt", request_id="previous", attempt=1, reservation_usd=5))
    append_event(prior / "generation_events.jsonl", dict(
        kind="terminal", request_id="previous", attempt=1, status="image_returned", cost_usd=15.01))
    calls = []
    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep,
                        transport=httpx.MockTransport(lambda request: calls.append(request)))
    assert calls == []
    assert receipt["stop_reason"] == "spending_reservation_limit"
    assert receipt["status_counts"] == {"never_started": 192}
    assert receipt["namespace_budget"]["accounted_usd"] == pytest.approx(15.01)


def test_unknown_predecessor_charge_blocks_a_successor_before_network(tmp_path, monkeypatch):
    _, _, clock, _ = fixture(tmp_path, monkeypatch)
    ledger = tmp_path / common.directory("prv1-previous") / "generation_events.jsonl"
    append_event(ledger, dict(kind="attempt", request_id="prior", attempt=1, reservation_usd=5))
    append_event(ledger, dict(kind="terminal", request_id="prior", attempt=1,
                              status="outcome_uncertain", cost_usd=None))
    with pytest.raises(ValueError, match="unknown charge"):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda _: pytest.fail("must not send")))


def test_unexpected_vendor_bill_halts_and_reports_the_actual_breach(tmp_path, monkeypatch):
    _, _, clock, _ = fixture(tmp_path, monkeypatch)
    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(
        lambda _: httpx.Response(200, content=image_body(cost=21))))
    assert receipt["stop_reason"] == "reported_cost_exceeds_reservation"
    assert receipt["namespace_budget"]["known_cost_usd"] == 21
    assert receipt["spending_limit_breached"]
    assert receipt["terminal_attempts"] == 1


@pytest.mark.parametrize("damage", ("false_gate", "empty_checks", "source_hash", "request_hash",
                                    "uncommitted", "bound_source", "nan_interval"))
def test_gate_binding_and_commit_failures_block_every_post(tmp_path, monkeypatch, damage):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    path = directory / "generation_freeze.json"
    freeze = read_json(path)
    if damage == "false_gate":
        freeze["gates"]["checks"][next(iter(c.GATE_KEYS))] = False
    elif damage == "empty_checks":
        freeze["gates"]["checks"] = {}
    elif damage == "source_hash":
        freeze["source_freeze_sha256"] = "0" * 64
    elif damage == "request_hash":
        freeze["requests_sha256"] = "0" * 64
    elif damage == "uncommitted":
        monkeypatch.setattr(c, "committed", lambda *_: (
            _ for _ in ()).throw(ValueError("uncommitted")))
    elif damage == "bound_source":
        (tmp_path / common.PACKAGE / "collection.py").write_text("altered source")
    elif damage == "nan_interval":
        freeze["config"]["minimum_start_interval_seconds"] = float("nan")
        (tmp_path / common.CONFIG).write_text(json.dumps(freeze["config"]))
    path.write_text(json.dumps(freeze))
    calls = []
    with pytest.raises(ValueError):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda request: calls.append(request)))
    assert calls == []
    assert not (directory / "generation_events.jsonl").exists()


def test_existing_marker_or_pending_intent_blocks_redispatch(tmp_path, monkeypatch):
    directory, requests, clock, _ = fixture(tmp_path, monkeypatch)
    append_event(directory / "generation_events.jsonl", dict(
        kind="attempt", request_id=requests[0]["request_id"], attempt=1, reservation_usd=5))
    calls = []
    with pytest.raises(ValueError, match="interrupted"):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda request: calls.append(request)))
    assert calls == [] and c.budget_state(tmp_path)["accounted_usd"] == 5


def test_interruption_after_intent_is_unresolved_not_never_started(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(c.ThreadPoolExecutor, "submit", lambda *_: (
        _ for _ in ()).throw(KeyboardInterrupt("synthetic")))
    with pytest.raises(KeyboardInterrupt):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda _: pytest.fail("must not send")))
    receipt = read_json(directory / "collection_receipt.json")
    assert receipt["status_counts"] == {"outcome_unresolved": 1, "never_started": 191}
    assert receipt["namespace_budget"]["accounted_usd"] == 5
    assert receipt["attempt_intents"] == 1 and receipt["terminal_attempts"] == 0
    selected = next(r for r in read_jsonl(directory / "slot_outcomes.jsonl")
                    if r["status"] == "outcome_unresolved")
    assert selected["unknown_cost"] and selected["pending_attempts"]


def test_bound_mutation_stops_after_retaining_the_completed_response(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    calls = []

    def handler(request):
        calls.append(request)
        (tmp_path / common.PACKAGE / "collection.py").write_text("changed during collection")
        return httpx.Response(200, content=image_body())

    with pytest.raises(ValueError, match="bound input changed"):
        c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(handler))
    assert len(calls) == 1
    assert read_json(directory / "collection_receipt.json")["status"] == "stopped"
    assert terminals(directory)[0]["status"] == "image_returned"


def test_credential_echo_is_suppressed_and_halts_without_storing_the_key(tmp_path, monkeypatch):
    directory, _, clock, secret = fixture(tmp_path, monkeypatch)
    receipt = c.collect(tmp_path, RUN, sleep=clock.sleep, transport=httpx.MockTransport(
        lambda _: httpx.Response(403, json={"error": secret})))
    row = terminals(directory)[0]
    assert receipt["stop_reason"] == "unknown_charge"
    assert row["credential_echo_suppressed"]
    assert secret.encode() not in gzip.decompress((tmp_path / row["response_path"]).read_bytes())
    assert secret not in (directory / "generation_events.jsonl").read_text()


def test_actual_qualification_failure_blocks_a_manually_ready_freeze(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(generation_prepare, "verify_qualification", lambda *_: (
        _ for _ in ()).throw(ValueError("actual human qualification missing")))
    with pytest.raises(ValueError, match="actual human qualification"):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (directory / "generation_events.jsonl").exists()


def test_stale_metadata_blocks_live_start_but_not_measurement_verification(tmp_path, monkeypatch):
    directory, _, clock, _ = fixture(tmp_path, monkeypatch)
    freeze_path = directory / "generation_freeze.json"
    freeze = read_json(freeze_path)
    provider = tmp_path / freeze["provider_preflight_path"]
    provider.write_text(json.dumps(dict(
        checked_at_utc=(datetime.now(timezone.utc) - timedelta(hours=25)).isoformat())))
    freeze["inputs"] = bindings(tmp_path, [Path(row["path"]) for row in freeze["inputs"]])
    freeze_path.write_text(json.dumps(freeze))
    # The frozen file identity is valid; elapsed wall time alone does not invalidate a replay.
    c.verify_generation(tmp_path, RUN)
    with pytest.raises(ValueError, match="24 hours"):
        c.collect(tmp_path, RUN, sleep=clock.sleep,
                  transport=httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (directory / "generation_events.jsonl").exists()
