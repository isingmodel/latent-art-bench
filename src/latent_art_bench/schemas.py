from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AllowedImageModel = Literal["gpt-image-1", "gpt-image-2"]
Split = Literal["train", "held_out", "unassigned"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class CanonicalWorkRecord(StrictModel):
    record_type: Literal["canonical_work"] = "canonical_work"
    schema_version: Literal["1.0"] = "1.0"
    canonical_work_id: str
    artist_id: str
    artist_name: str
    title: str
    creation_year: Optional[int] = None
    creation_year_text: Optional[str] = None
    movements: List[str] = Field(default_factory=list)
    genre: Optional[str] = None
    medium: Optional[str] = None
    support: Optional[str] = None
    dimensions_text: Optional[str] = None
    collection: Optional[str] = None
    catalog_ids: Dict[str, str] = Field(default_factory=dict)
    attribution_status: Literal["confirmed", "attributed", "workshop", "disputed", "unknown"]
    public_domain_status: Literal["confirmed", "candidate", "not_public_domain", "unknown"]
    rights_notes: Optional[str] = None
    split: Split = "unassigned"
    metadata_source_urls: List[str] = Field(default_factory=list)

    @field_validator("canonical_work_id", "artist_id", "artist_name", "title")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class ReproductionRecord(StrictModel):
    record_type: Literal["reproduction"] = "reproduction"
    schema_version: Literal["1.0"] = "1.0"
    reproduction_id: str
    canonical_work_id: str
    source_id: str
    source_url: Optional[str] = None
    local_path: str
    sha256: Optional[str] = None
    perceptual_hash: Optional[str] = None
    native_width: Optional[int] = Field(default=None, gt=0)
    native_height: Optional[int] = Field(default=None, gt=0)
    color_profile: Optional[str] = None
    border_status: Literal["none", "present", "uncertain", "not_reviewed"] = "not_reviewed"
    rights_status: Literal["verified", "restricted", "unknown"] = "unknown"
    rights_basis: Optional[str] = None
    rights_checked_at: Optional[datetime] = None
    acquisition_notes: Optional[str] = None
    split: Split = "unassigned"

    @field_validator("sha256")
    @classmethod
    def valid_sha256(cls, value: Optional[str]) -> Optional[str]:
        invalid = value is not None and (
            len(value) != 64 or any(c not in "0123456789abcdef" for c in value)
        )
        if invalid:
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        return value


class DerivedViewRecord(StrictModel):
    record_type: Literal["derived_view"] = "derived_view"
    schema_version: Literal["1.0"] = "1.0"
    derived_view_id: str
    reproduction_id: str
    canonical_work_id: str
    source_sha256: str
    output_path: str
    output_sha256: str
    preprocessing_track: str
    preprocessing_version: str
    preprocessing_config_hash: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    color_space: Literal["sRGB"] = "sRGB"
    alpha_background_rgb: List[int]
    border_policy: Literal["keep"] = "keep"
    upsampled: bool = False
    created_at: datetime

    @field_validator("alpha_background_rgb")
    @classmethod
    def valid_rgb(cls, value: List[int]) -> List[int]:
        if len(value) != 3 or any(channel < 0 or channel > 255 for channel in value):
            raise ValueError("alpha_background_rgb must contain three integers in [0, 255]")
        return value


class FeatureRow(StrictModel):
    record_type: Literal["feature"] = "feature"
    schema_version: Literal["1.0"] = "1.0"
    feature_id: str
    derived_view_id: str
    reproduction_id: str
    canonical_work_id: str
    artist_id: Optional[str] = None
    origin: Literal["real", "generated", "synthetic"] = "real"
    split: Split = "unassigned"
    model: Optional[AllowedImageModel] = None
    prompt_id: Optional[str] = None
    repetition: Optional[int] = Field(default=None, ge=0)
    feature_name: str
    feature_version: str
    feature_config_hash: str
    vector: List[float]
    scalars: Dict[str, float]
    status: Literal["ok", "degenerate", "failed"]
    failure_reason: Optional[str] = None


class PromptRecord(StrictModel):
    record_type: Literal["prompt"] = "prompt"
    schema_version: Literal["1.0"] = "1.0"
    prompt_id: str
    content_id: str
    template_id: str
    prompt: str
    target_artist_id: Optional[str] = None
    target_artist_name: Optional[str] = None
    artist_free_control: bool = False
    test_only: bool = False

    @model_validator(mode="after")
    def target_is_consistent(self) -> "PromptRecord":
        if self.artist_free_control and (self.target_artist_id or self.target_artist_name):
            raise ValueError("artist-free controls cannot declare a target artist")
        if not self.prompt.strip():
            raise ValueError("prompt must not be blank")
        return self


class GenerationCallRecord(StrictModel):
    record_type: Literal["generation_call"] = "generation_call"
    schema_version: Literal["1.0"] = "1.0"
    call_id: str
    run_id: str
    prompt_id: str
    model: AllowedImageModel
    endpoint: str
    requested_size: str
    requested_quality: str
    requested_output_format: str
    repetition: int = Field(ge=0)
    status: Literal["planned", "succeeded", "refused", "failed"]
    qualification_bypass: bool = False
    started_at: datetime
    completed_at: Optional[datetime] = None
    retry_count: int = Field(default=0, ge=0)
    output_path: Optional[str] = None
    output_sha256: Optional[str] = None
    actual_width: Optional[int] = Field(default=None, gt=0)
    actual_height: Optional[int] = Field(default=None, gt=0)
    actual_format: Optional[str] = None
    revised_prompt: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    failure_kind: Optional[str] = None
    failure_reason: Optional[str] = None


class QualificationEvidence(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    measurement: str
    feature_version: str
    feature_config_hash: str
    real_work_count: int = Field(ge=0)
    reproduction_pair_count: int = Field(ge=0)
    source_behavior_recovered: bool
    stable_within_frozen_margin: bool
    held_out_artist_signal_valid: bool
    source_confounding_controlled: bool
    conditional_domains: List[str] = Field(default_factory=list)
    evidence_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class QualificationCard(StrictModel):
    record_type: Literal["qualification_card"] = "qualification_card"
    schema_version: Literal["1.0"] = "1.0"
    measurement: str
    status: Literal["pending", "pass", "conditional_pass", "fail"]
    feature_version: str
    feature_config_hash: str
    source_behavior_recovered: Optional[bool] = None
    stable_within_frozen_margin: Optional[bool] = None
    held_out_artist_signal_valid: Optional[bool] = None
    source_confounding_controlled: Optional[bool] = None
    real_work_count: int = Field(default=0, ge=0)
    reproduction_pair_count: int = Field(default=0, ge=0)
    conditional_domains: List[str] = Field(default_factory=list)
    supported_scope: List[str] = Field(default_factory=list)
    evidence_paths: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    decided_at: Optional[datetime] = None


class RunRecord(StrictModel):
    record_type: Literal["run"] = "run"
    schema_version: Literal["1.0"] = "1.0"
    run_id: str
    command: str
    arguments: Dict[str, Any]
    status: Literal["running", "complete", "failed"]
    started_at: datetime
    completed_at: Optional[datetime] = None
    git_revision: Optional[str] = None
    git_dirty: Optional[bool] = None
    implementation_sha256: Optional[str] = None
    dependency_lock_path: Optional[str] = None
    dependency_lock_sha256: Optional[str] = None
    config_path: Optional[str] = None
    config_sha256: Optional[str] = None
    resolved_config: Optional[Dict[str, Any]] = None
    resolved_config_sha256: Optional[str] = None
    input_hashes: Dict[str, str] = Field(default_factory=dict)
    checkpoint_hashes: Dict[str, str] = Field(default_factory=dict)
    random_seeds: Dict[str, int] = Field(default_factory=dict)
    outputs: List[str] = Field(default_factory=list)
    failure_reasons: List[str] = Field(default_factory=list)


class AnalysisCell(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    cell_id: str
    target_artist_id: str
    model: AllowedImageModel
    feature_name: str
    target_train_vectors: List[List[float]]
    target_held_out_vectors: List[List[float]]
    generated_vectors: List[List[float]]
    neighbor_vectors: Dict[str, List[List[float]]]


class AnalysisResult(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    cell_id: str
    target_artist_id: str
    model: AllowedImageModel
    feature_name: str
    target_gap: float
    real_real_gap: float
    nearest_neighbor_id: str
    nearest_neighbor_gap: float
    target_neighbor_separation: float
    calibrated_target_gap: float
    calibrated_target_gap_interval: List[float]
    specificity_margin: float
    specificity_margin_interval: List[float]
    subsample_size: int = Field(ge=1)
    subsample_draws: int = Field(ge=1)
    confidence_level: float = Field(gt=0, lt=1)
    specificity_sign_convention: Literal["positive_means_target_closer"] = (
        "positive_means_target_closer"
    )
