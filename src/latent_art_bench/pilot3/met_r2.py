"""Prospective Pilot 3 R2 acquisition through the Met's official ``primaryImage``.

This module is intentionally separate from :mod:`latent_art_bench.pilot3.phasea`.
The original Freeze-A1 Met delivery path is closed and its Wikimedia Commons
bytes, intents, and terminals are evidence only.  R2 reuses the twenty frozen
physical-work identities, but gives every digital asset a new namespace and
requires a metadata-only refreeze before the first official image request.

Network I/O is injected.  The module never creates an HTTP client, follows a
redirect, searches for an alternative, or chooses among image derivatives.
"""

from __future__ import annotations

import fcntl
import hashlib
import io
import json
import os
import subprocess
import unicodedata
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit

from PIL import Image

from latent_art_bench.io import (
    canonical_json,
    hash_bytes,
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)

NAMESPACE = "pilot3-met-r2-official-primaryimage"
INCIDENT_SCHEMA = "pilot3-met-asset-provider-incident/1.0"
AUTHORIZATION_SCHEMA = "pilot3-met-r2-authorization/1.0"
METADATA_ATTEMPT_SCHEMA = "pilot3-met-r2-metadata-attempt/1.0"
TARGET_ROW_SCHEMA = "pilot3-met-r2-target-row/1.0"
METADATA_FREEZE_SCHEMA = "pilot3-met-r2-metadata-freeze/1.0"
IMAGE_ATTEMPT_SCHEMA = "pilot3-met-r2-image-attempt/1.0"
IMAGE_ACQUISITION_SCHEMA = "pilot3-met-r2-image-acquisition/1.0"

DEFAULT_INCIDENT = Path("reports/pilot_3/evidence/met_asset_provider_incident.json")
DEFAULT_SPLITS = Path("data/manifests/pilot_3/real_splits.jsonl")
DEFAULT_AUTHORIZATION = Path("reports/pilot_3/evidence/met_r2_authorization.json")
DEFAULT_METADATA_ATTEMPTS = Path("artifacts/pilot_3/met_r2_metadata_attempts.jsonl")
DEFAULT_METADATA_RAW_DIR = Path("artifacts/pilot_3/met_r2/metadata_raw")
DEFAULT_TARGET_MANIFEST = Path("data/manifests/pilot_3/met_r2_targets.jsonl")
DEFAULT_METADATA_FREEZE = Path("reports/pilot_3/evidence/met_r2_metadata_freeze.json")
DEFAULT_IMAGE_ATTEMPTS = Path("artifacts/pilot_3/met_r2_image_attempts.jsonl")
DEFAULT_IMAGE_RAW_DIR = Path("artifacts/pilot_3/met_r2/image_raw")
DEFAULT_IMAGE_ACQUISITIONS = Path("artifacts/pilot_3/met_r2_image_acquisitions.jsonl")
IMPLEMENTATION_PATHS = (
    "src/latent_art_bench/pilot3/met_r2.py",
    "src/latent_art_bench/pilot3/normalization_scope.py",
    "src/latent_art_bench/pilot3/cli.py",
    "tests/pilot3/test_met_r2.py",
    "tests/pilot3/test_normalization_scope.py",
    "docs/PILOT_3_R2_OFFICIAL_MET.md",
)

OFFICIAL_OBJECT_ENDPOINT_PREFIX = (
    "https://collectionapi.metmuseum.org/public/collection/v1/objects/"
)
OFFICIAL_METADATA_HOST = "collectionapi.metmuseum.org"
OFFICIAL_IMAGE_HOST = "images.metmuseum.org"
SELECTED_IMAGE_FIELD = "primaryImage"
FORBIDDEN_SELECTION_FIELDS = ("additionalImages", "primaryImageSmall")

EXPECTED_INCIDENT_FILE_SHA256 = (
    "bb7cdbe1fc58532c8e649a19a7dfbb7c47a12ef723cede395bac516f39fa5eb9"
)
EXPECTED_INCIDENT_SHA256 = (
    "5279df2c0e46b193a855585305b55b69e23f5df80f234940c48efa876e0cbbb7"
)
EXPECTED_SPLITS_FILE_SHA256 = (
    "0390c43435176df178a8d0e9b6c2dc407dca5a42acd6353183eb9b6198f4095f"
)
EXPECTED_OBJECT_IDS = (
    "435877",
    "435878",
    "435879",
    "435880",
    "435885",
    "437299",
    "437307",
    "437308",
    "437310",
    "437426",
    "437427",
    "437431",
    "437436",
    "437680",
    "437682",
    "437683",
    "437685",
    "437686",
    "438738",
    "459111",
)
EXPECTED_ARTIST_COUNTS = {
    "alfred_sisley": 5,
    "camille_pissarro": 5,
    "paul_cezanne": 5,
    "pierre_auguste_renoir": 5,
}
EXPECTED_PARTITION_COUNTS = {
    "development_calibration": 4,
    "development_training": 16,
}
MAX_METADATA_BYTES = 4 * 1024 * 1024
MAX_IMAGE_BYTES = 128 * 1024 * 1024


class Pilot3MetR2Error(RuntimeError):
    """Raised when the prospective official-Met protocol must close."""


@dataclass(frozen=True)
class TransportResponse:
    """A deliberately small, client-independent first-response envelope.

    ``redirect_chain`` contains any response URL observed before ``final_url``.
    A conforming R2 transport calls the injected requester exactly once with
    redirects disabled, so successful responses always leave it empty.
    """

    status_code: int
    body: bytes
    headers: Mapping[str, str]
    final_url: str
    redirect_chain: Tuple[str, ...] = field(default_factory=tuple)


Request = Callable[[str], TransportResponse]
@contextmanager
def _r2_phase_lock(root: Path, phase: str) -> Iterator[None]:
    if phase not in {"metadata", "image"}:
        raise ValueError("R2 lock phase must be metadata or image")
    path = _resolve(root, Path(f"artifacts/pilot_3/met_r2_{phase}.lock"))
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            raise Pilot3MetR2Error(
                f"another R2 {phase} process already holds the one-shot lock"
            ) from exc
        yield
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _self_hash(payload: Mapping[str, Any], field_name: str) -> Dict[str, Any]:
    result = dict(payload)
    result.pop(field_name, None)
    result[field_name] = stable_hash(result)
    return result


def _verify_self_hash(
    payload: Mapping[str, Any], field_name: str, *, label: str
) -> str:
    recorded = payload.get(field_name)
    if not _is_sha256(recorded):
        raise Pilot3MetR2Error(f"{label} lacks a valid {field_name}")
    unsigned = dict(payload)
    unsigned.pop(field_name, None)
    observed = stable_hash(unsigned)
    if observed != recorded:
        raise Pilot3MetR2Error(
            f"{label} has a stale {field_name}: recorded {recorded}, found {observed}"
        )
    return str(recorded)


def _resolve(root: Path, relative: Path) -> Path:
    root = Path(root).expanduser().resolve()
    if relative.is_absolute() or ".." in relative.parts:
        raise Pilot3MetR2Error(f"R2 path must remain inside the repository: {relative}")
    result = (root / relative).resolve()
    try:
        result.relative_to(root)
    except ValueError as exc:
        raise Pilot3MetR2Error(f"R2 path escapes repository root: {relative}") from exc
    return result


