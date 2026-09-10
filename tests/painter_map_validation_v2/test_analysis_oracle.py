"""Independent observed-cloud oracles; no historical-law or new-image sampling.

The oracle constructs each transformed cloud and physically removes each paired
draw. It does not import precision tables, contrast kernels or deletion formulas.
These artificial arithmetic checks do not establish service interval coverage.
"""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
from scipy.spatial.distance import cdist
from scipy.stats import t

from latent_art_bench.painter_map_validation_v2 import analysis


def literal_components(free, named, reference, scene_weights, fitted):
    """Allow unequal per-scene lengths, as required by an actual paired deletion."""
    mu_f = np.asarray(fitted["free_mean"])
    mu_n = np.asarray(fitted["named_mean"])
    image_weights = np.concatenate(
        [np.full(len(f), weight / len(f)) for f, weight in zip(free, scene_weights, strict=True)]
    )
    p = np.full(len(reference), 1 / len(reference))
    reference_term = np.sum(cdist(reference, reference) * p[:, None] * p[None, :])
    result = {}
    for key in ("T1", "T2"):
        transformed = [
            f + mu_n - mu_f if key == "T1" else mu_n + fitted["scale"] * (f - mu_f)
            for f in free
        ]
        cloud = np.concatenate(transformed)
        result["energy_" + key] = float(
            2 * np.sum(cdist(reference, cloud) * p[:, None] * image_weights[None, :])
            - reference_term
            - np.sum(cdist(cloud, cloud) * image_weights[:, None] * image_weights[None, :])
        )
        score = 0.0
        for n, transformed_scene, weight in zip(named, transformed, scene_weights, strict=True):
            residual = n - transformed_scene
            r = len(residual)
            # Literal distinct ordered pairs, with no diagonal or noise truncation.
            score += weight * sum(
                float(residual[i] @ residual[j]) for i in range(r) for j in range(r) if i != j
            ) / (r * (r - 1))
        result["Q_" + key] = score
    return result


def literal_contrast(components):
    return np.array(
        [components["energy_T2"] - components["energy_T1"], components["Q_T2"] - components["Q_T1"]]
    )


def literal_jackknife(free, named, reference, weights, fitted):
    original = literal_components(free, named, reference, weights, fitted)
    deleted = np.empty((len(free), 10, 2))
    for j in range(len(free)):
        for r in range(10):
            f, n = list(free), list(named)
            f[j], n[j] = np.delete(free[j], r, axis=0), np.delete(named[j], r, axis=0)
            deleted[j, r] = literal_contrast(literal_components(f, n, reference, weights, fitted))
    variance = 0.9 * np.sum((deleted - deleted.mean(axis=1, keepdims=True)) ** 2, axis=(0, 1))
    return original, deleted, variance


@pytest.mark.parametrize("scenes,dimensions,reference_count", [(2, 2, 3), (3, 5, 7), (12, 31, 32)])
def test_literal_cloud_components_and_every_paired_deletion(scenes, dimensions, reference_count):
    rng = np.random.default_rng(63291 + scenes)
    free = rng.normal(size=(scenes, 10, dimensions))
    # Artificial heteroscedastic, paired-dependent errors; this is not a service proxy.
    scales = np.linspace(0.3, 1.7, scenes)[:, None, None]
    named = 0.35 * free + scales * rng.normal(size=free.shape) + 0.8
    reference = rng.normal(size=(reference_count, dimensions)) - 0.4
    weights = (
        np.repeat(np.array([3, 11, 18]) / 128, 4)
        if scenes == 12
        else np.arange(1, scenes + 1) / sum(range(1, scenes + 1))
    )
    fitted = dict(
        free_mean=rng.normal(size=dimensions),
        named_mean=rng.normal(size=dimensions),
        scale=0.6785365094757265,
    )
    expected, deletions, variance = literal_jackknife(free, named, reference, weights, fitted)
    result = analysis.analyze_arrays(free, named, reference, weights, fitted)
    assert result["status"] == "approximate_simultaneous_intervals"
    assert result["components"] == pytest.approx(expected, abs=5e-12, rel=5e-12)
    np.testing.assert_allclose(result["deleted_estimates"], deletions, atol=5e-12, rtol=5e-12)
    np.testing.assert_allclose(
        [row["estimate"] for row in result["primary"]],
        literal_contrast(expected),
        atol=5e-12,
        rtol=5e-12,
    )
    np.testing.assert_allclose(
        [row["jackknife_variance"] for row in result["primary"]],
        variance,
        atol=5e-12,
        rtol=5e-12,
    )
    half_width = t.ppf(0.9875, 9) * np.sqrt(variance)
    point = literal_contrast(expected)
    np.testing.assert_allclose(
        [row["interval"] for row in result["primary"]],
        np.stack((point - half_width, point + half_width), axis=1),
        atol=5e-12,
        rtol=5e-12,
    )
    assert result["degrees_of_freedom"] == 9
    assert result["interval_family_size"] == 2


