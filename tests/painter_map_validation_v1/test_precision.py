"""Artificial arithmetic/provenance checks; never run the formal proxy grid."""

import itertools
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_map_validation_v1 import precision as p


@pytest.fixture
def fixture():
    rng = np.random.default_rng(874)
    free = rng.normal(size=(2, 2, 3))
    named = rng.normal(size=free.shape)
    reference = rng.normal(size=(3, 3))
    fitted = dict(free_mean=[0.2, -0.4, 0.1], named_mean=[0.6, 0.2, -0.3], scale=0.6)
    return free, named, reference, np.array([0.3, 0.7]), fitted


def brute(free, named, reference, w, fitted, draws, deletion=None):
    fs, ns, vw = [], [], []
    qs = []
    a = fitted["scale"]
    fm, nm = np.array(fitted["free_mean"]), np.array(fitted["named_mean"])
    for j, chosen in enumerate(draws):
        chosen = [x for r, x in enumerate(chosen) if deletion != (j, r)]
        f, n = free[j, chosen], named[j, chosen]
        e1, e2 = n - (f + nm - fm), n - (nm + a * (f - fm))
        pairs = [(r, s) for r in range(len(chosen)) for s in range(len(chosen)) if r != s]
        qs.append(w[j] * np.mean([e2[r] @ e2[s] - e1[r] @ e1[s] for r, s in pairs]))
        fs.extend(f)
        ns.extend(n)
        vw.extend([w[j] / len(chosen)] * len(chosen))
    f, vw = np.array(fs), np.array(vw)
    energies = []
    for mapped in (f + nm - fm, nm + a * (f - fm)):
        energies.append(
            2 * np.mean(cdist(reference, mapped) @ vw)
            - vw @ cdist(mapped, mapped) @ vw
            - cdist(reference, reference).mean()
        )
    return np.array([energies[1] - energies[0], sum(qs)])


@pytest.mark.parametrize("repeats", [3, 4, 6, 8])
@pytest.mark.parametrize("scale", [0.4, 1.0, 1.3])
def test_cached_points_all_deletions_and_jackknife_match_direct(fixture, repeats, scale):
    f, n, x, w, fitted = fixture
    fitted = dict(fitted, scale=scale)
    table = p.support_tables(f, n, x, w, fitted)
    draws = np.random.default_rng(327).integers(2, size=(3, 2, repeats))
    result = p.statistics(table, draws)
    for b, chosen in enumerate(draws):
        np.testing.assert_allclose(
            result["estimate"][b], brute(f, n, x, w, fitted, chosen), atol=3e-14
        )
        deleted = np.array(
            [[brute(f, n, x, w, fitted, chosen, (j, r)) for r in range(repeats)] for j in range(2)]
        )
        np.testing.assert_allclose(result["deleted"][b], deleted, atol=4e-14)
        variance = (
            (repeats - 1) / repeats * ((deleted - deleted.mean(1, keepdims=True)) ** 2).sum((0, 1))
        )
        np.testing.assert_allclose(result["variance"][b], variance, atol=4e-14)


@pytest.mark.parametrize("repeats", [3, 4])
def test_exhaustive_tiny_support_truth_and_q_sampling_variance(fixture, repeats):
    table = p.support_tables(*fixture)
    draws = np.array(list(itertools.product(range(2), repeat=2 * repeats))).reshape(-1, 2, repeats)
    observed = p.statistics(table, draws)["estimate"]
    truth = p.exact_truth(table, repeats)
    np.testing.assert_allclose(observed.mean(0), truth["estimate"], atol=3e-14)
    assert observed[:, 1].var() == pytest.approx(truth["q_sampling_variance"], abs=3e-14)


def test_nonuniform_reference_weights_and_finite_r_energy_bias(fixture):
    f, n, x, w, fitted = fixture
    table = p.support_tables(f, n, x, w, fitted, [0.2, 0.3, 0.5])
    pairs = table.distances.reshape(2, 2, 2, 2).mean((1, 3))
    mixture = w @ table.cross.mean(1) + table.contraction * (w @ pairs @ w)
    finite = p.exact_truth(table, 4)["estimate"][0]
    assert finite - mixture == pytest.approx((fitted["scale"] - 1) / 4 * (w**2 @ pairs.diagonal()))


