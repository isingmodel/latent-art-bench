from pathlib import Path

import pytest
from PIL import Image

from latent_art_bench.generation.attestation import (
    attest_generation_calls,
    validate_generation_call_identities,
    verify_generation_attestation,
)
from latent_art_bench.generation.openai_images import plan_generation_calls
from latent_art_bench.io import hash_file, write_json, write_jsonl
from latent_art_bench.schemas import PromptRecord, RunRecord


def _write_qualification_context(
    root: Path,
) -> tuple[dict[str, Path], dict[str, str], dict[str, Path]]:
    card_paths: dict[str, Path] = {}
    contract_hashes: dict[str, str] = {}
    evidence_paths: dict[str, Path] = {}
    for index, measurement in enumerate(("chromatic", "learned_formal"), start=1):
        contract_hash = str(index) * 64
        evidence_path = root / f"{measurement}-evidence.json"
        write_json(evidence_path, {"measurement": measurement, "result": "test"})
        card_path = root / f"{measurement}-card.json"
        write_json(
            card_path,
            {
                "measurement": measurement,
                "status": "pass",
                "qualification_contract_hash": contract_hash,
                "evidence_paths": [str(evidence_path.relative_to(root))],
            },
        )
        card_paths[measurement] = card_path
        contract_hashes[measurement] = contract_hash
        evidence_paths[measurement] = evidence_path
    return card_paths, contract_hashes, evidence_paths


def test_legacy_attestation_rewrites_and_binds_manifest(tmp_path: Path, pilot_config) -> None:
    config = pilot_config.generation.model_copy(update={"repetitions": 1})
    prompt = PromptRecord(
        prompt_id="prompt-1",
        content_id="content-1",
        template_id="template-1",
        prompt="A frozen test prompt",
        artist_free_control=True,
        test_only=True,
    )
    prompt_manifest = tmp_path / "prompts.jsonl"
    write_jsonl(prompt_manifest, [prompt])
    output = tmp_path / "output.png"
    Image.new("RGB", (3, 2), (1, 2, 3)).save(output)
    calls = plan_generation_calls(
        "legacy-run",
        [prompt],
        config.models,
        config,
        qualification_bypass=False,
    )
    calls = [
        call.model_copy(
            update={
                "status": "succeeded",
                "request_identity_provenance": None,
                "request_identity_sha256": None,
                "prompt_record_sha256": None,
                "generation_config_sha256": None,
                "output_path": str(output),
                "output_sha256": hash_file(output),
                "actual_width": 3,
                "actual_height": 2,
                "actual_format": "png",
            }
        )
        for call in calls
    ]
    resolved_config = pilot_config.model_dump(mode="json")
    resolved_config["generation"] = config.model_dump(mode="json", exclude_none=True)
    run = RunRecord(
        run_id="legacy-run",
        command="generate",
        arguments={"prompt_manifest": str(prompt_manifest)},
        status="complete",
        started_at=calls[0].started_at,
        resolved_config=resolved_config,
        input_hashes={str(prompt_manifest): hash_file(prompt_manifest)},
    )
    run_path = tmp_path / "legacy-run.json"
    write_json(run_path, run)
    card_paths, contract_hashes, evidence_paths = _write_qualification_context(tmp_path)

    updated, evidence = attest_generation_calls(
        calls,
        [prompt],
        config,
        prompt_manifest,
        {run.run_id: run},
        {run.run_id: run_path},
        tmp_path,
        qualification_card_paths=card_paths,
        qualification_contract_hashes=contract_hashes,
    )

    assert evidence["legacy_run_attestation_count"] == 2
    assert evidence["unique_request_identity_count"] == 2
    assert evidence["requested_size_match_count"] == 0
    assert evidence["requested_size_mismatch_count"] == 2
    assert evidence["requested_dimension_contract_status"] == "violated"
    assert all(
        row["dimension_contract_status"] == "mismatch" for row in evidence["output_evidence"]
    )
    assert evidence["current_qualification_context"]["all_cards_pass"] is True
    assert evidence["originating_qualification_proven"] is False
    disposition = evidence["legacy_retention_disposition"]
    assert disposition["disposition"] == "grandfathered_engineering_only"
    assert disposition["superseded_by_current_qualification_context"] is True
    assert disposition["scientifically_eligible"] is False
    assert evidence["scientific_eligibility"]["eligible"] is False
    assert evidence["scientific_eligibility"]["permitted_use"] == "engineering_only"
    assert all(call.request_identity_provenance == "legacy_run_attestation" for call in updated)
    validate_generation_call_identities(updated, [prompt], config)

    manifest = tmp_path / "calls.jsonl"
    attestation = tmp_path / "attestation.json"
    write_jsonl(manifest, updated)
    evidence["attested_manifest_sha256"] = hash_file(manifest)
    write_json(attestation, evidence)
    verified = verify_generation_attestation(
        manifest,
        attestation,
        prompt_manifest,
        updated,
        [prompt],
        config,
        root=tmp_path,
        qualification_card_paths=card_paths,
        qualification_contract_hashes=contract_hashes,
    )
    assert verified["status"] == "verified"

    write_json(
        evidence_paths["chromatic"],
        {"measurement": "chromatic", "result": "changed-after-attestation"},
    )
    with pytest.raises(ValueError, match="stale|current inputs"):
        verify_generation_attestation(
            manifest,
            attestation,
            prompt_manifest,
            updated,
            [prompt],
            config,
            root=tmp_path,
            qualification_card_paths=card_paths,
            qualification_contract_hashes=contract_hashes,
        )


