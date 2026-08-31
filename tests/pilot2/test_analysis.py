from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from latent_art_bench.pilot2.analysis import (
    PRIMARY_ESTIMANDS,
    REQUESTED_LABELS,
    Pilot2GridSpec,
    analyze_requested_label_effects,
    exact_block_sign_flip_p_value,
    grid_spec_from_config,
    holm_adjust,
)
from latent_art_bench.pilot2.config import Pilot2Config
from latent_art_bench.schemas import PromptRecord

from .test_analysis_helpers import (
    PROJECTED_MANIFEST_SHA256,
    synthetic_generated_observations,
    synthetic_grid,
    synthetic_held_references,
    synthetic_result,
)


def test_grid_is_exactly_320_cells_and_256_pairs() -> None:
    grid = synthetic_grid()
    assert grid.expected_cell_count == 320
    assert grid.expected_pair_count == 256
    with pytest.raises(ValidationError, match="eight unique content"):
        Pilot2GridSpec(content_ids=[f"content-{index}" for index in range(7)])
    with pytest.raises(ValidationError, match="two requested labels"):
        Pilot2GridSpec(
            content_ids=[f"content-{index}" for index in range(8)],
            requested_labels=["gpt-image-2", "gpt-image-1"],
        )


def test_exact_sign_flip_and_holm_cover_the_fixed_four_test_family() -> None:
    assert exact_block_sign_flip_p_value([1.0] * 8) == pytest.approx(1 / 256)
    assert exact_block_sign_flip_p_value([-1.0] * 8) == pytest.approx(1.0)
    adjusted = holm_adjust(
        {
            "a": 1 / 256,
            "b": 1 / 256,
            "c": 1 / 256,
            "d": 1 / 256,
        }
    )
    assert all(value == pytest.approx(4 / 256) for value in adjusted.values())


def test_primary_estimands_use_raw_centroid_deltas_and_source_domains() -> None:
    result = synthetic_result(draws=100)
    assert result.analysis_scope == "requested_label_operational_effect"
    assert result.executed_model_claims is False
    assert result.cross_label_superiority_estimand is False
    assert result.scientific_completion.status == "complete"
    assert result.itt.complete_feature_pairs == 256
    assert len(result.primary_estimates) == 4
    assert len(result.secondary_artist_estimates) == 16

    for row in result.primary_estimates:
        # The frozen formula is a raw Euclidean distance-to-centroid delta.
        # Any target-neighbor normalization would not equal this value.
        assert row.estimate == pytest.approx(10.0)
        assert row.source_sign_diagnostics == {
            "aic": pytest.approx(9.8),
            "nga": pytest.approx(9.8),
        }
        assert set(row.content_block_estimates) == set(result.grid.content_ids)
        assert all(
            value == pytest.approx(10.0)
            for value in row.content_block_estimates.values()
        )
        assert row.exact_sign_flip_p_value == pytest.approx(1 / 256)
        assert row.holm_adjusted_p_value == pytest.approx(4 / 256)
        assert row.familywise_lower_confidence_bound is not None
        assert row.familywise_lower_confidence_bound > 0
        assert row.familywise_lower_confidence_bound_positive is True
        assert row.hypothesis_supported is True

    assert result.simultaneous_lower_bound_method == (
        "bonferroni_one_sided_four_primary_hypotheses"
    )
    assert "reference_separation" not in result.estimand_definitions
    assert set(result.hypothesis_support_by_requested_label) == set(REQUESTED_LABELS)
    assert all(result.hypothesis_support_by_requested_label.values())
    assert {row.estimand for row in result.primary_estimates} == set(PRIMARY_ESTIMANDS)
    assert all(row.inferential_claim is False for row in result.secondary_artist_estimates)
    assert all(row.complete_pairs == 32 for row in result.secondary_artist_estimates)
    for label in REQUESTED_LABELS:
        for estimand in PRIMARY_ESTIMANDS:
            values = [
                row.estimate
                for row in result.secondary_artist_estimates
                if row.requested_model_label == label and row.estimand == estimand
            ]
            assert sum(value for value in values if value is not None) / 4 == pytest.approx(10.0)


