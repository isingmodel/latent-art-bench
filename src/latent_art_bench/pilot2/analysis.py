"""Confirmatory analysis for the prospective pilot_2 requested-label study.

The treatment is the label present in the request body sent to the pinned OAuth
facade.  Nothing in this module treats that label as evidence of the model that
executed upstream, and no contrast between labels is estimated.

The frozen grid contains eight content blocks, four named-artist prompts and one
shared artist-free control per block, two requested labels, and four repetitions.
Named and control outcomes are paired within content block, requested label, and
repetition.  Positive estimates mean that adding the artist name moved the output
toward the requested artist's held-out references.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import stable_hash
from latent_art_bench.pilot2.config import PILOT2_ARTISTS, PILOT2_SOURCES, Pilot2Config

RequestedLabel = Literal["gpt-image-1", "gpt-image-2"]
SourceId = Literal["aic", "nga"]
PrimaryEstimandName = Literal["target_improvement", "specificity_difference_in_differences"]
Outcome = Literal[
    "succeeded",
    "refused",
    "terminal_failure",
    "retryable_failure",
]
GenerationDisposition = Literal[
    "succeeded",
    "refused",
    "terminal_failure",
    "failed_after_retry_cap",
    "retry_pending",
    "not_attempted",
]

REQUESTED_LABELS: Tuple[str, str] = ("gpt-image-1", "gpt-image-2")
PRIMARY_ESTIMANDS: Tuple[str, str] = (
    "target_improvement",
    "specificity_difference_in_differences",
)
NEIGHBOR_BY_ARTIST: Dict[str, str] = {
    "alfred_sisley": "claude_monet",
    "claude_monet": "alfred_sisley",
    "camille_pissarro": "paul_cezanne",
    "paul_cezanne": "camille_pissarro",
}


class StrictAnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Pilot2GridSpec(StrictAnalysisModel):
    """Resolved identities for the exact 320-cell frozen assignment grid."""

    content_ids: List[str]
    artist_ids: List[str] = Field(default_factory=lambda: list(PILOT2_ARTISTS))
    neighbor_by_artist: Dict[str, str] = Field(
        default_factory=lambda: dict(NEIGHBOR_BY_ARTIST)
    )
    requested_labels: List[RequestedLabel] = Field(
        default_factory=lambda: list(REQUESTED_LABELS)
    )
    source_ids: List[SourceId] = Field(default_factory=lambda: list(PILOT2_SOURCES))
    repetitions: Literal[4] = 4
    held_out_works_per_artist_source: Literal[2] = 2

    @model_validator(mode="after")
    def exact_frozen_grid(self) -> "Pilot2GridSpec":
        if len(self.content_ids) != 8 or len(set(self.content_ids)) != 8:
            raise ValueError("pilot_2 requires exactly eight unique content blocks")
        if any(not value.strip() for value in self.content_ids):
            raise ValueError("pilot_2 content identifiers must not be blank")
        if tuple(sorted(self.artist_ids)) != PILOT2_ARTISTS:
            raise ValueError("pilot_2 analysis requires the frozen four artists")
        if len(set(self.artist_ids)) != 4:
            raise ValueError("pilot_2 artist identifiers must be unique")
        if self.neighbor_by_artist != NEIGHBOR_BY_ARTIST:
            raise ValueError("pilot_2 requires the prospectively frozen neighbor pairs")
        if self.requested_labels != list(REQUESTED_LABELS):
            raise ValueError("pilot_2 requires exactly the two requested labels in frozen order")
        if tuple(sorted(self.source_ids)) != PILOT2_SOURCES:
            raise ValueError("pilot_2 analysis requires exactly AIC and NGA references")
        return self

    @property
    def expected_cell_count(self) -> int:
        return (
            len(self.content_ids)
            * (len(self.artist_ids) + 1)
            * len(self.requested_labels)
            * self.repetitions
        )

    @property
    def expected_pair_count(self) -> int:
        return (
            len(self.content_ids)
            * len(self.artist_ids)
            * len(self.requested_labels)
            * self.repetitions
        )


class Pilot2ReferenceFeature(StrictAnalysisModel):
    canonical_work_id: str
    artist_id: str
    source_id: SourceId
    vector: List[float]

    @field_validator("vector")
    @classmethod
    def finite_vector(cls, value: List[float]) -> List[float]:
        if not value or any(not math.isfinite(item) for item in value):
            raise ValueError("reference feature vectors must be finite and non-empty")
        return value


class Pilot2GeneratedObservation(StrictAnalysisModel):
    """Terminal or still-retryable outcome for one assigned logical cell."""

    cell_id: str
    content_id: str
    requested_model_label: RequestedLabel
    repetition: int = Field(ge=0, le=3)
    target_artist_id: Optional[str] = None
    artist_free_control: bool = False
    outcome: Outcome
    vector: Optional[List[float]] = None
    generation_disposition: Optional[GenerationDisposition] = None
    physical_attempt_count: int = Field(default=0, ge=0, le=10)

    @model_validator(mode="after")
    def coherent_outcome(self) -> "Pilot2GeneratedObservation":
        if not self.cell_id.strip():
            raise ValueError("generated cell identifiers must not be blank")
        if self.artist_free_control != (self.target_artist_id is None):
            raise ValueError("artist-free controls must have no target artist")
        if self.outcome != "succeeded" and self.vector is not None:
            raise ValueError("only succeeded cells may carry a feature vector")
        if self.vector is not None and (
            not self.vector or any(not math.isfinite(item) for item in self.vector)
        ):
            raise ValueError("generated feature vectors must be finite and non-empty")
        if self.generation_disposition == "failed_after_retry_cap":
            if self.outcome != "terminal_failure" or self.physical_attempt_count != 10:
                raise ValueError(
                    "retry-cap exhaustion must be a ten-attempt terminal analysis outcome"
                )
        elif self.generation_disposition == "retry_pending":
            if self.outcome != "retryable_failure":
                raise ValueError("retry-pending ledger cells must remain retryable")
        elif self.generation_disposition in {
            "succeeded",
            "refused",
            "terminal_failure",
        }:
            if self.outcome != self.generation_disposition:
                raise ValueError("analysis outcome disagrees with ledger disposition")
        return self


class Pilot2AnalysisBindings(StrictAnalysisModel):
    """Frozen artifact identities required before scientific analysis."""

    pilot2_config_sha256: str
    protocol_document_sha256: str
    prompt_manifest_sha256: str
    qualification_result_sha256: str
    qualification_contract_sha256: str
    generation_gate_sha256: str
    transport_conformance_sha256: str
    generation_grid_sha256: str
    generation_completion_sha256: str

    @field_validator("*")
    @classmethod
    def binding_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("pilot_2 analysis bindings must be lowercase SHA-256 values")
        return value


class Pilot2ProjectedRealObservation(StrictAnalysisModel):
    """A real A-vector transformed by the one frozen train-only PCA basis."""

    record_type: Literal["pilot2_projected_real"] = "pilot2_projected_real"
    schema_version: Literal["2.0"] = "2.0"
    canonical_work_id: str
    artist_id: str
    source_id: SourceId
    split: Literal["train", "held_out"]
    pca_state_sha256: str
    raw_feature_sha256: str
    vector: List[float]

    @field_validator("pca_state_sha256", "raw_feature_sha256")
    @classmethod
    def projected_hash(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("projected-feature identities must be lowercase SHA-256 values")
        return value

    @field_validator("vector")
    @classmethod
    def projected_vector(cls, value: List[float]) -> List[float]:
        if not value or any(not math.isfinite(item) for item in value):
            raise ValueError("projected real vectors must be finite and non-empty")
        return value


class Pilot2ProjectedGeneratedObservation(Pilot2GeneratedObservation):
    """An assigned generated outcome, with a projected vector when available."""

    record_type: Literal["pilot2_projected_generated"] = (
        "pilot2_projected_generated"
    )
    schema_version: Literal["2.0"] = "2.0"
    prompt_id: str
    generation_cell_identity_sha256: str
    output_sha256: Optional[str] = None
    derived_png_sha256: Optional[str] = None
    pca_state_sha256: str
    raw_feature_sha256: Optional[str] = None

    @field_validator(
        "generation_cell_identity_sha256",
        "pca_state_sha256",
        "raw_feature_sha256",
        "output_sha256",
        "derived_png_sha256",
    )
    @classmethod
    def optional_projected_hash(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (
            len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("projected generated identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def projected_success_is_bound(self) -> "Pilot2ProjectedGeneratedObservation":
        if not self.prompt_id.strip():
            raise ValueError("projected generated observations must bind a prompt")
        if self.generation_disposition is None:
            raise ValueError("projected generated observations must retain ledger disposition")
        if self.outcome == "succeeded":
            required = {
                "projected vector": self.vector,
                "output SHA-256": self.output_sha256,
                "derived PNG SHA-256": self.derived_png_sha256,
                "raw feature SHA-256": self.raw_feature_sha256,
            }
            missing = [name for name, value in required.items() if value is None]
            if missing:
                raise ValueError(
                    "a successful projected generated observation lacks: "
                    + ", ".join(missing)
                )
            if self.generation_disposition != "succeeded":
                raise ValueError("successful analysis outcome disagrees with ledger disposition")
            if self.physical_attempt_count < 1:
                raise ValueError("successful analysis outcome has no physical send")
        elif any(
            value is not None
            for value in (
                self.vector,
                self.output_sha256,
                self.derived_png_sha256,
                self.raw_feature_sha256,
            )
        ):
            raise ValueError("non-successful generated outcomes cannot carry feature evidence")
        return self


class Pilot2ProjectedAnalysisInputs(StrictAnalysisModel):
    """Compact, content-addressed bridge from extraction to inference."""

    record_type: Literal["pilot2_projected_analysis_inputs"] = (
        "pilot2_projected_analysis_inputs"
    )
    schema_version: Literal["2.0"] = "2.0"
    pca_state_sha256: str
    projected_dimension: int = Field(ge=1)
    bindings: Pilot2AnalysisBindings
    real_observations: List[Pilot2ProjectedRealObservation]
    generated_observations: List[Pilot2ProjectedGeneratedObservation]
    manifest_sha256: str

    @field_validator("pca_state_sha256", "manifest_sha256")
    @classmethod
    def manifest_hash(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("projected-input identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def one_basis_and_exact_real_atlas(self) -> "Pilot2ProjectedAnalysisInputs":
        if len(self.real_observations) != 40:
            raise ValueError("projected pilot_2 inputs require all 40 frozen real works")
        work_ids = [row.canonical_work_id for row in self.real_observations]
        if len(work_ids) != len(set(work_ids)):
            raise ValueError("projected real work identifiers must be unique")
        cell_ids = [row.cell_id for row in self.generated_observations]
        if len(cell_ids) != len(set(cell_ids)):
            raise ValueError("projected generated cell identifiers must be unique")
        all_rows: Iterable[Any] = itertools.chain(
            self.real_observations, self.generated_observations
        )
        for row in all_rows:
            if row.pca_state_sha256 != self.pca_state_sha256:
                raise ValueError("projected inputs mix PCA states")
            if row.vector is not None and len(row.vector) != self.projected_dimension:
                raise ValueError("projected inputs mix feature dimensions")
        return self


class Pilot2ITTLabelSummary(StrictAnalysisModel):
    expected_cells: int
    observed_cells: int
    terminal_cells: int
    succeeded_cells: int
    succeeded_without_feature_cells: int
    refused_cells: int
    terminal_failure_cells: int
    failed_after_retry_cap_cells: int
    retryable_failure_cells: int
    missing_cells: int
    expected_pairs: int
    complete_feature_pairs: int
    refused_pairs: int
    failed_pairs: int
    feature_missing_pairs: int
    missing_pairs: int


class Pilot2ITTSummary(StrictAnalysisModel):
    expected_cells: Literal[320] = 320
    expected_named_control_pairs: Literal[256] = 256
    by_requested_label: Dict[str, Pilot2ITTLabelSummary]
    observed_cells: int
    terminal_cells: int
    succeeded_cells: int
    succeeded_without_feature_cells: int
    refused_cells: int
    terminal_failure_cells: int
    failed_after_retry_cap_cells: int
    retryable_failure_cells: int
    missing_cells: int
    complete_feature_pairs: int
    refused_pairs: int
    failed_pairs: int
    feature_missing_pairs: int
    missing_pairs: int


class Pilot2ScientificCompletion(StrictAnalysisModel):
    status: Literal["complete", "incomplete"]
    protocol_preconditions_met: bool
    exact_assignment_grid_accounted_for: bool
    analysis_executed: Literal[True] = True
    feature_estimand_grid_complete: bool
    does_not_imply_hypothesis_support: Literal[True] = True
    reasons: List[str]


class Pilot2PrimaryEstimate(StrictAnalysisModel):
    requested_model_label: RequestedLabel
    estimand: PrimaryEstimandName
    analysis_population: Literal[
        "frozen_itt_feature_grid", "available_complete_pairs_descriptive"
    ]
    estimate: Optional[float]
    confidence_interval: Optional[List[float]]
    familywise_lower_confidence_bound: Optional[float]
    source_sign_diagnostics: Dict[str, Optional[float]]
    content_block_estimates: Dict[str, Optional[float]]
    exact_sign_flip_p_value: Optional[float]
    holm_adjusted_p_value: float = Field(ge=0, le=1)
    aic_and_nga_positive: bool
    familywise_lower_confidence_bound_positive: bool
    hypothesis_supported: bool
    test_status: Literal["tested", "not_tested_incomplete_feature_grid"]

    @field_validator("confidence_interval")
    @classmethod
    def ordered_interval(cls, value: Optional[List[float]]) -> Optional[List[float]]:
        if value is not None and (len(value) != 2 or value[0] > value[1]):
            raise ValueError("confidence intervals must contain ordered lower and upper bounds")
        return value


class Pilot2ArtistEstimate(StrictAnalysisModel):
    """Registered descriptive per-artist secondary estimate (no inference)."""

    requested_model_label: RequestedLabel
    artist_id: str
    estimand: PrimaryEstimandName
    analysis_population: Literal[
        "frozen_itt_feature_grid", "available_complete_pairs_descriptive"
    ]
    estimate: Optional[float]
    source_estimates: Dict[str, Optional[float]]
    complete_pairs: int = Field(ge=0, le=32)
    expected_pairs: Literal[32] = 32
    inferential_claim: Literal[False] = False
    multiplicity_adjusted: Literal[False] = False


class Pilot2ChromaticRealSummary(StrictAnalysisModel):
    artist_id: str
    source_id: SourceId
    work_count: Literal[5] = 5
    mean_seamlessness: float
    mean_histogram_hellinger_to_cell_centroid: float = Field(ge=0)


class Pilot2ChromaticLabelSummary(StrictAnalysisModel):
    requested_model_label: RequestedLabel
    expected_named_cells: Literal[128] = 128
    expected_control_cells: Literal[32] = 32
    named_feature_cells: int = Field(ge=0, le=128)
    control_feature_cells: int = Field(ge=0, le=32)
    complete_named_control_pairs: int = Field(ge=0, le=128)
    mean_named_seamlessness: Optional[float]
    mean_control_seamlessness: Optional[float]
    mean_paired_named_minus_control_seamlessness: Optional[float]
    mean_paired_named_control_histogram_hellinger: Optional[float]


class Pilot2ChromaticArtistPairSummary(StrictAnalysisModel):
    requested_model_label: RequestedLabel
    artist_id: str
    expected_pairs: Literal[32] = 32
    complete_pairs: int = Field(ge=0, le=32)
    mean_named_seamlessness: Optional[float]
    mean_matched_control_seamlessness: Optional[float]
    mean_paired_named_minus_control_seamlessness: Optional[float]
    mean_paired_named_control_histogram_hellinger: Optional[float]
    mean_named_to_real_artist_histogram_hellinger: Optional[float]
    mean_control_to_real_artist_histogram_hellinger: Optional[float]


class Pilot2ChromaticSecondaryResult(StrictAnalysisModel):
    record_type: Literal["pilot2_chromatic_secondary_analysis"] = (
        "pilot2_chromatic_secondary_analysis"
    )
    schema_version: Literal["2.0"] = "2.0"
    pilot_id: Literal["pilot_2"] = "pilot_2"
    role: Literal["secondary_descriptive_non_gating"] = (
        "secondary_descriptive_non_gating"
    )
    can_open_or_close_generation_gate: Literal[False] = False
    can_rescue_primary_analysis: Literal[False] = False
    executed_model_claims: Literal[False] = False
    cross_label_superiority_estimand: Literal[False] = False
    bindings: Pilot2AnalysisBindings
    feature_config_sha256: str
    chromatic_input_manifest_sha256: str
    expected_real_features: Literal[40] = 40
    observed_real_features: Literal[40] = 40
    expected_generated_cells: Literal[320] = 320
    observed_generated_features: int = Field(ge=0, le=320)
    generated_cells_without_chromatic_feature: int = Field(ge=0, le=320)
    real_reference_summaries: List[Pilot2ChromaticRealSummary]
    requested_label_summaries: List[Pilot2ChromaticLabelSummary]
    artist_pair_summaries: List[Pilot2ChromaticArtistPairSummary]
    result_sha256: str

    @field_validator(
        "feature_config_sha256", "chromatic_input_manifest_sha256", "result_sha256"
    )
    @classmethod
    def chromatic_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("chromatic analysis identities must be lowercase SHA-256")
        return value


class Pilot2AnalysisResult(StrictAnalysisModel):
    record_type: Literal["pilot2_requested_label_analysis"] = (
        "pilot2_requested_label_analysis"
    )
    schema_version: Literal["2.0"] = "2.0"
    pilot_id: Literal["pilot_2"] = "pilot_2"
    analysis_scope: Literal["requested_label_operational_effect"] = (
        "requested_label_operational_effect"
    )
    executed_model_claims: Literal[False] = False
    cross_label_superiority_estimand: Literal[False] = False
    grid: Pilot2GridSpec
    itt: Pilot2ITTSummary
    scientific_completion: Pilot2ScientificCompletion
    estimand_definitions: Dict[str, str]
    primary_estimates: List[Pilot2PrimaryEstimate]
    secondary_artist_estimates: List[Pilot2ArtistEstimate]
    hypothesis_support_by_requested_label: Dict[str, bool]
    all_four_primary_hypotheses_supported: bool
    multiplicity_method: Literal["holm_four_primary_hypotheses"] = (
        "holm_four_primary_hypotheses"
    )
    simultaneous_lower_bound_method: Literal[
        "bonferroni_one_sided_four_primary_hypotheses"
    ] = "bonferroni_one_sided_four_primary_hypotheses"
    familywise_alpha: Literal[0.05] = 0.05
    bootstrap_method: Literal[
        "real_work_within_artist_source_then_content_block_then_repetition"
    ] = "real_work_within_artist_source_then_content_block_then_repetition"
    bootstrap_draws: int = Field(ge=1)
    bootstrap_seed: int = Field(ge=0)
    confidence_level: float = Field(gt=0, lt=1)
    projected_input_manifest_sha256: str
    bootstrap_distribution_sha256: Optional[str]
    result_sha256: str

    @field_validator("result_sha256", "bootstrap_distribution_sha256")
    @classmethod
    def valid_optional_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and (
            len(value) != 64 or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError("analysis identities must be lowercase SHA-256 values")
        return value

    @field_validator("projected_input_manifest_sha256")
    @classmethod
    def valid_required_manifest_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("projected input identity must be a lowercase SHA-256")
        return value


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if hasattr(value, "__dict__"):
        return vars(value)
    raise TypeError(f"cannot read record of type {type(value).__name__}")


def _record_value(record: Any, *names: str, default: Any = None) -> Any:
    mapping = _as_mapping(record)
    for name in names:
        if name in mapping:
            return mapping[name]
    return default


def grid_spec_from_config(
    config: Pilot2Config,
    *,
    content_ids: Optional[Sequence[str]] = None,
    prompt_records: Optional[Sequence[Any]] = None,
) -> Pilot2GridSpec:
    """Resolve and validate the exact grid from config plus its prompt identities.

    The config freezes counts and treatment labels; content identifiers live in
    the separately hashed prompt manifest.  Callers must therefore supply either
    its eight identifiers or its prompt records.
    """

    if content_ids is None:
        if prompt_records is None:
            raise ValueError("content_ids or prompt_records are required to resolve the grid")
        content_ids = list(
            dict.fromkeys(
                str(_record_value(record, "content_id", default=""))
                for record in prompt_records
            )
        )
    # Content order is part of the frozen prompt manifest and affects the
    # deterministic bootstrap realization. Preserve first occurrence exactly.
    resolved = list(dict.fromkeys(str(value) for value in content_ids))
    spec = Pilot2GridSpec(
        content_ids=resolved,
        artist_ids=sorted(config.corpus.artist_ids),
        requested_labels=list(config.generation.models),
        source_ids=sorted(config.corpus.source_ids),
        repetitions=config.generation.repetitions,
        held_out_works_per_artist_source=config.corpus.held_out_per_artist_source,
    )
    if config.generation.content_block_count != len(spec.content_ids):
        raise ValueError("prompt content blocks disagree with the frozen config")
    if config.generation.logical_cell_count != spec.expected_cell_count:
        raise ValueError("resolved analysis grid disagrees with the frozen 320-cell config")
    if prompt_records is not None:
        by_content: Dict[str, List[Any]] = defaultdict(list)
        for record in prompt_records:
            by_content[str(_record_value(record, "content_id", default=""))].append(record)
        for content_id in spec.content_ids:
            rows = by_content.get(content_id, [])
            targets = [
                _record_value(row, "target_artist_id")
                for row in rows
                if not bool(_record_value(row, "artist_free_control", default=False))
            ]
            controls = [
                row
                for row in rows
                if bool(_record_value(row, "artist_free_control", default=False))
            ]
            if len(rows) != 5 or sorted(targets) != sorted(spec.artist_ids) or len(controls) != 1:
                raise ValueError(
                    f"content block {content_id!r} must contain four targets and one control"
                )
    return spec


def _coerce_reference_feature(record: Any) -> Optional[Pilot2ReferenceFeature]:
    split = _record_value(record, "split", default="held_out")
    if split != "held_out":
        return None
    status = _record_value(record, "status", default="ok")
    if status != "ok":
        raise ValueError("a held-out pilot_2 reference feature failed extraction")
    return Pilot2ReferenceFeature(
        canonical_work_id=str(
            _record_value(record, "canonical_work_id", "work_id", default="")
        ),
        artist_id=str(_record_value(record, "artist_id", default="")),
        source_id=str(_record_value(record, "source_id", default="")),
        vector=list(_record_value(record, "vector", default=[])),
    )


def _normalized_outcome(value: Any) -> str:
    normalized = str(value).strip().casefold()
    aliases = {
        "success": "succeeded",
        "ok": "succeeded",
        "failed": "terminal_failure",
        "failure": "terminal_failure",
        "refusal": "refused",
        "retryable": "retryable_failure",
        "pending": "retryable_failure",
        "retry_pending": "retryable_failure",
        "failed_after_retry_cap": "terminal_failure",
    }
    return aliases.get(normalized, normalized)


def _analysis_disposition(record: Mapping[str, Any]) -> Optional[str]:
    """Return the ledger disposition without mutating the immutable attempt ledger."""

    if bool(record.get("retry_cap_exhausted", False)):
        return "failed_after_retry_cap"
    value = record.get(
        "generation_disposition",
        record.get("cell_disposition", record.get("terminal_disposition")),
    )
    return None if value is None else str(value)


def _coerce_generated_observation(
    record: Any,
    feature_vectors_by_cell: Optional[Mapping[str, Sequence[float]]] = None,
) -> Pilot2GeneratedObservation:
    mapping = _as_mapping(record)
    cell = mapping.get("cell")
    cell_mapping: Mapping[str, Any] = _as_mapping(cell) if cell is not None else {}

    def value(*names: str, default: Any = None) -> Any:
        for source in (mapping, cell_mapping):
            for name in names:
                if name in source:
                    return source[name]
        return default

    cell_id = str(value("cell_id", default=""))
    vector = value("vector")
    if vector is None and feature_vectors_by_cell is not None:
        vector = feature_vectors_by_cell.get(cell_id)
    target = value("target_artist_id")
    control = bool(value("artist_free_control", default=target is None))
    return Pilot2GeneratedObservation(
        cell_id=cell_id,
        content_id=str(value("content_id", default="")),
        requested_model_label=str(
            value("requested_model_label", "requested_model", "model", default="")
        ),
        repetition=int(value("repetition", default=-1)),
        target_artist_id=None if target is None else str(target),
        artist_free_control=control,
        outcome=_normalized_outcome(value("outcome", "status", "terminal_outcome", default="")),
        vector=None if vector is None else list(vector),
        generation_disposition=_analysis_disposition(mapping),
        physical_attempt_count=int(value("physical_attempt_count", "attempt_count", default=0)),
    )


CellKey = Tuple[str, str, int, Optional[str]]


def _cell_key(
    content_id: str,
    label: str,
    repetition: int,
    target_artist_id: Optional[str],
) -> CellKey:
    return (content_id, label, repetition, target_artist_id)


def _expected_keys(grid: Pilot2GridSpec) -> List[CellKey]:
    return [
        _cell_key(content, label, repetition, target)
        for content in grid.content_ids
        for label in grid.requested_labels
        for repetition in range(grid.repetitions)
        for target in [None, *grid.artist_ids]
    ]


def _reference_arrays(
    records: Sequence[Any], grid: Pilot2GridSpec
) -> Tuple[Dict[Tuple[str, str], np.ndarray], int]:
    grouped: Dict[Tuple[str, str], List[Pilot2ReferenceFeature]] = defaultdict(list)
    all_work_ids: set[str] = set()
    dimension: Optional[int] = None
    for raw in records:
        record = _coerce_reference_feature(raw)
        if record is None:
            continue
        if record.artist_id not in grid.artist_ids or record.source_id not in grid.source_ids:
            raise ValueError("held-out reference feature lies outside the frozen atlas")
        if record.canonical_work_id in all_work_ids:
            raise ValueError("held-out physical works must be unique across reference cells")
        all_work_ids.add(record.canonical_work_id)
        if dimension is None:
            dimension = len(record.vector)
        elif len(record.vector) != dimension:
            raise ValueError("reference feature dimensions are inconsistent")
        grouped[(record.artist_id, record.source_id)].append(record)

    expected_keys = {
        (artist, source) for artist in grid.artist_ids for source in grid.source_ids
    }
    if set(grouped) != expected_keys:
        missing = sorted(expected_keys - set(grouped))
        raise ValueError(f"held-out reference atlas lacks artist-by-source cells: {missing}")
    arrays: Dict[Tuple[str, str], np.ndarray] = {}
    for key, rows in grouped.items():
        rows.sort(key=lambda row: row.canonical_work_id)
        if len(rows) != grid.held_out_works_per_artist_source:
            raise ValueError(
                f"reference cell {key!r} must contain exactly "
                f"{grid.held_out_works_per_artist_source} held-out works"
            )
        arrays[key] = np.asarray([row.vector for row in rows], dtype=np.float64)
    if dimension is None:
        raise ValueError("held-out reference features are empty")
    return arrays, dimension


def _generated_index(
    records: Sequence[Any],
    grid: Pilot2GridSpec,
    feature_dimension: int,
    feature_vectors_by_cell: Optional[Mapping[str, Sequence[float]]],
) -> Dict[CellKey, Pilot2GeneratedObservation]:
    expected = set(_expected_keys(grid))
    by_key: Dict[CellKey, Pilot2GeneratedObservation] = {}
    cell_ids: set[str] = set()
    for raw in records:
        record = _coerce_generated_observation(raw, feature_vectors_by_cell)
        if record.content_id not in grid.content_ids:
            raise ValueError(f"unexpected generated content block: {record.content_id}")
        if record.target_artist_id is not None and record.target_artist_id not in grid.artist_ids:
            raise ValueError(f"unexpected generated target artist: {record.target_artist_id}")
        key = _cell_key(
            record.content_id,
            record.requested_model_label,
            record.repetition,
            record.target_artist_id,
        )
        if key not in expected:
            raise ValueError(f"unexpected generated assignment cell: {key!r}")
        if key in by_key:
            raise ValueError(f"duplicate generated assignment cell: {key!r}")
        if record.cell_id in cell_ids:
            raise ValueError(f"duplicate generated cell identifier: {record.cell_id}")
        if record.vector is not None and len(record.vector) != feature_dimension:
            raise ValueError("generated and held-out feature dimensions disagree")
        by_key[key] = record
        cell_ids.add(record.cell_id)
    return by_key


def _pair_status(
    named: Optional[Pilot2GeneratedObservation],
    control: Optional[Pilot2GeneratedObservation],
) -> str:
    if named is None or control is None:
        return "missing"
    if named.outcome == "refused" or control.outcome == "refused":
        return "refused"
    if named.outcome != "succeeded" or control.outcome != "succeeded":
        return "failed"
    if named.vector is None or control.vector is None:
        return "feature_missing"
    return "complete"


def _itt_summary(
    grid: Pilot2GridSpec,
    observations: Mapping[CellKey, Pilot2GeneratedObservation],
) -> Pilot2ITTSummary:
    by_label: Dict[str, Pilot2ITTLabelSummary] = {}
    for label in grid.requested_labels:
        cell_counts: Counter[str] = Counter()
        pair_counts: Counter[str] = Counter()
        expected_for_label = [key for key in _expected_keys(grid) if key[1] == label]
        for key in expected_for_label:
            record = observations.get(key)
            if record is None:
                cell_counts["missing"] += 1
                continue
            cell_counts[record.outcome] += 1
            if record.generation_disposition == "failed_after_retry_cap":
                cell_counts["failed_after_retry_cap"] += 1
            if record.outcome == "succeeded" and record.vector is None:
                cell_counts["succeeded_without_feature"] += 1
        for content in grid.content_ids:
            for repetition in range(grid.repetitions):
                control = observations.get(_cell_key(content, label, repetition, None))
                for artist in grid.artist_ids:
                    named = observations.get(_cell_key(content, label, repetition, artist))
                    pair_counts[_pair_status(named, control)] += 1
        terminal = (
            cell_counts["succeeded"]
            + cell_counts["refused"]
            + cell_counts["terminal_failure"]
        )
        by_label[label] = Pilot2ITTLabelSummary(
            expected_cells=len(expected_for_label),
            observed_cells=len(expected_for_label) - cell_counts["missing"],
            terminal_cells=terminal,
            succeeded_cells=cell_counts["succeeded"],
            succeeded_without_feature_cells=cell_counts["succeeded_without_feature"],
            refused_cells=cell_counts["refused"],
            terminal_failure_cells=cell_counts["terminal_failure"],
            failed_after_retry_cap_cells=cell_counts["failed_after_retry_cap"],
            retryable_failure_cells=cell_counts["retryable_failure"],
            missing_cells=cell_counts["missing"],
            expected_pairs=(len(grid.content_ids) * len(grid.artist_ids) * grid.repetitions),
            complete_feature_pairs=pair_counts["complete"],
            refused_pairs=pair_counts["refused"],
            failed_pairs=pair_counts["failed"],
            feature_missing_pairs=pair_counts["feature_missing"],
            missing_pairs=pair_counts["missing"],
        )

    def total(field: str) -> int:
        return sum(int(getattr(row, field)) for row in by_label.values())

    return Pilot2ITTSummary(
        by_requested_label=by_label,
        observed_cells=total("observed_cells"),
        terminal_cells=total("terminal_cells"),
        succeeded_cells=total("succeeded_cells"),
        succeeded_without_feature_cells=total("succeeded_without_feature_cells"),
        refused_cells=total("refused_cells"),
        terminal_failure_cells=total("terminal_failure_cells"),
        failed_after_retry_cap_cells=total("failed_after_retry_cap_cells"),
        retryable_failure_cells=total("retryable_failure_cells"),
        missing_cells=total("missing_cells"),
        complete_feature_pairs=total("complete_feature_pairs"),
        refused_pairs=total("refused_pairs"),
        failed_pairs=total("failed_pairs"),
        feature_missing_pairs=total("feature_missing_pairs"),
        missing_pairs=total("missing_pairs"),
    )


def _centroid_distance(vector: np.ndarray, references: np.ndarray) -> float:
    return float(np.linalg.norm(vector - references.mean(axis=0)))


def _pair_contrasts(
    named: np.ndarray,
    control: np.ndarray,
    target: np.ndarray,
    neighbor: np.ndarray,
) -> Tuple[float, float]:
    named_target = _centroid_distance(named, target)
    control_target = _centroid_distance(control, target)
    named_neighbor = _centroid_distance(named, neighbor)
    control_neighbor = _centroid_distance(control, neighbor)
    target_improvement = control_target - named_target
    specificity_did = (
        (named_neighbor - named_target) - (control_neighbor - control_target)
    )
    return float(target_improvement), float(specificity_did)


def _generated_tensors(
    grid: Pilot2GridSpec,
    observations: Mapping[CellKey, Pilot2GeneratedObservation],
    dimension: int,
) -> Tuple[np.ndarray, np.ndarray]:
    named = np.full(
        (
            len(grid.requested_labels),
            len(grid.content_ids),
            grid.repetitions,
            len(grid.artist_ids),
            dimension,
        ),
        np.nan,
        dtype=np.float64,
    )
    controls = np.full(
        (
            len(grid.requested_labels),
            len(grid.content_ids),
            grid.repetitions,
            dimension,
        ),
        np.nan,
        dtype=np.float64,
    )
    for label_index, label in enumerate(grid.requested_labels):
        for content_index, content in enumerate(grid.content_ids):
            for repetition in range(grid.repetitions):
                control = observations.get(_cell_key(content, label, repetition, None))
                if (
                    control is not None
                    and control.outcome == "succeeded"
                    and control.vector is not None
                ):
                    controls[label_index, content_index, repetition] = control.vector
                for artist_index, artist in enumerate(grid.artist_ids):
                    row = observations.get(_cell_key(content, label, repetition, artist))
                    if row is not None and row.outcome == "succeeded" and row.vector is not None:
                        named[label_index, content_index, repetition, artist_index] = row.vector
    return named, controls


def _contrast_tensor(
    grid: Pilot2GridSpec,
    references: Mapping[Tuple[str, str], np.ndarray],
    named: np.ndarray,
    controls: np.ndarray,
) -> np.ndarray:
    # label, reference-domain (pooled, AIC, NGA), content, repetition,
    # artist, estimand
    values = np.full(
        (
            len(grid.requested_labels),
            len(grid.source_ids) + 1,
            len(grid.content_ids),
            grid.repetitions,
            len(grid.artist_ids),
            len(PRIMARY_ESTIMANDS),
        ),
        np.nan,
        dtype=np.float64,
    )
    for label_index in range(len(grid.requested_labels)):
        for artist_index, artist in enumerate(grid.artist_ids):
            neighbor_artist = grid.neighbor_by_artist[artist]
            domains = [
                (
                    np.concatenate(
                        [references[(artist, source)] for source in grid.source_ids]
                    ),
                    np.concatenate(
                        [
                            references[(neighbor_artist, source)]
                            for source in grid.source_ids
                        ]
                    ),
                ),
                *[
                    (
                        references[(artist, source)],
                        references[(neighbor_artist, source)],
                    )
                    for source in grid.source_ids
                ],
            ]
            for domain_index, (target, neighbor) in enumerate(domains):
                for content_index in range(len(grid.content_ids)):
                    for repetition in range(grid.repetitions):
                        named_vector = named[
                            label_index, content_index, repetition, artist_index
                        ]
                        control_vector = controls[label_index, content_index, repetition]
                        if not (
                            np.isfinite(named_vector).all()
                            and np.isfinite(control_vector).all()
                        ):
                            continue
                        values[
                            label_index,
                            domain_index,
                            content_index,
                            repetition,
                            artist_index,
                        ] = _pair_contrasts(
                            named_vector, control_vector, target, neighbor
                        )
    return values


def exact_block_sign_flip_p_value(values: Sequence[float]) -> float:
    """Exact one-sided sign-flip test over the eight frozen content blocks."""

    array = np.asarray(values, dtype=np.float64)
    if array.shape != (8,) or not np.isfinite(array).all():
        raise ValueError("the exact pilot_2 sign-flip test requires eight finite block values")
    observed = float(array.mean())
    assignments = np.asarray(list(itertools.product((-1.0, 1.0), repeat=8)))
    permuted = (assignments * array[None, :]).mean(axis=1)
    tolerance = 10.0 * np.finfo(np.float64).eps * max(1.0, abs(observed))
    return float(np.count_nonzero(permuted >= observed - tolerance) / permuted.size)


def holm_adjust(p_values: Mapping[str, float]) -> Dict[str, float]:
    """Return monotone Holm-adjusted p-values for one fixed family."""

    if not p_values:
        raise ValueError("Holm adjustment requires at least one hypothesis")
    for key, value in p_values.items():
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"invalid p-value for {key}: {value}")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    adjusted: Dict[str, float] = {}
    running = 0.0
    family_size = len(ordered)
    for index, (key, value) in enumerate(ordered):
        running = max(running, min(1.0, (family_size - index) * value))
        adjusted[key] = running
    return adjusted


def _resampled_contrast_tensor(
    grid: Pilot2GridSpec,
    references: Mapping[Tuple[str, str], np.ndarray],
    named: np.ndarray,
    controls: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    sampled: Dict[Tuple[str, str], np.ndarray] = {}
    # One shared resample per artist-by-source cell preserves its use as target
    # in one contrast and neighbor in the reciprocal contrast.
    for key in sorted(references):
        rows = references[key]
        indices = rng.integers(0, rows.shape[0], size=rows.shape[0])
        sampled[key] = rows[indices]
    return _contrast_tensor(grid, sampled, named, controls)


def _bootstrap_primary_estimates(
    grid: Pilot2GridSpec,
    references: Mapping[Tuple[str, str], np.ndarray],
    named: np.ndarray,
    controls: np.ndarray,
    *,
    draws: int,
    seed: int,
    complete_label_indices: Sequence[int],
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    estimates = np.full(
        (draws, len(grid.requested_labels), len(PRIMARY_ESTIMANDS)),
        np.nan,
        dtype=np.float64,
    )
    for draw in range(draws):
        contrasts = _resampled_contrast_tensor(
            grid, references, named, controls, rng
        )
        block_indices = rng.integers(
            0, len(grid.content_ids), size=len(grid.content_ids)
        )
        repetitions = rng.integers(
            0,
            grid.repetitions,
            size=(len(grid.content_ids), grid.repetitions),
        )
        selected = np.stack(
            [
                contrasts[:, :, block_index, repetitions[index], :, :]
                for index, block_index in enumerate(block_indices)
            ],
            axis=2,
        )
        # The primary reference centroid pools the equally populated AIC and NGA
        # held-out cells. Average artists equally, repetitions within sampled
        # blocks, and sampled blocks. Source-only domains remain diagnostics.
        draw_estimates = selected[:, 0].mean(axis=(1, 2, 3))
        estimates[draw, complete_label_indices] = draw_estimates[
            complete_label_indices
        ]
    if not np.isfinite(estimates[:, complete_label_indices]).all():
        raise ValueError("cluster bootstrap produced a non-finite estimate")
    return estimates


def _distribution_sha256(values: np.ndarray) -> str:
    normalized = np.ascontiguousarray(values, dtype="<f8")
    return hashlib.sha256(normalized.tobytes()).hexdigest()


def _quantile_interval(values: np.ndarray, confidence_level: float) -> List[float]:
    alpha = (1.0 - confidence_level) / 2.0
    return [
        float(np.quantile(values, alpha)),
        float(np.quantile(values, 1.0 - alpha)),
    ]


def _result_hash(payload: Mapping[str, Any]) -> str:
    return stable_hash(
        {key: value for key, value in payload.items() if key != "result_sha256"}
    )


def _vector_sha256(vector: Sequence[float]) -> str:
    values = np.ascontiguousarray(np.asarray(vector, dtype="<f8"))
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("raw feature hashes require a finite one-dimensional vector")
    digest = hashlib.sha256()
    digest.update(str(values.shape).encode("ascii"))
    digest.update(b"\0float64-le\0C\0")
    digest.update(values.tobytes())
    return digest.hexdigest()


def _projected_manifest_hash(payload: Mapping[str, Any]) -> str:
    return stable_hash(
        {key: value for key, value in payload.items() if key != "manifest_sha256"}
    )


def assemble_generation_analysis_rows(
    generation_cells: Sequence[Any],
    generation_attempts: Sequence[Any],
    *,
    raw_generated_vectors_by_cell: Mapping[str, Sequence[float]],
    derived_png_sha256_by_cell: Mapping[str, str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Join the immutable transport ledger to normalized extraction evidence.

    The transport layer deliberately preserves the tenth retry as the physical
    attempt outcome ``retryable_failure``.  Its terminal-record API maps that
    exhausted logical cell to ``terminal_failure`` for grid accounting while
    retaining the source attempt and retry-cap evidence.  This adapter adds only
    the downstream normalized-image and raw-feature evidence needed for PCA.
    """

    from latent_art_bench.pilot2.generation import (
        generation_completion_report,
        terminal_records_for_analysis,
    )

    completion = generation_completion_report(generation_cells, generation_attempts)
    terminal = terminal_records_for_analysis(generation_cells, generation_attempts)
    rows: List[Dict[str, Any]] = []
    for record in terminal:
        row = record.model_dump(mode="json")
        disposition = completion["cell_dispositions"][record.cell_id]
        row["generation_disposition"] = disposition
        row["physical_attempt_count"] = record.attempt_count
        if record.outcome == "succeeded":
            try:
                raw_vector = list(raw_generated_vectors_by_cell[record.cell_id])
                derived_sha = derived_png_sha256_by_cell[record.cell_id]
            except KeyError as exc:
                raise ValueError(
                    "successful generation cell lacks normalized feature evidence: "
                    f"{record.cell_id}"
                ) from exc
            row["raw_vector"] = raw_vector
            row["raw_feature_sha256"] = _vector_sha256(raw_vector)
            row["derived_png_sha256"] = derived_sha
        rows.append(row)
    return rows, completion


