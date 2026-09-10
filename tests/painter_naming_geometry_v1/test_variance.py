"""Mathematical and fixed-scene simulation checks; no retained image inputs."""

import json

import numpy as np
import pytest

from latent_art_bench.painter_naming_geometry_v1.variance import (
    corrected_variance,
    cross_repeat_residual,
)


def test_unequal_weight_hand_calculation_and_scene_accounting():
    # Means 0, 4; unbiased scene variances 1, 4; scene weights 1/4, 3/4.
    # Bobs=3, Wobs=13/6, N=13/4, correction=5/16, B*=43/16.
    x = np.array([[[-1.0], [0.0], [1.0]], [[2.0], [4.0], [6.0]]])
    result = corrected_variance(x, [0.25, 0.75])
    assert result["observed_between"] == pytest.approx(3)
    assert result["observed_within"] == pytest.approx(13 / 6)
    assert result["observed_total"] == pytest.approx(31 / 6)
    assert result["repeat_noise"] == pytest.approx(13 / 4)
    assert result["centroid_noise_correction"] == pytest.approx(5 / 16)
    assert result["corrected_between"] == pytest.approx(43 / 16)
    assert result["corrected_total"] == pytest.approx(95 / 16)
    assert result["corrected_signal_to_noise"] == pytest.approx(43 / 52)
    assert result["observed_identity_residual"] == pytest.approx(0, abs=1e-14)
    for key in (
        "observed_between", "observed_within", "observed_total", "repeat_noise",
        "centroid_noise_correction", "corrected_between",
    ):
        assert sum(row[key] for row in result["per_scene"]) == pytest.approx(result[key])
    assert [r["sample_covariance_trace"] for r in result["per_scene"]] == [1, 4]
    assert result["per_scene"][0]["centroid_noise_correction"] == pytest.approx(1 / 16)
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_negative_corrected_signal_is_retained_even_with_two_repeats():
    # Identical zero centroids, but nonzero repeat variation in both scenes.
    result = corrected_variance([[[-1], [1]], [[-2], [2]]], [0.5, 0.5])
    assert result["observed_between"] == 0
    assert result["repeat_noise"] == pytest.approx(5)
    assert result["centroid_noise_correction"] == pytest.approx(1.25)
    assert result["corrected_between"] == pytest.approx(-1.25)
    assert result["corrected_signal_to_noise"] == pytest.approx(-0.25)
    assert result["corrected_total"] == pytest.approx(3.75)


def test_zero_repeat_noise_has_no_signal_to_noise_ratio():
    separated = corrected_variance([[[0], [0]], [[2], [2]]], [0.5, 0.5])
    assert separated["repeat_noise"] == 0
    assert separated["corrected_between"] == 1
    assert separated["corrected_signal_to_noise"] is None
    identical = corrected_variance(np.zeros((3, 3, 2)), [0.2, 0.3, 0.5])
    assert identical["corrected_total"] == 0
    assert identical["corrected_signal_to_noise"] is None


def test_nonfinite_ratio_is_unavailable_without_discarding_finite_traces():
    x = np.array([[[0.0], [1e-150], [-1e-150]], [[1e100], [1e100], [1e100]]])
    result = corrected_variance(x, [0.5, 0.5])
    assert result["repeat_noise"] > 0
    assert np.isfinite(result["corrected_between"])
    assert result["corrected_signal_to_noise"] is None
    json.dumps(result, allow_nan=False)


def test_equal_scene_formula_and_unequal_scene_counts_are_distinct():
    rng = np.random.default_rng(320)
    x = rng.normal(size=(5, 3, 4))
    result = corrected_variance(x, np.full(5, 0.2))
    assert result["centroid_noise_correction"] == pytest.approx(
        (1 - 1 / 5) * result["observed_within"] / (3 - 1)
    )
    # Unequal weights cannot substitute an unweighted scene-count correction.
    unequal = corrected_variance(x, [0.05, 0.1, 0.15, 0.3, 0.4])
    assert unequal["centroid_noise_correction"] != pytest.approx(
        (1 - 1 / 5) * unequal["observed_within"] / (3 - 1)
    )


