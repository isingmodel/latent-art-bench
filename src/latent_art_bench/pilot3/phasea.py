"""Prospective real-only qualification of the Pilot 3 A-vector geometry.

The module enforces the two real-data freezes:

* development acquisition/extraction may use only ``development_training`` and
  ``development_calibration`` rows;
* the ``external_holdout`` may be opened only by the one-shot transaction bound to the
  self-hash of a committed, still-current P3-T07 protocol artifact.

All image payloads and normalized PNGs are content addressed.  The image-acquisition intent
is fsynced before a prior local file is opened or an HTTP request is sent.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import platform
import subprocess
import time
from collections import Counter
from contextlib import contextmanager
from itertools import permutations, product
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

import httpx
import numpy as np
from PIL import Image

try:
    import fcntl
except ImportError as exc:  # pragma: no cover - Pilot 3 is frozen for a POSIX runtime.
    raise RuntimeError("Pilot 3 external transactions require POSIX file locking") from exc

from latent_art_bench.features.learned_formal import (
    SOURCE_REPLICATION_POLICY,
    LearnedFormalPins,
    extract_learned_formal,
    learned_formal_vector_sha256,
    load_pinned_sd2_vae,
)
from latent_art_bench.io import (
    canonical_json,
    hash_bytes,
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
)
from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig
from latent_art_bench.pilot2.learned_formal import (
    Pilot2FrozenPCA,
    balanced_accuracy,
    fit_train_only_pca,
    predict_nearest_centroid,
    transform_with_pca,
)
from latent_art_bench.pilot2.preprocessing import common_png_bytes
from latent_art_bench.pilot3.design_freeze import verify_phase_b_freeze_bundle
from latent_art_bench.pilot3.planning import verify_planning_bundle

PHASE_A_SCHEMA = "pilot3-phase-a/1.0"
A_VECTOR_PROTOCOL_SCHEMA = "pilot3-a-vector-protocol/1.0"
EXTERNAL_RESULT_SCHEMA = "pilot3-a-vector-external-validation/1.0"

DEFAULT_CONFIG = Path("configs/pilot_3/phase_a.json")
DEFAULT_SPLITS = Path("data/manifests/pilot_3/real_splits.jsonl")
DEFAULT_EXTERNAL_UNSEAL_RECEIPT = Path(
    "artifacts/pilot_3/external_unseal_receipt.json"
)

DEVELOPMENT_PARTITIONS = frozenset(
    {"development_training", "development_calibration"}
)
EXTERNAL_PARTITION = "external_holdout"
EXPECTED_ARTISTS = (
    "alfred_sisley",
    "camille_pissarro",
    "paul_cezanne",
    "pierre_auguste_renoir",
)
DEVELOPMENT_SOURCES = ("aic", "met")
EXTERNAL_SOURCE = "museum_balanced"
EXPECTED_EXTERNAL_BLOCKS = ("minneapolis", "dallas", "toledo")
EXPECTED_SOURCES = (*DEVELOPMENT_SOURCES, EXTERNAL_SOURCE)

EXTERNAL_UNSEAL_RECEIPT_SCHEMA = "pilot3-external-unseal-receipt/1.0"
HTTP_ATTEMPT_SCHEMA = "pilot3-real-acquisition-http-attempt/1.0"
MAX_HTTP_ATTEMPTS = 4
MAX_HTTP_RESPONSE_BYTES = 128 * 1024 * 1024
HTTP_STREAM_CHUNK_BYTES = 64 * 1024
_EXTERNAL_TRANSACTION_CAPABILITY = object()
_EXTRACTION_RUNTIME_KEYS = (
    "source_repository",
    "source_revision",
    "model_repository",
    "model_revision",
    "config_sha256",
    "weights_sha256",
    "opencv_version",
    "opencv_build_sha256",
    "pillow_version",
    "jpeg_codec_version",
    "python_version",
    "platform_system",
    "platform_release",
    "platform_machine",
    "numpy_version",
    "torch_version",
    "diffusers_version",
    "torch_mps_built",
    "torch_mps_available",
    "device",
)


class Pilot3PhaseAError(RuntimeError):
    """A fail-closed Phase-A contract violation."""


def _resolve(root: Path, value: str | Path) -> Path:
    root = Path(root).expanduser().resolve()
    candidate = Path(value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise Pilot3PhaseAError(f"repository path escapes root: {value}") from exc
    return resolved


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _self_hash(payload: Mapping[str, Any], field: str = "result_sha256") -> Dict[str, Any]:
    result = dict(payload)
    result.pop(field, None)
    result[field] = stable_hash(result)
    return result


def verify_self_hash(payload: Mapping[str, Any], field: str = "result_sha256") -> str:
    recorded = payload.get(field)
    if not _is_sha256(recorded):
        raise Pilot3PhaseAError(f"artifact lacks a valid {field}")
    unsigned = dict(payload)
    unsigned.pop(field, None)
    observed = stable_hash(unsigned)
    if observed != recorded:
        raise Pilot3PhaseAError(
            f"artifact {field} is stale: expected {recorded}, recomputed {observed}"
        )
    return str(recorded)


def load_phase_a_config(root: Path, path: Path = DEFAULT_CONFIG) -> Dict[str, Any]:
    resolved = _resolve(root, path)
    canonical = _resolve(root, DEFAULT_CONFIG)
    if resolved != canonical:
        raise Pilot3PhaseAError(
            f"Phase-A execution accepts only the canonical config: {DEFAULT_CONFIG}"
        )
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    config = read_json(resolved)
    if not isinstance(config, dict) or config.get("schema_version") != PHASE_A_SCHEMA:
        raise Pilot3PhaseAError("Phase-A config has the wrong schema")
    roster = config.get("finite_roster", {})
    if tuple(roster.get("artist_ids", ())) != EXPECTED_ARTISTS:
        raise Pilot3PhaseAError("Phase-A config does not contain the frozen artist order")
    if roster.get("artist_superpopulation_claim") is not False:
        raise Pilot3PhaseAError("Phase-A must retain a finite-roster estimand")
    neighbor_map = roster.get("neighbor_map")
    if not isinstance(neighbor_map, dict) or set(neighbor_map) != set(EXPECTED_ARTISTS):
        raise Pilot3PhaseAError("Phase-A neighbor map is incomplete")
    if any(
        neighbor_map.get(neighbor_map.get(artist)) != artist
        or neighbor_map.get(artist) == artist
        for artist in EXPECTED_ARTISTS
    ):
        raise Pilot3PhaseAError("Phase-A neighbor map must consist of reciprocal disjoint pairs")
    if config.get("source_roles") != {
        "aic": "development",
        "met": "development",
        EXTERNAL_SOURCE: "external_holdout",
    }:
        raise Pilot3PhaseAError("Phase-A source roles are not frozen")
    allocation = config.get("allocation")
    expected_allocation = {
        "training_per_artist": 8,
        "calibration_per_artist": 2,
        "external_per_artist": 3,
        "training_per_artist_development_source": 4,
        "calibration_per_artist_development_source": 1,
        "external_collection_block_count": 3,
        "external_per_artist_collection_block": 1,
        "external_replacement_policy": "none_after_freeze",
    }
    if not isinstance(allocation, Mapping) or any(
        allocation.get(key) != value for key, value in expected_allocation.items()
    ):
        raise Pilot3PhaseAError("Phase-A allocation is not the frozen 8+2+3 design")
    external_gate = config.get("external_gate")
    if (
        not isinstance(external_gate, Mapping)
        or external_gate.get("permutation_scheme")
        != "exhaustive_independent_artist_label_permutations_within_each_complete_collection_block"
        or external_gate.get("permutation_assignment_count") != 13_824
        or "permutation_draws" in external_gate
        or "permutation_seed" in external_gate
    ):
        raise Pilot3PhaseAError(
            "Phase-A external permutation contract must exhaust the exact 24^3 assignments"
        )
    if config.get("acquisition_http") != {
        "method": "GET",
        "follow_redirects": True,
        "timeout_seconds": 120.0,
        "max_attempts": MAX_HTTP_ATTEMPTS,
        "max_response_bytes": MAX_HTTP_RESPONSE_BYTES,
        "trust_env": False,
        "retry_backoff_seconds": [1.0, 2.0, 4.0],
        "retryable_status_codes": [408, 409, 425, 429],
        "retryable_status_class": 5,
        "retryable_transport_errors": True,
        "retryable_invalid_content_type": True,
    }:
        raise Pilot3PhaseAError("Phase-A HTTP acquisition policy is not frozen")
    boundary = config.get("cross_digitization_boundary", {})
    if (
        boundary.get("independent_reproductions_required") is not False
        or "exact frozen museum image bytes" not in str(boundary.get("allowed_claim", ""))
    ):
        raise Pilot3PhaseAError("cross-digitization claim boundary is missing")
    return config


def _row_hash_is_current(row: Mapping[str, Any]) -> bool:
    value = row.get("row_sha256")
    unsigned = dict(row)
    unsigned.pop("row_sha256", None)
    return _is_sha256(value) and stable_hash(unsigned) == value


def validate_real_splits(
    rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    """Validate 40 development works and three complete external museum blocks."""

    selected = [dict(row) for row in rows if row.get("selection_status", "selected") == "selected"]
    if len(selected) != 52:
        raise Pilot3PhaseAError(f"Phase-A requires exactly 52 selected rows, found {len(selected)}")
    required = {
        "canonical_work_id",
        "artist_id",
        "artist_name",
        "asset_provider",
        "collection_block_id",
        "delivery_height",
        "delivery_width",
        "museum_accession",
        "source_id",
        "source_object_id",
        "source_url",
        "image_url",
        "partition",
    }
    for row in selected:
        if (
            row.get("record_type") != "pilot3_real_split_row"
            or row.get("schema_version") != "pilot3-real-split-row/1.0"
        ):
            raise Pilot3PhaseAError("split row schema or record type is stale")
        missing = sorted(key for key in required if not row.get(key))
        if missing:
            raise Pilot3PhaseAError(
                f"split row {row.get('canonical_work_id', '<unknown>')} lacks {', '.join(missing)}"
            )
        if not _row_hash_is_current(row):
            raise Pilot3PhaseAError(f"split row hash is stale: {row['canonical_work_id']}")
        if any(
            type(row.get(field)) is not int or int(row[field]) <= 0
            for field in ("delivery_width", "delivery_height")
        ):
            raise Pilot3PhaseAError(
                f"split row {row['canonical_work_id']} lacks positive delivered dimensions"
            )
    work_ids = [str(row["canonical_work_id"]) for row in selected]
    if len(set(work_ids)) != len(work_ids):
        raise Pilot3PhaseAError("Phase-A work identifiers are not unique")
    if {str(row["artist_id"]) for row in selected} != set(EXPECTED_ARTISTS):
        raise Pilot3PhaseAError("split manifest artist roster is stale")
    if {str(row["source_id"]) for row in selected} != set(EXPECTED_SOURCES):
        raise Pilot3PhaseAError("split manifest source roster is stale")
    counts = Counter(
        (str(row["artist_id"]), str(row["source_id"]), str(row["partition"]))
        for row in selected
    )
    expected: Counter[Tuple[str, str, str]] = Counter()
    for artist in EXPECTED_ARTISTS:
        for source in DEVELOPMENT_SOURCES:
            expected[(artist, source, "development_training")] = 4
            expected[(artist, source, "development_calibration")] = 1
        expected[(artist, EXTERNAL_SOURCE, EXTERNAL_PARTITION)] = len(
            EXPECTED_EXTERNAL_BLOCKS
        )
    if counts != expected:
        unexpected = {str(key): value for key, value in (counts - expected).items()}
        missing = {str(key): value for key, value in (expected - counts).items()}
        raise Pilot3PhaseAError(
            f"split allocation is not 8+2+3 per artist; missing={missing}, unexpected={unexpected}"
        )
    accession_keys = [
        (str(row["collection_block_id"]), str(row["museum_accession"]))
        for row in selected
    ]
    if len(set(accession_keys)) != len(accession_keys):
        raise Pilot3PhaseAError("museum accessions are not unique within collection block")
    external_rows = [
        row for row in selected if row["partition"] == EXTERNAL_PARTITION
    ]
    block_counts = Counter(
        (str(row["collection_block_id"]), str(row["artist_id"]))
        for row in external_rows
    )
    expected_block_counts = Counter(
        (block, artist)
        for block in EXPECTED_EXTERNAL_BLOCKS
        for artist in EXPECTED_ARTISTS
    )
    if block_counts != expected_block_counts:
        raise Pilot3PhaseAError(
            "external split must contain exactly one work per artist in every frozen block"
        )
    for row in selected:
        source = str(row["source_id"])
        partition = str(row["partition"])
        if source == EXTERNAL_SOURCE and partition != EXTERNAL_PARTITION:
            raise Pilot3PhaseAError("museum-balanced rows are the sealed external source")
        if source != EXTERNAL_SOURCE and partition not in DEVELOPMENT_PARTITIONS:
            raise Pilot3PhaseAError("development-source row has an external partition")
    return sorted(selected, key=lambda row: str(row["canonical_work_id"]))


def load_real_splits(root: Path, config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    path = _resolve(root, config["paths"]["split_manifest"])
    if not path.is_file():
        raise FileNotFoundError(path)
    selected = validate_real_splits(read_jsonl(path), config)
    roster_path = _resolve(root, "configs/pilot_3/external_museum_blocks.json")
    if not roster_path.is_file():
        raise Pilot3PhaseAError("frozen external museum-block roster is missing")
    roster = read_json(roster_path)
    if not isinstance(roster, Mapping):
        raise Pilot3PhaseAError("external museum-block roster is malformed")
    policy = roster.get("block_policy")
    blocks = roster.get("blocks")
    if (
        roster.get("schema_version") != "pilot3-official-museum-block-roster/1.0"
        or roster.get("status") != "frozen_before_artwork_pixel_acquisition"
        or roster.get("source_id") != EXTERNAL_SOURCE
        or not isinstance(policy, Mapping)
        or policy.get("primary_block_count") != 3
        or policy.get("replacement_eligible_reserve_block_count") != 0
        or policy.get("works_per_artist_per_block") != 1
        or policy.get("replacement_unit") != "none_after_freeze"
        or policy.get("replacement_order") != []
        or policy.get("analysis_unit") != "holding_institution_block"
        or policy.get("permutation_rule")
        != "permute_the_four_artist_labels_independently_within_each_complete_block"
        or not isinstance(blocks, list)
    ):
        raise Pilot3PhaseAError("external museum-block policy is stale")
    roster_rows: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for raw_block in blocks:
        if not isinstance(raw_block, Mapping):
            raise Pilot3PhaseAError("external museum block is malformed")
        block = str(raw_block.get("block_id", ""))
        works = raw_block.get("works")
        if (
            block not in EXPECTED_EXTERNAL_BLOCKS
            or raw_block.get("role") != "primary"
            or not isinstance(works, list)
            or len(works) != len(EXPECTED_ARTISTS)
        ):
            raise Pilot3PhaseAError("external museum block membership is stale")
        for raw_work in works:
            if not isinstance(raw_work, Mapping):
                raise Pilot3PhaseAError("external museum-block work is malformed")
            artist = str(raw_work.get("artist_id", ""))
            key = (block, artist)
            if artist not in EXPECTED_ARTISTS or key in roster_rows:
                raise Pilot3PhaseAError("external museum-block artist allocation is stale")
            roster_rows[key] = {**dict(raw_work), "asset_provider": raw_block.get("asset_provider")}
    expected_keys = {
        (block, artist)
        for block in EXPECTED_EXTERNAL_BLOCKS
        for artist in EXPECTED_ARTISTS
    }
    if set(roster_rows) != expected_keys:
        raise Pilot3PhaseAError("external museum-block roster is incomplete")
    external = [row for row in selected if row["partition"] == EXTERNAL_PARTITION]
    for row in external:
        roster_row = roster_rows[
            (str(row["collection_block_id"]), str(row["artist_id"]))
        ]
        expected = {
            "asset_provider": roster_row["asset_provider"],
            "delivery_height": roster_row["delivery_height"],
            "delivery_width": roster_row["delivery_width"],
            "image_url": roster_row["image_url"],
            "museum_accession": roster_row["museum_accession"],
            "source_object_id": (
                f"{row['collection_block_id']}:{roster_row['museum_object_id']}"
            ),
            "source_url": roster_row["object_url"],
        }
        if any(row.get(key) != value for key, value in expected.items()):
            raise Pilot3PhaseAError(
                "external split disagrees with frozen museum-block roster: "
                + str(row["canonical_work_id"])
            )
    return selected


def _freeze_a1_closure_paths() -> List[str]:
    return sorted(
        {
            "pyproject.toml",
            "uv.lock",
            "configs/pilot_3/corpus_freeze.json",
            "configs/pilot_3/external_museum_blocks.json",
            "configs/pilot_3/generation_authorization.json",
            "configs/pilot_3/phase_a.json",
            "configs/pilot_3/planning.json",
            "configs/pilot_3/study.json",
            "configs/pilot_3/lee_review.json",
            "configs/pilot_3/metadata/authoritative_candidates.jsonl",
            "configs/pilot_3/metadata/source_snapshots.json",
            "data/manifests/pilot_3/corpus_selection.jsonl",
            "data/manifests/pilot_3/real_splits.jsonl",
            "data/manifests/pilot_3/prompts.jsonl",
            "data/manifests/pilot_3/schedule.jsonl",
            "docs/PILOT_3_PROTOCOL.md",
            "reports/pilot_3/planning_index.json",
            "reports/pilot_3/evidence/analysis_contract.json",
            "reports/pilot_3/evidence/artist_source_feasibility.json",
            "reports/pilot_3/evidence/corpus_selection.json",
            "reports/pilot_3/evidence/holdout_seal.json",
            "reports/pilot_3/evidence/human_validation_disposition.json",
            "reports/pilot_3/evidence/lee_replication.json",
            "reports/pilot_3/evidence/phase_b_design.json",
            "reports/pilot_3/evidence/prompt_schedule_contract.json",
            "src/latent_art_bench/cli.py",
            "src/latent_art_bench/io.py",
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
            "src/latent_art_bench/pilot3/feasibility.py",
            "src/latent_art_bench/pilot3/lee.py",
            "src/latent_art_bench/pilot3/phasea.py",
            "src/latent_art_bench/pilot3/planning.py",
            "tests/pilot3/test_design.py",
            "tests/pilot3/test_design_freeze.py",
            "tests/pilot3/test_feasibility.py",
            "tests/pilot3/test_lee.py",
            "tests/pilot3/test_phase_b_analysis.py",
            "tests/pilot3/test_phasea.py",
            "tests/pilot3/test_pilot3_corpus.py",
            "tests/pilot3/test_planning.py",
        }
    )


def require_development_freeze(root: Path) -> Dict[str, str]:
    """Require the complete Freeze-A1 closure to be committed and byte-current."""

    root = Path(root).expanduser().resolve()
    corpus_path = root / "reports/pilot_3/evidence/corpus_selection.json"
    planning_path = root / "reports/pilot_3/planning_index.json"
    corpus = read_json(corpus_path)
    planning = read_json(planning_path)
    if not isinstance(corpus, dict) or corpus.get("status") != "freeze_a1_complete":
        raise Pilot3PhaseAError("development gate remains closed: Freeze-A1 corpus is absent")
    if not isinstance(planning, dict) or planning.get("generation_gate") != "closed":
        raise Pilot3PhaseAError("development gate requires the closed-gate planning index")
    verify_self_hash(corpus, "semantic_sha256")
    verify_self_hash(planning, "result_sha256")
    try:
        verify_planning_bundle(root)
    except Exception as exc:
        raise Pilot3PhaseAError(
            "development gate deterministic planning verification failed"
        ) from exc
    try:
        verify_phase_b_freeze_bundle(root)
    except Exception as exc:
        raise Pilot3PhaseAError(
            "development gate deterministic Phase-B verification failed"
        ) from exc
    bindings = {}
    for relative in _freeze_a1_closure_paths():
        path = _resolve(root, relative)
        if not path.is_file():
            raise Pilot3PhaseAError(f"development gate closure path is missing: {relative}")
        if not _git_path_committed_and_clean(root, relative):
            raise Pilot3PhaseAError(
                f"development gate closure path is not committed and clean: {relative}"
            )
        bindings[relative] = hash_file(path)
    return bindings


def _append_jsonl_fsync(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(row)) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError("short write while appending durable JSONL")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _ensure_durable_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    try:
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


def _read_existing_rows(path: Path, key: str) -> Dict[str, Dict[str, Any]]:
    if not path.is_file():
        return {}
    rows = read_jsonl(path)
    result: Dict[str, Dict[str, Any]] = {}
    for raw in rows:
        if not isinstance(raw, dict) or not raw.get(key):
            raise Pilot3PhaseAError(f"malformed append-only row in {path}")
        value = str(raw[key])
        if value in result:
            raise Pilot3PhaseAError(f"duplicate {key}={value} in {path}")
        result[value] = dict(raw)
    return result


def _phase_ledger_path(
    root: Path, config: Mapping[str, Any], phase: str, kind: str
) -> Path:
    if phase not in {"development", "external"}:
        raise ValueError("ledger phase must be development or external")
    if kind not in {
        "acquisition_intents",
        "acquisition_attempts",
        "acquisitions",
        "features",
    }:
        raise ValueError("unknown Phase-A ledger kind")
    return _resolve(root, config["paths"][f"{phase}_{kind}"])


def _combined_phase_rows(
    root: Path,
    config: Mapping[str, Any],
    kind: str,
    key: str,
    phases: Iterable[str],
) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for phase in phases:
        rows = _read_existing_rows(_phase_ledger_path(root, config, phase, kind), key)
        overlap = set(result) & set(rows)
        if overlap:
            raise Pilot3PhaseAError(
                f"{kind} identity appears in development and external ledgers: {sorted(overlap)}"
            )
        result.update(rows)
    return result


def _http_request_headers(source_url: str) -> Dict[str, str]:
    return {
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": source_url,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
        ),
    }


def _acquisition_response_limit(config: Mapping[str, Any]) -> int:
    policy = config.get("acquisition_http")
    if not isinstance(policy, Mapping):
        raise Pilot3PhaseAError("Phase-A HTTP acquisition policy is missing")
    maximum = policy.get("max_response_bytes")
    if type(maximum) is not int or maximum <= 0:
        raise Pilot3PhaseAError("Phase-A HTTP response-byte limit is invalid")
    if policy.get("trust_env") is not False:
        raise Pilot3PhaseAError("Phase-A HTTP acquisition must ignore ambient proxies")
    return maximum


def _declared_response_length(response: httpx.Response) -> Optional[int]:
    value = response.headers.get("content-length")
    if value is None:
        return None
    normalized = value.strip()
    if not normalized.isascii() or not normalized.isdecimal():
        raise ValueError("response has an invalid Content-Length header")
    return int(normalized)


def _http_attempt_start(
    *,
    phase: str,
    intent: Mapping[str, Any],
    attempt_number: int,
    event_sequence: int,
    previous_event_sha256: Optional[str],
    max_response_bytes: int,
) -> Dict[str, Any]:
    headers = _http_request_headers(str(intent["source_url"]))
    request_identity = {
        "method": "GET",
        "request_url": intent["image_url"],
        "source_url": intent["source_url"],
        "request_headers": headers,
        "follow_redirects": True,
        "timeout_seconds": 120.0,
        "max_response_bytes": max_response_bytes,
        "trust_env": False,
    }
    attempt_identity = {
        "phase": phase,
        "canonical_work_id": intent["canonical_work_id"],
        "intent_id": intent["intent_id"],
        "intent_sha256": stable_hash(intent),
        "attempt_number": attempt_number,
        "request_identity_sha256": stable_hash(request_identity),
    }
    payload = {
        "record_type": "pilot3_real_acquisition_http_attempt_start",
        "schema_version": HTTP_ATTEMPT_SCHEMA,
        "event_type": "start",
        "event_sequence": event_sequence,
        "previous_event_sha256": previous_event_sha256,
        **attempt_identity,
        "attempt_id": f"p3-real-http-{stable_hash(attempt_identity)[:24]}",
        **request_identity,
    }
    return _self_hash(payload, "event_sha256")


def _http_attempt_terminal(
    start: Mapping[str, Any],
    *,
    outcome: str,
    retryable: bool,
    http_status: Optional[int] = None,
    content_type: Optional[str] = None,
    resolved_url: Optional[str] = None,
    etag: Optional[str] = None,
    last_modified: Optional[str] = None,
    response_payload: Optional[bytes] = None,
    observed_response_byte_count: Optional[int] = None,
    observed_response_sha256: Optional[str] = None,
    declared_content_length: Optional[int] = None,
    response_complete: Optional[bool] = None,
    response_size_limit_source: Optional[str] = None,
    raw_path: Optional[str] = None,
    exception_class: Optional[str] = None,
    exception_family: Optional[str] = None,
    redirect_chain: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    if response_payload is not None:
        if (
            observed_response_byte_count is not None
            or observed_response_sha256 is not None
        ):
            raise ValueError("response payload and observed response evidence are exclusive")
        response_byte_count: Optional[int] = len(response_payload)
        response_sha256: Optional[str] = hash_bytes(response_payload)
    else:
        response_byte_count = observed_response_byte_count
        response_sha256 = observed_response_sha256
    payload = {
        "record_type": "pilot3_real_acquisition_http_attempt_terminal",
        "schema_version": HTTP_ATTEMPT_SCHEMA,
        "event_type": "terminal",
        "event_sequence": int(start["event_sequence"]) + 1,
        "previous_event_sha256": start["event_sha256"],
        "phase": start["phase"],
        "canonical_work_id": start["canonical_work_id"],
        "intent_id": start["intent_id"],
        "intent_sha256": start["intent_sha256"],
        "attempt_number": start["attempt_number"],
        "attempt_id": start["attempt_id"],
        "start_event_sha256": start["event_sha256"],
        "outcome": outcome,
        "retryable": retryable,
        "http_status": http_status,
        "content_type": content_type,
        "resolved_url": resolved_url,
        "etag": etag,
        "last_modified": last_modified,
        "redirect_chain": [dict(item) for item in redirect_chain],
        "declared_content_length": declared_content_length,
        "response_complete": response_complete,
        "response_size_limit_source": response_size_limit_source,
        "response_byte_count": response_byte_count,
        "response_sha256": response_sha256,
        "raw_path": raw_path,
        "exception_class": exception_class,
        "exception_family": exception_family,
    }
    return _self_hash(payload, "event_sha256")


def _http_status_retryable(status: int) -> bool:
    return status in {408, 409, 425, 429} or 500 <= status <= 599


def _validate_http_attempt_terminal(
    root: Path,
    config: Mapping[str, Any],
    start: Mapping[str, Any],
    terminal: Mapping[str, Any],
) -> None:
    required = {
        "record_type",
        "schema_version",
        "event_type",
        "event_sequence",
        "previous_event_sha256",
        "phase",
        "canonical_work_id",
        "intent_id",
        "intent_sha256",
        "attempt_number",
        "attempt_id",
        "start_event_sha256",
        "outcome",
        "retryable",
        "http_status",
        "content_type",
        "resolved_url",
        "etag",
        "last_modified",
        "redirect_chain",
        "declared_content_length",
        "response_complete",
        "response_size_limit_source",
        "response_byte_count",
        "response_sha256",
        "raw_path",
        "exception_class",
        "exception_family",
        "event_sha256",
    }
    if set(terminal) != required:
        raise Pilot3PhaseAError("HTTP attempt terminal has a stale field set")
    verify_self_hash(terminal, "event_sha256")
    if (
        terminal.get("record_type")
        != "pilot3_real_acquisition_http_attempt_terminal"
        or terminal.get("schema_version") != HTTP_ATTEMPT_SCHEMA
        or terminal.get("event_type") != "terminal"
        or terminal.get("event_sequence") != int(start.get("event_sequence", 0)) + 1
        or terminal.get("previous_event_sha256") != start.get("event_sha256")
        or terminal.get("start_event_sha256") != start.get("event_sha256")
        or any(
            terminal.get(key) != start.get(key)
            for key in (
                "phase",
                "canonical_work_id",
                "intent_id",
                "intent_sha256",
                "attempt_number",
                "attempt_id",
            )
        )
        or type(terminal.get("retryable")) is not bool
    ):
        raise Pilot3PhaseAError("HTTP attempt terminal does not bind its durable start")
    outcome = terminal.get("outcome")
    status = terminal.get("http_status")
    response_count = terminal.get("response_byte_count")
    response_sha = terminal.get("response_sha256")
    declared_content_length = terminal.get("declared_content_length")
    response_complete = terminal.get("response_complete")
    response_size_limit_source = terminal.get("response_size_limit_source")
    redirects = terminal.get("redirect_chain")
    if not isinstance(redirects, list) or any(
        not isinstance(item, Mapping)
        or set(item) != {"status", "url"}
        or type(item.get("status")) is not int
        or not 300 <= int(item.get("status", 0)) <= 399
        or not isinstance(item.get("url"), str)
        or not item.get("url")
        for item in redirects
    ):
        raise Pilot3PhaseAError("HTTP attempt redirect evidence is malformed")
    if any(
        value is not None and not isinstance(value, str)
        for value in (terminal.get("etag"), terminal.get("last_modified"))
    ):
        raise Pilot3PhaseAError("HTTP attempt response header evidence is malformed")
    if declared_content_length is not None and (
        type(declared_content_length) is not int or declared_content_length < 0
    ):
        raise Pilot3PhaseAError("HTTP attempt Content-Length evidence is malformed")
    if response_complete is not None and type(response_complete) is not bool:
        raise Pilot3PhaseAError("HTTP attempt response-completion evidence is malformed")
    if response_size_limit_source not in {None, "content_length", "streamed_bytes"}:
        raise Pilot3PhaseAError("HTTP attempt size-limit evidence is malformed")
    has_response_metadata = (
        type(status) is int
        and 100 <= status <= 599
        and isinstance(terminal.get("content_type"), str)
        and isinstance(terminal.get("resolved_url"), str)
        and bool(terminal.get("resolved_url"))
    )
    has_complete_response = (
        type(response_count) is int
        and response_count >= 0
        and _is_sha256(response_sha)
        and has_response_metadata
        and response_complete is True
        and response_size_limit_source is None
    )
    if outcome == "success":
        content_type = terminal.get("content_type")
        raw_value = terminal.get("raw_path")
        if (
            terminal.get("retryable") is not False
            or not has_complete_response
            or not 200 <= int(status) <= 299
            or not isinstance(content_type, str)
            or not content_type.startswith("image/")
            or not isinstance(raw_value, str)
            or terminal.get("exception_class") is not None
            or terminal.get("exception_family") is not None
        ):
            raise Pilot3PhaseAError("successful HTTP attempt evidence is malformed")
        raw_sha = str(response_sha)
        expected_path = (
            _resolve(root, config["paths"]["raw_dir"])
            / raw_sha[:2]
            / f"{raw_sha}.bin"
        )
        if raw_value != _portable(expected_path, root):
            raise Pilot3PhaseAError("successful HTTP attempt uses a non-canonical raw path")
        if (
            not expected_path.is_file()
            or expected_path.stat().st_size != response_count
            or hash_file(expected_path) != raw_sha
        ):
            raise Pilot3PhaseAError("successful HTTP attempt raw bytes are missing or stale")
    elif outcome == "http_status_failure":
        if (
            not has_complete_response
            or 200 <= int(status) <= 299
            or terminal.get("retryable") is not _http_status_retryable(int(status))
            or terminal.get("raw_path") is not None
            or terminal.get("exception_class") is not None
            or terminal.get("exception_family") is not None
        ):
            raise Pilot3PhaseAError("HTTP status-failure evidence is malformed")
    elif outcome == "invalid_content_type":
        content_type = terminal.get("content_type")
        if (
            not has_complete_response
            or not 200 <= int(status) <= 299
            or terminal.get("retryable") is not True
            or not isinstance(content_type, str)
            or content_type.startswith("image/")
            or terminal.get("raw_path") is not None
            or terminal.get("exception_class") is not None
            or terminal.get("exception_family") is not None
        ):
            raise Pilot3PhaseAError("invalid-content-type attempt evidence is malformed")
    elif outcome == "response_too_large":
        maximum = start.get("max_response_bytes")
        header_limit = (
            response_size_limit_source == "content_length"
            and type(maximum) is int
            and type(declared_content_length) is int
            and declared_content_length > maximum
            and response_count == 0
            and response_sha == hash_bytes(b"")
        )
        streamed_limit = (
            response_size_limit_source == "streamed_bytes"
            and type(maximum) is int
            and type(response_count) is int
            and response_count > maximum
            and _is_sha256(response_sha)
            and (
                declared_content_length is None
                or declared_content_length <= maximum
            )
        )
        if (
            terminal.get("retryable") is not False
            or not has_response_metadata
            or response_complete is not False
            or not (header_limit or streamed_limit)
            or terminal.get("raw_path") is not None
            or terminal.get("exception_class") is not None
            or terminal.get("exception_family") is not None
        ):
            raise Pilot3PhaseAError("response-too-large attempt evidence is malformed")
    elif outcome == "exception_failure":
        if (
            any(
                terminal.get(key) is not None
                for key in (
                    "http_status",
                    "content_type",
                    "resolved_url",
                    "etag",
                    "last_modified",
                    "declared_content_length",
                    "response_complete",
                    "response_size_limit_source",
                    "response_byte_count",
                    "response_sha256",
                    "raw_path",
                )
            )
            or redirects != []
            or not isinstance(terminal.get("exception_class"), str)
            or not terminal.get("exception_class")
            or terminal.get("exception_family")
            not in {"httpx.TransportError", "non_transport_exception"}
            or terminal.get("retryable")
            is not (terminal.get("exception_family") == "httpx.TransportError")
        ):
            raise Pilot3PhaseAError("HTTP exception attempt evidence is malformed")
    else:
        raise Pilot3PhaseAError(f"unknown HTTP attempt outcome: {outcome}")


def _read_canonical_http_attempt_events(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    payload = path.read_bytes()
    if not payload:
        return []
    if not payload.endswith(b"\n"):
        raise Pilot3PhaseAError("HTTP attempt ledger has a torn final row")
    if b"\r" in payload:
        raise Pilot3PhaseAError("HTTP attempt ledger contains non-canonical newlines")
    events: List[Dict[str, Any]] = []
    for index, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            raise Pilot3PhaseAError("HTTP attempt ledger contains a blank row")
        try:
            decoded = raw_line.decode("utf-8")
            raw = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError(
                f"HTTP attempt event {index} is not canonical JSON"
            ) from exc
        if not isinstance(raw, dict) or canonical_json(raw) != decoded:
            raise Pilot3PhaseAError(
                f"HTTP attempt event {index} is not a canonical JSON object"
            )
        events.append(raw)
    return events


def _verified_http_attempt_histories(
    root: Path,
    config: Mapping[str, Any],
    phase: str,
    intents: Mapping[str, Mapping[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Verify the append-only start/terminal journal and return histories by intent."""

    path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    histories: Dict[str, List[Dict[str, Any]]] = {
        intent_id: [] for intent_id in intents
    }
    active: Optional[Dict[str, Any]] = None
    previous_event_sha256: Optional[str] = None
    for index, event in enumerate(_read_canonical_http_attempt_events(path), start=1):
        if (
            event.get("event_sequence") != index
            or event.get("previous_event_sha256") != previous_event_sha256
        ):
            raise Pilot3PhaseAError("HTTP attempt ledger chain is stale or reordered")
        event_type = event.get("event_type")
        if event_type == "start":
            if active is not None:
                raise Pilot3PhaseAError(
                    "HTTP attempt ledger contains an indeterminate start without terminal"
                )
            intent_id = event.get("intent_id")
            intent = intents.get(str(intent_id))
            if intent is None or intent.get("acquisition_route") != "network":
                raise Pilot3PhaseAError("HTTP attempt start is not bound to a network intent")
            history = histories[str(intent_id)]
            attempt_number = len(history) // 2 + 1
            expected = _http_attempt_start(
                phase=phase,
                intent=intent,
                attempt_number=attempt_number,
                event_sequence=index,
                previous_event_sha256=previous_event_sha256,
                max_response_bytes=_acquisition_response_limit(config),
            )
            if event != expected:
                raise Pilot3PhaseAError("HTTP attempt start is stale or out of sequence")
            if history:
                previous = history[-1]
                if (
                    previous.get("outcome") == "success"
                    or previous.get("retryable") is False
                ):
                    raise Pilot3PhaseAError("HTTP attempt exists after a terminal outcome")
            if attempt_number > MAX_HTTP_ATTEMPTS:
                raise Pilot3PhaseAError("HTTP attempt ledger exceeds the retry limit")
            active = event
        elif event_type == "terminal":
            if active is None:
                raise Pilot3PhaseAError("HTTP attempt terminal has no preceding start")
            _validate_http_attempt_terminal(root, config, active, event)
            intent_id = str(active["intent_id"])
            histories[intent_id].extend((active, event))
            active = None
        else:
            raise Pilot3PhaseAError(f"HTTP attempt event {index} has an unknown type")
        previous_event_sha256 = str(event.get("event_sha256", ""))
    if active is not None:
        raise Pilot3PhaseAError(
            "HTTP attempt ledger contains an indeterminate start without terminal"
        )
    return histories


