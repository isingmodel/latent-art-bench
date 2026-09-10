"""Offline paid-transport accounting and full artificial grid; no live service."""

import base64
import copy
import io
import json
import threading
import time
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import events, publish
from latent_art_bench.painter_map_validation_v2 import analysis, common, metadata
from latent_art_bench.painter_map_validation_v2 import collection as c
from latent_art_bench.painter_map_validation_v2 import workflow as w

ROOT = Path(__file__).resolve().parents[2]


def image_body(cost=0.07, model=common.MODEL, size=512, alpha=255):
    data = io.BytesIO()
    Image.new("RGBA", (size, size), (70, 90, 120, alpha)).save(data, format="PNG")
    value = dict(model=model, data=[dict(b64_json=base64.b64encode(data.getvalue()).decode())])
    if cost is not None:
        value["usage"] = dict(cost=cost)
    return json.dumps(value).encode()


def test_exact_plan_and_no_rendering_seed_or_size():
    plan = common.build_plan(ROOT)
    assert len(common.validate_design(plan, common.configuration(ROOT))) == 120
    assert len({r["block_id"] for r in plan}) == 120
    assert len({r["template_id"] for r in plan}) == 12
    assert {r["repetition"] for r in plan[:24]} != {0}
    for row in plan:
        assert set(row["payload"]) == {
            "model",
            "prompt",
            "n",
            "aspect_ratio",
            "provider",
            "output_format",
        }
        assert row["payload"]["provider"] == dict(
            only=["black-forest-labs/us-3"], allow_fallbacks=False
        )
        assert row["payload"]["aspect_ratio"] == "1:1"
    for field in ("sequence", "arm", "payload", "block_order"):
        changed = copy.deepcopy(plan)
        changed[0][field] = False
        with pytest.raises(ValueError):
            common.validate_design(changed, common.configuration(ROOT))


@pytest.mark.parametrize("code", [400, 401, 402, 403, 404, 422, 429])
def test_explicit_rejection_convention_and_usage_precedence(code):
    value = {"error": {"code": code, "message": "rejected"}}
    assert c.cost_record(json.dumps(value), code, True) == (
        0.0,
        "retained_explicit_client_rejection",
    )
    value["usage"] = {"cost": 0.09}
    assert c.cost_record(json.dumps(value), code, True) == (0.09, "provider_reported")
    assert c.cost_record(json.dumps(value), code, False) == (None, "unresolved")


@pytest.mark.parametrize(
    "value,code",
    [
        ({"error": {"message": "server", "code": None}}, 500),
        ({"error": {"message": "rejection"}, "data": []}, 429),
        ({"error": "rejection"}, 429),
        ({"error": {}}, 429),
        ([], 429),
        ({"usage": {"cost": True}}, 200),
        ({"usage": {"cost": -1}}, 200),
        ({"usage": {"cost": float("nan")}}, 200),
    ],
)
def test_no_heuristic_free_unknown_response(value, code):
    assert c.cost_record(json.dumps(value), code, True) == (None, "unresolved")


def state(known=0, pending=0, settled=0, unknown=0):
    return dict(
        new_reported_usd=known,
        new_reserves_usd=5 * (pending + unknown),
        terminal_reserves_usd=5 * unknown,
        pending_paid=pending,
        settled_attempts=settled,
        accounted_usd=50.7219185 + known + 5 * (pending + unknown),
        unknown=["unknown"] * unknown,
        pending=["pending"] * pending,
    )


def test_conditional_credit_forecast_and_reservation_are_distinct():
    config = common.expected_config()
    assert c.admission(state(), config, Decimal("19.25")) == "admit"
    assert c.admission(state(pending=1), config, Decimal("19.25")) == "admit"
    assert (
        c.admission(state(known=14.3, pending=1, settled=204), config, 19.25)
        == "wait_in_flight_reserve"
    )
    assert c.admission(state(known=14.3, settled=204), config, 19.25) == "admit"
    assert c.admission(state(known=16.8, settled=240), config, 19.25) == "admit"
    assert c.admission(state(), config, Decimal("18.5999999")) == "stop_remaining_full_grid_budget"
    assert c.admission(state(unknown=1, settled=1), config, 19.25) == "stop_unknown_cost"
    assert (
        c.admission(state(known=19, settled=200), config, 19.25)
        == "stop_remaining_full_grid_budget"
    )


