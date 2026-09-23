"""Constructed collector/pixel/raw-vector artifacts; no feature extraction or fit."""

import base64
import copy
import io
import json
import shutil
from datetime import timedelta
from decimal import Decimal

import numpy as np
import pytest
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import measurement31 as m
from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_family_controls_v1.feature_census import (
    RECORD_FILES,
    TerminalCensus,
    load_terminal_census,
)


@pytest.fixture
def census(tmp_path):
    root = tmp_path / "collector"
    start = p.utc_datetime("2000-01-01T00:00:00Z")
    slots = p.assignments(start)
    pixel_buffer = io.BytesIO()
    Image.new("RGB", (1024, 1024), (20, 40, 60)).save(pixel_buffer, format="PNG")
    body = json.dumps({"usage": {"cost": "0.01"}, "data": [
        {"b64_json": base64.b64encode(pixel_buffer.getvalue()).decode()}
    ]}).encode()
    with Collector(root, slots, simulation=True, policy=CollectorPolicy(Decimal("350")),
                   free_bytes=lambda path: 100 * 1024**3) as collector:
        for index, slot in enumerate(slots[:4]):
            collector.execute_one(
                slot["id"], MockTransport([MockResponse(200, body)]),
                started_at=start + timedelta(seconds=5 * index),
                ended_at=start + timedelta(seconds=5 * index + 1),
            )
        collector.close_terminal(start + timedelta(seconds=20), "constructed raw31 fixture")
    hashes = {name: m.file_sha(root / name) for name in RECORD_FILES}
    return load_terminal_census(root, expected_hashes=hashes, allow_simulation=True)


def artifact_files(tmp_path, census):
    manifest = m.feature_manifest(census)
    manifest_path = tmp_path / "raw31_inputs.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    # Use only the retained scaler; no historical raw feature arrays are loaded.
    _, center, scale = m._historical_contract(m.ROOT)
    standardized = np.arange(len(manifest["rows"]) * 31, dtype=float).reshape(-1, 31) / 10
    raw = center + scale * standardized
    archive_path = tmp_path / "raw31.npz"
    ids = np.array([row["id"] for row in manifest["rows"]])
    names = np.array(m.NAMES)
    np.savez_compressed(archive_path, raw_features=raw, ids=ids, feature_names=names)
    return manifest_path, archive_path, raw, ids, names, standardized


def load(census, paths, *, root=m.ROOT, manifest_sha=None, raw_sha=None):
    manifest, raw = paths[:2]
    return m.load_feature_census(
        census, manifest, raw,
        expected_manifest_sha256=manifest_sha or m.file_sha(manifest),
        expected_raw_sha256=raw_sha or m.file_sha(raw), root=root,
    )


