"""Fail-closed orchestration for the offline Pilot 3 planning phase.

This module may read JSON/JSONL metadata and aggregate Pilot 2 evidence.  It has
no image decoder, HTTP client, browser adapter, or generation transport.  Its
only writes are deterministic planning evidence under ``reports/pilot_3``.
"""

from __future__ import annotations

import math
import statistics
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from latent_art_bench.io import (
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)
from latent_art_bench.pilot3.corpus import (
    DEFAULT_CORPUS_EVIDENCE,
    DEFAULT_CORPUS_MANIFEST,
    DEFAULT_HOLDOUT_SEAL,
    DEFAULT_REAL_SPLITS,
    build_corpus_bundle,
)
from latent_art_bench.pilot3.design import build_pilot3_design_sensitivity
from latent_art_bench.pilot3.feasibility import (
    CandidateArtist,
    MetadataRows,
    Pilot3FeasibilityConfig,
    audit_feasibility,
    load_metadata_rows,
    verify_feasibility_result,
)

PLANNING_CONFIG_SCHEMA = "pilot3-planning/1.0"
PLANNING_INDEX_SCHEMA = "pilot3-planning-index/1.0"
PILOT2_BASELINE_SCHEMA = "pilot3-pilot2-baseline-recovery/1.0"

DEFAULT_CONFIG = Path("configs/pilot_3/planning.json")
DEFAULT_DESIGN_EVIDENCE = Path("reports/pilot_3/evidence/design_sensitivity.json")
DEFAULT_FEASIBILITY_EVIDENCE = Path("reports/pilot_3/evidence/artist_source_feasibility.json")
DEFAULT_BASELINE_EVIDENCE = Path("reports/pilot_3/evidence/pilot2_baseline_recovery.json")
DEFAULT_PLANNING_INDEX = Path("reports/pilot_3/planning_index.json")
DEFAULT_PROTOCOL = Path("docs/PILOT_3_PROTOCOL.md")

