"""Descriptive weighted distributions and strict train/test transfer primitives."""

from __future__ import annotations

import hashlib

import numpy as np
from scipy.linalg import solve
from scipy.spatial.distance import cdist

from latent_art_bench.painter_distribution_exploration_v1.statistics import (
    RIDGE,
    kernel,
    matrix,
)
from latent_art_bench.painter_feature_generation_v2.statistics import weighted_quantile


def rng_for(seed, *keys):
    encoded = "\0".join([seed, *map(str, keys)]).encode()
    return np.random.default_rng(int.from_bytes(hashlib.sha256(encoded).digest()[:8], "big"))


def probability_weights(size, weights=None):
    w = np.full(size, 1 / size) if weights is None else np.asarray(weights, dtype=float)
    if (
        w.shape != (size,)
        or not np.isfinite(w).all()
        or np.any(w < 0)
        or not np.isclose(w.sum(), 1)
    ):
        raise ValueError("expected finite probability weights")
    return w


def content_weights(labels, classes):
    labels = np.asarray(labels)
    if len(set(classes)) != len(classes) or not classes:
        raise ValueError("content classes must be nonempty and unique")
    if set(labels) != set(classes):
        raise ValueError("all declared content classes must be represented")
    return np.array([1 / (len(classes) * np.sum(labels == label)) for label in labels])


def distribution_summary(real, generated, real_weights=None, generated_weights=None):
    x, y = matrix(real), matrix(generated)
    if x.shape[1] != y.shape[1] or min(len(x), len(y)) < 2:
        raise ValueError("two observations and matching dimensions required")
    wx, wy = (
        probability_weights(len(x), real_weights),
        probability_weights(len(y), generated_weights),
    )
    energy = 2 * wx @ cdist(x, y) @ wy - wx @ cdist(x, x) @ wx - wy @ cdist(y, y) @ wy
    vx = float(wx @ np.square(x - wx @ x).sum(axis=1))
    vy = float(wy @ np.square(y - wy @ y).sum(axis=1))
    qx = np.array([weighted_quantile(v, wx, [0.25, 0.75]) for v in x.T])
    qy = np.array([weighted_quantile(v, wy, [0.25, 0.75]) for v in y.T])
    ix, iy = qx[:, 1] - qx[:, 0], qy[:, 1] - qy[:, 0]
    sx, sy = float(ix @ ix), float(iy @ iy)
    sample_ratio = None
    if real_weights is None and generated_weights is None and vx > 0:
        sample_ratio = (vy * len(y) / (len(y) - 1)) / (vx * len(x) / (len(x) - 1))
    return dict(
        energy_distance=float(energy),
        population_variance_ratio=vy / vx if vx > 0 else None,
        sample_variance_ratio=sample_ratio,
        squared_iqr_sum_ratio=sy / sx if sx > 0 else None,
        coordinate_iqr_ratios=[float(b / a) if a > 0 else None for a, b in zip(ix, iy)],
        original_weight_effective_size=float(1 / (wx @ wx)),
        generated_weight_effective_size=float(1 / (wy @ wy)),
    )


def disjoint_splits(size, group_size, draws, rng):
    if group_size < 2 or 2 * group_size > size or draws < 1:
        raise ValueError("cannot draw two disjoint groups of the requested size")
    result = []
    for _ in range(draws):
        chosen = rng.permutation(size)[: 2 * group_size]
        result.append((chosen[:group_size], chosen[group_size:]))
    return result


def transfer_scores(train, labels, test, kind):
    train, test = matrix(train), matrix(test)
    labels = np.asarray(labels)
    if labels.shape != (len(train),) or set(labels) != {0, 1}:
        raise ValueError("training must contain two classes")
    weights = np.array([1 / (2 * np.sum(labels == label)) for label in labels])
    square_root = np.sqrt(weights)
    gram = kernel(train, train, kind) * np.outer(square_root, square_root)
    gram.flat[:: len(gram) + 1] += RIDGE
    coefficients = square_root * solve(gram, square_root * (2 * labels - 1), assume_a="pos")
    return kernel(test, train, kind) @ coefficients


def transfer_fold(source_items, target_items, source_work_folds, target_work_folds, fold):
    """Membership uses identity/scene metadata only, never feature values or labels."""

    def group(item, work_folds):
        if item["domain"] == "original":
            return work_folds[item["image_id"]]
        return item["scene_fold"]

    train = [i for i, item in enumerate(source_items) if group(item, source_work_folds) != fold]
    test = [i for i, item in enumerate(target_items) if group(item, target_work_folds) == fold]
    train_ids = {source_items[i]["image_id"] for i in train}
    if train_ids & {target_items[i]["image_id"] for i in test}:
        raise ValueError("physical image identity leaks across transfer split")
    train_scenes = {
        source_items[i]["template_id"] for i in train if source_items[i]["domain"] == "generated"
    }
    test_scenes = {
        target_items[i]["template_id"] for i in test if target_items[i]["domain"] == "generated"
    }
    if train_scenes & test_scenes:
        raise ValueError("scene family leaks across transfer split")
    return train, test
