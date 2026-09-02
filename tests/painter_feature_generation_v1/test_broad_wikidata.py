import hashlib
import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import broad_wikidata
from latent_art_bench.painter_feature_generation_v1.broad_wikidata import (
    BroadDiscoveryError,
    _validate_event_chain,
    build_intents,
    execute,
    load_config,
    parse_result,
    prepare,
    required_frozen_paths,
)

_VALID_DATE = "Wed, 02 Sep 2026 12:00:00 GMT"


def _config() -> dict:
    return {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-config/1.0",
        "census_id": "test-broad",
        "protocol_id": "painter-feature-generation-v1/2.0",
        "protocol_path": "studies/painter_feature_generation_v1/PROTOCOL.md",
        "scope": {
            "metadata_requests": True,
            "image_downloads": False,
            "active_study_admission": False,
            "visual_coding": False,
            "feature_extraction": False,
            "generation": False,
        },
        "source_contract": {
            "endpoint": "https://query.wikidata.org/sparql",
            "method": "GET",
            "accept": "application/sparql-results+json",
            "timeout_seconds": 1.0,
            "minimum_interval_seconds": 0.0,
            "redirects": "forbidden",
            "api_version": "test API",
            "data_version": "test mutable dataset",
            "request_not_after_utc": "2099-01-01T00:00:00Z",
            "canonicalization_rule": "strict test rule",
            "duplicate_rule": "reject test duplicates",
            "raw_response_rule": "hash test bytes",
            "rights_and_media_rule": "not in test scope",
        },
        "painters": [
            {"painter_id": "monet", "creator_qid": "Q296"},
            {"painter_id": "sisley", "creator_qid": "Q175130"},
            {"painter_id": "pissarro", "creator_qid": "Q134741"},
            {"painter_id": "cezanne", "creator_qid": "Q35548"},
        ],
        "query_template": (
            "SELECT DISTINCT ?item ?image WHERE { ?item wdt:P170 wd:{creator_qid}; "
            "wdt:P31 wd:Q3305213; wdt:P18 ?image. } "
            "ORDER BY STR(?item) STR(?image)"
        ),
        "paths": {
            "request_intents": "data/intents.jsonl",
            "request_events": "data/events.jsonl",
            "candidate_manifest": "data/candidates.jsonl",
            "execution_receipt": "data/receipt.json",
            "workspace": "workspace",
        },
    }


def _intent() -> dict:
    return {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-intent/1.0",
        "census_id": "test-broad",
        "request_id": "broad-wikidata-0001",
        "sequence": 1,
        "method": "GET",
        "endpoint": "https://query.wikidata.org/sparql",
        "params": {},
        "encoded_url": "https://query.wikidata.org/sparql",
        "painter_id": "monet",
        "creator_qid": "Q296",
        "material_filter_present": False,
    }


def _payload(*pairs: tuple[str, str]) -> dict:
    return {
        "head": {"vars": ["item", "image"]},
        "results": {
            "bindings": [
                {
                    "item": {
                        "type": "uri",
                        "value": f"http://www.wikidata.org/entity/{qid}",
                    },
                    "image": {
                        "type": "uri",
                        "value": (
                            "http://commons.wikimedia.org/wiki/Special:FilePath/"
                            + filename.replace(" ", "_")
                        ),
                    },
                }
                for qid, filename in pairs
            ]
        },
    }


def test_intents_are_four_exact_no_material_queries() -> None:
    rows = build_intents(_config())
    assert len(rows) == 4
    assert [row["sequence"] for row in rows] == [1, 2, 3, 4]
    assert {row["creator_qid"] for row in rows} == {
        "Q296",
        "Q175130",
        "Q134741",
        "Q35548",
    }
    assert all("P186" not in row["params"]["query"] for row in rows)
    assert all(row["material_filter_present"] is False for row in rows)


def test_parse_result_preserves_rows_without_admission() -> None:
    rows = parse_result(
        _payload(("Q1", "A.jpg"), ("Q2", "B image.png")),
        _intent(),
    )
    assert [row["item_qid"] for row in rows] == ["Q1", "Q2"]
    assert [row["commons_filename"] for row in rows] == ["A.jpg", "B image.png"]
    assert all(row["active_study_admission"] is False for row in rows)
    assert all("not_authority_verified" in row["discovery_status"] for row in rows)


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "unexpected top-level"),
        (
            {"head": {"vars": ["image", "item"]}, "results": {"bindings": []}},
            "unexpected variables",
        ),
        (
            _payload(("Q2", "B.jpg"), ("Q1", "A.jpg")),
            "unordered or duplicated",
        ),
        (
            _payload(("Q1", "A.jpg"), ("Q1", "A.jpg")),
            "unordered or duplicated",
        ),
        (
            {
                **_payload(("Q1", "A.jpg")),
                "warnings": {"query": "result may be incomplete"},
            },
            "unexpected top-level",
        ),
        (
            {
                "head": {"vars": ["item", "image"]},
                "results": {"bindings": [], "next": "cursor"},
            },
            "lacks bindings",
        ),
    ],
)
def test_parse_result_fails_closed(payload: dict, message: str) -> None:
    with pytest.raises(BroadDiscoveryError, match=message):
        parse_result(payload, _intent())


