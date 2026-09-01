"""Auditable, interruption-safe Pilot-3 image execution.

This module performs no work at import time.  All network-capable entry points require
an explicit execution-gate callback and a separately frozen OAuth runtime fingerprint.
"""

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Protocol, Sequence

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import canonical_json, hash_bytes, hash_file, read_jsonl, stable_hash
from latent_art_bench.pilot3.transport import (
    EXECUTED_MODEL_CLAIMS,
    OPERATIONAL_MODEL_ESTIMAND,
    REQUEST_OUTPUT_FORMAT,
    REQUEST_QUALITY,
    REQUEST_SIZE,
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthRuntimeRevalidation,
    Pilot3TransportConfig,
    RequestedImageModel,
    TransportExchange,
    canonical_image_request_bytes,
    revalidate_pilot3_oauth_runtime_fingerprint,
    sanitize_external_text,
    validate_frozen_requested_labels,
    verify_pilot3_oauth_runtime_fingerprint,
)

MAX_PHYSICAL_POSTS_PER_CELL: Literal[10] = 10
FIXED_RETRY_DELAYS_SECONDS = (1.0, 2.0, 4.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0)
RETRYABLE_EXACT_HTTP_STATUSES = frozenset({408, 409, 425, 429})
MIN_OUTPUT_AREA_EXCLUSIVE = 410 * 410
MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE = 2.0
DEFAULT_SCHEDULE_NAMESPACE = "pilot3-generation-order-v1"
DEFAULT_T12_SCHEDULE_NAMESPACE = "pilot3-assignment-order-v1"
DEFAULT_SCHEDULE_SEED = 20260903
DEFAULT_MAX_PARALLEL = 4
OPERATIONAL_SCOPE_STATEMENT = (
    "Comparisons are between exact requested aliases accepted by the local OAuth endpoint; "
    "the transport does not identify or attest the upstream executed model or snapshot."
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
    "not_sent_global_stop",
]


class ExecutionGateClosed(RuntimeError):
    """Raised before any runtime probe or write when explicit authorization is absent."""


