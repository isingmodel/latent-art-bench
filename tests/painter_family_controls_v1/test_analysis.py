"""Constructed-vector checks only: no existing images, outcomes, or network."""

import copy
import json
import math

import numpy as np
import pytest
from scipy.stats import t as student_t

from latent_art_bench.painter_family_controls_v1.analysis import (
    PAINTER_ORDER,
    _quadratic_confidence_set,
    analyze_primary,
    correlation_sensitivities,
    evaluate_transport,
    fieller_confidence_set,
    fit_transport_parameters,
    primary_decision,
    window_components,
)

TIMES = [
    {"start": f"constructed-window-{i}-start", "completion": f"constructed-{i}-end"}
    for i in range(8)
]


def fixed_vectors(*, generic_noise=None, common=0.02, labeled=0.03, family=0.04):
    """Unit-query oracle with known C_G, L, F and orthogonal filler energy."""
    refs = np.zeros((4, 6))
    refs[:, 0] = 0.4
    contrast = np.eye(4) - 0.25
    refs[:, 1:5] = 0.2 * contrast
    data = np.zeros((6, 8, 12, 8, 6))
    data[..., 2, 0] = 0.01 / 0.4
    data[..., 3, 0] = family / 0.4
    data[..., 4:8, 0] = common / 0.4
    data[..., 4:8, 1:5] = (labeled / 0.15) * contrast
    if generic_noise is not None:
        data[..., 1, 0] = np.asarray(generic_noise)[None, :, None] / 0.4
    data[..., -1] = np.sqrt(1 - np.sum(data[..., :-1] ** 2, axis=-1))
    np.testing.assert_allclose(np.linalg.norm(data, axis=-1), 1)
    return data, refs


def transport_vectors():
    refs = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
    old = np.broadcast_to(refs, (6, 14, 2, 4, 2)).copy()
    new = np.broadcast_to(refs, (6, 8, 12, 4, 2)).copy()
    return old, new, refs


def test_constructed_absolute_oracle_identities_and_raw_reference_energy():
    data, refs = fixed_vectors()
    result = window_components(data, refs)
    expected = {
        "N": 0.05,
        "F": 0.04,
        "S": 0.01,
        "L": 0.03,
        "C_G": 0.02,
        "C_F": -0.02,
        "F-S": 0.03,
        "N-F": 0.01,
        "T": 0.015,
    }
    for key, value in expected.items():
        np.testing.assert_allclose(result["components"][key], value, atol=1e-16)
    assert result["reference_contrast_energy_mean"] == pytest.approx(0.03)
    assert result["reference_contrast_energy_sum"] == pytest.approx(0.12)
    assert len(result["pairwise"]) == 6
    assert result["pairwise"][0]["painters"] == list(PAINTER_ORDER[:2])
    np.testing.assert_allclose(result["pairwise"][0]["aligned_dot_window_values"], 0.08)
    np.testing.assert_allclose(result["pairwise"][0]["beta_window_values"], 1.0)
    components = result["components"]
    np.testing.assert_allclose(components["N"], components["C_G"] + components["L"])
    np.testing.assert_allclose(components["N-F"], components["C_F"] + components["L"])
    # Normalizing raw references would change these targets; it is not done.
    normalized = refs / np.linalg.norm(refs, axis=-1, keepdims=True)
    assert not np.allclose(window_components(data, normalized)["components"]["N"], 0.05)


def test_shared_generic_covariance_retained_and_no_scene_noise_pooling():
    noise = np.arange(8) * 0.001
    data, refs = fixed_vectors(generic_noise=noise)
    report = analyze_primary(data, refs, TIMES)
    model = report["models"][0]
    values = np.array(model["components"]["T"]["window_values"])
    np.testing.assert_allclose(values, 0.015 - 0.5 * noise)
    variance = np.var(values, ddof=1)
    n = np.array(model["components"]["N"]["window_values"])
    f = np.array(model["components"]["F"]["window_values"])
    covariance = np.cov(n, f, ddof=1)[0, 1]
    assert variance == pytest.approx(np.var(f, ddof=1) + 0.25 * np.var(n, ddof=1) - covariance)
    assert np.var(f, ddof=1) + 0.25 * np.var(n, ddof=1) == pytest.approx(5 * variance)
    assert model["primary_intervals"]["T"]["se"] == pytest.approx(math.sqrt(variance / 8))
    assert model["primary_intervals"]["T"]["se"] != pytest.approx(math.sqrt(variance / 96))


