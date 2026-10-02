"""Constructed-data checks for the fifth TMLR revision diagnostics."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v5 as diag


def arms(named):
    """Stack zero free/generic arms before named arms: scenes, repeats, 6, features."""
    zeros = np.zeros((*named.shape[:2], 2, named.shape[-1]))
    return np.concatenate([zeros, named], axis=2)


def test_scaled_copy_has_unit_alignment_and_zero_held_out_error():
    rng = np.random.default_rng(5)
    means = rng.normal(size=(4, 6))
    r = means - means.mean(axis=0)
    named = np.broadcast_to(2.5 * r, (8, 2, 4, 6)).copy()
    beta, q, error = diag.scene_metrics(arms(named), means)
    assert diag.alignment(beta, q) == pytest.approx(1)
    assert diag.held_out(beta, q) == pytest.approx(0, abs=1e-12)
    assert error.mean() == pytest.approx((2.5 - 1) ** 2)


def test_split_adds_up_and_orthogonal_noise_is_off_pattern():
    rng = np.random.default_rng(6)
    means = rng.normal(size=(4, 5))
    named = rng.normal(size=(7, 2, 4, 5))
    x = arms(named)
    amp, off = diag.split(x, [np.array([m]) for m in means])
    _, _, error = diag.scene_metrics(x, means)
    assert amp + off == pytest.approx(error.mean())


def test_rho_threshold_and_repeat_noise():
    assert diag.rho_at_one(0.8, 1.0) is None
    assert diag.rho_at_one(1.5, 0.5) == pytest.approx(0.5)
    means = np.eye(4, 3)
    r = means - means.mean(axis=0)
    named = np.stack([np.stack([r, r + 1.0]) for _ in range(3)])
    noise = diag.repeat_noise(arms(named), means)
    # centered difference of the two repeats is zero because the offset is shared by all names
    assert noise == pytest.approx(0)


def test_proximity_shared_term_without_painter_differences():
    rng = np.random.default_rng(7)
    means = rng.normal(size=(4, 5))
    shift = rng.normal(size=5)
    named = np.broadcast_to(shift, (6, 2, 4, 5))
    x = arms(named)
    gain, shared = diag.proximity_terms(x, means)
    assert gain == pytest.approx(shared)


def test_distinct_share_detects_separated_configurations():
    a = np.zeros((3, 2, 6, 4))
    a[:, 1] += 0.01
    b = a + 5.0
    assert diag.distinct_share(a, b) == pytest.approx(1)
    assert diag.distinct_share(a, a + 0.001) == pytest.approx(0)