def test_identity_validation_rejects_a_changed_prompt(pilot_config) -> None:
    config = pilot_config.generation.model_copy(update={"repetitions": 1})
    prompt = PromptRecord(
        prompt_id="prompt-1",
        content_id="content-1",
        template_id="template-1",
        prompt="Original",
        artist_free_control=True,
        test_only=True,
    )
    calls = plan_generation_calls(
        "run", [prompt], config.models, config, qualification_bypass=False
    )
    changed = prompt.model_copy(update={"prompt": "Changed"})

    try:
        validate_generation_call_identities(calls, [changed], config)
    except ValueError as exc:
        assert "identity mismatch" in str(exc)
    else:  # pragma: no cover - makes the failure message direct
        raise AssertionError("changed prompt unexpectedly retained its request identity")


def test_exact_pass_context_is_proven_but_test_config_remains_engineering_only(
    tmp_path: Path, pilot_config
) -> None:
    config = pilot_config.generation.model_copy(update={"repetitions": 1})
    prompt = PromptRecord(
        prompt_id="prompt-1",
        content_id="content-1",
        template_id="template-1",
        prompt="A frozen test prompt",
        artist_free_control=True,
        test_only=True,
    )
    prompt_manifest = tmp_path / "prompts.jsonl"
    write_jsonl(prompt_manifest, [prompt])
    output = tmp_path / "output.png"
    Image.new("RGB", (1024, 1024), (1, 2, 3)).save(output)
    calls = [
        call.model_copy(
            update={
                "status": "succeeded",
                "output_path": str(output),
                "output_sha256": hash_file(output),
                "actual_width": 1024,
                "actual_height": 1024,
                "actual_format": "png",
            }
        )
        for call in plan_generation_calls(
            "native-pass-run",
            [prompt],
            config.models,
            config,
            qualification_bypass=False,
        )
    ]
    card_paths, contract_hashes, evidence_paths = _write_qualification_context(tmp_path)
    input_paths = [prompt_manifest, *card_paths.values(), *evidence_paths.values()]
    resolved_config = pilot_config.model_dump(mode="json")
    resolved_config["generation"] = config.model_dump(mode="json", exclude_none=True)
    run = RunRecord(
        run_id="native-pass-run",
        command="generate",
        arguments={"prompt_manifest": str(prompt_manifest)},
        status="complete",
        started_at=calls[0].started_at,
        resolved_config=resolved_config,
        input_hashes={str(path): hash_file(path) for path in input_paths},
    )
    run_path = tmp_path / "native-pass-run.json"
    write_json(run_path, run)

    _, attestation = attest_generation_calls(
        calls,
        [prompt],
        config,
        prompt_manifest,
        {run.run_id: run},
        {run.run_id: run_path},
        tmp_path,
        qualification_card_paths=card_paths,
        qualification_contract_hashes=contract_hashes,
    )

    assert attestation["originating_qualification_proven"] is True
    assert attestation["requested_dimension_contract_status"] == "satisfied"
    assert attestation["scientific_eligibility"] == {
        "eligible": False,
        "permitted_use": "engineering_only",
        "reasons": [
            "generation config is test-only and explicitly disables scientific claims"
        ],
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("endpoint", "http://127.0.0.1:9999/v1/images/generations"),
        ("requested_size", "1536x1024"),
        ("requested_quality", "high"),
        ("requested_output_format", "jpeg"),
    ],
)
def test_identity_validation_rejects_redundant_request_field_changes(
    pilot_config, field: str, value: str
) -> None:
    config = pilot_config.generation.model_copy(update={"repetitions": 1})
    prompt = PromptRecord(
        prompt_id="prompt-1",
        content_id="content-1",
        template_id="template-1",
        prompt="Frozen",
        artist_free_control=True,
        test_only=True,
    )
    calls = plan_generation_calls(
        "run", [prompt], config.models, config, qualification_bypass=False
    )
    changed = [calls[0].model_copy(update={field: value}), *calls[1:]]

    with pytest.raises(ValueError, match=field):
        validate_generation_call_identities(changed, [prompt], config)