def _response_evidence_from_terminal(terminal: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "http_status": terminal["http_status"],
        "content_type": terminal["content_type"],
        "etag": terminal["etag"],
        "last_modified": terminal["last_modified"],
        "resolved_url": terminal["resolved_url"],
        "technical_attempt_count": terminal["attempt_number"],
        "successful_http_attempt_id": terminal["attempt_id"],
        "successful_http_terminal_event_sha256": terminal["event_sha256"],
    }


def _download_image_bytes(
    root: Path,
    config: Mapping[str, Any],
    phase: str,
    intent: Mapping[str, Any],
) -> Tuple[bytes, Dict[str, Any], List[Dict[str, Any]]]:
    """Resume or execute a network GET with durable evidence for every attempt."""

    attempt_path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    _ensure_durable_file(attempt_path)
    intents = _read_existing_rows(
        _phase_ledger_path(root, config, phase, "acquisition_intents"), "intent_id"
    )
    if intents.get(str(intent["intent_id"])) != dict(intent):
        raise Pilot3PhaseAError("network acquisition intent is missing or stale")
    history = _verified_http_attempt_histories(root, config, phase, intents)[
        str(intent["intent_id"])
    ]
    all_events = _read_canonical_http_attempt_events(attempt_path)
    if history and history[-1]["outcome"] == "success":
        terminal = history[-1]
        payload = _resolve(root, str(terminal["raw_path"])).read_bytes()
        return payload, _response_evidence_from_terminal(terminal), history
    if history and history[-1]["retryable"] is False:
        raise Pilot3PhaseAError(
            "museum image acquisition has a recorded non-retryable terminal failure"
        )
    completed_attempts = len(history) // 2
    if completed_attempts >= MAX_HTTP_ATTEMPTS:
        raise Pilot3PhaseAError(
            f"museum image acquisition exhausted {MAX_HTTP_ATTEMPTS} recorded attempts"
        )
    max_response_bytes = _acquisition_response_limit(config)
    headers = _http_request_headers(str(intent["source_url"]))
    for attempt_number in range(completed_attempts + 1, MAX_HTTP_ATTEMPTS + 1):
        start = _http_attempt_start(
            phase=phase,
            intent=intent,
            attempt_number=attempt_number,
            event_sequence=len(all_events) + 1,
            previous_event_sha256=(
                str(all_events[-1]["event_sha256"]) if all_events else None
            ),
            max_response_bytes=max_response_bytes,
        )
        _append_jsonl_fsync(attempt_path, start)
        all_events.append(start)
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=120.0,
                headers=headers,
                trust_env=False,
            ) as client:
                with client.stream("GET", str(intent["image_url"])) as response:
                    content_type = (
                        response.headers.get("content-type", "")
                        .split(";", 1)[0]
                        .strip()
                    )
                    declared_content_length = _declared_response_length(response)
                    response_status = int(response.status_code)
                    response_metadata = {
                        "http_status": response_status,
                        "content_type": content_type,
                        "resolved_url": str(response.url),
                        "etag": response.headers.get("etag"),
                        "last_modified": response.headers.get("last-modified"),
                        "redirect_chain": [
                            {"status": int(item.status_code), "url": str(item.url)}
                            for item in response.history
                        ],
                        "declared_content_length": declared_content_length,
                    }
                    response_digest = hashlib.sha256()
                    response_byte_count = 0
                    response_chunks: List[bytes] = []
                    response_size_limit_source: Optional[str] = None
                    if (
                        declared_content_length is not None
                        and declared_content_length > max_response_bytes
                    ):
                        response_size_limit_source = "content_length"
                    else:
                        for chunk in response.iter_bytes(
                            chunk_size=HTTP_STREAM_CHUNK_BYTES
                        ):
                            if not chunk:
                                continue
                            response_digest.update(chunk)
                            response_byte_count += len(chunk)
                            if response_byte_count > max_response_bytes:
                                response_size_limit_source = "streamed_bytes"
                                break
                            response_chunks.append(chunk)
                    payload = (
                        b"".join(response_chunks)
                        if response_size_limit_source is None
                        else b""
                    )
        except Exception as exc:
            retryable = isinstance(exc, httpx.TransportError)
            terminal = _http_attempt_terminal(
                start,
                outcome="exception_failure",
                retryable=retryable,
                exception_class=type(exc).__name__,
                exception_family=(
                    "httpx.TransportError"
                    if retryable
                    else "non_transport_exception"
                ),
            )
            _append_jsonl_fsync(attempt_path, terminal)
            history.extend((start, terminal))
            all_events.append(terminal)
            if retryable and attempt_number < MAX_HTTP_ATTEMPTS:
                time.sleep(float(2 ** (attempt_number - 1)))
                continue
            raise Pilot3PhaseAError(
                "museum image acquisition ended with a recorded exception: "
                + type(exc).__name__
            ) from exc
        if response_size_limit_source is not None:
            terminal = _http_attempt_terminal(
                start,
                outcome="response_too_large",
                retryable=False,
                observed_response_byte_count=response_byte_count,
                observed_response_sha256=response_digest.hexdigest(),
                response_complete=False,
                response_size_limit_source=response_size_limit_source,
                **response_metadata,
            )
            _append_jsonl_fsync(attempt_path, terminal)
            history.extend((start, terminal))
            all_events.append(terminal)
            _validate_http_attempt_terminal(root, config, start, terminal)
            raise Pilot3PhaseAError(
                "museum image acquisition response exceeds the frozen byte limit"
            )
        response_fields = {
            **response_metadata,
            "response_payload": payload,
            "response_complete": True,
        }
        if not 200 <= response_status <= 299:
            retryable = _http_status_retryable(response_status)
            terminal = _http_attempt_terminal(
                start,
                outcome="http_status_failure",
                retryable=retryable,
                **response_fields,
            )
            _append_jsonl_fsync(attempt_path, terminal)
            history.extend((start, terminal))
            all_events.append(terminal)
            if retryable and attempt_number < MAX_HTTP_ATTEMPTS:
                time.sleep(float(2 ** (attempt_number - 1)))
                continue
            raise Pilot3PhaseAError(
                f"museum image acquisition ended with HTTP {response_status}"
            )
        if not content_type.startswith("image/"):
            terminal = _http_attempt_terminal(
                start,
                outcome="invalid_content_type",
                retryable=True,
                **response_fields,
            )
            _append_jsonl_fsync(attempt_path, terminal)
            history.extend((start, terminal))
            all_events.append(terminal)
            if attempt_number < MAX_HTTP_ATTEMPTS:
                time.sleep(float(2 ** (attempt_number - 1)))
                continue
            raise Pilot3PhaseAError(
                "museum image acquisition exhausted retries on non-image responses"
            )
        raw_sha = hash_bytes(payload)
        raw_path = (
            _resolve(root, config["paths"]["raw_dir"])
            / raw_sha[:2]
            / f"{raw_sha}.bin"
        )
        if raw_path.exists() and hash_file(raw_path) != raw_sha:
            raise Pilot3PhaseAError(f"raw content-address collision at {raw_path}")
        if not raw_path.exists():
            _atomic_bytes(raw_path, payload)
        terminal = _http_attempt_terminal(
            start,
            outcome="success",
            retryable=False,
            raw_path=_portable(raw_path, root),
            **response_fields,
        )
        _append_jsonl_fsync(attempt_path, terminal)
        history.extend((start, terminal))
        all_events.append(terminal)
        _validate_http_attempt_terminal(root, config, start, terminal)
        return payload, _response_evidence_from_terminal(terminal), history
    raise Pilot3PhaseAError("museum image acquisition reached an unreachable retry state")


