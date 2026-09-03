from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import federated_census as fc


class AICMetadataError(fc.CensusError):
    """Raised when the prospective AIC metadata contract fails closed."""


_CONFIG_SCHEMA = "painter-feature-generation-v1-aic-metadata-config/1.0"
_INTENT_SCHEMA = "painter-feature-generation-v1-aic-metadata-intent/1.0"
_FREEZE_SCHEMA = "painter-feature-generation-v1-aic-metadata-freeze/1.0"
_REVIEW_SCHEMA = "painter-feature-generation-v1-aic-metadata-review/1.0"
_AUTH_SCHEMA = "painter-feature-generation-v1-aic-metadata-authorization/1.0"
_CANDIDATE_SCHEMA = "painter-feature-generation-v1-aic-authority-candidate/1.0"
_RECEIPT_SCHEMA = "painter-feature-generation-v1-aic-metadata-execution/1.0"
_EVENT_SCHEMA = "painter-feature-generation-v1-aic-metadata-event/1.0"
_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "visual_coding": False,
    "active_study_admission": False,
    "feature_extraction": False,
    "generation": False,
}
_FIELDS = (
    "id",
    "title",
    "api_link",
    "artist_id",
    "artist_title",
    "alt_artist_ids",
    "artist_ids",
    "artist_titles",
    "artist_display",
    "date_start",
    "date_end",
    "date_display",
    "artwork_type_id",
    "artwork_type_title",
    "classification_id",
    "classification_title",
    "medium_display",
    "dimensions",
    "main_reference_number",
    "is_public_domain",
    "copyright_notice",
    "image_id",
    "thumbnail",
    "subject_titles",
    "style_titles",
    "place_of_origin",
    "provenance_text",
    "credit_line",
    "timestamp",
)
_PAINTERS = [
    ("claude_monet", "Claude Monet", 35809),
    ("alfred_sisley", "Alfred Sisley", 36707),
    ("camille_pissarro", "Camille Pissarro", 36211),
    ("paul_cezanne", "Paul Cezanne", 40482),
]


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise AICMetadataError(f"{label} must be a repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise AICMetadataError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise AICMetadataError(f"{label} escapes the repository") from exc
    return path


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise AICMetadataError("path is outside the repository") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_hashed(path: Path, expected: Any, label: str) -> bytes:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise AICMetadataError(f"{label} cannot be read") from exc
    if not isinstance(expected, str) or _sha256(body) != expected:
        raise AICMetadataError(f"{label} hash mismatch")
    return body


def _json_object(body: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AICMetadataError(f"{label} is not JSON") from exc
    if not isinstance(value, dict):
        raise AICMetadataError(f"{label} is not an object")
    return value


def _jsonl_objects(body: bytes, label: str) -> list[dict[str, Any]]:
    try:
        lines = body.decode().splitlines()
    except UnicodeDecodeError as exc:
        raise AICMetadataError(f"{label} is not UTF-8") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line:
            raise AICMetadataError(f"{label} has a blank row at {number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AICMetadataError(f"{label} row {number} is not JSON") from exc
        if not isinstance(value, dict):
            raise AICMetadataError(f"{label} row {number} is not an object")
        rows.append(value)
    return rows


def _parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise AICMetadataError(f"{label} must be UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AICMetadataError(f"{label} is invalid") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise AICMetadataError(f"{label} is not UTC")
    return parsed


def _load_config_bytes(
    root: Path, config_path: Path, body: bytes, protocol_body: bytes | None = None
) -> dict[str, Any]:
    _relative(root, config_path)
    config = _json_object(body, "config")
    if config.get("schema_version") != _CONFIG_SCHEMA:
        raise AICMetadataError("unsupported AIC metadata config")
    protocol = _repo_path(root, config.get("protocol_path"), "protocol_path")
    if protocol_body is None:
        try:
            protocol_body = protocol.read_bytes()
        except OSError as exc:
            raise AICMetadataError("protocol cannot be read") from exc
    try:
        protocol_text = protocol_body.decode()
    except UnicodeDecodeError as exc:
        raise AICMetadataError("protocol is not UTF-8") from exc
    match = re.search(r"^Protocol ID: `([^`]+)`$", protocol_text, re.MULTILINE)
    if not match or config.get("protocol_id") != match.group(1):
        raise AICMetadataError("config differs from the canonical protocol")
    source = config.get("source_contract")
    screening = config.get("screening_contract")
    paths = config.get("paths")
    if not isinstance(source, Mapping) or not isinstance(screening, Mapping):
        raise AICMetadataError("source and screening contracts must be objects")
    if not isinstance(paths, Mapping):
        raise AICMetadataError("paths must be an object")
    if (
        source.get("source_id") != "art_institute_of_chicago"
        or source.get("endpoint") != "https://api.artic.edu/api/v1/artworks/search"
        or source.get("method") != "GET"
        or source.get("authentication") != "none"
        or source.get("redirects") != "forbidden"
        or source.get("accept") != "application/json"
        or config.get("scope") != _SCOPE
    ):
        raise AICMetadataError("AIC source or scope contract is invalid")
    for key in (
        "api_version_contract",
        "expected_api_version",
        "expected_iiif_base_url",
        "query_rule",
        "pagination_rule",
        "terminal_condition",
        "canonicalization_rule",
        "duplicate_rule",
        "rights_rule",
        "raw_response_rule",
        "rate_limit_rule",
        "retry_rule",
        "failure_rule",
    ):
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise AICMetadataError(f"source contract lacks {key}")
    interval = source.get("minimum_interval_seconds")
    timeout = source.get("timeout_seconds")
    maximum_bytes = source.get("maximum_response_bytes")
    if not isinstance(interval, (int, float)) or not 0.5 <= float(interval) <= 30:
        raise AICMetadataError("minimum interval is invalid")
    if not isinstance(timeout, (int, float)) or not 5 <= float(timeout) <= 120:
        raise AICMetadataError("timeout is invalid")
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or not 1_048_576 <= maximum_bytes <= 52_428_800
    ):
        raise AICMetadataError("maximum response size is invalid")
    if (
        source.get("expected_api_version") != "1.15"
        or source.get("expected_iiif_base_url") != "https://www.artic.edu/iiif/2"
    ):
        raise AICMetadataError("AIC API or IIIF version contract is invalid")
    _parse_utc(source.get("execution_start_not_after_utc"), "execution cutoff")
    if tuple(config.get("requested_fields", [])) != _FIELDS:
        raise AICMetadataError("requested fields differ from the exact AIC contract")
    painters = config.get("painters")
    if not isinstance(painters, list) or len(painters) != 4:
        raise AICMetadataError("exactly four painters are required")
    observed: list[tuple[str, str, int]] = []
    for row in painters:
        if not isinstance(row, Mapping):
            raise AICMetadataError("painter row is not an object")
        painter_id = row.get("painter_id")
        name = row.get("artist_name")
        agent_id = row.get("aic_agent_id")
        if not isinstance(painter_id, str) or not isinstance(name, str):
            raise AICMetadataError("painter identity is malformed")
        if isinstance(agent_id, bool) or not isinstance(agent_id, int):
            raise AICMetadataError("AIC agent ID is malformed")
        observed.append((painter_id, name, agent_id))
    if observed != _PAINTERS:
        raise AICMetadataError("painter roster differs from the prospective contract")
    if (
        screening.get("painting_tokens") != ["painting"]
        or screening.get("required_medium_tokens") != ["oil", "canvas"]
        or screening.get("minimum_reported_short_side") != 1024
        or not isinstance(screening.get("candidate_gate"), str)
        or not isinstance(screening.get("authority_ceiling"), str)
        or not isinstance(screening.get("malformed_field_rule"), str)
    ):
        raise AICMetadataError("screening contract is invalid")
    expected_path_keys = {
        "request_intents",
        "request_events",
        "publication_directory",
        "candidate_manifest",
        "execution_receipt",
        "workspace",
    }
    if set(paths) != expected_path_keys:
        raise AICMetadataError("path contract has unexpected keys")
    resolved = {key: _repo_path(root, value, f"paths.{key}") for key, value in paths.items()}
    publication = resolved["publication_directory"]
    if (
        resolved["candidate_manifest"].parent != publication
        or resolved["execution_receipt"].parent != publication
        or publication == root.resolve()
    ):
        raise AICMetadataError("publication paths do not share their declared directory")
    if len(set(resolved.values())) != len(resolved) or any(
        resolved["workspace"] in path.parents
        for key, path in resolved.items()
        if key != "workspace"
    ):
        raise AICMetadataError("declared paths overlap")
    return config


def load_config(root: Path, config_path: Path) -> dict[str, Any]:
    try:
        body = config_path.resolve().read_bytes()
    except OSError as exc:
        raise AICMetadataError("config cannot be read") from exc
    return _load_config_bytes(root, config_path.resolve(), body)


def build_intents(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    endpoint = str(config["source_contract"]["endpoint"])
    fields = ",".join(config["requested_fields"])
    rows: list[dict[str, Any]] = []
    for sequence, painter in enumerate(config["painters"], start=1):
        params = {
            "fields": fields,
            "limit": "100",
            "page": "1",
            "query[term][artist_ids]": str(painter["aic_agent_id"]),
        }
        encoded_url = str(httpx.Request("GET", endpoint, params=params).url)
        rows.append(
            {
                "schema_version": _INTENT_SCHEMA,
                "census_id": config["census_id"],
                "request_id": f"aic-artist-{sequence:04d}",
                "sequence": sequence,
                "method": "GET",
                "endpoint": endpoint,
                "params": params,
                "encoded_url": encoded_url,
                "painter_id": painter["painter_id"],
                "artist_name": painter["artist_name"],
                "aic_agent_id": painter["aic_agent_id"],
            }
        )
    return rows


def prepare(root: Path, config_path: Path) -> dict[str, Any]:
    config = load_config(root, config_path)
    path = _repo_path(root, config["paths"]["request_intents"], "request_intents")
    rows = build_intents(config)
    fc._write_jsonl_atomic(path, rows)
    return {
        "census_id": config["census_id"],
        "requests": len(rows),
        "request_intents_path": _relative(root, path),
        "request_intents_sha256": hash_file(path),
    }


def required_frozen_paths(root: Path, config_path: Path, config: Mapping[str, Any]) -> list[str]:
    paths = {
        ".gitignore",
        _relative(root, config_path),
        str(config["protocol_path"]),
        str(config["paths"]["request_intents"]),
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_aic_metadata.py",
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/aic_metadata.py",
        "src/latent_art_bench/painter_feature_generation_v1/federated_census.py",
        "tests/conftest.py",
        "tests/painter_feature_generation_v1/test_aic_metadata.py",
    }
    for path in paths:
        if not _repo_path(root, path, "frozen input").is_file():
            raise AICMetadataError(f"required frozen input is missing: {path}")
    return sorted(paths)


def expected_outputs(config: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = config["paths"]
    workspace = Path(str(paths["workspace"]))
    return [
        {"path": str(paths["request_events"]), "state": "absent"},
        {"path": str(paths["candidate_manifest"]), "state": "absent"},
        {"path": str(paths["execution_receipt"]), "state": "absent"},
        {"path": str(paths["publication_directory"]), "state": "absent"},
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
        raise AICMetadataError(f"freeze does not uniquely bind {path}")
    return matches[0]


def validate_authorization(
    root: Path, config_path: Path, seal_path: Path, seal_sha256: str
) -> dict[str, Any]:
    _relative(root, seal_path)
    seal = _json_object(_read_hashed(seal_path, seal_sha256, "authorization"), "authorization")
    freeze_path = _repo_path(root, seal.get("freeze_path"), "freeze")
    freeze = _json_object(
        _read_hashed(freeze_path, seal.get("freeze_sha256"), "freeze"), "freeze"
    )
    entries = freeze.get("frozen_inputs")
    if not isinstance(entries, list):
        raise AICMetadataError("freeze inputs are not a list")
    frozen_bodies: dict[str, bytes] = {}
    for row in entries:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            raise AICMetadataError("freeze input row is malformed")
        path = str(row["path"])
        if path in frozen_bodies:
            raise AICMetadataError("freeze input path is duplicated")
        frozen_bodies[path] = _read_hashed(
            _repo_path(root, path, "frozen input"), row.get("sha256"), "frozen input"
        )
    config_relative = _relative(root, config_path)
    config_body = frozen_bodies.get(config_relative)
    if config_body is None:
        raise AICMetadataError("freeze does not bind the config")
    config_preparse = _json_object(config_body, "config")
    protocol_relative = config_preparse.get("protocol_path")
    if not isinstance(protocol_relative, str) or protocol_relative not in frozen_bodies:
        raise AICMetadataError("freeze does not bind the protocol")
    config = _load_config_bytes(
        root, config_path, config_body, frozen_bodies[protocol_relative]
    )
    required = required_frozen_paths(root, config_path, config)
    if (
        seal.get("schema_version") != _AUTH_SCHEMA
        or seal.get("status") != "authorized_for_aic_metadata_execution"
        or seal.get("census_id") != config["census_id"]
        or seal.get("protocol_id") != config["protocol_id"]
        or seal.get("authorization_scope") != _SCOPE
        or freeze.get("schema_version") != _FREEZE_SCHEMA
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != _SCOPE
        or [row.get("path") for row in entries] != required
        or freeze.get("preexecution_outputs") != expected_outputs(config)
    ):
        raise AICMetadataError("authorization or freeze semantics are invalid")
    if _sha256(canonical_json(entries).encode()) != freeze.get("frozen_input_set_sha256"):
        raise AICMetadataError("freeze aggregate mismatch")
    review_path = _repo_path(root, seal.get("review_path"), "review")
    review = _json_object(
        _read_hashed(review_path, seal.get("review_sha256"), "review"), "review"
    )
    if (
        review.get("schema_version") != _REVIEW_SCHEMA
        or review.get("decision") != "APPROVE_AIC_METADATA_ONLY"
        or review.get("blocking_findings") != []
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or review.get("approved_scope") != _SCOPE
        or review.get("reviewed_freeze_path") != seal.get("freeze_path")
        or review.get("reviewed_freeze_sha256") != seal.get("freeze_sha256")
    ):
        raise AICMetadataError("review is invalid")
    intent_path = str(config["paths"]["request_intents"])
    intent_body = frozen_bodies.get(intent_path)
    if intent_body is None or _sha256(intent_body) != _freeze_sha(freeze, intent_path):
        raise AICMetadataError("freeze does not bind request intents")
    intents = _jsonl_objects(intent_body, "request intents")
    if intents != build_intents(config) or len(intents) != 4:
        raise AICMetadataError("request intents differ from reconstruction")
    return {"seal": seal, "freeze": freeze, "review": review, "config": config, "intents": intents}


def _normalized_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_like = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]+", " ", ascii_like.casefold()).strip()


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _word_tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z]+", unicodedata.normalize("NFKD", value).casefold()))


def parse_result(
    payload: Any, intent: Mapping[str, Any], response_sha256: str
) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        raise AICMetadataError("AIC response is not an object")
    required_top = {"pagination", "data", "info", "config"}
    allowed_top = required_top | {"preference"}
    if not required_top.issubset(payload) or not set(payload).issubset(allowed_top):
        raise AICMetadataError("AIC response has unexpected top-level fields")
    pagination = payload["pagination"]
    data = payload["data"]
    info = payload["info"]
    provider_config = payload["config"]
    if not isinstance(pagination, Mapping) or not isinstance(data, list):
        raise AICMetadataError("AIC response lacks pagination or data")
    for key in ("total", "limit", "offset", "total_pages", "current_page"):
        if isinstance(pagination.get(key), bool) or not isinstance(pagination.get(key), int):
            raise AICMetadataError(f"AIC pagination {key} is not an integer")
    if (
        pagination["total"] != len(data)
        or pagination["offset"] != 0
        or pagination["current_page"] != 1
        or pagination["limit"] != 100
        or pagination["total_pages"] != (0 if pagination["total"] == 0 else 1)
        or len(data) > 100
    ):
        raise AICMetadataError("AIC response is not a complete one-page census")
    if not isinstance(info, Mapping) or info.get("version") != "1.15":
        raise AICMetadataError("AIC response lacks an API version")
    if (
        not isinstance(provider_config, Mapping)
        or provider_config.get("iiif_url") != "https://www.artic.edu/iiif/2"
    ):
        raise AICMetadataError("AIC response lacks an IIIF base URL")
    records: list[dict[str, Any]] = []
    ids: list[int] = []
    for item in data:
        if not isinstance(item, Mapping):
            raise AICMetadataError("AIC data row is not an object")
        artwork_id = _positive_int(item.get("id"))
        preferred_artist_id = _positive_int(item.get("artist_id"))
        preferred_artist_title = item.get("artist_title")
        artist_ids = item.get("artist_ids")
        artist_titles = item.get("artist_titles")
        if (
            artwork_id is None
            or (item.get("artist_id") is not None and preferred_artist_id is None)
            or (
                preferred_artist_title is not None
                and not isinstance(preferred_artist_title, str)
            )
            or not isinstance(artist_ids, list)
            or not isinstance(artist_titles, list)
            or len(artist_ids) != len(artist_titles)
            or any(_positive_int(value) is None for value in artist_ids)
            or any(not isinstance(value, str) for value in artist_titles)
        ):
            raise AICMetadataError("AIC row violates the exact artist identity query")
        required_strings = ("title", "api_link")
        optional_strings = (
            "artist_display",
            "date_display",
            "artwork_type_title",
            "classification_title",
            "medium_display",
            "dimensions",
            "main_reference_number",
            "copyright_notice",
            "image_id",
            "place_of_origin",
            "provenance_text",
            "credit_line",
            "timestamp",
        )
        optional_integers = (
            "date_start",
            "date_end",
            "artwork_type_id",
            "classification_id",
        )
        if any(not isinstance(item.get(key), str) for key in required_strings):
            raise AICMetadataError("AIC row has a malformed required string")
        if any(
            item.get(key) is not None and not isinstance(item.get(key), str)
            for key in optional_strings
        ):
            raise AICMetadataError("AIC row has a malformed optional string")
        if any(
            item.get(key) is not None and _positive_int(item.get(key)) is None
            for key in optional_integers
        ):
            raise AICMetadataError("AIC row has a malformed optional integer")
        if not isinstance(item.get("is_public_domain"), bool):
            raise AICMetadataError("AIC row has a malformed public-domain flag")
        alt_artist_ids = item.get("alt_artist_ids")
        if alt_artist_ids is not None and (
            not isinstance(alt_artist_ids, list)
            or any(_positive_int(value) is None for value in alt_artist_ids)
        ):
            raise AICMetadataError("AIC row has malformed alternate artist IDs")
        for key in ("subject_titles", "style_titles"):
            value = item.get(key)
            if value is not None and (
                not isinstance(value, list)
                or any(not isinstance(cell, str) for cell in value)
            ):
                raise AICMetadataError(f"AIC row has malformed {key}")
        matching_indexes = [
            index for index, value in enumerate(artist_ids) if value == intent["aic_agent_id"]
        ]
        if len(matching_indexes) != 1 or _normalized_name(
            artist_titles[matching_indexes[0]]
        ) != _normalized_name(str(intent["artist_name"])):
            raise AICMetadataError("AIC row violates the exact artist identity query")
        ids.append(artwork_id)
        record = {field: item.get(field) for field in _FIELDS}
        record["id"] = artwork_id
        record["artist_id"] = preferred_artist_id
        record["artist_title"] = preferred_artist_title
        classification = " ".join(
            str(item.get(key) or "")
            for key in ("artwork_type_title", "classification_title")
        ).casefold()
        medium = str(item.get("medium_display") or "").casefold()
        accession = str(item.get("main_reference_number") or "").strip()
        image_id = str(item.get("image_id") or "").strip()
        thumbnail = item.get("thumbnail")
        width = height = None
        inline_lqip_present = False
        if isinstance(thumbnail, Mapping):
            width = _positive_int(thumbnail.get("width"))
            height = _positive_int(thumbnail.get("height"))
            inline_lqip_present = isinstance(thumbnail.get("lqip"), str) and bool(
                thumbnail.get("lqip")
            )
            if (
                (thumbnail.get("width") is not None and width is None)
                or (thumbnail.get("height") is not None and height is None)
                or (
                    thumbnail.get("alt_text") is not None
                    and not isinstance(thumbnail.get("alt_text"), str)
                )
            ):
                raise AICMetadataError("AIC row has malformed thumbnail geometry")
        elif thumbnail is not None:
            raise AICMetadataError("AIC row thumbnail is not an object or null")
        record["thumbnail"] = (
            {
                "width": width,
                "height": height,
                "alt_text": thumbnail.get("alt_text"),
                "provider_inline_lqip_present_but_not_published": inline_lqip_present,
            }
            if isinstance(thumbnail, Mapping)
            else None
        )
        short_side = min(width, height) if width is not None and height is not None else None
        exact_artist = True
        preferred_artist_match = preferred_artist_id == intent["aic_agent_id"]
        classification_words = _word_tokens(classification)
        medium_words = _word_tokens(medium)
        painting = "painting" in classification_words
        oil_canvas = {"oil", "canvas"}.issubset(medium_words)
        has_accession = bool(accession)
        public_domain = item.get("is_public_domain") is True
        has_image = bool(image_id)
        geometry = short_side is not None and short_side >= 1024
        authority_candidate = exact_artist and painting and oil_canvas and has_accession
        media_candidate = authority_candidate and public_domain and has_image and geometry
        records.append(
            {
                "schema_version": _CANDIDATE_SCHEMA,
                "census_id": intent["census_id"],
                "painter_id": intent["painter_id"],
                "artist_name": intent["artist_name"],
                "aic_agent_id": intent["aic_agent_id"],
                "aic_artwork_id": artwork_id,
                "source_request_id": intent["request_id"],
                "raw_response_sha256": response_sha256,
                "provider_api_version": info["version"],
                "provider_iiif_base_url": provider_config["iiif_url"],
                "field_presence": sorted(key for key in _FIELDS if key in item),
                "aic_record": record,
                "screening": {
                    "target_in_paired_artist_ids_and_titles": exact_artist,
                    "preferred_artist_matches_target": preferred_artist_match,
                    "painting_classification": painting,
                    "oil_and_canvas_tokens": oil_canvas,
                    "accession_present": has_accession,
                    "public_domain_flag": public_domain,
                    "image_id_present": has_image,
                    "reported_width": width,
                    "reported_height": height,
                    "provider_inline_lqip_present_but_not_published": inline_lqip_present,
                    "reported_short_side_at_least_1024": geometry,
                    "authority_record_candidate": authority_candidate,
                    "metadata_and_media_candidate": media_candidate,
                },
                "authority_status": "aic_holding_record_candidate_not_role_or_identity_reconciled",
                "image_status": "not_requested",
                "content_status": "not_blind_coded",
                "physical_work_identity_status": "not_reconciled",
                "active_study_admission": False,
            }
        )
    if len(ids) != len(set(ids)):
        raise AICMetadataError("AIC response contains duplicate artwork IDs")
    return records


def _claim_lock(workspace: Path, census_id: str, seal_sha256: str) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    path = workspace / ".execution.lock"
    body = (
        canonical_json(
            {
                "schema_version": "painter-feature-generation-v1-execution-lock/1.0",
                "census_id": census_id,
                "authorization_seal_sha256": seal_sha256,
                "claimed_at_utc": fc._utc_now(),
                "rule": "one-shot; never remove or resume; use a new reviewed census ID",
            }
        )
        + "\n"
    ).encode()
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise AICMetadataError("AIC census execution is already claimed") from exc
    try:
        remaining = memoryview(body)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("execution lock write made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(workspace, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return path


def _enforce_cutoff(config: Mapping[str, Any]) -> str:
    cutoff = _parse_utc(
        config["source_contract"]["execution_start_not_after_utc"], "execution cutoff"
    )
    started = datetime.now(timezone.utc)
    if started >= cutoff:
        raise AICMetadataError("AIC execution-start cutoff has passed")
    return started.isoformat().replace("+00:00", "Z")


def _headers(response: httpx.Response) -> dict[str, list[str]]:
    keys = ("date", "server", "content-type", "content-length", "retry-after", "x-request-id")
    return {key: response.headers.get_list(key) for key in keys if response.headers.get_list(key)}


def _bounded_body(response: httpx.Response, maximum_bytes: int) -> tuple[bytes, bool]:
    retained = bytearray()
    try:
        for chunk in response.iter_bytes():
            retained.extend(chunk[: maximum_bytes + 1 - len(retained)])
            if len(retained) > maximum_bytes:
                return bytes(retained), False
    finally:
        response.close()
    return bytes(retained), True


def _validate_date(values: Sequence[str] | None) -> None:
    if not values or len(values) != 1:
        raise AICMetadataError("AIC response must have one HTTP Date header")
    try:
        parsed = email.utils.parsedate_to_datetime(values[0])
    except (TypeError, ValueError, OverflowError) as exc:
        raise AICMetadataError("AIC response Date header is malformed") from exc
    if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AICMetadataError("AIC response Date header is not timezone-aware")


def _validate_events(events: Sequence[Mapping[str, Any]], census_id: str) -> None:
    previous = "0" * 64
    for sequence, event in enumerate(events, start=1):
        if (
            event.get("schema_version") != _EVENT_SCHEMA
            or event.get("census_id") != census_id
            or event.get("sequence") != sequence
            or event.get("previous_event_sha256") != previous
        ):
            raise AICMetadataError("event chain metadata is invalid")
        body = dict(event)
        observed = body.pop("event_sha256", None)
        if observed != _sha256(canonical_json(body).encode()):
            raise AICMetadataError("event chain hash is invalid")
        previous = str(observed)


def _append_event(
    path: Path,
    census_id: str,
    events: list[dict[str, Any]],
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    row = {
        "schema_version": _EVENT_SCHEMA,
        "census_id": census_id,
        "sequence": len(events) + 1,
        "previous_event_sha256": events[-1]["event_sha256"] if events else "0" * 64,
        **fields,
    }
    row["event_sha256"] = _sha256(canonical_json(row).encode())
    fc._append_jsonl(path, row)
    events.append(row)
    return row


def _validate_success_events(
    events: Sequence[Mapping[str, Any]],
    intents: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
) -> None:
    if (
        len(events) != 1 + 2 * len(intents)
        or len(inventory) != len(intents)
        or events[0].get("event_type") != "execution_started"
    ):
        raise AICMetadataError("successful event ledger has the wrong shape")
    previous_time = _parse_utc(events[0].get("started_at_utc"), "genesis timestamp")
    for index, intent in enumerate(intents):
        started = events[1 + 2 * index]
        finished = events[2 + 2 * index]
        started_time = _parse_utc(started.get("started_at_utc"), "request-start timestamp")
        finished_time = _parse_utc(
            finished.get("finished_at_utc"), "request-finish timestamp"
        )
        digest = finished.get("response_sha256")
        byte_count = finished.get("response_bytes")
        candidate_rows = finished.get("candidate_rows")
        expected_path = (
            f"response_bodies/{digest[:2]}/{digest}.response"
            if isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
            else None
        )
        expected_inventory = {
            "request_id": intent["request_id"],
            "response_sha256": digest,
            "response_bytes": byte_count,
            "response_body_path": expected_path,
            "candidate_rows": candidate_rows,
        }
        if (
            started.get("event_type") != "request_started"
            or started.get("request_id") != intent["request_id"]
            or started.get("encoded_url") != intent["encoded_url"]
            or finished.get("event_type") != "request_finished"
            or finished.get("request_id") != intent["request_id"]
            or finished.get("outcome") != "success"
            or started_time < previous_time
            or finished_time < started_time
            or finished.get("status_code") != 200
            or finished.get("final_url") != intent["encoded_url"]
            or finished.get("response_body_complete") is not True
            or finished.get("error") is not None
            or expected_path is None
            or finished.get("response_body_path") != expected_path
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count <= 0
            or isinstance(candidate_rows, bool)
            or not isinstance(candidate_rows, int)
            or candidate_rows < 0
            or dict(inventory[index]) != expected_inventory
        ):
            raise AICMetadataError("successful event ledger differs from frozen request order")
        headers = finished.get("response_headers")
        if not isinstance(headers, Mapping):
            raise AICMetadataError("successful event lacks response headers")
        _validate_date(headers.get("date"))
        content_types = headers.get("content-type")
        if (
            not isinstance(content_types, list)
            or len(content_types) != 1
            or content_types[0].split(";", 1)[0].strip() != "application/json"
            or headers.get("retry-after") is not None
        ):
            raise AICMetadataError("successful event has invalid response headers")
        previous_time = finished_time


def _publish(
    root: Path,
    config: Mapping[str, Any],
    candidates: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    paths = config["paths"]
    final_dir = _repo_path(root, paths["publication_directory"], "publication directory")
    if final_dir.exists():
        raise AICMetadataError("publication directory already exists")
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{final_dir.name}.", dir=final_dir.parent))
    try:
        candidate_tmp = temporary / Path(str(paths["candidate_manifest"])).name
        receipt_tmp = temporary / Path(str(paths["execution_receipt"])).name
        fc._write_jsonl_atomic(candidate_tmp, candidates)
        receipt["candidate_manifest_sha256"] = hash_file(candidate_tmp)
        fc._write_json_atomic(receipt_tmp, receipt)
        directory = os.open(temporary, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        os.replace(temporary, final_dir)
        parent = os.open(final_dir.parent, os.O_RDONLY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return receipt


def execute(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    authorization = validate_authorization(root, config_path, seal_path, seal_sha256)
    config = authorization["config"]
    intents = authorization["intents"]
    for output in expected_outputs(config):
        if _repo_path(root, output["path"], "preexecution output").exists():
            raise AICMetadataError(f"preexecution output is not absent: {output['path']}")
    started_at = _enforce_cutoff(config)
    paths = config["paths"]
    workspace = _repo_path(root, paths["workspace"], "workspace")
    event_path = _repo_path(root, paths["request_events"], "request events")
    lock = _claim_lock(workspace, config["census_id"], seal_sha256)
    events: list[dict[str, Any]] = []
    genesis = _append_event(
        event_path,
        config["census_id"],
        events,
        {
            "event_type": "execution_started",
            "started_at_utc": started_at,
            "authorization_seal_path": _relative(root, seal_path),
            "authorization_seal_sha256": seal_sha256,
            "freeze_path": authorization["seal"]["freeze_path"],
            "freeze_sha256": authorization["seal"]["freeze_sha256"],
            "review_path": authorization["seal"]["review_path"],
            "review_sha256": authorization["seal"]["review_sha256"],
            "request_intents_sha256": _freeze_sha(
                authorization["freeze"], str(paths["request_intents"])
            ),
            "execution_lock_path": _relative(root, lock),
            "execution_lock_sha256": hash_file(lock),
        },
    )
    source = config["source_contract"]
    candidates: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    with httpx.Client(
        timeout=float(source["timeout_seconds"]),
        follow_redirects=False,
        transport=transport,
        headers={
            "Accept": str(source["accept"]),
            "User-Agent": "latent-art-bench/0.1 painter-feature-generation-v1 AIC metadata census",
        },
    ) as client:
        last_access = 0.0
        for intent in intents:
            delay = float(source["minimum_interval_seconds"]) - (time.monotonic() - last_access)
            if delay > 0:
                time.sleep(delay)
            request = client.build_request("GET", intent["endpoint"], params=intent["params"])
            if str(request.url) != intent["encoded_url"]:
                raise AICMetadataError("HTTP encoding differs from the frozen intent")
            _append_event(
                event_path,
                config["census_id"],
                events,
                {
                    "event_type": "request_started",
                    "request_id": intent["request_id"],
                    "started_at_utc": fc._utc_now(),
                    "encoded_url": intent["encoded_url"],
                },
            )
            try:
                response = client.send(request, stream=True)
                body, response_body_complete = _bounded_body(
                    response, int(source["maximum_response_bytes"])
                )
            except Exception as exc:
                _append_event(
                    event_path,
                    config["census_id"],
                    events,
                    {
                        "event_type": "request_finished",
                        "request_id": intent["request_id"],
                        "finished_at_utc": fc._utc_now(),
                        "outcome": "terminal_transport_failure",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                raise AICMetadataError("AIC request failed terminally") from exc
            last_access = time.monotonic()
            digest = _sha256(body)
            body_path = workspace / "response_bodies" / digest[:2] / f"{digest}.response"
            fc._atomic_bytes(body_path, body)
            response_headers = _headers(response)
            outcome = "success"
            error: str | None = None
            rows: list[dict[str, Any]] = []
            try:
                _validate_date(response_headers.get("date"))
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
                if (
                    response.status_code != 200
                    or response.history
                    or str(response.url) != intent["encoded_url"]
                    or content_type != "application/json"
                    or "retry-after" in response_headers
                    or not response_body_complete
                ):
                    raise AICMetadataError(
                        "HTTP status, redirect, URL, content type, or Retry-After "
                        "violated the contract"
                    )
                rows = parse_result(json.loads(body), intent, digest)
                prior_ids = {row["aic_artwork_id"] for row in candidates}
                if any(row["aic_artwork_id"] in prior_ids for row in rows):
                    raise AICMetadataError(
                        "AIC artwork IDs overlap across painter responses"
                    )
            except Exception as exc:
                outcome = "terminal_delivery_or_schema_failure"
                error = str(exc)
            terminal = _append_event(
                event_path,
                config["census_id"],
                events,
                {
                    "event_type": "request_finished",
                    "request_id": intent["request_id"],
                    "finished_at_utc": fc._utc_now(),
                    "outcome": outcome,
                    "status_code": response.status_code,
                    "final_url": str(response.url),
                    "response_headers": response_headers,
                    "response_bytes": len(body),
                    "response_body_complete": response_body_complete,
                    "response_sha256": digest,
                    "response_body_path": str(body_path.relative_to(workspace)),
                    "candidate_rows": len(rows),
                    "error": error,
                },
            )
            if outcome != "success":
                raise AICMetadataError(
                    f"{intent['request_id']} ended with {terminal['outcome']}"
                )
            candidates.extend(rows)
            inventory.append(
                {
                    "request_id": intent["request_id"],
                    "response_sha256": digest,
                    "response_bytes": len(body),
                    "response_body_path": str(body_path.relative_to(workspace)),
                    "candidate_rows": len(rows),
                }
            )
    try:
        for response in inventory:
            cas_path = workspace / str(response["response_body_path"])
            verified = _read_hashed(
                cas_path, response["response_sha256"], "content-addressed response"
            )
            if len(verified) != response["response_bytes"]:
                raise AICMetadataError("content-addressed response byte count drifted")
    except AICMetadataError as exc:
        _append_event(
            event_path,
            config["census_id"],
            events,
            {
                "event_type": "execution_finished",
                "finished_at_utc": fc._utc_now(),
                "outcome": "terminal_cas_verification_failure",
                "error": str(exc),
            },
        )
        raise
    candidates.sort(key=lambda row: (row["painter_id"], row["aic_artwork_id"]))
    for sequence, row in enumerate(candidates, start=1):
        row["candidate_sequence"] = sequence
    try:
        event_body = event_path.read_bytes()
    except OSError as exc:
        raise AICMetadataError("event ledger cannot be reread") from exc
    disk_events = _jsonl_objects(event_body, "event ledger")
    _validate_events(disk_events, config["census_id"])
    _validate_success_events(disk_events, intents, inventory)
    if disk_events != events:
        raise AICMetadataError("event ledger differs from the in-memory chain")
    event_sha = _sha256(event_body)
    by_painter: dict[str, dict[str, int]] = {}
    for painter in config["painters"]:
        group = [row for row in candidates if row["painter_id"] == painter["painter_id"]]
        by_painter[painter["painter_id"]] = {
            "returned_rows": len(group),
            "authority_record_candidates": sum(
                row["screening"]["authority_record_candidate"] for row in group
            ),
            "metadata_and_media_candidates": sum(
                row["screening"]["metadata_and_media_candidate"] for row in group
            ),
        }
    receipt = {
        "schema_version": _RECEIPT_SCHEMA,
        "status": "aic_metadata_census_complete_not_image_acquisition",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "completed_at_utc": fc._utc_now(),
        "authorization_seal_path": _relative(root, seal_path),
        "authorization_seal_sha256": seal_sha256,
        "execution_genesis_event_sha256": genesis["event_sha256"],
        "terminal_event_sha256": events[-1]["event_sha256"],
        "request_event_ledger_path": _relative(root, event_path),
        "request_event_ledger_sha256": event_sha,
        "request_event_count": len(events),
        "successful_requests": len(intents),
        "response_inventory": inventory,
        "candidate_manifest_path": str(paths["candidate_manifest"]),
        "counts": {
            "returned_rows": len(candidates),
            "authority_record_candidates": sum(
                row["screening"]["authority_record_candidate"] for row in candidates
            ),
            "metadata_and_media_candidates": sum(
                row["screening"]["metadata_and_media_candidate"] for row in candidates
            ),
            "by_painter": by_painter,
            "active_study_admissions": 0,
            "image_downloads": 0,
        },
        "limitations": [
            "AIC query rows are authority candidates, not yet reconciled physical works.",
            (
                "The public-domain flag and image ID do not replace item-level delivery "
                "and rights receipts."
            ),
            (
                "No image endpoint or file was requested, no content label was assigned, and "
                "no work was admitted. Provider-embedded LQIP values in metadata responses "
                "remain only in the raw CAS and are neither decoded nor published."
            ),
            "Every other named Protocol 2.0 source route remains separately required.",
        ],
    }
    return _publish(root, config, candidates, receipt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/painter_feature_generation_v1/aic_metadata_census.json"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    execute_parser = subparsers.add_parser("execute")
    execute_parser.add_argument("--seal", type=Path, required=True)
    execute_parser.add_argument("--seal-sha256", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    config_path = _repo_path(root, str(args.config), "config")
    if args.command == "prepare":
        result = prepare(root, config_path)
    else:
        seal_path = _repo_path(root, str(args.seal), "seal")
        result = execute(root, config_path, seal_path, args.seal_sha256)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
