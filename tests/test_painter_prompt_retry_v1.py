"""Offline cap, provenance and numeric checks for the user-authorized two-request retry."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest

from latent_art_bench import painter_prompt_retry_v1 as retry
from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import publish
from latent_art_bench.painter_feature_generation_v2.statistics import finite_energy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / retry.generation.MANIFESTS / retry.SOURCE


def source():
    return read_jsonl(SOURCE / "requests.jsonl"), read_jsonl(SOURCE / "outputs.jsonl")


def test_select_exact_refusals_and_reject_changed_roster():
    requests, outputs = source()
    selected = retry.select_requests(requests, outputs)
    assert selected == [requests[415], requests[1718]]
    selected[0]["payload"]["prompt"] = "modified"
    assert requests[415]["payload"]["prompt"] != "modified"
    outputs[0]["status"] = "refused"
    with pytest.raises(ValueError, match="roster"):
        retry.select_requests(requests, outputs)


@pytest.fixture
def ready(tmp_path, monkeypatch):
    requests, outputs = source()
    freeze = read_json(SOURCE / "generation_freeze.json")
    freeze.update(requests=retry.select_requests(requests, outputs), inputs=[])
    publish(tmp_path / retry.DIRECTORY / "retry_freeze.json", freeze)
    monkeypatch.setattr(retry, "load", lambda root: (freeze, SOURCE))
    monkeypatch.setattr(retry.shutil, "disk_usage", lambda p: SimpleNamespace(free=100 * 1024**3))
    return tmp_path, freeze


def test_exact_two_dispatches_and_no_reexecution(ready):
    root, freeze = ready
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(
            400, stream=httpx.ByteStream(b'{"error":{"code":"moderation_blocked"}}')
        )

    transport = httpx.MockTransport(handler)
    receipt = retry.execute(root, transport=transport, sleep=lambda _: None)
    assert sent == [r["payload"] for r in freeze["requests"]]
    assert receipt["attempted"] == 2 and sum(receipt["statuses"].values()) == 2
    with pytest.raises(FileExistsError, match="one-shot"):
        retry.execute(root, transport=transport, sleep=lambda _: None)
    assert len(sent) == 2


@pytest.mark.parametrize("status", [401, 429])
def test_auth_or_quota_stops_second_call(ready, status):
    root, _ = ready
    sent = []

    def handler(request):
        sent.append(request)
        return httpx.Response(
            status, stream=httpx.ByteStream(b'{"error":{"code":"rate_limit_exceeded"}}')
        )

    receipt = retry.execute(root, transport=httpx.MockTransport(handler), sleep=lambda _: None)
    assert len(sent) == receipt["attempted"] == 1
    assert read_jsonl(root / retry.DIRECTORY / "outputs.jsonl")[1]["status"] == "not_attempted"


def test_uncertain_transport_stops_and_preserves_partial_body(ready):
    root, _ = ready
    sent = []

    def handler(request):
        sent.append(request)
        raise httpx.ReadTimeout("fixture interruption")

    retry.execute(root, transport=httpx.MockTransport(handler), sleep=lambda _: None)
    rows = read_jsonl(root / retry.DIRECTORY / "outputs.jsonl")
    assert len(sent) == 1 and rows[0]["outcome_uncertain"]
    assert rows[1]["status"] == "not_attempted"
    assert (root / rows[0]["response_path"]).is_file()


def test_interrupted_start_cannot_redispatch(ready):
    root, _ = ready
    retry.append_event(root / retry.DIRECTORY / "generation_events.jsonl", {"kind": "start"})
    with pytest.raises(FileExistsError, match="one-shot"):
        retry.execute(root, transport=httpx.MockTransport(lambda r: pytest.fail("dispatch")))


def test_combination_is_a_copy_and_only_fills_refused_slots():
    original = read_jsonl(SOURCE / "measured_features.jsonl")
    untouched = copy.deepcopy(original)
    retries = [dict(original[i], run_id=retry.RUN) for i in retry.SEQUENCES]
    retries[0].update(status="measured", values=[0.0] * 31)
    combined = retry.combine(original, retries)
    assert original == untouched
    assert sum(r["status"] == "measured" for r in combined) == 1919
    assert combined[415]["retried"] and combined[1718] == original[1718]
    retries[0]["request_id"] = original[0]["request_id"]
    with pytest.raises(ValueError, match="another slot"):
        retry.combine(original, retries)


def test_descriptive_engine_matches_independent_uniform_energy(tmp_path):
    requests, _ = source()
    rng = np.random.default_rng(325)
    rows = [dict(r, values=rng.normal(size=31).tolist(), status="measured") for r in requests]
    real = {p: rng.normal(size=(7, 31)) for p in retry.PAINTER_IDS}
    scaler = dict(center=[0.0] * 31, scale=[1.0] * 31)
    result = retry.describe(real, rows, scaler)
    assert len(result["distances"]) == 360 and len(result["contrasts"]) == 48
    assert len(result["absolute"]) == len(result["control_comparisons"]) == 72
    for row in result["distances"]:
        chosen = np.array(
            [
                r["values"]
                for r in rows
                if (r["alias"], r["method_id"], r["condition"])
                == (row["alias"], row["method_id"], row["condition"])
            ]
        )
        section = retry.features.FAMILIES[row["family"]]
        assert row["distance"] == pytest.approx(
            finite_energy(real[row["painter_id"]][:, section], chosen[:, section]), abs=2e-14
        )
    assert all("raw_p" not in r and "holm_p" not in r for r in result["contrasts"])
    result.update(measured=1920, retried_measured=2, changes=[])
    retry.render(result, tmp_path / "first")
    retry.render(result, tmp_path / "second")
    files = [
        p.relative_to(tmp_path / "first") for p in (tmp_path / "first").rglob("*") if p.is_file()
    ]
    assert len(files) == 9
    assert all(
        (tmp_path / "first" / p).read_bytes() == (tmp_path / "second" / p).read_bytes()
        for p in files
    )
