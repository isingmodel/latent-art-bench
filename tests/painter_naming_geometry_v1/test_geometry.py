"""Synthetic geometry checks; no retained vectors, pixels, transport or fitting to references."""

import copy
import json

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_naming_geometry_v1 import geometry as g


def example():
    return np.array([[-3., 0.], [1., 2.], [5., -4.]]), np.array([0.2, 0.3, 0.5])


@pytest.mark.parametrize("scale", [0.25, 1.0, 2.5])
def test_weighted_known_shift_and_positive_scale_recovered_on_unseen_queries(scale):
    free, weights = example()
    shift = np.array([4.0, -7.0])
    named = scale * free + shift
    before = free.copy(), named.copy(), weights.copy()
    fitted = g.fit_map(free, named, weights)
    query = np.array([[20.0, -12.0], [-8.0, 31.0]])
    assert fitted["scale"] == pytest.approx(scale)
    assert fitted["named_trace"] == pytest.approx(scale ** 2 * fitted["free_trace"])
    assert g.apply(query, fitted) == pytest.approx(scale * query + shift)
    translated = g.apply(query, fitted, "translation")
    assert translated == pytest.approx(query + np.array(fitted["named_mean"])
                                       - np.array(fitted["free_mean"]))
    identity = g.apply(query, fitted, "identity")
    np.testing.assert_array_equal(identity, query)
    assert not np.shares_memory(identity, query)
    for actual, original in zip((free, named, weights), before):
        np.testing.assert_array_equal(actual, original)
    assert json.loads(json.dumps(fitted, allow_nan=False)) == fitted


def test_moments_use_weights_and_are_not_a_pairwise_regression():
    free = np.array([[0.0], [2.0], [8.0]])
    named = np.array([[3.0], [11.0], [5.0]])
    weights = np.array([0.25, 0.25, 0.5])
    fitted = g.fit_map(free, named, weights)
    assert fitted["free_mean"] == pytest.approx([4.5])
    assert fitted["named_mean"] == pytest.approx([6.0])
    assert fitted["free_trace"] == pytest.approx(12.75)
    assert fitted["named_trace"] == pytest.approx(9.0)
    # Permuting equal-weight named rows changes pairwise correspondence, not moments.
    permuted = g.fit_map(free, named[[1, 0, 2]], weights)
    assert permuted == fitted


def test_reference_evaluation_cannot_change_fitted_map_or_future_predictions():
    free, weights = example()
    named = 0.7 * free + [1.0, 3.0]
    fitted = g.fit_map(free, named, weights)
    frozen = copy.deepcopy(fitted)
    transformed = g.apply(free, fitted)
    nearby = np.array([[0.0, 1.0], [1.0, 1.0], [2.0, 0.0], [3.0, 0.0]])
    remote = nearby + 100
    for reference in (nearby, remote):
        g.energy_terms(reference, transformed, np.full(4, 0.25), weights)
        g.occupancy(reference, transformed)
    assert fitted == frozen == g.fit_map(free, named, weights)
    np.testing.assert_array_equal(g.apply(free, fitted), transformed)
    with pytest.raises(TypeError):
        g.fit_map(free, named, weights, reference=nearby)


def test_weighted_v_energy_matches_hand_calculation_symmetry_and_identity():
    reference = [[0.0], [2.0]]
    generated = [[1.0], [3.0]]
    wx, wy = [0.5, 0.5], [0.25, 0.75]
    actual = g.energy_terms(reference, generated, wx, wy)
    assert actual == pytest.approx(dict(energy=1.75, cross_twice=3.5,
                                       reference_within=1.0, generated_within=0.75))
    reversed_ = g.energy_terms(generated, reference, wy, wx)
    assert reversed_["energy"] == pytest.approx(actual["energy"])
    assert reversed_["reference_within"] == pytest.approx(actual["generated_within"])
    assert g.energy_terms(reference, reference, wx, wx)["energy"] == pytest.approx(0.0)


def test_reference_self_term_cancels_in_named_minus_benchmark_difference():
    free, weights = example()
    named = free * [0.3, 1.2] + [2.0, -1.0]
    reference = [[-4., 0.], [2., 3.], [6., -3.]]
    transformed = g.apply(free, g.fit_map(free, named, weights))
    actual = g.energy_terms(reference, named, weights, weights)
    benchmark = g.energy_terms(reference, transformed, weights, weights)
    assert actual["reference_within"] == benchmark["reference_within"]
    assert actual["energy"] - benchmark["energy"] == pytest.approx(
        actual["cross_twice"] - benchmark["cross_twice"]
        - actual["generated_within"] + benchmark["generated_within"]
    )


def test_global_positive_similarity_preserves_nearest_centroid_retrieval():
    # Three scenes with separated centers; each query is held out of all centroids.
    scenes = np.array([
        [[-8., -2.], [-6., -2.], [-7., -1.]],
        [[0., 5.], [1., 6.], [-1., 6.]],
        [[9., -3.], [8., -4.], [10., -4.]],
    ])
    train = scenes[:, :2].reshape(-1, 2)
    fitted = g.fit_map(train, 0.37 * train + [51.0, -18.0], np.full(6, 1 / 6))
    centroids, queries = scenes[:, :2].mean(axis=1), scenes[:, 2]
    baseline = cdist(queries, centroids)
    transformed = cdist(g.apply(queries, fitted), g.apply(centroids, fitted))
    assert transformed == pytest.approx(0.37 * baseline)
    np.testing.assert_array_equal(transformed.argmin(axis=1), baseline.argmin(axis=1))


