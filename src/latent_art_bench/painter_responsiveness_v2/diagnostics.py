"""Fixed-feature, split-repetition scene retrieval from retained numeric rows only.

Training and testing stay within the same generation condition. Uniform positive
contraction/translation preserves retrieval geometry; smaller between-scene trace
therefore need not imply less scene-distinctness. No feature transform is fitted.
"""

from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES, NAMES

PIPELINES = ("primary512", "resolution256", "jpeg90_512")
ROUTES = ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
PAINTERS = ("claude_monet", "paul_cezanne")
CONDITIONS = ("artist_free", "named")
VIEWS = {"original31": slice(0, 31), **FAMILIES, "no_texture19": slice(0, 19)}
SUMMARY_METRICS = (
    "top1_accuracy", "fractional_tie_top1_accuracy", "mean_midrank", "mean_lexicographic_rank",
    "mean_own_distance", "mean_nearest_other_distance", "mean_other_minus_own_distance",
)


def _summary(rows, scope):
    counts = {r["candidate_count"] for r in rows}
    return dict(
        scope=scope, queries=len(rows), candidate_counts=sorted(counts),
        chance_top1=float(np.mean([1 / r["candidate_count"] for r in rows])),
        chance_mean_rank=float(np.mean([(r["candidate_count"] + 1) / 2 for r in rows])),
        top1_accuracy=float(np.mean([r["correct"] for r in rows])),
        fractional_tie_top1_accuracy=float(np.mean([r["fractional_tie_correct"] for r in rows])),
        mean_midrank=float(np.mean([r["midrank"] for r in rows])),
        mean_lexicographic_rank=float(np.mean([r["lexicographic_rank"] for r in rows])),
        mean_own_distance=float(np.mean([r["own_distance"] for r in rows])),
        mean_nearest_other_distance=float(np.mean([r["nearest_other_distance"] for r in rows])),
        mean_other_minus_own_distance=float(np.mean([r["other_minus_own_distance"] for r in rows])),
        queries_with_top_ties=sum(len(r["nearest_brief_ids"]) > 1 for r in rows),
        queries_with_own_rank_ties=sum(r["rank_worst"] > r["rank_best"] for r in rows),
    )


def _prediction(distances, candidate_indices, own, briefs):
    candidates = sorted(candidate_indices, key=lambda i: (distances[i], briefs[i]))
    own_distance = distances[own]
    top = distances[candidates[0]]
    nearest = sorted(briefs[i] for i in candidates if distances[i] == top)
    others = [i for i in candidates if i != own]
    other_distance = min(distances[i] for i in others)
    rank_best = 1 + sum(distances[i] < own_distance for i in candidates)
    rank_worst = sum(distances[i] <= own_distance for i in candidates)
    return dict(
        candidate_count=len(candidates), predicted_brief_id=briefs[candidates[0]],
        nearest_brief_ids=nearest, correct=candidates[0] == own,
        fractional_tie_correct=1 / len(nearest) if briefs[own] in nearest else 0.0,
        rank_best=int(rank_best), rank_worst=int(rank_worst),
        midrank=float((rank_best + rank_worst) / 2),
        lexicographic_rank=candidates.index(own) + 1,
        own_distance=float(own_distance), nearest_other_distance=float(other_distance),
        nearest_other_brief_ids=sorted(briefs[i] for i in others
                                      if distances[i] == other_distance),
        other_minus_own_distance=float(other_distance - own_distance),
    )


