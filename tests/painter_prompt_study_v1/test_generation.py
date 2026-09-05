"""Offline transport accounting tests; real grid coverage is tested separately from tiny runs."""

import base64
import copy
import gzip
import hashlib
import importlib.metadata
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import digest, events, publish
from latent_art_bench.painter_prompt_study_v1 import design
from latent_art_bench.painter_prompt_study_v1 import generation as gen
from latent_art_bench.painter_prompt_study_v1.prompts import (
    CONDITIONS,
    METHOD_IDS,
    TEMPLATE_IDS,
    build_library,
)

REPO = Path(__file__).resolve().parents[2]
RUN = "transport-fixture"


def config(**updates):
    value = dict(
        repetitions=4, aliases=list(gen.ALIASES), method_ids=list(METHOD_IDS),
        maximum_requests=1920, base_url=gen.BASE, order_seed=20260905,
        maximum_response_bytes=gen.MAX_RESPONSE_BYTES, max_runtime_bytes=1024**3,
        reserve_disk_bytes=gen.RESERVE_DISK_BYTES, timeout_seconds=240,
        minimum_start_interval_seconds=15, minimum_decoded_short_side=512, **gen.RENDER,
        approved_maximum_requests=1920, authorization="Explicit offline fixture authorization",
        paid_fallback=False, primary_estimator="paired_randomization", simultaneous_alpha=.05,
        permutation_seed=20260906, permutation_draws=99999, multiplicity="holm",
        calibration_id="offline-calibration-fixture",
    )
    return dict(value, **updates)


@pytest.fixture
def library():
    return build_library(REPO)


@pytest.fixture
def image_response():
    handle = io.BytesIO()
    Image.new("RGB", (512, 512), "#aabbcc").save(handle, format="PNG")
    return json.dumps(dict(
        data=[dict(b64_json=base64.b64encode(handle.getvalue()).decode())],
        quality="low", size="512x512", output_format="png", background="opaque",
    )).encode()


@pytest.fixture
def prepared(tmp_path, monkeypatch, library):
    settings = config()
    # Exact 1,920-cell construction is tested below. A three-request frozen fixture keeps
    # transport fault tests small; production execute still requires exact regenerated grids.
    requests = gen.request_grid(settings, library)[:3]
    monkeypatch.setattr(gen, "request_grid", lambda _config, _library: copy.deepcopy(requests))
    monkeypatch.setattr(gen.shutil, "disk_usage", lambda _root: SimpleNamespace(free=100 * 1024**3))
    monkeypatch.setattr(design, "validate_study_calibration", lambda _root, _config: dict(
        primary_estimator="paired_randomization", simultaneous_alpha=.05,
        qualified_repetitions=[1, 2, 4],
        uses_empirical_outcomes_for_tuning=False,
    ))
    # These tiny transport fixtures are not repositories. Commit verification is tested
    # separately; working-file/config/grid binding and all transport accounting stay real.
    monkeypatch.setattr(gen, "_verify_commit", lambda *_: None)
    directory = tmp_path / gen.MANIFESTS / RUN
    directory.mkdir(parents=True)
    (tmp_path / "bound.txt").write_text("immutable fixture input")
    config_path = "fixture-config.json"
    publish(tmp_path / config_path, settings)
    publish(directory / "prompts.json", library)
    publish(directory / "requests.jsonl", requests, lines=True)
    freeze = dict(
        run_id=RUN, config=settings, config_path=config_path, recorded_git_commit="a" * 40,
        inputs=[dict(path="bound.txt", sha256=hash_file(tmp_path / "bound.txt")),
                dict(path=config_path, sha256=hash_file(tmp_path / config_path))],
        requests_sha256=hash_file(directory / "requests.jsonl"),
        library_sha256=hash_file(directory / "prompts.json"),
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
    )
    publish(directory / "generation_freeze.json", freeze)
    return SimpleNamespace(root=tmp_path, directory=directory, config=settings,
                           freeze=freeze, requests=requests)


def transport_for(body, *, status=200, seen=None):
    def handle(request):
        assert str(request.url) == gen.BASE + "/v1/images/generations"
        assert "authorization" not in request.headers
        assert request.headers["accept-encoding"] == "identity"
        if seen is not None:
            seen.append(json.loads(request.content))
        return httpx.Response(status, stream=httpx.ByteStream(body),
                              headers={"content-type": "application/json", "date": "fixture-date"})
    return httpx.MockTransport(handle)