def test_fixed_twelve_endpoint_multiplicity_equal_windows_and_influence():
    data, refs = fixed_vectors(generic_noise=np.arange(8) * 0.002)
    report = analyze_primary(data, refs, TIMES)
    critical = student_t.ppf(1 - 0.05 / 24, 7)
    assert report["primary_family_size"] == 12
    assert report["degrees_of_freedom"] == 7
    assert report["critical_t"] == pytest.approx(critical)
    assert report["half_width_per_observed_sd"] == pytest.approx(1.4758, abs=0.0001)
    assert report["window_times"] == TIMES
    summary = report["models"][0]["components"]["N"]
    values = np.array(summary["window_values"])
    assert summary["equal_window_mean"] == pytest.approx(np.mean(values))
    for omitted, mean in enumerate(summary["leave_one_window_out"]["means"]):
        assert mean == pytest.approx(np.delete(values, omitted).mean())
    interval = report["models"][0]["primary_intervals"]["N"]
    assert interval["upper"] - interval["mean"] == pytest.approx(
        critical * values.std(ddof=1) / 8**0.5
    )
    data[5, 0, 0, 1] = np.nan
    incomplete = analyze_primary(data, refs, TIMES)
    assert incomplete["critical_t"] == report["critical_t"]
    assert incomplete["models"][0]["primary_intervals"] == report["models"][0]["primary_intervals"]
    assert incomplete["models"][5]["primary_intervals"] == {}


@pytest.mark.parametrize(
    ("n", "t", "expected"),
    [
        ((0.1, 0.2), (0.01, 0.1), "name_free_prompt_exceeds_half_positive_named_gain"),
        ((0.1, 0.2), (-0.1, -0.01), "name_free_prompt_below_half_positive_named_gain"),
        ((0, 0.2), (0.01, 0.1), "unresolved"),
        ((0.1, 0.2), (0, 0.1), "unresolved"),
        ((0.1, 0.2), (-0.1, 0), "unresolved"),
        ((-0.2, -0.1), (0.01, 0.1), "unresolved"),
        ((0.1, 0.2), (-0.1, 0.1), "unresolved"),
    ],
)
def test_primary_strict_boundary_decisions(n, t, expected):
    assert primary_decision(n, t) == expected


def test_missing_primary_secondary_census_never_imputed():
    data, refs = fixed_vectors()
    data[0, 2, 7, 1] = np.nan
    data[1, 3, 2, 2] = np.nan
    data[2, 4, 1, 0] = np.nan
    result = analyze_primary(data, refs, TIMES)
    primary, style, free = result["models"][:3]
    assert not primary["primary_complete"]
    assert primary["missing_cells_window_scene_arm"] == [[2, 7, 1]]
    assert primary["components"]["N"]["window_values"][2] is None
    assert primary["components"]["N"]["equal_window_mean"] is None
    assert primary["components"]["N"]["leave_one_window_out"] is None
    assert primary["components"]["L"]["equal_window_mean"] == pytest.approx(0.03)
    assert primary["components"]["C_F"]["equal_window_mean"] == pytest.approx(-0.02)
    assert primary["components"]["N-F"]["equal_window_mean"] == pytest.approx(0.01)
    assert primary["components"]["F-S"]["equal_window_mean"] == pytest.approx(0.03)
    assert primary["primary_intervals"] == {}
    assert primary["secondary_ratios"]["F/N"]["status"] == "unavailable_incomplete_paired_windows"
    assert primary["secondary_ratios"]["C_F/(N-F)"]["raw_signed_ratio"] == pytest.approx(-2)
    assert style["primary_complete"] and free["primary_complete"]
    assert style["components"]["S"]["equal_window_mean"] is None
    assert free["free_baseline"]["N_free"]["equal_window_mean"] is None
    assert len(result["models"]) == 6
    json.dumps(result, allow_nan=False)


