"""Whole-scene cross-fitting and fixed-map temporal transfer; descriptive only."""

import numpy as np

from .geometry import KINDS, apply, energy_terms, fit_map, occupancy
from .inputs import PAINTERS, ROUTES
from .variance import corrected_variance, cross_repeat_residual

VIEWS = {"all31": list(range(31)), "no_lbp8": [i for i in range(31) if i != 25],
         "nontexture19": list(range(19))}


def weights(classes, targets):
    classes = np.asarray(classes)
    if set(classes) != set(targets):
        raise ValueError("all three fixed classes must remain represented")
    return np.asarray([targets[c] / np.sum(classes == c) for c in classes])


def folds(scene_ids, classes):
    if len(scene_ids) != len(set(scene_ids)) or len(scene_ids) != len(classes):
        raise ValueError("scene identities must be unique and aligned")
    assigned = np.full(len(scene_ids), -1, dtype=int)
    for content in sorted(set(classes)):
        ordered = sorted((s, i) for i, (s, c) in enumerate(zip(scene_ids, classes)) if c == content)
        if len(ordered) != 8:
            raise ValueError("four fixed folds require eight scenes per class")
        for position, (_, index) in enumerate(ordered):
            assigned[index] = position % 4
    return assigned


def flatten(values, scene_weights):
    values = np.asarray(values, dtype=float)
    if values.ndim != 3 or len(values) != len(scene_weights):
        raise ValueError("expected scene by repeat by feature values")
    return values.reshape(-1, values.shape[-1]), np.repeat(scene_weights / values.shape[1],
                                                         values.shape[1])


def evaluate(reference, free, named, scene_weights, fitted, details=True):
    f, w = flatten(free, scene_weights)
    n, _ = flatten(named, scene_weights)
    if f.shape != n.shape:
        raise ValueError("held-out arms must have paired shapes")
    reference = np.asarray(reference)
    rw = np.full(len(reference), 1 / len(reference))
    clouds = {kind: apply(f, fitted, kind) for kind in KINDS}
    clouds["named"] = n
    out = dict(energies={k: energy_terms(reference, y, rw, w) for k, y in clouds.items()})
    out["residuals"] = {
        k: out["energies"]["named"]["energy"] - out["energies"][k]["energy"]
        for k in KINDS
    }
    if details:
        out["occupancy"] = {k: occupancy(reference, y) for k, y in clouds.items()}
        if np.shape(free)[1] >= 2:
            out["conditional_residual"] = {
                k: cross_repeat_residual((n-y).reshape(np.shape(named)), scene_weights)
                for k, y in clouds.items() if k != "named"
            }
    return out


def crossfit(reference, free, named, classes, targets, scene_ids, delete=None, details=True):
    free, named, classes = np.asarray(free), np.asarray(named), np.asarray(classes)
    if free.shape != named.shape or free.shape[:2] != (24, 3):
        raise ValueError("original cross-fitting requires complete 24 by 3 paired arrays")
    allocation = folds(scene_ids, classes)
    keep = np.ones(len(classes), dtype=bool)
    if delete is not None:
        if delete not in scene_ids:
            raise ValueError("unknown deleted scene")
        keep[scene_ids.index(delete)] = False
    rows = []
    for fold in range(4):
        train, test = (allocation != fold) & keep, (allocation == fold) & keep
        wtrain, wtest = weights(classes[train], targets), weights(classes[test], targets)
        ft, wt = flatten(free[train], wtrain)
        nt, _ = flatten(named[train], wtrain)
        fitted = fit_map(ft, nt, wt)
        value = evaluate(reference, free[test], named[test], wtest, fitted, details=details)
        if details:
            value.update(fold=fold, train_scenes=np.asarray(scene_ids)[train].tolist(),
                         test_scenes=np.asarray(scene_ids)[test].tolist(), fitted=fitted,
                         test_scene_weights=wtest.tolist())
        rows.append(value)
    result = dict(
        energy_mean={k: float(np.mean([r["energies"][k]["energy"] for r in rows]))
                     for k in (*KINDS, "named")},
        residual_mean={k: float(np.mean([r["residuals"][k] for r in rows])) for k in KINDS},
    )
    if details:
        result.update(
            folds=rows,
            occupancy_mean={k: float(np.mean([r["occupancy"][k]["coverage"] for r in rows]))
                            for k in (*KINDS, "named")},
            conditional_residual_mean={
                k: float(np.mean([r["conditional_residual"][k]["cross_repeat_mean_square"]
                                  for r in rows])) for k in KINDS},
        )
    return result