def run(prepared, transport, **kwargs):
    return gen.execute(prepared.root, RUN, transport=transport, sleep=lambda _: None, **kwargs)


def replace_fixture_configuration(prepared, **updates):
    """Establish the intended fixture contract consistently before starting any request."""
    prepared.freeze["config"].update(updates)
    source = prepared.root / prepared.freeze["config_path"]
    source.write_text(json.dumps(prepared.freeze["config"]))
    for record in prepared.freeze["inputs"]:
        if record["path"] == prepared.freeze["config_path"]:
            record["sha256"] = hash_file(source)
    (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))


def raw_body(prepared, row):
    path = prepared.root / row["response_path"]
    assert hash_file(path) == row["stored_sha256"]
    with gzip.open(path, "rb") as handle:
        raw = handle.read()
    assert hashlib.sha256(raw).hexdigest() == row["response_sha256"]
    return raw


def test_full_grid_covers_every_literal_in_each_chronological_block(library):
    settings = config()
    rows = gen.request_grid(settings, library)
    assert len(rows) == len({r["request_id"] for r in rows}) == 1920
    assert rows == gen.request_grid(settings, library)
    assert [r["sequence"] for r in rows] == list(range(1920))
    assert [r["block"] for r in rows] == sorted(r["block"] for r in rows)
    expected = {(a, m, t, c) for a in gen.ALIASES for m in METHOD_IDS
                for t in TEMPLATE_IDS for c in CONDITIONS}
    prompt_map = {(r["method_id"], r["template_id"], r["condition"]): r["prompt"]
                  for r in library["prompts"]}
    for block in range(4):
        subset = [r for r in rows if r["block"] == block]
        assert {(r["alias"], r["method_id"], r["template_id"], r["condition"])
                for r in subset} == expected
        for row in subset:
            literal = prompt_map[row["method_id"], row["template_id"], row["condition"]]
            assert row["payload"] == dict(gen.RENDER, model=row["alias"], prompt=literal, n=1)
    reordered = copy.deepcopy(library)
    reordered["prompts"].reverse()
    assert rows == gen.request_grid(settings, reordered)


@pytest.mark.parametrize("change", [
    {"repetitions": 3}, {"repetitions": True}, {"maximum_requests": 100},
    {"base_url": "https://api.openai.com"}, {"aliases": ["gpt-image-2", "gpt-image-1"]},
    {"minimum_start_interval_seconds": 0}, {"minimum_start_interval_seconds": float("nan")},
    {"timeout_seconds": 241}, {"timeout_seconds": True}, {"maximum_response_bytes": 2**30},
    {"reserve_disk_bytes": 0}, {"size": "auto"}, {"quality": "high"},
    {"primary_estimator": "paired_t"},
])
def test_grid_rejects_changed_transport_contract(library, change):
    with pytest.raises(ValueError):
        gen.request_grid(config(**change), library)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "prompt", "hash"])
