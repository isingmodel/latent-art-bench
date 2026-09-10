"""Offline contract checks; all HTTP responses are artificial."""

import importlib.util
import json
import subprocess
from pathlib import Path

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location(
    "map_metadata_preflight", Path(__file__).parents[2]
    / "studies/painter_map_validation_v1/preflight.py",
)
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)
SECRET = "dummy-do-not-use-secret-123456789"


@pytest.fixture
def root(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Test", "-c",
                    "user.email=test@example.invalid", "commit", "-qm", "fixture",
                    "--allow-empty"], check=True)
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=" + SECRET + "\n")
    return tmp_path


def model():
    return dict(id=preflight.MODEL, endpoints=[dict(
        provider_slug=preflight.PROVIDER, provider_tag=preflight.PROVIDER,
        pricing=[dict(billable="output_image", unit="megapixel", cost_usd=0.07)],
    )])


def test_exact_two_gets_create_once_and_private_projection(root):
    requests = []

    def respond(request):
        requests.append(request)
        assert request.method == "GET"
        if str(request.url) == preflight.CREDITS:
            assert request.headers["authorization"] == "Bearer " + SECRET
            return httpx.Response(200, json={"data": {
                "total_credits": 50, "total_usage": "45.7273557", "account_id": "private",
            }})
        assert str(request.url) == preflight.ENDPOINTS
        assert "authorization" not in request.headers
        return httpx.Response(200, json=model())

    result = preflight.run(root, "one", live_metadata=True, transport=httpx.MockTransport(respond))
    assert result["status"] == "complete"
    assert len(requests) == 2
    assert result["requests"][0]["projection"] == {"available_usd": "4.2726443"}
    assert result["requests"][1]["projection"]["pricing"][0]["cost_usd"] == "0.07"
    text = (root / preflight.DIRECTORY / "one/receipt.json").read_text()
    assert all(s not in text for s in (SECRET, "account_id", "total_usage", "private"))
    with pytest.raises(FileExistsError):
        preflight.run(root, "one", live_metadata=True, transport=httpx.MockTransport(respond))
    assert len(requests) == 2


def test_default_blocks_network(root):
    with pytest.raises(ValueError, match="explicit"):
        preflight.run(root, "one")
    assert not (root / preflight.DIRECTORY).exists()


@pytest.mark.parametrize("case", [
    "redirect", "timeout", "oversize", "secret_echo", "escaped_secret", "wrong_model",
])
def test_failure_no_retry_or_sensitive_output(root, monkeypatch, case):
    calls = []
    monkeypatch.setattr(preflight, "MAX_BYTES", 1024)

    def respond(request):
        calls.append(request)
        if str(request.url) == preflight.CREDITS:
            if case == "redirect":
                return httpx.Response(302, headers={"location": "https://example.invalid/"})
            if case == "timeout":
                raise httpx.ReadTimeout(SECRET, request=request)
            if case == "oversize":
                return httpx.Response(200, content=b"x" * 1025)
            if case == "secret_echo":
                return httpx.Response(200, json={"secret": SECRET})
            return httpx.Response(200, json={"data": {"total_credits": 50, "total_usage": 45}})
        value = model()
        if case == "wrong_model":
            value["id"] = "another-model"
        if case == "escaped_secret":
            value["endpoints"][0]["pricing"][0]["unit"] = SECRET
            escaped = "".join("\\u%04x" % ord(c) for c in SECRET)
            return httpx.Response(200, content=json.dumps(value).replace(SECRET, escaped).encode())
        return httpx.Response(200, json=value)

    result = preflight.run(root, "one", live_metadata=True, transport=httpx.MockTransport(respond))
    assert result["status"] == "incomplete"
    assert [str(x.url) for x in calls] == list(preflight.URLS)
    assert SECRET not in json.dumps(result)


def test_unapproved_url_never_dispatched():
    with httpx.Client(transport=httpx.MockTransport(lambda _: pytest.fail("network"))) as client:
        with pytest.raises(ValueError, match="exact two-GET"):
            preflight.fetch(client, "https://openrouter.ai/api/v1/models", SECRET)


def test_json_decimal_precision_is_preserved(root):
    def respond(request):
        if str(request.url) == preflight.CREDITS:
            return httpx.Response(200, content=(
                b'{"data":{"total_credits":50.1234567890123456789,"total_usage":45.0}}'
            ))
        return httpx.Response(200, json=model())

    result = preflight.run(root, "precise", live_metadata=True,
                           transport=httpx.MockTransport(respond))
    assert result["requests"][0]["projection"]["available_usd"] == "5.1234567890123456789"


@pytest.mark.parametrize("bad", [
    [], {"data": []}, {"id": preflight.MODEL, "endpoints": ["wrong-node"]},
])
def test_malformed_nodes_get_terminal_unavailable_receipt(root, bad):
    result = preflight.run(root, "malformed", live_metadata=True,
                           transport=httpx.MockTransport(lambda _: httpx.Response(200, json=bad)))
    assert result["status"] == "incomplete"
    assert all(row["status"] == "unavailable" for row in result["requests"])
    assert (root / preflight.DIRECTORY / "malformed/receipt.json").is_file()
