"""Offline synthetic checks of the new retained-vector diagnostic contract."""

from copy import deepcopy

import numpy as np
import pytest

from latent_art_bench.painter_responsiveness_v1.analysis import (
    CHROMA,
    PAINTERS,
    PIPELINES,
    ROUTES,
    _summarize_scope,
    analyze,
)


def vectors(first_coordinate):
    values = np.zeros((*np.asarray(first_coordinate).shape, 31))
    values[..., 0] = first_coordinate
    return values


def test_noiseless_product_recovers_between_brief_trace_and_scaling():
    before = vectors([[-2, -2, -2], [0, 0, 0], [2, 2, 2]])
    after = 2 * before + np.ones(31) * 3
    result = _summarize_scope(before, after, ["a", "b", "c"], "all")
    assert result["before"]["within_brief_trace"] == 0
    assert result["before"]["between_brief_trace"] == pytest.approx(8 / 3)
    assert result["before"]["cross_repeat_between_trace"] == pytest.approx(8 / 3)
    assert result["after"]["cross_repeat_between_trace"] == pytest.approx(32 / 3)
    assert result["changes"]["cross_repeat_between_trace"] == pytest.approx(8)
    assert sum(r["change_total"] for r in result["coordinates"]) == pytest.approx(8)
    assert sum(r["change_total"] for r in result["families"]) == pytest.approx(8)


def test_negative_cross_repetition_product_is_not_clipped():
    before = vectors([[1, -1, 0], [-1, 1, 0]])
    result = _summarize_scope(before, before, ["a", "b"], "all")
    assert result["before"]["between_brief_trace"] == 0
    assert result["before"]["cross_repeat_between_trace"] == pytest.approx(-1 / 3)
    assert [p["product"] for p in result["before"]["cross_repeat_pairs"]] == [-1, 0, 0]
    assert result["changes"]["cross_repeat_between_trace"] == 0


def test_repeat_specific_common_shifts_cancel_in_centered_products():
    before = vectors([[-2, -2, -2], [2, 2, 2]])
    shifted = before + vectors([[3, -7, 8]])
    result = _summarize_scope(before, shifted, ["a", "b"], "all")
    assert result["before"]["cross_repeat_between_trace"] == 4
    assert result["after"]["cross_repeat_between_trace"] == 4
    assert result["after"]["within_brief_trace"] > 0


@pytest.fixture
def bundle():
    briefs = [dict(brief_id="b1", content_class="built", detailed="A building."),
              dict(brief_id="w1", content_class="water", detailed="A river.")]
    result = dict(generated=[], reference=[], requests=[],
                  config=dict(briefs=briefs, repetitions=3),
                  scalers={"primary512": {"scaler": dict(center=[10.] * 31, scale=[2.] * 31)}})
    for route in ROUTES:
        for painter in PAINTERS:
            for b, brief in enumerate(briefs):
                for repetition in range(3):
                    for condition in ("artist_free", "named"):
                        slot = f"{route}:{painter}:{b}:{repetition}:{condition}"
                        values = np.zeros(31)
                        values[0] = b + repetition / 10 + (condition == "named")
                        row = dict(
                            route=route, painter_id=painter, brief_id=brief["brief_id"],
                            content_class=brief["content_class"], repetition=repetition,
                            condition=condition, request_id=slot, image_id="generated:" + slot,
                            pipeline="primary512", status="measured", values=values.tolist(),
                            scaled=values.tolist(), reported_quality="low",
                        )
                        result["generated"].append(row)
                        result["requests"].append(dict(row, payload={"quality": "medium"}))
    for painter in PAINTERS:
        for i, pipeline in enumerate(PIPELINES):
            values = np.zeros(31)
            values[CHROMA] = 12 + 2 * i
            result["reference"].append(dict(
                image_id="real:" + painter, painter_id=painter, content_class="water",
                subject_subcategory="a free-text subject", pipeline=pipeline, status="measured",
                values=values.tolist(), scaled=values.tolist(), capture_workflow="unresolved",
            ))
    return result


def test_analysis_retains_all_pairs_and_fails_fine_content_feasibility(bundle):
    result = analyze(bundle)
    assert result["source_counts"]["analyzed_named_free_pairs"] == 36
    assert len(result["cells"]) == 6
    assert result["cells"][0]["briefs"][0]["before_image_ids"]
    assert result["cells"][0]["scopes"][1]["status"] == "single_brief_no_between_brief_support"
    support = result["reference_chroma"]
    assert support["fine_content_feasibility"]["status"] == "unavailable"
    assert support["fine_content_feasibility"]["reference_holdout_available"] is False
    assert support["subject_label_inventory"][0]["maximum_works_per_exact_label"] == 1
    assert sum(g["n"] for g in result["service_quality"]["groups"]) == 72


def test_chroma_uses_one_primary_scale_for_all_pipelines(bundle):
    result = analyze(bundle)["reference_chroma"]
    work = result["works"][0]
    assert work["common_primary_scaled_chroma"] == dict(primary512=1, resolution256=2, jpeg90_512=3)
    assert work["pipeline_span_primary_iqr_units"] == 2
    assert work["raw_pipeline_span"] == 4
    singleton = result["groups"][0]
    assert singleton["raw"]["minimum"] == singleton["raw"]["maximum"]
    assert singleton["support_status"] == "singleton_no_within_stratum_variation"


def test_missing_matched_generation_is_not_silently_dropped(bundle):
    bundle["generated"].pop()
    with pytest.raises(ValueError, match="complete matched design"):
        analyze(bundle)


def test_duplicate_measurement_and_nonfinite_vector_fail(bundle):
    malformed = deepcopy(bundle)
    malformed["generated"].append(malformed["generated"][0])
    with pytest.raises(ValueError, match="duplicate generated"):
        analyze(malformed)
    bundle["generated"][0]["scaled"][0] = float("nan")
    with pytest.raises(ValueError, match="finite vectors"):
        analyze(bundle)


def test_request_identity_mismatch_fails(bundle):
    bundle["requests"][0]["condition"] = "wrong"
    with pytest.raises(ValueError, match="identities disagree"):
        analyze(bundle)


def test_three_pipeline_reference_identity_support_is_required(bundle):
    bundle["reference"].pop()
    with pytest.raises(ValueError, match="matching work identities"):
        analyze(bundle)