def _executed_preprocessing_config(config: Mapping[str, Any]) -> Pilot2PreprocessingConfig:
    """Require the declarative Phase-A transform to equal the executed implementation."""

    runtime = Pilot2PreprocessingConfig()
    expected = runtime.model_dump(mode="json")
    expected["protocol_version"] = "pilot3-common-lossless-png-v1"
    if config.get("common_preprocessing") != expected:
        raise Pilot3PhaseAError(
            "Phase-A common preprocessing does not equal the executed PNG transform"
        )
    return runtime


def _decode_and_normalize(
    payload: bytes,
    config: Mapping[str, Any],
    *,
    expected_width: Optional[int] = None,
    expected_height: Optional[int] = None,
) -> Tuple[Dict[str, Any], bytes]:
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            decoded_width, decoded_height = image.size
            decoded_format = str(image.format or "unknown").casefold()
            decoded_mode = image.mode
            domain = config["input_domain"]
            if (expected_width is None) != (expected_height is None):
                raise Pilot3PhaseAError(
                    "delivered dimension enforcement requires both width and height"
                )
            checks = {
                "width_strictly_greater_than_410": (
                    decoded_width > int(domain["decoded_width_strict_min"])
                ),
                "height_strictly_greater_than_410": (
                    decoded_height > int(domain["decoded_height_strict_min"])
                ),
                "long_short_aspect_strictly_below_2": (
                    max(decoded_width, decoded_height) / min(decoded_width, decoded_height)
                    < float(domain["long_to_short_aspect_strict_max"])
                ),
                "released_code_area_predicate": (
                    decoded_width * decoded_height > 410 * 410
                ),
            }
            if expected_width is not None and expected_height is not None:
                checks["matches_frozen_delivery_dimensions"] = (
                    decoded_width == expected_width and decoded_height == expected_height
                )
            if not all(checks.values()):
                raise Pilot3PhaseAError(
                    f"decoded museum image is outside the frozen Kim intersection: {checks}"
                )
            normalized, normalized_size = common_png_bytes(
                image,
                _executed_preprocessing_config(config),
            )
    except Pilot3PhaseAError:
        raise
    except Exception as exc:
        raise Pilot3PhaseAError(f"cannot decode museum image bytes: {exc}") from exc
    return {
        "decoded_width": decoded_width,
        "decoded_height": decoded_height,
        "decoded_format": decoded_format,
        "decoded_mode": decoded_mode,
        "domain_checks": checks,
        "normalized_width": normalized_size[0],
        "normalized_height": normalized_size[1],
    }, normalized


