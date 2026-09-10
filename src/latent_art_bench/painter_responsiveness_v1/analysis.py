"""Descriptive responsiveness diagnostics on previously measured vectors only.

This module neither opens images nor fits an attenuation regression. Cross-repeat
products are signed observed statistics, not identified latent variance estimates.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES, NAMES

PIPELINES = ("primary512", "resolution256", "jpeg90_512")
ROUTES = ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
PAINTERS = ("claude_monet", "paul_cezanne")
CHROMA = NAMES.index("chroma_median")


def _array(value, *, ndim):
    result = np.asarray(value, dtype=float)
    if result.ndim != ndim or result.shape[-1] != len(NAMES) or not np.isfinite(result).all():
        raise ValueError("expected finite vectors in the fixed 31-coordinate order")
    return result


def _cross_products(x):
    """Center each repetition separately; retain every signed cross-repeat product."""
    centered = x - x.mean(axis=0, keepdims=True)
    pairs = [
        (left, right, (centered[:, left] * centered[:, right]).mean(axis=0))
        for left, right in combinations(range(x.shape[1]), 2)
    ]
    return np.mean([value for _, _, value in pairs], axis=0), pairs


def _condition(x):
    mean = x.mean(axis=1)
    grand = mean.mean(axis=0)
    within = np.square(x - mean[:, None]).mean(axis=(0, 1))
    between = np.square(mean - grand).mean(axis=0)
    total = np.square(x - grand).mean(axis=(0, 1))
    cross, pairs = _cross_products(x)
    if not np.allclose(total, within + between, atol=1e-12, rtol=1e-12):
        raise ValueError("empirical variance identity failed")
    coordinates = dict(total=total, within_brief=within, between_brief=between,
                       cross_repeat_between=cross)
    return coordinates, dict(
        **{key + "_trace": float(value.sum()) for key, value in coordinates.items()},
        cross_repeat_pairs=[dict(repetitions=[a, b], product=float(value.sum()))
                            for a, b, value in pairs],
    )


def _summarize_scope(before, after, brief_ids, scope):
    """Equal-brief/equal-repetition summaries; no cross-condition regression."""
    before, after = _array(before, ndim=3), _array(after, ndim=3)
    if before.shape != after.shape or len(brief_ids) != len(before):
        raise ValueError("paired arrays and brief identities must match")
    if len(before) < 1 or before.shape[1] < 2:
        raise ValueError("at least one brief and two repetitions are required")
    bc, bs = _condition(before)
    ac, ass = _condition(after)
    coordinates = []
    for i, name in enumerate(NAMES):
        coordinates.append(dict(
            feature=name,
            **{f"before_{key}": float(value[i]) for key, value in bc.items()},
            **{f"after_{key}": float(value[i]) for key, value in ac.items()},
            **{f"change_{key}": float(ac[key][i] - value[i]) for key, value in bc.items()},
        ))
    families = []
    for family, indices in FAMILIES.items():
        families.append(dict(
            family=family,
            **{f"before_{key}": float(value[indices].sum()) for key, value in bc.items()},
            **{f"after_{key}": float(value[indices].sum()) for key, value in ac.items()},
            **{f"change_{key}": float((ac[key] - value)[indices].sum())
               for key, value in bc.items()},
        ))
    delta = after - before
    delta_means = delta.mean(axis=1)
    delta_cross = [
        float((delta[:, a] * delta[:, b]).sum(axis=1).mean())
        for a, b in combinations(range(delta.shape[1]), 2)
    ]
    return dict(
        scope=scope, brief_ids=brief_ids, n_briefs=len(before),
        n_repetitions=before.shape[1],
        status="descriptive" if len(before) > 1 else "single_brief_no_between_brief_support",
        before=bs, after=ass, coordinates=coordinates, families=families,
        changes={key + "_trace": float((ac[key] - bc[key]).sum()) for key in bc},
        displacement=dict(
            grand_mean=delta_means.mean(axis=0).tolist(),
            mean_squared_brief_displacement=float(np.square(delta_means).sum(axis=1).mean()),
            squared_grand_mean_displacement=float(np.square(delta_means.mean(axis=0)).sum()),
            cross_repeat_mean_product=float(np.mean(delta_cross)),
            cross_repeat_products=delta_cross,
        ),
    )


def _validate_rows(rows, stage):
    seen = set()
    for row in rows:
        identity = (row["pipeline"], row["image_id"])
        if identity in seen:
            raise ValueError(f"duplicate {stage} image/pipeline")
        seen.add(identity)
        if row["pipeline"] not in PIPELINES or row.get("status") != "measured":
            raise ValueError(f"invalid {stage} pipeline or status")
        _array(row["values"], ndim=1)
        _array(row["scaled"], ndim=1)


def _cell(rows, route, painter, brief_spec, repetitions):
    selected = [r for r in rows if r["pipeline"] == "primary512"
                and r["route"] == route and r["painter_id"] == painter
                and r["condition"] in ("artist_free", "named")]
    index = {}
    for row in selected:
        key = (row["condition"], row["brief_id"], row["repetition"])
        if key in index:
            raise ValueError("duplicate condition/brief/repetition")
        if row["brief_id"] not in brief_spec:
            raise ValueError("generated brief absent from request design")
        if row["content_class"] != brief_spec[row["brief_id"]]["content_class"]:
            raise ValueError("generated content class disagrees with design")
        index[key] = row
    briefs = sorted(brief_spec)
    expected = {(c, b, r) for c in ("artist_free", "named")
                for b in briefs for r in range(repetitions)}
    if set(index) != expected:
        raise ValueError("named/free diagnostic requires the complete matched design")
    matrices = {
        c: _array([[index[c, b, r]["scaled"] for r in range(repetitions)] for b in briefs],
                  ndim=3)
        for c in ("artist_free", "named")
    }
    before, after = matrices["artist_free"], matrices["named"]
    details = []
    for i, brief in enumerate(briefs):
        delta = after[i] - before[i]
        details.append(dict(
            brief_id=brief, content_class=brief_spec[brief]["content_class"],
            detailed_prompt_scene=brief_spec[brief].get("detailed"),
            repetitions=list(range(repetitions)),
            before_image_ids=[index["artist_free", brief, r]["image_id"]
                              for r in range(repetitions)],
            after_image_ids=[index["named", brief, r]["image_id"] for r in range(repetitions)],
            before_mean=before[i].mean(axis=0).tolist(),
            after_mean=after[i].mean(axis=0).tolist(),
            mean_displacement=delta.mean(axis=0).tolist(),
            squared_mean_displacement=float(np.square(delta.mean(axis=0)).sum()),
            cross_repeat_displacement_products=[
                dict(repetitions=[a, b], product=float(delta[a] @ delta[b]))
                for a, b in combinations(range(repetitions), 2)
            ],
        ))
    scopes = [_summarize_scope(before, after, briefs, "all_briefs")]
    for content in sorted({b["content_class"] for b in brief_spec.values()}):
        ix = [i for i, brief in enumerate(briefs) if brief_spec[brief]["content_class"] == content]
        scopes.append(_summarize_scope(before[ix], after[ix], [briefs[i] for i in ix], content))
    return dict(
        cell_id=f"primary512:{route}:{painter}:named_minus_artist_free",
        route=route, painter_id=painter, n_briefs=len(briefs), n_pairs=len(briefs) * repetitions,
        weighting="equal brief, equal repetition; each content-only scope renormalizes",
        before="artist_free", after="named", briefs=details, scopes=scopes,
    )


def _range(values):
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError("finite nonempty chroma support required")
    levels = (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1)
    keys = ("minimum", "q10", "q25", "median", "q75", "q90", "maximum")
    return dict(zip(keys, np.quantile(a, levels, method="linear").tolist(), strict=True))


def _reference_chroma(bundle):
    rows = bundle["reference"]
    scale = bundle["scalers"]["primary512"]["scaler"]
    center, width = float(scale["center"][CHROMA]), float(scale["scale"][CHROMA])
    if not np.isfinite([center, width]).all() or width <= 0:
        raise ValueError("invalid primary development chroma scale")
    by_id = defaultdict(dict)
    for row in rows:
        by_id[row["image_id"]][row["pipeline"]] = row
    works = []
    for identity, pipelines in sorted(by_id.items()):
        if set(pipelines) != set(PIPELINES):
            raise ValueError("reference chroma requires matching work identities "
                             "in three pipelines")
        row = pipelines["primary512"]
        if any(p[k] != row[k] for p in pipelines.values()
               for k in ("painter_id", "content_class")):
            raise ValueError("reference identity metadata changes across pipelines")
        raw = {key: float(p["values"][CHROMA]) for key, p in pipelines.items()}
        works.append(dict(
            image_id=identity, painter_id=row["painter_id"], content_class=row["content_class"],
            subject_subcategory=row.get("subject_subcategory"),
            content_description=row.get("content_description"),
            source_id=row.get("source_id"), capture_workflow=row.get("capture_workflow"),
            raw_chroma=raw,
            common_primary_scaled_chroma={key: (value - center) / width
                                          for key, value in raw.items()},
            raw_pipeline_span=max(raw.values()) - min(raw.values()),
            pipeline_span_primary_iqr_units=(max(raw.values()) - min(raw.values())) / width,
        ))
    groups = []
    inventories = []
    for painter in PAINTERS:
        real = [r for r in works if r["painter_id"] == painter]
        if not real:
            raise ValueError("reference painter absent")
        subsets = [("all_reference", "all", real)]
        for content in sorted({r["content_class"] for r in real}):
            class_rows = [r for r in real if r["content_class"] == content]
            subsets.append(("broad_content", content, class_rows))
            for label in sorted({r["subject_subcategory"] for r in class_rows
                                 if r["subject_subcategory"]}):
                subsets.append(("exact_recorded_subject_label", f"{content}:{label}",
                                [r for r in class_rows if r["subject_subcategory"] == label]))
        counts = Counter((r["content_class"], r["subject_subcategory"]) for r in real
                         if r["subject_subcategory"])
        inventories.append(dict(
            painter_id=painter, n_reference=len(real), n_exact_labels=len(counts),
            n_missing_labels=sum(not r["subject_subcategory"] for r in real),
            maximum_works_per_exact_label=max(counts.values(), default=0),
            exact_label_groups_with_at_least_two=sum(n >= 2 for n in counts.values()),
            exact_label_groups_with_at_least_four=sum(n >= 4 for n in counts.values()),
        ))
        for level, label, members in subsets:
            for pipeline in PIPELINES:
                raw = [r["raw_chroma"][pipeline] for r in members]
                groups.append(dict(
                    painter_id=painter, level=level, label=label, pipeline=pipeline,
                    n_reference=len(members), image_ids=[r["image_id"] for r in members],
                    raw=_range(raw), common_primary_scaled=_range(
                        [(value - center) / width for value in raw]),
                    support_status="singleton_no_within_stratum_variation"
                    if len(members) == 1 else "finite_empirical_range_only",
                ))
    return dict(
        feature=NAMES[CHROMA], feature_index=CHROMA,
        common_scale=dict(pipeline="primary512", center=center, scale=width),
        quantile_rule="unweighted empirical linear interpolation; "
                      "ranges are not tolerance intervals",
        works=works, groups=groups, subject_label_inventory=inventories,
        fine_content_feasibility=dict(
            status="unavailable", independently_validated=False,
            reason="Reference subject labels are recorded free text, without a shared validated "
                   "ontology or independent generated-content coding. Broad classes and exact "
                   "string matches do not establish fine-content support "
                   "or reference reachability.",
            reference_holdout_available=False,
            holdout_reason="These reference vectors have already been exposed to analysis.",
        ),
    )


def _quality_inventory(bundle):
    requests = {r["request_id"]: r for r in bundle["requests"]}
    if len(requests) != len(bundle["requests"]):
        raise ValueError("duplicate request identity")
    groups = defaultdict(list)
    for row in bundle["generated"]:
        if row["pipeline"] != "primary512":
            continue
        request = requests[row["request_id"]]
        if any(row[key] != request[key] for key in
               ("route", "painter_id", "condition", "brief_id", "repetition")):
            raise ValueError("request and measured vector identities disagree")
        key = (row["route"], row["painter_id"], row["condition"],
               request["payload"].get("quality"), row.get("reported_quality"))
        groups[key].append(row)
    return dict(
        interpretation="Successful measured outputs only; reported quality is not verified "
                       "rendering quality. Treatment-associated metadata is not "
                       "an adjustment variable.",
        groups=[dict(route=key[0], painter_id=key[1], condition=key[2],
                     requested_quality=key[3], reported_quality=key[4], n=len(rows),
                     request_ids=sorted(r["request_id"] for r in rows),
                     brief_counts=dict(sorted(Counter(r["brief_id"] for r in rows).items())))
                for key, rows in sorted(groups.items(), key=lambda item: repr(item[0]))],
    )


def analyze(bundle):
    """Consume the pinned revision loader bundle; return finite JSON-native results.

    Required: measured reference/generated rows; scalers; requests; config.briefs
    and config.repetitions. Image files and response bodies are not read here.
    """
    for stage in ("reference", "generated"):
        _validate_rows(bundle[stage], stage)
    brief_list = bundle["config"]["briefs"]
    brief_spec = {b["brief_id"]: b for b in brief_list}
    if not brief_spec or len(brief_spec) != len(brief_list):
        raise ValueError("empty or duplicated brief design")
    repetitions = bundle["config"]["repetitions"]
    if not isinstance(repetitions, int) or repetitions < 2:
        raise ValueError("at least two designed repetitions required")
    cells = [_cell(bundle["generated"], route, painter, brief_spec, repetitions)
             for route in ROUTES for painter in PAINTERS]
    result = dict(
        schema="painter_responsiveness_v1.phase1.v1", status="post_result_descriptive",
        pipeline="primary512", metric_view="original31", feature_names=list(NAMES),
        methods=dict(
            empirical_variance="Population-denominator identity under equal brief/repetition mass; "
                               "the full scope includes between-content variation.",
            cross_repeat="For each condition and scope, subtract the across-brief mean separately "
                         "within each repetition. Average the across-brief coordinate products for "
                         "all unordered distinct repetition pairs. Retain signs and each pair.",
            interpretation="Expectation equals stable between-brief variance only with stable "
                           "brief means and zero-mean errors independent across repetitions. "
                           "The service and timing evidence do not establish these assumptions. "
                           "This is not an identified or corrected latent variance estimate.",
            displacement="Named minus free for matched brief/repetition records. Squared empirical "
                         "mean displacements contain sampling noise. Cross-repeat displacement "
                         "products use the same unverified repeat-independence assumptions.",
            inference="No OLS attenuation slope, population interval, p-value "
                      "or equivalence claim. Negative products are retained; "
                      "independent splits alone do not correct OLS.",
        ),
        cells=cells, reference_chroma=_reference_chroma(bundle),
        service_quality=_quality_inventory(bundle),
        source_counts=dict(
            primary_reference=sum(r["pipeline"] == "primary512" for r in bundle["reference"]),
            primary_generated=sum(r["pipeline"] == "primary512" for r in bundle["generated"]),
            analyzed_named_free_pairs=sum(c["n_pairs"] for c in cells),
            n_cells=len(cells), new_generated_images=0,
        ),
    )
    return json.loads(json.dumps(result, allow_nan=False))
