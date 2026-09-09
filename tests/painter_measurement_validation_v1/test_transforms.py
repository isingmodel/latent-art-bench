import numpy as np
import pytest
from skimage import color

from latent_art_bench.painter_measurement_validation_v1 import transforms as t


@pytest.fixture
def rgb():
    y, x = np.mgrid[:512, :512]
    return np.stack((x % 256, y % 256, (x * 7 + y * 3) % 256), axis=-1) / 255


def test_ten_fixed_conditions_all_finite_and_deterministic(rgb):
    assert len(t.CONDITIONS) == len(set(t.CONDITIONS)) == 10
    for name in t.CONDITIONS:
        result, metadata = t.condition(rgb, name)
        repeated, repeated_metadata = t.condition(rgb, name)
        assert result.shape == rgb.shape
        assert np.isfinite(result).all() and result.min() >= 0 and result.max() <= 1
        np.testing.assert_array_equal(result, repeated)
        assert metadata == repeated_metadata


def test_lossless_identity_is_exact_and_tiles_preserve_joint_pixels(rgb):
    png, _ = t.condition(rgb, "png")
    tiles, metadata = t.condition(rgb, "tiles4")
    np.testing.assert_array_equal(png, rgb)
    assert sorted(metadata["tile_order"]) == list(range(16))
    assert not np.array_equal(tiles, rgb)

    def packed(array):
        v = t.uint8(array).astype(np.uint32)
        return np.sort((v[:, :, 0] * 65536 + v[:, :, 1] * 256 + v[:, :, 2]).ravel())

    np.testing.assert_array_equal(packed(rgb), packed(tiles))


def test_chroma_has_signed_known_dose_and_preserves_lightness():
    rgb = np.broadcast_to(np.array([.3, .5, .7]), (512, 512, 3)).copy()
    original = color.rgb2lab(rgb)
    for factor in (.8, .6):
        changed, metadata = t.contract_chroma(rgb, factor)
        observed = color.rgb2lab(changed)
        np.testing.assert_allclose(observed[:, :, 0], original[:, :, 0], atol=1e-10)
        np.testing.assert_allclose(observed[:, :, 1:], factor * original[:, :, 1:], atol=1e-10)
        assert metadata["clipped_pixel_fraction"] == 0


def test_blur_dose_removes_known_high_frequency_signal():
    x = .5 + .4 * np.sin(np.arange(512) * 2 * np.pi / 8)
    rgb = np.broadcast_to(x[None, :, None], (512, 512, 3)).copy()
    first, _ = t.condition(rgb, "blur1")
    second, _ = t.condition(rgb, "blur2")
    assert np.var(second[:, 16:-16]) < np.var(first[:, 16:-16]) < np.var(rgb[:, 16:-16])


def test_square_window_crops_odd_excess_after_normalization():
    rgb = np.broadcast_to(np.arange(701)[None, :, None], (512, 701, 3)).copy()
    square, metadata = t.square_window(rgb)
    np.testing.assert_array_equal(square, rgb[:, 94:606])
    assert metadata == dict(top=0, left=94, width=512, height=512,
                            retained_area_fraction=512 / 701)
    with pytest.raises(ValueError, match="short-side512"):
        t.square_window(np.zeros((600, 701, 3)))


def test_invalid_condition_and_out_of_range_pixels_rejected(rgb):
    with pytest.raises(ValueError, match="invalid challenge"):
        t.condition(rgb, "adaptive_new_condition")
    with pytest.raises(ValueError, match="invalid challenge"):
        t.condition(rgb + 1, "baseline")
