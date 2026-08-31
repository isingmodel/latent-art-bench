"""Prospective pilot-2 generation cells, immutable attempts, and conformance."""

from __future__ import annotations

import base64
import binascii
import fcntl
import io
import json
import os
import tempfile
import threading
import time
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import canonical_json, hash_bytes, hash_file, stable_hash
from latent_art_bench.pilot2.transport import (
    ALLOWED_REQUESTED_MODELS,
    EXECUTED_MODEL_CLAIMS,
    OPERATIONAL_MODEL_ESTIMAND,
    REQUEST_OUTPUT_FORMAT,
    REQUEST_QUALITY,
    REQUEST_SIZE,
    OAuthRuntimeFingerprint,
    OAuthRuntimeRevalidation,
    OAuthTransportConfig,
    Pilot2OAuthTransport,
    RequestedImageModel,
    TransportExchange,
    canonical_image_request_bytes,
    revalidate_oauth_runtime_fingerprint,
    sanitize_external_text,
    verify_oauth_runtime_fingerprint,
)
from latent_art_bench.schemas import PromptRecord

RuntimeRevalidator = Callable[
    [OAuthTransportConfig, OAuthRuntimeFingerprint], OAuthRuntimeRevalidation
]

MAX_PHYSICAL_POSTS_PER_CELL: Literal[10] = 10
FIXED_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0)
RETRYABLE_EXACT_HTTP_STATUSES = frozenset({408, 409, 425, 429})
MIN_OUTPUT_AREA_EXCLUSIVE = 410 * 410
MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE = 2.0
GENERATION_ORDER_NAMESPACE: Literal["pilot2-generation-order-v1"] = (
    "pilot2-generation-order-v1"
)
GENERATION_ORDER_SEED: Literal[20260901] = 20260901
FROZEN_MAX_PARALLEL: Literal[4] = 4
OPERATIONAL_SCOPE_STATEMENT = (
    "Comparisons are between exact requested labels accepted by the local OAuth endpoint; "
    "the transport does not identify or attest the upstream executed model."
)


def _eligible_output_geometry(width: int, height: int) -> bool:
    return (
        width * height > MIN_OUTPUT_AREA_EXCLUSIVE
        and max(width, height) < MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE * min(width, height)
    )

AttemptOutcome = Literal[
    "succeeded", "refused", "retryable_failure", "terminal_failure"
]
CellDisposition = Literal[
    "succeeded",
    "refused",
    "terminal_failure",
    "failed_after_retry_cap",
    "retry_pending",
    "not_attempted",
]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class TransportConformanceFailure(RuntimeError):
    """Raised before the full grid when either requested label fails preflight."""

    def __init__(self, report: Mapping[str, Any]) -> None:
        super().__init__("pilot-2 OAuth transport conformance failed")
        self.report = dict(report)


class GenerationCell(_StrictModel):
    record_type: Literal["pilot2_generation_cell"] = "pilot2_generation_cell"
    schema_version: Literal["2.0"] = "2.0"
    cell_id: str
    prompt_id: str
    content_id: str
    prompt_pair_id: str
    template_id: str
    prompt_text: str
    prompt_sha256: str
    target_artist_id: Optional[str] = None
    target_artist_name: Optional[str] = None
    artist_free_control: bool
    requested_model_label: RequestedImageModel
    repetition: int = Field(ge=0)
    requested_size: Literal["auto"] = REQUEST_SIZE
    requested_quality: Literal["low"] = REQUEST_QUALITY
    requested_output_format: Literal["png"] = REQUEST_OUTPUT_FORMAT
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    executed_model_claims: Literal[False] = EXECUTED_MODEL_CLAIMS
    canonical_request_sha256: str
    cell_identity_sha256: str

    @model_validator(mode="after")
    def identity_is_consistent(self) -> "GenerationCell":
        if self.artist_free_control and (self.target_artist_id or self.target_artist_name):
            raise ValueError("artist-free control cells cannot declare a target artist")
        if not self.artist_free_control and not self.target_artist_id:
            raise ValueError("artist-target cells must declare target_artist_id")
        request = canonical_image_request_bytes(self.prompt_text, self.requested_model_label)
        if hash_bytes(request) != self.canonical_request_sha256:
            raise ValueError("generation cell canonical request hash is stale")
        if hash_bytes(self.prompt_text.encode("utf-8")) != self.prompt_sha256:
            raise ValueError("generation cell prompt hash is stale")
        expected = _cell_identity_payload(self, include_identity=False)
        if stable_hash(expected) != self.cell_identity_sha256:
            raise ValueError("generation cell identity hash is stale")
        if self.cell_id != f"p2cell-{self.cell_identity_sha256[:24]}":
            raise ValueError("generation cell id is not derived from its identity")
        return self


class GenerationPostIntent(_StrictModel):
    """Fsync'd evidence that a single physical POST is about to be attempted."""

    record_type: Literal["pilot2_generation_post_intent"] = (
        "pilot2_generation_post_intent"
    )
    schema_version: Literal["pilot2-generation-post-intent-v1"] = (
        "pilot2-generation-post-intent-v1"
    )
    intent_sequence: int = Field(ge=1)
    attempt_id: str
    cell_id: str
    cell_identity_sha256: str
    attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    requested_model_label: RequestedImageModel
    endpoint: str
    canonical_request_utf8: str
    canonical_request_sha256: str
    canonical_request_byte_count: int = Field(ge=1)
    oauth_runtime_fingerprint_sha256: str
    created_at: datetime
    physical_post_may_have_executed: Literal[True] = True
    post_intent_sha256: str

    @model_validator(mode="after")
    def intent_is_consistent(self) -> "GenerationPostIntent":
        body = self.canonical_request_utf8.encode("utf-8")
        if (
            len(body) != self.canonical_request_byte_count
            or hash_bytes(body) != self.canonical_request_sha256
        ):
            raise ValueError("post intent canonical request bytes are stale")
        try:
            request = json.loads(self.canonical_request_utf8)
        except json.JSONDecodeError as exc:
            raise ValueError("post intent request is not JSON") from exc
        if (
            request.get("model") != self.requested_model_label
            or body
            != canonical_image_request_bytes(
                request.get("prompt"), self.requested_model_label
            )
        ):
            raise ValueError("post intent does not bind the canonical request")
        payload = self.model_dump(mode="json", exclude={"post_intent_sha256"})
        if stable_hash(payload) != self.post_intent_sha256:
            raise ValueError("post intent hash is stale")
        return self

    @field_validator(
        "cell_identity_sha256",
        "canonical_request_sha256",
        "oauth_runtime_fingerprint_sha256",
        "post_intent_sha256",
    )
    @classmethod
    def intent_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("post intent hashes must be lowercase SHA-256")
        return value


class GenerationAttempt(_StrictModel):
    record_type: Literal["pilot2_generation_attempt"] = "pilot2_generation_attempt"
    schema_version: Literal["2.0"] = "2.0"
    attempt_id: str
    cell_id: str
    cell_identity_sha256: str
    attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    post_intent_sequence: int = Field(ge=1)
    post_intent_sha256: str
    requested_model_label: RequestedImageModel
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    executed_model_claims: Literal[False] = EXECUTED_MODEL_CLAIMS
    endpoint: str
    http_method: Literal["POST"] = "POST"
    requested_size: Literal["auto"] = REQUEST_SIZE
    requested_quality: Literal["low"] = REQUEST_QUALITY
    requested_output_format: Literal["png"] = REQUEST_OUTPUT_FORMAT
    canonical_request_utf8: str
    canonical_request_sha256: str
    canonical_request_byte_count: int = Field(ge=1)
    oauth_runtime_fingerprint_sha256: str
    started_at: datetime
    completed_at: datetime
    physical_post_may_have_executed: Literal[True] = True
    post_exchange_observed: bool = True
    outcome: AttemptOutcome
    retry_classification: Literal[
        "not_retryable_success",
        "not_retryable_refusal",
        "retryable_transport",
        "not_retryable_transport",
        "retryable_http_status",
        "not_retryable_http_status",
        "not_retryable_invalid_response",
        "not_retryable_invalid_image",
        "not_retryable_output_error",
        "not_retryable_indeterminate_after_interruption",
    ]
    request_label_accepted: bool
    http_status: Optional[int] = Field(default=None, ge=100, le=599)
    response_body_sha256: Optional[str] = None
    response_body_byte_count: int = Field(default=0, ge=0)
    response_metadata: Dict[str, str] = Field(default_factory=dict)
    failure_kind: Optional[str] = None
    failure_reason: Optional[str] = None
    output_path: Optional[str] = None
    output_sha256: Optional[str] = None
    decoded_output_sha256: Optional[str] = None
    decoded_output_byte_count: Optional[int] = Field(default=None, ge=0)
    actual_width: Optional[int] = Field(default=None, gt=0)
    actual_height: Optional[int] = Field(default=None, gt=0)
    actual_format: Optional[str] = None
    output_format_contract_satisfied: Optional[bool] = None
    exact_dimensions_claimed: Literal[False] = False
    dimension_evidence_scope: Literal[
        "observed_output_only_size_auto_no_exact_dimension_claim"
    ] = "observed_output_only_size_auto_no_exact_dimension_claim"
    revised_prompt: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def attempt_is_internally_consistent(self) -> "GenerationAttempt":
        body = self.canonical_request_utf8.encode("utf-8")
        if len(body) != self.canonical_request_byte_count:
            raise ValueError("canonical request byte count is stale")
        if hash_bytes(body) != self.canonical_request_sha256:
            raise ValueError("canonical request hash is stale")
        try:
            request = json.loads(self.canonical_request_utf8)
        except json.JSONDecodeError as exc:
            raise ValueError("canonical request is not valid JSON") from exc
        if request.get("model") != self.requested_model_label:
            raise ValueError("attempt requested label disagrees with request bytes")
        if body != canonical_image_request_bytes(
            request.get("prompt"), self.requested_model_label
        ):
            raise ValueError("attempt request is not the canonical pilot-2 request")
        if self.outcome == "succeeded":
            required = {
                "output_path": self.output_path,
                "output_sha256": self.output_sha256,
                "decoded_output_sha256": self.decoded_output_sha256,
                "decoded_output_byte_count": self.decoded_output_byte_count,
                "actual_width": self.actual_width,
                "actual_height": self.actual_height,
                "actual_format": self.actual_format,
            }
            if any(value is None for value in required.values()):
                raise ValueError("successful attempt lacks decoded output provenance")
            if self.actual_format != "png" or self.output_format_contract_satisfied is not True:
                raise ValueError("successful attempt must decode as the requested PNG")
            if not self.request_label_accepted:
                raise ValueError("successful attempt must record requested-label acceptance")
            assert self.actual_width is not None and self.actual_height is not None
            if not _eligible_output_geometry(self.actual_width, self.actual_height):
                raise ValueError("successful attempt is outside the frozen image geometry domain")
        if self.retry_classification == "not_retryable_indeterminate_after_interruption":
            if (
                self.outcome != "terminal_failure"
                or self.post_exchange_observed
                or self.request_label_accepted
                or self.http_status is not None
                or self.response_body_sha256 is not None
                or self.failure_kind != "indeterminate_after_interruption"
            ):
                raise ValueError("interrupted-post terminal semantics are inconsistent")
        elif not self.post_exchange_observed:
            raise ValueError("only interrupted posts may lack an observed exchange result")
        if self.decoded_output_sha256 is not None and self.output_sha256 is not None:
            if self.decoded_output_sha256 != self.output_sha256:
                raise ValueError("decoded-output and stored-output hashes disagree")
        return self

    @field_validator(
        "cell_identity_sha256",
        "post_intent_sha256",
        "canonical_request_sha256",
        "oauth_runtime_fingerprint_sha256",
        "response_body_sha256",
        "output_sha256",
        "decoded_output_sha256",
    )
    @classmethod
    def required_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("attempt provenance hashes must be lowercase SHA-256")
        return value


class GenerationAttemptReceipt(_StrictModel):
    """Durable exact row plus the attempt-ledger prefix it must extend."""

    record_type: Literal["pilot2_generation_attempt_receipt"] = (
        "pilot2_generation_attempt_receipt"
    )
    schema_version: Literal["pilot2-generation-attempt-receipt-v1"] = (
        "pilot2-generation-attempt-receipt-v1"
    )
    ledger_row_index: int = Field(ge=0)
    ledger_prefix_semantic_sha256: str
    attempt: GenerationAttempt
    receipt_sha256: str

    @model_validator(mode="after")
    def receipt_is_consistent(self) -> "GenerationAttemptReceipt":
        payload = self.model_dump(mode="json", exclude={"receipt_sha256"})
        if stable_hash(payload) != self.receipt_sha256:
            raise ValueError("generation attempt receipt hash is stale")
        return self

    @field_validator("ledger_prefix_semantic_sha256", "receipt_sha256")
    @classmethod
    def receipt_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("attempt receipt hashes must be lowercase SHA-256")
        return value


