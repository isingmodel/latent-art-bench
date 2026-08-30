from __future__ import annotations

import io
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np
from PIL import Image

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.distances import energy_distance
from latent_art_bench.evaluation.frozen_transform import RealOnlyStandardizer
from latent_art_bench.features.chromatic import (
    adjacent_chromatic_distances,
    chromatic_summary,
)
from latent_art_bench.preprocessing.pipeline import preprocess_image_bytes
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    DerivedViewRecord,
    FeatureRow,
    QualificationEvidence,
    ReproductionRecord,
)


def _balanced_accuracy(expected: Sequence[str], predicted: Sequence[str]) -> float:
    if not expected or len(expected) != len(predicted):
        raise ValueError("balanced accuracy requires equally sized, non-empty labels")
    recalls = []
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        recalls.append(sum(predicted[index] == label for index in indices) / len(indices))
    return float(np.mean(recalls))


def _centroids(matrix: np.ndarray, labels: Sequence[str]) -> Dict[str, np.ndarray]:
    if matrix.shape[0] != len(labels):
        raise ValueError("centroid labels do not match the feature matrix")
    return {
        label: matrix[np.asarray(labels) == label].mean(axis=0)
        for label in sorted(set(labels))
    }


def _predict(matrix: np.ndarray, centroids: Dict[str, np.ndarray]) -> List[str]:
    if not centroids:
        raise ValueError("at least one centroid is required")
    labels = sorted(centroids)
    reference = np.stack([centroids[label] for label in labels])
    distances = np.linalg.norm(matrix[:, None, :] - reference[None, :, :], axis=2)
    return [labels[index] for index in np.argmin(distances, axis=1)]


def _median(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=np.float64)
    if array.size == 0:
        raise ValueError("a median cannot be computed from an empty collection")
    return float(np.median(array))


def _quantiles(values: Iterable[float]) -> Dict[str, float]:
    array = np.asarray(list(values), dtype=np.float64)
    if array.size == 0:
        return {"count": 0, "median": float("nan"), "p90": float("nan")}
    return {
        "count": int(array.size),
        "median": float(np.median(array)),
        "p90": float(np.quantile(array, 0.9)),
    }


def _source_behavior(config: PilotConfig) -> Tuple[bool, Dict[str, float]]:
    chromatic = config.measurements.chromatic
    delta = chromatic_summary(np.full(1000, 5.0), chromatic)
    rng = np.random.default_rng(config.qualification.random_seed)
    exponential = chromatic_summary(rng.exponential(4.0, 200_000), chromatic)
    heavy_tail = chromatic_summary(
        np.concatenate((np.zeros(999), np.asarray([1000.0]))), chromatic
    )
    scale_input = np.asarray([0.2, 0.5, 1.0, 2.5, 10.0])
    scale_a = chromatic_summary(scale_input, chromatic)
    scale_b = chromatic_summary(scale_input * 37.0, chromatic)
    metrics = {
        "delta_seamlessness": float(delta["scalars"]["seamlessness"]),
        "exponential_seamlessness": float(
            exponential["scalars"]["seamlessness"]
        ),
        "heavy_tail_seamlessness": float(heavy_tail["scalars"]["seamlessness"]),
        "scale_invariance_max_abs": float(
            np.max(
                np.abs(
                    np.asarray(scale_a["vector"], dtype=np.float64)
                    - np.asarray(scale_b["vector"], dtype=np.float64)
                )
            )
        ),
    }
    recovered = (
        abs(metrics["delta_seamlessness"] + 1.0) <= 1e-12
        and abs(metrics["exponential_seamlessness"]) <= 0.03
        and metrics["heavy_tail_seamlessness"] >= 0.9
        and metrics["scale_invariance_max_abs"] <= 1e-12
    )
    return recovered, metrics