def retrieve(x, brief_ids, image_ids, content_classes):
    """Use two other repetitions for each centroid, never the held query repetition.

    The small public helper supports synthetic fixed-scene tests. Main analyze()
    separately enforces the actual 24-brief/three-repeat inventory. Exact computed
    Euclidean-distance ties are retained; lexical ID order is the deterministic
    top1 policy. Midrank and fractional top1 also expose ambiguity without breaking
    ties in favor of the correct label. Same-content retrieval restricts candidates
    to the query's recorded prompt class, not a new visual-content annotation.
    """
    x = np.asarray(x, dtype=float)
    if (x.ndim != 3 or x.shape[1] != 3 or not x.shape[2]
            or not np.isfinite(x).all() or x.shape[0] != len(brief_ids)):
        raise ValueError("retrieval requires finite scene-by-three-repeat feature vectors")
    if len(set(brief_ids)) != len(brief_ids) or len(content_classes) != len(brief_ids):
        raise ValueError("distinct brief identities and matching content labels are required")
    if any(count < 2 for count in Counter(content_classes).values()):
        raise ValueError("each within-content retrieval scope needs at least two briefs")
    if (len(image_ids) != len(brief_ids) or any(len(row) != 3 for row in image_ids)
            or len({i for row in image_ids for i in row}) != 3 * len(brief_ids)):
        raise ValueError("every brief/repetition needs a distinct image identity")
    predictions = []
    for held in range(3):
        train = [r for r in range(3) if r != held]
        centroid = x[:, train, :].mean(axis=1)
        # Only the other two repetitions enter all candidate centroids in this fold.
        distances = np.sqrt(np.square(x[:, held, None, :] - centroid[None, :, :]).sum(axis=2))
        for own, brief in enumerate(brief_ids):
            same_content = [i for i, c in enumerate(content_classes) if c == content_classes[own]]
            for scope, candidates in (("all_briefs", range(len(brief_ids))),
                                      ("same_content", same_content)):
                predictions.append(dict(
                    image_id=image_ids[own][held], brief_id=brief, held_repetition=held,
                    content_class=content_classes[own], candidate_scope=scope,
                    **_prediction(distances[own], candidates, own, brief_ids),
                ))
    summaries = [_summary([r for r in predictions if r["candidate_scope"] == scope], scope)
                 for scope in ("all_briefs", "same_content")]
    summaries += [_summary([r for r in predictions if r["candidate_scope"] == "same_content"
                           and r["content_class"] == content], "same_content:" + content)
                  for content in sorted(set(content_classes))]
    means = x.mean(axis=1)
    for item in summaries:
        scope = item["scope"]
        selected = [i for i, c in enumerate(content_classes)
                    if ":" not in scope or c == scope.split(":", 1)[1]]
        local = x[selected]
        if scope == "same_content":
            centers = np.array([means[[i for i, c in enumerate(content_classes)
                                      if c == content_classes[b]]].mean(axis=0) for b in selected])
        else:
            centers = local.mean(axis=(0, 1))
        item["between_brief_trace"] = float(
            np.square(local.mean(axis=1) - centers).sum(axis=1).mean())
        item["within_brief_trace"] = float(
            np.square(local - local.mean(axis=1)[:, None, :]).sum(axis=2).mean())
    return dict(
        summaries=summaries, predictions=predictions,
        between_brief_trace=float(np.square(means - means.mean(axis=0)).sum(axis=1).mean()),
        within_brief_trace=float(np.square(x - means[:, None, :]).sum(axis=2).mean()),
    )


def _inventory(bundle):
    brief_rows = bundle["config"]["briefs"]
    specs = {b["brief_id"]: b for b in brief_rows}
    if len(specs) != 24 or len(brief_rows) != 24 or bundle["config"]["repetitions"] != 3:
        raise ValueError("retained retrieval requires exactly 24 briefs and three repeats")
    if Counter(b["content_class"] for b in brief_rows) != {"water": 8, "built": 8, "land": 8}:
        raise ValueError("the retained design requires eight briefs per recorded broad class")
    index, identities, across_pipelines = {}, set(), defaultdict(dict)
    for row in bundle["generated"]:
        if row["condition"] not in CONDITIONS:
            continue
        key = (row["route"], row["painter_id"], row["pipeline"], row["condition"],
               row["brief_id"], row["repetition"])
        identity = row["pipeline"], row["image_id"]
        if key in index or identity in identities:
            raise ValueError("duplicate retrieval slot or image identity")
        if (row["route"] not in ROUTES or row["painter_id"] not in PAINTERS
                or row["pipeline"] not in PIPELINES or row["brief_id"] not in specs
                or type(row["repetition"]) is not int or row["repetition"] not in range(3)
                or row["status"] != "measured"):
            raise ValueError("retrieval row lies outside the fixed measured design")
        if row["content_class"] != specs[row["brief_id"]]["content_class"]:
            raise ValueError("retrieval content class differs from the recorded prompt class")
        x = np.asarray(row["scaled"], dtype=float)
        if x.shape != (31,) or not np.isfinite(x).all():
            raise ValueError("retrieval needs all 31 finite frozen-scale coordinates")
        index[key] = row
        identities.add(identity)
        across_pipelines[key[:2] + key[3:]][row["pipeline"]] = row["image_id"]
    expected = {(route, painter, pipeline, condition, brief, repetition)
                for route in ROUTES for painter in PAINTERS for pipeline in PIPELINES
                for condition in CONDITIONS for brief in specs for repetition in range(3)}
    if set(index) != expected:
        raise ValueError("retrieval requires complete named/free matched grids in every pipeline")
    if any(set(rows) != set(PIPELINES) or len(set(rows.values())) != 1
           for rows in across_pipelines.values()):
        raise ValueError("image membership differs across processing pipelines")
    return specs, index


