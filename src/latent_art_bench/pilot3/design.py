"""Deterministic, offline design sensitivity for pilot_3.

This module deliberately does not estimate an effect from pilot_2.  Pilot 2's
complete-pair estimates are selected by image availability and therefore are
development observations, not plug-in truths.  The simulator instead crosses
explicit standardized-effect, variance-component, and refusal scenarios.

The proposed study has one requested-label stratum.  For every content block
and repetition it requests one shared artist-free control and one named image
per artist, so the request count is ``(artists + 1) * blocks * repetitions``.
The two conditional A-vector-proximity outcomes are co-primary.  Availability is a
separate outcome and missing images are never imputed as feature values.
"""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

from latent_art_bench.io import stable_hash

DESIGN_VERSION = "pilot3-crossed-cluster-scenario-sensitivity-v1"
SCHEMA_VERSION = "1.0"
SIMULATION_DRAWS = 2_000
SIMULATION_SEED = 20_260_903
FAMILYWISE_ALPHA = 0.05
CO_PRIMARY_FAMILY_SIZE = 2
MINIMUM_PAIR_AVAILABILITY = 0.90
MAXIMUM_ARTIST_AVAILABILITY_DISPARITY = 0.10
CURRENT_CANDIDATE_ARTIST_UNIVERSE_SIZE = 9
SHARED_CONTROL_RESIDUAL_FRACTION = 0.35

DEFAULT_ARTIST_COUNTS = (6, 8, 10)
DEFAULT_CONTENT_BLOCK_COUNTS = (8, 12, 16)
DEFAULT_REPETITION_COUNTS = (2, 3, 4)
DEFAULT_MIN_REQUEST_BUDGET = 250
DEFAULT_MAX_REQUEST_BUDGET = 500

DEFAULT_EFFECT_SCENARIOS: Tuple[Mapping[str, object], ...] = (
    {
        "name": "small",
        "target_improvement_standardized_effect": 0.20,
        "specificity_standardized_effect": 0.15,
        "force_one_artist_reversal": False,
    },
    {
        "name": "moderate",
        "target_improvement_standardized_effect": 0.40,
        "specificity_standardized_effect": 0.30,
        "force_one_artist_reversal": False,
    },
    {
        "name": "strong",
        "target_improvement_standardized_effect": 0.60,
        "specificity_standardized_effect": 0.50,
        "force_one_artist_reversal": False,
    },
    {
        "name": "moderate_one_artist_reversal_stress",
        "target_improvement_standardized_effect": 0.40,
        "specificity_standardized_effect": 0.30,
        "force_one_artist_reversal": True,
    },
)

DEFAULT_VARIANCE_SCENARIOS: Tuple[Mapping[str, object], ...] = (
    {
        "name": "moderate_crossed_clustering",
        "artist_variance_share": 0.18,
        "content_block_variance_share": 0.22,
        "artist_content_variance_share": 0.20,
        "residual_variance_share": 0.40,
    },
    {
        "name": "high_crossed_clustering",
        "artist_variance_share": 0.30,
        "content_block_variance_share": 0.30,
        "artist_content_variance_share": 0.25,
        "residual_variance_share": 0.15,
    },
)

DEFAULT_AVAILABILITY_SCENARIOS: Tuple[Mapping[str, object], ...] = (
    {
        "name": "diffuse_low_refusal",
        "named_refusal_probability_at_zero": 0.010,
        "control_refusal_probability_at_zero": 0.005,
        "artist_refusal_logit_sd": 0.50,
        "content_refusal_logit_sd": 0.25,
        "refusal_target_artist_effect_correlation": 0.0,
    },
    {
        "name": "pilot2_clustered_refusal",
        # Five refusals among 256 named requests in pilot_2.  The random artist
        # intercept represents the fact that all five belonged to one artist.
        "named_refusal_probability_at_zero": 5.0 / 256.0,
        # Zero observed control refusals is not evidence that the true risk is zero.
        "control_refusal_probability_at_zero": 0.005,
        "artist_refusal_logit_sd": 1.25,
        "content_refusal_logit_sd": 0.35,
        "refusal_target_artist_effect_correlation": 0.0,
    },
    {
        "name": "clustered_mnar_stress",
        "named_refusal_probability_at_zero": 0.040,
        "control_refusal_probability_at_zero": 0.010,
        "artist_refusal_logit_sd": 1.50,
        "content_refusal_logit_sd": 0.50,
        # Positive means artists with larger latent target effects are more
        # refusal-prone.  It is a stress scenario, not an empirical estimate.
        "refusal_target_artist_effect_correlation": 0.35,
    },
)

PILOT2_DEVELOPMENT_INPUTS: Mapping[str, object] = {
    "source_artifact": "reports/pilot_2/analysis.json",
    "source_result_sha256": (
        "a7fb58770ced0315a5963f1cd9606d91dd10ec30a324196af7720da85b82025c"
    ),
    "design": {
        "artists": 4,
        "content_blocks": 8,
        "repetitions": 4,
        "requested_label_strata": 2,
        "total_requests": 320,
        "named_requests": 256,
        "shared_control_requests": 64,
    },
    "refusal_observations": {
        "total": 5,
        "overall_rate": 5.0 / 320.0,
        "by_requested_label": {
            "gpt-image-1": {"count": 4, "denominator": 160},
            "gpt-image-2": {"count": 1, "denominator": 160},
        },
        "named_total": 5,
        "named_rate": 5.0 / 256.0,
        "shared_control_total": 0,
        "all_refusals_artist_id": "paul_cezanne",
        "one_artist_named_count": 5,
        "one_artist_named_denominator": 64,
        "remaining_artist_named_count": 0,
        "remaining_artist_named_denominator": 192,
        "technical_failure_total": 0,
    },
    "descriptive_complete_pair_content_block_sample_sd": {
        "gpt-image-1": {
            "target_improvement": 5.710051668006982,
            "specificity_difference_in_differences": 1.6085094023309372,
        },
        "gpt-image-2": {
            "target_improvement": 5.509064487646692,
            "specificity_difference_in_differences": 1.9679478664387795,
        },
    },
    "descriptive_complete_pair_artist_estimate_range": {
        "gpt-image-1": {
            "target_improvement": [1.7803884985334972, 14.37466076534324],
            "specificity_difference_in_differences": [
                -6.943118151171107,
                15.603853027828134,
            ],
        },
        "gpt-image-2": {
            "target_improvement": [3.071581995843801, 15.066876135509323],
            "specificity_difference_in_differences": [
                -6.853109103150654,
                14.524930353662038,
            ],
        },
        "note": (
            "Monet's descriptive specificity estimate was negative in both requested-label "
            "strata while the other artists' estimates were positive; these selected-case "
            "ranges motivate artist random-effect scenarios only"
        ),
    },
    "use_boundary": (
        "These biased, descriptive complete-pair quantities only motivate the "
        "crossed-cluster and artist-dependent-refusal scenario ranges. They are not "
        "effect estimates, variance-component estimates, priors, or assumed truths."
    ),
}

