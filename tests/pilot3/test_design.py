from __future__ import annotations

import json

import numpy as np
import pytest

from latent_art_bench.io import stable_hash
from latent_art_bench.pilot3.design import (
    _cluster_summary,
    _metric_sensitivity,
    build_pilot3_design_sensitivity,
    exact_sign_flip_resolution,
    request_count,
    simulate_candidate_design,
)

EFFECTS = (
    {
        "name": "low",
        "target_improvement_standardized_effect": 0.10,
        "specificity_standardized_effect": 0.10,
    },
    {
        "name": "high",
        "target_improvement_standardized_effect": 1.00,
        "specificity_standardized_effect": 1.00,
    },
)
VARIANCES = (
    {
        "name": "balanced",
        "artist_variance_share": 0.25,
        "content_block_variance_share": 0.25,
        "artist_content_variance_share": 0.20,
        "residual_variance_share": 0.30,
    },
)
AVAILABILITY = (
    {
        "name": "low_refusal",
        "named_refusal_probability_at_zero": 0.01,
        "control_refusal_probability_at_zero": 0.005,
        "artist_refusal_logit_sd": 0.50,
        "content_refusal_logit_sd": 0.25,
        "refusal_target_artist_effect_correlation": 0.0,
    },
)


def _small_build(**overrides: object) -> dict[str, object]:
    kwargs = {
        "artist_counts": (6,),
        "content_block_counts": (6,),
        "repetition_counts": (2,),
        "min_request_budget": 84,
        "max_request_budget": 84,
        "draws": 128,
        "seed": 1234,
        "effect_scenarios": EFFECTS,
        "variance_scenarios": VARIANCES,
        "availability_scenarios": AVAILABILITY,
    }
    kwargs.update(overrides)
    return build_pilot3_design_sensitivity(**kwargs)


def test_request_count_includes_one_shared_control_per_block_repetition() -> None:
    assert request_count(8, 12, 3) == 324
    assert request_count(8, 16, 3) == 432


def test_exact_sign_flip_resolution_accounts_for_two_co_primary_tests() -> None:
    five = exact_sign_flip_resolution(5)
    six = exact_sign_flip_resolution(6)
    eight = exact_sign_flip_resolution(8)

    assert five["minimum_attainable_one_sided_p"] == 1 / 32
    assert not five["can_ever_pass_strict_bonferroni_threshold"]
    assert six["can_ever_pass_strict_bonferroni_threshold"]
    assert eight["minimum_attainable_one_sided_p"] < six[
        "minimum_attainable_one_sided_p"
    ]
    assert eight["per_estimand_strict_alpha"] == 0.025


def test_build_is_deterministic_json_ready_and_self_hashed() -> None:
    first = _small_build()
    second = _small_build()

    assert first == second
    json.dumps(first, allow_nan=False)
    unsigned = {key: value for key, value in first.items() if key != "result_sha256"}
    assert first["result_sha256"] == stable_hash(unsigned)
    assert first["network_or_image_requests_made"] is False
    assert "not guaranteed power" in first["claim_boundary"]
    assert "availability-selected" in first["claim_boundary"]


def test_candidate_order_does_not_change_candidate_simulation() -> None:
    forward = _small_build(
        artist_counts=(6, 7),
        min_request_budget=84,
        max_request_budget=96,
    )
    reverse = _small_build(
        artist_counts=(7, 6),
        min_request_budget=84,
        max_request_budget=96,
    )

    by_id_forward = {row["design_id"]: row for row in forward["candidate_designs"]}
    by_id_reverse = {row["design_id"]: row for row in reverse["candidate_designs"]}
    assert by_id_forward == by_id_reverse


def test_stronger_effects_cannot_reduce_sensitivity_with_common_draws() -> None:
    result = simulate_candidate_design(
        artist_count=6,
        content_block_count=6,
        repetitions=2,
        draws=512,
        seed=42,
        effect_scenarios=EFFECTS,
        variance_scenarios=VARIANCES,
        availability_scenarios=AVAILABILITY,
    )
    rows = result["scenario_results"][0][
        "conditional_a_vector_proximity_sensitivity"
    ]
    by_effect = {row["effect_scenario"]: row for row in rows}
    for outcome in (
        "target_improvement",
        "specificity_difference_in_differences",
    ):
        low = by_effect["low"][outcome][
            "positive_bonferroni_crossed_cluster_lower_bound"
        ]["estimated_probability"]
        high = by_effect["high"][outcome][
            "positive_bonferroni_crossed_cluster_lower_bound"
        ]["estimated_probability"]
        assert high >= low
    assert by_effect["high"][
        "both_co_primary_endpoints_pass_aggregate_and_reversal_rule"
    ][
        "estimated_probability"
    ] >= by_effect["low"][
        "both_co_primary_endpoints_pass_aggregate_and_reversal_rule"
    ][
        "estimated_probability"
    ]


