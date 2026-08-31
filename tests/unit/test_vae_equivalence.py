from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from latent_art_bench.evaluation.vae_equivalence import (
    EXPECTED_MAPPING_MANIFEST_SHA256,
    ArtifactIntegrityError,
    MappingContractError,
    UnsafeCheckpointError,
    _apply_transform,
    build_sd2_vae_key_mapping,
    checkpoint_key_for_diffusers_key,
    verify_sd2_vae_equivalence,
)
from latent_art_bench.io import stable_hash

torch = pytest.importorskip("torch")
safetensors_torch = pytest.importorskip("safetensors.torch")


class NotAllowlisted:
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _small_artifacts(tmp_path: Path, *, destination_delta: float = 0.0):
    checkpoint_path = tmp_path / "source.ckpt"
    weights_path = tmp_path / "vae.safetensors"
    direct = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    attention = torch.arange(20, dtype=torch.float32).reshape(4, 5, 1, 1)
    torch.save(
        {
            "epoch": 1,
            "global_step": 7,
            "pytorch-lightning_version": "test",
            "state_dict": {
                "first_stage_model.encoder.conv_in.weight": direct,
                "first_stage_model.encoder.mid.attn_1.q.weight": attention,
            },
        },
        checkpoint_path,
    )
    destination_attention = attention[:, :, 0, 0].clone()
    destination_attention[0, 0] += destination_delta
    safetensors_torch.save_file(
        {
            "encoder.conv_in.weight": direct.clone(),
            "encoder.mid_block.attentions.0.query.weight": destination_attention,
        },
        weights_path,
        metadata={"format": "pt"},
    )
    return checkpoint_path, weights_path


def _verify_small(checkpoint_path: Path, weights_path: Path):
    return verify_sd2_vae_equivalence(
        checkpoint_path,
        weights_path,
        expected_checkpoint_sha256=_sha256(checkpoint_path),
        expected_checkpoint_size_bytes=checkpoint_path.stat().st_size,
        expected_weights_sha256=_sha256(weights_path),
        expected_weights_size_bytes=weights_path.stat().st_size,
        expected_tensor_count=2,
        model_repository="test/repository",
        model_revision="1" * 40,
    )


def _all_diffusers_keys():
    keys = set()
    for side in ("encoder", "decoder"):
        for layer in ("conv_in", "conv_norm_out", "conv_out"):
            for parameter in ("weight", "bias"):
                keys.add(f"{side}.{layer}.{parameter}")
        for block in (0, 1):
            for layer in ("norm1", "conv1", "norm2", "conv2"):
                for parameter in ("weight", "bias"):
                    keys.add(f"{side}.mid_block.resnets.{block}.{layer}.{parameter}")
        for layer in ("group_norm", "query", "key", "value", "proj_attn"):
            for parameter in ("weight", "bias"):
                keys.add(f"{side}.mid_block.attentions.0.{layer}.{parameter}")

    for layer in ("quant_conv", "post_quant_conv"):
        for parameter in ("weight", "bias"):
            keys.add(f"{layer}.{parameter}")

    for block in range(4):
        for resnet in range(2):
            for layer in ("norm1", "conv1", "norm2", "conv2"):
                for parameter in ("weight", "bias"):
                    keys.add(f"encoder.down_blocks.{block}.resnets.{resnet}.{layer}.{parameter}")
    for block in (1, 2):
        for parameter in ("weight", "bias"):
            keys.add(f"encoder.down_blocks.{block}.resnets.0.conv_shortcut.{parameter}")
    for block in range(3):
        for parameter in ("weight", "bias"):
            keys.add(f"encoder.down_blocks.{block}.downsamplers.0.conv.{parameter}")

    for block in range(4):
        for resnet in range(3):
            for layer in ("norm1", "conv1", "norm2", "conv2"):
                for parameter in ("weight", "bias"):
                    keys.add(f"decoder.up_blocks.{block}.resnets.{resnet}.{layer}.{parameter}")
    for block in (2, 3):
        for parameter in ("weight", "bias"):
            keys.add(f"decoder.up_blocks.{block}.resnets.0.conv_shortcut.{parameter}")
    for block in range(3):
        for parameter in ("weight", "bias"):
            keys.add(f"decoder.up_blocks.{block}.upsamplers.0.conv.{parameter}")
    return keys


def test_frozen_mapping_is_a_248_key_bijection() -> None:
    destination = _all_diffusers_keys()
    source = {checkpoint_key_for_diffusers_key(key)[0] for key in destination}

    rows = build_sd2_vae_key_mapping(destination, source)

    assert len(destination) == 248
    assert len(rows) == 248
    assert len({row["source_key"] for row in rows}) == 248
    assert sum(row["transform"] == "squeeze_trailing_singletons" for row in rows) == 8
    assert stable_hash(rows) == EXPECTED_MAPPING_MANIFEST_SHA256


