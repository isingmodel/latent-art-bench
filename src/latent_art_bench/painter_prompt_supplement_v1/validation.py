"""Synthetic-only validation of the explicitly post-registration missingness supplement.

The exhaustive oracle allocates all three methods before filtering and weighting.
The larger FWER experiment is a contribution-space conditional-sign construction,
not a simulation of images, moderation, or a remote service. Its efficient exact-tail
shortcut is kept separate from checks of the actual randomization engine.
"""

from __future__ import annotations

import itertools
from functools import lru_cache

import numpy as np

from latent_art_bench.painter_prompt_study_v1.calibration import wilson
from latent_art_bench.painter_prompt_study_v1.randomization import (
    DRAW_COUNT,
    holm,
    randomization_pvalue,
)
from latent_art_bench.painter_prompt_study_v1.randomization import (
    paired_energy_contributions as uniform_contributions,
)

CASE_IDS = ("full64_drift", "one63_large_contribution", "severe40", "unavailable_template")
DEPENDENCE_IDS = ("independent_endpoints", "shared_three_family_signs")
ORACLE_IDS = (
    "weighted_energy_swaps",
    "uniform_weight_reduction",
    "ties_and_zero",
    "conditional_triplet_allocations",
    "unavailable_template",
)
DEVELOPMENT_SEED, VALIDATION_SEED = 20260910, 20260911
TRIALS = 2000
CRITERION = (
    "Every prescribed valid-null cell in development and unseen-seed validation has "
    "a Wilson 95% upper bound <= 0.065 for FWER over all 48 hypotheses. "
    "All independent numerical/allocation oracles must pass. No retuning if a cell fails."
)


def _energy_oracle(reference, generated, weights):
    """Direct finite weighted double sums; independent of the coefficient identity."""
    cross = sum(
        w * np.linalg.norm(x - y) for x, w in zip(generated, weights) for y in reference
    ) / len(reference)
    real = sum(np.linalg.norm(x - y) for x in reference for y in reference) / len(reference) ** 2
    within = sum(
        w * v * np.linalg.norm(x - y)
        for x, w in zip(generated, weights)
        for y, v in zip(generated, weights)
    )
    return float(2 * cross - real - within)


def _template_weights(template_ids, template_count):
    counts = np.bincount(template_ids, minlength=template_count)
    if len(counts) != template_count or np.any(counts == 0):
        return None
    return 1 / (template_count * counts[template_ids])


def _assigned_pairs(slots, available, assignments, before, after, templates, template_count):
    """Rebuild support from counterfactual assignments, never relabel a prefiltered table."""
    positions = np.argsort(np.asarray(assignments), axis=1)
    units = np.arange(len(slots))
    keep = available[units, positions[:, before]] & available[units, positions[:, after]]
    weights = _template_weights(templates[keep], template_count)
    if weights is None:
        return None
    selected = units[keep]
    return (
        slots[selected, positions[keep, before]],
        slots[selected, positions[keep, after]],
        weights,
        keep,
    )


