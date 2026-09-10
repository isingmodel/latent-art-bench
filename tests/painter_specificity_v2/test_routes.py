"""Targeted checks for the repaired route and cumulative-cost boundary."""

import base64
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_specificity_v2 import study as s
from latent_art_bench.painter_specificity_v2 import workflow as w


def test_disjoint_payloads_and_cumulative_budget():
    items = s.assignments()
    assert len(items) == 1008
    assert all(r["id"].startswith("psv2-") for r in items)
    assert len({(r["scene"], r["model"], r["arm"], r["repeat"]) for r in items}) == 1008
    for r in items:
        if r["model"].startswith("gpt-image"):
            assert r["payload"]["model"] == "openai/" + r["model"]
            assert r["payload"]["quality"] == "medium"
            assert r["payload"]["provider"] == dict(only=["openai"], allow_fallbacks=False)
    event = dict(kind="start", id="x", attempt=1)
    assert s.accounted([event]) == pytest.approx(s.BASELINE + 5)
    end = dict(kind="end", id="x", attempt=1, cost_usd=0.005975)
    assert s.accounted([event, end]) == pytest.approx(s.BASELINE + 0.005975)
    with pytest.raises(ValueError):
        s.accounted([event, end, end])


def test_explicit_openai_route_keeps_model_and_known_charge(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "ROOT", tmp_path)
    monkeypatch.setattr(s, "WORK", tmp_path)
    (tmp_path / "images").mkdir()
    (tmp_path / "responses").mkdir()
    buf = io.BytesIO()
    Image.new("RGB", (512, 512), "blue").save(buf, format="PNG")
    image = base64.b64encode(buf.getvalue()).decode()
    expected = "openai/gpt-image-2.5-sunburst"

    def respond(request):
        import json

        assert json.loads(request.content)["model"] == expected
        return httpx.Response(
            200, json=dict(model=expected, data=[dict(b64_json=image)], usage=dict(cost=0.005975))
        )

    client = httpx.Client
    monkeypatch.setattr(
        w.httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(respond), **kw)
    )
    r = next(r for r in s.assignments() if r["model"] == "gpt-image-2.5-sunburst")
    result = w.post(r, 1, "test-key")
    assert result["success"]
    assert result["cost_usd"] == 0.005975
    assert result["reported"]["model"] == expected


def test_fourteen_scene_reference_recovery_oracle():
    import numpy as np

    from latent_art_bench.painter_specificity_v2.analysis import compute

    rng = np.random.default_rng(41)
    ref = [rng.normal(size=(20, 31)) + i for i in range(4)]
    centers = np.array([r.mean(axis=0) for r in ref])
    x = np.zeros((6, 14, 2, 6, 31))
    # Arbitrary model/scene offsets must vanish from artist-relative recovery.
    x[:, :, :, 2:] = centers + rng.normal(size=(6, 14, 1, 1, 31))
    result = compute(x, ref)
    assert result['common_complete_scenes'] == list(range(14))
    for model in result['models']:
        assert model['beta']['mean'] == pytest.approx(1)
        assert model['distortion']['mean'] == pytest.approx(0, abs=1e-14)
    assert result['scene_fixed_effects_regression']['n_scenes'] == 14
