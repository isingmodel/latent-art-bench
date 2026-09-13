"""Analytical and structural checks for the review clarification diagnostics."""

import itertools

import numpy as np
import pytest

from latent_art_bench import painter_specificity_review_v1 as previous
from latent_art_bench.painter_specificity_review_v2 import (
    PAIRS,
    calibration_stability,
    centered_noise_power,
    cross_repeat_alignment,
    expected_control_error,
    real_control_decomposition,
    simulation_endpoints,
    simulation_geometry,
    simulation_sweep,
)
from latent_art_bench.painter_specificity_v1.analysis import centered


def test_cross_moments_remove_shared_free_arm_noise_in_expectation():
    results = []
    for e0, e1 in itertools.product((-1, 1), repeat=2):
        x = np.zeros((1, 2, 6, 2))
        x[0, :, 1] = [2, 0]
        x[0, :, 2:] = [1, 1]
        x[0, :, 0, 1] = [e0, e1]
        results.append(cross_repeat_alignment(x))
    assert np.mean([v["cross_numerator"] for v in results]) == pytest.approx(2)
    assert np.mean([v["plugin_numerator"] for v in results]) == pytest.approx(2.5)
    assert np.mean([v["generic_cross_norm_squared"] for v in results]) == pytest.approx(4)
    assert np.mean([v["common_cross_norm_squared"] for v in results]) == pytest.approx(2)


def test_ratio_is_symmetric_and_not_clipped_or_defined_for_negative_norms():
    x = np.zeros((3, 2, 6, 2))
    x[:, 0, 1] = [1, 2]
    x[:, 1, 1] = [1, 0]
    x[:, 0, 2:] = [1, 0]
    x[:, 1, 2:] = [1, 2]
    result = cross_repeat_alignment(x)
    assert result["ratio"] == pytest.approx(3)
    assert cross_repeat_alignment(x[:, ::-1]) == result
    x[:, 1, 1] = [-1, 0]
    assert cross_repeat_alignment(x)["ratio"] is None


def test_conditional_expectation_integrates_independent_finite_pool_sampling():
    pools = [np.array([[0.0], [2.0]]), np.array([[3.0], [7.0]])]
    target = np.array([[-2.0], [2.0]])
    scores = []
    for indices in itertools.product(range(2), repeat=4):
        draws = np.array([[pools[a][indices[2 * k + a]] for a in range(2)] for k in range(2)])
        scores.append(previous.metrics(centered(draws[None]), target)[2].mean())
    mu = centered(np.array([p.mean(axis=0) for p in pools]))
    expected = expected_control_error(mu, target)
    assert expected == pytest.approx(np.mean(scores), abs=1e-14)
    assert expected == pytest.approx(0)
    assert np.std(scores) > 0


def test_conditional_class_targets_use_average_target_normalization():
    mu = np.array([[[-1.0], [1.0]], [[-4.0], [4.0]]])
    target = np.array([[[-2.0], [2.0]], [[-3.0], [3.0]]])
    expected = np.square(mu - target).sum(axis=(1, 2)).mean()
    expected /= np.square(target).sum(axis=(1, 2)).mean()
    assert expected_control_error(mu, target) == pytest.approx(expected)


def test_control_decomposition_replays_original_draws_exactly():
    rng = np.random.default_rng(4)
    refs = [rng.normal(size=(24, 3)) + a for a in range(4)]
    labels = [np.repeat(previous.CLASSES, 6) for _ in range(4)]
    original = previous.real_controls(refs, labels, draws=7)
    result = real_control_decomposition(refs, labels, draws=7, original=original)
    assert all(len(row["conditional_expected"]["draws"]) == 7 for row in result.values())
    assert all(min(row["conditional_expected"]["draws"]) >= 0 for row in result.values())


def test_scene_deletion_refits_inner_folds_and_does_not_average_original_folds():
    r = np.array([[-1.0, 0], [1.0, 0]])
    scales = np.array([1.0, 1.5, 2, 4])
    a = np.repeat((scales[:, None, None] * r)[:, None], 2, axis=1)
    b = np.repeat(np.broadcast_to(2 * r, (4, 1, 2, 2)), 2, axis=1)
    result = calibration_stability(a, b, r)
    for i, deletion in enumerate(result["scene_deletions"]):
        remaining = np.delete(scales, i)
        for j, scalar in enumerate(deletion["a"]["fitted_scalars"]):
            train = np.delete(remaining, j)
            assert scalar == pytest.approx(train.mean() / np.square(train).mean())
    omitted = result["scene_deletions"][-1]["a"]["held_out_d"]
    assert omitted != pytest.approx(np.mean(result["original_a"]["held_out_scene_d"][:-1]))


def test_noise_power_centers_before_squaring_and_removes_artist_common_noise():
    r = centered(np.arange(8).reshape(4, 2))
    x = np.zeros((3, 2, 6, 2))
    x[:, 0, 2:] = [1, 2]
    result = centered_noise_power(x, r)
    assert result["direct"] == pytest.approx(0)
    assert result["independent_artist_approximation"] > 0


def test_simulation_covariance_has_declared_power_rank_and_reference_alignment():
    r = centered(np.random.default_rng(8).normal(size=(4, 31)))
    target, _, axes, weights = simulation_geometry(r)
    flat = axes.reshape(3, -1)
    covariance = (flat.T * weights) @ flat
    assert np.trace(covariance) == pytest.approx(1)
    assert np.linalg.matrix_rank(covariance) == 3
    np.testing.assert_allclose(centered(axes), axes, atol=1e-12)
    assert target.ravel() @ covariance @ target.ravel() > 1 / 93


def test_simulation_uses_six_slopes_and_fifteen_paired_scene_differences():
    r = centered(np.random.default_rng(8).normal(size=(4, 31)))
    r, theta, _, _ = simulation_geometry(r)
    d = np.broadcast_to(theta[None, :, None, None], (1, 6, 14, 2, 4, 31))
    endpoints, errors = simulation_endpoints(d, r)
    assert endpoints.shape == (1, 21, 14)
    for index, (a, b) in enumerate(PAIRS):
        np.testing.assert_allclose(endpoints[:, 6 + index], errors[:, a] - errors[:, b])
    np.testing.assert_allclose(endpoints[0, :6, 0], [0.95, 1, 0.77, 0.82, 0.44, 0.47])


def test_simulation_sweep_has_correct_power_and_negligible_independent_repeat_bias():
    r = centered(np.random.default_rng(8).normal(size=(4, 31)))
    result = simulation_sweep(r, repetitions=300)
    assert len(result["scenarios"]) == 6
    assert len(result["endpoint_labels"]) == 21
    for row in result["scenarios"]:
        assert row["observed_mean_noise_power"] == pytest.approx(
            row["centered_noise_power"], rel=0.035
        )
        assert abs(np.mean(row["mean_error_bias"])) < 0.07
        assert len(row["marginal_coverage"]) == 21
