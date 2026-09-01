"""Fail-closed OAuth transport and runtime provenance for Pilot 3.

The transport intentionally measures acceptance of an exact requested model label.
Neither the local model catalog nor a successful response attests the model or
snapshot that executed upstream.
"""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import hash_bytes, stable_hash
from latent_art_bench.pilot2.transport import (
    capture_oauth_source_snapshot as _capture_audited_oauth_source_snapshot,
)
from latent_art_bench.pilot2.transport import inspect_oauth_process as _inspect_oauth_process

RequestedImageModel = Literal["gpt-image-1", "gpt-image-2"]

ALLOWED_REQUESTED_MODELS: Tuple[RequestedImageModel, ...] = (
    "gpt-image-1",
    "gpt-image-2",
)
EXECUTED_MODEL_CLAIMS: Literal[False] = False
SNAPSHOT_IDENTITY_CLAIMS: Literal[False] = False
OPERATIONAL_MODEL_ESTIMAND = "requested_model_label_accepted_by_oauth_endpoint"
REQUEST_SIZE: Literal["auto"] = "auto"
REQUEST_QUALITY: Literal["low"] = "low"
REQUEST_OUTPUT_FORMAT: Literal["png"] = "png"
EXPECTED_ENDPOINT_PATH = "/v1/images/generations"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT = Path(
    "packages/openai-oauth/src/cli.ts"
)
EXPECTED_PILOT3_OAUTH_FILE = (Path.home() / ".codex" / "auth.json").resolve()
_SAFE_RESPONSE_HEADERS = frozenset(
    {
        "content-type",
        "openai-processing-ms",
        "request-id",
        "retry-after",
        "x-request-id",
    }
)


class Pilot3TransportError(RuntimeError):
    """Base class for Pilot-3 transport and provenance failures."""


class TransportConfigurationError(Pilot3TransportError, ValueError):
    """Raised before a request when transport scope is invalid."""