def test_timing_records_spacing_and_overlap():
    def row(start, latency):
        return dict(post_started=True, transport_started_monotonic=start, latency_seconds=latency)

    assert c.timing_contract([row(0, 8), row(5, 3), row(10, 3)])
    assert not c.timing_contract([row(0, 8), row(4.99, 3)])
    assert not c.timing_contract([row(0, 15), row(5, 10), row(10, 5)])
    assert not c.timing_contract([dict(post_started=True)])


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    config, requests = common.configuration(ROOT), common.build_plan(ROOT)
    freeze = dict(config=config)
    directory = tmp_path / common.directory(common.RUN_ID)
    publish(directory / "freeze.json", freeze)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    for name in ("receipt.json", "started.json"):
        publish(tmp_path / metadata.directory(common.DISPATCH_ID) / name, {"artificial": True})
    monkeypatch.setattr(common, "requests", lambda *a: requests)
    monkeypatch.setattr(w, "verify", lambda *a: freeze)
    monkeypatch.setattr(w, "dispatch_metadata", lambda *a, **k: ({}, Decimal("19.25")))
    monkeypatch.setattr(w, "verify_dispatch_metadata", lambda *a: ({}, Decimal("19.25")))
    monkeypatch.setattr(c, "key_from_env", lambda *a: "artificial-secret")
    monkeypatch.setattr(c, "retry_delay", lambda r: 0)
    # Remove wall-clock waits only; real spacing/overlap predicate has separate tests.
    monkeypatch.setattr(
        c,
        "OrderedStartGate",
        lambda stop, *a: lambda ticket: None if stop.is_set() else time.monotonic(),
    )
    monkeypatch.setattr(c, "timing_contract", lambda *a, **k: True)
    monkeypatch.setattr(w, "timing_contract", lambda *a, **k: True)
    return SimpleNamespace(
        root=tmp_path,
        directory=directory,
        requests=requests,
        freeze=freeze,
        config=config,
        body=image_body(),
    )


def run(cohort, handler=None):
    def success(request):
        assert request.method == "POST"
        assert str(request.url) == c.legacy.OPENROUTER_URL
        assert request.headers["authorization"] == "Bearer artificial-secret"
        return httpx.Response(200, content=cohort.body)

    return c.collect(cohort.root, common.RUN_ID, transport=httpx.MockTransport(handler or success))


def test_complete_240_transport_accounting_and_one_shot(cohort):
    receipt = run(cohort)
    assert receipt["analysis_eligible"] is True
    assert receipt["slot_counts"] == {"image_returned": 240}
    assert receipt["budget"]["new_reported_usd"] == 16.8
    assert receipt["budget"]["accounted_usd"] == 67.5219185
    assert receipt["budget"]["pending"] == []
    assert len(w.collection_inputs(cohort.root, common.RUN_ID)[3]) == 240
    with pytest.raises(ValueError, match="never resume"):
        run(cohort)


