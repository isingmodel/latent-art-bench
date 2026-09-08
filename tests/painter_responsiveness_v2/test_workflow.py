"""Offline end-to-end allocation, measurement and replay integrity tests."""

import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import events, publish
from latent_art_bench.painter_responsiveness_v2 import collection as c
from latent_art_bench.painter_responsiveness_v2 import common
from latent_art_bench.painter_responsiveness_v2 import workflow as w

from .test_collection import RUN, image_body, setup


def closed(tmp_path, monkeypatch, *, retry=False):
    directory, requests, clock = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(w, "source_paths", lambda _: sorted(c.required_sources()))
    monkeypatch.setattr(w, "committed", lambda *_: "a" * 40)
    calls = []

    def handler(_):
        calls.append(None)
        if retry and len(calls) == 1:
            return httpx.Response(503, json={"error": "temporary"})
        if len(calls) == 1 + int(retry):
            return httpx.Response(200, content=image_body(dimensions=(640, 512), fmt="JPEG"))
        return httpx.Response(401, json={"error": "synthetic stop"})

    c.collect(
        tmp_path,
        RUN,
        tmp_path / "mock-proxy",
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
    )
    return directory, requests


def measurement_dependencies(tmp_path, monkeypatch):
    config = common.configuration(tmp_path)
    original = Path(__file__).resolve().parents[2] / w.retained.MAIN / "scalers.json"
    publish(tmp_path / w.retained.MAIN / "scalers.json", read_json(original))
    measured = []

    def extractor(path, item, pipelines):
        assert path.is_file()
        measured.append(item["request_id"])
        values = [1.0] * 31
        values[2] = config["primary_chroma_center"] + config["primary_chroma_scale"]
        return [dict(item, pipeline=p, status="measured", values=values) for p in pipelines]

    monkeypatch.setattr(w, "measure_path", extractor)
    references = [
        dict(
            image_id=f"synthetic:{painter}:{content}",
            pipeline=pipeline,
            painter_id=painter,
            content_class=content,
            status="measured",
            values=[float(i + 1)] * 31,
        )
        for painter in ("claude_monet", "paul_cezanne")
        for i, content in enumerate(("built", "land", "water"))
        for pipeline in w.PIPELINES
    ]
    monkeypatch.setattr(w.retained, "load", lambda _: {"reference": references})

    def renderer(value, output):
        output.mkdir(parents=True, exist_ok=False)
        (output / "REPORT.md").write_text(json.dumps(value, sort_keys=True) + "\n")
        return ["REPORT.md"]

    monkeypatch.setattr(w.report, "render_experiment", renderer)
    return measured


def test_missing_grid_measurement_and_exact_vector_report_replay(tmp_path, monkeypatch):
    directory, _ = closed(tmp_path, monkeypatch, retry=True)
    measured = measurement_dependencies(tmp_path, monkeypatch)
    result = w.measure(tmp_path, RUN)
    assert result["measurements"] == 576 and len(measured) == 1
    rows = read_jsonl(directory / "generated_features.jsonl")
    assert sum(row["status"] == "measured" for row in rows) == 3
    assert len({row["request_id"] for row in rows}) == 192
    assert rows[0]["chroma_primary_iqr"] == pytest.approx(1)
    analysis = read_json(directory / "analysis.json")
    assert analysis["primary"]["primary"] is None
    transport = analysis["collection"]
    assert len(transport["per_attempt_transport"]) == 3
    assert transport["transport_summary"]["geometry_counts"] == {"640x512": 1}
    assert transport["transport_summary"]["format_counts"] == {"JPEG": 1}
    assert transport["transport_summary"]["reported_quality_counts"] == {"low": 1}
    assert w.measure(tmp_path, RUN, check=True)["report_files"] == 1
    assert len(measured) == 1  # Replay consumes retained vectors, never regenerates features.
    receipt = read_json(directory / "analysis_receipt.json")
    raw_paths = [r["path"] for r in receipt["inputs"] if r["path"].endswith(".json.gz")]
    assert len(raw_paths) == 3  # Includes both failed bodies, not just the selected attempt.
    with pytest.raises(ValueError, match="terminal or interrupted"):
        w.measure(tmp_path, RUN)


