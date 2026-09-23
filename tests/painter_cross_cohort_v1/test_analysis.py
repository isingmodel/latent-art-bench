"""Constructed arithmetic oracles only; never load empirical feature files."""

import itertools

import numpy as np
import pytest

from latent_art_bench import painter_cross_cohort_v1 as a


def oracle_u(x):
    return np.mean(
        [np.sum(x[i] * x[j], axis=-1) for i in range(len(x)) for j in range(len(x)) if i != j],
        axis=0,
    )


@pytest.mark.parametrize("shape", [(2, 7), (3, 4, 7), (25, 16, 4, 31)])
def test_u_matches_ordered_pair_oracle(shape):
    values = np.random.default_rng(5).normal(size=shape)
    np.testing.assert_allclose(a.u_product(values), oracle_u(values), atol=3e-15)


def test_two_repeats_is_original_cross_product():
    x = np.array([[2.0, -3, 7], [-4, 5, -2]])
    assert a.u_product(x) == pytest.approx(-37)
    assert a.u_product(x) == pytest.approx(x[0] @ x[1])


@pytest.mark.parametrize(
    "x", [np.ones((1, 3)), np.ones(4), np.empty((3, 0)), np.array([[1.0, 2], [3, np.nan]])]
)
def test_u_rejects_invalid_inputs(x):
    with pytest.raises(ValueError):
        a.u_product(x)


def example(k=5, scenes=3):
    z = np.zeros((k, scenes, 5, 31))
    means = np.zeros((4, 31))
    means[:, 0] = [-3, -1, 1, 3]
    return z, means


def test_common_only_response_and_all_delete_one_records():
    z, means = example(25)
    z[:, :, 1:, 0] = 2
    result = a.summarize(z, means)
    for family in ("all31", "color"):
        p = result["families"][family]["pooled"]
        assert [p[k] for k in ("C", "L", "N", "T", "common_fraction", "beta", "D")] == [
            16,
            0,
            16,
            16,
            1,
            0,
            1,
        ]
    assert [r["block"] for r in result["leave_one_block_out"]] == list(range(25))
    assert result["sensitivity_ranges"]["all31"]["pooled"]["C"] == dict(
        minimum=16, maximum=16, available=25, unavailable_blocks=[]
    )


def test_perfect_centered_response_is_not_common_majority():
    z, means = example()
    z[:, :, 1:] = means
    result = a.summarize(z, means)["families"]["all31"]
    p = result["pooled"]
    assert [p[k] for k in ("C", "L", "N", "T", "common_fraction", "beta", "D")] == [
        0,
        20,
        20,
        -20,
        0,
        1,
        0,
    ]
    assert not p["common_majority_descriptive"]
    assert all(r["aligned_amplitude"] == 1 and r["scene_D"] == 0 for r in result["pairs"])


def test_common_noise_cancels_only_where_pairing_requires():
    z, means = example(5)
    noise = np.array([-2, -1, 0, 1, 2])
    # All five arms share this nuisance: it cancels exactly in every difference.
    z[:, :, :, 0] = noise[:, None, None]
    first = a.summarize(z, means)["families"]["all31"]["pooled"]
    assert first["N"] == first["C"] == first["L"] == 0
    # A common named-arm perturbation must survive and can give negative U.
    z[:, :, 1:, 0] += noise[:, None, None]
    p = a.summarize(z, means)["families"]["all31"]["pooled"]
    assert p["C"] == p["N"] == -2
    assert p["L"] == 0
    assert p["common_fraction"] is None
    assert p["common_fraction_reason"] == "nonpositive_total_naming_change"


def test_negative_centered_estimate_can_yield_fraction_above_one():
    z, means = example(4)
    z[:, :, 1:, 0] = 2
    z[:, :, 1:, 1] = np.array([1, -1, 1, -1])[:, None, None] * np.array([-1, -1, 1, 1])
    p = a.summarize(z, means)["families"]["all31"]["pooled"]
    assert p["L"] == pytest.approx(-4 / 3)
    assert p["common_fraction"] > 1
    assert p["N"] == pytest.approx(p["C"] + p["L"])