def test_grid_rejects_incomplete_or_changed_prompt_library(library, mutation):
    if mutation == "missing":
        library["prompts"].pop()
    elif mutation == "duplicate":
        library["prompts"].append(library["prompts"][0])
    elif mutation == "prompt":
        library["prompts"][0]["prompt"] += " Extra words."
    else:
        library["prompts"][0]["prompt_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        gen.request_grid(config(), library)


def test_complete_retains_exact_gzip_once_without_decoded_copies(prepared, image_response):
    seen = []
    result = run(prepared, transport_for(image_response, seen=seen))
    assert result["terminal"] and result["complete_generated_grid"]
    assert result["statuses"] == {"generated": 3}
    assert seen == [r["payload"] for r in prepared.requests]
    rows = read_jsonl(prepared.directory / "outputs.jsonl")
    assert all(raw_body(prepared, row) == image_response for row in rows)
    assert all(row["reported"]["quality"] == "low" for row in rows)
    assert all(row["model_snapshot_independently_verified"] is False for row in rows)
    assert all("decoded_size" in row["requested_returned_mismatches"] for row in rows)
    paths = [p for p in (prepared.root / gen.WORKSPACE / RUN).rglob("*") if p.is_file()]
    assert len(paths) == 2  # One lock, one compressed response; no duplicate decoded image.
    assert raw_body(prepared, rows[0]) == image_response
    assert (prepared.root / rows[0]["response_path"]).read_bytes()[4:8] == b"\0\0\0\0"
    assert gen.status(prepared.root, RUN) == result
    with pytest.raises(FileExistsError, match="permanently terminal"):
        run(prepared, transport_for(image_response))


def test_batches_resume_only_never_attempted_requests(prepared, image_response):
    seen = []
    transport = transport_for(image_response, seen=seen)
    for count in (1, 2):
        result = run(prepared, transport, max_new_requests=1)
        assert result["status"] == "paused_batch_limit" and not result["terminal"]
        assert result["image_attempts"] == count
        assert not (prepared.directory / "generation_receipt.json").exists()
    result = run(prepared, transport, max_new_requests=1)
    assert result["terminal"] and result["image_attempts"] == 3
    assert seen == [r["payload"] for r in prepared.requests]
    assert len([r for r in events(prepared.directory / "generation_events.jsonl")
                if r["kind"] == "attempt"]) == 3


@pytest.mark.parametrize("status_code,payload,outcome", [
    (401, {"error": {"message": "expired"}}, "authentication_blocked"),
    (403, {"error": {"message": "permission denied"}}, "authentication_blocked"),
    (429, {"error": {"code": "rate_limit_exceeded"}}, "quota_or_rate_limited"),
])
def test_authentication_and_quota_close_all_remaining_without_sending(
    prepared, status_code, payload, outcome,
):
    seen = []
    body = json.dumps(payload).encode()
    result = run(prepared, transport_for(body, status=status_code, seen=seen))
    assert result["terminal"] and result["stopped_on"] == outcome
    assert result["statuses"] == {outcome: 1, "not_attempted": 2}
    assert result["image_attempts"] == len(seen) == 1
    assert raw_body(prepared, read_jsonl(prepared.directory / "outputs.jsonl")[0]) == body


def test_refusal_is_accounted_once_and_other_cells_are_attempted(prepared):
    body = json.dumps({"error": {"code": "moderation_blocked"}}).encode()
    seen = []
    result = run(prepared, transport_for(body, status=403, seen=seen))
    assert result["terminal"] and result["image_attempts"] == len(seen) == 3
    assert result["statuses"] == {"refused": 3}
    assert not result["complete_generated_grid"]


@pytest.mark.parametrize("status_code,outcome", [
    (401, "authentication_blocked"), (403, "authentication_blocked"),
    (429, "quota_or_rate_limited"),
])
def test_non_json_auth_or_quota_error_still_stops_dispatch(prepared, status_code, outcome):
    result = run(prepared, transport_for(b"<html>blocked</html>", status=status_code))
    assert result["terminal"] and result["image_attempts"] == 1
    assert result["stopped_on"] == outcome


class BrokenStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b'{"data":['
        raise httpx.ReadError("lost socket")


def test_partial_response_prefix_is_retained_and_not_retried(prepared):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(200, stream=BrokenStream())

    result = run(prepared, httpx.MockTransport(handle), max_new_requests=1)
    assert result["terminal"] and result["stopped_on"] == "outcome_uncertain"
    assert result["statuses"] == {"transport_failure": 1, "not_attempted": 2}
    assert len(calls) == 1
    terminal = [r for r in events(prepared.directory / "generation_events.jsonl")
                if r["kind"] == "terminal"][0]
    assert terminal["partial_body"] and terminal["outcome_uncertain"]
    assert terminal["status"] == "transport_failure"
    assert raw_body(prepared, terminal) == b'{"data":['


def test_durable_intent_precedes_transport_and_interruption_closes_run(prepared):
    seen = []

    def crash(request):
        seen.append(request)
        rows = events(prepared.directory / "generation_events.jsonl")
        assert rows[-1]["kind"] == "attempt"
        assert rows[-1]["request_sha256"] == digest(prepared.requests[0])
        assert gen.status(prepared.root, RUN)["status"] == "in_flight_or_interrupted"
        raise KeyboardInterrupt("simulated abrupt operator interruption")

    with pytest.raises(KeyboardInterrupt):
        run(prepared, httpx.MockTransport(crash))
    assert gen.status(prepared.root, RUN)["status"] == "in_flight_or_interrupted"

    def forbidden(_request):
        pytest.fail("an interrupted request must never be resent")

    result = run(prepared, httpx.MockTransport(forbidden))
    assert len(seen) == 1 and result["image_attempts"] == 1
    assert result["terminal"] and result["stopped_on"] == "outcome_uncertain"
    assert result["statuses"] == {"outcome_uncertain": 1, "not_attempted": 2}


@pytest.mark.parametrize("reason", ["disk", "runtime"])
def test_resource_preflight_pauses_before_any_attempt(prepared, monkeypatch, reason):
    if reason == "disk":
        monkeypatch.setattr(gen.shutil, "disk_usage", lambda _: SimpleNamespace(free=0))
    else:
        # The fixture freeze deliberately starts with a cap too small for a worst-case response.
        replace_fixture_configuration(prepared, max_runtime_bytes=1000)
    result = run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not result["terminal"] and result["image_attempts"] == 0
    assert result["status"] == ("paused_disk_reserve" if reason == "disk"
                                else "paused_runtime_budget")
    assert not (prepared.directory / "generation_events.jsonl").exists()
    assert not (prepared.directory / "generation_receipt.json").exists()


def test_response_ceiling_retains_prefix_then_terminalizes_remainder(prepared):
    replace_fixture_configuration(prepared, maximum_response_bytes=64)
    result = run(prepared, transport_for(b"x" * 80))
    assert result["terminal"] and result["stopped_on"] == "resource_ceiling"
    assert result["image_attempts"] == 1
    row = read_jsonl(prepared.directory / "outputs.jsonl")[0]
    assert row["partial_body"] and row["bytes"] == 64
    assert raw_body(prepared, row) == b"x" * 64


def test_changed_retained_bytes_block_resume(prepared, image_response):
    run(prepared, transport_for(image_response), max_new_requests=1)
    row = [r for r in events(prepared.directory / "generation_events.jsonl")
           if r["kind"] == "terminal"][0]
    (prepared.root / row["response_path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="compressed response changed"):
        run(prepared, transport_for(image_response))


def test_changed_bound_input_prevents_dispatch(prepared):
    (prepared.root / "bound.txt").write_text("changed fixture")
    with pytest.raises(ValueError, match="bound input changed"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))


def test_inconsistent_receipt_counts_fail_read_only_status(prepared, image_response):
    run(prepared, transport_for(image_response))
    path = prepared.directory / "generation_receipt.json"
    receipt = read_json(path)
    receipt["image_attempts"] = 1
    path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="terminal generation evidence changed"):
        gen.status(prepared.root, RUN)


def test_status_and_zero_batch_are_offline_without_attempt_intent(prepared):
    before = sorted(p.relative_to(prepared.root) for p in prepared.root.rglob("*") if p.is_file())
    assert gen.status(prepared.root, RUN)["status"] == "ready"
    after = sorted(p.relative_to(prepared.root) for p in prepared.root.rglob("*") if p.is_file())
    assert before == after
    result = run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")),
                 max_new_requests=0)
    assert result["status"] == "paused_batch_limit" and result["image_attempts"] == 0