def test_fixed_anchor_occupancy_excludes_self_retains_boundaries_and_query_counts():
    reference = np.array([[0.0], [2.0], [5.0], [9.0]])
    before = reference.copy()
    result = g.occupancy(reference, [[-9.0], [16.0]])
    assert result == dict(coverage=0.5, radii=[9.0, 7.0, 5.0, 9.0],
                         hit=[True, False, False, True], hit_count=[1, 0, 0, 1],
                         n_reference=4, n_queries=2, k=3)
    # Duplicate queries retain allocation counts but do not create extra occupied balls.
    duplicate = g.occupancy(reference, [[-9.0], [16.0], [-9.0], [16.0]])
    assert duplicate["coverage"] == result["coverage"]
    assert duplicate["n_queries"] == 4
    assert duplicate["hit_count"] == [2, 0, 0, 2]
    np.testing.assert_array_equal(reference, before)
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_occupancy_records_concentration_without_claiming_distribution_matching():
    # Four widely spread corners: one central query hits every k=3 reference ball.
    reference = [[-1., -1.], [-1., 1.], [1., -1.], [1., 1.]]
    result = g.occupancy(reference, [[0.0, 0.0]])
    assert result["coverage"] == 1.0
    assert g.energy_terms(reference, [[0.0, 0.0]], [0.25] * 4, [1.0])["energy"] > 0


@pytest.mark.parametrize("weights", [
    [0.2, 0.3], [0.0, 0.5, 0.5], [-0.1, 0.5, 0.6], [0.2, 0.3, 0.6],
    [float("nan"), 0.3, 0.7], [float("inf"), 0.3, 0.7], [[0.2, 0.3, 0.5]],
])
def test_invalid_weights_fail_in_fitting_and_energy(weights):
    free, good = example()
    with pytest.raises(ValueError, match="weights"):
        g.fit_map(free, free + 1, weights)
    with pytest.raises(ValueError, match="weights"):
        g.energy_terms(free, free, good, weights)


@pytest.mark.parametrize("invalid", [[], [[]], [1.0, 2.0], [[float("nan")]],
                                     [[float("inf")]], np.ones((2, 2, 2))])
def test_invalid_matrices_fail_in_all_entry_points(invalid):
    free, weights = example()
    fitted = g.fit_map(free, free + 1, weights)
    for operation in (
        lambda: g.fit_map(invalid, free, weights),
        lambda: g.apply(invalid, fitted),
        lambda: g.energy_terms(invalid, free, weights, weights),
        lambda: g.occupancy(free, invalid, k=1),
    ):
        with pytest.raises(ValueError, match="matrix"):
            operation()


@pytest.mark.parametrize("free,named", [
    ([[1.0], [1.0]], [[0.0], [2.0]]),
    ([[0.0], [2.0]], [[1.0], [1.0]]),
    ([[-1e308], [1e308]], [[0.0], [2.0]]),
])
def test_zero_or_nonfinite_traces_fail_explicitly(free, named):
    with pytest.raises(ValueError, match="traces"):
        g.fit_map(free, named, [0.5, 0.5])


def test_dimension_mismatch_unknown_kind_and_invalid_map_fail():
    free, weights = example()
    fitted = g.fit_map(free, free + 1, weights)
    with pytest.raises(ValueError, match="matching shape"):
        g.fit_map(free, free[:, :1], weights)
    with pytest.raises(ValueError, match="dimensions"):
        g.energy_terms(free, free[:, :1], weights, weights)
    with pytest.raises(ValueError, match="matching finite means"):
        g.apply(free[:, :1], fitted)
    with pytest.raises(ValueError, match="unknown"):
        g.apply(free, fitted, "optimize_reference")
    for invalid in ({}, dict(fitted, scale=0), dict(fitted, scale=float("nan")),
                    dict(fitted, free_trace=0), dict(fitted, named_mean=[1.0])):
        with pytest.raises(ValueError, match="map"):
            g.apply(free, invalid)


@pytest.mark.parametrize("k", [0, -1, 4, 5, 1.5, True, float("nan")])
def test_invalid_neighborhood_support_fails(k):
    with pytest.raises(ValueError, match="k must"):
        g.occupancy([[0.0], [1.0], [2.0], [3.0]], [[1.0]], k=k)


def test_nonfinite_distance_or_transformed_output_fails():
    with pytest.raises(ValueError, match="distances"):
        g.energy_terms([[-1e308]], [[1e308]], [1.0], [1.0])
    free, weights = example()
    fitted = g.fit_map(free, 3.0 * free, weights)
    with pytest.raises(ValueError, match="nonfinite evaluation"):
        g.apply([[1e308, -1e308]], fitted)