def prepare_projected_analysis_inputs(
    frozen_pca: Any,
    real_raw_features: Sequence[Any],
    generated_records: Sequence[Any],
    *,
    bindings: Pilot2AnalysisBindings,
    generation_cells: Sequence[Any],
    generation_completion: Mapping[str, Any],
    raw_generated_vectors_by_cell: Optional[Mapping[str, Sequence[float]]] = None,
    derived_png_sha256_by_cell: Optional[Mapping[str, str]] = None,
) -> Pilot2ProjectedAnalysisInputs:
    """Project real and generated raw A-vectors with one qualified PCA state.

    ``real_raw_features`` is the complete 40-work atlas, including the 24 rows
    used to fit ``frozen_pca`` and the 16 held-out references.  Generated rows
    are already joined to their prompt/cell assignment and terminal outcome;
    their raw 16,384-value vectors may be carried on the row as ``raw_vector``
    or ``vector``, or supplied by cell identifier in
    ``raw_generated_vectors_by_cell``.
    """

    from latent_art_bench.pilot2.generation import generation_grid_sha256
    from latent_art_bench.pilot2.learned_formal import transform_with_pca

    if not hasattr(frozen_pca, "mean") or not hasattr(frozen_pca, "components"):
        raise TypeError("frozen_pca must expose mean and components")
    evidence = getattr(frozen_pca, "evidence", None)
    state_sha = getattr(evidence, "state_sha256", None)
    if not isinstance(state_sha, str):
        raise ValueError("frozen_pca lacks a content-addressed state identity")
    if len(generation_cells) != 320:
        raise ValueError("projection requires the exact 320-cell generation grid")
    observed_grid_hash = generation_grid_sha256(generation_cells)
    if observed_grid_hash != bindings.generation_grid_sha256:
        raise ValueError("generation cells disagree with the frozen grid binding")
    if generation_completion.get("generation_grid_sha256") != observed_grid_hash:
        raise ValueError("generation completion report binds a different grid")
    if generation_completion.get("report_sha256") != bindings.generation_completion_sha256:
        raise ValueError("generation completion report hash disagrees with its binding")
    completion_payload = {
        key: value
        for key, value in generation_completion.items()
        if key != "report_sha256"
    }
    if stable_hash(completion_payload) != bindings.generation_completion_sha256:
        raise ValueError("generation completion report has an invalid self-hash")
    cell_index: Dict[str, Mapping[str, Any]] = {}
    for raw_cell in generation_cells:
        cell = _as_mapping(raw_cell)
        cell_id = str(cell.get("cell_id", ""))
        if not cell_id or cell_id in cell_index:
            raise ValueError("generation cell identities must be unique and nonblank")
        cell_index[cell_id] = cell

    real_rows: List[Mapping[str, Any]] = []
    raw_real_vectors: List[List[float]] = []
    for raw in real_raw_features:
        row = _as_mapping(raw)
        if row.get("status", "ok") != "ok":
            raise ValueError("all 40 real pilot_2 A-vectors must extract successfully")
        vector = list(row.get("vector", []))
        raw_real_vectors.append(vector)
        real_rows.append(row)
    if len(real_rows) != 40:
        raise ValueError("projection requires the complete 40-work real atlas")
    real_matrix = np.asarray(raw_real_vectors, dtype=np.float64)
    projected_real_matrix = transform_with_pca(real_matrix, frozen_pca)

    projected_real: List[Pilot2ProjectedRealObservation] = []
    for index, row in enumerate(real_rows):
        projected_real.append(
            Pilot2ProjectedRealObservation(
                canonical_work_id=str(row.get("canonical_work_id", "")),
                artist_id=str(row.get("artist_id", "")),
                source_id=str(row.get("source_id", "")),
                split=str(row.get("split", "")),
                pca_state_sha256=state_sha,
                raw_feature_sha256=_vector_sha256(raw_real_vectors[index]),
                vector=projected_real_matrix[index].tolist(),
            )
        )

    train_ids = sorted(
        row.canonical_work_id for row in projected_real if row.split == "train"
    )
    fit_ids = sorted(str(value) for value in getattr(evidence, "fit_work_ids", []))
    if len(train_ids) != 24 or fit_ids != train_ids:
        raise ValueError("frozen PCA was not fitted on exactly the 24 frozen training works")

    generated_parts: List[Tuple[Mapping[str, Any], Mapping[str, Any], Optional[List[float]]]] = []
    vectors_to_project: List[List[float]] = []
    vector_positions: List[int] = []
    for raw in generated_records:
        row = _as_mapping(raw)
        cell_value = row.get("cell")
        cell = _as_mapping(cell_value) if cell_value is not None else {}
        cell_id = str(row.get("cell_id", cell.get("cell_id", "")))
        frozen_cell = cell_index.get(cell_id)
        if frozen_cell is None:
            raise ValueError(f"generated analysis row references unknown cell: {cell_id}")
        for field in (
            "prompt_id",
            "content_id",
            "target_artist_id",
            "artist_free_control",
            "requested_model_label",
            "repetition",
        ):
            observed = row.get(field, cell.get(field))
            if observed != frozen_cell.get(field):
                raise ValueError(
                    f"generated analysis row disagrees with frozen cell {cell_id}: {field}"
                )
        cell_identity = row.get(
            "generation_cell_identity_sha256",
            row.get("cell_identity_sha256", cell.get("cell_identity_sha256")),
        )
        if cell_identity != frozen_cell.get("cell_identity_sha256"):
            raise ValueError("generated analysis row has a stale cell identity")
        recorded_disposition = _analysis_disposition(row)
        expected_disposition = generation_completion.get("cell_dispositions", {}).get(
            cell_id
        )
        if recorded_disposition != expected_disposition:
            raise ValueError("generated analysis row disagrees with completion disposition")
        raw_vector = row.get("raw_vector", row.get("vector"))
        if raw_vector is None and raw_generated_vectors_by_cell is not None:
            raw_vector = raw_generated_vectors_by_cell.get(cell_id)
        outcome = _normalized_outcome(
            row.get("outcome", row.get("status", row.get("terminal_outcome", "")))
        )
        vector_list = None if raw_vector is None else list(raw_vector)
        if vector_list is not None:
            if outcome != "succeeded":
                raise ValueError("a non-successful generated cell cannot carry an A-vector")
            vector_positions.append(len(generated_parts))
            vectors_to_project.append(vector_list)
        generated_parts.append((row, cell, vector_list))

    projected_by_position: Dict[int, np.ndarray] = {}
    if vectors_to_project:
        projected_matrix = transform_with_pca(
            np.asarray(vectors_to_project, dtype=np.float64), frozen_pca
        )
        projected_by_position = {
            position: projected_matrix[index]
            for index, position in enumerate(vector_positions)
        }

    projected_generated: List[Pilot2ProjectedGeneratedObservation] = []
    for position, (row, cell, raw_vector) in enumerate(generated_parts):
        frozen_cell = cell_index[str(row.get("cell_id", cell.get("cell_id", "")))]

        def value(*names: str, default: Any = None) -> Any:
            for source in (row, cell, frozen_cell):
                for name in names:
                    if name in source:
                        return source[name]
            return default

        target = value("target_artist_id")
        outcome = _normalized_outcome(
            value("outcome", "status", "terminal_outcome", default="")
        )
        projected = projected_by_position.get(position)
        computed_raw_hash = None if raw_vector is None else _vector_sha256(raw_vector)
        recorded_raw_hash = value("raw_feature_sha256")
        if recorded_raw_hash is not None and recorded_raw_hash != computed_raw_hash:
            raise ValueError("generated raw feature hash disagrees with its vector")
        projected_generated.append(
            Pilot2ProjectedGeneratedObservation(
                cell_id=str(value("cell_id", default="")),
                content_id=str(value("content_id", default="")),
                requested_model_label=str(
                    value(
                        "requested_model_label",
                        "requested_model",
                        "model",
                        default="",
                    )
                ),
                repetition=int(value("repetition", default=-1)),
                target_artist_id=None if target is None else str(target),
                artist_free_control=bool(
                    value("artist_free_control", default=target is None)
                ),
                outcome=outcome,
                vector=None if projected is None else projected.tolist(),
                prompt_id=str(value("prompt_id", default="")),
                generation_cell_identity_sha256=str(
                    value(
                        "generation_cell_identity_sha256",
                        "cell_identity_sha256",
                        default="",
                    )
                ),
                output_sha256=(
                    None
                    if value("output_sha256", "decoded_output_sha256", "output_sha")
                    is None
                    else str(
                        value(
                            "output_sha256",
                            "decoded_output_sha256",
                            "output_sha",
                        )
                    )
                ),
                derived_png_sha256=(
                    (
                        derived_png_sha256_by_cell.get(str(value("cell_id")))
                        if derived_png_sha256_by_cell is not None
                        else None
                    )
                    if value("derived_png_sha256", "normalized_output_sha256") is None
                    else str(value("derived_png_sha256", "normalized_output_sha256"))
                ),
                pca_state_sha256=state_sha,
                raw_feature_sha256=computed_raw_hash,
                generation_disposition=_analysis_disposition(row),
                physical_attempt_count=int(
                    value("physical_attempt_count", "attempt_count", default=0)
                ),
            )
        )

    payload: Dict[str, Any] = {
        "record_type": "pilot2_projected_analysis_inputs",
        "schema_version": "2.0",
        "pca_state_sha256": state_sha,
        "projected_dimension": int(frozen_pca.components.shape[0]),
        "bindings": bindings.model_dump(mode="json"),
        "real_observations": [row.model_dump(mode="json") for row in projected_real],
        "generated_observations": [
            row.model_dump(mode="json") for row in projected_generated
        ],
    }
    payload["manifest_sha256"] = _projected_manifest_hash(payload)
    return Pilot2ProjectedAnalysisInputs.model_validate(payload)


