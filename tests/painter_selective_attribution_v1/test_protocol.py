"""Synthetic membership, immutable provenance and explicit execution boundary."""

import copy
import io
import json

import numpy as np
import pytest

from latent_art_bench import painter_selective_attribution_v1 as study


def fixture_rows():
    rows, values = [], []
    for scene in range(2):
        for repeat in range(2):
            for a, arm in enumerate(study.ARMS):
                rows.append(dict(id=f"g-{scene}-{repeat}-{arm}", view="original",
                                 role="generated", model="synthetic", scene=scene,
                                 repeat=repeat, arm=arm))
                values.append(np.eye(4)[a % 4])
    for role, n in (("reference", 2), ("development", 1)):
        for a, painter in enumerate(study.ARTISTS):
            for i in range(n):
                rows.append(dict(id=f"{role}-{a}-{i}", view="original", role=role,
                                 painter=painter, path=f"pixels/{role}-{a}-{i}.png",
                                 sha256="a" * 64, box=[0, 0, 1, 1]))
                values.append(np.eye(4)[a])
    for role, a in (("reference", 0), ("development", 1)):
        original = next(r for r in rows if r["id"] == f"{role}-{a}-0")
        rows.append(dict(original, view="audited_region", box=[.1, .1, .9, .9]))
        values.append(np.eye(4)[(a + 1) % 4])
    return rows, np.array(values)


def assemble(rows, values, regions=False):
    return study.assemble_rows(
        rows, values, use_regions=regions, model_names=("synthetic",), scenes=2,
        expected_counts={"reference": (2,) * 4, "development": (1,) * 4},
        expected_crops={"reference": (1, 0, 0, 0), "development": (0, 1, 0, 0)})


def test_all_generated_arms_retained_and_exact_existing_region_replacements():
    rows, values = fixture_rows()
    original, audited = assemble(rows, values), assemble(rows, values, True)
    assert original["generated"].shape == (1, 2, 2, 6, 4)
    assert original["generated_ids"].shape == (1, 2, 2, 6)
    np.testing.assert_array_equal(original["generated"], audited["generated"])
    np.testing.assert_array_equal(original["generated_ids"], audited["generated_ids"])
    np.testing.assert_array_equal(original["panels"]["reference"][0][0], np.eye(4)[0])
    np.testing.assert_array_equal(audited["panels"]["reference"][0][0], np.eye(4)[1])
    np.testing.assert_array_equal(audited["panels"]["reference"][0][1], np.eye(4)[0])
    np.testing.assert_array_equal(audited["panels"]["development"][1][0], np.eye(4)[2])
    assert audited["memberships"]["reference"][0][0]["selected_view"] == "audited_region"
    assert audited["memberships"]["reference"][0][1]["selected_view"] == "original"
    assert len(set(original["generated_ids"].ravel())) == 24


def test_duplicate_missing_generated_and_region_rows_fail_closed():
    rows, values = fixture_rows()
    with pytest.raises(ValueError, match="duplicate image/view"):
        assemble(rows + [rows[0]], np.vstack([values, values[0]]))
    with pytest.raises(ValueError, match="incomplete generated"):
        assemble(rows[1:], values[1:])
    with pytest.raises(ValueError, match="duplicate generated request"):
        assemble(rows + [dict(rows[0], id="other-id")], np.vstack([values, values[0]]))
    with pytest.raises(ValueError, match="source/crop census"):
        assemble(rows[:-1], values[:-1])
    with pytest.raises(ValueError, match="match manifest"):
        assemble(rows, values[:-1])


@pytest.mark.parametrize("field,value", [
    ("role", "development"), ("painter", study.ARTISTS[3]),
    ("path", "changed.png"), ("sha256", "b" * 64),
])
def test_crop_must_match_original_identity(field, value):
    rows, values = fixture_rows()
    rows[-2][field] = value
    with pytest.raises(ValueError, match="identity differs"):
        assemble(rows, values, True)


@pytest.mark.parametrize("field,value", [("scene", True), ("repeat", 0.),
                                         ("arm", "unknown"), ("model", "unknown")])
def test_generated_integer_identity_and_known_arms_strict(field, value):
    rows, values = fixture_rows()
    rows[0][field] = value
    with pytest.raises(ValueError, match="invalid generated request"):
        assemble(rows, values)


def test_invalid_box_generated_crop_or_orphan_crop_rejected():
    rows, values = fixture_rows()
    rows[-1]["box"] = [0, 0, 1, 1]
    with pytest.raises(ValueError, match="region box"):
        assemble(rows, values)
    rows, values = fixture_rows()
    rows[-1] = dict(rows[0], view="audited_region")
    with pytest.raises(ValueError, match="generated crop"):
        assemble(rows, values)
    rows, values = fixture_rows()
    index = next(i for i, r in enumerate(rows) if r["id"] == "reference-0-0")
    with pytest.raises(ValueError, match="requires original"):
        assemble(rows[:index] + rows[index+1:], np.delete(values, index, axis=0))


