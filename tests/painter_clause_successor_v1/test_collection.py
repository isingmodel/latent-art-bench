"""Offline transport failures and qualified-source gates; never contact a service."""

import base64
import copy
import gzip
import hashlib
import io
import json
import subprocess
import threading
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_clause_successor_v1 import collection as c
from latent_art_bench.painter_clause_successor_v1 import common
from latent_art_bench.painter_clause_successor_v1 import workflow as w
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    events,
    publish,
)
from latent_art_bench.painter_responsiveness_recovery_v1.collection import EXACT_BODY


def image_body(*, size=512, alpha=255, model="gpt-image-2"):
    buffer = io.BytesIO()
    Image.new("RGBA", (size, size), (60, 90, 150, alpha)).save(buffer, format="PNG")
    return json.dumps(
        dict(model=model, data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())])
    ).encode()


@pytest.fixture
def cohort(tmp_path, monkeypatch):
    requests = []
    for block in range(6):
        for within, arm in enumerate(common.ARMS):
            requests.append(
                dict(
                    request_id=f"b{block}:{arm}",
                    sequence=len(requests),
                    block_id=f"b{block}",
                    block_order=block + 1,
                    within_block=within,
                    route=c.OAUTH_ROUTE,
                    template_id=f"scene{block}",
                    content_class=common.CLASSES[block % 3],
                    repetition=0,
                    arm=arm,
                    experiment="clause_successor",
                    payload=dict(model="gpt-image-2", prompt=f"b{block}:{arm}", n=1),
                )
            )
    config = dict(
        maximum_images=len(requests),
        maximum_attempts=len(requests) + 8,
        maximum_technical_retries=8,
        maximum_in_flight=2,
        minimum_start_interval_seconds=0,
        maximum_collection_seconds=86400,
        minimum_free_bytes=0,
        historical_accounted_usd=c.HISTORICAL_ACCOUNTED_USD,
    )
    freeze = dict(config=config, proxy_snapshot={"fixed": True})
    directory = tmp_path / common.directory(common.RUN_ID)
    publish(directory / "freeze.json", freeze)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    monkeypatch.setattr(common, "requests", lambda *a, **k: requests)
    monkeypatch.setattr(w, "verify", lambda *a: freeze)
    monkeypatch.setattr(c.legacy, "proxy_snapshot", lambda *a: freeze["proxy_snapshot"])
    monkeypatch.setattr(c, "retry_delay", lambda row: 0)
    return SimpleNamespace(
        root=tmp_path,
        run=common.RUN_ID,
        directory=directory,
        config=config,
        requests=requests,
        freeze=freeze,
        body=image_body(),
    )


def run(cohort, handler=None):
    def success(request):
        assert request.method == "POST"
        assert str(request.url) == c.legacy.OAUTH_URL
        assert "authorization" not in request.headers
        return httpx.Response(200, content=cohort.body)

    return c.collect(
        cohort.root,
        cohort.run,
        Path("unused-proxy"),
        transport=httpx.MockTransport(handler or success),
    )


def test_complete_zero_cost_and_one_shot(cohort):
    result = run(cohort)
    assert result["status"] == "complete"
    assert result["identity_contract_met"] is True
    assert result["slot_counts"] == {"image_returned": 12}
    assert result["posted_attempts"] == 12
    assert result["budget"]["accounted_usd"] == 50.7219185
    assert result["budget"]["subscription_monetary_value"] is None
    assert result["budget"]["pending"] == []
    assert result["retries"] == 0
    assert len(w.collection_inputs(cohort.root, cohort.run)[3]) == 12
    assert w.verify_responses(cohort.root, cohort.run)["checked"] == 12
    with pytest.raises(ValueError, match="never resume"):
        run(cohort)


def test_real_transport_requires_explicit_live_before_any_gate(monkeypatch):
    monkeypatch.setattr(w, "verify", lambda *a: pytest.fail("gate should not run"))
    with pytest.raises(ValueError, match="explicit live"):
        c.collect(Path("unused"), common.RUN_ID, Path("unused"))


@pytest.mark.parametrize(
    "mutation", ["route", "model", "sequence", "duplicate", "block", "arm", "experiment"]
)
def test_invalid_inventory_rejected_before_dispatch(cohort, mutation):
    if mutation == "route":
        cohort.requests[0]["route"] = "flux_2_max"
    elif mutation == "model":
        cohort.requests[0]["payload"]["model"] = "paid-model"
    elif mutation == "sequence":
        cohort.requests[0]["sequence"] = 99
    elif mutation == "duplicate":
        cohort.requests[0]["request_id"] = cohort.requests[1]["request_id"]
    elif mutation == "block":
        cohort.requests[0]["block_order"] = 9
    elif mutation == "arm":
        cohort.requests[0]["arm"] = "monet"
    else:
        cohort.requests[0]["experiment"] = "clause"
    with pytest.raises(ValueError):
        run(cohort, lambda r: pytest.fail("invalid inventory dispatched"))


