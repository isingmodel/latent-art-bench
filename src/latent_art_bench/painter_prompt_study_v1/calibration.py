"""Synthetic-only coverage and precision planning; never load empirical artwork features.

The finite-support generators allow exact population truths for energy kernels.
The rare-outlier scenario is a finite contamination stress test, not a mathematical
heavy-tailed distribution. Failure is retained; no sample size is selected automatically.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from scipy.stats import chi2, t

from .statistics import energy_kernel

FAMILIES = {"color": slice(0, 11), "spatial": slice(11, 19), "texture": slice(19, 31)}
SCENARIOS = ("null", "shift", "dispersion", "rare_outlier")
SOURCES = [
    "https://doi.org/10.1016/j.jspi.2013.03.018",
    "https://www.jmlr.org/papers/volume13/gretton12a/gretton12a.pdf#page=17",
    "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm",
]


def wilson(successes: int, total: int) -> list[float]:
    if total < 1 or not 0 <= successes <= total:
        raise ValueError("invalid binomial accounting")
    z = 1.959963984540054
    probability, denominator = successes / total, 1 + z * z / total
    center = (probability + z * z / (2 * total)) / denominator
    half = z * np.sqrt(probability * (1 - probability) / total + z * z / (4 * total**2))
    return [float(center - half / denominator), float(center + half / denominator)]


def synthetic_kernels(scenario: str, *, seed: int = 20260906, states: int = 16) -> dict:
    """Two aliases x four painters x three methods x three families; shared finite states.

    Each state supplies one complete 16-template block. Permuted state assignments
    induce cross-condition dependence without assuming shared remote generation seeds.
    This is one specified dependence construction, not a service model validation.
    """
    if scenario not in SCENARIOS or states < 4:
        raise ValueError("unknown scenario or fewer than four states")
    rng = np.random.Generator(np.random.PCG64(seed))
    probabilities = np.full(states, 1 / states)
    if scenario == "rare_outlier":
        probabilities[:] = 0.99 / (states - 1)
        probabilities[-1] = 0.01
    kernels, labels, cache = [], [], {}
    for painter in range(4):
        base = rng.normal(size=(states, 16, 31)) + 0.3 * rng.normal(size=(states, 1, 31))
        reference = base.reshape(-1, 31)
        for alias in range(2):
            for method in range(3):
                generated = base[rng.permutation(states)].copy()
                if scenario == "shift":
                    generated += (0.5, 0.25, 0.1)[method]
                elif scenario == "dispersion":
                    generated *= (1.6, 1.25, 1.0)[method]
                elif scenario == "rare_outlier":
                    generated[-1] += (20.0, 10.0, 5.0)[method]
                for family, section in FAMILIES.items():
                    kernel = energy_kernel(reference[:, section], generated[:, :, section])
                    cache[alias, painter, method, family] = kernel
                    kernels.append(kernel)
                    labels.append(dict(alias=alias, painter=painter, method=method, family=family))
    contrasts, contrast_labels, contrast_indices = [], [], []
    positions = {(r["alias"], r["painter"], r["method"], r["family"]): i
                 for i, r in enumerate(labels)}
    for alias in range(2):
        for painter in range(4):
            for method in (1, 2):
                for family in FAMILIES:
                    contrasts.append(cache[alias, painter, method, family]
                                     - cache[alias, painter, method - 1, family])
                    contrast_labels.append(dict(
                        alias=alias, painter=painter, method=method,
                        baseline=method - 1, family=family))
                    contrast_indices.append((positions[alias, painter, method, family],
                                             positions[alias, painter, method - 1, family]))
    return dict(probabilities=probabilities, distances=np.array(kernels), distance_labels=labels,
                contrasts=np.array(contrasts), contrast_labels=contrast_labels,
                contrast_indices=contrast_indices)


def _trial_moments(kernels, indices, method):
    """Vectorized trials against small exact-support kernels, without image-sized arrays."""
    trials, repetitions = indices.shape
    endpoints, states, _ = kernels.shape
    if method == "paired_t":
        values = kernels[:, indices[:, ::2], indices[:, 1::2]].transpose(1, 2, 0)
        return values.mean(axis=1), values.std(axis=1, ddof=1) / np.sqrt(repetitions // 2)
    counts = np.stack([np.bincount(row, minlength=states) for row in indices])
    diagonal = np.diagonal(kernels, axis1=1, axis2=2)
    row_sums = np.einsum("bij,tj->tbi", kernels, counts, optimize=True) - diagonal[None, :, :]
    total = np.einsum("tbi,ti->tb", row_sums, counts, optimize=True)
    point = total / (repetitions * (repetitions - 1))
    pseudo = (2 * (repetitions - 1) * row_sums - total[:, :, None]) / (
        (repetitions - 1) * (repetitions - 2))
    variance = np.einsum("tbi,ti->tb", (pseudo - point[:, :, None])**2, counts, optimize=True)
    return point, np.sqrt(variance / (repetitions * (repetitions - 1)))


def _trial_units(kernels, indices, method):
    """Materialize pair observations or jackknife pseudovalues for a small condition group."""
    if method == "paired_t":
        return kernels[:, indices[:, ::2], indices[:, 1::2]].transpose(1, 2, 0)
    repetitions = indices.shape[1]
    counts = np.stack([np.bincount(row, minlength=kernels.shape[1]) for row in indices])
    diagonal = np.diagonal(kernels, axis1=1, axis2=2)
    rows = np.einsum("eij,tj->tei", kernels, counts, optimize=True) - diagonal[None, :, :]
    total = np.einsum("tei,ti->te", rows, counts, optimize=True)
    pseudo = (2 * (repetitions - 1) * rows - total[:, :, None]) / (
        (repetitions - 1) * (repetitions - 2))
    return np.take_along_axis(pseudo, indices[:, None, :], axis=2).transpose(0, 2, 1)


def _independent_moments(population, inventory, indices, method):
    groups = {}
    for i, row in enumerate(population["distance_labels"]):
        groups.setdefault((row["alias"], row["painter"], row["method"]), []).append(i)
    example = next(iter(indices.values()))
    units = example.shape[1] // 2 if method == "paired_t" else example.shape[1]
    values = np.zeros((example.shape[0], units, len(population[inventory])))
    for group, columns in groups.items():
        partial = _trial_units(population["distances"][columns], indices[group], method)
        if inventory == "distances":
            values[:, :, columns] = partial
        else:
            for endpoint, (left, right) in enumerate(population["contrast_indices"]):
                for sign, column in ((1, left), (-1, right)):
                    if column in columns:
                        values[:, :, endpoint] += sign * partial[:, :, columns.index(column)]
    return values.mean(axis=1), values.std(axis=1, ddof=1) / np.sqrt(units)


def normal_precision_plan(*, pair_counts=(10, 25, 50, 100), family_sizes=(48, 72),
                          effects=(0.5, 0.8, 1.0), alpha=0.05) -> list[dict]:
    """Exact noncentral-t marginal power under NORMAL IID pair contributions only.

    Effect is mean contrast / pair-contribution SD, not an artwork-coordinate shift.
    Power is endpoint-specific at the simultaneous interval cutoff, not joint power.
    """
    rows = []
    for pairs in pair_counts:
        if pairs < 2:
            raise ValueError("at least two pairs are required")
        for family_size in family_sizes:
            critical = float(t.ppf(1 - alpha / (2 * family_size), pairs - 1))
            for effect in effects:
                noncentrality = effect * np.sqrt(pairs)
                # Integrate the normal/chi-square representation directly: this avoids
                # noncentral-t CDF implementations returning NaN in a negligible tail.
                def integrand(variance):
                    threshold = critical * np.sqrt(variance / (pairs - 1))
                    tails = ndtr(-threshold - noncentrality) + ndtr(noncentrality - threshold)
                    return tails * chi2.pdf(variance, pairs - 1)

                power = quad(integrand, 0, np.inf, epsabs=1e-10)[0]
                rows.append(dict(
                    pairs=pairs, full_repetitions=2 * pairs, requests=960 * pairs,
                    family_size=family_size, standardized_effect=effect,
                    half_width_over_observed_pair_sd=critical / np.sqrt(pairs),
                    normal_theory_marginal_power=float(power),
                ))
    return rows


def simulate(*, trials=1000, pair_counts=(10, 25, 50, 100), seed=20260906,
             states=16, alpha=0.05, dependence="shared_state") -> dict:
    if trials < 1 or any(pairs < 2 for pairs in pair_counts) or not 0 < alpha < 1:
        raise ValueError("invalid simulation design")
    if dependence not in {"shared_state", "independent_conditions"}:
        raise ValueError("unknown synthetic dependence construction")
    rng = np.random.Generator(np.random.PCG64(seed + 1))
    output = []
    for scenario in SCENARIOS:
        population = synthetic_kernels(scenario, seed=seed, states=states)
        probabilities = population["probabilities"]
        for inventory in ("contrasts", "distances"):
            kernels = population[inventory]
            truth = np.einsum("i,eij,j->e", probabilities, kernels, probabilities)
            pair_variance = np.einsum(
                "i,eij,j->e", probabilities, (kernels - truth[:, None, None])**2, probabilities)
            projection = np.einsum("eij,j->ei", kernels, probabilities) - truth[:, None]
            first_order_variance = (projection**2) @ probabilities
            if dependence == "independent_conditions" and inventory == "contrasts":
                distance_truth = np.einsum(
                    "i,eij,j->e", probabilities, population["distances"], probabilities)
                centered = population["distances"] - distance_truth[:, None, None]
                distance_variance = np.einsum("i,eij,j->e", probabilities, centered**2,
                                              probabilities)
                projection = np.einsum("eij,j->ei", centered, probabilities)
                projection_variance = (projection**2) @ probabilities
                pair_variance = np.array([distance_variance[a] + distance_variance[b]
                                          for a, b in population["contrast_indices"]])
                first_order_variance = np.array([
                    projection_variance[a] + projection_variance[b]
                    for a, b in population["contrast_indices"]])
            nondegenerate = pair_variance > 1e-24
            for pairs in pair_counts:
                repetitions = 2 * pairs
                if dependence == "shared_state":
                    indices = rng.choice(states, size=(trials, repetitions), p=probabilities)
                else:
                    groups = sorted({(r["alias"], r["painter"], r["method"])
                                     for r in population["distance_labels"]})
                    indices = {group: rng.choice(states, size=(trials, repetitions),
                                                 p=probabilities) for group in groups}
                for method in ("paired_t", "jackknife_t"):
                    units = pairs if method == "paired_t" else repetitions
                    if dependence == "shared_state":
                        point, standard_error = _trial_moments(kernels, indices, method)
                    else:
                        point, standard_error = _independent_moments(
                            population, inventory, indices, method)
                    critical = float(t.ppf(1 - alpha / (2 * len(kernels)), units - 1))
                    half = critical * standard_error
                    valid = standard_error * np.sqrt(units) > 1e-12
                    covered = valid & (point - half <= truth + 1e-12)
                    covered &= point + half >= truth - 1e-12
                    joint = covered[:, nondegenerate].all(axis=1)
                    complete = covered.all(axis=1)
                    output.append(dict(
                        scenario=scenario, inventory=inventory, method=method,
                        family_size=len(kernels), pairs=pairs, full_repetitions=repetitions,
                        requests=480 * repetitions, trials=trials,
                        population_degenerate_endpoints=int((~nondegenerate).sum()),
                        u_first_order_degenerate_endpoints=int(
                            (first_order_variance < 1e-24).sum()),
                        trials_with_any_zero_sample_variance=int((~valid).any(axis=1).sum()),
                        joint_coverage_nondegenerate=float(joint.mean()),
                        joint_coverage_mc_wilson_95=wilson(int(joint.sum()), trials),
                        complete_inventory_coverage=float(complete.mean()),
                        worst_endpoint_coverage=float(covered.mean(axis=0).min()),
                        maximum_absolute_mc_bias=float(np.max(abs(point.mean(axis=0) - truth))),
                        median_worst_endpoint_half_width=float(np.median(half.max(axis=1))),
                        endpoint_truth_and_precision=[dict(
                            label, truth=float(value),
                            pair_contribution_sd=float(np.sqrt(variance)),
                            exact_pair_mean_sd=float(np.sqrt(variance / pairs)),
                            exact_complete_u_sd=float(np.sqrt(
                                (4 * (repetitions - 2) * first_order_variance[i] + 2 * variance)
                                / (repetitions * (repetitions - 1)))),
                            median_half_width=float(np.median(half[:, i])),
                            coverage=float(covered[:, i].mean()),
                        ) for i, (label, value, variance) in enumerate(zip(
                            population["contrast_labels" if inventory == "contrasts"
                                       else "distance_labels"], truth, pair_variance))],
                    ))
    return dict(
        schema_version="painter-prompt-calibration/1.0", seed=seed, rng="PCG64",
        dependence=dependence,
        trials_per_cell=trials, pair_counts=list(pair_counts), source_states=states,
        templates=16, coordinates=31, aliases=2, methods=3, painters=4,
        requests_per_full_repetition=480, nominal_family_coverage=1 - alpha,
        scenarios=output, normal_precision_plan=normal_precision_plan(
            pair_counts=pair_counts, alpha=alpha), sources=SOURCES,
        selection="No automatic sample-size selection or coverage guarantee",
        limitations=[
            "Exact truths are conditional on these artificial finite-support populations.",
            "Monte Carlo coverage diagnoses the specified construction, not all generators.",
            "Rare-outlier contamination has finite support, not an unbounded heavy tail.",
            "Complete-block U jackknife can be unreliable at or near degeneracy.",
            "Pair t needs independent stationary pairs and finite variance; no seed is assumed.",
            "Normal-theory power is marginal per endpoint, not simultaneous power.",
            "No empirical painter or generated-image feature data were read or used for tuning.",
        ],
    )