def test_load_config_rejects_material_filter(tmp_path: Path) -> None:
    protocol = tmp_path / "studies/painter_feature_generation_v1/PROTOCOL.md"
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Protocol ID: `painter-feature-generation-v1/2.0`\n")
    config = _config()
    config["query_template"] += " # P186"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    with pytest.raises(BroadDiscoveryError, match="no-P186"):
        load_config(tmp_path, path)


def _build_authorized_tree(tmp_path: Path) -> tuple[Path, Path, str]:
    config = _config()
    protocol = tmp_path / config["protocol_path"]
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Protocol ID: `painter-feature-generation-v1/2.0`\n")
    config_path = tmp_path / "configs/painter_feature_generation_v1/config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps(config))
    prepare(tmp_path, config_path)
    placeholder_paths = {
        ".gitignore",
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_broad_wikidata.py",
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/config.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/schemas.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_wikidata.py",
        "tests/conftest.py",
        "tests/painter_feature_generation_v1/test_broad_wikidata.py",
    }
    for relative in placeholder_paths:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative + "\n")
    required = required_frozen_paths(tmp_path, config, config_path)
    entries = [{"path": path, "sha256": hash_file(tmp_path / path)} for path in required]
    aggregate = hashlib.sha256(canonical_json(entries).encode()).hexdigest()
    freeze_path = tmp_path / "data/freeze.json"
    freeze = {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-freeze/1.0",
        "status": "sealed_for_neutral_quality_review",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "scope": config["scope"],
        "frozen_inputs": entries,
        "frozen_input_set_sha256": aggregate,
        "preexecution_outputs": broad_wikidata.expected_outputs(tmp_path, config),
    }
    freeze_path.parent.mkdir(parents=True, exist_ok=True)
    freeze_path.write_text(canonical_json(freeze) + "\n")
    review_path = tmp_path / "data/review.json"
    review = {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-review/1.0",
        "decision": "APPROVE_BROAD_WIKIDATA_METADATA_ONLY",
        "blocking_findings": [],
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "independent_reviewer": "test-neutral-reviewer",
        "approved_scope": config["scope"],
        "reviewed_freeze_path": "data/freeze.json",
        "reviewed_freeze_sha256": hash_file(freeze_path),
    }
    review_path.write_text(canonical_json(review) + "\n")
    seal_path = tmp_path / "data/seal.json"
    seal = {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-authorization/1.0",
        "status": "authorized_for_broad_wikidata_metadata_execution",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "authorization_scope": config["scope"],
        "freeze_path": "data/freeze.json",
        "freeze_sha256": hash_file(freeze_path),
        "review_path": "data/review.json",
        "review_sha256": hash_file(review_path),
    }
    seal_path.write_text(canonical_json(seal) + "\n")
    return config_path, seal_path, hash_file(seal_path)


def test_execute_completes_exact_four_request_census(tmp_path: Path) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        query = request.url.params["query"]
        qid = next(value for value in ("Q296", "Q175130", "Q134741", "Q35548") if value in query)
        item = {"Q296": "Q1", "Q175130": "Q2", "Q134741": "Q3", "Q35548": "Q4"}[qid]
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/sparql-results+json",
                "Date": _VALID_DATE,
            },
            json=_payload((item, f"{qid}.jpg")),
            request=request,
        )

    receipt = execute(
        tmp_path,
        config_path,
        seal_path,
        seal_hash,
        transport=httpx.MockTransport(handler),
    )
    assert len(calls) == 4
    assert receipt["successful_requests"] == 4
    assert receipt["counts"]["item_image_rows"] == 4
    assert receipt["counts"]["active_study_admissions"] == 0
    event_lines = (tmp_path / "data/events.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in event_lines]
    assert len(events) == 9
    _validate_event_chain(events, "test-broad")


def test_execute_stops_on_first_non_200(tmp_path: Path) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable", request=request)

    with pytest.raises(BroadDiscoveryError, match="terminal_http_or_delivery_failure"):
        execute(
            tmp_path,
            config_path,
            seal_path,
            seal_hash,
            transport=httpx.MockTransport(handler),
        )
    assert not (tmp_path / "data/candidates.jsonl").exists()
    assert not (tmp_path / "data/receipt.json").exists()


def test_execute_records_terminal_event_for_non_utf8_json(tmp_path: Path) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/sparql-results+json",
                "Date": _VALID_DATE,
            },
            content=b"\xff",
            request=request,
        )

    with pytest.raises(BroadDiscoveryError, match="terminal_schema_failure"):
        execute(
            tmp_path,
            config_path,
            seal_path,
            seal_hash,
            transport=httpx.MockTransport(handler),
        )
    events = [
        json.loads(line) for line in (tmp_path / "data/events.jsonl").read_text().splitlines()
    ]
    assert events[-1]["event_type"] == "request_finished"
    assert events[-1]["outcome"] == "terminal_schema_failure"
    assert not (tmp_path / "data/candidates.jsonl").exists()
    assert not (tmp_path / "data/receipt.json").exists()


