import io

import numpy as np
from PIL import Image, ImageCms

from latent_art_bench.preprocessing.pipeline import preprocess_image_bytes


def _decoded(encoded: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(encoded))
    image.load()
    return image


def test_preprocessing_is_byte_deterministic_and_preserves_aspect(pilot_config) -> None:
    source = Image.fromarray(np.arange(80 * 40 * 3, dtype=np.uint8).reshape((40, 80, 3)))
    first, first_size = preprocess_image_bytes(source, pilot_config.preprocessing)
    second, second_size = preprocess_image_bytes(source, pilot_config.preprocessing)
    assert first == second
    assert first_size == second_size == (80, 40)


def test_preprocessing_downsamples_without_upsampling(pilot_config) -> None:
    source = Image.new("RGB", (1024, 256), (10, 20, 30))
    encoded, size = preprocess_image_bytes(source, pilot_config.preprocessing)
    assert size == (512, 128)
    assert _decoded(encoded).size == (512, 128)


def test_alpha_is_composited_on_frozen_background(pilot_config) -> None:
    source = Image.new("RGBA", (2, 1), (255, 0, 0, 0))
    source.putpixel((1, 0), (255, 0, 0, 255))
    encoded, _ = preprocess_image_bytes(source, pilot_config.preprocessing)
    output = _decoded(encoded)
    assert output.mode == "RGB"
    assert output.getpixel((0, 0)) == (255, 255, 255)
    assert output.getpixel((1, 0)) == (255, 0, 0)


def test_embedded_srgb_profile_and_alpha_are_handled_together(pilot_config) -> None:
    source = Image.new("RGBA", (2, 1), (20, 40, 60, 128))
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    source.info["icc_profile"] = profile.tobytes()
    encoded, size = preprocess_image_bytes(source, pilot_config.preprocessing)
    output = _decoded(encoded)
    assert size == (2, 1)
    assert output.mode == "RGB"
    assert output.getpixel((0, 0)) == (137, 147, 157)
