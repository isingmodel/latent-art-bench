"""Constructed-data checks for the TMLR revision diagnostics."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v1 as diag


def panel(free, generic, named, scenes=3):
    """Noise-free panel: every scene and both repeats equal the given arm means."""
    arms = np.vstack([free, generic, named])
    return np.broadcast_to(arms, (scenes, 2, 6, arms.shape[1])).copy()


def test_exchangeable_orthogonal_shifts_give_one_quarter():
    shifts = np.eye(4)
    result = diag.decomposition(panel(np.zeros(4), np.zeros(4), shifts), np.eye(4))
    assert result["shared_fraction"] == pytest.approx(diag.EXCHANGEABLE_NULL)


def test_faithful_value_matches_named_means_at_references():
    rng = np.random.default_rng(1)
    refs = rng.normal(size=(4, 5))
    generic = rng.normal(size=5)
    result = diag.decomposition(panel(generic - 1, generic, refs), refs)
    assert result["B"] == pytest.approx(result["H"])
    assert result["shared_fraction"] == pytest.approx(result["faithful_shared_fraction"])
    assert result["projection_ratio"] == pytest.approx(1.0)
    assert result["direction_cosine"] == pytest.approx(1.0)


def test_centroid_proximity_identity_holds_with_noise():
    rng = np.random.default_rng(2)
    x = rng.normal(size=(7, 2, 6, 9))
    result = diag.decomposition(x, rng.normal(size=(4, 9)))
    assert abs(result["identity_residual"]) < 1e-10
    assert result["centroid_gain"] == pytest.approx(
        result["centroid_gain_shared"] + result["centroid_gain_between"]
    )


def test_cross_repeat_product_removes_independent_noise_on_average():
    rng = np.random.default_rng(3)
    signal = np.ones(20)
    values = [diag.xrep(signal + rng.normal(size=(2, 20)), signal + rng.normal(size=(2, 20)))
              for _ in range(4000)]
    assert np.mean(values) == pytest.approx(20, abs=0.3)


def test_fraction_along_generic_shift():
    parallel = diag.decomposition(
        panel(np.zeros(3), np.array([1.0, 0, 0]), np.full((4, 3), [3.0, 0, 0])), np.eye(4, 3)
    )
    orthogonal = diag.decomposition(
        panel(np.zeros(3), np.array([1.0, 0, 0]), np.full((4, 3), [1.0, 2.0, 0])), np.eye(4, 3)
    )
    assert parallel["fraction_along_generic"] == pytest.approx(1.0)
    assert orthogonal["fraction_along_generic"] == pytest.approx(0.0)


def test_corrected_h_is_unbiased_for_identical_painters():
    rng = np.random.default_rng(4)
    values = [
        diag.corrected_h([rng.normal(size=(n, 3)) for n in (30, 10, 15, 10)])["H_corrected"]
        for _ in range(3000)
    ]
    assert np.mean(values) == pytest.approx(0, abs=0.02)


def test_bootstrap_is_deterministic_and_paired():
    stats = {
        name: dict(scenes=list(range(5)), fn=(lambda idx, k=k: dict(d=float(np.mean(idx)) + k)))
        for k, name in enumerate(["a", "b"])
    }
    first = diag.stability(stats, ["d"], {"d": "lower"})
    assert first == diag.stability(stats, ["d"], {"d": "lower"})
    assert first["bootstrap"]["d"]["best_frequency"]["a"] == 1.0
    assert first["bootstrap"]["d"]["first_better_frequency"]["a|b"] == 1.0


def test_readouts_match_direct_computation():
    rng = np.random.default_rng(5)
    x = rng.normal(size=(4, 2, 6, 6))
    x /= np.linalg.norm(x, axis=-1, keepdims=True)
    prototypes = rng.normal(size=(4, 6))
    means, correct, errors = diag.scene_statistics(x, prototypes)
    row = diag.readouts(means, correct, errors, prototypes, list(range(4)))
    named = x[:, :, 2:].mean(axis=(0, 1))
    generic = x[:, :, 1].mean(axis=(0, 1))
    gain = np.mean(np.sum(named * prototypes, axis=1)) - generic @ prototypes.mean(axis=0)
    assert row["gain"] == pytest.approx(gain)
    assert 0 <= row["accuracy"] <= 1
