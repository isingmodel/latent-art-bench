from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import federated_census as fc


class BroadMediaFollowupError(fc.CensusError):
    """Raised when the broad media follow-up contract fails closed."""


_CONFIG_SCHEMA = "painter-feature-generation-v1-broad-media-followup-config/1.0"
_FREEZE_SCHEMA = "painter-feature-generation-v1-broad-media-followup-freeze/1.0"
_REVIEW_SCHEMA = "painter-feature-generation-v1-broad-media-followup-review/1.0"
_AUTH_SCHEMA = "painter-feature-generation-v1-broad-media-followup-authorization/1.0"
_RECEIPT_SCHEMA = "painter-feature-generation-v1-broad-media-followup-execution/1.0"
_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "visual_coding": False,
    "active_study_admission": False,
    "feature_extraction": False,
    "generation": False,
}


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise BroadMediaFollowupError(f"{label} must be a repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise BroadMediaFollowupError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise BroadMediaFollowupError(f"{label} escapes the repository") from exc
    return path


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise BroadMediaFollowupError("path is outside the repository") from exc


def _read_hashed_bytes(path: Path, expected: Any, label: str) -> bytes:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise BroadMediaFollowupError(f"{label} cannot be read") from exc
    if not isinstance(expected, str) or hashlib.sha256(body).hexdigest() != expected:
        raise BroadMediaFollowupError(f"{label} hash mismatch")
    return body


def _json_object(body: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BroadMediaFollowupError(f"{label} is not JSON") from exc
    if not isinstance(value, dict):
        raise BroadMediaFollowupError(f"{label} is not an object")
    return value


def _jsonl_objects(body: bytes, label: str) -> list[dict[str, Any]]:
    try:
        lines = body.decode().splitlines()
    except UnicodeDecodeError as exc:
        raise BroadMediaFollowupError(f"{label} is not UTF-8") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line:
            raise BroadMediaFollowupError(f"{label} has a blank row at {number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BroadMediaFollowupError(f"{label} row {number} is not JSON") from exc
        if not isinstance(value, dict):
            raise BroadMediaFollowupError(f"{label} row {number} is not an object")
        rows.append(value)
    return rows


def _load_config_bytes(root: Path, config_path: Path, body: bytes) -> dict[str, Any]:
    config = _json_object(body, "config")
    if config.get("schema_version") != _CONFIG_SCHEMA:
        raise BroadMediaFollowupError("unsupported broad follow-up config")
    protocol = _repo_path(root, config.get("protocol_path"), "protocol_path")
    match = re.search(r"^Protocol ID: `([^`]+)`$", protocol.read_text(), flags=re.MULTILINE)
    if not match or config.get("protocol_id") != match.group(1):
        raise BroadMediaFollowupError("config differs from the canonical protocol")
    source = config.get("source_frame_contract")
    request = config.get("request_contract")
    screening = config.get("screening_contract")
    paths = config.get("paths")
    if (
        not isinstance(source, Mapping)
        or source.get("frame_class")
        != "complete_followup_of_broad_no_p186_wikidata_discovery_not_authority_census"
        or not isinstance(request, Mapping)
        or not isinstance(screening, Mapping)
        or not isinstance(paths, Mapping)
    ):
        raise BroadMediaFollowupError("config contracts are incomplete")
    expected_path_keys = {
        "planned_requests",
        "request_events",
        "candidate_manifest",
        "execution_receipt",
        "workspace",
    }
    if set(paths) != expected_path_keys:
        raise BroadMediaFollowupError("config paths are not exact")
    resolved = [_repo_path(root, paths[key], f"paths.{key}") for key in sorted(paths)]
    if len(set(resolved)) != len(resolved) or any(
        left in right.parents or right in left.parents
        for index, left in enumerate(resolved)
        for right in resolved[index + 1 :]
    ):
        raise BroadMediaFollowupError("config paths overlap")
    candidate_path = _repo_path(root, paths["candidate_manifest"], "candidate manifest")
    receipt_path = _repo_path(root, paths["execution_receipt"], "execution receipt")
    if (
        candidate_path.parent != receipt_path.parent
        or candidate_path.name != "candidates.jsonl"
        or receipt_path.name != "execution_receipt.json"
    ):
        raise BroadMediaFollowupError("result files do not share the exact atomic publication root")
    if (
        request.get("wikidata_endpoint") != "https://www.wikidata.org/w/api.php"
        or request.get("commons_endpoint") != "https://commons.wikimedia.org/w/api.php"
        or request.get("batch_size") != 40
        or request.get("maximum_attempts") != 5
        or request.get("retryable_http_status_codes") != [429, 500, 502, 503, 504]
        or request.get("retryable_api_error_codes")
        != ["internal_api_error", "maxlag", "ratelimited", "readonly"]
    ):
        raise BroadMediaFollowupError("request contract differs from the approved API contract")
    cutoff = request.get("execution_start_not_after_utc")
    try:
        parsed = datetime.fromisoformat(str(cutoff).replace("Z", "+00:00"))
    except ValueError as exc:
        raise BroadMediaFollowupError("execution cutoff is invalid") from exc
    if not str(cutoff).endswith("Z") or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise BroadMediaFollowupError("execution cutoff is not UTC")
    if (
        _relative(root, config_path)
        != "configs/painter_feature_generation_v1/broad_media_followup.json"
    ):
        raise BroadMediaFollowupError("unexpected config path")
    return config


def load_config(root: Path, config_path: Path) -> dict[str, Any]:
    return _load_config_bytes(root, config_path.resolve(), config_path.read_bytes())


def _load_upstream(
    root: Path, config: Mapping[str, Any]
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    source = config["source_frame_contract"]
    candidate_path = _repo_path(root, source["upstream_candidate_path"], "upstream candidate")
    receipt_path = _repo_path(root, source["upstream_receipt_path"], "upstream receipt")
    raw_rows = _jsonl_objects(
        _read_hashed_bytes(
            candidate_path, source["upstream_candidate_sha256"], "upstream candidate"
        ),
        "upstream candidate",
    )
    receipt = _json_object(
        _read_hashed_bytes(receipt_path, source["upstream_receipt_sha256"], "upstream receipt"),
        "upstream receipt",
    )
    if (
        receipt.get("status") != "broad_wikidata_no_p186_metadata_census_complete"
        or receipt.get("candidate_manifest_sha256") != source["upstream_candidate_sha256"]
        or receipt.get("counts", {}).get("item_image_rows") != source["expected_rows"]
        or receipt.get("counts", {}).get("distinct_items") != source["expected_distinct_items"]
        or receipt.get("counts", {}).get("distinct_files") != source["expected_distinct_files"]
    ):
        raise BroadMediaFollowupError("upstream receipt does not bind the broad frame")
    painters = config["painters"]
    rows: list[dict[str, str]] = []
    expected_keys = {
        "schema_version",
        "census_id",
        "candidate_sequence",
        "painter_id",
        "creator_qid",
        "item_qid",
        "commons_filename",
        "source_request_id",
        "discovery_status",
        "active_study_admission",
    }
    for sequence, row in enumerate(raw_rows, start=1):
        if (
            set(row) != expected_keys
            or row.get("schema_version")
            != "painter-feature-generation-v1-broad-wikidata-candidate/1.0"
            or row.get("census_id") != receipt.get("census_id")
            or row.get("candidate_sequence") != sequence
            or row.get("discovery_status") != "broad_no_p186_candidate_not_authority_verified"
            or row.get("active_study_admission") is not False
            or painters.get(row.get("creator_qid")) != row.get("painter_id")
            or not re.fullmatch(r"Q[1-9][0-9]*", str(row.get("item_qid")))
            or not str(row.get("commons_filename") or "").strip()
        ):
            raise BroadMediaFollowupError("upstream candidate row is invalid")
        rows.append(
            {
                "painter_id": row["painter_id"],
                "creator_qid": row["creator_qid"],
                "item_qid": row["item_qid"],
                "commons_filename": row["commons_filename"],
            }
        )
    if (
        len(rows) != source["expected_rows"]
        or len({row["item_qid"] for row in rows}) != source["expected_distinct_items"]
        or len({row["commons_filename"] for row in rows}) != source["expected_distinct_files"]
        or len({(row["item_qid"], row["commons_filename"]) for row in rows}) != len(rows)
    ):
        raise BroadMediaFollowupError("upstream row counts or uniqueness drifted")
    return rows, receipt


def _intent_records(
    config: Mapping[str, Any], rows: Sequence[Mapping[str, str]]
) -> list[dict[str, Any]]:
    return [spec.as_record(str(config["census_id"])) for spec in _build_request_specs(config, rows)]


def _build_request_specs(
    config: Mapping[str, Any], rows: Sequence[Mapping[str, str]]
) -> list[fc.RequestSpec]:
    """Build a total-order request frame independent of set/hash iteration order."""
    request = config["request_contract"]
    size = int(request["batch_size"])
    if size < 1 or size > 50:
        raise BroadMediaFollowupError("batch_size must be between 1 and 50")
    item_ids = sorted({row["item_qid"] for row in rows}, key=lambda value: int(value[1:]))
    file_titles = sorted(
        {f"File:{row['commons_filename']}" for row in rows},
        key=lambda value: (value.casefold(), value),
    )
    specs: list[fc.RequestSpec] = []
    sequence = 0
    for index in range(0, len(item_ids), size):
        sequence += 1
        batch = item_ids[index : index + size]
        specs.append(
            fc.RequestSpec(
                request_id=f"wikidata-entities-{index // size + 1:04d}",
                stage="wikidata_entities",
                sequence=sequence,
                endpoint=str(request["wikidata_endpoint"]),
                params={
                    "action": "wbgetentities",
                    "curtimestamp": "1",
                    "errorformat": "plaintext",
                    "format": "json",
                    "formatversion": "2",
                    "ids": "|".join(batch),
                    "languages": "en|fr",
                    "languagefallback": "1",
                    "maxlag": "5",
                    "props": str(request["wikidata_properties"]),
                    "servedby": "1",
                    "uselang": "en",
                },
                members=tuple(batch),
            )
        )
    for index in range(0, len(file_titles), size):
        sequence += 1
        batch = file_titles[index : index + size]
        specs.append(
            fc.RequestSpec(
                request_id=f"commons-imageinfo-{index // size + 1:04d}",
                stage="commons_imageinfo",
                sequence=sequence,
                endpoint=str(request["commons_endpoint"]),
                params={
                    "action": "query",
                    "curtimestamp": "1",
                    "errorformat": "plaintext",
                    "format": "json",
                    "formatversion": "2",
                    "iiextmetadatalanguage": "en",
                    "iiextmetadatafilter": str(request["commons_extmetadata_fields"]),
                    "iilimit": "1",
                    "iimetadataversion": "1",
                    "iiprop": str(request["commons_imageinfo_properties"]),
                    "maxlag": "5",
                    "prop": "imageinfo",
                    "servedby": "1",
                    "titles": "|".join(batch),
                    "uselang": "en",
                },
                members=tuple(batch),
            )
        )
    return specs


def prepare(root: Path, config_path: Path) -> dict[str, Any]:
    config = load_config(root, config_path)
    rows, _ = _load_upstream(root, config)
    records = _intent_records(config, rows)
    if len(records) != 182:
        raise BroadMediaFollowupError("planned request count is not exactly 182")
    path = _repo_path(root, config["paths"]["planned_requests"], "planned requests")
    fc._write_jsonl_atomic(path, records)
    return {
        "census_id": config["census_id"],
        "rows": len(rows),
        "planned_requests": len(records),
        "wikidata_requests": sum(row["stage"] == "wikidata_entities" for row in records),
        "commons_requests": sum(row["stage"] == "commons_imageinfo" for row in records),
        "intent_path": _relative(root, path),
        "intent_sha256": hash_file(path),
    }


def required_frozen_paths(root: Path, config_path: Path, config: Mapping[str, Any]) -> list[str]:
    source = config["source_frame_contract"]
    paths = {
        ".gitignore",
        _relative(root, config_path),
        str(config["protocol_path"]),
        str(source["upstream_candidate_path"]),
        str(source["upstream_receipt_path"]),
        str(config["paths"]["planned_requests"]),
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_broad_media_followup.py",
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/federated_census.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_media_followup.py",
        "src/latent_art_bench/config.py",
        "src/latent_art_bench/schemas.py",
        "tests/conftest.py",
        "tests/painter_feature_generation_v1/test_broad_media_followup.py",
    }
    for value in paths:
        if not _repo_path(root, value, "frozen input").is_file():
            raise BroadMediaFollowupError(f"missing frozen input: {value}")
    return sorted(paths)


def expected_outputs(config: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = config["paths"]
    workspace = Path(str(paths["workspace"]))
    return [
        {"path": str(paths[key]), "state": "absent"}
        for key in ("request_events", "candidate_manifest", "execution_receipt")
    ] + [
        {
            "path": str(Path(str(paths["candidate_manifest"])).parent),
            "state": "absent",
        },
        {"path": str(workspace / ".execution.lock"), "state": "absent"},
        {"path": str(workspace / "response_bodies"), "state": "absent"},
    ]


def _freeze_sha(freeze: Mapping[str, Any], path: str) -> str:
    matches = [
        row.get("sha256")
        for row in freeze.get("frozen_inputs", [])
        if isinstance(row, Mapping) and row.get("path") == path
    ]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise BroadMediaFollowupError(f"freeze does not uniquely bind {path}")
    return matches[0]


def _validate_authorization(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
) -> dict[str, Any]:
    seal = _json_object(
        _read_hashed_bytes(seal_path, seal_sha256, "authorization"), "authorization"
    )
    freeze_path = _repo_path(root, seal.get("freeze_path"), "freeze")
    freeze = _json_object(
        _read_hashed_bytes(freeze_path, seal.get("freeze_sha256"), "freeze"), "freeze"
    )
    config_relative = _relative(root, config_path)
    config_body = _read_hashed_bytes(config_path, _freeze_sha(freeze, config_relative), "config")
    config = _load_config_bytes(root, config_path, config_body)
    entries = freeze.get("frozen_inputs")
    required = required_frozen_paths(root, config_path, config)
    if (
        seal.get("schema_version") != _AUTH_SCHEMA
        or seal.get("status") != "authorized_for_broad_media_followup_execution"
        or seal.get("census_id") != config["census_id"]
        or seal.get("protocol_id") != config["protocol_id"]
        or seal.get("authorization_scope") != _SCOPE
        or freeze.get("schema_version") != _FREEZE_SCHEMA
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != _SCOPE
        or not isinstance(entries, list)
        or [row.get("path") for row in entries] != required
        or freeze.get("preexecution_outputs") != expected_outputs(config)
    ):
        raise BroadMediaFollowupError("authorization or freeze semantics are invalid")
    for row in entries:
        _read_hashed_bytes(
            _repo_path(root, row["path"], "frozen input"), row.get("sha256"), "frozen input"
        )
    if hashlib.sha256(canonical_json(entries).encode()).hexdigest() != freeze.get(
        "frozen_input_set_sha256"
    ):
        raise BroadMediaFollowupError("freeze aggregate mismatch")
    review_path = _repo_path(root, seal.get("review_path"), "review")
    review = _json_object(
        _read_hashed_bytes(review_path, seal.get("review_sha256"), "review"), "review"
    )
    if (
        review.get("schema_version") != _REVIEW_SCHEMA
        or review.get("decision") != "APPROVE_BROAD_MEDIA_FOLLOWUP_ONLY"
        or review.get("blocking_findings") != []
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or review.get("approved_scope") != _SCOPE
        or review.get("reviewed_freeze_path") != seal.get("freeze_path")
        or review.get("reviewed_freeze_sha256") != seal.get("freeze_sha256")
    ):
        raise BroadMediaFollowupError("review is invalid")
    rows, upstream_receipt = _load_upstream(root, config)
    intent_path = str(config["paths"]["planned_requests"])
    intent_rows = _jsonl_objects(
        _read_hashed_bytes(
            _repo_path(root, intent_path, "intents"),
            _freeze_sha(freeze, intent_path),
            "intents",
        ),
        "intents",
    )
    expected_intents = _intent_records(config, rows)
    if intent_rows != expected_intents or len(intent_rows) != 182:
        raise BroadMediaFollowupError("request intents differ from reconstruction")
    specs = _build_request_specs(config, rows)
    return {
        "seal": seal,
        "freeze": freeze,
        "review": review,
        "config": config,
        "rows": rows,
        "upstream_receipt": upstream_receipt,
        "intents": intent_rows,
        "specs": specs,
        "intent_sha256": _freeze_sha(freeze, intent_path),
    }


def _enforce_cutoff(config: Mapping[str, Any]) -> str:
    cutoff = datetime.fromisoformat(
        str(config["request_contract"]["execution_start_not_after_utc"]).replace("Z", "+00:00")
    )
    started_at = fc._utc_now()
    started = fc._parse_media_timestamp(started_at)
    if started is None or started >= cutoff:
        raise BroadMediaFollowupError("execution-start cutoff has passed")
    return started_at


def _load_verified_payloads(
    specs: Sequence[fc.RequestSpec],
    inventory: Sequence[Mapping[str, Any]],
    response_paths: Mapping[str, Path],
) -> tuple[dict[str, dict[str, Any]], dict[str, str], list[str]]:
    """Bind digest, JSON value, stage schema, and provider time to one file read."""
    inventory_by_id = {str(row["request_id"]): row for row in inventory}
    payloads: dict[str, dict[str, Any]] = {}
    digests: dict[str, str] = {}
    provider_times: list[str] = []
    for spec in specs:
        receipt = inventory_by_id.get(spec.request_id)
        path = response_paths.get(spec.request_id)
        if receipt is None or path is None:
            raise BroadMediaFollowupError(f"missing response binding for {spec.request_id}")
        body = _read_hashed_bytes(path, receipt.get("response_sha256"), spec.request_id)
        if receipt.get("response_bytes") != len(body):
            raise BroadMediaFollowupError(f"response byte count drifted for {spec.request_id}")
        payload = _json_object(body, spec.request_id)
        fc._validate_stage_payload(spec, payload)
        payloads[spec.request_id] = payload
        digests[spec.request_id] = hashlib.sha256(body).hexdigest()
        provider_times.append(str(payload["curtimestamp"]))
    return payloads, digests, provider_times


def _parse_entity_payloads(
    specs: Sequence[fc.RequestSpec],
    payloads: Mapping[str, Mapping[str, Any]],
    digests: Mapping[str, str],
) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for spec in specs:
        if spec.stage != "wikidata_entities":
            continue
        payload = payloads[spec.request_id]
        batch_entities = payload.get("entities", {})
        if not isinstance(batch_entities, Mapping):
            raise BroadMediaFollowupError(f"{spec.request_id} lacks entities")
        raw_hash = digests[spec.request_id]
        for qid in spec.members:
            entity = batch_entities.get(qid)
            resolved_qid = (
                str(entity.get("id"))
                if isinstance(entity, Mapping) and re.fullmatch(r"Q\d+", str(entity.get("id")))
                else qid
            )
            if not isinstance(entity, Mapping) or entity.get("missing") is not None:
                entities[qid] = {
                    "entity_status": "missing",
                    "requested_entity_qid": qid,
                    "resolved_entity_qid": resolved_qid,
                    "redirected": resolved_qid != qid,
                    "raw_response_sha256": raw_hash,
                }
                continue
            labels = entity.get("labels", {})
            descriptions = entity.get("descriptions", {})
            tracked = (
                "P18",
                "P170",
                "P31",
                "P186",
                "P195",
                "P217",
                "P973",
                "P276",
                "P571",
                "P6216",
            )
            entities[qid] = {
                "entity_status": "resolved",
                "requested_entity_qid": qid,
                "resolved_entity_qid": resolved_qid,
                "redirected": resolved_qid != qid,
                "label": next(
                    (
                        labels[key].get("value")
                        for key in ("en", "fr")
                        if isinstance(labels.get(key), Mapping)
                    ),
                    None,
                ),
                "description": next(
                    (
                        descriptions[key].get("value")
                        for key in ("en", "fr")
                        if isinstance(descriptions.get(key), Mapping)
                    ),
                    None,
                ),
                "creator_qids": [str(value) for value in fc._statement_values(entity, "P170")],
                "commons_filenames": [str(value) for value in fc._statement_values(entity, "P18")],
                "instance_qids": [str(value) for value in fc._statement_values(entity, "P31")],
                "material_qids": [str(value) for value in fc._statement_values(entity, "P186")],
                "collection_qids": [str(value) for value in fc._statement_values(entity, "P195")],
                "location_qids": [str(value) for value in fc._statement_values(entity, "P276")],
                "inventory_numbers": [str(value) for value in fc._statement_values(entity, "P217")],
                "described_at_urls": [str(value) for value in fc._statement_values(entity, "P973")],
                "inception_values": fc._statement_values(entity, "P571"),
                "copyright_status_qids": [
                    str(value) for value in fc._statement_values(entity, "P6216")
                ],
                "best_rank_claims": {
                    property_id: fc._statement_records(entity, property_id)
                    for property_id in tracked
                },
                "reference_urls": fc._reference_urls(entity),
                "raw_response_sha256": raw_hash,
            }
    return entities


def _parse_media_payloads(
    specs: Sequence[fc.RequestSpec],
    payloads: Mapping[str, Mapping[str, Any]],
    digests: Mapping[str, str],
    config: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    media: dict[str, dict[str, Any]] = {}
    screen = config["screening_contract"]
    allowed_urls = [
        str(value).casefold() for value in screen["allowed_commons_license_url_prefixes"]
    ]
    allowed_names = {
        str(value).casefold() for value in screen["allowed_unlinked_license_short_names"]
    }
    nonfree = [str(value).casefold() for value in screen["nonfree_markers"]]
    supported_mimes = {str(value).casefold() for value in screen["supported_image_mime_types"]}
    minimum_short = int(screen["minimum_short_side_pixels"])
    for spec in specs:
        if spec.stage != "commons_imageinfo":
            continue
        pages = payloads[spec.request_id].get("query", {}).get("pages", [])
        if not isinstance(pages, list):
            raise BroadMediaFollowupError(f"{spec.request_id} lacks pages")
        page_by_title = {
            str(page.get("title")): page
            for page in pages
            if isinstance(page, Mapping) and page.get("title")
        }
        raw_hash = digests[spec.request_id]
        for requested_title in spec.members:
            key = requested_title.removeprefix("File:")
            page = page_by_title.get(requested_title)
            if page is None:
                media[key] = {"media_status": "missing", "raw_response_sha256": raw_hash}
                continue
            info_rows = page.get("imageinfo") or []
            if len(info_rows) != 1:
                media[key] = {
                    "media_status": "missing_or_ambiguous",
                    "canonical_title": requested_title,
                    "raw_response_sha256": raw_hash,
                }
                continue
            info = info_rows[0]
            metadata = info.get("extmetadata") or {}
            license_short = fc._plain_text(fc._metadata_value(metadata, "LicenseShortName"))
            usage_terms = fc._plain_text(fc._metadata_value(metadata, "UsageTerms"))
            license_url = fc._plain_text(fc._metadata_value(metadata, "LicenseUrl"))
            copyrighted = fc._plain_text(fc._metadata_value(metadata, "Copyrighted"))
            restrictions = fc._plain_text(fc._metadata_value(metadata, "Restrictions"))
            permission = fc._plain_text(fc._metadata_value(metadata, "Permission"))
            normalized_url = license_url.casefold().replace("http://", "https://", 1)
            open_url = any(normalized_url.startswith(prefix) for prefix in allowed_urls)
            unlinked_pd = (
                not normalized_url
                and license_short.casefold() in allowed_names
                and copyrighted.casefold() in {"false", "no"}
            )
            rights_text = " ".join(
                (license_short, usage_terms, license_url, copyrighted, restrictions, permission)
            ).casefold()
            has_restriction = bool(restrictions and restrictions.casefold() not in {"none", "no"})
            copyrighted_value = copyrighted.casefold()
            consistent = copyrighted_value in {"", "false", "no", "true", "yes"}
            if "/publicdomain/" in normalized_url:
                consistent = copyrighted_value in {"false", "no"}
            rights_candidate = (
                (open_url or unlinked_pd)
                and not any(marker in rights_text for marker in nonfree)
                and not has_restriction
                and consistent
            )
            width = int(info.get("width") or 0)
            height = int(info.get("height") or 0)
            mime = str(info.get("mime") or "").casefold()
            sha1 = str(info.get("sha1") or "")
            timestamp = info.get("timestamp")
            delivery_complete = (
                fc._is_http_url(info.get("url"))
                and fc._is_http_url(info.get("descriptionurl"))
                and bool(re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-z]{31})", sha1.casefold()))
                and fc._is_media_timestamp(timestamp)
            )
            media[key] = {
                "media_status": "resolved",
                "canonical_title": requested_title,
                "description_url": info.get("descriptionurl"),
                "original_url": info.get("url"),
                "original_width": width,
                "original_height": height,
                "original_short_side": min(width, height),
                "mime": mime,
                "mediawiki_sha1": sha1,
                "media_timestamp": timestamp,
                "license_short_name": license_short,
                "usage_terms": usage_terms,
                "license_url": license_url,
                "copyrighted": copyrighted,
                "restrictions": restrictions,
                "permission": permission,
                "artist_text": fc._plain_text(fc._metadata_value(metadata, "Artist")),
                "institution_text": fc._plain_text(fc._metadata_value(metadata, "Institution")),
                "credit_text": fc._plain_text(fc._metadata_value(metadata, "Credit")),
                "source_text": fc._plain_text(fc._metadata_value(metadata, "Source")),
                "object_name": fc._plain_text(fc._metadata_value(metadata, "ObjectName")),
                "image_description": fc._plain_text(
                    fc._metadata_value(metadata, "ImageDescription")
                ),
                "metadata_urls": fc._metadata_urls(
                    metadata, ("Institution", "Credit", "Source", "ImageDescription")
                ),
                "rights_candidate_status": "commons_open_rights_marker_candidate"
                if rights_candidate
                else "rights_review",
                "geometry_candidate_status": "reported_original_geometry_candidate"
                if min(width, height) >= minimum_short
                else "original_short_side_below_minimum",
                "decode_format_candidate_status": "supported_image_mime"
                if mime in supported_mimes
                else "unsupported_image_mime",
                "delivery_receipt_status": "complete_media_delivery_receipt_candidate"
                if delivery_complete
                else "incomplete_media_delivery_receipt",
                "raw_response_sha256": raw_hash,
            }
    return media


def _execute_specs(
    root: Path,
    config: Mapping[str, Any],
    specs: Sequence[fc.RequestSpec],
    workspace: Path,
    events: list[dict[str, Any]],
    transport: httpx.BaseTransport | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    """Execute the frame; an unknown transport outcome is terminal, never retried."""
    event_path = _repo_path(root, config["paths"]["request_events"], "request events")
    request = config["request_contract"]
    interval = float(request["minimum_interval_seconds"])
    retry_base = float(request["retry_backoff_base_seconds"])
    maximum_attempts = int(request["maximum_attempts"])
    maximum_wait = float(request["maximum_retry_wait_seconds"])
    retryable_http = {int(value) for value in request["retryable_http_status_codes"]}
    retryable_api = {str(value).casefold() for value in request["retryable_api_error_codes"]}
    spec_by_id = {spec.request_id: spec for spec in specs}
    starts, finishes = _followup_attempt_maps(events, spec_by_id, workspace, request)
    for key, start in list(starts.items()):
        if key not in finishes:
            fc._append_event(
                event_path,
                str(config["census_id"]),
                events,
                {
                    "event_type": "attempt_finished",
                    "request_id": key[0],
                    "stage": start["stage"],
                    "attempt": key[1],
                    "finished_at_utc": fc._utc_now(),
                    "outcome": "terminal_interrupted_new_census_required",
                    "semantic_outcome": None,
                    "retryable": False,
                    "status_code": None,
                    "final_url": None,
                    "redirect_history": [],
                    "response_headers": {},
                    "response_bytes": None,
                    "response_sha256": None,
                    "response_body_path": None,
                    "api_error_code": None,
                    "retry_after_seconds": None,
                    "error": (
                        "The prior attempt has an unknowable network outcome; "
                        "a new reviewed census ID is required."
                    ),
                },
            )
    starts, finishes = _followup_attempt_maps(events, spec_by_id, workspace, request)
    if finishes:
        finish_times = [
            fc._parse_media_timestamp(row.get("finished_at_utc")) for row in finishes.values()
        ]
        if any(value is None for value in finish_times):
            raise BroadMediaFollowupError("persisted finish lacks a valid timestamp")
        latest_finish = max(value for value in finish_times if value is not None)
        elapsed = max(
            0.0,
            (datetime.now(timezone.utc) - latest_finish).total_seconds(),
        )
        remaining_interval = max(0.0, interval - elapsed)
        if remaining_interval:
            time.sleep(remaining_interval)
    receipts: list[dict[str, Any]] = []
    response_paths: dict[str, Path] = {}
    last_access = 0.0
    with httpx.Client(
        timeout=float(request["timeout_seconds"]),
        follow_redirects=False,
        transport=transport,
        headers={
            "User-Agent": str(request["user_agent"]),
            "Api-User-Agent": str(request["user_agent"]),
            "Accept": "application/json",
        },
    ) as client:
        for spec in specs:
            successes = [
                row
                for (request_id, _), row in finishes.items()
                if request_id == spec.request_id and row.get("outcome") == "success"
            ]
            if len(successes) > 1:
                raise BroadMediaFollowupError(f"multiple successes for {spec.request_id}")
            if successes:
                path, payload = fc._success_response_path(workspace, successes[0])
                fc._validate_stage_payload(spec, payload)
                response_paths[spec.request_id] = path
                receipts.append(
                    {
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "status": "verified_success_event",
                        "attempt": successes[0]["attempt"],
                        "response_sha256": successes[0]["response_sha256"],
                        "response_bytes": successes[0]["response_bytes"],
                        "response_body_path": successes[0]["response_body_path"],
                    }
                )
                continue
            prior = [
                row for (request_id, _), row in finishes.items() if request_id == spec.request_id
            ]
            if any(row.get("retryable") is False for row in prior):
                raise BroadMediaFollowupError(f"{spec.request_id} already ended terminally")
            attempts_used = sum(request_id == spec.request_id for request_id, _ in starts)
            if prior:
                delay = fc._remaining_retry_delay_seconds(
                    max(prior, key=lambda row: int(row["attempt"])),
                    retry_backoff_base=retry_base,
                    minimum_interval=interval,
                    maximum_wait=maximum_wait,
                )
                if delay:
                    time.sleep(delay)
            terminal: Mapping[str, Any] | None = None
            while attempts_used < maximum_attempts:
                delay = interval - (time.monotonic() - last_access)
                if delay > 0:
                    time.sleep(delay)
                attempt = attempts_used + 1
                prepared = client.build_request("GET", spec.endpoint, params=spec.params)
                if str(prepared.url) != fc._encoded_request_url(spec):
                    raise BroadMediaFollowupError(f"HTTP encoding drift for {spec.request_id}")
                fc._append_event(
                    event_path,
                    str(config["census_id"]),
                    events,
                    {
                        "event_type": "attempt_started",
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "attempt": attempt,
                        "started_at_utc": fc._utc_now(),
                        "method": "GET",
                        "encoded_request_url": str(prepared.url),
                        "intent_sequence": spec.sequence,
                    },
                )
                attempts_used += 1
                try:
                    response = client.send(prepared)
                    body = response.content
                except httpx.HTTPError as exc:
                    last_access = time.monotonic()
                    terminal = fc._append_event(
                        event_path,
                        str(config["census_id"]),
                        events,
                        {
                            "event_type": "attempt_finished",
                            "request_id": spec.request_id,
                            "stage": spec.stage,
                            "attempt": attempt,
                            "finished_at_utc": fc._utc_now(),
                            "outcome": "terminal_interrupted_new_census_required",
                            "semantic_outcome": None,
                            "retryable": False,
                            "status_code": None,
                            "final_url": None,
                            "redirect_history": [],
                            "response_headers": {},
                            "response_bytes": None,
                            "response_sha256": None,
                            "response_body_path": None,
                            "api_error_code": None,
                            "retry_after_seconds": None,
                            "error": (
                                f"{type(exc).__name__}: {exc}; network outcome is "
                                "unknowable and requires a new reviewed census ID."
                            ),
                        },
                    )
                    raise BroadMediaFollowupError(
                        f"{spec.request_id} ended with an unknowable transport outcome"
                    ) from exc
                last_access = time.monotonic()
                response_path, response_digest = fc._store_response_body(workspace, body)
                outcome = "terminal_http_error"
                retryable = False
                semantic: str | None = None
                api_code: str | None = None
                error: str | None = None
                if response.status_code == 200:
                    try:
                        parsed = json.loads(body)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        parsed = None
                    if not isinstance(parsed, Mapping):
                        outcome = "terminal_malformed_json_200"
                    elif "error" in parsed:
                        api_error = parsed.get("error")
                        api_code = (
                            str(api_error.get("code") or "unknown").casefold()
                            if isinstance(api_error, Mapping)
                            else "unknown"
                        )
                        retryable = api_code in retryable_api
                        outcome = "retryable_api_error" if retryable else "terminal_api_error"
                    else:
                        try:
                            semantic = fc._validate_stage_payload(spec, parsed)
                        except fc.CensusError as exc:
                            error = str(exc)
                            outcome = "terminal_stage_schema_failure"
                        else:
                            outcome = "success"
                else:
                    retryable = response.status_code in retryable_http
                    outcome = "retryable_http_error" if retryable else "terminal_http_error"
                retry_after: float | None = None
                if "retry-after" in response.headers:
                    try:
                        retry_after = fc._retry_after_seconds(response.headers["retry-after"])
                    except (TypeError, ValueError, fc.CensusError) as exc:
                        outcome, retryable, error = (
                            "terminal_retry_after_new_census_required",
                            False,
                            str(exc),
                        )
                    if retry_after is not None and retry_after > maximum_wait:
                        outcome, retryable = "terminal_retry_after_new_census_required", False
                        semantic = None
                        error = (
                            "Retry-After exceeds the frozen wait ceiling; a new "
                            "reviewed census ID is required."
                        )
                    elif not retryable:
                        outcome = "terminal_retry_after_new_census_required"
                        semantic = None
                        error = (
                            "Unexpected Retry-After on a non-retryable response; "
                            "a new reviewed census ID is required."
                        )
                headers = {
                    key: response.headers[key]
                    for key in (
                        "age",
                        "cache-control",
                        "content-encoding",
                        "content-length",
                        "content-type",
                        "date",
                        "etag",
                        "last-modified",
                        "retry-after",
                        "server",
                        "server-timing",
                        "x-cache",
                        "x-cache-status",
                        "x-database-lag",
                        "x-request-id",
                    )
                    if key in response.headers
                }
                terminal = fc._append_event(
                    event_path,
                    str(config["census_id"]),
                    events,
                    {
                        "event_type": "attempt_finished",
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "attempt": attempt,
                        "finished_at_utc": fc._utc_now(),
                        "outcome": outcome,
                        "semantic_outcome": semantic,
                        "retryable": retryable,
                        "status_code": response.status_code,
                        "final_url": str(response.url),
                        "redirect_history": [
                            {"status_code": item.status_code, "url": str(item.url)}
                            for item in response.history
                        ],
                        "response_headers": headers,
                        "response_bytes": len(body),
                        "response_sha256": response_digest,
                        "response_body_path": str(response_path.relative_to(workspace)),
                        "api_error_code": api_code,
                        "retry_after_seconds": retry_after,
                        "error": error,
                    },
                )
                starts, finishes = _followup_attempt_maps(events, spec_by_id, workspace, request)
                if outcome == "success":
                    response_paths[spec.request_id] = response_path
                    break
                if not retryable:
                    raise BroadMediaFollowupError(f"{spec.request_id} ended with {outcome}")
                if attempts_used < maximum_attempts:
                    retry_delay = max(retry_after or 0.0, retry_base * float(2 ** (attempt - 1)))
                    if retry_delay > maximum_wait:
                        raise BroadMediaFollowupError("retry delay exceeds the frozen wait ceiling")
                    time.sleep(retry_delay)
            if terminal is None or terminal.get("outcome") != "success":
                raise BroadMediaFollowupError(f"{spec.request_id} exhausted its frozen attempts")
            receipts.append(
                {
                    "request_id": spec.request_id,
                    "stage": spec.stage,
                    "status": "verified_success_event",
                    "attempt": terminal["attempt"],
                    "response_sha256": terminal["response_sha256"],
                    "response_bytes": terminal["response_bytes"],
                    "response_body_path": terminal["response_body_path"],
                }
            )
    return receipts, response_paths


def _followup_attempt_maps(
    events: Sequence[Mapping[str, Any]],
    specs: Mapping[str, fc.RequestSpec],
    workspace: Path,
    request: Mapping[str, Any],
) -> tuple[
    dict[tuple[str, int], Mapping[str, Any]],
    dict[tuple[str, int], Mapping[str, Any]],
]:
    maximum_attempts = int(request["maximum_attempts"])
    if any(
        not isinstance(row.get("attempt"), int)
        or isinstance(row.get("attempt"), bool)
        or not 1 <= row["attempt"] <= maximum_attempts
        for row in events[1:]
    ):
        raise BroadMediaFollowupError("event ledger exceeds the frozen attempt ceiling")
    starts, finishes = fc._attempt_maps(events, specs, workspace)
    retryable_http = {int(value) for value in request["retryable_http_status_codes"]}
    retryable_api = {str(value).casefold() for value in request["retryable_api_error_codes"]}
    retry_base = float(request["retry_backoff_base_seconds"])
    maximum_wait = float(request["maximum_retry_wait_seconds"])
    for row in finishes.values():
        outcome = row.get("outcome")
        if outcome == "retryable_http_error" and row.get("status_code") not in retryable_http:
            raise BroadMediaFollowupError("ledger retries an unfrozen HTTP status")
        if outcome == "terminal_http_error" and row.get("status_code") in retryable_http:
            raise BroadMediaFollowupError("ledger terminalizes a frozen retryable HTTP status")
        if outcome == "retryable_api_error" and row.get("api_error_code") not in retryable_api:
            raise BroadMediaFollowupError("ledger retries an unfrozen API error code")
        if outcome == "terminal_api_error" and row.get("api_error_code") in retryable_api:
            raise BroadMediaFollowupError("ledger terminalizes a frozen retryable API error code")
        if row.get("retryable") is True:
            retry_after = float(row.get("retry_after_seconds") or 0.0)
            frozen_delay = max(
                retry_after,
                retry_base * float(2 ** (int(row["attempt"]) - 1)),
            )
            if frozen_delay > maximum_wait:
                raise BroadMediaFollowupError("ledger exceeds the frozen retry wait ceiling")
    if any(row.get("outcome") == "transport_error" for row in finishes.values()):
        raise BroadMediaFollowupError(
            "retryable transport_error is invalid for this follow-up; "
            "an unknown network outcome requires a new reviewed census ID"
        )
    return starts, finishes


def _binding(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "authorization_seal_path": _relative(root, seal_path),
        "authorization_seal_sha256": seal_sha256,
        "freeze_path": authorization["seal"]["freeze_path"],
        "freeze_sha256": authorization["seal"]["freeze_sha256"],
        "review_path": authorization["seal"]["review_path"],
        "review_sha256": authorization["seal"]["review_sha256"],
        "config_path": _relative(root, config_path),
        "config_sha256": _freeze_sha(authorization["freeze"], _relative(root, config_path)),
        "request_intents_path": authorization["config"]["paths"]["planned_requests"],
        "request_intents_sha256": authorization["intent_sha256"],
        "frozen_input_set_sha256": authorization["freeze"]["frozen_input_set_sha256"],
        "authorization_scope": _SCOPE,
    }


def _ensure_genesis(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    authorization: Mapping[str, Any],
) -> list[dict[str, Any]]:
    config = authorization["config"]
    event_path = _repo_path(root, config["paths"]["request_events"], "events")
    events = fc._load_event_ledger(event_path, str(config["census_id"]))
    binding = _binding(root, config_path, seal_path, seal_sha256, authorization)
    if not events:
        lock_path = _repo_path(
            root,
            str(Path(str(config["paths"]["workspace"])) / ".execution.lock"),
            "execution lock",
        )
        for output in authorization["freeze"]["preexecution_outputs"]:
            output_path = _repo_path(root, output["path"], "preexecution output")
            if output_path != lock_path and output_path.exists():
                raise BroadMediaFollowupError("preexecution output is not absent")
        started_at = _enforce_cutoff(config)
        return [
            fc._append_event(
                event_path,
                str(config["census_id"]),
                [],
                {"event_type": "execution_started", "started_at_utc": started_at, **binding},
            )
        ]
    if events[0].get("event_type") != "execution_started" or any(
        events[0].get(key) != value for key, value in binding.items()
    ):
        raise BroadMediaFollowupError("existing genesis differs from authorization")
    cutoff = datetime.fromisoformat(
        str(config["request_contract"]["execution_start_not_after_utc"]).replace("Z", "+00:00")
    )
    started = fc._parse_media_timestamp(events[0].get("started_at_utc"))
    if started is None or started >= cutoff:
        raise BroadMediaFollowupError("existing genesis started at or after the cutoff")
    return events


def _receipt(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    authorization: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
    provider_times: Sequence[str],
    manifest_path: Path,
    manifest_sha256: str,
    manifest: Sequence[Mapping[str, Any]],
    completed_at: str,
) -> dict[str, Any]:
    config = authorization["config"]
    event_path = _repo_path(root, config["paths"]["request_events"], "events")
    return {
        "schema_version": _RECEIPT_SCHEMA,
        "status": "broad_media_followup_complete_not_authority_or_image_acquisition",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "completed_at_utc": completed_at,
        "authorization_seal_path": _relative(root, seal_path),
        "authorization_seal_sha256": seal_sha256,
        "config_path": _relative(root, config_path),
        "config_sha256": _freeze_sha(authorization["freeze"], _relative(root, config_path)),
        "request_intents_path": config["paths"]["planned_requests"],
        "request_intents_sha256": authorization["intent_sha256"],
        "request_event_ledger_path": config["paths"]["request_events"],
        "request_event_ledger_sha256": hash_file(event_path),
        "execution_genesis_event_sha256": events[0]["event_sha256"],
        "terminal_request_event_sha256": events[-1]["event_sha256"],
        "request_event_count": len(events),
        "successful_requests": len(authorization["specs"]),
        "provider_observation_window_utc": {
            "first_batch_timestamp": min(provider_times),
            "last_batch_timestamp": max(provider_times),
        },
        "raw_response_inventory": list(inventory),
        "candidate_manifest_path": config["paths"]["candidate_manifest"],
        "candidate_manifest_sha256": manifest_sha256,
        "counts": fc.summarize_manifest(manifest),
        "active_study_counts": {"downloaded_images": 0, "admitted_physical_works": 0},
        "limitations": [
            (
                "This is a complete current Wikidata/Commons follow-up of the broad "
                "discovery output, not a museum authority census."
            ),
            (
                "Commons rights markers and reported geometry are screening evidence, "
                "not image acquisition or decode evidence."
            ),
            (
                "No physical-work deduplication, content coding, image download, or "
                "active-study admission occurred."
            ),
        ],
    }


def execute(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    config_path = config_path.resolve()
    seal_path = seal_path.resolve()
    _relative(root, config_path)
    _relative(root, seal_path)
    authorization = _validate_authorization(root, config_path, seal_path, seal_sha256)
    config = authorization["config"]
    workspace = _repo_path(root, config["paths"]["workspace"], "workspace")
    receipt_path = _repo_path(root, config["paths"]["execution_receipt"], "receipt")
    manifest_path = _repo_path(root, config["paths"]["candidate_manifest"], "manifest")
    event_path = _repo_path(root, config["paths"]["request_events"], "events")
    publication_root = manifest_path.parent
    existing_events = fc._load_event_ledger(event_path, str(config["census_id"]))
    if not existing_events:
        if event_path.exists():
            raise BroadMediaFollowupError("empty preexisting event ledger is not clean")
        for output in authorization["freeze"]["preexecution_outputs"]:
            if _repo_path(root, output["path"], "preexecution output").exists():
                raise BroadMediaFollowupError("preexecution output is not absent")
    with fc._exclusive_execution_lock(workspace):
        events = _ensure_genesis(root, config_path, seal_path, seal_sha256, authorization)
        receipts, response_paths = _execute_specs(
            root,
            config,
            authorization["specs"],
            workspace,
            events,
            transport=transport,
        )
        events = fc._load_event_ledger(event_path, str(config["census_id"]))
        inventory, verified_paths, _ = fc._verified_success_inventory(
            authorization["specs"], events, workspace
        )
        if receipts != inventory or response_paths != verified_paths:
            raise BroadMediaFollowupError("response inventory differs from ledger verification")
        payloads, digests, provider_times = _load_verified_payloads(
            authorization["specs"], inventory, response_paths
        )
        entities = _parse_entity_payloads(authorization["specs"], payloads, digests)
        media = _parse_media_payloads(authorization["specs"], payloads, digests, config)
        manifest = fc.build_candidate_manifest(authorization["rows"], entities, media, config)
        if any(row.get("active_study_admission") is not False for row in manifest):
            raise BroadMediaFollowupError("manifest overstates active-study admission")
        manifest_body = "".join(canonical_json(row) + "\n" for row in manifest).encode()
        manifest_sha256 = hashlib.sha256(manifest_body).hexdigest()
        receipt = _receipt(
            root,
            config_path,
            seal_path,
            seal_sha256,
            authorization,
            events,
            inventory,
            provider_times,
            manifest_path,
            manifest_sha256,
            manifest,
            fc._utc_now(),
        )
        if publication_root.exists():
            raise BroadMediaFollowupError("atomic publication root already exists")
        publication_root.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{publication_root.name}.", dir=publication_root.parent)
        )
        try:
            temporary_manifest = temporary / manifest_path.name
            temporary_receipt = temporary / receipt_path.name
            fc._write_jsonl_atomic(temporary_manifest, manifest)
            if hash_file(temporary_manifest) != manifest_sha256:
                raise BroadMediaFollowupError("temporary manifest serialization drifted")
            fc._write_json_atomic(temporary_receipt, receipt)
            os.replace(temporary, publication_root)
            directory = os.open(publication_root.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except BaseException:
            if temporary.exists():
                shutil.rmtree(temporary)
            raise
        return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--seal", type=Path, required=True)
    execute_parser.add_argument("--seal-sha256", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    config_path = _repo_path(root, str(args.config), "config")
    if args.command == "prepare":
        print(json.dumps(prepare(root, config_path), indent=2, sort_keys=True))
        return 0
    seal_path = _repo_path(root, str(args.seal), "seal")
    result = execute(root, config_path, seal_path, args.seal_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
