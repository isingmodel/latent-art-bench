"""Synthetic checks for post-result metric diagnostics; no retained study values."""

import copy
import json

import numpy as np
import pytest

from latent_art_bench.painter_distribution_revision_v1 import metrics as m


def rows(values, classes, briefs=None):
    return [dict(
        scaled=[float(v)] * 31, content_class=c, image_id=f"image{i}",
        brief_id=(briefs or list(range(len(values))))[i], repetition=i % 3, window=0,
    ) for i, (v, c) in enumerate(zip(values, classes))]


def synthetic_bundle():
    rng = np.random.default_rng(193)
    reference, generated, development, requests = [], [], [], []
    targets = {"a": {"water": 0.75, "land": 0.25}, "b": {"water": 0.25, "land": 0.75}}
    for painter in targets:
        for content in ("water", "land"):
            for repetition in range(3):
                vector = rng.normal(size=31).tolist()
                reference.append(dict(
                    image_id=f"reference:{painter}:{content}:{repetition}", pipeline="primary512",
                    painter_id=painter, content_class=content, scaled=vector, values=vector,
                    source_id=f"collection:{repetition % 2}",
                ))
            for brief in range(2):
                for repetition in range(3):
                    for condition in ("artist_free", "named"):
                        slot = f"slot{len(requests):04d}"
                        factor = 0.7 if condition == "named" else 1
                        vector = (rng.normal(size=31) * factor).tolist()
                        request = dict(
                            request_id=slot, route="route", painter_id=painter,
                            content_class=content, brief_id=content + str(brief),
                            repetition=repetition, window=brief, condition=condition,
                            payload=dict(prompt=content + str(brief) + (
                                painter if condition == "named" else ""
                            )),
                        )
                        requests.append(request)
                        generated.append(dict(
                            request, image_id="generated:" + slot, pipeline="primary512",
                            scaled=vector, values=vector,
                        ))
    for painter in ("d1", "d2", "d3", "d4"):
        for i in range(8):
            vector = rng.normal(size=31).tolist()
            development.append(dict(
                image_id=f"dev:{painter}:{i}", painter_id=painter, pipeline="primary512",
                content_class="water", scaled=vector, values=vector,
            ))
    return dict(
        reference=reference, generated=generated, development=development, requests=requests,
        targets=targets, config={}, timings={},
    )


def test_energy_terms_equal_hand_weighted_distances_and_are_symmetric():
    # X is equally weighted {0,2}; Y has masses {1/4,3/4} at {1,3}.
    # E|X-Y|=7/4, E|X-X'|=1, E|Y-Y'|=3/4, hence V-energy=7/4.
    x, y = np.array([[0.0], [2.0]]), np.array([[1.0], [3.0]])
    wx, wy = np.array([0.5, 0.5]), np.array([0.25, 0.75])
    value = m.energy_terms(x, y, wx, wy)
    assert value == pytest.approx(dict(
        energy=1.75, cross_twice=3.5, reference_within=1, generated_within=0.75
    ))
    assert m.energy_terms(y, x, wy, wx)["energy"] == pytest.approx(value["energy"])
    assert m.energy_terms(x, x, wx, wx)["energy"] == pytest.approx(0)
    with pytest.raises(ValueError, match="weights"):
        m.energy_terms(x, y, wx, [1, 1])


def test_feature_geometries_have_exact_declared_squared_contributions():
    x = np.ones((1, 31))
    assert m.feature_view(x, "original31").sum() == 31
    assert m.feature_view(np.arange(31)[None, :], "nonredundant28").tolist() == [
        [i for i in range(31) if i not in (10, 23, 24)]
    ]
    assert m.feature_view(x, "no_texture19").shape == (1, 19)
    transformed = m.feature_view(x, "family_balanced31")
    assert np.square(transformed[:, :11]).sum() == pytest.approx(1)
    assert np.square(transformed[:, 11:19]).sum() == pytest.approx(1)
    assert np.square(transformed[:, 19:]).sum() == pytest.approx(1)
    assert x.sum() == 31  # Transformations do not mutate caller vectors.
    with pytest.raises(ValueError, match="undeclared"):
        m.feature_view(x, "new_favorable_metric")