class RequestGateClosed(RuntimeError):
    """Raised before an intent write when per-request authorization is absent."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _eligible_output_geometry(width: int, height: int) -> bool:
    """The strict Kim eligibility domain used by the learned-formal pipeline."""

    return (
        width * height > MIN_OUTPUT_AREA_EXCLUSIVE
        and max(width, height) < MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE * min(width, height)
    )


class GenerationCell(_StrictModel):
    record_type: Literal["pilot3_generation_cell"] = "pilot3_generation_cell"
    schema_version: Literal["3.0"] = "3.0"
    cell_id: str
    prompt_id: str
    content_id: str
    content_block_id: str
    prompt_pair_id: str
    template_id: str
    prompt_text: str
    prompt_text_sha256: str
    target_artist_id: Optional[str] = None
    target_artist_name: Optional[str] = None
    artist_free_control: bool
    requested_model_label: RequestedImageModel
    repetition: int = Field(ge=0)
    source_manifest_bound: bool = False
    source_request_id: Optional[str] = None
    source_sequence: Optional[int] = Field(default=None, ge=1)
    source_repetition: Optional[int] = Field(default=None, ge=1)
    source_schedule_row_sha256: Optional[str] = None
    source_prompt_row_sha256: Optional[str] = None
    source_semantic_request_sha256: Optional[str] = None
    source_paired_control_request_id: Optional[str] = None
    source_paired_control_prompt_id: Optional[str] = None
    source_neighbor_artist_id: Optional[str] = None
    source_transport: Optional[str] = None
    source_endpoint: Optional[str] = None
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
        if not all(
            value.strip()
            for value in (
                self.prompt_id,
                self.content_id,
                self.content_block_id,
                self.prompt_pair_id,
                self.template_id,
            )
        ):
            raise ValueError("generation cell identifiers must not be blank")
        if self.artist_free_control and (self.target_artist_id or self.target_artist_name):
            raise ValueError("artist-free control cells cannot declare a target artist")
        if not self.artist_free_control and not self.target_artist_id:
            raise ValueError("artist-target cells must declare target_artist_id")
        request = canonical_image_request_bytes(
            self.prompt_text, self.requested_model_label
        )
        if hash_bytes(request) != self.canonical_request_sha256:
            raise ValueError("generation cell canonical request hash is stale")
        if hash_bytes(self.prompt_text.encode("utf-8")) != self.prompt_text_sha256:
            raise ValueError("generation cell prompt hash is stale")
        source_values = (
            self.source_request_id,
            self.source_sequence,
            self.source_repetition,
            self.source_schedule_row_sha256,
            self.source_prompt_row_sha256,
            self.source_semantic_request_sha256,
            self.source_transport,
            self.source_endpoint,
        )
        if self.source_manifest_bound:
            if any(value is None for value in source_values):
                raise ValueError("manifest-bound cells require complete source provenance")
            if self.source_repetition != self.repetition + 1:
                raise ValueError("source 1-based repetition does not match internal repetition")
            if self.source_transport != "~/dev/openai-oauth":
                raise ValueError("manifest-bound cells require the frozen OAuth transport")
            if self.source_endpoint != "/v1/images/generations":
                raise ValueError("manifest-bound cells require the frozen image endpoint")
            request_value = json.loads(request.decode("utf-8"))
            if stable_hash(request_value) != self.source_semantic_request_sha256:
                raise ValueError("manifest semantic request hash disagrees with request bytes")
            if self.artist_free_control:
                if (
                    self.source_paired_control_request_id is not None
                    or self.source_paired_control_prompt_id is not None
                    or self.source_neighbor_artist_id is not None
                    or self.prompt_pair_id != self.source_request_id
                ):
                    raise ValueError("manifest-bound control pairing provenance is invalid")
            elif (
                not self.source_paired_control_request_id
                or not self.source_paired_control_prompt_id
                or not self.source_neighbor_artist_id
                or self.prompt_pair_id != self.source_paired_control_request_id
            ):
                raise ValueError("manifest-bound named-artist pairing provenance is invalid")
        elif any(value is not None for value in source_values) or any(
            value is not None
            for value in (
                self.source_paired_control_request_id,
                self.source_paired_control_prompt_id,
                self.source_neighbor_artist_id,
            )
        ):
            raise ValueError("unbound cells cannot carry partial manifest provenance")
        expected = _cell_identity_payload(self, include_identity=False)
        if stable_hash(expected) != self.cell_identity_sha256:
            raise ValueError("generation cell identity hash is stale")
        if self.cell_id != f"p3cell-{self.cell_identity_sha256[:24]}":
            raise ValueError("generation cell id is not derived from its identity")
        return self

    @field_validator(
        "prompt_text_sha256",
        "source_schedule_row_sha256",
        "source_prompt_row_sha256",
        "source_semantic_request_sha256",
        "canonical_request_sha256",
        "cell_identity_sha256",
    )
    @classmethod
    def hashes_are_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("generation cell hashes must be lowercase SHA-256")
        return value


def _cell_identity_payload(
    cell: GenerationCell | Mapping[str, Any], *, include_identity: bool
) -> Dict[str, Any]:
    payload = (
        cell.model_dump(mode="json")
        if isinstance(cell, GenerationCell)
        else dict(cell)
    )
    if not include_identity:
        payload.pop("cell_id", None)
        payload.pop("cell_identity_sha256", None)
    return payload


def make_generation_cell(
    *,
    prompt_id: str,
    content_id: str,
    content_block_id: str,
    prompt_pair_id: str,
    template_id: str,
    prompt_text: str,
    artist_free_control: bool,
    requested_model_label: RequestedImageModel,
    repetition: int,
    target_artist_id: Optional[str] = None,
    target_artist_name: Optional[str] = None,
    source_manifest_bound: bool = False,
    source_request_id: Optional[str] = None,
    source_sequence: Optional[int] = None,
    source_repetition: Optional[int] = None,
    source_schedule_row_sha256: Optional[str] = None,
    source_prompt_row_sha256: Optional[str] = None,
    source_semantic_request_sha256: Optional[str] = None,
    source_paired_control_request_id: Optional[str] = None,
    source_paired_control_prompt_id: Optional[str] = None,
    source_neighbor_artist_id: Optional[str] = None,
    source_transport: Optional[str] = None,
    source_endpoint: Optional[str] = None,
) -> GenerationCell:
    """Construct one content-addressed logical request cell."""

    request = canonical_image_request_bytes(prompt_text, requested_model_label)
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_cell",
        "schema_version": "3.0",
        "prompt_id": prompt_id,
        "content_id": content_id,
        "content_block_id": content_block_id,
        "prompt_pair_id": prompt_pair_id,
        "template_id": template_id,
        "prompt_text": prompt_text,
        "prompt_text_sha256": hash_bytes(prompt_text.encode("utf-8")),
        "target_artist_id": target_artist_id,
        "target_artist_name": target_artist_name,
        "artist_free_control": artist_free_control,
        "requested_model_label": requested_model_label,
        "repetition": repetition,
        "source_manifest_bound": source_manifest_bound,
        "source_request_id": source_request_id,
        "source_sequence": source_sequence,
        "source_repetition": source_repetition,
        "source_schedule_row_sha256": source_schedule_row_sha256,
        "source_prompt_row_sha256": source_prompt_row_sha256,
        "source_semantic_request_sha256": source_semantic_request_sha256,
        "source_paired_control_request_id": source_paired_control_request_id,
        "source_paired_control_prompt_id": source_paired_control_prompt_id,
        "source_neighbor_artist_id": source_neighbor_artist_id,
        "source_transport": source_transport,
        "source_endpoint": source_endpoint,
        "requested_size": REQUEST_SIZE,
        "requested_quality": REQUEST_QUALITY,
        "requested_output_format": REQUEST_OUTPUT_FORMAT,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "executed_model_claims": False,
        "canonical_request_sha256": hash_bytes(request),
    }
    identity = stable_hash(payload)
    payload["cell_identity_sha256"] = identity
    payload["cell_id"] = f"p3cell-{identity[:24]}"
    return GenerationCell.model_validate(payload)


def validate_generation_cells(
    cells: Sequence[GenerationCell],
    frozen_requested_labels: Sequence[str],
) -> None:
    labels = validate_frozen_requested_labels(frozen_requested_labels)
    if not cells:
        raise ValueError("Pilot-3 generation grid must not be empty")
    cell_ids = [cell.cell_id for cell in cells]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("Pilot-3 generation cells contain duplicate identities")
    seen_labels = {cell.requested_model_label for cell in cells}
    if not seen_labels.issubset(labels):
        raise ValueError("generation grid contains a label outside the frozen subset")
    if seen_labels != set(labels):
        raise ValueError("generation grid does not cover every frozen requested label")
    for cell in cells:
        GenerationCell.model_validate(cell.model_dump(mode="json"))
        canonical_image_request_bytes(
            cell.prompt_text,
            cell.requested_model_label,
            frozen_requested_labels=labels,
        )


def generation_grid_sha256(cells: Sequence[GenerationCell]) -> str:
    if not cells:
        raise ValueError("cannot hash an empty generation grid")
    ordered = sorted(cells, key=lambda cell: cell.cell_id)
    return stable_hash([cell.model_dump(mode="json") for cell in ordered])


class GenerationScheduleEntry(_StrictModel):
    record_type: Literal["pilot3_generation_schedule_entry"] = (
        "pilot3_generation_schedule_entry"
    )
    schema_version: Literal["3.0"] = "3.0"
    cell_id: str
    cell_identity_sha256: str
    content_block_id: str
    requested_model_label: RequestedImageModel
    repetition: int = Field(ge=0)
    batch_id: str
    batch_rank: int = Field(ge=1)
    within_batch_rank: int = Field(ge=1)
    scheduled_cell_rank: int = Field(ge=1)
    runtime_image_preflight_rank: Optional[int] = Field(default=None, ge=1)
    source_request_id: Optional[str] = None
    source_sequence: Optional[int] = Field(default=None, ge=1)
    source_schedule_row_sha256: Optional[str] = None

    @field_validator("cell_identity_sha256", "source_schedule_row_sha256")
    @classmethod
    def entry_hashes(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("schedule-entry hashes must be lowercase SHA-256")
        return value


class GenerationSchedule(_StrictModel):
    record_type: Literal["pilot3_generation_schedule"] = "pilot3_generation_schedule"
    schema_version: Literal["3.0"] = "3.0"
    namespace: str
    seed: int
    max_parallel: int = Field(ge=1)
    batch_count: int = Field(ge=1)
    cell_count: int = Field(ge=1)
    generation_grid_sha256: str
    frozen_requested_labels: List[RequestedImageModel]
    ordering_basis: Literal["deterministic_cell_hash", "t12_canonical_sequence"]
    source_prompt_manifest_semantic_sha256: Optional[str] = None
    source_schedule_manifest_semantic_sha256: Optional[str] = None
    source_prompt_manifest_file_sha256: Optional[str] = None
    source_schedule_manifest_file_sha256: Optional[str] = None
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
        batches: Dict[int, List[GenerationScheduleEntry]] = {}
        for entry in self.entries:
            batches.setdefault(entry.batch_rank, []).append(entry)
        if sorted(batches) != list(range(1, self.batch_count + 1)):
            raise ValueError("generation schedule batch ranks must be contiguous")
        for batch_rank, rows in batches.items():
            expected_size = (
                self.cell_count - self.max_parallel * (self.batch_count - 1)
                if batch_rank == self.batch_count
                else self.max_parallel
            )
            if len(rows) != expected_size or sorted(
                row.within_batch_rank for row in rows
            ) != list(range(1, expected_size + 1)):
                raise ValueError("generation schedule batch membership is stale")
        labels = validate_frozen_requested_labels(self.frozen_requested_labels)
        preflight = sorted(
            entry.runtime_image_preflight_rank
            for entry in self.entries
            if entry.runtime_image_preflight_rank is not None
        )
        if preflight != list(range(1, len(labels) + 1)):
            raise ValueError(
                "schedule must identify one runtime image preflight cell per frozen label"
            )
        if self.ordering_basis == "t12_canonical_sequence":
            required_hashes = (
                self.source_prompt_manifest_semantic_sha256,
                self.source_schedule_manifest_semantic_sha256,
            )
            if any(value is None for value in required_hashes):
                raise ValueError("T12 schedules require source manifest semantic hashes")
            if any(
                entry.source_request_id is None
                or entry.source_sequence is None
                or entry.source_schedule_row_sha256 is None
                for entry in self.entries
            ):
                raise ValueError("T12 schedule entries require complete source bindings")
            if [entry.source_sequence for entry in self.entries] != list(
                range(1, self.cell_count + 1)
            ):
                raise ValueError("T12 schedule must retain exact canonical source order")
            if [entry.source_sequence for entry in self.entries] != [
                entry.scheduled_cell_rank for entry in self.entries
            ]:
                raise ValueError("T12 source sequence and execution rank must be identical")
            if len({entry.source_request_id for entry in self.entries}) != self.cell_count:
                raise ValueError("T12 request ids must be unique")
            preflight_entries = sorted(
                (
                    entry
                    for entry in self.entries
                    if entry.runtime_image_preflight_rank is not None
                ),
                key=lambda entry: entry.runtime_image_preflight_rank or 0,
            )
            if [entry.scheduled_cell_rank for entry in preflight_entries] != list(
                range(1, len(labels) + 1)
            ):
                raise ValueError(
                    "T12 runtime image preflight must be the canonical schedule prefix"
                )
        elif any(
            value is not None
            for value in (
                self.source_prompt_manifest_semantic_sha256,
                self.source_schedule_manifest_semantic_sha256,
                self.source_prompt_manifest_file_sha256,
                self.source_schedule_manifest_file_sha256,
            )
        ):
            raise ValueError("non-T12 schedules cannot claim source manifest bindings")
        payload = self.model_dump(mode="json", exclude={"schedule_sha256"})
        if stable_hash(payload) != self.schedule_sha256:
            raise ValueError("generation schedule hash is stale")
        return self

    @field_validator(
        "generation_grid_sha256",
        "source_prompt_manifest_semantic_sha256",
        "source_schedule_manifest_semantic_sha256",
        "source_prompt_manifest_file_sha256",
        "source_schedule_manifest_file_sha256",
        "schedule_sha256",
    )
    @classmethod
    def schedule_hashes(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("schedule hashes must be lowercase SHA-256")
        return value


def select_runtime_image_preflight_cells(
    cells: Sequence[GenerationCell], frozen_requested_labels: Sequence[str]
) -> List[GenerationCell]:
    """Select one ordinary grid cell per alias without changing T12 send order.

    A manifest-bound run uses the first canonical request for each label. Those
    first appearances must form the initial schedule prefix; otherwise a
    separate preflight would reorder or add study requests and execution fails
    closed. Unbound development grids retain the stricter control-cell rule.
    """

    labels = validate_frozen_requested_labels(frozen_requested_labels)
    validate_generation_cells(cells, labels)
    manifest_bound = [cell.source_manifest_bound for cell in cells]
    if any(manifest_bound) and not all(manifest_bound):
        raise ValueError("generation grids cannot mix T12-bound and unbound cells")
    if all(manifest_bound):
        selected: List[GenerationCell] = []
        for label in labels:
            candidates = sorted(
                (cell for cell in cells if cell.requested_model_label == label),
                key=lambda cell: (cell.source_sequence or 0, cell.cell_id),
            )
            if not candidates:
                raise ValueError(f"no manifest-bound runtime preflight cell for {label}")
            selected.append(candidates[0])
        selected.sort(key=lambda cell: (cell.source_sequence or 0, cell.cell_id))
        if [cell.source_sequence for cell in selected] != list(
            range(1, len(labels) + 1)
        ):
            raise ValueError(
                "first request for every frozen label must form the canonical "
                "T12 schedule prefix"
            )
        return selected

    selected: List[GenerationCell] = []
    for label in labels:
        candidates = sorted(
            (
                cell
                for cell in cells
                if cell.requested_model_label == label
                and cell.artist_free_control
                and cell.repetition == 0
            ),
            key=lambda cell: (
                cell.content_block_id,
                cell.content_id,
                cell.prompt_id,
                cell.cell_id,
            ),
        )
        if not candidates:
            raise ValueError(
                f"no artist-free repetition-zero runtime preflight cell for {label}"
            )
        selected.append(candidates[0])
    return selected


def build_generation_schedule(
    cells: Sequence[GenerationCell],
    *,
    frozen_requested_labels: Sequence[str],
    namespace: str = DEFAULT_SCHEDULE_NAMESPACE,
    seed: int = DEFAULT_SCHEDULE_SEED,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
) -> GenerationSchedule:
    """Build a deterministic, hash-ranked schedule with bounded batches."""

    labels = validate_frozen_requested_labels(frozen_requested_labels)
    validate_generation_cells(cells, labels)
    if not namespace.strip():
        raise ValueError("schedule namespace must not be blank")
    if max_parallel < 1:
        raise ValueError("max_parallel must be positive")
    preflight = select_runtime_image_preflight_cells(cells, labels)
    preflight_rank = {cell.cell_id: index for index, cell in enumerate(preflight, 1)}

    def rank(cell: GenerationCell) -> tuple[str, str]:
        digest = hash_bytes(
            f"{namespace}|{seed}|{cell.cell_identity_sha256}".encode("utf-8")
        )
        return digest, cell.cell_id

    ordered = sorted(cells, key=rank)
    entries: List[GenerationScheduleEntry] = []
    for position, cell in enumerate(ordered, 1):
        batch_rank = (position - 1) // max_parallel + 1
        within_rank = (position - 1) % max_parallel + 1
        batch_digest = hash_bytes(
            f"{namespace}|{seed}|batch|{batch_rank}".encode("utf-8")
        )
        entries.append(
            GenerationScheduleEntry(
                cell_id=cell.cell_id,
                cell_identity_sha256=cell.cell_identity_sha256,
                content_block_id=cell.content_block_id,
                requested_model_label=cell.requested_model_label,
                repetition=cell.repetition,
                batch_id=f"p3batch-{batch_rank:05d}-{batch_digest[:12]}",
                batch_rank=batch_rank,
                within_batch_rank=within_rank,
                scheduled_cell_rank=position,
                runtime_image_preflight_rank=preflight_rank.get(cell.cell_id),
                source_request_id=cell.source_request_id,
                source_sequence=cell.source_sequence,
                source_schedule_row_sha256=cell.source_schedule_row_sha256,
            )
        )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_schedule",
        "schema_version": "3.0",
        "namespace": namespace,
        "seed": seed,
        "max_parallel": max_parallel,
        "batch_count": (len(cells) + max_parallel - 1) // max_parallel,
        "cell_count": len(cells),
        "generation_grid_sha256": generation_grid_sha256(cells),
        "frozen_requested_labels": list(labels),
        "ordering_basis": "deterministic_cell_hash",
        "source_prompt_manifest_semantic_sha256": None,
        "source_schedule_manifest_semantic_sha256": None,
        "source_prompt_manifest_file_sha256": None,
        "source_schedule_manifest_file_sha256": None,
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    payload["schedule_sha256"] = stable_hash(payload)
    return GenerationSchedule.model_validate(payload)


def _verify_manifest_row_hash(
    row: Mapping[str, Any], *, hash_field: str, label: str
) -> None:
    unsigned = dict(row)
    recorded = unsigned.pop(hash_field, None)
    if not isinstance(recorded, str) or not _is_sha256(recorded):
        raise ValueError(f"{label} lacks a valid {hash_field}")
    if stable_hash(unsigned) != recorded:
        raise ValueError(f"{label} has a stale {hash_field}")


def adapt_t12_manifests_to_generation(
    prompt_rows: Sequence[Mapping[str, Any]],
    schedule_rows: Sequence[Mapping[str, Any]],
    *,
    transport_config: Pilot3TransportConfig,
    namespace: str = DEFAULT_T12_SCHEDULE_NAMESPACE,
    seed: int = DEFAULT_SCHEDULE_SEED,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
    prompt_manifest_file_sha256: Optional[str] = None,
    schedule_manifest_file_sha256: Optional[str] = None,
) -> tuple[List[GenerationCell], GenerationSchedule]:
    """Validate T12 manifests and preserve their exact 1-based send sequence.

    The adapter does not mutate or reinterpret T12.  Its internal zero-based
    repetition is a redundant execution convenience; every cell retains the
    authoritative source repetition and all pairing/neighbor/self-hash fields.
    """

    if not prompt_rows or not schedule_rows:
        raise ValueError("T12 prompt and schedule manifests must not be empty")
    if not namespace.strip() or max_parallel < 1:
        raise ValueError("T12 schedule namespace and max_parallel must be valid")
    for value, label in (
        (prompt_manifest_file_sha256, "prompt manifest file hash"),
        (schedule_manifest_file_sha256, "schedule manifest file hash"),
    ):
        if value is not None and not _is_sha256(value):
            raise ValueError(f"{label} must be lowercase SHA-256")

    prompts: Dict[str, Dict[str, Any]] = {}
    for index, raw in enumerate(prompt_rows, 1):
        row = dict(raw)
        label = f"T12 prompt row {index}"
        if (
            row.get("record_type") != "pilot3_prompt"
            or row.get("schema_version") != "pilot3-prompt/1.0"
        ):
            raise ValueError(f"{label} has the wrong schema")
        _verify_manifest_row_hash(row, hash_field="prompt_sha256", label=label)
        prompt_id = row.get("prompt_id")
        if not isinstance(prompt_id, str) or not prompt_id.strip() or prompt_id in prompts:
            raise ValueError("T12 prompt ids must be unique and non-blank")
        if not isinstance(row.get("prompt_text"), str) or not row["prompt_text"].strip():
            raise ValueError(f"{label} has a blank prompt")
        if row.get("condition") not in {"artist_free_control", "named_artist"}:
            raise ValueError(f"{label} has an invalid condition")
        prompts[prompt_id] = row

    rows = [dict(row) for row in schedule_rows]
    if [row.get("sequence") for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("T12 schedule rows must be in exact contiguous canonical sequence")
    request_ids = [row.get("request_id") for row in rows]
    if any(not isinstance(value, str) or not value.strip() for value in request_ids):
        raise ValueError("T12 request ids must be non-blank strings")
    if len(request_ids) != len(set(request_ids)):
        raise ValueError("T12 request ids must be unique")
    if set(prompts) != {str(row.get("prompt_id")) for row in rows}:
        raise ValueError("T12 prompt and schedule manifests do not bind the same prompt set")
    request_index = {str(row["request_id"]): row for row in rows}

    cells: List[GenerationCell] = []
    for index, row in enumerate(rows, 1):
        label = f"T12 schedule row {index}"
        if (
            row.get("record_type") != "pilot3_scheduled_request"
            or row.get("schema_version") != "pilot3-scheduled-request/1.0"
        ):
            raise ValueError(f"{label} has the wrong schema")
        _verify_manifest_row_hash(
            row, hash_field="schedule_row_sha256", label=label
        )
        prompt_id = row.get("prompt_id")
        prompt = prompts.get(str(prompt_id))
        if prompt is None:
            raise ValueError(f"{label} references an unknown prompt")
        if row.get("prompt_sha256") != prompt.get("prompt_sha256"):
            raise ValueError(f"{label} prompt-row hash binding is stale")
        for field in ("content_block_id", "condition", "target_artist_id", "neighbor_artist_id"):
            if row.get(field) != prompt.get(field):
                raise ValueError(f"{label} disagrees with its prompt on {field}")
        requested_label = row.get("requested_model_label")
        if requested_label not in transport_config.frozen_requested_labels:
            raise ValueError(f"{label} requested alias is outside the frozen subset")
        if row.get("transport") != "~/dev/openai-oauth":
            raise ValueError(f"{label} does not use the frozen OAuth transport")
        if row.get("endpoint") != "/v1/images/generations":
            raise ValueError(f"{label} does not use the frozen image endpoint")
        repetition = row.get("repetition")
        if isinstance(repetition, bool) or not isinstance(repetition, int) or repetition < 1:
            raise ValueError(f"{label} repetition must be a positive 1-based integer")
        body = row.get("request_body")
        if not isinstance(body, Mapping):
            raise ValueError(f"{label} request_body must be an object")
        canonical = canonical_image_request_bytes(
            body.get("prompt"),  # type: ignore[arg-type]
            requested_label,  # type: ignore[arg-type]
            frozen_requested_labels=transport_config.frozen_requested_labels,
        )
        canonical_value = json.loads(canonical.decode("utf-8"))
        if dict(body) != canonical_value:
            raise ValueError(f"{label} request body is not the canonical Pilot-3 body")
        if body.get("prompt") != prompt.get("prompt_text"):
            raise ValueError(f"{label} embedded prompt text disagrees with prompt row")
        if row.get("semantic_request_sha256") != stable_hash(canonical_value):
            raise ValueError(f"{label} semantic request hash is stale")
        expected_order_sha256 = stable_hash(
            {
                "namespace": namespace,
                "seed": seed,
                "request_id": row["request_id"],
                "semantic_request_sha256": row["semantic_request_sha256"],
            }
        )
        if row.get("execution_order_sha256") != expected_order_sha256:
            raise ValueError(f"{label} deterministic execution-order hash is stale")

        artist_free = row["condition"] == "artist_free_control"
        paired_request = row.get("paired_control_request_id")
        paired_prompt = prompt.get("paired_control_prompt_id")
        if artist_free:
            if any(
                value is not None
                for value in (
                    row.get("target_artist_id"),
                    row.get("neighbor_artist_id"),
                    paired_request,
                    paired_prompt,
                )
            ):
                raise ValueError(f"{label} control row carries named-artist provenance")
            prompt_pair_id = str(row["request_id"])
        else:
            if not isinstance(paired_request, str) or not isinstance(paired_prompt, str):
                raise ValueError(f"{label} named row lacks its shared-control binding")
            control = request_index.get(paired_request)
            if control is None:
                raise ValueError(f"{label} paired control request does not exist")
            if (
                control.get("condition") != "artist_free_control"
                or control.get("content_block_id") != row.get("content_block_id")
                or control.get("repetition") != repetition
                or control.get("prompt_id") != paired_prompt
            ):
                raise ValueError(f"{label} shared-control request binding is invalid")
            if not isinstance(row.get("neighbor_artist_id"), str):
                raise ValueError(f"{label} named row lacks its frozen neighbor")
            prompt_pair_id = paired_request

        cells.append(
            make_generation_cell(
                prompt_id=str(prompt_id),
                content_id=str(row["content_block_id"]),
                content_block_id=str(row["content_block_id"]),
                prompt_pair_id=prompt_pair_id,
                template_id="pilot3-matched-landscape-v1",
                prompt_text=str(body["prompt"]),
                artist_free_control=artist_free,
                requested_model_label=requested_label,  # type: ignore[arg-type]
                repetition=repetition - 1,
                target_artist_id=(
                    None if artist_free else str(row["target_artist_id"])
                ),
                target_artist_name=(
                    None if artist_free else str(prompt["target_artist_name"])
                ),
                source_manifest_bound=True,
                source_request_id=str(row["request_id"]),
                source_sequence=int(row["sequence"]),
                source_repetition=repetition,
                source_schedule_row_sha256=str(row["schedule_row_sha256"]),
                source_prompt_row_sha256=str(row["prompt_sha256"]),
                source_semantic_request_sha256=str(row["semantic_request_sha256"]),
                source_paired_control_request_id=(
                    None if artist_free else paired_request
                ),
                source_paired_control_prompt_id=(
                    None if artist_free else paired_prompt
                ),
                source_neighbor_artist_id=(
                    None if artist_free else str(row["neighbor_artist_id"])
                ),
                source_transport=str(row["transport"]),
                source_endpoint=str(row["endpoint"]),
            )
        )

    remaining_order = [
        (str(row["execution_order_sha256"]), str(row["request_id"]))
        for row in rows[1:]
    ]
    if remaining_order != sorted(remaining_order):
        raise ValueError(
            "T12 rows after the frozen runtime preflight are not in seeded hash order"
        )

    validate_generation_cells(cells, transport_config.frozen_requested_labels)
    preflight = select_runtime_image_preflight_cells(
        cells, transport_config.frozen_requested_labels
    )
    preflight_rank = {cell.cell_id: rank for rank, cell in enumerate(preflight, 1)}
    entries: List[GenerationScheduleEntry] = []
    for position, cell in enumerate(cells, 1):
        if cell.source_sequence != position:
            raise AssertionError("T12 adapter lost canonical sequence")
        batch_rank = (position - 1) // max_parallel + 1
        within_rank = (position - 1) % max_parallel + 1
        batch_digest = hash_bytes(
            (
                f"{namespace}|{seed}|{stable_hash(rows)}|batch|{batch_rank}"
            ).encode("utf-8")
        )
        entries.append(
            GenerationScheduleEntry(
                cell_id=cell.cell_id,
                cell_identity_sha256=cell.cell_identity_sha256,
                content_block_id=cell.content_block_id,
                requested_model_label=cell.requested_model_label,
                repetition=cell.repetition,
                batch_id=f"p3batch-{batch_rank:05d}-{batch_digest[:12]}",
                batch_rank=batch_rank,
                within_batch_rank=within_rank,
                scheduled_cell_rank=position,
                runtime_image_preflight_rank=preflight_rank.get(cell.cell_id),
                source_request_id=cell.source_request_id,
                source_sequence=cell.source_sequence,
                source_schedule_row_sha256=cell.source_schedule_row_sha256,
            )
        )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_schedule",
        "schema_version": "3.0",
        "namespace": namespace,
        "seed": seed,
        "max_parallel": max_parallel,
        "batch_count": (len(cells) + max_parallel - 1) // max_parallel,
        "cell_count": len(cells),
        "generation_grid_sha256": generation_grid_sha256(cells),
        "frozen_requested_labels": list(transport_config.frozen_requested_labels),
        "ordering_basis": "t12_canonical_sequence",
        "source_prompt_manifest_semantic_sha256": stable_hash(
            [dict(row) for row in prompt_rows]
        ),
        "source_schedule_manifest_semantic_sha256": stable_hash(rows),
        "source_prompt_manifest_file_sha256": prompt_manifest_file_sha256,
        "source_schedule_manifest_file_sha256": schedule_manifest_file_sha256,
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    payload["schedule_sha256"] = stable_hash(payload)
    return cells, GenerationSchedule.model_validate(payload)


def load_t12_generation_plan(
    prompt_manifest_path: Path,
    schedule_manifest_path: Path,
    *,
    transport_config: Pilot3TransportConfig,
    namespace: str = DEFAULT_T12_SCHEDULE_NAMESPACE,
    seed: int = DEFAULT_SCHEDULE_SEED,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
) -> tuple[List[GenerationCell], GenerationSchedule]:
    """Read and fully bind canonical T12 JSONL files without external I/O."""

    prompt_path = Path(prompt_manifest_path)
    schedule_path = Path(schedule_manifest_path)
    if not prompt_path.is_file() or not schedule_path.is_file():
        raise FileNotFoundError("canonical T12 prompt or schedule manifest is missing")
    return adapt_t12_manifests_to_generation(
        read_jsonl(prompt_path),
        read_jsonl(schedule_path),
        transport_config=transport_config,
        namespace=namespace,
        seed=seed,
        max_parallel=max_parallel,
        prompt_manifest_file_sha256=hash_file(prompt_path),
        schedule_manifest_file_sha256=hash_file(schedule_path),
    )


class GenerationPostIntent(_StrictModel):
    """Fsync'd evidence that one physical POST is about to be attempted."""

    record_type: Literal["pilot3_generation_post_intent"] = (
        "pilot3_generation_post_intent"
    )
    schema_version: Literal["pilot3-generation-post-intent-v2"] = (
        "pilot3-generation-post-intent-v2"
    )
    intent_sequence: int = Field(ge=1)
    prior_ledger_semantic_sha256: str
    attempt_id: str
    cell_id: str
    cell_identity_sha256: str
    attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    requested_model_label: RequestedImageModel
    source_request_id: Optional[str] = None
    source_sequence: Optional[int] = Field(default=None, ge=1)
    source_repetition: Optional[int] = Field(default=None, ge=1)
    source_schedule_row_sha256: Optional[str] = None
    source_prompt_row_sha256: Optional[str] = None
    source_paired_control_request_id: Optional[str] = None
    source_neighbor_artist_id: Optional[str] = None
    endpoint: str
    transport_config_sha256: str
    execution_namespace: str
    canonical_request_utf8: str
    canonical_request_sha256: str
    canonical_request_byte_count: int = Field(ge=1)
    oauth_runtime_fingerprint_sha256: str
    pre_post_runtime_revalidation: Pilot3OAuthRuntimeRevalidation
    request_gate_context_sha256: str
    attempt_ledger_path: str
    post_intent_ledger_path: str
    output_dir: str
    created_at: datetime
    physical_post_may_have_executed: Literal[True] = True
    post_intent_sha256: str

    @model_validator(mode="after")
    def intent_is_consistent(self) -> "GenerationPostIntent":
        if not self.attempt_id.startswith("p3attempt-"):
            raise ValueError("Pilot-3 attempt ids must use the p3attempt prefix")
        if any(
            str(Path(value).resolve()) != value
            for value in (
                self.attempt_ledger_path,
                self.post_intent_ledger_path,
                self.output_dir,
            )
        ):
            raise ValueError("post intent execution paths must be canonical absolute paths")
        source_core = (
            self.source_request_id,
            self.source_sequence,
            self.source_repetition,
            self.source_schedule_row_sha256,
            self.source_prompt_row_sha256,
        )
        if any(value is not None for value in source_core) and any(
            value is None for value in source_core
        ):
            raise ValueError("post intent carries partial T12 source provenance")
        if all(value is None for value in source_core) and (
            self.source_paired_control_request_id is not None
            or self.source_neighbor_artist_id is not None
        ):
            raise ValueError("unbound post intent carries T12 pairing provenance")
        body = self.canonical_request_utf8.encode("utf-8")
        if len(body) != self.canonical_request_byte_count or hash_bytes(
            body
        ) != self.canonical_request_sha256:
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
        runtime = self.pre_post_runtime_revalidation
        if (
            runtime.persisted_fingerprint_sha256
            != self.oauth_runtime_fingerprint_sha256
            or runtime.transport_config_sha256 != self.transport_config_sha256
            or runtime.endpoint_url != self.endpoint
            or runtime.frozen_requested_labels != [self.requested_model_label]
        ):
            raise ValueError("post intent runtime revalidation is bound elsewhere")
        payload = self.model_dump(mode="json", exclude={"post_intent_sha256"})
        if stable_hash(payload) != self.post_intent_sha256:
            raise ValueError("post intent hash is stale")
        return self

    @field_validator(
        "prior_ledger_semantic_sha256",
        "cell_identity_sha256",
        "source_schedule_row_sha256",
        "source_prompt_row_sha256",
        "transport_config_sha256",
        "canonical_request_sha256",
        "oauth_runtime_fingerprint_sha256",
        "request_gate_context_sha256",
        "post_intent_sha256",
    )
    @classmethod
    def intent_hashes(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("post intent hashes must be lowercase SHA-256")
        return value


class GenerationAttempt(_StrictModel):
    record_type: Literal["pilot3_generation_attempt"] = "pilot3_generation_attempt"
    schema_version: Literal["3.1"] = "3.1"
    attempt_id: str
    cell_id: str
    cell_identity_sha256: str
    attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    post_intent_sequence: int = Field(ge=1)
    post_intent_sha256: str
    requested_model_label: RequestedImageModel
    source_request_id: Optional[str] = None
    source_sequence: Optional[int] = Field(default=None, ge=1)
    source_repetition: Optional[int] = Field(default=None, ge=1)
    source_schedule_row_sha256: Optional[str] = None
    source_prompt_row_sha256: Optional[str] = None
    source_paired_control_request_id: Optional[str] = None
    source_neighbor_artist_id: Optional[str] = None
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    executed_model_claims: Literal[False] = EXECUTED_MODEL_CLAIMS
    snapshot_identity_claims: Literal[False] = False
    endpoint: str
    transport_config_sha256: str
    execution_namespace: str
    http_method: Literal["POST"] = "POST"
    requested_size: Literal["auto"] = REQUEST_SIZE
    requested_quality: Literal["low"] = REQUEST_QUALITY
    requested_output_format: Literal["png"] = REQUEST_OUTPUT_FORMAT
    canonical_request_utf8: str
    canonical_request_sha256: str
    canonical_request_byte_count: int = Field(ge=1)
    oauth_runtime_fingerprint_sha256: str
    pre_post_runtime_revalidation: Pilot3OAuthRuntimeRevalidation
    request_gate_context_sha256: str
    attempt_ledger_path: str
    post_intent_ledger_path: str
    output_dir: str
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
    kim_geometry_contract_satisfied: Optional[bool] = None
    exact_dimensions_claimed: Literal[False] = False
    dimension_evidence_scope: Literal[
        "observed_output_only_size_auto_no_exact_dimension_claim"
    ] = "observed_output_only_size_auto_no_exact_dimension_claim"
    revised_prompt: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def attempt_is_internally_consistent(self) -> "GenerationAttempt":
        if not self.attempt_id.startswith("p3attempt-"):
            raise ValueError("Pilot-3 attempt ids must use the p3attempt prefix")
        if any(
            str(Path(value).resolve()) != value
            for value in (
                self.attempt_ledger_path,
                self.post_intent_ledger_path,
                self.output_dir,
            )
        ):
            raise ValueError("attempt execution paths must be canonical absolute paths")
        source_core = (
            self.source_request_id,
            self.source_sequence,
            self.source_repetition,
            self.source_schedule_row_sha256,
            self.source_prompt_row_sha256,
        )
        if any(value is not None for value in source_core) and any(
            value is None for value in source_core
        ):
            raise ValueError("attempt carries partial T12 source provenance")
        if all(value is None for value in source_core) and (
            self.source_paired_control_request_id is not None
            or self.source_neighbor_artist_id is not None
        ):
            raise ValueError("unbound attempt carries T12 pairing provenance")
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
            raise ValueError("attempt request is not the canonical Pilot-3 request")
        runtime = self.pre_post_runtime_revalidation
        if (
            runtime.persisted_fingerprint_sha256
            != self.oauth_runtime_fingerprint_sha256
            or runtime.transport_config_sha256 != self.transport_config_sha256
            or runtime.endpoint_url != self.endpoint
            or runtime.frozen_requested_labels != [self.requested_model_label]
        ):
            raise ValueError("attempt runtime revalidation is bound elsewhere")
        if self.completed_at < self.started_at:
            raise ValueError("attempt completed before it started")
        retryable_classes = {"retryable_transport", "retryable_http_status"}
        if (self.outcome == "retryable_failure") != (
            self.retry_classification in retryable_classes
        ):
            raise ValueError("retryable outcome and classification disagree")
        if (self.outcome == "refused") != (
            self.retry_classification == "not_retryable_refusal"
        ):
            raise ValueError("refusal outcome and classification disagree")
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
            if (
                self.actual_format != "png"
                or self.output_format_contract_satisfied is not True
                or self.kim_geometry_contract_satisfied is not True
            ):
                raise ValueError("successful attempt violates PNG/Kim output contracts")
            if not self.request_label_accepted:
                raise ValueError("successful attempt must record requested-label acceptance")
            assert self.actual_width is not None and self.actual_height is not None
            if not _eligible_output_geometry(self.actual_width, self.actual_height):
                raise ValueError("successful attempt is outside the strict Kim geometry domain")
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
        "source_schedule_row_sha256",
        "source_prompt_row_sha256",
        "post_intent_sha256",
        "transport_config_sha256",
        "canonical_request_sha256",
        "oauth_runtime_fingerprint_sha256",
        "request_gate_context_sha256",
        "response_body_sha256",
        "output_sha256",
        "decoded_output_sha256",
    )
    @classmethod
    def attempt_hashes(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("attempt provenance hashes must be lowercase SHA-256")
        return value


class GenerationAttemptReceipt(_StrictModel):
    """Durable exact row plus the attempt-ledger prefix it must extend."""

    record_type: Literal["pilot3_generation_attempt_receipt"] = (
        "pilot3_generation_attempt_receipt"
    )
    schema_version: Literal["pilot3-generation-attempt-receipt-v2"] = (
        "pilot3-generation-attempt-receipt-v2"
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
        if not _is_sha256(value):
            raise ValueError("attempt receipt hashes must be lowercase SHA-256")
        return value


class GenerationGlobalStopDisposition(_StrictModel):
    """Proof that one frozen cell received neither an intent nor a POST."""

    record_type: Literal["pilot3_generation_global_stop_disposition"] = (
        "pilot3_generation_global_stop_disposition"
    )
    schema_version: Literal["pilot3-generation-global-stop-disposition-v1"] = (
        "pilot3-generation-global-stop-disposition-v1"
    )
    stop_sequence: int = Field(ge=1)
    cell_id: str
    cell_identity_sha256: str
    source_request_id: str
    source_sequence: int = Field(ge=1)
    source_schedule_row_sha256: str
    requested_model_label: RequestedImageModel
    generation_grid_sha256: str
    generation_schedule_sha256: str
    runtime_image_preflight_sha256: str
    preflight_cell_id: str
    preflight_source_request_id: str
    global_stop_reason: Literal["runtime_image_preflight_failed"] = (
        "runtime_image_preflight_failed"
    )
    terminal_category: Literal["not_sent_global_stop"] = "not_sent_global_stop"
    physical_post_count: Literal[0] = 0
    physical_post_may_have_executed: Literal[False] = False
    post_intent_written: Literal[False] = False
    fake_attempt_row_created: Literal[False] = False
    attempts_at_stop_count: int = Field(ge=1)
    post_intents_at_stop_count: int = Field(ge=1)
    record_sha256: str

    @model_validator(mode="after")
    def disposition_is_consistent(self) -> "GenerationGlobalStopDisposition":
        payload = self.model_dump(mode="json", exclude={"record_sha256"})
        if stable_hash(payload) != self.record_sha256:
            raise ValueError("global-stop disposition hash is stale")
        if not self.cell_id or not self.source_request_id:
            raise ValueError("global-stop disposition identity is blank")
        return self

    @field_validator(
        "cell_identity_sha256",
        "source_schedule_row_sha256",
        "generation_grid_sha256",
        "generation_schedule_sha256",
        "runtime_image_preflight_sha256",
        "record_sha256",
    )
    @classmethod
    def disposition_hashes(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("global-stop disposition hashes must be lowercase SHA-256")
        return value


RuntimeRevalidationPhase = Literal[
    "start_before_runtime_image_preflight",
    "before_batch",
    "end_after_runtime_image_preflight",
    "end_after_all_batches",
]


class GenerationRuntimeRevalidationRecord(_StrictModel):
    record_type: Literal["pilot3_generation_runtime_revalidation"] = (
        "pilot3_generation_runtime_revalidation"
    )
    schema_version: Literal["pilot3-generation-runtime-revalidation-v1"] = (
        "pilot3-generation-runtime-revalidation-v1"
    )
    record_id: str
    ledger_sequence: int = Field(ge=1)
    prior_ledger_semantic_sha256: str
    invocation_id: str
    invocation_sequence: int = Field(ge=1)
    phase: RuntimeRevalidationPhase
    batch_rank: Optional[int] = Field(default=None, ge=1)
    generation_grid_sha256: str
    generation_schedule_sha256: str
    attempt_ledger_row_count: int = Field(ge=0)
    attempt_ledger_semantic_sha256: str
    evidence: Pilot3OAuthRuntimeRevalidation
    runtime_revalidation_record_sha256: str

    @model_validator(mode="after")
    def record_is_consistent(self) -> "GenerationRuntimeRevalidationRecord":
        if not self.record_id.startswith("p3runtime-"):
            raise ValueError("runtime record id must use the p3runtime prefix")
        if (self.phase == "before_batch") != (self.batch_rank is not None):
            raise ValueError("runtime revalidation batch rank disagrees with phase")
        payload = self.model_dump(
            mode="json", exclude={"runtime_revalidation_record_sha256"}
        )
        if stable_hash(payload) != self.runtime_revalidation_record_sha256:
            raise ValueError("runtime revalidation record hash is stale")
        return self

    @field_validator(
        "prior_ledger_semantic_sha256",
        "generation_grid_sha256",
        "generation_schedule_sha256",
        "attempt_ledger_semantic_sha256",
        "runtime_revalidation_record_sha256",
    )
    @classmethod
    def record_hashes(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("runtime revalidation record hashes must be SHA-256")
        return value


class ExecutionGateContext(_StrictModel):
    record_type: Literal["pilot3_execution_gate_context"] = (
        "pilot3_execution_gate_context"
    )
    schema_version: Literal["pilot3-execution-gate-context-v1"] = (
        "pilot3-execution-gate-context-v1"
    )
    transport_config_sha256: str
    oauth_runtime_fingerprint_sha256: str
    generation_grid_sha256: str
    generation_schedule_sha256: str
    frozen_requested_labels: List[RequestedImageModel]
    cell_count: int = Field(ge=1)
    existing_attempt_count: int = Field(ge=0)
    existing_attempt_ledger_semantic_sha256: str
    existing_post_intent_count: int = Field(ge=0)
    existing_post_intent_ledger_semantic_sha256: str
    context_sha256: str

    @model_validator(mode="after")
    def context_is_consistent(self) -> "ExecutionGateContext":
        payload = self.model_dump(mode="json", exclude={"context_sha256"})
        if stable_hash(payload) != self.context_sha256:
            raise ValueError("execution gate context hash is stale")
        return self

    @field_validator(
        "transport_config_sha256",
        "oauth_runtime_fingerprint_sha256",
        "generation_grid_sha256",
        "generation_schedule_sha256",
        "existing_attempt_ledger_semantic_sha256",
        "existing_post_intent_ledger_semantic_sha256",
        "context_sha256",
    )
    @classmethod
    def context_hashes(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("execution gate context hashes must be SHA-256")
        return value


ExecutionGate = Callable[[ExecutionGateContext], bool]


class RequestGateContext(_StrictModel):
    """Exact pre-intent state authorized immediately before one physical POST."""

    record_type: Literal["pilot3_request_gate_context"] = (
        "pilot3_request_gate_context"
    )
    schema_version: Literal["pilot3-request-gate-context-v1"] = (
        "pilot3-request-gate-context-v1"
    )
    transport_config_sha256: str
    oauth_runtime_fingerprint_sha256: str
    cell_id: str
    cell_identity_sha256: str
    source_request_id: Optional[str] = None
    source_schedule_row_sha256: Optional[str] = None
    requested_model_label: RequestedImageModel
    canonical_request_sha256: str
    attempt_ledger_path: str
    post_intent_ledger_path: str
    output_dir: str
    attempt_number: int = Field(ge=1, le=MAX_PHYSICAL_POSTS_PER_CELL)
    existing_attempt_count: int = Field(ge=0)
    existing_attempt_ledger_semantic_sha256: str
    existing_post_intent_count: int = Field(ge=0)
    existing_post_intent_ledger_semantic_sha256: str
    context_sha256: str

    @model_validator(mode="after")
    def context_is_consistent(self) -> "RequestGateContext":
        payload = self.model_dump(mode="json", exclude={"context_sha256"})
        if stable_hash(payload) != self.context_sha256:
            raise ValueError("request gate context hash is stale")
        if any(
            str(Path(value).resolve()) != value
            for value in (
                self.attempt_ledger_path,
                self.post_intent_ledger_path,
                self.output_dir,
            )
        ):
            raise ValueError("request gate execution paths must be canonical absolute paths")
        return self

    @field_validator(
        "transport_config_sha256",
        "oauth_runtime_fingerprint_sha256",
        "cell_identity_sha256",
        "source_schedule_row_sha256",
        "canonical_request_sha256",
        "existing_attempt_ledger_semantic_sha256",
        "existing_post_intent_ledger_semantic_sha256",
        "context_sha256",
    )
    @classmethod
    def request_gate_hashes(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("request gate context hashes must be SHA-256")
        return value


RequestGate = Callable[[RequestGateContext], bool]


class OnePostTransport(Protocol):
    config: Pilot3TransportConfig

    def post_once(self, canonical_request: bytes) -> TransportExchange: ...


RuntimeRevalidator = Callable[
    [Pilot3TransportConfig, Pilot3OAuthRuntimeFingerprint],
    Pilot3OAuthRuntimeRevalidation,
]


_PATH_LOCKS_GUARD = threading.Lock()
_PATH_LOCKS: Dict[str, threading.RLock] = {}


def _path_lock(path: Path) -> threading.RLock:
    key = str(path.resolve())
    with _PATH_LOCKS_GUARD:
        return _PATH_LOCKS.setdefault(key, threading.RLock())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _canonical_row_bytes(model: BaseModel) -> bytes:
    return (canonical_json(model.model_dump(mode="json")) + "\n").encode("utf-8")


def post_intent_ledger_semantic_sha256(
    intents: Sequence[GenerationPostIntent],
) -> str:
    return stable_hash([intent.model_dump(mode="json") for intent in intents])


def generation_attempt_ledger_semantic_sha256(
    attempts: Sequence[GenerationAttempt],
) -> str:
    return stable_hash([attempt.model_dump(mode="json") for attempt in attempts])


def runtime_revalidation_ledger_semantic_sha256(
    records: Sequence[GenerationRuntimeRevalidationRecord],
) -> str:
    return stable_hash([record.model_dump(mode="json") for record in records])


def global_stop_ledger_semantic_sha256(
    rows: Sequence[GenerationGlobalStopDisposition],
) -> str:
    return stable_hash([row.model_dump(mode="json") for row in rows])


class GenerationGlobalStopLedger:
    """Immutable canonical JSONL proof for cells stopped before any intent/POST."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_name(f".{self.path.name}.lock")
        self._lock = _path_lock(self.path)

    def _validated_rows_from_bytes(
        self, raw: bytes, path: Optional[Path] = None
    ) -> List[GenerationGlobalStopDisposition]:
        if raw and not raw.endswith(b"\n"):
            raise ValueError(f"global-stop ledger has a torn final row: {path or self.path}")
        rows: List[GenerationGlobalStopDisposition] = []
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("global-stop ledger is not UTF-8") from exc
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line:
                raise ValueError(f"blank global-stop ledger row {line_number}")
            try:
                row = GenerationGlobalStopDisposition.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(
                    f"invalid global-stop ledger row {line_number}: {exc}"
                ) from exc
            if line.encode("utf-8") + b"\n" != _canonical_row_bytes(row):
                raise ValueError(f"global-stop row {line_number} is not canonical")
            rows.append(row)
        if [row.stop_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError("global-stop ledger sequence is not contiguous")
        if len({row.cell_id for row in rows}) != len(rows):
            raise ValueError("global-stop ledger contains duplicate cell ids")
        if len({row.source_request_id for row in rows}) != len(rows):
            raise ValueError("global-stop ledger contains duplicate request ids")
        return rows

    def rows(self) -> List[GenerationGlobalStopDisposition]:
        if not self.path.exists():
            return []
        with self._lock:
            return self._validated_rows_from_bytes(self.path.read_bytes(), self.path)

    def write_once(
        self, rows: Sequence[GenerationGlobalStopDisposition]
    ) -> List[GenerationGlobalStopDisposition]:
        values = [
            GenerationGlobalStopDisposition.model_validate(row.model_dump(mode="json"))
            for row in rows
        ]
        expected = b"".join(_canonical_row_bytes(row) for row in values)
        self._validated_rows_from_bytes(expected)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            lock_descriptor = os.open(
                self.lock_path, os.O_RDWR | os.O_CREAT, 0o600
            )
            try:
                fcntl.flock(lock_descriptor, fcntl.LOCK_EX)
                if self.path.exists():
                    existing_raw = self.path.read_bytes()
                    self._validated_rows_from_bytes(existing_raw, self.path)
                    if existing_raw == expected:
                        return values
                    raise RuntimeError(
                        "global-stop ledger is immutable once created"
                    )
                descriptor, temporary = tempfile.mkstemp(
                    prefix=f".{self.path.name}.", dir=self.path.parent
                )
                try:
                    with os.fdopen(descriptor, "wb") as handle:
                        handle.write(expected)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, self.path)
                    _fsync_directory(self.path.parent)
                except BaseException:
                    try:
                        os.unlink(temporary)
                    except FileNotFoundError:
                        pass
                    raise
                return values
            finally:
                fcntl.flock(lock_descriptor, fcntl.LOCK_UN)
                os.close(lock_descriptor)


class AppendOnlyPostIntentLedger:
    """Canonical JSONL journal fsync'd before every possible POST."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = _path_lock(self.path)

    def _validated_rows_from_text(
        self, text: str, path: Optional[Path] = None
    ) -> List[GenerationPostIntent]:
        if text and not text.endswith("\n"):
            raise ValueError(f"post-intent ledger has a torn final row: {path or self.path}")
        rows: List[GenerationPostIntent] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line:
                raise ValueError(f"blank post-intent ledger row {line_number}")
            try:
                row = GenerationPostIntent.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(
                    f"invalid post-intent ledger row {line_number}: {exc}"
                ) from exc
            if line.encode("utf-8") + b"\n" != _canonical_row_bytes(row):
                raise ValueError(f"post-intent row {line_number} is not canonical")
            rows.append(row)
        if [row.intent_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError("post-intent ledger sequence is not contiguous")
        if len({row.attempt_id for row in rows}) != len(rows):
            raise ValueError("post-intent ledger contains duplicate attempt ids")
        if len({(row.cell_id, row.attempt_number) for row in rows}) != len(rows):
            raise ValueError("post-intent ledger contains duplicate attempt coordinates")
        for index, row in enumerate(rows):
            if row.prior_ledger_semantic_sha256 != post_intent_ledger_semantic_sha256(
                rows[:index]
            ):
                raise ValueError("post-intent ledger prefix hash chain is stale")
        return rows

    def rows(self) -> List[GenerationPostIntent]:
        if not self.path.exists():
            return []
        with self._lock:
            return self._validated_rows_from_text(
                self.path.read_text(encoding="utf-8"), self.path
            )

    def append_new(self, payload: Mapping[str, Any]) -> GenerationPostIntent:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            descriptor = os.open(
                self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600
            )
            try:
                with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    handle.seek(0)
                    existing = self._validated_rows_from_text(handle.read(), self.path)
                    value = dict(payload)
                    value.update(
                        {
                            "intent_sequence": len(existing) + 1,
                            "prior_ledger_semantic_sha256": (
                                post_intent_ledger_semantic_sha256(existing)
                            ),
                        }
                    )
                    value.pop("post_intent_sha256", None)
                    # Bind the JSON artifact, not Python's space-separated
                    # fallback representation of ``datetime``.
                    created_at = value.get("created_at")
                    if isinstance(created_at, datetime):
                        value["created_at"] = created_at.isoformat().replace(
                            "+00:00", "Z"
                        )
                    value["post_intent_sha256"] = stable_hash(value)
                    intent = GenerationPostIntent.model_validate(value)
                    if any(
                        row.attempt_id == intent.attempt_id
                        or (
                            row.cell_id,
                            row.attempt_number,
                        )
                        == (intent.cell_id, intent.attempt_number)
                        for row in existing
                    ):
                        raise ValueError("post-intent reservation collides with the ledger")
                    handle.seek(0, os.SEEK_END)
                    handle.write(canonical_json(intent.model_dump(mode="json")) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    _fsync_directory(self.path.parent)
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                    return intent
            except BaseException:
                raise


class AppendOnlyAttemptLedger:
    """Attempt JSONL plus immutable per-row receipts for crash recovery."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.sidecar_dir = self.path.parent / f".{self.path.name}.attempt_receipts"
        self.recovery_dir = self.path.parent / f".{self.path.name}.recovered_tails"
        self._lock = _path_lock(self.path)

    def _validated_rows_from_text(
        self,
        text: str,
        path: Optional[Path] = None,
        *,
        require_final_newline: bool = True,
    ) -> List[GenerationAttempt]:
        if require_final_newline and text and not text.endswith("\n"):
            raise ValueError(f"attempt ledger has a torn final row: {path or self.path}")
        rows: List[GenerationAttempt] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line:
                raise ValueError(f"blank attempt ledger row {line_number}")
            try:
                row = GenerationAttempt.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(f"invalid attempt ledger row {line_number}: {exc}") from exc
            if line.encode("utf-8") + b"\n" != _canonical_row_bytes(row):
                raise ValueError(f"attempt ledger row {line_number} is not canonical")
            rows.append(row)
        attempt_ids = [row.attempt_id for row in rows]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("attempt ledger contains duplicate ids")
        coordinates = [(row.cell_id, row.attempt_number) for row in rows]
        if len(coordinates) != len(set(coordinates)):
            raise ValueError("attempt ledger contains duplicate cell/attempt coordinates")
        return rows

    def rows(self) -> List[GenerationAttempt]:
        if not self.path.exists():
            return []
        with self._lock:
            return self._validated_rows_from_text(
                self.path.read_text(encoding="utf-8"), self.path
            )

    @staticmethod
    def _receipt_for_attempt(
        attempt: GenerationAttempt, prior_attempts: Sequence[GenerationAttempt]
    ) -> GenerationAttemptReceipt:
        payload: Dict[str, Any] = {
            "record_type": "pilot3_generation_attempt_receipt",
            "schema_version": "pilot3-generation-attempt-receipt-v2",
            "ledger_row_index": len(prior_attempts),
            "ledger_prefix_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(prior_attempts)
            ),
            "attempt": attempt.model_dump(mode="json"),
        }
        payload["receipt_sha256"] = stable_hash(payload)
        return GenerationAttemptReceipt.model_validate(payload)

    def _write_receipt(
        self, attempt: GenerationAttempt, prior_attempts: Sequence[GenerationAttempt]
    ) -> Path:
        sidecar_was_missing = not self.sidecar_dir.exists()
        self.sidecar_dir.mkdir(parents=True, exist_ok=True)
        if sidecar_was_missing:
            _fsync_directory(self.sidecar_dir.parent)
        path = self.sidecar_dir / f"{attempt.attempt_id}.json"
        expected = _canonical_row_bytes(self._receipt_for_attempt(attempt, prior_attempts))
        if path.exists():
            if path.read_bytes() != expected:
                raise RuntimeError(f"attempt receipt collision: {path}")
            return path
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.sidecar_dir)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(expected)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != expected:
                    raise RuntimeError(f"attempt receipt collision: {path}")
            finally:
                os.unlink(temporary)
            _fsync_directory(self.sidecar_dir)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise
        return path

    def receipt_rows(self) -> List[GenerationAttemptReceipt]:
        if not self.sidecar_dir.is_dir():
            return []
        receipts: List[GenerationAttemptReceipt] = []
        for path in sorted(self.sidecar_dir.glob("p3attempt-*.json")):
            try:
                raw = path.read_bytes()
                receipt = GenerationAttemptReceipt.model_validate_json(
                    raw.decode("utf-8")
                )
            except (UnicodeDecodeError, ValueError) as exc:
                raise ValueError(f"invalid attempt receipt {path}: {exc}") from exc
            if raw != _canonical_row_bytes(receipt):
                raise ValueError(f"attempt receipt is not canonical: {path}")
            if path.name != f"{receipt.attempt.attempt_id}.json":
                raise ValueError(f"attempt receipt filename disagrees with payload: {path}")
            receipts.append(receipt)
        ids = [receipt.attempt.attempt_id for receipt in receipts]
        if len(ids) != len(set(ids)):
            raise ValueError("attempt receipts contain duplicate ids")
        return receipts

    @staticmethod
    def _verify_receipt_prefixes(
        attempts: Sequence[GenerationAttempt],
        receipts: Sequence[GenerationAttemptReceipt],
        *,
        allow_one_extra: bool,
    ) -> Optional[GenerationAttemptReceipt]:
        by_id = {receipt.attempt.attempt_id: receipt for receipt in receipts}
        if len(by_id) != len(receipts):
            raise ValueError("attempt receipts contain duplicate ids")
        for index, attempt in enumerate(attempts):
            receipt = by_id.get(attempt.attempt_id)
            if receipt is None:
                raise RuntimeError("attempt receipts do not cover the exact ledger")
            if (
                receipt.ledger_row_index != index
                or receipt.ledger_prefix_semantic_sha256
                != generation_attempt_ledger_semantic_sha256(attempts[:index])
                or receipt.attempt.model_dump(mode="json")
                != attempt.model_dump(mode="json")
            ):
                raise RuntimeError("attempt receipt disagrees with its ledger prefix")
        attempt_ids = {attempt.attempt_id for attempt in attempts}
        extras = [
            receipt for receipt in receipts if receipt.attempt.attempt_id not in attempt_ids
        ]
        if not extras:
            return None
        if not allow_one_extra or len(extras) != 1:
            raise RuntimeError("attempt receipts do not cover the exact ledger")
        extra = extras[0]
        if (
            extra.ledger_row_index != len(attempts)
            or extra.ledger_prefix_semantic_sha256
            != generation_attempt_ledger_semantic_sha256(attempts)
        ):
            raise RuntimeError("extra receipt is not the exact final ledger append")
        return extra

    def verify_receipts(self, attempts: Optional[Sequence[GenerationAttempt]] = None) -> None:
        values = list(attempts) if attempts is not None else self.rows()
        self._verify_receipt_prefixes(values, self.receipt_rows(), allow_one_extra=False)

    def append(self, attempt: GenerationAttempt) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            descriptor = os.open(
                self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600
            )
            try:
                with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    handle.seek(0)
                    existing = self._validated_rows_from_text(handle.read(), self.path)
                    if any(row.attempt_id == attempt.attempt_id for row in existing):
                        raise ValueError("attempt id already exists")
                    if any(
                        (row.cell_id, row.attempt_number)
                        == (attempt.cell_id, attempt.attempt_number)
                        for row in existing
                    ):
                        raise ValueError("attempt coordinate already exists")
                    self._write_receipt(attempt, existing)
                    handle.seek(0, os.SEEK_END)
                    handle.write(canonical_json(attempt.model_dump(mode="json")) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    _fsync_directory(self.path.parent)
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except BaseException:
                raise

    def _preserve_torn_tail(self, trailing: bytes) -> None:
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        path = self.recovery_dir / f"{hash_bytes(trailing)}.partial"
        if path.exists():
            if path.read_bytes() != trailing:
                raise RuntimeError("torn-tail recovery evidence collision")
            return
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=self.recovery_dir)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(trailing)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, path)
            os.unlink(temporary)
            _fsync_directory(self.recovery_dir)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def recover_from_receipts(
        self, post_intent_ledger: AppendOnlyPostIntentLedger
    ) -> List[str]:
        """Recover only the exact final row proven by a durable receipt and intent."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        recovered: List[str] = []
        with self._lock:
            descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                with os.fdopen(descriptor, "r+b") as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    raw = handle.read()
                    trailing = b""
                    prefix = raw
                    if raw and not raw.endswith(b"\n"):
                        newline = raw.rfind(b"\n")
                        prefix = raw[: newline + 1] if newline >= 0 else b""
                        trailing = raw[newline + 1 :]
                    try:
                        attempts = self._validated_rows_from_text(
                            prefix.decode("utf-8"), self.path
                        )
                    except (UnicodeDecodeError, ValueError) as exc:
                        raise RuntimeError("attempt ledger damage is not recoverable") from exc
                    receipts = self.receipt_rows()
                    extra = self._verify_receipt_prefixes(
                        attempts, receipts, allow_one_extra=True
                    )
                    if trailing:
                        if extra is None or not _canonical_row_bytes(extra.attempt).startswith(
                            trailing
                        ):
                            raise RuntimeError(
                                "torn attempt tail does not match the durable final receipt"
                            )
                        self._preserve_torn_tail(trailing)
                        handle.seek(0)
                        handle.truncate(len(prefix))
                        handle.flush()
                        os.fsync(handle.fileno())
                    if extra is not None:
                        intents = {
                            intent.attempt_id: intent
                            for intent in post_intent_ledger.rows()
                        }
                        intent = intents.get(extra.attempt.attempt_id)
                        if (
                            intent is None
                            or extra.attempt.post_intent_sha256
                            != intent.post_intent_sha256
                            or extra.attempt.post_intent_sequence
                            != intent.intent_sequence
                        ):
                            raise RuntimeError(
                                "durable attempt receipt lacks its matching post intent"
                            )
                        handle.seek(0, os.SEEK_END)
                        handle.write(_canonical_row_bytes(extra.attempt))
                        handle.flush()
                        os.fsync(handle.fileno())
                        recovered.append(extra.attempt.attempt_id)
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except BaseException:
                raise
        self.verify_receipts(self.rows())
        return recovered

    def for_cell(self, cell_id: str) -> List[GenerationAttempt]:
        return sorted(
            (row for row in self.rows() if row.cell_id == cell_id),
            key=lambda row: row.attempt_number,
        )


class AppendOnlyRuntimeRevalidationLedger:
    """Canonical append-only journal of pre/post execution runtime checks."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._lock = _path_lock(self.path)

    def _validated_rows_from_text(
        self, text: str, path: Optional[Path] = None
    ) -> List[GenerationRuntimeRevalidationRecord]:
        if text and not text.endswith("\n"):
            raise ValueError(
                f"runtime revalidation ledger has a torn row: {path or self.path}"
            )
        rows: List[GenerationRuntimeRevalidationRecord] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            if not line:
                raise ValueError(f"blank runtime revalidation row {line_number}")
            try:
                row = GenerationRuntimeRevalidationRecord.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(
                    f"invalid runtime revalidation row {line_number}: {exc}"
                ) from exc
            if line.encode("utf-8") + b"\n" != _canonical_row_bytes(row):
                raise ValueError(f"runtime revalidation row {line_number} is not canonical")
            rows.append(row)
        if [row.ledger_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError("runtime revalidation ledger sequence is not contiguous")
        if len({row.record_id for row in rows}) != len(rows):
            raise ValueError("runtime revalidation ledger contains duplicate ids")
        for index, row in enumerate(rows):
            if row.prior_ledger_semantic_sha256 != (
                runtime_revalidation_ledger_semantic_sha256(rows[:index])
            ):
                raise ValueError("runtime revalidation prefix hash chain is stale")
        return rows

    def rows(self) -> List[GenerationRuntimeRevalidationRecord]:
        if not self.path.exists():
            return []
        with self._lock:
            return self._validated_rows_from_text(
                self.path.read_text(encoding="utf-8"), self.path
            )

    def append_new(
        self, payload: Mapping[str, Any]
    ) -> GenerationRuntimeRevalidationRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            descriptor = os.open(
                self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600
            )
            try:
                with os.fdopen(descriptor, "r+", encoding="utf-8", newline="\n") as handle:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    handle.seek(0)
                    existing = self._validated_rows_from_text(handle.read(), self.path)
                    value = dict(payload)
                    value.update(
                        {
                            "ledger_sequence": len(existing) + 1,
                            "prior_ledger_semantic_sha256": (
                                runtime_revalidation_ledger_semantic_sha256(existing)
                            ),
                        }
                    )
                    value.pop("runtime_revalidation_record_sha256", None)
                    value["runtime_revalidation_record_sha256"] = stable_hash(value)
                    record = GenerationRuntimeRevalidationRecord.model_validate(value)
                    handle.seek(0, os.SEEK_END)
                    handle.write(canonical_json(record.model_dump(mode="json")) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                    _fsync_directory(self.path.parent)
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                    return record
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
        for term in (
            "content_policy",
            "content policy",
            "content filter",
            "moderation",
            "safety",
            "refusal",
        )
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


def _store_content_addressed_png(output_dir: Path, image_bytes: bytes) -> tuple[Path, str]:
    digest = hash_bytes(image_bytes)
    root = output_dir.resolve()
    path = root / "sha256" / digest[:2] / f"{digest}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if hash_file(path) != digest:
            raise RuntimeError(f"content-address collision at {path}")
    else:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(image_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    return path, digest


def _base_attempt(
    cell: GenerationCell,
    intent: GenerationPostIntent,
    transport: OnePostTransport,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    exchange: TransportExchange,
) -> Dict[str, Any]:
    request = canonical_image_request_bytes(
        cell.prompt_text,
        cell.requested_model_label,
        frozen_requested_labels=transport.config.frozen_requested_labels,
    )
    return {
        "record_type": "pilot3_generation_attempt",
        "schema_version": "3.1",
        "attempt_id": intent.attempt_id,
        "cell_id": cell.cell_id,
        "cell_identity_sha256": cell.cell_identity_sha256,
        "attempt_number": intent.attempt_number,
        "post_intent_sequence": intent.intent_sequence,
        "post_intent_sha256": intent.post_intent_sha256,
        "requested_model_label": cell.requested_model_label,
        "source_request_id": cell.source_request_id,
        "source_sequence": cell.source_sequence,
        "source_repetition": cell.source_repetition,
        "source_schedule_row_sha256": cell.source_schedule_row_sha256,
        "source_prompt_row_sha256": cell.source_prompt_row_sha256,
        "source_paired_control_request_id": cell.source_paired_control_request_id,
        "source_neighbor_artist_id": cell.source_neighbor_artist_id,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "endpoint": transport.config.endpoint_url,
        "transport_config_sha256": transport.config.config_sha256,
        "execution_namespace": transport.config.execution_namespace,
        "http_method": "POST",
        "requested_size": REQUEST_SIZE,
        "requested_quality": REQUEST_QUALITY,
        "requested_output_format": REQUEST_OUTPUT_FORMAT,
        "canonical_request_utf8": request.decode("utf-8"),
        "canonical_request_sha256": hash_bytes(request),
        "canonical_request_byte_count": len(request),
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "pre_post_runtime_revalidation": (
            intent.pre_post_runtime_revalidation.model_dump(mode="json")
        ),
        "request_gate_context_sha256": intent.request_gate_context_sha256,
        "attempt_ledger_path": intent.attempt_ledger_path,
        "post_intent_ledger_path": intent.post_intent_ledger_path,
        "output_dir": intent.output_dir,
        "started_at": exchange.started_at,
        "completed_at": exchange.completed_at,
        "physical_post_may_have_executed": True,
        "post_exchange_observed": True,
        "http_status": exchange.http_status,
        "response_body_sha256": exchange.response_body_sha256,
        "response_body_byte_count": exchange.response_body_bytes,
        "response_metadata": exchange.response_metadata,
        "exact_dimensions_claimed": False,
        "dimension_evidence_scope": (
            "observed_output_only_size_auto_no_exact_dimension_claim"
        ),
    }


def _attempt_from_exchange(
    cell: GenerationCell,
    intent: GenerationPostIntent,
    transport: OnePostTransport,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    exchange: TransportExchange,
    output_dir: Path,
) -> GenerationAttempt:
    payload = _base_attempt(cell, intent, transport, fingerprint, exchange)
    if exchange.transport_error_kind is not None:
        retryable = exchange.transport_error_retryable is True
        if not retryable:
            payload.update(
                {
                    "post_exchange_observed": False,
                    "outcome": "terminal_failure",
                    "retry_classification": (
                        "not_retryable_indeterminate_after_interruption"
                    ),
                    "request_label_accepted": False,
                    "failure_kind": "indeterminate_after_interruption",
                    "failure_reason": sanitize_external_text(
                        "physical POST may have executed before the transport "
                        f"failed with {exchange.transport_error_kind}: "
                        + (
                            exchange.transport_error_reason
                            or exchange.transport_error_kind
                        ),
                        1000,
                    ),
                }
            )
            return GenerationAttempt.model_validate(payload)
        payload.update(
            {
                "outcome": "retryable_failure",
                "retry_classification": "retryable_transport",
                "request_label_accepted": False,
                "failure_kind": sanitize_external_text(
                    exchange.transport_error_kind, 200
                ),
                "failure_reason": sanitize_external_text(
                    exchange.transport_error_reason or exchange.transport_error_kind,
                    1000,
                ),
            }
        )
        return GenerationAttempt.model_validate(payload)

    if exchange.http_status is None:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_transport",
                "request_label_accepted": False,
                "failure_kind": "missing_http_status",
                "failure_reason": "transport returned neither an HTTP status nor an error",
            }
        )
        return GenerationAttempt.model_validate(payload)

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
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_response",
                "failure_kind": "invalid_response",
                "failure_reason": sanitize_external_text(
                    f"response is not valid JSON: {type(exc).__name__}", 1000
                ),
            }
        )
        return GenerationAttempt.model_validate(payload)

    if isinstance(response, dict) and "error" in response:
        code, message = _response_error(exchange.response_body)
        if _is_refusal(code, message):
            payload.update(
                {
                    "outcome": "refused",
                    "retry_classification": "not_retryable_refusal",
                    "failure_kind": code,
                    "failure_reason": message,
                }
            )
            return GenerationAttempt.model_validate(payload)

    try:
        if not isinstance(response, dict):
            raise TypeError("top-level response is not an object")
        data = response["data"]
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise TypeError("data must contain exactly one image item")
        item = data[0]
        encoded = item["b64_json"]
        if not isinstance(encoded, str):
            raise TypeError("b64_json is not a string")
        image_bytes = base64.b64decode(encoded, validate=True)
        if not image_bytes:
            raise ValueError("decoded image is empty")
    except (KeyError, TypeError, ValueError, binascii.Error) as exc:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_response",
                "failure_kind": "invalid_response",
                "failure_reason": sanitize_external_text(
                    f"missing or invalid data[0].b64_json: {exc}", 1000
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
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "invalid_image",
                "failure_reason": sanitize_external_text(
                    f"{type(exc).__name__}: {exc}", 1000
                ),
                "output_format_contract_satisfied": False,
                "kim_geometry_contract_satisfied": False,
            }
        )
        return GenerationAttempt.model_validate(payload)

    payload.update(
        {
            "actual_width": width,
            "actual_height": height,
            "actual_format": image_format,
            "output_format_contract_satisfied": image_format == "png",
            "kim_geometry_contract_satisfied": _eligible_output_geometry(width, height),
        }
    )
    if image_format != "png":
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "unexpected_output_format",
                "failure_reason": f"requested PNG but decoded {image_format}",
            }
        )
        return GenerationAttempt.model_validate(payload)
    if not _eligible_output_geometry(width, height):
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_invalid_image",
                "failure_kind": "ineligible_kim_geometry",
                "failure_reason": (
                    "decoded PNG falls outside strict Kim area/aspect-ratio eligibility"
                ),
            }
        )
        return GenerationAttempt.model_validate(payload)

    try:
        path, digest = _store_content_addressed_png(output_dir, image_bytes)
    except (OSError, RuntimeError) as exc:
        payload.update(
            {
                "outcome": "terminal_failure",
                "retry_classification": "not_retryable_output_error",
                "failure_kind": "output_storage_error",
                "failure_reason": sanitize_external_text(
                    f"{type(exc).__name__}: {exc}", 1000
                ),
            }
        )
        return GenerationAttempt.model_validate(payload)

    revised_prompt = item.get("revised_prompt")
    usage = response.get("usage")
    payload.update(
        {
            "outcome": "succeeded",
            "retry_classification": "not_retryable_success",
            "output_path": str(path),
            "output_sha256": digest,
            "revised_prompt": (
                sanitize_external_text(revised_prompt, 4000)
                if isinstance(revised_prompt, str)
                else None
            ),
            "usage": _numeric_usage(usage) if isinstance(usage, dict) else {},
        }
    )
    return GenerationAttempt.model_validate(payload)


def _validated_attempts_by_cell(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> Dict[str, List[GenerationAttempt]]:
    cell_ids = [cell.cell_id for cell in cells]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("generation cells contain duplicate ids")
    by_cell: Dict[str, List[GenerationAttempt]] = {cell_id: [] for cell_id in cell_ids}
    cell_index = {cell.cell_id: cell for cell in cells}
    attempt_ids: set[str] = set()
    fingerprints: set[str] = set()
    configs: set[str] = set()
    for attempt in attempts:
        if attempt.attempt_id in attempt_ids:
            raise ValueError(f"duplicate attempt id: {attempt.attempt_id}")
        attempt_ids.add(attempt.attempt_id)
        fingerprints.add(attempt.oauth_runtime_fingerprint_sha256)
        configs.add(attempt.transport_config_sha256)
        if attempt.cell_id not in by_cell:
            raise ValueError(f"attempt references unexpected cell: {attempt.cell_id}")
        cell = cell_index[attempt.cell_id]
        if (
            attempt.cell_identity_sha256 != cell.cell_identity_sha256
            or attempt.requested_model_label != cell.requested_model_label
            or attempt.canonical_request_sha256 != cell.canonical_request_sha256
            or attempt.source_request_id != cell.source_request_id
            or attempt.source_sequence != cell.source_sequence
            or attempt.source_repetition != cell.source_repetition
            or attempt.source_schedule_row_sha256
            != cell.source_schedule_row_sha256
            or attempt.source_prompt_row_sha256 != cell.source_prompt_row_sha256
            or attempt.source_paired_control_request_id
            != cell.source_paired_control_request_id
            or attempt.source_neighbor_artist_id != cell.source_neighbor_artist_id
        ):
            raise ValueError(f"attempt provenance disagrees with cell: {attempt.cell_id}")
        by_cell[attempt.cell_id].append(attempt)
    if len(fingerprints) > 1 or len(configs) > 1:
        raise ValueError("Pilot-3 grid spans runtime fingerprints or transport configs")
    for cell_id, rows in by_cell.items():
        rows.sort(key=lambda row: row.attempt_number)
        if [row.attempt_number for row in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f"attempt numbers are not contiguous: {cell_id}")
        if len(rows) > MAX_PHYSICAL_POSTS_PER_CELL:
            raise ValueError(f"cell exceeds fixed retry cap: {cell_id}")
        if any(row.outcome != "retryable_failure" for row in rows[:-1]):
            raise ValueError(f"attempt exists after a terminal outcome: {cell_id}")
    return by_cell


def verify_post_intent_attempt_bijection(
    intents: Sequence[GenerationPostIntent],
    attempts: Sequence[GenerationAttempt],
    cells: Sequence[GenerationCell],
    *,
    allow_unmatched: bool = False,
) -> None:
    cell_index = {cell.cell_id: cell for cell in cells}
    if len(cell_index) != len(cells):
        raise ValueError("generation cells contain duplicate ids")
    intents_by_id = {intent.attempt_id: intent for intent in intents}
    attempts_by_id = {attempt.attempt_id: attempt for attempt in attempts}
    if len(intents_by_id) != len(intents) or len(attempts_by_id) != len(attempts):
        raise ValueError("intent or attempt ids are duplicated")
    for intent in intents:
        cell = cell_index.get(intent.cell_id)
        if cell is None:
            raise ValueError(f"post intent references unexpected cell: {intent.cell_id}")
        if (
            intent.cell_identity_sha256 != cell.cell_identity_sha256
            or intent.requested_model_label != cell.requested_model_label
            or intent.canonical_request_sha256 != cell.canonical_request_sha256
            or intent.source_request_id != cell.source_request_id
            or intent.source_sequence != cell.source_sequence
            or intent.source_repetition != cell.source_repetition
            or intent.source_schedule_row_sha256 != cell.source_schedule_row_sha256
            or intent.source_prompt_row_sha256 != cell.source_prompt_row_sha256
            or intent.source_paired_control_request_id
            != cell.source_paired_control_request_id
            or intent.source_neighbor_artist_id != cell.source_neighbor_artist_id
        ):
            raise ValueError(f"post intent provenance disagrees with cell: {intent.cell_id}")
    if [intent.intent_sequence for intent in intents] != list(
        range(1, len(intents) + 1)
    ):
        raise ValueError("post intent sequence is not canonical")
    if [attempt.post_intent_sequence for attempt in attempts] != list(
        range(1, len(attempts) + 1)
    ):
        raise ValueError("attempt ledger does not follow post-intent order")
    for index, intent in enumerate(intents):
        preceding_attempts = list(attempts[:index])
        context_payload: Dict[str, Any] = {
            "record_type": "pilot3_request_gate_context",
            "schema_version": "pilot3-request-gate-context-v1",
            "transport_config_sha256": intent.transport_config_sha256,
            "oauth_runtime_fingerprint_sha256": (
                intent.oauth_runtime_fingerprint_sha256
            ),
            "cell_id": intent.cell_id,
            "cell_identity_sha256": intent.cell_identity_sha256,
            "source_request_id": intent.source_request_id,
            "source_schedule_row_sha256": intent.source_schedule_row_sha256,
            "requested_model_label": intent.requested_model_label,
            "canonical_request_sha256": intent.canonical_request_sha256,
            "attempt_ledger_path": intent.attempt_ledger_path,
            "post_intent_ledger_path": intent.post_intent_ledger_path,
            "output_dir": intent.output_dir,
            "attempt_number": intent.attempt_number,
            "existing_attempt_count": len(preceding_attempts),
            "existing_attempt_ledger_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(preceding_attempts)
            ),
            "existing_post_intent_count": index,
            "existing_post_intent_ledger_semantic_sha256": (
                post_intent_ledger_semantic_sha256(intents[:index])
            ),
        }
        context_payload["context_sha256"] = stable_hash(context_payload)
        expected_context = RequestGateContext.model_validate(context_payload)
        if intent.request_gate_context_sha256 != expected_context.context_sha256:
            raise RuntimeError(
                f"post intent lacks its exact request gate context: {intent.attempt_id}"
            )
    for attempt in attempts:
        intent = intents_by_id.get(attempt.attempt_id)
        if intent is None:
            raise RuntimeError(f"attempt lacks a pre-send intent: {attempt.attempt_id}")
        if (
            attempt.post_intent_sequence != intent.intent_sequence
            or attempt.post_intent_sha256 != intent.post_intent_sha256
            or attempt.cell_id != intent.cell_id
            or attempt.attempt_number != intent.attempt_number
            or attempt.transport_config_sha256 != intent.transport_config_sha256
            or attempt.oauth_runtime_fingerprint_sha256
            != intent.oauth_runtime_fingerprint_sha256
            or attempt.pre_post_runtime_revalidation
            != intent.pre_post_runtime_revalidation
            or attempt.source_request_id != intent.source_request_id
            or attempt.source_sequence != intent.source_sequence
            or attempt.source_repetition != intent.source_repetition
            or attempt.source_schedule_row_sha256
            != intent.source_schedule_row_sha256
            or attempt.source_prompt_row_sha256 != intent.source_prompt_row_sha256
            or attempt.source_paired_control_request_id
            != intent.source_paired_control_request_id
            or attempt.source_neighbor_artist_id != intent.source_neighbor_artist_id
            or attempt.request_gate_context_sha256
            != intent.request_gate_context_sha256
            or attempt.attempt_ledger_path != intent.attempt_ledger_path
            or attempt.post_intent_ledger_path != intent.post_intent_ledger_path
            or attempt.output_dir != intent.output_dir
        ):
            raise RuntimeError(f"attempt disagrees with post intent: {attempt.attempt_id}")
    by_cell: Dict[str, List[GenerationPostIntent]] = {}
    for intent in intents:
        by_cell.setdefault(intent.cell_id, []).append(intent)
    for cell_id, rows in by_cell.items():
        ordered = sorted(rows, key=lambda row: row.attempt_number)
        if [row.attempt_number for row in ordered] != list(range(1, len(rows) + 1)):
            raise RuntimeError(f"post intents are not contiguous for cell: {cell_id}")
        unmatched = [row for row in ordered if row.attempt_id not in attempts_by_id]
        if len(unmatched) > 1 or (unmatched and unmatched[0] is not ordered[-1]):
            raise RuntimeError(f"post-intent resolution order is invalid for cell: {cell_id}")
    unmatched_ids = sorted(set(intents_by_id) - set(attempts_by_id))
    if unmatched_ids and not allow_unmatched:
        raise RuntimeError(
            "unmatched post intent requires interruption reconciliation: "
            + ", ".join(unmatched_ids)
        )


def reconcile_unmatched_post_intents(
    cells: Sequence[GenerationCell],
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
) -> List[GenerationAttempt]:
    """Terminalize uncertain sends without issuing another physical POST."""

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
            "record_type": "pilot3_generation_attempt",
            "schema_version": "3.1",
            "attempt_id": intent.attempt_id,
            "cell_id": intent.cell_id,
            "cell_identity_sha256": intent.cell_identity_sha256,
            "attempt_number": intent.attempt_number,
            "post_intent_sequence": intent.intent_sequence,
            "post_intent_sha256": intent.post_intent_sha256,
            "requested_model_label": intent.requested_model_label,
            "source_request_id": intent.source_request_id,
            "source_sequence": intent.source_sequence,
            "source_repetition": intent.source_repetition,
            "source_schedule_row_sha256": intent.source_schedule_row_sha256,
            "source_prompt_row_sha256": intent.source_prompt_row_sha256,
            "source_paired_control_request_id": (
                intent.source_paired_control_request_id
            ),
            "source_neighbor_artist_id": intent.source_neighbor_artist_id,
            "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
            "executed_model_claims": False,
            "snapshot_identity_claims": False,
            "endpoint": intent.endpoint,
            "transport_config_sha256": intent.transport_config_sha256,
            "execution_namespace": intent.execution_namespace,
            "http_method": "POST",
            "requested_size": REQUEST_SIZE,
            "requested_quality": REQUEST_QUALITY,
            "requested_output_format": REQUEST_OUTPUT_FORMAT,
            "canonical_request_utf8": intent.canonical_request_utf8,
            "canonical_request_sha256": intent.canonical_request_sha256,
            "canonical_request_byte_count": intent.canonical_request_byte_count,
            "oauth_runtime_fingerprint_sha256": intent.oauth_runtime_fingerprint_sha256,
            "pre_post_runtime_revalidation": (
                intent.pre_post_runtime_revalidation.model_dump(mode="json")
            ),
            "request_gate_context_sha256": intent.request_gate_context_sha256,
            "attempt_ledger_path": intent.attempt_ledger_path,
            "post_intent_ledger_path": intent.post_intent_ledger_path,
            "output_dir": intent.output_dir,
            "started_at": intent.created_at,
            "completed_at": datetime.now(timezone.utc),
            "physical_post_may_have_executed": True,
            "post_exchange_observed": False,
            "outcome": "terminal_failure",
            "retry_classification": "not_retryable_indeterminate_after_interruption",
            "request_label_accepted": False,
            "response_body_byte_count": 0,
            "response_metadata": {},
            "failure_kind": "indeterminate_after_interruption",
            "failure_reason": (
                "physical POST may have executed before interruption; no exchange result "
                "was observed and automatic resend is prohibited"
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


def _validate_existing_attempts(
    cell: GenerationCell,
    attempts: Sequence[GenerationAttempt],
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    config: Pilot3TransportConfig,
    *,
    attempt_ledger_path: Path,
    post_intent_ledger_path: Path,
    output_dir: Path,
) -> None:
    ordered = sorted(attempts, key=lambda attempt: attempt.attempt_number)
    if [attempt.attempt_number for attempt in ordered] != list(
        range(1, len(ordered) + 1)
    ):
        raise ValueError(f"existing attempts are not contiguous: {cell.cell_id}")
    if len(ordered) > MAX_PHYSICAL_POSTS_PER_CELL:
        raise ValueError(f"existing attempts exceed the fixed cap: {cell.cell_id}")
    for index, attempt in enumerate(ordered):
        if (
            attempt.cell_id != cell.cell_id
            or attempt.cell_identity_sha256 != cell.cell_identity_sha256
            or attempt.requested_model_label != cell.requested_model_label
            or attempt.canonical_request_sha256 != cell.canonical_request_sha256
            or attempt.source_request_id != cell.source_request_id
            or attempt.source_sequence != cell.source_sequence
            or attempt.source_repetition != cell.source_repetition
            or attempt.source_schedule_row_sha256
            != cell.source_schedule_row_sha256
            or attempt.source_prompt_row_sha256 != cell.source_prompt_row_sha256
            or attempt.source_paired_control_request_id
            != cell.source_paired_control_request_id
            or attempt.source_neighbor_artist_id != cell.source_neighbor_artist_id
            or attempt.oauth_runtime_fingerprint_sha256
            != fingerprint.fingerprint_sha256
            or attempt.transport_config_sha256 != config.config_sha256
            or attempt.endpoint != config.endpoint_url
            or attempt.execution_namespace != config.execution_namespace
            or attempt.attempt_ledger_path != str(attempt_ledger_path.resolve())
            or attempt.post_intent_ledger_path
            != str(post_intent_ledger_path.resolve())
            or attempt.output_dir != str(output_dir.resolve())
        ):
            raise ValueError(f"existing attempt provenance is stale: {cell.cell_id}")
        if index < len(ordered) - 1 and attempt.outcome != "retryable_failure":
            raise ValueError(f"attempt follows a terminal outcome: {cell.cell_id}")


def _request_gate_context(
    *,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    cell: GenerationCell,
    attempt_number: int,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    output_dir: Path,
) -> RequestGateContext:
    attempts = ledger.rows()
    intents = post_intent_ledger.rows()
    payload: Dict[str, Any] = {
        "record_type": "pilot3_request_gate_context",
        "schema_version": "pilot3-request-gate-context-v1",
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "cell_id": cell.cell_id,
        "cell_identity_sha256": cell.cell_identity_sha256,
        "source_request_id": cell.source_request_id,
        "source_schedule_row_sha256": cell.source_schedule_row_sha256,
        "requested_model_label": cell.requested_model_label,
        "canonical_request_sha256": cell.canonical_request_sha256,
        "attempt_ledger_path": str(ledger.path.resolve()),
        "post_intent_ledger_path": str(post_intent_ledger.path.resolve()),
        "output_dir": str(Path(output_dir).resolve()),
        "attempt_number": attempt_number,
        "existing_attempt_count": len(attempts),
        "existing_attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(attempts)
        ),
        "existing_post_intent_count": len(intents),
        "existing_post_intent_ledger_semantic_sha256": (
            post_intent_ledger_semantic_sha256(intents)
        ),
    }
    payload["context_sha256"] = stable_hash(payload)
    return RequestGateContext.model_validate(payload)


def _require_open_request_gate(
    gate: Optional[RequestGate], context: RequestGateContext
) -> None:
    if gate is None:
        raise RequestGateClosed("Pilot-3 per-request gate callback is required")
    try:
        result = gate(context)
    except BaseException as exc:
        raise RequestGateClosed("Pilot-3 per-request gate callback failed closed") from exc
    if result is not True:
        raise RequestGateClosed("Pilot-3 per-request gate did not return literal True")


def generate_cell(
    cell: GenerationCell,
    *,
    transport: OnePostTransport,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    output_dir: Path,
    request_gate: Optional[RequestGate],
    runtime_revalidator: RuntimeRevalidator,
    sleep: Callable[[float], None] = time.sleep,
) -> GenerationAttempt:
    """Execute one cell under the exact ten-POST stopping rule."""

    config = transport.config
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    if not fingerprint.runtime_ready:
        raise ValueError("OAuth runtime fingerprint is not ready for Pilot-3 generation")
    if cell.requested_model_label not in config.frozen_requested_labels:
        raise ValueError("cell requested label is outside the frozen transport subset")
    GenerationCell.model_validate(cell.model_dump(mode="json"))

    existing = ledger.for_cell(cell.cell_id)
    intents = post_intent_ledger.rows()
    intent_by_id = {intent.attempt_id: intent for intent in intents}
    all_attempt_ids = {attempt.attempt_id for attempt in ledger.rows()}
    unmatched_for_cell = [
        intent
        for intent in intents
        if intent.cell_id == cell.cell_id and intent.attempt_id not in all_attempt_ids
    ]
    if unmatched_for_cell:
        raise RuntimeError(
            f"cell {cell.cell_id} has an unreconciled interrupted post intent"
        )
    for attempt in existing:
        intent = intent_by_id.get(attempt.attempt_id)
        if (
            intent is None
            or attempt.post_intent_sha256 != intent.post_intent_sha256
            or attempt.post_intent_sequence != intent.intent_sequence
        ):
            raise RuntimeError(f"cell {cell.cell_id} attempts lack matching post intents")
    _validate_existing_attempts(
        cell,
        existing,
        fingerprint,
        config,
        attempt_ledger_path=ledger.path,
        post_intent_ledger_path=post_intent_ledger.path,
        output_dir=Path(output_dir),
    )
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
        remaining = max(0.0, required_delay - elapsed)
        if remaining > 0:
            sleep(remaining)

    request = canonical_image_request_bytes(
        cell.prompt_text,
        cell.requested_model_label,
        frozen_requested_labels=config.frozen_requested_labels,
    )
    attempt: GenerationAttempt
    for attempt_number in range(len(existing) + 1, MAX_PHYSICAL_POSTS_PER_CELL + 1):
        request_context = _request_gate_context(
            config=config,
            fingerprint=fingerprint,
            cell=cell,
            attempt_number=attempt_number,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            output_dir=output_dir,
        )
        # A fresh live check is required for every physical POST/retry.  Its
        # complete self-hashed evidence is then fsync'd inside the intent.
        pre_post_runtime = runtime_revalidator(config, fingerprint)
        if (
            pre_post_runtime.persisted_fingerprint_sha256
            != fingerprint.fingerprint_sha256
            or pre_post_runtime.transport_config_sha256 != config.config_sha256
            or pre_post_runtime.endpoint_url != config.endpoint_url
            or pre_post_runtime.frozen_requested_labels
            != list(config.frozen_requested_labels)
        ):
            raise RuntimeError(
                "pre-POST runtime revalidation is bound to another execution"
            )
        # The committed request gate remains the final check immediately before
        # the sole fsynced intent/POST sequence.
        _require_open_request_gate(request_gate, request_context)
        intent = post_intent_ledger.append_new(
            {
                "record_type": "pilot3_generation_post_intent",
                "schema_version": "pilot3-generation-post-intent-v2",
                "attempt_id": f"p3attempt-{uuid.uuid4().hex}",
                "cell_id": cell.cell_id,
                "cell_identity_sha256": cell.cell_identity_sha256,
                "attempt_number": attempt_number,
                "requested_model_label": cell.requested_model_label,
                "source_request_id": cell.source_request_id,
                "source_sequence": cell.source_sequence,
                "source_repetition": cell.source_repetition,
                "source_schedule_row_sha256": cell.source_schedule_row_sha256,
                "source_prompt_row_sha256": cell.source_prompt_row_sha256,
                "source_paired_control_request_id": (
                    cell.source_paired_control_request_id
                ),
                "source_neighbor_artist_id": cell.source_neighbor_artist_id,
                "endpoint": config.endpoint_url,
                "transport_config_sha256": config.config_sha256,
                "execution_namespace": config.execution_namespace,
                "canonical_request_utf8": request.decode("utf-8"),
                "canonical_request_sha256": hash_bytes(request),
                "canonical_request_byte_count": len(request),
                "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
                "pre_post_runtime_revalidation": pre_post_runtime.model_dump(
                    mode="json"
                ),
                "request_gate_context_sha256": request_context.context_sha256,
                "attempt_ledger_path": request_context.attempt_ledger_path,
                "post_intent_ledger_path": request_context.post_intent_ledger_path,
                "output_dir": request_context.output_dir,
                "created_at": datetime.now(timezone.utc),
                "physical_post_may_have_executed": True,
            }
        )
        # This is the sole physical POST site; the transport itself has no retry loop.
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


def _cell_disposition(attempts: Sequence[GenerationAttempt]) -> CellDisposition:
    if not attempts:
        return "not_attempted"
    final = attempts[-1]
    if final.outcome == "succeeded":
        return "succeeded"
    if final.outcome == "refused":
        return "refused"
    if final.outcome == "terminal_failure":
        return "terminal_failure"
    if len(attempts) >= MAX_PHYSICAL_POSTS_PER_CELL:
        return "failed_after_retry_cap"
    return "retry_pending"


def _global_stop_disposition_rows(
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    attempts: Sequence[GenerationAttempt],
    intents: Sequence[GenerationPostIntent],
    runtime_preflight: Mapping[str, Any],
) -> List[GenerationGlobalStopDisposition]:
    """Derive every no-POST row after a terminal runtime-preflight failure."""

    if runtime_preflight.get("status") != "fail":
        raise ValueError("global-stop rows require a failed runtime image preflight")
    preflight_cells = select_runtime_image_preflight_cells(
        cells, schedule.frozen_requested_labels
    )
    if len(preflight_cells) != 1:
        raise ValueError("Pilot-3 global stop requires exactly one preflight cell")
    preflight = preflight_cells[0]
    attempted_cell_ids = {attempt.cell_id for attempt in attempts}
    intent_cell_ids = {intent.cell_id for intent in intents}
    if not attempted_cell_ids or not attempted_cell_ids.issubset({preflight.cell_id}):
        raise RuntimeError(
            "runtime-preflight global stop found an attempt outside the preflight cell"
        )
    if intent_cell_ids != attempted_cell_ids:
        raise RuntimeError(
            "runtime-preflight global stop has an intent/attempt cell mismatch"
        )
    preflight_attempts = sorted(
        (attempt for attempt in attempts if attempt.cell_id == preflight.cell_id),
        key=lambda value: value.attempt_number,
    )
    if _cell_disposition(preflight_attempts) in {"not_attempted", "retry_pending"}:
        raise RuntimeError("failed runtime preflight lacks a terminal attempt")
    grid_sha256 = generation_grid_sha256(cells)
    attempts_count = len(attempts)
    intents_count = len(intents)
    rows: List[GenerationGlobalStopDisposition] = []
    ordered = sorted(cells, key=lambda cell: int(cell.source_sequence or 0))
    for cell in ordered:
        if cell.cell_id in attempted_cell_ids:
            continue
        if (
            not cell.source_manifest_bound
            or cell.source_request_id is None
            or cell.source_sequence is None
            or cell.source_schedule_row_sha256 is None
            or preflight.source_request_id is None
        ):
            raise ValueError("global-stop cells require complete T12 provenance")
        payload: Dict[str, Any] = {
            "record_type": "pilot3_generation_global_stop_disposition",
            "schema_version": "pilot3-generation-global-stop-disposition-v1",
            "stop_sequence": len(rows) + 1,
            "cell_id": cell.cell_id,
            "cell_identity_sha256": cell.cell_identity_sha256,
            "source_request_id": cell.source_request_id,
            "source_sequence": cell.source_sequence,
            "source_schedule_row_sha256": cell.source_schedule_row_sha256,
            "requested_model_label": cell.requested_model_label,
            "generation_grid_sha256": grid_sha256,
            "generation_schedule_sha256": schedule.schedule_sha256,
            "runtime_image_preflight_sha256": runtime_preflight["report_sha256"],
            "preflight_cell_id": preflight.cell_id,
            "preflight_source_request_id": preflight.source_request_id,
            "global_stop_reason": "runtime_image_preflight_failed",
            "terminal_category": "not_sent_global_stop",
            "physical_post_count": 0,
            "physical_post_may_have_executed": False,
            "post_intent_written": False,
            "fake_attempt_row_created": False,
            "attempts_at_stop_count": attempts_count,
            "post_intents_at_stop_count": intents_count,
        }
        payload["record_sha256"] = stable_hash(payload)
        rows.append(GenerationGlobalStopDisposition.model_validate(payload))
    return rows


def verify_generation_global_stop_dispositions(
    rows: Sequence[GenerationGlobalStopDisposition],
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    attempts: Sequence[GenerationAttempt],
    intents: Sequence[GenerationPostIntent],
    runtime_preflight: Mapping[str, Any],
) -> List[GenerationGlobalStopDisposition]:
    expected = _global_stop_disposition_rows(
        cells,
        schedule=schedule,
        attempts=attempts,
        intents=intents,
        runtime_preflight=runtime_preflight,
    )
    values = [
        GenerationGlobalStopDisposition.model_validate(row.model_dump(mode="json"))
        for row in rows
    ]
    if values != expected:
        raise ValueError("global-stop disposition ledger is stale or tampered")
    stopped_ids = {row.cell_id for row in values}
    if any(
        intent.cell_id in stopped_ids for intent in intents
    ) or any(attempt.cell_id in stopped_ids for attempt in attempts):
        raise RuntimeError("global-stop cell has an intent or fake attempt row")
    return expected


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
    if attempt.outcome != "succeeded":
        raise ValueError("successful-output verification received a non-success attempt")
    if not attempt.output_path or not attempt.output_sha256:
        raise RuntimeError(f"successful output lacks path/hash: {attempt.cell_id}")
    path = _resolve_recorded_output_path(attempt.output_path, output_root)
    if not path.is_file():
        raise FileNotFoundError(f"successful output is missing: {path}")
    observed_sha256 = hash_file(path)
    if observed_sha256 != attempt.output_sha256:
        raise RuntimeError(f"successful output SHA-256 mismatch: {attempt.cell_id}")
    if path.name != f"{attempt.output_sha256}.png":
        raise RuntimeError(f"output path is not content-addressed PNG: {attempt.cell_id}")
    observed_byte_count = path.stat().st_size
    if (
        attempt.decoded_output_byte_count is not None
        and observed_byte_count != attempt.decoded_output_byte_count
    ):
        raise RuntimeError(f"output byte count mismatch: {attempt.cell_id}")
    try:
        with Image.open(path) as image:
            image.load()
            observed_format = (image.format or "unknown").lower()
            observed_width, observed_height = image.size
    except Exception as exc:
        raise RuntimeError(
            f"successful output does not decode: {attempt.cell_id}: {type(exc).__name__}"
        ) from exc
    if observed_format != "png":
        raise RuntimeError(f"successful output is not PNG: {attempt.cell_id}")
    if (observed_width, observed_height) != (
        attempt.actual_width,
        attempt.actual_height,
    ):
        raise RuntimeError(f"output dimensions disagree with ledger: {attempt.cell_id}")
    if not _eligible_output_geometry(observed_width, observed_height):
        raise RuntimeError(f"output violates strict Kim geometry: {attempt.cell_id}")
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
        "strict_kim_geometry_eligible": True,
    }


def verify_successful_output_artifacts(
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    *,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
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
                "content_block_id": cell.content_block_id,
                "prompt_pair_id": cell.prompt_pair_id,
                "target_artist_id": cell.target_artist_id,
                "artist_free_control": cell.artist_free_control,
                "repetition": cell.repetition,
                "source_request_id": cell.source_request_id,
                "source_sequence": cell.source_sequence,
                "source_repetition": cell.source_repetition,
                "source_schedule_row_sha256": cell.source_schedule_row_sha256,
                "source_prompt_row_sha256": cell.source_prompt_row_sha256,
                "source_semantic_request_sha256": (
                    cell.source_semantic_request_sha256
                ),
                "source_paired_control_request_id": (
                    cell.source_paired_control_request_id
                ),
                "source_neighbor_artist_id": cell.source_neighbor_artist_id,
            }
        )
        outputs.append(evidence)
    payload: Dict[str, Any] = {
        "record_type": "pilot3_successful_output_manifest",
        "schema_version": "pilot3-successful-output-manifest-v1",
        "generation_grid_sha256": generation_grid_sha256(cells),
        "successful_output_count": len(outputs),
        "outputs": outputs,
        "contains_raw_image_bytes": False,
        "strict_kim_geometry_required": True,
    }
    payload["successful_output_manifest_sha256"] = stable_hash(payload)
    return payload


def generation_completion_report(
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    *,
    frozen_requested_labels: Sequence[str],
    output_root: Optional[Path] = None,
    global_stop_dispositions: Sequence[GenerationGlobalStopDisposition] = (),
    global_stop_triggered: bool = False,
) -> Dict[str, Any]:
    labels = validate_frozen_requested_labels(frozen_requested_labels)
    validate_generation_cells(cells, labels)
    by_cell = _validated_attempts_by_cell(cells, attempts)
    stopped_by_cell = {
        row.cell_id: GenerationGlobalStopDisposition.model_validate(
            row.model_dump(mode="json")
        )
        for row in global_stop_dispositions
    }
    if len(stopped_by_cell) != len(global_stop_dispositions):
        raise ValueError("global-stop dispositions contain duplicate cell ids")
    if not set(stopped_by_cell).issubset(by_cell):
        raise ValueError("global-stop disposition is outside the generation grid")
    if any(by_cell[cell_id] for cell_id in stopped_by_cell):
        raise ValueError("global-stop cells cannot contain physical attempts")
    dispositions = {}
    for cell_id, rows in by_cell.items():
        dispositions[cell_id] = (
            "not_sent_global_stop" if cell_id in stopped_by_cell else _cell_disposition(rows)
        )
    resolved_global_stop = global_stop_triggered or bool(stopped_by_cell)
    if resolved_global_stop:
        no_attempt_ids = {cell_id for cell_id, rows in by_cell.items() if not rows}
        if set(stopped_by_cell) != no_attempt_ids:
            raise ValueError(
                "global-stop ledger must cover every and only no-attempt cell"
            )
    manifest_bound = all(cell.source_manifest_bound for cell in cells)
    source_request_dispositions = (
        {
            str(cell.source_request_id): dispositions[cell.cell_id]
            for cell in cells
        }
        if manifest_bound
        else {}
    )
    source_schedule_row_hashes = (
        {
            str(cell.source_request_id): str(cell.source_schedule_row_sha256)
            for cell in cells
        }
        if manifest_bound
        else {}
    )
    disposition_counts = Counter(dispositions.values())
    by_model: Dict[str, Dict[str, int]] = {}
    for label in labels:
        model_dispositions = Counter(
            dispositions[cell.cell_id]
            for cell in cells
            if cell.requested_model_label == label
        )
        by_model[label] = dict(sorted(model_dispositions.items()))
    all_terminal = all(
        disposition
        in {
            "succeeded",
            "refused",
            "terminal_failure",
            "failed_after_retry_cap",
            "not_sent_global_stop",
        }
        for disposition in dispositions.values()
    )
    all_succeeded = bool(cells) and all(
        disposition == "succeeded" for disposition in dispositions.values()
    )
    outputs = verify_successful_output_artifacts(
        cells, attempts, output_root=output_root
    )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_completion",
        "schema_version": "pilot3-generation-completion-v2",
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "scope_statement": OPERATIONAL_SCOPE_STATEMENT,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "exact_dimensions_claimed": False,
        "strict_kim_geometry_required": True,
        "fixed_max_physical_posts_per_cell": MAX_PHYSICAL_POSTS_PER_CELL,
        "fixed_retry_delays_seconds": list(FIXED_RETRY_DELAYS_SECONDS),
        "retryable_exact_http_statuses": sorted(RETRYABLE_EXACT_HTTP_STATUSES),
        "retryable_http_status_range": "500-599",
        "frozen_requested_labels": list(labels),
        "generation_grid_sha256": generation_grid_sha256(cells),
        "source_manifest_bound": manifest_bound,
        "cell_count": len(cells),
        "attempt_count": len(attempts),
        "attempt_count_semantics": (
            "durable pre-send intents resolved to observed exchanges or conservative "
            "indeterminate-after-interruption terminal rows"
        ),
        "post_exchange_observed_attempt_count": sum(
            attempt.post_exchange_observed for attempt in attempts
        ),
        "indeterminate_after_interruption_count": sum(
            attempt.failure_kind == "indeterminate_after_interruption"
            for attempt in attempts
        ),
        "attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(attempts)
        ),
        "global_stop_triggered": resolved_global_stop,
        "global_stop_disposition_count": len(stopped_by_cell),
        "global_stop_ledger_semantic_sha256": (
            global_stop_ledger_semantic_sha256(list(stopped_by_cell.values()))
        ),
        "physical_post_or_indeterminate_cell_count": sum(
            bool(rows) for rows in by_cell.values()
        ),
        "no_post_cell_count": len(stopped_by_cell),
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "by_requested_model_label": by_model,
        "cell_dispositions": dict(sorted(dispositions.items())),
        "source_request_dispositions": dict(
            sorted(source_request_dispositions.items())
        ),
        "source_schedule_row_hashes": dict(
            sorted(source_schedule_row_hashes.items())
        ),
        "all_cells_terminal": all_terminal,
        "all_cells_succeeded": all_succeeded,
        "generation_output_eligible_for_preprocessing_count": (
            disposition_counts.get("succeeded", 0)
        ),
        "generation_output_unavailable_count": (
            len(cells) - disposition_counts.get("succeeded", 0)
        ),
        "analysis_usable_image_status": (
            "pending_frozen_preprocessing_and_a_vector_feature_qualification"
        ),
        "generation_success_is_final_analysis_usable_image": False,
        "successful_output_count": outputs["successful_output_count"],
        "successful_output_manifest_sha256": outputs[
            "successful_output_manifest_sha256"
        ],
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def verify_generation_completion_report(
    report: Mapping[str, Any],
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    *,
    frozen_requested_labels: Sequence[str],
    output_root: Optional[Path] = None,
    global_stop_dispositions: Sequence[GenerationGlobalStopDisposition] = (),
    global_stop_triggered: bool = False,
) -> Dict[str, Any]:
    expected = generation_completion_report(
        cells,
        attempts,
        frozen_requested_labels=frozen_requested_labels,
        output_root=output_root,
        global_stop_dispositions=global_stop_dispositions,
        global_stop_triggered=global_stop_triggered,
    )
    if dict(report) != expected:
        raise ValueError("generation completion report is stale or tampered")
    return expected


def verify_runtime_image_preflight(
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    *,
    frozen_requested_labels: Sequence[str],
) -> Dict[str, Any]:
    labels = validate_frozen_requested_labels(frozen_requested_labels)
    if len(cells) != len(labels):
        raise ValueError("runtime preflight requires exactly one cell per frozen label")
    if {cell.requested_model_label for cell in cells} != set(labels):
        raise ValueError("runtime preflight cells do not cover the frozen labels")
    by_cell = {cell.cell_id: [] for cell in cells}
    for attempt in attempts:
        if attempt.cell_id in by_cell:
            by_cell[attempt.cell_id].append(attempt)
    evidence: Dict[str, Any] = {}
    all_pass = fingerprint.runtime_ready
    for cell in cells:
        rows = sorted(by_cell[cell.cell_id], key=lambda row: row.attempt_number)
        final = rows[-1] if rows else None
        submitted = bool(rows) and all(
            json.loads(row.canonical_request_utf8).get("model")
            == cell.requested_model_label
            for row in rows
        )
        accepted = final is not None and final.request_label_accepted
        png_verified = False
        if final is not None and final.outcome == "succeeded":
            try:
                _verify_successful_output_attempt(final, output_root=None)
            except (FileNotFoundError, RuntimeError, ValueError):
                pass
            else:
                png_verified = True
        passed = bool(submitted and accepted and png_verified)
        all_pass = all_pass and passed
        evidence[cell.requested_model_label] = {
            "cell_id": cell.cell_id,
            "physical_post_or_indeterminate_count": len(rows),
            "exact_requested_label_submitted": submitted,
            "requested_label_accepted_by_endpoint": accepted,
            "png_hash_and_strict_kim_geometry_verified": png_verified,
            "executed_model_claims": False,
            "snapshot_identity_claims": False,
            "status": "pass" if passed else "fail",
        }
    payload: Dict[str, Any] = {
        "record_type": "pilot3_runtime_image_preflight",
        "schema_version": "pilot3-runtime-image-preflight-v1",
        "status": "pass" if all_pass else "fail",
        "study_role": "first_analytic_request_fail_stop_after_generation_gate",
        "counts_in_frozen_320_request_grid": True,
        "transport_qualification_p3_t11_claimed": False,
        "frozen_requested_labels": list(labels),
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "scope_statement": OPERATIONAL_SCOPE_STATEMENT,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "oauth_runtime_ready": fingerprint.runtime_ready,
        "models": evidence,
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def verified_attempt_receipt_manifest(
    ledger: AppendOnlyAttemptLedger,
    attempts: Optional[Sequence[GenerationAttempt]] = None,
) -> Dict[str, Any]:
    values = list(attempts) if attempts is not None else ledger.rows()
    ledger.verify_receipts(values)
    receipts = sorted(ledger.receipt_rows(), key=lambda row: row.ledger_row_index)
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_attempt_receipt_manifest",
        "schema_version": "pilot3-generation-attempt-receipt-manifest-v2",
        "attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(values)
        ),
        "attempt_receipt_count": len(receipts),
        "receipt_sha256s": [receipt.receipt_sha256 for receipt in receipts],
    }
    payload["attempt_receipt_manifest_sha256"] = stable_hash(payload)
    return payload


def _execution_gate_context(
    *,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
) -> ExecutionGateContext:
    existing_attempts = ledger.rows()
    existing_intents = post_intent_ledger.rows()
    payload: Dict[str, Any] = {
        "record_type": "pilot3_execution_gate_context",
        "schema_version": "pilot3-execution-gate-context-v1",
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "generation_schedule_sha256": schedule.schedule_sha256,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "cell_count": len(cells),
        "existing_attempt_count": len(existing_attempts),
        "existing_attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(existing_attempts)
        ),
        "existing_post_intent_count": len(existing_intents),
        "existing_post_intent_ledger_semantic_sha256": (
            post_intent_ledger_semantic_sha256(existing_intents)
        ),
    }
    payload["context_sha256"] = stable_hash(payload)
    return ExecutionGateContext.model_validate(payload)


def build_generation_execution_context(
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
) -> ExecutionGateContext:
    """Build the deterministic, pre-network execution context for persistence."""

    validate_generation_cells(cells, config.frozen_requested_labels)
    _validate_schedule_against_cells(schedule, cells, config)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    return _execution_gate_context(
        config=config,
        fingerprint=fingerprint,
        cells=cells,
        schedule=schedule,
        ledger=ledger,
        post_intent_ledger=post_intent_ledger,
    )


def verify_generation_execution_context(
    context: ExecutionGateContext,
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
) -> ExecutionGateContext:
    """Verify a durable context and its exact on-disk ledger prefixes."""

    validate_generation_cells(cells, config.frozen_requested_labels)
    _validate_schedule_against_cells(schedule, cells, config)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    value = ExecutionGateContext.model_validate(context.model_dump(mode="json"))
    expected = {
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "generation_schedule_sha256": schedule.schedule_sha256,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "cell_count": len(cells),
    }
    for field, required in expected.items():
        if getattr(value, field) != required:
            raise ValueError(f"execution context is bound to another run: {field}")
    attempts = ledger.rows()
    intents = post_intent_ledger.rows()
    if (
        value.existing_attempt_count > len(attempts)
        or value.existing_attempt_ledger_semantic_sha256
        != generation_attempt_ledger_semantic_sha256(
            attempts[: value.existing_attempt_count]
        )
        or value.existing_post_intent_count > len(intents)
        or value.existing_post_intent_ledger_semantic_sha256
        != post_intent_ledger_semantic_sha256(
            intents[: value.existing_post_intent_count]
        )
    ):
        raise ValueError("execution context ledger-prefix binding is stale")
    return value


def _require_open_execution_gate(
    gate: Optional[ExecutionGate], context: ExecutionGateContext
) -> None:
    if gate is None:
        raise ExecutionGateClosed("Pilot-3 execution gate callback is required")
    try:
        result = gate(context)
    except BaseException as exc:
        raise ExecutionGateClosed("Pilot-3 execution gate callback failed closed") from exc
    if result is not True:
        raise ExecutionGateClosed("Pilot-3 execution gate did not return literal True")


def _validate_schedule_against_cells(
    schedule: GenerationSchedule,
    cells: Sequence[GenerationCell],
    config: Pilot3TransportConfig,
) -> None:
    if schedule.ordering_basis != "t12_canonical_sequence":
        raise ValueError("Pilot-3 execution requires the canonical T12 sequence adapter")
    if any(not cell.source_manifest_bound for cell in cells):
        raise ValueError("Pilot-3 execution requires manifest-bound generation cells")
    if schedule.generation_grid_sha256 != generation_grid_sha256(cells):
        raise ValueError("generation schedule binds a different grid")
    if schedule.frozen_requested_labels != list(config.frozen_requested_labels):
        raise ValueError("generation schedule binds a different requested-label subset")
    cell_index = {cell.cell_id: cell for cell in cells}
    if set(cell_index) != {entry.cell_id for entry in schedule.entries}:
        raise ValueError("generation schedule does not cover the exact grid")
    for entry in schedule.entries:
        cell = cell_index[entry.cell_id]
        if (
            entry.cell_identity_sha256 != cell.cell_identity_sha256
            or entry.content_block_id != cell.content_block_id
            or entry.requested_model_label != cell.requested_model_label
            or entry.repetition != cell.repetition
            or entry.source_request_id != cell.source_request_id
            or entry.source_sequence != cell.source_sequence
            or entry.source_schedule_row_sha256
            != cell.source_schedule_row_sha256
        ):
            raise ValueError(f"generation schedule entry is stale: {entry.cell_id}")


def _append_runtime_revalidation(
    *,
    phase: RuntimeRevalidationPhase,
    batch_rank: Optional[int],
    invocation_id: str,
    invocation_sequence: int,
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    transport: OnePostTransport,
    ledger: AppendOnlyAttemptLedger,
    runtime_ledger: AppendOnlyRuntimeRevalidationLedger,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    runtime_revalidator: RuntimeRevalidator,
) -> GenerationRuntimeRevalidationRecord:
    evidence = runtime_revalidator(transport.config, fingerprint)
    if (
        evidence.persisted_fingerprint_sha256 != fingerprint.fingerprint_sha256
        or evidence.transport_config_sha256 != transport.config.config_sha256
        or evidence.endpoint_url != transport.config.endpoint_url
        or evidence.frozen_requested_labels
        != list(transport.config.frozen_requested_labels)
    ):
        raise RuntimeError("runtime revalidation evidence is bound to another execution")
    attempts = ledger.rows()
    return runtime_ledger.append_new(
        {
            "record_type": "pilot3_generation_runtime_revalidation",
            "schema_version": "pilot3-generation-runtime-revalidation-v1",
            "record_id": f"p3runtime-{uuid.uuid4().hex}",
            "invocation_id": invocation_id,
            "invocation_sequence": invocation_sequence,
            "phase": phase,
            "batch_rank": batch_rank,
            "generation_grid_sha256": generation_grid_sha256(cells),
            "generation_schedule_sha256": schedule.schedule_sha256,
            "attempt_ledger_row_count": len(attempts),
            "attempt_ledger_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(attempts)
            ),
            "evidence": evidence.model_dump(mode="json"),
        }
    )


def verify_generation_runtime_revalidation_ledger(
    records: Sequence[GenerationRuntimeRevalidationRecord],
    attempts: Sequence[GenerationAttempt],
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    *,
    require_completed_generation: bool = False,
    global_stop_completed: bool = False,
) -> None:
    """Verify every observed POST interval follows a matching persisted check."""

    if not records:
        if attempts or require_completed_generation:
            raise RuntimeError("generation evidence lacks runtime revalidation records")
        return
    if [record.ledger_sequence for record in records] != list(
        range(1, len(records) + 1)
    ):
        raise ValueError("runtime revalidation sequence is not contiguous")
    expected_grid = generation_grid_sha256(cells)
    if any(
        record.generation_grid_sha256 != expected_grid
        or record.generation_schedule_sha256 != schedule.schedule_sha256
        or record.evidence.persisted_fingerprint_sha256
        != fingerprint.fingerprint_sha256
        for record in records
    ):
        raise RuntimeError("runtime revalidation ledger spans execution identities")
    for record in records:
        count = record.attempt_ledger_row_count
        if count > len(attempts):
            raise RuntimeError("runtime record points beyond the attempt ledger")
        if record.attempt_ledger_semantic_sha256 != (
            generation_attempt_ledger_semantic_sha256(attempts[:count])
        ):
            raise RuntimeError("runtime record attempt-prefix hash is stale")

    invocation_rows: Dict[str, List[GenerationRuntimeRevalidationRecord]] = {}
    invocation_order: List[str] = []
    for record in records:
        if record.invocation_id not in invocation_rows:
            invocation_order.append(record.invocation_id)
            invocation_rows[record.invocation_id] = []
        invocation_rows[record.invocation_id].append(record)
    flattened = [
        row for invocation_id in invocation_order for row in invocation_rows[invocation_id]
    ]
    if list(records) != flattened:
        raise RuntimeError("runtime revalidation invocations are interleaved")
    for rows in invocation_rows.values():
        if rows[0].phase != "start_before_runtime_image_preflight":
            raise RuntimeError("runtime invocation lacks its start check")
        if [row.invocation_sequence for row in rows] != list(range(1, len(rows) + 1)):
            raise RuntimeError("runtime invocation sequence is not contiguous")
        endings = [
            row
            for row in rows
            if row.phase
            in {"end_after_runtime_image_preflight", "end_after_all_batches"}
        ]
        if endings and (len(endings) != 1 or rows[-1] is not endings[0]):
            raise RuntimeError("runtime invocation has a non-final ending record")

    preflight_ids = {
        cell.cell_id
        for cell in select_runtime_image_preflight_cells(
            cells, schedule.frozen_requested_labels
        )
    }
    batch_ids: Dict[int, set[str]] = {}
    for entry in schedule.entries:
        batch_ids.setdefault(entry.batch_rank, set()).add(entry.cell_id)
    for index, record in enumerate(records):
        start = record.attempt_ledger_row_count
        end = (
            records[index + 1].attempt_ledger_row_count
            if index + 1 < len(records)
            else len(attempts)
        )
        if end < start:
            raise RuntimeError("runtime revalidation attempt counts move backwards")
        interval = attempts[start:end]
        observed_ids = {
            attempt.cell_id for attempt in interval if attempt.post_exchange_observed
        }
        if record.phase == "start_before_runtime_image_preflight":
            permitted = preflight_ids
        elif record.phase == "before_batch":
            assert record.batch_rank is not None
            permitted = batch_ids[record.batch_rank]
        else:
            permitted = set()
        if not observed_ids.issubset(permitted):
            raise RuntimeError("attempts were made outside their revalidated schedule phase")

    if require_completed_generation:
        final = records[-1]
        expected_phase = (
            "end_after_runtime_image_preflight"
            if global_stop_completed
            else "end_after_all_batches"
        )
        if (
            final.phase != expected_phase
            or final.attempt_ledger_row_count != len(attempts)
        ):
            raise RuntimeError("completed generation lacks its final runtime check")


def _generation_execution_payload(
    *,
    context: ExecutionGateContext,
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    global_stop_ledger: GenerationGlobalStopLedger,
    runtime_preflight: Mapping[str, Any],
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    attempts = ledger.rows()
    intents = post_intent_ledger.rows()
    runtime_records = runtime_revalidation_ledger.rows()
    stopped = global_stop_ledger.rows()
    global_stop = runtime_preflight.get("status") == "fail"
    for intent in intents:
        evidence = intent.pre_post_runtime_revalidation
        if (
            intent.oauth_runtime_fingerprint_sha256
            != fingerprint.fingerprint_sha256
            or intent.transport_config_sha256 != config.config_sha256
            or intent.endpoint != config.endpoint_url
            or intent.requested_model_label not in config.frozen_requested_labels
            or evidence.persisted_fingerprint_sha256
            != fingerprint.fingerprint_sha256
            or evidence.transport_config_sha256 != config.config_sha256
            or evidence.endpoint_url != config.endpoint_url
            or evidence.frozen_requested_labels
            != list(config.frozen_requested_labels)
        ):
            raise RuntimeError(
                "pre-POST runtime revalidation does not bind the frozen execution"
            )
    if global_stop:
        verify_generation_global_stop_dispositions(
            stopped,
            cells,
            schedule=schedule,
            attempts=attempts,
            intents=intents,
            runtime_preflight=runtime_preflight,
        )
        if not global_stop_ledger.path.is_file():
            raise RuntimeError("global-stop execution lacks its no-POST ledger file")
    elif stopped or global_stop_ledger.path.exists():
        raise RuntimeError("passing generation cannot carry a global-stop ledger")
    verify_post_intent_attempt_bijection(intents, attempts, cells)
    receipts = verified_attempt_receipt_manifest(ledger, attempts)
    verify_generation_runtime_revalidation_ledger(
        runtime_records,
        attempts,
        cells,
        schedule,
        fingerprint,
        require_completed_generation=True,
        global_stop_completed=global_stop,
    )
    completion = generation_completion_report(
        cells,
        attempts,
        frozen_requested_labels=config.frozen_requested_labels,
        output_root=output_root,
        global_stop_dispositions=stopped,
        global_stop_triggered=global_stop,
    )
    post_or_indeterminate_cell_ids = sorted(
        {attempt.cell_id for attempt in attempts}
    )
    observed_post_cell_ids = sorted(
        {
            attempt.cell_id
            for attempt in attempts
            if attempt.post_exchange_observed
        }
    )
    preflight_cell_ids = {
        cell.cell_id
        for cell in select_runtime_image_preflight_cells(
            cells, config.frozen_requested_labels
        )
    }
    if global_stop and set(post_or_indeterminate_cell_ids) != preflight_cell_ids:
        raise RuntimeError(
            "global-stop execution has a post or indeterminate intent outside "
            "the preflight cell"
        )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_execution",
        "schema_version": "pilot3-generation-execution-v3",
        "status": "global_stop_complete" if global_stop else (
            "complete" if completion["all_cells_terminal"] else "incomplete"
        ),
        "execution_gate_context": context.model_dump(mode="json"),
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "generation_schedule_sha256": schedule.schedule_sha256,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "runtime_image_preflight": dict(runtime_preflight),
        "runtime_image_preflight_sha256": runtime_preflight["report_sha256"],
        "runtime_image_preflight_is_p3_t11": False,
        "global_stop_triggered": global_stop,
        "global_stop_reason": (
            "runtime_image_preflight_failed" if global_stop else None
        ),
        "global_stop_ledger_path": str(global_stop_ledger.path.resolve()),
        "global_stop_ledger_file_sha256": (
            hash_file(global_stop_ledger.path) if global_stop else None
        ),
        "global_stop_disposition_count": len(stopped),
        "global_stop_ledger_semantic_sha256": (
            global_stop_ledger_semantic_sha256(stopped)
        ),
        "physical_post_or_indeterminate_cell_ids": post_or_indeterminate_cell_ids,
        "physical_post_or_indeterminate_cell_count": len(
            post_or_indeterminate_cell_ids
        ),
        "post_exchange_observed_cell_ids": observed_post_cell_ids,
        "post_exchange_observed_cell_count": len(observed_post_cell_ids),
        "no_post_cell_count": len(stopped),
        "only_preflight_cell_posted_or_indeterminate_before_global_stop": (
            set(post_or_indeterminate_cell_ids) == preflight_cell_ids
            if global_stop
            else None
        ),
        "fake_attempt_row_count": 0,
        "generation_completion": completion,
        "generation_completion_sha256": completion["report_sha256"],
        "per_physical_post_request_gate_required": True,
        "per_physical_post_runtime_revalidation_required": True,
        "pre_post_runtime_revalidation_count": len(intents),
        "pre_post_runtime_revalidation_semantic_sha256": stable_hash(
            [
                intent.pre_post_runtime_revalidation.revalidation_sha256
                for intent in intents
            ]
        ),
        "request_gate_context_count": len(intents),
        "request_gate_context_semantic_sha256": stable_hash(
            [intent.request_gate_context_sha256 for intent in intents]
        ),
        "post_intent_count": len(intents),
        "post_intent_ledger_semantic_sha256": (
            post_intent_ledger_semantic_sha256(intents)
        ),
        "attempt_count": len(attempts),
        "attempt_ledger_semantic_sha256": (
            generation_attempt_ledger_semantic_sha256(attempts)
        ),
        "attempt_receipt_manifest_sha256": receipts[
            "attempt_receipt_manifest_sha256"
        ],
        "runtime_revalidation_count": len(runtime_records),
        "runtime_revalidation_ledger_semantic_sha256": (
            runtime_revalidation_ledger_semantic_sha256(runtime_records)
        ),
        "final_runtime_revalidation_sha256": (
            runtime_records[-1].runtime_revalidation_record_sha256
        ),
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def reconstruct_generation_execution_report(
    context: ExecutionGateContext,
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    global_stop_ledger: GenerationGlobalStopLedger,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Reconstruct a completed report after a crash without sending a request."""

    verified_context = verify_generation_execution_context(
        context,
        cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=post_intent_ledger,
    )
    preflight = verify_runtime_image_preflight(
        select_runtime_image_preflight_cells(
            cells, config.frozen_requested_labels
        ),
        ledger.rows(),
        fingerprint,
        frozen_requested_labels=config.frozen_requested_labels,
    )
    return _generation_execution_payload(
        context=verified_context,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=post_intent_ledger,
        runtime_revalidation_ledger=runtime_revalidation_ledger,
        global_stop_ledger=global_stop_ledger,
        runtime_preflight=preflight,
        output_root=output_root,
    )


def run_generation_grid(
    cells: Sequence[GenerationCell],
    *,
    schedule: GenerationSchedule,
    transport: OnePostTransport,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    global_stop_ledger: GenerationGlobalStopLedger,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    output_dir: Path,
    execution_gate: Optional[ExecutionGate],
    request_gate: Optional[RequestGate],
    execution_context: Optional[ExecutionGateContext] = None,
    sleep: Callable[[float], None] = time.sleep,
    runtime_revalidator: RuntimeRevalidator = (
        revalidate_pilot3_oauth_runtime_fingerprint
    ),
) -> Dict[str, Any]:
    """Run the analytic runtime preflight then deterministic frozen batches."""

    config = transport.config
    validate_generation_cells(cells, config.frozen_requested_labels)
    _validate_schedule_against_cells(schedule, cells, config)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    context = (
        build_generation_execution_context(
            cells,
            schedule=schedule,
            config=config,
            fingerprint=fingerprint,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
        )
        if execution_context is None
        else verify_generation_execution_context(
            execution_context,
            cells,
            schedule=schedule,
            config=config,
            fingerprint=fingerprint,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
        )
    )
    # No probe, journal write, or POST occurs before literal authorization.
    _require_open_execution_gate(execution_gate, context)

    if global_stop_ledger.path.exists():
        # Even an empty file can represent the zero-unsent-cell edge case of a
        # previously completed global stop.  Never resume POSTs past it.
        global_stop_ledger.rows()
        raise RuntimeError("generation is terminal under an existing global-stop ledger")

    ledger.recover_from_receipts(post_intent_ledger)
    invocation_id = f"p3runtime-invocation-{uuid.uuid4().hex}"
    invocation_sequence = 1
    _append_runtime_revalidation(
        phase="start_before_runtime_image_preflight",
        batch_rank=None,
        invocation_id=invocation_id,
        invocation_sequence=invocation_sequence,
        cells=cells,
        schedule=schedule,
        transport=transport,
        ledger=ledger,
        runtime_ledger=runtime_revalidation_ledger,
        fingerprint=fingerprint,
        runtime_revalidator=runtime_revalidator,
    )
    reconcile_unmatched_post_intents(cells, ledger, post_intent_ledger, fingerprint)

    preflight_cells = select_runtime_image_preflight_cells(
        cells, config.frozen_requested_labels
    )
    for cell in preflight_cells:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            fingerprint=fingerprint,
            output_dir=output_dir,
            request_gate=request_gate,
            runtime_revalidator=runtime_revalidator,
            sleep=sleep,
        )
    runtime_preflight = verify_runtime_image_preflight(
        preflight_cells,
        ledger.rows(),
        fingerprint,
        frozen_requested_labels=config.frozen_requested_labels,
    )
    if runtime_preflight["status"] != "pass":
        invocation_sequence += 1
        _append_runtime_revalidation(
            phase="end_after_runtime_image_preflight",
            batch_rank=None,
            invocation_id=invocation_id,
            invocation_sequence=invocation_sequence,
            cells=cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            runtime_ledger=runtime_revalidation_ledger,
            fingerprint=fingerprint,
            runtime_revalidator=runtime_revalidator,
        )
        attempts = ledger.rows()
        intents = post_intent_ledger.rows()
        verify_post_intent_attempt_bijection(intents, attempts, cells)
        stopped = _global_stop_disposition_rows(
            cells,
            schedule=schedule,
            attempts=attempts,
            intents=intents,
            runtime_preflight=runtime_preflight,
        )
        global_stop_ledger.write_once(stopped)
        return _generation_execution_payload(
            context=context,
            cells=cells,
            schedule=schedule,
            config=config,
            fingerprint=fingerprint,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            runtime_revalidation_ledger=runtime_revalidation_ledger,
            global_stop_ledger=global_stop_ledger,
            runtime_preflight=runtime_preflight,
        )

    cell_index = {cell.cell_id: cell for cell in cells}
    entries_by_batch: Dict[int, List[GenerationScheduleEntry]] = {}
    for entry in schedule.entries:
        entries_by_batch.setdefault(entry.batch_rank, []).append(entry)
    for batch_rank in range(1, schedule.batch_count + 1):
        batch_cells = [
            cell_index[entry.cell_id]
            for entry in sorted(
                entries_by_batch[batch_rank], key=lambda item: item.within_batch_rank
            )
        ]
        existing_by_cell = _validated_attempts_by_cell(cells, ledger.rows())
        pending = [
            cell
            for cell in batch_cells
            if _cell_disposition(existing_by_cell[cell.cell_id])
            in {"not_attempted", "retry_pending"}
        ]
        if not pending:
            continue
        invocation_sequence += 1
        _append_runtime_revalidation(
            phase="before_batch",
            batch_rank=batch_rank,
            invocation_id=invocation_id,
            invocation_sequence=invocation_sequence,
            cells=cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            runtime_ledger=runtime_revalidation_ledger,
            fingerprint=fingerprint,
            runtime_revalidator=runtime_revalidator,
        )
        # T12 ``sequence`` is the authoritative send order. The frozen
        # ``max_parallel`` remains a batching/revalidation cap, while physical
        # sends are serialized so scheduling cannot reorder fsync'd intents or
        # POSTs.
        for cell in pending:
            generate_cell(
                cell,
                transport=transport,
                ledger=ledger,
                post_intent_ledger=post_intent_ledger,
                fingerprint=fingerprint,
                output_dir=output_dir,
                request_gate=request_gate,
                runtime_revalidator=runtime_revalidator,
                sleep=sleep,
            )

    invocation_sequence += 1
    _append_runtime_revalidation(
        phase="end_after_all_batches",
        batch_rank=None,
        invocation_id=invocation_id,
        invocation_sequence=invocation_sequence,
        cells=cells,
        schedule=schedule,
        transport=transport,
        ledger=ledger,
        runtime_ledger=runtime_revalidation_ledger,
        fingerprint=fingerprint,
        runtime_revalidator=runtime_revalidator,
    )
    return _generation_execution_payload(
        context=context,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=post_intent_ledger,
        runtime_revalidation_ledger=runtime_revalidation_ledger,
        global_stop_ledger=global_stop_ledger,
        runtime_preflight=runtime_preflight,
    )


def verify_generation_execution(
    report: Mapping[str, Any],
    *,
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    ledger: AppendOnlyAttemptLedger,
    post_intent_ledger: AppendOnlyPostIntentLedger,
    runtime_revalidation_ledger: AppendOnlyRuntimeRevalidationLedger,
    global_stop_ledger: GenerationGlobalStopLedger,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Recompute every durable binding without making a network request."""

    validate_generation_cells(cells, config.frozen_requested_labels)
    _validate_schedule_against_cells(schedule, cells, config)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    attempts = ledger.rows()
    intents = post_intent_ledger.rows()
    verify_post_intent_attempt_bijection(intents, attempts, cells)
    preflight_cells = select_runtime_image_preflight_cells(
        cells, config.frozen_requested_labels
    )
    runtime_preflight = verify_runtime_image_preflight(
        preflight_cells,
        attempts,
        fingerprint,
        frozen_requested_labels=config.frozen_requested_labels,
    )
    context_payload = dict(report.get("execution_gate_context", {}))
    context = ExecutionGateContext.model_validate(context_payload)
    expected_context_values = {
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "generation_schedule_sha256": schedule.schedule_sha256,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "cell_count": len(cells),
    }
    for key, value in expected_context_values.items():
        if getattr(context, key) != value:
            raise ValueError("execution gate context is bound to another run")
    if (
        context.existing_attempt_count > len(attempts)
        or context.existing_attempt_ledger_semantic_sha256
        != generation_attempt_ledger_semantic_sha256(
            attempts[: context.existing_attempt_count]
        )
        or context.existing_post_intent_count > len(intents)
        or context.existing_post_intent_ledger_semantic_sha256
        != post_intent_ledger_semantic_sha256(
            intents[: context.existing_post_intent_count]
        )
    ):
        raise ValueError("execution gate context ledger-prefix binding is stale")
    expected = _generation_execution_payload(
        context=context,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=post_intent_ledger,
        runtime_revalidation_ledger=runtime_revalidation_ledger,
        global_stop_ledger=global_stop_ledger,
        runtime_preflight=runtime_preflight,
        output_root=output_root,
    )
    if dict(report) != expected:
        raise ValueError("generation execution report is stale or tampered")
    return expected


__all__ = [
    "AppendOnlyAttemptLedger",
    "AppendOnlyPostIntentLedger",
    "AppendOnlyRuntimeRevalidationLedger",
    "DEFAULT_MAX_PARALLEL",
    "DEFAULT_SCHEDULE_NAMESPACE",
    "DEFAULT_SCHEDULE_SEED",
    "DEFAULT_T12_SCHEDULE_NAMESPACE",
    "ExecutionGate",
    "ExecutionGateClosed",
    "ExecutionGateContext",
    "FIXED_RETRY_DELAYS_SECONDS",
    "GenerationAttempt",
    "GenerationAttemptReceipt",
    "GenerationCell",
    "GenerationGlobalStopDisposition",
    "GenerationGlobalStopLedger",
    "GenerationPostIntent",
    "GenerationRuntimeRevalidationRecord",
    "GenerationSchedule",
    "GenerationScheduleEntry",
    "MAX_PHYSICAL_POSTS_PER_CELL",
    "MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE",
    "MIN_OUTPUT_AREA_EXCLUSIVE",
    "RETRYABLE_EXACT_HTTP_STATUSES",
    "RequestGate",
    "RequestGateClosed",
    "RequestGateContext",
    "adapt_t12_manifests_to_generation",
    "build_generation_execution_context",
    "build_generation_schedule",
    "generate_cell",
    "generation_attempt_ledger_semantic_sha256",
    "generation_completion_report",
    "generation_grid_sha256",
    "global_stop_ledger_semantic_sha256",
    "make_generation_cell",
    "load_t12_generation_plan",
    "post_intent_ledger_semantic_sha256",
    "reconcile_unmatched_post_intents",
    "reconstruct_generation_execution_report",
    "run_generation_grid",
    "runtime_revalidation_ledger_semantic_sha256",
    "select_runtime_image_preflight_cells",
    "validate_generation_cells",
    "verified_attempt_receipt_manifest",
    "verify_generation_completion_report",
    "verify_generation_execution",
    "verify_generation_execution_context",
    "verify_generation_global_stop_dispositions",
    "verify_generation_runtime_revalidation_ledger",
    "verify_post_intent_attempt_bijection",
    "verify_successful_output_artifacts",
    "verify_runtime_image_preflight",
]