class RuntimeFingerprintError(Pilot3TransportError):
    """Raised when runtime provenance is ambiguous or stale."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_utc_now() -> str:
    """Return the same UTC representation produced by Pydantic JSON mode.

    Self-hashes bind the JSON-ready artifact, so hashing a Python ``datetime``
    (whose fallback string contains a space) would disagree after validation
    normalizes it to RFC 3339.
    """

    return _utc_now().isoformat().replace("+00:00", "Z")


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise TransportConfigurationError(
            f"request is not canonical JSON data: {exc}"
        ) from exc
    return rendered.encode("utf-8")


def validate_frozen_requested_labels(
    labels: Sequence[str],
) -> Tuple[RequestedImageModel, ...]:
    """Return the canonical non-empty subset of the two permitted aliases."""

    values = tuple(labels)
    if not values:
        raise TransportConfigurationError("at least one requested model label is required")
    if len(values) != len(set(values)):
        raise TransportConfigurationError("requested model labels must not repeat")
    if any(value not in ALLOWED_REQUESTED_MODELS for value in values):
        raise TransportConfigurationError(
            f"requested labels must be a subset of {list(ALLOWED_REQUESTED_MODELS)!r}"
        )
    canonical = tuple(value for value in ALLOWED_REQUESTED_MODELS if value in values)
    if values != canonical:
        raise TransportConfigurationError(
            "requested labels must use canonical order: " + ", ".join(canonical)
        )
    return values  # type: ignore[return-value]


def canonical_image_request_bytes(
    prompt: str,
    requested_model: RequestedImageModel,
    *,
    frozen_requested_labels: Optional[Sequence[str]] = None,
) -> bytes:
    """Return the exact UTF-8 bytes permitted on the Pilot-3 image route."""

    if requested_model not in ALLOWED_REQUESTED_MODELS:
        raise TransportConfigurationError(
            f"requested model must be one of {list(ALLOWED_REQUESTED_MODELS)!r}"
        )
    if frozen_requested_labels is not None:
        labels = validate_frozen_requested_labels(frozen_requested_labels)
        if requested_model not in labels:
            raise TransportConfigurationError(
                f"requested model {requested_model!r} is outside the frozen label subset"
            )
    if not isinstance(prompt, str) or not prompt.strip():
        raise TransportConfigurationError("image prompt must not be blank")
    return _canonical_json_bytes(
        {
            "model": requested_model,
            "n": 1,
            "output_format": REQUEST_OUTPUT_FORMAT,
            "prompt": prompt,
            "quality": REQUEST_QUALITY,
            "size": REQUEST_SIZE,
        }
    )


class Pilot3TransportConfig(_StrictModel):
    """Frozen scope guard for one dedicated local Pilot-3 proxy endpoint."""

    base_url: str = "http://127.0.0.1:10533/v1"
    dedicated_port: int = Field(default=10533, ge=1, le=65535)
    checkout_path: Path = Field(
        default_factory=lambda: Path.home() / "dev" / "openai-oauth"
    )
    required_checkout_path: Path = Field(
        default_factory=lambda: Path.home() / "dev" / "openai-oauth"
    )
    frozen_requested_labels: Tuple[RequestedImageModel, ...] = ("gpt-image-2",)
    timeout_seconds: float = Field(default=300.0, gt=0)
    execution_namespace: str = "pilot3-generation-v1"

    @model_validator(mode="after")
    def exact_local_transport(self) -> "Pilot3TransportConfig":
        parsed = urlsplit(self.base_url)
        if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
            raise ValueError("Pilot-3 generation requires an HTTP loopback OAuth URL")
        if parsed.port is None or parsed.port != self.dedicated_port:
            raise ValueError("base_url must use the explicitly frozen dedicated_port")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("OAuth base URL cannot contain credentials, a query, or a fragment")
        if parsed.path.rstrip("/") != "/v1":
            raise ValueError("OAuth base URL must end at the exact /v1 API root")
        labels = validate_frozen_requested_labels(self.frozen_requested_labels)
        checkout = self.checkout_path.expanduser().resolve()
        required = self.required_checkout_path.expanduser().resolve()
        if checkout != required:
            raise ValueError(
                f"OAuth checkout must be the pinned checkout {required}, found {checkout}"
            )
        if not self.execution_namespace.strip():
            raise ValueError("execution_namespace must not be blank")
        object.__setattr__(self, "checkout_path", checkout)
        object.__setattr__(self, "required_checkout_path", required)
        object.__setattr__(self, "frozen_requested_labels", labels)
        return self

    @property
    def endpoint_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/images/generations"

    @property
    def health_url(self) -> str:
        parsed = urlsplit(self.base_url)
        return urlunsplit((parsed.scheme, parsed.netloc, "/health", "", ""))

    @property
    def models_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/models"

    @property
    def config_sha256(self) -> str:
        return stable_hash(self.model_dump(mode="json"))


class SourceFileEvidence(_StrictModel):
    path: str
    state: Literal["present", "deleted"]
    tracked_at_head: bool
    current_sha256: Optional[str] = None
    current_size_bytes: Optional[int] = Field(default=None, ge=0)


class Pilot3OAuthSourceSnapshot(_StrictModel):
    schema_version: Literal["pilot3-oauth-source-snapshot-v1"] = (
        "pilot3-oauth-source-snapshot-v1"
    )
    checkout_path: str
    git_head: str
    git_remote: str
    dirty: bool
    relevant_roots: List[str]
    files: List[SourceFileEvidence]
    git_status_porcelain: str
    tracked_diff: str
    tracked_diff_sha256: str
    untracked_source_contents: Dict[str, str]
    excluded_dirty_paths: List[str]
    runtime_source_dirty_paths: List[str]
    dirty_runtime_source_capture_complete: bool
    source_snapshot_sha256: str

    @field_validator("tracked_diff_sha256", "source_snapshot_sha256")
    @classmethod
    def lowercase_sha256(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("source fingerprint hashes must be lowercase SHA-256")
        return value

    @field_validator("git_head")
    @classmethod
    def full_sha1(cls, value: str) -> str:
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("git_head must be a full lowercase SHA-1 commit id")
        return value


class OAuthProcessEvidence(_StrictModel):
    pid: int = Field(gt=0)
    cwd: str
    cwd_inside_checkout: bool
    command_sanitized: str
    command_sha256: str
    executable_path: Optional[str] = None
    executable_sha256: Optional[str] = None
    runtime_version: Optional[str] = None
    launcher_contract_version: Optional[
        Literal["pilot3-openai-oauth-launcher-v1"]
    ] = None
    launcher_entrypoint_path: Optional[str] = None
    launcher_host: Optional[str] = None
    launcher_port: Optional[int] = Field(default=None, ge=1, le=65535)
    launcher_models: Optional[List[str]] = None
    oauth_file_path_sha256: Optional[str] = None
    launcher_contract_valid: Optional[bool] = None

    @field_validator("oauth_file_path_sha256")
    @classmethod
    def oauth_file_hash_is_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("OAuth-file path hash must be lowercase SHA-256")
        return value


class EndpointProbeEvidence(_StrictModel):
    url: str
    http_status: int = Field(ge=100, le=599)
    response_body_sha256: str
    response_body_bytes: int = Field(ge=0)
    response_metadata: Dict[str, str]
    parsed_summary: Dict[str, Any]


class Pilot3OAuthRuntimeFingerprint(_StrictModel):
    schema_version: Literal["pilot3-oauth-runtime-fingerprint-v1"] = (
        "pilot3-oauth-runtime-fingerprint-v1"
    )
    captured_at: datetime
    transport_config_sha256: str
    endpoint_url: str
    frozen_requested_labels: List[RequestedImageModel]
    executed_model_claims: Literal[False] = False
    snapshot_identity_claims: Literal[False] = False
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    source: Pilot3OAuthSourceSnapshot
    process: OAuthProcessEvidence
    health: EndpointProbeEvidence
    model_catalog: EndpointProbeEvidence
    health_ok: bool
    model_catalog_contains_frozen_labels: bool
    model_catalog_is_execution_attestation: Literal[False] = False
    runtime_ready: bool
    fingerprint_sha256: str

    @field_validator("transport_config_sha256", "fingerprint_sha256")
    @classmethod
    def fingerprint_hashes(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("runtime fingerprint hashes must be lowercase SHA-256")
        return value


class Pilot3OAuthRuntimeRevalidation(_StrictModel):
    schema_version: Literal["pilot3-oauth-runtime-revalidation-v1"] = (
        "pilot3-oauth-runtime-revalidation-v1"
    )
    checked_at: datetime
    status: Literal["pass"] = "pass"
    persisted_fingerprint_sha256: str
    transport_config_sha256: str
    endpoint_url: str
    frozen_requested_labels: List[RequestedImageModel]
    current_listener_pid: int = Field(gt=0)
    current_process_cwd: str
    current_source_snapshot_sha256: str
    current_health_response_sha256: str
    current_model_catalog_response_sha256: str
    checks: Dict[str, bool]
    revalidation_sha256: str

    @model_validator(mode="after")
    def content_hash_is_current(self) -> "Pilot3OAuthRuntimeRevalidation":
        if not self.checks or not all(self.checks.values()):
            raise ValueError("successful runtime revalidation contains a failed check")
        payload = self.model_dump(mode="json", exclude={"revalidation_sha256"})
        if stable_hash(payload) != self.revalidation_sha256:
            raise ValueError("OAuth runtime revalidation hash is stale")
        return self

    @field_validator(
        "persisted_fingerprint_sha256",
        "transport_config_sha256",
        "current_source_snapshot_sha256",
        "current_health_response_sha256",
        "current_model_catalog_response_sha256",
        "revalidation_sha256",
    )
    @classmethod
    def revalidation_hashes(cls, value: str) -> str:
        if not _is_sha256(value):
            raise ValueError("runtime revalidation hashes must be lowercase SHA-256")
        return value


class TransportExchange(_StrictModel):
    """In-memory result of exactly one physical POST."""

    started_at: datetime
    completed_at: datetime
    http_status: Optional[int] = Field(default=None, ge=100, le=599)
    response_body: bytes = Field(default=b"", exclude=True)
    response_body_sha256: Optional[str] = None
    response_body_bytes: int = Field(default=0, ge=0)
    response_metadata: Dict[str, str] = Field(default_factory=dict)
    transport_error_kind: Optional[str] = None
    transport_error_reason: Optional[str] = None
    transport_error_retryable: Optional[bool] = None

    @model_validator(mode="after")
    def exchange_is_consistent(self) -> "TransportExchange":
        if self.completed_at < self.started_at:
            raise ValueError("transport exchange completed before it started")
        has_http = self.http_status is not None
        has_error = self.transport_error_kind is not None
        if has_http == has_error:
            raise ValueError("transport exchange must contain exactly one result class")
        if has_http:
            if (
                self.transport_error_reason is not None
                or self.transport_error_retryable is not None
            ):
                raise ValueError("HTTP exchanges cannot also carry transport-error fields")
            if self.response_body_bytes != len(self.response_body):
                raise ValueError("transport response byte count is stale")
            if self.response_body_sha256 != hash_bytes(self.response_body):
                raise ValueError("transport response hash is stale")
        elif (
            not self.transport_error_kind
            or not self.transport_error_reason
            or self.transport_error_retryable is None
            or self.response_body
            or self.response_body_sha256 is not None
            or self.response_body_bytes != 0
            or self.response_metadata
        ):
            raise ValueError("transport-error exchange contains inconsistent HTTP evidence")
        return self

    @field_validator("response_body_sha256")
    @classmethod
    def response_hash_is_sha256(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _is_sha256(value):
            raise ValueError("transport response hash must be lowercase SHA-256")
        return value


def sanitize_external_text(value: object, limit: int = 1000) -> str:
    """Reuse the audited Pilot-2 redactor without reusing its evidence schemas."""

    from latent_art_bench.pilot2.transport import sanitize_external_text as audited

    return audited(value, limit)


def capture_pilot3_oauth_source_snapshot(checkout_path: Path) -> Pilot3OAuthSourceSnapshot:
    """Adapt the audited full checkout capture into a Pilot-3 evidence schema."""

    audited = _capture_audited_oauth_source_snapshot(checkout_path)
    payload = audited.model_dump(mode="json", exclude={"schema_version", "source_snapshot_sha256"})
    payload["schema_version"] = "pilot3-oauth-source-snapshot-v1"
    payload["source_snapshot_sha256"] = stable_hash(payload)
    return Pilot3OAuthSourceSnapshot.model_validate(payload)


def verify_pilot3_oauth_source_snapshot(snapshot: Pilot3OAuthSourceSnapshot) -> None:
    payload = snapshot.model_dump(mode="json", exclude={"source_snapshot_sha256"})
    if stable_hash(payload) != snapshot.source_snapshot_sha256:
        raise RuntimeFingerprintError("OAuth source snapshot hash does not match its content")
    if not snapshot.dirty_runtime_source_capture_complete:
        raise RuntimeFingerprintError("OAuth dirty runtime source capture is incomplete")
    evidence_paths = {item.path for item in snapshot.files}
    if not set(snapshot.runtime_source_dirty_paths).issubset(evidence_paths):
        raise RuntimeFingerprintError("OAuth source snapshot omits dirty runtime paths")
    untracked_paths = set(snapshot.untracked_source_contents)
    for item in snapshot.files:
        if (
            not item.tracked_at_head
            and item.state == "present"
            and item.path not in untracked_paths
        ):
            raise RuntimeFingerprintError(
                f"OAuth source snapshot omits untracked content: {item.path}"
            )


def _safe_response_metadata(headers: httpx.Headers) -> Dict[str, str]:
    return {
        name.lower(): sanitize_external_text(value, limit=500)
        for name, value in headers.multi_items()
        if name.lower() in _SAFE_RESPONSE_HEADERS
    }


def _endpoint_probe(
    response: httpx.Response, url: str, summary: Dict[str, Any]
) -> EndpointProbeEvidence:
    body = response.content
    return EndpointProbeEvidence(
        url=url,
        http_status=response.status_code,
        response_body_sha256=hash_bytes(body),
        response_body_bytes=len(body),
        response_metadata=_safe_response_metadata(response.headers),
        parsed_summary=summary,
    )


def _parse_health(response: httpx.Response) -> Tuple[EndpointProbeEvidence, bool]:
    try:
        parsed: Any = response.json()
    except ValueError:
        parsed = None
    summary = {
        "ok": parsed.get("ok") if isinstance(parsed, dict) else None,
        "replay_state": (
            sanitize_external_text(parsed.get("replay_state"), limit=100)
            if isinstance(parsed, dict) and parsed.get("replay_state") is not None
            else None
        ),
    }
    return _endpoint_probe(response, str(response.request.url), summary), (
        response.status_code == 200 and summary["ok"] is True
    )


def _parse_model_catalog(
    response: httpx.Response,
) -> Tuple[EndpointProbeEvidence, List[str]]:
    try:
        parsed: Any = response.json()
    except ValueError:
        parsed = None
    models: List[str] = []
    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        for item in parsed["data"]:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                models.append(sanitize_external_text(item["id"], limit=200))
    models = sorted(set(models))
    summary = {
        "object": parsed.get("object") if isinstance(parsed, dict) else None,
        "model_ids": models,
        "execution_attestation": False,
    }
    return _endpoint_probe(response, str(response.request.url), summary), models


ProcessInspector = Callable[[str, int, Path], Any]


def _parse_launcher_options(arguments: Sequence[str]) -> Optional[Dict[str, str]]:
    """Parse the four exact value-taking options of the dedicated listener."""

    expected = {"--host", "--port", "--models", "--oauth-file"}
    parsed: Dict[str, str] = {}
    index = 0
    while index < len(arguments):
        item = arguments[index]
        if "=" in item:
            name, value = item.split("=", 1)
            index += 1
        else:
            name = item
            if index + 1 >= len(arguments):
                return None
            value = arguments[index + 1]
            index += 2
        if name not in expected or name in parsed or not value:
            return None
        parsed[name] = value
    return parsed if set(parsed) == expected else None


def _inspect_pilot3_oauth_process(
    host: str, port: int, checkout: Path
) -> Mapping[str, Any]:
    """Capture the audited process evidence plus a secret-free exact argv contract."""

    audited = _inspect_oauth_process(host, port, checkout)
    payload = audited.model_dump(mode="json")
    process = subprocess.run(
        ["ps", "-p", str(audited.pid), "-ww", "-o", "command="],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    command = process.stdout.strip()
    if process.returncode != 0 or not command:
        raise RuntimeFingerprintError(
            f"could not recover exact launcher argv for OAuth process {audited.pid}"
        )
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise RuntimeFingerprintError("OAuth launcher command is not valid shell argv") from exc
    cwd = Path(audited.cwd).resolve()
    checkout = Path(checkout).resolve()
    expected_entrypoint = (checkout / EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT).resolve()
    options = _parse_launcher_options(argv[2:]) if len(argv) >= 2 else None
    entrypoint = (cwd / argv[1]).resolve() if len(argv) >= 2 else None
    oauth_path = (
        Path(options["--oauth-file"]).expanduser().resolve()
        if options is not None
        else None
    )
    valid = bool(
        argv
        and Path(argv[0]).name == "bun"
        and entrypoint == expected_entrypoint
        and options is not None
        and options["--host"] == "127.0.0.1"
        and options["--port"] == "10533"
        and options["--models"] == "gpt-image-2"
        and oauth_path == EXPECTED_PILOT3_OAUTH_FILE
    )
    payload.update(
        {
            "launcher_contract_version": "pilot3-openai-oauth-launcher-v1",
            "launcher_entrypoint_path": (
                None if entrypoint is None else str(entrypoint)
            ),
            "launcher_host": None if options is None else options["--host"],
            "launcher_port": (
                None
                if options is None or not options["--port"].isdigit()
                else int(options["--port"])
            ),
            "launcher_models": (
                None
                if options is None
                else [
                    value
                    for value in options["--models"].split(",")
                    if value
                ]
            ),
            "oauth_file_path_sha256": (
                None
                if oauth_path is None
                else hashlib.sha256(str(oauth_path).encode("utf-8")).hexdigest()
            ),
            "launcher_contract_valid": valid,
        }
    )
    return payload


def capture_pilot3_oauth_runtime_fingerprint(
    config: Pilot3TransportConfig,
    *,
    client: Optional[httpx.Client] = None,
    process_inspector: ProcessInspector = _inspect_pilot3_oauth_process,
) -> Pilot3OAuthRuntimeFingerprint:
    """Capture process/source/health/catalog evidence without claiming execution identity."""

    source = capture_pilot3_oauth_source_snapshot(config.checkout_path)
    parsed = urlsplit(config.base_url)
    assert parsed.hostname is not None and parsed.port is not None
    observed_process = process_inspector(parsed.hostname, parsed.port, config.checkout_path)
    process = OAuthProcessEvidence.model_validate(
        observed_process.model_dump(mode="json")
        if hasattr(observed_process, "model_dump")
        else observed_process
    )
    owns_client = client is None
    probe_client = client or httpx.Client(
        timeout=min(config.timeout_seconds, 30.0),
        follow_redirects=False,
        trust_env=False,
    )
    try:
        health_response = probe_client.get(
            config.health_url, headers={"accept": "application/json"}
        )
        model_response = probe_client.get(
            config.models_url, headers={"accept": "application/json"}
        )
    except httpx.HTTPError as exc:
        raise RuntimeFingerprintError(
            f"OAuth runtime probe failed: {sanitize_external_text(exc)}"
        ) from exc
    finally:
        if owns_client:
            probe_client.close()
    health, health_ok = _parse_health(health_response)
    catalog, catalog_models = _parse_model_catalog(model_response)
    contains_labels = set(config.frozen_requested_labels).issubset(catalog_models)
    ready = bool(
        health_ok
        and contains_labels
        and process.cwd_inside_checkout
        and source.dirty_runtime_source_capture_complete
    )
    payload: Dict[str, Any] = {
        "schema_version": "pilot3-oauth-runtime-fingerprint-v1",
        "captured_at": _json_utc_now(),
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "source": source.model_dump(mode="json"),
        "process": process.model_dump(mode="json"),
        "health": health.model_dump(mode="json"),
        "model_catalog": catalog.model_dump(mode="json"),
        "health_ok": health_ok,
        "model_catalog_contains_frozen_labels": contains_labels,
        "model_catalog_is_execution_attestation": False,
        "runtime_ready": ready,
    }
    payload["fingerprint_sha256"] = stable_hash(payload)
    fingerprint = Pilot3OAuthRuntimeFingerprint.model_validate(payload)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    return fingerprint


def verify_pilot3_oauth_runtime_fingerprint(
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    *,
    config: Optional[Pilot3TransportConfig] = None,
) -> None:
    verify_pilot3_oauth_source_snapshot(fingerprint.source)
    payload = fingerprint.model_dump(mode="json", exclude={"fingerprint_sha256"})
    if stable_hash(payload) != fingerprint.fingerprint_sha256:
        raise RuntimeFingerprintError("OAuth runtime fingerprint hash does not match its content")
    expected_ready = bool(
        fingerprint.health_ok
        and fingerprint.model_catalog_contains_frozen_labels
        and fingerprint.process.cwd_inside_checkout
        and fingerprint.source.dirty_runtime_source_capture_complete
    )
    if fingerprint.runtime_ready != expected_ready:
        raise RuntimeFingerprintError("OAuth runtime-ready decision is stale")
    labels = validate_frozen_requested_labels(fingerprint.frozen_requested_labels)
    if list(labels) != fingerprint.frozen_requested_labels:
        raise RuntimeFingerprintError("runtime fingerprint label subset is not canonical")
    if config is not None:
        if fingerprint.transport_config_sha256 != config.config_sha256:
            raise RuntimeFingerprintError("runtime fingerprint binds a different transport config")
        if fingerprint.endpoint_url != config.endpoint_url:
            raise RuntimeFingerprintError("runtime fingerprint endpoint is stale")
        if fingerprint.frozen_requested_labels != list(config.frozen_requested_labels):
            raise RuntimeFingerprintError("runtime fingerprint label subset is stale")


def verify_pilot3_production_runtime_fingerprint(
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    *,
    config: Pilot3TransportConfig,
) -> None:
    """Require the exact dedicated Pilot-3 listener launch contract.

    The persisted process evidence proves how the local proxy was launched; it
    does not attest which upstream model snapshot executed a request.  The
    ``--models`` value controls catalog exposure, not endpoint allowlisting;
    Pilot 3's canonical client validation is what restricts study requests.
    """

    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    process = fingerprint.process
    expected_entrypoint = (
        config.checkout_path / EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT
    ).resolve()
    expected_oauth_hash = hashlib.sha256(
        str(EXPECTED_PILOT3_OAUTH_FILE).encode("utf-8")
    ).hexdigest()
    catalog = fingerprint.model_catalog.parsed_summary.get("model_ids")
    if (
        not fingerprint.runtime_ready
        or fingerprint.endpoint_url
        != "http://127.0.0.1:10533/v1/images/generations"
        or fingerprint.frozen_requested_labels != ["gpt-image-2"]
        or catalog != ["gpt-image-2"]
        or process.launcher_contract_version
        != "pilot3-openai-oauth-launcher-v1"
        or process.launcher_contract_valid is not True
        or process.launcher_entrypoint_path != str(expected_entrypoint)
        or process.launcher_host != "127.0.0.1"
        or process.launcher_port != 10533
        or process.launcher_models != ["gpt-image-2"]
        or process.oauth_file_path_sha256 != expected_oauth_hash
    ):
        raise RuntimeFingerprintError(
            "Pilot-3 production runtime must use the exact bun openai-oauth "
            "entrypoint on 127.0.0.1:10533 with --models gpt-image-2 and the "
            "canonical Codex OAuth file"
        )


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def revalidate_pilot3_oauth_runtime_fingerprint(
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    *,
    client: Optional[httpx.Client] = None,
    process_inspector: ProcessInspector = _inspect_pilot3_oauth_process,
) -> Pilot3OAuthRuntimeRevalidation:
    """Fail closed if the dedicated listener or source changed after freezing."""

    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    current = capture_pilot3_oauth_runtime_fingerprint(
        config, client=client, process_inspector=process_inspector
    )
    exact_checkout = config.checkout_path.resolve()
    current_cwd = Path(current.process.cwd).resolve()
    checks = {
        "transport_config_unchanged": current.transport_config_sha256
        == fingerprint.transport_config_sha256,
        "endpoint_unchanged": current.endpoint_url == fingerprint.endpoint_url,
        "frozen_requested_labels_unchanged": current.frozen_requested_labels
        == fingerprint.frozen_requested_labels,
        "captured_checkout_is_exact": Path(fingerprint.source.checkout_path).resolve()
        == exact_checkout,
        "current_listener_pid_unchanged": current.process.pid == fingerprint.process.pid,
        "current_cwd_inside_exact_checkout": current.process.cwd_inside_checkout
        and _inside(current_cwd, exact_checkout),
        "process_command_unchanged": current.process.command_sha256
        == fingerprint.process.command_sha256,
        "process_executable_unchanged": fingerprint.process.executable_sha256 is None
        or current.process.executable_sha256 == fingerprint.process.executable_sha256,
        "source_snapshot_unchanged": current.source.source_snapshot_sha256
        == fingerprint.source.source_snapshot_sha256,
        "health_true": current.health_ok,
        "model_catalog_contains_frozen_labels": current.model_catalog_contains_frozen_labels,
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeFingerprintError(
            "live OAuth runtime no longer matches the persisted fingerprint: "
            + ", ".join(failed)
        )
    payload: Dict[str, Any] = {
        "schema_version": "pilot3-oauth-runtime-revalidation-v1",
        "checked_at": _json_utc_now(),
        "status": "pass",
        "persisted_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": list(config.frozen_requested_labels),
        "current_listener_pid": current.process.pid,
        "current_process_cwd": current.process.cwd,
        "current_source_snapshot_sha256": current.source.source_snapshot_sha256,
        "current_health_response_sha256": current.health.response_body_sha256,
        "current_model_catalog_response_sha256": current.model_catalog.response_body_sha256,
        "checks": checks,
    }
    payload["revalidation_sha256"] = stable_hash(payload)
    return Pilot3OAuthRuntimeRevalidation.model_validate(payload)


class Pilot3OAuthTransport:
    """One-call transport; a call performs at most one physical POST."""

    def __init__(
        self,
        config: Pilot3TransportConfig,
        *,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.config = config
        self._client = client or httpx.Client(
            timeout=config.timeout_seconds,
            follow_redirects=False,
            trust_env=False,
        )
        self._owns_client = client is None

    def __enter__(self) -> "Pilot3OAuthTransport":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def post_once(self, canonical_request: bytes) -> TransportExchange:
        try:
            parsed = json.loads(canonical_request.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransportConfigurationError("request bytes are not UTF-8 JSON") from exc
        if not isinstance(parsed, dict):
            raise TransportConfigurationError("request JSON must be an object")
        expected = canonical_image_request_bytes(
            parsed.get("prompt"),
            parsed.get("model"),
            frozen_requested_labels=self.config.frozen_requested_labels,
        )
        if canonical_request != expected:
            raise TransportConfigurationError(
                "request bytes are not the canonical Pilot-3 image request"
            )
        started = _utc_now()
        try:
            request = self._client.build_request(
                "POST",
                self.config.endpoint_url,
                content=canonical_request,
                headers={"accept": "application/json", "content-type": "application/json"},
            )
            response = self._client.send(request, stream=False)
            body = response.content
            return TransportExchange(
                started_at=started,
                completed_at=_utc_now(),
                http_status=response.status_code,
                response_body=body,
                response_body_sha256=hash_bytes(body),
                response_body_bytes=len(body),
                response_metadata=_safe_response_metadata(response.headers),
            )
        except httpx.HTTPError as exc:
            return TransportExchange(
                started_at=started,
                completed_at=_utc_now(),
                transport_error_kind=type(exc).__name__,
                transport_error_reason=sanitize_external_text(exc),
                # Once ``send`` has begun, httpx cannot attest that zero request
                # bytes reached the loopback proxy (nor that the proxy did not
                # complete the upstream image request).  Blindly retrying such an
                # ambiguous failure could duplicate an executed analytic request.
                transport_error_retryable=False,
            )
        except Exception as exc:
            return TransportExchange(
                started_at=started,
                completed_at=_utc_now(),
                transport_error_kind=type(exc).__name__,
                transport_error_reason=sanitize_external_text(exc),
                transport_error_retryable=False,
            )


__all__ = [
    "ALLOWED_REQUESTED_MODELS",
    "EXECUTED_MODEL_CLAIMS",
    "EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT",
    "EXPECTED_PILOT3_OAUTH_FILE",
    "OPERATIONAL_MODEL_ESTIMAND",
    "Pilot3OAuthRuntimeFingerprint",
    "Pilot3OAuthRuntimeRevalidation",
    "Pilot3OAuthSourceSnapshot",
    "Pilot3OAuthTransport",
    "Pilot3TransportConfig",
    "Pilot3TransportError",
    "REQUEST_OUTPUT_FORMAT",
    "REQUEST_QUALITY",
    "REQUEST_SIZE",
    "RequestedImageModel",
    "RuntimeFingerprintError",
    "SNAPSHOT_IDENTITY_CLAIMS",
    "TransportConfigurationError",
    "TransportExchange",
    "canonical_image_request_bytes",
    "capture_pilot3_oauth_runtime_fingerprint",
    "capture_pilot3_oauth_source_snapshot",
    "revalidate_pilot3_oauth_runtime_fingerprint",
    "sanitize_external_text",
    "validate_frozen_requested_labels",
    "verify_pilot3_oauth_runtime_fingerprint",
    "verify_pilot3_production_runtime_fingerprint",
    "verify_pilot3_oauth_source_snapshot",
]