@pytest.mark.parametrize("alpha,sign", [(0, 1), (0.5, 0), (1, -1)])
def test_named_mean_alignment_controls_q_truth(fixture, alpha, sign):
    f, _, x, w, fitted = fixture
    t1, t2 = p.maps(f.mean(1), fitted)
    named = np.repeat(((1 - alpha) * t1 + alpha * t2)[:, None, :], 2, axis=1)
    value = p.exact_truth(p.support_tables(f, named, x, w, fitted), 4)["estimate"][1]
    expected = (1 - 2 * alpha) * (w @ ((t2 - t1) ** 2).sum(1))
    assert value == pytest.approx(expected, abs=1e-14)
    if sign:
        assert value * sign > 0


def test_translation_and_feature_orthogonal_permutation_invariance(fixture):
    f, n, x, w, fitted = fixture
    shift = np.array([2.0, -1.0, 0.3])
    new = dict(
        fitted,
        free_mean=(np.array(fitted["free_mean"]) + shift)[::-1],
        named_mean=(np.array(fitted["named_mean"]) + shift)[::-1],
    )
    first = p.support_tables(*fixture)
    second = p.support_tables(
        (f + shift)[..., ::-1], (n + shift)[..., ::-1], (x + shift)[..., ::-1], w, new
    )
    draws = np.array([[[0, 1, 0, 1], [1, 1, 0, 1]]])
    for key in ("estimate", "variance", "deleted"):
        np.testing.assert_allclose(
            p.statistics(first, draws)[key], p.statistics(second, draws)[key], atol=4e-14
        )


def test_intervals_fixed_bonferroni_critical_values_and_unavailable():
    for r, critical in [(4, 4.176534846104503), (6, 3.1633814497486084), (8, 2.841244248588211)]:
        half, available = p.intervals([[-1, 2], [0, 0]], [[1, 4], [0, 1]], r)
        np.testing.assert_allclose(half[0], [critical, 2 * critical])
        assert available.tolist() == [True, False]
        assert np.isinf(half[1]).all()
    half, available = p.intervals([[1, -2]], [[-0.1, 2]], 4)
    assert not available[0] and np.isinf(half).all()


def test_exact_cp_family_boundary():
    assert p.coverage_lower(9475, 10000) < 0.94 <= p.coverage_lower(9476, 10000)
    assert p.coverage_lower(0, 10000) == 0
    assert p.coverage_lower(10000, 10000) < 1
    with pytest.raises(ValueError):
        p.coverage_lower(10001, 10000)


def decision_grid():
    return [
        dict(
            R=r,
            shape=sh,
            mean=m,
            regime=rg,
            trials=10000,
            coverage_lower=0.95,
            median_half_width=[0.2, 0.8],
        )
        for r in p.REPEATS
        for sh in p.SHAPES
        for m in p.MEANS
        for rg in p.REGIMES
    ]


def test_coverage_all_cells_but_width_only_baseline_and_smallest_selection():
    rows = decision_grid()
    for row in rows:
        if row["regime"] != "baseline":
            row["median_half_width"] = [1000, None]
    assert p.allocation_decision(rows)["selected_R"] == 4
    rows[1]["coverage_lower"] = 0.93
    assert p.allocation_decision(rows)["selected_R"] == 6
    for row in rows:
        if row["R"] == 6 and row["regime"] == "baseline":
            row["median_half_width"][1] = 1.01
    assert p.allocation_decision(rows)["selected_R"] == 8
    rows[-1]["coverage_lower"] = 0.93
    assert p.allocation_decision(rows)["decision"] == "stop_inferential_proposal"
    with pytest.raises(ValueError):
        p.allocation_decision(rows[:-1])


