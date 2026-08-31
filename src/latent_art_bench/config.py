from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import AllowedImageModel


class StrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ArtistConfig(StrictConfig):
    artist_id: str
    artist_name: str
    neighbor_artist_id: str
    movements: List[str]
    authority_ids: Dict[str, str]


class CorpusConfig(StrictConfig):
    roster_status: Literal["pending", "frozen"]
    candidate_artist_audit: str
    candidate_work_audit: str
    candidate_overrides: str
    canonical_manifest: str
    reproduction_manifest: str
    canonical_manifest_sha256: Optional[str] = None
    reproduction_manifest_sha256: Optional[str] = None
    common_genre: str
    target_works_per_artist: List[int]
    target_reproduction_pairs: List[int]
    selected_artists: List[ArtistConfig]
    museum_sources: List[Literal["aic", "cma", "met", "nga"]]
    aic_image_width: int = Field(ge=512, le=2048)
    image_long_side: int = Field(ge=512, le=2048)
    max_works_per_artist: int = Field(ge=1)
    split_seed: int
    held_out_fraction: float = Field(gt=0, lt=0.5)
    nga_open_data_revision: str
    met_open_data_revision: str
    met_open_data_sha256: str

    @model_validator(mode="after")
    def frozen_roster_is_complete(self) -> "CorpusConfig":
        artist_ids = [artist.artist_id for artist in self.selected_artists]
        if self.roster_status == "frozen" and len(artist_ids) != 4:
            raise ValueError("the frozen development roster must contain exactly four artists")
        if len(artist_ids) != len(set(artist_ids)):
            raise ValueError("selected artist identifiers must be unique")
        known = set(artist_ids)
        if any(artist.neighbor_artist_id not in known for artist in self.selected_artists):
            raise ValueError("every neighbor artist must be present in the frozen roster")
        if set(self.museum_sources) != {"aic", "cma", "met", "nga"}:
            raise ValueError("the corpus audit requires AIC, CMA, Met, and NGA sources")
        return self


class PreprocessingConfig(StrictConfig):
    track: Literal["harmonized_chromatic_v1", "harmonized_chromatic_v2"]
    version: str
    color_space: Literal["sRGB"]
    alpha_background_rgb: List[int]
    border_policy: Literal["keep"]
    resample: Literal["lanczos"]
    max_long_side: int = Field(gt=0)
    no_upsampling: Literal[True] = True
    output_format: Literal["png"] = "png"

    @field_validator("alpha_background_rgb")
    @classmethod
    def valid_rgb(cls, value: List[int]) -> List[int]:
        if len(value) != 3 or any(channel < 0 or channel > 255 for channel in value):
            raise ValueError("alpha_background_rgb must contain three integers in [0, 255]")
        return value


class ChromaticConfig(StrictConfig):
    enabled: bool
    feature_version: str
    source_doi: str
    adjacency: Literal["horizontal_and_vertical"]
    standard_deviation_ddof: Literal[0]
    degenerate_epsilon: float = Field(gt=0)
    normalized_histogram_lower_edges: List[float]
    vector_representation: Optional[
        Literal[
            "normalized_histogram",
            "seamlessness",
            "seamlessness_plus_hellinger",
        ]
    ] = None

    @field_validator("normalized_histogram_lower_edges")
    @classmethod
    def sorted_edges(cls, value: List[float]) -> List[float]:
        if not value or value[0] != 0 or any(b <= a for a, b in zip(value, value[1:])):
            raise ValueError("histogram lower edges must start at 0 and increase strictly")
        return value


