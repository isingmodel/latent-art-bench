"""Separate the original map's origin from scaling around the evaluation-free mean.

This pure numerical successor reuses all predecessor fitted maps and memberships.
Only the evaluation-free weighted mean enters the additional map. Complete v1
recomputation must agree exactly before a result is returned. There is no file
I/O, image access, scalar tuning, new metric view, testing or interval estimation.
"""

from __future__ import annotations

import copy
import json

import numpy as np

from latent_art_bench.painter_naming_geometry_v1 import analysis as predecessor_analysis
from latent_art_bench.painter_naming_geometry_v1.geometry import apply, energy_terms, occupancy

NEW_KIND = "centered_scale"
KINDS = ("identity", "translation", "translation_scale", NEW_KIND, "named")


def _weights(values, count):
    weights = np.asarray(values, dtype=float)
    if (weights.shape != (count,) or not np.isfinite(weights).all()
            or np.any(weights <= 0)
            or not np.isclose(weights.sum(), 1.0, atol=1e-12, rtol=1e-12)):
        raise ValueError("positive normalized evaluation weights required")
    return weights


def apply_centered(free, weights, fitted):
    """Return (T2c vectors, JSON-native algebra/mean record), without fitting.

    T2c(y) = mean_eval_free + delta_train
             + scale_train * (y - mean_eval_free).
    Evaluation-free centering uses the same probability weights as energy. Its
    mean equals T1's mean; its centered distances equal the original T2's. It is
    a cohort-dependent diagnostic, not a pointwise map transferred unchanged.
    """
    free = apply(free, fitted, "identity")  # Validate vectors and the fixed map.
    weights = _weights(weights, len(free))
    training_free = np.asarray(fitted["free_mean"], dtype=float)
    delta = np.asarray(fitted["named_mean"], dtype=float) - training_free
    scale = fitted["scale"]
    with np.errstate(over="ignore", invalid="ignore"):
        mean = weights @ free
        centered = mean + delta + scale * (free - mean)
        mean_translation = weights @ apply(free, fitted, "translation")
        mean_old_scale = weights @ apply(free, fitted, "translation_scale")
        mean_centered = weights @ centered
        old_minus_translation = (scale - 1) * (mean - training_free)
    if not np.isfinite(centered).all() or not np.isfinite(mean_centered).all():
        raise ValueError("centering produced nonfinite vectors or means")
    if (not np.allclose(mean_centered, mean_translation, atol=1e-10, rtol=1e-10)
            or not np.allclose(mean_old_scale - mean_translation, old_minus_translation,
                               atol=1e-10, rtol=1e-10)):
        raise ValueError("evaluation mean identity failed")
    return centered, dict(
        evaluation_free_mean=mean.tolist(), training_displacement=delta.tolist(),
        fixed_training_scale=float(scale), translation_mean=mean_translation.tolist(),
        old_scale_mean=mean_old_scale.tolist(), centered_scale_mean=mean_centered.tolist(),
        centered_minus_translation_mean=(mean_centered - mean_translation).tolist(),
        old_scale_minus_translation_mean=(mean_old_scale - mean_translation).tolist(),
        theoretical_old_scale_minus_translation_mean=old_minus_translation.tolist(),
        centered_minus_old_scale_mean=(mean_centered - mean_old_scale).tolist(),
    )


def evaluate(reference, free, named, scene_weights, fitted, old):
    """Evaluate T2c on one intact predecessor fold or later cohort.

    The predecessor's evaluation record supplies unchanged T0/T1/T2/named
    comparisons. The complete caller verifies it against v1 before returning.
    """
    scene_weights = _weights(scene_weights, len(free))
    f, w = predecessor_analysis.flatten(free, scene_weights)
    n, _ = predecessor_analysis.flatten(named, scene_weights)
    if f.shape != n.shape:
        raise ValueError("evaluation arms must have paired shapes")
    centered, mean_record = apply_centered(f, w, fitted)
    reference = np.asarray(reference, dtype=float)
    rw = np.full(len(reference), 1 / len(reference))
    energies = copy.deepcopy(old["energies"])
    energies[NEW_KIND] = energy_terms(reference, centered, rw, w)
    balls = copy.deepcopy(old["occupancy"])
    balls[NEW_KIND] = occupancy(reference, centered)
    if any(v["n_queries"] != len(f) for v in balls.values()):
        raise ValueError("predecessor query counts changed")
    if any(v["radii"] != balls[NEW_KIND]["radii"] for v in balls.values()):
        raise ValueError("predecessor reference anchors or radii changed")
    old_within = energies["translation_scale"]["generated_within"]
    if not np.isclose(old_within, energies[NEW_KIND]["generated_within"],
                      atol=1e-10, rtol=1e-10):
        raise ValueError("centering changed the old map's centered distances")
    out = dict(
        centering=mean_record, energies=energies, occupancy=balls,
        residuals={k: energies["named"]["energy"] - energies[k]["energy"]
                   for k in KINDS if k != "named"},
        centering_contrasts={
            "centered_minus_translation": energies[NEW_KIND]["energy"]
            - energies["translation"]["energy"],
            "old_scale_minus_centered": energies["translation_scale"]["energy"]
            - energies[NEW_KIND]["energy"],
            "old_scale_minus_translation": energies["translation_scale"]["energy"]
            - energies["translation"]["energy"],
        },
    )
    if np.shape(free)[1] >= 2:
        out["conditional_residual"] = copy.deepcopy(old["conditional_residual"])
    return out


