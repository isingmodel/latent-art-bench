"""Prospective, exact-membership normalization authority for Pilot 3.

The preprocessing-determinism amendment is deliberately left AIC-only.  This
module creates a separate authority for the three input classes that were not
covered by that amendment: official Met R2 ``primaryImage`` assets, the frozen
external museum assets, and outputs corresponding to the frozen analytic
``gpt-image-2`` schedule.

Construction is offline and fail-closed.  In particular, it is impossible to
build the authority until the Met R2 metadata freeze and every other source of
membership are committed and clean.  The resulting document authorizes only
normalization; it cannot open acquisition, external-unseal, generation, or
feature-extraction gates.
"""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple
from urllib.parse import urlsplit

from latent_art_bench.io import hash_file, read_json, read_jsonl, stable_hash, write_json
from latent_art_bench.pilot3.met_r2 import (
    DEFAULT_AUTHORIZATION as DEFAULT_MET_R2_AUTHORIZATION,
)
from latent_art_bench.pilot3.met_r2 import (
    DEFAULT_INCIDENT as DEFAULT_MET_INCIDENT,
)
from latent_art_bench.pilot3.met_r2 import (
    DEFAULT_METADATA_ATTEMPTS,
    DEFAULT_METADATA_FREEZE,
    DEFAULT_SPLITS,
    DEFAULT_TARGET_MANIFEST,
    Pilot3MetR2Error,
    require_committed_metadata_freeze,
)
from latent_art_bench.pilot3.met_r2 import (
    NAMESPACE as MET_R2_NAMESPACE,
)
from latent_art_bench.pilot3.preprocessing import (
    PILOT3_CANONICAL_PNG_CHUNKS,
    PILOT3_NORMALIZATION_PROTOCOL_VERSION,
    pilot3_normalization_runtime_fingerprint,
)

SCHEMA_VERSION = "pilot3-normalization-scope-extension/1.0"
NAMESPACE = "pilot3-common-lossless-png-v2-exact-scope-extension"

DEFAULT_AUTHORIZATION = Path("reports/pilot_3/evidence/normalization_scope_extension.json")
LEGACY_AMENDMENT_PATH = Path("reports/pilot_3/evidence/preprocessing_determinism_amendment.json")
PHASE_A_CONFIG_PATH = Path("configs/pilot_3/phase_a.json")
SPLIT_MANIFEST_PATH = Path("data/manifests/pilot_3/real_splits.jsonl")
SCHEDULE_MANIFEST_PATH = Path("data/manifests/pilot_3/schedule.jsonl")
PREPROCESSING_IMPLEMENTATION_PATH = Path("src/latent_art_bench/pilot3/preprocessing.py")
MET_R2_IMPLEMENTATION_PATH = Path("src/latent_art_bench/pilot3/met_r2.py")
SCOPE_IMPLEMENTATION_PATH = Path("src/latent_art_bench/pilot3/normalization_scope.py")
SCOPE_TEST_PATH = Path("tests/pilot3/test_normalization_scope.py")

LEGACY_AMENDMENT_SCHEMA = "pilot3-preprocessing-determinism-amendment/1.0"
LEGACY_AMENDMENT_SCOPE = "exact_frozen_aic_development_image_urls_only"
EXPECTED_LEGACY_AMENDMENT_FILE_SHA256 = (
    "2aafe9e264b3c9df59734d9fd03737ca86c8f2a2ceaeffe210b3b649ce4c840b"
)
EXPECTED_LEGACY_AMENDMENT_SHA256 = (
    "4b8617941c934893489d6d3d73ec54b9c6bc57088c2c5d55524ffe972f1fba31"
)
EXPECTED_PHASE_A_CONFIG_FILE_SHA256 = (
    "34848c3a08b4409f0f09390ca4448153a0a8098efed8a6f59afb2b5bffaaeff8"
)
EXPECTED_SPLIT_MANIFEST_FILE_SHA256 = (
    "0390c43435176df178a8d0e9b6c2dc407dca5a42acd6353183eb9b6198f4095f"
)
EXPECTED_SCHEDULE_MANIFEST_FILE_SHA256 = (
    "9c15f007f2bbc7a644922228ab3ca5379697174d1f97c8c11672b7b9da0d5b4a"
)
EXPECTED_PREPROCESSING_IMPLEMENTATION_FILE_SHA256 = (
    "1a823cc8de0b99090cb6b14aa2069dda808d737c6811bcb0cb40364fb1d108af"
)

