"""Fixed, post-result diagnostics on retained numeric vectors only.

No pixel access, estimator tuning, population intervals, or new hypothesis tests
occur here. All metric views and deletion rules are declared before execution.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES, NAMES
from latent_art_bench.painter_feature_generation_v2.statistics import weighted_quantile

VIEWS = ("original31", "nonredundant28", "family_balanced31", "no_texture19")
DROP = (10, 23, 24)


def content_weights(rows, target):
    """Keep the declared class masses; never silently discard absent support."""
    if (
        not rows
        or not target
        or not np.isfinite(list(target.values())).all()
        or any(value < 0 for value in target.values())
        or not np.isclose(sum(target.values()), 1)
    ):
        raise ValueError("invalid content target or empty observations")
    counts = Counter(row["content_class"] for row in rows)
    if any(value > 0 and counts[key] == 0 for key, value in target.items()):
        raise ValueError("required content support is absent")
    return np.array([target.get(r["content_class"], 0) / counts[r["content_class"]] for r in rows])


def feature_view(array, name):
    values = np.asarray(array, dtype=float)
    if values.ndim != 2 or values.shape[1] != 31 or not np.isfinite(values).all():
        raise ValueError("expected a finite N by 31 feature matrix")
    if name == "original31":
        return values.copy()
    if name == "nonredundant28":
        return np.delete(values, DROP, axis=1)
    if name == "no_texture19":
        return values[:, :19].copy()
    if name == "family_balanced31":
        return values / np.sqrt(np.repeat([11, 8, 12], [11, 8, 12]))
    raise ValueError("undeclared metric view")


def _matrix(rows, view):
    return feature_view([row["scaled"] for row in rows], view)


def _ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def _probabilities(weights, size):
    weights = np.asarray(weights, dtype=float)
    if (
        weights.shape != (size,)
        or not np.isfinite(weights).all()
        or (weights < 0).any()
        or not np.isclose(weights.sum(), 1)
    ):
        raise ValueError("expected normalized finite nonnegative weights")
    return weights


def energy_terms(real, generated, real_weights, generated_weights):
    """Weighted empirical V-energy, including both within-distribution terms."""
    x, y = np.asarray(real, dtype=float), np.asarray(generated, dtype=float)
    if (
        x.ndim != 2
        or y.ndim != 2
        or x.shape[1] != y.shape[1]
        or not np.isfinite(x).all()
        or not np.isfinite(y).all()
    ):
        raise ValueError("expected finite matrices with matching dimensions")
    wx, wy = _probabilities(real_weights, len(x)), _probabilities(generated_weights, len(y))
    cross = float(2 * wx @ cdist(x, y) @ wy)
    real_within = float(wx @ cdist(x, x) @ wx)
    generated_within = float(wy @ cdist(y, y) @ wy)
    return dict(
        energy=cross - real_within - generated_within,
        cross_twice=cross,
        reference_within=real_within,
        generated_within=generated_within,
    )


def variance_parts(values, weights, rows, *, generated):
    """Weighted population ANOVA identity; repetitions are empirical, not unbiased."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or len(rows) != len(x) or not np.isfinite(x).all():
        raise ValueError("invalid variance decomposition input")
    w = _probabilities(weights, len(x))
    mean = w @ x
    total = float(w @ np.square(x - mean).sum(axis=1))
    classes = sorted({row["content_class"] for row in rows})
    between_class = 0.0
    within_class = 0.0
    within_brief = 0.0
    between_brief_within_class = 0.0
    for content in classes:
        ix = np.array([i for i, r in enumerate(rows) if r["content_class"] == content])
        mass = float(w[ix].sum())
        if mass == 0:
            continue
        class_mean = w[ix] @ x[ix] / mass
        between_class += mass * float(np.square(class_mean - mean).sum())
        within_class += float(w[ix] @ np.square(x[ix] - class_mean).sum(axis=1))
        if not generated:
            continue
        for brief in sorted({rows[i]["brief_id"] for i in ix}):
            bx = np.array([i for i in ix if rows[i]["brief_id"] == brief])
            brief_mass = float(w[bx].sum())
            brief_mean = w[bx] @ x[bx] / brief_mass
            within_brief += float(w[bx] @ np.square(x[bx] - brief_mean).sum(axis=1))
            between_brief_within_class += brief_mass * float(
                np.square(brief_mean - class_mean).sum()
            )
    result = dict(total_trace=total, within_class=within_class, between_class=between_class)
    components = within_class + between_class
    if generated:
        result.update(
            within_brief=within_brief,
            between_brief_within_class=between_brief_within_class,
            between_brief_means=between_brief_within_class + between_class,
        )
        components = within_brief + between_brief_within_class + between_class
    result["identity_residual"] = total - components
    if not np.isclose(total, components, atol=1e-10, rtol=1e-10):
        raise ValueError("variance decomposition identity failed")
    return result