def test_bootstrap_and_result_hash_are_deterministic() -> None:
    first = synthetic_result(draws=80)
    second = synthetic_result(draws=80)
    assert first == second
    assert first.bootstrap_distribution_sha256 == second.bootstrap_distribution_sha256
    assert first.result_sha256 == second.result_sha256


def test_refusal_completes_assignment_ledger_but_cannot_support_hypothesis() -> None:
    observations = synthetic_generated_observations()
    refused = observations[0]
    refused["outcome"] = "refused"
    refused["vector"] = None
    result = analyze_requested_label_effects(
        synthetic_grid(),
        synthetic_held_references(),
        observations,
        bootstrap_draws=20,
        protocol_preconditions_met=True,
        projected_input_manifest_sha256=PROJECTED_MANIFEST_SHA256,
    )
    assert result.scientific_completion.status == "complete"
    assert result.scientific_completion.exact_assignment_grid_accounted_for is True
    assert result.scientific_completion.feature_estimand_grid_complete is False
    assert result.itt.refused_cells == 1
    # One shared control refusal makes all four target pairs unavailable.
    assert result.itt.refused_pairs == 4
    by_label = {
        label: [
            row for row in result.primary_estimates
            if row.requested_model_label == label
        ]
        for label in REQUESTED_LABELS
    }
    assert all(
        row.test_status == "not_tested_incomplete_feature_grid"
        and row.holm_adjusted_p_value == 1.0
        and not row.hypothesis_supported
        for row in by_label["gpt-image-1"]
    )
    assert all(
        row.test_status == "tested" and row.hypothesis_supported
        for row in by_label["gpt-image-2"]
    )


def test_missing_assignment_and_success_without_feature_are_incomplete() -> None:
    complete = synthetic_generated_observations()
    missing_result = analyze_requested_label_effects(
        synthetic_grid(),
        synthetic_held_references(),
        complete[:-1],
        bootstrap_draws=20,
        protocol_preconditions_met=True,
        projected_input_manifest_sha256=PROJECTED_MANIFEST_SHA256,
    )
    assert missing_result.scientific_completion.status == "incomplete"
    assert missing_result.itt.missing_cells == 1

    no_feature = deepcopy(complete)
    no_feature[0]["vector"] = None
    feature_result = analyze_requested_label_effects(
        synthetic_grid(),
        synthetic_held_references(),
        no_feature,
        bootstrap_draws=20,
        protocol_preconditions_met=True,
        projected_input_manifest_sha256=PROJECTED_MANIFEST_SHA256,
    )
    assert feature_result.scientific_completion.status == "incomplete"
    assert feature_result.itt.succeeded_without_feature_cells == 1


def test_real_reference_cell_counts_are_not_silently_reweighted() -> None:
    references = synthetic_held_references()
    references.pop()
    with pytest.raises(ValueError, match="exactly 2 held-out works"):
        analyze_requested_label_effects(
            synthetic_grid(),
            references,
            synthetic_generated_observations(),
            bootstrap_draws=5,
            protocol_preconditions_met=True,
            projected_input_manifest_sha256=PROJECTED_MANIFEST_SHA256,
        )


def test_prompt_manifest_first_occurrence_order_is_preserved() -> None:
    content_order = ["zeta", "eta", "theta", "iota", "kappa", "lambda", "mu", "nu"]
    prompts = []
    for content in content_order:
        prompts.append(
            PromptRecord(
                prompt_id=f"{content}-control",
                content_id=content,
                template_id="control",
                prompt=f"Control {content}",
                artist_free_control=True,
                test_only=True,
            )
        )
        for artist in sorted(synthetic_grid().artist_ids):
            prompts.append(
                PromptRecord(
                    prompt_id=f"{content}-{artist}",
                    content_id=content,
                    template_id="named",
                    prompt=f"Named {content} {artist}",
                    target_artist_id=artist,
                    target_artist_name=artist,
                    test_only=True,
                )
            )
    grid = grid_spec_from_config(Pilot2Config(), prompt_records=prompts)
    assert grid.content_ids == content_order