def analyze_projected_pilot2(
    config: Pilot2Config,
    projected_inputs: Pilot2ProjectedAnalysisInputs,
    *,
    content_ids: Optional[Sequence[str]] = None,
    prompt_records: Optional[Sequence[Any]] = None,
    protocol_preconditions_met: bool,
    bootstrap_draws: Optional[int] = None,
) -> Pilot2AnalysisResult:
    """Run analysis directly from the compact PCA-projected bridge artifact."""

    payload = projected_inputs.model_dump(mode="json")
    if payload["manifest_sha256"] != _projected_manifest_hash(payload):
        raise ValueError("projected analysis-input manifest hash is stale")
    if config.content_hash() != projected_inputs.bindings.pilot2_config_sha256:
        raise ValueError("analysis config disagrees with the projected-input binding")
    return analyze_pilot2(
        config,
        projected_inputs.real_observations,
        projected_inputs.generated_observations,
        content_ids=content_ids,
        prompt_records=prompt_records,
        protocol_preconditions_met=protocol_preconditions_met,
        projected_input_manifest_sha256=projected_inputs.manifest_sha256,
        bootstrap_draws=bootstrap_draws,
    )


def analyze_requested_label_effects(
    grid: Pilot2GridSpec,
    reference_features: Sequence[Any],
    generated_observations: Sequence[Any],
    *,
    bootstrap_draws: int = 10_000,
    confidence_level: float = 0.95,
    random_seed: int = 20_260_901,
    protocol_preconditions_met: bool,
    projected_input_manifest_sha256: str,
    feature_vectors_by_cell: Optional[Mapping[str, Sequence[float]]] = None,
) -> Pilot2AnalysisResult:
    """Analyze the frozen requested-label grid without a cross-label comparison."""

    if bootstrap_draws < 1:
        raise ValueError("bootstrap_draws must be positive")
    if not 0.0 < confidence_level < 1.0:
        raise ValueError("confidence_level must be between zero and one")
    if random_seed < 0:
        raise ValueError("random_seed must be non-negative")
    if (
        len(projected_input_manifest_sha256) != 64
        or any(
            character not in "0123456789abcdef"
            for character in projected_input_manifest_sha256
        )
    ):
        raise ValueError("projected_input_manifest_sha256 must be a lowercase SHA-256")
    if grid.expected_cell_count != 320 or grid.expected_pair_count != 256:
        raise ValueError("analysis requires the exact frozen 320-cell/256-pair grid")

    references, feature_dimension = _reference_arrays(reference_features, grid)
    observations = _generated_index(
        generated_observations,
        grid,
        feature_dimension,
        feature_vectors_by_cell,
    )
    itt = _itt_summary(grid, observations)
    exact_grid_accounted = bool(
        itt.terminal_cells == itt.expected_cells
        and itt.missing_cells == 0
        and itt.retryable_failure_cells == 0
    )
    feature_grid_complete = itt.complete_feature_pairs == itt.expected_named_control_pairs
    expected_pairs_per_label = (
        len(grid.content_ids) * len(grid.artist_ids) * grid.repetitions
    )
    label_feature_complete = {
        label: (
            itt.by_requested_label[label].complete_feature_pairs
            == expected_pairs_per_label
        )
        for label in grid.requested_labels
    }
    complete_label_indices = [
        index
        for index, label in enumerate(grid.requested_labels)
        if label_feature_complete[label]
    ]
    completion_reasons: List[str] = []
    if not protocol_preconditions_met:
        completion_reasons.append("one or more frozen protocol preconditions were not met")
    if not exact_grid_accounted:
        completion_reasons.append(
            "the exact assignment grid contains missing or still-retryable cells"
        )
    if exact_grid_accounted and not feature_grid_complete:
        completion_reasons.append(
            "terminal refusals, failures, or missing features prevent a complete feature estimand"
        )
    normalized_successes_complete = itt.succeeded_without_feature_cells == 0
    if not normalized_successes_complete:
        completion_reasons.append(
            "one or more successful outputs lacks its normalized projected feature"
        )
    completion = Pilot2ScientificCompletion(
        status=(
            "complete"
            if (
                protocol_preconditions_met
                and exact_grid_accounted
                and normalized_successes_complete
            )
            else "incomplete"
        ),
        protocol_preconditions_met=protocol_preconditions_met,
        exact_assignment_grid_accounted_for=exact_grid_accounted,
        feature_estimand_grid_complete=feature_grid_complete,
        reasons=completion_reasons,
    )

    named, controls = _generated_tensors(grid, observations, feature_dimension)
    contrasts = _contrast_tensor(grid, references, named, controls)

    point_estimates: Dict[Tuple[int, int], Optional[float]] = {}
    source_diagnostics: Dict[Tuple[int, int], Dict[str, Optional[float]]] = {}
    block_estimates: Dict[Tuple[int, int], Dict[str, Optional[float]]] = {}
    raw_p_values: Dict[str, float] = {}
    raw_p_or_none: Dict[Tuple[int, int], Optional[float]] = {}
    for label_index, label in enumerate(grid.requested_labels):
        for estimand_index, estimand in enumerate(PRIMARY_ESTIMANDS):
            values = contrasts[label_index, :, :, :, :, estimand_index]
            primary_values = values[0]
            finite = np.isfinite(primary_values)
            point_estimates[(label_index, estimand_index)] = (
                float(primary_values[finite].mean()) if finite.any() else None
            )
            source_diagnostics[(label_index, estimand_index)] = {
                source: (
                    float(
                        values[source_index + 1][
                            np.isfinite(values[source_index + 1])
                        ].mean()
                    )
                    if np.isfinite(values[source_index + 1]).any()
                    else None
                )
                for source_index, source in enumerate(grid.source_ids)
            }
            blocks: Dict[str, Optional[float]] = {}
            for block_index, content_id in enumerate(grid.content_ids):
                block = primary_values[block_index, :, :]
                blocks[content_id] = (
                    float(block[np.isfinite(block)].mean())
                    if np.isfinite(block).any()
                    else None
                )
            block_estimates[(label_index, estimand_index)] = blocks
            key = f"{label}|{estimand}"
            if label_feature_complete[label]:
                block_vector = [blocks[content_id] for content_id in grid.content_ids]
                assert all(value is not None for value in block_vector)
                raw = exact_block_sign_flip_p_value(
                    [float(value) for value in block_vector if value is not None]
                )
                raw_p_or_none[(label_index, estimand_index)] = raw
                raw_p_values[key] = raw
            else:
                raw_p_or_none[(label_index, estimand_index)] = None
                # Retain the full four-hypothesis family conservatively.
                raw_p_values[key] = 1.0

    adjusted = holm_adjust(raw_p_values)
    bootstrap: Optional[np.ndarray] = None
    if complete_label_indices:
        bootstrap = _bootstrap_primary_estimates(
            grid,
            references,
            named,
            controls,
            draws=bootstrap_draws,
            seed=random_seed,
            complete_label_indices=complete_label_indices,
        )

    estimates: List[Pilot2PrimaryEstimate] = []
    for label_index, label in enumerate(grid.requested_labels):
        label_complete = label_feature_complete[label]
        for estimand_index, estimand in enumerate(PRIMARY_ESTIMANDS):
            source_values = source_diagnostics[(label_index, estimand_index)]
            source_positive = all(
                value is not None and value > 0.0 for value in source_values.values()
            )
            interval = (
                _quantile_interval(
                    bootstrap[:, label_index, estimand_index], confidence_level
                )
                if bootstrap is not None and label_complete
                else None
            )
            familywise_lower = (
                float(
                    np.quantile(
                        bootstrap[:, label_index, estimand_index],
                        (1.0 - confidence_level)
                        / (len(REQUESTED_LABELS) * len(PRIMARY_ESTIMANDS)),
                    )
                )
                if bootstrap is not None and label_complete
                else None
            )
            lower_positive = familywise_lower is not None and familywise_lower > 0.0
            key = f"{label}|{estimand}"
            supported = bool(
                completion.status == "complete"
                and label_complete
                and source_positive
                and lower_positive
                and adjusted[key] < 0.05
            )
            estimates.append(
                Pilot2PrimaryEstimate(
                    requested_model_label=label,
                    estimand=estimand,
                    analysis_population=(
                        "frozen_itt_feature_grid"
                        if label_complete
                        else "available_complete_pairs_descriptive"
                    ),
                    estimate=point_estimates[(label_index, estimand_index)],
                    confidence_interval=interval,
                    familywise_lower_confidence_bound=familywise_lower,
                    source_sign_diagnostics=source_values,
                    content_block_estimates=block_estimates[(label_index, estimand_index)],
                    exact_sign_flip_p_value=raw_p_or_none[(label_index, estimand_index)],
                    holm_adjusted_p_value=adjusted[key],
                    aic_and_nga_positive=source_positive,
                    familywise_lower_confidence_bound_positive=lower_positive,
                    hypothesis_supported=supported,
                    test_status=(
                        "tested"
                        if label_complete
                        else "not_tested_incomplete_feature_grid"
                    ),
                )
            )

    secondary: List[Pilot2ArtistEstimate] = []
    expected_artist_pairs = len(grid.content_ids) * grid.repetitions
    if expected_artist_pairs != 32:
        raise AssertionError("pilot_2 secondary artist grid must contain 32 pairs")
    for label_index, label in enumerate(grid.requested_labels):
        for artist_index, artist_id in enumerate(grid.artist_ids):
            for estimand_index, estimand in enumerate(PRIMARY_ESTIMANDS):
                artist_domains = contrasts[
                    label_index, :, :, :, artist_index, estimand_index
                ]
                pooled = artist_domains[0]
                complete_pairs = int(np.isfinite(pooled).sum())
                secondary.append(
                    Pilot2ArtistEstimate(
                        requested_model_label=label,
                        artist_id=artist_id,
                        estimand=estimand,
                        analysis_population=(
                            "frozen_itt_feature_grid"
                            if complete_pairs == expected_artist_pairs
                            else "available_complete_pairs_descriptive"
                        ),
                        estimate=(
                            float(pooled[np.isfinite(pooled)].mean())
                            if np.isfinite(pooled).any()
                            else None
                        ),
                        source_estimates={
                            source: (
                                float(
                                    artist_domains[source_index + 1][
                                        np.isfinite(
                                            artist_domains[source_index + 1]
                                        )
                                    ].mean()
                                )
                                if np.isfinite(
                                    artist_domains[source_index + 1]
                                ).any()
                                else None
                            )
                            for source_index, source in enumerate(grid.source_ids)
                        },
                        complete_pairs=complete_pairs,
                    )
                )

    support_by_label = {
        label: all(
            row.hypothesis_supported
            for row in estimates
            if row.requested_model_label == label
        )
        for label in grid.requested_labels
    }
    payload: Dict[str, Any] = {
        "record_type": "pilot2_requested_label_analysis",
        "schema_version": "2.0",
        "pilot_id": "pilot_2",
        "analysis_scope": "requested_label_operational_effect",
        "executed_model_claims": False,
        "cross_label_superiority_estimand": False,
        "grid": grid.model_dump(mode="json"),
        "itt": itt.model_dump(mode="json"),
        "scientific_completion": completion.model_dump(mode="json"),
        "estimand_definitions": {
            "distance": (
                "d(g,a)=Euclidean distance in the frozen PCA space from generated "
                "vector g to artist a's held-reference centroid"
            ),
            "target_improvement": (
                "d(control,target)-d(named,target); positive means the name moved "
                "closer to target"
            ),
            "specificity_difference_in_differences": (
                "(d(named,neighbor)-d(named,target))-(d(control,neighbor)-"
                "d(control,target)); positive means target specificity improved "
                "beyond control"
            ),
        },
        "primary_estimates": [row.model_dump(mode="json") for row in estimates],
        "secondary_artist_estimates": [
            row.model_dump(mode="json") for row in secondary
        ],
        "hypothesis_support_by_requested_label": support_by_label,
        "all_four_primary_hypotheses_supported": all(
            row.hypothesis_supported for row in estimates
        ),
        "multiplicity_method": "holm_four_primary_hypotheses",
        "simultaneous_lower_bound_method": (
            "bonferroni_one_sided_four_primary_hypotheses"
        ),
        "familywise_alpha": 0.05,
        "bootstrap_method": (
            "real_work_within_artist_source_then_content_block_then_repetition"
        ),
        "bootstrap_draws": bootstrap_draws,
        "bootstrap_seed": random_seed,
        "confidence_level": confidence_level,
        "projected_input_manifest_sha256": projected_input_manifest_sha256,
        "bootstrap_distribution_sha256": (
            _distribution_sha256(bootstrap) if bootstrap is not None else None
        ),
    }
    payload["result_sha256"] = _result_hash(payload)
    return Pilot2AnalysisResult.model_validate(payload)