def _summary(rows):
    return dict(
        energy_mean={k: float(np.mean([r["energies"][k]["energy"] for r in rows]))
                     for k in KINDS},
        residual_mean={k: float(np.mean([r["residuals"][k] for r in rows]))
                       for k in KINDS if k != "named"},
        occupancy_mean={k: float(np.mean([r["occupancy"][k]["coverage"] for r in rows]))
                        for k in KINDS},
        centering_contrast_mean={k: float(np.mean([r["centering_contrasts"][k] for r in rows]))
                                for k in rows[0]["centering_contrasts"]},
        conditional_residual_mean={k: float(np.mean([
            r["conditional_residual"][k]["cross_repeat_mean_square"] for r in rows]))
            for k in ("identity", "translation", "translation_scale")},
    )


def compute(inputs, predecessor):
    """Evaluate all 60 original cells and 18 transfer cells; then verify v1 exactly.

    Both arguments are the existing compact JSON objects, supplied by a separate
    commit-bound runner. Nothing is published here. All new evaluation means are
    fitted only to each fixed evaluation-free cloud, never to named or reference
    outcomes. Training maps, views, source scaler and fold memberships remain v1.
    """
    if (inputs.get("schema") != "painter-naming-geometry-inputs/1"
            or predecessor.get("schema") != "painter-naming-geometry-analysis/1"
            or len(predecessor.get("original", [])) != 60
            or len(predecessor.get("transfer", [])) != 18):
        raise ValueError("complete predecessor input/result schemas required")
    original, transfer = [], []
    for old in predecessor["original"]:
        pipeline, view, route, painter = (old[k] for k in ("pipeline", "view", "route", "painter"))
        coordinates = predecessor_analysis.VIEWS[view]
        cell = inputs["original"][pipeline][route][painter]
        free = np.asarray(cell["free"])[..., coordinates]
        named = np.asarray(cell["named"])[..., coordinates]
        reference = np.asarray(inputs["reference"][pipeline][painter]["values"])[:, coordinates]
        rows = []
        for fold in old["folds"]:
            selected = [cell["scene_ids"].index(s) for s in fold["test_scenes"]]
            value = evaluate(reference, free[selected], named[selected],
                             fold["test_scene_weights"], fold["fitted"], fold)
            value.update(fold=fold["fold"], train_scenes=fold["train_scenes"],
                         test_scenes=fold["test_scenes"],
                         test_scene_weights=fold["test_scene_weights"], fitted=fold["fitted"])
            rows.append(value)
        if len(rows) != 4:
            raise ValueError("exactly four predecessor folds required")
        value = dict(pipeline=pipeline, view=view, route=route, painter=painter,
                     folds=rows, **_summary(rows))
        original.append(value)
    for old in predecessor["transfer"]:
        pipeline, view, painter = (old[k] for k in ("pipeline", "view", "painter"))
        coordinates = predecessor_analysis.VIEWS[view]
        cell = inputs["later"][pipeline][painter]
        free = np.asarray(cell["free"])[..., coordinates]
        named = np.asarray(cell["named"])[..., coordinates]
        reference = np.asarray(inputs["reference"][pipeline][painter]["values"])[:, coordinates]
        value = evaluate(reference, free, named, old["scene_weights"], old["fitted"], old)
        value.update(pipeline=pipeline, view=view, painter=painter, fitted=old["fitted"],
                     scene_ids=old["scene_ids"], scene_weights=old["scene_weights"])
        transfer.append(value)
    # This complete exact bridge also protects against stale fitted maps, changed
    # memberships, altered old metrics and favorable omission/duplication of cells.
    recomputed = json.loads(json.dumps(predecessor_analysis.compute(inputs), allow_nan=False))
    if recomputed != predecessor:
        raise ValueError("complete predecessor numerical bridge differs")
    result = dict(
        schema="painter-naming-centering-analysis/1", original=original, transfer=transfer,
        predecessor_bridge=dict(exact=True, original_cells=60, transfer_cells=18),
        scope="Post-v1-result fixed-grid centering diagnostic; no new tests or intervals",
        original_images=864, later_images=72, new_images=0,
    )
    return json.loads(json.dumps(result, allow_nan=False))
