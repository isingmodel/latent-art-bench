import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v1 import federated_census
from latent_art_bench.painter_feature_generation_v1.federated_census import (
    CensusError,
    RequestSpec,
    _append_event,
    _attempt_maps,
    _ensure_execution_genesis,
    _execute_specs,
    _load_event_ledger,
    _reference_urls,
    _repo_path,
    _retry_after_seconds,
    _specs_from_intents,
    _statement_values,
    _validate_seal,
    _validate_stage_payload,
    build_candidate_manifest,
    build_request_specs,
    load_discovery_rows,
    parse_entity_batches,
    parse_media_batches,
    summarize_manifest,
)

PAINTERS = {"Q296": "claude_monet"}


def _binding(creator: str, item: str, filename: str) -> dict:
    return {
        "creator": {"type": "uri", "value": f"http://www.wikidata.org/entity/{creator}"},
        "item": {"type": "uri", "value": f"http://www.wikidata.org/entity/{item}"},
        "image": {
            "type": "uri",
            "value": f"http://commons.wikimedia.org/wiki/Special:FilePath/{filename}",
        },
    }


def _config() -> dict:
    return {
        "census_id": "test-census",
        "request_contract": {
            "user_agent": "test-agent",
            "timeout_seconds": 1.0,
            "minimum_interval_seconds": 0.0,
            "retry_backoff_base_seconds": 0.0,
            "maximum_retry_wait_seconds": 30.0,
            "maximum_attempts": 2,
            "batch_size": 40,
            "wikidata_endpoint": "https://www.wikidata.org/w/api.php",
            "commons_endpoint": "https://commons.wikimedia.org/w/api.php",
            "wikidata_properties": "info|claims|labels|descriptions",
            "commons_imageinfo_properties": (
                "url|size|mime|sha1|timestamp|canonicaltitle|extmetadata"
            ),
            "commons_extmetadata_fields": (
                "LicenseShortName|LicenseUrl|UsageTerms|Copyrighted|Restrictions|Permission|"
                "Artist|Institution|Credit|Source|ObjectName|ImageDescription"
            ),
            "retryable_http_status_codes": [429, 500, 502, 503, 504],
            "retryable_api_error_codes": ["maxlag"],
        },
        "screening_contract": {
            "minimum_short_side_pixels": 1024,
            "allowed_commons_license_url_prefixes": [
                "https://creativecommons.org/licenses/by/",
                "https://creativecommons.org/publicdomain/mark/",
            ],
            "allowed_unlinked_license_short_names": ["cc0", "public domain"],
            "nonfree_markers": ["fair use", "non-free", "permission required"],
            "supported_image_mime_types": ["image/jpeg", "image/png"],
        },
        "paths": {
            "planned_requests": "intents.jsonl",
            "request_events": "events.jsonl",
            "candidate_manifest": "candidates.jsonl",
            "execution_receipt": "receipt.json",
            "workspace": "workspace",
        },
    }


def _valid_entity(entity_id: str = "Q1") -> dict:
    return {
        "id": entity_id,
        "labels": {},
        "descriptions": {},
        "lastrevid": 123,
        "modified": "2026-09-02T00:00:00Z",
        "claims": {},
    }


def _entity_with_p854_reference(snak: dict) -> dict:
    entity = _valid_entity()
    entity["claims"] = {
        "P31": [
            {
                "rank": "normal",
                "mainsnak": {
                    "snaktype": "value",
                    "datavalue": {"value": {"id": "Q3305213"}},
                },
                "references": [{"snaks": {"P854": [snak]}}],
            }
        ]
    }
    return entity


def _test_genesis(path: Path) -> list[dict]:
    events: list[dict] = []
    _append_event(
        path,
        "test-census",
        events,
        {
            "event_type": "execution_started",
            "started_at_utc": "2026-09-02T00:00:00Z",
        },
    )
    return events


def _media_payload(*, metadata: dict | None = None, info_overrides: dict | None = None) -> dict:
    info = {
        "url": "https://upload.wikimedia.org/a.jpg",
        "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
        "width": 2000,
        "height": 1500,
        "mime": "image/jpeg",
        "sha1": "a" * 40,
        "timestamp": "2026-01-01T00:00:00Z",
        "canonicaltitle": "File:A.jpg",
        "extmetadata": metadata
        or {
            "LicenseShortName": {"value": "Public domain"},
            "LicenseUrl": {"value": "https://creativecommons.org/publicdomain/mark/1.0/"},
            "Copyrighted": {"value": "False"},
        },
    }
    info.update(info_overrides or {})
    return {
        "batchcomplete": True,
        "query": {"pages": [{"title": "File:A.jpg", "imageinfo": [info]}]},
    }


