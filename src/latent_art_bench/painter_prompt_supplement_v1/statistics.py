"""Post-registration weighted descriptions and conditional joint-null prompt tests.

This module accepts terminal numeric rows only. It neither loads evidence nor changes
the original study's complete-grid decision. Every planned cell and pair is retained.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.statistics import transform, weighted_quantile
from latent_art_bench.painter_prompt_study_v1 import randomization
from latent_art_bench.painter_prompt_study_v1.generation import ALIASES
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS

TRANSITIONS = (("by_name", "style_instruction"), ("style_instruction", "style_aspects"))
QUANTILE_RULE = "weighted_empirical_inverse_cdf"
JOINT_NULL = (
    "joint sharp no-method-effect on availability AND measured features, with no interference "
    "across requests, conditional on third-method slots; not equal distances or feature-only null"
)
AVAILABLE = "descriptive_all_available"
UNAVAILABLE = "unavailable_missing_template"
ELIGIBLE = "conditional_joint_randomization"


def _matrices(reference, generated):
    reference, generated = np.asarray(reference, dtype=float), np.asarray(generated, dtype=float)
    if (
        reference.ndim != 2
        or generated.ndim != 2
        or not len(reference)
        or not len(generated)
        or not reference.shape[1]
        or reference.shape[1] != generated.shape[1]
        or not np.isfinite(reference).all()
        or not np.isfinite(generated).all()
    ):
        raise ValueError("expected nonempty finite reference[N,D] and generated[n,D]")
    return reference, generated


def _weights(weights, count):
    weights = np.asarray(weights, dtype=float)
    if (
        weights.shape != (count,)
        or not np.isfinite(weights).all()
        or np.any(weights < 0)
        or not np.isclose(weights.sum(), 1.0, rtol=0, atol=1e-12)
    ):
        raise ValueError("weights must be finite nonnegative probabilities summing to one")
    return weights


def weighted_energy(reference, generated, weights):
    """V-energy with a uniform finite reference and explicit generated probability mass."""
    reference, generated = _matrices(reference, generated)
    weights = _weights(weights, len(generated))
    value = (
        2 * (cdist(reference, generated).mean(axis=0) @ weights)
        - cdist(reference, reference).mean()
        - weights @ cdist(generated, generated) @ weights
    )
    if not np.isfinite(value):
        raise ValueError("nonfinite weighted energy")
    return float(value)


def paired_energy_contributions(reference, before, after, weights):
    """Coefficients for complementary pair swaps with identical fixed weights per method.

    Their sum equals weighted V-energy(after, reference) minus V-energy(before, reference).
    Pair eligibility and weights must be invariant to swapping the complete joint outcomes.
    """
    reference, before = _matrices(reference, before)
    _, after = _matrices(reference, after)
    if before.shape != after.shape:
        raise ValueError("paired methods require identical array shapes")
    weights = _weights(weights, len(before))
    pooled = np.concatenate([before, after])
    reference_means = cdist(pooled, reference).mean(axis=1)
    pooled_rows = cdist(pooled, pooled) @ np.tile(weights, 2)
    n = len(before)
    result = weights * (
        2 * (reference_means[n:] - reference_means[:n]) - (pooled_rows[n:] - pooled_rows[:n])
    )
    if not np.isfinite(result).all():
        raise ValueError("nonfinite weighted contributions")
    return result


def _validate(real, rows, scaler, repetitions):
    if type(repetitions) is not int or repetitions not in (1, 2, 4):
        raise ValueError("expected the registered one, two or four repetitions")
    if set(real) != set(PAINTER_IDS):
        raise ValueError("the finite reference requires all four painters")
    references = {p: np.asarray(real[p], dtype=float) for p in PAINTER_IDS}
    if any(
        x.ndim != 2 or x.shape[1] != 31 or not len(x) or not np.isfinite(x).all()
        for x in references.values()
    ):
        raise ValueError("reference features must be finite [N,31] arrays")
    if (
        np.shape(scaler["center"]) != (31,)
        or np.shape(scaler["scale"]) != (31,)
        or not np.isfinite(scaler["center"]).all()
    ):
        raise ValueError("the frozen scaler must have exactly 31 coordinates")
    # Validate the scaler even when no request yielded measured features.
    transform(np.zeros((1, 31)), scaler)
    expected = {
        (a, m, c, b, t)
        for a in ALIASES
        for m in METHOD_IDS
        for c in CONDITIONS
        for b in range(repetitions)
        for t in TEMPLATE_IDS
    }
    keys = [
        (r["alias"], r["method_id"], r["condition"], r["block"], r["template_id"]) for r in rows
    ]
    if (
        len(keys) != len(expected)
        or set(keys) != expected
        or any(type(r["block"]) is not int for r in rows)
        or any(type(r["request_sequence"]) is not int for r in rows)
        or {r["request_sequence"] for r in rows} != set(range(len(expected)))
        or any(
            not isinstance(r["request_id"], str)
            or not r["request_id"]
            or r["image_id"] != r["request_id"]
            for r in rows
        )
        or len({r["request_id"] for r in rows}) != len(expected)
        or any(r["status"] not in {"measured", "failed", "not_generated"} for r in rows)
    ):
        raise ValueError(
            "terminal request inventory or dispositions differ from the registered grid"
        )
    values = {}
    for row in rows:
        if row["status"] == "measured":
            if np.shape(row["values"]) != (31,) or not np.isfinite(row["values"]).all():
                raise ValueError("measured features must contain exactly 31 finite raw values")
            values[row["request_id"]] = transform(np.asarray(row["values"], dtype=float), scaler)
        elif "values" in row:
            raise ValueError("unmeasured disposition cannot carry a measured feature vector")
    return references, dict(zip(keys, rows)), values


def compute(real, rows, scaler, repetitions, *, permutation_seed, permutation_draws=99999):
    """Return complete descriptive and exploratory inventories from all terminal dispositions."""
    real, inventory, values = _validate(real, rows, scaler, repetitions)
    randomization.endpoint_seed(permutation_seed, 0)
    if type(permutation_draws) is not int or permutation_draws < 1:
        raise ValueError("permutation draws must be a positive integer")
    distances, absolute, coordinates, contrasts, pair_support, scenes, secondary, time = (
        [] for _ in range(8)
    )
    distance_lookup = {}
    reference_quantiles = {
        p: np.array(
            [
                weighted_quantile(x[:, i], np.ones(len(x), dtype=int), [0.25, 0.5, 0.75])
                for i in range(31)
            ]
        )
        for p, x in real.items()
    }
    for alias in ALIASES:
        for method in METHOD_IDS:
            for condition in CONDITIONS:
                measured = [
                    inventory[alias, method, condition, b, t]
                    for b in range(repetitions)
                    for t in TEMPLATE_IDS
                    if inventory[alias, method, condition, b, t]["status"] == "measured"
                ]
                counts = Counter(r["template_id"] for r in measured)
                missing = [t for t in TEMPLATE_IDS if not counts[t]]
                status = UNAVAILABLE if missing else AVAILABLE
                if not missing:
                    array = np.array([values[r["request_id"]] for r in measured])
                    weights = np.array([1 / (16 * counts[r["template_id"]]) for r in measured])
                    # Integer masses preserve exact CDF boundaries for counts in {1,2,3,4}.
                    quantile_mass = np.array([12 // counts[r["template_id"]] for r in measured])
                for family, section in features.FAMILIES.items():
                    for painter in PAINTER_IDS:
                        value = (
                            None
                            if missing
                            else weighted_energy(
                                real[painter][:, section], array[:, section], weights
                            )
                        )
                        row = dict(
                            alias=alias,
                            method_id=method,
                            condition=condition,
                            painter_id=painter,
                            family=family,
                            distance=value,
                            generated_count=len(measured),
                            reference_count=len(real[painter]),
                            missing_templates=missing,
                            status=status,
                        )
                        distances.append(row)
                        distance_lookup[alias, method, condition, painter, family] = value
                        if condition == painter:
                            absolute.append(
                                dict(
                                    alias=alias,
                                    method_id=method,
                                    painter_id=painter,
                                    family=family,
                                    finite_distance=value,
                                    generated_count=len(measured),
                                    missing_templates=missing,
                                    status=status,
                                )
                            )
                if condition in PAINTER_IDS:
                    for family, section in features.FAMILIES.items():
                        for i in range(section.start, section.stop):
                            reference_q = reference_quantiles[condition][i]
                            reference_iqr = float(reference_q[2] - reference_q[0])
                            q = (
                                None
                                if missing
                                else weighted_quantile(
                                    array[:, i], quantile_mass, [0.25, 0.5, 0.75]
                                )
                            )
                            generated_iqr = None if missing else float(q[2] - q[0])
                            coordinates.append(
                                dict(
                                    alias=alias,
                                    method_id=method,
                                    painter_id=condition,
                                    family=family,
                                    coordinate=features.NAMES[i],
                                    status=status,
                                    missing_templates=missing,
                                    reference_median=float(reference_q[1]),
                                    reference_iqr=reference_iqr,
                                    generated_median=None if missing else float(q[1]),
                                    generated_iqr=generated_iqr,
                                    median_difference=None
                                    if missing
                                    else float(q[1] - reference_q[1]),
                                    iqr_ratio=(
                                        generated_iqr / reference_iqr
                                        if not missing and reference_iqr > 0
                                        else None
                                    ),
                                )
                            )
    for alias in ALIASES:
        for painter in PAINTER_IDS:
            support_by_transition = {}
            for before, after in TRANSITIONS:
                candidates = [
                    (
                        inventory[alias, before, painter, b, t],
                        inventory[alias, after, painter, b, t],
                    )
                    for b in range(repetitions)
                    for t in TEMPLATE_IDS
                ]
                counts = Counter(
                    a["template_id"]
                    for a, b in candidates
                    if a["status"] == b["status"] == "measured"
                )
                missing = [t for t in TEMPLATE_IDS if not counts[t]]
                support = []
                for earlier, later in candidates:
                    both = earlier["status"] == later["status"] == "measured"
                    included = both and not missing
                    support.append(
                        dict(
                            alias=alias,
                            painter_id=painter,
                            before=before,
                            after=after,
                            block=earlier["block"],
                            template_id=earlier["template_id"],
                            before_request_id=earlier["request_id"],
                            after_request_id=later["request_id"],
                            before_status=earlier["status"],
                            after_status=later["status"],
                            before_request_sequence=earlier["request_sequence"],
                            after_request_sequence=later["request_sequence"],
                            order_sequence=min(
                                earlier["request_sequence"], later["request_sequence"]
                            ),
                            both_measured=both,
                            included=included,
                            weight=1 / (16 * counts[earlier["template_id"]]) if included else 0.0,
                        )
                    )
                pair_support.extend(support)
                support_by_transition[before, after] = support, missing
            for family, section in features.FAMILIES.items():
                for before, after in TRANSITIONS:
                    label = dict(
                        alias=alias, painter_id=painter, family=family, before=before, after=after
                    )
                    support, missing = support_by_transition[before, after]
                    chosen = [r for r in support if r["included"]]
                    entry = dict(
                        **label,
                        pairs=len(chosen),
                        both_measured_pairs=sum(r["both_measured"] for r in support),
                        missing_templates=missing,
                        before_distance=None,
                        after_distance=None,
                        estimate=None,
                        status=UNAVAILABLE,
                        raw_p=None,
                        holm_p=None,
                        reject_holm=False,
                        holm_input=1.0,
                    )
                    coefficients = {}
                    if not missing:
                        first = np.array([values[r["before_request_id"]][section] for r in chosen])
                        second = np.array([values[r["after_request_id"]][section] for r in chosen])
                        weights = np.array([r["weight"] for r in chosen])
                        x = real[painter][:, section]
                        contribution = paired_energy_contributions(x, first, second, weights)
                        inferred = randomization.randomization_pvalue(
                            contribution,
                            seed=randomization.endpoint_seed(permutation_seed, len(contrasts)),
                            draws=permutation_draws,
                        )
                        entry.update(
                            inferred,
                            before_distance=weighted_energy(x, first, weights),
                            after_distance=weighted_energy(x, second, weights),
                            status=ELIGIBLE,
                            null=JOINT_NULL,
                            holm_input=inferred["raw_p"],
                        )
                        coefficients = {
                            (r["block"], r["template_id"]): float(c)
                            for r, c in zip(chosen, contribution)
                        }
                    contrasts.append(entry)
                    entries = [
                        dict(
                            r,
                            family=family,
                            status=entry["status"],
                            contribution=coefficients.get((r["block"], r["template_id"])),
                        )
                        for r in support
                    ]
                    entries.sort(key=lambda r: r["order_sequence"])
                    scenes.extend(entries)
                    ordered = np.array([r["contribution"] for r in entries if r["included"]])
                    midpoint = len(ordered) // 2
                    time.append(
                        dict(
                            **label,
                            status=entry["status"],
                            included_pairs=len(ordered),
                            first_half_mean=float(ordered[:midpoint].mean())
                            if len(ordered)
                            else None,
                            second_half_mean=float(ordered[midpoint:].mean())
                            if len(ordered)
                            else None,
                            contribution_sd=float(ordered.std(ddof=1)) if len(ordered) else None,
                            interpretation="descriptive slot order; does not test no interference",
                        )
                    )
                    selected = [
                        distance_lookup[alias, method, condition, painter, family]
                        for condition in (painter, "artist_free")
                        for method in (before, after)
                    ]
                    estimate = (
                        None
                        if any(v is None for v in selected)
                        else (selected[1] - selected[0]) - (selected[3] - selected[2])
                    )
                    secondary.append(
                        dict(
                            **label,
                            endpoint="control_adjusted_transition",
                            estimate=estimate,
                            support="all_available_equal_template",
                            status=UNAVAILABLE if estimate is None else AVAILABLE,
                        )
                    )
                first = distance_lookup[alias, "by_name", painter, painter, family]
                last = distance_lookup[alias, "style_aspects", painter, painter, family]
                estimate = None if first is None or last is None else last - first
                secondary.append(
                    dict(
                        alias=alias,
                        painter_id=painter,
                        family=family,
                        before="by_name",
                        after="style_aspects",
                        endpoint="overall_transition",
                        estimate=estimate,
                        support="all_available_equal_template",
                        status=UNAVAILABLE if estimate is None else AVAILABLE,
                    )
                )
    adjusted = randomization.holm([r["holm_input"] for r in contrasts])
    for row, value in zip(contrasts, adjusted):
        if row["status"] == ELIGIBLE:
            row["holm_p"] = float(value)
            row["reject_holm"] = bool(value <= 0.05)
    return dict(
        distances=distances,
        absolute=absolute,
        coordinates=coordinates,
        exploratory_contrasts=contrasts,
        pair_support=pair_support,
        scene_contributions=scenes,
        secondary=secondary,
        time_diagnostics=time,
        inference=dict(
            method="post_registration_paired_joint_randomization",
            alpha=0.05,
            multiplicity="Holm",
            family_size=48,
            endpoint_count=48,
            eligible_endpoints=sum(r["status"] == ELIGIBLE for r in contrasts),
            permutation_seed=permutation_seed,
            permutation_draws=permutation_draws,
            confidence_intervals=False,
            null=JOINT_NULL,
            quantile_rule=QUANTILE_RULE,
            weights="equal mass1/16 per template; uniform within available or common-pair template",
            unavailable_holm_rule="input1 reserves the family; reported p-values remain null",
            scope="post-registration supplement; original registered primary is not restored",
        ),
    )
