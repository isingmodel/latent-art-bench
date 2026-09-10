"""Synthetic mathematics and provenance checks; no new images or real-data run."""

import copy
import itertools
import json
import subprocess

import numpy as np
import pytest
from scipy.spatial.distance import cdist

from latent_art_bench.painter_clause_validation_v1 import precision
from latent_art_bench.painter_distribution_study_v1.inference import paired_contributions
from latent_art_bench.painter_prompt_study_v1.randomization import holm


@pytest.fixture
def proxy_inputs():
    rng = np.random.default_rng(29)
    reference, cells = {}, {}
    for painter, count in zip(precision.PAINTERS, (38, 32)):
        reference[painter] = dict(
            ids=[f"{painter}/{i}" for i in range(count)],
            values=rng.normal(size=(count, 31)).tolist(),
        )
        cells[painter] = dict(
            scene_ids=[f"{c}{i:02d}" for c in precision.CLASSES for i in range(1, 9)],
            classes=[c for c in precision.CLASSES for _ in range(8)],
            repeat_ids=[0, 1, 2],
            free=rng.normal(size=(24, 3, 31)).tolist(),
            named=rng.normal(size=(24, 3, 31)).tolist(),
        )
    return dict(
        schema="painter-naming-geometry-inputs/1",
        original=dict(primary512=dict(oauth_gpt_image_2=cells)),
        reference=dict(primary512=reference),
        targets=copy.deepcopy(precision.TARGETS),
    )


def _direct_energy(reference, generated, weights):
    return (
        2 * cdist(reference, generated).mean(axis=0) @ weights
        - cdist(reference, reference).mean()
        - weights @ cdist(generated, generated) @ weights
    )


def test_prespecified_design_constants():
    assert precision.ALLOCATIONS == ((12, 3), (24, 3), (24, 4))
    assert (precision.PROXY_TRIALS, precision.PROXY_SEED) == (250, 120260910)
    assert (precision.NULL_TRIALS, precision.NULL_DRAWS, precision.NULL_SEED) == (
        5000,
        999,
        120260911,
    )
    assert precision.PRIMARY_DRAWS == 99999
    assert precision.NULL_UPPER_LIMIT == 0.065


def test_proxy_preserves_original_rng_order_and_exact_computation(proxy_inputs):
    """Independent spelling of the original calculation, with synthetic inputs."""
    old = [
        proxy_inputs["original"]["primary512"]["oauth_gpt_image_2"][p] for p in precision.PAINTERS
    ]
    f, n = np.array([v["free"] for v in old]), np.array([v["named"] for v in old])
    classes = np.array(old[0]["classes"])
    refs = [
        np.array(proxy_inputs["reference"]["primary512"][p]["values"]) for p in precision.PAINTERS
    ]
    pooled = f.transpose(1, 0, 2, 3).reshape(24, 6, 31)
    fm, nm = pooled.mean(1), n.mean(2)
    fr = (pooled - fm[:, None, :]) * np.sqrt(6 / 5)
    nr = (n - nm[:, :, None, :]) * np.sqrt(3 / 2)
    gn = nr.transpose(1, 0, 2, 3).reshape(24, 6, 31)
    rng = np.random.default_rng(precision.PROXY_SEED)
    subset = np.sort(
        np.concatenate(
            [rng.choice(np.where(classes == c)[0], 4, replace=False) for c in precision.CLASSES]
        )
    )
    expected = []
    for j, r in ((12, 3), (24, 3), (24, 4)):
        selected = subset if j == 12 else np.arange(24)
        cl = classes[selected]
        weights = [
            np.repeat([proxy_inputs["targets"][p][c] / np.sum(cl == c) / r for c in cl], r)
            for p in precision.PAINTERS
        ]

        def draw(mean, residual):
            indexes = rng.integers(0, residual.shape[1], size=(j, r))
            return mean[:, None, :] + residual[np.arange(j)[:, None], indexes]

        for alpha in (0.0, 0.5, 1.0):
            for noise in ("free", "named", "free_x1.5"):
                residual = {"free": fr, "named": gn, "free_x1.5": fr * 1.5}[noise][selected]
                gm = ((1 - alpha) * fm + alpha * nm.mean(0))[selected]
                estimates = []
                for _ in range(3):
                    generic = draw(gm, residual)
                    named = [draw(nm[k, selected], nr[k, selected]) for k in range(2)]
                    estimates.append(
                        [
                            _direct_energy(refs[k], named[k].reshape(-1, 31), weights[k])
                            - _direct_energy(refs[k], generic.reshape(-1, 31), weights[k])
                            for k in range(2)
                        ]
                    )
                estimates = np.array(estimates)
                expected.append((estimates.mean(0), estimates.std(axis=0, ddof=1)))
    result = precision.compute(proxy_inputs, trials=3)
    assert result["selected12"] == [
        "built01",
        "built05",
        "built06",
        "built07",
        "land03",
        "land06",
        "land07",
        "land08",
        "water03",
        "water04",
        "water06",
        "water07",
    ]
    assert len(result["records"]) == 27
    for row, (mean, sd) in zip(result["records"], expected):
        np.testing.assert_allclose(row["mean"], mean, rtol=0, atol=2e-14)
        np.testing.assert_allclose(row["sd"], sd, rtol=0, atol=2e-14)
    assert result["observed_new_generic_outcomes"] == 0
    assert result["generic_shared_between_endpoints"] is True


