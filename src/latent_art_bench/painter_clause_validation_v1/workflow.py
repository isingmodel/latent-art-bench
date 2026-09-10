"""Qualified prospective freeze and terminal-only OAuth measurement/replay."""

import base64
import gzip
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_distribution_study_v1 import transport
from latent_art_bench.painter_distribution_study_v1.measurement import measure_path
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    confined,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import common
from .collection import (
    HISTORICAL_ACCOUNTED_USD,
    inspect_response,
    invalidates_identity,
    stop_reason,
    validate_inventory,
)

RUNTIME = ("numpy", "scipy", "Pillow", "httpx", "PyWavelets", "scikit-image")


def environment():
    return dict(
        python=platform.python_version(),
        **{name: importlib.metadata.version(name) for name in RUNTIME},
    )


def clean_commit(root, paths):
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *map(str, paths)], cwd=root, check=False
    ).returncode:
        raise ValueError("freeze-bound index changes must be committed first")
    return committed(root, paths)


def qualification_paths(root):
    paths = {common.CONFIG, common.SCENES, common.INPUTS, common.STUDIES / "PROTOCOL.md"}
    for directory in (common.PACKAGE, Path("tests") / common.NAMESPACE):
        paths.update(p.relative_to(root) for p in (root / directory).glob("*.py"))
    return paths


def qualification(root):
    """Require reviewed qualification of the exact committed scientific inputs."""
    root = Path(root)
    value = read_json(root / common.QUALIFICATION)
    if (
        value.get("schema") != "painter-clause-validation-qualification/1"
        or value.get("qualified") is not True
        or not re.fullmatch(r"[0-9a-f]{40}", value.get("source_commit", ""))
    ):
        raise ValueError("explicit source-bound qualification is required")
    records = value.get("source_bindings", [])
    paths = [Path(row["path"]) for row in records]
    if (
        len(set(paths)) != len(paths)
        or not qualification_paths(root) <= set(paths)
        or any(p.is_absolute() or ".." in p.parts for p in paths)
    ):
        raise ValueError("qualification omits scientific source/design or repeats unsafe paths")
    verify_bindings(root, records)
    for row in records:
        blob = subprocess.run(
            ["git", "show", f"{value['source_commit']}:{row['path']}"],
            cwd=root,
            capture_output=True,
        )
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != row["sha256"]:
            raise ValueError("qualification source commit differs from bound bytes")
    return value


def source_paths(root):
    root = Path(root)
    paths = set(common.binding_paths(root)) | {
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
    }
    packages = (
        common.NAMESPACE,
        "painter_naming_replication_v1",
        "painter_naming_geometry_v1",
        "painter_distribution_study_v1",
        "painter_distribution_revision_v1",
        "painter_distribution_exploration_v1",
        "painter_feature_generation_v2",
        "painter_prompt_study_v1",
        "painter_responsiveness_v1",
        "painter_responsiveness_v2",
        "painter_responsiveness_recovery_v1",
    )
    for package in packages:
        paths.update(
            p.relative_to(root) for p in (root / "src/latent_art_bench" / package).glob("*.py")
        )
    paths.update(qualification_paths(root))
    return sorted(paths)


def historical_budget(root, config):
    budget = read_json(root / common.BUDGET_RECEIPT)["budget"]
    if (
        not math.isclose(
            budget["accounted_usd"], HISTORICAL_ACCOUNTED_USD, rel_tol=0, abs_tol=1e-10
        )
        or config["historical_accounted_usd"] != HISTORICAL_ACCOUNTED_USD
        or budget["pending"]
        or budget["unknown"]
        or budget["pending_paid"] != 0
        or budget["terminal_reserves_usd"] != 0
        or budget["new_reserves_usd"] != 0
    ):
        raise ValueError("historical accounting differs from the terminal predecessor")
    return budget


def prepare(root, run_id, proxy_root):
    root = Path(root)
    directory = root / common.directory(run_id)
    if directory.exists() or (root / common.WORKSPACE / run_id).exists():
        raise ValueError("run identity already exists; never prepare over retained evidence")
    config = common.configuration(root)
    qualified = qualification(root)
    paths = source_paths(root)
    commit = clean_commit(root, paths)
    budget = historical_budget(root, config)
    proxy = transport.proxy_snapshot(proxy_root)
    inventory = common.requests(root, config)
    validate_inventory(inventory, config)
    publish(directory / "planned_requests.jsonl", inventory, lines=True)
    publish(
        directory / "freeze.json",
        dict(
            schema="painter-clause-validation-freeze/1",
            run_id=run_id,
            prepared_at_utc=utc_now().isoformat(),
            recorded_git_commit=commit,
            config=config,
            inputs=bindings(root, paths),
            environment=environment(),
            proxy_snapshot=proxy,
            requests_sha256=hash_file(directory / "planned_requests.jsonl"),
            qualification_sha256=hash_file(root / common.QUALIFICATION),
            qualified_source_commit=qualified["source_commit"],
            budget_baseline_usd=HISTORICAL_ACCOUNTED_USD,
            historical_budget=budget,
            scope="One OAuth-only finite-scene collection; "
            "no paid API or independent-backend claim",
        ),
    )
    return dict(
        status="prepared_commit_freeze_before_collection",
        run_id=run_id,
        planned=len(inventory),
        recorded_git_commit=commit,
    )


