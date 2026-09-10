"""Prospective source freeze, terminal measurement and separate replay layers."""

import base64
import csv
import gzip
import hashlib
import importlib.metadata
import io
import json
import math
import platform
import subprocess
import tempfile
from pathlib import Path

import httpx
import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_study_v1 import study, transport
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

from . import analysis, common

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


def source_paths(root):
    paths = {
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
        common.CONFIG,
        common.METADATA,
        common.STUDIES / "PROTOCOL.md",
        study.CONFIG,
        Path("configs/painter_responsiveness_v2/study.json"),
        retained.REFERENCE,
        retained.MAIN / "reference_panel.jsonl",
        retained.MAIN / "scalers.json",
        common.BUDGET_RECEIPT,
        common.OLD_NAMING,
        common.OLD_PALETTE,
    }
    packages = (
        common.NAMESPACE,
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
    paths.update(p.relative_to(root) for p in (root / "tests" / common.NAMESPACE).glob("*.py"))
    paths.update(
        p.relative_to(root) for p in (root / retained.BASE).glob("*/generation_events.jsonl")
    )
    return sorted(paths)


def prepare(root, run_id, proxy_root):
    root = Path(root)
    directory = root / common.directory(run_id)
    if directory.exists() or (root / common.WORKSPACE / run_id).exists():
        raise ValueError("run identity already exists; never prepare over retained evidence")
    config = common.configuration(root)
    common.endpoint_record(root)
    paths = source_paths(root)
    commit = clean_commit(root, paths)
    budget = read_json(root / common.BUDGET_RECEIPT)["budget"]
    if (
        not math.isclose(budget["accounted_usd"], config["historical_accounted_usd"], abs_tol=1e-9)
        or budget["contingency_reserve_usd"] != 5
        or budget["unresolved"] != 0
        or budget["uncertain"] != 0
    ):
        raise ValueError(
            "historical conservative budget differs from the qualified terminal receipt"
        )
    proxy = transport.proxy_snapshot(proxy_root)
    inventory = common.requests(root, config)
    publish(directory / "planned_requests.jsonl", inventory, lines=True)
    value = dict(
        schema="painter-naming-replication-freeze/1",
        run_id=run_id,
        prepared_at_utc=utc_now().isoformat(),
        recorded_git_commit=commit,
        config=config,
        inputs=bindings(root, paths),
        environment=environment(),
        proxy_snapshot=proxy,
        requests_sha256=hash_file(directory / "planned_requests.jsonl"),
        budget_baseline_usd=budget["accounted_usd"],
        historical_budget=budget,
        scope="One fresh <=24h collection, no independent-backend or external-review claim",
    )
    publish(directory / "freeze.json", value)
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
    if set(source_paths(root)) != bound:
        raise ValueError("freeze input inventory differs")
    clean_commit(
        root, sorted(bound | {directory / "freeze.json", directory / "planned_requests.jsonl"})
    )
    verify_bindings(root, value["inputs"])
    if (
        value["run_id"] != run_id
        or value["config"] != common.configuration(root)
        or value["environment"] != environment()
    ):
        raise ValueError("freeze identity, configuration or runtime changed")
    path = root / directory / "planned_requests.jsonl"
    if hash_file(path) != value["requests_sha256"] or read_jsonl(path) != common.requests(root):
        raise ValueError("prospective request inventory changed")
    return value


def verify_live_metadata(root, freeze, proxy_root, *, transport=None):
    """Read-only endpoint and local process checks; no generation or pixel access."""
    pinned = read_json(root / common.METADATA)
    with httpx.Client(timeout=30, follow_redirects=False, transport=transport) as client:
        response = client.get(pinned["url"])
    response.raise_for_status()
    if response.json() != json.loads(pinned["response_body"]):
        raise ValueError("public paid endpoint identity/capability/pricing changed")
    if globals()["transport"].proxy_snapshot(proxy_root) != freeze["proxy_snapshot"]:
        raise ValueError("OAuth source/process identity changed")


def collection_inputs(root, run_id):
    freeze = verify(root, run_id)
    directory = root / common.directory(run_id)
    receipt = read_json(directory / "collection_receipt.json")
    verify_bindings(root, receipt["outputs"])
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
        if row["slot_sequence"] != source["sequence"] or row["route"] != source["route"]:
            raise ValueError("transport/assignment identity mismatch")
        if row["kind"] == "attempt":
            expected = hashlib.sha256(
                json.dumps(source["payload"], sort_keys=True).encode()
            ).hexdigest()
            if key in intents or row["payload_sha256"] != expected:
                raise ValueError("duplicate or altered request intent")
            intents[key] = row
        elif row["kind"] == "terminal":
            if key not in intents or key in terminals:
                raise ValueError("unpaired terminal")
            terminals[key] = row
        else:
            raise ValueError("unknown ledger event")
    if set(intents) != set(terminals) or receipt["attempts"] != len(terminals):
        raise ValueError("collection contains unresolved transport intents")
    for request, slot in zip(requests, slots, strict=True):
        if (slot["request_id"], slot["sequence"]) != (request["request_id"], request["sequence"]):
            raise ValueError("slot inventory reordered")
        successes = [
            r
            for (identity, _), r in terminals.items()
            if identity == request["request_id"] and r["status"] == "image_returned"
        ]
        if len(successes) > 1 or bool(successes) != (slot["status"] == "image_returned"):
            raise ValueError("slot selection differs from the first valid output rule")
        if successes:
            chosen = successes[0]
            if slot["selected_attempt"] != chosen["attempt"] or any(
                slot[k] != chosen[k] for k in ("response_path", "response_sha256", "observed")
            ):
                raise ValueError("selected output provenance differs")
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
            if (
                row["status"] == "image_returned"
                and transport.inspect_response(body) != row["observed"]
            ):
                raise ValueError("returned image metadata/hash differs")
            checked += 1
    return dict(status="raw_responses_verified", checked=checked, new_measurements=0)


def reference_rows(root):
    scalers = read_json(root / retained.MAIN / "scalers.json")
    rows = events(root / retained.REFERENCE)
    for row in rows:
        row["scaled"] = transform(
            np.asarray(row["values"]), scalers[row["pipeline"]]["scaler"]
        ).tolist()
    return rows


def _measure(root, run_id, requests, slots, terminals):
    scalers = read_json(root / retained.MAIN / "scalers.json")
    primary = scalers["primary512"]["scaler"]
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
                dict(
                    item,
                    pipeline=p,
                    status=slot["status"],
                    values=None,
                    scaled=None,
                    chroma_primary_iqr=None,
                )
                for p in study.PIPELINES
            )
            continue
        row = terminals[request["request_id"], slot["selected_attempt"]]
        body = response_bytes(root, run_id, row)
        if transport.inspect_response(body) != slot["observed"]:
            raise ValueError("selected image metadata differs")
        raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
        item["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory(prefix="measure-", dir=workspace) as temporary:
            path = Path(temporary) / "image.bin"
            path.write_bytes(raw)
            measured = measure_path(path, item, study.PIPELINES)
        for result in measured:
            if result["status"] == "measured":
                values = np.asarray(result["values"])
                result["scaled"] = transform(values, scalers[result["pipeline"]]["scaler"]).tolist()
                result["chroma_primary_iqr"] = float(
                    (values[2] - primary["center"][2]) / primary["scale"][2]
                )
            else:
                result.update(values=None, scaled=None, chroma_primary_iqr=None)
            rows.append(result)
    return rows


def _historical(root):
    naming = list(csv.DictReader(io.StringIO((root / common.OLD_NAMING).read_text())))
    palette = list(csv.DictReader(io.StringIO((root / common.OLD_PALETTE).read_text())))
    return dict(
        naming=[
            {k: r[k] for k in ("painter_id", "estimate", "raw_p", "holm_p", "pairs")}
            for r in naming
            if r["route"] == "flux_2_max" and r["after"] == "named"
        ],
        palette=palette,
        caveat="Old FLUX has 72 outputs per painter/arm; new counts and shared controls "
        "change finite-sample V-energy behavior and dependence. Magnitudes are "
        "descriptive comparisons, not a formal old/new equality test.",
    )


def result_value(root, requests, rows, config):
    value = analysis.analyze(requests, rows, reference_rows(root), config)
    value["historical"] = _historical(root)
    return value


def apply_collection_scope(value, receipt):
    if not receipt["duration_contract_met"]:
        for row in value["primary"]:
            row.update(
                status="withheld_collection_duration_contract",
                raw_p=None,
                holm_p=1.0,
                reject=False,
                interval=None,
            )
            if "directional_replication" in row:
                row["directional_replication"] = False
    value["collection"] = receipt
    return value


def report_text(value):
    lines = [
        "# Fresh finite-template naming replication",
        "",
        value["scope"],
        "",
        "Four fixed primary endpoints; unavailable p-values enter Holm as 1.",
        "",
        "| Endpoint | Estimate | Holm p | Interval | Status |",
        "|---|---:|---:|---|---|",
    ]
    for row in value["primary"]:
        lines.append(
            f"| {row['endpoint']} | {row['estimate']} | {row['holm_p']} | "
            f"{row['interval']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "Palette intervals are 98.75% marginal intervals allocated within the four-endpoint "
            "family. Naming effects have no confidence interval. "
            "Palette nominal control intervals remain 95%.",
            "",
            value["component_diagnostics_scope"],
            "",
            value["historical"]["caveat"],
            "",
            "Historical palette interactions were unresolved; "
            "a new null result does not establish equivalence. Failed controls remove no images.",
            "",
            "`analysis.json` includes weighted gap/spread/coverage summaries, shared-control "
            "covariance, all contribution identities and old/new estimates. `measurements.jsonl` "
            "retains every allocated slot under all three fixed pipelines.",
            "",
            "`check` replays retained numbers only. "
            "`verify-responses` verifies raw transport/image hashes. "
            "`check-pixels` re-extracts retained generated pixels. Local replay is not "
            "evidence of public availability or independent external replication.",
            "",
        ]
    )
    return "\n".join(lines)