def test_generic_cloud_is_shared_for_both_endpoints(proxy_inputs, monkeypatch):
    seen = []

    def energy(reference, generated, weights):
        seen.append(generated)
        return float(np.sum(generated))

    monkeypatch.setattr(precision, "_energy_without_reference_self", energy)
    precision.compute(proxy_inputs, trials=2)
    assert len(seen) == 27 * 2 * 4
    for first, generic_monet, second, generic_cezanne in zip(*[iter(seen)] * 4):
        assert generic_monet is generic_cezanne
        assert first is not second and first is not generic_monet and second is not generic_monet


def test_noiseless_proxy_has_no_simulation_variance(proxy_inputs):
    for cell in proxy_inputs["original"]["primary512"]["oauth_gpt_image_2"].values():
        for arm in ("free", "named"):
            x = np.asarray(cell[arm])
            # Exact powers of two remove residual rounding in the empirical mean.
            cell[arm] = np.repeat(np.round(x[:, :1, :]) * 0.5, 3, axis=1).tolist()
    cells = proxy_inputs["original"]["primary512"]["oauth_gpt_image_2"]
    cells["paul_cezanne"]["free"] = copy.deepcopy(cells["claude_monet"]["free"])
    result = precision.compute(proxy_inputs, trials=2)
    for row in result["records"]:
        assert row["sd"] == [0.0, 0.0]
        assert row["endpoint_correlation"] is None


@pytest.mark.parametrize(
    "problem",
    ["nan", "complex", "bool", "order", "classes", "weights", "references", "schema", "repeats"],
)
def test_proxy_rejects_invalid_or_changed_contract(proxy_inputs, problem):
    cell = proxy_inputs["original"]["primary512"]["oauth_gpt_image_2"]["claude_monet"]
    if problem in ("nan", "complex", "bool"):
        cell["free"] = np.full((24, 3, 31), {"nan": np.nan, "complex": 1j, "bool": True}[problem])
    elif problem == "order":
        cell["scene_ids"][0:2] = cell["scene_ids"][1::-1]
    elif problem == "classes":
        cell["classes"][0] = "land"
    elif problem == "weights":
        proxy_inputs["targets"]["claude_monet"]["built"] = 0.3
    elif problem == "references":
        proxy_inputs["reference"]["primary512"]["claude_monet"]["ids"][0] = proxy_inputs[
            "reference"
        ]["primary512"]["claude_monet"]["ids"][1]
    elif problem == "schema":
        proxy_inputs["schema"] = "future-generic-outcomes/1"
    else:
        cell["repeat_ids"] = [1, 2, 3]
    with pytest.raises(ValueError):
        precision.compute(proxy_inputs, trials=2)


def test_centered_residual_sampling_calibrates_covariance():
    rng = np.random.default_rng(123)
    sample = np.array([[[-2.0, 1.0], [1.0, -3.0], [4.0, 2.0]]])
    mean = sample.mean(1)
    residual = (sample - mean[:, None, :]) * np.sqrt(3 / 2)
    drawn = precision._draw_residuals(rng, mean, residual, 100000)[0]
    np.testing.assert_allclose(drawn.mean(0), mean[0], atol=0.025)
    np.testing.assert_allclose(np.cov(drawn.T), np.cov(sample[0].T), atol=0.07)