def analyze(bundle):
    """Return descriptive retrieval, compact shared splits and matched condition changes."""
    specs, index = _inventory(bundle)
    briefs = sorted(specs)
    content = [specs[b]["content_class"] for b in briefs]
    splits, by_cell = [], {}
    queries, prediction_sets, predictions = [], [], []
    for route in ROUTES:
        for painter in PAINTERS:
            for condition in CONDITIONS:
                ids = [[index[route, painter, "primary512", condition, b, r]["image_id"]
                        for r in range(3)] for b in briefs]
                query_ids = {}
                for i, brief in enumerate(briefs):
                    for repetition in range(3):
                        query_ids[brief, repetition] = len(queries)
                        queries.append(dict(
                            query_id=len(queries), image_id=ids[i][repetition], brief_id=brief,
                            repetition=repetition, content_class=content[i], route=route,
                            painter_id=painter, condition=condition,
                        ))
                split_ids = []
                for held in range(3):
                    split_id = f"{route}:{painter}:{condition}:hold-r{held}"
                    split_ids.append(split_id)
                    splits.append(dict(
                        split_id=split_id, route=route, painter_id=painter, condition=condition,
                        held_repetition=held,
                        training_repetitions=[r for r in range(3) if r != held],
                        centroids=[dict(brief_id=b, query_ids=[query_ids[b, r] for r in range(3)
                                                             if r != held]) for b in briefs],
                        query_ids=[query_ids[b, held] for b in briefs],
                    ))
                for pipeline in PIPELINES:
                    x = np.asarray([[index[route, painter, pipeline, condition, b, r]["scaled"]
                                     for r in range(3)] for b in briefs])
                    for view, columns in VIEWS.items():
                        cell_id = f"{pipeline}:{view}:{route}:{painter}:{condition}"
                        result = retrieve(x[..., columns], briefs, ids, content)
                        prediction_set_id = len(prediction_sets)
                        prediction_sets.append(dict(
                            prediction_set_id=prediction_set_id, pipeline=pipeline, view=view,
                            route=route, painter_id=painter, condition=condition,
                            split_ids=split_ids, feature_count=len(NAMES[columns]),
                        ))
                        for row in result.pop("predictions"):
                            query_id = query_ids[row["brief_id"], row["held_repetition"]]
                            predictions.append(dict(
                                prediction_set_id=prediction_set_id, query_id=query_id,
                                **{k: v for k, v in row.items() if k not in {
                                    "image_id", "brief_id", "held_repetition", "content_class"}},
                            ))
                        cell = dict(cell_id=cell_id, pipeline=pipeline, view=view, route=route,
                                    painter_id=painter, condition=condition, split_ids=split_ids,
                                    prediction_set_id=prediction_set_id,
                                    feature_count=len(NAMES[columns]), **result)
                        by_cell[pipeline, view, route, painter, condition] = cell
    cells = []
    for pipeline in PIPELINES:
        for view in VIEWS:
            for route in ROUTES:
                for painter in PAINTERS:
                    before = by_cell[pipeline, view, route, painter, "artist_free"]
                    after = by_cell[pipeline, view, route, painter, "named"]
                    for free, named in zip(before["summaries"], after["summaries"]):
                        if free["scope"] != named["scope"]:
                            raise ValueError("condition retrieval scopes do not match")
                        denominator = free["between_brief_trace"]
                        cells.append(dict(
                            pipeline=pipeline, view=view, route=route, painter_id=painter,
                            candidate_scope=free["scope"],
                            before=dict(free, condition="artist_free",
                                        prediction_set_id=before["prediction_set_id"]),
                            after=dict(named, condition="named",
                                       prediction_set_id=after["prediction_set_id"]),
                            named_minus_free={k: named[k] - free[k] for k in SUMMARY_METRICS},
                            named_free_between_brief_trace_ratio=(named["between_brief_trace"]
                                                                 / denominator if denominator > 0
                                                                 else None),
                        ))
    return dict(
        schema="painter_responsiveness_v2.retrieval.v1", status="post_result_descriptive",
        methods=dict(
            transform="Unchanged per-pipeline development-scaled coordinates supplied by the "
                      "retained loader; no generated-data scaler, PCA or tuned metric.",
            distance="Euclidean distance to each brief's mean of the two other repetitions; "
                     "held repetition excluded from every centroid. "
                     "Train/test use the same condition.",
            ties="Exact equality of computed float64 Euclidean distances; no tolerance. "
                 "Top1 and deterministic rank use lexical brief ID; also report all nearest ties, "
                 "fractional tie top1, and average best/worst rank (midrank).",
            content_control="Restrict candidates to the query's recorded prompt class: eight "
                            "briefs/class. This is not independent visual content validation.",
            mass="Every one of the 24 fixed briefs and three held repetitions has equal mass; "
                 "all three classes have eight briefs. No resampling or model tuning.",
            trace_scope="Equal-mass empirical between-brief/within-brief traces match each "
                        "view and scope. Pooled same-content between trace centers each brief "
                        "mean within its recorded class, removing between-class variation.",
            interpretation="Within-condition repeat retrieval describes scene-associated geometry. "
                           "Uniform contraction preserves retrieval and naming can reduce noise "
                           "enough to improve it. Neither direction establishes causal scene "
                           "fidelity, painter style, human perception or new-scene generalization. "
                           "There are no p-values, population intervals or new generation calls.",
            identity_tables="Every prediction joins prediction_sets on prediction_set_id and "
                            "queries on query_id. Splits use those same query IDs for exact "
                            "training-image and held-image membership; no features are duplicated.",
        ),
        views={name: list(NAMES[section]) for name, section in VIEWS.items()},
        brief_ids=briefs, splits=splits, cells=cells, queries=queries,
        prediction_sets=prediction_sets, predictions=predictions,
        counts=dict(cells=len(cells), prediction_sets=len(prediction_sets), splits=len(splits),
                    predictions=len(predictions),
                    selected_unique_images=len(index) // len(PIPELINES),
                    selected_vector_rows=len(index), new_images=0),
    )