def verify(root, run_id):
    root = Path(root)
    directory = common.directory(run_id)
    value = read_json(root / directory / "freeze.json")
    bound = {Path(r["path"]) for r in value["inputs"]}
    if len(bound) != len(value["inputs"]) or set(source_paths(root)) != bound:
        raise ValueError("freeze input inventory differs")
    clean_commit(
        root, sorted(bound | {directory / "freeze.json", directory / "planned_requests.jsonl"})
    )
    verify_bindings(root, value["inputs"])
    # The freeze may be committed after the scientific source and qualification.
    for row in value["inputs"]:
        blob = subprocess.run(
            ["git", "show", f"{value['recorded_git_commit']}:{row['path']}"],
            cwd=root,
            capture_output=True,
        )
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != row["sha256"]:
            raise ValueError("freeze source commit differs from bound bytes")
    qualified = qualification(root)
    if (
        value["schema"] != "painter-clause-validation-freeze/1"
        or value["run_id"] != run_id
        or value["config"] != common.configuration(root)
        or value["environment"] != environment()
        or value["qualification_sha256"] != hash_file(root / common.QUALIFICATION)
        or value["qualified_source_commit"] != qualified["source_commit"]
    ):
        raise ValueError("freeze identity, qualification, configuration or runtime changed")
    path = root / directory / "planned_requests.jsonl"
    requests = read_jsonl(path)
    if hash_file(path) != value["requests_sha256"] or requests != common.requests(root):
        raise ValueError("prospective request inventory changed")
    validate_inventory(requests, value["config"])
    return value


def verify_live_metadata(root, freeze, proxy_root):
    """Local proxy source/process identity only; no API or account request."""
    if transport.proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
        raise ValueError("OAuth source/process identity changed")


