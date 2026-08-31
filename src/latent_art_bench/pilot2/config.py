"""Strict, prospective configuration for pilot_2.

Pilot 2 intentionally has its own schema.  Extending the pilot_1 schema would
change the code closure of the already completed pilot and make its evidence
stale.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import stable_hash

PILOT2_ARTISTS = (
    "alfred_sisley",
    "camille_pissarro",
    "claude_monet",
    "paul_cezanne",
)
PILOT2_SOURCES = ("aic", "nga")


class StrictPilot2Config(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _validate_optional_sha256(value: Optional[str]) -> Optional[str]:
    if value is not None and (
        len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("content pins must be lowercase SHA-256 values")
    return value


class Pilot2CorpusConfig(StrictPilot2Config):
    candidate_audit: str = "configs/pilot_0/candidate_work_audit.jsonl"
    selection_namespace: Literal["pilot2-v1|20260901"] = "pilot2-v1|20260901"
    artist_ids: List[str] = Field(default_factory=lambda: list(PILOT2_ARTISTS))
    source_ids: List[Literal["aic", "nga"]] = Field(
        default_factory=lambda: list(PILOT2_SOURCES)
    )
    works_per_artist_source: Literal[5] = 5
    train_per_artist_source: Literal[3] = 3
    held_out_per_artist_source: Literal[2] = 2
    atlas_manifest: str = "configs/pilot_2/manifests/atlas.jsonl"
    atlas_manifest_sha256: Optional[str] = None
    real_image_manifest: str = "configs/pilot_2/manifests/real_images.jsonl"
    real_image_manifest_sha256: Optional[str] = None

    _valid_atlas_hash = field_validator("atlas_manifest_sha256")(
        _validate_optional_sha256
    )
    _valid_real_image_hash = field_validator("real_image_manifest_sha256")(
        _validate_optional_sha256
    )

    @model_validator(mode="after")
    def exact_balanced_atlas(self) -> "Pilot2CorpusConfig":
        if tuple(sorted(self.artist_ids)) != PILOT2_ARTISTS:
            raise ValueError("pilot_2 requires the frozen four-artist roster")
        if len(self.artist_ids) != len(set(self.artist_ids)):
            raise ValueError("pilot_2 artist identifiers must be unique")
        if tuple(sorted(self.source_ids)) != PILOT2_SOURCES:
            raise ValueError("pilot_2 requires exactly the AIC and NGA source domains")
        if self.train_per_artist_source + self.held_out_per_artist_source != 5:
            raise ValueError("pilot_2 requires first three train and next two held out")
        return self


class Pilot2PreprocessingConfig(StrictPilot2Config):
    protocol_version: Literal["pilot2-common-lossless-png-v1"] = (
        "pilot2-common-lossless-png-v1"
    )
    color_space: Literal["sRGB"] = "sRGB"
    alpha_background_rgb: List[int] = Field(default_factory=lambda: [255, 255, 255])
    border_policy: Literal["keep"] = "keep"
    resample: Literal["lanczos"] = "lanczos"
    max_long_side: Literal[1024] = 1024
    no_upsampling: Literal[True] = True
    output_format: Literal["png"] = "png"

    @field_validator("alpha_background_rgb")
    @classmethod
    def valid_background(cls, value: List[int]) -> List[int]:
        if len(value) != 3 or any(
            type(channel) is not int or not 0 <= channel <= 255 for channel in value
        ):
            raise ValueError("alpha_background_rgb must be three integers in [0, 255]")
        return value


class Pilot2LearnedFormalConfig(StrictPilot2Config):
    protocol_version: Literal["pilot2-learned-primary-v2"] = "pilot2-learned-primary-v2"
    feature_version: Literal["kim2026-a-vector-harmonized-png-seeded-v1"] = (
        "kim2026-a-vector-harmonized-png-seeded-v1"
    )
    raw_dimension: int = Field(default=16_384, ge=2)
    latent_policy: Literal["seeded_posterior_sample"] = "seeded_posterior_sample"
    base_seed: Literal[20260901] = 20260901
    source_repository: Literal["https://github.com/aljinny/art-history"] = (
        "https://github.com/aljinny/art-history"
    )
    source_revision: Literal["7da12358cf34dad2184f357a048c2cf114b3c4e0"] = (
        "7da12358cf34dad2184f357a048c2cf114b3c4e0"
    )
    model_repository: Literal["Manojb/stable-diffusion-2-base"] = (
        "Manojb/stable-diffusion-2-base"
    )
    model_revision: Literal["64bf7b4f10eee35494b38d55c06c0c78cf8b44d0"] = (
        "64bf7b4f10eee35494b38d55c06c0c78cf8b44d0"
    )
    model_config_sha256: Literal[
        "6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0"
    ] = "6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0"
    model_weights_sha256: Literal[
        "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
    ] = "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
    model_snapshot_dir: str = "artifacts/models/sd2-base-vae"
    source_checkout_dir: str = "artifacts/sources/kim-art-history"
    full_checkpoint_sha256: Literal[
        "d635794c1fedfdfa261e065370bea59c651fc9bfa65dc6d67ad29e11869a1824"
    ] = "d635794c1fedfdfa261e065370bea59c651fc9bfa65dc6d67ad29e11869a1824"
    model_verification_report: str = (
        "reports/pilot_1/evidence/learned_formal_model_verification.json"
    )
    model_verification_report_sha256: Literal[
        "b847cc733c1b9b6f02246c0357b2f13841cb0f7dbf27d41c7bcf1cf6732bce27"
    ] = "b847cc733c1b9b6f02246c0357b2f13841cb0f7dbf27d41c7bcf1cf6732bce27"
    device: Literal["mps"] = "mps"
    opencv_version: Literal["4.14.0"] = "4.14.0"
    opencv_build_sha256: Literal[
        "c201b5ba726b7370afc3cb0d338454e2964afe1aa907849908b27850ecc043cf"
    ] = "c201b5ba726b7370afc3cb0d338454e2964afe1aa907849908b27850ecc043cf"
    pillow_version: Literal["11.3.0"] = "11.3.0"
    jpeg_codec_version: Literal["6.2"] = "6.2"
    python_version: Literal["3.13.11"] = "3.13.11"
    platform_system: Literal["Darwin"] = "Darwin"
    platform_release: Literal["25.6.0"] = "25.6.0"
    platform_machine: Literal["arm64"] = "arm64"
    numpy_version: Literal["2.5.2"] = "2.5.2"
    torch_version: Literal["2.13.0"] = "2.13.0"
    diffusers_version: Literal["0.40.0"] = "0.40.0"
    torch_mps_built: Literal[True] = True
    torch_mps_available: Literal[True] = True
    pca_variance_target: Literal[0.95] = 0.95
    pca_component_cap_rule: Literal["n_train_minus_1"] = "n_train_minus_1"
    pca_whiten: Literal[False] = False
    classifier: Literal["nearest_artist_centroid_euclidean"] = (
        "nearest_artist_centroid_euclidean"
    )
    pooled_held_artist_ba_strict_min: Literal[0.25] = 0.25
    pooled_classifier_held_by_source_artist_ba_strict_min: Literal[0.25] = 0.25
    permutation_scheme: Literal["artist_labels_within_source_by_split"] = (
        "artist_labels_within_source_by_split"
    )
    permutation_statistic: Literal["pooled_held_balanced_accuracy"] = (
        "pooled_held_balanced_accuracy"
    )
    permutation_draws: int = Field(default=9_999, ge=19)
    permutation_seed: int = Field(default=20260901, ge=0, lt=2**63)
    permutation_p_max: Literal[0.05] = 0.05


class Pilot2MeasurementConfig(StrictPilot2Config):
    primary: List[Literal["learned_formal"]] = Field(
        default_factory=lambda: ["learned_formal"]
    )
    secondary: List[Literal["chromatic"]] = Field(default_factory=lambda: ["chromatic"])

    @model_validator(mode="after")
    def sole_primary(self) -> "Pilot2MeasurementConfig":
        if self.primary != ["learned_formal"]:
            raise ValueError("learned_formal is the sole pilot_2 primary gate")
        if self.secondary != ["chromatic"]:
            raise ValueError("chromatic is a non-gating pilot_2 secondary measurement")
        return self


class Pilot2GenerationConfig(StrictPilot2Config):
    models: List[Literal["gpt-image-1", "gpt-image-2"]] = Field(
        default_factory=lambda: ["gpt-image-1", "gpt-image-2"]
    )
    base_url: Literal["http://127.0.0.1:10532/v1"] = "http://127.0.0.1:10532/v1"
    endpoint: Literal["images/generations"] = "images/generations"
    prompt_manifest: str = "configs/pilot_2/prompts.jsonl"
    prompt_manifest_sha256: Optional[str] = None
    generation_cells_manifest: str = "configs/pilot_2/generation_cells.jsonl"
    generation_cells_manifest_sha256: Optional[str] = None
    generation_schedule: str = "configs/pilot_2/generation_schedule.json"
    generation_schedule_sha256: Optional[str] = None
    runtime_revalidation_ledger: str = (
        "reports/pilot_2/evidence/generation_runtime_revalidations.jsonl"
    )
    post_intent_ledger: str = "artifacts/pilot_2/generation_post_intents.jsonl"
    attempt_receipt_manifest: str = (
        "reports/pilot_2/evidence/generation_attempt_receipts.json"
    )
    output_dir: str = "outputs/pilot_2/gpt_images"
    transport_fingerprint: str = (
        "reports/pilot_2/evidence/oauth_runtime_fingerprint.json"
    )
    transport_fingerprint_sha256: Optional[str] = None
    transport_source_snapshot: str = (
        "reports/pilot_2/evidence/oauth_source_snapshot.json"
    )
    transport_source_snapshot_sha256: Optional[str] = None
    content_block_count: Literal[8] = 8
    prompt_variants_per_block: Literal[5] = 5
    target_artist_prompts_per_block: Literal[4] = 4
    artist_free_prompts_per_block: Literal[1] = 1
    repetitions: Literal[4] = 4
    size: Literal["auto"] = "auto"
    quality: Literal["low"] = "low"
    output_format: Literal["png"] = "png"
    max_attempts_per_cell: Literal[10] = 10
    max_parallel: Literal[4] = 4
    schedule_namespace: Literal["pilot2-generation-order-v1"] = (
        "pilot2-generation-order-v1"
    )
    schedule_seed: Literal[20260901] = 20260901
    timeout_seconds: float = Field(default=300.0, gt=0)

    _valid_prompt_hash = field_validator("prompt_manifest_sha256")(
        _validate_optional_sha256
    )
    _valid_cells_hash = field_validator("generation_cells_manifest_sha256")(
        _validate_optional_sha256
    )
    _valid_schedule_hash = field_validator("generation_schedule_sha256")(
        _validate_optional_sha256
    )
    _valid_fingerprint_hash = field_validator("transport_fingerprint_sha256")(
        _validate_optional_sha256
    )
    _valid_snapshot_hash = field_validator("transport_source_snapshot_sha256")(
        _validate_optional_sha256
    )

    @model_validator(mode="after")
    def exact_generation_grid(self) -> "Pilot2GenerationConfig":
        if self.models != ["gpt-image-1", "gpt-image-2"]:
            raise ValueError("pilot_2 requires exactly gpt-image-1 and gpt-image-2 labels")
        if self.target_artist_prompts_per_block + self.artist_free_prompts_per_block != 5:
            raise ValueError("each pilot_2 content block requires four targets and one control")
        return self

    @property
    def logical_cell_count(self) -> int:
        return (
            self.content_block_count
            * self.prompt_variants_per_block
            * len(self.models)
            * self.repetitions
        )


class Pilot2AnalysisConfig(StrictPilot2Config):
    resampling_unit: Literal["content_block_then_repetition"] = (
        "content_block_then_repetition"
    )
    bootstrap_draws: Literal[10000] = 10_000
    confidence_level: Literal[0.95] = 0.95
    random_seed: Literal[20260901] = 20260901


class Pilot2DesignConfig(StrictPilot2Config):
    sensitivity_artifact: str = (
        "reports/pilot_2/evidence/sample_size_sensitivity.json"
    )
    sensitivity_artifact_sha256: Optional[str] = None
    design_version: Literal["pilot2-standardized-sign-flip-sensitivity-v1"] = (
        "pilot2-standardized-sign-flip-sensitivity-v1"
    )
    simulation_draws: Literal[100000] = 100_000
    simulation_seed: Literal[20260901] = 20260901
    standardized_effects: List[float] = Field(
        default_factory=lambda: [0.5, 0.75, 1.0, 1.25, 1.5]
    )
    top_level_block_count: Literal[8] = 8
    repetitions_per_block: Literal[4] = 4

    _valid_sensitivity_hash = field_validator("sensitivity_artifact_sha256")(
        _validate_optional_sha256
    )

    @field_validator("standardized_effects")
    @classmethod
    def exact_effect_grid(cls, value: List[float]) -> List[float]:
        if value != [0.5, 0.75, 1.0, 1.25, 1.5]:
            raise ValueError("pilot_2 requires the frozen standardized-effect grid")
        return value


class Pilot2QualificationArtifactConfig(StrictPilot2Config):
    learned_result: str = (
        "reports/pilot_2/evidence/learned_formal_qualification.json"
    )
    learned_card: str = "configs/pilot_2/qualification/learned_formal.json"


class Pilot2Config(StrictPilot2Config):
    schema_version: Literal["2.0"] = "2.0"
    pilot_id: Literal["pilot_2"] = "pilot_2"
    protocol_status: Literal["prospectively_frozen"] = "prospectively_frozen"
    protocol_document: str = "docs/PILOT_2_PROTOCOL.md"
    protocol_document_sha256: Optional[str] = None
    corpus: Pilot2CorpusConfig = Field(default_factory=Pilot2CorpusConfig)
    preprocessing: Pilot2PreprocessingConfig = Field(default_factory=Pilot2PreprocessingConfig)
    learned_formal: Pilot2LearnedFormalConfig = Field(
        default_factory=Pilot2LearnedFormalConfig
    )
    measurements: Pilot2MeasurementConfig = Field(default_factory=Pilot2MeasurementConfig)
    generation: Pilot2GenerationConfig = Field(default_factory=Pilot2GenerationConfig)
    analysis: Pilot2AnalysisConfig = Field(default_factory=Pilot2AnalysisConfig)
    design: Pilot2DesignConfig = Field(default_factory=Pilot2DesignConfig)
    qualification_artifacts: Pilot2QualificationArtifactConfig = Field(
        default_factory=Pilot2QualificationArtifactConfig
    )

    _valid_protocol_hash = field_validator("protocol_document_sha256")(
        _validate_optional_sha256
    )

    @model_validator(mode="after")
    def exact_320_cell_generation_design(self) -> "Pilot2Config":
        if self.generation.logical_cell_count != 320:
            raise ValueError("pilot_2 requires exactly 320 logical generation cells")
        return self

    def content_hash(self) -> str:
        return stable_hash(self.model_dump(mode="json"))


def load_pilot2_config(path: Path) -> Pilot2Config:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return Pilot2Config.model_validate(raw)