def _perturbed_vectors(
    view: DerivedViewRecord,
    config: PilotConfig,
    root: Path,
) -> Dict[str, List[float]]:
    path = Path(view.output_path)
    if not path.is_absolute():
        path = root / path
    with Image.open(path) as image:
        baseline = image.convert("RGB")
        longest = max(baseline.size)
        if longest > config.qualification.perturbation_long_side:
            scale = config.qualification.perturbation_long_side / float(longest)
            target = tuple(max(1, round(value * scale)) for value in baseline.size)
            resolution = baseline.resize(target, Image.Resampling.LANCZOS, reducing_gap=3.0)
        else:
            resolution = baseline.copy()
        jpeg_buffer = io.BytesIO()
        baseline.save(
            jpeg_buffer,
            format="JPEG",
            quality=config.qualification.perturbation_jpeg_quality,
            subsampling=2,
            optimize=False,
        )
        jpeg_buffer.seek(0)
        with Image.open(jpeg_buffer) as encoded:
            jpeg = encoded.convert("RGB")
    outputs = {}
    for name, image in (("resolution", resolution), ("jpeg", jpeg)):
        rgb = np.asarray(image, dtype=np.uint8)
        outputs[name] = list(
            chromatic_summary(
                adjacent_chromatic_distances(rgb), config.measurements.chromatic
            )["vector"]
        )
    return outputs