class LearnedFormalConfig(StrictConfig):
    enabled: bool
    feature_version: str
    source_repository: str
    source_revision: str
    source_checkout_dir: Optional[str] = None
    checkpoint: str
    input_size: List[int]
    latent_shape: List[int]
    flatten_order: Literal["C"]
    feasibility_report: str
    model_repository: Optional[str] = None
    model_revision: Optional[str] = None
    model_snapshot_dir: Optional[str] = None
    model_config_sha256: Optional[str] = None
    model_weights_sha256: Optional[str] = None
    full_checkpoint_sha256: Optional[str] = None
    full_checkpoint_size_bytes: Optional[int] = Field(default=None, gt=0)
    model_verification_report: Optional[str] = None
    resize_library: Optional[Literal["opencv"]] = None
    resize_interpolation: Optional[Literal["INTER_LANCZOS4"]] = None
    opencv_version: Optional[str] = None
    opencv_build_sha256: Optional[str] = None
    pillow_version: Optional[str] = None
    jpeg_codec_version: Optional[str] = None
    python_version: Optional[str] = None
    platform_system: Optional[str] = None
    platform_release: Optional[str] = None
    platform_machine: Optional[str] = None
    numpy_version: Optional[str] = None
    torch_version: Optional[str] = None
    diffusers_version: Optional[str] = None
    torch_mps_built: Optional[bool] = None
    torch_mps_available: Optional[bool] = None
    input_color_order: Optional[Literal["RGB"]] = None
    input_tensor_range: Optional[List[float]] = None
    latent_scale: Optional[float] = Field(default=None, gt=0)
    sampling_policy: Optional[
        Literal["seeded_posterior_sample", "posterior_mode"]
    ] = None
    base_seed: Optional[int] = Field(default=None, ge=0, lt=2**63)
    seed_derivation: Optional[Literal["sha256_of_resized_rgb_plus_base_seed"]] = None
    device: Optional[Literal["auto", "cpu", "mps", "cuda"]] = None
    dtype: Optional[Literal["float32"]] = None
    pca_variance_target: Optional[float] = Field(default=None, gt=0, le=1)
    pca_max_components: Optional[int] = Field(default=None, ge=1)
    source_input_role: Optional[Literal["original_reproduction_file"]] = None
    source_preprocessing_policy: Optional[
        Literal["opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"]
    ] = None
    intermediate_encoding_policy: Optional[
        Literal["preserve_source_extension"]
    ] = None

    @model_validator(mode="after")
    def enabled_track_is_fully_pinned(self) -> "LearnedFormalConfig":
        if not self.enabled:
            return self
        required = {
            "model_repository": self.model_repository,
            "source_checkout_dir": self.source_checkout_dir,
            "model_revision": self.model_revision,
            "model_snapshot_dir": self.model_snapshot_dir,
            "model_config_sha256": self.model_config_sha256,
            "model_weights_sha256": self.model_weights_sha256,
            "full_checkpoint_sha256": self.full_checkpoint_sha256,
            "full_checkpoint_size_bytes": self.full_checkpoint_size_bytes,
            "model_verification_report": self.model_verification_report,
            "resize_library": self.resize_library,
            "resize_interpolation": self.resize_interpolation,
            "opencv_version": self.opencv_version,
            "opencv_build_sha256": self.opencv_build_sha256,
            "pillow_version": self.pillow_version,
            "jpeg_codec_version": self.jpeg_codec_version,
            "python_version": self.python_version,
            "platform_system": self.platform_system,
            "platform_release": self.platform_release,
            "platform_machine": self.platform_machine,
            "numpy_version": self.numpy_version,
            "torch_version": self.torch_version,
            "diffusers_version": self.diffusers_version,
            "torch_mps_built": self.torch_mps_built,
            "torch_mps_available": self.torch_mps_available,
            "input_color_order": self.input_color_order,
            "input_tensor_range": self.input_tensor_range,
            "latent_scale": self.latent_scale,
            "sampling_policy": self.sampling_policy,
            "base_seed": self.base_seed,
            "seed_derivation": self.seed_derivation,
            "device": self.device,
            "dtype": self.dtype,
            "pca_variance_target": self.pca_variance_target,
            "pca_max_components": self.pca_max_components,
            "source_input_role": self.source_input_role,
            "source_preprocessing_policy": self.source_preprocessing_policy,
            "intermediate_encoding_policy": self.intermediate_encoding_policy,
        }
        missing = sorted(name for name, value in required.items() if value is None)
        if missing:
            raise ValueError("enabled learned-formal track lacks pins: " + ", ".join(missing))
        if self.input_tensor_range != [-1.0, 1.0]:
            raise ValueError("learned-formal input_tensor_range must be [-1.0, 1.0]")
        if self.input_size != [512, 512] or self.latent_shape != [4, 64, 64]:
            raise ValueError("learned-formal SD2 contract requires 512 input and 4x64x64 latent")
        if self.opencv_build_sha256 is not None and (
            len(self.opencv_build_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.opencv_build_sha256)
        ):
            raise ValueError("opencv_build_sha256 must be a lowercase SHA-256")
        return self


class MeasurementConfig(StrictConfig):
    required: List[Literal["chromatic", "learned_formal"]]
    chromatic: ChromaticConfig
    learned_formal: LearnedFormalConfig

    @field_validator("required")
    @classmethod
    def both_measurements_are_required(cls, value: List[str]) -> List[str]:
        if set(value) != {"chromatic", "learned_formal"}:
            raise ValueError("pilot_0 requires chromatic and learned_formal measurements")
        return value


class QualificationConfig(StrictConfig):
    required_before_scientific_generation: bool
    cards: List[str]
    source_prediction_max_balanced_accuracy: float = Field(gt=0, le=1)
    artist_prediction_min_balanced_accuracy: float = Field(ge=0, lt=1)
    leave_source_out_artist_min_balanced_accuracy: float = Field(ge=0, lt=1)
    reproduction_to_within_artist_median_ratio_max: float = Field(gt=0)
    perturbation_to_within_artist_median_ratio_max: float = Field(gt=0)
    perturbation_long_side: int = Field(ge=128)
    perturbation_jpeg_quality: int = Field(ge=1, le=95)
    random_seed: int
    qualification_protocol_version: Optional[str] = None
    matched_input_long_side: Optional[int] = Field(default=None, ge=500)
    canonical_chromatic_long_side: Optional[int] = Field(default=None, ge=500)
    perturbation_jpeg_subsampling: Optional[Literal["4:2:0"]] = None
    bootstrap_draws: Optional[int] = Field(default=None, ge=100)
    confidence_level: Optional[float] = Field(default=None, gt=0, lt=1)
    require_bootstrap_upper_bound: Optional[bool] = None
    learned_determinism_probe_count: Optional[int] = Field(
        default=None, ge=1, le=12
    )


