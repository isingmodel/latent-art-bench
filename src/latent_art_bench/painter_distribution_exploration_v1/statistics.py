"""Fixed PCA views and descriptive, grouped out-of-fold separability diagnostics."""

from __future__ import annotations

import hashlib

import numpy as np
from scipy.linalg import solve
from scipy.spatial.distance import cdist
from scipy.stats import rankdata

RIDGE = 0.01
KERNELS = ("linear", "rbf")


def matrix(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("expected a nonempty finite matrix")
    return values


def pca_fit(values, weights):
    """Weighted covariance PCA; deterministic sign, no whitening or label optimization."""
    values = matrix(values)
    weights = np.asarray(weights, dtype=float)
    if (
        weights.shape != (len(values),)
        or np.any(weights < 0)
        or not np.isfinite(weights).all()
        or not np.isclose(weights.sum(), 1)
    ):
        raise ValueError("expected probability weights")
    center = weights @ values
    centered = values - center
    covariance = centered.T @ (weights[:, None] * centered)
    eigenvalues, vectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues, vectors = np.maximum(eigenvalues[order], 0), vectors[:, order]
    if len(eigenvalues) < 2 or eigenvalues.sum() <= 0:
        raise ValueError("PCA requires two coordinates and positive variance")
    for j in range(vectors.shape[1]):
        if vectors[np.argmax(abs(vectors[:, j])), j] < 0:
            vectors[:, j] *= -1
    return dict(
        center=center.tolist(),
        components=vectors[:, :2].T.tolist(),
        explained_variance_ratio=(eigenvalues[:2] / eigenvalues.sum()).tolist(),
    )


def project(values, fit):
    return (matrix(values) - np.array(fit["center"])) @ np.array(fit["components"]).T


def spread(reference, generated):
    """Sum of coordinate sample variances, centered separately within each group."""
    reference, generated = matrix(reference), matrix(generated)
    if min(len(reference), len(generated)) < 2 or reference.shape[1] != generated.shape[1]:
        raise ValueError("spread requires matching dimensions and two images per group")
    real = float(reference.var(axis=0, ddof=1).sum())
    fake = float(generated.var(axis=0, ddof=1).sum())
    if real <= 0:
        raise ValueError("reference has zero spread")
    return dict(
        original_total_variance=real,
        generated_total_variance=fake,
        generated_to_original_variance_ratio=fake / real,
    )


def work_folds(ids, count):
    """Stable balanced work folds, independent of feature values and input row ordering."""
    if len(set(ids)) != len(ids) or len(ids) < count or count < 2:
        raise ValueError("unique work IDs and at least one work per fold required")
    ordered = sorted(
        ids, key=lambda s: hashlib.sha256(("painter-distribution-v1:" + s).encode()).hexdigest()
    )
    lookup = {key: i % count for i, key in enumerate(ordered)}
    return np.array([lookup[key] for key in ids])


def kernel(left, right, kind):
    left, right = matrix(left), matrix(right)
    if left.shape[1] != right.shape[1]:
        raise ValueError("different feature dimensions")
    dimension = left.shape[1]
    if kind == "linear":
        return left @ right.T / dimension + 1
    if kind == "rbf":
        return np.exp(-cdist(left, right, "sqeuclidean") / dimension) + 1
    raise ValueError("unknown kernel")


def heldout_scores(values, labels, folds, kind):
    """Class-balanced kernel ridge, trained strictly outside each test fold.

    Minimize sum_i w_i (f(x_i)-y_i)^2 + 0.01 ||f||_H^2, y in {-1,+1},
    w_i=1/(2*n_class) within training. Positive score means generated.
    The constant kernel is a regularized intercept. No outcome-driven tuning.
    """
    values = matrix(values)
    labels, folds = np.asarray(labels), np.asarray(folds)
    if (
        labels.shape != (len(values),)
        or folds.shape != labels.shape
        or set(labels) != {0, 1}
        or len(set(folds)) < 2
    ):
        raise ValueError("expected two classes and multiple folds")
    gram = kernel(values, values, kind)  # Fixed pairwise function; no fitted preprocessing.
    scores = np.empty(len(values))
    for fold in sorted(set(folds)):
        test = folds == fold
        train = ~test
        if set(labels[train]) != {0, 1} or set(labels[test]) != {0, 1}:
            raise ValueError("every train and test fold must contain both classes")
        y = labels[train]
        weights = np.array([1 / (2 * np.sum(y == label)) for label in y])
        square_root = np.sqrt(weights)
        system = gram[np.ix_(train, train)] * np.outer(square_root, square_root)
        system.flat[:: len(system) + 1] += RIDGE
        coefficient = square_root * solve(system, square_root * (2 * y - 1), assume_a="pos")
        scores[test] = gram[np.ix_(test, train)] @ coefficient
    return scores


def metrics(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    if labels.shape != scores.shape or set(labels) != {0, 1} or not np.isfinite(scores).all():
        raise ValueError("expected finite two-class scores")
    prediction = scores >= 0
    real_specificity = np.mean(~prediction[labels == 0])
    generated_recall = np.mean(prediction[labels == 1])
    n1, n0 = np.sum(labels == 1), np.sum(labels == 0)
    auc = (rankdata(scores)[labels == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    return dict(
        balanced_accuracy=float((real_specificity + generated_recall) / 2),
        auc=float(auc),
        real_specificity=float(real_specificity),
        generated_recall=float(generated_recall),
    )