@pytest.mark.parametrize(
    ("destination", "source"),
    [
        (
            "encoder.conv_norm_out.weight",
            "first_stage_model.encoder.norm_out.weight",
        ),
        (
            "encoder.down_blocks.2.resnets.0.conv_shortcut.weight",
            "first_stage_model.encoder.down.2.block.0.nin_shortcut.weight",
        ),
        (
            "decoder.up_blocks.0.upsamplers.0.conv.bias",
            "first_stage_model.decoder.up.3.upsample.conv.bias",
        ),
        (
            "decoder.up_blocks.3.resnets.2.norm2.bias",
            "first_stage_model.decoder.up.0.block.2.norm2.bias",
        ),
    ],
)
def test_mapping_examples(destination: str, source: str) -> None:
    assert checkpoint_key_for_diffusers_key(destination)[0] == source


def test_mapping_fails_closed_for_unknown_key() -> None:
    with pytest.raises(MappingContractError, match="unrecognized"):
        checkpoint_key_for_diffusers_key("encoder.future_block.weight")


def test_attention_transform_only_squeezes_trailing_singletons() -> None:
    tensor = torch.zeros((2, 3, 1, 1), dtype=torch.float32)
    assert tuple(_apply_transform(tensor, (2, 3), "squeeze_trailing_singletons").shape) == (2, 3)

    with pytest.raises(MappingContractError, match="exactly two"):
        _apply_transform(
            torch.zeros((2, 3, 2), dtype=torch.float32),
            (2, 3),
            "squeeze_trailing_singletons",
        )
    with pytest.raises(MappingContractError, match="exactly two"):
        _apply_transform(
            torch.zeros((2, 3, 1, 1, 1), dtype=torch.float32),
            (2, 3),
            "squeeze_trailing_singletons",
        )


def test_verifier_uses_restricted_mmap_loader_and_emits_complete_evidence(
    tmp_path: Path,
) -> None:
    checkpoint_path, weights_path = _small_artifacts(tmp_path)

    evidence = _verify_small(checkpoint_path, weights_path)

    assert evidence["verification_status"] == "pass"
    assert evidence["loader"]["weights_only"] is True
    assert evidence["loader"]["weights_only_load_succeeded"] is True
    assert evidence["loader"]["mmap"] is True
    assert evidence["loader"]["unsafe_globals"] == []
    assert evidence["checkpoint_metadata"]["container"]["pickle_protocol"] is not None
    assert evidence["checkpoint_metadata"]["container"]["storage_record_count"] == 2
    assert evidence["mapping"]["expected_tensor_count"] == 2
    assert evidence["mapping"]["attention_weight_transform_count"] == 1
    assert evidence["comparison"]["exact_equal_count"] == 2
    assert evidence["comparison"]["mismatch_count"] == 0
    assert evidence["comparison"]["canonical_tensor_sets_equal"] is True
    assert len(evidence["per_tensor"]) == 2
    assert all(row["source_payload_sha256"] for row in evidence["per_tensor"])
    assert "path" not in evidence["artifacts"]["full_checkpoint"]
    assert evidence["artifacts"]["full_checkpoint"]["post_comparison_pin_reverified"]
    assert evidence["model"]["identity_profile"] == "custom"
    assert "module_path" not in evidence["verifier"]


def test_verifier_records_a_bitwise_tensor_mismatch(tmp_path: Path) -> None:
    checkpoint_path, weights_path = _small_artifacts(tmp_path, destination_delta=1.0)

    evidence = _verify_small(checkpoint_path, weights_path)

    assert evidence["verification_status"] == "fail"
    assert evidence["comparison"]["exact_equal_count"] == 1
    assert evidence["comparison"]["mismatch_count"] == 1
    assert evidence["comparison"]["canonical_tensor_sets_equal"] is False
    assert evidence["comparison"]["mismatches"][0]["destination_key"].endswith("query.weight")


def test_artifact_pin_is_checked_before_deserialization(tmp_path: Path) -> None:
    checkpoint_path, weights_path = _small_artifacts(tmp_path)

    with pytest.raises(ArtifactIntegrityError, match="SHA-256 mismatch"):
        verify_sd2_vae_equivalence(
            checkpoint_path,
            weights_path,
            expected_checkpoint_sha256="0" * 64,
            expected_checkpoint_size_bytes=checkpoint_path.stat().st_size,
            expected_weights_sha256=_sha256(weights_path),
            expected_weights_size_bytes=weights_path.stat().st_size,
            expected_tensor_count=2,
        )


def test_non_allowlisted_checkpoint_global_is_rejected(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "unsafe.ckpt"
    weights_path = tmp_path / "vae.safetensors"
    torch.save(
        {
            "payload": NotAllowlisted(),
            "state_dict": {"first_stage_model.encoder.conv_in.weight": torch.zeros(1)},
        },
        checkpoint_path,
    )
    safetensors_torch.save_file({"encoder.conv_in.weight": torch.zeros(1)}, weights_path)

    with pytest.raises(UnsafeCheckpointError, match="outside the weights-only allowlist"):
        verify_sd2_vae_equivalence(
            checkpoint_path,
            weights_path,
            expected_checkpoint_sha256=_sha256(checkpoint_path),
            expected_checkpoint_size_bytes=checkpoint_path.stat().st_size,
            expected_weights_sha256=_sha256(weights_path),
            expected_weights_size_bytes=weights_path.stat().st_size,
            expected_tensor_count=1,
        )
