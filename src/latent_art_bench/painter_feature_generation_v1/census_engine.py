"""Shared fail-closed census engine for Protocol 2.1 source routes.

The seven existing collectors each carry their own copy of the same machinery: config
validation, exact request intents, a hash-bound freeze, review and authorization seals, a
one-shot execution lock, a hash-chained event ledger, a content-addressed raw-response store,
and atomic publication. Every retry duplicated ~1,300 lines to change one parser rule.

This module keeps that machinery in one tested place and lets a route supply only what is
route-specific through a :class:`RouteContract`: its endpoint, config validation, intent
builder, response parser/screen, duplicate key, sort key, and receipt summary. The engine
itself never downloads an image, admits a work, extracts a feature, or generates anything.

Differences from the copied collectors, all deliberate:

- ``prepare`` writes the freeze as well as the intents, records ``recorded_git_commit``, and
  refuses to run when a tracked frozen input is dirty against HEAD, so commit-bound
  verification (``latent_art_bench.evidence``) can always reproduce the bound bytes;
- the review seal must state ``reviewer_kind`` (``human`` or ``llm_subagent``) so reports can
  disclose who reviewed;
- a route's parser is expected to validate only the fields its screen uses and to retain the
  rest raw, so an unfamiliar provider representation is recorded rather than fatal.
"""

from __future__ import annotations

import argparse
import email.utils
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import httpx

from latent_art_bench import evidence
from latent_art_bench.io import canonical_json, hash_bytes, hash_file, stable_hash

METADATA_ONLY_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "visual_coding": False,
    "active_study_admission": False,
    "feature_extraction": False,
    "generation": False,
}
ENGINE_MODULE_PATH = "src/latent_art_bench/painter_feature_generation_v1/census_engine.py"
ENGINE_TEST_PATH = "tests/painter_feature_generation_v1/test_census_engine.py"
SHARED_FROZEN_INPUTS = (
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    "src/latent_art_bench/__init__.py",
    "src/latent_art_bench/io.py",
    "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
    ENGINE_MODULE_PATH,
    ENGINE_TEST_PATH,
)
REQUIRED_SOURCE_RULES = (
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
)
PATH_KEYS = {
    "request_intents",
    "request_events",
    "freeze",
    "publication_directory",
    "candidate_manifest",
    "execution_receipt",
    "workspace",
}
REVIEWER_KINDS = ("human", "llm_subagent")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CENSUS_ID_RE = re.compile(r"pfg-v1-[a-z0-9-]+")


class CensusError(RuntimeError):
    """Raised whenever the frozen contract fails closed."""


ParseResponse = Callable[[bytes, Mapping[str, Any], Mapping[str, Any], str], List[Dict[str, Any]]]


@dataclass(frozen=True)
class RouteContract:
    route_id: str
    schema_prefix: str
    module_path: str
    script_path: str
    test_path: str
    endpoint: str
    user_agent: str
    validate_config: Callable[[Mapping[str, Any]], None]
    build_intents: Callable[[Mapping[str, Any]], List[Dict[str, Any]]]
    parse_response: ParseResponse
    candidate_key: Callable[[Mapping[str, Any]], Any]
    sort_key: Callable[[Mapping[str, Any]], Any]
    summarize: Callable[[Sequence[Mapping[str, Any]], Mapping[str, Any]], Dict[str, Any]]
    limitations: Sequence[str]

    def schema(self, kind: str) -> str:
        return f"{self.schema_prefix}-{kind}/1.0"

    @property
    def review_decision(self) -> str:
        return f"APPROVE_{self.route_id.upper()}_ONLY"

    @property
    def authorization_status(self) -> str:
        return f"authorized_for_{self.route_id}_execution"

    @property
    def receipt_status(self) -> str:
        return f"{self.route_id}_census_complete_not_image_acquisition"


# --------------------------------------------------------------------------- primitives


