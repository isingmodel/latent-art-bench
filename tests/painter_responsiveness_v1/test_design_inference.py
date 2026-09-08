"""Prospective factorial checks using synthetic scalars only; no live transport."""

import copy
import json
from collections import Counter, defaultdict

import numpy as np
import pytest

from latent_art_bench.painter_responsiveness_v1.design import (
    ARMS,
    POLARITIES,
    make_schedule,
    validate_schedule,
)
from latent_art_bench.painter_responsiveness_v1.inference import (
    _simulation_statistics,
    analyze_factorial,
    retained_noise,
    simulate_design,
)

TEMPLATES = [f"scene{i}" for i in range(6)]


def synthetic_outcomes(schedule, *, shift=0.0):
    """A shared noisy generic response gives analytically positive covariance.

    The generic response is 10+z, z=(-3,-1,1,3), Var_sample(z)=20/3.
    The two contrasts are -2-z+(j-2.5) and -3-z. Their equal-template
    covariance is (20/3)/24=5/18; template heterogeneity must not inflate it.
    """
    rows = []
    for slot in schedule:
        j = TEMPLATES.index(slot["template_id"])
        z = (-3, -1, 1, 3)[slot["repetition"]]
        response = {"free": 12 + 2 * z, "generic": 10 + z,
                    "monet": 8 + j - 2.5, "cezanne": 7}[slot["arm"]]
        baseline = shift + j * 100 + ARMS.index(slot["arm"]) * 5
        rows.append(dict(request_id=slot["request_id"], status="measured",
                         value=baseline + (response if slot["polarity"] == "vivid" else 0)))
    return rows


def synthetic_noise_rows():
    rows = []
    for painter, multiplier in (("claude_monet", 2), ("paul_cezanne", 3)):
        for condition in ("named", "artist_free"):
            for brief in range(2):
                for repetition, noise in enumerate((-1, 0, 1)):
                    scale = multiplier if condition == "named" else 1
                    rows.append(dict(
                        image_id=f"{painter}:{condition}:{brief}:{repetition}",
                        painter_id=painter, condition=condition, brief_id=f"b{brief}",
                        repetition=repetition, route="flux_2_max", pipeline="primary512",
                        scaled=[0, 0, 100 * brief + scale * noise],
                    ))
    return rows


def test_schedule_has_shared_controls_and_joint_eight_cell_randomization():
    schedule = make_schedule(TEMPLATES, seed=130)
    assert schedule == make_schedule(TEMPLATES, seed=130)
    second = make_schedule(TEMPLATES, seed=131)
    assert schedule != second
    assert {r["request_id"] for r in schedule} == {r["request_id"] for r in second}
    assert len(schedule) == 192
    assert Counter(r["arm"] for r in schedule) == dict.fromkeys(ARMS, 48)
    blocks = defaultdict(list)
    for slot in schedule:
        blocks[slot["block_id"]].append(slot)
    assert len(blocks) == 24
    assert all({(s["arm"], s["polarity"]) for s in b} ==
               {(a, p) for a in ARMS for p in POLARITIES} for b in blocks.values())
    assert len({tuple(s["polarity"] for s in b) for b in blocks.values()}) > 1
    assert validate_schedule(schedule)["repetitions"] == 4


def test_invalid_design_cannot_silently_change_the_finite_target():
    with pytest.raises(ValueError, match="six distinct"):
        make_schedule(TEMPLATES[:-1], seed=2)
    with pytest.raises(ValueError, match="repetitions"):
        make_schedule(TEMPLATES, seed=2, repetitions=1)
    schedule = make_schedule(TEMPLATES, seed=2)
    duplicate = copy.deepcopy(schedule)
    duplicate[0]["request_id"] = duplicate[1]["request_id"]
    with pytest.raises(ValueError, match="duplicate"):
        validate_schedule(duplicate)
    incomplete = copy.deepcopy(schedule)
    incomplete[0]["arm"] = incomplete[1]["arm"]
    incomplete[0]["polarity"] = incomplete[1]["polarity"]
    with pytest.raises(ValueError, match="eight cells"):
        validate_schedule(incomplete)


