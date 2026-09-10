"""Measurement-contract tests and non-inferential numerical edge cases."""

from copy import deepcopy

import numpy as np
import pytest

from latent_art_bench.painter_map_validation_v2 import analysis as a


@pytest.fixture
def inputs():
    return dict(
        schema="painter-map-validation-inputs/2",
        origins=a.ORIGINS.copy(),
        pipeline=a.PIPELINE,
        painter_id=a.PAINTER,
        features=list(a.NAMES),
        targets=a.primitive.MASSES.copy(),
        reference=dict(
            ids=[f"invented_ref_{i}" for i in range(32)], values=np.zeros((32, 31)).tolist()
        ),
        scaler=dict(center=np.arange(31).tolist(), scale=np.linspace(1, 4, 31).tolist()),
        fitted=dict(
            free_mean=np.zeros(31).tolist(),
            named_mean=np.ones(31).tolist(),
            scale=0.6785365094757265,
        ),
    )


@pytest.fixture
def measurements(inputs):
    from pathlib import Path

    from latent_art_bench.painter_map_validation_v2 import common

    requests = common.build_plan(Path(__file__).resolve().parents[2], common.expected_config())
    rows = []
    rng = np.random.default_rng(34923)
    for request in requests:
        raw = rng.normal(size=31)
        scaled = (raw - inputs["scaler"]["center"]) / inputs["scaler"]["scale"]
        item = {k: v for k, v in request.items() if k != "payload"}
        rows.append(
            dict(
                item,
                pipeline=a.PIPELINE,
                status="measured",
                feature_names=list(a.NAMES),
                values=raw.tolist(),
                scaled=scaled.tolist(),
            )
        )
    return requests, rows


def test_measurement_grid_and_exact_scaling(inputs, measurements):
    a.validate_inputs(inputs)
    requests, rows = measurements
    selected = a.validate_measurements(requests, rows[::-1], inputs)
    assert len(selected) == 240
    changed = deepcopy(rows)
    changed[0]["scaled"][0] = np.nextafter(changed[0]["scaled"][0], np.inf)
    with pytest.raises(ValueError, match="development transformation"):
        a.validate_measurements(requests, changed, inputs)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "pipeline",
        "identity",
        "features",
        "nan",
        "absent_status",
        "failed_vector",
    ],
)
def test_reject_malformed_or_incomplete_measurement_inventory(fault, inputs, measurements):
    requests, rows = measurements
    if fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows[-1] = deepcopy(rows[0])
    elif fault == "pipeline":
        rows[0]["pipeline"] = "resolution256"
    elif fault == "identity":
        rows[0]["repetition"] = (rows[0]["repetition"] + 1) % 10
    elif fault == "features":
        rows[0]["feature_names"].reverse()
    elif fault == "nan":
        rows[0]["values"][0] = float("nan")
    elif fault == "absent_status":
        rows[0].pop("status")
    else:
        rows[0]["status"] = "normalization_failed"
    with pytest.raises(ValueError):
        a.validate_measurements(requests, rows, inputs)


def test_failed_slot_requires_explicit_empty_values(inputs, measurements):
    requests, rows = measurements
    rows[0].update(status="normalization_failed", values=None, scaled=None)
    assert (
        a.validate_measurements(requests, rows, inputs)[rows[0]["request_id"]]["status"]
        == "normalization_failed"
    )


@pytest.mark.parametrize("field", ["sequence", "repetition"])
def test_numeric_identity_types_cannot_alias_integers(inputs, measurements, field):
    requests, rows = measurements
    row = next(row for row in rows if row[field] == 0)
    row[field] = 0.0 if field == "sequence" else False
    with pytest.raises(ValueError, match="identity"):
        a.validate_measurements(requests, rows, inputs)


@pytest.mark.parametrize(
    "fault", ["origin", "scale", "reference_ids", "feature_order", "map_scale"]
)
def test_fixed_input_contract_rejects_changes(inputs, fault):
    if fault == "origin":
        inputs["origins"][next(iter(inputs["origins"]))] = "0" * 64
    elif fault == "scale":
        inputs["scaler"]["scale"][0] = 0
    elif fault == "reference_ids":
        inputs["reference"]["ids"][0] = inputs["reference"]["ids"][1]
    elif fault == "feature_order":
        inputs["features"].reverse()
    else:
        inputs["fitted"]["scale"] = 0.7
    with pytest.raises(ValueError):
        a.validate_inputs(inputs)


def test_no_variance_withholds_both_intervals_but_keeps_finite_points():
    free = np.zeros((2, 10, 2))
    named = np.ones_like(free)
    fitted = dict(free_mean=[0, 0], named_mean=[1, 1], scale=0.6)
    result = a.analyze_arrays(free, named, [[0, 0], [1, 1]], [0.2, 0.8], fitted)
    assert result["status"] == "descriptive_points_only"
    assert result["joint_direction"] == "unavailable"
    assert all(row["estimate"] == 0 and row["interval"] is None for row in result["primary"])
    assert result["components"]["Q_T1"] == 0
    assert result["components"]["Q_T2"] == 0


