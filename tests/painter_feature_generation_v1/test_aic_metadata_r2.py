from __future__ import annotations

import copy
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import aic_metadata_r2 as aic


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n")


def _config(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    source = Path("configs/painter_feature_generation_v1/aic_metadata_census.json")
    config = json.loads(source.read_text())
    config["protocol_path"] = "protocol.md"
    config["source_contract"]["execution_start_not_after_utc"] = "2099-01-01T00:00:00Z"
    config["source_contract"]["minimum_interval_seconds"] = 0.5
    config["paths"] = {
        "request_intents": "data/intents.jsonl",
        "request_events": "data/events.jsonl",
        "publication_directory": "data/publication",
        "candidate_manifest": "data/publication/candidates.jsonl",
        "execution_receipt": "data/publication/execution_receipt.json",
        "workspace": "workspace/aic",
    }
    (tmp_path / "protocol.md").write_text("Protocol ID: `painter-feature-generation-v1/2.0`\n")
    config_path = tmp_path / "config.json"
    _write_json(config_path, config)
    return config_path, config


def _authorized_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, str, dict[str, object]]:
    config_path, config = _config(tmp_path)
    aic.prepare(tmp_path, config_path)
    required = sorted(["config.json", "data/intents.jsonl", "protocol.md"])
    monkeypatch.setattr(aic, "required_frozen_paths", lambda *_: required)
    entries = [{"path": path, "sha256": hash_file(tmp_path / path)} for path in required]
    freeze = {
        "schema_version": "painter-feature-generation-v1-aic-metadata-freeze/1.0",
        "status": "sealed_for_neutral_quality_review",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "scope": config["scope"],
        "frozen_input_set_sha256": aic._sha256(canonical_json(entries).encode()),
        "frozen_inputs": entries,
        "preexecution_outputs": aic.expected_outputs(config),
    }
    freeze_path = tmp_path / "freeze.json"
    _write_json(freeze_path, freeze)
    review = {
        "schema_version": "painter-feature-generation-v1-aic-metadata-review/1.0",
        "decision": "APPROVE_AIC_METADATA_ONLY",
        "blocking_findings": [],
        "independent_reviewer": "neutral test reviewer",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "approved_scope": config["scope"],
        "reviewed_freeze_path": "freeze.json",
        "reviewed_freeze_sha256": hash_file(freeze_path),
    }
    review_path = tmp_path / "review.json"
    _write_json(review_path, review)
    authorization = {
        "schema_version": "painter-feature-generation-v1-aic-metadata-authorization/1.0",
        "status": "authorized_for_aic_metadata_execution",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "authorization_scope": config["scope"],
        "freeze_path": "freeze.json",
        "freeze_sha256": hash_file(freeze_path),
        "review_path": "review.json",
        "review_sha256": hash_file(review_path),
    }
    seal_path = tmp_path / "authorization.json"
    _write_json(seal_path, authorization)
    return config_path, seal_path, hash_file(seal_path), config


def _item(artist_id: int, artist_name: str, artwork_id: int) -> dict[str, object]:
    item = {field: None for field in aic._FIELDS}
    item.update(
        {
            "id": artwork_id,
            "title": f"Artwork {artwork_id}",
            "api_link": f"https://api.artic.edu/api/v1/artworks/{artwork_id}",
            "artist_id": artist_id,
            "artist_title": artist_name,
            "alt_artist_ids": [],
            "artist_ids": [artist_id],
            "artist_titles": [artist_name],
            "artist_display": artist_name,
            "artwork_type_title": "Painting",
            "classification_title": "painting",
            "medium_display": "Oil on canvas",
            "main_reference_number": f"A.{artwork_id}",
            "is_public_domain": True,
            "image_id": f"image-{artwork_id}",
            "thumbnail": {"width": 2400, "height": 1800, "alt_text": "outdoor view"},
            "subject_titles": ["landscape"],
            "style_titles": ["Impressionism"],
            "timestamp": "2098-01-01T00:00:00-06:00",
        }
    )
    return item


def _payload(item: dict[str, object], *, total: int = 1) -> dict[str, object]:
    return {
        "pagination": {
            "total": total,
            "limit": 100,
            "offset": 0,
            "total_pages": 1,
            "current_page": 1,
        },
        "data": [item],
        "info": {"version": "1.15", "license_text": "CC0 except description"},
        "config": {"iiif_url": "https://www.artic.edu/iiif/2"},
    }


