"""Constructed finite-array algebra only; no scientific outcomes or extraction."""

import itertools
import json

import numpy as np
import pytest

from latent_art_bench.painter_family_controls_v1.secondary_features import (
    BASELINES,
    SHAPE,
    analyze_realized_features,
)

TIMES = [dict(start=f"constructed-{i}", completion=f"constructed-{i}-end") for i in range(8)]


def panel():
    return np.zeros(SHAPE)


def oracle():
    x = panel()
    x[..., 0, 0] = -1
    x[..., 2, 0] = 1
    x[..., 3, 0] = 3
    x[..., 4:, 0] = [1, 2, 3, 2]
    return x


def test_exact_energies_vectors_and_negative_path_interactions():
    report = analyze_realized_features(oracle(), TIMES)
    assert report["axes"]["shape"] == list(SHAPE)
    assert len(report["axes"]["features"]) == 31
    assert len(report["models"]) == 6
    assert report["window_times"] == TIMES
    assert report["observed_cells"] == 4608
    assert report["missing_cells"] == []
    model = report["models"][0]
    assert model["specific_energy"]["equal_window_mean"] == 2
    for baseline, common in zip(BASELINES, (36, 16, 4, 4)):
        row = model["baselines"][baseline]
        assert row["common_energy"]["window_values"] == [common] * 8
        assert row["total_energy"]["equal_window_mean"] == common + 2
        assert row["decomposition_residual"]["equal_window_mean"] == 0
    path = model["paths"]["generic_via_shared_family"]
    expected = {
        "control_energy": 36, "remaining_common_energy": 4,
        "combined_common_energy": 16, "signed_interaction": -24,
        "signed_total_energy_change": 12, "scalar_identity_residual": 0,
        "total_change_identity_residual": 0, "vector_identity_max_abs_residual": 0,
    }
    for key, value in expected.items():
        assert path["components"][key]["equal_window_mean"] == value
    assert path["vectors_by_window"]["control_displacement"][0][0] == 3
    assert path["vectors_by_window"]["remaining_named_displacement"][0][0] == -1
    assert model["specific_pairwise_identity_residual"]["equal_window_mean"] == 0
    assert report["scaler_contract"]["new_scaler_fitting"] is False
    json.dumps(report, allow_nan=False)


def test_scene_averaging_precedes_squares_and_window_averaging_follows():
    x = panel()
    # Within every window, named scene vectors cancel; scene-level energies do not.
    x[:, :, :6, 4:, 0] = 1
    x[:, :, 6:, 4:, 0] = -1
    report = analyze_realized_features(x, TIMES)
    assert report["models"][0]["baselines"]["generic"]["common_energy"]["equal_window_mean"] == 0
    # Window means alternate, so pooling windows before squaring would erase all energy.
    x[..., 4:, 0] = np.array([1, -1] * 4)[None, :, None, None]
    model = analyze_realized_features(x, TIMES)["models"][0]
    assert model["baselines"]["generic"]["common_energy"]["equal_window_mean"] == 4
    assert np.mean(model["named_means_by_window"], axis=0)[0] == 0


def test_general_multicoordinate_identities_and_equal_window_influence():
    x = np.random.default_rng(2026091908).normal(size=SHAPE)
    x *= np.arange(1, 9)[None, :, None, None, None]
    report = analyze_realized_features(x, TIMES)
    for model in report["models"]:
        specific = np.array(model["specific_energy"]["window_values"])
        np.testing.assert_allclose(
            model["specific_pairwise_identity_residual"]["window_values"], 0, atol=1e-12
        )
        for row in model["baselines"].values():
            common = np.array(row["common_energy"]["window_values"])
            total = np.array(row["total_energy"]["window_values"])
            np.testing.assert_allclose(total, common + specific, atol=1e-12)
            summary = row["total_energy"]
            assert summary["equal_window_mean"] == pytest.approx(total.mean())
            assert summary["between_window_sd"] == pytest.approx(total.std(ddof=1))
            np.testing.assert_allclose(
                summary["leave_one_window_out"]["means"],
                [np.delete(total, i).mean() for i in range(8)],
            )
        for row in model["paths"].values():
            terms = row["components"]
            for residual in (
                "scalar_identity_residual", "total_change_identity_residual",
                "vector_identity_max_abs_residual",
            ):
                np.testing.assert_allclose(terms[residual]["window_values"], 0, atol=1e-12)


