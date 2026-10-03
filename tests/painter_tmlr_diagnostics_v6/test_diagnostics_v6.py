"""Constructed-data checks for diagnostics v6."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v6 as v6
from latent_art_bench.painter_tmlr_diagnostics_v1 import decomposition


def test_fractions_match_the_paper_decomposition():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(14, 2, 6, 31))
    x[:, :, 2:] += rng.normal(size=(1, 1, 4, 31))
    means = rng.normal(size=(4, 31))
    observed, faithful = v6.fractions(x, means)
    dec = decomposition(x, means)
    assert observed == pytest.approx(dec["shared_fraction"])
    assert faithful == pytest.approx(dec["faithful_shared_fraction"])
    out = v6.shared_interval(x, means, draws=200)
    assert out["ci95"][0] <= out["observed"] <= out["ci95"][1]
    assert 0 <= out["observed_below_faithful"] <= 1


def test_recognition_is_perfect_for_separated_prototypes_and_chance_when_scrambled():
    rng = np.random.default_rng(4)
    prototypes = np.eye(4, 8) * 5
    named = [prototypes[a] + 0.1 * rng.normal(size=(28, 8)) for a in range(4)]
    assert v6.recognition(named, prototypes) == 1.0
    assert v6.recognition(named[::-1], prototypes) == 0.0


def test_compute_runs_on_constructed_collection(tmp_path, monkeypatch):
    import json

    from latent_art_bench.painter_specificity_v3 import report as v3

    rng = np.random.default_rng(5)

    def generated(rep):
        p = 31 if rep == "hand31" else 12
        x = rng.normal(size=(6, 14, 2, 10, p))
        x[:, :, :, 2:] += rng.normal(size=(1, 1, 1, 8, p)) * 2
        return x

    def references(rep):
        p = 31 if rep == "hand31" else 12
        return {g: [rng.normal(size=(20, p)) + rng.normal(size=p) for _ in range(4)]
                for g in ("century", "hudson")}

    analysis = {"representations": {rep: {
        "complete_scenes": list(range(14)),
        "groups": {g: [{"alignment_ratio": float(m)} for m in range(6)]
                   for g in ("century", "hudson")}} for rep in v6.REPS}}
    (tmp_path / "analysis.json").write_text(json.dumps(analysis))
    monkeypatch.setattr(v3, "OUT", tmp_path)
    monkeypatch.setattr(v3, "generated", generated)
    monkeypatch.setattr(v3, "references", references)
    result = v6.compute(draws=20)
    clip = result["representations"]["clip"]["groups"]["century"]
    assert len(clip["configurations"]) == 6
    assert 0 <= clip["configurations"][0]["recognition_eight_way"] <= 1
    assert "corr_shared" in clip["proximity"]
    assert "H" not in v6.report(result)[:10]