def _triplet_oracle(reference, rng):
    from .statistics import paired_energy_contributions

    # Two toy scenes, two repetitions each. Each scene retains an always-available
    # triplet; another triplet has one unavailable *fixed slot*, irrespective of label.
    slots = rng.normal(size=(4, 3, 3)) + np.arange(4)[:, None, None] * 2
    available = np.ones((4, 3), dtype=bool)
    available[0, 2], available[2, 1] = False, False
    templates = np.array([0, 0, 1, 1])
    permutations = list(itertools.permutations(range(3)))
    strata, allocations, maximum_error, maximum_anti = 0, 0, 0.0, 0.0
    patterns = set()
    for before, after, third in ((0, 1, 2), (1, 2, 0)):
        for third_positions in itertools.product(range(3), repeat=4):
            allowed = [[p for p in permutations if p[slot] == third] for slot in third_positions]
            observed = []
            for assignment in itertools.product(*allowed):
                pair = _assigned_pairs(slots, available, assignment, before, after, templates, 2)
                if pair is None:
                    raise ValueError("always-available anchors unexpectedly lost a toy template")
                a, b, weights, keep = pair
                statistic = _energy_oracle(reference, b, weights) - _energy_oracle(
                    reference, a, weights
                )
                coefficients = paired_energy_contributions(reference, a, b, weights)
                pvalue = randomization_pvalue(coefficients, seed=20260910)["raw_p"]
                pattern = tuple(keep), tuple(weights)
                patterns.add(pattern)
                observed.append((statistic, pvalue, pattern))
                maximum_error = max(maximum_error, abs(statistic - float(coefficients.sum())))
                allocations += 1
            if len(observed) != 16 or len({row[2] for row in observed}) != 1:
                raise ValueError("conditional complete-case mask/weights changed under allocation")
            statistics = np.abs([row[0] for row in observed])
            pvalues = np.array([row[1] for row in observed])
            for statistic, pvalue, _ in observed:
                direct_p = float(np.mean(statistics >= abs(statistic) - 1e-12))
                maximum_error = max(maximum_error, abs(pvalue - direct_p))
            for cutoff in np.unique(pvalues):
                maximum_anti = max(maximum_anti, float(np.mean(pvalues <= cutoff) - cutoff))
            strata += 1
    missing_template = available.copy()
    missing_template[2:] = False
    excluded = _assigned_pairs(slots, missing_template, [(0, 1, 2)] * 4, 0, 1, templates, 2) is None
    return dict(
        conditioning_strata=strata,
        full_triplet_allocations=allocations,
        distinct_weight_support_patterns=len(patterns),
        maximum_error=maximum_error,
        maximum_conditional_cdf_minus_alpha=maximum_anti,
        unavailable_template_is_ineligible=excluded,
    )


def validate_oracles() -> dict:
    """Return deterministic independent numerical and actual-allocation checks."""
    from .statistics import paired_energy_contributions, weighted_energy

    rng = np.random.default_rng(20260910)
    reference, a, b = rng.normal(size=(11, 5)), rng.normal(size=(7, 5)), rng.normal(size=(7, 5))
    weights = np.array([1 / 9] * 3 + [1 / 6] * 4)
    coefficients = paired_energy_contributions(reference, a, b, weights)
    maximum_error, count = 0.0, 0
    for signs in itertools.product((-1, 1), repeat=len(a)):
        signs = np.asarray(signs)
        before, after = np.where(signs[:, None] > 0, a, b), np.where(signs[:, None] > 0, b, a)
        before_direct, after_direct = (
            _energy_oracle(reference, values, weights) for values in (before, after)
        )
        maximum_error = max(
            maximum_error,
            abs(after_direct - before_direct - float(signs @ coefficients)),
            abs(weighted_energy(reference, before, weights) - before_direct),
            abs(weighted_energy(reference, after, weights) - after_direct),
        )
        count += 1
    uniform_error = float(
        np.max(
            np.abs(
                paired_energy_contributions(reference, a, b, np.ones(len(a)) / len(a))
                - uniform_contributions(reference, a, b)
            )
        )
    )
    ties = [
        randomization_pvalue(values, seed=20260910)["raw_p"]
        for values in (np.zeros(16), np.tile([1.0, -1.0], 8))
    ]
    triplet = _triplet_oracle(rng.normal(size=(7, 3)), rng)
    checks = [
        dict(
            id="weighted_energy_swaps",
            passed=maximum_error <= 1e-12,
            assignments=count,
            maximum_absolute_error=maximum_error,
        ),
        dict(
            id="uniform_weight_reduction",
            passed=uniform_error <= 1e-12,
            maximum_absolute_error=uniform_error,
        ),
        dict(id="ties_and_zero", passed=ties == [1.0, 1.0], pvalues=ties),
        dict(
            id="conditional_triplet_allocations",
            passed=triplet["maximum_error"] <= 1e-12
            and triplet["maximum_conditional_cdf_minus_alpha"] <= 1e-12,
            **triplet,
        ),
        dict(id="unavailable_template", passed=triplet["unavailable_template_is_ineligible"]),
    ]
    return dict(
        schema_version="painter-prompt-supplement-oracles/1.0",
        overall="PASS" if all(row["passed"] for row in checks) else "FAIL",
        seed=20260910,
        checks=checks,
        scope="Independent direct weighted energy sums and full triplet allocations "
        "with selection and weights rebuilt after every counterfactual assignment.",
        empirical_outcomes_used=False,
    )