def test_explicit_missing_mask_and_reject_nonfinite_observed_or_wrong_axes():
    data, refs = fixed_vectors()
    observed = np.ones(data.shape[:-1], dtype=bool)
    observed[0, 0, 0, 3] = False
    assert not analyze_primary(data, refs, TIMES, observed=observed)["models"][0][
        "primary_complete"
    ]
    data[0, 0, 0, 4] = np.nan
    with pytest.raises(ValueError, match="observed cell"):
        window_components(data, refs, observed=observed)
    with pytest.raises(ValueError, match="expected axes"):
        window_components(data[:, :, :11], refs)
    with pytest.raises(ValueError, match="CSD"):
        analyze_primary(data, refs, TIMES, representation="clip")
    with pytest.raises(ValueError, match="eight"):
        analyze_primary(data, refs, TIMES[:7])


def test_negative_and_unequal_gains_and_unclipped_secondary_shares():
    data, refs = fixed_vectors(common=-0.04, labeled=0.01, family=0.02)
    model = analyze_primary(data, refs, TIMES)["models"][0]
    assert model["components"]["N"]["equal_window_mean"] == pytest.approx(-0.03)
    assert model["components"]["L"]["equal_window_mean"] == pytest.approx(0.01)
    assert model["secondary_ratios"]["F/N"]["raw_signed_ratio"] == pytest.approx(-2 / 3)
    assert model["secondary_ratios"]["F/N"]["positive_denominator_share"] is None
    assert model["decision"] == "unresolved"
    positive, refs = fixed_vectors(common=0.01, labeled=0.01, family=0.06)
    fraction = analyze_primary(positive, refs, TIMES)["models"][0]["secondary_ratios"]["F/N"]
    assert fraction["positive_denominator_share"] == pytest.approx(3)


def test_assumed_correlation_multipliers_are_explicit_not_estimated():
    result = correlation_sensitivities()
    assert [item["assumed_rho"] for item in result] == [0, 0.1, 0.25, 0.5]
    assert [item["se_multiplier"] for item in result] == pytest.approx(
        [1, math.sqrt(1.7 / 0.9), math.sqrt(2.75 / 0.75), 3]
    )


