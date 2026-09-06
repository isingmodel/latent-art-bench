import itertools

import numpy as np
import pytest

from latent_art_bench.painter_distribution_study_v1 import inference as i
from latent_art_bench.painter_distribution_study_v1.statistics import distribution_summary


def test_weighted_pair_coefficients_match_direct_energy_under_every_swap():
    rng = np.random.default_rng(36)
    real, a, b = rng.normal(size=(7, 5)), rng.normal(size=(4, 5)), rng.normal(size=(4, 5))
    wr = np.arange(1, 8) / 28
    wg = np.array([0.1, 0.2, 0.3, 0.4])
    values = i.paired_contributions(real, a, b, wr, wg)
    for signs in itertools.product((-1, 1), repeat=4):
        swap = np.array(signs) == -1
        first, second = a.copy(), b.copy()
        first[swap], second[swap] = b[swap], a[swap]
        direct = (
            distribution_summary(real, second, wr, wg)["energy_distance"]
            - distribution_summary(real, first, wr, wg)["energy_distance"]
        )
        assert np.dot(signs, values) == pytest.approx(direct, abs=1e-12)


def test_weighted_contrast_rejects_unmatched_data():
    with pytest.raises(ValueError, match="matching"):
        i.paired_contributions(np.ones((8, 3)), np.ones((4, 3)), np.ones((5, 3)))
    with pytest.raises(ValueError, match="probability"):
        i.paired_contributions(
            np.ones((8, 3)), np.ones((4, 3)), np.ones((4, 3)), pair_weights=[1, 1, 1, 1]
        )


def test_qualification_retains_full_null_inventory_and_invalid_control():
    result = i.simulate(32, trials=30)
    assert len(result["null_cells"]) == 24
    assert len(result["hypothetical_sign_bias_power"]) == 3
    assert result["invalid_window_synchronized_assignments"]["invalid_window_signs"]
    assert all(
        r["family_size"] == 8 and not r["invalid_window_signs"] for r in result["null_cells"]
    )
    assert i.simulate(32, trials=30) == result
