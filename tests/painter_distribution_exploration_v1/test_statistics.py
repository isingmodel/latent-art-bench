import numpy as np
import pytest

from latent_art_bench.painter_distribution_exploration_v1.statistics import (
    RIDGE,
    heldout_scores,
    metrics,
    pca_fit,
    project,
    spread,
    work_folds,
)


def test_pca_matches_weighted_svd_and_preserves_distances_in_two_dimensions():
    x = np.array([[0, 0], [1, 2], [4, -2], [-2, -1]], dtype=float)
    w = np.array([0.1, 0.2, 0.3, 0.4])
    fit = pca_fit(x, w)
    singular = np.linalg.svd(np.sqrt(w[:, None]) * (x - w @ x), compute_uv=False)
    np.testing.assert_allclose(fit["explained_variance_ratio"], singular**2 / sum(singular**2))
    projected = project(x, fit)
    np.testing.assert_allclose(w @ projected, [0, 0], atol=1e-14)
    np.testing.assert_allclose(
        np.linalg.norm(projected[0] - projected[2]), np.linalg.norm(x[0] - x[2])
    )


def test_original_only_pca_is_not_refit_on_generated_images():
    reference = np.array([[-3, 0, 0], [3, 0, 0], [0, -1, 0], [0, 1, 0]])
    fit = pca_fit(reference, np.full(4, 0.25))
    np.testing.assert_array_equal(project([[0, 0, 100]], fit), [[0, 0]])
    assert sum(fit["explained_variance_ratio"]) == pytest.approx(1)


def test_work_folds_are_balanced_and_order_invariant():
    ids = [f"work:{i}" for i in range(105)]
    folds = work_folds(ids, 16)
    np.testing.assert_array_equal(folds, work_folds(ids[::-1], 16)[::-1])
    assert max(np.bincount(folds)) - min(np.bincount(folds)) == 1
    with pytest.raises(ValueError, match="unique"):
        work_folds(["same", "same"], 2)


@pytest.mark.parametrize("kind", ["linear", "rbf"])
def test_identical_empirical_distributions_have_chance_balanced_accuracy(kind):
    x = np.random.default_rng(140).normal(size=(64, 3))
    y = np.r_[np.zeros(64), np.ones(64)]
    folds = np.tile(np.arange(64) % 16, 2)
    result = metrics(y, heldout_scores(np.tile(x, (2, 1)), y, folds, kind))
    assert result["balanced_accuracy"] == pytest.approx(0.5)
    assert result["auc"] == pytest.approx(0.5)


@pytest.mark.parametrize("kind", ["linear", "rbf"])
def test_mean_shift_is_detectable_out_of_fold(kind):
    rng = np.random.default_rng(923)
    x = np.r_[rng.normal(-2, 0.15, (80, 2)), rng.normal(2, 0.15, (64, 2))]
    y = np.r_[np.zeros(80), np.ones(64)]
    folds = np.r_[np.arange(80) % 16, np.arange(64) % 16]
    assert metrics(y, heldout_scores(x, y, folds, kind))["balanced_accuracy"] > 0.99


def test_nonlinear_classifier_detects_equal_mean_different_spread():
    angles = np.arange(64) * 2 * np.pi / 64
    unit = np.c_[np.cos(angles), np.sin(angles)]
    x = np.r_[0.15 * unit, 2 * unit]
    y = np.r_[np.zeros(64), np.ones(64)]
    folds = np.tile(np.arange(64) % 16, 2)
    np.testing.assert_allclose(x[:64].mean(0), x[64:].mean(0), atol=1e-15)
    assert metrics(y, heldout_scores(x, y, folds, "rbf"))["balanced_accuracy"] > 0.99
    assert metrics(y, heldout_scores(x, y, folds, "linear"))["balanced_accuracy"] < 0.6


def test_heldout_label_does_not_affect_its_own_prediction():
    rng = np.random.default_rng(245)
    x = rng.normal(size=(40, 4))
    y = np.tile([0, 1], 20)
    folds = np.repeat(np.arange(4), 10)
    changed = y.copy()
    changed[folds == 0] = 1 - changed[folds == 0]
    for kind in ("linear", "rbf"):
        first = heldout_scores(x, y, folds, kind)
        second = heldout_scores(x, changed, folds, kind)
        np.testing.assert_array_equal(first[folds == 0], second[folds == 0])


def test_linear_kernel_solution_matches_independent_weighted_primal_ridge():
    rng = np.random.default_rng(55)
    x = rng.normal(size=(45, 4))
    y = np.r_[np.zeros(30), np.ones(15)]
    folds = np.arange(45) % 3
    actual = heldout_scores(x, y, folds, "linear")
    design = np.c_[x / np.sqrt(x.shape[1]), np.ones(len(x))]
    for fold in range(3):
        train, test = folds != fold, folds == fold
        w = np.array([1 / (2 * sum(y[train] == label)) for label in y[train]])
        xt = design[train]
        coefficient = np.linalg.solve(
            xt.T @ (w[:, None] * xt) + RIDGE * np.eye(5), xt.T @ (w * (2 * y[train] - 1))
        )
        np.testing.assert_allclose(actual[test], design[test] @ coefficient, atol=2e-14)


def test_class_imbalance_does_not_inflate_constant_predictor():
    result = metrics([0] * 100 + [1] * 10, [-1] * 110)
    assert result["balanced_accuracy"] == result["auc"] == 0.5


def test_spread_measures_dispersion_separately_from_location():
    x = np.random.default_rng(198).normal(size=(50, 4))
    result = spread(x, x * 0.5 + 100)
    assert result["generated_to_original_variance_ratio"] == pytest.approx(0.25)


def test_rejects_single_class_test_fold_and_invalid_pca():
    with pytest.raises(ValueError, match="both classes"):
        heldout_scores(np.ones((4, 2)), [0, 0, 1, 1], [0, 0, 1, 1], "rbf")
    with pytest.raises(ValueError, match="positive variance"):
        pca_fit(np.ones((4, 2)), np.full(4, 0.25))