@pytest.mark.parametrize("qualification_bypass", [False, True])
def test_verification_rehashes_successful_outputs(
    tmp_path: Path, pilot_config, qualification_bypass: bool
) -> None:
    config = pilot_config.generation.model_copy(update={"repetitions": 1})
    prompt = PromptRecord(
        prompt_id="prompt-1",
        content_id="content-1",
        template_id="template-1",
        prompt="Frozen",
        artist_free_control=True,
        test_only=True,
    )
    prompt_manifest = tmp_path / "prompts.jsonl"
    write_jsonl(prompt_manifest, [prompt])
    output = tmp_path / "output.png"
    Image.new("RGB", (3, 2), (1, 2, 3)).save(output)
    calls = [
        call.model_copy(
            update={
                "status": "succeeded",
                "output_path": str(output),
                "output_sha256": hash_file(output),
                "actual_width": 3,
                "actual_height": 2,
                "actual_format": "png",
            }
        )
        for call in plan_generation_calls(
            "native-run",
            [prompt],
            config.models,
            config,
            qualification_bypass=qualification_bypass,
        )
    ]
    resolved_config = pilot_config.model_dump(mode="json")
    resolved_config["generation"] = config.model_dump(mode="json", exclude_none=True)
    run = RunRecord(
        run_id="native-run",
        command="generate",
        arguments={"prompt_manifest": str(prompt_manifest)},
        status="complete",
        started_at=calls[0].started_at,
        resolved_config=resolved_config,
        input_hashes={str(prompt_manifest): hash_file(prompt_manifest)},
    )
    run_path = tmp_path / "native-run.json"
    write_json(run_path, run)
    updated, evidence = attest_generation_calls(
        calls,
        [prompt],
        config,
        prompt_manifest,
        {run.run_id: run},
        {run.run_id: run_path},
        tmp_path,
    )
    manifest = tmp_path / "calls.jsonl"
    attestation = tmp_path / "attestation.json"
    write_jsonl(manifest, updated)
    evidence["attested_manifest_sha256"] = hash_file(manifest)
    write_json(attestation, evidence)
    bypass_reasons = [
        reason
        for reason in evidence["scientific_eligibility"]["reasons"]
        if "unqualified test bypass" in reason
    ]
    assert bool(bypass_reasons) is qualification_bypass
    verified = verify_generation_attestation(
        manifest,
        attestation,
        prompt_manifest,
        updated,
        [prompt],
        config,
        root=tmp_path,
    )
    assert verified["scientific_eligibility"]["eligible"] is False

    Image.new("RGB", (3, 2), (9, 8, 7)).save(output)
    with pytest.raises(ValueError, match="output hash mismatch"):
        verify_generation_attestation(
            manifest,
            attestation,
            prompt_manifest,
            updated,
            [prompt],
            config,
            root=tmp_path,
        )