@pytest.mark.parametrize(
    "kind", ["refused", "server500", "timeout", "wrong_model", "unknown_success", "overcharge"]
)
def test_first_unavailable_or_unknown_slot_stops_and_drains(cohort, kind):
    calls = []

    def handler(request):
        calls.append(request.content)
        if len(calls) > 1:
            return httpx.Response(200, content=cohort.body)
        if kind == "timeout":
            raise httpx.ReadTimeout("private request error")
        if kind == "refused":
            return httpx.Response(
                400, json={"error": {"code": "moderation_blocked", "message": "refused"}}
            )
        if kind == "server500":
            return httpx.Response(500, json={"error": {"code": None, "message": "server"}})
        body = (
            image_body(model="wrong")
            if kind == "wrong_model"
            else image_body(None if kind == "unknown_success" else 5.1)
        )
        return httpx.Response(200, content=body)

    receipt = run(cohort, handler)
    assert receipt["status"] == "stopped" and receipt["analysis_eligible"] is False
    assert receipt["attempts"] <= 2
    assert receipt["budget"]["pending"] == []
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_exact_429_retries_same_payload_once(cohort):
    calls = []

    def handler(request):
        calls.append(request.content)
        if len(calls) == 1:
            return httpx.Response(429, json={"error": {"code": 429, "message": "temporary"}})
        return httpx.Response(200, content=cohort.body)

    receipt = run(cohort, handler)
    assert receipt["analysis_eligible"] is True and receipt["attempts"] == 241
    ledger = events(cohort.directory / "generation_events.jsonl")
    retry = [r for r in ledger if r["kind"] == "attempt" and r["attempt"] == 2][0]
    first = next(
        r for r in ledger if r["kind"] == "attempt" and r["request_id"] == retry["request_id"]
    )
    assert first["payload_sha256"] == retry["payload_sha256"]
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_second_technical_failure_permanently_closes(cohort):
    counts = {}

    def handler(request):
        prompt = json.loads(request.content)["prompt"]
        counts[prompt] = counts.get(prompt, 0) + 1
        return httpx.Response(429, json={"error": {"code": 429, "message": "temporary"}})

    receipt = run(cohort, handler)
    assert receipt["analysis_eligible"] is False
    assert max(counts.values()) <= 2 and len(counts) <= 2
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_last_success_overcharge_is_ineligible(cohort):
    calls = 0
    lock = threading.Lock()

    def handler(request):
        nonlocal calls
        with lock:
            calls += 1
            last = calls == 240
        return httpx.Response(200, content=image_body(5.1) if last else cohort.body)

    receipt = run(cohort, handler)
    assert receipt["slot_counts"] == {"image_returned": 240}
    assert receipt["reason"] == "reported_cost_exceeds_reservation"
    assert receipt["analysis_eligible"] is False
    assert "terminal_budget_exceeded" in receipt["analysis_unavailability_reasons"]
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_final_identity_failure_overrides_complete_grid(cohort, monkeypatch):
    monkeypatch.setattr(
        w, "verify_dispatch_metadata", lambda *a: (_ for _ in ()).throw(ValueError("changed"))
    )
    receipt = run(cohort)
    assert receipt["slot_counts"] == {"image_returned": 240}
    assert receipt["identity_contract_met"] is False and receipt["analysis_eligible"] is False
    monkeypatch.setattr(w, "verify_dispatch_metadata", lambda *a: ({}, Decimal("19.25")))
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_full_240_measure_and_replay_with_artificial_extraction(cohort, monkeypatch):
    run(cohort)
    inputs = analysis.load_inputs(ROOT)  # fixed retained numeric lineage, no old pixels
    publish(cohort.root / common.INPUTS, inputs)
    rng = np.random.default_rng(177)
    feature_vectors = rng.normal(size=(240, 31))

    def fake_measure(path, item, pipelines):
        assert path.exists() and pipelines == ("primary512",)
        return [
            dict(
                item,
                pipeline="primary512",
                status="measured",
                values=feature_vectors[item["sequence"]].tolist(),
            )
        ]

    monkeypatch.setattr(w, "measure_path", fake_measure)
    w.measure(cohort.root, common.RUN_ID)
    assert len(read_jsonl(cohort.directory / "measurements.jsonl")) == 240
    assert w.check(cohort.root, common.RUN_ID)["status"] == "numbers_replayed"
    receipt = read_json(cohort.directory / "measurement_receipt.json")
    assert len(receipt["outputs"]) == 4
    receipt["outputs"].pop()
    (cohort.directory / "measurement_receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="output inventory"):
        w.check(cohort.root, common.RUN_ID)


def test_real_live_gate_precedes_source_or_key(monkeypatch):
    monkeypatch.setattr(w, "verify", lambda *a: pytest.fail("source read before explicit gate"))
    with pytest.raises(ValueError, match="explicit live"):
        c.collect(ROOT, common.RUN_ID)
    with pytest.raises(ValueError, match="explicit live"):
        metadata.run(ROOT, common.PREFLIGHT_ID)


def test_exact_retained_budget_schema_and_input_lineage(tmp_path, monkeypatch):
    assert w.historical_budget(ROOT, common.configuration(ROOT))["accounted_usd"] == 50.7219185
    value = analysis.load_inputs(ROOT)
    publish(tmp_path / common.INPUTS, value)
    monkeypatch.setattr(analysis, "load_inputs", lambda root: value)
    w.validate_input_lineage(tmp_path)
    altered = copy.deepcopy(value)
    altered["reference"]["values"][0][0] += 0.001
    (tmp_path / common.INPUTS).write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="exact immutable"):
        w.validate_input_lineage(tmp_path)


