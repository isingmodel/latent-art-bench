import numpy as np
import pytest

from latent_art_bench.painter_request_timing_v1 import cross_validate, paired_arrays, summarize


def test_true_linear_drift_predicts_held_out_scenes_and_repeat_swap_invariance():
    rng = np.random.default_rng(17)
    gaps = rng.uniform(-10, 10, (14, 6))
    drift = np.array([0.25, -0.1, 0.03])
    # Differencing arbitrary stable cell means recovers the same temporal change.
    fixed_cells = rng.normal(size=(14, 6, 3)) * 100
    repeat_0 = fixed_cells
    repeat_1 = fixed_cells + gaps[..., None] * drift
    differences = repeat_1 - repeat_0
    result = summarize(gaps, differences)
    assert result["predictive_gain_fraction"] == pytest.approx(1)
    assert result["slope_iqr_per_minute"] == pytest.approx(drift)
    assert result["scene_deletion_gain_range"] == pytest.approx([1, 1])
    swap = rng.choice([-1, 1], size=gaps.shape)
    swapped = summarize(gaps * swap, differences * swap[..., None])
    assert swapped["slope_iqr_per_minute"] == pytest.approx(drift)
    assert swapped["mse_held_out"] == pytest.approx(result["mse_held_out"])


def test_scene_specific_drift_does_not_imply_transfer():
    gaps = np.ones((14, 6))
    differences = np.zeros((14, 6, 2))
    differences[:, :, 0] = np.tile([1, -1], 7)[:, None]
    # In-sample global slope is zero; leave-one-out fitting overpredicts opposite drift.
    result = cross_validate(gaps, differences)
    assert result["predictive_gain_fraction"] < 0


def test_incomplete_attempt_census_is_rejected():
    with pytest.raises(ValueError, match="complete attempt"):
        paired_arrays([], [], [], {})


def test_invalid_time_design_is_rejected():
    with pytest.raises(ValueError, match="positive time variation"):
        cross_validate(np.zeros((14, 6)), np.ones((14, 6, 31)))
