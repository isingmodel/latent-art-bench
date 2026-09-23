"""Analytic/synthetic identities only; never load retained measurement data."""

import itertools

import numpy as np
import pytest

from latent_art_bench import painter_repeat_covariance_v1 as covariance


def reference():
    return np.array([[-1.0, 0], [1, 0], [0, -1], [0, 1]])


def test_expectation_with_unequal_variances_and_cross_repeat_covariance():
    r = reference()
    h = np.square(r).sum()
    theta = 0.6 * r
    shared = np.array([[1.0, 1], [-1, 0], [0, -1], [0, 0]])
    repeat0 = np.array([[0.0, 1], [0, -1], [0, 0], [0, 0]])
    repeat1 = np.array([[2.0, 0], [-2, 0], [0, 0], [0, 0]])
    marginal_v = (np.square(shared).sum() + (
        np.square(repeat0).sum() + np.square(repeat1).sum()
    ) / 2) / h
    cross_c = np.square(shared).sum() / h
    rho = cross_c / marginal_v
    true_d = np.square(theta - r).sum() / h
    rows = []
    adjusted = []
    for u, e0, e1 in itertools.product((-1, 1), repeat=3):
        named = np.stack([theta + u * shared + e0 * repeat0,
                          theta + u * shared + e1 * repeat1])[None]
        row = covariance.scene_statistics(named, r)
        rows.append(row)
        adjusted.append(covariance.sensitivity(row["d"], row["q"], rho)["adjusted_d"])
    assert np.mean([row["d"] for row in rows]) == pytest.approx(true_d + cross_c)
    assert np.mean([row["q"] for row in rows]) == pytest.approx(marginal_v - cross_c)
    assert np.mean(adjusted) == pytest.approx(true_d)
    assert np.square(repeat0).sum() != np.square(repeat1).sum()


def test_negative_cross_covariance_also_obeys_variance_minus_covariance_identity():
    r = reference()
    rows = [covariance.scene_statistics(np.stack([r + sign*r, r - sign*r])[None], r)
            for sign in (-1, 1)]
    assert np.mean([row["d"] for row in rows]) == pytest.approx(-1)
    assert np.mean([row["q"] for row in rows]) == pytest.approx(2)


def test_shared_state_is_invisible_to_repeat_differences():
    r = reference()
    before = np.stack([r + 0.5*r, r - 0.5*r])[None]
    shifted = before + 8 * r
    first = covariance.scene_statistics(before, r)
    second = covariance.scene_statistics(shifted, r)
    assert first["q"] == pytest.approx(second["q"])
    assert first["d"] != pytest.approx(second["d"])


def test_centering_reference_scale_and_repeat_swap():
    r = reference()
    rng = np.random.default_rng(92)
    named = rng.normal(size=(3, 2, 4, 2))
    base = covariance.scene_statistics(named, r)
    shifted = covariance.scene_statistics(named + rng.normal(size=(3, 2, 1, 2)), r)
    swapped = covariance.scene_statistics(named[:, ::-1], r)
    scaled = covariance.scene_statistics(7 * named, 7 * r)
    for result in (shifted, swapped, scaled):
        for key in ("scene_d", "scene_q", "d", "q"):
            assert result[key] == pytest.approx(base[key])
    assert scaled["reference_h"] == pytest.approx(49 * base["reference_h"])


def test_scene_mean_is_mean_of_scene_cross_products_not_product_of_scene_means():
    r = reference()
    named = np.array([[r, r], [3*r, 3*r]])
    result = covariance.scene_statistics(named, r)
    assert result["scene_d"] == pytest.approx([0, 4])
    assert result["d"] == pytest.approx(2)
    assert result["q"] == 0
    assert result["d"] != pytest.approx(np.square(named.mean(axis=(0, 1)) - r).sum()
                                        / np.square(r).sum())


