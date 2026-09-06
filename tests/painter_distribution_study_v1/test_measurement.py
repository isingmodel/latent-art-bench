from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import measurement as m


def test_common_jpeg_changes_encoding_without_resizing_or_saturating():
    rng = np.random.default_rng(123)
    rgb = rng.uniform(0.05, 0.95, size=(32, 47, 3))
    decoded, sha = m.jpeg_sensitivity(rgb)
    assert decoded.shape == rgb.shape
    assert np.isfinite(decoded).all() and decoded.min() >= 0 and decoded.max() <= 1
    assert len(sha) == 64
    assert m.jpeg_sensitivity(rgb)[1] == sha
    assert not np.array_equal(rgb, decoded)


def test_pipeline_preserves_all_measurement_failures_without_upscaling(tmp_path):
    source = tmp_path / "small.png"
    Image.new("RGB", (300, 300), (30, 60, 70)).save(source)
    rows = m.measure_path(source, dict(image_id="test"), ("primary512", "jpeg90_512"))
    assert len(rows) == 2 and all(r["status"] == "failed" for r in rows)
    assert all("values" not in r for r in rows)


def test_development_failure_withholds_whole_sensitivity(monkeypatch):
    monkeypatch.setattr(m, "read_json", lambda path: dict(center=[0] * 31, scale=[1] * 31))
    result = m.build_scalers(Path("."), [])
    assert result["primary512"]["status"] == "available"
    assert result["resolution256"]["status"] == "unavailable"
    assert result["jpeg90_512"]["status"] == "unavailable"
