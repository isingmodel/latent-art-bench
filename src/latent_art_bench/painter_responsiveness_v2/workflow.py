"""Commit-bound prospective collection, all-slot measurement and offline replay."""

from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.metadata
import json
import math
import platform
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_revision_v1.analysis import source_paths as prior_paths
from latent_art_bench.painter_distribution_study_v1.measurement import measure_path
from latent_art_bench.painter_distribution_study_v1.study import PIPELINES
from latent_art_bench.painter_distribution_study_v1.transport import (
    inspect_response,
    proxy_snapshot,
)
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    confined,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_responsiveness_v1 import inference
from latent_art_bench.painter_responsiveness_v1.collection import _slot_outcomes

from . import analysis, common, diagnostics, report

RUNTIME = ("numpy", "scipy", "Pillow", "matplotlib", "httpx", "PyWavelets", "scikit-image")


def source_paths(root):
    paths = set(prior_paths(root))
    paths.update(p.relative_to(root) for p in (root / common.PACKAGE).glob("*") if p.is_file())
    paths.update(p.relative_to(root) for p in root.glob("tests/painter_responsiveness_v2/*.py"))
    paths.update(p.relative_to(root) for p in (root / common.STUDIES).glob("*.md"))
    paths.update(
        Path("src/latent_art_bench/painter_responsiveness_v1") / name
        for name in ("collection.py", "common.py", "design.py", "inference.py")
    )
    paths.update((common.CONFIG, Path("docs/RESEARCH_IDEA_20260908.md")))
    predecessor = Path("data/manifests/painter_responsiveness_v1/prv1-diagnostic-20260908")
    paths.update(predecessor / name for name in ("freeze.json", "analysis_receipt.json"))
    return sorted(paths)


def prepare(root, run_id, proxy_root):
    directory = root / common.directory(run_id)
    if directory.exists():
        raise ValueError("run namespace already exists; never prepare over a retained run")
    config = common.configuration(root)
    paths = source_paths(root)
    commit = committed(root, paths)
    proxy = proxy_snapshot(proxy_root)
    publish(directory / "planned_requests.jsonl", common.requests(config), lines=True)
    freeze = dict(
        schema="painter-responsiveness-freeze/2",
        run_id=run_id,
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        config=config,
        proxy_snapshot=proxy,
        requests_sha256=hash_file(directory / "planned_requests.jsonl"),
        environment=dict(
            python=platform.python_version(),
            **{name: importlib.metadata.version(name) for name in RUNTIME},
        ),
        scope="User-authorized computational-only OAuth study; no human-reference prerequisite.",
        new_openrouter_spending_authorized_usd=0,
        planned_images=192,
    )
    publish(directory / "freeze.json", freeze)
    return dict(
        status="prepared",
        run_id=run_id,
        inputs=len(paths),
        recorded_git_commit=commit,
        next="Commit freeze and requests before collection.",
    )


def verify(root, run_id):
    directory = common.directory(run_id)
    freeze = read_json(root / directory / "freeze.json")
    paths = {Path(row["path"]) for row in freeze["inputs"]}
    if not set(source_paths(root)).issubset(paths):
        raise ValueError("freeze omits a required source, scaler, or predecessor input")
    committed(
        root, sorted(paths | {directory / "freeze.json", directory / "planned_requests.jsonl"})
    )
    if freeze["run_id"] != run_id or freeze["config"] != common.configuration(root):
        raise ValueError("freeze/configuration identity changed")
    verify_bindings(root, freeze["inputs"])
    if set(freeze.get("environment", {})) != {"python", *RUNTIME}:
        raise ValueError("freeze must bind the complete numerical runtime")
    for name, expected in freeze["environment"].items():
        actual = platform.python_version() if name == "python" else importlib.metadata.version(name)
        if actual != expected:
            raise ValueError("bound numerical runtime changed: " + name)
    if hash_file(root / directory / "planned_requests.jsonl") != freeze[
        "requests_sha256"
    ] or read_jsonl(root / directory / "planned_requests.jsonl") != common.requests(
        freeze["config"]
    ):
        raise ValueError("the frozen request inventory changed")
    return freeze