class GenerationScheduleEntry(_StrictModel):
    record_type: Literal["pilot2_generation_schedule_entry"] = (
        "pilot2_generation_schedule_entry"
    )
    schema_version: Literal["2.0"] = "2.0"
    cell_id: str
    cell_identity_sha256: str
    content_id: str
    requested_model_label: RequestedImageModel
    repetition: int = Field(ge=0)
    batch_id: str
    batch_rank: int = Field(ge=1)
    within_batch_rank: int = Field(ge=1, le=5)
    scheduled_cell_rank: int = Field(ge=1)
    conformance_preflight_rank: Optional[int] = Field(default=None, ge=1, le=2)


class GenerationSchedule(_StrictModel):
    record_type: Literal["pilot2_generation_schedule"] = "pilot2_generation_schedule"
    schema_version: Literal["2.0"] = "2.0"
    namespace: Literal["pilot2-generation-order-v1"] = GENERATION_ORDER_NAMESPACE
    seed: Literal[20260901] = GENERATION_ORDER_SEED
    max_parallel: Literal[4] = FROZEN_MAX_PARALLEL
    batch_count: int = Field(ge=1)
    cell_count: int = Field(ge=1)
    entries: List[GenerationScheduleEntry]
    schedule_sha256: str

    @model_validator(mode="after")
    def schedule_is_consistent(self) -> "GenerationSchedule":
        if len(self.entries) != self.cell_count:
            raise ValueError("generation schedule cell count is stale")
        if len({entry.cell_id for entry in self.entries}) != self.cell_count:
            raise ValueError("generation schedule cell ids must be unique")
        if [entry.scheduled_cell_rank for entry in self.entries] != list(
            range(1, self.cell_count + 1)
        ):
            raise ValueError("generation schedule ranks must be contiguous")
        if len({entry.batch_id for entry in self.entries}) != self.batch_count:
            raise ValueError("generation schedule batch count is stale")
        batches: Dict[int, List[GenerationScheduleEntry]] = {}
        for entry in self.entries:
            batches.setdefault(entry.batch_rank, []).append(entry)
        if sorted(batches) != list(range(1, self.batch_count + 1)):
            raise ValueError("generation schedule batch ranks must be contiguous")
        for rows in batches.values():
            if len(rows) != 5 or sorted(row.within_batch_rank for row in rows) != list(
                range(1, 6)
            ):
                raise ValueError("every generation schedule batch must contain five cells")
        preflight = sorted(
            entry.conformance_preflight_rank
            for entry in self.entries
            if entry.conformance_preflight_rank is not None
        )
        if preflight != [1, 2]:
            raise ValueError("generation schedule must identify two conformance cells")
        payload = self.model_dump(mode="json", exclude={"schedule_sha256"})
        if stable_hash(payload) != self.schedule_sha256:
            raise ValueError("generation schedule hash is stale")
        return self


RuntimeRevalidationPhase = Literal[
    "start_before_conformance",
    "after_conformance_before_batch",
    "batch_boundary_before_batch",
    "end_after_conformance",
    "end_after_all_batches",
]


class GenerationRuntimeRevalidationRecord(_StrictModel):
    """One fsync'd runtime check bound to the attempt-ledger prefix it observed."""

    record_type: Literal["pilot2_generation_runtime_revalidation"] = (
        "pilot2_generation_runtime_revalidation"
    )
    schema_version: Literal["pilot2-generation-runtime-revalidation-v1"] = (
        "pilot2-generation-runtime-revalidation-v1"
    )
    record_id: str
    ledger_sequence: int = Field(ge=1)
    invocation_id: str
    invocation_sequence: int = Field(ge=1)
    phase: RuntimeRevalidationPhase
    batch_rank: Optional[int] = Field(default=None, ge=1)
    generation_grid_sha256: str
    generation_schedule_sha256: str
    attempt_ledger_row_count: int = Field(ge=0)
    attempt_ledger_semantic_sha256: str
    evidence: OAuthRuntimeRevalidation
    runtime_revalidation_record_sha256: str

    @model_validator(mode="after")
    def record_is_consistent(self) -> "GenerationRuntimeRevalidationRecord":
        is_batch_boundary = self.phase in {
            "after_conformance_before_batch",
            "batch_boundary_before_batch",
        }
        if is_batch_boundary != (self.batch_rank is not None):
            raise ValueError("runtime revalidation batch rank disagrees with phase")
        if self.phase == "after_conformance_before_batch" and self.batch_rank != 1:
            raise ValueError("post-conformance revalidation must precede batch one")
        if self.phase == "batch_boundary_before_batch" and self.batch_rank == 1:
            raise ValueError("batch-one boundary must be the post-conformance phase")
        payload = self.model_dump(
            mode="json", exclude={"runtime_revalidation_record_sha256"}
        )
        if stable_hash(payload) != self.runtime_revalidation_record_sha256:
            raise ValueError("runtime revalidation record hash is stale")
        return self

    @field_validator(
        "generation_grid_sha256",
        "generation_schedule_sha256",
        "attempt_ledger_semantic_sha256",
        "runtime_revalidation_record_sha256",
    )
    @classmethod
    def record_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ValueError("runtime revalidation record hashes must be SHA-256")
        return value


class TerminalGenerationRecord(_StrictModel):
    """Strict one-row analysis handoff for a fully resolved logical cell."""

    record_type: Literal["pilot2_generation_terminal"] = "pilot2_generation_terminal"
    schema_version: Literal["2.0"] = "2.0"
    cell_id: str
    cell_identity_sha256: str
    prompt_id: str
    content_id: str
    prompt_pair_id: str
    target_artist_id: Optional[str] = None
    target_artist_name: Optional[str] = None
    artist_free_control: bool
    requested_model_label: RequestedImageModel
    repetition: int = Field(ge=0)
    outcome: Literal["succeeded", "refused", "terminal_failure"]
    terminal_disposition: Literal["succeeded", "refused", "terminal_failure"]
    retry_cap_exhausted: bool
    attempt_count: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    ledger_attempt_ids: List[str]
    ledger_rows_sha256: str
    source_terminal_attempt_id: str
    source_terminal_attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    source_terminal_attempt_outcome: AttemptOutcome
    physical_post_may_have_executed: Literal[True] = True
    source_post_exchange_observed: bool
    source_failure_kind: Optional[str] = None
    source_failure_reason: Optional[str] = None
    oauth_runtime_fingerprint_sha256: str
    output_path: Optional[str] = None
    output_sha256: Optional[str] = None
    actual_width: Optional[int] = Field(default=None, gt=0)
    actual_height: Optional[int] = Field(default=None, gt=0)
    actual_format: Optional[str] = None
    failure_kind: Optional[str] = None
    failure_reason: Optional[str] = None
    executed_model_claims: Literal[False] = False
    exact_dimensions_claimed: Literal[False] = False
    terminal_record_sha256: str

    @model_validator(mode="after")
    def terminal_record_is_consistent(self) -> "TerminalGenerationRecord":
        if self.outcome != self.terminal_disposition:
            raise ValueError("terminal outcome and disposition disagree")
        if len(self.ledger_attempt_ids) != self.attempt_count:
            raise ValueError("terminal record attempt count is stale")
        if self.source_terminal_attempt_number != self.attempt_count:
            raise ValueError("terminal record does not point at the last attempt")
        if self.retry_cap_exhausted:
            if (
                self.attempt_count != MAX_PHYSICAL_POSTS_PER_CELL
                or self.source_terminal_attempt_outcome != "retryable_failure"
                or self.outcome != "terminal_failure"
            ):
                raise ValueError("retry-cap terminal mapping is inconsistent")
        elif self.source_terminal_attempt_outcome != self.outcome:
            raise ValueError("terminal record changes a non-cap outcome")
        if (
            self.source_failure_kind == "indeterminate_after_interruption"
            and self.source_post_exchange_observed
        ):
            raise ValueError("interrupted terminal record cannot claim observed exchange")
        if self.outcome == "succeeded":
            if not self.output_path or not self.output_sha256 or self.actual_format != "png":
                raise ValueError("successful terminal record lacks PNG output provenance")
            assert self.actual_width is not None and self.actual_height is not None
            if not _eligible_output_geometry(self.actual_width, self.actual_height):
                raise ValueError("successful terminal record has ineligible geometry")
        payload = self.model_dump(mode="json", exclude={"terminal_record_sha256"})
        if stable_hash(payload) != self.terminal_record_sha256:
            raise ValueError("terminal record hash is stale")
        return self

    @field_validator(
        "cell_identity_sha256",
        "ledger_rows_sha256",
        "oauth_runtime_fingerprint_sha256",
        "terminal_record_sha256",
    )
    @classmethod
    def terminal_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("terminal record hashes must be lowercase SHA-256")
        return value


def _cell_identity_payload(
    value: GenerationCell | Mapping[str, Any], *, include_identity: bool
) -> Dict[str, Any]:
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json")
    else:
        payload = dict(value)
    for key in ("record_type", "schema_version", "cell_id"):
        payload.pop(key, None)
    if not include_identity:
        payload.pop("cell_identity_sha256", None)
    return payload


def _make_cell(
    prompt: PromptRecord, requested_model: RequestedImageModel, repetition: int
) -> GenerationCell:
    request = canonical_image_request_bytes(prompt.prompt, requested_model)
    payload: Dict[str, Any] = {
        "prompt_id": prompt.prompt_id,
        "content_id": prompt.content_id,
        "prompt_pair_id": prompt.content_id,
        "template_id": prompt.template_id,
        "prompt_text": prompt.prompt,
        "prompt_sha256": hash_bytes(prompt.prompt.encode("utf-8")),
        "target_artist_id": prompt.target_artist_id,
        "target_artist_name": prompt.target_artist_name,
        "artist_free_control": prompt.artist_free_control,
        "requested_model_label": requested_model,
        "repetition": repetition,
        "requested_size": REQUEST_SIZE,
        "requested_quality": REQUEST_QUALITY,
        "requested_output_format": REQUEST_OUTPUT_FORMAT,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "executed_model_claims": False,
        "canonical_request_sha256": hash_bytes(request),
    }
    identity = stable_hash(payload)
    payload.update(
        {
            "cell_id": f"p2cell-{identity[:24]}",
            "cell_identity_sha256": identity,
        }
    )
    return GenerationCell.model_validate(payload)


def build_generation_cells(
    prompts: Sequence[PromptRecord], *, repetitions: int
) -> List[GenerationCell]:
    """Expand frozen prompts across both and only both requested labels."""

    if repetitions < 1:
        raise ValueError("pilot-2 repetitions must be positive")
    prompt_ids = [prompt.prompt_id for prompt in prompts]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ValueError("pilot-2 prompt ids must be unique")
    cells = [
        _make_cell(prompt, model, repetition)
        for prompt in prompts
        for model in ALLOWED_REQUESTED_MODELS
        for repetition in range(repetitions)
    ]
    validate_generation_cells(cells)
    return cells


def validate_generation_cells(cells: Sequence[GenerationCell]) -> None:
    ids = [cell.cell_id for cell in cells]
    if len(ids) != len(set(ids)):
        raise ValueError("pilot-2 generation cell ids must be unique")
    labels = {cell.requested_model_label for cell in cells}
    if cells and labels != set(ALLOWED_REQUESTED_MODELS):
        raise ValueError("pilot-2 grid must contain exactly gpt-image-1 and gpt-image-2")


def generation_grid_sha256(cells: Sequence[GenerationCell]) -> str:
    validate_generation_cells(cells)
    return stable_hash([cell.model_dump(mode="json") for cell in cells])


def _schedule_digest(*parts: object) -> str:
    material = "|".join(
        [GENERATION_ORDER_NAMESPACE, str(GENERATION_ORDER_SEED), *(str(part) for part in parts)]
    )
    return hash_bytes(material.encode("utf-8"))


