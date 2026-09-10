"""Small independent oracles for the new scientific estimands and spend guard."""

import numpy as np
import pytest

from latent_art_bench.painter_specificity_v1 import study as s
from latent_art_bench.painter_specificity_v1.analysis import (
    centered,
    fixed_effects,
    geometry,
    interval,
)
from latent_art_bench.painter_specificity_v1.workflow import budget


def fixture():
    reference = [np.eye(4)[[a]] for a in range(4)]
    r = centered(np.eye(4))
    return reference, r


def test_exact_recovery_common_translation_and_amplitude():
    reference, r = fixture()
    x = np.broadcast_to(r, (16, 2, 4, 4)).copy()
    x += np.arange(16)[:, None, None, None] * 7
    result = geometry(x, reference)
    np.testing.assert_allclose(result["beta"], 1)
    np.testing.assert_allclose(result["distortion"], 0, atol=1e-24)
    weak = geometry(0.4 * x, reference)
    np.testing.assert_allclose(weak["beta"], 0.4)
    np.testing.assert_allclose(weak["distortion"], 0.36)
    absent = geometry(np.zeros_like(x), reference)
    np.testing.assert_allclose(absent["distortion"], 1)


def test_noise_cross_product_is_not_naive_squared_error():
    reference, r = fixture()
    # Exactly orthogonal repeat errors: nonzero individual squared errors, zero cross bias.
    e1 = np.array([[1, 0, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
    e2 = np.roll(e1, 1, axis=1)
    x = np.array([[r + e1, r + e2]])
    g = geometry(x, reference)
    assert g["distortion"][0] == pytest.approx(0)
    assert np.sum((x - r) ** 2) > 0
    np.testing.assert_allclose(
        g["amplitude_error"] + g["off_axis_error"], g["distortion"], atol=1e-14
    )


def test_artist_label_permutation_is_penalized():
    reference, r = fixture()
    g = geometry(np.broadcast_to(r[::-1], (16, 2, 4, 4)), reference)
    assert g["distortion"].mean() > 1
    assert g["beta"].mean() < 0


def test_fixed_effects_matches_paired_regression_oracle():
    scene = np.arange(16) / 7
    effects = np.array([1, 0, 2, 3, -1, -0.5])
    values = effects[:, None] + scene
    fit = fixed_effects(values)
    np.testing.assert_allclose(fit["scene_intercepts"], scene, atol=1e-12)
    for m, name in enumerate(s.MODELS):
        if m != 1:
            assert fit["model_coefficients"][name] == pytest.approx(effects[m])
    assert interval(values[0] - values[1])["mean"] == pytest.approx(1)
    assert not interval(np.arange(11))["available"]


def test_allocation_and_exact_named_generic_control():
    requests = s.assignments()
    assert len(requests) == len({r["id"] for r in requests}) == 1152
    assert len({(r["model"], r["scene"], r["arm"], r["repeat"]) for r in requests}) == 1152
    for r in requests:
        assert r["payload"]["model"] == r["model"]
        if r["model"] in s.PROVIDERS:
            assert r["payload"]["provider"]["allow_fallbacks"] is False
    assert sum(r["model"] in s.PROVIDERS for r in requests) == 384


def test_spend_reservations_settlement_unknowns_and_duplicate_terminal():
    a = dict(kind="start", id="a", attempt=1, paid=True)
    b = dict(kind="start", id="b", attempt=1, paid=True)
    end = dict(kind="end", id="a", attempt=1, cost_usd=0.07)
    assert budget([a, b]) == pytest.approx(s.BASELINE + 10)
    assert budget([a, b, end]) == pytest.approx(s.BASELINE + 5.07)
    assert budget([a, b, end, dict(kind="end", id="b", attempt=1, cost_usd=None)]) == (
        pytest.approx(s.BASELINE + 5.07)
    )
    with pytest.raises(ValueError):
        budget([a, end, end])


def test_complete_numerical_pipeline_preserves_known_model_ordering():
    from latent_art_bench.painter_specificity_v1.analysis import compute

    rng = np.random.default_rng(71)
    reference = [rng.normal(size=(4, 31)) + a for a in range(4)]
    r = centered(np.array([a.mean(axis=0) for a in reference]))
    x = np.zeros((6, 16, 2, 6, 31))
    for m, amplitude in enumerate([1, 0.8, 0.6, 0.4, 0.2, 0]):
        x[m, :, :, 2:] = amplitude * r
    result = compute(x, reference)
    for m, expected in enumerate([0, 0.04, 0.16, 0.36, 0.64, 1]):
        assert result["models"][m]["distortion"]["mean"] == pytest.approx(expected, abs=1e-14)
        assert result["sensitivities"]["without_texture"][m]["distortion"] == (
            pytest.approx(expected, abs=1e-14)
        )
    assert result["scene_fixed_effects_regression"]["available"]
    assert len(result["comparisons"]) == 15


def test_transport_boundary_with_artificial_response(tmp_path, monkeypatch):
    import base64
    import io
    import json

    import httpx
    from PIL import Image

    from latent_art_bench.painter_specificity_v1 import workflow as w

    monkeypatch.setattr(s, "WORK", tmp_path)
    monkeypatch.setattr(s, "ROOT", tmp_path)
    (tmp_path / "images").mkdir()
    (tmp_path / "responses").mkdir()
    buf = io.BytesIO()
    Image.new("RGB", (512, 512), "green").save(buf, format="PNG")
    payload = dict(
        model=s.MODELS[4],
        data=[dict(b64_json=base64.b64encode(buf.getvalue()).decode())],
        usage=dict(cost=0.06),
    )

    def handler(request):
        assert str(request.url) == s.PAID_URL
        assert json.loads(request.content)["model"] == s.MODELS[4]
        return httpx.Response(200, json=payload)

    client = httpx.Client
    monkeypatch.setattr(
        w.httpx, "Client", lambda **kw: client(transport=httpx.MockTransport(handler), **kw)
    )
    request = dict(
        id="synthetic", model=s.MODELS[4], payload=s.payload(s.MODELS[4], s.SCENES[0][1], "generic")
    )
    result = w.post(request, 1, "artificial-test-key")
    assert result["success"]
    assert result["cost_usd"] == 0.06
    assert result["reported"]["model"] == s.MODELS[4]
    assert (tmp_path / result["image_path"]).exists()
