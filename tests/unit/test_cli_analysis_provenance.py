from datetime import datetime, timezone
from pathlib import Path

import pytest

import latent_art_bench.cli as cli
from latent_art_bench.config import load_config
from latent_art_bench.evaluation.qualification import load_qualification_cards
from latent_art_bench.generation.openai_images import plan_generation_calls
from latent_art_bench.io import read_jsonl
from latent_art_bench.schemas import PromptRecord, RunRecord

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_all_card_evidence_files_are_report_inputs() -> None:
    config = load_config(REPOSITORY_ROOT / "configs/pilot_1/pilot.yaml")
    cards = load_qualification_cards(
        REPOSITORY_ROOT / path for path in config.qualification.cards
    )

    evidence_paths = cli._qualification_evidence_paths(REPOSITORY_ROOT, cards)

    assert (
        REPOSITORY_ROOT
        / "reports/pilot_1/evidence/learned_formal_model_verification.json"
    ) in evidence_paths


def test_closed_gate_preparation_accepts_only_explicit_test_bypass_calls() -> None:
    config = load_config(REPOSITORY_ROOT / "configs/pilot_1/pilot.yaml")
    prompts = [
        PromptRecord.model_validate(row)
        for row in read_jsonl(REPOSITORY_ROOT / "configs/pilot_1/prompts.jsonl")
    ]
    calls = [
        call.model_copy(update={"status": "succeeded"})
        for call in plan_generation_calls(
            "fresh-bypass-run",
            prompts,
            config.generation.models,
            config.generation,
            qualification_bypass=True,
        )
    ]
    expected_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }

    selected = cli._generation_calls_for_preparation(
        calls, expected_cells, preparation_bypass=True
    )

    assert set(selected) == expected_cells
    with pytest.raises(ValueError, match="explicit closed-gate"):
        cli._generation_calls_for_preparation(
            calls, expected_cells, preparation_bypass=False
        )


def test_existing_run_outputs_are_included_without_external_paths(tmp_path: Path) -> None:
    retained = tmp_path / "artifacts" / "pilot_1" / "derived.jsonl"
    retained.parent.mkdir(parents=True)
    retained.write_text("{}\n", encoding="utf-8")
    missing = tmp_path / "artifacts" / "pilot_1" / "missing.jsonl"
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    run = RunRecord(
        run_id="run-output-ledger",
        command="prepare",
        arguments={},
        status="complete",
        started_at=now,
        completed_at=now,
        outputs=[str(retained), str(missing), "/private/tmp/external.jsonl"],
    )

    paths = cli._existing_run_output_paths(tmp_path, [(run, "a" * 64)])

    assert paths == [retained.resolve()]


def _touch_inputs(tmp_path: Path) -> dict[str, Path]:
    paths = {
        name: tmp_path / f"{name}.jsonl"
        for name in (
            "cells",
            "results",
            "generation",
            "real_chromatic",
            "generated_chromatic",
            "real_learned",
            "generated_learned",
        )
    }
    for path in paths.values():
        path.write_text("", encoding="utf-8")
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    paths["evidence"] = evidence
    attestation = tmp_path / "attestation.json"
    attestation.write_text("{}\n", encoding="utf-8")
    paths["attestation"] = attestation
    return paths


def _patch_common(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, paths: dict[str, Path]):
    config = load_config(REPOSITORY_ROOT / "configs/pilot_1/pilot.yaml")
    config.generation.prompt_manifest = str(
        REPOSITORY_ROOT / "configs/pilot_1/prompts.jsonl"
    )
    config.generation.manifest_attestation = str(paths["attestation"])
    prompts = [
        PromptRecord.model_validate(row)
        for row in read_jsonl(REPOSITORY_ROOT / "configs/pilot_1/prompts.jsonl")
    ]
    monkeypatch.setattr(cli, "_resolved_config", lambda *_: (config, paths["evidence"]))
    monkeypatch.setattr(cli, "_existing_cards", lambda *_: [])
    monkeypatch.setattr(cli, "_existing_card_paths", lambda *_: [])
    monkeypatch.setattr(
        cli,
        "_qualification_analysis_provenance",
        lambda _root, _config, measurement, _real_feature_manifest=None: (
            "a" * 64,
            "b" * 64 if measurement == "learned_formal" else None,
            paths["evidence"],
        ),
    )
    monkeypatch.setattr(
        cli,
        "_qualification_identities",
        lambda *_: {
            measurement: (*config.measurement_identities()[measurement], "c" * 64)
            for measurement in config.measurements.required
        },
    )
    monkeypatch.setattr(cli, "qualification_gate", lambda *_: (True, {}))
    monkeypatch.setattr(
        cli,
        "_verify_complete_generation_manifest",
        lambda *_: ([], prompts),
    )
    return config


def test_analyze_command_invokes_exact_grid_provenance_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _touch_inputs(tmp_path)
    _patch_common(monkeypatch, tmp_path, paths)

    def reject(*_args, **_kwargs):
        raise RuntimeError("analysis-grid-validator-called")

    monkeypatch.setattr(cli, "validate_analysis_grid_provenance", reject)

    with pytest.raises(RuntimeError, match="analysis-grid-validator-called"):
        cli.analyze_pilot_command(
            cells_path=paths["cells"],
            generation_manifest=paths["generation"],
            real_chromatic=paths["real_chromatic"],
            generated_chromatic=paths["generated_chromatic"],
            real_learned=paths["real_learned"],
            generated_learned=paths["generated_learned"],
            output_manifest=tmp_path / "out.jsonl",
            config_path=paths["evidence"],
            allow_unqualified_test_analysis=False,
            root=tmp_path,
        )


def test_report_command_invokes_exact_grid_provenance_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = _touch_inputs(tmp_path)
    _patch_common(monkeypatch, tmp_path, paths)

    def reject(*_args, **_kwargs):
        raise RuntimeError("report-grid-validator-called")

    monkeypatch.setattr(cli, "validate_analysis_grid_provenance", reject)

    with pytest.raises(RuntimeError, match="report-grid-validator-called"):
        cli.report_pilot_command(
            config_path=paths["evidence"],
            generation_manifest=paths["generation"],
            analysis_manifest=paths["results"],
            analysis_cells=paths["cells"],
            real_chromatic=paths["real_chromatic"],
            generated_chromatic=paths["generated_chromatic"],
            real_learned=paths["real_learned"],
            generated_learned=paths["generated_learned"],
            output_dir=tmp_path / "report",
            root=tmp_path,
        )
