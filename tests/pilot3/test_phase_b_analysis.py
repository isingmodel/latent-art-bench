from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional

import pytest

from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.pilot3.analysis import (
    PRIMARY_OUTCOMES,
    _analyze_phase_b_core_for_verified_inputs,
    analyze_conditional_proximity,
    analyze_phase_b,
    build_pair_outcomes,
    validate_runtime_bindings,
    validate_schedule,
    validate_terminal_accounting,
)
from latent_art_bench.pilot3.design_freeze import EXPECTED_ARTIST_IDS

ROOT = Path(__file__).resolve().parents[2]


def _contract() -> dict[str, object]:
    return read_json(ROOT / "reports/pilot_3/evidence/analysis_contract.json")


def _schedule() -> list[dict[str, object]]:
    return read_jsonl(ROOT / "data/manifests/pilot_3/schedule.jsonl")


def _runtime_bindings(contract: dict[str, object]) -> dict[str, object]:
    internal = contract["internal_bindings"]
    placeholder = "0" * 64
    return {
        "corpus_selection_file_sha256": placeholder,
        "a_vector_protocol_file_sha256": placeholder,
        "a_vector_external_validation_file_sha256": placeholder,
        "transport_qualification_file_sha256": placeholder,
        "generation_gate_file_sha256": placeholder,
        "generation_completion_file_sha256": placeholder,
        "phase_b_design_file_sha256": internal["phase_b_design"]["file_sha256"],
        "prompt_manifest_file_sha256": internal["prompt_manifest"]["file_sha256"],
        "schedule_manifest_file_sha256": internal["schedule_manifest"]["file_sha256"],
        "analysis_contract_semantic_sha256": contract["semantic_sha256"],
        "phase_a_status": "pass",
        "transport_status": "pass",
        "generation_gate_status": "open",
        "generation_completion_status": "complete",
        "requested_model_label": "gpt-image-2",
        "transport": "~/dev/openai-oauth",
    }


def _terminal_rows(
    schedule: list[dict[str, object]],
    overrides: Optional[Dict[str, str]] = None,
) -> list[dict[str, object]]:
    overrides = overrides or {}
    return [
        {
            "request_id": row["request_id"],
            "terminal_category": overrides.get(str(row["request_id"]), "usable_image"),
        }
        for row in schedule
    ]


def _distance_rows(
    schedule: list[dict[str, object]],
    terminal_rows: list[dict[str, object]],
    *,
    specificity: float = 3.0,
) -> list[dict[str, object]]:
    category = {row["request_id"]: row["terminal_category"] for row in terminal_rows}
    rows = []
    for request in schedule:
        request_id = request["request_id"]
        if category[request_id] != "usable_image":
            continue
        distances = {artist_id: 10.0 for artist_id in EXPECTED_ARTIST_IDS}
        if request["condition"] == "named_artist":
            target = request["target_artist_id"]
            neighbor = request["neighbor_artist_id"]
            distances[target] = 8.0
            distances[neighbor] = 8.0 + specificity
        rows.append({"request_id": request_id, "distances_by_artist": distances})
    return rows


def _run(
    *,
    overrides: Optional[Dict[str, str]] = None,
    specificity: float = 3.0,
) -> dict[str, object]:
    contract = _contract()
    schedule = _schedule()
    terminals = _terminal_rows(schedule, overrides)
    return _analyze_phase_b_core_for_verified_inputs(
        schedule_rows=schedule,
        terminal_rows=terminals,
        distance_rows=_distance_rows(schedule, terminals, specificity=specificity),
        analysis_contract=contract,
        runtime_bindings=_runtime_bindings(contract),
        tau_by_outcome={
            "target_improvement": 1.0,
            "specificity_difference_in_differences": 1.0,
        },
    )


def test_analysis_fails_closed_without_every_runtime_binding() -> None:
    contract = _contract()
    bindings = _runtime_bindings(contract)
    del bindings["transport_qualification_file_sha256"]

    with pytest.raises(RuntimeError, match="caller-supplied hashes/statuses"):
        validate_runtime_bindings(bindings, contract)


def test_public_analysis_entrypoint_rejects_even_plausible_self_attestation() -> None:
    contract = _contract()
    schedule = _schedule()
    terminals = _terminal_rows(schedule)

    with pytest.raises(RuntimeError, match="caller-supplied hashes/statuses"):
        analyze_phase_b(
            schedule_rows=schedule,
            terminal_rows=terminals,
            distance_rows=_distance_rows(schedule, terminals),
            analysis_contract=contract,
            runtime_bindings=_runtime_bindings(contract),
            tau_by_outcome={
                "target_improvement": 1.0,
                "specificity_difference_in_differences": 1.0,
            },
        )


