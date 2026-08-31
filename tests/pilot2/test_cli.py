from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from latent_art_bench.cli import app as root_app
from latent_art_bench.features.learned_formal import learned_formal_vector_sha256
from latent_art_bench.io import hash_file, stable_hash, write_json
from latent_art_bench.pilot2.cli import (
    GeneratedLearnedFeature,
    _bind_attempt_and_terminal_manifests,
    _expected_extraction_metadata,
    _make_generated_feature,
    _preprocessing_config_sha256,
    _require_exact_primary_result,
    _validate_attempt_and_terminal_manifests,
    _validate_derived_preprocessing,
    _validate_embedded_schedule,
    _validate_execution_envelope,
    _validate_generated_extraction_provenance,
    app,
)
from latent_art_bench.pilot2.config import Pilot2Config
from latent_art_bench.pilot2.generation import (
    AppendOnlyAttemptLedger,
    AppendOnlyRuntimeRevalidationLedger,
    GenerationRuntimeRevalidationRecord,
    build_generation_cells,
    build_generation_schedule,
    generation_attempt_ledger_semantic_sha256,
    generation_grid_sha256,
    runtime_revalidation_ledger_semantic_sha256,
    verified_attempt_receipt_manifest,
    verify_successful_output_artifacts,
)
from latent_art_bench.pilot2.schemas import Pilot2DerivedInput
from latent_art_bench.pilot2.transport import OAuthRuntimeRevalidation
from latent_art_bench.schemas import PromptRecord


def _target_prompt() -> PromptRecord:
    return PromptRecord(
        prompt_id="fixture-monet",
        content_id="fixture-content",
        template_id="fixture-template",
        prompt="An original outdoor oil painting associated with Claude Monet.",
        target_artist_id="claude_monet",
        target_artist_name="Claude Monet",
    )


def _derived() -> Pilot2DerivedInput:
    source_sha = "1" * 64
    output_sha = "2" * 64
    preprocessing_sha = "3" * 64
    identity = stable_hash(
        {
            "source_record_id": "fixture-cell",
            "source_sha256": source_sha,
            "output_sha256": output_sha,
            "preprocessing_config_sha256": preprocessing_sha,
        }
    )
    return Pilot2DerivedInput(
        derived_input_id=f"pilot2-input-{identity[:24]}",
        source_record_id="fixture-cell",
        source_path="source.png",
        source_sha256=source_sha,
        output_path="common.png",
        output_sha256=output_sha,
        preprocessing_config_sha256=preprocessing_sha,
        source_width=512,
        source_height=512,
        source_decoded_format="png",
        width=512,
        height=512,
    )


def _bound_derived(config: Pilot2Config, source_record_id: str) -> Pilot2DerivedInput:
    original = _derived().model_dump(mode="json")
    original["source_record_id"] = source_record_id
    original["preprocessing_config_sha256"] = _preprocessing_config_sha256(config)
    identity = stable_hash(
        {
            "source_record_id": original["source_record_id"],
            "source_sha256": original["source_sha256"],
            "output_sha256": original["output_sha256"],
            "preprocessing_config_sha256": original["preprocessing_config_sha256"],
        }
    )
    original["derived_input_id"] = f"pilot2-input-{identity[:24]}"
    return Pilot2DerivedInput.model_validate(original)


def test_pilot2_subcli_is_mounted_on_root_cli() -> None:
    result = CliRunner().invoke(root_app, ["pilot2", "--help"])
    assert result.exit_code == 0, result.output
    assert "validate-manifests" in result.output
    assert "prepare-generated" in result.output
    assert "verify" in result.output


@pytest.mark.parametrize("command", ["conform", "generate"])
def test_network_commands_require_explicit_execute_before_loading_config(
    command: str, tmp_path: Path
) -> None:
    result = CliRunner().invoke(app, [command, "--root", str(tmp_path)])
    assert result.exit_code != 0
    assert "--execute" in result.output
    assert not list(tmp_path.iterdir())


def test_generated_feature_is_content_bound_and_rejects_tampering() -> None:
    config = Pilot2Config()
    cell = build_generation_cells([_target_prompt()], repetitions=1)[0]
    derived = _derived()
    vector = [float(index) / 10.0 for index in range(32)]
    row = _make_generated_feature(
        cell,
        "4" * 64,
        derived,
        vector,
        {"common_derived_png_sha256": derived.output_sha256},
        config,
    )

    assert row.requested_model_label == "gpt-image-1"
    assert row.generation_cell_identity_sha256 == cell.cell_identity_sha256
    assert row.derived_png_sha256 == derived.output_sha256

    tampered = row.model_dump(mode="json")
    tampered["source_output_sha256"] = "5" * 64
    with pytest.raises(ValidationError, match="feature id"):
        GeneratedLearnedFeature.model_validate(tampered)


