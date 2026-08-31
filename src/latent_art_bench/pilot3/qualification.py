"""One-shot, non-analytic Pilot-3 transport qualification (P3-T11).

This module is intentionally separate from the 320-request generation grid.  It
permits exactly one neutral Image API request after the frozen Phase-A external
result passes and before Freeze B exists.  A durable intent is fsync'd before
the POST; an unmatched intent is indeterminate and can never be resent.
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Mapping, Optional, Protocol, Tuple

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import canonical_json, hash_bytes, hash_file, read_json, stable_hash
from latent_art_bench.pilot3.generation import (
    MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE,
    MIN_OUTPUT_AREA_EXCLUSIVE,
)
from latent_art_bench.pilot3.transport import (
    OPERATIONAL_MODEL_ESTIMAND,
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthRuntimeRevalidation,
    Pilot3TransportConfig,
    TransportExchange,
    canonical_image_request_bytes,
    revalidate_pilot3_oauth_runtime_fingerprint,
    sanitize_external_text,
    verify_pilot3_oauth_runtime_fingerprint,
    verify_pilot3_production_runtime_fingerprint,
)

TRANSPORT_QUALIFICATION_ARTIFACT_PATH = Path(
    "reports/pilot_3/evidence/transport_qualification.json"
)
TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH = Path(
    "artifacts/pilot_3/transport_qualification_post_intents.jsonl"
)
TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH = Path(
    "artifacts/pilot_3/transport_qualification_attempts.jsonl"
)
TRANSPORT_QUALIFICATION_OUTPUT_ROOT = Path(
    "outputs/pilot_3/transport_qualification"
)
TRANSPORT_QUALIFICATION_REQUEST_ID = "p3-t11-neutral-transport-qualification-v1"
# P3-T11 and analytic generation deliberately share one frozen transport
# configuration/fingerprint. Separation is provided by the neutral request id,
# schemas, ledgers, output root, and artifact—not by manufacturing an
# incompatible transport-config hash.
TRANSPORT_QUALIFICATION_NAMESPACE = "pilot3-generation-v1"
TRANSPORT_QUALIFICATION_PROMPT = (
    "Create one original abstract image composed only of a centered blue circle, a small "
    "red square, and two pale gray horizontal bars on a plain white background. Use flat "
    "colors and simple clean edges. Do not depict a landscape, a person, an artist, an "
    "artistic style, or a recognizable existing artwork. Do not include text, lettering, "
    "a signature, a watermark, a border, a frame, or a collage."
)
TRANSPORT_QUALIFICATION_PROMPT_SHA256 = hash_bytes(
    TRANSPORT_QUALIFICATION_PROMPT.encode("utf-8")
)
EXPECTED_PHASE_A_RECORD_TYPE = "pilot3_a_vector_external_validation"
EXPECTED_PHASE_A_SCHEMA = "pilot3-a-vector-external-validation/1.0"
EXPECTED_ENDPOINT_URL = "http://127.0.0.1:10533/v1/images/generations"
EXPECTED_CHECKOUT = (Path.home() / "dev" / "openai-oauth").resolve()
ACCOUNT_AUTHORIZATION_SCHEMA = "pilot3-account-authorization/1.0"
MODEL_DOCUMENTATION_SCHEMA = "pilot3-model-documentation/1.0"
GPT_IMAGE_2_DOCUMENTATION_URL = (
    "https://developers.openai.com/api/docs/models/gpt-image-2"
)
ACCOUNT_AUTHORIZATION_RECORD_ID = (
    "pilot3-explicit-user-authorization-current-codex-task-2026-09-01"
)

QualificationOutcome = Literal[
    "passed",
    "policy_refusal",
    "http_failure",
    "transport_failure",
    "invalid_response",
    "invalid_image",
    "ineligible_geometry",
    "output_storage_failure",
]


class QualificationError(RuntimeError):
    """Fail-closed P3-T11 contract violation."""


class QualificationWindowClosed(QualificationError):
    """P3-T11 was attempted outside its Phase-A-pass/pre-Freeze-B window."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


class AccountAuthorizationEvidence(_StrictModel):
    """Exact user-authorized request scope consumed by the production gate."""

    record_type: Literal["pilot3_account_authorization"] = (
        "pilot3_account_authorization"
    )
    schema_version: Literal["pilot3-account-authorization/1.0"] = (
        ACCOUNT_AUTHORIZATION_SCHEMA
    )
    authorization_record_id: Literal[
        "pilot3-explicit-user-authorization-current-codex-task-2026-09-01"
    ] = ACCOUNT_AUTHORIZATION_RECORD_ID
    authorization_basis: Literal["explicit_user_instructions_in_current_codex_task"] = (
        "explicit_user_instructions_in_current_codex_task"
    )
    authorization_assertion: str = (
        "finish Pilot 3 using only gpt-image-1 and gpt-image-2 through "
        "~/dev/openai-oauth; the frozen prospective schedule uses only gpt-image-2"
    )
    user_allowed_image_model_family: Tuple[
        Literal["gpt-image-1"], Literal["gpt-image-2"]
    ] = ("gpt-image-1", "gpt-image-2")
    scheduled_requested_labels: Tuple[Literal["gpt-image-2"]] = ("gpt-image-2",)
    gpt_image_1_role: Literal["historical_comparator_only_not_scheduled"] = (
        "historical_comparator_only_not_scheduled"
    )
    transport: Literal["~/dev/openai-oauth"] = "~/dev/openai-oauth"
    checkout_path: str
    endpoint_url: Literal["http://127.0.0.1:10533/v1/images/generations"] = (
        EXPECTED_ENDPOINT_URL
    )
    direct_api_allowed: Literal[False] = False
    browser_or_chatgpt_generation_allowed: Literal[False] = False
    alternative_transport_or_model_fallback_allowed: Literal[False] = False
    qualification_request_id: Literal[
        "p3-t11-neutral-transport-qualification-v1"
    ] = TRANSPORT_QUALIFICATION_REQUEST_ID
    qualification_timing: Literal["after_exact_p3_t08_pass_before_p3_t14"] = (
        "after_exact_p3_t08_pass_before_p3_t14"
    )
    qualification_physical_post_budget: Literal[1] = 1
    qualification_retry_allowed: Literal[False] = False
    analytic_request_budget_after_committed_p3_t14: Literal[320] = 320
    account_identity_or_entitlement_claimed: Literal[False] = False
    evidence_sha256: str

    @model_validator(mode="after")
    def evidence_is_current(self) -> "AccountAuthorizationEvidence":
        unsigned = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if stable_hash(unsigned) != self.evidence_sha256:
            raise ValueError("account authorization evidence hash is stale")
        return self

    @field_validator("evidence_sha256")
    @classmethod
    def evidence_hash_is_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("account authorization evidence hash must be SHA-256")
        return value