def test_append_writer_verifies_chain_once_per_execution(prepared, image_response, monkeypatch):
    actual = gen.events
    calls = []

    def counted(path):
        calls.append(path)
        return actual(path)

    monkeypatch.setattr(gen, "events", counted)
    run(prepared, transport_for(image_response))
    assert len(calls) == 1


def test_runtime_boundary_can_be_on_external_mount(prepared, image_response, monkeypatch, tmp_path):
    external = tmp_path / "external-drive"
    external.mkdir()
    boundary = prepared.root / gen.WORKSPACE
    boundary.parent.mkdir(parents=True, exist_ok=True)
    boundary.symlink_to(external, target_is_directory=True)
    checked = []

    def disk_usage(path):
        checked.append(Path(path).resolve())
        return SimpleNamespace(free=100 * 1024**3)

    monkeypatch.setattr(gen.shutil, "disk_usage", disk_usage)
    result = run(prepared, transport_for(image_response))
    assert result["complete_generated_grid"]
    assert checked == [external / RUN] * 3
    rows = read_jsonl(prepared.directory / "outputs.jsonl")
    assert raw_body(prepared, rows[0]) == image_response
    assert rows[0]["response_path"].startswith(gen.WORKSPACE.as_posix())


@pytest.mark.parametrize("change", [
    {"approved_maximum_requests": 0}, {"approved_maximum_requests": 1919},
    {"authorization": None}, {"authorization": " "}, {"paid_fallback": True},
])
def test_execution_rejects_unapproved_freeze_even_with_mock_transport(prepared, change):
    replace_fixture_configuration(prepared, **change)
    with pytest.raises(ValueError):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.root / gen.WORKSPACE).exists()
    assert not (prepared.directory / "generation_events.jsonl").exists()


