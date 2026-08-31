"""Deterministic, metadata-free common PNG serialization for Pilot 3.

Pilot 2's historical serializer is intentionally left unchanged.  Pilot 3 uses this
prospective v2 serializer after the preprocessing-determinism incident: embedded colour
profiles are still applied to the pixels, but no source or generated metadata is carried
into the content-addressed PNG container.
"""

from __future__ import annotations

import io
import platform
import struct
import sys
import zlib

import PIL
from PIL import Image, ImageCms, ImageOps, features

from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig

PILOT3_NORMALIZATION_PROTOCOL_VERSION = (
    "pilot3-common-lossless-png-v2-metadata-free"
)
PILOT3_CANONICAL_PNG_CHUNKS = ("IHDR", "IDAT", "IEND")


class Pilot3PreprocessingError(RuntimeError):
    """Raised when the Pilot-3 canonical PNG cannot be produced or verified."""


def pilot3_normalization_runtime_fingerprint() -> dict[str, str]:
    """Return the exact decoder/colour/encoder runtime that v2 authorizes."""

    versions = {
        name: features.version(name)
        for name in ("jpg", "jpg_2000", "zlib", "libtiff", "littlecms2", "webp")
    }
    if any(not isinstance(value, str) or not value for value in versions.values()):
        raise Pilot3PreprocessingError(
            "Pilot-3 normalization runtime lacks a required codec version"
        )
    return {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": str(sys.implementation.cache_tag),
        "platform_system": platform.system(),
        "platform_machine": platform.machine(),
        "pillow_version": PIL.__version__,
        "pillow_jpeg_version": versions["jpg"],
        "pillow_jpeg2000_version": versions["jpg_2000"],
        "pillow_zlib_version": versions["zlib"],
        "pillow_libtiff_version": versions["libtiff"],
        "pillow_littlecms2_version": versions["littlecms2"],
        "pillow_webp_version": versions["webp"],
        "python_zlib_compile_version": zlib.ZLIB_VERSION,
        "python_zlib_runtime_version": zlib.ZLIB_RUNTIME_VERSION,
    }


def _srgb_pixels_with_alpha(image: Image.Image) -> Image.Image:
    """Apply an embedded profile while retaining alpha solely as pixel data."""

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
            raise Pilot3PreprocessingError(
                f"embedded ICC conversion failed: {exc}"
            ) from exc
    else:
        color = image.convert("RGB")
    if alpha is not None:
        color.putalpha(alpha)
    return color


def _metadata_free_rgb(image: Image.Image) -> Image.Image:
    """Detach pixels from all Pillow ``info`` metadata before serialization."""

    rgb = image.convert("RGB")
    return Image.frombytes("RGB", rgb.size, rgb.tobytes())


def png_chunk_types(payload: bytes) -> tuple[str, ...]:
    """Return a strictly parsed PNG chunk sequence, validating every CRC."""

    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise Pilot3PreprocessingError("canonical payload lacks the PNG signature")
    offset = 8
    chunks = []
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise Pilot3PreprocessingError("canonical PNG has a truncated chunk")
        length = struct.unpack(">I", payload[offset : offset + 4])[0]
        end = offset + 12 + length
        if end > len(payload):
            raise Pilot3PreprocessingError("canonical PNG chunk exceeds the payload")
        raw_type = payload[offset + 4 : offset + 8]
        try:
            chunk_type = raw_type.decode("ascii")
        except UnicodeDecodeError as exc:
            raise Pilot3PreprocessingError("canonical PNG chunk type is not ASCII") from exc
        data = payload[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", payload[offset + 8 + length : end])[0]
        observed_crc = zlib.crc32(raw_type)
        observed_crc = zlib.crc32(data, observed_crc) & 0xFFFFFFFF
        if observed_crc != expected_crc:
            raise Pilot3PreprocessingError("canonical PNG chunk CRC is stale")
        if len(chunk_type) != 4 or not chunk_type.isalpha():
            raise Pilot3PreprocessingError("canonical PNG chunk type is malformed")
        if chunk_type == "IHDR" and length != 13:
            raise Pilot3PreprocessingError("canonical PNG IHDR has the wrong length")
        if chunk_type == "IEND" and length != 0:
            raise Pilot3PreprocessingError("canonical PNG IEND has the wrong length")
        chunks.append(chunk_type)
        offset = end
        if chunk_type == "IEND":
            break
    idat_indices = [index for index, value in enumerate(chunks) if value == "IDAT"]
    if (
        offset != len(payload)
        or not chunks
        or chunks[0] != "IHDR"
        or chunks.count("IHDR") != 1
        or chunks[-1] != "IEND"
        or chunks.count("IEND") != 1
        or not idat_indices
        or idat_indices != list(range(idat_indices[0], idat_indices[-1] + 1))
        or any(chunk not in PILOT3_CANONICAL_PNG_CHUNKS for chunk in chunks)
    ):
        raise Pilot3PreprocessingError("canonical PNG has trailing or missing data")
    return tuple(chunks)


def pilot3_common_png_bytes(
    image: Image.Image, config: Pilot2PreprocessingConfig
) -> tuple[bytes, tuple[int, int]]:
    """Normalize pixels and emit a deterministic RGB PNG with no ancillary chunks."""

    transformed = ImageOps.exif_transpose(image)
    transformed = _srgb_pixels_with_alpha(transformed)
    if transformed.mode == "RGBA":
        background = Image.new(
            "RGB", transformed.size, tuple(config.alpha_background_rgb)
        )
        background.paste(transformed, mask=transformed.getchannel("A"))
        transformed = background
    else:
        transformed = transformed.convert("RGB")

    longest = max(transformed.size)
    if longest > config.max_long_side:
        scale = config.max_long_side / float(longest)
        target = tuple(
            max(1, round(dimension * scale)) for dimension in transformed.size
        )
        transformed = transformed.resize(
            target, Image.Resampling.LANCZOS, reducing_gap=3.0
        )

    transformed = _metadata_free_rgb(transformed)
    output = io.BytesIO()
    transformed.save(output, format="PNG", optimize=False, compress_level=9)
    encoded = output.getvalue()
    chunks = png_chunk_types(encoded)
    idat_indices = [index for index, value in enumerate(chunks) if value == "IDAT"]
    if (
        chunks[0] != "IHDR"
        or chunks.count("IHDR") != 1
        or chunks[-1] != "IEND"
        or chunks.count("IEND") != 1
        or not idat_indices
        or idat_indices != list(range(idat_indices[0], idat_indices[-1] + 1))
        or any(chunk not in PILOT3_CANONICAL_PNG_CHUNKS for chunk in chunks)
    ):
        raise Pilot3PreprocessingError(
            "Pilot-3 canonical PNG contains an ancillary metadata chunk"
        )
    with Image.open(io.BytesIO(encoded)) as verification:
        if (
            verification.format != "PNG"
            or verification.mode != "RGB"
            or verification.info
        ):
            raise Pilot3PreprocessingError(
                "Pilot-3 canonical PNG is not metadata-free RGB"
            )
        verification.load()
    return encoded, transformed.size
