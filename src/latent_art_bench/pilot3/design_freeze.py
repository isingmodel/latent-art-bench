"""Deterministic, offline Phase-B design freeze for Pilot 3.

This module materializes the prospective estimation design, prompt manifest,
request schedule, human-validation disposition, and analysis contract.  It has
no HTTP client, image decoder, browser adapter, or generation transport.  The
result remains fail-closed until the separately produced Phase-A, transport,
and generation-gate evidence is present and valid.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from latent_art_bench.io import (
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)

STUDY_SCHEMA = "pilot3-phase-b-study/1.0"
PROMPT_SCHEMA = "pilot3-prompt/1.0"
SCHEDULE_SCHEMA = "pilot3-scheduled-request/1.0"
DESIGN_SCHEMA = "pilot3-phase-b-design/1.0"
HUMAN_SCHEMA = "pilot3-human-validation-disposition/1.0"
PROMPT_SCHEDULE_SCHEMA = "pilot3-prompt-schedule-contract/1.0"
ANALYSIS_CONTRACT_SCHEMA = "pilot3-analysis-contract/1.0"

DEFAULT_CONFIG = Path("configs/pilot_3/study.json")

EXPECTED_ARTIST_IDS = (
    "alfred_sisley",
    "camille_pissarro",
    "paul_cezanne",
    "pierre_auguste_renoir",
)
EXPECTED_REQUESTED_LABEL = "gpt-image-2"
EXPECTED_TRANSPORT = "~/dev/openai-oauth"
EXPECTED_GENERATION_AUTHORIZATION_SCHEMA = "pilot3-generation-authorization/1.0"
EXPECTED_ARTIST_COUNT = 4
EXPECTED_CONTENT_BLOCK_COUNT = 16
EXPECTED_REPETITIONS = 4
EXPECTED_REQUEST_BUDGET = 320
EXPECTED_PROMPT_COUNT = 80
EXPECTED_SCHEDULE_COUNT = 320
EXPECTED_PAIR_COUNT = 256
EXPECTED_QUALIFICATION_PROMPT = (
    "Create one original abstract image composed only of a centered blue circle, a small "
    "red square, and two pale gray horizontal bars on a plain white background. Use flat "
    "colors and simple clean edges. Do not depict a landscape, a person, an artist, an "
    "artistic style, or a recognizable existing artwork. Do not include text, lettering, "
    "a signature, a watermark, a border, a frame, or a collage."
)
EXPECTED_QUALIFICATION_PROMPT_SHA256 = (
    "3e102ad72192b8414045eb723db9980db872a75f2f8139507a54d99586068904"
)
EXPECTED_QUALIFICATION_REQUEST_SHA256 = (
    "dc887cb518e2df74f0ca150cb5545569300dfe0a060cc3ca6b55e2a19ea5d1df"
)
EXPECTED_OUTPUTS = {
    "prompt_manifest": "data/manifests/pilot_3/prompts.jsonl",
    "schedule_manifest": "data/manifests/pilot_3/schedule.jsonl",
    "phase_b_design": "reports/pilot_3/evidence/phase_b_design.json",
    "human_validation_disposition": ("reports/pilot_3/evidence/human_validation_disposition.json"),
    "prompt_schedule_contract": "reports/pilot_3/evidence/prompt_schedule_contract.json",
    "analysis_contract": "reports/pilot_3/evidence/analysis_contract.json",
}

_SHA256_CHARACTERS = frozenset("0123456789abcdef")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value).issubset(_SHA256_CHARACTERS)


def _mapping(value: object, *, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return dict(value)


def _sequence(value: object, *, label: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return list(value)


def _relative_path(value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-blank repository-relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must remain inside the repository")
    return path


def _resolve(root: Path, value: object, *, label: str) -> Path:
    relative = _relative_path(value, label=label)
    resolved_root = root.expanduser().resolve()
    resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the repository") from exc
    return resolved


def _seal(payload: Mapping[str, Any], *, field: str = "semantic_sha256") -> Dict[str, Any]:
    result = dict(payload)
    if field in result:
        raise ValueError(f"cannot seal a payload that already contains {field}")
    result[field] = stable_hash(result)
    return result


def _verify_seal(
    payload: Mapping[str, Any],
    *,
    field: str = "semantic_sha256",
    label: str,
) -> None:
    unsigned = dict(payload)
    recorded = unsigned.pop(field, None)
    if not _is_sha256(recorded) or stable_hash(unsigned) != recorded:
        raise ValueError(f"{label} has a stale or invalid {field}")


def _artifact_input(root: Path, item: Mapping[str, Any], *, label: str) -> Dict[str, str]:
    path = _resolve(root, item.get("path"), label=f"{label}.path")
    expected_file = item.get("file_sha256")
    expected_semantic = item.get("semantic_sha256")
    if not _is_sha256(expected_file) or not _is_sha256(expected_semantic):
        raise ValueError(f"{label} requires file and semantic SHA-256 values")
    if not path.is_file():
        raise FileNotFoundError(path)
    observed_file = hash_file(path)
    if observed_file != expected_file:
        raise RuntimeError(
            f"{label} file hash mismatch: expected {expected_file}, found {observed_file}"
        )
    value = _mapping(read_json(path), label=label)
    observed_semantic = value.get("semantic_sha256", value.get("result_sha256"))
    if observed_semantic != expected_semantic:
        raise RuntimeError(f"{label} semantic hash mismatch")
    use = item.get("use")
    if not isinstance(use, str) or not use.strip():
        raise ValueError(f"{label}.use must be explicit")
    return {
        "path": path.relative_to(root.resolve()).as_posix(),
        "file_sha256": observed_file,
        "semantic_sha256": expected_semantic,
        "use": use,
    }


def load_study_config(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Load and strictly validate the fixed Phase-B study configuration."""

    resolved_root = root.expanduser().resolve()
    path = _resolve(resolved_root, config_path.as_posix(), label="study config")
    if not path.is_file():
        raise FileNotFoundError(path)
    config = _mapping(read_json(path), label="study config")

    expected_header = {
        "schema_version": STUDY_SCHEMA,
        "status": "prospective_contract_pending_phase_a_transport_and_generation_gate",
        "generation_gate": "closed",
    }
    for key, expected in expected_header.items():
        if config.get(key) != expected:
            raise ValueError(f"study config requires {key}={expected!r}")

    boundary = _mapping(config.get("claim_boundary"), label="claim_boundary")
    if boundary.get("target_unit") != "finite_named_artist_roster":
        raise ValueError("Pilot 3 targets the finite named-artist roster")
    if boundary.get("artist_superpopulation_claim") is not False:
        raise ValueError("Pilot 3 must prohibit artist-superpopulation claims")
    if boundary.get("power_claim") is not False:
        raise ValueError("the 320-request design is an estimation design, not a power claim")
    if boundary.get("missingness_claim") != "realized_finite_assignment_schedule_only":
        raise ValueError("missingness claims must remain finite-schedule-only")

    artists = [
        _mapping(row, label="artist") for row in _sequence(config.get("artists"), label="artists")
    ]
    artist_ids = tuple(row.get("artist_id") for row in artists)
    if artist_ids != EXPECTED_ARTIST_IDS:
        raise ValueError("study config must contain the frozen four artists in canonical order")
    if any(
        not isinstance(row.get("artist_name"), str) or not row["artist_name"].strip()
        for row in artists
    ):
        raise ValueError("every artist requires a non-blank display name")
    neighbors = {str(row["artist_id"]): row.get("neighbor_artist_id") for row in artists}
    if any(neighbor not in artist_ids for neighbor in neighbors.values()):
        raise ValueError("every frozen neighbor must be in the finite roster")
    if any(artist_id == neighbor for artist_id, neighbor in neighbors.items()):
        raise ValueError("an artist cannot be its own neighbor")
    if any(neighbors.get(str(neighbor)) != artist_id for artist_id, neighbor in neighbors.items()):
        raise ValueError("the four-artist neighbor graph must consist of reciprocal pairs")
    if any(
        not isinstance(row.get("neighbor_rationale"), str) or not row["neighbor_rationale"].strip()
        for row in artists
    ):
        raise ValueError("every neighbor edge requires an outcome-independent rationale")

    design = _mapping(config.get("design"), label="design")
    expected_design = {
        "request_budget": EXPECTED_REQUEST_BUDGET,
        "content_block_count": EXPECTED_CONTENT_BLOCK_COUNT,
        "repetitions": EXPECTED_REPETITIONS,
        "requested_label_strata": 1,
        "power_or_minimum_detectable_effect_claim": False,
    }
    for key, expected in expected_design.items():
        if design.get(key) != expected:
            raise ValueError(f"design requires {key}={expected!r}")
    request_count = (
        (EXPECTED_ARTIST_COUNT + 1) * EXPECTED_CONTENT_BLOCK_COUNT * EXPECTED_REPETITIONS
    )
    next_request_count = (
        (EXPECTED_ARTIST_COUNT + 1) * (EXPECTED_CONTENT_BLOCK_COUNT + 1) * EXPECTED_REPETITIONS
    )
    if request_count != EXPECTED_REQUEST_BUDGET or next_request_count <= EXPECTED_REQUEST_BUDGET:
        raise ValueError("content-block maximization proof is inconsistent")

    condition = _mapping(config.get("request_condition"), label="request_condition")
    if condition.get("allowed_model_families") != ["gpt-image-1", "gpt-image-2"]:
        raise ValueError("only the two project-approved GPT Image families are allowed")
    if condition.get("scheduled_requested_labels") != [EXPECTED_REQUESTED_LABEL]:
        raise ValueError("Pilot 3 schedules exactly one gpt-image-2 requested-label stratum")
    if condition.get("transport") != EXPECTED_TRANSPORT:
        raise ValueError("Pilot 3 is restricted to ~/dev/openai-oauth")
    if condition.get("endpoint") != "/v1/images/generations":
        raise ValueError("Pilot 3 requires the frozen Image API generation endpoint")
    if condition.get("direct_api_browser_or_fallback_allowed") is not False:
        raise ValueError("direct API, browser, and fallback transports must be prohibited")
    parameters = _mapping(condition.get("parameters"), label="request parameters")
    if parameters != {
        "model": EXPECTED_REQUESTED_LABEL,
        "n": 1,
        "output_format": "png",
        "quality": "low",
        "size": "auto",
    }:
        raise ValueError("request parameters differ from the frozen condition")

    qualification = _mapping(
        config.get("transport_qualification"), label="transport_qualification"
    )
    expected_qualification = {
        "task_id": "P3-T11",
        "timing": "after_p3_t08_pass_before_freeze_b",
        "request_id": "p3-t11-neutral-transport-qualification-v1",
        "neutral_prompt": EXPECTED_QUALIFICATION_PROMPT,
        "neutral_prompt_sha256": EXPECTED_QUALIFICATION_PROMPT_SHA256,
        "canonical_request_sha256": EXPECTED_QUALIFICATION_REQUEST_SHA256,
        "requested_model_label": EXPECTED_REQUESTED_LABEL,
        "transport": EXPECTED_TRANSPORT,
        "endpoint_url": "http://127.0.0.1:10533/v1/images/generations",
        "dedicated_port": 10533,
        "execution_namespace": "pilot3-generation-v1",
        "parameters": {
            "model": EXPECTED_REQUESTED_LABEL,
            "n": 1,
            "output_format": "png",
            "quality": "low",
            "size": "auto",
        },
        "phase_a_result_path": (
            "reports/pilot_3/evidence/a_vector_external_validation.json"
        ),
        "account_authorization_evidence_path": (
            "reports/pilot_3/evidence/account_authorization.json"
        ),
        "model_documentation_evidence_path": (
            "reports/pilot_3/evidence/model_documentation.json"
        ),
        "oauth_runtime_fingerprint_path": (
            "reports/pilot_3/evidence/oauth_runtime_fingerprint.json"
        ),
        "freeze_b_generation_gate_path": "reports/pilot_3/evidence/generation_gate.json",
        "intent_ledger_path": (
            "artifacts/pilot_3/transport_qualification_post_intents.jsonl"
        ),
        "attempt_ledger_path": (
            "artifacts/pilot_3/transport_qualification_attempts.jsonl"
        ),
        "output_root": "outputs/pilot_3/transport_qualification",
        "artifact_path": "reports/pilot_3/evidence/transport_qualification.json",
        "physical_post_budget": 1,
        "retry_allowed": False,
        "outside_artist_content_grid": True,
        "excluded_from_feature_fitting_and_outcome_selection": True,
        "analytic_request_budget": EXPECTED_REQUEST_BUDGET,
        "shares_frozen_analytic_transport_config_and_runtime_fingerprint": True,
    }
    if qualification != expected_qualification:
        raise ValueError("P3-T11 transport qualification differs from the frozen contract")
    for key in (
        "phase_a_result_path",
        "account_authorization_evidence_path",
        "model_documentation_evidence_path",
        "oauth_runtime_fingerprint_path",
        "freeze_b_generation_gate_path",
        "intent_ledger_path",
        "attempt_ledger_path",
        "output_root",
        "artifact_path",
    ):
        _resolve(resolved_root, qualification[key], label=f"transport_qualification.{key}")

    operational_authorization = _mapping(
        config.get("operational_authorization"), label="operational_authorization"
    )
    if operational_authorization != {
        "path": "configs/pilot_3/generation_authorization.json",
        "schema_version": EXPECTED_GENERATION_AUTHORIZATION_SCHEMA,
        "initial_status": "closed",
        "freeze_b_required_status": "preregistered_generation_gate_open",
        "immutable_scientific_protocol_path": "docs/PILOT_3_PROTOCOL.md",
        "generation_gate_path": "reports/pilot_3/evidence/generation_gate.json",
        "transition_timing": (
            "after_p3_t01_through_p3_t13_including_one_shot_p3_t11_before_p3_t14"
        ),
        "generation_authorized_by_record_alone": False,
        "must_be_committed_clean_with_generation_gate": True,
    }:
        raise ValueError(
            "operational authorization differs from the frozen protocol/status split"
        )
    for key in ("path", "immutable_scientific_protocol_path", "generation_gate_path"):
        _resolve(
            resolved_root,
            operational_authorization[key],
            label=f"operational_authorization.{key}",
        )

    execution_schedule = _mapping(config.get("execution_schedule"), label="execution_schedule")
    if execution_schedule != {
        "namespace": "pilot3-assignment-order-v1",
        "seed": 20260903,
        "max_parallel": 4,
        "assignment_manifest_order": (
            "frozen_runtime_image_preflight_request_first_then_deterministic_seeded_sha256_"
            "rank_of_remaining_request_identities"
        ),
        "physical_send_order": (
            "runtime_image_preflight_first_then_canonical_sequence_batches_ascending; "
            "no_within_batch_post_order_claim_under_parallelism"
        ),
        "runtime_image_preflight_request_id": "p3-b16-r01-control",
        "runtime_image_preflight": (
            "the frozen autumn_vineyard repetition-one artist-free request is the first "
            "analytic request after the generation gate opens, provides fail-stop runtime "
            "and output revalidation only, remains an assigned analytic control in the "
            "320-request grid, and does not resolve P3-T11"
        ),
    }:
        raise ValueError("execution schedule differs from the frozen deterministic contract")

    prompt_contract = _mapping(config.get("prompt_contract"), label="prompt_contract")
    for key in ("prefix", "named_artist_clause_template", "separator", "common_suffix"):
        if not isinstance(prompt_contract.get(key), str) or not prompt_contract[key]:
            raise ValueError(f"prompt_contract.{key} must be a non-empty string")
    if prompt_contract.get("visual_selection_allowed") is not False:
        raise ValueError("visual output selection must be prohibited")

    blocks = [
        _mapping(row, label="content block")
        for row in _sequence(config.get("content_blocks"), label="content_blocks")
    ]
    if len(blocks) != EXPECTED_CONTENT_BLOCK_COUNT:
        raise ValueError("Pilot 3 requires exactly sixteen content blocks")
    block_ids = [row.get("content_block_id") for row in blocks]
    if len(set(block_ids)) != len(block_ids) or any(
        not isinstance(value, str) or not value.strip() for value in block_ids
    ):
        raise ValueError("content block identifiers must be unique and non-blank")
    for row in blocks:
        if not isinstance(row.get("scene"), str) or not row["scene"].strip():
            raise ValueError("every content block requires concrete scene text")
        annotations = row.get("annotations")
        if (
            not isinstance(annotations, list)
            or not annotations
            or any(not isinstance(value, str) or not value.strip() for value in annotations)
        ):
            raise ValueError("every content block requires non-blank annotations")

    human = _mapping(config.get("human_validation"), label="human_validation")
    if (
        human.get("disposition") != "excluded"
        or human.get("human_validity_claim_allowed") is not False
    ):
        raise ValueError("human validation must be terminally excluded")

    analysis = _mapping(config.get("analysis"), label="analysis")
    availability = _mapping(analysis.get("availability"), label="analysis.availability")
    if availability.get("family_size") != 17 or availability.get("degrees_of_freedom") != 15:
        raise ValueError("availability simultaneous family must have 17 tests and 15 df")
    conditional = _mapping(
        analysis.get("conditional_proximity"), label="analysis.conditional_proximity"
    )
    if conditional.get("family_size") != 2 or conditional.get("degrees_of_freedom") != 3:
        raise ValueError("conditional co-primary family must have two tests and three df")
    reversal = _mapping(analysis.get("artist_reversal_harm"), label="analysis.artist_reversal_harm")
    if reversal.get("family_size") != 8 or reversal.get("degrees_of_freedom") != 15:
        raise ValueError("artist-harm family must have eight tests and 15 df")
    missingness = _mapping(analysis.get("missingness"), label="analysis.missingness")
    if missingness.get("stochastic_generator_or_future_prompt_claim") is not False:
        raise ValueError("the contract must prohibit stochastic missingness claims")
    if not math.isclose(float(missingness.get("cell_weight", -1)), 1 / EXPECTED_PAIR_COUNT):
        raise ValueError("missingness cell weight must equal 1/256")
    runtime_inputs = _mapping(analysis.get("runtime_inputs"), label="analysis.runtime_inputs")
    expected_runtime_inputs = {
        "generation_attempts": "artifacts/pilot_3/generation_attempts.jsonl",
        "generation_post_intents": "artifacts/pilot_3/generation_post_intents.jsonl",
        "generation_global_stop_dispositions": (
            "artifacts/pilot_3/generation_global_stop_dispositions.jsonl"
        ),
        "generation_runtime_revalidations": (
            "reports/pilot_3/evidence/generation_runtime_revalidations.jsonl"
        ),
        "generation_completion": "reports/pilot_3/evidence/generation_completion.json",
        "terminal_dispositions": ("reports/pilot_3/evidence/terminal_dispositions.jsonl"),
        "terminal_disposition_envelope": (
            "reports/pilot_3/evidence/terminal_disposition_manifest.json"
        ),
        "generated_distances": "artifacts/pilot_3/generated_a_vector_distances.jsonl",
        "generated_measurement_completion": (
            "reports/pilot_3/evidence/generated_a_vector_measurement.json"
        ),
    }
    if runtime_inputs != expected_runtime_inputs:
        raise ValueError("analysis runtime input paths differ from the frozen contract")
    for name, value in runtime_inputs.items():
        _resolve(resolved_root, value, label=f"analysis.runtime_inputs.{name}")

    development = _mapping(config.get("development_evidence"), label="development_evidence")
    for name in ("pilot2_baseline_recovery", "planning_design_sensitivity"):
        _artifact_input(
            resolved_root,
            _mapping(development.get(name), label=f"development_evidence.{name}"),
            label=f"development_evidence.{name}",
        )

    future = _mapping(config.get("required_future_bindings"), label="required_future_bindings")
    expected_future = {
        "corpus_selection",
        "a_vector_protocol",
        "a_vector_external_validation",
        "lee_replication",
        "transport_qualification",
        "generation_authorization",
        "generation_gate",
    }
    if set(future) != expected_future:
        raise ValueError("required future bindings are incomplete")
    lee_binding = _mapping(future.get("lee_replication"), label="Lee binding")
    if lee_binding != {
        "path": "reports/pilot_3/evidence/lee_replication.json",
        "required_statuses": ["pass", "retire", "ineligible_retire"],
    }:
        raise ValueError("Lee binding must require one frozen terminal replication status")
    transport_binding = _mapping(future.get("transport_qualification"), label="transport binding")
    if transport_binding.get("path") != qualification["artifact_path"]:
        raise ValueError("transport binding must use the sole canonical P3-T11 artifact")
    if transport_binding.get("required_status") != "pass":
        raise ValueError("transport binding must require a terminal P3-T11 pass")
    if transport_binding.get("required_requested_label") != EXPECTED_REQUESTED_LABEL:
        raise ValueError("transport binding must require exact gpt-image-2 label")
    if transport_binding.get("required_transport") != EXPECTED_TRANSPORT:
        raise ValueError("transport binding must require ~/dev/openai-oauth")
    authorization_binding = _mapping(
        future.get("generation_authorization"), label="generation authorization binding"
    )
    if authorization_binding != {
        "path": operational_authorization["path"],
        "required_status": operational_authorization["freeze_b_required_status"],
    }:
        raise ValueError(
            "future generation authorization binding differs from the operational contract"
        )

    outputs = _mapping(config.get("outputs"), label="outputs")
    if outputs != EXPECTED_OUTPUTS:
        raise ValueError("study outputs must use the frozen canonical paths")
    for key, value in outputs.items():
        _resolve(resolved_root, value, label=f"outputs.{key}")
    return config


