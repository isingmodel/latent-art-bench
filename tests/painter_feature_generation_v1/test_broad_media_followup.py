import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import broad_media_followup as followup
from latent_art_bench.painter_feature_generation_v1.broad_media_followup import (
    BroadMediaFollowupError,
)


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n")


def _tree(tmp_path: Path) -> Path:
    protocol = tmp_path / "studies/painter_feature_generation_v1/PROTOCOL.md"
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Protocol ID: `painter-feature-generation-v1/2.0`\n")
    painters = [
        ("Q296", "claude_monet"),
        ("Q175130", "alfred_sisley"),
        ("Q134741", "camille_pissarro"),
        ("Q35548", "paul_cezanne"),
    ]
    rows = []
    for index in range(3722):
        creator, painter = painters[index % 4]
        rows.append(
            {
                "schema_version": "painter-feature-generation-v1-broad-wikidata-candidate/1.0",
                "census_id": "upstream",
                "candidate_sequence": index + 1,
                "painter_id": painter,
                "creator_qid": creator,
                "item_qid": f"Q{1000 + index % 3543}",
                "commons_filename": (
                    "Bridge.jpg"
                    if index % 3718 == 0
                    else "bridge.jpg"
                    if index % 3718 == 1
                    else f"File {index % 3718}.jpg"
                ),
                "source_request_id": f"request-{index % 4}",
                "discovery_status": "broad_no_p186_candidate_not_authority_verified",
                "active_study_admission": False,
            }
        )
    candidate = tmp_path / "data/upstream.jsonl"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("".join(canonical_json(row) + "\n" for row in rows))
    candidate_sha = hash_file(candidate)
    receipt = tmp_path / "data/upstream-receipt.json"
    _write_json(
        receipt,
        {
            "status": "broad_wikidata_no_p186_metadata_census_complete",
            "census_id": "upstream",
            "candidate_manifest_sha256": candidate_sha,
            "counts": {
                "item_image_rows": 3722,
                "distinct_items": 3543,
                "distinct_files": 3718,
            },
        },
    )
    config = {
        "schema_version": "painter-feature-generation-v1-broad-media-followup-config/1.0",
        "census_id": "test-followup",
        "protocol_id": "painter-feature-generation-v1/2.0",
        "protocol_path": "studies/painter_feature_generation_v1/PROTOCOL.md",
        "source_frame_contract": {
            "frame_class": (
                "complete_followup_of_broad_no_p186_wikidata_discovery_not_authority_census"
            ),
            "upstream_candidate_path": "data/upstream.jsonl",
            "upstream_candidate_sha256": candidate_sha,
            "upstream_receipt_path": "data/upstream-receipt.json",
            "upstream_receipt_sha256": hash_file(receipt),
            "expected_rows": 3722,
            "expected_distinct_items": 3543,
            "expected_distinct_files": 3718,
        },
        "painters": dict(painters),
        "request_contract": {
            "user_agent": "test",
            "execution_start_not_after_utc": "2099-01-01T00:00:00Z",
            "timeout_seconds": 1.0,
            "minimum_interval_seconds": 0.0,
            "retry_backoff_base_seconds": 0.0,
            "maximum_retry_wait_seconds": 1.0,
            "maximum_attempts": 5,
            "batch_size": 40,
            "wikidata_endpoint": "https://www.wikidata.org/w/api.php",
            "commons_endpoint": "https://commons.wikimedia.org/w/api.php",
            "wikidata_properties": "info|claims|labels|descriptions",
            "commons_imageinfo_properties": (
                "url|size|mime|sha1|timestamp|canonicaltitle|extmetadata"
            ),
            "commons_extmetadata_fields": "LicenseShortName",
            "retryable_http_status_codes": [429, 500, 502, 503, 504],
            "retryable_api_error_codes": [
                "internal_api_error",
                "maxlag",
                "ratelimited",
                "readonly",
            ],
        },
        "screening_contract": {
            "minimum_short_side_pixels": 1024,
            "allowed_commons_license_url_prefixes": [],
            "allowed_unlinked_license_short_names": [],
            "nonfree_markers": [],
            "supported_image_mime_types": ["image/jpeg"],
        },
        "paths": {
            "planned_requests": "data/intents.jsonl",
            "request_events": "data/events.jsonl",
            "candidate_manifest": "data/publication/candidates.jsonl",
            "execution_receipt": "data/publication/execution_receipt.json",
            "workspace": "workspace/followup",
        },
    }
    config_path = tmp_path / "configs/painter_feature_generation_v1/broad_media_followup.json"
    _write_json(config_path, config)
    return config_path


