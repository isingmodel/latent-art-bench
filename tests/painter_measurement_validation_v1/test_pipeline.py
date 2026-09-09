import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_revision_v1 import common
from latent_art_bench.painter_feature_generation_v2.features import Normalized
from latent_art_bench.painter_measurement_validation_v1 import pipeline as p


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def prospective(tmp_path, monkeypatch):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "Offline test")
    git(tmp_path, "config", "user.email", "offline@example.invalid")
    source = Path("source.txt")
    (tmp_path / source).write_text("fixed source\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "prospective source")
    monkeypatch.setattr(p, "source_paths", lambda root: [source])
    monkeypatch.setattr(p.common, "load", lambda root: {})
    monkeypatch.setattr(p.statistics, "verify_primary", lambda bundle: [])
    monkeypatch.setattr(p, "image_inventory", lambda root, bundle: [{"image_id": "metadata-only"}])
    return tmp_path


def test_prepare_is_metadata_only_and_run_rejects_uncommitted_freeze(prospective, monkeypatch):
    def forbidden(*args):
        raise AssertionError("raw pixels must not be opened")

    monkeypatch.setattr(p, "normalized_item", forbidden)
    result = p.prepare(prospective)
    assert result["status"] == "prepared_no_pixels_read"
    with pytest.raises(ValueError, match="commit exact"):
        p.run(prospective)
    directory, workspace, _ = p.locations(p.RUN_ID)
    assert not (prospective / workspace / "started.json").exists()
    freeze = read_json(prospective / directory / "freeze.json")
    assert freeze["config"]["total_vectors"] == 1706
    assert not freeze["config"]["new_collection_authorized"]


def test_prepare_rejects_uncommitted_source(prospective):
    (prospective / "source.txt").write_text("changed after source commit")
    with pytest.raises(ValueError, match="commit exact"):
        p.prepare(prospective)


def test_committed_freeze_detects_source_or_image_manifest_change(prospective):
    p.prepare(prospective)
    git(prospective, "add", ".")
    git(prospective, "commit", "-m", "freeze before pixels")
    assert p.verify(prospective)["config"] == p.config()
    (prospective / "source.txt").write_text("changed source")
    with pytest.raises(ValueError, match="bound input changed"):
        p.verify(prospective)


def test_environment_drift_is_rejected_before_measurement(prospective, monkeypatch):
    p.prepare(prospective)
    git(prospective, "add", ".")
    git(prospective, "commit", "-m", "freeze environment")
    observed = p.environment()
    assert set(observed) == {"python", "numpy", "pillow", "scipy", "scikit_image", "pywavelets"}
    monkeypatch.setattr(p, "environment", lambda: dict(observed, pillow="different"))
    with pytest.raises(ValueError, match="active extraction environment"):
        p.verify(prospective)


def test_failed_run_is_permanently_closed(prospective, monkeypatch):
    p.prepare(prospective)
    git(prospective, "add", ".")
    git(prospective, "commit", "-m", "frozen inventory")

    def failure(*args):
        raise ValueError("synthetic measurement failure")

    monkeypatch.setattr(p, "measure_item", failure)
    with pytest.raises(ValueError, match="synthetic measurement"):
        p.run(prospective)
    _, workspace, _ = p.locations(p.RUN_ID)
    assert read_json(prospective / workspace / "failure.json")["terminal"]
    with pytest.raises(FileExistsError):
        p.run(prospective)


def test_measurement_crops_after_one_normalization_and_reuses_baseline(tmp_path, monkeypatch):
    rgb = np.full((512, 640, 3), 128 / 255)
    calls = []

    def normalize(*args):
        calls.append("normalize")
        return Normalized(rgb, {"normalized_sha256": "fixed"})

    def extract(array):
        assert array.shape == (512, 512, 3)
        calls.append("extract")
        return np.full(31, array.mean())

    monkeypatch.setattr(p, "normalized_item", normalize)
    monkeypatch.setattr(p.features, "extract", extract)
    row = dict(image_id="work", painter_id="claude_monet", stage="reference",
               raw_sha256="raw", normalized_sha256="fixed")
    records = p.measure_item(tmp_path, Path("workspace"), row)
    assert calls.count("normalize") == 1 and calls.count("extract") == 10
    assert records[0]["values"] == records[1]["values"]
    assert all(r["window"]["retained_area_fraction"] == .8 for r in records)


def test_raw_hash_failure_prevents_normalization(tmp_path, monkeypatch):
    path = tmp_path / "synthetic.bin"
    path.write_bytes(b"not an image")
    item = dict(stage="reference", raw_sha256="wrong", source=dict(response_path=path.name))

    def forbidden(*args):
        raise AssertionError("hash gate must precede pixel normalization")

    monkeypatch.setattr(p.features, "normalize", forbidden)
    with pytest.raises(ValueError, match="raw bytes changed"):
        p.normalized_item(tmp_path, Path("workspace"), item)


def test_actual_metadata_inventory_never_needs_raw_bytes(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    bundle = common.load(root)

    def forbidden(*args):
        raise AssertionError("raw hashing is forbidden during metadata inventory")

    monkeypatch.setattr(p, "hash_file", forbidden)
    inventory = p.image_inventory(root, bundle)
    assert len(inventory) == 1076
    assert sum(i["stage"] == "reference" for i in inventory) == 70
    assert sum(i["stage"] == "generated" for i in inventory) == 1006
    assert len({i["image_id"] for i in inventory}) == 1076
    json.dumps(inventory, allow_nan=False)


def test_run_ids_and_incomplete_result_cannot_escape_contract():
    with pytest.raises(ValueError, match="identifier"):
        p.locations("../old-study")
    with pytest.raises(ValueError, match="complete1706"):
        p.compute([], {})
