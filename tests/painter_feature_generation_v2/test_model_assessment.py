import base64
import importlib.metadata
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v2 import model_assessment as module
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    events,
    publish,
)


def freeze_fixture(root):
    output = root / MANIFESTS / "access-fixture"
    publish(output / "requests.jsonl", module.request_frame(), lines=True)
    publish(output / "assessment_freeze.json", dict(
        inputs=[], requests_sha256=hash_file(output / "requests.jsonl"),
        base_url=module.BASE, maximum_image_attempts=2,
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")}))
    return output


def image_payload(mode="RGB", size=(1024, 1024)):
    out = io.BytesIO()
    Image.new(mode, size).save(out, format="PNG")
    return dict(data=[dict(b64_json=base64.b64encode(out.getvalue()).decode())])


def test_fixed_access_frame_not_painter_experiment():
    rows = module.request_frame()
    assert [r["model"] for r in rows] == list(module.MODELS)
    assert rows[0]["payload"]["prompt"] == rows[1]["payload"]["prompt"]
    assert all("seed" not in r["payload"] for r in rows)
    assert all(r["payload"]["n"] == 1 for r in rows)


@pytest.mark.parametrize("payload", [dict(data=[dict(url="https://example.org/a.png")]),
                                      dict(data=[]), dict(data=[dict(b64_json="!")])])
def test_rejects_urls_and_invalid_images(payload):
    with pytest.raises(ValueError):
        module.decode_image(payload)


def test_decode_enforces_geometry_opacity_and_identity_uncertainty():
    _, info = module.decode_image(image_payload())
    assert info["returned_model"] is None
    assert info["requested_alias_is_not_snapshot_attestation"]
    for payload in (image_payload(size=(512, 512)), image_payload(mode="RGBA")):
        with pytest.raises(ValueError):
            module.decode_image(payload)


def test_catalog_auth_failure_never_generates_or_reruns(tmp_path):
    output = freeze_fixture(tmp_path)
    methods = []

    def handler(request):
        methods.append(request.method)
        assert request.url.host == "127.0.0.1" and request.url.port == 10532
        assert "authorization" not in request.headers
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(502, json={"error": {"message":
                                                 "Provided authentication token is expired."}})

    transport = httpx.MockTransport(handler)
    receipt = module.execute(tmp_path, "access-fixture", transport=transport)
    assert receipt["blocker"] == "authentication_blocked"
    assert receipt["image_attempts"] == 0 and methods == ["GET", "GET"]
    assert len(events(output / "assessment_events.jsonl")) == 6
    with pytest.raises(FileExistsError):
        module.execute(tmp_path, "access-fixture", transport=transport)


@pytest.mark.parametrize("limited", [False, True])
def test_success_is_bounded_and_rate_limit_stops_next_model(tmp_path, limited):
    freeze_fixture(tmp_path)
    posts = []

    def handler(request):
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        if request.url.path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": m} for m in module.MODELS]})
        posts.append(request.content)
        if limited:
            return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded"}})
        return httpx.Response(200, json=image_payload())

    result = module.execute(tmp_path, "access-fixture", transport=httpx.MockTransport(handler))
    assert len(posts) == (1 if limited else 2)
    assert result["images_generated"] == (0 if limited else 2)
    assert result["authenticated_catalog"]
    assert result["scope"] == "access_only_not_artistic_quality_or_fidelity"


def test_no_redirect_following(tmp_path):
    freeze_fixture(tmp_path)
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(307, headers={"location": "https://example.org/"})

    result = module.execute(tmp_path, "access-fixture", transport=httpx.MockTransport(handler))
    assert result["image_attempts"] == 0
    assert calls == ["127.0.0.1", "127.0.0.1"]