@pytest.mark.parametrize("kind", ["json", "exact"])
def test_only_exact_technical_retry_same_payload(cohort, kind):
    calls = []

    def handler(request):
        calls.append(request.content)
        if len(calls) == 1:
            return (
                httpx.Response(503, content=EXACT_BODY, headers={"content-type": "text/plain"})
                if kind == "exact"
                else httpx.Response(
                    503, json={"error": {"code": 503, "message": "technical failure"}}
                )
            )
        return httpx.Response(200, content=cohort.body)

    result = run(cohort, handler)
    assert result["status"] == "complete"
    assert result["attempts"] == 13 and result["retries"] == 1
    assert calls[0] == calls[1]
    assert read_jsonl(cohort.directory / "slot_outcomes.jsonl")[0]["selected_attempt"] == 2
    w.collection_inputs(cohort.root, cohort.run)


def test_at_most_one_retry_per_slot_and_cluster_stops(cohort):
    calls = Counter()

    def handler(request):
        calls[json.loads(request.content)["prompt"]] += 1
        return httpx.Response(503, json={"error": {"code": 503, "message": "technical"}})

    result = run(cohort, handler)
    assert result["reason"] == "three_failures_in_latest_eight"
    assert max(calls.values()) <= 2
    assert result["slot_counts"]["not_attempted_collection_stopped"] > 0
    w.collection_inputs(cohort.root, cohort.run)


@pytest.mark.parametrize("limit", [2, 8])
def test_global_retry_cap_without_error_cluster(cohort, monkeypatch, limit):
    cohort.config["maximum_technical_retries"] = limit
    monkeypatch.setattr(c, "stop_reason", lambda *a: None)
    calls = Counter()

    def handler(request):
        prompt = json.loads(request.content)["prompt"]
        calls[prompt] += 1
        return (
            httpx.Response(503, json={"error": {"code": 503, "message": "technical"}})
            if calls[prompt] == 1
            else httpx.Response(200, content=cohort.body)
        )

    result = run(cohort, handler)
    assert result["retry_decisions"] == result["retry_intents"] == result["retries"] == limit
    assert result["reason"] == "technical_retry_limit"
    assert result["attempts"] == 2 * limit + 1
    assert result["slot_counts"] == {
        "image_returned": limit,
        "http_error": 1,
        "not_attempted_collection_stopped": 11 - limit,
    }
    w.collection_inputs(cohort.root, cohort.run)


@pytest.mark.parametrize(
    "body,code",
    [
        (b"not-json", 200),
        (image_body(size=64), 200),
        (image_body(alpha=20), 200),
        (image_body(model="wrong-model"), 200),
        (b"unauthorized", 401),
        (b"contract", 422),
    ],
)
def test_contract_and_unsupported_success_stop(cohort, body, code):
    result = run(cohort, lambda r: httpx.Response(code, content=body))
    assert result["status"] == "stopped"
    assert result["identity_contract_met"] is False
    assert result["retries"] == 0
    assert result["slot_counts"]["not_attempted_collection_stopped"] > 0


def test_read_failure_is_uncertain_and_never_retried(cohort):
    def handler(request):
        raise httpx.ReadError("lost connection after admission", request=request)

    result = run(cohort, handler)
    assert result["reason"] == "uncertain_or_unsupported_delivery"
    assert result["retries"] == 0
    assert result["slot_counts"]["outcome_uncertain"] == 1


def test_response_cap_retains_prefix_and_stops(cohort, monkeypatch):
    monkeypatch.setattr(c, "MAX_RESPONSE", 16)
    result = run(cohort)
    assert result["reason"] == "uncertain_or_unsupported_delivery"
    row = events(cohort.directory / "generation_events.jsonl")[-1]
    assert row["response_bytes"] == 16 and row["received_bytes"] > 16
    assert len(w.response_bytes(cohort.root, cohort.run, row)) == 16


@pytest.mark.parametrize("cause", ["deadline", "disk", "proxy", "accounting"])
def test_gates_stop_before_new_post(cohort, monkeypatch, cause):
    if cause == "deadline":
        cohort.config["maximum_collection_seconds"] = 300
    elif cause == "disk":
        cohort.config["minimum_free_bytes"] = 10**30
    elif cause == "proxy":
        monkeypatch.setattr(c.legacy, "proxy_snapshot", lambda *a: {"changed": True})
    else:
        cohort.config["historical_accounted_usd"] = 1
    if cause in ("proxy", "accounting"):
        with pytest.raises(ValueError):
            run(cohort, lambda r: pytest.fail("blocked post"))
    else:
        result = run(cohort, lambda r: pytest.fail("blocked post"))
        assert result["posted_attempts"] == 0
        assert result["slot_counts"] == {"not_attempted_collection_stopped": 12}


def test_completion_order_cluster_and_two_worker_bound(cohort):
    lock, starts, ends, active = threading.Lock(), [], [], []
    cohort.config["minimum_start_interval_seconds"] = 0.02

    def handler(request):
        name = json.loads(request.content)["prompt"]
        with lock:
            starts.append((name, time.monotonic()))
            active.append(name)
            assert len(active) <= 2
        time.sleep(0.35 if name.endswith("generic") else 0.015)
        with lock:
            active.remove(name)
            ends.append((name, time.monotonic()))
        return httpx.Response(200, content=cohort.body)

    result = run(cohort, handler)
    assert result["status"] == "complete"
    assert all(b[1] - a[1] >= 0.018 for a, b in zip(starts, starts[1:]))
    for block in (1, 2):
        assert min(t for n, t in starts if n.startswith(f"b{block}:")) >= max(
            t for n, t in ends if n.startswith(f"b{block - 1}:")
        )
    actual = [
        r["request_id"]
        for r in events(cohort.directory / "generation_events.jsonl")
        if r["kind"] == "terminal"
    ]
    # Full response validation follows HTTP-body completion; check a deliberately
    # wide separation, not a race between similarly timed decode operations.
    assert actual.index("b0:cezanne") < actual.index("b0:generic")


