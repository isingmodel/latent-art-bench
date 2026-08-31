"""Deterministic pre-generation sample-size sensitivity for pilot_2.

The real effect scale is unknown and the preceding pilot used a confounded
feature path.  This module therefore does not estimate power from pilot_1 or
invent a minimum detectable effect.  It reports exact-test discreteness and a
standardized-effect sensitivity surface for the frozen eight block means.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Sequence

import numpy as np

from latent_art_bench.io import stable_hash

DESIGN_VERSION = "pilot2-standardized-sign-flip-sensitivity-v1"
BLOCK_COUNT = 8
REPETITIONS_PER_BLOCK = 4
FAMILY_SIZE = 4
FAMILYWISE_ALPHA = 0.05
STRICT_RAW_P_THRESHOLD = FAMILYWISE_ALPHA / FAMILY_SIZE
SIMULATION_DRAWS = 100_000
SIMULATION_SEED = 20_260_901
STANDARDIZED_EFFECTS = (0.5, 0.75, 1.0, 1.25, 1.5)


def _sign_assignments(block_count: int) -> np.ndarray:
    if block_count < 1:
        raise ValueError("sign-flip sensitivity requires at least one block")
    return np.asarray(
        list(itertools.product((-1.0, 1.0), repeat=block_count)),
        dtype=np.float64,
    )


def _passing_count_for_batch(
    values: np.ndarray,
    signs: np.ndarray,
    *,
    strict_p_threshold: float,
) -> int:
    observed = values.mean(axis=1)
    permuted = values @ signs.T / values.shape[1]
    tolerance = (
        10.0
        * np.finfo(np.float64).eps
        * np.maximum(1.0, np.abs(observed))[:, None]
    )
    exceedances = np.count_nonzero(
        permuted >= observed[:, None] - tolerance,
        axis=1,
    )
    return int(np.count_nonzero(exceedances / signs.shape[0] < strict_p_threshold))


def simulate_standardized_sign_flip_power(
    standardized_effects: Sequence[float] = STANDARDIZED_EFFECTS,
    *,
    draws: int = SIMULATION_DRAWS,
    seed: int = SIMULATION_SEED,
    block_count: int = BLOCK_COUNT,
    strict_p_threshold: float = STRICT_RAW_P_THRESHOLD,
    batch_size: int = 2_000,
) -> List[Dict[str, float | int]]:
    """Simulate a one-test sensitivity curve for standardized block means.

    Each block mean is independently distributed as ``N(delta, 1)``.  The
    result is only a sensitivity analysis for the exact sign-flip component of
    the decision rule; it excludes the bootstrap lower bound and source-sign
    requirements and is not an empirical effect estimate.
    """

    if draws < 1 or batch_size < 1:
        raise ValueError("simulation draws and batch size must be positive")
    if seed < 0:
        raise ValueError("simulation seed must be non-negative")
    if not 0.0 < strict_p_threshold < 1.0:
        raise ValueError("the strict raw-p threshold must lie in (0, 1)")
    effects = [float(value) for value in standardized_effects]
    if not effects or any(not np.isfinite(value) or value <= 0.0 for value in effects):
        raise ValueError("standardized effects must be finite and positive")

    signs = _sign_assignments(block_count)
    rng = np.random.default_rng(seed)
    rows: List[Dict[str, float | int]] = []
    for effect in effects:
        passing = 0
        remaining = draws
        while remaining:
            count = min(batch_size, remaining)
            values = rng.normal(
                loc=effect,
                scale=1.0,
                size=(count, block_count),
            )
            passing += _passing_count_for_batch(
                values,
                signs,
                strict_p_threshold=strict_p_threshold,
            )
            remaining -= count
        rows.append(
            {
                "standardized_block_mean_effect": effect,
                "passing_draw_count": passing,
                "draw_count": draws,
                "estimated_probability": passing / draws,
            }
        )
    return rows


def build_sample_size_sensitivity(
    *,
    draws: int = SIMULATION_DRAWS,
    seed: int = SIMULATION_SEED,
) -> Dict[str, object]:
    assignments = 2**BLOCK_COUNT
    maximum_passing_exceedances = int(
        np.ceil(STRICT_RAW_P_THRESHOLD * assignments) - 1
    )
    exact_resolution = [
        {
            "block_count": count,
            "assignment_count": 2**count,
            "minimum_attainable_p": 1.0 / (2**count),
            "four_equal_minimum_holm_adjusted_p": min(1.0, FAMILY_SIZE / (2**count)),
            "four_equal_minimum_can_pass_strict_0_05": (
                FAMILY_SIZE / (2**count) < FAMILYWISE_ALPHA
            ),
        }
        for count in range(4, BLOCK_COUNT + 1)
    ]
    payload: Dict[str, object] = {
        "record_type": "pilot2_sample_size_sensitivity",
        "schema_version": "2.0",
        "design_version": DESIGN_VERSION,
        "status": "pass",
        "frozen_design": {
            "content_block_count": BLOCK_COUNT,
            "repetitions_per_block": REPETITIONS_PER_BLOCK,
            "top_level_inference_unit": "content_block",
            "primary_hypothesis_family_size": FAMILY_SIZE,
            "familywise_alpha": FAMILYWISE_ALPHA,
            "strict_raw_p_sensitivity_threshold": STRICT_RAW_P_THRESHOLD,
        },
        "exact_sign_flip_resolution": {
            "assignment_count": assignments,
            "minimum_attainable_p": 1.0 / assignments,
            "maximum_passing_exceedance_count_under_strict_0_0125": (
                maximum_passing_exceedances
            ),
            "largest_attainable_p_below_strict_0_0125": (
                maximum_passing_exceedances / assignments
            ),
            "block_count_sensitivity": exact_resolution,
        },
        "simulation": {
            "data_generating_assumption": (
                "independent standardized block means X_b ~ Normal(delta, 1)"
            ),
            "draws_per_effect": draws,
            "seed": seed,
            "standardized_effect_grid": list(STANDARDIZED_EFFECTS),
            "decision_event": "exact one-sided sign-flip p < 0.0125",
            "results": simulate_standardized_sign_flip_power(draws=draws, seed=seed),
        },
        "decision": (
            "retain eight content blocks and four repetitions as a resource-bounded "
            "feasibility pilot: eight blocks provide useful exact-test resolution and "
            "four repetitions stabilize each block mean, but the top-level n remains "
            "eight and modest standardized effects are not assumed to have 80% power"
        ),
        "claim_boundary": (
            "standardized-effect sensitivity only; not an empirical effect estimate, "
            "not a full simulation of bootstrap/source-sign criteria, and not evidence "
            "that an unsupported result proves absence"
        ),
    }
    payload["evidence_sha256"] = stable_hash(payload)
    return payload


__all__ = [
    "BLOCK_COUNT",
    "DESIGN_VERSION",
    "REPETITIONS_PER_BLOCK",
    "SIMULATION_DRAWS",
    "SIMULATION_SEED",
    "STANDARDIZED_EFFECTS",
    "build_sample_size_sensitivity",
    "simulate_standardized_sign_flip_power",
]