def _portable(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _acquisition_intent(
    split: Mapping[str, Any],
    *,
    acquisition_route: str,
    phase_a_config_file_sha256: str,
    external_protocol_result_sha256: Optional[str],
    external_unseal_receipt_sha256: Optional[str],
) -> Dict[str, Any]:
    payload = {
        "record_type": "pilot3_real_acquisition_intent",
        "schema_version": "1.0",
        "canonical_work_id": split["canonical_work_id"],
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
        "acquisition_route": acquisition_route,
        "phase_a_config_file_sha256": phase_a_config_file_sha256,
        "external_protocol_result_sha256": external_protocol_result_sha256,
        "external_unseal_receipt_sha256": external_unseal_receipt_sha256,
    }
    return {
        **payload,
        "intent_id": f"p3-real-intent-{stable_hash(payload)[:24]}",
    }


def _verify_acquisition_http_history(
    row: Mapping[str, Any],
    root: Path,
    config: Mapping[str, Any],
    expected_intent: Mapping[str, Any],
) -> None:
    phase = (
        "external" if row.get("partition") == EXTERNAL_PARTITION else "development"
    )
    intent_path = _phase_ledger_path(root, config, phase, "acquisition_intents")
    attempts_path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    if not attempts_path.is_file():
        raise Pilot3PhaseAError(f"{phase} HTTP attempt ledger is missing")
    intents = _read_existing_rows(intent_path, "intent_id")
    by_work: Dict[str, Dict[str, Any]] = {}
    for intent in intents.values():
        work_id = str(intent.get("canonical_work_id", ""))
        if not work_id or work_id in by_work:
            raise Pilot3PhaseAError("acquisition intents are duplicate or lack work identity")
        by_work[work_id] = intent
    work_id = str(row["canonical_work_id"])
    if (
        by_work.get(work_id) != dict(expected_intent)
        or row.get("intent_id") != expected_intent.get("intent_id")
    ):
        raise Pilot3PhaseAError("acquisition does not bind its exact durable intent")
    history = _verified_http_attempt_histories(root, config, phase, intents)[
        str(expected_intent["intent_id"])
    ]
    starts = history[::2]
    successful_terminal: Optional[Mapping[str, Any]] = None
    if expected_intent.get("acquisition_route") == "network":
        if not history or history[-1].get("outcome") != "success":
            raise Pilot3PhaseAError("network acquisition lacks a successful HTTP history")
        successful_terminal = history[-1]
        if (
            successful_terminal.get("raw_path") != row.get("raw_path")
            or successful_terminal.get("response_sha256") != row.get("raw_sha256")
            or successful_terminal.get("response_byte_count")
            != row.get("raw_byte_count")
            or row.get("response_evidence")
            != _response_evidence_from_terminal(successful_terminal)
        ):
            raise Pilot3PhaseAError("network acquisition disagrees with HTTP success evidence")
    elif expected_intent.get("acquisition_route") == "prior_local_reproduction":
        if history:
            raise Pilot3PhaseAError("prior-local acquisition unexpectedly has HTTP attempts")
        response = row.get("response_evidence")
        if not isinstance(response, Mapping) or response.get("technical_attempt_count") != 0:
            raise Pilot3PhaseAError("prior-local acquisition has stale response evidence")
    else:
        raise Pilot3PhaseAError("acquisition intent has an unknown route")
    expected_binding = {
        "http_attempt_ids": [str(start["attempt_id"]) for start in starts],
        "http_attempt_count": len(starts),
        "http_attempt_event_count": len(history),
        "http_attempt_history_semantic_sha256": stable_hash(history),
        "successful_http_attempt_id": (
            successful_terminal["attempt_id"] if successful_terminal is not None else None
        ),
        "successful_http_terminal_event_sha256": (
            successful_terminal["event_sha256"]
            if successful_terminal is not None
            else None
        ),
    }
    if any(row.get(key) != value for key, value in expected_binding.items()):
        raise Pilot3PhaseAError("acquisition HTTP-attempt binding is stale")


def _verify_existing_acquisition(
    row: Mapping[str, Any],
    root: Path,
    split: Mapping[str, Any],
    config: Mapping[str, Any],
    external_unseal_token: Optional[str],
    *,
    expected_external_receipt_sha256: Optional[str] = None,
) -> None:
    verify_self_hash(row, "record_sha256")
    expected_identity = {
        key: split[key]
        for key in (
            "canonical_work_id",
            "artist_id",
            "asset_provider",
            "collection_block_id",
            "delivery_height",
            "delivery_width",
            "museum_accession",
            "source_id",
            "source_object_id",
            "partition",
            "image_url",
            "source_url",
        )
    }
    if any(row.get(key) != value for key, value in expected_identity.items()):
        raise Pilot3PhaseAError("existing acquisition identity disagrees with split manifest")
    expected_config_sha = hash_file(_resolve(root, DEFAULT_CONFIG))
    if row.get("phase_a_config_file_sha256") != expected_config_sha:
        raise Pilot3PhaseAError("existing acquisition binds a stale Phase-A config")
    expected_token = (
        external_unseal_token if split["partition"] == EXTERNAL_PARTITION else None
    )
    if row.get("external_protocol_result_sha256") != expected_token:
        raise Pilot3PhaseAError("existing acquisition binds a stale external-unseal token")
    expected_receipt = None
    if split["partition"] == EXTERNAL_PARTITION:
        if expected_external_receipt_sha256 is None:
            protocol = require_external_unseal(root, config, external_unseal_token)
            expected_receipt = verify_external_unseal_receipt(root, config, protocol)[
                "receipt_sha256"
            ]
        elif not _is_sha256(expected_external_receipt_sha256):
            raise Pilot3PhaseAError("expected external-unseal receipt hash is malformed")
        else:
            expected_receipt = expected_external_receipt_sha256
    if row.get("external_unseal_receipt_sha256") != expected_receipt:
        raise Pilot3PhaseAError("existing acquisition binds a stale external-unseal receipt")
    expected_intent = _acquisition_intent(
        split,
        acquisition_route=str(row.get("acquisition_route", "")),
        phase_a_config_file_sha256=expected_config_sha,
        external_protocol_result_sha256=expected_token,
        external_unseal_receipt_sha256=expected_receipt,
    )
    _verify_acquisition_http_history(row, root, config, expected_intent)
    if row.get("common_preprocessing_config_sha256") != stable_hash(
        config["common_preprocessing"]
    ):
        raise Pilot3PhaseAError("existing acquisition binds stale preprocessing")
    if (
        row.get("decoded_width") != split.get("delivery_width")
        or row.get("decoded_height") != split.get("delivery_height")
    ):
        raise Pilot3PhaseAError(
            "existing acquisition disagrees with frozen delivered dimensions"
        )
    for path_key, hash_key in (
        ("raw_path", "raw_sha256"),
        ("normalized_path", "normalized_sha256"),
    ):
        path = _resolve(root, str(row[path_key]))
        if not path.is_file() or hash_file(path) != row.get(hash_key):
            raise Pilot3PhaseAError(f"existing acquisition payload is missing or stale: {path}")
    if not all(bool(value) for value in row.get("domain_checks", {}).values()):
        raise Pilot3PhaseAError("existing acquisition violates the frozen input domain")


@contextmanager
def _acquisition_phase_lock(root: Path, phase: str) -> Iterator[None]:
    if phase not in {"development", "external"}:
        raise ValueError("phase must be development or external")
    lock_path = _resolve(root, f"artifacts/pilot_3/{phase}_acquisition.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            raise Pilot3PhaseAError(
                f"another {phase} acquisition process is already running"
            ) from exc
        yield
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def acquire_real_partition(
    root: Path,
    *,
    phase: str,
    config_path: Path = DEFAULT_CONFIG,
    external_unseal_token: Optional[str] = None,
    _transaction_capability: object | None = None,
) -> List[Dict[str, Any]]:
    """Acquire one Phase-A partition under an exclusive crash-recoverable lock."""

    root = Path(root).expanduser().resolve()
    with _acquisition_phase_lock(root, phase):
        return _acquire_real_partition_locked(
            root,
            phase=phase,
            config_path=config_path,
            external_unseal_token=external_unseal_token,
            _transaction_capability=_transaction_capability,
        )


def _acquire_real_partition_locked(
    root: Path,
    *,
    phase: str,
    config_path: Path = DEFAULT_CONFIG,
    external_unseal_token: Optional[str] = None,
    _transaction_capability: object | None = None,
) -> List[Dict[str, Any]]:
    """Acquire development bytes or the once-unsealed external source.

    ``phase`` must be ``development`` or ``external``.  The latter requires the exact
    P3-T07 self-hash and a still-current committed protocol closure.
    """

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root, config_path)
    external_receipt_sha256: Optional[str] = None
    if phase not in {"development", "external"}:
        raise ValueError("phase must be development or external")
    if phase == "external":
        if _transaction_capability is not _EXTERNAL_TRANSACTION_CAPABILITY:
            raise Pilot3PhaseAError(
                "external acquisition is available only inside unseal_and_validate_external"
            )
        protocol = require_external_unseal(root, config, external_unseal_token)
        external_receipt_sha256 = verify_external_unseal_receipt(
            root, config, protocol
        )["receipt_sha256"]
        allowed = {EXTERNAL_PARTITION}
    else:
        require_development_freeze(root)
        if external_unseal_token is not None:
            raise Pilot3PhaseAError("development acquisition does not accept an unseal token")
        allowed = set(DEVELOPMENT_PARTITIONS)

    splits = [row for row in load_real_splits(root, config) if row["partition"] in allowed]
    expected_count = 12 if phase == "external" else 40
    if len(splits) != expected_count:
        raise Pilot3PhaseAError(
            f"{phase} acquisition expected {expected_count} rows, found {len(splits)}"
        )

    paths = config["paths"]
    intent_path = _phase_ledger_path(root, config, phase, "acquisition_intents")
    attempt_path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    acquisition_path = _phase_ledger_path(root, config, phase, "acquisitions")
    _ensure_durable_file(attempt_path)
    intents = _read_existing_rows(intent_path, "intent_id")
    acquisitions = _read_existing_rows(acquisition_path, "canonical_work_id")
    config_sha = hash_file(_resolve(root, config_path))
    split_work_ids = {str(row["canonical_work_id"]) for row in splits}
    if not set(acquisitions).issubset(split_work_ids):
        raise Pilot3PhaseAError(f"{phase} acquisition ledger contains an unknown work")
    intents_by_work: Dict[str, Dict[str, Any]] = {}
    for existing_intent in intents.values():
        existing_work_id = str(existing_intent.get("canonical_work_id", ""))
        if (
            not existing_work_id
            or existing_work_id not in split_work_ids
            or existing_work_id in intents_by_work
        ):
            raise Pilot3PhaseAError(
                f"{phase} acquisition intents are duplicate or outside the frozen split"
            )
        intents_by_work[existing_work_id] = existing_intent
    _verified_http_attempt_histories(root, config, phase, intents)

    for split in splits:
        work_id = str(split["canonical_work_id"])
        partition = str(split["partition"])
        if work_id in acquisitions:
            _verify_existing_acquisition(
                acquisitions[work_id],
                root,
                split,
                config,
                external_unseal_token,
                expected_external_receipt_sha256=external_receipt_sha256,
            )
            continue

        acquisition_route = "network"
        prior_path: Optional[Path] = None
        prior_expected_sha: Optional[str] = None
        prior_pointer_path = split.get("prior_local_reproduction_path")
        prior_pointer_sha = split.get("prior_local_reproduction_sha256")
        prior_pointer_row_sha = split.get("prior_local_reproduction_manifest_row_sha256")
        if prior_pointer_path is not None:
            if not (
                isinstance(prior_pointer_path, str)
                and _is_sha256(prior_pointer_sha)
                and _is_sha256(prior_pointer_row_sha)
            ):
                raise Pilot3PhaseAError(f"frozen prior pointer is incomplete: {work_id}")
            candidate = _resolve(root, prior_pointer_path)
            if candidate.is_file():
                acquisition_route = "prior_local_reproduction"
                prior_path = candidate
                prior_expected_sha = str(prior_pointer_sha)

        intent = _acquisition_intent(
            split,
            acquisition_route=acquisition_route,
            phase_a_config_file_sha256=config_sha,
            external_protocol_result_sha256=(
                external_unseal_token if phase == "external" else None
            ),
            external_unseal_receipt_sha256=external_receipt_sha256,
        )
        intent_id = str(intent["intent_id"])
        existing_intent = intents_by_work.get(work_id)
        if existing_intent is not None and existing_intent != intent:
            raise Pilot3PhaseAError(
                f"durable acquisition intent changed or its route drifted: {work_id}"
            )
        if existing_intent is None:
            _append_jsonl_fsync(intent_path, intent)
            intents[intent_id] = intent
            intents_by_work[work_id] = intent

        if prior_path is not None:
            payload = prior_path.read_bytes()
            if hash_bytes(payload) != prior_expected_sha:
                raise Pilot3PhaseAError(f"prior reproduction hash is stale: {work_id}")
            response_evidence: Dict[str, Any] = {
                "prior_local_path": _portable(prior_path, root),
                "prior_manifest_path": paths["prior_reproduction_manifest"],
                "prior_manifest_row_sha256": prior_pointer_row_sha,
                "pointer_source": "frozen_pilot3_real_split_row",
                "technical_attempt_count": 0,
            }
            http_history = _verified_http_attempt_histories(
                root, config, phase, intents
            )[intent_id]
            if http_history:
                raise Pilot3PhaseAError(
                    f"prior-local acquisition has recorded HTTP attempts: {work_id}"
                )
        else:
            payload, response_evidence, http_history = _download_image_bytes(
                root, config, phase, intent
            )

        decode, normalized = _decode_and_normalize(
            payload,
            config,
            expected_width=int(split["delivery_width"]),
            expected_height=int(split["delivery_height"]),
        )
        raw_sha = hash_bytes(payload)
        normalized_sha = hash_bytes(normalized)
        raw_path = _resolve(root, paths["raw_dir"]) / raw_sha[:2] / f"{raw_sha}.bin"
        normalized_path = (
            _resolve(root, paths["normalized_dir"])
            / normalized_sha[:2]
            / f"{normalized_sha}.png"
        )
        if raw_path.exists() and hash_file(raw_path) != raw_sha:
            raise Pilot3PhaseAError(f"raw content-address collision at {raw_path}")
        if normalized_path.exists() and hash_file(normalized_path) != normalized_sha:
            raise Pilot3PhaseAError(f"PNG content-address collision at {normalized_path}")
        if not raw_path.exists():
            _atomic_bytes(raw_path, payload)
        if not normalized_path.exists():
            _atomic_bytes(normalized_path, normalized)

        record_payload = {
            "record_type": "pilot3_real_acquisition",
            "schema_version": "1.0",
            "canonical_work_id": work_id,
            "artist_id": split["artist_id"],
            "asset_provider": split["asset_provider"],
            "collection_block_id": split["collection_block_id"],
            "museum_accession": split["museum_accession"],
            "source_id": split["source_id"],
            "source_object_id": split["source_object_id"],
            "partition": partition,
            "intent_id": intent_id,
            "acquisition_route": acquisition_route,
            "image_url": split["image_url"],
            "source_url": split["source_url"],
            "delivery_width": split["delivery_width"],
            "delivery_height": split["delivery_height"],
            "phase_a_config_file_sha256": config_sha,
            "external_protocol_result_sha256": (
                external_unseal_token if phase == "external" else None
            ),
            "external_unseal_receipt_sha256": external_receipt_sha256,
            "raw_path": _portable(raw_path, root),
            "raw_sha256": raw_sha,
            "raw_byte_count": len(payload),
            "normalized_path": _portable(normalized_path, root),
            "normalized_sha256": normalized_sha,
            "normalized_byte_count": len(normalized),
            "common_preprocessing_config_sha256": stable_hash(
                config["common_preprocessing"]
            ),
            "http_attempt_ids": [
                str(event["attempt_id"])
                for event in http_history
                if event["event_type"] == "start"
            ],
            "http_attempt_count": len(http_history) // 2,
            "http_attempt_event_count": len(http_history),
            "http_attempt_history_semantic_sha256": stable_hash(http_history),
            "successful_http_attempt_id": (
                http_history[-1]["attempt_id"] if http_history else None
            ),
            "successful_http_terminal_event_sha256": (
                http_history[-1]["event_sha256"] if http_history else None
            ),
            **decode,
            "response_evidence": response_evidence,
        }
        record = _self_hash(record_payload, "record_sha256")
        _append_jsonl_fsync(acquisition_path, record)
        acquisitions[work_id] = record

    result = [acquisitions[str(row["canonical_work_id"])] for row in splits]
    for row in result:
        split = next(
            item for item in splits if item["canonical_work_id"] == row["canonical_work_id"]
        )
        _verify_existing_acquisition(
            row,
            root,
            split,
            config,
            external_unseal_token,
            expected_external_receipt_sha256=external_receipt_sha256,
        )
    return sorted(result, key=lambda row: str(row["canonical_work_id"]))