def test_missing_baseline_cancels_and_no_partial_panel_reweighting():
    x = oracle()
    x[0, 0, 0, 1] = np.nan  # Generic missing: family/framing remain usable.
    x[1, 1, 1, 4] = np.nan  # Named missing: control-only energy remains usable.
    result = analyze_realized_features(x, TIMES)
    first, second = result["models"][:2]
    incomplete = first["baselines"]["generic"]["common_energy"]
    assert incomplete["window_values"] == [None] + [16] * 7
    assert incomplete["equal_window_mean"] is None
    assert incomplete["between_window_sd"] is None
    assert incomplete["leave_one_window_out"] is None
    assert first["baselines"]["shared_family"]["common_energy"]["equal_window_mean"] == 4
    assert first["specific_energy"]["equal_window_mean"] == 2
    assert first["paths"]["style_frame_via_shared_family"]["components"][
        "control_energy"
    ]["equal_window_mean"] == 16
    assert second["specific_energy"]["window_values"][1] is None
    path = second["paths"]["generic_via_shared_family"]["components"]
    assert path["control_energy"]["equal_window_mean"] == 36
    assert path["remaining_common_energy"]["equal_window_mean"] is None
    assert result["observed_cells"] == 4606
    assert len(result["missing_cells"]) == 2
    assert first["missing_cells_by_window"] == [1, 0, 0, 0, 0, 0, 0, 0]
    assert first["complete_arm_scene_panels_by_window"][0][1] is False


def test_explicit_mask_ignores_finite_placeholders_and_all_missing_is_retained():
    x = oracle()
    observed = np.ones(SHAPE[:-1], dtype=bool)
    observed[0] = False
    x[0] = 1000  # Ignored, never treated as zero or a generated image.
    result = analyze_realized_features(x, TIMES, observed=observed)
    assert result["models"][0]["specific_energy"]["window_values"] == [None] * 8
    assert result["models"][0]["specific_energy"]["equal_window_mean"] is None
    assert result["models"][1]["specific_energy"]["equal_window_mean"] == 2
    assert len(result["missing_cells"]) == 768
    assert len(result["models"]) == 6


def test_exact_noise_contribution_finite_enumeration():
    # Each arm's scene-averaged error is an independent +/-1 variable; means zero.
    # Repeat each error over scenes, deliberately allowing perfect within-arm
    # cross-scene dependence. Enumerate the 32 possibilities, never fit data.
    energies = []
    for errors in itertools.product((-1, 1), repeat=5):
        x = panel()
        x[..., 1, 0] = errors[0]
        x[..., 4:, 0] = errors[1:]
        model = analyze_realized_features(x, TIMES)["models"][0]
        generic = model["baselines"]["generic"]
        energies.append([
            generic["common_energy"]["equal_window_mean"],
            model["specific_energy"]["equal_window_mean"],
            generic["total_energy"]["equal_window_mean"],
        ])
    # C has v_named + 4 v_baseline, S has 3 v_named, Q has 4+4.
    np.testing.assert_allclose(np.mean(energies, axis=0), [5, 3, 8])


def test_drift_without_noise_invalidates_cross_window_products():
    x = panel()
    deterministic_means = np.array([1, -1] * 4)
    x[..., 4:, 0] = deterministic_means[None, :, None, None]
    model = analyze_realized_features(x, TIMES)["models"][0]
    common = model["baselines"]["generic"]["common_energy"]
    assert common["equal_window_mean"] == 4
    cross = np.outer(deterministic_means, deterministic_means)
    assert cross[~np.eye(8, dtype=bool)].mean() == pytest.approx(-1 / 7)
    assert deterministic_means.mean() ** 2 == 0
    # Neither 4 nor 0 is the scaled off-window product -4/7.


def test_signed_total_change_can_be_negative_and_zero_totals_need_no_ratio():
    x = panel()
    x[..., 3, 0] = 2
    result = analyze_realized_features(x, TIMES)
    model = result["models"][0]
    assert model["baselines"]["generic"]["total_energy"]["equal_window_mean"] == 0
    terms = model["paths"]["generic_via_shared_family"]["components"]
    assert terms["signed_interaction"]["equal_window_mean"] == -32
    assert terms["signed_total_energy_change"]["equal_window_mean"] == -16
    for forbidden in ("common_fraction", "specific_fraction", "fieller", "ci95"):
        assert forbidden not in json.dumps(result)


@pytest.mark.parametrize("bad", [np.inf, -np.inf, np.nan])
def test_reject_partial_nonfinite_even_if_masked(bad):
    x = panel()
    x[0, 0, 0, 0, 0] = bad
    observed = np.ones(SHAPE[:-1], dtype=bool)
    observed[0, 0, 0, 0] = False
    with pytest.raises(ValueError, match="entirely finite"):
        analyze_realized_features(x, TIMES, observed=observed)


def test_reject_wrong_axes_mask_times_and_overflow():
    x = panel()
    with pytest.raises(ValueError, match="axes"):
        analyze_realized_features(x[..., :30], TIMES)
    with pytest.raises(ValueError, match="boolean"):
        analyze_realized_features(x, TIMES, observed=np.ones(SHAPE[:-1]))
    with pytest.raises(ValueError, match="eight"):
        analyze_realized_features(x, TIMES[:7])
    with pytest.raises(ValueError, match="strict JSON"):
        analyze_realized_features(x, [np.nan] * 8)
    x[0, 0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="observed cell"):
        analyze_realized_features(x, TIMES, observed=np.ones(SHAPE[:-1], dtype=bool))
    with pytest.raises(ValueError, match="masked arrays"):
        analyze_realized_features(np.ma.array(panel()), TIMES)
    x = panel()
    x[..., 4:, :] = 1e308
    with pytest.raises(ValueError, match="overflows"):
        analyze_realized_features(x, TIMES)
