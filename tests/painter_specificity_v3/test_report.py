"""The report driver assembles, renders and serializes the analysis (constructed inputs)."""

from __future__ import annotations

import json

import numpy as np

from latent_art_bench.painter_specificity_v3 import report


def test_compute_render_and_clean_on_constructed_inputs(monkeypatch):
    rng = np.random.default_rng(13)

    def generated(rep):
        p = 31 if rep.startswith("hand31") else 8
        x = rng.normal(size=(6, 14, 2, 10, p))
        x[:, :, :, 2:] += rng.normal(size=(1, 1, 1, 8, p)) * 2
        return x

    def references(rep):
        p = 31 if rep.startswith("hand31") else 8
        return {g: [rng.normal(size=(25, p)) + rng.normal(size=p) for _ in range(4)]
                for g in ("century", "hudson")}

    def september(rep):
        return rng.normal(size=(6, 14, 2, 2, 31 if rep.startswith("hand31") else 8))

    monkeypatch.setattr(report, "generated", generated)
    monkeypatch.setattr(report, "references", references)
    monkeypatch.setattr(report, "september", september)
    monkeypatch.setattr(report, "inputs", lambda: [])
    result = report._clean(report.compute(draws=20))
    text = json.dumps(result, allow_nan=False)
    assert set(result["representations"]) == set(report.REPRESENTATIONS)
    hand = result["representations"]["hand31"]
    assert hand["primary"]["century"]["inference_family"] == 21
    assert "primary" in result["representations"]["clip"] and not \
        result["representations"]["clip"]["primary"]
    assert "H1 closeness" in report.render(result) and len(text) > 1000
