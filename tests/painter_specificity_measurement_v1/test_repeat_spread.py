"""An algebraic oracle separates repeat spread from centered artist geometry."""

import numpy as np

from latent_art_bench.painter_specificity_measurement_v1.report import artist_diagnostics


def test_shared_repeat_changes_do_not_become_artist_geometry_error():
    artist_means = np.array([[-3.0, 0], [-1.0, 0], [1.0, 0], [3.0, 0]])
    references = [a + np.array([[-1.0, 0], [0.0, 0], [1.0, 0]]) for a in artist_means]
    scenes = np.array([[0.0, 0], [10.0, -3], [-7.0, 4]])
    repeats = np.array([[2.0, -1], [-2.0, 1]])
    named = 2 * artist_means + scenes[:, None, None] + repeats[None, :, None]
    observed = artist_diagnostics(named, references)
    # Each pair differs by (4, -2), hence sample variance trace 10. Reference
    # trace is 1. Artist contrasts are doubled: squared normalized error is 1,
    # apportioned as 9/20, 1/20, 1/20, 9/20 regardless of shared scene/repeat shifts.
    np.testing.assert_allclose([v["within_scene_trace"] for v in observed], 10)
    np.testing.assert_allclose([v["within_reference_trace_ratio"] for v in observed], 10)
    np.testing.assert_allclose(
        [v["geometry_error_contribution"] for v in observed], [.45, .05, .05, .45]
    )
    assert [v["complete_repeat_scenes"] for v in observed] == [3] * 4
