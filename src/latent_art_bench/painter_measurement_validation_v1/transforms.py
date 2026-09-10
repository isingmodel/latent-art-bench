"""Ten fixed square-window conditions; no learned evaluator or adaptive parameters."""

from __future__ import annotations

import hashlib
import io

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from skimage import color

from latent_art_bench.painter_feature_generation_v2 import features

CONDITIONS = (
    "baseline", "png", "jpeg95", "jpeg75", "resample384", "chroma80", "chroma60",
    "blur1", "blur2", "tiles4",
)
TILE_SEED = 2026091001


def square_window(rgb):
    """Crop AFTER the unchanged short-side512 normalization; do not resize again."""
    rgb = np.asarray(rgb, dtype=float)
    h, w, channels = rgb.shape
    if min(h, w) != 512 or channels != 3:
        raise ValueError("expected the aspect-preserving short-side512 normalized image")
    top, left = (h - 512) // 2, (w - 512) // 2
    return rgb[top:top + 512, left:left + 512].copy(), dict(
        top=top, left=left, width=512, height=512, retained_area_fraction=512**2 / (h * w),
    )


def uint8(rgb):
    return np.floor(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)


def encode_linear(linear):
    result = 12.92 * linear
    mask = linear > 0.0031308
    result[mask] = 1.055 * linear[mask] ** (1 / 2.4) - 0.055
    return result


def contract_chroma(rgb, factor):
    """D65 Lab contraction with an explicit, recorded RGB gamut clip."""
    lab = color.rgb2lab(rgb, illuminant="D65", observer="2")
    lab[:, :, 1:] *= factor
    fy = (lab[:, :, 0] + 16) / 116
    fxyz = np.stack((fy + lab[:, :, 1] / 500, fy, fy - lab[:, :, 2] / 200), axis=-1)
    delta = 6 / 29
    xyz = np.where(fxyz > delta, fxyz**3, 3 * delta**2 * (fxyz - 4 / 29))
    xyz *= np.array([0.95047, 1.0, 1.08883])
    # Same sRGB/D65 matrix as the frozen skimage conversion, inverted without clipping.
    rgb_to_xyz = np.array([[.412453, .357580, .180423], [.212671, .715160, .072169],
                           [.019334, .119193, .950227]])
    raw = encode_linear(xyz @ np.linalg.inv(rgb_to_xyz).T)
    clipped = (raw < 0) | (raw > 1)
    return np.clip(raw, 0, 1), dict(
        chroma_factor=factor, clipped_channel_fraction=float(clipped.mean()),
        clipped_pixel_fraction=float(clipped.any(axis=2).mean()),
    )


def condition(rgb, name):
    rgb = np.asarray(rgb, dtype=float)
    if rgb.shape != (512, 512, 3) or not np.isfinite(rgb).all():
        raise ValueError("challenge baseline must be finite512x512 RGB")
    if np.any((rgb < 0) | (rgb > 1)) or name not in CONDITIONS:
        raise ValueError("invalid challenge input or condition")
    metadata = {}
    if name == "baseline":
        result = rgb.copy()
    elif name in ("png", "jpeg95", "jpeg75"):
        buffer = io.BytesIO()
        options = {} if name == "png" else dict(
            quality=int(name[4:]), subsampling=0, optimize=False, progressive=False,
        )
        Image.fromarray(uint8(rgb)).save(
            buffer, format="PNG" if name == "png" else "JPEG", **options,
        )
        raw = buffer.getvalue()
        metadata["encoded_sha256"] = hashlib.sha256(raw).hexdigest()
        with Image.open(io.BytesIO(raw)) as image:
            result = np.asarray(image.convert("RGB"), dtype=float) / 255
    elif name == "resample384":
        image = Image.fromarray(uint8(rgb))
        image = image.resize((384, 384), Image.Resampling.LANCZOS)
        image = image.resize((512, 512), Image.Resampling.LANCZOS)
        result = np.asarray(image, dtype=float) / 255
    elif name.startswith("chroma"):
        result, metadata = contract_chroma(rgb, int(name[6:]) / 100)
    elif name.startswith("blur"):
        sigma = int(name[4:])
        linear = gaussian_filter(features.linearize(rgb), sigma=(sigma, sigma, 0),
                                 mode="reflect", truncate=4.0)
        result = np.clip(encode_linear(linear), 0, 1)
    else:
        order = np.random.default_rng(TILE_SEED).permutation(16)
        tiles = rgb.reshape(4, 128, 4, 128, 3).transpose(0, 2, 1, 3, 4).reshape(16, 128, 128, 3)
        result = tiles[order].reshape(4, 4, 128, 128, 3).transpose(0, 2, 1, 3, 4)
        result = result.reshape(512, 512, 3).copy()
        metadata["tile_order"] = order.tolist()
    metadata["array_sha256"] = hashlib.sha256(result.astype("<f8").tobytes()).hexdigest()
    return result, metadata
