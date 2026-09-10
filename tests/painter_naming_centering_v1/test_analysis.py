"""Synthetic checks only: no retained input files or scientific output evaluation."""

import copy
import json

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_naming_centering_v1 import analysis as c
from latent_art_bench.painter_naming_geometry_v1 import analysis as old
from latent_art_bench.painter_naming_geometry_v1.geometry import apply, energy_terms, fit_map


def fixed_map(scale=0.4):
    training = np.array([[-2., 1.], [0., -3.], [5., 2.]])
    weights = np.array([0.2, 0.3, 0.5])
    fitted = fit_map(training, scale * training + [4., -1.], weights)
    evaluation = training + [8., -11.]
    return training, evaluation, weights, fitted


def test_same_mean_as_translation_and_same_centered_distances_as_old_scale():
    _, free, w, fitted = fixed_map()
    frozen = copy.deepcopy(fitted)
    centered, record = c.apply_centered(free, w, fitted)
    shift, scale = apply(free, fitted, "translation"), apply(free, fitted)
    assert w @ centered == pytest.approx(w @ shift)
    assert cdist(centered, centered) == pytest.approx(cdist(scale, scale))
    offset = (fitted["scale"] - 1) * (w @ free - np.array(fitted["free_mean"]))
    assert w @ scale - w @ shift == pytest.approx(offset)
    assert centered - scale == pytest.approx(np.broadcast_to(-offset, free.shape))
    assert record["old_scale_minus_translation_mean"] == pytest.approx(offset)
    assert record["centered_minus_translation_mean"] == pytest.approx([0., 0.], abs=1e-13)
    assert fitted == frozen
    assert json.loads(json.dumps(record, allow_nan=False)) == record


def test_centering_uses_weighted_evaluation_mean_and_original_scale_displacement():
    _, free, w, fitted = fixed_map(0.6)
    centered, record = c.apply_centered(free, w, fitted)
    unweighted, _ = c.apply_centered(free, np.full(3, 1 / 3), fitted)
    assert record["evaluation_free_mean"] == pytest.approx(w @ free)
    assert record["fixed_training_scale"] == fitted["scale"]
    assert record["training_displacement"] == pytest.approx(
        np.array(fitted["named_mean"]) - np.array(fitted["free_mean"]))
    assert not np.allclose(centered, unweighted)
    assert centered - unweighted == pytest.approx(np.broadcast_to(
        (1 - fitted["scale"]) * (w @ free - free.mean(axis=0)), free.shape))


def test_unit_scale_collapses_to_translation_and_equal_means_collapse_to_old_map():
    training, evaluation, weights, fitted = fixed_map(1.0)
    centered, _ = c.apply_centered(evaluation, weights, fitted)
    assert centered == pytest.approx(apply(evaluation, fitted, "translation"))
    training, _, weights, fitted = fixed_map(0.4)
    centered, _ = c.apply_centered(training, weights, fitted)
    assert centered == pytest.approx(apply(training, fitted))


def test_centering_can_help_or_harm_proximity_for_known_reference_clouds():
    _, free, weights, fitted = fixed_map()
    centered, _ = c.apply_centered(free, weights, fitted)
    anchored = apply(free, fitted)
    # Each map can be the exact empirical target; centering has no universal benefit.
    for target, exact, alternative in ((centered, centered, anchored),
                                       (anchored, anchored, centered)):
        assert energy_terms(target, exact, weights, weights)["energy"] == pytest.approx(0.)
        assert energy_terms(target, alternative, weights, weights)["energy"] > 0


def test_evaluation_named_and_reference_changes_do_not_change_centering():
    rng = np.random.default_rng(260910)
    free, named = rng.normal(size=(4, 3, 2)), rng.normal(size=(4, 3, 2))
    references = rng.normal(size=(8, 2))
    _, _, _, fitted = fixed_map()
    weights = np.array([.1, .2, .3, .4])
    old_first = old.evaluate(references, free, named, weights, fitted)
    first = c.evaluate(references, free, named, weights, fitted, old_first)
    old_changed = old.evaluate(references + 11, free, named * 3 + 7, weights, fitted)
    changed = c.evaluate(references + 11, free, named * 3 + 7, weights, fitted, old_changed)
    assert first["centering"] == changed["centering"]
    assert first["residuals"] != changed["residuals"]
    assert first["energies"]["translation_scale"]["generated_within"] == pytest.approx(
        first["energies"][c.NEW_KIND]["generated_within"])
    assert set(first["conditional_residual"]) == {
        "identity", "translation", "translation_scale"}
    assert first["conditional_residual"] == old_first["conditional_residual"]


