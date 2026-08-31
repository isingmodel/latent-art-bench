from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, cast

import typer
from PIL import Image

from latent_art_bench.config import PilotConfig, load_config
from latent_art_bench.data.corpus import (
    acquire_corpus,
    acquisition_summary,
    apply_candidate_overrides,
    load_candidate_overrides,
    select_candidate_works,
    write_artist_audit_csv,
    write_contact_sheets,
)
from latent_art_bench.data.museums import audit_museum_sources
from latent_art_bench.evaluation.contracts import expected_qualification_identities
from latent_art_bench.evaluation.distances import analyze_cell
from latent_art_bench.evaluation.pilot_cells import (
    build_analysis_cells,
    validate_analysis_grid_provenance,
)
from latent_art_bench.evaluation.qualification import (
    load_qualification_cards,
    qualification_card_from_evidence,
    qualification_gate,
    validate_qualification_artifact_binding,
)
from latent_art_bench.evaluation.qualification_orchestration import (
    learned_formal_v2_protocol,
    run_chromatic_qualification,
    run_learned_formal_qualification,
)
from latent_art_bench.evaluation.real_only import evaluate_chromatic_real_only
from latent_art_bench.evaluation.vae_equivalence import verify_sd2_vae_equivalence
from latent_art_bench.features.chromatic import extract_chromatic_features
from latent_art_bench.features.learned_pipeline import extract_learned_formal_features
from latent_art_bench.generation.attestation import (
    attest_generation_calls,
    validate_generation_call_identities,
    verify_generation_attestation,
)
from latent_art_bench.generation.openai_images import (
    ALLOWED_MODELS,
    OpenAIImageAdapter,
    generation_endpoint,
    plan_generation_calls,
    unique_successful_generation_calls_by_cell,
)
from latent_art_bench.io import (
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)
from latent_art_bench.manifests import parse_manifest, validate_manifests, validate_records
from latent_art_bench.preprocessing.pipeline import preprocess_reproductions
from latent_art_bench.preprocessing.synthetic import write_synthetic_images
from latent_art_bench.provenance import recorded_run
from latent_art_bench.reporting.pilot import (
    build_artist_free_control_diagnostics,
    build_pilot_report,
    write_generation_contact_sheet,
    write_pilot_artifact_index,
    write_pilot_evidence_snapshots,
    write_pilot_report,
)
from latent_art_bench.schemas import (
    AllowedImageModel,
    AnalysisCell,
    AnalysisResult,
    CanonicalWorkRecord,
    CorpusCandidateRecord,
    DerivedViewRecord,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    QualificationCard,
    QualificationEvidence,
    ReproductionRecord,
    RunRecord,
)

app = typer.Typer(
    name="latent-art-bench",
    no_args_is_help=True,
    help="Run the gated LatentArtBench development pilot.",
)
DEFAULT_CONFIG = Path("configs/pilot_0/pilot.yaml")


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _relative_artifact_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolved_config(root: Path, config_path: Path) -> tuple:
    path = _resolve(root, config_path)
    return load_config(path), path


def _existing_cards(root: Path, config: PilotConfig) -> List[QualificationCard]:
    cards = load_qualification_cards(_existing_card_paths(root, config))
    for card in cards:
        validate_qualification_artifact_binding(card, root)
    return cards


def _existing_card_paths(root: Path, config: PilotConfig) -> List[Path]:
    paths = [_resolve(root, Path(value)) for value in config.qualification.cards]
    return [path for path in paths if path.is_file()]


def _qualification_evidence_paths(
    root: Path, cards: List[QualificationCard]
) -> List[Path]:
    """Resolve every evidence file cited by qualification cards exactly once."""

    paths: List[Path] = []
    seen: set[Path] = set()
    for card in cards:
        for value in card.evidence_paths:
            path = _resolve(root, Path(value)).resolve()
            if not path.is_file():
                raise FileNotFoundError(
                    f"missing {card.measurement} qualification evidence: {path}"
                )
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _qualification_identities(root: Path, config: PilotConfig) -> Dict[str, tuple]:
    return expected_qualification_identities(config, root)


def _qualification_contract_hash(
    root: Path, config: PilotConfig, measurement: str
) -> Optional[str]:
    identity = _qualification_identities(root, config)[measurement]
    return str(identity[2]) if len(identity) >= 3 else None


def _qualification_attestation_context(
    root: Path, config: PilotConfig
) -> tuple[Dict[str, Path], Dict[str, str]]:
    """Resolve current, content-validated cards for generation attestation."""

    paths = _existing_card_paths(root, config)
    cards = _existing_cards(root, config)
    card_paths = {card.measurement: path for path, card in zip(paths, cards)}
    if set(card_paths) != set(config.measurements.required):
        raise ValueError("generation attestation requires one current card per measurement")
    contract_hashes: Dict[str, str] = {}
    for measurement in config.measurements.required:
        value = _qualification_contract_hash(root, config, measurement)
        if value is None:
            raise ValueError(
                f"generation attestation lacks a {measurement} qualification contract"
            )
        contract_hashes[measurement] = value
    return card_paths, contract_hashes


def _qualification_analysis_provenance(
    root: Path,
    config: PilotConfig,
    measurement: str,
    real_feature_manifest: Optional[Path] = None,
) -> tuple[str, Optional[str], Path]:
    """Resolve the current qualification artifact and its learned PCA identity."""

    matching = [
        (path, card)
        for path, card in zip(
            _existing_card_paths(root, config), _existing_cards(root, config)
        )
        if card.measurement == measurement
    ]
    if len(matching) != 1:
        raise ValueError(
            f"analysis requires exactly one current {measurement} qualification card"
        )
    _, card = matching[0]
    expected = _qualification_identities(root, config)[measurement]
    if (
        card.feature_version != expected[0]
        or card.feature_config_hash != expected[1]
        or (len(expected) >= 3 and card.qualification_contract_hash != expected[2])
    ):
        raise ValueError(f"{measurement} qualification card identity is stale")
    artifact_path = validate_qualification_artifact_binding(card, root)
    artifact = read_json(artifact_path)
    if not isinstance(artifact, dict):
        raise ValueError(f"{measurement} qualification artifact must be a JSON object")
    if artifact.get("feature_config_sha256") != card.feature_config_hash:
        raise ValueError(f"{measurement} qualification artifact identity is stale")
    if artifact.get("status") != card.status:
        raise ValueError(f"{measurement} card status disagrees with its evidence artifact")
    if measurement == "learned_formal":
        if card.input_feature_manifest_sha256 is None:
            raise ValueError("learned-formal qualification card lacks its input manifest hash")
        if real_feature_manifest is not None and (
            hash_file(real_feature_manifest) != card.input_feature_manifest_sha256
        ):
            raise ValueError(
                "learned-formal qualification used a different real feature manifest"
            )
    qualified_pca: Optional[str] = None
    if measurement == "learned_formal":
        primary_pca = artifact.get("primary_pca")
        if not isinstance(primary_pca, dict):
            raise ValueError("learned-formal qualification artifact lacks primary PCA evidence")
        state = primary_pca.get("state_sha256")
        if not isinstance(state, str) or len(state) != 64:
            raise ValueError("learned-formal qualification artifact has an invalid PCA state")
        qualified_pca = state
    return hash_file(artifact_path), qualified_pca, artifact_path


def _verify_complete_generation_manifest(
    root: Path,
    config: PilotConfig,
    generation_manifest: Path,
    attestation_path: Path,
    prompt_path: Path,
) -> tuple[List[GenerationCallRecord], List[PromptRecord]]:
    calls = [
        GenerationCallRecord.model_validate(row) for row in read_jsonl(generation_manifest)
    ]
    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
    card_paths, contract_hashes = _qualification_attestation_context(root, config)
    evidence = verify_generation_attestation(
        generation_manifest,
        attestation_path,
        prompt_path,
        calls,
        prompts,
        config.generation,
        root=root,
        qualification_card_paths=card_paths,
        qualification_contract_hashes=contract_hashes,
    )
    expected_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }
    if config.pilot_id == "pilot_1" and len(expected_cells) != 40:
        raise ValueError("pilot_1 requires exactly 40 frozen generation cells")
    successful = unique_successful_generation_calls_by_cell(
        calls, include_qualification_bypass=True
    )
    if set(successful) != expected_cells:
        missing = len(expected_cells - set(successful))
        extra = len(set(successful) - expected_cells)
        raise ValueError(
            "generation manifest does not resolve the exact frozen grid: "
            f"missing={missing}, extra={extra}"
        )
    expected_endpoint = generation_endpoint(config.generation)
    for call in calls:
        redundant_fields = {
            "endpoint": expected_endpoint,
            "requested_size": config.generation.size,
            "requested_quality": config.generation.quality,
            "requested_output_format": config.generation.output_format,
        }
        mismatches = [
            name
            for name, expected in redundant_fields.items()
            if getattr(call, name) != expected
        ]
        if mismatches:
            raise ValueError(
                f"generation call fields disagree with request identity for {call.call_id}: "
                + ", ".join(sorted(mismatches))
            )
    for call in successful.values():
        if not call.output_path or not call.output_sha256:
            raise ValueError(f"successful generation call lacks output evidence: {call.call_id}")
        output_path = _resolve(root, Path(call.output_path))
        if hash_file(output_path) != call.output_sha256:
            raise ValueError(f"generated output hash mismatch: {call.call_id}")
        with Image.open(output_path) as image:
            image.load()
            observed_size = image.size
            observed_format = (image.format or "unknown").lower()
        if observed_size != (call.actual_width, call.actual_height):
            raise ValueError(f"generated output dimensions mismatch: {call.call_id}")
        if observed_format != call.actual_format:
            raise ValueError(f"generated output format mismatch: {call.call_id}")
    expected_evidence = {
        "expected_frozen_cell_count": len(expected_cells),
        "resolved_frozen_cell_count": len(expected_cells),
        "successful_output_count": len(expected_cells),
    }
    mismatches = [
        name for name, value in expected_evidence.items() if evidence.get(name) != value
    ]
    if mismatches:
        raise ValueError(
            "generation attestation does not certify the complete frozen grid: "
            + ", ".join(sorted(mismatches))
        )
    return calls, prompts