def diagnostic_value(root):
    bundle, config = retained.load(root), common.configuration(root)
    value = diagnostics.analyze(bundle)
    noise = inference.retained_noise(bundle["generated"], route=config["route"])
    # The retained helper's original text names its first FLUX application.
    noise["assumptions"] = [
        s.replace("generic-clause FLUX data", "generic-clause OAuth data")
        for s in noise["assumptions"]
    ]
    effects = [[0, 0]] + [[-d, -d] for d in config["hypothetical_effect_grid"]]
    effects += [[-0.5, 0], [0, -0.5]]
    simulation = inference.simulate_design(
        noise,
        seed=config["simulation_seed"],
        trials=config["simulation_trials"],
        effects=effects,
        repetitions=config["repetitions"],
        alpha=config["alpha"],
    )
    return dict(
        diagnostics=value,
        simulation=simulation,
        retained_noise=noise,
        scope="Exposed-data falsification and prospective sensitivity; no new images.",
    )


def _check_report(value, renderer, published, receipt, root):
    verify_bindings(root, receipt["reports"])
    with tempfile.TemporaryDirectory(prefix="prv2-report-replay-") as temporary:
        output = Path(temporary) / "report"
        renderer(value, output)
        replay = sorted(p.relative_to(output) for p in output.rglob("*") if p.is_file())
        original = sorted(p.relative_to(published) for p in published.rglob("*") if p.is_file())
        if replay != original or any(
            hash_file(output / p) != hash_file(published / p) for p in replay
        ):
            raise ValueError("report byte replay differs")
    return len(replay)


def diagnose(root, run_id, *, check=False):
    verify(root, run_id)
    directory = root / common.directory(run_id)
    output = root / common.REPORTS / run_id / "diagnostics"
    if not check and (
        output.exists()
        or (directory / "diagnostics.json").exists()
        or (directory / "diagnostic_receipt.json").exists()
    ):
        raise ValueError("diagnostic publication is terminal")
    value = diagnostic_value(root)
    if check:
        receipt = read_json(directory / "diagnostic_receipt.json")
        if (
            value != read_json(directory / "diagnostics.json")
            or hash_file(directory / "diagnostics.json") != receipt["numeric_sha256"]
            or hash_file(directory / "freeze.json") != receipt["freeze_sha256"]
        ):
            raise ValueError("diagnostic numerical replay differs")
        n = _check_report(value, report.render_diagnostic, output, receipt, root)
        return dict(status="verified", stage="diagnostic", report_files=n)
    publish(directory / "diagnostics.json", value)
    report.render_diagnostic(value, output)
    publish(
        directory / "diagnostic_receipt.json",
        dict(
            freeze_sha256=hash_file(directory / "freeze.json"),
            numeric_sha256=hash_file(directory / "diagnostics.json"),
            reports=bindings(root, [p.relative_to(root) for p in output.rglob("*") if p.is_file()]),
        ),
    )
    return dict(status="published", stage="diagnostic", report=str(output.relative_to(root)))