def _spread(values, weights):
    mean = weights @ values
    coordinate_trace = weights @ np.square(values - mean)
    quantiles = np.array([weighted_quantile(v, weights, [0.25, 0.75]) for v in values.T])
    coordinate_squared_iqr = np.square(quantiles[:, 1] - quantiles[:, 0])
    return dict(
        trace=float(coordinate_trace.sum()),
        squared_iqr_sum=float(coordinate_squared_iqr.sum()),
        coordinate_trace=coordinate_trace.tolist(),
        coordinate_squared_iqr=coordinate_squared_iqr.tolist(),
    )


def distribution(real, generated, target, view="original31", *, detail=True):
    """Summarize one cell; missing positive-mass classes return explicit unavailability."""
    base = dict(n_reference=len(real), n_generated=len(generated), target=dict(target))
    try:
        wx, wy = content_weights(real, target), content_weights(generated, target)
    except ValueError as exc:
        return dict(base, status="unavailable", reason=str(exc))
    x, y = _matrix(real, view), _matrix(generated, view)
    reference_spread, generated_spread = _spread(x, wx), _spread(y, wy)
    result = dict(
        base,
        status="descriptive",
        **energy_terms(x, y, wx, wy),
        reference_trace=reference_spread["trace"],
        generated_trace=generated_spread["trace"],
        trace_ratio=_ratio(generated_spread["trace"], reference_spread["trace"]),
        reference_squared_iqr_sum=reference_spread["squared_iqr_sum"],
        generated_squared_iqr_sum=generated_spread["squared_iqr_sum"],
        squared_iqr_sum_ratio=_ratio(
            generated_spread["squared_iqr_sum"], reference_spread["squared_iqr_sum"]
        ),
        reference_weight_effective_size=float(1 / (wx @ wx)),
        generated_weight_effective_size=float(1 / (wy @ wy)),
    )
    if detail:
        result.update(
            reference_decomposition=variance_parts(x, wx, real, generated=False),
            generated_decomposition=variance_parts(y, wy, generated, generated=True),
            reference_coordinate_trace=reference_spread["coordinate_trace"],
            generated_coordinate_trace=generated_spread["coordinate_trace"],
        )
    return result


def _pair_key(row):
    return row["brief_id"], row["repetition"]


def common_pairs(before, after, expected=(), *, require_same_window=True):
    """Preserve common brief/repetition pairs, returning every absent side and identity."""
    left, right = {_pair_key(r): r for r in before}, {_pair_key(r): r for r in after}
    if len(left) != len(before) or len(right) != len(after):
        raise ValueError("duplicate brief/repetition observation")
    first, second, excluded = [], [], []
    for key in sorted(set(left) | set(right) | set(expected)):
        a, b = left.get(key), right.get(key)
        if a is None or b is None:
            excluded.append(
                dict(
                    brief_id=key[0],
                    repetition=key[1],
                    before_image_id=None if a is None else a["image_id"],
                    after_image_id=None if b is None else b["image_id"],
                )
            )
            continue
        if a["content_class"] != b["content_class"]:
            raise ValueError("paired content classes disagree")
        if require_same_window and a["window"] != b["window"]:
            raise ValueError("paired prompt conditions have different randomized windows")
        first.append(a)
        second.append(b)
    return first, second, excluded


