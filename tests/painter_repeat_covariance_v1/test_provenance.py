"""Temporary/mocked provenance tests; no retained vectors or outcomes are read."""

import itertools
import json

import pytest

from latent_art_bench import painter_repeat_covariance_v1 as covariance


def test_writer_refuses_replacement_and_rejects_nonfinite_json(tmp_path):
    path = tmp_path / "new" / "result.json"
    covariance.write_new(path, {"value": 3})
    with pytest.raises(FileExistsError):
        covariance.write_new(path, {"value": 4})
    assert json.loads(path.read_text()) == {"value": 3}
    bad = tmp_path / "bad.json"
    with pytest.raises(ValueError):
        covariance.write_new(bad, {"value": float("nan")})
    assert not bad.exists()


def test_freeze_only_binds_sources_and_rejects_mutation_or_replacement(tmp_path, monkeypatch):
    source = tmp_path / "source.py"
    source.write_text("# synthetic fixture\n")
    monkeypatch.setattr(covariance.s, "ROOT", tmp_path)
    monkeypatch.setattr(covariance, "OUT", tmp_path / "out")
    monkeypatch.setattr(covariance, "binding_paths", lambda: [source])
    monkeypatch.setattr(covariance, "verify_inherited_bindings", lambda: None)

    def forbidden(*args, **kwargs):
        pytest.fail("hash-only freeze must not load or compute real data")

    monkeypatch.setattr(covariance, "compute_real", forbidden)
    monkeypatch.setattr(covariance.measured, "load", forbidden)
    covariance.freeze()
    assert covariance.verify_freeze()["rho_grid"] == [0, .1, .25, .5, .75]
    with pytest.raises(FileExistsError):
        covariance.freeze()
    source.write_text("# modified synthetic fixture\n")
    with pytest.raises(ValueError, match="frozen covariance input changed"):
        covariance.verify_freeze()


def test_execution_requires_flag_before_compute(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("CLI must reject real execution without explicit flag")

    monkeypatch.setattr(covariance, "execute", forbidden)
    for action in ("analyze", "check"):
        monkeypatch.setattr("sys.argv", ["module", action])
        with pytest.raises(SystemExit) as error:
            covariance.main()
        assert error.value.code == 2


def test_existing_results_block_analysis_before_compute(tmp_path, monkeypatch):
    monkeypatch.setattr(covariance, "OUT", tmp_path)
    (tmp_path / "REPORT.md").write_text("retained\n")

    def forbidden():
        pytest.fail("existing artifacts must block recomputation in analyze mode")

    monkeypatch.setattr(covariance, "compute_real", forbidden)
    with pytest.raises(FileExistsError):
        covariance.execute()
    assert (tmp_path / "REPORT.md").read_text() == "retained\n"


def test_canonical_replay_rejects_shape_or_numeric_disagreement():
    covariance.require_replay([1, 2], [1, 2], "fixture")
    for value in ([1], [1, 2.01]):
        with pytest.raises(ValueError, match="canonical replay differs"):
            covariance.require_replay(value, [1, 2], "fixture")


def test_output_replay_preserves_all_synthetic_curves_and_detects_changed_report(
    tmp_path, monkeypatch
):
    models = [dict(
        model=f"model-{i}", title=f"Synthetic {i}", d=float(i + 1), q=float(i + 2),
        grid=covariance.model_curve(i + 1, i + 2),
    ) for i in range(6)]
    pairs = [dict(
        title_a=a["title"], title_b=b["title"],
        **covariance.pair_curve(a["d"], a["q"], b["d"], b["q"]),
    ) for a, b in itertools.combinations(models, 2)]
    synthetic = dict(models=models, pairs=pairs, inputs_sha256="synthetic-test-binding")
    monkeypatch.setattr(covariance, "OUT", tmp_path)
    monkeypatch.setattr(covariance, "compute_real", lambda: synthetic)
    covariance.execute()
    covariance.execute(check=True)
    saved = json.loads((tmp_path / "analysis.json").read_text())
    assert len(saved["models"]) == 6
    assert len(saved["pairs"]) == 15
    assert all(len(row["grid"]) == 5 for row in saved["models"] + saved["pairs"])
    markdown = (tmp_path / "REPORT.md").read_text()
    for pair in pairs:
        assert f"{pair['title_a']} minus {pair['title_b']}" in markdown
    (tmp_path / "REPORT.md").write_text(markdown + "changed\n")
    with pytest.raises(ValueError, match="exact covariance sensitivity replay differs"):
        covariance.execute(check=True)
