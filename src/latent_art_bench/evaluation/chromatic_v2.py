"""Source-faithful, conditional qualification for Lee et al. chromatic seamlessness.

This module is deliberately separate from :mod:`real_only`.  The pilot-0 evaluator
is historical evidence; changing its perturbation graph would make that evidence
non-reproducible.  Version 2 instead records the complete branch graph and treats
Lee et al.'s scalar seamlessness statistic as the primary feature.  The normalized
histogram remains in the provenance as a diagnostic extension.  Qualification of
the cited empirical resolution behavior is separate: it compares every sample in
the mean-rescaled adjacent-pixel distance distributions and cannot be satisfied by
the scalar formula tests alone.
"""

from __future__ import annotations

import io
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Literal, NamedTuple, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageOps
from pydantic import Field, model_validator

from latent_art_bench.config import ChromaticConfig, PreprocessingConfig
from latent_art_bench.features.chromatic import adjacent_chromatic_distances, chromatic_summary
from latent_art_bench.io import hash_bytes, hash_file, stable_hash
from latent_art_bench.preprocessing.pipeline import PreprocessingError, _convert_to_srgb
from latent_art_bench.schemas import CanonicalWorkRecord, ReproductionRecord, StrictModel


class ChromaticV2Protocol(StrictModel):
    """Frozen protocol values; changing one requires a new protocol version."""

    protocol_version: Literal["lee2018-chromatic-qualification-v3"] = (
        "lee2018-chromatic-qualification-v3"
    )
    feature_version: Literal["lee2018-seamlessness-s-v2"] = "lee2018-seamlessness-s-v2"
    matched_input_long_side: Literal[1024] = 1024
    canonical_long_side: Literal[500] = 500
    direct_resolution_long_sides: Tuple[Literal[500], Literal[400], Literal[256]] = (
        500,
        400,
        256,
    )
    # Figure 1 of Lee et al. reports the collapse for 500--3000 px images.  The
    # frozen pilot corpus has no 3000 px primary file, so the executable v2 test
    # is explicitly an adapted, lower-resolution diagnostic rather than an
    # exact replication of that figure.
    paper_figure_resolution_long_sides: Tuple[
        Literal[500],
        Literal[1000],
        Literal[1500],
        Literal[2000],
        Literal[2500],
        Literal[3000],
    ] = (500, 1000, 1500, 2000, 2500, 3000)
    distribution_collapse_reference_long_side: Literal[500] = 500
    distribution_collapse_comparison_long_sides: Tuple[Literal[400], Literal[256]] = (400, 256)
    distribution_collapse_statistic: Literal["two_sample_ecdf_ks"] = "two_sample_ecdf_ks"
    distribution_collapse_ks_max: Literal[0.05] = 0.05
    distribution_collapse_aggregation: Literal["every_eligible_image_and_resolution_pair"] = (
        "every_eligible_image_and_resolution_pair"
    )
    distribution_collapse_registration: Literal[
        "frozen_before_first_full_distribution_evaluation"
    ] = "frozen_before_first_full_distribution_evaluation"
    jpeg_quality: Literal[85] = 85
    jpeg_subsampling: Literal[2] = 2
    sensitivity_jpeg_quality: Literal[95] = 95
    sensitivity_jpeg_subsampling: Literal[0] = 0
    perturbation_ratio_max: Literal[0.5] = 0.5
    reproduction_ratio_max: Literal[1.0] = 1.0
    artist_prediction_min_balanced_accuracy: float = Field(default=0.35, ge=0, le=1)
    source_prediction_max_balanced_accuracy: float = Field(default=0.55, ge=0, le=1)
    leave_source_out_artist_min_balanced_accuracy: float = Field(default=0.30, ge=0, le=1)
    bootstrap_draws: int = Field(default=2_000, ge=100)
    confidence_level: Literal[0.95] = 0.95
    random_seed: int = 20_260_830
    alternate_source_ids: Tuple[str, ...] = ("cma_alternate_capture",)

    @model_validator(mode="after")
    def frozen_resolution_order(self) -> "ChromaticV2Protocol":
        if self.direct_resolution_long_sides != (500, 400, 256):
            raise ValueError("v2 direct resolution branches are frozen at 500, 400, and 256")
        if self.paper_figure_resolution_long_sides != (
            500,
            1000,
            1500,
            2000,
            2500,
            3000,
        ):
            raise ValueError("Lee et al. Figure 1 resolution labels must remain exact")
        if self.distribution_collapse_reference_long_side != 500:
            raise ValueError("the distribution-collapse reference branch is frozen at 500")
        if self.distribution_collapse_comparison_long_sides != (400, 256):
            raise ValueError("the adapted distribution-collapse comparisons are 400 and 256")
        if not self.alternate_source_ids:
            raise ValueError("at least one alternate-reproduction source id is required")
        return self


class ChromaticVariantEvidence(StrictModel):
    condition: str
    branch_parent_pixel_sha256: str
    requested_long_side: int = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    exact_requested_resolution: bool
    pixel_sha256: str
    png_sha256: str
    primary_vector: List[float]
    diagnostic_histogram: List[float]
    scalars: Dict[str, float]
    mean_rescaling_defined: bool
    mean_rescaled_distribution_sha256: str
    feature_sha256: str


class ResolutionDistributionPairEvidence(StrictModel):
    """Full-sample comparison of two mean-rescaled distance distributions.

    Lee et al. define ``pi(d) = mean(d)^-1 F(d / mean(d))``.  Comparing the
    empirical CDFs of ``d / mean(d)`` therefore compares the complete rescaled
    distributions without reducing them to S or to the project's coarse
    diagnostic histogram.
    """

    statistic: Literal["two_sample_ecdf_ks"] = "two_sample_ecdf_ks"
    reference_long_side: int = Field(gt=0)
    comparison_long_side: int = Field(gt=0)
    reference_distance_count: int = Field(gt=0)
    comparison_distance_count: int = Field(gt=0)
    reference_mean_delta_e76: float = Field(ge=0)
    comparison_mean_delta_e76: float = Field(ge=0)
    reference_mean_rescaled_distribution_sha256: str
    comparison_mean_rescaled_distribution_sha256: str
    shared_source_parent_pixel_sha256: str
    independently_derived_from_shared_source: bool
    exact_requested_resolutions: bool
    ks_distance: Optional[float] = Field(default=None, ge=0, le=1)
    threshold: float = Field(gt=0, lt=1)
    supported: bool
    reason: Optional[str] = None


class ChromaticV2ImageProbe(StrictModel):
    protocol_version: str
    reproduction_id: str
    canonical_work_id: str
    source_id: str
    source_path: str
    expected_source_sha256: Optional[str]
    observed_source_sha256: str
    encoded_width: int = Field(gt=0)
    encoded_height: int = Field(gt=0)
    normalized_width: int = Field(gt=0)
    normalized_height: int = Field(gt=0)
    normalized_pixel_sha256: str
    normalized_png_sha256: str
    lossless_repeat_normalized_pixel_sha256: str
    lossless_repeat_canonical_pixel_sha256: str
    lossless_processing_deterministic: bool
    direct_resolution_branches: Dict[str, ChromaticVariantEvidence]
    resolution_distribution_pairs: List[ResolutionDistributionPairEvidence]
    adapted_full_distribution_collapse_supported: bool
    codec_probe_eligible: bool
    codec_ineligibility_reason: Optional[str] = None
    matched_input_width: Optional[int] = Field(default=None, gt=0)
    matched_input_height: Optional[int] = Field(default=None, gt=0)
    matched_input_parent_pixel_sha256: Optional[str] = None
    matched_input_pixel_sha256: Optional[str] = None
    matched_input_png_sha256: Optional[str] = None
    jpeg_quality: Optional[int] = None
    jpeg_subsampling: Optional[int] = None
    jpeg_payload_sha256: Optional[str] = None
    codec_lossless_control: Optional[ChromaticVariantEvidence] = None
    codec_q85_420_treatment: Optional[ChromaticVariantEvidence] = None
    sensitivity_jpeg_quality: Optional[int] = None
    sensitivity_jpeg_subsampling: Optional[int] = None
    sensitivity_jpeg_payload_sha256: Optional[str] = None
    codec_q95_444_sensitivity: Optional[ChromaticVariantEvidence] = None
    feature_config_sha256: str
    provenance_sha256: str

    @model_validator(mode="after")
    def internally_consistent_distribution_evidence(self) -> "ChromaticV2ImageProbe":
        if set(self.direct_resolution_branches) != {"500", "400", "256"}:
            raise ValueError("v2 requires exactly the 500, 400, and 256 direct branches")
        comparison_sides = [
            pair.comparison_long_side for pair in self.resolution_distribution_pairs
        ]
        if comparison_sides != [400, 256] or any(
            pair.reference_long_side != 500 for pair in self.resolution_distribution_pairs
        ):
            raise ValueError("v2 distribution evidence requires 500-vs-400 and 500-vs-256")
        for pair in self.resolution_distribution_pairs:
            reference = self.direct_resolution_branches[str(pair.reference_long_side)]
            comparison = self.direct_resolution_branches[str(pair.comparison_long_side)]
            if (
                pair.reference_mean_rescaled_distribution_sha256
                != reference.mean_rescaled_distribution_sha256
                or pair.comparison_mean_rescaled_distribution_sha256
                != comparison.mean_rescaled_distribution_sha256
            ):
                raise ValueError("distribution pair hashes do not bind to direct branches")
        expected_supported = bool(
            self.resolution_distribution_pairs
            and all(pair.supported for pair in self.resolution_distribution_pairs)
        )
        if self.adapted_full_distribution_collapse_supported != expected_supported:
            raise ValueError("image-level collapse decision disagrees with pair evidence")
        return self