def test_discovery_input_is_hash_bound_and_normalized(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text(
        json.dumps(
            {
                "results": {
                    "bindings": [
                        _binding("Q296", "Q2", "Monet%20B.jpg"),
                        _binding("Q296", "Q1", "Monet_A.jpg"),
                    ]
                }
            }
        )
    )
    rows = load_discovery_rows(path, hash_file(path), PAINTERS, 2, 2, 2)
    assert [row["item_qid"] for row in rows] == ["Q1", "Q2"]
    assert rows[0]["commons_filename"] == "Monet A.jpg"
    with pytest.raises(CensusError, match="SHA-256 drift"):
        load_discovery_rows(path, "0" * 64, PAINTERS, 2, 2, 2)


def test_requests_are_complete_deterministic_batches() -> None:
    rows = [
        {
            "painter_id": "claude_monet",
            "creator_qid": "Q296",
            "item_qid": "Q1",
            "commons_filename": "B.jpg",
        },
        {
            "painter_id": "claude_monet",
            "creator_qid": "Q296",
            "item_qid": "Q2",
            "commons_filename": "A.jpg",
        },
    ]
    specs = build_request_specs(_config(), rows)
    assert [(spec.stage, spec.members) for spec in specs] == [
        ("wikidata_entities", ("Q1", "Q2")),
        ("commons_imageinfo", ("File:A.jpg", "File:B.jpg")),
    ]
    assert [spec.sequence for spec in specs] == [1, 2]
    assert "redirects" not in specs[0].params
    assert specs[0].params["servedby"] == "1"
    assert specs[1].params["iilimit"] == "1"
    assert specs[1].params["iimetadataversion"] == "1"
    assert specs[1].params["iiextmetadatalanguage"] == "en"
    assert "iistart" not in specs[1].params
    assert "iiurlwidth" not in specs[1].params
    assert "redirects" not in specs[1].params


def test_statement_values_follow_wikibase_best_rank_semantics() -> None:
    def claim(value: str, rank: str) -> dict:
        return {
            "rank": rank,
            "mainsnak": {
                "snaktype": "value",
                "datavalue": {"value": {"id": value}},
            },
        }

    entity = {
        "claims": {
            "P170": [
                claim("Q1", "normal"),
                claim("Q2", "preferred"),
                claim("Q3", "deprecated"),
            ],
            "P186": [claim("Q4", "normal"), claim("Q5", "deprecated")],
        }
    }
    assert _statement_values(entity, "P170") == ["Q2"]
    assert _statement_values(entity, "P186") == ["Q4"]


def test_wikidata_redirects_are_rejected() -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test",
        {},
        ("Q1",),
    )
    payload = {
        "entities": {"Q1": _valid_entity("Q2")},
    }
    with pytest.raises(CensusError, match="redirected or changed identity"):
        _validate_stage_payload(spec, payload)


def test_wikidata_language_fallback_terms_are_validated_without_rejection() -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test",
        {},
        ("Q1",),
    )
    entity = _valid_entity()
    entity["labels"] = {
        "en": {"language": "en", "value": "Rocks"},
        "fr": {"language": "en", "for-language": "fr", "value": "Rocks"},
    }
    assert (
        _validate_stage_payload(spec, {"entities": {"Q1": entity}})
        == "complete_wikidata_entity_batch"
    )
    entity["labels"]["fr"]["for-language"] = "de"
    with pytest.raises(CensusError, match="malformed labels"):
        _validate_stage_payload(spec, {"entities": {"Q1": entity}})


