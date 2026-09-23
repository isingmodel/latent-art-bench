"""Constructed scientific controls for the learned-representation audit."""

import json

import numpy as np
import pytest

from latent_art_bench.painter_learned_analysis_v1 import (
    _geometry,
    _recognition,
    _shared,
    analyze_arrays,
)


def painter_vectors(amplitude=0.25):
    # Four distinct directions at a common latitude of a unit sphere. Doubling
    # their lateral amplitude preserves valid unit vectors and doubles contrasts.
    vectors = np.zeros((4, 768))
    vectors[0, 0] = amplitude
    vectors[1, 0] = -amplitude
    vectors[2, 1] = amplitude
    vectors[3, 1] = -amplitude
    vectors[:, 2] = np.sqrt(1 - amplitude**2)
    return vectors


def cohort(named):
    x = np.zeros((6, 14, 2, 6, 768))
    x[:, :, :, :2, 2] = 1
    x[:, :, :, 2:] = named
    return x


def panel(vectors):
    return [row[None] for row in vectors]


@pytest.mark.parametrize("amplitude,beta,d", [(0, 0, 1), (0.25, 1, 0), (0.5, 2, 1)])
def test_no_distinction_exact_and_doubled_valid_unit_cases(amplitude, beta, d):
    reference = painter_vectors()
    result = analyze_arrays(cohort(painter_vectors(amplitude)), panel(reference), panel(reference))
    metric = result["targets"]["primary"]["models"][0]["centered"]
    assert metric["beta"] == pytest.approx(beta)
    assert metric["q"] == pytest.approx(beta**2)
    assert metric["d"] == pytest.approx(d)
    assert metric["aggregate_d"] == pytest.approx(d)
    assert metric["scene_variation"] == pytest.approx(0, abs=1e-15)
    if beta:
        assert metric["calibration"]["held_out_d"] == pytest.approx(0, abs=1e-14)
        assert metric["calibration"]["fitted_scalars"] == pytest.approx([1 / beta] * 14)
    else:
        assert metric["calibration"]["held_out_d"] is None
    json.dumps(result, allow_nan=False)


def test_swapped_names_are_detected_despite_high_prototype_similarity():
    ref = painter_vectors()
    result = analyze_arrays(cohort(ref[[1, 0, 2, 3]]), panel(ref), panel(ref))
    row = result["targets"]["primary"]["models"][0]
    assert row["prototype"]["mean_diagonal"] > 0.9
    assert row["recognition"]["macro_accuracy"] == 0.5
    assert row["painter_pairs"][0]["beta"] == pytest.approx(-1)
    assert row["label_permutations"]["identity"]["d_rank_interval"][0] > 1
    best = next(
        p for p in row["label_permutations"]["rows"]
        if p["reference_indices_for_generated_names"] == [1, 0, 2, 3]
    )
    assert best["d"] == pytest.approx(0)
    assert best["d_rank_interval"] == [1, 1]
    assert best["prototype_diagonal_mean_rank_interval"] == [1, 1]
    assert len(row["label_permutations"]["rows"]) == 24


def test_common_translation_changes_proximity_but_not_centered_geometry():
    ref = painter_vectors()[:, :3]
    named = np.broadcast_to(ref, (5, 2, 4, 3)).copy()
    translated = named + np.arange(30).reshape(5, 2, 1, 3) / 10
    original, shifted = _geometry(named, ref), _geometry(translated, ref)
    for key in ["beta", "q", "d", "aggregate_d", "scene_variation"]:
        assert shifted[key] == pytest.approx(original[key], abs=1e-14)
    assert not np.isclose(np.sum(named.mean((0, 1)) * ref),
                          np.sum(translated.mean((0, 1)) * ref))


