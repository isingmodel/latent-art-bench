import io
import json

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import reference_delivery as s


def test_unscaled_metadata_uses_smaller_standard_size_without_changing_parent(
    tmp_path, monkeypatch
):
    candidate = dict(
        work_id="wikidata:Q1",
        item_qid="Q1",
        commons_filename="File:Example.jpg",
        expected_sha1="a" * 40,
        expected_width=1280,
        expected_height=800,
    )
    metadata = {
        "query": {
            "pages": [
                {
                    "title": "File:Example.jpg",
                    "pageid": 12,
                    "imageinfo": [
                        dict(
                            sha1="a" * 40,
                            width=1280,
                            height=800,
                            thumbwidth=1280,
                            thumbheight=800,
                            thumburl="https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.jpg",
                        )
                    ],
                }
            ]
        }
    }
    monkeypatch.setattr(s, "read_jsonl", lambda _: [candidate])
    monkeypatch.setattr(
        s,
        "events",
        lambda _: [
            dict(
                kind="response",
                url="https://example.org/?iiurlwidth=1280",
                retained_path="raw.gz",
                body_sha256="b" * 64,
            )
        ],
    )
    monkeypatch.setattr(s.d, "read_cached", lambda *_: json.dumps(metadata).encode())
    rows, omitted, _ = s.select(tmp_path)
    assert not omitted and len(rows) == 1
    assert rows[0]["delivery_width"] == 960 and rows[0]["delivery_height"] == 600
    assert (
        rows[0]["delivery_url"]
        == "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/960px-Example.jpg"
    )
    assert rows[0]["parent_sha1"] == candidate["expected_sha1"]
    metadata["query"]["pages"][0]["imageinfo"][0]["sha1"] = "c" * 40
    with pytest.raises(ValueError, match="never refresh"):
        s.select(tmp_path)


def fixture(tmp_path, monkeypatch):
    directory = tmp_path / s.DIRECTORY
    candidate = dict(
        work_id="wikidata:Q1",
        item_qid="Q1",
        expected_width=1280,
        expected_height=800,
        delivery_width=960,
        delivery_height=600,
        parent_sha1="a" * 40,
        delivery_url="https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/x.jpg/960px-x.jpg",
    )
    s.publish(directory / "deliveries.jsonl", [candidate], lines=True)
    s.publish(directory / "omissions.jsonl", [], lines=True)
    s.publish(
        directory / "acquisition_freeze.json",
        dict(
            inputs=[],
            earliest_dispatch_unix=600,
            deliveries_sha256=s.hash_file(directory / "deliveries.jsonl"),
        ),
    )
    monkeypatch.setattr(s, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(
        s.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 10 * 1024**3})()
    )
    return directory, candidate


def test_cooldown_prevents_any_dispatch(tmp_path, monkeypatch):
    directory, _ = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="cooldown"):
        s.acquire(tmp_path, now=lambda: 599)
    assert not (directory / "acquisition_events.jsonl").exists()


def test_first_rate_limit_closes_run_and_retains_retry_after(tmp_path, monkeypatch):
    directory, _ = fixture(tmp_path, monkeypatch)
    calls = []

    def handler(request):
        calls.append(request)
        assert s.events(directory / "acquisition_events.jsonl")[-1]["kind"] == "attempt"
        return httpx.Response(429, content=b"rate limited", headers={"Retry-After": "600"})

    result = s.acquire(
        tmp_path, transport=httpx.MockTransport(handler), now=lambda: 1000, sleep=lambda _: None
    )
    assert result["status"] == "stopped_provider_or_transport" and len(calls) == 1
    terminal = s.events(directory / "acquisition_events.jsonl")[-1]
    assert terminal["response_headers"]["retry-after"] == "600"
    with pytest.raises(ValueError, match="terminal"):
        s.acquire(tmp_path, transport=httpx.MockTransport(handler), now=lambda: 2000)
    assert len(calls) == 1


def test_thumbnail_has_separate_hash_and_parent_identity(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (960, 600)).save(buffer, format="JPEG")
    candidate = dict(
        item_qid="Q1",
        work_id="wikidata:Q1",
        parent_sha1="a" * 40,
        expected_width=1280,
        expected_height=800,
        delivery_width=960,
        delivery_height=600,
        delivery_url="https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/x.jpg/960px-x.jpg",
    )
    result = s.receive(
        tmp_path,
        candidate,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=buffer.getvalue())),
    )
    assert result["status"] == "acquired" and result["parent_sha1"] == "a" * 40
    assert len(result["response_sha256"]) == 64
    with pytest.raises(FileExistsError, match="no redispatch"):
        s.receive(tmp_path, candidate)
