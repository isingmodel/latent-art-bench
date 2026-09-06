import base64
import gzip
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import pilot
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events, publish


def image_body(cost=0.07):
    buffer = io.BytesIO()
    Image.new("RGB", (1024, 1024), (35, 80, 120)).save(buffer, format="PNG")
    return json.dumps(
        {
            "data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}],
            "usage": {"cost": cost},
        }
    ).encode()


def fixture(tmp_path, monkeypatch):
    config = {"scenes": ["River.", "Village.", "Field."]}
    requests = pilot.request_grid(config)
    directory = tmp_path / t.MANIFESTS / pilot.RUN_ID
    publish(directory / "requests.jsonl", requests, lines=True)
    publish(
        directory / "generation_freeze.json",
        dict(
            run_id=pilot.RUN_ID,
            requests_sha256=t.hash_file(directory / "requests.jsonl"),
            inputs=[],
            proxy_source={},
            software={},
            authority="PILOT.md: 18 technical requests; no research measurement",
        ),
    )
    monkeypatch.setattr(t, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(t, "proxy_snapshot", lambda *_: {})
    monkeypatch.setattr(
        t.shutil, "disk_usage", lambda _: type("Disk", (), {"free": 10 * 1024**3})()
    )
    secret = "sk-or-test-" + "q" * 30
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=" + secret)
    return requests, directory, secret


def test_exact_route_contract_and_no_unsupported_resolution():
    rows = pilot.request_grid({"scenes": ["River.", "Village.", "Field."]})
    assert len(rows) == 18
    assert all(sum(r["route"] == route for r in rows) == 6 for route in t.ROUTES)
    assert "resolution" not in rows[1]["payload"]
    assert rows[0]["payload"]["provider"] == {
        "only": ["google-ai-studio"],
        "allow_fallbacks": False,
    }
    rows[0]["payload"]["n"] = 2
    with pytest.raises(ValueError, match="pinned"):
        t.validate_requests(rows)


@pytest.mark.parametrize(
    "body", [b"[]", b'{"data":[]}', b'{"data":[{"url":"https://example.org/x.png"}]}']
)
def test_nonembedded_or_wrong_envelope_is_rejected(body):
    with pytest.raises(ValueError):
        t.inspect_response(body)


def test_geometry_and_cost_are_not_feature_measurements():
    observed = t.inspect_response(image_body())
    assert observed["square_1024"] and observed["minimum_512"]
    assert set(observed) == {
        "image_sha256",
        "image_bytes",
        "width",
        "height",
        "format",
        "mode",
        "minimum_512",
        "square_1024",
        "reported",
    }
    assert t.cost_from_response(image_body(), 200, True) == 0.07
    assert t.cost_from_response(b'{"data":[]}', 200, True) is None
    assert t.cost_from_response(b'{"error":{"code":402}}', 402, True) == 0
    assert t.cost_from_response(b"unparseable", 200, False) == 0
    assert t.cost_from_response(b'{"usage":{"cost":NaN}}', 200, True) is None


def test_complete_mock_pilot_has_durable_intents_no_key_leak_and_no_rerun(tmp_path, monkeypatch):
    requests, directory, secret = fixture(tmp_path, monkeypatch)
    calls = []

    def handler(request):
        calls.append(request)
        rows = events(directory / "generation_events.jsonl")
        assert rows[-1]["kind"] == "attempt"
        assert rows[-1]["request_id"] == requests[len(calls) - 1]["request_id"]
        assert request.method == "POST"
        if request.url.host == "openrouter.ai":
            assert request.headers["Authorization"] == "Bearer " + secret
        else:
            assert request.url.host == "127.0.0.1"
            assert "Authorization" not in request.headers
        return httpx.Response(200, content=image_body())

    receipt = t.run(
        tmp_path,
        pilot.RUN_ID,
        Path("unused"),
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    assert len(calls) == 18 and receipt["budget"]["paid_attempts"] == 12
    assert receipt["budget"]["accounted_usd"] == pytest.approx(0.84)
    for row in events(directory / "generation_events.jsonl"):
        if row["kind"] == "terminal":
            body = gzip.decompress((tmp_path / row["response_path"]).read_bytes())
            assert body == image_body() and secret.encode() not in body
    assert secret not in (directory / "generation_events.jsonl").read_text()
    with pytest.raises(ValueError, match="terminal"):
        t.run(tmp_path, pilot.RUN_ID, Path("unused"))


def test_uncertain_transport_stops_and_cannot_redispatch(tmp_path, monkeypatch):
    _, directory, _ = fixture(tmp_path, monkeypatch)
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("not retained", request=request)

    for _ in range(2):
        with pytest.raises(ValueError, match="uncertain|unresolved"):
            t.run(
                tmp_path,
                pilot.RUN_ID,
                Path("unused"),
                transport=httpx.MockTransport(handler),
                sleep=lambda _: None,
            )
    assert len(calls) == 1
    assert t.budget_state(tmp_path)["accounted_usd"] == 5
    assert events(directory / "generation_events.jsonl")[-1]["error"] == "ReadTimeout"


def test_missing_cost_on_success_stops_after_one_request(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="uncertain"):
        t.run(
            tmp_path,
            pilot.RUN_ID,
            Path("unused"),
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=image_body(None))),
            sleep=lambda _: None,
        )
    assert t.budget_state(tmp_path)["attempts"] == 1


def test_budget_guard_counts_prior_run_and_reserves_before_dispatch(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    prior = tmp_path / t.MANIFESTS / "prior" / "generation_events.jsonl"
    append_event(prior, dict(kind="attempt", request_id="prior-1", paid=True))
    append_event(
        prior, dict(kind="terminal", request_id="prior-1", status="image_returned", cost_usd=71)
    )
    with pytest.raises(ValueError, match="spending reserve"):
        t.run(tmp_path, pilot.RUN_ID, Path("unused"))
    assert t.budget_state(tmp_path)["attempts"] == 1


def test_secret_echo_is_suppressed_from_all_evidence(tmp_path, monkeypatch):
    _, directory, secret = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="uncertain"):
        t.run(
            tmp_path,
            pilot.RUN_ID,
            Path("unused"),
            transport=httpx.MockTransport(lambda _: httpx.Response(400, json={"error": secret})),
            sleep=lambda _: None,
        )
    terminal = events(directory / "generation_events.jsonl")[-1]
    assert secret not in (directory / "generation_events.jsonl").read_text()
    assert secret.encode() not in gzip.decompress(
        (tmp_path / terminal["response_path"]).read_bytes()
    )
    assert terminal["error"] == "credential_echo"


def test_unresolved_intent_from_crash_prevents_new_calls(tmp_path, monkeypatch):
    requests, directory, _ = fixture(tmp_path, monkeypatch)
    append_event(
        directory / "generation_events.jsonl",
        dict(
            kind="attempt",
            request_id="technical-00",
            paid=True,
            request_sha256=t.digest(requests[0]),
        ),
    )
    with pytest.raises(ValueError, match="unresolved"):
        t.run(tmp_path, pilot.RUN_ID, Path("unused"))