def test_prepare_closes_exact_broad_followup_request_frame(tmp_path: Path) -> None:
    config_path = _tree(tmp_path)
    result = followup.prepare(tmp_path, config_path)
    rows = [json.loads(line) for line in (tmp_path / "data/intents.jsonl").read_text().splitlines()]
    assert result == {
        "census_id": "test-followup",
        "rows": 3722,
        "planned_requests": 182,
        "wikidata_requests": 89,
        "commons_requests": 93,
        "intent_path": "data/intents.jsonl",
        "intent_sha256": hash_file(tmp_path / "data/intents.jsonl"),
    }
    assert [row["sequence"] for row in rows] == list(range(1, 183))
    assert len({member for row in rows[:89] for member in row["members"]}) == 3543
    assert len({member for row in rows[89:] for member in row["members"]}) == 3718


def test_intent_hash_is_independent_of_python_hash_seed(tmp_path: Path) -> None:
    config_path = _tree(tmp_path)
    code = """
import hashlib
from pathlib import Path
from latent_art_bench.painter_feature_generation_v1 import broad_media_followup as f
root = Path(__import__('sys').argv[1])
config_path = Path(__import__('sys').argv[2])
config = f.load_config(root, config_path)
rows, _ = f._load_upstream(root, config)
body = ''.join(f.canonical_json(row) + '\\n' for row in f._intent_records(config, rows)).encode()
print(hashlib.sha256(body).hexdigest())
"""
    hashes = []
    for seed in ("0", "1", "77"):
        environment = dict(os.environ, PYTHONHASHSEED=seed)
        hashes.append(
            subprocess.check_output(
                [sys.executable, "-c", code, str(tmp_path), str(config_path)],
                text=True,
                env=environment,
            ).strip()
        )
    assert len(set(hashes)) == 1


def test_verified_payload_read_rejects_cas_replacement(tmp_path: Path) -> None:
    spec = followup.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"curtimestamp": "1", "servedby": "1"},
        members=("Q1",),
    )
    original = canonical_json(
        {
            "curtimestamp": "2026-09-02T00:00:00Z",
            "servedby": "host",
            "success": 1,
            "entities": {"Q1": {"id": "Q1", "missing": True}},
        }
    ).encode()
    path = tmp_path / "response"
    path.write_bytes(original)
    inventory = [
        {
            "request_id": spec.request_id,
            "response_sha256": hashlib.sha256(original).hexdigest(),
            "response_bytes": len(original),
        }
    ]
    path.write_bytes(b"{}")
    with pytest.raises(BroadMediaFollowupError, match="hash mismatch"):
        followup._load_verified_payloads([spec], inventory, {spec.request_id: path})


def test_transport_unknown_is_terminal_without_retry(tmp_path: Path) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    config["paths"]["request_events"] = "data/transport-events.jsonl"
    spec = followup.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "format": "json", "ids": "Q1"},
        members=("Q1",),
    )
    event_path = tmp_path / config["paths"]["request_events"]
    events = [
        followup.fc._append_event(
            event_path,
            config["census_id"],
            [],
            {"event_type": "execution_started", "started_at_utc": followup.fc._utc_now()},
        )
    ]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("unknown", request=request)

    with pytest.raises(BroadMediaFollowupError, match="unknowable transport"):
        followup._execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace/transport",
            events,
            transport=httpx.MockTransport(handler),
        )
    ledger = followup.fc._load_event_ledger(event_path, config["census_id"])
    assert calls == 1
    assert ledger[-1]["outcome"] == "terminal_interrupted_new_census_required"
    assert ledger[-1]["retryable"] is False