def _case(case):
    if case not in CASE_IDS:
        raise ValueError("unknown supplemental synthetic support case")
    counts = np.array(
        [3] + [4] * 15
        if case == "one63_large_contribution"
        else [1, 2, 3, 4] * 4
        if case == "severe40"
        else [4] * 16
    )
    templates = np.repeat(np.arange(16), counts)
    weights = _template_weights(templates, 16)
    # For m in1,2,3,4, 1/(16*m) is an integer multiple of1/192.
    integer_weights = np.rint(weights * 192).astype(int)
    if not np.allclose(integer_weights / 192, weights, rtol=0, atol=1e-15):
        raise ValueError("synthetic template weight is not on the declared rational grid")
    magnitudes = np.ones(len(weights), dtype=int)
    if case in ("full64_drift", "unavailable_template"):
        magnitudes += np.arange(len(weights)) % 4
    elif case == "one63_large_contribution":
        magnitudes[-1] = 20
    unavailable = [0, 1, 2] if case == "unavailable_template" else []
    return dict(
        counts=counts,
        integer_coefficients=integer_weights * magnitudes,
        template_weights=weights,
        unavailable_endpoints=unavailable,
        unavailable_template_counts=[0] + [4] * 15 if unavailable else None,
    )


@lru_cache(maxsize=32)
def _exact_tail(integer_coefficients):
    total = sum(integer_coefficients)
    mass = np.array([1.0])
    for weight in integer_coefficients:
        expanded = np.zeros(len(mass) + 2 * weight)
        expanded[: len(mass)] += mass / 2
        expanded[2 * weight : 2 * weight + len(mass)] += mass / 2
        mass = expanded
    magnitudes = np.abs(np.arange(len(mass)) - total)
    absolute_mass = np.bincount(magnitudes, weights=mass, minlength=total + 1)
    return np.minimum(1, np.cumsum(absolute_mass[::-1])[::-1])


def _null_cell(rng, case, dependence, trials):
    plan = _case(case)
    coefficients = plan["integer_coefficients"]
    groups = 48 if dependence == "independent_endpoints" else 16
    totals = np.zeros((trials, groups), dtype=int)
    for weight in np.unique(coefficients):
        count = int(np.count_nonzero(coefficients == weight))
        totals += weight * (2 * rng.binomial(count, 0.5, size=(trials, groups)) - count)
    p_exact = _exact_tail(tuple(int(v) for v in coefficients))[np.abs(totals)]
    if groups == 16:
        p_exact = np.repeat(p_exact, 3, axis=1)
    pvalues = (1 + rng.binomial(DRAW_COUNT, p_exact)) / (DRAW_COUNT + 1)
    pvalues[:, plan["unavailable_endpoints"]] = 1
    rejected = np.array([holm(row) <= 0.05 for row in pvalues])
    count = int(rejected.any(axis=1).sum())
    interval = wilson(count, trials)
    return dict(
        case=case,
        dependence=dependence,
        trials=trials,
        family_size=48,
        family_rejections=count,
        family_rejection_rate=count / trials,
        family_rejection_wilson_95=interval,
        mean_rejected_endpoints=float(rejected.sum(axis=1).mean()),
        matched_pairs_for_available_endpoints=int(plan["counts"].sum()),
        template_counts_for_available_endpoints=plan["counts"].tolist(),
        unavailable_endpoint_indices=plan["unavailable_endpoints"],
        template_counts_for_unavailable_endpoints=plan["unavailable_template_counts"],
        tested_endpoints=48 - len(plan["unavailable_endpoints"]),
        adjustment_input_for_unavailable=1,
        integer_coefficient_multiset=coefficients.tolist(),
        qualification_passes=interval[1] <= 0.065,
    )


