"""The 31 prespecified color, spatial, and texture measurements; no learned evaluator."""

from __future__ import annotations

import hashlib
import io
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pywt
from PIL import Image, ImageCms, ImageOps
from scipy import ndimage, signal, stats
from skimage import color, feature

FAMILY_NAMES = {
    "color": ("lightness_median", "lightness_iqr", "chroma_median", "chroma_iqr",
              "chromatic_fraction", "hue_concentration", "hue_entropy", "deltae_01",
              "deltae_04", "deltae_16", "deltae_slope"),
    "spatial": ("spectral_slope", "spectral_residual", "spectral_anisotropy",
                "orientation_entropy", "horizontal_vertical_balance", "gradient_median",
                "gradient_iqr", "quadrant_jsd"),
    "texture": ("wavelet_energy_1", "wavelet_energy_2", "wavelet_energy_3",
                "wavelet_energy_4", "wavelet_slope", "wavelet_curvature", "lbp_entropy_8",
                "lbp_entropy_16", "lbp_entropy_32", "local_cv_01", "local_cv_04", "local_cv_16"),
}
NAMES = tuple(name for names in FAMILY_NAMES.values() for name in names)
FAMILIES = {"color": slice(0, 11), "spatial": slice(11, 19), "texture": slice(19, 31)}


@dataclass
class Normalized:
    rgb: np.ndarray
    metadata: dict


def half_up(value: float) -> int:
    return int(np.floor(value + 0.5))


def normalize(path: Path, short_side: int = 1024, crop_fraction: float = 0.0) -> Normalized:
    if short_side < 256 or not 0 <= crop_fraction <= 0.05:
        raise ValueError("invalid normalization contract")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as original:
            if original.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
                raise ValueError("unsupported image format")
            original.load()
            image = ImageOps.exif_transpose(original)
            if "A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255):
                raise ValueError("nonopaque alpha is not a painting area")
            if "transparency" in image.info:
                alpha = image.convert("RGBA").getchannel("A")
                if alpha.getextrema() != (255, 255):
                    raise ValueError("nonopaque palette transparency")
            width, height = image.size
            profile = image.info.get("icc_profile")
            if profile:
                try:
                    source = ImageCms.ImageCmsProfile(io.BytesIO(profile))
                    image = ImageCms.profileToProfile(
                        image, source, ImageCms.createProfile("sRGB"),
                        renderingIntent=ImageCms.Intent.PERCEPTUAL, outputMode="RGB",
                    )
                except (OSError, ValueError, ImageCms.PyCMSError) as exc:
                    raise ValueError("invalid or incompatible ICC profile") from exc
            else:
                if image.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                    raise ValueError("unprofiled non-RGB color space")
                image = image.convert("RGB")
            if crop_fraction:
                x, y = half_up(width * crop_fraction), half_up(height * crop_fraction)
                image = image.crop((x, y, width - x, height - y))
            if min(image.size) < short_side:
                raise ValueError("normalization would upsample")
            factor = short_side / min(image.size)
            target = tuple(half_up(v * factor) for v in image.size)
            image = image.resize(target, Image.Resampling.LANCZOS)
            rgb = np.asarray(image, dtype=np.float64) / 255.0
    return Normalized(rgb, dict(
        original_width=width, original_height=height,
        normalized_width=target[0], normalized_height=target[1], short_side=short_side,
        color_profile="embedded_to_srgb" if profile else "missing_assumed_srgb",
        crop_fraction=crop_fraction,
        normalized_sha256=hashlib.sha256(rgb.astype("<f8").tobytes()).hexdigest(),
    ))


def linearize(rgb: np.ndarray) -> np.ndarray:
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def iqr(values: np.ndarray) -> float:
    q = np.quantile(values, [0.25, 0.75])
    return float(q[1] - q[0])


def entropy(histogram: np.ndarray) -> float:
    total = histogram.sum()
    if total == 0:
        return 0.0
    p = histogram[histogram > 0] / total
    return float(-np.sum(p * np.log(p)) / np.log(len(histogram)))


def color_features(rgb: np.ndarray) -> np.ndarray:
    lab = color.rgb2lab(rgb, illuminant="D65", observer="2")
    lightness, a, b = np.moveaxis(lab, -1, 0)
    chroma = np.hypot(a, b)
    mask = chroma >= 5
    fraction = float(mask.mean())
    concentration, hue_entropy = 0.0, 0.0
    if fraction >= 0.01:
        angles = np.mod(np.arctan2(b[mask], a[mask]), 2 * np.pi)
        weights = chroma[mask]
        concentration = float(abs(np.sum(weights * np.exp(1j * angles))) / weights.sum())
        histogram, _ = np.histogram(angles, bins=24, range=(0, 2 * np.pi), weights=weights)
        hue_entropy = entropy(histogram)
    short_side = min(rgb.shape[:2])
    lags = [half_up(f * short_side) for f in (0.01, 0.04, 0.16)]
    distances = []
    for lag in lags:
        horizontal = color.deltaE_ciede2000(lab[:, :-lag], lab[:, lag:])
        vertical = color.deltaE_ciede2000(lab[:-lag], lab[lag:])
        distances.append(float(np.median(np.concatenate((horizontal.ravel(), vertical.ravel())))))
    slope = float(np.polyfit(np.log(lags), np.log(np.asarray(distances) + 1e-6), 1)[0])
    return np.array([np.median(lightness), iqr(lightness), np.median(chroma), iqr(chroma),
                     fraction, concentration, hue_entropy, *distances, slope])