def test_finite_template_estimates_and_shared_covariance_have_hand_calculated_values():
    schedule = make_schedule(TEMPLATES, seed=20)
    result = analyze_factorial(schedule, synthetic_outcomes(schedule), manipulation_margin=1)
    assert result["status"] == "complete_grid_approximate_inference"
    assert [r["estimate"] for r in result["primary"]] == pytest.approx([-2, -3])
    assert result["primary_covariance"] == pytest.approx(np.full((2, 2), 5 / 18))
    assert [r["welch_df"] for r in result["primary"]] == pytest.approx([18, 18])
    for row in result["primary"]:
        assert row["standard_error"] == pytest.approx(np.sqrt(5 / 18))
        assert row["family_interval"][1] < 0
        assert row["reject_holm"]
        assert row["family_interval"][0] < row["nominal_interval"][0]
    assert [r["estimate"] for r in result["responses"]] == pytest.approx([12, 10, 8, 7])
    assert len(result["cells"]) == 48
    assert len(result["arm_means"]) == 8
    assert result["manipulation_checks"][0]["status"] == "nominal_interval_above_margin"
    shifted = analyze_factorial(schedule, synthetic_outcomes(schedule, shift=500))
    assert shifted["primary"] == result["primary"]
    json.dumps(result, allow_nan=False)


def test_weak_interaction_null_allows_large_arm_and_instruction_main_effects():
    schedule = make_schedule(TEMPLATES, seed=1)
    outcomes = synthetic_outcomes(schedule)
    for slot, outcome in zip(schedule, outcomes):
        if slot["polarity"] == "vivid":
            j = TEMPLATES.index(slot["template_id"])
            if slot["arm"] == "monet":
                outcome["value"] += 2 - (j - 2.5)
            elif slot["arm"] == "cezanne":
                outcome["value"] += 3
    result = analyze_factorial(schedule, outcomes)
    assert [r["estimate"] for r in result["primary"]] == pytest.approx([0, 0])
    assert all(r["p_holm"] == pytest.approx(1) for r in result["primary"])
    assert any("not" in a and "exact" in a for a in result["assumptions"])


def test_one_missing_free_value_withholds_primary_and_never_drops_it_silently():
    schedule = make_schedule(TEMPLATES, seed=5)
    outcomes = synthetic_outcomes(schedule)
    target = next(s for s in schedule if s["arm"] == "free")
    row = next(r for r in outcomes if r["request_id"] == target["request_id"])
    row.update(status="refused", value=None)
    result = analyze_factorial(schedule, outcomes)
    assert result["status"] == "primary_withheld_unavailable_planned_values"
    assert result["primary"] is None
    assert sum(result["complete_blocks_by_template"].values()) == 23
    assert sum(c["measured"] for c in result["availability"]) == 191
    assert result["complete_block_descriptive"]["kappa_equal_template"] is not None
    assert "p_holm" not in json.dumps(result)
    assert "family_interval\"" not in json.dumps(result)
    json.dumps(result, allow_nan=False)


def test_an_entire_missing_template_cannot_be_reweighted_away():
    schedule = make_schedule(TEMPLATES, seed=7)
    retained = {s["request_id"] for s in schedule if s["template_id"] != TEMPLATES[0]}
    outcomes = [r for r in synthetic_outcomes(schedule) if r["request_id"] in retained]
    result = analyze_factorial(schedule, outcomes)
    assert result["primary"] is None
    assert result["complete_block_descriptive"]["kappa_equal_template"] is None
    assert sum(c["statuses"].get("not_recorded", 0) for c in result["availability"]) == 32


@pytest.mark.parametrize("mutation,pattern", [
    (lambda rows: rows.append(dict(rows[0])), "duplicate"),
    (lambda rows: rows[0].update(request_id="unknown"), "unknown"),
    (lambda rows: rows[0].update(value=float("nan")), "finite"),
    (lambda rows: rows[0].update(status="refused"), "unavailable"),
])
def test_outcome_identity_and_availability_are_enforced(mutation, pattern):
    schedule = make_schedule(TEMPLATES, seed=7)
    outcomes = synthetic_outcomes(schedule)
    mutation(outcomes)
    with pytest.raises(ValueError, match=pattern):
        analyze_factorial(schedule, outcomes)


