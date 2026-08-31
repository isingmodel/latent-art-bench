"""Frozen finite-schedule analysis for the Pilot-3 Phase-B estimation design.

The analysis separates request availability from A-vector proximity conditional
on a usable named/control pair.  Missing images never receive vectors.  The
only full-schedule sensitivity result is the deterministic tanh bound over the
256 frozen pairs; it is not a claim about future prompts or generator draws.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from latent_art_bench.io import stable_hash
from latent_art_bench.pilot3.design_freeze import (
    ANALYSIS_CONTRACT_SCHEMA,
    EXPECTED_ARTIST_IDS,
    EXPECTED_CONTENT_BLOCK_COUNT,
    EXPECTED_PAIR_COUNT,
    EXPECTED_REPETITIONS,
    EXPECTED_REQUESTED_LABEL,
    EXPECTED_SCHEDULE_COUNT,
    EXPECTED_TRANSPORT,
    SCHEDULE_SCHEMA,
)

PRIMARY_OUTCOMES = (
    "target_improvement",
    "specificity_difference_in_differences",
)
TERMINAL_CATEGORIES = (
    "usable_image",
    "policy_refusal",
    "nonretryable_client_response",
    "malformed_or_ineligible_success",
    "retry_cap_technical_failure",
    "indeterminate_after_interruption",
    "not_sent_global_stop",
)
_SHA256_CHARACTERS = frozenset("0123456789abcdef")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value).issubset(_SHA256_CHARACTERS)


def _mapping(value: object, *, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return dict(value)


def _verify_seal(
    value: Mapping[str, Any],
    *,
    field: str,
    label: str,
) -> None:
    payload = dict(value)
    recorded = payload.pop(field, None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise ValueError(f"{label} has a stale or invalid {field}")


def validate_runtime_bindings(
    bindings: Mapping[str, Any],
    analysis_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    """Reject caller-self-attested hashes as an execution authority.

    Phase B is still prospectively closed.  A later P3-T14 file-backed loader
    must re-hash the canonical artifacts, validate their self-seals/statuses,
    extract the two tau values from the verified P3-T07 artifact, bind the
    exact schedule bytes, and derive terminal/distance rows from verified
    post-generation evidence.  Free strings that merely look like SHA-256
    values cannot open analysis.
    """

    _mapping(bindings, label="runtime bindings")
    _mapping(analysis_contract, label="analysis contract")
    raise RuntimeError(
        "analysis is closed: caller-supplied hashes/statuses are not authority; "
        "use the canonical P3-T14 file-backed verifier after Freeze B"
    )


def validate_schedule(schedule_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Validate exact schedule cardinality, identities, pairing, and row hashes."""

    rows = [_mapping(row, label="schedule row") for row in schedule_rows]
    if len(rows) != EXPECTED_SCHEDULE_COUNT:
        raise ValueError("analysis requires exactly 320 scheduled requests")
    request_ids = [row.get("request_id") for row in rows]
    if len(set(request_ids)) != len(request_ids):
        raise ValueError("scheduled request identifiers must be unique")
    if [row.get("sequence") for row in rows] != list(range(1, EXPECTED_SCHEDULE_COUNT + 1)):
        raise ValueError("schedule sequence must be the frozen contiguous order")

    by_cell: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    artist_ids = set(EXPECTED_ARTIST_IDS)
    for row in rows:
        if row.get("schema_version") != SCHEDULE_SCHEMA:
            raise ValueError("unexpected Pilot-3 schedule schema")
        _verify_seal(row, field="schedule_row_sha256", label="schedule row")
        if row.get("requested_model_label") != EXPECTED_REQUESTED_LABEL:
            raise ValueError("schedule contains a non-frozen requested label")
        if row.get("transport") != EXPECTED_TRANSPORT:
            raise ValueError("schedule contains a non-frozen transport")
        block_rank = row.get("content_block_rank")
        repetition = row.get("repetition")
        if (
            isinstance(block_rank, bool)
            or not isinstance(block_rank, int)
            or not 1 <= block_rank <= EXPECTED_CONTENT_BLOCK_COUNT
        ):
            raise ValueError("invalid content-block rank")
        if (
            isinstance(repetition, bool)
            or not isinstance(repetition, int)
            or not 1 <= repetition <= EXPECTED_REPETITIONS
        ):
            raise ValueError("invalid repetition")
        condition = row.get("condition")
        artist_id = row.get("target_artist_id")
        if condition == "artist_free_control":
            if artist_id is not None or row.get("paired_control_request_id") is not None:
                raise ValueError("shared controls cannot target or pair to an artist")
        elif condition == "named_artist":
            if artist_id not in artist_ids:
                raise ValueError("named schedule row targets an artist outside the roster")
            if not isinstance(row.get("paired_control_request_id"), str):
                raise ValueError("named schedule rows require a paired control")
        else:
            raise ValueError("unknown schedule condition")
        by_cell[(str(row["content_block_id"]), repetition)].append(row)

    if len(by_cell) != EXPECTED_CONTENT_BLOCK_COUNT * EXPECTED_REPETITIONS:
        raise ValueError("schedule does not contain every content-block/repetition cell")
    for cell_rows in by_cell.values():
        controls = [row for row in cell_rows if row["condition"] == "artist_free_control"]
        named = [row for row in cell_rows if row["condition"] == "named_artist"]
        if len(controls) != 1 or len(named) != len(EXPECTED_ARTIST_IDS):
            raise ValueError("every cell requires one shared control and four named requests")
        control_id = controls[0]["request_id"]
        if {row["target_artist_id"] for row in named} != artist_ids:
            raise ValueError("every cell must contain the complete finite artist roster")
        if any(row["paired_control_request_id"] != control_id for row in named):
            raise ValueError("named requests must bind the shared within-cell control")
    return rows


