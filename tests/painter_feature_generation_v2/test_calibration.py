import numpy as np

from latent_art_bench.painter_feature_generation_v2 import calibration, statistics


def test_aggregate_state_counts_match_frozen_materialized_block_estimator():
    rng = np.random.default_rng(74)
    real, generated = rng.normal(size=(13, 3)), rng.normal(size=(8, 16, 3))
    terms = statistics.energy_terms(real, generated)
    indices = rng.integers(0, 8, size=25)
    aggregate = np.bincount(indices, minlength=8)
    point = calibration.evaluate_counts(
        terms.cross_by_block[None],
        np.array([terms.real_self]),
        terms.generated_block_pairs[None],
        aggregate,
        25,
    )[0, 0]
    expected = statistics.energy_terms(real, generated[indices]).evaluate()[0]
    np.testing.assert_allclose(point, expected, atol=1e-12)


def test_calibration_exact_truth_and_scope():
    result = calibration.simulate(trials=2, bootstrap_draws=99, seed=1)
    assert len(result["scenarios"]) == 3
    null = result["scenarios"][0]
    assert len(null["endpoint_truth_and_mc_bias"]) == 60
    np.testing.assert_allclose(
        [r["truth"] for r in null["endpoint_truth_and_mc_bias"]], 0, atol=1e-12
    )
    assert null["zero_variance_endpoint_counts"] == [48]
    assert "synthetic" in result["scope"]