def test_worker_exception_drained_and_accounted(cohort, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("unexpected worker error")

    monkeypatch.setattr(c, "_send", explode)
    result = run(cohort)
    assert result["reason"] == "uncertain_or_unsupported_delivery"
    assert result["budget"]["pending"] == []
    w.collection_inputs(cohort.root, cohort.run)


def test_existing_workspace_and_unresolved_intent_block(cohort):
    path = cohort.root / common.MANIFESTS / "old" / "generation_events.jsonl"
    append_event(
        path,
        dict(
            kind="attempt",
            request_id="pending",
            attempt=1,
            route=c.OAUTH_ROUTE,
            paid=False,
            reserved_usd=0,
        ),
    )
    with pytest.raises(ValueError, match="unresolved"):
        run(cohort)


def test_retained_response_tamper_and_path_escape(cohort):
    run(cohort)
    row = next(
        r for r in events(cohort.directory / "generation_events.jsonl") if r["kind"] == "terminal"
    )
    with pytest.raises(ValueError):
        w.response_bytes(cohort.root, cohort.run, dict(row, response_path="../outside.gz"))
    path = cohort.root / row["response_path"]
    path.write_bytes(gzip.compress(b"changed"))
    with pytest.raises(ValueError, match="storage hash"):
        w.verify_responses(cohort.root, cohort.run)


def test_receipt_bound_output_tamper_rejected(cohort):
    run(cohort)
    with (cohort.directory / "slot_outcomes.jsonl").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="bound input changed"):
        w.collection_inputs(cohort.root, cohort.run)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


@pytest.fixture
def qualified(tmp_path, monkeypatch):
    git(tmp_path, "init", "--quiet")
    git(tmp_path, "config", "user.email", "offline@example.invalid")
    git(tmp_path, "config", "user.name", "Offline Test")
    required = (
        common.CONFIG,
        common.SCENES,
        common.INPUTS,
        w.predecessor.common.INPUTS,
        common.STUDIES / "PROTOCOL.md",
        common.STUDIES / "DESIGN_DECISION.md",
        common.PACKAGE / "analysis.py",
        Path("tests") / common.NAMESPACE / "test_a.py",
    )
    for path in required:
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("{}\n")
    projected = synthetic_inputs()
    prior_inputs = {k: projected[k] for k in ("targets", "reference", "scalers")}
    (tmp_path / w.predecessor.common.INPUTS).write_text(json.dumps(prior_inputs))
    projected["origin"]["sha256"] = hash_file(tmp_path / w.predecessor.common.INPUTS)
    (tmp_path / common.INPUTS).write_text(json.dumps(projected))
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "--quiet", "-m", "scientific source")
    value = dict(
        schema="painter-clause-successor-qualification/1",
        qualified=True,
        source_commit=git(tmp_path, "rev-parse", "HEAD"),
        source_bindings=bindings(tmp_path, required),
    )
    publish(tmp_path / common.QUALIFICATION, value)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "--quiet", "-m", "qualification after source")
    return tmp_path, value, required


def test_qualification_accepts_earlier_exact_source_commit(qualified):
    root, value, _ = qualified
    assert value["source_commit"] != git(root, "rev-parse", "HEAD")
    assert w.qualification(root) == value


@pytest.mark.parametrize("mutation", ["bool", "missing", "duplicate", "commit", "bytes", "new"])
def test_qualification_rejects_unqualified_or_changed_source(qualified, mutation):
    root, value, required = qualified
    if mutation == "bool":
        value["qualified"] = 1
    elif mutation == "missing":
        value["source_bindings"].pop()
    elif mutation == "duplicate":
        value["source_bindings"].append(value["source_bindings"][0])
    elif mutation == "commit":
        value["source_commit"] = "0" * 40
    elif mutation == "bytes":
        (root / required[0]).write_text("changed")
    else:
        (root / common.PACKAGE / "new.py").write_text("new")
    (root / common.QUALIFICATION).write_text(json.dumps(value))
    with pytest.raises(ValueError):
        w.qualification(root)


def test_clean_commit_rejects_staged_difference_even_if_worktree_restored(qualified):
    root, _, required = qualified
    path = root / required[0]
    old = path.read_text()
    path.write_text("staged modification")
    git(root, "add", str(required[0]))
    path.write_text(old)
    with pytest.raises(ValueError, match="index changes"):
        w.clean_commit(root, list(required))


