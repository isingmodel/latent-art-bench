"""Offline synthetic checks of the computational-only successor analysis."""

import json
from copy import deepcopy

import numpy as np
import pytest

from latent_art_bench.painter_distribution_study_v1.study import PIPELINES
from latent_art_bench.painter_responsiveness_v1.design import ARMS, make_schedule
from latent_art_bench.painter_responsiveness_v2.analysis import (
    PAINTERS,
    _quantiles,
    analyze,
)


@pytest.fixture
def study():
    templates = ["built_one", "built_two", "land_one", "land_two", "water_one", "water_two"]
    requests = make_schedule(templates, seed=907, repetitions=4)
    for row in requests:
        row["content_class"] = row["template_id"].split("_")[0]
    config = dict(feature_index=2, primary_pipeline="primary512", primary_chroma_center=10.0,
                  primary_chroma_scale=2.0, route="synthetic_offline", alpha=0.05)
    generated = []
    for r in requests:
        arm_index = ARMS.index(r["arm"])
        response = (20, 20, 5, 10)[arm_index]
        sign = -1 if r["polarity"] == "muted" else 1
        for pipeline_index, pipeline in enumerate(PIPELINES):
            value = (50 + templates.index(r["template_id"]) + response * sign / 2
                     + (r["repetition"] - 1.5) * (1 + 0.2 * (arm_index + 1) * sign)
                     + pipeline_index * 10)
            vector = [float(i) for i in range(31)]
            vector[0] += sign * (arm_index + 1)
            vector[2] = value
            scaled = list(vector)
            scaled[2] = (value - 10) / 2 if pipeline == "primary512" else 999.0
            generated.append(dict(r, pipeline=pipeline, status="measured", values=vector,
                                  scaled=scaled, chroma_primary_iqr=(value - 10) / 2))
    refs = []
    for painter in PAINTERS:
        for content in ("built", "land", "water"):
            # Unequal class counts expose accidental empirical/equal-class conflation.
            for repeat in range({"built": 2, "land": 3, "water": 5}[content]):
                for pipeline_index, pipeline in enumerate(PIPELINES):
                    vector = [0.0] * 31
                    vector[2] = 35 + {"built": 0, "land": 12, "water": 24}[content]
                    vector[2] += repeat + pipeline_index * 10
                    refs.append(dict(image_id=f"{painter}:{content}:{repeat}",
                                     painter_id=painter, content_class=content,
                                     pipeline=pipeline, status="measured", values=vector))
    return requests, generated, refs, config


def test_shared_control_interaction_matches_known_response_and_json(study):
    result = analyze(*study)
    assert result["counts"] == dict(planned_images=192, measured_by_pipeline={
        p: 192 for p in PIPELINES}, reference_images=20, human_ratings=0)
    assert [r["estimate"] for r in result["primary"]["primary"]] == pytest.approx([-7.5, -5])
    assert result["primary"]["primary_covariance"][0][1] > 0
    assert all(r["reject_holm"] for r in result["primary"]["primary"])
    assert [r["verdict"] for r in result["computational_interpretation"]["painters"]] == [
        "smaller_positive_named_chroma_response", "smaller_positive_named_chroma_response"]
    json.dumps(result, allow_nan=False)
    assert result == analyze(*study)


def test_processing_sensitivity_uses_common_raw_scale_not_pipeline_scaler(study):
    result = analyze(*study)
    for sensitivity in result["processing_sensitivity"].values():
        assert [r["estimate"] for r in sensitivity["primary"]] == pytest.approx([-7.5, -5])
        assert all("p_holm" not in r and "p_two_sided" not in r for r in sensitivity["primary"])
        assert "Descriptive" in sensitivity["scope"]
    means = [result["primary"]["arm_means"][0]["mean"]] + [
        result["processing_sensitivity"][p]["arm_means"][0]["mean"] for p in PIPELINES[1:]]
    assert np.diff(means) == pytest.approx([5, 5])


def test_all_coordinates_have_point_estimates_and_template_counterexamples(study):
    result = analyze(*study)["all_coordinate_responses"]
    assert result["status"] == "complete_descriptive"
    assert len(result["coordinates"]) == 31
    chroma = result["coordinates"][2]
    assert chroma["interactions"] == pytest.approx(dict(monet_minus_generic=-7.5,
                                                       cezanne_minus_generic=-5))
    assert len(chroma["template_responses"]) == 6
    assert result["coordinates"][0]["interactions"] == pytest.approx(
        dict(monet_minus_generic=2, cezanne_minus_generic=4))
    assert "p_value" not in json.dumps(result)