def synthetic_freeze(tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    source.write_text("fixed synthetic source\n")
    own = tmp_path / "implementation.py"
    own.write_text("# synthetic implementation\n")
    monkeypatch.setattr(study, "retained_bindings", lambda root: {
        "source.txt": study.file_sha(source)})
    monkeypatch.setattr(study, "own_paths", lambda root: ["implementation.py"])
    path = tmp_path / "new-inputs.json"
    digest = study.freeze(path, root=tmp_path)
    return path, digest, source, own


def test_freeze_hash_only_create_once_external_digest_and_tamper_detection(tmp_path, monkeypatch):
    monkeypatch.setattr(study.np, "load", lambda *a, **k: pytest.fail("freeze loaded vectors"))
    monkeypatch.setattr(study, "evaluate_model", lambda *a, **k: pytest.fail("freeze evaluated"))
    path, digest, source, own = synthetic_freeze(tmp_path, monkeypatch)
    record = study.verify_freeze(path, expected_sha256=digest, root=tmp_path)
    assert record["new_outcomes_computed"] is False
    assert record["specification"]["primary"] == "csd/original/primary"
    assert len(record["specification"]["encoders"]) * len(
        record["specification"]["views"]) * len(record["specification"]["targets"]) == 8
    with pytest.raises(FileExistsError):
        study.freeze(path, root=tmp_path)
    with pytest.raises(ValueError, match="external expected"):
        study.verify_freeze(path, expected_sha256="0" * 64, root=tmp_path)
    own.write_text("changed")
    with pytest.raises(ValueError, match="binding membership or bytes"):
        study.verify_freeze(path, expected_sha256=digest, root=tmp_path)
    own.write_text("# synthetic implementation\n")
    source.write_text("changed")
    with pytest.raises(ValueError, match="binding membership or bytes"):
        study.verify_freeze(path, expected_sha256=digest, root=tmp_path)


def test_self_consistent_freeze_specification_tamper_is_rejected(tmp_path, monkeypatch):
    path, _, _, _ = synthetic_freeze(tmp_path, monkeypatch)
    record = json.loads(path.read_text())
    record["specification"]["alpha"] = .2
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="specification"):
        study.verify_freeze(path, expected_sha256=study.file_sha(path), root=tmp_path)


def test_runtime_version_mismatch_fails_before_loading_archive(tmp_path, monkeypatch):
    path, digest, _, _ = synthetic_freeze(tmp_path, monkeypatch)
    monkeypatch.setattr(study.platform, "python_version", lambda: "synthetic-other-version")
    with pytest.raises(ValueError, match="environment differs"):
        study.verify_freeze(path, expected_sha256=digest, root=tmp_path)


def test_numpy_version_mismatch_fails_before_loading_archive(tmp_path, monkeypatch):
    path, digest, _, _ = synthetic_freeze(tmp_path, monkeypatch)
    monkeypatch.setattr(study.np, "__version__", "synthetic-other-version")
    with pytest.raises(ValueError, match="environment differs"):
        study.verify_freeze(path, expected_sha256=digest, root=tmp_path)


def audit_fixture(tmp_path, monkeypatch):
    required = [f"studies/{study.NS}/PLAN.md", f"src/latent_art_bench/{study.NS}.py",
                f"tests/{study.NS}/test_one.py", f"tests/{study.NS}/test_two.py"]
    bindings = {}
    for relative in required:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"synthetic content for {relative}\n")
        bindings[relative] = study.file_sha(path)
    monkeypatch.setattr(study, "own_paths", lambda root: required)
    audit = dict(schema="painter-selective-attribution-audit/1.0", study=study.NS,
                 status="passed", inputs_sha256="1" * 64,
                 bindings=[dict(path=path, sha256=digest) for path, digest in bindings.items()])
    audit_path = tmp_path / "independent-audit.json"
    study.write_new(audit_path, audit)
    return audit_path, dict(bindings=bindings), audit


def test_valid_external_audit_and_all_plan_code_test_bindings_required(tmp_path, monkeypatch):
    path, record, _ = audit_fixture(tmp_path, monkeypatch)
    audited = study.verify_audit(path, expected_sha256=study.file_sha(path),
                                 inputs_sha256="1" * 64, record=record, root=tmp_path)
    assert audited["status"] == "passed"
    with pytest.raises(ValueError, match="external expected"):
        study.verify_audit(path, expected_sha256="0" * 64,
                           inputs_sha256="1" * 64, record=record, root=tmp_path)
    required = next(iter(record["bindings"]))
    (tmp_path / required).write_text("changed after audit")
    with pytest.raises(ValueError, match="bound file changed"):
        study.verify_audit(path, expected_sha256=study.file_sha(path),
                           inputs_sha256="1" * 64, record=record, root=tmp_path)


