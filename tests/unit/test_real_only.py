import pytest

from latent_art_bench.evaluation.real_only import _balanced_accuracy, _source_behavior


def test_balanced_accuracy_weights_classes_equally() -> None:
    expected = ["large", "large", "large", "small"]
    predicted = ["large", "large", "large", "large"]
    assert _balanced_accuracy(expected, predicted) == pytest.approx(0.5)


def test_frozen_source_behavior_is_recovered(pilot_config) -> None:
    recovered, metrics = _source_behavior(pilot_config)
    assert recovered is True
    assert metrics["delta_seamlessness"] == pytest.approx(-1.0)
    assert metrics["heavy_tail_seamlessness"] > 0.9
