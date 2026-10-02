"""Constructed-data checks for the third TMLR revision diagnostics."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v3 as diag


def test_distinct_pair_never_repeats_a_work():
    rng = np.random.default_rng(0)
    pool = np.arange(5)
    pairs = [diag.distinct_pair(rng, pool) for _ in range(500)]
    assert all(a != b for a, b in pairs)


def test_agreement_for_exact_and_absent_differences():
    refs = np.eye(4, 3)
    exact = np.broadcast_to(np.vstack([np.zeros(3), np.zeros(3), refs]), (5, 2, 6, 3)).copy()
    beta, error = diag.agreement(exact, refs)
    assert beta == pytest.approx(1) and error == pytest.approx(0)
    none = np.zeros((5, 2, 6, 3))
    beta, error = diag.agreement(none, refs)
    assert beta == pytest.approx(0) and error == pytest.approx(1)


def test_normalized_prototype_share_is_one_without_between_name_differences():
    rng = np.random.default_rng(1)
    prototypes = rng.normal(size=(4, 5))
    units = prototypes / np.linalg.norm(prototypes, axis=1, keepdims=True)
    shift = units.mean(axis=0)
    named = np.tile(shift, (4, 1))
    x = np.broadcast_to(np.vstack([np.zeros(5), np.zeros(5), named]), (3, 2, 6, 5)).copy()
    assert diag.normalized_prototype_share(x, prototypes) == pytest.approx(1)
