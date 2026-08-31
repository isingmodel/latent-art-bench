from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image
from typer.testing import CliRunner

from latent_art_bench.cli import app as root_app
from latent_art_bench.io import hash_file, read_json, stable_hash, write_json, write_jsonl
from latent_art_bench.pilot3.execution import (
    FREEZE_B_CODE_CLOSURE,
    FREEZE_B_EVIDENCE_CLOSURE,
    FREEZE_B_OPERATIONAL_CLOSURE,
    GENERATION_AUTHORIZATION_CLOSED,
    GENERATION_AUTHORIZATION_OPEN,
    Pilot3ExecutionError,
    _generation_authorization_payload,
    _generation_terminal_category,
    _jsonl_file_sha256,
    _pilot2_preprocessing_from_phase_a,
    _preprocess_generated_output,
    _require_committed_closure,
    _rows_by_request,
    _verify_generation_gate_closure,
    _verify_preprocessing_row,
    _verify_seal,
    build_generation_authorization,
    build_generation_gate,
    verify_generation_authorization,
    write_generation_gate,
)
from latent_art_bench.pilot3.generation import GenerationAttempt
from latent_art_bench.pilot3.phasea import load_phase_a_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _attempt(
    *,
    retry_classification: str,
    failure_kind: str | None = None,
    request_label_accepted: bool = False,
) -> GenerationAttempt:
    return GenerationAttempt.model_construct(
        retry_classification=retry_classification,
        failure_kind=failure_kind,
        request_label_accepted=request_label_accepted,
    )


@pytest.mark.parametrize(
    ("disposition", "attempt", "expected"),
    [
        (
            "succeeded",
            _attempt(retry_classification="not_retryable_success"),
            "usable_image",
        ),
        (
            "refused",
            _attempt(retry_classification="not_retryable_refusal"),
            "policy_refusal",
        ),
        (
            "failed_after_retry_cap",
            _attempt(retry_classification="retryable_transport"),
            "retry_cap_technical_failure",
        ),
        (
            "terminal_failure",
            _attempt(
                retry_classification="not_retryable_indeterminate_after_interruption",
                failure_kind="indeterminate_after_interruption",
            ),
            "indeterminate_after_interruption",
        ),
        (
            "terminal_failure",
            _attempt(retry_classification="not_retryable_http_status"),
            "nonretryable_client_response",
        ),
        (
            "terminal_failure",
            _attempt(
                retry_classification="not_retryable_invalid_image",
                request_label_accepted=True,
            ),
            "malformed_or_ineligible_success",
        ),
    ],
)
def test_terminal_adapter_uses_only_registered_categories(
    disposition: str,
    attempt: GenerationAttempt,
    expected: str,
) -> None:
    assert _generation_terminal_category(disposition, attempt) == expected


def test_terminal_adapter_fails_closed_for_unregistered_transport_outcome() -> None:
    attempt = _attempt(
        retry_classification="not_retryable_transport",
        failure_kind="local_configuration_error",
    )
    with pytest.raises(Pilot3ExecutionError, match="no frozen scientific category"):
        _generation_terminal_category("terminal_failure", attempt)


def test_self_seal_and_jsonl_byte_hash_are_exact(tmp_path: Path) -> None:
    row = {"schema_version": "test", "request_id": "p3-test"}
    sealed = {**row, "record_sha256": stable_hash(row)}
    _verify_seal(sealed, field="record_sha256", label="test row")
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, [sealed])
    assert hash_file(path) == _jsonl_file_sha256([sealed])
    tampered = {**sealed, "request_id": "p3-other"}
    with pytest.raises(Pilot3ExecutionError, match="stale or invalid"):
        _verify_seal(tampered, field="record_sha256", label="test row")


def test_rows_by_request_rejects_duplicate_identity(tmp_path: Path) -> None:
    unsigned = {
        "schema_version": "pilot3-generated-preprocessing/1.0",
        "request_id": "duplicate",
    }
    row = {**unsigned, "record_sha256": stable_hash(unsigned)}
    path = tmp_path / "rows.jsonl"
    write_jsonl(path, [row, row])
    with pytest.raises(Pilot3ExecutionError, match="duplicated"):
        _rows_by_request(
            path,
            schema="pilot3-generated-preprocessing/1.0",
            label="rows",
        )


def test_generated_preprocessing_recomputes_exact_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (512, 512), (40, 80, 120)).save(source, format="PNG")
    output = {
        "output_path": source.as_posix(),
        "output_sha256": hash_file(source),
    }
    schedule = {
        "request_id": "p3-request",
        "sequence": 1,
        "schedule_row_sha256": "a" * 64,
    }
    config = read_json(REPOSITORY_ROOT / "configs/pilot_3/phase_a.json")
    row = _preprocess_generated_output(tmp_path, output, schedule, config)
    _verify_preprocessing_row(
        tmp_path,
        row,
        output=output,
        schedule_row=schedule,
        phase_a_config=config,
    )
    changed = dict(row)
    changed["source_width"] = 513
    unsigned = dict(changed)
    unsigned.pop("record_sha256")
    changed["record_sha256"] = stable_hash(unsigned)
    with pytest.raises(Pilot3ExecutionError, match="does not recompute exactly"):
        _verify_preprocessing_row(
            tmp_path,
            changed,
            output=output,
            schedule_row=schedule,
            phase_a_config=config,
        )