def analyze_pilot2(
    config: Pilot2Config,
    reference_features: Sequence[Any],
    generated_observations: Sequence[Any],
    *,
    content_ids: Optional[Sequence[str]] = None,
    prompt_records: Optional[Sequence[Any]] = None,
    protocol_preconditions_met: bool,
    projected_input_manifest_sha256: str,
    feature_vectors_by_cell: Optional[Mapping[str, Sequence[float]]] = None,
    bootstrap_draws: Optional[int] = None,
) -> Pilot2AnalysisResult:
    """Config-bound convenience API used by orchestration and clean-checkout tests."""

    grid = grid_spec_from_config(
        config, content_ids=content_ids, prompt_records=prompt_records
    )
    return analyze_requested_label_effects(
        grid,
        reference_features,
        generated_observations,
        bootstrap_draws=(
            config.analysis.bootstrap_draws
            if bootstrap_draws is None
            else bootstrap_draws
        ),
        confidence_level=config.analysis.confidence_level,
        random_seed=config.analysis.random_seed,
        protocol_preconditions_met=protocol_preconditions_met,
        projected_input_manifest_sha256=projected_input_manifest_sha256,
        feature_vectors_by_cell=feature_vectors_by_cell,
    )


def _chromatic_feature_payload(record: Any) -> Dict[str, Any]:
    outer = _as_mapping(record)
    nested = outer.get("feature", outer.get("chromatic_feature"))
    feature = _as_mapping(nested) if nested is not None else outer

    def value(*names: str, default: Any = None) -> Any:
        for source in (feature, outer):
            for name in names:
                if name in source:
                    return source[name]
        return default

    vector = np.asarray(value("vector", default=[]), dtype=np.float64)
    if vector.shape != (31,) or not np.isfinite(vector).all():
        raise ValueError("pilot_2 chromatic features require S plus 30 histogram values")
    histogram_root = vector[1:]
    if (histogram_root < 0).any() or not np.isclose(
        float(np.square(histogram_root).sum()), 1.0, atol=1e-9
    ):
        raise ValueError("chromatic Hellinger embedding is not a normalized histogram")
    scalars = value("scalars", default={})
    seamlessness = float(scalars.get("seamlessness", vector[0]))
    if not math.isfinite(seamlessness) or not np.isclose(
        seamlessness, float(vector[0]), atol=1e-12
    ):
        raise ValueError("chromatic seamlessness scalar disagrees with its vector")
    payload = {
        "record_id": str(value("record_id", default="")),
        "source_record_id": str(value("source_record_id", default="")),
        "source_png_sha256": str(value("source_png_sha256", default="")),
        "feature_config_sha256": str(value("feature_config_sha256", default="")),
        "feature_version": str(value("feature_version", default="")),
        "seamlessness": seamlessness,
        "histogram_root": histogram_root.tolist(),
    }
    for name in ("source_png_sha256", "feature_config_sha256"):
        digest = payload[name]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"chromatic {name} is not a lowercase SHA-256")
    return payload


