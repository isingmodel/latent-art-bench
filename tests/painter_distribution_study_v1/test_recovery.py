import base64
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import collection as c
from latent_art_bench.painter_distribution_study_v1 import recovery as p
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events, publish


def failure(root, monkeypatch, code=502):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    request = dict(
        request_id=p.RECOVERY_SLOT,
        route=s.ROUTES[1],
        window=0,
        payload=t.payload(s.ROUTES[1], "An oil painting of a landscape."),
    )
    path = root / p.predecessor.DIRECTORY / "generation_events.jsonl"
    append_event(path, dict(kind="attempt", request_id=request["request_id"], paid=True))
    result = t._send(
        root,
        p.predecessor.RUN_ID,
        request,
        transport=httpx.MockTransport(
            lambda req: httpx.Response(
                code, json={"error": {"message": "Upstream submission failed", "code": code}}
            )
        ),
    )
    row = append_event(path, result)
    return request, row


def good_response():
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (20, 50, 90)).save(buffer, format="PNG")
    return dict(
        data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())], usage=dict(cost=0.07)
    )


@pytest.mark.parametrize("code", [500, 502, 503, 504])
def test_complete_explicit_failure_keeps_full_cost_reserve(tmp_path, monkeypatch, code):
    _, row = failure(tmp_path, monkeypatch, code)
    assert row["cost_usd"] is None and p.reserved_failure(tmp_path, row)
    raw, budget = t.budget_state(tmp_path), p.budget_state(tmp_path)
    assert raw["uncertain"] == 1 and budget["uncertain"] == 0
    assert raw["accounted_usd"] == budget["accounted_usd"] == 5
    assert budget["provider_reported_usd"] == 0
    assert budget["missing_cost_failures"] == 1 and budget["contingency_reserve_usd"] == 5
    assert p.retry_eligible(tmp_path, row) and p.stop_reason(tmp_path, row) is None


def test_exception_does_not_cover_unknown_outcomes_or_nonerror_payloads(tmp_path, monkeypatch):
    _, row = failure(tmp_path, monkeypatch)
    assert not p.reserved_failure(tmp_path, dict(row, complete=False))
    assert not p.reserved_failure(tmp_path, dict(row, status="image_returned"))
    assert not p.reserved_failure(tmp_path, dict(row, route=s.ROUTES[2]))
    monkeypatch.setattr(
        c,
        "read_response",
        lambda root, item: b'{"error":{"code":502,"message":"x"},"id":"job-pending"}',
    )
    assert not p.reserved_failure(tmp_path, row)
    assert p.budget_state(tmp_path)["uncertain"] == 1


@pytest.mark.parametrize("retry_fails", [False, True])
def test_cross_census_retry_is_once_and_never_releases_missing_cost_reserve(
    tmp_path, monkeypatch, retry_fails
):
    request, parent = failure(tmp_path, monkeypatch)
    monkeypatch.setattr(c, "retry_delay", lambda row, now: 0)
    freeze = dict(proxy_source={})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", freeze)
    next_request = dict(request, request_id="next")
    calls = []

    def handler(req):
        calls.append(req)
        if retry_fails and len(calls) == 1:
            return httpx.Response(
                502, json={"error": {"message": "submission failed", "code": 502}}
            )
        return httpx.Response(200, json=good_response())

    engine = p.Window(
        tmp_path,
        freeze,
        [request, next_request],
        tmp_path,
        transport=httpx.MockTransport(handler),
        interval=0,
    )
    assert engine.run() is None and len(calls) == 2
    child_dir = tmp_path / t.MANIFESTS / (p.RUN_ID + "-retry-" + p.RECOVERY_SLOT)
    authority = read_json(child_dir / "retry_authority.json")
    assert authority["parent_run_id"] == p.predecessor.RUN_ID
    assert authority["predecessor_terminal"] == parent
    assert authority["request"]["payload"] == request["payload"]
    slots = events(tmp_path / p.DIRECTORY / "slot_events.jsonl")
    assert slots[0]["initial_status"] == "http_error" and slots[0]["retry_terminal_sha256"]
    assert slots[0]["status"] == ("http_error" if retry_fails else "image_returned")
    assert len(events(child_dir / "generation_events.jsonl")) == 2
    budget = p.budget_state(tmp_path)
    assert budget["contingency_reserve_usd"] == (10 if retry_fails else 5)
    assert budget["provider_reported_usd"] == pytest.approx(0.07 if retry_fails else 0.14)
    receipt = p.close(tmp_path, [request, next_request], "completed", None)
    assert receipt["unattempted_slot_ids"] == receipt["unresolved_slot_ids"] == []
