from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pytest

from latent_art_bench.config import QualificationConfig
from latent_art_bench.evaluation.learned_formal_v2 import (
    CONDITIONAL_LIMITATIONS,
    FEATURE_NAME,
    FEATURE_VERSION,
    RAW_DIMENSION,
    LearnedFormalV2Protocol,
    bootstrap_distance_ratio,
    build_determinism_probe,
    evaluate_learned_formal_v2,
    evaluate_source_behavior,
    evaluate_source_domain_eligibility,
    group_independent_alternate_distances,
    nested_leave_source_out_pca_artist_accuracy,
    prepare_real_feature_rows,
)
from latent_art_bench.features.learned_formal import (
    SOURCE_REPLICATION_POLICY,
    SOURCE_REVISION,
    LearnedFormalResult,
    learned_formal_vector_sha256,
)
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    FeatureRow,
    ReproductionRecord,
)

CONFIG_HASH = hashlib.sha256(b"synthetic-learned-formal-config").hexdigest()


@dataclass
class SyntheticCorpus:
    canonical: List[CanonicalWorkRecord]
    reproductions: List[ReproductionRecord]
    features: List[FeatureRow]
    primary_vectors: np.ndarray
    primary_artist_ids: List[str]
    primary_source_ids: List[str]
    primary_work_ids: List[str]
    primary_reproduction_ids: List[str]


def _thresholds() -> QualificationConfig:
    return QualificationConfig(
        required_before_scientific_generation=True,
        cards=[],
        source_prediction_max_balanced_accuracy=0.55,
        artist_prediction_min_balanced_accuracy=0.8,
        leave_source_out_artist_min_balanced_accuracy=0.8,
        reproduction_to_within_artist_median_ratio_max=0.5,
        perturbation_to_within_artist_median_ratio_max=0.5,
        perturbation_long_side=256,
        perturbation_jpeg_quality=85,
        random_seed=20260830,
        bootstrap_draws=500,
        confidence_level=0.95,
        require_bootstrap_upper_bound=True,
    )


def _vector(
    artist_id: str,
    source_id: str,
    work_offset: float,
    alternate_offset: float = 0.0,
) -> np.ndarray:
    vector = np.zeros(RAW_DIMENSION, dtype=np.float32)
    vector[0] = (-10.0 if artist_id == "artist_a" else 10.0) + work_offset
    vector[1] = work_offset * 0.05
    vector[2] = -0.2 if source_id == "museum_a" else 0.2
    vector[0] += alternate_offset
    return vector


def _canonical(work_id: str, artist_id: str, split: str) -> CanonicalWorkRecord:
    return CanonicalWorkRecord(
        canonical_work_id=work_id,
        artist_id=artist_id,
        artist_name=artist_id.replace("_", " ").title(),
        title=f"Synthetic {work_id}",
        attribution_status="confirmed",
        public_domain_status="confirmed",
        split=split,
    )


def _reproduction(
    reproduction_id: str,
    work_id: str,
    source_id: str,
    split: str,
) -> ReproductionRecord:
    return ReproductionRecord(
        reproduction_id=reproduction_id,
        canonical_work_id=work_id,
        source_id=source_id,
        local_path=f"/synthetic/{reproduction_id}.png",
        sha256=hashlib.sha256(reproduction_id.encode("utf-8")).hexdigest(),
        native_width=512,
        native_height=512,
        split=split,
    )


def _content_seed(seed_basis_sha256: str, base_seed: int = 20260830) -> int:
    digest = hashlib.sha256()
    digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
    digest.update(base_seed.to_bytes(8, "big", signed=False))
    digest.update(bytes.fromhex(seed_basis_sha256))
    return int.from_bytes(digest.digest()[:8], "big", signed=False) & ((1 << 63) - 1)