@pytest.mark.parametrize("change", [
    {"qualified_repetitions": []}, {"primary_estimator": "jackknife_t"},
    {"simultaneous_alpha": .025}, {"uses_empirical_outcomes_for_tuning": True},
])
def test_execution_rechecks_prospective_calibration(prepared, monkeypatch, change):
    decision = dict(primary_estimator="paired_randomization", simultaneous_alpha=.05,
                    qualified_repetitions=[4], uses_empirical_outcomes_for_tuning=False)
    decision.update(change)
    monkeypatch.setattr(design, "validate_study_calibration", lambda *_: decision)
    with pytest.raises(ValueError, match="qualified prospective calibration"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.directory / "generation_events.jsonl").exists()


def test_live_execution_requires_explicit_proxy_checkout_before_creating_workspace(prepared):
    with pytest.raises(ValueError, match="explicitly bound proxy source"):
        gen.execute(prepared.root, RUN, sleep=lambda _: None)
    assert not (prepared.root / gen.WORKSPACE).exists()


def test_live_listener_replacement_stops_before_next_intent(prepared, monkeypatch, image_response):
    seen, checks = [], []
    actual_client = httpx.Client

    def mocked_client(**kwargs):
        kwargs["transport"] = transport_for(image_response, seen=seen)
        return actual_client(**kwargs)

    def verify(_freeze, proxy_root, *, verify_commit=True):
        assert proxy_root == prepared.root / "proxy-fixture"
        checks.append(verify_commit)
        if len(checks) == 3:
            raise ValueError("proxy listener identity changed")

    monkeypatch.setattr(gen.httpx, "Client", mocked_client)
    monkeypatch.setattr(gen, "_verify_proxy", verify)
    with pytest.raises(ValueError, match="proxy listener identity changed"):
        gen.execute(prepared.root, RUN, proxy_root=prepared.root / "proxy-fixture",
                    sleep=lambda _: None)
    assert checks == [True, False, False]
    assert len(seen) == 1
    journal = events(prepared.directory / "generation_events.jsonl")
    assert [r["kind"] for r in journal] == ["attempt", "terminal"]
    assert not (prepared.directory / "generation_receipt.json").exists()


def test_freeze_changed_during_spacing_is_rejected_before_attempt(prepared, image_response):
    def changed(_duration):
        prepared.freeze["config"]["authorization"] = None
        (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))

    with pytest.raises(ValueError, match="freeze changed before dispatch"):
        gen.execute(prepared.root, RUN, transport=transport_for(image_response), sleep=changed)
    assert not (prepared.directory / "generation_events.jsonl").exists()


def test_proxy_identity_records_only_portable_noncredential_process_fields(tmp_path, monkeypatch):
    calls = []
    source = tmp_path / "packages/openai-oauth"
    source.mkdir(parents=True)

    def process(arguments):
        calls.append(arguments)
        if arguments[0] == "lsof" and "-iTCP:10532" in arguments:
            return "p123\nn127.0.0.1:10532"
        if arguments[0] == "lsof":
            return f"p123\nn{source}"
        return "Sat Sep  5 01:05:53 2026" if arguments[-1] == "lstart=" else "/runtime/bun"

    monkeypatch.setattr(gen, "_process_output", process)
    identity = gen.proxy_identity(tmp_path)
    assert identity == dict(pid=123, started_utc="Sat Sep  5 01:05:53 2026", executable="bun",
                            address="127.0.0.1", port=10532,
                            source_directory="packages/openai-oauth")
    assert all("args" not in " ".join(c) and "command" not in " ".join(c) for c in calls)
    assert str(tmp_path) not in json.dumps(identity)


@pytest.mark.parametrize("listing", ["p123\nn*:10532", "p123\nn[::1]:10532",
                                      "p123\nn127.0.0.1:10532\np456\nn127.0.0.1:10532"])
def test_proxy_identity_rejects_nonexclusive_or_nonloopback_listener(
    tmp_path, monkeypatch, listing,
):
    monkeypatch.setattr(gen, "_process_output", lambda _: listing)
    with pytest.raises(ValueError, match="one IPv4 loopback-only"):
        gen.proxy_identity(tmp_path)


