from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from latent_art_bench.config import load_config
from latent_art_bench.evaluation.qualification import load_qualification_cards
from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.reporting.pilot import (
    build_artist_free_control_diagnostics,
    build_pilot_report,
    write_generation_contact_sheet,
    write_pilot_artifact_index,
)
from latent_art_bench.schemas import (
    AnalysisResult,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    RunRecord,
)


def _result(*, preparation_bypass: bool = False) -> AnalysisResult:
    return AnalysisResult(
        cell_id="cell",
        target_artist_id="artist",
        model="gpt-image-1",
        measurement="learned_formal",
        feature_name="learned_formal",
        feature_version="learned-formal-test-v1",
        feature_config_hash="b" * 64,
        qualification_evidence_artifact_sha256="d" * 64,
        real_feature_manifest_sha256="e" * 64,
        generated_feature_manifest_sha256="f" * 64,
        generation_manifest_sha256="1" * 64,
        generation_attestation_sha256="2" * 64,
        reference_transform_state_sha256="c" * 64,
        qualified_reference_transform_state_sha256="c" * 64,
        preparation_qualification_bypass=preparation_bypass,
        analysis_cell_sha256="3" * 64,
        target_gap=1.0,
        real_real_gap=2.0,
        nearest_neighbor_id="neighbor",
        nearest_neighbor_gap=1.5,
        target_neighbor_separation=1.0,
        calibrated_target_gap=-1.0,
        calibrated_target_gap_interval=[-2.0, 0.5],
        specificity_margin=0.1,
        specificity_margin_interval=[-0.2, 0.4],
        subsample_size=4,
        subsample_draws=200,
        confidence_level=0.95,
    )


def _prompt(prompt_id: str) -> PromptRecord:
    return PromptRecord(
        prompt_id=prompt_id,
        content_id="content",
        template_id="template",
        prompt=f"Frozen prompt {prompt_id}",
        artist_free_control=True,
        test_only=True,
    )


def _call(
    prompt_id: str,
    model: str,
    repetition: int,
    status: str = "succeeded",
    *,
    bypass: bool = False,
    output_path: str | None = None,
    actual_size: tuple[int, int] | None = None,
    request_identity: str | None = None,
    identity_provenance: str | None = None,
) -> GenerationCallRecord:
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    return GenerationCallRecord(
        call_id=f"call-{prompt_id}-{model}-{repetition}-{status}",
        run_id="run",
        prompt_id=prompt_id,
        model=model,
        endpoint="http://127.0.0.1:10531/v1/images/generations",
        requested_size="1024x1024",
        requested_quality="low",
        requested_output_format="png",
        repetition=repetition,
        request_identity_sha256=request_identity,
        request_identity_provenance=identity_provenance,
        status=status,
        qualification_bypass=bypass,
        started_at=now,
        completed_at=now,
        output_path=output_path,
        actual_width=actual_size[0] if actual_size else None,
        actual_height=actual_size[1] if actual_size else None,
    )


def test_contact_sheet_includes_both_models_and_every_repetition(tmp_path: Path) -> None:
    calls = []
    for model_index, model in enumerate(("gpt-image-1", "gpt-image-2")):
        for repetition in range(2):
            path = tmp_path / f"{model}-{repetition}.png"
            Image.new(
                "RGB", (32, 24), (50 * model_index, 80 * repetition, 120)
            ).save(path)
            calls.append(
                _call(
                    "prompt-a",
                    model,
                    repetition,
                    output_path=str(path),
                )
            )

    output = write_generation_contact_sheet(calls, tmp_path, tmp_path / "sheet.jpg")

    with Image.open(output) as sheet:
        assert sheet.size == (420 * 4, 336 + 44)


