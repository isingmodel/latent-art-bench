"""Auditable, single-POST transport for the prospective pilot-2 image run.

This module deliberately distinguishes a requested model label from an executed
backend model identity.  The local OAuth service validates and forwards the label,
but its successful response does not attest which model executed upstream.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit, urlunsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.io import hash_bytes, hash_file, stable_hash

RequestedImageModel = Literal["gpt-image-1", "gpt-image-2"]

ALLOWED_REQUESTED_MODELS: Tuple[RequestedImageModel, ...] = (
    "gpt-image-1",
    "gpt-image-2",
)
EXECUTED_MODEL_CLAIMS: Literal[False] = False
OPERATIONAL_MODEL_ESTIMAND = "requested_model_label_accepted_by_oauth_endpoint"
REQUEST_SIZE: Literal["auto"] = "auto"
REQUEST_QUALITY: Literal["low"] = "low"
REQUEST_OUTPUT_FORMAT: Literal["png"] = "png"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
EXPECTED_ENDPOINT_PATH = "/v1/images/generations"

_SOURCE_PREFIXES = (
    "packages/openai-oauth/src/",
    "packages/openai-oauth-core/src/",
    "packages/openai-oauth-provider/src/",
)
_RUNTIME_METADATA_PATHS = frozenset(
    {
        "package.json",
        "bun.lock",
        "turbo.json",
        "tsconfig.json",
        "packages/openai-oauth/package.json",
        "packages/openai-oauth/tsconfig.json",
        "packages/openai-oauth-core/package.json",
        "packages/openai-oauth-core/tsconfig.json",
        "packages/openai-oauth-provider/package.json",
        "packages/openai-oauth-provider/tsconfig.json",
    }
)
_SOURCE_SUFFIXES = frozenset({".ts", ".tsx", ".js", ".mjs", ".cjs", ".json"})
_SAFE_RESPONSE_HEADERS = frozenset(
    {
        "content-type",
        "openai-processing-ms",
        "request-id",
        "retry-after",
        "x-request-id",
    }
)
_SECRET_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r'''(?ix)["'](?:access_token|refresh_token|id_token|api_key|private_key)["']
        \s*[:=]\s*["'][^"']{8,}["']'''
    ),
)


class Pilot2TransportError(RuntimeError):
    """Base class for pilot-2 transport and provenance failures."""


class TransportConfigurationError(Pilot2TransportError, ValueError):
    """Raised before any network request when the transport is out of scope."""


class RuntimeFingerprintError(Pilot2TransportError):
    """Raised when the OAuth runtime cannot be captured without ambiguity."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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
        raise TransportConfigurationError(f"request is not canonical JSON data: {exc}") from exc
    return rendered.encode("utf-8")