def test_proxy_verifies_source_bytes_commit_and_listener(tmp_path, monkeypatch):
    from latent_art_bench.painter_prompt_study_v1.design import PROXY_BINDINGS

    records = []
    for name in PROXY_BINDINGS:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("bound proxy code")
        records.append(dict(path=name, sha256=hash_file(path)))
    listener = dict(pid=123, started_utc="fixture")
    freeze = dict(proxy_source=dict(repository="openai-oauth", files=records,
                                    recorded_git_commit="a" * 40, listener=listener))
    commits = []
    monkeypatch.setattr(gen, "proxy_identity", lambda _: listener)
    monkeypatch.setattr(gen, "_verify_commit", lambda *args: commits.append(args))
    gen._verify_proxy(freeze, tmp_path)
    assert commits == [(tmp_path, "a" * 40, records)]
    monkeypatch.setattr(gen, "proxy_identity", lambda _: dict(listener, pid=456))
    with pytest.raises(ValueError, match="listener identity changed"):
        gen._verify_proxy(freeze, tmp_path, verify_commit=False)
    (tmp_path / records[0]["path"]).write_text("changed proxy code")
    with pytest.raises(ValueError, match="bound input changed"):
        gen._verify_proxy(freeze, tmp_path, verify_commit=False)


def randomization_config(repetitions=4, **updates):
    value = config(repetitions=repetitions, maximum_requests=480 * repetitions)
    return dict(value, **updates)


@pytest.mark.parametrize("repetitions", [1, 2, 4])
def test_small_grid_has_complete_independent_method_triplets(library, repetitions):
    settings = randomization_config(repetitions)
    rows = gen.request_grid(settings, library)
    assert len(rows) == len({r["request_id"] for r in rows}) == 480 * repetitions
    assert rows == gen.request_grid(settings, library)
    reordered = copy.deepcopy(library)
    reordered["prompts"].reverse()
    assert rows == gen.request_grid(settings, reordered)
    assert [r["sequence"] for r in rows] == list(range(len(rows)))
    units, permutations = {}, set()
    for start in range(0, len(rows), 3):
        triplet = rows[start:start + 3]
        assert len({r["assignment_unit_id"] for r in triplet}) == 1
        assert len({(r["block"], r["alias"], r["condition"], r["template_id"])
                    for r in triplet}) == 1
        assert [r["method_position"] for r in triplet] == [0, 1, 2]
        assert {r["method_id"] for r in triplet} == set(METHOD_IDS)
        assert [r["treatment_position"] for r in triplet] == [
            triplet[0]["alias_position"] * 3 + k for k in range(3)]
        unit = triplet[0]["assignment_unit_id"]
        assert unit not in units
        units[unit] = triplet
        permutations.add(tuple(r["method_id"] for r in triplet))
        assert all(r["payload"] == dict(gen.RENDER, model=r["alias"], prompt=r["prompt"], n=1)
                   for r in triplet)
        assert all(gen._identity(r)["assignment_unit_id"] == unit for r in triplet)
    assert len(units) == 160 * repetitions
    # The fixed seed exercises all six assignments, including both conditional swaps
    # with each possible third-method slot; a cyclic-only or coupled design fails this.
    assert len(permutations) == 6
    for start in range(0, len(rows), 6):
        cell = rows[start:start + 6]
        assert len({(r["block"], r["condition"], r["template_id"], r["cell_position"])
                    for r in cell}) == 1
        assert {r["alias"] for r in cell} == set(gen.ALIASES)
        assert [r["alias_position"] for r in cell] == [0, 0, 0, 1, 1, 1]


def test_randomization_uses_separate_uniform_draw_for_every_method_triplet(library, monkeypatch):
    actual = np.random.Generator
    draws = []

    class RecordingGenerator:
        def __init__(self, bit_generator):
            self.generator = actual(bit_generator)

        def permutation(self, count):
            draws.append(count)
            return self.generator.permutation(count)

    monkeypatch.setattr(gen.np.random, "Generator", RecordingGenerator)
    gen.request_grid(randomization_config(2), library)
    assert draws == ([80] + [2, 3, 3] * 80) * 2