def artificial_proxy():
    rng = np.random.default_rng(194)
    return dict(
        free_mean=rng.normal(size=(12, 31)),
        cov_free=np.diag(np.linspace(0.1, 0.6, 31) ** 2),
        cov_named=np.diag(np.linspace(0.05, 0.3, 31) ** 2),
        scene_weights=np.repeat([3 / 128, 11 / 128, 18 / 128], 4),
        fitted=dict(free_mean=np.zeros(31), named_mean=np.ones(31) * 0.2, scale=0.7),
        reference=rng.normal(size=(32, 31)),
    )


@pytest.mark.parametrize("shape", range(3))
def test_codebooks_and_artificial_regime_supports(shape):
    proxy = artificial_proxy()
    u, v = p.codebook(shape)
    np.testing.assert_allclose(np.vstack([u.mean(0), v.mean(0)]), 0, atol=5e-15)
    np.testing.assert_allclose(np.vstack([(u * u).mean(0), (v * v).mean(0)]), 1, atol=1e-14)
    for regime in range(3):
        table = p.scenario(proxy, shape, 1, regime)
        np.testing.assert_allclose(table.free.mean(1), proxy["free_mean"], atol=1e-14)
        assert p.exact_truth(table, 4)["estimate"][1] == pytest.approx(0, abs=1e-13)
        mult = (1, 2, 0.5)[regime]
        # Weighted total coordinate noise variances remain the prescribed multiplier.
        observed = proxy["scene_weights"] @ table.free.var(1)
        np.testing.assert_allclose(observed, mult**2 * np.diag(proxy["cov_free"]), atol=1e-14)


def test_artificial_small_simulation_reproducible_and_unavailable_counted(fixture):
    table = p.support_tables(*fixture)
    first = p.simulate_cell(table, 4, 20, 881)
    assert first == p.simulate_cell(table, 4, 20, 881)
    f, n, x, w, fitted = fixture
    zero = p.support_tables(
        f, n, x, w, dict(fitted, scale=1, free_mean=[0] * 3, named_mean=[0] * 3)
    )
    result = p.simulate_cell(zero, 4, 20, 881)
    assert result["unavailable"] == 20 and result["joint_covered"] == 0
    assert result["median_half_width"] == [None, None]


@pytest.mark.parametrize("bad", [[0.1, 0.1], [-1, 2], [np.nan, 1], [True, False]])
def test_invalid_weights_rejected(fixture, bad):
    f, n, x, _, fitted = fixture
    with pytest.raises(ValueError):
        p.support_tables(f, n, x, bad, fitted)


def test_invalid_shapes_maps_and_indices_rejected(fixture):
    f, n, x, w, fitted = fixture
    for bad in (0, -1, np.nan, True):
        with pytest.raises(ValueError):
            p.support_tables(f, n, x, w, dict(fitted, scale=bad))
    table = p.support_tables(*fixture)
    for indices in (
        np.zeros((1, 2, 2), dtype=int),
        np.ones((1, 2, 3)) * 0.5,
        np.ones((1, 2, 3), dtype=int) * 2,
        np.zeros((1, 3, 3), dtype=int),
    ):
        with pytest.raises(ValueError):
            p.statistics(table, indices)


def test_only_bound_historical_inputs_loaded():
    root = Path(__file__).resolve().parents[2]
    value = p.load_proxy(root)
    assert value["scene_ids"] == [f"{c}{i:02d}" for c in p.CLASSES for i in range(1, 5)]
    assert value["fitted"]["scale"] == 0.6785365094757265
    np.testing.assert_array_equal(
        value["scene_weights"], np.repeat([3 / 128, 11 / 128, 18 / 128], 4)
    )
    assert value["reference"].shape == (32, 31)


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_clean_source_gate_and_create_once_without_formal_simulation(tmp_path, monkeypatch):
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    bound = Path("source.txt")
    (tmp_path / bound).write_text("one")
    monkeypatch.setattr(p, "BINDINGS", (bound,))
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-m", "artificial")
    monkeypatch.setattr(p, "load_proxy", lambda root: dict(scene_ids=["artificial"]))
    fake = dict(records=[], decision="stop_inferential_proposal", selected_outputs=None)
    calls = []
    monkeypatch.setattr(p, "qualify", lambda proxy: calls.append(True) or fake)
    (tmp_path / bound).write_text("changed")
    with pytest.raises(ValueError, match="commit clean"):
        p.build(tmp_path)
    assert not calls
    (tmp_path / bound).write_text("one")
    value = p.build(tmp_path)
    assert calls == [True]
    assert json.loads((tmp_path / p.OUTPUT_PATH / "precision.json").read_text()) == value
    with pytest.raises(ValueError, match="create-once"):
        p.build(tmp_path)