def test_content_weights_preserve_zero_mass_and_reject_missing_support():
    data = rows([0, 1, 2], ["water", "water", "land"])
    assert m.content_weights(data, {"water": 0.2, "land": 0.8}).tolist() == [0.1, 0.1, 0.8]
    assert m.content_weights(data, {"water": 1.0, "land": 0.0}).tolist() == [0.5, 0.5, 0]
    with pytest.raises(ValueError, match="support"):
        m.content_weights(data[:2], {"water": 0.2, "land": 0.8})
    assert m.distribution(data[:2], data, {"water": 0.2, "land": 0.8})["status"] == "unavailable"


def test_nested_variance_identity_and_increasing_within_brief_despite_total_contraction():
    # Equal-mass classes; each class has two briefs with two replicates.
    before = np.array([[-7], [-5], [-3], [-1], [1], [3], [5], [7]], dtype=float)
    after = np.array([[-4], [0], [-2], [2], [-2], [2], [0], [4]], dtype=float)
    metadata = rows(range(8), ["water"] * 4 + ["land"] * 4,
                    ["w0", "w0", "w1", "w1", "l0", "l0", "l1", "l1"])
    weights = np.full(8, 1 / 8)
    a = m.variance_parts(before, weights, metadata, generated=True)
    b = m.variance_parts(after, weights, metadata, generated=True)
    assert a["total_trace"] == pytest.approx(21)
    assert a["within_brief"] == pytest.approx(1)
    assert a["between_brief_within_class"] == pytest.approx(4)
    assert a["between_class"] == pytest.approx(16)
    assert b["total_trace"] < a["total_trace"]
    assert b["within_brief"] > a["within_brief"]
    assert b["identity_residual"] == pytest.approx(0)
    original = m.variance_parts(before, weights, metadata, generated=False)
    assert original["within_class"] == pytest.approx(5)
    assert original["between_class"] == pytest.approx(16)


def test_common_pairs_records_missing_both_sides_and_rejects_mismatches():
    before = rows([1, 2], ["water", "water"], ["w0", "w1"])
    after = copy.deepcopy(before[:1])
    after[0]["image_id"] = "second0"
    a, b, excluded = m.common_pairs(before, after, expected=[("w2", 0)])
    assert len(a) == len(b) == 1
    assert excluded == [
        dict(brief_id="w1", repetition=1, before_image_id="image1", after_image_id=None),
        dict(brief_id="w2", repetition=0, before_image_id=None, after_image_id=None),
    ]
    after[0]["window"] = 1
    with pytest.raises(ValueError, match="windows"):
        m.common_pairs(before, after)
    assert len(m.common_pairs(before, after, require_same_window=False)[0]) == 1
    with pytest.raises(ValueError, match="duplicate"):
        m.common_pairs(before + before, after)


def test_paired_energy_change_cancels_reference_self_term():
    reference = rows([0, 1, 4, 5], ["water", "water", "land", "land"])
    before = rows([1, 2, 6, 7], ["water", "water", "land", "land"])
    after = rows([1, 1, 3, 3], ["water", "water", "land", "land"])
    value = m.paired_summary(reference, before, after, {"water": 0.25, "land": 0.75}, "original31")
    terms = value["energy_term_changes"]
    assert terms["reference_within"] == 0
    assert value["energy_change"] == pytest.approx(terms["cross_twice"] - terms["generated_within"])
    assert value["n_pairs"] == 4


def test_complete_synthetic_grid_is_json_safe_and_preserves_all_metric_views():
    bundle = synthetic_bundle()
    frozen = json.dumps(bundle, sort_keys=True)
    result = m.analyze(bundle)
    assert len(result["cells"]) == 16  # Four route/painter/condition cells by four views.
    assert len(result["prompt_contrasts"]) == 8
    assert {r["metric_view"] for r in result["cells"]} == set(m.VIEWS)
    assert len(result["development_scaler_sensitivity"]) == 4
    assert all(r["status"] == "descriptive" for r in result["development_scaler_sensitivity"])
    assert json.loads(json.dumps(result, allow_nan=False)) == result
    assert json.dumps(bundle, sort_keys=True) == frozen
    assert json.dumps(m.analyze(bundle), sort_keys=True) == json.dumps(result, sort_keys=True)
    for row in result["trace_contributions"]:
        for domain in row["domains"]:
            assert sum(f["trace"] for f in domain["families"]) == pytest.approx(
                domain["total_trace"]
            )
            assert sum(c["fraction"] for c in domain["coordinates"]) == pytest.approx(1)


