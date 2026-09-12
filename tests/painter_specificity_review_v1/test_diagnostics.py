"""Small analytical controls for the new post-result estimands."""

import itertools

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_specificity_reference_v1.analysis import CLASSES
from latent_art_bench.painter_specificity_review_v1 import (
    calibration,
    covariance_map,
    metrics,
    real_controls,
    simulation,
    stratified_energy,
)
from latent_art_bench.painter_specificity_v1.analysis import centered, energy


def test_scene_interaction_is_penalized_despite_correct_aggregate():
    r = np.array([[-1.0, 0], [1.0, 0]])
    u = np.array([[0.0, -1], [0.0, 1]])
    d = np.stack([np.stack([r + u, r + u]), np.stack([r - u, r - u])])
    result = calibration(d, r)
    assert result["beta"] == pytest.approx(1)
    assert result["aggregate_d"] == pytest.approx(0)
    assert result["scene_variation"] == pytest.approx(1)
    assert result["d"] == pytest.approx(1)


def test_independent_repeat_noise_cancels_but_shared_noise_does_not():
    r = np.array([[-1.0, 0], [1.0, 0]])
    e = np.array([[0.0, -1], [0.0, 1]])
    independent = np.array(
        [[r + a * e, r + b * e] for a, b in itertools.product((-1, 1), repeat=2)]
    )
    dependent = np.array([[r + a * e, r + a * e] for a in (-1, 1)])
    assert metrics(independent, r)[2].mean() == pytest.approx(0)
    assert metrics(dependent, r)[2].mean() == pytest.approx(1)


def test_scalar_fitting_uses_only_other_scenes():
    r = np.array([[-1.0, 0], [1.0, 0]])
    d = np.broadcast_to(2 * r, (14, 2, 2, 2)).copy()
    base = calibration(d, r)
    assert base["held_out_d"] == pytest.approx(0)
    assert base["fitted_scalars"] == pytest.approx([0.5] * 14)
    d[-1] *= 7
    changed = calibration(d, r)
    assert changed["fitted_scalars"][-1] == pytest.approx(0.5)
    assert changed["held_out_scene_d"][-1] == pytest.approx(36)


def test_stratified_energy_expectation_matches_fixed_mixture():
    ref = np.array([[0.0], [1.0], [3.0]])
    support = [np.array([[0.0], [2.0]]), np.array([[3.0], [6.0]])]
    draws = []
    for indices in itertools.product(range(2), repeat=4):
        y = np.array([[support[s][indices[2 * s + k]] for k in range(2)] for s in range(2)])
        draws.append(stratified_energy(ref, y)["corrected"])
    # Each stratum contributes equally, so four support points have equal mass.
    assert np.mean(draws) == pytest.approx(energy(ref, np.concatenate(support)))
    assert cdist(np.concatenate(support), np.concatenate(support)).shape == (4, 4)


def test_covariance_map_is_positive_and_weighted_replication_invariant():
    dev = np.array([[0.0, 0], [1.0, 4], [2.0, 8], [3.0, 9]])
    weights = np.array([0.4, 0.3, 0.2, 0.1])
    a = covariance_map(dev, weights)
    b = covariance_map(np.repeat(dev, 2, axis=0), np.repeat(weights / 2, 2))
    np.testing.assert_allclose(a, b, atol=1e-12)
    assert np.linalg.eigvalsh(a).min() > 0


def test_real_control_seed_and_disjoint_half_support():
    rng = np.random.default_rng(4)
    refs = [rng.normal(size=(24, 3)) + a for a in range(4)]
    labels = [np.repeat(CLASSES, 6) for _ in range(4)]
    a = real_controls(refs, labels, draws=5)
    assert a == real_controls(refs, labels, draws=5)
    assert all(len(v["draws"]) == 5 for v in a.values())
    with pytest.raises(ValueError, match="support"):
        real_controls([v[:12] for v in refs], [np.repeat(CLASSES, 3)] * 4, draws=1)


def test_simulation_detects_shared_state_bias():
    r = centered(np.random.default_rng(2).normal(size=(4, 31)))
    results = simulation(r, repetitions=200)
    assert np.mean(results[0]["mean_error_bias"]) == pytest.approx(0, abs=0.06)
    assert np.mean(results[-1]["mean_error_bias"]) == pytest.approx(0.25, abs=0.06)
