"""Constructed report-selection tests; no real prospective outcomes exist."""

import copy
import json

import numpy as np
import pytest

from latent_art_bench.painter_family_controls_v1.analysis import fit_transport_parameters
from latent_art_bench.painter_family_controls_v1.reference_panels import PANEL_IDS
from latent_art_bench.painter_family_controls_v1.reporting import _analyze_arrays


def inputs():
    refs = np.eye(4)
    generated = np.zeros((6, 8, 12, 8, 4))
    generated[..., 0] = 1
    generated[..., 4:8, :] = refs
    observed = np.ones(generated.shape[:-1], dtype=bool)
    times = [{"fixture_window": i} for i in range(8)]
    value = dict(generated=generated, observed=observed,
                 window_times=times, simulation_only=True)
    learned = {encoder: copy.deepcopy(value) for encoder in ("clip", "csd")}
    panels = {
        encoder: {panel: {"reference_means": refs.tolist()} for panel in PANEL_IDS}
        for encoder in ("clip", "csd")
    }
    old = np.broadcast_to(refs, (6, 14, 2, 4, 4))
    params = {encoder: fit_transport_parameters(old, refs, encoder=encoder)
              for encoder in ("clip", "csd")}
    features31 = dict(generated=np.zeros((6, 8, 12, 8, 31)), observed=observed.copy(),
                      window_times=times, simulation_only=True)
    return learned, panels, params, features31


def test_exact_primary_seven_secondary_two_transport_and_realized31_reports():
    report = _analyze_arrays(*inputs())
    assert report["simulation_only"] is True
    assert report["status"] == "simulation_only_not_scientific_evidence"
    assert report["primary"]["representation"] == "csd"
    assert report["primary"]["reference_panel"] == "primary_original"
    assert report["primary"]["primary_family_size"] == 12
    assert len(report["secondary_embeddings"]) == 7
    assert "csd/primary_original" not in report["secondary_embeddings"]
    assert set(report["frozen_transport"]) == {"clip", "csd"}
    assert report["scope"]["scientific_review_score"] is None
    for model in report["primary"]["models"]:
        assert model["decision"] == "name_free_prompt_below_half_positive_named_gain"
    for result in report["secondary_embeddings"].values():
        assert result["familywise_claim"] is False
        assert result["primary_inference"] is False
        assert len(result["models"]) == 6
    assert len(report["secondary_features"]["models"]) == 6
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize("change", ["encoder", "panel", "params", "reference", "times", "mask",
                                   "simulation"])
def test_report_never_selects_representation_or_mixes_censuses(change):
    learned, panels, params, features31 = inputs()
    if change == "encoder":
        del learned["clip"]
    elif change == "panel":
        del panels["clip"]["development_original"]
    elif change == "params":
        params["clip"]["encoder"] = "csd"
    elif change == "reference":
        panels["csd"]["primary_original"]["reference_means"][0][0] = 0.5
    elif change == "times":
        learned["clip"]["window_times"][0]["fixture_window"] = 99
    elif change == "mask":
        features31["observed"][0, 0, 0, 0] = False
    else:
        learned["clip"]["simulation_only"] = False
    with pytest.raises(ValueError):
        _analyze_arrays(learned, panels, params, features31)


def test_shared_missing_primary_cell_stays_missing_in_every_report():
    learned, panels, params, features31 = inputs()
    for value in [*learned.values(), features31]:
        value["observed"][0, 0, 0, 1] = False
        value["generated"][0, 0, 0, 1] = np.nan
    report = _analyze_arrays(learned, panels, params, features31)
    assert report["primary"]["models"][0]["primary_intervals"] == {}
    assert report["primary"]["models"][1]["primary_complete"]
    assert report["primary"]["primary_family_size"] == 12
    for result in report["secondary_embeddings"].values():
        first = result["models"][0]
        assert len(first["missing_census"]) == 1
        assert first["components"]["N"]["equal_window_mean"] is None
        assert first["components"]["N-F"]["equal_window_mean"] is not None
    # Recognition uses only names; a generic-arm failure must not remove queries.
    assert report["frozen_transport"]["csd"]["models"][0]["complete_eight_windows"]
