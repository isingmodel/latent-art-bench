"""Frozen orchestration for the two pilot_1 qualification measurements.

The qualification contract hashes this module.  Keep protocol construction,
probe selection, evaluator invocation, and evidence mapping here rather than in
the general CLI so every result-changing orchestration change invalidates the
corresponding cards.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Sequence, Tuple, TypeVar, cast

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.chromatic_v2 import (
    ChromaticV2Protocol,
    ChromaticV2QualificationResult,
    evaluate_chromatic_v2,
)
from latent_art_bench.evaluation.contracts import qualification_contract
from latent_art_bench.evaluation.learned_formal_v2 import (
    LearnedFormalDeterminismProbe,
    LearnedFormalV2Protocol,
    LearnedFormalV2QualificationResult,
    build_determinism_probe,
    evaluate_learned_formal_v2,
)
from latent_art_bench.features.learned_formal import (
    LoadedSD2VAE,
    extract_learned_formal,
)
from latent_art_bench.features.learned_pipeline import load_configured_vae
from latent_art_bench.io import hash_file, stable_hash, write_json
from latent_art_bench.manifests import parse_manifest
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    DerivedViewRecord,
    FeatureRow,
    QualificationEvidence,
    ReproductionRecord,
)

QualificationManifestRow = TypeVar(
    "QualificationManifestRow",
    CanonicalWorkRecord,
    ReproductionRecord,
    DerivedViewRecord,
    FeatureRow,
)


@dataclass(frozen=True)
class ChromaticQualificationRun:
    result: ChromaticV2QualificationResult
    evidence: QualificationEvidence


@dataclass(frozen=True)
class LearnedFormalQualificationRun:
    result: LearnedFormalV2QualificationResult
    evidence: QualificationEvidence
    determinism_probe_count: int
    determinism_probe_sources: Tuple[str, ...]


def load_exact_qualification_manifest(
    path: Path,
    expected_type: type[QualificationManifestRow],
) -> List[QualificationManifestRow]:
    """Load a qualification input without silently discarding mixed row types."""

    records = parse_manifest(path)
    unexpected = [
        f"line {index}: {record.record_type}"
        for index, record in enumerate(records, start=1)
        if type(record) is not expected_type
    ]
    if unexpected:
        raise ValueError(
            f"qualification manifest {path} must contain only "
            f"{expected_type.__name__} rows; found " + ", ".join(unexpected)
        )
    if not records:
        raise ValueError(f"qualification manifest is empty: {path}")
    return [cast(QualificationManifestRow, record) for record in records]


def _relative_artifact_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _resolve_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def chromatic_v2_protocol(config: PilotConfig) -> ChromaticV2Protocol:
    qualification = config.qualification
    if qualification.qualification_protocol_version != "real-only-qualification-v3":
        raise ValueError("pilot_1 requires real-only-qualification-v3")
    return ChromaticV2Protocol(
        matched_input_long_side=qualification.matched_input_long_side,
        canonical_long_side=qualification.canonical_chromatic_long_side,
        jpeg_quality=qualification.perturbation_jpeg_quality,
        jpeg_subsampling=(
            2 if qualification.perturbation_jpeg_subsampling == "4:2:0" else -1
        ),
        perturbation_ratio_max=(
            qualification.perturbation_to_within_artist_median_ratio_max
        ),
        reproduction_ratio_max=(
            qualification.reproduction_to_within_artist_median_ratio_max
        ),
        artist_prediction_min_balanced_accuracy=(
            qualification.artist_prediction_min_balanced_accuracy
        ),
        source_prediction_max_balanced_accuracy=(
            qualification.source_prediction_max_balanced_accuracy
        ),
        leave_source_out_artist_min_balanced_accuracy=(
            qualification.leave_source_out_artist_min_balanced_accuracy
        ),
        bootstrap_draws=qualification.bootstrap_draws,
        confidence_level=qualification.confidence_level,
        random_seed=qualification.random_seed,
    )


def learned_formal_v2_protocol(config: PilotConfig) -> LearnedFormalV2Protocol:
    learned = config.measurements.learned_formal
    _, feature_config_hash = config.measurement_identities()["learned_formal"]
    return LearnedFormalV2Protocol(
        feature_version=learned.feature_version,
        expected_base_seed=learned.base_seed,
        expected_device=learned.device,
        expected_source_input_role=learned.source_input_role,
        expected_source_preprocessing_policy=learned.source_preprocessing_policy,
        expected_source_repository=learned.source_repository,
        expected_source_revision=learned.source_revision,
        expected_model_repository=learned.model_repository,
        expected_model_revision=learned.model_revision,
        expected_model_config_sha256=learned.model_config_sha256,
        expected_model_weights_sha256=learned.model_weights_sha256,
        expected_opencv_version=learned.opencv_version,
        expected_opencv_build_sha256=learned.opencv_build_sha256,
        expected_pillow_version=learned.pillow_version,
        expected_jpeg_codec_version=learned.jpeg_codec_version,
        expected_python_version=learned.python_version,
        expected_platform_system=learned.platform_system,
        expected_platform_release=learned.platform_release,
        expected_platform_machine=learned.platform_machine,
        expected_numpy_version=learned.numpy_version,
        expected_torch_version=learned.torch_version,
        expected_diffusers_version=learned.diffusers_version,
        expected_torch_mps_built=learned.torch_mps_built,
        expected_torch_mps_available=learned.torch_mps_available,
        expected_feature_config_hash=feature_config_hash,
        pca_variance_target=learned.pca_variance_target,
        pca_max_components=learned.pca_max_components,
    )


def evaluate_chromatic_qualification(
    config: PilotConfig,
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    root: Path,
) -> ChromaticV2QualificationResult:
    return evaluate_chromatic_v2(
        canonical,
        reproductions,
        config.measurements.chromatic,
        config.preprocessing,
        root,
        chromatic_v2_protocol(config),
    )


def chromatic_qualification_evidence(
    config: PilotConfig,
    result: ChromaticV2QualificationResult,
    *,
    qualification_contract_hash: str,
    qualification_artifact_sha256: str,
    qualification_artifact_path: str,
) -> QualificationEvidence:
    direct_400 = result.direct_resolution_stability.get("400")
    stable = bool(
        result.lossless_processing_deterministic
        and direct_400
        and direct_400.supported
        and result.reproduction_stability.supported
    )
    classification = result.classification
    artist_signal = bool(
        classification.held_out_artist_balanced_accuracy is not None
        and classification.held_out_artist_balanced_accuracy
        >= config.qualification.artist_prediction_min_balanced_accuracy
    )
    source_controlled = bool(
        classification.held_out_source_balanced_accuracy is not None
        and classification.held_out_source_balanced_accuracy
        <= config.qualification.source_prediction_max_balanced_accuracy
        and classification.nested_leave_source_out_artist_balanced_accuracy is not None
        and classification.nested_leave_source_out_artist_balanced_accuracy
        >= config.qualification.leave_source_out_artist_min_balanced_accuracy
        and classification.every_nested_source_fold_meets_minimum
    )
    return QualificationEvidence(
        measurement="chromatic",
        qualification_result_status=result.status,
        feature_version=config.measurements.chromatic.feature_version,
        feature_config_hash=result.feature_config_sha256,
        qualification_contract_hash=qualification_contract_hash,
        qualification_result_sha256=result.result_sha256,
        evidence_artifact_sha256=qualification_artifact_sha256,
        real_work_count=result.primary_work_count,
        reproduction_pair_count=result.independent_alternate_work_count,
        source_behavior_recovered=result.source_behavior_recovered,
        stable_within_frozen_margin=stable,
        held_out_artist_signal_valid=artist_signal,
        source_confounding_controlled=source_controlled,
        conditional_domains=result.conditional_domains,
        supported_scope=result.supported_scope,
        evidence_paths=[qualification_artifact_path],
        notes=[
            "The Q85 4:2:0 branch remains an unsupported diagnostic; it is not part "
            "of a scientific pass.",
            *[f"Unsupported: {value}" for value in result.unsupported_conditions],
        ],
    )


def run_chromatic_qualification(
    config: PilotConfig,
    root: Path,
    artifact_path: Path,
    evidence_path: Path,
) -> ChromaticQualificationRun:
    """Load, evaluate, and bind the complete chromatic qualification run."""

    root = root.resolve()
    artifact_path = _resolve_path(root, artifact_path)
    evidence_path = _resolve_path(root, evidence_path)
    canonical_path = _resolve_path(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve_path(root, Path(config.corpus.reproduction_manifest))
    qualification_contract_hash = qualification_contract(
        config, "chromatic", root
    )[0]
    canonical = load_exact_qualification_manifest(
        canonical_path, CanonicalWorkRecord
    )
    reproductions = load_exact_qualification_manifest(
        reproduction_path, ReproductionRecord
    )
    result = evaluate_chromatic_qualification(
        config,
        canonical,
        reproductions,
        root,
    )
    write_json(artifact_path, result)
    evidence = chromatic_qualification_evidence(
        config,
        result,
        qualification_contract_hash=qualification_contract_hash,
        qualification_artifact_sha256=hash_file(artifact_path),
        qualification_artifact_path=_relative_artifact_path(artifact_path, root),
    )
    write_json(evidence_path, evidence)
    return ChromaticQualificationRun(result=result, evidence=evidence)


def validate_learned_feature_view_links(
    features: Sequence[FeatureRow], views: Sequence[DerivedViewRecord]
) -> None:
    view_by_id = {view.derived_view_id: view for view in views}
    if len(view_by_id) != len(views):
        raise ValueError("learned-formal derived-view identifiers must be unique")
    for feature in features:
        view = view_by_id.get(feature.derived_view_id)
        if view is None or view.reproduction_id != feature.reproduction_id:
            raise ValueError(
                f"learned feature has stale derived-view linkage: {feature.feature_id}"
            )
        metadata = feature.extraction_metadata
        if (
            metadata.get("linkage_derived_view_id") != view.derived_view_id
            or metadata.get("linkage_derived_view_sha256") != view.output_sha256
        ):
            raise ValueError(
                f"learned feature provenance does not bind its view: {feature.feature_id}"
            )


def select_learned_determinism_probe_rows(
    features: Sequence[FeatureRow],
    reproductions: Sequence[ReproductionRecord],
    probe_count: int,
) -> Tuple[List[FeatureRow], List[str]]:
    reproduction_by_id = {row.reproduction_id: row for row in reproductions}
    if len(reproduction_by_id) != len(reproductions):
        raise ValueError("learned-formal reproduction identifiers must be unique")
    primary_features = [
        row
        for row in features
        if reproduction_by_id[row.reproduction_id].source_id
        != "cma_alternate_capture"
    ]
    selected: List[FeatureRow] = []
    represented_artists = set()
    represented_sources = set()
    source_ids = sorted(
        {reproduction_by_id[row.reproduction_id].source_id for row in primary_features}
    )
    for source_id in source_ids:
        candidates = sorted(
            (
                row
                for row in primary_features
                if reproduction_by_id[row.reproduction_id].source_id == source_id
            ),
            key=lambda item: (
                item.artist_id in represented_artists,
                str(item.artist_id),
                item.canonical_work_id,
            ),
        )
        if candidates:
            chosen = candidates[0]
            selected.append(chosen)
            represented_artists.add(chosen.artist_id)
            represented_sources.add(source_id)
        if len(selected) >= probe_count:
            break
    for row in sorted(primary_features, key=lambda item: item.canonical_work_id):
        if len(selected) >= probe_count:
            break
        if row not in selected:
            selected.append(row)
    if len(selected) != probe_count:
        raise ValueError(
            f"learned-formal qualification requires {probe_count} determinism probes"
        )
    return selected, sorted(represented_sources)


def build_learned_determinism_probes(
    selected_rows: Sequence[FeatureRow],
    reproductions: Sequence[ReproductionRecord],
    loaded_vae: LoadedSD2VAE,
    config: PilotConfig,
    root: Path,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> List[LearnedFormalDeterminismProbe]:
    reproduction_by_id = {row.reproduction_id: row for row in reproductions}
    learned = config.measurements.learned_formal
    probes = []
    for index, row in enumerate(selected_rows, start=1):
        reproduction = reproduction_by_id[row.reproduction_id]
        image_path = Path(reproduction.local_path)
        if not image_path.is_absolute():
            image_path = root / image_path
        first = extract_learned_formal(
            image_path,
            loaded_vae,
            policy=str(learned.sampling_policy),
            base_seed=int(learned.base_seed or 0),
            device=str(learned.device),
        )
        repeated = extract_learned_formal(
            image_path,
            loaded_vae,
            policy=str(learned.sampling_policy),
            base_seed=int(learned.base_seed or 0),
            device=str(learned.device),
        )
        probes.append(build_determinism_probe(row.reproduction_id, first, repeated))
        if progress is not None:
            progress(index, len(selected_rows))
    return probes


def evaluate_learned_qualification(
    config: PilotConfig,
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    features: Sequence[FeatureRow],
    determinism_probes: Sequence[LearnedFormalDeterminismProbe],
) -> LearnedFormalV2QualificationResult:
    neighbors = {
        artist.artist_id: artist.neighbor_artist_id
        for artist in config.corpus.selected_artists
    }
    return evaluate_learned_formal_v2(
        canonical,
        reproductions,
        features,
        config.qualification,
        neighbors,
        determinism_probes,
        learned_formal_v2_protocol(config),
    )


def learned_qualification_evidence(
    config: PilotConfig,
    result: LearnedFormalV2QualificationResult,
    *,
    qualification_contract_hash: str,
    qualification_artifact_sha256: str,
    qualification_artifact_path: str,
    input_feature_manifest_sha256: str,
    model_verification_path: str,
) -> QualificationEvidence:
    learned = config.measurements.learned_formal
    return QualificationEvidence(
        measurement="learned_formal",
        qualification_result_status=result.status,
        feature_version=learned.feature_version,
        feature_config_hash=result.feature_config_sha256,
        qualification_contract_hash=qualification_contract_hash,
        qualification_result_sha256=result.result_sha256,
        evidence_artifact_sha256=qualification_artifact_sha256,
        input_feature_manifest_sha256=input_feature_manifest_sha256,
        real_work_count=result.primary_work_count,
        reproduction_pair_count=result.independent_alternate_work_count,
        source_behavior_recovered=result.source_behavior_recovered,
        stable_within_frozen_margin=result.stable_within_frozen_margin,
        held_out_artist_signal_valid=result.held_out_artist_signal_valid,
        source_confounding_controlled=result.source_confounding_controlled,
        conditional_domains=result.conditional_limitations,
        supported_scope=result.supported_scope,
        evidence_paths=[qualification_artifact_path, model_verification_path],
        notes=[
            *[f"Unsupported: {value}" for value in result.unsupported_conditions],
            "The VAE-only weights were independently verified bit-for-bit against the "
            "recovered full 512-base-ema.ckpt first-stage state.",
        ],
    )


def run_learned_formal_qualification(
    config: PilotConfig,
    root: Path,
    feature_manifest: Path,
    derived_manifest: Path,
    artifact_path: Path,
    evidence_path: Path,
    *,
    determinism_probe_count: int | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> LearnedFormalQualificationRun:
    """Run the complete path-bound learned-formal qualification sequence."""

    root = root.resolve()
    feature_manifest = _resolve_path(root, feature_manifest)
    derived_manifest = _resolve_path(root, derived_manifest)
    artifact_path = _resolve_path(root, artifact_path)
    evidence_path = _resolve_path(root, evidence_path)
    canonical_path = _resolve_path(root, Path(config.corpus.canonical_manifest))
    reproduction_path = _resolve_path(root, Path(config.corpus.reproduction_manifest))
    qualification_contract_hash = qualification_contract(
        config, "learned_formal", root
    )[0]

    configured_probe_count = config.qualification.learned_determinism_probe_count
    if configured_probe_count is None:
        raise ValueError("learned-formal qualification lacks a frozen probe count")
    if (
        determinism_probe_count is not None
        and determinism_probe_count != configured_probe_count
    ):
        raise ValueError(
            "determinism probe count must match the frozen qualification config"
        )
    probe_count = configured_probe_count

    canonical = load_exact_qualification_manifest(
        canonical_path, CanonicalWorkRecord
    )
    reproductions = load_exact_qualification_manifest(
        reproduction_path, ReproductionRecord
    )
    features = load_exact_qualification_manifest(feature_manifest, FeatureRow)
    views = load_exact_qualification_manifest(derived_manifest, DerivedViewRecord)
    validate_learned_feature_view_links(features, views)

    selected_probes, represented_sources = select_learned_determinism_probe_rows(
        features, reproductions, probe_count
    )
    loaded_vae = load_configured_vae(config.measurements.learned_formal, root)
    determinism_probes = build_learned_determinism_probes(
        selected_probes,
        reproductions,
        loaded_vae,
        config,
        root,
        progress=progress,
    )
    result = evaluate_learned_qualification(
        config, canonical, reproductions, features, determinism_probes
    )
    write_json(artifact_path, result)

    model_verification = config.measurements.learned_formal.model_verification_report
    if model_verification is None:
        raise ValueError("learned-formal qualification lacks model verification evidence")
    model_verification_path = _resolve_path(root, Path(model_verification))
    evidence = learned_qualification_evidence(
        config,
        result,
        qualification_contract_hash=qualification_contract_hash,
        qualification_artifact_sha256=hash_file(artifact_path),
        qualification_artifact_path=_relative_artifact_path(artifact_path, root),
        input_feature_manifest_sha256=hash_file(feature_manifest),
        model_verification_path=_relative_artifact_path(
            model_verification_path, root
        ),
    )
    write_json(evidence_path, evidence)
    return LearnedFormalQualificationRun(
        result=result,
        evidence=evidence,
        determinism_probe_count=len(determinism_probes),
        determinism_probe_sources=tuple(sorted(represented_sources)),
    )


def orchestration_sha256() -> str:
    """Stable semantic marker used by regression tests and evidence reviews."""

    return stable_hash(
        {
            "chromatic_protocol": ChromaticV2Protocol().model_dump(mode="json"),
            "learned_protocol": LearnedFormalV2Protocol().model_dump(mode="json"),
        }
    )
