"""Synthetic/offline checks of assignment, inference, transport and replay boundaries."""

import base64
import copy
import io
import json
import shutil
import subprocess
import threading
import time
from collections import Counter
from pathlib import Path

import httpx
import numpy as np
import pytest
from PIL import Image
from scipy.spatial.distance import cdist
from scipy.stats import t

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import study
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, events
from latent_art_bench.painter_naming_replication_v1 import analysis, collection, common, workflow
from latent_art_bench.painter_prompt_study_v1.randomization import holm
from latent_art_bench.painter_responsiveness_v1.inference import analyze_factorial
from latent_art_bench.painter_responsiveness_v2 import common as old_palette

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def input_root(tmp_path):
    for path in (
        common.CONFIG,
        common.METADATA,
        study.CONFIG,
        old_palette.CONFIG,
        common.retained.MAIN / "scalers.json",
    ):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, tmp_path / path)
    return tmp_path


def synthetic(requests):
    rng = np.random.default_rng(2071)
    refs = []
    for painter, n in (("claude_monet", 38), ("paul_cezanne", 32)):
        for i in range(n):
            vector = rng.normal(size=31).tolist()
            for pipeline in study.PIPELINES:
                refs.append(
                    dict(
                        image_id=f"{painter}:{i}",
                        painter_id=painter,
                        pipeline=pipeline,
                        content_class=("water", "built", "land")[i % 3],
                        scaled=vector,
                        values=vector,
                        status="measured",
                    )
                )
    rows = []
    for request in requests:
        vector = rng.normal(size=31) + (4 if request["arm"] == "free" else 0)
        chroma = rng.normal() + (3 if request["polarity"] == "vivid" else 0)
        for pipeline in study.PIPELINES:
            rows.append(
                dict(
                    {k: v for k, v in request.items() if k != "payload"},
                    pipeline=pipeline,
                    values=vector.tolist(),
                    scaled=vector.tolist(),
                    chroma_primary_iqr=chroma,
                    status="measured",
                )
            )
    return refs, rows


@pytest.mark.parametrize("repetitions", [1, 4])
def test_exact_prompts_all_scenes_assignment_and_counts(input_root, repetitions):
    config = read_json(input_root / common.CONFIG)
    config.update(
        naming_repetitions=repetitions,
        maximum_images=192 + 72 * repetitions,
        maximum_attempts=200 + 72 * repetitions,
    )
    schedule = common.requests(input_root, config)
    assert len(schedule) == 192 + 72 * repetitions
    assert schedule == common.requests(input_root, config)
    assert len({r["request_id"] for r in schedule}) == len(schedule)
    assert [r["sequence"] for r in schedule] == list(range(len(schedule)))
    briefs = {b["brief_id"]: b for b in read_json(input_root / study.CONFIG)["briefs"]}
    for block in sorted({r["block_id"] for r in schedule}):
        rows = [r for r in schedule if r["block_id"] == block]
        assert [r["within_block"] for r in rows] == list(range(len(rows)))
        assert [r["sequence"] for r in rows] == list(
            range(rows[0]["sequence"], rows[0]["sequence"] + len(rows))
        )
        if rows[0]["experiment"] == "naming":
            assert {r["arm"] for r in rows} == {"free", "monet", "cezanne"}
            for row in rows:
                expected = study.prompt(
                    briefs[row["template_id"]],
                    common.PAINTERS.get(row["arm"], "claude_monet"),
                    "artist_free" if row["arm"] == "free" else "named",
                )
                assert row["payload"]["prompt"] == expected
    assert Counter(r["arm"] for r in schedule if r["experiment"] == "naming") == dict.fromkeys(
        ("free", "monet", "cezanne"), 24 * repetitions
    )
    assert len(common.palette_schedule(schedule)) == 192


