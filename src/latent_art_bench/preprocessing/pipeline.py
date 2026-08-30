from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, List

from PIL import Image, ImageCms, ImageOps

from latent_art_bench.config import PreprocessingConfig
from latent_art_bench.io import hash_bytes, hash_file, stable_hash, utc_now
from latent_art_bench.schemas import DerivedViewRecord, ReproductionRecord


class PreprocessingError(RuntimeError):
    pass


def _convert_to_srgb(image: Image.Image) -> Image.Image:
    has_alpha = "A" in image.getbands() or "transparency" in image.info
    alpha = image.convert("RGBA").getchannel("A") if has_alpha else None
    embedded_profile = image.info.get("icc_profile")
    if embedded_profile:
        try:
            source_profile = ImageCms.ImageCmsProfile(io.BytesIO(embedded_profile))
            target_profile = ImageCms.createProfile("sRGB")
            profile_input = image.convert("RGB") if has_alpha else image
            color = ImageCms.profileToProfile(
                profile_input,
                source_profile,
                target_profile,
                renderingIntent=0,
                outputMode="RGB",
            )
        except Exception as exc:
            raise PreprocessingError(f"embedded ICC conversion failed: {exc}") from exc
    else:
        color = image.convert("RGB")
    if alpha is not None:
        color.putalpha(alpha)
    return color


def preprocess_image_bytes(image: Image.Image, config: PreprocessingConfig) -> tuple:
    if config.border_policy != "keep":
        raise PreprocessingError("pilot_0 implements only the frozen 'keep' border policy")
    image = ImageOps.exif_transpose(image)
    image = _convert_to_srgb(image)

    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, tuple(config.alpha_background_rgb))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")

    width, height = image.size
    longest = max(width, height)
    if longest > config.max_long_side:
        scale = config.max_long_side / float(longest)
        target = (max(1, round(width * scale)), max(1, round(height * scale)))
        image = image.resize(target, resample=Image.Resampling.LANCZOS, reducing_gap=3.0)

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue(), image.size


def preprocess_reproduction(
    record: ReproductionRecord,
    config: PreprocessingConfig,
    root: Path,
    output_dir: Path,
) -> DerivedViewRecord:
    source_path = Path(record.local_path)
    if not source_path.is_absolute():
        source_path = root / source_path
    if not source_path.is_file():
        raise PreprocessingError(f"missing input for {record.reproduction_id}: {source_path}")

    source_sha256 = hash_file(source_path)
    if record.sha256 and source_sha256 != record.sha256:
        raise PreprocessingError(
            f"source hash mismatch for {record.reproduction_id}: expected {record.sha256}, "
            f"found {source_sha256}"
        )
    try:
        with Image.open(source_path) as image:
            encoded, (width, height) = preprocess_image_bytes(image, config)
    except PreprocessingError:
        raise
    except Exception as exc:
        raise PreprocessingError(f"cannot preprocess {record.reproduction_id}: {exc}") from exc

    output_sha256 = hash_bytes(encoded)
    output_path = output_dir / output_sha256[:2] / f"{output_sha256}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        if hash_file(output_path) != output_sha256:
            raise PreprocessingError(f"content-address collision at {output_path}")
    else:
        output_path.write_bytes(encoded)

    config_hash = stable_hash(config.model_dump(mode="json"))
    view_hash = stable_hash(
        {
            "reproduction_id": record.reproduction_id,
            "source_sha256": source_sha256,
            "output_sha256": output_sha256,
            "config_hash": config_hash,
        }
    )
    try:
        stored_path = str(output_path.relative_to(root))
    except ValueError:
        stored_path = str(output_path)
    return DerivedViewRecord(
        derived_view_id=f"view-{view_hash[:24]}",
        reproduction_id=record.reproduction_id,
        canonical_work_id=record.canonical_work_id,
        source_sha256=source_sha256,
        output_path=stored_path,
        output_sha256=output_sha256,
        preprocessing_track=config.track,
        preprocessing_version=config.version,
        preprocessing_config_hash=config_hash,
        width=width,
        height=height,
        alpha_background_rgb=config.alpha_background_rgb,
        border_policy=config.border_policy,
        upsampled=False,
        created_at=utc_now(),
    )


def preprocess_reproductions(
    records: Iterable[ReproductionRecord],
    config: PreprocessingConfig,
    root: Path,
    output_dir: Path,
) -> List[DerivedViewRecord]:
    return [preprocess_reproduction(row, config, root, output_dir) for row in records]