def test_zero_q_variance_withholds_the_nonzero_energy_interval_too():
    # Dyadic values give e_T1 = -e_T2 exactly, so the Q contrast and its every
    # deletion are exactly zero, while the energy contrast has genuine variation.
    free = np.arange(40).reshape(2, 10, 2) / 8
    named = 0.75 * free
    reference = np.array([[0.0, 0.0], [1.0, -1.0]])
    fitted = dict(free_mean=[0.0, 0.0], named_mean=[0.0, 0.0], scale=0.5)
    expected, _, variance = literal_jackknife(free, named, reference, [0.25, 0.75], fitted)
    result = analysis.analyze_arrays(free, named, reference, [0.25, 0.75], fitted)
    assert variance[0] > 0 and variance[1] == 0
    assert result["status"] == "descriptive_points_only"
    assert result["joint_direction"] == "unavailable"
    assert result["components"] == pytest.approx(expected)
    assert result["primary"][0]["estimate"] != 0
    assert result["primary"][0]["jackknife_variance"] > 0
    assert result["primary"][1]["estimate"] == 0
    assert result["primary"][1]["jackknife_variance"] == 0
    assert all(row["interval"] is None and row["half_width"] is None for row in result["primary"])


def test_negative_component_q_and_negative_contrast_have_literal_covariance_identity():
    rng = np.random.default_rng(40982)
    free = rng.normal(size=(3, 10, 4)) + 2.0
    residual = rng.normal(size=free.shape)
    residual -= residual.mean(axis=1, keepdims=True)
    fitted = dict(free_mean=[0.0] * 4, named_mean=[1.0] * 4, scale=0.5)
    named = 1.0 + 0.5 * free + residual
    reference = rng.normal(size=(5, 4))
    weights = np.array([0.1, 0.3, 0.6])
    result = analysis.analyze_arrays(free, named, reference, weights, fitted)
    expected = literal_components(free, named, reference, weights, fitted)
    sample_covariance_form = sum(
        weight * (np.sum(e.mean(axis=0) ** 2) - np.trace(np.cov(e, rowvar=False, ddof=1)) / 10)
        for e, weight in zip(residual, weights, strict=True)
    )
    assert sample_covariance_form < 0
    assert result["components"]["Q_T2"] == pytest.approx(sample_covariance_form, abs=1e-13)
    assert result["components"] == pytest.approx(expected, abs=1e-12)
    assert result["primary"][1]["estimate"] == pytest.approx(
        expected["Q_T2"] - expected["Q_T1"], abs=1e-12
    )
    assert result["primary"][1]["estimate"] < 0


@pytest.fixture
def planned_artificial_measurements():
    """Actual prospective assignments, wholly invented numerical observations."""
    from latent_art_bench.painter_map_validation_v2 import common

    root = Path(__file__).resolve().parents[2]
    config = common.configuration(root)
    requests = common.build_plan(root, config)
    rng = np.random.default_rng(930285)
    center, scale = np.arange(31) / 8, np.linspace(0.75, 2.25, 31)
    inputs = dict(
        schema="painter-map-validation-inputs/2",
        origins=analysis.ORIGINS.copy(),
        pipeline="primary512",
        painter_id="paul_cezanne",
        features=list(analysis.NAMES),
        targets=dict(water=3 / 32, built=11 / 32, land=18 / 32),
        reference=dict(
            ids=[f"artificial_work_{i:02d}" for i in range(32)],
            values=rng.normal(size=(32, 31)).tolist(),
        ),
        scaler=dict(center=center.tolist(), scale=scale.tolist()),
        fitted=dict(
            free_mean=rng.normal(size=31).tolist(),
            named_mean=rng.normal(size=31).tolist(),
            scale=0.6785365094757265,
        ),
    )
    rows = []
    for request in requests:
        raw = rng.normal(size=31)
        rows.append(
            dict(
                {key: request[key] for key in ("request_id", *analysis.IDENTITY_FIELDS)},
                pipeline="primary512",
                status="measured",
                feature_names=list(analysis.NAMES),
                values=raw.tolist(),
                scaled=((raw - center) / scale).tolist(),
            )
        )
    receipt = dict(analysis_eligible=True, analysis_unavailability_reasons=[])
    return requests, rows, inputs, config, receipt