def _hellinger(first_root: Sequence[float], second_root: Sequence[float]) -> float:
    first = np.asarray(first_root, dtype=np.float64)
    second = np.asarray(second_root, dtype=np.float64)
    return float(np.linalg.norm(first - second) / math.sqrt(2.0))


def _optional_mean(values: Sequence[float]) -> Optional[float]:
    return float(np.mean(values)) if values else None


def _validate_derived_input_identity(derived: Mapping[str, Any]) -> None:
    required = (
        "derived_input_id",
        "source_record_id",
        "source_sha256",
        "output_sha256",
        "preprocessing_config_sha256",
    )
    if any(not derived.get(name) for name in required):
        raise ValueError("chromatic derived-input evidence is incomplete")
    for name in (
        "source_sha256",
        "output_sha256",
        "preprocessing_config_sha256",
    ):
        digest = str(derived[name])
        if len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError("chromatic derived-input hashes must be lowercase SHA-256")
    identity = stable_hash(
        {
            "source_record_id": derived["source_record_id"],
            "source_sha256": derived["source_sha256"],
            "output_sha256": derived["output_sha256"],
            "preprocessing_config_sha256": derived[
                "preprocessing_config_sha256"
            ],
        }
    )
    if derived["derived_input_id"] != f"pilot2-input-{identity[:24]}":
        raise ValueError("chromatic derived-input identity is stale")