class GenerationConfig(StrictConfig):
    mode: Literal["test_only"]
    scientific_claims_enabled: Literal[False]
    models: List[AllowedImageModel]
    base_url: str
    require_loopback: bool = True
    endpoint: Literal["images/generations"]
    prompt_manifest: str
    output_dir: str
    manifest_attestation: Optional[str] = None
    repetitions: int = Field(ge=1)
    size: Literal["1024x1024", "1024x1536", "1536x1024", "auto"]
    quality: Literal["low", "medium", "high", "auto"]
    output_format: Literal["png", "jpeg", "webp"]
    timeout_seconds: float = Field(gt=0)
    max_retries: int = Field(ge=0, le=5)

    @model_validator(mode="after")
    def exactly_the_test_models(self) -> "GenerationConfig":
        if set(self.models) != {"gpt-image-1", "gpt-image-2"} or len(self.models) != 2:
            raise ValueError("test configuration must contain exactly gpt-image-1 and gpt-image-2")
        return self


class AnalysisConfig(StrictConfig):
    primary_distance: Literal["energy_distance"]
    calibrated_target_gap_formula: str
    specificity_formula: str
    specificity_sign_convention: Literal["positive_means_target_closer"]
    equal_sample_seed: int
    equal_sample_draws: int = Field(ge=1)
    confidence_level: float = Field(gt=0, lt=1)


class PilotConfig(StrictConfig):
    schema_version: Literal["1.0"]
    pilot_id: Literal["pilot_0", "pilot_1"]
    purpose: Literal["api_integration_test_only"]
    corpus: CorpusConfig
    preprocessing: PreprocessingConfig
    measurements: MeasurementConfig
    qualification: QualificationConfig
    generation: GenerationConfig
    analysis: AnalysisConfig

    @model_validator(mode="after")
    def pilot_1_contract_is_content_pinned(self) -> "PilotConfig":
        if self.pilot_id != "pilot_1":
            return self
        required_hashes = {
            "canonical_manifest_sha256": self.corpus.canonical_manifest_sha256,
            "reproduction_manifest_sha256": self.corpus.reproduction_manifest_sha256,
        }
        missing_hashes = sorted(
            name for name, value in required_hashes.items() if value is None
        )
        if missing_hashes:
            raise ValueError(
                "pilot_1 lacks corpus content pins: " + ", ".join(missing_hashes)
            )
        for name, value in required_hashes.items():
            assert value is not None
            if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
                raise ValueError(f"{name} must be a lowercase SHA-256")
        qualification_required = {
            "qualification_protocol_version": self.qualification.qualification_protocol_version,
            "matched_input_long_side": self.qualification.matched_input_long_side,
            "canonical_chromatic_long_side": (
                self.qualification.canonical_chromatic_long_side
            ),
            "perturbation_jpeg_subsampling": (
                self.qualification.perturbation_jpeg_subsampling
            ),
            "bootstrap_draws": self.qualification.bootstrap_draws,
            "confidence_level": self.qualification.confidence_level,
            "require_bootstrap_upper_bound": (
                self.qualification.require_bootstrap_upper_bound
            ),
            "learned_determinism_probe_count": (
                self.qualification.learned_determinism_probe_count
            ),
        }
        missing_qualification = sorted(
            name for name, value in qualification_required.items() if value is None
        )
        if missing_qualification:
            raise ValueError(
                "pilot_1 lacks qualification pins: "
                + ", ".join(missing_qualification)
            )
        if self.qualification.require_bootstrap_upper_bound is not True:
            raise ValueError("pilot_1 must gate stability bootstrap upper bounds")
        if self.measurements.learned_formal.device == "auto":
            raise ValueError("pilot_1 learned-formal device must be resolved, not auto")
        if self.generation.manifest_attestation is None:
            raise ValueError("pilot_1 requires a generation manifest attestation path")
        return self

    def content_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))

    def measurement_identities(self) -> dict:
        return {
            "chromatic": (
                self.measurements.chromatic.feature_version,
                stable_hash(
                    self.measurements.chromatic.model_dump(mode="json", exclude_none=True)
                ),
            ),
            "learned_formal": (
                self.measurements.learned_formal.feature_version,
                stable_hash(
                    self.measurements.learned_formal.model_dump(
                        mode="json", exclude_none=True
                    )
                ),
            ),
        }


def load_config(path: Path) -> PilotConfig:
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    config = PilotConfig.model_validate(raw)
    override = os.environ.get("LATENT_ART_IMAGE_BASE_URL")
    if override:
        config.generation.base_url = override
    return config