def collection_inputs(root, run_id):
    """Validate the terminal allocation offline; a running proxy is not needed."""
    freeze = verify(root, run_id)
    directory = common.directory(run_id)
    receipt = read_json(root / directory / "collection_receipt.json")
    if (
        receipt.get("schema") != "painter-responsiveness-collection/2"
        or receipt.get("terminal") is not True
        or receipt["run_id"] != run_id
        or receipt["status"] not in ("completed", "stopped")
        or receipt["total_planned"] != 192
        or receipt["paid_requests"] != 0
        or receipt["incremental_api_spend_usd"] != 0
        or receipt["new_feature_measurements"] != 0
        or (receipt["status"] == "completed") != (receipt["stop_reason"] is None)
        or receipt["recorded_git_commit"] != freeze["recorded_git_commit"]
    ):
        raise ValueError("a terminal, fixed 192-slot OAuth collection is required")
    for key, name in (
        ("freeze_sha256", "freeze.json"),
        ("requests_sha256", "planned_requests.jsonl"),
        ("slot_outcomes_sha256", "slot_outcomes.jsonl"),
    ):
        if hash_file(root / directory / name) != receipt[key]:
            raise ValueError("collection receipt binding changed: " + name)
    ledger_path = root / directory / "generation_events.jsonl"
    if (hash_file(ledger_path) if ledger_path.exists() else None) != receipt[
        "generation_events_sha256"
    ]:
        raise ValueError("collection ledger changed")
    requests = read_jsonl(root / directory / "planned_requests.jsonl")
    by_id = {r["request_id"]: r for r in requests}
    intents, terminals, first_attempts, admitted = {}, {}, [], []
    for event in events(ledger_path):
        rid, attempt = event["request_id"], event["attempt"]
        if rid not in by_id or type(attempt) is not int or attempt not in (1, 2):
            raise ValueError("unknown collection slot or attempt")
        key = rid, attempt
        request = by_id[rid]
        if (event["slot_sequence"], event["route"]) != (request["sequence"], request["route"]):
            raise ValueError("collection treatment identity changed")
        if event["kind"] == "attempt":
            if key in intents or key in terminals or event.get("paid") is not False:
                raise ValueError("invalid collection intent")
            if (
                event["request_sha256"] != digest(request)
                or event["payload_sha256"] != digest(request["payload"])
                or event["reservation_usd"] != 0
            ):
                raise ValueError("attempt differs from its frozen request")
            if attempt == 1:
                first_attempts.append(request["sequence"])
            else:
                previous = terminals.get((rid, 1), {})
                if (
                    previous.get("status") != "http_error"
                    or previous.get("complete") is not True
                    or previous.get("status_code") not in (429, 500, 502, 503, 504)
                    or previous.get("known_error_envelope") is not True
                ):
                    raise ValueError("retry lacks an eligible completed predecessor")
            time_value = event["admitted_monotonic"]
            if type(time_value) not in (int, float) or not math.isfinite(time_value):
                raise ValueError("request admission requires a finite monotonic timestamp")
            if admitted and time_value - admitted[-1] < 5:
                raise ValueError("request admission violates frozen pacing")
            admitted.append(time_value)
            intents[key] = event
        elif event["kind"] == "terminal":
            if key not in intents or key in terminals:
                raise ValueError("unpaired terminal collection event")
            if event.get("cost_usd") != 0:
                raise ValueError("an OAuth collection cannot acquire paid-route accounting")
            if event["status"] == "image_returned" and (
                event.get("complete") is not True
                or event.get("post_started") is not True
                or not 200 <= event.get("status_code", 0) < 300
                or event.get("observed", {}).get("minimum_512") is not True
                or not event.get("response_path")
            ):
                raise ValueError("selected image lacks a complete supported delivery")
            terminals[key] = event
        else:
            raise ValueError("undeclared collection event")
    slots = read_jsonl(root / directory / "slot_outcomes.jsonl")
    retries = sum(
        row["attempt"] > 1 and row.get("post_started", True) for row in terminals.values()
    )
    if (
        first_attempts != list(range(len(first_attempts)))
        or (receipt["status"] == "completed" and len(first_attempts) != 192)
        or set(intents) != set(terminals)
        or receipt["unresolved_intents"] != []
        or retries != receipt["technical_retries_dispatched"]
        or sum(attempt == 2 for _, attempt in intents)
        > freeze["config"]["maximum_technical_retries"]
    ):
        raise ValueError("terminal retry, ordering or unresolved-attempt accounting changed")
    if (
        slots != _slot_outcomes(requests, list(terminals.values()), list(intents.values()))
        or len(intents) != receipt["attempt_intents"]
        or len(terminals) != receipt["terminal_attempts"]
        or dict(Counter(s["status"] for s in slots)) != receipt["status_counts"]
    ):
        raise ValueError("terminal allocation no longer reproduces its ledger")
    return freeze, requests, slots, receipt


def _response_entity(root, run_id, row, attempt):
    from .collection import MAX_RESPONSE

    sequence = row.get("slot_sequence", row.get("sequence"))
    expected = common.WORKSPACE / run_id / "responses" / f"{sequence:04d}-a{attempt}.json.gz"
    if row["response_path"] != str(expected):
        raise ValueError("response path differs from its canonical slot attempt")
    path = confined(root, expected, common.WORKSPACE / run_id / "responses")
    if hash_file(path) != row["stored_response_sha256"]:
        raise ValueError("compressed response changed")
    with gzip.open(path, "rb") as handle:
        body = handle.read(MAX_RESPONSE + 1)
    if len(body) > MAX_RESPONSE or hashlib.sha256(body).hexdigest() != row["response_sha256"]:
        raise ValueError("response entity changed or exceeds its byte bound")
    return body


def selected_bytes(root, run_id, slot):
    body = _response_entity(root, run_id, slot, slot["selected_attempt"])
    raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
    if (
        hashlib.sha256(raw).hexdigest() != slot["observed"]["image_sha256"]
        or len(raw) != slot["observed"]["image_bytes"]
        or inspect_response(body) != slot["observed"]
    ):
        raise ValueError("embedded image changed")
    return body, raw


