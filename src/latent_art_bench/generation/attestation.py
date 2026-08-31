from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from PIL import Image

from latent_art_bench.config import GenerationConfig
from latent_art_bench.generation.openai_images import (
    attest_legacy_generation_call,
    generation_config_sha256,
    generation_endpoint,
    generation_prompt_record_sha256,
    generation_request_sha256,
    unique_successful_generation_calls_by_cell,
)
from latent_art_bench.io import hash_file, read_json, stable_hash
from latent_art_bench.schemas import GenerationCallRecord, PromptRecord, RunRecord


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _display_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(resolved)


def _requested_dimensions(value: str) -> Optional[Tuple[int, int]]:
    if value == "auto":
        return None
    try:
        width, height = value.lower().split("x", maxsplit=1)
        parsed = (int(width), int(height))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid requested image dimensions: {value!r}") from exc
    if parsed[0] <= 0 or parsed[1] <= 0:
        raise ValueError(f"invalid requested image dimensions: {value!r}")
    return parsed


def _prompt_index(prompts: Sequence[PromptRecord]) -> Dict[str, PromptRecord]:
    by_id = {prompt.prompt_id: prompt for prompt in prompts}
    if len(by_id) != len(prompts):
        raise ValueError("generation prompt identifiers must be unique")
    return by_id


def _expected_cells(
    prompts: Sequence[PromptRecord], config: GenerationConfig
) -> set[Tuple[str, str, int]]:
    return {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.models
        for repetition in range(config.repetitions)
    }


def validate_generation_call_identities(
    calls: Iterable[GenerationCallRecord],
    prompts: Sequence[PromptRecord],
    config: GenerationConfig,
) -> None:
    """Reject missing, stale, or internally inconsistent request identities."""

    rows = list(calls)
    prompt_by_id = _prompt_index(prompts)
    call_ids = [call.call_id for call in rows]
    if len(call_ids) != len(set(call_ids)):
        raise ValueError("generation call identifiers must be unique")
    expected_config_hash = generation_config_sha256(config)
    expected_cells = _expected_cells(prompts, config)
    observed_cells = {(call.prompt_id, call.model, call.repetition) for call in rows}
    unexpected = observed_cells - expected_cells
    if unexpected:
        raise ValueError(f"generation manifest contains {len(unexpected)} unexpected cells")
    for call in rows:
        prompt = prompt_by_id.get(call.prompt_id)
        if prompt is None:
            raise ValueError(f"generation call references unknown prompt: {call.prompt_id}")
        expected = {
            "endpoint": generation_endpoint(config),
            "requested_size": config.size,
            "requested_quality": config.quality,
            "requested_output_format": config.output_format,
            "prompt_record_sha256": generation_prompt_record_sha256(prompt),
            "generation_config_sha256": expected_config_hash,
            "request_identity_sha256": generation_request_sha256(
                prompt, call.model, call.repetition, config
            ),
        }
        mismatches = [name for name, value in expected.items() if getattr(call, name) != value]
        if call.model not in config.models:
            mismatches.append("model")
        if call.request_identity_provenance not in {
            "native_pre_request",
            "legacy_run_attestation",
        }:
            mismatches.append("request_identity_provenance")
        if mismatches:
            raise ValueError(
                f"generation request identity mismatch for {call.call_id}: "
                + ", ".join(sorted(mismatches))
            )


def _verify_output(call: GenerationCallRecord, root: Path) -> Dict[str, Any]:
    if not call.output_path or not call.output_sha256:
        raise ValueError(f"successful generation call lacks output provenance: {call.call_id}")
    path = _resolve(root, call.output_path)
    if not path.is_file():
        raise FileNotFoundError(f"missing generated output for {call.call_id}: {path}")
    observed_sha256 = hash_file(path)
    if observed_sha256 != call.output_sha256:
        raise ValueError(f"generated output hash mismatch for {call.call_id}")
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        image_format = (image.format or "unknown").lower()
    observed_sha256_after_decode = hash_file(path)
    if observed_sha256_after_decode != observed_sha256:
        raise ValueError(f"generated output changed while verifying {call.call_id}")
    if (width, height) != (call.actual_width, call.actual_height):
        raise ValueError(f"generated output dimensions mismatch for {call.call_id}")
    if image_format != call.actual_format:
        raise ValueError(f"generated output format mismatch for {call.call_id}")
    requested_dimensions = _requested_dimensions(call.requested_size)
    if requested_dimensions is None:
        dimension_contract_status = "not_comparable_auto"
        dimension_contract_satisfied: Optional[bool] = None
    else:
        dimension_contract_satisfied = requested_dimensions == (width, height)
        dimension_contract_status = "exact_match" if dimension_contract_satisfied else "mismatch"
    format_contract_satisfied = image_format == call.requested_output_format
    return {
        "call_id": call.call_id,
        "request_identity_sha256": call.request_identity_sha256,
        "output_path": _display_path(path, root),
        "output_sha256": observed_sha256,
        "requested_size": call.requested_size,
        "requested_width": (requested_dimensions[0] if requested_dimensions is not None else None),
        "requested_height": (requested_dimensions[1] if requested_dimensions is not None else None),
        "actual_width": width,
        "actual_height": height,
        "dimension_contract_status": dimension_contract_status,
        "dimension_contract_satisfied": dimension_contract_satisfied,
        "requested_format": call.requested_output_format,
        "actual_format": image_format,
        "format_contract_status": ("exact_match" if format_contract_satisfied else "mismatch"),
        "format_contract_satisfied": format_contract_satisfied,
    }