class ArrayStandardizerEvidence(StrictModel):
    fit_work_ids: List[str]
    fit_source_ids: List[str]
    mean: List[float]
    scale: List[float]
    state_sha256: str


class NestedFoldEvidence(StrictModel):
    held_out_source_id: str
    fit_source_ids: List[str]
    fit_work_ids: List[str]
    test_work_ids: List[str]
    eligible_test_work_ids: List[str]
    known_artist_ids: List[str]
    standardizer: ArrayStandardizerEvidence
    expected_artist_ids: List[str]
    predicted_artist_ids: List[str]
    balanced_accuracy: Optional[float]


class NestedSourceEvaluation(StrictModel):
    folds: List[NestedFoldEvidence]
    expected_artist_ids: List[str]
    predicted_artist_ids: List[str]
    balanced_accuracy: Optional[float]


class GroupedReproductionDistance(StrictModel):
    canonical_work_id: str
    artist_id: str
    alternate_image_count: int = Field(gt=0)
    alternate_reproduction_ids: List[str]
    image_level_distances: List[float]
    independent_work_distance: float = Field(ge=0)


class BootstrapRatioEvidence(StrictModel):
    metric: str
    numerator_unit: str
    numerator_count: int = Field(ge=0)
    denominator_count: int = Field(ge=0)
    numerator_median: Optional[float] = None
    denominator_median: Optional[float] = None
    point_ratio: Optional[float] = None
    confidence_level: float = Field(gt=0, lt=1)
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    bootstrap_draws: int = Field(ge=0)
    threshold: float = Field(gt=0)
    supported: bool
    reason: Optional[str] = None


class ClassificationEvidence(StrictModel):
    held_out_artist_balanced_accuracy: Optional[float]
    held_out_artist_per_class_recall: Dict[str, float]
    held_out_source_balanced_accuracy: Optional[float]
    held_out_source_per_class_recall: Dict[str, float]
    nested_leave_source_out_artist_balanced_accuracy: Optional[float]
    every_nested_source_fold_meets_minimum: bool
    held_out_work_count: int = Field(ge=0)
    nested_test_work_count: int = Field(ge=0)


class ChromaticV2ScopeDecision(StrictModel):
    status: Literal["conditional_pass", "fail"]
    supported_scope: List[str]
    conditional_domains: List[str]
    unsupported_conditions: List[str]


class LeeInputEligibilityEvidence(StrictModel):
    """Eligibility against the exclusions stated in Lee et al.'s data section."""

    paper_excluded_conditions: List[str]
    represented_review_fields: List[str]
    missing_review_fields: List[str]
    primary_reproduction_count: int = Field(ge=0)
    painting_metadata_eligible_count: int = Field(ge=0)
    border_clear_count: int = Field(ge=0)
    border_ineligible_or_unreviewed_reproduction_ids: List[str]
    paper_domain_review_complete: bool
    supported: bool
    reason: str


class LeeResolutionCollapseEvidence(StrictModel):
    """Corpus-level evidence for Lee et al.'s empirical resolution behavior."""

    statistic: Literal["two_sample_ecdf_ks"] = "two_sample_ecdf_ks"
    threshold: float = Field(gt=0, lt=1)
    threshold_source: Literal["project_equivalence_margin_not_reported_by_lee2018"] = (
        "project_equivalence_margin_not_reported_by_lee2018"
    )
    registration_status: Literal["frozen_before_first_full_distribution_evaluation"] = (
        "frozen_before_first_full_distribution_evaluation"
    )
    prospective_to_corpus_collection: Literal[False] = False
    aggregation_rule: Literal["every_eligible_image_and_resolution_pair"] = (
        "every_eligible_image_and_resolution_pair"
    )
    paper_figure_resolution_long_sides: List[int]
    evaluated_resolution_long_sides: List[int]
    exact_paper_resolution_set: bool
    primary_native_supporting_paper_resolution_set_count: int = Field(ge=0)
    primary_image_count: int = Field(ge=0)
    raw_diagnostic_pass_count: int = Field(ge=0)
    raw_diagnostic_pass_fraction: float = Field(ge=0, le=1)
    raw_diagnostic_fail_reproduction_ids: List[str]
    raw_pair_count: int = Field(ge=0)
    raw_defined_ks_count: int = Field(ge=0)
    raw_ks_minimum: Optional[float] = Field(default=None, ge=0, le=1)
    raw_ks_median: Optional[float] = Field(default=None, ge=0, le=1)
    raw_ks_maximum: Optional[float] = Field(default=None, ge=0, le=1)
    paper_domain_eligible_image_count: int = Field(ge=0)
    eligible_pass_count: int = Field(ge=0)
    supported: bool
    reason: str


class ChromaticV2QualificationResult(StrictModel):
    record_type: Literal["chromatic_v2_qualification"] = "chromatic_v2_qualification"
    schema_version: Literal["2.0"] = "2.0"
    status: Literal["conditional_pass", "fail"]
    protocol: ChromaticV2Protocol
    protocol_sha256: str
    feature_config_sha256: str
    source_behavior_recovered: bool
    formula_behavior_verified: bool
    paper_resolution_collapse_status: Literal["supported", "failed", "ineligible"]
    source_behavior_recovery_reason: str
    source_behavior_metrics: Dict[str, float]
    lee_input_eligibility: LeeInputEligibilityEvidence
    paper_resolution_collapse: LeeResolutionCollapseEvidence
    lee_input_eligibility_verified: bool
    border_eligible_primary_count: int = Field(ge=0)
    border_ineligible_or_unreviewed_reproduction_ids: List[str]
    primary_standardizer: ArrayStandardizerEvidence
    classification: ClassificationEvidence
    nested_source_evaluation: NestedSourceEvaluation
    within_artist_held_out_distances: List[float]
    codec_stability: BootstrapRatioEvidence
    codec_sensitivity_q95_444: BootstrapRatioEvidence
    direct_resolution_stability: Dict[str, BootstrapRatioEvidence]
    reproduction_stability: BootstrapRatioEvidence
    reproduction_groups: List[GroupedReproductionDistance]
    primary_work_count: int = Field(ge=0)
    codec_eligible_work_count: int = Field(ge=0)
    lossless_deterministic_image_count: int = Field(ge=0)
    lossless_processing_deterministic: bool
    alternate_image_count: int = Field(ge=0)
    independent_alternate_work_count: int = Field(ge=0)
    supported_scope: List[str]
    conditional_domains: List[str]
    unsupported_conditions: List[str]
    probes: List[ChromaticV2ImageProbe]
    result_sha256: str


def _pixel_hash(image: Image.Image) -> str:
    rgb = image.convert("RGB")
    return stable_hash(
        {
            "mode": "RGB",
            "width": rgb.width,
            "height": rgb.height,
            "pixel_bytes_sha256": hash_bytes(rgb.tobytes()),
        }
    )