def test_no_observed_variance_does_not_manufacture_certain_inference():
    schedule = make_schedule(TEMPLATES, seed=10)
    outcomes = [dict(request_id=s["request_id"], status="measured",
                     value=1.0 if s["arm"] == "generic" and s["polarity"] == "vivid" else 0.0)
                for s in schedule]
    result = analyze_factorial(schedule, outcomes)
    assert all(r["family_interval"] is None and r["p_holm"] is None
               for r in result["primary"])
    assert all(not r["reject_holm"] for r in result["primary"])


def test_failed_manipulation_and_named_reversal_keep_all_allocated_outputs():
    schedule = make_schedule(TEMPLATES, seed=10)
    outcomes = synthetic_outcomes(schedule)
    for slot, outcome in zip(schedule, outcomes):
        if slot["polarity"] == "vivid" and slot["arm"] in ("free", "monet"):
            outcome["value"] -= 20
    result = analyze_factorial(schedule, outcomes, manipulation_margin=0.25)
    checks = {r["arm"]: r for r in result["manipulation_checks"]}
    assert checks["free"]["status"] == "nominal_interval_not_above_margin"
    assert checks["free"]["point_response_reversed"]
    assert checks["monet"]["point_response_reversed"]
    assert sum(r["measured"] for r in result["availability"]) == 192
    assert sum(result["complete_blocks_by_template"].values()) == 24
    assert result["primary"][0]["estimate"] == pytest.approx(-22)


def test_retained_residuals_keep_arm_variance_and_document_generic_proxy():
    noise = retained_noise(synthetic_noise_rows())
    assert noise["marginal_variances"] == pytest.approx(
        dict(free=1, generic=1, monet=4, cezanne=9))
    assert all(np.mean(pool) == pytest.approx(0) for pool in noise["pools"].values())
    assert noise["pools"]["generic"] == noise["pools"]["free"]
    assert noise["pools"]["generic"] is not noise["pools"]["free"]
    assert any("unvalidated" in a and "proxy" in a for a in noise["assumptions"])
    rows = synthetic_noise_rows()
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError, match="duplicate"):
        retained_noise(rows)


def test_vectorized_simulation_uses_the_same_estimator_and_intervals():
    schedule = make_schedule(TEMPLATES, seed=29)
    outcomes = synthetic_outcomes(schedule)
    result = analyze_factorial(schedule, outcomes)
    z = np.array([-3, -1, 1, 3])
    blocks = np.empty((1, 6, 4, 2))
    for j in range(6):
        blocks[0, j, :, 0] = -2 - z + j - 2.5
        blocks[0, j, :, 1] = -3 - z
    estimate, rejected, halfwidth, valid = _simulation_statistics(blocks, alpha=0.05)
    assert estimate[0] == pytest.approx([r["estimate"] for r in result["primary"]])
    assert valid.all() and rejected.all()
    for i, row in enumerate(result["primary"]):
        assert row["estimate"] - halfwidth[0, i] == pytest.approx(row["family_interval"][0])


def test_simulation_checks_partial_nulls_and_power_without_claiming_a_guarantee():
    noise = retained_noise(synthetic_noise_rows())
    result = simulate_design(noise, seed=919, trials=2000,
                             effects=((0, 0), (-3, -3), (-3, 0)))
    assert result == simulate_design(noise, seed=919, trials=2000,
                                     effects=((0, 0), (-3, -3), (-3, 0)))
    assert result["planned_images"] == 192
    assert len(result["results"]) == 9
    for row in result["results"]:
        assert row["simultaneous_interval_coverage"] > 0.90
        if 0 in row["true_interactions"]:
            assert row["null_endpoint_family_error"] < 0.08
    empirical = [r for r in result["results"] if r["scenario"] == "empirical_proxy"]
    assert empirical[1]["rejection_probability"][0] > empirical[0]["rejection_probability"][0]
    assert empirical[1]["rejection_probability"][1] > empirical[0]["rejection_probability"][1]
    assert "not a perceptually meaningful threshold" in result["scope"]
    json.dumps(result, allow_nan=False)
