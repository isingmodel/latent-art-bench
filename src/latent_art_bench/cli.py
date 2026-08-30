from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional, cast

import typer

from latent_art_bench.config import PilotConfig, load_config
from latent_art_bench.evaluation.distances import analyze_cell
from latent_art_bench.evaluation.qualification import (
    load_qualification_cards,
    qualification_card_from_evidence,
    qualification_gate,
)
from latent_art_bench.features.chromatic import extract_chromatic_features
from latent_art_bench.generation.openai_images import (
    ALLOWED_MODELS,
    OpenAIImageAdapter,
    plan_generation_calls,
)
from latent_art_bench.io import hash_file, read_json, read_jsonl, write_json, write_jsonl
from latent_art_bench.manifests import parse_manifest, validate_manifests
from latent_art_bench.preprocessing.pipeline import preprocess_reproductions
from latent_art_bench.preprocessing.synthetic import write_synthetic_images
from latent_art_bench.provenance import recorded_run
from latent_art_bench.reporting.pilot import build_pilot_report, write_pilot_report
from latent_art_bench.schemas import (
    AllowedImageModel,
    AnalysisCell,
    AnalysisResult,
    CanonicalWorkRecord,
    DerivedViewRecord,
    GenerationCallRecord,
    PromptRecord,
    QualificationCard,
    QualificationEvidence,
    ReproductionRecord,
)

app = typer.Typer(
    name="latent-art-bench",
    no_args_is_help=True,
    help="Run the gated LatentArtBench development pilot.",
)
DEFAULT_CONFIG = Path("configs/pilot_0/pilot.yaml")


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _resolved_config(root: Path, config_path: Path) -> tuple:
    path = _resolve(root, config_path)
    return load_config(path), path


def _existing_cards(root: Path, config: PilotConfig) -> List[QualificationCard]:
    return load_qualification_cards(_existing_card_paths(root, config))


def _existing_card_paths(root: Path, config: PilotConfig) -> List[Path]:
    paths = [_resolve(root, Path(value)) for value in config.qualification.cards]
    return [path for path in paths if path.is_file()]


@app.command("validate-manifest")
def validate_manifest_command(
    manifests: List[Path] = typer.Argument(..., help="One or more JSONL manifests."),
    root: Path = typer.Option(Path("."), help="Repository/data path root."),
    check_files: bool = typer.Option(False, help="Check local files and declared SHA-256 values."),
) -> None:
    root = root.resolve()
    paths = [_resolve(root, path) for path in manifests]
    with recorded_run(
        root,
        root / "artifacts/runs",
        "validate-manifest",
        {"manifests": [str(path) for path in paths], "check_files": check_files},
        input_paths=paths,
    ) as run:
        counts = validate_manifests(paths, root=root, check_files=check_files)
        typer.echo(json.dumps({"valid": True, "counts": counts}, sort_keys=True))
        run.outputs.extend(str(path) for path in paths)