@pytest.mark.parametrize("date_header", [None, "not-a-date"])
def test_execute_rejects_missing_or_malformed_provider_date(
    tmp_path: Path, date_header: str | None
) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        headers = {"Content-Type": "application/sparql-results+json"}
        if date_header is not None:
            headers["Date"] = date_header
        return httpx.Response(200, headers=headers, json=_payload(), request=request)

    with pytest.raises(BroadDiscoveryError, match="terminal_http_or_delivery_failure"):
        execute(
            tmp_path,
            config_path,
            seal_path,
            seal_hash,
            transport=httpx.MockTransport(handler),
        )
    events = [
        json.loads(line) for line in (tmp_path / "data/events.jsonl").read_text().splitlines()
    ]
    assert events[-1]["outcome"] == "terminal_http_or_delivery_failure"
    assert "Date" in events[-1]["error"]


@pytest.mark.parametrize(
    "image_uri",
    [
        "https://user@commons.wikimedia.org/wiki/Special:FilePath/A.jpg",
        "https://commons.wikimedia.org:443/wiki/Special:FilePath/A.jpg",
        "https://commons.wikimedia.org/extra/wiki/Special:FilePath/A.jpg",
        "https://commons.wikimedia.org/wiki/Special:FilePath/%FF.jpg",
        "https://commons.wikimedia.org/wiki/Special:FilePath/A%7CB.jpg",
        "https://commons.wikimedia.org/wiki/Special:FilePath/A\\B.jpg",
        'https://commons.wikimedia.org/wiki/Special:FilePath/A"B.jpg',
        "https://commons.wikimedia.org/wiki/Special:FilePath/A^B.jpg",
        "https://commons.wikimedia.org/wiki/Special:FilePath/A`B.jpg",
        "https://[broken/wiki/Special:FilePath/A.jpg",
    ],
)
def test_parse_result_rejects_noncanonical_commons_uri(image_uri: str) -> None:
    payload = _payload(("Q1", "A.jpg"))
    payload["results"]["bindings"][0]["image"]["value"] = image_uri
    with pytest.raises(
        BroadDiscoveryError,
        match="Commons filename|invalid item or image|malformed image URI",
    ):
        parse_result(payload, _intent())


def test_parse_result_rejects_canonical_duplicate() -> None:
    payload = _payload(("Q1", "A%20B.jpg"), ("Q1", "A_B.jpg"))
    with pytest.raises(BroadDiscoveryError, match="unordered or duplicated"):
        parse_result(payload, _intent())


def test_parse_result_accepts_valid_commons_punctuation() -> None:
    rows = parse_result(
        _payload(("Q1", "L'art_%22study%22%5E%60.jpg")),
        _intent(),
    )
    assert rows[0]["commons_filename"] == "L'art \"study\"^`.jpg"


def test_parse_result_rejects_extra_uri_cell_fields() -> None:
    payload = _payload(("Q1", "A.jpg"))
    payload["results"]["bindings"][0]["image"]["xml:lang"] = "en"
    with pytest.raises(BroadDiscoveryError, match="not a URI"):
        parse_result(payload, _intent())


def test_execute_rejects_preclaimed_one_shot_lock(tmp_path: Path) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)
    lock = tmp_path / "workspace/execution.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("already claimed\n")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json=_payload(), request=request)

    with pytest.raises(BroadDiscoveryError, match="preexecution output is not absent"):
        execute(
            tmp_path,
            config_path,
            seal_path,
            seal_hash,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0


def test_execute_rechecks_cutoff_immediately_before_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_hash = _build_authorized_tree(tmp_path)
    checks = 0
    calls = 0

    def boundary_cutoff(source: dict) -> None:
        nonlocal checks
        checks += 1
        if checks == 3:
            raise BroadDiscoveryError("broad Wikidata request cutoff has passed")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"Content-Type": "application/sparql-results+json", "Date": _VALID_DATE},
            json=_payload(),
            request=request,
        )

    monkeypatch.setattr(broad_wikidata, "_enforce_request_cutoff", boundary_cutoff)
    with pytest.raises(BroadDiscoveryError, match="cutoff has passed"):
        execute(
            tmp_path,
            config_path,
            seal_path,
            seal_hash,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    events = [
        json.loads(line) for line in (tmp_path / "data/events.jsonl").read_text().splitlines()
    ]
    assert events[-1]["outcome"] == "terminal_request_cutoff_failure"