def test_resumed_retryable_transport_event_is_rejected_before_network(tmp_path: Path) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    config["paths"]["request_events"] = "data/resumed-transport-events.jsonl"
    spec = followup.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "format": "json", "ids": "Q1"},
        members=("Q1",),
    )
    event_path = tmp_path / config["paths"]["request_events"]
    events: list[dict] = []
    followup.fc._append_event(
        event_path,
        config["census_id"],
        events,
        {"event_type": "execution_started", "started_at_utc": followup.fc._utc_now()},
    )
    followup.fc._append_event(
        event_path,
        config["census_id"],
        events,
        {
            "event_type": "attempt_started",
            "request_id": spec.request_id,
            "stage": spec.stage,
            "attempt": 1,
            "started_at_utc": followup.fc._utc_now(),
            "method": "GET",
            "encoded_request_url": followup.fc._encoded_request_url(spec),
            "intent_sequence": 1,
        },
    )
    followup.fc._append_event(
        event_path,
        config["census_id"],
        events,
        {
            "event_type": "attempt_finished",
            "request_id": spec.request_id,
            "stage": spec.stage,
            "attempt": 1,
            "finished_at_utc": followup.fc._utc_now(),
            "outcome": "transport_error",
            "semantic_outcome": None,
            "retryable": True,
            "status_code": None,
            "final_url": None,
            "redirect_history": [],
            "response_headers": {},
            "response_bytes": None,
            "response_sha256": None,
            "response_body_path": None,
            "api_error_code": None,
            "retry_after_seconds": None,
            "error": "legacy retryable transport event",
        },
    )
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request, json={})

    with pytest.raises(BroadMediaFollowupError, match="transport_error is invalid"):
        followup._execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace/resumed-transport",
            events,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    assert len(followup.fc._load_event_ledger(event_path, config["census_id"])) == 3


@pytest.mark.parametrize(
    ("response_body", "expected_outcome"),
    [
        (b"\xff", "terminal_malformed_json_200"),
        (b'{"error":{}}', "terminal_api_error"),
    ],
)
def test_malformed_200_responses_receive_one_terminal_finish(
    tmp_path: Path, response_body: bytes, expected_outcome: str
) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    config["paths"]["request_events"] = "data/malformed-events.jsonl"
    spec = followup.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "format": "json", "ids": "Q1"},
        members=("Q1",),
    )
    event_path = tmp_path / config["paths"]["request_events"]
    events = [
        followup.fc._append_event(
            event_path,
            config["census_id"],
            [],
            {"event_type": "execution_started", "started_at_utc": followup.fc._utc_now()},
        )
    ]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request, content=response_body)

    with pytest.raises(BroadMediaFollowupError, match="ended with terminal"):
        followup._execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace/malformed",
            events,
            transport=httpx.MockTransport(handler),
        )
    ledger = followup.fc._load_event_ledger(event_path, config["census_id"])
    assert calls == 1
    assert len(ledger) == 3
    assert ledger[-1]["outcome"] == expected_outcome
    assert ledger[-1]["retryable"] is False
    if expected_outcome == "terminal_api_error":
        assert ledger[-1]["api_error_code"] == "unknown"


@pytest.mark.parametrize(
    ("status_code", "retry_after_header"), [(200, "1"), (403, "1"), (200, "31")]
)
def test_retry_after_on_nonretryable_response_is_terminal(
    tmp_path: Path, status_code: int, retry_after_header: str
) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    config["paths"]["request_events"] = "data/unexpected-retry-after-events.jsonl"
    spec = followup.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "format": "json", "ids": "Q1"},
        members=("Q1",),
    )
    event_path = tmp_path / config["paths"]["request_events"]
    events = [
        followup.fc._append_event(
            event_path,
            config["census_id"],
            [],
            {"event_type": "execution_started", "started_at_utc": followup.fc._utc_now()},
        )
    ]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        payload = (
            {"success": 1, "entities": {"Q1": {"id": "Q1", "missing": True}}}
            if status_code == 200
            else {"message": "forbidden"}
        )
        return httpx.Response(
            status_code,
            request=request,
            headers={"Retry-After": retry_after_header},
            json=payload,
        )

    with pytest.raises(BroadMediaFollowupError, match="terminal_retry_after"):
        followup._execute_specs(
            tmp_path,
            config,
            [spec],
            tmp_path / "workspace/unexpected-retry-after",
            events,
            transport=httpx.MockTransport(handler),
        )
    ledger = followup.fc._load_event_ledger(event_path, config["census_id"])
    assert calls == 1
    assert len(ledger) == 3
    assert ledger[-1]["outcome"] == "terminal_retry_after_new_census_required"
    assert ledger[-1]["retryable"] is False
    assert ledger[-1]["retry_after_seconds"] == float(retry_after_header)


