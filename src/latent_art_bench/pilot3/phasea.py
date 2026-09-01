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

import base64
import ctypes
import hashlib
import io
import json
import math
import os
import platform
import plistlib
import stat
import subprocess
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from itertools import permutations, product
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlsplit

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
from latent_art_bench.pilot3 import met_r2 as pilot3_met_r2
from latent_art_bench.pilot3 import normalization_scope as pilot3_normalization_scope
from latent_art_bench.pilot3.design_freeze import verify_phase_b_freeze_bundle
from latent_art_bench.pilot3.planning import verify_planning_bundle
from latent_art_bench.pilot3.preprocessing import (
    PILOT3_NORMALIZATION_PROTOCOL_VERSION,
    pilot3_common_png_bytes,
    pilot3_normalization_runtime_fingerprint,
)

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
BROWSER_RECOVERY_AUTHORIZATION_SCHEMA = (
    "pilot3-aic-browser-recovery-authorization/1.0"
)
BROWSER_RECOVERY_SCHEMA = "pilot3-real-acquisition-browser-recovery/1.0"
BROWSER_RECOVERY_AUTHORIZATION_PATH = Path(
    "reports/pilot_3/evidence/aic_browser_recovery_authorization.json"
)
BROWSER_RECOVERY_LEDGER_PATH = Path(
    "artifacts/pilot_3/development_browser_recoveries.jsonl"
)
BROWSER_DIRECTORY_INTENT_LEDGER_PATH = Path(
    "artifacts/pilot_3/development_browser_directory_intents.jsonl"
)
BROWSER_RECOVERY_SCRIPT_PATH = Path(
    "scripts/import_pilot3_browser_acquisition.py"
)
BROWSER_RECOVERY_AMENDMENT_PATH = Path(
    "docs/PILOT_3_AIC_BROWSER_RECOVERY.md"
)
BROWSER_RECOVERY_IMPLEMENTATION_PATHS = (
    "src/latent_art_bench/pilot3/phasea.py",
    str(BROWSER_RECOVERY_SCRIPT_PATH),
    str(BROWSER_RECOVERY_AMENDMENT_PATH),
)
PREPROCESSING_INCIDENT_PATH = Path(
    "reports/pilot_3/evidence/preprocessing_determinism_incident.json"
)
PREPROCESSING_AMENDMENT_PATH = Path(
    "reports/pilot_3/evidence/preprocessing_determinism_amendment.json"
)
NORMALIZATION_REVALIDATION_LEDGER_PATH = Path(
    "artifacts/pilot_3/development_normalization_revalidations.jsonl"
)
PREPROCESSING_AMENDMENT_DOC_PATH = Path(
    "docs/PILOT_3_PREPROCESSING_DETERMINISM_AMENDMENT.md"
)
PREPROCESSING_AMENDMENT_SCHEMA = "pilot3-preprocessing-determinism-amendment/1.0"
MET_R2_NORMALIZED_ACQUISITION_SCHEMA = "3.0"
MET_R2_ASSET_PROVIDER = "The Metropolitan Museum of Art primaryImage"
GENERIC_NORMALIZATION_LINEAGE_FIELDS = (
    "normalization_authorization_schema",
    "normalization_authorization_sha256",
)
MET_R2_LINEAGE_FIELDS = (
    "digital_asset_protocol_namespace",
    "r2_asset_id",
    "r2_authorization_sha256",
    "r2_metadata_freeze_sha256",
    "r2_target_row_sha256",
    "r2_image_terminal_event_sha256",
    "r2_image_acquisition_record_sha256",
    "r2_cohort_observation_sha256",
)
NORMALIZATION_REVALIDATION_SCHEMA = "pilot3-normalization-revalidation-supersession/1.0"
PREPROCESSING_INCIDENT_SCHEMA = "pilot3-preprocessing-determinism-incident/1.0"
PREPROCESSING_INCIDENT_COMMIT = "582fc07ad34e90f0ba585f88a7e3efce8236780c"
PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT = (
    "83f4d9a679f45324367654f64eb735a4f1a5f874"
)
PREPROCESSING_FREEZE_A1_COMMIT = "dbabde357520226fa7e6c0153af59ed3003e703a"
PREPROCESSING_INCIDENT_SHA256 = (
    "ddfebc98d60b02609124280df5d91ba7ae8713b5fd6663179ce0669e2fed0b22"
)
PREPROCESSING_INCIDENT_WORK_ID = "work-aic-45240"
PREPROCESSING_INCIDENT_ACQUISITION_COUNT = 12
PREPROCESSING_AMENDMENT_IMPLEMENTATION_PATHS = (
    "src/latent_art_bench/pilot3/preprocessing.py",
    "src/latent_art_bench/pilot3/phasea.py",
    "src/latent_art_bench/pilot3/execution.py",
    str(BROWSER_RECOVERY_SCRIPT_PATH),
    str(PREPROCESSING_AMENDMENT_DOC_PATH),
    "tests/pilot3/test_phasea.py",
    "tests/pilot3/test_execution.py",
)
PREPROCESSING_AMENDMENT_CANONICALIZER_PATHS = (
    "src/latent_art_bench/pilot3/preprocessing.py",
)
PREPROCESSING_HISTORICAL_BLOB_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "configs/pilot_3/phase_a.json",
    "data/manifests/pilot_3/real_splits.jsonl",
    "src/latent_art_bench/pilot2/config.py",
    "src/latent_art_bench/pilot2/preprocessing.py",
    "src/latent_art_bench/pilot3/phasea.py",
    str(BROWSER_RECOVERY_SCRIPT_PATH),
    str(BROWSER_RECOVERY_AMENDMENT_PATH),
    "tests/pilot3/test_phasea.py",
)
PREPROCESSING_UNCHANGED_BASE_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "configs/pilot_3/phase_a.json",
    "data/manifests/pilot_3/real_splits.jsonl",
    "src/latent_art_bench/pilot2/config.py",
    "src/latent_art_bench/pilot2/preprocessing.py",
)
PREPROCESSING_PROSPECTIVE_FORBIDDEN_PATHS = (
    "artifacts/pilot_3/development_a_vectors.jsonl",
    "artifacts/pilot_3/determinism_probes.jsonl",
    "artifacts/pilot_3/a_vector_state",
    "reports/pilot_3/evidence/a_vector_protocol.json",
    "artifacts/pilot_3/external_unseal_receipt.json",
    "artifacts/pilot_3/external_acquisition_intents.jsonl",
    "artifacts/pilot_3/external_acquisition_http_attempts.jsonl",
    "artifacts/pilot_3/external_acquisitions.jsonl",
    "artifacts/pilot_3/external_a_vectors.jsonl",
    "reports/pilot_3/evidence/a_vector_external_validation.json",
    "reports/pilot_3/evidence/account_authorization.json",
    "reports/pilot_3/evidence/model_documentation.json",
    "reports/pilot_3/evidence/oauth_runtime_fingerprint.json",
    "artifacts/pilot_3/transport_qualification_post_intents.jsonl",
    "artifacts/pilot_3/transport_qualification_attempts.jsonl",
    "artifacts/pilot_3/transport_qualification.lock",
    "outputs/pilot_3/transport_qualification",
    "reports/pilot_3/evidence/transport_qualification.json",
    "reports/pilot_3/evidence/generation_gate.json",
    "artifacts/pilot_3/generation_post_intents.jsonl",
    "artifacts/pilot_3/generation_attempts.jsonl",
    "artifacts/pilot_3/generation_global_stop_dispositions.jsonl",
    "artifacts/pilot_3/generation_execution.lock",
    "reports/pilot_3/evidence/generation_runtime_revalidations.jsonl",
    "reports/pilot_3/evidence/generation_execution_context.json",
    "reports/pilot_3/evidence/generation_execution.json",
    "reports/pilot_3/evidence/generation_completion.json",
    "reports/pilot_3/evidence/successful_output_manifest.json",
    "outputs/pilot_3/generated",
    "artifacts/pilot_3/generated_normalized",
    "artifacts/pilot_3/generated_preprocessing.jsonl",
    "artifacts/pilot_3/generated_a_vectors.jsonl",
    "artifacts/pilot_3/generated_a_vector_distances.jsonl",
    "reports/pilot_3/evidence/generated_a_vector_measurement.json",
    "reports/pilot_3/evidence/terminal_dispositions.jsonl",
    "reports/pilot_3/evidence/terminal_disposition_manifest.json",
    "reports/pilot_3/analysis.json",
    "reports/pilot_3/REPORT.md",
    "reports/pilot_3/completion.json",
    "reports/pilot_3/requirement_audit.json",
    "reports/pilot_3/artifact_index.json",
)
AIC_IMAGE_PROVIDER = "Art Institute of Chicago IIIF"
AIC_IMAGE_HOST = "www.artic.edu"
WHERE_FROMS_XATTR = "com.apple.metadata:kMDItemWhereFroms"
QUARANTINE_XATTR = "com.apple.quarantine"
MAX_WHERE_FROMS_PLIST_BYTES = 64 * 1024
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
            str(BROWSER_RECOVERY_AMENDMENT_PATH),
            str(PREPROCESSING_INCIDENT_PATH),
            str(PREPROCESSING_AMENDMENT_DOC_PATH),
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
            "src/latent_art_bench/pilot3/preprocessing.py",
            "src/latent_art_bench/pilot3/planning.py",
            str(BROWSER_RECOVERY_SCRIPT_PATH),
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
    normalization_amendment: Optional[Mapping[str, Any]] = None,
    normalization_authorization: Optional[Mapping[str, Any]] = None,
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
    lineage: Dict[str, Any] = {}
    if normalization_amendment is not None and normalization_authorization is not None:
        raise Pilot3PhaseAError("HTTP start received two normalization authorities")
    if normalization_amendment is not None:
        if (
            normalization_amendment.get("normalization_protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or not _is_sha256(normalization_amendment.get("authorization_sha256"))
        ):
            raise Pilot3PhaseAError("HTTP start received a stale normalization amendment")
        lineage = {
            "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
            "preprocessing_determinism_amendment_sha256": (
                normalization_amendment["authorization_sha256"]
            ),
            "effective_preprocessing_contract_sha256": (
                normalization_amendment["effective_preprocessing_contract_sha256"]
            ),
        }
    elif normalization_authorization is not None:
        implementation = normalization_authorization.get("normalization_implementation")
        if (
            normalization_authorization.get("schema_version")
            != pilot3_normalization_scope.SCHEMA_VERSION
            or not _is_sha256(normalization_authorization.get("authorization_sha256"))
            or not isinstance(implementation, Mapping)
            or implementation.get("protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or not _is_sha256(
                implementation.get("effective_preprocessing_contract_sha256")
            )
        ):
            raise Pilot3PhaseAError(
                "HTTP start received a stale normalization authority"
            )
        lineage = {
            "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
            "normalization_authorization_schema": (
                pilot3_normalization_scope.SCHEMA_VERSION
            ),
            "normalization_authorization_sha256": normalization_authorization[
                "authorization_sha256"
            ],
            "effective_preprocessing_contract_sha256": implementation[
                "effective_preprocessing_contract_sha256"
            ],
        }
    attempt_identity = {
        "phase": phase,
        "canonical_work_id": intent["canonical_work_id"],
        "intent_id": intent["intent_id"],
        "intent_sha256": stable_hash(intent),
        "attempt_number": attempt_number,
        "request_identity_sha256": stable_hash(request_identity),
        **lineage,
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
        **lineage,
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
    lineage = {
        key: start[key]
        for key in (
            "normalization_protocol_version",
            "preprocessing_determinism_amendment_sha256",
            "normalization_authorization_schema",
            "normalization_authorization_sha256",
            "effective_preprocessing_contract_sha256",
        )
        if key in start
    }
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
        **lineage,
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
    legacy_lineage_keys = {
        "normalization_protocol_version",
        "preprocessing_determinism_amendment_sha256",
        "effective_preprocessing_contract_sha256",
    }
    generic_lineage_keys = {
        "normalization_protocol_version",
        "normalization_authorization_schema",
        "normalization_authorization_sha256",
        "effective_preprocessing_contract_sha256",
    }
    all_lineage_keys = legacy_lineage_keys | generic_lineage_keys
    present_lineage = all_lineage_keys & set(start)
    if present_lineage not in (set(), legacy_lineage_keys, generic_lineage_keys):
        raise Pilot3PhaseAError("HTTP attempt start has partial preprocessing lineage")
    if present_lineage:
        required |= present_lineage
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
                *sorted(present_lineage),
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
    *,
    normalization_amendment: Optional[Mapping[str, Any]] = None,
    normalization_authorization: Optional[Mapping[str, Any]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """Verify the append-only start/terminal journal and return histories by intent."""

    path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    histories: Dict[str, List[Dict[str, Any]]] = {
        intent_id: [] for intent_id in intents
    }
    active: Optional[Dict[str, Any]] = None
    previous_event_sha256: Optional[str] = None
    incident_path = _resolve(root, PREPROCESSING_INCIDENT_PATH)
    historical_events: List[Dict[str, Any]] = []
    if incident_path.is_file() and phase == "development":
        historical = subprocess.run(
            [
                "git",
                "show",
                (
                    f"{PREPROCESSING_INCIDENT_COMMIT}:"
                    + _portable(path, root)
                ),
            ],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if historical.returncode != 0:
            raise Pilot3PhaseAError("incident HTTP journal blob is unavailable")
        try:
            historical_events = [
                json.loads(line)
                for line in historical.stdout.decode("utf-8").splitlines()
                if line
            ]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError("incident HTTP journal blob is malformed") from exc
    legacy_lineage_keys = {
        "normalization_protocol_version",
        "preprocessing_determinism_amendment_sha256",
        "effective_preprocessing_contract_sha256",
    }
    generic_lineage_keys = {
        "normalization_protocol_version",
        "normalization_authorization_schema",
        "normalization_authorization_sha256",
        "effective_preprocessing_contract_sha256",
    }
    all_lineage_keys = legacy_lineage_keys | generic_lineage_keys
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
            event_lineage = all_lineage_keys & set(event)
            if event_lineage not in (
                set(),
                legacy_lineage_keys,
                generic_lineage_keys,
            ):
                raise Pilot3PhaseAError(
                    "HTTP attempt start has partial preprocessing lineage"
                )
            is_legacy_v2 = event_lineage == legacy_lineage_keys
            is_generic_v2 = event_lineage == generic_lineage_keys
            is_v2 = is_legacy_v2 or is_generic_v2
            if incident_path.is_file() and not is_v2:
                if index > len(historical_events) or event != historical_events[index - 1]:
                    raise Pilot3PhaseAError(
                        "post-incident HTTP start lacks the v2 technical amendment"
                    )
            if is_legacy_v2 and (
                normalization_amendment is None
                or event.get("normalization_protocol_version")
                != PILOT3_NORMALIZATION_PROTOCOL_VERSION
                or event.get("preprocessing_determinism_amendment_sha256")
                != normalization_amendment.get("authorization_sha256")
                or event.get("effective_preprocessing_contract_sha256")
                != _effective_preprocessing_contract_sha256(config)
            ):
                raise Pilot3PhaseAError(
                    "HTTP attempt start lacks the authorized v2 normalization lineage"
                )
            if is_generic_v2 and (
                normalization_authorization is None
                or event.get("normalization_protocol_version")
                != PILOT3_NORMALIZATION_PROTOCOL_VERSION
                or event.get("normalization_authorization_schema")
                != pilot3_normalization_scope.SCHEMA_VERSION
                or event.get("normalization_authorization_sha256")
                != normalization_authorization.get("authorization_sha256")
                or event.get("effective_preprocessing_contract_sha256")
                != _effective_preprocessing_contract_sha256(config)
            ):
                raise Pilot3PhaseAError(
                    "HTTP attempt start lacks the exact normalization-scope lineage"
                )
            expected = _http_attempt_start(
                phase=phase,
                intent=intent,
                attempt_number=attempt_number,
                event_sequence=index,
                previous_event_sha256=previous_event_sha256,
                max_response_bytes=_acquisition_response_limit(config),
                normalization_amendment=(
                    normalization_amendment if is_legacy_v2 else None
                ),
                normalization_authorization=(
                    normalization_authorization if is_generic_v2 else None
                ),
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
            if incident_path.is_file() and not (all_lineage_keys & set(active)):
                if (
                    index > len(historical_events)
                    or event != historical_events[index - 1]
                ):
                    raise Pilot3PhaseAError(
                        "post-incident HTTP terminal lacks the v2 technical amendment"
                    )
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


def _aic_development_splits(
    root: Path, config: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    rows = [
        row
        for row in load_real_splits(root, config)
        if row["source_id"] == "aic" and row["partition"] in DEVELOPMENT_PARTITIONS
    ]
    if len(rows) != 20:
        raise Pilot3PhaseAError(
            f"AIC browser-recovery scope requires exactly 20 works, found {len(rows)}"
        )
    if len({str(row["image_url"]) for row in rows}) != len(rows):
        raise Pilot3PhaseAError("AIC browser-recovery URLs are not one-to-one with works")
    for row in rows:
        parsed = urlsplit(str(row["image_url"]))
        if (
            row.get("asset_provider") != AIC_IMAGE_PROVIDER
            or row.get("collection_block_id") != "aic"
            or parsed.scheme != "https"
            or parsed.hostname != AIC_IMAGE_HOST
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port is not None
            or not parsed.path.startswith("/iiif/2/")
            or not parsed.path.endswith("/default.jpg")
            or parsed.query
            or parsed.fragment
        ):
            raise Pilot3PhaseAError(
                "AIC browser-recovery target is outside the exact frozen provider domain: "
                + str(row.get("canonical_work_id"))
            )
    return sorted(rows, key=lambda row: str(row["canonical_work_id"]))


def _aic_challenge_evidence(
    root: Path,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    """Return the unique scripted-client 403 that triggered provider recovery.

    The evidence supports only an observed provider-layer access challenge.  It does not
    identify Cloudflare or any other upstream component.
    """

    intent_path = _phase_ledger_path(
        root, config, "development", "acquisition_intents"
    )
    intents = _read_existing_rows(intent_path, "intent_id")
    rows_by_work = {str(row["canonical_work_id"]): dict(row) for row in rows}
    all_development_work_ids = {
        str(row["canonical_work_id"])
        for row in load_real_splits(root, config)
        if row["partition"] in DEVELOPMENT_PARTITIONS
    }
    by_work: Dict[str, Dict[str, Any]] = {}
    for intent in intents.values():
        work_id = str(intent.get("canonical_work_id", ""))
        if not work_id or work_id not in all_development_work_ids:
            raise Pilot3PhaseAError(
                "AIC recovery authorization found an out-of-scope development intent"
            )
        if work_id not in rows_by_work:
            continue
        if work_id in by_work:
            raise Pilot3PhaseAError("AIC recovery authorization found a duplicate AIC intent")
        by_work[work_id] = intent
    first = rows[0]
    first_work_id = str(first["canonical_work_id"])
    intent = by_work.get(first_work_id)
    if intent is None:
        raise Pilot3PhaseAError(
            "AIC recovery requires the first frozen AIC work's durable network intent"
        )
    expected_intent = _acquisition_intent(
        first,
        acquisition_route="network",
        phase_a_config_file_sha256=hash_file(_resolve(root, DEFAULT_CONFIG)),
        external_protocol_result_sha256=None,
        external_unseal_receipt_sha256=None,
    )
    if intent != expected_intent:
        raise Pilot3PhaseAError("AIC challenge intent is not the exact frozen network intent")
    if _resolve(root, PREPROCESSING_INCIDENT_PATH).is_file():
        attempt_path = _phase_ledger_path(
            root, config, "development", "acquisition_attempts"
        )
        historical = subprocess.run(
            [
                "git",
                "show",
                f"{PREPROCESSING_INCIDENT_COMMIT}:{_portable(attempt_path, root)}",
            ],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if historical.returncode != 0:
            raise Pilot3PhaseAError("incident HTTP challenge blob is unavailable")
        try:
            history = [
                json.loads(line)
                for line in historical.stdout.decode("utf-8").splitlines()
                if line
            ]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError("incident HTTP challenge blob is malformed") from exc
        current = _read_canonical_http_attempt_events(attempt_path)
        if current[: len(history)] != history:
            raise Pilot3PhaseAError("incident HTTP challenge prefix changed")
        if len(history) == 2:
            expected_start = _http_attempt_start(
                phase="development",
                intent=intent,
                attempt_number=1,
                event_sequence=1,
                previous_event_sha256=None,
                max_response_bytes=_acquisition_response_limit(config),
            )
            if history[0] != expected_start:
                raise Pilot3PhaseAError("incident HTTP challenge start is stale")
            _validate_http_attempt_terminal(root, config, history[0], history[1])
    else:
        histories = _verified_http_attempt_histories(
            root, config, "development", intents
        )
        history = histories[str(intent["intent_id"])]
    if len(history) != 2:
        raise Pilot3PhaseAError(
            "AIC recovery requires exactly one completed scripted-client attempt"
        )
    start, terminal = history
    if (
        terminal.get("outcome") != "http_status_failure"
        or terminal.get("http_status") != 403
        or terminal.get("content_type") != "text/html"
        or terminal.get("resolved_url") != intent["image_url"]
        or terminal.get("response_complete") is not True
        or terminal.get("retryable") is not False
        or type(terminal.get("response_byte_count")) is not int
        or int(terminal["response_byte_count"]) <= 0
        or not _is_sha256(terminal.get("response_sha256"))
        or terminal.get("raw_path") is not None
    ):
        raise Pilot3PhaseAError(
            "AIC recovery trigger is not the exact observed HTTP 403 HTML response"
        )
    return intent, terminal, history


def _browser_recovery_target_bindings(
    rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        {
            "canonical_work_id": row["canonical_work_id"],
            "image_url": row["image_url"],
            "delivery_width": row["delivery_width"],
            "delivery_height": row["delivery_height"],
            "partition": row["partition"],
            "split_row_sha256": row["row_sha256"],
        }
        for row in rows
    ]


def _browser_recovery_authorization_payload(
    root: Path,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    intent: Mapping[str, Any],
    terminal: Mapping[str, Any],
    history: Sequence[Mapping[str, Any]],
    *,
    pre_recovery_freeze_a1_git_commit: str,
) -> Dict[str, Any]:
    return {
        "record_type": "pilot3_aic_browser_recovery_authorization",
        "schema_version": BROWSER_RECOVERY_AUTHORIZATION_SCHEMA,
        "status": (
            "authorized_before_fresh_recovery_downloads_and_before_any_browser_file_admission"
        ),
        "authorization_scope": "exact_frozen_aic_development_image_urls_only",
        "provider": AIC_IMAGE_PROVIDER,
        "provider_hostname": AIC_IMAGE_HOST,
        "target_count": len(rows),
        "target_bindings": _browser_recovery_target_bindings(rows),
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "split_manifest_file_sha256": hash_file(
            _resolve(root, config["paths"]["split_manifest"])
        ),
        "pre_recovery_freeze_a1_git_commit": pre_recovery_freeze_a1_git_commit,
        "recovery_implementation_file_sha256": {
            relative: hash_file(_resolve(root, relative))
            for relative in BROWSER_RECOVERY_IMPLEMENTATION_PATHS
        },
        "trigger": {
            "claim": "observed_aic_scripted_client_http_403_html_response",
            "cloudflare_attribution_claimed": False,
            "canonical_work_id": intent["canonical_work_id"],
            "intent_id": intent["intent_id"],
            "intent_sha256": stable_hash(intent),
            "http_attempt_id": terminal["attempt_id"],
            "http_terminal_event_sha256": terminal["event_sha256"],
            "http_attempt_history_semantic_sha256": stable_hash(list(history)),
            "http_status": terminal["http_status"],
            "content_type": terminal["content_type"],
            "resolved_url": terminal["resolved_url"],
            "response_byte_count": terminal["response_byte_count"],
            "response_sha256": terminal["response_sha256"],
        },
        "browser_intent_rule": (
            "the_trigger_work_retains_its_failed_network_intent;_the_other_19_works_"
            "receive_first_route_browser_recovery_intents_before_navigation"
        ),
        "where_froms_requirement": (
            "binary_com.apple.metadata:kMDItemWhereFroms_contains_the_exact_frozen_url"
        ),
        "download_directory_policy": (
            "one_create_exclusive_empty_bound_directory_per_attempt;_exactly_one_new_"
            "direct_regular_file;_birth_ctime_and_quarantine_not_before_start"
        ),
        "diagnostic_browser_fetch_disposition": {
            "canonical_work_id": "work-aic-100026",
            "image_url": (
                "https://www.artic.edu/iiif/2/bda9058b-5be6-37d0-e5a6-"
                "926584540757/full/951,1125/0/default.jpg"
            ),
            "raw_sha256": (
                "1703506070e75a50978132507031ec04693aa776a0e437afa238fb3227545fd5"
            ),
            "raw_byte_count": 699_009,
            "downloaded_before_authorization_for_transport_diagnosis": True,
            "visually_inspected": False,
            "feature_extracted": False,
            "admitted_to_analytic_artifacts": False,
            "eligible_for_later_import": False,
            "disposition": "quarantined_and_ineligible;_fresh_post-start_download_required",
        },
        "corpus_url_dimensions_or_provider_changed": False,
        "external_holdout_access_authorized": False,
        "fresh_recovery_navigation_download_or_admission_performed_by_authorizer": False,
    }


def _require_base_freeze_for_recovery_authorization(root: Path) -> None:
    """Verify Freeze A1 while allowing only the prospective recovery amendment to be dirty."""

    corpus = read_json(root / "reports/pilot_3/evidence/corpus_selection.json")
    if not isinstance(corpus, dict) or corpus.get("status") != "freeze_a1_complete":
        raise Pilot3PhaseAError("AIC recovery authorization requires Freeze A1")
    verify_self_hash(corpus, "semantic_sha256")
    try:
        verify_planning_bundle(root)
        verify_phase_b_freeze_bundle(root)
    except Exception as exc:
        raise Pilot3PhaseAError(
            "AIC recovery authorization requires current deterministic freeze bundles"
        ) from exc
    amendment_paths = {
        *BROWSER_RECOVERY_IMPLEMENTATION_PATHS,
        "tests/pilot3/test_phasea.py",
    }
    for relative in _freeze_a1_closure_paths():
        if relative in amendment_paths:
            continue
        if not _git_path_committed_and_clean(root, relative):
            raise Pilot3PhaseAError(
                "base Freeze-A1 closure is not committed and clean: " + relative
            )


def authorize_aic_browser_recovery(root: Path) -> Dict[str, Any]:
    """Create the one prospective provider-recovery authorization, without image I/O."""

    root = Path(root).expanduser().resolve()
    _require_base_freeze_for_recovery_authorization(root)
    config = load_phase_a_config(root)
    rows = _aic_development_splits(root, config)
    path = _resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH)
    if path.is_file():
        observed = read_json(path)
        if not isinstance(observed, dict):
            raise Pilot3PhaseAError("AIC browser-recovery authorization is malformed")
        verify_aic_browser_recovery_authorization(
            root, require_committed=False, require_complete_closure=False
        )
        return observed
    if _read_existing_rows(
        _phase_ledger_path(root, config, "development", "acquisitions"),
        "canonical_work_id",
    ):
        raise Pilot3PhaseAError(
            "AIC recovery authorization must precede development acquisition records"
        )
    for ledger_relative in (
        BROWSER_DIRECTORY_INTENT_LEDGER_PATH,
        BROWSER_RECOVERY_LEDGER_PATH,
    ):
        ledger_path = _resolve(root, ledger_relative)
        if ledger_path.is_file() and ledger_path.stat().st_size:
            raise Pilot3PhaseAError(
                "AIC recovery authorization must precede browser directory/attempt events"
            )
    intent, terminal, history = _aic_challenge_evidence(root, config, rows)
    payload = _browser_recovery_authorization_payload(
        root,
        config,
        rows,
        intent,
        terminal,
        history,
        pre_recovery_freeze_a1_git_commit=_git_head(root),
    )
    authorization = _self_hash(payload, "authorization_sha256")
    _write_exclusive_json(path, authorization)
    return authorization


def _verify_aic_browser_recovery_authorization(
    root: Path,
    *,
    require_committed: bool = True,
    require_complete_closure: bool = True,
    historical_implementation_commit: Optional[str] = None,
) -> Dict[str, Any]:
    """Verify the authorization and, for execution, its committed amendment closure."""

    root = Path(root).expanduser().resolve()
    config = load_phase_a_config(root)
    path = _resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH)
    if not path.is_file():
        raise Pilot3PhaseAError("AIC browser-recovery authorization is missing")
    authorization = read_json(path)
    if not isinstance(authorization, dict):
        raise Pilot3PhaseAError("AIC browser-recovery authorization is malformed")
    required = {
        "record_type",
        "schema_version",
        "status",
        "authorization_scope",
        "provider",
        "provider_hostname",
        "target_count",
        "target_bindings",
        "phase_a_config_file_sha256",
        "split_manifest_file_sha256",
        "pre_recovery_freeze_a1_git_commit",
        "recovery_implementation_file_sha256",
        "trigger",
        "browser_intent_rule",
        "where_froms_requirement",
        "download_directory_policy",
        "corpus_url_dimensions_or_provider_changed",
        "external_holdout_access_authorized",
        "diagnostic_browser_fetch_disposition",
        "fresh_recovery_navigation_download_or_admission_performed_by_authorizer",
        "authorization_sha256",
    }
    if set(authorization) != required:
        raise Pilot3PhaseAError("AIC browser-recovery authorization field set is stale")
    verify_self_hash(authorization, "authorization_sha256")
    rows = _aic_development_splits(root, config)
    intent, terminal, history = _aic_challenge_evidence(root, config, rows)
    implementation = authorization.get("recovery_implementation_file_sha256")
    if not isinstance(implementation, Mapping) or set(implementation) != set(
        BROWSER_RECOVERY_IMPLEMENTATION_PATHS
    ):
        raise Pilot3PhaseAError("AIC recovery implementation closure is incomplete")
    expected_static = {
        "record_type": "pilot3_aic_browser_recovery_authorization",
        "schema_version": BROWSER_RECOVERY_AUTHORIZATION_SCHEMA,
        "status": (
            "authorized_before_fresh_recovery_downloads_and_before_any_browser_file_admission"
        ),
        "authorization_scope": "exact_frozen_aic_development_image_urls_only",
        "provider": AIC_IMAGE_PROVIDER,
        "provider_hostname": AIC_IMAGE_HOST,
        "target_count": 20,
        "target_bindings": _browser_recovery_target_bindings(rows),
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "split_manifest_file_sha256": hash_file(
            _resolve(root, config["paths"]["split_manifest"])
        ),
        "trigger": _browser_recovery_authorization_payload(
            root,
            config,
            rows,
            intent,
            terminal,
            history,
            pre_recovery_freeze_a1_git_commit=str(
                authorization["pre_recovery_freeze_a1_git_commit"]
            ),
        )["trigger"],
        "browser_intent_rule": (
            "the_trigger_work_retains_its_failed_network_intent;_the_other_19_works_"
            "receive_first_route_browser_recovery_intents_before_navigation"
        ),
        "where_froms_requirement": (
            "binary_com.apple.metadata:kMDItemWhereFroms_contains_the_exact_frozen_url"
        ),
        "download_directory_policy": (
            "one_create_exclusive_empty_bound_directory_per_attempt;_exactly_one_new_"
            "direct_regular_file;_birth_ctime_and_quarantine_not_before_start"
        ),
        "diagnostic_browser_fetch_disposition": {
            "canonical_work_id": "work-aic-100026",
            "image_url": (
                "https://www.artic.edu/iiif/2/bda9058b-5be6-37d0-e5a6-"
                "926584540757/full/951,1125/0/default.jpg"
            ),
            "raw_sha256": (
                "1703506070e75a50978132507031ec04693aa776a0e437afa238fb3227545fd5"
            ),
            "raw_byte_count": 699_009,
            "downloaded_before_authorization_for_transport_diagnosis": True,
            "visually_inspected": False,
            "feature_extracted": False,
            "admitted_to_analytic_artifacts": False,
            "eligible_for_later_import": False,
            "disposition": "quarantined_and_ineligible;_fresh_post-start_download_required",
        },
        "corpus_url_dimensions_or_provider_changed": False,
        "external_holdout_access_authorized": False,
        "fresh_recovery_navigation_download_or_admission_performed_by_authorizer": False,
    }
    if any(authorization.get(key) != value for key, value in expected_static.items()):
        raise Pilot3PhaseAError("AIC browser-recovery authorization is stale")
    for relative, digest in implementation.items():
        path_value = _resolve(root, str(relative))
        current_matches = (
            _is_sha256(digest)
            and path_value.is_file()
            and hash_file(path_value) == digest
        )
        if not current_matches and historical_implementation_commit is not None:
            historical = subprocess.run(
                [
                    "git",
                    "show",
                    f"{historical_implementation_commit}:{relative}",
                ],
                cwd=root,
                check=False,
                capture_output=True,
            )
            current_matches = (
                historical.returncode == 0
                and _is_sha256(digest)
                and hash_bytes(historical.stdout) == digest
            )
        if not current_matches:
            raise Pilot3PhaseAError(
                "AIC recovery implementation hash is stale: " + str(relative)
            )
        if (
            require_committed
            and historical_implementation_commit is None
            and not _git_path_committed_and_clean(root, str(relative))
        ):
            raise Pilot3PhaseAError(
                "AIC recovery implementation is not committed and clean: "
                + str(relative)
            )
    commit = authorization.get("pre_recovery_freeze_a1_git_commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise Pilot3PhaseAError("AIC recovery authorization has an invalid base commit")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise Pilot3PhaseAError("AIC recovery base commit is not an ancestor of HEAD")
    if require_complete_closure:
        require_development_freeze(root)
    if require_committed and not _git_path_committed_and_clean(
        root, str(BROWSER_RECOVERY_AUTHORIZATION_PATH)
    ):
        raise Pilot3PhaseAError(
            "AIC browser-recovery authorization is not committed and clean"
        )
    return authorization


def verify_aic_browser_recovery_authorization(
    root: Path,
    *,
    require_committed: bool = True,
    require_complete_closure: bool = True,
) -> Dict[str, Any]:
    """Verify the original authorization only against its live implementation."""

    return _verify_aic_browser_recovery_authorization(
        root,
        require_committed=require_committed,
        require_complete_closure=require_complete_closure,
    )


def _git_blob_evidence(root: Path, commit: str, relative: str) -> Dict[str, str]:
    blob = subprocess.run(
        ["git", "rev-parse", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    content = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    object_id = blob.stdout.strip()
    if (
        blob.returncode != 0
        or content.returncode != 0
        or len(object_id) not in {40, 64}
        or any(character not in "0123456789abcdef" for character in object_id)
    ):
        raise Pilot3PhaseAError(
            f"historical preprocessing implementation blob is unavailable: {relative}"
        )
    return {"git_blob_object_id": object_id, "file_sha256": hash_bytes(content.stdout)}


def _git_introduction_commit(root: Path, relative: str) -> str:
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%H", "--reverse", "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    commits = [value.strip() for value in result.stdout.splitlines() if value.strip()]
    if (
        result.returncode != 0
        or len(commits) != 1
        or len(commits[0]) != 40
        or any(character not in "0123456789abcdef" for character in commits[0])
    ):
        raise Pilot3PhaseAError(
            "governance artifact lacks one unambiguous Git introduction: " + relative
        )
    return commits[0]


def _require_git_ancestor(root: Path, ancestor: str, descendant: str, label: str) -> None:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise Pilot3PhaseAError(label)


def _require_strict_git_ancestor(
    root: Path, ancestor: str, descendant: str, label: str
) -> None:
    if ancestor == descendant:
        raise Pilot3PhaseAError(label)
    _require_git_ancestor(root, ancestor, descendant, label)


def verify_preprocessing_determinism_incident(
    root: Path, *, require_exact_checkpoint: bool = False
) -> Dict[str, Any]:
    """Verify the committed incident and the immutable prefixes it checkpointed."""

    root = Path(root).expanduser().resolve()
    path = _resolve(root, PREPROCESSING_INCIDENT_PATH)
    if not path.is_file():
        raise Pilot3PhaseAError("preprocessing-determinism incident is missing")
    incident = read_json(path)
    if not isinstance(incident, dict):
        raise Pilot3PhaseAError("preprocessing-determinism incident is malformed")
    verify_self_hash(incident, "incident_sha256")
    if (
        incident.get("record_type") != "pilot3_preprocessing_determinism_incident"
        or incident.get("schema_version") != PREPROCESSING_INCIDENT_SCHEMA
        or incident.get("status")
        != "incident_detected_pre_freeze_a2_acquisition_stopped"
        or incident.get("incident_sha256") != PREPROCESSING_INCIDENT_SHA256
        or incident.get("code_head_at_detection")
        != PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT
        or incident.get("required_resolution")
        != (
            "prospective_committed_pilot3_specific_deterministic_normalization_"
            "amendment_and_append_only_supersession_before_resume"
        )
    ):
        raise Pilot3PhaseAError("preprocessing-determinism incident identity is stale")
    committed = subprocess.run(
        ["git", "show", f"{PREPROCESSING_INCIDENT_COMMIT}:{PREPROCESSING_INCIDENT_PATH}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREPROCESSING_INCIDENT_COMMIT, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if (
        committed.returncode != 0
        or committed.stdout != path.read_bytes()
        or ancestry.returncode != 0
        or not _git_path_committed_and_clean(root, str(PREPROCESSING_INCIDENT_PATH))
    ):
        raise Pilot3PhaseAError(
            "preprocessing incident is not the exact committed checkpoint"
        )
    _require_git_ancestor(
        root,
        PREPROCESSING_FREEZE_A1_COMMIT,
        PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT,
        "historical browser implementation does not descend from Freeze-A1",
    )
    _require_git_ancestor(
        root,
        PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT,
        PREPROCESSING_INCIDENT_COMMIT,
        "preprocessing incident does not descend from the browser implementation",
    )
    checkpoints = incident.get("ledger_checkpoint")
    if not isinstance(checkpoints, Mapping):
        raise Pilot3PhaseAError("preprocessing incident lacks ledger checkpoints")
    for evidence in checkpoints.values():
        if not isinstance(evidence, Mapping) or not isinstance(evidence.get("path"), str):
            raise Pilot3PhaseAError("preprocessing incident ledger checkpoint is malformed")
        relative = str(evidence["path"])
        current_path = _resolve(root, relative)
        historical = subprocess.run(
            ["git", "show", f"{PREPROCESSING_INCIDENT_COMMIT}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if historical.returncode != 0 or not current_path.is_file():
            raise Pilot3PhaseAError("incident-checkpoint ledger is missing: " + relative)
        current_bytes = current_path.read_bytes()
        if (
            hash_bytes(historical.stdout) != evidence.get("file_sha256")
            or not current_bytes.startswith(historical.stdout)
            or (require_exact_checkpoint and current_bytes != historical.stdout)
        ):
            raise Pilot3PhaseAError("incident-checkpoint ledger prefix changed: " + relative)
        try:
            historical_rows = [
                json.loads(line)
                for line in historical.stdout.decode("utf-8").splitlines()
                if line.strip()
            ]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError(
                "incident-checkpoint ledger blob is not canonical JSONL: " + relative
            ) from exc
        if (
            len(historical_rows) != evidence.get("row_count")
            or stable_hash(historical_rows) != evidence.get("semantic_sha256")
        ):
            raise Pilot3PhaseAError("incident-checkpoint ledger evidence is stale: " + relative)
        last = historical_rows[-1] if historical_rows else None
        last_hash = None
        if isinstance(last, Mapping):
            last_hash = last.get("record_sha256") or last.get("event_sha256")
        if last_hash != evidence.get("last_row_sha256"):
            raise Pilot3PhaseAError("incident-checkpoint ledger tip is stale: " + relative)
    acquisitions = read_jsonl(
        _resolve(root, "artifacts/pilot_3/development_acquisitions.jsonl")
    )[:PREPROCESSING_INCIDENT_ACQUISITION_COUNT]
    bindings = incident.get("acquisition_bindings")
    if not isinstance(bindings, list) or len(bindings) != len(acquisitions):
        raise Pilot3PhaseAError("incident acquisition bindings are incomplete")
    binding_fields = {
        "canonical_work_id",
        "record_sha256",
        "raw_path",
        "raw_sha256",
        "raw_byte_count",
        "normalized_path",
        "normalized_sha256",
        "normalized_byte_count",
    }
    expected_bindings = [
        {key: row[key] for key in binding_fields} for row in acquisitions
    ]
    if bindings != expected_bindings:
        raise Pilot3PhaseAError("incident acquisition bindings changed")
    original = incident.get("original_browser_authorization")
    if (
        not isinstance(original, Mapping)
        or original.get("authorization_sha256")
        != "5964917a97850831bf7da9e8f6a6a9018dc212a770d5279b42e762de9e3df800"
        or original.get("file_sha256")
        != hash_file(_resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH))
    ):
        raise Pilot3PhaseAError("incident original browser authorization binding is stale")
    return incident


def _verify_historical_aic_browser_recovery_authorization(
    root: Path,
    *,
    incident: Mapping[str, Any],
    require_committed: bool,
) -> Dict[str, Any]:
    """Accept the superseded implementation only through the committed incident chain."""

    root = Path(root).expanduser().resolve()
    if incident.get("incident_sha256") != PREPROCESSING_INCIDENT_SHA256:
        raise Pilot3PhaseAError("historical browser authorization lacks the incident gate")
    authorization_path = _resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH)
    historical_authorization = subprocess.run(
        [
            "git",
            "show",
            (
                f"{PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT}:"
                f"{BROWSER_RECOVERY_AUTHORIZATION_PATH}"
            ),
        ],
        cwd=root,
        check=False,
        capture_output=True,
    )
    incident_authorization = subprocess.run(
        [
            "git",
            "show",
            f"{PREPROCESSING_INCIDENT_COMMIT}:{BROWSER_RECOVERY_AUTHORIZATION_PATH}",
        ],
        cwd=root,
        check=False,
        capture_output=True,
    )
    original = incident.get("original_browser_authorization")
    if (
        historical_authorization.returncode != 0
        or incident_authorization.returncode != 0
        or historical_authorization.stdout != incident_authorization.stdout
        or historical_authorization.stdout != authorization_path.read_bytes()
        or not isinstance(original, Mapping)
        or hash_bytes(historical_authorization.stdout) != original.get("file_sha256")
    ):
        raise Pilot3PhaseAError(
            "original browser authorization is not the exact historical Git blob"
        )
    return _verify_aic_browser_recovery_authorization(
        root,
        require_committed=require_committed,
        require_complete_closure=False,
        historical_implementation_commit=(
            PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT
        ),
    )


def _preprocessing_amendment_payload(
    root: Path,
    *,
    original_authorization: Mapping[str, Any],
    incident: Mapping[str, Any],
    remediation_implementation_git_commit: str,
) -> Dict[str, Any]:
    config = load_phase_a_config(root)
    rows = _aic_development_splits(root, config)
    historical = {
        relative: _git_blob_evidence(
            root, PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT, relative
        )
        for relative in PREPROCESSING_HISTORICAL_BLOB_PATHS
    }
    original_implementation = original_authorization[
        "recovery_implementation_file_sha256"
    ]
    for relative, digest in original_implementation.items():
        if historical[str(relative)]["file_sha256"] != digest:
            raise Pilot3PhaseAError(
                "historical browser-recovery blob does not match original authorization"
            )
    if (
        historical["configs/pilot_3/phase_a.json"]["file_sha256"]
        != original_authorization["phase_a_config_file_sha256"]
        or historical["data/manifests/pilot_3/real_splits.jsonl"]["file_sha256"]
        != original_authorization["split_manifest_file_sha256"]
        or hash_file(_resolve(root, DEFAULT_CONFIG))
        != historical["configs/pilot_3/phase_a.json"]["file_sha256"]
        or hash_file(_resolve(root, config["paths"]["split_manifest"]))
        != historical["data/manifests/pilot_3/real_splits.jsonl"]["file_sha256"]
    ):
        raise Pilot3PhaseAError(
            "historical config/split blobs do not match the original authorization"
        )
    for relative in PREPROCESSING_UNCHANGED_BASE_PATHS:
        if hash_file(_resolve(root, relative)) != historical[relative]["file_sha256"]:
            raise Pilot3PhaseAError(
                "preprocessing remediation changed an immutable base path: " + relative
            )
    remediation_implementation = {
        relative: _git_blob_evidence(
            root, remediation_implementation_git_commit, relative
        )["file_sha256"]
        for relative in PREPROCESSING_AMENDMENT_IMPLEMENTATION_PATHS
    }
    for relative in PREPROCESSING_AMENDMENT_CANONICALIZER_PATHS:
        if hash_file(_resolve(root, relative)) != remediation_implementation[relative]:
            raise Pilot3PhaseAError(
                "preprocessing remediation changed an immutable canonicalizer: "
                + relative
            )
    acquired_work_ids = [
        str(binding["canonical_work_id"])
        for binding in incident["acquisition_bindings"]
    ]
    all_work_ids = [str(row["canonical_work_id"]) for row in rows]
    remaining_work_ids = [value for value in all_work_ids if value not in acquired_work_ids]
    if (
        acquired_work_ids != all_work_ids[:PREPROCESSING_INCIDENT_ACQUISITION_COUNT]
        or len(remaining_work_ids) != 8
    ):
        raise Pilot3PhaseAError(
            "incident does not preserve the exact acquired/remaining AIC boundary"
        )
    return {
        "record_type": "pilot3_preprocessing_determinism_amendment",
        "schema_version": PREPROCESSING_AMENDMENT_SCHEMA,
        "status": "prospectively_authorized_before_normalization_correction_or_resume",
        "incident_checkpoint_git_commit": PREPROCESSING_INCIDENT_COMMIT,
        "incident_path": str(PREPROCESSING_INCIDENT_PATH),
        "incident_file_sha256": hash_file(_resolve(root, PREPROCESSING_INCIDENT_PATH)),
        "incident_sha256": incident["incident_sha256"],
        "original_browser_authorization_path": str(
            BROWSER_RECOVERY_AUTHORIZATION_PATH
        ),
        "original_browser_authorization_file_sha256": hash_file(
            _resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH)
        ),
        "original_browser_authorization_sha256": original_authorization[
            "authorization_sha256"
        ],
        "historical_browser_implementation_git_commit": (
            PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT
        ),
        "historical_browser_implementation_blobs": historical,
        "remediation_implementation_file_sha256": remediation_implementation,
        "remediation_implementation_git_commit": (
            remediation_implementation_git_commit
        ),
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "effective_preprocessing_contract": _effective_preprocessing_contract(config),
        "effective_preprocessing_contract_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        "technical_change": (
            "after_embedded_icc_to_srgb_pixel_conversion_detach_rgb_pixels_and_emit_"
            "png_with_only_ihdr_idat_iend_chunks"
        ),
        "historical_acquisition_count": PREPROCESSING_INCIDENT_ACQUISITION_COUNT,
        "historical_acquired_aic_work_ids": acquired_work_ids,
        "remaining_aic_work_ids": remaining_work_ids,
        "required_historical_difference_set": [PREPROCESSING_INCIDENT_WORK_ID],
        "correction_ledger_path": str(NORMALIZATION_REVALIDATION_LEDGER_PATH),
        "provider": original_authorization["provider"],
        "provider_hostname": original_authorization["provider_hostname"],
        "authorization_scope": original_authorization["authorization_scope"],
        "target_count": original_authorization["target_count"],
        "target_bindings": _browser_recovery_target_bindings(rows),
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "split_manifest_file_sha256": hash_file(
            _resolve(root, config["paths"]["split_manifest"])
        ),
        "corpus_url_dimensions_provider_or_partition_changed": False,
        "pixel_transform_or_input_domain_changed": False,
        "pilot2_preprocessing_changed": False,
        "external_holdout_access_authorized": False,
        "browser_network_feature_or_external_operation_performed_by_authorizer": False,
    }


def _require_preprocessing_amendment_prospective_boundary(
    root: Path, incident: Mapping[str, Any]
) -> None:
    """Refuse a technical authorization after downstream work has resumed."""

    state = incident.get("state_boundary")
    if not isinstance(state, Mapping):
        raise Pilot3PhaseAError("preprocessing incident lacks its state boundary")
    absent_path_fields = (
        "determinism_probe_path",
        "development_feature_path",
        "external_unseal_receipt_path",
        "p3_t07_path",
    )
    for field in absent_path_fields:
        value = state.get(field)
        if not isinstance(value, str) or _resolve(root, value).exists():
            raise Pilot3PhaseAError(
                "preprocessing amendment is no longer prospective: " + field
            )
    for field in (
        "determinism_probes_exist",
        "development_features_exist",
        "external_unseal_receipt_exists",
        "external_acquisition_attempts_exist",
        "external_acquisition_intents_exist",
        "external_acquisitions_exist",
        "external_features_exist",
        "external_result_exists",
        "gpt_image_requests_made",
        "gpt_image_transport_opened",
        "p3_t07_exists",
    ):
        if state.get(field) is not False:
            raise Pilot3PhaseAError(
                "preprocessing incident state boundary is not pre-downstream: " + field
            )
    for relative in PREPROCESSING_PROSPECTIVE_FORBIDDEN_PATHS:
        if _resolve(root, relative).exists():
            raise Pilot3PhaseAError(
                "preprocessing amendment is no longer prospective: " + relative
            )
    generation_authorization_path = _resolve(
        root, "configs/pilot_3/generation_authorization.json"
    )
    historical_authorization = subprocess.run(
        [
            "git",
            "show",
            (
                f"{PREPROCESSING_INCIDENT_COMMIT}:configs/pilot_3/generation_authorization.json"
            ),
        ],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if (
        historical_authorization.returncode != 0
        or not generation_authorization_path.is_file()
        or generation_authorization_path.read_bytes() != historical_authorization.stdout
        or not _git_path_committed_and_clean(
            root, "configs/pilot_3/generation_authorization.json"
        )
    ):
        raise Pilot3PhaseAError(
            "preprocessing amendment requires the unchanged closed generation authorization"
        )
    generation_authorization = read_json(generation_authorization_path)
    if (
        not isinstance(generation_authorization, Mapping)
        or generation_authorization.get("status") != "closed"
        or generation_authorization.get("generation_authorization_open") is not False
        or generation_authorization.get("eligible_for_p3_t14") is not False
    ):
        raise Pilot3PhaseAError(
            "preprocessing amendment requires a closed generation authorization"
        )
    verify_self_hash(generation_authorization)
    ancestry = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            PREPROCESSING_HISTORICAL_IMPLEMENTATION_COMMIT,
            PREPROCESSING_INCIDENT_COMMIT,
        ],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise Pilot3PhaseAError(
            "preprocessing incident does not descend from the historical implementation"
        )


def authorize_preprocessing_determinism_amendment(root: Path) -> Dict[str, Any]:
    """Create the prospective technical amendment without image or network I/O."""

    root = Path(root).expanduser().resolve()
    incident = verify_preprocessing_determinism_incident(
        root, require_exact_checkpoint=True
    )
    require_development_freeze(root)
    _require_preprocessing_amendment_prospective_boundary(root, incident)
    original = _verify_historical_aic_browser_recovery_authorization(
        root, incident=incident, require_committed=True
    )
    path = _resolve(root, PREPROCESSING_AMENDMENT_PATH)
    if path.is_file():
        observed = verify_preprocessing_determinism_amendment(
            root, require_committed=False
        )
        return observed
    correction_path = _resolve(root, NORMALIZATION_REVALIDATION_LEDGER_PATH)
    if correction_path.exists():
        raise Pilot3PhaseAError(
            "preprocessing amendment must precede the correction ledger"
        )
    for relative in PREPROCESSING_AMENDMENT_IMPLEMENTATION_PATHS:
        if not _git_path_committed_and_clean(root, relative):
            raise Pilot3PhaseAError(
                "preprocessing remediation implementation is not committed and clean: "
                + relative
            )
    payload = _preprocessing_amendment_payload(
        root,
        original_authorization=original,
        incident=incident,
        remediation_implementation_git_commit=_git_head(root),
    )
    amendment = _self_hash(payload, "authorization_sha256")
    _write_exclusive_json(path, amendment)
    return amendment


def verify_preprocessing_determinism_amendment(
    root: Path, *, require_committed: bool = True
) -> Dict[str, Any]:
    """Verify the immutable v2 technical authorization and its code closure."""

    root = Path(root).expanduser().resolve()
    path = _resolve(root, PREPROCESSING_AMENDMENT_PATH)
    if not path.is_file():
        raise Pilot3PhaseAError("preprocessing-determinism amendment is missing")
    amendment = read_json(path)
    if not isinstance(amendment, dict):
        raise Pilot3PhaseAError("preprocessing-determinism amendment is malformed")
    verify_self_hash(amendment, "authorization_sha256")
    incident = verify_preprocessing_determinism_incident(root)
    original = _verify_historical_aic_browser_recovery_authorization(
        root, incident=incident, require_committed=require_committed
    )
    implementation_commit = amendment.get("remediation_implementation_git_commit")
    if not isinstance(implementation_commit, str) or len(implementation_commit) != 40:
        raise Pilot3PhaseAError(
            "preprocessing amendment lacks its implementation commit"
        )
    expected = _self_hash(
        _preprocessing_amendment_payload(
            root,
            original_authorization=original,
            incident=incident,
            remediation_implementation_git_commit=implementation_commit,
        ),
        "authorization_sha256",
    )
    if amendment != expected:
        raise Pilot3PhaseAError("preprocessing-determinism amendment is stale")
    for relative in PREPROCESSING_AMENDMENT_IMPLEMENTATION_PATHS:
        implementation_blob = subprocess.run(
            ["git", "show", f"{implementation_commit}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if (
            implementation_blob.returncode != 0
            or hash_bytes(implementation_blob.stdout)
            != amendment["remediation_implementation_file_sha256"].get(relative)
        ):
            raise Pilot3PhaseAError(
                "preprocessing remediation implementation commit is stale: " + relative
            )
        if require_committed and not _git_path_committed_and_clean(root, relative):
            raise Pilot3PhaseAError(
                "preprocessing remediation implementation is not committed and clean: "
                + relative
            )
    if require_committed and not _git_path_committed_and_clean(
        root, str(PREPROCESSING_AMENDMENT_PATH)
    ):
        raise Pilot3PhaseAError(
            "preprocessing-determinism amendment is not committed and clean"
        )
    if require_committed:
        amendment_commit = _git_introduction_commit(
            root, str(PREPROCESSING_AMENDMENT_PATH)
        )
        parent = subprocess.run(
            ["git", "rev-parse", f"{amendment_commit}^"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if parent != implementation_commit:
            raise Pilot3PhaseAError(
                "preprocessing amendment was not committed immediately after its "
                "bound implementation"
            )
        _require_git_ancestor(
            root,
            PREPROCESSING_INCIDENT_COMMIT,
            implementation_commit,
            "preprocessing remediation implementation does not descend from the incident",
        )
        amendment_blob = subprocess.run(
            ["git", "show", f"{amendment_commit}:{PREPROCESSING_AMENDMENT_PATH}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if amendment_blob.returncode != 0 or amendment_blob.stdout != path.read_bytes():
            raise Pilot3PhaseAError(
                "preprocessing amendment introduction blob differs from the live artifact"
            )
    return amendment


def _fgetxattr_bytes(descriptor: int, name: str) -> bytes:
    """Read one Darwin extended attribute from an already-open file descriptor."""

    if platform.system() != "Darwin":
        raise Pilot3PhaseAError(
            "AIC browser recovery requires Darwin fgetxattr provenance semantics"
        )
    library = ctypes.CDLL(None, use_errno=True)
    function = library.fgetxattr
    function.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint32,
        ctypes.c_int,
    ]
    function.restype = ctypes.c_ssize_t
    encoded_name = name.encode("utf-8")
    size = int(function(descriptor, encoded_name, None, 0, 0, 0))
    if size < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), name)
    if size <= 0 or size > MAX_WHERE_FROMS_PLIST_BYTES:
        raise Pilot3PhaseAError("browser provenance xattr has an invalid byte size")
    buffer = ctypes.create_string_buffer(size)
    observed = int(function(descriptor, encoded_name, buffer, size, 0, 0))
    if observed < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), name)
    if observed != size:
        raise Pilot3PhaseAError("browser WhereFroms xattr changed while being read")
    return bytes(buffer.raw[:observed])


def _parse_where_froms_binary_plist(payload: bytes) -> List[str]:
    if (
        not payload.startswith(b"bplist00")
        or not payload
        or len(payload) > MAX_WHERE_FROMS_PLIST_BYTES
    ):
        raise Pilot3PhaseAError("browser WhereFroms evidence is not a bounded binary plist")
    try:
        decoded = plistlib.loads(payload, fmt=plistlib.FMT_BINARY)
    except Exception as exc:
        raise Pilot3PhaseAError("browser WhereFroms binary plist cannot be decoded") from exc
    if (
        not isinstance(decoded, list)
        or not decoded
        or len(decoded) > 16
        or any(
            not isinstance(value, str)
            or not value
            or len(value.encode("utf-8")) > 8192
            for value in decoded
        )
    ):
        raise Pilot3PhaseAError("browser WhereFroms plist is not a bounded URL array")
    return list(decoded)


def _parse_quarantine_xattr(payload: bytes) -> Dict[str, Any]:
    if not payload or len(payload) > 4096:
        raise Pilot3PhaseAError("browser quarantine xattr has an invalid byte size")
    try:
        decoded = payload.decode("ascii")
    except UnicodeDecodeError as exc:
        raise Pilot3PhaseAError("browser quarantine xattr is not ASCII") from exc
    fields = decoded.split(";")
    if len(fields) != 4:
        raise Pilot3PhaseAError("browser quarantine xattr has the wrong field count")
    flags, timestamp_hex, agent, identifier = fields
    if (
        len(flags) != 4
        or any(character not in "0123456789abcdefABCDEF" for character in flags)
        or len(timestamp_hex) != 8
        or any(
            character not in "0123456789abcdefABCDEF"
            for character in timestamp_hex
        )
        or len(agent.encode("ascii")) > 256
    ):
        raise Pilot3PhaseAError("browser quarantine flags/timestamp/agent is malformed")
    try:
        parsed_uuid = uuid.UUID(identifier)
    except (ValueError, AttributeError) as exc:
        raise Pilot3PhaseAError("browser quarantine UUID is malformed") from exc
    if str(parsed_uuid).casefold() != identifier.casefold():
        raise Pilot3PhaseAError("browser quarantine UUID is not canonical")
    return {
        "flags_hex": flags.casefold(),
        "download_time_unix_seconds": int(timestamp_hex, 16),
        "agent": agent,
        "uuid": str(parsed_uuid),
    }


def _lexical_absolute_path(path: Path) -> Path:
    expanded = Path(path).expanduser()
    return Path(os.path.abspath(os.fspath(expanded)))


def _browser_file_where_froms(path: Path) -> Tuple[bytes, List[str]]:
    """Probe provenance without following a file symlink."""

    candidate = _lexical_absolute_path(path)
    before = os.lstat(candidate)
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise Pilot3PhaseAError("browser input is not a direct regular non-symlink file")
    if candidate.name.casefold().endswith(".crdownload"):
        raise Pilot3PhaseAError("browser input is an incomplete .crdownload file")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise Pilot3PhaseAError("runtime lacks O_NOFOLLOW for browser provenance")
    descriptor = os.open(candidate, os.O_RDONLY | nofollow)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
        ):
            raise Pilot3PhaseAError("browser input changed before provenance inspection")
        raw_xattr = _fgetxattr_bytes(descriptor, WHERE_FROMS_XATTR)
        urls = _parse_where_froms_binary_plist(raw_xattr)
    finally:
        os.close(descriptor)
    return raw_xattr, urls


def _read_completed_browser_file(
    path: Path,
    config: Mapping[str, Any],
    split: Mapping[str, Any],
) -> Tuple[bytes, bytes, List[str], Dict[str, Any], Dict[str, Any], bytes]:
    """Read xattr and bytes from the same no-follow descriptor, then decode exactly once."""

    candidate = _lexical_absolute_path(path)
    before = os.lstat(candidate)
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise Pilot3PhaseAError("browser input is not a direct regular non-symlink file")
    if candidate.name.casefold().endswith(".crdownload"):
        raise Pilot3PhaseAError("browser input is an incomplete .crdownload file")
    maximum = _acquisition_response_limit(config)
    if before.st_size <= 0 or before.st_size > maximum:
        raise Pilot3PhaseAError("browser input violates the frozen response-byte cap")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise Pilot3PhaseAError("runtime lacks O_NOFOLLOW for browser provenance")
    descriptor = os.open(candidate, os.O_RDONLY | nofollow)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
            or opened.st_size != before.st_size
        ):
            raise Pilot3PhaseAError("browser input changed before same-fd import")
        raw_xattr = _fgetxattr_bytes(descriptor, WHERE_FROMS_XATTR)
        urls = _parse_where_froms_binary_plist(raw_xattr)
        if str(split["image_url"]) not in urls:
            raise Pilot3PhaseAError(
                "browser WhereFroms does not contain the exact frozen image URL"
            )
        chunks: List[bytes] = []
        count = 0
        while True:
            chunk = os.read(descriptor, HTTP_STREAM_CHUNK_BYTES)
            if not chunk:
                break
            count += len(chunk)
            if count > maximum:
                raise Pilot3PhaseAError(
                    "browser input exceeds the frozen response-byte cap while reading"
                )
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            after.st_dev != opened.st_dev
            or after.st_ino != opened.st_ino
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or count != opened.st_size
        ):
            raise Pilot3PhaseAError("browser input changed during same-fd import")
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    decode, normalized = _decode_and_normalize(
        payload,
        config,
        expected_width=int(split["delivery_width"]),
        expected_height=int(split["delivery_height"]),
    )
    if decode["decoded_format"] != "jpeg":
        raise Pilot3PhaseAError("AIC browser input is not a decoded JPEG image")
    stat_evidence = {
        "device": opened.st_dev,
        "inode": opened.st_ino,
        "mode": opened.st_mode,
        "size": opened.st_size,
        "mtime_ns": opened.st_mtime_ns,
    }
    return payload, raw_xattr, urls, stat_evidence, decode, normalized


def _read_bound_browser_download(
    download_directory: Path,
    start: Mapping[str, Any],
    config: Mapping[str, Any],
    split: Mapping[str, Any],
) -> Tuple[
    Path,
    bytes,
    bytes,
    List[str],
    bytes,
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    bytes,
]:
    """Read the sole post-start direct file through its bound directory descriptor."""

    directory = _lexical_absolute_path(download_directory)
    if str(directory) != start.get("download_directory_path"):
        raise Pilot3PhaseAError("import directory differs from the prepared directory")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    odirectory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or odirectory is None:
        raise Pilot3PhaseAError("runtime lacks no-follow directory descriptors")
    directory_descriptor = os.open(directory, os.O_RDONLY | nofollow | odirectory)
    try:
        directory_stat = _directory_stat_evidence(os.fstat(directory_descriptor))
        start_stat = start.get("download_directory_stat_at_start")
        if (
            not isinstance(start_stat, Mapping)
            or directory_stat["device"] != start_stat.get("device")
            or directory_stat["inode"] != start_stat.get("inode")
            or not stat.S_ISDIR(directory_stat["mode"])
        ):
            raise Pilot3PhaseAError("prepared browser directory identity was replaced")
        names = sorted(os.listdir(directory_descriptor))
        if len(names) != 1:
            raise Pilot3PhaseAError(
                "prepared browser directory must contain exactly one newly appearing file"
            )
        name = names[0]
        if not name or "/" in name or name.casefold().endswith(".crdownload"):
            raise Pilot3PhaseAError("prepared browser file name is incomplete or malformed")
        listed_stat = os.stat(
            name, dir_fd=directory_descriptor, follow_symlinks=False
        )
        if not stat.S_ISREG(listed_stat.st_mode) or stat.S_ISLNK(listed_stat.st_mode):
            raise Pilot3PhaseAError("prepared browser entry is not a direct regular file")
        maximum = _acquisition_response_limit(config)
        if listed_stat.st_size <= 0 or listed_stat.st_size > maximum:
            raise Pilot3PhaseAError("browser input violates the frozen response-byte cap")
        file_descriptor = os.open(
            name,
            os.O_RDONLY | nofollow,
            dir_fd=directory_descriptor,
        )
        try:
            opened = os.fstat(file_descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != listed_stat.st_dev
                or opened.st_ino != listed_stat.st_ino
                or opened.st_size != listed_stat.st_size
            ):
                raise Pilot3PhaseAError("browser file changed before same-fd import")
            source_stat = _directory_stat_evidence(opened)
            raw_where_froms = _fgetxattr_bytes(file_descriptor, WHERE_FROMS_XATTR)
            urls = _parse_where_froms_binary_plist(raw_where_froms)
            if str(split["image_url"]) not in urls:
                raise Pilot3PhaseAError(
                    "browser WhereFroms does not contain the exact frozen image URL"
                )
            raw_quarantine = _fgetxattr_bytes(file_descriptor, QUARANTINE_XATTR)
            quarantine = _parse_quarantine_xattr(raw_quarantine)
            start_seconds = int(start["start_not_before_wall_time_ns"]) // 1_000_000_000
            if (
                source_stat["birthtime_ns"] // 1_000_000_000 < start_seconds
                or source_stat["ctime_ns"] // 1_000_000_000 < start_seconds
                or int(quarantine["download_time_unix_seconds"]) < start_seconds
            ):
                raise Pilot3PhaseAError(
                    "browser candidate predates its fsynced attempt start"
                )
            chunks: List[bytes] = []
            count = 0
            while True:
                chunk = os.read(file_descriptor, HTTP_STREAM_CHUNK_BYTES)
                if not chunk:
                    break
                count += len(chunk)
                if count > maximum:
                    raise Pilot3PhaseAError(
                        "browser input exceeds the frozen byte cap while reading"
                    )
                chunks.append(chunk)
            after = os.fstat(file_descriptor)
            if (
                after.st_dev != opened.st_dev
                or after.st_ino != opened.st_ino
                or after.st_size != opened.st_size
                or after.st_mtime_ns != opened.st_mtime_ns
                or after.st_ctime_ns != opened.st_ctime_ns
                or count != opened.st_size
            ):
                raise Pilot3PhaseAError("browser input changed during same-fd import")
        finally:
            os.close(file_descriptor)
        after_directory = _directory_stat_evidence(os.fstat(directory_descriptor))
        if (
            after_directory["device"] != directory_stat["device"]
            or after_directory["inode"] != directory_stat["inode"]
            or sorted(os.listdir(directory_descriptor)) != [name]
        ):
            raise Pilot3PhaseAError("browser directory changed during import")
    finally:
        os.close(directory_descriptor)
    payload = b"".join(chunks)
    decode, normalized = _decode_and_normalize(
        payload,
        config,
        expected_width=int(split["delivery_width"]),
        expected_height=int(split["delivery_height"]),
    )
    if decode["decoded_format"] != "jpeg":
        raise Pilot3PhaseAError("AIC browser input is not a decoded JPEG image")
    return (
        directory / name,
        payload,
        raw_where_froms,
        urls,
        raw_quarantine,
        quarantine,
        source_stat,
        after_directory,
        decode,
        normalized,
    )


def _read_canonical_browser_events(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    payload = path.read_bytes()
    if not payload:
        return []
    if not payload.endswith(b"\n"):
        raise Pilot3PhaseAError("browser recovery ledger has a torn final row")
    if b"\r" in payload:
        raise Pilot3PhaseAError("browser recovery ledger has non-canonical newlines")
    events: List[Dict[str, Any]] = []
    for index, raw_line in enumerate(payload.splitlines(), start=1):
        try:
            decoded = raw_line.decode("utf-8")
            row = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError(
                f"browser recovery event {index} is not canonical JSON"
            ) from exc
        if not isinstance(row, dict) or canonical_json(row) != decoded:
            raise Pilot3PhaseAError(
                f"browser recovery event {index} is not a canonical JSON object"
            )
        events.append(row)
    return events


def _directory_stat_evidence(value: os.stat_result) -> Dict[str, Any]:
    birthtime = getattr(value, "st_birthtime", None)
    if birthtime is None:
        raise Pilot3PhaseAError("Darwin directory/file birthtime evidence is unavailable")
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": value.st_mode,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
        "birthtime_ns": int(float(birthtime) * 1_000_000_000),
    }


def _read_directory_intents(path: Path) -> List[Dict[str, Any]]:
    rows = _read_canonical_browser_events(path)
    previous: Optional[str] = None
    prior: List[Dict[str, Any]] = []
    seen_works: set[str] = set()
    seen_paths: set[str] = set()
    for sequence, row in enumerate(rows, start=1):
        required = {
            "record_type",
            "schema_version",
            "directory_intent_sequence",
            "previous_directory_intent_sha256",
            "expected_ledger_prefix_sha256",
            "authorization_sha256",
            "canonical_work_id",
            "download_directory_path",
            "directory_must_not_exist_at_intent_write",
            "intent_written_before_mkdir_wall_time_ns",
            "directory_intent_id",
            "record_sha256",
        }
        if set(row) != required:
            raise Pilot3PhaseAError("browser directory-intent field set is stale")
        verify_self_hash(row, "record_sha256")
        work_id = str(row.get("canonical_work_id", ""))
        if (
            row.get("record_type") != "pilot3_browser_download_directory_intent"
            or row.get("schema_version") != BROWSER_RECOVERY_SCHEMA
            or row.get("directory_intent_sequence") != sequence
            or row.get("previous_directory_intent_sha256") != previous
            or row.get("expected_ledger_prefix_sha256") != stable_hash(prior)
            or row.get("directory_must_not_exist_at_intent_write") is not True
            or type(row.get("intent_written_before_mkdir_wall_time_ns")) is not int
            or int(row["intent_written_before_mkdir_wall_time_ns"]) <= 0
            or not isinstance(row.get("download_directory_path"), str)
            or not Path(str(row["download_directory_path"])).is_absolute()
            or work_id in seen_works
            or str(row["download_directory_path"]) in seen_paths
        ):
            raise Pilot3PhaseAError("browser directory-intent ledger is stale")
        identity = {
            "authorization_sha256": row["authorization_sha256"],
            "canonical_work_id": work_id,
            "download_directory_path": row["download_directory_path"],
        }
        if row.get("directory_intent_id") != (
            f"p3-browser-dir-{stable_hash(identity)[:24]}"
        ):
            raise Pilot3PhaseAError("browser directory-intent identity is stale")
        prior.append(row)
        previous = str(row["record_sha256"])
        seen_works.add(work_id)
        seen_paths.add(str(row["download_directory_path"]))
    return rows


def _browser_directory_intent(
    authorization: Mapping[str, Any],
    canonical_work_id: str,
    download_directory: Path,
    prior: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    absolute = str(_lexical_absolute_path(download_directory))
    identity = {
        "authorization_sha256": authorization["authorization_sha256"],
        "canonical_work_id": canonical_work_id,
        "download_directory_path": absolute,
    }
    payload = {
        "record_type": "pilot3_browser_download_directory_intent",
        "schema_version": BROWSER_RECOVERY_SCHEMA,
        "directory_intent_sequence": len(prior) + 1,
        "previous_directory_intent_sha256": (
            prior[-1]["record_sha256"] if prior else None
        ),
        "expected_ledger_prefix_sha256": stable_hash(list(prior)),
        **identity,
        "directory_must_not_exist_at_intent_write": True,
        "intent_written_before_mkdir_wall_time_ns": time.time_ns(),
        "directory_intent_id": f"p3-browser-dir-{stable_hash(identity)[:24]}",
    }
    return _self_hash(payload, "record_sha256")


def _browser_attempt_start(
    *,
    authorization: Mapping[str, Any],
    split: Mapping[str, Any],
    intent: Mapping[str, Any],
    directory_intent: Mapping[str, Any],
    download_directory_stat: Mapping[str, Any],
    start_not_before_wall_time_ns: int,
    start_not_before_monotonic_ns: int,
    event_sequence: int,
    previous_event_sha256: Optional[str],
    prior_events: Sequence[Mapping[str, Any]],
    normalization_amendment: Optional[Mapping[str, Any]] = None,
    effective_preprocessing_contract_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    identity = {
        "authorization_sha256": authorization["authorization_sha256"],
        "canonical_work_id": split["canonical_work_id"],
        "intent_id": intent["intent_id"],
        "intent_sha256": stable_hash(intent),
        "image_url": split["image_url"],
    }
    if normalization_amendment is not None:
        if not _is_sha256(effective_preprocessing_contract_sha256):
            raise Pilot3PhaseAError(
                "v2 browser start lacks the effective preprocessing contract"
            )
        identity["preprocessing_determinism_amendment_sha256"] = (
            normalization_amendment["authorization_sha256"]
        )
    payload = {
        "record_type": "pilot3_real_acquisition_browser_attempt_start",
        "schema_version": BROWSER_RECOVERY_SCHEMA,
        "event_type": "start",
        "event_sequence": event_sequence,
        "previous_event_sha256": previous_event_sha256,
        "expected_ledger_prefix_sha256": stable_hash(list(prior_events)),
        **identity,
        "browser_attempt_id": f"p3-real-browser-{stable_hash(identity)[:24]}",
        "directory_intent_id": directory_intent["directory_intent_id"],
        "directory_intent_record_sha256": directory_intent["record_sha256"],
        "download_directory_path": directory_intent["download_directory_path"],
        "download_directory_stat_at_start": dict(download_directory_stat),
        "empty_directory_snapshot": {
            "direct_entry_names": [],
            "direct_entry_names_sha256": stable_hash([]),
        },
        "directory_created_exclusively_by_prepare": True,
        "start_not_before_wall_time_ns": start_not_before_wall_time_ns,
        "start_not_before_monotonic_ns": start_not_before_monotonic_ns,
        "acquisition_intent_route": intent["acquisition_route"],
        "artist_id": split["artist_id"],
        "asset_provider": split["asset_provider"],
        "source_id": split["source_id"],
        "partition": split["partition"],
        "source_url": split["source_url"],
        "delivery_width": split["delivery_width"],
        "delivery_height": split["delivery_height"],
        "browser_action": "navigate_exact_frozen_image_url_then_download",
        "where_froms_xattr_required": WHERE_FROMS_XATTR,
        "max_response_bytes": MAX_HTTP_RESPONSE_BYTES,
        "external_holdout_access_authorized": False,
        "browser_navigation_or_download_performed_by_start_writer": False,
    }
    if normalization_amendment is not None:
        payload.update(
            {
                "normalization_protocol_version": (
                    PILOT3_NORMALIZATION_PROTOCOL_VERSION
                ),
                "preprocessing_determinism_amendment_sha256": (
                    normalization_amendment["authorization_sha256"]
                ),
                "effective_preprocessing_contract_sha256": (
                    effective_preprocessing_contract_sha256
                ),
            }
        )
    return _self_hash(payload, "event_sha256")


def _browser_attempt_terminal(
    start: Mapping[str, Any],
    *,
    source_file: Path,
    source_file_stat: Mapping[str, Any],
    raw_xattr: bytes,
    where_froms_urls: Sequence[str],
    raw_quarantine_xattr: bytes,
    quarantine_evidence: Mapping[str, Any],
    download_directory_stat_at_import: Mapping[str, Any],
    payload: bytes,
    raw_path: Path,
    decode: Mapping[str, Any],
    normalized: bytes,
    normalized_path: Path,
    root: Path,
    prior_events: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    record = {
        "record_type": "pilot3_real_acquisition_browser_attempt_terminal",
        "schema_version": BROWSER_RECOVERY_SCHEMA,
        "event_type": "terminal",
        "event_sequence": len(prior_events) + 1,
        "previous_event_sha256": (
            prior_events[-1]["event_sha256"] if prior_events else None
        ),
        "expected_ledger_prefix_sha256": stable_hash(list(prior_events)),
        "authorization_sha256": start["authorization_sha256"],
        "canonical_work_id": start["canonical_work_id"],
        "intent_id": start["intent_id"],
        "intent_sha256": start["intent_sha256"],
        "image_url": start["image_url"],
        "browser_attempt_id": start["browser_attempt_id"],
        "start_event_sha256": start["event_sha256"],
        "outcome": "imported_exact_browser_download",
        "browser_transport": "darwin_browser_download_wherefroms_import",
        "source_file_path": str(_lexical_absolute_path(source_file)),
        "source_file_stat": dict(source_file_stat),
        "download_directory_path": start["download_directory_path"],
        "download_directory_stat_at_import": dict(
            download_directory_stat_at_import
        ),
        "candidate_direct_entry_name": source_file.name,
        "where_froms_plist_base64": base64.b64encode(raw_xattr).decode("ascii"),
        "where_froms_plist_byte_count": len(raw_xattr),
        "where_froms_plist_sha256": hash_bytes(raw_xattr),
        "where_froms_urls": list(where_froms_urls),
        "quarantine_xattr_base64": base64.b64encode(raw_quarantine_xattr).decode(
            "ascii"
        ),
        "quarantine_xattr_byte_count": len(raw_quarantine_xattr),
        "quarantine_xattr_sha256": hash_bytes(raw_quarantine_xattr),
        "quarantine_evidence": dict(quarantine_evidence),
        "freshness_not_before_wall_time_ns": start[
            "start_not_before_wall_time_ns"
        ],
        "raw_path": _portable(raw_path, root),
        "raw_sha256": hash_bytes(payload),
        "raw_byte_count": len(payload),
        "normalized_path": _portable(normalized_path, root),
        "normalized_sha256": hash_bytes(normalized),
        "normalized_byte_count": len(normalized),
        "decode_evidence": dict(decode),
        "external_holdout_accessed": False,
        "httpx_success_claimed": False,
    }
    for key in (
        "normalization_protocol_version",
        "preprocessing_determinism_amendment_sha256",
        "normalization_authorization_schema",
        "normalization_authorization_sha256",
        "effective_preprocessing_contract_sha256",
    ):
        if key in start:
            record[key] = start[key]
    return _self_hash(record, "event_sha256")


def _normalized_rgb_pixel_sha256(payload: bytes) -> str:
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            if image.format != "PNG" or image.mode != "RGB":
                raise Pilot3PhaseAError("normalized evidence is not an RGB PNG")
            return hash_bytes(image.tobytes())
    except Pilot3PhaseAError:
        raise
    except Exception as exc:
        raise Pilot3PhaseAError("normalized RGB pixel evidence cannot be decoded") from exc


def _validate_browser_attempt_terminal(
    root: Path,
    config: Mapping[str, Any],
    start: Mapping[str, Any],
    terminal: Mapping[str, Any],
    prior_events: Sequence[Mapping[str, Any]],
) -> None:
    required = {
        "record_type",
        "schema_version",
        "event_type",
        "event_sequence",
        "previous_event_sha256",
        "expected_ledger_prefix_sha256",
        "authorization_sha256",
        "canonical_work_id",
        "intent_id",
        "intent_sha256",
        "image_url",
        "browser_attempt_id",
        "start_event_sha256",
        "outcome",
        "browser_transport",
        "source_file_path",
        "source_file_stat",
        "download_directory_path",
        "download_directory_stat_at_import",
        "candidate_direct_entry_name",
        "where_froms_plist_base64",
        "where_froms_plist_byte_count",
        "where_froms_plist_sha256",
        "where_froms_urls",
        "quarantine_xattr_base64",
        "quarantine_xattr_byte_count",
        "quarantine_xattr_sha256",
        "quarantine_evidence",
        "freshness_not_before_wall_time_ns",
        "raw_path",
        "raw_sha256",
        "raw_byte_count",
        "normalized_path",
        "normalized_sha256",
        "normalized_byte_count",
        "decode_evidence",
        "external_holdout_accessed",
        "httpx_success_claimed",
        "event_sha256",
    }
    versioned_fields = {
        "normalization_protocol_version",
        "preprocessing_determinism_amendment_sha256",
        "effective_preprocessing_contract_sha256",
    }
    start_is_v2 = start.get("normalization_protocol_version") is not None
    if start_is_v2:
        required.update(versioned_fields)
    if set(terminal) != required:
        raise Pilot3PhaseAError("browser attempt terminal field set is stale")
    verify_self_hash(terminal, "event_sha256")
    if (
        terminal.get("record_type")
        != "pilot3_real_acquisition_browser_attempt_terminal"
        or terminal.get("schema_version") != BROWSER_RECOVERY_SCHEMA
        or terminal.get("event_type") != "terminal"
        or terminal.get("event_sequence") != len(prior_events) + 1
        or terminal.get("previous_event_sha256")
        != (prior_events[-1]["event_sha256"] if prior_events else None)
        or terminal.get("expected_ledger_prefix_sha256")
        != stable_hash(list(prior_events))
        or terminal.get("start_event_sha256") != start.get("event_sha256")
        or any(
            terminal.get(key) != start.get(key)
            for key in (
                "authorization_sha256",
                "canonical_work_id",
                "intent_id",
                "intent_sha256",
                "image_url",
                "browser_attempt_id",
            )
        )
        or terminal.get("outcome") != "imported_exact_browser_download"
        or terminal.get("browser_transport")
        != "darwin_browser_download_wherefroms_import"
        or terminal.get("external_holdout_accessed") is not False
        or terminal.get("httpx_success_claimed") is not False
    ):
        raise Pilot3PhaseAError("browser attempt terminal does not bind its start")
    if start_is_v2 and (
        terminal.get("normalization_protocol_version")
        != PILOT3_NORMALIZATION_PROTOCOL_VERSION
        or any(terminal.get(key) != start.get(key) for key in versioned_fields)
    ):
        raise Pilot3PhaseAError("browser terminal lacks its v2 amendment lineage")
    source_file_path = terminal.get("source_file_path")
    source_stat = terminal.get("source_file_stat")
    stat_fields = {
        "device",
        "inode",
        "mode",
        "size",
        "mtime_ns",
        "ctime_ns",
        "birthtime_ns",
    }
    directory_stat = terminal.get("download_directory_stat_at_import")
    if (
        not isinstance(source_file_path, str)
        or not Path(source_file_path).is_absolute()
        or not isinstance(source_stat, Mapping)
        or set(source_stat) != stat_fields
        or any(type(source_stat.get(key)) is not int for key in source_stat)
        or not stat.S_ISREG(int(source_stat["mode"]))
        or int(source_stat["size"]) != terminal.get("raw_byte_count")
        or terminal.get("download_directory_path")
        != start.get("download_directory_path")
        or not isinstance(directory_stat, Mapping)
        or set(directory_stat) != stat_fields
        or any(type(directory_stat.get(key)) is not int for key in directory_stat)
        or not stat.S_ISDIR(int(directory_stat["mode"]))
        or directory_stat.get("device")
        != start.get("download_directory_stat_at_start", {}).get("device")
        or directory_stat.get("inode")
        != start.get("download_directory_stat_at_start", {}).get("inode")
        or not isinstance(terminal.get("candidate_direct_entry_name"), str)
        or not terminal.get("candidate_direct_entry_name")
        or Path(source_file_path).name != terminal.get("candidate_direct_entry_name")
        or str(Path(source_file_path).parent)
        != terminal.get("download_directory_path")
    ):
        raise Pilot3PhaseAError("browser source-file evidence is malformed")
    encoded_plist = terminal.get("where_froms_plist_base64")
    if not isinstance(encoded_plist, str):
        raise Pilot3PhaseAError("browser WhereFroms base64 evidence is malformed")
    try:
        raw_xattr = base64.b64decode(encoded_plist, validate=True)
    except Exception as exc:
        raise Pilot3PhaseAError("browser WhereFroms base64 evidence cannot be decoded") from exc
    urls = _parse_where_froms_binary_plist(raw_xattr)
    if (
        terminal.get("where_froms_plist_byte_count") != len(raw_xattr)
        or terminal.get("where_froms_plist_sha256") != hash_bytes(raw_xattr)
        or terminal.get("where_froms_urls") != urls
        or start["image_url"] not in urls
    ):
        raise Pilot3PhaseAError("browser WhereFroms evidence is stale or URL-mismatched")
    encoded_quarantine = terminal.get("quarantine_xattr_base64")
    if not isinstance(encoded_quarantine, str):
        raise Pilot3PhaseAError("browser quarantine base64 evidence is malformed")
    try:
        raw_quarantine = base64.b64decode(encoded_quarantine, validate=True)
    except Exception as exc:
        raise Pilot3PhaseAError("browser quarantine base64 cannot be decoded") from exc
    quarantine = _parse_quarantine_xattr(raw_quarantine)
    start_ns = start.get("start_not_before_wall_time_ns")
    start_seconds = (
        int(start_ns) // 1_000_000_000 if type(start_ns) is int else -1
    )
    if (
        terminal.get("quarantine_xattr_byte_count") != len(raw_quarantine)
        or terminal.get("quarantine_xattr_sha256") != hash_bytes(raw_quarantine)
        or terminal.get("quarantine_evidence") != quarantine
        or terminal.get("freshness_not_before_wall_time_ns") != start_ns
        or source_stat["birthtime_ns"] // 1_000_000_000 < start_seconds
        or source_stat["ctime_ns"] // 1_000_000_000 < start_seconds
        or quarantine["download_time_unix_seconds"] < start_seconds
    ):
        raise Pilot3PhaseAError("browser quarantine/freshness evidence is stale")
    raw_sha = terminal.get("raw_sha256")
    raw_count = terminal.get("raw_byte_count")
    if not _is_sha256(raw_sha) or type(raw_count) is not int or raw_count <= 0:
        raise Pilot3PhaseAError("browser raw-byte evidence is malformed")
    expected_raw_path = (
        _resolve(root, config["paths"]["raw_dir"])
        / str(raw_sha)[:2]
        / f"{raw_sha}.bin"
    )
    if (
        terminal.get("raw_path") != _portable(expected_raw_path, root)
        or not expected_raw_path.is_file()
        or expected_raw_path.stat().st_size != raw_count
        or hash_file(expected_raw_path) != raw_sha
    ):
        raise Pilot3PhaseAError("browser raw CAS object is missing or stale")
    payload = expected_raw_path.read_bytes()
    split = {
        "delivery_width": start["delivery_width"],
        "delivery_height": start["delivery_height"],
    }
    decode, normalized = _decode_and_normalize(
        payload,
        config,
        expected_width=int(split["delivery_width"]),
        expected_height=int(split["delivery_height"]),
    )
    if decode.get("decoded_format") != "jpeg" or terminal.get("decode_evidence") != decode:
        raise Pilot3PhaseAError("browser decoded JPEG evidence is stale")
    normalized_sha = hash_bytes(normalized)
    recorded_normalized_sha = terminal.get("normalized_sha256")
    if not _is_sha256(recorded_normalized_sha):
        raise Pilot3PhaseAError("browser normalized SHA is malformed")
    recorded_normalized_path = (
        _resolve(root, config["paths"]["normalized_dir"])
        / str(recorded_normalized_sha)[:2]
        / f"{recorded_normalized_sha}.png"
    )
    if (
        terminal.get("normalized_path")
        != _portable(recorded_normalized_path, root)
        or not recorded_normalized_path.is_file()
        or recorded_normalized_path.stat().st_size
        != terminal.get("normalized_byte_count")
        or hash_file(recorded_normalized_path) != recorded_normalized_sha
    ):
        raise Pilot3PhaseAError("browser normalized CAS object is missing or stale")
    if terminal.get("normalization_protocol_version") is None:
        recorded = recorded_normalized_path.read_bytes()
        if _normalized_rgb_pixel_sha256(recorded) != _normalized_rgb_pixel_sha256(
            normalized
        ):
            raise Pilot3PhaseAError(
                "historical browser normalized pixels differ from v2 recomputation"
            )
        changed = recorded_normalized_sha != normalized_sha
        if changed != (
            terminal.get("canonical_work_id") == PREPROCESSING_INCIDENT_WORK_ID
        ):
            raise Pilot3PhaseAError(
                "historical browser normalization difference set is stale"
            )
    elif (
        terminal.get("normalization_protocol_version")
        != PILOT3_NORMALIZATION_PROTOCOL_VERSION
        or terminal.get("normalized_sha256") != normalized_sha
        or terminal.get("normalized_byte_count") != len(normalized)
    ):
        raise Pilot3PhaseAError("browser v2 normalization evidence is stale")


def _verified_browser_attempt_histories(
    root: Path,
    config: Mapping[str, Any],
    authorization: Mapping[str, Any],
    intents: Mapping[str, Mapping[str, Any]],
    *,
    normalization_amendment: Optional[Mapping[str, Any]] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    rows = _aic_development_splits(root, config)
    rows_by_work = {str(row["canonical_work_id"]): row for row in rows}
    histories: Dict[str, List[Dict[str, Any]]] = {
        str(intent["intent_id"]): []
        for intent in intents.values()
        if str(intent.get("canonical_work_id", "")) in rows_by_work
    }
    events = _read_canonical_browser_events(
        _resolve(root, BROWSER_RECOVERY_LEDGER_PATH)
    )
    directory_intents = _read_directory_intents(
        _resolve(root, BROWSER_DIRECTORY_INTENT_LEDGER_PATH)
    )
    directory_intents_by_id = {
        str(row["directory_intent_id"]): row for row in directory_intents
    }
    previous: Optional[str] = None
    prior_events: List[Dict[str, Any]] = []
    starts_by_attempt: Dict[str, Dict[str, Any]] = {}
    terminal_attempts: set[str] = set()
    work_starts: set[str] = set()
    active_start: Optional[Dict[str, Any]] = None
    for sequence, event in enumerate(events, start=1):
        if (
            event.get("event_sequence") != sequence
            or event.get("previous_event_sha256") != previous
            or event.get("expected_ledger_prefix_sha256")
            != stable_hash(prior_events)
        ):
            raise Pilot3PhaseAError("browser recovery ledger chain or CAS prefix is stale")
        event_type = event.get("event_type")
        if event_type == "start":
            if active_start is not None:
                raise Pilot3PhaseAError(
                    "browser recovery journal has multiple unmatched starts"
                )
            work_id = str(event.get("canonical_work_id", ""))
            intent_id = str(event.get("intent_id", ""))
            split = rows_by_work.get(work_id)
            intent = intents.get(intent_id)
            if split is None or intent is None or work_id in work_starts:
                raise Pilot3PhaseAError(
                    "browser attempt start is duplicate or outside the AIC scope"
                )
            directory_intent = directory_intents_by_id.get(
                str(event.get("directory_intent_id", ""))
            )
            directory_stat = event.get("download_directory_stat_at_start")
            if (
                directory_intent is None
                or directory_intent.get("record_sha256")
                != event.get("directory_intent_record_sha256")
                or directory_intent.get("canonical_work_id") != work_id
                or directory_intent.get("authorization_sha256")
                != authorization.get("authorization_sha256")
                or not isinstance(directory_stat, Mapping)
                or set(directory_stat)
                != {
                    "device",
                    "inode",
                    "mode",
                    "size",
                    "mtime_ns",
                    "ctime_ns",
                    "birthtime_ns",
                }
                or any(type(value) is not int for value in directory_stat.values())
                or not stat.S_ISDIR(int(directory_stat["mode"]))
                or event.get("empty_directory_snapshot")
                != {
                    "direct_entry_names": [],
                    "direct_entry_names_sha256": stable_hash([]),
                }
                or event.get("directory_created_exclusively_by_prepare") is not True
                or type(event.get("start_not_before_wall_time_ns")) is not int
                or type(event.get("start_not_before_monotonic_ns")) is not int
                or int(event["start_not_before_wall_time_ns"])
                < int(directory_intent["intent_written_before_mkdir_wall_time_ns"])
            ):
                raise Pilot3PhaseAError("browser start directory evidence is malformed")
            event_is_v2 = event.get("normalization_protocol_version") is not None
            historical_work_ids = {
                str(row["canonical_work_id"])
                for row in rows[:PREPROCESSING_INCIDENT_ACQUISITION_COUNT]
            }
            if event_is_v2:
                if (
                    normalization_amendment is None
                    or event.get("normalization_protocol_version")
                    != PILOT3_NORMALIZATION_PROTOCOL_VERSION
                    or event.get("preprocessing_determinism_amendment_sha256")
                    != normalization_amendment.get("authorization_sha256")
                    or event.get("effective_preprocessing_contract_sha256")
                    != _effective_preprocessing_contract_sha256(config)
                ):
                    raise Pilot3PhaseAError(
                        "browser start lacks the authorized v2 normalization lineage"
                    )
            elif work_id not in historical_work_ids or sequence > 23:
                raise Pilot3PhaseAError(
                    "post-incident browser start lacks the v2 technical amendment"
                )
            expected = _browser_attempt_start(
                authorization=authorization,
                split=split,
                intent=intent,
                directory_intent=directory_intent,
                download_directory_stat=directory_stat,
                start_not_before_wall_time_ns=int(
                    event["start_not_before_wall_time_ns"]
                ),
                start_not_before_monotonic_ns=int(
                    event["start_not_before_monotonic_ns"]
                ),
                event_sequence=sequence,
                previous_event_sha256=previous,
                prior_events=prior_events,
                normalization_amendment=(
                    normalization_amendment if event_is_v2 else None
                ),
                effective_preprocessing_contract_sha256=(
                    _effective_preprocessing_contract_sha256(config)
                    if event_is_v2
                    else None
                ),
            )
            if event != expected:
                raise Pilot3PhaseAError("browser attempt start is stale")
            attempt_id = str(event["browser_attempt_id"])
            if attempt_id in starts_by_attempt:
                raise Pilot3PhaseAError("browser attempt identity is duplicated")
            starts_by_attempt[attempt_id] = event
            work_starts.add(work_id)
            histories[intent_id].append(event)
            active_start = event
        elif event_type == "terminal":
            attempt_id = str(event.get("browser_attempt_id", ""))
            start = starts_by_attempt.get(attempt_id)
            if (
                start is None
                or attempt_id in terminal_attempts
                or active_start is None
                or active_start.get("browser_attempt_id") != attempt_id
            ):
                raise Pilot3PhaseAError(
                    "browser terminal lacks a unique preceding attempt start"
                )
            _validate_browser_attempt_terminal(root, config, start, event, prior_events)
            histories[str(start["intent_id"])].append(event)
            terminal_attempts.add(attempt_id)
            active_start = None
        else:
            raise Pilot3PhaseAError("browser recovery event has an unknown type")
        prior_events.append(event)
        previous = str(event.get("event_sha256", ""))
    return histories


def prepare_aic_browser_recovery(
    root: Path, canonical_work_id: str, download_directory: Path
) -> Dict[str, Any]:
    """Fsync one exact browser intent/start before that work's fresh navigation."""

    root = Path(root).expanduser().resolve()
    requested_directory = _lexical_absolute_path(download_directory)
    with _acquisition_phase_lock(root, "development"):
        resolution = require_preprocessing_incident_resolution(root)
        require_development_freeze(root)
        amendment = resolution["amendment"]
        incident = verify_preprocessing_determinism_incident(root)
        authorization = _verify_historical_aic_browser_recovery_authorization(
            root, incident=incident, require_committed=True
        )
        config = load_phase_a_config(root)
        rows = _aic_development_splits(root, config)
        rows_by_work = {str(row["canonical_work_id"]): row for row in rows}
        split = rows_by_work.get(canonical_work_id)
        if split is None:
            raise Pilot3PhaseAError(
                "browser prepare work is not in the frozen AIC development scope"
            )
        acquisition_path = _phase_ledger_path(
            root, config, "development", "acquisitions"
        )
        acquisitions = _read_existing_rows(acquisition_path, "canonical_work_id")
        if canonical_work_id in acquisitions:
            raise Pilot3PhaseAError(
                "browser prepare target is already acquired: " + canonical_work_id
            )
        intent_path = _phase_ledger_path(
            root, config, "development", "acquisition_intents"
        )
        intents = _read_existing_rows(intent_path, "intent_id")
        by_work: Dict[str, Dict[str, Any]] = {}
        for intent in intents.values():
            work_id = str(intent.get("canonical_work_id", ""))
            if work_id in by_work:
                raise Pilot3PhaseAError("development acquisition intents duplicate a work")
            by_work[work_id] = intent
        first_work_id = str(rows[0]["canonical_work_id"])
        route = "network" if canonical_work_id == first_work_id else "browser_recovery"
        expected = _acquisition_intent(
            split,
            acquisition_route=route,
            phase_a_config_file_sha256=hash_file(_resolve(root, DEFAULT_CONFIG)),
            external_protocol_result_sha256=None,
            external_unseal_receipt_sha256=None,
        )
        existing = by_work.get(canonical_work_id)
        if existing is not None and existing != expected:
            raise Pilot3PhaseAError(
                "AIC browser-recovery acquisition intent route is stale: "
                + canonical_work_id
            )
        if existing is None:
            _append_jsonl_fsync(intent_path, expected)
            intents[str(expected["intent_id"])] = expected
            by_work[canonical_work_id] = expected
        http_histories = _verified_http_attempt_histories(
            root,
            config,
            "development",
            intents,
            normalization_amendment=amendment,
        )
        histories = _verified_browser_attempt_histories(
            root,
            config,
            authorization,
            intents,
            normalization_amendment=amendment,
        )
        intents_by_id = {str(intent["intent_id"]): intent for intent in intents.values()}
        for completed_intent_id, completed_history in histories.items():
            if len(completed_history) != 2:
                continue
            completed_start, completed_terminal = completed_history
            completed_work_id = str(completed_start["canonical_work_id"])
            if completed_work_id in acquisitions:
                continue
            completed_split = rows_by_work[completed_work_id]
            completed_intent = intents_by_id[completed_intent_id]
            completed_payload = _resolve(
                root, str(completed_terminal["raw_path"])
            ).read_bytes()
            acquisitions[completed_work_id] = _materialize_real_acquisition(
                root,
                config,
                completed_split,
                completed_intent,
                completed_payload,
                _browser_response_evidence(completed_terminal),
                http_histories[completed_intent_id],
                acquisition_completion_route="browser_download_import",
                browser_terminal=completed_terminal,
                external_unseal_token=None,
                external_unseal_receipt_sha256=None,
                normalization_amendment=amendment,
            )
        if canonical_work_id in acquisitions:
            raise Pilot3PhaseAError(
                "browser prepare target already has a completed recovery: "
                + canonical_work_id
            )
        pending = [
            history[0]
            for history in histories.values()
            if len(history) == 1 and history[0].get("event_type") == "start"
        ]
        if pending and any(
            event.get("canonical_work_id") != canonical_work_id for event in pending
        ):
            raise Pilot3PhaseAError(
                "an earlier browser start is unmatched; reconcile it before another start"
            )
        ledger_path = _resolve(root, BROWSER_RECOVERY_LEDGER_PATH)
        _ensure_durable_file(ledger_path)
        events = _read_canonical_browser_events(ledger_path)
        intent = by_work[canonical_work_id]
        history = histories[str(intent["intent_id"])]
        if history:
            if history[0].get("download_directory_path") != str(requested_directory):
                raise Pilot3PhaseAError(
                    "prepared browser work is bound to a different download directory"
                )
            return history[0]
        directory_intent_path = _resolve(
            root, BROWSER_DIRECTORY_INTENT_LEDGER_PATH
        )
        _ensure_durable_file(directory_intent_path)
        directory_intents = _read_directory_intents(directory_intent_path)
        by_directory_work = {
            str(row["canonical_work_id"]): row for row in directory_intents
        }
        directory_intent = by_directory_work.get(canonical_work_id)
        if directory_intent is None:
            if os.path.lexists(requested_directory):
                raise Pilot3PhaseAError(
                    "prepared browser download directory must not already exist"
                )
            parent_stat = os.lstat(requested_directory.parent)
            if not stat.S_ISDIR(parent_stat.st_mode) or stat.S_ISLNK(parent_stat.st_mode):
                raise Pilot3PhaseAError(
                    "browser download directory parent must be a non-symlink directory"
                )
            directory_intent = _browser_directory_intent(
                authorization,
                canonical_work_id,
                requested_directory,
                directory_intents,
            )
            _append_jsonl_fsync(directory_intent_path, directory_intent)
            directory_intents.append(directory_intent)
            try:
                os.mkdir(requested_directory, 0o700)
            except FileExistsError as exc:
                raise Pilot3PhaseAError(
                    "browser download directory appeared after its durable intent"
                ) from exc
        else:
            if directory_intent.get("download_directory_path") != str(
                requested_directory
            ):
                raise Pilot3PhaseAError(
                    "browser directory intent is bound to a different path"
                )
            if not os.path.lexists(requested_directory):
                os.mkdir(requested_directory, 0o700)
        nofollow = getattr(os, "O_NOFOLLOW", None)
        odirectory = getattr(os, "O_DIRECTORY", None)
        if nofollow is None or odirectory is None:
            raise Pilot3PhaseAError(
                "runtime lacks no-follow directory descriptors for browser recovery"
            )
        directory_descriptor = os.open(
            requested_directory, os.O_RDONLY | nofollow | odirectory
        )
        try:
            download_directory_stat = _directory_stat_evidence(
                os.fstat(directory_descriptor)
            )
            direct_entry_names = sorted(os.listdir(directory_descriptor))
            if direct_entry_names:
                raise Pilot3PhaseAError(
                    "prepared browser download directory is not exactly empty"
                )
            if (
                download_directory_stat["birthtime_ns"] // 1_000_000_000
                < int(directory_intent["intent_written_before_mkdir_wall_time_ns"])
                // 1_000_000_000
            ):
                raise Pilot3PhaseAError(
                    "browser download directory predates its durable creation intent"
                )
            start_wall_time_ns = time.time_ns()
            start_monotonic_ns = time.monotonic_ns()
        finally:
            os.close(directory_descriptor)
        if not history:
            start = _browser_attempt_start(
                authorization=authorization,
                split=split,
                intent=intent,
                directory_intent=directory_intent,
                download_directory_stat=download_directory_stat,
                start_not_before_wall_time_ns=start_wall_time_ns,
                start_not_before_monotonic_ns=start_monotonic_ns,
                event_sequence=len(events) + 1,
                previous_event_sha256=(
                    str(events[-1]["event_sha256"]) if events else None
                ),
                prior_events=events,
                normalization_amendment=amendment,
                effective_preprocessing_contract_sha256=(
                    _effective_preprocessing_contract_sha256(config)
                ),
            )
            _append_jsonl_fsync(ledger_path, start)
            events.append(start)
            history.append(start)
        verified = _verified_browser_attempt_histories(
            root,
            config,
            authorization,
            intents,
            normalization_amendment=amendment,
        )
        result = verified[str(intent["intent_id"])][0]
        if result.get("canonical_work_id") != canonical_work_id:
            raise Pilot3PhaseAError("AIC browser recovery prepared the wrong work")
        return result


def import_aic_browser_recovery_directory(
    root: Path, directory: Path
) -> List[Dict[str, Any]]:
    """Reconcile completed direct browser downloads into the append-only recovery journal."""

    root = Path(root).expanduser().resolve()
    source_directory = _lexical_absolute_path(directory)
    directory_stat = os.lstat(source_directory)
    if not stat.S_ISDIR(directory_stat.st_mode) or stat.S_ISLNK(directory_stat.st_mode):
        raise Pilot3PhaseAError("browser import directory must be a direct non-symlink directory")
    with _acquisition_phase_lock(root, "development"):
        resolution = require_preprocessing_incident_resolution(root)
        require_development_freeze(root)
        amendment = resolution["amendment"]
        incident = verify_preprocessing_determinism_incident(root)
        authorization = _verify_historical_aic_browser_recovery_authorization(
            root, incident=incident, require_committed=True
        )
        config = load_phase_a_config(root)
        rows = _aic_development_splits(root, config)
        rows_by_work = {str(row["canonical_work_id"]): row for row in rows}
        intents = _read_existing_rows(
            _phase_ledger_path(root, config, "development", "acquisition_intents"),
            "intent_id",
        )
        histories = _verified_browser_attempt_histories(
            root,
            config,
            authorization,
            intents,
            normalization_amendment=amendment,
        )
        http_histories = _verified_http_attempt_histories(
            root,
            config,
            "development",
            intents,
            normalization_amendment=amendment,
        )
        matching_histories = [
            history
            for history in histories.values()
            if history
            and history[0].get("download_directory_path") == str(source_directory)
        ]
        if len(matching_histories) != 1:
            raise Pilot3PhaseAError(
                "import directory is not bound to exactly one browser attempt"
            )
        history = matching_histories[0]
        start = history[0]
        work_id = str(start["canonical_work_id"])
        split = rows_by_work[work_id]
        intent = intents[str(start["intent_id"])]
        (
            candidate,
            payload,
            raw_xattr,
            urls,
            raw_quarantine,
            quarantine,
            source_stat,
            import_directory_stat,
            decode,
            normalized,
        ) = _read_bound_browser_download(source_directory, start, config, split)
        ledger_path = _resolve(root, BROWSER_RECOVERY_LEDGER_PATH)
        events = _read_canonical_browser_events(ledger_path)
        if len(history) == 2:
            terminal = history[-1]
            if terminal.get("raw_sha256") != hash_bytes(payload):
                raise Pilot3PhaseAError(
                    "completed browser attempt conflicts with the bound download"
                )
        else:
            if len(history) != 1:
                raise Pilot3PhaseAError("browser attempt history has a stale event count")
            raw_sha = hash_bytes(payload)
            raw_path = (
                _resolve(root, config["paths"]["raw_dir"])
                / raw_sha[:2]
                / f"{raw_sha}.bin"
            )
            normalized_sha = hash_bytes(normalized)
            normalized_path = (
                _resolve(root, config["paths"]["normalized_dir"])
                / normalized_sha[:2]
                / f"{normalized_sha}.png"
            )
            for path, content, digest in (
                (raw_path, payload, raw_sha),
                (normalized_path, normalized, normalized_sha),
            ):
                if path.exists() and hash_file(path) != digest:
                    raise Pilot3PhaseAError(f"browser CAS collision at {path}")
                if not path.exists():
                    _atomic_bytes(path, content)
            terminal = _browser_attempt_terminal(
                start,
                source_file=candidate,
                source_file_stat=source_stat,
                raw_xattr=raw_xattr,
                where_froms_urls=urls,
                raw_quarantine_xattr=raw_quarantine,
                quarantine_evidence=quarantine,
                download_directory_stat_at_import=import_directory_stat,
                payload=payload,
                raw_path=raw_path,
                decode=decode,
                normalized=normalized,
                normalized_path=normalized_path,
                root=root,
                prior_events=events,
            )
            _validate_browser_attempt_terminal(root, config, start, terminal, events)
            _append_jsonl_fsync(ledger_path, terminal)
            events.append(terminal)
            histories[str(intent["intent_id"])].append(terminal)
        acquisition = _materialize_real_acquisition(
            root,
            config,
            split,
            intent,
            payload,
            _browser_response_evidence(terminal),
            http_histories[str(intent["intent_id"])],
            acquisition_completion_route="browser_download_import",
            browser_terminal=terminal,
            external_unseal_token=None,
            external_unseal_receipt_sha256=None,
            normalization_amendment=amendment,
        )
        _verified_browser_attempt_histories(
            root,
            config,
            authorization,
            intents,
            normalization_amendment=amendment,
        )
        return [acquisition]


def _browser_recovery_for_intent(
    root: Path,
    config: Mapping[str, Any],
    intent: Mapping[str, Any],
) -> Optional[Tuple[bytes, Dict[str, Any], Dict[str, Any]]]:
    if str(intent.get("source_id", "aic")) not in {"", "aic"}:
        return None
    authorization_path = _resolve(root, BROWSER_RECOVERY_AUTHORIZATION_PATH)
    ledger_path = _resolve(root, BROWSER_RECOVERY_LEDGER_PATH)
    if not authorization_path.is_file() or not ledger_path.is_file():
        return None
    resolution = require_preprocessing_incident_resolution(root)
    amendment = resolution["amendment"]
    incident = verify_preprocessing_determinism_incident(root)
    authorization = _verify_historical_aic_browser_recovery_authorization(
        root, incident=incident, require_committed=True
    )
    intents = _read_existing_rows(
        _phase_ledger_path(root, config, "development", "acquisition_intents"),
        "intent_id",
    )
    histories = _verified_browser_attempt_histories(
        root,
        config,
        authorization,
        intents,
        normalization_amendment=amendment,
    )
    history = histories.get(str(intent["intent_id"]), [])
    if not history:
        return None
    if len(history) == 1:
        raise Pilot3PhaseAError(
            "prepared browser recovery has no imported terminal for "
            + str(intent["canonical_work_id"])
        )
    terminal = history[-1]
    payload = _resolve(root, str(terminal["raw_path"])).read_bytes()
    return payload, _browser_response_evidence(terminal), terminal


def _browser_response_evidence(terminal: Mapping[str, Any]) -> Dict[str, Any]:
    result = {
        "transport": "darwin_browser_download_wherefroms_import",
        "browser_attempt_id": terminal["browser_attempt_id"],
        "browser_start_event_sha256": terminal["start_event_sha256"],
        "browser_terminal_event_sha256": terminal["event_sha256"],
        "browser_authorization_sha256": terminal["authorization_sha256"],
        "where_froms_plist_sha256": terminal["where_froms_plist_sha256"],
        "where_froms_urls": terminal["where_froms_urls"],
        "quarantine_xattr_sha256": terminal["quarantine_xattr_sha256"],
        "quarantine_evidence": terminal["quarantine_evidence"],
        "download_directory_path": terminal["download_directory_path"],
        "download_directory_device": terminal["download_directory_stat_at_import"][
            "device"
        ],
        "download_directory_inode": terminal["download_directory_stat_at_import"][
            "inode"
        ],
        "candidate_direct_entry_name": terminal["candidate_direct_entry_name"],
        "freshness_not_before_wall_time_ns": terminal[
            "freshness_not_before_wall_time_ns"
        ],
        "httpx_success_claimed": False,
    }
    for key in (
        "normalization_protocol_version",
        "preprocessing_determinism_amendment_sha256",
        "effective_preprocessing_contract_sha256",
    ):
        if key in terminal:
            result[key] = terminal[key]
    return result


def _download_image_bytes(
    root: Path,
    config: Mapping[str, Any],
    phase: str,
    intent: Mapping[str, Any],
    *,
    normalization_amendment: Optional[Mapping[str, Any]] = None,
    normalization_authorization: Optional[Mapping[str, Any]] = None,
) -> Tuple[bytes, Dict[str, Any], List[Dict[str, Any]]]:
    """Resume or execute a network GET with durable evidence for every attempt."""

    attempt_path = _phase_ledger_path(root, config, phase, "acquisition_attempts")
    _ensure_durable_file(attempt_path)
    intents = _read_existing_rows(
        _phase_ledger_path(root, config, phase, "acquisition_intents"), "intent_id"
    )
    if intents.get(str(intent["intent_id"])) != dict(intent):
        raise Pilot3PhaseAError("network acquisition intent is missing or stale")
    if _resolve(root, PREPROCESSING_INCIDENT_PATH).is_file() and (
        normalization_amendment is None and normalization_authorization is None
    ):
        raise Pilot3PhaseAError(
            "post-incident HTTP acquisition requires the committed v2 amendment "
            "or normalization-scope authority"
        )
    history = _verified_http_attempt_histories(
        root,
        config,
        phase,
        intents,
        normalization_amendment=normalization_amendment,
        normalization_authorization=normalization_authorization,
    )[str(intent["intent_id"])]
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
            normalization_amendment=normalization_amendment,
            normalization_authorization=normalization_authorization,
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
            normalized, normalized_size = pilot3_common_png_bytes(
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


def _effective_preprocessing_contract(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Describe the authorized v2 overlay without rewriting the frozen v1 config."""

    return {
        "base_common_preprocessing": dict(config["common_preprocessing"]),
        "base_common_preprocessing_config_sha256": stable_hash(
            config["common_preprocessing"]
        ),
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "pixel_transform_changed": False,
        "container_metadata_policy": "no_ancillary_png_chunks",
        "canonical_chunk_sequence": "IHDR_then_contiguous_IDAT_then_IEND",
        "embedded_icc_policy": (
            "apply_to_rgb_pixels_then_detach_generated_profile_metadata"
        ),
        "normalization_runtime": pilot3_normalization_runtime_fingerprint(),
    }


def _effective_preprocessing_contract_sha256(config: Mapping[str, Any]) -> str:
    return stable_hash(_effective_preprocessing_contract(config))


def _require_normalization_scope(
    root: Path, config: Mapping[str, Any]
) -> Dict[str, Any]:
    """Require the committed exact-member authority for non-AIC inputs."""

    try:
        scope = pilot3_normalization_scope.require_committed_normalization_scope_authorization(
            root
        )
    except pilot3_normalization_scope.Pilot3NormalizationScopeError as exc:
        raise Pilot3PhaseAError(
            "the committed normalization-scope authority is required"
        ) from exc
    implementation = scope.get("normalization_implementation")
    if (
        not isinstance(implementation, Mapping)
        or implementation.get("protocol_version")
        != PILOT3_NORMALIZATION_PROTOCOL_VERSION
        or implementation.get("effective_preprocessing_contract")
        != _effective_preprocessing_contract(config)
        or implementation.get("effective_preprocessing_contract_sha256")
        != _effective_preprocessing_contract_sha256(config)
        or not _is_sha256(scope.get("authorization_sha256"))
    ):
        raise Pilot3PhaseAError(
            "normalization-scope authority binds a stale preprocessing contract"
        )
    return scope


def _normalization_authority_lineage(
    authorization: Mapping[str, Any], *, schema: str
) -> Dict[str, str]:
    sha256 = authorization.get("authorization_sha256")
    if not _is_sha256(sha256):
        raise Pilot3PhaseAError("normalization authority lacks a valid self-hash")
    return {
        "normalization_authorization_schema": schema,
        "normalization_authorization_sha256": str(sha256),
    }


def _verify_scope_member(
    scope: Mapping[str, Any],
    split: Mapping[str, Any],
    *,
    primary_image_url: Optional[str] = None,
    target_row_sha256: Optional[str] = None,
) -> None:
    eligible = scope.get("eligible_membership")
    if not isinstance(eligible, Mapping):
        raise Pilot3PhaseAError("normalization scope lacks eligible membership")
    source_id = str(split.get("source_id", ""))
    if source_id == "met":
        section = eligible.get("met_r2")
        members = section.get("members") if isinstance(section, Mapping) else None
        expected = {
            "physical_work_id": split.get("canonical_work_id"),
            "object_id": str(split.get("source_object_id")),
            "artist_id": split.get("artist_id"),
            "partition": split.get("partition"),
            "primary_image_url": primary_image_url,
            "target_row_sha256": target_row_sha256,
        }
        matches = [
            member
            for member in members or []
            if isinstance(member, Mapping)
            and all(member.get(key) == value for key, value in expected.items())
        ]
        if len(matches) != 1:
            raise Pilot3PhaseAError(
                "normalization scope does not contain the exact Met R2 asset"
            )
        return
    if split.get("partition") == EXTERNAL_PARTITION:
        section = eligible.get("external_official_assets")
        members = section.get("members") if isinstance(section, Mapping) else None
        expected = {
            "asset_id": split.get("canonical_work_id"),
            "source_object_id": split.get("source_object_id"),
            "artist_id": split.get("artist_id"),
            "collection_block_id": split.get("collection_block_id"),
            "image_url": split.get("image_url"),
            "split_row_sha256": split.get("row_sha256"),
        }
        matches = [
            member
            for member in members or []
            if isinstance(member, Mapping)
            and all(member.get(key) == value for key, value in expected.items())
        ]
        if len(matches) != 1:
            raise Pilot3PhaseAError(
                "normalization scope does not contain the exact external asset"
            )
        return
    raise Pilot3PhaseAError("normalization-scope membership is unknown for this split")


def _normalization_revalidation_row(
    *,
    root: Path,
    config: Mapping[str, Any],
    amendment: Mapping[str, Any],
    incident: Mapping[str, Any],
    original: Mapping[str, Any],
    split: Mapping[str, Any],
    normalized: bytes,
    normalized_path: Path,
    prior: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    original_path = _resolve(root, str(original["normalized_path"]))
    original_payload = original_path.read_bytes()
    original_pixel_sha = _normalized_rgb_pixel_sha256(original_payload)
    effective_pixel_sha = _normalized_rgb_pixel_sha256(normalized)
    effective_sha = hash_bytes(normalized)
    identity = {
        "original_acquisition_record_sha256": original["record_sha256"],
        "preprocessing_determinism_amendment_sha256": amendment[
            "authorization_sha256"
        ],
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "effective_normalized_sha256": effective_sha,
    }
    payload = {
        "record_type": "pilot3_real_acquisition_normalization_revalidation",
        "schema_version": NORMALIZATION_REVALIDATION_SCHEMA,
        "sequence": len(prior) + 1,
        "previous_record_sha256": prior[-1]["record_sha256"] if prior else None,
        "expected_ledger_prefix_sha256": stable_hash(list(prior)),
        "canonical_work_id": original["canonical_work_id"],
        "incident_sha256": incident["incident_sha256"],
        **identity,
        "effective_acquisition_sha256": stable_hash(identity),
        "raw_path": original["raw_path"],
        "raw_sha256": original["raw_sha256"],
        "raw_byte_count": original["raw_byte_count"],
        "original_normalized_path": original["normalized_path"],
        "original_normalized_sha256": original["normalized_sha256"],
        "original_normalized_byte_count": original["normalized_byte_count"],
        "effective_normalized_path": _portable(normalized_path, root),
        "effective_normalized_byte_count": len(normalized),
        "original_rgb_pixel_sha256": original_pixel_sha,
        "effective_rgb_pixel_sha256": effective_pixel_sha,
        "exact_rgb_pixel_equality": original_pixel_sha == effective_pixel_sha,
        "normalized_container_changed": original["normalized_sha256"] != effective_sha,
        "disposition": (
            "superseded"
            if original["normalized_sha256"] != effective_sha
            else "revalidated_unchanged"
        ),
        "base_phase_a_config_file_sha256": original[
            "phase_a_config_file_sha256"
        ],
        "base_common_preprocessing_config_sha256": original[
            "common_preprocessing_config_sha256"
        ],
        "effective_preprocessing_contract": _effective_preprocessing_contract(config),
        "effective_preprocessing_contract_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        "original_acquisition_and_cas_preserved": True,
        "visual_inspection_feature_extraction_or_network_performed": False,
    }
    return _self_hash(payload, "record_sha256")


def _incident_acquisition_rows(
    root: Path, config: Mapping[str, Any], incident: Mapping[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Mapping[str, Any]]]:
    path = _phase_ledger_path(root, config, "development", "acquisitions")
    all_rows = read_jsonl(path)
    rows = [dict(value) for value in all_rows[:PREPROCESSING_INCIDENT_ACQUISITION_COUNT]]
    bindings = incident["acquisition_bindings"]
    if len(rows) != PREPROCESSING_INCIDENT_ACQUISITION_COUNT:
        raise Pilot3PhaseAError("incident acquisition prefix is incomplete")
    split_by_work = {
        str(row["canonical_work_id"]): row
        for row in load_real_splits(root, config)
    }
    for row, binding in zip(rows, bindings):
        verify_self_hash(row, "record_sha256")
        if row["record_sha256"] != binding["record_sha256"]:
            raise Pilot3PhaseAError("incident acquisition prefix record changed")
        split = split_by_work.get(str(row["canonical_work_id"]))
        if split is None:
            raise Pilot3PhaseAError("incident acquisition left the frozen split")
        for path_key, hash_key, count_key in (
            ("raw_path", "raw_sha256", "raw_byte_count"),
            ("normalized_path", "normalized_sha256", "normalized_byte_count"),
        ):
            candidate = _resolve(root, str(row[path_key]))
            if (
                not candidate.is_file()
                or candidate.stat().st_size != row[count_key]
                or hash_file(candidate) != row[hash_key]
            ):
                raise Pilot3PhaseAError(
                    "incident acquisition CAS is missing or stale: " + str(candidate)
                )
    return rows, split_by_work


def _read_canonical_normalization_revalidations(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    payload = path.read_bytes()
    if not payload:
        return []
    if not payload.endswith(b"\n"):
        raise Pilot3PhaseAError("normalization revalidation ledger has a torn final row")
    if b"\r" in payload:
        raise Pilot3PhaseAError("normalization revalidation ledger has noncanonical newlines")
    rows: List[Dict[str, Any]] = []
    for index, raw_line in enumerate(payload.splitlines(), start=1):
        if not raw_line:
            raise Pilot3PhaseAError("normalization revalidation ledger has a blank row")
        try:
            decoded = raw_line.decode("utf-8")
            row = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise Pilot3PhaseAError(
                f"normalization revalidation row {index} is not canonical JSON"
            ) from exc
        if not isinstance(row, dict) or canonical_json(row) != decoded:
            raise Pilot3PhaseAError(
                f"normalization revalidation row {index} is not canonical JSON"
            )
        rows.append(row)
    return rows


def verify_normalization_revalidations(
    root: Path, *, require_committed: bool = True, require_complete: bool = True
) -> Dict[str, Dict[str, Any]]:
    """Verify the append-only v1-to-v2 revalidation ledger and replacement CAS."""

    root = Path(root).expanduser().resolve()
    amendment = verify_preprocessing_determinism_amendment(
        root, require_committed=require_committed
    )
    incident = verify_preprocessing_determinism_incident(root)
    config = load_phase_a_config(root)
    originals, split_by_work = _incident_acquisition_rows(root, config, incident)
    path = _resolve(root, NORMALIZATION_REVALIDATION_LEDGER_PATH)
    rows = _read_canonical_normalization_revalidations(path)
    if len(rows) > len(originals) or (require_complete and len(rows) != len(originals)):
        raise Pilot3PhaseAError(
            "normalization revalidation ledger does not cover the incident prefix"
        )
    verified: Dict[str, Dict[str, Any]] = {}
    prior: List[Dict[str, Any]] = []
    differences: set[str] = set()
    supersession_count = 0
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise Pilot3PhaseAError("normalization revalidation row is malformed")
        original = originals[index]
        split = split_by_work[str(original["canonical_work_id"])]
        raw_path = _resolve(root, str(original["raw_path"]))
        _, normalized = _decode_and_normalize(
            raw_path.read_bytes(),
            config,
            expected_width=int(split["delivery_width"]),
            expected_height=int(split["delivery_height"]),
        )
        effective_sha = hash_bytes(normalized)
        normalized_path = (
            _resolve(root, config["paths"]["normalized_dir"])
            / effective_sha[:2]
            / f"{effective_sha}.png"
        )
        expected = _normalization_revalidation_row(
            root=root,
            config=config,
            amendment=amendment,
            incident=incident,
            original=original,
            split=split,
            normalized=normalized,
            normalized_path=normalized_path,
            prior=prior,
        )
        if raw != expected:
            raise Pilot3PhaseAError(
                "normalization revalidation row is stale: "
                + str(original["canonical_work_id"])
            )
        if (
            not normalized_path.is_file()
            or normalized_path.stat().st_size != len(normalized)
            or hash_file(normalized_path) != effective_sha
            or normalized_path.read_bytes() != normalized
            or raw["exact_rgb_pixel_equality"] is not True
        ):
            raise Pilot3PhaseAError(
                "normalization revalidation CAS is missing or stale: "
                + str(normalized_path)
            )
        work_id = str(original["canonical_work_id"])
        if raw["normalized_container_changed"]:
            differences.add(work_id)
            supersession_count += 1
            if raw.get("disposition") != "superseded":
                raise Pilot3PhaseAError("changed normalization is not superseded")
        elif raw.get("disposition") != "revalidated_unchanged":
            raise Pilot3PhaseAError("unchanged normalization has a stale disposition")
        verified[work_id] = raw
        prior.append(raw)
    if require_complete and (
        differences != {PREPROCESSING_INCIDENT_WORK_ID} or supersession_count != 1
    ):
        raise Pilot3PhaseAError(
            "normalization revalidation difference set is not exactly the incident work"
        )
    if require_committed:
        if not _git_path_committed_and_clean(
            root, str(NORMALIZATION_REVALIDATION_LEDGER_PATH)
        ):
            raise Pilot3PhaseAError(
                "normalization revalidation ledger is not committed and clean"
            )
        amendment_commit = _git_introduction_commit(
            root, str(PREPROCESSING_AMENDMENT_PATH)
        )
        correction_commit = _git_introduction_commit(
            root, str(NORMALIZATION_REVALIDATION_LEDGER_PATH)
        )
        _require_strict_git_ancestor(
            root,
            amendment_commit,
            correction_commit,
            "normalization revalidation was not committed strictly after the amendment",
        )
        correction_blob = subprocess.run(
            [
                "git",
                "show",
                f"{correction_commit}:{NORMALIZATION_REVALIDATION_LEDGER_PATH}",
            ],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if correction_blob.returncode != 0 or correction_blob.stdout != path.read_bytes():
            raise Pilot3PhaseAError(
                "normalization revalidation introduction blob differs from the live ledger"
            )
    return verified


def create_normalization_revalidations(root: Path) -> List[Dict[str, Any]]:
    """Append the exact 12-row offline revalidation, with no browser/network I/O."""

    root = Path(root).expanduser().resolve()
    with _acquisition_phase_lock(root, "development"):
        amendment = verify_preprocessing_determinism_amendment(
            root, require_committed=True
        )
        require_development_freeze(root)
        incident = verify_preprocessing_determinism_incident(
            root, require_exact_checkpoint=True
        )
        config = load_phase_a_config(root)
        originals, split_by_work = _incident_acquisition_rows(root, config, incident)
        path = _resolve(root, NORMALIZATION_REVALIDATION_LEDGER_PATH)
        recomputed: List[Tuple[Mapping[str, Any], Mapping[str, Any], bytes, Path]] = []
        differences: set[str] = set()
        for original in originals:
            split = split_by_work[str(original["canonical_work_id"])]
            raw_payload = _resolve(root, str(original["raw_path"])).read_bytes()
            _, normalized = _decode_and_normalize(
                raw_payload,
                config,
                expected_width=int(split["delivery_width"]),
                expected_height=int(split["delivery_height"]),
            )
            _, repeated = _decode_and_normalize(
                raw_payload,
                config,
                expected_width=int(split["delivery_width"]),
                expected_height=int(split["delivery_height"]),
            )
            if normalized != repeated:
                raise Pilot3PhaseAError(
                    "Pilot-3 v2 normalization is not stable across repeated serialization"
                )
            if _normalized_rgb_pixel_sha256(normalized) != _normalized_rgb_pixel_sha256(
                _resolve(root, str(original["normalized_path"])).read_bytes()
            ):
                raise Pilot3PhaseAError(
                    "Pilot-3 v2 normalization changed historical RGB pixels"
                )
            effective_sha = hash_bytes(normalized)
            if effective_sha != original["normalized_sha256"]:
                differences.add(str(original["canonical_work_id"]))
            normalized_path = (
                _resolve(root, config["paths"]["normalized_dir"])
                / effective_sha[:2]
                / f"{effective_sha}.png"
            )
            recomputed.append((original, split, normalized, normalized_path))
        if differences != {PREPROCESSING_INCIDENT_WORK_ID}:
            raise Pilot3PhaseAError(
                "normalization preflight difference set is not exactly the incident work"
            )
        existing = verify_normalization_revalidations(
            root, require_committed=False, require_complete=False
        )
        rows = _read_canonical_normalization_revalidations(path)
        if len(existing) != len(rows):
            raise Pilot3PhaseAError("normalization revalidation prefix is ambiguous")
        for original, split, normalized, normalized_path in recomputed[len(rows) :]:
            effective_sha = hash_bytes(normalized)
            if normalized_path.exists() and hash_file(normalized_path) != effective_sha:
                raise Pilot3PhaseAError(
                    "normalization revalidation CAS collision at "
                    + str(normalized_path)
                )
            if not normalized_path.exists():
                _atomic_bytes(normalized_path, normalized)
            row = _normalization_revalidation_row(
                root=root,
                config=config,
                amendment=amendment,
                incident=incident,
                original=original,
                split=split,
                normalized=normalized,
                normalized_path=normalized_path,
                prior=rows,
            )
            _append_jsonl_fsync(path, row)
            rows.append(row)
        verify_normalization_revalidations(
            root, require_committed=False, require_complete=True
        )
        return [dict(row) for row in rows]


def _effective_acquisition_from_revalidation(
    original: Mapping[str, Any], revalidation: Mapping[str, Any]
) -> Dict[str, Any]:
    effective = dict(original)
    if revalidation["disposition"] == "superseded":
        effective.update(
            {
                "normalized_path": revalidation["effective_normalized_path"],
                "normalized_sha256": revalidation["effective_normalized_sha256"],
                "normalized_byte_count": revalidation[
                    "effective_normalized_byte_count"
                ],
            }
        )
    effective.update(
        {
            "base_common_preprocessing_config_sha256": revalidation[
                "base_common_preprocessing_config_sha256"
            ],
            "common_preprocessing_config_sha256": revalidation[
                "effective_preprocessing_contract_sha256"
            ],
            "normalization_protocol_version": revalidation[
                "normalization_protocol_version"
            ],
            "preprocessing_determinism_amendment_sha256": revalidation[
                "preprocessing_determinism_amendment_sha256"
            ],
            "effective_preprocessing_contract_sha256": revalidation[
                "effective_preprocessing_contract_sha256"
            ],
            "original_acquisition_record_sha256": original["record_sha256"],
            "normalization_revalidation_record_sha256": revalidation[
                "record_sha256"
            ],
            "effective_acquisition_sha256": revalidation[
                "effective_acquisition_sha256"
            ],
        }
    )
    return effective


def effective_acquisition_rows(
    root: Path,
    config: Mapping[str, Any],
    phase: str,
    originals: Optional[Mapping[str, Mapping[str, Any]]] = None,
    *,
    require_committed: bool = True,
) -> Dict[str, Dict[str, Any]]:
    """Resolve immutable base rows to their authorized effective v2 inputs."""

    if phase not in {"development", "external"}:
        raise ValueError("phase must be development or external")
    amendment = verify_preprocessing_determinism_amendment(
        root, require_committed=require_committed
    )
    source = (
        dict(originals)
        if originals is not None
        else _read_existing_rows(
            _phase_ledger_path(root, config, phase, "acquisitions"),
            "canonical_work_id",
        )
    )
    corrections = (
        verify_normalization_revalidations(
            root, require_committed=require_committed, require_complete=True
        )
        if phase == "development"
        else {}
    )
    result: Dict[str, Dict[str, Any]] = {}
    scope: Optional[Dict[str, Any]] = None
    for work_id, original in source.items():
        correction = corrections.get(str(work_id))
        if correction is not None:
            if original.get("source_id") != "aic":
                raise Pilot3PhaseAError(
                    "legacy normalization revalidation escaped its AIC-only scope"
                )
            if correction["original_acquisition_record_sha256"] != original.get(
                "record_sha256"
            ):
                raise Pilot3PhaseAError(
                    "normalization revalidation binds a different acquisition"
                )
            effective = _effective_acquisition_from_revalidation(original, correction)
            effective.update(
                _normalization_authority_lineage(
                    amendment, schema=PREPROCESSING_AMENDMENT_SCHEMA
                )
            )
            result[str(work_id)] = effective
            continue
        if original.get("schema_version") == MET_R2_NORMALIZED_ACQUISITION_SCHEMA:
            scope = scope or _require_normalization_scope(root, config)
            if (
                original.get("source_id") not in {"met", EXTERNAL_SOURCE}
                or original.get("normalization_protocol_version")
                != PILOT3_NORMALIZATION_PROTOCOL_VERSION
                or original.get("preprocessing_determinism_amendment_sha256")
                is not None
                or original.get("base_common_preprocessing_config_sha256")
                != stable_hash(config["common_preprocessing"])
                or original.get("common_preprocessing_config_sha256")
                != _effective_preprocessing_contract_sha256(config)
                or original.get("effective_preprocessing_contract_sha256")
                != _effective_preprocessing_contract_sha256(config)
                or original.get("normalization_authorization_schema")
                != pilot3_normalization_scope.SCHEMA_VERSION
                or original.get("normalization_authorization_sha256")
                != scope["authorization_sha256"]
            ):
                raise Pilot3PhaseAError(
                    "schema-v3 acquisition lacks the exact normalization scope: "
                    + str(work_id)
                )
            effective = dict(original)
            effective_identity = {
                "original_acquisition_record_sha256": original["record_sha256"],
                "normalization_authorization_schema": (
                    pilot3_normalization_scope.SCHEMA_VERSION
                ),
                "normalization_authorization_sha256": scope["authorization_sha256"],
                "normalization_protocol_version": (
                    PILOT3_NORMALIZATION_PROTOCOL_VERSION
                ),
                "effective_normalized_sha256": original["normalized_sha256"],
            }
            effective.update(
                {
                    "original_acquisition_record_sha256": original["record_sha256"],
                    "normalization_revalidation_record_sha256": None,
                    "effective_acquisition_sha256": stable_hash(effective_identity),
                }
            )
            result[str(work_id)] = effective
            continue
        if (
            original.get("normalization_protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or original.get("preprocessing_determinism_amendment_sha256")
            != amendment["authorization_sha256"]
            or original.get("effective_preprocessing_contract_sha256")
            != _effective_preprocessing_contract_sha256(config)
        ):
            raise Pilot3PhaseAError(
                "acquisition lacks an authorized effective v2 normalization: "
                + str(work_id)
            )
        effective = dict(original)
        effective.update(
            _normalization_authority_lineage(
                amendment, schema=PREPROCESSING_AMENDMENT_SCHEMA
            )
        )
        effective_identity = {
            "original_acquisition_record_sha256": original["record_sha256"],
            "preprocessing_determinism_amendment_sha256": amendment[
                "authorization_sha256"
            ],
            "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
            "effective_normalized_sha256": original["normalized_sha256"],
        }
        effective.update(
            {
                "original_acquisition_record_sha256": original["record_sha256"],
                "normalization_revalidation_record_sha256": None,
                "effective_acquisition_sha256": stable_hash(effective_identity),
            }
        )
        result[str(work_id)] = effective
    for work_id, effective in result.items():
        if (
            effective.get("base_common_preprocessing_config_sha256")
            != stable_hash(config["common_preprocessing"])
            or effective.get("common_preprocessing_config_sha256")
            != _effective_preprocessing_contract_sha256(config)
            or effective.get("effective_preprocessing_contract_sha256")
            != _effective_preprocessing_contract_sha256(config)
            or not _is_sha256(effective.get("effective_acquisition_sha256"))
            or not _is_sha256(effective.get("original_acquisition_record_sha256"))
            or effective.get("normalization_authorization_schema")
            not in {
                PREPROCESSING_AMENDMENT_SCHEMA,
                pilot3_normalization_scope.SCHEMA_VERSION,
            }
            or not _is_sha256(effective.get("normalization_authorization_sha256"))
        ):
            raise Pilot3PhaseAError(
                "effective acquisition has inconsistent v2 lineage: " + work_id
            )
    return result


def require_preprocessing_incident_resolution(root: Path) -> Dict[str, Any]:
    """Fail closed until the committed amendment and complete correction both verify."""

    amendment = verify_preprocessing_determinism_amendment(root, require_committed=True)
    corrections = verify_normalization_revalidations(
        root, require_committed=True, require_complete=True
    )
    return {"amendment": amendment, "corrections": corrections}


def _require_met_r2_normalization_inputs(
    root: Path, config: Mapping[str, Any]
) -> Tuple[
    Dict[str, Any],
    List[Dict[str, Any]],
    Dict[str, Any],
    List[Dict[str, Any]],
    Dict[str, Any],
]:
    """Load the committed all-20 official-image cohort and exact scope authority."""

    try:
        authorization, targets, freeze, acquisitions = (
            pilot3_met_r2.require_committed_image_acquisitions(root)
        )
    except pilot3_met_r2.Pilot3MetR2Error as exc:
        raise Pilot3PhaseAError(
            "committed complete Met R2 official-image evidence is required"
        ) from exc
    scope = _require_normalization_scope(root, config)
    met_scope = scope["eligible_membership"]["met_r2"]
    if met_scope.get("authorization_sha256") != authorization.get(
        "authorization_sha256"
    ) or met_scope.get("metadata_freeze_sha256") != freeze.get("freeze_sha256"):
        raise Pilot3PhaseAError(
            "normalization scope does not bind the committed Met R2 closure"
        )
    return authorization, targets, freeze, acquisitions, scope


def _met_r2_normalized_acquisition(
    root: Path,
    config: Mapping[str, Any],
    split: Mapping[str, Any],
    authorization: Mapping[str, Any],
    target: Mapping[str, Any],
    freeze: Mapping[str, Any],
    r2_acquisition: Mapping[str, Any],
    scope: Mapping[str, Any],
    *,
    normalized: bytes,
    decode: Mapping[str, Any],
    normalized_path: Path,
) -> Dict[str, Any]:
    """Construct the deterministic schema-v3 bridge without legacy Commons fields."""

    work_id = str(split["canonical_work_id"])
    object_id = str(split["source_object_id"])
    authorization_targets = authorization.get("targets")
    bound_targets = [
        value
        for value in authorization_targets or []
        if isinstance(value, Mapping)
        and value.get("physical_work_id") == work_id
        and str(value.get("object_id")) == object_id
    ]
    if len(bound_targets) != 1:
        raise Pilot3PhaseAError("Met R2 authorization target is missing or duplicated")
    authorized_target = bound_targets[0]
    expected_physical = {
        "physical_work_id": work_id,
        "object_id": object_id,
        "artist_id": split["artist_id"],
        "partition": split["partition"],
    }
    for candidate, label in (
        (target, "target"),
        (r2_acquisition, "image acquisition"),
    ):
        if any(candidate.get(key) != value for key, value in expected_physical.items()):
            raise Pilot3PhaseAError(f"Met R2 {label} changed physical-work identity")
    if (
        target.get("r2_asset_id") != r2_acquisition.get("r2_asset_id")
        or target.get("row_sha256") != r2_acquisition.get("target_row_sha256")
        or target.get("primary_image_url") != r2_acquisition.get("primary_image_url")
        or authorized_target.get("r2_asset_id") != target.get("r2_asset_id")
        or authorized_target.get("frozen_split_row_sha256") != split.get("row_sha256")
        or authorized_target.get("frozen_selection_sha256")
        != split.get("selection_sha256")
        or authorized_target.get("accession_number") != split.get("museum_accession")
    ):
        raise Pilot3PhaseAError("Met R2 digital target lineage is inconsistent")
    _verify_scope_member(
        scope,
        split,
        primary_image_url=str(target["primary_image_url"]),
        target_row_sha256=str(target["row_sha256"]),
    )
    if (
        decode.get("decoded_width") != r2_acquisition.get("decoded_width")
        or decode.get("decoded_height") != r2_acquisition.get("decoded_height")
        or str(decode.get("decoded_format", "")).upper()
        != r2_acquisition.get("decoded_format")
        or decode.get("decoded_mode") != r2_acquisition.get("decoded_mode")
        or decode.get("domain_checks") != r2_acquisition.get("domain_checks")
    ):
        raise Pilot3PhaseAError(
            "Met R2 normalization does not match first-response geometry"
        )
    raw_path = str(r2_acquisition["raw_image_path"])
    raw_sha256 = str(r2_acquisition["raw_image_sha256"])
    raw_byte_count = r2_acquisition["raw_image_byte_count"]
    normalized_sha256 = hash_bytes(normalized)
    lineage = _normalization_authority_lineage(
        scope, schema=pilot3_normalization_scope.SCHEMA_VERSION
    )
    payload = {
        "record_type": "pilot3_real_acquisition",
        "schema_version": MET_R2_NORMALIZED_ACQUISITION_SCHEMA,
        "canonical_work_id": work_id,
        "artist_id": split["artist_id"],
        "collection_block_id": split["collection_block_id"],
        "museum_accession": split["museum_accession"],
        "source_id": split["source_id"],
        "source_object_id": object_id,
        "partition": split["partition"],
        "frozen_split_row_sha256": split["row_sha256"],
        "physical_work_source_url": split["source_url"],
        "asset_provider": MET_R2_ASSET_PROVIDER,
        "image_url": target["primary_image_url"],
        "source_url": authorized_target["object_endpoint"],
        "delivery_width": decode["decoded_width"],
        "delivery_height": decode["decoded_height"],
        "acquisition_route": "met_r2_official_primary_image",
        "acquisition_completion_route": "met_r2_committed_image_acquisition",
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "external_protocol_result_sha256": None,
        "external_unseal_receipt_sha256": None,
        "raw_path": raw_path,
        "raw_sha256": raw_sha256,
        "raw_byte_count": raw_byte_count,
        "normalized_path": _portable(normalized_path, root),
        "normalized_sha256": normalized_sha256,
        "normalized_byte_count": len(normalized),
        "base_common_preprocessing_config_sha256": stable_hash(
            config["common_preprocessing"]
        ),
        "common_preprocessing_config_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "preprocessing_determinism_amendment_sha256": None,
        "effective_preprocessing_contract_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        **lineage,
        "digital_asset_protocol_namespace": pilot3_met_r2.NAMESPACE,
        "r2_asset_id": target["r2_asset_id"],
        "r2_authorization_sha256": authorization["authorization_sha256"],
        "r2_metadata_freeze_sha256": freeze["freeze_sha256"],
        "r2_target_row_sha256": target["row_sha256"],
        "r2_image_terminal_event_sha256": r2_acquisition["image_terminal_event_sha256"],
        "r2_image_acquisition_record_sha256": r2_acquisition["record_sha256"],
        "r2_cohort_observation_sha256": r2_acquisition["cohort_observation_sha256"],
        **dict(decode),
        "response_evidence": {
            "transport": "committed_met_r2_official_primaryImage",
            "metadata_freeze_sha256": freeze["freeze_sha256"],
            "target_row_sha256": target["row_sha256"],
            "image_terminal_event_sha256": r2_acquisition[
                "image_terminal_event_sha256"
            ],
            "image_acquisition_record_sha256": r2_acquisition["record_sha256"],
            "cohort_observation_sha256": r2_acquisition["cohort_observation_sha256"],
        },
    }
    return _self_hash(payload, "record_sha256")


def _materialize_met_r2_development_acquisitions(
    root: Path,
    config: Mapping[str, Any],
    splits: Sequence[Mapping[str, Any]],
    acquisitions: Dict[str, Dict[str, Any]],
) -> None:
    """Append only the exact committed official-Met cohort to the legacy ledger."""

    met_splits = [row for row in splits if row.get("source_id") == "met"]
    if len(met_splits) != 20:
        raise Pilot3PhaseAError("Met R2 bridge requires exactly twenty frozen works")
    expected_met_order = [str(row["canonical_work_id"]) for row in met_splits]
    existing_met_order = [
        str(row.get("canonical_work_id"))
        for row in acquisitions.values()
        if row.get("source_id") == "met"
    ]
    if existing_met_order != expected_met_order[: len(existing_met_order)]:
        raise Pilot3PhaseAError(
            "persisted Met R2 normalized acquisitions are not a deterministic prefix"
        )
    for work_id, existing in acquisitions.items():
        if existing.get("source_id") == "met" and existing.get("schema_version") != (
            MET_R2_NORMALIZED_ACQUISITION_SCHEMA
        ):
            raise Pilot3PhaseAError(
                "legacy Met/Commons acquisition is quarantined and cannot be admitted: "
                + work_id
            )
    authorization, targets, freeze, r2_acquisitions, scope = (
        _require_met_r2_normalization_inputs(root, config)
    )
    target_by_work = {str(row["physical_work_id"]): row for row in targets}
    r2_by_work = {str(row["physical_work_id"]): row for row in r2_acquisitions}
    expected_ids = {str(row["canonical_work_id"]) for row in met_splits}
    if set(target_by_work) != expected_ids or set(r2_by_work) != expected_ids:
        raise Pilot3PhaseAError(
            "Met R2 closure is not the exact frozen twenty-work cohort"
        )

    prepared: List[Tuple[Mapping[str, Any], bytes, Path, Dict[str, Any]]] = []
    normalized_dir = _resolve(root, config["paths"]["normalized_dir"])
    for split in met_splits:
        work_id = str(split["canonical_work_id"])
        r2_acquisition = r2_by_work[work_id]
        raw_path = _resolve(root, str(r2_acquisition["raw_image_path"]))
        raw_payload = raw_path.read_bytes()
        if hash_bytes(raw_payload) != r2_acquisition.get("raw_image_sha256") or len(
            raw_payload
        ) != r2_acquisition.get("raw_image_byte_count"):
            raise Pilot3PhaseAError("Met R2 raw CAS changed after cohort verification")
        decode, normalized = _decode_and_normalize(raw_payload, config)
        normalized_sha256 = hash_bytes(normalized)
        normalized_path = (
            normalized_dir / normalized_sha256[:2] / f"{normalized_sha256}.png"
        )
        row = _met_r2_normalized_acquisition(
            root,
            config,
            split,
            authorization,
            target_by_work[work_id],
            freeze,
            r2_acquisition,
            scope,
            normalized=normalized,
            decode=decode,
            normalized_path=normalized_path,
        )
        existing = acquisitions.get(work_id)
        if existing is not None and existing != row:
            raise Pilot3PhaseAError(
                "persisted Met R2 normalized acquisition is stale: " + work_id
            )
        prepared.append((split, normalized, normalized_path, row))

    acquisition_path = _phase_ledger_path(root, config, "development", "acquisitions")
    for split, normalized, normalized_path, row in prepared:
        work_id = str(split["canonical_work_id"])
        if (
            normalized_path.exists()
            and hash_file(normalized_path) != row["normalized_sha256"]
        ):
            raise Pilot3PhaseAError(
                "Met R2 normalization CAS collision at " + str(normalized_path)
            )
        if not normalized_path.exists():
            _atomic_bytes(normalized_path, normalized)
        if work_id not in acquisitions:
            _append_jsonl_fsync(acquisition_path, row)
            acquisitions[work_id] = row


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
    resolution = require_preprocessing_incident_resolution(root)
    normalization_amendment = resolution["amendment"]
    phase = "external" if row.get("partition") == EXTERNAL_PARTITION else "development"
    normalization_authorization: Optional[Mapping[str, Any]] = None
    if phase == "external" and row.get("schema_version") == (
        MET_R2_NORMALIZED_ACQUISITION_SCHEMA
    ):
        normalization_authorization = _require_normalization_scope(root, config)
        normalization_amendment = None
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
    history = _verified_http_attempt_histories(
        root,
        config,
        phase,
        intents,
        normalization_amendment=normalization_amendment,
        normalization_authorization=normalization_authorization,
    )[str(expected_intent["intent_id"])]
    starts = history[::2]
    successful_terminal: Optional[Mapping[str, Any]] = None
    completion_route = row.get("acquisition_completion_route")
    intent_route = expected_intent.get("acquisition_route")
    browser_terminal: Optional[Mapping[str, Any]] = None
    if intent_route == "network" and completion_route == "httpx_get":
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
    elif (
        intent_route in {"network", "browser_recovery"}
        and completion_route == "browser_download_import"
    ):
        if intent_route == "network":
            if (
                len(history) != 2
                or history[-1].get("outcome") != "http_status_failure"
                or history[-1].get("http_status") != 403
            ):
                raise Pilot3PhaseAError(
                    "trigger browser acquisition must retain its exact failed HTTP history"
                )
        elif history:
            raise Pilot3PhaseAError(
                "first-route browser acquisition unexpectedly has HTTP attempts"
            )
        incident = verify_preprocessing_determinism_incident(root)
        authorization = _verify_historical_aic_browser_recovery_authorization(
            root, incident=incident, require_committed=True
        )
        browser_histories = _verified_browser_attempt_histories(
            root,
            config,
            authorization,
            intents,
            normalization_amendment=resolution["amendment"],
        )
        browser_history = browser_histories.get(str(expected_intent["intent_id"]), [])
        if len(browser_history) != 2:
            raise Pilot3PhaseAError("browser acquisition lacks a completed browser attempt")
        browser_terminal = browser_history[-1]
        if (
            browser_terminal.get("raw_path") != row.get("raw_path")
            or browser_terminal.get("raw_sha256") != row.get("raw_sha256")
            or browser_terminal.get("raw_byte_count") != row.get("raw_byte_count")
            or row.get("response_evidence")
            != _browser_response_evidence(browser_terminal)
            or row.get("browser_attempt_id")
            != browser_terminal.get("browser_attempt_id")
            or row.get("browser_terminal_event_sha256")
            != browser_terminal.get("event_sha256")
            or row.get("browser_authorization_sha256")
            != browser_terminal.get("authorization_sha256")
        ):
            raise Pilot3PhaseAError(
                "browser acquisition disagrees with browser terminal evidence"
            )
    elif intent_route == "prior_local_reproduction" and completion_route == (
        "prior_local_reproduction"
    ):
        if history:
            raise Pilot3PhaseAError("prior-local acquisition unexpectedly has HTTP attempts")
        response = row.get("response_evidence")
        if not isinstance(response, Mapping) or response.get("technical_attempt_count") != 0:
            raise Pilot3PhaseAError("prior-local acquisition has stale response evidence")
    else:
        raise Pilot3PhaseAError("acquisition intent/completion route combination is unknown")
    expected_browser_binding = {
        "browser_attempt_id": (
            browser_terminal["browser_attempt_id"]
            if browser_terminal is not None
            else None
        ),
        "browser_terminal_event_sha256": (
            browser_terminal["event_sha256"]
            if browser_terminal is not None
            else None
        ),
        "browser_authorization_sha256": (
            browser_terminal["authorization_sha256"]
            if browser_terminal is not None
            else None
        ),
    }
    if any(row.get(key) != value for key, value in expected_browser_binding.items()):
        raise Pilot3PhaseAError("acquisition browser-attempt binding is stale")
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


def _verify_existing_met_r2_acquisition(
    row: Mapping[str, Any],
    root: Path,
    split: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    if split.get("source_id") != "met":
        raise Pilot3PhaseAError("Met R2 schema is attached to a non-Met split")
    authorization, targets, freeze, acquisitions, scope = (
        _require_met_r2_normalization_inputs(root, config)
    )
    work_id = str(split["canonical_work_id"])
    target_by_work = {str(value["physical_work_id"]): value for value in targets}
    r2_by_work = {str(value["physical_work_id"]): value for value in acquisitions}
    if work_id not in target_by_work or work_id not in r2_by_work:
        raise Pilot3PhaseAError("Met R2 acquisition is outside the complete cohort")
    r2_acquisition = r2_by_work[work_id]
    raw_path = _resolve(root, str(r2_acquisition["raw_image_path"]))
    raw_payload = raw_path.read_bytes()
    decode, normalized = _decode_and_normalize(raw_payload, config)
    normalized_sha256 = hash_bytes(normalized)
    normalized_path = (
        _resolve(root, config["paths"]["normalized_dir"])
        / normalized_sha256[:2]
        / f"{normalized_sha256}.png"
    )
    expected = _met_r2_normalized_acquisition(
        root,
        config,
        split,
        authorization,
        target_by_work[work_id],
        freeze,
        r2_acquisition,
        scope,
        normalized=normalized,
        decode=decode,
        normalized_path=normalized_path,
    )
    if dict(row) != expected:
        raise Pilot3PhaseAError("existing Met R2 normalized acquisition is stale")
    if (
        not normalized_path.is_file()
        or normalized_path.stat().st_size != len(normalized)
        or hash_file(normalized_path) != normalized_sha256
        or normalized_path.read_bytes() != normalized
    ):
        raise Pilot3PhaseAError("Met R2 normalized CAS is missing or stale")
    legacy_url = str(split.get("image_url", ""))
    if (
        row.get("asset_provider") == split.get("asset_provider")
        or row.get("image_url") == legacy_url
        or "wikimedia" in str(row.get("asset_provider", "")).casefold()
        or "wikimedia" in str(row.get("image_url", "")).casefold()
        or "/real_raw/" in str(row.get("raw_path", ""))
    ):
        raise Pilot3PhaseAError("legacy Commons digital asset escaped quarantine")


def _verify_existing_acquisition(
    row: Mapping[str, Any],
    root: Path,
    split: Mapping[str, Any],
    config: Mapping[str, Any],
    external_unseal_token: Optional[str],
    *,
    expected_external_receipt_sha256: Optional[str] = None,
) -> None:
    resolution = require_preprocessing_incident_resolution(root)
    amendment = resolution["amendment"]
    verify_self_hash(row, "record_sha256")
    if row.get("schema_version") == MET_R2_NORMALIZED_ACQUISITION_SCHEMA and (
        split.get("source_id") == "met"
    ):
        if (
            external_unseal_token is not None
            or expected_external_receipt_sha256 is not None
        ):
            raise Pilot3PhaseAError(
                "development Met R2 acquisition received external state"
            )
        _verify_existing_met_r2_acquisition(row, root, split, config)
        return
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
    is_v2 = row.get("schema_version") in {
        "2.0",
        MET_R2_NORMALIZED_ACQUISITION_SCHEMA,
    }
    is_generic_v2 = row.get("schema_version") == MET_R2_NORMALIZED_ACQUISITION_SCHEMA
    if is_generic_v2:
        scope = _require_normalization_scope(root, config)
        _verify_scope_member(scope, split)
        if (
            row.get("normalization_protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or row.get("preprocessing_determinism_amendment_sha256") is not None
            or row.get("normalization_authorization_schema")
            != pilot3_normalization_scope.SCHEMA_VERSION
            or row.get("normalization_authorization_sha256")
            != scope["authorization_sha256"]
            or row.get("base_common_preprocessing_config_sha256")
            != stable_hash(config["common_preprocessing"])
            or row.get("common_preprocessing_config_sha256")
            != _effective_preprocessing_contract_sha256(config)
            or row.get("effective_preprocessing_contract_sha256")
            != _effective_preprocessing_contract_sha256(config)
        ):
            raise Pilot3PhaseAError("schema-v3 acquisition binds stale preprocessing")
    elif is_v2:
        if (
            row.get("normalization_protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or row.get("preprocessing_determinism_amendment_sha256")
            != amendment["authorization_sha256"]
            or row.get("base_common_preprocessing_config_sha256")
            != stable_hash(config["common_preprocessing"])
            or row.get("common_preprocessing_config_sha256")
            != _effective_preprocessing_contract_sha256(config)
            or row.get("effective_preprocessing_contract_sha256")
            != _effective_preprocessing_contract_sha256(config)
        ):
            raise Pilot3PhaseAError("v2 acquisition binds stale preprocessing")
    else:
        correction = resolution["corrections"].get(
            str(row.get("canonical_work_id", ""))
        )
        if (
            row.get("schema_version") != "1.0"
            or correction is None
            or correction.get("original_acquisition_record_sha256")
            != row.get("record_sha256")
            or row.get("common_preprocessing_config_sha256")
            != stable_hash(config["common_preprocessing"])
        ):
            raise Pilot3PhaseAError(
                "historical acquisition lacks its normalization revalidation"
            )
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
    if is_v2:
        raw_payload = _resolve(root, str(row["raw_path"])).read_bytes()
        decode, normalized = _decode_and_normalize(
            raw_payload,
            config,
            expected_width=int(split["delivery_width"]),
            expected_height=int(split["delivery_height"]),
        )
        if (
            hash_bytes(normalized) != row.get("normalized_sha256")
            or len(normalized) != row.get("normalized_byte_count")
            or any(row.get(key) != value for key, value in decode.items())
        ):
            raise Pilot3PhaseAError("v2 acquisition does not recompute exactly")
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


def _materialize_real_acquisition(
    root: Path,
    config: Mapping[str, Any],
    split: Mapping[str, Any],
    intent: Mapping[str, Any],
    payload: bytes,
    response_evidence: Mapping[str, Any],
    http_history: Sequence[Mapping[str, Any]],
    *,
    acquisition_completion_route: str,
    browser_terminal: Optional[Mapping[str, Any]],
    external_unseal_token: Optional[str],
    external_unseal_receipt_sha256: Optional[str],
    normalization_amendment: Optional[Mapping[str, Any]] = None,
    normalization_authorization: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Create one canonical acquisition row from its already-durable byte transport."""

    phase = "external" if split["partition"] == EXTERNAL_PARTITION else "development"
    acquisition_path = _phase_ledger_path(root, config, phase, "acquisitions")
    acquisitions = _read_existing_rows(acquisition_path, "canonical_work_id")
    work_id = str(split["canonical_work_id"])
    existing = acquisitions.get(work_id)
    if existing is not None:
        _verify_existing_acquisition(
            existing,
            root,
            split,
            config,
            external_unseal_token,
            expected_external_receipt_sha256=external_unseal_receipt_sha256,
        )
        return existing
    if normalization_amendment is not None and normalization_authorization is not None:
        raise Pilot3PhaseAError(
            "new acquisition received two normalization authorities"
        )
    if normalization_amendment is None and normalization_authorization is None:
        raise Pilot3PhaseAError(
            "new acquisition requires a committed normalization authority"
        )
    if normalization_amendment is not None:
        if normalization_amendment.get("normalization_protocol_version") != (
            PILOT3_NORMALIZATION_PROTOCOL_VERSION
        ):
            raise Pilot3PhaseAError(
                "new acquisition received a stale normalization amendment"
            )
        schema_version = "2.0"
        normalization_lineage: Dict[str, Any] = {
            "preprocessing_determinism_amendment_sha256": (
                normalization_amendment["authorization_sha256"]
            )
        }
    else:
        assert normalization_authorization is not None
        _verify_scope_member(normalization_authorization, split)
        implementation = normalization_authorization.get("normalization_implementation")
        if (
            not isinstance(implementation, Mapping)
            or implementation.get("protocol_version")
            != PILOT3_NORMALIZATION_PROTOCOL_VERSION
            or implementation.get("effective_preprocessing_contract_sha256")
            != _effective_preprocessing_contract_sha256(config)
        ):
            raise Pilot3PhaseAError(
                "new acquisition received a stale normalization scope"
            )
        schema_version = MET_R2_NORMALIZED_ACQUISITION_SCHEMA
        normalization_lineage = {
            "preprocessing_determinism_amendment_sha256": None,
            **_normalization_authority_lineage(
                normalization_authorization,
                schema=pilot3_normalization_scope.SCHEMA_VERSION,
            ),
            "digital_asset_protocol_namespace": (
                "pilot3-external-official-assets"
                if split.get("partition") == EXTERNAL_PARTITION
                else "pilot3-normalization-scope-member"
            ),
        }
    decode, normalized = _decode_and_normalize(
        payload,
        config,
        expected_width=int(split["delivery_width"]),
        expected_height=int(split["delivery_height"]),
    )
    raw_sha = hash_bytes(payload)
    normalized_sha = hash_bytes(normalized)
    raw_path = _resolve(root, config["paths"]["raw_dir"]) / raw_sha[:2] / f"{raw_sha}.bin"
    normalized_path = (
        _resolve(root, config["paths"]["normalized_dir"])
        / normalized_sha[:2]
        / f"{normalized_sha}.png"
    )
    for path, content, digest in (
        (raw_path, payload, raw_sha),
        (normalized_path, normalized, normalized_sha),
    ):
        if path.exists() and hash_file(path) != digest:
            raise Pilot3PhaseAError(f"acquisition CAS collision at {path}")
        if not path.exists():
            _atomic_bytes(path, content)
    successful_http_terminal = (
        http_history[-1]
        if http_history and http_history[-1].get("outcome") == "success"
        else None
    )
    record_payload = {
        "record_type": "pilot3_real_acquisition",
        "schema_version": schema_version,
        "canonical_work_id": work_id,
        "artist_id": split["artist_id"],
        "asset_provider": split["asset_provider"],
        "collection_block_id": split["collection_block_id"],
        "museum_accession": split["museum_accession"],
        "source_id": split["source_id"],
        "source_object_id": split["source_object_id"],
        "partition": split["partition"],
        "intent_id": intent["intent_id"],
        "acquisition_route": intent["acquisition_route"],
        "acquisition_completion_route": acquisition_completion_route,
        "image_url": split["image_url"],
        "source_url": split["source_url"],
        "delivery_width": split["delivery_width"],
        "delivery_height": split["delivery_height"],
        "phase_a_config_file_sha256": hash_file(_resolve(root, DEFAULT_CONFIG)),
        "external_protocol_result_sha256": (
            external_unseal_token if phase == "external" else None
        ),
        "external_unseal_receipt_sha256": external_unseal_receipt_sha256,
        "raw_path": _portable(raw_path, root),
        "raw_sha256": raw_sha,
        "raw_byte_count": len(payload),
        "normalized_path": _portable(normalized_path, root),
        "normalized_sha256": normalized_sha,
        "normalized_byte_count": len(normalized),
        "base_common_preprocessing_config_sha256": stable_hash(
            config["common_preprocessing"]
        ),
        "common_preprocessing_config_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        **normalization_lineage,
        "effective_preprocessing_contract_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
        "http_attempt_ids": [
            str(event["attempt_id"])
            for event in http_history
            if event["event_type"] == "start"
        ],
        "http_attempt_count": len(http_history) // 2,
        "http_attempt_event_count": len(http_history),
        "http_attempt_history_semantic_sha256": stable_hash(list(http_history)),
        "successful_http_attempt_id": (
            successful_http_terminal["attempt_id"]
            if successful_http_terminal is not None
            else None
        ),
        "successful_http_terminal_event_sha256": (
            successful_http_terminal["event_sha256"]
            if successful_http_terminal is not None
            else None
        ),
        "browser_attempt_id": (
            browser_terminal["browser_attempt_id"]
            if browser_terminal is not None
            else None
        ),
        "browser_terminal_event_sha256": (
            browser_terminal["event_sha256"]
            if browser_terminal is not None
            else None
        ),
        "browser_authorization_sha256": (
            browser_terminal["authorization_sha256"]
            if browser_terminal is not None
            else None
        ),
        **decode,
        "response_evidence": dict(response_evidence),
    }
    record = _self_hash(record_payload, "record_sha256")
    _append_jsonl_fsync(acquisition_path, record)
    _verify_existing_acquisition(
        record,
        root,
        split,
        config,
        external_unseal_token,
        expected_external_receipt_sha256=external_unseal_receipt_sha256,
    )
    return record


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
    resolution = require_preprocessing_incident_resolution(root)
    normalization_amendment = resolution["amendment"]
    normalization_authorization: Optional[Mapping[str, Any]] = None
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
        normalization_authorization = _require_normalization_scope(root, config)
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
    if phase == "development" and any(
        split.get("source_id") == "met" for split in splits
    ):
        _materialize_met_r2_development_acquisitions(root, config, splits, acquisitions)
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
    _verified_http_attempt_histories(
        root,
        config,
        phase,
        intents,
        normalization_amendment=(
            normalization_amendment if phase == "development" else None
        ),
        normalization_authorization=normalization_authorization,
    )

    for split in splits:
        work_id = str(split["canonical_work_id"])
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

        existing_intent = intents_by_work.get(work_id)
        if (
            phase == "development"
            and split["source_id"] == "aic"
            and existing_intent is None
        ):
            raise Pilot3PhaseAError(
                "AIC acquisition requires a durable browser-recovery prepare before resume: "
                + work_id
            )
        acquisition_route = (
            str(existing_intent["acquisition_route"])
            if existing_intent is not None
            else "network"
        )
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

        if phase == "development" and split["source_id"] == "aic":
            expected_aic_route = (
                "network"
                if work_id == str(_aic_development_splits(root, config)[0]["canonical_work_id"])
                else "browser_recovery"
            )
            if acquisition_route != expected_aic_route or prior_path is not None:
                raise Pilot3PhaseAError(
                    "AIC acquisition route disagrees with the frozen browser authorization: "
                    + work_id
                )

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
        if existing_intent is not None and existing_intent != intent:
            raise Pilot3PhaseAError(
                f"durable acquisition intent changed or its route drifted: {work_id}"
            )
        if existing_intent is None:
            _append_jsonl_fsync(intent_path, intent)
            intents[intent_id] = intent
            intents_by_work[work_id] = intent

        browser_terminal: Optional[Mapping[str, Any]] = None
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
                root,
                config,
                phase,
                intents,
                normalization_amendment=(
                    normalization_amendment if phase == "development" else None
                ),
                normalization_authorization=normalization_authorization,
            )[intent_id]
            if http_history:
                raise Pilot3PhaseAError(
                    f"prior-local acquisition has recorded HTTP attempts: {work_id}"
                )
            completion_route = "prior_local_reproduction"
        else:
            browser_recovery = (
                _browser_recovery_for_intent(root, config, intent)
                if phase == "development" and split["source_id"] == "aic"
                else None
            )
            if browser_recovery is not None:
                payload, response_evidence, browser_terminal = browser_recovery
                http_history = _verified_http_attempt_histories(
                    root,
                    config,
                    phase,
                    intents,
                    normalization_amendment=(
                        normalization_amendment if phase == "development" else None
                    ),
                    normalization_authorization=normalization_authorization,
                )[intent_id]
                completion_route = "browser_download_import"
            else:
                if phase == "development" and split["source_id"] == "aic":
                    raise Pilot3PhaseAError(
                        "AIC browser intent has no completed recovery terminal"
                    )
                payload, response_evidence, http_history = _download_image_bytes(
                    root,
                    config,
                    phase,
                    intent,
                    normalization_amendment=(
                        normalization_amendment if phase == "development" else None
                    ),
                    normalization_authorization=normalization_authorization,
                )
                completion_route = "httpx_get"

        record = _materialize_real_acquisition(
            root,
            config,
            split,
            intent,
            payload,
            response_evidence,
            http_history,
            acquisition_completion_route=completion_route,
            browser_terminal=browser_terminal,
            external_unseal_token=external_unseal_token,
            external_unseal_receipt_sha256=external_receipt_sha256,
            normalization_amendment=(
                normalization_amendment if phase == "development" else None
            ),
            normalization_authorization=normalization_authorization,
        )
        acquisitions[work_id] = record

    effective = effective_acquisition_rows(
        root, config, phase, acquisitions, require_committed=True
    )
    result = [effective[str(row["canonical_work_id"])] for row in splits]
    for original in acquisitions.values():
        split = next(
            item
            for item in splits
            if item["canonical_work_id"] == original["canonical_work_id"]
        )
        _verify_existing_acquisition(
            original,
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
    expected_schema = (
        "3.0"
        if _is_sha256(acquisition.get("normalization_authorization_sha256"))
        else "2.0"
    )
    if (
        row.get("record_type") != "pilot3_real_a_vector"
        or row.get("schema_version") != expected_schema
    ):
        raise Pilot3PhaseAError("A-vector row schema is stale")
    for key in (
        "canonical_work_id",
        "artist_id",
        "collection_block_id",
        "museum_accession",
        "source_id",
        "partition",
    ):
        if row.get(key) != split.get(key):
            raise Pilot3PhaseAError(f"A-vector {key} disagrees with the frozen split")
    digital_fields = ("asset_provider", "delivery_height", "delivery_width")
    if expected_schema == "3.0":
        digital_fields = (*digital_fields, "image_url")
    if any(row.get(key) != acquisition.get(key) for key in digital_fields):
        raise Pilot3PhaseAError(
            "A-vector digital reproduction fields disagree with acquisition"
        )
    if row.get("normalized_sha256") != acquisition.get("normalized_sha256"):
        raise Pilot3PhaseAError("feature binds a stale normalized input")
    if row.get("raw_sha256") != acquisition.get("raw_sha256"):
        raise Pilot3PhaseAError("feature binds stale raw museum bytes")
    for key in (
        "normalization_protocol_version",
        "base_common_preprocessing_config_sha256",
        "common_preprocessing_config_sha256",
        "preprocessing_determinism_amendment_sha256",
        "effective_preprocessing_contract_sha256",
        "effective_acquisition_sha256",
        "original_acquisition_record_sha256",
        "normalization_revalidation_record_sha256",
        *GENERIC_NORMALIZATION_LINEAGE_FIELDS,
        *MET_R2_LINEAGE_FIELDS,
    ):
        if key in acquisition or key in row:
            if row.get(key) == acquisition.get(key):
                continue
            raise Pilot3PhaseAError(
                "feature binds stale effective normalization lineage: " + key
            )
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
        "normalization_protocol_version": acquisition[
            "normalization_protocol_version"
        ],
        "base_common_preprocessing_config_sha256": acquisition[
            "base_common_preprocessing_config_sha256"
        ],
        "common_preprocessing_config_sha256": acquisition[
            "common_preprocessing_config_sha256"
        ],
        "preprocessing_determinism_amendment_sha256": acquisition[
            "preprocessing_determinism_amendment_sha256"
        ],
        "effective_preprocessing_contract_sha256": acquisition[
            "effective_preprocessing_contract_sha256"
        ],
        "effective_acquisition_sha256": acquisition[
            "effective_acquisition_sha256"
        ],
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
    for key in (*GENERIC_NORMALIZATION_LINEAGE_FIELDS, *MET_R2_LINEAGE_FIELDS):
        if key in acquisition:
            expected_metadata[key] = acquisition[key]
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
    require_preprocessing_incident_resolution(root)
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
    effective_acquisitions = effective_acquisition_rows(
        root, config, phase, acquisitions, require_committed=True
    )

    feature_path = _phase_ledger_path(root, config, phase, "features")
    features = _read_existing_rows(feature_path, "canonical_work_id")
    if not set(features) <= expected_ids:
        raise Pilot3PhaseAError(f"{phase} feature ledger contains an unselected work")
    loaded = None
    section = config["a_vector"]
    config_sha = hash_file(_resolve(root, config_path))
    for split in split_rows:
        work_id = str(split["canonical_work_id"])
        original = acquisitions[work_id]
        _verify_existing_acquisition(
            original,
            root,
            split,
            config,
            external_unseal_token,
            expected_external_receipt_sha256=external_receipt_sha256,
        )
        acquired = effective_acquisitions[work_id]
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
                "normalization_protocol_version": acquired[
                    "normalization_protocol_version"
                ],
                "base_common_preprocessing_config_sha256": acquired[
                    "base_common_preprocessing_config_sha256"
                ],
                "common_preprocessing_config_sha256": acquired[
                    "common_preprocessing_config_sha256"
                ],
                "preprocessing_determinism_amendment_sha256": acquired[
                    "preprocessing_determinism_amendment_sha256"
                ],
                "effective_preprocessing_contract_sha256": acquired[
                    "effective_preprocessing_contract_sha256"
                ],
                "effective_acquisition_sha256": acquired[
                    "effective_acquisition_sha256"
                ],
                **{
                    key: acquired[key]
                    for key in (
                        *GENERIC_NORMALIZATION_LINEAGE_FIELDS,
                        *MET_R2_LINEAGE_FIELDS,
                    )
                    if key in acquired
                },
            }
        )
        row_payload: Dict[str, Any] = {
            "record_type": "pilot3_real_a_vector",
            "schema_version": (
                "3.0"
                if _is_sha256(acquired.get("normalization_authorization_sha256"))
                else "2.0"
            ),
            "canonical_work_id": work_id,
            "artist_id": split["artist_id"],
            "asset_provider": acquired["asset_provider"],
            **(
                {"image_url": acquired["image_url"]}
                if _is_sha256(acquired.get("normalization_authorization_sha256"))
                else {}
            ),
            "collection_block_id": split["collection_block_id"],
            "museum_accession": split["museum_accession"],
            "delivery_width": acquired["delivery_width"],
            "delivery_height": acquired["delivery_height"],
            "source_id": split["source_id"],
            "partition": split["partition"],
            "normalized_sha256": acquired["normalized_sha256"],
            "raw_sha256": acquired["raw_sha256"],
            "normalization_protocol_version": acquired[
                "normalization_protocol_version"
            ],
            "base_common_preprocessing_config_sha256": acquired[
                "base_common_preprocessing_config_sha256"
            ],
            "common_preprocessing_config_sha256": acquired[
                "common_preprocessing_config_sha256"
            ],
            "preprocessing_determinism_amendment_sha256": acquired[
                "preprocessing_determinism_amendment_sha256"
            ],
            "effective_preprocessing_contract_sha256": acquired[
                "effective_preprocessing_contract_sha256"
            ],
            "effective_acquisition_sha256": acquired[
                "effective_acquisition_sha256"
            ],
            "original_acquisition_record_sha256": acquired[
                "original_acquisition_record_sha256"
            ],
            "normalization_revalidation_record_sha256": acquired[
                "normalization_revalidation_record_sha256"
            ],
            **{
                key: acquired[key]
                for key in (
                    *GENERIC_NORMALIZATION_LINEAGE_FIELDS,
                    *MET_R2_LINEAGE_FIELDS,
                )
                if key in acquired
            },
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
            effective_acquisitions[str(row["canonical_work_id"])],
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
    require_preprocessing_incident_resolution(root)
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
    effective_acquisitions = effective_acquisition_rows(
        root, config, "development", acquisitions, require_committed=True
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
        if work_id not in acquisitions or work_id not in features:
            raise Pilot3PhaseAError(f"probe input or first extraction is missing: {work_id}")
        acquired = effective_acquisitions[work_id]
        _verify_existing_acquisition(acquisitions[work_id], root, split, config, None)
        _verify_feature(features[work_id], acquired, split, config)
        metadata = features[work_id].get("extraction_metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("seed"), int):
            raise Pilot3PhaseAError(f"determinism probe seed is missing: {work_id}")
        first_hash = str(features[work_id]["vector_sha256"])
        common_payload = {
            "record_type": "pilot3_a_vector_determinism_probe",
            "schema_version": (
                "3.0"
                if _is_sha256(acquired.get("normalization_authorization_sha256"))
                else "2.0"
            ),
            "canonical_work_id": work_id,
            "artist_id": split["artist_id"],
            "source_id": split["source_id"],
            "normalized_sha256": acquired["normalized_sha256"],
            "normalization_protocol_version": acquired[
                "normalization_protocol_version"
            ],
            "base_common_preprocessing_config_sha256": acquired[
                "base_common_preprocessing_config_sha256"
            ],
            "common_preprocessing_config_sha256": acquired[
                "common_preprocessing_config_sha256"
            ],
            "preprocessing_determinism_amendment_sha256": acquired[
                "preprocessing_determinism_amendment_sha256"
            ],
            "effective_preprocessing_contract_sha256": acquired[
                "effective_preprocessing_contract_sha256"
            ],
            "effective_acquisition_sha256": acquired[
                "effective_acquisition_sha256"
            ],
            "normalization_revalidation_record_sha256": acquired[
                "normalization_revalidation_record_sha256"
            ],
            **{
                field: acquired[field]
                for field in (
                    *GENERIC_NORMALIZATION_LINEAGE_FIELDS,
                    *MET_R2_LINEAGE_FIELDS,
                )
                if field in acquired
            },
            "first_vector_sha256": first_hash,
            "seed": metadata["seed"],
        }
        if work_id in probes:
            expected = _self_hash(
                {
                    **common_payload,
                    "repeated_vector_sha256": first_hash,
                    "exact_equal": True,
                },
                "record_sha256",
            )
            if probes[work_id] != expected:
                raise Pilot3PhaseAError(f"persisted determinism probe is stale: {work_id}")
            continue
        if loaded is None:
            loaded = _load_vae(root, config)
        path = _resolve(root, str(acquired["normalized_path"]))
        repeated = extract_learned_formal(
            path,
            loaded,
            policy=SOURCE_REPLICATION_POLICY,
            base_seed=int(section["base_seed"]),
            device=str(section["device"]),
        )
        repeated_hash = learned_formal_vector_sha256(repeated.vector)
        payload = {
            **common_payload,
            "repeated_vector_sha256": repeated_hash,
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
        str(BROWSER_RECOVERY_AUTHORIZATION_PATH),
        str(BROWSER_RECOVERY_LEDGER_PATH),
        str(BROWSER_DIRECTORY_INTENT_LEDGER_PATH),
        str(BROWSER_RECOVERY_AMENDMENT_PATH),
        str(BROWSER_RECOVERY_SCRIPT_PATH),
        str(PREPROCESSING_INCIDENT_PATH),
        str(PREPROCESSING_AMENDMENT_PATH),
        str(NORMALIZATION_REVALIDATION_LEDGER_PATH),
        str(PREPROCESSING_AMENDMENT_DOC_PATH),
        str(pilot3_met_r2.DEFAULT_INCIDENT),
        str(pilot3_met_r2.DEFAULT_AUTHORIZATION),
        str(pilot3_met_r2.DEFAULT_METADATA_ATTEMPTS),
        str(pilot3_met_r2.DEFAULT_TARGET_MANIFEST),
        str(pilot3_met_r2.DEFAULT_METADATA_FREEZE),
        str(pilot3_met_r2.DEFAULT_IMAGE_ATTEMPTS),
        str(pilot3_met_r2.DEFAULT_IMAGE_ACQUISITIONS),
        str(pilot3_normalization_scope.DEFAULT_AUTHORIZATION),
        "docs/PILOT_3_R2_OFFICIAL_MET.md",
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
        "src/latent_art_bench/pilot3/met_r2.py",
        "src/latent_art_bench/pilot3/normalization_scope.py",
        "src/latent_art_bench/pilot3/phasea.py",
        "src/latent_art_bench/pilot3/preprocessing.py",
        "src/latent_art_bench/pilot3/execution.py",
        "tests/pilot3/test_lee.py",
        "tests/pilot3/test_met_r2.py",
        "tests/pilot3/test_normalization_scope.py",
        "tests/pilot3/test_phasea.py",
        "tests/pilot3/test_execution.py",
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
    effective_rows: Dict[str, Dict[str, Any]] = {}
    for phase in sorted(phases):
        phase_originals = {
            work_id: row
            for work_id, row in acquisition_rows.items()
            if (
                (phase == "external" and row.get("partition") == EXTERNAL_PARTITION)
                or (
                    phase == "development"
                    and row.get("partition") in DEVELOPMENT_PARTITIONS
                )
            )
        }
        effective_rows.update(
            effective_acquisition_rows(
                root,
                config,
                phase,
                phase_originals,
                require_committed=True,
            )
        )
    result = []
    for split in split_rows:
        work_id = str(split["canonical_work_id"])
        feature = feature_rows[work_id]
        if split["partition"] in DEVELOPMENT_PARTITIONS:
            _verify_existing_acquisition(
                acquisition_rows[work_id],
                root,
                split,
                config,
                None,
            )
        _verify_feature(feature, effective_rows[work_id], split, config)
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
    effective_acquisitions = effective_acquisition_rows(
        root, config, "development", acquisitions, require_committed=True
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
        acquisition = effective_acquisitions.get(work_id)
        if acquisition is None:
            raise Pilot3PhaseAError(f"determinism probe acquisition is missing: {work_id}")
        metadata = feature.get("extraction_metadata")
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("seed"), int):
            raise Pilot3PhaseAError(f"determinism probe seed is missing: {work_id}")
        payload = {
            "record_type": "pilot3_a_vector_determinism_probe",
            "schema_version": (
                "3.0"
                if _is_sha256(acquisition.get("normalization_authorization_sha256"))
                else "2.0"
            ),
            "canonical_work_id": work_id,
            "artist_id": feature["artist_id"],
            "source_id": feature["source_id"],
            "normalized_sha256": acquisition["normalized_sha256"],
            "normalization_protocol_version": acquisition[
                "normalization_protocol_version"
            ],
            "base_common_preprocessing_config_sha256": acquisition[
                "base_common_preprocessing_config_sha256"
            ],
            "common_preprocessing_config_sha256": acquisition[
                "common_preprocessing_config_sha256"
            ],
            "preprocessing_determinism_amendment_sha256": acquisition[
                "preprocessing_determinism_amendment_sha256"
            ],
            "effective_preprocessing_contract_sha256": acquisition[
                "effective_preprocessing_contract_sha256"
            ],
            "effective_acquisition_sha256": acquisition[
                "effective_acquisition_sha256"
            ],
            "normalization_revalidation_record_sha256": acquisition[
                "normalization_revalidation_record_sha256"
            ],
            **{
                field: acquisition[field]
                for field in (
                    *GENERIC_NORMALIZATION_LINEAGE_FIELDS,
                    *MET_R2_LINEAGE_FIELDS,
                )
                if field in acquisition
            },
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
    resolution = require_preprocessing_incident_resolution(root)
    amendment = resolution["amendment"]
    incident = verify_preprocessing_determinism_incident(root)
    revalidation_path = _resolve(root, NORMALIZATION_REVALIDATION_LEDGER_PATH)
    revalidation_rows = _read_canonical_normalization_revalidations(revalidation_path)
    r2_authorization, r2_targets, r2_freeze, r2_acquisitions, scope = (
        _require_met_r2_normalization_inputs(root, config)
    )
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
        "effective_preprocessing": {
            "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
            "contract": _effective_preprocessing_contract(config),
            "effective_preprocessing_contract_sha256": (
                _effective_preprocessing_contract_sha256(config)
            ),
            "incident_path": str(PREPROCESSING_INCIDENT_PATH),
            "incident_file_sha256": hash_file(
                _resolve(root, PREPROCESSING_INCIDENT_PATH)
            ),
            "incident_sha256": incident["incident_sha256"],
            "amendment_path": str(PREPROCESSING_AMENDMENT_PATH),
            "amendment_file_sha256": hash_file(
                _resolve(root, PREPROCESSING_AMENDMENT_PATH)
            ),
            "amendment_authorization_sha256": amendment["authorization_sha256"],
            "normalization_revalidation_ledger_path": str(
                NORMALIZATION_REVALIDATION_LEDGER_PATH
            ),
            "normalization_revalidation_ledger_file_sha256": hash_file(
                revalidation_path
            ),
            "normalization_revalidation_ledger_semantic_sha256": stable_hash(
                revalidation_rows
            ),
            "normalization_revalidation_count": len(revalidation_rows),
            "normalization_scope_path": str(
                pilot3_normalization_scope.DEFAULT_AUTHORIZATION
            ),
            "normalization_scope_file_sha256": hash_file(
                _resolve(root, pilot3_normalization_scope.DEFAULT_AUTHORIZATION)
            ),
            "normalization_scope_schema": pilot3_normalization_scope.SCHEMA_VERSION,
            "normalization_scope_authorization_sha256": scope["authorization_sha256"],
            "effective_acquisition_lineage_semantic_sha256": stable_hash(
                [
                    {
                        "canonical_work_id": row["canonical_work_id"],
                        "normalized_sha256": row["normalized_sha256"],
                        "effective_acquisition_sha256": row[
                            "effective_acquisition_sha256"
                        ],
                        "normalization_revalidation_record_sha256": row[
                            "normalization_revalidation_record_sha256"
                        ],
                        "normalization_authorization_schema": row[
                            "normalization_authorization_schema"
                        ],
                        "normalization_authorization_sha256": row[
                            "normalization_authorization_sha256"
                        ],
                        "r2_image_acquisition_record_sha256": row.get(
                            "r2_image_acquisition_record_sha256"
                        ),
                    }
                    for row in rows
                ]
            ),
        },
        "official_met_r2": {
            "namespace": pilot3_met_r2.NAMESPACE,
            "asset_provider": MET_R2_ASSET_PROVIDER,
            "authorization_sha256": r2_authorization["authorization_sha256"],
            "metadata_freeze_sha256": r2_freeze["freeze_sha256"],
            "target_manifest_semantic_sha256": stable_hash(r2_targets),
            "image_acquisition_manifest_semantic_sha256": stable_hash(r2_acquisitions),
            "target_count": len(r2_targets),
            "image_acquisition_count": len(r2_acquisitions),
            "legacy_commons_admitted": False,
        },
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
                "distance_to_frozen_neighbor_centroid_minus_distance_to_frozen_target_centroid"
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
    require_preprocessing_incident_resolution(root)
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
    require_preprocessing_incident_resolution(root)
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
