"""Canonical, file-backed Pilot-3 Freeze-B and post-generation execution layer.

This module deliberately performs no image-generation network I/O.  It opens
the generation gate only from repository files, verifies durable generation
evidence produced by :mod:`latent_art_bench.pilot3.generation`, measures every
successful PNG with the frozen Phase-A representation, and invokes the
registered analysis only after the complete on-disk evidence graph verifies.
"""

from __future__ import annotations

import fcntl
import json
import math
import os
import subprocess
import tempfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from latent_art_bench.features.learned_formal import (
    SOURCE_REPLICATION_POLICY,
    extract_learned_formal,
    learned_formal_vector_sha256,
)
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
from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig
from latent_art_bench.pilot3.analysis import (
    PRIMARY_OUTCOMES,
    _analyze_phase_b_core_for_verified_inputs,
    validate_schedule,
    validate_terminal_accounting,
)
from latent_art_bench.pilot3.design_freeze import (
    EXPECTED_ARTIST_IDS,
    EXPECTED_REQUESTED_LABEL,
    EXPECTED_SCHEDULE_COUNT,
    EXPECTED_TRANSPORT,
    verify_phase_b_freeze_bundle,
)
from latent_art_bench.pilot3.generation import (
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    ExecutionGateContext,
    GenerationAttempt,
    GenerationCell,
    GenerationGlobalStopLedger,
    GenerationSchedule,
    RequestGateContext,
    build_generation_execution_context,
    generation_attempt_ledger_semantic_sha256,
    generation_completion_report,
    generation_grid_sha256,
    global_stop_ledger_semantic_sha256,
    load_t12_generation_plan,
    post_intent_ledger_semantic_sha256,
    reconstruct_generation_execution_report,
    run_generation_grid,
    runtime_revalidation_ledger_semantic_sha256,
    verify_generation_completion_report,
    verify_generation_execution,
    verify_generation_execution_context,
    verify_successful_output_artifacts,
)
from latent_art_bench.pilot3.normalization_scope import (
    DEFAULT_AUTHORIZATION as NORMALIZATION_SCOPE_AUTHORIZATION_PATH,
)
from latent_art_bench.pilot3.normalization_scope import (
    SCHEMA_VERSION as NORMALIZATION_SCOPE_SCHEMA,
)
from latent_art_bench.pilot3.normalization_scope import (
    require_committed_normalization_scope_authorization,
)
from latent_art_bench.pilot3.phasea import (
    NORMALIZATION_REVALIDATION_LEDGER_PATH,
    PREPROCESSING_AMENDMENT_PATH,
    PREPROCESSING_INCIDENT_PATH,
    Pilot3PhaseAError,
    _load_vae,
    _verify_existing_acquisition,
    _verify_feature,
    effective_acquisition_rows,
    load_frozen_a_vector_state,
    load_phase_a_config,
    load_real_splits,
    project_a_vectors,
    require_preprocessing_incident_resolution,
    verify_a_vector_protocol,
    verify_external_holdout_result,
    verify_self_hash,
)
from latent_art_bench.pilot3.preprocessing import (
    PILOT3_NORMALIZATION_PROTOCOL_VERSION,
    pilot3_common_png_bytes,
)
from latent_art_bench.pilot3.qualification import (
    TRANSPORT_QUALIFICATION_ARTIFACT_PATH,
    TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH,
    TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH,
    TRANSPORT_QUALIFICATION_OUTPUT_ROOT,
    TRANSPORT_QUALIFICATION_PROMPT_SHA256,
    QualificationAttemptLedger,
    QualificationGateContext,
    QualificationIntentLedger,
    build_account_authorization_evidence,
    build_model_documentation_evidence,
    finalize_transport_qualification_artifact,
    run_neutral_transport_qualification,
    verify_account_authorization_evidence,
    verify_model_documentation_evidence,
    verify_transport_qualification_report,
)
from latent_art_bench.pilot3.transport import (
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthTransport,
    Pilot3TransportConfig,
    capture_pilot3_oauth_runtime_fingerprint,
    verify_pilot3_production_runtime_fingerprint,
)


class Pilot3ExecutionError(RuntimeError):
    """Raised when a Pilot-3 execution or analysis gate fails closed."""


GENERATION_GATE_SCHEMA = "pilot3-generation-gate/1.0"
GENERATION_AUTHORIZATION_SCHEMA = "pilot3-generation-authorization/1.0"
GENERATION_AUTHORIZATION_CLOSED = "closed"
GENERATION_AUTHORIZATION_OPEN = "preregistered_generation_gate_open"
TERMINAL_ROW_SCHEMA = "pilot3-terminal-disposition/2.0"
TERMINAL_ENVELOPE_SCHEMA = "pilot3-terminal-disposition-manifest/2.0"
GENERATED_PREPROCESSING_SCHEMA = "pilot3-generated-preprocessing/2.0"
GENERATED_NORMALIZATION_CONTRACT_SCHEMA = (
    "pilot3-generated-normalization-contract/2.0"
)
GENERATED_A_VECTOR_SCHEMA = "pilot3-generated-a-vector/1.0"
GENERATED_DISTANCE_SCHEMA = "pilot3-generated-a-vector-distance/1.0"
GENERATED_MEASUREMENT_SCHEMA = "pilot3-generated-a-vector-measurement/2.0"
COMPLETION_SCHEMA = "pilot3-scientific-completion/2.0"
REQUIREMENT_AUDIT_SCHEMA = "pilot3-requirement-audit/1.0"
ARTIFACT_INDEX_SCHEMA = "pilot3-artifact-index/1.0"

CANONICAL_PATHS: Dict[str, Path] = {
    "study_config": Path("configs/pilot_3/study.json"),
    "phase_a_config": Path("configs/pilot_3/phase_a.json"),
    "generation_authorization": Path("configs/pilot_3/generation_authorization.json"),
    "protocol": Path("docs/PILOT_3_PROTOCOL.md"),
    "prompt_manifest": Path("data/manifests/pilot_3/prompts.jsonl"),
    "schedule_manifest": Path("data/manifests/pilot_3/schedule.jsonl"),
    "a_vector_protocol": Path("reports/pilot_3/evidence/a_vector_protocol.json"),
    "a_vector_external": Path("reports/pilot_3/evidence/a_vector_external_validation.json"),
    "external_unseal_receipt": Path("artifacts/pilot_3/external_unseal_receipt.json"),
    "preprocessing_incident": PREPROCESSING_INCIDENT_PATH,
    "preprocessing_amendment": PREPROCESSING_AMENDMENT_PATH,
    "normalization_revalidations": NORMALIZATION_REVALIDATION_LEDGER_PATH,
    "transport_qualification": Path("reports/pilot_3/evidence/transport_qualification.json"),
    "account_authorization": Path("reports/pilot_3/evidence/account_authorization.json"),
    "model_documentation": Path("reports/pilot_3/evidence/model_documentation.json"),
    "oauth_runtime_fingerprint": Path("reports/pilot_3/evidence/oauth_runtime_fingerprint.json"),
    "generation_gate": Path("reports/pilot_3/evidence/generation_gate.json"),
    "generation_post_intents": Path("artifacts/pilot_3/generation_post_intents.jsonl"),
    "generation_attempts": Path("artifacts/pilot_3/generation_attempts.jsonl"),
    "generation_global_stops": Path(
        "artifacts/pilot_3/generation_global_stop_dispositions.jsonl"
    ),
    "generation_runtime_revalidations": Path(
        "reports/pilot_3/evidence/generation_runtime_revalidations.jsonl"
    ),
    "generation_execution_context": Path(
        "reports/pilot_3/evidence/generation_execution_context.json"
    ),
    "generation_execution": Path("reports/pilot_3/evidence/generation_execution.json"),
    "qualification_execution_lock": Path(
        "artifacts/pilot_3/transport_qualification.lock"
    ),
    "generation_execution_lock": Path("artifacts/pilot_3/generation_execution.lock"),
    "generation_completion": Path("reports/pilot_3/evidence/generation_completion.json"),
    "successful_outputs": Path("reports/pilot_3/evidence/successful_output_manifest.json"),
    "generated_output_root": Path("outputs/pilot_3/generated"),
    "generated_normalized_root": Path("artifacts/pilot_3/generated_normalized"),
    "generated_preprocessing": Path("artifacts/pilot_3/generated_preprocessing.jsonl"),
    "generated_a_vectors": Path("artifacts/pilot_3/generated_a_vectors.jsonl"),
    "generated_distances": Path("artifacts/pilot_3/generated_a_vector_distances.jsonl"),
    "generated_measurement": Path("reports/pilot_3/evidence/generated_a_vector_measurement.json"),
    "terminal_rows": Path("reports/pilot_3/evidence/terminal_dispositions.jsonl"),
    "terminal_envelope": Path("reports/pilot_3/evidence/terminal_disposition_manifest.json"),
    "analysis": Path("reports/pilot_3/analysis.json"),
    "report": Path("reports/pilot_3/REPORT.md"),
    "completion": Path("reports/pilot_3/completion.json"),
    "requirement_audit": Path("reports/pilot_3/requirement_audit.json"),
    "artifact_index": Path("reports/pilot_3/artifact_index.json"),
}


# The gate binds code and tests that can change an estimand, eligibility,
# transport semantics, preprocessing, measurement, inference, or reporting.
# It intentionally excludes generated artifacts and P3-T14 itself.
FREEZE_B_CODE_CLOSURE: Tuple[Path, ...] = tuple(
    Path(value)
    for value in (
        "pyproject.toml",
        "uv.lock",
        "docs/PILOT_3_PROTOCOL.md",
        "docs/PILOT_3_R2_OFFICIAL_MET.md",
        "docs/PILOT_3_PREPROCESSING_DETERMINISM_AMENDMENT.md",
        "configs/pilot_3/study.json",
        "configs/pilot_3/phase_a.json",
        "configs/pilot_3/corpus_freeze.json",
        "configs/pilot_3/external_museum_blocks.json",
        "configs/pilot_3/lee_review.json",
        "configs/pilot_3/metadata/authoritative_candidates.jsonl",
        "configs/pilot_3/metadata/source_snapshots.json",
        "configs/pilot_3/planning.json",
        "data/manifests/pilot_3/corpus_selection.jsonl",
        "data/manifests/pilot_3/real_splits.jsonl",
        "data/manifests/pilot_3/prompts.jsonl",
        "data/manifests/pilot_3/schedule.jsonl",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/cli.py",
        "src/latent_art_bench/features/learned_formal.py",
        "src/latent_art_bench/pilot2/config.py",
        "src/latent_art_bench/pilot2/learned_formal.py",
        "src/latent_art_bench/pilot2/preprocessing.py",
        "src/latent_art_bench/pilot2/schemas.py",
        "src/latent_art_bench/pilot3/analysis.py",
        "src/latent_art_bench/pilot3/cli.py",
        "src/latent_art_bench/pilot3/corpus.py",
        "src/latent_art_bench/pilot3/design.py",
        "src/latent_art_bench/pilot3/design_freeze.py",
        "src/latent_art_bench/pilot3/execution.py",
        "src/latent_art_bench/pilot3/feasibility.py",
        "src/latent_art_bench/pilot3/generation.py",
        "src/latent_art_bench/pilot3/lee.py",
        "src/latent_art_bench/pilot3/met_r2.py",
        "src/latent_art_bench/pilot3/normalization_scope.py",
        "src/latent_art_bench/pilot3/phasea.py",
        "src/latent_art_bench/pilot3/planning.py",
        "src/latent_art_bench/pilot3/preprocessing.py",
        "src/latent_art_bench/pilot3/qualification.py",
        "src/latent_art_bench/pilot3/transport.py",
        "tests/pilot3/test_design.py",
        "tests/pilot3/test_design_freeze.py",
        "tests/pilot3/test_feasibility.py",
        "tests/pilot3/test_generation_transport.py",
        "tests/pilot3/test_lee.py",
        "tests/pilot3/test_met_r2.py",
        "tests/pilot3/test_normalization_scope.py",
        "tests/pilot3/test_phase_b_analysis.py",
        "tests/pilot3/test_phasea.py",
        "tests/pilot3/test_pilot3_corpus.py",
        "tests/pilot3/test_planning.py",
        "tests/pilot3/test_transport_qualification.py",
        "tests/pilot3/test_execution.py",
        "tests/pilot3/test_runtime_workflow.py",
    )
)

FREEZE_B_EVIDENCE_CLOSURE: Tuple[Path, ...] = tuple(
    Path(value)
    for value in (
        "reports/pilot_3/planning_index.json",
        "reports/pilot_3/evidence/artist_source_feasibility.json",
        "reports/pilot_3/evidence/pilot2_baseline_recovery.json",
        "reports/pilot_3/evidence/design_sensitivity.json",
        "reports/pilot_3/evidence/corpus_selection.json",
        "reports/pilot_3/evidence/holdout_seal.json",
        "reports/pilot_3/evidence/preprocessing_determinism_incident.json",
        "reports/pilot_3/evidence/preprocessing_determinism_amendment.json",
        "reports/pilot_3/evidence/met_asset_provider_incident.json",
        "reports/pilot_3/evidence/met_r2_authorization.json",
        "artifacts/pilot_3/met_r2_metadata_attempts.jsonl",
        "data/manifests/pilot_3/met_r2_targets.jsonl",
        "reports/pilot_3/evidence/met_r2_metadata_freeze.json",
        "reports/pilot_3/evidence/normalization_scope_extension.json",
        "artifacts/pilot_3/met_r2_image_attempts.jsonl",
        "artifacts/pilot_3/met_r2_image_acquisitions.jsonl",
        "reports/pilot_3/evidence/a_vector_protocol.json",
        "reports/pilot_3/evidence/a_vector_external_validation.json",
        "artifacts/pilot_3/external_unseal_receipt.json",
        "reports/pilot_3/evidence/lee_replication.json",
        "reports/pilot_3/evidence/human_validation_disposition.json",
        "reports/pilot_3/evidence/phase_b_design.json",
        "reports/pilot_3/evidence/prompt_schedule_contract.json",
        "reports/pilot_3/evidence/analysis_contract.json",
        "reports/pilot_3/evidence/transport_qualification.json",
        "reports/pilot_3/evidence/oauth_runtime_fingerprint.json",
        "reports/pilot_3/evidence/account_authorization.json",
        "reports/pilot_3/evidence/model_documentation.json",
        "artifacts/pilot_3/transport_qualification_post_intents.jsonl",
        "artifacts/pilot_3/transport_qualification_attempts.jsonl",
        "artifacts/pilot_3/development_acquisition_intents.jsonl",
        "artifacts/pilot_3/external_acquisition_intents.jsonl",
        "artifacts/pilot_3/development_acquisition_http_attempts.jsonl",
        "artifacts/pilot_3/external_acquisition_http_attempts.jsonl",
        "artifacts/pilot_3/development_acquisitions.jsonl",
        "artifacts/pilot_3/development_normalization_revalidations.jsonl",
        "artifacts/pilot_3/external_acquisitions.jsonl",
        "artifacts/pilot_3/development_a_vectors.jsonl",
        "artifacts/pilot_3/external_a_vectors.jsonl",
        "artifacts/pilot_3/determinism_probes.jsonl",
        "artifacts/pilot_3/a_vector_state/pca_mean.npy",
        "artifacts/pilot_3/a_vector_state/pca_components.npy",
        "artifacts/pilot_3/a_vector_state/artist_centroids.npy",
    )
)

# This record is intentionally absent from the immutable P3-T07 closure.  It is
# the sole mutable operational status file: Freeze A1 records it as closed,
# then P3-T14 changes it once to the exact open form derived from verified
# P3-T01--P3-T13 evidence.  Runtime authorization requires this file and the
# matching P3-T14 gate to be committed and clean together.
FREEZE_B_OPERATIONAL_CLOSURE: Tuple[Path, ...] = (
    CANONICAL_PATHS["generation_authorization"],
)


def _root(root: Path) -> Path:
    return Path(root).expanduser().resolve()


def _path(root: Path, relative: Path) -> Path:
    resolved = (_root(root) / relative).resolve()
    try:
        resolved.relative_to(_root(root))
    except ValueError as exc:
        raise Pilot3ExecutionError(f"canonical path escapes repository: {relative}") from exc
    return resolved