def paired_summary(reference, before, after, target, view, expected=()):
    before, after, excluded = common_pairs(before, after, expected)
    first = distribution(reference, before, target, view, detail=True)
    second = distribution(reference, after, target, view, detail=True)
    result = dict(
        status="unavailable",
        n_pairs=len(before),
        distinct_briefs=len({r["brief_id"] for r in before}),
        excluded_pairs=excluded,
        before_image_ids=[r["image_id"] for r in before],
        after_image_ids=[r["image_id"] for r in after],
        n_reference=len(reference),
        target=dict(target),
    )
    if first["status"] == "unavailable" or second["status"] == "unavailable":
        result["reason"] = first.get("reason", second.get("reason"))
        return result
    differences = {key: second[key] - first[key] for key in (
        "energy", "cross_twice", "reference_within", "generated_within"
    )}
    result.update(
        status="descriptive",
        before_energy=first["energy"],
        after_energy=second["energy"],
        energy_change=differences["energy"],
        energy_term_changes=differences,
        before_reference_trace_ratio=first["trace_ratio"],
        after_reference_trace_ratio=second["trace_ratio"],
        generated_total_trace_ratio=_ratio(second["generated_trace"], first["generated_trace"]),
        generated_squared_iqr_sum_ratio=_ratio(
            second["generated_squared_iqr_sum"], first["generated_squared_iqr_sum"]
        ),
        generated_decomposition_ratios={
            key: _ratio(second["generated_decomposition"][key], value)
            for key, value in first["generated_decomposition"].items()
            if key != "identity_residual"
        },
    )
    return result


def _select(rows, **labels):
    return [row for row in rows if all(row.get(key) == value for key, value in labels.items())]


def _membership(rows):
    return dict(
        image_ids=[r["image_id"] for r in rows],
        content_counts=dict(sorted(Counter(r["content_class"] for r in rows).items())),
    )


def _expected(requests, route, painter):
    return {_pair_key(r) for r in _select(requests, route=route, painter_id=painter)}


def _specs(bundle):
    inventory = bundle.get("requests") or bundle["generated"]
    labels = sorted({(r["route"], r["painter_id"], r["condition"]) for r in inventory})
    comparisons = sorted({(route, painter) for route, painter, _ in labels})
    return labels, comparisons


def _coordinate_contributions(cell, view):
    indices = [i for i in range(31) if not (view == "nonredundant28" and i in DROP)]
    if view == "no_texture19":
        indices = list(range(19))
    result = []
    for domain, total in (("reference", cell["reference_trace"]),
                          ("generated", cell["generated_trace"])):
        coordinates = cell[domain + "_coordinate_trace"]
        families = defaultdict(float)
        for i, value in zip(indices, coordinates):
            family = next(k for k, section in FAMILIES.items() if section.start <= i < section.stop)
            families[family] += value
        result.append(dict(
            domain=domain,
            total_trace=total,
            coordinates=[dict(name=NAMES[i], trace=v, fraction=_ratio(v, total))
                         for i, v in zip(indices, coordinates)],
            families=[dict(family=k, trace=v, fraction=_ratio(v, total))
                      for k, v in families.items()],
        ))
    return result


def _reference_influence(real, generated, targets, comparisons, requests):
    rows = []
    for route, painter in comparisons:
        reference = _select(real, painter_id=painter)
        selected = _select(generated, route=route, painter_id=painter)
        before = _select(selected, condition="artist_free")
        after = _select(selected, condition="named")
        expected = _expected(requests, route, painter)
        full = paired_summary(reference, before, after, targets[painter], "original31", expected)
        deletions = [("work", r["image_id"]) for r in reference]
        deletions += [("content_class", value) for value in sorted(targets[painter])]
        sources = sorted({r.get("source_id", "unknown") for r in reference})
        deletions += [("source_id", value) for value in sources]
        for kind, omitted in deletions:
            key = "image_id" if kind == "work" else kind
            keep = [r for r in reference if r.get(key, "unknown") != omitted]
            target = dict(targets[painter])
            a, b = before, after
            if kind == "content_class":
                target.pop(omitted)
                mass = sum(target.values())
                target = {c: value / mass for c, value in target.items()} if mass > 0 else {}
                a = [r for r in before if r["content_class"] != omitted]
                b = [r for r in after if r["content_class"] != omitted]
            active_expected = {_pair_key(r) for r in a + b} if kind == "content_class" else expected
            value = paired_summary(keep, a, b, target, "original31", active_expected)
            # Shared generated memberships are in the base contrast manifest. A deletion
            # records differences explicitly, keeping the sensitivity output compact.
            value.pop("before_image_ids")
            value.pop("after_image_ids")
            if value["status"] == "descriptive" and full["status"] == "descriptive":
                value["change_from_full_contrast"] = value["energy_change"] - full["energy_change"]
            rows.append(dict(
                route=route, painter_id=painter, deletion_kind=kind, omitted=omitted,
                dropped_reference_ids=[r["image_id"] for r in reference if r not in keep],
                dropped_generated_ids=[r["image_id"] for r in before + after if r not in a + b],
                retained_reference_class_counts=dict(Counter(r["content_class"] for r in keep)),
                source_definition="collection metadata proxy; not a photographic workflow",
                **value,
            ))
    return rows