def _load_vae(root: Path, config: Mapping[str, Any]):
    section = config["a_vector"]
    pins = LearnedFormalPins(
        model_revision=section["model_revision"],
        config_sha256=section["model_config_sha256"],
        weights_sha256=section["model_weights_sha256"],
        source_repository=section["source_repository"],
        source_revision=section["source_revision"],
        model_repository=section["model_repository"],
    )
    snapshot = _resolve(root, section["model_snapshot_dir"])
    source_checkout = _resolve(root, section["source_checkout_dir"])
    return load_pinned_sd2_vae(
        snapshot,
        pins,
        config_relative_path=Path("config.json"),
        weights_relative_path=Path("diffusion_pytorch_model.safetensors"),
        source_checkout=source_checkout,
    )


def _feature_identity_payload(row: Mapping[str, Any]) -> Dict[str, Any]:
    payload = dict(row)
    for field in ("feature_id", "vector", "record_sha256"):
        payload.pop(field, None)
    return payload


def _verify_feature(
    row: Mapping[str, Any],
    acquisition: Mapping[str, Any],
    split: Mapping[str, Any],
    config: Mapping[str, Any],
    *,
    expected_runtime: Optional[Mapping[str, Any]] = None,
) -> None:
    if row.get("record_type") != "pilot3_real_a_vector" or row.get("schema_version") != "1.0":
        raise Pilot3PhaseAError("A-vector row schema is stale")
    for key in (
        "canonical_work_id",
        "artist_id",
        "asset_provider",
        "collection_block_id",
        "delivery_height",
        "delivery_width",
        "museum_accession",
        "source_id",
        "partition",
    ):
        if row.get(key) != split.get(key):
            raise Pilot3PhaseAError(f"A-vector {key} disagrees with the frozen split")
    if row.get("normalized_sha256") != acquisition.get("normalized_sha256"):
        raise Pilot3PhaseAError("feature binds a stale normalized input")
    if row.get("raw_sha256") != acquisition.get("raw_sha256"):
        raise Pilot3PhaseAError("feature binds stale raw museum bytes")
    if row.get("external_unseal_receipt_sha256") != acquisition.get(
        "external_unseal_receipt_sha256"
    ):
        raise Pilot3PhaseAError("feature binds a stale external-unseal receipt")
    section = config["a_vector"]
    if (
        row.get("feature_version") != section["feature_version"]
        or row.get("feature_config_sha256") != stable_hash(section)
    ):
        raise Pilot3PhaseAError("feature binds a stale A-vector config")
    metadata = row.get("extraction_metadata")
    if not isinstance(metadata, Mapping):
        raise Pilot3PhaseAError("feature extraction metadata is missing")
    expected_metadata = {
        "pilot3_feature_version": section["feature_version"],
        "normalized_png_sha256": acquisition["normalized_sha256"],
        "raw_museum_sha256": acquisition["raw_sha256"],
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
        raise Pilot3PhaseAError("feature extraction provenance is stale")
    if expected_runtime is not None and any(
        metadata.get(key) != value for key, value in expected_runtime.items()
    ):
        raise Pilot3PhaseAError(
            "feature extraction runtime differs from the frozen P3-T07 runtime"
        )
    if metadata.get("phase_a_config_file_sha256") != acquisition.get(
        "phase_a_config_file_sha256"
    ):
        raise Pilot3PhaseAError("feature binds a different Phase-A config than acquisition")
    vector = row.get("vector")
    if not isinstance(vector, list) or len(vector) != 16_384:
        raise Pilot3PhaseAError("A-vector has the wrong dimension")
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in vector):
        raise Pilot3PhaseAError("A-vector contains non-finite values")
    if learned_formal_vector_sha256(vector) != row.get("vector_sha256"):
        raise Pilot3PhaseAError("A-vector hash is stale")
    if row.get("feature_id") != (
        f"p3-a-vector-{stable_hash(_feature_identity_payload(row))[:24]}"
    ):
        raise Pilot3PhaseAError("A-vector feature id is stale")
    verify_self_hash(row, "record_sha256")


def extract_real_partition(
    root: Path,
    *,
    phase: str,
    config_path: Path = DEFAULT_CONFIG,
    external_unseal_token: Optional[str] = None,
    _transaction_capability: object | None = None,
) -> List[Dict[str, Any]]:
    """Extract the pinned A-vector for acquired development or external rows."""

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root, config_path)
    frozen_runtime: Optional[Mapping[str, Any]] = None
    external_receipt_sha256: Optional[str] = None
    if phase == "external":
        if _transaction_capability is not _EXTERNAL_TRANSACTION_CAPABILITY:
            raise Pilot3PhaseAError(
                "external extraction is available only inside unseal_and_validate_external"
            )
        protocol = require_external_unseal(root, config, external_unseal_token)
        frozen_runtime = protocol.get("runtime_environment")
        if not isinstance(frozen_runtime, Mapping) or not frozen_runtime:
            raise Pilot3PhaseAError("P3-T07 lacks its frozen extraction runtime")
        external_receipt_sha256 = verify_external_unseal_receipt(
            root, config, protocol
        )["receipt_sha256"]
        allowed = {EXTERNAL_PARTITION}
    elif phase == "development":
        require_development_freeze(root)
        if external_unseal_token is not None:
            raise Pilot3PhaseAError("development extraction does not accept an unseal token")
        allowed = set(DEVELOPMENT_PARTITIONS)
    else:
        raise ValueError("phase must be development or external")

    split_rows = [row for row in load_real_splits(root, config) if row["partition"] in allowed]
    acquisition_path = _phase_ledger_path(root, config, phase, "acquisitions")
    acquisitions = _read_existing_rows(acquisition_path, "canonical_work_id")
    expected_ids = {str(row["canonical_work_id"]) for row in split_rows}
    if set(acquisitions) != expected_ids:
        raise Pilot3PhaseAError(
            f"{phase} acquisition ledger is not the exact selected partition"
        )
    missing = sorted(
        str(row["canonical_work_id"])
        for row in split_rows
        if str(row["canonical_work_id"]) not in acquisitions
    )
    if missing:
        raise Pilot3PhaseAError("missing acquired images: " + ", ".join(missing))

    feature_path = _phase_ledger_path(root, config, phase, "features")
    features = _read_existing_rows(feature_path, "canonical_work_id")
    if not set(features) <= expected_ids:
        raise Pilot3PhaseAError(f"{phase} feature ledger contains an unselected work")
    loaded = None
    section = config["a_vector"]
    config_sha = hash_file(_resolve(root, config_path))
    for split in split_rows:
        work_id = str(split["canonical_work_id"])
        acquired = acquisitions[work_id]
        _verify_existing_acquisition(
            acquired,
            root,
            split,
            config,
            external_unseal_token,
            expected_external_receipt_sha256=external_receipt_sha256,
        )
        if work_id in features:
            _verify_feature(
                features[work_id],
                acquired,
                split,
                config,
                expected_runtime=frozen_runtime,
            )
            continue
        if loaded is None:
            loaded = _load_vae(root, config)
        normalized_path = _resolve(root, str(acquired["normalized_path"]))
        extraction = extract_learned_formal(
            normalized_path,
            loaded,
            policy=SOURCE_REPLICATION_POLICY,
            base_seed=int(section["base_seed"]),
            device=str(section["device"]),
        )
        vector = np.asarray(extraction.vector, dtype=np.float32)
        if vector.shape != (int(section["raw_dimension"]),) or not np.isfinite(vector).all():
            raise Pilot3PhaseAError(f"malformed extracted A-vector for {work_id}")
        metadata = dict(extraction.metadata)
        metadata.update(
            {
                "pilot3_feature_version": section["feature_version"],
                "normalized_png_sha256": acquired["normalized_sha256"],
                "raw_museum_sha256": acquired["raw_sha256"],
                "phase_a_config_file_sha256": config_sha,
            }
        )
        row_payload: Dict[str, Any] = {
            "record_type": "pilot3_real_a_vector",
            "schema_version": "1.0",
            "canonical_work_id": work_id,
            "artist_id": split["artist_id"],
            "asset_provider": split["asset_provider"],
            "collection_block_id": split["collection_block_id"],
            "museum_accession": split["museum_accession"],
            "delivery_width": split["delivery_width"],
            "delivery_height": split["delivery_height"],
            "source_id": split["source_id"],
            "partition": split["partition"],
            "normalized_sha256": acquired["normalized_sha256"],
            "raw_sha256": acquired["raw_sha256"],
            "external_unseal_receipt_sha256": acquired.get(
                "external_unseal_receipt_sha256"
            ),
            "feature_version": section["feature_version"],
            "feature_config_sha256": stable_hash(section),
            "vector_sha256": learned_formal_vector_sha256(vector),
            "extraction_metadata": metadata,
            "vector": vector.astype(float).tolist(),
        }
        row_payload["feature_id"] = (
            f"p3-a-vector-{stable_hash(_feature_identity_payload(row_payload))[:24]}"
        )
        row = _self_hash(row_payload, "record_sha256")
        _append_jsonl_fsync(feature_path, row)
        features[work_id] = row

    result = [features[str(row["canonical_work_id"])] for row in split_rows]
    for row in result:
        split = next(
            item for item in split_rows if item["canonical_work_id"] == row["canonical_work_id"]
        )
        _verify_feature(
            row,
            acquisitions[str(row["canonical_work_id"])],
            split,
            config,
            expected_runtime=frozen_runtime,
        )
    return sorted(result, key=lambda row: str(row["canonical_work_id"]))


def run_determinism_probes(
    root: Path,
    *,
    config_path: Path = DEFAULT_CONFIG,
) -> List[Dict[str, Any]]:
    """Repeat one frozen training image per artist and development source."""

    root = Path(root).expanduser().resolve()
    require_development_freeze(root)
    config = load_phase_a_config(root, config_path)
    splits = load_real_splits(root, config)
    candidates: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in splits:
        if row["partition"] != "development_training":
            continue
        key = (str(row["artist_id"]), str(row["source_id"]))
        if key not in candidates or str(row["canonical_work_id"]) < str(
            candidates[key]["canonical_work_id"]
        ):
            candidates[key] = row
    expected_keys = {
        (artist, source)
        for artist in EXPECTED_ARTISTS
        for source in DEVELOPMENT_SOURCES
    }
    if set(candidates) != expected_keys:
        raise Pilot3PhaseAError("determinism probe set is not artist/source stratified")

    acquisitions = _read_existing_rows(
        _phase_ledger_path(root, config, "development", "acquisitions"),
        "canonical_work_id",
    )
    features = _read_existing_rows(
        _phase_ledger_path(root, config, "development", "features"),
        "canonical_work_id",
    )
    probe_path = _resolve(root, config["paths"]["determinism_probes"])
    probes = _read_existing_rows(probe_path, "canonical_work_id")
    if probes and set(probes) != {str(row["canonical_work_id"]) for row in candidates.values()}:
        raise Pilot3PhaseAError("persisted determinism probes do not match the frozen probe set")
    loaded = None
    section = config["a_vector"]
    for key in sorted(candidates):
        split = candidates[key]
        work_id = str(split["canonical_work_id"])
        if work_id in probes:
            verify_self_hash(probes[work_id], "record_sha256")
            if probes[work_id].get("exact_equal") is not True:
                raise Pilot3PhaseAError(f"persisted determinism probe failed: {work_id}")
            continue
        if work_id not in acquisitions or work_id not in features:
            raise Pilot3PhaseAError(f"probe input or first extraction is missing: {work_id}")
        if loaded is None:
            loaded = _load_vae(root, config)
        path = _resolve(root, str(acquisitions[work_id]["normalized_path"]))
        repeated = extract_learned_formal(
            path,
            loaded,
            policy=SOURCE_REPLICATION_POLICY,
            base_seed=int(section["base_seed"]),
            device=str(section["device"]),
        )
        first_hash = str(features[work_id]["vector_sha256"])
        repeated_hash = learned_formal_vector_sha256(repeated.vector)
        payload = {
            "record_type": "pilot3_a_vector_determinism_probe",
            "schema_version": "1.0",
            "canonical_work_id": work_id,
            "artist_id": split["artist_id"],
            "source_id": split["source_id"],
            "normalized_sha256": acquisitions[work_id]["normalized_sha256"],
            "first_vector_sha256": first_hash,
            "repeated_vector_sha256": repeated_hash,
            "seed": repeated.metadata.get("seed"),
            "exact_equal": bool(first_hash == repeated_hash),
        }
        row = _self_hash(payload, "record_sha256")
        _append_jsonl_fsync(probe_path, row)
        probes[work_id] = row
        if row["exact_equal"] is not True:
            raise Pilot3PhaseAError(f"A-vector repeatability failed: {work_id}")
    return [probes[key] for key in sorted(probes)]


