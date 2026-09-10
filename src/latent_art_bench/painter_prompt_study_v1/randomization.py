"""Small-study finite energy contrasts and conditional paired randomization tests.

Random assignment of three methods to fixed positions makes each pair's assignments
equiprobable conditional on the third position. Validity requires the sharp no-effect
null with no interference, or joint invariance under every within-scene pair swap.
Equal population energy distances alone do not imply that null. No CI is produced.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist

from .calibration import wilson

DRAW_COUNT = 99999
REPETITIONS = (1, 2, 4)
SCENARIOS = (
    "constant_magnitude",
    "scene_magnitude_drift",
    "rare_large_contribution",
    "zero_contributions",
)
DEPENDENCE = ("independent_endpoints", "shared_three_family_signs")
NULL = (
    "sharp no-prompt-effect with no interference under the frozen randomized assignment; "
    "alternatively joint within-scene method-label swap invariance; not equal energy alone"
)
SOURCES = [
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC6405018/",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC3416023/",
    "https://doi.org/10.2307/4615733",
]


def _integer(value, minimum=0):
    return type(value) is int and value >= minimum


def paired_energy_contributions(reference, before, after):
    """Return n coefficients whose sum is V-energy(after,R) minus V-energy(before,R).

    All arrays have shape [observations, coordinates]. Before and after rows are
    matched by fixed scene and repetition. Under complementary label swaps the
    statistic is exactly sign @ coefficients, despite nonlinear within-set energy.
    """
    reference, before, after = [np.asarray(v, dtype=float) for v in (reference, before, after)]
    if (
        any(
            v.ndim != 2 or not len(v) or not np.isfinite(v).all()
            for v in (reference, before, after)
        )
        or before.shape != after.shape
        or not before.shape[1]
        or reference.shape[1] != before.shape[1]
    ):
        raise ValueError("expected finite reference[N,D] and paired before/after[n,D]")
    n = len(before)
    pooled = np.concatenate([before, after])
    reference_means = cdist(pooled, reference).mean(axis=1)
    pooled_rows = cdist(pooled, pooled).sum(axis=1)
    coefficients = (
        2 * (reference_means[n:] - reference_means[:n]) / n
        - (pooled_rows[n:] - pooled_rows[:n]) / n**2
    )
    if not np.isfinite(coefficients).all():
        raise ValueError("nonfinite energy contributions")
    return coefficients


def endpoint_seed(seed: int, index: int) -> int:
    if not _integer(seed) or not _integer(index):
        raise ValueError("seed and canonical endpoint index must be nonnegative integers")
    return int(np.random.SeedSequence([seed, index]).generate_state(1, dtype=np.uint64)[0])


def randomization_pvalue(
    contributions, *, seed: int, draws: int = DRAW_COUNT, exact_max_pairs: int = 16
) -> dict:
    values = np.asarray(contributions, dtype=float)
    if (
        values.ndim != 1
        or not len(values)
        or not np.isfinite(values).all()
        or not _integer(seed)
        or not _integer(draws, 1)
        or not _integer(exact_max_pairs)
        or exact_max_pairs > 20
    ):
        raise ValueError("expected finite paired coefficients and valid randomization settings")
    n = len(values)
    estimate = float(values.sum())
    if not np.isfinite(estimate):
        raise ValueError("nonfinite energy contrast")
    # The tolerance includes numerically equal ties conservatively; no tie randomization.
    tolerance = float(32 * np.finfo(float).eps * np.abs(values).sum())
    threshold = abs(estimate) - tolerance
    exact = n <= exact_max_pairs
    count = 2**n if exact else draws
    rng = np.random.default_rng(seed)
    exceedances = 0
    for start in range(0, count, 4096):
        batch = min(4096, count - start)
        if exact:
            numbers = np.arange(start, start + batch, dtype=np.uint64)
            bits = ((numbers[:, None] >> np.arange(n, dtype=np.uint64)) & 1).astype(np.int8)
        else:
            bits = rng.integers(0, 2, size=(batch, n), dtype=np.int8)
        statistics = np.einsum("ij,j->i", 2 * bits - 1, values)
        exceedances += int(np.count_nonzero(np.abs(statistics) >= threshold))
    pvalue = exceedances / count if exact else (exceedances + 1) / (count + 1)
    return dict(
        estimate=estimate,
        raw_p=float(pvalue),
        pairs=n,
        permutations=count,
        exceedances=exceedances,
        seed=None if exact else seed,
        method="exact_paired_randomization" if exact else "monte_carlo_paired_randomization",
        status="conditional_randomization",
        null=NULL,
        zero_contributions=bool(not np.any(values)),
        tie_tolerance=tolerance,
    )


def holm(pvalues):
    """Holm-adjusted p-values in original order; arbitrary endpoint dependence is allowed."""
    values = np.asarray(pvalues, dtype=float)
    if (
        values.ndim != 1
        or not len(values)
        or not np.isfinite(values).all()
        or np.any((values < 0) | (values > 1))
    ):
        raise ValueError("expected finite p-values in [0,1]")
    order = np.argsort(values, kind="stable")
    adjusted = np.minimum(1, np.maximum.accumulate(values[order] * np.arange(len(values), 0, -1)))
    result = np.empty_like(adjusted)
    result[order] = adjusted
    return result


def _weights(scenario, n):
    weights = np.ones(n, dtype=int)
    if scenario == "scene_magnitude_drift":
        weights = 1 + np.arange(n) % 4
    elif scenario == "rare_large_contribution":
        weights[-1] = 20
    elif scenario == "zero_contributions":
        weights[:] = 0
    elif scenario != "constant_magnitude":
        raise ValueError("unknown synthetic contribution scenario")
    return weights


def _exact_absolute_tail(weights):
    """Exact weighted-Rademacher tails by finite integer convolution, no normal approximation."""
    total = int(weights.sum())
    mass = np.array([1.0])
    for weight in weights:
        expanded = np.zeros(len(mass) + 2 * int(weight))
        expanded[: len(mass)] += mass / 2
        expanded[2 * weight : 2 * weight + len(mass)] += mass / 2
        mass = expanded
    absolute = np.abs(np.arange(len(mass)) - total)
    by_magnitude = np.bincount(absolute, weights=mass, minlength=total + 1)
    return np.minimum(1, np.cumsum(by_magnitude[::-1])[::-1])


def _synthetic_cell(
    rng,
    *,
    trials,
    repetitions,
    scenario,
    dependence,
    positive_probability=0.5,
    persistent_sign=False,
):
    n = 16 * repetitions
    weights = _weights(scenario, n)
    groups = 48 if dependence == "independent_endpoints" else 16
    totals = np.zeros((trials, groups), dtype=int)
    if persistent_sign:
        totals = (2 * rng.binomial(1, 0.5, size=(trials, groups)) - 1) * weights.sum()
    else:
        for weight in np.unique(weights):
            count = int(np.count_nonzero(weights == weight))
            totals += weight * (
                2 * rng.binomial(count, positive_probability, size=(trials, groups)) - count
            )
    exact_p = _exact_absolute_tail(weights)[np.abs(totals)]
    if groups == 16:
        exact_p = np.repeat(exact_p, 3, axis=1)
    # Conditional on the observed statistic, independent uniform Monte Carlo sign
    # draws give an exactly Binomial(B,p_exact) exceedance count. This shortcut
    # avoids 2000*48*99999 permutations and is not an asymptotic approximation.
    pvalues = (
        exact_p if repetitions == 1 else (1 + rng.binomial(DRAW_COUNT, exact_p)) / (DRAW_COUNT + 1)
    )
    rejected = np.array([holm(row) <= 0.05 for row in pvalues])
    any_rejections = int(rejected.any(axis=1).sum())
    return dict(
        repetitions=repetitions,
        matched_scenes=n,
        scenario=scenario,
        dependence=dependence,
        trials=trials,
        endpoints=48,
        family_rejections=any_rejections,
        family_rejection_rate=any_rejections / trials,
        family_rejection_wilson_95=wilson(any_rejections, trials),
        mean_rejected_endpoints=float(rejected.sum(axis=1).mean()),
        exact_enumeration=repetitions == 1,
        monte_carlo_draws=0 if repetitions == 1 else DRAW_COUNT,
    )


def simulate_randomization(*, seed: int, trials: int = 2000) -> dict:
    """Synthetic contribution-space calibration; never reads empirical outcomes.

    Fixed magnitudes represent arbitrary scene heterogeneity, magnitude drift and
    one large observation. Independent randomized pair signs provide the null law.
    These are statistical constructions, not simulations of image-service outputs
    or a proof that actual service carryover is absent.
    """
    if not _integer(seed) or not _integer(trials, 1):
        raise ValueError("seed and trials must be nonnegative/positive integers")
    rng = np.random.default_rng(seed)
    null = [
        _synthetic_cell(rng, trials=trials, repetitions=r, scenario=s, dependence=d)
        for r in REPETITIONS
        for s in SCENARIOS
        for d in DEPENDENCE
    ]
    power = []
    for r in REPETITIONS:
        for probability in (0.65, 0.8, 0.95):
            row = _synthetic_cell(
                rng,
                trials=trials,
                repetitions=r,
                scenario="constant_magnitude",
                dependence="independent_endpoints",
                positive_probability=probability,
            )
            power.append(dict(row, positive_sign_probability=probability))
    invalid = [
        _synthetic_cell(
            rng,
            trials=trials,
            repetitions=r,
            scenario="constant_magnitude",
            dependence="independent_endpoints",
            persistent_sign=True,
        )
        for r in REPETITIONS
    ]
    return dict(
        schema_version="painter-prompt-randomization-calibration/1.0",
        seed=seed,
        rng="PCG64",
        trials_per_cell=trials,
        repetitions=list(REPETITIONS),
        endpoints=48,
        alpha=0.05,
        adjustment="Holm",
        monte_carlo_draws=DRAW_COUNT,
        exact_max_pairs=16,
        null_cells=null,
        power_diagnostics=power,
        invalid_persistent_sign_stress=invalid,
        criterion="Every prescribed valid-null cell has Wilson95 upper <= 0.065. "
        "Chosen before development/validation; invalid stress is excluded.",
        simulation_scope="Fixed contribution magnitudes and random paired assignment signs; "
        "48 independent endpoints or 16 groups of three dependent families.",
        shortcut="Exact finite weighted-Rademacher tails; conditional Monte Carlo exceedances "
        "sampled as Binomial(99999,p_exact). R1 uses the full exact tail.",
        power_scope="Sign-alignment alternatives in contribution space, not raw feature effects "
        "or a guarantee of power for generated images.",
        invalid_scope="Persistent common sign across scenes violates independent within-scene "
        "swap invariance; the expected failure is not a qualified null.",
        sources=SOURCES,
        uses_empirical_outcomes_for_tuning=False,
    )
