"""Create-once small-study calibration records reject incomplete or relabeled evidence."""

import copy
import json
from pathlib import Path

import pytest

from latent_art_bench.painter_prompt_study_v1 import randomization_record as record
from latent_art_bench.painter_prompt_study_v1.randomization import simulate_randomization


@pytest.fixture(scope="module")
def documents():
    return [simulate_randomization(seed=seed, trials=2000) for _, seed in record.RECORDS]


def test_fixed_development_and_unseen_validation_qualify_small_counts(documents):
    result = record._decision_fields(documents)
    assert result["qualified_repetitions"] == [1, 2, 4]
    assert result["primary_estimator"] == "paired_randomization"
    assert result["primary_endpoints"] == 48
    assert result["simultaneous_alpha"] == 0.05
    assert "no CIs" in result["inference_scope"]


@pytest.mark.parametrize(
    "fault",
    [
        "seed",
        "trials",
        "missing_null",
        "duplicate_null",
        "count",
        "wilson",
        "draws",
        "missing_power",
        "missing_stress",
    ],
)
def test_incomplete_or_relabeled_calibration_is_rejected(documents, fault):
    changed = copy.deepcopy(documents)
    row = changed[1]
    if fault == "seed":
        row["seed"] = 20260908
    elif fault == "trials":
        row["trials_per_cell"] = 1000
    elif fault == "missing_null":
        row["null_cells"].pop()
    elif fault == "duplicate_null":
        row["null_cells"][0] = row["null_cells"][1]
    elif fault == "count":
        row["null_cells"][0]["family_rejections"] += 1
    elif fault == "wilson":
        row["null_cells"][0]["family_rejection_wilson_95"][1] = 0
    elif fault == "draws":
        row["monte_carlo_draws"] = 9999
    elif fault == "missing_power":
        row["power_diagnostics"].pop()
    else:
        row["invalid_persistent_sign_stress"].pop()
    with pytest.raises(ValueError):
        record._decision_fields(changed)


def test_validly_recorded_failure_disqualifies_only_its_count(documents):
    changed = copy.deepcopy(documents)
    row = changed[1]["null_cells"][0]
    row.update(
        family_rejections=200,
        family_rejection_rate=0.1,
        family_rejection_wilson_95=record.wilson(200, 2000),
    )
    assert record._decision_fields(changed)["qualified_repetitions"] == [2, 4]


def test_source_commit_must_exist_before_publication(tmp_path, monkeypatch):
    def reject(*args):
        raise ValueError("commit first")

    monkeypatch.setattr(record, "committed", reject)
    with pytest.raises(ValueError, match="commit first"):
        record.publish_randomization_calibration(tmp_path, "small", [Path("a"), Path("b")])
    assert not (tmp_path / record.MANIFESTS).exists()


def test_original_values_are_retained_and_tampering_or_republication_fails(
    tmp_path, monkeypatch, documents
):
    for path in record.CODE_INPUTS:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("bound fixture\n")
    sources = []
    for index, document in enumerate(documents):
        path = Path(f"source-{index}.json")
        (tmp_path / path).write_text(json.dumps(document))
        sources.append(path)
    monkeypatch.setattr(record, "committed", lambda *args: "a" * 40)
    monkeypatch.setattr(record, "_verify_commit", lambda *args: None)
    decision = record.publish_randomization_calibration(tmp_path, "small", sources)
    assert record.validate_randomization_calibration(tmp_path, "small") == decision
    for (name, _), document in zip(record.RECORDS, documents):
        assert json.loads((tmp_path / record.MANIFESTS / "small" / name).read_bytes()) == document
    with pytest.raises(FileExistsError):
        record.publish_randomization_calibration(tmp_path, "small", sources)
    path = tmp_path / record.MANIFESTS / "small" / "decision.json"
    path.write_text(json.dumps(dict(decision, qualified_repetitions=[1, 2, 4, 8])))
    with pytest.raises(ValueError, match="qualification does not reproduce"):
        record.validate_randomization_calibration(tmp_path, "small")