def _validate_unqualified_generation_scope(
    config: PilotConfig, prompts: List[PromptRecord]
) -> None:
    """Restrict closed-gate image calls to the frozen non-scientific test domain."""

    if (
        config.purpose != "api_integration_test_only"
        or config.generation.mode != "test_only"
        or config.generation.scientific_claims_enabled is not False
    ):
        raise ValueError(
            "the unqualified generation bypass is restricted to the non-scientific "
            "test-only pilot"
        )
    if any(not prompt.test_only for prompt in prompts):
        raise ValueError("the unqualified bypass accepts only prompts marked test_only=true")


def _generation_calls_for_preparation(
    calls: List[GenerationCallRecord],
    expected_cells: set[tuple[str, str, int]],
    *,
    preparation_bypass: bool,
) -> Dict[tuple[str, str, int], GenerationCallRecord]:
    """Select the exact output grid while keeping bypass calls engineering-only."""

    successful = unique_successful_generation_calls_by_cell(
        calls, include_qualification_bypass=True
    )
    missing = sorted(expected_cells - set(successful))
    if missing:
        raise ValueError(
            f"generated feature extraction has {len(missing)} unresolved frozen cells"
        )
    unexpected = sorted(set(successful) - expected_cells)
    if unexpected:
        raise ValueError(
            f"generated feature extraction has {len(unexpected)} unexpected frozen cells"
        )
    if any(call.qualification_bypass for call in calls) and not preparation_bypass:
        raise ValueError(
            "qualification-bypass generation calls require the explicit closed-gate "
            "test-only preparation path"
        )
    return successful


def _existing_run_output_paths(
    root: Path, run_records: List[tuple[RunRecord, str]]
) -> List[Path]:
    """Resolve every retained in-repository run output that still exists."""

    root = root.resolve()
    paths = set()
    for run, _ in run_records:
        for value in run.outputs:
            path = _resolve(root, Path(value)).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if path.is_file():
                paths.add(path)
    return sorted(paths, key=str)


