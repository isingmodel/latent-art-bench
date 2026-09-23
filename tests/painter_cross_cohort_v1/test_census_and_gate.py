"""Synthetic metadata and create-once gates; no empirical outcomes loaded."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from latent_art_bench import painter_cross_cohort_v1 as a


@pytest.fixture
def census():
    requests, outputs, features = [], [], []
    for block in range(25):
        for scene in a.SCENES:
            for arm in a.ARMS:
                identity = f"b{block:03d}-{scene}-{arm}"
                cell = dict(block=block, template_id=scene, condition=arm)
                requests.append(dict(request_id=identity, **cell))
                outputs.append(
                    dict(request_id=identity, status="generated", sha256="fixture", **cell)
                )
                features.append(
                    dict(
                        image_id=identity,
                        status="measured",
                        raw_sha256="fixture",
                        values=[0.0] * 31,
                        normalization=dict(
                            crop_fraction=0.0,
                            short_side=512,
                            original_width=512,
                            original_height=512,
                            normalized_width=512,
                            normalized_height=512,
                            color_profile="missing_assumed_srgb",
                        ),
                        **cell,
                    )
                )
    return requests, outputs, features


def test_complete_foreign_free_grid_is_accepted(census):
    output, feature = a.validate_cell_rows(*census)
    assert len(output) == len(feature) == 2000


@pytest.mark.parametrize("target", [0, 1, 2])
def test_missing_rows_are_rejected(census, target):
    census[target].pop()
    with pytest.raises(ValueError, match="incomplete"):
        a.validate_cell_rows(*census)


@pytest.mark.parametrize("target", [0, 1, 2])
def test_duplicate_rows_are_rejected(census, target):
    census[target][-1] = copy.deepcopy(census[target][0])
    with pytest.raises(ValueError, match="duplicate"):
        a.validate_cell_rows(*census)


@pytest.mark.parametrize(
    "target,key,value",
    [
        (0, "condition", "other"),
        (0, "block", False),
        (1, "block", True),
        (2, "condition", "other"),
        (2, "raw_sha256", "changed"),
        (1, "status", "failed"),
        (2, "status", "failed"),
    ],
)
def test_invalid_cell_provenance_is_rejected(census, target, key, value):
    census[target][0][key] = value
    with pytest.raises(ValueError):
        a.validate_cell_rows(*census)


@pytest.mark.parametrize("value", [[0.0] * 30, [float("nan")] * 31, [float("inf")] * 31])
def test_invalid_features_are_rejected(census, value):
    census[2][0]["values"] = value
    with pytest.raises(ValueError, match="feature vector"):
        a.validate_cell_rows(*census)


def test_changed_normalization_rejected(census):
    census[2][0]["normalization"]["crop_fraction"] = 0.01
    with pytest.raises(ValueError, match="normalization"):
        a.validate_cell_rows(*census)


@pytest.mark.parametrize("command", ["analyze", "check"])
def test_cli_requires_explicit_real_execution(command):
    with pytest.raises(SystemExit):
        a.main([command])


def test_loader_denies_before_reading_any_paths(tmp_path):
    with pytest.raises(PermissionError, match="execute-real"):
        a.load_frozen(tmp_path)


def test_explicit_real_flag_still_requires_external_input_hash(tmp_path):
    with pytest.raises(ValueError, match="external expected"):
        a.load_frozen(tmp_path, execute_real=True)


@pytest.mark.parametrize("command", ["analyze", "check"])
def test_cli_still_requires_external_hash(command):
    with pytest.raises(SystemExit):
        a.main([command, "--execute-real"])


def test_freeze_requires_audit_argument():
    with pytest.raises(SystemExit):
        a.main(["freeze"])


def make_code(root):
    files = [
        a.PLAN,
        a.IMPLEMENTATION,
        a.OUT / "audit.json",
        Path("pytest-paper.ini"),
        Path("tests") / a.NS / "test_fixture.py",
    ]
    for path in files:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text("fixture\n")
    bindings = [dict(path=str(p), sha256=a.sha(root / p)) for p in a.code_paths(root)]
    audit_path = root / a.OUT / "audit.json"
    audit_path.write_text(json.dumps(dict(status="passed", bindings=bindings)))
    return audit_path


def test_audit_must_bind_all_code_and_plan(tmp_path):
    audit = make_code(tmp_path)
    assert a.verify_audit(audit, tmp_path)["status"] == "passed"
    content = a.read(audit)
    content["bindings"].pop()
    audit.write_text(json.dumps(content))
    with pytest.raises(ValueError, match="audit must bind"):
        a.verify_audit(audit, tmp_path)


def test_audit_cannot_be_unpassed_or_stale(tmp_path):
    audit = make_code(tmp_path)
    (tmp_path / a.PLAN).write_text("changed\n")
    with pytest.raises(ValueError, match="binding changed"):
        a.verify_audit(audit, tmp_path)
    audit.write_text(json.dumps(dict(status="failed", bindings=[])))
    with pytest.raises(ValueError, match="must pass"):
        a.verify_audit(audit, tmp_path)


def test_freeze_is_metadata_only_and_create_once(tmp_path, monkeypatch):
    audit = make_code(tmp_path)
    monkeypatch.setattr(
        a, "validate_census", lambda root: dict(bindings=[], provenance={"fixture": True})
    )
    monkeypatch.setattr(a, "summarize", lambda *args: pytest.fail("freeze computed outcomes"))
    result = a.freeze(audit, tmp_path)
    assert result["empirical_summaries_computed"] is False
    with pytest.raises(FileExistsError):
        a.freeze(audit, tmp_path)


def test_binding_escape_duplicate_and_mutation(tmp_path):
    p = tmp_path / "x"
    p.write_text("a")
    binding = dict(path="x", sha256=a.sha(p))
    a.verify_bindings([binding], tmp_path)
    with pytest.raises(ValueError, match="duplicate"):
        a.verify_bindings([binding, binding], tmp_path)
    with pytest.raises(ValueError, match="inside repository"):
        a.verify_bindings([dict(path="../x", sha256=binding["sha256"])], tmp_path)
    p.write_text("b")
    with pytest.raises(ValueError, match="binding changed"):
        a.verify_bindings([binding], tmp_path)


@pytest.mark.parametrize("text", ['{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}'])
def test_strict_json_rejects_ambiguous_numbers_and_keys(text):
    with pytest.raises(ValueError):
        a._json(text)


def test_write_never_overwrites(tmp_path):
    path = tmp_path / "new.json"
    a.write_new(path, dict(first=True))
    with pytest.raises(FileExistsError):
        a.write_new(path, dict(first=False))
    assert a.read(path) == {"first": True}


def test_constructed_analysis_serialization_replay_and_mutation(tmp_path, monkeypatch):
    # All data are created here. The real-census loader is replaced, never called.
    z, means = np.zeros((25, 1, 5, 31)), np.zeros((4, 31))
    z[:, :, 1:, 0] = 2
    means[:, 0] = [-3, -1, 1, 3]
    a.write_new(tmp_path / a.OUT / "inputs.json", {"constructed_test_only": True})
    digest = a.sha(tmp_path / a.OUT / "inputs.json")
    monkeypatch.setattr(a, "load_frozen", lambda *args, **kwargs: (z, means, {}))
    result = a.analyze(tmp_path, execute_real=True, expected_inputs_sha256=digest)
    assert result["blocks"] == 25
    assert a.check(tmp_path, execute_real=True, expected_inputs_sha256=digest)["status"] == "passed"
    with pytest.raises(FileExistsError):
        a.analyze(tmp_path, execute_real=True, expected_inputs_sha256=digest)
    path = tmp_path / a.OUT / "analysis.json"
    altered = a.read(path)
    altered["families"]["all31"]["pooled"]["C"] = 15
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="replay failed"):
        a.check(tmp_path, execute_real=True, expected_inputs_sha256=digest)