def _extractor_metadata(
    reproduction: ReproductionRecord,
    vector: np.ndarray,
) -> Dict[str, object]:
    protocol = LearnedFormalV2Protocol()
    seed_basis = hashlib.sha256(
        f"resized-rgb:{reproduction.reproduction_id}".encode("utf-8")
    ).hexdigest()
    assert reproduction.sha256 is not None
    return {
        "feature_version": FEATURE_VERSION,
        "representation_role": protocol.expected_representation_role,
        "policy": SOURCE_REPLICATION_POLICY,
        "seed": _content_seed(seed_basis),
        "seed_strategy": protocol.expected_seed_strategy,
        "base_seed": protocol.expected_base_seed,
        "seed_basis_sha256": seed_basis,
        "input_size": [512, 512],
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": [4, 64, 64],
        "latent_scale": 0.18215,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": "C",
        "vector_length": RAW_DIMENSION,
        "device": protocol.expected_device,
        "dtype": "float32",
        "vector_sha256": learned_formal_vector_sha256(vector),
        "source_input_role": protocol.expected_source_input_role,
        "source_preprocessing_policy": protocol.expected_source_preprocessing_policy,
        "source_file_sha256": reproduction.sha256,
        "source_extension": ".png",
        "intermediate_payload_sha256": hashlib.sha256(
            f"intermediate:{reproduction.reproduction_id}".encode("utf-8")
        ).hexdigest(),
        "intermediate_encoding": "png",
        "opencv_version": protocol.expected_opencv_version,
        "opencv_build_sha256": protocol.expected_opencv_build_sha256,
        "pillow_version": protocol.expected_pillow_version,
        "jpeg_codec_version": protocol.expected_jpeg_codec_version,
        "python_version": protocol.expected_python_version,
        "platform_system": protocol.expected_platform_system,
        "platform_release": protocol.expected_platform_release,
        "platform_machine": protocol.expected_platform_machine,
        "numpy_version": protocol.expected_numpy_version,
        "torch_version": protocol.expected_torch_version,
        "diffusers_version": protocol.expected_diffusers_version,
        "torch_mps_built": protocol.expected_torch_mps_built,
        "torch_mps_available": protocol.expected_torch_mps_available,
        "source_repository": "https://github.com/aljinny/art-history",
        "source_revision": SOURCE_REVISION,
        "source_checkout_verified": True,
        "model_repository": protocol.expected_model_repository,
        "model_revision": protocol.expected_model_revision,
        "config_sha256": protocol.expected_model_config_sha256,
        "weights_sha256": protocol.expected_model_weights_sha256,
        "artifacts_verified": True,
    }


def _feature(
    reproduction: ReproductionRecord,
    artist_id: str,
    vector: np.ndarray,
) -> FeatureRow:
    feature_id = f"feature_{reproduction.reproduction_id}"
    derived_view_id = f"view_{reproduction.reproduction_id}"
    vector = np.asarray(vector, dtype=np.float32)
    assert reproduction.sha256 is not None
    extraction_metadata = {
        "record_type": "learned_formal_extraction",
        "schema_version": "2.0",
        "feature_id": feature_id,
        "linkage_derived_view_id": derived_view_id,
        "linkage_derived_view_sha256": hashlib.sha256(
            derived_view_id.encode("utf-8")
        ).hexdigest(),
        "input_role": "original_reproduction_file",
        "input_path": reproduction.local_path,
        "input_sha256": reproduction.sha256,
        "feature_config_hash": CONFIG_HASH,
        **_extractor_metadata(reproduction, vector),
    }
    return FeatureRow(
        feature_id=feature_id,
        derived_view_id=derived_view_id,
        reproduction_id=reproduction.reproduction_id,
        canonical_work_id=reproduction.canonical_work_id,
        artist_id=artist_id,
        origin="real",
        split=reproduction.split,
        feature_name=FEATURE_NAME,
        feature_version=FEATURE_VERSION,
        feature_config_hash=CONFIG_HASH,
        vector=vector.tolist(),
        scalars={},
        extraction_metadata=extraction_metadata,
        status="ok",
    )