def test_scene_variation_and_held_out_calibration_use_other_scenes():
    ref = painter_vectors()[:, :3]
    # Two matching scenes and one doubled scene. Each doubled-scene validation
    # fold is calibrated only on matching scenes, so its held-out error is 1.
    named = np.stack([ref, ref, 2 * ref])[:, None].repeat(2, axis=1)
    metric = _geometry(named, ref)
    assert metric["d"] == pytest.approx(1 / 3)
    assert metric["aggregate_d"] == pytest.approx(1 / 9)
    assert metric["scene_variation"] == pytest.approx(2 / 9)
    assert metric["calibration"]["fitted_scalars"] == pytest.approx([0.6, 0.6, 1.0])
    assert metric["calibration"]["held_out_scene_d"] == pytest.approx([0.16, 0.16, 1.0])


def test_repeat_correction_preserves_negative_error_and_undefined_calibration():
    ref = painter_vectors()[:, :3]
    named = np.stack([3 * ref, -ref])[None].repeat(3, axis=0)
    metric = _geometry(named, ref)
    assert metric["beta"] == pytest.approx(1)
    assert metric["q"] == pytest.approx(-3)
    assert metric["d"] == pytest.approx(-4)
    assert metric["corrected_alignment"] is None
    assert metric["calibration"]["held_out_d"] is None
    assert metric["calibration"]["fitted_scalars"] == [None, None, None]


def test_shared_fractions_isolate_incremental_naming_and_keep_negative_terms():
    values = np.zeros((3, 2, 6, 2))
    values[:, :, 1, 0] = 2
    values[:, :, 2:, 0] = 2
    values[:, :, 2:, 1] = [-1, 1, -1, 1]
    free = _shared(values, 0)["scene_averaged"]
    generic = _shared(values, 1)["scene_averaged"]
    assert free["common_fraction"] == pytest.approx(0.8)
    assert generic["common_fraction"] == pytest.approx(0)
    values[:, 0, 2:, 0] = 0.5
    values[:, 1, 2:, 0] = -0.5
    negative = _shared(values, 0)["scene_averaged"]
    assert negative["common_ss"] == pytest.approx(-1)
    assert negative["common_fraction"] == pytest.approx(-1 / 3)
    values[:, :, 2:, 1] = 0
    assert _shared(values, 0)["scene_averaged"]["common_fraction"] is None


def test_unequal_panel_counts_do_not_change_macro_accuracy():
    ref = np.eye(4)
    groups = [np.repeat(ref[i][None], n, axis=0) for i, n in enumerate([1, 2, 3, 10])]
    groups[3] = np.repeat(ref[0][None], 10, axis=0)
    result = _recognition(groups, ref)
    assert result["macro_accuracy"] == 0.75
    assert result["micro_accuracy"] == 6 / 16
    assert result["confusion_counts"][3] == [10, 0, 0, 0]


def test_development_target_is_separate_and_normalized_recognition_is_distinct():
    ref = painter_vectors()
    dev = ref[[1, 0, 2, 3]]
    result = analyze_arrays(cohort(ref), panel(ref), panel(dev))
    assert result["targets"]["primary"]["models"][0]["centered"]["d"] == pytest.approx(0)
    assert result["targets"]["development"]["models"][0]["painter_pairs"][0]["beta"] == -1
    assert result["development_recognition"]["macro_accuracy"] == 0.5
    # Prototype length is irrelevant to normalized cosine recognition.
    classification = _recognition([row[None] for row in np.eye(4)], np.eye(4) * [0.1, 1, 2, 4])
    assert classification["macro_accuracy"] == 1


def test_scene_deletion_retains_the_known_influence_pattern():
    ref = painter_vectors()
    values = cohort(ref)
    values[:, 0, :, 2:] = painter_vectors(0.5)
    result = analyze_arrays(values, panel(ref), panel(ref))
    influence = result["targets"]["primary"]["models"][0]["scene_influence"]
    assert influence["beta"]["range"] == pytest.approx([1, 14 / 13])
    assert influence["d"]["range"] == pytest.approx([0, 1 / 13])
    assert influence["aggregate_d"]["range"] == pytest.approx([0, 1 / 169])
    assert "scene-conditional" in influence["d"]["estimand"]
    assert influence["monet_sisley_beta"]["range"] == pytest.approx([1, 14 / 13])