def canonical_image_request_bytes(
    prompt: str, requested_model: RequestedImageModel
) -> bytes:
    """Return the exact UTF-8 bytes sent to the OAuth image endpoint."""

    if requested_model not in ALLOWED_REQUESTED_MODELS:
        raise TransportConfigurationError(
            f"requested model must be one of {list(ALLOWED_REQUESTED_MODELS)!r}"
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


class OAuthTransportConfig(_StrictModel):
    """Immutable-in-practice scope guard for the only permitted pilot-2 route."""

    base_url: str = "http://127.0.0.1:10531/v1"
    checkout_path: Path = Field(
        default_factory=lambda: Path.home() / "dev" / "openai-oauth"
    )
    required_checkout_path: Path = Field(
        default_factory=lambda: Path.home() / "dev" / "openai-oauth"
    )
    timeout_seconds: float = Field(default=600.0, gt=0)

    @model_validator(mode="after")
    def exact_local_transport(self) -> "OAuthTransportConfig":
        parsed = urlsplit(self.base_url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOOPBACK_HOSTS:
            raise ValueError("pilot-2 image generation requires an HTTP(S) loopback OAuth URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("OAuth base URL cannot contain credentials, a query, or a fragment")
        if parsed.path.rstrip("/") != "/v1":
            raise ValueError("OAuth base URL must end at the exact /v1 API root")
        checkout = self.checkout_path.expanduser().resolve()
        required = self.required_checkout_path.expanduser().resolve()
        if checkout != required:
            raise ValueError(
                f"OAuth checkout must be the pinned checkout {required}, found {checkout}"
            )
        object.__setattr__(self, "checkout_path", checkout)
        object.__setattr__(self, "required_checkout_path", required)
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


class SourceFileEvidence(_StrictModel):
    path: str
    state: Literal["present", "deleted"]
    tracked_at_head: bool
    current_sha256: Optional[str] = None
    current_size_bytes: Optional[int] = Field(default=None, ge=0)


class OAuthSourceSnapshot(_StrictModel):
    schema_version: Literal["pilot2-oauth-source-snapshot-v1"] = (
        "pilot2-oauth-source-snapshot-v1"
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
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
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


class EndpointProbeEvidence(_StrictModel):
    url: str
    http_status: int = Field(ge=100, le=599)
    response_body_sha256: str
    response_body_bytes: int = Field(ge=0)
    response_metadata: Dict[str, str]
    parsed_summary: Dict[str, Any]


class OAuthRuntimeFingerprint(_StrictModel):
    schema_version: Literal["pilot2-oauth-runtime-fingerprint-v1"] = (
        "pilot2-oauth-runtime-fingerprint-v1"
    )
    captured_at: datetime
    endpoint_url: str
    executed_model_claims: Literal[False] = False
    operational_model_estimand: Literal[
        "requested_model_label_accepted_by_oauth_endpoint"
    ] = OPERATIONAL_MODEL_ESTIMAND
    source: OAuthSourceSnapshot
    process: OAuthProcessEvidence
    health: EndpointProbeEvidence
    model_catalog: EndpointProbeEvidence
    required_requested_labels: List[RequestedImageModel]
    health_ok: bool
    model_catalog_contains_required_labels: bool
    runtime_ready: bool
    fingerprint_sha256: str

    @field_validator("fingerprint_sha256")
    @classmethod
    def fingerprint_is_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("runtime fingerprint hash must be lowercase SHA-256")
        return value


class OAuthRuntimeRevalidation(_StrictModel):
    schema_version: Literal["pilot2-oauth-runtime-revalidation-v1"] = (
        "pilot2-oauth-runtime-revalidation-v1"
    )
    checked_at: datetime
    status: Literal["pass"] = "pass"
    persisted_fingerprint_sha256: str
    endpoint_url: str
    current_listener_pid: int = Field(gt=0)
    current_process_cwd: str
    current_source_snapshot_sha256: str
    current_health_response_sha256: str
    current_model_catalog_response_sha256: str
    checks: Dict[str, bool]
    revalidation_sha256: str

    @model_validator(mode="after")
    def content_hash_is_current(self) -> "OAuthRuntimeRevalidation":
        if not self.checks or not all(self.checks.values()):
            raise ValueError("successful runtime revalidation contains a failed check")
        payload = self.model_dump(mode="json", exclude={"revalidation_sha256"})
        if stable_hash(payload) != self.revalidation_sha256:
            raise ValueError("OAuth runtime revalidation hash is stale")
        return self

    @field_validator(
        "persisted_fingerprint_sha256",
        "current_source_snapshot_sha256",
        "current_health_response_sha256",
        "current_model_catalog_response_sha256",
        "revalidation_sha256",
    )
    @classmethod
    def revalidation_hashes(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("runtime revalidation hashes must be lowercase SHA-256")
        return value


class TransportExchange(_StrictModel):
    """In-memory result of exactly one physical POST.

    ``response_body`` is excluded from normal serialization.  The durable attempt
    ledger stores its hash and sanitized derivatives, never the base64 response body.
    """

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


def _run_git(checkout: Path, arguments: Sequence[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = sanitize_external_text(result.stderr.strip() or result.stdout.strip())
        raise RuntimeFingerprintError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _is_relevant_source_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if normalized in _RUNTIME_METADATA_PATHS:
        return True
    return any(normalized.startswith(prefix) for prefix in _SOURCE_PREFIXES) and (
        Path(normalized).suffix in _SOURCE_SUFFIXES
    )


def _assert_secret_free(value: str, description: str) -> None:
    for pattern in _SECRET_PATTERNS:
        if pattern.search(value):
            raise RuntimeFingerprintError(
                f"refusing to persist possible secret in {description}; "
                "remove it from runtime source before fingerprinting"
            )


def sanitize_external_text(value: object, limit: int = 1000) -> str:
    """Redact common credential forms from untrusted process/error text."""

    text = str(value)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("<redacted-secret>", text)
    text = re.sub(
        r"(?i)(--(?:oauth-file|token|api-key|authorization))(?:=|\s+)\S+",
        r"\1 <redacted>",
        text,
    )
    return text[:limit]


def _sanitize_remote(remote: str) -> str:
    remote = remote.strip()
    parsed = urlsplit(remote)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        host = parsed.hostname
        if parsed.port is not None:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    return sanitize_external_text(remote)


def _parse_porcelain_paths(status: str) -> List[str]:
    paths: List[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", maxsplit=1)[1]
        if raw_path.startswith('"'):
            try:
                raw_path = shlex.split(raw_path)[0]
            except (ValueError, IndexError):
                pass
        paths.append(raw_path)
    return paths


def capture_oauth_source_snapshot(checkout_path: Path) -> OAuthSourceSnapshot:
    """Capture a reconstructable snapshot of all first-party OAuth runtime source.

    Tracked files are reconstructable from ``git_head`` plus ``tracked_diff``.
    Every relevant untracked source file is embedded verbatim.  Cache, test, and
    documentation dirt is reported separately but does not affect runtime coverage.
    """

    checkout = checkout_path.expanduser().resolve()
    if not checkout.is_dir():
        raise RuntimeFingerprintError(f"OAuth checkout does not exist: {checkout}")
    head = _run_git(checkout, ["rev-parse", "HEAD"]).strip()
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise RuntimeFingerprintError("OAuth checkout HEAD is not a full SHA-1 commit id")
    remote = _sanitize_remote(_run_git(checkout, ["remote", "get-url", "origin"]))
    status = _run_git(checkout, ["status", "--porcelain=v1", "--untracked-files=all"])
    _assert_secret_free(status, "OAuth git status paths")

    head_paths = set(_run_git(checkout, ["ls-tree", "-r", "--name-only", "HEAD"]).splitlines())
    current_paths = {
        str(path.relative_to(checkout)).replace("\\", "/")
        for prefix in _SOURCE_PREFIXES
        for path in (checkout / prefix).rglob("*")
        if path.is_file()
    }
    current_paths.update(
        path for path in _RUNTIME_METADATA_PATHS if (checkout / path).is_file()
    )
    relevant_paths = sorted(
        path for path in head_paths | current_paths if _is_relevant_source_path(path)
    )
    if not relevant_paths:
        raise RuntimeFingerprintError("OAuth checkout contains no recognized runtime source")

    tracked_paths = [path for path in relevant_paths if path in head_paths]
    diff_arguments = ["diff", "--binary", "--no-ext-diff", "HEAD", "--", *tracked_paths]
    tracked_diff = _run_git(checkout, diff_arguments) if tracked_paths else ""
    _assert_secret_free(tracked_diff, "tracked OAuth source diff")

    files: List[SourceFileEvidence] = []
    untracked_contents: Dict[str, str] = {}
    for relative in relevant_paths:
        path = checkout / relative
        if not path.is_file():
            files.append(
                SourceFileEvidence(
                    path=relative,
                    state="deleted",
                    tracked_at_head=relative in head_paths,
                )
            )
            continue
        payload = path.read_bytes()
        files.append(
            SourceFileEvidence(
                path=relative,
                state="present",
                tracked_at_head=relative in head_paths,
                current_sha256=hash_bytes(payload),
                current_size_bytes=len(payload),
            )
        )
        if relative not in head_paths:
            try:
                content = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RuntimeFingerprintError(
                    f"untracked runtime source is not UTF-8 and cannot be captured: {relative}"
                ) from exc
            _assert_secret_free(content, f"untracked OAuth source {relative}")
            untracked_contents[relative] = content

    dirty_paths = _parse_porcelain_paths(status)
    runtime_dirty_paths = sorted(path for path in dirty_paths if _is_relevant_source_path(path))
    excluded_dirty_paths = sorted(
        path for path in dirty_paths if not _is_relevant_source_path(path)
    )
    captured_paths = {item.path for item in files}
    capture_complete = all(path in captured_paths for path in runtime_dirty_paths)
    if not capture_complete:
        missing = sorted(set(runtime_dirty_paths) - captured_paths)
        raise RuntimeFingerprintError(
            "dirty runtime source was not captured completely: " + ", ".join(missing)
        )

    payload: Dict[str, Any] = {
        "schema_version": "pilot2-oauth-source-snapshot-v1",
        "checkout_path": str(checkout),
        "git_head": head,
        "git_remote": remote,
        "dirty": bool(status.strip()),
        "relevant_roots": [*_SOURCE_PREFIXES, *sorted(_RUNTIME_METADATA_PATHS)],
        "files": [item.model_dump(mode="json") for item in files],
        "git_status_porcelain": status,
        "tracked_diff": tracked_diff,
        "tracked_diff_sha256": hash_bytes(tracked_diff.encode("utf-8")),
        "untracked_source_contents": untracked_contents,
        "excluded_dirty_paths": excluded_dirty_paths,
        "runtime_source_dirty_paths": runtime_dirty_paths,
        "dirty_runtime_source_capture_complete": capture_complete,
    }
    payload["source_snapshot_sha256"] = stable_hash(payload)
    return OAuthSourceSnapshot.model_validate(payload)


def _listener_pid(host: str, port: int) -> int:
    del host  # lsof filters the bound port; cwd verification supplies the stronger link.
    result = subprocess.run(
        ["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-t"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    pids = sorted({int(line) for line in result.stdout.splitlines() if line.strip().isdigit()})
    if result.returncode != 0 or len(pids) != 1:
        raise RuntimeFingerprintError(
            f"expected exactly one process listening on loopback port {port}, found {pids}"
        )
    return pids[0]


def _process_cwd(pid: int) -> Path:
    result = subprocess.run(
        ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    candidates = [line[1:] for line in result.stdout.splitlines() if line.startswith("n/")]
    if result.returncode != 0 or len(candidates) != 1:
        raise RuntimeFingerprintError(f"could not determine cwd for OAuth process {pid}")
    return Path(candidates[0]).resolve()


def _process_command(pid: int) -> str:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-ww", "-o", "command="],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    command = result.stdout.strip()
    if result.returncode != 0 or not command:
        raise RuntimeFingerprintError(f"could not determine command for OAuth process {pid}")
    return command


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def inspect_oauth_process(host: str, port: int, checkout: Path) -> OAuthProcessEvidence:
    pid = _listener_pid(host, port)
    cwd = _process_cwd(pid)
    command = _process_command(pid)
    sanitized_command = sanitize_external_text(command, limit=4000)
    command_sha256 = hashlib.sha256(command.encode("utf-8")).hexdigest()

    executable_path: Optional[str] = None
    executable_sha256: Optional[str] = None
    runtime_version: Optional[str] = None
    try:
        first_argument = shlex.split(command)[0]
        executable = Path(first_argument).expanduser()
        if executable.is_file():
            executable = executable.resolve()
            executable_path = str(executable)
            executable_sha256 = hash_file(executable)
            version = subprocess.run(
                [str(executable), "--version"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            runtime_version = sanitize_external_text(
                version.stdout.strip() or version.stderr.strip(), limit=200
            )
    except (OSError, ValueError, subprocess.SubprocessError):
        pass

    return OAuthProcessEvidence(
        pid=pid,
        cwd=str(cwd),
        cwd_inside_checkout=_inside(cwd, checkout),
        command_sanitized=sanitized_command,
        command_sha256=command_sha256,
        executable_path=executable_path,
        executable_sha256=executable_sha256,
        runtime_version=runtime_version,
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
    parsed: Any = None
    try:
        parsed = response.json()
    except ValueError:
        pass
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
    parsed: Any = None
    try:
        parsed = response.json()
    except ValueError:
        pass
    models: List[str] = []
    if isinstance(parsed, dict) and isinstance(parsed.get("data"), list):
        for item in parsed["data"]:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                models.append(sanitize_external_text(item["id"], limit=200))
    models = sorted(set(models))
    summary = {
        "object": parsed.get("object") if isinstance(parsed, dict) else None,
        "model_ids": models,
    }
    return _endpoint_probe(response, str(response.request.url), summary), models


ProcessInspector = Callable[[str, int, Path], OAuthProcessEvidence]


def capture_oauth_runtime_fingerprint(
    config: OAuthTransportConfig,
    *,
    client: Optional[httpx.Client] = None,
    process_inspector: ProcessInspector = inspect_oauth_process,
) -> OAuthRuntimeFingerprint:
    """Capture source, process, health, and model-catalog evidence without secrets."""

    source = capture_oauth_source_snapshot(config.checkout_path)
    parsed = urlsplit(config.base_url)
    if parsed.port is not None:
        port = parsed.port
    else:
        port = 443 if parsed.scheme == "https" else 80
    assert parsed.hostname is not None
    process = process_inspector(parsed.hostname, port, config.checkout_path)

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
        model_response = probe_client.get(config.models_url, headers={"accept": "application/json"})
    except httpx.HTTPError as exc:
        raise RuntimeFingerprintError(
            f"OAuth runtime probe failed: {sanitize_external_text(exc)}"
        ) from exc
    finally:
        if owns_client:
            probe_client.close()

    health, health_ok = _parse_health(health_response)
    catalog, catalog_models = _parse_model_catalog(model_response)
    contains_models = set(ALLOWED_REQUESTED_MODELS).issubset(catalog_models)
    ready = bool(
        health_ok
        and contains_models
        and process.cwd_inside_checkout
        and source.dirty_runtime_source_capture_complete
    )
    payload: Dict[str, Any] = {
        "schema_version": "pilot2-oauth-runtime-fingerprint-v1",
        "captured_at": _utc_now(),
        "endpoint_url": config.endpoint_url,
        "executed_model_claims": False,
        "operational_model_estimand": OPERATIONAL_MODEL_ESTIMAND,
        "source": source.model_dump(mode="json"),
        "process": process.model_dump(mode="json"),
        "health": health.model_dump(mode="json"),
        "model_catalog": catalog.model_dump(mode="json"),
        "required_requested_labels": list(ALLOWED_REQUESTED_MODELS),
        "health_ok": health_ok,
        "model_catalog_contains_required_labels": contains_models,
        "runtime_ready": ready,
    }
    provisional = OAuthRuntimeFingerprint.model_validate(
        {**payload, "fingerprint_sha256": "0" * 64}
    )
    normalized = provisional.model_dump(mode="json", exclude={"fingerprint_sha256"})
    payload["fingerprint_sha256"] = stable_hash(normalized)
    fingerprint = OAuthRuntimeFingerprint.model_validate(payload)
    verify_oauth_runtime_fingerprint(fingerprint)
    return fingerprint


def verify_oauth_source_snapshot(snapshot: OAuthSourceSnapshot) -> None:
    """Reject a persisted source snapshot whose content identity is stale."""

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
        untracked_content_missing = (
            not item.tracked_at_head
            and item.state == "present"
            and item.path not in untracked_paths
        )
        if untracked_content_missing:
            raise RuntimeFingerprintError(
                f"OAuth source snapshot omits untracked content: {item.path}"
            )


def verify_oauth_runtime_fingerprint(fingerprint: OAuthRuntimeFingerprint) -> None:
    """Verify all persisted hashes and the derived runtime-ready decision."""

    verify_oauth_source_snapshot(fingerprint.source)
    payload = fingerprint.model_dump(mode="json", exclude={"fingerprint_sha256"})
    if stable_hash(payload) != fingerprint.fingerprint_sha256:
        raise RuntimeFingerprintError("OAuth runtime fingerprint hash does not match its content")
    expected_ready = bool(
        fingerprint.health_ok
        and fingerprint.model_catalog_contains_required_labels
        and fingerprint.process.cwd_inside_checkout
        and fingerprint.source.dirty_runtime_source_capture_complete
    )
    if fingerprint.runtime_ready != expected_ready:
        raise RuntimeFingerprintError("OAuth runtime-ready decision is stale")
    if fingerprint.required_requested_labels != list(ALLOWED_REQUESTED_MODELS):
        raise RuntimeFingerprintError("OAuth fingerprint requested-label allowlist is stale")


def revalidate_oauth_runtime_fingerprint(
    config: OAuthTransportConfig,
    fingerprint: OAuthRuntimeFingerprint,
    *,
    client: Optional[httpx.Client] = None,
    process_inspector: ProcessInspector = inspect_oauth_process,
) -> OAuthRuntimeRevalidation:
    """Fail closed if the live listener or source changed after fingerprint freeze."""

    verify_oauth_runtime_fingerprint(fingerprint)
    current = capture_oauth_runtime_fingerprint(
        config, client=client, process_inspector=process_inspector
    )
    exact_checkout = config.checkout_path.resolve()
    current_cwd = Path(current.process.cwd).resolve()
    checks = {
        "endpoint_unchanged": (
            fingerprint.endpoint_url == config.endpoint_url == current.endpoint_url
        ),
        "captured_checkout_is_exact": (
            Path(fingerprint.source.checkout_path).resolve() == exact_checkout
        ),
        "current_listener_pid_unchanged": current.process.pid == fingerprint.process.pid,
        "current_cwd_inside_exact_checkout": (
            current.process.cwd_inside_checkout and _inside(current_cwd, exact_checkout)
        ),
        "process_command_unchanged": (
            current.process.command_sha256 == fingerprint.process.command_sha256
        ),
        "process_executable_unchanged": (
            fingerprint.process.executable_sha256 is None
            or current.process.executable_sha256 == fingerprint.process.executable_sha256
        ),
        "source_snapshot_unchanged": (
            current.source.source_snapshot_sha256
            == fingerprint.source.source_snapshot_sha256
        ),
        "health_true": current.health_ok,
        "model_catalog_contains_required_labels": (
            current.model_catalog_contains_required_labels
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeFingerprintError(
            "live OAuth runtime no longer matches the persisted fingerprint: "
            + ", ".join(failed)
        )
    payload: Dict[str, Any] = {
        "schema_version": "pilot2-oauth-runtime-revalidation-v1",
        "checked_at": _utc_now(),
        "status": "pass",
        "persisted_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "endpoint_url": config.endpoint_url,
        "current_listener_pid": current.process.pid,
        "current_process_cwd": current.process.cwd,
        "current_source_snapshot_sha256": current.source.source_snapshot_sha256,
        "current_health_response_sha256": current.health.response_body_sha256,
        "current_model_catalog_response_sha256": (
            current.model_catalog.response_body_sha256
        ),
        "checks": checks,
    }
    provisional = OAuthRuntimeRevalidation.model_construct(
        **payload, revalidation_sha256="0" * 64
    )
    normalized = provisional.model_dump(mode="json", exclude={"revalidation_sha256"})
    payload["revalidation_sha256"] = stable_hash(normalized)
    return OAuthRuntimeRevalidation.model_validate(payload)


class Pilot2OAuthTransport:
    """One-call transport: every invocation performs at most one physical POST."""

    def __init__(
        self,
        config: OAuthTransportConfig,
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

    def __enter__(self) -> "Pilot2OAuthTransport":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def post_once(self, canonical_request: bytes) -> TransportExchange:
        """Send exactly ``canonical_request`` as content, with no adapter retry."""

        try:
            parsed = json.loads(canonical_request.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransportConfigurationError("request bytes are not UTF-8 JSON") from exc
        if not isinstance(parsed, dict):
            raise TransportConfigurationError("request JSON must be an object")
        expected = canonical_image_request_bytes(parsed.get("prompt"), parsed.get("model"))
        if canonical_request != expected:
            raise TransportConfigurationError(
                "request bytes are not the canonical pilot-2 image request"
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
                transport_error_retryable=isinstance(exc, httpx.TransportError),
            )
        except Exception as exc:
            return TransportExchange(
                started_at=started,
                completed_at=_utc_now(),
                transport_error_kind=type(exc).__name__,
                transport_error_reason=sanitize_external_text(exc),
                transport_error_retryable=False,
            )