EXPECTED_MET_COUNT = 20
EXPECTED_EXTERNAL_COUNT = 12
EXPECTED_GENERATED_COUNT = 320
EXPECTED_GENERATED_MODEL = "gpt-image-2"
EXPECTED_GENERATED_TRANSPORT = "~/dev/openai-oauth"
EXPECTED_GENERATED_ENDPOINT = "/v1/images/generations"
EXPECTED_EXTERNAL_ARTIST_COUNTS = {
    "alfred_sisley": 3,
    "camille_pissarro": 3,
    "paul_cezanne": 3,
    "pierre_auguste_renoir": 3,
}
EXPECTED_EXTERNAL_BLOCK_COUNTS = {"dallas": 4, "minneapolis": 4, "toledo": 4}
EXPECTED_EXTERNAL_HOSTS = {
    "dallas": "files.dma.org",
    "minneapolis": "img.artsmia.org",
    "toledo": "emuseum.toledomuseum.org",
}


class Pilot3NormalizationScopeError(RuntimeError):
    """Raised when the prospective normalization authority must remain closed."""


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _self_hash(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result.pop("authorization_sha256", None)
    result["authorization_sha256"] = stable_hash(result)
    return result


def _verify_self_hash(payload: Mapping[str, Any], *, label: str) -> str:
    recorded = payload.get("authorization_sha256")
    if not _is_sha256(recorded):
        raise Pilot3NormalizationScopeError(f"{label} lacks a valid authorization_sha256")
    unsigned = dict(payload)
    unsigned.pop("authorization_sha256", None)
    if stable_hash(unsigned) != recorded:
        raise Pilot3NormalizationScopeError(f"{label} has a stale authorization_sha256")
    return str(recorded)


def _verify_row_hash(row: Mapping[str, Any], field: str, *, label: str) -> str:
    recorded = row.get(field)
    if not _is_sha256(recorded):
        raise Pilot3NormalizationScopeError(f"{label} lacks a valid {field}")
    unsigned = dict(row)
    unsigned.pop(field, None)
    if stable_hash(unsigned) != recorded:
        raise Pilot3NormalizationScopeError(f"{label} has a stale {field}")
    return str(recorded)


def _resolve(root: Path, relative: Path) -> Path:
    root = Path(root).expanduser().resolve()
    if relative.is_absolute() or ".." in relative.parts:
        raise Pilot3NormalizationScopeError(
            f"normalization-scope path must remain inside the repository: {relative}"
        )
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise Pilot3NormalizationScopeError(
            f"normalization-scope path escapes repository root: {relative}"
        ) from exc
    return resolved


def _require_exact_file(root: Path, relative: Path, expected_sha256: str) -> Path:
    path = _resolve(root, relative)
    if not path.is_file() or hash_file(path) != expected_sha256:
        raise Pilot3NormalizationScopeError(
            f"exact frozen prerequisite is absent or changed: {relative}"
        )
    return path


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
    paths: Sequence[Path],
) -> None:
    for path in paths:
        if not _git_path_committed_and_clean(root, path.as_posix()):
            raise Pilot3NormalizationScopeError(
                f"normalization-scope gate requires a committed and clean path: {path}"
            )


def _read_mapping(path: Path, *, label: str) -> Dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise Pilot3NormalizationScopeError(f"{label} must be a JSON object")
    return dict(value)


