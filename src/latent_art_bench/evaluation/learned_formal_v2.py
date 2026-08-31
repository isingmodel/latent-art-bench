"""Real-only qualification for the repaired Kim et al. SD2 A-vector.

The source paper uses a 16,384-value Stable Diffusion 2.0 VAE latent.  The
authors' released extractor samples the posterior without publishing its RNG
state.  The project therefore keeps the sampled representation, but repairs
the seed deterministically in :mod:`latent_art_bench.features.learned_formal`.

This module qualifies that explicitly versioned repair.  PCA is fitted only on
one primary reproduction per real training work.  Leave-source-out evaluation
fits a fresh PCA inside every fold so neither centering nor the learned basis
can see the held source.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np
from pydantic import Field

from latent_art_bench.config import QualificationConfig
from latent_art_bench.evaluation.distances import energy_distance
from latent_art_bench.features.learned_formal import (
    FLATTEN_ORDER,
    LATENT_SCALE,
    LATENT_SHAPE,
    SOURCE_FILE_FEATURE_VERSION,
    SOURCE_REPLICATION_POLICY,
    SOURCE_REVISION,
    LearnedFormalResult,
    learned_formal_vector_sha256,
)
from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    FeatureRow,
    ReproductionRecord,
    StrictModel,
)

RAW_DIMENSION = 16_384
FEATURE_NAME = "learned_formal"
FEATURE_VERSION = SOURCE_FILE_FEATURE_VERSION
SOURCE_MIN_NATIVE_AREA_EXCLUSIVE = 410 * 410
SOURCE_MAX_ASPECT_RATIO_EXCLUSIVE = 2.0
MODEL_REPOSITORY = "Manojb/stable-diffusion-2-base"
MODEL_REVISION = "64bf7b4f10eee35494b38d55c06c0c78cf8b44d0"
MODEL_CONFIG_SHA256 = "6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0"
MODEL_WEIGHTS_SHA256 = "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
OPENCV_VERSION = "4.14.0"
OPENCV_BUILD_SHA256 = "c201b5ba726b7370afc3cb0d338454e2964afe1aa907849908b27850ecc043cf"
PILLOW_VERSION = "11.3.0"
SOURCE_INPUT_ROLE = "original_reproduction_file"
SOURCE_PREPROCESSING_POLICY = (
    "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
)
SEED_STRATEGY = "sha256_of_resized_rgb_plus_base_seed"
REPRESENTATION_ROLE = "source_replication_seeded_posterior_sample"
CONDITIONAL_LIMITATIONS = (
    "posterior sampling is deterministically seed-repaired because the authors published "
    "neither a seed nor RNG state",
    "no author-supplied A-vectors or reference vector are available for byte-level comparison",
    "the authors' source repository has no explicit reuse license; this evaluator is a "
    "clean-room implementation",
)


class LearnedFormalV2Protocol(StrictModel):
    """Frozen learned-formal qualification behavior."""

    protocol_version: Literal["kim2026-sd20-a-vector-qualification-v4"] = (
        "kim2026-sd20-a-vector-qualification-v4"
    )
    feature_name: Literal["learned_formal"] = "learned_formal"
    feature_version: Literal[
        "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
    ] = FEATURE_VERSION
    expected_policy: Literal["seeded_posterior_sample"] = SOURCE_REPLICATION_POLICY
    expected_representation_role: Literal[
        "source_replication_seeded_posterior_sample"
    ] = REPRESENTATION_ROLE
    expected_seed_strategy: Literal[
        "sha256_of_resized_rgb_plus_base_seed"
    ] = SEED_STRATEGY
    expected_base_seed: Literal[20260830] = 20260830
    expected_device: Literal["mps"] = "mps"
    expected_source_input_role: Literal["original_reproduction_file"] = SOURCE_INPUT_ROLE
    expected_source_preprocessing_policy: Literal[
        "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
    ] = SOURCE_PREPROCESSING_POLICY
    expected_source_repository: Literal[
        "https://github.com/aljinny/art-history"
    ] = "https://github.com/aljinny/art-history"
    expected_source_revision: Literal[
        "7da12358cf34dad2184f357a048c2cf114b3c4e0"
    ] = SOURCE_REVISION
    expected_model_repository: Literal[
        "Manojb/stable-diffusion-2-base"
    ] = MODEL_REPOSITORY
    expected_model_revision: Literal[
        "64bf7b4f10eee35494b38d55c06c0c78cf8b44d0"
    ] = MODEL_REVISION
    expected_model_config_sha256: Literal[
        "6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0"
    ] = MODEL_CONFIG_SHA256
    expected_model_weights_sha256: Literal[
        "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
    ] = MODEL_WEIGHTS_SHA256
    expected_opencv_version: Literal["4.14.0"] = OPENCV_VERSION
    expected_opencv_build_sha256: Literal[
        "c201b5ba726b7370afc3cb0d338454e2964afe1aa907849908b27850ecc043cf"
    ] = OPENCV_BUILD_SHA256
    expected_pillow_version: Literal["11.3.0"] = PILLOW_VERSION
    expected_jpeg_codec_version: Literal["6.2"] = "6.2"
    expected_python_version: Literal["3.13.11"] = "3.13.11"
    expected_platform_system: Literal["Darwin"] = "Darwin"
    expected_platform_release: Literal["25.6.0"] = "25.6.0"
    expected_platform_machine: Literal["arm64"] = "arm64"
    expected_numpy_version: Literal["2.5.2"] = "2.5.2"
    expected_torch_version: Literal["2.13.0"] = "2.13.0"
    expected_diffusers_version: Literal["0.40.0"] = "0.40.0"
    expected_torch_mps_built: Literal[True] = True
    expected_torch_mps_available: Literal[True] = True
    expected_feature_config_hash: Optional[str] = None
    raw_dimension: Literal[16384] = RAW_DIMENSION
    pca_variance_target: Literal[0.95] = 0.95
    pca_max_components: Literal[32] = 32
    pca_whiten: Literal[False] = False
    pca_solver: Literal["numpy_svd_full_sign_canonicalized"] = "numpy_svd_full_sign_canonicalized"
    alternate_source_ids: Tuple[str, ...] = ("cma_alternate_capture",)


class PCABasisEvidence(StrictModel):
    fit_work_ids: List[str]
    fit_reproduction_ids: List[str]
    fit_source_ids: List[str]
    input_dimension: Literal[16384] = RAW_DIMENSION
    component_count: int = Field(ge=1, le=32)
    basis_shape: Tuple[int, int]
    variance_target: Literal[0.95] = 0.95
    max_components: Literal[32] = 32
    whiten: Literal[False] = False
    explained_variance_ratio: List[float]
    cumulative_explained_variance: float = Field(ge=0, le=1)
    variance_target_reached: bool
    mean_sha256: str
    basis_sha256: str
    state_sha256: str


@dataclass(frozen=True)
class FrozenPCA:
    mean: np.ndarray
    components: np.ndarray
    evidence: PCABasisEvidence


class LabelClassificationEvidence(StrictModel):
    expected_labels: List[str]
    predicted_labels: List[str]
    per_class_recall: Dict[str, float]
    balanced_accuracy: float = Field(ge=0, le=1)


class NestedPCAFoldEvidence(StrictModel):
    held_out_source_id: str
    fit_source_ids: List[str]
    fit_work_ids: List[str]
    test_work_ids: List[str]
    eligible_test_work_ids: List[str]
    known_artist_ids: List[str]
    pca: Optional[PCABasisEvidence]
    classification: Optional[LabelClassificationEvidence]
    supported: bool
    reason: Optional[str] = None


class NestedSourceEvaluation(StrictModel):
    folds: List[NestedPCAFoldEvidence]
    pooled_classification: Optional[LabelClassificationEvidence]
    all_sources_supported: bool


class ClassificationEvidence(StrictModel):
    held_out_artist: LabelClassificationEvidence
    held_out_source: LabelClassificationEvidence
    nested_leave_source_out_artist: Optional[LabelClassificationEvidence]
    held_out_work_count: int = Field(ge=0)
    nested_test_work_count: int = Field(ge=0)


class WithinArtistDistance(StrictModel):
    canonical_work_id: str
    reproduction_id: str
    artist_id: str
    distance: float = Field(ge=0)


class GroupedIndependentAlternateDistance(StrictModel):
    canonical_work_id: str
    artist_id: str
    alternate_image_count: int = Field(gt=0)
    alternate_reproduction_ids: List[str]
    image_level_distances: List[float]
    independent_work_distance: float = Field(ge=0)


class DistanceRatioEvidence(StrictModel):
    metric: str
    numerator_unit: str
    numerator_count: int = Field(ge=0)
    denominator_count: int = Field(ge=0)
    numerator_median: Optional[float] = None
    denominator_median: Optional[float] = None
    point_ratio: Optional[float] = None
    confidence_level: float = Field(gt=0, lt=1)
    confidence_lower: Optional[float] = Field(default=None, ge=0)
    confidence_upper: Optional[float] = Field(default=None, ge=0)
    bootstrap_draws: int = Field(ge=0)
    random_seed: int
    decision_rule: Literal["bootstrap_upper_bound_le_threshold"] = (
        "bootstrap_upper_bound_le_threshold"
    )
    threshold: float = Field(gt=0)
    supported: bool
    reason: Optional[str] = None


class ExtractionMetadataEvidence(StrictModel):
    row_count: int = Field(gt=0)
    feature_ids: List[str]
    resolved_device: str
    opencv_version: str
    opencv_build_sha256: str
    pillow_version: str
    jpeg_codec_version: str
    python_version: str
    platform_system: str
    platform_release: str
    platform_machine: str
    numpy_version: str
    torch_version: str
    diffusers_version: str
    torch_mps_built: bool
    torch_mps_available: bool
    model_repository: str
    model_revision: str
    model_config_sha256: str
    model_weights_sha256: str
    source_repository: str
    source_revision: str
    source_checkout_verified_for_all_rows: bool
    metadata_sha256: str


class ArtistNeighborEnergyDistance(StrictModel):
    artist_id: str
    neighbor_artist_id: str
    artist_work_count: int = Field(ge=0)
    neighbor_work_count: int = Field(ge=0)
    energy_distance: Optional[float] = Field(default=None, ge=0)
    supported: bool
    reason: Optional[str] = None


class LearnedFormalDeterminismProbe(StrictModel):
    reproduction_id: str
    first_vector_sha256: str
    repeated_vector_sha256: str
    first_metadata_sha256: str
    repeated_metadata_sha256: str
    vector_exact_match: bool
    metadata_exact_match: bool
    contract_verified: bool
    policy: str
    feature_version: str
    seed: Optional[int]
    seed_strategy: str
    seed_basis_sha256: Optional[str]
    config_sha256: Optional[str]
    weights_sha256: Optional[str]


class SourceBehaviorEvidence(StrictModel):
    expected_policy: str
    expected_feature_version: str
    vector_contract_verified: bool
    determinism_probe_count: int = Field(ge=0)
    exact_repeat_count: int = Field(ge=0)
    exact_metadata_count: int = Field(ge=0)
    feature_row_match_count: int = Field(ge=0)
    probe_reproduction_ids: List[str]
    deterministic_repeats_verified: bool
    source_behavior_recovered: bool
    limitations: List[str]


class LearnedFormalThresholdEvidence(StrictModel):
    artist_prediction_min_balanced_accuracy: float = Field(ge=0, le=1)
    source_prediction_max_balanced_accuracy: float = Field(ge=0, le=1)
    leave_source_out_artist_min_balanced_accuracy: float = Field(ge=0, le=1)
    reproduction_to_within_artist_median_ratio_max: float = Field(gt=0)


class SourceDomainEligibilityEvidence(StrictModel):
    """Whether primary inputs satisfy Kim et al.'s pre-resize image filter."""

    minimum_native_area_exclusive: Literal[168100] = SOURCE_MIN_NATIVE_AREA_EXCLUSIVE
    maximum_aspect_ratio_exclusive: Literal[2.0] = SOURCE_MAX_ASPECT_RATIO_EXCLUSIVE
    evaluated_primary_count: int = Field(ge=0)
    eligible_primary_count: int = Field(ge=0)
    aspect_ratio_violation_count: int = Field(ge=0)
    aspect_ratio_violating_reproduction_ids: List[str]
    native_area_violation_count: int = Field(ge=0)
    native_area_violating_reproduction_ids: List[str]
    missing_dimension_count: int = Field(ge=0)
    missing_dimension_reproduction_ids: List[str]
    all_primary_inputs_eligible: bool