def variance_pair(free, named, classes, targets):
    out = {}
    for key, w in (("reference_content", weights(classes, targets)),
                   ("equal_scene", np.full(len(classes), 1 / len(classes)))):
        arms = {"free": corrected_variance(free, w), "named": corrected_variance(named, w)}
        ratios = {}
        for field in ("observed_between", "observed_within", "observed_total", "repeat_noise",
                      "corrected_between", "corrected_signal_to_noise"):
            first, second = arms["free"][field], arms["named"][field]
            ratios[field] = None if first in (None, 0) or second is None else second / first
        out[key] = dict(arms=arms, named_free_ratios=ratios)
    return out


def compute(inputs):
    original, transfer = [], []
    for pipeline, routes in inputs["original"].items():
        views = {"all31": VIEWS["all31"]} if pipeline == "common_square" else VIEWS
        for view, coordinates in views.items():
            for route in ROUTES:
                for painter in PAINTERS:
                    cell = routes[route][painter]
                    free = np.asarray(cell["free"])[..., coordinates]
                    named = np.asarray(cell["named"])[..., coordinates]
                    reference = np.asarray(inputs["reference"][pipeline][painter]["values"])
                    reference = reference[:, coordinates]
                    target = inputs["targets"][painter]
                    value = crossfit(reference, free, named, cell["classes"], target,
                                     cell["scene_ids"])
                    value.update(pipeline=pipeline, view=view, route=route, painter=painter,
                                 variance=variance_pair(free, named, cell["classes"], target))
                    if pipeline == "primary512" and view == "all31":
                        value["delete_one_scene"] = [dict(
                            deleted=s, **crossfit(reference, free, named, cell["classes"], target,
                                                 cell["scene_ids"], delete=s, details=False))
                            for s in cell["scene_ids"]]
                    original.append(value)
                    if route != "flux_2_max" or pipeline == "common_square":
                        continue
                    later = inputs["later"][pipeline][painter]
                    wold = weights(cell["classes"], target)
                    fold, w = flatten(free, wold)
                    nold, _ = flatten(named, wold)
                    fitted = fit_map(fold, nold, w)
                    lf = np.asarray(later["free"])[..., coordinates]
                    ln = np.asarray(later["named"])[..., coordinates]
                    lw = weights(later["classes"], target)
                    value = evaluate(reference, lf, ln, lw, fitted)
                    value.update(pipeline=pipeline, view=view, painter=painter, fitted=fitted,
                                 scene_ids=later["scene_ids"], scene_weights=lw.tolist())
                    if pipeline == "primary512" and view == "all31":
                        value["delete_one_scene"] = []
                        for index, scene in enumerate(later["scene_ids"]):
                            keep = np.arange(len(lf)) != index
                            wk = weights(np.asarray(later["classes"])[keep], target)
                            value["delete_one_scene"].append(dict(
                                deleted=scene, **evaluate(reference, lf[keep], ln[keep], wk,
                                                         fitted, details=False)))
                    transfer.append(value)
    if len(original) != 60 or len(transfer) != 18:
        raise ValueError("incomplete predefined sensitivity grid")
    return dict(schema="painter-naming-geometry-analysis/1", original=original, transfer=transfer,
                scope="Post-result fixed-scene diagnostics; no new hypothesis tests or intervals",
                original_images=864, later_images=72, new_images=0)