def _render_prompt(
    prompt_contract: Mapping[str, Any],
    scene: str,
    *,
    artist_name: Optional[str],
) -> str:
    clause = ""
    if artist_name is not None:
        clause = str(prompt_contract["named_artist_clause_template"]).format(
            artist_name=artist_name
        )
    return (
        f"{prompt_contract['prefix']}{clause}{prompt_contract['separator']}"
        f"{scene}. {prompt_contract['common_suffix']}"
    )


def build_prompt_rows(config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Build 16 controls and 64 named prompts with exact matched wording."""

    artists = [_mapping(row, label="artist") for row in config["artists"]]
    prompt_contract = _mapping(config["prompt_contract"], label="prompt_contract")
    rows: List[Dict[str, Any]] = []
    for block_rank, raw_block in enumerate(config["content_blocks"], start=1):
        block = _mapping(raw_block, label="content block")
        block_id = str(block["content_block_id"])
        pair_basis = {
            "prefix": prompt_contract["prefix"],
            "separator": prompt_contract["separator"],
            "scene": block["scene"],
            "common_suffix": prompt_contract["common_suffix"],
        }
        pair_basis_sha256 = stable_hash(pair_basis)
        control_id = f"p3-b{block_rank:02d}-control"
        control = {
            "record_type": "pilot3_prompt",
            "schema_version": PROMPT_SCHEMA,
            "prompt_id": control_id,
            "content_block_id": block_id,
            "content_block_rank": block_rank,
            "condition": "artist_free_control",
            "target_artist_id": None,
            "target_artist_name": None,
            "neighbor_artist_id": None,
            "paired_control_prompt_id": None,
            "content_annotations": list(block["annotations"]),
            "pair_basis_sha256": pair_basis_sha256,
            "prompt_text": _render_prompt(prompt_contract, str(block["scene"]), artist_name=None),
            "visual_selection_allowed": False,
        }
        rows.append(_seal(control, field="prompt_sha256"))
        for artist in artists:
            artist_id = str(artist["artist_id"])
            named = {
                "record_type": "pilot3_prompt",
                "schema_version": PROMPT_SCHEMA,
                "prompt_id": f"p3-b{block_rank:02d}-{artist_id.replace('_', '-')}",
                "content_block_id": block_id,
                "content_block_rank": block_rank,
                "condition": "named_artist",
                "target_artist_id": artist_id,
                "target_artist_name": artist["artist_name"],
                "neighbor_artist_id": artist["neighbor_artist_id"],
                "paired_control_prompt_id": control_id,
                "content_annotations": list(block["annotations"]),
                "pair_basis_sha256": pair_basis_sha256,
                "prompt_text": _render_prompt(
                    prompt_contract,
                    str(block["scene"]),
                    artist_name=str(artist["artist_name"]),
                ),
                "visual_selection_allowed": False,
            }
            rows.append(_seal(named, field="prompt_sha256"))
    if len(rows) != EXPECTED_PROMPT_COUNT:
        raise AssertionError("prompt builder did not emit exactly 80 prompts")
    return rows


def _request_body(condition: Mapping[str, Any], prompt_text: str) -> Dict[str, Any]:
    parameters = _mapping(condition["parameters"], label="request parameters")
    return {**parameters, "prompt": prompt_text}


def build_schedule_rows(
    config: Mapping[str, Any],
    prompt_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Build the exact 320-request schedule with one shared control per block/rep."""

    prompts = {str(row["prompt_id"]): dict(row) for row in prompt_rows}
    if len(prompts) != EXPECTED_PROMPT_COUNT:
        raise ValueError("prompt identifiers must be unique")
    condition = _mapping(config["request_condition"], label="request_condition")
    artists = [_mapping(row, label="artist") for row in config["artists"]]
    unsigned_rows: List[Dict[str, Any]] = []
    for block_rank in range(1, EXPECTED_CONTENT_BLOCK_COUNT + 1):
        block_id = str(config["content_blocks"][block_rank - 1]["content_block_id"])
        control_prompt_id = f"p3-b{block_rank:02d}-control"
        control_prompt = prompts[control_prompt_id]
        for repetition in range(1, EXPECTED_REPETITIONS + 1):
            control_request_id = f"p3-b{block_rank:02d}-r{repetition:02d}-control"
            control_body = _request_body(condition, str(control_prompt["prompt_text"]))
            control = {
                "record_type": "pilot3_scheduled_request",
                "schema_version": SCHEDULE_SCHEMA,
                "request_id": control_request_id,
                "content_block_id": block_id,
                "content_block_rank": block_rank,
                "repetition": repetition,
                "condition": "artist_free_control",
                "target_artist_id": None,
                "neighbor_artist_id": None,
                "prompt_id": control_prompt_id,
                "prompt_sha256": control_prompt["prompt_sha256"],
                "paired_control_request_id": None,
                "requested_model_label": EXPECTED_REQUESTED_LABEL,
                "transport": EXPECTED_TRANSPORT,
                "endpoint": condition["endpoint"],
                "request_body": control_body,
                "semantic_request_sha256": stable_hash(control_body),
            }
            unsigned_rows.append(control)
            for artist in artists:
                artist_id = str(artist["artist_id"])
                prompt_id = f"p3-b{block_rank:02d}-{artist_id.replace('_', '-')}"
                prompt = prompts[prompt_id]
                request_id = f"p3-b{block_rank:02d}-r{repetition:02d}-{artist_id.replace('_', '-')}"
                body = _request_body(condition, str(prompt["prompt_text"]))
                named = {
                    "record_type": "pilot3_scheduled_request",
                    "schema_version": SCHEDULE_SCHEMA,
                    "request_id": request_id,
                    "content_block_id": block_id,
                    "content_block_rank": block_rank,
                    "repetition": repetition,
                    "condition": "named_artist",
                    "target_artist_id": artist_id,
                    "neighbor_artist_id": artist["neighbor_artist_id"],
                    "prompt_id": prompt_id,
                    "prompt_sha256": prompt["prompt_sha256"],
                    "paired_control_request_id": control_request_id,
                    "requested_model_label": EXPECTED_REQUESTED_LABEL,
                    "transport": EXPECTED_TRANSPORT,
                    "endpoint": condition["endpoint"],
                    "request_body": body,
                    "semantic_request_sha256": stable_hash(body),
                }
                unsigned_rows.append(named)
    if len(unsigned_rows) != EXPECTED_SCHEDULE_COUNT:
        raise AssertionError("schedule builder did not emit exactly 320 requests")
    execution = _mapping(config["execution_schedule"], label="execution_schedule")
    namespace = str(execution["namespace"])
    seed = int(execution["seed"])
    runtime_preflight_request_id = str(
        execution["runtime_image_preflight_request_id"]
    )
    ranked: List[tuple[int, str, str, Dict[str, Any]]] = []
    for row in unsigned_rows:
        request_id = str(row["request_id"])
        order_sha256 = stable_hash(
            {
                "namespace": namespace,
                "seed": seed,
                "request_id": request_id,
                "semantic_request_sha256": row["semantic_request_sha256"],
            }
        )
        preflight_rank = 0 if request_id == runtime_preflight_request_id else 1
        ranked.append((preflight_rank, order_sha256, request_id, row))
    if sum(item[0] == 0 for item in ranked) != 1:
        raise AssertionError("schedule requires exactly one frozen runtime image preflight")
    ranked.sort(key=lambda item: (item[0], item[1], item[2]))

    rows: List[Dict[str, Any]] = []
    for sequence, (_, order_sha256, _, raw_row) in enumerate(ranked, start=1):
        row = dict(raw_row)
        row["sequence"] = sequence
        row["execution_order_sha256"] = order_sha256
        rows.append(_seal(row, field="schedule_row_sha256"))
    return rows


def adapt_schedule_to_generation(
    config: Mapping[str, Any],
    prompt_rows: Sequence[Mapping[str, Any]],
    schedule_rows: Sequence[Mapping[str, Any]],
    *,
    transport_config: Optional[Any] = None,
    prompt_manifest_file_sha256: Optional[str] = None,
    schedule_manifest_file_sha256: Optional[str] = None,
) -> tuple[List[Any], Any]:
    """Project canonical T12 rows into generation cells without reordering.

    This is a pure, offline integration adapter.  The schedule manifest's
    contiguous 1-based ``sequence`` remains the sole execution order; the
    generation layer retains every source identity, pairing, neighbor, row
    self-hash, and the redundant 1-based repetition alongside its internal
    zero-based repetition.
    """

    # The lazy imports keep prompt/config construction independent of the
    # image decoder and runtime transport modules.  The called adapter performs
    # validation and object construction only; it performs no network or image I/O.
    from latent_art_bench.pilot3.generation import (  # noqa: PLC0415
        adapt_t12_manifests_to_generation,
    )
    from latent_art_bench.pilot3.transport import (  # noqa: PLC0415
        Pilot3TransportConfig,
    )

    execution = _mapping(config["execution_schedule"], label="execution_schedule")
    resolved_transport = transport_config or Pilot3TransportConfig(
        frozen_requested_labels=(EXPECTED_REQUESTED_LABEL,)
    )
    if tuple(resolved_transport.frozen_requested_labels) != (EXPECTED_REQUESTED_LABEL,):
        raise ValueError("T12 generation adapter requires only the frozen gpt-image-2 alias")
    return adapt_t12_manifests_to_generation(
        prompt_rows,
        schedule_rows,
        transport_config=resolved_transport,
        namespace=str(execution["namespace"]),
        seed=int(execution["seed"]),
        max_parallel=int(execution["max_parallel"]),
        prompt_manifest_file_sha256=prompt_manifest_file_sha256,
        schedule_manifest_file_sha256=schedule_manifest_file_sha256,
    )


def _development_inputs(root: Path, config: Mapping[str, Any]) -> Dict[str, Dict[str, str]]:
    development = _mapping(config["development_evidence"], label="development_evidence")
    return {
        name: _artifact_input(
            root,
            _mapping(value, label=f"development_evidence.{name}"),
            label=f"development_evidence.{name}",
        )
        for name, value in sorted(development.items())
    }


def build_phase_b_design(
    root: Path,
    config_path: Path,
    config: Mapping[str, Any],
) -> Dict[str, Any]:
    cost_per_block = (EXPECTED_ARTIST_COUNT + 1) * EXPECTED_REPETITIONS
    maximum_blocks = EXPECTED_REQUEST_BUDGET // cost_per_block
    payload = {
        "record_type": "pilot3_phase_b_design",
        "schema_version": DESIGN_SCHEMA,
        "resolves_task_id": "P3-T04",
        "status": "selected_estimation_design_pending_phase_a_and_transport",
        "design_decision": "SELECTED_BUDGET_CONSTRAINED_ESTIMATION_DESIGN_NO_POWER_CLAIM",
        "generation_authorized": False,
        "network_or_image_requests_made": False,
        "config": {
            "path": config_path.as_posix(),
            "file_sha256": hash_file(_resolve(root, config_path.as_posix(), label="config")),
        },
        "claim_boundary": dict(config["claim_boundary"]),
        "finite_roster": [
            {
                "artist_id": row["artist_id"],
                "artist_name": row["artist_name"],
                "neighbor_artist_id": row["neighbor_artist_id"],
                "neighbor_rationale": row["neighbor_rationale"],
            }
            for row in config["artists"]
        ],
        "selection_proof": {
            "objective": "maximize_distinct_content_blocks_under_frozen_budget",
            "artist_count": EXPECTED_ARTIST_COUNT,
            "shared_controls_per_block_repetition": 1,
            "repetitions": EXPECTED_REPETITIONS,
            "request_budget": EXPECTED_REQUEST_BUDGET,
            "requests_per_content_block": cost_per_block,
            "maximum_integer_content_blocks": maximum_blocks,
            "selected_content_blocks": EXPECTED_CONTENT_BLOCK_COUNT,
            "selected_request_count": cost_per_block * EXPECTED_CONTENT_BLOCK_COUNT,
            "next_larger_design_request_count": cost_per_block * (EXPECTED_CONTENT_BLOCK_COUNT + 1),
            "tie_break_required": False,
        },
        "request_condition": dict(config["request_condition"]),
        "transport_qualification": dict(config["transport_qualification"]),
        "operational_authorization": dict(config["operational_authorization"]),
        "content_block_ids": [row["content_block_id"] for row in config["content_blocks"]],
        "expected_counts": {
            "nonanalytic_transport_qualification_requests": 1,
            "prompts": EXPECTED_PROMPT_COUNT,
            "logical_requests": EXPECTED_SCHEDULE_COUNT,
            "named_requests": EXPECTED_PAIR_COUNT,
            "shared_control_requests": EXPECTED_SCHEDULE_COUNT - EXPECTED_PAIR_COUNT,
            "named_control_pairs": EXPECTED_PAIR_COUNT,
        },
        "selection_basis": {
            "purpose": "estimation_and_uncertainty_characterization",
            "power_claim": False,
            "pilot2_values_role": "development-only guardrail calibration",
            "design_sensitivity_role": (
                "diagnostic evidence showing that no 80-percent power recommendation was "
                "available; it is not overwritten or relabeled as a power result"
            ),
        },
        "development_inputs": _development_inputs(root, config),
        "unresolved_prerequisites": sorted(config["required_future_bindings"]),
    }
    return _seal(payload)


def build_human_validation_disposition(config: Mapping[str, Any]) -> Dict[str, Any]:
    human = _mapping(config["human_validation"], label="human_validation")
    payload = {
        "record_type": "pilot3_human_validation_disposition",
        "schema_version": HUMAN_SCHEMA,
        "resolves_task_id": "P3-T10",
        "status": "excluded",
        "disposition": "excluded",
        "human_validity_claim_allowed": False,
        "reason": human["reason"],
        "post_output_addition_allowed": False,
        "effect_on_generation_authority": "none; all other gates remain required",
        "generation_authorized": False,
        "network_image_or_human_subject_io": "none",
    }
    return _seal(payload)


def _manifest_binding(path: Path, rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "path": path.as_posix(),
        "file_sha256": hash_file(path),
        "semantic_sha256": stable_hash(list(rows)),
        "row_count": len(rows),
    }


def build_prompt_schedule_contract(
    config: Mapping[str, Any],
    prompt_path: Path,
    prompt_rows: Sequence[Mapping[str, Any]],
    schedule_path: Path,
    schedule_rows: Sequence[Mapping[str, Any]],
    design_path: Path,
) -> Dict[str, Any]:
    generation_cells, generation_schedule = adapt_schedule_to_generation(
        config,
        prompt_rows,
        schedule_rows,
        prompt_manifest_file_sha256=hash_file(prompt_path),
        schedule_manifest_file_sha256=hash_file(schedule_path),
    )
    source_bijection = [
        {
            "source_sequence": cell.source_sequence,
            "source_request_id": cell.source_request_id,
            "source_schedule_row_sha256": cell.source_schedule_row_sha256,
            "generation_cell_id": cell.cell_id,
            "generation_cell_identity_sha256": cell.cell_identity_sha256,
        }
        for cell in generation_cells
    ]
    payload = {
        "record_type": "pilot3_prompt_schedule_contract",
        "schema_version": PROMPT_SCHEDULE_SCHEMA,
        "resolves_task_id": "P3-T12",
        "status": "frozen_offline_pending_phase_a_transport_and_generation_gate",
        "generation_authorized": False,
        "network_or_image_requests_made": False,
        "phase_b_design": {
            "path": design_path.as_posix(),
            "file_sha256": hash_file(design_path),
        },
        "prompt_manifest": _manifest_binding(prompt_path, prompt_rows),
        "schedule_manifest": _manifest_binding(schedule_path, schedule_rows),
        "pairing_contract": {
            "named_prompt_count": 64,
            "artist_free_prompt_count": 16,
            "named_request_count": EXPECTED_PAIR_COUNT,
            "shared_control_request_count": 64,
            "named_control_pair_count": EXPECTED_PAIR_COUNT,
            "control_sharing_unit": "content_block_by_repetition",
            "artist_count": EXPECTED_ARTIST_COUNT,
            "content_block_count": EXPECTED_CONTENT_BLOCK_COUNT,
            "repetitions": EXPECTED_REPETITIONS,
            "only_named_control_text_difference": config["prompt_contract"][
                "only_named_control_difference"
            ],
        },
        "request_contract": dict(config["request_condition"]),
        "generation_adapter_contract": {
            "adapter": ("latent_art_bench.pilot3.generation.adapt_t12_manifests_to_generation"),
            "ordering_basis": generation_schedule.ordering_basis,
            "cell_count": len(generation_cells),
            "generation_grid_sha256": generation_schedule.generation_grid_sha256,
            "generation_schedule_sha256": generation_schedule.schedule_sha256,
            "source_prompt_manifest_semantic_sha256": (
                generation_schedule.source_prompt_manifest_semantic_sha256
            ),
            "source_schedule_manifest_semantic_sha256": (
                generation_schedule.source_schedule_manifest_semantic_sha256
            ),
            "source_prompt_manifest_file_sha256": (
                generation_schedule.source_prompt_manifest_file_sha256
            ),
            "source_schedule_manifest_file_sha256": (
                generation_schedule.source_schedule_manifest_file_sha256
            ),
            "source_to_generation_bijection_sha256": stable_hash(source_bijection),
            "source_repetition_rule": (
                "manifest_1_through_4_maps_bijectively_to_internal_0_through_3"
            ),
            "secondary_reordering_allowed": False,
        },
        "execution_schedule": dict(config["execution_schedule"]),
        "schedule_order": (
            "the frozen runtime image preflight is the first analytic request and remains in "
            "the 320-request grid; it is not P3-T11. Remaining JSONL lines and contiguous "
            "sequence values follow the deterministic seeded SHA-256 rank of frozen request "
            "identity, with request_id as a collision tie-break; downstream adapters preserve "
            "this batch-dispatch order without a second ranking, while no within-batch physical "
            "POST ordering is claimed under four-way parallelism"
        ),
        "retry_identity": (
            "any future technical retry must preserve semantic_request_sha256 exactly; this "
            "contract itself does not authorize or send a request"
        ),
        "visual_selection_allowed": False,
    }
    return _seal(payload)


def build_analysis_contract(
    config: Mapping[str, Any],
    *,
    design_path: Path,
    human_path: Path,
    prompt_contract_path: Path,
    prompt_path: Path,
    schedule_path: Path,
) -> Dict[str, Any]:
    analysis = _mapping(config["analysis"], label="analysis")
    payload = {
        "record_type": "pilot3_analysis_contract",
        "schema_version": ANALYSIS_CONTRACT_SCHEMA,
        "resolves_task_id": "P3-T13",
        "status": "frozen_offline_pending_phase_a_transport_and_generation_gate",
        "generation_authorized": False,
        "analysis_authorized": False,
        "claim_boundary": dict(config["claim_boundary"]),
        "internal_bindings": {
            "phase_b_design": {
                "path": design_path.as_posix(),
                "file_sha256": hash_file(design_path),
            },
            "human_validation_disposition": {
                "path": human_path.as_posix(),
                "file_sha256": hash_file(human_path),
            },
            "prompt_schedule_contract": {
                "path": prompt_contract_path.as_posix(),
                "file_sha256": hash_file(prompt_contract_path),
            },
            "prompt_manifest": {
                "path": prompt_path.as_posix(),
                "file_sha256": hash_file(prompt_path),
            },
            "schedule_manifest": {
                "path": schedule_path.as_posix(),
                "file_sha256": hash_file(schedule_path),
            },
        },
        "required_future_bindings": {
            name: {**dict(value), "file_sha256": None}
            for name, value in sorted(config["required_future_bindings"].items())
        },
        "terminal_categories": [
            "usable_image",
            "policy_refusal",
            "nonretryable_client_response",
            "malformed_or_ineligible_success",
            "retry_cap_technical_failure",
            "indeterminate_after_interruption",
            "not_sent_global_stop",
        ],
        "usable_definition": (
            "U=1 only for usable_image after the frozen decode, PNG, geometry, provenance, "
            "preprocessing, and A-vector feature contract; every other terminal category has U=0"
        ),
        "availability": dict(analysis["availability"]),
        "conditional_proximity": {
            **dict(analysis["conditional_proximity"]),
            "co_primary_estimands": {
                "target_improvement": "d(control,a)-d(named,a)",
                "specificity_difference_in_differences": (
                    "[d(named,n(a))-d(named,a)]-[d(control,n(a))-d(control,a)]"
                ),
            },
            "conditioning": "usable named/control pairs only",
            "assigned_and_usable_denominators_required": True,
        },
        "artist_reversal_harm": dict(analysis["artist_reversal_harm"]),
        "missingness": dict(analysis["missingness"]),
        "execution_guard": {
            "state": "closed_pending_canonical_p3_t14_file_backed_verifier",
            "caller_supplied_hashes_or_statuses_may_authorize": False,
            "runtime_inputs": dict(analysis["runtime_inputs"]),
            "required_verification": [
                (
                    "load the canonical analysis contract and schedule files and match their "
                    "file and semantic hashes to the opened P3-T14 generation gate"
                ),
                (
                    "re-hash and self-seal-check corpus, P3-T07, P3-T08, P3-T09, P3-T11, "
                    "P3-T14, generation-completion, terminal-envelope, and "
                    "generated-measurement artifacts and enforce their exact terminal statuses"
                ),
                (
                    "extract target_improvement tau from P3-T07 development_results.tau.target "
                    "and specificity tau from P3-T07 development_results.tau.specificity; no "
                    "caller override is permitted"
                ),
                (
                    "require terminal-envelope bindings to the schedule file hash, "
                    "generation-completion file hash, generation-grid and schedule hashes, "
                    "attempt-ledger semantic hash, and every source schedule-row hash"
                ),
                (
                    "treat a successful generation only as output_eligible_for_preprocessing "
                    "until the terminal envelope binds successful preprocessing and A-vector "
                    "extraction before assigning usable_image"
                ),
                (
                    "require generated-measurement completion to bind P3-T07 state files and "
                    "result hash, every generated PNG hash, every generated A-vector hash, and "
                    "the exact distance-manifest semantic hash"
                ),
            ],
            "public_analysis_entrypoint_behavior_before_verifier": (
                "raise_runtime_error_before_computation"
            ),
        },
        "terminal_decisions": dict(analysis["terminal_decisions"]),
        "exact_accounting": {
            "scheduled_request_count": EXPECTED_SCHEDULE_COUNT,
            "named_control_pair_count": EXPECTED_PAIR_COUNT,
            "one_terminal_disposition_per_request": True,
            "unscheduled_or_duplicate_terminal_rows_allowed": False,
            "feature_for_unusable_request_allowed": False,
            "outcome_dependent_stopping_or_replacement_allowed": False,
        },
        "readiness": {
            "ready": False,
            "decision": "CLOSED_PENDING_EXTERNAL_BINDINGS",
            "required_bindings": sorted(config["required_future_bindings"]),
        },
    }
    return _seal(payload)


def _output_paths(root: Path, config: Mapping[str, Any]) -> Dict[str, Path]:
    return {
        name: _resolve(root, value, label=f"outputs.{name}")
        for name, value in _mapping(config["outputs"], label="outputs").items()
    }


def write_phase_b_freeze_bundle(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Write all deterministic Phase-B freeze artifacts without external I/O."""

    resolved_root = root.expanduser().resolve()
    config = load_study_config(resolved_root, config_path)
    paths = _output_paths(resolved_root, config)
    relative_paths = {name: path.relative_to(resolved_root) for name, path in paths.items()}

    prompt_rows = build_prompt_rows(config)
    schedule_rows = build_schedule_rows(config, prompt_rows)
    write_jsonl(paths["prompt_manifest"], prompt_rows)
    write_jsonl(paths["schedule_manifest"], schedule_rows)

    design = build_phase_b_design(resolved_root, config_path, config)
    human = build_human_validation_disposition(config)
    write_json(paths["phase_b_design"], design)
    write_json(paths["human_validation_disposition"], human)

    prompt_contract = build_prompt_schedule_contract(
        config,
        paths["prompt_manifest"],
        prompt_rows,
        paths["schedule_manifest"],
        schedule_rows,
        paths["phase_b_design"],
    )
    for binding_name in ("phase_b_design", "prompt_manifest", "schedule_manifest"):
        prompt_contract[binding_name]["path"] = relative_paths[
            "phase_b_design" if binding_name == "phase_b_design" else binding_name
        ].as_posix()
    unsigned_prompt_contract = dict(prompt_contract)
    unsigned_prompt_contract.pop("semantic_sha256")
    prompt_contract["semantic_sha256"] = stable_hash(unsigned_prompt_contract)
    write_json(paths["prompt_schedule_contract"], prompt_contract)

    analysis_contract = build_analysis_contract(
        config,
        design_path=paths["phase_b_design"],
        human_path=paths["human_validation_disposition"],
        prompt_contract_path=paths["prompt_schedule_contract"],
        prompt_path=paths["prompt_manifest"],
        schedule_path=paths["schedule_manifest"],
    )
    for name, key in (
        ("phase_b_design", "phase_b_design"),
        ("human_validation_disposition", "human_validation_disposition"),
        ("prompt_schedule_contract", "prompt_schedule_contract"),
        ("prompt_manifest", "prompt_manifest"),
        ("schedule_manifest", "schedule_manifest"),
    ):
        analysis_contract["internal_bindings"][name]["path"] = relative_paths[key].as_posix()
    unsigned_analysis = dict(analysis_contract)
    unsigned_analysis.pop("semantic_sha256")
    analysis_contract["semantic_sha256"] = stable_hash(unsigned_analysis)
    write_json(paths["analysis_contract"], analysis_contract)

    return verify_phase_b_freeze_bundle(resolved_root, config_path)


def _verify_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    hash_field: str,
    label: str,
) -> None:
    for index, row in enumerate(rows, start=1):
        _verify_seal(row, field=hash_field, label=f"{label}[{index}]")


def verify_phase_b_freeze_bundle(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Recompute and verify the complete offline Phase-B freeze bundle."""

    resolved_root = root.expanduser().resolve()
    config = load_study_config(resolved_root, config_path)
    paths = _output_paths(resolved_root, config)
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    prompt_rows = read_jsonl(paths["prompt_manifest"])
    schedule_rows = read_jsonl(paths["schedule_manifest"])
    _verify_rows(prompt_rows, hash_field="prompt_sha256", label="prompt")
    _verify_rows(schedule_rows, hash_field="schedule_row_sha256", label="schedule")
    expected_prompts = build_prompt_rows(config)
    expected_schedule = build_schedule_rows(config, expected_prompts)
    if prompt_rows != expected_prompts:
        raise ValueError("prompt manifest does not recompute exactly")
    if schedule_rows != expected_schedule:
        raise ValueError("schedule manifest does not recompute exactly")

    design = _mapping(read_json(paths["phase_b_design"]), label="phase_b design")
    human = _mapping(read_json(paths["human_validation_disposition"]), label="human disposition")
    prompt_contract = _mapping(
        read_json(paths["prompt_schedule_contract"]), label="prompt/schedule contract"
    )
    analysis_contract = _mapping(read_json(paths["analysis_contract"]), label="analysis contract")
    for value, label in (
        (design, "phase_b design"),
        (human, "human disposition"),
        (prompt_contract, "prompt/schedule contract"),
        (analysis_contract, "analysis contract"),
    ):
        _verify_seal(value, label=label)

    expected_design = build_phase_b_design(resolved_root, config_path, config)
    expected_human = build_human_validation_disposition(config)
    if design != expected_design:
        raise ValueError("phase_b design does not recompute exactly")
    if human != expected_human:
        raise ValueError("human disposition does not recompute exactly")

    relative = {name: path.relative_to(resolved_root) for name, path in paths.items()}
    expected_prompt_contract = build_prompt_schedule_contract(
        config,
        paths["prompt_manifest"],
        prompt_rows,
        paths["schedule_manifest"],
        schedule_rows,
        paths["phase_b_design"],
    )
    for binding_name in ("phase_b_design", "prompt_manifest", "schedule_manifest"):
        expected_prompt_contract[binding_name]["path"] = relative[
            "phase_b_design" if binding_name == "phase_b_design" else binding_name
        ].as_posix()
    unsigned = dict(expected_prompt_contract)
    unsigned.pop("semantic_sha256")
    expected_prompt_contract["semantic_sha256"] = stable_hash(unsigned)
    if prompt_contract != expected_prompt_contract:
        raise ValueError("prompt/schedule contract does not recompute exactly")

    expected_analysis = build_analysis_contract(
        config,
        design_path=paths["phase_b_design"],
        human_path=paths["human_validation_disposition"],
        prompt_contract_path=paths["prompt_schedule_contract"],
        prompt_path=paths["prompt_manifest"],
        schedule_path=paths["schedule_manifest"],
    )
    for name, key in (
        ("phase_b_design", "phase_b_design"),
        ("human_validation_disposition", "human_validation_disposition"),
        ("prompt_schedule_contract", "prompt_schedule_contract"),
        ("prompt_manifest", "prompt_manifest"),
        ("schedule_manifest", "schedule_manifest"),
    ):
        expected_analysis["internal_bindings"][name]["path"] = relative[key].as_posix()
    unsigned = dict(expected_analysis)
    unsigned.pop("semantic_sha256")
    expected_analysis["semantic_sha256"] = stable_hash(unsigned)
    if analysis_contract != expected_analysis:
        raise ValueError("analysis contract does not recompute exactly")

    return {
        "status": "verified_closed_pending_external_bindings",
        "generation_authorized": False,
        "analysis_authorized": False,
        "prompt_count": len(prompt_rows),
        "schedule_count": len(schedule_rows),
        "named_control_pair_count": EXPECTED_PAIR_COUNT,
        "requested_labels": [EXPECTED_REQUESTED_LABEL],
        "transport": EXPECTED_TRANSPORT,
        "phase_b_design_sha256": design["semantic_sha256"],
        "prompt_schedule_contract_sha256": prompt_contract["semantic_sha256"],
        "analysis_contract_sha256": analysis_contract["semantic_sha256"],
        "required_bindings": sorted(config["required_future_bindings"]),
    }


def assess_future_bindings(
    root: Path,
    config_path: Path = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Read future evidence and report readiness without changing the frozen bundle."""

    resolved_root = root.expanduser().resolve()
    config = load_study_config(resolved_root, config_path)
    results: Dict[str, Dict[str, Any]] = {}
    for name, raw in sorted(config["required_future_bindings"].items()):
        requirement = _mapping(raw, label=f"required_future_bindings.{name}")
        path = _resolve(resolved_root, requirement.get("path"), label=f"{name}.path")
        row: Dict[str, Any] = {
            "path": path.relative_to(resolved_root).as_posix(),
            "present": path.is_file(),
            "satisfied": False,
            "file_sha256": hash_file(path) if path.is_file() else None,
        }
        if path.is_file():
            value = _mapping(read_json(path), label=name)
            row["observed_status"] = value.get("status")
            if "required_statuses" in requirement:
                statuses = _sequence(
                    requirement.get("required_statuses"),
                    label=f"required_future_bindings.{name}.required_statuses",
                )
                row["satisfied"] = value.get("status") in statuses
            else:
                row["satisfied"] = value.get("status") == requirement.get("required_status")
            if name == "transport_qualification":
                row["satisfied"] = bool(
                    row["satisfied"]
                    and value.get("requested_model_label")
                    == requirement.get("required_requested_label")
                    and value.get("transport") == requirement.get("required_transport")
                )
        results[name] = row
    ready = all(row["satisfied"] for row in results.values())
    return {
        "required_bindings_present_and_status_matched": ready,
        "generation_authorized": False,
        "decision": (
            "BINDINGS_MATCHED_REQUIRES_SEPARATE_GENERATION_GATE_VERIFIER" if ready else "CLOSED"
        ),
        "bindings": results,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("write", "verify", "readiness"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    if args.action == "write":
        result = write_phase_b_freeze_bundle(args.root, args.config)
    elif args.action == "verify":
        result = verify_phase_b_freeze_bundle(args.root, args.config)
    else:
        result = assess_future_bindings(args.root, args.config)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