def test_measure_uses_each_retained_scaler_and_keeps_failure_slots(cohort, monkeypatch):
    run(cohort)
    _, requests, slots, terminals, _ = w.collection_inputs(cohort.root, cohort.run)
    inputs = dict(
        scalers={
            p: dict(scaler=dict(center=[i] * 31, scale=[i + 1] * 31))
            for i, p in enumerate(common.PIPELINES)
        }
    )
    monkeypatch.setattr(w, "reference_rows", lambda root: inputs)

    def measurements(path, item, pipelines):
        assert path.read_bytes().startswith(b"\x89PNG")
        return [dict(item, pipeline=p, status="measured", values=[8.0] * 31) for p in pipelines]

    monkeypatch.setattr(w, "measure_path", measurements)
    selected = copy.deepcopy(slots[:2])
    selected[1].update(
        status="refused",
        response_path=None,
        response_sha256=None,
        selected_attempt=None,
        observed=None,
    )
    rows = w._measure(cohort.root, cohort.run, requests[:2], selected, terminals)
    assert len(rows) == 6
    for i, row in enumerate(rows[:3]):
        np.testing.assert_allclose(row["scaled"], (8 - i) / (i + 1))
    assert all(r["values"] is None and r["scaled"] is None for r in rows[3:])


def test_stopped_receipt_passed_unchanged_to_analysis(cohort, monkeypatch):
    from latent_art_bench.painter_clause_successor_v1 import analysis

    receipt = run(cohort, lambda r: httpx.Response(401, content=b"unauthorized"))
    inputs = {"schema": "synthetic"}
    monkeypatch.setattr(w, "reference_rows", lambda root: inputs)

    def stub_analyze(requests, measurements, reference_rows, config, *, collection_receipt):
        assert collection_receipt == receipt
        assert reference_rows is inputs
        return {"primary": [], "withheld": True}

    monkeypatch.setattr(analysis, "analyze", stub_analyze)
    assert w.result_value(cohort.root, [], [], cohort.config, receipt)["withheld"]


def test_namespace_never_accepts_paid_events(cohort):
    append_event(
        cohort.directory / "generation_events.jsonl",
        dict(
            kind="attempt",
            request_id="paid",
            attempt=1,
            route="flux_2_max",
            paid=True,
            reserved_usd=5,
        ),
    )
    with pytest.raises(ValueError, match="paid event"):
        c.namespace_state(cohort.root)


def test_measure_requires_terminal_collection(cohort):
    with pytest.raises(FileNotFoundError):
        w.measure(cohort.root, cohort.run)
    assert not (cohort.root / common.WORKSPACE / cohort.run / "measurement_started.json").exists()


def test_entity_hash_checked_after_valid_gzip_storage(cohort):
    run(cohort)
    row = next(
        r for r in events(cohort.directory / "generation_events.jsonl") if r["kind"] == "terminal"
    )
    path = cohort.root / row["response_path"]
    path.write_bytes(gzip.compress(b"changed"))
    row["stored_response_sha256"] = hash_file(path)
    assert row["response_sha256"] != hashlib.sha256(b"changed").hexdigest()
    with pytest.raises(ValueError, match="entity hash"):
        w.response_bytes(cohort.root, cohort.run, row)


def test_no_collection_receipt_can_be_rebound_to_other_freeze(cohort):
    run(cohort)
    receipt_path = cohort.directory / "collection_receipt.json"
    receipt = read_json(receipt_path)
    receipt["freeze_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="terminal receipt identity"):
        w.collection_inputs(cohort.root, cohort.run)


@pytest.mark.parametrize(
    "code,body",
    [
        (503, b"unknown backend result"),
        (503, b'{"error":{"code":503,"message":"failure"},"data":[]}'),
        (302, b"redirect"),
    ],
)
def test_unrecognized_complete_errors_stop_without_retry(cohort, code, body):
    result = run(cohort, lambda r: httpx.Response(code, content=body))
    assert result["reason"] == "unrecognized_backend_error"
    assert result["retries"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("outputs", []),
        ("posted_attempts", 0),
        ("retry_intents", 8),
        ("slot_counts", {}),
        ("duration_contract_met", False),
        ("status", "running"),
    ],
)
def test_receipt_contract_cannot_omit_evidence_or_change_totals(cohort, field, value):
    run(cohort)
    path = cohort.directory / "collection_receipt.json"
    receipt = read_json(path)
    receipt[field] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        w.collection_inputs(cohort.root, cohort.run)


@pytest.mark.parametrize("failure", ["proxy", "source"])
def test_final_identity_failure_preserves_complete_outputs_but_disqualifies_run(
    cohort, monkeypatch, failure
):
    calls = 0

    def final_proxy(*args):
        nonlocal calls
        calls += 1
        return {"changed": True} if calls == 8 else cohort.freeze["proxy_snapshot"]

    def final_source(*args):
        nonlocal calls
        calls += 1
        if calls == 8:
            raise ValueError("source differs only at final drain")
        return cohort.freeze

    if failure == "proxy":
        monkeypatch.setattr(c.legacy, "proxy_snapshot", final_proxy)
    else:
        monkeypatch.setattr(w, "verify", final_source)
    receipt = run(cohort)
    assert receipt["slot_counts"] == {"image_returned": 12}
    assert receipt["duration_contract_met"] is True
    assert receipt["identity_contract_met"] is False
    assert receipt["status"] == "stopped"
    w.collection_inputs(cohort.root, cohort.run)


def test_receipt_cannot_restore_identity_after_unsupported_delivery(cohort):
    run(cohort, lambda r: httpx.Response(200, content=b"unsupported"))
    path = cohort.directory / "collection_receipt.json"
    receipt = read_json(path)
    receipt["identity_contract_met"] = True
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="identity contract differs"):
        w.collection_inputs(cohort.root, cohort.run)