def _portable(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise Pilot3MetR2Error(f"R2 artifact escapes repository root: {path}") from exc


def _canonical_jsonl_sha256(rows: Iterable[Mapping[str, Any]]) -> str:
    payload = "".join(f"{canonical_json(dict(row))}\n" for row in rows).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _append_jsonl_fsync(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(row)) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError("short write while appending R2 JSONL")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _write_cas(root: Path, directory: Path, payload: bytes, suffix: str) -> Tuple[str, str]:
    digest = hash_bytes(payload)
    path = _resolve(root, directory) / digest[:2] / f"{digest}.{suffix}"
    if path.exists():
        if not path.is_file() or hash_file(path) != digest:
            raise Pilot3MetR2Error(f"R2 content-address collision at {path}")
    else:
        _atomic_bytes(path, payload)
    return _portable(path, root), digest


def _verify_cas_binding(
    root: Path,
    *,
    recorded_path: object,
    recorded_sha256: object,
    recorded_byte_count: object,
    directory: Path,
    suffix: str,
    label: str,
) -> bytes:
    if not isinstance(recorded_path, str) or not _is_sha256(recorded_sha256):
        raise Pilot3MetR2Error(f"{label} has an incomplete CAS binding")
    expected = (
        directory / str(recorded_sha256)[:2] / f"{recorded_sha256}.{suffix}"
    ).as_posix()
    if recorded_path != expected:
        raise Pilot3MetR2Error(f"{label} is not at its canonical R2 CAS path")
    path = _resolve(root, Path(recorded_path))
    if not path.is_file():
        raise Pilot3MetR2Error(f"{label} CAS payload is absent")
    payload = path.read_bytes()
    if (
        hash_bytes(payload) != recorded_sha256
        or not isinstance(recorded_byte_count, int)
        or isinstance(recorded_byte_count, bool)
        or recorded_byte_count != len(payload)
    ):
        raise Pilot3MetR2Error(f"{label} CAS hash or byte count changed")
    return payload


def _official_url(value: object, *, host: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise Pilot3MetR2Error(f"{label} must be a non-blank URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname is None
        or parsed.hostname.casefold() != host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or not parsed.path.startswith("/")
        or parsed.fragment
    ):
        raise Pilot3MetR2Error(f"{label} is not an exact official {host} HTTPS URL")
    return value


def _object_endpoint(object_id: str) -> str:
    if object_id not in EXPECTED_OBJECT_IDS:
        raise Pilot3MetR2Error(f"object {object_id} is outside the exact R2 cohort")
    return f"{OFFICIAL_OBJECT_ENDPOINT_PREFIX}{object_id}"


def verify_incident(root: Path) -> Dict[str, Any]:
    """Verify the exact self-hashed incident that closed the Commons path."""

    path = _resolve(root, DEFAULT_INCIDENT)
    if not path.is_file() or hash_file(path) != EXPECTED_INCIDENT_FILE_SHA256:
        raise Pilot3MetR2Error("the exact committed Met provider incident is absent or changed")
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != INCIDENT_SCHEMA:
        raise Pilot3MetR2Error("the Met provider incident has the wrong schema")
    observed = _verify_self_hash(value, "incident_sha256", label="Met provider incident")
    if observed != EXPECTED_INCIDENT_SHA256:
        raise Pilot3MetR2Error("R2 is bound to a different Met provider incident")
    if value.get("status") != "transport_succeeded_but_protocol_ineligible_not_admitted":
        raise Pilot3MetR2Error("the Met provider incident is not in the frozen closed status")
    authorization_effect = value.get("authorization_effect")
    if not isinstance(authorization_effect, dict) or authorization_effect != {
        "incident_authorizes_image_access": False,
        "incident_authorizes_metadata_access": False,
        "incident_authorizes_successor_protocol": False,
        "original_freeze_a1_met_delivery_path": "closed",
    }:
        raise Pilot3MetR2Error("the incident's authorization boundary changed")
    if tuple(value.get("selected_met_canonical_work_ids", ())) != tuple(
        f"work-met-{object_id}" for object_id in EXPECTED_OBJECT_IDS
    ):
        raise Pilot3MetR2Error("the incident does not bind the exact twenty Met works")
    quarantine = value.get("quarantine")
    if not isinstance(quarantine, dict) or any(
        quarantine.get(key) is not False
        for key in (
            "eligible_for_acquisition_materialization",
            "eligible_for_feature_extraction",
            "eligible_for_normalization",
            "eligible_for_retry_or_reuse_in_the_successor_protocol",
        )
    ):
        raise Pilot3MetR2Error("the original Commons payload is not fully quarantined")
    return value


def _selected_met_splits(root: Path) -> List[Dict[str, Any]]:
    path = _resolve(root, DEFAULT_SPLITS)
    if not path.is_file() or hash_file(path) != EXPECTED_SPLITS_FILE_SHA256:
        raise Pilot3MetR2Error("the exact frozen real split is absent or changed")
    selected: List[Dict[str, Any]] = []
    for raw in read_jsonl(path):
        if not isinstance(raw, dict):
            raise Pilot3MetR2Error("the frozen split contains a non-object row")
        if raw.get("source_id") != "met" or raw.get("selection_status") != "selected":
            continue
        _verify_self_hash(raw, "row_sha256", label="frozen Met split row")
        selected.append(dict(raw))
    selected.sort(key=lambda row: int(str(row["source_object_id"])))
    object_ids = tuple(str(row.get("source_object_id")) for row in selected)
    if object_ids != EXPECTED_OBJECT_IDS:
        raise Pilot3MetR2Error("the frozen split does not contain the exact R2 object cohort")
    if Counter(str(row.get("artist_id")) for row in selected) != EXPECTED_ARTIST_COUNTS:
        raise Pilot3MetR2Error("the frozen split changed the R2 artist balance")
    if Counter(str(row.get("partition")) for row in selected) != EXPECTED_PARTITION_COUNTS:
        raise Pilot3MetR2Error("the frozen split changed the R2 partition balance")
    for row in selected:
        object_id = str(row["source_object_id"])
        if (
            row.get("canonical_work_id") != f"work-met-{object_id}"
            or row.get("source_role") != "development"
            or row.get("public_domain_status") != "confirmed"
            or row.get("asset_provider")
            != "Wikimedia Commons P18 delivery for Met work"
        ):
            raise Pilot3MetR2Error(f"frozen work identity changed for object {object_id}")
        catalog_ids = row.get("catalog_ids")
        authority_ids = row.get("artist_authority_ids")
        if (
            not isinstance(catalog_ids, dict)
            or str(catalog_ids.get("met")) != object_id
            or catalog_ids.get("met_accession") != row.get("museum_accession")
            or not isinstance(authority_ids, dict)
            or not str(authority_ids.get("met_constituent_id", "")).isdigit()
        ):
            raise Pilot3MetR2Error(f"frozen Met identity is incomplete for object {object_id}")
    return selected


def _target_binding(split: Mapping[str, Any]) -> Dict[str, Any]:
    object_id = str(split["source_object_id"])
    return {
        "r2_asset_id": f"met-r2-primaryimage-{object_id}",
        "physical_work_id": split["canonical_work_id"],
        "object_id": object_id,
        "object_endpoint": _object_endpoint(object_id),
        "accession_number": split["museum_accession"],
        "artist_id": split["artist_id"],
        "artist_name": split["artist_name"],
        "artist_constituent_id": str(
            split["artist_authority_ids"]["met_constituent_id"]
        ),
        "partition": split["partition"],
        "frozen_split_row_sha256": split["row_sha256"],
        "frozen_selection_sha256": split["selection_sha256"],
    }


def _implementation_bindings(root: Path) -> List[Dict[str, str]]:
    bindings: List[Dict[str, str]] = []
    for relative in IMPLEMENTATION_PATHS:
        path = _resolve(root, Path(relative))
        if not path.is_file():
            raise Pilot3MetR2Error(f"R2 implementation closure path is absent: {relative}")
        bindings.append({"path": relative, "file_sha256": hash_file(path)})
    return bindings


def build_offline_authorization(root: Path) -> Dict[str, Any]:
    """Build the prospective authorization without metadata or image access."""

    incident = verify_incident(root)
    splits = _selected_met_splits(root)
    payload = {
        "schema_version": AUTHORIZATION_SCHEMA,
        "record_type": "pilot3_met_r2_authorization",
        "namespace": NAMESPACE,
        "status": "metadata_authorized_image_conditional_on_committed_metadata_freeze",
        "incident_binding": {
            "path": str(DEFAULT_INCIDENT),
            "file_sha256": EXPECTED_INCIDENT_FILE_SHA256,
            "incident_sha256": incident["incident_sha256"],
            "closed_legacy_namespace": "pilot3-real-split-row/1.0:met:commons-delivery",
        },
        "physical_work_freeze_binding": {
            "path": str(DEFAULT_SPLITS),
            "file_sha256": EXPECTED_SPLITS_FILE_SHA256,
            "work_count": len(splits),
        },
        "implementation_bindings": _implementation_bindings(root),
        "metadata_policy": {
            "request_method": "GET",
            "request_count": 20,
            "endpoint_prefix": OFFICIAL_OBJECT_ENDPOINT_PREFIX,
            "exact_endpoint_per_object": True,
            "redirect_policy": "forbid_all",
            "search_endpoints_allowed": False,
            "selected_image_field": SELECTED_IMAGE_FIELD,
            "forbidden_selection_fields": list(FORBIDDEN_SELECTION_FIELDS),
            "fallback_allowed": False,
        },
        "image_policy": {
            "request_count": 20,
            "request_url_source": "committed_target_manifest.primary_image_url",
            "required_host": OFFICIAL_IMAGE_HOST,
            "redirect_policy": "forbid_all",
            "fallback_allowed": False,
            "replacement_allowed": False,
            "dimensions": "observe_first_response_without_derivative_switching",
            "atomic_eligibility": "all_20_or_none",
        },
        "targets": [_target_binding(split) for split in splits],
    }
    return _self_hash(payload, "authorization_sha256")


def verify_authorization(root: Path, value: Mapping[str, Any]) -> Dict[str, Any]:
    """Verify self-hash and exact deterministic reconstruction of an authorization."""

    if value.get("schema_version") != AUTHORIZATION_SCHEMA:
        raise Pilot3MetR2Error("R2 authorization has the wrong schema")
    _verify_self_hash(value, "authorization_sha256", label="R2 authorization")
    expected = build_offline_authorization(root)
    observed = dict(value)
    if observed != expected:
        changed = sorted(
            key for key in set(observed) | set(expected) if observed.get(key) != expected.get(key)
        )
        raise Pilot3MetR2Error(
            "R2 authorization differs from deterministic reconstruction: "
            + ", ".join(changed)
        )
    return observed


def write_offline_authorization(
    root: Path,
    *,
    path: Path = DEFAULT_AUTHORIZATION,
) -> Dict[str, Any]:
    """Materialize the offline authorization; callers must commit it before capture."""

    value = build_offline_authorization(root)
    resolved = _resolve(root, path)
    if resolved.exists():
        existing = read_json(resolved)
        if existing != value:
            raise Pilot3MetR2Error("refusing to replace an existing R2 authorization")
    else:
        write_json(resolved, value)
    return value


def load_authorization(
    root: Path, path: Path = DEFAULT_AUTHORIZATION
) -> Dict[str, Any]:
    resolved = _resolve(root, path)
    if not resolved.is_file():
        raise Pilot3MetR2Error("R2 authorization is absent")
    value = read_json(resolved)
    if not isinstance(value, dict):
        raise Pilot3MetR2Error("R2 authorization must be a JSON object")
    return verify_authorization(root, value)


def _git_path_committed_and_clean(root: Path, relative: str) -> bool:
    listed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if listed.returncode != 0:
        return False
    dirty = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=root,
        check=False,
    )
    return dirty.returncode == 0


def _require_committed_paths(
    root: Path,
    paths: Sequence[str],
) -> None:
    for relative in paths:
        if not _git_path_committed_and_clean(root, relative):
            raise Pilot3MetR2Error(
                f"R2 gate requires a committed and clean path: {relative}"
            )


def require_committed_authorization(
    root: Path,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
) -> Dict[str, Any]:
    value = load_authorization(root, authorization_path)
    _require_committed_paths(
        root,
        [
            str(DEFAULT_INCIDENT),
            str(DEFAULT_SPLITS),
            str(authorization_path),
            *(binding["path"] for binding in value["implementation_bindings"]),
        ],
    )
    return value


def _headers(response: TransportResponse) -> Dict[str, str]:
    if not isinstance(response.headers, Mapping):
        raise Pilot3MetR2Error("transport response headers must be a mapping")
    return {str(key).casefold(): str(value).strip() for key, value in response.headers.items()}


def _response_evidence(response: TransportResponse) -> Dict[str, Any]:
    headers = _headers(response)
    return {
        "status_code": response.status_code,
        "content_type": headers.get("content-type", "").split(";", 1)[0].casefold(),
        "content_length_header": headers.get("content-length"),
        "final_url": response.final_url,
        "redirect_chain": list(response.redirect_chain),
        "response_byte_count": len(response.body),
    }


def _event(
    payload: Mapping[str, Any],
    *,
    schema: str,
    event_index: int,
    previous_event_sha256: Optional[str],
) -> Dict[str, Any]:
    result = {
        "schema_version": schema,
        "namespace": NAMESPACE,
        "event_index": event_index,
        "previous_event_sha256": previous_event_sha256,
        **dict(payload),
    }
    return _self_hash(result, "event_sha256")


def _append_event(
    path: Path,
    events: List[Dict[str, Any]],
    payload: Mapping[str, Any],
    *,
    schema: str,
) -> Dict[str, Any]:
    value = _event(
        payload,
        schema=schema,
        event_index=len(events) + 1,
        previous_event_sha256=(events[-1]["event_sha256"] if events else None),
    )
    _append_jsonl_fsync(path, value)
    events.append(value)
    return value


def _verify_event_chain(
    path: Path,
    *,
    schema: str,
    allowed_event_types: Sequence[str],
) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    previous: Optional[str] = None
    for index, raw in enumerate(read_jsonl(path), start=1):
        if not isinstance(raw, dict):
            raise Pilot3MetR2Error(f"R2 journal {path} contains a non-object row")
        if (
            raw.get("schema_version") != schema
            or raw.get("namespace") != NAMESPACE
            or raw.get("event_index") != index
            or raw.get("previous_event_sha256") != previous
            or raw.get("event_type") not in allowed_event_types
        ):
            raise Pilot3MetR2Error(f"R2 journal chain is malformed at {path}:{index}")
        previous = _verify_self_hash(raw, "event_sha256", label=f"R2 journal row {index}")
        events.append(dict(raw))
    return events


def _metadata_attempt_id(authorization_sha256: str, asset_id: str) -> str:
    return "met-r2-metadata-" + stable_hash(
        {"authorization_sha256": authorization_sha256, "r2_asset_id": asset_id}
    )[:24]


def _normalize_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character))
        .casefold()
        .split()
    )


