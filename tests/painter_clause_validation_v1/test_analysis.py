"""Prospective identity, missingness, fixed-fit and arithmetic integration checks."""

import copy
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from latent_art_bench.painter_clause_validation_v1 import analysis, common
from latent_art_bench.painter_distribution_study_v1.statistics import distribution_summary
from latent_art_bench.painter_naming_geometry_v1 import geometry

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def artificial():
    rng = np.random.default_rng(612)
    config = common.configuration(ROOT)
    requests = common.requests(ROOT)
    inputs = dict(
        schema="painter-clause-validation-inputs/1",
        targets={},
        reference={},
        original={},
        maps={},
        scalers={},
    )
    counts = dict(
        claude_monet=dict(water=21, built=4, land=13), paul_cezanne=dict(water=3, built=11, land=18)
    )
    for pipe in common.PIPELINES:
        inputs["reference"][pipe] = {}
        inputs["maps"][pipe] = {}
        inputs["original"][pipe] = {"oauth_gpt_image_2": {}}
        inputs["scalers"][pipe] = {"scaler": dict(center=[0.0] * 31, scale=[1.0] * 31)}
        for painter, classes in counts.items():
            n = sum(classes.values())
            inputs["targets"][painter] = {k: v / n for k, v in classes.items()}
            inputs["reference"][pipe][painter] = dict(
                ids=[f"ref-{painter}-{i}" for i in range(n)],
                values=rng.normal(size=(n, 31)).tolist(),
            )
            old_classes = [c for c in common.CLASSES for _ in range(8)]
            f = rng.normal(size=(24, 3, 31))
            named = 0.6 * f + 0.3
            old = dict(
                scene_ids=[f"old-{i:02}" for i in range(24)],
                classes=old_classes,
                repeat_ids=[0, 1, 2],
                free=f.tolist(),
                named=named.tolist(),
            )
            inputs["original"][pipe]["oauth_gpt_image_2"][painter] = old
            w = np.repeat([inputs["targets"][painter][c] / 24 for c in old_classes], 3)
            inputs["maps"][pipe][painter] = geometry.fit_map(
                f.reshape(-1, 31), named.reshape(-1, 31), w
            )
    rows = []
    for request in requests:
        for pipe in common.PIPELINES:
            x = rng.normal(size=31) + (0.7 if request["arm"] == "generic" else 0)
            rows.append(
                dict(
                    {k: v for k, v in request.items() if k != "payload"},
                    pipeline=pipe,
                    image_id=request["request_id"],
                    status="measured",
                    values=x.tolist(),
                    scaled=x.tolist(),
                )
            )
    receipt = dict(duration_contract_met=True, identity_contract_met=True, planned=len(requests))
    return requests, rows, inputs, config, receipt


def run(data):
    requests, rows, inputs, config, receipt = data
    return analysis.analyze(requests, rows, inputs, config, collection_receipt=receipt)


@pytest.fixture(scope="module")
def complete(artificial):
    return run(artificial)


def test_primary_direct_energy_and_two_endpoint_family(artificial, complete):
    assert len(complete["primary"]) == 2
    assert len(complete["views"]) == 6
    assert complete["measured_by_pipeline"] == dict.fromkeys(common.PIPELINES, 288)
    for row in complete["primary"]:
        view = next(
            v
            for v in complete["views"]
            if v["painter_id"] == row["painter_id"] and v["pipeline"] == "primary512"
        )
        arm = next(k for k, v in common.PAINTERS.items() if v == row["painter_id"])
        assert row["estimate"] == pytest.approx(view["contrasts"][arm + "_minus_generic"])
        assert sum(row["contributions"]) == pytest.approx(row["estimate"])
        assert len(row["contributions"]) == 72
        assert row["status"] == "available" and row["interval"] is None
        assert 0 < row["raw_p"] <= row["holm_p"] <= 1
        assert row["ordered_pairs"] == sorted(row["ordered_pairs"])
    assert "No non-rejection establishes equivalence" in analysis.report_text(complete)


