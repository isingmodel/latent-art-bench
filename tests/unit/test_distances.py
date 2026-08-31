import pytest

from latent_art_bench.evaluation.distances import analyze_cell, energy_distance
from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import AnalysisCell


def _cell(**updates: object) -> AnalysisCell:
    digest = "a" * 64
    values = {
        "cell_id": "cell",
        "target_artist_id": "target",
        "model": "gpt-image-1",
        "measurement": "chromatic",
        "feature_name": "chromatic_distance_seamlessness",
        "feature_version": "test-v1",
        "feature_config_hash": digest,
        "qualification_evidence_artifact_sha256": digest,
        "real_feature_manifest_sha256": digest,
        "generated_feature_manifest_sha256": digest,
        "generation_manifest_sha256": digest,
        "generation_attestation_sha256": digest,
        "reference_transform_state_sha256": digest,
        "target_train_vectors": [[0.0], [0.1]],
        "target_held_out_vectors": [[0.0], [0.2]],
        "generated_vectors": [[0.1], [0.2]],
        "neighbor_vectors": {"neighbor": [[1.0], [1.2]]},
    }
    values.update(updates)
    return AnalysisCell.model_validate(values)


def test_energy_distance_is_zero_for_identical_samples() -> None:
    values = [[0.0, 0.0], [1.0, 1.0]]
    assert energy_distance(values, values) == pytest.approx(0.0)


def test_analysis_specificity_is_positive_when_target_is_closer() -> None:
    cell = _cell(
        cell_id="cell-1",
        target_artist_id="artist-1",
        model="gpt-image-2",
        target_train_vectors=[[0.0], [0.2]],
        target_held_out_vectors=[[0.1], [0.3]],
        generated_vectors=[[0.1], [0.2]],
        neighbor_vectors={"artist-2": [[4.0], [4.2]]},
    )
    result = analyze_cell(cell)
    assert result.specificity_margin > 0
    assert result.nearest_neighbor_id == "artist-2"
    assert result.specificity_sign_convention == "positive_means_target_closer"
    assert result.subsample_draws == 200
    assert result.subsample_size == 2
    assert len(result.specificity_margin_interval) == 2
    assert result.analysis_cell_sha256 == stable_hash(cell.model_dump(mode="json"))


def test_neighbor_is_selected_from_real_only_separation() -> None:
    cell = _cell(
        cell_id="cell-neighbor-freeze",
        target_artist_id="target",
        model="gpt-image-1",
        target_train_vectors=[[0.0], [0.1]],
        target_held_out_vectors=[[0.0], [0.2]],
        generated_vectors=[[100.0], [101.0]],
        neighbor_vectors={
            "real-nearest": [[1.0], [1.2]],
            "generated-nearest": [[100.0], [101.0]],
        },
    )
    result = analyze_cell(cell, draws=1)
    assert result.nearest_neighbor_id == "real-nearest"