def _adversarial_example():
    from .statistics import paired_energy_contributions

    # A possible allocation in the stratum where the third method occupies slot2.
    # The first repetition has identical zero-valued feature slots and guarantees
    # support. In later repetitions, slot0/slot1 have fixed values0/1 for ANY method.
    # Only method0 has feature-dependent availability; method1 is always available.
    templates = np.tile(np.arange(16), 4)
    blocks = np.repeat(np.arange(4), 16)
    slots = np.zeros((64, 3, 1))
    slots[blocks > 0, 1, 0] = 1
    assignments = np.array(
        [(1, 0, 2) if (t + b) % 2 == 0 else (0, 1, 2) for t, b in zip(templates, blocks)]
    )

    def available_for(allocated):
        return ~((blocks[:, None] > 0) & (allocated == 0) & (slots[:, :, 0] == 0))

    availability = available_for(assignments)
    pair = _assigned_pairs(slots, availability, assignments, 0, 1, templates, 16)
    if pair is None:
        raise ValueError("adversarial anchors unexpectedly lost template support")
    a, b, weights, keep = pair
    changed = assignments.copy()
    changed[assignments == 0], changed[assignments == 1] = 1, 0
    other = _assigned_pairs(slots, available_for(changed), changed, 0, 1, templates, 16)
    coefficients = paired_energy_contributions(np.zeros((3, 1)), a, b, weights)
    result = randomization_pvalue(coefficients, seed=20260910, draws=DRAW_COUNT)
    adjusted = float(holm(np.repeat(result["raw_p"], 48))[0])
    return dict(
        id="method_dependent_availability_unchanged_feature_potentials",
        assignment_construction="One fixed possible allocation conditional on third slot2; "
        "this is an illustrative counterexample, not a power simulation.",
        feature_potential_effect=0,
        joint_null_holds=False,
        feature_only_sharp_null_holds=True,
        observed_common_pairs=int(keep.sum()),
        mask_changes_after_counterfactual_swap=int(np.count_nonzero(keep != other[3])),
        contrast=result["estimate"],
        raw_p=result["raw_p"],
        holm48_p=adjusted,
        rejects_joint_null_at_05=adjusted <= 0.05,
        interpretation="Availability alone causes complete-case selection. Rejection concerns "
        "the false joint feature-and-availability null; it cannot establish a "
        "feature effect. This example is excluded from valid-null qualification.",
    )


def simulate(seed: int, trials: int = TRIALS) -> dict:
    """Fixed 48-hypothesis experiments with template-balanced support patterns."""
    if type(seed) is not int or seed < 0 or type(trials) is not int or trials < 1:
        raise ValueError("seed and trials must be nonnegative/positive integers")
    rng = np.random.default_rng(seed)
    cells = [
        _null_cell(rng, case, dependence, trials)
        for case in CASE_IDS
        for dependence in DEPENDENCE_IDS
    ]
    return dict(
        schema_version="painter-prompt-supplement-validation/1.0",
        seed=seed,
        rng="PCG64",
        trials_per_cell=trials,
        family_size=48,
        alpha=0.05,
        adjustment="Holm",
        permutation_draws=DRAW_COUNT,
        repetitions=4,
        template_count=16,
        cases=list(CASE_IDS),
        dependencies=list(DEPENDENCE_IDS),
        null_cells=cells,
        all_valid_null_cells_pass=all(row["qualification_passes"] for row in cells),
        adversarial_example=_adversarial_example(),
        criterion=CRITERION,
        simulation_scope="Fixed complete-pair support and exact1/(16*m_template) weights; "
        "conditional random contribution signs. These are contribution-space "
        "constructions, not simulated generated images or service moderation.",
        shortcut="Exact finite integer weighted-Rademacher convolution plus exact conditional "
        "Binomial(99999,p_exact) Monte Carlo exceedance sampling. Actual full allocation "
        "and permutation-engine oracles are separate.",
        qualification_scope="Diagnostic under joint feature-and-availability swap invariance. "
        "Neither simulation success nor the oracle establishes "
        "that service assumption.",
        uses_empirical_outcomes_for_tuning=False,
    )
