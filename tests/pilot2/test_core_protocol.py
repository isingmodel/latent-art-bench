from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.features.learned_formal import learned_formal_vector_sha256
from latent_art_bench.io import stable_hash
from latent_art_bench.pilot2.config import PILOT2_ARTISTS, Pilot2Config
from latent_art_bench.pilot2.contracts import pilot2_generation_gate
from latent_art_bench.pilot2.corpus import build_pilot2_atlas
from latent_art_bench.pilot2.learned_formal import fit_train_only_pca
from latent_art_bench.pilot2.preprocessing import (
    common_png_bytes,
    preprocess_common_png,
)
from latent_art_bench.pilot2.qualification import (
    qualification_card_from_result,
    qualify_learned_formal,
)
from latent_art_bench.pilot2.schemas import (
    Pilot2AcquiredImage,
    Pilot2DeterminismProbe,
    Pilot2Feature,
)

ROOT = Path(__file__).resolve().parents[2]


def test_config_and_sha_atlas_freeze_exact_design() -> None:
    config = Pilot2Config()
    assert config.generation.logical_cell_count == 320
    assert config.generation.models == ["gpt-image-1", "gpt-image-2"]
    assert config.generation.base_url == "http://127.0.0.1:10532/v1"
    assert config.measurements.primary == ["learned_formal"]
    assert config.measurements.secondary == ["chromatic"]

    path = ROOT / config.corpus.candidate_audit
    first = build_pilot2_atlas(path, config.corpus)
    second = build_pilot2_atlas(path, config.corpus)
    assert first == second
    assert len(first) == 40
    assert first[0].canonical_work_id == "work-aic-73054"
    assert first[0].selection_digest == hashlib.sha256(
        b"pilot2-v1|20260901|work-aic-73054"
    ).hexdigest()
    assert all(work.canonical_work_id.startswith("work-") for work in first)
    assert all(
        work.native_width * work.native_height > 410 * 410
        and max(work.native_width, work.native_height)
        / min(work.native_width, work.native_height)
        < 2
        for work in first
    )