def test_full_wrapper_preserves_exact_panel_weights_and_literal_component_points(
    planned_artificial_measurements,
):
    requests, rows, inputs, config, receipt = planned_artificial_measurements
    result = analysis.analyze(requests, rows[::-1], inputs, config, collection_receipt=receipt)
    scene_ids = [f"pmv2_{c}{i:02d}" for c in ("water", "built", "land") for i in range(1, 5)]
    by_slot = {(row["template_id"], row["repetition"], row["arm"]): row for row in rows}
    arrays = [
        np.array([[by_slot[scene, r, arm]["scaled"] for r in range(10)] for scene in scene_ids])
        for arm in ("artist_free", "named")
    ]
    weights = np.repeat(np.array([3, 11, 18]) / 128, 4)
    expected = literal_components(*arrays, inputs["reference"]["values"], weights, inputs["fitted"])
    assert result["allocated_images"] == 240 and result["allocated_pairs"] == 120
    assert result["fixed_scenes"] == 12 and result["repeats"] == 10
    assert result["collection_eligible"] is True and result["unavailability_reasons"] == []
    assert result["reference_weights"] == [1 / 32] * 32
    assert result["components"] == pytest.approx(expected, abs=5e-12, rel=5e-12)
    np.testing.assert_allclose(
        [item["estimate"] for item in result["primary"]],
        literal_contrast(expected),
        atol=5e-12,
        rtol=5e-12,
    )
    assert [item["scene_id"] for item in result["memberships"]] == scene_ids
    for scene, weight in zip(result["memberships"], weights, strict=True):
        assert scene["weight"] == weight
        for r, pair in enumerate(scene["pairs"]):
            assert pair["repetition"] == r
            assert pair["image_weight"] == weight / 10
            for arm, field in (("artist_free", "artist_free_id"), ("named", "named_id")):
                assert pair[field] == by_slot[scene["scene_id"], r, arm]["request_id"]


@pytest.mark.parametrize("failure", ["missing_vector", "identity_gate", "duration_gate"])
def test_ineligible_or_incomplete_full_inventory_cannot_call_any_numerical_summary(
    planned_artificial_measurements, monkeypatch, failure,
):
    requests, rows, inputs, config, receipt = planned_artificial_measurements
    if failure == "missing_vector":
        rows[-1].update(status="generation_failed", values=None, scaled=None)
    else:
        receipt.update(analysis_eligible=False, analysis_unavailability_reasons=[failure])

    def forbidden(*args, **kwargs):
        pytest.fail("ineligible or incomplete allocation reached the scientific calculation")

    monkeypatch.setattr(analysis, "analyze_arrays", forbidden)
    result = analysis.analyze(requests, rows, inputs, config, collection_receipt=receipt)
    assert result["status"] == "unavailable_complete_grid"
    assert result["deleted_estimates"] is None
    assert all(value is None for value in result["components"].values())
    assert all(row["estimate"] is None and row["interval"] is None for row in result["primary"])
    assert result["joint_direction"] == "unavailable"


@pytest.mark.parametrize(
    "fault", ["row_missing", "wrong_scaled", "feature_order", "wrong_identity"]
)
def test_complete_wrapper_rejects_measurement_contract_drift(
    planned_artificial_measurements, fault,
):
    requests, rows, inputs, config, receipt = planned_artificial_measurements
    if fault == "row_missing":
        rows.pop()
    elif fault == "wrong_scaled":
        rows[0]["scaled"][0] = np.nextafter(rows[0]["scaled"][0], np.inf)
    elif fault == "feature_order":
        rows[0]["feature_names"] = rows[0]["feature_names"][::-1]
    else:
        rows[0]["repetition"] = (rows[0]["repetition"] + 1) % 10
    with pytest.raises(ValueError):
        analysis.analyze(requests, rows, inputs, config, collection_receipt=receipt)


@pytest.mark.parametrize(
    "receipt",
    [
        dict(analysis_eligible=1, analysis_unavailability_reasons=[]),
        dict(analysis_eligible=True, analysis_unavailability_reasons=["identity_failed"]),
        dict(analysis_eligible=False, analysis_unavailability_reasons=[]),
        dict(analysis_eligible=False, analysis_unavailability_reasons=[""]),
    ],
)
def test_collection_eligibility_is_literal_and_consistent(planned_artificial_measurements, receipt):
    requests, rows, inputs, config, _ = planned_artificial_measurements
    with pytest.raises(ValueError, match="eligibility"):
        analysis.analyze(requests, rows, inputs, config, collection_receipt=deepcopy(receipt))
