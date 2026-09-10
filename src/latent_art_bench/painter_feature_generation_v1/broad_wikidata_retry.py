from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import httpx

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import broad_wikidata as broad


class RetryGateError(RuntimeError):
    """Raised when the broad-census retry lineage is not exactly authorized."""


_FREEZE_SCHEMA = "painter-feature-generation-v1-broad-retry-freeze/1.0"
_REVIEW_SCHEMA = "painter-feature-generation-v1-broad-retry-review/1.0"
_AUTH_SCHEMA = "painter-feature-generation-v1-broad-retry-authorization/1.0"
_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "active_study_admission": False,
    "visual_coding": False,
    "feature_extraction": False,
    "generation": False,
}

# Explicit aliases used by the isolated prevalidated executor below. The R1 module remains
# byte-identical to its executed freeze; no process-global function is replaced.
BroadDiscoveryError = broad.BroadDiscoveryError
_RECEIPT_SCHEMA = broad._RECEIPT_SCHEMA
_append_event = broad._append_event
_atomic_bytes = broad._atomic_bytes
_claim_execution_lock = broad._claim_execution_lock
_enforce_request_cutoff = broad._enforce_request_cutoff
_relative = broad._relative
_repo_path_broad = broad._repo_path
_response_headers = broad._response_headers
_sha256_bytes = broad._sha256_bytes
_utc_now = broad._utc_now
_validate_event_chain = broad._validate_event_chain
_validate_provider_date = broad._validate_provider_date
_write_json = broad._write_json
_write_jsonl = broad._write_jsonl
expected_outputs = broad.expected_outputs
load_config = broad.load_config
load_intents = broad.load_intents
parse_result = broad.parse_result


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise RetryGateError(f"{label} must be a repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise RetryGateError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RetryGateError(f"{label} escapes the repository") from exc
    return path


def _confine_path(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RetryGateError(f"{label} is outside the repository") from exc
    return _repo_path(root, str(relative), label)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetryGateError(f"{label} is not JSON") from exc
    if not isinstance(value, dict):
        raise RetryGateError(f"{label} is not an object")
    return value


def _read_hashed_json(path: Path, expected: Any, label: str) -> dict[str, Any]:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise RetryGateError(f"{label} cannot be read") from exc
    if not isinstance(expected, str) or hashlib.sha256(body).hexdigest() != expected:
        raise RetryGateError(f"{label} hash mismatch")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RetryGateError(f"{label} is not JSON") from exc
    if not isinstance(value, dict):
        raise RetryGateError(f"{label} is not an object")
    return value


def _read_hashed_jsonl(path: Path, expected: Any, label: str) -> list[dict[str, Any]]:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise RetryGateError(f"{label} cannot be read") from exc
    if not isinstance(expected, str) or hashlib.sha256(body).hexdigest() != expected:
        raise RetryGateError(f"{label} hash mismatch")
    rows: list[dict[str, Any]] = []
    try:
        lines = body.decode().splitlines()
    except UnicodeDecodeError as exc:
        raise RetryGateError(f"{label} is not UTF-8 JSONL") from exc
    for line_number, line in enumerate(lines, start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RetryGateError(f"invalid JSONL at {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise RetryGateError(f"non-object JSONL at {path}:{line_number}")
        rows.append(row)
    return rows


def _frozen_sha(freeze: Mapping[str, Any], path: str, label: str) -> str:
    matches = [
        row.get("sha256")
        for row in freeze.get("frozen_inputs", [])
        if isinstance(row, Mapping) and row.get("path") == path
    ]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise RetryGateError(f"{label} is not uniquely bound in the retry freeze")
    return matches[0]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RetryGateError(f"invalid JSONL at {path}:{line_number}") from exc
        if not isinstance(row, dict):
            raise RetryGateError(f"non-object JSONL at {path}:{line_number}")
        rows.append(row)
    return rows


def _validate_hash(path: Path, expected: Any, label: str) -> None:
    if not isinstance(expected, str) or hash_file(path) != expected:
        raise RetryGateError(f"{label} hash mismatch")


def _paths_overlap(paths: Sequence[Path]) -> bool:
    resolved = [path.resolve() for path in paths]
    return any(
        left == right or left in right.parents or right in left.parents
        for index, left in enumerate(resolved)
        for right in resolved[index + 1 :]
    )


def _validate_config_delta(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> None:
    candidate = copy.deepcopy(dict(current))
    predecessor = candidate.pop("predecessor_terminal_census", None)
    if not isinstance(predecessor, Mapping):
        raise RetryGateError("current config lacks the retry predecessor contract")
    candidate["census_id"] = previous["census_id"]
    candidate["paths"] = previous["paths"]
    candidate["source_contract"]["minimum_interval_seconds"] = previous[
        "source_contract"
    ]["minimum_interval_seconds"]
    if candidate != previous:
        raise RetryGateError("retry config differs outside census, paths, and interval")
    previous_paths = [Path(value) for value in previous["paths"].values()]
    current_paths = [Path(value) for value in current["paths"].values()]
    if _paths_overlap(previous_paths + current_paths) or _paths_overlap(current_paths):
        raise RetryGateError("retry paths are equal, nested, or overlap predecessor paths")


def _validate_freeze(
    root: Path,
    freeze: Mapping[str, Any],
    config: Mapping[str, Any],
    config_path: Path,
) -> None:
    required = broad.required_frozen_paths(root, config, config_path)
    entries = freeze.get("frozen_inputs")
    if (
        freeze.get("schema_version")
        != "painter-feature-generation-v1-broad-wikidata-freeze/1.0"
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != _SCOPE
        or not isinstance(entries, list)
        or [entry.get("path") for entry in entries] != required
        or freeze.get("preexecution_outputs") != broad.expected_outputs(root, config)
    ):
        raise RetryGateError("collection freeze semantics or closure is invalid")
    for entry in entries:
        _validate_hash(
            _repo_path(root, entry["path"], "frozen input"),
            entry.get("sha256"),
            "frozen input",
        )
    digest = hashlib.sha256(canonical_json(entries).encode()).hexdigest()
    if digest != freeze.get("frozen_input_set_sha256"):
        raise RetryGateError("collection freeze aggregate mismatch")


def _validate_review_authorization(
    review: Mapping[str, Any],
    authorization: Mapping[str, Any],
    config: Mapping[str, Any],
    freeze_path: str,
    freeze_sha256: str,
    review_path: str,
    review_sha256: str,
) -> None:
    if (
        review.get("schema_version")
        != "painter-feature-generation-v1-broad-wikidata-review/1.0"
        or review.get("decision") != "APPROVE_BROAD_WIKIDATA_METADATA_ONLY"
        or review.get("blocking_findings") != []
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("approved_scope") != _SCOPE
        or review.get("reviewed_freeze_path") != freeze_path
        or review.get("reviewed_freeze_sha256") != freeze_sha256
        or authorization.get("schema_version")
        != "painter-feature-generation-v1-broad-wikidata-authorization/1.0"
        or authorization.get("status")
        != "authorized_for_broad_wikidata_metadata_execution"
        or authorization.get("census_id") != config["census_id"]
        or authorization.get("protocol_id") != config["protocol_id"]
        or authorization.get("authorization_scope") != _SCOPE
        or authorization.get("freeze_path") != freeze_path
        or authorization.get("freeze_sha256") != freeze_sha256
        or authorization.get("review_path") != review_path
        or authorization.get("review_sha256") != review_sha256
    ):
        raise RetryGateError("collection review or authorization is invalid")


def _validate_gate_a_review(
    review: Mapping[str, Any],
    config: Mapping[str, Any],
    freeze_path: str,
    freeze_sha256: str,
) -> None:
    if (
        review.get("schema_version")
        != "painter-feature-generation-v1-broad-wikidata-review/1.0"
        or review.get("decision") != "APPROVE_BROAD_WIKIDATA_BASE_COLLECTION_ONLY"
        or review.get("blocking_findings") != []
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("approved_scope") != _SCOPE
        or review.get("review_gate") != "A_BASE_COLLECTION"
        or review.get("retry_lineage_approved") is not False
        or review.get("execution_authorized") is not False
        or review.get("reviewed_freeze_path") != freeze_path
        or review.get("reviewed_freeze_sha256") != freeze_sha256
    ):
        raise RetryGateError("Gate A review boundary is invalid")


def validate_lineage(root: Path, current_config_path: Path) -> dict[str, Any]:
    current = broad.load_config(root, current_config_path)
    predecessor = current.get("predecessor_terminal_census")
    if not isinstance(predecessor, Mapping):
        raise RetryGateError("retry predecessor contract is absent")
    expected_keys = {
        "census_id",
        "config_path",
        "config_sha256",
        "freeze_path",
        "freeze_sha256",
        "review_path",
        "review_sha256",
        "authorization_path",
        "authorization_sha256",
        "event_ledger_path",
        "event_ledger_sha256",
        "terminal_event_sha256",
        "terminal_status_code",
        "terminal_content_type",
        "terminal_outcome",
        "execution_lock_path",
        "execution_lock_sha256",
        "response_bodies",
        "required_absent_outputs",
        "allowed_config_delta",
    }
    if set(predecessor) != expected_keys:
        raise RetryGateError("retry predecessor contract has unexpected fields")
    previous_config_path = _repo_path(root, predecessor["config_path"], "R1 config")
    _validate_hash(previous_config_path, predecessor["config_sha256"], "R1 config")
    previous = broad.load_config(root, previous_config_path)
    if previous["census_id"] != predecessor["census_id"]:
        raise RetryGateError("R1 config census mismatch")
    if set(predecessor["allowed_config_delta"]) != {
        "census_id",
        "paths",
        "predecessor_terminal_census",
        "source_contract.minimum_interval_seconds",
    }:
        raise RetryGateError("allowed retry delta is invalid")
    _validate_config_delta(previous, current)

    evidence: dict[str, tuple[str, Path, dict[str, Any]]] = {}
    for label in ("freeze", "review", "authorization", "execution_lock"):
        declared_path = str(predecessor[f"{label}_path"])
        path = _repo_path(root, declared_path, f"R1 {label}")
        value = _read_hashed_json(
            path, predecessor[f"{label}_sha256"], f"R1 {label}"
        )
        evidence[label] = (declared_path, path, value)
    freeze = evidence["freeze"][2]
    review = evidence["review"][2]
    authorization = evidence["authorization"][2]
    lock = evidence["execution_lock"][2]
    _validate_freeze(root, freeze, previous, previous_config_path)
    _validate_review_authorization(
        review,
        authorization,
        previous,
        evidence["freeze"][0],
        str(predecessor["freeze_sha256"]),
        evidence["review"][0],
        str(predecessor["review_sha256"]),
    )
    if (
        lock.get("schema_version")
        != "painter-feature-generation-v1-execution-lock/1.0"
        or lock.get("census_id") != previous["census_id"]
        or lock.get("authorization_seal_sha256")
        != predecessor["authorization_sha256"]
    ):
        raise RetryGateError("R1 one-shot lock is invalid")

    event_path = _repo_path(root, predecessor["event_ledger_path"], "R1 ledger")
    events = _read_hashed_jsonl(
        event_path, predecessor["event_ledger_sha256"], "R1 ledger"
    )
    broad._validate_event_chain(events, previous["census_id"])
    intents = broad.build_intents(previous)
    signature = [(event.get("event_type"), event.get("request_id")) for event in events]
    expected_signature = [
        ("execution_started", None),
        ("request_started", intents[0]["request_id"]),
        ("request_finished", intents[0]["request_id"]),
        ("request_started", intents[1]["request_id"]),
        ("request_finished", intents[1]["request_id"]),
    ]
    terminal = events[-1] if events else {}
    if (
        signature != expected_signature
        or events[1].get("encoded_url") != intents[0]["encoded_url"]
        or events[2].get("outcome") != "success"
        or events[2].get("status_code") != 200
        or events[3].get("encoded_url") != intents[1]["encoded_url"]
        or terminal.get("event_sha256") != predecessor["terminal_event_sha256"]
        or terminal.get("status_code") != predecessor["terminal_status_code"]
        or terminal.get("content_type") != predecessor["terminal_content_type"]
        or terminal.get("outcome") != predecessor["terminal_outcome"]
        or terminal.get("outcome") == "success"
    ):
        raise RetryGateError("R1 terminal state machine is invalid")
    if (
        events[0].get("authorization_seal_sha256")
        != predecessor["authorization_sha256"]
        or events[0].get("freeze_sha256") != predecessor["freeze_sha256"]
        or events[0].get("execution_lock_sha256")
        != predecessor["execution_lock_sha256"]
    ):
        raise RetryGateError("R1 genesis linkage is invalid")

    bodies = predecessor["response_bodies"]
    if (
        not isinstance(bodies, list)
        or len(bodies) != 2
        or len({row.get("path") for row in bodies if isinstance(row, Mapping)}) != 2
    ):
        raise RetryGateError("R1 response inventory is invalid")
    declared: dict[str, tuple[str, int]] = {}
    for row in bodies:
        if not isinstance(row, Mapping) or set(row) != {"path", "sha256", "bytes"}:
            raise RetryGateError("R1 response inventory row is invalid")
        path = _repo_path(root, row["path"], "R1 response")
        _validate_hash(path, row["sha256"], "R1 response")
        if path.stat().st_size != row["bytes"]:
            raise RetryGateError("R1 response byte count mismatch")
        declared[str(row["path"])] = (str(row["sha256"]), int(row["bytes"]))
    workspace = Path(previous["paths"]["workspace"])
    observed = {
        str(workspace / event["response_body_path"]): (
            event["response_sha256"],
            event["response_bytes"],
        )
        for event in events
        if event.get("response_body_path")
    }
    if declared != observed:
        raise RetryGateError("R1 responses differ from the event ledger")
    exact_absent = [
        previous["paths"]["candidate_manifest"],
        previous["paths"]["execution_receipt"],
    ]
    if predecessor["required_absent_outputs"] != exact_absent or any(
        _repo_path(root, path, "R1 absent output").exists() for path in exact_absent
    ):
        raise RetryGateError("R1 candidate/receipt absence is invalid")
    return {"previous": previous, "current": current, "events": events}


def required_gate_paths(
    root: Path, config_path: Path, retry_freeze: Mapping[str, Any]
) -> list[str]:
    config = broad.load_config(root, config_path)
    predecessor = config["predecessor_terminal_census"]
    paths = {
        ".gitignore",
        str(config_path.resolve().relative_to(root.resolve())),
        str(config["paths"]["request_intents"]),
        str(config["protocol_path"]),
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_broad_wikidata_retry.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_wikidata.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_wikidata_retry.py",
        "tests/painter_feature_generation_v1/test_broad_wikidata_retry.py",
        str(predecessor["config_path"]),
        str(predecessor["freeze_path"]),
        str(predecessor["review_path"]),
        str(predecessor["authorization_path"]),
        str(predecessor["event_ledger_path"]),
        str(predecessor["execution_lock_path"]),
    }
    paths.update(str(row["path"]) for row in predecessor["response_bodies"])
    paths.update(
        {
            str(retry_freeze["collection_freeze_path"]),
            str(retry_freeze["collection_review_path"]),
        }
    )
    for path in paths:
        if not _repo_path(root, path, "retry gate input").is_file():
            raise RetryGateError(f"retry gate input is missing: {path}")
    return sorted(paths)


def validate_retry_authorization(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
) -> dict[str, Any]:
    seal = _read_hashed_json(seal_path, seal_sha256, "retry authorization")
    config = broad.load_config(root, config_path)
    if (
        seal.get("schema_version") != _AUTH_SCHEMA
        or seal.get("status") != "authorized_for_terminal_retry_execution"
        or seal.get("census_id") != config["census_id"]
        or seal.get("protocol_id") != config["protocol_id"]
        or seal.get("authorization_scope") != _SCOPE
    ):
        raise RetryGateError("retry authorization semantics are invalid")
    freeze_path = _repo_path(root, seal.get("freeze_path"), "retry freeze")
    freeze = _read_hashed_json(
        freeze_path, seal.get("freeze_sha256"), "retry freeze"
    )
    entries = freeze.get("frozen_inputs")
    required = required_gate_paths(root, config_path, freeze)
    if (
        freeze.get("schema_version") != _FREEZE_SCHEMA
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != _SCOPE
        or not isinstance(entries, list)
        or [row.get("path") for row in entries] != required
        or freeze.get("preexecution_outputs") != broad.expected_outputs(root, config)
    ):
        raise RetryGateError("retry freeze semantics or closure is invalid")
    for output in freeze["preexecution_outputs"]:
        if _repo_path(root, output["path"], "retry preexecution output").exists():
            raise RetryGateError("retry preexecution output is not absent")
    for row in entries:
        _validate_hash(_repo_path(root, row["path"], "retry input"), row["sha256"], "retry input")
    if hashlib.sha256(canonical_json(entries).encode()).hexdigest() != freeze.get(
        "frozen_input_set_sha256"
    ):
        raise RetryGateError("retry freeze aggregate mismatch")
    collection_freeze_path = _repo_path(
        root, freeze.get("collection_freeze_path"), "collection freeze"
    )
    collection_review_path = _repo_path(
        root, freeze.get("collection_review_path"), "collection review"
    )
    collection_freeze = _read_hashed_json(
        collection_freeze_path,
        freeze.get("collection_freeze_sha256"),
        "collection freeze",
    )
    collection_review = _read_hashed_json(
        collection_review_path,
        freeze.get("collection_review_sha256"),
        "collection review",
    )
    _validate_freeze(root, collection_freeze, config, config_path)
    _validate_gate_a_review(
        collection_review,
        config,
        str(freeze["collection_freeze_path"]),
        str(freeze["collection_freeze_sha256"]),
    )
    review_path = _repo_path(root, seal.get("review_path"), "retry review")
    review = _read_hashed_json(review_path, seal.get("review_sha256"), "retry review")
    if (
        review.get("schema_version") != _REVIEW_SCHEMA
        or review.get("decision") != "APPROVE_TERMINAL_RETRY_EXECUTION"
        or review.get("blocking_findings") != []
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("approved_scope") != _SCOPE
        or review.get("reviewed_freeze_path") != seal.get("freeze_path")
        or review.get("reviewed_freeze_sha256") != seal.get("freeze_sha256")
    ):
        raise RetryGateError("retry review is invalid")
    validate_lineage(root, config_path)
    return {"seal": seal, "freeze": freeze, "review": review}


def _validated_execution_context(
    root: Path,
    config_path: Path,
    collection_seal_path: Path,
    collection_seal_sha256: str,
    retry_seal_path: Path,
    retry_seal_sha256: str,
) -> dict[str, Any]:
    config_path = _confine_path(root, config_path, "retry config")
    collection_seal_path = _confine_path(
        root, collection_seal_path, "combined collection seal"
    )
    retry_seal_path = _confine_path(root, retry_seal_path, "retry seal")
    authorization = validate_retry_authorization(
        root, config_path, retry_seal_path, retry_seal_sha256
    )
    freeze = authorization["freeze"]
    combined = _read_hashed_json(
        collection_seal_path, collection_seal_sha256, "combined collection seal"
    )
    config_relative = str(config_path.relative_to(root.resolve()))
    config = _read_hashed_json(
        config_path,
        _frozen_sha(freeze, config_relative, "retry config"),
        "retry config",
    )
    if (
        combined.get("schema_version")
        != "painter-feature-generation-v1-broad-wikidata-authorization/1.0"
        or combined.get("status")
        != "authorized_for_broad_wikidata_metadata_execution"
        or combined.get("census_id") != config["census_id"]
        or combined.get("protocol_id") != config["protocol_id"]
        or combined.get("authorization_scope") != _SCOPE
        or combined.get("freeze_path") != freeze["collection_freeze_path"]
        or combined.get("freeze_sha256") != freeze["collection_freeze_sha256"]
        or combined.get("review_path") != freeze["collection_review_path"]
        or combined.get("review_sha256") != freeze["collection_review_sha256"]
        or combined.get("retry_gate_authorization_path")
        != str(retry_seal_path.resolve().relative_to(root.resolve()))
        or combined.get("retry_gate_authorization_sha256") != retry_seal_sha256
    ):
        raise RetryGateError("combined collection/retry seal is invalid")
    collection_freeze = _read_hashed_json(
        _repo_path(root, combined["freeze_path"], "collection freeze"),
        combined["freeze_sha256"],
        "collection freeze",
    )
    collection_review = _read_hashed_json(
        _repo_path(root, combined["review_path"], "collection review"),
        combined["review_sha256"],
        "collection review",
    )
    intent_path = str(config["paths"]["request_intents"])
    intent_sha256 = _frozen_sha(freeze, intent_path, "request intents")
    intents = _read_hashed_jsonl(
        _repo_path(root, intent_path, "request intents"),
        intent_sha256,
        "request intents",
    )
    if intents != broad.build_intents(config):
        raise RetryGateError("request intents differ from the config snapshot")
    return {
        "seal": combined,
        "freeze": collection_freeze,
        "review": collection_review,
        "config": config,
        "intents": intents,
        "request_intents_sha256": intent_sha256,
        "config_path": config_path,
        "collection_seal_path": collection_seal_path,
        "retry_seal_path": retry_seal_path,
    }


def _execute_authorized_retry(
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    retry_seal_path: Path,
    retry_seal_sha256: str,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    incoming_paths = (config_path, seal_path, retry_seal_path)
    config_path = _confine_path(root, config_path, "retry config")
    seal_path = _confine_path(root, seal_path, "combined collection seal")
    retry_seal_path = _confine_path(root, retry_seal_path, "retry seal")
    authorization = _validated_execution_context(
        root,
        config_path,
        seal_path,
        seal_sha256,
        retry_seal_path,
        retry_seal_sha256,
    )
    canonical_paths = (config_path, seal_path, retry_seal_path)
    if any(
        incoming.resolve() != canonical
        for incoming, canonical in zip(incoming_paths, canonical_paths, strict=True)
    ):
        raise RetryGateError("an execution input path changed after validation")
    config = authorization["config"]
    intents = authorization["intents"]
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
            "request_intents_sha256": authorization["request_intents_sha256"],
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




def execute_retry(
    root: Path,
    config_path: Path,
    collection_seal_path: Path,
    collection_seal_sha256: str,
    retry_seal_path: Path,
    retry_seal_sha256: str,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    return _execute_authorized_retry(
        root,
        config_path,
        collection_seal_path,
        collection_seal_sha256,
        retry_seal_path,
        retry_seal_sha256,
        transport=transport,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--collection-seal", type=Path, required=True)
    parser.add_argument("--collection-seal-sha256", required=True)
    parser.add_argument("--retry-seal", type=Path, required=True)
    parser.add_argument("--retry-seal-sha256", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    receipt = execute_retry(
        root,
        _repo_path(root, str(args.config), "config"),
        _repo_path(root, str(args.collection_seal), "collection seal"),
        args.collection_seal_sha256,
        _repo_path(root, str(args.retry_seal), "retry seal"),
        args.retry_seal_sha256,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0