def _feature_matrix(rows: Sequence[Mapping[str, Any]]) -> np.ndarray:
    matrix = np.asarray([row["vector"] for row in rows], dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != 16_384 or not np.isfinite(matrix).all():
        raise Pilot3PhaseAError("feature matrix is malformed")
    return matrix


def _centroids(
    scores: np.ndarray, labels: Sequence[str], ordered_labels: Sequence[str]
) -> np.ndarray:
    label_array = np.asarray(labels)
    return np.stack([scores[label_array == label].mean(axis=0) for label in ordered_labels])


def _distances(scores: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    return np.linalg.norm(scores[:, None, :] - centroids[None, :, :], axis=2)


def _classification(
    train_scores: np.ndarray,
    train_labels: Sequence[str],
    test_scores: np.ndarray,
    test_labels: Sequence[str],
) -> Dict[str, Any]:
    predictions = predict_nearest_centroid(train_scores, train_labels, test_scores)
    accuracy, recalls = balanced_accuracy(test_labels, predictions)
    label_order = sorted(set(train_labels))
    confusion = {
        expected: {
            predicted: sum(
                1
                for truth, guess in zip(test_labels, predictions)
                if truth == expected and guess == predicted
            )
            for predicted in label_order
        }
        for expected in label_order
    }
    return {
        "balanced_accuracy": accuracy,
        "per_artist_recall": recalls,
        "expected_labels": list(test_labels),
        "predicted_labels": predictions,
        "confusion": confusion,
    }


def _target_neighbor_margins(
    scores: np.ndarray,
    labels: Sequence[str],
    centroids: np.ndarray,
    label_order: Sequence[str],
    neighbor_map: Mapping[str, str],
) -> np.ndarray:
    lookup = {label: index for index, label in enumerate(label_order)}
    distances = _distances(scores, centroids)
    values = []
    for index, label in enumerate(labels):
        values.append(
            distances[index, lookup[neighbor_map[label]]] - distances[index, lookup[label]]
        )
    return np.asarray(values, dtype=np.float64)


def _positive_median(values: np.ndarray, label: str) -> float:
    positives = np.asarray(values, dtype=np.float64)
    positives = positives[np.isfinite(positives) & (positives > 0)]
    if positives.size == 0:
        raise Pilot3PhaseAError(f"cannot freeze positive {label} from development data")
    return float(np.median(positives))


def _npy_bytes(array: np.ndarray) -> bytes:
    output = io.BytesIO()
    np.save(output, np.asarray(array, dtype="<f8"), allow_pickle=False)
    return output.getvalue()


def _scientific_array_sha256(array: np.ndarray) -> str:
    """Match the train-only PCA implementation's semantic array identity."""

    normalized = np.ascontiguousarray(np.asarray(array, dtype="<f8"))
    digest = hashlib.sha256()
    digest.update(str(normalized.shape).encode("ascii"))
    digest.update(b"\0float64-le\0C\0")
    digest.update(normalized.tobytes(order="C"))
    return digest.hexdigest()


def _write_state_array(path: Path, array: np.ndarray) -> Dict[str, Any]:
    payload = _npy_bytes(array)
    digest = hash_bytes(payload)
    if path.exists() and hash_file(path) != digest:
        raise Pilot3PhaseAError(f"frozen state path contains different bytes: {path}")
    if not path.exists():
        _atomic_bytes(path, payload)
    return {
        "path": path.as_posix(),
        "file_sha256": digest,
        "array_shape": list(np.asarray(array).shape),
        "array_dtype": "float64-le",
    }


def _environment_from_feature(row: Mapping[str, Any]) -> Dict[str, Any]:
    metadata = row.get("extraction_metadata", {})
    if not isinstance(metadata, Mapping):
        raise Pilot3PhaseAError("feature extraction metadata is missing")
    return {key: metadata.get(key) for key in _EXTRACTION_RUNTIME_KEYS}


def _single_runtime_environment(
    rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    if not rows:
        raise Pilot3PhaseAError("cannot freeze an empty extraction runtime")
    environments = [_environment_from_feature(row) for row in rows]
    first = environments[0]
    missing = sorted(
        key
        for key, value in first.items()
        if value is None or (isinstance(value, str) and not value.strip())
    )
    if missing:
        raise Pilot3PhaseAError(
            "feature extraction runtime is incomplete: " + ", ".join(missing)
        )
    for row, environment in zip(rows[1:], environments[1:]):
        if environment != first:
            raise Pilot3PhaseAError(
                "development A-vectors use multiple extraction runtimes; first mismatch: "
                + str(row.get("canonical_work_id", "<unknown>"))
            )
    return first


def _closure_paths(config: Mapping[str, Any]) -> List[str]:
    paths = [
        "pyproject.toml",
        "uv.lock",
        "configs/pilot_3/phase_a.json",
        "configs/pilot_3/lee_review.json",
        "configs/pilot_3/external_museum_blocks.json",
        "data/manifests/pilot_3/real_splits.jsonl",
        "reports/pilot_3/evidence/artist_source_feasibility.json",
        "reports/pilot_3/evidence/corpus_selection.json",
        "reports/pilot_3/evidence/holdout_seal.json",
        "reports/pilot_3/evidence/lee_replication.json",
        "reports/pilot_3/evidence/human_validation_disposition.json",
        "docs/PILOT_3_PROTOCOL.md",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/features/learned_formal.py",
        "src/latent_art_bench/pilot2/config.py",
        "src/latent_art_bench/pilot2/learned_formal.py",
        "src/latent_art_bench/pilot2/preprocessing.py",
        "src/latent_art_bench/pilot2/schemas.py",
        "src/latent_art_bench/cli.py",
        "src/latent_art_bench/pilot3/cli.py",
        "src/latent_art_bench/pilot3/lee.py",
        "src/latent_art_bench/pilot3/phasea.py",
        "tests/pilot3/test_lee.py",
        "tests/pilot3/test_phasea.py",
    ]
    runtime_paths = config["paths"]
    paths.extend(
        str(runtime_paths[key])
        for key in (
            "development_acquisition_intents",
            "development_acquisition_attempts",
            "development_acquisitions",
            "development_features",
            "determinism_probes",
        )
    )
    state_dir = Path(str(runtime_paths["state_dir"]))
    paths.extend(
        (state_dir / filename).as_posix()
        for filename in ("pca_mean.npy", "pca_components.npy", "artist_centroids.npy")
    )
    return sorted(set(paths))


def _file_bindings(root: Path, paths: Iterable[str]) -> Dict[str, str]:
    bindings = {}
    for value in sorted(paths):
        path = _resolve(root, value)
        if not path.is_file():
            raise Pilot3PhaseAError(f"required Phase-A closure path is missing: {value}")
        bindings[value] = hash_file(path)
    return bindings


def _selected_feature_rows(
    root: Path, config: Mapping[str, Any], partitions: set[str]
) -> List[Dict[str, Any]]:
    split_rows = [row for row in load_real_splits(root, config) if row["partition"] in partitions]
    phases = {
        "external" if partition == EXTERNAL_PARTITION else "development"
        for partition in partitions
    }
    feature_rows = _combined_phase_rows(
        root, config, "features", "canonical_work_id", sorted(phases)
    )
    acquisition_rows = _combined_phase_rows(
        root, config, "acquisitions", "canonical_work_id", sorted(phases)
    )
    expected_ids = {str(row["canonical_work_id"]) for row in split_rows}
    if set(feature_rows) != expected_ids or set(acquisition_rows) != expected_ids:
        raise Pilot3PhaseAError(
            "Phase-A acquisition/feature ledgers are not the exact selected partition"
        )
    missing = [
        str(row["canonical_work_id"])
        for row in split_rows
        if str(row["canonical_work_id"]) not in feature_rows
        or str(row["canonical_work_id"]) not in acquisition_rows
    ]
    if missing:
        raise Pilot3PhaseAError("Phase-A feature coverage is incomplete: " + ", ".join(missing))
    result = []
    for split in split_rows:
        work_id = str(split["canonical_work_id"])
        feature = feature_rows[work_id]
        _verify_feature(feature, acquisition_rows[work_id], split, config)
        result.append(feature)
    return sorted(result, key=lambda row: str(row["canonical_work_id"]))


def _validated_determinism_probes(
    root: Path,
    config: Mapping[str, Any],
    development_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    training = [
        row for row in development_rows if row["partition"] == "development_training"
    ]
    candidates: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for row in training:
        key = (str(row["artist_id"]), str(row["source_id"]))
        if key not in candidates or str(row["canonical_work_id"]) < str(
            candidates[key]["canonical_work_id"]
        ):
            candidates[key] = row
    expected_keys = {
        (artist, source)
        for artist in EXPECTED_ARTISTS
        for source in DEVELOPMENT_SOURCES
    }
    if set(candidates) != expected_keys:
        raise Pilot3PhaseAError("determinism probe set is not artist/source stratified")
    acquisitions = _read_existing_rows(
        _phase_ledger_path(root, config, "development", "acquisitions"),
        "canonical_work_id",
    )
    raw = _read_existing_rows(
        _resolve(root, config["paths"]["determinism_probes"]),
        "canonical_work_id",
    )
    expected_ids = {str(row["canonical_work_id"]) for row in candidates.values()}
    if set(raw) != expected_ids:
        raise Pilot3PhaseAError("persisted determinism probes do not match the frozen probe set")
    result: List[Dict[str, Any]] = []
    for key in sorted(candidates):
        feature = candidates[key]
        work_id = str(feature["canonical_work_id"])
        acquisition = acquisitions.get(work_id)
        if acquisition is None:
            raise Pilot3PhaseAError(f"determinism probe acquisition is missing: {work_id}")
        metadata = feature.get("extraction_metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("seed"), int):
            raise Pilot3PhaseAError(f"determinism probe seed is missing: {work_id}")
        payload = {
            "record_type": "pilot3_a_vector_determinism_probe",
            "schema_version": "1.0",
            "canonical_work_id": work_id,
            "artist_id": feature["artist_id"],
            "source_id": feature["source_id"],
            "normalized_sha256": acquisition["normalized_sha256"],
            "first_vector_sha256": feature["vector_sha256"],
            "repeated_vector_sha256": feature["vector_sha256"],
            "seed": metadata["seed"],
            "exact_equal": True,
        }
        expected = _self_hash(payload, "record_sha256")
        if raw[work_id] != expected:
            raise Pilot3PhaseAError(f"determinism probe is stale: {work_id}")
        result.append(expected)
    return sorted(result, key=lambda row: str(row["canonical_work_id"]))


def _compute_development_state(
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    probes: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    if len(rows) != 40:
        raise Pilot3PhaseAError("P3-T07 requires exactly 40 development A-vectors")
    runtime_environment = _single_runtime_environment(rows)
    training = [row for row in rows if row["partition"] == "development_training"]
    calibration = [
        row for row in rows if row["partition"] == "development_calibration"
    ]
    if len(training) != 32 or len(calibration) != 8:
        raise Pilot3PhaseAError("development rows do not preserve the 32/8 allocation")
    matrix = _feature_matrix(training)
    pca = fit_train_only_pca(
        matrix,
        [str(row["canonical_work_id"]) for row in training],
        variance_target=float(config["a_vector"]["pca_variance_target"]),
    )
    train_scores = transform_with_pca(matrix, pca)
    calibration_scores = transform_with_pca(_feature_matrix(calibration), pca)
    train_labels = [str(row["artist_id"]) for row in training]
    calibration_labels = [str(row["artist_id"]) for row in calibration]
    label_order = list(EXPECTED_ARTISTS)
    centroids = _centroids(train_scores, train_labels, label_order)
    calibration_classification = _classification(
        train_scores, train_labels, calibration_scores, calibration_labels
    )
    margins = _target_neighbor_margins(
        calibration_scores,
        calibration_labels,
        centroids,
        label_order,
        config["finite_roster"]["neighbor_map"],
    )
    distances = _distances(calibration_scores, centroids)
    label_index = {label: index for index, label in enumerate(label_order)}
    own_distances = np.asarray(
        [distances[index, label_index[label]] for index, label in enumerate(calibration_labels)],
        dtype=np.float64,
    )
    tau_target = _positive_median(own_distances, "target tau")
    tau_specificity = _positive_median(np.abs(margins), "specificity tau")
    source_classification = _classification(
        train_scores,
        [str(row["source_id"]) for row in training],
        calibration_scores,
        [str(row["source_id"]) for row in calibration],
    )
    development_gate = config["development_gate"]
    checks = {
        "exact_repeatability": len(probes) == 8
        and all(row.get("exact_equal") is True for row in probes),
        "complete_feature_support": len(rows) == 40,
        "finite_vectors": bool(np.isfinite(_feature_matrix(rows)).all()),
        "single_exact_extraction_runtime": True,
        "pca_variance_target_reached": bool(pca.evidence.variance_target_reached),
        "calibration_balanced_accuracy_above_chance": (
            calibration_classification["balanced_accuracy"]
            > float(development_gate["calibration_balanced_accuracy_strict_min"])
        ),
        "calibration_mean_target_neighbor_margin_positive": (
            float(np.mean(margins))
            > float(development_gate["calibration_mean_target_neighbor_margin_strict_min"])
        ),
        "positive_target_tau": tau_target > 0,
        "positive_specificity_tau": tau_specificity > 0,
    }
    return {
        "training": training,
        "calibration": calibration,
        "pca": pca,
        "centroids": centroids,
        "label_order": label_order,
        "calibration_classification": calibration_classification,
        "margins": margins,
        "source_classification": source_classification,
        "tau_target": tau_target,
        "tau_specificity": tau_specificity,
        "checks": checks,
        "status": "frozen" if all(checks.values()) else "development_fail",
        "runtime_environment": runtime_environment,
    }


def _state_file_evidence(
    root: Path, path: Path, array: np.ndarray
) -> Dict[str, Any]:
    normalized = np.asarray(array, dtype="<f8")
    return {
        "path": _portable(path, root),
        "file_sha256": hash_bytes(_npy_bytes(normalized)),
        "array_shape": list(normalized.shape),
        "array_dtype": "float64-le",
    }


def _a_vector_protocol_payload(
    root: Path,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    probes: Sequence[Mapping[str, Any]],
    computed: Mapping[str, Any],
    state_files: Mapping[str, Any],
) -> Dict[str, Any]:
    training = computed["training"]
    calibration = computed["calibration"]
    pca = computed["pca"]
    margins = computed["margins"]
    development_gate = config["development_gate"]
    external_rows = [
        row
        for row in load_real_splits(root, config)
        if row["partition"] == EXTERNAL_PARTITION
    ]
    return {
        "record_type": "pilot3_a_vector_protocol",
        "schema_version": A_VECTOR_PROTOCOL_SCHEMA,
        "todo_id": "P3-T07",
        "status": computed["status"],
        "claim_boundary": config["cross_digitization_boundary"],
        "paper_method_boundary": {
            "paper": "Kim et al. 2026, doi:10.1073/pnas.2517969123",
            "paper_a_vector_dimension": 16_384,
            "paper_default_input": [512, 512],
            "paper_aspect_exclusion": "one dimension at least twice the other",
            "paper_low_resolution_wording": "both dimensions described against 410 x 410",
            "released_source_area_predicate_recorded_separately": True,
            "project_intersection": config["input_domain"],
            "project_harmonization_not_unpublished_rng_realization": True,
        },
        "phase_a_config": config,
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "development_feature_manifest_semantic_sha256": stable_hash(rows),
        "training_work_ids": [str(row["canonical_work_id"]) for row in training],
        "calibration_work_ids": [
            str(row["canonical_work_id"]) for row in calibration
        ],
        "expected_external_work_ids": [
            str(row["canonical_work_id"]) for row in external_rows
        ],
        "expected_external_manifest_semantic_sha256": stable_hash(external_rows),
        "pca": pca.evidence.model_dump(mode="json"),
        "label_order": computed["label_order"],
        "state_files": dict(state_files),
        "development_results": {
            "calibration_classification": computed["calibration_classification"],
            "calibration_target_neighbor_margins": margins.astype(float).tolist(),
            "calibration_mean_target_neighbor_margin": float(np.mean(margins)),
            "source_label_predictability_diagnostic": computed[
                "source_classification"
            ],
            "source_predictability_can_open_or_close_gate": False,
            "tau": {
                "target": computed["tau_target"],
                "specificity": computed["tau_specificity"],
                "target_rule": development_gate["tau_target_rule"],
                "specificity_rule": development_gate["tau_specificity_rule"],
            },
            "determinism_probes": list(probes),
        },
        "external_algorithm": {
            "pca_refit_allowed": False,
            "centroid_refit_allowed": False,
            "classifier": "nearest frozen training artist centroid by Euclidean distance",
            "target_neighbor_margin": (
                "distance_to_frozen_neighbor_centroid_minus_"
                "distance_to_frozen_target_centroid"
            ),
            "permutation": (
                "external artist labels independently permuted within each complete "
                "four-artist museum block; frozen reference geometry unchanged"
            ),
            "collection_block_ids": list(EXPECTED_EXTERNAL_BLOCKS),
            "replacement_policy": "none_after_freeze",
            "thresholds": config["external_gate"],
            "single_unseal": True,
        },
        "development_gate_checks": computed["checks"],
        "runtime_environment": computed["runtime_environment"],
        "closure_file_sha256": _file_bindings(root, _closure_paths(config)),
    }


def freeze_a_vector_protocol(
    root: Path,
    *,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Fit development-only PCA/references and emit the P3-T07 A2 contract."""

    root = Path(root).expanduser().resolve()
    require_development_freeze(root)
    config = load_phase_a_config(root, config_path)
    rows = _selected_feature_rows(root, config, set(DEVELOPMENT_PARTITIONS))
    if len(rows) != 40:
        raise Pilot3PhaseAError("P3-T07 requires exactly 40 development A-vectors")
    run_determinism_probes(root, config_path=config_path)
    probes = _validated_determinism_probes(root, config, rows)
    computed = _compute_development_state(config, rows, probes)
    pca = computed["pca"]
    centroids = computed["centroids"]
    checks = computed["checks"]
    status = computed["status"]

    state_dir = _resolve(root, config["paths"]["state_dir"])
    mean_path = state_dir / "pca_mean.npy"
    components_path = state_dir / "pca_components.npy"
    centroids_path = state_dir / "artist_centroids.npy"
    state_files = {
        "pca_mean": _write_state_array(mean_path, pca.mean),
        "pca_components": _write_state_array(components_path, pca.components),
        "artist_centroids": _write_state_array(centroids_path, centroids),
    }
    for evidence in state_files.values():
        evidence["path"] = _portable(_resolve(root, evidence["path"]), root)

    payload = _a_vector_protocol_payload(
        root, config, rows, probes, computed, state_files
    )
    result = _self_hash(payload)
    write_json(_resolve(root, config["paths"]["protocol_evidence"]), result)
    if status != "frozen":
        raise Pilot3PhaseAError(f"development A-vector gate failed: {checks}")
    return result


def verify_a_vector_protocol(
    root: Path,
    protocol: Optional[Mapping[str, Any]] = None,
    *,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Recompute P3-T07 and its numerical state from immutable development rows."""

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root, config_path)
    protocol_path = _resolve(root, config["paths"]["protocol_evidence"])
    if not protocol_path.is_file():
        raise Pilot3PhaseAError("P3-T07 is missing")
    raw = read_json(protocol_path)
    if not isinstance(raw, Mapping):
        raise Pilot3PhaseAError("P3-T07 is not a JSON object")
    observed = dict(raw)
    if protocol is not None and dict(protocol) != observed:
        raise Pilot3PhaseAError("supplied P3-T07 differs from the canonical artifact")
    verify_self_hash(observed)

    rows = _selected_feature_rows(root, config, set(DEVELOPMENT_PARTITIONS))
    probes = _validated_determinism_probes(root, config, rows)
    computed = _compute_development_state(config, rows, probes)
    state_dir = _resolve(root, config["paths"]["state_dir"])
    expected_arrays = {
        "pca_mean": computed["pca"].mean,
        "pca_components": computed["pca"].components,
        "artist_centroids": computed["centroids"],
    }
    expected_paths = {
        "pca_mean": state_dir / "pca_mean.npy",
        "pca_components": state_dir / "pca_components.npy",
        "artist_centroids": state_dir / "artist_centroids.npy",
    }
    state_files = {
        key: _state_file_evidence(root, expected_paths[key], array)
        for key, array in expected_arrays.items()
    }
    for key, expected_array in expected_arrays.items():
        path = expected_paths[key]
        if not path.is_file() or hash_file(path) != state_files[key]["file_sha256"]:
            raise Pilot3PhaseAError(
                f"P3-T07 state bytes do not equal deterministic recomputation: {key}"
            )
        try:
            persisted = np.load(path, allow_pickle=False)
        except Exception as exc:
            raise Pilot3PhaseAError(f"cannot load P3-T07 state array: {key}") from exc
        if not np.array_equal(persisted, np.asarray(expected_array, dtype="<f8")):
            raise Pilot3PhaseAError(
                f"P3-T07 state values do not equal deterministic recomputation: {key}"
            )

    expected = _self_hash(
        _a_vector_protocol_payload(
            root, config, rows, probes, computed, state_files
        )
    )
    if observed != expected:
        mismatches = sorted(
            key
            for key in set(observed) | set(expected)
            if observed.get(key) != expected.get(key)
        )
        raise Pilot3PhaseAError(
            "P3-T07 does not equal deterministic recomputation: "
            + ", ".join(mismatches)
        )
    load_frozen_a_vector_state(root, observed)
    return observed


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


def require_external_unseal(
    root: Path,
    config: Mapping[str, Any],
    token: Optional[str],
) -> Dict[str, Any]:
    """Require a committed, hash-current P3-T07 before external bytes are opened."""

    protocol_path = _resolve(root, config["paths"]["protocol_evidence"])
    if not protocol_path.is_file():
        raise Pilot3PhaseAError("external holdout remains sealed: P3-T07 is missing")
    protocol = read_json(protocol_path)
    if not isinstance(protocol, dict):
        raise Pilot3PhaseAError("P3-T07 is not a JSON object")
    protocol = verify_a_vector_protocol(root, protocol)
    digest = str(protocol["result_sha256"])
    if token != digest or protocol.get("status") != "frozen":
        raise Pilot3PhaseAError("external unseal token/status does not match frozen P3-T07")
    canonical_config_path = _resolve(root, DEFAULT_CONFIG)
    if (
        protocol.get("phase_a_config_file_sha256") != hash_file(canonical_config_path)
        or protocol.get("phase_a_config") != config
    ):
        raise Pilot3PhaseAError("external unseal config does not match frozen P3-T07")
    expected_external_rows = [
        row
        for row in load_real_splits(root, config)
        if row["partition"] == EXTERNAL_PARTITION
    ]
    if (
        protocol.get("expected_external_work_ids")
        != [str(row["canonical_work_id"]) for row in expected_external_rows]
        or protocol.get("expected_external_manifest_semantic_sha256")
        != stable_hash(expected_external_rows)
    ):
        raise Pilot3PhaseAError("external split does not match frozen P3-T07")
    closure = protocol.get("closure_file_sha256")
    expected_closure_paths = set(_closure_paths(config))
    if not isinstance(closure, Mapping) or set(closure) != expected_closure_paths:
        raise Pilot3PhaseAError("P3-T07 closure path set is incomplete or stale")
    for relative, expected in closure.items():
        if not isinstance(relative, str) or not _is_sha256(expected):
            raise Pilot3PhaseAError("P3-T07 closure contains an invalid binding")
        path = _resolve(root, relative)
        if not path.is_file() or hash_file(path) != expected:
            raise Pilot3PhaseAError(f"P3-T07 closure is stale: {relative}")
        if not _git_path_committed_and_clean(root, relative):
            raise Pilot3PhaseAError(f"P3-T07 closure path is not committed and clean: {relative}")
    relative_protocol = _portable(protocol_path, root)
    if not _git_path_committed_and_clean(root, relative_protocol):
        raise Pilot3PhaseAError("P3-T07 itself is not committed and clean")
    return protocol


def _git_head(root: Path) -> str:
    value = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise Pilot3PhaseAError("repository HEAD is not an immutable Git commit")
    return value


def _require_freeze_commit_contains_closure(
    root: Path,
    commit: str,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> None:
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise Pilot3PhaseAError("Freeze-A2 commit is not an ancestor of current HEAD")
    closure = protocol.get("closure_file_sha256")
    if not isinstance(closure, Mapping):
        raise Pilot3PhaseAError("P3-T07 lacks its immutable closure")
    expected = dict(closure)
    protocol_path = _resolve(root, config["paths"]["protocol_evidence"])
    expected[_portable(protocol_path, root)] = hash_file(protocol_path)
    for relative, digest in expected.items():
        if not isinstance(relative, str) or not _is_sha256(digest):
            raise Pilot3PhaseAError("Freeze-A2 closure contains an invalid binding")
        result = subprocess.run(
            ["git", "show", f"{commit}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if result.returncode != 0 or hash_bytes(result.stdout) != digest:
            raise Pilot3PhaseAError(
                f"Freeze-A2 commit does not contain the exact frozen file: {relative}"
            )


def _external_unseal_receipt_payload(
    root: Path,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
    *,
    freeze_a2_git_commit: str,
) -> Dict[str, Any]:
    if (
        len(freeze_a2_git_commit) != 40
        or any(character not in "0123456789abcdef" for character in freeze_a2_git_commit)
    ):
        raise Pilot3PhaseAError("external unseal receipt has an invalid Git commit")
    commit_exists = subprocess.run(
        ["git", "cat-file", "-e", f"{freeze_a2_git_commit}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if commit_exists.returncode != 0:
        raise Pilot3PhaseAError("external unseal receipt references an unknown Git commit")
    _require_freeze_commit_contains_closure(
        root, freeze_a2_git_commit, config, protocol
    )
    external_rows = [
        row
        for row in load_real_splits(root, config)
        if row["partition"] == EXTERNAL_PARTITION
    ]
    payload = {
        "record_type": "pilot3_external_unseal_receipt",
        "schema_version": EXTERNAL_UNSEAL_RECEIPT_SCHEMA,
        "status": "consumed_resume_only_until_terminal_result",
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "a_vector_protocol_file_sha256": hash_file(
            _resolve(root, config["paths"]["protocol_evidence"])
        ),
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "freeze_a2_git_commit": freeze_a2_git_commit,
        "freeze_a2_commit_contains_exact_p3_t07_closure": True,
        "expected_external_work_ids": [
            str(row["canonical_work_id"]) for row in external_rows
        ],
        "expected_external_manifest_semantic_sha256": stable_hash(external_rows),
        "transaction": "unseal_and_validate_external",
        "resume_policy": (
            "only the exact token/config/manifest-bound transaction may resume after interruption"
        ),
        "outcome_dependent_replacement_or_restart_allowed": False,
    }
    return _self_hash(payload, "receipt_sha256")


def _write_exclusive_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(dict(value)) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError("short write while persisting immutable JSON")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


@contextmanager
def _external_transaction_lock(root: Path) -> Iterator[None]:
    """Exclude concurrent unseal/resume processes while allowing crash recovery."""

    receipt_path = _resolve(root, DEFAULT_EXTERNAL_UNSEAL_RECEIPT)
    lock_path = receipt_path.with_name("external_unseal_transaction.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            raise Pilot3PhaseAError(
                "another external unseal transaction is already running"
            ) from exc
        yield
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _consume_external_unseal(
    root: Path,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> Dict[str, Any]:
    """Durably consume the one external transaction before its first network request."""

    path = _resolve(root, DEFAULT_EXTERNAL_UNSEAL_RECEIPT)
    if path.exists():
        observed = read_json(path)
        if not isinstance(observed, Mapping):
            raise Pilot3PhaseAError("external unseal receipt is malformed")
        receipt = dict(observed)
        verify_self_hash(receipt, "receipt_sha256")
        commit = receipt.get("freeze_a2_git_commit")
        if not isinstance(commit, str):
            raise Pilot3PhaseAError("external unseal receipt lacks its Freeze-A2 commit")
        expected = _external_unseal_receipt_payload(
            root,
            config,
            protocol,
            freeze_a2_git_commit=commit,
        )
        if receipt != expected:
            raise Pilot3PhaseAError(
                "external unseal was already consumed by another token/config/manifest"
            )
        return receipt

    receipt = _external_unseal_receipt_payload(
        root,
        config,
        protocol,
        freeze_a2_git_commit=_git_head(root),
    )
    try:
        _write_exclusive_json(path, receipt)
    except FileExistsError:
        return _consume_external_unseal(root, config, protocol)
    return receipt


def verify_external_unseal_receipt(
    root: Path,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
) -> Dict[str, Any]:
    path = _resolve(root, DEFAULT_EXTERNAL_UNSEAL_RECEIPT)
    if not path.is_file():
        raise Pilot3PhaseAError("external unseal receipt is missing")
    raw = read_json(path)
    if not isinstance(raw, Mapping):
        raise Pilot3PhaseAError("external unseal receipt is malformed")
    receipt = dict(raw)
    verify_self_hash(receipt, "receipt_sha256")
    commit = receipt.get("freeze_a2_git_commit")
    if not isinstance(commit, str):
        raise Pilot3PhaseAError("external unseal receipt lacks its Freeze-A2 commit")
    expected = _external_unseal_receipt_payload(
        root,
        config,
        protocol,
        freeze_a2_git_commit=commit,
    )
    if receipt != expected:
        raise Pilot3PhaseAError("external unseal receipt is stale")
    return receipt


def load_frozen_a_vector_state(
    root: Path, protocol: Mapping[str, Any]
) -> Tuple[Pilot2FrozenPCA, np.ndarray, List[str]]:
    state = protocol.get("state_files", {})
    if not isinstance(state, Mapping) or set(state) != {
        "pca_mean",
        "pca_components",
        "artist_centroids",
    }:
        raise Pilot3PhaseAError("P3-T07 state-file manifest is incomplete or has extras")
    arrays: Dict[str, np.ndarray] = {}
    for key in ("pca_mean", "pca_components", "artist_centroids"):
        evidence = state.get(key, {})
        if not isinstance(evidence, Mapping) or set(evidence) != {
            "path",
            "file_sha256",
            "array_shape",
            "array_dtype",
        }:
            raise Pilot3PhaseAError(f"frozen A-vector state evidence is malformed: {key}")
        if evidence.get("array_dtype") != "float64-le":
            raise Pilot3PhaseAError(f"frozen A-vector state dtype is stale: {key}")
        path = _resolve(root, str(evidence.get("path", "")))
        if not path.is_file() or hash_file(path) != evidence.get("file_sha256"):
            raise Pilot3PhaseAError(f"frozen A-vector state is missing or stale: {key}")
        try:
            arrays[key] = np.load(path, allow_pickle=False)
        except Exception as exc:
            raise Pilot3PhaseAError(f"cannot load frozen A-vector state: {key}") from exc
        if list(arrays[key].shape) != evidence.get("array_shape"):
            raise Pilot3PhaseAError(f"frozen A-vector state shape is stale: {key}")
        if arrays[key].dtype.kind != "f" or arrays[key].dtype.itemsize != 8:
            raise Pilot3PhaseAError(f"frozen A-vector state has a non-float64 dtype: {key}")
        if not np.isfinite(arrays[key]).all():
            raise Pilot3PhaseAError(f"frozen A-vector state is non-finite: {key}")
    evidence = protocol.get("pca")
    if not isinstance(evidence, dict):
        raise Pilot3PhaseAError("P3-T07 lacks PCA evidence")
    from latent_art_bench.pilot2.schemas import Pilot2PCAEvidence

    try:
        validated_evidence = Pilot2PCAEvidence.model_validate(evidence)
    except Exception as exc:
        raise Pilot3PhaseAError("P3-T07 PCA evidence is malformed") from exc
    evidence_payload = validated_evidence.model_dump(mode="json")
    recorded_state_sha256 = evidence_payload.pop("state_sha256")
    if recorded_state_sha256 != stable_hash(evidence_payload):
        raise Pilot3PhaseAError("P3-T07 PCA evidence self-identity is stale")
    mean = np.asarray(arrays["pca_mean"], dtype=np.float64)
    components = np.asarray(arrays["pca_components"], dtype=np.float64)
    training_ids = protocol.get("training_work_ids")
    if (
        not isinstance(training_ids, list)
        or len(training_ids) != 32
        or len(set(training_ids)) != 32
        or validated_evidence.fit_work_ids != training_ids
    ):
        raise Pilot3PhaseAError("P3-T07 PCA fit identities are stale")
    if (
        mean.shape != (16_384,)
        or components.ndim != 2
        or components.shape
        != (validated_evidence.component_count, validated_evidence.input_dimension)
        or validated_evidence.input_dimension != 16_384
        or validated_evidence.component_cap != 31
        or validated_evidence.variance_target_reached is not True
    ):
        raise Pilot3PhaseAError("frozen PCA geometry disagrees with its evidence")
    if (
        _scientific_array_sha256(mean) != validated_evidence.mean_sha256
        or _scientific_array_sha256(components) != validated_evidence.basis_sha256
    ):
        raise Pilot3PhaseAError("frozen PCA arrays disagree with their semantic hashes")
    gram = components @ components.T
    if not np.allclose(
        gram,
        np.eye(components.shape[0], dtype=np.float64),
        rtol=1e-10,
        atol=1e-10,
    ):
        raise Pilot3PhaseAError("frozen PCA basis is not orthonormal")
    pca = Pilot2FrozenPCA(
        mean=mean,
        components=components,
        evidence=validated_evidence,
    )
    labels = list(protocol.get("label_order", ()))
    if labels != list(EXPECTED_ARTISTS):
        raise Pilot3PhaseAError("frozen centroid label order is stale")
    centroids = np.asarray(arrays["artist_centroids"], dtype=np.float64)
    if centroids.shape != (4, pca.components.shape[0]):
        raise Pilot3PhaseAError("frozen centroid geometry has the wrong shape")
    return pca, centroids, labels


def project_a_vectors(
    vectors: Sequence[Sequence[float]], pca: Pilot2FrozenPCA
) -> np.ndarray:
    """Project real or generated raw A-vectors through the frozen Phase-A PCA."""

    return transform_with_pca(np.asarray(vectors, dtype=np.float64), pca)


def _permutation_p_values(
    scores: np.ndarray,
    true_labels: Sequence[str],
    collection_block_ids: Sequence[str],
    centroids: np.ndarray,
    label_order: Sequence[str],
    neighbor_map: Mapping[str, str],
) -> Dict[str, Any]:
    if len(collection_block_ids) != len(true_labels):
        raise Pilot3PhaseAError("external permutation blocks do not align with labels")
    block_order = sorted(set(collection_block_ids))
    if not block_order:
        raise Pilot3PhaseAError("external permutation requires collection blocks")
    for block in block_order:
        block_labels = [
            label
            for label, observed_block in zip(true_labels, collection_block_ids)
            if observed_block == block
        ]
        if Counter(block_labels) != Counter(label_order):
            raise Pilot3PhaseAError(
                f"external permutation block is not one-per-artist complete: {block}"
            )
    label_lookup = {label: index for index, label in enumerate(label_order)}
    distances = _distances(scores, centroids)
    predictions = [label_order[index] for index in np.argmin(distances, axis=1)]
    observed_ba, _ = balanced_accuracy(true_labels, predictions)
    observed_margins = _target_neighbor_margins(
        scores, true_labels, centroids, label_order, neighbor_map
    )
    observed_margin = float(np.mean(observed_margins))
    block_indices = [
        [
            index
            for index, observed_block in enumerate(collection_block_ids)
            if observed_block == block
        ]
        for block in block_order
    ]
    block_assignments = tuple(permutations(label_order))
    assignment_count = len(block_assignments) ** len(block_order)
    classification_exceedances = 0
    margin_exceedances = 0
    for assignments in product(block_assignments, repeat=len(block_order)):
        permuted = list(true_labels)
        for indices, labels_for_block in zip(block_indices, assignments):
            for index, label in zip(indices, labels_for_block):
                permuted[index] = label
        statistic, _ = balanced_accuracy(permuted, predictions)
        classification_exceedances += int(statistic >= observed_ba)
        permuted_margins = []
        for index, label in enumerate(permuted):
            permuted_margins.append(
                distances[index, label_lookup[neighbor_map[label]]]
                - distances[index, label_lookup[label]]
            )
        margin_exceedances += int(float(np.mean(permuted_margins)) >= observed_margin)
    return {
        "assignment_count": assignment_count,
        "assignment_space": f"{math.factorial(len(label_order))}^{len(block_order)}",
        "exhaustive": True,
        "scheme": (
            "all artist-label assignments independently enumerated within each "
            "complete museum block"
        ),
        "collection_block_ids": block_order,
        "classification_exceedance_count": classification_exceedances,
        "classification_p_value": classification_exceedances / assignment_count,
        "neighbor_margin_exceedance_count": margin_exceedances,
        "neighbor_margin_p_value": margin_exceedances / assignment_count,
    }


def _holm_checks(p_values: Mapping[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    decisions = {}
    continuing = True
    for rank, (name, value) in enumerate(ordered, start=1):
        threshold = alpha / (len(ordered) - rank + 1)
        passed = continuing and value <= threshold
        decisions[name] = {
            "raw_p_value": value,
            "holm_threshold": threshold,
            "reject": passed,
        }
        continuing = passed
    return {
        "familywise_alpha": alpha,
        "method": "Holm step-down",
        "ordered_hypotheses": [name for name, _ in ordered],
        "decisions": decisions,
        "all_rejected": all(item["reject"] for item in decisions.values()),
    }


def _external_holdout_result_payload(
    root: Path,
    config: Mapping[str, Any],
    protocol: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    """Recompute the complete P3-T08 payload without trusting stored statistics."""

    rows = _selected_feature_rows(root, config, {EXTERNAL_PARTITION})
    if len(rows) != 12:
        raise Pilot3PhaseAError("external evaluation requires exactly 12 A-vectors")
    frozen_runtime = protocol.get("runtime_environment")
    if (
        not isinstance(frozen_runtime, Mapping)
        or set(frozen_runtime) != set(_EXTRACTION_RUNTIME_KEYS)
        or _single_runtime_environment(rows) != dict(frozen_runtime)
    ):
        raise Pilot3PhaseAError(
            "external A-vectors do not match the exact frozen P3-T07 runtime"
        )
    pca, centroids, label_order = load_frozen_a_vector_state(root, protocol)
    scores = project_a_vectors([row["vector"] for row in rows], pca)
    labels = [str(row["artist_id"]) for row in rows]
    collection_block_ids = [str(row["collection_block_id"]) for row in rows]
    asset_providers = [str(row["asset_provider"]) for row in rows]
    block_artist_counts = Counter(zip(collection_block_ids, labels))
    if block_artist_counts != Counter(
        (block, artist)
        for block in EXPECTED_EXTERNAL_BLOCKS
        for artist in EXPECTED_ARTISTS
    ):
        raise Pilot3PhaseAError("external feature rows do not preserve complete museum blocks")
    distances = _distances(scores, centroids)
    predictions = [label_order[index] for index in np.argmin(distances, axis=1)]
    accuracy, recalls = balanced_accuracy(labels, predictions)
    margins = _target_neighbor_margins(
        scores,
        labels,
        centroids,
        label_order,
        config["finite_roster"]["neighbor_map"],
    )
    confusion = {
        expected: {
            predicted: sum(
                1
                for truth, guess in zip(labels, predictions)
                if truth == expected and guess == predicted
            )
            for predicted in label_order
        }
        for expected in label_order
    }
    block_diagnostics: Dict[str, Any] = {}
    provider_diagnostics: Dict[str, Any] = {}
    for block in EXPECTED_EXTERNAL_BLOCKS:
        indices = [
            index
            for index, observed_block in enumerate(collection_block_ids)
            if observed_block == block
        ]
        block_labels = [labels[index] for index in indices]
        block_predictions = [predictions[index] for index in indices]
        block_accuracy, block_recalls = balanced_accuracy(
            block_labels, block_predictions
        )
        block_confusion = {
            expected: {
                predicted: sum(
                    1
                    for truth, guess in zip(block_labels, block_predictions)
                    if truth == expected and guess == predicted
                )
                for predicted in label_order
            }
            for expected in label_order
        }
        providers = {asset_providers[index] for index in indices}
        if len(providers) != 1:
            raise Pilot3PhaseAError(
                f"external collection block has multiple asset providers: {block}"
            )
        provider = providers.pop()
        diagnostic = {
            "asset_provider": provider,
            "work_ids": [str(rows[index]["canonical_work_id"]) for index in indices],
            "balanced_accuracy": block_accuracy,
            "per_artist_recall": block_recalls,
            "confusion": block_confusion,
        }
        block_diagnostics[block] = diagnostic
        if provider in provider_diagnostics:
            raise Pilot3PhaseAError("asset provider is reused across external blocks")
        provider_diagnostics[provider] = {
            "collection_block_id": block,
            **{key: value for key, value in diagnostic.items() if key != "asset_provider"},
        }
    thresholds = config["external_gate"]
    permutation = _permutation_p_values(
        scores,
        labels,
        collection_block_ids,
        centroids,
        label_order,
        config["finite_roster"]["neighbor_map"],
    )
    if permutation["assignment_count"] != thresholds["permutation_assignment_count"]:
        raise Pilot3PhaseAError(
            "enumerated external assignment count disagrees with the frozen contract"
        )
    holm = _holm_checks(
        {
            "classification_above_chance": float(permutation["classification_p_value"]),
            "target_neighbor_margin_positive": float(
                permutation["neighbor_margin_p_value"]
            ),
        }
    )
    centroid_pair_distances = []
    for left in range(len(label_order)):
        for right in range(left + 1, len(label_order)):
            centroid_pair_distances.append(
                float(np.linalg.norm(centroids[left] - centroids[right]))
            )
    reference_scale = float(np.median(centroid_pair_distances))
    effect = float(np.mean(margins) / reference_scale) if reference_scale > 0 else float("nan")
    checks = {
        "exact_external_count": len(rows) == 12,
        "external_source_is_museum_balanced": {
            row["source_id"] for row in rows
        }
        == {EXTERNAL_SOURCE},
        "three_complete_one_per_artist_collection_blocks": set(
            collection_block_ids
        )
        == set(EXPECTED_EXTERNAL_BLOCKS),
        "no_post_freeze_block_replacement": True,
        "all_vectors_finite": bool(np.isfinite(_feature_matrix(rows)).all()),
        "single_exact_extraction_runtime": True,
        "no_training_or_calibration_work_overlap": not bool(
            {row["canonical_work_id"] for row in rows}
            & set(protocol["training_work_ids"] + protocol["calibration_work_ids"])
        ),
        "pca_and_centroids_not_refit": True,
        "balanced_accuracy_above_chance": (
            accuracy > float(thresholds["balanced_accuracy_strict_min"])
        ),
        "every_artist_recall_at_or_above_floor": all(
            value >= float(thresholds["per_artist_recall_min"]) for value in recalls.values()
        ),
        "mean_target_neighbor_margin_positive": (
            float(np.mean(margins))
            > float(thresholds["mean_target_neighbor_margin_strict_min"])
        ),
        "holm_external_tests_pass": bool(holm["all_rejected"]),
    }
    status = "pass" if all(checks.values()) else "fail"
    acquisition_rows = _read_existing_rows(
        _phase_ledger_path(root, config, "external", "acquisitions"),
        "canonical_work_id",
    )
    external_attempt_path = _phase_ledger_path(
        root, config, "external", "acquisition_attempts"
    )
    external_attempt_events = _read_canonical_http_attempt_events(
        external_attempt_path
    )
    payload = {
        "record_type": "pilot3_a_vector_external_validation",
        "schema_version": EXTERNAL_RESULT_SCHEMA,
        "todo_id": "P3-T08",
        "status": status,
        "a_vector_protocol_result_sha256": protocol["result_sha256"],
        "external_unseal_receipt_sha256": receipt["receipt_sha256"],
        "freeze_a2_git_commit": receipt["freeze_a2_git_commit"],
        "external_work_ids": [str(row["canonical_work_id"]) for row in rows],
        "external_collection_blocks": {
            block: [
                str(row["canonical_work_id"])
                for row in rows
                if row["collection_block_id"] == block
            ]
            for block in EXPECTED_EXTERNAL_BLOCKS
        },
        "external_feature_manifest_semantic_sha256": stable_hash(rows),
        "external_acquisition_record_sha256": {
            str(row["canonical_work_id"]): acquisition_rows[str(row["canonical_work_id"])][
                "record_sha256"
            ]
            for row in rows
        },
        "external_acquisition_http_attempt_ledger_file_sha256": hash_file(
            external_attempt_path
        ),
        "external_acquisition_http_attempt_ledger_semantic_sha256": stable_hash(
            external_attempt_events
        ),
        "classification": {
            "balanced_accuracy": accuracy,
            "chance_balanced_accuracy": 0.25,
            "per_artist_recall": recalls,
            "expected_labels": labels,
            "predicted_labels": predictions,
            "per_source_confusion": {EXTERNAL_SOURCE: confusion},
            "per_collection_block_diagnostics": block_diagnostics,
            "per_asset_provider_diagnostics": provider_diagnostics,
        },
        "target_neighbor_validation": {
            "neighbor_map": config["finite_roster"]["neighbor_map"],
            "margins": margins.astype(float).tolist(),
            "mean_margin": float(np.mean(margins)),
            "median_margin": float(np.median(margins)),
            "reference_scale_median_pairwise_centroid_distance": reference_scale,
            "standardized_mean_margin": effect,
        },
        "permutation": permutation,
        "multiplicity": holm,
        "reproduction_validation": {
            "status": "not_run_no_eligible_independent_byte_level_reproductions",
            "can_open_or_close_gate": False,
            "claim_restriction": config["cross_digitization_boundary"],
        },
        "leakage_and_provenance": {
            "checks": checks,
            "training_work_ids_sha256": stable_hash(protocol["training_work_ids"]),
            "calibration_work_ids_sha256": stable_hash(protocol["calibration_work_ids"]),
            "external_work_ids_sha256": stable_hash(
                [str(row["canonical_work_id"]) for row in rows]
            ),
            "reference_sources": list(DEVELOPMENT_SOURCES),
            "query_source": EXTERNAL_SOURCE,
            "collection_block_ids": list(EXPECTED_EXTERNAL_BLOCKS),
            "replacement_policy": "none_after_freeze",
        },
        "gate_checks": checks,
    }
    return payload


def verify_external_holdout_result(
    root: Path,
    *,
    external_unseal_token: Optional[str] = None,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Deterministically recompute and verify the canonical P3-T08 artifact."""

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root, config_path)
    result_path = _resolve(root, config["paths"]["external_result"])
    if not result_path.is_file():
        raise Pilot3PhaseAError("P3-T08 is missing")
    raw = read_json(result_path)
    if not isinstance(raw, Mapping):
        raise Pilot3PhaseAError("persisted external result is malformed")
    observed = dict(raw)
    verify_self_hash(observed)
    recorded_token = observed.get("a_vector_protocol_result_sha256")
    if not isinstance(recorded_token, str):
        raise Pilot3PhaseAError("P3-T08 lacks its P3-T07 token")
    if external_unseal_token is not None and external_unseal_token != recorded_token:
        raise Pilot3PhaseAError("persisted external result belongs to another protocol")
    protocol = require_external_unseal(root, config, recorded_token)
    receipt = verify_external_unseal_receipt(root, config, protocol)
    expected = _self_hash(
        _external_holdout_result_payload(root, config, protocol, receipt)
    )
    if observed != expected:
        mismatches = sorted(
            key
            for key in set(observed) | set(expected)
            if observed.get(key) != expected.get(key)
        )
        raise Pilot3PhaseAError(
            "P3-T08 does not equal deterministic recomputation: "
            + ", ".join(mismatches)
        )
    return observed


def evaluate_external_holdout(
    root: Path,
    *,
    external_unseal_token: str,
    config_path: Path = DEFAULT_CONFIG,
    _transaction_capability: object | None = None,
) -> Dict[str, Any]:
    """Evaluate P3-T08 only as the terminal step of the unseal transaction."""

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root, config_path)
    protocol = require_external_unseal(root, config, external_unseal_token)
    receipt = verify_external_unseal_receipt(root, config, protocol)
    result_path = _resolve(root, config["paths"]["external_result"])
    if result_path.exists():
        return verify_external_holdout_result(
            root,
            external_unseal_token=external_unseal_token,
            config_path=config_path,
        )
    if _transaction_capability is not _EXTERNAL_TRANSACTION_CAPABILITY:
        raise Pilot3PhaseAError(
            "external evaluation is available only inside unseal_and_validate_external"
        )
    result = _self_hash(
        _external_holdout_result_payload(root, config, protocol, receipt)
    )
    try:
        _write_exclusive_json(result_path, result)
    except FileExistsError:
        pass
    return verify_external_holdout_result(
        root,
        external_unseal_token=external_unseal_token,
        config_path=config_path,
    )


def unseal_and_validate_external(
    root: Path,
    *,
    external_unseal_token: str,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Consume the token, then acquire, extract, and evaluate without yielding control."""

    root = Path(root).expanduser().resolve()
    with _external_transaction_lock(root):
        return _run_external_transaction(
            root,
            external_unseal_token=external_unseal_token,
            config_path=config_path,
        )


def _run_external_transaction(
    root: Path,
    *,
    external_unseal_token: str,
    config_path: Path,
) -> Dict[str, Any]:
    config = load_phase_a_config(root, config_path)
    protocol = require_external_unseal(root, config, external_unseal_token)
    _consume_external_unseal(root, config, protocol)
    result_path = _resolve(root, config["paths"]["external_result"])
    if result_path.exists():
        return verify_external_holdout_result(
            root,
            external_unseal_token=external_unseal_token,
            config_path=config_path,
        )
    acquire_real_partition(
        root,
        phase="external",
        config_path=config_path,
        external_unseal_token=external_unseal_token,
        _transaction_capability=_EXTERNAL_TRANSACTION_CAPABILITY,
    )
    extract_real_partition(
        root,
        phase="external",
        config_path=config_path,
        external_unseal_token=external_unseal_token,
        _transaction_capability=_EXTERNAL_TRANSACTION_CAPABILITY,
    )
    return evaluate_external_holdout(
        root,
        external_unseal_token=external_unseal_token,
        config_path=config_path,
        _transaction_capability=_EXTERNAL_TRANSACTION_CAPABILITY,
    )


def phase_a_runtime_summary() -> Dict[str, str]:
    """Small deterministic diagnostic useful in evidence and tests."""

    return {
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "numpy_version": np.__version__,
    }