@pytest.mark.parametrize("change", ["status", "input_identity", "missing_test", "wrong_binding",
                                    "duplicate_binding"])
def test_self_consistent_invalid_audit_rejected(tmp_path, monkeypatch, change):
    path, record, audit = audit_fixture(tmp_path, monkeypatch)
    changed = copy.deepcopy(audit)
    if change == "status":
        changed["status"] = "pending"
    elif change == "input_identity":
        changed["inputs_sha256"] = "2" * 64
    elif change == "missing_test":
        changed["bindings"].pop()
    elif change == "wrong_binding":
        changed["bindings"][-1]["sha256"] = "0" * 64
    else:
        changed["bindings"].append(changed["bindings"][-1])
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,
                       match="audit status|every constructed test|frozen study|duplicate"):
        study.verify_audit(path, expected_sha256=study.file_sha(path),
                           inputs_sha256="1" * 64, record=record, root=tmp_path)


def test_real_flag_alone_cannot_bypass_independent_audit_before_archive_load(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "verify_freeze", lambda *a, **k: dict(bindings={}))
    monkeypatch.setattr(study, "load_archive", lambda *a, **k: pytest.fail("loaded archive"))
    with pytest.raises(ValueError, match="independent passed audit"):
        study.compute_real(tmp_path / "inputs.json", expected_sha256="0" * 64, execute_real=True)


def test_real_execution_requires_explicit_flag_before_any_input_read(tmp_path, monkeypatch):
    monkeypatch.setattr(study, "verify_freeze", lambda *a, **k: pytest.fail("read real inputs"))
    with pytest.raises(ValueError, match="explicit execution"):
        study.compute_real(tmp_path / "nonexistent.json", expected_sha256="0" * 64)


def test_json_duplicates_nonfinite_path_escape_hash_and_create_once_guards(tmp_path):
    for raw in (b'{"a": 1, "a": 2}', b'{"a": NaN}', b'{"a": Infinity}'):
        with pytest.raises(ValueError):
            study.read_json_bytes(raw)
    with pytest.raises(ValueError, match="relative"):
        study.verified_bytes(tmp_path, "/outside", "0" * 64)
    with pytest.raises(ValueError, match="escapes"):
        study.verified_bytes(tmp_path, "../outside", "0" * 64)
    path = tmp_path / "one.json"
    study.write_new(path, {"value": 1})
    with pytest.raises(FileExistsError):
        study.write_new(path, {"value": 2})
    with pytest.raises(ValueError, match="bound file changed"):
        study.verified_bytes(tmp_path, "one.json", "0" * 64)


def synthetic_archive(tmp_path):
    # Numeric values are constructed, not extracted or read from retained cohorts.
    relative = study.LEARNED
    manifest = dict(rows=[dict(id=f"synthetic-{i}") for i in range(2009)],
                    models={"clip": {"name": "synthetic-clip"},
                            "csd": {"name": "synthetic-csd"}})
    manifest_path = tmp_path / relative / "inputs.json"
    study.write_new(manifest_path, manifest)
    x = np.zeros((2009, 768), dtype=np.float32)
    x[:, 0] = 1
    buffer = io.BytesIO()
    np.savez(buffer, embeddings=x)
    archive_path = tmp_path / relative / "embeddings_clip.npz"
    archive_path.write_bytes(buffer.getvalue())
    receipt = dict(input_sha256=study.file_sha(manifest_path),
                   embeddings_sha256=study.file_sha(archive_path),
                   model=manifest["models"]["clip"], shape=[2009, 768], dtype="float32")
    receipt_path = tmp_path / relative / "extraction_clip.json"
    study.write_new(receipt_path, receipt)
    record = dict(bindings={str(p.relative_to(tmp_path)): study.file_sha(p)
                            for p in (manifest_path, archive_path, receipt_path)})
    return record, manifest_path, archive_path, receipt_path


def test_archive_loader_authenticates_exact_npz_bytes_receipt_and_dtype(tmp_path):
    record, _, archive, receipt = synthetic_archive(tmp_path)
    rows, vectors = study.load_archive(tmp_path, record, "clip")
    assert len(rows) == 2009 and vectors.shape == (2009, 768)
    assert np.all(vectors[:, 0] == 1)
    archived = archive.read_bytes()
    archive.write_bytes(archived + b"tampered")
    with pytest.raises(ValueError, match="bound file changed"):
        study.load_archive(tmp_path, record, "clip")
    archive.write_bytes(archived)
    altered = json.loads(receipt.read_text())
    altered["shape"] = [1, 768]
    receipt.write_text(json.dumps(altered))
    changed = copy.deepcopy(record)
    changed["bindings"][str(receipt.relative_to(tmp_path))] = study.file_sha(receipt)
    with pytest.raises(ValueError, match="receipt census disagrees"):
        study.load_archive(tmp_path, changed, "clip")