def test_derived_loader_rejects_non_frozen_preprocessing_digest() -> None:
    config = Pilot2Config()
    valid = _bound_derived(config, "fixture-cell")
    _validate_derived_preprocessing([valid], config, label="fixture")

    stale = valid.model_copy(update={"preprocessing_config_sha256": "9" * 64})
    with pytest.raises(ValueError, match="non-frozen preprocessing config"):
        _validate_derived_preprocessing([stale], config, label="fixture")


def test_generated_extraction_metadata_is_bound_to_frozen_pipeline() -> None:
    config = Pilot2Config()
    cell = build_generation_cells([_target_prompt()], repetitions=1)[0]
    derived = _bound_derived(config, cell.cell_id)
    vector = [0.0] * config.learned_formal.raw_dimension
    seed_basis = "6" * 64
    seed_digest = hashlib.sha256()
    seed_digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
    seed_digest.update(config.learned_formal.base_seed.to_bytes(8, "big"))
    seed_digest.update(bytes.fromhex(seed_basis))
    seed = int.from_bytes(seed_digest.digest()[:8], "big") & ((1 << 63) - 1)
    metadata = {
        **_expected_extraction_metadata(config, derived),
        "seed_basis_sha256": seed_basis,
        "intermediate_payload_sha256": "7" * 64,
        "seed": seed,
        "vector_sha256": learned_formal_vector_sha256(vector),
    }
    feature = _make_generated_feature(
        cell,
        derived.source_sha256,
        derived,
        vector,
        metadata,
        config,
    )
    _validate_generated_extraction_provenance(feature, derived, config)

    tampered = _make_generated_feature(
        cell,
        derived.source_sha256,
        derived,
        vector,
        {**metadata, "common_preprocessing_config_sha256": "8" * 64},
        config,
    )
    with pytest.raises(ValueError, match="common_preprocessing_config_sha256"):
        _validate_generated_extraction_provenance(tampered, derived, config)


def test_execution_schedule_envelope_rejects_schedule_and_parallelism_tampering() -> None:
    prompts = [
        PromptRecord(
            prompt_id=f"prompt-{content}-{target or 'control'}",
            content_id=f"content-{content}",
            template_id="fixture-template",
            prompt=f"Fixture content {content} target {target or 'control'}.",
            target_artist_id=target,
            target_artist_name=(None if target is None else target.replace("_", " ")),
            artist_free_control=target is None,
        )
        for content in range(8)
        for target in [
            "alfred_sisley",
            "camille_pissarro",
            "claude_monet",
            "paul_cezanne",
            None,
        ]
    ]
    schedule = build_generation_schedule(build_generation_cells(prompts, repetitions=4))
    completion = {
        "max_parallel": 4,
        "generation_schedule_sha256": schedule.schedule_sha256,
        "generation_schedule": schedule.model_dump(mode="json"),
    }
    _validate_embedded_schedule(completion, schedule, expected_max_parallel=4)

    wrong_parallel = {**completion, "max_parallel": 3}
    with pytest.raises(RuntimeError, match="parallelism"):
        _validate_embedded_schedule(wrong_parallel, schedule, expected_max_parallel=4)
    wrong_schedule = {
        **completion,
        "generation_schedule": {
            **completion["generation_schedule"],
            "seed": 1,
        },
    }
    with pytest.raises(RuntimeError, match="different generation schedule"):
        _validate_embedded_schedule(wrong_schedule, schedule, expected_max_parallel=4)


class _DumpFixture:
    def __init__(self, value: int) -> None:
        self.value = value

    def model_dump(self, *, mode: str) -> dict[str, int]:
        assert mode == "json"
        return {"value": self.value}


def test_report_primary_guard_requires_exact_recomputation() -> None:
    _require_exact_primary_result(_DumpFixture(1), _DumpFixture(1))  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="primary analysis is stale"):
        _require_exact_primary_result(  # type: ignore[arg-type]
            _DumpFixture(1), _DumpFixture(2)
        )


