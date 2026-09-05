from __future__ import annotations

import numpy as np
import pytest
from PIL import Image
from scipy.spatial.distance import cdist

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import artifacts, corpus, features, statistics


def test_block_energy_matches_explicit_sum_and_retains_negative_estimates():
    real = np.array([[0.0]])
    generated = np.array([[[-1.0]], [[1.0]]])
    terms = statistics.energy_terms(real, generated)
    assert terms.evaluate()[0] == 0.0
    real = np.array([[-1.0], [1.0]])
    terms = statistics.energy_terms(real, generated)
    assert terms.evaluate()[0] == -1.0
    # Generator blocks are independent draws; the real self term includes its zero diagonal.
    assert statistics.finite_energy(real, generated.reshape(-1, 1)) == 0.0


def test_bootstrap_duplicate_blocks_match_materialized_position_oracle():
    rng = np.random.default_rng(7)
    real, generated = rng.normal(size=(9, 3)), rng.normal(size=(4, 3, 3))
    original = statistics.energy_terms(real, generated)
    indices = [0, 0, 1, 3]
    sampled = generated[indices]
    r, t, _ = sampled.shape
    cross = 2 * cdist(real, sampled.reshape(-1, 3)).mean()
    between = sum(cdist(sampled[i], sampled[j]).sum()
                  for i in range(r) for j in range(r) if i != j) / (r * (r - 1) * t * t)
    expected = cross - cdist(real, real).mean() - between
    assert original.evaluate(np.bincount(indices, minlength=4))[0] == pytest.approx(expected)


def test_equal_painter_scaling_is_invariant_to_replicating_one_painters_development():
    rng = np.random.default_rng(12)
    development = {p: rng.normal(size=(20 + i * 5, 31)) for i, p in enumerate(PAINTER_IDS)}
    first = statistics.fit_scaler(development)
    development[PAINTER_IDS[0]] = np.repeat(development[PAINTER_IDS[0]], 3, axis=0)
    second = statistics.fit_scaler(development)
    assert first["center"] == second["center"]
    assert first["scale"] == second["scale"]


def test_constant_coordinate_invalidates_family_instead_of_being_dropped():
    data = {p: np.ones((10, 31)) for p in PAINTER_IDS}
    scaler = statistics.fit_scaler(data)
    assert len(scaler["invalid_coordinates"]["texture"]) == 12
    with pytest.raises(ValueError, match="invalid development IQR"):
        statistics.transform(np.ones((1, 31)), scaler)


def test_zero_bootstrap_variance_is_inconclusive():
    intervals, critical = statistics.simultaneous_intervals(np.array([0.0]), np.zeros((99, 1)))
    assert intervals[0]["upper"] is None
    assert intervals[0]["status"] == "inconclusive_zero_bootstrap_variance"
    assert critical is None


def test_simultaneous_intervals_use_joint_maximum():
    rng = np.random.default_rng(1)
    draws = rng.normal(size=(999, 60))
    intervals, critical = statistics.simultaneous_intervals(np.zeros(60), draws)
    assert 2.5 < critical < 4.5
    assert all(r["lower"] < 0 < r["upper"] for r in intervals)


def test_full_analysis_requires_complete_registered_grid():
    real = {p: np.zeros((100, 31)) for p in PAINTER_IDS}
    generated = {p: np.zeros((25, 15, 31)) for p in (*PAINTER_IDS, "artist_free")}
    with pytest.raises(ValueError, match="16-template"):
        statistics.analyze(real, generated)


def test_black_and_white_have_known_color_and_flat_texture():
    black = features.extract(np.zeros((256, 256, 3)))
    white = features.extract(np.ones((256, 256, 3)))
    assert black.shape == white.shape == (31,)
    assert black[0] == 0
    assert white[0] == pytest.approx(100)
    assert black[4:7].tolist() == [0, 0, 0]
    assert white[4:7].tolist() == [0, 0, 0]
    np.testing.assert_allclose(black[7:10], 0, atol=1e-10)
    np.testing.assert_allclose(black[19:23], np.log(1e-12))


def test_rotating_stripes_flips_orientation_balance_and_preserves_spectrum():
    x = np.arange(256)
    stripes = np.broadcast_to(0.5 + 0.4 * np.sin(x * np.pi / 16), (256, 256))
    first = features.spatial_features(stripes)
    second = features.spatial_features(stripes.T)
    assert first[4] > 0.9 and second[4] < -0.9
    assert first[0] == pytest.approx(second[0], abs=1e-8)
    assert first[2] == pytest.approx(second[2], abs=1e-8)


def test_normalization_preserves_aspect_and_refuses_upsampling(tmp_path):
    path = tmp_path / "test.png"
    Image.new("RGB", (600, 400), "red").save(path)
    result = features.normalize(path, 256)
    assert result.rgb.shape == (256, 384, 3)
    assert result.metadata["color_profile"] == "missing_assumed_srgb"
    with pytest.raises(ValueError, match="upsample"):
        features.normalize(path, 512)


def test_transparency_is_not_silently_made_black(tmp_path):
    path = tmp_path / "alpha.png"
    Image.new("RGBA", (256, 256), (255, 0, 0, 0)).save(path)
    with pytest.raises(ValueError, match="nonopaque"):
        features.normalize(path, 256)


def test_identity_join_needs_unambiguous_collection_accession():
    rows = [dict(item_qid="Q1", collections=["museum"], accessions=["A.1"]),
            dict(item_qid="Q2", collections=["museum"], accessions=["A.1"]),
            dict(item_qid="Q3", collections=["museum", "other"], accessions=["A.1"])]
    assert sorted(len(g) for g in corpus.work_components(rows)) == [1, 2]


def test_roles_are_order_independent_and_exposure_never_enters_holdout():
    rows = [dict(work_id=f"Q{i}", painter_id=PAINTER_IDS[0],
                 role_hash=artifacts.digest([i]), exposure_matches=["old"] if i == 0 else [])
            for i in range(101)]
    corpus.assign_roles(rows)
    first = {r["work_id"]: r["role"] for r in rows}
    corpus.assign_roles(list(reversed(rows)))
    assert first == {r["work_id"]: r["role"] for r in rows}
    assert rows[0]["role"] == "historical_development"
    assert sum(r["role"] == "confirmation" for r in rows) == 60


def test_immutable_artifacts_and_hash_chains_detect_tampering(tmp_path):
    path = tmp_path / "receipt.json"
    artifacts.publish(path, {"a": 1})
    with pytest.raises(FileExistsError):
        artifacts.publish(path, {"a": 2})
    ledger = tmp_path / "events.jsonl"
    artifacts.append_event(ledger, {"kind": "start"})
    artifacts.append_event(ledger, {"kind": "finish"})
    assert len(artifacts.events(ledger)) == 2
    ledger.write_text(ledger.read_text().replace('"start"', '"altered"'))
    with pytest.raises(ValueError, match="broken event chain"):
        artifacts.events(ledger)