def test_later_identity_failure_is_recorded_after_an_earlier_storage_halt(cohort, monkeypatch):
    cohort.config["minimum_free_bytes"] = 10**30
    original = c.append_event

    def interrupt_after_first_halt(path, payload):
        result = original(path, payload)
        if payload.get("kind") == "halt" and payload.get("reason") == "storage_reserve":
            raise KeyboardInterrupt("interrupted after retained storage halt")
        return result

    monkeypatch.setattr(c, "append_event", interrupt_after_first_halt)
    with pytest.raises(KeyboardInterrupt):
        run(cohort)
    receipt = read_json(cohort.directory / "collection_receipt.json")
    assert receipt["reason"] == "storage_reserve"
    assert receipt["identity_contract_met"] is False
    operators = events(cohort.directory / "operator_events.jsonl")
    assert [(r["kind"], r.get("reason")) for r in operators] == [
        ("halt", "storage_reserve"),
        ("identity_contract_failure", "interrupted_KeyboardInterrupt"),
        ("final_identity_check", None),
    ]
    assert operators[-1]["source_verified"] and operators[-1]["proxy_verified"]
    w.collection_inputs(cohort.root, cohort.run)


def test_retained_budget_schema_and_machine_tail_are_preserved():
    root = Path(__file__).resolve().parents[2]
    recorded = read_json(root / common.BUDGET_RECEIPT)["budget"]
    result = w.historical_budget(root, dict(historical_accounted_usd=50.7219185))
    assert result == recorded
    assert result["accounted_usd"] == 50.72191850000009


@pytest.mark.parametrize(
    "field,value",
    [
        ("accounted_usd", 50.721919),
        ("pending", ["unresolved"]),
        ("unknown", ["unknown"]),
        ("pending_paid", 1),
        ("new_reserves_usd", 5),
        ("terminal_reserves_usd", 5),
    ],
)
def test_budget_gate_rejects_real_mismatch_and_unresolved_state(tmp_path, field, value):
    budget = dict(
        accounted_usd=50.72191850000009,
        pending=[],
        unknown=[],
        pending_paid=0,
        new_reserves_usd=0,
        terminal_reserves_usd=0,
    )
    budget[field] = value
    publish(tmp_path / common.BUDGET_RECEIPT, dict(budget=budget))
    with pytest.raises(ValueError, match="historical accounting"):
        w.historical_budget(tmp_path, dict(historical_accounted_usd=50.7219185))


def test_three_completed_failures_halt_and_drain_the_last_pair(cohort):
    def handler(request):
        if json.loads(request.content)["prompt"].endswith("generic"):
            time.sleep(0.15)
            return httpx.Response(200, content=cohort.body)
        return httpx.Response(400, json={"error": {"message": "content policy refusal"}})

    result = run(cohort, handler)
    assert result["reason"] == "three_failures_in_latest_eight"
    assert result["attempts"] == 6
    assert result["slot_counts"] == {
        "image_returned": 3,
        "refused": 3,
        "not_attempted_collection_stopped": 6,
    }
    terminal = [
        r for r in events(cohort.directory / "generation_events.jsonl") if r["kind"] == "terminal"
    ]
    assert [r["status"] for r in terminal] == ["refused", "image_returned"] * 3


def test_prepare_then_separately_committed_freeze_and_verify(qualified, monkeypatch):
    root, _, scientific_paths = qualified
    config = dict(maximum_images=2, historical_accounted_usd=50.7219185)
    inventory = [
        dict(
            request_id=f"slot-{i}",
            sequence=i,
            block_id="one",
            block_order=1,
            within_block=i,
            arm=common.ARMS[i],
            experiment="clause_successor",
            route=c.OAUTH_ROUTE,
            payload=dict(model="gpt-image-2"),
        )
        for i in range(2)
    ]
    prior = dict(
        accounted_usd=50.72191850000009,
        pending=[],
        unknown=[],
        pending_paid=0,
        new_reserves_usd=0,
        terminal_reserves_usd=0,
    )
    publish(root / common.BUDGET_RECEIPT, dict(budget=prior))
    paths = sorted([*scientific_paths, common.QUALIFICATION, common.BUDGET_RECEIPT])
    monkeypatch.setattr(common, "configuration", lambda *a: config)
    monkeypatch.setattr(common, "requests", lambda *a, **k: inventory)
    monkeypatch.setattr(w, "source_paths", lambda *a: paths)
    monkeypatch.setattr(w, "predecessor_terminal", lambda *a: {"synthetic_terminal": True})
    monkeypatch.setattr(w.transport, "proxy_snapshot", lambda *a: {"mock": "source-process"})
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "bound qualification and budget lineage")
    result = w.prepare(root, common.RUN_ID, Path("mock-only"))
    assert result["planned"] == 2
    frozen = read_json(root / common.directory(common.RUN_ID) / "freeze.json")
    assert frozen["historical_budget"] == prior
    with pytest.raises(ValueError, match="commit exact prospective input"):
        w.verify(root, common.RUN_ID)
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "commit freeze before collection")
    assert w.verify(root, common.RUN_ID) == frozen
    assert frozen["recorded_git_commit"] != git(root, "rev-parse", "HEAD")
    assert frozen["recorded_git_commit"] != frozen["qualified_source_commit"]
    with pytest.raises(ValueError, match="already exists"):
        w.prepare(root, common.RUN_ID, Path("mock-only"))
    path = root / common.CONFIG
    path.write_text("changed after freeze")
    with pytest.raises(ValueError, match="commit exact prospective input"):
        w.verify(root, common.RUN_ID)