def test_completion_binds_ledger_terminal_and_successful_output_files(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "attempts.jsonl"
    terminal_path = tmp_path / "terminal.jsonl"
    receipt_path = tmp_path / "receipts.json"
    successful_path = tmp_path / "successful.json"
    ledger_path.write_text("", encoding="utf-8")
    terminal_path.write_text("", encoding="utf-8")
    receipts = verified_attempt_receipt_manifest(AppendOnlyAttemptLedger(ledger_path), [])
    write_json(receipt_path, receipts)
    successful = verify_successful_output_artifacts([], [])
    write_json(successful_path, successful)
    base = {
        "attempt_ledger_semantic_sha256": (generation_attempt_ledger_semantic_sha256([])),
        "attempt_receipt_count": 0,
        "attempt_receipt_manifest_sha256": receipts["attempt_receipt_manifest_sha256"],
        "successful_output_count": 0,
        "successful_output_manifest_sha256": successful["successful_output_manifest_sha256"],
    }
    report = {**base, "report_sha256": stable_hash(base)}
    bound = _bind_attempt_and_terminal_manifests(
        report,
        ledger_path=ledger_path,
        attempts=[],
        terminal_path=terminal_path,
        terminal_records=[],
        attempt_receipt_path=receipt_path,
        attempt_receipt_manifest=receipts,
        successful_output_path=successful_path,
        successful_output_manifest=successful,
    )
    _validate_attempt_and_terminal_manifests(
        bound,
        ledger_path=ledger_path,
        attempts=[],
        terminal_path=terminal_path,
        terminal_records=[],
        attempt_receipt_path=receipt_path,
        attempt_receipt_manifest=receipts,
        successful_output_path=successful_path,
        successful_output_manifest=successful,
    )

    receipt_path.write_text(receipt_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="attempt-receipt file"):
        _validate_attempt_and_terminal_manifests(
            bound,
            ledger_path=ledger_path,
            attempts=[],
            terminal_path=terminal_path,
            terminal_records=[],
            attempt_receipt_path=receipt_path,
            attempt_receipt_manifest=receipts,
            successful_output_path=successful_path,
            successful_output_manifest=successful,
        )
    write_json(receipt_path, receipts)

    ledger_path.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="attempt-ledger file"):
        _validate_attempt_and_terminal_manifests(
            bound,
            ledger_path=ledger_path,
            attempts=[],
            terminal_path=terminal_path,
            terminal_records=[],
            attempt_receipt_path=receipt_path,
            attempt_receipt_manifest=receipts,
            successful_output_path=successful_path,
            successful_output_manifest=successful,
        )

    ledger_path.write_text("", encoding="utf-8")
    successful_path.write_text(successful_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="successful-output file"):
        _validate_attempt_and_terminal_manifests(
            bound,
            ledger_path=ledger_path,
            attempts=[],
            terminal_path=terminal_path,
            terminal_records=[],
            attempt_receipt_path=receipt_path,
            attempt_receipt_manifest=receipts,
            successful_output_path=successful_path,
            successful_output_manifest=successful,
        )


def test_completion_rejects_broken_pre_file_binding_chain(tmp_path: Path) -> None:
    ledger_path = tmp_path / "attempts.jsonl"
    terminal_path = tmp_path / "terminal.jsonl"
    receipt_path = tmp_path / "receipts.json"
    successful_path = tmp_path / "successful.json"
    ledger_path.write_text("", encoding="utf-8")
    terminal_path.write_text("", encoding="utf-8")
    receipts = verified_attempt_receipt_manifest(AppendOnlyAttemptLedger(ledger_path), [])
    write_json(receipt_path, receipts)
    successful = verify_successful_output_artifacts([], [])
    write_json(successful_path, successful)
    base = {
        "attempt_ledger_semantic_sha256": (generation_attempt_ledger_semantic_sha256([])),
        "attempt_receipt_count": 0,
        "attempt_receipt_manifest_sha256": receipts["attempt_receipt_manifest_sha256"],
        "successful_output_count": 0,
        "successful_output_manifest_sha256": successful["successful_output_manifest_sha256"],
    }
    bound = _bind_attempt_and_terminal_manifests(
        {**base, "report_sha256": stable_hash(base)},
        ledger_path=ledger_path,
        attempts=[],
        terminal_path=terminal_path,
        terminal_records=[],
        attempt_receipt_path=receipt_path,
        attempt_receipt_manifest=receipts,
        successful_output_path=successful_path,
        successful_output_manifest=successful,
    )
    tampered = {
        **bound,
        "completion_without_file_manifest_bindings_sha256": "0" * 64,
    }
    tampered["report_sha256"] = stable_hash(
        {key: value for key, value in tampered.items() if key != "report_sha256"}
    )
    with pytest.raises(RuntimeError, match="pre-file evidence chain"):
        _validate_attempt_and_terminal_manifests(
            tampered,
            ledger_path=ledger_path,
            attempts=[],
            terminal_path=terminal_path,
            terminal_records=[],
            attempt_receipt_path=receipt_path,
            attempt_receipt_manifest=receipts,
            successful_output_path=successful_path,
            successful_output_manifest=successful,
        )


