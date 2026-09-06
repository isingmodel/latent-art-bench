import base64
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import collection as c
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import publish


def request():
    return dict(
        request_id="slot0000",
        route=s.ROUTES[0],
        sequence=0,
        payload=t.payload(s.ROUTES[0], "An oil painting of a river."),
    )


def success():
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (30, 60, 90)).save(buffer, format="PNG")
    return dict(
        data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())], usage=dict(cost=0.07)
    )


def test_transient_retry_has_disjoint_evidence_obeys_delay_and_never_resends_success(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    calls, elapsed = [], [0.0]

    def handler(req):
        calls.append(req)
        return (
            httpx.Response(
                429, json={"error": {"message": "rate limited"}}, headers={"retry-after": "120"}
            )
            if len(calls) == 1
            else httpx.Response(200, json=success())
        )

    transport = httpx.MockTransport(handler)

    def sleep(delay):
        elapsed[0] += delay

    freeze = {"proxy_source": {}}
    publish(tmp_path / s.DIRECTORY / "main_freeze.json", freeze)
    req = request()
    parent = c.send_once(
        tmp_path, s.RUN_ID, req, freeze, tmp_path, transport=transport, sleep=sleep
    )
    assert c.retry_eligible(tmp_path, parent)
    child = c.retry_once(
        tmp_path,
        req,
        parent,
        freeze,
        tmp_path,
        transport=transport,
        sleep=sleep,
        now=lambda: elapsed[0],
    )
    assert child["status"] == "image_returned" and child["response_path"] != parent["response_path"]
    assert child["request_id"] != parent["request_id"] and len(calls) == 2
    assert calls[0].content == calls[1].content
    assert elapsed[0] >= 150
    budget = t.budget_state(tmp_path)
    assert budget["attempts"] == 2 and budget["accounted_usd"] == pytest.approx(0.07)
    assert not c.retry_eligible(tmp_path, child)
    again = c.retry_once(
        tmp_path,
        req,
        parent,
        freeze,
        tmp_path,
        transport=transport,
        sleep=sleep,
        now=lambda: elapsed[0],
    )
    assert again == child and len(calls) == 2
    with pytest.raises(ValueError, match="already exists"):
        c.send_once(tmp_path, s.RUN_ID, req, freeze, tmp_path, transport=transport, sleep=sleep)


def test_unknown_charge_cannot_trigger_retry_or_more_dispatch(tmp_path, monkeypatch):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    transport = httpx.MockTransport(
        lambda req: httpx.Response(500, json={"error": "internal error"})
    )
    row = c.send_once(
        tmp_path, s.RUN_ID, request(), {}, tmp_path, transport=transport, sleep=lambda _: None
    )
    assert row["cost_usd"] is None and c.stop_reason(row) == "uncertain_outcome_or_charge"
    assert not c.retry_eligible(tmp_path, row)
    with pytest.raises(ValueError, match="unresolved"):
        c.check_resources(tmp_path, request())


def test_clusters_are_per_route_and_count_failed_initial_attempts():
    def row(route, failed):
        return dict(route=route, status="http_error" if failed else "image_returned")

    a, b = s.ROUTES[:2]
    rows = [row(a, True), row(b, False), row(a, True), row(b, False)]
    assert not c.failure_cluster(rows, a)
    assert c.failure_cluster(rows + [row(a, True)], a)
    spaced = [row(a, i in (0, 5, 10, 15)) for i in range(20)]
    assert c.failure_cluster(spaced, a)
    assert not c.failure_cluster(spaced, b)


@pytest.mark.parametrize(
    "budget",
    [
        dict(attempts=1050, paid_attempts=500, accounted_usd=40, unresolved=0, uncertain=0),
        dict(attempts=900, paid_attempts=612, accounted_usd=40, unresolved=0, uncertain=0),
        dict(attempts=900, paid_attempts=500, accounted_usd=70.01, unresolved=0, uncertain=0),
    ],
)
def test_resource_caps_stop_before_an_extra_request(tmp_path, monkeypatch, budget):
    monkeypatch.setattr(t, "budget_state", lambda root: budget)
    with pytest.raises(ValueError):
        c.check_resources(tmp_path, request())


def test_retry_after_date_and_bad_value():
    assert (
        c.retry_delay(
            {"response_headers": {"retry-after": "Sun, 06 Sep 2026 00:02:00 GMT"}}, 1788652800
        )
        >= 60
    )
    with pytest.raises(ValueError, match="Retry-After"):
        c.retry_delay({"response_headers": {"retry-after": "later"}}, 0)


def test_repeated_failures_close_collection_before_more_retries(tmp_path, monkeypatch):
    elapsed, calls = [0.0], []

    def sleep(delay):
        elapsed[0] += delay

    def handler(req):
        calls.append(req)
        return httpx.Response(429, json={"error": "rate limited"})

    freeze = dict(proxy_source={}, window_origin_unix=0, window_offsets_hours=[0] * 8)
    monkeypatch.setattr(s, "verify", lambda root: freeze)
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    rows = [dict(request(), request_id=f"slot{i:04d}", sequence=i, window=0) for i in range(5)]
    publish(tmp_path / s.DIRECTORY / "main_freeze.json", freeze)
    publish(tmp_path / s.DIRECTORY / "requests.jsonl", rows, lines=True)
    result = c.run_due(
        tmp_path,
        tmp_path,
        transport=httpx.MockTransport(handler),
        sleep=sleep,
        now=lambda: elapsed[0],
    )
    assert result["status"] == "stopped_for_diagnosis"
    assert result["reason"] == "systematic_failure_cluster"
    assert result["terminal_slots"] == 3 and len(result["unattempted_slot_ids"]) == 2
    assert len(calls) == 5  # first two slots each retry once; third trips the stop.
    with pytest.raises(ValueError, match="permanently terminal"):
        c.run_due(tmp_path, tmp_path, transport=httpx.MockTransport(handler))
    assert len(calls) == 5


def test_future_window_returns_without_any_request(tmp_path, monkeypatch):
    freeze = dict(window_origin_unix=100, window_offsets_hours=[0] * 8)
    monkeypatch.setattr(s, "verify", lambda root: freeze)
    publish(tmp_path / s.DIRECTORY / "requests.jsonl", [dict(request(), window=0)], lines=True)
    result = c.run_due(tmp_path, tmp_path, now=lambda: 0)
    assert result["status"] == "waiting" and result["not_before_unix"] == 100
    assert result["budget"]["attempts"] == 0
