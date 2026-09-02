from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from latent_art_bench.io import canonical_json, hash_file


class BroadDiscoveryError(RuntimeError):
    """Raised when the broad Wikidata discovery contract fails closed."""


_CONFIG_SCHEMA = "painter-feature-generation-v1-broad-wikidata-config/1.0"
_INTENT_SCHEMA = "painter-feature-generation-v1-broad-wikidata-intent/1.0"
_EVENT_SCHEMA = "painter-feature-generation-v1-broad-wikidata-event/1.0"
_FREEZE_SCHEMA = "painter-feature-generation-v1-broad-wikidata-freeze/1.0"
_REVIEW_SCHEMA = "painter-feature-generation-v1-broad-wikidata-review/1.0"
_AUTH_SCHEMA = "painter-feature-generation-v1-broad-wikidata-authorization/1.0"
_CANDIDATE_SCHEMA = "painter-feature-generation-v1-broad-wikidata-candidate/1.0"
_RECEIPT_SCHEMA = "painter-feature-generation-v1-broad-wikidata-execution/1.0"
_METADATA_ONLY_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "active_study_admission": False,
    "visual_coding": False,
    "feature_extraction": False,
    "generation": False,
}
_QUERY_TEMPLATE = (
    "SELECT DISTINCT ?item ?image WHERE { ?item wdt:P170 wd:{creator_qid}; "
    "wdt:P31 wd:Q3305213; wdt:P18 ?image. } "
    "ORDER BY STR(?item) STR(?image)"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_bytes(path, (canonical_json(dict(value)) + "\n").encode())


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    body = "".join(canonical_json(dict(row)) + "\n" for row in rows).encode()
    _atomic_bytes(path, body)


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise BroadDiscoveryError(f"{label} must be a non-empty repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise BroadDiscoveryError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise BroadDiscoveryError(f"{label} escapes the repository") from exc
    return path


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise BroadDiscoveryError(f"path is outside repository: {path}") from exc


def load_config(root: Path, config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    _relative(root, config_path)
    config = json.loads(config_path.read_text())
    if config.get("schema_version") != _CONFIG_SCHEMA:
        raise BroadDiscoveryError("unsupported broad Wikidata config schema")
    protocol = _repo_path(root, config.get("protocol_path"), "protocol_path")
    match = re.search(
        r"^Protocol ID: `([^`]+)`$", protocol.read_text(), flags=re.MULTILINE
    )
    if not match or config.get("protocol_id") != match.group(1):
        raise BroadDiscoveryError("config protocol ID differs from canonical protocol")
    source = config.get("source_contract")
    if not isinstance(source, Mapping):
        raise BroadDiscoveryError("source_contract must be an object")
    if (
        source.get("endpoint") != "https://query.wikidata.org/sparql"
        or source.get("method") != "GET"
        or source.get("redirects") != "forbidden"
    ):
        raise BroadDiscoveryError("unsupported endpoint, method, or redirect contract")
    if config.get("scope") != _METADATA_ONLY_SCOPE:
        raise BroadDiscoveryError("scope must be exactly metadata-only")
    cutoff = source.get("request_not_after_utc")
    if not isinstance(cutoff, str) or not cutoff.endswith("Z"):
        raise BroadDiscoveryError("source contract lacks a UTC request cutoff")
    try:
        parsed_cutoff = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BroadDiscoveryError("source contract has an invalid UTC request cutoff") from exc
    if parsed_cutoff.utcoffset() != timezone.utc.utcoffset(parsed_cutoff):
        raise BroadDiscoveryError("source contract request cutoff is not UTC")
    for field in (
        "api_version",
        "data_version",
        "canonicalization_rule",
        "duplicate_rule",
        "raw_response_rule",
        "rights_and_media_rule",
    ):
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise BroadDiscoveryError(f"source contract lacks {field}")
    painters = config.get("painters")
    if not isinstance(painters, list) or len(painters) != 4:
        raise BroadDiscoveryError("exactly four painter records are required")
    ids = {row.get("painter_id") for row in painters if isinstance(row, Mapping)}
    qids = {row.get("creator_qid") for row in painters if isinstance(row, Mapping)}
    if len(ids) != 4 or len(qids) != 4 or any(
        not isinstance(value, str) for value in ids | qids
    ):
        raise BroadDiscoveryError("painter identifiers must be unique strings")
    if any(not re.fullmatch(r"Q[1-9][0-9]*", str(value)) for value in qids):
        raise BroadDiscoveryError("creator QID is malformed")
    template = config.get("query_template")
    if template != _QUERY_TEMPLATE:
        raise BroadDiscoveryError("query template differs from the exact no-P186 contract")
    return config


def build_intents(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = config["source_contract"]
    endpoint = str(source["endpoint"])
    template = str(config["query_template"])
    records: list[dict[str, Any]] = []
    for sequence, painter in enumerate(config["painters"], start=1):
        query = template.replace("{creator_qid}", str(painter["creator_qid"]))
        params = {"format": "json", "query": query}
        encoded_url = str(httpx.Request("GET", endpoint, params=params).url)
        records.append(
            {
                "schema_version": _INTENT_SCHEMA,
                "census_id": config["census_id"],
                "request_id": f"broad-wikidata-{sequence:04d}",
                "sequence": sequence,
                "method": "GET",
                "endpoint": endpoint,
                "params": params,
                "encoded_url": encoded_url,
                "painter_id": painter["painter_id"],
                "creator_qid": painter["creator_qid"],
                "material_filter_present": False,
            }
        )
    return records


def prepare(root: Path, config_path: Path) -> dict[str, Any]:
    config = load_config(root, config_path)
    path = _repo_path(root, config["paths"]["request_intents"], "request_intents")
    rows = build_intents(config)
    _write_jsonl(path, rows)
    return {
        "census_id": config["census_id"],
        "requests": len(rows),
        "intent_path": _relative(root, path),
        "intent_sha256": hash_file(path),
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BroadDiscoveryError(f"invalid JSONL at {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise BroadDiscoveryError(f"non-object JSONL row at {path}:{line_number}")
        rows.append(row)
    return rows


def load_intents(root: Path, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    path = _repo_path(root, config["paths"]["request_intents"], "request_intents")
    rows = _load_jsonl(path)
    if rows != build_intents(config):
        raise BroadDiscoveryError("request intents differ from deterministic reconstruction")
    return rows


def required_frozen_paths(root: Path, config: Mapping[str, Any], config_path: Path) -> list[str]:
    paths = {
        ".gitignore",
        _relative(root, config_path.resolve()),
        str(config["protocol_path"]),
        str(config["paths"]["request_intents"]),
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_broad_wikidata.py",
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/config.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/schemas.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_wikidata.py",
        "tests/conftest.py",
        "tests/painter_feature_generation_v1/test_broad_wikidata.py",
    }
    for path in paths:
        if not _repo_path(root, path, "frozen input").is_file():
            raise BroadDiscoveryError(f"required frozen input is missing: {path}")
    return sorted(paths)


def expected_outputs(root: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = config["paths"]
    return [
        {"path": str(paths[key]), "state": "absent"}
        for key in ("request_events", "candidate_manifest", "execution_receipt")
    ] + [
        {
            "path": str(Path(str(paths["workspace"])) / "execution.lock"),
            "state": "absent",
        },
        {
            "path": str(Path(str(paths["workspace"])) / "response_bodies"),
            "state": "absent",
        }
    ]


def validate_authorization(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    seal_path: Path,
    expected_seal_sha256: str,
) -> dict[str, Any]:
    if hash_file(seal_path) != expected_seal_sha256:
        raise BroadDiscoveryError("authorization seal hash mismatch")
    seal = json.loads(seal_path.read_text())
    if (
        seal.get("schema_version") != _AUTH_SCHEMA
        or seal.get("status") != "authorized_for_broad_wikidata_metadata_execution"
        or seal.get("census_id") != config["census_id"]
        or seal.get("protocol_id") != config["protocol_id"]
        or seal.get("authorization_scope") != config["scope"]
    ):
        raise BroadDiscoveryError("invalid broad Wikidata authorization seal")
    freeze_path = _repo_path(root, seal.get("freeze_path"), "freeze_path")
    if hash_file(freeze_path) != seal.get("freeze_sha256"):
        raise BroadDiscoveryError("freeze hash mismatch")
    freeze = json.loads(freeze_path.read_text())
    if (
        freeze.get("schema_version") != _FREEZE_SCHEMA
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != config["scope"]
        or freeze.get("preexecution_outputs") != expected_outputs(root, config)
    ):
        raise BroadDiscoveryError("invalid broad Wikidata freeze")
    entries = freeze.get("frozen_inputs")
    required = required_frozen_paths(root, config, config_path)
    if not isinstance(entries, list) or [row.get("path") for row in entries] != required:
        raise BroadDiscoveryError("freeze does not bind the exact required input set")
    for entry in entries:
        path = _repo_path(root, entry["path"], "frozen input")
        if hash_file(path) != entry.get("sha256"):
            raise BroadDiscoveryError(f"frozen input drift: {entry['path']}")
    digest = _sha256_bytes(canonical_json(entries).encode())
    if digest != freeze.get("frozen_input_set_sha256"):
        raise BroadDiscoveryError("frozen input aggregate mismatch")
    review_path = _repo_path(root, seal.get("review_path"), "review_path")
    if hash_file(review_path) != seal.get("review_sha256"):
        raise BroadDiscoveryError("quality review hash mismatch")
    review = json.loads(review_path.read_text())
    if (
        review.get("schema_version") != _REVIEW_SCHEMA
        or review.get("decision") != "APPROVE_BROAD_WIKIDATA_METADATA_ONLY"
        or review.get("blocking_findings") != []
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("reviewed_freeze_path") != seal.get("freeze_path")
        or review.get("reviewed_freeze_sha256") != seal.get("freeze_sha256")
        or review.get("approved_scope") != config["scope"]
    ):
        raise BroadDiscoveryError("quality review does not approve the exact freeze")
    return {"seal": seal, "freeze": freeze, "review": review}


def _append_event(
    path: Path, census_id: str, events: list[dict[str, Any]], payload: Mapping[str, Any]
) -> dict[str, Any]:
    row = {
        "schema_version": _EVENT_SCHEMA,
        "census_id": census_id,
        "sequence": len(events) + 1,
        "previous_event_sha256": events[-1]["event_sha256"] if events else None,
        **payload,
    }
    row["event_sha256"] = _sha256_bytes(canonical_json(row).encode())
    existing = path.read_bytes() if path.exists() else b""
    if existing and not existing.endswith(b"\n"):
        raise BroadDiscoveryError("event ledger is torn")
    _atomic_bytes(path, existing + (canonical_json(row) + "\n").encode())
    events.append(row)
    return row


def _validate_event_chain(events: Sequence[Mapping[str, Any]], census_id: str) -> None:
    previous: str | None = None
    for sequence, row in enumerate(events, start=1):
        if (
            row.get("schema_version") != _EVENT_SCHEMA
            or row.get("census_id") != census_id
            or row.get("sequence") != sequence
            or row.get("previous_event_sha256") != previous
        ):
            raise BroadDiscoveryError("event ledger chain metadata is invalid")
        observed = row.get("event_sha256")
        body = dict(row)
        body.pop("event_sha256", None)
        if observed != _sha256_bytes(canonical_json(body).encode()):
            raise BroadDiscoveryError("event ledger hash is invalid")
        previous = str(observed)


def _binding_value(binding: Mapping[str, Any], name: str) -> str:
    cell = binding.get(name)
    if (
        not isinstance(cell, Mapping)
        or set(cell) != {"type", "value"}
        or cell.get("type") != "uri"
    ):
        raise BroadDiscoveryError(f"SPARQL binding {name} is not a URI")
    value = cell.get("value")
    if not isinstance(value, str):
        raise BroadDiscoveryError(f"SPARQL binding {name} has no string value")
    return value


def parse_result(payload: Any, intent: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        raise BroadDiscoveryError("SPARQL response is not an object")
    if set(payload) != {"head", "results"}:
        raise BroadDiscoveryError("SPARQL response has unexpected top-level fields")
    head = payload.get("head")
    results = payload.get("results")
    if (
        not isinstance(head, Mapping)
        or set(head) != {"vars"}
        or head.get("vars") != ["item", "image"]
    ):
        raise BroadDiscoveryError("SPARQL response has unexpected variables")
    if (
        not isinstance(results, Mapping)
        or set(results) != {"bindings"}
        or not isinstance(results.get("bindings"), list)
    ):
        raise BroadDiscoveryError("SPARQL response lacks bindings")
    records: list[dict[str, Any]] = []
    order_keys: list[tuple[str, str]] = []
    canonical_keys: list[tuple[str, str]] = []
    for binding in results["bindings"]:
        if not isinstance(binding, Mapping) or set(binding) != {"item", "image"}:
            raise BroadDiscoveryError("SPARQL binding has unexpected fields")
        item_uri = _binding_value(binding, "item")
        image_uri = _binding_value(binding, "image")
        item_match = re.fullmatch(
            r"https?://www\.wikidata\.org/entity/(Q[1-9][0-9]*)", item_uri
        )
        marker = "/wiki/Special:FilePath/"
        try:
            parsed_image = urllib.parse.urlsplit(image_uri)
        except ValueError as exc:
            raise BroadDiscoveryError(
                "SPARQL result contains a malformed image URI"
            ) from exc
        if (
            item_match is None
            or parsed_image.scheme not in {"http", "https"}
            or parsed_image.netloc != "commons.wikimedia.org"
            or not parsed_image.path.startswith(marker)
            or parsed_image.query
            or parsed_image.fragment
        ):
            raise BroadDiscoveryError("SPARQL result contains an invalid item or image URI")
        raw_filename = parsed_image.path.split(marker, 1)[1]
        if (
            re.search(r"%(?![0-9A-Fa-f]{2})", raw_filename)
            or re.search(r'''[\\"<>\[\]|{}^`]''', raw_filename)
            or any(
                character.isspace() or not character.isprintable()
                for character in raw_filename
            )
        ):
            raise BroadDiscoveryError("SPARQL result contains an invalid Commons filename URI")
        try:
            filename = urllib.parse.unquote_to_bytes(raw_filename).decode(
                "utf-8", errors="strict"
            )
        except UnicodeDecodeError as exc:
            raise BroadDiscoveryError(
                "SPARQL result contains a non-UTF-8 Commons filename"
            ) from exc
        filename = filename.replace("_", " ")
        if (
            not filename
            or filename != filename.strip()
            or any(
                not character.isprintable()
                or character in "#<>[]|{}"
                for character in filename
            )
        ):
            raise BroadDiscoveryError("SPARQL result contains an invalid Commons filename")
        order_keys.append((item_uri, image_uri))
        canonical_keys.append((item_match.group(1), filename))
        records.append(
            {
                "schema_version": _CANDIDATE_SCHEMA,
                "census_id": intent["census_id"],
                "painter_id": intent["painter_id"],
                "creator_qid": intent["creator_qid"],
                "item_qid": item_match.group(1),
                "commons_filename": filename,
                "source_request_id": intent["request_id"],
                "discovery_status": "broad_no_p186_candidate_not_authority_verified",
                "active_study_admission": False,
            }
        )
    if order_keys != sorted(order_keys) or len(canonical_keys) != len(
        set(canonical_keys)
    ):
        raise BroadDiscoveryError("SPARQL bindings are unordered or duplicated")
    return records


def _claim_execution_lock(workspace: Path, census_id: str, seal_sha256: str) -> Path:
    """Atomically and permanently claim this one-shot census execution."""
    workspace.mkdir(parents=True, exist_ok=True)
    path = workspace / "execution.lock"
    payload = (
        canonical_json(
            {
                "schema_version": "painter-feature-generation-v1-execution-lock/1.0",
                "census_id": census_id,
                "authorization_seal_sha256": seal_sha256,
                "claimed_at_utc": _utc_now(),
                "rule": "one-shot; never resume or remove; use a new reviewed census ID",
            }
        )
        + "\n"
    ).encode()
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise BroadDiscoveryError("broad Wikidata census execution is already claimed") from exc
    try:
        os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(workspace, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return path


def _enforce_request_cutoff(source: Mapping[str, Any]) -> None:
    cutoff = datetime.fromisoformat(
        str(source["request_not_after_utc"]).replace("Z", "+00:00")
    )
    if datetime.now(timezone.utc) > cutoff:
        raise BroadDiscoveryError("broad Wikidata request cutoff has passed")


def _response_headers(response: httpx.Response) -> dict[str, list[str]]:
    return {
        key: response.headers.get_list(key)
        for key in ("date", "server", "content-length")
        if response.headers.get_list(key)
    }


def _validate_provider_date(headers: Mapping[str, list[str]]) -> None:
    values = headers.get("date", [])
    if len(values) != 1:
        raise BroadDiscoveryError("response must contain exactly one HTTP Date header")
    try:
        parsed = email.utils.parsedate_to_datetime(values[0])
    except (TypeError, ValueError) as exc:
        raise BroadDiscoveryError("response Date header is malformed") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BroadDiscoveryError("response Date header is not timezone-aware")


def execute(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    config = load_config(root, config_path)
    authorization = validate_authorization(
        root, config, config_path, seal_path.resolve(), seal_sha256
    )
    intents = load_intents(root, config)
    paths = config["paths"]
    event_path = _repo_path(root, paths["request_events"], "request_events")
    candidate_path = _repo_path(root, paths["candidate_manifest"], "candidate_manifest")
    receipt_path = _repo_path(root, paths["execution_receipt"], "execution_receipt")
    workspace = _repo_path(root, paths["workspace"], "workspace")
    for row in expected_outputs(root, config):
        if _repo_path(root, row["path"], "preexecution output").exists():
            raise BroadDiscoveryError(f"preexecution output is not absent: {row['path']}")
    source = config["source_contract"]
    _enforce_request_cutoff(source)
    lock_path = _claim_execution_lock(workspace, config["census_id"], seal_sha256)
    events: list[dict[str, Any]] = []
    genesis = _append_event(
        event_path,
        config["census_id"],
        events,
        {
            "event_type": "execution_started",
            "started_at_utc": _utc_now(),
            "authorization_seal_path": _relative(root, seal_path),
            "authorization_seal_sha256": seal_sha256,
            "freeze_path": authorization["seal"]["freeze_path"],
            "freeze_sha256": authorization["seal"]["freeze_sha256"],
            "request_intents_sha256": hash_file(
                _repo_path(root, paths["request_intents"], "request_intents")
            ),
            "execution_lock_path": str(lock_path.relative_to(workspace)),
            "execution_lock_sha256": hash_file(lock_path),
        },
    )
    all_candidates: list[dict[str, Any]] = []
    response_inventory: list[dict[str, Any]] = []
    with httpx.Client(
        timeout=float(source["timeout_seconds"]),
        follow_redirects=False,
        transport=transport,
        headers={
            "Accept": str(source["accept"]),
            "User-Agent": (
                "latent-art-bench/0.1 painter-feature-generation-v1 broad metadata census"
            ),
        },
    ) as client:
        last_access = 0.0
        for intent in intents:
            delay = float(source["minimum_interval_seconds"]) - (
                time.monotonic() - last_access
            )
            if delay > 0:
                time.sleep(delay)
            _enforce_request_cutoff(source)
            _append_event(
                event_path,
                config["census_id"],
                events,
                {
                    "event_type": "request_started",
                    "request_id": intent["request_id"],
                    "started_at_utc": _utc_now(),
                    "encoded_url": intent["encoded_url"],
                },
            )
            request = client.build_request("GET", intent["endpoint"], params=intent["params"])
            if str(request.url) != intent["encoded_url"]:
                raise BroadDiscoveryError("HTTP client encoding differs from frozen intent")
            try:
                _enforce_request_cutoff(source)
            except BroadDiscoveryError as exc:
                _append_event(
                    event_path,
                    config["census_id"],
                    events,
                    {
                        "event_type": "request_finished",
                        "request_id": intent["request_id"],
                        "finished_at_utc": _utc_now(),
                        "outcome": "terminal_request_cutoff_failure",
                        "error": str(exc),
                    },
                )
                raise
            try:
                response = client.send(request)
            except httpx.HTTPError as exc:
                _append_event(
                    event_path,
                    config["census_id"],
                    events,
                    {
                        "event_type": "request_finished",
                        "request_id": intent["request_id"],
                        "finished_at_utc": _utc_now(),
                        "outcome": "terminal_transport_failure",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                raise BroadDiscoveryError("broad Wikidata request failed terminally") from exc
            last_access = time.monotonic()
            body = response.content
            digest = _sha256_bytes(body)
            body_path = workspace / "response_bodies" / digest[:2] / f"{digest}.response"
            _atomic_bytes(body_path, body)
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
            response_headers = _response_headers(response)
            header_error: str | None = None
            try:
                _validate_provider_date(response_headers)
            except BroadDiscoveryError as exc:
                header_error = str(exc)
            outcome = "success"
            error: str | None = None
            candidates: list[dict[str, Any]] = []
            if (
                response.status_code != 200
                or response.history
                or str(response.url) != intent["encoded_url"]
                or header_error is not None
                or content_type
                not in {"application/sparql-results+json", "application/json"}
            ):
                outcome = "terminal_http_or_delivery_failure"
                error = header_error or (
                    "HTTP status, redirect, final URL, or content type violated the contract"
                )
            else:
                try:
                    payload = json.loads(body)
                    candidates = parse_result(payload, intent)
                except (UnicodeDecodeError, json.JSONDecodeError, BroadDiscoveryError) as exc:
                    outcome = "terminal_schema_failure"
                    error = str(exc)
            terminal = _append_event(
                event_path,
                config["census_id"],
                events,
                {
                    "event_type": "request_finished",
                    "request_id": intent["request_id"],
                    "finished_at_utc": _utc_now(),
                    "outcome": outcome,
                    "status_code": response.status_code,
                    "final_url": str(response.url),
                    "content_type": content_type,
                    "response_headers": response_headers,
                    "response_bytes": len(body),
                    "response_sha256": digest,
                    "response_body_path": str(body_path.relative_to(workspace)),
                    "candidate_rows": len(candidates),
                    "error": error,
                },
            )
            if outcome != "success":
                raise BroadDiscoveryError(
                    f"{intent['request_id']} ended with {terminal['outcome']}"
                )
            all_candidates.extend(candidates)
            response_inventory.append(
                {
                    "request_id": intent["request_id"],
                    "response_sha256": digest,
                    "response_bytes": len(body),
                    "response_body_path": str(body_path.relative_to(workspace)),
                    "candidate_rows": len(candidates),
                    "response_headers": terminal["response_headers"],
                }
            )
    global_keys = [
        (row["creator_qid"], row["item_qid"], row["commons_filename"])
        for row in all_candidates
    ]
    if len(global_keys) != len(set(global_keys)):
        raise BroadDiscoveryError("cross-painter candidate rows are duplicated")
    all_candidates.sort(
        key=lambda row: (row["painter_id"], row["item_qid"], row["commons_filename"])
    )
    for sequence, row in enumerate(all_candidates, start=1):
        row["candidate_sequence"] = sequence
    _write_jsonl(candidate_path, all_candidates)
    _validate_event_chain(events, config["census_id"])
    by_painter: dict[str, dict[str, int]] = {}
    for painter in config["painters"]:
        group = [row for row in all_candidates if row["painter_id"] == painter["painter_id"]]
        by_painter[painter["painter_id"]] = {
            "item_image_rows": len(group),
            "distinct_items": len({row["item_qid"] for row in group}),
            "distinct_files": len({row["commons_filename"] for row in group}),
        }
    receipt = {
        "schema_version": _RECEIPT_SCHEMA,
        "status": "broad_wikidata_no_p186_metadata_census_complete",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "completed_at_utc": _utc_now(),
        "execution_genesis_event_sha256": genesis["event_sha256"],
        "terminal_event_sha256": events[-1]["event_sha256"],
        "request_event_count": len(events),
        "successful_requests": len(intents),
        "response_inventory": response_inventory,
        "candidate_manifest_path": _relative(root, candidate_path),
        "candidate_manifest_sha256": hash_file(candidate_path),
        "counts": {
            "item_image_rows": len(all_candidates),
            "distinct_items": len({row["item_qid"] for row in all_candidates}),
            "distinct_files": len({row["commons_filename"] for row in all_candidates}),
            "by_painter": by_painter,
            "active_study_admissions": 0,
            "image_downloads": 0,
        },
        "limitations": [
            (
                "Wikidata is discovery-only and cannot establish exact authority, "
                "medium/support, rights, or physical-work identity."
            ),
            (
                "This completes only the broad Wikidata route; every other Protocol 2.0 "
                "source route remains required."
            ),
            "No image bytes were downloaded and no work was admitted.",
        ],
    }
    _write_json(receipt_path, receipt)
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/painter_feature_generation_v1/broad_wikidata_discovery.json"),
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
        print(json.dumps(prepare(root, config_path), indent=2, sort_keys=True))
    else:
        seal_path = _repo_path(root, str(args.seal), "seal")
        print(
            json.dumps(
                execute(root, config_path, seal_path, args.seal_sha256),
                indent=2,
                sort_keys=True,
            )
        )
    return 0