def measure(root, run_id):
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".measurement.lock"):
        freeze, requests, slots, terminal, receipt = collection_inputs(root, run_id)
        directory = root / common.directory(run_id)
        marker = root / common.WORKSPACE / run_id / "measurement_started.json"
        publish(marker, dict(started_at_utc=utc_now().isoformat(), one_shot=True))
        rows = _measure(root, run_id, requests, slots, terminal)
        value = result_value(root, requests, rows, freeze["config"])
        apply_collection_scope(value, receipt)
        report = root / common.REPORTS / run_id
        publish(directory / "measurements.jsonl", rows, lines=True)
        publish(report / "analysis.json", value)
        with (report / "REPORT.md").open("x", encoding="utf-8") as handle:
            handle.write(report_text(value))
        outputs = [directory / "measurements.jsonl", report / "analysis.json", report / "REPORT.md"]
        publish(
            directory / "measurement_receipt.json",
            dict(
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
    if hash_file(directory / "collection_receipt.json") != measured["collection_receipt_sha256"]:
        raise ValueError("terminal collection receipt changed")
    verify_bindings(root, measured["outputs"])
    rows = read_jsonl(directory / "measurements.jsonl")
    if pixels and _measure(root, run_id, requests, slots, terminal) != rows:
        raise ValueError("pixel measurement replay differs")
    value = result_value(root, requests, rows, freeze["config"])
    apply_collection_scope(value, receipt)
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