def _transport(
    *, bad_total: bool = False, shared_artwork_id: bool = False
) -> tuple[httpx.MockTransport, list[str]]:
    calls: list[str] = []
    names = {agent_id: name for _, name, agent_id in aic._PAINTERS}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        query = parse_qs(urlsplit(str(request.url)).query)
        agent_id = int(query["query[term][artist_ids]"][0])
        artwork_id = 999999 if shared_artwork_id else 100000 + agent_id
        payload = _payload(
            _item(agent_id, names[agent_id], artwork_id), total=2 if bad_total else 1
        )
        return httpx.Response(
            200,
            request=request,
            headers={
                "Date": "Wed, 02 Sep 2098 12:00:00 GMT",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
        )

    return httpx.MockTransport(handler), calls


def test_build_intents_is_exact_and_deterministic(tmp_path: Path) -> None:
    config_path, config = _config(tmp_path)
    loaded = aic.load_config(tmp_path, config_path)
    first = aic.build_intents(loaded)
    assert first == aic.build_intents(loaded)
    assert len(first) == 4
    assert [row["aic_agent_id"] for row in first] == [35809, 36707, 36211, 40482]
    assert all(row["params"]["page"] == "1" for row in first)
    assert all(row["params"]["limit"] == "100" for row in first)
    assert config["scope"] == aic._SCOPE


def test_parse_result_retains_all_fields_and_separates_gates() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "paul_cezanne",
        "artist_name": "Paul Cezanne",
        "aic_agent_id": 40482,
    }
    item = _item(40482, "Paul Cézanne", 7)
    rows = aic.parse_result(_payload(item), intent, "a" * 64)
    assert rows[0]["aic_record"]["id"] == 7
    assert rows[0]["field_presence"] == sorted(aic._FIELDS)
    assert rows[0]["screening"]["target_in_paired_artist_ids_and_titles"] is True
    assert rows[0]["screening"]["authority_record_candidate"] is True
    assert rows[0]["screening"]["metadata_and_media_candidate"] is True
    assert rows[0]["active_study_admission"] is False


def test_aic_string_classification_identifier_is_retained() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "claude_monet",
        "artist_name": "Claude Monet",
        "aic_agent_id": 35809,
    }
    item = _item(35809, "Claude Monet", 71)
    item["classification_id"] = "TM-66"
    row = aic.parse_result(_payload(item), intent, "f" * 64)[0]
    assert row["aic_record"]["classification_id"] == "TM-66"


def test_parse_result_keeps_failed_screening_row() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "claude_monet",
        "artist_name": "Claude Monet",
        "aic_agent_id": 35809,
    }
    item = _item(35809, "Claude Monet", 8)
    item["medium_display"] = "Etching on paper"
    item["is_public_domain"] = False
    rows = aic.parse_result(_payload(item), intent, "b" * 64)
    assert len(rows) == 1
    assert rows[0]["screening"]["authority_record_candidate"] is False
    assert rows[0]["screening"]["metadata_and_media_candidate"] is False


def test_screening_uses_whole_words_not_substrings() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "claude_monet",
        "artist_name": "Claude Monet",
        "aic_agent_id": 35809,
    }
    item = _item(35809, "Claude Monet", 81)
    item["artwork_type_title"] = "Overpainting equipment"
    item["classification_title"] = None
    item["medium_display"] = "Spoiled varnish on canvasboard"
    row = aic.parse_result(_payload(item), intent, "d" * 64)[0]
    assert row["screening"]["painting_classification"] is False
    assert row["screening"]["oil_and_canvas_tokens"] is False
    assert row["screening"]["authority_record_candidate"] is False


def test_inline_lqip_is_not_published() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "claude_monet",
        "artist_name": "Claude Monet",
        "aic_agent_id": 35809,
    }
    item = _item(35809, "Claude Monet", 82)
    item["thumbnail"]["lqip"] = "data:image/gif;base64,preview"
    row = aic.parse_result(_payload(item), intent, "e" * 64)[0]
    thumbnail = row["aic_record"]["thumbnail"]
    assert "lqip" not in thumbnail
    assert thumbnail["provider_inline_lqip_present_but_not_published"] is True


def test_nonpreferred_but_explicitly_associated_artist_is_retained() -> None:
    intent = {
        "census_id": "census",
        "request_id": "request",
        "painter_id": "claude_monet",
        "artist_name": "Claude Monet",
        "aic_agent_id": 35809,
    }
    item = _item(35809, "Claude Monet", 9)
    item["artist_id"] = 123
    item["artist_title"] = "Another Artist"
    item["alt_artist_ids"] = [35809]
    item["artist_ids"] = [123, 35809]
    item["artist_titles"] = ["Another Artist", "Claude Monet"]
    rows = aic.parse_result(_payload(item), intent, "c" * 64)
    assert rows[0]["screening"]["target_in_paired_artist_ids_and_titles"] is True
    assert rows[0]["screening"]["preferred_artist_matches_target"] is False
    assert rows[0]["screening"]["authority_record_candidate"] is True