def git(root, *args):
    import subprocess

    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def metadata_repo(tmp_path, monkeypatch):
    from latent_art_bench.io import hash_file

    for relative in (
        common.PREFLIGHT_SOURCE,
        common.PACKAGE / "metadata.py",
        common.PACKAGE / "common.py",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Offline Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "artificial metadata source")
    monkeypatch.setattr(metadata, "key_from_env", lambda root: "test-secret-never-output")
    endpoint = read_json(ROOT / common.ENDPOINT_METADATA)["response_body"].encode()
    assert hash_file(tmp_path / common.PREFLIGHT_SOURCE)
    return tmp_path, endpoint


def test_metadata_exact_two_gets_precision_and_create_once(metadata_repo):
    root, endpoint = metadata_repo
    urls = []

    def handler(request):
        urls.append(str(request.url))
        assert request.method == "GET"
        if str(request.url).endswith("/credits"):
            assert request.headers["authorization"] == "Bearer test-secret-never-output"
            return httpx.Response(
                200,
                content=b'{"data":{"total_credits":20.000000000000001,"total_usage":0.75}}',
            )
        assert "authorization" not in request.headers
        return httpx.Response(200, content=endpoint)

    result = metadata.run(root, common.PREFLIGHT_ID, transport=httpx.MockTransport(handler))
    assert len(urls) == 2 and "test-secret" not in json.dumps(result)
    _, available = metadata.validate(root, common.PREFLIGHT_ID)
    assert available == Decimal("19.250000000000001")
    with pytest.raises(ValueError, match="create-once"):
        metadata.run(root, common.PREFLIGHT_ID, transport=httpx.MockTransport(handler))
    assert len(urls) == 2


@pytest.mark.parametrize(
    "kind", ["redirect", "wrong_endpoint", "malformed", "insufficient", "echo"]
)
def test_metadata_unavailable_or_changed_is_not_authorization(metadata_repo, kind):
    root, endpoint = metadata_repo

    def handler(request):
        if str(request.url).endswith("/credits"):
            if kind == "redirect":
                return httpx.Response(302, headers={"location": "https://unallowed.invalid"})
            if kind == "malformed":
                return httpx.Response(200, json={"data": []})
            if kind == "echo":
                return httpx.Response(200, content=b"test-secret-never-output")
            return httpx.Response(
                200,
                json={
                    "data": {
                        "total_credits": 10 if kind == "insufficient" else 20,
                        "total_usage": 0,
                    }
                },
            )
        return httpx.Response(200, content=endpoint + (b" " if kind == "wrong_endpoint" else b""))

    value = metadata.run(root, common.PREFLIGHT_ID, transport=httpx.MockTransport(handler))
    assert len(value["requests"]) == 2
    assert "test-secret" not in json.dumps(value)
    with pytest.raises(ValueError):
        metadata.validate(root, common.PREFLIGHT_ID)


def test_no_metadata_before_exact_source_commit(metadata_repo):
    root, _ = metadata_repo
    with (root / common.PACKAGE / "common.py").open("a") as handle:
        handle.write("\n# uncommitted change\n")
    with pytest.raises(ValueError, match="commit exact"):
        metadata.run(
            root,
            common.PREFLIGHT_ID,
            transport=httpx.MockTransport(lambda r: pytest.fail("network")),
        )