def evaluate_chromatic_real_only(
    config: PilotConfig,
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    views: Sequence[DerivedViewRecord],
    features: Sequence[FeatureRow],
    root: Path,
    evidence_artifact_path: str,
) -> Tuple[Dict[str, object], QualificationEvidence]:
    if len(canonical) == 0 or len(features) == 0:
        raise ValueError("real-only qualification requires a non-empty corpus and features")
    reproduction_by_id = {row.reproduction_id: row for row in reproductions}
    view_by_reproduction = {row.reproduction_id: row for row in views}
    primary_rows = [
        row
        for row in features
        if reproduction_by_id[row.reproduction_id].source_id != "cma_alternate_capture"
    ]
    if len(primary_rows) != len(canonical):
        raise ValueError("qualification requires exactly one primary feature per canonical work")
    if any(row.status == "failed" for row in features):
        raise ValueError("failed real feature rows cannot enter qualification")

    train_rows = [row for row in primary_rows if row.split == "train"]
    held_out_rows = [row for row in primary_rows if row.split == "held_out"]
    standardizer = RealOnlyStandardizer()
    state = standardizer.fit(train_rows)
    transformed = standardizer.transform(features)
    vector_by_reproduction = {
        row.reproduction_id: transformed[index] for index, row in enumerate(features)
    }
    train_matrix = np.stack(
        [vector_by_reproduction[row.reproduction_id] for row in train_rows]
    )
    held_out_matrix = np.stack(
        [vector_by_reproduction[row.reproduction_id] for row in held_out_rows]
    )

    artist_train_labels = [str(row.artist_id) for row in train_rows]
    artist_held_out_labels = [str(row.artist_id) for row in held_out_rows]
    artist_predictions = _predict(
        held_out_matrix, _centroids(train_matrix, artist_train_labels)
    )
    artist_accuracy = _balanced_accuracy(artist_held_out_labels, artist_predictions)

    train_source_labels = [reproduction_by_id[row.reproduction_id].source_id for row in train_rows]
    held_out_source_labels = [
        reproduction_by_id[row.reproduction_id].source_id for row in held_out_rows
    ]
    source_predictions = _predict(
        held_out_matrix, _centroids(train_matrix, train_source_labels)
    )
    source_accuracy = _balanced_accuracy(held_out_source_labels, source_predictions)

    leave_source_expected: List[str] = []
    leave_source_predicted: List[str] = []
    for source in sorted(set(train_source_labels)):
        fit_indices = [index for index, label in enumerate(train_source_labels) if label != source]
        test_indices = [index for index, label in enumerate(train_source_labels) if label == source]
        fit_labels = [artist_train_labels[index] for index in fit_indices]
        known_artists = set(fit_labels)
        test_indices = [
            index for index in test_indices if artist_train_labels[index] in known_artists
        ]
        if not fit_indices or not test_indices:
            continue
        predictions = _predict(
            train_matrix[test_indices],
            _centroids(train_matrix[fit_indices], fit_labels),
        )
        leave_source_expected.extend(artist_train_labels[index] for index in test_indices)
        leave_source_predicted.extend(predictions)
    leave_source_accuracy = _balanced_accuracy(
        leave_source_expected, leave_source_predicted
    )

    artist_centroids = _centroids(train_matrix, artist_train_labels)
    within_artist_distances = [
        float(
            np.linalg.norm(
                vector_by_reproduction[row.reproduction_id]
                - artist_centroids[str(row.artist_id)]
            )
        )
        for row in held_out_rows
    ]
    within_artist_median = _median(within_artist_distances)

    primary_by_work = {row.canonical_work_id: row for row in primary_rows}
    alternate_rows = [
        row
        for row in features
        if reproduction_by_id[row.reproduction_id].source_id == "cma_alternate_capture"
    ]
    reproduction_distances = [
        float(
            np.linalg.norm(
                vector_by_reproduction[row.reproduction_id]
                - vector_by_reproduction[
                    primary_by_work[row.canonical_work_id].reproduction_id
                ]
            )
        )
        for row in alternate_rows
    ]
    reproduction_ratio = _median(reproduction_distances) / within_artist_median

    mean = np.asarray(state.mean, dtype=np.float64)
    scale = np.asarray(state.scale, dtype=np.float64)
    perturbation_distances: Dict[str, List[float]] = defaultdict(list)
    for row in primary_rows:
        perturbations = _perturbed_vectors(
            view_by_reproduction[row.reproduction_id], config, root
        )
        baseline = vector_by_reproduction[row.reproduction_id]
        for name, vector in perturbations.items():
            standardized = (np.asarray(vector, dtype=np.float64) - mean) / scale
            perturbation_distances[name].append(
                float(np.linalg.norm(standardized - baseline))
            )
    perturbation_ratios = {
        name: _median(values) / within_artist_median
        for name, values in perturbation_distances.items()
    }

    deterministic_count = 0
    for reproduction in reproductions:
        source_path = Path(reproduction.local_path)
        if not source_path.is_absolute():
            source_path = root / source_path
        with Image.open(source_path) as first_image:
            first, _ = preprocess_image_bytes(first_image, config.preprocessing)
        with Image.open(source_path) as second_image:
            second, _ = preprocess_image_bytes(second_image, config.preprocessing)
        view = view_by_reproduction[reproduction.reproduction_id]
        derived_path = Path(view.output_path)
        if not derived_path.is_absolute():
            derived_path = root / derived_path
        with Image.open(io.BytesIO(first)) as repeated_image, Image.open(
            derived_path
        ) as recorded_image, Image.open(io.BytesIO(second)) as second_image:
            repeated_pixels = np.asarray(repeated_image.convert("RGB"))
            same_pixels = np.array_equal(
                repeated_pixels,
                np.asarray(recorded_image.convert("RGB")),
            ) and np.array_equal(
                repeated_pixels,
                np.asarray(second_image.convert("RGB")),
            )
        # Some source ICC profiles change lossless PNG metadata bytes across
        # Pillow versions while producing identical sRGB pixels. The frozen
        # tolerance is therefore exact pixel identity, not container identity.
        deterministic_count += int(same_pixels)

    neighbor_distances = {}
    held_out_by_artist: Dict[str, List[np.ndarray]] = defaultdict(list)
    for row in held_out_rows:
        held_out_by_artist[str(row.artist_id)].append(
            vector_by_reproduction[row.reproduction_id]
        )
    artist_configs = {artist.artist_id: artist for artist in config.corpus.selected_artists}
    for artist_id, artist in artist_configs.items():
        left = np.stack(held_out_by_artist[artist_id])
        right = np.stack(held_out_by_artist[artist.neighbor_artist_id])
        neighbor_distances[f"{artist_id}__{artist.neighbor_artist_id}"] = energy_distance(
            left, right
        )

    source_behavior_recovered, source_behavior_metrics = _source_behavior(config)
    stable = (
        deterministic_count == len(reproductions)
        and reproduction_ratio
        <= config.qualification.reproduction_to_within_artist_median_ratio_max
        and all(
            ratio <= config.qualification.perturbation_to_within_artist_median_ratio_max
            for ratio in perturbation_ratios.values()
        )
    )
    artist_signal = (
        artist_accuracy >= config.qualification.artist_prediction_min_balanced_accuracy
        and all(value > 0 for value in neighbor_distances.values())
    )
    source_controlled = (
        source_accuracy <= config.qualification.source_prediction_max_balanced_accuracy
        and leave_source_accuracy
        >= config.qualification.leave_source_out_artist_min_balanced_accuracy
    )

    artifact: Dict[str, object] = {
        "schema_version": "1.0",
        "measurement": "chromatic",
        "feature_version": config.measurements.chromatic.feature_version,
        "feature_config_hash": features[0].feature_config_hash,
        "corpus": {
            "canonical_work_count": len(canonical),
            "reproduction_count": len(reproductions),
            "primary_work_count": len(primary_rows),
            "train_work_count": len(train_rows),
            "held_out_work_count": len(held_out_rows),
            "same_work_pair_count": len(alternate_rows),
        },
        "thresholds": config.qualification.model_dump(mode="json"),
        "standardizer": state.model_dump(mode="json"),
        "source_behavior": source_behavior_metrics,
        "same_file_preprocessing": {
            "deterministic_count": deterministic_count,
            "evaluated_count": len(reproductions),
        },
        "reproduction_distance": {
            **_quantiles(reproduction_distances),
            "median_to_within_artist_ratio": reproduction_ratio,
            "scope": "Cleveland Museum of Art alternate captures only",
        },
        "within_artist_held_out_distance": _quantiles(within_artist_distances),
        "perturbation_distance": {
            name: {
                **_quantiles(values),
                "median_to_within_artist_ratio": perturbation_ratios[name],
            }
            for name, values in sorted(perturbation_distances.items())
        },
        "classification": {
            "held_out_artist_balanced_accuracy": artist_accuracy,
            "held_out_source_balanced_accuracy": source_accuracy,
            "leave_source_out_train_artist_balanced_accuracy": leave_source_accuracy,
            "held_out_count": len(held_out_rows),
            "leave_source_out_count": len(leave_source_expected),
        },
        "held_out_neighbor_energy_distance": neighbor_distances,
        "decisions": {
            "source_behavior_recovered": source_behavior_recovered,
            "stable_within_frozen_margin": stable,
            "held_out_artist_signal_valid": artist_signal,
            "source_confounding_controlled": source_controlled,
        },
    }
    conditional_domains = [
        "same-work reproduction calibration is limited to CMA alternate captures"
    ]
    if len(alternate_rows) < config.corpus.target_reproduction_pairs[0]:
        conditional_domains.append(
            "same-work reproduction-pair count is below the 15-pair planning target"
        )
    evidence = QualificationEvidence(
        measurement="chromatic",
        feature_version=config.measurements.chromatic.feature_version,
        feature_config_hash=features[0].feature_config_hash,
        real_work_count=len(canonical),
        reproduction_pair_count=len(alternate_rows),
        source_behavior_recovered=source_behavior_recovered,
        stable_within_frozen_margin=stable,
        held_out_artist_signal_valid=artist_signal,
        source_confounding_controlled=source_controlled,
        conditional_domains=conditional_domains,
        evidence_paths=[evidence_artifact_path],
        notes=[
            "All transformations were fitted on one primary reproduction per real training work.",
            "Nearest-centroid checks are construct diagnostics, not artist-recognition claims.",
        ],
    )
    return artifact, evidence
