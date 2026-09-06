import base64
import io
import json
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import collection as c
from latent_art_bench.painter_distribution_study_v1 import continuation as p
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events, publish

REFUSAL = dict(error=dict(type="image_generation_user_error", code="moderation_blocked"))


def test_only_verified_complete_explicit_zero_cost_moderation_avoids_contract_stop(monkeypatch):
    row = dict(complete=True, status="http_error", status_code=400, cost_usd=0)
    monkeypatch.setattr(c, "read_response", lambda root, record: json.dumps(REFUSAL).encode())
    assert p.stop_reason(Path(), row) is None
    assert p.stop_reason(Path(), dict(row, complete=False)) == "uncertain_outcome_or_charge"
    assert p.stop_reason(Path(), dict(row, cost_usd=None)) == "uncertain_outcome_or_charge"
    monkeypatch.setattr(c, "read_response", lambda root, record: b'{"error":{"code":"bad_key"}}')
    assert p.stop_reason(Path(), row) == "authentication_payment_or_payload_contract"

    def tampered(root, record):
        raise ValueError("hash differs")

    monkeypatch.setattr(c, "read_response", tampered)
    assert p.stop_reason(Path(), row) == "invalid_refusal_evidence"


def exercise(tmp_path, monkeypatch, *, predecessor_failures=0):
    monkeypatch.setattr(t, "key_from_env", lambda root: "offline-test-token")
    monkeypatch.setattr(t, "proxy_snapshot", lambda root: {})
    route = s.ROUTES[2]
    freeze = dict(proxy_source={})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", freeze)
    for i in range(predecessor_failures):
        path = tmp_path / p.predecessor.DIRECTORY / "generation_events.jsonl"
        append_event(path, dict(kind="attempt", request_id=f"prior{i}", route=route, paid=False))
        append_event(
            path,
            dict(
                kind="terminal",
                request_id=f"prior{i}",
                route=route,
                status="http_error",
                cost_usd=0,
            ),
        )
    requests = [
        dict(
            request_id=f"next{i}",
            route=route,
            window=0,
            payload=t.payload(route, "An oil painting of a pond."),
        )
        for i in range(2)
    ]
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (20, 50, 90)).save(buffer, format="PNG")
    good = dict(data=[dict(b64_json=base64.b64encode(buffer.getvalue()).decode())])
    calls = []

    def handler(request):
        calls.append(request)
        return (
            httpx.Response(400, json=REFUSAL) if len(calls) == 1 else httpx.Response(200, json=good)
        )

    engine = p.Window(
        tmp_path, freeze, requests, tmp_path, transport=httpx.MockTransport(handler), interval=0
    )
    return engine, calls


def test_isolated_refusal_is_retained_without_retry_and_next_slot_runs(tmp_path, monkeypatch):
    engine, calls = exercise(tmp_path, monkeypatch)
    assert engine.run() is None
    assert len(calls) == 2
    assert [r["status"] for r in events(tmp_path / p.DIRECTORY / "slot_events.jsonl")] == [
        "http_error",
        "image_returned",
    ]
    assert not list((tmp_path / t.MANIFESTS).glob(p.RUN_ID + "-retry-*"))
    assert t.budget_state(tmp_path)["unresolved"] == 0


def test_predecessor_failures_still_count_toward_route_cluster_stop(tmp_path, monkeypatch):
    engine, calls = exercise(tmp_path, monkeypatch, predecessor_failures=2)
    assert engine.run() == "systematic_failure_cluster"
    assert len(calls) == 1


def test_remaining_inventory_excludes_nonprefix_completed_slots_and_refusal(tmp_path, monkeypatch):
    requests = s.request_inventory(read_json(Path.cwd() / s.CONFIG))
    path = tmp_path / s.DIRECTORY / "requests.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in requests))
    indices = [*range(47), 95]
    for i in indices:
        status = "http_error" if i == 36 else "image_returned"
        append_event(
            tmp_path / p.predecessor.DIRECTORY / "slot_events.jsonl",
            dict(request_id=requests[i]["request_id"], status=status),
        )
        append_event(
            tmp_path / p.predecessor.DIRECTORY / "generation_events.jsonl",
            dict(
                kind="terminal",
                request_id=requests[i]["request_id"],
                status=status,
                complete=True,
                status_code=400 if i == 36 else 200,
                cost_usd=0,
            ),
        )
    publish(
        tmp_path / p.predecessor.DIRECTORY / "generation_receipt.json",
        dict(status="stopped_for_diagnosis", unresolved_slot_ids=[], outputs=[]),
    )
    monkeypatch.setattr(c, "read_response", lambda root, row: json.dumps(REFUSAL).encode())
    remaining = p.remaining_requests(tmp_path)
    assert len(remaining) == 960
    assert remaining == [r for i, r in enumerate(requests) if i not in indices]
    assert all(r["request_id"] != "slot0036" for r in remaining)