def test_common_covariance_preserves_gap_but_common_correlation_need_not():
    d_a, d_b, q_a, q_b = 3.0, 1.0, 5.0, 1.0
    common_bias = 0.4
    assert (d_a - common_bias) - (d_b - common_bias) == pytest.approx(d_a - d_b)
    rho_a, rho_b = common_bias / (q_a + common_bias), common_bias / (q_b + common_bias)
    a = covariance.sensitivity(d_a, q_a, rho_a)
    b = covariance.sensitivity(d_b, q_b, rho_b)
    assert a["implied_bias"] == pytest.approx(b["implied_bias"])
    assert a["adjusted_d"] - b["adjusted_d"] == pytest.approx(2)
    pair = covariance.pair_curve(d_a, q_a, d_b, q_b)
    assert pair["crossing"]["rho"] == pytest.approx(1/3)
    assert pair["grid"][3]["adjusted_difference"] == pytest.approx(-2)


@pytest.mark.parametrize("reverse", [False, True])
def test_analytic_positive_crossing_and_both_implied_biases(reverse):
    values = (3.0, 5.0, 1.0, 1.0)
    if reverse:
        values = values[2:] + values[:2]
    pair = covariance.pair_curve(*values)
    c = pair["crossing"]
    assert c["status"] == "positive_interior_crossing"
    assert c["rho"] == pytest.approx(1/3)
    assert c["alpha"] == pytest.approx(0.5)
    assert values[0] - c["implied_bias_a"] == pytest.approx(values[2] - c["implied_bias_b"])
    left, right = c["rho"] - 0.01, c["rho"] + 0.01
    gaps = [covariance.sensitivity(values[0], values[1], rho)["adjusted_d"]
            - covariance.sensitivity(values[2], values[3], rho)["adjusted_d"]
            for rho in (left, right)]
    assert gaps[0] * gaps[1] < 0


@pytest.mark.parametrize("values,status", [
    ((1, 5, 3, 1), "no_positive_interior_crossing"),
    ((3, 2, 1, 2), "no_positive_interior_crossing"),
    ((3, 2, 3, 2), "tied_for_all_rho"),
    ((3, 2, 3, 1), "initial_tie_separates"),
])
def test_no_crossing_and_tie_cases(values, status):
    result = covariance.pair_curve(*values)
    assert result["crossing"]["status"] == status
    for key in ("rho", "alpha", "implied_bias_a", "implied_bias_b"):
        assert result["crossing"][key] is None


def test_crossing_above_grid_is_retained_and_rounding_does_not_create_ties():
    high = covariance.pair_curve(11, 2, 1, 1)
    assert high["crossing"]["rho"] == pytest.approx(10/11)
    tiny = covariance.pair_curve(1 + 1e-10, 2, 1, 1)
    assert tiny["crossing"]["status"] == "positive_interior_crossing"
    assert tiny["delta_d"] > 0


def test_grid_and_negative_adjustments_are_retained_without_clipping():
    curve = covariance.model_curve(0.2, 2)
    assert [row["rho"] for row in curve] == [0, 0.1, 0.25, 0.5, 0.75]
    assert curve[0]["adjusted_d"] == 0.2
    assert curve[-1]["adjusted_d"] == pytest.approx(-5.8)
    assert curve[-1]["negative_adjusted_d"]


@pytest.mark.parametrize("values", [(1, -1, 0.5), (np.nan, 1, .5), (1, 1, 1),
                                    (1, 1, -0.1), (1, np.inf, 0)])
def test_invalid_sensitivity_values_are_rejected(values):
    with pytest.raises(ValueError):
        covariance.sensitivity(*values)


def test_invalid_scene_arrays_or_reference_are_rejected():
    r = reference()
    valid = np.zeros((2, 2, 4, 2))
    for named in (valid[:, :1], valid[:, :, :3], valid[:0], np.full_like(valid, np.nan)):
        with pytest.raises(ValueError):
            covariance.scene_statistics(named, r)
    for bad_r in (np.zeros_like(r), r + 1, r[:, :1], np.full_like(r, np.inf)):
        with pytest.raises(ValueError):
            covariance.scene_statistics(valid, bad_r)