def test_parsers_keep_authority_and_media_as_candidates_only(tmp_path: Path) -> None:
    entity_spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test",
        {},
        ("Q1",),
    )
    media_spec = RequestSpec(
        "commons-imageinfo-0001",
        "commons_imageinfo",
        2,
        "https://example.test",
        {},
        ("File:A.jpg",),
    )
    (tmp_path / "wikidata-entities-0001.json").write_text(
        json.dumps(
            {
                "entities": {
                    "Q1": {
                        "labels": {"en": {"value": "A landscape"}},
                        "descriptions": {},
                        "claims": {
                            "P170": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": {"id": "Q296"}},
                                    }
                                }
                            ],
                            "P18": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": "A.jpg"},
                                    }
                                }
                            ],
                            "P195": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": {"id": "Q999"}},
                                    }
                                }
                            ],
                            "P31": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": {"id": "Q3305213"}},
                                    }
                                }
                            ],
                            "P186": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": {"id": "Q296955"}},
                                    }
                                },
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": {"id": "Q12321255"}},
                                    }
                                },
                            ],
                            "P217": [
                                {
                                    "mainsnak": {
                                        "snaktype": "value",
                                        "datavalue": {"value": "INV-1"},
                                    }
                                }
                            ],
                        },
                    }
                }
            }
        )
    )
    (tmp_path / "commons-imageinfo-0001.json").write_text(
        json.dumps(
            {
                "query": {
                    "pages": [
                        {
                            "title": "File:A.jpg",
                            "imageinfo": [
                                {
                                    "url": "https://upload.wikimedia.org/a.jpg",
                                    "descriptionurl": "https://commons.wikimedia.org/wiki/File:A.jpg",
                                    "width": 2000,
                                    "height": 1500,
                                    "mime": "image/jpeg",
                                    "sha1": "a" * 31,
                                    "timestamp": "2026-01-01T00:00:00Z",
                                    "canonicaltitle": "File:A.jpg",
                                    "extmetadata": {
                                        "LicenseShortName": {"value": "Public domain"},
                                        "LicenseUrl": {
                                            "value": "https://creativecommons.org/publicdomain/mark/1.0/"
                                        },
                                        "Copyrighted": {"value": "False"},
                                        "Institution": {
                                            "value": "<a href='https://museum.example/object/1'>Museum</a>"
                                        },
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    response_paths = {
        "wikidata-entities-0001": tmp_path / "wikidata-entities-0001.json",
        "commons-imageinfo-0001": tmp_path / "commons-imageinfo-0001.json",
    }
    entities = parse_entity_batches([entity_spec, media_spec], response_paths)
    media = parse_media_batches([entity_spec, media_spec], response_paths, _config())
    rows = [
        {
            "painter_id": "claude_monet",
            "creator_qid": "Q296",
            "item_qid": "Q1",
            "commons_filename": "A.jpg",
        }
    ]
    manifest = build_candidate_manifest(rows, entities, media, _config())
    assert manifest[0]["discovery_gate"] == "federated_metadata_candidate"
    assert manifest[0]["authority_status"] == "authoritative_holding_record_not_yet_verified"
    assert manifest[0]["active_study_admission"] is False
    assert manifest[0]["media"]["metadata_urls"] == ["https://museum.example/object/1"]
    assert summarize_manifest(manifest)["active_study_admissions"] == 0


def test_candidate_gate_fails_closed_on_claim_rights_or_mime_drift() -> None:
    row = {
        "painter_id": "claude_monet",
        "creator_qid": "Q296",
        "item_qid": "Q1",
        "commons_filename": "A.jpg",
    }
    entity = {
        "entity_status": "resolved",
        "creator_qids": ["Q296"],
        "instance_qids": ["Q3305213"],
        "material_qids": ["Q296955", "Q12321255"],
        "commons_filenames": ["A.jpg"],
    }
    media = {
        "media_status": "resolved",
        "rights_candidate_status": "commons_open_rights_marker_candidate",
        "geometry_candidate_status": "reported_original_geometry_candidate",
        "decode_format_candidate_status": "supported_image_mime",
        "delivery_receipt_status": "complete_media_delivery_receipt_candidate",
    }
    assert (
        build_candidate_manifest([row], {"Q1": entity}, {"A.jpg": media}, _config())[0][
            "discovery_gate"
        ]
        == "federated_metadata_candidate"
    )

    failures = [
        ({**entity, "material_qids": ["Q296955"]}, media),
        ({**entity, "commons_filenames": ["B.jpg"]}, media),
        (entity, {**media, "rights_candidate_status": "rights_review"}),
        (entity, {**media, "decode_format_candidate_status": "unsupported_image_mime"}),
    ]
    for failed_entity, failed_media in failures:
        candidate = build_candidate_manifest(
            [row], {"Q1": failed_entity}, {"A.jpg": failed_media}, _config()
        )[0]
        assert candidate["discovery_gate"] == "failed_or_unresolved_discovery_gate"
        assert candidate["active_study_admission"] is False


def test_candidate_gate_requires_current_best_rank_p18_item_file_link() -> None:
    row = {
        "painter_id": "claude_monet",
        "creator_qid": "Q296",
        "item_qid": "Q1",
        "commons_filename": "Current.jpg",
    }
    entity = {
        "entity_status": "resolved",
        "creator_qids": ["Q296"],
        "instance_qids": ["Q3305213"],
        "material_qids": ["Q296955", "Q12321255"],
        "commons_filenames": ["Replacement.jpg"],
    }
    media = {
        "media_status": "resolved",
        "rights_candidate_status": "commons_open_rights_marker_candidate",
        "geometry_candidate_status": "reported_original_geometry_candidate",
        "decode_format_candidate_status": "supported_image_mime",
        "delivery_receipt_status": "complete_media_delivery_receipt_candidate",
    }
    candidate = build_candidate_manifest(
        [row], {"Q1": entity}, {"Current.jpg": media}, _config()
    )[0]
    assert candidate["discovery_gate"] == "failed_or_unresolved_discovery_gate"


def test_stage_validator_rejects_valid_json_without_exact_member_coverage() -> None:
    entity_spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    with pytest.raises(CensusError, match="exact entity members"):
        _validate_stage_payload(entity_spec, {"entities": {}})

    media_spec = RequestSpec(
        "commons-imageinfo-0001",
        "commons_imageinfo",
        1,
        "https://example.test/media",
        {},
        ("File:A.jpg",),
    )
    with pytest.raises(CensusError, match="explicitly cover"):
        _validate_stage_payload(media_spec, {"batchcomplete": True, "query": {"pages": []}})


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"entities": {"Q1": {}}}, "redirected or changed identity"),
        (
            {"entities": {"Q1": {"id": "Q1", "labels": {}, "descriptions": {}}}},
            "claim mapping",
        ),
    ],
)
def test_entity_stage_rejects_parser_incomplete_objects(payload: dict, message: str) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    with pytest.raises(CensusError, match=message):
        _validate_stage_payload(spec, payload)


@pytest.mark.parametrize(
    "snak",
    [
        {"datavalue": {"value": "https://example.test/source"}},
        {"snaktype": 7, "datavalue": {"value": "https://example.test/source"}},
        {"snaktype": "somevalue"},
        {"snaktype": "value", "datavalue": []},
        {"snaktype": "value", "datavalue": {}},
        {"snaktype": "value", "datavalue": {"value": 7}},
        {"snaktype": "value", "datavalue": {"value": "not-a-url"}},
        {"snaktype": "value", "datavalue": {"value": "https://[broken"}},
        {"snaktype": "value", "datavalue": {"value": "https://example.test/a\\b"}},
        {"snaktype": "value", "datavalue": {"value": "https://example.test/a|b"}},
        {"snaktype": "value", "datavalue": {"value": "https://example.test/<a>"}},
        {"snaktype": "value", "datavalue": {"value": "https://example.test/\"a\""}},
    ],
    ids=[
        "missing-snaktype",
        "malformed-snaktype",
        "non-value-snaktype",
        "non-object-datavalue",
        "missing-datavalue-value",
        "non-string-datavalue",
        "non-http-url",
        "malformed-url",
        "backslash",
        "vertical-bar",
        "angle-brackets",
        "quotes",
    ],
)
def test_p854_reference_snaks_fail_closed_before_extraction(snak: dict) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    entity = _entity_with_p854_reference(snak)
    with pytest.raises(CensusError, match="P854 reference snak"):
        _validate_stage_payload(spec, {"entities": {"Q1": entity}})
    with pytest.raises(CensusError, match="P854 reference snak"):
        _reference_urls(entity)


def test_valid_p854_reference_is_extractable_after_stage_validation() -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    url = "https://example.test/source?id=1"
    entity = _entity_with_p854_reference(
        {"snaktype": "value", "datavalue": {"value": url}}
    )
    assert _validate_stage_payload(spec, {"entities": {"Q1": entity}}) == (
        "complete_wikidata_entity_batch"
    )
    assert _reference_urls(entity) == [url]


@pytest.mark.parametrize(
    "page",
    [
        {"title": "File:A.jpg"},
        {"title": "File:A.jpg", "imageinfo": ["bad"]},
        {
            "title": "File:A.jpg",
            "imageinfo": [{"url": "https://upload.wikimedia.org/a.jpg"}],
        },
    ],
)
def test_commons_stage_rejects_title_only_or_malformed_imageinfo(page: dict) -> None:
    spec = RequestSpec(
        "commons-imageinfo-0001",
        "commons_imageinfo",
        1,
        "https://example.test/media",
        {},
        ("File:A.jpg",),
    )
    with pytest.raises(CensusError, match="image"):
        _validate_stage_payload(spec, {"batchcomplete": True, "query": {"pages": [page]}})


def test_commons_continuation_and_redirects_are_rejected() -> None:
    spec = RequestSpec(
        "commons-imageinfo-0001",
        "commons_imageinfo",
        1,
        "https://example.test/media",
        {},
        ("File:A.jpg",),
    )
    payload = _media_payload()
    payload.pop("batchcomplete")
    payload["continue"] = {"iistart": "2020-01-01T00:00:00Z", "continue": "||"}
    with pytest.raises(CensusError, match="not a complete one-response batch"):
        _validate_stage_payload(spec, payload)
    redirected = _media_payload()
    redirected["query"]["redirects"] = [{"from": "File:A.jpg", "to": "File:B.jpg"}]
    with pytest.raises(CensusError, match="redirect or title normalization"):
        _validate_stage_payload(spec, redirected)


@pytest.mark.parametrize(
    "metadata, override, expected_rights, expected_delivery",
    [
        (
            {
                "LicenseShortName": {"value": "Public domain"},
                "LicenseUrl": {"value": "https://creativecommons.org/publicdomain/mark/1.0/"},
                "Copyrighted": {"value": "True"},
            },
            {},
            "rights_review",
            "complete_media_delivery_receipt_candidate",
        ),
        (
            {"LicenseShortName": {"value": "Public domain"}},
            {},
            "rights_review",
            "complete_media_delivery_receipt_candidate",
        ),
        (
            {
                "LicenseShortName": {"value": "Public domain"},
                "LicenseUrl": {"value": "https://creativecommons.org/publicdomain/mark/1.0/"},
                "Copyrighted": {"value": "False"},
                "Permission": {"value": "Permission required"},
            },
            {},
            "rights_review",
            "complete_media_delivery_receipt_candidate",
        ),
        (
            {
                "LicenseShortName": {"value": "Public domain"},
                "LicenseUrl": {"value": "https://creativecommons.org/publicdomain/mark/1.0/"},
                "Copyrighted": {"value": "False"},
            },
            {"sha1": ""},
            "commons_open_rights_marker_candidate",
            "incomplete_media_delivery_receipt",
        ),
    ],
)
def test_rights_and_delivery_evidence_fail_closed(
    tmp_path: Path,
    metadata: dict,
    override: dict,
    expected_rights: str,
    expected_delivery: str,
) -> None:
    spec = RequestSpec(
        "commons-imageinfo-0001",
        "commons_imageinfo",
        1,
        "https://example.test/media",
        {},
        ("File:A.jpg",),
    )
    path = tmp_path / "media.json"
    path.write_text(json.dumps(_media_payload(metadata=metadata, info_overrides=override)))
    parsed = parse_media_batches([spec], {spec.request_id: path}, _config())["A.jpg"]
    assert parsed["rights_candidate_status"] == expected_rights
    assert parsed["delivery_receipt_status"] == expected_delivery


def test_execution_journals_start_before_access_and_reuses_verified_success(
    tmp_path: Path,
) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {"ids": "Q1"},
        ("Q1",),
    )
    config = _config()
    workspace = tmp_path / "workspace"
    events = _test_genesis(tmp_path / "events.jsonl")
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        events = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
        assert events[-1]["event_type"] == "attempt_started"
        assert events[-1]["encoded_request_url"] == str(request.url)
        calls.append(str(request.url))
        return httpx.Response(
            200,
            json={"entities": {"Q1": _valid_entity()}},
            request=request,
        )

    receipts, paths = _execute_specs(
        tmp_path,
        config,
        [spec],
        workspace,
        events,
        transport=httpx.MockTransport(handler),
    )
    assert len(calls) == 1
    assert receipts[0]["status"] == "verified_success_event"
    assert paths[spec.request_id].is_file()
    events = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
    assert [event["event_type"] for event in events] == [
        "execution_started",
        "attempt_started",
        "attempt_finished",
    ]

    def forbidden_handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"unexpected repeated network access: {request.url}")

    reused, reused_paths = _execute_specs(
        tmp_path,
        config,
        [spec],
        workspace,
        _load_event_ledger(tmp_path / "events.jsonl", "test-census"),
        transport=httpx.MockTransport(forbidden_handler),
    )
    assert reused[0]["status"] == "verified_success_event"
    assert reused_paths == paths

    paths[spec.request_id].write_bytes(b"corrupt")
    with pytest.raises(CensusError, match="missing or corrupt"):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            workspace,
            _load_event_ledger(tmp_path / "events.jsonl", "test-census"),
            transport=httpx.MockTransport(forbidden_handler),
        )


def test_retry_is_lifetime_bounded_and_terminal_http_is_not_retried(tmp_path: Path) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    config = _config()
    config["request_contract"]["maximum_attempts"] = 1
    events = _test_genesis(tmp_path / "events.jsonl")
    calls = 0

    def forbidden_response(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(403, json={"error": "forbidden"}, request=request)

    with pytest.raises(CensusError, match="non-retryable terminal_http_error"):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(forbidden_response),
        )
    assert calls == 1
    with pytest.raises(CensusError, match="non-retryable terminal outcome"):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace",
            _load_event_ledger(tmp_path / "events.jsonl", "test-census"),
            transport=httpx.MockTransport(forbidden_response),
        )
    assert calls == 1


def test_retry_after_supports_http_date_and_long_wait_requires_new_census(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 9, 2, 5, 0, 0, tzinfo=timezone.utc)
    assert _retry_after_seconds("Wed, 02 Sep 2026 05:01:00 GMT", now) == 60.0
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    config = _config()
    events = _test_genesis(tmp_path / "events.jsonl")
    calls = 0

    def throttled(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, headers={"Retry-After": "120"}, request=request)

    with pytest.raises(CensusError, match="new_census_required"):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(throttled),
        )
    assert calls == 1
    terminal = _load_event_ledger(tmp_path / "events.jsonl", "test-census")[-1]
    assert terminal["outcome"] == "terminal_retry_after_new_census_required"
    assert terminal["retryable"] is False


