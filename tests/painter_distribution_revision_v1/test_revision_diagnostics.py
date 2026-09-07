"""Synthetic checks for revised finite-panel coverage and train/test boundaries."""

import json
from collections import Counter

import numpy as np
import pytest

from latent_art_bench.painter_distribution_revision_v1 import diagnostics as d
from latent_art_bench.painter_distribution_study_v1.analysis import classify, mass


def row(key, point, content="water", **kwargs):
    return dict(image_id=key, painter_id="monet", pipeline="primary512",
                scaled=list(point), content_class=content, **kwargs)


def fixture_rows():
    rng = np.random.default_rng(813)
    original, source, target = [], [], []
    for class_index, content in enumerate(("water", "built", "land")):
        for i in range(8):
            original.append(row(
                f"work{class_index}-{i}", rng.normal(0, 1, 31), content,
                normalization=dict(original_width=1100 + i * 10, original_height=1000,
                                   color_profile="missing_assumed_srgb"),
                native_short_side=1300 + i * 10,
            ))
        for brief in range(8):
            for repetition in range(2):
                brief_index = class_index * 8 + brief
                fields = dict(
                    brief_id=f"brief{brief_index}", brief_index=brief_index,
                    condition="named", repetition=repetition,
                    normalization=dict(original_width=1024, original_height=1024,
                                       color_profile="missing_assumed_srgb"),
                )
                source.append(row(f"source{brief_index}-{repetition}",
                                  rng.normal(2, 1, 31), content, route="source", **fields))
                target.append(row(f"target{brief_index}-{repetition}",
                                  rng.normal(2, 1, 31), content, route="target", **fields))
    return original, source, target


def test_neighbor_radius_excludes_self_and_counts_k_correctly():
    reference = [row(str(i), [x]) for i, x in enumerate((0, 2, 5))]
    radii, neighbors = d.neighbor_geometry(reference, 1)
    assert radii.tolist() == [2, 2, 3]
    assert neighbors.tolist() == [[1], [0], [1]]
    assert d.neighbor_geometry(reference, 2)[0].tolist() == [5, 3, 5]
    with pytest.raises(ValueError, match="smaller"):
        d.neighbor_geometry(reference, 3)


def test_largest_remainder_exact_total_and_deterministic_ties():
    assert d.largest_remainder({"water": 21, "built": 4, "land": 13}, 19) == {
        "built": 2, "land": 7, "water": 10,
    }
    assert d.largest_remainder({"b": 1, "a": 1}, 1) == {"a": 1, "b": 0}
    with pytest.raises(ValueError):
        d.largest_remainder({"a": 1}, 2)


def test_stratified_coverage_preserves_requested_class_mass_and_shared_draws():
    real, fake, _ = fixture_rows()
    # Deliberately imbalanced finite reference while retaining all content classes.
    real = real[:8] + real[8:11] + real[16:22]
    result = d.coverage_cell(real, fake, draws=4, key="synthetic")
    counts = dict(Counter(r["content_class"] for r in real))
    designs = result["sample_designs"]
    for design in designs:
        if design["mode"] == "reference_class_counts":
            expected = d.largest_remainder(counts, design["sample_size"])
            assert all(observed == expected for observed in design["observed_class_counts"])
        assert all(len(set(x)) == design["sample_size"] for x in design["generated_indices"])
    assert [r["k"] for r in result["k_results"]] == [1, 3, 5]
    # Every k refers to the same draw designs, so k comparisons do not change query images.
    assert all([c["sample_design_index"] for c in k["curves"]] == [0, 1, 2, 3]
               for k in result["k_results"])
    for k in result["k_results"]:
        for anchor in k["per_reference"]:
            assert anchor["generated_hit_count"] == (
                anchor["same_class_hit_count"] + anchor["cross_class_hit_count"]
            )
    json.dumps(result, allow_nan=False)


def test_stratified_queries_refuse_insufficient_class_support_without_resampling():
    real = [row(f"r{i}", [i], "water" if i < 7 else "land") for i in range(8)]
    fake = [row(f"g{i}", [i], "water" if i < 3 else "land") for i in range(8)]
    result = d.coverage_cell(real, fake, draws=3)
    designs = {(s["size_label"], s["mode"]): s for s in result["sample_designs"]}
    assert designs["reference_n", "reference_class_counts"]["status"] == "unavailable"
    assert designs["reference_n", "uniform"]["status"] == "available"


def test_heldout_control_has_disjoint_work_support_and_identical_anchor_radii():
    real, fake, _ = fixture_rows()
    design = d.heldout_design(real, draws=5, key="synthetic")
    for split in design["memberships"]:
        assert not set(split["anchor_indices"]) & set(split["real_query_indices"])
        for field in ("anchor_indices", "real_query_indices"):
            assert Counter(real[i]["content_class"] for i in split[field]) == {
                "water": 4, "built": 4, "land": 4,
            }
    result = d.heldout_coverage(real, fake, design, key="synthetic")
    first = design["memberships"][0]
    radii, _ = d.neighbor_geometry([real[i] for i in first["anchor_indices"]], 3)
    assert result["k_results"][1]["median_anchor_radius"][0] == np.median(radii)
    assert all(len(set(indices)) == 12 for indices in result["generated_query_indices"])
    assert d.heldout_design(real[:9])["status"] == "unavailable"
    json.dumps(result, allow_nan=False)