def _measure(root, run_id, requests, slots, config):
    scalers = read_json(root / retained.MAIN / "scalers.json")
    if set(scalers) != set(PIPELINES):
        raise ValueError("all three frozen development scalers are required")
    for record in scalers.values():
        center, scale = (
            np.asarray(record["scaler"][key], dtype=float) for key in ("center", "scale")
        )
        if (
            center.shape != (31,)
            or scale.shape != (31,)
            or not np.isfinite(center).all()
            or not np.isfinite(scale).all()
            or np.any(scale <= 0)
        ):
            raise ValueError("invalid frozen development scale")
    workspace = root / common.WORKSPACE / run_id
    rows = []
    for request, slot in zip(requests, slots, strict=True):
        item = {k: v for k, v in request.items() if k != "payload"}
        item.update(
            image_id=f"{run_id}:{request['request_id']}",
            collection_status=slot["status"],
            source_response_path=slot["response_path"],
            source_response_sha256=slot["response_sha256"],
            selected_attempt=slot["selected_attempt"],
            observed=slot["observed"],
        )
        if slot["status"] != "image_returned":
            rows.extend(
                dict(
                    item,
                    pipeline=p,
                    status=slot["status"],
                    values=None,
                    scaled=None,
                    chroma_primary_iqr=None,
                )
                for p in PIPELINES
            )
            continue
        body, raw = selected_bytes(root, run_id, slot)
        if inspect_response(body) != slot["observed"]:
            raise ValueError("retained image/container metadata changed")
        with tempfile.TemporaryDirectory(prefix="decode-", dir=workspace) as temporary:
            path = Path(temporary) / "image.bin"
            path.write_bytes(raw)
            measured = measure_path(path, item, PIPELINES)
        if [r["pipeline"] for r in measured] != list(PIPELINES):
            raise ValueError("extractor did not return the three fixed pipelines")
        for row in measured:
            if any(row.get(key) != value for key, value in item.items()):
                raise ValueError("extractor changed the measurement treatment identity")
            if row["status"] == "measured":
                vector = np.asarray(row["values"], dtype=float)
                if vector.shape != (31,) or not np.isfinite(vector).all():
                    raise ValueError("invalid measured feature vector")
                row["scaled"] = transform(vector, scalers[row["pipeline"]]["scaler"]).tolist()
                row["chroma_primary_iqr"] = float(
                    (vector[2] - config["primary_chroma_center"]) / config["primary_chroma_scale"]
                )
            else:
                row.update(values=None, scaled=None, chroma_primary_iqr=None)
        rows.extend(measured)
    return rows


def result_value(root, run_id, rows):
    _, requests, slots, receipt = collection_inputs(root, run_id)
    expected = [(request["request_id"], pipeline) for request in requests for pipeline in PIPELINES]
    if [(row.get("request_id"), row.get("pipeline")) for row in rows] != expected:
        raise ValueError("measurement inventory must preserve all 192 slots and three pipelines")
    for row, (request_id, _) in zip(rows, expected, strict=True):
        index = next(i for i, request in enumerate(requests) if request["request_id"] == request_id)
        if row.get("collection_status") != slots[index]["status"] or (
            slots[index]["status"] != "image_returned" and row["status"] == "measured"
        ):
            raise ValueError("measurement availability differs from its allocated collection slot")
    value = analysis.analyze(
        requests, rows, retained.load(root)["reference"], common.configuration(root)
    )
    terminals = [
        row
        for row in events(root / common.directory(run_id) / "generation_events.jsonl")
        if row["kind"] == "terminal"
    ]
    timing = [
        {
            key: row.get(key)
            for key in (
                "request_id",
                "attempt",
                "slot_sequence",
                "status",
                "status_code",
                "complete",
                "post_started",
                "latency_seconds",
                "transport_started_monotonic",
                "observed",
            )
        }
        for row in terminals
    ]
    latencies = [
        row["latency_seconds"]
        for row in terminals
        if row.get("post_started", True) and row.get("latency_seconds") is not None
    ]
    observed = [row["observed"] for row in terminals if row.get("observed") is not None]
    transport_summary = dict(
        measured_latencies=len(latencies),
        latency_median_seconds=float(np.median(latencies)) if latencies else None,
        latency_p90_seconds=float(np.quantile(latencies, 0.9)) if latencies else None,
        requested_rendering=common.configuration(root)["requested_rendering"],
        geometry_counts=dict(Counter(f"{row['width']}x{row['height']}" for row in observed)),
        format_counts=dict(Counter(row["format"] for row in observed)),
        reported_quality_counts=dict(
            Counter(str(row["reported"].get("quality") or "not_reported") for row in observed)
        ),
        scope="All completed attempts with retained metadata, including failures and retries; "
        "latency summaries exclude attempts without an observed transport duration.",
    )
    value["collection"] = dict(
        status=receipt["status"],
        stop_reason=receipt["stop_reason"],
        attempts=receipt["attempt_intents"],
        slots=slots,
        incremental_api_spend_usd=0,
        paid_requests=0,
        per_attempt_transport=timing,
        transport_summary=transport_summary,
    )
    return value


