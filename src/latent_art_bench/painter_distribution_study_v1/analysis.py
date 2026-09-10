"""Fixed finite-reference endpoints, paired prompt tests and distribution diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.linalg import solve
from scipy.spatial.distance import cdist

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_distribution_exploration_v1.statistics import (
    RIDGE,
    kernel,
    pca_fit,
    project,
)
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    events,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.randomization import holm

from . import inference
from . import study as s
from .statistics import distribution_summary, rng_for

FEATURE_SETS = {"all31": slice(0, 31), **FAMILIES}


def mass(rows):
    counts = Counter(r["content_class"] for r in rows)
    return {c: n / len(rows) for c, n in counts.items()}


def weights(rows, target):
    if not rows or not np.isclose(sum(target.values()), 1) or any(v < 0 for v in target.values()):
        raise ValueError("invalid content probability target")
    counts = Counter(r["content_class"] for r in rows)
    if any(v > 0 and counts[c] == 0 for c, v in target.items()):
        raise ValueError("required content support is absent")
    return np.array([target.get(r["content_class"], 0) / counts[r["content_class"]] for r in rows])


def values(rows):
    return np.array([r["scaled"] for r in rows])


def energy(x, y, wx, wy):
    return float(2 * wx @ cdist(x, y) @ wy - wx @ cdist(x, x) @ wx - wy @ cdist(y, y) @ wy)


def variant(reference, generated, target, name):
    real, fake = reference, generated
    if name == "unambiguous":
        real = [r for r in real if not r["mixed_uncertain"]]
        target = mass(real)
    elif name == "native1024":
        real = [r for r in real if r["native_short_side"] >= 1024]
        target = mass(real)
    elif name == "initial_only":
        fake = [r for r in fake if r["initial_only_eligible"]]
    elif name == "equal_content":
        target = dict.fromkeys(s.CLASSES, 1 / 3)
    elif name not in ("reference_content", "collected"):
        raise ValueError("unknown content sensitivity")
    if name == "collected":
        return real, fake, np.full(len(real), 1 / len(real)), np.full(len(fake), 1 / len(fake))
    fake = [r for r in fake if target.get(r["content_class"], 0) > 0]
    return real, fake, weights(real, target), weights(fake, target)


def cell_summaries(reference, generated, target, label):
    result = []
    for name in (
        "reference_content",
        "collected",
        "equal_content",
        "unambiguous",
        "native1024",
        "initial_only",
    ):
        try:
            real, fake, wx, wy = variant(reference, generated, target, name)
            if min(len(real), len(fake)) < 2:
                raise ValueError("insufficient measured observations")
        except (ValueError, ZeroDivisionError):
            result.extend(
                dict(label, weighting=name, feature_set=family, status="unavailable")
                for family in FEATURE_SETS
            )
            continue
        for family, section in FEATURE_SETS.items():
            summary = distribution_summary(
                values(real)[:, section], values(fake)[:, section], wx, wy
            )
            result.append(
                dict(
                    label,
                    weighting=name,
                    feature_set=family,
                    status="available",
                    n_original=len(real),
                    n_generated=len(fake),
                    **summary,
                )
            )
    return result


def paired(
    reference, generated, target, route, painter, before, after, config, endpoint, run_test=True
):
    selected = [r for r in generated if r["route"] == route and r["painter_id"] == painter]
    lookup = {(r["brief_id"], r["repetition"], r["condition"]): r for r in selected}
    if len(lookup) != len(selected):
        raise ValueError("duplicate paired slot measurement")
    a, b, excluded = [], [], []
    for brief in config["briefs"]:
        for repetition in range(3):
            key = brief["brief_id"], repetition
            first, second = lookup.get((*key, before)), lookup.get((*key, after))
            if first is None or second is None:
                excluded.append(
                    dict(
                        brief_id=key[0],
                        repetition=repetition,
                        before_measured=first is not None,
                        after_measured=second is not None,
                    )
                )
                continue
            if any(
                first[k] != second[k] for k in ("window", "content_class", "brief_id", "repetition")
            ):
                raise ValueError("conditions do not share a randomized group")
            a.append(first)
            b.append(second)
    result = dict(
        endpoint_index=endpoint,
        route=route,
        painter_id=painter,
        before=before,
        after=after,
        pairs=len(a),
        distinct_briefs=len({r["brief_id"] for r in a}),
        excluded_pairs=excluded,
        status="unavailable",
        raw_p=1.0,
    )
    try:
        wr, wg = weights(reference, target), weights(a, target)
        if len(a) < 24 or result["distinct_briefs"] < 12:
            return result
    except ValueError:
        return result
    coefficients = inference.paired_contributions(values(reference), values(a), values(b), wr, wg)
    if run_test:
        test, checked = inference.test_contrast(
            values(reference),
            values(a),
            values(b),
            seed=config["analysis_seed"] + endpoint,
            reference_weights=wr,
            pair_weights=wg,
        )
        if not np.array_equal(checked, coefficients):
            raise ValueError("paired computation disagrees")
        result.update(test)
        result["null"] = (
            "sharp no effect on availability and features under the fixed slot policy, "
            "with no interference"
        )
    else:
        result.update(status="descriptive", estimate=float(coefficients.sum()))
    result["contributions"] = [
        dict(
            before_image_id=x["image_id"],
            after_image_id=y["image_id"],
            brief_id=x["brief_id"],
            repetition=x["repetition"],
            window=x["window"],
            weight=float(w),
            contribution=float(c),
        )
        for x, y, w, c in zip(a, b, wg, coefficients)
    ]
    return result


def prompt_endpoints(reference, generated, targets, config):
    specs = [(route, p, "artist_free", "named") for route in s.ROUTES for p in s.PAINTERS]
    specs += [(s.ROUTES[2], p, "generic_named", "named") for p in s.PAINTERS]
    results, sensitivities = [], []
    for index, (route, p, before, after) in enumerate(specs):
        real = [r for r in reference if r["painter_id"] == p]
        result = paired(real, generated, targets[p], route, p, before, after, config, index)
        results.append(result)
        for kind, excluded in [("window", i) for i in range(8)] + [
            ("brief_id", b["brief_id"]) for b in config["briefs"]
        ]:
            reduced = [r for r in generated if r[kind] != excluded]
            sensitivity = paired(
                real, reduced, targets[p], route, p, before, after, config, index, run_test=False
            )
            sensitivities.append(
                dict(
                    endpoint_index=index,
                    excluded_kind=kind,
                    excluded_value=excluded,
                    status=sensitivity["status"],
                    pairs=sensitivity["pairs"],
                    estimate=sensitivity.get("estimate"),
                )
            )
    for row, adjusted in zip(results, holm([r["raw_p"] for r in results])):
        row["holm_p"] = float(adjusted)
        row["reject_at_05"] = adjusted <= 0.05 and row["status"] != "unavailable"
    return results, sensitivities


def baseline(reference, generated, target, rng, draws=999):
    indices = {
        c: np.array([i for i, r in enumerate(reference) if r["content_class"] == c]) for c in target
    }
    gi = {
        c: np.array([i for i, r in enumerate(generated) if r["content_class"] == c]) for c in target
    }
    counts = {c: len(ix) // 2 for c, ix in indices.items()}
    if any(n < 1 or len(gi[c]) < n for c, n in counts.items()):
        return dict(status="unavailable", reason="insufficient disjoint content support")
    rr, rg = [], []
    x, y = values(reference), values(generated)
    weight = np.concatenate([np.full(n, target[c] / n) for c, n in counts.items()])
    for _ in range(draws):
        first, second, fake = [], [], []
        for c, n in counts.items():
            sampled = rng.permutation(indices[c])[: 2 * n]
            first.extend(sampled[:n])
            second.extend(sampled[n:])
            fake.extend(rng.permutation(gi[c])[:n])
        rr.append(energy(x[first], x[second], weight, weight))
        rg.append(energy(x[first], y[fake], weight, weight))
    return dict(
        status="available",
        draws=draws,
        group_size=sum(counts.values()),
        class_counts=counts,
        real_real_energy=rr,
        original_generated_energy=rg,
        real_real_median=float(np.median(rr)),
        original_generated_median=float(np.median(rg)),
    )


def coverage(reference, generated, target, rng, draws=100):
    if len(reference) < 4 or not generated:
        return dict(status="unavailable")
    try:
        wr = weights(reference, target)
    except ValueError:
        return dict(status="unavailable")
    x, y = values(reference), values(generated)
    within = cdist(x, x)
    np.fill_diagonal(within, np.inf)
    radii = np.partition(within, 2, axis=1)[:, 2]
    cross = cdist(x, y)
    indicators = cross <= radii[:, None]
    n = min(len(reference), len(generated))
    sampled = [
        float(wr @ indicators[:, rng.permutation(len(y))[:n]].any(axis=1)) for _ in range(draws)
    ]
    return dict(
        status="available",
        k=3,
        all_available=float(wr @ indicators.any(axis=1)),
        sample_size=n,
        sampled_coverage=sampled,
        sampled_median=float(np.median(sampled)),
        original_radii=radii.tolist(),
    )


def weighted_metrics(real_scores, generated_scores, wr, wg):
    specificity = float(wr @ (real_scores < 0))
    recall = float(wg @ (generated_scores >= 0))
    difference = generated_scores[:, None] - real_scores[None, :]
    auc = float(wg @ ((difference > 0) + 0.5 * (difference == 0)) @ wr)
    return dict(
        balanced_accuracy=(specificity + recall) / 2,
        auc=auc,
        real_specificity=specificity,
        generated_recall=recall,
    )


def reference_folds(reference, count):
    if len({r["image_id"] for r in reference}) != len(reference):
        raise ValueError("duplicate physical work in classification")
    assigned, offset = {}, 0
    for content in s.CLASSES:
        ordered = sorted(
            [r["image_id"] for r in reference if r["content_class"] == content],
            key=lambda key: hashlib.sha256(("pdsv1-work-fold:" + key).encode()).digest(),
        )
        assigned.update({key: (i + offset) % count for i, key in enumerate(ordered)})
        offset += len(ordered)
    return np.array([assigned[r["image_id"]] for r in reference])


def classify(reference, generated, target, scheme, kind):
    count = 6 if scheme == "brief" else 8
    if len(reference) < count or len(generated) < count:
        return dict(status="unavailable")
    try:
        wr, wg = weights(reference, target), weights(generated, target)
    except ValueError:
        return dict(status="unavailable")
    real_folds = reference_folds(reference, count)
    generated_folds = np.array(
        [r["brief_index"] % 6 if scheme == "brief" else r["window"] for r in generated]
    )
    folds = np.r_[real_folds, generated_folds]
    items = reference + generated
    labels = np.r_[np.zeros(len(reference), dtype=int), np.ones(len(generated), dtype=int)]
    gram = kernel(values(items), values(items), kind)
    scores = np.full(len(items), np.nan)
    memberships = []
    for fold in range(count):
        train, test = np.flatnonzero(folds != fold), np.flatnonzero(folds == fold)
        if set(labels[test]) != {0, 1}:
            return dict(status="unavailable", reason="empty held-out domain")
        rtrain = [items[i] for i in train if labels[i] == 0]
        gtrain = [items[i] for i in train if labels[i] == 1]
        try:
            w = 0.5 * np.r_[weights(rtrain, target), weights(gtrain, target)]
        except ValueError:
            return dict(status="unavailable", reason="training content support absent")
        square = np.sqrt(w)
        system = gram[np.ix_(train, train)] * np.outer(square, square)
        system.flat[:: len(system) + 1] += RIDGE
        coefficient = square * solve(system, square * (2 * labels[train] - 1), assume_a="pos")
        scores[test] = gram[np.ix_(test, train)] @ coefficient
        memberships.append(
            dict(
                fold=fold,
                train_image_ids=[items[i]["image_id"] for i in train],
                test_image_ids=[items[i]["image_id"] for i in test],
            )
        )
    if not np.isfinite(scores).all():
        raise ValueError("held-out predictions are incomplete")
    return dict(
        status="available",
        **weighted_metrics(scores[: len(reference)], scores[len(reference) :], wr, wg),
        memberships=memberships,
        predictions=[
            dict(
                image_id=r["image_id"],
                domain="original" if i < len(reference) else "generated",
                fold=int(folds[i]),
                score=float(scores[i]),
            )
            for i, r in enumerate(items)
        ],
    )


def projections(reference, generated, target):
    groups = [(route, c) for route in s.ROUTES for c in s.conditions(route)]
    try:
        wr = weights(reference, target)
        chunks, chunks_w = [reference], [0.5 * wr]
        for route, condition in groups:
            selected = [r for r in generated if r["route"] == route and r["condition"] == condition]
            chunks.append(selected)
            chunks_w.append(0.5 / len(groups) * weights(selected, target))
        items = [r for chunk in chunks for r in chunk]
        x, w = values(items), np.concatenate(chunks_w)
        fits = dict(balanced_joint=pca_fit(x, w), original_only=pca_fit(values(reference), wr))
    except ValueError:
        return dict(status="unavailable", reason="incomplete projection content support")
    result = {}
    for name, fit in fits.items():
        coordinates = project(x, fit)
        result[name] = dict(
            fit=fit,
            points=[
                dict(
                    image_id=r["image_id"],
                    route=r.get("route", "original"),
                    condition=r.get("condition", "original"),
                    content_class=r["content_class"],
                    pc1=float(xy[0]),
                    pc2=float(xy[1]),
                )
                for r, xy in zip(items, coordinates)
            ],
        )
    return dict(status="available", bases=result)


def compute(
    reference_rows,
    generated_rows,
    scalers,
    targets,
    config,
    *,
    baseline_draws=999,
    coverage_draws=100,
):
    output = dict(
        cells=[],
        endpoints=[],
        sensitivity_contrasts=[],
        baselines=[],
        coverage=[],
        classifiers=[],
        projections={},
        specificity=[],
        availability=[],
    )
    for pipeline in s.PIPELINES:
        if scalers[pipeline]["status"] != "available":
            output["availability"].append(dict(pipeline=pipeline, status="unavailable_scaler"))
            continue
        scaler = scalers[pipeline]["scaler"]
        real = [
            dict(r, scaled=transform(np.array(r["values"]), scaler).tolist())
            for r in reference_rows
            if r["pipeline"] == pipeline and r["status"] == "measured"
        ]
        fake = [
            dict(r, scaled=transform(np.array(r["values"]), scaler).tolist())
            for r in generated_rows
            if r["pipeline"] == pipeline and r["status"] == "measured"
        ]
        for painter in s.PAINTERS:
            reference = [r for r in real if r["painter_id"] == painter]
            generated = [r for r in fake if r["painter_id"] == painter]
            for route in s.ROUTES:
                for condition in s.conditions(route):
                    selected = [
                        r for r in generated if r["route"] == route and r["condition"] == condition
                    ]
                    label = dict(
                        pipeline=pipeline, painter_id=painter, route=route, condition=condition
                    )
                    output["availability"].append(
                        dict(
                            label,
                            measured_originals=len(reference),
                            measured_generated=len(selected),
                            expected_slots=72,
                        )
                    )
                    output["cells"].extend(
                        cell_summaries(reference, selected, targets[painter], label)
                    )
                    if pipeline != "primary512":
                        continue
                    key = tuple(label.values())
                    output["baselines"].append(
                        dict(
                            label,
                            **baseline(
                                reference,
                                selected,
                                targets[painter],
                                rng_for(str(config["analysis_seed"]), "baseline", *key),
                                draws=baseline_draws,
                            ),
                        )
                    )
                    output["coverage"].append(
                        dict(
                            label,
                            **coverage(
                                reference,
                                selected,
                                targets[painter],
                                rng_for(str(config["analysis_seed"]), "coverage", *key),
                                draws=coverage_draws,
                            ),
                        )
                    )
                    for scheme in ("brief", "window"):
                        for kind in ("linear", "rbf"):
                            output["classifiers"].append(
                                dict(
                                    label,
                                    scheme=scheme,
                                    kernel=kind,
                                    **classify(reference, selected, targets[painter], scheme, kind),
                                )
                            )
                    if condition == "named":
                        for target_painter in s.PAINTERS:
                            target_real = [r for r in real if r["painter_id"] == target_painter]
                            try:
                                wx = weights(target_real, dict.fromkeys(s.CLASSES, 1 / 3))
                                wy = weights(selected, dict.fromkeys(s.CLASSES, 1 / 3))
                                value = energy(values(target_real), values(selected), wx, wy)
                                row = dict(status="available", energy_distance=value)
                            except ValueError:
                                row = dict(status="unavailable")
                            output["specificity"].append(
                                dict(label, target_painter=target_painter, **row)
                            )
            if pipeline == "primary512":
                output["projections"][painter] = projections(reference, generated, targets[painter])
        if pipeline == "primary512":
            output["endpoints"], output["sensitivity_contrasts"] = prompt_endpoints(
                real, fake, targets, config
            )
    return output


def analyze(root):
    s.verify(root)
    directory = root / s.DIRECTORY
    receipts = [
        directory / (stage + "_measurement_receipt.json")
        for stage in ("development", "reference", "generated")
    ]
    for path in receipts:
        verify_bindings(root, read_json(path)["outputs"])
    real, fake = (
        events(directory / (stage + "_features.jsonl")) for stage in ("reference", "generated")
    )
    freeze = read_json(directory / "main_freeze.json")
    result = compute(
        real,
        fake,
        read_json(directory / "scalers.json"),
        freeze["content_weights"],
        read_json(root / s.CONFIG),
    )
    result["generation_accounting"] = read_json(directory / "generation_receipt.json")
    slots = events(directory / "slot_events.jsonl")
    result["actual_slot_times"] = [
        dict(request_id=r["request_id"], window=r["window"], completed_at_utc=r["at_utc"])
        for r in slots
    ]
    result["claim_scope"] = (
        "finite recorded reference panel; feature-distribution results, "
        "no aesthetic or oeuvre-equivalence conclusion"
    )
    return result


def build(root):
    result = analyze(root)
    directory = root / s.DIRECTORY
    paths = [
        s.DIRECTORY / n
        for n in (
            "main_freeze.json",
            "scalers.json",
            "reference_features.jsonl",
            "generated_features.jsonl",
            "generation_receipt.json",
            "slot_events.jsonl",
        )
    ]
    publish(directory / "analysis.json", result)
    publish(
        directory / "analysis_receipt.json",
        dict(
            inputs=bindings(root, paths),
            analysis_sha256=hash_file(directory / "analysis.json"),
            method_source_commit=read_json(directory / "main_freeze.json")["recorded_git_commit"],
        ),
    )
    return dict(
        cells=len(result["cells"]),
        inferential_endpoints=len(result["endpoints"]),
        output=(s.DIRECTORY / "analysis.json").as_posix(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "build":
        result = build(root)
    else:
        directory = root / s.DIRECTORY
        receipt = read_json(directory / "analysis_receipt.json")
        verify_bindings(root, receipt["inputs"])
        if hash_file(directory / "analysis.json") != receipt["analysis_sha256"]:
            raise ValueError("published analysis hash differs")
        if analyze(root) != read_json(directory / "analysis.json"):
            raise ValueError("deterministic numeric analysis replay differs")
        result = dict(status="verified", numeric_replay=True)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
