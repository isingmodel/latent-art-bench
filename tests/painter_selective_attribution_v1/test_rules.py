"""Constructed arrays only: no retained observations or real numerical outcomes."""

import copy
import json

import numpy as np
import pytest

from latent_art_bench import painter_selective_attribution_v1 as study


def quantiles(values):
    return [dict(n=9, rank=9, infinite=False, threshold=float(x)) for x in values]


def calibration(threshold=-.5):
    return dict(prototypes=np.eye(4).tolist(), quantiles=quantiles([threshold] * 4))


def generated_fixture(scenes=3):
    x = np.zeros((scenes, 2, 6, 4))
    x[:, :, :2] = np.ones(4) / 2
    x[:, :, 2:] = np.eye(4)
    ids = np.array([f"img-{s:02d}-{r}-{a}" for s in range(scenes)
                    for r in range(2) for a in range(6)]).reshape(scenes, 2, 6)
    return x, ids


def test_quantile_exact_order_statistic_no_interpolation_and_infinity():
    assert study.fixed_quantile(np.arange(9)[::-1]) == dict(
        n=9, rank=9, infinite=False, threshold=8.)
    assert study.fixed_quantile(np.arange(10)) == dict(
        n=10, rank=10, infinite=False, threshold=9.)
    assert study.fixed_quantile(np.arange(19)) == dict(
        n=19, rank=18, infinite=False, threshold=17.)
    assert study.fixed_quantile([1, 2]) == dict(n=2, rank=3, infinite=True, threshold=None)
    with pytest.raises(ValueError, match="empty calibration"):
        study.fixed_quantile([])


def test_nonconformity_uses_max_other_for_each_candidate():
    scores = np.array([[3., 2., 1., 0.], [1., 1., -1., -3.]])
    np.testing.assert_array_equal(study.nonconformity(scores),
                                  [[-1, 1, 2, 3], [0, 0, 2, 4]])


def test_all_four_decision_reasons_inclusive_threshold_and_first_index_tie():
    scores = np.array([[3., 2., 1., 0.]])
    accepted = study.decide(scores, quantiles([-1, -1, -1, -1]))
    assert accepted["accepted"].tolist() == [True]
    assert accepted["members"].tolist() == [[True, False, False, False]]
    assert accepted["reasons"].tolist() == ["accepted"]
    assert study.decide(scores, quantiles([-2] * 4))["reasons"].tolist() == ["empty_set"]
    assert study.decide(scores, quantiles([4] * 4))["reasons"].tolist() == ["multiple_labels"]
    out = study.decide(scores, quantiles([-2, 1, -1, -1]))
    assert out["reasons"].tolist() == ["singleton_disagrees_with_top1"]
    assert not out["accepted"][0]
    tied = study.decide([[1., 1., 0., 0.]], quantiles([0, 0, 0, 0]))
    assert tied["predictions"].tolist() == [0]
    assert tied["top_ties"].tolist() == [True]
    assert tied["margins"].tolist() == [0.]
    assert tied["reasons"].tolist() == ["multiple_labels"]


def test_infinite_quantile_has_explicit_null_semantics_and_no_guarantee():
    groups = [np.eye(4)[[a]] for a in range(4)]
    cal = study.calibrate(groups, groups)
    assert all(q["infinite"] and q["threshold"] is None for q in cal["quantiles"])
    assert cal["generated_image_coverage_guarantee"] is False
    out = study.decide(np.eye(4), cal["quantiles"])
    assert out["members"].all()
    assert not out["accepted"].any()
    json.dumps(cal, allow_nan=False)


def test_calibration_means_each_artist_then_unit_normalizes_without_generated_inputs():
    groups = []
    for a in range(4):
        pair = np.zeros((2, 5))
        pair[:, a], pair[:, 4] = .6, [.8, -.8]
        groups.append(pair)
    calibrators = [np.repeat(group[:1], 9, axis=0) for group in groups]
    fitted = study.calibrate(groups, calibrators)
    np.testing.assert_allclose(fitted["reference_mean_norms"], [.6] * 4)
    np.testing.assert_array_equal(np.array(fitted["prototypes"])[:, :4], np.eye(4))
    assert fitted["reference_counts"] == [2] * 4
    assert fitted["calibration_counts"] == [9] * 4
    np.testing.assert_allclose([q["threshold"] for q in fitted["quantiles"]], [-.6] * 4)
    changed = study.calibrate(groups[::-1], calibrators[::-1])
    np.testing.assert_array_equal(changed["prototypes"], np.array(fitted["prototypes"])[::-1])


