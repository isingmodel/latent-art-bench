"""Bitwise equivalence verification for the pinned SD2-base VAE artifacts.

This module is intentionally independent of the qualification-card schema and the
main CLI.  Run it as ``python -m latent_art_bench.evaluation.vae_equivalence`` to
produce a durable evidence JSON file.  PyTorch and safetensors are imported only
inside the verifier so importing the core package does not require learned-feature
dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import pickletools
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from latent_art_bench.io import hash_file, stable_hash, write_json

MODEL_REPOSITORY = "Manojb/stable-diffusion-2-base"
MODEL_REVISION = "64bf7b4f10eee35494b38d55c06c0c78cf8b44d0"
MODEL_REVISION_URL = f"https://huggingface.co/{MODEL_REPOSITORY}/tree/{MODEL_REVISION}"
CHECKPOINT_SHA256 = "d635794c1fedfdfa261e065370bea59c651fc9bfa65dc6d67ad29e11869a1824"
CHECKPOINT_SIZE_BYTES = 5_214_864_007
CHECKPOINT_DATA_PKL_SHA256 = "33728c2a4da187ee85333cd6934ae6418f61be635415c790124d4c9505766f15"
VAE_CONFIG_SHA256 = "6b194a1bad5f6ab0431cc254088949b814f75d0c3230483ad8fc6be2cc1495a0"
VAE_CONFIG_SIZE_BYTES = 716
VAE_WEIGHTS_SHA256 = "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
VAE_WEIGHTS_SIZE_BYTES = 334_643_276
EXPECTED_VAE_TENSOR_COUNT = 248
EXPECTED_VAE_NUMEL = 83_653_863
EXPECTED_VAE_LOGICAL_BYTES = 334_615_452
CHECKPOINT_PREFIX = "first_stage_model."
MAX_CHECKPOINT_PICKLE_BYTES = 16 * 1024 * 1024

# This is the immutable commit behind the Diffusers v0.10.2 tag.  Its converter
# produces the legacy query/key/value/proj_attn names stored in the pinned VAE.
DIFFUSERS_CONVERTER_COMMIT = "0ca172407db4f0656395bae40ea5848f4918742b"
DIFFUSERS_CONVERTER_URL = (
    "https://github.com/huggingface/diffusers/blob/"
    f"{DIFFUSERS_CONVERTER_COMMIT}/scripts/"
    "convert_original_stable_diffusion_to_diffusers.py#L429-L519"
)
MAPPING_CONTRACT = "sd2-ldm-first-stage-to-diffusers-vae-v1"
EXPECTED_MAPPING_MANIFEST_SHA256 = (
    "f038fc11bb8deb04c612b050baad94e9023639de6ca4270c4d755b66fba5ff9e"
)


class VAEEquivalenceError(RuntimeError):
    """Base error for a verifier precondition or safety failure."""


class ArtifactIntegrityError(VAEEquivalenceError):
    """An artifact does not match its required size or SHA-256 pin."""


class MappingContractError(VAEEquivalenceError):
    """Checkpoint and Diffusers keys do not satisfy the frozen bijection."""


class UnsafeCheckpointError(VAEEquivalenceError):
    """The restricted loader's static scan found a non-allowlisted global."""


_ATTENTION_NAME_TO_LDM = {
    "group_norm": "norm",
    "query": "q",
    "key": "k",
    "value": "v",
    "proj_attn": "proj_out",
}