def test_report_retains_failure_retry_and_uncertainty_accounting() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    cards = load_qualification_cards(
        Path(path) for path in config.qualification.cards
    )
    prompts = [_prompt("prompt-a")]
    calls = [
        _call("prompt-a", model, repetition, actual_size=(1400, 1120))
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    ]
    calls.insert(0, _call("prompt-a", "gpt-image-1", 1, "refused"))
    result = _result()

    markdown, summary = build_pilot_report(
        config, cards, calls, [result], prompts=prompts
    )

    generation = summary["generation"]
    assert generation["attempt_records"] == 5
    assert generation["expected_frozen_cells"] == 4
    assert generation["resolved_engineering_cells"] == 4
    assert generation["resolved_non_bypass_cells"] == 4
    assert generation["retry_resolved_cells"] == 1
    assert generation["unresolved_frozen_cells"] == 0
    assert generation["returned_dimensions"]["exact_requested_size_matches"] == 0
    assert (
        generation["returned_dimensions"]["comparable_requested_and_returned_sizes"]
        == 4
    )
    assert generation["request_identity_unverified_retry_cells"] == 1
    assert "only the prompt ID, model, and repetition match" in markdown
    assert "Exact requested-size matches: 0/4" in markdown
    assert "The generated side is fixed at n=4" in markdown
    assert "not inferential confidence intervals" in markdown
    assert "generator-sampling and prompt-cluster uncertainty" in markdown
    assert "Specificity reference-resampling ranges include zero in 1/1 cells" in markdown
    assert "They are not quality scores" in markdown

    interval_accounting = summary["analysis_intervals"]
    assert interval_accounting["kind"] == "real_reference_subsampling_quantiles"
    assert not interval_accounting["inferential_confidence_intervals"]
    assert interval_accounting["generated_sample_sizes"] == [4]


def test_closed_gate_reports_explicit_engineering_traversal_without_narrow_decision() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    cards = load_qualification_cards(Path(path) for path in config.qualification.cards)
    failed_cards = [
        card.model_copy(update={"status": "fail"})
        if card.measurement == "learned_formal"
        else card
        for card in cards
    ]

    markdown, summary = build_pilot_report(
        config,
        failed_cards,
        analysis_results=[_result(preparation_bypass=True)],
    )

    assert not summary["qualification_gate"]["allowed"]
    assert summary["engineering_traversal"]["qualification_bypass_explicit"]
    assert "scientific gate closed; engineering traversal completed" in markdown
    assert "Decision: narrow" not in markdown


def test_report_labels_legacy_request_identity_as_retrospective_attestation() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    cards = load_qualification_cards(Path(path) for path in config.qualification.cards)
    identity = "a" * 64
    calls = [
        _call(
            "prompt-a",
            "gpt-image-1",
            0,
            "refused",
            request_identity=identity,
            identity_provenance="legacy_run_attestation",
        ),
        _call(
            "prompt-a",
            "gpt-image-1",
            0,
            request_identity=identity,
            identity_provenance="legacy_run_attestation",
        ),
    ]

    markdown, summary = build_pilot_report(
        config, cards, calls, prompts=[_prompt("prompt-a")]
    )

    generation = summary["generation"]
    assert generation["request_identity_verified_retry_cells"] == 1
    assert generation["legacy_attested_request_identity_retry_cells"] == 1
    assert generation["native_request_identity_retry_cells"] == 0
    assert "reconstructed from retained legacy run metadata" in markdown
    assert "not a native pre-request identity capture" in markdown


def test_bypassed_success_resolves_only_an_engineering_frozen_cell() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    cards = load_qualification_cards(
        Path(path) for path in config.qualification.cards
    )
    prompt = _prompt("prompt-a")

    _, summary = build_pilot_report(
        config,
        cards,
        [_call("prompt-a", "gpt-image-1", 0, bypass=True)],
        prompts=[prompt],
    )

    generation = summary["generation"]
    assert generation["qualification_bypass_calls"] == 1
    assert generation["resolved_engineering_cells"] == 1
    assert generation["resolved_non_bypass_cells"] == 0
    assert generation["unresolved_frozen_cells"] == 3


