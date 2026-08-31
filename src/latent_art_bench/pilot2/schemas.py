"""Persisted records emitted by the pilot_2 core."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import stable_hash

Pilot2Source = Literal["aic", "nga"]
Pilot2Split = Literal["train", "held_out"]


class StrictPilot2Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


class Pilot2AtlasWork(StrictPilot2Model):
    record_type: Literal["pilot2_atlas_work"] = "pilot2_atlas_work"
    schema_version: Literal["2.0"] = "2.0"
    canonical_work_id: str
    artist_id: str
    artist_name: str
    source_id: Pilot2Source
    source_object_id: str
    title: str
    image_url: str
    source_url: str
    native_width: int = Field(gt=0)
    native_height: int = Field(gt=0)
    split: Pilot2Split
    selection_rank: int = Field(ge=1, le=5)
    selection_digest: str
    selection_namespace: Literal["pilot2-v1|20260901"] = "pilot2-v1|20260901"

    @field_validator(
        "canonical_work_id",
        "artist_id",
        "artist_name",
        "source_object_id",
        "title",
        "image_url",
        "source_url",
    )
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("atlas fields must not be blank")
        return value

    @field_validator("selection_digest")
    @classmethod
    def digest_is_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("selection_digest must be a lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def native_kim_domain_is_eligible(self) -> "Pilot2AtlasWork":
        if self.native_width * self.native_height <= 410 * 410:
            raise ValueError("pilot_2 native image area must be strictly greater than 410^2")
        ratio = max(self.native_width, self.native_height) / min(
            self.native_width, self.native_height
        )
        if ratio >= 2.0:
            raise ValueError("pilot_2 native image aspect ratio must be strictly less than 2")
        return self


class Pilot2DerivedInput(StrictPilot2Model):
    record_type: Literal["pilot2_derived_input"] = "pilot2_derived_input"
    schema_version: Literal["2.0"] = "2.0"
    derived_input_id: str
    source_record_id: str
    source_path: str
    source_sha256: str
    output_path: str
    output_sha256: str
    preprocessing_version: Literal["pilot2-common-lossless-png-v1"] = (
        "pilot2-common-lossless-png-v1"
    )
    preprocessing_config_sha256: str
    source_width: int = Field(gt=0)
    source_height: int = Field(gt=0)
    source_decoded_format: str
    width: int = Field(gt=0, le=1024)
    height: int = Field(gt=0, le=1024)
    output_format: Literal["png"] = "png"
    color_space: Literal["sRGB"] = "sRGB"
    upsampled: Literal[False] = False

    @field_validator(
        "source_sha256", "output_sha256", "preprocessing_config_sha256"
    )
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("content identities must be lowercase SHA-256 values")
        return value


class Pilot2AcquiredImage(StrictPilot2Model):
    record_type: Literal["pilot2_acquired_image"] = "pilot2_acquired_image"
    schema_version: Literal["2.0"] = "2.0"
    canonical_work_id: str
    artist_id: str
    source_id: Pilot2Source
    source_object_id: str
    local_path: str
    sha256: str
    decoded_width: int = Field(gt=0)
    decoded_height: int = Field(gt=0)
    decoded_format: str
    atlas_selection_digest: str

    @field_validator("sha256", "atlas_selection_digest")
    @classmethod
    def identities_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("acquired-image identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def decoded_domain_is_eligible(self) -> "Pilot2AcquiredImage":
        if self.decoded_width * self.decoded_height <= 410 * 410:
            raise ValueError("pilot_2 acquired image area must be strictly greater than 410^2")
        ratio = max(self.decoded_width, self.decoded_height) / min(
            self.decoded_width, self.decoded_height
        )
        if ratio >= 2.0:
            raise ValueError("pilot_2 acquired image aspect ratio must be strictly less than 2")
        return self


class Pilot2Feature(StrictPilot2Model):
    record_type: Literal["pilot2_feature"] = "pilot2_feature"
    schema_version: Literal["2.0"] = "2.0"
    feature_id: str
    canonical_work_id: str
    artist_id: str
    source_id: Pilot2Source
    split: Pilot2Split
    feature_version: str
    feature_config_sha256: str
    derived_png_sha256: str
    vector: List[float]
    extraction_metadata: Dict[str, Any]
    status: Literal["ok", "failed"]
    failure_reason: Optional[str] = None

    @field_validator("feature_config_sha256", "derived_png_sha256")
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("feature identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def successful_vector_is_finite(self) -> "Pilot2Feature":
        if self.status == "ok":
            if not self.vector or any(not math.isfinite(value) for value in self.vector):
                raise ValueError("successful pilot_2 feature vectors must be finite and non-empty")
            if not self.extraction_metadata:
                raise ValueError("successful pilot_2 features require extraction provenance")
            if self.failure_reason is not None:
                raise ValueError("successful pilot_2 features cannot declare a failure")
            identity = stable_hash(
                {
                    "canonical_work_id": self.canonical_work_id,
                    "derived_png_sha256": self.derived_png_sha256,
                    "feature_version": self.feature_version,
                    "feature_config_sha256": self.feature_config_sha256,
                    "extraction_metadata": self.extraction_metadata,
                }
            )
            if self.feature_id != f"pilot2-feature-{identity[:24]}":
                raise ValueError("pilot_2 feature id does not hash its extraction contract")
        elif self.vector or self.extraction_metadata or not self.failure_reason:
            raise ValueError(
                "failed pilot_2 features require a reason, no vector, and no extraction metadata"
            )
        return self


class Pilot2PCAEvidence(StrictPilot2Model):
    fit_work_ids: List[str]
    input_dimension: int = Field(ge=2)
    component_cap: int = Field(ge=1)
    component_count: int = Field(ge=1)
    variance_target: Literal[0.95] = 0.95
    cumulative_explained_variance: float = Field(gt=0, le=1)
    variance_target_reached: bool
    mean_sha256: str
    basis_sha256: str
    state_sha256: str

    @model_validator(mode="after")
    def component_count_within_cap(self) -> "Pilot2PCAEvidence":
        if self.component_count > self.component_cap:
            raise ValueError("PCA component count exceeds its train-only rank cap")
        return self


class Pilot2ClassificationEvidence(StrictPilot2Model):
    expected_labels: List[str]
    predicted_labels: List[str]
    per_class_recall: Dict[str, float]
    balanced_accuracy: float = Field(ge=0, le=1)
    test_work_ids: List[str]

    @model_validator(mode="after")
    def rows_align(self) -> "Pilot2ClassificationEvidence":
        if not self.expected_labels:
            raise ValueError("classification evidence cannot be empty")
        if not (
            len(self.expected_labels)
            == len(self.predicted_labels)
            == len(self.test_work_ids)
        ):
            raise ValueError("classification evidence rows do not align")
        return self


class Pilot2HeldBySourceClassificationEvidence(StrictPilot2Model):
    source_id: Pilot2Source
    classifier_fit_work_count: Literal[24] = 24
    test_work_count: Literal[8] = 8
    shared_pca_state_sha256: str
    shared_artist_classifier_state_sha256: str
    classification: Pilot2ClassificationEvidence
    sample_size_note: Literal[
        "n=8 held works per source; balanced accuracy is a coarse discrete estimate"
    ] = "n=8 held works per source; balanced accuracy is a coarse discrete estimate"

    @field_validator(
        "shared_pca_state_sha256", "shared_artist_classifier_state_sha256"
    )
    @classmethod
    def shared_pca_hash_is_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("shared PCA identity must be a lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def exact_held_source_sample_size(self) -> "Pilot2HeldBySourceClassificationEvidence":
        if len(self.classification.test_work_ids) != 8:
            raise ValueError("held-source classification must contain exactly n=8 works")
        return self


class Pilot2OppositeSourceTransferDiagnostic(StrictPilot2Model):
    held_source_id: Pilot2Source
    pca: Pilot2PCAEvidence
    classification: Pilot2ClassificationEvidence
    role: Literal["development_non_gating"] = "development_non_gating"


class Pilot2SourcePredictabilityDiagnostic(StrictPilot2Model):
    classification: Pilot2ClassificationEvidence
    chance_balanced_accuracy: Literal[0.5] = 0.5
    shared_pca_state_sha256: str
    source_classifier_state_sha256: str
    role: Literal["development_non_gating"] = "development_non_gating"

    @field_validator("shared_pca_state_sha256", "source_classifier_state_sha256")
    @classmethod
    def shared_pca_hash_is_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("shared PCA identity must be a lowercase SHA-256")
        return value


class Pilot2DevelopmentDiagnostics(StrictPilot2Model):
    opposite_source_transfer: Dict[str, Pilot2OppositeSourceTransferDiagnostic]
    pooled_source_label_predictability: Pilot2SourcePredictabilityDiagnostic
    claim_boundary: Literal[
        "diagnostic_only_not_used_by_any_qualification_check"
    ] = "diagnostic_only_not_used_by_any_qualification_check"

    @model_validator(mode="after")
    def both_transfer_diagnostics_are_present(self) -> "Pilot2DevelopmentDiagnostics":
        if set(self.opposite_source_transfer) != {"aic", "nga"}:
            raise ValueError("development diagnostics require both opposite-source transfers")
        if any(
            key != evidence.held_source_id
            or len(evidence.classification.test_work_ids) != 8
            for key, evidence in self.opposite_source_transfer.items()
        ):
            raise ValueError("opposite-source transfer diagnostics are stale")
        source_diagnostic = self.pooled_source_label_predictability.classification
        if len(source_diagnostic.test_work_ids) != 16 or set(
            source_diagnostic.expected_labels
        ) != {"aic", "nga"}:
            raise ValueError("pooled source-label diagnostic must cover all 16 held works")
        return self


class Pilot2PermutationEvidence(StrictPilot2Model):
    scheme: Literal["artist_labels_within_source_by_split"] = (
        "artist_labels_within_source_by_split"
    )
    statistic: Literal["pooled_held_balanced_accuracy"] = (
        "pooled_held_balanced_accuracy"
    )
    observed_statistic: float = Field(ge=0, le=1)
    draws: int = Field(ge=19)
    seed: int = Field(ge=0)
    exceedance_count: int = Field(ge=0)
    p_value: float = Field(gt=0, le=1)
    threshold: Literal[0.05] = 0.05


class Pilot2DeterminismProbe(StrictPilot2Model):
    artist_id: str
    canonical_work_id: str
    feature_version: str
    derived_png_sha256: str
    seed: int = Field(ge=0, lt=2**63)
    first_vector_sha256: str
    second_vector_sha256: str
    exact_equal: bool

    @field_validator(
        "derived_png_sha256", "first_vector_sha256", "second_vector_sha256"
    )
    @classmethod
    def vector_hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("determinism vector identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def equality_matches_hashes(self) -> "Pilot2DeterminismProbe":
        if self.exact_equal != (self.first_vector_sha256 == self.second_vector_sha256):
            raise ValueError("determinism probe boolean disagrees with its vector hashes")
        return self


class Pilot2LearnedQualificationResult(StrictPilot2Model):
    record_type: Literal["pilot2_learned_qualification"] = (
        "pilot2_learned_qualification"
    )
    schema_version: Literal["2.0"] = "2.0"
    measurement: Literal["learned_formal"] = "learned_formal"
    status: Literal["pass", "fail"]
    feature_version: str
    feature_config_sha256: str
    input_feature_manifest_sha256: str
    input_acquired_manifest_sha256: str
    qualification_config_sha256: str
    qualification_contract_sha256: Optional[str] = None
    atlas_work_count: Literal[40] = 40
    train_work_count: Literal[24] = 24
    held_out_work_count: Literal[16] = 16
    pca: Pilot2PCAEvidence
    pooled_artist_classifier_state_sha256: str
    pooled_held: Pilot2ClassificationEvidence
    pooled_classifier_held_by_source: Dict[
        str, Pilot2HeldBySourceClassificationEvidence
    ]
    development_diagnostics: Pilot2DevelopmentDiagnostics
    permutation: Pilot2PermutationEvidence
    determinism_probes: List[Pilot2DeterminismProbe]
    checks: Dict[str, bool]
    reasons: List[str]
    result_sha256: str

    @field_validator(
        "feature_config_sha256",
        "input_feature_manifest_sha256",
        "input_acquired_manifest_sha256",
        "qualification_config_sha256",
        "result_sha256",
        "pooled_artist_classifier_state_sha256",
    )
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("qualification identities must be lowercase SHA-256 values")
        return value

    @field_validator("qualification_contract_sha256")
    @classmethod
    def optional_hash_is_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("qualification_contract_sha256 must be a lowercase SHA-256")
        return value

    @model_validator(mode="after")
    def exact_status_matches_checks(self) -> "Pilot2LearnedQualificationResult":
        passed = bool(self.checks) and all(self.checks.values())
        if (self.status == "pass") != passed:
            raise ValueError("qualification status disagrees with its required checks")
        if set(self.pooled_classifier_held_by_source) != {"aic", "nga"}:
            raise ValueError("qualification requires both held-source strata")
        if any(
            key != evidence.source_id
            or evidence.shared_pca_state_sha256 != self.pca.state_sha256
            or evidence.shared_artist_classifier_state_sha256
            != self.pooled_artist_classifier_state_sha256
            for key, evidence in self.pooled_classifier_held_by_source.items()
        ):
            raise ValueError("held-source strata do not use the pooled PCA/classifier")
        if self.status == "pass" and self.reasons:
            raise ValueError("passing qualification cannot contain failure reasons")
        return self


class Pilot2QualificationCard(StrictPilot2Model):
    record_type: Literal["pilot2_qualification_card"] = "pilot2_qualification_card"
    schema_version: Literal["2.0"] = "2.0"
    measurement: Literal["learned_formal"] = "learned_formal"
    status: Literal["pass", "fail"]
    feature_version: str
    feature_config_sha256: str
    qualification_contract_sha256: str
    qualification_result_sha256: str
    evidence_artifact_path: str
    evidence_artifact_sha256: str
    input_feature_manifest_sha256: str
    input_acquired_manifest_sha256: str
    reasons: List[str]

    @field_validator(
        "feature_config_sha256",
        "qualification_contract_sha256",
        "qualification_result_sha256",
        "evidence_artifact_sha256",
        "input_feature_manifest_sha256",
        "input_acquired_manifest_sha256",
    )
    @classmethod
    def card_hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("qualification card identities must be lowercase SHA-256 values")
        return value