def _synthetic_corpus() -> SyntheticCorpus:
    canonical: List[CanonicalWorkRecord] = []
    reproductions: List[ReproductionRecord] = []
    features: List[FeatureRow] = []
    primary_vectors: List[np.ndarray] = []
    primary_artist_ids: List[str] = []
    primary_source_ids: List[str] = []
    primary_work_ids: List[str] = []
    primary_reproduction_ids: List[str] = []

    held_work_ids: List[str] = []
    for artist_id in ("artist_a", "artist_b"):
        for source_id in ("museum_a", "museum_b"):
            for repetition, work_offset in enumerate((-0.3, 0.3)):
                work_id = f"train_{artist_id}_{source_id}_{repetition}"
                reproduction_id = f"primary_{work_id}"
                work = _canonical(work_id, artist_id, "train")
                reproduction = _reproduction(reproduction_id, work_id, source_id, "train")
                vector = _vector(artist_id, source_id, work_offset)
                canonical.append(work)
                reproductions.append(reproduction)
                features.append(_feature(reproduction, artist_id, vector))
                primary_vectors.append(vector)
                primary_artist_ids.append(artist_id)
                primary_source_ids.append(source_id)
                primary_work_ids.append(work_id)
                primary_reproduction_ids.append(reproduction_id)

            held_offset = -0.5 if source_id == "museum_a" else 0.5
            work_id = f"held_{artist_id}_{source_id}"
            reproduction_id = f"primary_{work_id}"
            work = _canonical(work_id, artist_id, "held_out")
            reproduction = _reproduction(reproduction_id, work_id, source_id, "held_out")
            vector = _vector(artist_id, source_id, held_offset)
            canonical.append(work)
            reproductions.append(reproduction)
            features.append(_feature(reproduction, artist_id, vector))
            primary_vectors.append(vector)
            primary_artist_ids.append(artist_id)
            primary_source_ids.append(source_id)
            primary_work_ids.append(work_id)
            primary_reproduction_ids.append(reproduction_id)
            held_work_ids.append(work_id)

    artist_by_work = {row.canonical_work_id: row.artist_id for row in canonical}
    primary_by_work = {
        row.canonical_work_id: row
        for row in reproductions
        if row.source_id != "cma_alternate_capture"
    }
    feature_by_reproduction: Dict[str, FeatureRow] = {row.reproduction_id: row for row in features}
    for work_position, work_id in enumerate(held_work_ids):
        primary = primary_by_work[work_id]
        primary_feature = feature_by_reproduction[primary.reproduction_id]
        alternate_count = 2 if work_position == 0 else 1
        for alternate_position in range(alternate_count):
            reproduction_id = f"alternate_{work_id}_{alternate_position}"
            reproduction = _reproduction(
                reproduction_id,
                work_id,
                "cma_alternate_capture",
                "held_out",
            )
            alternate_vector = np.asarray(primary_feature.vector, dtype=np.float32).copy()
            alternate_vector[0] += np.float32(0.04 + 0.02 * alternate_position)
            reproductions.append(reproduction)
            features.append(_feature(reproduction, artist_by_work[work_id], alternate_vector))

    return SyntheticCorpus(
        canonical=canonical,
        reproductions=reproductions,
        features=features,
        primary_vectors=np.stack(primary_vectors),
        primary_artist_ids=primary_artist_ids,
        primary_source_ids=primary_source_ids,
        primary_work_ids=primary_work_ids,
        primary_reproduction_ids=primary_reproduction_ids,
    )


def _probe_for_first_primary(corpus: SyntheticCorpus):
    feature = next(
        row for row in corpus.features if row.reproduction_id == corpus.primary_reproduction_ids[0]
    )
    reproduction = next(
        row for row in corpus.reproductions if row.reproduction_id == feature.reproduction_id
    )
    vector = np.asarray(feature.vector, dtype=np.float32)
    metadata = _extractor_metadata(reproduction, vector)
    first = LearnedFormalResult(vector=vector.copy(), metadata=dict(metadata))
    repeated = LearnedFormalResult(vector=vector.copy(), metadata=dict(metadata))
    return build_determinism_probe(feature.reproduction_id, first, repeated)


def _replace_feature_vector(feature: FeatureRow, vector: np.ndarray) -> FeatureRow:
    metadata = dict(feature.extraction_metadata)
    metadata["vector_sha256"] = learned_formal_vector_sha256(vector)
    return FeatureRow(
        **{
            **feature.model_dump(mode="python"),
            "vector": np.asarray(vector, dtype=np.float32).tolist(),
            "extraction_metadata": metadata,
        }
    )