def _parse_metadata(
    target: Mapping[str, Any], payload: bytes
) -> Tuple[Dict[str, Any], str]:
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Pilot3MetR2Error("official Met metadata is not UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise Pilot3MetR2Error("official Met metadata must be a JSON object")
    object_id = target["object_id"]
    if str(decoded.get("objectID")) != object_id:
        raise Pilot3MetR2Error(f"official metadata objectID mismatch for {object_id}")
    if decoded.get("accessionNumber") != target["accession_number"]:
        raise Pilot3MetR2Error(f"official metadata accession mismatch for {object_id}")
    if str(decoded.get("artistConstituentID")) != target["artist_constituent_id"]:
        raise Pilot3MetR2Error(f"official metadata artist authority mismatch for {object_id}")
    display_name = decoded.get("artistDisplayName")
    if not isinstance(display_name, str) or not _normalize_name(display_name):
        raise Pilot3MetR2Error(f"official metadata artist display name is blank for {object_id}")
    if decoded.get("isPublicDomain") is not True:
        raise Pilot3MetR2Error(f"official metadata isPublicDomain is not true for {object_id}")
    primary_image = _official_url(
        decoded.get(SELECTED_IMAGE_FIELD),
        host=OFFICIAL_IMAGE_HOST,
        label=f"official metadata {SELECTED_IMAGE_FIELD}",
    )
    return decoded, primary_image


def _verify_metadata_events(
    root: Path,
    authorization: Mapping[str, Any],
    *,
    attempts_path: Path,
) -> List[Dict[str, Any]]:
    path = _resolve(root, attempts_path)
    events = _verify_event_chain(
        path,
        schema=METADATA_ATTEMPT_SCHEMA,
        allowed_event_types=("metadata_request_start", "metadata_request_terminal"),
    )
    targets = authorization["targets"]
    if len(events) > 2 * len(targets):
        raise Pilot3MetR2Error("metadata journal exceeds the exact twenty-request schedule")
    for index, event in enumerate(events):
        target = targets[index // 2]
        common_fields = {
            "schema_version",
            "namespace",
            "event_index",
            "previous_event_sha256",
            "event_sha256",
            "event_type",
            "authorization_sha256",
            "r2_asset_id",
            "object_id",
            "attempt_id",
        }
        start_fields = common_fields | {
            "request_method",
            "request_url",
            "request_accept",
            "follow_redirects",
        }
        terminal_fields = common_fields | {
            "start_event_sha256",
            "outcome",
            "error_type",
            "error_message",
            "raw_metadata_path",
            "raw_metadata_sha256",
            "primary_image_url",
            "status_code",
            "content_type",
            "content_length_header",
            "final_url",
            "redirect_chain",
            "response_byte_count",
        }
        expected_id = _metadata_attempt_id(
            str(authorization["authorization_sha256"]), str(target["r2_asset_id"])
        )
        if (
            event.get("authorization_sha256") != authorization["authorization_sha256"]
            or event.get("r2_asset_id") != target["r2_asset_id"]
            or event.get("object_id") != target["object_id"]
            or event.get("attempt_id") != expected_id
        ):
            raise Pilot3MetR2Error("metadata journal target binding changed")
        if index % 2 == 0:
            if (
                set(event) != start_fields
                or
                event.get("event_type") != "metadata_request_start"
                or event.get("request_method") != "GET"
                or event.get("request_url") != target["object_endpoint"]
                or event.get("request_accept") != "application/json"
                or event.get("follow_redirects") is not False
            ):
                raise Pilot3MetR2Error("metadata request start is not the exact object endpoint")
        else:
            start = events[index - 1]
            if (
                set(event) != terminal_fields
                or
                event.get("event_type") != "metadata_request_terminal"
                or event.get("start_event_sha256") != start["event_sha256"]
            ):
                raise Pilot3MetR2Error("metadata terminal does not close its durable start")
            raw_path = event.get("raw_metadata_path")
            raw_sha = event.get("raw_metadata_sha256")
            if raw_path is not None or raw_sha is not None:
                payload = _verify_cas_binding(
                    root,
                    recorded_path=raw_path,
                    recorded_sha256=raw_sha,
                    recorded_byte_count=event.get("response_byte_count"),
                    directory=DEFAULT_METADATA_RAW_DIR,
                    suffix="json",
                    label="metadata terminal",
                )
            else:
                payload = b""
            if event.get("outcome") == "success":
                if (
                    event.get("status_code") != 200
                    or event.get("final_url") != target["object_endpoint"]
                    or event.get("redirect_chain") != []
                    or event.get("content_type") != "application/json"
                    or raw_path is None
                    or event.get("error_type") is not None
                    or event.get("error_message") is not None
                ):
                    raise Pilot3MetR2Error("successful metadata terminal violates R2 transport")
                _, selected_url = _parse_metadata(target, payload)
                if event.get("primary_image_url") != selected_url:
                    raise Pilot3MetR2Error("metadata terminal changed the selected primaryImage")
            elif event.get("outcome") in {"protocol_rejected", "transport_error"}:
                if (
                    not isinstance(event.get("error_type"), str)
                    or not event.get("error_type")
                    or not isinstance(event.get("error_message"), str)
                    or not event.get("error_message")
                    or event.get("primary_image_url") is not None
                ):
                    raise Pilot3MetR2Error("failed metadata terminal is incomplete")
            else:
                raise Pilot3MetR2Error("metadata terminal has an unknown outcome")
    return events


def capture_official_metadata(
    root: Path,
    request: Request,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
) -> List[Dict[str, Any]]:
    """Capture the fixed metadata schedule under an exclusive one-shot lock."""

    root = Path(root).expanduser().resolve()
    with _r2_phase_lock(root, "metadata"):
        return _capture_official_metadata_locked(
            root,
            request,
            authorization_path=authorization_path,
            attempts_path=attempts_path,
        )


def _capture_official_metadata_locked(
    root: Path,
    request: Request,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
) -> List[Dict[str, Any]]:
    """Capture exactly twenty object records, with no retry or image request.

    Every start is durably appended before ``request`` is invoked.  Any dangling
    start or non-success terminal closes the run; R2 never guesses whether an
    unrecorded response was observed and never substitutes another work.
    """

    root = Path(root).expanduser().resolve()
    authorization = require_committed_authorization(
        root,
        authorization_path=authorization_path,
    )
    path = _resolve(root, attempts_path)
    events = _verify_metadata_events(
        root, authorization, attempts_path=attempts_path
    )
    if len(events) % 2:
        raise Pilot3MetR2Error("metadata journal has a dangling durable start; no retry allowed")
    terminals = events[1::2]
    if any(event.get("outcome") != "success" for event in terminals):
        raise Pilot3MetR2Error("metadata journal contains a terminal failure; cohort is closed")

    for target in authorization["targets"][len(terminals) :]:
        attempt_id = _metadata_attempt_id(
            str(authorization["authorization_sha256"]), str(target["r2_asset_id"])
        )
        start = _append_event(
            path,
            events,
            {
                "event_type": "metadata_request_start",
                "authorization_sha256": authorization["authorization_sha256"],
                "r2_asset_id": target["r2_asset_id"],
                "object_id": target["object_id"],
                "attempt_id": attempt_id,
                "request_method": "GET",
                "request_url": target["object_endpoint"],
                "request_accept": "application/json",
                "follow_redirects": False,
            },
            schema=METADATA_ATTEMPT_SCHEMA,
        )
        try:
            response = request(str(target["object_endpoint"]))
            if not isinstance(response, TransportResponse):
                raise Pilot3MetR2Error("metadata requester returned an unsupported response")
            if not isinstance(response.body, bytes) or len(response.body) > MAX_METADATA_BYTES:
                raise Pilot3MetR2Error("metadata response body is invalid or too large")
            evidence = _response_evidence(response)
            raw_path, raw_sha = _write_cas(
                root, DEFAULT_METADATA_RAW_DIR, response.body, "json"
            )
            error: Optional[Exception] = None
            selected_url: Optional[str] = None
            try:
                if response.status_code != 200:
                    raise Pilot3MetR2Error(
                        f"official metadata returned HTTP {response.status_code}"
                    )
                if response.final_url != target["object_endpoint"]:
                    raise Pilot3MetR2Error("official metadata final URL changed")
                if response.redirect_chain:
                    raise Pilot3MetR2Error("official metadata redirects are forbidden")
                _official_url(
                    response.final_url,
                    host=OFFICIAL_METADATA_HOST,
                    label="official metadata final URL",
                )
                if evidence["content_type"] != "application/json":
                    raise Pilot3MetR2Error("official metadata content type is not JSON")
                _, selected_url = _parse_metadata(target, response.body)
            except Exception as exc:  # terminal evidence is mandatory before propagation
                error = exc
            terminal = _append_event(
                path,
                events,
                {
                    "event_type": "metadata_request_terminal",
                    "authorization_sha256": authorization["authorization_sha256"],
                    "r2_asset_id": target["r2_asset_id"],
                    "object_id": target["object_id"],
                    "attempt_id": attempt_id,
                    "start_event_sha256": start["event_sha256"],
                    "outcome": "success" if error is None else "protocol_rejected",
                    "error_type": None if error is None else type(error).__name__,
                    "error_message": None if error is None else str(error),
                    "raw_metadata_path": raw_path,
                    "raw_metadata_sha256": raw_sha,
                    "primary_image_url": selected_url,
                    **evidence,
                },
                schema=METADATA_ATTEMPT_SCHEMA,
            )
            if error is not None:
                raise Pilot3MetR2Error(str(error)) from error
            terminals.append(terminal)
        except BaseException as exc:
            if len(events) % 2:
                _append_event(
                    path,
                    events,
                    {
                        "event_type": "metadata_request_terminal",
                        "authorization_sha256": authorization["authorization_sha256"],
                        "r2_asset_id": target["r2_asset_id"],
                        "object_id": target["object_id"],
                        "attempt_id": attempt_id,
                        "start_event_sha256": start["event_sha256"],
                        "outcome": "transport_error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "raw_metadata_path": None,
                        "raw_metadata_sha256": None,
                        "primary_image_url": None,
                        "status_code": None,
                        "content_type": None,
                        "content_length_header": None,
                        "final_url": None,
                        "redirect_chain": [],
                        "response_byte_count": None,
                    },
                    schema=METADATA_ATTEMPT_SCHEMA,
                )
            raise
    return _verify_metadata_events(root, authorization, attempts_path=attempts_path)[1::2]


def _target_rows_from_metadata(
    root: Path,
    authorization: Mapping[str, Any],
    *,
    attempts_path: Path,
) -> List[Dict[str, Any]]:
    events = _verify_metadata_events(
        root, authorization, attempts_path=attempts_path
    )
    if len(events) != 2 * len(authorization["targets"]):
        raise Pilot3MetR2Error("R2 metadata freeze requires all twenty terminals")
    terminals = events[1::2]
    if any(event.get("outcome") != "success" for event in terminals):
        raise Pilot3MetR2Error("R2 metadata freeze is all-20 atomic")
    rows: List[Dict[str, Any]] = []
    for target, terminal in zip(authorization["targets"], terminals):
        raw_path = _resolve(root, Path(str(terminal["raw_metadata_path"])))
        metadata, primary_image = _parse_metadata(target, raw_path.read_bytes())
        payload = {
            "schema_version": TARGET_ROW_SCHEMA,
            "record_type": "pilot3_met_r2_target_row",
            "namespace": NAMESPACE,
            "r2_asset_id": target["r2_asset_id"],
            "physical_work_id": target["physical_work_id"],
            "object_id": target["object_id"],
            "object_endpoint": target["object_endpoint"],
            "accession_number": target["accession_number"],
            "artist_id": target["artist_id"],
            "artist_name": target["artist_name"],
            "artist_constituent_id": target["artist_constituent_id"],
            "partition": target["partition"],
            "frozen_split_row_sha256": target["frozen_split_row_sha256"],
            "frozen_selection_sha256": target["frozen_selection_sha256"],
            "authorization_sha256": authorization["authorization_sha256"],
            "metadata_attempt_event_sha256": terminal["event_sha256"],
            "raw_metadata_path": terminal["raw_metadata_path"],
            "raw_metadata_sha256": terminal["raw_metadata_sha256"],
            "raw_metadata_object_sha256": stable_hash(metadata),
            "selected_image_field": SELECTED_IMAGE_FIELD,
            "primary_image_url": primary_image,
            "image_dimensions_at_freeze": None,
            "image_dimension_policy": "observe_first_response_without_derivative_switching",
            "fallback_allowed": False,
            "replacement_allowed": False,
        }
        rows.append(_self_hash(payload, "row_sha256"))
    primary_urls = [str(row["primary_image_url"]) for row in rows]
    if len(set(primary_urls)) != len(primary_urls):
        raise Pilot3MetR2Error(
            "official metadata maps multiple frozen works to one primaryImage URL"
        )
    return rows


def verify_target_manifest(
    root: Path,
    authorization: Mapping[str, Any],
    *,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
) -> List[Dict[str, Any]]:
    """Verify the exact deterministic all-20 metadata-derived image target set."""

    path = _resolve(root, target_manifest_path)
    if not path.is_file():
        raise Pilot3MetR2Error("R2 target manifest is absent")
    observed_raw = read_jsonl(path)
    if any(not isinstance(row, dict) for row in observed_raw):
        raise Pilot3MetR2Error("R2 target manifest contains a non-object row")
    observed = [dict(row) for row in observed_raw]
    expected = _target_rows_from_metadata(
        root, authorization, attempts_path=attempts_path
    )
    if observed != expected:
        raise Pilot3MetR2Error("R2 target manifest is stale or was not deterministically built")
    if hash_file(path) != _canonical_jsonl_sha256(expected):
        raise Pilot3MetR2Error("R2 target manifest is not canonical JSONL")
    for row in observed:
        _verify_self_hash(row, "row_sha256", label="R2 target row")
        _official_url(
            row.get("primary_image_url"),
            host=OFFICIAL_IMAGE_HOST,
            label="R2 target primary_image_url",
        )
        if (
            row.get("namespace") != NAMESPACE
            or row.get("selected_image_field") != SELECTED_IMAGE_FIELD
            or row.get("fallback_allowed") is not False
            or row.get("replacement_allowed") is not False
            or row.get("image_dimensions_at_freeze") is not None
        ):
            raise Pilot3MetR2Error("R2 target row weakens the official primaryImage policy")
    return observed


def _metadata_raw_bindings(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "path": str(row["raw_metadata_path"]),
            "file_sha256": str(row["raw_metadata_sha256"]),
        }
        for row in rows
    ]


def _metadata_freeze_payload(
    root: Path,
    authorization: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    *,
    authorization_path: Path,
    attempts_path: Path,
    target_manifest_path: Path,
) -> Dict[str, Any]:
    attempts = _resolve(root, attempts_path)
    manifest = _resolve(root, target_manifest_path)
    return {
        "schema_version": METADATA_FREEZE_SCHEMA,
        "record_type": "pilot3_met_r2_metadata_freeze",
        "namespace": NAMESPACE,
        "status": "all_20_metadata_eligible_image_requests_pending_commit_gate",
        "authorization_binding": {
            "path": str(authorization_path),
            "authorization_sha256": authorization["authorization_sha256"],
        },
        "metadata_attempt_binding": {
            "path": str(attempts_path),
            "file_sha256": hash_file(attempts),
            "event_count": 40,
            "terminal_count": 20,
        },
        "target_manifest_binding": {
            "path": str(target_manifest_path),
            "file_sha256": hash_file(manifest),
            "semantic_sha256": stable_hash(list(rows)),
            "row_count": 20,
        },
        "raw_metadata_bindings": _metadata_raw_bindings(rows),
        "selection_policy": {
            "field": SELECTED_IMAGE_FIELD,
            "provider_host": OFFICIAL_IMAGE_HOST,
            "forbidden_fields": list(FORBIDDEN_SELECTION_FIELDS),
            "fallback_allowed": False,
            "replacement_allowed": False,
        },
        "image_request_gate": (
            "authorization_metadata_journal_manifest_and_freeze_must_be_committed_"
            "and_clean_with_local_raw_metadata_hash_current"
        ),
    }


def freeze_metadata_targets(
    root: Path,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    freeze_path: Path = DEFAULT_METADATA_FREEZE,
) -> Dict[str, Any]:
    """Materialize the metadata-derived manifest and its self-hashed freeze.

    This function performs no network access.  Existing artifacts are accepted
    only when byte-semantic reconstruction is identical; they are never replaced.
    """

    root = Path(root).expanduser().resolve()
    authorization = load_authorization(root, authorization_path)
    rows = _target_rows_from_metadata(root, authorization, attempts_path=attempts_path)
    manifest = _resolve(root, target_manifest_path)
    if manifest.exists():
        if read_jsonl(manifest) != rows or hash_file(manifest) != _canonical_jsonl_sha256(rows):
            raise Pilot3MetR2Error("refusing to replace an existing R2 target manifest")
    else:
        write_jsonl(manifest, rows)
    payload = _metadata_freeze_payload(
        root,
        authorization,
        rows,
        authorization_path=authorization_path,
        attempts_path=attempts_path,
        target_manifest_path=target_manifest_path,
    )
    value = _self_hash(payload, "freeze_sha256")
    resolved_freeze = _resolve(root, freeze_path)
    if resolved_freeze.exists():
        if read_json(resolved_freeze) != value:
            raise Pilot3MetR2Error("refusing to replace an existing R2 metadata freeze")
    else:
        write_json(resolved_freeze, value)
    return value


def verify_metadata_freeze(
    root: Path,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    freeze_path: Path = DEFAULT_METADATA_FREEZE,
) -> Dict[str, Any]:
    root = Path(root).expanduser().resolve()
    authorization = load_authorization(root, authorization_path)
    rows = verify_target_manifest(
        root,
        authorization,
        attempts_path=attempts_path,
        target_manifest_path=target_manifest_path,
    )
    path = _resolve(root, freeze_path)
    if not path.is_file():
        raise Pilot3MetR2Error("R2 metadata freeze is absent")
    observed = read_json(path)
    if not isinstance(observed, dict) or observed.get("schema_version") != METADATA_FREEZE_SCHEMA:
        raise Pilot3MetR2Error("R2 metadata freeze has the wrong schema")
    _verify_self_hash(observed, "freeze_sha256", label="R2 metadata freeze")
    expected = _self_hash(
        _metadata_freeze_payload(
            root,
            authorization,
            rows,
            authorization_path=authorization_path,
            attempts_path=attempts_path,
            target_manifest_path=target_manifest_path,
        ),
        "freeze_sha256",
    )
    if observed != expected:
        raise Pilot3MetR2Error("R2 metadata freeze differs from deterministic reconstruction")
    return observed


def require_committed_metadata_freeze(
    root: Path,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    freeze_path: Path = DEFAULT_METADATA_FREEZE,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """Open the image-request gate only for a committed, byte-current closure."""

    root = Path(root).expanduser().resolve()
    authorization = load_authorization(root, authorization_path)
    freeze = verify_metadata_freeze(
        root,
        authorization_path=authorization_path,
        attempts_path=attempts_path,
        target_manifest_path=target_manifest_path,
        freeze_path=freeze_path,
    )
    targets = verify_target_manifest(
        root,
        authorization,
        attempts_path=attempts_path,
        target_manifest_path=target_manifest_path,
    )
    paths = [
        str(DEFAULT_INCIDENT),
        str(DEFAULT_SPLITS),
        str(authorization_path),
        str(attempts_path),
        str(target_manifest_path),
        str(freeze_path),
        *(binding["path"] for binding in authorization["implementation_bindings"]),
    ]
    _require_committed_paths(root, paths)
    return authorization, targets, freeze


def _image_attempt_id(freeze_sha256: str, asset_id: str) -> str:
    return "met-r2-image-" + stable_hash(
        {"freeze_sha256": freeze_sha256, "r2_asset_id": asset_id}
    )[:24]


def _decode_first_image_response(payload: bytes) -> Dict[str, Any]:
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            width, height = image.size
            decoded_format = str(image.format or "").upper()
            decoded_mode = str(image.mode)
    except Exception as exc:
        raise Pilot3MetR2Error("official primaryImage response cannot be decoded") from exc
    checks = {
        "decoded_format_is_jpeg": decoded_format == "JPEG",
        "width_strictly_greater_than_410": width > 410,
        "height_strictly_greater_than_410": height > 410,
        "long_short_aspect_strictly_below_2": max(width, height) / min(width, height) < 2,
        "released_code_area_predicate": width * height > 410 * 410,
    }
    if not all(checks.values()):
        raise Pilot3MetR2Error(
            "official primaryImage first response is outside the unchanged Kim intersection: "
            + canonical_json(checks)
        )
    return {
        "decoded_width": width,
        "decoded_height": height,
        "decoded_format": decoded_format,
        "decoded_mode": decoded_mode,
        "domain_checks": checks,
        "dimension_observation": "first_response_no_derivative_switching",
    }


def _verify_image_events(
    root: Path,
    authorization: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    freeze: Mapping[str, Any],
    *,
    attempts_path: Path,
) -> List[Dict[str, Any]]:
    path = _resolve(root, attempts_path)
    events = _verify_event_chain(
        path,
        schema=IMAGE_ATTEMPT_SCHEMA,
        allowed_event_types=("image_request_start", "image_request_terminal"),
    )
    if len(events) > 2 * len(targets):
        raise Pilot3MetR2Error("image journal exceeds the exact twenty-request schedule")
    for index, event in enumerate(events):
        target = targets[index // 2]
        common_fields = {
            "schema_version",
            "namespace",
            "event_index",
            "previous_event_sha256",
            "event_sha256",
            "event_type",
            "authorization_sha256",
            "metadata_freeze_sha256",
            "target_row_sha256",
            "r2_asset_id",
            "attempt_id",
        }
        start_fields = common_fields | {
            "request_method",
            "request_url",
            "request_accept",
            "follow_redirects",
            "fallback_allowed",
        }
        terminal_fields = common_fields | {
            "start_event_sha256",
            "outcome",
            "error_type",
            "error_message",
            "raw_image_path",
            "raw_image_sha256",
            "status_code",
            "content_type",
            "content_length_header",
            "final_url",
            "redirect_chain",
            "response_byte_count",
        }
        expected_id = _image_attempt_id(
            str(freeze["freeze_sha256"]), str(target["r2_asset_id"])
        )
        if (
            event.get("authorization_sha256") != authorization["authorization_sha256"]
            or event.get("metadata_freeze_sha256") != freeze["freeze_sha256"]
            or event.get("target_row_sha256") != target["row_sha256"]
            or event.get("r2_asset_id") != target["r2_asset_id"]
            or event.get("attempt_id") != expected_id
        ):
            raise Pilot3MetR2Error("image journal target binding changed")
        if index % 2 == 0:
            if (
                set(event) != start_fields
                or
                event.get("event_type") != "image_request_start"
                or event.get("request_method") != "GET"
                or event.get("request_url") != target["primary_image_url"]
                or event.get("request_accept") != "image/jpeg"
                or event.get("follow_redirects") is not False
                or event.get("fallback_allowed") is not False
            ):
                raise Pilot3MetR2Error("image request start is not the exact primaryImage URL")
        else:
            start = events[index - 1]
            expected_terminal_fields = terminal_fields
            if event.get("outcome") == "success":
                expected_terminal_fields = terminal_fields | {
                    "decoded_width",
                    "decoded_height",
                    "decoded_format",
                    "decoded_mode",
                    "domain_checks",
                    "dimension_observation",
                }
            if (
                set(event) != expected_terminal_fields
                or
                event.get("event_type") != "image_request_terminal"
                or event.get("start_event_sha256") != start["event_sha256"]
            ):
                raise Pilot3MetR2Error("image terminal does not close its durable start")
            raw_path = event.get("raw_image_path")
            raw_sha = event.get("raw_image_sha256")
            if raw_path is not None or raw_sha is not None:
                payload = _verify_cas_binding(
                    root,
                    recorded_path=raw_path,
                    recorded_sha256=raw_sha,
                    recorded_byte_count=event.get("response_byte_count"),
                    directory=DEFAULT_IMAGE_RAW_DIR,
                    suffix="bin",
                    label="image terminal",
                )
            else:
                payload = b""
            if event.get("outcome") == "success":
                if (
                    event.get("status_code") != 200
                    or event.get("content_type") != "image/jpeg"
                    or event.get("final_url") != target["primary_image_url"]
                    or event.get("redirect_chain") != []
                    or raw_path is None
                    or event.get("error_type") is not None
                    or event.get("error_message") is not None
                ):
                    raise Pilot3MetR2Error("successful image terminal violates R2 transport")
                observed = _decode_first_image_response(payload)
                for key, value in observed.items():
                    if event.get(key) != value:
                        raise Pilot3MetR2Error("image terminal geometry evidence changed")
            elif event.get("outcome") in {"protocol_rejected", "transport_error"}:
                if (
                    not isinstance(event.get("error_type"), str)
                    or not event.get("error_type")
                    or not isinstance(event.get("error_message"), str)
                    or not event.get("error_message")
                ):
                    raise Pilot3MetR2Error("failed image terminal is incomplete")
            else:
                raise Pilot3MetR2Error("image terminal has an unknown outcome")
    return events


def _image_acquisition_rows(
    authorization: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    freeze: Mapping[str, Any],
    terminals: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    raw_hashes = [str(terminal["raw_image_sha256"]) for terminal in terminals]
    if len(set(raw_hashes)) != len(raw_hashes):
        raise Pilot3MetR2Error(
            "official primaryImage responses duplicate bytes across frozen works"
        )
    observations: List[Dict[str, Any]] = []
    for target, terminal in zip(targets, terminals):
        observations.append(
            {
                "r2_asset_id": target["r2_asset_id"],
                "target_row_sha256": target["row_sha256"],
                "image_terminal_event_sha256": terminal["event_sha256"],
                "raw_image_sha256": terminal["raw_image_sha256"],
                "decoded_width": terminal["decoded_width"],
                "decoded_height": terminal["decoded_height"],
            }
        )
    cohort_sha256 = stable_hash(observations)
    rows: List[Dict[str, Any]] = []
    for target, terminal in zip(targets, terminals):
        payload = {
            "schema_version": IMAGE_ACQUISITION_SCHEMA,
            "record_type": "pilot3_met_r2_image_acquisition",
            "namespace": NAMESPACE,
            "cohort_eligibility": "eligible_only_as_complete_20_asset_cohort",
            "cohort_observation_sha256": cohort_sha256,
            "authorization_sha256": authorization["authorization_sha256"],
            "metadata_freeze_sha256": freeze["freeze_sha256"],
            "r2_asset_id": target["r2_asset_id"],
            "physical_work_id": target["physical_work_id"],
            "object_id": target["object_id"],
            "artist_id": target["artist_id"],
            "partition": target["partition"],
            "target_row_sha256": target["row_sha256"],
            "primary_image_url": target["primary_image_url"],
            "image_terminal_event_sha256": terminal["event_sha256"],
            "raw_image_path": terminal["raw_image_path"],
            "raw_image_sha256": terminal["raw_image_sha256"],
            "raw_image_byte_count": terminal["response_byte_count"],
            "decoded_width": terminal["decoded_width"],
            "decoded_height": terminal["decoded_height"],
            "decoded_format": terminal["decoded_format"],
            "decoded_mode": terminal["decoded_mode"],
            "domain_checks": terminal["domain_checks"],
            "dimension_observation": terminal["dimension_observation"],
        }
        rows.append(_self_hash(payload, "record_sha256"))
    return rows


def verify_image_acquisitions(
    root: Path,
    authorization: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    freeze: Mapping[str, Any],
    *,
    attempts_path: Path = DEFAULT_IMAGE_ATTEMPTS,
    acquisitions_path: Path = DEFAULT_IMAGE_ACQUISITIONS,
) -> List[Dict[str, Any]]:
    events = _verify_image_events(
        root,
        authorization,
        targets,
        freeze,
        attempts_path=attempts_path,
    )
    if len(events) != 2 * len(targets):
        raise Pilot3MetR2Error("R2 image acquisitions require all twenty terminals")
    terminals = events[1::2]
    if any(event.get("outcome") != "success" for event in terminals):
        raise Pilot3MetR2Error("R2 image eligibility is all-20 atomic")
    expected = _image_acquisition_rows(authorization, targets, freeze, terminals)
    path = _resolve(root, acquisitions_path)
    if not path.is_file():
        raise Pilot3MetR2Error("R2 atomic image acquisition manifest is absent")
    observed_raw = read_jsonl(path)
    if any(not isinstance(row, dict) for row in observed_raw):
        raise Pilot3MetR2Error("R2 image acquisition manifest contains a non-object row")
    observed = [dict(row) for row in observed_raw]
    if observed != expected or hash_file(path) != _canonical_jsonl_sha256(expected):
        raise Pilot3MetR2Error("R2 image acquisition manifest is stale or non-canonical")
    for row in observed:
        _verify_self_hash(row, "record_sha256", label="R2 image acquisition")
    return observed


def require_committed_image_acquisitions(
    root: Path,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    metadata_attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    metadata_freeze_path: Path = DEFAULT_METADATA_FREEZE,
    image_attempts_path: Path = DEFAULT_IMAGE_ATTEMPTS,
    acquisitions_path: Path = DEFAULT_IMAGE_ACQUISITIONS,
) -> Tuple[
    Dict[str, Any],
    List[Dict[str, Any]],
    Dict[str, Any],
    List[Dict[str, Any]],
]:
    """Require the complete official-image cohort and its compact evidence committed."""

    root = Path(root).expanduser().resolve()
    authorization, targets, freeze = require_committed_metadata_freeze(
        root,
        authorization_path=authorization_path,
        attempts_path=metadata_attempts_path,
        target_manifest_path=target_manifest_path,
        freeze_path=metadata_freeze_path,
    )
    _require_committed_normalization_scope_for_images(
        root, authorization, targets, freeze
    )
    acquisitions = verify_image_acquisitions(
        root,
        authorization,
        targets,
        freeze,
        attempts_path=image_attempts_path,
        acquisitions_path=acquisitions_path,
    )
    _require_committed_paths(
        root,
        [str(image_attempts_path), str(acquisitions_path)],
    )
    return authorization, targets, freeze, acquisitions


def _require_committed_normalization_scope_for_images(
    root: Path,
    authorization: Mapping[str, Any],
    targets: Sequence[Mapping[str, Any]],
    freeze: Mapping[str, Any],
) -> Dict[str, Any]:
    """Require the prospective exact-member normalizer before opening image bytes."""

    # Imported lazily because the scope builder itself verifies this module's
    # metadata freeze.  Image acquisition occurs only after that offline cycle.
    from latent_art_bench.pilot3.normalization_scope import (
        require_committed_normalization_scope_authorization,
    )

    scope = require_committed_normalization_scope_authorization(root)
    eligible = scope.get("eligible_membership")
    met_scope = eligible.get("met_r2") if isinstance(eligible, Mapping) else None
    expected_members = [
        {
            "r2_asset_id": target["r2_asset_id"],
            "physical_work_id": target["physical_work_id"],
            "object_id": target["object_id"],
            "artist_id": target["artist_id"],
            "partition": target["partition"],
            "primary_image_url": target["primary_image_url"],
            "target_row_sha256": target["row_sha256"],
        }
        for target in targets
    ]
    expected_members.sort(key=lambda row: int(str(row["object_id"])))
    if (
        not isinstance(met_scope, Mapping)
        or met_scope.get("count") != 20
        or met_scope.get("authorization_sha256")
        != authorization.get("authorization_sha256")
        or met_scope.get("metadata_freeze_sha256") != freeze.get("freeze_sha256")
        or met_scope.get("selected_image_field") != SELECTED_IMAGE_FIELD
        or met_scope.get("members") != expected_members
    ):
        raise Pilot3MetR2Error(
            "committed normalization scope does not bind the exact R2 image cohort"
        )
    return scope


def acquire_official_images(
    root: Path,
    request: Request,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    metadata_attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    metadata_freeze_path: Path = DEFAULT_METADATA_FREEZE,
    image_attempts_path: Path = DEFAULT_IMAGE_ATTEMPTS,
    acquisitions_path: Path = DEFAULT_IMAGE_ACQUISITIONS,
) -> List[Dict[str, Any]]:
    """Acquire the fixed image schedule under an exclusive one-shot lock."""

    root = Path(root).expanduser().resolve()
    with _r2_phase_lock(root, "image"):
        return _acquire_official_images_locked(
            root,
            request,
            authorization_path=authorization_path,
            metadata_attempts_path=metadata_attempts_path,
            target_manifest_path=target_manifest_path,
            metadata_freeze_path=metadata_freeze_path,
            image_attempts_path=image_attempts_path,
            acquisitions_path=acquisitions_path,
        )


def _acquire_official_images_locked(
    root: Path,
    request: Request,
    *,
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    metadata_attempts_path: Path = DEFAULT_METADATA_ATTEMPTS,
    target_manifest_path: Path = DEFAULT_TARGET_MANIFEST,
    metadata_freeze_path: Path = DEFAULT_METADATA_FREEZE,
    image_attempts_path: Path = DEFAULT_IMAGE_ATTEMPTS,
    acquisitions_path: Path = DEFAULT_IMAGE_ACQUISITIONS,
) -> List[Dict[str, Any]]:
    """Request each committed ``primaryImage`` once and atomically admit all twenty."""

    root = Path(root).expanduser().resolve()
    authorization, targets, freeze = require_committed_metadata_freeze(
        root,
        authorization_path=authorization_path,
        attempts_path=metadata_attempts_path,
        target_manifest_path=target_manifest_path,
        freeze_path=metadata_freeze_path,
    )
    _require_committed_normalization_scope_for_images(
        root, authorization, targets, freeze
    )
    path = _resolve(root, image_attempts_path)
    events = _verify_image_events(
        root,
        authorization,
        targets,
        freeze,
        attempts_path=image_attempts_path,
    )
    if len(events) % 2:
        raise Pilot3MetR2Error("image journal has a dangling durable start; no retry allowed")
    terminals = events[1::2]
    if any(event.get("outcome") != "success" for event in terminals):
        raise Pilot3MetR2Error("image journal contains a terminal failure; cohort is closed")
    existing_manifest = _resolve(root, acquisitions_path)
    if existing_manifest.exists():
        return verify_image_acquisitions(
            root,
            authorization,
            targets,
            freeze,
            attempts_path=image_attempts_path,
            acquisitions_path=acquisitions_path,
        )

    for target in targets[len(terminals) :]:
        image_url = _official_url(
            target["primary_image_url"],
            host=OFFICIAL_IMAGE_HOST,
            label="committed R2 primaryImage",
        )
        attempt_id = _image_attempt_id(
            str(freeze["freeze_sha256"]), str(target["r2_asset_id"])
        )
        start = _append_event(
            path,
            events,
            {
                "event_type": "image_request_start",
                "authorization_sha256": authorization["authorization_sha256"],
                "metadata_freeze_sha256": freeze["freeze_sha256"],
                "target_row_sha256": target["row_sha256"],
                "r2_asset_id": target["r2_asset_id"],
                "attempt_id": attempt_id,
                "request_method": "GET",
                "request_url": image_url,
                "request_accept": "image/jpeg",
                "follow_redirects": False,
                "fallback_allowed": False,
            },
            schema=IMAGE_ATTEMPT_SCHEMA,
        )
        try:
            response = request(image_url)
            if not isinstance(response, TransportResponse):
                raise Pilot3MetR2Error("image requester returned an unsupported response")
            if not isinstance(response.body, bytes) or len(response.body) > MAX_IMAGE_BYTES:
                raise Pilot3MetR2Error("image response body is invalid or too large")
            evidence = _response_evidence(response)
            raw_path, raw_sha = _write_cas(root, DEFAULT_IMAGE_RAW_DIR, response.body, "bin")
            error: Optional[Exception] = None
            decoded: Dict[str, Any] = {}
            try:
                if response.status_code != 200:
                    raise Pilot3MetR2Error(
                        f"official primaryImage returned HTTP {response.status_code}"
                    )
                if response.final_url != image_url:
                    final_host = urlsplit(response.final_url).hostname
                    if final_host is None or final_host.casefold() != OFFICIAL_IMAGE_HOST:
                        raise Pilot3MetR2Error("cross-provider image redirect is forbidden")
                    raise Pilot3MetR2Error("any image redirect or final-URL change is forbidden")
                if response.redirect_chain:
                    redirect_hosts = {
                        (urlsplit(url).hostname or "").casefold()
                        for url in response.redirect_chain
                    }
                    if redirect_hosts - {OFFICIAL_IMAGE_HOST}:
                        raise Pilot3MetR2Error("cross-provider image redirect is forbidden")
                    raise Pilot3MetR2Error("image redirects are forbidden")
                _official_url(
                    response.final_url,
                    host=OFFICIAL_IMAGE_HOST,
                    label="official image final URL",
                )
                if evidence["content_type"] != "image/jpeg":
                    raise Pilot3MetR2Error("official primaryImage content type is not JPEG")
                decoded = _decode_first_image_response(response.body)
            except Exception as exc:  # terminal evidence is mandatory before propagation
                error = exc
            terminal = _append_event(
                path,
                events,
                {
                    "event_type": "image_request_terminal",
                    "authorization_sha256": authorization["authorization_sha256"],
                    "metadata_freeze_sha256": freeze["freeze_sha256"],
                    "target_row_sha256": target["row_sha256"],
                    "r2_asset_id": target["r2_asset_id"],
                    "attempt_id": attempt_id,
                    "start_event_sha256": start["event_sha256"],
                    "outcome": "success" if error is None else "protocol_rejected",
                    "error_type": None if error is None else type(error).__name__,
                    "error_message": None if error is None else str(error),
                    "raw_image_path": raw_path,
                    "raw_image_sha256": raw_sha,
                    **evidence,
                    **decoded,
                },
                schema=IMAGE_ATTEMPT_SCHEMA,
            )
            if error is not None:
                raise Pilot3MetR2Error(str(error)) from error
            terminals.append(terminal)
        except BaseException as exc:
            if len(events) % 2:
                _append_event(
                    path,
                    events,
                    {
                        "event_type": "image_request_terminal",
                        "authorization_sha256": authorization["authorization_sha256"],
                        "metadata_freeze_sha256": freeze["freeze_sha256"],
                        "target_row_sha256": target["row_sha256"],
                        "r2_asset_id": target["r2_asset_id"],
                        "attempt_id": attempt_id,
                        "start_event_sha256": start["event_sha256"],
                        "outcome": "transport_error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "raw_image_path": None,
                        "raw_image_sha256": None,
                        "status_code": None,
                        "content_type": None,
                        "content_length_header": None,
                        "final_url": None,
                        "redirect_chain": [],
                        "response_byte_count": None,
                    },
                    schema=IMAGE_ATTEMPT_SCHEMA,
                )
            raise

    verified_events = _verify_image_events(
        root,
        authorization,
        targets,
        freeze,
        attempts_path=image_attempts_path,
    )
    terminals = verified_events[1::2]
    if len(terminals) != 20 or any(row.get("outcome") != "success" for row in terminals):
        raise Pilot3MetR2Error("R2 refuses partial image eligibility")
    rows = _image_acquisition_rows(authorization, targets, freeze, terminals)
    if existing_manifest.exists():
        raise Pilot3MetR2Error("R2 image manifest appeared during acquisition")
    write_jsonl(existing_manifest, rows)
    return verify_image_acquisitions(
        root,
        authorization,
        targets,
        freeze,
        attempts_path=image_attempts_path,
        acquisitions_path=acquisitions_path,
    )
