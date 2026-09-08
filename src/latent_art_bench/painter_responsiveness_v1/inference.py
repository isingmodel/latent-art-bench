"""Fixed-template factorial estimation and explicitly conditional design simulation.

The confidence intervals are approximate repeated-generation, model-based
intervals. Joint dispatch randomization is not an exact weak-interaction test.
No function in this module opens an image, calls a service, or publishes evidence.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from scipy.stats import t

from .design import ARMS, POLARITIES, TEMPLATE_COUNT, validate_schedule

PRIMARY = ("monet_minus_generic", "cezanne_minus_generic")
NOISE_PAINTERS = {"monet": "claude_monet", "cezanne": "paul_cezanne"}
ASSUMPTIONS = (
    "Conditional on the six fixed templates and their equal weights; no new-scene inference.",
    "Independent replicate blocks with stable within-template distributions; block-common "
    "additive disturbances cancel in the response interactions.",
    "Welch–Satterthwaite t inference is approximate, including under non-Gaussian noise; "
    "randomized dispatch does not make a weak zero-interaction test exact.",
    "The two primary intervals use Bonferroni allocation of the family alpha. "
    "Holm-adjusted two-sided p-values are reported separately.",
    "Any unavailable planned measurement withholds primary inference. Complete-block "
    "survivor summaries cannot identify the originally allocated response effect.",
)


def _settings(alpha, manipulation_margin):
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    if not np.isfinite(manipulation_margin) or manipulation_margin < 0:
        raise ValueError("the prespecified manipulation margin must be finite and nonnegative")


def _holm(pvalues):
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    adjusted[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return adjusted


def _contrasts(values):
    """Keep a single generic-control draw in both painter contrasts."""
    response = values[..., 1] - values[..., 0]
    kappa = response[..., 2:] - response[..., 1, None]
    tau = response[..., 2:] - response[..., 0, None]
    generic_minus_free = response[..., 1, None] - response[..., 0, None]
    return response, kappa, tau, generic_minus_free


def _mean_covariance(block_values):
    """Stratify by fixed template; do not count its fixed mean as generation noise.

    With B[j,r] the paired vector, Cov(mean_j mean_r B) is estimated by
    sum_j sample_cov_r(B[j]) / (J**2 * R). Welch degrees of freedom are computed
    separately for each coordinate from the J estimated variance contributions.
    """
    j, r, _ = block_values.shape
    means = block_values.mean(axis=1)
    centered = block_values - means[:, None, :]
    template_cov = np.einsum("jrk,jrl->jkl", centered, centered) / (r - 1)
    contributions = template_cov / (j * j * r)
    covariance = contributions.sum(axis=0)
    variances = np.diag(covariance)
    diagonal_parts = np.diagonal(contributions, axis1=1, axis2=2)
    denominator = np.square(diagonal_parts).sum(axis=0) / (r - 1)
    df = np.divide(np.square(variances), denominator, out=np.zeros_like(variances),
                   where=denominator > 0)
    return means.mean(axis=0), covariance, df, means


def _estimates(block_values, names, *, alpha, primary=False):
    mean, covariance, df, template_means = _mean_covariance(block_values)
    result = []
    for index, name in enumerate(names):
        estimate = float(mean[index])
        se = float(np.sqrt(max(0.0, covariance[index, index])))
        row = dict(contrast=name, estimate=estimate, standard_error=se,
                   welch_df=float(df[index]), template_estimates=template_means[:, index].tolist())
        if se == 0 or df[index] == 0:
            # Four identical realizations do not establish a noiseless service.
            row.update(inference_status="unavailable_zero_estimated_variance",
                       nominal_interval=None, family_interval=None, p_two_sided=None)
        else:
            critical = float(t.ppf(1 - alpha / 2, df[index]))
            row.update(inference_status="approximate_model_based",
                       nominal_interval=[estimate - critical * se, estimate + critical * se])
            if primary:
                family_critical = float(t.ppf(1 - alpha / (2 * len(PRIMARY)), df[index]))
                row.update(
                    family_interval=[estimate - family_critical * se,
                                     estimate + family_critical * se],
                    p_two_sided=float(2 * t.sf(abs(estimate) / se, df[index])),
                )
        result.append(row)
    if primary:
        # Treat a variance-degenerate endpoint conservatively in multiplicity,
        # but retain its unavailable status and never manufacture a confidence interval.
        adjusted = _holm([r["p_two_sided"] if r["p_two_sided"] is not None else 1.0
                          for r in result])
        for row, pvalue in zip(result, adjusted):
            row["p_holm"] = float(pvalue) if row["p_two_sided"] is not None else None
            row["reject_holm"] = row["p_holm"] is not None and row["p_holm"] <= alpha
    return result, covariance.tolist()


def _availability(schedule, outcomes):
    expected = {row["request_id"] for row in schedule}
    by_id = {}
    for row in outcomes:
        identity = row["request_id"]
        if identity not in expected or identity in by_id:
            raise ValueError("unknown or duplicate terminal outcome identity")
        status = row.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("every terminal outcome requires a status")
        if status == "measured":
            value = row.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("a measured outcome requires a finite scalar value")
            if not np.isfinite(value):
                raise ValueError("a measured outcome requires a finite scalar value")
        elif row.get("value") is not None:
            raise ValueError("an unavailable outcome cannot carry an analysis value")
        by_id[identity] = row
    cells = []
    for arm in ARMS:
        for polarity in POLARITIES:
            wanted = [s for s in schedule if s["arm"] == arm and s["polarity"] == polarity]
            counts = Counter(by_id.get(s["request_id"], {}).get("status", "not_recorded")
                             for s in wanted)
            cells.append(dict(arm=arm, polarity=polarity, allocated=len(wanted),
                              measured=counts.get("measured", 0),
                              statuses=dict(sorted(counts.items()))))
    return by_id, cells


def analyze_factorial(schedule, outcomes, *, alpha=0.05, manipulation_margin=0.0):
    """Analyze one recorded terminal value per slot under the complete-grid gate.

    The margin is in frozen development-scale chroma units and must be selected
    before collection. Manipulation intervals are descriptive nominal intervals;
    neither their sign nor a primary p-value establishes perceptual validity.
    """
    _settings(alpha, manipulation_margin)
    design = validate_schedule(schedule)
    by_id, availability = _availability(schedule, outcomes)
    templates, repetitions = design["templates"], design["repetitions"]
    values = np.full((len(templates), repetitions, len(ARMS), len(POLARITIES)), np.nan)
    template_index = {name: i for i, name in enumerate(templates)}
    for slot in schedule:
        outcome = by_id.get(slot["request_id"], {})
        if outcome.get("status") == "measured":
            values[template_index[slot["template_id"]], slot["repetition"],
                   ARMS.index(slot["arm"]), POLARITIES.index(slot["polarity"])] = outcome["value"]
    cells = []
    for j, template in enumerate(templates):
        for a, arm in enumerate(ARMS):
            for p, polarity in enumerate(POLARITIES):
                selected = values[j, :, a, p]
                selected = selected[np.isfinite(selected)]
                cells.append(dict(template_id=template, arm=arm, polarity=polarity,
                                  available=int(len(selected)), allocated=repetitions,
                                  mean=float(selected.mean()) if len(selected) else None,
                                  values=selected.tolist()))
    arm_means = []
    for arm in ARMS:
        for polarity in POLARITIES:
            selected = [c for c in cells if c["arm"] == arm and c["polarity"] == polarity]
            mean = (float(np.mean([c["mean"] for c in selected]))
                    if all(c["mean"] is not None for c in selected) else None)
            arm_means.append(dict(arm=arm, polarity=polarity, mean=mean,
                                  weighting="equal templates; available outputs within template"))
    complete = np.isfinite(values).all(axis=(2, 3))
    result = dict(
        design=design, alpha=alpha, manipulation_margin=manipulation_margin,
        availability=availability, cells=cells, arm_means=arm_means,
        complete_blocks_by_template={
            name: int(complete[j].sum()) for j, name in enumerate(templates)},
        assumptions=list(ASSUMPTIONS), primary_family_size=len(PRIMARY),
        nominal_interval_coverage=1 - alpha, family_interval_target_coverage=1 - alpha,
    )
    if not complete.all():
        survivors = []
        for j, template in enumerate(templates):
            if complete[j].any():
                _, kappa, tau, _ = _contrasts(values[j, complete[j]])
                survivors.append(dict(template_id=template, blocks=int(complete[j].sum()),
                                      kappa=kappa.mean(axis=0).tolist(),
                                      tau=tau.mean(axis=0).tolist()))
        result.update(
            status="primary_withheld_unavailable_planned_values", primary=None,
            complete_block_descriptive=dict(
                templates=survivors,
                kappa_equal_template=(np.mean([s["kappa"] for s in survivors], axis=0).tolist()
                                      if len(survivors) == TEMPLATE_COUNT else None),
                scope="Selected surviving complete blocks only; no p-values, intervals, "
                      "missing-at-random claim, or originally allocated causal estimand.",
            ),
        )
        return result
    response, kappa, tau, generic_minus_free = _contrasts(values)
    primary, covariance = _estimates(kappa, PRIMARY, alpha=alpha, primary=True)
    responses, _ = _estimates(response, ARMS, alpha=alpha)
    secondary, _ = _estimates(tau, ("monet_minus_free", "cezanne_minus_free"), alpha=alpha)
    generic, _ = _estimates(generic_minus_free, ("generic_minus_free",), alpha=alpha)
    checks = []
    for row in responses:
        interval = row["nominal_interval"]
        status = "uncertain"
        if interval is not None and interval[0] > manipulation_margin:
            status = "nominal_interval_above_margin"
        elif interval is not None and interval[1] <= manipulation_margin:
            status = "nominal_interval_not_above_margin"
        checks.append(dict(arm=row["contrast"], estimate=row["estimate"],
                           margin=manipulation_margin, status=status,
                           point_response_reversed=row["estimate"] < 0))
    status = ("complete_grid_approximate_inference"
              if all(r["inference_status"] == "approximate_model_based" for r in primary)
              else "complete_grid_partial_inference_zero_variance")
    result.update(status=status, primary=primary,
                  primary_covariance=covariance, responses=responses,
                  secondary_named_minus_free=secondary, generic_minus_free=generic,
                  manipulation_checks=checks,
                  interpretation="An attenuation claim additionally requires a positive generic "
                  "response, a functioning free-arm manipulation, no named-arm response reversal, "
                  "and reference/perceptual validation. Failed or uncertain checks exclude "
                  "no output.")
    return result


def retained_noise(generated_rows, *, feature_index=2, route="flux_2_max", pipeline="primary512"):
    """Extract corrected within-prompt residuals from already scaled retained vectors.

    Each historical painter/condition/brief mean is removed before pooling. For n
    repeats, sqrt(n/(n-1)) scaling makes the empirical residual distribution's
    variance equal that group's unbiased sample variance. It does not recover
    unobserved tail behavior or prove independent, stationary generation errors.
    """
    groups = defaultdict(list)
    selected_ids = set()
    for row in generated_rows:
        if row["route"] != route or row["pipeline"] != pipeline:
            continue
        if row["painter_id"] not in NOISE_PAINTERS.values():
            continue
        if row["condition"] not in ("named", "artist_free"):
            continue
        if row["image_id"] in selected_ids:
            raise ValueError("duplicate retained image identity")
        selected_ids.add(row["image_id"])
        scaled = np.asarray(row["scaled"], dtype=float)
        if (scaled.ndim != 1 or not 0 <= feature_index < len(scaled)
                or not np.isfinite(scaled[feature_index])):
            raise ValueError("invalid retained feature coordinate")
        key = row["painter_id"], row["condition"], row["brief_id"]
        groups[key].append((row["repetition"], float(scaled[feature_index])))
    pools = {arm: [] for arm in ("free", "monet", "cezanne")}
    inventory = []
    for (painter, condition, brief), rows in sorted(groups.items()):
        if len(rows) < 2 or len({r[0] for r in rows}) != len(rows):
            raise ValueError("retained noise requires at least two distinct repeats per prompt")
        x = np.asarray([r[1] for r in rows])
        residual = (x - x.mean()) * np.sqrt(len(x) / (len(x) - 1))
        arm = ("free" if condition == "artist_free" else
               next(a for a, p in NOISE_PAINTERS.items() if p == painter))
        pools[arm].extend(residual.tolist())
        inventory.append(dict(painter_id=painter, condition=condition, brief_id=brief,
                              repetitions=len(x), sample_variance=float(x.var(ddof=1))))
    if any(len(pools[arm]) < 2 for arm in pools):
        raise ValueError("both painters and both historical conditions need retained noise")
    pools["generic"] = list(pools["free"])
    return dict(
        route=route, pipeline=pipeline, feature_index=feature_index, pools=pools,
        groups=inventory, measured_images=len(selected_ids),
        marginal_variances={a: float(np.var(pools[a])) for a in ARMS},
        assumptions=[
            "New prompts, delivery versions, instruction polarities and selected templates "
            "can have different noise than these pooled historical prompts.",
            "Generic-clause noise is an unvalidated pooled artist-free proxy, not observed "
            "generic-clause FLUX data. Free and generic draws are distinct simulated requests.",
            "Historical artist-free allocations are centered separately by painter/brief; "
            "pooling them does not establish service/time equivalence.",
            "Three-repeat residual correction preserves marginal sample variance, not "
            "independence, tail fidelity, or future heteroskedasticity.",
        ],
    )


def _wilson(successes, total):
    # Fixed 95% Monte Carlo precision interval, distinct from experimental inference.
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [float(max(0, center - radius)), float(min(1, center + radius))]


def _simulation_statistics(blocks, *, alpha):
    """Vectorized counterpart of the exact estimator used by analyze_factorial."""
    _, j, r, _ = blocks.shape
    template_means = blocks.mean(axis=2)
    estimate = template_means.mean(axis=1)
    parts = blocks.var(axis=2, ddof=1) / (j * j * r)
    variance = parts.sum(axis=1)
    denominator = np.square(parts).sum(axis=1) / (r - 1)
    df = np.divide(np.square(variance), denominator, out=np.zeros_like(variance),
                   where=denominator > 0)
    se = np.sqrt(variance)
    valid = (se > 0) & (df > 0)
    statistic = np.divide(np.abs(estimate), se, out=np.zeros_like(estimate), where=valid)
    pvalues = np.where(valid, 2 * t.sf(statistic, np.maximum(df, 1)), 1.0)
    minimum = np.minimum(pvalues[:, 0], pvalues[:, 1])
    adjusted = np.maximum(pvalues, np.minimum(1, 2 * minimum[:, None]))
    rejected = adjusted <= alpha
    halfwidth = np.where(valid, t.ppf(1 - alpha / 4, np.maximum(df, 1)) * se, np.nan)
    return estimate, rejected, halfwidth, valid


def simulate_design(noise, *, seed, trials=10000, effects=None, repetitions=4, alpha=0.05):
    """Power/precision sensitivity conditional on residual proxies, not a guarantee.

    Effects are the two true named-minus-generic vivid/muted interactions in
    fixed development-scale units. The named arms and shared control are drawn
    once per simulated slot, including in partial-null multiplicity scenarios.
    """
    _settings(alpha, 0.0)
    if (isinstance(trials, bool) or not isinstance(trials, int) or trials < 100
            or isinstance(repetitions, bool) or not isinstance(repetitions, int)
            or repetitions < 2):
        raise ValueError("simulation requires at least 100 trials and two repetitions")
    if effects is None:
        effects = ((0.0, 0.0), (-0.25, -0.25), (-0.5, -0.5), (-0.75, -0.75),
                   (-0.5, 0.0), (0.0, -0.5))
    effects = np.asarray(effects, dtype=float)
    if effects.ndim != 2 or effects.shape[1] != 2 or not np.isfinite(effects).all():
        raise ValueError("effects must be a finite list of two-painter interactions")
    pools = {a: np.asarray(noise["pools"][a], dtype=float) for a in ARMS}
    if any(x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all() or x.var() <= 0
           for x in pools.values()):
        raise ValueError("each arm needs a finite nondegenerate retained noise pool")
    rng = np.random.default_rng(seed)
    # The second scenario makes common generic noise larger; the third adds
    # template, arm and polarity heteroskedasticity, without changing true means.
    scenarios = (
        ("empirical_proxy", "empirical", 1.0, False),
        ("generic_noise_x1_5", "empirical", 1.5, False),
        ("heteroskedastic_normal", "normal", 1.5, True),
    )
    results = []
    for scenario, distribution, generic_scale, heterogeneous in scenarios:
        values = np.empty((trials, TEMPLATE_COUNT, repetitions, len(ARMS), 2))
        for a, arm in enumerate(ARMS):
            shape = (trials, TEMPLATE_COUNT, repetitions, 2)
            if distribution == "empirical":
                errors = rng.choice(pools[arm] - pools[arm].mean(), size=shape)
            else:
                errors = rng.normal(0, np.std(pools[arm]), size=shape)
            if arm == "generic":
                errors *= generic_scale
            if heterogeneous:
                errors *= np.linspace(0.7, 1.8, TEMPLATE_COUNT)[None, :, None, None]
                errors *= np.array([0.8, 1.4])[None, None, None, :]
                if arm == "cezanne":
                    errors *= 1.25
            values[..., a, :] = errors
        _, null_kappa, _, _ = _contrasts(values)
        for effect in effects:
            blocks = null_kappa + effect[None, None, None, :]
            estimate, rejected, halfwidth, valid = _simulation_statistics(blocks, alpha=alpha)
            null_endpoints = effect == 0
            false_rejection = (rejected & null_endpoints[None, :]).any(axis=1)
            family_covered = ((np.abs(estimate - effect[None, :]) <= halfwidth) & valid).all(axis=1)
            count = int(false_rejection.sum())
            row = dict(
                scenario=scenario, true_interactions=effect.tolist(),
                rejection_probability=rejected.mean(axis=0).tolist(),
                rejection_probability_mc95=[_wilson(int(rejected[:, k].sum()), trials)
                                             for k in range(len(PRIMARY))],
                null_endpoint_family_error=float(false_rejection.mean()) if null_endpoints.any()
                else None,
                null_endpoint_family_error_mc95=_wilson(count, trials) if null_endpoints.any()
                else None,
                simultaneous_interval_coverage=float(family_covered.mean()),
                simultaneous_interval_coverage_mc95=_wilson(int(family_covered.sum()), trials),
                mean_bias=(estimate.mean(axis=0) - effect).tolist(),
                median_family_interval_halfwidth=np.nanmedian(halfwidth, axis=0).tolist(),
                p90_family_interval_halfwidth=np.nanquantile(halfwidth, 0.9, axis=0).tolist(),
                invalid_variance_trials=int((~valid.all(axis=1)).sum()),
            )
            results.append(row)
    return dict(
        seed=seed, trials_per_scenario=trials, repetitions=repetitions,
        planned_images=TEMPLATE_COUNT * repetitions * 8, fixed_templates=TEMPLATE_COUNT,
        alpha=alpha, primary_family=list(PRIMARY), results=results,
        scenarios=[dict(name=n, distribution=d, generic_noise_multiplier=g,
                        additional_template_arm_polarity_heteroskedasticity=h)
                   for n, d, g, h in scenarios],
        assumptions=list(ASSUMPTIONS) + list(noise.get("assumptions", [])),
        scope="All outputs available; independent simulated errors. The six templates are "
              "fixed. Hypothetical effect grid is not a perceptually meaningful threshold. "
              "Residual-proxy simulation cannot establish future service power, independence, "
              "availability or reference validity. No image generation was performed.",
    )
