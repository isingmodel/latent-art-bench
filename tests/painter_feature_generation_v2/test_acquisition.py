from __future__ import annotations

import hashlib
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_feature_generation_v2 import acquire


def image_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (1536, 1024), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_acquisition_binds_the_actual_snapshot_image():
    body = image_bytes()
    surrogate = dict(expected_sha1=hashlib.sha1(body).hexdigest(),
                     expected_width=1536, expected_height=1024)
    assert acquire.inspect_body(body, surrogate)["width"] == 1536
    with pytest.raises(ValueError, match="snapshot_sha1_mismatch"):
        acquire.inspect_body(body + b"changed", surrogate)
    surrogate["expected_width"] = 1024
    with pytest.raises(ValueError, match="dimensions_mismatch"):
        acquire.inspect_body(body, surrogate)


def test_fetch_does_not_follow_provider_redirects():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(302, headers={"Location": "https://example.org/other.jpg"})

    with httpx.Client(transport=httpx.MockTransport(handle), follow_redirects=False) as client:
        status, _headers, _body = acquire.fetch(client, "https://upload.wikimedia.org/a.jpg")
    assert status == 302
    assert calls == ["https://upload.wikimedia.org/a.jpg"]


def test_nonallowlisted_url_is_rejected_before_transport():
    def handle(request):
        pytest.fail("must not make a request")

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ValueError, match="nonallowlisted"):
            acquire.fetch(client, "http://127.0.0.1/private")
