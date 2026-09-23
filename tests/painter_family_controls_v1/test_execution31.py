"""Real frozen feature extraction of synthetic pixels; no new service data."""

import base64
import copy
import io
import json
from datetime import timedelta
from decimal import Decimal

import numpy as np
import pytest
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import execution31 as e
from latent_art_bench.painter_family_controls_v1 import feature_census as fc
from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_feature_generation_v2 import features


def make_census(path, count=1):
    start = p.utc_datetime("2000-01-01T00:00:00Z")
    slots = p.assignments(start)
    y, x = np.indices((1024, 1024))
    array = np.stack((x % 256, y % 256, (x // 16 + y // 16) % 2 * 255), axis=-1)
    pixels = io.BytesIO()
    Image.fromarray(array.astype(np.uint8)).save(pixels, format="PNG")
    body = json.dumps({"usage": {"cost": "0.01"}, "data": [
        {"b64_json": base64.b64encode(pixels.getvalue()).decode()}
    ]}).encode()
    with Collector(path, slots, simulation=True, policy=CollectorPolicy(Decimal("350")),
                   free_bytes=lambda _: 100 * 1024**3) as collector:
        for i, slot in enumerate(slots[:count]):
            collector.execute_one(
                slot["id"], MockTransport([MockResponse(200, body)]),
                started_at=start + timedelta(seconds=i * 5),
                ended_at=start + timedelta(seconds=i * 5 + 1),
            )
        if count == 0:
            collector.execute_one(
                slots[0]["id"], MockTransport([MockResponse(400, body)]),
                started_at=start, ended_at=start + timedelta(seconds=1),
            )
        collector.close_terminal(start + timedelta(seconds=max(count, 1) * 5),
                                 "synthetic extraction")
    return fc.load_terminal_census(
        path, expected_hashes={name: e.file_sha(path / name) for name in fc.RECORD_FILES},
        allow_simulation=True,
    )


@pytest.fixture
def census(tmp_path):
    return make_census(tmp_path / "collector")


@pytest.fixture
def executed(census, tmp_path):
    output = tmp_path / "extracted"
    digest = e.execute(census, output, allow_simulation=True)
    return census, output, digest


def verify(executed):
    census, output, digest = executed
    return e.replay(census, output, expected_receipt_sha256=digest, allow_simulation=True)


def change_receipt(executed, change):
    census, output, _ = executed
    path = output / "execution.json"
    receipt = json.loads(path.read_text())
    change(receipt)
    path.write_bytes(e._json_bytes(receipt))
    return census, output, e.file_sha(path)


def test_actual_frozen_extraction_exact_replay_and_fixed_scaler(executed):
    census, output, _ = executed
    result = verify(executed)
    assert result["raw31_extraction_reproduced"] is True
    assert result["learned_extraction_reproduced"] is False
    assert result["rows_recomputed"] == 1
    assert result["simulation_only"] is True
    row = census.evidence["images"][0]
    normalized = features.normalize(census.run_dir / row["path"], short_side=512, crop_fraction=0.0)
    expected = features.extract(normalized.rgb)
    with np.load(output / "raw31.npz", allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["raw_features"][0], expected)
        assert archive["raw_features"].dtype == np.dtype("<f8")
        assert archive["feature_names"].tolist() == list(features.NAMES)
    receipt = json.loads((output / "execution.json").read_text())
    assert receipt["rows"][0]["normalization"] == normalized.metadata
    assert receipt["row_count"] + len(census.evidence["missing"]) == 4608
    assert receipt["runtime"]["executable_sha256"]


def test_disk_verified_source_ignores_monkeypatched_import(census, tmp_path, monkeypatch):
    def fake(*args, **kwargs):
        raise AssertionError("ordinary imported method must not be used")
    monkeypatch.setattr(features, "normalize", fake)
    monkeypatch.setattr(features, "extract", fake)
    output = tmp_path / "safe"
    digest = e.execute(census, output, allow_simulation=True)
    assert verify((census, output, digest))["raw31_extraction_reproduced"] is True


def test_simulation_opt_in_and_create_once(executed, tmp_path):
    census, output, digest = executed
    with pytest.raises(ValueError, match="simulation"):
        e.execute(census, tmp_path / "not-created")
    assert not (tmp_path / "not-created").exists()
    with pytest.raises(ValueError, match="simulation"):
        e.replay(census, output, expected_receipt_sha256=digest)
    with pytest.raises(FileExistsError):
        e.execute(census, output, allow_simulation=True)
    with pytest.raises(ValueError, match="outside"):
        e.execute(census, census.run_dir / "extras", allow_simulation=True)
    assert e.file_sha(output / "execution.json") == digest


@pytest.mark.parametrize("tamper", ["raw", "float32", "normalization", "runtime", "simulation",
                                  "membership", "method", "times", "extra_field"])
def test_self_consistent_forged_receipt_does_not_establish_replay(executed, tamper):
    _, output, _ = executed

    def change(receipt):
        if tamper in ("raw", "float32"):
            archive_path = output / "raw31.npz"
            with np.load(archive_path, allow_pickle=False) as archive:
                fields = {name: archive[name] for name in archive.files}
            if tamper == "raw":
                fields["raw_features"][0, 0] += 1
            else:
                fields["raw_features"] = fields["raw_features"].astype(np.float32)
            np.savez_compressed(archive_path, **fields)
            receipt["raw_features_sha256"] = e.file_sha(archive_path)
            receipt["rows"][0]["raw_vector_sha256"] = fc._digest(
                fields["raw_features"][0].astype("<f8").tobytes())
        elif tamper == "normalization":
            receipt["rows"][0]["normalization"]["normalized_sha256"] = "0" * 64
        elif tamper == "runtime":
            receipt["runtime"]["packages"]["numpy"] = "0.0"
        elif tamper == "simulation":
            receipt["simulation_only"] = False
        elif tamper == "membership":
            receipt["rows"][0]["id"] = "invented-row"
        elif tamper == "method":
            receipt["method_contract_sha256"] = "0" * 64
        elif tamper == "times":
            receipt["finished_utc"] = "1999-01-01T00:00:00Z"
        else:
            receipt["assert_execution_true"] = True
    changed = change_receipt(executed, change)
    with pytest.raises(ValueError):
        verify(changed)


@pytest.mark.parametrize("tamper", ["crop", "names", "row_id"])
def test_altered_manifest_or_axes_with_updated_hashes_rejected(executed, tamper):
    _, output, _ = executed

    def change(receipt):
        if tamper == "crop":
            path = output / "inputs.json"
            manifest = json.loads(path.read_text())
            manifest["measurement"]["normalize"]["crop_fraction"] = 0.01
            path.write_bytes(e._json_bytes(manifest))
            receipt["manifest_sha256"] = e.file_sha(path)
        else:
            path = output / "raw31.npz"
            with np.load(path, allow_pickle=False) as archive:
                fields = {name: archive[name] for name in archive.files}
            if tamper == "names":
                fields["feature_names"] = fields["feature_names"][::-1]
            else:
                fields["ids"][0] = "foreign"
            np.savez_compressed(path, **fields)
            receipt["raw_features_sha256"] = e.file_sha(path)
    with pytest.raises(ValueError):
        verify(change_receipt(executed, change))


def test_pixels_changed_after_execution_rejected(executed):
    census, _, _ = executed
    path = census.run_dir / census.evidence["images"][0]["path"]
    path.write_bytes(b"replaced pixels")
    with pytest.raises(ValueError):
        verify(executed)


def test_extractor_failure_has_no_success_receipt(census, tmp_path, monkeypatch):
    original = copy.deepcopy(census.evidence)
    def fail(*args):
        raise ValueError("constructed extraction failure")
    monkeypatch.setattr(e, "_compute", fail)
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="constructed extraction failure"):
        e.execute(census, output, allow_simulation=True)
    assert not (output / "execution.json").exists()
    assert fc.revalidate_census(census).evidence == original


def test_empty_census_cannot_claim_execution(tmp_path):
    census = make_census(tmp_path / "empty", count=0)
    output = tmp_path / "empty-extraction"
    with pytest.raises(ValueError, match="empty census"):
        e.execute(census, output, allow_simulation=True)
    assert not (output / "execution.json").exists()


def test_alternate_root_cannot_bind_unused_helper_files(tmp_path):
    with pytest.raises(ValueError, match="installed project root"):
        e._bindings(tmp_path)
