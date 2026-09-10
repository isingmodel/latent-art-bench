"""Scene leakage, temporal-map and inventory boundaries on artificial observations."""

import numpy as np
import pytest

from latent_art_bench.painter_naming_geometry_v1.analysis import crossfit, evaluate, folds, weights
from latent_art_bench.painter_naming_geometry_v1.geometry import fit_map
from latent_art_bench.painter_naming_geometry_v1.inputs import cube, paired, scale


def design():
    classes = [c for c in ("built", "land", "water") for _ in range(8)]
    ids = [f"{c}{i:02d}" for c in ("built", "land", "water") for i in range(1, 9)]
    targets = dict(built=.2, land=.3, water=.5)
    f = np.random.default_rng(71).normal(size=(24, 3, 5))
    n = f * .6 + np.arange(5)
    x = np.random.default_rng(72).normal(size=(12, 5))
    return x, f, n, classes, targets, ids


def test_exact_map_on_whole_held_scenes_and_fixed_class_masses():
    x, f, n, classes, targets, ids = design()
    out = crossfit(x, f, n, classes, targets, ids)
    assert out["residual_mean"]["translation_scale"] == pytest.approx(0, abs=1e-12)
    assert out["conditional_residual_mean"]["translation_scale"] == pytest.approx(0, abs=1e-25)
    for row in out["folds"]:
        assert len(row["train_scenes"]) == 18
        assert len(row["test_scenes"]) == 6
        assert not set(row["train_scenes"]) & set(row["test_scenes"])
        for c, mass in targets.items():
            assert sum(w for s, w in zip(row["test_scenes"], row["test_scene_weights"])
                       if s.startswith(c)) == pytest.approx(mass)
        assert row["occupancy"]["identity"]["n_queries"] == 18


def test_held_data_and_reference_cannot_change_fitted_map():
    x, f, n, classes, targets, ids = design()
    baseline = crossfit(x, f, n, classes, targets, ids)
    held = folds(ids, classes) == 0
    changed = n.copy()
    changed[held] += 100
    altered = crossfit(x * 3, f, changed, classes, targets, ids)
    assert altered["folds"][0]["fitted"] == baseline["folds"][0]["fitted"]
    assert altered["folds"][0]["residuals"] != baseline["folds"][0]["residuals"]


def test_fold_scores_averaged_not_pooled_and_deletion_reweights_within_fold():
    x, f, n, classes, targets, ids = design()
    out = crossfit(x, f, n, classes, targets, ids, delete=ids[0])
    for row in out["folds"]:
        assert ids[0] not in row["train_scenes"] + row["test_scenes"]
    assert [len(r["test_scenes"]) for r in out["folds"]] == [5, 6, 6, 6]
    assert out["energy_mean"]["named"] == np.mean(
        [r["energies"]["named"]["energy"] for r in out["folds"]])
    first = out["folds"][0]
    assert sum(w for s, w in zip(first["test_scenes"], first["test_scene_weights"])
               if s.startswith("built")) == pytest.approx(.2)


def test_temporal_evaluation_keeps_map_and_skips_unidentifiable_r1_correction():
    x, f, n, classes, targets, _ = design()
    fitted = fit_map(f.reshape(-1, 5), n.reshape(-1, 5), np.full(72, 1/72))
    frozen = {k: v[:] if isinstance(v, list) else v for k, v in fitted.items()}
    later = np.random.default_rng(9).normal(size=(24, 1, 5))
    out = evaluate(x, later, .6 * later + np.arange(5), weights(classes, targets), fitted)
    assert fitted == frozen
    assert "conditional_residual" not in out
    assert out["residuals"]["translation_scale"] == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan")])
def test_scaler_rejects_invalid_spread(bad):
    scaler = dict(center=[0] * 31, scale=[1] * 30 + [bad])
    with pytest.raises(ValueError):
        scale([[1] * 31], scaler)


def test_fixed_scaling_and_nonfinite_center():
    assert scale([[3] * 31], dict(center=[1] * 31, scale=[2] * 31)) == [[1] * 31]
    with pytest.raises(ValueError):
        scale([[3] * 31], dict(center=[float("inf")] * 31, scale=[2] * 31))


def test_cube_rejects_duplicate_images_and_changed_repeats():
    _, _, _, classes, _, ids = design()
    scaler = dict(center=[0] * 31, scale=[1] * 31)
    rows = [dict(scene=s, repetition=0, content_class=c, image_id=s, status="measured",
                 values=[0] * 31) for s, c in zip(ids, classes)]
    valid = cube(rows, "scene", 1, scaler)
    assert paired(valid, valid)["scene_ids"] == ids
    rows[-1] = dict(rows[-1], image_id=rows[0]["image_id"])
    with pytest.raises(ValueError):
        cube(rows, "scene", 1, scaler)
    rows[-1] = dict(rows[-1], image_id=ids[-1], repetition=1)
    with pytest.raises(ValueError):
        cube(rows, "scene", 1, scaler)