def _qualification_context(
    qualification_card_paths: Optional[Mapping[str, Path]],
    qualification_contract_hashes: Optional[Mapping[str, str]],
    root: Path,
) -> Dict[str, Any]:
    """Hash current qualification artifacts without attributing them to old calls."""

    if qualification_card_paths is None:
        if qualification_contract_hashes is not None:
            raise ValueError("qualification contract hashes require qualification card paths")
        return {
            "provided": False,
            "all_cards_pass": False,
            "contracts_present": False,
            "evidence_complete": False,
            "artifacts": {},
            "context_sha256": None,
        }
    if not qualification_card_paths:
        raise ValueError("qualification card paths must not be empty")
    if qualification_contract_hashes is not None and set(qualification_contract_hashes) != set(
        qualification_card_paths
    ):
        raise ValueError("qualification contract hashes must cover exactly the supplied cards")

    artifacts: Dict[str, Any] = {}
    for measurement, raw_card_path in sorted(qualification_card_paths.items()):
        card_path = _resolve(root, str(raw_card_path)).resolve()
        if not card_path.is_file():
            raise FileNotFoundError(
                f"missing current qualification card for {measurement}: {card_path}"
            )
        card = read_json(card_path)
        if not isinstance(card, dict):
            raise ValueError(f"qualification card is not an object: {card_path}")
        if card.get("measurement") != measurement:
            raise ValueError(
                f"qualification card measurement mismatch for {measurement}: {card_path}"
            )
        status = card.get("status")
        if status not in {"pending", "pass", "conditional_pass", "fail"}:
            raise ValueError(f"invalid qualification card status: {card_path}")
        contract_hash = card.get("qualification_contract_hash")
        if contract_hash is not None and (
            not isinstance(contract_hash, str)
            or len(contract_hash) != 64
            or any(character not in "0123456789abcdef" for character in contract_hash)
        ):
            raise ValueError(f"invalid qualification contract hash: {card_path}")
        if qualification_contract_hashes is not None:
            expected_contract = qualification_contract_hashes[measurement]
            if contract_hash != expected_contract:
                raise ValueError(f"qualification card contract mismatch for {measurement}")

        raw_evidence_paths = card.get("evidence_paths")
        if (
            not isinstance(raw_evidence_paths, list)
            or not raw_evidence_paths
            or not all(isinstance(value, str) and value for value in raw_evidence_paths)
        ):
            raise ValueError(f"qualification card has invalid evidence_paths: {card_path}")
        evidence_artifacts = []
        for raw_evidence_path in raw_evidence_paths:
            evidence_path = _resolve(root, raw_evidence_path).resolve()
            if not evidence_path.is_file():
                raise FileNotFoundError(
                    f"missing qualification evidence for {measurement}: {evidence_path}"
                )
            evidence_artifacts.append(
                {
                    "path": _display_path(evidence_path, root),
                    "sha256": hash_file(evidence_path),
                }
            )
        artifacts[measurement] = {
            "card_path": _display_path(card_path, root),
            "card_sha256": hash_file(card_path),
            "card_status": status,
            "qualification_contract_hash": contract_hash,
            "evidence_artifacts": evidence_artifacts,
        }

    return {
        "provided": True,
        "all_cards_pass": all(artifact["card_status"] == "pass" for artifact in artifacts.values()),
        "contracts_present": all(
            artifact["qualification_contract_hash"] is not None for artifact in artifacts.values()
        ),
        "evidence_complete": all(
            bool(artifact["evidence_artifacts"]) for artifact in artifacts.values()
        ),
        "artifacts": artifacts,
        "context_sha256": stable_hash(artifacts),
    }