def test_artifact_index_tracks_ignored_and_report_evidence(tmp_path: Path) -> None:
    ignored = tmp_path / "artifacts" / "pilot_1" / "rows.jsonl"
    ignored_source = tmp_path / "data" / "pilot_1" / "source" / "work.jpg"
    tracked = tmp_path / "reports" / "pilot_1" / "summary.json"
    ignored.parent.mkdir(parents=True)
    ignored_source.parent.mkdir(parents=True)
    tracked.parent.mkdir(parents=True)
    ignored.write_text('{"row":1}\n{"row":2}\n', encoding="utf-8")
    ignored_source.write_bytes(b"local source media")
    tracked.write_text('{"ok":true}\n', encoding="utf-8")
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    run = RunRecord(
        run_id="run-1",
        command="report-pilot",
        arguments={},
        input_hashes={str(ignored.resolve()): "b" * 64},
        status="complete",
        started_at=now,
        completed_at=now,
    )

    paths = write_pilot_artifact_index(
        tmp_path / "reports" / "pilot_1",
        tmp_path,
        [ignored, ignored_source, tracked],
        [(run, "a" * 64)],
    )

    run_rows = read_jsonl(paths[0])
    index = read_json(paths[1])
    by_path = {row["path"]: row for row in index["entries"]}
    assert len(run_rows) == 1
    assert run_rows[0]["source_run_record_sha256"] == "a" * 64
    assert run_rows[0]["input_hashes"] == {"artifacts/pilot_1/rows.jsonl": "b" * 64}
    assert str(tmp_path.resolve()) not in paths[0].read_text(encoding="utf-8")
    assert by_path["artifacts/pilot_1/rows.jsonl"]["retention"] == "ignored_local"
    assert by_path["artifacts/pilot_1/rows.jsonl"]["row_count"] == 2
    assert by_path["data/pilot_1/source/work.jpg"]["retention"] == "ignored_local"
    assert by_path["reports/pilot_1/summary.json"]["retention"] == "tracked_evidence"
    assert by_path["reports/pilot_1/summary.json"]["sha256"] == hash_file(tracked)
    assert hash_file(paths[1]) in paths[2].read_text(encoding="utf-8")


def test_sanitizer_replaces_external_absolute_path_values(tmp_path: Path) -> None:
    now = datetime(2026, 8, 31, tzinfo=timezone.utc)
    run = RunRecord(
        run_id="run-external",
        command="verify",
        arguments={"checkpoint": "/private/tmp/checkpoint.ckpt"},
        status="complete",
        started_at=now,
        completed_at=now,
    )

    paths = write_pilot_artifact_index(
        tmp_path / "reports" / "pilot_1", tmp_path, [], [(run, "c" * 64)]
    )

    rows = read_jsonl(paths[0])
    assert rows[0]["arguments"]["checkpoint"] == "<external-path>/checkpoint.ckpt"
    assert "/private/tmp" not in paths[0].read_text(encoding="utf-8")


def test_artist_free_controls_cover_the_complete_matched_grid() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    prompts = [
        PromptRecord.model_validate(row)
        for row in read_jsonl(Path(config.generation.prompt_manifest))
    ]
    generated = {}
    for measurement in config.measurements.required:
        version, config_hash = config.measurement_identities()[measurement]
        rows = []
        for prompt_index, prompt in enumerate(prompts):
            for model_index, model in enumerate(config.generation.models):
                for repetition in range(config.generation.repetitions):
                    identifier = f"{measurement}-{prompt.prompt_id}-{model}-{repetition}"
                    rows.append(
                        FeatureRow(
                            feature_id=identifier,
                            derived_view_id=f"view-{identifier}",
                            reproduction_id=f"reproduction-{identifier}",
                            canonical_work_id=f"work-{identifier}",
                            artist_id=prompt.target_artist_id,
                            origin="generated",
                            model=model,
                            prompt_id=prompt.prompt_id,
                            repetition=repetition,
                            feature_name=measurement,
                            feature_version=version,
                            feature_config_hash=config_hash,
                            vector=[float(prompt_index + model_index + repetition)],
                            scalars={},
                            status="ok",
                        )
                    )
        generated[measurement] = rows

    result = build_artist_free_control_diagnostics(
        config,
        prompts,
        generated,
        {measurement: measurement[0] * 64 for measurement in generated},
    )

    assert result["pair_count"] == 64
    assert len(result["summaries"]) == 4
    assert all(row["pair_count"] == 16 for row in result["summaries"])
    assert len(result["result_sha256"]) == 64
