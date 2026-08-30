from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
from PIL import Image


def synthetic_images(size: int = 64, seed: int = 1729) -> Dict[str, Image.Image]:
    if size < 2:
        raise ValueError("size must be at least 2")
    solid = np.full((size, size, 3), (64, 128, 192), dtype=np.uint8)

    ramp = np.linspace(0, 255, size, dtype=np.uint8)
    x_ramp, y_ramp = np.meshgrid(ramp, ramp)
    gradient = np.stack(
        (y_ramp, x_ramp, np.full((size, size), 128, dtype=np.uint8)), axis=-1
    )

    stripes = np.zeros((size, size, 3), dtype=np.uint8)
    stripes[:, ::2] = (255, 255, 255)

    checker = ((np.indices((size, size)).sum(axis=0) % 2) * 255).astype(np.uint8)
    checkerboard = np.repeat(checker[:, :, None], 3, axis=2)

    rng = np.random.default_rng(seed)
    noise = rng.integers(0, 256, size=(size, size, 3), dtype=np.uint8)

    return {
        "solid": Image.fromarray(solid),
        "gradient": Image.fromarray(gradient),
        "stripes": Image.fromarray(stripes),
        "checkerboard": Image.fromarray(checkerboard),
        "noise": Image.fromarray(noise),
    }


def write_synthetic_images(output_dir: Path, size: int = 64, seed: int = 1729) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[str, Path] = {}
    for name, image in synthetic_images(size=size, seed=seed).items():
        path = output_dir / f"{name}.png"
        image.save(path, format="PNG", optimize=False, compress_level=9)
        paths[name] = path
    return paths
