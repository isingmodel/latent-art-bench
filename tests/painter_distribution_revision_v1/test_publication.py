import json
import subprocess

import pytest

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_revision_v1 import analysis, common


def commit(root, message):
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "-m", message], cwd=root, check=True, capture_output=True)


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    source = tmp_path / "input.json"
    source.write_text('{"value": 1}')
    commit(tmp_path, "input")
    monkeypatch.setattr(analysis, "source_paths", lambda root: [source.relative_to(root)])
    monkeypatch.setattr(common, "load", lambda root: read_json(root / "input.json"))
    monkeypatch.setattr(analysis, "compute", lambda bundle: bundle)
    analysis.prepare(tmp_path)
    return tmp_path


def test_uncommitted_freeze_and_changed_input_are_rejected(frozen):
    with pytest.raises(ValueError, match="commit exact"):
        analysis.build(frozen)
    commit(frozen, "freeze")
    (frozen / "input.json").write_text('{"value": 2}')
    with pytest.raises(ValueError, match="bound input changed"):
        analysis.build(frozen)
    assert not (frozen / common.DIRECTORY / "analysis.json").exists()


def test_terminal_publication_replays_and_rejects_overwrite_and_tampering(frozen):
    commit(frozen, "freeze")
    analysis.build(frozen)
    assert analysis.build(frozen, check=True)["numeric_replay"]
    with pytest.raises(ValueError, match="terminal"):
        analysis.build(frozen)
    path = frozen / common.DIRECTORY / "analysis.json"
    path.write_text('{"value": 2}')
    with pytest.raises(ValueError, match="bytes changed"):
        analysis.build(frozen, check=True)


def test_receipt_binds_freeze_and_numerical_replay(frozen, monkeypatch):
    commit(frozen, "freeze")
    analysis.build(frozen)
    monkeypatch.setattr(analysis, "compute", lambda bundle: {"value": 2})
    with pytest.raises(ValueError, match="replay differs"):
        analysis.build(frozen, check=True)
    path = frozen / common.DIRECTORY / "analysis_receipt.json"
    receipt = read_json(path)
    receipt["freeze_sha256"] = "bad"
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="freeze receipt"):
        analysis.build(frozen, check=True)


def test_metric_bridge_detects_changed_results_and_missing_grid():
    labels = [dict(pipeline="primary512", painter_id="p", route="r", condition=str(i))
              for i in range(14)]
    old = dict(cells=[dict(
        r, weighting="reference_content", feature_set="all31", energy_distance=1,
        population_variance_ratio=0.5, squared_iqr_sum_ratio=0.4,
    ) for r in labels], endpoints=[dict(
        painter_id="p", route=str(i), before="artist_free", after="named", estimate=-1,
    ) for i in range(6)])
    revised = dict(cells=[dict(
        r, cell_id=str(i), metric_view="original31", energy=1, trace_ratio=0.5,
        squared_iqr_sum_ratio=0.4,
    ) for i, r in enumerate(labels)], prompt_contrasts=[dict(
        r, pipeline="primary512", metric_view="original31", energy_change=-1,
    ) for r in old["endpoints"]])
    assert analysis.metric_consistency(old, revised)["prompt_contrasts"] == 6
    revised["cells"][0]["trace_ratio"] = 0.6
    with pytest.raises(ValueError, match="bridge changed"):
        analysis.metric_consistency(old, revised)
    revised["cells"].pop(0)
    with pytest.raises(ValueError, match="incomplete"):
        analysis.metric_consistency(old, revised)
