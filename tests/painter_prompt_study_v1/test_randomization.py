"""Exact numerical oracles and synthetic-only checks of the small-study test."""

import itertools

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_prompt_study_v1.randomization import (
    _exact_absolute_tail,
    endpoint_seed,
    holm,
    paired_energy_contributions,
    randomization_pvalue,
    simulate_randomization,
)


def _energy(reference, generated):
    return (
        2 * cdist(reference, generated).mean()
        - cdist(reference, reference).mean()
        - cdist(generated, generated).mean()
    )


def test_linear_coefficients_equal_brute_energy_under_every_complementary_swap():
    rng = np.random.default_rng(21)
    reference, before, after = (
        rng.normal(size=(9, 4)),
        rng.normal(size=(5, 4)),
        rng.normal(size=(5, 4)),
    )
    coefficients = paired_energy_contributions(reference, before, after)
    statistics = []
    for signs in itertools.product((-1, 1), repeat=5):
        swap = np.array(signs) < 0
        a, b = before.copy(), after.copy()
        a[swap], b[swap] = after[swap], before[swap]
        actual = _energy(reference, b) - _energy(reference, a)
        assert actual == pytest.approx(np.dot(signs, coefficients), abs=1e-12)
        statistics.append(actual)
    observed = _energy(reference, after) - _energy(reference, before)
    expected_p = np.mean(np.abs(statistics) >= abs(observed) - 1e-12)
    result = randomization_pvalue(coefficients, seed=42)
    assert result["estimate"] == pytest.approx(observed)
    assert result["raw_p"] == expected_p


def test_exact_r1_enumerates_full_group_including_ties_and_identity():
    row = randomization_pvalue(np.ones(16), seed=23)
    assert row["permutations"] == 65536
    assert row["exceedances"] == 2
    assert row["raw_p"] == 2 / 65536
    assert row["seed"] is None
    assert "equal energy" in row["null"]
    zero = randomization_pvalue(np.zeros(16), seed=23)
    assert zero["raw_p"] == 1
    assert zero["zero_contributions"]


def test_monte_carlo_includes_identity_never_reports_zero_and_reproduces():
    values = np.ones(64)
    result = randomization_pvalue(values, seed=23, draws=9999)
    assert result == randomization_pvalue(values, seed=23, draws=9999)
    assert result["raw_p"] == 1 / 10000
    assert result["permutations"] == 9999
    assert result["method"] == "monte_carlo_paired_randomization"
    assert endpoint_seed(42, 0) != endpoint_seed(42, 1)


@pytest.mark.parametrize("weights", [[1, 2, 3, 0], [1, 1, 1, 1], [0, 0]])
def test_exact_convolution_shortcut_equals_actual_group_enumeration(weights):
    values = np.array(weights)
    statistics = np.abs(
        [np.dot(signs, values) for signs in itertools.product((-1, 1), repeat=len(values))]
    )
    expected = np.array([np.mean(statistics >= cutoff) for cutoff in range(sum(weights) + 1)])
    np.testing.assert_allclose(_exact_absolute_tail(values), expected, rtol=0, atol=1e-15)


def test_actual_monte_carlo_engine_with_random_null_assignments_is_not_anticonservative():
    rng = np.random.default_rng(20260908)
    weights = np.tile([1.0, 2.0, 3.0, 4.0], 8)
    rejected = 0
    # Bounded engine smoke test, separate from retained exact-tail qualification.
    for trial in range(300):
        values = weights * rng.choice([-1, 1], size=32)
        row = randomization_pvalue(values, seed=endpoint_seed(100, trial), draws=1999)
        rejected += row["raw_p"] <= 0.05
    assert rejected <= 27


def test_holm_adjusts_complete_family_and_preserves_original_order():
    np.testing.assert_allclose(holm([0.04, 0.001, 0.02, 0.01]), [0.04, 0.004, 0.04, 0.03])
    assert np.all(holm(np.repeat(0.002, 48)) > 0.05)
    assert np.all(holm(np.repeat(0.001, 48)) <= 0.05)


@pytest.mark.parametrize("values", [[], [np.nan], [-0.1], [1.1], [[0.5]]])
def test_holm_rejects_invalid_inputs(values):
    with pytest.raises(ValueError):
        holm(values)


def test_simulation_records_whole_inventory_and_excludes_invalid_stress_from_null():
    result = simulate_randomization(seed=123, trials=12)
    assert len(result["null_cells"]) == 24
    assert len(result["power_diagnostics"]) == 9
    assert len(result["invalid_persistent_sign_stress"]) == 3
    assert all(
        row["family_rejection_rate"] == 1 for row in result["invalid_persistent_sign_stress"]
    )
    assert result["uses_empirical_outcomes_for_tuning"] is False