def test_bound_method_fixed_scaler_and_declared_execution_limit(census, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("the raw artifact loader must not extract or fit")
    from latent_art_bench.painter_feature_generation_v2 import features, statistics
    monkeypatch.setattr(features, "normalize", forbidden)
    monkeypatch.setattr(features, "extract", forbidden)
    monkeypatch.setattr(statistics, "fit_scaler", forbidden)
    paths = artifact_files(tmp_path, census)
    result = load(census, paths)
    assert result["generated"].shape == (6, 8, 12, 8, 31)
    assert result["observed"].sum() == 4
    assert np.isnan(result["generated"][~result["observed"]]).all()
    assert result["window_times"] == census.evidence["window_times"]
    assert result["simulation_only"] is True
    assert len(result["missing"]) == 4604
    for index, row in enumerate(census.evidence["images"]):
        np.testing.assert_allclose(result["generated"][m._cell(row)], paths[-1][index], atol=1e-12)
    provenance = result["provenance"]
    contract = provenance["measurement_contract"]
    assert contract["normalize"]["short_side"] == 512
    assert contract["normalize"]["crop_fraction"] == 0.0
    assert contract["feature_names"] == list(m.NAMES)
    assert contract["standardization"]["new_fitting"] is False
    assert contract["standardization"]["unit_normalization"] is False
    assert provenance["original_pixels_rechecked"] is True
    assert provenance["extraction_execution_authenticated"] is False
    assert provenance["extraction_execution_receipt_or_replay_required"] is True


@pytest.mark.parametrize("tamper", [
    "ids", "names", "row_count", "dimension", "nonfinite", "integer", "extra_key",
    "id_object", "partial_missing", "crop", "timings", "manifest_hash", "raw_hash", "image",
])
def test_bound_raw_artifact_mutations_are_rejected(census, tmp_path, tamper):
    paths = artifact_files(tmp_path, census)
    manifest_path, archive, raw, ids, names, _ = paths
    fields = dict(raw_features=raw, ids=ids, feature_names=names)
    kwargs = {}
    if tamper == "ids":
        fields["ids"] = ids[::-1]
    elif tamper == "names":
        fields["feature_names"] = names[::-1]
    elif tamper == "row_count":
        fields["raw_features"] = raw[:-1]
    elif tamper == "dimension":
        fields["raw_features"] = raw[:, :30]
    elif tamper in ("nonfinite", "partial_missing"):
        fields["raw_features"][0, 0] = np.inf if tamper == "nonfinite" else np.nan
    elif tamper == "integer":
        fields["raw_features"] = raw.astype(np.int64)
    elif tamper == "extra_key":
        fields["unknown"] = np.zeros(1)
    elif tamper == "id_object":
        fields["ids"] = ids.astype(object)
    elif tamper in ("crop", "timings"):
        manifest = json.loads(manifest_path.read_text())
        if tamper == "crop":
            manifest["measurement"]["normalize"]["crop_fraction"] = 0.01
        else:
            manifest["window_times"][0]["assigned_end"] = "2000-01-01T03:00:00+00:00"
        manifest_path.write_text(json.dumps(manifest))
    elif tamper == "manifest_hash":
        kwargs["manifest_sha"] = "0" * 64
    elif tamper == "raw_hash":
        kwargs["raw_sha"] = "0" * 64
    else:
        row = census.evidence["images"][0]
        (census.run_dir / row["path"]).write_bytes(b"changed pixels")
    np.savez_compressed(archive, **fields)
    with pytest.raises(ValueError):
        load(census, paths, **kwargs)


def test_utf8_byte_ids_names_and_no_implicit_raw_standardization_confusion(census, tmp_path):
    paths = artifact_files(tmp_path, census)
    _, archive, raw, ids, names, expected = paths
    np.savez_compressed(archive, raw_features=raw, ids=ids.astype("S"),
                        feature_names=names.astype("S"))
    result = load(census, paths)
    first = census.evidence["images"][0]
    np.testing.assert_allclose(result["generated"][m._cell(first)], expected[0], atol=1e-12)
    assert not np.allclose(result["generated"][m._cell(first)], raw[0])


@pytest.mark.parametrize("path", [*m.HISTORICAL_BINDINGS, *m.METHOD_SOURCES])
def test_historical_method_scaler_or_source_mutation_rejected(census, tmp_path, path):
    paths = artifact_files(tmp_path, census)
    alternate = tmp_path / "retained"
    for relative in (*m.HISTORICAL_BINDINGS, *m.METHOD_SOURCES):
        output = alternate / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(m.ROOT / relative, output)
    changed = alternate / path
    changed.write_bytes(changed.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="externally bound"):
        load(census, paths, root=alternate)


@pytest.mark.parametrize("tamper", ["simulation", "cell", "missing", "times"])
def test_forged_detached_census_cannot_bypass_terminal_revalidation(census, tamper):
    evidence = census.evidence
    if tamper == "simulation":
        evidence["simulation_only"] = False
    elif tamper == "cell":
        evidence["images"][0]["scene"] = -1
    elif tamper == "missing":
        evidence["missing"].pop()
    else:
        evidence["window_times"][0]["attempts"] = []
    forged = TerminalCensus(census.run_dir, json.dumps(evidence))
    with pytest.raises(ValueError):
        m.feature_manifest(forged)


@pytest.mark.parametrize("key,value", [
    ("center", [0] * 30), ("scale", [0] * 31), ("scale", [-1] * 31),
    ("scale", [float("inf")] * 31), ("center", [float("nan")] * 31),
    ("center", [True] * 31), ("scale", ["1"] * 31),
])
def test_numeric_scaler_contract_is_explicit(key, value):
    scaler = dict(center=[0] * 31, scale=[1] * 31)
    scaler[key] = value
    with pytest.raises(ValueError):
        m._scaler_arrays(scaler)


@pytest.mark.parametrize("key,value", [("session", -1), ("scene", True),
                                      ("scene_id", "wrong"), ("view", "crop")])
def test_cell_mapping_checks_types_ranges_and_full_frame_identity(census, key, value):
    row = copy.deepcopy(census.evidence["images"][0])
    row[key] = value
    with pytest.raises(ValueError):
        m._cell(row)