def test_geometry_invariances_and_no_input_mutation():
    rng = np.random.default_rng(98)
    x = rng.normal(size=(4, 3, 3))
    weights = np.array([0.1, 0.2, 0.3, 0.4])
    before_x, before_w = x.copy(), weights.copy()
    baseline = corrected_variance(x, weights)
    rotation = np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]])
    variants = (
        corrected_variance(x + [10, -3, 7], weights),
        corrected_variance(x @ rotation, weights),
        corrected_variance(x[:, [2, 0, 1]], weights),
        corrected_variance(x[[2, 0, 3, 1]], weights[[2, 0, 3, 1]]),
    )
    trace_keys = (
        "observed_between", "observed_within", "observed_total", "repeat_noise",
        "centroid_noise_correction", "corrected_between", "corrected_total",
    )
    for variant in variants:
        for key in trace_keys + ("corrected_signal_to_noise",):
            assert variant[key] == pytest.approx(baseline[key], abs=1e-12)
    scaled = corrected_variance(-2 * x, weights)
    for key in trace_keys:
        assert scaled[key] == pytest.approx(4 * baseline[key])
    assert scaled["corrected_signal_to_noise"] == pytest.approx(
        baseline["corrected_signal_to_noise"]
    )
    assert np.array_equal(x, before_x)
    assert np.array_equal(weights, before_w)


@pytest.mark.parametrize("noise_kind", ["normal", "student_t5"])
def test_fixed_scene_heteroskedastic_noise_calibration(noise_kind):
    # Fixed means/weights throughout: these trials sample only independent repeat errors.
    rng = np.random.default_rng(104)
    weights = np.array([0.1, 0.2, 0.3, 0.4])
    means = np.array([[-2, 1], [0, -1], [1, 0], [3, 2]])
    std = np.array([[0.5, 1], [1, 2], [2, 0.25], [0.75, 1.5]])
    trials, repeats = 4000, 3
    if noise_kind == "normal":
        errors = rng.normal(size=(trials, 4, repeats, 2))
    else:
        errors = rng.standard_t(5, size=(trials, 4, repeats, 2)) * np.sqrt(3 / 5)
    samples = means[None, :, None, :] + errors * std[None, :, None, :]
    output = [corrected_variance(sample, weights) for sample in samples]
    true_signal = float(weights @ np.square(means - weights @ means).sum(axis=1))
    scene_trace = np.square(std).sum(axis=1)
    true_noise = float(weights @ scene_trace)
    correction = float((weights * (1 - weights)) @ scene_trace / repeats)
    targets = dict(
        corrected_between=true_signal,
        repeat_noise=true_noise,
        corrected_total=true_signal + true_noise,
        centroid_noise_correction=correction,
        observed_between=true_signal + correction,
        observed_within=(repeats - 1) / repeats * true_noise,
    )
    for key, target in targets.items():
        estimates = np.array([row[key] for row in output])
        # A mean across simulated independent experiments, not an effect CI or
        # a claim that simulation establishes service-error assumptions.
        monte_carlo_se = estimates.std(ddof=1) / np.sqrt(trials)
        assert abs(estimates.mean() - target) < 5 * monte_carlo_se


def test_shared_repeat_error_can_make_the_model_correction_biased():
    # A common shock in a repeat changes every scene identically: between-scene
    # distances retain only their fixed means. Subtracting independent-scene
    # centroid noise would be wrong under this cross-scene error dependence.
    means = np.array([[[0.0]], [[4.0]]])
    x = means + np.array([[[-1.0], [0.0], [1.0]]])
    result = corrected_variance(x, [0.5, 0.5])
    assert result["observed_between"] == 4
    assert result["corrected_between"] == pytest.approx(4 - 1 / 6)


@pytest.mark.parametrize(
    "values, weights, message",
    [
        (np.zeros((2, 2)), [0.5, 0.5], "J by R by D"),
        (np.zeros((1, 3, 2)), [1], "J by R by D"),
        (np.zeros((2, 1, 2)), [0.5, 0.5], "J by R by D"),
        (np.zeros((2, 3, 0)), [0.5, 0.5], "J by R by D"),
        (np.full((2, 3, 1), np.nan), [0.5, 0.5], "finite"),
        (np.full((2, 3, 1), np.inf), [0.5, 0.5], "finite"),
        (np.zeros((2, 3, 1)), [0, 1], "positive"),
        (np.zeros((2, 3, 1)), [-0.5, 1.5], "positive"),
        (np.zeros((2, 3, 1)), [0.4, 0.4], "sum to one"),
        (np.zeros((2, 3, 1)), [0.5, 0.500001], "sum to one"),
        (np.zeros((2, 3, 1)), [0.5, np.nan], "finite"),
        (np.zeros((2, 3, 1)), [[0.5], [0.5]], "per scene"),
        (np.zeros((2, 3, 1)), [1 / 3] * 3, "per scene"),
        (np.full((2, 3, 1), 1j), [0.5, 0.5], "real numeric"),
        ([[["not a number"]]], [0.5, 0.5], "real numeric"),
        ([[[0], [1]], [[2]]], [0.5, 0.5], "real numeric"),
        (np.full((2, 3, 1), 1e308), [0.5, 0.5], "finite trace"),
    ],
)
def test_invalid_inputs_fail_without_silent_repairs(values, weights, message):
    with pytest.raises(ValueError, match=message):
        corrected_variance(values, weights)
    with pytest.raises(ValueError, match=message):
        cross_repeat_residual(values, weights)