def summarize_chromatic_secondary(
    grid: Pilot2GridSpec,
    real_records: Sequence[Any],
    generated_records: Sequence[Any],
    *,
    bindings: Pilot2AnalysisBindings,
    generation_cells: Sequence[Any],
    generation_completion: Mapping[str, Any],
) -> Pilot2ChromaticSecondaryResult:
    """Produce the frozen, descriptive-only Lee chromatic pilot_2 summary.

    Real rows must join artist/source metadata, their normalized derived input,
    and a chromatic feature. Generated rows must join a successful terminal
    generation record, its normalized derived input, and a chromatic feature.
    This makes the summary executable without allowing it to affect any gate or
    primary hypothesis decision.
    """

    from latent_art_bench.pilot2.chromatic import (
        FEATURE_VERSION,
        LONG_SIDE,
        chromatic_config,
    )
    from latent_art_bench.pilot2.generation import generation_grid_sha256

    if len(generation_cells) != grid.expected_cell_count:
        raise ValueError("chromatic summary requires the exact 320 generation cells")
    grid_hash = generation_grid_sha256(generation_cells)
    if grid_hash != bindings.generation_grid_sha256:
        raise ValueError("chromatic summary generation grid binding is stale")
    if generation_completion.get("generation_grid_sha256") != grid_hash:
        raise ValueError("chromatic completion report binds a different grid")
    completion_sha = generation_completion.get("report_sha256")
    completion_payload = {
        key: value
        for key, value in generation_completion.items()
        if key != "report_sha256"
    }
    if (
        completion_sha != bindings.generation_completion_sha256
        or completion_sha != stable_hash(completion_payload)
    ):
        raise ValueError("chromatic completion report has a stale binding")
    expected_config_sha = stable_hash(
        chromatic_config().model_dump(mode="json", exclude_none=True)
    )
    frozen_cells: Dict[str, Mapping[str, Any]] = {}
    cells_by_assignment: Dict[CellKey, Mapping[str, Any]] = {}
    for raw in generation_cells:
        cell = _as_mapping(raw)
        cell_id = str(cell.get("cell_id", ""))
        if not cell_id or cell_id in frozen_cells:
            raise ValueError("chromatic generation cells must be unique and nonblank")
        frozen_cells[cell_id] = cell
        target = cell.get("target_artist_id")
        assignment = _cell_key(
            str(cell.get("content_id", "")),
            str(cell.get("requested_model_label", "")),
            int(cell.get("repetition", -1)),
            None if target is None else str(target),
        )
        if assignment in cells_by_assignment:
            raise ValueError("chromatic generation assignments must be unique")
        cells_by_assignment[assignment] = cell
    if set(cells_by_assignment) != set(_expected_keys(grid)):
        raise ValueError("chromatic generation cells disagree with the analysis grid")

    real: List[Dict[str, Any]] = []
    real_ids: set[str] = set()
    for raw in real_records:
        row = _as_mapping(raw)
        feature = _chromatic_feature_payload(raw)
        derived_value = row.get("derived_input")
        if derived_value is None:
            raise ValueError("real chromatic rows must bind normalized derived inputs")
        derived = _as_mapping(derived_value)
        _validate_derived_input_identity(derived)
        work_id = str(row.get("canonical_work_id", feature["source_record_id"]))
        artist_id = str(row.get("artist_id", ""))
        source_id = str(row.get("source_id", ""))
        if work_id in real_ids:
            raise ValueError("real chromatic work identifiers must be unique")
        if artist_id not in grid.artist_ids or source_id not in grid.source_ids:
            raise ValueError("real chromatic row lies outside the frozen atlas")
        if (
            feature["source_record_id"] != work_id
            or derived.get("source_record_id") != work_id
            or derived.get("output_sha256") != feature["source_png_sha256"]
        ):
            raise ValueError("real chromatic provenance chain is inconsistent")
        if feature["feature_config_sha256"] != expected_config_sha:
            raise ValueError("real chromatic feature uses a non-frozen configuration")
        if feature["feature_version"] != FEATURE_VERSION:
            raise ValueError("real chromatic feature uses a non-frozen version")
        identity = stable_hash(
            {
                "source_record_id": work_id,
                "source_png_sha256": feature["source_png_sha256"],
                "feature_version": FEATURE_VERSION,
                "feature_config_sha256": expected_config_sha,
                "analysis_long_side": LONG_SIDE,
            }
        )
        if feature["record_id"] != f"pilot2-chromatic-{identity[:24]}":
            raise ValueError("real chromatic feature identity is stale")
        real_ids.add(work_id)
        real.append(
            {
                **feature,
                "canonical_work_id": work_id,
                "artist_id": artist_id,
                "source_id": source_id,
                "derived_png_sha256": str(derived.get("output_sha256", "")),
            }
        )
    if len(real) != 40:
        raise ValueError("chromatic summary requires all 40 frozen real works")

    generated: Dict[str, Dict[str, Any]] = {}
    for raw in generated_records:
        row = _as_mapping(raw)
        feature = _chromatic_feature_payload(raw)
        terminal_value = row.get("terminal_record", row.get("terminal"))
        derived_value = row.get("derived_input")
        if terminal_value is None or derived_value is None:
            raise ValueError(
                "generated chromatic rows must bind terminal and derived-input evidence"
            )
        terminal = _as_mapping(terminal_value)
        derived = _as_mapping(derived_value)
        _validate_derived_input_identity(derived)
        cell_id = str(terminal.get("cell_id", feature["source_record_id"]))
        cell = frozen_cells.get(cell_id)
        if cell is None or cell_id in generated:
            raise ValueError("generated chromatic cell is unknown or duplicated")
        if terminal.get("outcome") != "succeeded":
            raise ValueError("only successful cells may have a chromatic feature")
        if generation_completion.get("cell_dispositions", {}).get(cell_id) != "succeeded":
            raise ValueError("chromatic feature disagrees with completion disposition")
        terminal_sha = terminal.get("terminal_record_sha256")
        terminal_payload = {
            key: value
            for key, value in terminal.items()
            if key != "terminal_record_sha256"
        }
        if (
            terminal.get("record_type") != "pilot2_generation_terminal"
            or terminal.get("executed_model_claims") is not False
            or terminal_sha != stable_hash(terminal_payload)
        ):
            raise ValueError("generated chromatic terminal record is not attested")
        if terminal.get("cell_identity_sha256") != cell.get("cell_identity_sha256"):
            raise ValueError("generated chromatic terminal record has a stale cell identity")
        if (
            feature["source_record_id"] != cell_id
            or derived.get("source_record_id") != cell_id
            or derived.get("source_sha256") != terminal.get("output_sha256")
            or derived.get("output_sha256") != feature["source_png_sha256"]
        ):
            raise ValueError("generated chromatic provenance chain is inconsistent")
        if feature["feature_config_sha256"] != expected_config_sha:
            raise ValueError("generated chromatic feature uses a non-frozen configuration")
        if feature["feature_version"] != FEATURE_VERSION:
            raise ValueError("generated chromatic feature uses a non-frozen version")
        identity = stable_hash(
            {
                "source_record_id": cell_id,
                "source_png_sha256": feature["source_png_sha256"],
                "feature_version": FEATURE_VERSION,
                "feature_config_sha256": expected_config_sha,
                "analysis_long_side": LONG_SIDE,
            }
        )
        if feature["record_id"] != f"pilot2-chromatic-{identity[:24]}":
            raise ValueError("generated chromatic feature identity is stale")
        generated[cell_id] = {**feature, "cell": dict(cell)}

    real_cell_counts = Counter((row["artist_id"], row["source_id"]) for row in real)
    if set(real_cell_counts.values()) != {5} or len(real_cell_counts) != 8:
        raise ValueError("real chromatic atlas must contain five works per artist-by-source")

    artist_histogram_centroids: Dict[str, List[float]] = {}
    for artist_id in grid.artist_ids:
        probabilities = np.asarray(
            [
                np.square(row["histogram_root"])
                for row in real
                if row["artist_id"] == artist_id
            ],
            dtype=np.float64,
        )
        artist_histogram_centroids[artist_id] = np.sqrt(
            probabilities.mean(axis=0)
        ).tolist()

    real_summaries: List[Pilot2ChromaticRealSummary] = []
    for artist_id in grid.artist_ids:
        for source_id in grid.source_ids:
            rows = [
                row
                for row in real
                if row["artist_id"] == artist_id and row["source_id"] == source_id
            ]
            cell_probability = np.asarray(
                [np.square(row["histogram_root"]) for row in rows]
            ).mean(axis=0)
            cell_root = np.sqrt(cell_probability)
            real_summaries.append(
                Pilot2ChromaticRealSummary(
                    artist_id=artist_id,
                    source_id=source_id,
                    mean_seamlessness=float(
                        np.mean([row["seamlessness"] for row in rows])
                    ),
                    mean_histogram_hellinger_to_cell_centroid=float(
                        np.mean(
                            [
                                _hellinger(row["histogram_root"], cell_root)
                                for row in rows
                            ]
                        )
                    ),
                )
            )

    label_summaries: List[Pilot2ChromaticLabelSummary] = []
    artist_summaries: List[Pilot2ChromaticArtistPairSummary] = []
    for label in grid.requested_labels:
        label_features = [
            row
            for row in generated.values()
            if row["cell"]["requested_model_label"] == label
        ]
        named_features = [
            row for row in label_features if not row["cell"]["artist_free_control"]
        ]
        control_features = [
            row for row in label_features if row["cell"]["artist_free_control"]
        ]
        all_deltas: List[float] = []
        all_histogram_distances: List[float] = []
        for artist_id in grid.artist_ids:
            named_values: List[float] = []
            control_values: List[float] = []
            deltas: List[float] = []
            histogram_distances: List[float] = []
            named_to_real: List[float] = []
            control_to_real: List[float] = []
            for content_id in grid.content_ids:
                for repetition in range(grid.repetitions):
                    named_cell = cells_by_assignment[
                        _cell_key(content_id, label, repetition, artist_id)
                    ]
                    control_cell = cells_by_assignment[
                        _cell_key(content_id, label, repetition, None)
                    ]
                    named = generated.get(str(_record_value(named_cell, "cell_id")))
                    control = generated.get(str(_record_value(control_cell, "cell_id")))
                    if named is None or control is None:
                        continue
                    named_values.append(named["seamlessness"])
                    control_values.append(control["seamlessness"])
                    deltas.append(named["seamlessness"] - control["seamlessness"])
                    histogram_distances.append(
                        _hellinger(
                            named["histogram_root"], control["histogram_root"]
                        )
                    )
                    centroid = artist_histogram_centroids[artist_id]
                    named_to_real.append(_hellinger(named["histogram_root"], centroid))
                    control_to_real.append(
                        _hellinger(control["histogram_root"], centroid)
                    )
            all_deltas.extend(deltas)
            all_histogram_distances.extend(histogram_distances)
            artist_summaries.append(
                Pilot2ChromaticArtistPairSummary(
                    requested_model_label=label,
                    artist_id=artist_id,
                    complete_pairs=len(deltas),
                    mean_named_seamlessness=_optional_mean(named_values),
                    mean_matched_control_seamlessness=_optional_mean(control_values),
                    mean_paired_named_minus_control_seamlessness=_optional_mean(deltas),
                    mean_paired_named_control_histogram_hellinger=_optional_mean(
                        histogram_distances
                    ),
                    mean_named_to_real_artist_histogram_hellinger=_optional_mean(
                        named_to_real
                    ),
                    mean_control_to_real_artist_histogram_hellinger=_optional_mean(
                        control_to_real
                    ),
                )
            )
        label_summaries.append(
            Pilot2ChromaticLabelSummary(
                requested_model_label=label,
                named_feature_cells=len(named_features),
                control_feature_cells=len(control_features),
                complete_named_control_pairs=len(all_deltas),
                mean_named_seamlessness=_optional_mean(
                    [row["seamlessness"] for row in named_features]
                ),
                mean_control_seamlessness=_optional_mean(
                    [row["seamlessness"] for row in control_features]
                ),
                mean_paired_named_minus_control_seamlessness=_optional_mean(
                    all_deltas
                ),
                mean_paired_named_control_histogram_hellinger=_optional_mean(
                    all_histogram_distances
                ),
            )
        )

    canonical_real = sorted(real, key=lambda row: row["canonical_work_id"])
    canonical_generated = [
        generated[cell_id]
        for cell_id in [str(_record_value(cell, "cell_id")) for cell in generation_cells]
        if cell_id in generated
    ]
    manifest_sha = stable_hash(
        {
            "bindings": bindings.model_dump(mode="json"),
            "feature_config_sha256": expected_config_sha,
            "real": canonical_real,
            "generated": canonical_generated,
        }
    )
    payload: Dict[str, Any] = {
        "record_type": "pilot2_chromatic_secondary_analysis",
        "schema_version": "2.0",
        "pilot_id": "pilot_2",
        "role": "secondary_descriptive_non_gating",
        "can_open_or_close_generation_gate": False,
        "can_rescue_primary_analysis": False,
        "executed_model_claims": False,
        "cross_label_superiority_estimand": False,
        "bindings": bindings.model_dump(mode="json"),
        "feature_config_sha256": expected_config_sha,
        "chromatic_input_manifest_sha256": manifest_sha,
        "expected_real_features": 40,
        "observed_real_features": 40,
        "expected_generated_cells": 320,
        "observed_generated_features": len(generated),
        "generated_cells_without_chromatic_feature": 320 - len(generated),
        "real_reference_summaries": [
            row.model_dump(mode="json") for row in real_summaries
        ],
        "requested_label_summaries": [
            row.model_dump(mode="json") for row in label_summaries
        ],
        "artist_pair_summaries": [
            row.model_dump(mode="json") for row in artist_summaries
        ],
    }
    payload["result_sha256"] = stable_hash(payload)
    return Pilot2ChromaticSecondaryResult.model_validate(payload)


