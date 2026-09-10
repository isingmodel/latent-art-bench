"""Artificial-only R10 checks; never sample the historical R10 qualification laws."""

import copy
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_map_validation_v1 import precision as old
from latent_art_bench.painter_map_validation_v2 import precision as new


def grid():
    return [
        dict(
            R=10,
            outputs=240,
            shape=sh,
            mean=m,
            regime=rg,
            trials=10000,
            coverage_lower=0.95,
            median_half_width=[0.2, 0.9],
        )
        for sh, m, rg in itertools.product(old.SHAPES, old.MEANS, old.REGIMES)
    ]


def test_single_candidate_and_unchanged_criteria():
    rows = grid()
    assert new.allocation_decision(rows)["selected_outputs"] == 240
    for r in rows:
        if r["regime"] != "baseline":
            r["median_half_width"] = [None, 100]
    assert new.allocation_decision(rows)["selected_R"] == 10
    rows[-1]["coverage_lower"] = 0.939999
    assert new.allocation_decision(rows)["decision"] == "stop_inferential_proposal"
    rows[-1]["coverage_lower"] = 0.94
    rows[0]["median_half_width"] = [0.25, 1.0]
    assert new.allocation_decision(rows)["selected_R"] == 10
    rows[0]["median_half_width"][1] = 1.0000001
    assert new.allocation_decision(rows)["selected_R"] is None
    assert old.MC_ALPHA == 0.05 / 81 and old.REPEATS == (4, 6, 8)


@pytest.mark.parametrize("change", ["missing", "duplicate", "R12", "trials", "width", "nan"])
def test_rejects_unplanned_or_malformed_grid(change):
    rows = grid()
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif change == "R12":
        rows[0]["R"] = 12
    elif change == "trials":
        rows[0]["trials"] = 9999
    elif change == "width":
        rows[0]["median_half_width"] = []
    else:
        rows[0]["coverage_lower"] = np.nan
    with pytest.raises(ValueError):
        new.allocation_decision(rows)


def test_orchestration_calls_only_R10_with_exact_seeds_no_numerical_trial(monkeypatch):
    calls, scenarios = [], []
    table = SimpleNamespace(free=np.zeros((2, 2, 2)), named=np.ones((2, 2, 2)))

    def scenario(proxy, sh, m, rg):
        scenarios.append((sh, m, rg))
        return table

    def simulate(table, r, trials, seed):
        calls.append((r, trials, seed.entropy))
        return dict(
            R=r, outputs=240, trials=trials, coverage_lower=0.95, median_half_width=[0.2, 0.9]
        )

    monkeypatch.setattr(old, "scenario", scenario)
    monkeypatch.setattr(old, "simulate_cell", simulate)
    result = new.qualify(object())
    assert len(calls) == len(scenarios) == 27
    assert result["selected_R"] == 10
    assert [x[2] for x in calls] == [
        [old.TRIAL_SEED, sh, m, rg, 10] for sh, m, rg in itertools.product(range(3), repeat=3)
    ]
    assert all(x[:2] == (10, 10000) for x in calls)
    assert old.REPEATS == (4, 6, 8)
    expected_hash = hashlib.sha256(
        table.free.astype("<f8").tobytes() + table.named.astype("<f8").tobytes()
    ).hexdigest()
    assert {r["support_sha256"] for r in result["records"]} == {expected_hash}


def brute(free, named, reference, w, fitted, chosen, deleted=None):
    fm, nm, a = np.array(fitted["free_mean"]), np.array(fitted["named_mean"]), fitted["scale"]
    cloud, weight, q = [], [], 0.0
    for j, rows in enumerate(chosen):
        rows = [s for r, s in enumerate(rows) if deleted != (j, r)]
        f, n = free[j, rows], named[j, rows]
        e1, e2 = n - f - nm + fm, n - nm - a * (f - fm)
        q += (
            w[j]
            * sum(
                e2[r] @ e2[s] - e1[r] @ e1[s]
                for r in range(len(rows))
                for s in range(len(rows))
                if r != s
            )
            / (len(rows) * (len(rows) - 1))
        )
        cloud.extend(f)
        weight.extend([w[j] / len(rows)] * len(rows))
    cloud, weight = np.asarray(cloud), np.array(weight)
    energy = []
    for y in (cloud + nm - fm, nm + a * (cloud - fm)):
        energy.append(2 * np.mean(cdist(reference, y) @ weight) - weight @ cdist(y, y) @ weight)
    return np.array([energy[1] - energy[0], q])