def test_generated_preprocessing_runtime_equals_frozen_phase_a_contract() -> None:
    config = load_phase_a_config(REPOSITORY_ROOT)
    runtime = _pilot2_preprocessing_from_phase_a(config)
    assert runtime.max_long_side == config["common_preprocessing"]["max_long_side"]
    mutated = {**config, "common_preprocessing": dict(config["common_preprocessing"])}
    mutated["common_preprocessing"]["max_long_side"] = 512
    with pytest.raises(Pilot3ExecutionError, match="does not equal"):
        _pilot2_preprocessing_from_phase_a(mutated)


def test_committed_clean_closure_rejects_dirty_and_untracked_files(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "pilot3@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Pilot 3 Test"], cwd=tmp_path, check=True
    )
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("frozen\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "freeze"], cwd=tmp_path, check=True)
    _require_committed_closure(tmp_path, [Path("tracked.txt")])
    tracked.write_text("changed\n", encoding="utf-8")
    with pytest.raises(Pilot3ExecutionError, match="not committed and clean"):
        _require_committed_closure(tmp_path, [Path("tracked.txt")])
    untracked = tmp_path / "untracked.txt"
    untracked.write_text("new\n", encoding="utf-8")
    with pytest.raises(Pilot3ExecutionError, match="not committed and clean"):
        _require_committed_closure(tmp_path, [Path("untracked.txt")])


def test_per_request_gate_detects_closure_mutation_before_next_post(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "pilot3@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Pilot 3 Test"], cwd=tmp_path, check=True
    )
    closure_path = tmp_path / "frozen.txt"
    closure_path.write_text("frozen\n", encoding="utf-8")
    authorization_path = tmp_path / "configs/pilot_3/generation_authorization.json"
    write_json(authorization_path, {"status": GENERATION_AUTHORIZATION_OPEN})
    authorization_hash = hash_file(authorization_path)
    gate_payload = {
        "record_type": "pilot3_generation_gate",
        "schema_version": "pilot3-generation-gate/1.0",
        "status": "open",
        "generation_authorized": True,
        "requested_model_labels": ["gpt-image-2"],
        "transport": "~/dev/openai-oauth",
        "direct_api_browser_or_fallback_allowed": False,
        "operational_generation_authorization": {
            "path": "configs/pilot_3/generation_authorization.json",
            "file_sha256": authorization_hash,
            "result_sha256": "a" * 64,
            "status": GENERATION_AUTHORIZATION_OPEN,
            "authorizes_analytic_generation_by_itself": False,
        },
        "closure_file_sha256": {
            "configs/pilot_3/generation_authorization.json": authorization_hash,
            "frozen.txt": hash_file(closure_path),
        },
    }
    gate = {**gate_payload, "result_sha256": stable_hash(gate_payload)}
    gate_path = tmp_path / "reports/pilot_3/evidence/generation_gate.json"
    write_json(gate_path, gate)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "freeze"], cwd=tmp_path, check=True)
    _verify_generation_gate_closure(
        tmp_path, expected_result_sha256=gate["result_sha256"]
    )
    closure_path.write_text("mutated\n", encoding="utf-8")
    with pytest.raises(Pilot3ExecutionError, match="changed during generation"):
        _verify_generation_gate_closure(
            tmp_path, expected_result_sha256=gate["result_sha256"]
        )


def test_generation_gate_cannot_be_opened_from_caller_assertions(tmp_path: Path) -> None:
    with pytest.raises(Pilot3ExecutionError, match="freeze bundle does not verify"):
        build_generation_gate(tmp_path)


def test_repository_generation_authorization_is_exact_and_initially_closed() -> None:
    authorization = verify_generation_authorization(REPOSITORY_ROOT)
    assert authorization["status"] == GENERATION_AUTHORIZATION_CLOSED
    assert authorization["generation_authorization_open"] is False
    assert authorization["eligible_for_p3_t14"] is False
    assert authorization["transition_proof"] is None
    assert authorization["authorizes_analytic_generation_by_itself"] is False


