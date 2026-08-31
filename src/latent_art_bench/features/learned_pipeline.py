from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np

from latent_art_bench.config import LearnedFormalConfig
from latent_art_bench.features.learned_formal import (
    LearnedFormalPins,
    LoadedSD2VAE,
    extract_learned_formal,
    load_pinned_sd2_vae,
)
from latent_art_bench.io import hash_file, stable_hash
from latent_art_bench.schemas import DerivedViewRecord, FeatureRow, ReproductionRecord


def load_configured_vae(config: LearnedFormalConfig, root: Path) -> LoadedSD2VAE:
    """Verify and load the exact local VAE pinned by a learned-formal config."""

    required = {
        "model_revision": config.model_revision,
        "model_snapshot_dir": config.model_snapshot_dir,
        "model_config_sha256": config.model_config_sha256,
        "model_weights_sha256": config.model_weights_sha256,
    }
    missing = sorted(name for name, value in required.items() if value is None)
    if missing:
        raise ValueError("learned-formal config is incomplete: " + ", ".join(missing))
    snapshot_dir = Path(str(config.model_snapshot_dir))
    if not snapshot_dir.is_absolute():
        snapshot_dir = root / snapshot_dir
    pins = LearnedFormalPins(
        model_revision=str(config.model_revision),
        config_sha256=str(config.model_config_sha256),
        weights_sha256=str(config.model_weights_sha256),
        source_repository=config.source_repository,
        source_revision=config.source_revision,
        model_repository=str(config.model_repository),
    )
    source_checkout = Path(str(config.source_checkout_dir))
    if not source_checkout.is_absolute():
        source_checkout = root / source_checkout
    return load_pinned_sd2_vae(
        snapshot_dir,
        pins,
        config_relative_path=Path("config.json"),
        weights_relative_path=Path("diffusion_pytorch_model.safetensors"),
        source_checkout=source_checkout,
    )