def _originating_qualification_evidence(
    run: RunRecord,
    qualification_context: Mapping[str, Any],
    root: Path,
) -> Dict[str, Any]:
    artifacts = qualification_context.get("artifacts", {})
    recorded_by_resolved_path: Dict[Path, List[str]] = {}
    for raw_path, digest in run.input_hashes.items():
        resolved_path = _resolve(root, raw_path).resolve()
        recorded_by_resolved_path.setdefault(resolved_path, []).append(digest)

    card_comparisons = []
    evidence_comparisons = []
    for measurement, artifact in sorted(artifacts.items()):
        card_path = _resolve(root, artifact["card_path"]).resolve()
        recorded_hashes = sorted(set(recorded_by_resolved_path.get(card_path, [])))
        if len(recorded_hashes) > 1:
            raise ValueError(
                f"originating run {run.run_id} recorded conflicting hashes for "
                f"the {measurement} qualification card"
            )
        recorded_hash = recorded_hashes[0] if recorded_hashes else None
        card_comparisons.append(
            {
                "measurement": measurement,
                "card_path": artifact["card_path"],
                "originating_card_sha256": recorded_hash,
                "current_card_sha256": artifact["card_sha256"],
                "exact_hash_match": recorded_hash == artifact["card_sha256"],
            }
        )
        for evidence_artifact in artifact["evidence_artifacts"]:
            evidence_path = _resolve(root, evidence_artifact["path"]).resolve()
            recorded_evidence_hashes = sorted(set(recorded_by_resolved_path.get(evidence_path, [])))
            if len(recorded_evidence_hashes) > 1:
                raise ValueError(
                    f"originating run {run.run_id} recorded conflicting hashes for "
                    f"qualification evidence {evidence_artifact['path']}"
                )
            recorded_evidence_hash = (
                recorded_evidence_hashes[0] if recorded_evidence_hashes else None
            )
            evidence_comparisons.append(
                {
                    "measurement": measurement,
                    "evidence_path": evidence_artifact["path"],
                    "originating_evidence_sha256": recorded_evidence_hash,
                    "current_evidence_sha256": evidence_artifact["sha256"],
                    "exact_hash_match": (recorded_evidence_hash == evidence_artifact["sha256"]),
                }
            )
    all_comparisons = card_comparisons + evidence_comparisons
    exact_context_match = bool(all_comparisons) and all(
        comparison["exact_hash_match"] for comparison in all_comparisons
    )
    return {
        "qualification_card_inputs": card_comparisons,
        "qualification_evidence_inputs": evidence_comparisons,
        "exact_current_context_match": exact_context_match,
    }


def _output_contract_summary(
    output_evidence: Sequence[Mapping[str, Any]], config: GenerationConfig
) -> Dict[str, Any]:
    dimension_counts = Counter(
        f"{row['actual_width']}x{row['actual_height']}" for row in output_evidence
    )
    dimension_status_counts = Counter(
        str(row["dimension_contract_status"]) for row in output_evidence
    )
    format_status_counts = Counter(str(row["format_contract_status"]) for row in output_evidence)
    if dimension_status_counts.get("mismatch", 0):
        overall_dimension_status = "violated"
    elif dimension_status_counts.get("not_comparable_auto", 0):
        overall_dimension_status = "not_verifiable"
    else:
        overall_dimension_status = "satisfied"
    overall_format_status = "violated" if format_status_counts.get("mismatch", 0) else "satisfied"
    return {
        "requested_size": config.size,
        "requested_size_match_count": dimension_status_counts.get("exact_match", 0),
        "requested_size_mismatch_count": dimension_status_counts.get("mismatch", 0),
        "requested_size_not_comparable_count": dimension_status_counts.get(
            "not_comparable_auto", 0
        ),
        "requested_dimension_contract_status": overall_dimension_status,
        "requested_output_format": config.output_format,
        "requested_format_match_count": format_status_counts.get("exact_match", 0),
        "requested_format_mismatch_count": format_status_counts.get("mismatch", 0),
        "requested_format_contract_status": overall_format_status,
        "actual_dimension_counts": dict(sorted(dimension_counts.items())),
    }


