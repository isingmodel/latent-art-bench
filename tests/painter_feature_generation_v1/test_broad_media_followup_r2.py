import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.painter_feature_generation_v1 import (
    broad_media_followup_r2 as r2,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _config(tmp_path: Path) -> dict:
    config = json.loads(
        (
            REPOSITORY_ROOT / "configs/painter_feature_generation_v1/broad_media_followup_r2.json"
        ).read_text()
    )
    config["census_id"] = "test-r2"
    config["request_contract"]["minimum_interval_seconds"] = 0.0
    config["request_contract"]["retry_backoff_base_seconds"] = 0.0
    config["paths"]["request_events"] = "events.jsonl"
    return config


def _spec() -> r2.fc.RequestSpec:
    return r2.fc.RequestSpec(
        request_id="wikidata-entities-0001",
        stage="wikidata_entities",
        sequence=1,
        endpoint="https://www.wikidata.org/w/api.php",
        params={"action": "wbgetentities", "format": "json", "ids": "Q1"},
        members=("Q1",),
    )


def _genesis(tmp_path: Path, config: dict) -> list[dict]:
    return [
        r2.fc._append_event(
            tmp_path / config["paths"]["request_events"],
            config["census_id"],
            [],
            {"event_type": "execution_started", "started_at_utc": r2.fc._utc_now()},
        )
    ]


def _success(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        request=request,
        json={"success": 1, "entities": {"Q1": {"id": "Q1", "missing": True}}},
    )


def test_r2_binds_actual_terminal_r1_plural_error() -> None:
    config_path = (
        REPOSITORY_ROOT / "configs/painter_feature_generation_v1/broad_media_followup_r2.json"
    )
    config = r2.load_config(REPOSITORY_ROOT, config_path)
    r2._validate_prior_terminal(REPOSITORY_ROOT, config)
    retry = config["retry_contract"]
    events = [
        json.loads(line)
        for line in (REPOSITORY_ROOT / retry["prior_events_path"]).read_text().splitlines()
    ]
    assert retry["prior_terminal_outcome"] == "terminal_retry_after_new_census_required"
    assert events[-1]["event_sha256"] == retry["prior_terminal_event_sha256"]
    assert events[-1]["retry_after_seconds"] == 5.0


def test_plural_maxlag_retries_then_completes(tmp_path: Path) -> None:
    config = _config(tmp_path)
    spec = _spec()
    events = _genesis(tmp_path, config)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200,
                request=request,
                headers={"Retry-After": "0"},
                json={"errors": [{"code": "maxlag", "text": "Waiting for replica"}]},
            )
        return _success(request)

    receipts, _ = r2._execute_specs(
        tmp_path,
        config,
        [spec],
        tmp_path / "workspace",
        events,
        transport=httpx.MockTransport(handler),
    )
    ledger = r2.fc._load_event_ledger(
        tmp_path / config["paths"]["request_events"], config["census_id"]
    )
    assert calls == 2
    assert receipts[0]["attempt"] == 2
    assert [row.get("outcome") for row in ledger] == [
        None,
        None,
        "retryable_api_error",
        None,
        "success",
    ]
    assert ledger[2]["api_error_code"] == "maxlag"
    assert ledger[2]["retry_after_seconds"] == 0.0


@pytest.mark.parametrize(
    "errors",
    [
        [],
        {},
        [{"code": ""}],
        [{"code": 5}],
        [{"code": "maxlag"}, {"code": "readonly"}],
    ],
)
def test_malformed_or_multiple_plural_errors_are_terminal(tmp_path: Path, errors: object) -> None:
    config = _config(tmp_path)
    events = _genesis(tmp_path, config)
    with pytest.raises(r2.BroadMediaFollowupError, match="terminal_api_error"):
        r2._execute_specs(
            tmp_path,
            config,
            [_spec()],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, request=request, json={"errors": errors})
            ),
        )
    ledger = r2.fc._load_event_ledger(
        tmp_path / config["paths"]["request_events"], config["census_id"]
    )
    assert len(ledger) == 3
    assert ledger[-1]["outcome"] == "terminal_api_error"
    assert ledger[-1]["api_error_code"] == "malformed_or_multiple_plural_errors"


@pytest.mark.parametrize("plural", [[], [{"code": "readonly"}]])
def test_mixed_singular_and_plural_error_envelopes_are_terminal(
    tmp_path: Path, plural: list[dict]
) -> None:
    config = _config(tmp_path)
    events = _genesis(tmp_path, config)
    with pytest.raises(r2.BroadMediaFollowupError, match="terminal_api_error"):
        r2._execute_specs(
            tmp_path,
            config,
            [_spec()],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    request=request,
                    json={"error": {"code": "maxlag"}, "errors": plural},
                )
            ),
        )
    ledger = r2.fc._load_event_ledger(
        tmp_path / config["paths"]["request_events"], config["census_id"]
    )
    assert len(ledger) == 3
    assert ledger[-1]["api_error_code"] == "mixed_api_error_envelopes"


def test_extremely_long_retry_after_is_terminalized(tmp_path: Path) -> None:
    config = _config(tmp_path)
    events = _genesis(tmp_path, config)
    huge = "9" * 5000
    with pytest.raises(r2.BroadMediaFollowupError, match="terminal_retry_after"):
        r2._execute_specs(
            tmp_path,
            config,
            [_spec()],
            tmp_path / "workspace",
            events,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    request=request,
                    headers={"Retry-After": huge},
                    json={"errors": [{"code": "maxlag"}]},
                )
            ),
        )
    ledger = r2.fc._load_event_ledger(
        tmp_path / config["paths"]["request_events"], config["census_id"]
    )
    assert len(ledger) == 3
    assert ledger[-1]["outcome"] == "terminal_retry_after_new_census_required"
    assert ledger[-1]["retryable"] is False