def test_http_date_retry_receipt_cannot_be_shortened_after_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class SimulatedCrash(RuntimeError):
        pass

    frozen_now = datetime(2026, 9, 2, 5, 0, 0, tzinfo=timezone.utc)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            if tz is None:
                return frozen_now.replace(tzinfo=None)
            return frozen_now.astimezone(tz)

    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    events = _test_genesis(tmp_path / "events.jsonl")
    config = _config()
    config["request_contract"]["maximum_retry_wait_seconds"] = 120.0

    def throttled(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"Retry-After": "Wed, 02 Sep 2026 05:01:00 GMT"},
            request=request,
        )

    monkeypatch.setattr(federated_census, "datetime", FrozenDateTime)
    monkeypatch.setattr(
        federated_census.time,
        "sleep",
        lambda _seconds: (_ for _ in ()).throw(SimulatedCrash()),
    )
    with pytest.raises(SimulatedCrash):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(throttled),
        )

    persisted = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
    persisted[-1]["retry_after_seconds"] = 1.0
    with pytest.raises(CensusError, match="header and receipt disagree"):
        _attempt_maps(
            persisted,
            {spec.request_id: spec},
            tmp_path / "workspace",
        )


def test_event_timestamps_must_be_monotonic(tmp_path: Path) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {"ids": "Q1"},
        ("Q1",),
    )
    events = _test_genesis(tmp_path / "events.jsonl")

    def succeeds(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"entities": {"Q1": _valid_entity()}},
            request=request,
        )

    _execute_specs(
        tmp_path,
        _config(),
        [spec],
        tmp_path / "workspace",
        events,
        transport=httpx.MockTransport(succeeds),
    )
    persisted = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
    persisted[-1]["finished_at_utc"] = "2026-09-01T23:59:59Z"
    with pytest.raises(CensusError, match="timestamp precedes"):
        _attempt_maps(
            persisted,
            {spec.request_id: spec},
            tmp_path / "workspace",
        )