def test_primary_pca_fit_is_invariant_to_held_out_vectors() -> None:
    corpus = _synthetic_corpus()
    probe = _probe_for_first_primary(corpus)
    baseline = evaluate_learned_formal_v2(
        corpus.canonical,
        corpus.reproductions,
        corpus.features,
        _thresholds(),
        {"artist_a": "artist_b", "artist_b": "artist_a"},
        [probe],
    )

    shifted_features: List[FeatureRow] = []
    for feature in corpus.features:
        if feature.split != "held_out":
            shifted_features.append(feature)
            continue
        vector = np.asarray(feature.vector, dtype=np.float32).copy()
        vector[0] += 10_000.0
        shifted_features.append(_replace_feature_vector(feature, vector))
    shifted = evaluate_learned_formal_v2(
        corpus.canonical,
        corpus.reproductions,
        shifted_features,
        _thresholds(),
        {"artist_a": "artist_b", "artist_b": "artist_a"},
        [probe],
    )

    assert baseline.primary_pca.fit_work_ids == shifted.primary_pca.fit_work_ids
    assert baseline.primary_pca.state_sha256 == shifted.primary_pca.state_sha256
    assert baseline.primary_pca.basis_sha256 == shifted.primary_pca.basis_sha256
    assert all(work_id.startswith("train_") for work_id in baseline.primary_pca.fit_work_ids)


def test_protocol_freezes_the_source_file_feature_literal() -> None:
    assert LearnedFormalV2Protocol().feature_version == (
        "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
    )
    with pytest.raises(ValueError):
        LearnedFormalV2Protocol(  # type: ignore[arg-type]
            feature_version="kim2026-sd20-a-vector-seeded-sample-v1"
        )


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("weights_sha256", "0" * 64),
        ("opencv_version", "4.13.0"),
        ("torch_version", "0.0.0"),
        ("seed_strategy", "explicit"),
        ("source_file_sha256", "f" * 64),
    ],
)
def test_prepare_rejects_per_row_extraction_contract_mismatches(
    field: str, invalid_value: object
) -> None:
    corpus = _synthetic_corpus()
    feature = corpus.features[0]
    metadata = {**feature.extraction_metadata, field: invalid_value}
    malformed = FeatureRow(
        **{
            **feature.model_dump(mode="python"),
            "extraction_metadata": metadata,
        }
    )

    with pytest.raises(ValueError, match="extraction metadata mismatch"):
        prepare_real_feature_rows(
            corpus.canonical,
            corpus.reproductions,
            [malformed, *corpus.features[1:]],
        )


def test_prepare_rejects_a_stale_per_row_vector_digest() -> None:
    corpus = _synthetic_corpus()
    feature = corpus.features[0]
    changed = np.asarray(feature.vector, dtype=np.float32).copy()
    changed[0] += 1.0
    malformed = FeatureRow(
        **{
            **feature.model_dump(mode="python"),
            "vector": changed.tolist(),
        }
    )

    with pytest.raises(ValueError, match="vector_sha256"):
        prepare_real_feature_rows(
            corpus.canonical,
            corpus.reproductions,
            [malformed, *corpus.features[1:]],
        )


def test_bootstrap_upper_bound_controls_qualification_not_the_point_ratio() -> None:
    evidence = bootstrap_distance_ratio(
        [0.1, 0.1, 0.1, 1.9],
        ["artist_a"] * 4,
        [1.0] * 8,
        ["artist_a"] * 8,
        0.5,
        draws=2_000,
        confidence_level=0.95,
        random_seed=20260830,
    )

    assert evidence.point_ratio == pytest.approx(0.1)
    assert evidence.point_ratio <= evidence.threshold
    assert evidence.confidence_upper is not None
    assert evidence.confidence_upper > evidence.threshold
    assert evidence.decision_rule == "bootstrap_upper_bound_le_threshold"
    assert evidence.supported is False