def test_independent_energy_and_four_endpoint_inference(input_root):
    schedule = common.requests(input_root)
    refs, rows = synthetic(schedule)
    value = analysis.analyze(schedule, rows, refs, common.configuration(input_root))
    assert len(value["primary"]) == 4
    assert len(value["distributions"]) == 18
    summaries = {
        (r["painter_id"], r["arm"]): r
        for r in value["distributions"]
        if r["pipeline"] == "primary512"
    }
    for row in value["primary"][:2]:
        painter = row["painter_id"]
        arm = row["endpoint"].split("_")[1]
        own, free = summaries[painter, arm], summaries[painter, "free"]
        assert row["estimate"] == pytest.approx(own["energy_distance"] - free["energy_distance"])
        assert row["interval"] is None
        pieces = [c for c in value["naming_contributions"] if c["endpoint"] == row["endpoint"]]
        assert len(pieces) == 24
        assert sum(c["weight"] for c in pieces) == pytest.approx(1)
        x = np.array(
            [
                r["scaled"]
                for r in refs
                if r["painter_id"] == painter and r["pipeline"] == "primary512"
            ]
        )
        by_id = {r["request_id"]: r for r in rows if r["pipeline"] == "primary512"}
        y = np.array([by_id[c["named_id"]]["scaled"] for c in pieces])
        z = np.array([by_id[c["free_id"]]["scaled"] for c in pieces])
        w = np.array([c["weight"] for c in pieces])
        direct = 2 * (cdist(x, y).mean(axis=0) @ w - cdist(x, z).mean(axis=0) @ w)
        direct -= w @ cdist(y, y) @ w - w @ cdist(z, z) @ w
        assert direct == pytest.approx(row["estimate"])
    p = common.palette_schedule(schedule)
    by_id = {r["request_id"]: r for r in rows if r["pipeline"] == "primary512"}
    old = analyze_factorial(
        p,
        [
            dict(
                request_id=r["request_id"],
                status="measured",
                value=by_id[r["request_id"]]["chroma_primary_iqr"],
            )
            for r in p
        ],
    )
    assert old["primary_covariance"] == value["palette"]["primary512"]["primary_covariance"]
    for result, original in zip(value["primary"][2:], old["primary"], strict=True):
        assert result["raw_p"] == original["p_two_sided"]
        critical = t.ppf(1 - 0.05 / 8, original["welch_df"])
        assert result["interval"] == pytest.approx(
            [
                original["estimate"] - critical * original["standard_error"],
                original["estimate"] + critical * original["standard_error"],
            ]
        )
    assert [r["holm_p"] for r in value["primary"]] == pytest.approx(
        holm([r["raw_p"] for r in value["primary"]])
    )
    json.dumps(value)


@pytest.mark.parametrize("experiment,indexes", [("naming", (0, 1)), ("palette", (2, 3))])
def test_missing_component_preserves_other_and_family(input_root, experiment, indexes):
    schedule = common.requests(input_root)
    refs, rows = synthetic(schedule)
    chosen = next(r for r in rows if r["experiment"] == experiment)
    chosen.update(status="missing", values=None, scaled=None, chroma_primary_iqr=None)
    value = analysis.analyze(schedule, rows, refs, common.configuration(input_root))
    assert all(value["primary"][i]["raw_p"] is None for i in indexes)
    assert all(value["primary"][i]["holm_p"] == 1 for i in indexes)
    assert all(value["primary"][i]["raw_p"] is not None for i in set(range(4)) - set(indexes))


@pytest.mark.parametrize("failure", ["duplicate", "missing", "nan", "identity"])
def test_measurement_fail_closed(input_root, failure):
    schedule = common.requests(input_root)
    _, rows = synthetic(schedule)
    if failure == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif failure == "missing":
        rows.pop()
    elif failure == "nan":
        rows[0]["scaled"][0] = float("nan")
    else:
        rows[0]["arm"] = "changed"
    with pytest.raises(ValueError):
        analysis.validate_measurements(schedule, rows)


@pytest.mark.parametrize("header,expected", [(None, 60), ("120", 120), ("-5", 60)])
def test_retry_after_honored(header, expected):
    row = {"response_headers": {} if header is None else {"retry-after": header}}
    assert collection.retry_delay(row) == expected


@pytest.mark.parametrize("header", ["nonsense", "301", "nan"])
def test_unsupported_retry_after_stops(header):
    with pytest.raises(ValueError):
        collection.retry_delay({"response_headers": {"retry-after": header}})


def test_budget_reserves_pending_and_unknown_and_dynamic_worker(tmp_path):
    ledger = tmp_path / common.MANIFESTS / common.RUN_ID / "generation_events.jsonl"
    append_event(ledger, dict(kind="attempt", request_id="a", attempt=1, paid=True))
    b = collection.budget_state(tmp_path, 65.1)
    assert b["accounted_usd"] == pytest.approx(70.1)
    assert not collection.can_admit(b, True)
    assert collection.can_admit(b, False)
    append_event(ledger, dict(kind="terminal", request_id="a", attempt=1, cost_usd=0.07))
    b = collection.budget_state(tmp_path, 65.1)
    assert collection.can_admit(b, True)
    append_event(ledger, dict(kind="attempt", request_id="b", attempt=1, paid=True))
    append_event(ledger, dict(kind="terminal", request_id="b", attempt=1, cost_usd=None))
    b = collection.budget_state(tmp_path, 65.1)
    assert b["new_reserves_usd"] == 5
    assert b["unknown"]
    assert not collection.can_admit(b, True)


def image_body(alpha=255, cost=0.07):
    buf = io.BytesIO()
    Image.new("RGBA", (512, 512), (80, 120, 160, alpha)).save(buf, format="PNG")
    return json.dumps(
        dict(data=[dict(b64_json=base64.b64encode(buf.getvalue()).decode())], usage=dict(cost=cost))
    ).encode()


