"""Offline publication contracts with opaque synthetic bytes and mocked extraction.

No test opens an image, invokes the feature extractor or calls a provider. Human
qualification and Git admission are separate tested boundaries and are mocked.
"""

import base64
import copy
import gzip
import hashlib
import importlib.metadata
import json
import platform
from collections import Counter
from pathlib import Path

import pytest

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_responsiveness_v1 import (
    collection,
    common,
    design,
    generation_prepare,
    workflow,
)
from latent_art_bench.painter_responsiveness_v1 import measurement as m

ROOT = Path(__file__).resolve().parents[1]
RUN, SOURCE = "prv1-measurement-mock", "prv1-diagnostic-mock"


def rewrite(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def observed(body):
    raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"])
    return dict(image_sha256=hashlib.sha256(raw).hexdigest(), image_bytes=len(raw),
                width=512, height=512, format="PNG", mode="RGB", minimum_512=True,
                square_1024=False, reported={})


def fixture(tmp_path, monkeypatch, *, statuses=None, default="image_returned", failures=(),
            margin=0.75):
    config = common.configuration(ROOT)
    paths = m._required_sources() | {
        Path("src/latent_art_bench/painter_distribution_study_v1/discovery.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
    }
    for path in paths - {common.CONFIG, m.SCALERS}:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Synthetic frozen source identity.\n")
    publish(tmp_path / common.CONFIG, config)
    scales = dict(primary512=2, resolution256=4, jpeg90_512=0.5)
    publish(tmp_path / m.SCALERS, {
        p: {"scaler": {"center": [1.0] * 31, "scale": [scales[p]] * 31}}
        for p in m.PIPELINES})
    source_path = common.directory(SOURCE) / "freeze.json"
    publish(tmp_path / source_path, dict(
        run_id=SOURCE, recorded_git_commit="a" * 40,
        inputs=bindings(tmp_path, paths), config=config,
        environment=dict(python=platform.python_version(), **{
            name: importlib.metadata.version(name) for name in
            ("numpy", "scipy", "Pillow", "matplotlib", "httpx")})))
    requests = common.requests_from_schedule(design.make_schedule(
        [r["template_id"] for r in config["templates"]], seed=config["seed"]), config)
    directory = tmp_path / common.directory(RUN)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    publish(directory / "generation_freeze.json", dict(
        run_id=RUN, diagnostic_run_id=SOURCE, recorded_git_commit="a" * 40,
        inputs=bindings(tmp_path, paths | {source_path}), config=config,
        requests_sha256=hash_file(directory / "planned_requests.jsonl"),
        source_freeze_sha256=hash_file(tmp_path / source_path), budget_baseline_usd=45.6819185,
        gates=dict(status="ready", checks=dict.fromkeys(collection.GATE_KEYS, True), missing=[]),
        meaningful_margin_primary_iqr=margin,
        precision=dict(margin_status="validated", decision="proceed",
                       meaningful_margin_primary_iqr=margin)))
    monkeypatch.setattr(collection, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(workflow, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(generation_prepare, "verify_qualification", lambda *_: {})
    ledger = directory / "generation_events.jsonl"
    for request in requests:
        status = (statuses or {}).get(request["sequence"], default)
        if status == "never_started":
            continue
        append_event(ledger, dict(
            kind="attempt", request_id=request["request_id"], attempt=1,
            slot_sequence=request["sequence"], route=request["route"],
            request_sha256=digest(request), payload_sha256=digest(request["payload"]),
            reservation_usd=5.0))
        fields = dict(response_path=None, response_sha256=None, stored_response_sha256=None,
                      observed=None)
        if status == "image_returned":
            # These are deliberately not valid image bytes: accidental decoding fails the test.
            raw = ("synthetic opaque image " + request["request_id"]).encode()
            body = json.dumps(dict(data=[dict(b64_json=base64.b64encode(raw).decode())])).encode()
            path = common.WORKSPACE / RUN / "responses" / f"{request['sequence']:04d}-a1.json.gz"
            target = tmp_path / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(gzip.compress(body, mtime=0))
            fields = dict(response_path=str(path), response_sha256=hashlib.sha256(body).hexdigest(),
                          stored_response_sha256=hash_file(target), observed=observed(body))
        append_event(ledger, dict(
            kind="terminal", request_id=request["request_id"], attempt=1,
            slot_sequence=request["sequence"], route=request["route"], status=status,
            complete=True, post_started=True, cost_usd=0.01, **fields))
    entries = events(ledger)
    intents = [r for r in entries if r["kind"] == "attempt"]
    terminals = [r for r in entries if r["kind"] == "terminal"]
    slots = collection._slot_outcomes(requests, terminals, intents)
    publish(directory / "slot_outcomes.jsonl", slots, lines=True)
    publish(directory / "collection_receipt.json", dict(
        schema="painter-responsiveness-collection/1", run_id=RUN,
        recorded_git_commit="a" * 40, terminal=True,
        generation_freeze_sha256=hash_file(directory / "generation_freeze.json"),
        requests_sha256=hash_file(directory / "planned_requests.jsonl"),
        status="stopped" if default == "never_started" else "completed",
        stop_reason="synthetic stop" if default == "never_started" else None,
        total_planned=192, status_counts=dict(Counter(r["status"] for r in slots)),
        attempt_intents=len(intents), terminal_attempts=len(terminals),
        technical_retries_dispatched=0, generation_events_sha256=hash_file(ledger)
        if ledger.exists() else None,
        slot_outcomes_sha256=hash_file(directory / "slot_outcomes.jsonl"),
        new_feature_measurements=0))
    calls = []

    def extract(path, item, pipelines):
        calls.append(item["request_id"])
        assert path.read_bytes() == ("synthetic opaque image " + item["request_id"]).encode()
        output = []
        for pipeline in pipelines:
            row = dict(kind="measurement", **item, pipeline=pipeline)
            if (item["sequence"], pipeline) in failures:
                output.append(dict(row, status="failed", error_type="SyntheticExtractionFailure"))
                continue
            arm = design.ARMS.index(item["arm"])
            polarity = design.POLARITIES.index(item["polarity"])
            slope = [8, 6, 2, 4][arm]
            processing = dict(primary512=0, resolution256=0.25, jpeg90_512=-0.1)[pipeline]
            values = [2.0 + i for i in range(31)]
            values[2] = (40 + arm + polarity * slope + processing
                         + 0.01 * (item["repetition"] - 1.5) * (arm + 1) * (polarity + 1))
            output.append(dict(row, status="measured", values=values,
                               feature_sha256=digest(values), normalization=dict(synthetic=True)))
        return output

    monkeypatch.setattr(m, "measure_path", extract)
    monkeypatch.setattr(m, "inspect_response", observed)
    return directory, requests, slots, calls


def test_complete_publication_uses_frozen_scalers_shared_control_and_margin(tmp_path, monkeypatch):
    directory, requests, _, calls = fixture(tmp_path, monkeypatch)
    result = m.measure(tmp_path, RUN)
    assert result["feature_rows"] == 576 and len(calls) == 192
    rows = read_jsonl(directory / "generated_features.jsonl")
    assert [r["request_id"] for r in rows[::3]] == [r["request_id"] for r in requests]
    assert all(r["status"] == "measured" for r in rows)
    for row in rows:
        scale = dict(primary512=2, resolution256=4, jpeg90_512=0.5)[row["pipeline"]]
        assert row["scaled"][2] == (row["values"][2] - 1) / scale
        assert row["chroma_primary_iqr"] == (row["values"][2] - 1) / 2
    output = read_json(directory / "factorial_results.json")
    primary = output["factorial"]
    assert primary["status"] == "complete_grid_approximate_inference"
    assert primary["manipulation_margin"] == 0.0
    assert output["meaningful_margin_primary_iqr"] == 0.75
    assert [r["estimate"] for r in primary["primary"]] == pytest.approx([-2, -1])
    assert all(r["status"] == "interval_beyond_negative_margin"
               for r in output["meaningful_interactions"])
    assert primary["primary_covariance"][0][1] > 0
    assert len(output["processing_blocks"]) == 72
    assert all(r["measured"] == 8 for r in output["processing_blocks"])
    receipt = read_json(directory / "measurement_receipt.json")
    verify_bindings(tmp_path, receipt["inputs"])
    verify_bindings(tmp_path, receipt["reports"])
    assert receipt["allocated_slots"] == 192 and receipt["new_generation_calls"] == 0
    assert receipt["generated_features_sha256"] == hash_file(directory / "generated_features.jsonl")
    assert "pending" in (tmp_path / result["report"]).read_text()
    with pytest.raises(ValueError, match="terminal or interrupted"):
        m.build(tmp_path, RUN)
    assert len(calls) == 192


def test_interaction_precision_margin_is_not_the_response_threshold(tmp_path, monkeypatch):
    directory, _, _, _ = fixture(tmp_path, monkeypatch, margin=10.0)
    m.measure(tmp_path, RUN)
    output = read_json(directory / "factorial_results.json")
    assert all(r["estimate"] < output["meaningful_margin_primary_iqr"]
               for r in output["factorial"]["responses"])
    assert all(r["status"] == "nominal_interval_above_margin" and r["margin"] == 0
               for r in output["factorial"]["manipulation_checks"])
    assert all(r["status"] == "interval_excludes_negative_margin"
               for r in output["meaningful_interactions"])


def test_meaningful_interaction_classification_retains_boundary_and_unavailable_cases():
    intervals = [[-2, -1.1], [-1.0, 0], [-2, -1], [-1.5, -0.5], None]
    result = m._meaningful_interactions(dict(primary=[
        dict(contrast=f"case{i}", estimate=-1.0, family_interval=value)
        for i, value in enumerate(intervals)]), 1.0)
    assert [r["status"] for r in result] == [
        "interval_beyond_negative_margin", "unresolved_at_negative_margin",
        "unresolved_at_negative_margin", "unresolved_at_negative_margin", "unavailable"]
    assert all("p_value" not in r for r in result)


def test_stopped_grid_preserves_all_unstarted_and_refused_slots(tmp_path, monkeypatch):
    directory, requests, _, calls = fixture(
        tmp_path, monkeypatch, statuses={0: "image_returned", 1: "refused"},
        default="never_started")
    result = m.measure(tmp_path, RUN)
    assert len(calls) == 1
    rows = read_jsonl(directory / "generated_features.jsonl")
    assert len(rows) == 576
    assert Counter(r["status"] for r in rows) == dict(measured=3, refused=3, never_started=570)
    assert {r["request_id"] for r in rows} == {r["request_id"] for r in requests}
    assert all(r["values"] is None and r["scaled"] is None
               for r in rows if r["status"] != "measured")
    output = read_json(directory / "factorial_results.json")
    assert output["factorial"]["primary"] is None
    assert result["primary_inference_status"] == "primary_withheld_unavailable_planned_values"
    assert sum(r["allocated"] for r in output["factorial"]["availability"]) == 192
    assert all(r["monet_minus_generic"] is None for r in output["processing_blocks"])


@pytest.mark.parametrize("pipeline,withheld", [("primary512", True), ("resolution256", False)])
def test_extraction_failures_remain_pipeline_specific_without_complete_case_inference(
    tmp_path, monkeypatch, pipeline, withheld
):
    directory, _, _, calls = fixture(tmp_path, monkeypatch, failures={(7, pipeline)})
    result = m.measure(tmp_path, RUN)
    assert len(calls) == 192
    rows = read_jsonl(directory / "generated_features.jsonl")
    failures = [r for r in rows if r["status"] == "failed"]
    assert len(failures) == 1 and failures[0]["pipeline"] == pipeline
    assert failures[0]["values"] is None and failures[0]["collection_status"] == "image_returned"
    assert (result["primary_inference_status"] == "primary_withheld_unavailable_planned_values"
            ) is withheld
    result = read_json(directory / "factorial_results.json")
    if withheld:
        assert "p_holm" not in json.dumps(result["factorial"])
        assert sum(result["factorial"]["complete_blocks_by_template"].values()) == 23
    else:
        assert sum(r["monet_minus_generic"] is None for r in result["processing_blocks"]) == 1


@pytest.mark.parametrize("mutation", ["gate", "source", "runtime", "margin", "nonterminal"])
def test_missing_or_changed_admission_evidence_blocks_before_image_access(
    tmp_path, monkeypatch, mutation
):
    directory, _, _, calls = fixture(tmp_path, monkeypatch, default="never_started")
    if mutation == "source":
        (tmp_path / common.PACKAGE / "measurement.py").write_text("# Changed frozen source\n")
    elif mutation == "runtime":
        monkeypatch.setattr(workflow.platform, "python_version", lambda: "not-the-frozen-runtime")
    elif mutation in ("gate", "margin"):
        path = directory / "generation_freeze.json"
        freeze = read_json(path)
        if mutation == "gate":
            freeze["gates"]["checks"]["human_assessment_feasible"] = False
        else:
            freeze["meaningful_margin_primary_iqr"] = 0.2
        rewrite(path, freeze)
    else:
        path = directory / "collection_receipt.json"
        receipt = read_json(path)
        receipt["terminal"] = False
        rewrite(path, receipt)
    monkeypatch.setattr(m, "_selected_bytes", lambda *_: pytest.fail("must not access image bytes"))
    with pytest.raises(ValueError):
        m.measure(tmp_path, RUN)
    assert calls == []
    assert not (directory / "generated_features.jsonl").exists()


def test_slot_omission_cannot_be_hidden_by_updating_receipt(tmp_path, monkeypatch):
    directory, _, slots, calls = fixture(tmp_path, monkeypatch, default="never_started")
    publish(directory / "altered_slots.jsonl", slots[:-1], lines=True)
    altered = (directory / "altered_slots.jsonl").read_bytes()
    (directory / "slot_outcomes.jsonl").write_bytes(altered)
    receipt = read_json(directory / "collection_receipt.json")
    receipt["slot_outcomes_sha256"] = hash_file(directory / "slot_outcomes.jsonl")
    rewrite(directory / "collection_receipt.json", receipt)
    with pytest.raises(ValueError, match="complete terminal ledger"):
        m.measure(tmp_path, RUN)
    assert calls == []


@pytest.mark.parametrize("field", ["stored_response_sha256", "response_sha256", "image_sha256",
                                  "response_path"])
def test_selected_response_requires_all_three_hashes_and_confined_slot_path(
    tmp_path, monkeypatch, field
):
    _, _, slots, _ = fixture(tmp_path, monkeypatch, statuses={0: "image_returned"},
                             default="never_started")
    slot = copy.deepcopy(slots[0])
    if field == "image_sha256":
        slot["observed"][field] = "0" * 64
    else:
        slot[field] = "../another-run.json.gz" if field == "response_path" else "0" * 64
    with pytest.raises(ValueError):
        m._selected_bytes(tmp_path, RUN, slot)


def test_late_selected_corruption_is_found_before_any_feature_extraction(tmp_path, monkeypatch):
    directory, _, slots, calls = fixture(
        tmp_path, monkeypatch, statuses={0: "image_returned", 191: "image_returned"},
        default="never_started")
    path = tmp_path / slots[-1]["response_path"]
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="compressed response changed"):
        m.measure(tmp_path, RUN)
    assert calls == []
    assert not (directory / "generated_features.jsonl").exists()
    assert not (tmp_path / common.WORKSPACE / RUN / "measurement_started.json").exists()


def test_no_selected_images_still_publishes_the_full_allocated_denominator(tmp_path, monkeypatch):
    directory, _, _, calls = fixture(tmp_path, monkeypatch, default="never_started")
    m.measure(tmp_path, RUN)
    result = read_json(directory / "factorial_results.json")["factorial"]
    assert calls == [] and result["primary"] is None
    assert all(r["measured"] == 0 and r["allocated"] == 24 for r in result["availability"])
    assert result["complete_block_descriptive"]["kappa_equal_template"] is None
