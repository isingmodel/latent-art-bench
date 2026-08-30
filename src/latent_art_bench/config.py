from __future__ import annotations

import os
from pathlib import Path
from typing import List, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import AllowedImageModel


class StrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CorpusConfig(StrictConfig):
    roster_status: Literal["pending", "frozen"]
    candidate_artist_audit: str
    canonical_manifest: str
    reproduction_manifest: str
    common_genre: str
    target_works_per_artist: List[int]
    target_reproduction_pairs: List[int]


class PreprocessingConfig(StrictConfig):
    track: Literal["harmonized_chromatic_v1"]
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

    @field_validator("normalized_histogram_lower_edges")
    @classmethod
    def sorted_edges(cls, value: List[float]) -> List[float]:
        if not value or value[0] != 0 or any(b <= a for a, b in zip(value, value[1:])):
            raise ValueError("histogram lower edges must start at 0 and increase strictly")
        return value


class LearnedFormalConfig(StrictConfig):
    enabled: bool
    qualification_status: Literal["pending", "pass", "conditional_pass", "fail"]
    feature_version: str
    source_repository: str
    source_revision: str
    checkpoint: str
    input_size: List[int]
    latent_shape: List[int]
    flatten_order: Literal["C"]
    feasibility_report: str


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


class GenerationConfig(StrictConfig):
    mode: Literal["test_only"]
    scientific_claims_enabled: Literal[False]
    models: List[AllowedImageModel]
    base_url: str
    require_loopback: bool = True
    endpoint: Literal["images/generations"]
    prompt_manifest: str
    output_dir: str
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
    pilot_id: Literal["pilot_0"]
    purpose: Literal["api_integration_test_only"]
    corpus: CorpusConfig
    preprocessing: PreprocessingConfig
    measurements: MeasurementConfig
    qualification: QualificationConfig
    generation: GenerationConfig
    analysis: AnalysisConfig

    def content_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))

    def measurement_identities(self) -> dict:
        return {
            "chromatic": (
                self.measurements.chromatic.feature_version,
                stable_hash(self.measurements.chromatic.model_dump(mode="json")),
            ),
            "learned_formal": (
                self.measurements.learned_formal.feature_version,
                stable_hash(self.measurements.learned_formal.model_dump(mode="json")),
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