def test_conditional_point_estimator_weights_artists_equally() -> None:
    # Artist 0 has one usable pair with value 1. Artist 1 has three usable
    # pairs with value 0. Pooling pairs would yield 0.25; artist weighting is 0.5.
    noise = np.asarray([[[[1.0, 9.0, 9.0]], [[0.0, 0.0, 0.0]]]])
    available = np.asarray([[[[True, False, False]], [[True, True, True]]]])

    estimate, _, valid_artists, _, _ = _cluster_summary(noise, available)

    assert estimate.tolist() == [0.5]
    assert valid_artists.tolist() == [2]


def test_conditional_readiness_requires_every_configured_artist() -> None:
    noise = np.zeros((1, 6, 1, 2), dtype=np.float64)
    available = np.ones_like(noise, dtype=bool)
    available[:, 0, :, :] = False
    estimate, standard_error, valid_artists, valid_blocks, artist_means = (
        _cluster_summary(noise, available)
    )

    _, _, summary = _metric_sensitivity(
        observed_estimate=estimate + 1.0,
        conservative_se=standard_error,
        valid_artists=valid_artists,
        valid_blocks=valid_blocks,
        artist_observed_means=artist_means + 1.0,
        scenario_standardized_effect=1.0,
        force_one_artist_reversal=False,
        critical_value=1.96,
        minimum_valid_artists=6,
        minimum_valid_blocks=1,
    )

    assert valid_artists.tolist() == [5]
    assert summary["analysis_ready"]["event_count"] == 0


def test_forced_artist_reversal_is_executed_in_each_draw() -> None:
    support, aggregate, summary = _metric_sensitivity(
        observed_estimate=np.full(1, 0.4),
        conservative_se=np.zeros(1),
        valid_artists=np.asarray([6]),
        valid_blocks=np.asarray([6]),
        artist_observed_means=np.asarray(
            [[-0.4, 0.56, 0.56, 0.56, 0.56, 0.56]]
        ),
        scenario_standardized_effect=0.4,
        force_one_artist_reversal=True,
        critical_value=2.0,
        minimum_valid_artists=6,
        minimum_valid_blocks=6,
    )

    assert aggregate.tolist() == [True]
    assert support.tolist() == [False]
    assert summary["forced_reversal_artist_true_effect"] == -0.4
    assert summary["no_artist_point_estimate_reversal"]["event_count"] == 0


def test_reversal_false_support_is_excluded_from_positive_sensitivity_ranking() -> None:
    effects = (
        {
            "name": "positive",
            "target_improvement_standardized_effect": 0.4,
            "specificity_standardized_effect": 0.3,
            "force_one_artist_reversal": False,
        },
        {
            "name": "reversal",
            "target_improvement_standardized_effect": 0.4,
            "specificity_standardized_effect": 0.3,
            "force_one_artist_reversal": True,
        },
    )
    result = simulate_candidate_design(
        artist_count=6,
        content_block_count=6,
        repetitions=2,
        draws=512,
        seed=2718,
        effect_scenarios=effects,
        variance_scenarios=VARIANCES,
        availability_scenarios=AVAILABILITY,
    )
    rows = {
        row["effect_scenario"]: row
        for row in result["scenario_results"][0][
            "conditional_a_vector_proximity_sensitivity"
        ]
    }
    positive_probability = rows["positive"][
        "both_co_primary_endpoints_pass_aggregate_and_reversal_rule"
    ]["estimated_probability"]
    reversal_false_support = rows["reversal"][
        "false_support_under_forced_artist_reversal"
    ]["estimated_probability"]

    assert rows["positive"]["scenario_role"] == "positive_effect_sensitivity"
    assert rows["reversal"]["scenario_role"] == "artist_reversal_false_support_stress"
    assert rows["reversal"]["excluded_from_positive_effect_sensitivity_ranking"] is True
    assert result["summary"][
        "minimum_joint_co_primary_sensitivity_across_scenarios"
    ] == positive_probability
    assert result["summary"][
        "maximum_false_support_under_forced_artist_reversal_stress"
    ] == reversal_false_support


def test_zero_effect_calibration_reports_endpoint_and_familywise_events_separately() -> None:
    result = simulate_candidate_design(
        artist_count=6,
        content_block_count=6,
        repetitions=2,
        draws=512,
        seed=314,
        effect_scenarios=EFFECTS,
        variance_scenarios=VARIANCES,
        availability_scenarios=AVAILABILITY,
    )
    calibration = result["scenario_results"][0]["zero_effect_null_calibration"]
    target = calibration["target_improvement_false_positive"]["event_count"]
    specificity = calibration[
        "specificity_difference_in_differences_false_positive"
    ]["event_count"]
    any_endpoint = calibration["any_endpoint_false_positive_fwer"]["event_count"]
    both = calibration["both_co_primary_endpoints_false_positive"]["event_count"]

    assert any_endpoint >= max(target, specificity)
    assert both <= min(target, specificity)
    assert calibration["any_endpoint_false_positive_fwer"]["estimated_probability"] <= 0.05
    assert calibration["excluded_from_recommendation_ranking"] is True
    assert result["summary"]["null_calibration_excluded_from_ranking_score"] is True