def test_negative_q_is_retained_without_truncation():
    free = np.zeros((2, 10, 2))
    named = np.zeros_like(free)
    named[:, ::2, 0] = 1
    named[:, 1::2, 0] = -1
    fitted = dict(free_mean=[0, 0], named_mean=[0, 0], scale=0.6)
    result = a.analyze_arrays(free, named, [[0, 0]], [0.2, 0.8], fitted)
    assert result["components"]["Q_T1"] == pytest.approx(-1 / 9)
    assert result["components"]["Q_T2"] == pytest.approx(-1 / 9)


def test_repeat_order_and_scene_order_do_not_change_points_or_intervals():
    rng = np.random.default_rng(7803)
    free, named = (rng.normal(size=(3, 10, 5)) for _ in range(2))
    x = rng.normal(size=(7, 5))
    fitted = dict(free_mean=np.zeros(5), named_mean=np.ones(5), scale=0.72)
    base = a.analyze_arrays(free, named, x, [0.2, 0.3, 0.5], fitted)
    f, n = free.copy(), named.copy()
    for j in range(3):
        perm = rng.permutation(10)
        f[j], n[j] = free[j, perm], named[j, perm]
    other = a.analyze_arrays(f[::-1], n[::-1], x[::-1], [0.5, 0.3, 0.2], fitted)
    for left, right in zip(base["primary"], other["primary"], strict=True):
        assert left["estimate"] == pytest.approx(right["estimate"], abs=1e-12)
        assert left["interval"] == pytest.approx(right["interval"], abs=1e-12)


def test_extreme_finite_overflow_is_unavailable_not_silently_dropped():
    free = np.full((2, 10, 2), 1e308)
    named = -free
    fitted = dict(free_mean=[0, 0], named_mean=[0, 0], scale=0.5)
    result = a.analyze_arrays(free, named, [[0, 0]], [0.2, 0.8], fitted)
    assert result["status"] == "unavailable_numerical_calculation"
    assert all(row["estimate"] is None for row in result["primary"])


def test_actual_historical_compact_extraction_has_exact_fixed_map():
    from pathlib import Path

    value = a.load_inputs(Path(__file__).resolve().parents[2])
    assert len(value["reference"]["ids"]) == 32
    assert value["fitted"]["scale"] == 0.6785365094757265
    assert sum(value["scaler"]["development_counts"].values()) == 221


@pytest.mark.parametrize("failure", ["collection", "measurement"])
def test_one_ineligible_or_missing_slot_withholds_every_scientific_value(
    inputs, measurements, failure
):
    from latent_art_bench.painter_map_validation_v2 import common

    requests, rows = measurements
    receipt = dict(analysis_eligible=True, analysis_unavailability_reasons=[])
    if failure == "collection":
        receipt = dict(
            analysis_eligible=False, analysis_unavailability_reasons=["deadline_exceeded"]
        )
    else:
        rows[0].update(status="normalization_failed", values=None, scaled=None)
    result = a.analyze(requests, rows, inputs, common.expected_config(), collection_receipt=receipt)
    assert result["status"] == "unavailable_complete_grid"
    assert all(row["estimate"] is None and row["interval"] is None for row in result["primary"])
    assert all(value is None for value in result["components"].values())
    assert result["deleted_estimates"] is None
    assert result["unavailability_reasons"]
    assert len(result["memberships"]) == 12


@pytest.mark.parametrize(
    "eligible,reasons", [(1, []), (True, ["failed"]), (False, []), (False, [1])]
)
def test_collection_gate_has_consistent_explicit_types(inputs, measurements, eligible, reasons):
    from latent_art_bench.painter_map_validation_v2 import common

    with pytest.raises(ValueError, match="eligibility"):
        a.analyze(
            *measurements,
            inputs,
            common.expected_config(),
            collection_receipt=dict(
                analysis_eligible=eligible, analysis_unavailability_reasons=reasons
            ),
        )


def test_full_wrapper_records_fixed_weights_and_reproducible_two_target_report(
    inputs, measurements
):
    import json

    from latent_art_bench.painter_map_validation_v2 import common

    result = a.analyze(
        *measurements,
        inputs,
        common.expected_config(),
        collection_receipt=dict(analysis_eligible=True, analysis_unavailability_reasons=[]),
    )
    assert len(result["primary"]) == 2
    assert len(result["deleted_estimates"]) == 12
    assert len(result["deleted_estimates"][0]) == 10
    assert sum(row["weight"] for row in result["memberships"]) == pytest.approx(1)
    assert sum(
        pair["image_weight"] for row in result["memberships"] for pair in row["pairs"]
    ) == pytest.approx(1)
    assert result["reference_weights"] == [1 / 32] * 32
    assert a.report_text(json.loads(json.dumps(result, allow_nan=False))) == a.report_text(result)
