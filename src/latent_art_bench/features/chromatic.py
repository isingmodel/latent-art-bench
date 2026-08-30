from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
from PIL import Image

from latent_art_bench.config import ChromaticConfig
from latent_art_bench.io import hash_file, stable_hash
from latent_art_bench.schemas import DerivedViewRecord, FeatureRow


def srgb_to_cielab(rgb: np.ndarray) -> np.ndarray:
    """Convert sRGB bytes or floats in [0, 255] to CIE 1976 L*a*b* under D65."""
    values = np.asarray(rgb, dtype=np.float64) / 255.0
    if values.ndim < 2 or values.shape[-1] != 3:
        raise ValueError("expected an array whose last dimension is RGB")
    linear = np.where(values <= 0.04045, values / 12.92, ((values + 0.055) / 1.055) ** 2.4)
    matrix = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    )
    xyz = linear @ matrix.T
    xyz /= np.array([0.95047, 1.0, 1.08883], dtype=np.float64)
    delta = 6.0 / 29.0
    f_xyz = np.where(xyz > delta**3, np.cbrt(xyz), xyz / (3 * delta**2) + 4.0 / 29.0)
    lightness = 116.0 * f_xyz[..., 1] - 16.0
    a_axis = 500.0 * (f_xyz[..., 0] - f_xyz[..., 1])
    b_axis = 200.0 * (f_xyz[..., 1] - f_xyz[..., 2])
    return np.stack((lightness, a_axis, b_axis), axis=-1)


def adjacent_chromatic_distances(rgb: np.ndarray) -> np.ndarray:
    lab = srgb_to_cielab(rgb)
    horizontal = np.linalg.norm(lab[:, 1:, :] - lab[:, :-1, :], axis=2).reshape(-1)
    vertical = np.linalg.norm(lab[1:, :, :] - lab[:-1, :, :], axis=2).reshape(-1)
    return np.concatenate((horizontal, vertical))


def chromatic_summary(distances: np.ndarray, config: ChromaticConfig) -> Dict[str, object]:
    values = np.asarray(distances, dtype=np.float64).reshape(-1)
    if values.size == 0:
        raise ValueError("at least one adjacent-pixel distance is required")
    mean = float(values.mean())
    standard_deviation = float(values.std(ddof=config.standard_deviation_ddof))
    degenerate = mean <= config.degenerate_epsilon
    if degenerate:
        coefficient_of_variation = 0.0
        seamlessness = -1.0
        normalized = np.zeros_like(values)
    else:
        coefficient_of_variation = standard_deviation / mean
        denominator = standard_deviation + mean
        seamlessness = (standard_deviation - mean) / denominator
        normalized = values / mean

    lower_edges = np.asarray(config.normalized_histogram_lower_edges, dtype=np.float64)
    bins = np.concatenate((lower_edges, np.array([np.inf])))
    counts, _ = np.histogram(normalized, bins=bins)
    vector = counts.astype(np.float64) / float(values.size)
    quantiles = np.quantile(normalized, [0.05, 0.25, 0.5, 0.75, 0.95])
    scalars = {
        "distance_count": float(values.size),
        "mean_delta_e76": mean,
        "std_delta_e76": standard_deviation,
        "coefficient_of_variation": float(coefficient_of_variation),
        "seamlessness": float(seamlessness),
        "normalized_q05": float(quantiles[0]),
        "normalized_q25": float(quantiles[1]),
        "normalized_q50": float(quantiles[2]),
        "normalized_q75": float(quantiles[3]),
        "normalized_q95": float(quantiles[4]),
    }
    return {"vector": vector.tolist(), "scalars": scalars, "degenerate": degenerate}


def extract_chromatic_feature(
    view: DerivedViewRecord,
    config: ChromaticConfig,
    root: Path,
    artist_id: Optional[str] = None,
    split: str = "unassigned",
) -> FeatureRow:
    path = Path(view.output_path)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise FileNotFoundError(f"missing derived view: {path}")
    if hash_file(path) != view.output_sha256:
        raise ValueError(f"derived-view hash mismatch: {view.derived_view_id}")
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    summary = chromatic_summary(adjacent_chromatic_distances(rgb), config)
    config_hash = stable_hash(config.model_dump(mode="json"))
    feature_id = stable_hash(
        {
            "view": view.derived_view_id,
            "feature": config.feature_version,
            "config": config_hash,
        }
    )
    return FeatureRow(
        feature_id=f"feature-{feature_id[:24]}",
        derived_view_id=view.derived_view_id,
        reproduction_id=view.reproduction_id,
        canonical_work_id=view.canonical_work_id,
        artist_id=artist_id,
        split=split,
        feature_name="chromatic_distance_seamlessness",
        feature_version=config.feature_version,
        feature_config_hash=config_hash,
        vector=summary["vector"],
        scalars=summary["scalars"],
        status="degenerate" if summary["degenerate"] else "ok",
    )


def extract_chromatic_features(
    views: Iterable[DerivedViewRecord],
    config: ChromaticConfig,
    root: Path,
    artist_by_work: Optional[Dict[str, str]] = None,
    split_by_work: Optional[Dict[str, str]] = None,
) -> List[FeatureRow]:
    artist_by_work = artist_by_work or {}
    split_by_work = split_by_work or {}
    return [
        extract_chromatic_feature(
            view,
            config,
            root,
            artist_id=artist_by_work.get(view.canonical_work_id),
            split=split_by_work.get(view.canonical_work_id, "unassigned"),
        )
        for view in views
    ]
