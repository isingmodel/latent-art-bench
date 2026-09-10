"""Qualified fixed-map freeze, terminal accounting and primary-only measurement/replay."""

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

from . import common, metadata, precision
from .collection import (
    HISTORICAL_ACCOUNTED_USD,
    admission,
    cost_record,
    eligibility,
    inspect_response,
    invalidates_identity,
    namespace_state,
    stop_reason,
    timing_contract,
    validate_inventory,
)

RUNTIME = ("numpy", "scipy", "Pillow", "httpx", "PyWavelets", "scikit-image")


def environment():
    return dict(
        python=platform.python_version(),
        **{name: importlib.metadata.version(name) for name in RUNTIME},
    )


def clean_commit(root, paths):
    if any((Path(root) / p).is_symlink() for p in paths):
        raise ValueError("symlink source bindings forbidden")
    if subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *map(str, paths)], cwd=root, check=False
    ).returncode:
        raise ValueError("freeze-bound index changes must be committed first")
    return committed(root, paths)


def qualification_paths(root):
    paths = {
        common.CONFIG,
        common.SCENES,
        common.INPUTS,
        common.STUDIES / "PROTOCOL.md",
        common.STUDIES / "DECISION.md",
        common.STUDIES / "TECHNICAL_PROTOCOL.md",
    }
    for directory in (common.PACKAGE, Path("tests") / common.NAMESPACE):
        paths.update(p.relative_to(root) for p in (root / directory).glob("*.py"))
    return paths