def test_new_seed_changes_assignment_order_but_preserves_complete_population(library):
    settings = randomization_config(2)
    first = gen.request_grid(settings, library)
    settings["order_seed"] += 1
    second = gen.request_grid(settings, library)
    assert {r["request_id"] for r in first} == {r["request_id"] for r in second}
    assert [r["request_id"] for r in first] != [r["request_id"] for r in second]
    first_positions = {r["assignment_unit_id"]: [] for r in first}
    for row in first:
        first_positions[row["assignment_unit_id"]].append(row["method_id"])
    # Adjacent repetitions are independently drawn, not reversed or otherwise tied.
    paired = [(value, first_positions[key.replace("b0000-", "b0001-", 1)])
              for key, value in first_positions.items() if key.startswith("b0000-")]
    assert any(first != list(reversed(second)) for first, second in paired)


@pytest.mark.parametrize("value", [None, True, -1, 1.5, "20260905"])
def test_small_randomization_requires_explicit_integer_order_seed(library, value):
    settings = randomization_config()
    settings["order_seed"] = value
    with pytest.raises(ValueError, match="integer seed"):
        gen.request_grid(settings, library)


def test_small_randomization_execution_uses_selected_calibration_gate(
    prepared, monkeypatch, image_response,
):
    replace_fixture_configuration(prepared, **randomization_config())
    checked = []

    def calibration(_root, settings):
        checked.append(settings["primary_estimator"])
        return dict(primary_estimator="paired_randomization", simultaneous_alpha=.05,
                    qualified_repetitions=[1, 2, 4], uses_empirical_outcomes_for_tuning=False)

    monkeypatch.setattr(design, "validate_study_calibration", calibration)
    assert run(prepared, transport_for(image_response))["complete_generated_grid"]
    assert checked == ["paired_randomization", "paired_randomization"]


def test_embedded_configuration_cannot_override_bound_source(prepared):
    prepared.freeze["config"]["max_runtime_bytes"] += 1
    (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))
    with pytest.raises(ValueError, match="embedded configuration differs"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.root / gen.WORKSPACE).exists()


@pytest.mark.parametrize("path", [None, "", "../outside.json", "/outside.json",
                                   "directory\\config.json", "./fixture-config.json"])
def test_configuration_path_must_be_portable_and_bound(prepared, path):
    prepared.freeze["config_path"] = path
    (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))
    with pytest.raises(ValueError, match="portable"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.root / gen.WORKSPACE).exists()


@pytest.mark.parametrize("copies", [0, 2])
def test_configuration_must_have_exactly_one_source_binding(prepared, copies):
    record = next(r for r in prepared.freeze["inputs"]
                  if r["path"] == prepared.freeze["config_path"])
    prepared.freeze["inputs"] = [r for r in prepared.freeze["inputs"] if r != record]
    prepared.freeze["inputs"] += [record] * copies
    (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))
    with pytest.raises(ValueError, match="exactly one"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))


def test_configuration_symlink_cannot_escape_repository(prepared, tmp_path_factory):
    source = prepared.root / prepared.freeze["config_path"]
    external = tmp_path_factory.mktemp("external-configuration") / "config.json"
    external.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(external)
    with pytest.raises(ValueError):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.root / gen.WORKSPACE).exists()


def test_configuration_byte_hash_remains_bound_even_when_json_values_match(prepared):
    source = prepared.root / prepared.freeze["config_path"]
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="bound input changed"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))


def test_rebinding_changed_config_cannot_bypass_recorded_commit(prepared, monkeypatch):
    from latent_art_bench.painter_prompt_study_v1.calibration_record import _verify_commit

    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=prepared.root, text=True).strip()

    git("init", "--quiet")
    git("add", "--", "bound.txt", prepared.freeze["config_path"])
    git("-c", "user.name=Offline Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "--quiet", "-m", "Commit prospective fixture inputs")
    prepared.freeze["recorded_git_commit"] = git("rev-parse", "HEAD")
    (prepared.directory / "generation_freeze.json").write_text(json.dumps(prepared.freeze))
    monkeypatch.setattr(gen, "_verify_commit", _verify_commit)
    assert gen.status(prepared.root, RUN)["status"] == "ready"
    # The embedded/current configuration and its byte hash now agree with each other,
    # but no longer match the prospective commit. A refreshed hash cannot repair that.
    replace_fixture_configuration(
        prepared, max_runtime_bytes=prepared.config["max_runtime_bytes"] + 1)
    with pytest.raises(ValueError, match="commit-bound calibration code mismatch"):
        run(prepared, httpx.MockTransport(lambda _: pytest.fail("must not send")))
    assert not (prepared.directory / "generation_events.jsonl").exists()