def checkpoint_key_for_diffusers_key(key: str) -> Tuple[str, str]:
    """Return ``(checkpoint_key, transform)`` for one pinned Diffusers VAE key.

    The mapping is the inverse of the pinned Diffusers conversion script.  It is
    deliberately grammar-based rather than a sequence of unrestricted string
    replacements, so an unfamiliar key fails closed.
    """

    match = re.fullmatch(
        r"(encoder|decoder)\.mid_block\.attentions\.0\."
        r"(group_norm|query|key|value|proj_attn)\.(weight|bias)",
        key,
    )
    if match:
        side, diffusers_name, parameter = match.groups()
        source = (
            f"{CHECKPOINT_PREFIX}{side}.mid.attn_1."
            f"{_ATTENTION_NAME_TO_LDM[diffusers_name]}.{parameter}"
        )
        transform = (
            "squeeze_trailing_singletons"
            if parameter == "weight" and diffusers_name != "group_norm"
            else "identity"
        )
        return source, transform

    match = re.fullmatch(r"(encoder|decoder)\.mid_block\.resnets\.(0|1)\.(.+)", key)
    if match:
        side, block, suffix = match.groups()
        suffix = suffix.replace("conv_shortcut", "nin_shortcut")
        return (
            f"{CHECKPOINT_PREFIX}{side}.mid.block_{int(block) + 1}.{suffix}",
            "identity",
        )

    match = re.fullmatch(r"encoder\.down_blocks\.(\d+)\.resnets\.(\d+)\.(.+)", key)
    if match:
        block, resnet, suffix = match.groups()
        suffix = suffix.replace("conv_shortcut", "nin_shortcut")
        return (
            f"{CHECKPOINT_PREFIX}encoder.down.{block}.block.{resnet}.{suffix}",
            "identity",
        )

    match = re.fullmatch(
        r"encoder\.down_blocks\.(\d+)\.downsamplers\.0\.conv\.(weight|bias)",
        key,
    )
    if match:
        block, parameter = match.groups()
        return (
            f"{CHECKPOINT_PREFIX}encoder.down.{block}.downsample.conv.{parameter}",
            "identity",
        )

    match = re.fullmatch(r"decoder\.up_blocks\.(\d+)\.resnets\.(\d+)\.(.+)", key)
    if match:
        block, resnet, suffix = match.groups()
        block_number = int(block)
        if block_number > 3:
            raise MappingContractError(f"unexpected decoder up-block index: {key}")
        suffix = suffix.replace("conv_shortcut", "nin_shortcut")
        return (
            f"{CHECKPOINT_PREFIX}decoder.up.{3 - block_number}.block.{resnet}.{suffix}",
            "identity",
        )

    match = re.fullmatch(r"decoder\.up_blocks\.(\d+)\.upsamplers\.0\.conv\.(weight|bias)", key)
    if match:
        block, parameter = match.groups()
        block_number = int(block)
        if block_number > 3:
            raise MappingContractError(f"unexpected decoder up-block index: {key}")
        return (
            f"{CHECKPOINT_PREFIX}decoder.up.{3 - block_number}.upsample.conv.{parameter}",
            "identity",
        )

    if key.startswith("encoder.conv_norm_out.") or key.startswith("decoder.conv_norm_out."):
        return (
            CHECKPOINT_PREFIX + key.replace(".conv_norm_out.", ".norm_out."),
            "identity",
        )

    if re.fullmatch(r"(encoder|decoder)\.(conv_in|conv_out)\.(weight|bias)", key) or re.fullmatch(
        r"(quant_conv|post_quant_conv)\.(weight|bias)", key
    ):
        return CHECKPOINT_PREFIX + key, "identity"

    raise MappingContractError(f"unrecognized Diffusers VAE key: {key}")


def build_sd2_vae_key_mapping(
    diffusers_keys: Iterable[str],
    checkpoint_keys: Iterable[str],
    *,
    expected_count: int = EXPECTED_VAE_TENSOR_COUNT,
) -> List[Dict[str, str]]:
    """Build and validate the complete one-to-one checkpoint conversion map."""

    destination = set(diffusers_keys)
    source = {key for key in checkpoint_keys if key.startswith(CHECKPOINT_PREFIX)}
    if len(destination) != expected_count:
        raise MappingContractError(
            f"expected {expected_count} Diffusers tensors, observed {len(destination)}"
        )
    if len(source) != expected_count:
        raise MappingContractError(
            f"expected {expected_count} checkpoint first-stage tensors, observed {len(source)}"
        )

    rows: List[Dict[str, str]] = []
    for destination_key in sorted(destination):
        source_key, transform = checkpoint_key_for_diffusers_key(destination_key)
        rows.append(
            {
                "destination_key": destination_key,
                "source_key": source_key,
                "transform": transform,
            }
        )

    mapped_source = {row["source_key"] for row in rows}
    if len(mapped_source) != len(rows):
        raise MappingContractError("the conversion map is not one-to-one")
    missing = sorted(source - mapped_source)
    unexpected = sorted(mapped_source - source)
    if missing or unexpected:
        raise MappingContractError(
            f"checkpoint key coverage mismatch: missing={missing!r}, unexpected={unexpected!r}"
        )
    return rows