_EFFECT_KEYS = (
    "target_improvement_standardized_effect",
    "specificity_standardized_effect",
)
_VARIANCE_KEYS = (
    "artist_variance_share",
    "content_block_variance_share",
    "artist_content_variance_share",
    "residual_variance_share",
)
_AVAILABILITY_PROBABILITY_KEYS = (
    "named_refusal_probability_at_zero",
    "control_refusal_probability_at_zero",
)
_AVAILABILITY_SD_KEYS = (
    "artist_refusal_logit_sd",
    "content_refusal_logit_sd",
)


def request_count(artist_count: int, content_block_count: int, repetitions: int) -> int:
    """Return requests for named artists plus one shared control per block/repetition."""

    values = (artist_count, content_block_count, repetitions)
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in values):
        raise ValueError("artist_count, content_block_count, and repetitions must be integers >= 1")
    return (artist_count + 1) * content_block_count * repetitions


def exact_sign_flip_resolution(
    cluster_count: int,
    *,
    familywise_alpha: float = FAMILYWISE_ALPHA,
    family_size: int = CO_PRIMARY_FAMILY_SIZE,
) -> Dict[str, object]:
    """Describe exact one-sided sign-flip discreteness for one cluster axis.

    This is a resolution diagnostic.  The Monte Carlo sensitivity event below
    uses a conservative crossed-cluster lower-bound proxy; it does not pretend
    that artist and content signs can be permuted independently in the final
    analysis without additional assumptions.
    """

    if isinstance(cluster_count, bool) or not isinstance(cluster_count, int) or cluster_count < 1:
        raise ValueError("cluster_count must be an integer >= 1")
    if not math.isfinite(familywise_alpha) or not 0.0 < familywise_alpha < 1.0:
        raise ValueError("familywise_alpha must lie in (0, 1)")
    if isinstance(family_size, bool) or not isinstance(family_size, int) or family_size < 1:
        raise ValueError("family_size must be an integer >= 1")

    assignments = 2**cluster_count
    per_estimand_alpha = familywise_alpha / family_size
    maximum_passing_exceedances = max(
        0,
        int(math.ceil(per_estimand_alpha * assignments) - 1),
    )
    minimum_p = 1.0 / assignments
    return {
        "cluster_count": cluster_count,
        "assignment_count": assignments,
        "minimum_attainable_one_sided_p": minimum_p,
        "bonferroni_family_size": family_size,
        "per_estimand_strict_alpha": per_estimand_alpha,
        "minimum_bonferroni_adjusted_p": min(1.0, family_size * minimum_p),
        "can_ever_pass_strict_bonferroni_threshold": minimum_p < per_estimand_alpha,
        "maximum_passing_exceedance_count": maximum_passing_exceedances,
        "largest_attainable_p_below_threshold": (
            maximum_passing_exceedances / assignments
        ),
    }


def _validated_counts(values: Sequence[int], name: str) -> Tuple[int, ...]:
    if not values:
        raise ValueError(f"{name} must not be empty")
    normalized: List[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must contain only integers >= 1")
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _scenario_name(row: Mapping[str, object], family: str) -> str:
    name = row.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"each {family} scenario requires a non-empty string name")
    return name.strip()


def _finite_float(row: Mapping[str, object], key: str, family: str) -> float:
    value = row.get(key)
    if isinstance(value, bool):
        raise ValueError(f"{family} scenario {key} must be a finite number")
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{family} scenario {key} must be a finite number") from exc
    if not math.isfinite(result):
        raise ValueError(f"{family} scenario {key} must be a finite number")
    return result


def _normalize_effect_scenarios(
    rows: Sequence[Mapping[str, object]],
) -> Tuple[Dict[str, object], ...]:
    if not rows:
        raise ValueError("effect_scenarios must not be empty")
    normalized: List[Dict[str, object]] = []
    names = set()
    for row in rows:
        name = _scenario_name(row, "effect")
        if name in names:
            raise ValueError(f"duplicate effect scenario name: {name}")
        names.add(name)
        values = {key: _finite_float(row, key, "effect") for key in _EFFECT_KEYS}
        if any(value <= 0.0 for value in values.values()):
            raise ValueError(
                "standardized conditional A-vector-proximity effects must be positive"
            )
        force_reversal = row.get("force_one_artist_reversal", False)
        if not isinstance(force_reversal, bool):
            raise ValueError("force_one_artist_reversal must be boolean")
        normalized.append(
            {
                "name": name,
                **values,
                "force_one_artist_reversal": force_reversal,
            }
        )
    if all(bool(row["force_one_artist_reversal"]) for row in normalized):
        raise ValueError(
            "effect_scenarios must include at least one positive-effect sensitivity scenario"
        )
    return tuple(normalized)