_ALLOWED_MODEL_FAMILIES = ("gpt-image-1", "gpt-image-2")
_IMPLEMENTATION_PATHS = (
    Path("src/latent_art_bench/cli.py"),
    Path("src/latent_art_bench/io.py"),
    Path("src/latent_art_bench/pilot3/design.py"),
    Path("src/latent_art_bench/pilot3/corpus.py"),
    Path("src/latent_art_bench/pilot3/feasibility.py"),
    Path("src/latent_art_bench/pilot3/planning.py"),
    Path("src/latent_art_bench/pilot3/cli.py"),
)
_VERIFICATION_PATHS = (
    Path("tests/pilot3/test_design.py"),
    Path("tests/pilot3/test_pilot3_corpus.py"),
    Path("tests/pilot3/test_feasibility.py"),
    Path("tests/pilot3/test_planning.py"),
)
_ENVIRONMENT_PATHS = (Path("pyproject.toml"), Path("uv.lock"))


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _relative_path(value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-blank repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must remain inside the repository")
    return path


def _resolve(root: Path, value: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    resolved = (resolved_root / value).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return resolved


def _require_mapping(value: object, *, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return dict(value)


def _require_int_sequence(value: object, *, label: str) -> Tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in value):
        raise ValueError(f"{label} must contain positive integers")
    normalized = tuple(value)
    if tuple(sorted(set(normalized))) != normalized:
        raise ValueError(f"{label} must be sorted and unique")
    return normalized


def _require_positive_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _require_nonnegative_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _require_probability(value: object, *, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a numeric probability")
    normalized = float(value)
    if not math.isfinite(normalized) or not 0.0 < normalized <= 1.0:
        raise ValueError(f"{label} must lie in (0, 1]")
    return normalized


def _candidate_artists(config: Mapping[str, Any]) -> Tuple[CandidateArtist, ...]:
    raw = config.get("candidate_artists")
    if not isinstance(raw, list) or not raw:
        raise ValueError("candidate_artists must be a non-empty list")
    artists = []
    seen = set()
    for rank, item in enumerate(raw, start=1):
        row = _require_mapping(item, label=f"candidate_artists[{rank}]")
        artist_id = row.get("artist_id")
        artist_name = row.get("artist_name")
        if not isinstance(artist_id, str) or not isinstance(artist_name, str):
            raise ValueError("every candidate artist requires string id and name")
        if artist_id in seen:
            raise ValueError(f"duplicate candidate artist id: {artist_id}")
        seen.add(artist_id)
        artists.append(CandidateArtist(artist_id, artist_name))
    if [artist.artist_id for artist in artists] != sorted(seen):
        raise ValueError("candidate artists must be sorted by artist_id")
    return tuple(artists)


def _validate_hard_stop(config: Mapping[str, Any]) -> None:
    expected = {
        "schema_version": PLANNING_CONFIG_SCHEMA,
        "status": "development_draft",
        "generation_gate": "closed",
        "planning_scope": "offline_metadata_and_simulation_only",
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"Pilot 3 planning requires {key}={value!r}")

    boundary = _require_mapping(
        config.get("future_generation_boundary"), label="future_generation_boundary"
    )
    if boundary.get("generation_permitted_in_this_phase") is not False:
        raise ValueError("Pilot 3 planning must prohibit generation")
    if tuple(boundary.get("allowed_model_families") or ()) != _ALLOWED_MODEL_FAMILIES:
        raise ValueError("the only allowed future model families are gpt-image-1 and gpt-image-2")
    if boundary.get("transport") != "~/dev/openai-oauth":
        raise ValueError("future GPT Image work is constrained to ~/dev/openai-oauth")
    if boundary.get("future_single_label_candidate") != "gpt-image-2":
        raise ValueError("the development plan must retain one unresolved gpt-image-2 stratum")
    if boundary.get("snapshot_status") != "documented_but_not_verified_or_frozen_for_openai_oauth":
        raise ValueError("the dated GPT Image 2 snapshot must remain unverified and unfrozen")


def load_planning_config(root: Path, config_path: Path = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Load and validate the immutable hard stop and planning-only config shape."""

    resolved_root = root.expanduser().resolve()
    relative_config = _relative_path(config_path.as_posix(), label="planning config")
    path = _resolve(resolved_root, relative_config)
    if not path.is_file():
        raise FileNotFoundError(path)
    config = _require_mapping(read_json(path), label="planning config")
    _validate_hard_stop(config)
    _candidate_artists(config)
    return config


def _verified_development_inputs(
    root: Path, config: Mapping[str, Any]
) -> Dict[str, Dict[str, str]]:
    bindings = _require_mapping(config.get("development_inputs"), label="development_inputs")
    verified: Dict[str, Dict[str, str]] = {}
    for name, raw in sorted(bindings.items()):
        row = _require_mapping(raw, label=f"development_inputs.{name}")
        relative = _relative_path(row.get("path"), label=f"development_inputs.{name}.path")
        expected = row.get("file_sha256")
        if not _is_sha256(expected):
            raise ValueError(f"development_inputs.{name}.file_sha256 is invalid")
        path = _resolve(root, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        observed = hash_file(path)
        if observed != expected:
            raise RuntimeError(
                f"development input hash mismatch for {relative}: expected {expected}, "
                f"found {observed}"
            )
        use = row.get("use")
        if not isinstance(use, str) or not use.strip():
            raise ValueError(f"development_inputs.{name}.use must be explicit")
        verified[name] = {
            "path": relative.as_posix(),
            "file_sha256": observed,
            "use": use,
        }
    return verified


def _feasibility_config(
    section: Mapping[str, Any],
    artists: Sequence[CandidateArtist],
    *,
    eligible_decisions: Sequence[str],
    require_confirmed_public_domain: bool,
) -> Pilot3FeasibilityConfig:
    source_ids = section.get("source_ids")
    if not isinstance(source_ids, list) or any(
        not isinstance(source_id, str) or not source_id for source_id in source_ids
    ):
        raise ValueError("feasibility source_ids must be a list of non-blank strings")
    return Pilot3FeasibilityConfig(
        candidate_artists=tuple(artists),
        min_unique_works_per_artist_source=_require_positive_int(
            section.get("min_unique_works_per_artist_source"),
            label="min_unique_works_per_artist_source",
        ),
        min_artist_count=_require_positive_int(
            section.get("min_artist_count"), label="min_artist_count"
        ),
        min_source_count=_require_positive_int(
            section.get("min_source_count"), label="min_source_count"
        ),
        source_ids=tuple(source_ids),
        eligible_decisions=tuple(eligible_decisions),
        require_confirmed_public_domain=require_confirmed_public_domain,
    )


def _portable_metadata_rows(root: Path, metadata_paths: Sequence[Path]) -> MetadataRows:
    absolute_paths = [_resolve(root, path) for path in metadata_paths]
    loaded = load_metadata_rows(absolute_paths)
    evidence = []
    for row in loaded.input_evidence:
        portable = dict(row)
        manifest_path = Path(str(portable["manifest_path"])).resolve()
        portable["manifest_path"] = manifest_path.relative_to(root.resolve()).as_posix()
        evidence.append(portable)
    return MetadataRows(rows=loaded.rows, input_evidence=tuple(evidence))


def _verify_design_result(result: Mapping[str, Any]) -> None:
    payload = dict(result)
    recorded = payload.pop("result_sha256", None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise ValueError("Pilot 3 design result has a stale result_sha256")
    if result.get("network_or_image_requests_made") is not False:
        raise ValueError("Pilot 3 planning evidence must attest zero network/image requests")


def _seal_semantic(payload: Mapping[str, Any], field: str) -> Dict[str, Any]:
    result = dict(payload)
    result[field] = stable_hash(result)
    return result


def _verify_pilot2_baseline(result: Mapping[str, Any]) -> bool:
    payload = dict(result)
    if payload.get("schema_version") != PILOT2_BASELINE_SCHEMA:
        raise ValueError("unexpected Pilot 2 baseline-recovery schema")
    recorded = payload.pop("semantic_sha256", None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise ValueError("Pilot 2 baseline recovery has a stale semantic_sha256")
    nested = payload.get("corpus_balance_recovery")
    if not isinstance(nested, Mapping):
        raise ValueError("Pilot 2 baseline recovery lacks its nested corpus audit")
    verify_feasibility_result(nested)
    return True


def _primary_rows_by_identity(analysis: Mapping[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    raw_rows = analysis.get("primary_estimates")
    if not isinstance(raw_rows, list):
        raise ValueError("Pilot 2 analysis lacks primary_estimates")
    indexed: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for raw in raw_rows:
        row = _require_mapping(raw, label="Pilot 2 primary estimate")
        key = (str(row.get("requested_model_label")), str(row.get("estimand")))
        if key in indexed:
            raise ValueError(f"duplicate Pilot 2 primary estimate: {key}")
        indexed[key] = row
    return indexed


def _build_pilot2_baseline_recovery(
    *,
    root: Path,
    verified_inputs: Mapping[str, Mapping[str, str]],
    design_result: Mapping[str, Any],
    corpus_baseline: Mapping[str, Any],
) -> Dict[str, Any]:
    """Re-derive every Pilot 2 quantity used by the planning simulator."""

    if corpus_baseline.get("configured_snapshot_threshold_result") != (
        "meets_configured_snapshot_thresholds"
    ):
        raise RuntimeError("Pilot 2 metadata threshold regression was not recovered")

    analysis_binding = verified_inputs.get("pilot2_analysis")
    completion_binding = verified_inputs.get("pilot2_generation_completion")
    qualification_binding = verified_inputs.get("pilot2_learned_formal_qualification")
    if analysis_binding is None or completion_binding is None or qualification_binding is None:
        raise ValueError(
            "planning requires pinned Pilot 2 analysis, completion, and qualification inputs"
        )
    analysis = _require_mapping(
        read_json(_resolve(root, Path(analysis_binding["path"]))),
        label="Pilot 2 analysis",
    )
    completion = _require_mapping(
        read_json(_resolve(root, Path(completion_binding["path"]))),
        label="Pilot 2 generation completion",
    )
    qualification = _require_mapping(
        read_json(_resolve(root, Path(qualification_binding["path"]))),
        label="Pilot 2 learned-formal qualification",
    )
    qualification_payload = dict(qualification)
    qualification_result_sha256 = qualification_payload.pop("result_sha256", None)
    if (
        not _is_sha256(qualification_result_sha256)
        or stable_hash(qualification_payload) != qualification_result_sha256
    ):
        raise ValueError("Pilot 2 qualification has a stale result_sha256")
    development = _require_mapping(
        design_result.get("pilot2_development_inputs"),
        label="design_result.pilot2_development_inputs",
    )

    grid = _require_mapping(analysis.get("grid"), label="Pilot 2 analysis grid")
    itt = _require_mapping(analysis.get("itt"), label="Pilot 2 ITT")
    by_label_itt = _require_mapping(itt.get("by_requested_label"), label="Pilot 2 label ITT")
    completion_by_label = _require_mapping(
        completion.get("by_requested_model_label"), label="Pilot 2 completion label counts"
    )
    design_counts = {
        "artists": len(grid.get("artist_ids") or []),
        "content_blocks": len(grid.get("content_ids") or []),
        "repetitions": int(grid.get("repetitions")),
        "requested_label_strata": len(grid.get("requested_labels") or []),
        "total_requests": int(completion.get("cell_count")),
        "named_requests": int(itt.get("expected_named_control_pairs")),
        "shared_control_requests": int(completion.get("cell_count"))
        - int(itt.get("expected_named_control_pairs")),
    }
    if development.get("design") != design_counts:
        raise RuntimeError("Pilot 3 simulator embeds stale Pilot 2 design counts")
    if development.get("source_result_sha256") != analysis.get("result_sha256"):
        raise RuntimeError("Pilot 3 simulator embeds a stale Pilot 2 semantic identity")

    disposition_counts = _require_mapping(
        completion.get("disposition_counts"), label="Pilot 2 dispositions"
    )
    refusal_total = int(disposition_counts.get("refused", 0))
    technical_failure_total = sum(
        int(value)
        for key, value in disposition_counts.items()
        if key not in {"refused", "succeeded"}
    )
    refusal_by_label = {
        label: {
            "count": int(_require_mapping(row, label=label).get("refused", 0)),
            "denominator": sum(int(value) for value in row.values()),
        }
        for label, row in sorted(completion_by_label.items())
    }
    secondary_rows = analysis.get("secondary_artist_estimates")
    if not isinstance(secondary_rows, list):
        raise ValueError("Pilot 2 analysis lacks secondary artist estimates")
    deficits_by_artist_label: Dict[Tuple[str, str], int] = {}
    artist_estimates: Dict[Tuple[str, str], list[float]] = {}
    for raw in secondary_rows:
        row = _require_mapping(raw, label="Pilot 2 secondary artist estimate")
        artist_id = str(row.get("artist_id"))
        requested_label = str(row.get("requested_model_label"))
        estimand = str(row.get("estimand"))
        estimate = float(row.get("estimate"))
        if not math.isfinite(estimate):
            raise ValueError("Pilot 2 secondary artist estimate must be finite")
        artist_estimates.setdefault((requested_label, estimand), []).append(estimate)
        expected_pairs = _require_positive_int(
            row.get("expected_pairs"), label="Pilot 2 expected artist pairs"
        )
        complete_pairs = _require_nonnegative_int(
            row.get("complete_pairs"), label="Pilot 2 complete artist pairs"
        )
        if complete_pairs > expected_pairs:
            raise ValueError("Pilot 2 complete artist pairs exceed assigned pairs")
        key = (artist_id, requested_label)
        deficit = expected_pairs - complete_pairs
        if key in deficits_by_artist_label and deficits_by_artist_label[key] != deficit:
            raise ValueError("Pilot 2 estimands disagree on an artist/label pair deficit")
        deficits_by_artist_label[key] = deficit
    refusal_by_artist: Dict[str, int] = {}
    for (artist_id, _), deficit in deficits_by_artist_label.items():
        refusal_by_artist[artist_id] = refusal_by_artist.get(artist_id, 0) + deficit
    incomplete_artist_ids = sorted(
        artist_id for artist_id, deficit in refusal_by_artist.items() if deficit > 0
    )
    if sum(refusal_by_artist.values()) != int(itt.get("refused_pairs")):
        raise RuntimeError("Pilot 2 secondary estimates do not recover all refused pairs")
    if refusal_total != int(itt.get("refused_pairs")):
        raise RuntimeError("Pilot 2 completion and analysis disagree on refusal count")
    concentrated_refusal_count = (
        refusal_by_artist[incomplete_artist_ids[0]] if len(incomplete_artist_ids) == 1 else 0
    )
    refusal_observations = {
        "total": refusal_total,
        "overall_rate": refusal_total / design_counts["total_requests"],
        "by_requested_label": refusal_by_label,
        "named_total": int(itt.get("refused_pairs")),
        "named_rate": int(itt.get("refused_pairs")) / design_counts["named_requests"],
        "shared_control_total": refusal_total - int(itt.get("refused_pairs")),
        "all_refusals_artist_id": (
            incomplete_artist_ids[0] if len(incomplete_artist_ids) == 1 else None
        ),
        "one_artist_named_count": concentrated_refusal_count,
        "one_artist_named_denominator": (
            design_counts["content_blocks"]
            * design_counts["repetitions"]
            * design_counts["requested_label_strata"]
        ),
        "remaining_artist_named_count": int(itt.get("refused_pairs")) - concentrated_refusal_count,
        "remaining_artist_named_denominator": design_counts["named_requests"]
        - (
            design_counts["content_blocks"]
            * design_counts["repetitions"]
            * design_counts["requested_label_strata"]
        ),
        "technical_failure_total": technical_failure_total,
    }
    if development.get("refusal_observations") != refusal_observations:
        raise RuntimeError("Pilot 3 simulator embeds stale Pilot 2 refusal observations")

    artist_estimate_ranges: Dict[str, Dict[str, list[float]]] = {}
    for (label, estimand), values in sorted(artist_estimates.items()):
        artist_estimate_ranges.setdefault(label, {})[estimand] = [
            min(values),
            max(values),
        ]
    embedded_ranges = _require_mapping(
        development.get("descriptive_complete_pair_artist_estimate_range"),
        label="embedded Pilot 2 artist estimate ranges",
    )
    for label, estimates in artist_estimate_ranges.items():
        embedded = _require_mapping(
            embedded_ranges.get(label), label=f"embedded artist ranges for {label}"
        )
        for estimand, observed in estimates.items():
            candidate = embedded.get(estimand)
            if not isinstance(candidate, list) or len(candidate) != 2:
                raise RuntimeError("Pilot 3 simulator lacks a Pilot 2 artist range")
            if any(
                not math.isclose(float(expected), actual, rel_tol=0.0, abs_tol=1e-12)
                for expected, actual in zip(candidate, observed)
            ):
                raise RuntimeError("Pilot 3 simulator embeds a stale Pilot 2 artist range")

    primary_by_identity = _primary_rows_by_identity(analysis)
    block_sds: Dict[str, Dict[str, float]] = {}
    primary_descriptive = []
    for (label, estimand), row in sorted(primary_by_identity.items()):
        block_values = _require_mapping(
            row.get("content_block_estimates"), label=f"{label}/{estimand} block estimates"
        )
        values = [float(value) for _, value in sorted(block_values.items())]
        if len(values) < 2 or any(not math.isfinite(value) for value in values):
            raise ValueError("Pilot 2 block estimates must be finite with at least two blocks")
        block_sds.setdefault(label, {})[estimand] = statistics.stdev(values)
        primary_descriptive.append(
            {
                "requested_model_label": label,
                "estimand": estimand,
                "estimate": float(row["estimate"]),
                "complete_pair_population": row.get("analysis_population"),
                "test_status": row.get("test_status"),
                "hypothesis_supported": row.get("hypothesis_supported"),
            }
        )
    embedded_sds = _require_mapping(
        development.get("descriptive_complete_pair_content_block_sample_sd"),
        label="embedded Pilot 2 block SDs",
    )
    for label, estimates in block_sds.items():
        embedded = _require_mapping(embedded_sds.get(label), label=f"embedded SDs for {label}")
        for estimand, observed in estimates.items():
            if not math.isclose(
                float(embedded.get(estimand)), observed, rel_tol=0.0, abs_tol=1e-12
            ):
                raise RuntimeError("Pilot 3 simulator embeds a stale Pilot 2 block SD")

    scientific_completion = _require_mapping(
        analysis.get("scientific_completion"), label="Pilot 2 scientific completion"
    )
    payload = {
        "record_type": "pilot3_pilot2_baseline_recovery",
        "schema_version": PILOT2_BASELINE_SCHEMA,
        "status": "pass",
        "source_bindings": {
            "analysis": dict(analysis_binding),
            "generation_completion": dict(completion_binding),
            "learned_formal_qualification": dict(qualification_binding),
        },
        "recovered_generation": {
            "all_cells_terminal": completion.get("all_cells_terminal"),
            "all_cells_succeeded": completion.get("all_cells_succeeded"),
            "attempt_count": completion.get("attempt_count"),
            "cell_count": completion.get("cell_count"),
            "successful_output_count": completion.get("successful_output_count"),
            "disposition_counts": disposition_counts,
            "by_requested_model_label": completion_by_label,
        },
        "recovered_analysis": {
            "scientific_completion": scientific_completion,
            "all_four_primary_hypotheses_supported": analysis.get(
                "all_four_primary_hypotheses_supported"
            ),
            "itt": {
                "expected_named_control_pairs": itt.get("expected_named_control_pairs"),
                "complete_feature_pairs": itt.get("complete_feature_pairs"),
                "refused_pairs": itt.get("refused_pairs"),
                "by_requested_label": by_label_itt,
            },
            "primary_descriptive_estimates": primary_descriptive,
            "incomplete_artist_ids": incomplete_artist_ids,
            "refused_pair_count_by_artist": dict(sorted(refusal_by_artist.items())),
        },
        "recovered_learned_formal_qualification": {
            "record_type": qualification.get("record_type"),
            "schema_version": qualification.get("schema_version"),
            "status": qualification.get("status"),
            "reasons": qualification.get("reasons"),
            "atlas_work_count": qualification.get("atlas_work_count"),
            "train_work_count": qualification.get("train_work_count"),
            "held_out_work_count": qualification.get("held_out_work_count"),
            "checks": qualification.get("checks"),
            "result_sha256": qualification_result_sha256,
        },
        "verified_simulator_inputs": {
            "design": design_counts,
            "refusal_observations": refusal_observations,
            "descriptive_complete_pair_content_block_sample_sd": block_sds,
            "descriptive_complete_pair_artist_estimate_range": artist_estimate_ranges,
            "source_result_sha256": analysis.get("result_sha256"),
        },
        "corpus_balance_recovery": dict(corpus_baseline),
        "claim_boundary": (
            "Pass means the planning code exactly re-derived its Pilot 2 development "
            "inputs and recovered the prior 4-artist by 2-source, 5-work threshold. It "
            "does not mean Pilot 2 hypotheses passed or that Pilot 3 is feasible."
        ),
    }
    result = _seal_semantic(payload, "semantic_sha256")
    _verify_pilot2_baseline(result)
    return result


def _seal_index(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result["result_sha256"] = stable_hash(result)
    return result


def verify_planning_index(index: Mapping[str, Any]) -> bool:
    payload = dict(index)
    if payload.get("schema_version") != PLANNING_INDEX_SCHEMA:
        raise ValueError("unexpected Pilot 3 planning-index schema")
    recorded = payload.pop("result_sha256", None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise ValueError("Pilot 3 planning index has a stale result_sha256")
    return True


def build_planning_results(root: Path, config_path: Path = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Recompute all planning results without writing or contacting a network."""

    resolved_root = root.expanduser().resolve()
    config = load_planning_config(resolved_root, config_path)
    verified_inputs = _verified_development_inputs(resolved_root, config)
    artists = _candidate_artists(config)

    design = _require_mapping(config.get("design"), label="design")
    design_result = build_pilot3_design_sensitivity(
        artist_counts=_require_int_sequence(design.get("artist_counts"), label="artist_counts"),
        content_block_counts=_require_int_sequence(
            design.get("content_block_counts"), label="content_block_counts"
        ),
        repetition_counts=_require_int_sequence(
            design.get("repetition_counts"), label="repetition_counts"
        ),
        min_request_budget=_require_positive_int(
            design.get("min_request_budget"), label="design.min_request_budget"
        ),
        max_request_budget=_require_positive_int(
            design.get("max_request_budget"), label="design.max_request_budget"
        ),
        draws=_require_positive_int(design.get("draws"), label="design.draws"),
        seed=_require_nonnegative_int(design.get("seed"), label="design.seed"),
        familywise_alpha=_require_probability(
            design.get("familywise_alpha"), label="design.familywise_alpha"
        ),
        minimum_pair_availability=_require_probability(
            design.get("minimum_pair_availability"),
            label="design.minimum_pair_availability",
        ),
    )
    _verify_design_result(design_result)

    feasibility = _require_mapping(config.get("feasibility"), label="feasibility")
    eligible_decisions = feasibility.get("eligible_decisions")
    if not isinstance(eligible_decisions, list) or not all(
        isinstance(value, str) for value in eligible_decisions
    ):
        raise ValueError("feasibility.eligible_decisions must be a list of strings")
    require_public_domain = feasibility.get("require_confirmed_public_domain")
    if not isinstance(require_public_domain, bool):
        raise ValueError("require_confirmed_public_domain must be boolean")
    if feasibility.get("source_ids") != ["aic", "met", "museum_balanced"]:
        raise ValueError("current feasibility sources must be AIC, Met, and museum-balanced")
    if (
        feasibility.get("min_unique_works_per_artist_source") != 3
        or feasibility.get("min_artist_count") != 4
        or feasibility.get("min_source_count") != 3
    ):
        raise ValueError("current feasibility floor must cover every frozen source cell")
    corpus_freeze = _require_mapping(config.get("corpus_freeze"), label="corpus_freeze")
    corpus_config_path = _relative_path(
        corpus_freeze.get("config_path"), label="corpus_freeze.config_path"
    )
    expected_corpus_config_hash = corpus_freeze.get("config_file_sha256")
    if not _is_sha256(expected_corpus_config_hash):
        raise ValueError("corpus_freeze.config_file_sha256 is invalid")
    observed_corpus_config_hash = hash_file(_resolve(resolved_root, corpus_config_path))
    if observed_corpus_config_hash != expected_corpus_config_hash:
        raise RuntimeError("corpus freeze config hash mismatch")
    corpus_bundle = build_corpus_bundle(resolved_root, corpus_config_path)
    feasibility_result = corpus_bundle["feasibility"]
    verify_feasibility_result(feasibility_result)

    baseline = _require_mapping(
        config.get("pilot2_baseline_recovery"), label="pilot2_baseline_recovery"
    )
    baseline_ids = baseline.get("candidate_artist_ids")
    if not isinstance(baseline_ids, list) or not all(
        isinstance(value, str) for value in baseline_ids
    ):
        raise ValueError("pilot2_baseline_recovery candidate ids must be strings")
    artist_by_id = {artist.artist_id: artist for artist in artists}
    if set(baseline_ids) - set(artist_by_id):
        raise ValueError("baseline recovery references an unknown candidate artist")
    candidate_metadata_binding = verified_inputs.get("candidate_metadata")
    if candidate_metadata_binding is None:
        raise ValueError("baseline recovery requires the pinned Pilot 0 metadata")
    loaded = _portable_metadata_rows(resolved_root, (Path(candidate_metadata_binding["path"]),))
    baseline_artists = tuple(artist_by_id[artist_id] for artist_id in sorted(baseline_ids))
    baseline_config = _feasibility_config(
        baseline,
        baseline_artists,
        eligible_decisions=eligible_decisions,
        require_confirmed_public_domain=require_public_domain,
    )
    baseline_result = audit_feasibility(loaded, baseline_config)
    verify_feasibility_result(baseline_result)
    baseline_recovery = _build_pilot2_baseline_recovery(
        root=resolved_root,
        verified_inputs=verified_inputs,
        design_result=design_result,
        corpus_baseline=baseline_result,
    )

    return {
        "config": config,
        "config_path": config_path.as_posix(),
        "config_file_sha256": hash_file(_resolve(resolved_root, config_path)),
        "verified_development_inputs": verified_inputs,
        "design": design_result,
        "feasibility": feasibility_result,
        "baseline": baseline_recovery,
        "corpus_rows": corpus_bundle["corpus_rows"],
        "split_rows": corpus_bundle["split_rows"],
        "corpus_summary": corpus_bundle["summary"],
        "holdout_seal": corpus_bundle["holdout"],
    }


def _planning_index(
    root: Path,
    results: Mapping[str, Any],
    evidence_paths: Mapping[str, Path],
) -> Dict[str, Any]:
    protocol_path = _resolve(root, DEFAULT_PROTOCOL)
    if not protocol_path.is_file():
        raise FileNotFoundError(protocol_path)
    implementation = {}
    for relative in _IMPLEMENTATION_PATHS:
        path = _resolve(root, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        implementation[relative.as_posix()] = hash_file(path)
    verification = {}
    for relative in _VERIFICATION_PATHS:
        path = _resolve(root, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        verification[relative.as_posix()] = hash_file(path)
    environment = {}
    for relative in _ENVIRONMENT_PATHS:
        path = _resolve(root, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        environment[relative.as_posix()] = hash_file(path)

    evidence = {}
    semantic_fields = {
        "design_sensitivity": "result_sha256",
        "artist_source_feasibility": "semantic_sha256",
        "pilot2_baseline_recovery": "semantic_sha256",
        "corpus_selection": "semantic_sha256",
        "holdout_seal": "semantic_sha256",
    }
    objects = {
        "design_sensitivity": results["design"],
        "artist_source_feasibility": results["feasibility"],
        "pilot2_baseline_recovery": results["baseline"],
        "corpus_selection": results["corpus_summary"],
        "holdout_seal": results["holdout_seal"],
    }
    for name, path in evidence_paths.items():
        resolved = _resolve(root, path)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        semantic_field = semantic_fields[name]
        evidence[name] = {
            "path": path.as_posix(),
            "file_sha256": hash_file(resolved),
            "semantic_sha256": objects[name][semantic_field],
            "status": objects[name]["status"],
        }
        if name == "artist_source_feasibility":
            evidence[name]["configured_snapshot_threshold_result"] = objects[name][
                "configured_snapshot_threshold_result"
            ]

    feasibility = results["feasibility"]
    baseline = results["baseline"]
    snapshot_threshold_result = feasibility["configured_snapshot_threshold_result"]
    freeze_a1_ready = feasibility["freeze_readiness"]["freeze_a1_ready"] is True
    snapshot_decision = (
        "SNAPSHOT_THRESHOLD_MET_FREEZE_A1_READY"
        if snapshot_threshold_result == "meets_configured_snapshot_thresholds" and freeze_a1_ready
        else "SNAPSHOT_THRESHOLD_NOT_MET_OR_NOT_FREEZE_READY"
    )
    payload = {
        "record_type": "pilot3_planning_index",
        "schema_version": PLANNING_INDEX_SCHEMA,
        "status": "offline_planning_and_freeze_a1_complete_generation_gate_closed",
        "generation_gate": "closed",
        "config": {
            "path": results["config_path"],
            "file_sha256": results["config_file_sha256"],
        },
        "protocol": {
            "path": DEFAULT_PROTOCOL.as_posix(),
            "file_sha256": hash_file(protocol_path),
            "status": "development_draft_not_preregistered",
        },
        "development_inputs": results["verified_development_inputs"],
        "implementation_file_sha256": implementation,
        "verification_file_sha256": verification,
        "environment_lock_file_sha256": environment,
        "evidence": evidence,
        "decision": {
            "planning_bundle_emitted": True,
            "offline_evidence_bundle_verifiable": baseline["status"] == "pass",
            "planning_prerequisites_resolved": freeze_a1_ready,
            "p3_t01_freeze_ready": freeze_a1_ready,
            "p3_t02_baseline_recovery_passed": baseline["status"] == "pass",
            "p3_t03_closed_gate_index_emitted": True,
            "p3_t04_final_design_selected": False,
            "p3_t05_corpus_selection_emitted": True,
            "p3_t06_real_split_and_holdout_seal_emitted": True,
            "pilot2_baseline_recovered": baseline["status"] == "pass",
            "successor_metadata_audit_status": feasibility["status"],
            "successor_snapshot_threshold_result": snapshot_threshold_result,
            "metadata_audit_decision": "METADATA_AUDIT_COMPLETE_FREEZE_A1_READY",
            "successor_metadata_decision": snapshot_decision,
            "design_decision": results["design"].get("design_decision"),
            "final_artist_roster_selected": True,
            "final_sample_size_selected": True,
            "phase_a_artwork_acquisition_authorized": True,
            "phase_b_generation_authorized": False,
            "next_action": (
                "begin Phase-A acquisition: rehash exact prior local reproductions when "
                "available, acquire remaining selected works, and apply the frozen "
                "decode/visual/feature qualification gates; do not begin generation"
            ),
        },
        "offline_integrity": {
            "network_requests_made": False,
            "image_requests_made": False,
            "artwork_bytes_opened": False,
            "feature_or_generated_outcomes_used_by_current_computation": False,
            "upstream_selection_provenance_verified": True,
            "permitted_io": "planning config, text metadata, aggregate Pilot 2 evidence",
        },
        "claim_boundary": (
            "This index freezes 40 AIC/Met development works and a 12-work external "
            "holdout made of three complete official-museum blocks. It does not claim "
            "artwork bytes were "
            "opened, decoded, visually reviewed, or feature-qualified, and generation "
            "remains closed."
        ),
    }
    return _seal_index(payload)


def write_planning_bundle(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
    *,
    design_path: Path = DEFAULT_DESIGN_EVIDENCE,
    feasibility_path: Path = DEFAULT_FEASIBILITY_EVIDENCE,
    baseline_path: Path = DEFAULT_BASELINE_EVIDENCE,
    index_path: Path = DEFAULT_PLANNING_INDEX,
) -> Dict[str, Any]:
    """Recompute and atomically write the canonical offline planning bundle."""

    resolved_root = root.expanduser().resolve()
    results = build_planning_results(resolved_root, config_path)
    write_json(_resolve(resolved_root, design_path), results["design"])
    write_json(_resolve(resolved_root, feasibility_path), results["feasibility"])
    write_json(_resolve(resolved_root, baseline_path), results["baseline"])
    write_jsonl(_resolve(resolved_root, DEFAULT_CORPUS_MANIFEST), results["corpus_rows"])
    write_jsonl(_resolve(resolved_root, DEFAULT_REAL_SPLITS), results["split_rows"])
    write_json(_resolve(resolved_root, DEFAULT_CORPUS_EVIDENCE), results["corpus_summary"])
    write_json(_resolve(resolved_root, DEFAULT_HOLDOUT_SEAL), results["holdout_seal"])
    evidence_paths = {
        "design_sensitivity": design_path,
        "artist_source_feasibility": feasibility_path,
        "pilot2_baseline_recovery": baseline_path,
        "corpus_selection": DEFAULT_CORPUS_EVIDENCE,
        "holdout_seal": DEFAULT_HOLDOUT_SEAL,
    }
    index = _planning_index(resolved_root, results, evidence_paths)
    verify_planning_index(index)
    write_json(_resolve(resolved_root, index_path), index)
    return index


def verify_planning_bundle(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
    *,
    design_path: Path = DEFAULT_DESIGN_EVIDENCE,
    feasibility_path: Path = DEFAULT_FEASIBILITY_EVIDENCE,
    baseline_path: Path = DEFAULT_BASELINE_EVIDENCE,
    index_path: Path = DEFAULT_PLANNING_INDEX,
) -> Dict[str, Any]:
    """Recompute every artifact and reject stale bytes, hashes, or hard stops."""

    resolved_root = root.expanduser().resolve()
    results = build_planning_results(resolved_root, config_path)
    expected_objects = {
        design_path: results["design"],
        feasibility_path: results["feasibility"],
        baseline_path: results["baseline"],
        DEFAULT_CORPUS_EVIDENCE: results["corpus_summary"],
        DEFAULT_HOLDOUT_SEAL: results["holdout_seal"],
    }
    for relative, expected in expected_objects.items():
        path = _resolve(resolved_root, relative)
        if not path.is_file():
            raise FileNotFoundError(path)
        if read_json(path) != expected:
            raise RuntimeError(f"stale deterministic Pilot 3 planning artifact: {relative}")

    if read_jsonl(_resolve(resolved_root, DEFAULT_CORPUS_MANIFEST)) != results["corpus_rows"]:
        raise RuntimeError("stale deterministic Pilot 3 corpus-selection manifest")
    if read_jsonl(_resolve(resolved_root, DEFAULT_REAL_SPLITS)) != results["split_rows"]:
        raise RuntimeError("stale deterministic Pilot 3 real-splits manifest")

    evidence_paths = {
        "design_sensitivity": design_path,
        "artist_source_feasibility": feasibility_path,
        "pilot2_baseline_recovery": baseline_path,
        "corpus_selection": DEFAULT_CORPUS_EVIDENCE,
        "holdout_seal": DEFAULT_HOLDOUT_SEAL,
    }
    expected_index = _planning_index(resolved_root, results, evidence_paths)
    index_file = _resolve(resolved_root, index_path)
    if not index_file.is_file():
        raise FileNotFoundError(index_file)
    observed_index = _require_mapping(read_json(index_file), label="planning index")
    verify_planning_index(observed_index)
    if observed_index != expected_index:
        raise RuntimeError("stale deterministic Pilot 3 planning index")
    return observed_index


__all__ = [
    "DEFAULT_BASELINE_EVIDENCE",
    "DEFAULT_CONFIG",
    "DEFAULT_DESIGN_EVIDENCE",
    "DEFAULT_FEASIBILITY_EVIDENCE",
    "DEFAULT_PLANNING_INDEX",
    "PLANNING_CONFIG_SCHEMA",
    "PLANNING_INDEX_SCHEMA",
    "PILOT2_BASELINE_SCHEMA",
    "build_planning_results",
    "load_planning_config",
    "verify_planning_bundle",
    "verify_planning_index",
    "write_planning_bundle",
]