@pytest.mark.parametrize("target", ["features", "report", "failed_response"])
def test_replay_detects_changed_vectors_reports_and_failed_evidence(tmp_path, monkeypatch, target):
    directory, _ = closed(tmp_path, monkeypatch)
    measurement_dependencies(tmp_path, monkeypatch)
    w.measure(tmp_path, RUN)
    if target == "features":
        path = directory / "generated_features.jsonl"
    elif target == "report":
        path = tmp_path / common.REPORTS / RUN / "experiment" / "REPORT.md"
    else:
        row = next(
            r
            for r in events(directory / "generation_events.jsonl")
            if r["kind"] == "terminal" and r["status"] == "http_error"
        )
        path = tmp_path / row["response_path"]
    with path.open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ValueError):
        w.measure(tmp_path, RUN, check=True)


@pytest.mark.parametrize("case", ["missing", "duplicate", "allocation"])
def test_analysis_rejects_missing_duplicate_or_falsely_measured_allocations(
    tmp_path, monkeypatch, case
):
    directory, requests = closed(tmp_path, monkeypatch)
    measurement_dependencies(tmp_path, monkeypatch)
    slots = read_jsonl(directory / "slot_outcomes.jsonl")
    rows = w._measure(tmp_path, RUN, requests, slots, common.configuration(tmp_path))
    if case == "missing":
        rows.pop()
    elif case == "duplicate":
        rows[-1] = rows[0]
    else:
        rows[3]["status"] = "measured"
    with pytest.raises(ValueError):
        w.result_value(tmp_path, RUN, rows)


def test_extractor_cannot_change_treatment_identity(tmp_path, monkeypatch):
    _, _ = closed(tmp_path, monkeypatch)
    measurement_dependencies(tmp_path, monkeypatch)

    def wrong_identity(_, item, pipelines):
        return [dict(item, request_id="wrong", pipeline=p, status="failed") for p in pipelines]

    monkeypatch.setattr(w, "measure_path", wrong_identity)
    with pytest.raises(ValueError, match="treatment identity"):
        w.measure(tmp_path, RUN)


@pytest.mark.parametrize(
    "field,value",
    [
        ("technical_retries_dispatched", 1),
        ("unresolved_intents", ["pending"]),
        ("incremental_api_spend_usd", 1),
        ("status", "completed"),
    ],
)
def test_terminal_receipt_accounting_is_recomputed(tmp_path, monkeypatch, field, value):
    directory, _ = closed(tmp_path, monkeypatch)
    path = directory / "collection_receipt.json"
    receipt = read_json(path)
    receipt[field] = value
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError):
        w.collection_inputs(tmp_path, RUN)


@pytest.mark.parametrize("case", ["runtime", "missing_runtime", "missing_source"])
def test_offline_verifier_requires_full_runtime_and_source_closure(tmp_path, monkeypatch, case):
    directory, _, _ = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(w, "source_paths", lambda _: sorted(c.required_sources()))
    monkeypatch.setattr(w, "committed", lambda *_: "a" * 40)
    path = directory / "freeze.json"
    freeze = read_json(path)
    if case == "runtime":
        freeze["environment"]["numpy"] = "wrong"
    elif case == "missing_runtime":
        freeze["environment"].pop("numpy")
    else:
        freeze["inputs"].pop()
    path.write_text(json.dumps(freeze))
    with pytest.raises(ValueError):
        w.verify(tmp_path, RUN)


def test_selected_image_metadata_is_verified_before_measurement(tmp_path, monkeypatch):
    directory, _ = closed(tmp_path, monkeypatch)
    slot = read_jsonl(directory / "slot_outcomes.jsonl")[0]
    slot["observed"]["reported"]["quality"] = "high"
    with pytest.raises(ValueError, match="embedded image"):
        w.selected_bytes(tmp_path, RUN, slot)


def test_retry_must_follow_a_recorded_eligible_error(tmp_path, monkeypatch):
    directory, _ = closed(tmp_path, monkeypatch, retry=True)
    ledger = directory / "generation_events.jsonl"
    original = events(ledger)
    changed = [dict(row) for row in original]
    predecessor = next(row for row in changed if row["kind"] == "terminal")
    predecessor["known_error_envelope"] = False
    monkeypatch.setattr(w, "events", lambda _: changed)
    # Keep the original on-disk bytes: this targets semantic validation after hash-chain reading.
    assert (
        hash_file(ledger)
        == read_json(directory / "collection_receipt.json")["generation_events_sha256"]
    )
    with pytest.raises(ValueError, match="eligible completed predecessor"):
        w.collection_inputs(tmp_path, RUN)
