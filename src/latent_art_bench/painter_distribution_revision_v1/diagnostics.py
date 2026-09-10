"""Post-result coverage, metadata and fixed cross-route detection diagnostics.

This module reads numeric rows only. It never acquires or measures images, tunes
a detector, or adds a hypothesis test. Coverage draws describe this finite panel.
"""

from __future__ import annotations

from collections import Counter
from itertools import permutations

import numpy as np
from scipy.linalg import solve
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr

from latent_art_bench.painter_distribution_exploration_v1.statistics import RIDGE, kernel
from latent_art_bench.painter_distribution_study_v1.analysis import (
    mass,
    reference_folds,
    values,
    weighted_metrics,
    weights,
)
from latent_art_bench.painter_distribution_study_v1.statistics import rng_for
from latent_art_bench.painter_feature_generation_v2.features import NAMES

SEED = "2026090719"
DRAW_COUNT = 100
KS = (1, 3, 5)
TRANSFER_CONDITIONS = ("artist_free", "named")


def largest_remainder(counts, size):
    """Allocate a fixed total proportionally; alphabetical class order breaks ties."""
    if size < 1 or not counts or any(n < 1 for n in counts.values()):
        raise ValueError("positive sample size and class counts required")
    total = sum(counts.values())
    if size > total:
        raise ValueError("allocation cannot exceed its reference total")
    quotas = {c: size * n / total for c, n in sorted(counts.items())}
    result = {c: int(np.floor(q)) for c, q in quotas.items()}
    order = sorted(quotas, key=lambda c: (-(quotas[c] - result[c]), c))
    for c in order[: size - sum(result.values())]:
        result[c] += 1
    return result


def stratified_sample(labels, counts, rng):
    labels = np.asarray(labels)
    selected = []
    for content, count in sorted(counts.items()):
        available = np.flatnonzero(labels == content)
        if count < 0 or len(available) < count:
            raise ValueError("generated class support cannot supply the requested count")
        selected.extend(rng.permutation(available)[:count].tolist())
    return selected


def neighbor_geometry(reference, k):
    """Exclude self before finding the kth neighbor (k=1 uses the nearest other work)."""
    if k < 1 or len(reference) <= k:
        raise ValueError("k must be smaller than the anchor panel")
    distance = cdist(values(reference), values(reference))
    np.fill_diagonal(distance, np.inf)
    # Stable ordering makes equal-distance neighborhood membership reproducible.
    neighbors = np.argsort(distance, axis=1, kind="stable")[:, :k]
    radii = np.take_along_axis(distance, neighbors[:, -1:], axis=1)[:, 0]
    return radii, neighbors


def _range(numbers):
    return dict(
        median=float(np.median(numbers)),
        minimum=float(np.min(numbers)),
        maximum=float(np.max(numbers)),
        quantile05=float(np.quantile(numbers, 0.05)),
        quantile95=float(np.quantile(numbers, 0.95)),
    )


