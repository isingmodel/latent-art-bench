"""Analytical checks of retrospective naming estimands, not fitted-result snapshots."""

import itertools

import numpy as np
import pytest

from latent_art_bench.painter_specificity_review_v3 import (
    monet_sisley_alignment,
    shared_decomposition,
    summarize_model,
)


def fixed_panel(generic, naming, artists=(-1, -1, 1, 1), scenes=3):
    x = np.zeros((scenes, 2, 6, 1))
    x[:, :, 1, 0] = generic
    x[:, :, 2:, 0] = generic + naming + np.array(artists)
    return x


@pytest.mark.parametrize("generic,naming", [(2, 3), (2, -3), (2, -2), (0, 3)])
def test_exact_generic_naming_interaction_allows_reinforcement_and_cancellation(generic, naming):
    result = shared_decomposition(fixed_panel(generic, naming))
    identity = result["common_shift_identity"]
    assert identity["generic_component"] == pytest.approx(4 * generic**2)
    assert identity["additional_naming_component"] == pytest.approx(4 * naming**2)
    assert identity["signed_interaction"] == pytest.approx(8 * generic * naming)
    assert identity["combined_common"] == pytest.approx(4 * (generic + naming)**2)
    assert identity["scalar_identity_residual"] == pytest.approx(0, abs=1e-13)
    assert identity["vector_identity_max_abs_residual"] == pytest.approx(0, abs=1e-13)
    assert result["named_minus_free"]["specific"] == pytest.approx(4)
    assert result["named_minus_generic"]["specific"] == pytest.approx(4)


def test_shared_fraction_changes_with_baseline_but_specific_component_does_not():
    result = shared_decomposition(fixed_panel(2, 1))
    assert result["named_minus_free"]["shared_fraction"] == pytest.approx(36 / 40)
    assert result["named_minus_generic"]["shared_fraction"] == pytest.approx(4 / 8)
    assert result["named_minus_free"]["specific"] == result["named_minus_generic"]["specific"]


def test_cross_products_remove_independent_mean_zero_repeat_noise_in_expectation():
    mu = fixed_panel(2, 1, scenes=1)
    loadings = np.array([2, -1, 3, 1, -2, 2.0])[None, None, :, None]
    truth = shared_decomposition(mu)
    observed = []
    for e0, e1 in itertools.product((-1, 1), repeat=2):
        signs = np.array([e0, e1])[None, :, None, None]
        observed.append(shared_decomposition(mu + signs * loadings))
    for baseline in ("named_minus_free", "named_minus_generic"):
        for component in ("common", "specific", "total"):
            expectation = np.mean([r[baseline][component] for r in observed])
            assert expectation == pytest.approx(truth[baseline][component], abs=1e-13)
    for key in ("generic_component", "additional_naming_component", "signed_interaction"):
        expectation = np.mean([r["common_shift_identity"][key] for r in observed])
        assert expectation == pytest.approx(truth["common_shift_identity"][key], abs=1e-13)


def test_cross_repeat_ratio_can_exceed_one_and_negative_components_are_retained():
    x = np.zeros((2, 2, 6, 1))
    x[:, 0, 2:, 0] = [2, 0, 2, 0]
    x[:, 1, 2:, 0] = [0.5, 1.5, 0.5, 1.5]
    result = shared_decomposition(x)["named_minus_free"]
    assert result["specific"] == pytest.approx(-2)
    assert result["total"] == pytest.approx(2)
    assert result["shared_fraction"] == pytest.approx(2)


@pytest.mark.parametrize("second", [-1, 0])
def test_nonpositive_total_has_no_shared_fraction(second):
    x = np.zeros((2, 2, 6, 1))
    x[:, 0, 2:] = 1
    x[:, 1, 2:] = second
    result = shared_decomposition(x)["named_minus_free"]
    assert result["total"] <= 0
    assert result["shared_fraction"] is None


def test_repeat_swapping_and_arbitrary_shared_translation_preserve_scalar_results():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(4, 2, 6, 3))
    original = shared_decomposition(x)
    transformed = shared_decomposition(x + rng.normal(size=(4, 2, 1, 3)))
    swapped = shared_decomposition(x[:, ::-1])
    for baseline in ("named_minus_free", "named_minus_generic"):
        for key in ("common", "specific", "total", "shared_fraction"):
            assert transformed[baseline][key] == pytest.approx(original[baseline][key])
            assert swapped[baseline][key] == pytest.approx(original[baseline][key])


def test_pair_projection_ignores_orthogonal_offsets_and_uses_correct_normalizer():
    q = np.array([-2.0, 1])
    orthogonal = np.array([1.0, 2])
    refs = np.array([q / 2, -q / 2, [0, 0], [0, 0]])
    x = np.zeros((3, 2, 6, 2))
    coefficients = np.array([[1, 2], [-2, 4], [0, 1]])
    x[:, :, 2] = coefficients[:, :, None] * q + 9 * orthogonal
    result = monet_sisley_alignment(x, refs)
    assert result["reference_pair_squared_distance"] == pytest.approx(5)
    assert result["beta"] == pytest.approx(coefficients.mean())
    np.testing.assert_allclose(result["scene_beta"], coefficients.mean(axis=1))


def test_scene_deletion_recomputes_scene_means_before_taking_ratio():
    x = fixed_panel(0, 0, scenes=3)
    offsets = np.array([0.0, 2, 10])
    x[:, :, 2:, 0] += offsets[:, None, None]
    refs = np.array([[-1.0], [1], [2], [3]])
    result = summarize_model(x, refs)
    assert result["scene_averaged"]["named_minus_free"]["shared_fraction"] == pytest.approx(16 / 17)
    for row in result["scene_deletions"]:
        c = np.delete(offsets, row["omitted_scene"]).mean()
        assert row["named_minus_free"]["shared_fraction"] == pytest.approx(c*c / (c*c + 1))
    deleted = result["scene_deletions"][2]["named_minus_free"]["shared_fraction"]
    incorrect_average_of_ratios = np.mean(offsets[:2]**2 / (offsets[:2]**2 + 1))
    assert deleted != pytest.approx(incorrect_average_of_ratios)
    assert result["scene_deletion_summaries"]["named_minus_free"]["available_deletions"] == 3


def test_pair_deletion_retains_fixed_reference_and_omits_the_correct_scene():
    x = np.zeros((3, 2, 6, 1))
    x[:, :, 2, 0] = np.array([1, 2, 9])[:, None]
    refs = np.array([[1.0], [0], [0], [0]])
    result = summarize_model(x, refs)
    assert result["monet_sisley"]["beta"] == pytest.approx(4)
    assert [d["monet_sisley_beta"] for d in result["scene_deletions"]] == [5.5, 5.0, 1.5]
    assert result["scene_deletion_summaries"]["monet_sisley_beta"]["range"] == [1.5, 5.5]


def test_invalid_panels_and_degenerate_pair_target_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        shared_decomposition(np.full((2, 2, 6, 1), np.nan))
    with pytest.raises(ValueError, match="two repeats"):
        shared_decomposition(np.zeros((2, 3, 6, 1)))
    with pytest.raises(ValueError, match="positive"):
        monet_sisley_alignment(np.zeros((2, 2, 6, 1)), np.zeros((4, 1)))
    with pytest.raises(ValueError, match="at least two scenes"):
        summarize_model(np.zeros((1, 2, 6, 1)), np.array([[1.0], [0], [0], [0]]))