def _effective_preprocessing_contract(root: Path) -> Dict[str, Any]:
    config_path = _require_exact_file(
        root, PHASE_A_CONFIG_PATH, EXPECTED_PHASE_A_CONFIG_FILE_SHA256
    )
    config = _read_mapping(config_path, label="Phase-A config")
    common = config.get("common_preprocessing")
    if not isinstance(common, dict):
        raise Pilot3NormalizationScopeError("Phase-A config lacks common_preprocessing")
    return {
        "base_common_preprocessing": dict(common),
        "base_common_preprocessing_config_sha256": stable_hash(common),
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "pixel_transform_changed": False,
        "container_metadata_policy": "no_ancillary_png_chunks",
        "canonical_chunk_sequence": "IHDR_then_contiguous_IDAT_then_IEND",
        "embedded_icc_policy": ("apply_to_rgb_pixels_then_detach_generated_profile_metadata"),
        "normalization_runtime": pilot3_normalization_runtime_fingerprint(),
    }


def _expected_aic_bindings(split_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    selected = [
        row
        for row in split_rows
        if row.get("source_id") == "aic" and row.get("selection_status") == "selected"
    ]
    selected.sort(key=lambda row: str(row.get("canonical_work_id")))
    if len(selected) != 20:
        raise Pilot3NormalizationScopeError(
            "the legacy amendment boundary requires exactly twenty selected AIC works"
        )
    bindings: List[Dict[str, Any]] = []
    for row in selected:
        _verify_row_hash(row, "row_sha256", label="frozen AIC split row")
        if row.get("source_role") != "development" or row.get("partition") not in {
            "development_training",
            "development_calibration",
        }:
            raise Pilot3NormalizationScopeError(
                "the legacy amendment contains a non-development AIC target"
            )
        bindings.append(
            {
                "canonical_work_id": row["canonical_work_id"],
                "image_url": row["image_url"],
                "delivery_width": row["delivery_width"],
                "delivery_height": row["delivery_height"],
                "partition": row["partition"],
                "split_row_sha256": row["row_sha256"],
            }
        )
    return bindings


def _legacy_amendment_binding(
    root: Path,
    split_rows: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    path = _require_exact_file(root, LEGACY_AMENDMENT_PATH, EXPECTED_LEGACY_AMENDMENT_FILE_SHA256)
    amendment = _read_mapping(path, label="legacy preprocessing amendment")
    observed_sha = _verify_self_hash(amendment, label="legacy preprocessing amendment")
    expected_bindings = _expected_aic_bindings(split_rows)
    if (
        amendment.get("schema_version") != LEGACY_AMENDMENT_SCHEMA
        or amendment.get("record_type") != "pilot3_preprocessing_determinism_amendment"
        or observed_sha != EXPECTED_LEGACY_AMENDMENT_SHA256
        or amendment.get("authorization_scope") != LEGACY_AMENDMENT_SCOPE
        or amendment.get("provider") != "Art Institute of Chicago IIIF"
        or amendment.get("provider_hostname") != "www.artic.edu"
        or amendment.get("target_count") != 20
        or amendment.get("target_bindings") != expected_bindings
        or amendment.get("external_holdout_access_authorized") is not False
        or amendment.get("browser_network_feature_or_external_operation_performed_by_authorizer")
        is not False
        or amendment.get("normalization_protocol_version") != PILOT3_NORMALIZATION_PROTOCOL_VERSION
        or amendment.get("effective_preprocessing_contract") != dict(contract)
        or amendment.get("effective_preprocessing_contract_sha256") != stable_hash(contract)
    ):
        raise Pilot3NormalizationScopeError(
            "legacy preprocessing amendment is not the exact AIC-only authority"
        )
    implementation_hashes = amendment.get("remediation_implementation_file_sha256")
    if (
        not isinstance(implementation_hashes, dict)
        or implementation_hashes.get(PREPROCESSING_IMPLEMENTATION_PATH.as_posix())
        != EXPECTED_PREPROCESSING_IMPLEMENTATION_FILE_SHA256
    ):
        raise Pilot3NormalizationScopeError(
            "legacy amendment does not bind the canonical preprocessing implementation"
        )
    return {
        "path": LEGACY_AMENDMENT_PATH.as_posix(),
        "file_sha256": EXPECTED_LEGACY_AMENDMENT_FILE_SHA256,
        "authorization_sha256": observed_sha,
        "authorization_scope": LEGACY_AMENDMENT_SCOPE,
        "provider": "Art Institute of Chicago IIIF",
        "authorized_aic_target_count": 20,
        "authorized_aic_target_bindings_sha256": stable_hash(expected_bindings),
        "external_holdout_access_authorized": False,
        "met_assets_authorized_by_legacy_amendment": False,
        "generated_outputs_authorized_by_legacy_amendment": False,
        "legacy_authority_modified_or_broadened": False,
    }


def _official_external_url(value: object, *, block_id: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise Pilot3NormalizationScopeError(f"external asset in {block_id} lacks an exact URL")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or parsed.hostname != EXPECTED_EXTERNAL_HOSTS[block_id]
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is not None
        or not parsed.path.startswith("/")
        or parsed.fragment
    ):
        raise Pilot3NormalizationScopeError(
            f"external asset URL is not official for block {block_id}"
        )
    return value


def _external_members(split_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    selected = [
        row
        for row in split_rows
        if row.get("source_id") == "museum_balanced" and row.get("selection_status") == "selected"
    ]
    selected.sort(key=lambda row: str(row.get("canonical_work_id")))
    if len(selected) != EXPECTED_EXTERNAL_COUNT:
        raise Pilot3NormalizationScopeError(
            "normalization extension requires exactly twelve external assets"
        )
    if Counter(str(row.get("artist_id")) for row in selected) != EXPECTED_EXTERNAL_ARTIST_COUNTS:
        raise Pilot3NormalizationScopeError("external artist balance changed")
    if (
        Counter(str(row.get("collection_block_id")) for row in selected)
        != EXPECTED_EXTERNAL_BLOCK_COUNTS
    ):
        raise Pilot3NormalizationScopeError("external collection-block balance changed")
    members: List[Dict[str, Any]] = []
    for row in selected:
        _verify_row_hash(row, "row_sha256", label="frozen external split row")
        block_id = str(row.get("collection_block_id"))
        authorization = row.get("digital_reproduction_authorization")
        if (
            row.get("source_role") != "external"
            or row.get("partition") != "external_holdout"
            or row.get("public_domain_status") != "confirmed"
            or block_id not in EXPECTED_EXTERNAL_HOSTS
            or not isinstance(authorization, dict)
            or authorization.get("status") != "authorized"
            or authorization.get("source_id") != "museum_balanced"
            or authorization.get("source_object_id") != row.get("source_object_id")
        ):
            raise Pilot3NormalizationScopeError(
                "external asset identity or reproduction authority changed"
            )
        members.append(
            {
                "asset_id": row["canonical_work_id"],
                "source_object_id": row["source_object_id"],
                "artist_id": row["artist_id"],
                "collection_block_id": block_id,
                "image_url": _official_external_url(row.get("image_url"), block_id=block_id),
                "split_row_sha256": row["row_sha256"],
                "selection_sha256": row["selection_sha256"],
                "digital_reproduction_authorization_sha256": stable_hash(authorization),
            }
        )
    if (
        len({member["asset_id"] for member in members}) != EXPECTED_EXTERNAL_COUNT
        or len({member["image_url"] for member in members}) != EXPECTED_EXTERNAL_COUNT
    ):
        raise Pilot3NormalizationScopeError("external asset IDs and URLs must be unique")
    return members


def _generated_members(root: Path) -> Tuple[List[Dict[str, Any]], str]:
    path = _require_exact_file(root, SCHEDULE_MANIFEST_PATH, EXPECTED_SCHEDULE_MANIFEST_FILE_SHA256)
    raw_rows = read_jsonl(path)
    if len(raw_rows) != EXPECTED_GENERATED_COUNT or any(
        not isinstance(row, dict) for row in raw_rows
    ):
        raise Pilot3NormalizationScopeError(
            "normalization extension requires the exact 320-row schedule"
        )
    rows = [dict(row) for row in raw_rows]
    members: List[Dict[str, Any]] = []
    for sequence, row in enumerate(rows, start=1):
        _verify_row_hash(row, "schedule_row_sha256", label="frozen schedule row")
        request_body = row.get("request_body")
        if (
            row.get("schema_version") != "pilot3-scheduled-request/1.0"
            or row.get("record_type") != "pilot3_scheduled_request"
            or row.get("sequence") != sequence
            or row.get("requested_model_label") != EXPECTED_GENERATED_MODEL
            or not isinstance(request_body, dict)
            or request_body.get("model") != EXPECTED_GENERATED_MODEL
            or row.get("transport") != EXPECTED_GENERATED_TRANSPORT
            or row.get("endpoint") != EXPECTED_GENERATED_ENDPOINT
        ):
            raise Pilot3NormalizationScopeError(
                "schedule contains an ineligible model, transport, endpoint, or sequence"
            )
        members.append(
            {
                "request_id": row["request_id"],
                "sequence": sequence,
                "requested_model_label": EXPECTED_GENERATED_MODEL,
                "schedule_row_sha256": row["schedule_row_sha256"],
                "semantic_request_sha256": row["semantic_request_sha256"],
            }
        )
    if len({member["request_id"] for member in members}) != EXPECTED_GENERATED_COUNT:
        raise Pilot3NormalizationScopeError("frozen request IDs are not unique")
    return members, stable_hash(rows)


def _met_members(targets: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    if len(targets) != EXPECTED_MET_COUNT:
        raise Pilot3NormalizationScopeError(
            "normalization extension requires exactly twenty Met R2 targets"
        )
    members: List[Dict[str, Any]] = []
    for target in targets:
        if (
            target.get("namespace") != MET_R2_NAMESPACE
            or target.get("selected_image_field") != "primaryImage"
            or target.get("fallback_allowed") is not False
            or target.get("replacement_allowed") is not False
            or target.get("image_dimensions_at_freeze") is not None
            or not _is_sha256(target.get("row_sha256"))
        ):
            raise Pilot3NormalizationScopeError(
                "Met R2 target weakens the committed primaryImage policy"
            )
        members.append(
            {
                "r2_asset_id": target["r2_asset_id"],
                "physical_work_id": target["physical_work_id"],
                "object_id": target["object_id"],
                "artist_id": target["artist_id"],
                "partition": target["partition"],
                "primary_image_url": target["primary_image_url"],
                "target_row_sha256": target["row_sha256"],
            }
        )
    members.sort(key=lambda member: int(str(member["object_id"])))
    if (
        len({member["r2_asset_id"] for member in members}) != EXPECTED_MET_COUNT
        or len({member["physical_work_id"] for member in members}) != EXPECTED_MET_COUNT
        or len({member["primary_image_url"] for member in members}) != EXPECTED_MET_COUNT
    ):
        raise Pilot3NormalizationScopeError(
            "Met R2 asset IDs, works, and primaryImage URLs must be unique"
        )
    return members


def _path_binding(root: Path, relative: Path) -> Dict[str, str]:
    path = _resolve(root, relative)
    if not path.is_file():
        raise Pilot3NormalizationScopeError(f"required path is absent: {relative}")
    return {"path": relative.as_posix(), "file_sha256": hash_file(path)}


def build_normalization_scope_authorization(root: Path) -> Dict[str, Any]:
    """Build the offline exact-membership authority after all prerequisites commit."""

    root = Path(root).expanduser().resolve()

    # This call verifies raw metadata, the exact primaryImage selection, all
    # self-hashes, and the committed-and-clean R2 metadata closure.
    try:
        met_authorization, met_targets, metadata_freeze = require_committed_metadata_freeze(root)
    except Pilot3MetR2Error as exc:
        raise Pilot3NormalizationScopeError(
            f"committed and verified Met R2 metadata freeze is required: {exc}"
        ) from exc

    prerequisite_paths = (
        LEGACY_AMENDMENT_PATH,
        PHASE_A_CONFIG_PATH,
        SPLIT_MANIFEST_PATH,
        SCHEDULE_MANIFEST_PATH,
        PREPROCESSING_IMPLEMENTATION_PATH,
        MET_R2_IMPLEMENTATION_PATH,
        SCOPE_IMPLEMENTATION_PATH,
        SCOPE_TEST_PATH,
    )
    _require_committed_paths(root, prerequisite_paths)

    split_path = _require_exact_file(root, SPLIT_MANIFEST_PATH, EXPECTED_SPLIT_MANIFEST_FILE_SHA256)
    raw_split_rows = read_jsonl(split_path)
    if any(not isinstance(row, dict) for row in raw_split_rows):
        raise Pilot3NormalizationScopeError("frozen split contains a non-object row")
    split_rows = [dict(row) for row in raw_split_rows]

    preprocessing_path = _require_exact_file(
        root,
        PREPROCESSING_IMPLEMENTATION_PATH,
        EXPECTED_PREPROCESSING_IMPLEMENTATION_FILE_SHA256,
    )
    contract = _effective_preprocessing_contract(root)
    legacy = _legacy_amendment_binding(root, split_rows, contract)
    met_members = _met_members(met_targets)
    external_members = _external_members(split_rows)
    generated_members, schedule_semantic_sha256 = _generated_members(root)

    met_closure_paths = (
        DEFAULT_MET_INCIDENT,
        DEFAULT_SPLITS,
        DEFAULT_MET_R2_AUTHORIZATION,
        DEFAULT_METADATA_ATTEMPTS,
        DEFAULT_TARGET_MANIFEST,
        DEFAULT_METADATA_FREEZE,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "pilot3_normalization_scope_extension",
        "namespace": NAMESPACE,
        "status": "prospectively_authorized_exact_membership_only",
        "authorization_boundary": {
            "normalization_only": True,
            "network_access_authorized": False,
            "image_acquisition_authorized": False,
            "external_unseal_authorized": False,
            "generation_authorized": False,
            "feature_extraction_authorized": False,
            "fallback_replacement_or_visual_selection_authorized": False,
            "membership_extension_after_outcome_observation_allowed": False,
        },
        "legacy_aic_amendment_boundary": legacy,
        "normalization_implementation": {
            "path": PREPROCESSING_IMPLEMENTATION_PATH.as_posix(),
            "file_sha256": hash_file(preprocessing_path),
            "protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
            "canonical_png_chunks": list(PILOT3_CANONICAL_PNG_CHUNKS),
            "runtime_fingerprint": contract["normalization_runtime"],
            "runtime_fingerprint_sha256": stable_hash(contract["normalization_runtime"]),
            "effective_preprocessing_contract": contract,
            "effective_preprocessing_contract_sha256": stable_hash(contract),
        },
        "prerequisite_commit_gate": {
            "checked_before_authorization_build": True,
            "all_paths_required_committed_and_clean": True,
            "met_r2_metadata_freeze_verified_with_local_raw_metadata": True,
            "met_r2_closure": [_path_binding(root, path) for path in met_closure_paths],
            "other_prerequisites": [_path_binding(root, path) for path in prerequisite_paths],
        },
        "eligible_membership": {
            "met_r2": {
                "count": EXPECTED_MET_COUNT,
                "namespace": MET_R2_NAMESPACE,
                "authorization_sha256": met_authorization["authorization_sha256"],
                "metadata_freeze_sha256": metadata_freeze["freeze_sha256"],
                "target_manifest": _path_binding(root, DEFAULT_TARGET_MANIFEST),
                "selected_image_field": "primaryImage",
                "members": met_members,
            },
            "external_official_assets": {
                "count": EXPECTED_EXTERNAL_COUNT,
                "split_manifest": {
                    "path": SPLIT_MANIFEST_PATH.as_posix(),
                    "file_sha256": EXPECTED_SPLIT_MANIFEST_FILE_SHA256,
                },
                "members": external_members,
            },
            "generated_outputs": {
                "count": EXPECTED_GENERATED_COUNT,
                "schedule_manifest": {
                    "path": SCHEDULE_MANIFEST_PATH.as_posix(),
                    "file_sha256": EXPECTED_SCHEDULE_MANIFEST_FILE_SHA256,
                    "semantic_sha256": schedule_semantic_sha256,
                },
                "required_requested_model_label": EXPECTED_GENERATED_MODEL,
                "required_transport": EXPECTED_GENERATED_TRANSPORT,
                "required_endpoint": EXPECTED_GENERATED_ENDPOINT,
                "members": generated_members,
            },
            "extension_member_count": (
                EXPECTED_MET_COUNT + EXPECTED_EXTERNAL_COUNT + EXPECTED_GENERATED_COUNT
            ),
        },
        "explicit_exclusions": {
            "legacy_aic_assets_remain_governed_only_by_legacy_amendment": True,
            "legacy_met_commons_assets": True,
            "met_primaryImageSmall_or_additionalImages": True,
            "gpt-image-1_analytic_outputs": True,
            "unscheduled_generation_request_ids": True,
            "unenumerated_asset_ids_or_urls": True,
        },
        "construction_io": "offline_no_network_image_generation_or_feature_io",
    }
    return _self_hash(payload)


def verify_normalization_scope_authorization(
    root: Path,
    value: Mapping[str, Any],
) -> Dict[str, Any]:
    """Verify the self-hash and deterministic reconstruction of an authority."""

    if value.get("schema_version") != SCHEMA_VERSION:
        raise Pilot3NormalizationScopeError(
            "normalization-scope authorization has the wrong schema"
        )
    _verify_self_hash(value, label="normalization-scope authorization")
    expected = build_normalization_scope_authorization(root)
    observed = dict(value)
    if observed != expected:
        changed = sorted(
            key for key in set(observed) | set(expected) if observed.get(key) != expected.get(key)
        )
        raise Pilot3NormalizationScopeError(
            "normalization-scope authorization differs from deterministic reconstruction: "
            + ", ".join(changed)
        )
    return observed


def write_normalization_scope_authorization(
    root: Path,
    *,
    path: Path = DEFAULT_AUTHORIZATION,
) -> Dict[str, Any]:
    """Write the authority once; a different existing document is never replaced."""

    root = Path(root).expanduser().resolve()
    value = build_normalization_scope_authorization(root)
    resolved = _resolve(root, path)
    if resolved.exists():
        existing = read_json(resolved)
        if existing != value:
            raise Pilot3NormalizationScopeError(
                "refusing to replace an existing normalization-scope authorization"
            )
    else:
        write_json(resolved, value)
    return value


def load_normalization_scope_authorization(
    root: Path,
    *,
    path: Path = DEFAULT_AUTHORIZATION,
) -> Dict[str, Any]:
    """Load and fully verify an existing authority."""

    resolved = _resolve(Path(root).expanduser().resolve(), path)
    if not resolved.is_file():
        raise Pilot3NormalizationScopeError("normalization-scope authorization is absent")
    value = read_json(resolved)
    if not isinstance(value, dict):
        raise Pilot3NormalizationScopeError(
            "normalization-scope authorization must be a JSON object"
        )
    return verify_normalization_scope_authorization(root, value)


def require_committed_normalization_scope_authorization(
    root: Path,
    *,
    path: Path = DEFAULT_AUTHORIZATION,
) -> Dict[str, Any]:
    """Open normalization only when the authority itself is committed and clean."""

    root = Path(root).expanduser().resolve()
    value = load_normalization_scope_authorization(root, path=path)
    _require_committed_paths(root, (path,))
    return value


# Concise aliases for callers that import this module for its single artifact.
build = build_normalization_scope_authorization
write = write_normalization_scope_authorization
load = load_normalization_scope_authorization
verify = verify_normalization_scope_authorization
require_committed = require_committed_normalization_scope_authorization


__all__ = [
    "DEFAULT_AUTHORIZATION",
    "NAMESPACE",
    "Pilot3NormalizationScopeError",
    "SCHEMA_VERSION",
    "build",
    "build_normalization_scope_authorization",
    "load",
    "load_normalization_scope_authorization",
    "require_committed",
    "require_committed_normalization_scope_authorization",
    "verify",
    "verify_normalization_scope_authorization",
    "write",
    "write_normalization_scope_authorization",
]
