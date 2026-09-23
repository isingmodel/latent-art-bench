"""Pixel semantics and validation-case membership; never load neural weights."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageCms

from latent_art_bench.painter_learned_audit_v1 import FULL, digest, load_rgb

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check_learned_extraction.py"
SPEC = importlib.util.spec_from_file_location("learned_validation_helper", SCRIPT)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def test_orientation_is_applied_before_normalized_region_coordinates(tmp_path):
    values = np.arange(45, dtype=np.uint8).reshape(3, 5, 3)
    image = Image.fromarray(values)
    exif = Image.Exif()
    exif[274] = 6  # Rotate clockwise: the oriented image is 3 wide by 5 high.
    path = tmp_path / "oriented.png"
    image.save(path, exif=exif)
    expected = np.rot90(values, k=-1)
    np.testing.assert_array_equal(np.asarray(load_rgb(path, FULL)), expected)
    # Half of odd width 3 uses nearest pixel boundary 2, after orientation.
    np.testing.assert_array_equal(np.asarray(load_rgb(path, [0, 0, 0.5, 1])), expected[:, :2])
    assert helper.oriented_dimensions(path) == (3, 5)


def test_embedded_lab_profile_is_converted_to_rgb_before_measurement(tmp_path):
    image = Image.new("LAB", (2, 1))
    image.putdata([(0, 128, 128), (255, 128, 128)])
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("LAB")).tobytes()
    path = tmp_path / "profiled.tiff"
    image.save(path, icc_profile=profile)
    converted = load_rgb(path, FULL)
    assert converted.mode == "RGB"
    np.testing.assert_allclose(np.asarray(converted)[0], [[0, 0, 0], [255, 255, 255]], atol=1)


def test_transparency_unprofiled_cmyk_and_invalid_profile_fail_closed(tmp_path):
    transparent = tmp_path / "transparent.png"
    Image.new("RGBA", (3, 2), (10, 20, 30, 127)).save(transparent)
    with pytest.raises(ValueError, match="nonopaque"):
        load_rgb(transparent, FULL)
    cmyk = tmp_path / "cmyk.tiff"
    Image.new("CMYK", (3, 2)).save(cmyk)
    with pytest.raises(ValueError, match="unprofiled"):
        load_rgb(cmyk, FULL)
    invalid = tmp_path / "invalid.png"
    Image.new("RGB", (3, 2)).save(invalid, icc_profile=b"invalid ICC bytes")
    with pytest.raises((OSError, ImageCms.PyCMSError)):
        load_rgb(invalid, FULL)


def make_rows(tmp_path):
    rows = []
    for name, role, size in [("generated", "generated", (4, 4)),
                             ("reference", "reference", (6, 6)),
                             ("odd", "reference", (9, 5))]:
        path = tmp_path / (name + ".png")
        Image.new("RGB", size, (20, 40, 60)).save(path)
        rows.append(dict(id=name, role=role, view="original", box=FULL,
                         path=path.name, sha256=digest(path), painter="monet"))
    rows.append(dict(rows[1], view="audited_region", box=[0.1, 0, 0.9, 1]))
    return rows


def test_fixed_cases_are_distinct_and_cover_originals_rounding_and_region(tmp_path):
    rows = make_rows(tmp_path)
    helper.validate_rows(rows, require_cohort=False)
    cases = helper.select_cases(rows, root=tmp_path)
    assert [c["index"] for c in cases] == [0, 1, 2, 3]
    assert [c["case"] for c in cases] == [
        "original_generated", "original_reference", "odd_aspect_reference", "audited_region"
    ]
    assert helper.odd_aspect_candidate((9, 5))
    assert not helper.odd_aspect_candidate((7, 5))
    assert not helper.odd_aspect_candidate((5, 3))
    assert not helper.odd_aspect_candidate((5, 5))
    with pytest.raises(ValueError, match="complete original cohort"):
        helper.validate_rows(rows)


def test_region_membership_and_pixel_identity_are_verified(tmp_path):
    rows = make_rows(tmp_path)
    with pytest.raises(ValueError, match="duplicate"):
        helper.validate_rows(rows + [rows[0]], require_cohort=False)
    altered = [dict(row) for row in rows]
    altered[-1]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="match its original"):
        helper.validate_rows(altered, require_cohort=False)
    altered = [dict(row) for row in rows]
    altered[-1]["box"] = [0.8, 0, 0.1, 1]
    with pytest.raises(ValueError, match="crop box"):
        helper.validate_rows(altered, require_cohort=False)
    Image.new("RGB", (4, 4), (90, 90, 90)).save(tmp_path / rows[0]["path"])
    with pytest.raises(ValueError, match="source hash differs"):
        helper.select_cases(rows, root=tmp_path)