class ModelDocumentationEvidence(_StrictModel):
    """Exact documented-label/local-implementation claim boundary for P3-T11."""

    record_type: Literal["pilot3_model_documentation"] = "pilot3_model_documentation"
    schema_version: Literal["pilot3-model-documentation/1.0"] = (
        MODEL_DOCUMENTATION_SCHEMA
    )
    documentation_accessed_date: Literal["2026-09-01"] = "2026-09-01"
    official_documentation_urls: Tuple[
        Literal["https://developers.openai.com/api/docs/models/gpt-image-2"]
    ] = (GPT_IMAGE_2_DOCUMENTATION_URL,)
    documented_requested_label: Literal["gpt-image-2"] = "gpt-image-2"
    documented_image_generation_endpoint: Literal["/v1/images/generations"] = (
        "/v1/images/generations"
    )
    local_supported_image_aliases: Tuple[
        Literal["gpt-image-1"], Literal["gpt-image-2"]
    ] = ("gpt-image-1", "gpt-image-2")
    dedicated_listener_exposed_labels: Tuple[Literal["gpt-image-2"]] = (
        "gpt-image-2",
    )
    dedicated_listener_exposed_labels_semantics: Literal[
        "catalog_advertisement_only_not_endpoint_allowlist"
    ] = "catalog_advertisement_only_not_endpoint_allowlist"
    models_flag_is_endpoint_allowlist: Literal[False] = False
    endpoint_accepted_image_aliases: Tuple[
        Literal["gpt-image-1"], Literal["gpt-image-2"]
    ] = ("gpt-image-1", "gpt-image-2")
    pilot3_client_canonical_allowed_labels: Tuple[Literal["gpt-image-2"]] = (
        "gpt-image-2",
    )
    transport_config_sha256: str
    oauth_runtime_fingerprint_sha256: str
    oauth_source_snapshot_sha256: str
    oauth_checkout_path: str
    oauth_git_head: str
    local_alias_support_is_execution_attestation: Literal[False] = False
    model_catalog_is_execution_attestation: Literal[False] = False
    executed_model_claims: Literal[False] = False
    snapshot_identity_claims: Literal[False] = False
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    limitation: str = (
        "documentation and local source/catalog evidence do not attest the upstream "
        "model or snapshot that executed any request"
    )
    evidence_sha256: str

    @model_validator(mode="after")
    def evidence_is_current(self) -> "ModelDocumentationEvidence":
        unsigned = self.model_dump(mode="json", exclude={"evidence_sha256"})
        if stable_hash(unsigned) != self.evidence_sha256:
            raise ValueError("model documentation evidence hash is stale")
        return self

    @field_validator(
        "transport_config_sha256",
        "oauth_runtime_fingerprint_sha256",
        "oauth_source_snapshot_sha256",
        "evidence_sha256",
    )
    @classmethod
    def evidence_hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("model documentation hashes must be SHA-256")
        return value


def build_account_authorization_evidence(
    config: Pilot3TransportConfig,
) -> AccountAuthorizationEvidence:
    validate_transport_qualification_config(config)
    payload: Dict[str, Any] = {
        "record_type": "pilot3_account_authorization",
        "schema_version": ACCOUNT_AUTHORIZATION_SCHEMA,
        "authorization_record_id": ACCOUNT_AUTHORIZATION_RECORD_ID,
        "authorization_basis": "explicit_user_instructions_in_current_codex_task",
        "authorization_assertion": (
            "finish Pilot 3 using only gpt-image-1 and gpt-image-2 through "
            "~/dev/openai-oauth; the frozen prospective schedule uses only gpt-image-2"
        ),
        "user_allowed_image_model_family": ["gpt-image-1", "gpt-image-2"],
        "scheduled_requested_labels": ["gpt-image-2"],
        "gpt_image_1_role": "historical_comparator_only_not_scheduled",
        "transport": "~/dev/openai-oauth",
        "checkout_path": str(EXPECTED_CHECKOUT),
        "endpoint_url": EXPECTED_ENDPOINT_URL,
        "direct_api_allowed": False,
        "browser_or_chatgpt_generation_allowed": False,
        "alternative_transport_or_model_fallback_allowed": False,
        "qualification_request_id": TRANSPORT_QUALIFICATION_REQUEST_ID,
        "qualification_timing": "after_exact_p3_t08_pass_before_p3_t14",
        "qualification_physical_post_budget": 1,
        "qualification_retry_allowed": False,
        "analytic_request_budget_after_committed_p3_t14": 320,
        "account_identity_or_entitlement_claimed": False,
    }
    payload["evidence_sha256"] = stable_hash(payload)
    return AccountAuthorizationEvidence.model_validate(payload)


def verify_account_authorization_evidence(
    value: Mapping[str, Any], config: Pilot3TransportConfig
) -> AccountAuthorizationEvidence:
    observed = AccountAuthorizationEvidence.model_validate(value)
    expected = build_account_authorization_evidence(config)
    if observed != expected:
        raise QualificationError(
            "account authorization evidence is not the exact current-task scope"
        )
    return expected