def test_minimal_real_git_prepare_verify_gate(tmp_path, monkeypatch):
    from latent_art_bench.io import hash_file
    from latent_art_bench.painter_feature_generation_v2.artifacts import bindings

    for relative in (common.CONFIG, common.SCENES, common.PACKAGE / "common.py"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    publish(tmp_path / common.INPUTS, analysis.load_inputs(ROOT))
    publish(tmp_path / common.METADATA, {"artificial": True})
    paths = [
        common.CONFIG,
        common.SCENES,
        common.PACKAGE / "common.py",
        common.INPUTS,
        common.METADATA,
        common.QUALIFICATION,
    ]
    monkeypatch.setattr(w, "source_paths", lambda root: paths)
    monkeypatch.setattr(w, "numerical_qualification", lambda root: {"selected_outputs": 240})
    monkeypatch.setattr(w, "historical_budget", lambda root, config: {"accounted_usd": 50.7219185})
    monkeypatch.setattr(metadata, "validate", lambda *a: ({}, Decimal("19.25")))
    monkeypatch.setattr(analysis, "load_inputs", lambda root: read_json(ROOT / common.INPUTS))
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Offline Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "artificial qualified source")
    source = git(tmp_path, "rev-parse", "HEAD").stdout.decode().strip()
    publish(
        tmp_path / common.QUALIFICATION,
        dict(
            schema="painter-map-validation-qualification/2",
            qualified=True,
            source_commit=source,
            source_bindings=bindings(tmp_path, paths[:-1]),
        ),
    )
    with pytest.raises(ValueError, match="commit exact prospective"):
        w.prepare(tmp_path, common.RUN_ID)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "artificial qualification")
    w.prepare(tmp_path, common.RUN_ID)
    with pytest.raises(ValueError, match="commit exact prospective"):
        w.verify(tmp_path, common.RUN_ID)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "artificial freeze")
    assert len(w.verify(tmp_path, common.RUN_ID)["inputs"]) == len(paths)
    assert hash_file(tmp_path / common.directory(common.RUN_ID) / "freeze.json")
    with (tmp_path / common.PACKAGE / "common.py").open("a") as handle:
        handle.write("\n# changed source\n")
    with pytest.raises(ValueError, match="commit exact prospective"):
        w.verify(tmp_path, common.RUN_ID)


@pytest.mark.parametrize(
    "field,value",
    [
        ("transport_started_monotonic", float("nan")),
        ("transport_started_monotonic", float("inf")),
        ("transport_started_monotonic", True),
        ("latency_seconds", float("nan")),
        ("latency_seconds", float("inf")),
        ("latency_seconds", -1),
        ("latency_seconds", True),
        ("post_started", 1),
    ],
)
def test_timing_invalid_numeric_fields_fail(field, value):
    row = dict(post_started=True, transport_started_monotonic=10.0, latency_seconds=1.0)
    row[field] = value
    assert c.timing_contract([row]) is False


def test_low_total_final_overcharge_cannot_forge_complete_receipt(cohort):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(200, content=image_body(5.01 if calls == 240 else 0.01))

    receipt = run(cohort, handler)
    assert receipt["slot_counts"] == {"image_returned": 240}
    assert receipt["budget"]["new_reported_usd"] == 7.40
    assert receipt["reason"] == "reported_cost_exceeds_reservation"
    receipt.update(
        status="complete", reason=None, analysis_eligible=True, analysis_unavailability_reasons=[]
    )
    (cohort.directory / "collection_receipt.json").write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="disposition"):
        w.collection_inputs(cohort.root, common.RUN_ID)


@pytest.mark.parametrize("failures,complete", [(8, True), (9, False)])
def test_eight_retries_are_allowed_but_ninth_needed_stops(cohort, failures, complete):
    calls = 0
    failures_seen = 0
    lock = threading.Lock()

    def handler(request):
        nonlocal calls, failures_seen
        with lock:
            calls += 1
            fail = (calls - 1) % 26 == 0 and failures_seen < failures
            failures_seen += fail
        if fail:
            return httpx.Response(429, json={"error": {"code": 429, "message": "technical"}})
        return httpx.Response(200, content=cohort.body)

    receipt = run(cohort, handler)
    assert receipt["analysis_eligible"] is complete
    assert receipt["retry_intents"] == 8 and receipt["attempts"] <= 248
    if not complete:
        assert receipt["reason"] == "technical_retry_limit"
    w.collection_inputs(cohort.root, common.RUN_ID)


def test_storage_stop_is_terminal_without_network(cohort, monkeypatch):
    monkeypatch.setattr(c.shutil, "disk_usage", lambda root: SimpleNamespace(free=0))
    receipt = run(cohort, lambda r: pytest.fail("image call despite storage gate"))
    assert receipt["reason"] == "storage_reserve" and receipt["attempts"] == 0
    assert receipt["analysis_eligible"] is False
    w.collection_inputs(cohort.root, common.RUN_ID)
