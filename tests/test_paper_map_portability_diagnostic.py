"""Artificial comparator/orchestration tests; never simulate historical laws."""

import importlib.util
import json
import math
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagnostic = load("portability_diagnostic", ROOT / "tools/paper_map_portability_diagnostic.py")
base = load("frozen_comparator_oracle", ROOT / "tools/paper_map_release.py")


@pytest.mark.parametrize(
    "actual,expected,accepted",
    [
        (1, 1.0, True),
        (1.0, 1, False),
        (True, 1.0, False),
        (1, True, False),
        (1 + 5e-11, 1.0, True),
        (1 + 1.5e-10, 1.0, False),
        (100 + 5e-9, 100.0, True),
        (100 + 1.5e-8, 100.0, False),
        (-0.0, 0.0, True),
        (float("nan"), float("nan"), False),
        (float("inf"), float("inf"), False),
        (0.0, float("-inf"), False),
        ({"x": [1, "a"]}, {"x": [1, "a"]}, True),
        ({"x": ["a", 1]}, {"x": [1, "a"]}, False),
        ({"x": 1, "extra": {"a": 2}}, {"x": 1}, False),
        ({}, {"x": [1, 2]}, False),
        ([1], [1, 2], False),
        ([1, 2], [1], False),
        ({"x": None}, {"x": None}, True),
        ([], {}, False),
    ],
)
def test_comparator_matches_unchanged_oracle(actual, expected, accepted):
    result = diagnostic.compare_leaves(actual, expected)
    assert result["comparator_equal"] is accepted
    assert result["comparator_equal"] == base.compare(actual, expected)
    json.loads(diagnostic.encoded(result))  # Nonfinite arithmetic is explicitly tagged.


def test_all_shared_leaves_structures_exact_drift_and_support_hashes():
    expected = {
        "cells": [{"support_sha256": "old", "a/b~": 1.0, "count": 4}],
        "missing": {"v": [1, 2]},
    }
    actual = {"cells": [{"support_sha256": "new", "a/b~": 1 + 5e-11, "count": 4.0}], "extra": [3]}
    result = diagnostic.compare_leaves(actual, expected)
    found = {d["pointer"]: d for d in result["differences"]}
    assert len(found) == 5 and result["mismatch_count"] == 4
    assert found["/cells/0/a~1b~0"]["comparator_equal"] is True
    assert found["/cells/0/a~1b~0"]["absolute_difference"] > 0
    assert found["/cells/0/count"]["comparator_equal"] is False
    assert found["/cells/0/count"]["frozen_float_tolerance_applies"] is False
    assert found["/cells/0/support_sha256"]["comparator_equal"] is False
    assert found["/missing"]["expected"] == {"v": [1, 2]}
    assert result["tolerated_exact_difference_count"] == 1


def test_tolerance_is_max_not_sum_and_signed_zero_is_only_descriptive():
    d = diagnostic.compare_leaves(1 + 1.5e-10, 1.0)["differences"][0]
    assert d["absolute_difference"] < 2e-10 and not d["comparator_equal"]
    assert d["tolerance_limit"] == max(1e-10, 1e-10 * abs(1 + 1.5e-10))
    zero = diagnostic.compare_leaves(-0.0, 0.0)
    assert zero["comparator_equal"] and not zero["exact_equal"]
    assert zero["differences"][0]["actual_hex"] == "-0x0.0p+0"


def test_nonfinite_and_overflow_deviation_are_retained_as_tags():
    result = diagnostic.compare_leaves(-1e308, 1e308)
    raw = json.loads(diagnostic.encoded(result))
    assert raw["differences"][0]["signed_difference"] == {"__diagnostic_nonfinite_float__": "-inf"}
    assert diagnostic.tagged([math.nan]) == [{"__diagnostic_nonfinite_float__": "nan"}]


@pytest.fixture
def fake_runtime(tmp_path, monkeypatch):
    """Fake 27-cell calculation; the frozen real comparator is the independent oracle."""
    root, output = tmp_path / "archive", tmp_path / "diagnostic"
    root.mkdir()
    calls = []
    expected_q = {"qualification": {"cells": [{"value": 1.0, "support_sha256": "saved"}]}}
    actual_q = {"cells": [{"value": 1 + 5e-11, "support_sha256": "different"}]}
    observed_expected = {"deltaE": -0.39, "deltaQ": -5.0}
    observed_actual = {"deltaE": -0.39, "deltaQ": -5.0 + 1e-12}
    records = {
        "qualification/precision.json": expected_q,
        "export/inputs.json": {"rows": []},
        "report/analysis.json": observed_expected,
    }

    def qualify(proxy):
        calls.append("qualify")
        assert proxy == "artificial"
        return actual_q

    def observed(archive, bundle):
        calls.append("observed")
        assert archive == root and bundle == records["export/inputs.json"]
        return observed_actual, lambda value: "reconstructed report\n"

    def file_bytes(archive, relative):
        assert archive == root
        if relative == "qualification/PRECISION.md":
            return b"qualification report\n"
        if relative == "report/REPORT.md":
            return b"published report\n"
        raise AssertionError(relative)

    precision = SimpleNamespace(
        qualify=qualify,
        v1=SimpleNamespace(load_proxy=lambda archive: "artificial"),
        report=lambda value: "qualification report\n",
    )
    release = SimpleNamespace(
        QUALIFICATION="qualification",
        EXPORT="export",
        REPORT="report",
        numerical_modules=lambda archive: (None, None, precision),
        read=lambda archive, relative: records[relative],
        observed_replay=observed,
        base=SimpleNamespace(compare=base.compare, encoded=base.encoded, file_bytes=file_bytes),
    )
    monkeypatch.setattr(diagnostic, "load_release", lambda archive: release)
    monkeypatch.setattr(diagnostic, "inventory", lambda archive, module: {"source.py": "abc"})
    monkeypatch.setattr(diagnostic, "module_bindings", lambda *args: {"mock": "bound"})
    monkeypatch.setattr(diagnostic, "runtime_summary", lambda: {"runtime": "artificial"})
    return SimpleNamespace(
        root=root,
        output=output,
        calls=calls,
        release=release,
        precision=precision,
        actual_q=actual_q,
    )