def test_maps_are_fixed_original_fits(artificial, complete):
    requests, rows, inputs, config, _ = artificial
    slots, classes = analysis.validate_design(requests, config)
    indexed = {(r["request_id"], r["pipeline"]): r for r in rows}
    for view in complete["views"]:
        pipe, painter = view["pipeline"], view["painter_id"]
        free = np.array(
            [
                indexed[slots[s, r, "free"]["request_id"], pipe]["scaled"]
                for s in sorted(classes)
                for r in range(3)
            ]
        )
        old = inputs["maps"][pipe][painter]
        assert view["historical_fit"] == old
        for kind in ("translation", "translation_scale"):
            y = np.asarray(old["named_mean"]) + (
                old["scale"] if kind == "translation_scale" else 1
            ) * (free - old["free_mean"])
            expected = distribution_summary(
                inputs["reference"][pipe][painter]["values"],
                y,
                generated_weights=view["generated_weights"],
            )
            assert view["maps"][kind]["energy_terms"]["energy"] == pytest.approx(
                expected["energy_distance"]
            )
            assert "raw_p" not in view["maps"][kind]


@pytest.mark.parametrize(
    "arm,available", [("generic", 0), ("monet", 1), ("cezanne", 1), ("free", 2)]
)
def test_allocated_pair_completeness_not_posthoc_complete_cases(artificial, arm, available):
    data = copy.deepcopy(artificial)
    row = next(r for r in data[1] if r["arm"] == arm and r["pipeline"] == "primary512")
    row.update(status="measurement_failed", values=None, scaled=None)
    result = run(data)
    assert sum(r["status"] == "available" for r in result["primary"]) == available
    for row in result["primary"]:
        if row["status"] != "available":
            assert row["raw_p"] is None and row["holm_p"] == 1 and not row["reject"]


@pytest.mark.parametrize(
    "receipt",
    [
        None,
        {},
        {"duration_contract_met": False, "planned": 288},
        {"duration_contract_met": 1, "planned": 288},
        {"duration_contract_met": True, "planned": 287},
    ],
)
def test_no_inference_without_terminal_collection_contract(artificial, receipt):
    data = list(artificial)
    data[-1] = receipt
    result = run(data)
    assert all(
        r["status"] == "withheld_collection_contract"
        and r["holm_p"] == 1
        and r["raw_p"] is None
        and not r["reject"]
        for r in result["primary"]
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("arm", "free"),
        ("sequence", 99),
        ("repetition", 9),
        ("content_class", "new"),
        ("route", "flux_2_max"),
    ],
)
def test_measurement_assignment_cannot_change(artificial, field, value):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    rows[0][field] = value if rows[0][field] != value else "changed"
    with pytest.raises(ValueError, match="assigned request identity"):
        analysis.validate_measurements(requests, rows, inputs)


def test_missing_duplicate_and_nonfinite_measurements_rejected(artificial):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    with pytest.raises(ValueError, match="terminal accounting"):
        analysis.validate_measurements(requests, rows[:-1], inputs)
    with pytest.raises(ValueError, match="duplicate"):
        analysis.validate_measurements(requests, rows + [rows[0]], inputs)
    rows[0]["values"][0] = float("nan")
    with pytest.raises(ValueError, match="finite vectors"):
        analysis.validate_measurements(requests, rows, inputs)


def test_changed_scaler_and_outcome_fitted_map_rejected(artificial):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    rows[0]["scaled"][0] += 0.01
    with pytest.raises(ValueError, match="changed scaler"):
        analysis.validate_measurements(requests, rows, inputs)
    inputs["maps"]["primary512"]["claude_monet"]["scale"] *= 0.99
    with pytest.raises(ValueError, match="historical map"):
        analysis.validate_inputs(inputs)


def test_prospective_inventory_uses_four_clauses_and_no_palette_extremes():
    requests = common.requests(ROOT)
    assert requests == common.requests(ROOT)
    assert len(requests) == 288
    assert Counter(r["arm"] for r in requests) == dict.fromkeys(common.ARMS, 72)
    for r in requests:
        assert r["payload"]["model"] == "gpt-image-2"
        assert "muted, low-chroma" not in r["payload"]["prompt"]
        assert "vivid, high-chroma" not in r["payload"]["prompt"]
    common.configuration(ROOT)
    analysis.validate_design(requests, common.configuration(ROOT))


