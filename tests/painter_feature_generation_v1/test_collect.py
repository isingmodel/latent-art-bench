from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.painter_feature_generation_v1 import collect

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _config(root: Path, **overrides: object) -> Path:
    config = {
        "protocol_id": collect.PROTOCOL_ID,
        "census_id": "pfg-v1-test-20260904",
        "source_id": "test_source",
        "records_at": "data",
        "minimum_interval_seconds": 0.0,
        "requests": [
            {"request_id": "r1", "painter_id": "claude_monet", "url": "https://x.invalid/monet"},
            {"request_id": "r2", "painter_id": "alfred_sisley", "url": "https://x.invalid/sisley"},
        ],
        "paths": {
            "manifest": "out/records.jsonl",
            "receipt": "out/receipt.json",
            "workspace": "ws",
        },
    }
    config.update(overrides)
    path = root / "config.json"
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def _transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _ok(payload: object) -> httpx.Response:
    return httpx.Response(200, json=payload, headers={"Content-Type": "application/json"})


def test_every_provider_field_survives_into_the_manifest(tmp_path: Path) -> None:
    record = {
        "id": 7,
        "title": "Le Pont de Moret",
        "technique": "oil on fabric",
        "nested": {"a": [1, 2, {"b": None}]},
        "a_field_no_screen_uses": "kept anyway",
        "unicode": "Cézanne — Sainte-Victoire",
    }
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok({"data": [record], "info": {"total": 1}})

    receipt = collect.run(tmp_path, config_path, "test", _transport(handler))
    rows = [
        json.loads(line)
        for line in (tmp_path / "out/records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(rows) == 2
    assert rows[0]["record"] == record
    assert rows[0]["painter_id"] == "claude_monet"
    assert receipt["counts"]["returned_records"] == 2
    assert receipt["complete"] is True


def test_no_verdict_field_is_emitted(tmp_path: Path) -> None:
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok({"data": [{"id": 1}]})

    collect.run(tmp_path, config_path, "test", _transport(handler))
    text = (tmp_path / "out/records.jsonl").read_text(encoding="utf-8")
    for banned in (
        "screening",
        "candidate",
        "eligible",
        "disposition",
        "score",
        "authority_status",
        "admission",
    ):
        assert banned not in text, f"collection emitted a verdict field: {banned}"


def test_a_failed_request_does_not_stop_the_census(tmp_path: Path) -> None:
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("monet"):
            return httpx.Response(502, text="<html>bad gateway</html>")
        return _ok({"data": [{"id": 9}, {"id": 10}]})

    receipt = collect.run(tmp_path, config_path, "test", _transport(handler))
    assert receipt["complete"] is False
    assert receipt["counts"]["requests_succeeded"] == 1
    assert receipt["counts"]["returned_records"] == 2
    first, second = receipt["requests"]
    assert first["outcome"] == "failed"
    assert "HTTP 502" in first["error"]
    assert first["status_code"] == 502
    assert second["outcome"] == "success"
    # The failed body is still stored, so the failure is diagnosable later.
    assert (tmp_path / "ws" / first["response_body_path"]).read_bytes().startswith(b"<html>")


def test_only_the_record_path_can_fail_a_request(tmp_path: Path) -> None:
    config_path = _config(tmp_path)
    weird = {
        "id": None,
        "type": ["unexpected", "list"],
        "images": "a string where an object was expected",
        "created": 3.5,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok({"data": [weird]})

    receipt = collect.run(tmp_path, config_path, "test", _transport(handler))
    assert receipt["complete"] is True
    rows = [
        json.loads(line)
        for line in (tmp_path / "out/records.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert rows[0]["record"] == weird


def test_missing_record_path_fails_only_that_request(tmp_path: Path) -> None:
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("monet"):
            return _ok({"results": {"bindings": []}})
        return _ok({"data": [{"id": 1}]})

    receipt = collect.run(tmp_path, config_path, "test", _transport(handler))
    assert receipt["complete"] is False
    assert "no 'data'" in receipt["requests"][0]["error"]
    assert receipt["requests"][1]["outcome"] == "success"


def test_dotted_record_path_and_whole_payload_mode(tmp_path: Path) -> None:
    payload = {"results": {"bindings": [{"item": {"value": "Q1"}}, {"item": {"value": "Q2"}}]}}
    assert collect.records_from(payload, "results.bindings") == payload["results"]["bindings"]
    assert collect.records_from(payload, None) == [payload]
    with pytest.raises(collect.CollectionError, match="no 'results.missing'"):
        collect.records_from(payload, "results.missing")
    with pytest.raises(collect.CollectionError, match="not a list"):
        collect.records_from(payload, "results")


def test_outputs_are_never_overwritten(tmp_path: Path) -> None:
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok({"data": []})

    collect.run(tmp_path, config_path, "test", _transport(handler))
    with pytest.raises(collect.CollectionError, match="needs a new census ID"):
        collect.run(tmp_path, config_path, "test", _transport(handler))


def test_config_validation(tmp_path: Path) -> None:
    with pytest.raises(collect.CollectionError, match="protocol_id"):
        collect.load_config(tmp_path, _config(tmp_path, protocol_id="painter-feature-v1/2.1"))
    with pytest.raises(collect.CollectionError, match="https URL"):
        collect.load_config(
            tmp_path,
            _config(tmp_path, requests=[{"request_id": "r", "url": "http://x.invalid/a"}]),
        )
    with pytest.raises(collect.CollectionError, match="duplicated"):
        collect.load_config(
            tmp_path,
            _config(
                tmp_path,
                requests=[
                    {"request_id": "r", "url": "https://x.invalid/a"},
                    {"request_id": "r", "url": "https://x.invalid/b"},
                ],
            ),
        )
    with pytest.raises(collect.CollectionError, match="cutoff has passed"):
        collect.load_config(
            tmp_path, _config(tmp_path, execution_start_not_after_utc="2020-01-01T00:00:00Z")
        )
    with pytest.raises(collect.CollectionError, match="escapes the repository"):
        collect.load_config(
            tmp_path,
            _config(
                tmp_path,
                paths={"manifest": "/tmp/a", "receipt": "b", "workspace": "c"},
            ),
        )


def test_receipt_names_its_counts_honestly(tmp_path: Path) -> None:
    config_path = _config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return _ok({"data": [{"id": 1}]})

    receipt = collect.run(tmp_path, config_path, "maintainer, in session", _transport(handler))
    assert receipt["authorized_by"] == "maintainer, in session"
    assert set(receipt["counts"]) == {
        "requests_planned",
        "requests_succeeded",
        "returned_records",
        "returned_records_by_painter",
    }
    assert "not works and not candidates" in receipt["note"]
    assert receipt["manifest_sha256"]
    assert receipt["config_sha256"]