def build_model_documentation_evidence(
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
) -> ModelDocumentationEvidence:
    validate_transport_qualification_config(config)
    verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)
    payload: Dict[str, Any] = {
        "record_type": "pilot3_model_documentation",
        "schema_version": MODEL_DOCUMENTATION_SCHEMA,
        "documentation_accessed_date": "2026-09-01",
        "official_documentation_urls": [GPT_IMAGE_2_DOCUMENTATION_URL],
        "documented_requested_label": "gpt-image-2",
        "documented_image_generation_endpoint": "/v1/images/generations",
        "local_supported_image_aliases": ["gpt-image-1", "gpt-image-2"],
        "dedicated_listener_exposed_labels": ["gpt-image-2"],
        "dedicated_listener_exposed_labels_semantics": (
            "catalog_advertisement_only_not_endpoint_allowlist"
        ),
        "models_flag_is_endpoint_allowlist": False,
        "endpoint_accepted_image_aliases": ["gpt-image-1", "gpt-image-2"],
        "pilot3_client_canonical_allowed_labels": ["gpt-image-2"],
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "oauth_source_snapshot_sha256": fingerprint.source.source_snapshot_sha256,
        "oauth_checkout_path": str(EXPECTED_CHECKOUT),
        "oauth_git_head": fingerprint.source.git_head,
        "local_alias_support_is_execution_attestation": False,
        "model_catalog_is_execution_attestation": False,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "limitation": (
            "documentation and local source/catalog evidence do not attest the upstream "
            "model or snapshot that executed any request"
        ),
    }
    payload["evidence_sha256"] = stable_hash(payload)
    return ModelDocumentationEvidence.model_validate(payload)


def verify_model_documentation_evidence(
    value: Mapping[str, Any],
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
) -> ModelDocumentationEvidence:
    observed = ModelDocumentationEvidence.model_validate(value)
    expected = build_model_documentation_evidence(config, fingerprint)
    if observed != expected:
        raise QualificationError(
            "model documentation evidence is stale or outside the claim boundary"
        )
    return expected


def _json_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_json_now() -> str:
    return _json_time(datetime.now(timezone.utc))


def _canonical_row_bytes(value: BaseModel) -> bytes:
    return (canonical_json(value.model_dump(mode="json")) + "\n").encode("utf-8")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _verify_self_hash(
    value: Mapping[str, Any], *, field: str, label: str
) -> str:
    recorded = value.get(field)
    if not _is_sha256(recorded):
        raise QualificationError(f"{label} lacks a valid {field}")
    unsigned = dict(value)
    unsigned.pop(field, None)
    if stable_hash(unsigned) != recorded:
        raise QualificationError(f"{label} has a stale {field}")
    return str(recorded)


def load_phase_a_pass(path: Path) -> tuple[Dict[str, Any], str]:
    """Load the exact self-hashed P3-T08 pass required before P3-T11."""

    resolved = Path(path)
    if not resolved.is_file():
        raise QualificationWindowClosed("P3-T11 requires the Phase-A result file")
    value = read_json(resolved)
    if not isinstance(value, dict):
        raise QualificationWindowClosed("Phase-A result must be a JSON object")
    if (
        value.get("record_type") != EXPECTED_PHASE_A_RECORD_TYPE
        or value.get("schema_version") != EXPECTED_PHASE_A_SCHEMA
        or value.get("todo_id") != "P3-T08"
        or value.get("status") != "pass"
    ):
        raise QualificationWindowClosed("P3-T11 requires an exact terminal P3-T08 pass")
    _verify_self_hash(value, field="result_sha256", label="Phase-A result")
    checks = value.get("gate_checks")
    if (
        not isinstance(checks, dict)
        or not checks
        or any(passed is not True for passed in checks.values())
    ):
        raise QualificationWindowClosed("Phase-A pass has incomplete gate checks")
    return value, hash_file(resolved)


def validate_transport_qualification_config(config: Pilot3TransportConfig) -> None:
    """Require the exact shared analytic alias, listener, checkout, and namespace."""

    if (
        config.base_url != "http://127.0.0.1:10533/v1"
        or config.dedicated_port != 10533
        or config.endpoint_url != EXPECTED_ENDPOINT_URL
        or tuple(config.frozen_requested_labels) != ("gpt-image-2",)
        or config.checkout_path.resolve() != EXPECTED_CHECKOUT
        or config.required_checkout_path.resolve() != EXPECTED_CHECKOUT
        or config.execution_namespace != TRANSPORT_QUALIFICATION_NAMESPACE
    ):
        raise QualificationError(
            "P3-T11 requires gpt-image-2 on the dedicated 127.0.0.1:10533 listener "
            "from the exact ~/dev/openai-oauth checkout and frozen analytic namespace"
        )


def validate_transport_qualification_fingerprint(
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    config: Pilot3TransportConfig,
) -> None:
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    catalog = fingerprint.model_catalog.parsed_summary.get("model_ids")
    if (
        not fingerprint.runtime_ready
        or fingerprint.endpoint_url != EXPECTED_ENDPOINT_URL
        or fingerprint.frozen_requested_labels != ["gpt-image-2"]
        or catalog != ["gpt-image-2"]
        or Path(fingerprint.source.checkout_path).resolve() != EXPECTED_CHECKOUT
    ):
        raise QualificationError(
            "P3-T11 runtime fingerprint is not ready or its catalog is not exactly gpt-image-2"
        )


class QualificationGateContext(_StrictModel):
    record_type: Literal["pilot3_transport_qualification_gate_context"] = (
        "pilot3_transport_qualification_gate_context"
    )
    schema_version: Literal["pilot3-transport-qualification-gate-context-v1"] = (
        "pilot3-transport-qualification-gate-context-v1"
    )
    phase_a_record_type: Literal["pilot3_a_vector_external_validation"]
    phase_a_status: Literal["pass"]
    phase_a_result_sha256: str
    phase_a_result_file_sha256: str
    account_authorization_evidence_file_sha256: str
    model_documentation_evidence_file_sha256: str
    freeze_b_status_at_authorization: Literal["not_frozen"] = "not_frozen"
    analytic_generation_gate_status: Literal["closed"] = "closed"
    freeze_b_generation_gate_path_absent: Literal[True] = True
    transport_config_sha256: str
    oauth_runtime_fingerprint_sha256: str
    request_id: Literal["p3-t11-neutral-transport-qualification-v1"] = (
        "p3-t11-neutral-transport-qualification-v1"
    )
    canonical_request_sha256: str
    neutral_prompt_sha256: str
    existing_intent_count: Literal[0] = 0
    existing_attempt_count: Literal[0] = 0
    context_sha256: str

    @model_validator(mode="after")
    def context_is_current(self) -> "QualificationGateContext":
        unsigned = self.model_dump(mode="json", exclude={"context_sha256"})
        if stable_hash(unsigned) != self.context_sha256:
            raise ValueError("qualification gate context hash is stale")
        return self

    @field_validator(
        "phase_a_result_sha256",
        "phase_a_result_file_sha256",
        "account_authorization_evidence_file_sha256",
        "model_documentation_evidence_file_sha256",
        "transport_config_sha256",
        "oauth_runtime_fingerprint_sha256",
        "canonical_request_sha256",
        "neutral_prompt_sha256",
        "context_sha256",
    )
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("qualification gate hashes must be lowercase SHA-256")
        return value