class JointArtistSourceSplitEvidence(StrictModel):
    """Coverage needed to distinguish artist signal from acquisition source."""

    artist_ids: List[str]
    source_ids: List[str]
    cell_counts: Dict[str, Dict[str, int]]
    missing_train_cells: List[str]
    missing_held_out_cells: List[str]
    complete_joint_coverage: bool


class LearnedFormalV2QualificationResult(StrictModel):
    record_type: Literal["learned_formal_v2_qualification"] = "learned_formal_v2_qualification"
    schema_version: Literal["2.0"] = "2.0"
    status: Literal["conditional_pass", "fail"]
    protocol: LearnedFormalV2Protocol
    protocol_sha256: str
    feature_config_sha256: str
    thresholds: LearnedFormalThresholdEvidence
    source_domain_eligibility: SourceDomainEligibilityEvidence
    joint_artist_source_split: JointArtistSourceSplitEvidence
    primary_pca: PCABasisEvidence
    classification: ClassificationEvidence
    nested_source_evaluation: NestedSourceEvaluation
    within_artist_distances: List[WithinArtistDistance]
    within_artist_median: Optional[float]
    reproduction_groups: List[GroupedIndependentAlternateDistance]
    reproduction_stability: DistanceRatioEvidence
    artist_neighbor_energy_distances: List[ArtistNeighborEnergyDistance]
    extraction_metadata: ExtractionMetadataEvidence
    source_behavior: SourceBehaviorEvidence
    source_behavior_recovered: bool
    stable_within_frozen_margin: bool
    held_out_artist_signal_valid: bool
    source_confounding_controlled: bool
    primary_work_count: int = Field(ge=0)
    train_work_count: int = Field(ge=0)
    held_out_work_count: int = Field(ge=0)
    alternate_image_count: int = Field(ge=0)
    independent_alternate_work_count: int = Field(ge=0)
    supported_scope: List[str]
    conditional_limitations: List[str]
    unsupported_conditions: List[str]
    result_sha256: str


@dataclass(frozen=True)
class PreparedLearnedFormalRows:
    work_by_id: Dict[str, CanonicalWorkRecord]
    reproduction_by_id: Dict[str, ReproductionRecord]
    feature_by_reproduction: Dict[str, FeatureRow]
    primary_rows: Tuple[FeatureRow, ...]
    alternate_rows: Tuple[FeatureRow, ...]
    feature_config_hash: str
    extraction_metadata: ExtractionMetadataEvidence


def _array_sha256(values: np.ndarray) -> str:
    array = np.asarray(values, dtype="<f8", order="C")
    digest = hashlib.sha256()
    digest.update(str(array.shape).encode("ascii"))
    digest.update(b"\0float64-le\0C\0")
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _seed_from_basis_sha256(seed_basis_sha256: str, base_seed: int) -> int:
    if not _is_sha256(seed_basis_sha256):
        raise ValueError("seed_basis_sha256 must be a lowercase SHA-256")
    digest = hashlib.sha256()
    digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
    digest.update(base_seed.to_bytes(8, "big", signed=False))
    digest.update(bytes.fromhex(seed_basis_sha256))
    return int.from_bytes(digest.digest()[:8], "big", signed=False) & ((1 << 63) - 1)


def _source_extension(path: str) -> str:
    extension = Path(path).suffix.lower()
    return ".jpg" if extension == ".jpeg" else extension


