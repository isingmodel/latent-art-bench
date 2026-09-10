"""Finite-reference energy distances and paired repetition-block inference."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.features import FAMILIES, NAMES


def weighted_quantile(values: np.ndarray, weights: np.ndarray, probabilities: list) -> np.ndarray:
    values, weights = np.asarray(values), np.asarray(weights)
    if (values.ndim != 1 or weights.shape != values.shape or not len(values)
            or not np.isfinite(values).all() or not np.isfinite(weights).all()
            or np.any(weights < 0) or weights.sum() <= 0
            or any(not 0 <= p <= 1 for p in probabilities)):
        raise ValueError("invalid weighted quantile inputs")
    order = np.argsort(values, kind="stable")
    cumulative = np.cumsum(weights[order]) / weights.sum()
    indices = np.minimum(np.searchsorted(cumulative, probabilities, side="left"), len(values) - 1)
    return values[order[indices]]


def fit_scaler(development: dict[str, np.ndarray]) -> dict:
    if set(development) != set(PAINTER_IDS):
        raise ValueError("scaling requires every painter")
    arrays, weights = [], []
    for painter in PAINTER_IDS:
        values = np.asarray(development[painter], dtype=float)
        if values.ndim != 2 or values.shape[1] != 31 or len(values) < 10:
            raise ValueError(f"insufficient new development: {painter}")
        arrays.append(values)
        weights.extend([1 / (4 * len(values))] * len(values))
    combined = np.concatenate(arrays)
    q = np.array([weighted_quantile(combined[:, i], np.array(weights), [0.25, 0.5, 0.75])
                  for i in range(31)])
    center, scale = q[:, 1], q[:, 2] - q[:, 0]
    invalid = {family: [NAMES[i] for i in range(section.start, section.stop)
                        if not np.isfinite(scale[i]) or scale[i] <= 0]
               for family, section in FAMILIES.items()}
    return dict(center=center.tolist(), scale=scale.tolist(), invalid_coordinates=invalid,
                development_counts={p: len(development[p]) for p in PAINTER_IDS},
                quantile_rule="equal_painter_weighted_empirical_inverse_cdf")


def transform(values: np.ndarray, scaler: dict) -> np.ndarray:
    center, scale = np.asarray(scaler["center"]), np.asarray(scaler["scale"])
    if np.any(scale <= 0) or not np.isfinite(scale).all():
        raise ValueError("one or more feature families have invalid development IQR")
    result = (np.asarray(values) - center) / scale
    if not np.isfinite(result).all():
        raise ValueError("nonfinite transformed feature")
    return result


@dataclass
class EnergyTerms:
    real_self: float
    cross_by_block: np.ndarray
    generated_block_pairs: np.ndarray

    def evaluate(self, counts: np.ndarray | None = None) -> np.ndarray:
        r = len(self.cross_by_block)
        if counts is None:
            counts = np.ones((1, r))
        counts = np.atleast_2d(np.asarray(counts, dtype=float))
        if (counts.shape[1] != r or np.any(counts < 0)
                or not np.isfinite(counts).all() or not np.all(counts.sum(axis=1) == r)):
            raise ValueError("bootstrap counts must represent exactly R sampled blocks")
        cross = counts @ self.cross_by_block / r
        pairs = np.einsum("bi,ij,bj->b", counts, self.generated_block_pairs, counts, optimize=True)
        # Remove same *resampled position*, not every duplicate original block. This distinction
        # preserves the empirical bootstrap when one original block is sampled multiple times.
        diagonal = counts @ np.diag(self.generated_block_pairs)
        return cross - self.real_self - (pairs - diagonal) / (r * (r - 1))


def energy_terms(real: np.ndarray, generated: np.ndarray) -> EnergyTerms:
    real, generated = np.asarray(real, dtype=float), np.asarray(generated, dtype=float)
    if (real.ndim != 2 or generated.ndim != 3 or real.shape[1] != generated.shape[2]
            or not len(real) or generated.shape[0] < 2 or generated.shape[1] < 1
            or not np.isfinite(real).all() or not np.isfinite(generated).all()):
        raise ValueError("expected real[N,D] and complete generated[R,T,D], R >= 2")
    r, t, d = generated.shape
    flat = generated.reshape(r * t, d)
    cross = 2 * cdist(flat, real).reshape(r, t, len(real)).mean(axis=(1, 2))
    self_real = float(cdist(real, real).mean())
    block_pairs = cdist(flat, flat).reshape(r, t, r, t).mean(axis=(1, 3))
    return EnergyTerms(self_real, cross, block_pairs)


def finite_energy(first: np.ndarray, second: np.ndarray) -> float:
    first, second = np.asarray(first), np.asarray(second)
    if not len(first) or not len(second):
        raise ValueError("empty finite population")
    return float(2 * cdist(first, second).mean() - cdist(first, first).mean()
                 - cdist(second, second).mean())


def simultaneous_intervals(points: np.ndarray, replicates: np.ndarray,
                           alpha: float = 0.05) -> tuple[list[dict], float | None]:
    points, replicates = np.asarray(points), np.asarray(replicates)
    if (replicates.ndim != 2 or replicates.shape[1:] != points.shape
            or len(replicates) < 99 or not 0 < alpha < 1
            or not np.isfinite(points).all() or not np.isfinite(replicates).all()):
        raise ValueError("invalid inference array")
    sd = replicates.std(axis=0, ddof=1)
    valid = np.isfinite(sd) & (sd > 1e-12)
    critical = None
    if np.any(valid):
        maxima = np.max(np.abs((replicates[:, valid] - points[valid]) / sd[valid]), axis=1)
        index = min(int(np.ceil((1 - alpha) * (len(maxima) + 1))) - 1, len(maxima) - 1)
        critical = float(np.sort(maxima)[index])
    intervals = []
    for i, point in enumerate(points):
        intervals.append(dict(
            estimate=float(point), bootstrap_sd=float(sd[i]),
            lower=float(point - critical * sd[i]) if valid[i] else None,
            upper=float(point + critical * sd[i]) if valid[i] else None,
            status="estimated" if valid[i] else "inconclusive_zero_bootstrap_variance",
        ))
    return intervals, critical


def analyze(real: dict[str, np.ndarray], generated: dict[str, np.ndarray],
            *, replicates: int = 9999, seed: int = 20260905) -> dict:
    if set(real) != set(PAINTER_IDS) or set(generated) != {*PAINTER_IDS, "artist_free"}:
        raise ValueError("all four real painters and all five generated conditions are required")
    shapes = {np.shape(x) for x in generated.values()}
    if len(shapes) != 1:
        raise ValueError("incomplete or unequal generation grid")
    shape = shapes.pop()
    if len(shape) != 3 or shape[0] < 25 or shape[1:] != (16, 31):
        raise ValueError("primary analysis requires at least 25 complete 16-template blocks")
    rng = np.random.Generator(np.random.PCG64(seed))
    counts = rng.multinomial(shape[0], np.full(shape[0], 1 / shape[0]), size=replicates)
    points, boot, labels, diagnostics = [], [], [], []
    for family, section in FAMILIES.items():
        cache = {}
        for condition, samples in generated.items():
            for target, reference in real.items():
                terms = energy_terms(reference[:, section], samples[:, :, section])
                cache[condition, target] = (float(terms.evaluate()[0]), terms.evaluate(counts))
        for painter in PAINTER_IDS:
            own, own_boot = cache[painter, painter]
            comparisons = [("target_fit", None, own, own_boot)]
            for other in PAINTER_IDS:
                if other != painter:
                    point, resampled = cache[painter, other]
                    comparisons.append(("specificity", other, own - point, own_boot - resampled))
            control, control_boot = cache["artist_free", painter]
            comparisons.append(("control_improvement", "artist_free", own - control,
                                own_boot - control_boot))
            for kind, comparison, point, resampled in comparisons:
                labels.append(dict(painter_id=painter, family=family, endpoint=kind,
                                   comparison=comparison))
                points.append(point)
                boot.append(resampled)
            x = real[painter][:, section]
            y = generated[painter][:, :, section].reshape(-1, section.stop - section.start)
            for j, name in enumerate(NAMES[section]):
                real_iqr = float(np.diff(np.quantile(x[:, j], [0.25, 0.75]))[0])
                generated_iqr = float(np.diff(np.quantile(y[:, j], [0.25, 0.75]))[0])
                diagnostics.append(dict(
                    painter_id=painter, family=family, coordinate=name,
                    median_difference=float(np.median(y[:, j]) - np.median(x[:, j])),
                    iqr_ratio=generated_iqr / real_iqr if real_iqr > 0 else None,
                    status="descriptive" if real_iqr > 0 else "zero_reference_iqr",
                ))
    intervals, critical = simultaneous_intervals(np.array(points), np.array(boot).T)
    endpoints = [dict(label, **interval) for label, interval in zip(labels, intervals)]
    return dict(
        schema_version="pfg-v2-analysis/1.0", real_counts={p: len(x) for p, x in real.items()},
        repetitions=shape[0], templates=shape[1], bootstrap_replicates=replicates,
        bootstrap_seed=seed, bootstrap_rng="PCG64", simultaneous_endpoint_count=len(endpoints),
        simultaneous_critical_value=critical, endpoints=endpoints,
        coordinate_diagnostics=diagnostics,
        reproduction_status="not_demonstrated_no_independent_capture_equivalence_calibration",
        inference_scope="approximate paired-block intervals, conditional on finite real frame",
    )