def test_container_opacity_and_known_error_rules():
    assert collection.inspect_response(image_body())["width"] == 512
    with pytest.raises(ValueError, match="transparent"):
        collection.inspect_response(image_body(alpha=0))
    assert collection.technical_error(
        collection.EXACT_BODY, 503, True, "text/plain", "oauth_gpt_image_2"
    )
    assert not collection.technical_error(
        collection.EXACT_BODY + b"\n", 503, True, "text/plain", "oauth_gpt_image_2"
    )
    assert not collection.technical_error(
        b'{"error":{"code":503,"message":"x"},"data":[]}',
        503,
        True,
        "application/json",
        "flux_2_max",
    )
    assert collection.technical_error(
        b'{"error":{"code":503,"message":"x"}}', 503, True, "application/json", "flux_2_max"
    )


@pytest.mark.parametrize("code", [400, 401, 402, 403, 404, 422])
def test_contract_status_stops(code):
    assert collection.stop_reason(dict(status="http_error", status_code=code, cost_usd=0), [])


def test_executor_stops_before_draining():
    stop, ready, observed = threading.Event(), threading.Event(), []

    def worker():
        ready.set()
        observed.append(stop.wait(1))

    with pytest.raises(KeyboardInterrupt):
        with collection.stopping_executor(stop) as executor:
            executor.submit(worker)
            assert ready.wait(1)
            raise KeyboardInterrupt
    assert observed == [True]


def test_start_gate_later_worker_arrives_first():
    stop = threading.Event()
    gate = collection.OrderedStartGate(stop, 0.01, time.monotonic() + 2)
    order = []
    arrived = threading.Event()

    def later_worker():
        arrived.set()
        stamp = gate(1)
        order.append((1, stamp))

    thread = threading.Thread(target=later_worker)
    thread.start()
    assert arrived.wait(1)
    first = gate(0)
    order.append((0, first))
    thread.join(1)
    assert not thread.is_alive()
    assert [i for i, _ in sorted(order, key=lambda row: row[1])] == [0, 1]
    assert dict(order)[1] - dict(order)[0] >= 0.01
    stop.set()
    assert gate(2) is None


def test_unselected_live_allocation_is_rejected(input_root):
    config = read_json(input_root / common.CONFIG)
    config.update(naming_repetitions=4, maximum_images=480, maximum_attempts=488)
    (input_root / common.CONFIG).write_text(json.dumps(config))
    with pytest.raises(ValueError, match="fixed allocation"):
        common.configuration(input_root)


def test_credit_gate_distinct_from_cumulative_reserve():
    budget = dict(new_reported_usd=4.2, terminal_reserves_usd=0, pending_paid=1)
    assert collection.can_credit_admit(budget, 4.34)
    assert not collection.can_credit_admit(budget, 4.33)
    budget["terminal_reserves_usd"] = 5
    assert not collection.can_credit_admit(budget, 9.31)


def test_start_gate_deadline_cancels_without_post():
    stop = threading.Event()
    gate = collection.OrderedStartGate(stop, 5, time.monotonic() - 1)
    assert gate(0) is None
    assert stop.is_set()


def test_duration_contract_reaches_primary_claims():
    value = dict(
        primary=[
            dict(
                endpoint="naming_monet",
                estimate=-1,
                raw_p=0.001,
                directional_replication=True,
                reject=True,
                holm_p=0.004,
                interval=[-2, -1],
                status="conditional_randomization",
            )
        ]
    )
    workflow.apply_collection_scope(value, dict(duration_contract_met=False))
    row = value["primary"][0]
    assert row["estimate"] == -1
    assert not row["directional_replication"] and not row["reject"]
    assert row["holm_p"] == 1 and row["raw_p"] is None and row["interval"] is None