def _validated_extraction_metadata(
    feature: FeatureRow,
    reproduction: ReproductionRecord,
    protocol: LearnedFormalV2Protocol,
) -> Dict[str, object]:
    metadata = dict(feature.extraction_metadata)
    if not metadata:
        raise ValueError(f"feature {feature.feature_id} lacks extraction metadata")
    if reproduction.sha256 is None:
        raise ValueError(
            f"reproduction {reproduction.reproduction_id} lacks a source SHA-256"
        )
    extension = _source_extension(reproduction.local_path)
    if extension not in {".jpg", ".png", ".webp"}:
        raise ValueError(
            f"reproduction {reproduction.reproduction_id} has an unsupported source extension"
        )
    exact = {
        "record_type": "learned_formal_extraction",
        "schema_version": "2.0",
        "feature_id": feature.feature_id,
        "linkage_derived_view_id": feature.derived_view_id,
        "input_role": protocol.expected_source_input_role,
        "input_path": reproduction.local_path,
        "input_sha256": reproduction.sha256,
        "feature_config_hash": feature.feature_config_hash,
        "feature_version": protocol.feature_version,
        "representation_role": protocol.expected_representation_role,
        "policy": protocol.expected_policy,
        "seed_strategy": protocol.expected_seed_strategy,
        "base_seed": protocol.expected_base_seed,
        "input_size": [512, 512],
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": list(LATENT_SHAPE),
        "latent_scale": LATENT_SCALE,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": FLATTEN_ORDER,
        "vector_length": protocol.raw_dimension,
        "device": protocol.expected_device,
        "dtype": "float32",
        "source_input_role": protocol.expected_source_input_role,
        "source_preprocessing_policy": protocol.expected_source_preprocessing_policy,
        "source_file_sha256": reproduction.sha256,
        "source_extension": extension,
        "intermediate_encoding": extension.lstrip("."),
        "source_repository": protocol.expected_source_repository,
        "source_revision": protocol.expected_source_revision,
        "source_checkout_verified": True,
        "model_repository": protocol.expected_model_repository,
        "model_revision": protocol.expected_model_revision,
        "config_sha256": protocol.expected_model_config_sha256,
        "weights_sha256": protocol.expected_model_weights_sha256,
        "opencv_version": protocol.expected_opencv_version,
        "opencv_build_sha256": protocol.expected_opencv_build_sha256,
        "pillow_version": protocol.expected_pillow_version,
        "jpeg_codec_version": protocol.expected_jpeg_codec_version,
        "python_version": protocol.expected_python_version,
        "platform_system": protocol.expected_platform_system,
        "platform_release": protocol.expected_platform_release,
        "platform_machine": protocol.expected_platform_machine,
        "numpy_version": protocol.expected_numpy_version,
        "torch_version": protocol.expected_torch_version,
        "diffusers_version": protocol.expected_diffusers_version,
        "torch_mps_built": protocol.expected_torch_mps_built,
        "torch_mps_available": protocol.expected_torch_mps_available,
        "artifacts_verified": True,
        "vector_sha256": learned_formal_vector_sha256(feature.vector),
    }
    mismatches = [
        key for key, expected in exact.items() if metadata.get(key) != expected
    ]
    if mismatches:
        raise ValueError(
            f"feature {feature.feature_id} extraction metadata mismatch: "
            + ", ".join(sorted(mismatches))
        )
    if protocol.expected_feature_config_hash is not None and (
        feature.feature_config_hash != protocol.expected_feature_config_hash
    ):
        raise ValueError(
            f"feature {feature.feature_id} does not match the protocol config hash"
        )
    sha_fields = (
        "feature_config_hash",
        "linkage_derived_view_sha256",
        "input_sha256",
        "source_file_sha256",
        "intermediate_payload_sha256",
        "seed_basis_sha256",
        "config_sha256",
        "weights_sha256",
        "vector_sha256",
    )
    malformed = [key for key in sha_fields if not _is_sha256(metadata.get(key))]
    if malformed:
        raise ValueError(
            f"feature {feature.feature_id} has malformed extraction hashes: "
            + ", ".join(sorted(malformed))
        )
    seed_basis = str(metadata["seed_basis_sha256"])
    expected_seed = _seed_from_basis_sha256(seed_basis, protocol.expected_base_seed)
    if metadata.get("seed") != expected_seed:
        raise ValueError(
            f"feature {feature.feature_id} seed does not match its content-derived basis"
        )
    return metadata