def test_prototype_gain_separates_common_shift_from_labeled_response():
    ref = painter_vectors()
    values = cohort(ref)
    values[:, :, :, 1] *= -1  # Generic control is opposite to the common reference direction.
    result = analyze_arrays(values, panel(ref), panel(ref))
    row = result["targets"]["primary"]["models"][0]
    prototype = row["prototype"]
    gains = prototype["common_vs_labeled_prototype_gain"]
    reference_latitude = np.sqrt(1 - 0.25**2)
    free, generic = gains["named_minus_free"], gains["named_minus_generic"]
    assert free["common_term"] == pytest.approx((reference_latitude - 1) * reference_latitude)
    assert generic["common_term"] == pytest.approx((reference_latitude + 1) * reference_latitude)
    assert free["labeled_term"] == generic["labeled_term"] == pytest.approx(0.25**2)
    assert free["total"] == pytest.approx(1 - reference_latitude)
    assert generic["total"] == pytest.approx(1 + reference_latitude)
    assert free["common_fraction"] < 0
    assert free["labeled_fraction"] > 1
    for baseline in ["free", "generic"]:
        entry = gains["named_minus_" + baseline]
        assert entry["total"] == pytest.approx(prototype["mean_named_minus_" + baseline])
        assert entry["identity_residual"] == pytest.approx(0, abs=1e-14)
    contrast = row["centered"]
    assert prototype["mean_diagonal"] - prototype["mean_off_diagonal"] == pytest.approx(
        contrast["reference_energy"] * contrast["beta"] / 3
    )


@pytest.mark.parametrize("amplitude", [0, 0.5])
def test_nonpositive_total_prototype_gain_has_undefined_fractions(amplitude):
    ref = painter_vectors()
    result = analyze_arrays(cohort(painter_vectors(amplitude)), panel(ref), panel(ref))
    prototype = result["targets"]["primary"]["models"][0]["prototype"]
    for gain in prototype["common_vs_labeled_prototype_gain"].values():
        assert gain["total"] <= 0
        assert gain["common_fraction"] is None
        assert gain["labeled_fraction"] is None
        assert gain["total"] == pytest.approx(gain["direct_score_total"], abs=1e-14)


def test_permutation_ties_use_one_scale_even_when_prototypes_are_nearly_equal():
    ref = painter_vectors(1e-6)
    result = analyze_arrays(cohort(ref), panel(ref), panel(ref))
    permutations = result["targets"]["primary"]["models"][0]["label_permutations"]
    assert permutations["identity"]["beta_rank_interval"] == [1, 1]
    # Raw similarities are all within the numerical rank tolerance of one,
    # whereas beta normalizes by the tiny reference energy. Independent score
    # tolerances would misleadingly label all 24 prototype permutations tied.
    scores = [row["prototype_diagonal_mean"] for row in permutations["rows"]]
    assert np.ptp(scores) < 1e-10
    for row in permutations["rows"]:
        assert row["beta_rank_interval"] == row["d_rank_interval"]
        assert row["beta_rank_interval"] == row["prototype_diagonal_mean_rank_interval"]


def test_identical_reference_painters_are_reported_as_undefined():
    ref = painter_vectors(0)
    result = analyze_arrays(cohort(ref), panel(ref), panel(ref))
    row = result["targets"]["primary"]["models"][0]
    assert row["centered"]["d"] is None
    assert row["painter_pairs"][0]["beta"] is None
    assert row["label_permutations"]["identity"]["d_rank_interval"] is None
    assert row["label_permutations"]["identity"]["prototype_diagonal_mean_rank_interval"] == [1, 24]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("fault", ["shape", "nan", "not_unit", "empty_panel"])
def test_invalid_or_partial_embedding_inputs_fail_explicitly(fault):
    ref = painter_vectors()
    values, refs = cohort(ref), panel(ref)
    if fault == "shape":
        values = values[:, :-1]
    elif fault == "nan":
        values[0, 0, 0, 0, 0] = np.nan
    elif fault == "not_unit":
        values[0, 0, 0, 0] *= 2
    else:
        refs[0] = refs[0][:0]
    with pytest.raises(ValueError):
        analyze_arrays(values, refs, panel(ref))
