"""Prospective real-only qualification for the pilot_2 primary measurement."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from latent_art_bench.features.learned_formal import learned_formal_vector_sha256
from latent_art_bench.io import stable_hash
from latent_art_bench.pilot2.config import PILOT2_ARTISTS, PILOT2_SOURCES, Pilot2Config
from latent_art_bench.pilot2.corpus import (
    acquired_image_manifest_sha256,
    validate_pilot2_acquired_images,
    validate_pilot2_atlas,
)
from latent_art_bench.pilot2.learned_formal import (
    Pilot2FrozenPCA,
    balanced_accuracy,
    centroid_classifier_state_sha256,
    classify_projected,
    fit_train_only_pca,
    predict_nearest_centroid,
    transform_with_pca,
)
from latent_art_bench.pilot2.schemas import (
    Pilot2AcquiredImage,
    Pilot2AtlasWork,
    Pilot2DeterminismProbe,
    Pilot2DevelopmentDiagnostics,
    Pilot2Feature,
    Pilot2HeldBySourceClassificationEvidence,
    Pilot2LearnedQualificationResult,
    Pilot2OppositeSourceTransferDiagnostic,
    Pilot2PermutationEvidence,
    Pilot2QualificationCard,
    Pilot2SourcePredictabilityDiagnostic,
)


@dataclass(frozen=True)
class _Projection:
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_scores: np.ndarray
    test_scores: np.ndarray
    pca: Pilot2FrozenPCA


def _feature_manifest_sha256(rows: Sequence[Pilot2Feature]) -> str:
    return stable_hash(
        [
            row.model_dump(mode="json")
            for row in sorted(rows, key=lambda item: item.canonical_work_id)
        ]
    )


def _validate_feature_atlas_binding(
    features: Sequence[Pilot2Feature],
    atlas: Sequence[Pilot2AtlasWork],
    acquired_images: Sequence[Pilot2AcquiredImage],
    config: Pilot2Config,
) -> Tuple[List[Pilot2Feature], str]:
    validate_pilot2_atlas(atlas, config.corpus)
    validate_pilot2_acquired_images(acquired_images, atlas)
    if len(features) != 40:
        raise ValueError(
            f"pilot_2 qualification requires exactly 40 features, found {len(features)}"
        )
    if any(row.status != "ok" for row in features):
        raise ValueError("pilot_2 qualification cannot consume failed features")
    feature_ids = [row.feature_id for row in features]
    work_ids = [row.canonical_work_id for row in features]
    if len(feature_ids) != len(set(feature_ids)) or len(work_ids) != len(set(work_ids)):
        raise ValueError("pilot_2 qualification requires unique feature and work identifiers")

    atlas_by_work = {row.canonical_work_id: row for row in atlas}
    acquired_by_work = {row.canonical_work_id: row for row in acquired_images}
    if set(work_ids) != set(atlas_by_work):
        raise ValueError("pilot_2 features do not cover the selected atlas exactly")
    expected_config_hash = stable_hash(config.learned_formal.model_dump(mode="json"))
    expected_preprocessing_hash = stable_hash(
        config.preprocessing.model_dump(mode="json")
    )
    expected_version = config.learned_formal.feature_version
    for row in features:
        work = atlas_by_work[row.canonical_work_id]
        if (row.artist_id, row.source_id, row.split) != (
            work.artist_id,
            work.source_id,
            work.split,
        ):
            raise ValueError(f"feature labels disagree with atlas: {row.canonical_work_id}")
        if (
            row.feature_version != expected_version
            or row.feature_config_sha256 != expected_config_hash
        ):
            raise ValueError(f"feature identity is stale: {row.feature_id}")
        if len(row.vector) != config.learned_formal.raw_dimension:
            raise ValueError(
                f"feature {row.feature_id} has dimension {len(row.vector)}; "
                f"expected {config.learned_formal.raw_dimension}"
            )
        metadata = row.extraction_metadata
        acquired = acquired_by_work[row.canonical_work_id]
        expected_metadata = {
            "feature_version": expected_version,
            "pilot2_representation_role": "harmonized_png_seeded_a_vector",
            "upstream_extractor_feature_version": (
                "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
            ),
            "representation_role": "source_replication_seeded_posterior_sample",
            "policy": "seeded_posterior_sample",
            "seed_strategy": "sha256_of_resized_rgb_plus_base_seed",
            "base_seed": config.learned_formal.base_seed,
            "source_input_role": "original_reproduction_file",
            "source_preprocessing_policy": (
                "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
            ),
            "source_file_sha256": row.derived_png_sha256,
            "source_extension": ".png",
            "intermediate_encoding": "png",
            "common_derived_png_sha256": row.derived_png_sha256,
            "acquired_source_sha256": acquired.sha256,
            "acquired_source_record_id": acquired.canonical_work_id,
            "acquired_source_width": acquired.decoded_width,
            "acquired_source_height": acquired.decoded_height,
            "acquired_source_decoded_format": acquired.decoded_format,
            "common_preprocessing_config_sha256": expected_preprocessing_hash,
            "input_size": [512, 512],
            "input_color_order": "RGB",
            "input_tensor_range": [-1.0, 1.0],
            "resize_library": "opencv",
            "resize_interpolation": "INTER_LANCZOS4",
            "latent_shape": [4, 64, 64],
            "latent_scale": 0.18215,
            "latent_scale_application": "explicit_after_encode",
            "flatten_order": "C",
            "vector_length": config.learned_formal.raw_dimension,
            "dtype": "float32",
            "source_repository": config.learned_formal.source_repository,
            "source_revision": config.learned_formal.source_revision,
            "model_repository": config.learned_formal.model_repository,
            "model_revision": config.learned_formal.model_revision,
            "config_sha256": config.learned_formal.model_config_sha256,
            "weights_sha256": config.learned_formal.model_weights_sha256,
            "device": config.learned_formal.device,
            "opencv_version": config.learned_formal.opencv_version,
            "opencv_build_sha256": config.learned_formal.opencv_build_sha256,
            "pillow_version": config.learned_formal.pillow_version,
            "jpeg_codec_version": config.learned_formal.jpeg_codec_version,
            "python_version": config.learned_formal.python_version,
            "platform_system": config.learned_formal.platform_system,
            "platform_release": config.learned_formal.platform_release,
            "platform_machine": config.learned_formal.platform_machine,
            "numpy_version": config.learned_formal.numpy_version,
            "torch_version": config.learned_formal.torch_version,
            "diffusers_version": config.learned_formal.diffusers_version,
            "torch_mps_built": config.learned_formal.torch_mps_built,
            "torch_mps_available": config.learned_formal.torch_mps_available,
            "source_checkout_verified": True,
            "artifacts_verified": True,
        }
        mismatches = [
            key for key, expected in expected_metadata.items() if metadata.get(key) != expected
        ]
        digest_fields = (
            "seed_basis_sha256",
            "intermediate_payload_sha256",
        )
        for key in digest_fields:
            value = metadata.get(key)
            if not isinstance(value, str) or len(value) != 64 or any(
                character not in "0123456789abcdef" for character in value
            ):
                mismatches.append(key)
        expected_vector_hash = learned_formal_vector_sha256(row.vector)
        if metadata.get("vector_sha256") != expected_vector_hash:
            mismatches.append("vector_sha256")
        seed_basis = metadata.get("seed_basis_sha256")
        if isinstance(seed_basis, str) and len(seed_basis) == 64:
            seed_digest = hashlib.sha256()
            seed_digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
            seed_digest.update(config.learned_formal.base_seed.to_bytes(8, "big"))
            try:
                seed_digest.update(bytes.fromhex(seed_basis))
                expected_seed = int.from_bytes(seed_digest.digest()[:8], "big") & (
                    (1 << 63) - 1
                )
            except ValueError:
                expected_seed = None
            if metadata.get("seed") != expected_seed:
                mismatches.append("seed")
        if mismatches:
            raise ValueError(
                f"feature extraction provenance is stale for {row.feature_id}: "
                + ", ".join(sorted(set(mismatches)))
            )

    ordered = sorted(features, key=lambda row: row.canonical_work_id)
    counts = Counter((row.artist_id, row.source_id, row.split) for row in ordered)
    expected_counts = Counter(
        {
            (artist, source, split): count
            for artist in PILOT2_ARTISTS
            for source in PILOT2_SOURCES
            for split, count in (("train", 3), ("held_out", 2))
        }
    )
    if counts != expected_counts:
        raise ValueError("pilot_2 feature cohort is not balanced at 3 train + 2 held per cell")
    return ordered, expected_config_hash


def _projection(
    matrix: np.ndarray,
    rows: Sequence[Pilot2Feature],
    train_indices: Sequence[int],
    test_indices: Sequence[int],
    variance_target: float,
) -> _Projection:
    train_indices_array = np.asarray(train_indices, dtype=np.int64)
    test_indices_array = np.asarray(test_indices, dtype=np.int64)
    if train_indices_array.size == 0 or test_indices_array.size == 0:
        raise ValueError("qualification projection requires train and test rows")
    pca = fit_train_only_pca(
        matrix[train_indices_array],
        [rows[index].canonical_work_id for index in train_indices_array],
        variance_target=variance_target,
    )
    return _Projection(
        train_indices=train_indices_array,
        test_indices=test_indices_array,
        train_scores=transform_with_pca(matrix[train_indices_array], pca),
        test_scores=transform_with_pca(matrix[test_indices_array], pca),
        pca=pca,
    )


def _accuracy_for_labels(projection: _Projection, labels: Sequence[str]) -> float:
    train_labels = [labels[index] for index in projection.train_indices]
    test_labels = [labels[index] for index in projection.test_indices]
    predictions = predict_nearest_centroid(
        projection.train_scores,
        train_labels,
        projection.test_scores,
    )
    accuracy, _ = balanced_accuracy(test_labels, predictions)
    return accuracy


def _classification_evidence(
    projection: _Projection,
    labels: Sequence[str],
    rows: Sequence[Pilot2Feature],
):
    return classify_projected(
        projection.train_scores,
        [labels[index] for index in projection.train_indices],
        projection.test_scores,
        [labels[index] for index in projection.test_indices],
        [rows[index].canonical_work_id for index in projection.test_indices],
    )


def _classification_evidence_for_test_indices(
    projection: _Projection,
    labels: Sequence[str],
    rows: Sequence[Pilot2Feature],
    selected_test_indices: Sequence[int],
):
    positions = {int(index): position for position, index in enumerate(projection.test_indices)}
    try:
        selected_positions = [positions[index] for index in selected_test_indices]
    except KeyError as exc:
        raise ValueError("classification subset is outside the shared held-out projection") from exc
    return classify_projected(
        projection.train_scores,
        [labels[index] for index in projection.train_indices],
        projection.test_scores[np.asarray(selected_positions, dtype=np.int64)],
        [labels[index] for index in selected_test_indices],
        [rows[index].canonical_work_id for index in selected_test_indices],
    )


def _constrained_permutation_test(
    rows: Sequence[Pilot2Feature],
    labels: Sequence[str],
    pooled_projection: _Projection,
    draws: int,
    seed: int,
) -> Pilot2PermutationEvidence:
    observed = _accuracy_for_labels(pooled_projection, labels)
    blocks: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        blocks[(row.source_id, row.split)].append(index)

    rng = np.random.default_rng(seed)
    original = np.asarray(labels, dtype=object)
    exceedances = 0
    for _ in range(draws):
        permuted = original.copy()
        for indices in blocks.values():
            index_array = np.asarray(indices, dtype=np.int64)
            permuted[index_array] = original[rng.permutation(index_array)]
        statistic = _accuracy_for_labels(pooled_projection, permuted.tolist())
        exceedances += int(statistic >= observed)
    p_value = (exceedances + 1.0) / (draws + 1.0)
    return Pilot2PermutationEvidence(
        observed_statistic=observed,
        draws=draws,
        seed=seed,
        exceedance_count=exceedances,
        p_value=p_value,
    )


def qualification_result_sha256(
    result_or_payload: Union[Pilot2LearnedQualificationResult, Mapping[str, object]],
) -> str:
    if isinstance(result_or_payload, Pilot2LearnedQualificationResult):
        payload = result_or_payload.model_dump(mode="json")
    else:
        payload = dict(result_or_payload)
    payload.pop("result_sha256", None)
    return stable_hash(payload)


def qualify_learned_formal(
    features: Sequence[Pilot2Feature],
    atlas: Sequence[Pilot2AtlasWork],
    acquired_images: Sequence[Pilot2AcquiredImage],
    config: Pilot2Config,
    determinism_probes: Sequence[Pilot2DeterminismProbe],
    *,
    qualification_contract_sha256: Optional[str] = None,
) -> Pilot2LearnedQualificationResult:
    """Apply every predeclared gate and return exactly ``pass`` or ``fail``.

    PCA and artist centroids are fit once on all 24 balanced training rows.
    Their held predictions are evaluated both pooled and separately in the
    AIC and NGA n=8 strata.  The permutation statistic is pooled held balanced
    accuracy with labels shuffled only within each source-by-split block.
    Opposite-source transfer is retained only as a development diagnostic.
    """

    rows, feature_config_hash = _validate_feature_atlas_binding(
        list(features), list(atlas), list(acquired_images), config
    )
    matrix = np.asarray([row.vector for row in rows], dtype=np.float64)
    labels = [row.artist_id for row in rows]
    train_indices = [index for index, row in enumerate(rows) if row.split == "train"]
    held_indices = [index for index, row in enumerate(rows) if row.split == "held_out"]
    pooled_projection = _projection(
        matrix,
        rows,
        train_indices,
        held_indices,
        config.learned_formal.pca_variance_target,
    )
    pooled = _classification_evidence(pooled_projection, labels, rows)
    pooled_artist_classifier_state_sha256 = centroid_classifier_state_sha256(
        pooled_projection.train_scores,
        [labels[index] for index in pooled_projection.train_indices],
    )

    pooled_classifier_held_by_source: Dict[
        str, Pilot2HeldBySourceClassificationEvidence
    ] = {}
    for held_source in PILOT2_SOURCES:
        source_test = [
            index
            for index, row in enumerate(rows)
            if row.split == "held_out" and row.source_id == held_source
        ]
        source_classification = _classification_evidence_for_test_indices(
            pooled_projection,
            labels,
            rows,
            source_test,
        )
        pooled_classifier_held_by_source[held_source] = (
            Pilot2HeldBySourceClassificationEvidence(
                source_id=held_source,
                shared_pca_state_sha256=pooled_projection.pca.evidence.state_sha256,
                shared_artist_classifier_state_sha256=(
                    pooled_artist_classifier_state_sha256
                ),
                classification=source_classification,
            )
        )

    opposite_source_transfer: Dict[str, Pilot2OppositeSourceTransferDiagnostic] = {}
    for held_source in PILOT2_SOURCES:
        fold_train = [
            index
            for index, row in enumerate(rows)
            if row.split == "train" and row.source_id != held_source
        ]
        fold_test = [
            index
            for index, row in enumerate(rows)
            if row.split == "held_out" and row.source_id == held_source
        ]
        fold = _projection(
            matrix,
            rows,
            fold_train,
            fold_test,
            config.learned_formal.pca_variance_target,
        )
        opposite_source_transfer[held_source] = Pilot2OppositeSourceTransferDiagnostic(
            held_source_id=held_source,
            pca=fold.pca.evidence,
            classification=_classification_evidence(fold, labels, rows),
        )

    source_labels = [row.source_id for row in rows]
    source_classifier_state_sha256 = centroid_classifier_state_sha256(
        pooled_projection.train_scores,
        [source_labels[index] for index in pooled_projection.train_indices],
    )
    development_diagnostics = Pilot2DevelopmentDiagnostics(
        opposite_source_transfer=opposite_source_transfer,
        pooled_source_label_predictability=Pilot2SourcePredictabilityDiagnostic(
            classification=_classification_evidence(
                pooled_projection, source_labels, rows
            ),
            shared_pca_state_sha256=pooled_projection.pca.evidence.state_sha256,
            source_classifier_state_sha256=source_classifier_state_sha256,
        ),
    )

    permutation = _constrained_permutation_test(
        rows,
        labels,
        pooled_projection,
        draws=config.learned_formal.permutation_draws,
        seed=config.learned_formal.permutation_seed,
    )
    sorted_probes = sorted(
        determinism_probes,
        key=lambda probe: (probe.artist_id, probe.canonical_work_id),
    )
    probe_artists = {probe.artist_id for probe in sorted_probes}
    probe_work_ids = {probe.canonical_work_id for probe in sorted_probes}
    atlas_work_ids = {work.canonical_work_id for work in atlas}
    atlas_by_work = {work.canonical_work_id: work for work in atlas}
    feature_by_work = {row.canonical_work_id: row for row in rows}
    determinism_valid = (
        len(sorted_probes) >= 4
        and len(probe_work_ids) >= 4
        and probe_artists == set(PILOT2_ARTISTS)
        and probe_work_ids <= atlas_work_ids
        and all(
            probe.exact_equal
            and atlas_by_work[probe.canonical_work_id].artist_id == probe.artist_id
            and feature_by_work[probe.canonical_work_id].derived_png_sha256
            == probe.derived_png_sha256
            and probe.feature_version == config.learned_formal.feature_version
            and feature_by_work[probe.canonical_work_id].extraction_metadata.get("seed")
            == probe.seed
            for probe in sorted_probes
        )
    )
    native_domain_valid = all(
        work.native_width * work.native_height > 410 * 410
        and max(work.native_width, work.native_height)
        / min(work.native_width, work.native_height)
        < 2.0
        for work in atlas
    )
    acquired_domain_valid = all(
        image.decoded_width * image.decoded_height > 410 * 410
        and max(image.decoded_width, image.decoded_height)
        / min(image.decoded_width, image.decoded_height)
        < 2.0
        for image in acquired_images
    )
    checks = {
        "all_feature_extraction_contracts_are_pinned": True,
        "all_40_native_images_meet_area_and_aspect_domain": native_domain_valid,
        "all_40_acquired_images_meet_area_and_aspect_domain": acquired_domain_valid,
        "at_least_one_exact_repeat_probe_per_artist": determinism_valid,
        "pca_reached_95_percent_with_train_only_rank": (
            pooled_projection.pca.evidence.variance_target_reached
        ),
        "pooled_held_artist_ba_strictly_above_chance": (
            pooled.balanced_accuracy
            > config.learned_formal.pooled_held_artist_ba_strict_min
        ),
        "each_pooled_classifier_held_source_ba_strictly_above_chance": all(
            evidence.classification.balanced_accuracy
            > config.learned_formal.pooled_classifier_held_by_source_artist_ba_strict_min
            for evidence in pooled_classifier_held_by_source.values()
        ),
        "constrained_permutation_p_at_most_0_05": (
            permutation.p_value <= config.learned_formal.permutation_p_max
        ),
    }
    reasons = [name for name, passed in checks.items() if not passed]
    payload = {
        "record_type": "pilot2_learned_qualification",
        "schema_version": "2.0",
        "measurement": "learned_formal",
        "status": "pass" if all(checks.values()) else "fail",
        "feature_version": config.learned_formal.feature_version,
        "feature_config_sha256": feature_config_hash,
        "input_feature_manifest_sha256": _feature_manifest_sha256(rows),
        "input_acquired_manifest_sha256": acquired_image_manifest_sha256(
            acquired_images
        ),
        "qualification_config_sha256": stable_hash(
            config.learned_formal.model_dump(mode="json")
        ),
        "qualification_contract_sha256": qualification_contract_sha256,
        "atlas_work_count": 40,
        "train_work_count": 24,
        "held_out_work_count": 16,
        "pca": pooled_projection.pca.evidence.model_dump(mode="json"),
        "pooled_artist_classifier_state_sha256": (
            pooled_artist_classifier_state_sha256
        ),
        "pooled_held": pooled.model_dump(mode="json"),
        "pooled_classifier_held_by_source": {
            source: evidence.model_dump(mode="json")
            for source, evidence in pooled_classifier_held_by_source.items()
        },
        "development_diagnostics": development_diagnostics.model_dump(mode="json"),
        "permutation": permutation.model_dump(mode="json"),
        "determinism_probes": [
            probe.model_dump(mode="json") for probe in sorted_probes
        ],
        "checks": checks,
        "reasons": reasons,
    }
    return Pilot2LearnedQualificationResult(
        **payload,
        result_sha256=qualification_result_sha256(payload),
    )


def qualification_card_from_result(
    result: Pilot2LearnedQualificationResult,
    evidence_artifact_path: str,
    evidence_artifact_sha256: str,
) -> Pilot2QualificationCard:
    if result.qualification_contract_sha256 is None:
        raise ValueError("pilot_2 qualification card requires a bound contract")
    if result.result_sha256 != qualification_result_sha256(result):
        raise ValueError("pilot_2 qualification result self-hash is stale")
    return Pilot2QualificationCard(
        status=result.status,
        feature_version=result.feature_version,
        feature_config_sha256=result.feature_config_sha256,
        qualification_contract_sha256=result.qualification_contract_sha256,
        qualification_result_sha256=result.result_sha256,
        evidence_artifact_path=evidence_artifact_path,
        evidence_artifact_sha256=evidence_artifact_sha256,
        input_feature_manifest_sha256=result.input_feature_manifest_sha256,
        input_acquired_manifest_sha256=result.input_acquired_manifest_sha256,
        reasons=result.reasons,
    )