@pytest.mark.parametrize(
    "retry_after, backoff, expected_delay",
    [("10", 0.0, 10.0), ("1", 8.0, 8.0)],
    ids=["retry-after-dominates", "backoff-dominates"],
)
def test_resume_honors_persisted_retry_delay_after_crash_before_sleep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    retry_after: str,
    backoff: float,
    expected_delay: float,
) -> None:
    class SimulatedCrash(RuntimeError):
        pass

    frozen_now = datetime(2026, 9, 2, 5, 0, 0, tzinfo=timezone.utc)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            if tz is None:
                return frozen_now.replace(tzinfo=None)
            return frozen_now.astimezone(tz)

    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    config = _config()
    config["request_contract"]["retry_backoff_base_seconds"] = backoff
    workspace = tmp_path / "workspace"
    events = _test_genesis(tmp_path / "events.jsonl")

    def throttled(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": retry_after}, request=request)

    def crash_before_sleep(seconds: float) -> None:
        assert seconds == expected_delay
        raise SimulatedCrash

    monkeypatch.setattr(federated_census, "datetime", FrozenDateTime)
    monkeypatch.setattr(federated_census.time, "sleep", crash_before_sleep)
    with pytest.raises(SimulatedCrash):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            workspace,
            events,
            transport=httpx.MockTransport(throttled),
        )

    persisted = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
    assert persisted[-1]["event_type"] == "attempt_finished"
    assert persisted[-1]["retryable"] is True
    assert persisted[-1]["retry_after_seconds"] == float(retry_after)
    resumed_sleeps: list[float] = []

    def record_sleep(seconds: float) -> None:
        resumed_sleeps.append(seconds)

    def succeeds_after_wait(request: httpx.Request) -> httpx.Response:
        assert resumed_sleeps
        return httpx.Response(
            200,
            json={"entities": {"Q1": _valid_entity()}},
            request=request,
        )

    monkeypatch.setattr(federated_census.time, "sleep", record_sleep)
    receipts, _ = _execute_specs(
        tmp_path,
        config,
        [spec],
        workspace,
        persisted,
        transport=httpx.MockTransport(succeeds_after_wait),
    )
    assert receipts[0]["attempt"] == 2
    assert resumed_sleeps == [expected_delay]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -1.0, True])
