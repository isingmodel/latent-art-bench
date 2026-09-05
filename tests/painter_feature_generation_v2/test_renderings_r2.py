import hashlib
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_feature_generation_v2 import renderings_r2 as module


def png(width, height):
    out = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(out, format="PNG")
    return out.getvalue()


def test_documented_host_and_larger_standard_size_are_recognized():
    url = "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Test.png/1920px-Test.png"
    assert module.url_kind(url) == ("thumbnail", 1920)
    row = dict(
        url=url, source_width=3000, source_height=2000, expected_width=1536, expected_height=1024
    )
    result = module.inspect_body(png(1920, 1280), row)
    assert result["differs_from_reported_dimensions"]
    assert result["width"] == 1920
    with pytest.raises(ValueError, match="aspect"):
        module.inspect_body(png(1920, 1100), row)


def test_native_original_uses_source_hash_and_geometry_not_requested_thumbnail_size():
    body = png(1800, 1200)
    row = dict(
        url="https://upload.wikimedia.org/wikipedia/commons/a/ab/Test.png?x=1",
        source_sha1=hashlib.sha1(body).hexdigest(),
        source_width=1800,
        source_height=1200,
        expected_width=1600,
        expected_height=1067,
    )
    result = module.inspect_body(body, row)
    assert result["source_kind"] == "original"
    assert result["differs_from_reported_dimensions"]
    with pytest.raises(ValueError, match="sha1"):
        module.inspect_body(body, dict(row, source_sha1="0" * 40))


@pytest.mark.parametrize(
    "url",
    [
        "https://thumb.wikimedia.org.evil.example/wikipedia/commons/thumb/a/b/f/1920px-f.jpg",
        "http://thumb.wikimedia.org/wikipedia/commons/thumb/a/b/f/1920px-f.jpg",
        "https://user@thumb.wikimedia.org/wikipedia/commons/thumb/a/b/f/1920px-f.jpg",
        "https://thumb.wikimedia.org:8080/wikipedia/commons/thumb/a/b/f/1920px-f.jpg",
        "https://thumb.wikimedia.org/wikipedia/commons/a/b/original.jpg",
    ],
)
def test_transport_allowlist_is_exact(url):
    with pytest.raises(ValueError):
        module.url_kind(url)


def test_redirect_is_not_followed():
    calls = []

    def handler(request):
        calls.append(request.url.host)
        return httpx.Response(302, headers={"location": "https://example.org/"})

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
        status, _, _, _ = module.fetch(
            client, "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/b/f/1920px-f.jpg"
        )
    assert status == 302 and calls == ["thumb.wikimedia.org"]