def synthetic_inputs():
    rng = np.random.default_rng(88301)
    classes = [content for content in ("built", "land", "water") for _ in range(8)]
    ids = [f"{content}{i:02d}" for content in ("built", "land", "water") for i in range(8)]
    inputs = dict(schema="painter-naming-geometry-inputs/1", original={}, later={}, reference={},
                  targets={p: dict(built=.2, land=.3, water=.5)
                           for p in old.PAINTERS})
    for pipeline in ("primary512", "resolution256", "jpeg90_512", "common_square"):
        inputs["original"][pipeline], inputs["reference"][pipeline] = {}, {}
        if pipeline != "common_square":
            inputs["later"][pipeline] = {}
        for painter in old.PAINTERS:
            inputs["reference"][pipeline][painter] = dict(values=rng.normal(size=(8, 31)).tolist())
        for route in old.ROUTES:
            inputs["original"][pipeline][route] = {}
            for painter in old.PAINTERS:
                free = rng.normal(size=(24, 3, 31))
                named = .6 * free + np.linspace(-1, 1, 31) + rng.normal(0, .1, size=free.shape)
                inputs["original"][pipeline][route][painter] = dict(
                    scene_ids=ids[:], classes=classes[:], repeat_ids=[0, 1, 2],
                    free=free.tolist(), named=named.tolist())
        if pipeline != "common_square":
            for painter in old.PAINTERS:
                free = rng.normal(size=(24, 1, 31)) + .8
                named = .7 * free + np.linspace(-1, 1, 31)
                inputs["later"][pipeline][painter] = dict(
                    scene_ids=ids[:], classes=classes[:], repeat_ids=[0],
                    free=free.tolist(), named=named.tolist())
    return inputs


@pytest.fixture(scope="module")
def full_grid():
    inputs = synthetic_inputs()
    predecessor = json.loads(json.dumps(old.compute(inputs), allow_nan=False))
    before = json.dumps((inputs, predecessor), sort_keys=True)
    result = c.compute(inputs, predecessor)
    assert json.dumps((inputs, predecessor), sort_keys=True) == before
    return inputs, predecessor, result


def test_complete_grid_and_exact_old_metrics_retained_without_mutation(full_grid):
    _, predecessor, result = full_grid
    assert len(result["original"]) == 60 and len(result["transfer"]) == 18
    assert result["predecessor_bridge"] == dict(exact=True, original_cells=60, transfer_cells=18)
    assert result["new_images"] == 0
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    for before, after in zip(predecessor["original"], result["original"]):
        for a, b in zip(before["folds"], after["folds"]):
            assert a["fitted"] == b["fitted"]
            assert a["train_scenes"] == b["train_scenes"]
            assert a["test_scenes"] == b["test_scenes"]
            for kind in a["energies"]:
                assert a["energies"][kind] == b["energies"][kind]
                assert a["occupancy"][kind] == b["occupancy"][kind]
            assert b["occupancy"][c.NEW_KIND]["n_queries"] == 18
    for before, after in zip(predecessor["transfer"], result["transfer"]):
        assert before["fitted"] == after["fitted"]
        assert "conditional_residual" not in after
        assert after["occupancy"][c.NEW_KIND]["n_queries"] == 24


def test_fixed_path_energy_identity_and_fold_aggregation_not_pooling(full_grid):
    inputs, _, result = full_grid
    for row in result["original"]:
        assert row["energy_mean"][c.NEW_KIND] == np.mean([
            f["energies"][c.NEW_KIND]["energy"] for f in row["folds"]])
        for f in row["folds"]:
            a = f["centering_contrasts"]
            assert a["centered_minus_translation"] + a["old_scale_minus_centered"] == (
                pytest.approx(a["old_scale_minus_translation"]))
    row = result["original"][0]
    cell = inputs["original"][row["pipeline"]][row["route"]][row["painter"]]
    clouds, weights = [], []
    for fold in row["folds"]:
        ix = [cell["scene_ids"].index(s) for s in fold["test_scenes"]]
        free = np.array(cell["free"])[ix].reshape(18, 31)
        w = np.repeat(np.array(fold["test_scene_weights"]) / 3, 3)
        clouds.append(c.apply_centered(free, w, fold["fitted"])[0])
        weights.append(w / 4)
    reference = inputs["reference"][row["pipeline"]][row["painter"]]["values"]
    pooled = energy_terms(reference, np.concatenate(clouds), np.full(8, 1 / 8),
                          np.concatenate(weights))["energy"]
    assert not np.isclose(pooled, row["energy_mean"][c.NEW_KIND])


@pytest.mark.parametrize("corruption", ["metric", "duplicate_cell", "fit", "missing_cell"])
def test_changed_predecessor_fails_exact_bridge(full_grid, corruption):
    inputs, original, _ = full_grid
    predecessor = copy.deepcopy(original)
    if corruption == "metric":
        predecessor["original"][0]["residual_mean"]["translation"] += 1
    elif corruption == "duplicate_cell":
        predecessor["original"][-1] = copy.deepcopy(predecessor["original"][0])
    elif corruption == "fit":
        predecessor["transfer"][0]["fitted"]["scale"] *= 2
    else:
        predecessor["transfer"].pop()
    with pytest.raises(ValueError):
        c.compute(inputs, predecessor)


@pytest.mark.parametrize("weights", [[0., .5, .5], [-.1, .4, .7], [.2, .3, .6],
                                     [.2, .8], [float("nan"), .5, .5]])
def test_invalid_evaluation_weights_rejected(weights):
    _, free, _, fitted = fixed_map()
    with pytest.raises(ValueError, match="weights"):
        c.apply_centered(free, weights, fitted)


@pytest.mark.parametrize("bad", [[], [[float("nan"), 1.]], [[float("inf"), 1.]],
                                [[1.0, 2.0, 3.0]]])
def test_invalid_vectors_rejected(bad):
    _, _, _, fitted = fixed_map()
    with pytest.raises(ValueError):
        c.apply_centered(bad, [1.], fitted)