def test_higher_refusal_probability_reduces_availability_with_common_draws() -> None:
    availability = (
        {**AVAILABILITY[0], "name": "lower", "named_refusal_probability_at_zero": 0.01},
        {**AVAILABILITY[0], "name": "higher", "named_refusal_probability_at_zero": 0.20},
    )
    result = simulate_candidate_design(
        artist_count=6,
        content_block_count=6,
        repetitions=2,
        draws=512,
        seed=99,
        effect_scenarios=EFFECTS[:1],
        variance_scenarios=VARIANCES,
        availability_scenarios=availability,
    )
    by_availability = {
        row["availability_scenario"]: row["availability"]
        for row in result["scenario_results"]
    }
    assert by_availability["higher"]["mean_complete_pair_availability"] < by_availability[
        "lower"
    ]["mean_complete_pair_availability"]
    assert by_availability["higher"]["mean_request_availability"] < by_availability[
        "lower"
    ]["mean_request_availability"]
    assert by_availability["higher"][
        "mean_minimum_artist_complete_pair_availability"
    ] < by_availability["lower"]["mean_minimum_artist_complete_pair_availability"]
    assert by_availability["higher"][
        "mean_artist_availability_disparity"
    ] > by_availability["lower"]["mean_artist_availability_disparity"]
    assert (
        by_availability["higher"][
            "all_artists_raw_complete_pair_availability_at_or_above_floor"
        ]["estimated_probability"]
        <= by_availability["lower"][
            "all_artists_raw_complete_pair_availability_at_or_above_floor"
        ]["estimated_probability"]
    )
    assert by_availability["lower"]["valid_clustered_availability_lower_bound_implemented"] is False


def test_budget_filter_emits_diagnostics_but_no_false_recommendation() -> None:
    result = _small_build(
        artist_counts=(6, 8),
        content_block_counts=(6, 8),
        repetition_counts=(2, 3),
        min_request_budget=100,
        max_request_budget=216,
    )
    candidates = result["candidate_designs"]
    assert candidates
    assert all(100 <= row["request_count"] <= 216 for row in candidates)
    assert result["recommended_feasible_designs"] == []
    assert result["design_decision"] == "NO_DESIGN_SELECTED_CRITERIA_UNRESOLVED"
    assert result["prospective_acceptance_criteria_frozen"] is False
    assert result["scenario_relative_ranked_designs"]
    assert all(
        "not a powered" in row["diagnostic_scope"]
        for row in result["scenario_relative_ranked_designs"]
    )


@pytest.mark.parametrize(
    ("function", "kwargs", "match"),
    [
        (request_count, {"artist_count": 0, "content_block_count": 2, "repetitions": 2}, ">= 1"),
        (exact_sign_flip_resolution, {"cluster_count": 0}, ">= 1"),
        (_small_build, {"draws": 0}, "draws"),
        (_small_build, {"seed": -1}, "seed"),
        (_small_build, {"min_request_budget": 100, "max_request_budget": 99}, "must not exceed"),
        (_small_build, {"minimum_pair_availability": 0.0}, "availability"),
        (
            _small_build,
            {"maximum_artist_availability_disparity": 1.1},
            "disparity",
        ),
        (
            _small_build,
            {
                "effect_scenarios": (
                    {
                        "name": "bad",
                        "target_improvement_standardized_effect": 0.0,
                        "specificity_standardized_effect": 0.2,
                    },
                )
            },
            "positive",
        ),
        (
            _small_build,
            {
                "effect_scenarios": (
                    {
                        "name": "only_reversal",
                        "target_improvement_standardized_effect": 0.4,
                        "specificity_standardized_effect": 0.3,
                        "force_one_artist_reversal": True,
                    },
                )
            },
            "positive-effect sensitivity",
        ),
        (
            _small_build,
            {
                "variance_scenarios": (
                    {
                        "name": "bad",
                        "artist_variance_share": 0.2,
                        "content_block_variance_share": 0.2,
                        "artist_content_variance_share": 0.2,
                        "residual_variance_share": 0.2,
                    },
                )
            },
            "sum to 1",
        ),
        (
            _small_build,
            {
                "availability_scenarios": (
                    {
                        **AVAILABILITY[0],
                        "named_refusal_probability_at_zero": 1.0,
                    },
                )
            },
            "strictly",
        ),
    ],
)
def test_invalid_inputs_fail_closed(
    function: object,
    kwargs: dict[str, object],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        function(**kwargs)


def test_empty_budget_search_fails_instead_of_making_a_recommendation() -> None:
    with pytest.raises(ValueError, match="no candidate design"):
        _small_build(min_request_budget=1_000, max_request_budget=2_000)