def _evidence_hash(payload: Dict[str, object]) -> str:
    """Hash nested evidence as JSON data, never as model repr strings."""

    def json_value(value: object) -> object:
        if isinstance(value, StrictModel):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return {str(key): json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [json_value(item) for item in value]
        return value

    return stable_hash(json_value(payload))


def _png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    rgb = image.convert("RGB")
    # Rebuild from pixels so source ICC/EXIF encoder metadata cannot leak into the
    # lossless evidence container.  Color normalization has already been recorded.
    metadata_free = Image.frombytes("RGB", rgb.size, rgb.tobytes())
    metadata_free.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _jpeg_bytes(image: Image.Image, quality: int, subsampling: int) -> bytes:
    """Encode only normalized pixels, excluding inherited source metadata."""

    rgb = image.convert("RGB")
    metadata_free = Image.frombytes("RGB", rgb.size, rgb.tobytes())
    output = io.BytesIO()
    metadata_free.save(
        output,
        format="JPEG",
        quality=quality,
        subsampling=subsampling,
        optimize=False,
        progressive=False,
    )
    return output.getvalue()


def _normalize_source(image: Image.Image, config: PreprocessingConfig) -> Image.Image:
    if config.border_policy != "keep":
        raise PreprocessingError("chromatic v2 requires the frozen 'keep' border policy")
    normalized = ImageOps.exif_transpose(image)
    normalized = _convert_to_srgb(normalized)
    if normalized.mode == "RGBA":
        background = Image.new("RGB", normalized.size, tuple(config.alpha_background_rgb))
        background.paste(normalized, mask=normalized.getchannel("A"))
        return background
    return normalized.convert("RGB")


def _direct_resize(image: Image.Image, long_side: int) -> Tuple[Image.Image, bool]:
    """Resize directly from ``image`` and never upsample."""

    longest = max(image.size)
    if longest < long_side:
        return image.copy(), False
    if longest == long_side:
        return image.copy(), True
    scale = long_side / float(longest)
    target = tuple(max(1, round(value * scale)) for value in image.size)
    return (
        image.resize(target, Image.Resampling.LANCZOS, reducing_gap=3.0),
        max(target) == long_side,
    )


class _VariantMeasurement(NamedTuple):
    evidence: ChromaticVariantEvidence
    mean_rescaled_distances: np.ndarray


def _sorted_mean_rescaled_distances(distances: np.ndarray) -> Tuple[np.ndarray, bool]:
    """Return the complete sorted ``d / mean(d)`` sample used by Lee et al.

    Sorting makes the evidence hash independent of horizontal/vertical
    concatenation order while retaining every adjacent-pixel observation.
    """

    values = np.asarray(distances, dtype=np.float64).reshape(-1)
    if values.size == 0 or not np.isfinite(values).all() or np.any(values < 0):
        raise ValueError("chromatic distances must be non-empty, finite, and non-negative")
    mean = float(values.mean())
    if mean <= np.finfo(np.float64).eps:
        return np.zeros_like(values), False
    return np.sort(values / mean, kind="mergesort"), True


def two_sample_ecdf_ks_distance(left: np.ndarray, right: np.ndarray) -> float:
    """Exact two-sample empirical-CDF K-S distance, including tied values.

    This is a descriptive equivalence statistic.  Pixel pairs are spatially
    dependent, so no iid K-S p-value is calculated or reported.
    """

    left_values = np.sort(np.asarray(left, dtype=np.float64).reshape(-1))
    right_values = np.sort(np.asarray(right, dtype=np.float64).reshape(-1))
    if left_values.size == 0 or right_values.size == 0:
        raise ValueError("K-S distance requires two non-empty samples")
    if not np.isfinite(left_values).all() or not np.isfinite(right_values).all():
        raise ValueError("K-S distance samples must be finite")

    # Evaluate both right-continuous ECDFs at every observed support value.  The
    # two passes avoid constructing a potentially much larger union array.
    left_at_left = np.searchsorted(left_values, left_values, side="right") / float(left_values.size)
    right_at_left = np.searchsorted(right_values, left_values, side="right") / float(
        right_values.size
    )
    left_at_right = np.searchsorted(left_values, right_values, side="right") / float(
        left_values.size
    )
    right_at_right = np.searchsorted(right_values, right_values, side="right") / float(
        right_values.size
    )
    return float(
        max(
            np.max(np.abs(left_at_left - right_at_left)),
            np.max(np.abs(left_at_right - right_at_right)),
        )
    )


def _variant(
    image: Image.Image,
    *,
    condition: str,
    parent_pixel_sha256: str,
    requested_long_side: int,
    exact_requested_resolution: bool,
    chromatic_config: ChromaticConfig,
) -> _VariantMeasurement:
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    distances = adjacent_chromatic_distances(rgb)
    summary = chromatic_summary(distances, chromatic_config)
    mean_rescaled, mean_rescaling_defined = _sorted_mean_rescaled_distances(distances)
    seamlessness = float(summary["scalars"]["seamlessness"])
    primary_vector = [float(value) for value in summary["vector"]]
    if len(primary_vector) != 1 or not np.isclose(
        primary_vector[0], seamlessness, rtol=0.0, atol=1e-15
    ):
        raise ValueError(
            "chromatic v2 requires vector_representation='seamlessness' so Lee et al.'s "
            "S is the sole primary feature"
        )
    histogram = [float(value) for value in summary["normalized_histogram"]]
    scalars = {key: float(value) for key, value in summary["scalars"].items()}
    distribution_sha256 = hash_bytes(np.ascontiguousarray(mean_rescaled, dtype="<f8").tobytes())
    feature_payload = {
        "feature_version": "lee2018-seamlessness-s-v2",
        "primary_vector": primary_vector,
        "diagnostic_histogram": histogram,
        "scalars": scalars,
        "mean_rescaling_defined": mean_rescaling_defined,
        "mean_rescaled_distribution_sha256": distribution_sha256,
    }
    evidence = ChromaticVariantEvidence(
        condition=condition,
        branch_parent_pixel_sha256=parent_pixel_sha256,
        requested_long_side=requested_long_side,
        width=image.width,
        height=image.height,
        exact_requested_resolution=exact_requested_resolution,
        pixel_sha256=_pixel_hash(image),
        png_sha256=hash_bytes(_png_bytes(image)),
        primary_vector=primary_vector,
        diagnostic_histogram=histogram,
        scalars=scalars,
        mean_rescaling_defined=mean_rescaling_defined,
        mean_rescaled_distribution_sha256=distribution_sha256,
        feature_sha256=stable_hash(feature_payload),
    )
    return _VariantMeasurement(evidence=evidence, mean_rescaled_distances=mean_rescaled)


def _resolution_distribution_pair(
    reference: _VariantMeasurement,
    comparison: _VariantMeasurement,
    protocol: ChromaticV2Protocol,
) -> ResolutionDistributionPairEvidence:
    reference_evidence = reference.evidence
    comparison_evidence = comparison.evidence
    shared_parent = reference_evidence.branch_parent_pixel_sha256
    independently_derived = (
        shared_parent == comparison_evidence.branch_parent_pixel_sha256
        and reference_evidence.condition.startswith("direct_native_to_")
        and comparison_evidence.condition.startswith("direct_native_to_")
    )
    exact = (
        reference_evidence.exact_requested_resolution
        and comparison_evidence.exact_requested_resolution
    )
    mean_defined = (
        reference_evidence.mean_rescaling_defined and comparison_evidence.mean_rescaling_defined
    )
    ks_distance: Optional[float] = None
    reason: Optional[str] = None
    if not independently_derived:
        reason = "resolution branches do not share the untouched normalized source parent"
    elif not exact:
        reason = "one or both branches did not reach the requested resolution"
    elif not mean_defined:
        reason = "mean chromatic distance is zero, so Lee et al. mean-rescaling is undefined"
    else:
        ks_distance = two_sample_ecdf_ks_distance(
            reference.mean_rescaled_distances,
            comparison.mean_rescaled_distances,
        )

    supported = bool(
        ks_distance is not None and ks_distance <= protocol.distribution_collapse_ks_max
    )
    return ResolutionDistributionPairEvidence(
        reference_long_side=reference_evidence.requested_long_side,
        comparison_long_side=comparison_evidence.requested_long_side,
        reference_distance_count=int(reference.mean_rescaled_distances.size),
        comparison_distance_count=int(comparison.mean_rescaled_distances.size),
        reference_mean_delta_e76=reference_evidence.scalars["mean_delta_e76"],
        comparison_mean_delta_e76=comparison_evidence.scalars["mean_delta_e76"],
        reference_mean_rescaled_distribution_sha256=(
            reference_evidence.mean_rescaled_distribution_sha256
        ),
        comparison_mean_rescaled_distribution_sha256=(
            comparison_evidence.mean_rescaled_distribution_sha256
        ),
        shared_source_parent_pixel_sha256=shared_parent,
        independently_derived_from_shared_source=independently_derived,
        exact_requested_resolutions=exact,
        ks_distance=ks_distance,
        threshold=protocol.distribution_collapse_ks_max,
        supported=supported,
        reason=reason,
    )


def build_chromatic_v2_probe(
    record: ReproductionRecord,
    chromatic_config: ChromaticConfig,
    preprocessing_config: PreprocessingConfig,
    root: Path,
    protocol: Optional[ChromaticV2Protocol] = None,
) -> ChromaticV2ImageProbe:
    """Build independent source branches and their complete in-memory provenance."""

    protocol = protocol or ChromaticV2Protocol()
    source_path = Path(record.local_path)
    if not source_path.is_absolute():
        source_path = root / source_path
    if not source_path.is_file():
        raise PreprocessingError(f"missing input for {record.reproduction_id}: {source_path}")
    observed_sha256 = hash_file(source_path)
    if record.sha256 and observed_sha256 != record.sha256:
        raise PreprocessingError(
            f"source hash mismatch for {record.reproduction_id}: expected {record.sha256}, "
            f"found {observed_sha256}"
        )

    try:
        with Image.open(source_path) as opened:
            encoded_width, encoded_height = opened.size
            opened.load()
            normalized = _normalize_source(opened, preprocessing_config)
    except PreprocessingError:
        raise
    except Exception as exc:
        raise PreprocessingError(f"cannot normalize {record.reproduction_id}: {exc}") from exc

    normalized_pixel_sha256 = _pixel_hash(normalized)
    normalized_png_sha256 = hash_bytes(_png_bytes(normalized))
    direct_measurements: Dict[str, _VariantMeasurement] = {}
    for long_side in protocol.direct_resolution_long_sides:
        # Each call receives the untouched normalized source, never another branch.
        resized, exact = _direct_resize(normalized, long_side)
        direct_measurements[str(long_side)] = _variant(
            resized,
            condition=f"direct_native_to_{long_side}_lossless",
            parent_pixel_sha256=normalized_pixel_sha256,
            requested_long_side=long_side,
            exact_requested_resolution=exact,
            chromatic_config=chromatic_config,
        )
    direct_branches = {
        long_side: measurement.evidence for long_side, measurement in direct_measurements.items()
    }
    collapse_reference = direct_measurements[
        str(protocol.distribution_collapse_reference_long_side)
    ]
    resolution_distribution_pairs = [
        _resolution_distribution_pair(
            collapse_reference,
            direct_measurements[str(long_side)],
            protocol,
        )
        for long_side in protocol.distribution_collapse_comparison_long_sides
    ]
    adapted_distribution_collapse_supported = bool(
        resolution_distribution_pairs
        and all(pair.supported for pair in resolution_distribution_pairs)
    )

    # Repeat the complete lossless source decode, EXIF/ICC normalization, and
    # canonical resize.  This is the determinism gate for the PNG scientific domain.
    try:
        with Image.open(source_path) as repeated_opened:
            repeated_opened.load()
            repeated_normalized = _normalize_source(repeated_opened, preprocessing_config)
    except PreprocessingError:
        raise
    except Exception as exc:
        raise PreprocessingError(
            f"cannot repeat lossless normalization for {record.reproduction_id}: {exc}"
        ) from exc
    repeated_canonical, _ = _direct_resize(repeated_normalized, protocol.canonical_long_side)
    repeat_normalized_pixel_sha256 = _pixel_hash(repeated_normalized)
    repeat_canonical_pixel_sha256 = _pixel_hash(repeated_canonical)
    lossless_deterministic = (
        repeat_normalized_pixel_sha256 == normalized_pixel_sha256
        and repeat_canonical_pixel_sha256
        == direct_branches[str(protocol.canonical_long_side)].pixel_sha256
    )

    codec_eligible = max(normalized.size) >= protocol.matched_input_long_side
    codec_reason: Optional[str] = None
    matched_input_width: Optional[int] = None
    matched_input_height: Optional[int] = None
    matched_input_pixel_sha256: Optional[str] = None
    matched_input_png_sha256: Optional[str] = None
    jpeg_payload_sha256: Optional[str] = None
    sensitivity_jpeg_payload_sha256: Optional[str] = None
    control: Optional[ChromaticVariantEvidence] = None
    treatment: Optional[ChromaticVariantEvidence] = None
    sensitivity: Optional[ChromaticVariantEvidence] = None

    if codec_eligible:
        matched, exact = _direct_resize(normalized, protocol.matched_input_long_side)
        if not exact:
            raise AssertionError("eligible matched-input branch did not reach 1024 pixels")
        matched_input_width, matched_input_height = matched.size
        matched_input_pixel_sha256 = _pixel_hash(matched)
        matched_input_png_sha256 = hash_bytes(_png_bytes(matched))

        jpeg_payload = _jpeg_bytes(matched, protocol.jpeg_quality, protocol.jpeg_subsampling)
        jpeg_payload_sha256 = hash_bytes(jpeg_payload)
        with Image.open(io.BytesIO(jpeg_payload)) as decoded:
            decoded.load()
            jpeg_decoded = _normalize_source(decoded, preprocessing_config)

        control_image, control_exact = _direct_resize(matched, protocol.canonical_long_side)
        treatment_image, treatment_exact = _direct_resize(
            jpeg_decoded, protocol.canonical_long_side
        )
        control = _variant(
            control_image,
            condition="matched_1024_lossless_then_500",
            parent_pixel_sha256=matched_input_pixel_sha256,
            requested_long_side=protocol.canonical_long_side,
            exact_requested_resolution=control_exact,
            chromatic_config=chromatic_config,
        ).evidence
        treatment = _variant(
            treatment_image,
            condition="matched_1024_q85_420_then_500",
            parent_pixel_sha256=matched_input_pixel_sha256,
            requested_long_side=protocol.canonical_long_side,
            exact_requested_resolution=treatment_exact,
            chromatic_config=chromatic_config,
        ).evidence

        sensitivity_payload = _jpeg_bytes(
            matched,
            protocol.sensitivity_jpeg_quality,
            protocol.sensitivity_jpeg_subsampling,
        )
        sensitivity_jpeg_payload_sha256 = hash_bytes(sensitivity_payload)
        with Image.open(io.BytesIO(sensitivity_payload)) as sensitivity_decoded:
            sensitivity_decoded.load()
            sensitivity_rgb = _normalize_source(sensitivity_decoded, preprocessing_config)
        sensitivity_image, sensitivity_exact = _direct_resize(
            sensitivity_rgb, protocol.canonical_long_side
        )
        sensitivity = _variant(
            sensitivity_image,
            condition="matched_1024_q95_444_then_500_sensitivity",
            parent_pixel_sha256=matched_input_pixel_sha256,
            requested_long_side=protocol.canonical_long_side,
            exact_requested_resolution=sensitivity_exact,
            chromatic_config=chromatic_config,
        ).evidence
    else:
        codec_reason = (
            f"normalized native long side {max(normalized.size)} is below the frozen "
            f"{protocol.matched_input_long_side}-pixel matched input; no upsampling allowed"
        )

    payload = {
        "protocol_version": protocol.protocol_version,
        "reproduction_id": record.reproduction_id,
        "canonical_work_id": record.canonical_work_id,
        "source_id": record.source_id,
        "source_path": record.local_path,
        "expected_source_sha256": record.sha256,
        "observed_source_sha256": observed_sha256,
        "encoded_width": encoded_width,
        "encoded_height": encoded_height,
        "normalized_width": normalized.width,
        "normalized_height": normalized.height,
        "normalized_pixel_sha256": normalized_pixel_sha256,
        "normalized_png_sha256": normalized_png_sha256,
        "lossless_repeat_normalized_pixel_sha256": repeat_normalized_pixel_sha256,
        "lossless_repeat_canonical_pixel_sha256": repeat_canonical_pixel_sha256,
        "lossless_processing_deterministic": lossless_deterministic,
        "direct_resolution_branches": direct_branches,
        "resolution_distribution_pairs": resolution_distribution_pairs,
        "adapted_full_distribution_collapse_supported": (adapted_distribution_collapse_supported),
        "codec_probe_eligible": codec_eligible,
        "codec_ineligibility_reason": codec_reason,
        "matched_input_width": matched_input_width,
        "matched_input_height": matched_input_height,
        "matched_input_parent_pixel_sha256": (normalized_pixel_sha256 if codec_eligible else None),
        "matched_input_pixel_sha256": matched_input_pixel_sha256,
        "matched_input_png_sha256": matched_input_png_sha256,
        "jpeg_quality": protocol.jpeg_quality if codec_eligible else None,
        "jpeg_subsampling": protocol.jpeg_subsampling if codec_eligible else None,
        "jpeg_payload_sha256": jpeg_payload_sha256,
        "codec_lossless_control": control,
        "codec_q85_420_treatment": treatment,
        "sensitivity_jpeg_quality": (protocol.sensitivity_jpeg_quality if codec_eligible else None),
        "sensitivity_jpeg_subsampling": (
            protocol.sensitivity_jpeg_subsampling if codec_eligible else None
        ),
        "sensitivity_jpeg_payload_sha256": sensitivity_jpeg_payload_sha256,
        "codec_q95_444_sensitivity": sensitivity,
        "feature_config_sha256": stable_hash(
            chromatic_config.model_dump(mode="json", exclude_none=True)
        ),
    }
    return ChromaticV2ImageProbe(**payload, provenance_sha256=_evidence_hash(payload))


def _as_matrix(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or values.shape[1] == 0:
        raise ValueError("features must form a non-empty two-dimensional matrix")
    if not np.isfinite(values).all():
        raise ValueError("features contain non-finite values")
    return values


def fit_array_standardizer(
    matrix: np.ndarray, work_ids: Sequence[str], source_ids: Sequence[str]
) -> ArrayStandardizerEvidence:
    values = _as_matrix(matrix)
    if values.shape[0] != len(work_ids) or values.shape[0] != len(source_ids):
        raise ValueError("standardizer labels do not match the feature matrix")
    if len(set(work_ids)) != len(work_ids):
        raise ValueError("standardizer fit requires one primary row per work")
    mean = values.mean(axis=0)
    scale = values.std(axis=0, ddof=0)
    scale = np.where(scale <= np.finfo(np.float64).eps, 1.0, scale)
    payload = {
        "fit_work_ids": sorted(work_ids),
        "fit_source_ids": sorted(set(source_ids)),
        "mean": mean.tolist(),
        "scale": scale.tolist(),
    }
    return ArrayStandardizerEvidence(**payload, state_sha256=stable_hash(payload))


def transform_with_standardizer(matrix: np.ndarray, state: ArrayStandardizerEvidence) -> np.ndarray:
    values = _as_matrix(matrix)
    mean = np.asarray(state.mean, dtype=np.float64)
    scale = np.asarray(state.scale, dtype=np.float64)
    if values.shape[1] != mean.size or mean.size != scale.size:
        raise ValueError("feature width does not match the fitted standardizer")
    return (values - mean) / scale


def _centroids(matrix: np.ndarray, labels: Sequence[str]) -> Dict[str, np.ndarray]:
    values = _as_matrix(matrix)
    if values.shape[0] != len(labels):
        raise ValueError("centroid labels do not match the feature matrix")
    label_array = np.asarray(labels)
    return {label: values[label_array == label].mean(axis=0) for label in sorted(set(labels))}


def _predict(matrix: np.ndarray, centroids: Dict[str, np.ndarray]) -> List[str]:
    values = _as_matrix(matrix)
    if not centroids:
        raise ValueError("at least one centroid is required")
    labels = sorted(centroids)
    references = np.stack([centroids[label] for label in labels])
    distances = np.linalg.norm(values[:, None, :] - references[None, :, :], axis=2)
    return [labels[index] for index in np.argmin(distances, axis=1)]


def _balanced_accuracy(expected: Sequence[str], predicted: Sequence[str]) -> float:
    if not expected or len(expected) != len(predicted):
        raise ValueError("balanced accuracy requires equally sized, non-empty labels")
    recalls = []
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        recalls.append(sum(predicted[index] == label for index in indices) / len(indices))
    return float(np.mean(recalls))


def _per_class_recall(expected: Sequence[str], predicted: Sequence[str]) -> Dict[str, float]:
    if not expected or len(expected) != len(predicted):
        raise ValueError("class recall requires equally sized, non-empty labels")
    output: Dict[str, float] = {}
    for label in sorted(set(expected)):
        indices = [index for index, value in enumerate(expected) if value == label]
        output[label] = float(sum(predicted[index] == label for index in indices) / len(indices))
    return output


def nested_leave_source_out_artist_accuracy(
    matrix: np.ndarray,
    artist_ids: Sequence[str],
    source_ids: Sequence[str],
    work_ids: Sequence[str],
) -> NestedSourceEvaluation:
    """Fit a fresh standardizer inside each held-source fold.

    The returned fit-source lists are auditable proof that the held source did not
    influence either standardization or centroids.
    """

    values = _as_matrix(matrix)
    row_count = values.shape[0]
    if any(len(labels) != row_count for labels in (artist_ids, source_ids, work_ids)):
        raise ValueError("nested-fold labels do not match the feature matrix")
    folds: List[NestedFoldEvidence] = []
    all_expected: List[str] = []
    all_predicted: List[str] = []
    for held_source in sorted(set(source_ids)):
        fit_indices = [index for index, source in enumerate(source_ids) if source != held_source]
        raw_test_indices = [
            index for index, source in enumerate(source_ids) if source == held_source
        ]
        if not fit_indices or not raw_test_indices:
            continue
        fit_artists = [artist_ids[index] for index in fit_indices]
        known_artists = sorted(set(fit_artists))
        test_indices = [
            index for index in raw_test_indices if artist_ids[index] in set(known_artists)
        ]
        state = fit_array_standardizer(
            values[fit_indices],
            [work_ids[index] for index in fit_indices],
            [source_ids[index] for index in fit_indices],
        )
        expected: List[str] = []
        predicted: List[str] = []
        if test_indices:
            fit_matrix = transform_with_standardizer(values[fit_indices], state)
            test_matrix = transform_with_standardizer(values[test_indices], state)
            expected = [artist_ids[index] for index in test_indices]
            predicted = _predict(test_matrix, _centroids(fit_matrix, fit_artists))
            all_expected.extend(expected)
            all_predicted.extend(predicted)
        folds.append(
            NestedFoldEvidence(
                held_out_source_id=held_source,
                fit_source_ids=sorted({source_ids[index] for index in fit_indices}),
                fit_work_ids=sorted(work_ids[index] for index in fit_indices),
                test_work_ids=sorted(work_ids[index] for index in raw_test_indices),
                eligible_test_work_ids=sorted(work_ids[index] for index in test_indices),
                known_artist_ids=known_artists,
                standardizer=state,
                expected_artist_ids=expected,
                predicted_artist_ids=predicted,
                balanced_accuracy=(_balanced_accuracy(expected, predicted) if expected else None),
            )
        )
    return NestedSourceEvaluation(
        folds=folds,
        expected_artist_ids=all_expected,
        predicted_artist_ids=all_predicted,
        balanced_accuracy=(
            _balanced_accuracy(all_expected, all_predicted) if all_expected else None
        ),
    )


def group_reproduction_alternates(
    distances: Sequence[float],
    canonical_work_ids: Sequence[str],
    artist_ids: Sequence[str],
    reproduction_ids: Sequence[str],
) -> List[GroupedReproductionDistance]:
    """Collapse alternate images to one independent sampling unit per artwork."""

    count = len(distances)
    if any(len(values) != count for values in (canonical_work_ids, artist_ids, reproduction_ids)):
        raise ValueError("alternate-reproduction labels do not match the distances")
    grouped: Dict[str, List[Tuple[float, str, str]]] = defaultdict(list)
    for distance, work_id, artist_id, reproduction_id in zip(
        distances, canonical_work_ids, artist_ids, reproduction_ids
    ):
        value = float(distance)
        if not np.isfinite(value) or value < 0:
            raise ValueError("reproduction distances must be finite and non-negative")
        grouped[work_id].append((value, artist_id, reproduction_id))
    outputs = []
    for work_id, values in sorted(grouped.items()):
        values = sorted(values, key=lambda item: item[2])
        artists = {artist for _, artist, _ in values}
        if len(artists) != 1:
            raise ValueError(f"alternate records disagree on artist for {work_id}")
        image_distances = [value for value, _, _ in values]
        outputs.append(
            GroupedReproductionDistance(
                canonical_work_id=work_id,
                artist_id=next(iter(artists)),
                alternate_image_count=len(values),
                alternate_reproduction_ids=sorted(
                    reproduction_id for _, _, reproduction_id in values
                ),
                image_level_distances=image_distances,
                independent_work_distance=float(np.median(image_distances)),
            )
        )
    return outputs


def _stratified_resample(
    values: np.ndarray, strata: Sequence[str], rng: np.random.Generator
) -> np.ndarray:
    sampled: List[np.ndarray] = []
    strata_array = np.asarray(strata)
    for label in sorted(set(strata)):
        members = values[strata_array == label]
        sampled.append(rng.choice(members, size=members.size, replace=True))
    return np.concatenate(sampled)


def stratified_bootstrap_ratio(
    numerator_values: Sequence[float],
    numerator_artist_ids: Sequence[str],
    denominator_values: Sequence[float],
    denominator_artist_ids: Sequence[str],
    *,
    metric: str,
    numerator_unit: str,
    threshold: float = 0.5,
    draws: int = 2_000,
    confidence_level: float = 0.95,
    seed: int = 2_026_083_000,
) -> BootstrapRatioEvidence:
    """Percentile interval for a median ratio, resampling within artist strata."""

    if len(numerator_values) != len(numerator_artist_ids):
        raise ValueError("numerator artist labels do not match values")
    if len(denominator_values) != len(denominator_artist_ids):
        raise ValueError("denominator artist labels do not match values")
    if draws < 100:
        raise ValueError("at least 100 bootstrap draws are required")
    if not 0 < confidence_level < 1 or threshold <= 0:
        raise ValueError("confidence level and threshold must be in their valid ranges")
    numerator = np.asarray(numerator_values, dtype=np.float64)
    denominator = np.asarray(denominator_values, dtype=np.float64)
    if numerator.size == 0 or denominator.size == 0:
        return BootstrapRatioEvidence(
            metric=metric,
            numerator_unit=numerator_unit,
            numerator_count=int(numerator.size),
            denominator_count=int(denominator.size),
            confidence_level=confidence_level,
            bootstrap_draws=0,
            threshold=threshold,
            supported=False,
            reason="both numerator and held-out within-artist denominator require data",
        )
    if not np.isfinite(numerator).all() or not np.isfinite(denominator).all():
        raise ValueError("bootstrap values must be finite")
    if np.any(numerator < 0) or np.any(denominator < 0):
        raise ValueError("bootstrap distances must be non-negative")
    numerator_median = float(np.median(numerator))
    denominator_median = float(np.median(denominator))
    if denominator_median <= np.finfo(np.float64).eps:
        return BootstrapRatioEvidence(
            metric=metric,
            numerator_unit=numerator_unit,
            numerator_count=int(numerator.size),
            denominator_count=int(denominator.size),
            numerator_median=numerator_median,
            denominator_median=denominator_median,
            confidence_level=confidence_level,
            bootstrap_draws=0,
            threshold=threshold,
            supported=False,
            reason="held-out within-artist median is zero; ratio is undefined",
        )

    rng = np.random.default_rng(seed)
    ratios = np.empty(draws, dtype=np.float64)
    for draw in range(draws):
        numerator_draw = _stratified_resample(numerator, numerator_artist_ids, rng)
        denominator_draw = _stratified_resample(denominator, denominator_artist_ids, rng)
        draw_denominator = float(np.median(denominator_draw))
        ratios[draw] = (
            float(np.median(numerator_draw)) / draw_denominator
            if draw_denominator > np.finfo(np.float64).eps
            else np.inf
        )
    alpha = (1.0 - confidence_level) / 2.0
    lower = float(np.quantile(ratios, alpha))
    upper = float(np.quantile(ratios, 1.0 - alpha))
    point_ratio = numerator_median / denominator_median
    return BootstrapRatioEvidence(
        metric=metric,
        numerator_unit=numerator_unit,
        numerator_count=int(numerator.size),
        denominator_count=int(denominator.size),
        numerator_median=numerator_median,
        denominator_median=denominator_median,
        point_ratio=point_ratio,
        confidence_level=confidence_level,
        confidence_lower=lower,
        confidence_upper=upper,
        bootstrap_draws=draws,
        threshold=threshold,
        supported=bool(np.isfinite(upper) and upper <= threshold),
        reason=None if np.isfinite(upper) else "bootstrap denominator reached zero",
    )


def _source_behavior(config: ChromaticConfig, seed: int) -> Tuple[bool, Dict[str, float]]:
    delta = chromatic_summary(np.full(1_000, 5.0), config)
    rng = np.random.default_rng(seed)
    exponential = chromatic_summary(rng.exponential(4.0, 200_000), config)
    heavy_tail = chromatic_summary(np.concatenate((np.zeros(999), [1_000.0])), config)
    scale_input = np.asarray([0.2, 0.5, 1.0, 2.5, 10.0])
    scale_a = chromatic_summary(scale_input, config)
    scale_b = chromatic_summary(scale_input * 37.0, config)
    metrics = {
        "delta_seamlessness": float(delta["scalars"]["seamlessness"]),
        "exponential_seamlessness": float(exponential["scalars"]["seamlessness"]),
        "heavy_tail_seamlessness": float(heavy_tail["scalars"]["seamlessness"]),
        "scale_invariance_abs": abs(
            float(scale_a["scalars"]["seamlessness"]) - float(scale_b["scalars"]["seamlessness"])
        ),
    }
    recovered = (
        abs(metrics["delta_seamlessness"] + 1.0) <= 1e-12
        and abs(metrics["exponential_seamlessness"]) <= 0.03
        and metrics["heavy_tail_seamlessness"] >= 0.9
        and metrics["scale_invariance_abs"] <= 1e-12
    )
    return recovered, metrics


def assess_lee_input_eligibility(
    canonical: Sequence[CanonicalWorkRecord],
    primary_records: Sequence[ReproductionRecord],
) -> LeeInputEligibilityEvidence:
    """Audit the corpus against the exclusions stated by Lee et al.

    The current records can establish that the catalogued objects are paintings
    and can carry a border review.  They cannot attest that a digital file is not
    a partial capture or that the depicted work is not seriously damaged.  That
    absence is recorded as an eligibility failure instead of being inferred from
    a successful decode or a museum source.
    """

    work_by_id = {work.canonical_work_id: work for work in canonical}
    painting_metadata_eligible = []
    for record in primary_records:
        work = work_by_id[record.canonical_work_id]
        medium = (work.medium or "").strip().lower()
        if medium and "photo" not in medium:
            painting_metadata_eligible.append(record.reproduction_id)

    border_problem_ids = sorted(
        record.reproduction_id for record in primary_records if record.border_status != "none"
    )
    border_clear_count = len(primary_records) - len(border_problem_ids)
    missing_review_fields = [
        "partial_image_status",
        "serious_damage_status",
    ]
    paper_domain_review_complete = not missing_review_fields
    supported = bool(
        primary_records
        and len(painting_metadata_eligible) == len(primary_records)
        and border_clear_count == len(primary_records)
        and paper_domain_review_complete
    )
    reasons: List[str] = []
    if len(painting_metadata_eligible) != len(primary_records):
        reasons.append("not every primary work has non-photographic painting metadata")
    if border_problem_ids:
        reasons.append("one or more primary files lack a clear border review")
    if missing_review_fields:
        reasons.append(
            "the manifest schema has no explicit review for partial captures or serious damage"
        )
    return LeeInputEligibilityEvidence(
        paper_excluded_conditions=[
            "partial image of a larger original",
            "non-rectangular frame",
            "seriously damaged image",
            "photograph or other non-painting input",
        ],
        represented_review_fields=[
            "ReproductionRecord.border_status",
            "CanonicalWorkRecord.medium",
        ],
        missing_review_fields=missing_review_fields,
        primary_reproduction_count=len(primary_records),
        painting_metadata_eligible_count=len(painting_metadata_eligible),
        border_clear_count=border_clear_count,
        border_ineligible_or_unreviewed_reproduction_ids=border_problem_ids,
        paper_domain_review_complete=paper_domain_review_complete,
        supported=supported,
        reason="; ".join(reasons) if reasons else "all Lee et al. input checks passed",
    )


def aggregate_lee_resolution_collapse(
    primary_probes: Sequence[ChromaticV2ImageProbe],
    primary_records: Sequence[ReproductionRecord],
    input_eligibility: LeeInputEligibilityEvidence,
    protocol: ChromaticV2Protocol,
) -> LeeResolutionCollapseEvidence:
    """Aggregate the preregistered full-distribution diagnostic by artwork.

    The raw adapted diagnostic remains visible even when the paper-domain gate is
    ineligible.  It is never promoted to an exact Figure 1 replication because
    the tested branch set differs and the paper gives no numerical K-S margin.
    """

    if not primary_probes or not primary_records:
        raise ValueError("resolution-collapse aggregation requires primary images")
    probe_ids = [probe.reproduction_id for probe in primary_probes]
    record_ids = [record.reproduction_id for record in primary_records]
    if len(set(probe_ids)) != len(probe_ids) or len(set(record_ids)) != len(record_ids):
        raise ValueError("resolution-collapse aggregation requires unique reproduction ids")
    if set(probe_ids) != set(record_ids):
        raise ValueError("resolution-collapse aggregation must cover exactly the primary corpus")

    raw_fail_ids = sorted(
        probe.reproduction_id
        for probe in primary_probes
        if not probe.adapted_full_distribution_collapse_supported
    )
    raw_pass_count = len(primary_probes) - len(raw_fail_ids)
    pair_evidence = [
        pair for probe in primary_probes for pair in probe.resolution_distribution_pairs
    ]
    ks_values = np.asarray(
        [pair.ks_distance for pair in pair_evidence if pair.ks_distance is not None],
        dtype=np.float64,
    )
    paper_long_sides = list(protocol.paper_figure_resolution_long_sides)
    evaluated_long_sides = [
        protocol.distribution_collapse_reference_long_side,
        *protocol.distribution_collapse_comparison_long_sides,
    ]
    exact_paper_resolution_set = evaluated_long_sides == paper_long_sides
    paper_max = max(paper_long_sides)
    native_support_count = sum(
        max(probe.normalized_width, probe.normalized_height) >= paper_max
        for probe in primary_probes
    )

    # Domain eligibility is an all-record gate in v2.  Selectively dropping files
    # after observing their K-S distances would make the maximum rule gameable.
    eligible_count = len(primary_probes) if input_eligibility.supported else 0
    eligible_pass_count = raw_pass_count if input_eligibility.supported else 0
    supported = bool(
        input_eligibility.supported
        and exact_paper_resolution_set
        and native_support_count == len(primary_records)
        and raw_pass_count == len(primary_probes)
    )
    reasons: List[str] = []
    if not input_eligibility.supported:
        reasons.append(f"paper-domain inputs are ineligible: {input_eligibility.reason}")
    if not exact_paper_resolution_set:
        reasons.append(
            "the adapted 500/400/256 branches do not reproduce Lee et al. Figure 1's "
            "500--3000 px branch set"
        )
    if native_support_count != len(primary_records):
        reasons.append(
            f"only {native_support_count}/{len(primary_records)} primary files support "
            f"the paper's {paper_max}px maximum without upsampling"
        )
    if raw_fail_ids:
        reasons.append(
            f"{len(raw_fail_ids)}/{len(primary_probes)} primary files exceed the "
            "project's full-distribution K-S equivalence margin on at least one branch"
        )
    return LeeResolutionCollapseEvidence(
        threshold=protocol.distribution_collapse_ks_max,
        paper_figure_resolution_long_sides=paper_long_sides,
        evaluated_resolution_long_sides=evaluated_long_sides,
        exact_paper_resolution_set=exact_paper_resolution_set,
        primary_native_supporting_paper_resolution_set_count=native_support_count,
        primary_image_count=len(primary_probes),
        raw_diagnostic_pass_count=raw_pass_count,
        raw_diagnostic_pass_fraction=raw_pass_count / len(primary_probes),
        raw_diagnostic_fail_reproduction_ids=raw_fail_ids,
        raw_pair_count=len(pair_evidence),
        raw_defined_ks_count=int(ks_values.size),
        raw_ks_minimum=float(ks_values.min()) if ks_values.size else None,
        raw_ks_median=float(np.median(ks_values)) if ks_values.size else None,
        raw_ks_maximum=float(ks_values.max()) if ks_values.size else None,
        paper_domain_eligible_image_count=eligible_count,
        eligible_pass_count=eligible_pass_count,
        supported=supported,
        reason="; ".join(reasons) if reasons else "all preregistered checks passed",
    )


def _vectors(probes: Sequence[ChromaticV2ImageProbe], long_side: int) -> np.ndarray:
    variants = [probe.direct_resolution_branches[str(long_side)] for probe in probes]
    if not all(variant.exact_requested_resolution for variant in variants):
        raise ValueError(f"not every source supports a direct {long_side}-pixel branch")
    return _as_matrix(np.asarray([variant.primary_vector for variant in variants]))


def _empty_ratio(
    metric: str,
    numerator_unit: str,
    denominator_count: int,
    threshold: float,
    confidence_level: float,
    reason: str,
) -> BootstrapRatioEvidence:
    return BootstrapRatioEvidence(
        metric=metric,
        numerator_unit=numerator_unit,
        numerator_count=0,
        denominator_count=denominator_count,
        confidence_level=confidence_level,
        bootstrap_draws=0,
        threshold=threshold,
        supported=False,
        reason=reason,
    )


def decide_chromatic_v2_scope(
    *,
    source_behavior_recovered: bool,
    artist_signal_valid: bool,
    source_confounding_controlled: bool,
    lossless_processing_deterministic: bool,
    codec_q85_diagnostic: BootstrapRatioEvidence,
    codec_q95_sensitivity: BootstrapRatioEvidence,
    reproduction_generalization: BootstrapRatioEvidence,
    direct_resolution_stability: Dict[str, BootstrapRatioEvidence],
) -> ChromaticV2ScopeDecision:
    """Qualify only the exact lossless digital corpus, keeping failed probes visible."""

    direct_400 = direct_resolution_stability.get("400")
    core_supported = (
        source_behavior_recovered
        and artist_signal_valid
        and source_confounding_controlled
        and lossless_processing_deterministic
        and direct_400 is not None
        and direct_400.supported
        and reproduction_generalization.supported
    )
    supported_scope: List[str] = []
    if core_supported:
        supported_scope.extend(
            [
                "Lee et al. scalar seamlessness S on independently normalized sRGB inputs",
                "direct native-to-500 lossless canonical chromatic views",
                "exact versioned primary digital reproductions only; no cross-digitization "
                "or physical-artwork inference",
            ]
        )
    for long_side, evidence in sorted(
        direct_resolution_stability.items(), key=lambda item: int(item[0]), reverse=True
    ):
        if evidence.supported:
            supported_scope.append(f"direct native-to-{long_side} lossless sensitivity views")
    if codec_q95_sensitivity.supported:
        supported_scope.append(
            "secondary Q95 4:4:4 sensitivity before 500-pixel canonicalization "
            "from matched 1024 inputs"
        )

    conditional_domains = [
        "the primary scientific domain is lossless PNG; Lee et al. make no JPEG claim",
        "codec sensitivities apply only to normalized sources with native long side >=1024",
        "same-work calibration applies only to represented alternate-capture sources",
        "classification checks are construct diagnostics, not artist-recognition claims",
        "resolution claims are reported separately for each independently derived branch",
    ]
    unsupported_conditions = [
        "JPEG recompression after scientific canonicalization was not qualified",
        "upsampling sources below a requested branch size was not qualified",
    ]
    if not source_behavior_recovered:
        unsupported_conditions.append(
            "Lee et al.'s real-image full normalized-distribution collapse across sizes"
        )
    if not artist_signal_valid:
        unsupported_conditions.append("held-out artist construct signal")
    if not source_confounding_controlled:
        unsupported_conditions.append("museum-source robustness in every held-source fold")
    if not codec_q85_diagnostic.supported:
        unsupported_conditions.append(
            "diagnostic matched 1024 Q85 4:2:0 codec perturbation; this does not "
            "veto the lossless PNG scientific domain"
        )
    if not codec_q95_sensitivity.supported:
        unsupported_conditions.append("secondary matched 1024 Q95 4:4:4 codec sensitivity")
    if not lossless_processing_deterministic:
        unsupported_conditions.append("exact repeated lossless preprocessing")
    if not reproduction_generalization.supported:
        unsupported_conditions.append(
            "same-work reproduction generalization beyond exact versioned primary files"
        )
    for long_side, evidence in sorted(direct_resolution_stability.items()):
        if not evidence.supported:
            unsupported_conditions.append(f"direct native-to-{long_side} resolution")

    return ChromaticV2ScopeDecision(
        status="conditional_pass" if core_supported else "fail",
        supported_scope=supported_scope,
        conditional_domains=conditional_domains,
        unsupported_conditions=unsupported_conditions,
    )


def evaluate_chromatic_v2(
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    chromatic_config: ChromaticConfig,
    preprocessing_config: PreprocessingConfig,
    root: Path,
    protocol: Optional[ChromaticV2Protocol] = None,
) -> ChromaticV2QualificationResult:
    """Evaluate the v2 protocol without mutating pilot-0 artifacts or configuration."""

    protocol = protocol or ChromaticV2Protocol()
    if not canonical or not reproductions:
        raise ValueError("chromatic v2 qualification requires a non-empty real corpus")
    work_by_id = {work.canonical_work_id: work for work in canonical}
    if len(work_by_id) != len(canonical):
        raise ValueError("canonical work identifiers must be unique")
    unknown_work_ids = {reproduction.canonical_work_id for reproduction in reproductions} - set(
        work_by_id
    )
    if unknown_work_ids:
        raise ValueError(f"reproductions reference unknown works: {sorted(unknown_work_ids)}")

    alternate_ids = set(protocol.alternate_source_ids)
    primary_records = [row for row in reproductions if row.source_id not in alternate_ids]
    alternate_records = [row for row in reproductions if row.source_id in alternate_ids]
    primary_by_work: Dict[str, ReproductionRecord] = {}
    for record in primary_records:
        if record.canonical_work_id in primary_by_work:
            raise ValueError(
                f"qualification requires one primary reproduction for {record.canonical_work_id}"
            )
        primary_by_work[record.canonical_work_id] = record
    if set(primary_by_work) != set(work_by_id):
        missing = sorted(set(work_by_id) - set(primary_by_work))
        raise ValueError(f"canonical works without exactly one primary reproduction: {missing}")

    all_probes = [
        build_chromatic_v2_probe(row, chromatic_config, preprocessing_config, root, protocol)
        for row in reproductions
    ]
    probe_by_reproduction = {probe.reproduction_id: probe for probe in all_probes}
    primary_probes = [
        probe_by_reproduction[primary_by_work[work_id].reproduction_id]
        for work_id in sorted(work_by_id)
    ]
    primary_work_ids = [probe.canonical_work_id for probe in primary_probes]
    primary_artists = [work_by_id[work_id].artist_id for work_id in primary_work_ids]
    primary_sources = [probe.source_id for probe in primary_probes]
    primary_splits = [work_by_id[work_id].split for work_id in primary_work_ids]
    baseline_matrix = _vectors(primary_probes, protocol.canonical_long_side)

    train_indices = [index for index, split in enumerate(primary_splits) if split == "train"]
    held_indices = [index for index, split in enumerate(primary_splits) if split == "held_out"]
    if not train_indices or not held_indices:
        raise ValueError("v2 qualification requires both train and held-out canonical works")
    state = fit_array_standardizer(
        baseline_matrix[train_indices],
        [primary_work_ids[index] for index in train_indices],
        [primary_sources[index] for index in train_indices],
    )
    transformed = transform_with_standardizer(baseline_matrix, state)
    train_matrix = transformed[train_indices]
    held_matrix = transformed[held_indices]
    train_artists = [primary_artists[index] for index in train_indices]
    held_artists = [primary_artists[index] for index in held_indices]
    train_sources = [primary_sources[index] for index in train_indices]
    held_sources = [primary_sources[index] for index in held_indices]

    artist_predictions = _predict(held_matrix, _centroids(train_matrix, train_artists))
    source_predictions = _predict(held_matrix, _centroids(train_matrix, train_sources))
    artist_accuracy = _balanced_accuracy(held_artists, artist_predictions)
    source_accuracy = _balanced_accuracy(held_sources, source_predictions)
    nested = nested_leave_source_out_artist_accuracy(
        baseline_matrix[train_indices],
        train_artists,
        train_sources,
        [primary_work_ids[index] for index in train_indices],
    )

    artist_centroids = _centroids(train_matrix, train_artists)
    within_distances: List[float] = []
    within_artists: List[str] = []
    for position, index in enumerate(held_indices):
        artist = primary_artists[index]
        if artist not in artist_centroids:
            continue
        within_distances.append(
            float(np.linalg.norm(held_matrix[position] - artist_centroids[artist]))
        )
        within_artists.append(artist)
    if not within_distances:
        raise ValueError("held-out works do not overlap artists represented in training")

    codec_distances: List[float] = []
    codec_artists: List[str] = []
    sensitivity_distances: List[float] = []
    sensitivity_artists: List[str] = []
    for probe, artist in zip(primary_probes, primary_artists):
        if not probe.codec_probe_eligible:
            continue
        assert probe.codec_lossless_control is not None
        assert probe.codec_q85_420_treatment is not None
        assert probe.codec_q95_444_sensitivity is not None
        pair = np.asarray(
            [
                probe.codec_lossless_control.primary_vector,
                probe.codec_q85_420_treatment.primary_vector,
            ],
            dtype=np.float64,
        )
        standardized_pair = transform_with_standardizer(pair, state)
        codec_distances.append(float(np.linalg.norm(standardized_pair[0] - standardized_pair[1])))
        codec_artists.append(artist)
        sensitivity_pair = np.asarray(
            [
                probe.codec_lossless_control.primary_vector,
                probe.codec_q95_444_sensitivity.primary_vector,
            ],
            dtype=np.float64,
        )
        standardized_sensitivity = transform_with_standardizer(sensitivity_pair, state)
        sensitivity_distances.append(
            float(np.linalg.norm(standardized_sensitivity[0] - standardized_sensitivity[1]))
        )
        sensitivity_artists.append(artist)
    codec_ratio = stratified_bootstrap_ratio(
        codec_distances,
        codec_artists,
        within_distances,
        within_artists,
        metric="matched_1024_q85_420_then_500_vs_lossless",
        numerator_unit="primary_work",
        threshold=protocol.perturbation_ratio_max,
        draws=protocol.bootstrap_draws,
        confidence_level=protocol.confidence_level,
        seed=protocol.random_seed,
    )
    sensitivity_ratio = stratified_bootstrap_ratio(
        sensitivity_distances,
        sensitivity_artists,
        within_distances,
        within_artists,
        metric="matched_1024_q95_444_then_500_vs_lossless_sensitivity",
        numerator_unit="primary_work",
        threshold=protocol.perturbation_ratio_max,
        draws=protocol.bootstrap_draws,
        confidence_level=protocol.confidence_level,
        seed=protocol.random_seed + 95,
    )

    resolution_ratios: Dict[str, BootstrapRatioEvidence] = {}
    for long_side in protocol.direct_resolution_long_sides[1:]:
        distances: List[float] = []
        artists: List[str] = []
        for baseline, probe, artist in zip(transformed, primary_probes, primary_artists):
            variant = probe.direct_resolution_branches[str(long_side)]
            if not variant.exact_requested_resolution:
                continue
            variant_transformed = transform_with_standardizer(
                np.asarray([variant.primary_vector], dtype=np.float64), state
            )[0]
            distances.append(float(np.linalg.norm(variant_transformed - baseline)))
            artists.append(artist)
        resolution_ratios[str(long_side)] = stratified_bootstrap_ratio(
            distances,
            artists,
            within_distances,
            within_artists,
            metric=f"direct_native_{long_side}_vs_500",
            numerator_unit="primary_work",
            threshold=protocol.perturbation_ratio_max,
            draws=protocol.bootstrap_draws,
            confidence_level=protocol.confidence_level,
            seed=protocol.random_seed + long_side,
        )

    alternate_distances: List[float] = []
    alternate_work_ids: List[str] = []
    alternate_artists: List[str] = []
    alternate_reproduction_ids: List[str] = []
    primary_index_by_work = {work_id: index for index, work_id in enumerate(primary_work_ids)}
    for record in alternate_records:
        probe = probe_by_reproduction[record.reproduction_id]
        variant = probe.direct_resolution_branches[str(protocol.canonical_long_side)]
        if not variant.exact_requested_resolution:
            continue
        alternate_vector = transform_with_standardizer(
            np.asarray([variant.primary_vector], dtype=np.float64), state
        )[0]
        primary_vector = transformed[primary_index_by_work[record.canonical_work_id]]
        alternate_distances.append(float(np.linalg.norm(alternate_vector - primary_vector)))
        alternate_work_ids.append(record.canonical_work_id)
        alternate_artists.append(work_by_id[record.canonical_work_id].artist_id)
        alternate_reproduction_ids.append(record.reproduction_id)
    reproduction_groups = group_reproduction_alternates(
        alternate_distances,
        alternate_work_ids,
        alternate_artists,
        alternate_reproduction_ids,
    )
    if reproduction_groups:
        reproduction_ratio = stratified_bootstrap_ratio(
            [group.independent_work_distance for group in reproduction_groups],
            [group.artist_id for group in reproduction_groups],
            within_distances,
            within_artists,
            metric="same_work_independent_reproduction_vs_primary",
            numerator_unit="canonical_work",
            threshold=protocol.reproduction_ratio_max,
            draws=protocol.bootstrap_draws,
            confidence_level=protocol.confidence_level,
            seed=protocol.random_seed + 1,
        )
    else:
        reproduction_ratio = _empty_ratio(
            "same_work_independent_reproduction_vs_primary",
            "canonical_work",
            len(within_distances),
            protocol.reproduction_ratio_max,
            protocol.confidence_level,
            "no exact 500-pixel alternate reproduction branches are available",
        )

    formula_behavior_verified, source_metrics = _source_behavior(
        chromatic_config, protocol.random_seed
    )
    input_eligibility = assess_lee_input_eligibility(canonical, primary_records)
    distribution_collapse = aggregate_lee_resolution_collapse(
        primary_probes,
        primary_records,
        input_eligibility,
        protocol,
    )
    source_behavior_recovered = bool(formula_behavior_verified and distribution_collapse.supported)
    paper_resolution_collapse_status: Literal["supported", "failed", "ineligible"]
    if distribution_collapse.supported:
        paper_resolution_collapse_status = "supported"
    elif (
        not input_eligibility.supported
        or not distribution_collapse.exact_paper_resolution_set
        or distribution_collapse.primary_native_supporting_paper_resolution_set_count
        != len(primary_records)
    ):
        paper_resolution_collapse_status = "ineligible"
    else:
        paper_resolution_collapse_status = "failed"
    source_behavior_recovery_reason = distribution_collapse.reason
    source_metrics.update(
        {
            "full_distribution_ks_threshold": (protocol.distribution_collapse_ks_max),
            "full_distribution_raw_pass_fraction": (
                distribution_collapse.raw_diagnostic_pass_fraction
            ),
            "full_distribution_paper_domain_eligible_count": float(
                distribution_collapse.paper_domain_eligible_image_count
            ),
            "full_distribution_exact_paper_resolution_set": float(
                distribution_collapse.exact_paper_resolution_set
            ),
        }
    )
    if distribution_collapse.raw_ks_maximum is not None:
        source_metrics["full_distribution_raw_ks_maximum"] = distribution_collapse.raw_ks_maximum
    border_problem_ids = input_eligibility.border_ineligible_or_unreviewed_reproduction_ids
    lee_input_eligibility_verified = input_eligibility.supported
    artist_signal = artist_accuracy >= protocol.artist_prediction_min_balanced_accuracy
    every_nested_fold_meets_minimum = bool(nested.folds) and all(
        fold.balanced_accuracy is not None
        and fold.balanced_accuracy >= protocol.leave_source_out_artist_min_balanced_accuracy
        for fold in nested.folds
    )
    source_controlled = (
        source_accuracy <= protocol.source_prediction_max_balanced_accuracy
        and nested.balanced_accuracy is not None
        and nested.balanced_accuracy >= protocol.leave_source_out_artist_min_balanced_accuracy
        and every_nested_fold_meets_minimum
    )
    deterministic_count = sum(probe.lossless_processing_deterministic for probe in all_probes)
    lossless_deterministic = deterministic_count == len(all_probes)
    scope = decide_chromatic_v2_scope(
        source_behavior_recovered=source_behavior_recovered,
        artist_signal_valid=artist_signal,
        source_confounding_controlled=source_controlled,
        lossless_processing_deterministic=lossless_deterministic,
        codec_q85_diagnostic=codec_ratio,
        codec_q95_sensitivity=sensitivity_ratio,
        reproduction_generalization=reproduction_ratio,
        direct_resolution_stability=resolution_ratios,
    )

    classification = ClassificationEvidence(
        held_out_artist_balanced_accuracy=artist_accuracy,
        held_out_artist_per_class_recall=_per_class_recall(held_artists, artist_predictions),
        held_out_source_balanced_accuracy=source_accuracy,
        held_out_source_per_class_recall=_per_class_recall(held_sources, source_predictions),
        nested_leave_source_out_artist_balanced_accuracy=nested.balanced_accuracy,
        every_nested_source_fold_meets_minimum=every_nested_fold_meets_minimum,
        held_out_work_count=len(held_indices),
        nested_test_work_count=len(nested.expected_artist_ids),
    )
    payload = {
        "status": scope.status,
        "protocol": protocol,
        "protocol_sha256": stable_hash(protocol.model_dump(mode="json")),
        "feature_config_sha256": stable_hash(
            chromatic_config.model_dump(mode="json", exclude_none=True)
        ),
        "source_behavior_recovered": source_behavior_recovered,
        "formula_behavior_verified": formula_behavior_verified,
        "paper_resolution_collapse_status": paper_resolution_collapse_status,
        "source_behavior_recovery_reason": source_behavior_recovery_reason,
        "source_behavior_metrics": source_metrics,
        "lee_input_eligibility": input_eligibility,
        "paper_resolution_collapse": distribution_collapse,
        "lee_input_eligibility_verified": lee_input_eligibility_verified,
        "border_eligible_primary_count": len(primary_records) - len(border_problem_ids),
        "border_ineligible_or_unreviewed_reproduction_ids": border_problem_ids,
        "primary_standardizer": state,
        "classification": classification,
        "nested_source_evaluation": nested,
        "within_artist_held_out_distances": within_distances,
        "codec_stability": codec_ratio,
        "codec_sensitivity_q95_444": sensitivity_ratio,
        "direct_resolution_stability": resolution_ratios,
        "reproduction_stability": reproduction_ratio,
        "reproduction_groups": reproduction_groups,
        "primary_work_count": len(primary_probes),
        "codec_eligible_work_count": len(codec_distances),
        "lossless_deterministic_image_count": deterministic_count,
        "lossless_processing_deterministic": lossless_deterministic,
        "alternate_image_count": len(alternate_distances),
        "independent_alternate_work_count": len(reproduction_groups),
        "supported_scope": scope.supported_scope,
        "conditional_domains": scope.conditional_domains,
        "unsupported_conditions": scope.unsupported_conditions,
        "probes": all_probes,
    }
    return ChromaticV2QualificationResult(**payload, result_sha256=_evidence_hash(payload))