def test_mismatch_does_not_suppress_observed_or_turn_into_a_strict_pass(fake_runtime):
    f = fake_runtime
    result = diagnostic.diagnose(f.root, f.output)
    assert f.calls == ["qualify", "observed"]
    assert result["status"] == "diagnostic_complete"
    assert result["phases"]["qualification"]["comparator_equal"] is False
    observed = result["phases"]["observed"]
    assert observed["exact_json"] is False and observed["exact_report"] is False
    assert observed["supplemental_tolerance"]["comparator_equal"] is True
    assert json.loads((f.output / "qualification_actual.json").read_bytes()) == f.actual_q
    assert (f.output / "observed_report.diff").read_text().startswith("--- published/")
    assert str(f.root) not in (f.output / "RECEIPT.json").read_text()
    for name, sha in result["outputs"].items():
        assert diagnostic.digest((f.output / name).read_bytes()) == sha
    with pytest.raises(FileExistsError):
        diagnostic.diagnose(f.root, f.output)
    assert f.calls == ["qualify", "observed"]


def test_qualification_exception_is_preserved_and_observed_still_runs(fake_runtime):
    f = fake_runtime

    def failed(_):
        f.calls.append("qualify")
        raise ValueError("private absolute path /Users/private/secret is not serialized")

    f.precision.qualify = failed
    result = diagnostic.diagnose(f.root, f.output)
    assert result["status"] == "diagnostic_failed"
    assert result["exceptions"][0]["stage"] == "qualification"
    assert result["phases"]["postverify"]["status"] == "verified"
    assert f.calls == ["qualify", "observed"]
    assert "secret" not in (f.output / "RECEIPT.json").read_text()


def test_post_replay_inventory_difference_fails_with_receipt(fake_runtime, monkeypatch):
    f = fake_runtime
    versions = iter([{"source.py": "before"}, {"source.py": "after"}])
    monkeypatch.setattr(diagnostic, "inventory", lambda *args: next(versions))
    result = diagnostic.diagnose(f.root, f.output)
    assert result["status"] == "diagnostic_failed"
    assert result["exceptions"][0]["type"] == "ValueError"
    assert (f.output / "observed_actual.json").exists()


def test_runtime_exception_still_checks_final_inventory(fake_runtime, monkeypatch):
    f = fake_runtime
    verifications = []

    def inventory(*args):
        verifications.append("verify")
        return {"source.py": "unchanged"}

    def unavailable_runtime():
        raise RuntimeError("artificial runtime probe failure")

    monkeypatch.setattr(diagnostic, "inventory", inventory)
    monkeypatch.setattr(diagnostic, "runtime_summary", unavailable_runtime)
    result = diagnostic.diagnose(f.root, f.output)
    assert result["status"] == "diagnostic_failed"
    assert result["phases"]["qualification"]["status"] == "not_reached"
    assert result["phases"]["observed"]["status"] == "not_reached"
    assert result["phases"]["postverify"]["status"] == "verified"
    assert verifications == ["verify", "verify"] and not f.calls


def test_bad_exporter_hash_is_rejected_before_execution(tmp_path, monkeypatch):
    root = tmp_path / "archive"
    (root / "tools").mkdir(parents=True)
    (root / diagnostic.TOOL).write_text("raise AssertionError('must never import')")
    monkeypatch.setattr(diagnostic, "PINS", {diagnostic.TOOL: "0" * 64})
    with pytest.raises(ValueError, match="fingerprint"):
        diagnostic.load_release(root)


def test_output_disjointness_symlinks_and_existing_directory(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    for output in (root, root / "nested", tmp_path):
        with pytest.raises(ValueError, match="disjoint"):
            diagnostic.diagnose(root, output)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        diagnostic.diagnose(link, tmp_path / "new")
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(FileExistsError):
        diagnostic.diagnose(root, output)


def test_guard_allows_only_new_output_writes_and_no_transport(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    with diagnostic.guarded_replay(output):
        (output / "result.json").write_text("{}")
        with pytest.raises(PermissionError, match="outside"):
            (tmp_path / "archive.py").write_text("modified")
        with pytest.raises(PermissionError, match="network/subprocess"):
            socket.socket()
        with pytest.raises(PermissionError, match="network/subprocess"):
            subprocess.run(["must-never-execute"], check=True)
    assert not (tmp_path / "archive.py").exists()


def test_cli_status_exit_is_diagnostic_not_comparison_pass(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["diagnostic", "--root", "archive", "--output", "out"])
    for status, exit_code in (("diagnostic_complete", 0), ("diagnostic_failed", 1)):
        monkeypatch.setattr(diagnostic, "diagnose", lambda *args: {"status": status, "phases": {}})
        assert diagnostic.main() == exit_code
        assert json.loads(capsys.readouterr().out)["status"] == status