def _require_file(root: Path, relative: Path) -> Path:
    path = _path(root, relative)
    if not path.is_file():
        raise Pilot3ExecutionError(f"required Pilot-3 artifact is missing: {relative}")
    return path


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _persist_json_once(path: Path, value: Mapping[str, Any], *, label: str) -> None:
    """Create canonical JSON once; accept only a byte-identical recovery."""

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        json.dumps(dict(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    if resolved.exists():
        if not resolved.is_file() or resolved.read_bytes() != rendered:
            raise Pilot3ExecutionError(f"existing {label} differs from canonical evidence")
        return
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{resolved.name}.", dir=resolved.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, resolved)
        except FileExistsError:
            if not resolved.is_file() or resolved.read_bytes() != rendered:
                raise Pilot3ExecutionError(f"{label} creation collided with divergent data")
        finally:
            os.unlink(temporary)
        _fsync_directory(resolved.parent)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


@contextmanager
def _exclusive_workflow_lock(path: Path, *, label: str):
    """Hold a cross-process advisory lock for the complete production run."""

    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(resolved, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Pilot3ExecutionError(f"another {label} process holds the run lock") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_seal(value: Mapping[str, Any], *, field: str, label: str) -> str:
    payload = dict(value)
    recorded = payload.pop(field, None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise Pilot3ExecutionError(f"{label} has a stale or invalid {field}")
    return str(recorded)


def _seal(value: Mapping[str, Any], *, field: str) -> Dict[str, Any]:
    payload = dict(value)
    payload.pop(field, None)
    payload[field] = stable_hash(payload)
    return payload


def _semantic_field(value: Mapping[str, Any], *, label: str) -> Tuple[str, str]:
    present = [
        field for field in ("result_sha256", "semantic_sha256", "report_sha256") if field in value
    ]
    if len(present) != 1:
        raise Pilot3ExecutionError(
            f"{label} must have exactly one recognized deterministic self-hash"
        )
    field = present[0]
    return field, _verify_seal(value, field=field, label=label)


def _json_binding(
    root: Path,
    relative: Path,
    *,
    label: str,
    statuses: Optional[Iterable[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    path = _require_file(root, relative)
    raw = read_json(path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError(f"{label} must be a JSON object")
    value = dict(raw)
    field, semantic = _semantic_field(value, label=label)
    if statuses is not None and value.get("status") not in set(statuses):
        raise Pilot3ExecutionError(
            f"{label} status {value.get('status')!r} does not satisfy Freeze B"
        )
    return value, {
        "path": relative.as_posix(),
        "file_sha256": hash_file(path),
        "self_hash_field": field,
        "semantic_sha256": semantic,
        "status": value.get("status"),
    }


def _jsonl_binding(
    root: Path,
    relative: Path,
    *,
    row_hash_field: str,
    label: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    path = _require_file(root, relative)
    rows = read_jsonl(path)
    if any(not isinstance(row, Mapping) for row in rows):
        raise Pilot3ExecutionError(f"{label} contains a non-object row")
    normalized = [dict(row) for row in rows]
    for index, row in enumerate(normalized, 1):
        _verify_seal(row, field=row_hash_field, label=f"{label}[{index}]")
    return normalized, {
        "path": relative.as_posix(),
        "file_sha256": hash_file(path),
        "semantic_sha256": stable_hash(normalized),
        "row_count": len(normalized),
        "row_hash_field": row_hash_field,
    }


def _require_committed_closure(root: Path, paths: Iterable[Path]) -> None:
    repository = _root(root)
    relative_paths = sorted(set(paths))
    values = [path.as_posix() for path in relative_paths]
    if not values:
        return
    if any(path.is_absolute() or ".." in path.parts for path in relative_paths):
        raise Pilot3ExecutionError("Freeze-B closure contains a non-repository path")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", *values],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *values],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked.returncode != 0 or dirty.returncode != 0 or dirty.stdout:
        detail = dirty.stdout.splitlines()[0] if dirty.stdout else tracked.stderr.strip()
        raise Pilot3ExecutionError(
            "Freeze-B closure path is not committed and clean"
            + (f": {detail}" if detail else "")
        )


def _transport_config() -> Pilot3TransportConfig:
    config = Pilot3TransportConfig()
    if tuple(config.frozen_requested_labels) != (EXPECTED_REQUESTED_LABEL,):
        raise Pilot3ExecutionError("runtime transport is not restricted to gpt-image-2")
    return config


def _load_t12_plan(root: Path) -> Tuple[List[GenerationCell], GenerationSchedule]:
    return load_t12_generation_plan(
        _require_file(root, CANONICAL_PATHS["prompt_manifest"]),
        _require_file(root, CANONICAL_PATHS["schedule_manifest"]),
        transport_config=_transport_config(),
        namespace="pilot3-assignment-order-v1",
        seed=20260903,
        max_parallel=4,
    )


def _load_runtime_fingerprint(root: Path) -> Pilot3OAuthRuntimeFingerprint:
    raw = read_json(_require_file(root, CANONICAL_PATHS["oauth_runtime_fingerprint"]))
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("OAuth runtime fingerprint must be a JSON object")
    return Pilot3OAuthRuntimeFingerprint.model_validate(raw)


def _verify_strict_qualification_evidence(
    root: Path,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)
    authorization_raw = read_json(
        _require_file(root, CANONICAL_PATHS["account_authorization"])
    )
    documentation_raw = read_json(
        _require_file(root, CANONICAL_PATHS["model_documentation"])
    )
    if not isinstance(authorization_raw, Mapping) or not isinstance(
        documentation_raw, Mapping
    ):
        raise Pilot3ExecutionError(
            "P3-T11 authorization and documentation evidence must be JSON objects"
        )
    try:
        authorization = verify_account_authorization_evidence(
            authorization_raw, config
        )
        documentation = verify_model_documentation_evidence(
            documentation_raw, config, fingerprint
        )
    except Exception as exc:
        raise Pilot3ExecutionError(
            f"strict P3-T11 evidence does not verify: {type(exc).__name__}: {exc}"
        ) from exc
    return (
        authorization.model_dump(mode="json"),
        documentation.model_dump(mode="json"),
    )


def write_qualification_authorization(root: Path) -> Dict[str, Any]:
    """Write the exact current-task authorization scope without network I/O."""

    resolved_root = _root(root)
    evidence = build_account_authorization_evidence(_transport_config()).model_dump(
        mode="json"
    )
    _persist_json_once(
        _path(resolved_root, CANONICAL_PATHS["account_authorization"]),
        evidence,
        label="P3-T11 account authorization",
    )
    return evidence


def capture_oauth_runtime_evidence(root: Path) -> Dict[str, Any]:
    """Capture or verify the exact listener fingerprint and documentation record.

    The first invocation performs only health/model-catalog GETs; it never sends
    an image-generation POST.  Once the fingerprint exists, reruns are offline
    and refuse divergent evidence.
    """

    resolved_root = _root(root)
    config = _transport_config()
    write_qualification_authorization(resolved_root)
    fingerprint_path = _path(
        resolved_root, CANONICAL_PATHS["oauth_runtime_fingerprint"]
    )
    if fingerprint_path.exists():
        fingerprint = _load_runtime_fingerprint(resolved_root)
    else:
        fingerprint = capture_pilot3_oauth_runtime_fingerprint(config)
        verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)
        _persist_json_once(
            fingerprint_path,
            fingerprint.model_dump(mode="json"),
            label="Pilot-3 OAuth runtime fingerprint",
        )
    verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)
    documentation = build_model_documentation_evidence(
        config, fingerprint
    ).model_dump(mode="json")
    _persist_json_once(
        _path(resolved_root, CANONICAL_PATHS["model_documentation"]),
        documentation,
        label="P3-T11 model documentation",
    )
    _verify_strict_qualification_evidence(resolved_root, config, fingerprint)
    return {
        "status": "ready",
        "image_generation_post_count": 0,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "account_authorization_evidence_sha256": build_account_authorization_evidence(
            config
        ).evidence_sha256,
        "model_documentation_evidence_sha256": documentation["evidence_sha256"],
    }


def _verify_p3_t11(root: Path) -> Tuple[Dict[str, Any], Path]:
    """Recompute the one-shot neutral P3-T11 from its exact durable evidence."""

    report_path = _require_file(root, CANONICAL_PATHS["transport_qualification"])
    raw = read_json(report_path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("P3-T11 transport qualification is not a JSON object")
    report = dict(raw)
    config = _transport_config()
    fingerprint = _load_runtime_fingerprint(root)
    _verify_strict_qualification_evidence(root, config, fingerprint)
    intent_ledger = QualificationIntentLedger(
        _require_file(root, TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH)
    )
    attempt_ledger = QualificationAttemptLedger(
        _require_file(root, TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH)
    )
    expected = verify_transport_qualification_report(
        report,
        phase_a_result_path=_require_file(root, CANONICAL_PATHS["a_vector_external"]),
        account_authorization_evidence_path=_require_file(
            root, CANONICAL_PATHS["account_authorization"]
        ),
        model_documentation_evidence_path=_require_file(
            root, CANONICAL_PATHS["model_documentation"]
        ),
        config=config,
        fingerprint=fingerprint,
        intent_ledger=intent_ledger,
        attempt_ledger=attempt_ledger,
        output_root=_path(root, TRANSPORT_QUALIFICATION_OUTPUT_ROOT),
    )
    if (
        expected.get("status") != "pass"
        or expected.get("outside_artist_content_grid") is not True
        or expected.get("analytic_grid_membership") is not False
        or expected.get("physical_post_count") != 1
        or expected.get("retry_allowed") is not False
        or expected.get("requested_model_label") != EXPECTED_REQUESTED_LABEL
        or expected.get("executed_model_claims") is not False
        or expected.get("snapshot_identity_claims") is not False
        or expected.get("output_hash_png_and_geometry_verified") is not True
    ):
        raise Pilot3ExecutionError("P3-T11 does not satisfy the frozen neutral qualification")
    output = expected.get("output_evidence")
    if not isinstance(output, Mapping):
        raise Pilot3ExecutionError("P3-T11 pass lacks output evidence")
    output_path = _resolve_recorded(root, output.get("output_path"))
    if not output_path.is_file() or hash_file(output_path) != output.get("output_sha256"):
        raise Pilot3ExecutionError("P3-T11 output evidence is missing or stale")
    return expected, output_path


def _verified_p3_t07_closure_paths(
    root: Path, protocol: Mapping[str, Any]
) -> Tuple[Path, ...]:
    """Return only safe, byte-current paths from P3-T07's complete closure."""

    closure = protocol.get("closure_file_sha256")
    if not isinstance(closure, Mapping) or not closure:
        raise Pilot3ExecutionError("P3-T07 has no closure hashes")
    paths: List[Path] = []
    for relative, expected in closure.items():
        if not isinstance(relative, str) or not _is_sha256(expected):
            raise Pilot3ExecutionError("P3-T07 closure contains an invalid binding")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise Pilot3ExecutionError("P3-T07 closure path escapes the repository")
        if hash_file(_require_file(root, path)) != expected:
            raise Pilot3ExecutionError(f"P3-T07 closure is stale: {relative}")
        paths.append(path)
    return tuple(sorted(paths))


def _verify_phase_a_artifacts(
    root: Path,
    protocol: Mapping[str, Any],
    external: Mapping[str, Any],
) -> None:
    """Verify the exact Phase-A files P3-T07/P3-T08 summarize."""

    try:
        recomputed_protocol = verify_a_vector_protocol(_root(root), protocol)
        recomputed_external = verify_external_holdout_result(
            _root(root),
            external_unseal_token=str(recomputed_protocol["result_sha256"]),
        )
    except Pilot3PhaseAError as exc:
        raise Pilot3ExecutionError(
            f"Phase-A deterministic recomputation failed: {exc}"
        ) from exc
    if dict(protocol) != recomputed_protocol or dict(external) != recomputed_external:
        raise Pilot3ExecutionError(
            "P3-T07/P3-T08 differ from deterministic recomputation"
        )

    phase_config_path = _require_file(root, CANONICAL_PATHS["phase_a_config"])
    phase_config = load_phase_a_config(root)
    if (
        protocol.get("phase_a_config") != phase_config
        or protocol.get("phase_a_config_file_sha256") != hash_file(phase_config_path)
    ):
        raise Pilot3ExecutionError("P3-T07 binds a stale Phase-A configuration")
    if external.get("a_vector_protocol_result_sha256") != protocol.get("result_sha256"):
        raise Pilot3ExecutionError("P3-T08 does not bind the exact frozen P3-T07")
    load_frozen_a_vector_state(_root(root), protocol)
    _verified_p3_t07_closure_paths(root, protocol)

    config_paths = phase_config["paths"]
    split_rows = load_real_splits(_root(root), phase_config)
    split_by_work = {
        str(row["canonical_work_id"]): row for row in split_rows
    }
    artist_count = len(phase_config["finite_roster"]["artist_ids"])
    allocation = phase_config["allocation"]
    expected_development_count = artist_count * (
        int(allocation["training_per_artist"])
        + int(allocation["calibration_per_artist"])
    )
    expected_external_count = artist_count * int(allocation["external_per_artist"])
    expected_split_count = expected_development_count + expected_external_count
    if len(split_by_work) != expected_split_count:
        raise Pilot3ExecutionError(
            "Phase-A split identity does not match the frozen per-artist allocation"
        )
    acquisition_rows: Dict[str, Dict[str, Any]] = {}
    for phase, key in (
        ("development", "development_acquisitions"),
        ("external", "external_acquisitions"),
    ):
        path = _require_file(root, Path(config_paths[key]))
        originals: Dict[str, Dict[str, Any]] = {}
        for index, raw in enumerate(read_jsonl(path), 1):
            if not isinstance(raw, Mapping):
                raise Pilot3ExecutionError(f"{phase} acquisition row {index} is not an object")
            row = dict(raw)
            work_id = row.get("canonical_work_id")
            if (
                not isinstance(work_id, str)
                or work_id in originals
                or work_id in acquisition_rows
                or work_id not in split_by_work
            ):
                raise Pilot3ExecutionError("Phase-A acquisition work ids are invalid or duplicate")
            split = split_by_work[work_id]
            expected_phase = (
                "external" if split["partition"] == "external_holdout" else "development"
            )
            if phase != expected_phase:
                raise Pilot3ExecutionError("Phase-A acquisition is in the wrong phase ledger")
            _verify_existing_acquisition(
                row,
                _root(root),
                split,
                phase_config,
                protocol["result_sha256"] if phase == "external" else None,
                expected_external_receipt_sha256=(
                    str(external["external_unseal_receipt_sha256"])
                    if phase == "external"
                    else None
                ),
            )
            originals[work_id] = row
        try:
            effective = effective_acquisition_rows(
                _root(root),
                phase_config,
                phase,
                originals,
                require_committed=True,
            )
        except Pilot3PhaseAError as exc:
            raise Pilot3ExecutionError(
                f"Phase-A effective acquisition resolution failed: {exc}"
            ) from exc
        if set(effective) != set(originals):
            raise Pilot3ExecutionError(
                f"{phase} effective acquisition coverage differs from its base ledger"
            )
        acquisition_rows.update(effective)
    if set(acquisition_rows) != set(split_by_work):
        raise Pilot3ExecutionError("Phase-A acquisition coverage is not the exact frozen split")

    for phase, key in (
        ("development", "development_acquisition_intents"),
        ("external", "external_acquisition_intents"),
    ):
        path = _require_file(root, Path(config_paths[key]))
        raw_rows = read_jsonl(path)
        expected_splits = {
            work_id: split
            for work_id, split in split_by_work.items()
            if (
                (split["partition"] == "external_holdout")
                == (phase == "external")
            )
        }
        seen: set[str] = set()
        for index, raw in enumerate(raw_rows, 1):
            if not isinstance(raw, Mapping):
                raise Pilot3ExecutionError(
                    f"{phase} acquisition intent row {index} is not an object"
                )
            row = dict(raw)
            work_id = row.get("canonical_work_id")
            if not isinstance(work_id, str) or work_id in seen or work_id not in expected_splits:
                raise Pilot3ExecutionError(
                    f"{phase} acquisition intent identities are invalid or duplicate"
                )
            acquisition = acquisition_rows[work_id]
            split = expected_splits[work_id]
            expected_payload = {
                "record_type": "pilot3_real_acquisition_intent",
                "schema_version": "1.0",
                "canonical_work_id": work_id,
                "artist_id": split["artist_id"],
                "asset_provider": split["asset_provider"],
                "collection_block_id": split["collection_block_id"],
                "museum_accession": split["museum_accession"],
                "source_id": split["source_id"],
                "partition": split["partition"],
                "image_url": split["image_url"],
                "source_url": split["source_url"],
                "delivery_width": split["delivery_width"],
                "delivery_height": split["delivery_height"],
                "acquisition_route": acquisition["acquisition_route"],
                "phase_a_config_file_sha256": hash_file(phase_config_path),
                "external_protocol_result_sha256": (
                    protocol["result_sha256"] if phase == "external" else None
                ),
                "external_unseal_receipt_sha256": (
                    external["external_unseal_receipt_sha256"]
                    if phase == "external"
                    else None
                ),
            }
            expected = {
                **expected_payload,
                "intent_id": f"p3-real-intent-{stable_hash(expected_payload)[:24]}",
            }
            if row != expected or acquisition.get("intent_id") != expected["intent_id"]:
                raise Pilot3ExecutionError(
                    f"{phase} acquisition intent is stale: {work_id}"
                )
            seen.add(work_id)
        if seen != set(expected_splits):
            raise Pilot3ExecutionError(
                f"{phase} acquisition intents do not cover the exact frozen split"
            )

    feature_groups: Dict[str, List[Dict[str, Any]]] = {}
    for phase, key in (
        ("development", "development_features"),
        ("external", "external_features"),
    ):
        path = _require_file(root, Path(config_paths[key]))
        rows: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for index, raw in enumerate(read_jsonl(path), 1):
            if not isinstance(raw, Mapping):
                raise Pilot3ExecutionError(f"{phase} feature row {index} is not an object")
            row = dict(raw)
            work_id = row.get("canonical_work_id")
            if not isinstance(work_id, str) or work_id in seen or work_id not in acquisition_rows:
                raise Pilot3ExecutionError("Phase-A feature work ids are invalid or duplicate")
            split = split_by_work[work_id]
            expected_phase = (
                "external" if split["partition"] == "external_holdout" else "development"
            )
            if phase != expected_phase:
                raise Pilot3ExecutionError("Phase-A feature is in the wrong phase ledger")
            _verify_feature(
                row,
                acquisition_rows[work_id],
                split,
                phase_config,
                expected_runtime=(
                    protocol["runtime_environment"] if phase == "external" else None
                ),
            )
            seen.add(work_id)
            rows.append(row)
        feature_groups[phase] = sorted(rows, key=lambda row: str(row["canonical_work_id"]))
    if (
        len(feature_groups["development"]) != expected_development_count
        or stable_hash(feature_groups["development"])
        != protocol.get("development_feature_manifest_semantic_sha256")
        or len(feature_groups["external"]) != expected_external_count
        or stable_hash(feature_groups["external"])
        != external.get("external_feature_manifest_semantic_sha256")
    ):
        raise Pilot3ExecutionError("Phase-A feature manifests do not match P3-T07/P3-T08")
    if external.get("external_work_ids") != [
        str(row["canonical_work_id"]) for row in feature_groups["external"]
    ]:
        raise Pilot3ExecutionError("P3-T08 external work identity/order is stale")
    expected_external_acquisitions = external.get("external_acquisition_record_sha256")
    if not isinstance(expected_external_acquisitions, Mapping):
        raise Pilot3ExecutionError("P3-T08 lacks external acquisition bindings")
    for row in feature_groups["external"]:
        work_id = str(row["canonical_work_id"])
        if acquisition_rows[work_id].get("record_sha256") != expected_external_acquisitions.get(
            work_id
        ):
            raise Pilot3ExecutionError(f"P3-T08 external acquisition is stale: {work_id}")
    checks = external.get("gate_checks")
    if (
        not isinstance(checks, Mapping)
        or not checks
        or any(value is not True for value in checks.values())
    ):
        raise Pilot3ExecutionError("P3-T08 pass has incomplete gate checks")


def _qualification_committed_closure(
    root: Path, protocol: Mapping[str, Any]
) -> Tuple[Path, ...]:
    phase_config = load_phase_a_config(root)
    config_paths = phase_config["paths"]
    paths = set(FREEZE_B_CODE_CLOSURE)
    closure = protocol.get("closure_file_sha256")
    if not isinstance(closure, Mapping) or not closure:
        raise Pilot3ExecutionError("P3-T07 has no committed closure")
    paths.update(Path(relative) for relative in closure)
    paths.update(
        {
            CANONICAL_PATHS["a_vector_protocol"],
            CANONICAL_PATHS["a_vector_external"],
            CANONICAL_PATHS["external_unseal_receipt"],
            CANONICAL_PATHS["account_authorization"],
            CANONICAL_PATHS["model_documentation"],
            CANONICAL_PATHS["oauth_runtime_fingerprint"],
            CANONICAL_PATHS["generation_authorization"],
            Path(config_paths["external_acquisition_intents"]),
            Path(config_paths["external_acquisition_attempts"]),
            Path(config_paths["external_acquisitions"]),
            Path(config_paths["external_features"]),
        }
    )
    return tuple(sorted(paths))


def verify_transport_qualification_window(
    root: Path,
    *,
    context: Optional[QualificationGateContext] = None,
    require_committed: bool = True,
) -> Dict[str, Any]:
    """Verify the only production authorization path for the P3-T11 POST."""

    resolved_root = _root(root)
    gate_path = _path(resolved_root, CANONICAL_PATHS["generation_gate"])
    if gate_path.exists():
        raise Pilot3ExecutionError("P3-T11 window closed because P3-T14 exists")
    tracked_gate = subprocess.run(
        [
            "git",
            "ls-files",
            "--error-unmatch",
            "--",
            CANONICAL_PATHS["generation_gate"].as_posix(),
        ],
        cwd=resolved_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if tracked_gate.returncode == 0:
        raise Pilot3ExecutionError("P3-T11 window closed because P3-T14 is tracked")
    for relative in (
        CANONICAL_PATHS["transport_qualification"],
        TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH,
        TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH,
    ):
        if _path(resolved_root, relative).exists():
            raise Pilot3ExecutionError(
                f"P3-T11 one-shot window was already consumed: {relative}"
            )

    protocol_raw = read_json(
        _require_file(resolved_root, CANONICAL_PATHS["a_vector_protocol"])
    )
    external_raw = read_json(
        _require_file(resolved_root, CANONICAL_PATHS["a_vector_external"])
    )
    if not isinstance(protocol_raw, Mapping) or not isinstance(external_raw, Mapping):
        raise Pilot3ExecutionError("P3-T07 and P3-T08 must be JSON objects")
    protocol = dict(protocol_raw)
    external = dict(external_raw)
    _verify_phase_a_artifacts(resolved_root, protocol, external)
    _verify_generation_authorization(resolved_root, require_open=False)
    authorization = read_json(
        _require_file(resolved_root, CANONICAL_PATHS["generation_authorization"])
    )
    if not isinstance(authorization, Mapping) or authorization.get("status") != "closed":
        raise Pilot3ExecutionError("P3-T11 requires generation authorization closed")

    config = _transport_config()
    fingerprint = _load_runtime_fingerprint(resolved_root)
    _verify_strict_qualification_evidence(resolved_root, config, fingerprint)
    if require_committed:
        _require_committed_closure(
            resolved_root,
            _qualification_committed_closure(resolved_root, protocol),
        )
    if context is not None:
        expected = {
            "phase_a_result_sha256": external.get("result_sha256"),
            "phase_a_result_file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["a_vector_external"])
            ),
            "account_authorization_evidence_file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["account_authorization"])
            ),
            "model_documentation_evidence_file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["model_documentation"])
            ),
            "transport_config_sha256": config.config_sha256,
            "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
            "neutral_prompt_sha256": TRANSPORT_QUALIFICATION_PROMPT_SHA256,
            "existing_intent_count": 0,
            "existing_attempt_count": 0,
        }
        for field, required in expected.items():
            if getattr(context, field) != required:
                raise Pilot3ExecutionError(
                    f"P3-T11 gate context does not match committed evidence: {field}"
                )
    return {
        "status": "open_for_exactly_one_p3_t11_post",
        "phase_a_result_sha256": external["result_sha256"],
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "committed_closure_verified": require_committed,
        "freeze_b_absent": True,
    }


def transport_qualification_gate(root: Path):
    """Return the canonical committed file-backed P3-T11 callback."""

    resolved_root = _root(root)

    def gate(context: QualificationGateContext) -> bool:
        verify_transport_qualification_window(
            resolved_root, context=context, require_committed=True
        )
        return True

    return gate


def run_canonical_transport_qualification(root: Path) -> Dict[str, Any]:
    """Run or safely recover P3-T11 using only canonical repository evidence."""

    resolved_root = _root(root)
    with _exclusive_workflow_lock(
        _path(resolved_root, CANONICAL_PATHS["qualification_execution_lock"]),
        label="P3-T11 qualification",
    ):
        config = _transport_config()
        fingerprint = _load_runtime_fingerprint(resolved_root)
        _verify_strict_qualification_evidence(resolved_root, config, fingerprint)
        intent_ledger = QualificationIntentLedger(
            _path(resolved_root, TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH)
        )
        attempt_ledger = QualificationAttemptLedger(
            _path(resolved_root, TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH)
        )
        artifact_path = _path(
            resolved_root, TRANSPORT_QUALIFICATION_ARTIFACT_PATH
        )
        common = {
            "phase_a_result_path": _require_file(
                resolved_root, CANONICAL_PATHS["a_vector_external"]
            ),
            "account_authorization_evidence_path": _require_file(
                resolved_root, CANONICAL_PATHS["account_authorization"]
            ),
            "model_documentation_evidence_path": _require_file(
                resolved_root, CANONICAL_PATHS["model_documentation"]
            ),
            "fingerprint": fingerprint,
            "intent_ledger": intent_ledger,
            "attempt_ledger": attempt_ledger,
            "output_root": _path(
                resolved_root, TRANSPORT_QUALIFICATION_OUTPUT_ROOT
            ),
        }
        if artifact_path.exists():
            raw = read_json(artifact_path)
            if not isinstance(raw, Mapping):
                raise Pilot3ExecutionError("existing P3-T11 report is not a JSON object")
            return verify_transport_qualification_report(
                raw, config=config, **common
            )
        if intent_ledger.row() is not None or attempt_ledger.row() is not None:
            return finalize_transport_qualification_artifact(
                artifact_path, config=config, **common
            )
        verify_transport_qualification_window(resolved_root, require_committed=True)
        with Pilot3OAuthTransport(config) as transport:
            return run_neutral_transport_qualification(
                freeze_b_generation_gate_path=_path(
                    resolved_root, CANONICAL_PATHS["generation_gate"]
                ),
                transport=transport,
                artifact_path=artifact_path,
                authorization_gate=transport_qualification_gate(resolved_root),
                **common,
            )


def _phase_b_prerequisites(root: Path) -> Dict[str, Dict[str, Any]]:
    """Verify and bind every prerequisite represented by P3-T01 through P3-T13."""

    try:
        verify_phase_b_freeze_bundle(_root(root))
    except Exception as exc:
        raise Pilot3ExecutionError(
            f"offline Phase-B freeze bundle does not verify: {type(exc).__name__}"
        ) from exc
    bindings: Dict[str, Dict[str, Any]] = {}
    specs = (
        (
            "p3_t01_artist_source_feasibility",
            Path("reports/pilot_3/evidence/artist_source_feasibility.json"),
            {"authoritative_metadata_audit_complete_freeze_a1_ready"},
        ),
        (
            "p3_t02_pilot2_baseline_recovery",
            Path("reports/pilot_3/evidence/pilot2_baseline_recovery.json"),
            {"pass"},
        ),
        (
            "p3_t03_planning_index",
            Path("reports/pilot_3/planning_index.json"),
            {"offline_planning_and_freeze_a1_complete_generation_gate_closed"},
        ),
        (
            "p3_t04_design_sensitivity",
            Path("reports/pilot_3/evidence/design_sensitivity.json"),
            {"development_sensitivity_complete"},
        ),
        (
            "p3_t05_corpus_selection",
            Path("reports/pilot_3/evidence/corpus_selection.json"),
            {"freeze_a1_complete"},
        ),
        (
            "p3_t06_holdout_seal",
            Path("reports/pilot_3/evidence/holdout_seal.json"),
            {"external_holdout_metadata_sealed_not_acquired"},
        ),
        (
            "p3_t07_a_vector_protocol",
            CANONICAL_PATHS["a_vector_protocol"],
            {"frozen"},
        ),
        (
            "p3_t08_a_vector_external_validation",
            CANONICAL_PATHS["a_vector_external"],
            {"pass"},
        ),
        (
            "p3_t09_lee_replication",
            Path("reports/pilot_3/evidence/lee_replication.json"),
            {"pass", "retire", "ineligible_retire"},
        ),
        (
            "p3_t10_human_validation",
            Path("reports/pilot_3/evidence/human_validation_disposition.json"),
            {"excluded"},
        ),
        (
            "p3_t11_transport_qualification",
            CANONICAL_PATHS["transport_qualification"],
            {"pass"},
        ),
        (
            "p3_t12_prompt_schedule_contract",
            Path("reports/pilot_3/evidence/prompt_schedule_contract.json"),
            {"frozen_offline_pending_phase_a_transport_and_generation_gate"},
        ),
        (
            "p3_t13_analysis_contract",
            Path("reports/pilot_3/evidence/analysis_contract.json"),
            {"frozen_offline_pending_phase_a_transport_and_generation_gate"},
        ),
    )
    values: Dict[str, Dict[str, Any]] = {}
    for name, relative, statuses in specs:
        value, binding = _json_binding(root, relative, label=name, statuses=statuses)
        values[name] = value
        bindings[name] = binding

    design, design_binding = _json_binding(
        root,
        Path("reports/pilot_3/evidence/phase_b_design.json"),
        label="P3-T04 resolving Phase-B design",
        statuses={"selected_estimation_design_pending_phase_a_and_transport"},
    )
    if (
        design.get("design_decision")
        != "SELECTED_BUDGET_CONSTRAINED_ESTIMATION_DESIGN_NO_POWER_CLAIM"
        or design.get("selection_proof", {}).get("request_budget") != 320
        or design.get("selection_proof", {}).get("selected_request_count") != 320
        or design.get("claim_boundary", {}).get("power_claim") is not False
    ):
        raise Pilot3ExecutionError("P3-T04 does not contain the frozen 320-request approval")
    bindings["p3_t04_phase_b_design_and_budget_approval"] = design_binding

    if values["p3_t10_human_validation"].get("disposition") != "excluded":
        raise Pilot3ExecutionError("human validation is not terminally excluded")
    _verify_phase_a_artifacts(
        root,
        values["p3_t07_a_vector_protocol"],
        values["p3_t08_a_vector_external_validation"],
    )
    bindings["pre_p3_t07_preprocessing_determinism_resolution"] = (
        _generated_normalization_contract(
            root,
            load_phase_a_config(root),
            values["p3_t07_a_vector_protocol"],
        )
    )
    t11 = values["p3_t11_transport_qualification"]
    if (
        t11.get("requested_model_label") != EXPECTED_REQUESTED_LABEL
        or t11.get("transport") != EXPECTED_TRANSPORT
        or t11.get("executed_model_claims") is not False
        or t11.get("snapshot_identity_claims") is not False
    ):
        raise Pilot3ExecutionError("P3-T11 violates the requested-label claim boundary")
    verified_t11, qualification_output_path = _verify_p3_t11(root)
    if verified_t11 != t11:
        raise Pilot3ExecutionError("P3-T11 recomputation differs from its canonical artifact")
    for name, relative in (
        ("p3_t11_account_authorization", CANONICAL_PATHS["account_authorization"]),
        ("p3_t11_model_documentation", CANONICAL_PATHS["model_documentation"]),
        ("p3_t11_intent_ledger", TRANSPORT_QUALIFICATION_INTENT_LEDGER_PATH),
        ("p3_t11_attempt_ledger", TRANSPORT_QUALIFICATION_ATTEMPT_LEDGER_PATH),
    ):
        path = _require_file(root, relative)
        bindings[name] = {
            "path": relative.as_posix(),
            "file_sha256": hash_file(path),
        }
    bindings["p3_t11_neutral_output"] = {
        "path": _portable(qualification_output_path, root),
        "file_sha256": hash_file(qualification_output_path),
    }

    _, corpus_manifest = _jsonl_binding(
        root,
        Path("data/manifests/pilot_3/corpus_selection.jsonl"),
        row_hash_field="row_sha256",
        label="P3-T05 corpus manifest",
    )
    _, split_manifest = _jsonl_binding(
        root,
        Path("data/manifests/pilot_3/real_splits.jsonl"),
        row_hash_field="row_sha256",
        label="P3-T06 split manifest",
    )
    prompts, prompt_manifest = _jsonl_binding(
        root,
        CANONICAL_PATHS["prompt_manifest"],
        row_hash_field="prompt_sha256",
        label="P3-T12 prompt manifest",
    )
    schedule_rows, schedule_manifest = _jsonl_binding(
        root,
        CANONICAL_PATHS["schedule_manifest"],
        row_hash_field="schedule_row_sha256",
        label="P3-T12 schedule manifest",
    )
    validate_schedule(schedule_rows)
    if len(prompts) != 80 or len(schedule_rows) != EXPECTED_SCHEDULE_COUNT:
        raise Pilot3ExecutionError("P3-T12 manifest cardinality is stale")
    bindings.update(
        {
            "p3_t05_corpus_manifest": corpus_manifest,
            "p3_t06_split_manifest": split_manifest,
            "p3_t12_prompt_manifest": prompt_manifest,
            "p3_t12_schedule_manifest": schedule_manifest,
        }
    )
    return bindings


def _generation_authorization_payload(
    root: Path,
    *,
    status: str,
    prerequisites: Optional[Mapping[str, Mapping[str, Any]]] = None,
    opening_transition: bool = False,
) -> Dict[str, Any]:
    """Derive the sole valid closed or open operational authorization record.

    The scientific protocol is deliberately immutable and remains in P3-T07's
    raw-byte closure.  The open record is not caller attestation: its transition
    proof is recomputed from the exact canonical P3-T07, P3-T08, and one-shot
    P3-T11 artifacts and ledgers.
    """

    resolved_root = _root(root)
    if status not in {GENERATION_AUTHORIZATION_CLOSED, GENERATION_AUTHORIZATION_OPEN}:
        raise Pilot3ExecutionError(f"unsupported generation authorization status: {status}")
    is_open = status == GENERATION_AUTHORIZATION_OPEN
    if opening_transition and (
        not is_open
        or _path(resolved_root, CANONICAL_PATHS["generation_gate"]).exists()
    ):
        raise Pilot3ExecutionError(
            "open generation authorization can transition only while P3-T14 is absent"
        )
    transition_proof: Optional[Dict[str, Any]] = None
    if is_open:
        verified = dict(prerequisites or _phase_b_prerequisites(resolved_root))
        protocol_path = _require_file(resolved_root, CANONICAL_PATHS["a_vector_protocol"])
        external_path = _require_file(resolved_root, CANONICAL_PATHS["a_vector_external"])
        qualification_path = _require_file(
            resolved_root, CANONICAL_PATHS["transport_qualification"]
        )
        protocol_raw = read_json(protocol_path)
        external_raw = read_json(external_path)
        qualification_raw = read_json(qualification_path)
        if not all(
            isinstance(value, Mapping)
            for value in (protocol_raw, external_raw, qualification_raw)
        ):
            raise Pilot3ExecutionError(
                "generation authorization lineage artifacts must be JSON objects"
            )
        protocol = dict(protocol_raw)
        external = dict(external_raw)
        qualification = dict(qualification_raw)
        scientific_protocol_path = _require_file(
            resolved_root, CANONICAL_PATHS["protocol"]
        )
        scientific_protocol_hash = hash_file(scientific_protocol_path)
        p3_t07_closure = protocol.get("closure_file_sha256")
        if (
            not isinstance(p3_t07_closure, Mapping)
            or p3_t07_closure.get(CANONICAL_PATHS["protocol"].as_posix())
            != scientific_protocol_hash
        ):
            raise Pilot3ExecutionError(
                "P3-T07 does not raw-hash the immutable scientific protocol"
            )
        if (
            qualification.get("analytic_generation_gate_status_at_authorization")
            != "closed"
            or qualification.get("freeze_b_status_at_authorization") != "not_frozen"
            or qualification.get("physical_post_count") != 1
            or qualification.get("retry_count") != 0
            or qualification.get("outside_artist_content_grid") is not True
            or qualification.get("authorizes_analytic_generation_by_itself") is not False
        ):
            raise Pilot3ExecutionError(
                "P3-T11 does not prove the one-shot pre-Freeze-B lineage"
            )
        transition_proof = {
            "immutable_scientific_protocol_file_sha256": scientific_protocol_hash,
            "p3_t07_protocol_closure_file_sha256": p3_t07_closure[
                CANONICAL_PATHS["protocol"].as_posix()
            ],
            "p3_t07_result_sha256": protocol.get("result_sha256"),
            "p3_t07_file_sha256": hash_file(protocol_path),
            "p3_t08_result_sha256": external.get("result_sha256"),
            "p3_t08_file_sha256": hash_file(external_path),
            "p3_t11_report_sha256": qualification.get("report_sha256"),
            "p3_t11_report_file_sha256": hash_file(qualification_path),
            "p3_t11_intent_sha256": qualification.get("intent_sha256"),
            "p3_t11_intent_ledger_file_sha256": qualification.get(
                "intent_ledger_file_sha256"
            ),
            "p3_t11_attempt_sha256": qualification.get("attempt_sha256"),
            "p3_t11_attempt_ledger_file_sha256": qualification.get(
                "attempt_ledger_file_sha256"
            ),
            "p3_t11_neutral_output_file_sha256": verified[
                "p3_t11_neutral_output"
            ]["file_sha256"],
            "p3_t11_reported_freeze_b_status": "not_frozen",
            "p3_t11_reported_generation_gate_status": "closed",
            "p3_t11_physical_post_count": 1,
            "p3_t11_retry_count": 0,
            "p3_t11_outside_analytic_grid": True,
            "p3_t14_file_absent_when_transition_written": True,
        }
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_authorization",
        "schema_version": GENERATION_AUTHORIZATION_SCHEMA,
        "status": status,
        "generation_authorization_open": is_open,
        "eligible_for_p3_t14": is_open,
        "p3_t01_through_p3_t13_verified": is_open,
        "immutable_scientific_protocol_path": CANONICAL_PATHS["protocol"].as_posix(),
        "generation_gate_path": CANONICAL_PATHS["generation_gate"].as_posix(),
        "requested_model_labels": [EXPECTED_REQUESTED_LABEL],
        "transport": EXPECTED_TRANSPORT,
        "direct_api_browser_or_fallback_allowed": False,
        "authorizes_analytic_generation_by_itself": False,
        "effective_only_with_matching_committed_clean_p3_t14": True,
        "transition_rule": (
            "change from closed to preregistered_generation_gate_open only after the "
            "canonical P3-T01 through P3-T13 artifacts, including the one-shot neutral "
            "P3-T11 lineage, recompute successfully and before P3-T14 is written; commit "
            "the open record and matching P3-T14 together before any analytic request"
        ),
        "transition_proof": transition_proof,
    }
    return _seal(payload, field="result_sha256")


def build_generation_authorization(root: Path) -> Dict[str, Any]:
    """Build only the exact closed operational authorization state."""

    return _generation_authorization_payload(
        root, status=GENERATION_AUTHORIZATION_CLOSED
    )


def _verify_generation_authorization(
    root: Path,
    *,
    require_open: bool,
    prerequisites: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    path = _require_file(root, CANONICAL_PATHS["generation_authorization"])
    raw = read_json(path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("generation authorization must be a JSON object")
    observed = dict(raw)
    _verify_seal(observed, field="result_sha256", label="generation authorization")
    status = observed.get("status")
    if require_open and status != GENERATION_AUTHORIZATION_OPEN:
        raise Pilot3ExecutionError("operational generation authorization is not open")
    if status not in {GENERATION_AUTHORIZATION_CLOSED, GENERATION_AUTHORIZATION_OPEN}:
        raise Pilot3ExecutionError("generation authorization has an unknown status")
    expected = _generation_authorization_payload(
        root,
        status=str(status),
        prerequisites=prerequisites,
    )
    if observed != expected:
        raise Pilot3ExecutionError(
            "generation authorization does not recompute from canonical evidence"
        )
    return observed


def verify_generation_authorization(
    root: Path, *, require_open: bool = False
) -> Dict[str, Any]:
    """Verify the canonical mutable status record; it never authorizes alone."""

    return _verify_generation_authorization(root, require_open=require_open)


def build_generation_gate(root: Path) -> Dict[str, Any]:
    """Build P3-T14 from verified files without authorizing by caller assertion.

    The returned artifact may be written before the Freeze-B commit.  Runtime
    verification separately requires the artifact and every bound closure path
    to be committed and clean, so the first analytic request cannot occur from
    an uncommitted prospective state.
    """

    resolved_root = _root(root)
    prerequisites = _phase_b_prerequisites(resolved_root)
    authorization = _verify_generation_authorization(
        resolved_root,
        require_open=True,
        prerequisites=prerequisites,
    )
    cells, generation_schedule = _load_t12_plan(resolved_root)
    fingerprint = _load_runtime_fingerprint(resolved_root)
    t11 = read_json(_require_file(resolved_root, CANONICAL_PATHS["transport_qualification"]))
    if not isinstance(t11, Mapping):
        raise Pilot3ExecutionError("P3-T11 is not a JSON object")
    expected_fingerprint = t11.get("oauth_runtime_fingerprint_sha256")
    if expected_fingerprint is None and isinstance(t11.get("runtime"), Mapping):
        expected_fingerprint = t11["runtime"].get("oauth_runtime_fingerprint_sha256")
    if expected_fingerprint != fingerprint.fingerprint_sha256:
        raise Pilot3ExecutionError("P3-T11 does not bind the canonical runtime fingerprint")

    protocol_raw = read_json(
        _require_file(resolved_root, CANONICAL_PATHS["a_vector_protocol"])
    )
    if not isinstance(protocol_raw, Mapping):
        raise Pilot3ExecutionError("P3-T07 is not a JSON object")
    p3_t07_closure_paths = _verified_p3_t07_closure_paths(
        resolved_root, protocol_raw
    )
    qualification_output = Path(prerequisites["p3_t11_neutral_output"]["path"])
    closure_paths = sorted(
        set(
            FREEZE_B_CODE_CLOSURE
            + FREEZE_B_EVIDENCE_CLOSURE
            + FREEZE_B_OPERATIONAL_CLOSURE
            + p3_t07_closure_paths
        )
        | {qualification_output}
    )
    closure_hashes = {
        relative.as_posix(): hash_file(_require_file(resolved_root, relative))
        for relative in closure_paths
    }
    transport = _transport_config()
    payload: Dict[str, Any] = {
        "record_type": "pilot3_generation_gate",
        "schema_version": GENERATION_GATE_SCHEMA,
        "resolves_task_id": "P3-T14",
        "status": "open",
        "generation_authorized": True,
        "analysis_authorized": False,
        "network_or_image_request_performed_by_builder": False,
        "requested_model_labels": [EXPECTED_REQUESTED_LABEL],
        "transport": EXPECTED_TRANSPORT,
        "direct_api_browser_or_fallback_allowed": False,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "request_budget": 320,
        "scheduled_request_count": len(cells),
        "transport_config_sha256": transport.config_sha256,
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "generation_grid_sha256": generation_grid_sha256(cells),
        "generation_schedule_sha256": generation_schedule.schedule_sha256,
        "operational_generation_authorization": {
            "path": CANONICAL_PATHS["generation_authorization"].as_posix(),
            "file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["generation_authorization"])
            ),
            "result_sha256": authorization["result_sha256"],
            "status": authorization["status"],
            "authorizes_analytic_generation_by_itself": False,
        },
        "immutable_scientific_protocol": {
            "path": CANONICAL_PATHS["protocol"].as_posix(),
            "file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["protocol"])
            ),
            "bound_raw_by_p3_t07": True,
        },
        "source_prompt_manifest_file_sha256": (
            generation_schedule.source_prompt_manifest_file_sha256
        ),
        "source_schedule_manifest_file_sha256": (
            generation_schedule.source_schedule_manifest_file_sha256
        ),
        "prerequisites": prerequisites,
        "closure_file_sha256": closure_hashes,
        "runtime_rule": (
            "the invocation and every physical POST require this exact committed-clean "
            "closure and a context matching the frozen transport, runtime fingerprint, "
            "grid, schedule, request identity, and gpt-image-2 label"
        ),
    }
    return _seal(payload, field="result_sha256")


def write_generation_gate(root: Path) -> Dict[str, Any]:
    """Transition the operational record and write P3-T14, without any request.

    The transition is prospective: P3-T01--P3-T13 are verified while the status
    record is still closed and P3-T14 is absent.  The open record and P3-T14
    must subsequently be committed together; until then runtime verification
    remains closed.
    """

    resolved_root = _root(root)
    gate_path = _path(resolved_root, CANONICAL_PATHS["generation_gate"])
    authorization = _verify_generation_authorization(
        resolved_root, require_open=False
    )
    if authorization["status"] == GENERATION_AUTHORIZATION_CLOSED:
        if gate_path.exists():
            raise Pilot3ExecutionError(
                "cannot open authorization while a P3-T14 artifact already exists"
            )
        prerequisites = _phase_b_prerequisites(resolved_root)
        opened = _generation_authorization_payload(
            resolved_root,
            status=GENERATION_AUTHORIZATION_OPEN,
            prerequisites=prerequisites,
            opening_transition=True,
        )
        write_json(
            _path(resolved_root, CANONICAL_PATHS["generation_authorization"]),
            opened,
        )
    else:
        _verify_generation_authorization(resolved_root, require_open=True)
    result = build_generation_gate(resolved_root)
    if gate_path.exists():
        existing = read_json(gate_path)
        if not isinstance(existing, Mapping) or dict(existing) != result:
            raise Pilot3ExecutionError("existing P3-T14 differs from the canonical gate")
        return result
    write_json(gate_path, result)
    return result


def verify_generation_gate(
    root: Path,
    *,
    context: Optional[ExecutionGateContext] = None,
    require_committed: bool = True,
) -> Dict[str, Any]:
    """Recompute P3-T14 and, optionally, authorize one generation context."""

    resolved_root = _root(root)
    gate_path = _require_file(resolved_root, CANONICAL_PATHS["generation_gate"])
    raw = read_json(gate_path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("P3-T14 must be a JSON object")
    observed = dict(raw)
    _verify_seal(observed, field="result_sha256", label="P3-T14")
    expected = build_generation_gate(resolved_root)
    if observed != expected:
        raise Pilot3ExecutionError("P3-T14 does not recompute from the current closure")
    if require_committed:
        closure_paths = tuple(
            Path(relative) for relative in observed["closure_file_sha256"]
        )
        _require_committed_closure(
            resolved_root, closure_paths + (CANONICAL_PATHS["generation_gate"],)
        )
    if context is not None:
        expected_context = {
            "transport_config_sha256": observed["transport_config_sha256"],
            "oauth_runtime_fingerprint_sha256": observed["oauth_runtime_fingerprint_sha256"],
            "generation_grid_sha256": observed["generation_grid_sha256"],
            "generation_schedule_sha256": observed["generation_schedule_sha256"],
            "frozen_requested_labels": [EXPECTED_REQUESTED_LABEL],
            "cell_count": EXPECTED_SCHEDULE_COUNT,
        }
        for key, value in expected_context.items():
            if getattr(context, key) != value:
                raise Pilot3ExecutionError(f"generation context does not match P3-T14: {key}")
    return observed


def generation_execution_gate(root: Path):
    """Return the only supported callback for ``run_generation_grid``."""

    resolved_root = _root(root)

    def gate(context: ExecutionGateContext) -> bool:
        verify_generation_gate(resolved_root, context=context, require_committed=True)
        return True

    return gate


def _verify_generation_gate_closure(
    root: Path,
    *,
    expected_result_sha256: str,
) -> Dict[str, Any]:
    """Fast per-POST check of the already fully verified immutable gate closure."""

    resolved_root = _root(root)
    gate_path = _require_file(resolved_root, CANONICAL_PATHS["generation_gate"])
    raw = read_json(gate_path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("P3-T14 must be a JSON object")
    gate = dict(raw)
    _verify_seal(gate, field="result_sha256", label="P3-T14")
    if (
        gate.get("result_sha256") != expected_result_sha256
        or gate.get("status") != "open"
        or gate.get("generation_authorized") is not True
        or gate.get("requested_model_labels") != [EXPECTED_REQUESTED_LABEL]
        or gate.get("transport") != EXPECTED_TRANSPORT
        or gate.get("direct_api_browser_or_fallback_allowed") is not False
    ):
        raise Pilot3ExecutionError("P3-T14 identity or authorization changed during generation")
    authorization = gate.get("operational_generation_authorization")
    if (
        not isinstance(authorization, Mapping)
        or authorization.get("path")
        != CANONICAL_PATHS["generation_authorization"].as_posix()
        or authorization.get("status") != GENERATION_AUTHORIZATION_OPEN
        or not _is_sha256(authorization.get("file_sha256"))
        or not _is_sha256(authorization.get("result_sha256"))
        or authorization.get("authorizes_analytic_generation_by_itself") is not False
    ):
        raise Pilot3ExecutionError("P3-T14 has no exact open operational authorization")
    closure = gate.get("closure_file_sha256")
    if not isinstance(closure, Mapping) or not closure:
        raise Pilot3ExecutionError("P3-T14 has no file closure")
    if (
        closure.get(CANONICAL_PATHS["generation_authorization"].as_posix())
        != authorization["file_sha256"]
    ):
        raise Pilot3ExecutionError(
            "P3-T14 operational authorization is absent from its file closure"
        )
    closure_paths: List[Path] = []
    for relative, expected_hash in closure.items():
        if not isinstance(relative, str) or not _is_sha256(expected_hash):
            raise Pilot3ExecutionError("P3-T14 contains an invalid closure binding")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise Pilot3ExecutionError("P3-T14 closure path escapes the repository")
        if hash_file(_require_file(resolved_root, path)) != expected_hash:
            raise Pilot3ExecutionError(f"P3-T14 closure changed during generation: {relative}")
        closure_paths.append(path)
    _require_committed_closure(
        resolved_root, tuple(closure_paths) + (CANONICAL_PATHS["generation_gate"],)
    )
    return gate


def generation_request_gate(root: Path):
    """Return the mandatory committed-closure callback for every physical POST."""

    resolved_root = _root(root)
    verified_gate = verify_generation_gate(resolved_root, require_committed=True)
    expected_result = str(verified_gate["result_sha256"])
    cells, _ = _load_t12_plan(resolved_root)
    cells_by_id = {cell.cell_id: cell for cell in cells}

    def gate(context: RequestGateContext) -> bool:
        current = _verify_generation_gate_closure(
            resolved_root, expected_result_sha256=expected_result
        )
        global_stop_path = _path(
            resolved_root, CANONICAL_PATHS["generation_global_stops"]
        )
        if global_stop_path.exists():
            GenerationGlobalStopLedger(global_stop_path).rows()
            raise Pilot3ExecutionError(
                "per-request gate is permanently closed by the global-stop ledger"
            )
        cell = cells_by_id.get(context.cell_id)
        if cell is None:
            raise Pilot3ExecutionError("per-request context is outside the frozen grid")
        expected = {
            "transport_config_sha256": current["transport_config_sha256"],
            "oauth_runtime_fingerprint_sha256": current[
                "oauth_runtime_fingerprint_sha256"
            ],
            "cell_identity_sha256": cell.cell_identity_sha256,
            "source_request_id": cell.source_request_id,
            "source_schedule_row_sha256": cell.source_schedule_row_sha256,
            "requested_model_label": cell.requested_model_label,
            "canonical_request_sha256": cell.canonical_request_sha256,
            "attempt_ledger_path": str(
                _path(resolved_root, CANONICAL_PATHS["generation_attempts"])
            ),
            "post_intent_ledger_path": str(
                _path(resolved_root, CANONICAL_PATHS["generation_post_intents"])
            ),
            "output_dir": str(
                _path(resolved_root, CANONICAL_PATHS["generated_output_root"])
            ),
        }
        for field, value in expected.items():
            if getattr(context, field) != value:
                raise Pilot3ExecutionError(
                    f"per-request context does not match P3-T14: {field}"
                )
        attempts = AppendOnlyAttemptLedger(
            _path(resolved_root, CANONICAL_PATHS["generation_attempts"])
        ).rows()
        intents = AppendOnlyPostIntentLedger(
            _path(resolved_root, CANONICAL_PATHS["generation_post_intents"])
        ).rows()
        prefix_expected = {
            "existing_attempt_count": len(attempts),
            "existing_attempt_ledger_semantic_sha256": (
                generation_attempt_ledger_semantic_sha256(attempts)
            ),
            "existing_post_intent_count": len(intents),
            "existing_post_intent_ledger_semantic_sha256": (
                post_intent_ledger_semantic_sha256(intents)
            ),
            "attempt_number": len(
                [attempt for attempt in attempts if attempt.cell_id == context.cell_id]
            )
            + 1,
        }
        for field, value in prefix_expected.items():
            if getattr(context, field) != value:
                raise Pilot3ExecutionError(
                    f"per-request ledger prefix does not match disk: {field}"
                )
        return True

    return gate


def _production_generation_runtime(
    root: Path,
) -> Tuple[
    List[GenerationCell],
    GenerationSchedule,
    Pilot3TransportConfig,
    Pilot3OAuthRuntimeFingerprint,
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    GenerationGlobalStopLedger,
]:
    resolved_root = _root(root)
    cells, schedule = _load_t12_plan(resolved_root)
    config = _transport_config()
    fingerprint = _load_runtime_fingerprint(resolved_root)
    verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)
    return (
        cells,
        schedule,
        config,
        fingerprint,
        AppendOnlyAttemptLedger(
            _path(resolved_root, CANONICAL_PATHS["generation_attempts"])
        ),
        AppendOnlyPostIntentLedger(
            _path(resolved_root, CANONICAL_PATHS["generation_post_intents"])
        ),
        AppendOnlyRuntimeRevalidationLedger(
            _path(
                resolved_root,
                CANONICAL_PATHS["generation_runtime_revalidations"],
            )
        ),
        GenerationGlobalStopLedger(
            _path(resolved_root, CANONICAL_PATHS["generation_global_stops"])
        ),
    )


def _load_or_persist_generation_context(
    root: Path,
    *,
    cells: Sequence[GenerationCell],
    schedule: GenerationSchedule,
    config: Pilot3TransportConfig,
    fingerprint: Pilot3OAuthRuntimeFingerprint,
    attempts: AppendOnlyAttemptLedger,
    intents: AppendOnlyPostIntentLedger,
) -> ExecutionGateContext:
    context_path = _path(root, CANONICAL_PATHS["generation_execution_context"])
    if context_path.exists():
        raw = read_json(context_path)
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError(
                "generation execution context must be a JSON object"
            )
        context = ExecutionGateContext.model_validate(raw)
    else:
        context = build_generation_execution_context(
            cells,
            schedule=schedule,
            config=config,
            fingerprint=fingerprint,
            ledger=attempts,
            post_intent_ledger=intents,
        )
        _persist_json_once(
            context_path,
            context.model_dump(mode="json"),
            label="generation execution context",
        )
    return verify_generation_execution_context(
        context,
        cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=attempts,
        post_intent_ledger=intents,
    )


def run_canonical_generation_grid(root: Path) -> Dict[str, Any]:
    """Run/resume the frozen grid and atomically persist its verified report."""

    resolved_root = _root(root)
    with _exclusive_workflow_lock(
        _path(resolved_root, CANONICAL_PATHS["generation_execution_lock"]),
        label="Pilot-3 generation",
    ):
        verify_generation_gate(resolved_root, require_committed=True)
        (
            cells,
            schedule,
            config,
            fingerprint,
            attempts,
            intents,
            runtime,
            global_stops,
        ) = _production_generation_runtime(resolved_root)
        context = _load_or_persist_generation_context(
            resolved_root,
            cells=cells,
            schedule=schedule,
            config=config,
            fingerprint=fingerprint,
            attempts=attempts,
            intents=intents,
        )
        report_path = _path(
            resolved_root, CANONICAL_PATHS["generation_execution"]
        )
        verify_kwargs = {
            "cells": cells,
            "schedule": schedule,
            "config": config,
            "fingerprint": fingerprint,
            "ledger": attempts,
            "post_intent_ledger": intents,
            "runtime_revalidation_ledger": runtime,
            "global_stop_ledger": global_stops,
            "output_root": resolved_root,
        }
        if report_path.exists():
            raw = read_json(report_path)
            if not isinstance(raw, Mapping):
                raise Pilot3ExecutionError(
                    "generation execution report must be a JSON object"
                )
            if raw.get("execution_gate_context") != context.model_dump(mode="json"):
                raise Pilot3ExecutionError(
                    "generation report does not bind the durable execution context"
                )
            return verify_generation_execution(raw, **verify_kwargs)

        if global_stops.path.exists():
            report = reconstruct_generation_execution_report(
                context, **verify_kwargs
            )
        else:
            with Pilot3OAuthTransport(config) as transport:
                report = run_generation_grid(
                    cells,
                    schedule=schedule,
                    transport=transport,
                    ledger=attempts,
                    post_intent_ledger=intents,
                    runtime_revalidation_ledger=runtime,
                    global_stop_ledger=global_stops,
                    fingerprint=fingerprint,
                    output_dir=_path(
                        resolved_root, CANONICAL_PATHS["generated_output_root"]
                    ),
                    execution_gate=generation_execution_gate(resolved_root),
                    request_gate=generation_request_gate(resolved_root),
                    execution_context=context,
                )
            verify_generation_execution(report, **verify_kwargs)
        _persist_json_once(
            report_path,
            report,
            label="generation execution report",
        )
        raw = read_json(report_path)
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError(
                "persisted generation execution report is not a JSON object"
            )
        return verify_generation_execution(raw, **verify_kwargs)


def _generation_runtime(
    root: Path,
) -> Tuple[
    List[GenerationCell],
    GenerationSchedule,
    Pilot3TransportConfig,
    Pilot3OAuthRuntimeFingerprint,
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    GenerationGlobalStopLedger,
]:
    resolved_root = _root(root)
    cells, schedule = _load_t12_plan(resolved_root)
    config = _transport_config()
    fingerprint = _load_runtime_fingerprint(resolved_root)
    attempts = AppendOnlyAttemptLedger(
        _require_file(resolved_root, CANONICAL_PATHS["generation_attempts"])
    )
    intents = AppendOnlyPostIntentLedger(
        _require_file(resolved_root, CANONICAL_PATHS["generation_post_intents"])
    )
    runtime = AppendOnlyRuntimeRevalidationLedger(
        _require_file(resolved_root, CANONICAL_PATHS["generation_runtime_revalidations"])
    )
    global_stops = GenerationGlobalStopLedger(
        _path(resolved_root, CANONICAL_PATHS["generation_global_stops"])
    )
    return cells, schedule, config, fingerprint, attempts, intents, runtime, global_stops


def write_generation_completion(root: Path) -> Dict[str, Any]:
    """Verify durable generation execution and emit canonical completion files."""

    resolved_root = _root(root)
    verify_generation_gate(resolved_root, require_committed=True)
    (
        cells,
        schedule,
        config,
        fingerprint,
        attempts,
        intents,
        runtime,
        global_stops,
    ) = _generation_runtime(resolved_root)
    execution_path = _require_file(resolved_root, CANONICAL_PATHS["generation_execution"])
    execution = read_json(execution_path)
    if not isinstance(execution, Mapping):
        raise Pilot3ExecutionError("generation execution evidence must be a JSON object")
    verified_execution = verify_generation_execution(
        execution,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=attempts,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
        output_root=resolved_root,
    )
    completion = generation_completion_report(
        cells,
        attempts.rows(),
        frozen_requested_labels=config.frozen_requested_labels,
        output_root=resolved_root,
        global_stop_dispositions=global_stops.rows(),
        global_stop_triggered=bool(verified_execution["global_stop_triggered"]),
    )
    if not completion["all_cells_terminal"] or len(cells) != EXPECTED_SCHEDULE_COUNT:
        raise Pilot3ExecutionError("generation is not terminal for all 320 scheduled requests")
    if verified_execution.get("generation_completion_sha256") != completion["report_sha256"]:
        raise Pilot3ExecutionError("execution report carries a stale generation completion")
    outputs = verify_successful_output_artifacts(cells, attempts.rows(), output_root=resolved_root)
    write_json(_path(resolved_root, CANONICAL_PATHS["generation_completion"]), completion)
    write_json(_path(resolved_root, CANONICAL_PATHS["successful_outputs"]), outputs)
    return completion


def verify_generation_completion_files(root: Path) -> Dict[str, Any]:
    """Verify canonical execution, completion, output, and ledger artifacts."""

    resolved_root = _root(root)
    gate = verify_generation_gate(resolved_root, require_committed=True)
    (
        cells,
        schedule,
        config,
        fingerprint,
        attempts,
        intents,
        runtime,
        global_stops,
    ) = _generation_runtime(resolved_root)
    execution = read_json(_require_file(resolved_root, CANONICAL_PATHS["generation_execution"]))
    completion = read_json(_require_file(resolved_root, CANONICAL_PATHS["generation_completion"]))
    outputs = read_json(_require_file(resolved_root, CANONICAL_PATHS["successful_outputs"]))
    if not all(isinstance(value, Mapping) for value in (execution, completion, outputs)):
        raise Pilot3ExecutionError("generation evidence contains a non-object artifact")
    verify_generation_execution(
        execution,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=attempts,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
        output_root=resolved_root,
    )
    expected_completion = verify_generation_completion_report(
        completion,
        cells,
        attempts.rows(),
        frozen_requested_labels=config.frozen_requested_labels,
        output_root=resolved_root,
        global_stop_dispositions=global_stops.rows(),
        global_stop_triggered=bool(execution["global_stop_triggered"]),
    )
    expected_outputs = verify_successful_output_artifacts(
        cells, attempts.rows(), output_root=resolved_root
    )
    expected_execution_paths = {
        "attempt_ledger_path": str(
            _path(resolved_root, CANONICAL_PATHS["generation_attempts"])
        ),
        "post_intent_ledger_path": str(
            _path(resolved_root, CANONICAL_PATHS["generation_post_intents"])
        ),
        "output_dir": str(_path(resolved_root, CANONICAL_PATHS["generated_output_root"])),
    }
    for intent in intents.rows():
        if any(
            getattr(intent, field) != value
            for field, value in expected_execution_paths.items()
        ):
            raise Pilot3ExecutionError("generation intent used a noncanonical execution path")
    if execution.get("global_stop_ledger_path") != str(global_stops.path.resolve()):
        raise Pilot3ExecutionError("generation execution used a noncanonical global-stop path")
    if dict(outputs) != expected_outputs:
        raise Pilot3ExecutionError("successful-output manifest is stale or tampered")
    if not expected_completion["all_cells_terminal"]:
        raise Pilot3ExecutionError("generation completion is not terminal")
    return {
        "gate": gate,
        "execution": dict(execution),
        "completion": expected_completion,
        "successful_outputs": expected_outputs,
        "cells": cells,
        "schedule": schedule,
        "config": config,
        "fingerprint": fingerprint,
        "attempts": attempts.rows(),
        "intents": intents.rows(),
        "runtime_revalidations": runtime.rows(),
        "global_stop_dispositions": global_stops.rows(),
    }


def _append_jsonl_fsync(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, (canonical_json(dict(row)) + "\n").encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if hash_file(path) != hash_bytes(payload):
            raise Pilot3ExecutionError(f"content-address collision at {path}")
        return
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_replace_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _portable(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(_root(root)).as_posix()
    except ValueError:
        return str(path.resolve())


def _resolve_recorded(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise Pilot3ExecutionError("recorded artifact path is missing")
    candidate = Path(value)
    return candidate.resolve() if candidate.is_absolute() else _path(root, candidate)


def _verify_protocol_config(
    root: Path,
    protocol: Mapping[str, Any],
    phase_a_config: Mapping[str, Any],
) -> Dict[str, Any]:
    config_path = _require_file(root, CANONICAL_PATHS["phase_a_config"])
    if (
        protocol.get("phase_a_config") != phase_a_config
        or protocol.get("phase_a_config_file_sha256") != hash_file(config_path)
    ):
        raise Pilot3ExecutionError("P3-T07 does not bind the current Phase-A config")
    runtime = protocol.get("runtime_environment")
    if not isinstance(runtime, Mapping) or not runtime:
        raise Pilot3ExecutionError("P3-T07 lacks its frozen extraction runtime")
    _pilot3_preprocessing_from_phase_a(phase_a_config)
    return _generated_normalization_contract(root, phase_a_config, protocol)


def _pilot3_preprocessing_from_phase_a(
    phase_a_config: Mapping[str, Any],
) -> Pilot2PreprocessingConfig:
    """Validate the frozen v1 pixel transform beneath Pilot 3's v2 container overlay."""

    runtime = Pilot2PreprocessingConfig()
    expected = runtime.model_dump(mode="json")
    expected["protocol_version"] = "pilot3-common-lossless-png-v1"
    if phase_a_config.get("common_preprocessing") != expected:
        raise Pilot3ExecutionError(
            "Phase-A common preprocessing does not equal the executed PNG transform"
        )
    return runtime


def _scope_generated_contract_payload(
    root: Path,
    phase_a_config: Mapping[str, Any],
    protocol_result_sha256: str,
    scope: Mapping[str, Any],
) -> Dict[str, Any]:
    normalization = scope.get("normalization_implementation")
    eligible = scope.get("eligible_membership")
    generated = eligible.get("generated_outputs") if isinstance(eligible, Mapping) else None
    legacy = scope.get("legacy_aic_amendment_boundary")
    if (
        scope.get("schema_version") != NORMALIZATION_SCOPE_SCHEMA
        or not _is_sha256(scope.get("authorization_sha256"))
        or not isinstance(normalization, Mapping)
        or not isinstance(generated, Mapping)
        or not isinstance(legacy, Mapping)
        or generated.get("count") != EXPECTED_SCHEDULE_COUNT
        or generated.get("required_requested_model_label") != EXPECTED_REQUESTED_LABEL
        or generated.get("required_transport") != EXPECTED_TRANSPORT
        or generated.get("required_endpoint") != "/v1/images/generations"
        or len(generated.get("members", [])) != EXPECTED_SCHEDULE_COUNT
        or legacy.get("generated_outputs_authorized_by_legacy_amendment") is not False
    ):
        raise Pilot3ExecutionError("normalization scope has stale generated membership")
    effective = normalization.get("effective_preprocessing_contract")
    if (
        normalization.get("protocol_version") != PILOT3_NORMALIZATION_PROTOCOL_VERSION
        or not isinstance(effective, Mapping)
        or effective.get("base_common_preprocessing")
        != phase_a_config.get("common_preprocessing")
        or normalization.get("effective_preprocessing_contract_sha256")
        != stable_hash(effective)
    ):
        raise Pilot3ExecutionError(
            "normalization scope disagrees with the generated transform"
        )
    scope_path = _require_file(root, NORMALIZATION_SCOPE_AUTHORIZATION_PATH)
    canonicalizer_path = _require_file(
        root, Path("src/latent_art_bench/pilot3/preprocessing.py")
    )
    scope_implementation_path = _require_file(
        root, Path("src/latent_art_bench/pilot3/normalization_scope.py")
    )
    scope_test_path = _require_file(
        root, Path("tests/pilot3/test_normalization_scope.py")
    )
    schedule = generated.get("schedule_manifest")
    if not isinstance(schedule, Mapping):
        raise Pilot3ExecutionError("normalization scope lacks its schedule binding")
    return {
        "record_type": "pilot3_generated_normalization_contract",
        "schema_version": GENERATED_NORMALIZATION_CONTRACT_SCHEMA,
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "base_common_preprocessing_config_sha256": stable_hash(
            phase_a_config["common_preprocessing"]
        ),
        "effective_preprocessing_contract_sha256": normalization[
            "effective_preprocessing_contract_sha256"
        ],
        "metadata_policy": (
            "apply_embedded_icc_to_pixels_then_emit_only_ihdr_idat_iend"
        ),
        "normalization_authority": {
            "path": NORMALIZATION_SCOPE_AUTHORIZATION_PATH.as_posix(),
            "file_sha256": hash_file(scope_path),
            "schema_version": NORMALIZATION_SCOPE_SCHEMA,
            "namespace": scope["namespace"],
            "authorization_sha256": scope["authorization_sha256"],
            "eligible_generated_count": generated["count"],
            "generated_members_semantic_sha256": stable_hash(generated["members"]),
            "schedule_manifest_path": schedule["path"],
            "schedule_manifest_file_sha256": schedule["file_sha256"],
            "schedule_manifest_semantic_sha256": schedule["semantic_sha256"],
            "required_requested_model_label": generated[
                "required_requested_model_label"
            ],
            "required_transport": generated["required_transport"],
            "required_endpoint": generated["required_endpoint"],
        },
        "legacy_aic_boundary": {
            "path": legacy["path"],
            "file_sha256": legacy["file_sha256"],
            "authorization_sha256": legacy["authorization_sha256"],
            "authorization_scope": legacy["authorization_scope"],
            "generated_outputs_authorized": False,
        },
        "implementation": {
            "canonicalizer_path": "src/latent_art_bench/pilot3/preprocessing.py",
            "canonicalizer_file_sha256": hash_file(canonicalizer_path),
            "scope_implementation_path": (
                "src/latent_art_bench/pilot3/normalization_scope.py"
            ),
            "scope_implementation_file_sha256": hash_file(
                scope_implementation_path
            ),
            "scope_test_path": "tests/pilot3/test_normalization_scope.py",
            "scope_test_file_sha256": hash_file(scope_test_path),
        },
        "a_vector_protocol_result_sha256": protocol_result_sha256,
    }


def _verify_generated_normalization_contract(
    root: Path,
    value: Mapping[str, Any],
    phase_a_config: Mapping[str, Any],
    *,
    expected_protocol_result_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    contract = dict(value)
    _verify_seal(
        contract,
        field="contract_sha256",
        label="generated normalization contract",
    )
    scope_raw = read_json(_require_file(root, NORMALIZATION_SCOPE_AUTHORIZATION_PATH))
    if not isinstance(scope_raw, Mapping):
        raise Pilot3ExecutionError("normalization-scope authorization is malformed")
    protocol_sha = str(contract.get("a_vector_protocol_result_sha256", ""))
    expected = _seal(
        _scope_generated_contract_payload(
            root,
            phase_a_config,
            protocol_sha,
            scope_raw,
        ),
        field="contract_sha256",
    )
    if contract != expected:
        raise Pilot3ExecutionError("generated normalization contract is stale")
    if (
        expected_protocol_result_sha256 is not None
        and protocol_sha != expected_protocol_result_sha256
    ):
        raise Pilot3ExecutionError(
            "generated normalization contract binds a different P3-T07"
        )
    return contract


def _generated_normalization_contract(
    root: Path,
    phase_a_config: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> Dict[str, Any]:
    """Bind generated derivatives to the committed exact-member authority."""

    try:
        scope = require_committed_normalization_scope_authorization(_root(root))
    except Exception as exc:
        raise Pilot3ExecutionError(
            f"normalization-scope authorization does not verify: {exc}"
        ) from exc
    closure = protocol.get("closure_file_sha256")
    required_paths = (
        NORMALIZATION_SCOPE_AUTHORIZATION_PATH,
        Path("src/latent_art_bench/pilot3/normalization_scope.py"),
        Path("tests/pilot3/test_normalization_scope.py"),
        Path("src/latent_art_bench/pilot3/preprocessing.py"),
    )
    if not isinstance(closure, Mapping) or any(
        closure.get(path.as_posix()) != hash_file(_require_file(root, path))
        for path in required_paths
    ):
        raise Pilot3ExecutionError(
            "P3-T07 does not bind the normalization-scope authority"
        )
    contract = _seal(
        _scope_generated_contract_payload(
            root,
            phase_a_config,
            str(protocol["result_sha256"]),
            scope,
        ),
        field="contract_sha256",
    )
    return _verify_generated_normalization_contract(
        root,
        contract,
        phase_a_config,
        expected_protocol_result_sha256=str(protocol["result_sha256"]),
    )


def _rows_by_request(
    path: Path,
    *,
    schema: str,
    label: str,
) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    rows = read_jsonl(path)
    result: Dict[str, Dict[str, Any]] = {}
    for index, raw in enumerate(rows, 1):
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError(f"{label}[{index}] is not an object")
        row = dict(raw)
        if row.get("schema_version") != schema:
            raise Pilot3ExecutionError(f"{label}[{index}] has the wrong schema")
        _verify_seal(row, field="record_sha256", label=f"{label}[{index}]")
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or request_id in result:
            raise Pilot3ExecutionError(f"{label} request ids are invalid or duplicated")
        result[request_id] = row
    return result


def _verify_preprocessing_row(
    root: Path,
    row: Mapping[str, Any],
    *,
    output: Mapping[str, Any],
    schedule_row: Mapping[str, Any],
    phase_a_config: Mapping[str, Any],
    normalization_contract: Mapping[str, Any],
) -> None:
    _verify_seal(row, field="record_sha256", label="generated preprocessing row")
    verified_contract = _verify_generated_normalization_contract(
        root,
        normalization_contract,
        phase_a_config,
    )
    if (
        row.get("request_id") != schedule_row.get("request_id")
        or row.get("schedule_row_sha256") != schedule_row.get("schedule_row_sha256")
        or row.get("source_png_sha256") != output.get("output_sha256")
        or row.get("requested_model_label") != EXPECTED_REQUESTED_LABEL
        or row.get("common_preprocessing_config_sha256")
        != stable_hash(phase_a_config["common_preprocessing"])
        or row.get("normalization_contract") != verified_contract
    ):
        raise Pilot3ExecutionError("generated preprocessing provenance is stale")
    source_path = _resolve_recorded(root, row.get("source_png_path"))
    output_path = _resolve_recorded(root, output.get("output_path"))
    normalized_path = _resolve_recorded(root, row.get("normalized_png_path"))
    if source_path != output_path:
        raise Pilot3ExecutionError("generated preprocessing binds a different source path")
    try:
        normalized_path.relative_to(
            _path(root, CANONICAL_PATHS["generated_normalized_root"])
        )
    except ValueError as exc:
        raise Pilot3ExecutionError(
            "generated normalized PNG is outside its canonical root"
        ) from exc
    for path, hash_field in (
        (source_path, "source_png_sha256"),
        (normalized_path, "normalized_png_sha256"),
    ):
        if not path.is_file() or hash_file(path) != row.get(hash_field):
            raise Pilot3ExecutionError(f"generated preprocessing file is stale: {path}")
    try:
        with Image.open(source_path) as image:
            image.load()
            width, height = image.size
            decoded_format = (image.format or "unknown").casefold()
            domain = phase_a_config["input_domain"]
            expected_checks = {
                "width_strictly_greater_than_410": width
                > int(domain["decoded_width_strict_min"]),
                "height_strictly_greater_than_410": height
                > int(domain["decoded_height_strict_min"]),
                "long_short_aspect_strictly_below_2": max(width, height)
                / min(width, height)
                < float(domain["long_to_short_aspect_strict_max"]),
                "released_code_area_predicate": width * height > 410 * 410,
            }
            normalized, normalized_size = pilot3_common_png_bytes(
                image, _pilot3_preprocessing_from_phase_a(phase_a_config)
            )
    except Exception as exc:
        raise Pilot3ExecutionError(
            f"cannot recompute generated preprocessing: {type(exc).__name__}"
        ) from exc
    if (
        decoded_format != "png"
        or not all(expected_checks.values())
        or row.get("domain_checks") != expected_checks
        or row.get("source_width") != width
        or row.get("source_height") != height
        or row.get("source_format") != decoded_format
        or row.get("source_png_byte_count") != source_path.stat().st_size
        or row.get("normalized_png_sha256") != hash_bytes(normalized)
        or row.get("normalized_png_byte_count") != len(normalized)
        or row.get("normalized_width") != normalized_size[0]
        or row.get("normalized_height") != normalized_size[1]
        or normalized_path.read_bytes() != normalized
        or row.get("visual_selection_or_exclusion_used") is not False
    ):
        raise Pilot3ExecutionError("generated preprocessing does not recompute exactly")
    expected_row = _preprocess_generated_output(
        root,
        output,
        schedule_row,
        phase_a_config,
        normalization_contract=verified_contract,
    )
    if dict(row) != expected_row:
        raise Pilot3ExecutionError("generated preprocessing row is not canonical")


def _verify_feature_row(
    row: Mapping[str, Any],
    *,
    preprocessing: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> None:
    _verify_seal(row, field="record_sha256", label="generated A-vector row")
    vector = row.get("vector")
    if not isinstance(vector, list) or len(vector) != 16_384:
        raise Pilot3ExecutionError("generated A-vector has the wrong dimension")
    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        for value in vector
    ):
        raise Pilot3ExecutionError("generated A-vector contains non-finite values")
    if learned_formal_vector_sha256(np.asarray(vector, dtype=np.float32)) != row.get(
        "vector_sha256"
    ):
        raise Pilot3ExecutionError("generated A-vector hash is stale")
    phase_a_config = protocol["phase_a_config"]
    section = phase_a_config["a_vector"]
    metadata = row.get("extraction_metadata")
    if not isinstance(metadata, Mapping):
        raise Pilot3ExecutionError("generated A-vector extraction metadata is missing")
    expected_metadata = {
        "pilot3_feature_version": section["feature_version"],
        "normalized_png_sha256": preprocessing["normalized_png_sha256"],
        "generated_source_png_sha256": preprocessing["source_png_sha256"],
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "phase_a_config_file_sha256": protocol["phase_a_config_file_sha256"],
        "source_repository": section["source_repository"],
        "source_revision": section["source_revision"],
        "model_repository": section["model_repository"],
        "model_revision": section["model_revision"],
        "config_sha256": section["model_config_sha256"],
        "weights_sha256": section["model_weights_sha256"],
        "policy": section["latent_policy"],
        "base_seed": section["base_seed"],
        "input_size": section["input_size"],
        "latent_shape": section["latent_shape"],
        "latent_scale": section["latent_scale"],
        "flatten_order": section["flatten_order"],
        "device": section["device"],
        "artifacts_verified": True,
        "source_checkout_verified": True,
    }
    if any(metadata.get(key) != value for key, value in expected_metadata.items()):
        raise Pilot3ExecutionError("generated A-vector extraction provenance is stale")
    runtime = protocol["runtime_environment"]
    if any(metadata.get(key) != value for key, value in runtime.items()):
        raise Pilot3ExecutionError("generated A-vector runtime differs from frozen P3-T07")
    if (
        row.get("normalized_png_sha256") != preprocessing.get("normalized_png_sha256")
        or row.get("a_vector_protocol_result_sha256") != protocol.get("result_sha256")
        or row.get("phase_a_config_file_sha256")
        != protocol.get("phase_a_config_file_sha256")
        or row.get("feature_version") != section["feature_version"]
        or row.get("feature_config_sha256") != stable_hash(section)
        or row.get("requested_model_label") != EXPECTED_REQUESTED_LABEL
    ):
        raise Pilot3ExecutionError("generated A-vector provenance is stale")


def _output_by_request(root: Path, generation: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw_outputs = generation["successful_outputs"].get("outputs")
    if not isinstance(raw_outputs, list):
        raise Pilot3ExecutionError("successful output manifest has no output rows")
    result: Dict[str, Dict[str, Any]] = {}
    for raw in raw_outputs:
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError("successful output row is not an object")
        row = dict(raw)
        request_id = row.get("source_request_id")
        if not isinstance(request_id, str) or request_id in result:
            raise Pilot3ExecutionError("successful output request ids are invalid or duplicate")
        if row.get("requested_model_label") != EXPECTED_REQUESTED_LABEL:
            raise Pilot3ExecutionError("successful output uses a non-frozen requested label")
        output_path = _resolve_recorded(root, row.get("output_path"))
        output_root = _path(root, CANONICAL_PATHS["generated_output_root"])
        try:
            output_path.relative_to(output_root)
        except ValueError as exc:
            raise Pilot3ExecutionError(
                "successful output is outside the canonical generated-output root"
            ) from exc
        if output_path.name != f"{row.get('output_sha256')}.png":
            raise Pilot3ExecutionError("successful output is not content addressed")
        result[request_id] = row
    return result


def _preprocess_generated_output(
    root: Path,
    output: Mapping[str, Any],
    schedule_row: Mapping[str, Any],
    phase_a_config: Mapping[str, Any],
    *,
    normalization_contract: Mapping[str, Any],
) -> Dict[str, Any]:
    verified_contract = _verify_generated_normalization_contract(
        root,
        normalization_contract,
        phase_a_config,
    )
    source_path = _resolve_recorded(root, output.get("output_path"))
    if not source_path.is_file() or hash_file(source_path) != output.get("output_sha256"):
        raise Pilot3ExecutionError("generated source PNG is missing or stale")
    try:
        with Image.open(source_path) as image:
            image.load()
            width, height = image.size
            decoded_format = (image.format or "unknown").casefold()
            domain = phase_a_config["input_domain"]
            checks = {
                "width_strictly_greater_than_410": width > int(domain["decoded_width_strict_min"]),
                "height_strictly_greater_than_410": height
                > int(domain["decoded_height_strict_min"]),
                "long_short_aspect_strictly_below_2": max(width, height) / min(width, height)
                < float(domain["long_to_short_aspect_strict_max"]),
                "released_code_area_predicate": width * height > 410 * 410,
            }
            if decoded_format != "png" or not all(checks.values()):
                raise Pilot3ExecutionError(
                    "successful output no longer satisfies PNG/Kim input eligibility"
                )
            normalized, normalized_size = pilot3_common_png_bytes(
                image, _pilot3_preprocessing_from_phase_a(phase_a_config)
            )
    except Pilot3ExecutionError:
        raise
    except Exception as exc:
        raise Pilot3ExecutionError(f"cannot preprocess generated PNG: {exc}") from exc
    normalized_sha = hash_bytes(normalized)
    normalized_path = (
        _path(root, CANONICAL_PATHS["generated_normalized_root"])
        / normalized_sha[:2]
        / f"{normalized_sha}.png"
    )
    _atomic_bytes(normalized_path, normalized)
    payload = {
        "record_type": "pilot3_generated_preprocessing",
        "schema_version": GENERATED_PREPROCESSING_SCHEMA,
        "request_id": schedule_row["request_id"],
        "schedule_sequence": schedule_row["sequence"],
        "schedule_row_sha256": schedule_row["schedule_row_sha256"],
        "requested_model_label": EXPECTED_REQUESTED_LABEL,
        "source_png_path": _portable(source_path, root),
        "source_png_sha256": output["output_sha256"],
        "source_png_byte_count": source_path.stat().st_size,
        "source_width": width,
        "source_height": height,
        "source_format": decoded_format,
        "domain_checks": checks,
        "normalized_png_path": _portable(normalized_path, root),
        "normalized_png_sha256": normalized_sha,
        "normalized_png_byte_count": len(normalized),
        "normalized_width": normalized_size[0],
        "normalized_height": normalized_size[1],
        "common_preprocessing_config_sha256": stable_hash(phase_a_config["common_preprocessing"]),
        "normalization_contract": verified_contract,
        "normalized_png_metadata_free": True,
        "visual_selection_or_exclusion_used": False,
    }
    return _seal(payload, field="record_sha256")


def _extract_generated_feature(
    root: Path,
    preprocessing: Mapping[str, Any],
    schedule_row: Mapping[str, Any],
    phase_a_config: Mapping[str, Any],
    protocol: Mapping[str, Any],
    loaded_vae: Any,
) -> Dict[str, Any]:
    normalized_path = _resolve_recorded(root, preprocessing["normalized_png_path"])
    section = phase_a_config["a_vector"]
    extraction = extract_learned_formal(
        normalized_path,
        loaded_vae,
        policy=SOURCE_REPLICATION_POLICY,
        base_seed=int(section["base_seed"]),
        device=str(section["device"]),
    )
    vector = np.asarray(extraction.vector, dtype=np.float32)
    if vector.shape != (int(section["raw_dimension"]),) or not np.isfinite(vector).all():
        raise Pilot3ExecutionError("generated A-vector is malformed")
    metadata = dict(extraction.metadata)
    metadata.update(
        {
            "pilot3_feature_version": section["feature_version"],
            "normalized_png_sha256": preprocessing["normalized_png_sha256"],
            "generated_source_png_sha256": preprocessing["source_png_sha256"],
            "a_vector_protocol_result_sha256": protocol["result_sha256"],
            "phase_a_config_file_sha256": protocol["phase_a_config_file_sha256"],
        }
    )
    payload = {
        "record_type": "pilot3_generated_a_vector",
        "schema_version": GENERATED_A_VECTOR_SCHEMA,
        "request_id": schedule_row["request_id"],
        "schedule_sequence": schedule_row["sequence"],
        "schedule_row_sha256": schedule_row["schedule_row_sha256"],
        "requested_model_label": EXPECTED_REQUESTED_LABEL,
        "normalized_png_sha256": preprocessing["normalized_png_sha256"],
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "phase_a_config_file_sha256": protocol["phase_a_config_file_sha256"],
        "feature_version": section["feature_version"],
        "feature_config_sha256": stable_hash(section),
        "vector_sha256": learned_formal_vector_sha256(vector),
        "extraction_metadata": metadata,
        "vector": vector.astype(float).tolist(),
    }
    return _seal(payload, field="record_sha256")


def _distance_rows(
    features: Sequence[Mapping[str, Any]],
    schedule_by_request: Mapping[str, Mapping[str, Any]],
    protocol: Mapping[str, Any],
    root: Path,
) -> List[Dict[str, Any]]:
    pca, centroids, labels = load_frozen_a_vector_state(_root(root), protocol)
    if labels != list(EXPECTED_ARTIST_IDS):
        raise Pilot3ExecutionError("P3-T07 centroid label order is stale")
    rows: List[Dict[str, Any]] = []
    for feature in sorted(
        features, key=lambda row: int(schedule_by_request[str(row["request_id"])]["sequence"])
    ):
        raw = np.asarray(feature["vector"], dtype=np.float64)
        projected = project_a_vectors([raw], pca)[0]
        if not np.isfinite(projected).all():
            raise Pilot3ExecutionError("generated projected A-vector is non-finite")
        distances = np.sqrt(np.square(centroids - projected[None, :]).sum(axis=1))
        if not np.isfinite(distances).all() or np.any(distances < 0):
            raise Pilot3ExecutionError("generated centroid distances are invalid")
        schedule_row = schedule_by_request[str(feature["request_id"])]
        payload = {
            "record_type": "pilot3_generated_a_vector_distance",
            "schema_version": GENERATED_DISTANCE_SCHEMA,
            "request_id": feature["request_id"],
            "schedule_sequence": schedule_row["sequence"],
            "schedule_row_sha256": schedule_row["schedule_row_sha256"],
            "requested_model_label": EXPECTED_REQUESTED_LABEL,
            "a_vector_protocol_result_sha256": protocol["result_sha256"],
            "raw_vector_sha256": feature["vector_sha256"],
            "projected_vector_sha256": stable_hash(projected.astype(float).tolist()),
            "pca_component_count": int(projected.size),
            "distances_by_artist": {
                artist_id: float(distances[index]) for index, artist_id in enumerate(labels)
            },
        }
        rows.append(_seal(payload, field="record_sha256"))
    return rows


def measure_generated_outputs(root: Path) -> Dict[str, Any]:
    """Preprocess and measure every successful generated PNG, with resume safety."""

    resolved_root = _root(root)
    generation = verify_generation_completion_files(resolved_root)
    gate = generation["gate"]
    phase_a_config = load_phase_a_config(resolved_root)
    protocol_raw = read_json(_require_file(resolved_root, CANONICAL_PATHS["a_vector_protocol"]))
    if not isinstance(protocol_raw, Mapping):
        raise Pilot3ExecutionError("P3-T07 is not a JSON object")
    protocol = dict(protocol_raw)
    verify_self_hash(protocol)
    if protocol.get("status") != "frozen":
        raise Pilot3ExecutionError("P3-T07 is not frozen")
    normalization_contract = _verify_protocol_config(
        resolved_root, protocol, phase_a_config
    )

    schedule_rows = validate_schedule(
        read_jsonl(_require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"]))
    )
    schedule_by_request = {str(row["request_id"]): row for row in schedule_rows}
    outputs = _output_by_request(resolved_root, generation)
    expected_successes = {
        request_id
        for request_id, disposition in generation["completion"][
            "source_request_dispositions"
        ].items()
        if disposition == "succeeded"
    }
    if set(outputs) != expected_successes:
        raise Pilot3ExecutionError("successful output manifest does not match completion")

    preprocessing_path = _path(resolved_root, CANONICAL_PATHS["generated_preprocessing"])
    feature_path = _path(resolved_root, CANONICAL_PATHS["generated_a_vectors"])
    preprocessing_rows = _rows_by_request(
        preprocessing_path,
        schema=GENERATED_PREPROCESSING_SCHEMA,
        label="generated preprocessing",
    )
    feature_rows = _rows_by_request(
        feature_path,
        schema=GENERATED_A_VECTOR_SCHEMA,
        label="generated A-vectors",
    )
    if not set(preprocessing_rows).issubset(expected_successes) or not set(feature_rows).issubset(
        expected_successes
    ):
        raise Pilot3ExecutionError("measurement manifests contain unavailable requests")

    if not preprocessing_path.exists():
        write_jsonl(preprocessing_path, [])
    if not feature_path.exists():
        write_jsonl(feature_path, [])

    loaded_vae = None
    ordered_request_ids = sorted(
        expected_successes,
        key=lambda value: schedule_by_request[value]["sequence"],
    )
    for request_id in ordered_request_ids:
        output = outputs[request_id]
        schedule_row = schedule_by_request[request_id]
        existing_preprocessing = preprocessing_rows.get(request_id)
        if existing_preprocessing is None:
            existing_preprocessing = _preprocess_generated_output(
                resolved_root,
                output,
                schedule_row,
                phase_a_config,
                normalization_contract=normalization_contract,
            )
            _append_jsonl_fsync(preprocessing_path, existing_preprocessing)
            preprocessing_rows[request_id] = existing_preprocessing
        _verify_preprocessing_row(
            resolved_root,
            existing_preprocessing,
            output=output,
            schedule_row=schedule_row,
            phase_a_config=phase_a_config,
            normalization_contract=normalization_contract,
        )

        existing_feature = feature_rows.get(request_id)
        if existing_feature is None:
            if loaded_vae is None:
                loaded_vae = _load_vae(resolved_root, phase_a_config)
            existing_feature = _extract_generated_feature(
                resolved_root,
                existing_preprocessing,
                schedule_row,
                phase_a_config,
                protocol,
                loaded_vae,
            )
            _append_jsonl_fsync(feature_path, existing_feature)
            feature_rows[request_id] = existing_feature
        _verify_feature_row(
            existing_feature,
            preprocessing=existing_preprocessing,
            protocol=protocol,
        )

    if set(preprocessing_rows) != expected_successes or set(feature_rows) != expected_successes:
        raise Pilot3ExecutionError("generated measurement coverage is incomplete")
    ordered_features = [feature_rows[request_id] for request_id in ordered_request_ids]
    distances = _distance_rows(ordered_features, schedule_by_request, protocol, resolved_root)
    distance_path = _path(resolved_root, CANONICAL_PATHS["generated_distances"])
    write_jsonl(distance_path, distances)

    preprocessing_values = [preprocessing_rows[request_id] for request_id in ordered_request_ids]
    state_files = {
        name: {
            "path": evidence["path"],
            "file_sha256": evidence["file_sha256"],
            "array_shape": evidence["array_shape"],
        }
        for name, evidence in sorted(protocol["state_files"].items())
    }
    payload = {
        "record_type": "pilot3_generated_a_vector_measurement",
        "schema_version": GENERATED_MEASUREMENT_SCHEMA,
        "status": "complete",
        "generation_gate_result_sha256": gate["result_sha256"],
        "generation_completion_report_sha256": generation["completion"]["report_sha256"],
        "generation_grid_sha256": generation["completion"]["generation_grid_sha256"],
        "schedule_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"])
        ),
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "normalization_contract": normalization_contract,
        "a_vector_state_files": state_files,
        "successful_generated_png_count": len(expected_successes),
        "preprocessed_png_count": len(preprocessing_values),
        "a_vector_count": len(ordered_features),
        "distance_count": len(distances),
        "preprocessing_manifest": {
            "path": CANONICAL_PATHS["generated_preprocessing"].as_posix(),
            "file_sha256": hash_file(preprocessing_path),
            "semantic_sha256": stable_hash(preprocessing_values),
        },
        "a_vector_manifest": {
            "path": CANONICAL_PATHS["generated_a_vectors"].as_posix(),
            "file_sha256": hash_file(feature_path),
            "semantic_sha256": stable_hash(ordered_features),
        },
        "distance_manifest": {
            "path": CANONICAL_PATHS["generated_distances"].as_posix(),
            "file_sha256": hash_file(distance_path),
            "semantic_sha256": stable_hash(distances),
        },
        "generated_png_sha256_by_request": {
            request_id: outputs[request_id]["output_sha256"]
            for request_id in sorted(expected_successes)
        },
        "generated_a_vector_sha256_by_request": {
            request_id: feature_rows[request_id]["vector_sha256"]
            for request_id in sorted(expected_successes)
        },
        "feature_for_unavailable_request_count": 0,
        "visual_selection_or_outcome_dependent_exclusion_used": False,
    }
    result = _seal(payload, field="result_sha256")
    write_json(_path(resolved_root, CANONICAL_PATHS["generated_measurement"]), result)
    return verify_generated_measurement(resolved_root)["measurement"]


def verify_generated_measurement(root: Path) -> Dict[str, Any]:
    """Re-hash every generated PNG, normalized PNG, A-vector, and distance row."""

    resolved_root = _root(root)
    generation = verify_generation_completion_files(resolved_root)
    gate = generation["gate"]
    protocol_raw = read_json(_require_file(resolved_root, CANONICAL_PATHS["a_vector_protocol"]))
    measurement_raw = read_json(
        _require_file(resolved_root, CANONICAL_PATHS["generated_measurement"])
    )
    if not isinstance(protocol_raw, Mapping) or not isinstance(measurement_raw, Mapping):
        raise Pilot3ExecutionError("generated measurement inputs must be JSON objects")
    protocol = dict(protocol_raw)
    measurement = dict(measurement_raw)
    verify_self_hash(protocol)
    if protocol.get("status") != "frozen":
        raise Pilot3ExecutionError("P3-T07 is not frozen")
    _verify_seal(measurement, field="result_sha256", label="generated measurement")
    if measurement.get("status") != "complete":
        raise Pilot3ExecutionError("generated measurement is not complete")

    phase_a_config = load_phase_a_config(resolved_root)
    normalization_contract = _verify_protocol_config(
        resolved_root, protocol, phase_a_config
    )
    schedule_rows = validate_schedule(
        read_jsonl(_require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"]))
    )
    schedule_by_request = {str(row["request_id"]): row for row in schedule_rows}
    outputs = _output_by_request(resolved_root, generation)
    expected_successes = set(outputs)
    ordered_request_ids = sorted(
        expected_successes,
        key=lambda value: int(schedule_by_request[value]["sequence"]),
    )
    preprocessing = _rows_by_request(
        _require_file(resolved_root, CANONICAL_PATHS["generated_preprocessing"]),
        schema=GENERATED_PREPROCESSING_SCHEMA,
        label="generated preprocessing",
    )
    features = _rows_by_request(
        _require_file(resolved_root, CANONICAL_PATHS["generated_a_vectors"]),
        schema=GENERATED_A_VECTOR_SCHEMA,
        label="generated A-vectors",
    )
    if set(preprocessing) != expected_successes or set(features) != expected_successes:
        raise Pilot3ExecutionError("generated measurement request coverage is stale")
    if list(preprocessing) != ordered_request_ids or list(features) != ordered_request_ids:
        raise Pilot3ExecutionError("generated measurement manifests are not in schedule order")
    if hash_file(
        _require_file(resolved_root, CANONICAL_PATHS["generated_preprocessing"])
    ) != _jsonl_file_sha256(list(preprocessing.values())) or hash_file(
        _require_file(resolved_root, CANONICAL_PATHS["generated_a_vectors"])
    ) != _jsonl_file_sha256(list(features.values())):
        raise Pilot3ExecutionError("generated measurement manifests are not canonical JSONL")
    loaded_vae = _load_vae(resolved_root, phase_a_config) if expected_successes else None
    for request_id in sorted(
        expected_successes, key=lambda value: int(schedule_by_request[value]["sequence"])
    ):
        _verify_preprocessing_row(
            resolved_root,
            preprocessing[request_id],
            output=outputs[request_id],
            schedule_row=schedule_by_request[request_id],
            phase_a_config=phase_a_config,
            normalization_contract=normalization_contract,
        )
        _verify_feature_row(
            features[request_id],
            preprocessing=preprocessing[request_id],
            protocol=protocol,
        )
        assert loaded_vae is not None
        recomputed = _extract_generated_feature(
            resolved_root,
            preprocessing[request_id],
            schedule_by_request[request_id],
            phase_a_config,
            protocol,
            loaded_vae,
        )
        if features[request_id] != recomputed:
            raise Pilot3ExecutionError(
                f"generated A-vector does not recompute exactly: {request_id}"
            )

    distance_path = _require_file(resolved_root, CANONICAL_PATHS["generated_distances"])
    distance_rows_raw = read_jsonl(distance_path)
    distances: List[Dict[str, Any]] = []
    for index, raw in enumerate(distance_rows_raw, 1):
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError(f"generated distance[{index}] is not an object")
        row = dict(raw)
        if row.get("schema_version") != GENERATED_DISTANCE_SCHEMA:
            raise Pilot3ExecutionError("generated distance has the wrong schema")
        _verify_seal(row, field="record_sha256", label=f"generated distance[{index}]")
        distances.append(row)
    if [row.get("request_id") for row in distances] != ordered_request_ids:
        raise Pilot3ExecutionError("generated distance manifest is not in schedule order")
    if hash_file(distance_path) != _jsonl_file_sha256(distances):
        raise Pilot3ExecutionError("generated distance manifest is not canonical JSONL")
    expected_distances = _distance_rows(
        [features[request_id] for request_id in ordered_request_ids],
        schedule_by_request,
        protocol,
        resolved_root,
    )
    expected_by_request = {row["request_id"]: row for row in expected_distances}
    observed_by_request = {row["request_id"]: row for row in distances}
    if observed_by_request != expected_by_request:
        raise Pilot3ExecutionError("generated distances do not recompute exactly")

    state_files = {
        name: {
            "path": evidence["path"],
            "file_sha256": evidence["file_sha256"],
            "array_shape": evidence["array_shape"],
        }
        for name, evidence in sorted(protocol["state_files"].items())
    }
    for name, evidence in protocol["state_files"].items():
        state_path = _resolve_recorded(resolved_root, evidence["path"])
        if not state_path.is_file() or hash_file(state_path) != evidence["file_sha256"]:
            raise Pilot3ExecutionError(f"generated measurement has stale state file: {name}")
    preprocessing_values = [
        preprocessing[request_id] for request_id in ordered_request_ids
    ]
    feature_values = [features[request_id] for request_id in ordered_request_ids]
    expected_payload = {
        "record_type": "pilot3_generated_a_vector_measurement",
        "schema_version": GENERATED_MEASUREMENT_SCHEMA,
        "status": "complete",
        "generation_gate_result_sha256": gate["result_sha256"],
        "generation_completion_report_sha256": generation["completion"]["report_sha256"],
        "generation_grid_sha256": generation["completion"]["generation_grid_sha256"],
        "schedule_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"])
        ),
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "normalization_contract": normalization_contract,
        "a_vector_state_files": state_files,
        "successful_generated_png_count": len(expected_successes),
        "preprocessed_png_count": len(preprocessing),
        "a_vector_count": len(features),
        "distance_count": len(distances),
        "preprocessing_manifest": {
            "path": CANONICAL_PATHS["generated_preprocessing"].as_posix(),
            "file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["generated_preprocessing"])
            ),
            "semantic_sha256": stable_hash(preprocessing_values),
        },
        "a_vector_manifest": {
            "path": CANONICAL_PATHS["generated_a_vectors"].as_posix(),
            "file_sha256": hash_file(
                _require_file(resolved_root, CANONICAL_PATHS["generated_a_vectors"])
            ),
            "semantic_sha256": stable_hash(feature_values),
        },
        "distance_manifest": {
            "path": CANONICAL_PATHS["generated_distances"].as_posix(),
            "file_sha256": hash_file(distance_path),
            "semantic_sha256": stable_hash(distances),
        },
        "generated_png_sha256_by_request": {
            request_id: outputs[request_id]["output_sha256"]
            for request_id in sorted(expected_successes)
        },
        "generated_a_vector_sha256_by_request": {
            request_id: features[request_id]["vector_sha256"]
            for request_id in sorted(expected_successes)
        },
        "feature_for_unavailable_request_count": 0,
        "visual_selection_or_outcome_dependent_exclusion_used": False,
    }
    expected_measurement = _seal(expected_payload, field="result_sha256")
    if measurement != expected_measurement:
        raise Pilot3ExecutionError("generated measurement does not recompute exactly")
    return {
        "measurement": measurement,
        "preprocessing": preprocessing,
        "features": features,
        "distances": distances,
        "generation": generation,
        "protocol": protocol,
        "schedule_rows": schedule_rows,
    }


def _final_attempts_by_request(
    cells: Sequence[GenerationCell], attempts: Sequence[GenerationAttempt]
) -> Dict[str, GenerationAttempt]:
    cell_to_request = {cell.cell_id: str(cell.source_request_id) for cell in cells}
    by_cell: Dict[str, List[GenerationAttempt]] = {cell.cell_id: [] for cell in cells}
    for attempt in attempts:
        by_cell[attempt.cell_id].append(attempt)
    result: Dict[str, GenerationAttempt] = {}
    for cell_id, rows in by_cell.items():
        if not rows:
            continue
        rows.sort(key=lambda row: row.attempt_number)
        result[cell_to_request[cell_id]] = rows[-1]
    return result


def _generation_terminal_category(disposition: str, final_attempt: GenerationAttempt) -> str:
    if disposition == "succeeded":
        return "usable_image"
    if disposition == "refused":
        return "policy_refusal"
    if disposition == "failed_after_retry_cap":
        return "retry_cap_technical_failure"
    if disposition != "terminal_failure":
        raise Pilot3ExecutionError(f"non-terminal generation disposition: {disposition}")
    if final_attempt.failure_kind == "indeterminate_after_interruption":
        return "indeterminate_after_interruption"
    if final_attempt.retry_classification == "not_retryable_http_status":
        return "nonretryable_client_response"
    if final_attempt.request_label_accepted and final_attempt.retry_classification in {
        "not_retryable_invalid_response",
        "not_retryable_invalid_image",
        "not_retryable_output_error",
    }:
        return "malformed_or_ineligible_success"
    raise Pilot3ExecutionError(
        "terminal transport outcome has no frozen scientific category; stop and version "
        f"a prospective protocol rather than relabel it: {final_attempt.failure_kind}"
    )


def _jsonl_file_sha256(rows: Sequence[Mapping[str, Any]]) -> str:
    encoded = "".join(canonical_json(dict(row)) + "\n" for row in rows).encode("utf-8")
    return hash_bytes(encoded)


def _terminal_envelope_payload(
    root: Path,
    *,
    verified_measurement: Optional[Mapping[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Compute terminal rows and their envelope without writing either artifact."""

    resolved_root = _root(root)
    verified = (
        dict(verified_measurement)
        if verified_measurement is not None
        else verify_generated_measurement(resolved_root)
    )
    generation = verified["generation"]
    measurement = verified["measurement"]
    schedule_rows = verified["schedule_rows"]
    successful_ids = set(verified["features"])
    cells = generation["cells"]
    final_attempts = _final_attempts_by_request(cells, generation["attempts"])
    global_stops = {
        row.source_request_id: row
        for row in generation["global_stop_dispositions"]
    }
    dispositions = generation["completion"]["source_request_dispositions"]
    rows: List[Dict[str, Any]] = []
    for schedule_row in schedule_rows:
        request_id = str(schedule_row["request_id"])
        disposition = str(dispositions[request_id])
        final_attempt = final_attempts.get(request_id)
        global_stop = global_stops.get(request_id)
        if disposition == "not_sent_global_stop":
            if final_attempt is not None or global_stop is None:
                raise Pilot3ExecutionError(
                    f"global-stop request has an attempt or no stop proof: {request_id}"
                )
            category = "not_sent_global_stop"
        else:
            if final_attempt is None or global_stop is not None:
                raise Pilot3ExecutionError(
                    f"attempted request has stale global-stop accounting: {request_id}"
                )
            category = _generation_terminal_category(disposition, final_attempt)
        if category == "usable_image" and request_id not in successful_ids:
            raise Pilot3ExecutionError(
                f"generation success lacks verified A-vector measurement: {request_id}"
            )
        if category != "usable_image" and request_id in successful_ids:
            raise Pilot3ExecutionError(
                f"unavailable request has an A-vector measurement: {request_id}"
            )
        payload = {
            "record_type": "pilot3_terminal_disposition",
            "schema_version": TERMINAL_ROW_SCHEMA,
            "request_id": request_id,
            "schedule_sequence": schedule_row["sequence"],
            "schedule_row_sha256": schedule_row["schedule_row_sha256"],
            "requested_model_label": EXPECTED_REQUESTED_LABEL,
            "generation_cell_id": (
                global_stop.cell_id if global_stop is not None else final_attempt.cell_id
            ),
            "final_attempt_id": (
                None if final_attempt is None else final_attempt.attempt_id
            ),
            "final_attempt_number": (
                None if final_attempt is None else final_attempt.attempt_number
            ),
            "generation_disposition": disposition,
            "generation_retry_classification": (
                None if final_attempt is None else final_attempt.retry_classification
            ),
            "generation_failure_kind": (
                "runtime_image_preflight_failed_before_send"
                if global_stop is not None
                else final_attempt.failure_kind
            ),
            "global_stop_record_sha256": (
                None if global_stop is None else global_stop.record_sha256
            ),
            "terminal_category": category,
            "measurement_present": request_id in successful_ids,
            "output_sha256": None if final_attempt is None else final_attempt.output_sha256,
            "visual_selection_or_replacement_used": False,
        }
        rows.append(_seal(payload, field="record_sha256"))
    validate_terminal_accounting(schedule_rows, rows)
    attempts = generation["attempts"]
    intents = generation["intents"]
    runtime = generation["runtime_revalidations"]
    global_stop_values = generation["global_stop_dispositions"]
    global_stop_path = _path(
        resolved_root, CANONICAL_PATHS["generation_global_stops"]
    )
    envelope = {
        "record_type": "pilot3_terminal_disposition_manifest",
        "schema_version": TERMINAL_ENVELOPE_SCHEMA,
        "status": "complete",
        "schedule_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"])
        ),
        "schedule_semantic_sha256": stable_hash(schedule_rows),
        "generation_gate_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_gate"])
        ),
        "generation_gate_result_sha256": read_json(
            _require_file(resolved_root, CANONICAL_PATHS["generation_gate"])
        )["result_sha256"],
        "generation_completion_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_completion"])
        ),
        "generation_completion_report_sha256": generation["completion"]["report_sha256"],
        "generated_measurement_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generated_measurement"])
        ),
        "generated_measurement_result_sha256": measurement["result_sha256"],
        "generation_grid_sha256": generation["completion"]["generation_grid_sha256"],
        "generation_schedule_sha256": generation["schedule"].schedule_sha256,
        "attempt_ledger_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_attempts"])
        ),
        "attempt_ledger_semantic_sha256": generation_attempt_ledger_semantic_sha256(attempts),
        "post_intent_ledger_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_post_intents"])
        ),
        "post_intent_ledger_semantic_sha256": post_intent_ledger_semantic_sha256(intents),
        "runtime_revalidation_ledger_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_runtime_revalidations"])
        ),
        "runtime_revalidation_ledger_semantic_sha256": (
            runtime_revalidation_ledger_semantic_sha256(runtime)
        ),
        "global_stop_ledger_path": CANONICAL_PATHS[
            "generation_global_stops"
        ].as_posix(),
        "global_stop_ledger_file_sha256": (
            hash_file(global_stop_path) if global_stop_path.is_file() else None
        ),
        "global_stop_ledger_semantic_sha256": (
            global_stop_ledger_semantic_sha256(global_stop_values)
        ),
        "global_stop_disposition_count": len(global_stop_values),
        "fake_attempt_row_count": 0,
        "terminal_rows_path": CANONICAL_PATHS["terminal_rows"].as_posix(),
        "terminal_rows_file_sha256": _jsonl_file_sha256(rows),
        "terminal_rows_semantic_sha256": stable_hash(rows),
        "terminal_request_count": len(rows),
        "terminal_category_counts": dict(
            sorted(Counter(row["terminal_category"] for row in rows).items())
        ),
        "source_schedule_row_sha256_by_request": {
            str(row["request_id"]): row["schedule_row_sha256"] for row in schedule_rows
        },
        "generation_success_requires_verified_measurement_for_usable_image": True,
        "caller_self_attestation_used": False,
    }
    result = _seal(envelope, field="result_sha256")
    return rows, result


def write_terminal_envelope(root: Path) -> Dict[str, Any]:
    """Assign one analysis category per request after measurement verification."""

    resolved_root = _root(root)
    rows, result = _terminal_envelope_payload(resolved_root)
    terminal_path = _path(resolved_root, CANONICAL_PATHS["terminal_rows"])
    write_jsonl(terminal_path, rows)
    if hash_file(terminal_path) != result["terminal_rows_file_sha256"]:
        raise Pilot3ExecutionError("terminal row serialization hash is inconsistent")
    write_json(_path(resolved_root, CANONICAL_PATHS["terminal_envelope"]), result)
    return result


def _verify_terminal_envelope_artifacts(
    root: Path,
    *,
    verified_measurement: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    resolved_root = _root(root)
    envelope_path = _require_file(resolved_root, CANONICAL_PATHS["terminal_envelope"])
    rows_path = _require_file(resolved_root, CANONICAL_PATHS["terminal_rows"])
    observed_envelope = read_json(envelope_path)
    observed_rows = read_jsonl(rows_path)
    if not isinstance(observed_envelope, Mapping):
        raise Pilot3ExecutionError("terminal envelope is not a JSON object")
    for index, raw in enumerate(observed_rows, 1):
        if not isinstance(raw, Mapping):
            raise Pilot3ExecutionError(f"terminal row {index} is not an object")
        _verify_seal(raw, field="record_sha256", label=f"terminal row {index}")
    expected_rows, expected = _terminal_envelope_payload(
        resolved_root, verified_measurement=verified_measurement
    )
    if (
        dict(observed_envelope) != expected
        or observed_rows != expected_rows
        or hash_file(rows_path) != expected["terminal_rows_file_sha256"]
    ):
        raise Pilot3ExecutionError("terminal envelope is stale or tampered")
    return {"envelope": expected, "rows": expected_rows}


def verify_terminal_envelope(root: Path) -> Dict[str, Any]:
    """Recompute the terminal envelope without trusting its status strings."""

    return _verify_terminal_envelope_artifacts(root)


def _analysis_contract(root: Path) -> Dict[str, Any]:
    path = _require_file(root, Path("reports/pilot_3/evidence/analysis_contract.json"))
    raw = read_json(path)
    if not isinstance(raw, Mapping):
        raise Pilot3ExecutionError("analysis contract must be a JSON object")
    value = dict(raw)
    _verify_seal(value, field="semantic_sha256", label="analysis contract")
    return value


def _verified_analysis_payload(root: Path) -> Dict[str, Any]:
    """Compute the registered analysis exclusively from canonical verified files."""

    resolved_root = _root(root)
    measurement = verify_generated_measurement(resolved_root)
    gate = measurement["generation"]["gate"]
    terminal = _verify_terminal_envelope_artifacts(
        resolved_root, verified_measurement=measurement
    )
    contract = _analysis_contract(resolved_root)
    protocol = measurement["protocol"]
    tau = protocol.get("development_results", {}).get("tau", {})
    tau_by_outcome = {
        "target_improvement": tau.get("target"),
        "specificity_difference_in_differences": tau.get("specificity"),
    }
    distance_rows = measurement["distances"]
    runtime_bindings = {
        "verification_authority": "canonical_file_backed_p3_t14_runtime_verifier",
        "caller_supplied_hashes_or_statuses_used": False,
        "generation_authorization_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_authorization"])
        ),
        "generation_authorization_result_sha256": gate[
            "operational_generation_authorization"
        ]["result_sha256"],
        "generation_gate_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_gate"])
        ),
        "generation_gate_result_sha256": gate["result_sha256"],
        "generation_completion_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generation_completion"])
        ),
        "generation_completion_report_sha256": measurement["generation"]["completion"][
            "report_sha256"
        ],
        "terminal_envelope_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["terminal_envelope"])
        ),
        "terminal_envelope_result_sha256": terminal["envelope"]["result_sha256"],
        "generated_measurement_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generated_measurement"])
        ),
        "generated_measurement_result_sha256": measurement["measurement"]["result_sha256"],
        "analysis_contract_file_sha256": hash_file(
            _require_file(resolved_root, Path("reports/pilot_3/evidence/analysis_contract.json"))
        ),
        "analysis_contract_semantic_sha256": contract["semantic_sha256"],
        "schedule_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["schedule_manifest"])
        ),
        "schedule_semantic_sha256": stable_hash(measurement["schedule_rows"]),
        "generated_distance_file_sha256": hash_file(
            _require_file(resolved_root, CANONICAL_PATHS["generated_distances"])
        ),
        "generated_distance_semantic_sha256": stable_hash(distance_rows),
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "generation_gate_status": "open",
        "generation_authorization_status": GENERATION_AUTHORIZATION_OPEN,
        "generation_completion_status": "complete",
        "terminal_envelope_status": "complete",
        "generated_measurement_status": "complete",
    }
    return _analyze_phase_b_core_for_verified_inputs(
        schedule_rows=measurement["schedule_rows"],
        terminal_rows=terminal["rows"],
        distance_rows=distance_rows,
        analysis_contract=contract,
        runtime_bindings=runtime_bindings,
        tau_by_outcome=tau_by_outcome,
    )


def run_verified_analysis(root: Path) -> Dict[str, Any]:
    """Write the analysis computed by the canonical file-backed verifier."""

    resolved_root = _root(root)
    result = _verified_analysis_payload(resolved_root)
    write_json(_path(resolved_root, CANONICAL_PATHS["analysis"]), result)
    return result


def verify_analysis(root: Path) -> Dict[str, Any]:
    resolved_root = _root(root)
    path = _require_file(resolved_root, CANONICAL_PATHS["analysis"])
    observed = read_json(path)
    if not isinstance(observed, Mapping):
        raise Pilot3ExecutionError("analysis artifact is not a JSON object")
    _verify_seal(observed, field="result_sha256", label="analysis")
    expected = _verified_analysis_payload(resolved_root)
    if dict(observed) != expected:
        raise Pilot3ExecutionError("analysis does not recompute from verified artifacts")
    return expected


def _fmt(value: object, digits: int = 4) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{float(value):.{digits}f}"
    return "—" if value is None else str(value)


def render_report(analysis: Mapping[str, Any]) -> str:
    availability = analysis["availability"]
    conditional = analysis["conditional_a_vector_proximity"]
    missingness = analysis["finite_schedule_missingness"]
    decision = analysis["decision"]
    terminal = analysis["terminal_accounting"]
    lines = [
        "# Pilot 3 final report",
        "",
        "## Outcome",
        "",
        f"- Scientific execution: **{analysis['status']}**.",
        f"- Registered decision: **{str(decision['status']).upper()}**.",
        f"- All 320 scheduled requests terminal: **{str(terminal['complete']).lower()}**.",
        f"- Usable named/control pairs: **{availability['usable_pairs']}/256**.",
        "",
        "Completion means the frozen study was executed and accounted for; it does not by "
        "itself mean that the registered proximity result was supported.",
        "",
        "## Claim boundary",
        "",
        "This is a finite-roster, finite-content result for requests carrying the exact "
        "`gpt-image-2` label through the pinned `~/dev/openai-oauth` route. It is not an "
        "executed-model or snapshot attestation, artist-superpopulation result, authorship "
        "test, broad style-fidelity score, or future-prompt claim.",
        "",
        "## Intention-to-request availability",
        "",
        "Metric | Estimate | Simultaneous bound | Threshold | Pass",
        "--- | ---: | ---: | ---: | ---",
        (
            "Aggregate matched-pair availability | "
            f"{_fmt(availability['estimate'])} | "
            f"{_fmt(availability['simultaneous_one_sided_lower_bound'])} | "
            f"{_fmt(availability['aggregate_threshold'])} | "
            f"{str(availability['component_decisions']['aggregate_lower_bound_passes']).lower()}"
        ),
    ]
    for artist_id in EXPECTED_ARTIST_IDS:
        row = availability["per_artist"][artist_id]
        lines.append(
            f"`{artist_id}` | {_fmt(row['estimate'])} | "
            f"{_fmt(row['simultaneous_one_sided_lower_bound'])} | "
            f"{_fmt(row['threshold'])} | {str(row['passes']).lower()}"
        )
    lines.extend(
        [
            "",
            "The simultaneous cross-artist availability-disparity upper bound is "
            f"{_fmt(availability['simultaneous_artist_disparity_upper_bound'])} "
            f"against the frozen maximum {_fmt(availability['artist_disparity_threshold'])}.",
            "",
            "## A-vector proximity conditional on usable pairs",
            "",
            "Endpoint | Estimate | Familywise lower bound | Pass",
            "--- | ---: | ---: | ---",
        ]
    )
    for outcome in PRIMARY_OUTCOMES:
        row = conditional["outcomes"][outcome]
        lines.append(
            f"`{outcome}` | {_fmt(row['estimate'])} | "
            f"{_fmt(row['bonferroni_one_sided_lower_bound'])} | "
            f"{str(row['passes']).lower()}"
        )
    lines.extend(
        [
            "",
            "These estimates condition on usable named/control pairs. Unavailable images "
            "are not assigned features or imputed.",
            "",
            "## Finite-schedule missingness bounds",
            "",
            "Endpoint | Worst-case lower | Best-case upper | Positive lower",
            "--- | ---: | ---: | ---",
        ]
    )
    for outcome in PRIMARY_OUTCOMES:
        row = missingness["outcomes"][outcome]
        lines.append(
            f"`{outcome}` | {_fmt(row['worst_case_lower_bound'])} | "
            f"{_fmt(row['best_case_upper_bound'])} | "
            f"{str(row['positive_worst_case_lower_bound']).lower()}"
        )
    lines.extend(
        [
            "",
            "The bounds apply only to the bounded `tanh(delta/tau)` scores over the realized "
            "256-pair schedule, not to unbounded Euclidean effects or future generator draws.",
            "",
            "## Terminal accounting",
            "",
            "Category | Requests",
            "--- | ---:",
        ]
    )
    for category, count in terminal["category_counts"].items():
        lines.append(f"`{category}` | {count}")
    lines.extend(
        [
            "",
            "## Registered decision rationale",
            "",
        ]
    )
    lines.extend(f"- `{reason}`" for reason in decision["reasons"])
    lines.extend(
        [
            "",
            f"Analysis result SHA-256: `{analysis['result_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def _next_step(decision: str) -> str:
    return {"supported": "go", "mixed": "narrow", "unsupported": "redesign"}[decision]


def _write_report(root: Path, analysis: Mapping[str, Any]) -> str:
    rendered = render_report(analysis)
    path = _path(root, CANONICAL_PATHS["report"])
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_replace_bytes(path, rendered.encode("utf-8"))
    return rendered


def _completion_payload(root: Path, analysis: Mapping[str, Any]) -> Dict[str, Any]:
    terminal = read_json(_require_file(root, CANONICAL_PATHS["terminal_envelope"]))
    measurement = read_json(_require_file(root, CANONICAL_PATHS["generated_measurement"]))
    generation = read_json(_require_file(root, CANONICAL_PATHS["generation_completion"]))
    authorization = read_json(
        _require_file(root, CANONICAL_PATHS["generation_authorization"])
    )
    if not isinstance(authorization, Mapping):
        raise Pilot3ExecutionError("generation authorization completion input is malformed")
    payload = {
        "record_type": "pilot3_scientific_completion",
        "schema_version": COMPLETION_SCHEMA,
        "status": "complete",
        "scientific_completion": True,
        "hypothesis_support_is_not_completion": True,
        "registered_decision": analysis["decision"]["status"],
        "roadmap_next_step": _next_step(str(analysis["decision"]["status"])),
        "requested_model_label": EXPECTED_REQUESTED_LABEL,
        "transport": EXPECTED_TRANSPORT,
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "scheduled_request_count": 320,
        "generation_authorization_result_sha256": authorization["result_sha256"],
        "global_stop_triggered": generation["global_stop_triggered"],
        "not_sent_global_stop_count": generation["disposition_counts"].get(
            "not_sent_global_stop", 0
        ),
        "post_exchange_observed_count": generation[
            "post_exchange_observed_attempt_count"
        ],
        "physical_post_or_indeterminate_count": generation["attempt_count"],
        "all_requests_terminal": analysis["terminal_accounting"]["complete"],
        "generation_completion_report_sha256": generation["report_sha256"],
        "terminal_envelope_result_sha256": terminal["result_sha256"],
        "generated_measurement_result_sha256": measurement["result_sha256"],
        "analysis_result_sha256": analysis["result_sha256"],
        "report_file_sha256": hash_file(_require_file(root, CANONICAL_PATHS["report"])),
        "post_result_extension_or_rescue_run_allowed": False,
    }
    return _seal(payload, field="result_sha256")


def _requirement_audit_payload(
    root: Path, analysis: Mapping[str, Any], completion: Mapping[str, Any]
) -> Dict[str, Any]:
    gate = read_json(_require_file(root, CANONICAL_PATHS["generation_gate"]))
    execution = read_json(_require_file(root, CANONICAL_PATHS["generation_execution"]))
    authorization = read_json(
        _require_file(root, CANONICAL_PATHS["generation_authorization"])
    )
    if not all(isinstance(value, Mapping) for value in (gate, execution, authorization)):
        raise Pilot3ExecutionError(
            "generation authorization/gate/execution audit inputs are malformed"
        )
    checks = {
        "P3-T01": "p3_t01_artist_source_feasibility" in gate["prerequisites"],
        "P3-T02": "p3_t02_pilot2_baseline_recovery" in gate["prerequisites"],
        "P3-T03": "p3_t03_planning_index" in gate["prerequisites"],
        "P3-T04": "p3_t04_phase_b_design_and_budget_approval" in gate["prerequisites"],
        "P3-T05": "p3_t05_corpus_manifest" in gate["prerequisites"],
        "P3-T06": "p3_t06_split_manifest" in gate["prerequisites"],
        "P3-T07": "p3_t07_a_vector_protocol" in gate["prerequisites"],
        "P3-T08": "p3_t08_a_vector_external_validation" in gate["prerequisites"],
        "P3-T09": "p3_t09_lee_replication" in gate["prerequisites"],
        "P3-T10": "p3_t10_human_validation" in gate["prerequisites"],
        "P3-T11": "p3_t11_transport_qualification" in gate["prerequisites"],
        "P3-T12": "p3_t12_schedule_manifest" in gate["prerequisites"],
        "P3-T13": "p3_t13_analysis_contract" in gate["prerequisites"],
        "P3-T14": (
            gate.get("status") == "open"
            and gate.get("generation_authorized") is True
            and authorization.get("status") == GENERATION_AUTHORIZATION_OPEN
            and gate.get("operational_generation_authorization", {}).get("result_sha256")
            == authorization.get("result_sha256")
        ),
        "per_physical_post_gate_recorded": (
            execution.get("per_physical_post_request_gate_required") is True
            and execution.get("request_gate_context_count")
            == execution.get("post_intent_count")
        ),
        "global_stop_accounting_distinguishes_post_or_indeterminate_from_no_post": (
            execution.get("fake_attempt_row_count") == 0
            and (
                (
                    execution.get("global_stop_triggered") is True
                    and execution.get("physical_post_or_indeterminate_cell_count")
                    == 1
                    and execution.get("no_post_cell_count")
                    == execution.get("global_stop_disposition_count")
                    and execution.get(
                        "only_preflight_cell_posted_or_indeterminate_before_global_stop"
                    )
                    is True
                )
                or (
                    execution.get("global_stop_triggered") is False
                    and execution.get("global_stop_disposition_count") == 0
                    and execution.get("no_post_cell_count") == 0
                )
            )
        ),
        "all_320_requests_terminal": analysis["terminal_accounting"]["complete"],
        "generated_measurement_complete": _require_file(
            root, CANONICAL_PATHS["generated_measurement"]
        ).is_file(),
        "registered_analysis_complete": analysis.get("status") == "complete",
        "deterministic_report_present": _require_file(root, CANONICAL_PATHS["report"]).is_file(),
        "scientific_completion_recorded": completion.get("scientific_completion") is True,
        "only_gpt_image_2_scheduled": analysis.get("requested_model_label")
        == EXPECTED_REQUESTED_LABEL,
        "no_executed_model_claim": completion.get("executed_model_claims") is False,
    }
    payload = {
        "record_type": "pilot3_requirement_audit",
        "schema_version": REQUIREMENT_AUDIT_SCHEMA,
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_count": len(checks),
        "analysis_result_sha256": analysis["result_sha256"],
        "completion_result_sha256": completion["result_sha256"],
    }
    return _seal(payload, field="result_sha256")


def _media_type(path: Path) -> str:
    if path.suffix == ".jsonl":
        return "application/x-ndjson"
    if path.suffix == ".json":
        return "application/json"
    if path.suffix == ".md":
        return "text/markdown"
    if path.suffix == ".npy":
        return "application/x-npy"
    if path.suffix == ".png":
        return "image/png"
    return "application/octet-stream"


def _repository_relative_artifact(root: Path, path: Path) -> Path:
    try:
        relative = path.resolve().relative_to(_root(root))
    except ValueError as exc:
        raise Pilot3ExecutionError(f"artifact is outside the repository: {path}") from exc
    if not path.is_file():
        raise Pilot3ExecutionError(f"indexed artifact is missing: {relative}")
    return relative


def _artifact_index_payload(
    root: Path, analysis: Mapping[str, Any], completion: Mapping[str, Any]
) -> Dict[str, Any]:
    paths = sorted(
        set(FREEZE_B_EVIDENCE_CLOSURE + FREEZE_B_OPERATIONAL_CLOSURE)
        | {
            CANONICAL_PATHS[name]
            for name in (
                "generation_gate",
                "generation_post_intents",
                "generation_attempts",
                "generation_runtime_revalidations",
                "generation_execution",
                "generation_completion",
                "successful_outputs",
                "generated_preprocessing",
                "generated_a_vectors",
                "generated_distances",
                "generated_measurement",
                "terminal_rows",
                "terminal_envelope",
                "analysis",
                "report",
                "completion",
                "requirement_audit",
            )
        }
    )
    dynamic_paths: set[Path] = set()
    global_stop_path = _path(root, CANONICAL_PATHS["generation_global_stops"])
    if global_stop_path.is_file():
        dynamic_paths.add(
            _repository_relative_artifact(root, global_stop_path)
        )
    qualification = read_json(
        _require_file(root, CANONICAL_PATHS["transport_qualification"])
    )
    successful = read_json(_require_file(root, CANONICAL_PATHS["successful_outputs"]))
    preprocessing = read_jsonl(
        _require_file(root, CANONICAL_PATHS["generated_preprocessing"])
    )
    if not isinstance(qualification, Mapping) or not isinstance(successful, Mapping):
        raise Pilot3ExecutionError("binary artifact manifests must be JSON objects")
    qualification_output = qualification.get("output_evidence")
    if not isinstance(qualification_output, Mapping):
        raise Pilot3ExecutionError("P3-T11 output evidence is missing from artifact index")
    dynamic_paths.add(
        _repository_relative_artifact(
            root, _resolve_recorded(root, qualification_output.get("output_path"))
        )
    )
    for output in successful.get("outputs", []):
        if not isinstance(output, Mapping):
            raise Pilot3ExecutionError("successful output manifest is malformed")
        dynamic_paths.add(
            _repository_relative_artifact(
                root, _resolve_recorded(root, output.get("output_path"))
            )
        )
    for row in preprocessing:
        if not isinstance(row, Mapping):
            raise Pilot3ExecutionError("preprocessing manifest is malformed")
        dynamic_paths.add(
            _repository_relative_artifact(
                root, _resolve_recorded(root, row.get("normalized_png_path"))
            )
        )
    phase_config = load_phase_a_config(root)
    for key in ("development_acquisitions", "external_acquisitions"):
        acquisition_path = _require_file(root, Path(phase_config["paths"][key]))
        for row in read_jsonl(acquisition_path):
            if not isinstance(row, Mapping):
                raise Pilot3ExecutionError("Phase-A acquisition manifest is malformed")
            for field in ("raw_path", "normalized_path"):
                dynamic_paths.add(
                    _repository_relative_artifact(
                        root, _resolve_recorded(root, row.get(field))
                    )
                )
    try:
        normalization_resolution = require_preprocessing_incident_resolution(root)
    except Pilot3PhaseAError as exc:
        raise Pilot3ExecutionError(
            f"artifact index cannot verify preprocessing incident resolution: {exc}"
        ) from exc
    corrections = normalization_resolution.get("corrections")
    if not isinstance(corrections, Mapping):
        raise Pilot3ExecutionError(
            "artifact index preprocessing correction map is malformed"
        )
    for row in corrections.values():
        if not isinstance(row, Mapping):
            raise Pilot3ExecutionError(
                "artifact index preprocessing correction row is malformed"
            )
        for field in ("original_normalized_path", "effective_normalized_path"):
            dynamic_paths.add(
                _repository_relative_artifact(
                    root, _resolve_recorded(root, row.get(field))
                )
            )
    attempt_ledger = AppendOnlyAttemptLedger(
        _require_file(root, CANONICAL_PATHS["generation_attempts"])
    )
    for directory in (attempt_ledger.sidecar_dir, attempt_ledger.recovery_dir):
        if directory.is_dir():
            dynamic_paths.update(
                _repository_relative_artifact(root, path)
                for path in directory.rglob("*")
                if path.is_file()
            )
    paths = sorted(set(paths) | dynamic_paths)
    artifacts = []
    for relative in paths:
        path = _require_file(root, relative)
        artifacts.append(
            {
                "path": relative.as_posix(),
                "media_type": _media_type(relative),
                "size_bytes": path.stat().st_size,
                "sha256": hash_file(path),
            }
        )
    payload = {
        "record_type": "pilot3_artifact_index",
        "schema_version": ARTIFACT_INDEX_SCHEMA,
        "status": "complete",
        "analysis_result_sha256": analysis["result_sha256"],
        "completion_result_sha256": completion["result_sha256"],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    return _seal(payload, field="result_sha256")


def finalize_pilot(root: Path) -> Dict[str, Any]:
    """Write and verify the deterministic final report, completion, audit, and index."""

    resolved_root = _root(root)
    analysis = verify_analysis(resolved_root)
    _write_report(resolved_root, analysis)
    completion = _completion_payload(resolved_root, analysis)
    write_json(_path(resolved_root, CANONICAL_PATHS["completion"]), completion)
    audit = _requirement_audit_payload(resolved_root, analysis, completion)
    if audit["status"] != "pass":
        raise Pilot3ExecutionError(f"Pilot-3 requirement audit failed: {audit['checks']}")
    write_json(_path(resolved_root, CANONICAL_PATHS["requirement_audit"]), audit)
    index = _artifact_index_payload(resolved_root, analysis, completion)
    write_json(_path(resolved_root, CANONICAL_PATHS["artifact_index"]), index)
    return {
        "status": "complete",
        "decision": analysis["decision"]["status"],
        "roadmap_next_step": completion["roadmap_next_step"],
        "analysis_result_sha256": analysis["result_sha256"],
        "completion_result_sha256": completion["result_sha256"],
        "requirement_audit_result_sha256": audit["result_sha256"],
        "artifact_index_result_sha256": index["result_sha256"],
    }


def verify_pilot_completion(root: Path) -> Dict[str, Any]:
    """Offline end-to-end verifier for a completed Pilot 3."""

    resolved_root = _root(root)
    analysis = verify_analysis(resolved_root)
    report_path = _require_file(resolved_root, CANONICAL_PATHS["report"])
    if report_path.read_text(encoding="utf-8") != render_report(analysis):
        raise Pilot3ExecutionError("final Markdown report is stale")
    completion_raw = read_json(_require_file(resolved_root, CANONICAL_PATHS["completion"]))
    audit_raw = read_json(_require_file(resolved_root, CANONICAL_PATHS["requirement_audit"]))
    index_raw = read_json(_require_file(resolved_root, CANONICAL_PATHS["artifact_index"]))
    if not all(isinstance(value, Mapping) for value in (completion_raw, audit_raw, index_raw)):
        raise Pilot3ExecutionError("final completion artifacts must be JSON objects")
    completion = _completion_payload(resolved_root, analysis)
    if dict(completion_raw) != completion:
        raise Pilot3ExecutionError("scientific completion artifact is stale")
    audit = _requirement_audit_payload(resolved_root, analysis, completion)
    if dict(audit_raw) != audit or audit["status"] != "pass":
        raise Pilot3ExecutionError("requirement audit is stale or failing")
    index = _artifact_index_payload(resolved_root, analysis, completion)
    if dict(index_raw) != index:
        raise Pilot3ExecutionError("artifact index is stale")
    return {
        "status": "verified_complete",
        "decision": analysis["decision"]["status"],
        "roadmap_next_step": completion["roadmap_next_step"],
        "analysis_result_sha256": analysis["result_sha256"],
        "completion_result_sha256": completion["result_sha256"],
        "requirement_audit_result_sha256": audit["result_sha256"],
        "artifact_index_result_sha256": index["result_sha256"],
    }


__all__ = [
    "CANONICAL_PATHS",
    "FREEZE_B_CODE_CLOSURE",
    "FREEZE_B_EVIDENCE_CLOSURE",
    "FREEZE_B_OPERATIONAL_CLOSURE",
    "GENERATION_AUTHORIZATION_CLOSED",
    "GENERATION_AUTHORIZATION_OPEN",
    "Pilot3ExecutionError",
    "build_generation_authorization",
    "build_generation_gate",
    "capture_oauth_runtime_evidence",
    "finalize_pilot",
    "generation_execution_gate",
    "generation_request_gate",
    "measure_generated_outputs",
    "render_report",
    "run_verified_analysis",
    "run_canonical_generation_grid",
    "run_canonical_transport_qualification",
    "verify_analysis",
    "verify_generated_measurement",
    "verify_generation_completion_files",
    "verify_generation_authorization",
    "verify_generation_gate",
    "verify_pilot_completion",
    "verify_terminal_envelope",
    "verify_transport_qualification_window",
    "write_generation_completion",
    "write_generation_gate",
    "write_qualification_authorization",
    "write_terminal_envelope",
]