def test_resume_rejects_nonfinite_or_invalid_retry_receipt(value: object) -> None:
    terminal = {
        "attempt": 1,
        "finished_at_utc": "2026-09-02T05:00:00Z",
        "retry_after_seconds": value,
    }
    with pytest.raises(CensusError, match="invalid Retry-After receipt"):
        federated_census._remaining_retry_delay_seconds(
            terminal,
            retry_backoff_base=8.0,
            minimum_interval=4.0,
            maximum_wait=30.0,
            now=datetime(2026, 9, 2, 5, 0, 0, tzinfo=timezone.utc),
        )


@pytest.mark.parametrize("value", ["", "-1", "1.5", "nan", "not-a-date"])
def test_retry_after_rejects_malformed_values(value: str) -> None:
    with pytest.raises(CensusError, match="invalid Retry-After"):
        _retry_after_seconds(value)


def test_http_redirect_is_terminal_and_is_not_followed(tmp_path: Path) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    calls: list[str] = []

    def redirect(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(
            302,
            headers={"Location": "https://evil.example/collector"},
            request=request,
        )

    with pytest.raises(CensusError, match="non-retryable terminal_http_error"):
        _execute_specs(
            tmp_path,
            _config(),
            [spec],
            tmp_path / "workspace",
            _test_genesis(tmp_path / "events.jsonl"),
            transport=httpx.MockTransport(redirect),
        )
    assert calls == ["https://example.test/entities"]


def test_intent_parser_and_event_append_fail_closed_on_torn_jsonl(tmp_path: Path) -> None:
    intent_path = tmp_path / "intents.jsonl"
    intent_path.write_text('{"schema_version":"wrong"}\n')
    with pytest.raises(CensusError, match="unexpected schema"):
        _specs_from_intents(intent_path, "test-census")

    event_path = tmp_path / "events.jsonl"
    event_path.write_bytes(b'{"partial":')
    before = event_path.read_bytes()
    with pytest.raises(CensusError, match="torn JSONL"):
        _append_event(event_path, "test-census", [], {"event_type": "execution_started"})
    assert event_path.read_bytes() == before


def test_event_resume_rejects_intent_url_drift_and_path_escape(tmp_path: Path) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {"ids": "Q1"},
        ("Q1",),
    )
    events = _test_genesis(tmp_path / "events.jsonl")
    _append_event(
        tmp_path / "events.jsonl",
        "test-census",
        events,
        {
            "event_type": "attempt_started",
            "request_id": spec.request_id,
            "stage": spec.stage,
            "attempt": 1,
            "started_at_utc": "2026-09-02T00:00:00Z",
            "method": "GET",
            "encoded_request_url": "https://example.test/entities?ids=Q999",
            "intent_sequence": 1,
        },
    )
    with pytest.raises(CensusError, match="differs from frozen intent"):
        _attempt_maps(events, {spec.request_id: spec}, tmp_path / "workspace")
    with pytest.raises(CensusError, match="escapes the repository"):
        _repo_path(tmp_path, "../escape", "test.path")
    with pytest.raises(CensusError, match="escapes the repository"):
        _repo_path(tmp_path, str(tmp_path / "absolute"), "test.path")