def test_scene_average_before_square_is_distinct_from_within_scene():
    z, means = example(5, 2)
    z[:, 0, 1:, 0] = 2
    z[:, 1, 1:, 0] = -2
    z[:, 0, 1:, 1] = [-3, -1, 1, 3]
    z[:, 1, 1:, 1] = [3, 1, -1, -3]
    family = a.summarize(z, means)["families"]["all31"]
    assert family["pooled"]["C"] == 0
    assert family["within_scene"]["C"] == 16
    assert family["pooled"]["D"] == 1
    assert family["within_scene"]["D"] == 2
    assert family["scene_minus_pooled_D"] == 1


def test_general_identities_pairs_and_own_family_denominators():
    rng = np.random.default_rng(22)
    z, means = rng.normal(size=(5, 3, 5, 31)), rng.normal(size=(4, 31))
    result = a.summarize(z, means)
    for name, section in a.VIEWS.items():
        family = result["families"][name]
        r = means[:, section] - means[:, section].mean(axis=0)
        h = np.square(r).sum()
        p, w = family["pooled"], family["within_scene"]
        assert p["H"] == pytest.approx(h)
        assert p["N"] == pytest.approx(p["C"] + p["L"])
        assert p["D"] == pytest.approx(p["L"] / h - 2 * p["beta"] + 1)
        assert w["D"] == pytest.approx(w["L"] / h - 2 * w["beta"] + 1)
        for row, (i, j) in zip(family["pairs"], itertools.combinations(range(4), 2)):
            q = means[i, section] - means[j, section]
            g = z[:, :, i + 1, section] - z[:, :, j + 1, section]
            assert row["painters"] == [a.ARTISTS[i], a.ARTISTS[j]]
            assert row["aligned_amplitude"] == pytest.approx(g.mean(axis=(0, 1)) @ q / (q @ q))
            assert row["scene_D"] == pytest.approx(oracle_u(g - q).mean() / (q @ q))
    assert result["families"]["all31"]["pooled"]["C"] == pytest.approx(
        sum(result["families"][name]["pooled"]["C"] for name in ("color", "spatial", "texture"))
    )


def test_zero_family_and_pair_denominators_are_explicitly_unavailable():
    z, means = example()
    means[1] = means[0]
    result = a.summarize(z, means)
    all31 = result["families"]["all31"]
    assert all31["pairs"][0]["scene_D"] is None
    assert all31["pairs"][0]["reason"] == "zero_reference_pair_distance"
    assert all31["pairs"][1]["scene_D"] is not None
    p = result["families"]["texture"]["pooled"]
    assert p["beta"] is p["D"] is None
    assert p["alignment_reason"] == "zero_reference_energy"
    ranges = result["sensitivity_ranges"]["texture"]["pooled"]["D"]
    assert ranges == dict(
        minimum=None, maximum=None, available=0, unavailable_blocks=list(range(5))
    )


def test_deletion_results_are_all_recomputed_on_retained_blocks():
    rng = np.random.default_rng(54)
    z, means = rng.normal(size=(5, 2, 5, 31)), rng.normal(size=(4, 31))
    result = a.summarize(z, means)
    for row in result["leave_one_block_out"]:
        expected = a.summarize(np.delete(z, row["block"], axis=0), means)["families"]
        assert row["families"] == expected


@pytest.mark.parametrize("shape", [(2, 3, 5, 31), (3, 0, 5, 31), (3, 2, 4, 31), (3, 2, 5, 30)])
def test_summary_rejects_wrong_census_shape(shape):
    with pytest.raises(ValueError):
        a.summarize(np.zeros(shape), np.zeros((4, 31)))


def test_summary_rejects_nonfinite_and_wrong_references():
    z, means = example()
    with pytest.raises(ValueError):
        a.summarize(z, means[:3])
    z[0, 0, 0, 0] = np.inf
    with pytest.raises(ValueError):
        a.summarize(z, means)
