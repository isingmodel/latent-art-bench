"""Constructed-data checks for the second TMLR revision diagnostics."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v2 as diag


def panel(generic, named, scenes=4):
    arms = np.vstack([generic - 1.0, generic, named])
    return np.broadcast_to(arms, (scenes, 2, 6, arms.shape[1])).copy()


def test_exact_differences_equals_observed_when_names_reproduce_reference_differences():
    rng = np.random.default_rng(1)
    refs = rng.normal(size=(4, 6))
    generic = rng.normal(size=6)
    shift = rng.normal(size=6)
    named = generic + shift + (refs - refs.mean(axis=0))
    result = diag.fractions(panel(generic, named), refs)
    assert result["exact"] == pytest.approx(result["observed"])


def test_prototype_faithful_equals_observed_for_a_faithful_imitator():
    rng = np.random.default_rng(2)
    prototypes = rng.normal(size=(4, 5))
    generic = rng.normal(size=5)
    result = diag.prototype_shares(panel(generic, prototypes), prototypes)
    assert result["observed"] == pytest.approx(result["faithful"])


def test_pair_metrics_for_exact_and_doubled_pairs():
    refs = np.eye(4, 3)
    exact = diag.pair_metrics(panel(np.zeros(3), refs), refs)
    doubled = diag.pair_metrics(panel(np.zeros(3), 2 * refs), refs)
    assert all(r["beta"] == pytest.approx(1) and r["d"] == pytest.approx(0) for r in exact)
    assert all(r["beta"] == pytest.approx(2) and r["d"] == pytest.approx(1) for r in doubled)


def test_nearest_centroid_recognizes_separated_classes():
    means = np.eye(4, 3) * 10
    labels = np.repeat(np.arange(4), 3)
    values = means[labels] + 0.1
    result = diag.nearest_centroid(values, labels, means)
    assert result["macro_accuracy"] == 1.0


def test_interval_ignores_missing_values():
    assert diag.interval([None, 1.0, 2.0, 3.0]) == pytest.approx([1.05, 2.95])
    assert diag.interval([None]) is None


def test_reference_resampling_keeps_means_for_identical_works():
    refs = [np.ones((5, 2)) * k for k in range(4)]
    means = diag.resample_refs(refs, np.random.default_rng(0))
    assert means == pytest.approx(np.array([[k, k] for k in range(4)], dtype=float))