def collection_inputs(root, run_id):
    root = Path(root)
    freeze = verify(root, run_id)
    directory = root / common.directory(run_id)
    receipt = read_json(directory / "collection_receipt.json")
    required_outputs = {
        common.directory(run_id) / "generation_events.jsonl",
        common.directory(run_id) / "slot_outcomes.jsonl",
        common.WORKSPACE / run_id / "collection_started.json",
    }
    if (directory / "operator_events.jsonl").exists():
        required_outputs.add(common.directory(run_id) / "operator_events.jsonl")
    if (
        len(receipt["outputs"]) != len(required_outputs)
        or {Path(r["path"]) for r in receipt["outputs"]} != required_outputs
    ):
        raise ValueError("collection receipt output inventory differs")
    verify_bindings(root, receipt["outputs"])
    if (
        receipt["schema"] != "painter-clause-validation-collection/1"
        or receipt["run_id"] != run_id
        or receipt["freeze_sha256"] != hash_file(directory / "freeze.json")
        or receipt["budget"]["accounted_usd"] != HISTORICAL_ACCOUNTED_USD
        or receipt["budget"]["pending"]
        or receipt["status"] not in ("complete", "stopped")
        or (receipt["reason"] is None) != (receipt["status"] == "complete")
        or type(receipt["duration_contract_met"]) is not bool
        or type(receipt.get("identity_contract_met")) is not bool
        or receipt["elapsed_seconds"] < 0
        or receipt["duration_contract_met"]
        != (receipt["elapsed_seconds"] <= freeze["config"]["maximum_collection_seconds"])
    ):
        raise ValueError("terminal receipt identity, freeze or accounting differs")
    requests = read_jsonl(directory / "planned_requests.jsonl")
    slots = read_jsonl(directory / "slot_outcomes.jsonl")
    ledger = events(directory / "generation_events.jsonl")
    if len(slots) != len(requests) or receipt["planned"] != len(requests):
        raise ValueError("complete planned slot accounting is required")
    intents, terminals = {}, {}
    by_id = {r["request_id"]: r for r in requests}
    for row in ledger:
        key = row["request_id"], row["attempt"]
        if key[0] not in by_id or key[1] not in (1, 2):
            raise ValueError("unknown attempt identity")
        source = by_id[key[0]]
        if (
            row["slot_sequence"] != source["sequence"]
            or row["route"] != source["route"]
            or row.get("paid") is not False
        ):
            raise ValueError("transport/assignment identity mismatch")
        if row["kind"] == "attempt":
            expected = hashlib.sha256(json.dumps(source["payload"], sort_keys=True).encode())
            if (
                key in intents
                or row["payload_sha256"] != expected.hexdigest()
                or row["reserved_usd"] != 0
                or row["dispatch_ticket"] != len(intents)
            ):
                raise ValueError("duplicate, reordered or altered request intent")
            if key[1] == 2:
                previous = terminals.get((key[0], 1), {})
                if (
                    previous.get("status") != "http_error"
                    or previous.get("recognized_technical_error") is not True
                ):
                    raise ValueError("retry lacks a preceding qualified technical error")
            intents[key] = row
        elif row["kind"] == "terminal":
            if key not in intents or key in terminals or row["cost_usd"] != 0:
                raise ValueError("unpaired terminal or paid accounting")
            terminals[key] = row
        else:
            raise ValueError("unknown ledger event")
    if (
        set(intents) != set(terminals)
        or receipt["attempts"] != len(terminals)
        or len(intents) > freeze["config"]["maximum_attempts"]
        or sum(k[1] == 2 for k in intents) > freeze["config"]["maximum_technical_retries"]
    ):
        raise ValueError("unresolved transport intents or exceeded attempt limits")
    operators = events(directory / "operator_events.jsonl")
    final_checks = [r for r in operators if r["kind"] == "final_identity_check"]
    if len(final_checks) != 1:
        raise ValueError("exactly one final source/proxy check is required")
    final_check = final_checks[0]
    expected_identity = (
        final_check.get("source_verified") is True
        and final_check.get("proxy_verified") is True
        and not any(invalidates_identity(r.get("reason")) for r in operators)
        and not any(invalidates_identity(stop_reason(r, [])) for r in terminals.values())
    )
    if receipt["identity_contract_met"] != expected_identity:
        raise ValueError("identity contract differs from terminal/final-check evidence")
    for request, slot in zip(requests, slots, strict=True):
        if (slot["request_id"], slot["sequence"]) != (request["request_id"], request["sequence"]):
            raise ValueError("slot inventory reordered")
        attempts = [
            r for (identity, _), r in terminals.items() if identity == request["request_id"]
        ]
        successes = [r for r in attempts if r["status"] == "image_returned"]
        chosen = successes[0] if successes else attempts[-1] if attempts else None
        expected_status = chosen["status"] if chosen else "not_attempted_collection_stopped"
        if len(successes) > 1 or slot["status"] != expected_status:
            raise ValueError("slot selection differs from the first valid output rule")
        expected = dict(
            selected_attempt=chosen["attempt"] if successes else None,
            response_path=chosen.get("response_path") if successes else None,
            response_sha256=chosen.get("response_sha256") if successes else None,
            observed=chosen.get("observed") if successes else None,
        )
        if any(slot[k] != v for k, v in expected.items()):
            raise ValueError("selected output provenance differs")
    if receipt["slot_counts"] != dict(Counter(s["status"] for s in slots)):
        raise ValueError("receipt slot totals differ")
    retry_intents = sum(k[1] == 2 for k in intents)
    if (
        receipt["retry_intents"] != retry_intents
        or not retry_intents
        <= receipt["retry_decisions"]
        <= freeze["config"]["maximum_technical_retries"]
        or receipt["posted_attempts"]
        != sum(r.get("post_started", True) for r in terminals.values())
        or receipt["retries"]
        != sum(k[1] == 2 and r.get("post_started", True) for k, r in terminals.items())
    ):
        raise ValueError("receipt transport totals differ")
    return freeze, requests, slots, terminals, receipt


def response_bytes(root, run_id, row):
    path = confined(root, row["response_path"], common.WORKSPACE / run_id / "responses")
    if hash_file(path) != row["stored_response_sha256"]:
        raise ValueError("retained response storage hash changed")
    with gzip.open(path, "rb") as handle:
        body = handle.read(64 * 1024**2 + 1)
    if len(body) > 64 * 1024**2 or hashlib.sha256(body).hexdigest() != row["response_sha256"]:
        raise ValueError("retained response entity hash changed")
    return body


def verify_responses(root, run_id):
    _, _, _, terminal, _ = collection_inputs(root, run_id)
    checked = 0
    for row in terminal.values():
        if row.get("response_path"):
            body = response_bytes(root, run_id, row)
            if row["status"] == "image_returned" and inspect_response(body) != row["observed"]:
                raise ValueError("returned image metadata/hash differs")
            checked += 1
    return dict(status="raw_responses_verified", checked=checked, new_measurements=0)