def build_generation_schedule(cells: Sequence[GenerationCell]) -> GenerationSchedule:
    """Freeze the SHA-256-keyed order of matched five-cell execution batches."""

    validate_generation_cells(cells)
    grouped: Dict[tuple[str, RequestedImageModel, int], List[GenerationCell]] = {}
    for cell in cells:
        key = (cell.content_id, cell.requested_model_label, cell.repetition)
        grouped.setdefault(key, []).append(cell)
    if not grouped:
        raise ValueError("cannot schedule an empty generation grid")
    target_sets = set()
    for key, rows in grouped.items():
        controls = [row for row in rows if row.artist_free_control]
        targets = frozenset(
            row.target_artist_id for row in rows if not row.artist_free_control
        )
        if len(rows) != 5 or len(controls) != 1 or None in targets or len(targets) != 4:
            raise ValueError(f"schedule batch {key!r} is not one control plus four targets")
        target_sets.add(targets)
    if len(target_sets) != 1:
        raise ValueError("generation schedule target roster changes across batches")

    ordered_batch_keys = sorted(
        grouped,
        key=lambda key: (
            _schedule_digest("batch", key[0], key[1], key[2]),
            key,
        ),
    )
    preflight_by_cell = {
        cell.cell_id: index
        for index, cell in enumerate(select_conformance_cells(cells), start=1)
    }
    entries: List[GenerationScheduleEntry] = []
    scheduled_rank = 0
    for batch_rank, key in enumerate(ordered_batch_keys, start=1):
        content_id, requested_model, repetition = key
        batch_identity = stable_hash(
            {
                "namespace": GENERATION_ORDER_NAMESPACE,
                "seed": GENERATION_ORDER_SEED,
                "content_id": content_id,
                "requested_model_label": requested_model,
                "repetition": repetition,
            }
        )
        batch_id = f"p2batch-{batch_identity[:24]}"
        ordered_cells = sorted(
            grouped[key],
            key=lambda cell: (
                _schedule_digest("within-batch", batch_identity, cell.cell_identity_sha256),
                cell.cell_id,
            ),
        )
        for within_rank, cell in enumerate(ordered_cells, start=1):
            scheduled_rank += 1
            entries.append(
                GenerationScheduleEntry(
                    cell_id=cell.cell_id,
                    cell_identity_sha256=cell.cell_identity_sha256,
                    content_id=content_id,
                    requested_model_label=requested_model,
                    repetition=repetition,
                    batch_id=batch_id,
                    batch_rank=batch_rank,
                    within_batch_rank=within_rank,
                    scheduled_cell_rank=scheduled_rank,
                    conformance_preflight_rank=preflight_by_cell.get(cell.cell_id),
                )
            )
    payload: Dict[str, Any] = {
        "record_type": "pilot2_generation_schedule",
        "schema_version": "2.0",
        "namespace": GENERATION_ORDER_NAMESPACE,
        "seed": GENERATION_ORDER_SEED,
        "max_parallel": FROZEN_MAX_PARALLEL,
        "batch_count": len(ordered_batch_keys),
        "cell_count": len(cells),
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    payload["schedule_sha256"] = stable_hash(payload)
    return GenerationSchedule.model_validate(payload)


class AppendOnlyAttemptLedger:
    """A JSONL ledger that only appends one final row per physical POST."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.sidecar_dir = self.path.parent / f".{self.path.name}.attempt_rows"
        self.recovery_dir = self.path.parent / f".{self.path.name}.recovered_tails"

    @staticmethod
    def _canonical_row_bytes(attempt: GenerationAttempt) -> bytes:
        return (canonical_json(attempt.model_dump(mode="json")) + "\n").encode(
            "utf-8"
        )

    @staticmethod
    def _ledger_semantic_sha256(attempts: Sequence[GenerationAttempt]) -> str:
        return stable_hash(
            [attempt.model_dump(mode="json") for attempt in attempts]
        )

    @staticmethod
    def _canonical_receipt_bytes(receipt: GenerationAttemptReceipt) -> bytes:
        return (canonical_json(receipt.model_dump(mode="json")) + "\n").encode(
            "utf-8"
        )

    @classmethod
    def _receipt_for_attempt(
        cls,
        attempt: GenerationAttempt,
        prior_attempts: Sequence[GenerationAttempt],
    ) -> GenerationAttemptReceipt:
        payload: Dict[str, Any] = {
            "record_type": "pilot2_generation_attempt_receipt",
            "schema_version": "pilot2-generation-attempt-receipt-v1",
            "ledger_row_index": len(prior_attempts),
            "ledger_prefix_semantic_sha256": cls._ledger_semantic_sha256(
                prior_attempts
            ),
            "attempt": attempt.model_dump(mode="json"),
        }
        payload["receipt_sha256"] = stable_hash(payload)
        return GenerationAttemptReceipt.model_validate(payload)

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _write_attempt_sidecar(
        self,
        attempt: GenerationAttempt,
        prior_attempts: Sequence[GenerationAttempt],
    ) -> Path:
        self.sidecar_dir.mkdir(parents=True, exist_ok=True)
        path = self.sidecar_dir / f"{attempt.attempt_id}.json"
        expected = self._canonical_receipt_bytes(
            self._receipt_for_attempt(attempt, prior_attempts)
        )
        if path.exists():
            if path.read_bytes() != expected:
                raise RuntimeError(f"attempt sidecar collision: {path}")
            return path
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=str(self.sidecar_dir)
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(expected)
                handle.flush()
                os.fsync(handle.fileno())
            if path.exists():
                if path.read_bytes() != expected:
                    raise RuntimeError(f"attempt sidecar collision: {path}")
                os.unlink(temporary)
            else:
                os.replace(temporary, path)
                self._fsync_directory(self.sidecar_dir)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return path

    def _write_recovery_evidence(self, path: Path, value: bytes) -> None:
        if path.exists():
            if path.read_bytes() != value:
                raise RuntimeError("torn-tail recovery evidence collision")
            return
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=str(path.parent)
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            if path.exists():
                if path.read_bytes() != value:
                    raise RuntimeError("torn-tail recovery evidence collision")
                os.unlink(temporary)
            else:
                os.replace(temporary, path)
                self._fsync_directory(path.parent)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def _sidecar_receipts(self) -> List[GenerationAttemptReceipt]:
        if not self.sidecar_dir.is_dir():
            return []
        receipts: List[GenerationAttemptReceipt] = []
        for path in sorted(self.sidecar_dir.glob("p2attempt-*.json")):
            try:
                raw = path.read_bytes()
                receipt = GenerationAttemptReceipt.model_validate_json(
                    raw.decode("utf-8")
                )
            except (UnicodeDecodeError, ValueError) as exc:
                raise ValueError(f"invalid durable attempt sidecar {path}: {exc}") from exc
            if path.name != f"{receipt.attempt.attempt_id}.json":
                raise ValueError(
                    f"durable attempt sidecar filename disagrees with payload: {path}"
                )
            if raw != self._canonical_receipt_bytes(receipt):
                raise ValueError(f"durable attempt sidecar is not canonical: {path}")
            receipts.append(receipt)
        ids = [receipt.attempt.attempt_id for receipt in receipts]
        if len(ids) != len(set(ids)):
            raise ValueError("durable attempt sidecars contain duplicate ids")
        return receipts

    def _verify_sidecar_prefixes(
        self,
        attempts: Sequence[GenerationAttempt],
        receipts: Sequence[GenerationAttemptReceipt],
        *,
        allow_one_final_missing_row: bool,
    ) -> Optional[GenerationAttemptReceipt]:
        receipt_by_id = {
            receipt.attempt.attempt_id: receipt for receipt in receipts
        }
        attempt_ids = {attempt.attempt_id for attempt in attempts}
        for index, attempt in enumerate(attempts):
            receipt = receipt_by_id.get(attempt.attempt_id)
            if receipt is None:
                raise RuntimeError(
                    "durable attempt sidecars do not cover the exact ledger"
                )
            if (
                receipt.attempt.model_dump(mode="json")
                != attempt.model_dump(mode="json")
                or receipt.ledger_row_index != index
                or receipt.ledger_prefix_semantic_sha256
                != self._ledger_semantic_sha256(attempts[:index])
            ):
                raise RuntimeError(
                    "durable attempt receipt disagrees with ledger prefix: "
                    f"{attempt.attempt_id}"
                )
        extras = [
            receipt
            for receipt in receipts
            if receipt.attempt.attempt_id not in attempt_ids
        ]
        if not extras:
            return None
        if not allow_one_final_missing_row or len(extras) != 1:
            raise RuntimeError(
                "durable attempt sidecars do not cover the exact ledger"
            )
        missing = extras[0]
        if (
            missing.ledger_row_index != len(attempts)
            or missing.ledger_prefix_semantic_sha256
            != self._ledger_semantic_sha256(attempts)
        ):
            raise RuntimeError(
                "missing durable attempt row is not the exact final append"
            )
        return missing

    def verify_sidecars(self, attempts: Sequence[GenerationAttempt]) -> None:
        self._verify_sidecar_prefixes(
            attempts,
            self._sidecar_receipts(),
            allow_one_final_missing_row=False,
        )

    def recover_from_sidecars(
        self, post_intent_ledger: AppendOnlyPostIntentLedger
    ) -> List[str]:
        """Recover only a missing/torn final append backed by an exact durable row."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        recovered: List[str] = []
        try:
            with os.fdopen(descriptor, "r+b") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0)
                raw = handle.read()
                trailing = b""
                valid_prefix = raw
                if raw and not raw.endswith(b"\n"):
                    newline = raw.rfind(b"\n")
                    valid_prefix = raw[: newline + 1] if newline >= 0 else b""
                    trailing = raw[newline + 1 :]
                    try:
                        GenerationAttempt.model_validate_json(trailing.decode("utf-8"))
                    except (UnicodeDecodeError, ValueError):
                        pass
                    else:
                        handle.seek(0, os.SEEK_END)
                        handle.write(b"\n")
                        handle.flush()
                        os.fsync(handle.fileno())
                        raw += b"\n"
                        valid_prefix = raw
                        trailing = b""
                try:
                    existing = self._validated_rows_from_text(
                        valid_prefix.decode("utf-8"), self.path
                    )
                except (UnicodeDecodeError, ValueError) as exc:
                    raise RuntimeError(
                        "attempt ledger damage is not a recoverable trailing partial"
                    ) from exc
                intents = {
                    intent.attempt_id: intent for intent in post_intent_ledger.rows()
                }
                receipts = self._sidecar_receipts()
                missing_receipt = self._verify_sidecar_prefixes(
                    existing,
                    receipts,
                    allow_one_final_missing_row=True,
                )
                missing = (
                    [missing_receipt.attempt]
                    if missing_receipt is not None
                    else []
                )
                if trailing:
                    candidates = [
                        row
                        for row in missing
                        if self._canonical_row_bytes(row).startswith(trailing)
                        and row.attempt_id in intents
                        and row.post_intent_sha256
                        == intents[row.attempt_id].post_intent_sha256
                    ]
                    if len(candidates) != 1:
                        raise RuntimeError(
                            "torn attempt tail does not match exactly one durable "
                            "intent-backed row"
                        )
                    self.recovery_dir.mkdir(parents=True, exist_ok=True)
                    tail_hash = hash_bytes(trailing)
                    recovery_path = self.recovery_dir / f"{tail_hash}.partial"
                    self._write_recovery_evidence(recovery_path, trailing)
                    handle.seek(0)
                    handle.truncate(len(valid_prefix))
                    handle.flush()
                    os.fsync(handle.fileno())
                    missing = candidates
                for row in missing:
                    intent = intents.get(row.attempt_id)
                    if (
                        intent is None
                        or row.post_intent_sha256 != intent.post_intent_sha256
                        or row.post_intent_sequence != intent.intent_sequence
                    ):
                        raise RuntimeError(
                            "durable attempt sidecar lacks its matching post intent"
                        )
                    handle.seek(0)
                    current_text = handle.read().decode("utf-8")
                    current = self._validated_rows_from_text(current_text, self.path)
                    coordinate = (row.cell_id, row.attempt_number)
                    if coordinate in {
                        (attempt.cell_id, attempt.attempt_number) for attempt in current
                    }:
                        raise RuntimeError("attempt recovery would overwrite a valid row")
                    prior = sorted(
                        (
                            attempt
                            for attempt in current
                            if attempt.cell_id == row.cell_id
                        ),
                        key=lambda attempt: attempt.attempt_number,
                    )
                    if (
                        row.attempt_number != len(prior) + 1
                        or (prior and prior[-1].outcome != "retryable_failure")
                    ):
                        raise RuntimeError("durable attempt row is not safely appendable")
                    handle.seek(0, os.SEEK_END)
                    handle.write(self._canonical_row_bytes(row))
                    handle.flush()
                    os.fsync(handle.fileno())
                    recovered.append(row.attempt_id)
                handle.seek(0)
                final = self._validated_rows_from_text(
                    handle.read().decode("utf-8"), self.path
                )
                self._verify_sidecar_prefixes(
                    final,
                    receipts,
                    allow_one_final_missing_row=False,
                )
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except BaseException:
            raise
        return recovered

    @staticmethod
    def _validated_rows_from_text(text: str, source: Path) -> List[GenerationAttempt]:
        rows: List[GenerationAttempt] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(GenerationAttempt.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(f"{source}:{line_number}: invalid attempt row: {exc}") from exc
        ids = [row.attempt_id for row in rows]
        coordinates = [(row.cell_id, row.attempt_number) for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{source}: duplicate attempt_id")
        if len(coordinates) != len(set(coordinates)):
            raise ValueError(f"{source}: duplicate cell attempt number")
        return rows

    def rows(self) -> List[GenerationAttempt]:
        if not self.path.exists():
            return []
        return self._validated_rows_from_text(self.path.read_text(encoding="utf-8"), self.path)

    def append(self, attempt: GenerationAttempt) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0)
                existing = self._validated_rows_from_text(handle.read(), self.path)
                # A durable receipt without its row means a prior append may have
                # crashed. Reconcile it before allowing any later append.
                self._verify_sidecar_prefixes(
                    existing,
                    self._sidecar_receipts(),
                    allow_one_final_missing_row=False,
                )
                if attempt.attempt_id in {row.attempt_id for row in existing}:
                    raise ValueError(f"attempt already exists: {attempt.attempt_id}")
                coordinate = (attempt.cell_id, attempt.attempt_number)
                if coordinate in {(row.cell_id, row.attempt_number) for row in existing}:
                    raise ValueError(f"cell attempt number already exists: {coordinate}")
                prior_for_cell = sorted(
                    (row for row in existing if row.cell_id == attempt.cell_id),
                    key=lambda row: row.attempt_number,
                )
                if prior_for_cell and prior_for_cell[-1].outcome != "retryable_failure":
                    raise ValueError(
                        f"cannot append after terminal attempt for {attempt.cell_id}"
                    )
                if attempt.attempt_number != len(prior_for_cell) + 1:
                    raise ValueError(
                        f"attempt number is not contiguous for {attempt.cell_id}"
                    )
                self._write_attempt_sidecar(attempt, existing)
                handle.seek(0, os.SEEK_END)
                handle.write(canonical_json(attempt.model_dump(mode="json")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except BaseException:
            # fdopen owns and closes the descriptor on every path.
            raise

    def for_cell(self, cell_id: str) -> List[GenerationAttempt]:
        return sorted(
            (row for row in self.rows() if row.cell_id == cell_id),
            key=lambda row: row.attempt_number,
        )


class AppendOnlyPostIntentLedger:
    """Append-only pre-send journal; each row is durable before its physical POST."""

    _creation_lock = threading.Lock()

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @staticmethod
    def _validated_rows_from_text(
        text: str, source: Path
    ) -> List[GenerationPostIntent]:
        rows: List[GenerationPostIntent] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(GenerationPostIntent.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(
                    f"{source}:{line_number}: invalid post intent: {exc}"
                ) from exc
        if [row.intent_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"{source}: post-intent sequence is not contiguous")
        attempt_ids = [row.attempt_id for row in rows]
        coordinates = [(row.cell_id, row.attempt_number) for row in rows]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError(f"{source}: duplicate post-intent attempt_id")
        if len(coordinates) != len(set(coordinates)):
            raise ValueError(f"{source}: duplicate post-intent cell attempt number")
        return rows

    def rows(self) -> List[GenerationPostIntent]:
        if not self.path.exists():
            return []
        return self._validated_rows_from_text(
            self.path.read_text(encoding="utf-8"), self.path
        )

    def append(self, intent: GenerationPostIntent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0)
                existing = self._validated_rows_from_text(handle.read(), self.path)
                if intent.intent_sequence != len(existing) + 1:
                    raise ValueError("post-intent sequence is stale")
                if intent.attempt_id in {row.attempt_id for row in existing}:
                    raise ValueError(f"post intent already exists: {intent.attempt_id}")
                coordinate = (intent.cell_id, intent.attempt_number)
                if coordinate in {
                    (row.cell_id, row.attempt_number) for row in existing
                }:
                    raise ValueError(
                        f"post intent cell attempt number already exists: {coordinate}"
                    )
                handle.seek(0, os.SEEK_END)
                handle.write(canonical_json(intent.model_dump(mode="json")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except BaseException:
            raise

    def append_new(self, payload: Mapping[str, Any]) -> GenerationPostIntent:
        """Allocate sequence, self-hash, append, and fsync under one journal lock."""

        forbidden = {"intent_sequence", "post_intent_sha256"}.intersection(payload)
        if forbidden:
            raise ValueError(
                "append_new allocates these post-intent fields: "
                + ", ".join(sorted(forbidden))
            )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._creation_lock:
            descriptor = os.open(
                self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644
            )
            try:
                with os.fdopen(
                    descriptor, "r+", encoding="utf-8", newline="\n"
                ) as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    handle.seek(0)
                    existing = self._validated_rows_from_text(
                        handle.read(), self.path
                    )
                    normalized_payload = {
                        **dict(payload),
                        "intent_sequence": len(existing) + 1,
                    }
                    provisional = GenerationPostIntent.model_construct(
                        **normalized_payload, post_intent_sha256="0" * 64
                    )
                    normalized_payload = provisional.model_dump(
                        mode="json", exclude={"post_intent_sha256"}
                    )
                    normalized_payload["post_intent_sha256"] = stable_hash(
                        normalized_payload
                    )
                    intent = GenerationPostIntent.model_validate(normalized_payload)
                    if intent.attempt_id in {row.attempt_id for row in existing}:
                        raise ValueError(
                            f"post intent already exists: {intent.attempt_id}"
                        )
                    coordinate = (intent.cell_id, intent.attempt_number)
                    if coordinate in {
                        (row.cell_id, row.attempt_number) for row in existing
                    }:
                        raise ValueError(
                            "post intent cell attempt number already exists: "
                            f"{coordinate}"
                        )
                    handle.seek(0, os.SEEK_END)
                    handle.write(
                        canonical_json(intent.model_dump(mode="json")) + "\n"
                    )
                    handle.flush()
                    os.fsync(handle.fileno())
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                    return intent
            except BaseException:
                raise


class AppendOnlyRuntimeRevalidationLedger:
    """Resume-safe JSONL evidence written before requests at each batch boundary."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @staticmethod
    def _validated_rows_from_text(
        text: str, source: Path
    ) -> List[GenerationRuntimeRevalidationRecord]:
        rows: List[GenerationRuntimeRevalidationRecord] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                rows.append(
                    GenerationRuntimeRevalidationRecord.model_validate_json(line)
                )
            except ValueError as exc:
                raise ValueError(
                    f"{source}:{line_number}: invalid runtime revalidation row: {exc}"
                ) from exc
        if [row.ledger_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"{source}: runtime revalidation sequence is not contiguous")
        ids = [row.record_id for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{source}: duplicate runtime revalidation record_id")
        seen_invocations: set[str] = set()
        current_invocation: Optional[str] = None
        invocation_sequence = 0
        for row in rows:
            if row.invocation_id != current_invocation:
                if row.invocation_id in seen_invocations:
                    raise ValueError(
                        f"{source}: runtime revalidation invocation is non-contiguous"
                    )
                seen_invocations.add(row.invocation_id)
                current_invocation = row.invocation_id
                invocation_sequence = 0
            invocation_sequence += 1
            if row.invocation_sequence != invocation_sequence:
                raise ValueError(
                    f"{source}: invocation-local revalidation sequence is stale"
                )
        return rows

    def rows(self) -> List[GenerationRuntimeRevalidationRecord]:
        if not self.path.exists():
            return []
        return self._validated_rows_from_text(
            self.path.read_text(encoding="utf-8"), self.path
        )

    def append(self, record: GenerationRuntimeRevalidationRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                handle.seek(0)
                existing = self._validated_rows_from_text(handle.read(), self.path)
                if record.ledger_sequence != len(existing) + 1:
                    raise ValueError("runtime revalidation ledger sequence is stale")
                if existing:
                    prior = existing[-1]
                    prior_invocation_ids = {row.invocation_id for row in existing}
                    if record.invocation_id == prior.invocation_id:
                        expected_invocation_sequence = prior.invocation_sequence + 1
                    else:
                        if record.invocation_id in prior_invocation_ids:
                            raise ValueError(
                                "runtime revalidation invocation is non-contiguous"
                            )
                        expected_invocation_sequence = 1
                    if record.invocation_sequence != expected_invocation_sequence:
                        raise ValueError(
                            "runtime revalidation invocation sequence is stale"
                        )
                    if (
                        record.generation_grid_sha256 != prior.generation_grid_sha256
                        or record.generation_schedule_sha256
                        != prior.generation_schedule_sha256
                        or record.evidence.persisted_fingerprint_sha256
                        != prior.evidence.persisted_fingerprint_sha256
                    ):
                        raise ValueError(
                            "runtime revalidation ledger spans frozen execution identities"
                        )
                elif record.invocation_sequence != 1:
                    raise ValueError(
                        "first runtime revalidation invocation sequence must be one"
                    )
                handle.seek(0, os.SEEK_END)
                handle.write(canonical_json(record.model_dump(mode="json")) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except BaseException:
            raise


def _retryable_http_status(status: int) -> bool:
    return status in RETRYABLE_EXACT_HTTP_STATUSES or 500 <= status <= 599


def _response_error(body: bytes) -> tuple[str, str]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "http_error", "HTTP response did not contain a JSON error object"
    error: Any = value.get("error", value) if isinstance(value, dict) else value
    if isinstance(error, dict):
        code = str(error.get("code") or error.get("type") or "http_error")
        message = str(error.get("message") or code)
    else:
        code = "http_error"
        message = str(error)
    return sanitize_external_text(code, 200), sanitize_external_text(message, 1000)


def _is_refusal(code: str, message: str) -> bool:
    combined = f"{code} {message}".lower()
    return any(
        term in combined
        for term in ("content_policy", "content filter", "moderation", "safety", "refusal")
    )


def _numeric_usage(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        return {str(key): _numeric_usage(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_numeric_usage(item) for item in value]
    return None


def _store_content_addressed(
    output_dir: Path, image_bytes: bytes, image_format: str
) -> tuple[Path, str]:
    digest = hash_bytes(image_bytes)
    suffix = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}.get(image_format, ".bin")
    path = output_dir.resolve() / "sha256" / digest[:2] / f"{digest}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        if hash_file(path) != digest:
            raise RuntimeError(f"content-address collision at {path}")
    else:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(image_bytes)
            handle.flush()
            os.fsync(handle.fileno())
    return path, digest


def _base_attempt(
    cell: GenerationCell,
    intent: GenerationPostIntent,
    transport: Pilot2OAuthTransport,
    fingerprint: OAuthRuntimeFingerprint,
    exchange: TransportExchange,
) -> Dict[str, Any]:
    request = canonical_image_request_bytes(cell.prompt_text, cell.requested_model_label)
    return {
        "attempt_id": intent.attempt_id,
        "cell_id": cell.cell_id,
        "cell_identity_sha256": cell.cell_identity_sha256,
        "attempt_number": intent.attempt_number,
        "post_intent_sequence": intent.intent_sequence,
        "post_intent_sha256": intent.post_intent_sha256,
        "requested_model_label": cell.requested_model_label,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "executed_model_claims": False,
        "endpoint": transport.config.endpoint_url,
        "http_method": "POST",
        "requested_size": REQUEST_SIZE,
        "requested_quality": REQUEST_QUALITY,
        "requested_output_format": REQUEST_OUTPUT_FORMAT,
        "canonical_request_utf8": request.decode("utf-8"),
        "canonical_request_sha256": hash_bytes(request),
        "canonical_request_byte_count": len(request),
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "started_at": exchange.started_at,
        "completed_at": exchange.completed_at,
        "physical_post_may_have_executed": True,
        "post_exchange_observed": True,
        "http_status": exchange.http_status,
        "response_body_sha256": exchange.response_body_sha256,
        "response_body_byte_count": exchange.response_body_bytes,
        "response_metadata": exchange.response_metadata,
        "exact_dimensions_claimed": False,
        "dimension_evidence_scope": "observed_output_only_size_auto_no_exact_dimension_claim",
    }


def _attempt_from_exchange(
    cell: GenerationCell,
    intent: GenerationPostIntent,
    transport: Pilot2OAuthTransport,
    fingerprint: OAuthRuntimeFingerprint,
    exchange: TransportExchange,
    output_dir: Path,
) -> GenerationAttempt:
    payload = _base_attempt(cell, intent, transport, fingerprint, exchange)
    if exchange.transport_error_kind is not None:
        retryable = exchange.transport_error_retryable is True
        payload.update(
            {
                "outcome": "retryable_failure" if retryable else "terminal_failure",
                "retry_classification": (
                    "retryable_transport" if retryable else "not_retryable_transport"
                ),
                "request_label_accepted": False,
                "failure_kind": exchange.transport_error_kind,
                "failure_reason": exchange.transport_error_reason,
            }
        )
        return GenerationAttempt.model_validate(payload)

    assert exchange.http_status is not None
    if not 200 <= exchange.http_status <= 299:
        code, message = _response_error(exchange.response_body)
        refusal = _is_refusal(code, message)
        retryable = _retryable_http_status(exchange.http_status)
        payload.update(
            {
                "outcome": (
                    "refused"
                    if refusal
                    else "retryable_failure"
                    if retryable
                    else "terminal_failure"
                ),
                "retry_classification": (
                    "not_retryable_refusal"
                    if refusal
                    else "retryable_http_status"
                    if retryable
                    else "not_retryable_http_status"
                ),
                "request_label_accepted": False,
                "failure_kind": code,
                "failure_reason": message,
            }
        )
        return GenerationAttempt.model_validate(payload)

    payload["request_label_accepted"] = True
    try:
        response = json.loads(exchange.response_body.decode("utf-8"))
        item = response["data"][0]
        encoded = item["b64_json"]
        image_bytes = base64.b64decode(encoded, validate=True)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
        TypeError,
        binascii.Error,
    ) as exc:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_response",
                "failure_kind": "invalid_response",
                "failure_reason": sanitize_external_text(
                    f"missing or invalid data[0].b64_json: {exc}"
                ),
            }
        )
        return GenerationAttempt.model_validate(payload)

    decoded_digest = hash_bytes(image_bytes)
    payload.update(
        {
            "decoded_output_sha256": decoded_digest,
            "decoded_output_byte_count": len(image_bytes),
        }
    )

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            width, height = image.size
            image_format = (image.format or "unknown").lower()
    except Exception as exc:
        try:
            invalid_path, _ = _store_content_addressed(output_dir, image_bytes, "unknown")
        except (OSError, RuntimeError):
            invalid_path = None
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "invalid_image",
                "failure_reason": sanitize_external_text(f"{type(exc).__name__}: {exc}"),
                "output_path": str(invalid_path) if invalid_path is not None else None,
                "output_sha256": decoded_digest if invalid_path is not None else None,
            }
        )
        return GenerationAttempt.model_validate(payload)

    try:
        path, digest = _store_content_addressed(output_dir, image_bytes, image_format)
    except (OSError, RuntimeError) as exc:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_output_error",
                "failure_kind": "output_error",
                "failure_reason": sanitize_external_text(f"{type(exc).__name__}: {exc}"),
                "actual_width": width,
                "actual_height": height,
                "actual_format": image_format,
                "output_sha256": hash_bytes(image_bytes),
                "output_format_contract_satisfied": image_format == "png",
            }
        )
        return GenerationAttempt.model_validate(payload)

    response_dict = response if isinstance(response, dict) else {}
    item_dict = item if isinstance(item, dict) else {}
    payload.update(
        {
            "output_path": str(path),
            "output_sha256": digest,
            "actual_width": width,
            "actual_height": height,
            "actual_format": image_format,
            "output_format_contract_satisfied": image_format == "png",
            "revised_prompt": (
                sanitize_external_text(item_dict["revised_prompt"], 4000)
                if isinstance(item_dict.get("revised_prompt"), str)
                else None
            ),
            "usage": (
                _numeric_usage(response_dict.get("usage"))
                if isinstance(response_dict.get("usage"), dict)
                else {}
            ),
        }
    )
    if image_format != "png":
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "output_format_mismatch",
                "failure_reason": f"requested png but decoded {image_format}",
            }
        )
    elif not _eligible_output_geometry(width, height):
        area = width * height
        aspect_ratio = max(width, height) / min(width, height)
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "invalid_image_geometry",
                "failure_reason": (
                    f"decoded PNG is outside the frozen input domain: area={area} "
                    f"must be >{MIN_OUTPUT_AREA_EXCLUSIVE}; aspect_ratio={aspect_ratio:.8g} "
                    f"must be <{MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE:g}"
                ),
            }
        )
    else:
        payload.update(
            {
                "outcome": "succeeded",
                "retry_classification": "not_retryable_success",
            }
        )
    return GenerationAttempt.model_validate(payload)


def _validate_existing_attempts(
    cell: GenerationCell,
    attempts: Sequence[GenerationAttempt],
    fingerprint: OAuthRuntimeFingerprint,
) -> None:
    expected_numbers = list(range(1, len(attempts) + 1))
    if [attempt.attempt_number for attempt in attempts] != expected_numbers:
        raise ValueError(f"attempt sequence for {cell.cell_id} is not contiguous")
    if any(attempt.outcome != "retryable_failure" for attempt in attempts[:-1]):
        raise ValueError(f"attempt exists after a terminal outcome for {cell.cell_id}")
    for attempt in attempts:
        if attempt.cell_identity_sha256 != cell.cell_identity_sha256:
            raise ValueError(f"attempt cell identity is stale for {cell.cell_id}")
        if attempt.requested_model_label != cell.requested_model_label:
            raise ValueError(f"attempt requested label is stale for {cell.cell_id}")
        if attempt.canonical_request_sha256 != cell.canonical_request_sha256:
            raise ValueError(f"attempt request hash is stale for {cell.cell_id}")
        if attempt.oauth_runtime_fingerprint_sha256 != fingerprint.fingerprint_sha256:
            raise ValueError(
                f"cell {cell.cell_id} spans multiple OAuth runtime fingerprints"
            )


def runtime_revalidation_ledger_semantic_sha256(
    records: Sequence[GenerationRuntimeRevalidationRecord],
) -> str:
    """Hash normalized runtime evidence in its immutable append order."""

    return stable_hash([record.model_dump(mode="json") for record in records])


def post_intent_ledger_semantic_sha256(
    intents: Sequence[GenerationPostIntent],
) -> str:
    """Hash every normalized pre-send intent in its immutable append order."""

    return stable_hash([intent.model_dump(mode="json") for intent in intents])


def verified_attempt_receipt_manifest(
    ledger: AppendOnlyAttemptLedger,
    attempts: Sequence[GenerationAttempt],
) -> Dict[str, Any]:
    """Verify durable exact-attempt sidecars and return a byte-free receipt manifest."""

    ledger.verify_sidecars(attempts)
    receipts: List[Dict[str, Any]] = []
    receipt_by_attempt_id = {
        receipt.attempt.attempt_id: receipt
        for receipt in ledger._sidecar_receipts()
    }
    for attempt in sorted(attempts, key=lambda row: row.post_intent_sequence):
        receipt = receipt_by_attempt_id[attempt.attempt_id]
        sidecar_path = ledger.sidecar_dir / f"{attempt.attempt_id}.json"
        receipts.append(
            {
                "post_intent_sequence": attempt.post_intent_sequence,
                "post_intent_sha256": attempt.post_intent_sha256,
                "attempt_id": attempt.attempt_id,
                "cell_id": attempt.cell_id,
                "cell_identity_sha256": attempt.cell_identity_sha256,
                "attempt_number": attempt.attempt_number,
                "sidecar_path": sanitize_external_text(str(sidecar_path), 4096),
                "sidecar_file_sha256": hash_file(sidecar_path),
                "ledger_row_index": receipt.ledger_row_index,
                "ledger_prefix_semantic_sha256": (
                    receipt.ledger_prefix_semantic_sha256
                ),
                "receipt_sha256": receipt.receipt_sha256,
                "attempt_payload_sha256": stable_hash(
                    attempt.model_dump(mode="json")
                ),
                "post_exchange_observed": attempt.post_exchange_observed,
                "physical_post_may_have_executed": (
                    attempt.physical_post_may_have_executed
                ),
            }
        )
    recovered_tails: List[Dict[str, Any]] = []
    if ledger.recovery_dir.is_dir():
        for path in sorted(ledger.recovery_dir.glob("*.partial")):
            file_sha256 = hash_file(path)
            if path.stem != file_sha256:
                raise RuntimeError(f"recovered torn-tail evidence is stale: {path}")
            recovered_tails.append(
                {
                    "path": sanitize_external_text(str(path), 4096),
                    "file_sha256": file_sha256,
                    "byte_count": path.stat().st_size,
                }
            )
    payload: Dict[str, Any] = {
        "record_type": "pilot2_generation_attempt_receipt_manifest",
        "schema_version": "pilot2-generation-attempt-receipts-v1",
        "attempt_receipt_count": len(receipts),
        "receipts": receipts,
        "recovered_tail_count": len(recovered_tails),
        "recovered_tails": recovered_tails,
        "contains_raw_response_body": False,
    }
    payload["attempt_receipt_manifest_sha256"] = stable_hash(payload)
    return payload


def verify_post_intent_attempt_bijection(
    intents: Sequence[GenerationPostIntent],
    attempts: Sequence[GenerationAttempt],
    cells: Sequence[GenerationCell],
    *,
    allow_unmatched: bool = False,
) -> None:
    """Bind each attempt to one prior durable intent and reject blind resends."""

    validate_generation_cells(cells)
    cell_index = {cell.cell_id: cell for cell in cells}
    if [intent.intent_sequence for intent in intents] != list(
        range(1, len(intents) + 1)
    ):
        raise RuntimeError("post-intent order is not contiguous")
    intents_by_attempt = {intent.attempt_id: intent for intent in intents}
    if len(intents_by_attempt) != len(intents):
        raise RuntimeError("post-intent ledger contains duplicate attempt ids")
    attempts_by_id = {attempt.attempt_id: attempt for attempt in attempts}
    if len(attempts_by_id) != len(attempts):
        raise RuntimeError("attempt ledger contains duplicate attempt ids")
    unexpected_attempts = sorted(set(attempts_by_id) - set(intents_by_attempt))
    if unexpected_attempts:
        raise RuntimeError("attempt ledger contains rows without durable post intents")

    intents_by_cell: Dict[str, List[GenerationPostIntent]] = {}
    for intent in intents:
        cell = cell_index.get(intent.cell_id)
        if cell is None:
            raise RuntimeError(f"post intent references unexpected cell: {intent.cell_id}")
        if (
            intent.cell_identity_sha256 != cell.cell_identity_sha256
            or intent.requested_model_label != cell.requested_model_label
            or intent.canonical_request_sha256 != cell.canonical_request_sha256
        ):
            raise RuntimeError(f"post intent disagrees with frozen cell: {intent.cell_id}")
        intents_by_cell.setdefault(intent.cell_id, []).append(intent)
        attempt = attempts_by_id.get(intent.attempt_id)
        if attempt is None:
            continue
        if (
            attempt.post_intent_sequence != intent.intent_sequence
            or attempt.post_intent_sha256 != intent.post_intent_sha256
            or attempt.cell_id != intent.cell_id
            or attempt.cell_identity_sha256 != intent.cell_identity_sha256
            or attempt.attempt_number != intent.attempt_number
            or attempt.requested_model_label != intent.requested_model_label
            or attempt.endpoint != intent.endpoint
            or attempt.canonical_request_utf8 != intent.canonical_request_utf8
            or attempt.canonical_request_sha256 != intent.canonical_request_sha256
            or attempt.canonical_request_byte_count
            != intent.canonical_request_byte_count
            or attempt.oauth_runtime_fingerprint_sha256
            != intent.oauth_runtime_fingerprint_sha256
            or attempt.started_at < intent.created_at
        ):
            raise RuntimeError(
                f"attempt row disagrees with its durable post intent: {attempt.attempt_id}"
            )
    for cell_id, rows in intents_by_cell.items():
        ordered = sorted(rows, key=lambda row: row.attempt_number)
        if [row.attempt_number for row in ordered] != list(
            range(1, len(ordered) + 1)
        ):
            raise RuntimeError(f"post intents are not contiguous for cell: {cell_id}")
        unmatched = [row for row in ordered if row.attempt_id not in attempts_by_id]
        if len(unmatched) > 1 or (unmatched and unmatched[0] is not ordered[-1]):
            raise RuntimeError(f"post-intent resolution order is invalid for cell: {cell_id}")
    unmatched_ids = sorted(set(intents_by_attempt) - set(attempts_by_id))
    if unmatched_ids and not allow_unmatched:
        raise RuntimeError(
            "unmatched post intent requires interruption reconciliation: "
            + ", ".join(unmatched_ids)
        )


def reconcile_unmatched_post_intents(
    cells: Sequence[GenerationCell],
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    fingerprint: OAuthRuntimeFingerprint,
) -> List[GenerationAttempt]:
    """Terminalize interrupted intents without issuing another physical POST."""

    intents = post_intent_ledger.rows()
    attempts = ledger.rows()
    verify_post_intent_attempt_bijection(
        intents, attempts, cells, allow_unmatched=True
    )
    attempts_by_id = {attempt.attempt_id: attempt for attempt in attempts}
    reconciled: List[GenerationAttempt] = []
    for intent in intents:
        if intent.attempt_id in attempts_by_id:
            continue
        if intent.oauth_runtime_fingerprint_sha256 != fingerprint.fingerprint_sha256:
            raise RuntimeError("unmatched post intent binds a different OAuth fingerprint")
        payload: Dict[str, Any] = {
            "record_type": "pilot2_generation_attempt",
            "schema_version": "2.0",
            "attempt_id": intent.attempt_id,
            "cell_id": intent.cell_id,
            "cell_identity_sha256": intent.cell_identity_sha256,
            "attempt_number": intent.attempt_number,
            "post_intent_sequence": intent.intent_sequence,
            "post_intent_sha256": intent.post_intent_sha256,
            "requested_model_label": intent.requested_model_label,
            "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
            "executed_model_claims": False,
            "endpoint": intent.endpoint,
            "http_method": "POST",
            "requested_size": REQUEST_SIZE,
            "requested_quality": REQUEST_QUALITY,
            "requested_output_format": REQUEST_OUTPUT_FORMAT,
            "canonical_request_utf8": intent.canonical_request_utf8,
            "canonical_request_sha256": intent.canonical_request_sha256,
            "canonical_request_byte_count": intent.canonical_request_byte_count,
            "oauth_runtime_fingerprint_sha256": (
                intent.oauth_runtime_fingerprint_sha256
            ),
            "started_at": intent.created_at,
            "completed_at": datetime.now(timezone.utc),
            "physical_post_may_have_executed": True,
            "post_exchange_observed": False,
            "outcome": "terminal_failure",
            "retry_classification": (
                "not_retryable_indeterminate_after_interruption"
            ),
            "request_label_accepted": False,
            "response_body_byte_count": 0,
            "response_metadata": {},
            "failure_kind": "indeterminate_after_interruption",
            "failure_reason": (
                "physical POST may have executed before interruption; no exchange "
                "result or HTTP response was observed; automatic resend prohibited"
            ),
            "exact_dimensions_claimed": False,
            "dimension_evidence_scope": (
                "observed_output_only_size_auto_no_exact_dimension_claim"
            ),
        }
        attempt = GenerationAttempt.model_validate(payload)
        ledger.append(attempt)
        attempts_by_id[attempt.attempt_id] = attempt
        reconciled.append(attempt)
    verify_post_intent_attempt_bijection(
        post_intent_ledger.rows(), ledger.rows(), cells
    )
    return reconciled


def verify_generation_runtime_revalidation_ledger(
    records: Sequence[GenerationRuntimeRevalidationRecord],
    attempts: Sequence[GenerationAttempt],
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    *,
    require_completed_generation: bool = False,
) -> None:
    """Prove every attempt interval follows a persisted pre-request runtime check."""

    validate_generation_cells(cells)
    if schedule.schedule_sha256 != build_generation_schedule(cells).schedule_sha256:
        raise ValueError("runtime evidence is being checked against a stale schedule")
    if not records:
        if attempts:
            raise RuntimeError(
                "attempt ledger exists without persisted runtime revalidation evidence"
            )
        if require_completed_generation:
            raise RuntimeError("completed generation lacks runtime revalidation evidence")
        return
    if [record.ledger_sequence for record in records] != list(
        range(1, len(records) + 1)
    ):
        raise ValueError("runtime revalidation ledger sequence is not contiguous")
    if records[0].attempt_ledger_row_count != 0:
        raise RuntimeError("first runtime revalidation does not bind an empty ledger")

    grid_sha256 = generation_grid_sha256(cells)
    cell_ids_by_batch: Dict[int, set[str]] = {}
    for entry in schedule.entries:
        cell_ids_by_batch.setdefault(entry.batch_rank, set()).add(entry.cell_id)
    conformance_ids = {cell.cell_id for cell in select_conformance_cells(cells)}
    invocation_rows: Dict[str, List[GenerationRuntimeRevalidationRecord]] = {}
    invocation_order: List[str] = []
    prior_count = -1
    fingerprint_hashes: set[str] = set()
    for record in records:
        if (
            record.generation_grid_sha256 != grid_sha256
            or record.generation_schedule_sha256 != schedule.schedule_sha256
        ):
            raise RuntimeError("runtime revalidation evidence binds a different grid")
        count = record.attempt_ledger_row_count
        if count < prior_count or count > len(attempts):
            raise RuntimeError("runtime revalidation attempt count is impossible")
        if record.attempt_ledger_semantic_sha256 != (
            generation_attempt_ledger_semantic_sha256(attempts[:count])
        ):
            raise RuntimeError("runtime revalidation binds a stale attempt-ledger prefix")
        prior_count = count
        fingerprint_hashes.add(record.evidence.persisted_fingerprint_sha256)
        if record.invocation_id not in invocation_rows:
            invocation_order.append(record.invocation_id)
            invocation_rows[record.invocation_id] = []
        invocation_rows[record.invocation_id].append(record)
    if len(fingerprint_hashes) != 1:
        raise RuntimeError("runtime revalidation ledger spans OAuth fingerprints")
    flattened = [
        record
        for invocation_id in invocation_order
        for record in invocation_rows[invocation_id]
    ]
    if list(records) != flattened:
        raise RuntimeError("runtime revalidation invocations are interleaved")

    for rows in invocation_rows.values():
        if rows[0].phase != "start_before_conformance":
            raise RuntimeError("runtime revalidation invocation lacks its start check")
        if [row.invocation_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise RuntimeError("runtime invocation sequence is not contiguous")
        tail = rows[1:]
        if tail and tail[0].phase == "end_after_conformance":
            if len(tail) != 1:
                raise RuntimeError("conformance-only runtime invocation has extra checks")
            continue
        batch_rows = [
            row
            for row in tail
            if row.phase
            in {"after_conformance_before_batch", "batch_boundary_before_batch"}
        ]
        if [row.batch_rank for row in batch_rows] != list(
            range(1, len(batch_rows) + 1)
        ):
            raise RuntimeError("runtime invocation skipped a generation batch boundary")
        ending_rows = [row for row in tail if row.phase == "end_after_all_batches"]
        if ending_rows:
            if (
                len(ending_rows) != 1
                or tail[-1] is not ending_rows[0]
                or len(batch_rows) != schedule.batch_count
            ):
                raise RuntimeError("generation runtime invocation ended before every batch")
        elif len(batch_rows) != len(tail):
            raise RuntimeError("runtime invocation has an invalid phase sequence")

    for index, record in enumerate(records):
        start = record.attempt_ledger_row_count
        end = (
            records[index + 1].attempt_ledger_row_count
            if index + 1 < len(records)
            else len(attempts)
        )
        appended_cell_ids = {attempt.cell_id for attempt in attempts[start:end]}
        if record.phase == "start_before_conformance":
            permitted_cell_ids = conformance_ids
        elif record.batch_rank is not None:
            permitted_cell_ids = cell_ids_by_batch[record.batch_rank]
        else:
            permitted_cell_ids = set()
        if not appended_cell_ids.issubset(permitted_cell_ids):
            raise RuntimeError(
                "attempts were appended without the matching persisted runtime boundary"
            )

    if require_completed_generation:
        final = records[-1]
        if (
            final.phase != "end_after_all_batches"
            or final.attempt_ledger_row_count != len(attempts)
        ):
            raise RuntimeError("generation completion lacks its final runtime check")


def generate_cell(
    cell: GenerationCell,
    *,
    transport: Pilot2OAuthTransport,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    fingerprint: OAuthRuntimeFingerprint,
    output_dir: Path,
    sleep: Callable[[float], None] = time.sleep,
) -> GenerationAttempt:
    """Execute a cell under the fixed ten-POST stopping rule."""

    if not fingerprint.runtime_ready:
        raise ValueError("OAuth runtime fingerprint is not ready for pilot-2 generation")
    verify_oauth_runtime_fingerprint(fingerprint)
    if fingerprint.endpoint_url != transport.config.endpoint_url:
        raise ValueError("runtime fingerprint endpoint differs from generation endpoint")
    existing = ledger.for_cell(cell.cell_id)
    all_intents = post_intent_ledger.rows()
    intents_by_attempt = {intent.attempt_id: intent for intent in all_intents}
    existing_attempt_ids = {attempt.attempt_id for attempt in ledger.rows()}
    unmatched_for_cell = [
        intent
        for intent in all_intents
        if intent.cell_id == cell.cell_id
        and intent.attempt_id not in existing_attempt_ids
    ]
    if unmatched_for_cell:
        raise RuntimeError(
            f"cell {cell.cell_id} has an unreconciled interrupted post intent"
        )
    if any(
        attempt.attempt_id not in intents_by_attempt
        or attempt.post_intent_sha256
        != intents_by_attempt[attempt.attempt_id].post_intent_sha256
        for attempt in existing
    ):
        raise RuntimeError(f"cell {cell.cell_id} attempts lack matching post intents")
    _validate_existing_attempts(cell, existing, fingerprint)
    if existing and existing[-1].outcome != "retryable_failure":
        return existing[-1]
    if len(existing) >= MAX_PHYSICAL_POSTS_PER_CELL:
        return existing[-1]
    if existing:
        required_delay = FIXED_RETRY_DELAYS_SECONDS[len(existing) - 1]
        elapsed = max(
            0.0,
            (datetime.now(timezone.utc) - existing[-1].completed_at).total_seconds(),
        )
        remaining_delay = max(0.0, required_delay - elapsed)
        if remaining_delay > 0:
            sleep(remaining_delay)

    request = canonical_image_request_bytes(cell.prompt_text, cell.requested_model_label)
    for attempt_number in range(len(existing) + 1, MAX_PHYSICAL_POSTS_PER_CELL + 1):
        # Allocation and fsync are atomic under both the in-process lock and
        # the journal's OS file lock. No POST occurs if reservation fails.
        intent = post_intent_ledger.append_new(
            {
                "record_type": "pilot2_generation_post_intent",
                "schema_version": "pilot2-generation-post-intent-v1",
                "attempt_id": f"p2attempt-{uuid.uuid4().hex}",
                "cell_id": cell.cell_id,
                "cell_identity_sha256": cell.cell_identity_sha256,
                "attempt_number": attempt_number,
                "requested_model_label": cell.requested_model_label,
                "endpoint": transport.config.endpoint_url,
                "canonical_request_utf8": request.decode("utf-8"),
                "canonical_request_sha256": hash_bytes(request),
                "canonical_request_byte_count": len(request),
                "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
                "created_at": datetime.now(timezone.utc),
                "physical_post_may_have_executed": True,
            }
        )
        # This is the only physical POST. Pilot2OAuthTransport has no retry loop.
        exchange = transport.post_once(request)
        attempt = _attempt_from_exchange(
            cell, intent, transport, fingerprint, exchange, output_dir
        )
        ledger.append(attempt)
        if attempt.outcome != "retryable_failure":
            return attempt
        if attempt_number < MAX_PHYSICAL_POSTS_PER_CELL:
            sleep(FIXED_RETRY_DELAYS_SECONDS[attempt_number - 1])
    return attempt


def run_generation_grid(
    cells: Sequence[GenerationCell],
    *,
    transport: Pilot2OAuthTransport,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    fingerprint: OAuthRuntimeFingerprint,
    output_dir: Path,
    sleep: Callable[[float], None] = time.sleep,
    max_parallel: int = 4,
    runtime_revalidator: RuntimeRevalidator = revalidate_oauth_runtime_fingerprint,
) -> Dict[str, Any]:
    """Pass preflight, then execute one frozen five-cell batch at a time."""

    validate_generation_cells(cells)
    if max_parallel != FROZEN_MAX_PARALLEL:
        raise ValueError("pilot-2 generation requires frozen max_parallel=4")
    schedule = build_generation_schedule(cells)
    ledger.recover_from_sidecars(post_intent_ledger)
    reconcile_unmatched_post_intents(
        cells, ledger, post_intent_ledger, fingerprint
    )
    ledger.verify_sidecars(ledger.rows())
    verify_post_intent_attempt_bijection(
        post_intent_ledger.rows(), ledger.rows(), cells
    )
    verify_generation_runtime_revalidation_ledger(
        runtime_revalidation_ledger.rows(),
        ledger.rows(),
        cells,
        schedule,
    )
    invocation_id = f"p2runtime-invocation-{uuid.uuid4().hex}"
    invocation_sequence = 0

    def revalidate_runtime(
        phase: str, batch_rank: Optional[int] = None
    ) -> OAuthRuntimeRevalidation:
        nonlocal invocation_sequence
        evidence = runtime_revalidator(transport.config, fingerprint)
        attempts_at_check = ledger.rows()
        existing_records = runtime_revalidation_ledger.rows()
        invocation_sequence += 1
        payload: Dict[str, Any] = {
            "record_type": "pilot2_generation_runtime_revalidation",
            "schema_version": "pilot2-generation-runtime-revalidation-v1",
            "record_id": f"p2runtime-{uuid.uuid4().hex}",
            "ledger_sequence": len(existing_records) + 1,
            "invocation_id": invocation_id,
            "invocation_sequence": invocation_sequence,
            "phase": phase,
            "batch_rank": batch_rank,
            "generation_grid_sha256": generation_grid_sha256(cells),
            "generation_schedule_sha256": schedule.schedule_sha256,
            "attempt_ledger_row_count": len(attempts_at_check),
            "attempt_ledger_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(attempts_at_check)
            ),
            "evidence": evidence.model_dump(mode="json"),
        }
        payload["runtime_revalidation_record_sha256"] = stable_hash(payload)
        runtime_revalidation_ledger.append(
            GenerationRuntimeRevalidationRecord.model_validate(payload)
        )
        return evidence

    revalidate_runtime("start_before_conformance")
    conformance_cells = select_conformance_cells(cells)
    for cell in conformance_cells:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            fingerprint=fingerprint,
            output_dir=output_dir,
            sleep=sleep,
        )
    conformance = verify_transport_conformance(
        conformance_cells, ledger.rows(), fingerprint
    )
    if conformance["status"] != "pass":
        revalidate_runtime("end_after_conformance")
        raise TransportConformanceFailure(conformance)

    cell_by_id = {cell.cell_id: cell for cell in cells}
    entries_by_batch: Dict[int, List[GenerationScheduleEntry]] = {}
    for entry in schedule.entries:
        entries_by_batch.setdefault(entry.batch_rank, []).append(entry)
    post_conformance_revalidation: Optional[OAuthRuntimeRevalidation] = None
    for batch_rank in range(1, schedule.batch_count + 1):
        boundary_evidence = revalidate_runtime(
            (
                "after_conformance_before_batch"
                if batch_rank == 1
                else "batch_boundary_before_batch"
            ),
            batch_rank,
        )
        if batch_rank == 1:
            post_conformance_revalidation = boundary_evidence
        entries = sorted(
            entries_by_batch[batch_rank], key=lambda entry: entry.within_batch_rank
        )
        # The two preflight cells appear in their frozen batches; generate_cell
        # observes their terminal ledger rows and returns without another POST.
        with ThreadPoolExecutor(max_workers=FROZEN_MAX_PARALLEL) as executor:
            futures = [
                executor.submit(
                    generate_cell,
                    cell_by_id[entry.cell_id],
                    transport=transport,
                    ledger=ledger,
                    post_intent_ledger=post_intent_ledger,
                    fingerprint=fingerprint,
                    output_dir=output_dir,
                    sleep=sleep,
                )
                for entry in entries
            ]
            for future in as_completed(futures):
                future.result()
    final_runtime_revalidation = revalidate_runtime("end_after_all_batches")
    assert post_conformance_revalidation is not None
    final_attempts = ledger.rows()
    all_runtime_revalidation_records = runtime_revalidation_ledger.rows()
    verify_generation_runtime_revalidation_ledger(
        all_runtime_revalidation_records,
        final_attempts,
        cells,
        schedule,
        require_completed_generation=True,
    )
    final_post_intents = post_intent_ledger.rows()
    verify_post_intent_attempt_bijection(
        final_post_intents, final_attempts, cells
    )
    attempt_receipts = verified_attempt_receipt_manifest(ledger, final_attempts)
    report = generation_completion_report(cells, final_attempts)
    report["transport_conformance"] = conformance
    report["generation_schedule"] = schedule.model_dump(mode="json")
    report["generation_schedule_sha256"] = schedule.schedule_sha256
    # The singular compatibility field is the immediate post-conformance check.
    # The ordered records below bind every prospective batch boundary and the
    # final post-execution check.
    report["oauth_runtime_revalidation"] = (
        post_conformance_revalidation.model_dump(mode="json")
    )
    report["oauth_runtime_revalidation_sha256"] = (
        post_conformance_revalidation.revalidation_sha256
    )
    report["oauth_runtime_revalidation_records"] = [
        record.model_dump(mode="json")
        for record in all_runtime_revalidation_records
    ]
    report["oauth_runtime_revalidation_records_sha256"] = stable_hash(
        report["oauth_runtime_revalidation_records"]
    )
    report["oauth_runtime_revalidation_count"] = len(
        all_runtime_revalidation_records
    )
    report["oauth_runtime_revalidation_ledger_semantic_sha256"] = (
        runtime_revalidation_ledger_semantic_sha256(
            all_runtime_revalidation_records
        )
    )
    report["oauth_runtime_revalidation_ledger_file_sha256"] = hash_file(
        runtime_revalidation_ledger.path
    )
    report["oauth_runtime_revalidation_ledger_path"] = sanitize_external_text(
        str(runtime_revalidation_ledger.path), 4096
    )
    report["current_execution_invocation_id"] = invocation_id
    report["post_intent_count"] = len(final_post_intents)
    report["post_intent_ledger_semantic_sha256"] = (
        post_intent_ledger_semantic_sha256(final_post_intents)
    )
    report["post_intent_ledger_file_sha256"] = hash_file(post_intent_ledger.path)
    report["post_intent_ledger_path"] = sanitize_external_text(
        str(post_intent_ledger.path), 4096
    )
    report["attempt_receipt_count"] = attempt_receipts["attempt_receipt_count"]
    report["attempt_receipt_manifest_sha256"] = attempt_receipts[
        "attempt_receipt_manifest_sha256"
    ]
    report["final_oauth_runtime_revalidation_sha256"] = (
        final_runtime_revalidation.revalidation_sha256
    )
    report["max_parallel"] = FROZEN_MAX_PARALLEL
    original_hash = report.pop("report_sha256")
    report["completion_report_without_conformance_sha256"] = original_hash
    report["report_sha256"] = stable_hash(report)
    return report


def _cell_disposition(attempts: Sequence[GenerationAttempt]) -> CellDisposition:
    if not attempts:
        return "not_attempted"
    last = attempts[-1]
    if last.outcome == "succeeded":
        return "succeeded"
    if last.outcome == "refused":
        return "refused"
    if last.outcome == "terminal_failure":
        return "terminal_failure"
    if len(attempts) >= MAX_PHYSICAL_POSTS_PER_CELL:
        return "failed_after_retry_cap"
    return "retry_pending"


def generation_attempt_ledger_semantic_sha256(
    attempts: Sequence[GenerationAttempt],
) -> str:
    """Hash every normalized attempt payload in immutable ledger order."""

    return stable_hash([attempt.model_dump(mode="json") for attempt in attempts])


def _validated_attempts_by_cell(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> Dict[str, List[GenerationAttempt]]:
    """Validate ledger structure while retaining the physical append order separately."""

    validate_generation_cells(cells)
    by_cell: Dict[str, List[GenerationAttempt]] = {cell.cell_id: [] for cell in cells}
    cell_index = {cell.cell_id: cell for cell in cells}
    attempt_ids: set[str] = set()
    runtime_fingerprints: set[str] = set()
    for attempt in attempts:
        if attempt.attempt_id in attempt_ids:
            raise ValueError(f"duplicate attempt id: {attempt.attempt_id}")
        attempt_ids.add(attempt.attempt_id)
        runtime_fingerprints.add(attempt.oauth_runtime_fingerprint_sha256)
        if attempt.cell_id not in by_cell:
            raise ValueError(f"attempt references unexpected cell: {attempt.cell_id}")
        by_cell[attempt.cell_id].append(attempt)
    if len(runtime_fingerprints) > 1:
        raise ValueError("pilot-2 generation grid spans OAuth runtime fingerprints")
    for cell_id, rows in by_cell.items():
        rows.sort(key=lambda row: row.attempt_number)
        if not rows:
            continue
        fingerprints = {row.oauth_runtime_fingerprint_sha256 for row in rows}
        if len(fingerprints) != 1:
            raise ValueError(f"cell spans OAuth runtime fingerprints: {cell_id}")
        if [row.attempt_number for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"attempts are not contiguous: {cell_id}")
        if len(rows) > MAX_PHYSICAL_POSTS_PER_CELL:
            raise ValueError(f"cell exceeds fixed retry cap: {cell_id}")
        if any(row.outcome != "retryable_failure" for row in rows[:-1]):
            raise ValueError(f"attempt exists after terminal outcome: {cell_id}")
        cell = cell_index[cell_id]
        if any(row.cell_identity_sha256 != cell.cell_identity_sha256 for row in rows):
            raise ValueError(f"attempt identity disagrees with cell: {cell_id}")
    return by_cell


def _resolve_recorded_output_path(
    recorded_path: str, output_root: Optional[Path]
) -> Path:
    path = Path(recorded_path)
    if not path.is_absolute() and output_root is not None:
        path = Path(output_root) / path
    return path


def _verify_successful_output_attempt(
    attempt: GenerationAttempt, *, output_root: Optional[Path]
) -> Dict[str, Any]:
    """Verify stored original bytes and return a byte-free canonical evidence row."""

    if attempt.outcome != "succeeded":
        raise ValueError("successful-output verification received a non-success attempt")
    if not attempt.output_path or not attempt.output_sha256:
        raise RuntimeError(
            f"successful output lacks its recorded path/hash: {attempt.cell_id}"
        )
    path = _resolve_recorded_output_path(attempt.output_path, output_root)
    if not path.is_file():
        raise FileNotFoundError(
            f"successful original output is missing for {attempt.cell_id}: {path}"
        )
    observed_sha256 = hash_file(path)
    if observed_sha256 != attempt.output_sha256:
        raise RuntimeError(
            f"successful original output SHA-256 mismatch for {attempt.cell_id}"
        )
    if path.name != f"{attempt.output_sha256}.png":
        raise RuntimeError(
            f"successful original output path is not content-addressed for "
            f"{attempt.cell_id}"
        )
    observed_byte_count = path.stat().st_size
    if (
        attempt.decoded_output_byte_count is not None
        and observed_byte_count != attempt.decoded_output_byte_count
    ):
        raise RuntimeError(
            f"successful original output byte count mismatch for {attempt.cell_id}"
        )
    try:
        with Image.open(path) as image:
            image.load()
            observed_format = (image.format or "unknown").lower()
            observed_width, observed_height = image.size
    except Exception as exc:
        raise RuntimeError(
            f"successful original output does not decode for {attempt.cell_id}: "
            f"{type(exc).__name__}"
        ) from exc
    if observed_format != "png":
        raise RuntimeError(
            f"successful original output is not PNG for {attempt.cell_id}: "
            f"{observed_format}"
        )
    if (observed_width, observed_height) != (
        attempt.actual_width,
        attempt.actual_height,
    ):
        raise RuntimeError(
            f"successful original output dimensions disagree with ledger for "
            f"{attempt.cell_id}"
        )
    if not _eligible_output_geometry(observed_width, observed_height):
        raise RuntimeError(
            f"successful original output geometry is ineligible for {attempt.cell_id}"
        )
    return {
        "cell_id": attempt.cell_id,
        "cell_identity_sha256": attempt.cell_identity_sha256,
        "attempt_id": attempt.attempt_id,
        "attempt_number": attempt.attempt_number,
        "requested_model_label": attempt.requested_model_label,
        "output_path": sanitize_external_text(attempt.output_path, 4096),
        "output_sha256": attempt.output_sha256,
        "output_byte_count": observed_byte_count,
        "width": observed_width,
        "height": observed_height,
        "format": observed_format,
        "eligible_geometry": True,
    }


def verify_successful_output_artifacts(
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    *,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Verify every terminal success and return its sanitized metadata manifest."""

    by_cell = _validated_attempts_by_cell(cells, attempts)
    cell_index = {cell.cell_id: cell for cell in cells}
    outputs: List[Dict[str, Any]] = []
    for cell_id in sorted(by_cell):
        rows = by_cell[cell_id]
        if not rows or rows[-1].outcome != "succeeded":
            continue
        evidence = _verify_successful_output_attempt(
            rows[-1], output_root=output_root
        )
        cell = cell_index[cell_id]
        evidence.update(
            {
                "prompt_id": cell.prompt_id,
                "content_id": cell.content_id,
                "prompt_pair_id": cell.prompt_pair_id,
                "target_artist_id": cell.target_artist_id,
                "artist_free_control": cell.artist_free_control,
                "repetition": cell.repetition,
            }
        )
        outputs.append(evidence)
    payload: Dict[str, Any] = {
        "record_type": "pilot2_successful_output_manifest",
        "schema_version": "pilot2-successful-output-manifest-v1",
        "generation_grid_sha256": generation_grid_sha256(cells),
        "successful_output_count": len(outputs),
        "outputs": outputs,
        "contains_raw_image_bytes": False,
    }
    payload["successful_output_manifest_sha256"] = stable_hash(payload)
    return payload


def generation_completion_report(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> Dict[str, Any]:
    by_cell = _validated_attempts_by_cell(cells, attempts)
    dispositions: Dict[str, CellDisposition] = {}
    for cell_id, rows in by_cell.items():
        dispositions[cell_id] = _cell_disposition(rows)

    disposition_counts = Counter(dispositions.values())
    by_model: Dict[str, Dict[str, int]] = {}
    for model in ALLOWED_REQUESTED_MODELS:
        model_dispositions = Counter(
            dispositions[cell.cell_id]
            for cell in cells
            if cell.requested_model_label == model
        )
        by_model[model] = dict(sorted(model_dispositions.items()))
    all_terminal = all(
        disposition
        in {"succeeded", "refused", "terminal_failure", "failed_after_retry_cap"}
        for disposition in dispositions.values()
    )
    all_succeeded = bool(cells) and all(
        disposition == "succeeded" for disposition in dispositions.values()
    )
    successful_output_manifest = verify_successful_output_artifacts(cells, attempts)
    indeterminate_count = sum(
        attempt.failure_kind == "indeterminate_after_interruption"
        for attempt in attempts
    )
    payload: Dict[str, Any] = {
        "schema_version": "pilot2-generation-completion-v1",
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "scope_statement": OPERATIONAL_SCOPE_STATEMENT,
        "executed_model_claims": False,
        "exact_dimensions_claimed": False,
        "fixed_max_physical_posts_per_cell": MAX_PHYSICAL_POSTS_PER_CELL,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "cell_count": len(cells),
        "attempt_count": len(attempts),
        "attempt_count_semantics": (
            "durable pre-send intents resolved to observed exchanges or conservative "
            "indeterminate-after-interruption terminal rows; not every row proves a send"
        ),
        "post_exchange_observed_attempt_count": sum(
            attempt.post_exchange_observed for attempt in attempts
        ),
        "indeterminate_after_interruption_count": indeterminate_count,
        "attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(attempts)
        ),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "by_requested_model_label": by_model,
        "cell_dispositions": dict(sorted(dispositions.items())),
        "all_cells_terminal": all_terminal,
        "all_cells_succeeded": all_succeeded,
        "analysis_eligible_cell_count": disposition_counts.get("succeeded", 0),
        "analysis_missing_cell_count": len(cells) - disposition_counts.get("succeeded", 0),
        "successful_output_count": successful_output_manifest[
            "successful_output_count"
        ],
        "successful_output_manifest_sha256": successful_output_manifest[
            "successful_output_manifest_sha256"
        ],
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def successful_outputs_by_cell(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> Dict[str, GenerationAttempt]:
    """Return the sole successful output for each resolved logical cell."""

    generation_completion_report(cells, attempts)
    successful: Dict[str, GenerationAttempt] = {}
    for attempt in attempts:
        if attempt.outcome != "succeeded":
            continue
        if attempt.cell_id in successful:
            raise ValueError(f"multiple successful outputs for cell {attempt.cell_id}")
        successful[attempt.cell_id] = attempt
    return successful


def terminal_records_for_analysis(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> List[TerminalGenerationRecord]:
    """Collapse resolved cells to strict analysis rows without changing the ledger."""

    completion = generation_completion_report(cells, attempts)
    if not completion["all_cells_terminal"]:
        unresolved = sorted(
            cell_id
            for cell_id, disposition in completion["cell_dispositions"].items()
            if disposition in {"not_attempted", "retry_pending"}
        )
        raise ValueError(
            "cannot create terminal analysis records for unresolved cells: "
            + ", ".join(unresolved)
        )
    by_cell: Dict[str, List[GenerationAttempt]] = {cell.cell_id: [] for cell in cells}
    for attempt in attempts:
        by_cell[attempt.cell_id].append(attempt)

    terminal_records: List[TerminalGenerationRecord] = []
    for cell in cells:
        rows = sorted(by_cell[cell.cell_id], key=lambda row: row.attempt_number)
        source = rows[-1]
        retry_cap_exhausted = (
            len(rows) == MAX_PHYSICAL_POSTS_PER_CELL
            and source.outcome == "retryable_failure"
        )
        outcome = "terminal_failure" if retry_cap_exhausted else source.outcome
        if outcome == "retryable_failure":  # guarded by all_cells_terminal
            raise AssertionError("retryable outcome escaped terminal completion check")
        failure_kind = "retry_cap_exhausted" if retry_cap_exhausted else source.failure_kind
        failure_reason = (
            "fixed ten-attempt cap exhausted; inspect preserved ledger attempts"
            if retry_cap_exhausted
            else source.failure_reason
        )
        payload: Dict[str, Any] = {
            "record_type": "pilot2_generation_terminal",
            "schema_version": "2.0",
            "cell_id": cell.cell_id,
            "cell_identity_sha256": cell.cell_identity_sha256,
            "prompt_id": cell.prompt_id,
            "content_id": cell.content_id,
            "prompt_pair_id": cell.prompt_pair_id,
            "target_artist_id": cell.target_artist_id,
            "target_artist_name": cell.target_artist_name,
            "artist_free_control": cell.artist_free_control,
            "requested_model_label": cell.requested_model_label,
            "repetition": cell.repetition,
            "outcome": outcome,
            "terminal_disposition": outcome,
            "retry_cap_exhausted": retry_cap_exhausted,
            "attempt_count": len(rows),
            "ledger_attempt_ids": [row.attempt_id for row in rows],
            "ledger_rows_sha256": stable_hash(
                [row.model_dump(mode="json") for row in rows]
            ),
            "source_terminal_attempt_id": source.attempt_id,
            "source_terminal_attempt_number": source.attempt_number,
            "source_terminal_attempt_outcome": source.outcome,
            "physical_post_may_have_executed": (
                source.physical_post_may_have_executed
            ),
            "source_post_exchange_observed": source.post_exchange_observed,
            "source_failure_kind": source.failure_kind,
            "source_failure_reason": source.failure_reason,
            "oauth_runtime_fingerprint_sha256": (
                source.oauth_runtime_fingerprint_sha256
            ),
            "output_path": source.output_path,
            "output_sha256": source.output_sha256,
            "actual_width": source.actual_width,
            "actual_height": source.actual_height,
            "actual_format": source.actual_format,
            "failure_kind": failure_kind,
            "failure_reason": failure_reason,
            "executed_model_claims": False,
            "exact_dimensions_claimed": False,
        }
        payload["terminal_record_sha256"] = stable_hash(payload)
        terminal_records.append(TerminalGenerationRecord.model_validate(payload))
    return terminal_records


def terminal_records_manifest_sha256(
    records: Sequence[TerminalGenerationRecord],
) -> str:
    """Hash the complete terminal handoff in canonical cell-id order."""

    cell_ids = [record.cell_id for record in records]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("terminal-record manifest contains duplicate cell ids")
    ordered = sorted(records, key=lambda record: record.cell_id)
    return stable_hash([record.model_dump(mode="json") for record in ordered])


def _verify_output(attempt: GenerationAttempt) -> bool:
    if attempt.outcome != "succeeded":
        return False
    try:
        _verify_successful_output_attempt(attempt, output_root=None)
    except (FileNotFoundError, RuntimeError, ValueError):
        return False
    return True


def verify_transport_conformance(
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    fingerprint: OAuthRuntimeFingerprint,
) -> Dict[str, Any]:
    """Verify label submission/acceptance and PNG decoding without model overclaim."""

    if len(cells) != len(ALLOWED_REQUESTED_MODELS):
        raise ValueError("conformance requires exactly one cell per requested model label")
    validate_generation_cells(cells)
    if {cell.requested_model_label for cell in cells} != set(ALLOWED_REQUESTED_MODELS):
        raise ValueError("conformance cells do not cover the exact requested labels")
    by_cell: Dict[str, List[GenerationAttempt]] = {cell.cell_id: [] for cell in cells}
    for attempt in attempts:
        if attempt.cell_id in by_cell:
            by_cell[attempt.cell_id].append(attempt)

    model_evidence: Dict[str, Any] = {}
    all_pass = fingerprint.runtime_ready
    for cell in cells:
        rows = sorted(by_cell[cell.cell_id], key=lambda row: row.attempt_number)
        final = rows[-1] if rows else None
        request_submitted = bool(rows) and all(
            json.loads(row.canonical_request_utf8).get("model")
            == cell.requested_model_label
            for row in rows
        )
        accepted = final is not None and final.request_label_accepted
        png_decoded = final is not None and final.outcome == "succeeded" and _verify_output(final)
        passed = bool(request_submitted and accepted and png_decoded)
        all_pass = all_pass and passed
        model_evidence[cell.requested_model_label] = {
            "cell_id": cell.cell_id,
            "physical_post_count": len(rows),
            "exact_requested_label_submitted": request_submitted,
            "requested_label_accepted_by_endpoint": accepted,
            "png_decoded_and_hash_verified": png_decoded,
            "observed_width": final.actual_width if final else None,
            "observed_height": final.actual_height if final else None,
            "exact_dimensions_claimed": False,
            "executed_model_claims": False,
            "status": "pass" if passed else "fail",
        }
    payload: Dict[str, Any] = {
        "schema_version": "pilot2-oauth-conformance-v1",
        "status": "pass" if all_pass else "fail",
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "scope_statement": OPERATIONAL_SCOPE_STATEMENT,
        "executed_model_claims": False,
        "exact_dimensions_claimed": False,
        "requested_size": "auto",
        "requested_quality": "low",
        "requested_output_format": "png",
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "oauth_runtime_ready": fingerprint.runtime_ready,
        "models": model_evidence,
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def conformance_generation_cells() -> List[GenerationCell]:
    prompt = PromptRecord(
        prompt_id="pilot2-oauth-conformance",
        content_id="pilot2-oauth-conformance",
        template_id="pilot2-oauth-conformance-v1",
        prompt=(
            "A simple centered arrangement of three matte geometric forms on a plain "
            "warm-white background, no text, no logo, no signature."
        ),
        artist_free_control=True,
        test_only=True,
    )
    return build_generation_cells([prompt], repetitions=1)


def select_conformance_cells(
    cells: Sequence[GenerationCell],
) -> List[GenerationCell]:
    """Choose the first artist-free repetition-zero cell under each label.

    These are ordinary frozen grid cells. Their successful outputs therefore count
    toward grid completion rather than creating an extra, adaptively discarded pair.
    """

    validate_generation_cells(cells)
    selected: List[GenerationCell] = []
    for model in ALLOWED_REQUESTED_MODELS:
        candidates = sorted(
            (
                cell
                for cell in cells
                if cell.requested_model_label == model
                and cell.artist_free_control
                and cell.repetition == 0
            ),
            key=lambda cell: (cell.content_id, cell.prompt_id, cell.cell_id),
        )
        if not candidates:
            raise ValueError(
                f"no artist-free repetition-zero conformance cell for {model}"
            )
        selected.append(candidates[0])
    return selected


def run_transport_conformance(
    *,
    cells: Sequence[GenerationCell],
    transport: Pilot2OAuthTransport,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    fingerprint: OAuthRuntimeFingerprint,
    output_dir: Path,
    sleep: Callable[[float], None] = time.sleep,
    runtime_revalidator: RuntimeRevalidator = revalidate_oauth_runtime_fingerprint,
) -> Dict[str, Any]:
    schedule = build_generation_schedule(cells)
    ledger.recover_from_sidecars(post_intent_ledger)
    reconcile_unmatched_post_intents(
        cells, ledger, post_intent_ledger, fingerprint
    )
    ledger.verify_sidecars(ledger.rows())
    verify_post_intent_attempt_bijection(
        post_intent_ledger.rows(), ledger.rows(), cells
    )
    verify_generation_runtime_revalidation_ledger(
        runtime_revalidation_ledger.rows(), ledger.rows(), cells, schedule
    )
    invocation_id = f"p2runtime-invocation-{uuid.uuid4().hex}"

    def record_check(
        phase: RuntimeRevalidationPhase,
        invocation_sequence: int,
    ) -> OAuthRuntimeRevalidation:
        evidence = runtime_revalidator(transport.config, fingerprint)
        attempts_at_check = ledger.rows()
        existing_records = runtime_revalidation_ledger.rows()
        payload: Dict[str, Any] = {
            "record_type": "pilot2_generation_runtime_revalidation",
            "schema_version": "pilot2-generation-runtime-revalidation-v1",
            "record_id": f"p2runtime-{uuid.uuid4().hex}",
            "ledger_sequence": len(existing_records) + 1,
            "invocation_id": invocation_id,
            "invocation_sequence": invocation_sequence,
            "phase": phase,
            "batch_rank": None,
            "generation_grid_sha256": generation_grid_sha256(cells),
            "generation_schedule_sha256": schedule.schedule_sha256,
            "attempt_ledger_row_count": len(attempts_at_check),
            "attempt_ledger_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(attempts_at_check)
            ),
            "evidence": evidence.model_dump(mode="json"),
        }
        payload["runtime_revalidation_record_sha256"] = stable_hash(payload)
        runtime_revalidation_ledger.append(
            GenerationRuntimeRevalidationRecord.model_validate(payload)
        )
        return evidence

    runtime_revalidation = record_check("start_before_conformance", 1)
    selected = select_conformance_cells(cells)
    for cell in selected:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            fingerprint=fingerprint,
            output_dir=output_dir,
            sleep=sleep,
        )
    report = verify_transport_conformance(selected, ledger.rows(), fingerprint)
    final_runtime_revalidation = record_check("end_after_conformance", 2)
    all_runtime_revalidation_records = runtime_revalidation_ledger.rows()
    all_post_intents = post_intent_ledger.rows()
    verify_post_intent_attempt_bijection(
        all_post_intents, ledger.rows(), cells
    )
    attempt_receipts = verified_attempt_receipt_manifest(ledger, ledger.rows())
    verify_generation_runtime_revalidation_ledger(
        all_runtime_revalidation_records, ledger.rows(), cells, schedule
    )
    original_hash = report.pop("report_sha256")
    report["conformance_without_revalidation_sha256"] = original_hash
    report["oauth_runtime_revalidation"] = runtime_revalidation.model_dump(mode="json")
    report["oauth_runtime_revalidation_sha256"] = (
        runtime_revalidation.revalidation_sha256
    )
    report["oauth_runtime_revalidation_records"] = [
        record.model_dump(mode="json")
        for record in all_runtime_revalidation_records
    ]
    report["oauth_runtime_revalidation_records_sha256"] = (
        runtime_revalidation_ledger_semantic_sha256(
            all_runtime_revalidation_records
        )
    )
    report["oauth_runtime_revalidation_count"] = len(
        all_runtime_revalidation_records
    )
    report["oauth_runtime_revalidation_ledger_file_sha256"] = hash_file(
        runtime_revalidation_ledger.path
    )
    report["oauth_runtime_revalidation_ledger_path"] = sanitize_external_text(
        str(runtime_revalidation_ledger.path), 4096
    )
    report["final_oauth_runtime_revalidation_sha256"] = (
        final_runtime_revalidation.revalidation_sha256
    )
    report["current_execution_invocation_id"] = invocation_id
    report["post_intent_count"] = len(all_post_intents)
    report["post_intent_ledger_semantic_sha256"] = (
        post_intent_ledger_semantic_sha256(all_post_intents)
    )
    report["post_intent_ledger_file_sha256"] = hash_file(post_intent_ledger.path)
    report["post_intent_ledger_path"] = sanitize_external_text(
        str(post_intent_ledger.path), 4096
    )
    report["attempt_receipt_count"] = attempt_receipts["attempt_receipt_count"]
    report["attempt_receipt_manifest_sha256"] = attempt_receipts[
        "attempt_receipt_manifest_sha256"
    ]
    report["report_sha256"] = stable_hash(report)
    return report