def test_R10_artificial_points_and_every_paired_deletion_match_direct():
    rng = np.random.default_rng(944)
    f, n = rng.normal(size=(2, 2, 4, 3))
    x, w = rng.normal(size=(5, 3)), np.array([0.3, 0.7])
    fitted = dict(free_mean=[0.2, -0.3, 0.1], named_mean=[0.5, 0.3, -0.4], scale=0.7)
    chosen = rng.integers(4, size=(2, 10))
    table = old.support_tables(f, n, x, w, fitted)
    result = old.statistics(table, chosen[None])
    np.testing.assert_allclose(result["estimate"][0], brute(f, n, x, w, fitted, chosen), atol=1e-13)
    deleted = np.array(
        [[brute(f, n, x, w, fitted, chosen, (j, r)) for r in range(10)] for j in range(2)]
    )
    np.testing.assert_allclose(result["deleted"][0], deleted, atol=1e-13)
    np.testing.assert_allclose(
        result["variance"][0],
        0.9 * ((deleted - deleted.mean(1, keepdims=True)) ** 2).sum((0, 1)),
        atol=1e-13,
    )
    t8, t10 = old.exact_truth(table, 8), old.exact_truth(table, 10)
    distances = table.distances.reshape(2, 4, 2, 4).mean((1, 3))
    expected = (1 - fitted["scale"]) * (w * w @ distances.diagonal()) * (1 / 8 - 1 / 10)
    assert t10["estimate"][0] - t8["estimate"][0] == pytest.approx(expected, abs=1e-14)
    assert t10["estimate"][1] == t8["estimate"][1]


def test_unchanged_original_terminal_bundle_and_sources_verify_without_rerun():
    root = Path(__file__).resolve().parents[2]
    value = new.read_previous(root)
    assert value["decision"] == "stop_inferential_proposal"
    assert value["source_commit"] == new.PREVIOUS_COMMIT
    assert len(value["artifacts"]) == 3
    assert len(new.BINDINGS) == 20


def test_previous_hash_tampering_rejected_before_any_simulation(tmp_path):
    path = tmp_path / new.PREVIOUS_PATH / "RUN.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ValueError, match="terminal hash"):
        new.read_previous(tmp_path)


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_commit_gate_create_once_and_no_real_qualification(tmp_path, monkeypatch):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    (tmp_path / "source.txt").write_text("initial")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "artificial fixture")
    monkeypatch.setattr(new, "BINDINGS", (Path("source.txt"),))
    monkeypatch.setattr(
        new, "read_previous", lambda root: dict(decision="stop_inferential_proposal")
    )
    monkeypatch.setattr(old, "load_proxy", lambda root: dict(scene_ids=["artificial"]))
    calls = []
    result = dict(new.allocation_decision(grid()), records=[])
    monkeypatch.setattr(new, "qualify", lambda proxy: calls.append(True) or result)
    (tmp_path / "source.txt").write_text("dirty")
    with pytest.raises(ValueError, match="commit clean"):
        new.build(tmp_path)
    assert not calls
    (tmp_path / "source.txt").write_text("initial")
    value = new.build(tmp_path)
    assert calls == [True] and value["cross_version_confidence_claim"] is False
    assert json.loads((tmp_path / new.OUTPUT_PATH / "precision.json").read_text()) == value
    with pytest.raises(ValueError, match="create-once"):
        new.build(tmp_path)
    assert "V1 remains stopped" in new.report(value)