def test_followup_attempt_validation_rejects_over_ceiling_attempt(tmp_path: Path) -> None:
    request = followup.load_config(tmp_path, _tree(tmp_path))["request_contract"]
    with pytest.raises(BroadMediaFollowupError, match="attempt ceiling"):
        followup._followup_attempt_maps(
            [
                {"event_type": "execution_started"},
                {"event_type": "attempt_started", "attempt": 6},
            ],
            {},
            tmp_path,
            request,
        )


@pytest.mark.parametrize(
    ("outcome", "status_code", "api_error_code", "message"),
    [
        ("retryable_http_error", 418, None, "unfrozen HTTP"),
        ("terminal_http_error", 429, None, "frozen retryable HTTP"),
        ("retryable_api_error", 200, "not-approved", "unfrozen API"),
        ("terminal_api_error", 200, "maxlag", "frozen retryable API"),
    ],
)
def test_followup_attempt_validation_binds_frozen_retry_classes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
    status_code: int,
    api_error_code: str | None,
    message: str,
) -> None:
    request = followup.load_config(tmp_path, _tree(tmp_path))["request_contract"]
    finish = {
        "event_type": "attempt_finished",
        "attempt": 1,
        "outcome": outcome,
        "status_code": status_code,
        "api_error_code": api_error_code,
    }
    monkeypatch.setattr(
        followup.fc,
        "_attempt_maps",
        lambda events, specs, workspace: ({}, {("request", 1): finish}),
    )
    with pytest.raises(BroadMediaFollowupError, match=message):
        followup._followup_attempt_maps(
            [{"event_type": "execution_started"}, finish], {}, tmp_path, request
        )


def test_followup_attempt_validation_rejects_persisted_retry_over_wait_ceiling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = followup.load_config(tmp_path, _tree(tmp_path))["request_contract"]
    finish = {
        "event_type": "attempt_finished",
        "attempt": 1,
        "outcome": "retryable_http_error",
        "status_code": 429,
        "api_error_code": None,
        "retryable": True,
        "retry_after_seconds": 31.0,
    }
    monkeypatch.setattr(
        followup.fc,
        "_attempt_maps",
        lambda events, specs, workspace: ({}, {("request", 1): finish}),
    )
    with pytest.raises(BroadMediaFollowupError, match="retry wait ceiling"):
        followup._followup_attempt_maps(
            [{"event_type": "execution_started"}, finish], {}, tmp_path, request
        )


def test_resume_waits_remaining_global_interval_before_next_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    config["paths"]["request_events"] = "data/interval-events.jsonl"
    config["request_contract"]["minimum_interval_seconds"] = 10.0
    first = followup.fc.RequestSpec(
        "wikidata-entities-0001",
        "wikidata_entities",
        1,
        "https://www.wikidata.org/w/api.php",
        {"action": "wbgetentities", "format": "json", "ids": "Q1"},
        ("Q1",),
    )
    second = followup.fc.RequestSpec(
        "wikidata-entities-0002",
        "wikidata_entities",
        2,
        "https://www.wikidata.org/w/api.php",
        {"action": "wbgetentities", "format": "json", "ids": "Q2"},
        ("Q2",),
    )
    finished = {
        "outcome": "success",
        "attempt": 1,
        "finished_at_utc": followup.fc._utc_now(),
        "response_sha256": "a" * 64,
        "response_bytes": 1,
        "response_body_path": "response_bodies/aa/a.response",
    }
    monkeypatch.setattr(
        followup,
        "_followup_attempt_maps",
        lambda events, specs, workspace, request: (
            {(first.request_id, 1): {}},
            {(first.request_id, 1): finished},
        ),
    )
    monkeypatch.setattr(
        followup.fc,
        "_success_response_path",
        lambda workspace, event: (
            tmp_path / "response",
            {"success": 1, "entities": {"Q1": {"id": "Q1", "missing": True}}},
        ),
    )
    monkeypatch.setattr(followup.fc, "_validate_stage_payload", lambda spec, payload: "ok")
    sleeps: list[float] = []
    monkeypatch.setattr(followup.time, "sleep", sleeps.append)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("stop after interval observation", request=request)

    event_path = tmp_path / config["paths"]["request_events"]
    events = [
        followup.fc._append_event(
            event_path,
            config["census_id"],
            [],
            {"event_type": "execution_started", "started_at_utc": followup.fc._utc_now()},
        )
    ]
    with pytest.raises(BroadMediaFollowupError, match="unknowable transport"):
        followup._execute_specs(
            tmp_path,
            config,
            [first, second],
            tmp_path / "workspace/interval",
            events,
            transport=httpx.MockTransport(handler),
        )
    assert sleeps and 9.0 < sleeps[0] <= 10.0