def test_execution_genesis_binds_authorization_and_clean_outputs(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    protocol_path = tmp_path / "protocol.md"
    intent_path = tmp_path / "intents.jsonl"
    seal_path = tmp_path / "seal.json"
    for path, contents in (
        (config_path, "{}"),
        (protocol_path, "protocol"),
        (intent_path, "{}\n"),
        (seal_path, "{}"),
    ):
        path.write_text(contents)
    config = _config()
    config["protocol_path"] = "protocol.md"
    preexecution = [
        {"path": "events.jsonl", "state": "absent"},
        {"path": "candidates.jsonl", "state": "absent"},
        {"path": "receipt.json", "state": "absent"},
        {"path": "workspace/response_bodies", "state": "absent"},
    ]
    authorization = {
        "seal": {
            "freeze_path": "freeze.json",
            "freeze_sha256": "a" * 64,
            "review_path": "review.json",
            "review_sha256": "b" * 64,
        },
        "freeze": {
            "frozen_input_set_sha256": "c" * 64,
            "preexecution_outputs": preexecution,
        },
        "review": {"decision": "APPROVE_METADATA_CENSUS_ONLY"},
    }
    event_path = tmp_path / "events.jsonl"
    events = _ensure_execution_genesis(
        tmp_path,
        config,
        config_path,
        seal_path,
        "d" * 64,
        authorization,
        event_path,
    )
    assert events[0]["authorization_seal_sha256"] == "d" * 64
    with pytest.raises(CensusError, match="differs from the current frozen authorization"):
        _ensure_execution_genesis(
            tmp_path,
            config,
            config_path,
            seal_path,
            "e" * 64,
            authorization,
            event_path,
        )


def test_dangling_start_terminates_the_census_without_network_replay(tmp_path: Path) -> None:
    spec = RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://example.test/entities",
        {},
        ("Q1",),
    )
    config = _config()
    config["request_contract"]["maximum_attempts"] = 1
    events = _test_genesis(tmp_path / "events.jsonl")
    _append_event(
        tmp_path / "events.jsonl",
        "test-census",
        events,
        {
            "event_type": "attempt_started",
            "request_id": spec.request_id,
            "stage": spec.stage,
            "attempt": 1,
            "started_at_utc": "2026-09-02T00:00:00Z",
            "method": "GET",
            "encoded_request_url": spec.endpoint,
            "intent_sequence": 1,
        },
    )
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={}, request=request)

    with pytest.raises(CensusError, match="non-retryable terminal outcome"):
        _execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    recovered = _load_event_ledger(tmp_path / "events.jsonl", "test-census")
    assert recovered[-1]["outcome"] == "terminal_interrupted_new_census_required"
    assert recovered[-1]["retryable"] is False