def test_schedule_and_terminal_accounting_require_exact_closure() -> None:
    schedule = validate_schedule(_schedule())
    terminals = _terminal_rows(schedule)
    by_request, counts = validate_terminal_accounting(schedule, terminals)

    assert len(by_request) == 320
    assert counts["usable_image"] == 320
    with pytest.raises(ValueError, match="incomplete"):
        validate_terminal_accounting(schedule, terminals[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        validate_terminal_accounting(schedule, terminals + [terminals[0]])


def test_pair_formulas_have_registered_positive_orientation() -> None:
    schedule = validate_schedule(_schedule())
    terminals = _terminal_rows(schedule)
    terminal_by_request, _ = validate_terminal_accounting(schedule, terminals)
    distances = {
        row["request_id"]: row["distances_by_artist"]
        for row in _distance_rows(schedule, terminals, specificity=3.0)
    }
    pairs = build_pair_outcomes(schedule, terminal_by_request, distances)

    assert len(pairs) == 256
    assert all(pair["target_improvement"] == 2.0 for pair in pairs)
    assert all(pair["specificity_difference_in_differences"] == 3.0 for pair in pairs)


def test_all_usable_positive_grid_is_supported() -> None:
    result = _run()

    assert result["status"] == "complete"
    assert result["terminal_accounting"]["complete"] is True
    assert result["availability"]["passes"] is True
    assert result["conditional_a_vector_proximity"]["both_co_primary_pass"] is True
    assert (
        result["conditional_a_vector_proximity"]["artist_harm_family"]["any_harm_established"]
        is False
    )
    for outcome in PRIMARY_OUTCOMES:
        assert (
            result["finite_schedule_missingness"]["outcomes"][outcome][
                "positive_worst_case_lower_bound"
            ]
            is True
        )
    assert result["decision"]["status"] == "supported"


def test_artist_dependent_unavailability_fails_availability_and_is_unsupported() -> None:
    schedule = _schedule()
    overrides = {
        str(row["request_id"]): "policy_refusal"
        for row in schedule
        if row["target_artist_id"] == "paul_cezanne"
    }
    result = _run(overrides=overrides)

    availability = result["availability"]
    assert availability["passes"] is False
    assert availability["per_artist"]["paul_cezanne"]["usable_pairs"] == 0
    assert availability["component_decisions"]["all_per_artist_lower_bounds_pass"] is False
    assert availability["component_decisions"]["artist_disparity_upper_bound_passes"] is False
    assert result["decision"]["status"] == "unsupported"


def test_failed_preflight_global_stop_is_complete_but_unsupported() -> None:
    schedule = _schedule()
    overrides = {
        str(row["request_id"]): (
            "policy_refusal" if index == 0 else "not_sent_global_stop"
        )
        for index, row in enumerate(schedule)
    }
    result = _run(overrides=overrides)

    assert result["status"] == "complete"
    assert result["terminal_accounting"]["complete"] is True
    counts = result["terminal_accounting"]["category_counts"]
    assert counts["not_sent_global_stop"] == 319
    assert counts["policy_refusal"] == 1
    assert counts["usable_image"] == 0
    assert result["availability"]["usable_pairs"] == 0
    assert result["availability"]["passes"] is False
    assert result["decision"]["status"] == "unsupported"


def _pair_grid_for_weighting() -> list[dict[str, object]]:
    rows = []
    for artist_index, artist_id in enumerate(EXPECTED_ARTIST_IDS):
        for block_rank in range(1, 17):
            repetitions = 1 if artist_index == 0 else 4
            for repetition in range(1, repetitions + 1):
                value = 4.0 if artist_index == 0 else 0.0
                rows.append(
                    {
                        "artist_id": artist_id,
                        "content_block_rank": block_rank,
                        "repetition": repetition,
                        "usable_pair": True,
                        "target_improvement": value,
                        "specificity_difference_in_differences": value,
                    }
                )
    return rows


def test_conditional_estimator_equal_weights_artists_and_blocks_not_pairs() -> None:
    contract = _contract()
    result = analyze_conditional_proximity(
        _pair_grid_for_weighting(),
        contract["conditional_proximity"],
        contract["artist_reversal_harm"],
    )

    for outcome in PRIMARY_OUTCOMES:
        assert result["outcomes"][outcome]["estimate"] == 1.0


def test_negative_point_alone_is_not_artist_harm_but_precise_negative_is() -> None:
    contract = _contract()
    rows = _pair_grid_for_weighting()
    # Give Sisley a slightly negative but noisy block pattern: its upper bound remains positive.
    for row in rows:
        if row["artist_id"] == "alfred_sisley":
            row["target_improvement"] = -1.0 if row["content_block_rank"] <= 9 else 1.0
    noisy = analyze_conditional_proximity(
        rows,
        contract["conditional_proximity"],
        contract["artist_reversal_harm"],
    )
    sisley = noisy["outcomes"]["target_improvement"]["per_artist"]["alfred_sisley"]
    assert sisley["estimate"] < 0
    assert sisley["harm_established"] is False

    precise_rows = deepcopy(rows)
    for row in precise_rows:
        if row["artist_id"] == "alfred_sisley":
            row["target_improvement"] = -0.25
    precise = analyze_conditional_proximity(
        precise_rows,
        contract["conditional_proximity"],
        contract["artist_reversal_harm"],
    )
    sisley = precise["outcomes"]["target_improvement"]["per_artist"]["alfred_sisley"]
    assert sisley["harm_established"] is True
    assert precise["artist_harm_family"]["any_harm_established"] is True


def test_one_favorable_co_primary_is_terminal_mixed_not_supported() -> None:
    result = _run(specificity=0.0)

    conditional = result["conditional_a_vector_proximity"]["outcomes"]
    assert conditional["target_improvement"]["passes"] is True
    assert conditional["specificity_difference_in_differences"]["passes"] is False
    assert result["decision"]["status"] == "mixed"


def test_phase_a_tau_must_be_positive_and_finite() -> None:
    contract = _contract()
    schedule = _schedule()
    terminals = _terminal_rows(schedule)

    with pytest.raises(RuntimeError, match="tau"):
        _analyze_phase_b_core_for_verified_inputs(
            schedule_rows=schedule,
            terminal_rows=terminals,
            distance_rows=_distance_rows(schedule, terminals),
            analysis_contract=contract,
            runtime_bindings=_runtime_bindings(contract),
            tau_by_outcome={
                "target_improvement": 0.0,
                "specificity_difference_in_differences": 1.0,
            },
        )
