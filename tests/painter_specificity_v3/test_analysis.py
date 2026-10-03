"""Known-answer checks for the prespecified v3 analysis on constructed data."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from latent_art_bench.painter_specificity_v3 import analysis as a
from latent_art_bench.painter_specificity_v3 import study as s


def constructed(spread=(3.0, 0.5), noise=0.01, seed=7):
    """Names land exactly on their references plus repeat noise; centuries spread wider."""
    rng = np.random.default_rng(seed)
    p = 31
    means = {"century": spread[0] * rng.normal(size=(4, p)),
             "hudson": spread[1] * rng.normal(size=(4, p)) + 2.0}
    x = np.zeros((6, 14, 2, 10, p))
    scene = rng.normal(size=(1, 14, 1, 1, p))
    x += scene + rng.normal(size=(6, 1, 1, 1, p))
    x[:, :, :, 1] += 1.0
    for group, columns in s.GROUP_ARMS.items():
        x[:, :, :, columns[2:]] += means[group][None, None, None]
    x += noise * rng.normal(size=x.shape)
    return x, means


def test_faithful_names_give_unit_slope_and_zero_error():
    x, means = constructed()
    summary = a.group_summary(x[0][:, :, s.GROUP_ARMS["century"]], means["century"])
    assert summary["beta"] == pytest.approx(1, abs=0.01)
    assert summary["D"] == pytest.approx(0, abs=0.01)
    assert summary["alignment_ratio"] == pytest.approx(1, abs=0.01)


def test_shared_fraction_matches_the_paper_decomposition():
    from latent_art_bench.painter_tmlr_diagnostics_v1 import decomposition

    x, means = constructed()
    view = x[2][:, :, s.GROUP_ARMS["hudson"]]
    assert a.shared_fraction(view) == pytest.approx(decomposition(view, means["hudson"])
                                                     ["shared_fraction"])


def test_closeness_supported_when_century_painters_are_farther_apart():
    x, means = constructed()
    result = a.closeness_test(x, s.GROUP_ARMS, draws=200)
    assert result["pooled_difference"] < 0 and result["supported"]
    flipped = a.closeness_test(x, {"century": s.GROUP_ARMS["hudson"],
                                   "hudson": s.GROUP_ARMS["century"]}, draws=200)
    assert not flipped["supported"]


def test_mantel_matches_scipy_and_detects_dose_response():
    x, means = constructed()
    stacked = np.concatenate([means["century"], means["hudson"]])
    named = [c for g in s.GROUP_ARMS.values() for c in g[2:]]
    result = a.mantel(x[:, :, :, named], stacked)
    reference, names = a.pair_matrices(x[0][:, :, named], stacked)
    upper = np.triu_indices(8, 1)
    expected = stats.spearmanr(reference[upper], names[upper])[0]
    assert result["spearman_by_configuration"][0] == pytest.approx(expected)
    assert result["permutations"] == 40320
    assert result["supported"] and result["exact_p_one_sided"] < 0.001

    shuffled = x[:, :, :, named][:, :, :, np.random.default_rng(1).permutation(8)]
    unrelated = a.mantel(shuffled + 5 * np.random.default_rng(2).normal(size=shuffled.shape),
                         stacked)
    assert unrelated["exact_p_one_sided"] > 0.001


def test_drift_is_zero_for_identical_collections_and_positive_for_a_shift():
    rng = np.random.default_rng(3)
    old = rng.normal(size=(14, 2, 2, 31))
    same = old[:, ::-1]
    assert a.drift(same, old)["free"]["between_collections"] == pytest.approx(
        -a.drift(old, old)["free"]["september_repeat_noise"], rel=1e-9)
    shifted = a.drift(old + 3.0, old)
    assert shifted["generic"]["between_collections"] == pytest.approx(9 * 31, rel=0.2)


def test_predictions_and_full_analysis_run():
    x, means = constructed()
    pred = a.predictions(x[:, :, :, 1], means)
    assert pred["century"]["H"] > pred["hudson"]["H"]
    assert all(c < h for c, h in zip(pred["century"]["faithful_shared_fraction"],
                                     pred["hudson"]["faithful_shared_fraction"]))
    rng = np.random.default_rng(5)
    refs = {g: [m + 0.1 * rng.normal(size=(30, 31)) for m in means[g]] for g in means}
    result = a.analyze(x, refs, s.GROUP_ARMS, september=x[:, :, :, :2], draws=50)
    assert set(result) == {"available", "complete_scenes", "groups", "primary", "closeness",
                           "dose_response", "dose_response_uncorrected", "reference_spread",
                           "drift"}
    spread = result["reference_spread"]["hudson"]
    assert 0 < spread["H_corrected"] < spread["H"]
    assert result["dose_response"]["supported"]
    assert result["primary"]["century"]["inference_family"] == 21
    assert result["primary"]["century"]["models"][0]["beta"]["mean"] == pytest.approx(1, abs=0.05)
    missing = x.copy()
    missing[0, 3, 1, 4] = np.nan
    assert a.analyze(missing, refs, s.GROUP_ARMS, draws=20)["complete_scenes"] == [
        i for i in range(14) if i != 3]
    missing[1, :3, 0, 7] = np.nan
    partial = a.analyze(missing, refs, s.GROUP_ARMS, draws=20)
    assert not partial["available"] and partial["complete_scenes"] == list(range(4, 14))


def test_panel_noise_correction_removes_finite_sample_inflation():
    rng = np.random.default_rng(11)
    means = np.zeros((4, 31))  # Identical painters: every true distance is zero.
    panels = [rng.normal(size=(n, 31)) for n in (20, 40, 80, 160)]
    observed = np.array([v.mean(axis=0) for v in panels])
    noise = np.array([a.panel_noise(v) for v in panels])
    x = np.zeros((14, 2, 4, 31))
    raw, _ = a.pair_matrices(x, observed)
    corrected, _ = a.pair_matrices(x, observed, noise)
    assert raw[0, 1] > raw[2, 3] > 0  # Small panels look farther apart.
    assert abs(corrected[0, 1]) < raw[0, 1] / 3
    assert means.shape == (4, 31)
