"""Constructed-data checks for diagnostics v7."""

import itertools

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v7 as v7
from latent_art_bench.painter_specificity_v3 import analysis


def test_pair_types_partition_the_28_pairs():
    types = v7.pair_types()
    assert [len(v) for v in types.values()] == [6, 6, 16]
    assert sorted(np.concatenate(list(types.values()))) == list(range(28))
    pairs = list(itertools.combinations(range(8), 2))
    assert all(a < 4 and b < 4 for a, b in (pairs[i] for i in types["within_century"]))
    assert all(a >= 4 for a, _ in (pairs[i] for i in types["within_hudson"]))


def test_spearman_by_type_reproduces_the_mantel_statistic():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(3, 12, 2, 8, 5))
    means = rng.normal(size=(8, 5)) * 2
    x += means[None, None, None]
    recorded = analysis.mantel(x, means)
    out = v7.spearman_by_type(recorded["reference_pairs"], recorded["name_pairs_by_configuration"])
    assert out["all"]["mean"] == pytest.approx(recorded["pooled_spearman"])
    assert out["within_century"]["pairs"] == 6 and out["across"]["pairs"] == 16


def _collection(rng, p=6):
    x = rng.normal(size=(2, 12, 2, 10, p))
    x[:, :, :, 2:6] += rng.normal(size=(1, 1, 1, 4, p)) * 3
    x[:, :, :, 6:] += rng.normal(size=(1, 1, 1, 1, p)) * 3
    means = {"century": rng.normal(size=(4, p)) * 3, "hudson": rng.normal(size=(4, p)) * 0.3}
    return x, means


def test_contrast_point_values_match_the_h1_estimator():
    rng = np.random.default_rng(8)
    x, means = _collection(rng)
    out = v7.contrast(x, means, draws=50)
    for m in range(2):
        expected = (analysis.shared_fraction(x[m][:, :, [0, 1, 2, 3, 4, 5]])
                    - analysis.shared_fraction(x[m][:, :, [0, 1, 6, 7, 8, 9]]))
        assert out["observed_difference"][m] == pytest.approx(expected)
    assert out["mean_excess"] == pytest.approx(
        out["mean_observed_difference"] - out["mean_faithful_difference"])
    lo, hi = out["mean_faithful_difference_ci95"]
    assert lo <= hi


def test_census_replays_the_h1_interval():
    rng = np.random.default_rng(9)
    x, _ = _collection(rng)
    arms = {"century": (0, 1, 2, 3, 4, 5), "hudson": (0, 1, 6, 7, 8, 9)}
    recorded = analysis.closeness_test(x, arms, draws=40, seed=11)
    out = v7.census(x, draws=40, seed=11)
    assert out["pooled_ci95"] == pytest.approx(recorded["pooled_ci95"])
    assert all(0 <= n <= 40 for counts in out["nonpositive_denominator"].values() for n in counts)