QualificationGate = Callable[[QualificationGateContext], bool]


class QualificationIntent(_StrictModel):
    record_type: Literal["pilot3_transport_qualification_post_intent"] = (
        "pilot3_transport_qualification_post_intent"
    )
    schema_version: Literal["pilot3-transport-qualification-post-intent-v1"] = (
        "pilot3-transport-qualification-post-intent-v1"
    )
    request_id: Literal["p3-t11-neutral-transport-qualification-v1"]
    physical_post_number: Literal[1] = 1
    retry_allowed: Literal[False] = False
    analytic_grid_membership: Literal[False] = False
    phase_a_result_sha256: str
    phase_a_result_file_sha256: str
    account_authorization_evidence_file_sha256: str
    model_documentation_evidence_file_sha256: str
    freeze_b_status_at_authorization: Literal["not_frozen"] = "not_frozen"
    analytic_generation_gate_status: Literal["closed"] = "closed"
    transport_config_sha256: str
    oauth_runtime_fingerprint_sha256: str
    pre_request_runtime_revalidation: Pilot3OAuthRuntimeRevalidation
    requested_model_label: Literal["gpt-image-2"] = "gpt-image-2"
    endpoint_url: Literal["http://127.0.0.1:10533/v1/images/generations"] = (
        "http://127.0.0.1:10533/v1/images/generations"
    )
    canonical_request_utf8: str
    canonical_request_sha256: str
    canonical_request_byte_count: int = Field(gt=0)
    neutral_prompt_sha256: str
    created_at: datetime
    physical_post_may_have_executed: Literal[True] = True
    intent_sha256: str

    @model_validator(mode="after")
    def intent_is_current(self) -> "QualificationIntent":
        request = canonical_image_request_bytes(
            TRANSPORT_QUALIFICATION_PROMPT,
            "gpt-image-2",
            frozen_requested_labels=("gpt-image-2",),
        )
        if (
            self.canonical_request_utf8.encode("utf-8") != request
            or self.canonical_request_sha256 != hash_bytes(request)
            or self.canonical_request_byte_count != len(request)
            or self.neutral_prompt_sha256 != TRANSPORT_QUALIFICATION_PROMPT_SHA256
            or self.pre_request_runtime_revalidation.persisted_fingerprint_sha256
            != self.oauth_runtime_fingerprint_sha256
        ):
            raise ValueError("qualification intent request/runtime binding is stale")
        unsigned = self.model_dump(mode="json", exclude={"intent_sha256"})
        if stable_hash(unsigned) != self.intent_sha256:
            raise ValueError("qualification intent hash is stale")
        return self

    @field_validator(
        "phase_a_result_sha256",
        "phase_a_result_file_sha256",
        "account_authorization_evidence_file_sha256",
        "model_documentation_evidence_file_sha256",
        "transport_config_sha256",
        "oauth_runtime_fingerprint_sha256",
        "canonical_request_sha256",
        "neutral_prompt_sha256",
        "intent_sha256",
    )
    @classmethod
    def hashes_are_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("qualification intent hashes must be lowercase SHA-256")
        return value


class QualificationAttempt(_StrictModel):
    record_type: Literal["pilot3_transport_qualification_attempt"] = (
        "pilot3_transport_qualification_attempt"
    )
    schema_version: Literal["pilot3-transport-qualification-attempt-v1"] = (
        "pilot3-transport-qualification-attempt-v1"
    )
    request_id: Literal["p3-t11-neutral-transport-qualification-v1"]
    intent_sha256: str
    physical_post_count: Literal[1] = 1
    retry_count: Literal[0] = 0
    retry_allowed: Literal[False] = False
    requested_model_label: Literal["gpt-image-2"] = "gpt-image-2"
    endpoint_url: Literal["http://127.0.0.1:10533/v1/images/generations"] = (
        "http://127.0.0.1:10533/v1/images/generations"
    )
    oauth_runtime_fingerprint_sha256: str
    started_at: datetime
    completed_at: datetime
    http_status: Optional[int] = Field(default=None, ge=100, le=599)
    response_body_sha256: Optional[str] = None
    response_body_byte_count: int = Field(ge=0)
    response_metadata: Dict[str, str]
    transport_error_kind: Optional[str] = None
    transport_error_reason: Optional[str] = None
    outcome: QualificationOutcome
    request_label_accepted: bool
    failure_kind: Optional[str] = None
    failure_reason: Optional[str] = None
    output_path: Optional[str] = None
    output_sha256: Optional[str] = None
    output_byte_count: Optional[int] = Field(default=None, ge=1)
    actual_width: Optional[int] = Field(default=None, gt=0)
    actual_height: Optional[int] = Field(default=None, gt=0)
    actual_format: Optional[str] = None
    strict_kim_geometry_eligible: Optional[bool] = None
    post_request_runtime_revalidation: Pilot3OAuthRuntimeRevalidation
    executed_model_claims: Literal[False] = False
    snapshot_identity_claims: Literal[False] = False
    attempt_sha256: str

    @model_validator(mode="after")
    def attempt_is_current(self) -> "QualificationAttempt":
        if self.completed_at < self.started_at:
            raise ValueError("qualification attempt completed before it started")
        if (
            self.post_request_runtime_revalidation.persisted_fingerprint_sha256
            != self.oauth_runtime_fingerprint_sha256
        ):
            raise ValueError("qualification post-request runtime binding is stale")
        if self.outcome == "passed":
            if (
                not self.request_label_accepted
                or self.http_status is None
                or not 200 <= self.http_status <= 299
                or not self.output_path
                or not self.output_sha256
                or not self.output_byte_count
                or self.actual_format != "png"
                or self.strict_kim_geometry_eligible is not True
                or self.actual_width is None
                or self.actual_height is None
                or not _eligible_geometry(self.actual_width, self.actual_height)
            ):
                raise ValueError("passing qualification attempt lacks exact output evidence")
        elif self.output_path is not None:
            raise ValueError("failed qualification attempts cannot retain an analytic output")
        unsigned = self.model_dump(mode="json", exclude={"attempt_sha256"})
        if stable_hash(unsigned) != self.attempt_sha256:
            raise ValueError("qualification attempt hash is stale")
        return self

    @field_validator(
        "intent_sha256",
        "oauth_runtime_fingerprint_sha256",
        "response_body_sha256",
        "output_sha256",
        "attempt_sha256",
    )
    @classmethod
    def hashes_are_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("qualification attempt hashes must be lowercase SHA-256")
        return value