def test_zero_prototype_mean_empty_class_nonunit_and_dimension_mismatch_rejected():
    groups = [np.repeat(np.eye(4)[[a]], 9, axis=0) for a in range(4)]
    zero_mean = copy.deepcopy(groups)
    zero_mean[0] = np.array([[1., 0, 0, 0], [-1., 0, 0, 0]])
    with pytest.raises(ValueError, match="zero or invalid reference mean"):
        study.calibrate(zero_mean, groups)
    empty = copy.deepcopy(groups)
    empty[0] = np.empty((0, 4))
    with pytest.raises(ValueError, match="nonempty historical"):
        study.calibrate(groups, empty)
    malformed = copy.deepcopy(groups)
    malformed[0] *= 2
    with pytest.raises(ValueError, match="nonunit"):
        study.calibrate(malformed, groups)
    malformed[0] = np.ones((9, 1))
    with pytest.raises(ValueError, match="matching dimensions"):
        study.calibrate(malformed, groups)


@pytest.mark.parametrize("field,value", [
    ("rank", 8), ("n", True), ("infinite", True), ("threshold", float("nan")),
])
def test_invalid_calibration_receipt_rejected(field, value):
    qs = quantiles([0] * 4)
    qs[0][field] = value
    with pytest.raises(ValueError, match="quantile|threshold"):
        study.decide(np.eye(4), qs)


def test_margin_match_exact_count_stable_id_ties_and_control_inclusive_cutoff():
    result = study.margin_match([.5, .5, .5, .2], ["c", "a", "b", "d"], 2)
    assert result["accepted"].tolist() == [False, True, True, False]
    assert result["boundary_id"] == "b"
    assert result["cutoff_ties"] == 3
    assert result["cutoff_ties_accepted"] == 2
    accepted, ties = study.control_margin_mask([.6, .5, .4], result)
    assert accepted.tolist() == [True, True, False]
    assert ties.tolist() == [False, True, False]
    reorder = [2, 0, 3, 1]
    reordered = study.margin_match(np.array([.5, .5, .5, .2])[reorder],
                                   np.array(["c", "a", "b", "d"])[reorder], 2)
    assert set(np.array(["c", "a", "b", "d"])[result["accepted"]]) == set(
        np.array(["c", "a", "b", "d"])[reorder][reordered["accepted"]])


def test_zero_and_full_margin_counts_preserve_control_semantics():
    empty = study.margin_match([.4, .7], ["a", "b"], 0)
    assert empty["cutoff"] is None
    assert not study.control_margin_mask([100., 0.], empty)[0].any()
    full = study.margin_match([.4, .7], ["a", "b"], 2)
    assert full["accepted"].all() and full["cutoff"] == .4
    assert study.control_margin_mask([.3, .4, .5], full)[0].tolist() == [False, True, True]
    with pytest.raises(ValueError, match="unique"):
        study.margin_match([.4, .7], ["a", "a"], 1)
    with pytest.raises(ValueError, match="acceptance count"):
        study.margin_match([.4, .7], ["a", "b"], True)


def test_summary_preserves_zero_acceptance_undefined_painter_risks_and_confusions():
    result = study.summarize_named(np.array([0, 0, 2, 1]), np.arange(4), np.zeros(4, bool))
    assert result["accepted_error"] is None
    assert result["abstained_error"] == .5
    assert result["unrestricted_error"] == .5
    assert result["coverage"] == 0
    assert result["accepted_correct"] == result["accepted_incorrect"] == 0
    assert all(p["accepted_error"] is None for p in result["per_painter"])
    assert np.sum(result["confusion"]) == np.sum(result["abstained_confusion"]) == 4


def test_correct_and_incorrect_acceptance_accounting_and_harm_are_not_hidden():
    result = study.summarize_named(np.array([1, 1, 2, 0]), np.arange(4),
                                   np.array([True, False, False, True]))
    assert result["accepted_error"] == 1
    assert result["unrestricted_error"] == .5
    assert result["abstained_error"] == 0
    assert result["accepted_incorrect"] == 2 and result["abstained_correct"] == 2
    assert result["per_painter"][1]["coverage"] == 0
    np.testing.assert_array_equal(np.array(result["accepted_confusion"])
                                  + result["abstained_confusion"], result["confusion"])


def test_model_evaluator_retains_all_arms_rows_and_scene_deletions():
    x, ids = generated_fixture()
    out = study.evaluate_model(x, ids, calibration())
    assert out["reference_gate"]["count"] == 24
    assert out["reference_gate"]["accepted_count"] == 24
    assert out["reference_gate"]["accepted_error"] == 0
    assert out["margin_comparator"]["accepted_count"] == 24
    assert len(out["observations"]) == 36
    assert len(out["scene_deletions"]) == 3
    for arm in ("free", "generic"):
        assert out["controls"][arm]["reference_gate"]["count"] == 6
        assert out["controls"][arm]["reference_gate"]["attribution_rate"] == 0
        assert out["controls"][arm]["margin_comparator"]["attribution_rate"] == 0
    for deletion in out["scene_deletions"]:
        assert deletion["deleted_scene"] not in deletion["retained_scenes"]
        assert deletion["reference_gate"]["count"] == 16
        assert deletion["reference_gate"]["accepted_count"] == 16
    json.dumps(out, allow_nan=False)


