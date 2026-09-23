"""Constructed reporting tests, independent of retained scientific outcomes."""

import json

import numpy as np
import pytest

from latent_art_bench.painter_family_controls_v1.analysis import analyze_primary
from latent_art_bench.painter_family_controls_v1.protocol import ARMS, MODELS, SCENES
from latent_art_bench.painter_family_controls_v1.reference_panels import PANEL_IDS
from latent_art_bench.painter_family_controls_v1.secondary_embeddings import analyze_secondary


def fixture():
    refs = np.zeros((4, 6))
    refs[:, 0] = 0.4
    contrast = np.eye(4) - 0.25
    refs[:, 1:5] = 0.2 * contrast
    data = np.zeros((6, 8, 12, 8, 6))
    data[..., 1, 0] = np.arange(8)[None, :, None] * 0.002 / 0.4
    data[..., 2, 0] = 0.01 / 0.4
    data[..., 3, 0] = 0.04 / 0.4
    data[..., 4:8, 0] = 0.02 / 0.4
    data[..., 4:8, 1:5] = 0.2 * contrast
    data[..., -1] = np.sqrt(1 - np.sum(data[..., :-1] ** 2, axis=-1))
    return data, refs, [dict(constructed_window=i) for i in range(8)]


@pytest.mark.parametrize("encoder", ["clip", "csd"])
@pytest.mark.parametrize("panel", PANEL_IDS)
def test_all_secondary_panels_keep_labels_terms_ratios_and_influence_without_primary(
    encoder, panel
):
    data, refs, times = fixture()
    result = analyze_secondary(data, refs, times, representation=encoder, reference_panel=panel)
    primary = analyze_primary(data, refs, times)
    assert result["model_order"] == list(MODELS)
    assert result["scene_order"] == [scene[0] for scene in SCENES]
    assert result["arm_order"] == list(ARMS)
    assert result["window_order"] == list(range(8))
    assert result["observed_cell_count"] == 4608
    assert result["missing_census"] == []
    assert result["primary_inference"] is False and result["familywise_claim"] is False
    assert "primary_family_size" not in result and "critical_t" not in result
    for index, model in enumerate(result["models"]):
        assert "primary_intervals" not in model and "decision" not in model
        for key in ("components", "secondary_ratios", "free_baseline", "pairwise_alignment"):
            assert model[key] == primary["models"][index][key]
        assert model["aggregate_beta"]["equal_window_mean"] == pytest.approx(1)
        assert len(model["components"]["N"]["leave_one_window_out"]["means"]) == 8
    json.dumps(result, allow_nan=False)


def test_missing_generic_retains_cancelled_terms_and_named_labelled_missing_census():
    data, refs, times = fixture()
    data[2, 3, 4, 1] = np.nan
    data[5, 1, 2, 0] = np.nan
    result = analyze_secondary(
        data, refs, times, representation="clip", reference_panel="primary_original"
    )
    assert result["observed_cell_count"] == 4606
    assert result["missing_census"][0] == dict(
        model_index=2,
        model=MODELS[2],
        window=3,
        scene_index=4,
        scene_id=SCENES[4][0],
        arm_index=1,
        arm="generic",
    )
    generic = result["models"][2]
    for key in ("N", "F", "C_G", "T"):
        assert generic["components"][key]["window_values"][3] is None
        assert generic["components"][key]["equal_window_mean"] is None
    for key in ("L", "C_F", "N-F", "F-S"):
        assert generic["components"][key]["complete_eight_windows"]
    assert (
        generic["secondary_ratios"]["C_F/(N-F)"]["status"] == "secondary_conditional_approximation"
    )
    free = result["models"][5]
    assert free["components"]["N"]["complete_eight_windows"]
    assert free["free_baseline"]["N_free"]["window_values"][1] is None
    json.dumps(result, allow_nan=False)


def test_adverse_and_weak_denominators_and_zero_reference_energy_are_retained():
    data, refs, times = fixture()
    data[..., 1, 0] = 0.1 / 0.4
    data[..., 1, -1] = np.sqrt(1 - data[..., 1, 0] ** 2)
    result = analyze_secondary(
        data, refs, times, representation="csd", reference_panel="development_original"
    )
    ratio = result["models"][0]["secondary_ratios"]["F/N"]
    assert ratio["denominator_mean"] < 0
    assert ratio["status"] == "secondary_conditional_approximation"
    data[..., 1, 0] = np.linspace(0.04, 0.06, 8)[None, :, None] / 0.4
    data[..., 1, -1] = np.sqrt(1 - data[..., 1, 0] ** 2)
    weak = analyze_secondary(
        data, refs, times, representation="clip", reference_panel="primary_audited_region"
    )
    assert weak["models"][0]["secondary_ratios"]["F/N"]["confidence_set"]["kind"] in (
        "disconnected",
        "all_real",
        "half_line",
    )
    zero = analyze_secondary(
        data,
        np.zeros_like(refs),
        times,
        representation="csd",
        reference_panel="development_audited_region",
    )
    assert zero["models"][0]["aggregate_beta"] is None
    assert all(pair["beta"] is None for pair in zero["models"][0]["pairwise_alignment"])


def test_explicit_observed_mask_does_not_turn_absent_cells_into_zero_vectors():
    data, refs, times = fixture()
    observed = np.ones(data.shape[:-1], dtype=bool)
    observed[0, 0, 0, 4] = False
    data[0, 0, 0, 4] = 0
    report = analyze_secondary(
        data,
        refs,
        times,
        observed=observed,
        representation="clip",
        reference_panel="primary_original",
    )
    assert len(report["missing_census"]) == 1
    assert report["models"][0]["components"]["L"]["window_values"][0] is None
    with pytest.raises(ValueError, match="unit vectors"):
        analyze_secondary(
            data, refs, times, representation="clip", reference_panel="primary_original"
        )
    for kwargs in (
        {"representation": "other", "reference_panel": "primary_original"},
        {"representation": "clip", "reference_panel": "chosen_after_results"},
    ):
        with pytest.raises(ValueError, match="fixed encoder"):
            analyze_secondary(data, refs, times, **kwargs)