def test_cross_repeat_noiseless_means_and_direct_inner_products():
    x = np.array([[[1, 2]] * 3, [[3, 4]] * 3], dtype=float)
    result = cross_repeat_residual(x, [0.25, 0.75])
    assert result["naive_mean_residual_squared"] == 20
    assert result["correction"] == 0
    assert result["cross_repeat_mean_square"] == 20
    rng = np.random.default_rng(124)
    x = rng.normal(size=(4, 3, 5))
    weights = np.array([0.1, 0.2, 0.3, 0.4])
    result = cross_repeat_residual(x, weights)
    direct = sum(
        weights[b] * sum(float(x[b, r] @ x[b, s]) for r in range(3)
                         for s in range(3) if r != s) / 6
        for b in range(4)
    )
    assert result["cross_repeat_mean_square"] == pytest.approx(direct, abs=1e-14)
    for key in ("naive_mean_residual_squared", "correction", "cross_repeat_mean_square"):
        assert sum(row[key] for row in result["per_scene"]) == pytest.approx(result[key])
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_cross_repeat_negative_estimate_is_not_truncated():
    result = cross_repeat_residual([[[-1], [1]], [[-2], [2]]], [0.5, 0.5])
    assert result["naive_mean_residual_squared"] == 0
    assert result["correction"] == 2.5
    assert result["cross_repeat_mean_square"] == -2.5


def test_cross_repeat_calibration_with_paired_dependence_and_zero_mean_noise():
    rng = np.random.default_rng(410)
    weights = np.array([0.2, 0.3, 0.5])
    trials, scenes, repeats, dimensions = 4000, 3, 3, 2
    shared = rng.normal(size=(trials, scenes, repeats, dimensions))
    free_error = shared + rng.normal(size=shared.shape)
    named_error = 0.5 * shared + rng.normal(size=shared.shape)
    # A fixed map slope; the paired named/free errors are correlated within a
    # repetition, but independent across repetitions. Mean mismatch is zero.
    residuals = named_error - 0.8 * free_error
    results = [cross_repeat_residual(x, weights) for x in residuals]
    corrected = np.array([r["cross_repeat_mean_square"] for r in results])
    naive = np.array([r["naive_mean_residual_squared"] for r in results])
    assert abs(corrected.mean()) < 5 * corrected.std(ddof=1) / np.sqrt(trials)
    assert naive.mean() > 1
    # Nonzero fixed means estimate squared mismatch rather than its noise floor.
    means = np.array([[1, -2], [2, 0], [-1, 1]])
    shifted = [cross_repeat_residual(x + means[:, None, :], weights)
               for x in residuals]
    estimates = np.array([r["cross_repeat_mean_square"] for r in shifted])
    target = float(weights @ np.square(means).sum(axis=1))
    assert abs(estimates.mean() - target) < 5 * estimates.std(ddof=1) / np.sqrt(trials)


def test_cross_repeat_geometry_and_permutation_invariance_without_mutation():
    rng = np.random.default_rng(903)
    x = rng.normal(size=(3, 3, 2))
    weights = np.array([0.2, 0.3, 0.5])
    original = x.copy()
    baseline = cross_repeat_residual(x, weights)
    transformed = cross_repeat_residual(x[:, [2, 0, 1]] @ np.array([[0, 1], [-1, 0]]),
                                        weights)
    reordered = cross_repeat_residual(x[[2, 0, 1]], weights[[2, 0, 1]])
    scaled = cross_repeat_residual(3 * x, weights)
    for key in ("naive_mean_residual_squared", "correction", "cross_repeat_mean_square"):
        assert transformed[key] == pytest.approx(baseline[key])
        assert reordered[key] == pytest.approx(baseline[key])
        assert scaled[key] == pytest.approx(9 * baseline[key])
    assert np.array_equal(x, original)
