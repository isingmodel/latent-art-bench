"""Pure, descriptive location/scale geometry on retained feature vectors.

Fitting uses only the two generated training sets. References never enter the
map, and transformed vectors need not correspond to attainable images. The
caller owns scene folds, query allocation and aggregation; this module neither
pools separately fitted clouds nor calculates tests or confidence intervals.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist

KINDS = ("identity", "translation", "translation_scale")


def _matrix(values):
    array = np.asarray(values, dtype=float)
    if (array.ndim != 2 or min(array.shape) < 1 or not np.isfinite(array).all()):
        raise ValueError("expected a finite nonempty N by D matrix")
    return array


def _weights(values, size):
    weights = np.asarray(values, dtype=float)
    if (weights.shape != (size,) or not np.isfinite(weights).all()
            or np.any(weights <= 0)
            or not np.isclose(weights.sum(), 1.0, atol=1e-12, rtol=1e-12)):
        raise ValueError("expected positive normalized weights matching the rows")
    return weights


def _moments(values, weights):
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        mean = weights @ values
        trace = float(weights @ np.square(values - mean).sum(axis=1))
    if not np.isfinite(mean).all() or not np.isfinite(trace) or trace <= 0:
        raise ValueError("fitting requires finite means and positive finite traces")
    return mean, trace


def fit_map(free, named, weights):
    """Return generated-only weighted moments and the positive trace-matching scale.

    Both input arrays contain the same training row allocation and use the same
    strictly positive probability weights. No pointwise least-squares fit or
    optimization against reference paintings is performed. The returned record
    contains ordinary Python scalars/lists and can be serialized as JSON.
    """
    free, named = _matrix(free), _matrix(named)
    if free.shape != named.shape:
        raise ValueError("free and named training matrices must have matching shape")
    weights = _weights(weights, len(free))
    free_mean, free_trace = _moments(free, weights)
    named_mean, named_trace = _moments(named, weights)
    with np.errstate(over="ignore", invalid="ignore", under="ignore"):
        scale = float(np.sqrt(named_trace) / np.sqrt(free_trace))
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("fitting requires a positive finite scale")
    return dict(free_mean=free_mean.tolist(), named_mean=named_mean.tolist(),
                free_trace=free_trace, named_trace=named_trace, scale=scale)


def apply(values, fitted, kind="translation_scale"):
    """Apply one fixed map to an evaluation set without refitting any moment."""
    values = _matrix(values)
    if kind not in KINDS:
        raise ValueError("unknown location/scale map kind")
    try:
        free_mean = np.asarray(fitted["free_mean"], dtype=float)
        named_mean = np.asarray(fitted["named_mean"], dtype=float)
        scale = float(fitted["scale"])
        traces = np.asarray([fitted["free_trace"], fitted["named_trace"]], dtype=float)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid fitted map record") from exc
    if (free_mean.shape != (values.shape[1],) or named_mean.shape != free_mean.shape
            or not np.isfinite(free_mean).all() or not np.isfinite(named_mean).all()
            or not np.isfinite(scale) or scale <= 0
            or traces.shape != (2,) or not np.isfinite(traces).all() or np.any(traces <= 0)):
        raise ValueError("fitted map must have matching finite means and positive scale/traces")
    with np.errstate(over="ignore", invalid="ignore"):
        if kind == "identity":
            result = values.copy()
        elif kind == "translation":
            result = values + (named_mean - free_mean)
        else:
            result = named_mean + scale * (values - free_mean)
    if not np.isfinite(result).all():
        raise ValueError("map produced nonfinite evaluation vectors")
    return result


def _distances(first, second):
    if first.shape[1] != second.shape[1]:
        raise ValueError("distance matrices must have matching feature dimensions")
    with np.errstate(over="ignore", invalid="ignore"):
        distances = cdist(first, second)
    if not np.isfinite(distances).all():
        raise ValueError("nonfinite pairwise distances")
    return distances


def energy_terms(reference, generated, reference_weights, generated_weights):
    """Weighted empirical V-energy with explicit cross and both self terms.

    All diagonal self-distances remain in the weighted sums. No U-statistic
    correction, nonnegative clipping or distribution-equality inference is used.
    """
    reference, generated = _matrix(reference), _matrix(generated)
    reference_weights = _weights(reference_weights, len(reference))
    generated_weights = _weights(generated_weights, len(generated))
    cross = _distances(reference, generated)
    reference_self = _distances(reference, reference)
    generated_self = _distances(generated, generated)
    with np.errstate(over="ignore", invalid="ignore"):
        cross_twice = float(2 * (reference_weights @ cross @ generated_weights))
        reference_within = float(reference_weights @ reference_self @ reference_weights)
        generated_within = float(generated_weights @ generated_self @ generated_weights)
        energy = cross_twice - reference_within - generated_within
    result = dict(energy=energy, cross_twice=cross_twice,
                  reference_within=reference_within, generated_within=generated_within)
    if not np.isfinite(list(result.values())).all():
        raise ValueError("nonfinite weighted energy terms")
    return result


def occupancy(reference, queries, k=3):
    """Fraction of fixed reference balls containing any query, without resampling.

    Each radius is the kth nearest *other* anchor distance; boundary hits count.
    Anchors have equal occupancy weight. The caller must keep query identities,
    counts and class allocation comparable across map kinds. This is not the old
    disjoint-anchor/matched-real comparison and supplies no real-query baseline.
    """
    reference, queries = _matrix(reference), _matrix(queries)
    if (isinstance(k, (bool, np.bool_)) or not isinstance(k, (int, np.integer))
            or k < 1 or k >= len(reference)):
        raise ValueError("k must be an integer between one and the number of anchors minus one")
    distance = _distances(reference, reference)
    np.fill_diagonal(distance, np.inf)
    radii = np.partition(distance, int(k) - 1, axis=1)[:, int(k) - 1]
    inside = _distances(reference, queries) <= radii[:, None]
    hit = inside.any(axis=1)
    return dict(coverage=float(hit.mean()), radii=radii.tolist(), hit=hit.tolist(),
                hit_count=inside.sum(axis=1).tolist(), n_reference=len(reference),
                n_queries=len(queries), k=int(k))
