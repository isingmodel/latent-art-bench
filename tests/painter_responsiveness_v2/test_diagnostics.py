"""Synthetic scene geometry only; no research vectors, image pixels or network."""

import copy
import json

import numpy as np
import pytest

from latent_art_bench.painter_responsiveness_v2 import diagnostics as d


def retrieval(x, *, briefs=None, classes=None):
    x = np.asarray(x, dtype=float)
    n = len(x)
    briefs = briefs or [f"brief-{i}" for i in range(n)]
    ids = [[f"image-{i}-{r}" for r in range(3)] for i in range(n)]
    return d.retrieve(x, briefs, ids, classes or ["land"] * n)


def summary(result, scope="all_briefs"):
    return next(s for s in result["summaries"] if s["scope"] == scope)


def test_other_two_repetitions_only_enter_every_candidate_centroid():
    x = np.array([[[0.0], [1.0], [2.0]], [[1000.0], [11.0], [12.0]]])
    result = retrieval(x)
    query = next(r for r in result["predictions"] if r["image_id"] == "image-0-0"
                 and r["candidate_scope"] == "all_briefs")
    assert query["own_distance"] == 1.5
    assert query["nearest_other_distance"] == 11.5  # held 1000 is excluded too
    assert query["correct"] and query["midrank"] == 1
    x[0, 0, 0] = 100
    changed = retrieval(x)
    query = next(r for r in changed["predictions"] if r["image_id"] == "image-0-0"
                 and r["candidate_scope"] == "all_briefs")
    assert query["own_distance"] == 98.5  # no movement of its own training centroid


def test_uniform_positive_contraction_preserves_retrieval_despite_smaller_trace():
    x = np.array([[[0.0], [1.0], [2.0]], [[10.0], [11.0], [12.0]]])
    before, after = retrieval(x), retrieval(x * 0.5 + 4)
    assert summary(before)["top1_accuracy"] == summary(after)["top1_accuracy"] == 1
    assert summary(before)["mean_midrank"] == summary(after)["mean_midrank"] == 1
    assert after["between_brief_trace"] == 0.25 * before["between_brief_trace"]
    assert summary(after)["mean_own_distance"] == 0.5 * summary(before)["mean_own_distance"]


def test_contraction_can_improve_retrieval_when_within_scene_noise_decreases():
    before = retrieval([[[-5], [0], [5]], [[5], [10], [15]]])
    after = retrieval([[[2], [2], [2]], [[4], [4], [4]]])
    assert after["between_brief_trace"] < before["between_brief_trace"]
    assert summary(before)["top1_accuracy"] == pytest.approx(4 / 6)
    assert summary(after)["top1_accuracy"] == 1


def test_exact_ties_are_transparent_and_never_optimistically_counted():
    result = retrieval(np.zeros((4, 3, 2)), briefs=["b", "a", "d", "c"],
                       classes=["water", "water", "land", "land"])
    total, within = summary(result), summary(result, "same_content")
    assert total["top1_accuracy"] == total["fractional_tie_top1_accuracy"] == 0.25
    assert total["mean_midrank"] == total["mean_lexicographic_rank"] == 2.5
    assert total["queries_with_top_ties"] == 12
    assert within["top1_accuracy"] == within["chance_top1"] == 0.5
    first = next(r for r in result["predictions"] if r["candidate_scope"] == "all_briefs")
    assert first["predicted_brief_id"] == "a" and first["nearest_brief_ids"] == ["a", "b", "c", "d"]
    assert (first["rank_best"], first["rank_worst"], first["midrank"]) == (1, 4, 2.5)
    assert first["other_minus_own_distance"] == 0


def test_within_content_control_exposes_only_coarse_class_discrimination():
    x = np.zeros((4, 3, 1))
    x[2:] = 10
    result = retrieval(x, classes=["water", "water", "land", "land"])
    assert summary(result)["top1_accuracy"] > summary(result)["chance_top1"]
    within = summary(result, "same_content")
    assert within["top1_accuracy"] == within["chance_top1"] == 0.5
    assert summary(result)["between_brief_trace"] > 0
    assert within["between_brief_trace"] == 0


