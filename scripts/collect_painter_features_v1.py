#!/usr/bin/env python3
"""One-shot, fail-closed acquisition for a reviewed Painter Features v1 freeze."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageCms, UnidentifiedImageError

ALLOWED_HOST = "api.nga.gov"
ALLOWED_MIME = "image/jpeg"
MAX_BYTES = 25 * 1024 * 1024
MIN_SHORT_EDGE = 512
REQUEST_DELAY_SECONDS = 1.0


class FrozenFailure(Exception):
    """A terminal failure with a prospectively named outcome code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(row)
    return rows


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_chain(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = read_jsonl(path)
    previous: str | None = None
    for number, row in enumerate(rows, 1):
        observed = row.get("event_sha256")
        payload = dict(row)
        payload.pop("event_sha256", None)
        expected = sha256_bytes(canonical_json(payload).encode("utf-8"))
        if observed != expected:
            raise ValueError(f"{path}:{number} has an invalid event hash")
        if row.get("previous_event_sha256") != previous:
            raise ValueError(f"{path}:{number} breaks the event chain")
        previous = str(observed)
    return rows


def append_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = validate_chain(path)
    previous = str(rows[-1]["event_sha256"]) if rows else None
    payload = dict(event)
    payload["previous_event_sha256"] = previous
    payload["event_sha256"] = sha256_bytes(canonical_json(payload).encode("utf-8"))
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    with os.fdopen(descriptor, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(payload) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return payload


def inspect_jpeg(content: bytes) -> dict[str, Any]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.load()
            if image.format != "JPEG":
                raise FrozenFailure(
                    "codec_failure", f"decoded format is {image.format!r}, expected JPEG"
                )
            width, height = image.size
            if min(width, height) < MIN_SHORT_EDGE:
                raise FrozenFailure(
                    "dimension_failure",
                    f"short edge {min(width, height)} is below {MIN_SHORT_EDGE}",
                )
            icc = image.info.get("icc_profile")
            icc_name: str | None = None
            if isinstance(icc, bytes):
                try:
                    icc_name = ImageCms.getProfileName(io.BytesIO(icc)).strip() or None
                except (OSError, ValueError):
                    icc_name = None
            exif = image.getexif()
            xmp = image.info.get("xmp") or image.info.get("XML:com.adobe.xmp")
            return {
                "decoded_format": image.format,
                "decoded_mode": image.mode,
                "decoded_width": width,
                "decoded_height": height,
                "decoded_bit_depth_per_channel": 8,
                "declared_color_space": image.mode,
                "alpha_present": "A" in image.getbands(),
                "icc_profile_present": isinstance(icc, bytes),
                "icc_profile_sha256": sha256_bytes(icc) if isinstance(icc, bytes) else None,
                "icc_profile_name": icc_name,
                "exif_present": bool(exif),
                "exif_orientation": exif.get(274) if exif else None,
                "xmp_present": xmp is not None,
            }
    except FrozenFailure:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        raise FrozenFailure("decode_failure", f"JPEG decode failed: {exc}") from exc


def write_content_addressed(workspace: Path, content: bytes, digest: str) -> Path:
    destination = workspace / "raw" / digest[:2] / f"{digest}.jpg"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(destination) != digest:
            raise FrozenFailure(
                "artifact_storage_failure",
                f"existing content-addressed path has wrong bytes: {destination}",
            )
        return destination
    incoming = workspace / "incoming"
    incoming.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix="pf1-", suffix=".part", dir=incoming)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def require_hash(root: Path, relative_path: str, expected: str, label: str) -> None:
    observed = sha256_file(root / relative_path)
    if observed != expected:
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, observed {observed}")


def validate_freeze(root: Path, seal_path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256_file(seal_path)
    if actual != expected_sha256:
        raise ValueError(f"seal SHA-256 mismatch: expected {expected_sha256}, observed {actual}")
    seal = read_json(seal_path)
    if seal.get("status") != "reviewed_and_sealed_for_collection":
        raise ValueError("authorization seal is not reviewed_and_sealed_for_collection")
    require_hash(root, str(seal["design_freeze_path"]), seal["design_freeze_sha256"], "freeze")
    require_hash(root, str(seal["review_record_path"]), seal["review_record_sha256"], "review")
    review = read_json(root / str(seal["review_record_path"]))
    if review.get("decision") != "APPROVE":
        raise ValueError("independent review did not approve collection")
    if review.get("reviewed_design_sha256") != seal["design_freeze_sha256"]:
        raise ValueError("review does not name the sealed design hash")
    if review.get("approved_scope") != seal.get("authorization_scope"):
        raise ValueError("review and seal authorize different scopes")

    freeze = read_json(root / str(seal["design_freeze_path"]))
    if freeze.get("status") != "sealed_for_independent_review":
        raise ValueError("design freeze is not sealed_for_independent_review")
    if freeze.get("freeze_id") != seal.get("freeze_id"):
        raise ValueError("seal and design freeze IDs differ")
    scope = freeze.get("scope", {})
    if scope.get("acquisition_only") is not True or any(
        scope.get(key) is not False
        for key in (
            "feature_extraction",
            "normalization",
            "human_data",
            "external_access",
            "generated_images",
        )
    ):
        raise ValueError("freeze scope is not strictly acquisition-only")

    require_hash(root, freeze["protocol_path"], freeze["protocol_sha256"], "protocol")
    require_hash(
        root,
        freeze["collection_frame_path"],
        freeze["collection_frame_sha256"],
        "collection frame",
    )
    for item in freeze["historical_inputs"]:
        require_hash(root, item["path"], item["sha256"], f"historical input {item['path']}")

    runtime = freeze["checklist"]["09_runtime_and_fixtures"]
    require_hash(root, runtime["collector_path"], runtime["collector_sha256"], "collector")
    require_hash(root, "pyproject.toml", runtime["pyproject_sha256"], "pyproject")
    require_hash(root, "uv.lock", runtime["uv_lock_sha256"], "uv lock")
    development = freeze["checklist"]["06_partitions"]["development"]
    require_hash(root, development["path"], development["sha256"], "development references")
    simulation = freeze["checklist"]["11_simulation_and_minimum_counts"]
    require_hash(root, simulation["simulation_path"], simulation["simulation_sha256"], "simulation")
    if platform.python_version() != runtime["python"]:
        raise ValueError("Python version differs from the freeze")
    if version("httpx") != runtime["httpx"] or version("pillow") != runtime["pillow"]:
        raise ValueError("httpx or Pillow version differs from the freeze")
    if Path(__file__).resolve() != (root / runtime["collector_path"]).resolve():
        raise ValueError("running collector path differs from the frozen collector path")

    rows = read_jsonl(root / freeze["collection_frame_path"])
    expected_count = freeze["checklist"]["03_work_frame_rights_and_acquisition"][
        "exact_work_count"
    ]
    if len(rows) != expected_count:
        raise ValueError("collection-frame row count differs from the freeze")
    if [row.get("acquisition_sequence") for row in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("collection-frame sequence is not exact and contiguous")
    for field in ("frame_row_id", "physical_work_id", "derivative_family_id", "asset_url"):
        values = [str(row.get(field)) for row in rows]
        if len(values) != len(set(values)) or "None" in values:
            raise ValueError(f"collection-frame field {field} is missing or duplicated")
    for row in rows:
        parsed = urlparse(str(row["asset_url"]))
        if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
            raise ValueError(f"unfrozen host or scheme in frame: {row['asset_url']}")
        if row.get("asset_license") != "CC0":
            raise ValueError("collection frame contains a non-CC0 asset")

    freeze["authorization_seal_sha256"] = expected_sha256
    freeze["design_freeze_sha256"] = seal["design_freeze_sha256"]
    return freeze


def validate_existing_ledgers(
    intent_path: Path,
    attempt_path: Path,
    acquired_path: Path,
    frame_ids: set[str],
    seal_sha256: str,
    freeze_sha256: str,
) -> bool:
    intents = validate_chain(intent_path)
    terminals = validate_chain(attempt_path)
    acquired = validate_chain(acquired_path)
    ledger_rows = (
        (intent_path, intents),
        (attempt_path, terminals),
        (acquired_path, acquired),
    )
    for path, rows in ledger_rows:
        for row in rows:
            if row.get("authorization_seal_sha256") != seal_sha256:
                raise ValueError(f"{path} contains an event from another seal")
            if row.get("design_freeze_sha256") != freeze_sha256:
                raise ValueError(f"{path} contains an event from another freeze")
            if str(row.get("frame_row_id")) not in frame_ids:
                raise ValueError(f"{path} contains a row outside the frozen frame")

    def unique_map(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for row in rows:
            row_id = str(row["frame_row_id"])
            if row_id in result:
                raise ValueError(f"duplicate {label} for {row_id}")
            result[row_id] = row
        return result

    intent_by_id = unique_map(intents, "intent")
    terminal_by_id = unique_map(terminals, "terminal")
    acquired_by_id = unique_map(acquired, "acquired record")
    if set(intent_by_id) - set(terminal_by_id):
        raise RuntimeError("dangling intent exists; the one-shot batch cannot resend")
    for row_id, row in acquired_by_id.items():
        terminal = terminal_by_id.get(row_id)
        if terminal is None or terminal.get("state") != "admitted":
            raise ValueError(f"acquired row {row_id} lacks an admitted terminal")
        if row.get("terminal_event_sha256") != terminal.get("event_sha256"):
            raise ValueError(f"acquired row {row_id} does not bind its terminal")
        if row.get("raw_sha256") != terminal.get("raw_sha256"):
            raise ValueError(f"acquired row {row_id} and terminal disagree on bytes")

    if not intents and not terminals and not acquired:
        return False
    if set(terminal_by_id) == frame_ids and set(acquired_by_id) == frame_ids and all(
        row.get("state") == "admitted" for row in terminal_by_id.values()
    ):
        return True
    raise RuntimeError("partial or failed ledger exists; the one-shot batch cannot resume")


def terminal_event(
    *,
    row_id: str,
    state: str,
    outcome_code: str,
    started_at: str | None,
    seal_sha256: str,
    freeze_sha256: str,
    reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "record_type": "pf1_acquisition_terminal",
        "schema_version": "2.0",
        "frame_row_id": row_id,
        "state": state,
        "outcome_code": outcome_code,
        "started_at": started_at,
        "recorded_at": utc_now(),
        "authorization_seal_sha256": seal_sha256,
        "design_freeze_sha256": freeze_sha256,
        "reason": reason,
    }
    if extra:
        event.update(extra)
    return event


def collect(root: Path, seal_path: Path, seal_sha256: str) -> int:
    freeze = validate_freeze(root, seal_path, seal_sha256)
    rows = read_jsonl(root / str(freeze["collection_frame_path"]))
    workspace = root / str(freeze["workspace_root"])
    manifest_root = root / "data/manifests/painter_features_v1"
    intent_path = manifest_root / "acquisition_intents.jsonl"
    attempt_path = manifest_root / "acquisition_attempts.jsonl"
    acquired_path = manifest_root / "acquired_files.jsonl"
    frame_ids = {str(row["frame_row_id"]) for row in rows}
    freeze_sha256 = str(freeze["design_freeze_sha256"])
    if validate_existing_ledgers(
        intent_path, attempt_path, acquired_path, frame_ids, seal_sha256, freeze_sha256
    ):
        print("all frozen rows are already admitted; no requests sent")
        return 0

    stop_reason: str | None = None
    with httpx.Client(follow_redirects=False, timeout=30.0, trust_env=False) as client:
        for index, row in enumerate(rows):
            row_id = str(row["frame_row_id"])
            if stop_reason is not None:
                append_event(
                    attempt_path,
                    terminal_event(
                        row_id=row_id,
                        state="not_attempted_after_global_stop",
                        outcome_code="global_stop",
                        started_at=None,
                        seal_sha256=seal_sha256,
                        freeze_sha256=freeze_sha256,
                        reason=stop_reason,
                    ),
                )
                continue

            url = str(row["asset_url"])
            request_headers = {
                "Accept": ALLOWED_MIME,
                "Accept-Encoding": "identity",
                "User-Agent": "LatentArtBench-PainterFeaturesV1/collection-freeze-2",
            }
            append_event(
                intent_path,
                {
                    "record_type": "pf1_acquisition_intent",
                    "schema_version": "2.0",
                    "frame_row_id": row_id,
                    "acquisition_sequence": row["acquisition_sequence"],
                    "method": "GET",
                    "asset_url": url,
                    "request_headers": request_headers,
                    "attempt_index": 0,
                    "retry_allowed": False,
                    "recorded_at": utc_now(),
                    "authorization_seal_sha256": seal_sha256,
                    "design_freeze_sha256": freeze_sha256,
                },
            )
            started = utc_now()
            terminal_written = False
            try:
                try:
                    response = client.get(url, headers=request_headers)
                except httpx.TimeoutException as exc:
                    raise FrozenFailure("transport_timeout", str(exc)) from exc
                except httpx.TransportError as exc:
                    raise FrozenFailure("transport_failure", str(exc)) from exc
                if 300 <= response.status_code < 400:
                    raise FrozenFailure("redirect_failure", f"HTTP status {response.status_code}")
                if response.status_code != 200:
                    raise FrozenFailure(
                        "http_status_failure", f"HTTP status {response.status_code}"
                    )
                content_encoding = response.headers.get("content-encoding")
                if content_encoding not in (None, "", "identity"):
                    raise FrozenFailure(
                        "content_encoding_failure",
                        f"unexpected Content-Encoding {content_encoding!r}",
                    )
                content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                if content_type != ALLOWED_MIME:
                    raise FrozenFailure(
                        "mime_failure", f"content type {content_type!r}, expected {ALLOWED_MIME!r}"
                    )
                if not response.content:
                    raise FrozenFailure("byte_count_failure", "empty response body")
                if len(response.content) > MAX_BYTES:
                    raise FrozenFailure(
                        "byte_limit_failure", f"response exceeds byte limit {MAX_BYTES}"
                    )
                decoded = inspect_jpeg(response.content)
                digest = sha256_bytes(response.content)
                try:
                    raw_path = write_content_addressed(workspace, response.content, digest)
                except FrozenFailure:
                    raise
                except OSError as exc:
                    raise FrozenFailure("artifact_storage_failure", str(exc)) from exc
                response_metadata = {
                    "status_code": response.status_code,
                    "response_headers": {
                        key: response.headers.get(key)
                        for key in (
                            "content-type",
                            "content-length",
                            "content-encoding",
                            "etag",
                            "last-modified",
                            "cache-control",
                        )
                    },
                    "byte_count": len(response.content),
                    "raw_sha256": digest,
                    "raw_path": str(raw_path.relative_to(root)),
                    **decoded,
                }
                terminal = append_event(
                    attempt_path,
                    terminal_event(
                        row_id=row_id,
                        state="admitted",
                        outcome_code="admitted",
                        started_at=started,
                        seal_sha256=seal_sha256,
                        freeze_sha256=freeze_sha256,
                        extra=response_metadata,
                    ),
                )
                terminal_written = True
                append_event(
                    acquired_path,
                    {
                        "record_type": "pf1_acquired_file",
                        "schema_version": "2.0",
                        "study_id": "painter_features_v1",
                        "freeze_id": freeze["freeze_id"],
                        "frame_row_id": row_id,
                        "acquisition_sequence": row["acquisition_sequence"],
                        "artist_id": row["artist_id"],
                        "artist_name": row["artist_name"],
                        "artist_role": row["artist_role"],
                        "physical_work_id": row["physical_work_id"],
                        "reproduction_id": row["reproduction_id"],
                        "capture_id": row["capture_id"],
                        "derivative_family_id": row["derivative_family_id"],
                        "capture_independence_class": row["capture_independence_class"],
                        "provider_workflow_id": row["provider_workflow_id"],
                        "partition": row["partition"],
                        "source_object_id": row["source_object_id"],
                        "asset_url": url,
                        "canonical_object_url": row["canonical_object_url"],
                        "license": row["asset_license"],
                        "rights_basis": row["rights_basis"],
                        "attribution_status": row["attribution_status"],
                        "creation_year": row["creation_year"],
                        "phase_band": row["phase_band"],
                        "content_family": row["content_family"],
                        "medium_raw": row["medium_raw"],
                        "medium_support_cell": row["medium_support_cell"],
                        "prior_metadata_exposure": row["prior_metadata_exposure"],
                        "prior_pixel_exposure": row["prior_pixel_exposure"],
                        "visual_condition_flags": "not_assessed_collection_only",
                        "painted_field_mask_status": "not_created_collection_only",
                        "terminal_event_sha256": terminal["event_sha256"],
                        "recorded_at": utc_now(),
                        "authorization_seal_sha256": seal_sha256,
                        "design_freeze_sha256": freeze_sha256,
                        **response_metadata,
                    },
                )
                print(f"admitted {row_id} {digest}")
            except Exception as exc:
                if terminal_written:
                    raise RuntimeError(
                        f"post-terminal manifest failure for {row_id}; manual adjudication required"
                    ) from exc
                outcome_code = exc.code if isinstance(exc, FrozenFailure) else "unexpected_failure"
                stop_reason = f"{outcome_code}: {type(exc).__name__}: {exc}"
                append_event(
                    attempt_path,
                    terminal_event(
                        row_id=row_id,
                        state="terminal_failure",
                        outcome_code=outcome_code,
                        started_at=started,
                        seal_sha256=seal_sha256,
                        freeze_sha256=freeze_sha256,
                        reason=stop_reason,
                    ),
                )
                print(f"STOP {row_id}: {stop_reason}", file=sys.stderr)
            if index + 1 < len(rows) and stop_reason is None:
                time.sleep(REQUEST_DELAY_SECONDS)
    return 1 if stop_reason else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--seal",
        type=Path,
        default=Path("studies/painter_features_v1/execution/COLLECTION_FREEZE_2_SEAL.json"),
    )
    parser.add_argument("--seal-sha256", required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    seal_path = args.seal if args.seal.is_absolute() else root / args.seal
    return collect(root, seal_path, args.seal_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