def test_input_hash_mismatch_rejected_before_parsing(tmp_path):
    path = tmp_path / p.INPUT_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        p.load_proxy(tmp_path)


def test_nonfinite_interval_is_unavailable_but_malformed_input_raises():
    half, available = p.intervals(
        [[np.inf, 0], [1, -1], [np.nan, 2]], [[1, 2], [np.inf, 2], [1, 2]], 4
    )
    assert not available.any() and np.isinf(half).all()
    with pytest.raises(ValueError, match="numeric"):
        p.intervals([["a", "b"]], [[1, 2]], 4)


def test_nonfinite_trial_counts_as_miss_without_trimming(fixture, monkeypatch):
    table = p.support_tables(*fixture)

    def failed(table, draws):
        b = len(draws)
        return dict(estimate=np.full((b, 2), np.inf), variance=np.ones((b, 2)))

    monkeypatch.setattr(p, "statistics", failed)
    value = p.simulate_cell(table, 4, 3, 22)
    assert value["joint_covered"] == 0 and value["unavailable"] == 3
    assert value["empirical_mean"] is None and value["nonfinite_estimate_trials"] == 3
    json.dumps(value, allow_nan=False)


def test_correlated_covariance_preserved_by_artificial_supports():
    proxy = artificial_proxy()
    root = np.eye(31) * 0.2 + np.ones((31, 31)) * 0.05
    proxy["cov_free"] = root @ root.T
    for sh in range(3):
        table = p.scenario(proxy, sh, 0, 0)
        errors = table.free[0] - table.free[0].mean(0)
        np.testing.assert_allclose(
            errors.T @ errors / len(errors), proxy["cov_free"], rtol=1e-12, atol=1e-13
        )
    with pytest.raises(ValueError, match="semidefinite"):
        p.covariance_root([[1, 2], [2, 1]])
    with pytest.raises(ValueError, match="whitened"):
        p.whiten_support(np.ones((64, 31)))


def test_finite_trial_aggregate_overflow_is_not_serialized(fixture, monkeypatch):
    table = p.support_tables(*fixture)

    def extreme(table, draws):
        value = np.full((len(draws), 2), 1e200)
        value[::2] *= -1
        return dict(estimate=value, variance=np.ones_like(value))

    monkeypatch.setattr(p, "statistics", extreme)
    result = p.simulate_cell(table, 4, 4, 22)
    assert result["nonfinite_estimate_trials"] == 0
    assert result["empirical_variance"] is None
    json.dumps(result, allow_nan=False)
    assert p.finite_summary(np.full((4, 2), 1e308)) is None


@pytest.mark.parametrize("bad", [[], [0.2], [0.2, 0.3, 0.4]])
def test_allocation_rejects_missing_or_extra_endpoint_widths(bad):
    rows = decision_grid()
    rows[0]["median_half_width"] = bad
    with pytest.raises(ValueError, match="exactly two"):
        p.allocation_decision(rows)


def test_both_arm_full_covariances_preserved_in_paired_stress():
    proxy = artificial_proxy()
    for arm, strength in [("free", 0.05), ("named", 0.03)]:
        root = np.eye(31) * 0.2 + np.ones((31, 31)) * strength
        proxy[f"cov_{arm}"] = root @ root.T
    for sh in range(3):
        for regime, mult in enumerate((1, 2, 0.5)):
            table = p.scenario(proxy, sh, 1, regime)
            for arm in ("free", "named"):
                values = getattr(table, arm)
                residual = values - values.mean(1, keepdims=True)
                actual = np.einsum("j,jsd,jse->de", table.w, residual, residual) / 64
                np.testing.assert_allclose(
                    actual, mult**2 * proxy[f"cov_{arm}"], rtol=1e-12, atol=1e-12
                )
