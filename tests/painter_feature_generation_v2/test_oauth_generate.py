import base64
import importlib.metadata
import io
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2 import oauth_generate as module
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    append_event,
    digest,
    publish,
)

ROOT = Path(__file__).resolve().parents[2]


def fixture(root):
    config, library = read_json(ROOT / module.CONFIG), read_json(ROOT / module.PROMPTS)
    publish(root / module.PROMPTS, library)
    requests = module.request_grid(config, library)
    output = root / MANIFESTS / "oauth-fixture"
    publish(output / "requests.jsonl", requests, lines=True)
    publish(
        output / "generation_freeze.json",
        dict(
            inputs=[],
            config=config,
            requests_sha256=hash_file(output / "requests.jsonl"),
            software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
        ),
    )
    return config, requests, output


def image_payload(size=(512, 512)):
    out = io.BytesIO()
    Image.new("RGB", size, "white").save(out, format="PNG")
    return dict(
        data=[dict(b64_json=base64.b64encode(out.getvalue()).decode())],
        size=f"{size[0]}x{size[1]}",
        quality="low",
    )


def test_complete_paired_alias_grid_is_exact_and_seedless(tmp_path):
    config, rows, _ = fixture(tmp_path)
    assert len(rows) == len({r["request_id"] for r in rows}) == 160
    for first, second in zip(rows[::2], rows[1::2]):
        assert first["cell_id"] == second["cell_id"]
        assert first["alias"] != second["alias"]
        assert first["payload"]["prompt"] == second["payload"]["prompt"]
        assert "seed" not in first["payload"]
    with pytest.raises(ValueError):
        module.request_grid(dict(config, maximum_requests=4000), read_json(ROOT / module.PROMPTS))


def test_service_contract_retains_requested_returned_difference(tmp_path):
    _, requests, _ = fixture(tmp_path)
    body, info = module.decode(image_payload((1254, 1254)), requests[0], 512)
    assert body and info["width"] == 1254
    assert set(info["requested_returned_mismatches"]) == {"size", "quality", "decoded_size"}
    assert not info["model_snapshot_independently_verified"]
    with pytest.raises(ValueError, match="upsampling"):
        module.decode(image_payload((256, 256)), requests[0], 512)
    with pytest.raises(ValueError, match="URLs"):
        module.decode({"data": [{"url": "https://example.org/"}]}, requests[0], 512)


def test_quota_failure_closes_all_requests_without_retry(tmp_path):
    fixture(tmp_path)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.url.host == "127.0.0.1" and request.url.port == 10532
        assert "authorization" not in request.headers
        return httpx.Response(429, json={"error": {"code": "rate_limit_exceeded"}})

    result = module.execute(
        tmp_path, "oauth-fixture", transport=httpx.MockTransport(handler), sleep=lambda _: None
    )
    assert len(calls) == result["image_attempts"] == 1
    assert result["terminal_requests"] == 160
    assert result["statuses"] == {"quota_or_rate_limited": 1, "not_attempted": 159}
    assert not result["complete_generated_grid"]
    with pytest.raises(FileExistsError):
        module.execute(tmp_path, "oauth-fixture", transport=httpx.MockTransport(handler))


def test_unknown_interrupted_outcome_is_never_rerolled(tmp_path):
    _, requests, output = fixture(tmp_path)
    append_event(
        output / "generation_events.jsonl",
        dict(
            kind="attempt", request_id=requests[0]["request_id"], request_sha256=digest(requests[0])
        ),
    )
    with pytest.raises(ValueError, match="uncertain"):
        module.execute(
            tmp_path,
            "oauth-fixture",
            transport=httpx.MockTransport(lambda _: pytest.fail("network must not be reached")),
        )


def test_redirect_and_partial_bytes_are_retained_without_following(tmp_path):
    config, requests, _ = fixture(tmp_path)
    small = dict(config, maximum_response_bytes=10)
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=b"x" * 50))
    ) as client:
        result = module._request(client, tmp_path, "oauth-fixture", requests[0], small)
    assert result["partial_body"] and result["bytes"] == 10
    assert result["status"] == "transport_failure"
    assert (tmp_path / result["raw_path"]).read_bytes() == b"x" * 10
    with httpx.Client(
        follow_redirects=False,
        transport=httpx.MockTransport(
            lambda _: httpx.Response(307, headers={"location": "https://example.org/"})
        ),
    ) as client:
        result = module._request(client, tmp_path, "oauth-fixture", requests[0], config)
    assert result["status"] != "generated" and result["http_status"] == 307
