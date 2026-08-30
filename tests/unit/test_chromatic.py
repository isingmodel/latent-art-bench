import numpy as np
import pytest

from latent_art_bench.features.chromatic import (
    adjacent_chromatic_distances,
    chromatic_summary,
    srgb_to_cielab,
)


def test_srgb_reference_colors() -> None:
    colors = np.array([[[255, 255, 255], [0, 0, 0], [255, 0, 0]]], dtype=np.uint8)
    lab = srgb_to_cielab(colors)[0]
    assert lab[0] == pytest.approx([100.0, 0.0, 0.0], abs=2e-4)
    assert lab[1] == pytest.approx([0.0, 0.0, 0.0], abs=2e-4)
    assert lab[2] == pytest.approx([53.2408, 80.0925, 67.2032], abs=2e-3)


def test_adjacent_pair_count_excludes_diagonals_and_wraparound() -> None:
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    distances = adjacent_chromatic_distances(image)
    assert distances.shape == (2 * (3 - 1) + (2 - 1) * 3,)
    assert np.all(distances == 0)


def test_seamlessness_source_reference_behaviors(pilot_config) -> None:
    config = pilot_config.measurements.chromatic
    delta = chromatic_summary(np.full(1000, 5.0), config)
    assert delta["scalars"]["seamlessness"] == pytest.approx(-1.0)

    rng = np.random.default_rng(8204430)
    exponential = chromatic_summary(rng.exponential(scale=4.0, size=200_000), config)
    assert exponential["scalars"]["seamlessness"] == pytest.approx(0.0, abs=0.01)

    heavy_tail = chromatic_summary(np.concatenate((np.zeros(999), np.array([1000.0]))), config)
    assert heavy_tail["scalars"]["seamlessness"] > 0.9


def test_normalization_and_seamlessness_are_scale_invariant(pilot_config) -> None:
    config = pilot_config.measurements.chromatic
    distances = np.array([0.2, 0.5, 1.0, 2.5, 10.0])
    first = chromatic_summary(distances, config)
    second = chromatic_summary(distances * 37.0, config)
    assert first["scalars"]["seamlessness"] == pytest.approx(
        second["scalars"]["seamlessness"], abs=1e-12
    )
    assert first["vector"] == pytest.approx(second["vector"], abs=1e-12)
    assert sum(first["vector"]) == pytest.approx(1.0)


def test_solid_image_uses_documented_degenerate_limit(pilot_config) -> None:
    config = pilot_config.measurements.chromatic
    summary = chromatic_summary(np.zeros(100), config)
    assert summary["degenerate"] is True
    assert summary["scalars"]["coefficient_of_variation"] == 0.0
    assert summary["scalars"]["seamlessness"] == -1.0
    assert summary["vector"][0] == 1.0