def qualification(root):
    """Require reviewed qualification of the exact committed scientific inputs."""
    root = Path(root)
    value = read_json(root / common.QUALIFICATION)
    if (
        value.get("schema") != "painter-map-validation-qualification/2"
        or value.get("qualified") is not True
        or not re.fullmatch(r"[0-9a-f]{40}", value.get("source_commit", ""))
    ):
        raise ValueError("explicit source-bound qualification is required")
    records = value.get("source_bindings", [])
    paths = [Path(row["path"]) for row in records]
    if (
        len(set(paths)) != len(paths)
        or not (set(source_paths(root)) - {common.QUALIFICATION}) <= set(paths)
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
        Path("src/latent_art_bench/__init__.py"),
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
    }
    packages = (
        common.NAMESPACE,
        "painter_naming_replication_v1",
        "painter_map_validation_v1",
        "painter_naming_geometry_v1",
        "painter_distribution_study_v1",
        "painter_distribution_revision_v1",
        "painter_distribution_exploration_v1",
        "painter_feature_generation_v2",
        "painter_feature_generation_v1",
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


def numerical_qualification(root):
    """Authenticate the sole completed proxy qualification, without resimulation."""
    root = Path(root)
    run = read_json(root / precision.OUTPUT_PATH / "RUN.json")
    result = read_json(root / precision.OUTPUT_PATH / "precision.json")
    if (
        run["schema"] != "painter-map-precision-v2-run/1"
        or any(result.get(k) != v for k, v in run.items())
        or {r["path"] for r in run["source_bindings"]} != {str(p) for p in precision.BINDINGS}
        or len(run["source_bindings"]) != len(precision.BINDINGS)
        or precision.read_previous(root) != run["predecessor"]
    ):
        raise ValueError("exact completed v2 qualification lineage required")
    verify_bindings(root, run["source_bindings"])
    for row in run["source_bindings"]:
        blob = subprocess.run(
            ["git", "show", f"{run['source_commit']}:{row['path']}"], cwd=root, capture_output=True
        )
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != row["sha256"]:
            raise ValueError("qualification source binding differs")
    decision = precision.allocation_decision(result["qualification"]["records"])
    if (
        decision["decision"] != "qualified_proxy_only"
        or any(result["qualification"].get(k) != v for k, v in decision.items())
        or (root / precision.OUTPUT_PATH / "PRECISION.md").read_text() != precision.report(result)
    ):
        raise ValueError("single full R10 qualification did not pass")
    return dict(
        source_commit=run["source_commit"],
        result_sha256=hash_file(root / precision.OUTPUT_PATH / "precision.json"),
        selected_outputs=240,
        status="qualified_proxy_only",
    )


def historical_budget(root, config):
    root = Path(root)
    budget = read_json(root / common.BUDGET_RECEIPT)["budget"]
    main = read_json(root / common.MAIN_RECEIPT)["budget"]
    if (
        not math.isclose(
            budget["accounted_usd"], HISTORICAL_ACCOUNTED_USD, rel_tol=0, abs_tol=1e-10
        )
        or not math.isclose(main["accounted_usd"], 45.6819185, rel_tol=0, abs_tol=1e-10)
        or config["historical_accounted_usd"] != HISTORICAL_ACCOUNTED_USD
        or budget["pending"]
        or budget["unknown"]
        or budget["pending_paid"] != 0
        or budget["terminal_reserves_usd"] != 0
        or budget["new_reserves_usd"] != 0
        or not math.isclose(budget["new_reported_usd"], 5.04, rel_tol=0, abs_tol=1e-10)
    ):
        raise ValueError("historical accounting differs from the retained baseline")
    # Independently sum all terminal paid ledgers, retaining the one old $5 unknown.
    total, pending, unknown = 0.0, [], 0
    for namespace in ("painter_distribution_study_v1", "painter_naming_replication_v1"):
        for path in sorted((root / "data/manifests" / namespace).glob("*/generation_events.jsonl")):
            intents, terminals = {}, set()
            for row in events(path):
                key = row["request_id"], row.get("attempt", 1)
                if row["kind"] == "attempt":
                    if key in intents:
                        raise ValueError("duplicate historical intent")
                    intents[key] = row
                elif row["kind"] == "terminal":
                    if key not in intents or key in terminals:
                        raise ValueError("invalid historical terminal")
                    terminals.add(key)
                    if intents[key]["paid"]:
                        cost = row.get("cost_usd")
                        total += 5 if cost is None else cost
                        unknown += cost is None
            pending.extend(set(intents) - terminals)
    if (
        pending
        or unknown != 1
        or not math.isclose(total, HISTORICAL_ACCOUNTED_USD, rel_tol=0, abs_tol=1e-10)
    ):
        raise ValueError("historical ledger arithmetic or unresolved liabilities changed")
    for path in common.ZERO_PAID_RECEIPTS:
        value = read_json(root / path)
        old_budget = value["budget"]
        if (
            old_budget["accounted_usd"] != HISTORICAL_ACCOUNTED_USD
            or old_budget["new_reported_usd"] != 0
            or old_budget["new_reserves_usd"] != 0
            or old_budget["pending"]
        ):
            raise ValueError("later zero-paid accounting changed")
        ledger = path.with_name("generation_events.jsonl")
        rows = events(root / ledger)
        required = [r for r in value["outputs"] if r["path"] == str(ledger)]
        if len(required) != 1:
            raise ValueError("zero-paid terminal ledger binding missing")
        verify_bindings(root, required)
        if any(r.get("paid") is not False or r.get("cost_usd", 0) != 0 for r in rows):
            raise ValueError("unexpected later paid cost")
    return dict(
        accounted_usd=HISTORICAL_ACCOUNTED_USD,
        permanent_unknown_reserve_usd=5,
        legacy_float_tolerance_usd=1e-10,
        no_new_unresolved_liability=True,
    )


def write_inputs(root):
    from . import analysis

    publish(Path(root) / common.INPUTS, analysis.load_inputs(root))
    return dict(status="inputs_written_commit_before_prepare", path=str(common.INPUTS))


def validate_input_lineage(root):
    from . import analysis

    value = read_json(Path(root) / common.INPUTS)
    if common.canonical(value) != common.canonical(analysis.load_inputs(root)):
        raise ValueError("compact inputs differ from exact immutable references/scaler/maps")
    analysis.validate_inputs(value)
    return value["origins"]


def prepare(root, run_id):
    root = Path(root)
    directory = root / common.directory(run_id)
    if directory.exists() or (root / common.WORKSPACE / run_id).exists():
        raise ValueError("run identity already exists; never prepare over retained evidence")
    config = common.configuration(root)
    qualified = qualification(root)
    prior = numerical_qualification(root)
    validate_input_lineage(root)
    paths = source_paths(root)
    commit = clean_commit(root, paths)
    budget = historical_budget(root, config)
    metadata.validate(root, common.PREFLIGHT_ID)
    inventory = common.requests(root, config)
    validate_inventory(inventory, config)
    publish(directory / "planned_requests.jsonl", inventory, lines=True)
    publish(
        directory / "freeze.json",
        dict(
            schema="painter-map-validation-freeze/2",
            run_id=run_id,
            prepared_at_utc=utc_now().isoformat(),
            recorded_git_commit=commit,
            config=config,
            inputs=bindings(root, paths),
            environment=environment(),
            metadata_sha256=hash_file(root / common.METADATA),
            requests_sha256=hash_file(directory / "planned_requests.jsonl"),
            qualification_sha256=hash_file(root / common.QUALIFICATION),
            qualified_source_commit=qualified["source_commit"],
            budget_baseline_usd=HISTORICAL_ACCOUNTED_USD,
            historical_budget=budget,
            numerical_qualification=prior,
            scope="One conditional-budget FLUX fixed-scene R10 collection; "
            "no fallback or checkpoint attestation",
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
    validate_input_lineage(root)
    if (
        value["schema"] != "painter-map-validation-freeze/2"
        or value["run_id"] != run_id
        or value["config"] != common.configuration(root)
        or value["environment"] != environment()
        or value["qualification_sha256"] != hash_file(root / common.QUALIFICATION)
        or value["qualified_source_commit"] != qualified["source_commit"]
        or value["numerical_qualification"] != numerical_qualification(root)
        or value["metadata_sha256"] != hash_file(root / common.METADATA)
        or value["historical_budget"] != historical_budget(root, value["config"])
    ):
        raise ValueError("freeze identity, qualification, configuration or runtime changed")
    path = root / directory / "planned_requests.jsonl"
    requests = read_jsonl(path)
    if hash_file(path) != value["requests_sha256"] or requests != common.requests(root):
        raise ValueError("prospective request inventory changed")
    validate_inventory(requests, value["config"])
    metadata.validate(root, common.PREFLIGHT_ID)
    return value


def dispatch_metadata(root, freeze, *, transport=None):
    # Called only by explicitly admitted collect(), once, before any paid image intent.
    metadata.run(root, common.DISPATCH_ID, live_metadata=True, transport=transport)
    return verify_dispatch_metadata(root, freeze)


def verify_dispatch_metadata(root, freeze):
    value, available = metadata.validate(root, common.DISPATCH_ID)
    if value["requests"][1]["response_body_sha256"] != metadata.ENDPOINT_HASH:
        raise ValueError("dispatch endpoint identity differs")
    initial = namespace_state(root)
    if not initial["attempts"] and admission(initial, freeze["config"], available) != "admit":
        raise ValueError("initial full-grid allowance is unaffordable")
    return value, available


def collection_inputs(root, run_id):
    root = Path(root)
    freeze = verify(root, run_id)
    directory = root / common.directory(run_id)
    receipt = read_json(directory / "collection_receipt.json")
    required_outputs = {
        common.directory(run_id) / "generation_events.jsonl",
        common.directory(run_id) / "slot_outcomes.jsonl",
        common.WORKSPACE / run_id / "collection_started.json",
        metadata.directory(common.DISPATCH_ID) / "receipt.json",
        metadata.directory(common.DISPATCH_ID) / "started.json",
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
        receipt["schema"] != "painter-map-validation-collection/2"
        or receipt["run_id"] != run_id
        or receipt["freeze_sha256"] != hash_file(directory / "freeze.json")
        or receipt["budget"]["pending"]
        or receipt["budget"] != namespace_state(root)
        or receipt["status"] not in ("complete", "stopped")
        or (receipt["reason"] is None) != (receipt["status"] == "complete")
        or type(receipt["duration_contract_met"]) is not bool
        or type(receipt.get("identity_contract_met")) is not bool
        or type(receipt["elapsed_seconds"]) not in (float, int)
        or not math.isfinite(receipt["elapsed_seconds"])
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
        if (
            key[0] not in by_id
            or type(key[1]) is not int
            or key[1] not in (1, 2)
            or type(row["slot_sequence"]) is not int
        ):
            raise ValueError("unknown attempt identity")
        source = by_id[key[0]]
        if (
            row["slot_sequence"] != source["sequence"]
            or row["route"] != source["route"]
            or row.get("paid") is not True
        ):
            raise ValueError("transport/assignment identity mismatch")
        if row["kind"] == "attempt":
            expected = hashlib.sha256(json.dumps(source["payload"], sort_keys=True).encode())
            if (
                key in intents
                or row["payload_sha256"] != expected.hexdigest()
                or row["reserved_usd"] != 5
                or type(row["dispatch_ticket"]) is not int
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
            if key not in intents or key in terminals:
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
    halts = [r for r in operators if r["kind"] == "halt"]
    if len(halts) > 1:
        raise ValueError("multiple primary halt records")
    expected_reason = (
        halts[0]["reason"]
        if halts
        else (None if receipt["duration_contract_met"] else "collection_duration_contract_exceeded")
    )
    if receipt["reason"] != expected_reason or (receipt["status"] == "complete") != (
        expected_reason is None
    ):
        raise ValueError("terminal disposition differs from recorded halt/duration evidence")
    if not halts and any(
        row["cost_usd"] is None
        or row["cost_usd"] > freeze["config"]["request_reservation_usd"]
        or row["status"] in ("refused", "outcome_uncertain", "unsupported_success")
        or (
            row["status"] == "http_error"
            and (row["attempt"] == 2 or row.get("recognized_technical_error") is not True)
        )
        for row in terminals.values()
    ):
        raise ValueError("mandatory terminal stop lacks retained halt evidence")
    final_checks = [r for r in operators if r["kind"] == "final_identity_check"]
    if len(final_checks) != 1:
        raise ValueError("exactly one final source/endpoint check is required")
    final_check = final_checks[0]
    expected_identity = (
        final_check.get("source_verified") is True
        and final_check.get("endpoint_verified") is True
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
    _, available = verify_dispatch_metadata(root, freeze)
    if (
        receipt["available_at_dispatch_usd"] != str(available)
        or receipt["timing_contract_met"] != timing_contract(list(terminals.values()))
        or any(receipt.get(k) != v for k, v in eligibility(receipt).items())
    ):
        raise ValueError("timing/credit/complete-grid eligibility differs")
    # Verify each retained cost basis; no feature extraction is performed here.
    for row in terminals.values():
        if row.get("response_path"):
            body = response_bytes(root, run_id, row)
            if (row["cost_usd"], row["cost_basis"]) != cost_record(
                body, row["status_code"], row["complete"]
            ):
                raise ValueError(
                    "terminal cost differs from retained response and accounting basis"
                )
        elif row["status"] == "cancelled_before_post":
            if row["cost_usd"] != 0 or row["cost_basis"] != "cancelled_before_post":
                raise ValueError("invalid cancelled cost")
        elif row["cost_usd"] is not None or row["cost_basis"] != "unresolved":
            raise ValueError("unretained response cannot claim a known charge")
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
    scaler = reference_rows(root)["scaler"]
    from latent_art_bench.painter_feature_generation_v2.features import NAMES

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
            feature_names=list(NAMES),
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
                result["scaled"] = transform(values, scaler).tolist()
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
                schema="painter-map-validation-measurement/2",
                run_id=run_id,
                collection_receipt_sha256=hash_file(directory / "collection_receipt.json"),
                outputs=bindings(root, [p.relative_to(root) for p in outputs]),
            ),
        )
        return dict(
            status="measured_and_reported", run_id=run_id, status_summary=value.get("status")
        )


def check(root, run_id, *, pixels=False):
    root = Path(root)
    freeze, requests, slots, terminal, receipt = collection_inputs(root, run_id)
    directory = root / common.directory(run_id)
    measured = read_json(directory / "measurement_receipt.json")
    required_outputs = {
        common.directory(run_id) / "measurements.jsonl",
        common.REPORTS / run_id / "analysis.json",
        common.REPORTS / run_id / "REPORT.md",
        common.WORKSPACE / run_id / "measurement_started.json",
    }
    if (
        measured["schema"] != "painter-map-validation-measurement/2"
        or measured["run_id"] != run_id
        or hash_file(directory / "collection_receipt.json") != measured["collection_receipt_sha256"]
    ):
        raise ValueError("terminal collection receipt changed")
    if (
        len(measured["outputs"]) != len(required_outputs)
        or {Path(row["path"]) for row in measured["outputs"]} != required_outputs
    ):
        raise ValueError("measurement receipt output inventory differs")
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
        status_summary=value.get("status"),
        raw_response_access=True,
        feature_reextraction=pixels,
    )