def coverage_cell(reference, generated, *, draws=DRAW_COUNT, key=""):
    """Coverage at fixed k, using identical query memberships across k values."""
    if draws < 1:
        raise ValueError("at least one coverage draw required")
    if not reference or not generated:
        return dict(status="unavailable", reason="empty domain")
    counts = dict(sorted(Counter(r["content_class"] for r in reference).items()))
    x, y = values(reference), values(generated)
    cross = cdist(x, y)
    labels = [r["content_class"] for r in generated]
    sample_designs = []
    for size_label, size in (("half_reference_n", len(x) // 2), ("reference_n", len(x))):
        allocation = largest_remainder(counts, size) if size else {}
        for mode in ("uniform", "reference_class_counts"):
            design = dict(size_label=size_label, sample_size=size, mode=mode)
            if not size or size > len(y):
                sample_designs.append(dict(design, status="unavailable", reason="sample size"))
                continue
            rng = rng_for(SEED, "coverage", key, size_label, mode)
            try:
                memberships = [
                    rng.permutation(len(y))[:size].tolist()
                    if mode == "uniform"
                    else stratified_sample(labels, allocation, rng)
                    for _ in range(draws)
                ]
            except ValueError as exc:
                sample_designs.append(dict(design, status="unavailable", reason=str(exc)))
                continue
            sample_designs.append(
                dict(
                    design,
                    status="available",
                    requested_class_counts=allocation if mode != "uniform" else None,
                    generated_indices=memberships,
                    observed_class_counts=[
                        dict(sorted(Counter(labels[i] for i in indices).items()))
                        for indices in memberships
                    ],
                )
            )
    results = []
    for k in KS:
        if len(x) <= k:
            results.append(dict(k=k, status="unavailable", reason="too few anchor works"))
            continue
        radii, neighbors = neighbor_geometry(reference, k)
        hit = cross <= radii[:, None]
        curves = []
        for design_index, design in enumerate(sample_designs):
            if design["status"] != "available":
                continue
            sampled_hits = np.array(
                [hit[:, indices].any(axis=1) for indices in design["generated_indices"]]
            )
            sampled = sampled_hits.mean(axis=1)
            curves.append(
                dict(
                    sample_design_index=design_index,
                    coverage=sampled.tolist(),
                    per_reference_hit_frequency=sampled_hits.mean(axis=0).tolist(),
                    **_range(sampled),
                )
            )
        per_reference = []
        for i, row in enumerate(reference):
            same = np.array([label == row["content_class"] for label in labels])
            nearest = int(np.argmin(cross[i]))
            per_reference.append(
                dict(
                    image_id=row["image_id"],
                    content_class=row["content_class"],
                    radius=float(radii[i]),
                    neighbor_image_ids=[reference[j]["image_id"] for j in neighbors[i]],
                    cross_class_anchor_neighbors=sum(
                        reference[j]["content_class"] != row["content_class"]
                        for j in neighbors[i]
                    ),
                    hit=bool(hit[i].any()),
                    generated_hit_count=int(hit[i].sum()),
                    same_class_hit_count=int(hit[i, same].sum()),
                    cross_class_hit_count=int(hit[i, ~same].sum()),
                    nearest_generated_image_id=generated[nearest]["image_id"],
                    nearest_generated_content_class=labels[nearest],
                    nearest_generated_distance=float(cross[i, nearest]),
                )
            )
        results.append(
            dict(
                k=k,
                status="available",
                all_available=float(hit.any(axis=1).mean()),
                curves=curves,
                per_reference=per_reference,
            )
        )
    return dict(
        status="available",
        n_original=len(x),
        n_generated=len(y),
        reference_class_counts=counts,
        generated_class_counts=dict(sorted(Counter(labels).items())),
        generated_image_ids=[r["image_id"] for r in generated],
        sample_designs=sample_designs,
        k_results=results,
    )


def heldout_design(reference, *, draws=DRAW_COUNT, key=""):
    """Equal-size disjoint anchor/test sets with floor(class N / 2) works each."""
    counts = dict(sorted(Counter(r["content_class"] for r in reference).items()))
    allocation = {c: n // 2 for c, n in counts.items()}
    if draws < 1:
        raise ValueError("at least one held-out draw required")
    if not allocation or min(allocation.values()) < 1 or sum(allocation.values()) <= 1:
        return dict(status="unavailable", reason="insufficient within-class disjoint support")
    labels = np.array([r["content_class"] for r in reference])
    rng = rng_for(SEED, "heldout_anchor", key)
    memberships = []
    for _ in range(draws):
        anchor, test = [], []
        for c, n in allocation.items():
            selected = rng.permutation(np.flatnonzero(labels == c))[: 2 * n]
            anchor.extend(selected[:n].tolist())
            test.extend(selected[n:].tolist())
        memberships.append(dict(anchor_indices=anchor, real_query_indices=test))
    return dict(
        status="available",
        reference_image_ids=[r["image_id"] for r in reference],
        class_counts_per_group=allocation,
        group_size=sum(allocation.values()),
        memberships=memberships,
    )


def heldout_coverage(reference, generated, design, *, key=""):
    if design["status"] != "available":
        return dict(status="unavailable", reason=design["reason"])
    labels = [r["content_class"] for r in generated]
    rng = rng_for(SEED, "heldout_generated", key)
    try:
        queries = [
            stratified_sample(labels, design["class_counts_per_group"], rng)
            for _ in design["memberships"]
        ]
    except ValueError as exc:
        return dict(status="unavailable", reason=str(exc))
    results = []
    for k in KS:
        if design["group_size"] <= k:
            results.append(dict(k=k, status="unavailable", reason="too few anchor works for k"))
            continue
        real_cover, generated_cover, radius_medians = [], [], []
        for membership, generated_indices in zip(design["memberships"], queries):
            anchors = [reference[i] for i in membership["anchor_indices"]]
            real_queries = [reference[i] for i in membership["real_query_indices"]]
            radii, _ = neighbor_geometry(anchors, k)
            x = values(anchors)
            real_cross = cdist(x, values(real_queries))
            gen_cross = cdist(x, values([generated[i] for i in generated_indices]))
            real_cover.append(float((real_cross <= radii[:, None]).any(axis=1).mean()))
            generated_cover.append(float((gen_cross <= radii[:, None]).any(axis=1).mean()))
            radius_medians.append(float(np.median(radii)))
        results.append(
            dict(
                k=k,
                status="available",
                real_query_coverage=real_cover,
                generated_query_coverage=generated_cover,
                paired_generated_minus_real=(
                    np.asarray(generated_cover) - np.asarray(real_cover)
                ).tolist(),
                median_anchor_radius=radius_medians,
                real_summary=_range(real_cover),
                generated_summary=_range(generated_cover),
            )
        )
    return dict(status="available", generated_query_indices=queries, k_results=results)


def _dimensions(row):
    metadata = row.get("normalization", {})
    width = metadata.get("original_width", row.get("width"))
    height = metadata.get("original_height", row.get("height"))
    if not width or not height or min(width, height) <= 0:
        return None
    return width, height


def descriptors(row):
    dimensions = _dimensions(row)
    metadata = row.get("normalization", {})
    result = dict(
        parent_surrogate_short_side=row.get("native_short_side"),
        embedded_profile=(
            int(metadata["color_profile"] == "embedded_to_srgb")
            if "color_profile" in metadata else None
        ),
        border_flag=int(row["border_flag"]) if row.get("border_flag") is not None else None,
    )
    if dimensions:
        width, height = dimensions
        result.update(
            aspect_ratio=width / height,
            absolute_log_aspect_ratio=abs(float(np.log(width / height))),
            square=int(width == height),
            delivered_short_side=min(width, height),
            log_delivered_pixel_count=float(np.log(width * height)),
        )
    else:
        result.update(dict.fromkeys((
            "aspect_ratio", "absolute_log_aspect_ratio", "square",
            "delivered_short_side", "log_delivered_pixel_count",
        )))
    return result


def nuisance_summary(rows):
    """Descriptive within-stratum Spearman associations; no causal adjustment or p values."""
    observed = [descriptors(r) for r in rows]
    association = []
    for name in sorted(observed[0]):
        indices = [i for i, r in enumerate(observed) if r[name] is not None]
        entry = dict(descriptor=name, n_available=len(indices), n_missing=len(rows) - len(indices))
        x = np.array([observed[i][name] for i in indices], dtype=float)
        if len(x) < 3 or len(set(x)) < 2:
            association.append(dict(entry, status="unavailable", reason="missing or constant"))
            continue
        y = values([rows[i] for i in indices])
        correlations = {}
        for feature_index, feature_name in enumerate(NAMES):
            coordinate = y[:, feature_index]
            correlations[feature_name] = (
                float(spearmanr(x, coordinate).statistic) if len(set(coordinate)) > 1 else None
            )
        association.append(dict(entry, status="available", feature_spearman=correlations))
    metadata = dict(
        n=len(rows),
        square_counts=dict(sorted(Counter(str(r["square"]) for r in observed).items())),
        color_profile_counts=dict(sorted(Counter(
            r.get("normalization", {}).get("color_profile", "unknown") for r in rows
        ).items())),
        format_counts=dict(sorted(Counter(
            r.get("image_format") or "unknown" for r in rows
        ).items())),
        border_counts=dict(sorted(Counter(
            str(r["border_flag"]) if r.get("border_flag") is not None else "unknown"
            for r in rows
        ).items())),
        source_proxy_counts=dict(sorted(Counter(r.get("source_id", "unknown") for r in rows)
                                       .items())),
        capture_workflow_counts=dict(sorted(Counter(
            r.get("capture_workflow", "unresolved") for r in rows
        ).items())),
        descriptor_ranges={
            name: dict(n_available=len(present), **_range(present)) if present
            else dict(n_available=0)
            for name in sorted(observed[0])
            for present in [[r[name] for r in observed if r[name] is not None]]
        },
    )
    return dict(metadata=metadata, associations=association)


def square_baseline(reference, generated):
    real = [_dimensions(r) for r in reference]
    fake = [_dimensions(r) for r in generated]
    if any(d is None for d in real + fake):
        return dict(status="unavailable", reason="missing delivered dimensions")
    target = mass(reference)
    try:
        wr, wg = weights(reference, target), weights(generated, target)
    except ValueError as exc:
        return dict(status="unavailable", reason=str(exc))
    rs = np.array([1 if w == h else -1 for w, h in real])
    gs = np.array([1 if w == h else -1 for w, h in fake])
    return dict(
        status="available", rule="predict generated exactly when delivered width equals height",
        original_square_n=int((rs > 0).sum()), generated_square_n=int((gs > 0).sum()),
        **weighted_metrics(rs, gs, wr, wg),
    )


def transfer_membership(reference, source, target):
    """Reuse original work folds and brief index modulo six across both routes."""
    if len(reference) < 6 or not source or not target:
        return dict(status="unavailable", reason="insufficient domains for six folds")
    rf = reference_folds(reference, 6)
    sf = np.array([r["brief_index"] % 6 for r in source])
    tf = np.array([r["brief_index"] % 6 for r in target])
    memberships = []
    for fold in range(6):
        train_real = np.flatnonzero(rf != fold).tolist()
        test_real = np.flatnonzero(rf == fold).tolist()
        train_gen = np.flatnonzero(sf != fold).tolist()
        test_gen = np.flatnonzero(tf == fold).tolist()
        train_ids = {reference[i]["image_id"] for i in train_real}
        train_ids.update(source[i]["image_id"] for i in train_gen)
        test_ids = {reference[i]["image_id"] for i in test_real}
        test_ids.update(target[i]["image_id"] for i in test_gen)
        train_briefs = {source[i]["brief_id"] for i in train_gen}
        test_briefs = {target[i]["brief_id"] for i in test_gen}
        if train_ids & test_ids or train_briefs & test_briefs:
            raise ValueError("work or brief identity leaks across transfer split")
        if not all((train_real, test_real, train_gen, test_gen)):
            return dict(status="unavailable", reason="empty fold domain")
        memberships.append(dict(
            fold=fold, train_reference_indices=train_real, test_reference_indices=test_real,
            train_source_indices=train_gen, test_target_indices=test_gen,
        ))
    return dict(status="available", memberships=memberships)


def cross_route_classify(reference, source, target, design, kind):
    if design["status"] != "available":
        return dict(status="unavailable", reason=design["reason"])
    target_mass = mass(reference)
    real_scores = np.full(len(reference), np.nan)
    gen_scores = np.full(len(target), np.nan)
    fold_results = []
    source_items, target_items = reference + source, reference + target
    train_gram = kernel(values(source_items), values(source_items), kind)
    cross_gram = kernel(values(target_items), values(source_items), kind)
    try:
        wr, wg = weights(reference, target_mass), weights(target, target_mass)
        for split in design["memberships"]:
            ri, gi = split["train_reference_indices"], split["train_source_indices"]
            rt, gt = split["test_reference_indices"], split["test_target_indices"]
            tr, tg = [reference[i] for i in ri], [source[i] for i in gi]
            w = 0.5 * np.r_[weights(tr, target_mass), weights(tg, target_mass)]
            train_indices = np.r_[ri, np.array(gi) + len(reference)]
            test_indices = np.r_[rt, np.array(gt) + len(reference)]
            square = np.sqrt(w)
            system = train_gram[np.ix_(train_indices, train_indices)] * np.outer(square, square)
            system.flat[:: len(system) + 1] += RIDGE
            labels = np.r_[-np.ones(len(ri)), np.ones(len(gi))]
            coefficient = square * solve(system, square * labels, assume_a="pos")
            scores = cross_gram[np.ix_(test_indices, train_indices)] @ coefficient
            real_scores[rt], gen_scores[gt] = scores[:len(rt)], scores[len(rt):]
            fold_results.append(dict(
                fold=split["fold"], n_train_original=len(ri), n_train_generated=len(gi),
                n_test_original=len(rt), n_test_generated=len(gt),
                train_original_class_counts=dict(sorted(Counter(
                    reference[i]["content_class"] for i in ri
                ).items())),
                train_generated_class_counts=dict(sorted(Counter(
                    source[i]["content_class"] for i in gi
                ).items())),
                test_original_class_counts=dict(sorted(Counter(
                    reference[i]["content_class"] for i in rt
                ).items())),
                test_generated_class_counts=dict(sorted(Counter(
                    target[i]["content_class"] for i in gt
                ).items())),
                false_positive_n=int((real_scores[rt] >= 0).sum()),
                false_negative_n=int((gen_scores[gt] < 0).sum()),
                **weighted_metrics(real_scores[rt], gen_scores[gt],
                                   wr[rt] / wr[rt].sum(), wg[gt] / wg[gt].sum()),
            ))
    except ValueError as exc:
        return dict(status="unavailable", reason=str(exc))
    if not np.isfinite(np.r_[real_scores, gen_scores]).all():
        raise ValueError("not every target observation received a held-out score")
    pooled = weighted_metrics(real_scores, gen_scores, wr, wg)
    pooled.pop("auc")  # Cross-fold score scales need not be calibrated.
    return dict(
        status="available", pooled_threshold_metrics=pooled, fold_metrics=fold_results,
        mean_fold_auc=float(np.mean([r["auc"] for r in fold_results])),
        auc_interpretation="AUC is within fold; the arithmetic mean is descriptive only",
        original_scores=real_scores.tolist(), target_generated_scores=gen_scores.tolist(),
    )


def analyze(bundle):
    reference = sorted(
        [r for r in bundle["reference"] if r["pipeline"] == "primary512"],
        key=lambda r: r["image_id"],
    )
    generated = sorted(
        [r for r in bundle["generated"] if r["pipeline"] == "primary512"],
        key=lambda r: r["image_id"],
    )
    output = dict(
        pipeline="primary512", feature_set="all31", seed=SEED, draws=DRAW_COUNT,
        coverage=[], heldout_reference_designs=[], metadata=[], cross_route_transfer=[],
        source_holdout=dict(
            status="unavailable",
            reason="No independently verified capture-workflow labels or crossed workflow support; "
                   "collection identifiers are source proxies, not capture workflows.",
        ),
        interpretation=dict(
            coverage="Finite-panel descriptive occupancy, not equivalence. Subsample draw ranges "
                     "are not population confidence intervals. Anchor radii change in the held-out "
                     "real control; compare real and generated queries under identical anchors.",
            content="Reference labels are maintainer coded; generated labels are intended prompts, "
                    "not independently verified depicted content.",
            metadata="Within-original/painter and within-generated/painter/route/condition "
                     "associations are descriptive; no causal attribution or nuisance removal.",
            detector="Fixed original scaler, six whole-brief/work-disjoint folds, ridge 0.01, "
                     "linear dot/d+1 or RBF exp(-squared_distance/d)+1. Train and score each "
                     "domain with the reference content mass; no hyperparameter tuning.",
        ),
    )
    for painter in sorted({r["painter_id"] for r in reference}):
        real = [r for r in reference if r["painter_id"] == painter]
        fake = [r for r in generated if r["painter_id"] == painter]
        design = heldout_design(real, key=painter)
        output["heldout_reference_designs"].append(dict(painter_id=painter, **design))
        output["metadata"].append(dict(
            painter_id=painter, domain="original", **nuisance_summary(real),
        ))
        groups = sorted({(r["route"], r["condition"]) for r in fake})
        for route, condition in groups:
            selected = [r for r in fake if (r["route"], r["condition"]) == (route, condition)]
            label = dict(painter_id=painter, route=route, condition=condition)
            key = ":".join((painter, route, condition))
            output["coverage"].append(dict(
                label, **coverage_cell(real, selected, key=key),
                heldout_real_control=heldout_coverage(real, selected, design, key=key),
                square_metadata_baseline=square_baseline(real, selected),
            ))
            output["metadata"].append(dict(
                label, domain="generated", **nuisance_summary(selected),
            ))
        routes = sorted({r["route"] for r in fake})
        for source_route, target_route in permutations(routes, 2):
            for condition in TRANSFER_CONDITIONS:
                source = [r for r in fake if r["route"] == source_route
                          and r["condition"] == condition]
                target = [r for r in fake if r["route"] == target_route
                          and r["condition"] == condition]
                split = transfer_membership(real, source, target)
                output["cross_route_transfer"].append(dict(
                    painter_id=painter, source_route=source_route, target_route=target_route,
                    condition=condition,
                    reference_image_ids=[r["image_id"] for r in real],
                    source_image_ids=[r["image_id"] for r in source],
                    target_image_ids=[r["image_id"] for r in target],
                    split=split,
                    kernels={kind: cross_route_classify(real, source, target, split, kind)
                             for kind in ("linear", "rbf")},
                ))
    return output