def _scientific_use_evidence(
    calls: Sequence[GenerationCallRecord],
    config: GenerationConfig,
    qualification_context: Mapping[str, Any],
    run_evidence: Sequence[Mapping[str, Any]],
    output_contract: Mapping[str, Any],
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    originating_qualification_proven = bool(
        qualification_context["provided"]
        and qualification_context["all_cards_pass"]
        and qualification_context["contracts_present"]
        and qualification_context["evidence_complete"]
        and run_evidence
        and all(
            row["originating_qualification"]["exact_current_context_match"] for row in run_evidence
        )
    )
    scientific_ineligibility_reasons = []
    if config.mode == "test_only" or config.scientific_claims_enabled is False:
        scientific_ineligibility_reasons.append(
            "generation config is test-only and explicitly disables scientific claims"
        )
    if not qualification_context["provided"]:
        scientific_ineligibility_reasons.append(
            "current qualification artifacts were not supplied to this attestation"
        )
    elif not qualification_context["all_cards_pass"]:
        scientific_ineligibility_reasons.append(
            "current qualification cards do not all have pass status"
        )
    if qualification_context["provided"] and not qualification_context["contracts_present"]:
        scientific_ineligibility_reasons.append(
            "current qualification cards do not all bind qualification contracts"
        )
    if qualification_context["provided"] and not qualification_context["evidence_complete"]:
        scientific_ineligibility_reasons.append(
            "current qualification cards do not all bind evidence artifacts"
        )
    if not originating_qualification_proven:
        scientific_ineligibility_reasons.append(
            "originating runs do not bind the exact current passing qualification cards "
            "and their evidence artifacts"
        )
    if output_contract["requested_dimension_contract_status"] != "satisfied":
        scientific_ineligibility_reasons.append(
            "returned image dimensions do not satisfy the exact requested-size contract"
        )
    if output_contract["requested_format_contract_status"] != "satisfied":
        scientific_ineligibility_reasons.append(
            "returned image formats do not satisfy the requested-format contract"
        )
    if any(call.qualification_bypass for call in calls):
        scientific_ineligibility_reasons.append(
            "one or more generation attempts used the explicit unqualified test bypass"
        )

    scientific_eligible = not scientific_ineligibility_reasons
    legacy_call_ids = [
        call.call_id
        for call in calls
        if call.request_identity_provenance == "legacy_run_attestation"
    ]
    legacy_disposition = {
        "attempt_count": len(legacy_call_ids),
        "call_ids": legacy_call_ids,
        "originating_qualification_proven": originating_qualification_proven,
        "disposition": (
            "originating_qualification_verified"
            if originating_qualification_proven
            else "grandfathered_engineering_only"
        ),
        "superseded_by_current_qualification_context": bool(
            qualification_context["provided"] and not originating_qualification_proven
        ),
        "scientifically_eligible": bool(scientific_eligible and originating_qualification_proven),
        "statement": (
            "Legacy attempts are retained for auditable engineering-only analysis; "
            "current qualification artifacts are contextual evidence and are not "
            "attributed retroactively to the originating API calls."
            if legacy_call_ids and not originating_qualification_proven
            else "No legacy qualification claim is inferred beyond recorded run inputs."
        ),
    }
    scientific_eligibility = {
        "eligible": scientific_eligible,
        "permitted_use": (
            "scientific_and_engineering" if scientific_eligible else "engineering_only"
        ),
        "reasons": scientific_ineligibility_reasons,
    }
    return (
        originating_qualification_proven,
        legacy_disposition,
        scientific_eligibility,
    )


def attest_generation_calls(
    calls: Sequence[GenerationCallRecord],
    prompts: Sequence[PromptRecord],
    config: GenerationConfig,
    prompt_manifest: Path,
    run_records: Mapping[str, RunRecord],
    run_record_paths: Mapping[str, Path],
    root: Path,
    *,
    qualification_card_paths: Optional[Mapping[str, Path]] = None,
    qualification_contract_hashes: Optional[Mapping[str, str]] = None,
) -> Tuple[List[GenerationCallRecord], Dict[str, Any]]:
    """Attest native and legacy calls, returning rewritten rows plus sidecar evidence."""

    root = root.resolve()
    qualification_context = _qualification_context(
        qualification_card_paths, qualification_contract_hashes, root
    )
    prompt_by_id = _prompt_index(prompts)
    expected_config_hash = generation_config_sha256(config)
    updated: List[GenerationCallRecord] = []
    legacy_count = 0
    native_count = 0
    for call in calls:
        prompt = prompt_by_id.get(call.prompt_id)
        if prompt is None:
            raise ValueError(f"generation call references unknown prompt: {call.prompt_id}")
        expected_identity = generation_request_sha256(prompt, call.model, call.repetition, config)
        if call.request_identity_provenance == "native_pre_request":
            native_count += 1
            if call.request_identity_sha256 != expected_identity:
                raise ValueError(f"native request identity mismatch for {call.call_id}")
            provenance = "native_pre_request"
        else:
            legacy_count += 1
            run = run_records.get(call.run_id)
            if run is None:
                raise ValueError(f"missing originating run record for {call.call_id}")
            attested_identity = attest_legacy_generation_call(call, run, prompt_manifest)
            if attested_identity != expected_identity:
                raise ValueError(
                    f"legacy run request contract differs from current config: {call.call_id}"
                )
            legacy_config = GenerationConfig.model_validate(
                dict(run.resolved_config or {}).get("generation")
            )
            if generation_config_sha256(legacy_config) != expected_config_hash:
                raise ValueError(
                    f"legacy run generation config differs from current config: {call.call_id}"
                )
            provenance = "legacy_run_attestation"
        updated.append(
            call.model_copy(
                update={
                    "prompt_record_sha256": generation_prompt_record_sha256(prompt),
                    "generation_config_sha256": expected_config_hash,
                    "request_identity_sha256": expected_identity,
                    "request_identity_provenance": provenance,
                }
            )
        )

    validate_generation_call_identities(updated, prompts, config)
    successful = unique_successful_generation_calls_by_cell(
        updated, include_qualification_bypass=True
    )
    expected_cells = _expected_cells(prompts, config)
    missing = expected_cells - set(successful)
    if missing:
        raise ValueError(f"generation manifest has {len(missing)} unresolved frozen cells")
    output_evidence = [_verify_output(call, root) for call in updated if call.status == "succeeded"]
    output_contract = _output_contract_summary(output_evidence, config)
    run_evidence = []
    for run_id in sorted({call.run_id for call in updated}):
        run = run_records[run_id]
        run_path = run_record_paths[run_id]
        disk_run = RunRecord.model_validate(read_json(run_path))
        if disk_run != run:
            raise ValueError(f"originating run record changed on disk: {run_id}")
        originating_qualification = _originating_qualification_evidence(
            run, qualification_context, root
        )
        run_evidence.append(
            {
                "run_id": run_id,
                "command": run.command,
                "run_status": run.status,
                "run_record_path": _display_path(run_path, root),
                "run_record_sha256": hash_file(run_path),
                "implementation_sha256": run.implementation_sha256,
                "resolved_config_sha256": run.resolved_config_sha256,
                "originating_qualification": originating_qualification,
            }
        )

    (
        originating_qualification_proven,
        legacy_disposition,
        scientific_eligibility,
    ) = _scientific_use_evidence(
        updated, config, qualification_context, run_evidence, output_contract
    )

    evidence: Dict[str, Any] = {
        "schema_version": "2.0",
        "status": "verified",
        "attestation_scope": (
            "request-contract reconstruction, output-file integrity, current "
            "qualification context, and legacy scientific-use disposition"
        ),
        "legacy_attestation_limitation": (
            "Legacy identities are reconstructed from the originating run record, exact "
            "prompt-manifest input hash, resolved generation config, and call fields; they "
            "are not contemporaneous wire-body captures."
        ),
        "prompt_manifest": _display_path(prompt_manifest, root),
        "prompt_manifest_sha256": hash_file(prompt_manifest),
        "generation_config_sha256": expected_config_hash,
        "attempt_record_count": len(updated),
        "native_pre_request_count": native_count,
        "legacy_run_attestation_count": legacy_count,
        "unique_request_identity_count": len({call.request_identity_sha256 for call in updated}),
        "expected_frozen_cell_count": len(expected_cells),
        "resolved_frozen_cell_count": len(successful),
        "successful_output_count": len(output_evidence),
        **output_contract,
        "current_qualification_context": qualification_context,
        "originating_qualification_proven": originating_qualification_proven,
        "legacy_retention_disposition": legacy_disposition,
        "scientific_eligibility": scientific_eligibility,
        "run_evidence": run_evidence,
        "output_evidence": output_evidence,
        "output_evidence_sha256": stable_hash(output_evidence),
        "attested_manifest_sha256": None,
    }
    return updated, evidence


def verify_generation_attestation(
    generation_manifest: Path,
    attestation_path: Path,
    prompt_manifest: Path,
    calls: Sequence[GenerationCallRecord],
    prompts: Sequence[PromptRecord],
    config: GenerationConfig,
    *,
    root: Optional[Path] = None,
    qualification_card_paths: Optional[Mapping[str, Path]] = None,
    qualification_contract_hashes: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Re-verify the sidecar, current inputs, and every successful output on disk."""

    resolved_root = (root or Path.cwd()).resolve()
    evidence = read_json(attestation_path)
    if (
        not isinstance(evidence, dict)
        or evidence.get("schema_version") != "2.0"
        or evidence.get("status") != "verified"
    ):
        raise ValueError("generation manifest attestation is absent or not verified")
    qualification_context = _qualification_context(
        qualification_card_paths, qualification_contract_hashes, resolved_root
    )
    output_evidence = [
        _verify_output(call, resolved_root) for call in calls if call.status == "succeeded"
    ]
    output_contract = _output_contract_summary(output_evidence, config)
    successful = unique_successful_generation_calls_by_cell(
        calls, include_qualification_bypass=True
    )
    expected_cells = _expected_cells(prompts, config)
    missing = expected_cells - set(successful)
    if missing:
        raise ValueError(f"generation manifest has {len(missing)} unresolved frozen cells")
    stored_run_evidence = evidence.get("run_evidence")
    if not isinstance(stored_run_evidence, list):
        raise ValueError("generation attestation lacks originating run evidence")
    expected_run_ids = {call.run_id for call in calls}
    observed_run_ids = {row.get("run_id") for row in stored_run_evidence if isinstance(row, dict)}
    if observed_run_ids != expected_run_ids:
        raise ValueError("generation attestation run set does not match the manifest")
    verified_run_evidence = []
    for stored_row in stored_run_evidence:
        if not isinstance(stored_row, dict):
            raise ValueError("generation attestation has invalid run evidence")
        run_path_value = stored_row.get("run_record_path")
        if not isinstance(run_path_value, str):
            raise ValueError("generation attestation run evidence lacks a path")
        run_path = _resolve(resolved_root, run_path_value).resolve()
        if not run_path.is_file():
            raise FileNotFoundError(f"missing originating run record: {run_path}")
        run = RunRecord.model_validate(read_json(run_path))
        originating_qualification = _originating_qualification_evidence(
            run, qualification_context, resolved_root
        )
        verified_row = {
            "run_id": run.run_id,
            "command": run.command,
            "run_status": run.status,
            "run_record_path": _display_path(run_path, resolved_root),
            "run_record_sha256": hash_file(run_path),
            "implementation_sha256": run.implementation_sha256,
            "resolved_config_sha256": run.resolved_config_sha256,
            "originating_qualification": originating_qualification,
        }
        if stored_row != verified_row:
            raise ValueError(f"generation attestation run evidence is stale for {run.run_id}")
        verified_run_evidence.append(verified_row)
    (
        originating_qualification_proven,
        legacy_disposition,
        scientific_eligibility,
    ) = _scientific_use_evidence(
        calls, config, qualification_context, verified_run_evidence, output_contract
    )
    expected = {
        "attested_manifest_sha256": hash_file(generation_manifest),
        "prompt_manifest_sha256": hash_file(prompt_manifest),
        "generation_config_sha256": generation_config_sha256(config),
        "attempt_record_count": len(calls),
        "native_pre_request_count": sum(
            call.request_identity_provenance == "native_pre_request" for call in calls
        ),
        "legacy_run_attestation_count": sum(
            call.request_identity_provenance == "legacy_run_attestation" for call in calls
        ),
        "unique_request_identity_count": len({call.request_identity_sha256 for call in calls}),
        "expected_frozen_cell_count": len(expected_cells),
        "resolved_frozen_cell_count": len(successful),
        "successful_output_count": len(output_evidence),
        "output_evidence": output_evidence,
        "output_evidence_sha256": stable_hash(output_evidence),
        "current_qualification_context": qualification_context,
        "originating_qualification_proven": originating_qualification_proven,
        "legacy_retention_disposition": legacy_disposition,
        "scientific_eligibility": scientific_eligibility,
        "run_evidence": verified_run_evidence,
        **output_contract,
    }
    mismatches = [name for name, value in expected.items() if evidence.get(name) != value]
    if mismatches:
        raise ValueError(
            "generation attestation does not bind current inputs: " + ", ".join(sorted(mismatches))
        )
    validate_generation_call_identities(calls, prompts, config)
    return evidence