def test_common_preprocessing_is_deterministic_lossless_png(tmp_path: Path) -> None:
    config = Pilot2Config().preprocessing
    source = tmp_path / "alpha.webp"
    Image.new("RGBA", (1600, 800), (255, 0, 0, 128)).save(source, format="WEBP")

    first = preprocess_common_png(source, "fixture", tmp_path / "derived", config)
    second = preprocess_common_png(source, "fixture", tmp_path / "derived", config)
    assert first.output_sha256 == second.output_sha256
    assert (first.width, first.height) == (1024, 512)
    with Image.open(first.output_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.mode == "RGB"

    with Image.open(source) as image:
        encoded, size = common_png_bytes(image, config)
    assert hashlib.sha256(encoded).hexdigest() == first.output_sha256
    assert size == (1024, 512)


def test_train_only_pca_uses_minimum_95_percent_basis_and_rank_cap() -> None:
    rng = np.random.default_rng(7)
    dominant = rng.normal(size=(12, 1))
    matrix = np.hstack(
        [dominant * 10, dominant * 2, rng.normal(scale=0.01, size=(12, 5))]
    )
    work_ids = [f"work-{index}" for index in range(12)]
    first = fit_train_only_pca(matrix, work_ids)
    second = fit_train_only_pca(matrix, work_ids)
    assert first.evidence.component_cap == 7
    assert first.evidence.component_count == 1
    assert first.evidence.cumulative_explained_variance >= 0.95
    assert first.evidence.state_sha256 == second.evidence.state_sha256


def _content_seed(seed_basis: str, base_seed: int) -> int:
    digest = hashlib.sha256()
    digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
    digest.update(base_seed.to_bytes(8, "big"))
    digest.update(bytes.fromhex(seed_basis))
    return int.from_bytes(digest.digest()[:8], "big") & ((1 << 63) - 1)


def _feature_metadata(
    config: Pilot2Config,
    derived_sha: str,
    vector: np.ndarray,
    work_id: str,
    source_width: int,
    source_height: int,
) -> dict:
    learned = config.learned_formal
    seed_basis = hashlib.sha256(f"seed:{work_id}".encode()).hexdigest()
    return {
        "feature_version": learned.feature_version,
        "pilot2_representation_role": "harmonized_png_seeded_a_vector",
        "upstream_extractor_feature_version": (
            "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
        ),
        "representation_role": "source_replication_seeded_posterior_sample",
        "policy": "seeded_posterior_sample",
        "seed": _content_seed(seed_basis, learned.base_seed),
        "seed_strategy": "sha256_of_resized_rgb_plus_base_seed",
        "base_seed": learned.base_seed,
        "seed_basis_sha256": seed_basis,
        "source_input_role": "original_reproduction_file",
        "source_preprocessing_policy": (
            "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
        ),
        "source_file_sha256": derived_sha,
        "source_extension": ".png",
        "intermediate_payload_sha256": hashlib.sha256(
            f"intermediate:{work_id}".encode()
        ).hexdigest(),
        "intermediate_encoding": "png",
        "common_derived_png_sha256": derived_sha,
        "acquired_source_sha256": derived_sha,
        "acquired_source_record_id": work_id,
        "acquired_source_width": source_width,
        "acquired_source_height": source_height,
        "acquired_source_decoded_format": "jpeg",
        "common_preprocessing_config_sha256": stable_hash(
            config.preprocessing.model_dump(mode="json")
        ),
        "input_size": [512, 512],
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": [4, 64, 64],
        "latent_scale": 0.18215,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": "C",
        "vector_length": learned.raw_dimension,
        "dtype": "float32",
        "vector_sha256": learned_formal_vector_sha256(vector),
        "source_repository": learned.source_repository,
        "source_revision": learned.source_revision,
        "source_checkout_verified": True,
        "model_repository": learned.model_repository,
        "model_revision": learned.model_revision,
        "config_sha256": learned.model_config_sha256,
        "weights_sha256": learned.model_weights_sha256,
        "artifacts_verified": True,
        "device": learned.device,
        "opencv_version": learned.opencv_version,
        "opencv_build_sha256": learned.opencv_build_sha256,
        "pillow_version": learned.pillow_version,
        "jpeg_codec_version": learned.jpeg_codec_version,
        "python_version": learned.python_version,
        "platform_system": learned.platform_system,
        "platform_release": learned.platform_release,
        "platform_machine": learned.platform_machine,
        "numpy_version": learned.numpy_version,
        "torch_version": learned.torch_version,
        "diffusers_version": learned.diffusers_version,
        "torch_mps_built": learned.torch_mps_built,
        "torch_mps_available": learned.torch_mps_available,
    }


def test_learned_primary_qualification_passes_and_alone_unlocks_generation() -> None:
    config = Pilot2Config(
        learned_formal={"raw_dimension": 8, "permutation_draws": 199}
    )
    atlas = build_pilot2_atlas(ROOT / config.corpus.candidate_audit, config.corpus)
    artist_axis = {artist: index for index, artist in enumerate(PILOT2_ARTISTS)}
    feature_config_sha = stable_hash(config.learned_formal.model_dump(mode="json"))
    features = []
    acquired_images = []
    probes = []
    for work in atlas:
        vector = np.zeros(8, dtype=np.float32)
        source_offset = 0 if work.source_id == "aic" else 4
        vector[source_offset + artist_axis[work.artist_id]] = 20.0
        derived_sha = hashlib.sha256(work.canonical_work_id.encode()).hexdigest()
        acquired_images.append(
            Pilot2AcquiredImage(
                canonical_work_id=work.canonical_work_id,
                artist_id=work.artist_id,
                source_id=work.source_id,
                source_object_id=work.source_object_id,
                local_path=f"/fixture/{work.canonical_work_id}.jpg",
                sha256=derived_sha,
                decoded_width=work.native_width,
                decoded_height=work.native_height,
                decoded_format="jpeg",
                atlas_selection_digest=work.selection_digest,
            )
        )
        metadata = _feature_metadata(
            config,
            derived_sha,
            vector,
            work.canonical_work_id,
            work.native_width,
            work.native_height,
        )
        feature_identity = stable_hash(
            {
                "canonical_work_id": work.canonical_work_id,
                "derived_png_sha256": derived_sha,
                "feature_version": config.learned_formal.feature_version,
                "feature_config_sha256": feature_config_sha,
                "extraction_metadata": metadata,
            }
        )
        features.append(
            Pilot2Feature(
                feature_id=f"pilot2-feature-{feature_identity[:24]}",
                canonical_work_id=work.canonical_work_id,
                artist_id=work.artist_id,
                source_id=work.source_id,
                split=work.split,
                feature_version=config.learned_formal.feature_version,
                feature_config_sha256=feature_config_sha,
                derived_png_sha256=derived_sha,
                vector=vector.tolist(),
                extraction_metadata=metadata,
                status="ok",
            )
        )
        if work.source_id == "aic" and work.selection_rank == 1:
            vector_sha = learned_formal_vector_sha256(vector)
            probes.append(
                Pilot2DeterminismProbe(
                    artist_id=work.artist_id,
                    canonical_work_id=work.canonical_work_id,
                    feature_version=config.learned_formal.feature_version,
                    derived_png_sha256=derived_sha,
                    seed=metadata["seed"],
                    first_vector_sha256=vector_sha,
                    second_vector_sha256=vector_sha,
                    exact_equal=True,
                )
            )

    contract_hash = hashlib.sha256(b"qualification-contract").hexdigest()
    result = qualify_learned_formal(
        features,
        atlas,
        acquired_images,
        config,
        probes,
        qualification_contract_sha256=contract_hash,
    )
    assert result.status == "pass"
    assert result.pca.component_count <= 23
    assert result.pooled_held.balanced_accuracy == 1.0
    assert all(
        stratum.classification.balanced_accuracy == 1.0
        for stratum in result.pooled_classifier_held_by_source.values()
    )
    assert all(
        stratum.test_work_count == 8
        and stratum.shared_pca_state_sha256 == result.pca.state_sha256
        and stratum.shared_artist_classifier_state_sha256
        == result.pooled_artist_classifier_state_sha256
        for stratum in result.pooled_classifier_held_by_source.values()
    )
    assert (
        result.development_diagnostics.pooled_source_label_predictability.role
        == "development_non_gating"
    )
    assert any(
        diagnostic.classification.balanced_accuracy <= 0.25
        for diagnostic in result.development_diagnostics.opposite_source_transfer.values()
    )
    assert not any("opposite_source" in name for name in result.checks)
    assert result.permutation.p_value <= 0.05
    assert result.permutation.statistic == "pooled_held_balanced_accuracy"
    assert len(result.determinism_probes) == 4
    card = qualification_card_from_result(
        result,
        "reports/pilot_2/evidence/learned_formal_qualification.json",
        hashlib.sha256(b"artifact").hexdigest(),
    )
    assert card.status == "pass"
    assert card.qualification_contract_sha256 == contract_hash

    allowed, reasons = pilot2_generation_gate(
        result, config, expected_contract_sha256=contract_hash
    )
    assert allowed is True
    assert reasons == []
    assert pilot2_generation_gate(result, config)[0] is False
    stale = result.model_copy(update={"result_sha256": "0" * 64})
    assert pilot2_generation_gate(
        stale, config, expected_contract_sha256=contract_hash
    )[0] is False