@app.command("audit-corpus")
def audit_corpus_command(
    nga_data_dir: Path = typer.Option(..., "--nga-data-dir", help="NGA open-data data/ path."),
    met_csv: Path = typer.Option(..., "--met-csv", help="Frozen MetObjects.csv path."),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    output_manifest: Optional[Path] = typer.Option(None, "--output-manifest"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    nga_data_dir = _resolve(root, nga_data_dir)
    met_csv = _resolve(root, met_csv)
    output_manifest = _resolve(
        root, output_manifest or Path(config.corpus.candidate_work_audit)
    )
    override_path = _resolve(root, Path(config.corpus.candidate_overrides))
    artist_audit_path = _resolve(root, Path(config.corpus.candidate_artist_audit))
    nga_inputs = [
        nga_data_dir / "objects.csv",
        nga_data_dir / "objects_constituents.csv",
        nga_data_dir / "published_images.csv",
    ]
    with recorded_run(
        root,
        root / "artifacts/runs",
        "audit-corpus",
        {
            "nga_data_dir": str(nga_data_dir),
            "met_csv": str(met_csv),
            "output_manifest": str(output_manifest),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[override_path, met_csv, *nga_inputs],
    ) as run:
        candidates = audit_museum_sources(config.corpus, nga_data_dir, met_csv)
        candidates = apply_candidate_overrides(
            candidates, load_candidate_overrides(override_path)
        )
        write_jsonl(output_manifest, candidates)
        write_artist_audit_csv(artist_audit_path, config.corpus, candidates)
        counts: Dict[str, Dict[str, int]] = {}
        for artist in config.corpus.selected_artists:
            artist_rows = [row for row in candidates if row.artist_id == artist.artist_id]
            counts[artist.artist_id] = {
                decision: sum(row.decision == decision for row in artist_rows)
                for decision in ("include", "review", "exclude")
            }
        run.outputs.extend([str(output_manifest), str(artist_audit_path)])
        typer.echo(
            json.dumps(
                {"candidates": len(candidates), "counts": counts},
                sort_keys=True,
            )
        )
@app.command("acquire-corpus")
def acquire_corpus_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    candidate_manifest: Optional[Path] = typer.Option(None, "--candidate-manifest"),
    image_dir: Path = typer.Option(Path("data/pilot_0/source"), "--image-dir"),
    screening_path: Path = typer.Option(
        Path("reports/pilot_0/evidence/reproduction_screening.json"),
        "--screening-output",
    ),
    summary_path: Path = typer.Option(
        Path("reports/pilot_0/evidence/corpus_summary.json"), "--summary-output"
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    candidate_manifest = _resolve(
        root, candidate_manifest or Path(config.corpus.candidate_work_audit)
    )
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    artist_audit_path = _resolve(root, Path(config.corpus.candidate_artist_audit))
    image_dir = _resolve(root, image_dir)
    screening_path = _resolve(root, screening_path)
    summary_path = _resolve(root, summary_path)
    with recorded_run(
        root,
        root / "artifacts/runs",
        "acquire-corpus",
        {
            "candidate_manifest": str(candidate_manifest),
            "image_dir": str(image_dir),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[candidate_manifest],
        random_seeds={"corpus_split": config.corpus.split_seed},
    ) as run:
        parsed = parse_manifest(candidate_manifest)
        candidates = [row for row in parsed if isinstance(row, CorpusCandidateRecord)]
        if len(candidates) != len(parsed):
            raise ValueError("acquire-corpus accepts a candidate-only manifest")
        selected = select_candidate_works(candidates, config.corpus)
        canonical, reproductions, screening = acquire_corpus(
            selected, config.corpus, root, image_dir
        )
        validate_records([*canonical, *reproductions], root=root, check_files=True)
        write_jsonl(canonical_path, canonical)
        write_jsonl(reproduction_path, reproductions)
        write_json(screening_path, {"records": screening})
        summary = acquisition_summary(canonical, reproductions, screening)
        write_json(summary_path, summary)
        write_artist_audit_csv(
            artist_audit_path,
            config.corpus,
            candidates,
            canonical=canonical,
            reproductions=reproductions,
        )
        contact_sheets = write_contact_sheets(
            canonical, reproductions, root, root / "data/pilot_0/contact_sheets"
        )
        run.outputs.extend(
            str(path)
            for path in [
                canonical_path,
                reproduction_path,
                screening_path,
                summary_path,
                artist_audit_path,
                *contact_sheets,
            ]
        )
        typer.echo(json.dumps(summary, sort_keys=True))


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
        expected_identities = _qualification_identities(root, config)
        for path in evidence_paths:
            evidence = QualificationEvidence.model_validate(read_json(path))
            expected = expected_identities.get(evidence.measurement)
            if expected is None:
                raise ValueError(
                    f"measurement is not required by {config.pilot_id}: "
                    f"{evidence.measurement}"
                )
            if (evidence.feature_version, evidence.feature_config_hash) != expected[:2]:
                raise ValueError(
                    f"evidence identity does not match the frozen {evidence.measurement} config"
                )
            if len(expected) >= 3 and evidence.qualification_contract_hash != expected[2]:
                raise ValueError(
                    f"evidence contract does not match the frozen {evidence.measurement} "
                    "data/config/code identity"
                )
            validate_qualification_artifact_binding(evidence, root)
            for evidence_value in evidence.evidence_paths:
                evidence_artifact = _resolve(root, Path(evidence_value))
                if not evidence_artifact.is_file():
                    raise ValueError(
                        f"missing qualification evidence artifact: {evidence_artifact}"
                    )
                run.input_hashes[str(evidence_artifact)] = hash_file(evidence_artifact)
            card = qualification_card_from_evidence(evidence)
            primary_artifact = read_json(
                _resolve(root, Path(evidence.evidence_paths[0]))
            )
            if not isinstance(primary_artifact, dict) or (
                primary_artifact.get("status") != card.status
            ):
                raise ValueError(
                    f"{card.measurement} evidence checks disagree with the result status"
                )
            card_path = output_dir / f"{card.measurement}.json"
            write_json(card_path, card)
            run.outputs.append(str(card_path))
            cards.append(card)
        typer.echo(
            json.dumps({card.measurement: card.status for card in cards}, sort_keys=True)
        )


@app.command("evaluate-chromatic")
def evaluate_chromatic_command(
    feature_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/chromatic_features.jsonl"), "--feature-manifest"
    ),
    derived_manifest: Path = typer.Option(
        Path("artifacts/pilot_0/derived_views.jsonl"), "--derived-manifest"
    ),
    evidence_path: Path = typer.Option(
        Path("configs/pilot_0/qualification/evidence.chromatic.json"),
        "--evidence-output",
    ),
    artifact_path: Path = typer.Option(
        Path("reports/pilot_0/evidence/chromatic_qualification.json"),
        "--artifact-output",
    ),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    feature_manifest = _resolve(root, feature_manifest)
    derived_manifest = _resolve(root, derived_manifest)
    evidence_path = _resolve(root, evidence_path)
    artifact_path = _resolve(root, artifact_path)
    input_paths = [
        canonical_path,
        reproduction_path,
        derived_manifest,
        feature_manifest,
    ]
    with recorded_run(
        root,
        root / "artifacts/runs",
        "evaluate-chromatic",
        {
            "feature_manifest": str(feature_manifest),
            "derived_manifest": str(derived_manifest),
            "evidence_output": str(evidence_path),
            "artifact_output": str(artifact_path),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=input_paths,
        random_seeds={"qualification": config.qualification.random_seed},
    ) as run:
        canonical = [
            row
            for row in parse_manifest(canonical_path)
            if isinstance(row, CanonicalWorkRecord)
        ]
        reproductions = [
            row
            for row in parse_manifest(reproduction_path)
            if isinstance(row, ReproductionRecord)
        ]
        views = [
            row
            for row in parse_manifest(derived_manifest)
            if isinstance(row, DerivedViewRecord)
        ]
        features = [
            row
            for row in parse_manifest(feature_manifest)
            if isinstance(row, FeatureRow)
        ]
        artifact_reference = _relative_artifact_path(artifact_path, root)
        artifact, evidence = evaluate_chromatic_real_only(
            config,
            canonical,
            reproductions,
            views,
            features,
            root,
            artifact_reference,
        )
        write_json(artifact_path, artifact)
        write_json(evidence_path, evidence)
        run.outputs.extend([str(artifact_path), str(evidence_path)])
        typer.echo(json.dumps(artifact["decisions"], sort_keys=True))


@app.command("evaluate-chromatic-v2")
def evaluate_chromatic_v2_command(
    evidence_path: Path = typer.Option(
        Path("configs/pilot_1/qualification/evidence.chromatic.json"),
        "--evidence-output",
    ),
    artifact_path: Path = typer.Option(
        Path("reports/pilot_1/evidence/chromatic_qualification.json"),
        "--artifact-output",
    ),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Run the source-branching Lee-seamlessness v2 qualification."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    evidence_path = _resolve(root, evidence_path)
    artifact_path = _resolve(root, artifact_path)
    with recorded_run(
        root,
        root / "artifacts/runs",
        "evaluate-chromatic-v2",
        {
            "evidence_output": str(evidence_path),
            "artifact_output": str(artifact_path),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[canonical_path, reproduction_path],
        random_seeds={"qualification": config.qualification.random_seed},
    ) as run:
        qualification_run = run_chromatic_qualification(
            config,
            root,
            artifact_path,
            evidence_path,
        )
        result = qualification_run.result
        evidence = qualification_run.evidence
        run.outputs.extend([str(artifact_path), str(evidence_path)])
        typer.echo(
            json.dumps(
                {
                    "status": result.status,
                    "codec_q85_supported": result.codec_stability.supported,
                    "stable_within_frozen_margin": (
                        evidence.stable_within_frozen_margin
                    ),
                    "artist_signal": evidence.held_out_artist_signal_valid,
                    "source_controlled": evidence.source_confounding_controlled,
                },
                sort_keys=True,
            )
        )


@app.command("extract-learned-formal")
def extract_learned_formal_command(
    derived_manifest: Path = typer.Argument(...),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    canonical_manifest: Optional[Path] = typer.Option(None, "--canonical-manifest"),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_features.jsonl"), "--output-manifest"
    ),
    provenance_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_provenance.jsonl"),
        "--provenance-manifest",
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Extract the pinned SD2 A-vector with per-image deterministic seeds."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    derived_manifest = _resolve(root, derived_manifest)
    output_manifest = _resolve(root, output_manifest)
    provenance_manifest = _resolve(root, provenance_manifest)
    canonical_path = canonical_manifest or Path(config.corpus.canonical_manifest)
    canonical_path = _resolve(root, canonical_path)
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    model_config = config.measurements.learned_formal
    snapshot = _resolve(root, Path(str(model_config.model_snapshot_dir)))
    model_files = [
        snapshot / "config.json",
        snapshot / "diffusion_pytorch_model.safetensors",
    ]
    source_checkout = _resolve(root, Path(str(model_config.source_checkout_dir)))
    with recorded_run(
        root,
        root / "artifacts/runs",
        "extract-learned-formal",
        {
            "derived_manifest": str(derived_manifest),
            "output_manifest": str(output_manifest),
            "provenance_manifest": str(provenance_manifest),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            derived_manifest,
            canonical_path,
            reproduction_path,
            source_checkout / ".git/HEAD",
            *model_files,
        ],
        random_seeds={"learned_formal_base": int(model_config.base_seed or 0)},
    ) as run:
        run.checkpoint_hashes.update(
            {
                "sd2_vae_config": str(model_config.model_config_sha256),
                "sd2_vae_weights": str(model_config.model_weights_sha256),
                "sd2_full_checkpoint_reference": str(
                    model_config.full_checkpoint_sha256
                ),
            }
        )
        parsed = parse_manifest(derived_manifest)
        views = [row for row in parsed if isinstance(row, DerivedViewRecord)]
        if len(views) != len(parsed):
            raise ValueError("extract-learned-formal accepts a derived-view-only manifest")
        canonical_rows = parse_manifest(canonical_path)
        canonical = [
            row for row in canonical_rows if isinstance(row, CanonicalWorkRecord)
        ]
        if len(canonical) != len(canonical_rows):
            raise ValueError("canonical manifest contains a non-canonical record")
        reproduction_rows = parse_manifest(reproduction_path)
        reproductions = [
            row for row in reproduction_rows if isinstance(row, ReproductionRecord)
        ]
        if len(reproductions) != len(reproduction_rows):
            raise ValueError("reproduction manifest contains a non-reproduction record")
        artist_by_work = {row.canonical_work_id: row.artist_id for row in canonical}
        split_by_work = {row.canonical_work_id: row.split for row in canonical}

        def progress(index: int, total: int) -> None:
            if index == 1 or index == total or index % 10 == 0:
                typer.echo(f"learned-formal {index}/{total}")

        features, provenance = extract_learned_formal_features(
            views,
            reproductions,
            model_config,
            root,
            artist_by_work=artist_by_work,
            split_by_work=split_by_work,
            progress=progress,
        )
        write_jsonl(output_manifest, features)
        write_jsonl(provenance_manifest, provenance)
        run.outputs.extend([str(output_manifest), str(provenance_manifest)])
        typer.echo(
            json.dumps(
                {
                    "features": len(features),
                    "vector_length": len(features[0].vector),
                    "manifest": str(output_manifest),
                },
                sort_keys=True,
            )
        )


@app.command("verify-learned-formal-model")
def verify_learned_formal_model_command(
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    full_checkpoint: Optional[Path] = typer.Option(None, "--full-checkpoint"),
    output_path: Optional[Path] = typer.Option(None, "--output"),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Verify every pinned VAE tensor against the recovered full checkpoint."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    learned = config.measurements.learned_formal
    if full_checkpoint is None:
        raise typer.BadParameter(
            "--full-checkpoint is required for bitwise tensor-equivalence evidence"
        )
    if output_path is None and learned.model_verification_report is None:
        raise ValueError("learned-formal model verification output is not configured")
    snapshot = _resolve(root, Path(str(learned.model_snapshot_dir)))
    config_file = snapshot / "config.json"
    weights_file = snapshot / "diffusion_pytorch_model.safetensors"
    checkpoint_path = _resolve(root, full_checkpoint)
    output_path = _resolve(
        root, output_path or Path(str(learned.model_verification_report))
    )
    with recorded_run(
        root,
        root / "artifacts/runs",
        "verify-learned-formal-model",
        {
            "full_checkpoint": str(checkpoint_path),
            "output": str(output_path),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        # The verifier hashes the 5.2 GB checkpoint before restricted loading and
        # records the pin in both its evidence and this run; avoid hashing it twice.
        input_paths=[config_file, weights_file],
    ) as run:
        evidence = verify_sd2_vae_equivalence(
            checkpoint_path,
            weights_file,
            config_path=config_file,
            expected_checkpoint_sha256=str(learned.full_checkpoint_sha256),
            expected_checkpoint_size_bytes=int(learned.full_checkpoint_size_bytes or 0),
            expected_weights_sha256=str(learned.model_weights_sha256),
            expected_weights_size_bytes=weights_file.stat().st_size,
            expected_config_sha256=str(learned.model_config_sha256),
            expected_config_size_bytes=config_file.stat().st_size,
            model_repository=str(learned.model_repository),
            model_revision=str(learned.model_revision),
        )
        write_json(output_path, evidence)
        run.outputs.append(str(output_path))
        run.checkpoint_hashes.update(
            {
                "sd2_full_checkpoint": str(learned.full_checkpoint_sha256),
                "sd2_vae_config": str(learned.model_config_sha256),
                "sd2_vae_weights": str(learned.model_weights_sha256),
            }
        )
        if evidence["verification_status"] != "pass":
            raise RuntimeError("full-checkpoint/VAE tensor equivalence failed")
        typer.echo(
            json.dumps(
                {
                    "verified": True,
                    "exact_equal_count": evidence["comparison"][
                        "exact_equal_count"
                    ],
                    "tensor_count": evidence["mapping"]["expected_tensor_count"],
                    "evidence": str(output_path),
                },
                sort_keys=True,
            )
        )


@app.command("evaluate-learned-formal-v2")
def evaluate_learned_formal_v2_command(
    feature_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_features.jsonl"),
        "--feature-manifest",
    ),
    derived_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/derived_views.jsonl"), "--derived-manifest"
    ),
    evidence_path: Path = typer.Option(
        Path("configs/pilot_1/qualification/evidence.learned_formal.json"),
        "--evidence-output",
    ),
    artifact_path: Path = typer.Option(
        Path("reports/pilot_1/evidence/learned_formal_qualification.json"),
        "--artifact-output",
    ),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    determinism_probe_count: Optional[int] = typer.Option(
        None,
        min=1,
        max=12,
        help="Must match the probe count frozen in the qualification config.",
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Qualify the seeded Kim A-vector with train-only and nested PCA fits."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    feature_manifest = _resolve(root, feature_manifest)
    derived_manifest = _resolve(root, derived_manifest)
    evidence_path = _resolve(root, evidence_path)
    artifact_path = _resolve(root, artifact_path)
    learned = config.measurements.learned_formal
    configured_probe_count = config.qualification.learned_determinism_probe_count
    if configured_probe_count is None:
        raise ValueError("learned-formal qualification lacks a frozen probe count")
    if (
        determinism_probe_count is not None
        and determinism_probe_count != configured_probe_count
    ):
        raise ValueError(
            "--determinism-probe-count must match the frozen qualification config"
        )
    probe_count = configured_probe_count
    snapshot = _resolve(root, Path(str(learned.model_snapshot_dir)))
    model_files = [
        snapshot / "config.json",
        snapshot / "diffusion_pytorch_model.safetensors",
    ]
    model_verification_path = _resolve(
        root, Path(str(learned.model_verification_report))
    )
    source_checkout = _resolve(root, Path(str(learned.source_checkout_dir)))
    with recorded_run(
        root,
        root / "artifacts/runs",
        "evaluate-learned-formal-v2",
        {
            "feature_manifest": str(feature_manifest),
            "derived_manifest": str(derived_manifest),
            "determinism_probe_count": probe_count,
            "evidence_output": str(evidence_path),
            "artifact_output": str(artifact_path),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            canonical_path,
            reproduction_path,
            feature_manifest,
            derived_manifest,
            model_verification_path,
            source_checkout / ".git/HEAD",
            *model_files,
        ],
        random_seeds={"learned_formal_base": int(learned.base_seed or 0)},
    ) as run:
        qualification_run = run_learned_formal_qualification(
            config,
            root,
            feature_manifest,
            derived_manifest,
            artifact_path,
            evidence_path,
            determinism_probe_count=probe_count,
            progress=lambda index, total: typer.echo(
                f"determinism-probe {index}/{total}"
            ),
        )
        result = qualification_run.result
        run.checkpoint_hashes.update(
            {
                "sd2_vae_config": str(learned.model_config_sha256),
                "sd2_vae_weights": str(learned.model_weights_sha256),
                "sd2_full_checkpoint_reference": str(
                    learned.full_checkpoint_sha256
                ),
            }
        )
        run.outputs.extend([str(artifact_path), str(evidence_path)])
        typer.echo(
            json.dumps(
                {
                    "status": result.status,
                    "artist_balanced_accuracy": (
                        result.classification.held_out_artist.balanced_accuracy
                    ),
                    "source_balanced_accuracy": (
                        result.classification.held_out_source.balanced_accuracy
                    ),
                    "reproduction_ratio": result.reproduction_stability.point_ratio,
                    "determinism_probes": qualification_run.determinism_probe_count,
                    "determinism_probe_sources": list(
                        qualification_run.determinism_probe_sources
                    ),
                },
                sort_keys=True,
            )
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
        config.measurements.required, cards, _qualification_identities(root, config)
    )
    if dry_run and allow_unqualified_test_generation:
        raise ValueError(
            "--allow-unqualified-test-generation is only meaningful for live requests"
        )
    if gate_open and allow_unqualified_test_generation:
        raise ValueError(
            "the unqualified generation bypass is only valid while the scientific gate "
            "is closed"
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
        input_paths=[
            prompts_path,
            *card_paths,
            *_qualification_evidence_paths(root, cards),
        ],
    ) as run:
        parsed = parse_manifest(prompts_path)
        prompts = [row for row in parsed if isinstance(row, PromptRecord)]
        if len(prompts) != len(parsed):
            raise ValueError("generate accepts a prompt-only manifest")
        if allow_unqualified_test_generation:
            _validate_unqualified_generation_scope(config, prompts)

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
                            call = adapter.generate(
                                run.run_id,
                                prompt,
                                selected_model,
                                repetition,
                                output_dir,
                                qualification_bypass=allow_unqualified_test_generation,
                            )
                            if call.output_path:
                                call.output_path = _relative_artifact_path(
                                    Path(call.output_path), root
                                )
                            calls.append(call)
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


@app.command("attest-generation-manifest")
def attest_generation_manifest_command(
    generation_manifest: Path = typer.Argument(...),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    evidence_path: Optional[Path] = typer.Option(None, "--evidence-output"),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Bind legacy/native attempts to frozen requests and verify every output byte."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    generation_manifest = _resolve(root, generation_manifest)
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    configured_evidence = config.generation.manifest_attestation
    if evidence_path is None and configured_evidence is None:
        raise ValueError("generation manifest attestation output is not configured")
    evidence_path = _resolve(
        root,
        evidence_path or Path(str(configured_evidence)),
    )
    calls = [
        GenerationCallRecord.model_validate(row) for row in read_jsonl(generation_manifest)
    ]
    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
    card_paths, contract_hashes = _qualification_attestation_context(root, config)
    run_record_paths = {
        run_id: root / "artifacts/runs" / f"{run_id}.json"
        for run_id in sorted({call.run_id for call in calls})
    }
    missing_runs = [path for path in run_record_paths.values() if not path.is_file()]
    if missing_runs:
        raise FileNotFoundError(f"missing {len(missing_runs)} originating run records")
    run_records = {
        run_id: RunRecord.model_validate(read_json(path))
        for run_id, path in run_record_paths.items()
    }
    output_paths = [
        _resolve(root, Path(call.output_path))
        for call in calls
        if call.status == "succeeded" and call.output_path
    ]
    with recorded_run(
        root,
        root / "artifacts/runs",
        "attest-generation-manifest",
        {
            "generation_manifest": str(generation_manifest),
            "evidence_output": str(evidence_path),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            generation_manifest,
            prompt_path,
            *card_paths.values(),
            *run_record_paths.values(),
            *output_paths,
        ],
    ) as run:
        updated, evidence = attest_generation_calls(
            calls,
            prompts,
            config.generation,
            prompt_path,
            run_records,
            run_record_paths,
            root,
            qualification_card_paths=card_paths,
            qualification_contract_hashes=contract_hashes,
        )
        write_jsonl(generation_manifest, updated)
        evidence["attested_manifest_sha256"] = hash_file(generation_manifest)
        write_json(evidence_path, evidence)
        run.outputs.extend([str(generation_manifest), str(evidence_path)])
        typer.echo(
            json.dumps(
                {
                    "verified": True,
                    "attempt_records": len(updated),
                    "unique_request_identities": evidence[
                        "unique_request_identity_count"
                    ],
                    "resolved_cells": evidence["resolved_frozen_cell_count"],
                    "legacy_attestations": evidence[
                        "legacy_run_attestation_count"
                    ],
                },
                sort_keys=True,
            )
        )


@app.command("retry-generation-failures")
def retry_generation_failures_command(
    generation_manifest: Path = typer.Argument(...),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    max_attempts_per_cell: int = typer.Option(3, min=1, max=10),
    allow_unqualified_test_generation: bool = typer.Option(
        False,
        "--allow-unqualified-test-generation",
        help="Retry closed-gate test-only cells; all attempts remain engineering-only.",
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Retry only unresolved frozen cells while retaining every failed attempt."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    generation_manifest = _resolve(root, generation_manifest)
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    output_dir = _resolve(root, Path(config.generation.output_dir))
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    gate_open, decisions = qualification_gate(
        config.measurements.required, cards, _qualification_identities(root, config)
    )
    if gate_open and allow_unqualified_test_generation:
        raise ValueError(
            "the unqualified generation bypass is only valid while the scientific gate "
            "is closed"
        )
    if not gate_open and not allow_unqualified_test_generation:
        raise RuntimeError(
            "WP5 qualification gate is closed: "
            + ", ".join(f"{name}={status}" for name, status in decisions.items())
        )
    calls = [
        GenerationCallRecord.model_validate(row) for row in read_jsonl(generation_manifest)
    ]
    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
    prompt_by_id = {row.prompt_id: row for row in prompts}
    if len(prompt_by_id) != len(prompts):
        raise ValueError("retry manifest contains duplicate prompt identifiers")
    if allow_unqualified_test_generation:
        _validate_unqualified_generation_scope(config, prompts)
    expected_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }
    validate_generation_call_identities(calls, prompts, config.generation)
    if gate_open and any(call.qualification_bypass for call in calls):
        raise ValueError(
            "scientific-gate retry rejects a manifest containing test-bypass attempts"
        )

    def resolved_cells() -> set:
        return set(
            unique_successful_generation_calls_by_cell(
                calls,
                include_qualification_bypass=allow_unqualified_test_generation,
            )
        )

    unexpected = {
        (call.prompt_id, call.model, call.repetition) for call in calls
    } - expected_cells
    if unexpected:
        raise ValueError(f"generation manifest contains {len(unexpected)} unexpected cells")

    unresolved = sorted(expected_cells - resolved_cells())
    if not unresolved:
        typer.echo(json.dumps({"retried": 0, "unresolved": 0}, sort_keys=True))
        return
    with recorded_run(
        root,
        root / "artifacts/runs",
        "retry-generation-failures",
        {
            "generation_manifest": str(generation_manifest),
            "unresolved_cells": unresolved,
            "max_attempts_per_cell": max_attempts_per_cell,
            "qualification_bypass": allow_unqualified_test_generation,
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            generation_manifest,
            prompt_path,
            *card_paths,
            *_qualification_evidence_paths(root, cards),
        ],
    ) as run:
        attempt_count = 0
        with OpenAIImageAdapter(config.generation) as adapter:
            for prompt_id, model, repetition in unresolved:
                prompt = prompt_by_id[prompt_id]
                for _ in range(max_attempts_per_cell):
                    attempt = adapter.generate(
                        run.run_id,
                        prompt,
                        model,
                        repetition,
                        output_dir,
                        qualification_bypass=allow_unqualified_test_generation,
                    )
                    if attempt.output_path:
                        attempt.output_path = _relative_artifact_path(
                            Path(attempt.output_path), root
                        )
                    calls.append(attempt)
                    attempt_count += 1
                    write_jsonl(generation_manifest, calls)
                    if attempt.status == "succeeded":
                        run.outputs.append(str(attempt.output_path))
                        break
        remaining = sorted(expected_cells - resolved_cells())
        run.outputs.append(str(generation_manifest))
        typer.echo(
            json.dumps(
                {
                    "retried": attempt_count,
                    "attempt_records": len(calls),
                    "unresolved": len(remaining),
                },
                sort_keys=True,
            )
        )
        if remaining:
            raise RuntimeError(f"{len(remaining)} generation cells remain unresolved")


@app.command("prepare-generated-features")
def prepare_generated_features_command(
    generation_manifest: Path = typer.Argument(...),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    reproduction_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generated_reproductions.jsonl"),
        "--reproduction-manifest",
    ),
    derived_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generated_derived_views.jsonl"),
        "--derived-manifest",
    ),
    chromatic_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generated_chromatic_features.jsonl"),
        "--chromatic-manifest",
    ),
    learned_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generated_learned_formal_features.jsonl"),
        "--learned-manifest",
    ),
    learned_provenance_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generated_learned_formal_provenance.jsonl"),
        "--learned-provenance-manifest",
    ),
    output_dir: Path = typer.Option(
        Path("artifacts/pilot_1/generated_derived"), "--output-dir"
    ),
    allow_unqualified_test_preparation: bool = typer.Option(
        False, "--allow-unqualified-test-preparation"
    ),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Prepare generated diagnostics, requiring an explicit bypass if the gate is closed."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    attestation_card_paths, attestation_contract_hashes = (
        _qualification_attestation_context(root, config)
    )
    gate_open, decisions = qualification_gate(
        config.measurements.required,
        cards,
        _qualification_identities(root, config),
    )
    if not gate_open and not allow_unqualified_test_preparation:
        raise RuntimeError(
            "WP5 qualification gate is closed: "
            + ", ".join(f"{name}={status}" for name, status in decisions.items())
            + "; use --allow-unqualified-test-preparation only for the separately "
            "labeled API-integration engineering path"
        )
    if allow_unqualified_test_preparation and gate_open:
        raise ValueError(
            "the qualification bypass is only valid while the scientific gate is closed"
        )
    preparation_bypass = not gate_open
    if preparation_bypass and (
        config.purpose != "api_integration_test_only"
        or config.generation.mode != "test_only"
        or config.generation.scientific_claims_enabled is not False
    ):
        raise ValueError(
            "closed-gate preparation is restricted to the non-scientific test-only pilot"
        )
    generation_manifest = _resolve(root, generation_manifest)
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    attestation_path = _resolve(
        root, Path(str(config.generation.manifest_attestation))
    )
    reproduction_manifest = _resolve(root, reproduction_manifest)
    derived_manifest = _resolve(root, derived_manifest)
    chromatic_manifest = _resolve(root, chromatic_manifest)
    learned_manifest = _resolve(root, learned_manifest)
    learned_provenance_manifest = _resolve(root, learned_provenance_manifest)
    output_dir = _resolve(root, output_dir)
    learned = config.measurements.learned_formal
    snapshot = _resolve(root, Path(str(learned.model_snapshot_dir)))
    with recorded_run(
        root,
        root / "artifacts/runs",
        "prepare-generated-features",
        {
            "generation_manifest": str(generation_manifest),
            "derived_manifest": str(derived_manifest),
            "chromatic_manifest": str(chromatic_manifest),
            "learned_manifest": str(learned_manifest),
            "allow_unqualified_test_preparation": allow_unqualified_test_preparation,
            "qualification_decisions": decisions,
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            generation_manifest,
            prompt_path,
            attestation_path,
            *card_paths,
            snapshot / "config.json",
            snapshot / "diffusion_pytorch_model.safetensors",
        ],
        random_seeds={"learned_formal_base": int(learned.base_seed or 0)},
    ) as run:
        calls = [
            GenerationCallRecord.model_validate(row)
            for row in read_jsonl(generation_manifest)
        ]
        prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
        if preparation_bypass and any(not prompt.test_only for prompt in prompts):
            raise ValueError(
                "closed-gate preparation requires every frozen prompt to be test_only"
            )
        verify_generation_attestation(
            generation_manifest,
            attestation_path,
            prompt_path,
            calls,
            prompts,
            config.generation,
            root=root,
            qualification_card_paths=attestation_card_paths,
            qualification_contract_hashes=attestation_contract_hashes,
        )
        prompt_by_id = {row.prompt_id: row for row in prompts}
        expected_cells = {
            (prompt.prompt_id, model, repetition)
            for prompt in prompts
            for model in config.generation.models
            for repetition in range(config.generation.repetitions)
        }
        successful_by_cell = _generation_calls_for_preparation(
            calls,
            expected_cells,
            preparation_bypass=preparation_bypass,
        )
        selected_calls = [successful_by_cell[cell] for cell in sorted(expected_cells)]
        generation_manifest_sha256 = hash_file(generation_manifest)
        generation_attestation_sha256 = hash_file(attestation_path)
        reproductions: List[ReproductionRecord] = []
        call_by_reproduction: Dict[str, GenerationCallRecord] = {}
        for call in selected_calls:
            if not call.output_path or not call.output_sha256:
                raise ValueError(f"successful call lacks output provenance: {call.call_id}")
            reproduction_id = f"generated-{call.call_id}"
            reproduction = ReproductionRecord(
                reproduction_id=reproduction_id,
                canonical_work_id=f"generated-work-{call.call_id}",
                source_id=f"generated_{call.model}",
                source_url=call.endpoint,
                local_path=call.output_path,
                sha256=call.output_sha256,
                native_width=call.actual_width,
                native_height=call.actual_height,
                border_status="none",
                rights_status="unknown",
                rights_basis="test-only GPT Image output; no physical-artwork rights claim",
                acquisition_notes=(
                    f"prompt_id={call.prompt_id}; repetition={call.repetition}; "
                    f"model={call.model}"
                ),
                split="unassigned",
            )
            reproductions.append(reproduction)
            call_by_reproduction[reproduction_id] = call
        views = preprocess_reproductions(
            reproductions, config.preprocessing, root, output_dir
        )
        view_by_reproduction = {row.reproduction_id: row for row in views}
        artist_by_work: Dict[str, str] = {}
        origin_by_view: Dict[str, str] = {}
        model_by_view: Dict[str, str] = {}
        prompt_by_view: Dict[str, str] = {}
        repetition_by_view: Dict[str, int] = {}
        for reproduction in reproductions:
            call = call_by_reproduction[reproduction.reproduction_id]
            prompt = prompt_by_id[call.prompt_id]
            view = view_by_reproduction[reproduction.reproduction_id]
            if prompt.target_artist_id:
                artist_by_work[reproduction.canonical_work_id] = prompt.target_artist_id
            origin_by_view[view.derived_view_id] = "generated"
            model_by_view[view.derived_view_id] = call.model
            prompt_by_view[view.derived_view_id] = call.prompt_id
            repetition_by_view[view.derived_view_id] = call.repetition

        raw_chromatic = extract_chromatic_features(
            views,
            config.measurements.chromatic,
            root,
            artist_by_work=artist_by_work,
        )
        chromatic = []
        for row in raw_chromatic:
            call = call_by_reproduction[row.reproduction_id]
            if call.request_identity_sha256 is None or call.output_sha256 is None:
                raise ValueError(
                    f"generated call lacks attested identity: {call.call_id}"
                )
            provenance = {
                **row.extraction_metadata,
                "engineering_scope": "api_integration_test_only",
                "preparation_qualification_bypass": preparation_bypass,
                "generation_attestation_sha256": generation_attestation_sha256,
                "generation_manifest_sha256": generation_manifest_sha256,
                "generation_request_identity_sha256": call.request_identity_sha256,
                "generation_call_id": call.call_id,
                "generation_output_sha256": call.output_sha256,
            }
            chromatic.append(
                row.model_copy(
                    update={
                        "origin": "generated",
                        "model": model_by_view[row.derived_view_id],
                        "prompt_id": prompt_by_view[row.derived_view_id],
                        "repetition": repetition_by_view[row.derived_view_id],
                        "extraction_metadata": provenance,
                    }
                )
            )

        def progress(index: int, total: int) -> None:
            if index == 1 or index == total or index % 10 == 0:
                typer.echo(f"generated learned-formal {index}/{total}")

        learned_features, learned_provenance = extract_learned_formal_features(
            views,
            reproductions,
            learned,
            root,
            artist_by_work=artist_by_work,
            origin_by_view=origin_by_view,
            model_by_view=model_by_view,
            prompt_by_view=prompt_by_view,
            repetition_by_view=repetition_by_view,
            progress=progress,
        )
        learned_by_id = {row.feature_id: row for row in learned_features}
        stamped_learned: List[FeatureRow] = []
        stamped_provenance: List[Dict[str, object]] = []
        for metadata in learned_provenance:
            feature_id = str(metadata["feature_id"])
            row = learned_by_id[feature_id]
            call = call_by_reproduction[row.reproduction_id]
            if call.request_identity_sha256 is None or call.output_sha256 is None:
                raise ValueError(
                    f"generated call lacks attested identity: {call.call_id}"
                )
            provenance = {
                **metadata,
                "engineering_scope": "api_integration_test_only",
                "preparation_qualification_bypass": preparation_bypass,
                "generation_attestation_sha256": generation_attestation_sha256,
                "generation_manifest_sha256": generation_manifest_sha256,
                "generation_request_identity_sha256": call.request_identity_sha256,
                "generation_call_id": call.call_id,
                "generation_output_sha256": call.output_sha256,
            }
            stamped_learned.append(
                row.model_copy(update={"extraction_metadata": provenance})
            )
            stamped_provenance.append(provenance)
        learned_features = stamped_learned
        learned_provenance = stamped_provenance
        write_jsonl(reproduction_manifest, reproductions)
        write_jsonl(derived_manifest, views)
        write_jsonl(chromatic_manifest, chromatic)
        write_jsonl(learned_manifest, learned_features)
        write_jsonl(learned_provenance_manifest, learned_provenance)
        outputs = [
            reproduction_manifest,
            derived_manifest,
            chromatic_manifest,
            learned_manifest,
            learned_provenance_manifest,
        ]
        run.outputs.extend(str(path) for path in outputs)
        run.checkpoint_hashes["sd2_vae_weights"] = str(learned.model_weights_sha256)
        typer.echo(
            json.dumps(
                {
                    "generation_attempts": len(calls),
                    "generated_outputs": len(selected_calls),
                    "chromatic_features": len(chromatic),
                    "learned_formal_features": len(learned_features),
                },
                sort_keys=True,
            )
        )


@app.command("build-analysis-cells")
def build_analysis_cells_command(
    measurement: str = typer.Argument(..., help="chromatic or learned_formal"),
    real_feature_manifest: Path = typer.Argument(...),
    generated_feature_manifest: Path = typer.Argument(...),
    generation_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generation_calls.jsonl"), "--generation-manifest"
    ),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/analysis_cells.jsonl"), "--output-manifest"
    ),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Build frozen artist/model analysis cells from qualified features."""

    if measurement not in {"chromatic", "learned_formal"}:
        raise typer.BadParameter("measurement must be chromatic or learned_formal")
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    real_feature_manifest = _resolve(root, real_feature_manifest)
    generated_feature_manifest = _resolve(root, generated_feature_manifest)
    generation_manifest = _resolve(root, generation_manifest)
    output_manifest = _resolve(root, output_manifest)
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    attestation_path = _resolve(
        root, Path(str(config.generation.manifest_attestation))
    )
    evidence_hash, qualified_pca_hash, evidence_path = (
        _qualification_analysis_provenance(
            root, config, measurement, real_feature_manifest
        )
    )
    with recorded_run(
        root,
        root / "artifacts/runs",
        "build-analysis-cells",
        {
            "measurement": measurement,
            "real_feature_manifest": str(real_feature_manifest),
            "generated_feature_manifest": str(generated_feature_manifest),
            "output_manifest": str(output_manifest),
        },
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            real_feature_manifest,
            generated_feature_manifest,
            generation_manifest,
            attestation_path,
            canonical_path,
            reproduction_path,
            prompt_path,
            evidence_path,
        ],
    ) as run:
        real_features = [
            FeatureRow.model_validate(row) for row in read_jsonl(real_feature_manifest)
        ]
        generated_features = [
            FeatureRow.model_validate(row)
            for row in read_jsonl(generated_feature_manifest)
        ]
        canonical = [
            CanonicalWorkRecord.model_validate(row) for row in read_jsonl(canonical_path)
        ]
        reproductions = [
            ReproductionRecord.model_validate(row)
            for row in read_jsonl(reproduction_path)
        ]
        generation_calls, prompts = _verify_complete_generation_manifest(
            root,
            config,
            generation_manifest,
            attestation_path,
            prompt_path,
        )
        cells = build_analysis_cells(
            config,
            real_features,
            generated_features,
            canonical,
            reproductions,
            prompts,
            generation_calls,
            measurement,
            qualification_contract_hash=_qualification_contract_hash(
                root, config, measurement
            ),
            qualification_evidence_artifact_sha256=evidence_hash,
            real_feature_manifest_sha256=hash_file(real_feature_manifest),
            generated_feature_manifest_sha256=hash_file(generated_feature_manifest),
            generation_manifest_sha256=hash_file(generation_manifest),
            generation_attestation_sha256=hash_file(attestation_path),
            qualified_reference_transform_state_sha256=qualified_pca_hash,
            learned_protocol=(
                learned_formal_v2_protocol(config)
                if measurement == "learned_formal"
                else None
            ),
        )
        write_jsonl(output_manifest, cells)
        run.outputs.append(str(output_manifest))
        typer.echo(
            json.dumps(
                {"measurement": measurement, "cells": len(cells)}, sort_keys=True
            )
        )


@app.command("build-pilot-analysis-cells")
def build_pilot_analysis_cells_command(
    generation_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generation_calls.jsonl"), "--generation-manifest"
    ),
    real_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/chromatic_features.jsonl"), "--real-chromatic"
    ),
    generated_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/generated_chromatic_features.jsonl"),
        "--generated-chromatic",
    ),
    real_learned: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_features.jsonl"), "--real-learned"
    ),
    generated_learned: Path = typer.Option(
        Path("artifacts/pilot_1/generated_learned_formal_features.jsonl"),
        "--generated-learned",
    ),
    output_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/analysis_cells.jsonl"), "--output-manifest"
    ),
    config_path: Path = typer.Option(Path("configs/pilot_1/pilot.yaml"), "--config"),
    root: Path = typer.Option(Path(".")),
) -> None:
    """Build the complete two-measurement test-only pilot cell manifest."""

    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    paths = {
        "real_chromatic": _resolve(root, real_chromatic),
        "generated_chromatic": _resolve(root, generated_chromatic),
        "real_learned": _resolve(root, real_learned),
        "generated_learned": _resolve(root, generated_learned),
    }
    generation_manifest = _resolve(root, generation_manifest)
    output_manifest = _resolve(root, output_manifest)
    canonical_path = _resolve(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    attestation_path = _resolve(
        root, Path(str(config.generation.manifest_attestation))
    )
    qualification_provenance = {
        measurement: _qualification_analysis_provenance(
            root,
            config,
            measurement,
            paths[f"real_{measurement.split('_')[0]}"],
        )
        for measurement in config.measurements.required
    }
    with recorded_run(
        root,
        root / "artifacts/runs",
        "build-pilot-analysis-cells",
        {**{name: str(path) for name, path in paths.items()}, "output": str(output_manifest)},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            *paths.values(),
            generation_manifest,
            attestation_path,
            canonical_path,
            reproduction_path,
            prompt_path,
            *[value[2] for value in qualification_provenance.values()],
        ],
    ) as run:
        canonical = [
            CanonicalWorkRecord.model_validate(row) for row in read_jsonl(canonical_path)
        ]
        reproductions = [
            ReproductionRecord.model_validate(row)
            for row in read_jsonl(reproduction_path)
        ]
        generation_calls, prompts = _verify_complete_generation_manifest(
            root,
            config,
            generation_manifest,
            attestation_path,
            prompt_path,
        )
        generation_manifest_sha256 = hash_file(generation_manifest)
        generation_attestation_sha256 = hash_file(attestation_path)
        cells = []
        for measurement in ("chromatic", "learned_formal"):
            real_rows = [
                FeatureRow.model_validate(row)
                for row in read_jsonl(paths[f"real_{measurement.split('_')[0]}"])
            ]
            generated_rows = [
                FeatureRow.model_validate(row)
                for row in read_jsonl(paths[f"generated_{measurement.split('_')[0]}"])
            ]
            cells.extend(
                build_analysis_cells(
                    config,
                    real_rows,
                    generated_rows,
                    canonical,
                    reproductions,
                    prompts,
                    generation_calls,
                    measurement,
                    qualification_contract_hash=_qualification_contract_hash(
                        root, config, measurement
                    ),
                    qualification_evidence_artifact_sha256=(
                        qualification_provenance[measurement][0]
                    ),
                    real_feature_manifest_sha256=hash_file(
                        paths[f"real_{measurement.split('_')[0]}"]
                    ),
                    generated_feature_manifest_sha256=hash_file(
                        paths[f"generated_{measurement.split('_')[0]}"]
                    ),
                    generation_manifest_sha256=generation_manifest_sha256,
                    generation_attestation_sha256=generation_attestation_sha256,
                    qualified_reference_transform_state_sha256=(
                        qualification_provenance[measurement][1]
                    ),
                    learned_protocol=(
                        learned_formal_v2_protocol(config)
                        if measurement == "learned_formal"
                        else None
                    ),
                )
            )
        write_jsonl(output_manifest, cells)
        run.outputs.append(str(output_manifest))
        typer.echo(json.dumps({"cells": len(cells)}, sort_keys=True))


@app.command("analyze-pilot")
def analyze_pilot_command(
    cells_path: Path = typer.Argument(..., help="JSONL file of frozen analysis cells."),
    generation_manifest: Path = typer.Option(
        Path("artifacts/pilot_1/generation_calls.jsonl"), "--generation-manifest"
    ),
    real_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/chromatic_features.jsonl"), "--real-chromatic"
    ),
    generated_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/generated_chromatic_features.jsonl"),
        "--generated-chromatic",
    ),
    real_learned: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_features.jsonl"), "--real-learned"
    ),
    generated_learned: Path = typer.Option(
        Path("artifacts/pilot_1/generated_learned_formal_features.jsonl"),
        "--generated-learned",
    ),
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
    generation_manifest = _resolve(root, generation_manifest)
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    attestation_path = _resolve(
        root, Path(str(config.generation.manifest_attestation))
    )
    feature_paths = {
        "chromatic": (_resolve(root, real_chromatic), _resolve(root, generated_chromatic)),
        "learned_formal": (_resolve(root, real_learned), _resolve(root, generated_learned)),
    }
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    qualification_provenance_full = {
        measurement: _qualification_analysis_provenance(
            root, config, measurement, feature_paths[measurement][0]
        )
        for measurement in config.measurements.required
    }
    gate_open, decisions = qualification_gate(
        config.measurements.required, cards, _qualification_identities(root, config)
    )
    if not gate_open and not allow_unqualified_test_analysis:
        raise RuntimeError(
            "WP5 qualification gate is closed: "
            + ", ".join(f"{name}={status}" for name, status in decisions.items())
        )
    if gate_open and allow_unqualified_test_analysis:
        raise ValueError(
            "the qualification bypass is only valid while the scientific gate is closed"
        )
    if not gate_open and (
        config.purpose != "api_integration_test_only"
        or config.generation.mode != "test_only"
        or config.generation.scientific_claims_enabled is not False
    ):
        raise ValueError(
            "closed-gate analysis is restricted to the non-scientific test-only pilot"
        )
    with recorded_run(
        root,
        root / "artifacts/runs",
        "analyze-pilot",
        {"cells_path": str(cells_path), "qualification_bypass": allow_unqualified_test_analysis},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=[
            cells_path,
            generation_manifest,
            attestation_path,
            prompt_path,
            *[path for pair in feature_paths.values() for path in pair],
            *card_paths,
            *[value[2] for value in qualification_provenance_full.values()],
        ],
        random_seeds={"equal_sample_seed": config.analysis.equal_sample_seed},
    ) as run:
        _verify_complete_generation_manifest(
            root,
            config,
            generation_manifest,
            attestation_path,
            prompt_path,
        )
        cells = [AnalysisCell.model_validate(row) for row in read_jsonl(cells_path)]
        identities = _qualification_identities(root, config)
        feature_manifest_hashes = {
            measurement: (hash_file(paths[0]), hash_file(paths[1]))
            for measurement, paths in feature_paths.items()
        }
        qualification_provenance = {
            measurement: (values[0], values[1])
            for measurement, values in qualification_provenance_full.items()
        }
        validate_analysis_grid_provenance(
            config,
            cells,
            identities,
            feature_manifest_hashes,
            qualification_provenance,
            hash_file(generation_manifest),
            hash_file(attestation_path),
        )
        if not gate_open and any(
            not cell.preparation_qualification_bypass for cell in cells
        ):
            raise ValueError(
                "closed-gate engineering analysis requires generated features prepared "
                "with the explicit qualification bypass"
            )
        if gate_open and any(cell.preparation_qualification_bypass for cell in cells):
            raise ValueError(
                "open-gate analysis rejects features prepared through the closed-gate "
                "qualification bypass"
            )
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
    analysis_cells: Optional[Path] = typer.Option(None, "--analysis-cells"),
    real_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/chromatic_features.jsonl"), "--real-chromatic"
    ),
    generated_chromatic: Path = typer.Option(
        Path("artifacts/pilot_1/generated_chromatic_features.jsonl"),
        "--generated-chromatic",
    ),
    real_learned: Path = typer.Option(
        Path("artifacts/pilot_1/learned_formal_features.jsonl"), "--real-learned"
    ),
    generated_learned: Path = typer.Option(
        Path("artifacts/pilot_1/generated_learned_formal_features.jsonl"),
        "--generated-learned",
    ),
    output_dir: Path = typer.Option(Path("reports/pilot_0"), "--output-dir"),
    root: Path = typer.Option(Path(".")),
) -> None:
    root = root.resolve()
    config, resolved_config_path = _resolved_config(root, config_path)
    output_dir = _resolve(root, output_dir)
    cards = _existing_cards(root, config)
    card_paths = _existing_card_paths(root, config)
    prompt_path = _resolve(root, Path(config.generation.prompt_manifest))
    attestation_path = _resolve(
        root, Path(str(config.generation.manifest_attestation))
    )
    feature_paths = {
        "chromatic": (_resolve(root, real_chromatic), _resolve(root, generated_chromatic)),
        "learned_formal": (_resolve(root, real_learned), _resolve(root, generated_learned)),
    }
    qualification_provenance_full = {
        measurement: _qualification_analysis_provenance(
            root, config, measurement, feature_paths[measurement][0]
        )
        for measurement in config.measurements.required
    }
    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
    calls: List[GenerationCallRecord] = []
    cells: List[AnalysisCell] = []
    results: List[AnalysisResult] = []
    input_paths: List[Path] = [
        *card_paths,
        *_qualification_evidence_paths(root, cards),
        prompt_path,
    ]
    generation_path: Optional[Path] = None
    analysis_path: Optional[Path] = None
    cells_path: Optional[Path] = None
    if config.pilot_id == "pilot_1" and (
        generation_manifest is None
        or analysis_manifest is None
        or analysis_cells is None
    ):
        raise ValueError(
            "pilot_1 report requires generation, analysis-cell, and analysis-result manifests"
        )
    if generation_manifest:
        generation_path = _resolve(root, generation_manifest)
        calls, prompts = _verify_complete_generation_manifest(
            root,
            config,
            generation_path,
            attestation_path,
            prompt_path,
        )
        input_paths.extend([generation_path, attestation_path])
    if analysis_cells:
        cells_path = _resolve(root, analysis_cells)
        input_paths.append(cells_path)
        cells = [AnalysisCell.model_validate(row) for row in read_jsonl(cells_path)]
    if analysis_manifest:
        analysis_path = _resolve(root, analysis_manifest)
        input_paths.append(analysis_path)
        results = [AnalysisResult.model_validate(row) for row in read_jsonl(analysis_path)]
    generation_runs: List[tuple[RunRecord, str]] = []
    artist_free_control_diagnostics: Optional[Dict[str, object]] = None
    generation_attestation_evidence: Optional[Dict[str, object]] = None
    if config.pilot_id == "pilot_1":
        assert generation_path is not None
        assert cells_path is not None
        assert analysis_path is not None
        feature_manifest_hashes = {
            measurement: (hash_file(paths[0]), hash_file(paths[1]))
            for measurement, paths in feature_paths.items()
        }
        qualification_provenance = {
            measurement: (values[0], values[1])
            for measurement, values in qualification_provenance_full.items()
        }
        validation_args = (
            config,
            _qualification_identities(root, config),
            feature_manifest_hashes,
            qualification_provenance,
            hash_file(generation_path),
            hash_file(attestation_path),
        )
        validate_analysis_grid_provenance(
            validation_args[0], cells, *validation_args[1:]
        )
        validate_analysis_grid_provenance(
            validation_args[0], results, *validation_args[1:]
        )
        cells_by_id = {cell.cell_id: cell for cell in cells}
        if len(cells_by_id) != len(cells):
            raise ValueError("analysis-cell identifiers must be unique")
        results_by_id = {result.cell_id: result for result in results}
        if len(results_by_id) != len(results) or set(results_by_id) != set(cells_by_id):
            raise ValueError("analysis results do not match the exact analysis-cell IDs")
        for cell_id, result in results_by_id.items():
            cell = cells_by_id[cell_id]
            if result.analysis_cell_sha256 != stable_hash(cell.model_dump(mode="json")):
                raise ValueError(f"analysis result is not bound to its exact cell: {cell_id}")
            if (
                result.subsample_draws != config.analysis.equal_sample_draws
                or result.confidence_level != config.analysis.confidence_level
            ):
                raise ValueError(f"analysis settings are stale: {cell_id}")
            recomputed = analyze_cell(
                cell,
                seed=config.analysis.equal_sample_seed,
                draws=config.analysis.equal_sample_draws,
                confidence_level=config.analysis.confidence_level,
            )
            if stable_hash(recomputed.model_dump(mode="json")) != stable_hash(
                result.model_dump(mode="json")
            ):
                raise ValueError(f"analysis result does not recompute exactly: {cell_id}")
        input_paths.extend(
            [
                *[path for pair in feature_paths.values() for path in pair],
                *[value[2] for value in qualification_provenance_full.values()],
            ]
        )
        generated_feature_rows = {
            measurement: [
                FeatureRow.model_validate(row)
                for row in read_jsonl(paths[1])
            ]
            for measurement, paths in feature_paths.items()
        }
        artist_free_control_diagnostics = build_artist_free_control_diagnostics(
            config,
            prompts,
            generated_feature_rows,
            {
                measurement: hash_file(paths[1])
                for measurement, paths in feature_paths.items()
            },
        )
        attestation = read_json(attestation_path)
        if not isinstance(attestation, dict):
            raise ValueError("generation attestation must be a JSON object")
        generation_attestation_evidence = attestation
        for item in attestation.get("run_evidence", []):
            run_path = _resolve(root, Path(str(item["run_record_path"])))
            observed_hash = hash_file(run_path)
            if observed_hash != item.get("run_record_sha256"):
                raise ValueError(f"generation run record hash mismatch: {run_path}")
            generation_runs.append(
                (RunRecord.model_validate(read_json(run_path)), observed_hash)
            )
            input_paths.append(run_path)
    with recorded_run(
        root,
        root / "artifacts/runs",
        "report-pilot",
        {"output_dir": str(output_dir)},
        config_path=resolved_config_path,
        resolved_config=config.model_dump(mode="json"),
        input_paths=input_paths,
    ) as run:
        snapshot_paths: List[Path] = []
        snapshot_hashes: Dict[str, str] = {}
        if config.pilot_id == "pilot_1":
            snapshot_paths, snapshot_hashes = write_pilot_evidence_snapshots(
                output_dir,
                root,
                calls,
                generation_runs,
                cells,
                results,
            )
            control_path = output_dir / "evidence" / "artist_free_control_diagnostics.json"
            assert artist_free_control_diagnostics is not None
            write_json(control_path, artist_free_control_diagnostics)
            snapshot_paths.append(control_path)
            snapshot_hashes[str(control_path.relative_to(output_dir))] = hash_file(
                control_path
            )
        markdown, summary = build_pilot_report(
            config,
            cards,
            calls,
            results,
            prompts=prompts,
            qualification_identities=_qualification_identities(root, config),
            evidence_snapshot_hashes=snapshot_hashes,
            artist_free_control_diagnostics=artist_free_control_diagnostics,
            generation_attestation=generation_attestation_evidence,
        )
        outputs = write_pilot_report(output_dir, markdown, summary, config)
        outputs.extend(snapshot_paths)
        if calls:
            outputs.append(
                write_generation_contact_sheet(
                    calls,
                    root,
                    _resolve(root, Path(config.generation.output_dir))
                    / "contact_sheet.jpg",
                )
            )
        run.outputs.extend(str(path) for path in outputs)
        typer.echo(
            json.dumps(
                {
                    "report": str(outputs[0]),
                    "gate_open": summary["qualification_gate"]["allowed"],
                }
            )
        )
    if config.pilot_id == "pilot_1":
        all_pilot_runs: List[tuple[RunRecord, str]] = []
        for run_path in sorted((root / "artifacts/runs").glob("*.json")):
            candidate = RunRecord.model_validate(read_json(run_path))
            resolved = candidate.resolved_config or {}
            if resolved.get("pilot_id") == config.pilot_id:
                all_pilot_runs.append((candidate, hash_file(run_path)))
        reproduction_path = _resolve(root, Path(config.corpus.reproduction_manifest))
        reproductions = [
            ReproductionRecord.model_validate(row)
            for row in read_jsonl(reproduction_path)
        ]
        audit_paths = [
            *input_paths,
            *outputs,
            reproduction_path,
            _resolve(root, Path(config.corpus.canonical_manifest)),
            *[
                _resolve(root, Path(call.output_path))
                for call in calls
                if call.output_path
            ],
            *[_resolve(root, Path(row.local_path)) for row in reproductions],
            *_existing_run_output_paths(root, all_pilot_runs),
        ]
        published = write_pilot_artifact_index(
            output_dir, root, audit_paths, all_pilot_runs
        )
        typer.echo(
            json.dumps(
                {
                    "artifact_index": str(published[1]),
                    "evidence_anchor": str(published[2]),
                    "run_records": len(all_pilot_runs),
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