def reference_rows(root):
    return read_json(Path(root) / common.INPUTS)


def _measure(root, run_id, requests, slots, terminals):
    scalers = reference_rows(root)["scalers"]
    rows = []
    workspace = root / common.WORKSPACE / run_id
    for request, slot in zip(requests, slots, strict=True):
        item = {k: v for k, v in request.items() if k != "payload"}
        item.update(
            image_id=f"{run_id}:{request['request_id']}",
            source_response_path=slot["response_path"],
            source_response_sha256=slot["response_sha256"],
            selected_attempt=slot["selected_attempt"],
            observed=slot["observed"],
        )
        if slot["status"] != "image_returned":
            rows.extend(
                dict(item, pipeline=p, status=slot["status"], values=None, scaled=None)
                for p in common.PIPELINES
            )
            continue
        row = terminals[request["request_id"], slot["selected_attempt"]]
        body = response_bytes(root, run_id, row)
        if inspect_response(body) != slot["observed"]:
            raise ValueError("selected image metadata differs")
        raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
        item["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory(prefix="measure-", dir=workspace) as temporary:
            path = Path(temporary) / "image.bin"
            path.write_bytes(raw)
            measured = measure_path(path, item, common.PIPELINES)
        if [r["pipeline"] for r in measured] != list(common.PIPELINES):
            raise ValueError("measurement pipeline inventory differs")
        for result in measured:
            if result["status"] == "measured":
                values = np.asarray(result["values"], dtype=float)
                if values.shape != (31,) or not np.all(np.isfinite(values)):
                    raise ValueError("finite fixed 31-feature vector required")
                result["scaled"] = transform(values, scalers[result["pipeline"]]["scaler"]).tolist()
            else:
                result.update(values=None, scaled=None)
            rows.append(result)
    return rows


def result_value(root, requests, rows, config, receipt):
    from . import analysis

    return analysis.analyze(
        requests, rows, reference_rows(root), config, collection_receipt=receipt
    )


def report_text(value):
    from . import analysis

    return analysis.report_text(value)


def measure(root, run_id):
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".measurement.lock"):
        freeze, requests, slots, terminal, receipt = collection_inputs(root, run_id)
        directory = root / common.directory(run_id)
        marker = root / common.WORKSPACE / run_id / "measurement_started.json"
        publish(marker, dict(started_at_utc=utc_now().isoformat(), one_shot=True))
        rows = _measure(root, run_id, requests, slots, terminal)
        value = result_value(root, requests, rows, freeze["config"], receipt)
        report = root / common.REPORTS / run_id
        publish(directory / "measurements.jsonl", rows, lines=True)
        publish(report / "analysis.json", value)
        with (report / "REPORT.md").open("x", encoding="utf-8") as handle:
            handle.write(report_text(value))
        outputs = [
            directory / "measurements.jsonl",
            report / "analysis.json",
            report / "REPORT.md",
            marker,
        ]
        publish(
            directory / "measurement_receipt.json",
            dict(
                schema="painter-clause-validation-measurement/1",
                run_id=run_id,
                collection_receipt_sha256=hash_file(directory / "collection_receipt.json"),
                outputs=bindings(root, [p.relative_to(root) for p in outputs]),
            ),
        )
        return dict(status="measured_and_reported", run_id=run_id, primary=value["primary"])


def check(root, run_id, *, pixels=False):
    root = Path(root)
    freeze, requests, slots, terminal, receipt = collection_inputs(root, run_id)
    directory = root / common.directory(run_id)
    measured = read_json(directory / "measurement_receipt.json")
    if (
        measured["schema"] != "painter-clause-validation-measurement/1"
        or measured["run_id"] != run_id
        or hash_file(directory / "collection_receipt.json") != measured["collection_receipt_sha256"]
    ):
        raise ValueError("terminal collection receipt changed")
    verify_bindings(root, measured["outputs"])
    rows = read_jsonl(directory / "measurements.jsonl")
    if pixels and _measure(root, run_id, requests, slots, terminal) != rows:
        raise ValueError("pixel measurement replay differs")
    value = result_value(root, requests, rows, freeze["config"], receipt)
    report = root / common.REPORTS / run_id
    if (
        value != read_json(report / "analysis.json")
        or report_text(value) != (report / "REPORT.md").read_text()
    ):
        raise ValueError("offline numerical/report replay differs")
    return dict(
        status="pixels_and_numbers_replayed" if pixels else "numbers_replayed",
        primary=value["primary"],
        raw_response_access=pixels,
    )