def test_public_execute_confines_seal_before_workspace_mutation(tmp_path: Path) -> None:
    config_path = _tree(tmp_path)
    external = tmp_path.parent / f"{tmp_path.name}-external-seal.json"
    external.write_text("{}")
    with pytest.raises(BroadMediaFollowupError, match="outside the repository"):
        followup.execute(tmp_path, config_path, external, hash_file(external))
    assert not (tmp_path / "workspace").exists()


def test_cutoff_is_rechecked_at_genesis_and_resume_uses_genesis_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _tree(tmp_path)
    config = followup.load_config(tmp_path, config_path)
    config["request_contract"]["execution_start_not_after_utc"] = "2000-01-01T00:00:00Z"
    seal_path = tmp_path / "data/seal.json"
    seal_path.parent.mkdir(parents=True, exist_ok=True)
    seal_path.write_text("{}")
    lock = tmp_path / config["paths"]["workspace"] / ".execution.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.touch()
    config_relative = str(config_path.relative_to(tmp_path))
    authorization = {
        "config": config,
        "seal": {
            "freeze_path": "data/freeze.json",
            "freeze_sha256": "a" * 64,
            "review_path": "data/review.json",
            "review_sha256": "b" * 64,
        },
        "freeze": {
            "frozen_inputs": [{"path": config_relative, "sha256": hash_file(config_path)}],
            "frozen_input_set_sha256": "c" * 64,
            "preexecution_outputs": followup.expected_outputs(config),
        },
        "intent_sha256": "d" * 64,
    }
    original_enforce_cutoff = followup._enforce_cutoff
    monkeypatch.setattr(
        followup,
        "_enforce_cutoff",
        lambda config: (_ for _ in ()).throw(BroadMediaFollowupError("cutoff passed")),
    )
    with pytest.raises(BroadMediaFollowupError, match="cutoff passed"):
        followup._ensure_genesis(
            tmp_path,
            config_path,
            seal_path,
            hash_file(seal_path),
            authorization,
        )
    event_path = tmp_path / config["paths"]["request_events"]
    assert not event_path.exists()

    monkeypatch.setattr(followup, "_enforce_cutoff", lambda config: "1999-12-31T23:59:59Z")
    events = followup._ensure_genesis(
        tmp_path,
        config_path,
        seal_path,
        hash_file(seal_path),
        authorization,
    )
    assert events[0]["event_type"] == "execution_started"
    assert events[0]["started_at_utc"] == "1999-12-31T23:59:59Z"
    monkeypatch.setattr(followup, "_enforce_cutoff", original_enforce_cutoff)
    resumed = followup._ensure_genesis(
        tmp_path,
        config_path,
        seal_path,
        hash_file(seal_path),
        authorization,
    )
    assert resumed == events