def test_execution_envelope_binds_conformance_and_runtime_fingerprint(
    tmp_path: Path,
) -> None:
    prompts = [
        PromptRecord(
            prompt_id=f"p-{block}-{target or 'control'}",
            content_id=f"c-{block}",
            template_id="fixture-template",
            prompt=f"Fixture {block} {target or 'control'}.",
            target_artist_id=target,
            target_artist_name=target,
            artist_free_control=target is None,
        )
        for block in range(8)
        for target in ["a", "b", "c", "d", None]
    ]
    cells = build_generation_cells(prompts, repetitions=4)
    schedule = build_generation_schedule(cells)
    fingerprint_sha = "a" * 64
    source_sha = "b" * 64
    endpoint = "http://127.0.0.1:10532/v1/images/generations"
    fingerprint = SimpleNamespace(
        fingerprint_sha256=fingerprint_sha,
        endpoint_url=endpoint,
        process=SimpleNamespace(pid=123, cwd="/tmp/openai-oauth"),
        source=SimpleNamespace(source_snapshot_sha256=source_sha),
    )

    def revalidation(bound_fingerprint: str) -> OAuthRuntimeRevalidation:
        payload = {
            "schema_version": "pilot2-oauth-runtime-revalidation-v1",
            "checked_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "status": "pass",
            "persisted_fingerprint_sha256": bound_fingerprint,
            "endpoint_url": endpoint,
            "current_listener_pid": 123,
            "current_process_cwd": "/tmp/openai-oauth",
            "current_source_snapshot_sha256": source_sha,
            "current_health_response_sha256": "c" * 64,
            "current_model_catalog_response_sha256": "d" * 64,
            "checks": {"fixture": True},
        }
        provisional = OAuthRuntimeRevalidation.model_construct(
            **payload, revalidation_sha256="0" * 64
        )
        normalized = provisional.model_dump(mode="json", exclude={"revalidation_sha256"})
        return OAuthRuntimeRevalidation.model_validate(
            {**payload, "revalidation_sha256": stable_hash(normalized)}
        )

    base_completion = {"cell_count": 320, "report_sha256": "e" * 64}
    base_conformance = {"status": "pass", "report_sha256": "f" * 64}
    current = revalidation(fingerprint_sha)

    def runtime_ledger(
        path: Path,
        evidence: OAuthRuntimeRevalidation,
        invocation_id: str,
    ) -> tuple[AppendOnlyRuntimeRevalidationLedger, list[dict[str, object]]]:
        envelope = [
            ("start_before_conformance", None),
            *[
                (
                    (
                        "after_conformance_before_batch"
                        if batch_rank == 1
                        else "batch_boundary_before_batch"
                    ),
                    batch_rank,
                )
                for batch_rank in range(1, schedule.batch_count + 1)
            ],
            ("end_after_all_batches", None),
        ]
        ledger = AppendOnlyRuntimeRevalidationLedger(path)
        for sequence, (phase, batch_rank) in enumerate(envelope, start=1):
            payload = {
                "record_type": "pilot2_generation_runtime_revalidation",
                "schema_version": "pilot2-generation-runtime-revalidation-v1",
                "record_id": f"runtime-{invocation_id}-{sequence}",
                "ledger_sequence": sequence,
                "invocation_id": invocation_id,
                "invocation_sequence": sequence,
                "phase": phase,
                "batch_rank": batch_rank,
                "generation_grid_sha256": generation_grid_sha256(cells),
                "generation_schedule_sha256": schedule.schedule_sha256,
                "attempt_ledger_row_count": 0,
                "attempt_ledger_semantic_sha256": (generation_attempt_ledger_semantic_sha256([])),
                "evidence": evidence.model_dump(mode="json"),
            }
            payload["runtime_revalidation_record_sha256"] = stable_hash(payload)
            ledger.append(GenerationRuntimeRevalidationRecord.model_validate(payload))
        return ledger, [row.model_dump(mode="json") for row in ledger.rows()]

    invocation_id = "fixture-current-invocation"
    runtime_path = tmp_path / "runtime.jsonl"
    runtime_journal, records = runtime_ledger(runtime_path, current, invocation_id)
    post_intent_path = tmp_path / "post-intents.jsonl"
    post_intent_path.write_text("", encoding="utf-8")
    completion = {
        "cell_count": 320,
        "completion_report_without_conformance_sha256": "e" * 64,
        "max_parallel": 4,
        "generation_schedule_sha256": schedule.schedule_sha256,
        "generation_schedule": schedule.model_dump(mode="json"),
        "transport_conformance": base_conformance,
        "post_intent_count": 0,
        "post_intent_ledger_semantic_sha256": stable_hash([]),
        "post_intent_ledger_file_sha256": hash_file(post_intent_path),
        "post_intent_ledger_path": str(post_intent_path),
        "oauth_runtime_revalidation": current.model_dump(mode="json"),
        "oauth_runtime_revalidation_sha256": current.revalidation_sha256,
        "oauth_runtime_revalidation_records": records,
        "oauth_runtime_revalidation_records_sha256": stable_hash(records),
        "oauth_runtime_revalidation_count": len(records),
        "oauth_runtime_revalidation_ledger_semantic_sha256": (
            runtime_revalidation_ledger_semantic_sha256(runtime_journal.rows())
        ),
        "oauth_runtime_revalidation_ledger_file_sha256": hash_file(runtime_path),
        "oauth_runtime_revalidation_ledger_path": str(runtime_path),
        "current_execution_invocation_id": invocation_id,
        "final_oauth_runtime_revalidation_sha256": current.revalidation_sha256,
    }
    observed = _validate_execution_envelope(
        completion,
        cells=cells,
        attempts=[],
        schedule=schedule,
        post_intent_ledger_path=post_intent_path,
        runtime_ledger_path=runtime_path,
        base_completion=base_completion,
        base_conformance=base_conformance,
        fingerprint=fingerprint,  # type: ignore[arg-type]
        expected_max_parallel=4,
    )
    assert observed == current

    post_intent_path.write_text("\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="post-intent ledger is stale"):
        _validate_execution_envelope(
            completion,
            cells=cells,
            attempts=[],
            schedule=schedule,
            post_intent_ledger_path=post_intent_path,
            runtime_ledger_path=runtime_path,
            base_completion=base_completion,
            base_conformance=base_conformance,
            fingerprint=fingerprint,  # type: ignore[arg-type]
            expected_max_parallel=4,
        )
    post_intent_path.write_text("", encoding="utf-8")

    stale = revalidation("0" * 64)
    stale_invocation_id = "fixture-stale-invocation"
    stale_path = tmp_path / "stale-runtime.jsonl"
    stale_journal, stale_records = runtime_ledger(stale_path, stale, stale_invocation_id)
    stale_completion = {
        **completion,
        "oauth_runtime_revalidation": stale.model_dump(mode="json"),
        "oauth_runtime_revalidation_sha256": stale.revalidation_sha256,
        "oauth_runtime_revalidation_records": stale_records,
        "oauth_runtime_revalidation_records_sha256": stable_hash(stale_records),
        "oauth_runtime_revalidation_ledger_semantic_sha256": (
            runtime_revalidation_ledger_semantic_sha256(stale_journal.rows())
        ),
        "oauth_runtime_revalidation_ledger_file_sha256": hash_file(stale_path),
        "oauth_runtime_revalidation_ledger_path": str(stale_path),
        "current_execution_invocation_id": stale_invocation_id,
        "final_oauth_runtime_revalidation_sha256": stale.revalidation_sha256,
    }
    with pytest.raises(RuntimeError, match="does not bind the fingerprint"):
        _validate_execution_envelope(
            stale_completion,
            cells=cells,
            attempts=[],
            schedule=schedule,
            post_intent_ledger_path=post_intent_path,
            runtime_ledger_path=stale_path,
            base_completion=base_completion,
            base_conformance=base_conformance,
            fingerprint=fingerprint,  # type: ignore[arg-type]
            expected_max_parallel=4,
        )