@pytest.mark.parametrize("balance", [1, 10])
def test_credit_shortfall_and_queued_retry_not_reported_as_post(input_root, monkeypatch, balance):
    config = dict(common.configuration(input_root), minimum_start_interval_seconds=0)
    schedule = common.requests(input_root)
    freeze = dict(config=config, budget_baseline_usd=45.6819185, proxy_snapshot={})
    directory = input_root / common.directory(common.RUN_ID)
    directory.mkdir(parents=True)
    (directory / "freeze.json").write_text(json.dumps(freeze))
    monkeypatch.setattr(workflow, "verify", lambda *_: freeze)
    monkeypatch.setattr(workflow, "verify_live_metadata", lambda *_, **__: None)
    monkeypatch.setattr(collection.legacy, "proxy_snapshot", lambda _: {})
    monkeypatch.setattr(collection, "key_from_env", lambda _: "fixture-secret")
    calls = []
    second_started, retry_selected = threading.Event(), threading.Event()
    original_retry_delay = collection.retry_delay

    def observed_retry_delay(row):
        delay = original_retry_delay(row)
        retry_selected.set()
        return delay

    monkeypatch.setattr(collection, "retry_delay", observed_retry_delay)

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"total_credits": balance, "total_usage": 0}})
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            assert second_started.wait(3)
            return httpx.Response(503, json={"error": {"code": 503, "message": "temporary"}})
        second_started.set()
        assert retry_selected.wait(3)
        return httpx.Response(400, json={"error": {"code": 400, "message": "contract"}})

    if balance == 1:
        with pytest.raises(ValueError, match="credit balance"):
            collection.collect(
                input_root, common.RUN_ID, Path("unused"), transport=httpx.MockTransport(handle)
            )
        assert not calls
        assert not (directory / "generation_events.jsonl").exists()
    else:
        receipt = collection.collect(
            input_root, common.RUN_ID, Path("unused"), transport=httpx.MockTransport(handle)
        )
        assert receipt["status"] == "stopped"
        assert receipt["reason"] == "authentication_quota_or_contract_error"
        assert receipt["retry_decisions"] == 1
        assert receipt["retry_intents"] == receipt["retries"] == 0
        assert receipt["posted_attempts"] == 2
        assert sum(receipt["slot_counts"].values()) == len(schedule)


def test_staged_input_is_not_clean(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    path = tmp_path / "x.txt"
    path.write_text("old")
    subprocess.run(["git", "add", "x.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    path.write_text("new")
    subprocess.run(["git", "add", "x.txt"], cwd=tmp_path, check=True)
    path.write_text("old")
    with pytest.raises(ValueError, match="index"):
        workflow.clean_commit(tmp_path, [Path("x.txt")])


def test_full_mocked_collection_measurement_analysis_replay(input_root, monkeypatch):
    config = common.configuration(input_root)
    fast = dict(config, minimum_start_interval_seconds=0)
    schedule = common.requests(input_root)
    refs, _ = synthetic(schedule)
    freeze = dict(config=fast, budget_baseline_usd=45.6819185, proxy_snapshot={"fixture": True})
    directory = input_root / common.directory(common.RUN_ID)
    directory.mkdir(parents=True)
    (directory / "freeze.json").write_text(json.dumps(freeze))
    (directory / "planned_requests.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in schedule)
    )
    monkeypatch.setattr(workflow, "verify", lambda *_: freeze)
    monkeypatch.setattr(workflow, "verify_live_metadata", lambda *_, **__: None)
    monkeypatch.setattr(collection.legacy, "proxy_snapshot", lambda _: freeze["proxy_snapshot"])
    monkeypatch.setattr(collection, "key_from_env", lambda _: "fixture-secret")
    monkeypatch.setattr(workflow, "reference_rows", lambda _: refs)
    monkeypatch.setattr(workflow, "_historical", lambda _: dict(caveat="synthetic comparison"))

    def measured(_path, item, pipelines):
        seed = item["sequence"] + 55
        rng = np.random.default_rng(seed)
        vector = rng.normal(size=31) + (3 if item["arm"] == "free" else 0)
        return [
            dict(item, pipeline=p, values=vector.tolist(), status="measured") for p in pipelines
        ]

    monkeypatch.setattr(workflow, "measure_path", measured)
    calls = []

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"data": {"total_credits": 50, "total_usage": 40}})
        calls.append((request.url.host, json.loads(request.content)))
        return httpx.Response(
            200, content=image_body(), headers={"content-type": "application/json"}
        )

    receipt = collection.collect(
        input_root, common.RUN_ID, Path("unused"), transport=httpx.MockTransport(handle)
    )
    assert receipt["status"] == "complete"
    assert receipt["attempts"] == 264
    assert len(calls) == 264
    assert receipt["budget"]["accounted_usd"] == pytest.approx(45.6819185 + 72 * 0.07)
    ledger = events(directory / "generation_events.jsonl")
    assert all(r.get("post_started_at_utc") for r in ledger if r["kind"] == "terminal")
    assert workflow.measure(input_root, common.RUN_ID)["status"] == "measured_and_reported"
    assert workflow.check(input_root, common.RUN_ID)["status"] == "numbers_replayed"
    assert workflow.verify_responses(input_root, common.RUN_ID)["checked"] == 264
    assert (
        workflow.check(input_root, common.RUN_ID, pixels=True)["status"]
        == "pixels_and_numbers_replayed"
    )
    with pytest.raises(ValueError, match="already started"):
        collection.collect(
            input_root, common.RUN_ID, Path("unused"), transport=httpx.MockTransport(handle)
        )
    vector_path = directory / "measurements.jsonl"
    vector_path.write_text(vector_path.read_text() + "\n")
    with pytest.raises(ValueError, match="bound input changed"):
        workflow.check(input_root, common.RUN_ID)
