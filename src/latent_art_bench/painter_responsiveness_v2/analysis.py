"""Computational instruction-response estimates and exposed-reference context.

This module is pure: it never reads images, fits a scale, dispatches generation,
or promotes digital feature overlap to perceptual or causal validation.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from scipy.stats import wasserstein_distance

from latent_art_bench.painter_distribution_study_v1.study import PIPELINES
from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_responsiveness_v1.design import ARMS, validate_schedule
from latent_art_bench.painter_responsiveness_v1.inference import analyze_factorial

CLASSES = ("built", "land", "water")
PAINTERS = ("claude_monet", "paul_cezanne")
INTERPRETATION = (
    "The primary estimands are finite-template, two-instruction service response "
    "interactions in median image chroma. A negative named-minus-generic interaction "
    "supports attenuation only with positive free/generic responses and without a "
    "named response reversal. Two levels do not distinguish reduced gain from a "
    "shifted operating range or saturation. No human validation, internal model "
    "mechanism, perceptual fidelity, or explanation of the original/generated gap "
    "is established by these estimates."
)
REFERENCE_SCOPE = (
    "Post-result exposed digital references, not an independent holdout or human-validated "
    "style target. Broad classes were assigned by a single maintainer-run LLM; class "
    "weighting does not establish fine-content, period or capture matching. Empirical "
    "chroma overlap and Wasserstein distance concern one coordinate, not overall style "
    "or equivalence. The equal-polarity mixture is a designed experimental mixture, "
    "not a model's unprompted output distribution."
)


def _scale(config):
    if config.get("feature_index") != 2 or config.get("primary_pipeline") != "primary512":
        raise ValueError("the fixed primary endpoint is primary512 chroma_median at index two")
    values = [config.get("primary_chroma_center"), config.get("primary_chroma_scale")]
    if any(type(v) not in (int, float) or not np.isfinite(v) for v in values):
        raise ValueError("a finite frozen primary-development chroma scale is required")
    if values[1] <= 0:
        raise ValueError("the frozen primary-development chroma scale must be positive")
    return values


def _chroma(row, center, scale):
    status = row.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("every feature row needs a measurement status")
    if status != "measured":
        if row.get("values") is not None or row.get("chroma_primary_iqr") is not None:
            raise ValueError("an unavailable measurement cannot carry feature values")
        return None
    vector = np.asarray(row.get("values"), dtype=float)
    if vector.shape != (31,) or not np.isfinite(vector).all():
        raise ValueError("a measured image must have exactly 31 finite features")
    value = float((vector[2] - center) / scale)
    if "chroma_primary_iqr" in row and row["chroma_primary_iqr"] != value:
        raise ValueError("stored chroma does not use the common primary-development scale")
    return value


def _generated(requests, rows, center, scale):
    planned = {r["request_id"]: r for r in requests}
    if len(planned) != len(requests):
        raise ValueError("request identities must be unique")
    indexed = {}
    for row in rows:
        key = row.get("request_id"), row.get("pipeline")
        if key[0] not in planned or key[1] not in PIPELINES or key in indexed:
            raise ValueError("unknown or duplicate generated measurement identity")
        request = planned[key[0]]
        for name in ("arm", "polarity", "template_id", "repetition", "content_class"):
            if name in row and row[name] != request[name]:
                raise ValueError("measurement treatment identity differs from its planned slot")
        value = _chroma(row, center, scale)
        indexed[key] = dict(request_id=key[0], pipeline=key[1], status=row["status"],
                            value=value)
    result = []
    for request in requests:
        if request.get("content_class") not in CLASSES:
            raise ValueError("each fixed template requires one of three declared broad classes")
        for pipeline in PIPELINES:
            row = indexed.get((request["request_id"], pipeline), dict(
                request_id=request["request_id"], pipeline=pipeline,
                status="not_recorded", value=None,
            ))
            result.append(dict(row, **{k: request[k] for k in (
                "arm", "polarity", "template_id", "repetition", "content_class",
            )}))
    return result


def _references(rows, center, scale):
    result, seen, membership = [], set(), {}
    for row in rows:
        identity = row.get("image_id", row.get("work_id"))
        key = identity, row.get("pipeline")
        if not isinstance(identity, str) or not identity or key[1] not in PIPELINES or key in seen:
            raise ValueError("reference image/pipeline identities must be valid and unique")
        painter, content = row.get("painter_id"), row.get("content_class")
        if painter not in PAINTERS or content not in CLASSES:
            raise ValueError("unexpected reference painter or broad content class")
        if identity in membership and membership[identity] != (painter, content):
            raise ValueError("reference painter/class changed across processing pipelines")
        value = _chroma(row, center, scale)
        if value is None:
            raise ValueError("the already-exposed reference inventory requires measured vectors")
        seen.add(key)
        membership[identity] = painter, content
        result.append(dict(image_id=identity, painter_id=painter, content_class=content,
                           pipeline=key[1], value=value))
    if not membership or len(result) != len(membership) * len(PIPELINES):
        raise ValueError("all reference identities must have all three processing pipelines")
    if {p for p, _ in membership.values()} != set(PAINTERS):
        raise ValueError("both retained painters are required")
    return sorted(result, key=lambda r: (r["pipeline"], r["painter_id"], r["image_id"]))


def _weights(rows, keys):
    """Give fixed strata equal mass; absent strata make the target unavailable."""
    levels = [(a, b) for a in CLASSES for b in ("muted", "vivid")] if keys == (
        "content_class", "polarity"
    ) else [(a,) for a in CLASSES] if keys else [()]
    counts = Counter(tuple(r[k] for k in keys) for r in rows)
    if set(counts) != set(levels):
        return None
    return np.asarray([1 / (len(levels) * counts[tuple(r[k] for k in keys)]) for r in rows])


def _quantiles(values, weights):
    """Generalized inverse of the normalized empirical CDF, including ties."""
    order = np.argsort(values, kind="stable")
    x, w = np.asarray(values)[order], np.asarray(weights)[order]
    cumulative = np.cumsum(w) / np.sum(w)
    indices = np.searchsorted(cumulative, (0.1, 0.5, 0.9), side="left")
    return x[np.minimum(indices, len(x) - 1)].tolist()


def _summary(rows, weights):
    values = np.asarray([r["value"] for r in rows])
    return dict(n=len(rows), weighted_mean=float(np.average(values, weights=weights)),
                quantiles_10_50_90=_quantiles(values, weights),
                minimum=float(values.min()), maximum=float(values.max()))


def _reference_bridge(generated, references):
    results, envelopes = [], []
    for pipeline in PIPELINES:
        for painter in PAINTERS:
            refs = [r for r in references if r["pipeline"] == pipeline
                    and r["painter_id"] == painter]
            for weighting in ("empirical_reference_mixture", "equal_broad_class"):
                weights = _weights(refs, () if weighting == "empirical_reference_mixture"
                                   else ("content_class",))
                envelope = dict(pipeline=pipeline, painter_id=painter, weighting=weighting,
                                image_ids=[r["image_id"] for r in refs],
                                class_counts=dict(Counter(r["content_class"] for r in refs)))
                if weights is None:
                    envelope.update(status="unavailable_reference_class", summary=None)
                else:
                    envelope.update(status="descriptive", summary=_summary(refs, weights),
                                    weights=weights.tolist())
                envelopes.append(envelope)
                for arm in ARMS:
                    for polarity in ("muted", "vivid", "equal_polarity_mixture"):
                        allocated = [r for r in generated if r["pipeline"] == pipeline
                                     and r["arm"] == arm and (polarity == "equal_polarity_mixture"
                                                              or r["polarity"] == polarity)]
                        available = [r for r in allocated if r["status"] == "measured"]
                        keys = (("content_class", "polarity")
                                if polarity == "equal_polarity_mixture" else ("content_class",))
                        generated_weights = _weights(available, keys)
                        item = dict(pipeline=pipeline, painter_id=painter, arm=arm,
                                    polarity=polarity, reference_weighting=weighting,
                                    allocated=len(allocated), measured=len(available),
                                    complete=len(allocated) == len(available),
                                    request_ids=[r["request_id"] for r in available],
                                    unavailable_request_ids=[r["request_id"] for r in allocated
                                                             if r["status"] != "measured"],
                                    generated_weighting="equal broad classes and, for mixture, "
                                                        "equal polarity within class")
                        if weights is None or generated_weights is None:
                            item.update(status="unavailable_stratum", wasserstein_1=None)
                        else:
                            x, y = ([r["value"] for r in refs], [r["value"] for r in available])
                            qref, qgen = (_quantiles(x, weights), _quantiles(y, generated_weights))
                            item.update(
                                status="descriptive_complete" if item["complete"]
                                else "descriptive_selected_available", generated_weights=
                                generated_weights.tolist(), generated_summary=
                                _summary(available, generated_weights),
                                wasserstein_1=float(wasserstein_distance(
                                    x, y, u_weights=weights, v_weights=generated_weights)),
                                generated_mass_in_reference_central80=float(np.average(
                                    (np.asarray(y) >= qref[0]) & (np.asarray(y) <= qref[2]),
                                    weights=generated_weights)),
                                reference_mass_in_generated_central80=float(np.average(
                                    (np.asarray(x) >= qgen[0]) & (np.asarray(x) <= qgen[2]),
                                    weights=weights)),
                            )
                        results.append(item)
    return dict(scope=REFERENCE_SCOPE, envelopes=envelopes, comparisons=results,
                quantile_definition="Generalized inverse of normalized weighted empirical CDF; "
                                    "central80 means inclusive empirical 10th–90th percentiles.",
                uncertainty="No confidence intervals, tests, target validation or equivalence "
                            "threshold is assigned to these exposed-reference descriptions.")


def _verdicts(factorial):
    if factorial["primary"] is None:
        return dict(status="unavailable_primary", painters=[])
    response = {r["contrast"]: r for r in factorial["responses"]}
    controls_positive = all(response[a]["nominal_interval"] is not None
                            and response[a]["nominal_interval"][0] > 0 for a in ("free", "generic"))
    result = []
    for row, arm in zip(factorial["primary"], ("monet", "cezanne"), strict=True):
        interval = row["family_interval"]
        if interval is None:
            verdict = "unavailable_estimated_variance"
        elif interval[0] > 0:
            verdict = ("larger_named_response" if controls_positive
                       else "positive_interaction_without_established_positive_controls")
        elif interval[1] >= 0:
            verdict = "interaction_direction_unresolved"
        elif not controls_positive:
            verdict = "negative_interaction_without_established_positive_controls"
        elif response[arm]["estimate"] <= 0:
            verdict = ("negative_interaction_with_named_response_reversal"
                       if response[arm]["estimate"] < 0
                       else "negative_interaction_with_zero_named_response")
        else:
            verdict = "smaller_positive_named_chroma_response"
        result.append(dict(
            arm=arm, verdict=verdict, named_response_estimate=response[arm]["estimate"],
            named_response_reversed=response[arm]["estimate"] < 0,
            simultaneous_interval_negative=interval is not None and interval[1] < 0,
            simultaneous_interval_positive=interval is not None and interval[0] > 0,
        ))
    return dict(status="computational_only", controls_nominal_intervals_positive=controls_positive,
                painters=result, scope=INTERPRETATION)


def _coordinates(requests, rows):
    selected = {r["request_id"]: r for r in rows if r["pipeline"] == "primary512"}
    unavailable = [r["request_id"] for r in requests
                   if selected.get(r["request_id"], {}).get("status") != "measured"]
    scope = ("All 31 frozen primary512 coordinates, equal fixed-template weights; "
             "descriptive point estimates only, without additional hypothesis tests.")
    if unavailable:
        return dict(status="withheld_incomplete_grid", unavailable_request_ids=unavailable,
                    scope=scope, coordinates=None)
    vectors = {}
    for identity, row in selected.items():
        value = np.asarray(row.get("scaled"), dtype=float)
        if value.shape != (31,) or not np.isfinite(value).all():
            raise ValueError("all-coordinate diagnostics require 31 finite frozen scaled values")
        if "chroma_primary_iqr" in row and value[2] != row["chroma_primary_iqr"]:
            raise ValueError("primary coordinate diagnostics use a different chroma scale")
        vectors[identity] = value
    templates = sorted({r["template_id"] for r in requests})
    means = {(template, arm, polarity): np.mean([
        vectors[r["request_id"]] for r in requests
        if (r["template_id"], r["arm"], r["polarity"]) == (template, arm, polarity)
    ], axis=0) for template in templates for arm in ARMS for polarity in ("muted", "vivid")}
    rows = []
    for index, name in enumerate(NAMES):
        cells = {arm: {p: float(np.mean([means[t, arm, p][index] for t in templates]))
                       for p in ("muted", "vivid")} for arm in ARMS}
        responses = {a: cells[a]["vivid"] - cells[a]["muted"] for a in ARMS}
        detail = []
        for template in templates:
            values = {a: float(means[template, a, "vivid"][index]
                               - means[template, a, "muted"][index]) for a in ARMS}
            detail.append(dict(template_id=template, responses=values, interactions={
                a + "_minus_generic": values[a] - values["generic"]
                for a in ("monet", "cezanne")}))
        rows.append(dict(feature_index=index, feature_name=name, arm_polarity_means=cells,
                         responses=responses, interactions={
                             a + "_minus_generic": responses[a] - responses["generic"]
                             for a in ("monet", "cezanne")},
                         generic_minus_free=responses["generic"] - responses["free"],
                         template_responses=detail))
    return dict(status="complete_descriptive", scope=scope, coordinates=rows)


def analyze(requests, feature_rows, reference_rows, config):
    """Analyze frozen requests and vectors, retaining missing slots and shared controls."""
    design = validate_schedule(requests)
    if design["repetitions"] != 4 or len(requests) != 192:
        raise ValueError("this successor scope fixes 192 requests and four repeats")
    content = {}
    for row in requests:
        previous = content.setdefault(row["template_id"], row.get("content_class"))
        if previous != row.get("content_class"):
            raise ValueError("one template cannot change its broad content identity")
    if Counter(content.values()) != Counter({c: 2 for c in CLASSES}):
        raise ValueError("the six templates must include exactly two per broad class")
    center, scale = _scale(config)
    generated = _generated(requests, feature_rows, center, scale)
    references = _references(reference_rows, center, scale)
    analyses = {}
    for pipeline in PIPELINES:
        outcomes = [{k: r[k] for k in ("request_id", "status", "value")}
                    for r in generated if r["pipeline"] == pipeline]
        result = analyze_factorial(requests, outcomes, alpha=config.get("alpha", 0.05),
                                   manipulation_margin=0)
        result["interpretation"] = INTERPRETATION
        result["scope"] = ("Prespecified primary family" if pipeline == "primary512"
                           else "Descriptive processing sensitivity; not an additional "
                           "confirmatory test family")
        if pipeline != "primary512" and result["primary"] is not None:
            for row in result["primary"]:
                for key in ("p_two_sided", "p_holm", "reject_holm"):
                    row.pop(key, None)
            result["sensitivity_intervals"] = (
                "Approximate sensitivity intervals, not independent confirmations "
                "or a new testing family."
            )
        analyses[pipeline] = result
    return dict(
        schema="painter-responsiveness-computational-results/2", route=config.get("route"),
        endpoint=dict(name="chroma_median", feature_index=2, primary_pipeline="primary512",
                      center=center, scale=scale, units="common primary-development IQR units"),
        primary=analyses["primary512"], processing_sensitivity={
            p: analyses[p] for p in PIPELINES if p != "primary512"},
        computational_interpretation=_verdicts(analyses["primary512"]),
        all_coordinate_responses=_coordinates(requests, feature_rows),
        reference_context=_reference_bridge(generated, references),
        generated_chroma=generated, reference_chroma=references,
        counts=dict(planned_images=len(requests), measured_by_pipeline={
            p: sum(r["pipeline"] == p and r["status"] == "measured" for r in generated)
            for p in PIPELINES}, reference_images=len(references) // len(PIPELINES),
            human_ratings=0),
        claim_scope=INTERPRETATION,
    )
