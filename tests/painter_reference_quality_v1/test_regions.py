"""Image-processing oracles for the separately versioned region correction."""

import numpy as np
import pytest
from PIL import Image, ImageCms

from latent_art_bench.painter_feature_generation_v2.features import normalize
from latent_art_bench.painter_reference_quality_v1 import normalize_region, validate_box


@pytest.mark.parametrize("profile", [False, True])
def test_full_region_preserves_original_orientation_and_color_pipeline(tmp_path, profile):
    rng = np.random.default_rng(13)
    im = Image.fromarray(rng.integers(0, 256, size=(600, 800, 3), dtype=np.uint8))
    exif = Image.Exif()
    exif[274] = 6
    options = {"exif": exif}
    if profile:
        options["icc_profile"] = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    path = tmp_path / "source.jpg"
    im.save(path, **options)
    original = normalize(path, short_side=512)
    actual, metadata = normalize_region(path, [0, 0, 1, 1])
    np.testing.assert_array_equal(actual, original.rgb)
    assert metadata["normalized_sha256"] == original.metadata["normalized_sha256"]
    assert metadata["original_width"] == 600


def test_region_is_applied_before_resize_and_removes_external_pixels(tmp_path):
    rng = np.random.default_rng(19)
    painting = rng.integers(0, 256, size=(700, 900, 3), dtype=np.uint8)
    framed = np.zeros((700, 1000, 3), dtype=np.uint8)
    framed[:, 100:] = painting
    source, clean = tmp_path / "framed.png", tmp_path / "painting.png"
    Image.fromarray(framed).save(source)
    Image.fromarray(painting).save(clean)
    actual, metadata = normalize_region(source, [0.1, 0, 1, 1])
    np.testing.assert_array_equal(actual, normalize(clean, short_side=512).rgb)
    assert metadata["pixel_box"] == [100, 0, 1000, 700]
    assert metadata["removed_area_fraction"] == pytest.approx(0.1)


def test_correction_does_not_silently_upsample(tmp_path):
    source = tmp_path / "small.png"
    Image.new("RGB", (512, 512)).save(source)
    with pytest.raises(ValueError, match="upsample"):
        normalize_region(source, [0.1, 0, 1, 1])


@pytest.mark.parametrize("box", [[0, 0, 1], [-0.1, 0, 1, 1], [1, 0, 0, 1], [0, 0, np.nan, 1]])
def test_invalid_regions_are_rejected(box):
    with pytest.raises(ValueError):
        validate_box(box)