def _normalize_variance_scenarios(
    rows: Sequence[Mapping[str, object]],
) -> Tuple[Dict[str, object], ...]:
    if not rows:
        raise ValueError("variance_scenarios must not be empty")
    normalized: List[Dict[str, object]] = []
    names = set()
    for row in rows:
        name = _scenario_name(row, "variance")
        if name in names:
            raise ValueError(f"duplicate variance scenario name: {name}")
        names.add(name)
        values = {key: _finite_float(row, key, "variance") for key in _VARIANCE_KEYS}
        if any(value < 0.0 for value in values.values()):
            raise ValueError("variance shares must be non-negative")
        if not math.isclose(sum(values.values()), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("variance shares must sum to 1")
        normalized.append({"name": name, **values})
    return tuple(normalized)


def _normalize_availability_scenarios(
    rows: Sequence[Mapping[str, object]],
) -> Tuple[Dict[str, object], ...]:
    if not rows:
        raise ValueError("availability_scenarios must not be empty")
    normalized: List[Dict[str, object]] = []
    names = set()
    for row in rows:
        name = _scenario_name(row, "availability")
        if name in names:
            raise ValueError(f"duplicate availability scenario name: {name}")
        names.add(name)
        probabilities = {
            key: _finite_float(row, key, "availability")
            for key in _AVAILABILITY_PROBABILITY_KEYS
        }
        if any(not 0.0 < value < 1.0 for value in probabilities.values()):
            raise ValueError("refusal probabilities must lie strictly in (0, 1)")
        standard_deviations = {
            key: _finite_float(row, key, "availability")
            for key in _AVAILABILITY_SD_KEYS
        }
        if any(value < 0.0 for value in standard_deviations.values()):
            raise ValueError("refusal logit standard deviations must be non-negative")
        correlation = _finite_float(
            row,
            "refusal_target_artist_effect_correlation",
            "availability",
        )
        if not -1.0 <= correlation <= 1.0:
            raise ValueError("refusal/effect correlation must lie in [-1, 1]")
        normalized.append(
            {
                "name": name,
                **probabilities,
                **standard_deviations,
                "refusal_target_artist_effect_correlation": correlation,
            }
        )
    return tuple(normalized)


def _derived_seed(seed: int, artist_count: int, block_count: int, repetitions: int) -> int:
    digest = stable_hash(
        {
            "seed": seed,
            "artist_count": artist_count,
            "content_block_count": block_count,
            "repetitions": repetitions,
            "purpose": DESIGN_VERSION,
        }
    )
    return int(digest[:16], 16)


def _logit(probability: float) -> float:
    return math.log(probability / (1.0 - probability))


def _expit(values: np.ndarray) -> np.ndarray:
    # Input ranges here are modest, but splitting by sign also keeps custom
    # stress scenarios numerically safe.
    result = np.empty_like(values, dtype=np.float64)
    nonnegative = values >= 0.0
    result[nonnegative] = 1.0 / (1.0 + np.exp(-values[nonnegative]))
    exponential = np.exp(values[~nonnegative])
    result[~nonnegative] = exponential / (1.0 + exponential)
    return result


def _student_t_critical_approximation(probability: float, degrees_of_freedom: int) -> float:
    """Return a deterministic Cornish-Fisher approximation to a t quantile.

    The default candidate grid has at least five degrees of freedom, where the
    third-order expansion is close to the tabulated t quantile.  It is an
    intentionally conservative small-cluster planning correction, not a
    replacement for the final preregistered randomization/bootstrap analysis.
    """

    if not 0.5 < probability < 1.0:
        raise ValueError("probability must lie in (0.5, 1)")
    if degrees_of_freedom < 1:
        raise ValueError("degrees_of_freedom must be positive")
    z = NormalDist().inv_cdf(probability)
    df = float(degrees_of_freedom)
    return (
        z
        + (z**3 + z) / (4.0 * df)
        + (5.0 * z**5 + 16.0 * z**3 + 3.0 * z) / (96.0 * df**2)
        + (3.0 * z**7 + 19.0 * z**5 + 17.0 * z**3 - 15.0 * z)
        / (384.0 * df**3)
    )


def _probability_summary(events: np.ndarray) -> Dict[str, float | int]:
    count = int(np.count_nonzero(events))
    draws = int(events.size)
    probability = count / draws
    return {
        "event_count": count,
        "draw_count": draws,
        "estimated_probability": probability,
        "monte_carlo_standard_error": math.sqrt(probability * (1.0 - probability) / draws),
    }


def _finite_mean_or_none(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    return float(np.mean(finite))


def _finite_quantile_or_none(values: np.ndarray, probability: float) -> float | None:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return None
    return float(np.quantile(finite, probability))


def _cluster_summary(
    noise: np.ndarray,
    available: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return conditional mean, conservative SE, and valid artist/block counts."""

    weighted = np.where(available, noise, 0.0)
    artist_count = available.sum(axis=(2, 3))
    artist_mean = np.divide(
        weighted.sum(axis=(2, 3)),
        artist_count,
        out=np.full(artist_count.shape, np.nan, dtype=np.float64),
        where=artist_count > 0,
    )
    valid_artists = np.count_nonzero(np.isfinite(artist_mean), axis=1)
    artist_center = np.divide(
        np.nansum(artist_mean, axis=1),
        valid_artists,
        out=np.full(valid_artists.shape, np.nan, dtype=np.float64),
        where=valid_artists > 0,
    )
    # The conditional point estimand gives every artist with at least one
    # usable pair equal weight.  Within an artist, usable content/repetition
    # pairs are frequency-weighted.  This avoids upweighting artists merely
    # because their requests were accepted more often.
    estimate = artist_center
    artist_ss = np.nansum((artist_mean - artist_center[:, None]) ** 2, axis=1)
    artist_variance = np.divide(
        artist_ss,
        valid_artists - 1,
        out=np.full(artist_ss.shape, np.inf, dtype=np.float64),
        where=valid_artists > 1,
    )
    artist_se = np.sqrt(
        np.divide(
            artist_variance,
            valid_artists,
            out=np.full(artist_variance.shape, np.inf, dtype=np.float64),
            where=valid_artists > 0,
        )
    )

    block_count = available.sum(axis=(1, 3))
    block_mean = np.divide(
        weighted.sum(axis=(1, 3)),
        block_count,
        out=np.full(block_count.shape, np.nan, dtype=np.float64),
        where=block_count > 0,
    )
    valid_blocks = np.count_nonzero(np.isfinite(block_mean), axis=1)
    block_center = np.divide(
        np.nansum(block_mean, axis=1),
        valid_blocks,
        out=np.zeros(valid_blocks.shape, dtype=np.float64),
        where=valid_blocks > 0,
    )
    block_ss = np.nansum((block_mean - block_center[:, None]) ** 2, axis=1)
    block_variance = np.divide(
        block_ss,
        valid_blocks - 1,
        out=np.full(block_ss.shape, np.inf, dtype=np.float64),
        where=valid_blocks > 1,
    )
    block_se = np.sqrt(
        np.divide(
            block_variance,
            valid_blocks,
            out=np.full(block_variance.shape, np.inf, dtype=np.float64),
            where=valid_blocks > 0,
        )
    )

    # Root-sum-squaring the two marginal-cluster contributions represents both
    # crossed axes.  It conservatively counts residual sampling variation in
    # both marginal terms.  This remains a planning proxy, not the final
    # preregistered estimator.
    conservative_se = np.sqrt(artist_se**2 + block_se**2)
    return estimate, conservative_se, valid_artists, valid_blocks, artist_mean


def _metric_sensitivity(
    *,
    observed_estimate: np.ndarray,
    conservative_se: np.ndarray,
    valid_artists: np.ndarray,
    valid_blocks: np.ndarray,
    artist_observed_means: np.ndarray,
    scenario_standardized_effect: float,
    force_one_artist_reversal: bool,
    critical_value: float,
    minimum_valid_artists: int,
    minimum_valid_blocks: int,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, object]]:
    analysis_ready = (
        np.isfinite(observed_estimate)
        & np.isfinite(conservative_se)
        & (valid_artists >= minimum_valid_artists)
        & (valid_blocks >= minimum_valid_blocks)
    )
    positive_lower_bound = analysis_ready & (
        observed_estimate - critical_value * conservative_se > 0.0
    )
    no_artist_reversal = analysis_ready & np.all(
        np.isfinite(artist_observed_means) & (artist_observed_means > 0.0),
        axis=1,
    )
    endpoint_planning_support = positive_lower_bound & no_artist_reversal
    summary: Dict[str, object] = {
        "scenario_standardized_effect": scenario_standardized_effect,
        "force_one_artist_reversal": force_one_artist_reversal,
        "forced_reversal_artist_index": 0 if force_one_artist_reversal else None,
        "forced_reversal_artist_true_effect": (
            -scenario_standardized_effect if force_one_artist_reversal else None
        ),
        "mean_observed_conditional_estimate": _finite_mean_or_none(observed_estimate),
        "mean_selection_shift_from_scenario_effect": _finite_mean_or_none(
            observed_estimate - scenario_standardized_effect
        ),
        "mean_crossed_cluster_standard_error": _finite_mean_or_none(conservative_se),
        "median_crossed_cluster_standard_error": _finite_quantile_or_none(
            conservative_se,
            0.50,
        ),
        "ninety_fifth_percentile_crossed_cluster_standard_error": (
            _finite_quantile_or_none(conservative_se, 0.95)
        ),
        "analysis_ready": _probability_summary(analysis_ready),
        "positive_bonferroni_crossed_cluster_lower_bound": _probability_summary(
            positive_lower_bound
        ),
        "no_artist_point_estimate_reversal": _probability_summary(no_artist_reversal),
        "aggregate_lower_bound_positive_and_no_artist_reversal": _probability_summary(
            endpoint_planning_support
        ),
    }
    return endpoint_planning_support, positive_lower_bound, summary


def _effect_adjusted_cluster_summary(
    *,
    noise: np.ndarray,
    available: np.ndarray,
    baseline: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    standardized_effect: float,
    force_one_artist_reversal: bool,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not force_one_artist_reversal:
        return (
            baseline[0] + standardized_effect,
            baseline[1],
            baseline[2],
            baseline[3],
            baseline[4] + standardized_effect,
        )

    artist_effects = np.full(noise.shape[1], standardized_effect, dtype=np.float64)
    # Preserve the equally weighted grand scenario effect while forcing artist
    # 0's true effect from +delta to -delta.
    artist_effects[0] = -standardized_effect
    if artist_effects.size > 1:
        artist_effects[1:] += 2.0 * standardized_effect / (artist_effects.size - 1)
    return _cluster_summary(
        noise + artist_effects[None, :, None, None],
        available,
    )


def simulate_candidate_design(
    *,
    artist_count: int,
    content_block_count: int,
    repetitions: int,
    draws: int = SIMULATION_DRAWS,
    seed: int = SIMULATION_SEED,
    familywise_alpha: float = FAMILYWISE_ALPHA,
    minimum_pair_availability: float = MINIMUM_PAIR_AVAILABILITY,
    maximum_artist_availability_disparity: float = (
        MAXIMUM_ARTIST_AVAILABILITY_DISPARITY
    ),
    effect_scenarios: Sequence[Mapping[str, object]] = DEFAULT_EFFECT_SCENARIOS,
    variance_scenarios: Sequence[Mapping[str, object]] = DEFAULT_VARIANCE_SCENARIOS,
    availability_scenarios: Sequence[Mapping[str, object]] = DEFAULT_AVAILABILITY_SCENARIOS,
) -> Dict[str, object]:
    """Simulate one crossed artist/content design under an explicit scenario grid."""

    total_requests = request_count(artist_count, content_block_count, repetitions)
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 1:
        raise ValueError("draws must be an integer >= 1")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not math.isfinite(familywise_alpha) or not 0.0 < familywise_alpha < 1.0:
        raise ValueError("familywise_alpha must lie in (0, 1)")
    if (
        not math.isfinite(minimum_pair_availability)
        or not 0.0 < minimum_pair_availability <= 1.0
    ):
        raise ValueError("minimum_pair_availability must lie in (0, 1]")
    if (
        not math.isfinite(maximum_artist_availability_disparity)
        or not 0.0 <= maximum_artist_availability_disparity <= 1.0
    ):
        raise ValueError("maximum_artist_availability_disparity must lie in [0, 1]")

    effects = _normalize_effect_scenarios(effect_scenarios)
    variances = _normalize_variance_scenarios(variance_scenarios)
    availabilities = _normalize_availability_scenarios(availability_scenarios)

    per_estimand_alpha = familywise_alpha / CO_PRIMARY_FAMILY_SIZE
    planning_degrees_of_freedom = max(1, min(artist_count, content_block_count) - 1)
    critical_value = _student_t_critical_approximation(
        1.0 - per_estimand_alpha,
        planning_degrees_of_freedom,
    )
    artist_resolution = exact_sign_flip_resolution(
        artist_count,
        familywise_alpha=familywise_alpha,
    )
    block_resolution = exact_sign_flip_resolution(
        content_block_count,
        familywise_alpha=familywise_alpha,
    )

    rng = np.random.default_rng(
        _derived_seed(seed, artist_count, content_block_count, repetitions)
    )
    metric_correlation = 0.50
    correlation_residual_scale = math.sqrt(1.0 - metric_correlation**2)

    def correlated_pair(shape: Tuple[int, ...]) -> np.ndarray:
        first = rng.normal(size=shape)
        second = metric_correlation * first + correlation_residual_scale * rng.normal(size=shape)
        return np.stack((first, second), axis=-1)

    artist_z = correlated_pair((draws, artist_count))
    block_z = correlated_pair((draws, content_block_count))
    artist_content_z = correlated_pair((draws, artist_count, content_block_count))
    named_residual_z = correlated_pair(
        (draws, artist_count, content_block_count, repetitions)
    )
    shared_control_residual_z = correlated_pair(
        (draws, content_block_count, repetitions)
    )
    artist_refusal_z = rng.normal(size=(draws, artist_count))
    content_refusal_z = rng.normal(size=(draws, content_block_count))
    named_uniform = rng.random(size=(draws, artist_count, content_block_count, repetitions))
    control_uniform = rng.random(size=(draws, content_block_count, repetitions))

    minimum_valid_artists = artist_count
    minimum_valid_blocks = min(6, content_block_count)
    scenario_results: List[Dict[str, object]] = []
    joint_probabilities: List[float] = []
    reversal_false_support_probabilities: List[float] = []
    null_any_endpoint_probabilities: List[float] = []
    null_both_endpoint_probabilities: List[float] = []
    pair_availability_means: List[float] = []
    pair_floor_probabilities: List[float] = []
    per_artist_floor_probabilities: List[float] = []
    artist_disparity_probabilities: List[float] = []

    for variance in variances:
        artist_scale = math.sqrt(float(variance["artist_variance_share"]))
        block_scale = math.sqrt(float(variance["content_block_variance_share"]))
        artist_content_scale = math.sqrt(
            float(variance["artist_content_variance_share"])
        )
        residual_scale = math.sqrt(float(variance["residual_variance_share"]))
        residual = residual_scale * (
            math.sqrt(1.0 - SHARED_CONTROL_RESIDUAL_FRACTION) * named_residual_z
            + math.sqrt(SHARED_CONTROL_RESIDUAL_FRACTION)
            * shared_control_residual_z[:, None, :, :, :]
        )
        noise = (
            artist_scale * artist_z[:, :, None, None, :]
            + block_scale * block_z[:, None, :, None, :]
            + artist_content_scale * artist_content_z[:, :, :, None, :]
            + residual
        )

        for availability in availabilities:
            refusal_effect_correlation = float(
                availability["refusal_target_artist_effect_correlation"]
            )
            refusal_effect_residual_scale = math.sqrt(
                max(0.0, 1.0 - refusal_effect_correlation**2)
            )
            artist_refusal_risk = (
                refusal_effect_correlation * artist_z[:, :, 0]
                + refusal_effect_residual_scale * artist_refusal_z
            )
            named_logit = (
                _logit(float(availability["named_refusal_probability_at_zero"]))
                + float(availability["artist_refusal_logit_sd"])
                * artist_refusal_risk[:, :, None]
                + float(availability["content_refusal_logit_sd"])
                * content_refusal_z[:, None, :]
            )
            control_logit = (
                _logit(float(availability["control_refusal_probability_at_zero"]))
                + float(availability["content_refusal_logit_sd"])
                * content_refusal_z
            )
            named_available = named_uniform >= _expit(named_logit)[:, :, :, None]
            control_available = control_uniform >= _expit(control_logit)[:, :, None]
            pair_available = named_available & control_available[:, None, :, :]

            named_successes = named_available.sum(axis=(1, 2, 3))
            control_successes = control_available.sum(axis=(1, 2))
            request_availability_fraction = (
                named_successes + control_successes
            ) / total_requests
            pair_availability_fraction = pair_available.mean(axis=(1, 2, 3))
            artist_pair_availability_fraction = pair_available.mean(axis=(2, 3))
            minimum_artist_pair_availability = artist_pair_availability_fraction.min(
                axis=1
            )
            artist_pair_availability_disparity = (
                artist_pair_availability_fraction.max(axis=1)
                - minimum_artist_pair_availability
            )
            artist_named_refusal_rate = 1.0 - named_available.mean(axis=(2, 3))
            max_artist_named_refusal_rate = artist_named_refusal_rate.max(axis=1)

            target_summary = _cluster_summary(noise[..., 0], pair_available)
            specificity_summary = _cluster_summary(noise[..., 1], pair_available)
            readiness = (
                (target_summary[2] >= minimum_valid_artists)
                & (target_summary[3] >= minimum_valid_blocks)
                & (specificity_summary[2] >= minimum_valid_artists)
                & (specificity_summary[3] >= minimum_valid_blocks)
            )
            availability_floor_event = pair_availability_fraction >= minimum_pair_availability
            per_artist_availability_floor_event = np.all(
                artist_pair_availability_fraction >= minimum_pair_availability,
                axis=1,
            )
            artist_disparity_event = (
                artist_pair_availability_disparity
                <= maximum_artist_availability_disparity
            )
            all_raw_availability_diagnostics_event = (
                availability_floor_event
                & per_artist_availability_floor_event
                & artist_disparity_event
            )
            availability_summary: Dict[str, object] = {
                "mean_request_availability": float(np.mean(request_availability_fraction)),
                "mean_complete_pair_availability": float(np.mean(pair_availability_fraction)),
                "assigned_named_control_pair_count": (
                    artist_count * content_block_count * repetitions
                ),
                "mean_usable_named_control_pair_count": float(
                    np.mean(pair_available.sum(axis=(1, 2, 3)))
                ),
                "fifth_percentile_usable_named_control_pair_count": float(
                    np.quantile(pair_available.sum(axis=(1, 2, 3)), 0.05)
                ),
                "fifth_percentile_complete_pair_availability": float(
                    np.quantile(pair_availability_fraction, 0.05)
                ),
                "complete_pair_availability_floor": minimum_pair_availability,
                "availability_floor_statistic": (
                    "raw simulated complete-pair fraction; not a confidence lower bound"
                ),
                "valid_clustered_availability_lower_bound_implemented": False,
                "complete_pair_availability_at_or_above_floor": _probability_summary(
                    availability_floor_event
                ),
                "mean_minimum_artist_complete_pair_availability": float(
                    np.mean(minimum_artist_pair_availability)
                ),
                "fifth_percentile_minimum_artist_complete_pair_availability": float(
                    np.quantile(minimum_artist_pair_availability, 0.05)
                ),
                "all_artists_raw_complete_pair_availability_at_or_above_floor": (
                    _probability_summary(per_artist_availability_floor_event)
                ),
                "artist_availability_disparity_definition": (
                    "maximum minus minimum raw complete-pair availability across roster "
                    "artists within a simulation draw"
                ),
                "maximum_artist_availability_disparity_diagnostic_threshold": (
                    maximum_artist_availability_disparity
                ),
                "mean_artist_availability_disparity": float(
                    np.mean(artist_pair_availability_disparity)
                ),
                "ninety_fifth_percentile_artist_availability_disparity": float(
                    np.quantile(artist_pair_availability_disparity, 0.95)
                ),
                "artist_availability_disparity_at_or_below_threshold": (
                    _probability_summary(artist_disparity_event)
                ),
                "all_raw_availability_diagnostics_pass": _probability_summary(
                    all_raw_availability_diagnostics_event
                ),
                "mean_maximum_artist_named_refusal_rate": float(
                    np.mean(max_artist_named_refusal_rate)
                ),
                "ninety_fifth_percentile_maximum_artist_named_refusal_rate": float(
                    np.quantile(max_artist_named_refusal_rate, 0.95)
                ),
                "conditional_analysis_cluster_ready": _probability_summary(readiness),
            }
            pair_availability_means.append(
                float(availability_summary["mean_complete_pair_availability"])
            )
            pair_floor_probabilities.append(
                float(
                    availability_summary["complete_pair_availability_at_or_above_floor"][  # type: ignore[index]
                        "estimated_probability"
                    ]
                )
            )
            per_artist_floor_probabilities.append(
                float(
                    availability_summary[
                        "all_artists_raw_complete_pair_availability_at_or_above_floor"
                    ]["estimated_probability"]  # type: ignore[index]
                )
            )
            artist_disparity_probabilities.append(
                float(
                    availability_summary[
                        "artist_availability_disparity_at_or_below_threshold"
                    ]["estimated_probability"]  # type: ignore[index]
                )
            )

            (
                null_target_event,
                null_target_aggregate_event,
                null_target_metric,
            ) = _metric_sensitivity(
                observed_estimate=target_summary[0],
                conservative_se=target_summary[1],
                valid_artists=target_summary[2],
                valid_blocks=target_summary[3],
                artist_observed_means=target_summary[4],
                scenario_standardized_effect=0.0,
                force_one_artist_reversal=False,
                critical_value=critical_value,
                minimum_valid_artists=minimum_valid_artists,
                minimum_valid_blocks=minimum_valid_blocks,
            )
            (
                null_specificity_event,
                null_specificity_aggregate_event,
                null_specificity_metric,
            ) = _metric_sensitivity(
                observed_estimate=specificity_summary[0],
                conservative_se=specificity_summary[1],
                valid_artists=specificity_summary[2],
                valid_blocks=specificity_summary[3],
                artist_observed_means=specificity_summary[4],
                scenario_standardized_effect=0.0,
                force_one_artist_reversal=False,
                critical_value=critical_value,
                minimum_valid_artists=minimum_valid_artists,
                minimum_valid_blocks=minimum_valid_blocks,
            )
            null_any_endpoint = null_target_event | null_specificity_event
            null_both_endpoints = null_target_event & null_specificity_event
            null_any_summary = _probability_summary(null_any_endpoint)
            null_both_summary = _probability_summary(null_both_endpoints)
            null_any_endpoint_probabilities.append(
                float(null_any_summary["estimated_probability"])
            )
            null_both_endpoint_probabilities.append(
                float(null_both_summary["estimated_probability"])
            )
            null_calibration: Dict[str, object] = {
                "effect_scenario": "zero_effect_calibration",
                "target_improvement_false_positive": null_target_metric[
                    "aggregate_lower_bound_positive_and_no_artist_reversal"
                ],
                "specificity_difference_in_differences_false_positive": (
                    null_specificity_metric[
                        "aggregate_lower_bound_positive_and_no_artist_reversal"
                    ]
                ),
                "aggregate_lcb_only_any_endpoint_false_positive": _probability_summary(
                    null_target_aggregate_event | null_specificity_aggregate_event
                ),
                "any_endpoint_false_positive_fwer": null_any_summary,
                "both_co_primary_endpoints_false_positive": null_both_summary,
                "excluded_from_recommendation_ranking": True,
                "interpretation": (
                    "empirical zero-effect calibration of the planning proxy under this "
                    "variance/availability scenario; not proof of finite-sample error control"
                ),
            }

            effect_results: List[Dict[str, object]] = []
            for effect in effects:
                target_effect = float(effect["target_improvement_standardized_effect"])
                specificity_effect = float(effect["specificity_standardized_effect"])
                force_reversal = bool(effect["force_one_artist_reversal"])
                target_effect_summary = _effect_adjusted_cluster_summary(
                    noise=noise[..., 0],
                    available=pair_available,
                    baseline=target_summary,
                    standardized_effect=target_effect,
                    force_one_artist_reversal=force_reversal,
                )
                specificity_effect_summary = _effect_adjusted_cluster_summary(
                    noise=noise[..., 1],
                    available=pair_available,
                    baseline=specificity_summary,
                    standardized_effect=specificity_effect,
                    force_one_artist_reversal=force_reversal,
                )
                target_event, _, target_metric = _metric_sensitivity(
                    observed_estimate=target_effect_summary[0],
                    conservative_se=target_effect_summary[1],
                    valid_artists=target_effect_summary[2],
                    valid_blocks=target_effect_summary[3],
                    artist_observed_means=target_effect_summary[4],
                    scenario_standardized_effect=target_effect,
                    force_one_artist_reversal=force_reversal,
                    critical_value=critical_value,
                    minimum_valid_artists=minimum_valid_artists,
                    minimum_valid_blocks=minimum_valid_blocks,
                )
                specificity_event, _, specificity_metric = _metric_sensitivity(
                    observed_estimate=specificity_effect_summary[0],
                    conservative_se=specificity_effect_summary[1],
                    valid_artists=specificity_effect_summary[2],
                    valid_blocks=specificity_effect_summary[3],
                    artist_observed_means=specificity_effect_summary[4],
                    scenario_standardized_effect=specificity_effect,
                    force_one_artist_reversal=force_reversal,
                    critical_value=critical_value,
                    minimum_valid_artists=minimum_valid_artists,
                    minimum_valid_blocks=minimum_valid_blocks,
                )
                joint_event = target_event & specificity_event
                joint_summary = _probability_summary(joint_event)
                effect_result: Dict[str, object] = {
                    "effect_scenario": effect["name"],
                    "target_improvement": target_metric,
                    "specificity_difference_in_differences": specificity_metric,
                }
                if force_reversal:
                    reversal_false_support_probabilities.append(
                        float(joint_summary["estimated_probability"])
                    )
                    effect_result.update(
                        {
                            "scenario_role": "artist_reversal_false_support_stress",
                            "false_support_under_forced_artist_reversal": joint_summary,
                            "false_support_and_all_raw_availability_diagnostics": (
                                _probability_summary(
                                    joint_event & all_raw_availability_diagnostics_event
                                )
                            ),
                            "excluded_from_positive_effect_sensitivity_ranking": True,
                            "desired_direction": "lower_false_support_is_better",
                        }
                    )
                else:
                    joint_probabilities.append(
                        float(joint_summary["estimated_probability"])
                    )
                    effect_result.update(
                        {
                            "scenario_role": "positive_effect_sensitivity",
                            "both_co_primary_endpoints_pass_aggregate_and_reversal_rule": (
                                joint_summary
                            ),
                            "both_co_primary_and_all_raw_availability_diagnostics": (
                                _probability_summary(
                                    joint_event & all_raw_availability_diagnostics_event
                                )
                            ),
                            "included_in_positive_effect_sensitivity_ranking": True,
                            "desired_direction": "higher_sensitivity_is_better",
                        }
                    )
                effect_results.append(effect_result)

            scenario_results.append(
                {
                    "variance_scenario": variance["name"],
                    "availability_scenario": availability["name"],
                    "availability": availability_summary,
                    "zero_effect_null_calibration": null_calibration,
                    "conditional_a_vector_proximity_sensitivity": effect_results,
                }
            )

    median_joint = float(np.median(np.asarray(joint_probabilities, dtype=np.float64)))
    minimum_joint = min(joint_probabilities)
    summary = {
        "minimum_joint_co_primary_sensitivity_across_scenarios": minimum_joint,
        "median_joint_co_primary_sensitivity_across_scenarios": median_joint,
        "maximum_joint_co_primary_sensitivity_across_scenarios": max(joint_probabilities),
        "maximum_false_support_under_forced_artist_reversal_stress": (
            max(reversal_false_support_probabilities)
            if reversal_false_support_probabilities
            else None
        ),
        "forced_artist_reversal_stress_excluded_from_sensitivity_ranking": True,
        "minimum_mean_complete_pair_availability_across_scenarios": min(
            pair_availability_means
        ),
        "minimum_probability_of_meeting_pair_availability_floor": min(
            pair_floor_probabilities
        ),
        "minimum_probability_all_artists_meet_raw_availability_floor": min(
            per_artist_floor_probabilities
        ),
        "minimum_probability_artist_disparity_is_within_diagnostic_threshold": min(
            artist_disparity_probabilities
        ),
        "maximum_null_any_endpoint_false_positive_fwer_across_scenarios": max(
            null_any_endpoint_probabilities
        ),
        "maximum_null_both_endpoints_false_positive_across_scenarios": max(
            null_both_endpoint_probabilities
        ),
        "null_any_endpoint_fwer_point_estimate_not_above_nominal": (
            max(null_any_endpoint_probabilities) <= familywise_alpha
        ),
        "null_calibration_excluded_from_ranking_score": True,
        "scenario_relative_ranking_score": 0.60 * median_joint + 0.40 * minimum_joint,
    }
    return {
        "design_id": (
            f"a{artist_count:02d}_b{content_block_count:02d}_r{repetitions:02d}"
        ),
        "artist_count": artist_count,
        "content_block_count": content_block_count,
        "repetitions": repetitions,
        "requested_label_strata": 1,
        "shared_artist_free_controls_per_block_repetition": 1,
        "request_count": total_requests,
        "within_current_nine_artist_candidate_universe": (
            artist_count <= CURRENT_CANDIDATE_ARTIST_UNIVERSE_SIZE
        ),
        "conditional_named_control_pair_count": (
            artist_count * content_block_count * repetitions
        ),
        "planning_test_proxy": {
            "method": (
                "root-sum-squared crossed marginal-cluster SE with a third-order "
                "Cornish-Fisher Student-t critical-value approximation"
            ),
            "degrees_of_freedom": planning_degrees_of_freedom,
            "critical_value": critical_value,
            "one_sided_per_estimand_alpha": per_estimand_alpha,
            "final_analysis_method": "not selected by this development simulation",
        },
        "exact_sign_flip_resolution": {
            "artist_axis": artist_resolution,
            "content_block_axis": block_resolution,
            "both_axes_can_resolve_multiplicity_threshold": bool(
                artist_resolution["can_ever_pass_strict_bonferroni_threshold"]
                and block_resolution["can_ever_pass_strict_bonferroni_threshold"]
            ),
        },
        "scenario_results": scenario_results,
        "summary": summary,
    }


def _scenario_relative_rankings(
    candidate_designs: Sequence[Mapping[str, object]],
) -> List[Dict[str, object]]:
    resolvable = [
        candidate
        for candidate in candidate_designs
        if bool(
            candidate["exact_sign_flip_resolution"][  # type: ignore[index]
                "both_axes_can_resolve_multiplicity_threshold"
            ]
        )
    ]
    ranked = sorted(
        resolvable,
        key=lambda candidate: (
            -float(candidate["summary"]["scenario_relative_ranking_score"]),  # type: ignore[index]
            -float(
                candidate["summary"][  # type: ignore[index]
                    "minimum_probability_of_meeting_pair_availability_floor"
                ]
            ),
            int(candidate["request_count"]),
            str(candidate["design_id"]),
        ),
    )
    rankings: List[Dict[str, object]] = []
    for rank, candidate in enumerate(ranked[:3], start=1):
        summary = candidate["summary"]
        rankings.append(
            {
                "rank": rank,
                "design_id": candidate["design_id"],
                "artist_count": candidate["artist_count"],
                "content_block_count": candidate["content_block_count"],
                "repetitions": candidate["repetitions"],
                "request_count": candidate["request_count"],
                "within_current_nine_artist_candidate_universe": candidate[
                    "within_current_nine_artist_candidate_universe"
                ],
                "scenario_relative_ranking_score": summary[
                    "scenario_relative_ranking_score"
                ],
                "minimum_joint_co_primary_sensitivity_across_scenarios": summary[
                    "minimum_joint_co_primary_sensitivity_across_scenarios"
                ],
                "median_joint_co_primary_sensitivity_across_scenarios": summary[
                    "median_joint_co_primary_sensitivity_across_scenarios"
                ],
                "maximum_false_support_under_forced_artist_reversal_stress": summary[
                    "maximum_false_support_under_forced_artist_reversal_stress"
                ],
                "reversal_false_support_excluded_from_ranking": True,
                "minimum_mean_complete_pair_availability_across_scenarios": summary[
                    "minimum_mean_complete_pair_availability_across_scenarios"
                ],
                "minimum_probability_all_artists_meet_raw_availability_floor": summary[
                    "minimum_probability_all_artists_meet_raw_availability_floor"
                ],
                "minimum_probability_artist_disparity_is_within_diagnostic_threshold": (
                    summary[
                        "minimum_probability_artist_disparity_is_within_diagnostic_threshold"
                    ]
                ),
                "maximum_null_any_endpoint_false_positive_fwer_across_scenarios": summary[
                    "maximum_null_any_endpoint_false_positive_fwer_across_scenarios"
                ],
                "null_calibration_excluded_from_ranking": True,
                "diagnostic_scope": (
                    "scenario-relative ranking only; not a feasible-design recommendation, "
                    "not a powered sample-size determination, and not a generation plan"
                ),
            }
        )
    return rankings


def build_pilot3_design_sensitivity(
    *,
    artist_counts: Sequence[int] = DEFAULT_ARTIST_COUNTS,
    content_block_counts: Sequence[int] = DEFAULT_CONTENT_BLOCK_COUNTS,
    repetition_counts: Sequence[int] = DEFAULT_REPETITION_COUNTS,
    min_request_budget: int = DEFAULT_MIN_REQUEST_BUDGET,
    max_request_budget: int = DEFAULT_MAX_REQUEST_BUDGET,
    draws: int = SIMULATION_DRAWS,
    seed: int = SIMULATION_SEED,
    familywise_alpha: float = FAMILYWISE_ALPHA,
    minimum_pair_availability: float = MINIMUM_PAIR_AVAILABILITY,
    maximum_artist_availability_disparity: float = (
        MAXIMUM_ARTIST_AVAILABILITY_DISPARITY
    ),
    effect_scenarios: Sequence[Mapping[str, object]] = DEFAULT_EFFECT_SCENARIOS,
    variance_scenarios: Sequence[Mapping[str, object]] = DEFAULT_VARIANCE_SCENARIOS,
    availability_scenarios: Sequence[Mapping[str, object]] = DEFAULT_AVAILABILITY_SCENARIOS,
) -> Dict[str, object]:
    """Search resource-feasible crossed designs and return self-hashed evidence."""

    artists = _validated_counts(artist_counts, "artist_counts")
    blocks = _validated_counts(content_block_counts, "content_block_counts")
    repetitions = _validated_counts(repetition_counts, "repetition_counts")
    for value, name in (
        (min_request_budget, "min_request_budget"),
        (max_request_budget, "max_request_budget"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be an integer >= 1")
    if min_request_budget > max_request_budget:
        raise ValueError("min_request_budget must not exceed max_request_budget")

    # Normalize before simulation so validation occurs even when no candidate
    # lies inside the budget and so the recorded grid is canonical.
    effects = _normalize_effect_scenarios(effect_scenarios)
    variances = _normalize_variance_scenarios(variance_scenarios)
    availabilities = _normalize_availability_scenarios(availability_scenarios)
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 1:
        raise ValueError("draws must be an integer >= 1")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not math.isfinite(familywise_alpha) or not 0.0 < familywise_alpha < 1.0:
        raise ValueError("familywise_alpha must lie in (0, 1)")
    if (
        not math.isfinite(minimum_pair_availability)
        or not 0.0 < minimum_pair_availability <= 1.0
    ):
        raise ValueError("minimum_pair_availability must lie in (0, 1]")
    if (
        not math.isfinite(maximum_artist_availability_disparity)
        or not 0.0 <= maximum_artist_availability_disparity <= 1.0
    ):
        raise ValueError("maximum_artist_availability_disparity must lie in [0, 1]")

    design_triplets = [
        (artist_count, block_count, repetition_count)
        for artist_count in artists
        for block_count in blocks
        for repetition_count in repetitions
        if min_request_budget
        <= request_count(artist_count, block_count, repetition_count)
        <= max_request_budget
    ]
    if not design_triplets:
        raise ValueError("no candidate design lies within the request-budget bounds")

    candidate_designs = [
        simulate_candidate_design(
            artist_count=artist_count,
            content_block_count=block_count,
            repetitions=repetition_count,
            draws=draws,
            seed=seed,
            familywise_alpha=familywise_alpha,
            minimum_pair_availability=minimum_pair_availability,
            maximum_artist_availability_disparity=(
                maximum_artist_availability_disparity
            ),
            effect_scenarios=effects,
            variance_scenarios=variances,
            availability_scenarios=availabilities,
        )
        for artist_count, block_count, repetition_count in design_triplets
    ]
    per_estimand_alpha = familywise_alpha / CO_PRIMARY_FAMILY_SIZE
    payload: Dict[str, object] = {
        "record_type": "pilot3_design_sensitivity",
        "schema_version": SCHEMA_VERSION,
        "design_version": DESIGN_VERSION,
        "status": "development_sensitivity_complete",
        "network_or_image_requests_made": False,
        "pilot2_development_inputs": dict(PILOT2_DEVELOPMENT_INPUTS),
        "assumptions": {
            "requested_label_strata": 1,
            "request_formula": "(artist_count + 1) * content_block_count * repetitions",
            "control_structure": (
                "one artist-free control request is shared across artists within each "
                "content-block/repetition cell"
            ),
            "conditional_a_vector_proximity_estimands": [
                "target_improvement",
                "specificity_difference_in_differences",
            ],
            "availability_estimand": (
                "probability of a usable response, reported separately from conditional "
                "A-vector proximity; refusals are outcomes and are not imputed"
            ),
            "conditional_point_estimator": (
                "equal mean of per-artist usable-pair means; within each artist, usable "
                "content-block/repetition pairs receive equal pair weight, so an artist's "
                "availability count does not determine its top-level weight"
            ),
            "multiplicity": {
                "method": "Bonferroni sensitivity threshold for two co-primary estimands",
                "familywise_alpha": familywise_alpha,
                "family_size": CO_PRIMARY_FAMILY_SIZE,
                "one_sided_per_estimand_alpha": per_estimand_alpha,
                "small_cluster_correction": (
                    "candidate-specific Student-t critical-value approximation with "
                    "df=min(artist_count, content_block_count)-1"
                ),
            },
            "outcome_scale": (
                "each conditional A-vector-proximity outcome has unit total latent variance within "
                "a scenario; effect values are standardized assumptions"
            ),
            "outcome_correlation": 0.50,
            "clustering": (
                "crossed Gaussian artist, content-block, and persistent artist-by-content "
                "effects plus residual variation; planning detection root-sum-squares "
                "artist- and block-marginal SEs"
            ),
            "shared_control_covariance": {
                "residual_variance_fraction": SHARED_CONTROL_RESIDUAL_FRACTION,
                "structure": (
                    "one block-by-repetition control residual is shared by every artist's "
                    "paired contrast in that cell; the remaining residual is artist-specific"
                ),
            },
            "availability_model": (
                "Bernoulli requests with logistic-normal artist and content random effects; "
                "the control request is shared, and the stress scenario permits refusal to "
                "correlate with the latent target artist effect"
            ),
            "minimum_valid_clusters_for_planning_event": {
                "artist_axis": "all configured roster artists must have a usable pair",
                "content_block_axis": 6,
            },
            "artist_reversal_rule": (
                "every configured artist's usable-pair point estimate must be positive for "
                "each endpoint in every draw; one scenario forces artist 0's true effect "
                "negative while preserving the equally weighted grand scenario effect; "
                "support in that stress is false support, so lower is better and it is "
                "excluded from positive-effect sensitivity rankings"
            ),
            "minimum_complete_pair_availability": minimum_pair_availability,
            "maximum_artist_availability_disparity_diagnostic": (
                maximum_artist_availability_disparity
            ),
            "availability_floor_boundary": (
                "the simulator evaluates raw aggregate and per-artist complete-pair "
                "fractions plus a raw max-minus-min artist disparity; no crossed-cluster "
                "availability confidence lower bound is implemented, so these diagnostics "
                "cannot satisfy the protocol's future availability gate"
            ),
            "conditional_content_weighting_limitation": (
                "within an artist, usable content/repetition pairs are frequency-weighted; "
                "a final equal-content estimand and its aligned crossed-cluster estimator "
                "remain prospective TODOs"
            ),
        },
        "search": {
            "artist_counts": list(artists),
            "content_block_counts": list(blocks),
            "repetition_counts": list(repetitions),
            "minimum_request_budget": min_request_budget,
            "maximum_request_budget": max_request_budget,
            "candidate_count": len(candidate_designs),
            "simulation_draws_per_candidate_scenario": draws,
            "simulation_seed": seed,
            "current_candidate_artist_universe_size": (
                CURRENT_CANDIDATE_ARTIST_UNIVERSE_SIZE
            ),
            "common_random_numbers_within_candidate": True,
            "candidate_seed_is_order_invariant": True,
        },
        "scenario_grid": {
            "zero_effect_null_calibration": {
                "target_improvement_standardized_effect": 0.0,
                "specificity_standardized_effect": 0.0,
                "reported_separately_and_excluded_from_ranking": True,
            },
            "conditional_effect_scenarios": list(effects),
            "variance_scenarios": list(variances),
            "availability_scenarios": list(availabilities),
        },
        "exact_sign_flip_resolution": {
            "purpose": (
                "discreteness diagnostic only; it does not license independent crossed-axis "
                "sign permutations for the final analysis"
            ),
            "artist_axis": [
                exact_sign_flip_resolution(
                    count,
                    familywise_alpha=familywise_alpha,
                )
                for count in artists
            ],
            "content_block_axis": [
                exact_sign_flip_resolution(
                    count,
                    familywise_alpha=familywise_alpha,
                )
                for count in blocks
            ],
        },
        "candidate_designs": candidate_designs,
        "scenario_relative_ranked_designs": _scenario_relative_rankings(
            candidate_designs
        ),
        "recommended_feasible_designs": [],
        "design_decision": "NO_DESIGN_SELECTED_CRITERIA_UNRESOLVED",
        "prospective_acceptance_criteria_frozen": False,
        "design_decision_reasons": [
            (
                "no prospective joint-sensitivity or precision acceptance threshold has "
                "been frozen"
            ),
            (
                "no maximum acceptable false-support probability under the forced artist "
                "reversal stress has been frozen"
            ),
            (
                "availability is evaluated with a raw fraction rather than the required "
                "crossed-cluster confidence lower bound"
            ),
            (
                "the raw per-artist availability floor and artist-disparity diagnostics are "
                "not substitutes for a prospectively implemented clustered lower-bound and "
                "disparity decision rule"
            ),
            (
                "some searched diagnostic designs request ten artists, exceeding the "
                "current nine-artist candidate universe"
            ),
            (
                "scenario-relative sensitivity estimates are low and cannot support a "
                "power claim or authorize generation"
            ),
        ],
        "interpretation": (
            "Diagnostic rankings compare candidate designs only under the recorded scenario "
            "grid. No design is recommended. Corpus feasibility, a valid clustered "
            "availability interval, a preregistered final estimator, and prospective "
            "acceptance criteria are required before any image request."
        ),
        "claim_boundary": (
            "Deterministic Monte Carlo sensitivity, not guaranteed power, not a pilot_2 "
            "effect estimate, not evidence of executed-model identity, and not authority to "
            "generate images. Pilot_2 complete-case effects may be availability-selected."
        ),
    }
    payload["result_sha256"] = stable_hash(payload)
    return payload


__all__ = [
    "CO_PRIMARY_FAMILY_SIZE",
    "CURRENT_CANDIDATE_ARTIST_UNIVERSE_SIZE",
    "DEFAULT_ARTIST_COUNTS",
    "DEFAULT_AVAILABILITY_SCENARIOS",
    "DEFAULT_CONTENT_BLOCK_COUNTS",
    "DEFAULT_EFFECT_SCENARIOS",
    "DEFAULT_MAX_REQUEST_BUDGET",
    "DEFAULT_MIN_REQUEST_BUDGET",
    "DEFAULT_REPETITION_COUNTS",
    "DEFAULT_VARIANCE_SCENARIOS",
    "DESIGN_VERSION",
    "FAMILYWISE_ALPHA",
    "MAXIMUM_ARTIST_AVAILABILITY_DISPARITY",
    "MINIMUM_PAIR_AVAILABILITY",
    "PILOT2_DEVELOPMENT_INPUTS",
    "SIMULATION_DRAWS",
    "SIMULATION_SEED",
    "SHARED_CONTROL_RESIDUAL_FRACTION",
    "build_pilot3_design_sensitivity",
    "exact_sign_flip_resolution",
    "request_count",
    "simulate_candidate_design",
]