def test_nested_leave_source_out_refits_pca_without_fold_leakage() -> None:
    corpus = _synthetic_corpus()
    train_indices = [
        index
        for index, work_id in enumerate(corpus.primary_work_ids)
        if work_id.startswith("train_")
    ]
    matrix = corpus.primary_vectors[train_indices]
    artists = [corpus.primary_artist_ids[index] for index in train_indices]
    sources = [corpus.primary_source_ids[index] for index in train_indices]
    works = [corpus.primary_work_ids[index] for index in train_indices]
    reproductions = [corpus.primary_reproduction_ids[index] for index in train_indices]
    baseline = nested_leave_source_out_pca_artist_accuracy(
        matrix, artists, sources, works, reproductions
    )

    changed = matrix.copy()
    changed[np.asarray(sources) == "museum_a", 0] += 5_000.0
    rerun = nested_leave_source_out_pca_artist_accuracy(
        changed, artists, sources, works, reproductions
    )
    baseline_fold = next(fold for fold in baseline.folds if fold.held_out_source_id == "museum_a")
    rerun_fold = next(fold for fold in rerun.folds if fold.held_out_source_id == "museum_a")

    assert baseline_fold.pca is not None
    assert rerun_fold.pca is not None
    assert "museum_a" not in baseline_fold.fit_source_ids
    assert all("museum_a" not in work_id for work_id in baseline_fold.fit_work_ids)
    assert baseline_fold.pca.state_sha256 == rerun_fold.pca.state_sha256
    assert baseline_fold.pca.basis_sha256 == rerun_fold.pca.basis_sha256


def test_grouping_collapses_multiple_images_to_independent_works() -> None:
    grouped = group_independent_alternate_distances(
        distances=[1.0, 3.0, 4.0],
        canonical_work_ids=["work_a", "work_a", "work_b"],
        artist_ids=["artist_a", "artist_a", "artist_b"],
        reproduction_ids=["alt_a_1", "alt_a_2", "alt_b_1"],
    )

    assert [row.canonical_work_id for row in grouped] == ["work_a", "work_b"]
    assert grouped[0].alternate_image_count == 2
    assert grouped[0].independent_work_distance == pytest.approx(2.0)
    assert grouped[1].independent_work_distance == pytest.approx(4.0)


def test_prepare_rejects_vectors_that_are_not_exactly_16384_values() -> None:
    corpus = _synthetic_corpus()
    malformed = FeatureRow(
        **{
            **corpus.features[0].model_dump(mode="python"),
            "vector": corpus.features[0].vector[:-1],
        }
    )

    with pytest.raises(ValueError, match="16384"):
        prepare_real_feature_rows(
            corpus.canonical,
            corpus.reproductions,
            [malformed, *corpus.features[1:]],
        )


def test_source_behavior_requires_an_exact_repeated_extraction() -> None:
    corpus = _synthetic_corpus()
    prepared = prepare_real_feature_rows(corpus.canonical, corpus.reproductions, corpus.features)
    good_probe = _probe_for_first_primary(corpus)
    good = evaluate_source_behavior(prepared, [good_probe])

    feature = corpus.features[0]
    reproduction = corpus.reproductions[0]
    first_vector = np.asarray(feature.vector, dtype=np.float32)
    repeated_vector = first_vector.copy()
    repeated_vector[0] += 0.25
    bad_probe = build_determinism_probe(
        feature.reproduction_id,
        LearnedFormalResult(
            vector=first_vector,
            metadata=_extractor_metadata(reproduction, first_vector),
        ),
        LearnedFormalResult(
            vector=repeated_vector,
            metadata=_extractor_metadata(reproduction, repeated_vector),
        ),
    )
    bad = evaluate_source_behavior(prepared, [bad_probe])

    assert good.deterministic_repeats_verified is True
    assert good.source_behavior_recovered is True
    assert bad.deterministic_repeats_verified is False
    assert bad.source_behavior_recovered is False


