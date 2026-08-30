from __future__ import annotations

from typing import Dict

import numpy as np

from latent_art_bench.schemas import AnalysisCell, AnalysisResult


def _matrix(values: object, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError(f"{name} must be a non-empty two-dimensional matrix")
    if not np.isfinite(array).all():
        raise ValueError(f"{name} contains a non-finite value")
    return array


def _mean_pairwise(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.linalg.norm(x[:, None, :] - y[None, :, :], axis=2).mean())


def energy_distance(x: object, y: object) -> float:
    left = _matrix(x, "x")
    right = _matrix(y, "y")
    if left.shape[1] != right.shape[1]:
        raise ValueError("energy-distance matrices must have the same feature dimension")
    value = 2.0 * _mean_pairwise(left, right)
    value -= _mean_pairwise(left, left)
    value -= _mean_pairwise(right, right)
    return max(0.0, float(value))


def _sample_rows(rng: np.random.Generator, values: np.ndarray, size: int) -> np.ndarray:
    if values.shape[0] == size:
        return values
    indices = rng.choice(values.shape[0], size=size, replace=False)
    return values[indices]


def _interval(values: np.ndarray, confidence_level: float) -> list:
    alpha = (1.0 - confidence_level) / 2.0
    return [
        float(np.quantile(values, alpha)),
        float(np.quantile(values, 1.0 - alpha)),
    ]


def analyze_cell(
    cell: AnalysisCell,
    seed: int = 20260829,
    draws: int = 200,
    confidence_level: float = 0.95,
) -> AnalysisResult:
    if draws < 1:
        raise ValueError("draws must be at least one")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    target_train = _matrix(cell.target_train_vectors, "target_train_vectors")
    target_held_out = _matrix(cell.target_held_out_vectors, "target_held_out_vectors")
    generated = _matrix(cell.generated_vectors, "generated_vectors")
    dimensions = {target_train.shape[1], target_held_out.shape[1], generated.shape[1]}
    if len(dimensions) != 1:
        raise ValueError("all cell vectors must have the same dimension")
    if not cell.neighbor_vectors:
        raise ValueError("at least one neighbor distribution is required")

    separations: Dict[str, float] = {}
    neighbor_arrays: Dict[str, np.ndarray] = {}
    for neighbor_id, vectors in cell.neighbor_vectors.items():
        neighbor = _matrix(vectors, f"neighbor_vectors[{neighbor_id}]")
        if neighbor.shape[1] != generated.shape[1]:
            raise ValueError(f"neighbor {neighbor_id} has a mismatched feature dimension")
        neighbor_arrays[neighbor_id] = neighbor
        separations[neighbor_id] = energy_distance(target_held_out, neighbor)

    # The comparison neighbor is frozen from real-only separation, never selected from model output.
    nearest_neighbor_id = min(separations, key=separations.get)
    frozen_neighbor = neighbor_arrays[nearest_neighbor_id]
    full_separation = separations[nearest_neighbor_id]
    if full_separation <= np.finfo(np.float64).eps:
        raise ValueError("target-to-nearest-neighbor separation is zero; calibration is undefined")

    sample_size = min(
        target_train.shape[0],
        target_held_out.shape[0],
        generated.shape[0],
        frozen_neighbor.shape[0],
    )
    rng = np.random.default_rng(seed)
    raw_rows = []
    for _ in range(draws):
        train_sample = _sample_rows(rng, target_train, sample_size)
        held_out_sample = _sample_rows(rng, target_held_out, sample_size)
        generated_sample = _sample_rows(rng, generated, sample_size)
        neighbor_sample = _sample_rows(rng, frozen_neighbor, sample_size)
        target_gap = energy_distance(generated_sample, held_out_sample)
        real_real_gap = energy_distance(train_sample, held_out_sample)
        neighbor_gap = energy_distance(generated_sample, neighbor_sample)
        separation = energy_distance(held_out_sample, neighbor_sample)
        if separation <= np.finfo(np.float64).eps:
            raise ValueError(
                "an equal-sample target-to-neighbor separation is zero; calibration is undefined"
            )
        raw_rows.append(
            (
                target_gap,
                real_real_gap,
                neighbor_gap,
                separation,
                (target_gap - real_real_gap) / separation,
                (neighbor_gap - target_gap) / separation,
            )
        )
    estimates = np.asarray(raw_rows, dtype=np.float64)
    return AnalysisResult(
        cell_id=cell.cell_id,
        target_artist_id=cell.target_artist_id,
        model=cell.model,
        feature_name=cell.feature_name,
        target_gap=float(estimates[:, 0].mean()),
        real_real_gap=float(estimates[:, 1].mean()),
        nearest_neighbor_id=nearest_neighbor_id,
        nearest_neighbor_gap=float(estimates[:, 2].mean()),
        target_neighbor_separation=float(estimates[:, 3].mean()),
        calibrated_target_gap=float(estimates[:, 4].mean()),
        calibrated_target_gap_interval=_interval(estimates[:, 4], confidence_level),
        specificity_margin=float(estimates[:, 5].mean()),
        specificity_margin_interval=_interval(estimates[:, 5], confidence_level),
        subsample_size=sample_size,
        subsample_draws=draws,
        confidence_level=confidence_level,
    )