def validate_terminal_accounting(
    schedule_rows: Sequence[Mapping[str, Any]],
    terminal_rows: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
    """Require exactly one frozen terminal category for every logical request."""

    scheduled_ids = {str(row["request_id"]) for row in schedule_rows}
    terminals: Dict[str, Dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for raw in terminal_rows:
        row = _mapping(raw, label="terminal row")
        request_id = row.get("request_id")
        category = row.get("terminal_category")
        if request_id not in scheduled_ids:
            raise ValueError(f"terminal row is not in the frozen schedule: {request_id}")
        if request_id in terminals:
            raise ValueError(f"duplicate terminal row: {request_id}")
        if category not in TERMINAL_CATEGORIES:
            raise ValueError(f"unknown terminal category: {category}")
        terminals[str(request_id)] = row
        counts[str(category)] += 1
    missing = sorted(scheduled_ids - set(terminals))
    if missing:
        raise ValueError(f"terminal accounting is incomplete; first missing request: {missing[0]}")
    return terminals, {name: counts.get(name, 0) for name in TERMINAL_CATEGORIES}


def validate_distance_rows(
    terminal_by_request: Mapping[str, Mapping[str, Any]],
    distance_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Require distances for every usable request and for no unavailable request."""

    expected_ids = {
        request_id
        for request_id, row in terminal_by_request.items()
        if row["terminal_category"] == "usable_image"
    }
    observed: Dict[str, Dict[str, float]] = {}
    for raw in distance_rows:
        row = _mapping(raw, label="distance row")
        request_id = row.get("request_id")
        if request_id not in expected_ids:
            raise ValueError(f"distance row does not correspond to a usable request: {request_id}")
        if request_id in observed:
            raise ValueError(f"duplicate distance row: {request_id}")
        raw_distances = _mapping(row.get("distances_by_artist"), label="distances_by_artist")
        if set(raw_distances) != set(EXPECTED_ARTIST_IDS):
            raise ValueError("every usable request requires distances to all frozen artists")
        distances: Dict[str, float] = {}
        for artist_id, value in raw_distances.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("A-vector distances must be numeric")
            normalized = float(value)
            if not math.isfinite(normalized) or normalized < 0:
                raise ValueError("A-vector distances must be finite and non-negative")
            distances[artist_id] = normalized
        observed[str(request_id)] = distances
    if set(observed) != expected_ids:
        missing = sorted(expected_ids - set(observed))
        raise ValueError(f"usable request lacks frozen distances: {missing[0]}")
    return observed


def build_pair_outcomes(
    schedule_rows: Sequence[Mapping[str, Any]],
    terminal_by_request: Mapping[str, Mapping[str, Any]],
    distances_by_request: Mapping[str, Mapping[str, float]],
) -> List[Dict[str, Any]]:
    """Build all 256 named/control pair outcomes without imputing unavailable cells."""

    pairs: List[Dict[str, Any]] = []
    for named in schedule_rows:
        if named["condition"] != "named_artist":
            continue
        named_id = str(named["request_id"])
        control_id = str(named["paired_control_request_id"])
        target = str(named["target_artist_id"])
        neighbor = str(named["neighbor_artist_id"])
        named_usable = terminal_by_request[named_id]["terminal_category"] == "usable_image"
        control_usable = terminal_by_request[control_id]["terminal_category"] == "usable_image"
        pair: Dict[str, Any] = {
            "pair_id": f"{named_id}__paired__{control_id}",
            "content_block_id": named["content_block_id"],
            "content_block_rank": named["content_block_rank"],
            "repetition": named["repetition"],
            "artist_id": target,
            "neighbor_artist_id": neighbor,
            "named_request_id": named_id,
            "control_request_id": control_id,
            "named_terminal_category": terminal_by_request[named_id]["terminal_category"],
            "control_terminal_category": terminal_by_request[control_id]["terminal_category"],
            "usable_pair": named_usable and control_usable,
            "target_improvement": None,
            "specificity_difference_in_differences": None,
        }
        if pair["usable_pair"]:
            named_distances = distances_by_request[named_id]
            control_distances = distances_by_request[control_id]
            pair["target_improvement"] = control_distances[target] - named_distances[target]
            pair["specificity_difference_in_differences"] = (
                named_distances[neighbor]
                - named_distances[target]
                - control_distances[neighbor]
                + control_distances[target]
            )
        pairs.append(pair)
    if len(pairs) != EXPECTED_PAIR_COUNT:
        raise AssertionError("pair builder did not emit exactly 256 pairs")
    return pairs


def _mean_standard_error(values: np.ndarray) -> Tuple[float, float]:
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError("interval input must contain at least two finite values")
    mean = float(values.mean())
    standard_error = float(values.std(ddof=1) / math.sqrt(values.size))
    return mean, standard_error


def analyze_availability(
    pair_rows: Sequence[Mapping[str, Any]],
    availability_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    """Apply the frozen 17-member simultaneous block-clustered availability family."""

    artist_index = {artist_id: index for index, artist_id in enumerate(EXPECTED_ARTIST_IDS)}
    values = np.zeros(
        (len(EXPECTED_ARTIST_IDS), EXPECTED_CONTENT_BLOCK_COUNT, EXPECTED_REPETITIONS),
        dtype=np.float64,
    )
    seen = np.zeros_like(values, dtype=bool)
    for row in pair_rows:
        index = (
            artist_index[str(row["artist_id"])],
            int(row["content_block_rank"]) - 1,
            int(row["repetition"]) - 1,
        )
        if seen[index]:
            raise ValueError("duplicate named/control pair identity")
        seen[index] = True
        values[index] = 1.0 if row["usable_pair"] else 0.0
    if not seen.all():
        raise ValueError("pair grid is incomplete")

    artist_block = values.mean(axis=2)
    critical = float(availability_contract["one_sided_student_t_critical_value"])
    aggregate_mean, aggregate_se = _mean_standard_error(artist_block.mean(axis=0))
    aggregate_lower = max(0.0, aggregate_mean - critical * aggregate_se)

    artist_results: Dict[str, Dict[str, Any]] = {}
    artist_means: List[float] = []
    artist_lowers: List[float] = []
    for artist_id, index in artist_index.items():
        mean, standard_error = _mean_standard_error(artist_block[index])
        lower = max(0.0, mean - critical * standard_error)
        artist_means.append(mean)
        artist_lowers.append(lower)
        artist_results[artist_id] = {
            "assigned_pairs": EXPECTED_CONTENT_BLOCK_COUNT * EXPECTED_REPETITIONS,
            "usable_pairs": int(values[index].sum()),
            "estimate": mean,
            "standard_error_across_content_blocks": standard_error,
            "simultaneous_one_sided_lower_bound": lower,
            "threshold": float(availability_contract["per_artist_lower_bound_minimum"]),
            "passes": lower >= float(availability_contract["per_artist_lower_bound_minimum"]),
        }

    ordered_contrasts: List[Dict[str, Any]] = []
    disparity_upper = 0.0
    for left_index, left_artist in enumerate(EXPECTED_ARTIST_IDS):
        for right_index, right_artist in enumerate(EXPECTED_ARTIST_IDS):
            if left_index == right_index:
                continue
            mean, standard_error = _mean_standard_error(
                artist_block[left_index] - artist_block[right_index]
            )
            upper = min(1.0, mean + critical * standard_error)
            disparity_upper = max(disparity_upper, upper)
            ordered_contrasts.append(
                {
                    "left_artist_id": left_artist,
                    "right_artist_id": right_artist,
                    "difference": mean,
                    "standard_error_across_content_blocks": standard_error,
                    "simultaneous_one_sided_upper_bound": upper,
                }
            )

    aggregate_pass = aggregate_lower >= float(
        availability_contract["aggregate_lower_bound_minimum"]
    )
    artist_pass = all(result["passes"] for result in artist_results.values())
    every_artist_has_usable_pair = all(value > 0 for value in values.sum(axis=(1, 2)))
    disparity_pass = disparity_upper <= float(
        availability_contract["artist_disparity_upper_bound_maximum"]
    )
    return {
        "estimand": "artist-equally-weighted matched-pair availability",
        "assigned_pairs": EXPECTED_PAIR_COUNT,
        "usable_pairs": int(values.sum()),
        "estimate": aggregate_mean,
        "standard_error_across_content_blocks": aggregate_se,
        "simultaneous_one_sided_lower_bound": aggregate_lower,
        "aggregate_threshold": float(availability_contract["aggregate_lower_bound_minimum"]),
        "per_artist": artist_results,
        "observed_artist_disparity": max(artist_means) - min(artist_means),
        "simultaneous_artist_disparity_upper_bound": disparity_upper,
        "artist_disparity_threshold": float(
            availability_contract["artist_disparity_upper_bound_maximum"]
        ),
        "ordered_artist_contrasts": ordered_contrasts,
        "simultaneous_family": {
            "familywise_alpha": availability_contract["familywise_alpha"],
            "family_size": availability_contract["family_size"],
            "critical_value": critical,
            "method": availability_contract["simultaneous_method"],
        },
        "component_decisions": {
            "aggregate_lower_bound_passes": aggregate_pass,
            "all_per_artist_lower_bounds_pass": artist_pass,
            "artist_disparity_upper_bound_passes": disparity_pass,
            "every_artist_has_at_least_one_usable_pair": every_artist_has_usable_pair,
        },
        "passes": bool(
            aggregate_pass and artist_pass and disparity_pass and every_artist_has_usable_pair
        ),
    }


def _conditional_matrix(
    pair_rows: Sequence[Mapping[str, Any]],
    outcome: str,
) -> Tuple[np.ndarray, np.ndarray]:
    artist_index = {artist_id: index for index, artist_id in enumerate(EXPECTED_ARTIST_IDS)}
    cell_values: Dict[Tuple[int, int], List[float]] = defaultdict(list)
    for row in pair_rows:
        if not row["usable_pair"]:
            continue
        value = row[outcome]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("usable pairs require numeric conditional outcomes")
        normalized = float(value)
        if not math.isfinite(normalized):
            raise ValueError("conditional outcomes must be finite")
        cell_values[
            (artist_index[str(row["artist_id"])], int(row["content_block_rank"]) - 1)
        ].append(normalized)

    matrix = np.full(
        (len(EXPECTED_ARTIST_IDS), EXPECTED_CONTENT_BLOCK_COUNT),
        np.nan,
        dtype=np.float64,
    )
    usable_repetitions = np.zeros_like(matrix, dtype=np.int64)
    for (artist_index_value, block_index), values in cell_values.items():
        matrix[artist_index_value, block_index] = float(np.mean(values))
        usable_repetitions[artist_index_value, block_index] = len(values)
    return matrix, usable_repetitions


def analyze_conditional_proximity(
    pair_rows: Sequence[Mapping[str, Any]],
    conditional_contract: Mapping[str, Any],
    harm_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    """Analyze the two conditional co-primaries with frozen equal cell weights."""

    critical = float(conditional_contract["one_sided_student_t_critical_value"])
    harm_critical = float(harm_contract["one_sided_student_t_critical_value"])
    outcome_results: Dict[str, Dict[str, Any]] = {}
    any_harm = False
    all_cells_ready = True
    for outcome in PRIMARY_OUTCOMES:
        matrix, usable_repetitions = _conditional_matrix(pair_rows, outcome)
        ready = bool(np.isfinite(matrix).all())
        all_cells_ready = all_cells_ready and ready
        if not ready:
            outcome_results[outcome] = {
                "analysis_ready": False,
                "missing_artist_content_cells": int(np.isnan(matrix).sum()),
                "estimate": None,
                "crossed_standard_error": None,
                "bonferroni_one_sided_lower_bound": None,
                "passes": False,
                "per_artist": {},
            }
            continue

        artist_means = matrix.mean(axis=1)
        block_means = matrix.mean(axis=0)
        estimate = float(matrix.mean())
        artist_se = float(artist_means.std(ddof=1) / math.sqrt(len(EXPECTED_ARTIST_IDS)))
        block_se = float(block_means.std(ddof=1) / math.sqrt(EXPECTED_CONTENT_BLOCK_COUNT))
        crossed_se = math.sqrt(artist_se**2 + block_se**2)
        lower = estimate - critical * crossed_se
        per_artist: Dict[str, Dict[str, Any]] = {}
        for index, artist_id in enumerate(EXPECTED_ARTIST_IDS):
            mean, standard_error = _mean_standard_error(matrix[index])
            upper = mean + harm_critical * standard_error
            harm = upper < 0.0
            any_harm = any_harm or harm
            per_artist[artist_id] = {
                "estimate": mean,
                "standard_error_across_content_blocks": standard_error,
                "simultaneous_one_sided_upper_bound": upper,
                "harm_established": harm,
                "usable_repetitions_by_content_block": usable_repetitions[index].tolist(),
            }
        outcome_results[outcome] = {
            "analysis_ready": True,
            "missing_artist_content_cells": 0,
            "estimate": estimate,
            "artist_marginal_standard_error": artist_se,
            "content_block_marginal_standard_error": block_se,
            "crossed_standard_error": crossed_se,
            "bonferroni_one_sided_lower_bound": lower,
            "critical_value": critical,
            "test_statistic": estimate / crossed_se if crossed_se > 0 else None,
            "test_rule": "bonferroni_one_sided_lower_bound_strictly_above_zero",
            "passes": lower > 0.0,
            "per_artist": per_artist,
        }
    return {
        "conditioning": "usable named/control pairs only",
        "equal_artist_and_content_block_weighting": True,
        "analysis_ready": all_cells_ready,
        "outcomes": outcome_results,
        "co_primary_family": {
            "familywise_alpha": conditional_contract["familywise_alpha"],
            "family_size": conditional_contract["family_size"],
            "one_sided_per_endpoint_alpha": conditional_contract["one_sided_per_endpoint_alpha"],
            "critical_value": critical,
        },
        "artist_harm_family": {
            "familywise_alpha": harm_contract["familywise_alpha"],
            "family_size": harm_contract["family_size"],
            "critical_value": harm_critical,
            "harm_rule": harm_contract["harm_rule"],
            "any_harm_established": any_harm,
        },
        "both_co_primary_pass": bool(
            all_cells_ready
            and all(outcome_results[outcome]["passes"] for outcome in PRIMARY_OUTCOMES)
        ),
    }


def analyze_finite_schedule_missingness(
    pair_rows: Sequence[Mapping[str, Any]],
    tau_by_outcome: Mapping[str, Any],
) -> Dict[str, Any]:
    """Compute deterministic worst/best tanh bounds over exactly 256 assignments."""

    tau: Dict[str, float] = {}
    for outcome in PRIMARY_OUTCOMES:
        value = tau_by_outcome.get(outcome)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError(f"Phase-A tau is missing for {outcome}")
        normalized = float(value)
        if not math.isfinite(normalized) or normalized <= 0:
            raise RuntimeError(f"Phase-A tau must be finite and positive for {outcome}")
        tau[outcome] = normalized

    weight = 1.0 / EXPECTED_PAIR_COUNT
    results: Dict[str, Dict[str, Any]] = {}
    for outcome in PRIMARY_OUTCOMES:
        observed_weighted_sum = 0.0
        observed_count = 0
        for row in pair_rows:
            if not row["usable_pair"]:
                continue
            observed_count += 1
            observed_weighted_sum += weight * math.tanh(float(row[outcome]) / tau[outcome])
        missing_count = EXPECTED_PAIR_COUNT - observed_count
        missing_weight = weight * missing_count
        lower = observed_weighted_sum - missing_weight
        upper = observed_weighted_sum + missing_weight
        results[outcome] = {
            "tau": tau[outcome],
            "assigned_pairs": EXPECTED_PAIR_COUNT,
            "observed_usable_pairs": observed_count,
            "unavailable_pairs": missing_count,
            "cell_weight": weight,
            "observed_weighted_sum": observed_weighted_sum,
            "worst_case_lower_bound": lower,
            "best_case_upper_bound": upper,
            "positive_worst_case_lower_bound": lower > 0.0,
        }
    return {
        "scope": "realized_256_pair_finite_assignment_schedule_only",
        "stochastic_generator_or_future_prompt_claim": False,
        "imputation_used": False,
        "outcomes": results,
    }


def _terminal_decision(
    availability: Mapping[str, Any],
    conditional: Mapping[str, Any],
    missingness: Mapping[str, Any],
) -> Dict[str, Any]:
    outcome_passes = {
        outcome: bool(conditional["outcomes"][outcome]["passes"]) for outcome in PRIMARY_OUTCOMES
    }
    both_missingness_robust = all(
        missingness["outcomes"][outcome]["positive_worst_case_lower_bound"]
        for outcome in PRIMARY_OUTCOMES
    )
    harm = bool(conditional["artist_harm_family"]["any_harm_established"])
    availability_pass = bool(availability["passes"])
    if availability_pass and all(outcome_passes.values()) and not harm and both_missingness_robust:
        status = "supported"
    elif availability_pass and not harm and any(outcome_passes.values()):
        status = "mixed"
    else:
        status = "unsupported"
    reasons = []
    if not availability_pass:
        reasons.append("availability_requirement_failed")
    if harm:
        reasons.append("simultaneous_artist_harm_established")
    for outcome, passes in outcome_passes.items():
        if not passes:
            reasons.append(f"{outcome}_co_primary_not_supported")
    if all(outcome_passes.values()) and not both_missingness_robust:
        reasons.append("finite_schedule_missingness_bounds_not_both_positive")
    if status == "supported":
        reasons.append("all_frozen_support_requirements_passed")
    return {
        "status": status,
        "reasons": reasons,
        "availability_passes": availability_pass,
        "co_primary_passes": outcome_passes,
        "simultaneous_artist_harm_established": harm,
        "both_finite_schedule_worst_case_bounds_positive": both_missingness_robust,
        "claim": (
            "finite-roster, finite-content, exact requested-label pipeline result; never an "
            "artist-superpopulation, executed-model, broad style-fidelity, or future-prompt claim"
        ),
    }


def _analyze_phase_b_core_for_verified_inputs(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    terminal_rows: Sequence[Mapping[str, Any]],
    distance_rows: Sequence[Mapping[str, Any]],
    analysis_contract: Mapping[str, Any],
    runtime_bindings: Mapping[str, Any],
    tau_by_outcome: Mapping[str, Any],
) -> Dict[str, Any]:
    """Compute estimators after a future authoritative loader verifies every input.

    This private function is intentionally not an execution gate.  It exists so
    the frozen estimators and terminal decision can be tested prospectively.
    """

    contract = _mapping(analysis_contract, label="analysis contract")
    if contract.get("schema_version") != ANALYSIS_CONTRACT_SCHEMA:
        raise ValueError("unexpected Pilot-3 analysis-contract schema")
    _verify_seal(contract, field="semantic_sha256", label="analysis contract")
    bindings = _mapping(runtime_bindings, label="verified runtime evidence")
    schedule = validate_schedule(schedule_rows)
    terminals, terminal_counts = validate_terminal_accounting(schedule, terminal_rows)
    distances = validate_distance_rows(terminals, distance_rows)
    pairs = build_pair_outcomes(schedule, terminals, distances)

    availability = analyze_availability(pairs, contract["availability"])
    conditional = analyze_conditional_proximity(
        pairs,
        contract["conditional_proximity"],
        contract["artist_reversal_harm"],
    )
    missingness = analyze_finite_schedule_missingness(pairs, tau_by_outcome)
    decision = _terminal_decision(availability, conditional, missingness)
    payload = {
        "record_type": "pilot3_phase_b_analysis",
        "schema_version": "pilot3-phase-b-analysis/1.0",
        "status": "complete",
        "requested_model_label": EXPECTED_REQUESTED_LABEL,
        "transport": EXPECTED_TRANSPORT,
        "claim_boundary": dict(contract["claim_boundary"]),
        "bindings": bindings,
        "terminal_accounting": {
            "scheduled_requests": EXPECTED_SCHEDULE_COUNT,
            "terminal_requests": sum(terminal_counts.values()),
            "complete": sum(terminal_counts.values()) == EXPECTED_SCHEDULE_COUNT,
            "category_counts": terminal_counts,
        },
        "availability": availability,
        "conditional_a_vector_proximity": conditional,
        "finite_schedule_missingness": missingness,
        "decision": decision,
    }
    payload["result_sha256"] = stable_hash(payload)
    return payload


def analyze_phase_b(
    *,
    schedule_rows: Sequence[Mapping[str, Any]],
    terminal_rows: Sequence[Mapping[str, Any]],
    distance_rows: Sequence[Mapping[str, Any]],
    analysis_contract: Mapping[str, Any],
    runtime_bindings: Mapping[str, Any],
    tau_by_outcome: Mapping[str, Any],
) -> Dict[str, Any]:
    """Fail closed until the canonical P3-T14 runtime verifier exists.

    The arguments are retained to make the future file-backed handoff
    explicit, but none can authorize analysis while they are caller supplied.
    """

    del schedule_rows, terminal_rows, distance_rows, tau_by_outcome
    validate_runtime_bindings(runtime_bindings, analysis_contract)
    raise AssertionError("unreachable")
