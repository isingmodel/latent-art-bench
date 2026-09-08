"""Exact-error recovery checks use synthetic bodies and offline MockTransport only."""

import gzip
import json

import httpx
import pytest
from painter_responsiveness_v2.test_collection import RUN, image_body, setup

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, events, publish
from latent_art_bench.painter_responsiveness_recovery_v1 import collection as r
from latent_art_bench.painter_responsiveness_v2 import collection as base
from latent_art_bench.painter_responsiveness_v2 import common, workflow

RECOVERY = "prv2-mock-recovery"


def ready(tmp_path, monkeypatch):
    prior, requests, clock = setup(tmp_path, monkeypatch)
    monkeypatch.setattr(workflow, "source_paths", lambda _: sorted(base.required_sources()))
    monkeypatch.setattr(workflow, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(r, "committed", lambda *_: "a" * 40)
    monkeypatch.setattr(r, "monotonic", clock.now)
    count = 0

    def original(_):
        nonlocal count
        count += 1
        if count == 1:
            return httpx.Response(503, content=r.EXACT_BODY, headers={"content-type": "text/plain"})
        return httpx.Response(401, json={"error": "synthetic stop"})

    base.collect(
        tmp_path,
        RUN,
        tmp_path / "proxy",
        transport=httpx.MockTransport(original),
        sleep=clock.sleep,
    )
    assert count == 2  # The original classifier did not retry this non-JSON response.
    source_paths = {row["path"] for row in read_json(prior / "freeze.json")["inputs"]}
    for path in r.required_sources():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Synthetic recovery source binding.\n")
    source_paths.update(str(path) for path in r.required_sources())
    source_paths.update(
        str(path.relative_to(tmp_path)) for path in prior.iterdir() if path.is_file()
    )
    error = next(
        row
        for row in events(prior / "generation_events.jsonl")
        if row["kind"] == "terminal" and row["status_code"] == 503
    )
    source = read_json(prior / "freeze.json")
    source.update(
        run_id=RECOVERY,
        inputs=bindings(tmp_path, source_paths),
        recovery=dict(
            policy=r.POLICY,
            predecessor_run_id=RUN,
            predecessor_receipt_path=str((prior / "collection_receipt.json").relative_to(tmp_path)),
            predecessor_receipt_sha256=hash_file(prior / "collection_receipt.json"),
            qualifying_error={
                key: error[key]
                for key in (
                    "request_id",
                    "attempt",
                    "response_path",
                    "response_sha256",
                    "stored_response_sha256",
                )
            },
        ),
    )
    directory = tmp_path / common.directory(RECOVERY)
    publish(directory / "planned_requests.jsonl", requests, lines=True)
    publish(directory / "freeze.json", source)
    preserved = {
        path: hash_file(path)
        for parent in (prior, tmp_path / common.WORKSPACE / RUN)
        for path in parent.rglob("*")
        if path.is_file()
    }
    return directory, requests, clock, preserved


def run(tmp_path, handler, clock):
    return r.collect(
        tmp_path,
        RECOVERY,
        tmp_path / "proxy",
        transport=httpx.MockTransport(handler),
        sleep=clock.sleep,
    )


def test_exact_proxy_503_retries_identically_preserves_bytes_and_predecessor(tmp_path, monkeypatch):
    directory, _, clock, preserved = ready(tmp_path, monkeypatch)
    calls, body = [], image_body()

    def handler(request):
        assert request.url == base.URL and request.method == "POST"
        assert "Authorization" not in request.headers
        calls.append(request.content)
        if len(calls) == 1:
            return httpx.Response(503, content=r.EXACT_BODY, headers={"content-type": "text/plain"})
        return httpx.Response(200, content=body)

    receipt = run(tmp_path, handler, clock)
    assert receipt["status_counts"] == {"image_returned": 192}
    assert len(calls) == 193 and calls[0] == calls[1]
    assert receipt["technical_retries_dispatched"] == 1 and receipt["paid_requests"] == 0
    rows = [
        row for row in events(directory / "generation_events.jsonl") if row["kind"] == "terminal"
    ]
    failed = rows[0]
    assert failed["known_error_envelope"] is True
    assert failed["original_known_error_envelope"] is False
    assert failed["retry_qualification"] == r.POLICY
    assert gzip.decompress((tmp_path / failed["response_path"]).read_bytes()) == r.EXACT_BODY
    assert read_jsonl(directory / "slot_outcomes.jsonl")[0]["selected_attempt"] == 2
    assert all(hash_file(path) == expected for path, expected in preserved.items())
    assert workflow.collection_inputs(tmp_path, RECOVERY)[3] == receipt


@pytest.mark.parametrize(
    "body,content_type,status",
    [
        (b"<html>gateway unavailable</html>", "text/html", "http_error"),
        (r.EXACT_BODY + b"\n", "text/plain", "http_error"),
        (r.EXACT_BODY, "text/html", "http_error"),
        (b'{"error":"safety refusal"}', "application/json", "refused"),
    ],
)
def test_other_errors_are_not_qualified_or_retried(
    tmp_path, monkeypatch, body, content_type, status
):
    directory, _, clock, _ = ready(tmp_path, monkeypatch)
    calls = 0

    def handler(_):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, content=body, headers={"content-type": content_type})
        return httpx.Response(401, json={"error": "synthetic stop"})

    receipt = run(tmp_path, handler, clock)
    assert calls == 2 and receipt["technical_retries_dispatched"] == 0
    first = next(
        row for row in events(directory / "generation_events.jsonl") if row["kind"] == "terminal"
    )
    assert first["status"] == status and "retry_qualification" not in first


def test_exact_prefix_with_incomplete_delivery_never_retries(tmp_path, monkeypatch):
    directory, _, clock, _ = ready(tmp_path, monkeypatch)

    class Broken(httpx.SyncByteStream):
        def __iter__(self):
            yield r.EXACT_BODY
            raise httpx.ReadTimeout("synthetic incomplete response")

    receipt = run(
        tmp_path,
        lambda _: httpx.Response(503, stream=Broken(), headers={"content-type": "text/plain"}),
        clock,
    )
    assert receipt["terminal_attempts"] == 1 and receipt["technical_retries_dispatched"] == 0
    first = next(
        row for row in events(directory / "generation_events.jsonl") if row["kind"] == "terminal"
    )
    assert first["status"] == "outcome_uncertain" and "retry_qualification" not in first
    assert gzip.decompress((tmp_path / first["response_path"]).read_bytes()) == r.EXACT_BODY


@pytest.mark.parametrize("case", ["predecessor", "policy", "source", "error_identity"])
def test_recovery_bindings_are_checked_before_post(tmp_path, monkeypatch, case):
    directory, _, clock, _ = ready(tmp_path, monkeypatch)
    path = directory / "freeze.json"
    source = read_json(path)
    if case == "predecessor":
        source["recovery"]["predecessor_receipt_sha256"] = "0" * 64
    elif case == "policy":
        source["recovery"]["policy"] = "retry anything"
    elif case == "source":
        source["inputs"] = [row for row in source["inputs"] if row["path"] != str(r.PROTOCOL)]
    else:
        source["recovery"]["qualifying_error"]["attempt"] = 2
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError):
        run(tmp_path, lambda _: pytest.fail("no live POST allowed"), clock)