@app.command("preprocess")
def preprocess_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    reproduction_manifest: Optional[Path] = typer.Option(None, "--manifest"),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/derived_views.jsonl"), "--output-manifest"
    ),
    output_dir: Path = typer.Option(Path("artifacts/pilot_0/derived"), "--output-dir"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    source_manifest = reproduction_manifest or Path(config.corpus.reproduction_manifest)
    source_manifest = _resolve(root, source_manifest)
    output_manifest = _resolve(root, output_manifest)
    output_dir = _resolve(root, output_dir)
    with recorded_run(
        root,
        root / "artifacts/runs",
        "preprocess",
        {
            "manifest": str(source_manifest),
            "output_manifest": str(output_manifest),
            "output_dir": str(output_dir),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[source_manifest],
    ) as run:
        parsed = parse_manifest(source_manifest)
        records = [row for row in parsed if isinstance(row, ReproductionRecord)]
        if len(records) != len(parsed):
            raise ValueError("preprocess accepts a reproduction-only manifest")
        views = preprocess_reproductions(records, config.preprocessing, root, output_dir)
        write_jsonl(output_manifest, views)
        run.outputs.append(str(output_manifest))
        typer.echo(json.dumps({"derived_views": len(views), "manifest": str(output_manifest)}))


@app.command("extract-features")
def extract_features_command(
    derived_manifest: Path = typer.Argument(...),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    canonical_manifest: Optional[Path] = typer.Option(None, "--canonical-manifest"),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/chromatic_features.jsonl"), "--output-manifest"
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    derived_manifest = _resolve(root, derived_manifest)
    output_manifest = _resolve(root, output_manifest)
    canonical_path = canonical_manifest or Path(config.corpus.canonical_manifest)
    canonical_path = _resolve(root, canonical_path)
    inputs = [derived_manifest] + ([canonical_path] if canonical_path.is_file() else [])
    with recorded_run(
        root,
        root / "artifacts/runs",
        "extract-features",
        {"derived_manifest": str(derived_manifest), "output_manifest": str(output_manifest)},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=inputs,
    ) as run:
        parsed = parse_manifest(derived_manifest)
        views = [row for row in parsed if isinstance(row, DerivedViewRecord)]
        if len(views) != len(parsed):
            raise ValueError("extract-features accepts a derived-view-only manifest")
        artist_by_work = {}
        split_by_work = {}
        if canonical_path.is_file():
            canonical_rows = parse_manifest(canonical_path)
            for row in canonical_rows:
                if not isinstance(row, CanonicalWorkRecord):
                    raise ValueError("canonical manifest contains a non-canonical record")
                artist_by_work[row.canonical_work_id] = row.artist_id
                split_by_work[row.canonical_work_id] = row.split
        features = extract_chromatic_features(
            views,
            config.measurements.chromatic,
            root,
            artist_by_work=artist_by_work,
            split_by_work=split_by_work,
        )
        write_jsonl(output_manifest, features)
        run.outputs.append(str(output_manifest))
        typer.echo(json.dumps({"features": len(features), "manifest": str(output_manifest)}))


@app.command("qualify")
def qualify_command(
    evidence_paths: List[Path] = typer.Argument(..., help="Frozen real-only evidence JSON files."),
    output_dir: Path = typer.Option(Path("artifacts/pilot_0/qualification"), "--output-dir"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    evidence_paths = [_resolve(root, path) for path in evidence_paths]
    output_dir = _resolve(root, output_dir)
    with recorded_run(
        root,
        root / "artifacts/runs",
        "qualify",
        {"evidence_paths": [str(path) for path in evidence_paths]},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=evidence_paths,
    ) as run:
        cards = []
        expected_identities = config.measurement_identities()
        for path in evidence_paths:
            evidence = QualificationEvidence.model_validate(read_json(path))
            expected = expected_identities.get(evidence.measurement)
            if expected is None:
                raise ValueError(f"measurement is not required by pilot_0: {evidence.measurement}")
            if (evidence.feature_version, evidence.feature_config_hash) != expected:
                raise ValueError(
                    f"evidence identity does not match the frozen {evidence.measurement} config"
                )
            for evidence_value in evidence.evidence_paths:
                evidence_artifact = _resolve(root, Path(evidence_value))
                if not evidence_artifact.is_file():
                    raise ValueError(
                        f"missing qualification evidence artifact: {evidence_artifact}"
                    )
                run.input_hashes[str(evidence_artifact)] = hash_file(evidence_artifact)
            card = qualification_card_from_evidence(evidence)
            card_path = output_dir / f"{card.measurement}.json"
            write_json(card_path, card)
            run.outputs.append(str(card_path))
            cards.append(card)
        typer.echo(
            json.dumps({card.measurement: card.status for card in cards}, sort_keys=True)
        )


@app.command("generate")
def generate_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    prompt_manifest: Optional[Path] = typer.Option(None, "--prompt-manifest"),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/generation_calls.jsonl"), "--output-manifest"
    ),
    model: Optional[List[str]] = typer.Option(None, "--model"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    allow_unqualified_test_generation: bool = typer.Option(
        False,
        "--allow-unqualified-test-generation",
        help="Explicitly bypass WP5 for test-only prompts; outputs cannot be benchmark evidence.",
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    prompts_path = prompt_manifest or Path(config.generation.prompt_manifest)
    prompts_path = _resolve(root, prompts_path)
    output_manifest = _resolve(root, output_manifest)
    output_dir = _resolve(root, Path(config.generation.output_dir))
    selected = model or list(config.generation.models)
    invalid = sorted(set(selected) - ALLOWED_MODELS)
    if invalid:
        raise typer.BadParameter(f"unsupported image model(s): {', '.join(invalid)}")
    if len(selected) != len(set(selected)):
        raise typer.BadParameter("duplicate --model values are not allowed")
    selected_models = cast(List[AllowedImageModel], selected)
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    gate_open, decisions = qualification_gate(
        config.measurements.required, cards, config.measurement_identities()
    )
    if not dry_run and not gate_open and not allow_unqualified_test_generation:
        raise RuntimeError(
            "WP5 qualification gate is closed: "
            + ", ".join(f"{name}={status}" for name, status in decisions.items())
        )

    with recorded_run(
        root,
        root / "artifacts/runs",
        "generate",
        {
            "prompt_manifest": str(prompts_path),
            "models": selected_models,
            "dry_run": dry_run,
            "qualification_bypass": allow_unqualified_test_generation,
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[prompts_path, *card_paths],
    ) as run:
        parsed = parse_manifest(prompts_path)
        prompts = [row for row in parsed if isinstance(row, PromptRecord)]
        if len(prompts) != len(parsed):
            raise ValueError("generate accepts a prompt-only manifest")
        if allow_unqualified_test_generation and any(not prompt.test_only for prompt in prompts):
            raise ValueError("the unqualified bypass accepts only prompts marked test_only=true")

        if dry_run:
            calls = plan_generation_calls(
                run.run_id,
                prompts,
                selected_models,
                config.generation,
                qualification_bypass=False,
            )
        else:
            calls: List[GenerationCallRecord] = []
            with OpenAIImageAdapter(config.generation) as adapter:
                for prompt in prompts:
                    for selected_model in selected_models:
                        for repetition in range(config.generation.repetitions):
                            calls.append(
                                adapter.generate(
                                    run.run_id,
                                    prompt,
                                    selected_model,
                                    repetition,
                                    output_dir,
                                    qualification_bypass=allow_unqualified_test_generation,
                                )
                            )
        write_jsonl(output_manifest, calls)
        run.outputs.append(str(output_manifest))
        run.outputs.extend(call.output_path for call in calls if call.output_path)
        counts = {
            status: sum(call.status == status for call in calls)
            for status in sorted({call.status for call in calls})
        }
        typer.echo(json.dumps({"calls": len(calls), "counts": counts}, sort_keys=True))
        if not dry_run and any(call.status != "succeeded" for call in calls):
            raise RuntimeError("one or more image calls did not succeed; inspect the call manifest")


@app.command("analyze-pilot")
def analyze_pilot_command(
    cells_path: Path = typer.Argument(..., help="JSONL file of frozen analysis cells."),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/analysis_results.jsonl"), "--output-manifest"
    ),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    allow_unqualified_test_analysis: bool = typer.Option(
        False, "--allow-unqualified-test-analysis"
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    cells_path = _resolve(root, cells_path)
    output_manifest = _resolve(root, output_manifest)
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    gate_open, decisions = qualification_gate(
        config.measurements.required, cards, config.measurement_identities()
    )
    if not gate_open and not allow_unqualified_test_analysis:
        raise RuntimeError(
            "WP5 qualification gate is closed: "
            + ", ".join(f"{name}={status}" for name, status in decisions.items())
        )
    with recorded_run(
        root,
        root / "artifacts/runs",
        "analyze-pilot",
        {"cells_path": str(cells_path), "qualification_bypass": allow_unqualified_test_analysis},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[cells_path, *card_paths],
        random_seeds={"equal_sample_seed": config.analysis.equal_sample_seed},
    ) as run:
        cells = [AnalysisCell.model_validate(row) for row in read_jsonl(cells_path)]
        results = [
            analyze_cell(
                cell,
                seed=config.analysis.equal_sample_seed,
                draws=config.analysis.equal_sample_draws,
                confidence_level=config.analysis.confidence_level,
            )
            for cell in cells
        ]
        write_jsonl(output_manifest, results)
        run.outputs.append(str(output_manifest))
        typer.echo(json.dumps({"analysis_cells": len(results), "manifest": str(output_manifest)}))


@app.command("report-pilot")
def report_pilot_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    generation_manifest: Optional[Path] = typer.Option(None, "--generation-manifest"),
    analysis_manifest: Optional[Path] = typer.Option(None, "--analysis-manifest"),
    output_dir: Path = typer.Option(Path("reports/pilot_0"), "--output-dir"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    output_dir = _resolve(root, output_dir)
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    calls: List[GenerationCallRecord] = []
    results: List[AnalysisResult] = []
    input_paths: List[Path] = list(card_paths)
    if generation_manifest:
        generation_path = _resolve(root, generation_manifest)
        input_paths.append(generation_path)
        calls = [GenerationCallRecord.model_validate(row) for row in read_jsonl(generation_path)]
    if analysis_manifest:
        analysis_path = _resolve(root, analysis_manifest)
        input_paths.append(analysis_path)
        results = [AnalysisResult.model_validate(row) for row in read_jsonl(analysis_path)]
    with recorded_run(
        root,
        root / "artifacts/runs",
        "report-pilot",
        {"output_dir": str(output_dir)},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=input_paths,
    ) as run:
        markdown, summary = build_pilot_report(config, cards, calls, results)
        outputs = write_pilot_report(output_dir, markdown, summary, config)
        run.outputs.extend(str(path) for path in outputs)
        typer.echo(
            json.dumps(
                {
                    "report": str(outputs[0]),
                    "gate_open": summary["qualification_gate"]["allowed"],
                }
            )
        )


@app.command("synthetic-dry-run")
def synthetic_dry_run_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    output_dir: Path = typer.Option(Path("artifacts/synthetic-dry-run"), "--output-dir"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    output_dir = _resolve(root, output_dir)
    fixture_dir = output_dir / "source"
    derived_dir = output_dir / "derived"
    with recorded_run(
        root,
        root / "artifacts/runs",
        "synthetic-dry-run",
        {"output_dir": str(output_dir)},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        random_seeds={"synthetic_fixture": 1729},
    ) as run:
        paths = write_synthetic_images(fixture_dir, size=64, seed=1729)
        reproductions = []
        for name, path in sorted(paths.items()):
            reproductions.append(
                ReproductionRecord(
                    reproduction_id=f"synthetic-{name}",
                    canonical_work_id=f"synthetic-work-{name}",
                    source_id="generated-fixture-v1",
                    local_path=str(path),
                    sha256=hash_file(path),
                    native_width=64,
                    native_height=64,
                    border_status="none",
                    rights_status="verified",
                    rights_basis="programmatically generated test fixture",
                    split="train",
                )
            )
        first_views = preprocess_reproductions(
            reproductions, config.preprocessing, root, derived_dir
        )
        second_views = preprocess_reproductions(
            reproductions, config.preprocessing, root, derived_dir
        )
        first_features = extract_chromatic_features(
            first_views, config.measurements.chromatic, root
        )
        second_features = extract_chromatic_features(
            second_views, config.measurements.chromatic, root
        )
        first_signature = [
            (view.derived_view_id, view.output_sha256, view.width, view.height)
            for view in first_views
        ]
        second_signature = [
            (view.derived_view_id, view.output_sha256, view.width, view.height)
            for view in second_views
        ]
        if first_signature != second_signature:
            raise AssertionError(
                "repeated preprocessing did not produce identical content signatures"
            )
        if [row.model_dump(mode="json") for row in first_features] != [
            row.model_dump(mode="json") for row in second_features
        ]:
            raise AssertionError("repeated feature extraction was not identical")

        reproduction_path = output_dir / "reproductions.jsonl"
        view_path = output_dir / "derived_views.jsonl"
        feature_path = output_dir / "features.jsonl"
        summary_path = output_dir / "summary.json"
        write_jsonl(reproduction_path, reproductions)
        write_jsonl(view_path, first_views)
        write_jsonl(feature_path, first_features)
        summary = {
            "deterministic": True,
            "fixture_count": len(reproductions),
            "derived_hashes": [view.output_sha256 for view in first_views],
            "feature_ids": [row.feature_id for row in first_features],
        }
        write_json(summary_path, summary)
        run.outputs.extend(
            str(path)
            for path in [reproduction_path, view_path, feature_path, summary_path]
        )
        typer.echo(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    app()