_sha256 = hash_bytes


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CensusError(f"{label} must be a repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise CensusError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CensusError(f"{label} escapes the repository") from exc
    return path


def relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise CensusError("path is outside the repository") from exc


def _read_hashed(path: Path, expected: Any, label: str) -> bytes:
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise CensusError(f"{label} cannot be read") from exc
    if not isinstance(expected, str) or _sha256(body) != expected:
        raise CensusError(f"{label} hash mismatch")
    return body


def json_object(body: bytes, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CensusError(f"{label} is not JSON") from exc
    if not isinstance(value, dict):
        raise CensusError(f"{label} is not an object")
    return value


def jsonl_objects(body: bytes, label: str) -> List[Dict[str, Any]]:
    """Parse JSONL split on LF only.

    ``str.splitlines`` also breaks on U+2028, U+2029, U+0085, and the ASCII separators, all of
    which ``canonical_json`` writes raw inside strings, so a valid row could split in two.
    """
    try:
        lines = body.decode("utf-8").split("\n")
    except UnicodeDecodeError as exc:
        raise CensusError(f"{label} is not UTF-8") from exc
    if lines and lines[-1] == "":
        lines.pop()
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line:
            raise CensusError(f"{label} has a blank row at {number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CensusError(f"{label} row {number} is not JSON") from exc
        if not isinstance(value, dict):
            raise CensusError(f"{label} row {number} is not an object")
        rows.append(value)
    return rows


def parse_utc(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise CensusError(f"{label} must be UTC")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CensusError(f"{label} is invalid") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise CensusError(f"{label} is not UTC")
    return parsed


def as_int(value: Any) -> Optional[int]:
    """Accept an int or a decimal string; reject bools, floats, and anything else."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?[0-9]+", value.strip()):
        return int(value.strip())
    return None


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    atomic_bytes(path, "".join(canonical_json(row) + "\n" for row in rows).encode("utf-8"))


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True, default=str)
    atomic_bytes(path, (rendered + "\n").encode("utf-8"))


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write((canonical_json(row) + "\n").encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())


# --------------------------------------------------------------------------- config


def load_config_bytes(
    route: RouteContract,
    root: Path,
    config_path: Path,
    body: bytes,
    protocol_body: Optional[bytes] = None,
) -> Dict[str, Any]:
    relative(root, config_path)
    config = json_object(body, "config")
    if config.get("schema_version") != route.schema("config"):
        raise CensusError(f"unsupported {route.route_id} config schema")
    census_id = config.get("census_id")
    if not isinstance(census_id, str) or not _CENSUS_ID_RE.fullmatch(census_id):
        raise CensusError("census_id is malformed")
    protocol = repo_path(root, config.get("protocol_path"), "protocol_path")
    if protocol_body is None:
        try:
            protocol_body = protocol.read_bytes()
        except OSError as exc:
            raise CensusError("protocol cannot be read") from exc
    try:
        protocol_text = protocol_body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CensusError("protocol is not UTF-8") from exc
    match = re.search(r"^Protocol ID: `([^`]+)`$", protocol_text, re.MULTILINE)
    if not match or config.get("protocol_id") != match.group(1):
        raise CensusError("config differs from the canonical protocol")
    if config.get("scope") != METADATA_ONLY_SCOPE:
        raise CensusError("scope must be metadata-only")
    source = config.get("source_contract")
    paths = config.get("paths")
    if not isinstance(source, Mapping) or not isinstance(paths, Mapping):
        raise CensusError("source contract and paths must be objects")
    if (
        not isinstance(source.get("source_id"), str)
        or source.get("endpoint") != route.endpoint
        or source.get("method") != "GET"
        or source.get("authentication") != "none"
        or source.get("redirects") != "forbidden"
        or source.get("accept") != "application/json"
        or source.get("expected_content_type") != "application/json"
    ):
        raise CensusError("source contract is invalid")
    for key in REQUIRED_SOURCE_RULES:
        if not isinstance(source.get(key), str) or not source[key].strip():
            raise CensusError(f"source contract lacks {key}")
    interval = source.get("minimum_interval_seconds")
    timeout = source.get("timeout_seconds")
    maximum_bytes = source.get("maximum_response_bytes")
    if isinstance(interval, bool) or not isinstance(interval, (int, float)):
        raise CensusError("minimum interval is invalid")
    if not 0.5 <= float(interval) <= 30:
        raise CensusError("minimum interval is invalid")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise CensusError("timeout is invalid")
    if not 5 <= float(timeout) <= 120:
        raise CensusError("timeout is invalid")
    if (
        isinstance(maximum_bytes, bool)
        or not isinstance(maximum_bytes, int)
        or not 1_048_576 <= maximum_bytes <= 52_428_800
    ):
        raise CensusError("maximum response size is invalid")
    parse_utc(source.get("execution_start_not_after_utc"), "execution cutoff")
    if set(paths) != PATH_KEYS:
        raise CensusError("path contract has unexpected keys")
    resolved = {key: repo_path(root, value, f"paths.{key}") for key, value in paths.items()}
    publication = resolved["publication_directory"]
    if (
        resolved["candidate_manifest"].parent != publication
        or resolved["execution_receipt"].parent != publication
        or publication == root.resolve()
    ):
        raise CensusError("publication paths do not share their declared directory")
    if len(set(resolved.values())) != len(resolved) or any(
        resolved["workspace"] in path.parents
        for key, path in resolved.items()
        if key != "workspace"
    ):
        raise CensusError("declared paths overlap")
    retry = config.get("retry_contract")
    if retry is not None:
        _validate_retry_contract(retry)
    route.validate_config(config)
    return config


def _validate_retry_contract(retry: Any) -> None:
    if not isinstance(retry, Mapping):
        raise CensusError("retry contract must be an object")
    for key in (
        "predecessor_census_id",
        "terminal_outcome",
        "terminal_error",
        "allowed_semantic_delta",
    ):
        if not isinstance(retry.get(key), str) or not retry[key].strip():
            raise CensusError(f"retry contract lacks {key}")
    state = retry.get("predecessor_terminal_state")
    if (
        not isinstance(state, Mapping)
        or not isinstance(state.get("absent_paths"), list)
        or not isinstance(state.get("workspace"), str)
        or not isinstance(state.get("exact_files"), list)
    ):
        raise CensusError("predecessor terminal state is malformed")
    evidence_rows = retry.get("predecessor_evidence")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        raise CensusError("predecessor evidence is malformed")
    roles = []
    for row in evidence_rows:
        if (
            not isinstance(row, Mapping)
            or not isinstance(row.get("role"), str)
            or not isinstance(row.get("path"), str)
            or not _SHA256_RE.fullmatch(str(row.get("sha256") or ""))
        ):
            raise CensusError("predecessor evidence row is malformed")
        roles.append(row["role"])
    if len(set(roles)) != len(roles) or "terminal_events" not in roles:
        raise CensusError("predecessor evidence roles must be unique and include terminal_events")


def load_config(route: RouteContract, root: Path, config_path: Path) -> Dict[str, Any]:
    try:
        body = config_path.resolve().read_bytes()
    except OSError as exc:
        raise CensusError("config cannot be read") from exc
    return load_config_bytes(route, root, config_path.resolve(), body)


# --------------------------------------------------------------------------- freeze


def declared_frozen_paths(
    route: RouteContract, root: Path, config_path: Path, config: Mapping[str, Any]
) -> List[str]:
    """Every path a freeze for this route binds, before any existence check."""
    paths = set(SHARED_FROZEN_INPUTS)
    paths.update(
        {
            route.module_path,
            route.script_path,
            route.test_path,
            relative(root, config_path),
            str(config["protocol_path"]),
            str(config["paths"]["request_intents"]),
        }
    )
    retry = config.get("retry_contract")
    if isinstance(retry, Mapping):
        for row in retry.get("predecessor_evidence", []):
            paths.add(str(row["path"]))
    return sorted(paths)


def required_frozen_paths(
    route: RouteContract, root: Path, config_path: Path, config: Mapping[str, Any]
) -> List[str]:
    paths = declared_frozen_paths(route, root, config_path, config)
    for path in paths:
        if not repo_path(root, path, "frozen input").is_file():
            raise CensusError(f"required frozen input is missing: {path}")
    return paths


def expected_outputs(config: Mapping[str, Any]) -> List[Dict[str, str]]:
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


def _tracked(root: Path, paths: Sequence[str]) -> List[str]:
    if not paths:
        return []
    listing = evidence._git(root, "ls-files", "--", *paths, check=False)
    return sorted(set(listing.stdout.decode().split()))


def prepare(route: RouteContract, root: Path, config_path: Path) -> Dict[str, Any]:
    root = root.resolve()
    if not evidence.is_git_repository(root):
        raise CensusError("prepare requires a git checkout so the freeze can record its commit")
    config = load_config(route, root, config_path)
    freeze_path = repo_path(root, config["paths"]["freeze"], "paths.freeze")
    if freeze_path.exists():
        raise CensusError("freeze already exists; a corrected contract needs a new census ID")
    intents = route.build_intents(config)
    if not intents:
        raise CensusError("route produced no request intents")
    intent_relative = str(config["paths"]["request_intents"])
    intent_path = repo_path(root, intent_relative, "paths.request_intents")
    # Check the tree before writing anything: the intents path must be new to git, and every
    # other tracked frozen input must be clean, or the freeze would bind bytes HEAD lacks.
    declared = declared_frozen_paths(route, root, config_path, config)
    if _tracked(root, [intent_relative]):
        raise CensusError(
            "request intents path is already tracked; a new census needs its own intents path: "
            + intent_relative
        )
    other = [path for path in declared if path != intent_relative]
    dirty = evidence.tracked_paths_dirty(root, _tracked(root, other))
    if dirty:
        raise CensusError(
            "tracked frozen inputs are dirty against HEAD; commit them first: " + ", ".join(dirty)
        )
    write_jsonl_atomic(intent_path, intents)
    required = required_frozen_paths(route, root, config_path, config)
    entries = [{"path": path, "sha256": hash_file(root / path)} for path in required]
    freeze = {
        "schema_version": route.schema("freeze"),
        "status": "sealed_for_neutral_quality_review",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "scope": METADATA_ONLY_SCOPE,
        evidence.RECORDED_COMMIT_FIELD: evidence.head_commit(root),
        "frozen_input_set_sha256": stable_hash(entries),
        "frozen_inputs": entries,
        "preexecution_outputs": expected_outputs(config),
    }
    write_json_atomic(freeze_path, freeze)
    return {
        "census_id": config["census_id"],
        "requests": len(intents),
        "request_intents_path": relative(root, intent_path),
        "request_intents_sha256": hash_file(intent_path),
        "freeze_path": relative(root, freeze_path),
        "freeze_sha256": hash_file(freeze_path),
        evidence.RECORDED_COMMIT_FIELD: freeze[evidence.RECORDED_COMMIT_FIELD],
        "next": (
            "commit the intents and freeze, obtain a neutral review, then an authorization seal"
        ),
    }


# --------------------------------------------------------------------------- authorization


def _freeze_sha(freeze: Mapping[str, Any], path: str) -> str:
    matches = [
        row.get("sha256")
        for row in freeze.get("frozen_inputs", [])
        if isinstance(row, Mapping) and row.get("path") == path
    ]
    if len(matches) != 1 or not isinstance(matches[0], str):
        raise CensusError(f"freeze does not uniquely bind {path}")
    return matches[0]


def validate_events(events: Sequence[Mapping[str, Any]], census_id: str, schema: str) -> None:
    for sequence, event in enumerate(events, start=1):
        if (
            event.get("schema_version") != schema
            or event.get("census_id") != census_id
            or event.get("sequence") != sequence
        ):
            raise CensusError("event chain metadata is invalid")
    error = evidence.chain_error(events, allow_null_genesis=False)
    if error is not None:
        raise CensusError(f"event chain hash is invalid: {error}")


def _validate_predecessor(
    root: Path, retry: Mapping[str, Any], freeze: Mapping[str, Any], bodies: Mapping[str, bytes]
) -> None:
    by_role: Dict[str, bytes] = {}
    for row in retry["predecessor_evidence"]:
        path = str(row["path"])
        if _freeze_sha(freeze, path) != row["sha256"]:
            raise CensusError("freeze does not bind predecessor evidence")
        by_role[str(row["role"])] = bodies[path]
    events = jsonl_objects(by_role["terminal_events"], "predecessor terminal ledger")
    if not events or evidence.chain_error(events, allow_null_genesis=True) is not None:
        raise CensusError("predecessor terminal ledger chain is invalid")
    terminal = events[-1]
    if (
        terminal.get("census_id") != retry["predecessor_census_id"]
        or terminal.get("outcome") != retry["terminal_outcome"]
        or terminal.get("error") != retry["terminal_error"]
    ):
        raise CensusError("predecessor terminal event differs from the retry contract")
    state = retry["predecessor_terminal_state"]
    if any(
        repo_path(root, path, "predecessor absent output").exists()
        for path in state["absent_paths"]
    ):
        raise CensusError("predecessor terminal publication absence has drifted")
    workspace = repo_path(root, state["workspace"], "predecessor workspace")
    observed = sorted(
        str(path.relative_to(workspace)) for path in workspace.rglob("*") if path.is_file()
    )
    if observed != list(state["exact_files"]):
        raise CensusError("predecessor terminal workspace inventory has drifted")


def validate_authorization(
    route: RouteContract, root: Path, config_path: Path, seal_path: Path, seal_sha256: str
) -> Dict[str, Any]:
    relative(root, seal_path)
    seal = json_object(_read_hashed(seal_path, seal_sha256, "authorization"), "authorization")
    freeze_path = repo_path(root, seal.get("freeze_path"), "freeze")
    freeze = json_object(_read_hashed(freeze_path, seal.get("freeze_sha256"), "freeze"), "freeze")
    entries = freeze.get("frozen_inputs")
    if not isinstance(entries, list):
        raise CensusError("freeze inputs are not a list")
    bodies: Dict[str, bytes] = {}
    for row in entries:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            raise CensusError("freeze input row is malformed")
        path = str(row["path"])
        if path in bodies:
            raise CensusError("freeze input path is duplicated")
        bodies[path] = _read_hashed(
            repo_path(root, path, "frozen input"), row.get("sha256"), "frozen input"
        )
    config_relative = relative(root, config_path)
    config_body = bodies.get(config_relative)
    if config_body is None:
        raise CensusError("freeze does not bind the config")
    preparse = json_object(config_body, "config")
    protocol_relative = preparse.get("protocol_path")
    if not isinstance(protocol_relative, str) or protocol_relative not in bodies:
        raise CensusError("freeze does not bind the protocol")
    config = load_config_bytes(route, root, config_path, config_body, bodies[protocol_relative])
    required = required_frozen_paths(route, root, config_path, config)
    commit = freeze.get(evidence.RECORDED_COMMIT_FIELD)
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise CensusError("freeze does not record its git commit")
    if evidence.is_git_repository(root):
        resolved = evidence._git(root, "cat-file", "-e", f"{commit}^{{commit}}", check=False)
        if resolved.returncode != 0:
            raise CensusError("freeze records a git commit that this checkout does not have")
    if (
        seal.get("schema_version") != route.schema("authorization")
        or seal.get("status") != route.authorization_status
        or seal.get("census_id") != config["census_id"]
        or seal.get("protocol_id") != config["protocol_id"]
        or seal.get("authorization_scope") != METADATA_ONLY_SCOPE
        or freeze.get("schema_version") != route.schema("freeze")
        or freeze.get("status") != "sealed_for_neutral_quality_review"
        or freeze.get("census_id") != config["census_id"]
        or freeze.get("protocol_id") != config["protocol_id"]
        or freeze.get("scope") != METADATA_ONLY_SCOPE
        or [row.get("path") for row in entries] != required
        or freeze.get("preexecution_outputs") != expected_outputs(config)
    ):
        raise CensusError("authorization or freeze semantics are invalid")
    if stable_hash(entries) != freeze.get("frozen_input_set_sha256"):
        raise CensusError("freeze aggregate mismatch")
    retry = config.get("retry_contract")
    if isinstance(retry, Mapping):
        _validate_predecessor(root, retry, freeze, bodies)
    review_path = repo_path(root, seal.get("review_path"), "review")
    review = json_object(_read_hashed(review_path, seal.get("review_sha256"), "review"), "review")
    if (
        review.get("schema_version") != route.schema("review")
        or review.get("decision") != route.review_decision
        or review.get("blocking_findings") != []
        or not str(review.get("independent_reviewer") or "").strip()
        or review.get("reviewer_kind") not in REVIEWER_KINDS
        or review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
        or review.get("approved_scope") != METADATA_ONLY_SCOPE
        or review.get("reviewed_freeze_path") != seal.get("freeze_path")
        or review.get("reviewed_freeze_sha256") != seal.get("freeze_sha256")
    ):
        raise CensusError("review is invalid")
    intent_path = str(config["paths"]["request_intents"])
    intent_body = bodies.get(intent_path)
    if intent_body is None or _sha256(intent_body) != _freeze_sha(freeze, intent_path):
        raise CensusError("freeze does not bind request intents")
    intents = jsonl_objects(intent_body, "request intents")
    if intents != route.build_intents(config):
        raise CensusError("request intents differ from reconstruction")
    return {"seal": seal, "freeze": freeze, "review": review, "config": config, "intents": intents}


# --------------------------------------------------------------------------- execution


def _claim_lock(workspace: Path, census_id: str, seal_sha256: str) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    path = workspace / ".execution.lock"
    body = (
        canonical_json(
            {
                "schema_version": "painter-feature-generation-v1-execution-lock/1.0",
                "census_id": census_id,
                "authorization_seal_sha256": seal_sha256,
                "claimed_at_utc": _utc_now(),
                "rule": "one-shot; never remove or resume; use a new reviewed census ID",
            }
        )
        + "\n"
    ).encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise CensusError("census execution is already claimed") from exc
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
    _fsync_directory(workspace)
    return path


def _headers(response: httpx.Response) -> Dict[str, List[str]]:
    keys = ("date", "server", "content-type", "content-length", "retry-after", "x-request-id")
    return {key: response.headers.get_list(key) for key in keys if response.headers.get_list(key)}


def _bounded_body(response: httpx.Response, maximum_bytes: int) -> tuple:
    retained = bytearray()
    try:
        for chunk in response.iter_bytes():
            retained.extend(chunk[: maximum_bytes + 1 - len(retained)])
            if len(retained) > maximum_bytes:
                return bytes(retained), False
    finally:
        response.close()
    return bytes(retained), True


def _validate_date(values: Optional[Sequence[str]]) -> None:
    if not values or len(values) != 1:
        raise CensusError("response must have one HTTP Date header")
    try:
        parsed = email.utils.parsedate_to_datetime(values[0])
    except (TypeError, ValueError, OverflowError) as exc:
        raise CensusError("response Date header is malformed") from exc
    if parsed is None or parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CensusError("response Date header is not timezone-aware")


def _append_event(
    path: Path, schema: str, census_id: str, events: List[Dict[str, Any]], fields: Mapping[str, Any]
) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "schema_version": schema,
        "census_id": census_id,
        "sequence": len(events) + 1,
        "previous_event_sha256": events[-1]["event_sha256"] if events else "0" * 64,
        **fields,
    }
    row["event_sha256"] = stable_hash(row)
    _append_jsonl(path, row)
    events.append(row)
    return row


def _validate_success_events(
    events: Sequence[Mapping[str, Any]],
    intents: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
    expected_content_type: str,
) -> None:
    """Re-audit the on-disk ledger of a fully successful census before publication.

    Mirrors the terminal collectors: one genesis plus a started/finished pair per intent in
    frozen order, monotonic timestamps, status 200 on the exact frozen URL, a complete body,
    the expected content type, no Retry-After, and an inventory that restates the ledger.
    """
    if (
        len(events) != 1 + 2 * len(intents)
        or len(inventory) != len(intents)
        or events[0].get("event_type") != "execution_started"
    ):
        raise CensusError("successful event ledger has the wrong shape")
    previous_time = parse_utc(events[0].get("started_at_utc"), "genesis timestamp")
    for index, intent in enumerate(intents):
        started = events[1 + 2 * index]
        finished = events[2 + 2 * index]
        started_time = parse_utc(started.get("started_at_utc"), "request-start timestamp")
        finished_time = parse_utc(finished.get("finished_at_utc"), "request-finish timestamp")
        digest = finished.get("response_sha256")
        expected_path = (
            f"response_bodies/{digest[:2]}/{digest}.response"
            if isinstance(digest, str) and _SHA256_RE.fullmatch(digest)
            else None
        )
        byte_count = finished.get("response_bytes")
        candidate_rows = finished.get("candidate_rows")
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
            raise CensusError("successful event ledger differs from frozen request order")
        headers = finished.get("response_headers")
        if not isinstance(headers, Mapping):
            raise CensusError("successful event lacks response headers")
        _validate_date(headers.get("date"))
        content_types = headers.get("content-type")
        if (
            not isinstance(content_types, list)
            or len(content_types) != 1
            or content_types[0].split(";", 1)[0].strip() != expected_content_type
            or headers.get("retry-after") is not None
        ):
            raise CensusError("successful event has invalid response headers")
        previous_time = finished_time


def _publish(
    root: Path,
    config: Mapping[str, Any],
    candidates: List[Dict[str, Any]],
    receipt: Dict[str, Any],
) -> Dict[str, Any]:
    paths = config["paths"]
    final_dir = repo_path(root, paths["publication_directory"], "publication directory")
    if final_dir.exists():
        raise CensusError("publication directory already exists")
    final_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{final_dir.name}.", dir=final_dir.parent))
    try:
        candidate_tmp = temporary / Path(str(paths["candidate_manifest"])).name
        receipt_tmp = temporary / Path(str(paths["execution_receipt"])).name
        write_jsonl_atomic(candidate_tmp, candidates)
        receipt["candidate_manifest_sha256"] = hash_file(candidate_tmp)
        write_json_atomic(receipt_tmp, receipt)
        _fsync_directory(temporary)
        os.replace(temporary, final_dir)
        _fsync_directory(final_dir.parent)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return receipt


def execute(
    route: RouteContract,
    root: Path,
    config_path: Path,
    seal_path: Path,
    seal_sha256: str,
    transport: Optional[httpx.BaseTransport] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    config_path = config_path.resolve(strict=True)
    seal_path = seal_path.resolve(strict=True)
    authorization = validate_authorization(route, root, config_path, seal_path, seal_sha256)
    config = authorization["config"]
    intents = authorization["intents"]
    for output in expected_outputs(config):
        if repo_path(root, output["path"], "preexecution output").exists():
            raise CensusError(f"preexecution output is not absent: {output['path']}")
    cutoff = parse_utc(config["source_contract"]["execution_start_not_after_utc"], "cutoff")
    if datetime.now(timezone.utc) >= cutoff:
        raise CensusError("execution-start cutoff has passed")
    started_at = _utc_now()
    paths = config["paths"]
    workspace = repo_path(root, paths["workspace"], "workspace")
    event_path = repo_path(root, paths["request_events"], "request events")
    event_schema = route.schema("event")
    census_id = str(config["census_id"])
    lock = _claim_lock(workspace, census_id, seal_sha256)
    events: List[Dict[str, Any]] = []
    genesis = _append_event(
        event_path,
        event_schema,
        census_id,
        events,
        {
            "event_type": "execution_started",
            "started_at_utc": started_at,
            "authorization_seal_path": relative(root, seal_path),
            "authorization_seal_sha256": seal_sha256,
            "freeze_path": authorization["seal"]["freeze_path"],
            "freeze_sha256": authorization["seal"]["freeze_sha256"],
            "freeze_recorded_git_commit": authorization["freeze"][evidence.RECORDED_COMMIT_FIELD],
            "review_path": authorization["seal"]["review_path"],
            "review_sha256": authorization["seal"]["review_sha256"],
            "reviewer_kind": authorization["review"]["reviewer_kind"],
            "request_intents_sha256": _freeze_sha(
                authorization["freeze"], str(paths["request_intents"])
            ),
            "execution_lock_path": relative(root, lock),
            "execution_lock_sha256": hash_file(lock),
        },
    )
    source = config["source_contract"]
    expected_content_type = str(source["expected_content_type"])
    candidates: List[Dict[str, Any]] = []
    seen_keys: set = set()
    inventory: List[Dict[str, Any]] = []
    with httpx.Client(
        timeout=float(source["timeout_seconds"]),
        follow_redirects=False,
        transport=transport,
        headers={"Accept": str(source["accept"]), "User-Agent": route.user_agent},
    ) as client:
        last_access = 0.0
        for intent in intents:
            delay = float(source["minimum_interval_seconds"]) - (time.monotonic() - last_access)
            if delay > 0:
                time.sleep(delay)
            request = client.build_request("GET", intent["endpoint"], params=intent["params"])
            if str(request.url) != intent["encoded_url"]:
                raise CensusError("HTTP encoding differs from the frozen intent")
            _append_event(
                event_path,
                event_schema,
                census_id,
                events,
                {
                    "event_type": "request_started",
                    "request_id": intent["request_id"],
                    "started_at_utc": _utc_now(),
                    "encoded_url": intent["encoded_url"],
                },
            )
            try:
                response = client.send(request, stream=True)
                body, complete = _bounded_body(response, int(source["maximum_response_bytes"]))
            except Exception as exc:
                _append_event(
                    event_path,
                    event_schema,
                    census_id,
                    events,
                    {
                        "event_type": "request_finished",
                        "request_id": intent["request_id"],
                        "finished_at_utc": _utc_now(),
                        "outcome": "terminal_transport_failure",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
                raise CensusError(f"{intent['request_id']} failed terminally in transport") from exc
            last_access = time.monotonic()
            digest = _sha256(body)
            body_path = workspace / "response_bodies" / digest[:2] / f"{digest}.response"
            atomic_bytes(body_path, body)
            headers = _headers(response)
            outcome = "success"
            error: Optional[str] = None
            rows: List[Dict[str, Any]] = []
            try:
                _validate_date(headers.get("date"))
                content_type = response.headers.get("content-type", "").split(";", 1)[0].strip()
                if (
                    response.status_code != 200
                    or response.history
                    or str(response.url) != intent["encoded_url"]
                    or content_type != expected_content_type
                    or "retry-after" in headers
                    or not complete
                ):
                    raise CensusError(
                        "HTTP status, redirect, URL, content type, Retry-After, or size violated "
                        "the contract"
                    )
                rows = route.parse_response(body, intent, config, digest)
                keys = [route.candidate_key(row) for row in rows]
                if len(set(keys)) != len(keys) or seen_keys.intersection(keys):
                    raise CensusError("candidate keys are duplicated within or across responses")
                seen_keys.update(keys)
            except Exception as exc:
                outcome = "terminal_delivery_or_schema_failure"
                error = str(exc)
            terminal = _append_event(
                event_path,
                event_schema,
                census_id,
                events,
                {
                    "event_type": "request_finished",
                    "request_id": intent["request_id"],
                    "finished_at_utc": _utc_now(),
                    "outcome": outcome,
                    "status_code": response.status_code,
                    "final_url": str(response.url),
                    "response_headers": headers,
                    "response_bytes": len(body),
                    "response_body_complete": complete,
                    "response_sha256": digest,
                    "response_body_path": str(body_path.relative_to(workspace)),
                    "candidate_rows": len(rows),
                    "error": error,
                },
            )
            if outcome != "success":
                raise CensusError(f"{intent['request_id']} ended with {terminal['outcome']}")
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
        for item in inventory:
            verified = _read_hashed(
                workspace / str(item["response_body_path"]),
                item["response_sha256"],
                "content-addressed response",
            )
            if len(verified) != item["response_bytes"]:
                raise CensusError("content-addressed response byte count drifted")
    except CensusError as exc:
        _append_event(
            event_path,
            event_schema,
            census_id,
            events,
            {
                "event_type": "execution_finished",
                "finished_at_utc": _utc_now(),
                "outcome": "terminal_cas_verification_failure",
                "error": str(exc),
            },
        )
        raise
    candidates.sort(key=route.sort_key)
    for sequence, row in enumerate(candidates, start=1):
        row["candidate_sequence"] = sequence
    try:
        event_body = event_path.read_bytes()
    except OSError as exc:
        raise CensusError("event ledger cannot be reread") from exc
    disk_events = jsonl_objects(event_body, "event ledger")
    validate_events(disk_events, census_id, event_schema)
    if disk_events != events:
        raise CensusError("event ledger differs from the in-memory chain")
    _validate_success_events(disk_events, intents, inventory, expected_content_type)
    receipt = {
        "schema_version": route.schema("execution"),
        "status": route.receipt_status,
        "census_id": census_id,
        "protocol_id": config["protocol_id"],
        "completed_at_utc": _utc_now(),
        "config_path": relative(root, config_path),
        "config_sha256": _freeze_sha(authorization["freeze"], relative(root, config_path)),
        "authorization_seal_path": relative(root, seal_path),
        "authorization_seal_sha256": seal_sha256,
        "freeze_recorded_git_commit": authorization["freeze"][evidence.RECORDED_COMMIT_FIELD],
        "reviewer_kind": authorization["review"]["reviewer_kind"],
        "execution_genesis_event_sha256": genesis["event_sha256"],
        "terminal_event_sha256": events[-1]["event_sha256"],
        "request_event_ledger_path": relative(root, event_path),
        "request_event_ledger_sha256": _sha256(event_body),
        "request_event_count": len(events),
        "request_intents_path": str(paths["request_intents"]),
        "request_intents_sha256": _freeze_sha(
            authorization["freeze"], str(paths["request_intents"])
        ),
        "successful_requests": len(intents),
        "response_inventory": inventory,
        "candidate_manifest_path": str(paths["candidate_manifest"]),
        "counts": {
            **route.summarize(candidates, config),
            "active_study_admissions": 0,
            "image_downloads": 0,
        },
        "limitations": list(route.limitations),
    }
    return _publish(root, config, candidates, receipt)


# --------------------------------------------------------------------------- CLI


def build_parser(route: RouteContract, default_config: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{route.route_id} census collector")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path(default_config))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="write exact intents and the commit-bound freeze")
    execute_parser = subparsers.add_parser("execute", help="run the one-shot authorized census")
    execute_parser.add_argument("--seal", type=Path, required=True)
    execute_parser.add_argument("--seal-sha256", required=True)
    return parser


def argument_path(root: Path, value: Path, label: str) -> Path:
    """Accept a repository-relative or an absolute path, as long as it lies inside root."""
    if value.is_absolute():
        return repo_path(root, relative(root, value), label)
    return repo_path(root, str(value), label)


def main(route: RouteContract, default_config: str, argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser(route, default_config).parse_args(argv)
    root = args.root.resolve()
    try:
        config_path = argument_path(root, args.config, "config")
        if args.command == "prepare":
            result = prepare(route, root, config_path)
        else:
            seal_path = argument_path(root, args.seal, "seal")
            result = execute(route, root, config_path, seal_path, args.seal_sha256)
    except CensusError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