def extract_learned_formal_features(
    views: Iterable[DerivedViewRecord],
    reproductions: Iterable[ReproductionRecord],
    config: LearnedFormalConfig,
    root: Path,
    *,
    artist_by_work: Optional[Dict[str, str]] = None,
    split_by_work: Optional[Dict[str, str]] = None,
    origin_by_view: Optional[Dict[str, str]] = None,
    model_by_view: Optional[Dict[str, str]] = None,
    prompt_by_view: Optional[Dict[str, str]] = None,
    repetition_by_view: Optional[Dict[str, int]] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> Tuple[List[FeatureRow], List[Dict[str, object]]]:
    """Extract the pinned learned-formal feature and its non-tabular provenance."""

    if not config.enabled:
        raise ValueError("learned-formal extraction requires an enabled measurement")
    required = {
        "model_revision": config.model_revision,
        "model_snapshot_dir": config.model_snapshot_dir,
        "model_config_sha256": config.model_config_sha256,
        "model_weights_sha256": config.model_weights_sha256,
        "sampling_policy": config.sampling_policy,
        "base_seed": config.base_seed,
        "device": config.device,
    }
    missing = sorted(name for name, value in required.items() if value is None)
    if missing:
        raise ValueError("learned-formal config is incomplete: " + ", ".join(missing))

    rows = list(views)
    reproduction_rows = list(reproductions)
    if not rows:
        raise ValueError("learned-formal extraction requires at least one derived view")
    reproduction_by_id = {
        reproduction.reproduction_id: reproduction for reproduction in reproduction_rows
    }
    if len(reproduction_by_id) != len(reproduction_rows):
        raise ValueError("learned-formal reproduction identifiers must be unique")
    view_reproduction_ids = {view.reproduction_id for view in rows}
    if view_reproduction_ids != set(reproduction_by_id):
        raise ValueError(
            "learned-formal views and original reproductions must have identical IDs"
        )
    artist_by_work = artist_by_work or {}
    split_by_work = split_by_work or {}
    origin_by_view = origin_by_view or {}
    model_by_view = model_by_view or {}
    prompt_by_view = prompt_by_view or {}
    repetition_by_view = repetition_by_view or {}

    loaded = load_configured_vae(config, root)
    config_hash = stable_hash(config.model_dump(mode="json", exclude_none=True))

    features: List[FeatureRow] = []
    provenance: List[Dict[str, object]] = []
    for index, view in enumerate(rows, start=1):
        reproduction = reproduction_by_id[view.reproduction_id]
        if reproduction.canonical_work_id != view.canonical_work_id:
            raise ValueError(
                f"view/reproduction work mismatch: {view.reproduction_id}"
            )
        path = Path(reproduction.local_path)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            raise FileNotFoundError(f"missing original learned-formal input: {path}")
        observed_hash = hash_file(path)
        if reproduction.sha256 is None or observed_hash != reproduction.sha256:
            raise ValueError(
                f"original reproduction hash mismatch: {reproduction.reproduction_id}"
            )
        result = extract_learned_formal(
            path,
            loaded,
            policy=str(config.sampling_policy),
            base_seed=int(config.base_seed),
            device=str(config.device),
        )
        if result.metadata["feature_version"] != config.feature_version:
            raise ValueError(
                "extractor feature identity does not match config: "
                f"{result.metadata['feature_version']} != {config.feature_version}"
            )
        expected_metadata = {
            "source_input_role": config.source_input_role,
            "source_preprocessing_policy": config.source_preprocessing_policy,
            "opencv_version": config.opencv_version,
            "opencv_build_sha256": config.opencv_build_sha256,
            "pillow_version": config.pillow_version,
            "jpeg_codec_version": config.jpeg_codec_version,
            "python_version": config.python_version,
            "platform_system": config.platform_system,
            "platform_release": config.platform_release,
            "platform_machine": config.platform_machine,
            "numpy_version": config.numpy_version,
            "torch_version": config.torch_version,
            "diffusers_version": config.diffusers_version,
            "torch_mps_built": config.torch_mps_built,
            "torch_mps_available": config.torch_mps_available,
            "policy": config.sampling_policy,
            "base_seed": config.base_seed,
            "seed_strategy": config.seed_derivation,
            "device": config.device,
            "dtype": config.dtype,
            "model_repository": config.model_repository,
            "model_revision": config.model_revision,
            "config_sha256": config.model_config_sha256,
            "weights_sha256": config.model_weights_sha256,
            "source_repository": config.source_repository,
            "source_revision": config.source_revision,
            "input_size": config.input_size,
            "latent_shape": config.latent_shape,
            "flatten_order": config.flatten_order,
            "latent_scale": config.latent_scale,
            "input_color_order": config.input_color_order,
            "input_tensor_range": config.input_tensor_range,
        }
        mismatches = {
            name: {"expected": expected, "observed": result.metadata.get(name)}
            for name, expected in expected_metadata.items()
            if result.metadata.get(name) != expected
        }
        if mismatches:
            raise ValueError(
                "extractor runtime/provenance does not match config: "
                + ", ".join(sorted(mismatches))
            )
        if result.metadata.get("source_file_sha256") != observed_hash:
            raise ValueError("extractor source hash does not match the reproduction manifest")
        vector = np.asarray(result.vector, dtype=np.float32)
        feature_payload = {
            "derived_view_id": view.derived_view_id,
            "feature_version": config.feature_version,
            "feature_config_hash": config_hash,
            "seed_basis_sha256": result.metadata["seed_basis_sha256"],
            "seed": result.metadata["seed"],
            "source_file_sha256": observed_hash,
            "intermediate_payload_sha256": result.metadata[
                "intermediate_payload_sha256"
            ],
            "extraction_contract_sha256": stable_hash(result.metadata),
        }
        feature_id = f"feature-{stable_hash(feature_payload)[:24]}"
        origin = origin_by_view.get(view.derived_view_id, "real")
        model = model_by_view.get(view.derived_view_id)
        extraction_metadata = {
            "record_type": "learned_formal_extraction",
            "schema_version": "2.0",
            "feature_id": feature_id,
            "linkage_derived_view_id": view.derived_view_id,
            "linkage_derived_view_sha256": view.output_sha256,
            "input_role": "original_reproduction_file",
            "input_path": reproduction.local_path,
            "input_sha256": observed_hash,
            "feature_config_hash": config_hash,
            **result.metadata,
        }
        features.append(
            FeatureRow(
                feature_id=feature_id,
                derived_view_id=view.derived_view_id,
                reproduction_id=view.reproduction_id,
                canonical_work_id=view.canonical_work_id,
                artist_id=artist_by_work.get(view.canonical_work_id),
                origin=origin,
                split=split_by_work.get(view.canonical_work_id, "unassigned"),
                model=model,
                prompt_id=prompt_by_view.get(view.derived_view_id),
                repetition=repetition_by_view.get(view.derived_view_id),
                feature_name="learned_formal",
                feature_version=config.feature_version,
                feature_config_hash=config_hash,
                vector=vector.astype(float).tolist(),
                scalars={
                    "vector_l2": float(np.linalg.norm(vector)),
                    "vector_mean": float(vector.mean()),
                    "vector_std": float(vector.std(ddof=0)),
                },
                extraction_metadata=extraction_metadata,
                status="ok",
            )
        )
        provenance.append(extraction_metadata)
        if progress is not None:
            progress(index, len(rows))
    return features, provenance