def test_selective_harm_and_success_have_explicit_counterexamples():
    x, ids = generated_fixture()
    # Large-margin incorrect images accepted; small-margin correct images rejected.
    x[0, 0, 2] = np.eye(4)[1]
    x[0, 1, 2] = np.array([.8, .6, 0, 0])
    out = study.evaluate_model(x, ids, calibration())
    assert out["baseline_minus_gate_risk"] < 0
    # Reverse confidence assignment without changing the incorrect image count.
    x[0, 0, 2] = np.array([.6, .8, 0, 0])
    x[0, 1, 2] = np.eye(4)[0]
    out = study.evaluate_model(x, ids, calibration())
    assert out["baseline_minus_gate_risk"] > 0
    assert out["reference_gate"]["accepted_incorrect"] == 0


def test_zero_gate_acceptance_propagates_through_model_and_influence():
    x, ids = generated_fixture()
    out = study.evaluate_model(x, ids, calibration(threshold=2.))
    assert out["reference_gate"]["accepted_count"] == 0
    assert out["reference_gate"]["accepted_error"] is None
    assert out["baseline_minus_gate_risk"] is None
    assert out["margin_minus_gate_risk"] is None
    assert out["comparator_cutoff"]["cutoff"] is None
    for key in ("baseline_minus_gate_risk", "margin_minus_gate_risk", "gate_accepted_error"):
        assert out["influence"][key]["range"] is None
        assert out["influence"][key]["missing_count"] == 3


def test_scene_deletion_rematches_margin_pool_and_keeps_reference_gate_fixed():
    x, ids = generated_fixture()
    x[0, :, 2:] = np.array([.8, .6, 0, 0])  # no gate accepts this scene's named images
    out = study.evaluate_model(x, ids, calibration())
    assert out["reference_gate"]["accepted_count"] == 16
    for deletion in out["scene_deletions"]:
        expected = 16 if deletion["deleted_scene"] == 0 else 8
        assert deletion["reference_gate"]["accepted_count"] == expected
        assert deletion["margin_comparator"]["accepted_count"] == expected
        assert deletion["comparator_cutoff"]["k"] == expected


def test_joint_criteria_strict_means_and_no_favorable_partial_average():
    x, ids = generated_fixture()
    base = study.evaluate_model(x, ids, calibration())
    models = [dict(model=f"synthetic-{i}", **copy.deepcopy(base)) for i in range(6)]
    # Exact ties cannot count as positive improvements.
    summary = study.summarize_setting(models)
    assert not summary["joint_usefulness"]
    assert not summary["criteria"]["positive_mean_margin_minus_gate"]
    for row in models:
        row["baseline_minus_gate_risk"] = .1
        row["margin_minus_gate_risk"] = .02
    assert study.summarize_setting(models)["joint_usefulness"]
    models[0]["margin_minus_gate_risk"] = None
    summary = study.summarize_setting(models)
    assert summary["mean_margin_minus_gate_risk"] is None
    assert summary["missing_means"] == ["margin_minus_gate"]
    assert not summary["joint_usefulness"]
    models[0]["reference_gate"]["per_painter"][2]["accepted_count"] = 0
    assert not study.summarize_setting(models)["criteria"][
        "every_painter_accepted_in_every_configuration"]
    assert study.complete_mean([.4, None, .7]) is None
    assert study.complete_mean([]) is None


def test_zero_coverage_setting_preserves_all_missing_mean_failure():
    x, ids = generated_fixture()
    base = study.evaluate_model(x, ids, calibration(threshold=2))
    out = study.summarize_setting([dict(model=f"synthetic-{i}", **base) for i in range(6)])
    assert out["configuration_count"] == 6
    assert out["missing_means"] == ["baseline_minus_gate", "margin_minus_gate"]
    assert len(out["failed_criteria"]) == 4
    assert not out["joint_usefulness"]


@pytest.mark.parametrize("change", ["nan", "zero", "shape", "duplicate_id", "id_shape"])
def test_invalid_generated_input_rejected(change):
    x, ids = generated_fixture()
    if change == "nan":
        x[0, 0, 0, 0] = np.nan
    elif change == "zero":
        x[0, 0, 0] = 0
    elif change == "shape":
        x = x[:, :, :5]
    elif change == "duplicate_id":
        ids[0, 0, 1] = ids[0, 0, 0]
    else:
        ids = ids[:, :, :5]
    with pytest.raises(ValueError):
        study.evaluate_model(x, ids, calibration())


def test_complex_bool_nonfinite_and_empty_score_inputs_rejected():
    for invalid in (np.eye(4).astype(complex), np.eye(4).astype(bool),
                    np.full((4, 4), np.inf), np.empty((0, 4)), np.eye(3)):
        with pytest.raises(ValueError):
            study.nonconformity(invalid)