def orientation_histogram(angle: np.ndarray, magnitude: np.ndarray) -> np.ndarray:
    return np.histogram(angle, bins=18, range=(0, np.pi), weights=magnitude)[0]


def spatial_features(luminance: np.ndarray) -> np.ndarray:
    h, w = luminance.shape
    short_side = min(h, w)
    window = signal.windows.tukey(h, 0.1)[:, None] * signal.windows.tukey(w, 0.1)[None, :]
    power = abs(np.fft.fft2((luminance - luminance.mean()) * window)) ** 2
    fy = np.fft.fftfreq(h)[:, None] * short_side
    fx = np.fft.fftfreq(w)[None, :] * short_side
    radius = np.hypot(fx, fy)
    edges = np.geomspace(4, 128, 33)
    bin_id = np.searchsorted(edges, radius, side="right") - 1
    bin_id[radius == 128] = 31
    band = (radius >= 4) & (radius <= 128)
    counts = np.bincount(bin_id[band], minlength=32)
    if np.any(counts == 0):
        raise ValueError("empty spectral bin")
    radial = np.bincount(bin_id[band], weights=power[band], minlength=32) / counts
    x, y = np.log(np.sqrt(edges[:-1] * edges[1:])), np.log(radial + 1e-12)
    slope = float(stats.theilslopes(y, x, method="joint").slope)
    intercept = np.median(y - slope * x)
    residual = float(np.sqrt(np.mean((y - slope * x - intercept) ** 2)))
    axial = np.mod(np.arctan2(np.broadcast_to(fy, (h, w)), np.broadcast_to(fx, (h, w))), np.pi)
    angle_power, _ = np.histogram(axial[band], bins=36, range=(0, np.pi), weights=power[band])
    centers = (np.arange(36) + 0.5) * np.pi / 36
    anisotropy = (float(abs(np.sum(angle_power * np.exp(2j * centers))) / angle_power.sum())
                  if angle_power.sum() else 0.0)
    kernel = np.array([[-3, 0, 3], [-10, 0, 10], [-3, 0, 3]], dtype=float) / 16
    gx = ndimage.correlate(luminance, kernel, mode="reflect")
    gy = ndimage.correlate(luminance, kernel.T, mode="reflect")
    magnitude = np.hypot(gx, gy)[1:-1, 1:-1]
    angle = np.mod(np.arctan2(gy, gx), np.pi)[1:-1, 1:-1]
    full = orientation_histogram(angle, magnitude)
    balance = (float(np.sum(full * np.cos(2 * (np.arange(18) + 0.5) * np.pi / 18)) / full.sum())
               if full.sum() else 0.0)
    p = (full + 1e-12) / (full + 1e-12).sum()
    hh, ww = angle.shape
    divergences = []
    for ys in (slice(None, hh // 2), slice(hh // 2, None)):
        for xs in (slice(None, ww // 2), slice(ww // 2, None)):
            q = orientation_histogram(angle[ys, xs], magnitude[ys, xs]) + 1e-12
            q /= q.sum()
            middle = (p + q) / 2
            divergences.append(0.5 * np.sum(p * np.log2(p / middle) + q * np.log2(q / middle)))
    return np.array([slope, residual, anisotropy, entropy(full), balance,
                     np.median(magnitude), iqr(magnitude), np.mean(divergences)])


def texture_features(luminance: np.ndarray) -> np.ndarray:
    h, w = luminance.shape
    padded = np.pad(luminance, ((0, -h % 16), (0, -w % 16)), mode="reflect")
    coefficients = pywt.swt2(padded, "db2", level=4)
    energies = []
    for _approximation, details in reversed(coefficients):
        energy = sum(d[:h, :w] ** 2 for d in details)
        energies.append(float(np.log(energy.mean() + 1e-12)))
    wavelet_slope = float(np.polyfit(np.arange(1, 5), energies, 1)[0])
    curvature = float(np.diff(energies, n=2).mean())
    integer = np.floor(np.clip(luminance, 0, 1) * 255 + 0.5).astype(np.uint8)
    lbp = []
    for points, radius in ((8, 1), (16, 2), (32, 4)):
        expanded = np.pad(integer, radius, mode="reflect")
        codes = feature.local_binary_pattern(expanded, points, radius, method="uniform")
        codes = codes[radius:-radius, radius:-radius].astype(int)
        lbp.append(entropy(np.bincount(codes.ravel(), minlength=points + 2)))
    variations = []
    for fraction in (0.01, 0.04, 0.16):
        side = half_up(fraction * min(h, w))
        side += side % 2 == 0
        mean = ndimage.uniform_filter(luminance, side, mode="reflect")
        second = ndimage.uniform_filter(luminance ** 2, side, mode="reflect")
        sd = np.sqrt(np.maximum(second - mean ** 2, 0))
        variations.append(float(np.median(sd / np.maximum(mean, 1e-6))))
    return np.array([*energies, wavelet_slope, curvature, *lbp, *variations])


def extract(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float64)
    if (rgb.ndim != 3 or rgb.shape[2] != 3 or min(rgb.shape[:2]) < 256
            or not np.isfinite(rgb).all() or np.any((rgb < 0) | (rgb > 1))):
        raise ValueError("expected finite RGB in [0,1] with short side at least 256")
    linear = linearize(rgb)
    luminance = linear @ np.array([0.2126, 0.7152, 0.0722])
    values = np.concatenate((color_features(rgb), spatial_features(luminance),
                             texture_features(luminance)))
    if values.shape != (31,) or not np.isfinite(values).all():
        raise ValueError("nonfinite or incomplete feature vector")
    return values