def validate_extraction_metadata(
    features: Sequence[FeatureRow],
    reproduction_by_id: Mapping[str, ReproductionRecord],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> ExtractionMetadataEvidence:
    """Validate and hash every row's source/model/runtime extraction contract."""

    protocol = protocol or LearnedFormalV2Protocol()
    ordered = sorted(features, key=lambda row: row.feature_id)
    if not ordered:
        raise ValueError("extraction metadata validation requires feature rows")
    if len({row.feature_id for row in ordered}) != len(ordered):
        raise ValueError("extraction metadata feature identifiers must be unique")
    validated: List[Dict[str, object]] = []
    for feature in ordered:
        reproduction = reproduction_by_id.get(feature.reproduction_id)
        if reproduction is None:
            raise ValueError(
                f"feature {feature.feature_id} lacks a joined reproduction for metadata"
            )
        validated.append(_validated_extraction_metadata(feature, reproduction, protocol))
    return ExtractionMetadataEvidence(
        row_count=len(ordered),
        feature_ids=[row.feature_id for row in ordered],
        resolved_device=protocol.expected_device,
        opencv_version=protocol.expected_opencv_version,
        opencv_build_sha256=protocol.expected_opencv_build_sha256,
        pillow_version=protocol.expected_pillow_version,
        jpeg_codec_version=protocol.expected_jpeg_codec_version,
        python_version=protocol.expected_python_version,
        platform_system=protocol.expected_platform_system,
        platform_release=protocol.expected_platform_release,
        platform_machine=protocol.expected_platform_machine,
        numpy_version=protocol.expected_numpy_version,
        torch_version=protocol.expected_torch_version,
        diffusers_version=protocol.expected_diffusers_version,
        torch_mps_built=protocol.expected_torch_mps_built,
        torch_mps_available=protocol.expected_torch_mps_available,
        model_repository=protocol.expected_model_repository,
        model_revision=protocol.expected_model_revision,
        model_config_sha256=protocol.expected_model_config_sha256,
        model_weights_sha256=protocol.expected_model_weights_sha256,
        source_repository=protocol.expected_source_repository,
        source_revision=protocol.expected_source_revision,
        source_checkout_verified_for_all_rows=all(
            bool(metadata["source_checkout_verified"]) for metadata in validated
        ),
        metadata_sha256=stable_hash(validated),
    )


def _as_matrix(values: object, expected_dimension: int = RAW_DIMENSION) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        raise ValueError("learned-formal features must form a non-empty matrix")
    if matrix.shape[1] != expected_dimension:
        raise ValueError(
            f"learned-formal vectors must have {expected_dimension} values; found {matrix.shape[1]}"
        )
    if not np.isfinite(matrix).all():
        raise ValueError("learned-formal features contain non-finite values")
    return matrix


def _canonicalize_component_signs(components: np.ndarray) -> np.ndarray:
    oriented = np.asarray(components, dtype=np.float64).copy()
    for index in range(oriented.shape[0]):
        component = oriented[index]
        pivot = int(np.argmax(np.abs(component)))
        if component[pivot] < 0:
            oriented[index] *= -1.0
    return np.ascontiguousarray(oriented)


def fit_real_pca(
    matrix: np.ndarray,
    work_ids: Sequence[str],
    reproduction_ids: Sequence[str],
    source_ids: Sequence[str],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> FrozenPCA:
    """Fit the frozen center-only PCA after sorting independent works by ID."""

    protocol = protocol or LearnedFormalV2Protocol()
    values = _as_matrix(matrix, protocol.raw_dimension)
    row_count = values.shape[0]
    if any(len(labels) != row_count for labels in (work_ids, reproduction_ids, source_ids)):
        raise ValueError("PCA labels do not match the feature matrix")
    if len(set(work_ids)) != row_count:
        raise ValueError("PCA fit requires exactly one row per canonical work")
    if len(set(reproduction_ids)) != row_count:
        raise ValueError("PCA fit reproduction identifiers must be unique")
    if row_count < 2:
        raise ValueError("PCA fit requires at least two independent training works")

    order = sorted(range(row_count), key=lambda index: (work_ids[index], reproduction_ids[index]))
    ordered = values[order]
    ordered_work_ids = [work_ids[index] for index in order]
    ordered_reproduction_ids = [reproduction_ids[index] for index in order]
    ordered_source_ids = [source_ids[index] for index in order]
    mean = ordered.mean(axis=0, dtype=np.float64)
    centered = ordered - mean
    _, singular_values, right_vectors = np.linalg.svd(centered, full_matrices=False)
    squared = np.square(singular_values, dtype=np.float64)
    total = float(squared.sum())
    if total <= np.finfo(np.float64).eps:
        raise ValueError("PCA fit vectors have zero total variance")
    tolerance = singular_values[0] * max(centered.shape) * np.finfo(np.float64).eps
    rank = int(np.sum(singular_values > tolerance))
    if rank < 1:
        raise ValueError("PCA fit vectors have zero numerical rank")
    ratios = squared / total
    cumulative = np.cumsum(ratios)
    target_count = int(np.searchsorted(cumulative, protocol.pca_variance_target) + 1)
    component_count = min(target_count, protocol.pca_max_components, rank)
    components = _canonicalize_component_signs(right_vectors[:component_count])
    selected_ratios = ratios[:component_count]
    achieved = float(selected_ratios.sum())
    mean_sha256 = _array_sha256(mean)
    basis_sha256 = _array_sha256(components)
    payload = {
        "fit_work_ids": ordered_work_ids,
        "fit_reproduction_ids": ordered_reproduction_ids,
        "fit_source_ids": sorted(set(ordered_source_ids)),
        "input_dimension": protocol.raw_dimension,
        "component_count": component_count,
        "basis_shape": tuple(components.shape),
        "variance_target": protocol.pca_variance_target,
        "max_components": protocol.pca_max_components,
        "whiten": protocol.pca_whiten,
        "explained_variance_ratio": selected_ratios.tolist(),
        "cumulative_explained_variance": achieved,
        "variance_target_reached": bool(
            achieved + 10 * np.finfo(np.float64).eps >= protocol.pca_variance_target
        ),
        "mean_sha256": mean_sha256,
        "basis_sha256": basis_sha256,
    }
    evidence = PCABasisEvidence(**payload, state_sha256=stable_hash(payload))
    return FrozenPCA(
        mean=np.ascontiguousarray(mean),
        components=components,
        evidence=evidence,
    )


def transform_with_pca(matrix: np.ndarray, state: FrozenPCA) -> np.ndarray:
    values = _as_matrix(matrix, state.evidence.input_dimension)
    if state.mean.shape != (state.evidence.input_dimension,):
        raise ValueError("PCA mean does not match its recorded input dimension")
    if state.components.shape != state.evidence.basis_shape:
        raise ValueError("PCA basis does not match its recorded shape")
    return np.ascontiguousarray((values - state.mean) @ state.components.T)


def prepare_real_feature_rows(
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    features: Sequence[FeatureRow],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> PreparedLearnedFormalRows:
    """Join and validate the complete real-only learned-formal input graph."""

    protocol = protocol or LearnedFormalV2Protocol()
    if not canonical or not reproductions or not features:
        raise ValueError("learned-formal qualification requires non-empty real inputs")
    work_by_id = {row.canonical_work_id: row for row in canonical}
    if len(work_by_id) != len(canonical):
        raise ValueError("canonical work identifiers must be unique")
    if any(work.split not in {"train", "held_out"} for work in canonical):
        raise ValueError("every canonical work must have a frozen train or held-out split")

    reproduction_by_id = {row.reproduction_id: row for row in reproductions}
    if len(reproduction_by_id) != len(reproductions):
        raise ValueError("reproduction identifiers must be unique")
    for reproduction in reproductions:
        work = work_by_id.get(reproduction.canonical_work_id)
        if work is None:
            raise ValueError(
                f"reproduction {reproduction.reproduction_id} references an unknown work"
            )
        if reproduction.split != work.split:
            raise ValueError(
                f"reproduction {reproduction.reproduction_id} disagrees with canonical split"
            )

    feature_by_reproduction: Dict[str, FeatureRow] = {}
    feature_ids = set()
    derived_view_ids = set()
    identities = set()
    for feature in features:
        if feature.feature_id in feature_ids:
            raise ValueError("feature identifiers must be unique")
        if feature.derived_view_id in derived_view_ids:
            raise ValueError("derived-view identifiers must be unique")
        feature_ids.add(feature.feature_id)
        derived_view_ids.add(feature.derived_view_id)
        if feature.reproduction_id in feature_by_reproduction:
            raise ValueError("qualification requires exactly one feature per reproduction")
        reproduction = reproduction_by_id.get(feature.reproduction_id)
        if reproduction is None:
            raise ValueError(f"feature {feature.feature_id} references an unknown reproduction")
        work = work_by_id[reproduction.canonical_work_id]
        if feature.origin != "real" or feature.status != "ok":
            raise ValueError("qualification accepts only successful real FeatureRows")
        if feature.feature_name != protocol.feature_name:
            raise ValueError(f"unexpected learned-formal feature name: {feature.feature_name}")
        if feature.feature_version != protocol.feature_version:
            raise ValueError(
                f"unexpected learned-formal feature version: {feature.feature_version}"
            )
        if feature.canonical_work_id != reproduction.canonical_work_id:
            raise ValueError(f"feature {feature.feature_id} disagrees with reproduction work")
        if feature.split != work.split or reproduction.split != work.split:
            raise ValueError(f"feature {feature.feature_id} disagrees with canonical split")
        if feature.artist_id is None or feature.artist_id != work.artist_id:
            raise ValueError(f"feature {feature.feature_id} disagrees with canonical artist")
        vector = np.asarray(feature.vector, dtype=np.float64)
        if vector.shape != (protocol.raw_dimension,):
            raise ValueError(
                f"feature {feature.feature_id} must contain {protocol.raw_dimension} values"
            )
        if not np.isfinite(vector).all():
            raise ValueError(f"feature {feature.feature_id} contains non-finite values")
        if float(np.linalg.norm(vector)) <= np.finfo(np.float64).eps:
            raise ValueError(f"feature {feature.feature_id} is an all-zero latent")
        identities.add((feature.feature_name, feature.feature_version, feature.feature_config_hash))
        feature_by_reproduction[feature.reproduction_id] = feature
    if len(identities) != 1:
        raise ValueError("learned-formal rows must share one frozen feature identity")
    if set(feature_by_reproduction) != set(reproduction_by_id):
        missing = sorted(set(reproduction_by_id) - set(feature_by_reproduction))
        extra = sorted(set(feature_by_reproduction) - set(reproduction_by_id))
        raise ValueError(
            f"features and reproductions must match exactly; missing={missing}, extra={extra}"
        )
    extraction_metadata = validate_extraction_metadata(
        list(feature_by_reproduction.values()), reproduction_by_id, protocol
    )

    alternate_ids = set(protocol.alternate_source_ids)
    primary_reproductions = [row for row in reproductions if row.source_id not in alternate_ids]
    alternate_reproductions = [row for row in reproductions if row.source_id in alternate_ids]
    primary_by_work: Dict[str, ReproductionRecord] = {}
    for reproduction in primary_reproductions:
        if reproduction.canonical_work_id in primary_by_work:
            raise ValueError(
                "qualification requires exactly one primary reproduction for "
                f"{reproduction.canonical_work_id}"
            )
        primary_by_work[reproduction.canonical_work_id] = reproduction
    if set(primary_by_work) != set(work_by_id):
        missing = sorted(set(work_by_id) - set(primary_by_work))
        raise ValueError(f"canonical works without one primary reproduction: {missing}")
    if any(row.canonical_work_id not in primary_by_work for row in alternate_reproductions):
        raise ValueError("an alternate reproduction does not have a primary work")

    primary_rows = tuple(
        feature_by_reproduction[primary_by_work[work_id].reproduction_id]
        for work_id in sorted(work_by_id)
    )
    alternate_rows = tuple(
        feature_by_reproduction[row.reproduction_id]
        for row in sorted(alternate_reproductions, key=lambda item: item.reproduction_id)
    )
    return PreparedLearnedFormalRows(
        work_by_id=work_by_id,
        reproduction_by_id=reproduction_by_id,
        feature_by_reproduction=feature_by_reproduction,
        primary_rows=primary_rows,
        alternate_rows=alternate_rows,
        feature_config_hash=next(iter(identities))[2],
        extraction_metadata=extraction_metadata,
    )


def _balanced_accuracy(expected: Sequence[str], predicted: Sequence[str]) -> float:
    if not expected or len(expected) != len(predicted):
        raise ValueError("balanced accuracy requires equally sized, non-empty labels")
    recalls = []
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        recalls.append(sum(predicted[index] == label for index in indices) / len(indices))
    return float(np.mean(recalls))


def _classification(
    expected: Sequence[str], predicted: Sequence[str]
) -> LabelClassificationEvidence:
    if not expected or len(expected) != len(predicted):
        raise ValueError("classification labels must be equally sized and non-empty")
    recalls = {}
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        recalls[label] = float(sum(predicted[index] == label for index in indices) / len(indices))
    return LabelClassificationEvidence(
        expected_labels=list(expected),
        predicted_labels=list(predicted),
        per_class_recall=recalls,
        balanced_accuracy=_balanced_accuracy(expected, predicted),
    )


def _centroids(matrix: np.ndarray, labels: Sequence[str]) -> Dict[str, np.ndarray]:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != len(labels) or values.shape[0] == 0:
        raise ValueError("centroid labels do not match a non-empty feature matrix")
    label_array = np.asarray(labels)
    return {label: values[label_array == label].mean(axis=0) for label in sorted(set(labels))}


def _predict(matrix: np.ndarray, centroids: Mapping[str, np.ndarray]) -> List[str]:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or not centroids:
        raise ValueError("prediction requires a matrix and at least one centroid")
    labels = sorted(centroids)
    references = np.stack([centroids[label] for label in labels])
    distances = np.linalg.norm(values[:, None, :] - references[None, :, :], axis=2)
    return [labels[index] for index in np.argmin(distances, axis=1)]


def nested_leave_source_out_pca_artist_accuracy(
    matrix: np.ndarray,
    artist_ids: Sequence[str],
    source_ids: Sequence[str],
    work_ids: Sequence[str],
    reproduction_ids: Sequence[str],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> NestedSourceEvaluation:
    """Refit PCA and artist centroids inside each leave-source-out fold."""

    protocol = protocol or LearnedFormalV2Protocol()
    values = _as_matrix(matrix, protocol.raw_dimension)
    row_count = values.shape[0]
    if any(
        len(labels) != row_count for labels in (artist_ids, source_ids, work_ids, reproduction_ids)
    ):
        raise ValueError("nested-fold labels do not match the feature matrix")
    folds: List[NestedPCAFoldEvidence] = []
    pooled_expected: List[str] = []
    pooled_predicted: List[str] = []
    for held_source in sorted(set(source_ids)):
        fit_indices = [index for index, source in enumerate(source_ids) if source != held_source]
        test_indices = [index for index, source in enumerate(source_ids) if source == held_source]
        fit_artists = [artist_ids[index] for index in fit_indices]
        known_artists = sorted(set(fit_artists))
        known_set = set(known_artists)
        eligible_indices = [index for index in test_indices if artist_ids[index] in known_set]
        reason: Optional[str] = None
        pca: Optional[FrozenPCA] = None
        classification: Optional[LabelClassificationEvidence] = None
        if len(fit_indices) < 2:
            reason = "fewer than two independent fit works remain after holding out source"
        elif len(known_artists) < 2:
            reason = "fewer than two artist classes remain after holding out source"
        elif not eligible_indices:
            reason = "held source has no works from artists represented outside that source"
        elif len({artist_ids[index] for index in eligible_indices}) < 2:
            reason = "held source has fewer than two eligible artist classes"
        else:
            try:
                pca = fit_real_pca(
                    values[fit_indices],
                    [work_ids[index] for index in fit_indices],
                    [reproduction_ids[index] for index in fit_indices],
                    [source_ids[index] for index in fit_indices],
                    protocol,
                )
            except ValueError as exc:
                reason = str(exc)
            if pca is not None:
                fit_matrix = transform_with_pca(values[fit_indices], pca)
                test_matrix = transform_with_pca(values[eligible_indices], pca)
                expected = [artist_ids[index] for index in eligible_indices]
                predicted = _predict(test_matrix, _centroids(fit_matrix, fit_artists))
                classification = _classification(expected, predicted)
                pooled_expected.extend(expected)
                pooled_predicted.extend(predicted)
        folds.append(
            NestedPCAFoldEvidence(
                held_out_source_id=held_source,
                fit_source_ids=sorted({source_ids[index] for index in fit_indices}),
                fit_work_ids=sorted(work_ids[index] for index in fit_indices),
                test_work_ids=sorted(work_ids[index] for index in test_indices),
                eligible_test_work_ids=sorted(work_ids[index] for index in eligible_indices),
                known_artist_ids=known_artists,
                pca=pca.evidence if pca else None,
                classification=classification,
                supported=classification is not None,
                reason=reason,
            )
        )
    pooled = _classification(pooled_expected, pooled_predicted) if pooled_expected else None
    return NestedSourceEvaluation(
        folds=folds,
        pooled_classification=pooled,
        all_sources_supported=bool(folds) and all(fold.supported for fold in folds),
    )


def group_independent_alternate_distances(
    distances: Sequence[float],
    canonical_work_ids: Sequence[str],
    artist_ids: Sequence[str],
    reproduction_ids: Sequence[str],
) -> List[GroupedIndependentAlternateDistance]:
    """Collapse multiple alternate images to one median distance per real work."""

    count = len(distances)
    if any(len(labels) != count for labels in (canonical_work_ids, artist_ids, reproduction_ids)):
        raise ValueError("alternate-distance labels do not match the values")
    grouped: Dict[str, List[Tuple[float, str, str]]] = defaultdict(list)
    for distance, work_id, artist_id, reproduction_id in zip(
        distances, canonical_work_ids, artist_ids, reproduction_ids
    ):
        value = float(distance)
        if not np.isfinite(value) or value < 0:
            raise ValueError("alternate distances must be finite and non-negative")
        grouped[work_id].append((value, artist_id, reproduction_id))
    outputs = []
    for work_id, members in sorted(grouped.items()):
        artists = {artist for _, artist, _ in members}
        if len(artists) != 1:
            raise ValueError(f"alternate records disagree on artist for {work_id}")
        values = [value for value, _, _ in members]
        outputs.append(
            GroupedIndependentAlternateDistance(
                canonical_work_id=work_id,
                artist_id=next(iter(artists)),
                alternate_image_count=len(members),
                alternate_reproduction_ids=sorted(
                    reproduction_id for _, _, reproduction_id in members
                ),
                image_level_distances=values,
                independent_work_distance=float(np.median(values)),
            )
        )
    return outputs


def _stratified_resample(
    values: np.ndarray, artist_ids: Sequence[str], rng: np.random.Generator
) -> np.ndarray:
    labels = np.asarray(artist_ids)
    sampled = []
    for artist_id in sorted(set(artist_ids)):
        members = values[labels == artist_id]
        sampled.append(rng.choice(members, size=members.size, replace=True))
    return np.concatenate(sampled)


def bootstrap_distance_ratio(
    numerator: Sequence[float],
    numerator_artist_ids: Sequence[str],
    denominator: Sequence[float],
    denominator_artist_ids: Sequence[str],
    threshold: float,
    *,
    draws: int,
    confidence_level: float,
    random_seed: int,
) -> DistanceRatioEvidence:
    """Gate the artist-stratified median ratio by its percentile upper bound."""

    if len(numerator) != len(numerator_artist_ids):
        raise ValueError("numerator artist labels do not match reproduction distances")
    if len(denominator) != len(denominator_artist_ids):
        raise ValueError("denominator artist labels do not match within-artist distances")
    if draws < 100:
        raise ValueError("learned-formal bootstrap requires at least 100 draws")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("learned-formal bootstrap confidence level must be between zero and one")
    top = np.asarray(numerator, dtype=np.float64)
    bottom = np.asarray(denominator, dtype=np.float64)
    if top.size == 0 or bottom.size == 0:
        return DistanceRatioEvidence(
            metric="same_work_independent_reproduction_vs_within_artist",
            numerator_unit="canonical_work",
            numerator_count=int(top.size),
            denominator_count=int(bottom.size),
            confidence_level=confidence_level,
            bootstrap_draws=0,
            random_seed=random_seed,
            threshold=threshold,
            supported=False,
            reason="same-work and held-out within-artist distances are both required",
        )
    if not np.isfinite(top).all() or not np.isfinite(bottom).all():
        raise ValueError("learned-formal bootstrap distances must be finite")
    if np.any(top < 0) or np.any(bottom < 0):
        raise ValueError("learned-formal bootstrap distances must be non-negative")
    numerator_median = float(np.median(top))
    denominator_median = float(np.median(bottom))
    if denominator_median <= np.finfo(np.float64).eps:
        return DistanceRatioEvidence(
            metric="same_work_independent_reproduction_vs_within_artist",
            numerator_unit="canonical_work",
            numerator_count=int(top.size),
            denominator_count=int(bottom.size),
            numerator_median=numerator_median,
            denominator_median=denominator_median,
            confidence_level=confidence_level,
            bootstrap_draws=0,
            random_seed=random_seed,
            threshold=threshold,
            supported=False,
            reason="within-artist median is zero; the ratio is undefined",
        )
    ratio = numerator_median / denominator_median
    rng = np.random.default_rng(random_seed)
    ratios = np.empty(draws, dtype=np.float64)
    for draw in range(draws):
        top_draw = _stratified_resample(top, numerator_artist_ids, rng)
        bottom_draw = _stratified_resample(bottom, denominator_artist_ids, rng)
        draw_denominator = float(np.median(bottom_draw))
        ratios[draw] = (
            float(np.median(top_draw)) / draw_denominator
            if draw_denominator > np.finfo(np.float64).eps
            else np.inf
        )
    alpha = (1.0 - confidence_level) / 2.0
    lower = float(np.quantile(ratios, alpha))
    upper = float(np.quantile(ratios, 1.0 - alpha))
    finite_interval = np.isfinite(lower) and np.isfinite(upper)
    return DistanceRatioEvidence(
        metric="same_work_independent_reproduction_vs_within_artist",
        numerator_unit="canonical_work",
        numerator_count=int(top.size),
        denominator_count=int(bottom.size),
        numerator_median=numerator_median,
        denominator_median=denominator_median,
        point_ratio=ratio,
        confidence_level=confidence_level,
        confidence_lower=lower if finite_interval else None,
        confidence_upper=upper if finite_interval else None,
        bootstrap_draws=draws,
        random_seed=random_seed,
        threshold=threshold,
        supported=bool(finite_interval and upper <= threshold),
        reason=None if finite_interval else "bootstrap denominator reached zero",
    )


def _result_metadata_contract_verified(
    vector: np.ndarray,
    metadata: Mapping[str, object],
    protocol: LearnedFormalV2Protocol,
) -> bool:
    required = {
        "policy": protocol.expected_policy,
        "feature_version": protocol.feature_version,
        "representation_role": protocol.expected_representation_role,
        "seed_strategy": protocol.expected_seed_strategy,
        "base_seed": protocol.expected_base_seed,
        "input_size": [512, 512],
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": list(LATENT_SHAPE),
        "latent_scale": LATENT_SCALE,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": FLATTEN_ORDER,
        "vector_length": protocol.raw_dimension,
        "device": protocol.expected_device,
        "dtype": "float32",
        "source_input_role": protocol.expected_source_input_role,
        "source_preprocessing_policy": protocol.expected_source_preprocessing_policy,
        "opencv_version": protocol.expected_opencv_version,
        "opencv_build_sha256": protocol.expected_opencv_build_sha256,
        "pillow_version": protocol.expected_pillow_version,
        "source_repository": protocol.expected_source_repository,
        "source_revision": protocol.expected_source_revision,
        "model_repository": protocol.expected_model_repository,
        "model_revision": protocol.expected_model_revision,
        "config_sha256": protocol.expected_model_config_sha256,
        "weights_sha256": protocol.expected_model_weights_sha256,
        "artifacts_verified": True,
    }
    seed_basis = metadata.get("seed_basis_sha256")
    seed_is_derived = bool(
        _is_sha256(seed_basis)
        and metadata.get("seed")
        == _seed_from_basis_sha256(str(seed_basis), protocol.expected_base_seed)
    )
    source_hashes_valid = all(
        _is_sha256(metadata.get(key))
        for key in ("source_file_sha256", "intermediate_payload_sha256")
    )
    extension = metadata.get("source_extension")
    encoding_matches_extension = (
        extension in {".jpg", ".png", ".webp"}
        and metadata.get("intermediate_encoding") == str(extension).lstrip(".")
    )
    return bool(
        vector.shape == (protocol.raw_dimension,)
        and np.isfinite(vector).all()
        and all(metadata.get(key) == value for key, value in required.items())
        and seed_is_derived
        and source_hashes_valid
        and encoding_matches_extension
        and isinstance(metadata.get("source_checkout_verified"), bool)
        and metadata.get("vector_sha256") == learned_formal_vector_sha256(vector)
    )


def build_determinism_probe(
    reproduction_id: str,
    first: LearnedFormalResult,
    repeated: LearnedFormalResult,
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> LearnedFormalDeterminismProbe:
    """Summarize two independent extractions without retaining their large vectors."""

    protocol = protocol or LearnedFormalV2Protocol()
    first_vector = np.asarray(first.vector, dtype=np.float32)
    repeated_vector = np.asarray(repeated.vector, dtype=np.float32)
    first_metadata = dict(first.metadata)
    repeated_metadata = dict(repeated.metadata)
    metadata_exact = stable_hash(first_metadata) == stable_hash(repeated_metadata)
    contract_verified = _result_metadata_contract_verified(
        first_vector, first_metadata, protocol
    ) and _result_metadata_contract_verified(repeated_vector, repeated_metadata, protocol)
    return LearnedFormalDeterminismProbe(
        reproduction_id=reproduction_id,
        first_vector_sha256=learned_formal_vector_sha256(first_vector),
        repeated_vector_sha256=learned_formal_vector_sha256(repeated_vector),
        first_metadata_sha256=stable_hash(first_metadata),
        repeated_metadata_sha256=stable_hash(repeated_metadata),
        vector_exact_match=bool(np.array_equal(first_vector, repeated_vector)),
        metadata_exact_match=metadata_exact,
        contract_verified=contract_verified,
        policy=str(first_metadata.get("policy", "")),
        feature_version=str(first_metadata.get("feature_version", "")),
        seed=(int(first_metadata["seed"]) if isinstance(first_metadata.get("seed"), int) else None),
        seed_strategy=str(first_metadata.get("seed_strategy", "")),
        seed_basis_sha256=(
            str(first_metadata["seed_basis_sha256"])
            if first_metadata.get("seed_basis_sha256") is not None
            else None
        ),
        config_sha256=(
            str(first_metadata["config_sha256"])
            if first_metadata.get("config_sha256") is not None
            else None
        ),
        weights_sha256=(
            str(first_metadata["weights_sha256"])
            if first_metadata.get("weights_sha256") is not None
            else None
        ),
    )


def evaluate_source_behavior(
    prepared: PreparedLearnedFormalRows,
    probes: Sequence[LearnedFormalDeterminismProbe],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> SourceBehaviorEvidence:
    protocol = protocol or LearnedFormalV2Protocol()
    probe_by_reproduction = {probe.reproduction_id: probe for probe in probes}
    if len(probe_by_reproduction) != len(probes):
        raise ValueError("determinism probe reproduction identifiers must be unique")
    unknown = set(probe_by_reproduction) - set(prepared.feature_by_reproduction)
    if unknown:
        raise ValueError(f"determinism probes reference unknown reproductions: {sorted(unknown)}")
    exact_repeat_count = sum(probe.vector_exact_match for probe in probes)
    exact_metadata_count = sum(probe.metadata_exact_match for probe in probes)
    row_match_count = sum(
        probe.first_vector_sha256
        == learned_formal_vector_sha256(
            prepared.feature_by_reproduction[probe.reproduction_id].vector
        )
        for probe in probes
    )
    vector_contract_verified = all(
        len(row.vector) == protocol.raw_dimension
        and np.isfinite(np.asarray(row.vector, dtype=np.float64)).all()
        for row in prepared.feature_by_reproduction.values()
    )
    deterministic = bool(probes) and all(
        probe.vector_exact_match
        and probe.metadata_exact_match
        and probe.contract_verified
        and probe.policy == protocol.expected_policy
        and probe.feature_version == protocol.feature_version
        for probe in probes
    )
    recovered = vector_contract_verified and deterministic and row_match_count == len(probes)
    return SourceBehaviorEvidence(
        expected_policy=protocol.expected_policy,
        expected_feature_version=protocol.feature_version,
        vector_contract_verified=vector_contract_verified,
        determinism_probe_count=len(probes),
        exact_repeat_count=exact_repeat_count,
        exact_metadata_count=exact_metadata_count,
        feature_row_match_count=row_match_count,
        probe_reproduction_ids=sorted(probe_by_reproduction),
        deterministic_repeats_verified=deterministic,
        source_behavior_recovered=recovered,
        limitations=list(CONDITIONAL_LIMITATIONS),
    )


def _threshold_evidence(config: QualificationConfig) -> LearnedFormalThresholdEvidence:
    return LearnedFormalThresholdEvidence(
        artist_prediction_min_balanced_accuracy=(config.artist_prediction_min_balanced_accuracy),
        source_prediction_max_balanced_accuracy=(config.source_prediction_max_balanced_accuracy),
        leave_source_out_artist_min_balanced_accuracy=(
            config.leave_source_out_artist_min_balanced_accuracy
        ),
        reproduction_to_within_artist_median_ratio_max=(
            config.reproduction_to_within_artist_median_ratio_max
        ),
    )


def evaluate_source_domain_eligibility(
    primary_reproductions: Sequence[ReproductionRecord],
) -> SourceDomainEligibilityEvidence:
    """Evaluate the source repository's strict pre-resize inclusion filter.

    The released Kim et al. dataset code retains an image only when its native
    pixel area is strictly greater than ``410 * 410`` and its aspect ratio is
    strictly less than ``2``.  Missing dimensions cannot establish either
    condition and are therefore ineligible.
    """

    reproduction_ids = [row.reproduction_id for row in primary_reproductions]
    if len(set(reproduction_ids)) != len(reproduction_ids):
        raise ValueError("primary source-domain eligibility inputs must be unique")

    aspect_ratio_violations: List[str] = []
    native_area_violations: List[str] = []
    missing_dimensions: List[str] = []
    for reproduction in primary_reproductions:
        width = reproduction.native_width
        height = reproduction.native_height
        if width is None or height is None:
            missing_dimensions.append(reproduction.reproduction_id)
            continue
        if width * height <= SOURCE_MIN_NATIVE_AREA_EXCLUSIVE:
            native_area_violations.append(reproduction.reproduction_id)
        if max(width, height) / min(width, height) >= SOURCE_MAX_ASPECT_RATIO_EXCLUSIVE:
            aspect_ratio_violations.append(reproduction.reproduction_id)

    ineligible_ids = {
        *aspect_ratio_violations,
        *native_area_violations,
        *missing_dimensions,
    }
    return SourceDomainEligibilityEvidence(
        evaluated_primary_count=len(primary_reproductions),
        eligible_primary_count=len(primary_reproductions) - len(ineligible_ids),
        aspect_ratio_violation_count=len(aspect_ratio_violations),
        aspect_ratio_violating_reproduction_ids=sorted(aspect_ratio_violations),
        native_area_violation_count=len(native_area_violations),
        native_area_violating_reproduction_ids=sorted(native_area_violations),
        missing_dimension_count=len(missing_dimensions),
        missing_dimension_reproduction_ids=sorted(missing_dimensions),
        all_primary_inputs_eligible=not ineligible_ids,
    )


def evaluate_learned_formal_v2(
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    features: Sequence[FeatureRow],
    thresholds: QualificationConfig,
    artist_neighbors: Mapping[str, str],
    determinism_probes: Sequence[LearnedFormalDeterminismProbe],
    protocol: Optional[LearnedFormalV2Protocol] = None,
) -> LearnedFormalV2QualificationResult:
    """Run the frozen real-only qualification without loading the VAE."""

    protocol = protocol or LearnedFormalV2Protocol()
    if not artist_neighbors:
        raise ValueError("artist-neighbor relationships must be frozen before evaluation")
    if thresholds.require_bootstrap_upper_bound is not True:
        raise ValueError("learned-formal qualification requires a bootstrap upper-bound gate")
    if thresholds.bootstrap_draws is None or thresholds.confidence_level is None:
        raise ValueError("learned-formal qualification requires frozen bootstrap settings")
    prepared = prepare_real_feature_rows(canonical, reproductions, features, protocol)
    primary_rows = list(prepared.primary_rows)
    raw_primary = _as_matrix([row.vector for row in primary_rows], protocol.raw_dimension)
    primary_work_ids = [row.canonical_work_id for row in primary_rows]
    primary_reproduction_ids = [row.reproduction_id for row in primary_rows]
    primary_artists = [str(row.artist_id) for row in primary_rows]
    primary_sources = [
        prepared.reproduction_by_id[row.reproduction_id].source_id for row in primary_rows
    ]
    primary_splits = [prepared.work_by_id[row.canonical_work_id].split for row in primary_rows]
    source_domain_eligibility = evaluate_source_domain_eligibility(
        [prepared.reproduction_by_id[row.reproduction_id] for row in primary_rows]
    )

    artist_ids = sorted(set(primary_artists))
    source_ids = sorted(set(primary_sources))
    split_counts: Dict[str, Dict[str, int]] = {}
    missing_train_cells: List[str] = []
    missing_held_cells: List[str] = []
    for artist_id in artist_ids:
        for source_id in source_ids:
            key = f"{artist_id}|{source_id}"
            counts = {
                "train": sum(
                    artist == artist_id and source == source_id and split == "train"
                    for artist, source, split in zip(
                        primary_artists, primary_sources, primary_splits
                    )
                ),
                "held_out": sum(
                    artist == artist_id and source == source_id and split == "held_out"
                    for artist, source, split in zip(
                        primary_artists, primary_sources, primary_splits
                    )
                ),
            }
            split_counts[key] = counts
            if counts["train"] == 0:
                missing_train_cells.append(key)
            if counts["held_out"] == 0:
                missing_held_cells.append(key)
    joint_split = JointArtistSourceSplitEvidence(
        artist_ids=artist_ids,
        source_ids=source_ids,
        cell_counts=split_counts,
        missing_train_cells=missing_train_cells,
        missing_held_out_cells=missing_held_cells,
        complete_joint_coverage=not missing_train_cells and not missing_held_cells,
    )
    train_indices = [index for index, split in enumerate(primary_splits) if split == "train"]
    held_indices = [index for index, split in enumerate(primary_splits) if split == "held_out"]
    if len(train_indices) < 2 or not held_indices:
        raise ValueError("qualification requires at least two train works and held-out works")

    primary_pca = fit_real_pca(
        raw_primary[train_indices],
        [primary_work_ids[index] for index in train_indices],
        [primary_reproduction_ids[index] for index in train_indices],
        [primary_sources[index] for index in train_indices],
        protocol,
    )
    all_rows = list(features)
    all_projected = transform_with_pca(
        _as_matrix([row.vector for row in all_rows], protocol.raw_dimension), primary_pca
    )
    projected_by_reproduction = {
        row.reproduction_id: all_projected[index] for index, row in enumerate(all_rows)
    }
    projected_primary = np.stack(
        [projected_by_reproduction[row.reproduction_id] for row in primary_rows]
    )
    train_matrix = projected_primary[train_indices]
    held_matrix = projected_primary[held_indices]
    train_artists = [primary_artists[index] for index in train_indices]
    held_artists = [primary_artists[index] for index in held_indices]
    train_sources = [primary_sources[index] for index in train_indices]
    held_sources = [primary_sources[index] for index in held_indices]

    if len(set(train_artists)) < 2 or len(set(train_sources)) < 2:
        raise ValueError(
            "artist and source qualification each require at least two training classes"
        )
    if len(set(held_artists)) < 2 or len(set(held_sources)) < 2:
        raise ValueError(
            "artist and source qualification each require at least two held-out classes"
        )
    unknown_held_artists = sorted(set(held_artists) - set(train_artists))
    unknown_held_sources = sorted(set(held_sources) - set(train_sources))
    if unknown_held_artists:
        raise ValueError(f"held-out artists are absent from training: {unknown_held_artists}")
    if unknown_held_sources:
        raise ValueError(f"held-out sources are absent from training: {unknown_held_sources}")
    known_artists = set(primary_artists)
    if set(artist_neighbors) != known_artists:
        raise ValueError("frozen artist-neighbor keys must exactly match the qualified artists")
    unknown_neighbor_artists = set(artist_neighbors.values()) - known_artists
    if unknown_neighbor_artists:
        raise ValueError(
            f"frozen neighbors reference unknown artists: {sorted(unknown_neighbor_artists)}"
        )

    artist_predictions = _predict(held_matrix, _centroids(train_matrix, train_artists))
    source_predictions = _predict(held_matrix, _centroids(train_matrix, train_sources))
    artist_classification = _classification(held_artists, artist_predictions)
    source_classification = _classification(held_sources, source_predictions)
    nested = nested_leave_source_out_pca_artist_accuracy(
        raw_primary[train_indices],
        train_artists,
        train_sources,
        [primary_work_ids[index] for index in train_indices],
        [primary_reproduction_ids[index] for index in train_indices],
        protocol,
    )

    artist_centroids = _centroids(train_matrix, train_artists)
    within: List[WithinArtistDistance] = []
    for held_position, primary_index in enumerate(held_indices):
        artist_id = primary_artists[primary_index]
        if artist_id not in artist_centroids:
            continue
        within.append(
            WithinArtistDistance(
                canonical_work_id=primary_work_ids[primary_index],
                reproduction_id=primary_reproduction_ids[primary_index],
                artist_id=artist_id,
                distance=float(
                    np.linalg.norm(held_matrix[held_position] - artist_centroids[artist_id])
                ),
            )
        )
    within_values = [row.distance for row in within]
    within_median = float(np.median(within_values)) if within_values else None

    primary_by_work = {row.canonical_work_id: row for row in primary_rows}
    alternate_distances: List[float] = []
    alternate_work_ids: List[str] = []
    alternate_artists: List[str] = []
    alternate_reproduction_ids: List[str] = []
    for row in prepared.alternate_rows:
        primary = primary_by_work[row.canonical_work_id]
        alternate_distances.append(
            float(
                np.linalg.norm(
                    projected_by_reproduction[row.reproduction_id]
                    - projected_by_reproduction[primary.reproduction_id]
                )
            )
        )
        alternate_work_ids.append(row.canonical_work_id)
        alternate_artists.append(str(row.artist_id))
        alternate_reproduction_ids.append(row.reproduction_id)
    reproduction_groups = group_independent_alternate_distances(
        alternate_distances,
        alternate_work_ids,
        alternate_artists,
        alternate_reproduction_ids,
    )
    reproduction_ratio = bootstrap_distance_ratio(
        [group.independent_work_distance for group in reproduction_groups],
        [group.artist_id for group in reproduction_groups],
        within_values,
        [row.artist_id for row in within],
        thresholds.reproduction_to_within_artist_median_ratio_max,
        draws=thresholds.bootstrap_draws,
        confidence_level=thresholds.confidence_level,
        random_seed=thresholds.random_seed,
    )

    held_by_artist: Dict[str, List[np.ndarray]] = defaultdict(list)
    for held_position, primary_index in enumerate(held_indices):
        held_by_artist[primary_artists[primary_index]].append(held_matrix[held_position])
    neighbor_evidence: List[ArtistNeighborEnergyDistance] = []
    seen_pairs = set()
    for artist_id, neighbor_id in sorted(artist_neighbors.items()):
        if artist_id == neighbor_id:
            raise ValueError("an artist cannot be its own frozen neighbor")
        pair = tuple(sorted((artist_id, neighbor_id)))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        left = held_by_artist.get(pair[0], [])
        right = held_by_artist.get(pair[1], [])
        if len(left) < 2 or len(right) < 2:
            neighbor_evidence.append(
                ArtistNeighborEnergyDistance(
                    artist_id=pair[0],
                    neighbor_artist_id=pair[1],
                    artist_work_count=len(left),
                    neighbor_work_count=len(right),
                    supported=False,
                    reason="energy distance requires at least two held-out works per artist",
                )
            )
            continue
        distance = energy_distance(np.stack(left), np.stack(right))
        neighbor_evidence.append(
            ArtistNeighborEnergyDistance(
                artist_id=pair[0],
                neighbor_artist_id=pair[1],
                artist_work_count=len(left),
                neighbor_work_count=len(right),
                energy_distance=distance,
                supported=True,
            )
        )

    source_behavior = evaluate_source_behavior(prepared, determinism_probes, protocol)
    nested_classification = nested.pooled_classification
    artist_signal = (
        artist_classification.balanced_accuracy
        >= thresholds.artist_prediction_min_balanced_accuracy
        and bool(neighbor_evidence)
        and all(item.supported for item in neighbor_evidence)
    )
    source_controlled = (
        source_classification.balanced_accuracy
        <= thresholds.source_prediction_max_balanced_accuracy
        and nested_classification is not None
        and nested_classification.balanced_accuracy
        >= thresholds.leave_source_out_artist_min_balanced_accuracy
        and nested.all_sources_supported
        and joint_split.complete_joint_coverage
    )
    stable = source_behavior.deterministic_repeats_verified and reproduction_ratio.supported
    core_supported = (
        source_behavior.source_behavior_recovered
        and source_domain_eligibility.all_primary_inputs_eligible
        and primary_pca.evidence.variance_target_reached
        and stable
        and artist_signal
        and source_controlled
    )
    unsupported_conditions: List[str] = []
    if not source_behavior.source_behavior_recovered:
        unsupported_conditions.append("deterministic repaired-source behavior")
    if not source_domain_eligibility.all_primary_inputs_eligible:
        unsupported_conditions.append(
            "Kim et al. primary-input domain (known dimensions, native area > "
            "410*410, and aspect ratio < 2)"
        )
    if not primary_pca.evidence.variance_target_reached:
        unsupported_conditions.append("frozen 95% PCA variance target")
    if not reproduction_ratio.supported:
        unsupported_conditions.append("same-work reproduction stability")
    if not artist_signal:
        unsupported_conditions.append("held-out artist construct signal")
    if not source_controlled:
        unsupported_conditions.append(
            "museum-source confounding control with complete artist-by-source split coverage"
        )
    classification = ClassificationEvidence(
        held_out_artist=artist_classification,
        held_out_source=source_classification,
        nested_leave_source_out_artist=nested_classification,
        held_out_work_count=len(held_indices),
        nested_test_work_count=(
            len(nested_classification.expected_labels) if nested_classification else 0
        ),
    )
    threshold_evidence = _threshold_evidence(thresholds)
    conditional_limitations = list(CONDITIONAL_LIMITATIONS)
    if not primary_pca.evidence.variance_target_reached:
        conditional_limitations.append(
            "the 95% PCA variance selection target was bounded by the frozen "
            f"{protocol.pca_max_components}-component cap; the primary train-only basis "
            f"retains {primary_pca.evidence.cumulative_explained_variance:.6%} variance"
        )
    supported_scope = (
        [
            "real public-domain pilot works under the frozen museum-source graph",
            "Kim-style SD2 A-vectors with deterministic content-derived posterior sampling",
            "center-only PCA fitted on one primary real training reproduction per work",
        ]
        if core_supported
        else []
    )
    payload = {
        "status": "conditional_pass" if core_supported else "fail",
        "protocol": protocol.model_dump(mode="json"),
        "protocol_sha256": stable_hash(protocol.model_dump(mode="json")),
        "feature_config_sha256": prepared.feature_config_hash,
        "thresholds": threshold_evidence.model_dump(mode="json"),
        "source_domain_eligibility": source_domain_eligibility.model_dump(mode="json"),
        "joint_artist_source_split": joint_split.model_dump(mode="json"),
        "primary_pca": primary_pca.evidence.model_dump(mode="json"),
        "classification": classification.model_dump(mode="json"),
        "nested_source_evaluation": nested.model_dump(mode="json"),
        "within_artist_distances": [row.model_dump(mode="json") for row in within],
        "within_artist_median": within_median,
        "reproduction_groups": [row.model_dump(mode="json") for row in reproduction_groups],
        "reproduction_stability": reproduction_ratio.model_dump(mode="json"),
        "artist_neighbor_energy_distances": [
            row.model_dump(mode="json") for row in neighbor_evidence
        ],
        "extraction_metadata": prepared.extraction_metadata.model_dump(mode="json"),
        "source_behavior": source_behavior.model_dump(mode="json"),
        "source_behavior_recovered": source_behavior.source_behavior_recovered,
        "stable_within_frozen_margin": stable,
        "held_out_artist_signal_valid": artist_signal,
        "source_confounding_controlled": source_controlled,
        "primary_work_count": len(primary_rows),
        "train_work_count": len(train_indices),
        "held_out_work_count": len(held_indices),
        "alternate_image_count": len(prepared.alternate_rows),
        "independent_alternate_work_count": len(reproduction_groups),
        "supported_scope": supported_scope,
        "conditional_limitations": conditional_limitations,
        "unsupported_conditions": unsupported_conditions,
    }
    return LearnedFormalV2QualificationResult(
        **payload,
        result_sha256=stable_hash(payload),
    )
