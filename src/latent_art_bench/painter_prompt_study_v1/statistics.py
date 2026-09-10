"""Fixed-reference energy kernels and prospective complete-block inference.

Blocks, not images or templates, are the independent sampling units. Adjacent blocks
form prespecified disjoint pairs. Student-t intervals are exact only for normal IID
pair contributions; the jackknife alternative is asymptotic and can fail at degeneracy.
Neither procedure proves stationarity or independence of a remote image service.
"""

from __future__ import annotations

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import t


def energy_kernel(reference: np.ndarray, blocks: np.ndarray) -> np.ndarray:
    """Return H[i,j] with E H(B,B') equal to the finite-reference energy distance.

    ``reference`` is [works, coordinates], with uniform fixed work weights;
    ``blocks`` is [repetitions, templates, coordinates]. Each complete block has
    uniform template weights. Diagonal entries are retained for exact synthetic
    population expectations; observed U estimates exclude equal observed blocks.
    """
    reference, blocks = np.asarray(reference, dtype=float), np.asarray(blocks, dtype=float)
    if (reference.ndim != 2 or blocks.ndim != 3 or not len(reference)
            or blocks.shape[0] < 2 or blocks.shape[1] < 1
            or reference.shape[1] < 1 or reference.shape[1] != blocks.shape[2]
            or not np.isfinite(reference).all() or not np.isfinite(blocks).all()):
        raise ValueError("expected finite reference[N,D] and blocks[R,T,D], R >= 2")
    repetitions, templates, dimension = blocks.shape
    flat = blocks.reshape(-1, dimension)
    cross = cdist(flat, reference).reshape(repetitions, templates, len(reference)).mean((1, 2))
    generated = cdist(flat, flat).reshape(
        repetitions, templates, repetitions, templates).mean((1, 3))
    return cross[:, None] + cross[None, :] - cdist(reference, reference).mean() - generated


def _kernels(kernels: np.ndarray) -> np.ndarray:
    values = np.asarray(kernels, dtype=float)
    if (values.ndim != 3 or values.shape[0] < 1 or values.shape[1] != values.shape[2]
            or values.shape[1] < 2 or not np.isfinite(values).all()
            or not np.allclose(values, values.transpose(0, 2, 1), rtol=1e-12, atol=1e-12)):
        raise ValueError("expected finite symmetric kernels[endpoints,blocks,blocks]")
    return values


def pair_contributions(kernels: np.ndarray) -> np.ndarray:
    """One unbiased observation per adjacent pair; never silently discard a block."""
    values = _kernels(kernels)
    repetitions = values.shape[1]
    if repetitions % 2:
        raise ValueError("disjoint-pair analysis requires an even number of complete blocks")
    return values[:, np.arange(0, repetitions, 2), np.arange(1, repetitions, 2)].T


def jackknife_pseudovalues(kernels: np.ndarray) -> np.ndarray:
    """Delete-one-block pseudovalues for the complete order-two U statistic.

    Their mean equals the complete U estimate. They are dependent, so feeding them
    to t intervals supplies a jackknife approximation, not ordinary IID t inference.
    """
    values = _kernels(kernels)
    repetitions = values.shape[1]
    if repetitions < 3:
        raise ValueError("jackknife requires at least three complete blocks")
    rows = values.sum(axis=2) - np.diagonal(values, axis1=1, axis2=2)
    total = rows.sum(axis=1)
    return ((2 * (repetitions - 1) * rows - total[:, None])
            / ((repetitions - 1) * (repetitions - 2))).T


def bonferroni_t(contributions: np.ndarray, *, alpha: float = 0.05,
                 family_size: int | None = None) -> dict:
    """Two-sided intervals over a fixed inventory; zero sample variance is unresolved."""
    values = np.asarray(contributions, dtype=float)
    if (values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 1
            or not np.isfinite(values).all() or not 0 < alpha < 1):
        raise ValueError("expected finite contributions[units,endpoints], units >= 2")
    units, endpoints = values.shape
    family_size = endpoints if family_size is None else family_size
    if not isinstance(family_size, int) or isinstance(family_size, bool) or family_size < endpoints:
        raise ValueError("multiplicity family must include every supplied endpoint")
    critical = float(t.ppf(1 - alpha / (2 * family_size), units - 1))
    means, sd = values.mean(axis=0), values.std(axis=0, ddof=1)
    errors = sd / np.sqrt(units)
    rows = []
    for mean, deviation, error in zip(means, sd, errors):
        valid = bool(deviation > 1e-12)
        rows.append(dict(
            estimate=float(mean), unit_sd=float(deviation), standard_error=float(error),
            lower=float(mean - critical * error) if valid else None,
            upper=float(mean + critical * error) if valid else None,
            status="approximate" if valid else "inconclusive_zero_sample_variance",
        ))
    return dict(units=units, endpoint_count=endpoints, family_size=family_size,
                alpha=alpha, critical_value=critical, endpoints=rows)


def infer(kernels: np.ndarray, *, method: str = "paired_t", alpha: float = 0.05,
          family_size: int | None = None) -> dict:
    if method == "paired_t":
        values = pair_contributions(kernels)
        scope = "IID disjoint-pair contributions; approximate for nonnormal contributions"
    elif method == "jackknife_t":
        values = jackknife_pseudovalues(kernels)
        scope = "complete-block U / delete-one-block jackknife; asymptotic, fragile at degeneracy"
    else:
        raise ValueError("method must be paired_t or jackknife_t")
    return dict(bonferroni_t(values, alpha=alpha, family_size=family_size),
                method=method, inference_scope=scope,
                reference_scope="conditional on the fixed finite real reference")
