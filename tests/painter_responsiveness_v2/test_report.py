"""Reproducible synthetic reports, not observed research outcomes."""

import csv
import hashlib
import json
from copy import deepcopy

import pytest

from latent_art_bench.painter_responsiveness_v2 import analysis, diagnostics, report

from .test_diagnostics import bundle
from .test_prv2_analysis import study as source_study


@pytest.fixture
def study():
    return source_study.__wrapped__()


def _hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob("*") if p.is_file()}


def _csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def _experiment(study_data, missing=False):
    requests, rows, references, config = deepcopy(study_data)
    if missing:
        rows.pop(0)
    value = analysis.analyze(requests, rows, references, config)
    value["collection"] = dict(
        status="stopped" if missing else "completed", stop_reason="synthetic failure" if missing
        else None, attempts=192, paid_requests=0, incremental_api_spend_usd=0,
        slots=[dict(request_id=r["request_id"], status="image_returned") for r in requests],
        per_attempt_transport=[dict(request_id=requests[0]["request_id"], attempt=1,
                                    latency_seconds=12.5, status="image_returned",
                                    observed=dict(width=1024, height=1024, format="PNG"))],
        transport_summary=dict(measured_latencies=1, latency_median_seconds=12.5,
                               latency_p90_seconds=12.5,
                               reported_quality_counts={"not_reported": 1}),
    )
    return value


def test_diagnostic_replay_and_complete_comparison_csv(tmp_path):
    value = dict(diagnostics=diagnostics.analyze(bundle()),
                 simulation=dict(results=[dict(scenario="synthetic", true_interactions=[0, 0],
                                               rejection_probability=[0.04, 0.05])]),
                 retained_noise=dict(groups=[dict(sample_variance=2.0)],
                                     marginal_variances={"free": 2.0}))
    first, second = tmp_path / "first", tmp_path / "second"
    before = deepcopy(value)
    paths = report.render_diagnostic(value, first)
    assert paths == report.render_diagnostic(value, second)
    assert sorted(_hashes(first)) == paths and _hashes(first) == _hashes(second)
    assert value == before
    assert len(_csv(first / "retrieval_comparisons.csv")) == 450
    assert not (first / "retrieval_predictions.csv").exists()
    assert "mean_midrank" in (first / "retrieval_comparisons.csv").read_text()
    assert "1/24 and 1/8" in (first / "REPORT.md").read_text()
    with pytest.raises(ValueError, match="empty directory"):
        report.render_diagnostic(value, first)


def test_experiment_replay_preserves_interval_fields_and_reference_weighting(tmp_path, study):
    value = _experiment(study)
    before = deepcopy(value)
    first, second = tmp_path / "first", tmp_path / "second"
    paths = report.render_experiment(value, first)
    assert paths == report.render_experiment(value, second)
    assert sorted(_hashes(first)) == paths and _hashes(first) == _hashes(second)
    assert value == before
    assert len(_csv(first / "generated_chroma.csv")) == 576
    assert len(_csv(first / "coordinate_responses.csv")) == 31
    assert len(_csv(first / "primary_covariance.csv")) == 2
    assert len(_csv(first / "reference_comparisons.csv")) == 144
    primary = _csv(first / "primary.csv")
    assert float(primary[0]["estimate"]) == pytest.approx(-7.5)
    assert len(json.loads(primary[0]["family_interval"])) == 2
    envelope = _csv(first / "reference_envelopes.csv")
    assert envelope[0]["summary.weighted_mean"] != envelope[1]["summary.weighted_mean"]
    assert not any("p_holm" in r for r in _csv(first / "processing_primary.csv"))
    text = (first / "REPORT.md").read_text()
    assert "named point response is positive" in text
    assert "**not confidence intervals**" in text and "No human ratings" in text
    assert len(_csv(first / "transport_attempts.csv")) == 1


def test_missing_primary_and_coordinate_results_are_explicit_and_renderable(tmp_path, study):
    value = _experiment(study, missing=True)
    report.render_experiment(value, tmp_path)
    text = (tmp_path / "REPORT.md").read_text()
    assert "Primary inference is withheld" in text
    assert "primary_withheld_unavailable_planned_values" in text
    assert len(_csv(tmp_path / "generated_chroma.csv")) == 576
    assert _csv(tmp_path / "primary.csv") == []
    assert _csv(tmp_path / "coordinate_responses.csv") == []
    assert (tmp_path / "plots/primary_interactions.png").is_file()
    assert (tmp_path / "plots/coordinate_interactions.svg").is_file()


def test_opposite_interaction_is_reported_without_attenuation_label(tmp_path, study):
    requests, rows, references, config = deepcopy(study)
    for row in rows:
        if row["arm"] == "monet":
            sign = -1 if row["polarity"] == "muted" else 1
            row["values"][2] += 20 * sign
            row["chroma_primary_iqr"] = (row["values"][2] - 10) / 2
            row["scaled"][2] = row["chroma_primary_iqr"]
    value = analysis.analyze(requests, rows, references, config)
    report.render_experiment(value, tmp_path)
    text = (tmp_path / "REPORT.md").read_text()
    assert "Monet: larger named response." in text
    assert float(_csv(tmp_path / "primary.csv")[0]["estimate"]) > 0