def test_refusal_is_terminal_without_retry_or_replacement(cohort):
    def handler(request):
        if json.loads(request.content)["prompt"] == "b0:cezanne":
            return httpx.Response(400, json={"error": {"code": "moderation_blocked"}})
        return httpx.Response(200, content=cohort.body)

    receipt = run(cohort, handler)
    assert receipt["status"] == "complete"
    assert receipt["identity_contract_met"] is True
    assert receipt["retries"] == 0
    assert receipt["slot_counts"] == {"image_returned": 11, "refused": 1}
    _, _, slots, terminals, _ = w.collection_inputs(cohort.root, cohort.run)
    refused = next(s for s in slots if s["request_id"] == "b0:cezanne")
    assert refused["selected_attempt"] is None and refused["response_path"] is None
    assert [(key, attempt) for key, attempt in terminals if key == "b0:cezanne"] == [
        ("b0:cezanne", 1)
    ]


def test_successor_storage_is_disjoint_from_retained_predecessor(cohort):
    prior = cohort.root / common.PREDECESSOR_DIR / "generation_events.jsonl"
    prior.parent.mkdir(parents=True, exist_ok=True)
    prior.write_bytes(b"retained predecessor bytes\n")
    old_hash = hash_file(prior)
    run(cohort)
    assert hash_file(prior) == old_hash
    for row in events(cohort.directory / "generation_events.jsonl"):
        if row["kind"] == "terminal":
            assert Path(row["response_path"]).is_relative_to(common.WORKSPACE / cohort.run)
            assert not Path(row["response_path"]).is_relative_to(w.predecessor.common.WORKSPACE)