def test_source_domain_eligibility_enforces_strict_area_and_aspect_boundaries() -> None:
    eligible = _reproduction("eligible", "work_eligible", "museum_a", "train").model_copy(
        update={"native_width": 411, "native_height": 410}
    )
    area_boundary = _reproduction(
        "area_boundary", "work_area", "museum_a", "train"
    ).model_copy(update={"native_width": 410, "native_height": 410})
    aspect_boundary = _reproduction(
        "aspect_boundary", "work_aspect", "museum_a", "train"
    ).model_copy(update={"native_width": 1000, "native_height": 500})
    missing = _reproduction("missing", "work_missing", "museum_a", "train").model_copy(
        update={"native_width": None, "native_height": None}
    )

    evidence = evaluate_source_domain_eligibility(
        [eligible, area_boundary, aspect_boundary, missing]
    )

    assert evidence.minimum_native_area_exclusive == 410 * 410
    assert evidence.maximum_aspect_ratio_exclusive == 2.0
    assert evidence.evaluated_primary_count == 4
    assert evidence.eligible_primary_count == 1
    assert evidence.native_area_violation_count == 1
    assert evidence.native_area_violating_reproduction_ids == ["area_boundary"]
    assert evidence.aspect_ratio_violation_count == 1
    assert evidence.aspect_ratio_violating_reproduction_ids == ["aspect_boundary"]
    assert evidence.missing_dimension_count == 1
    assert evidence.missing_dimension_reproduction_ids == ["missing"]
    assert evidence.all_primary_inputs_eligible is False


def test_determinism_probe_rejects_an_explicit_seed_or_stale_vector_digest() -> None:
    corpus = _synthetic_corpus()
    feature = corpus.features[0]
    reproduction = corpus.reproductions[0]
    vector = np.asarray(feature.vector, dtype=np.float32)
    metadata = _extractor_metadata(reproduction, vector)
    invalid = {
        **metadata,
        "seed_strategy": "explicit",
        "vector_sha256": "0" * 64,
    }

    probe = build_determinism_probe(
        feature.reproduction_id,
        LearnedFormalResult(vector=vector.copy(), metadata=dict(invalid)),
        LearnedFormalResult(vector=vector.copy(), metadata=dict(invalid)),
    )

    assert probe.vector_exact_match is True
    assert probe.metadata_exact_match is True
    assert probe.contract_verified is False


def test_full_synthetic_qualification_records_basis_and_limitations() -> None:
    corpus = _synthetic_corpus()
    result = evaluate_learned_formal_v2(
        corpus.canonical,
        corpus.reproductions,
        corpus.features,
        _thresholds(),
        {"artist_a": "artist_b", "artist_b": "artist_a"},
        [_probe_for_first_primary(corpus)],
    )

    assert result.status == "conditional_pass"
    assert result.primary_pca.input_dimension == RAW_DIMENSION
    assert result.primary_pca.component_count <= 32
    assert result.primary_pca.whiten is False
    assert result.primary_pca.variance_target_reached is True
    assert result.source_domain_eligibility.all_primary_inputs_eligible is True
    assert result.joint_artist_source_split.complete_joint_coverage is True
    assert len(result.primary_pca.basis_sha256) == 64
    assert len(result.primary_pca.state_sha256) == 64
    assert result.nested_source_evaluation.all_sources_supported is True
    assert all(fold.pca is not None for fold in result.nested_source_evaluation.folds)
    assert result.independent_alternate_work_count == 4
    assert result.alternate_image_count == 5
    assert result.source_behavior_recovered is True
    assert result.extraction_metadata.row_count == len(corpus.features)
    assert result.extraction_metadata.opencv_version == "4.14.0"
    assert len(result.extraction_metadata.metadata_sha256) == 64
    assert result.reproduction_stability.bootstrap_draws == 500
    assert result.reproduction_stability.confidence_upper is not None
    assert result.reproduction_stability.confidence_upper <= (
        result.reproduction_stability.threshold
    )
    assert result.conditional_limitations == list(CONDITIONAL_LIMITATIONS)
    assert any("seed-repaired" in item for item in result.conditional_limitations)
    assert any("author-supplied A-vectors" in item for item in result.conditional_limitations)
    assert any("no explicit reuse license" in item for item in result.conditional_limitations)
