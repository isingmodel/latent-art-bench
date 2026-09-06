import numpy as np
import pytest

from latent_art_bench.painter_distribution_study_v1.statistics import (
    content_weights,
    disjoint_splits,
    distribution_summary,
    rng_for,
    transfer_fold,
    transfer_scores,
)
from latent_art_bench.painter_feature_generation_v2.statistics import finite_energy


def test_uniform_energy_matches_existing_definition_and_known_scale_change():
    x = np.arange(1, 22, dtype=float).reshape(7, 3)
    y = x * 0.5 + 30
    result = distribution_summary(x, y)
    assert result["energy_distance"] == pytest.approx(finite_energy(x, y))
    assert result["sample_variance_ratio"] == pytest.approx(0.25)
    assert result["squared_iqr_sum_ratio"] == pytest.approx(0.25)
    assert result["coordinate_iqr_ratios"] == pytest.approx([0.5] * 3)


def test_content_weights_remove_pure_mixture_difference():
    x = np.array([[0.0], [0.0], [0.0], [10.0]])
    y = np.array([[0.0], [10.0], [10.0], [10.0]])
    wx = content_weights(["a", "a", "a", "b"], ["a", "b"])
    wy = content_weights(["a", "b", "b", "b"], ["a", "b"])
    assert distribution_summary(x, y)["energy_distance"] > 0
    weighted = distribution_summary(x, y, wx, wy)
    assert weighted["energy_distance"] == pytest.approx(0, abs=1e-12)
    assert weighted["population_variance_ratio"] == pytest.approx(1)
    assert weighted["sample_variance_ratio"] is None


def test_degenerate_reference_iqr_is_explicitly_undefined():
    result = distribution_summary(np.ones((8, 2)), np.zeros((8, 2)))
    assert result["squared_iqr_sum_ratio"] is None
    assert result["coordinate_iqr_ratios"] == [None, None]


def test_work_subsamples_are_disjoint_reproducible_and_not_bootstrap_duplicates():
    first = disjoint_splits(31, 12, 8, rng_for("seed", "painter"))
    second = disjoint_splits(31, 12, 8, rng_for("seed", "painter"))
    for (a, b), (c, d) in zip(first, second):
        assert not set(a) & set(b)
        assert len(set(a)) == len(set(b)) == 12
        np.testing.assert_array_equal(a, c)
        np.testing.assert_array_equal(b, d)
    with pytest.raises(ValueError, match="disjoint"):
        disjoint_splits(20, 12, 1, rng_for("seed"))


def test_unrepresented_content_cannot_be_silently_reweighted():
    with pytest.raises(ValueError, match="represented"):
        content_weights(["a", "a"], ["a", "b"])


@pytest.mark.parametrize("kind", ["linear", "rbf"])
def test_transfer_prediction_uses_training_only_and_detects_shift(kind):
    rng = rng_for("train-test")
    train = np.r_[rng.normal(-3, 0.2, (20, 3)), rng.normal(3, 0.2, (20, 3))]
    labels = np.r_[np.zeros(20), np.ones(20)]
    test = np.array([[-3, -3, -3], [3, 3, 3]], dtype=float)
    values = transfer_scores(train, labels, test, kind)
    assert values[0] < 0 < values[1]
    np.testing.assert_allclose(values[:1], transfer_scores(train, labels, test[:1], kind))


def test_transfer_holds_out_whole_scene_and_shared_original_work():
    original = [dict(image_id=f"r{i}", domain="original") for i in range(4)]
    generated = [
        dict(image_id=f"g{i}", domain="generated", template_id=f"t{i}", scene_fold=i % 2)
        for i in range(4)
    ]
    target = original + [dict(r, image_id=r["image_id"] + "other") for r in generated]
    folds = {f"r{i}": i % 2 for i in range(4)}
    train, test = transfer_fold(original + generated, target, folds, folds, 0)
    assert train == [1, 3, 5, 7]
    assert test == [0, 2, 4, 6]
    target[4]["template_id"] = "t1"
    with pytest.raises(ValueError, match="scene family"):
        transfer_fold(original + generated, target, folds, folds, 0)