def _payload(row):
    if row is None:
        return None
    if "payload" in row:
        encoded = json.dumps(row["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(encoded.encode()).hexdigest()
    return row.get("payload_sha256")


def _specificity(real, generated, targets, routes, view, requests):
    painters = sorted(targets)
    if len(painters) != 2:
        return [dict(status="unavailable", reason="exactly two painter labels required")]
    classes = sorted(set().union(*(set(t) for t in targets.values())))
    target = dict.fromkeys(classes, 1 / len(classes))
    request_lookup = {r["request_id"]: r for r in requests}
    results = []
    for route in routes:
        condition_matrices = {}
        for condition in ("artist_free", "named"):
            first = _select(generated, route=route, painter_id=painters[0], condition=condition)
            second = _select(generated, route=route, painter_id=painters[1], condition=condition)
            a, b, missing = common_pairs(first, second, require_same_window=False)
            generated_by_painter = dict(zip(painters, (a, b)))
            matrix = []
            for prompt_painter in painters:
                for reference_painter in painters:
                    value = distribution(
                        _select(real, painter_id=reference_painter),
                        generated_by_painter[prompt_painter], target, view, detail=False,
                    )
                    matrix.append(dict(
                        prompt_painter=prompt_painter, reference_painter=reference_painter, **value
                    ))
            result = dict(
                route=route, condition=condition, target=target, status="unavailable",
                n_common_pairs=len(a), excluded_pairs=missing, energy_matrix=matrix,
                generated_membership={p: _membership(g) for p, g in generated_by_painter.items()},
                interaction_definition="E(A,A) + E(B,B) - E(A,B) - E(B,A); negative favors own",
            )
            if all(row["status"] == "descriptive" for row in matrix):
                signs = [1, -1, -1, 1]
                interaction = {
                    key: sum(sign * row[key] for sign, row in zip(signs, matrix))
                    for key in ("energy", "cross_twice", "reference_within", "generated_within")
                }
                result.update(status="descriptive", interaction_terms=interaction)
                condition_matrices[condition] = interaction["energy"]
            if condition == "artist_free":
                checked, unverified, mismatched = [], [], []
                for x, y in zip(a, b):
                    left = request_lookup.get(x.get("request_id"))
                    right = request_lookup.get(y.get("request_id"))
                    identities = [x["image_id"], y["image_id"]]
                    px, py = _payload(left), _payload(right)
                    if px is None or py is None:
                        unverified.append(identities)
                    elif px != py:
                        mismatched.append(identities)
                    else:
                        checked.append(dict(image_ids=identities, payload_sha256=px))
                placebo = dict(
                    status="unavailable", verified_payload_pairs=checked,
                    unverified_pairs=unverified, mismatched_pairs=mismatched,
                    interpretation=(
                        "post-result collection-label diagnostic, not an equivalence test"
                    ),
                )
                if a and not unverified and not mismatched:
                    try:
                        wa, wb = content_weights(a, target), content_weights(b, target)
                    except ValueError as exc:
                        placebo["reason"] = str(exc)
                    else:
                        placebo.update(
                            status="descriptive",
                            **energy_terms(_matrix(a, view), _matrix(b, view), wa, wb),
                        )
                else:
                    placebo["reason"] = (
                        "complete measured pairs with verified identical payloads required"
                    )
                result["identical_payload_placebo"] = placebo
            results.append(result)
        if len(condition_matrices) == 2:
            results.append(dict(
                route=route, condition="named_minus_artist_free_interaction", status="descriptive",
                interaction_change=condition_matrices["named"] - condition_matrices["artist_free"],
                target=target,
            ))
    return results


def _development_correlations(rows):
    if not rows:
        return dict(status="unavailable", reason="no development vectors")
    counts = Counter(r["painter_id"] for r in rows)
    weights = np.array([1 / (len(counts) * counts[r["painter_id"]]) for r in rows])
    x = _matrix(rows, "original31")
    centered = x - weights @ x
    covariance = centered.T @ (weights[:, None] * centered)
    scales = np.sqrt(np.diag(covariance))
    divisor = np.outer(scales, scales)
    correlation = np.divide(covariance, divisor, out=np.zeros_like(covariance), where=divisor > 0)
    pairs = [dict(first=NAMES[i], second=NAMES[j], pearson=float(correlation[i, j]))
             for i in range(31) for j in range(i + 1, 31) if divisor[i, j] > 0]
    pairs.sort(key=lambda item: (-abs(item["pearson"]), item["first"], item["second"]))
    return dict(
        status="descriptive", n_development=len(rows), painter_counts=dict(sorted(counts.items())),
        weighting="equal painter mass, equal works within painter", feature_names=list(NAMES),
        correlation=[[float(correlation[i, j]) if divisor[i, j] > 0 else None
                      for j in range(31)] for i in range(31)],
        largest_absolute_correlations=pairs[:20],
        zero_variance_coordinates=[NAMES[i] for i in range(31) if scales[i] == 0],
    )


def _development_scaler_sensitivity(
    development, real, generated, targets, labels, comparisons, requests
):
    painters = sorted({r["painter_id"] for r in development})
    if len(painters) < 2:
        return [dict(status="unavailable", reason="at least two development painters required")]
    outputs = []
    for omitted in painters:
        retained = [r for r in development if r["painter_id"] != omitted]
        counts = Counter(r["painter_id"] for r in retained)
        weights = np.array([1 / (len(counts) * counts[r["painter_id"]]) for r in retained])
        x = _matrix(retained, "original31")
        q = np.array([weighted_quantile(column, weights, [0.25, 0.75]) for column in x.T])
        scale = q[:, 1] - q[:, 0]
        output = dict(
            omitted_development_painter=omitted, status="unavailable",
            dropped_development_ids=[
                r["image_id"] for r in development if r["painter_id"] == omitted
            ],
            retained_development_ids=[r["image_id"] for r in retained],
            retained_painter_counts=dict(sorted(counts.items())),
            iqr_relative_to_frozen_scale=scale.tolist(),
            invalid_coordinates=[NAMES[i] for i in range(31) if scale[i] <= 0],
            interpretation="post-result metric sensitivity; evaluation values never fit the scaler",
        )
        if output["invalid_coordinates"]:
            output["reason"] = "one or more retained-development IQRs are zero"
            outputs.append(output)
            continue
        rx = [dict(r, scaled=(np.asarray(r["scaled"]) / scale).tolist()) for r in real]
        gx = [dict(r, scaled=(np.asarray(r["scaled"]) / scale).tolist()) for r in generated]
        cells, contrasts = [], []
        for route, painter, condition in labels:
            cells.append(dict(
                route=route, painter_id=painter, condition=condition,
                **distribution(
                    _select(rx, painter_id=painter),
                    _select(gx, route=route, painter_id=painter, condition=condition),
                    targets[painter], detail=False,
                ),
            ))
        for route, painter in comparisons:
            selected = _select(gx, route=route, painter_id=painter)
            value = paired_summary(
                _select(rx, painter_id=painter), _select(selected, condition="artist_free"),
                _select(selected, condition="named"), targets[painter], "original31",
                _expected(requests, route, painter),
            )
            value.pop("before_image_ids")
            value.pop("after_image_ids")
            contrasts.append(dict(route=route, painter_id=painter, **value))
        output.update(status="descriptive", cells=cells, prompt_contrasts=contrasts)
        outputs.append(output)
    return outputs


def analyze(bundle):
    """Return the complete fixed numeric diagnostic grid as strict JSON-safe values.

    Required: reference/generated/development lists with pipeline, image_id,
    painter_id, content_class, scaled[31]; generated rows additionally contain
    route, condition, brief_id, repetition and window. Targets map painter to
    content probability masses. Requests retain original payload and request_id.
    Reference source_id is optional and denotes a collection metadata proxy.
    """
    labels, comparisons = _specs(bundle)
    requests = bundle.get("requests", [])
    targets = bundle["targets"]
    pipelines = sorted({r["pipeline"] for r in bundle["reference"]})
    for domain in ("reference", "generated", "development"):
        rows = bundle[domain]
        keys = {(r["pipeline"], r["image_id"]) for r in rows}
        if len(keys) != len(rows):
            raise ValueError("duplicate image/pipeline identity")
        for row in rows:
            feature_view([row["scaled"]], "original31")
        if set(r["pipeline"] for r in rows) - set(pipelines):
            raise ValueError("domain contains a pipeline absent from reference")
    outputs = dict(
        schema="painter_distribution_revision_v1.metrics.1",
        inference=(
            "all outputs are post-result descriptive diagnostics; no new p-values or intervals"
        ),
        metric_views={
            "original31": "unchanged fixed 31-coordinate scaled Euclidean metric",
            "nonredundant28": "drop indices 10, 23, 24; preserve all remaining frozen scales",
            "family_balanced31": "divide color/spatial/texture by sqrt(11),sqrt(8),sqrt(12)",
            "no_texture19": "retain unchanged scaled coordinates 0 through 18",
        },
        cells=[], prompt_contrasts=[], trace_contributions=[], specificity=[],
        development_correlations=[], memberships={},
    )
    for pipeline in pipelines:
        real, generated, development = (
            _select(bundle[domain], pipeline=pipeline)
            for domain in ("reference", "generated", "development")
        )
        outputs["development_correlations"].append(
            dict(pipeline=pipeline, **_development_correlations(development))
        )
        for painter in sorted(targets):
            outputs["memberships"][pipeline + ":reference:" + painter] = _membership(
                _select(real, painter_id=painter)
            )
        for route, painter, condition in labels:
            group = _select(generated, route=route, painter_id=painter, condition=condition)
            cell_id = ":".join((pipeline, route, painter, condition))
            outputs["memberships"][cell_id] = _membership(group)
            for view in VIEWS:
                value = distribution(
                    _select(real, painter_id=painter), group, targets[painter], view
                )
                label = dict(
                    cell_id=cell_id, pipeline=pipeline, metric_view=view,
                    route=route, painter_id=painter, condition=condition,
                    reference_membership=pipeline + ":reference:" + painter,
                )
                if value["status"] == "descriptive":
                    outputs["trace_contributions"].append(dict(
                        label, domains=_coordinate_contributions(value, view),
                    ))
                    value.pop("reference_coordinate_trace")
                    value.pop("generated_coordinate_trace")
                outputs["cells"].append(dict(label, **value))
        for view in VIEWS:
            for route, painter in comparisons:
                selected = _select(generated, route=route, painter_id=painter)
                value = paired_summary(
                    _select(real, painter_id=painter),
                    _select(selected, condition="artist_free"),
                    _select(selected, condition="named"),
                    targets[painter], view, _expected(requests, route, painter),
                )
                outputs["prompt_contrasts"].append(dict(
                    pipeline=pipeline, metric_view=view, route=route, painter_id=painter,
                    before="artist_free", after="named", **value,
                ))
            outputs["specificity"].extend(
                dict(pipeline=pipeline, metric_view=view, **row)
                for row in _specificity(
                    real, generated, targets, sorted({r for r, _ in comparisons}), view, requests
                )
            )
        if pipeline == "primary512":
            outputs["reference_influence"] = _reference_influence(
                real, generated, targets, comparisons, requests
            )
            outputs["development_scaler_sensitivity"] = _development_scaler_sensitivity(
                development, real, generated, targets, labels, comparisons, requests
            )
    # Fail closed on accidental NumPy scalars or nonfinite values before publication.
    json.dumps(outputs, allow_nan=False)
    return outputs