def test_fieller_ratio_of_means_uses_paired_covariance_and_all_denominators():
    numerator = np.array([2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    denominator = np.array([-1.0, 0.0, 2.0, 2.0, 2.0, 2.0, 2.0, 3.0])
    result = fieller_confidence_set(numerator, denominator)
    assert result["raw_signed_ratio"] == pytest.approx(numerator.mean() / denominator.mean())
    assert result["raw_signed_ratio"] != pytest.approx(np.mean(numerator[2:] / denominator[2:]))
    np.testing.assert_allclose(
        result["covariance_of_paired_means"], np.cov(numerator, denominator) / 8
    )
    assert result["denominator_windows"] == denominator.tolist()
    assert result["familywise_claim"] is False
    with pytest.raises(ValueError, match="eight finite paired"):
        fieller_confidence_set(numerator[:7], denominator[:7])
    numerator[0] = np.nan
    with pytest.raises(ValueError, match="eight finite paired"):
        fieller_confidence_set(numerator, denominator)


@pytest.mark.parametrize(
    ("coefficients", "kind", "intervals"),
    [
        ((1.0, -3.0, 2.0), "bounded", [[1.0, 2.0]]),
        ((-1.0, 3.0, -2.0), "disconnected", [[None, 1.0], [2.0, None]]),
        ((0.0, 2.0, -4.0), "half_line", [[None, 2.0]]),
        ((0.0, -2.0, 4.0), "half_line", [[2.0, None]]),
        ((0.0, 0.0, 0.0), "all_real", [[None, None]]),
        ((0.0, 0.0, 1.0), "empty", []),
        ((1.0, 0.0, 1.0), "empty", []),
        ((-1.0, 0.0, -1.0), "all_real", [[None, None]]),
        ((1.0, -2.0, 1.0), "singleton", [[1.0, 1.0]]),
        ((-1.0, 2.0, -1.0), "all_real", [[None, None]]),
    ],
)
def test_fieller_set_topologies_and_included_boundaries(coefficients, kind, intervals):
    result = _quadratic_confidence_set(*coefficients)
    assert result["kind"] == kind
    assert len(result["intervals"]) == len(intervals)
    for actual, expected in zip(result["intervals"], intervals):
        for bound, target in zip(actual, expected):
            assert bound is None if target is None else bound == pytest.approx(target)
    assert result["finite_boundaries_included"]


def test_fieller_degenerate_zero_negative_near_zero_denominators_and_no_clipping():
    zero = np.zeros(8)
    one = np.ones(8)
    result = fieller_confidence_set(one, zero)
    assert result["confidence_set"]["kind"] == "empty"
    assert result["raw_signed_ratio"] is None
    assert result["positive_denominator_share"] is None
    assert fieller_confidence_set(zero, zero)["confidence_set"]["kind"] == "all_real"
    negative = fieller_confidence_set(2 * one, -one)
    assert negative["raw_signed_ratio"] == -2
    assert negative["positive_denominator_share"] is None
    assert negative["confidence_set"]["intervals"] == [[-2, -2]]
    near_zero = fieller_confidence_set(one, one * 1e-10)
    assert near_zero["raw_signed_ratio"] == pytest.approx(1e10)
    assert near_zero["positive_denominator_share"] == pytest.approx(1e10)
    assert near_zero["confidence_set"]["kind"] == "singleton"
    disconnected = fieller_confidence_set(one, np.tile([-1.0, 1.0], 4))
    assert disconnected["confidence_set"]["kind"] == "disconnected"
    assert disconnected["confidence_set"]["intervals"][0][0] is None
    assert disconnected["confidence_set"]["intervals"][1][1] is None
    all_real = fieller_confidence_set(np.tile([-1.0, 1.0], 4), np.tile([-1.0, -1.0, 1.0, 1.0], 2))
    assert all_real["confidence_set"]["kind"] == "all_real"
    json.dumps(disconnected, allow_nan=False)


@pytest.mark.parametrize("ratio", [3.0, -0.3])
def test_fieller_exact_proportional_components_do_not_round_to_empty(ratio):
    denominator = np.arange(1.0, 9.0)
    result = fieller_confidence_set(ratio * denominator, denominator)
    assert result["confidence_set"]["kind"] == "singleton"
    assert result["confidence_set"]["intervals"] == [[ratio, ratio]]
    denominator = np.tile([-1.0, 1.0], 4)
    result = fieller_confidence_set(ratio * denominator, denominator)
    assert result["confidence_set"]["kind"] == "all_real"


@pytest.mark.parametrize("scale", [1.0, 1e-100, 1e-200, 1e100])
@pytest.mark.parametrize("ratio", [0.3, -0.3, 3.0])
def test_nearly_proportional_fieller_matches_direct_paired_student_inversion(scale, ratio):
    y = np.arange(1.0, 9.0) / 100
    x = ratio * y + 1e-10 * np.tile([-1.0, 1.0], 4)
    result = fieller_confidence_set(x * scale, y * scale)
    assert result["confidence_set"]["kind"] == "bounded"
    low, high = result["confidence_set"]["intervals"][0]
    raw = result["raw_signed_ratio"]
    assert low < raw < high
    # Independent oracle in residual space, avoiding the tested quadratic solver.
    for delta in [0, -1e-7, -1e-8, -1e-9, 1e-9, 1e-8, 1e-7]:
        candidate = ratio + delta
        residual = x - candidate * y
        allowed = abs(residual.mean()) <= student_t.ppf(0.975, 7) * residual.std(ddof=1) / 8**0.5
        assert bool(low <= candidate <= high) == bool(allowed)


def test_exact_proportional_fieller_is_scale_invariant_below_variance_underflow():
    y = np.arange(1.0, 9.0) * 1e-200
    result = fieller_confidence_set(3 * y, y)
    assert result["confidence_set"]["kind"] == "singleton"
    assert result["confidence_set"]["intervals"] == [[3, 3]]


@pytest.mark.parametrize("offset", [0, 1e-8, 1e-10, 1e-12, -1e-12])
def test_near_zero_mean_denominator_keeps_disconnected_fieller_boundaries(offset):
    x = np.ones(8)
    y = np.tile([-1.0, 1.0], 4) + offset
    result = fieller_confidence_set(x, y)
    intervals = result["confidence_set"]["intervals"]
    assert result["confidence_set"]["kind"] == "disconnected"
    assert intervals[0][0] is None and intervals[1][1] is None
    critical_se = student_t.ppf(0.975, 7) * y.std(ddof=1) / 8**0.5
    assert intervals[0][1] == pytest.approx(1 / (y.mean() - critical_se), abs=1e-12)
    assert intervals[1][0] == pytest.approx(1 / (y.mean() + critical_se), abs=1e-12)


def test_very_different_component_scales_preserve_bounded_fieller_set():
    x = np.arange(1.0, 9.0) / 100
    y = np.full(8, 1e-170)
    result = fieller_confidence_set(x, y)
    assert result["confidence_set"]["kind"] == "bounded"
    half_width = student_t.ppf(0.975, 7) * x.std(ddof=1) / 8**0.5
    assert result["confidence_set"]["intervals"][0] == pytest.approx(
        [(x.mean() - half_width) / y.mean(), (x.mean() + half_width) / y.mean()]
    )


def test_transport_full_old_only_fitting_and_exact_prediction_oracle():
    old, new, refs = transport_vectors()
    parameters = fit_transport_parameters(old, refs)
    np.testing.assert_array_equal(parameters["translation"], np.zeros((6, 2)))
    np.testing.assert_array_equal(parameters["reference_prototypes"], refs)
    np.testing.assert_array_equal(
        parameters["generated_prototypes"], np.broadcast_to(refs, (6, 4, 2))
    )
    report = evaluate_transport(new, parameters, TIMES)
    for rule in ("baseline", "translated", "supervised_generated"):
        aggregate = report["models"][0]["aggregate"][rule]
        assert aggregate["equal_window_accuracy"] == 1
        assert aggregate["equal_window_accuracy_difference"] == 0
        assert aggregate["equal_window_recall"] == [1, 1, 1, 1]
        np.testing.assert_array_equal(
            report["predictions"][rule]["prediction_index"],
            np.broadcast_to(np.arange(4), (6, 8, 12, 4)),
        )
    assert (
        report["models"][0]["windows"][0]["rules"]["baseline"][
            "observed_confusion_truth_rows_prediction_columns"
        ]
        == (np.eye(4, dtype=int) * 12).tolist()
    )
    with pytest.raises(ValueError, match="6,14,2,4"):
        fit_transport_parameters(old[:, :13], refs)
    with pytest.raises(ValueError, match="6,14,2,4"):
        fit_transport_parameters(old[:, :, :1], refs)
    old[0, 0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="complete finite old"):
        fit_transport_parameters(old, refs)


def test_translation_known_harm_retained_and_no_refit_on_new_queries():
    old, new, refs = transport_vectors()
    old[:] = [1.0, 0.0]
    parameters = fit_transport_parameters(old, refs)
    frozen = copy.deepcopy(parameters)
    np.testing.assert_array_equal(parameters["translation"], np.tile([-1.0, 0.0], (6, 1)))
    report = evaluate_transport(new, parameters, TIMES)
    aggregate = report["models"][0]["aggregate"]["translated"]
    assert aggregate["equal_window_accuracy"] == 0.5
    assert aggregate["equal_window_accuracy_difference"] == -0.5
    assert aggregate["observed_harms"] == 8 * 12 * 2
    assert aggregate["observed_corrections"] == 0
    assert report["predictions"]["translated"]["harm_from_baseline"][0][0][0] == [0, 0, 1, 1]
    assert report["zero_translated_query"][0][0][0] == [True, False, False, False]
    new[:] = [0.0, -1.0]
    evaluate_transport(new, parameters, TIMES)
    assert parameters == frozen


def test_transport_exact_ties_zero_queries_and_signed_truth_margins():
    old, new, refs = transport_vectors()
    parameters = fit_transport_parameters(old, refs)
    new[0, 0, 0] = np.sqrt(0.5)
    new[0, 0, 1, 0] = [-1.0, 0.0]
    result = evaluate_transport(new, parameters, TIMES)
    assert result["painter_order"] == list(PAINTER_ORDER)
    predictions = result["predictions"]["baseline"]
    assert predictions["prediction_index"][0][0][0] == [0, 0, 0, 0]
    assert predictions["tied_classes"][0][0][0] == [[True, False, True, False]] * 4
    assert predictions["exact_tie"][0][0][0] == [True] * 4
    assert predictions["truth_minus_best_other_margin"][0][0][0] == pytest.approx(
        [0, -np.sqrt(2), 0, -np.sqrt(2)]
    )
    assert predictions["truth_minus_best_other_margin"][0][0][1][0] == -2
    assert result["zero_query"][0][0][0] == [False] * 4
    old[:] = [1.0, 0.0]
    parameters = fit_transport_parameters(old, refs)
    new[0, 0, 0] = [1.0, 0.0]
    zero_result = evaluate_transport(new, parameters, TIMES)
    assert zero_result["zero_translated_query"][0][0][0] == [True] * 4
    translated = zero_result["predictions"]["translated"]
    assert translated["tied_classes"][0][0][0] == [[True] * 4] * 4
    assert translated["prediction_index"][0][0][0] == [0] * 4
    assert translated["truth_minus_best_other_margin"][0][0][0] == [0] * 4
    json.dumps(result, allow_nan=False)


def test_transport_incomplete_census_never_becomes_subset_estimand():
    old, new, refs = transport_vectors()
    parameters = fit_transport_parameters(old, refs)
    new[0, 3, 0, 2] = np.nan
    report = evaluate_transport(new, parameters, TIMES)
    assert report["missing_cells_model_window_scene_painter"] == [[0, 3, 0, 2]]
    model = report["models"][0]
    assert not model["complete_eight_windows"]
    assert model["aggregate"]["baseline"]["equal_window_accuracy"] is None
    assert model["aggregate"]["translated"]["equal_window_accuracy_difference"] is None
    window = model["windows"][3]
    assert window["observed_queries"] == 47
    assert window["rules"]["baseline"]["observed_correct"] == 47
    assert window["rules"]["baseline"]["fixed_window_accuracy"] is None
    assert window["rules"]["baseline"]["fixed_window_recall"] is None
    assert report["predictions"]["baseline"]["prediction_index"][0][3][0][2] is None
    assert report["models"][1]["aggregate"]["baseline"]["equal_window_accuracy"] == 1


def test_frozen_parameters_reject_changed_order_scale_or_zero_prototypes():
    old, new, refs = transport_vectors()
    parameters = fit_transport_parameters(old, refs)
    parameters["painter_order"] = list(reversed(PAINTER_ORDER))
    with pytest.raises(ValueError, match="painter order"):
        evaluate_transport(new, parameters, TIMES)
    parameters = fit_transport_parameters(old, refs)
    parameters["translation_scale"] = 0.5
    with pytest.raises(ValueError, match="scale"):
        evaluate_transport(new, parameters, TIMES)
    old[:] = 0
    with pytest.raises(ValueError, match="unit vectors"):
        fit_transport_parameters(old, refs)


def test_unit_embedding_and_whole_vector_missingness_contract():
    data, refs = fixed_vectors()
    data[0, 0, 0, 4] *= 2
    with pytest.raises(ValueError, match="unit vectors"):
        window_components(data, refs)
    data, refs = fixed_vectors()
    refs *= 3
    with pytest.raises(ValueError, match="norm above one"):
        window_components(data, refs)
    data, refs = fixed_vectors()
    data[0, 0, 0, 4, 0] = np.nan
    with pytest.raises(ValueError, match="partial NaN"):
        window_components(data, refs)
    observed = np.ones(data.shape[:-1], dtype=bool)
    observed[0, 0, 0, 4] = False
    assert not window_components(data, refs, observed=observed)["primary_complete_windows"][0, 0]
    old, new, refs = transport_vectors()
    parameters = fit_transport_parameters(old, refs)
    old[0, 0, 0, 0] *= 2
    with pytest.raises(ValueError, match="unit vectors"):
        fit_transport_parameters(old, refs)
    new[0, 0, 0, 0] *= 2
    with pytest.raises(ValueError, match="unit vectors"):
        evaluate_transport(new, parameters, TIMES)
    new[0, 0, 0, 0] = 0
    with pytest.raises(ValueError, match="unit vectors"):
        evaluate_transport(new, parameters, TIMES)