def test_square_metadata_rule_is_explicit_without_fitting():
    real, fake, _ = fixture_rows()
    result = d.square_baseline(real, fake)
    assert result["balanced_accuracy"] == pytest.approx(1)
    assert result["original_square_n"] == 0
    assert result["generated_square_n"] == len(fake)
    fake[0]["normalization"] = {}
    assert d.square_baseline(real, fake)["status"] == "unavailable"


def test_spearman_reports_constant_and_missing_descriptors_without_p_values():
    real, fake, _ = fixture_rows()
    summary = d.nuisance_summary(fake)
    assert all(a["status"] == "unavailable" for a in summary["associations"])
    summary = d.nuisance_summary(real)
    ratios = next(a for a in summary["associations"] if a["descriptor"] == "aspect_ratio")
    assert len(ratios["feature_spearman"]) == 31
    assert "pvalue" not in json.dumps(summary)
    json.dumps(summary, allow_nan=False)


def test_loader_metadata_keeps_unknown_borders_and_actual_image_format():
    _, fake, _ = fixture_rows()
    for row in fake:
        row.update(border_flag=None, image_format="PNG",
                   capture_workflow="not_applicable_generated")
    summary = d.nuisance_summary(fake)
    assert summary["metadata"]["border_counts"] == {"unknown": len(fake)}
    assert summary["metadata"]["format_counts"] == {"PNG": len(fake)}
    border = next(a for a in summary["associations"] if a["descriptor"] == "border_flag")
    assert border["status"] == "unavailable"
    assert border["n_available"] == 0
    assert d.descriptors(fake[0])["border_flag"] is None
    del fake[0]["border_flag"]
    fake[0]["image_format"] = None
    summary = d.nuisance_summary(fake)
    assert summary["metadata"]["border_counts"] == {"unknown": len(fake)}
    assert summary["metadata"]["format_counts"] == {"PNG": len(fake) - 1, "unknown": 1}
    json.dumps(summary, allow_nan=False)


def test_transfer_folds_exclude_same_work_and_every_repetition_of_test_brief():
    real, source, target = fixture_rows()
    design = d.transfer_membership(real, source, target)
    tested_real, tested_gen = [], []
    for split in design["memberships"]:
        assert not set(split["train_reference_indices"]) & set(split["test_reference_indices"])
        train_briefs = {source[i]["brief_id"] for i in split["train_source_indices"]}
        test_briefs = {target[i]["brief_id"] for i in split["test_target_indices"]}
        assert not train_briefs & test_briefs
        tested_real.extend(split["test_reference_indices"])
        tested_gen.extend(split["test_target_indices"])
    assert sorted(tested_real) == list(range(len(real)))
    assert sorted(tested_gen) == list(range(len(target)))
    target[0]["brief_index"] = 1  # Same content identity falsely assigned to a different fold.
    with pytest.raises(ValueError, match="leaks"):
        d.transfer_membership(real, source, target)


@pytest.mark.parametrize("kind", ["linear", "rbf"])
def test_same_route_limit_replays_existing_fixed_classifier(kind):
    real, fake, _ = fixture_rows()
    design = d.transfer_membership(real, fake, fake)
    revised = d.cross_route_classify(real, fake, fake, design, kind)
    existing = classify(real, fake, mass(real), "brief", kind)
    assert revised["pooled_threshold_metrics"]["balanced_accuracy"] == pytest.approx(
        existing["balanced_accuracy"]
    )
    assert revised["original_scores"] + revised["target_generated_scores"] == pytest.approx(
        [p["score"] for p in existing["predictions"]]
    )
    assert "auc" not in revised["pooled_threshold_metrics"]
    assert len(revised["fold_metrics"]) == 6
    assert all(0 <= f["auc"] <= 1 for f in revised["fold_metrics"])
    json.dumps(revised, allow_nan=False)


def test_transfer_cannot_train_with_reference_content_absent_in_source():
    real, fake, target = fixture_rows()
    fake = [r for r in fake if r["content_class"] != "water"]
    design = d.transfer_membership(real, fake, target)
    assert d.cross_route_classify(real, fake, target, design, "rbf")["status"] == "unavailable"


def test_complete_diagnostics_entry_point_is_json_native_and_keeps_unavailable_cases():
    real, source, target = fixture_rows()
    output = d.analyze(dict(reference=real, generated=source + target, development=[]))
    assert output["seed"] == "2026090719"
    assert len(output["coverage"]) == 2
    assert len(output["cross_route_transfer"]) == 4
    free = [r for r in output["cross_route_transfer"] if r["condition"] == "artist_free"]
    assert all(r["split"]["status"] == "unavailable" for r in free)
    assert output["source_holdout"]["status"] == "unavailable"
    assert len(output["heldout_reference_designs"][0]["memberships"]) == 100
    json.dumps(output, allow_nan=False)