def test_authorization_rejects_an_empty_frozen_input_set(tmp_path: Path) -> None:
    scope = {
        "metadata_requests": True,
        "image_downloads": False,
        "visual_coding": False,
        "active_study_admission": False,
        "feature_extraction": False,
        "generation": False,
    }
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(
        json.dumps(
            {
                "schema_version": "painter-feature-generation-v1-metadata-census-freeze/1.0",
                "status": "sealed_for_independent_metadata_census_review",
                "census_id": "test-census",
                "protocol_id": "test-protocol",
                "scope": scope,
                "frozen_inputs": [],
                "frozen_input_set_sha256": "0" * 64,
            }
        )
    )
    review_path = tmp_path / "review.json"
    review_path.write_text("{}")
    seal_path = tmp_path / "seal.json"
    seal_path.write_text(
        json.dumps(
            {
                "schema_version": (
                    "painter-feature-generation-v1-metadata-census-authorization/1.0"
                ),
                "status": "authorized_for_metadata_census_execution",
                "census_id": "test-census",
                "protocol_id": "test-protocol",
                "authorization_scope": scope,
                "freeze_path": "freeze.json",
                "freeze_sha256": hash_file(freeze_path),
                "review_path": "review.json",
                "review_sha256": hash_file(review_path),
            }
        )
    )
    config = {
        "census_id": "test-census",
        "protocol_id": "test-protocol",
        "protocol_path": "protocol.md",
        "discovery_input": {"path": "input.json"},
        "source_frame_contract": {"upstream_evidence_path": "evidence.json"},
        "paths": {"planned_requests": "intents.jsonl"},
    }
    with pytest.raises(CensusError, match="no frozen inputs"):
        _validate_seal(
            tmp_path,
            config,
            tmp_path / "config.json",
            seal_path,
            hash_file(seal_path),
        )