def test_open_authorization_binds_raw_p3_t07_and_one_shot_lineage(tmp_path: Path) -> None:
    protocol_path = tmp_path / "docs/PILOT_3_PROTOCOL.md"
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_text("immutable protocol\n", encoding="utf-8")
    protocol_hash = hash_file(protocol_path)
    p3_t07_path = tmp_path / "reports/pilot_3/evidence/a_vector_protocol.json"
    p3_t08_path = tmp_path / "reports/pilot_3/evidence/a_vector_external_validation.json"
    p3_t11_path = tmp_path / "reports/pilot_3/evidence/transport_qualification.json"
    p3_t07_path.parent.mkdir(parents=True)
    write_json(
        p3_t07_path,
        {
            "result_sha256": "a" * 64,
            "closure_file_sha256": {"docs/PILOT_3_PROTOCOL.md": protocol_hash},
        },
    )
    write_json(p3_t08_path, {"result_sha256": "b" * 64})
    write_json(
        p3_t11_path,
        {
            "report_sha256": "c" * 64,
            "intent_sha256": "d" * 64,
            "intent_ledger_file_sha256": "e" * 64,
            "attempt_sha256": "f" * 64,
            "attempt_ledger_file_sha256": "1" * 64,
            "analytic_generation_gate_status_at_authorization": "closed",
            "freeze_b_status_at_authorization": "not_frozen",
            "physical_post_count": 1,
            "retry_count": 0,
            "outside_artist_content_grid": True,
            "authorizes_analytic_generation_by_itself": False,
        },
    )
    prerequisites = {
        "p3_t11_neutral_output": {"file_sha256": "2" * 64},
    }
    authorization = _generation_authorization_payload(
        tmp_path,
        status=GENERATION_AUTHORIZATION_OPEN,
        prerequisites=prerequisites,
    )
    proof = authorization["transition_proof"]
    assert authorization["generation_authorization_open"] is True
    assert proof["immutable_scientific_protocol_file_sha256"] == protocol_hash
    assert proof["p3_t07_protocol_closure_file_sha256"] == protocol_hash
    assert proof["p3_t11_physical_post_count"] == 1
    assert proof["p3_t11_retry_count"] == 0
    assert proof["p3_t14_file_absent_when_transition_written"] is True

    protocol_path.write_text("mutated protocol\n", encoding="utf-8")
    with pytest.raises(Pilot3ExecutionError, match="does not raw-hash"):
        _generation_authorization_payload(
            tmp_path,
            status=GENERATION_AUTHORIZATION_OPEN,
            prerequisites=prerequisites,
        )

    protocol_path.write_text("immutable protocol\n", encoding="utf-8")
    qualification = read_json(p3_t11_path)
    assert isinstance(qualification, dict)
    qualification["retry_count"] = 1
    write_json(p3_t11_path, qualification)
    with pytest.raises(Pilot3ExecutionError, match="one-shot pre-Freeze-B lineage"):
        _generation_authorization_payload(
            tmp_path,
            status=GENERATION_AUTHORIZATION_OPEN,
            prerequisites=prerequisites,
        )


def test_closed_authorization_cannot_transition_after_p3_t14_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / "configs/pilot_3/generation_authorization.json",
        build_generation_authorization(tmp_path),
    )
    write_json(
        tmp_path / "reports/pilot_3/evidence/generation_gate.json",
        {"status": "unexpected_preexisting_gate"},
    )
    with pytest.raises(Pilot3ExecutionError, match="already exists"):
        write_generation_gate(tmp_path)


def test_freeze_b_closure_contains_scientific_code_tests_and_t11_evidence() -> None:
    code = {path.as_posix() for path in FREEZE_B_CODE_CLOSURE}
    evidence = {path.as_posix() for path in FREEZE_B_EVIDENCE_CLOSURE}
    operational = {path.as_posix() for path in FREEZE_B_OPERATIONAL_CLOSURE}
    assert {
        "configs/pilot_3/external_museum_blocks.json",
        "src/latent_art_bench/pilot3/execution.py",
        "src/latent_art_bench/pilot3/generation.py",
        "src/latent_art_bench/pilot3/qualification.py",
        "src/latent_art_bench/pilot3/analysis.py",
        "tests/pilot3/test_execution.py",
    }.issubset(code)
    assert {
        "reports/pilot_3/evidence/account_authorization.json",
        "reports/pilot_3/evidence/model_documentation.json",
        "reports/pilot_3/evidence/transport_qualification.json",
        "artifacts/pilot_3/external_unseal_receipt.json",
        "artifacts/pilot_3/transport_qualification_post_intents.jsonl",
        "artifacts/pilot_3/transport_qualification_attempts.jsonl",
        "artifacts/pilot_3/development_acquisition_http_attempts.jsonl",
        "artifacts/pilot_3/external_acquisition_http_attempts.jsonl",
    }.issubset(evidence)
    assert operational == {"configs/pilot_3/generation_authorization.json"}


def test_cli_exposes_only_offline_post_generation_steps() -> None:
    result = CliRunner().invoke(root_app, ["pilot3", "--help"])
    assert result.exit_code == 0
    for command in (
        "freeze-b-gate",
        "verify-b-gate",
        "finalize-generation",
        "measure-generated",
        "seal-terminals",
        "analyze",
        "finalize",
        "verify-complete",
    ):
        assert command in result.stdout