def bundle():
    briefs = [dict(brief_id=f"b{i:02d}", content_class=("water", "built", "land")[i // 8])
              for i in range(24)]
    rows = []
    for route in d.ROUTES:
        for painter in d.PAINTERS:
            for condition in d.CONDITIONS:
                for i, brief in enumerate(briefs):
                    for repetition in range(3):
                        image_id = f"{route}:{painter}:{condition}:{i}:{repetition}"
                        x = np.zeros(31)
                        x[i] = 10
                        x[30] = repetition * 0.1
                        if condition == "named":
                            x *= 0.5
                        for pipeline in d.PIPELINES:
                            rows.append(dict(route=route, painter_id=painter, pipeline=pipeline,
                                             condition=condition, repetition=repetition,
                                             image_id=image_id, status="measured",
                                             scaled=x.tolist(), **brief))
    return dict(config=dict(briefs=briefs, repetitions=3), generated=rows)


def test_full_inventory_shared_splits_and_views_are_exact_and_json_safe():
    source = bundle()
    result = d.analyze(source)
    assert result["counts"] == dict(
        cells=450, prediction_sets=180, splits=36, predictions=25920,
        selected_unique_images=864, selected_vector_rows=2592, new_images=0)
    assert {k: len(v) for k, v in result["views"].items()} == {
        "original31": 31, "color": 11, "spatial": 8, "texture": 12, "no_texture19": 19}
    for split in result["splits"]:
        training = {i for c in split["centroids"] for i in c["query_ids"]}
        query_ids = set(split["query_ids"])
        assert len(training) == 48 and len(query_ids) == 24 and not training & query_ids
        assert len({result["queries"][i]["image_id"] for i in training | query_ids}) == 72
        assert split["held_repetition"] not in split["training_repetitions"]
    for cell in result["cells"]:
        assert cell["before"]["condition"] == "artist_free"
        assert cell["after"]["condition"] == "named"
        chance = 1 / 24 if cell["candidate_scope"] == "all_briefs" else 1 / 8
        assert cell["before"]["chance_top1"] == pytest.approx(chance)
        if cell["before"]["between_brief_trace"] > 0:
            assert cell["named_free_between_brief_trace_ratio"] == pytest.approx(0.25)
        else:
            assert cell["named_free_between_brief_trace_ratio"] is None
        assert cell["named_minus_free"]["top1_accuracy"] == 0
    for row in result["predictions"]:
        query = result["queries"][row["query_id"]]
        prediction_set = result["prediction_sets"][row["prediction_set_id"]]
        assert all(query[k] == prediction_set[k] for k in ("route", "painter_id", "condition"))
    json.dumps(result, allow_nan=False)
    # Input row order is irrelevant; fixed class/brief/repetition identities determine every split.
    assert d.analyze(dict(source, generated=list(reversed(source["generated"])))) == result


@pytest.mark.parametrize("change", ["missing", "duplicate", "pipeline_identity", "content", "nan"])
def test_incomplete_or_inconsistent_grids_are_never_silently_filtered(change):
    source = bundle()
    if change == "missing":
        source["generated"].pop()
    elif change == "duplicate":
        source["generated"].append(copy.deepcopy(source["generated"][0]))
    elif change == "pipeline_identity":
        source["generated"][0]["image_id"] += "different"
    elif change == "content":
        source["generated"][0]["content_class"] = "land"
    else:
        source["generated"][0]["scaled"][2] = float("nan")
    with pytest.raises(ValueError):
        d.analyze(source)


def test_retrieval_rejects_duplicate_image_and_unsupported_singleton_content():
    with pytest.raises(ValueError, match="distinct image"):
        d.retrieve(np.zeros((2, 3, 1)), ["a", "b"], [["x"] * 3] * 2, ["land"] * 2)
    with pytest.raises(ValueError, match="at least two"):
        retrieval(np.zeros((2, 3, 1)), classes=["water", "land"])