@pytest.fixture
def predecessor_contract(tmp_path, monkeypatch):
    """Unit fixture for the successor gate; predecessor chain validation is separate."""
    request = dict(request_id=common.REFUSED_REQUEST_ID, arm="cezanne", experiment="clause")
    slot = dict(status="refused", selected_attempt=None)
    terminal = dict(
        request_id=common.REFUSED_REQUEST_ID,
        attempt=1,
        status="refused",
        status_code=400,
        complete=True,
        recognized_technical_error=False,
        response_path=str(
            w.predecessor.common.WORKSPACE / common.PREDECESSOR_RUN_ID / "responses/trigger.gz"
        ),
    )
    receipt = dict(
        planned=288,
        status="complete",
        budget=dict(accounted_usd=50.7219185, pending=[], new_reported_usd=0, new_reserves_usd=0),
    )
    freeze = dict(recorded_git_commit="c" * 40)
    terminals = {(common.REFUSED_REQUEST_ID, 1): terminal}
    value = freeze, [request], [slot], terminals, receipt
    publish(tmp_path / common.PREDECESSOR_DIR / "freeze.json", freeze)
    publish(tmp_path / common.PREDECESSOR_DIR / "collection_receipt.json", receipt)
    monkeypatch.setattr(w.predecessor, "collection_inputs", lambda *a: value)

    def write_body(body):
        path = tmp_path / terminal["response_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(body, mtime=0))
        terminal.update(
            stored_response_sha256=hash_file(path),
            response_sha256=hashlib.sha256(body).hexdigest(),
        )

    write_body(b'{"error":{"code":"moderation_blocked"}}')
    return SimpleNamespace(
        root=tmp_path, value=value, write_body=write_body, terminal=terminal, receipt=receipt
    )


def test_predecessor_gate_retains_exact_missingness_trigger_without_numerical_reads(
    predecessor_contract,
):
    prior = predecessor_contract
    # These files exist only as tripwires: gate input parsing would fail if read.
    (prior.root / common.PREDECESSOR_DIR / "measurements.jsonl").write_text("not JSON")
    result = w.predecessor_terminal(prior.root)
    assert result["trigger_request_id"] == common.REFUSED_REQUEST_ID
    assert result["trigger_response_sha256"] == prior.terminal["response_sha256"]
    assert result["cezanne_primary_complete"] is False
    assert result["numerical_outcomes_accessed"] is False


@pytest.mark.parametrize(
    "mutation",
    ["running", "pending", "paid", "missing_slot", "image", "retry", "technical", "mixed", "other"],
)
def test_predecessor_gate_rejects_unclosed_or_changed_trigger(predecessor_contract, mutation):
    prior = predecessor_contract
    if mutation == "running":
        prior.receipt["status"] = "running"
    elif mutation == "pending":
        prior.receipt["budget"]["pending"] = ["unresolved"]
    elif mutation == "paid":
        prior.receipt["budget"]["new_reported_usd"] = 1
    elif mutation == "missing_slot":
        prior.value[1][0]["request_id"] = "other"
    elif mutation == "image":
        prior.value[2][0].update(status="image_returned", selected_attempt=1)
    elif mutation == "retry":
        prior.value[3][common.REFUSED_REQUEST_ID, 2] = dict(prior.terminal, attempt=2)
    elif mutation == "technical":
        prior.terminal["recognized_technical_error"] = True
    elif mutation == "mixed":
        prior.write_body(b'{"error":{"code":"moderation_blocked"},"data":[]}')
    else:
        prior.write_body(b'{"error":{"code":"different"}}')
    with pytest.raises(ValueError):
        w.predecessor_terminal(prior.root)


def test_prepare_cannot_create_new_evidence_before_predecessor_terminal(qualified, monkeypatch):
    root, _, _ = qualified
    monkeypatch.setattr(common, "configuration", lambda *a: {})

    def absent(*args):
        raise FileNotFoundError("predecessor collection receipt is absent")

    monkeypatch.setattr(w.predecessor, "collection_inputs", absent)
    monkeypatch.setattr(w.transport, "proxy_snapshot", lambda *a: pytest.fail("gate bypassed"))
    with pytest.raises(FileNotFoundError, match="predecessor"):
        w.prepare(root, common.RUN_ID, Path("unused"))
    assert not (root / common.directory(common.RUN_ID)).exists()
    assert not (root / common.WORKSPACE / common.RUN_ID).exists()


def synthetic_inputs():
    """Artificial references only; no predecessor measurement outcomes."""
    rng = np.random.default_rng(30911)
    return dict(
        schema="painter-clause-successor-inputs/1",
        origin=dict(path="studies/painter_clause_validation_v1/inputs.json", sha256="a" * 64),
        targets={common.PAINTER_ID: dict(built=11 / 32, land=18 / 32, water=3 / 32)},
        reference={
            p: {
                common.PAINTER_ID: dict(
                    ids=[f"ref-{i:02}" for i in range(32)],
                    values=rng.normal(size=(32, 31)).tolist(),
                )
            }
            for p in common.PIPELINES
        },
        scalers={
            p: dict(scaler=dict(center=[0.0] * 31, scale=[1.0] * 31)) for p in common.PIPELINES
        },
    )


@pytest.mark.parametrize("missing_arm", [None, "generic", "cezanne"])
def test_full_96_slot_artificial_workflow_and_real_analysis(tmp_path, monkeypatch, missing_arm):
    root = Path(__file__).resolve().parents[2]
    requests, config = common.requests(root), common.configuration(root)
    assert len(requests) == 96
    config = dict(config, minimum_start_interval_seconds=0, minimum_free_bytes=0)
    freeze = dict(config=config, proxy_snapshot={"synthetic": True})
    directory = tmp_path / common.directory(common.RUN_ID)
    publish(directory / "freeze.json", freeze)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    publish(tmp_path / common.INPUTS, synthetic_inputs())
    monkeypatch.setattr(common, "requests", lambda *a, **k: requests)
    monkeypatch.setattr(w, "verify", lambda *a: freeze)
    monkeypatch.setattr(c.legacy, "proxy_snapshot", lambda *a: freeze["proxy_snapshot"])
    body, calls = image_body(), []
    missing = next((r for r in requests if r["arm"] == missing_arm), None)

    def handler(request):
        assert request.method == "POST" and str(request.url) == c.legacy.OAUTH_URL
        assert "authorization" not in request.headers
        value = json.loads(request.content)
        calls.append(value)
        if missing and value == missing["payload"]:
            return httpx.Response(400, json={"error": {"code": "moderation_blocked"}})
        return httpx.Response(200, content=body)

    receipt = c.collect(
        tmp_path, common.RUN_ID, Path("synthetic"), transport=httpx.MockTransport(handler)
    )
    # Repetitions have identical prompt bodies, so a selected prompt refusal here
    # deliberately withholds both repetitions for that arm/scene without retry.
    refused = 2 if missing_arm else 0
    expected = {"image_returned": 96 - refused}
    if refused:
        expected["refused"] = refused
    assert receipt["slot_counts"] == expected
    assert receipt["planned"] == receipt["attempts"] == 96
    assert receipt["retries"] == 0 and receipt["identity_contract_met"] is True
    assert Counter(json.dumps(r, sort_keys=True) for r in calls) == Counter(
        json.dumps(r["payload"], sort_keys=True) for r in requests
    )

    def fake_measure(path, item, pipelines):
        with Image.open(path) as image:
            assert image.size == (512, 512)
        rng = np.random.default_rng(941 + item["sequence"])
        return [
            dict(item, pipeline=p, status="measured", values=rng.normal(size=31).tolist())
            for p in pipelines
        ]

    monkeypatch.setattr(w, "measure_path", fake_measure)
    result = w.measure(tmp_path, common.RUN_ID)
    assert len(result["primary"]) == 1
    endpoint = result["primary"][0]
    if missing_arm:
        assert endpoint["status"] != "available" and endpoint["raw_p"] is None
    else:
        assert endpoint["status"] == "available" and endpoint["pairs"] == 48
    assert len(read_jsonl(directory / "measurements.jsonl")) == 288
    assert w.verify_responses(tmp_path, common.RUN_ID)["checked"] == 96
    assert w.check(tmp_path, common.RUN_ID)["status"] == "numbers_replayed"
    assert w.check(tmp_path, common.RUN_ID, pixels=True)["status"] == "pixels_and_numbers_replayed"
    # The check must reject incomplete or duplicate binding inventories even
    # when all underlying rows and replayed report still agree numerically.
    path = directory / "measurement_receipt.json"
    original_receipt = read_json(path)
    for outputs in (
        [],
        original_receipt["outputs"][1:],
        [original_receipt["outputs"][0]] * 4,
        original_receipt["outputs"] + [original_receipt["outputs"][0]],
    ):
        path.write_text(json.dumps(dict(original_receipt, outputs=outputs)))
        with pytest.raises(ValueError, match="measurement receipt output inventory"):
            w.check(tmp_path, common.RUN_ID)
    path.write_text(json.dumps(original_receipt))
    with pytest.raises(FileExistsError):
        w.measure(tmp_path, common.RUN_ID)


def test_predecessor_gate_uses_real_terminal_hash_chains_with_synthetic_responses(
    tmp_path, monkeypatch
):
    from latent_art_bench.painter_clause_validation_v1 import collection as old_collection

    old_common = w.predecessor.common
    repo = Path(__file__).resolve().parents[2]
    requests = old_common.requests(repo)
    config = dict(
        old_common.configuration(repo), minimum_start_interval_seconds=0, minimum_free_bytes=0
    )
    freeze = dict(config=config, proxy_snapshot={"synthetic": True}, recorded_git_commit="c" * 40)
    directory = tmp_path / common.PREDECESSOR_DIR
    publish(directory / "freeze.json", freeze)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    monkeypatch.setattr(old_common, "requests", lambda *a, **k: requests)
    monkeypatch.setattr(w.predecessor, "verify", lambda *a: freeze)
    monkeypatch.setattr(
        old_collection.legacy, "proxy_snapshot", lambda *a: freeze["proxy_snapshot"]
    )
    original_send = old_collection._send
    image = image_body()

    def synthetic_send(root, run_id, request, attempt, gate, **kwargs):
        def handler(_):
            if request["request_id"] == common.REFUSED_REQUEST_ID:
                return httpx.Response(400, json={"error": {"code": "moderation_blocked"}})
            return httpx.Response(200, content=image)

        return original_send(
            root, run_id, request, attempt, gate, transport=httpx.MockTransport(handler)
        )

    monkeypatch.setattr(old_collection, "_send", synthetic_send)
    receipt = old_collection.collect(
        tmp_path,
        common.PREDECESSOR_RUN_ID,
        Path("synthetic"),
        transport=httpx.MockTransport(lambda r: pytest.fail("unbound transport used")),
    )
    assert receipt["slot_counts"] == {"image_returned": 287, "refused": 1}
    before = {
        p: hash_file(directory / p)
        for p in (
            "freeze.json",
            "planned_requests.jsonl",
            "collection_receipt.json",
            "generation_events.jsonl",
            "slot_outcomes.jsonl",
            "operator_events.jsonl",
        )
    }
    result = w.predecessor_terminal(tmp_path)
    assert result["cezanne_primary_complete"] is False
    assert result["collection_receipt_sha256"] == before["collection_receipt.json"]
    assert before == {p: hash_file(directory / p) for p in before}
    with (directory / "operator_events.jsonl").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="bound input changed"):
        w.predecessor_terminal(tmp_path)