def measure(root, run_id, *, check=False):
    with stage_lock(root / common.WORKSPACE / ".measurement.lock"):
        freeze, requests, slots, _ = collection_inputs(root, run_id)
        directory = root / common.directory(run_id)
        output = root / common.REPORTS / run_id / "experiment"
        target, receipt_path = (
            directory / "generated_features.jsonl",
            directory / "analysis_receipt.json",
        )
        if check:
            receipt = read_json(receipt_path)
            expected_inputs = _measurement_input_paths(root, run_id)
            if receipt["recorded_git_commit"] != freeze["recorded_git_commit"] or {
                Path(row["path"]) for row in receipt["inputs"]
            } != set(expected_inputs):
                raise ValueError("measurement receipt source identity or input closure changed")
            verify_bindings(root, receipt["inputs"])
            if (
                hash_file(target) != receipt["features_sha256"]
                or hash_file(directory / "analysis.json") != receipt["analysis_sha256"]
            ):
                raise ValueError("measured-vector result bytes changed")
            value = result_value(root, run_id, read_jsonl(target))
            if value != read_json(directory / "analysis.json"):
                raise ValueError("experiment numeric replay changed")
            n = _check_report(value, report.render_experiment, output, receipt, root)
            return dict(
                status="verified",
                stage="experiment",
                report_files=n,
                scope="Retained vector, numerical and report replay; no feature re-extraction.",
            )
        marker = root / common.WORKSPACE / run_id / "measurement_started.json"
        if (
            marker.exists()
            or output.exists()
            or any(p.exists() for p in (target, receipt_path, directory / "analysis.json"))
        ):
            raise ValueError("measurement is terminal or interrupted; never overwrite it")
        selected = [s for s in slots if s["status"] == "image_returned"]
        for slot in selected:
            selected_bytes(root, run_id, slot)
        all_responses = [
            row
            for row in events(directory / "generation_events.jsonl")
            if row["kind"] == "terminal" and row.get("response_path") is not None
        ]
        for row in all_responses:
            _response_entity(root, run_id, row, row["attempt"])
        paths = _measurement_input_paths(root, run_id)
        inputs = bindings(root, paths)
        publish(marker, dict(inputs=inputs, source_commit=freeze["recorded_git_commit"]))
        rows = _measure(root, run_id, requests, slots, freeze["config"])
        verify_bindings(root, inputs)
        value = result_value(root, run_id, rows)
        publish(target, rows, lines=True)
        publish(directory / "analysis.json", value)
        report.render_experiment(value, output)
        publish(
            receipt_path,
            dict(
                recorded_git_commit=freeze["recorded_git_commit"],
                inputs=inputs,
                features_sha256=hash_file(target),
                analysis_sha256=hash_file(directory / "analysis.json"),
                reports=bindings(
                    root, [p.relative_to(root) for p in output.rglob("*") if p.is_file()]
                ),
            ),
        )
        return dict(
            status="published",
            stage="experiment",
            measurements=len(rows),
            primary_status=value["primary"]["status"],
            report=str(output.relative_to(root)),
        )


def _measurement_input_paths(root, run_id):
    directory = common.directory(run_id)
    paths = [
        directory / name
        for name in (
            "freeze.json",
            "planned_requests.jsonl",
            "collection_receipt.json",
            "slot_outcomes.jsonl",
            "generation_events.jsonl",
        )
        if (root / directory / name).exists()
    ]
    paths.extend(
        Path(row["response_path"])
        for row in events(root / directory / "generation_events.jsonl")
        if row["kind"] == "terminal" and row.get("response_path") is not None
    )
    return sorted(paths)