def test_cross_reference_interaction_cancels_both_self_terms_and_verifies_placebo():
    bundle = synthetic_bundle()
    rows_ = m._specificity(bundle["reference"], bundle["generated"], bundle["targets"],
                          ["route"], "original31", bundle["requests"])
    free = rows_[0]
    assert free["status"] == "descriptive"
    assert free["interaction_terms"]["reference_within"] == pytest.approx(0, abs=1e-12)
    assert free["interaction_terms"]["generated_within"] == pytest.approx(0, abs=1e-12)
    assert free["interaction_terms"]["energy"] == pytest.approx(
        free["interaction_terms"]["cross_twice"]
    )
    placebo = free["identical_payload_placebo"]
    assert placebo["status"] == "descriptive"
    assert len(placebo["verified_payload_pairs"]) == 12
    assert placebo["mismatched_pairs"] == []
    assert placebo["unverified_pairs"] == []
    bundle["requests"][0]["payload"] = dict(prompt="different")
    value = m._specificity(bundle["reference"], bundle["generated"], bundle["targets"],
                           ["route"], "original31", bundle["requests"])[0]
    assert value["identical_payload_placebo"]["status"] == "unavailable"
    assert len(value["identical_payload_placebo"]["mismatched_pairs"]) == 1


def test_reference_work_deletion_keeps_class_mass_and_class_deletion_changes_target():
    bundle = synthetic_bundle()
    values = m._reference_influence(
        bundle["reference"], bundle["generated"], bundle["targets"],
        [("route", "a")], bundle["requests"],
    )
    work = next(r for r in values if r["deletion_kind"] == "work")
    assert work["target"] == {"water": 0.75, "land": 0.25}
    assert work["n_pairs"] == 12
    assert len(work["dropped_reference_ids"]) == 1
    content = next(
        r for r in values if r["deletion_kind"] == "content_class" and r["omitted"] == "water"
    )
    assert content["target"] == {"land": 1}
    assert content["n_pairs"] == 6
    assert len(content["dropped_generated_ids"]) == 12
    source = next(r for r in values if r["deletion_kind"] == "source_id")
    assert source["target"] == {"water": 0.75, "land": 0.25}
    assert source["status"] == "descriptive"
    bundle["reference"] = [dict(r, source_id="unknown") for r in bundle["reference"]]
    values = m._reference_influence(
        bundle["reference"], bundle["generated"], bundle["targets"],
        [("route", "a")], bundle["requests"],
    )
    source = next(r for r in values if r["deletion_kind"] == "source_id")
    assert source["status"] == "unavailable"


def test_zero_development_iqr_is_unavailable_and_no_evaluation_fit_occurs():
    bundle = synthetic_bundle()
    development = [dict(r, scaled=[0.0] * 31) for r in bundle["development"]]
    values = m._development_scaler_sensitivity(
        development, bundle["reference"], bundle["generated"], bundle["targets"],
        *m._specs(bundle), bundle["requests"],
    )
    assert all(row["status"] == "unavailable" for row in values)
    assert all(len(row["invalid_coordinates"]) == 31 for row in values)
    correlations = m._development_correlations(development)
    assert correlations["correlation"] == [[None] * 31 for _ in range(31)]


def test_duplicate_or_nonfinite_vectors_fail_closed():
    bundle = synthetic_bundle()
    bundle["reference"].append(bundle["reference"][0])
    with pytest.raises(ValueError, match="duplicate"):
        m.analyze(bundle)
    bundle = synthetic_bundle()
    bundle["generated"][0]["scaled"][0] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        m.analyze(bundle)