def test_retrieval_known_geometry_translation_scaling_and_ties():
    values = np.repeat(np.arange(6)[:, None, None], 3, axis=1).astype(float)
    ids = [f"s{i}" for i in range(6)]
    classes = ["a"] * 3 + ["b"] * 3
    first = analysis.retrieval(values, ids, classes)
    assert first["all_scenes_accuracy"] == 1
    shifted = analysis.retrieval(values * 0.3 + 7, ids, classes)
    assert shifted == first
    ties = analysis.retrieval(np.zeros((6, 3, 1)), ids, classes)
    assert ties["all_scenes_accuracy"] == pytest.approx(1 / 6)
    assert ties["within_class_accuracy"] == pytest.approx(1 / 3)


@pytest.mark.parametrize("identity", [None, False, 1, "true"])
def test_identity_gate_cannot_be_replaced_by_complete_pairs(artificial, identity):
    data = copy.deepcopy(artificial)
    data[-1].update(identity_contract_met=identity, reason="proxy_identity_changed")
    result = run(data)
    assert all(
        r["estimate"] is not None
        and r["status"] == "withheld_collection_contract"
        and r["raw_p"] is None
        and r["holm_p"] == 1
        for r in result["primary"]
    )


def test_map_energy_survives_missing_named_but_not_conditional_target(artificial):
    data = copy.deepcopy(artificial)
    row = next(r for r in data[1] if r["arm"] == "monet" and r["pipeline"] == "primary512")
    row.update(status="measurement_failed", values=None, scaled=None)
    result = run(data)
    view = next(
        v
        for v in result["views"]
        if v["painter_id"] == "claude_monet" and v["pipeline"] == "primary512"
    )
    assert len(view["maps"]) == 2
    assert all(np.isfinite(m["energy_terms"]["energy"]) for m in view["maps"].values())
    assert view["map_target_differences"]["conditional_residual_t2_minus_t1"] is None
    assert np.isfinite(view["map_target_differences"]["energy_t2_minus_t1"])


def test_explicit_secondary_ratios_and_differences(complete):
    for view in complete["views"]:
        arm = next(k for k, v in common.PAINTERS.items() if v == view["painter_id"])
        totals = {
            k: v["variance_reference_weight"]["observed_total"] for k, v in view["arms"].items()
        }
        assert (
            view["trace_ratios"]["generic_over_free"]["ratio"] == totals["generic"] / totals["free"]
        )
        assert (
            view["trace_ratios"]["named_over_generic"]["ratio"] == totals[arm] / totals["generic"]
        )
        maps = view["maps"]
        diff = view["map_target_differences"]
        assert diff["energy_t2_minus_t1"] == (
            maps["translation_scale"]["energy_terms"]["energy"]
            - maps["translation"]["energy_terms"]["energy"]
        )
        assert diff["conditional_residual_t2_minus_t1"] == (
            maps["translation_scale"]["conditional_residual"]["cross_repeat_mean_square"]
            - maps["translation"]["conditional_residual"]["cross_repeat_mean_square"]
        )


def test_undefined_ratio_is_not_clipped_or_replaced_by_one():
    arms = {
        k: dict(status="descriptive", variance_reference_weight=dict(observed_total=0))
        for k in ("free", "generic")
    }
    assert analysis.trace_ratio(arms, "generic", "free") == dict(
        status="unavailable_zero_denominator", ratio=None
    )
    arms["generic"]["status"] = "unavailable"
    assert analysis.trace_ratio(arms, "generic", "free")["status"] == "unavailable_incomplete_arm"


def test_delivery_counts_outputs_once_and_retains_quality_field(artificial):
    rows = copy.deepcopy(artificial[1])
    for row in rows:
        row["observed"] = dict(width=1536, height=1024, format="PNG", reported={"quality": "low"})
    summary = analysis.delivery_summary(rows)
    assert all(r["planned"] == 72 and r["observed_outputs"] == 72 for r in summary.values())
    assert all(r["reported_quality"] == {"low": 72} for r in summary.values())
    assert all(r["dimensions"] == {"1536x1024": 72} for r in summary.values())