def test_weighted_energy_coefficients_match_frozen_primitive_and_all_swaps():
    rng = np.random.default_rng(183)
    reference, generic, named = (
        rng.normal(size=(5, 4)),
        rng.normal(size=(3, 4)),
        rng.normal(size=(3, 4)),
    )
    weights = np.array([0.1, 0.3, 0.6])
    coefficients = precision._pair_coefficients(reference, generic, named, weights)
    np.testing.assert_allclose(
        coefficients,
        paired_contributions(reference, generic, named, pair_weights=weights),
        rtol=0,
        atol=2e-15,
    )
    for bits in itertools.product((False, True), repeat=3):
        swapped = np.array(bits)[:, None]
        g, n = np.where(swapped, named, generic), np.where(swapped, generic, named)
        direct = _direct_energy(reference, n, weights) - _direct_energy(reference, g, weights)
        assert direct == pytest.approx((1 - 2 * np.array(bits)) @ coefficients, abs=3e-15)


def test_four_position_conditioning_exact_identity_and_uniform_remaining_pairs():
    """Enumerate 24^2 actual assignments, grouped by other-arm positions."""
    rng = np.random.default_rng(823)
    outcomes, reference, weights = (
        rng.normal(size=(2, 4, 3)),
        rng.normal(size=(4, 3)),
        np.array([0.3, 0.7]),
    )
    groups = {}
    for assignment in itertools.product(itertools.permutations(range(4)), repeat=2):
        positions = np.array(assignment)
        # Conditional M-vs-G: fix F and C positions in each block.
        key = tuple(positions[:, [0, 3]].ravel())
        assigned = outcomes[np.arange(2)[:, None], positions]
        groups.setdefault(key, []).append((assigned[:, 1], assigned[:, 2]))
    assert len(groups) == 12**2
    for pairs in groups.values():
        assert len(pairs) == 4  # exactly 2^2 equally likely remaining orientations
        generic, named = pairs[0]
        coefficients = precision._pair_coefficients(reference, generic, named, weights)
        actual = sorted(
            _direct_energy(reference, n, weights) - _direct_energy(reference, g, weights)
            for g, n in pairs
        )
        sign = sorted(np.array(s) @ coefficients for s in itertools.product((-1, 1), repeat=2))
        np.testing.assert_allclose(actual, sign, rtol=0, atol=3e-15)


def test_monte_carlo_plus_one_conservative_ties_and_small_exact_tail():
    assert np.array_equal(
        precision._monte_carlo_pvalues(np.zeros((2, 3)), np.random.default_rng(1), 999), [1.0, 1.0]
    )
    coefficients = np.array([[1.0, 1.0, 1.0], [1.0, -1.0, 1.0]])
    p = precision._monte_carlo_pvalues(coefficients, np.random.default_rng(32), 99999)
    assert p[0] == pytest.approx(0.25, abs=0.006)
    assert p[1] == 1.0
    assert np.all(p * 100000 == np.round(p * 100000))


@pytest.mark.parametrize(
    "pvalues", [[0.01, 0.04], [0.03, 0.2], [0.0, 1.0], [0.04, 0.04], [0.8, 0.02]]
)
def test_holm_matches_existing_primary_procedure(pvalues):
    assert np.array_equal(precision._holm2(pvalues), holm(pvalues))


def test_artificial_complete_grid_qualification_deterministic_and_partial_nulls():
    first = precision.randomization_qualification(trials=8, draws=31, seed=77)
    assert first == precision.randomization_qualification(trials=8, draws=31, seed=77)
    assert first["blocks"] == 72 and first["positions_per_block"] == 4
    assert first["generic_shared_between_endpoints"] is True
    assert first["service_assumptions_qualified"] is False
    assert [row["true_nulls"] for row in first["cases"]] == [
        [True, True],
        [True, True],
        [True, True],
        [True, False],
        [False, True],
    ]
    for row in first["cases"]:
        assert 0 <= row["true_null_family_rejections"] <= 8
        assert row["wilson_95"][1] > 0.065  # deliberately too few trials to qualify
    assert first["qualified"] is False


