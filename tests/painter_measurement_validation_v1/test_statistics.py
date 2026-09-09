from pathlib import Path

import numpy as np
import pytest

from latent_art_bench.painter_distribution_revision_v1 import common
from latent_art_bench.painter_measurement_validation_v1 import statistics as s
from latent_art_bench.painter_measurement_validation_v1.transforms import CONDITIONS


def test_bootstrap_balances_painters_and_preserves_work_response_dependence():
    base = np.array([0., 2., 4., 10.])
    values = np.stack((base, 2 * base, -base), axis=1)
    labels = [s.PAINTERS[0]] * 3 + [s.PAINTERS[1]]
    estimate, intervals, draws = s.work_bootstrap(values, labels, draws=199, seed=17)
    np.testing.assert_array_equal(estimate, [6., 12., -6.])
    np.testing.assert_allclose(draws[:, 1], 2 * draws[:, 0])
    np.testing.assert_allclose(draws[:, 2], -draws[:, 0])
    np.testing.assert_array_equal(intervals, np.quantile(draws, [.05 / 6, 1 - .05 / 6], axis=0))
    np.testing.assert_array_equal(draws, s.work_bootstrap(values, labels, draws=199, seed=17)[2])


def test_paired_processing_max_is_computed_before_averaging():
    scaler = dict(center=[0.] * 31, scale=[1.] * 31)
    rows = []
    for p in s.PAINTERS:
        for work in range(2):
            for condition in CONDITIONS:
                amplitude = (0 if condition in ("baseline", "png") else
                             (10 * work if condition == "jpeg95" else
                              (10 * (1 - work) if condition == "resample384" else 11)))
                values = np.full(31, amplitude, dtype=float)
                values[2] += 20
                rows.append(dict(image_id=f"{p}:{work}", painter_id=p, condition=condition,
                                 values=values.tolist(), transform={}))
    result = s.summarize_challenge(rows, scaler)
    assert len(result["family_matrix"]) == 90
    assert all(r["estimate"] == 1 for r in result["comparisons"])
    assert all(r["lower"] is None for r in result["comparisons"])
    assert all(r["zero_bootstrap_variance"] for r in result["comparisons"])
    assert set(result["by_work"][0]["signed_chroma_response"]) == {"chroma80", "chroma60"}
    with pytest.raises(ValueError, match="incomplete"):
        s.summarize_challenge(rows[:-1], scaler)
    with pytest.raises(ValueError, match="duplicate"):
        s.summarize_challenge(rows + [rows[0]], scaler)


def test_displacement_uses_all_coordinates_and_unchanged_iqr():
    scaler = dict(center=[7.] * 31, scale=[2.] * 31)
    before, after = np.zeros(31), np.zeros(31)
    after[0] = 2
    result = s.displacement(before, after, scaler)
    assert result["color"] == pytest.approx(1 / np.sqrt(11))
    assert result["spatial"] == result["texture"] == 0


def test_bootstrap_rejects_missing_painter_and_nonfinite_response():
    with pytest.raises(ValueError, match="both fixed painters"):
        s.work_bootstrap(np.zeros((2, 3)), [s.PAINTERS[0]] * 2)
    with pytest.raises(ValueError, match="finite"):
        s.work_bootstrap(np.full((2, 3), np.nan), s.PAINTERS)


def test_actual_compact_primary_and_identity_geometry_replay_all_eight_endpoints():
    # Tracked compact numerical inputs only. No raw image/response bytes are opened.
    bundle = common.load(Path(__file__).resolve().parents[2])
    assert s.verify_primary(bundle) == bundle["old_analysis"]["endpoints"]
    rows = [dict(image_id=r["image_id"], values=r["values"],
                 window=dict(retained_area_fraction=1.0))
            for stage in ("reference", "generated") for r in bundle[stage]
            if r["pipeline"] == "primary512"]
    result = s.geometry_analysis(rows, bundle)
    assert result["endpoints"] == bundle["old_analysis"]["endpoints"]
    assert len(result["comparisons"]) == 8
    assert all(r["estimate_change"] == 0 for r in result["comparisons"])
    assert all(r["min_retained_area_fraction"] == r["max_retained_area_fraction"] == 1
               for r in result["groups"])
    with pytest.raises(ValueError, match="complete original"):
        s.geometry_analysis(rows[:-1], bundle)