def _artifact_record(
    path: Path, expected_sha256: str, expected_size_bytes: int, label: str
) -> Dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ArtifactIntegrityError(f"{label} does not exist: {resolved}")
    actual_size = resolved.stat().st_size
    if actual_size != expected_size_bytes:
        raise ArtifactIntegrityError(
            f"{label} size mismatch: expected {expected_size_bytes}, observed {actual_size}"
        )
    actual_sha256 = hash_file(resolved)
    if actual_sha256.lower() != expected_sha256.lower():
        raise ArtifactIntegrityError(
            f"{label} SHA-256 mismatch: expected {expected_sha256}, observed {actual_sha256}"
        )
    return {
        "filename": resolved.name,
        "size_bytes": actual_size,
        "sha256": actual_sha256,
        "expected_size_bytes": expected_size_bytes,
        "expected_sha256": expected_sha256.lower(),
        "pin_verified": True,
    }


def _package_version(distribution: str) -> Optional[str]:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _inspect_checkpoint_container(path: Path) -> Dict[str, Any]:
    """Inspect torch-save metadata without executing the checkpoint pickle."""

    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            pickle_names = [name for name in names if name.endswith("/data.pkl")]
            if len(pickle_names) != 1:
                raise VAEEquivalenceError(
                    f"expected one torch data.pkl member, observed {pickle_names!r}"
                )
            pickle_name = pickle_names[0]
            prefix = pickle_name[: -len("data.pkl")]
            pickle_info = archive.getinfo(pickle_name)
            if pickle_info.file_size > MAX_CHECKPOINT_PICKLE_BYTES:
                raise VAEEquivalenceError(
                    "checkpoint data.pkl exceeds the verifier's safety limit: "
                    f"{pickle_info.file_size} > {MAX_CHECKPOINT_PICKLE_BYTES}"
                )
            pickle_payload = archive.read(pickle_name)
            globals_used = set()
            protocol = None
            for opcode, argument, _position in pickletools.genops(pickle_payload):
                if opcode.name == "PROTO":
                    protocol = int(argument)
                elif opcode.name == "GLOBAL":
                    module, name = str(argument).split(" ", 1)
                    globals_used.add(f"{module}.{name}")
            version_name = prefix + "version"
            archive_version = (
                archive.read(version_name).decode("ascii").strip()
                if version_name in names
                else None
            )
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise VAEEquivalenceError("checkpoint is not a readable torch ZIP archive") from exc

    return {
        "archive_entry_count": len(names),
        "archive_version": archive_version,
        "data_pickle_member": pickle_name,
        "data_pickle_size_bytes": len(pickle_payload),
        "data_pickle_sha256": hashlib.sha256(pickle_payload).hexdigest(),
        "pickle_protocol": protocol,
        "pickle_globals": sorted(globals_used),
        "storage_record_count": sum(name.startswith(prefix + "data/") for name in names),
    }


def _tensor_bytes(tensor: Any, torch_module: Any) -> Tuple[Any, Any]:
    value = tensor.detach()
    if value.device.type != "cpu":
        value = value.to(device="cpu")
    if not value.is_contiguous():
        value = value.contiguous()
    byte_array = value.view(torch_module.uint8).reshape(-1).numpy()
    return value, memoryview(byte_array)


def _apply_transform(source: Any, destination_shape: Sequence[int], transform: str) -> Any:
    if transform == "identity":
        return source
    if transform != "squeeze_trailing_singletons":
        raise MappingContractError(f"unknown tensor transform: {transform}")
    if source.ndim != len(destination_shape) + 2 or tuple(source.shape[-2:]) != (1, 1):
        raise MappingContractError(
            "attention conversion requires exactly two trailing singleton dimensions: "
            f"source={tuple(source.shape)}, destination={tuple(destination_shape)}"
        )
    return source[..., 0, 0]


