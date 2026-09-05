"""Independent weighted/allocation oracles and the complete synthetic qualification contract."""

import itertools
import json

import numpy as np
import pytest

from latent_art_bench.painter_prompt_supplement_v1 import validation


@pytest.fixture(scope="module")
def oracles():
    return validation.validate_oracles()


def test_independent_oracles_pass_and_cover_every_mandatory_case(oracles):
    assert oracles["overall"] == "PASS"
    assert {row["id"] for row in oracles["checks"]} == set(validation.ORACLE_IDS)
    assert len(oracles["checks"]) == len(validation.ORACLE_IDS)
    rows = {row["id"]: row for row in oracles["checks"]}
    assert rows["weighted_energy_swaps"]["assignments"] == 128
    allocation = rows["conditional_triplet_allocations"]
    assert allocation["conditioning_strata"] == 162
    assert allocation["full_triplet_allocations"] == 2592
    assert allocation["distinct_weight_support_patterns"] == 4
    assert allocation["maximum_conditional_cdf_minus_alpha"] <= 1e-12
    assert oracles["empirical_outcomes_used"] is False
    json.dumps(oracles, allow_nan=False)


def test_triplet_oracle_detects_a_wrong_core_coefficient(monkeypatch):
    from latent_art_bench.painter_prompt_supplement_v1 import statistics

    correct = statistics.paired_energy_contributions
    monkeypatch.setattr(
        statistics, "paired_energy_contributions", lambda *args: correct(*args) * 1.01
    )
    result = validation.validate_oracles()
    assert result["overall"] == "FAIL"
    assert any(
        not row["passed"] for row in result["checks"] if row["id"] == "weighted_energy_swaps"
    )


@pytest.mark.parametrize(
    "case,pairs",
    [
        ("full64_drift", 64),
        ("one63_large_contribution", 63),
        ("severe40", 40),
        ("unavailable_template", 64),
    ],
)
def test_synthetic_weights_are_template_balanced_without_renormalization(case, pairs):
    plan = validation._case(case)
    counts, weights = plan["counts"], plan["template_weights"]
    assert int(counts.sum()) == pairs
    assert len(weights) == pairs
    assert weights.sum() == pytest.approx(1)
    templates = np.repeat(np.arange(16), counts)
    for template in range(16):
        assert weights[templates == template].sum() == pytest.approx(1 / 16)
    if case == "unavailable_template":
        assert plan["unavailable_endpoints"] == [0, 1, 2]
        assert plan["unavailable_template_counts"][0] == 0


@pytest.mark.parametrize("values", [(1, 2, 4, 6), (0, 0), (3, 3, 4, 4)])
def test_finite_sign_shortcut_matches_exhaustive_tail(values):
    statistics = np.abs(
        [np.dot(signs, values) for signs in itertools.product((-1, 1), repeat=len(values))]
    )
    expected = [np.mean(statistics >= threshold) for threshold in range(sum(values) + 1)]
    np.testing.assert_allclose(validation._exact_tail(values), expected, atol=1e-15, rtol=0)


def test_simulation_retains_all_48_hypotheses_and_separates_false_joint_null_example():
    result = validation.simulate(seed=123, trials=30)
    assert result == validation.simulate(seed=123, trials=30)
    expected = {(c, d) for c in validation.CASE_IDS for d in validation.DEPENDENCE_IDS}
    assert len(result["null_cells"]) == 8
    assert {(r["case"], r["dependence"]) for r in result["null_cells"]} == expected
    assert all(r["family_size"] == 48 for r in result["null_cells"])
    assert all(
        r["tested_endpoints"] == 45
        for r in result["null_cells"]
        if r["case"] == "unavailable_template"
    )
    assert result["permutation_draws"] == 99999
    assert result["uses_empirical_outcomes_for_tuning"] is False
    stress = result["adversarial_example"]
    assert stress["feature_potential_effect"] == 0
    assert stress["feature_only_sharp_null_holds"] is True
    assert stress["joint_null_holds"] is False
    assert stress["mask_changes_after_counterfactual_swap"] == 48
    assert stress["rejects_joint_null_at_05"]
    assert stress["observed_common_pairs"] == 40
    json.dumps(result, allow_nan=False)


def test_missing_template_is_ineligible_before_any_weight_normalization():
    assert validation._template_weights(np.array([0, 0, 1]), 3) is None


@pytest.mark.parametrize("seed,trials", [(True, 2000), (-1, 2000), (123, 0), (123, 2.5)])
def test_simulation_rejects_invalid_settings(seed, trials):
    with pytest.raises(ValueError):
        validation.simulate(seed, trials)