@pytest.mark.parametrize(
    "kwargs", [dict(trials=True), dict(trials=0), dict(draws=0), dict(seed=-1), dict(seed=1.5)]
)
def test_randomization_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        precision.randomization_qualification(**kwargs)


def test_wilson_known_interval():
    np.testing.assert_allclose(precision._wilson(250, 5000), [0.044297, 0.056394], atol=1e-6)


@pytest.fixture
def committed_repo(tmp_path):
    for args in (
        ["init", "-q"],
        ["config", "user.email", "test@example.invalid"],
        ["config", "user.name", "Offline Test"],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True)
    path = tmp_path / "source.txt"
    path.write_text("original\n")
    subprocess.run(["git", "add", "source.txt"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "source"], cwd=tmp_path, check=True)
    return tmp_path


def test_source_binding_rejects_working_staged_untracked_and_symlink(committed_repo):
    root = committed_repo
    path = root / "source.txt"
    commit, bindings = precision._bindings_at_head(root, {path.relative_to(root)})
    assert len(commit) == 40 and bindings[0]["path"] == "source.txt"
    path.write_text("changed\n")
    with pytest.raises(ValueError, match="commit source/input"):
        precision._bindings_at_head(root, {path.relative_to(root)})
    subprocess.run(["git", "add", "source.txt"], cwd=root, check=True)
    path.write_text("original\n")  # working tree equals HEAD, index still differs
    with pytest.raises(ValueError, match="commit source/input"):
        precision._bindings_at_head(root, {path.relative_to(root)})
    untracked = root / "untracked.txt"
    untracked.write_text("original\n")
    with pytest.raises(ValueError, match="commit source/input"):
        precision._bindings_at_head(root, {untracked.relative_to(root)})
    linked = root / "linked.txt"
    linked.symlink_to(path.name)
    with pytest.raises(ValueError, match="symlink"):
        precision._bindings_at_head(root, {linked.relative_to(root)})


def test_final_build_refuses_existing_output_before_calculation(tmp_path, monkeypatch):
    output = tmp_path / precision.OUTPUT_DIRECTORY / "precision.json"
    output.parent.mkdir(parents=True)
    output.write_text("retained evidence\n")

    def forbidden(*args, **kwargs):
        pytest.fail("should refuse existing outputs before calculating or binding")

    monkeypatch.setattr(precision, "_bindings_at_head", forbidden)
    with pytest.raises(ValueError, match="create-once"):
        precision.build(tmp_path)
    assert output.read_text() == "retained evidence\n"


def test_build_binds_source_before_compute_rechecks_and_writes_once(tmp_path, monkeypatch):
    path = tmp_path / precision.INPUT_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    calls = []

    def bindings(root, paths):
        calls.append("bindings")
        assert precision.SOURCE_PATH in paths and precision.TEST_PATH in paths
        return "a" * 40, []

    def compute(inputs):
        calls.append("compute")
        assert calls == ["bindings", "compute"]
        return {"fake": True}

    monkeypatch.setattr(precision, "_bindings_at_head", bindings)
    monkeypatch.setattr(precision, "compute", compute)
    monkeypatch.setattr(precision, "randomization_qualification", lambda: {"qualified": False})
    monkeypatch.setattr(precision, "report", lambda value: "artificial report\n")
    result = precision.build(tmp_path)
    assert calls == ["bindings", "compute", "bindings"]
    assert result["randomization_qualification"]["qualified"] is False
    output = tmp_path / precision.OUTPUT_DIRECTORY / "precision.json"
    assert json.loads(output.read_text()) == result
    with pytest.raises(ValueError, match="create-once"):
        precision.build(tmp_path)


def test_build_detects_source_change_during_calculation(tmp_path, monkeypatch):
    path = tmp_path / precision.INPUT_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    commits = iter([("a" * 40, []), ("b" * 40, [])])
    monkeypatch.setattr(precision, "_bindings_at_head", lambda root, paths: next(commits))
    monkeypatch.setattr(precision, "compute", lambda inputs: {})
    monkeypatch.setattr(precision, "randomization_qualification", lambda: {})
    with pytest.raises(ValueError, match="changed during"):
        precision.build(tmp_path)
    assert not (tmp_path / precision.OUTPUT_DIRECTORY / "precision.json").exists()
