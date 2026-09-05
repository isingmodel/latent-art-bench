from __future__ import annotations

import hashlib
import json

import pytest

from latent_art_bench.painter_feature_distance_v1 import analysis, cli, report


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    source = tmp_path / "source.json"
    source.write_text('{"input": 1}\n')
    code = tmp_path / "code.py"
    code.write_text("# A recorded implementation\n")
    result = dict(
        schema_version=analysis.SCHEMA, method_id="fixture-method",
        source={"inputs": [{"path": "source.json", "sha256": cli.sha256(source)}]},
        **{key: [{"distance": 1.25, "ratio": None}] for key in cli.TABLES},
    )
    monkeypatch.setattr(analysis, "analyze", lambda *_: result)
    monkeypatch.setattr(cli, "code_paths", lambda _: [code])

    def write_report(result, path):
        (path / "REPORT.md").write_text("# Derived report\n", encoding="utf-8")

    monkeypatch.setattr(report, "write_report", write_report)
    return tmp_path, result


def test_build_check_reproduces_and_does_not_touch_sources(bundle):
    root, result = bundle
    before = (root / "source.json").read_bytes()
    built = cli.build(root, "reports/distances", "fixture-method")
    assert built["status"] == "complete"
    assert cli.check(root, "reports/distances")["status"] == "PASS"
    assert (root / "source.json").read_bytes() == before
    # Another output path must produce the same manifest and derived bytes.
    cli.build(root, "tmp/reproduction", "fixture-method")
    first, second = root / "reports/distances", root / "tmp/reproduction"
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert (first / "coordinates.csv").read_text() == "distance,ratio\n1.25,\n"
    with pytest.raises(FileExistsError, match="output already exists"):
        cli.build(root, "reports/distances", "fixture-method")
    empty = root / "reports/empty"
    empty.mkdir()
    with pytest.raises(FileExistsError):
        cli.build(root, "reports/empty", "fixture-method")


@pytest.mark.parametrize("target", ["source.json", "code.py", "reports/distances/distances.csv"])
def test_check_rejects_changed_source_code_or_output(bundle, target):
    root, _ = bundle
    cli.build(root, "reports/distances", "fixture-method")
    (root / target).write_text("changed\n")
    with pytest.raises(ValueError, match="provenance hash mismatch"):
        cli.check(root, "reports/distances")


def test_check_rejects_extra_files_and_nonreproducing_results(bundle):
    root, result = bundle
    cli.build(root, "reports/distances", "fixture-method")
    extra = root / "reports/distances/unexpected.txt"
    extra.write_text("unexpected")
    with pytest.raises(ValueError, match="file set differs"):
        cli.check(root, "reports/distances")
    extra.unlink()
    result["distances"][0]["distance"] = 99.0
    with pytest.raises(ValueError, match="numeric analysis does not reproduce"):
        cli.check(root, "reports/distances")


def test_check_rejects_tampered_csv_even_if_output_hash_was_refreshed(bundle):
    root, _ = bundle
    cli.build(root, "reports/distances", "fixture-method")
    path = root / "reports/distances/distances.csv"
    path.write_text("distance,ratio\n100,\n")
    manifest_path = path.parent / "provenance.json"
    manifest = json.loads(manifest_path.read_text())
    for record in manifest["outputs"]:
        if record["path"] == "distances.csv":
            record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_bytes(cli.encoded(manifest))
    with pytest.raises(ValueError, match="report/tables/plots differ"):
        cli.check(root, "reports/distances")


def test_failed_render_does_not_publish_partial_bundle(bundle, monkeypatch):
    root, _ = bundle

    def fail(*_):
        raise RuntimeError("plot rendering failed")

    monkeypatch.setattr(report, "write_report", fail)
    with pytest.raises(RuntimeError, match="plot rendering failed"):
        cli.build(root, "reports/distances", "fixture-method")
    assert not (root / "reports/distances").exists()
    assert not list((root / "reports").glob(".feature-distance-*"))


def test_output_and_provenance_cannot_escape_allowed_paths(tmp_path):
    for path in ("data/manifests/report", "research_workspace/report", "src/report", "reports",
                 "../escaped", "."):
        with pytest.raises(ValueError):
            cli.resolve_output(tmp_path, path)
    with pytest.raises(ValueError):
        cli.verify_files(tmp_path, [{"path": "../escaped", "sha256": "x"}])