def test_clean_authorized_execution_publishes_manifest_and_receipt_together(
    tmp_path: Path,
) -> None:
    config_path = _tree(tmp_path)
    followup.prepare(tmp_path, config_path)
    config = followup.load_config(tmp_path, config_path)
    required_placeholders = (
        ".gitignore",
        "pyproject.toml",
        "uv.lock",
        "scripts/collect_pfg_v1_broad_media_followup.py",
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/config.py",
        "src/latent_art_bench/io.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/broad_media_followup.py",
        "src/latent_art_bench/painter_feature_generation_v1/federated_census.py",
        "src/latent_art_bench/schemas.py",
        "tests/conftest.py",
        "tests/painter_feature_generation_v1/test_broad_media_followup.py",
    )
    for relative in required_placeholders:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative + "\n")
    required = followup.required_frozen_paths(tmp_path, config_path, config)
    entries = [{"path": path, "sha256": hash_file(tmp_path / path)} for path in required]
    freeze_path = tmp_path / "data/freeze.json"
    freeze = {
        "schema_version": followup._FREEZE_SCHEMA,
        "status": "sealed_for_neutral_quality_review",
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "scope": followup._SCOPE,
        "frozen_input_set_sha256": hashlib.sha256(canonical_json(entries).encode()).hexdigest(),
        "frozen_inputs": entries,
        "preexecution_outputs": followup.expected_outputs(config),
    }
    _write_json(freeze_path, freeze)
    review_path = tmp_path / "data/review.json"
    _write_json(
        review_path,
        {
            "schema_version": followup._REVIEW_SCHEMA,
            "decision": "APPROVE_BROAD_MEDIA_FOLLOWUP_ONLY",
            "blocking_findings": [],
            "independent_reviewer": "test reviewer",
            "census_id": config["census_id"],
            "protocol_id": config["protocol_id"],
            "approved_scope": followup._SCOPE,
            "reviewed_freeze_path": str(freeze_path.relative_to(tmp_path)),
            "reviewed_freeze_sha256": hash_file(freeze_path),
        },
    )
    seal_path = tmp_path / "data/seal.json"
    _write_json(
        seal_path,
        {
            "schema_version": followup._AUTH_SCHEMA,
            "status": "authorized_for_broad_media_followup_execution",
            "census_id": config["census_id"],
            "protocol_id": config["protocol_id"],
            "authorization_scope": followup._SCOPE,
            "freeze_path": str(freeze_path.relative_to(tmp_path)),
            "freeze_sha256": hash_file(freeze_path),
            "review_path": str(review_path.relative_to(tmp_path)),
            "review_sha256": hash_file(review_path),
        },
    )
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        params = request.url.params
        if "ids" in params:
            members = params["ids"].split("|")
            payload = {
                "curtimestamp": "2026-09-02T00:00:00Z",
                "servedby": "test",
                "success": 1,
                "entities": {member: {"id": member, "missing": True} for member in members},
            }
        else:
            members = params["titles"].split("|")
            payload = {
                "batchcomplete": True,
                "curtimestamp": "2026-09-02T00:00:00Z",
                "servedby": "test",
                "query": {"pages": [{"title": member, "missing": True} for member in members]},
            }
        return httpx.Response(200, request=request, json=payload)

    receipt = followup.execute(
        tmp_path,
        config_path,
        seal_path,
        hash_file(seal_path),
        transport=httpx.MockTransport(handler),
    )
    publication = tmp_path / "data/publication"
    assert calls == 182
    assert receipt["successful_requests"] == 182
    assert (publication / "candidates.jsonl").is_file()
    assert (publication / "execution_receipt.json").is_file()


def test_upstream_sequence_tamper_fails_closed(tmp_path: Path) -> None:
    config_path = _tree(tmp_path)
    config = json.loads(config_path.read_text())
    candidate = tmp_path / "data/upstream.jsonl"
    rows = candidate.read_text().splitlines()
    first = json.loads(rows[0])
    first["candidate_sequence"] = 2
    rows[0] = canonical_json(first)
    candidate.write_text("\n".join(rows) + "\n")
    config["source_frame_contract"]["upstream_candidate_sha256"] = hash_file(candidate)
    receipt = tmp_path / "data/upstream-receipt.json"
    receipt_value = json.loads(receipt.read_text())
    receipt_value["candidate_manifest_sha256"] = hash_file(candidate)
    _write_json(receipt, receipt_value)
    config["source_frame_contract"]["upstream_receipt_sha256"] = hash_file(receipt)
    _write_json(config_path, config)
    with pytest.raises(BroadMediaFollowupError, match="candidate row"):
        followup.prepare(tmp_path, config_path)


def test_config_rejects_nested_outputs(tmp_path: Path) -> None:
    config_path = _tree(tmp_path)
    config = json.loads(config_path.read_text())
    config["paths"]["candidate_manifest"] = "workspace/followup/candidates.jsonl"
    _write_json(config_path, config)
    with pytest.raises(BroadMediaFollowupError, match="overlap"):
        followup.load_config(tmp_path, config_path)


def test_single_read_hash_binding_rejects_same_path_replacement(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    path.write_text("reviewed\n")
    reviewed_sha = hashlib.sha256(b"reviewed\n").hexdigest()
    replacement = tmp_path / "replacement.json"
    replacement.write_text("unreviewed\n")
    replacement.replace(path)
    with pytest.raises(BroadMediaFollowupError, match="hash mismatch"):
        followup._read_hashed_bytes(path, reviewed_sha, "gate")


def test_expected_outputs_include_lock_and_response_store(tmp_path: Path) -> None:
    config = followup.load_config(tmp_path, _tree(tmp_path))
    assert followup.expected_outputs(config)[-3:] == [
        {"path": "data/publication", "state": "absent"},
        {"path": "workspace/followup/.execution.lock", "state": "absent"},
        {"path": "workspace/followup/response_bodies", "state": "absent"},
    ]