def chromatic_secondary_json_data(
    result: Pilot2ChromaticSecondaryResult,
) -> Dict[str, Any]:
    payload = result.model_dump(mode="json")
    observed = stable_hash(
        {key: value for key, value in payload.items() if key != "result_sha256"}
    )
    if observed != result.result_sha256:
        raise ValueError("pilot_2 chromatic result hash is stale")
    return payload


def analysis_json_data(result: Pilot2AnalysisResult) -> Dict[str, Any]:
    """Return a JSON-compatible, content-addressed analysis object."""

    payload = result.model_dump(mode="json")
    if payload["result_sha256"] != _result_hash(payload):
        raise ValueError("pilot_2 analysis result hash is stale")
    return payload


def analysis_json_text(result: Pilot2AnalysisResult, *, indent: int = 2) -> str:
    return json.dumps(
        analysis_json_data(result),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
    ) + "\n"


__all__ = [
    "NEIGHBOR_BY_ARTIST",
    "PRIMARY_ESTIMANDS",
    "REQUESTED_LABELS",
    "Pilot2AnalysisBindings",
    "Pilot2AnalysisResult",
    "Pilot2ArtistEstimate",
    "Pilot2ChromaticArtistPairSummary",
    "Pilot2ChromaticLabelSummary",
    "Pilot2ChromaticRealSummary",
    "Pilot2ChromaticSecondaryResult",
    "Pilot2GeneratedObservation",
    "Pilot2GridSpec",
    "Pilot2PrimaryEstimate",
    "Pilot2ProjectedAnalysisInputs",
    "Pilot2ProjectedGeneratedObservation",
    "Pilot2ProjectedRealObservation",
    "Pilot2ReferenceFeature",
    "analysis_json_data",
    "analysis_json_text",
    "assemble_generation_analysis_rows",
    "analyze_pilot2",
    "analyze_projected_pilot2",
    "analyze_requested_label_effects",
    "chromatic_secondary_json_data",
    "exact_block_sign_flip_p_value",
    "grid_spec_from_config",
    "holm_adjust",
    "prepare_projected_analysis_inputs",
    "summarize_chromatic_secondary",
]
