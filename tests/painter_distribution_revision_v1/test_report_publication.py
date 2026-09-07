"""Synthetic publication failures must not overwrite or misrepresent sealed reports."""

import json
import subprocess
from pathlib import Path

import pytest

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_revision_v1 import analysis, common
from latent_art_bench.painter_distribution_revision_v1 import report_publication as publication


def commit(root, message):
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-m", message], cwd=root, check=True, capture_output=True)


def synthetic_render(root, destination):
    value = read_json(root / common.DIRECTORY / "analysis.json")["value"]
    (destination / "REPORT.md").write_text(f"# Synthetic report\n\nValue: {value}\n")
    (destination / "numbers.csv").write_text(f"value\n{value}\n")
    return ["REPORT.md", Path("numbers.csv")]


@pytest.fixture
def ready(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "input.json").write_text('{"value": 7}')
    (tmp_path / "renderer_spec.txt").write_text("synthetic renderer version 1\n")
    commit(tmp_path, "numeric source")
    monkeypatch.setattr(analysis, "source_paths", lambda root: [Path("input.json")])
    monkeypatch.setattr(common, "load", lambda root: read_json(root / "input.json"))
    monkeypatch.setattr(analysis, "compute", lambda bundle: bundle)
    analysis.prepare(tmp_path)
    commit(tmp_path, "numeric freeze")
    analysis.build(tmp_path)
    commit(tmp_path, "numeric publication")
    monkeypatch.setattr(publication, "source_paths", lambda root, freeze: [
        Path("input.json"), Path("renderer_spec.txt"),
        common.DIRECTORY / "freeze.json", common.DIRECTORY / "analysis.json",
        common.DIRECTORY / "analysis_receipt.json",
    ])
    monkeypatch.setattr(publication, "render", synthetic_render)
    return tmp_path


def test_create_once_and_byte_replay_do_not_recompute_numeric_results(ready, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("report publication must not rerun the numeric stage")

    monkeypatch.setattr(analysis, "compute", forbidden)
    monkeypatch.setattr(common, "load", forbidden)
    assert publication.build(ready)["outputs"] == 2
    assert publication.build(ready, check=True)["byte_replay"]
    receipt = read_json(ready / publication.RECEIPT)
    assert not receipt["numeric_recomputed"]
    assert len(receipt["outputs"]) == 2
    with pytest.raises(ValueError, match="terminal"):
        publication.build(ready)


def test_uncommitted_renderer_is_rejected_before_output_creation(ready):
    (ready / "renderer_spec.txt").write_text("uncommitted change")
    with pytest.raises(ValueError, match="commit exact"):
        publication.build(ready)
    assert not (ready / common.REPORT).exists()
    assert not (ready / publication.RECEIPT).exists()


def test_numeric_receipt_hash_is_verified_without_recomputation(ready):
    path = ready / common.DIRECTORY / "analysis_receipt.json"
    value = read_json(path)
    value["analysis_sha256"] = "altered"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="numeric analysis receipt"):
        publication.build(ready)
    assert not (ready / common.REPORT).exists()


def test_failed_render_leaves_no_terminal_directory_or_receipt(ready, monkeypatch):
    def failure(root, destination):
        (destination / "partial.md").write_text("partial")
        raise RuntimeError("synthetic rendering failure")

    monkeypatch.setattr(publication, "render", failure)
    with pytest.raises(RuntimeError, match="rendering failure"):
        publication.build(ready)
    assert not (ready / common.REPORT).exists()
    assert not (ready / publication.RECEIPT).exists()


@pytest.mark.parametrize("defect", ["escape", "duplicate", "unlisted", "symlink"])
def test_invalid_renderer_inventory_never_publishes(ready, monkeypatch, defect):
    def invalid(root, destination):
        (destination / "ok.md").write_text("ok")
        if defect == "escape":
            return ["../escape.md"]
        if defect == "duplicate":
            return ["ok.md", "ok.md"]
        if defect == "unlisted":
            (destination / "hidden.md").write_text("extra")
        if defect == "symlink":
            (destination / "link.md").symlink_to("ok.md")
        return ["ok.md"]

    monkeypatch.setattr(publication, "render", invalid)
    with pytest.raises(ValueError, match="report output"):
        publication.build(ready)
    assert not (ready / common.REPORT).exists()


def test_output_tampering_and_extra_files_are_detected(ready):
    publication.build(ready)
    report = ready / common.REPORT / "REPORT.md"
    original = report.read_bytes()
    report.write_text("changed")
    with pytest.raises(ValueError, match="bound input changed"):
        publication.build(ready, check=True)
    report.write_bytes(original)
    (ready / common.REPORT / "extra.txt").write_text("extra")
    with pytest.raises(ValueError, match="inventory differs"):
        publication.build(ready, check=True)


def test_replay_detects_changed_rendered_bytes_even_when_saved_outputs_are_intact(
    ready, monkeypatch,
):
    publication.build(ready)

    def changed(root, destination):
        paths = synthetic_render(root, destination)
        (destination / "REPORT.md").write_text("different environment/render behavior")
        return paths

    monkeypatch.setattr(publication, "render", changed)
    with pytest.raises(ValueError, match="byte replay differs"):
        publication.build(ready, check=True)
