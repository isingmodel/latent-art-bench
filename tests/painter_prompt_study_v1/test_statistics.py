"""Synthetic identities and adversarial accounting for prospective block statistics."""

import numpy as np
import pytest
from scipy.spatial.distance import cdist
from scipy.stats import t

from latent_art_bench.painter_prompt_study_v1 import calibration, statistics


def test_kernel_expectation_matches_exact_generator_mixture_energy():
    reference = np.array([[0.0], [2.0], [4.0]])
    blocks = np.array([[[0.0], [1.0]], [[3.0], [5.0]], [[1.0], [2.0]]])
    probabilities = np.array([0.2, 0.3, 0.5])
    kernel = statistics.energy_kernel(reference, blocks)
    flat, weights = blocks.reshape(-1, 1), np.repeat(probabilities / 2, 2)
    truth = (2 * (cdist(reference, flat).mean(axis=0) @ weights)
             - cdist(reference, reference).mean() - weights @ cdist(flat, flat) @ weights)
    assert probabilities @ kernel @ probabilities == pytest.approx(truth)
    assert np.allclose(kernel, kernel.T)


def test_pair_contributions_preserve_pairing_and_negative_values():
    values = np.array([[[0., -3., 8., 9.], [-3., 0., 7., 8.],
                        [8., 7., 0., 2.], [9., 8., 2., 0.]]])
    assert statistics.pair_contributions(values).tolist() == [[-3.0], [2.0]]
    assert statistics.pair_contributions(values * 2 - values).tolist() == [[-3.0], [2.0]]
    with pytest.raises(ValueError, match="even"):
        statistics.pair_contributions(values[:, :3, :3])


def test_jackknife_matches_literal_leave_one_complete_block_estimates():
    rng = np.random.default_rng(42)
    raw = rng.normal(size=(2, 8, 8))
    values = raw + raw.transpose(0, 2, 1)

    def u(kernel):
        n = kernel.shape[-1]
        return (kernel.sum() - np.trace(kernel)) / (n * (n - 1))

    expected = []
    for index in range(8):
        keep = np.arange(8) != index
        expected.append([8 * u(k) - 7 * u(k[keep][:, keep]) for k in values])
    actual = statistics.jackknife_pseudovalues(values)
    assert actual == pytest.approx(np.array(expected))
    assert actual.mean(axis=0) == pytest.approx(np.array([u(k) for k in values]))


def test_t_intervals_use_all_endpoints_and_keep_degeneracy_unresolved():
    values = np.column_stack((np.arange(10.0), np.zeros(10)))
    result = statistics.bonferroni_t(values, family_size=48)
    row = result["endpoints"][0]
    half = t.ppf(1 - .05 / 96, 9) * np.std(values[:, 0], ddof=1) / np.sqrt(10)
    assert row["lower"] == pytest.approx(4.5 - half)
    assert result["endpoints"][1]["lower"] is None
    assert result["endpoints"][1]["status"] == "inconclusive_zero_sample_variance"
    with pytest.raises(ValueError, match="multiplicity"):
        statistics.bonferroni_t(values, family_size=1)


@pytest.mark.parametrize("method", ["paired_t", "jackknife_t"])
def test_fast_synthetic_moments_match_materialized_repeated_states(method):
    rng = np.random.default_rng(14)
    raw = rng.normal(size=(3, 4, 4))
    kernels = raw + raw.transpose(0, 2, 1)
    indices = np.array([[0, 0, 1, 1, 2, 3], [3, 2, 0, 2, 3, 1]])
    point, errors = calibration._trial_moments(kernels, indices, method)
    for trial, row in enumerate(indices):
        materialized = kernels[:, row][:, :, row]
        result = statistics.infer(materialized, method=method)
        assert point[trial] == pytest.approx([r["estimate"] for r in result["endpoints"]])
        assert errors[trial] == pytest.approx(
            [r["standard_error"] for r in result["endpoints"]])


def test_synthetic_inventory_has_known_null_and_preserves_multiplicity():
    population = calibration.synthetic_kernels("null", states=4)
    assert population["contrasts"].shape == (48, 4, 4)
    assert population["distances"].shape == (72, 4, 4)
    assert np.max(abs(population["distances"].mean(axis=(1, 2)))) < 1e-12
    assert np.max(abs(population["contrasts"].mean(axis=(1, 2)))) < 1e-12


def test_simulation_is_deterministic_and_never_labels_planning_as_guaranteed():
    first = calibration.simulate(trials=3, pair_counts=(2,), states=4)
    second = calibration.simulate(trials=3, pair_counts=(2,), states=4)
    assert first == second
    assert len(first["scenarios"]) == 4 * 2 * 2
    assert first["requests_per_full_repetition"] == 480
    assert "No automatic" in first["selection"]
    for row in first["scenarios"]:
        assert row["requests"] == 1920
        assert 0 <= row["complete_inventory_coverage"] <= 1
        assert len(row["endpoint_truth_and_precision"]) == row["family_size"]


def test_normal_planning_power_and_precision_improve_with_pair_count():
    rows = calibration.normal_precision_plan(pair_counts=(10, 100), family_sizes=(48,),
                                             effects=(0.8,))
    assert rows[0]["normal_theory_marginal_power"] < rows[1]["normal_theory_marginal_power"]
    assert rows[0]["half_width_over_observed_pair_sd"] > rows[1]["half_width_over_observed_pair_sd"]
    assert rows[1]["requests"] == 96000


@pytest.mark.parametrize("method", ["paired_t", "jackknife_t"])
def test_independent_condition_moments_subtract_aligned_block_observations(method):
    population = calibration.synthetic_kernels("shift", states=4)
    groups = {(r["alias"], r["painter"], r["method"])
              for r in population["distance_labels"]}
    rng = np.random.default_rng(202)
    indices = {group: rng.integers(0, 4, size=(2, 6)) for group in sorted(groups)}
    point, error = calibration._independent_moments(population, "contrasts", indices, method)
    for trial in range(2):
        materialized = []
        for left, right in population["contrast_indices"]:
            matrices = []
            for column in (left, right):
                label = population["distance_labels"][column]
                group = label["alias"], label["painter"], label["method"]
                chosen = indices[group][trial]
                matrices.append(population["distances"][column][chosen][:, chosen])
            materialized.append(matrices[0] - matrices[1])
        result = statistics.infer(np.array(materialized), method=method)
        assert point[trial] == pytest.approx([r["estimate"] for r in result["endpoints"]])
        assert error[trial] == pytest.approx([r["standard_error"] for r in result["endpoints"]])


def test_normal_power_under_zero_effect_equals_the_adjusted_type_one_rate():
    row = calibration.normal_precision_plan(pair_counts=(10,), family_sizes=(48,), effects=(0,))[0]
    assert row["normal_theory_marginal_power"] == pytest.approx(.05 / 48, abs=1e-10)