@pytest.mark.parametrize("change", ["dtype", "member", "nonunit"])
def test_archive_self_consistent_invalid_numeric_payload_rejected(tmp_path, change):
    record, _, archive, receipt = synthetic_archive(tmp_path)
    with np.load(io.BytesIO(archive.read_bytes())) as prior:
        x = prior["embeddings"]
    buffer = io.BytesIO()
    if change == "dtype":
        np.savez(buffer, embeddings=x.astype(np.float64))
    elif change == "member":
        np.savez(buffer, embeddings=x, extra=np.array([1]))
    else:
        x[0] = 0
        np.savez(buffer, embeddings=x)
    archive.write_bytes(buffer.getvalue())
    modified = json.loads(receipt.read_text())
    modified["embeddings_sha256"] = study.file_sha(archive)
    receipt.write_text(json.dumps(modified))
    for p in (archive, receipt):
        record["bindings"][str(p.relative_to(tmp_path))] = study.file_sha(p)
    with pytest.raises(ValueError, match="shape/dtype|archive members|nonunit"):
        study.load_archive(tmp_path, record, "clip")


def full_constructed_rows():
    """Full census with one-hot vectors, never reading any empirical data."""
    rows, values = [], []
    unit = np.eye(4)
    for model in study.MODELS:
        for scene in range(14):
            for repeat in range(2):
                for a, arm in enumerate(study.ARMS):
                    rows.append(dict(id=f"{model}-{scene}-{repeat}-{arm}", model=model,
                                     role="generated", view="original", scene=scene,
                                     repeat=repeat, arm=arm))
                    values.append(np.ones(4) / 2 if a < 2 else unit[a-2])
    for role in study.COUNTS:
        for a, painter in enumerate(study.ARTISTS):
            for i in range(study.COUNTS[role][a]):
                row = dict(id=f"{role}-{a}-{i}", role=role, painter=painter,
                           view="original", path=f"synthetic/{role}-{a}-{i}.png",
                           sha256="a" * 64, box=[0, 0, 1, 1])
                rows.append(row)
                values.append(unit[a])
                if i < study.CROPS[role][a]:
                    rows.append(dict(row, view="audited_region", box=[.1, .1, .9, .9]))
                    values.append(unit[a])
    return rows, np.array(values)


def test_full_orchestration_all_eight_settings_six_models_and_sources_are_constructed(
        tmp_path, monkeypatch):
    # Exercise the entire orchestration only after replacing every real-input boundary.
    rows, values = full_constructed_rows()
    assert len(rows) == 2009
    monkeypatch.setattr(study, "verify_freeze", lambda *a, **k: dict(bindings={}))
    monkeypatch.setattr(study, "verify_audit", lambda *a, **k: dict(status="passed"))
    monkeypatch.setattr(study, "load_archive", lambda *a, **k: (rows, values))
    result = study.compute_real(tmp_path / "synthetic-inputs.json", expected_sha256="1" * 64,
                                execute_real=True, audit_path=tmp_path / "synthetic-audit.json",
                                expected_audit_sha256="2" * 64)
    assert set(result["settings"]) == {f"{e}/{v}/{t}" for e in study.ENCODERS
                                      for v in study.VIEWS for t in study.TARGETS}
    assert result["primary_joint_usefulness"] is False  # no positive risk difference
    for key, setting in result["settings"].items():
        primary = key.endswith("/primary")
        assert setting["reference_role"] == ("reference" if primary else "development")
        assert setting["calibration_role"] == ("development" if primary else "reference")
        assert setting["calibration"]["reference_counts"] == list(
            study.COUNTS[setting["reference_role"]])
        assert setting["calibration"]["calibration_counts"] == list(
            study.COUNTS[setting["calibration_role"]])
        assert [m["model"] for m in setting["models"]] == list(study.MODELS)
        assert sum(len(m["observations"]) for m in setting["models"]) == 1008
        assert len(setting["scene_deletion_summaries"]) == 14
        for m in setting["models"]:
            assert m["reference_gate"]["count"] == 112
            assert m["reference_gate"]["accepted_count"] == 112
            assert m["controls"]["free"]["reference_gate"]["count"] == 28
            assert m["controls"]["generic"]["reference_gate"]["count"] == 28
    rendered = study.report(result)
    assert all(f"## {key}" in rendered for key in result["settings"])
    assert "no generated-image coverage guarantee" in rendered
    json.dumps(result, allow_nan=False)
