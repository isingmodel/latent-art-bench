from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from latent_art_bench.io import read_json, read_jsonl, stable_hash, write_jsonl
from latent_art_bench.pilot3.design_freeze import (
    DEFAULT_CONFIG,
    EXPECTED_ARTIST_IDS,
    adapt_schedule_to_generation,
    assess_future_bindings,
    build_prompt_rows,
    build_schedule_rows,
    load_study_config,
    verify_phase_b_freeze_bundle,
    write_phase_b_freeze_bundle,
)
from latent_art_bench.pilot3.qualification import (
    TRANSPORT_QUALIFICATION_PROMPT_SHA256,
    TRANSPORT_QUALIFICATION_REQUEST_ID,
)

ROOT = Path(__file__).resolve().parents[2]


def _copy_bundle_inputs(tmp_path: Path) -> None:
    for relative in (
        DEFAULT_CONFIG,
        Path("reports/pilot_3/evidence/pilot2_baseline_recovery.json"),
        Path("reports/pilot_3/evidence/design_sensitivity.json"),
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def test_repository_phase_b_freeze_bundle_verifies_closed() -> None:
    result = verify_phase_b_freeze_bundle(ROOT)

    assert result["status"] == "verified_closed_pending_external_bindings"
    assert result["generation_authorized"] is False
    assert result["analysis_authorized"] is False
    assert result["prompt_count"] == 80
    assert result["schedule_count"] == 320
    assert result["named_control_pair_count"] == 256
    assert result["requested_labels"] == ["gpt-image-2"]
    assert result["transport"] == "~/dev/openai-oauth"


def test_design_is_exact_budget_maximizing_estimation_design() -> None:
    design = read_json(ROOT / "reports/pilot_3/evidence/phase_b_design.json")

    assert design["resolves_task_id"] == "P3-T04"
    assert design["design_decision"] == (
        "SELECTED_BUDGET_CONSTRAINED_ESTIMATION_DESIGN_NO_POWER_CLAIM"
    )
    proof = design["selection_proof"]
    assert proof["selected_content_blocks"] == 16
    assert proof["selected_request_count"] == 320
    assert proof["next_larger_design_request_count"] == 340
    assert design["claim_boundary"]["power_claim"] is False
    assert design["claim_boundary"]["artist_superpopulation_claim"] is False
    assert design["generation_authorized"] is False
    qualification = design["transport_qualification"]
    assert qualification["request_id"] == TRANSPORT_QUALIFICATION_REQUEST_ID
    assert qualification["neutral_prompt_sha256"] == TRANSPORT_QUALIFICATION_PROMPT_SHA256
    assert qualification["physical_post_budget"] == 1
    assert qualification["retry_allowed"] is False
    assert qualification["outside_artist_content_grid"] is True
    assert qualification["analytic_request_budget"] == 320
    assert design["expected_counts"]["nonanalytic_transport_qualification_requests"] == 1
    authorization = design["operational_authorization"]
    assert authorization["path"] == "configs/pilot_3/generation_authorization.json"
    assert authorization["initial_status"] == "closed"
    assert authorization["freeze_b_required_status"] == (
        "preregistered_generation_gate_open"
    )
    assert authorization["generation_authorized_by_record_alone"] is False


def test_prompts_are_concrete_and_only_artist_clause_differs() -> None:
    config = load_study_config(ROOT)
    prompts = build_prompt_rows(config)
    by_id = {row["prompt_id"]: row for row in prompts}

    assert len(prompts) == 80
    assert len({row["content_block_id"] for row in prompts}) == 16
    for block_rank in range(1, 17):
        control = by_id[f"p3-b{block_rank:02d}-control"]
        assert control["condition"] == "artist_free_control"
        assert len(control["content_annotations"]) >= 1
        for artist in config["artists"]:
            artist_id = artist["artist_id"].replace("_", "-")
            named = by_id[f"p3-b{block_rank:02d}-{artist_id}"]
            clause = f" in the artistic style of {artist['artist_name']}"
            assert named["prompt_text"].replace(clause, "", 1) == control["prompt_text"]
            assert named["pair_basis_sha256"] == control["pair_basis_sha256"]
            assert named["paired_control_prompt_id"] == control["prompt_id"]
            assert named["visual_selection_allowed"] is False


def test_schedule_has_one_shared_control_and_four_named_requests_per_cell() -> None:
    config = load_study_config(ROOT)
    prompts = build_prompt_rows(config)
    schedule = build_schedule_rows(config, prompts)

    assert len(schedule) == 320
    assert [row["sequence"] for row in schedule] == list(range(1, 321))
    assert schedule[0]["request_id"] == "p3-b16-r01-control"
    assert schedule[0]["request_id"] != TRANSPORT_QUALIFICATION_REQUEST_ID
    assert {row["requested_model_label"] for row in schedule} == {"gpt-image-2"}
    assert {row["transport"] for row in schedule} == {"~/dev/openai-oauth"}
    assert all(row["request_body"]["model"] == "gpt-image-2" for row in schedule)
    assert all("gpt-image-1" not in row["request_body"]["prompt"] for row in schedule)
    assert all(
        row["request_id"] != TRANSPORT_QUALIFICATION_REQUEST_ID for row in schedule
    )

    by_cell: dict[tuple[str, int], list[dict[str, object]]] = {}
    for row in schedule:
        key = (row["content_block_id"], row["repetition"])
        by_cell.setdefault(key, []).append(row)
    assert len(by_cell) == 64
    for rows in by_cell.values():
        controls = [row for row in rows if row["condition"] == "artist_free_control"]
        named = [row for row in rows if row["condition"] == "named_artist"]
        assert len(controls) == 1
        assert len(named) == 4
        assert {row["target_artist_id"] for row in named} == set(EXPECTED_ARTIST_IDS)
        assert {row["paired_control_request_id"] for row in named} == {controls[0]["request_id"]}


def test_generation_adapter_preserves_t12_bijection_and_canonical_order() -> None:
    config = load_study_config(ROOT)
    prompts = build_prompt_rows(config)
    schedule = build_schedule_rows(config, prompts)

    cells, generation_schedule = adapt_schedule_to_generation(config, prompts, schedule)

    assert len(cells) == len(schedule) == 320
    assert generation_schedule.ordering_basis == "t12_canonical_sequence"
    assert generation_schedule.entries[0].runtime_image_preflight_rank == 1
    assert [entry.scheduled_cell_rank for entry in generation_schedule.entries] == list(
        range(1, 321)
    )
    assert [cell.source_request_id for cell in cells] == [row["request_id"] for row in schedule]
    assert [cell.source_sequence for cell in cells] == list(range(1, 321))
    for row, cell, entry in zip(schedule, cells, generation_schedule.entries):
        assert cell.source_request_id == row["request_id"]
        assert cell.source_schedule_row_sha256 == row["schedule_row_sha256"]
        assert cell.source_prompt_row_sha256 == row["prompt_sha256"]
        assert cell.source_semantic_request_sha256 == row["semantic_request_sha256"]
        assert cell.source_repetition == row["repetition"]
        assert cell.repetition == row["repetition"] - 1
        assert cell.source_paired_control_request_id == row["paired_control_request_id"]
        assert cell.source_neighbor_artist_id == row["neighbor_artist_id"]
        assert entry.source_request_id == row["request_id"]
        assert entry.source_sequence == row["sequence"]
        assert entry.source_schedule_row_sha256 == row["schedule_row_sha256"]


def test_human_disposition_and_analysis_contract_are_fail_closed() -> None:
    human = read_json(ROOT / "reports/pilot_3/evidence/human_validation_disposition.json")
    prompt_contract = read_json(ROOT / "reports/pilot_3/evidence/prompt_schedule_contract.json")
    contract = read_json(ROOT / "reports/pilot_3/evidence/analysis_contract.json")

    assert human["resolves_task_id"] == "P3-T10"
    assert human["disposition"] == "excluded"
    assert human["human_validity_claim_allowed"] is False
    adapter = prompt_contract["generation_adapter_contract"]
    assert adapter["ordering_basis"] == "t12_canonical_sequence"
    assert adapter["cell_count"] == 320
    assert adapter["secondary_reordering_allowed"] is False
    assert contract["resolves_task_id"] == "P3-T13"
    assert contract["generation_authorized"] is False
    assert contract["analysis_authorized"] is False
    assert contract["readiness"]["ready"] is False
    assert contract["availability"]["family_size"] == 17
    assert contract["conditional_proximity"]["family_size"] == 2
    assert contract["artist_reversal_harm"]["family_size"] == 8
    assert contract["missingness"]["stochastic_generator_or_future_prompt_claim"] is False
    assert contract["execution_guard"]["caller_supplied_hashes_or_statuses_may_authorize"] is False
    assert contract["execution_guard"]["state"] == (
        "closed_pending_canonical_p3_t14_file_backed_verifier"
    )


def test_artifacts_and_rows_are_deterministic_and_self_hashed() -> None:
    for relative, hash_field in (
        ("reports/pilot_3/evidence/phase_b_design.json", "semantic_sha256"),
        (
            "reports/pilot_3/evidence/human_validation_disposition.json",
            "semantic_sha256",
        ),
        ("reports/pilot_3/evidence/prompt_schedule_contract.json", "semantic_sha256"),
        ("reports/pilot_3/evidence/analysis_contract.json", "semantic_sha256"),
    ):
        value = read_json(ROOT / relative)
        recorded = value.pop(hash_field)
        assert recorded == stable_hash(value)

    for relative, hash_field in (
        ("data/manifests/pilot_3/prompts.jsonl", "prompt_sha256"),
        ("data/manifests/pilot_3/schedule.jsonl", "schedule_row_sha256"),
    ):
        for row in read_jsonl(ROOT / relative):
            recorded = row.pop(hash_field)
            assert recorded == stable_hash(row)


def test_write_is_deterministic_and_tampering_fails_verification(tmp_path: Path) -> None:
    _copy_bundle_inputs(tmp_path)
    first = write_phase_b_freeze_bundle(tmp_path)
    first_schedule = (tmp_path / "data/manifests/pilot_3/schedule.jsonl").read_bytes()
    second = write_phase_b_freeze_bundle(tmp_path)
    second_schedule = (tmp_path / "data/manifests/pilot_3/schedule.jsonl").read_bytes()

    assert first == second
    assert first_schedule == second_schedule

    schedule_path = tmp_path / "data/manifests/pilot_3/schedule.jsonl"
    rows = read_jsonl(schedule_path)
    rows[0]["request_body"]["quality"] = "high"
    write_jsonl(schedule_path, rows)
    with pytest.raises(ValueError, match="stale|recompute"):
        verify_phase_b_freeze_bundle(tmp_path)


def test_future_binding_check_is_closed_when_evidence_is_absent(tmp_path: Path) -> None:
    _copy_bundle_inputs(tmp_path)
    result = assess_future_bindings(tmp_path)

    assert result["required_bindings_present_and_status_matched"] is False
    assert result["generation_authorized"] is False
    assert result["decision"] == "CLOSED"
    assert all(not row["satisfied"] for row in result["bindings"].values())


def test_config_json_is_strict_json_without_nonfinite_values() -> None:
    config = load_study_config(ROOT)
    json.dumps(config, allow_nan=False)
