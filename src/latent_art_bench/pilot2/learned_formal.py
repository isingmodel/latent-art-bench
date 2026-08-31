"""Harmonized A-vector extraction and train-only PCA for pilot_2."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
from PIL import Image

from latent_art_bench.features.learned_formal import (
    SOURCE_REPLICATION_POLICY,
    LearnedFormalResult,
    LoadedSD2VAE,
    extract_learned_formal,
    learned_formal_vector_sha256,
)
from latent_art_bench.io import hash_file, stable_hash
from latent_art_bench.pilot2.config import Pilot2LearnedFormalConfig
from latent_art_bench.pilot2.schemas import (
    Pilot2AtlasWork,
    Pilot2ClassificationEvidence,
    Pilot2DerivedInput,
    Pilot2DeterminismProbe,
    Pilot2Feature,
    Pilot2PCAEvidence,
)


@dataclass(frozen=True)
class Pilot2FrozenPCA:
    mean: np.ndarray
    components: np.ndarray
    evidence: Pilot2PCAEvidence


def _array_sha256(array: np.ndarray) -> str:
    normalized = np.ascontiguousarray(np.asarray(array, dtype="<f8"))
    digest = hashlib.sha256()
    digest.update(str(normalized.shape).encode("ascii"))
    digest.update(b"\0float64-le\0C\0")
    digest.update(normalized.tobytes(order="C"))
    return digest.hexdigest()


def _canonicalize_component_signs(components: np.ndarray) -> np.ndarray:
    components = np.asarray(components, dtype=np.float64).copy()
    for index in range(components.shape[0]):
        pivot = int(np.argmax(np.abs(components[index])))
        if components[index, pivot] < 0:
            components[index] *= -1.0
    return components


def fit_train_only_pca(
    matrix: np.ndarray,
    fit_work_ids: Sequence[str],
    variance_target: float = 0.95,
) -> Pilot2FrozenPCA:
    """Fit the minimum PCA basis reaching 95%, capped at ``n_train - 1``."""

    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] < 2 or values.shape[1] < 2:
        raise ValueError("PCA requires at least two rows and two finite columns")
    if len(fit_work_ids) != values.shape[0] or len(set(fit_work_ids)) != len(fit_work_ids):
        raise ValueError("PCA fit work identifiers must be unique and align with rows")
    if not np.isfinite(values).all():
        raise ValueError("PCA input must be finite")
    if not 0 < variance_target <= 1:
        raise ValueError("PCA variance target must be in (0, 1]")

    mean = values.mean(axis=0)
    centered = values - mean
    _, singular_values, right = np.linalg.svd(centered, full_matrices=False)
    component_cap = min(values.shape[0] - 1, values.shape[1])
    variances = np.square(singular_values[:component_cap])
    total_variance = float(variances.sum())
    if not np.isfinite(total_variance) or total_variance <= 0:
        raise ValueError("PCA cannot qualify a zero-variance training matrix")
    ratios = variances / total_variance
    cumulative = np.cumsum(ratios)
    qualifying = np.flatnonzero(cumulative >= variance_target)
    if qualifying.size == 0:
        raise ValueError("n_train - 1 PCA rank did not reach the variance target")
    component_count = int(qualifying[0]) + 1
    components = _canonicalize_component_signs(right[:component_count])
    mean_sha = _array_sha256(mean)
    basis_sha = _array_sha256(components)
    evidence_payload = {
        "fit_work_ids": list(fit_work_ids),
        "input_dimension": values.shape[1],
        "component_cap": component_cap,
        "component_count": component_count,
        "variance_target": variance_target,
        "cumulative_explained_variance": float(cumulative[component_count - 1]),
        "variance_target_reached": True,
        "mean_sha256": mean_sha,
        "basis_sha256": basis_sha,
    }
    evidence = Pilot2PCAEvidence(
        **evidence_payload,
        state_sha256=stable_hash(evidence_payload),
    )
    return Pilot2FrozenPCA(mean=mean, components=components, evidence=evidence)


def transform_with_pca(matrix: np.ndarray, pca: Pilot2FrozenPCA) -> np.ndarray:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != pca.mean.shape[0]:
        raise ValueError("PCA transform input dimension disagrees with the fitted basis")
    if not np.isfinite(values).all():
        raise ValueError("PCA transform input must be finite")
    return np.ascontiguousarray((values - pca.mean) @ pca.components.T)


def balanced_accuracy(
    expected: Sequence[str], predicted: Sequence[str]
) -> Tuple[float, Dict[str, float]]:
    if not expected or len(expected) != len(predicted):
        raise ValueError("balanced accuracy requires aligned, non-empty labels")
    recalls: Dict[str, float] = {}
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        recalls[label] = float(
            sum(predicted[index] == label for index in indices) / len(indices)
        )
    return float(np.mean(list(recalls.values()))), recalls


def predict_nearest_centroid(
    train_matrix: np.ndarray,
    train_labels: Sequence[str],
    test_matrix: np.ndarray,
) -> List[str]:
    train = np.asarray(train_matrix, dtype=np.float64)
    test = np.asarray(test_matrix, dtype=np.float64)
    if train.ndim != 2 or test.ndim != 2 or train.shape[1] != test.shape[1]:
        raise ValueError("nearest-centroid matrices must have a shared feature dimension")
    if train.shape[0] != len(train_labels) or not train_labels:
        raise ValueError("nearest-centroid training labels do not align")
    labels = sorted(set(train_labels))
    label_array = np.asarray(train_labels)
    centroids = np.stack([train[label_array == label].mean(axis=0) for label in labels])
    distances = np.linalg.norm(test[:, None, :] - centroids[None, :, :], axis=2)
    return [labels[index] for index in np.argmin(distances, axis=1)]


def centroid_classifier_state_sha256(
    train_matrix: np.ndarray, train_labels: Sequence[str]
) -> str:
    train = np.asarray(train_matrix, dtype=np.float64)
    if train.ndim != 2 or train.shape[0] != len(train_labels) or not train_labels:
        raise ValueError("centroid classifier state requires aligned training rows")
    label_array = np.asarray(train_labels)
    payload = {
        "classifier": "nearest_centroid_euclidean",
        "labels": sorted(set(train_labels)),
        "centroid_sha256": {
            label: _array_sha256(train[label_array == label].mean(axis=0))
            for label in sorted(set(train_labels))
        },
    }
    return stable_hash(payload)


def classify_projected(
    train_matrix: np.ndarray,
    train_labels: Sequence[str],
    test_matrix: np.ndarray,
    test_labels: Sequence[str],
    test_work_ids: Sequence[str],
) -> Pilot2ClassificationEvidence:
    predictions = predict_nearest_centroid(train_matrix, train_labels, test_matrix)
    accuracy, recalls = balanced_accuracy(test_labels, predictions)
    return Pilot2ClassificationEvidence(
        expected_labels=list(test_labels),
        predicted_labels=predictions,
        per_class_recall=recalls,
        balanced_accuracy=accuracy,
        test_work_ids=list(test_work_ids),
    )


def extract_harmonized_learned_formal(
    derived: Pilot2DerivedInput,
    loaded_vae: LoadedSD2VAE,
    config: Pilot2LearnedFormalConfig,
    *,
    device: str,
) -> LearnedFormalResult:
    """Extract from the content-addressed common PNG, never the source codec."""

    path = Path(derived.output_path)
    if path.suffix.casefold() != ".png" or not path.is_file():
        raise ValueError("pilot_2 learned extraction requires an existing derived PNG")
    if hash_file(path) != derived.output_sha256:
        raise ValueError("pilot_2 derived PNG content hash is stale")
    with Image.open(path) as image:
        image.load()
        if image.format != "PNG" or image.mode != "RGB":
            raise ValueError("pilot_2 learned extraction accepts only normalized RGB PNGs")

    pins = loaded_vae.verification.pins
    observed_pins = {
        "source_repository": pins.source_repository,
        "source_revision": pins.source_revision,
        "model_repository": pins.model_repository,
        "model_revision": pins.model_revision,
        "model_config_sha256": pins.config_sha256,
        "model_weights_sha256": pins.weights_sha256,
    }
    expected_pins = {
        "source_repository": config.source_repository,
        "source_revision": config.source_revision,
        "model_repository": config.model_repository,
        "model_revision": config.model_revision,
        "model_config_sha256": config.model_config_sha256,
        "model_weights_sha256": config.model_weights_sha256,
    }
    if observed_pins != expected_pins:
        raise ValueError("loaded VAE provenance does not match the pilot_2 feature config")

    result = extract_learned_formal(
        path,
        loaded_vae,
        policy=SOURCE_REPLICATION_POLICY,
        base_seed=config.base_seed,
        device=device,
    )
    if result.vector.shape != (config.raw_dimension,):
        raise ValueError(
            f"pilot_2 A-vector has length {result.vector.size}; expected {config.raw_dimension}"
        )
    metadata = dict(result.metadata)
    if metadata.get("source_extension") != ".png" or metadata.get(
        "intermediate_encoding"
    ) != "png":
        raise ValueError("pilot_2 A-vector extraction left the lossless PNG domain")
    metadata.update(
        {
            "feature_version": config.feature_version,
            "pilot2_representation_role": "harmonized_png_seeded_a_vector",
            "common_derived_png_sha256": derived.output_sha256,
            "acquired_source_sha256": derived.source_sha256,
            "acquired_source_record_id": derived.source_record_id,
            "acquired_source_width": derived.source_width,
            "acquired_source_height": derived.source_height,
            "acquired_source_decoded_format": derived.source_decoded_format,
            "common_preprocessing_config_sha256": derived.preprocessing_config_sha256,
            "upstream_extractor_feature_version": result.metadata.get("feature_version"),
        }
    )
    return LearnedFormalResult(vector=result.vector, metadata=metadata)


def feature_from_extraction(
    work: Pilot2AtlasWork,
    derived: Pilot2DerivedInput,
    result: LearnedFormalResult,
    config: Pilot2LearnedFormalConfig,
) -> Pilot2Feature:
    if result.metadata.get("common_derived_png_sha256") != derived.output_sha256:
        raise ValueError("learned result does not bind to the supplied common PNG")
    config_hash = stable_hash(config.model_dump(mode="json"))
    identity = stable_hash(
        {
            "canonical_work_id": work.canonical_work_id,
            "derived_png_sha256": derived.output_sha256,
            "feature_version": config.feature_version,
            "feature_config_sha256": config_hash,
            "extraction_metadata": result.metadata,
        }
    )
    return Pilot2Feature(
        feature_id=f"pilot2-feature-{identity[:24]}",
        canonical_work_id=work.canonical_work_id,
        artist_id=work.artist_id,
        source_id=work.source_id,
        split=work.split,
        feature_version=config.feature_version,
        feature_config_sha256=config_hash,
        derived_png_sha256=derived.output_sha256,
        vector=np.asarray(result.vector, dtype=np.float32).tolist(),
        extraction_metadata=result.metadata,
        status="ok",
    )


def build_determinism_probe(
    work: Pilot2AtlasWork,
    first: LearnedFormalResult,
    second: LearnedFormalResult,
) -> Pilot2DeterminismProbe:
    first_vector = np.asarray(first.vector, dtype=np.float32)
    second_vector = np.asarray(second.vector, dtype=np.float32)
    first_hash = str(first.metadata.get("vector_sha256", ""))
    second_hash = str(second.metadata.get("vector_sha256", ""))
    if first_hash != learned_formal_vector_sha256(first_vector):
        raise ValueError("first determinism extraction has stale vector provenance")
    if second_hash != learned_formal_vector_sha256(second_vector):
        raise ValueError("second determinism extraction has stale vector provenance")
    first_input = first.metadata.get("common_derived_png_sha256")
    second_input = second.metadata.get("common_derived_png_sha256")
    first_version = first.metadata.get("feature_version")
    second_version = second.metadata.get("feature_version")
    first_seed = first.metadata.get("seed")
    second_seed = second.metadata.get("seed")
    if (
        first_input != second_input
        or first_version != second_version
        or first_seed != second_seed
        or not isinstance(first_input, str)
        or not isinstance(first_version, str)
        or not isinstance(first_seed, int)
    ):
        raise ValueError("determinism extractions do not share one input/config/seed")
    return Pilot2DeterminismProbe(
        artist_id=work.artist_id,
        canonical_work_id=work.canonical_work_id,
        feature_version=first_version,
        derived_png_sha256=first_input,
        seed=first_seed,
        first_vector_sha256=first_hash,
        second_vector_sha256=second_hash,
        exact_equal=bool(np.array_equal(first_vector, second_vector)),
    )


def verify_png_is_lossless_rgb(payload: bytes) -> Tuple[int, int]:
    """Small conformance helper used by acquisition and tests."""

    with Image.open(io.BytesIO(payload)) as image:
        image.load()
        if image.format != "PNG" or image.mode != "RGB":
            raise ValueError("payload is not a normalized RGB PNG")
        return image.size
