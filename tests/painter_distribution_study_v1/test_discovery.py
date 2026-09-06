import gzip
import json

import httpx
import pytest

from latent_art_bench.painter_distribution_study_v1 import discovery as d


@pytest.mark.parametrize(
    "url",
    [
        "http://openrouter.ai/api/v1/models",
        "https://openrouter.ai.example.org/api/v1/models",
        "https://openrouter.ai/api/v1/images",
        "https://openrouter.ai/api/v1/keys/delete",
        "https://commons.wikimedia.org/w/api.php?action=edit",
        "https://api.artic.edu/api/v1/artworks?api_key=secret",
        "https://user:pass@openrouter.ai/api/v1/models",
    ],
)
def test_read_only_metadata_source_boundaries(url):
    with pytest.raises(ValueError):
        d.validate_url(url)


def test_secret_reading_never_executes_shell(tmp_path):
    key = "sk-or-test-" + "x" * 30
    (tmp_path / ".env").write_text(f'OPENROUTER_API_KEY="{key}"\n')
    assert d.key_from_env(tmp_path) == key
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=$(echo unsafe)\n")
    with pytest.raises(ValueError, match="unsupported configuration"):
        d.key_from_env(tmp_path)


def test_account_projection_excludes_identifiers():
    body = json.dumps(
        {
            "data": {
                "label": "private",
                "hash": "private-hash",
                "limit": 100,
                "limit_remaining": 98.5,
                "total_usage": 1.5,
            }
        }
    ).encode()
    assert d.account_projection(body) == {"limit": 100, "limit_remaining": 98.5, "total_usage": 1.5}
    assert d.account_projection(b'{"data":null}') == {"body_suppressed": True}


def test_authenticated_reads_are_cached_without_storing_key_or_account_labels(
    tmp_path, monkeypatch
):
    directory = tmp_path / d.DIRECTORY
    directory.mkdir(parents=True)
    (directory / "freeze.json").write_text('{"inputs": []}')
    monkeypatch.setattr(d, "committed", lambda *_: "a" * 40)
    secret = "sk-or-test-" + "y" * 30
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=" + secret)
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        assert request.headers["Authorization"] == "Bearer " + secret
        return httpx.Response(200, json={"data": {"label": "private-name", "limit": 75}})

    transport = httpx.MockTransport(handler)
    url = "https://openrouter.ai/api/v1/key"
    first, body = d.fetch(tmp_path, url, transport=transport, sleep=lambda _: None)
    second, other = d.fetch(tmp_path, url, transport=transport, sleep=lambda _: None)
    assert len(calls) == 1
    assert first == second and body == other
    assert json.loads(body) == {"limit": 75}
    for path in directory.rglob("*"):
        if path.is_file():
            assert secret.encode() not in path.read_bytes()
            assert b"private-name" not in path.read_bytes()
    retained = gzip.decompress((tmp_path / first["retained_path"]).read_bytes())
    assert secret.encode() not in retained
    d.publish(directory / "terminal_receipt.json", {"terminal": True})
    with pytest.raises(ValueError, match="terminal"):
        d.fetch(tmp_path, url, transport=transport, sleep=lambda _: None)