def test_execute_publishes_only_after_four_complete_responses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    transport, calls = _transport()
    receipt = aic.execute(tmp_path, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 4
    assert receipt["successful_requests"] == 4
    assert receipt["request_event_count"] == 9
    assert receipt["counts"]["returned_rows"] == 4
    assert receipt["counts"]["metadata_and_media_candidates"] == 4
    assert receipt["counts"]["image_downloads"] == 0
    assert receipt["counts"]["active_study_admissions"] == 0
    assert (tmp_path / "data/publication/candidates.jsonl").is_file()
    assert (tmp_path / "data/publication/execution_receipt.json").is_file()
    assert len(list((tmp_path / "workspace/aic/response_bodies").rglob("*.response"))) == 4
    event = json.loads((tmp_path / "data/events.jsonl").read_text().splitlines()[0])
    assert event["schema_version"] == "painter-feature-generation-v1-aic-metadata-event/1.0"


def test_pagination_mismatch_is_terminal_without_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    transport, calls = _transport(bad_total=True)
    with pytest.raises(aic.AICMetadataError, match="terminal_delivery_or_schema_failure"):
        aic.execute(tmp_path, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 1
    assert not (tmp_path / "data/publication").exists()
    event_lines = (tmp_path / "data/events.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in event_lines]
    assert events[-1]["outcome"] == "terminal_delivery_or_schema_failure"


def test_cross_painter_duplicate_is_terminal_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    transport, calls = _transport(shared_artwork_id=True)
    with pytest.raises(aic.AICMetadataError, match="terminal_delivery_or_schema_failure"):
        aic.execute(tmp_path, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 2
    assert not (tmp_path / "data/publication").exists()


def test_frozen_config_drift_blocks_before_network(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, config = _authorized_tree(tmp_path, monkeypatch)
    changed = copy.deepcopy(config)
    changed["source_contract"]["timeout_seconds"] = 61.0
    _write_json(config_path, changed)
    transport, calls = _transport()
    with pytest.raises(aic.AICMetadataError, match="frozen input hash mismatch"):
        aic.execute(tmp_path, config_path, seal_path, seal_sha, transport)
    assert calls == []
    assert not (tmp_path / "workspace").exists()


def test_outside_root_authorization_cannot_burn_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    config_path, seal_path, seal_sha, _ = _authorized_tree(root, monkeypatch)
    outside = tmp_path / "authorization-copy.json"
    outside.write_bytes(seal_path.read_bytes())
    transport, calls = _transport()
    with pytest.raises(aic.AICMetadataError, match="outside the repository"):
        aic.execute(root, config_path, outside, seal_sha, transport)
    assert calls == []
    assert not (root / "workspace").exists()


def test_cas_drift_is_terminal_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    names = {agent_id: name for _, name, agent_id in aic._PAINTERS}
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 2:
            prior = next((tmp_path / "workspace/aic/response_bodies").rglob("*.response"))
            prior.write_bytes(b"mutated")
        query = parse_qs(urlsplit(str(request.url)).query)
        agent_id = int(query["query[term][artist_ids]"][0])
        return httpx.Response(
            200,
            request=request,
            headers={
                "Date": "Wed, 02 Sep 2098 12:00:00 GMT",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=_payload(_item(agent_id, names[agent_id], 100000 + agent_id)),
        )

    with pytest.raises(aic.AICMetadataError, match="content-addressed response hash mismatch"):
        aic.execute(
            tmp_path,
            config_path,
            seal_path,
            seal_sha,
            httpx.MockTransport(handler),
        )
    assert calls == 4
    assert not (tmp_path / "data/publication").exists()
    event_lines = (tmp_path / "data/events.jsonl").read_text().splitlines()
    assert json.loads(event_lines[-1])["outcome"] == "terminal_cas_verification_failure"


def test_unknown_transport_exception_is_terminal_without_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise RuntimeError("unexpected transport failure")

    with pytest.raises(aic.AICMetadataError, match="request failed terminally"):
        aic.execute(
            tmp_path, config_path, seal_path, seal_sha, httpx.MockTransport(handler)
        )
    event_lines = (tmp_path / "data/events.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in event_lines]
    assert calls == 1
    assert events[-1]["outcome"] == "terminal_transport_failure"
    assert not (tmp_path / "data/publication").exists()


def test_seal_symlink_retarget_after_validation_does_not_burn_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    link = tmp_path / "authorization-link.json"
    link.symlink_to(seal_path.name)
    replacement = tmp_path / "replacement.json"
    replacement.write_text("{}\n")
    original_claim = aic._claim_lock

    def retarget_then_claim(workspace: Path, census_id: str, seal_digest: str) -> Path:
        link.unlink()
        link.symlink_to(replacement.name)
        return original_claim(workspace, census_id, seal_digest)

    monkeypatch.setattr(aic, "_claim_lock", retarget_then_claim)
    transport, calls = _transport()
    receipt = aic.execute(tmp_path, config_path, link, seal_sha, transport)
    assert len(calls) == 4
    assert receipt["successful_requests"] == 4


def test_r2_config_delta_is_exactly_enforced() -> None:
    root = Path(__file__).resolve().parents[2]
    predecessor = json.loads(
        (root / "configs/painter_feature_generation_v1/aic_metadata_census.json").read_text()
    )
    current = json.loads(
        (root / "configs/painter_feature_generation_v1/aic_metadata_census_r2.json").read_text()
    )
    aic._validate_r2_config_delta(current, predecessor)
    changed = copy.deepcopy(current)
    changed["source_contract"]["timeout_seconds"] = 61.0
    with pytest.raises(aic.AICMetadataError, match="exceeds the exact allowed delta"):
        aic._validate_r2_config_delta(changed, predecessor)


def test_r1_terminal_absences_and_exact_workspace_inventory_are_enforced(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    current = json.loads(
        (root / "configs/painter_feature_generation_v1/aic_metadata_census_r2.json").read_text()
    )
    state = current["retry_contract"]["predecessor_terminal_state"]
    workspace = tmp_path / state["workspace"]
    for relative in state["exact_files"]:
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"evidence")
    aic._validate_predecessor_terminal_state(tmp_path, state)
    extra = workspace / "response_bodies/extra.response"
    extra.write_bytes(b"injected")
    with pytest.raises(aic.AICMetadataError, match="CAS inventory"):
        aic._validate_predecessor_terminal_state(tmp_path, state)
    extra.unlink()
    publication = tmp_path / state["absent_paths"][0]
    publication.parent.mkdir(parents=True, exist_ok=True)
    publication.write_bytes(b"injected")
    with pytest.raises(aic.AICMetadataError, match="publication absence"):
        aic._validate_predecessor_terminal_state(tmp_path, state)


def test_oversize_response_retains_only_bounded_prefix_and_terminates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, seal_path, seal_sha, config = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)
    maximum = int(config["source_contract"]["maximum_response_bytes"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={
                "Date": "Wed, 02 Sep 2098 12:00:00 GMT",
                "Content-Type": "application/json; charset=utf-8",
            },
            content=b"x" * (maximum + 100),
        )

    with pytest.raises(aic.AICMetadataError, match="terminal_delivery_or_schema_failure"):
        aic.execute(
            tmp_path, config_path, seal_path, seal_sha, httpx.MockTransport(handler)
        )
    bodies = list((tmp_path / "workspace/aic/response_bodies").rglob("*.response"))
    assert len(bodies) == 1
    assert bodies[0].stat().st_size == maximum + 1
    event = json.loads((tmp_path / "data/events.jsonl").read_text().splitlines()[-1])
    assert event["response_body_complete"] is False
    assert not (tmp_path / "data/publication").exists()


@pytest.mark.parametrize(
    ("date_header", "body"),
    [
        ("Sun, 06 Nov 9999 08:49:37 +99999999999999999999999", b"{}"),
        ("Wed, 02 Sep 2098 12:00:00 GMT", b'{"number":' + b"9" * 5000 + b"}"),
    ],
)
def test_malformed_provider_bytes_always_finish_the_request_terminally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    date_header: str,
    body: bytes,
) -> None:
    config_path, seal_path, seal_sha, _ = _authorized_tree(tmp_path, monkeypatch)
    monkeypatch.setattr(aic.time, "sleep", lambda _: None)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={"Date": date_header, "Content-Type": "application/json"},
            content=body,
        )

    with pytest.raises(aic.AICMetadataError, match="terminal_delivery_or_schema_failure"):
        aic.execute(
            tmp_path, config_path, seal_path, seal_sha, httpx.MockTransport(handler)
        )
    events = [
        json.loads(line)
        for line in (tmp_path / "data/events.jsonl").read_text().splitlines()
    ]
    assert [event["event_type"] for event in events] == [
        "execution_started",
        "request_started",
        "request_finished",
    ]
    assert events[-1]["outcome"] == "terminal_delivery_or_schema_failure"
    assert not (tmp_path / "data/publication").exists()