@pytest.mark.parametrize("mutation", ["vector", "scaler", "origin", "extra", "numeric_type"])
def test_input_lineage_rejects_shape_valid_source_projection_tampering(qualified, mutation):
    root, _, _ = qualified
    value = read_json(root / common.INPUTS)
    assert w.validate_input_lineage(root) == value["origin"]
    if mutation == "vector":
        value["reference"]["primary512"][common.PAINTER_ID]["values"][0][0] += 0.001
    elif mutation == "scaler":
        value["scalers"]["primary512"]["scaler"]["scale"][0] = 1.001
    elif mutation == "origin":
        value["origin"]["sha256"] = "0" * 64
    elif mutation == "extra":
        value["scalers"]["primary512"]["unexpected_metadata"] = "new"
    else:
        value["scalers"]["primary512"]["scaler"]["scale"][0] = 1
    (root / common.INPUTS).write_text(json.dumps(value))
    with pytest.raises(ValueError, match="exact frozen predecessor projection"):
        w.validate_input_lineage(root)


def test_attempt_intent_limit_halts_before_another_admission(cohort):
    cohort.config["maximum_attempts"] = 3
    receipt = run(cohort)
    assert receipt["reason"] == "attempt_limit"
    assert receipt["identity_contract_met"] is True
    assert receipt["attempts"] == receipt["posted_attempts"] == 3
    assert receipt["slot_counts"] == {"image_returned": 3, "not_attempted_collection_stopped": 9}
    w.collection_inputs(cohort.root, cohort.run)


@pytest.mark.parametrize(
    "field,value",
    [
        ("new_reported_usd", 1),
        ("new_reserves_usd", 1),
        ("attempts", 0),
        ("subscription_monetary_value", 1),
    ],
)
def test_terminal_budget_must_equal_the_zero_paid_ledger_state(cohort, field, value):
    run(cohort)
    path = cohort.directory / "collection_receipt.json"
    receipt = read_json(path)
    receipt["budget"][field] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="terminal receipt identity, freeze or accounting"):
        w.collection_inputs(cohort.root, cohort.run)