def _update_tensor_set_digest(
    digest: Any,
    *,
    key: str,
    dtype: str,
    shape: Sequence[int],
    payload: memoryview,
) -> None:
    header = json.dumps(
        {"dtype": dtype, "key": key, "shape": list(shape)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    digest.update(len(header).to_bytes(8, "big"))
    digest.update(header)
    digest.update(payload)


def verify_sd2_vae_equivalence(
    checkpoint_path: Path,
    weights_path: Path,
    *,
    config_path: Optional[Path] = None,
    expected_checkpoint_sha256: str = CHECKPOINT_SHA256,
    expected_checkpoint_size_bytes: int = CHECKPOINT_SIZE_BYTES,
    expected_weights_sha256: str = VAE_WEIGHTS_SHA256,
    expected_weights_size_bytes: int = VAE_WEIGHTS_SIZE_BYTES,
    expected_config_sha256: str = VAE_CONFIG_SHA256,
    expected_config_size_bytes: int = VAE_CONFIG_SIZE_BYTES,
    expected_tensor_count: int = EXPECTED_VAE_TENSOR_COUNT,
    model_repository: str = MODEL_REPOSITORY,
    model_revision: str = MODEL_REVISION,
) -> Dict[str, Any]:
    """Compare the pinned full-checkpoint VAE with the VAE safetensors bitwise.

    The checkpoint is loaded explicitly with ``weights_only=True``, on CPU, and
    with ``mmap=True``.  The destination safetensors file is also opened lazily,
    and tensors are compared one at a time.  The 5.2 GB checkpoint is not eagerly
    materialized as a 5.2 GB Python heap allocation; pages touched through the
    memory map can still become resident or enter the operating-system file cache.
    """

    checkpoint_path = Path(checkpoint_path).resolve()
    weights_path = Path(weights_path).resolve()
    config_path = Path(config_path).resolve() if config_path is not None else None

    checkpoint_artifact = _artifact_record(
        checkpoint_path,
        expected_checkpoint_sha256,
        expected_checkpoint_size_bytes,
        "full SD2 checkpoint",
    )
    weights_artifact = _artifact_record(
        weights_path,
        expected_weights_sha256,
        expected_weights_size_bytes,
        "Diffusers VAE weights",
    )
    config_artifact = None
    if config_path is not None:
        config_artifact = _artifact_record(
            config_path,
            expected_config_sha256,
            expected_config_size_bytes,
            "Diffusers VAE config",
        )
    checkpoint_container = _inspect_checkpoint_container(checkpoint_path)
    if (
        expected_checkpoint_sha256.lower() == CHECKPOINT_SHA256
        and checkpoint_container["data_pickle_sha256"] != CHECKPOINT_DATA_PKL_SHA256
    ):
        raise ArtifactIntegrityError(
            "the pinned checkpoint's data.pkl does not match its frozen SHA-256"
        )
    frozen_identity = (
        expected_checkpoint_sha256.lower() == CHECKPOINT_SHA256
        and expected_checkpoint_size_bytes == CHECKPOINT_SIZE_BYTES
        and expected_weights_sha256.lower() == VAE_WEIGHTS_SHA256
        and expected_weights_size_bytes == VAE_WEIGHTS_SIZE_BYTES
        and expected_tensor_count == EXPECTED_VAE_TENSOR_COUNT
        and model_repository == MODEL_REPOSITORY
        and model_revision == MODEL_REVISION
        and config_artifact is not None
        and expected_config_sha256.lower() == VAE_CONFIG_SHA256
        and expected_config_size_bytes == VAE_CONFIG_SIZE_BYTES
    )
    if frozen_identity:
        checkpoint_artifact.update(
            {
                "repository_path": "512-base-ema.ckpt",
                "artifact_url": (
                    f"https://huggingface.co/{MODEL_REPOSITORY}/blob/"
                    f"{MODEL_REVISION}/512-base-ema.ckpt"
                ),
            }
        )
        weights_artifact.update(
            {
                "repository_path": "vae/diffusion_pytorch_model.safetensors",
                "artifact_url": (
                    f"https://huggingface.co/{MODEL_REPOSITORY}/blob/{MODEL_REVISION}/"
                    "vae/diffusion_pytorch_model.safetensors"
                ),
            }
        )
        if config_artifact is not None and config_artifact["sha256"] == VAE_CONFIG_SHA256:
            config_artifact.update(
                {
                    "repository_path": "vae/config.json",
                    "artifact_url": (
                        f"https://huggingface.co/{MODEL_REPOSITORY}/blob/"
                        f"{MODEL_REVISION}/vae/config.json"
                    ),
                }
            )

    try:
        import torch
        from safetensors import safe_open
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise VAEEquivalenceError(
            "learned-feature dependencies are required; install the 'learned' extra"
        ) from exc

    unsafe_globals = sorted(
        torch.serialization.get_unsafe_globals_in_checkpoint(checkpoint_path)
    )
    if unsafe_globals:
        raise UnsafeCheckpointError(
            f"checkpoint requires globals outside the weights-only allowlist: {unsafe_globals!r}"
        )

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=True,
        mmap=True,
    )
    if not isinstance(checkpoint, Mapping):
        raise VAEEquivalenceError("checkpoint root is not a mapping")
    state_dict = checkpoint.get("state_dict")
    if not isinstance(state_dict, Mapping):
        raise VAEEquivalenceError("checkpoint has no mapping-valued state_dict")

    source_keys = set(state_dict)
    source_first_stage_keys = {
        key for key in source_keys if isinstance(key, str) and key.startswith(CHECKPOINT_PREFIX)
    }
    source_digest = hashlib.sha256()
    destination_digest = hashlib.sha256()
    per_tensor: List[Dict[str, Any]] = []
    source_dtypes: Counter[str] = Counter()
    destination_dtypes: Counter[str] = Counter()
    total_numel = 0
    total_logical_bytes = 0

    with safe_open(str(weights_path), framework="pt", device="cpu") as handle:
        destination_keys = set(handle.keys())
        mapping = build_sd2_vae_key_mapping(
            destination_keys,
            source_first_stage_keys,
            expected_count=expected_tensor_count,
        )
        safetensors_metadata = handle.metadata() or {}

        for row in mapping:
            destination_key = row["destination_key"]
            source_key = row["source_key"]
            destination = handle.get_tensor(destination_key)
            source_before_transform = state_dict[source_key]
            source_shape_before_transform = list(source_before_transform.shape)
            source = _apply_transform(
                source_before_transform, tuple(destination.shape), row["transform"]
            )
            source, source_payload = _tensor_bytes(source, torch)
            destination, destination_payload = _tensor_bytes(destination, torch)
            source_dtype = str(source.dtype).replace("torch.", "")
            destination_dtype = str(destination.dtype).replace("torch.", "")
            source_shape = list(source.shape)
            destination_shape = list(destination.shape)
            source_hash = hashlib.sha256(source_payload).hexdigest()
            destination_hash = hashlib.sha256(destination_payload).hexdigest()
            shape_equal = source_shape == destination_shape
            dtype_equal = source_dtype == destination_dtype
            bitwise_equal = shape_equal and dtype_equal and source_hash == destination_hash
            torch_equal = (
                bool(torch.equal(source, destination)) if shape_equal and dtype_equal else False
            )

            _update_tensor_set_digest(
                source_digest,
                key=destination_key,
                dtype=source_dtype,
                shape=source_shape,
                payload=source_payload,
            )
            _update_tensor_set_digest(
                destination_digest,
                key=destination_key,
                dtype=destination_dtype,
                shape=destination_shape,
                payload=destination_payload,
            )
            source_dtypes[source_dtype] += 1
            destination_dtypes[destination_dtype] += 1
            total_numel += destination.numel()
            total_logical_bytes += destination.numel() * destination.element_size()
            per_tensor.append(
                {
                    **row,
                    "source_shape_before_transform": source_shape_before_transform,
                    "source_shape_after_transform": source_shape,
                    "destination_shape": destination_shape,
                    "source_dtype": source_dtype,
                    "destination_dtype": destination_dtype,
                    "source_payload_sha256": source_hash,
                    "destination_payload_sha256": destination_hash,
                    "shape_equal": shape_equal,
                    "dtype_equal": dtype_equal,
                    "bitwise_equal": bitwise_equal,
                    "torch_equal": torch_equal,
                    "numel": destination.numel(),
                }
            )

    exact_equal_count = sum(row["bitwise_equal"] for row in per_tensor)
    torch_equal_count = sum(row["torch_equal"] for row in per_tensor)
    mapping_identity = [
        {
            "destination_key": row["destination_key"],
            "source_key": row["source_key"],
            "transform": row["transform"],
        }
        for row in per_tensor
    ]
    mapping_manifest_sha256 = stable_hash(mapping_identity)
    if (
        expected_tensor_count == EXPECTED_VAE_TENSOR_COUNT
        and mapping_manifest_sha256 != EXPECTED_MAPPING_MANIFEST_SHA256
    ):
        raise MappingContractError(
            "the complete conversion map does not match the frozen mapping-manifest pin"
        )
    source_set_hash = source_digest.hexdigest()
    destination_set_hash = destination_digest.hexdigest()
    mismatch_rows = [
        {
            "destination_key": row["destination_key"],
            "source_key": row["source_key"],
            "shape_equal": row["shape_equal"],
            "dtype_equal": row["dtype_equal"],
            "bitwise_equal": row["bitwise_equal"],
            "torch_equal": row["torch_equal"],
        }
        for row in per_tensor
        if not row["bitwise_equal"]
    ]
    status = (
        "pass"
        if len(per_tensor) == expected_tensor_count
        and exact_equal_count == expected_tensor_count
        and source_set_hash == destination_set_hash
        and (
            expected_tensor_count != EXPECTED_VAE_TENSOR_COUNT
            or (
                total_numel == EXPECTED_VAE_NUMEL
                and total_logical_bytes == EXPECTED_VAE_LOGICAL_BYTES
            )
        )
        else "fail"
    )

    # Close the path-level time-of-check/time-of-use window: each file is
    # re-opened and re-hashed after every tensor comparison. A concurrent
    # replacement therefore fails before durable evidence can be emitted.
    _artifact_record(
        checkpoint_path,
        checkpoint_artifact["sha256"],
        checkpoint_artifact["size_bytes"],
        "full SD2 checkpoint after comparison",
    )
    _artifact_record(
        weights_path,
        weights_artifact["sha256"],
        weights_artifact["size_bytes"],
        "Diffusers VAE weights after comparison",
    )
    if config_path is not None and config_artifact is not None:
        _artifact_record(
            config_path,
            config_artifact["sha256"],
            config_artifact["size_bytes"],
            "Diffusers VAE config after comparison",
        )
    checkpoint_artifact["post_comparison_pin_reverified"] = True
    weights_artifact["post_comparison_pin_reverified"] = True
    if config_artifact is not None:
        config_artifact["post_comparison_pin_reverified"] = True

    module_path = Path(__file__).resolve()
    return {
        "schema_version": "1.0",
        "record_type": "sd2_vae_tensor_equivalence",
        "verification_status": status,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "claim": (
            (
                "The Diffusers VAE tensors are bit-for-bit equal to the mapped "
                "first_stage_model tensors in the pinned full SD2 checkpoint."
                if frozen_identity
                else "The supplied destination tensors are bit-for-bit equal to their mapped "
                "source-checkpoint tensors."
            )
            if status == "pass"
            else "The supplied source-checkpoint and destination tensors are not equivalent."
        ),
        "model": {
            "repository": model_repository,
            "revision": model_revision,
            "identity_profile": "pinned_sd2_base" if frozen_identity else "custom",
            "revision_url": MODEL_REVISION_URL if frozen_identity else None,
        },
        "artifacts": {
            "full_checkpoint": checkpoint_artifact,
            "vae_weights": weights_artifact,
            "vae_config": config_artifact,
        },
        "loader": {
            "weights_only": True,
            "weights_only_load_succeeded": True,
            "unsafe_globals": unsafe_globals,
            "mmap": True,
            "map_location": "cpu",
            "torch_version": getattr(torch, "__version__", None),
            "safetensors_version": _package_version("safetensors"),
            "python_version": sys.version.split()[0],
            "host_byteorder": sys.byteorder,
        },
        "checkpoint_metadata": {
            "container": checkpoint_container,
            "root_keys": sorted(str(key) for key in checkpoint),
            "state_dict_tensor_count": len(state_dict),
            "epoch": checkpoint.get("epoch"),
            "global_step": checkpoint.get("global_step"),
            "pytorch_lightning_version": checkpoint.get("pytorch-lightning_version"),
        },
        "mapping": {
            "contract": MAPPING_CONTRACT,
            "reference_commit": DIFFUSERS_CONVERTER_COMMIT,
            "reference_url": DIFFUSERS_CONVERTER_URL,
            "manifest_sha256": mapping_manifest_sha256,
            "expected_manifest_sha256": (
                EXPECTED_MAPPING_MANIFEST_SHA256
                if expected_tensor_count == EXPECTED_VAE_TENSOR_COUNT
                else None
            ),
            "expected_tensor_count": expected_tensor_count,
            "checkpoint_first_stage_tensor_count": len(source_first_stage_keys),
            "destination_tensor_count": len(per_tensor),
            "mapped_unique_source_count": len({row["source_key"] for row in per_tensor}),
            "mapped_unique_destination_count": len({row["destination_key"] for row in per_tensor}),
            "attention_weight_transform_count": sum(
                row["transform"] == "squeeze_trailing_singletons" for row in per_tensor
            ),
        },
        "comparison": {
            "exact_equal_count": exact_equal_count,
            "torch_equal_count": torch_equal_count,
            "mismatch_count": len(mismatch_rows),
            "mismatches": mismatch_rows,
            "total_numel": total_numel,
            "logical_tensor_bytes": total_logical_bytes,
            "expected_total_numel": (
                EXPECTED_VAE_NUMEL if expected_tensor_count == EXPECTED_VAE_TENSOR_COUNT else None
            ),
            "expected_logical_tensor_bytes": (
                EXPECTED_VAE_LOGICAL_BYTES
                if expected_tensor_count == EXPECTED_VAE_TENSOR_COUNT
                else None
            ),
            "source_dtype_counts": dict(sorted(source_dtypes.items())),
            "destination_dtype_counts": dict(sorted(destination_dtypes.items())),
            "canonical_source_tensor_set_sha256": source_set_hash,
            "canonical_destination_tensor_set_sha256": destination_set_hash,
            "canonical_tensor_sets_equal": source_set_hash == destination_set_hash,
        },
        "safetensors_metadata": safetensors_metadata,
        "scope": {
            "supports": [
                "exact tensor payload equivalence after the frozen key mapping",
                "the eight documented trailing-singleton attention-weight squeezes",
            ],
            "does_not_establish": [
                "semantic configuration equivalence from file-hash verification alone",
                "inference-output identity across Diffusers or PyTorch versions",
                "reproduction of Kim et al.'s unpublished A-vectors or RNG realization",
                (
                    "that the recovered public-mirror checkpoint is the exact file used by "
                    "Kim et al.; the paper and author repository publish no checkpoint digest "
                    "or chain of custody"
                ),
            ],
        },
        "per_tensor": per_tensor,
        "verifier": {
            "module": "latent_art_bench.evaluation.vae_equivalence",
            "module_filename": module_path.name,
            "module_sha256": hash_file(module_path),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify the pinned SD2 full checkpoint and Diffusers VAE bitwise."
    )
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("vae_weights", type=Path)
    parser.add_argument("--vae-config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        evidence = verify_sd2_vae_equivalence(
            args.checkpoint,
            args.vae_weights,
            config_path=args.vae_config,
        )
    except VAEEquivalenceError as exc:
        print(f"verification error: {exc}", file=sys.stderr)
        return 2
    write_json(args.output, evidence)
    print(
        json.dumps(
            {
                "evidence_path": str(args.output.resolve()),
                "verification_status": evidence["verification_status"],
                "exact_equal_count": evidence["comparison"]["exact_equal_count"],
                "expected_tensor_count": evidence["mapping"]["expected_tensor_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if evidence["verification_status"] == "pass" else 1


if __name__ == "__main__":  # pragma: no cover - exercised through the module CLI
    raise SystemExit(main())