@pytest.mark.parametrize("missing", ["explicit", "omitted"])
def test_any_missing_primary_slot_withholds_inference_and_preserves_allocation(study, missing):
    requests, generated, references, config = deepcopy(study)
    identity = generated[0]["request_id"]
    if missing == "explicit":
        generated[0].update(status="http_error", values=None, scaled=None, chroma_primary_iqr=None)
    else:
        generated.pop(0)
    result = analyze(requests, generated, references, config)
    assert result["primary"]["primary"] is None
    assert result["counts"]["measured_by_pipeline"]["primary512"] == 191
    assert len(result["generated_chroma"]) == 576
    assert result["all_coordinate_responses"]["unavailable_request_ids"] == [identity]
    affected = [r for r in result["reference_context"]["comparisons"]
                if identity in r["unavailable_request_ids"]]
    assert affected and all(r["status"] == "descriptive_selected_available" for r in affected)
    assert all(r["allocated"] > r["measured"] for r in affected)


def test_reference_bridge_retains_exact_weights_and_distinguishes_reference_mixtures(study):
    bridge = analyze(*study)["reference_context"]
    assert len(bridge["envelopes"]) == 12
    assert len(bridge["comparisons"]) == 144
    empirical, equal = bridge["envelopes"][:2]
    assert empirical["image_ids"] == equal["image_ids"]
    assert empirical["summary"]["weighted_mean"] != equal["summary"]["weighted_mean"]
    assert sum(equal["weights"]) == pytest.approx(1)
    for content in ("built", "land", "water"):
        weight = sum(w for identity, w in zip(equal["image_ids"], equal["weights"], strict=True)
                     if f":{content}:" in identity)
        assert weight == pytest.approx(1 / 3)
    item = bridge["comparisons"][0]
    assert item["allocated"] == item["measured"] == 24
    assert len(item["request_ids"]) == len(item["generated_weights"]) == 24
    assert item["wasserstein_1"] >= 0
    assert 0 <= item["generated_mass_in_reference_central80"] <= 1
    assert "single maintainer-run LLM" in bridge["scope"]


def test_reference_missing_class_is_unavailable_without_renormalizing_target(study):
    requests, generated, references, config = study
    references = [r for r in references if not (r["painter_id"] == PAINTERS[0]
                                               and r["content_class"] == "built")]
    bridge = analyze(requests, generated, references, config)["reference_context"]
    affected = [r for r in bridge["comparisons"] if r["painter_id"] == PAINTERS[0]
                and r["reference_weighting"] == "equal_broad_class"]
    assert all(r["status"] == "unavailable_stratum" for r in affected)
    assert all(r["wasserstein_1"] is None for r in affected)


def test_empirical_quantile_definition_is_weighted_cdf_inverse():
    assert _quantiles([10, 1, 2], [0.2, 0.2, 0.6]) == [1, 2, 10]
    assert _quantiles([7, 7, 7], [0.1, 0.4, 0.5]) == [7, 7, 7]


@pytest.mark.parametrize("defect", ["duplicate", "treatment", "nonfinite", "wrong_scale",
                                    "reference_missing_pipeline", "reference_identity"])
def test_treatment_measurement_and_reference_integrity_fail_closed(study, defect):
    requests, generated, references, config = deepcopy(study)
    if defect == "duplicate":
        generated.append(deepcopy(generated[0]))
    elif defect == "treatment":
        generated[0]["arm"] = "unplanned"
    elif defect == "nonfinite":
        generated[0]["values"][4] = float("nan")
    elif defect == "wrong_scale":
        generated[0]["chroma_primary_iqr"] = 999
    elif defect == "reference_missing_pipeline":
        references.pop(0)
    else:
        references[0]["painter_id"] = PAINTERS[1]
    with pytest.raises(ValueError):
        analyze(requests, generated, references, config)


def test_reversed_named_response_is_not_called_attenuation(study):
    requests, generated, references, config = deepcopy(study)
    for row in generated:
        if row["arm"] == "monet":
            sign = -1 if row["polarity"] == "muted" else 1
            row["values"][2] -= 10 * sign
            row["chroma_primary_iqr"] = (row["values"][2] - 10) / 2
            row["scaled"][2] = row["chroma_primary_iqr"]
    result = analyze(requests, generated, references, config)
    assert result["computational_interpretation"]["painters"][0]["verdict"] == (
        "negative_interaction_with_named_response_reversal")


def test_nonresponsive_controls_prevent_attenuation_verdict(study):
    requests, generated, references, config = deepcopy(study)
    for row in generated:
        sign = -1 if row["polarity"] == "muted" else 1
        if row["arm"] in ("free", "generic"):
            row["values"][2] -= 10 * sign
            row["chroma_primary_iqr"] = (row["values"][2] - 10) / 2
            row["scaled"][2] = row["chroma_primary_iqr"]
    result = analyze(requests, generated, references, config)
    assert not result["computational_interpretation"]["controls_nominal_intervals_positive"]
    assert all(r["verdict"] == "positive_interaction_without_established_positive_controls"
               for r in result["computational_interpretation"]["painters"])
