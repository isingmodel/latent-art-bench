"""Read existing numeric evidence, retaining original work and retry provenance."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench import painter_prompt_retry_v1 as retry
from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.painter_feature_distance_v1.analysis import load_source
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, verify_bindings
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.generation import ALIASES
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS, TEMPLATE_IDS

from .statistics import KERNELS, heldout_scores, metrics, pca_fit, project, spread, work_folds

NAMESPACE = "painter_distribution_exploration_v1"
FEATURE_SETS = {"all31": slice(0, 31), **features.FAMILIES}
METHOD = "pfg2-method-20260905"


def load(root):
    freeze, original_dir = retry.load(root)
    receipt = read_json(root / retry.DIRECTORY / "measurement_receipt.json")
    verify_bindings(root, receipt["inputs"])
    original = read_jsonl(original_dir / "measured_features.jsonl")
    replacements = read_jsonl(root / retry.DIRECTORY / "measured_features.jsonl")
    combined = retry.combine(original, replacements)
    real, _, _, scaler, _, provenance = load_source(root, METHOD)
    reference_path = Path("data/manifests/painter_feature_generation_v2") / METHOD
    reference_path /= "confirmation_features.jsonl"
    reference = [r for r in read_jsonl(root / reference_path) if r["status"] == "measured"]
    if (
        freeze["source_method_id"] != METHOD
        or len(reference) != 649
        or len({r["image_id"] for r in reference}) != 649
        or len(combined) != 1920
        or any(r["status"] != "measured" for r in combined)
    ):
        raise ValueError("requires the complete existing reference and retry-derived grid")
    expected = {
        (a, m, p): 64 for a in ALIASES for m in METHOD_IDS for p in (*PAINTER_IDS, "artist_free")
    }
    if Counter((r["alias"], r["method_id"], r["condition"]) for r in combined) != expected:
        raise ValueError("unexpected generated cell inventory")
    painters = {}
    for painter in PAINTER_IDS:
        originals = [r for r in reference if r["painter_id"] == painter]
        if not np.array_equal(
            real[painter], transform(np.array([r["values"] for r in originals]), scaler)
        ):
            raise ValueError("reference identity order differs from validated numeric source")
        items = [
            dict(
                image_id=r["image_id"],
                domain="original",
                alias="original",
                method_id="original",
                template_id="",
                block=-1,
                retried=False,
                source_run_id=METHOD,
            )
            for r in originals
        ]
        arrays = [real[painter]]
        for alias in ALIASES:
            for method in METHOD_IDS:
                selected = sorted(
                    [
                        r
                        for r in combined
                        if (r["alias"], r["method_id"], r["condition"]) == (alias, method, painter)
                    ],
                    key=lambda r: r["request_sequence"],
                )
                if Counter((r["template_id"], r["block"]) for r in selected) != {
                    (t, b): 1 for t in TEMPLATE_IDS for b in range(4)
                }:
                    raise ValueError("expected one output per scene and block")
                arrays.append(transform(np.array([r["values"] for r in selected]), scaler))
                items.extend(
                    dict(
                        image_id=r["image_id"],
                        domain="generated",
                        alias=alias,
                        method_id=method,
                        template_id=r["template_id"],
                        block=r["block"],
                        retried=r.get("retried", False),
                        source_run_id=r["run_id"],
                    )
                    for r in selected
                )
        painters[painter] = dict(
            values=np.concatenate(arrays), items=items, reference_count=len(originals)
        )
    paths = {Path(r["path"]) for r in freeze["inputs"] + provenance["inputs"]}
    paths.update(Path(r["path"]) for r in receipt["inputs"])
    paths.update(
        {
            retry.DIRECTORY / "retry_freeze.json",
            retry.DIRECTORY / "measurement_receipt.json",
            reference_path,
        }
    )
    return painters, bindings(root, paths)


def compute(painters):
    points, projections, summaries, predictions, spreads = [], [], [], [], []
    for painter, data in painters.items():
        values, items, count = data["values"], data["items"], data["reference_count"]
        n_generated = len(items) - count
        if n_generated != 384:
            raise ValueError("expected six 64-image groups")
        real_ids = [r["image_id"] for r in items[:count]]
        real_folds = {
            scheme: work_folds(real_ids, folds) for scheme, folds in (("scene", 16), ("block", 4))
        }
        for family, section in FEATURE_SETS.items():
            x = values[:, section]
            for basis in ("balanced_joint", "original_only"):
                if basis == "original_only" and family != "all31":
                    continue
                weights = np.r_[
                    np.full(count, 0.5 / count), np.full(n_generated, 0.5 / n_generated)
                ]
                fit = (
                    pca_fit(x, weights)
                    if basis == "balanced_joint"
                    else pca_fit(x[:count], np.full(count, 1 / count))
                )
                coordinates = project(x, fit)
                projection_id = f"{painter}/{family}/{basis}"
                projections.append(
                    dict(
                        projection_id=projection_id,
                        painter_id=painter,
                        family=family,
                        basis=basis,
                        feature_names=list(features.NAMES[section]),
                        **fit,
                    )
                )
                points.extend(
                    dict(
                        projection_id=projection_id,
                        painter_id=painter,
                        family=family,
                        basis=basis,
                        **item,
                        pc1=float(xy[0]),
                        pc2=float(xy[1]),
                    )
                    for item, xy in zip(items, coordinates)
                )
            for alias in ALIASES:
                for method in METHOD_IDS:
                    indices = list(range(count)) + [
                        i
                        for i, r in enumerate(items)
                        if (r["alias"], r["method_id"]) == (alias, method)
                    ]
                    chosen = [items[i] for i in indices]
                    spreads.append(
                        dict(
                            painter_id=painter,
                            alias=alias,
                            method_id=method,
                            family=family,
                            reference_count=count,
                            generated_count=64,
                            **spread(x[:count], x[indices[count:]]),
                        )
                    )
                    labels = np.r_[np.zeros(count, dtype=int), np.ones(64, dtype=int)]
                    schemes = ("scene", "block") if family == "all31" else ("scene",)
                    for scheme in schemes:
                        generated_folds = [
                            TEMPLATE_IDS.index(r["template_id"])
                            if scheme == "scene"
                            else r["block"]
                            for r in chosen[count:]
                        ]
                        folds = np.r_[real_folds[scheme], generated_folds]
                        cell = dict(
                            painter_id=painter,
                            alias=alias,
                            method_id=method,
                            family=family,
                            split=scheme,
                        )
                        scores = {}
                        for kind in KERNELS:
                            scores[kind] = heldout_scores(x[indices], labels, folds, kind)
                            summaries.append(
                                dict(
                                    **cell,
                                    classifier=kind,
                                    reference_count=count,
                                    generated_count=64,
                                    folds=len(set(folds)),
                                    **metrics(labels, scores[kind]),
                                )
                            )
                        if family == "all31":
                            predictions.extend(
                                dict(
                                    **cell,
                                    image_id=r["image_id"],
                                    domain=r["domain"],
                                    source_run_id=r["source_run_id"],
                                    template_id=r["template_id"],
                                    block=r["block"],
                                    retried=r["retried"],
                                    fold=int(folds[i]),
                                    label=int(labels[i]),
                                    linear_score=float(scores["linear"][i]),
                                    rbf_score=float(scores["rbf"][i]),
                                )
                                for i, r in enumerate(chosen)
                            )
    return dict(
        projections=projections,
        points=points,
        separability=summaries,
        predictions=predictions,
        spread=spreads,
    )
