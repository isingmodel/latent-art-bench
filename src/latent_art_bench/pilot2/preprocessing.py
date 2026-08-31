"""One lossless, content-addressed PNG domain for all pilot_2 images."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageCms, ImageOps

from latent_art_bench.io import hash_bytes, hash_file, stable_hash
from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig
from latent_art_bench.pilot2.schemas import Pilot2AcquiredImage, Pilot2DerivedInput


class Pilot2PreprocessingError(RuntimeError):
    pass


def _srgb_with_alpha(image: Image.Image) -> Image.Image:
    """Convert embedded profiles before alpha compositing.

    This mirrors the established preprocessing policy without importing its
    pilot_1 configuration type or altering that evidence closure.
    """

    has_alpha = "A" in image.getbands() or "transparency" in image.info
    alpha = image.convert("RGBA").getchannel("A") if has_alpha else None
    embedded_profile = image.info.get("icc_profile")
    if embedded_profile:
        try:
            source = ImageCms.ImageCmsProfile(io.BytesIO(embedded_profile))
            target = ImageCms.createProfile("sRGB")
            profile_input = image.convert("RGB") if has_alpha else image
            color = ImageCms.profileToProfile(
                profile_input,
                source,
                target,
                renderingIntent=0,
                outputMode="RGB",
            )
        except Exception as exc:
            raise Pilot2PreprocessingError(f"embedded ICC conversion failed: {exc}") from exc
    else:
        color = image.convert("RGB")
    if alpha is not None:
        color.putalpha(alpha)
    return color


def common_png_bytes(
    image: Image.Image, config: Pilot2PreprocessingConfig
) -> Tuple[bytes, Tuple[int, int]]:
    """Normalize decoded pixels and serialize only a lossless PNG container."""

    image = ImageOps.exif_transpose(image)
    image = _srgb_with_alpha(image)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, tuple(config.alpha_background_rgb))
        background.paste(image, mask=image.getchannel("A"))
        image = background
    else:
        image = image.convert("RGB")

    longest = max(image.size)
    if longest > config.max_long_side:
        scale = config.max_long_side / float(longest)
        target = tuple(max(1, round(dimension * scale)) for dimension in image.size)
        image = image.resize(target, Image.Resampling.LANCZOS, reducing_gap=3.0)

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    encoded = output.getvalue()
    with Image.open(io.BytesIO(encoded)) as verification:
        if verification.format != "PNG" or verification.mode != "RGB":
            raise Pilot2PreprocessingError("common input did not serialize as RGB PNG")
        verification.load()
    return encoded, image.size


def preprocess_common_png(
    source_path: Path,
    source_record_id: str,
    output_dir: Path,
    config: Pilot2PreprocessingConfig,
    *,
    expected_source_sha256: Optional[str] = None,
) -> Pilot2DerivedInput:
    source_path = Path(source_path)
    if not source_path.is_file():
        raise Pilot2PreprocessingError(f"missing pilot_2 input: {source_path}")
    source_sha256 = hash_file(source_path)
    if expected_source_sha256 is not None and source_sha256 != expected_source_sha256:
        raise Pilot2PreprocessingError(
            f"source hash mismatch: expected {expected_source_sha256}, found {source_sha256}"
        )
    try:
        with Image.open(source_path) as image:
            source_width, source_height = image.size
            source_format = (image.format or "unknown").casefold()
            encoded, (width, height) = common_png_bytes(image, config)
    except Pilot2PreprocessingError:
        raise
    except Exception as exc:
        raise Pilot2PreprocessingError(f"cannot decode {source_path}: {exc}") from exc

    output_sha256 = hash_bytes(encoded)
    output_path = Path(output_dir) / output_sha256[:2] / f"{output_sha256}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        if hash_file(output_path) != output_sha256:
            raise Pilot2PreprocessingError(f"content-address collision at {output_path}")
    else:
        output_path.write_bytes(encoded)

    config_hash = stable_hash(config.model_dump(mode="json"))
    derived_id = stable_hash(
        {
            "source_record_id": source_record_id,
            "source_sha256": source_sha256,
            "output_sha256": output_sha256,
            "preprocessing_config_sha256": config_hash,
        }
    )
    return Pilot2DerivedInput(
        derived_input_id=f"pilot2-input-{derived_id[:24]}",
        source_record_id=source_record_id,
        source_path=str(source_path),
        source_sha256=source_sha256,
        output_path=str(output_path),
        output_sha256=output_sha256,
        preprocessing_config_sha256=config_hash,
        source_width=source_width,
        source_height=source_height,
        source_decoded_format=source_format,
        width=width,
        height=height,
    )


def preprocess_acquired_image(
    record: Pilot2AcquiredImage,
    root: Path,
    output_dir: Path,
    config: Pilot2PreprocessingConfig,
) -> Pilot2DerivedInput:
    path = Path(record.local_path)
    if not path.is_absolute():
        path = Path(root) / path
    derived = preprocess_common_png(
        path,
        record.canonical_work_id,
        output_dir,
        config,
        expected_source_sha256=record.sha256,
    )
    observed = (
        derived.source_width,
        derived.source_height,
        derived.source_decoded_format,
    )
    expected = (record.decoded_width, record.decoded_height, record.decoded_format)
    if observed != expected:
        raise Pilot2PreprocessingError(
            f"acquired-image decode metadata is stale: {record.canonical_work_id}"
        )
    return derived