class _OneRowLedger:
    model_type: type[BaseModel]

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def row(self) -> Optional[BaseModel]:
        if not self.path.exists():
            return None
        raw = self.path.read_bytes()
        if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
            raise QualificationError(f"one-shot ledger is torn or has multiple rows: {self.path}")
        try:
            row = self.model_type.model_validate_json(raw.decode("utf-8").rstrip("\n"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise QualificationError(f"invalid one-shot ledger: {self.path}: {exc}") from exc
        if raw != _canonical_row_bytes(row):
            raise QualificationError(f"one-shot ledger row is not canonical: {self.path}")
        return row

    def append_once(self, row: BaseModel) -> None:
        if not isinstance(row, self.model_type):
            raise TypeError("one-shot ledger received the wrong row type")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        expected = _canonical_row_bytes(row)
        try:
            descriptor = os.open(
                self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
            )
        except FileExistsError as exc:
            raise QualificationError("one-shot qualification ledger is already consumed") from exc
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(expected)
                handle.flush()
                os.fsync(handle.fileno())
            _fsync_directory(self.path.parent)
        except BaseException:
            raise


class QualificationIntentLedger(_OneRowLedger):
    model_type = QualificationIntent

    def row(self) -> Optional[QualificationIntent]:
        value = super().row()
        return None if value is None else QualificationIntent.model_validate(value)

    def append_once(self, row: QualificationIntent) -> None:
        super().append_once(row)


class QualificationAttemptLedger(_OneRowLedger):
    model_type = QualificationAttempt

    def row(self) -> Optional[QualificationAttempt]:
        value = super().row()
        return None if value is None else QualificationAttempt.model_validate(value)

    def append_once(self, row: QualificationAttempt) -> None:
        super().append_once(row)


class OnePostTransport(Protocol):
    config: Pilot3TransportConfig

    def post_once(self, canonical_request: bytes) -> TransportExchange: ...


RuntimeRevalidator = Callable[
    [Pilot3TransportConfig, Pilot3OAuthRuntimeFingerprint],
    Pilot3OAuthRuntimeRevalidation,
]


def _eligible_geometry(width: int, height: int) -> bool:
    return (
        width * height > MIN_OUTPUT_AREA_EXCLUSIVE
        and max(width, height) < MAX_OUTPUT_ASPECT_RATIO_EXCLUSIVE * min(width, height)
    )


def _store_png(output_root: Path, image_bytes: bytes) -> tuple[Path, str]:
    digest = hash_bytes(image_bytes)
    path = Path(output_root).resolve() / "sha256" / digest[:2] / f"{digest}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if hash_file(path) != digest:
            raise QualificationError("qualification output content-address collision")
    else:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(image_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(path.parent)
    return path, digest


def _response_error(body: bytes) -> tuple[str, str]:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "http_error", "HTTP response was not a JSON error object"
    error = value.get("error", value) if isinstance(value, dict) else value
    if isinstance(error, dict):
        code = str(error.get("code") or error.get("type") or "http_error")
        reason = str(error.get("message") or code)
    else:
        code, reason = "http_error", str(error)
    return sanitize_external_text(code, 200), sanitize_external_text(reason, 1000)


def _is_policy_refusal(code: str, reason: str) -> bool:
    combined = f"{code} {reason}".lower()
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


def _attempt_payload_from_exchange(
    exchange: TransportExchange,
    *,
    intent: QualificationIntent,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    output_root: Path,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "record_type": "pilot3_transport_qualification_attempt",
        "schema_version": "pilot3-transport-qualification-attempt-v1",
        "request_id": TRANSPORT_QUALIFICATION_REQUEST_ID,
        "intent_sha256": intent.intent_sha256,
        "physical_post_count": 1,
        "retry_count": 0,
        "retry_allowed": False,
        "requested_model_label": "gpt-image-2",
        "endpoint_url": EXPECTED_ENDPOINT_URL,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "started_at": exchange.started_at,
        "completed_at": exchange.completed_at,
        "http_status": exchange.http_status,
        "response_body_sha256": exchange.response_body_sha256,
        "response_body_byte_count": exchange.response_body_bytes,
        "response_metadata": exchange.response_metadata,
        "transport_error_kind": exchange.transport_error_kind,
        "transport_error_reason": exchange.transport_error_reason,
        "request_label_accepted": False,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
    }
    if exchange.transport_error_kind is not None:
        payload.update(
            {
                "outcome": "transport_failure",
                "failure_kind": sanitize_external_text(
                    exchange.transport_error_kind, 200
                ),
                "failure_reason": sanitize_external_text(
                    exchange.transport_error_reason or exchange.transport_error_kind,
                    1000,
                ),
            }
        )
        return payload
    assert exchange.http_status is not None
    if not 200 <= exchange.http_status <= 299:
        code, reason = _response_error(exchange.response_body)
        payload.update(
            {
                "outcome": (
                    "policy_refusal" if _is_policy_refusal(code, reason) else "http_failure"
                ),
                "failure_kind": code,
                "failure_reason": reason,
            }
        )
        return payload

    payload["request_label_accepted"] = True
    try:
        response = json.loads(exchange.response_body.decode("utf-8"))
        if not isinstance(response, dict):
            raise TypeError("response is not an object")
        data = response.get("data")
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise TypeError("data must contain exactly one item")
        encoded = data[0].get("b64_json")
        if not isinstance(encoded, str):
            raise TypeError("b64_json is not a string")
        image_bytes = base64.b64decode(encoded, validate=True)
        if not image_bytes:
            raise ValueError("decoded output is empty")
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        binascii.Error,
    ) as exc:
        payload.update(
            {
                "outcome": "invalid_response",
                "failure_kind": "invalid_response",
                "failure_reason": sanitize_external_text(
                    f"{type(exc).__name__}: {exc}", 1000
                ),
            }
        )
        return payload

    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            width, height = image.size
            image_format = (image.format or "unknown").lower()
    except Exception as exc:
        payload.update(
            {
                "outcome": "invalid_image",
                "failure_kind": "invalid_image",
                "failure_reason": sanitize_external_text(
                    f"{type(exc).__name__}: {exc}", 1000
                ),
            }
        )
        return payload
    if image_format != "png":
        payload.update(
            {
                "outcome": "invalid_image",
                "failure_kind": "unexpected_output_format",
                "failure_reason": f"requested PNG but decoded {image_format}",
                "actual_width": width,
                "actual_height": height,
                "actual_format": image_format,
                "strict_kim_geometry_eligible": _eligible_geometry(width, height),
            }
        )
        return payload
    if not _eligible_geometry(width, height):
        payload.update(
            {
                "outcome": "ineligible_geometry",
                "failure_kind": "ineligible_kim_geometry",
                "failure_reason": "decoded PNG is outside the strict Kim geometry domain",
                "actual_width": width,
                "actual_height": height,
                "actual_format": image_format,
                "strict_kim_geometry_eligible": False,
            }
        )
        return payload
    try:
        output_path, output_sha256 = _store_png(output_root, image_bytes)
    except (OSError, QualificationError) as exc:
        payload.update(
            {
                "outcome": "output_storage_failure",
                "failure_kind": "output_storage_failure",
                "failure_reason": sanitize_external_text(
                    f"{type(exc).__name__}: {exc}", 1000
                ),
                "actual_width": width,
                "actual_height": height,
                "actual_format": image_format,
                "strict_kim_geometry_eligible": True,
            }
        )
        return payload
    payload.update(
        {
            "outcome": "passed",
            "output_path": str(output_path),
            "output_sha256": output_sha256,
            "output_byte_count": len(image_bytes),
            "actual_width": width,
            "actual_height": height,
            "actual_format": image_format,
            "strict_kim_geometry_eligible": True,
        }
    )
    return payload


def _build_gate_context(
    *,
    phase_a: Mapping[str, Any],
    phase_a_file_sha256: str,
    account_authorization_file_sha256: str,
    model_documentation_file_sha256: str,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
) -> QualificationGateContext:
    request = canonical_image_request_bytes(
        TRANSPORT_QUALIFICATION_PROMPT,
        "gpt-image-2",
        frozen_requested_labels=("gpt-image-2",),
    )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_transport_qualification_gate_context",
        "schema_version": "pilot3-transport-qualification-gate-context-v1",
        "phase_a_record_type": EXPECTED_PHASE_A_RECORD_TYPE,
        "phase_a_status": "pass",
        "phase_a_result_sha256": phase_a["result_sha256"],
        "phase_a_result_file_sha256": phase_a_file_sha256,
        "account_authorization_evidence_file_sha256": (
            account_authorization_file_sha256
        ),
        "model_documentation_evidence_file_sha256": model_documentation_file_sha256,
        "freeze_b_status_at_authorization": "not_frozen",
        "analytic_generation_gate_status": "closed",
        "freeze_b_generation_gate_path_absent": True,
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "request_id": TRANSPORT_QUALIFICATION_REQUEST_ID,
        "canonical_request_sha256": hash_bytes(request),
        "neutral_prompt_sha256": TRANSPORT_QUALIFICATION_PROMPT_SHA256,
        "existing_intent_count": 0,
        "existing_attempt_count": 0,
    }
    payload["context_sha256"] = stable_hash(payload)
    return QualificationGateContext.model_validate(payload)


def _require_gate(gate: Optional[QualificationGate], context: QualificationGateContext) -> None:
    if gate is None:
        raise QualificationWindowClosed("P3-T11 requires an explicit authorization callback")
    try:
        opened = gate(context)
    except BaseException as exc:
        raise QualificationWindowClosed("P3-T11 authorization callback failed closed") from exc
    if opened is not True:
        raise QualificationWindowClosed("P3-T11 authorization callback did not return True")


def _persist_report_once(path: Path, report: Mapping[str, Any]) -> None:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    rendered = (json.dumps(
        dict(report), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n").encode("utf-8")
    if resolved.exists():
        if resolved.read_bytes() != rendered:
            raise QualificationError("transport qualification artifact already differs")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=f".{resolved.name}.", dir=resolved.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, resolved)
        except FileExistsError:
            if resolved.read_bytes() != rendered:
                raise QualificationError("transport qualification artifact collision")
        finally:
            os.unlink(temporary)
        _fsync_directory(resolved.parent)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def build_transport_qualification_report(
    *,
    phase_a_result_path: Path,
    account_authorization_evidence_path: Path,
    model_documentation_evidence_path: Path,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    intent_ledger: QualificationIntentLedger,
    attempt_ledger: QualificationAttemptLedger,
    output_root: Path,
) -> Dict[str, Any]:
    """Recompute the canonical P3-T11 artifact without any external request."""

    validate_transport_qualification_config(config)
    validate_transport_qualification_fingerprint(fingerprint, config)
    phase_a, phase_a_file_sha256 = load_phase_a_pass(phase_a_result_path)
    authorization_path = Path(account_authorization_evidence_path)
    documentation_path = Path(model_documentation_evidence_path)
    if not authorization_path.is_file() or not documentation_path.is_file():
        raise QualificationError("P3-T11 authorization/documentation evidence is missing")
    intent = intent_ledger.row()
    if intent is None:
        raise QualificationError("P3-T11 has no durable pre-POST intent")
    expected_intent_bindings = {
        "phase_a_result_sha256": phase_a["result_sha256"],
        "phase_a_result_file_sha256": phase_a_file_sha256,
        "account_authorization_evidence_file_sha256": hash_file(authorization_path),
        "model_documentation_evidence_file_sha256": hash_file(documentation_path),
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
    }
    for field, expected in expected_intent_bindings.items():
        if getattr(intent, field) != expected:
            raise QualificationError(f"P3-T11 intent has stale binding: {field}")
    attempt = attempt_ledger.row()
    if attempt is not None and (
        attempt.intent_sha256 != intent.intent_sha256
        or attempt.oauth_runtime_fingerprint_sha256 != fingerprint.fingerprint_sha256
    ):
        raise QualificationError("P3-T11 attempt is not bound to its intent/runtime")

    output_verified = False
    if attempt is not None and attempt.outcome == "passed":
        assert attempt.output_path and attempt.output_sha256
        output_path = Path(attempt.output_path)
        if (
            not output_path.is_file()
            or hash_file(output_path) != attempt.output_sha256
            or output_path.name != f"{attempt.output_sha256}.png"
            or Path(output_root).resolve() not in output_path.resolve().parents
        ):
            raise QualificationError("P3-T11 output path/hash binding is stale")
        with Image.open(output_path) as image:
            image.load()
            width, height = image.size
            image_format = (image.format or "unknown").lower()
        output_verified = (
            image_format == "png"
            and width == attempt.actual_width
            and height == attempt.actual_height
            and _eligible_geometry(width, height)
            and output_path.stat().st_size == attempt.output_byte_count
        )
        if not output_verified:
            raise QualificationError("P3-T11 output no longer satisfies its evidence")

    status = "pass" if attempt is not None and attempt.outcome == "passed" else (
        "indeterminate" if attempt is None else "fail"
    )
    payload: Dict[str, Any] = {
        "record_type": "pilot3_transport_qualification",
        "schema_version": "pilot3-transport-qualification-v1",
        "resolves_task_id": "P3-T11",
        "status": status,
        "timing_contract": "after_p3_t08_pass_and_before_freeze_b",
        "phase_a_result_sha256": phase_a["result_sha256"],
        "phase_a_result_file_sha256": phase_a_file_sha256,
        "freeze_b_status_at_authorization": "not_frozen",
        "analytic_generation_gate_status_at_authorization": "closed",
        "request_id": TRANSPORT_QUALIFICATION_REQUEST_ID,
        "neutral_prompt": TRANSPORT_QUALIFICATION_PROMPT,
        "neutral_prompt_sha256": TRANSPORT_QUALIFICATION_PROMPT_SHA256,
        "outside_artist_content_grid": True,
        "analytic_grid_membership": False,
        "excluded_from_feature_fitting_and_outcome_selection": True,
        "physical_post_budget": 1,
        "physical_post_count": None if attempt is None else 1,
        "physical_post_or_indeterminate_count": 1,
        "retry_allowed": False,
        "retry_count": 0,
        "requested_model_label": "gpt-image-2",
        "transport": "~/dev/openai-oauth",
        "endpoint_url": EXPECTED_ENDPOINT_URL,
        "dedicated_port": 10533,
        "oauth_checkout_path": str(EXPECTED_CHECKOUT),
        "execution_namespace": TRANSPORT_QUALIFICATION_NAMESPACE,
        "shares_frozen_analytic_transport_config_and_runtime_fingerprint": True,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "account_authorization_evidence_file_sha256": hash_file(authorization_path),
        "model_documentation_evidence_file_sha256": hash_file(documentation_path),
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "oauth_source_snapshot_sha256": fingerprint.source.source_snapshot_sha256,
        "pre_request_runtime_revalidation_sha256": (
            intent.pre_request_runtime_revalidation.revalidation_sha256
        ),
        "post_request_runtime_revalidation_sha256": (
            None
            if attempt is None
            else attempt.post_request_runtime_revalidation.revalidation_sha256
        ),
        "canonical_request_sha256": intent.canonical_request_sha256,
        "canonical_request_utf8": intent.canonical_request_utf8,
        "canonical_request_byte_count": intent.canonical_request_byte_count,
        "intent_sha256": intent.intent_sha256,
        "intent_ledger_file_sha256": hash_file(intent_ledger.path),
        "attempt_sha256": None if attempt is None else attempt.attempt_sha256,
        "attempt_ledger_file_sha256": (
            None if attempt is None else hash_file(attempt_ledger.path)
        ),
        "outcome": (
            "indeterminate_after_pre_post_intent"
            if attempt is None
            else attempt.outcome
        ),
        "request_label_accepted_by_endpoint": (
            False if attempt is None else attempt.request_label_accepted
        ),
        "output_hash_png_and_geometry_verified": output_verified,
        "output_evidence": (
            None
            if attempt is None
            else {
                "http_status": attempt.http_status,
                "response_body_sha256": attempt.response_body_sha256,
                "response_body_byte_count": attempt.response_body_byte_count,
                "response_metadata": attempt.response_metadata,
                "output_path": attempt.output_path,
                "output_sha256": attempt.output_sha256,
                "output_byte_count": attempt.output_byte_count,
                "actual_width": attempt.actual_width,
                "actual_height": attempt.actual_height,
                "actual_format": attempt.actual_format,
                "strict_kim_geometry_eligible": attempt.strict_kim_geometry_eligible,
                "failure_kind": attempt.failure_kind,
                "failure_reason": attempt.failure_reason,
            }
        ),
        "p3_t11_passes": status == "pass",
        "authorizes_analytic_generation_by_itself": False,
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def verify_transport_qualification_report(
    report: Mapping[str, Any],
    **kwargs: Any,
) -> Dict[str, Any]:
    expected = build_transport_qualification_report(**kwargs)
    if dict(report) != expected:
        raise QualificationError("P3-T11 transport qualification report is stale or tampered")
    return expected


def finalize_transport_qualification_artifact(
    artifact_path: Path = TRANSPORT_QUALIFICATION_ARTIFACT_PATH,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Write or recover the report without resending an unmatched request."""

    report = build_transport_qualification_report(**kwargs)
    _persist_report_once(artifact_path, report)
    return report


def run_neutral_transport_qualification(
    *,
    phase_a_result_path: Path,
    account_authorization_evidence_path: Path,
    model_documentation_evidence_path: Path,
    freeze_b_generation_gate_path: Path,
    transport: OnePostTransport,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    intent_ledger: QualificationIntentLedger,
    attempt_ledger: QualificationAttemptLedger,
    output_root: Path,
    artifact_path: Path,
    authorization_gate: Optional[QualificationGate],
    runtime_revalidator: RuntimeRevalidator = revalidate_pilot3_oauth_runtime_fingerprint,
) -> Dict[str, Any]:
    """Issue the sole P3-T11 image POST after all fail-closed checks pass."""

    config = transport.config
    validate_transport_qualification_config(config)
    validate_transport_qualification_fingerprint(fingerprint, config)
    phase_a, phase_a_file_sha256 = load_phase_a_pass(phase_a_result_path)
    authorization_path = Path(account_authorization_evidence_path)
    documentation_path = Path(model_documentation_evidence_path)
    if not authorization_path.is_file() or not documentation_path.is_file():
        raise QualificationWindowClosed(
            "P3-T11 requires account-authorization and model-documentation evidence"
        )
    if Path(freeze_b_generation_gate_path).exists():
        raise QualificationWindowClosed(
            "P3-T11 must run before the Freeze-B generation-gate artifact exists"
        )
    if intent_ledger.row() is not None or attempt_ledger.row() is not None:
        raise QualificationWindowClosed(
            "P3-T11 one-shot request was already consumed; blind resend is prohibited"
        )
    context = _build_gate_context(
        phase_a=phase_a,
        phase_a_file_sha256=phase_a_file_sha256,
        account_authorization_file_sha256=hash_file(authorization_path),
        model_documentation_file_sha256=hash_file(documentation_path),
        config=config,
        fingerprint=fingerprint,
    )
    # No live probe, ledger write, or POST occurs before literal authorization.
    _require_gate(authorization_gate, context)

    pre_runtime = runtime_revalidator(config, fingerprint)
    request = canonical_image_request_bytes(
        TRANSPORT_QUALIFICATION_PROMPT,
        "gpt-image-2",
        frozen_requested_labels=("gpt-image-2",),
    )
    intent_payload: Dict[str, Any] = {
        "record_type": "pilot3_transport_qualification_post_intent",
        "schema_version": "pilot3-transport-qualification-post-intent-v1",
        "request_id": TRANSPORT_QUALIFICATION_REQUEST_ID,
        "physical_post_number": 1,
        "retry_allowed": False,
        "analytic_grid_membership": False,
        "phase_a_result_sha256": phase_a["result_sha256"],
        "phase_a_result_file_sha256": phase_a_file_sha256,
        "account_authorization_evidence_file_sha256": hash_file(authorization_path),
        "model_documentation_evidence_file_sha256": hash_file(documentation_path),
        "freeze_b_status_at_authorization": "not_frozen",
        "analytic_generation_gate_status": "closed",
        "transport_config_sha256": config.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "pre_request_runtime_revalidation": pre_runtime.model_dump(mode="json"),
        "requested_model_label": "gpt-image-2",
        "endpoint_url": EXPECTED_ENDPOINT_URL,
        "canonical_request_utf8": request.decode("utf-8"),
        "canonical_request_sha256": hash_bytes(request),
        "canonical_request_byte_count": len(request),
        "neutral_prompt_sha256": TRANSPORT_QUALIFICATION_PROMPT_SHA256,
        "created_at": _utc_json_now(),
        "physical_post_may_have_executed": True,
    }
    intent_payload["intent_sha256"] = stable_hash(intent_payload)
    intent = QualificationIntent.model_validate(intent_payload)
    intent_ledger.append_once(intent)

    # The only image POST site in P3-T11. There is intentionally no retry loop.
    exchange = transport.post_once(request)
    attempt_payload = _attempt_payload_from_exchange(
        exchange,
        intent=intent,
        fingerprint=fingerprint,
        output_root=output_root,
    )
    post_runtime = runtime_revalidator(config, fingerprint)
    attempt_payload["post_request_runtime_revalidation"] = post_runtime
    normalized_attempt = QualificationAttempt.model_construct(
        **attempt_payload, attempt_sha256="0" * 64
    ).model_dump(mode="json", exclude={"attempt_sha256"})
    attempt_payload["attempt_sha256"] = stable_hash(normalized_attempt)
    attempt = QualificationAttempt.model_validate(attempt_payload)
    attempt_ledger.append_once(attempt)
    return finalize_transport_qualification_artifact(
        artifact_path,
        phase_a_result_path=phase_a_result_path,
        account_authorization_evidence_path=account_authorization_evidence_path,
        model_documentation_evidence_path=model_documentation_evidence_path,
        config=config,
        fingerprint=fingerprint,
        intent_ledger=intent_ledger,
        attempt_ledger=attempt_ledger,
        output_root=output_root,
    )


__all__ = [
    "ACCOUNT_AUTHORIZATION_RECORD_ID",
    "ACCOUNT_AUTHORIZATION_SCHEMA",
    "AccountAuthorizationEvidence",
    "GPT_IMAGE_2_DOCUMENTATION_URL",
    "MODEL_DOCUMENTATION_SCHEMA",
    "ModelDocumentationEvidence",
    "QualificationAttempt",
    "QualificationAttemptLedger",
    "QualificationError",
    "QualificationGate",
    "QualificationGateContext",
    "QualificationIntent",
    "QualificationIntentLedger",
    "QualificationWindowClosed",
    "TRANSPORT_QUALIFICATION_ARTIFACT_PATH",
    "TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH",
    "TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH",
    "TRANSPORT_QUALIFICATION_NAMESPACE",
    "TRANSPORT_QUALIFICATION_OUTPUT_ROOT",
    "TRANSPORT_QUALIFICATION_PROMPT",
    "TRANSPORT_QUALIFICATION_PROMPT_SHA256",
    "TRANSPORT_QUALIFICATION_REQUEST_ID",
    "build_transport_qualification_report",
    "build_account_authorization_evidence",
    "build_model_documentation_evidence",
    "finalize_transport_qualification_artifact",
    "load_phase_a_pass",
    "run_neutral_transport_qualification",
    "validate_transport_qualification_config",
    "validate_transport_qualification_fingerprint",
    "verify_transport_qualification_report",
    "verify_account_authorization_evidence",
    "verify_model_documentation_evidence",
]
