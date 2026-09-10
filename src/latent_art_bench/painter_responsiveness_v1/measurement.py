"""Measure a closed, gate-bound collection without selecting successful treatments.

Only retained response entities are decoded. This module has no transport entry
point, never fits a scaler, and never fills an unavailable planned endpoint.
"""

from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import json
import math
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_study_v1.measurement import measure_path
from latent_art_bench.painter_distribution_study_v1.study import PIPELINES
from latent_art_bench.painter_distribution_study_v1.transport import inspect_response
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    confined,
    digest,
    events,
    publish,
    stage_lock,
)
from latent_art_bench.painter_feature_generation_v2.statistics import transform

from . import collection, common, design, inference, workflow

SCALERS = retained.MAIN / "scalers.json"
OUTPUTS = ("generated_features.jsonl", "factorial_results.json", "measurement_receipt.json")
IDENTITIES = ("request_id", "sequence", "block_id", "template_id", "repetition", "arm",
              "polarity", "within_block", "content_class", "fine_subject", "route")


def _required_sources():
    paths = {SCALERS, common.CONFIG, Path("pyproject.toml"), Path("uv.lock")}
    paths.update(common.PACKAGE / name for name in (
        "measurement.py", "inference.py", "design.py", "common.py", "workflow.py",
        "collection.py", "generation_prepare.py",
    ))
    paths.update(Path("src/latent_art_bench") / name for name in (
        "io.py", "painter_feature_generation_v2/artifacts.py",
        "painter_feature_generation_v2/features.py", "painter_feature_generation_v2/statistics.py",
        "painter_distribution_study_v1/measurement.py", "painter_distribution_study_v1/study.py",
        "painter_distribution_study_v1/transport.py", "painter_distribution_revision_v1/common.py",
    ))
    return paths


def _ledger(root, directory, requests, receipt):
    """Check the chain and treatment/attempt bindings before trusting slot selection."""
    ledger = root / directory / "generation_events.jsonl"
    actual = hash_file(ledger) if ledger.exists() else None
    if actual != receipt["generation_events_sha256"]:
        raise ValueError("collection ledger differs from its terminal receipt")
    planned = {r["request_id"]: r for r in requests}
    intents, terminals = {}, {}
    for row in events(ledger):
        if row.get("request_id") not in planned or row.get("attempt") not in (1, 2):
            raise ValueError("undeclared collection attempt identity")
        request = planned[row["request_id"]]
        if (row.get("slot_sequence"), row.get("route")) != (
            request["sequence"], request["route"]
        ):
            raise ValueError("collection attempt does not match its treatment slot")
        key = row["request_id"], row["attempt"]
        if row["kind"] == "attempt":
            if key in intents or key in terminals:
                raise ValueError("duplicate collection attempt intent")
            if (row.get("request_sha256") != digest(request)
                    or row.get("payload_sha256") != digest(request["payload"])):
                raise ValueError("collection attempted a different frozen request")
            intents[key] = row
        elif row["kind"] == "terminal":
            if key not in intents or key in terminals:
                raise ValueError("unpaired or repeated terminal collection event")
            if row["status"] == "image_returned" and row.get("complete") is not True:
                raise ValueError("a selected image requires a complete retained entity")
            terminals[key] = row
        else:
            raise ValueError("undeclared collection ledger event")
    if (len(intents) != receipt["attempt_intents"]
            or len(terminals) != receipt["terminal_attempts"]
            or sum(r["attempt"] > 1 for r in terminals.values())
            != receipt["technical_retries_dispatched"]):
        raise ValueError("terminal collection attempt accounting changed")
    return collection._slot_outcomes(requests, list(terminals.values()), list(intents.values()))


def verify_collection(root, run_id):
    """Verify both committed freezes, terminal allocation and fixed scaler identity.

    A stopped terminal collection can be described. Its unavailable allocations
    remain unavailable and prevent primary inference; no collection is resumed.
    This verifier reads compact artifacts, not response/image bytes.
    """
    freeze, requests = collection.verify_generation(root, run_id)
    source = workflow.verify(root, freeze["diagnostic_run_id"])
    for bound in (freeze, source):
        if not _required_sources().issubset({Path(r["path"]) for r in bound["inputs"]}):
            raise ValueError("both freezes must bind measurement, inference and frozen scalers")
    margin = freeze.get("meaningful_margin_primary_iqr")
    precision = freeze.get("precision", {})
    if (type(margin) not in (int, float) or not math.isfinite(margin) or margin <= 0
            or precision.get("margin_status") != "validated"
            or precision.get("decision") != "proceed"
            or precision.get("meaningful_margin_primary_iqr") != margin):
        raise ValueError("a validated meaningful margin must be frozen before collection")
    directory = common.directory(run_id)
    receipt = read_json(root / directory / "collection_receipt.json")
    if (receipt.get("schema") != "painter-responsiveness-collection/1"
            or receipt.get("run_id") != run_id or receipt.get("terminal") is not True
            or receipt.get("status") not in ("completed", "stopped")
            or receipt.get("total_planned") != 192 or len(requests) != 192
            or receipt.get("recorded_git_commit") != freeze["recorded_git_commit"]
            or receipt.get("new_feature_measurements") != 0):
        raise ValueError("a closed 192-slot collection receipt is required before measurement")
    for key, name in (("generation_freeze_sha256", "generation_freeze.json"),
                      ("requests_sha256", "planned_requests.jsonl"),
                      ("slot_outcomes_sha256", "slot_outcomes.jsonl")):
        if receipt[key] != hash_file(root / directory / name):
            raise ValueError("collection receipt binding changed: " + name)
    slots = read_jsonl(root / directory / "slot_outcomes.jsonl")
    if slots != _ledger(root, directory, requests, receipt):
        raise ValueError("selected slot outcomes do not reproduce the complete terminal ledger")
    if dict(Counter(r["status"] for r in slots)) != receipt["status_counts"]:
        raise ValueError("terminal status denominators changed")
    scalers = read_json(root / SCALERS)
    if set(scalers) != set(PIPELINES):
        raise ValueError("all three previously frozen development scalers are required")
    for pipeline in PIPELINES:
        scaler = scalers[pipeline]["scaler"]
        center, scale = np.asarray(scaler["center"]), np.asarray(scaler["scale"])
        if (center.shape != (31,) or scale.shape != (31,)
                or not np.isfinite(center).all() or not np.isfinite(scale).all()
                or np.any(scale <= 0)):
            raise ValueError("invalid frozen development scaler")
    return freeze, requests, slots, receipt, scalers


def _selected_bytes(root, run_id, slot):
    """Verify compressed, entity and embedded-image hashes without fetching URLs."""
    expected = (common.WORKSPACE / run_id / "responses"
                / f"{slot['sequence']:04d}-a{slot['selected_attempt']}.json.gz")
    if slot["response_path"] != str(expected):
        raise ValueError("selected response has a noncanonical retained path")
    path = confined(root, expected, common.WORKSPACE / run_id / "responses")
    if hash_file(path) != slot["stored_response_sha256"]:
        raise ValueError("selected compressed response changed")
    with gzip.open(path, "rb") as handle:
        body = handle.read(collection.MAX_RESPONSE + 1)
    if len(body) > collection.MAX_RESPONSE:
        raise ValueError("retained response exceeds the frozen entity bound")
    if hashlib.sha256(body).hexdigest() != slot["response_sha256"]:
        raise ValueError("selected response entity changed")
    data = json.loads(body)
    entries = data.get("data") if isinstance(data, dict) else None
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise ValueError("selected response lacks exactly one embedded image")
    encoded = entries[0].get("b64_json")
    if not isinstance(encoded, str):
        raise ValueError("selected response must contain retained base64 image bytes")
    raw = base64.b64decode(encoded, validate=True)
    observed = slot["observed"]
    if (hashlib.sha256(raw).hexdigest() != observed["image_sha256"]
            or len(raw) != observed["image_bytes"]):
        raise ValueError("selected image bytes changed")
    return body, raw


def _measure_slot(root, run_id, request, slot, scalers, temporary):
    item = {key: request[key] for key in IDENTITIES}
    item.update(image_id=f"{run_id}:{request['request_id']}",
                payload_sha256=digest(request["payload"]), collection_status=slot["status"],
                selected_attempt=slot["selected_attempt"], attempt_count=slot["attempt_count"],
                selected_terminal_event_sha256=slot["selected_terminal_event_sha256"],
                source_response_path=slot["response_path"],
                source_response_sha256=slot["response_sha256"],
                source_stored_response_sha256=slot["stored_response_sha256"])
    if slot["status"] != "image_returned":
        return [dict(item, pipeline=p, status=slot["status"], values=None, scaled=None,
                     chroma_primary_iqr=None) for p in PIPELINES]
    body, raw = _selected_bytes(root, run_id, slot)
    if inspect_response(body) != slot["observed"]:
        raise ValueError("retained image metadata differs from its selected terminal event")
    item["raw_sha256"] = slot["observed"]["image_sha256"]
    with tempfile.TemporaryDirectory(prefix="decode-", dir=temporary) as directory:
        path = Path(directory) / "image.bin"
        path.write_bytes(raw)
        rows = measure_path(path, item, PIPELINES)
    if [r.get("pipeline") for r in rows] != list(PIPELINES):
        raise ValueError("the frozen extractor did not return all three pipelines in order")
    for row in rows:
        if any(row.get(k) != value for k, value in item.items()):
            raise ValueError("the frozen extractor changed measurement provenance")
        if row["status"] == "measured":
            values = np.asarray(row["values"], dtype=float)
            if values.shape != (31,) or not np.isfinite(values).all():
                raise ValueError("the extractor returned an invalid measured vector")
            row["scaled"] = transform(values, scalers[row["pipeline"]]["scaler"]).tolist()
            # A common scale permits a processing comparison without changing the unit.
            primary = scalers["primary512"]["scaler"]
            row["chroma_primary_iqr"] = float(
                (values[2] - primary["center"][2]) / primary["scale"][2])
        elif row["status"] == "failed":
            row.update(values=None, scaled=None, chroma_primary_iqr=None)
        else:
            raise ValueError("the frozen extractor returned an undeclared measurement status")
    return rows


def _sensitivity(requests, rows):
    """Only complete-block arithmetic; no additional tests or confidence intervals."""
    output = []
    for pipeline in PIPELINES:
        by_id = {r["request_id"]: r for r in rows if r["pipeline"] == pipeline}
        for block_id in dict.fromkeys(r["block_id"] for r in requests):
            wanted = [r for r in requests if r["block_id"] == block_id]
            measured = [by_id[r["request_id"]] for r in wanted]
            row = dict(pipeline=pipeline, block_id=block_id,
                       template_id=wanted[0]["template_id"], repetition=wanted[0]["repetition"],
                       request_ids=[r["request_id"] for r in wanted], allocated=8,
                       measured=sum(r["status"] == "measured" for r in measured))
            if row["measured"] == 8:
                values = {(r["arm"], r["polarity"]): r["chroma_primary_iqr"] for r in measured}
                response = {arm: values[arm, "vivid"] - values[arm, "muted"]
                            for arm in design.ARMS}
                row.update(responses=response,
                           monet_minus_generic=response["monet"] - response["generic"],
                           cezanne_minus_generic=response["cezanne"] - response["generic"])
            else:
                row.update(responses=None, monet_minus_generic=None, cezanne_minus_generic=None)
            output.append(row)
    return output


def _meaningful_interactions(factorial, margin):
    """Compare existing family intervals with the frozen interaction threshold only."""
    output = []
    for row in factorial.get("primary") or []:
        interval = row["family_interval"]
        status = "unavailable"
        if interval is not None:
            status = ("interval_beyond_negative_margin" if interval[1] < -margin else
                      "interval_excludes_negative_margin" if interval[0] > -margin else
                      "unresolved_at_negative_margin")
        output.append(dict(contrast=row["contrast"], meaningful_margin_primary_iqr=margin,
                           negative_threshold=-margin, estimate=row["estimate"],
                           family_interval=interval, status=status))
    return output


def _csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: json.dumps(value, ensure_ascii=False, sort_keys=True,
                                          allow_nan=False) if isinstance(value, (list, dict))
                         else value for key, value in row.items()} for row in rows)


def _report(result, rows, directory):
    """Render exact numeric outputs; never rerun inference or change memberships."""
    directory.mkdir(parents=True, exist_ok=False)
    primary = result["factorial"]
    tables = {
        "feature_rows": rows, "availability": primary["availability"],
        "cell_means": primary["cells"], "arm_means": primary["arm_means"],
        "primary": primary.get("primary") or [],
        "responses": primary.get("responses", []),
        "secondary_named_minus_free": primary.get("secondary_named_minus_free", []),
        "generic_minus_free": primary.get("generic_minus_free", []),
        "manipulation_checks": primary.get("manipulation_checks", []),
        "meaningful_interactions": result["meaningful_interactions"],
        "processing_blocks": result["processing_blocks"],
        "complete_block_survivors": primary.get("complete_block_descriptive", {}).get(
            "templates", []),
    }
    for name, table in tables.items():
        _csv(directory / (name + ".csv"), table)
    text = [
        "# Painter responsiveness: terminal factorial results", "",
        f"Primary inference status: `{primary['status']}`. "
        f"The collection ended `{result['collection_status']}`; all 192 allocated slots "
        "remain in the 576-row, three-pipeline feature table.", "",
        "The primary coordinate is median chroma after primary512 processing, scaled by "
        "the previously frozen development IQR. Responses are vivid minus muted. The two "
        "primary interactions subtract the shared generic response from each named-painter "
        "response. Templates have equal weight; the same generic draws enter both contrasts.",
        "", f"Frozen meaningful interaction margin: "
        f"{result['meaningful_margin_primary_iqr']:.9g} primary development-IQR units. "
        "This is the interaction planning/precision threshold, not the arm-response threshold. "
        "The manipulation checks assess positive vivid-minus-muted responses against zero. "
        "Generated-output human judgments are pending; "
        "numerical response differences alone do not establish a perceptual or internal-model "
        "mechanism.", "",
        "| Arm | Polarity | Allocated | Measured |", "| --- | --- | ---: | ---: |",
    ]
    for row in primary["availability"]:
        text.append(f"| {row['arm']} | {row['polarity']} | {row['allocated']} | "
                    f"{row['measured']} |")
    if primary.get("primary"):
        text += ["", "| Primary interaction | Estimate | Family interval | Holm p |",
                 "| --- | ---: | --- | ---: |"]
        for row in primary["primary"]:
            interval = row["family_interval"]
            rendered = (f"[{interval[0]:.6g}, {interval[1]:.6g}]"
                        if interval is not None else "unavailable")
            p = f"{row['p_holm']:.6g}" if row["p_holm"] is not None else "unavailable"
            text.append(f"| {row['contrast']} | {row['estimate']:.6g} | {rendered} | {p} |")
    else:
        text += ["", "Primary inference is withheld because at least one allocated primary "
                 "measurement is unavailable. Complete-block survivors are selected descriptions; "
                 "they do not recover the effect for the originally allocated grid."]
    text += ["", "`meaningful_interactions.csv` compares the already reported family intervals "
             "with the negative meaningful-interaction margin. An interval lies beyond the "
             "margin only if its upper endpoint is below the negative threshold; it excludes "
             "that magnitude if its lower endpoint is above the threshold. Otherwise its "
             "classification is unresolved or unavailable. This adds no new interval, p-value "
             "or multiplicity family and does not establish perceptual meaning."]
    text += ["", *primary["assumptions"], "", result["processing_scope"], "",
             "Full-precision numbers, per-slot sources and every unavailable outcome are retained "
             "in the JSON and CSV outputs. The receipt binds collection inputs, scalers, outputs "
             "and report bytes. Any review documented here is maintainer-run LLM review unless "
             "explicitly identified otherwise.", ""]
    (directory / "REPORT.md").write_text("\n".join(text), encoding="utf-8")
    return sorted(p for p in directory.iterdir() if p.is_file())


def measure(root, run_id):
    """Create one measurement publication; interrupted stages are never resumed in place."""
    root = Path(root)
    with stage_lock(root / common.WORKSPACE / ".measurement.lock"):
        freeze, requests, slots, collection_receipt, scalers = verify_collection(root, run_id)
        directory = root / common.directory(run_id)
        workspace = root / common.WORKSPACE / run_id
        marker = workspace / "measurement_started.json"
        report_dir = root / common.REPORTS / run_id
        if marker.exists() or report_dir.exists() or any((directory / p).exists() for p in OUTPUTS):
            raise ValueError("measurement is terminal or interrupted; use a disjoint study run")
        # Fail on all selected byte-identity mismatches before opening any image for extraction.
        for slot in slots:
            if slot["status"] == "image_returned":
                _selected_bytes(root, run_id, slot)
        source_paths = [common.directory(run_id) / name for name in (
            "generation_freeze.json", "planned_requests.jsonl", "collection_receipt.json",
            "slot_outcomes.jsonl",
        )]
        if (directory / "generation_events.jsonl").exists():
            source_paths.append(common.directory(run_id) / "generation_events.jsonl")
        source_paths += [SCALERS, common.directory(freeze["diagnostic_run_id"]) / "freeze.json"]
        source_paths += [Path(s["response_path"]) for s in slots if s["status"] == "image_returned"]
        inputs = bindings(root, source_paths)
        publish(marker, dict(run_id=run_id, collection_receipt_sha256=hash_file(
            directory / "collection_receipt.json"), inputs=inputs))
        workspace.mkdir(parents=True, exist_ok=True)
        rows = []
        for request, slot in zip(requests, slots, strict=True):
            rows.extend(_measure_slot(root, run_id, request, slot, scalers, workspace))
        primary = [dict(request_id=r["request_id"], status=r["status"],
                        value=r["scaled"][2] if r["status"] == "measured" else None)
                   for r in rows if r["pipeline"] == "primary512"]
        factorial = inference.analyze_factorial(
            requests, primary, alpha=freeze["config"]["alpha"],
            manipulation_margin=0.0)
        result = dict(
            schema="painter-responsiveness-factorial/1", run_id=run_id,
            collection_status=collection_receipt["status"],
            collection_stop_reason=collection_receipt["stop_reason"],
            meaningful_margin_primary_iqr=freeze["meaningful_margin_primary_iqr"],
            manipulation_margin_primary_iqr=0.0,
            meaningful_interactions=_meaningful_interactions(
                factorial, freeze["meaningful_margin_primary_iqr"]),
            primary_pipeline="primary512", feature_index=2, feature_name="chroma_median",
            factorial=factorial, processing_blocks=_sensitivity(requests, rows),
            processing_scope="Processing summaries use a common primary-development chroma "
            "IQR for all three pipelines. They retain every block and its eight identities; "
            "incomplete blocks have no interaction. These are descriptive arithmetic, with no "
            "additional tests or intervals. Per-pipeline scaled full vectors are also retained.",
            human=dict(status="generated_output_judgments_pending", ratings=0),
        )
        # Recheck compact and retained-byte bindings before sealing any result.
        if bindings(root, source_paths) != inputs:
            raise ValueError("measurement input changed during execution")
        verify_collection(root, run_id)
        publish(directory / OUTPUTS[0], rows, lines=True)
        publish(directory / OUTPUTS[1], result)
        reports = _report(result, rows, report_dir)
        receipt = dict(
            schema="painter-responsiveness-measurement/1", run_id=run_id, terminal=True,
            recorded_git_commit=freeze["recorded_git_commit"], inputs=inputs,
            collection_receipt_sha256=hash_file(directory / "collection_receipt.json"),
            generated_features_sha256=hash_file(directory / OUTPUTS[0]),
            factorial_results_sha256=hash_file(directory / OUTPUTS[1]),
            reports=bindings(root, [p.relative_to(root) for p in reports]),
            allocated_slots=192, feature_rows=len(rows),
            measurements_by_pipeline={
                p: dict(Counter(r["status"] for r in rows if r["pipeline"] == p))
                for p in PIPELINES},
            primary_inference_status=factorial["status"], new_generation_calls=0,
            human_judgments=0,
        )
        publish(directory / OUTPUTS[2], receipt)
        return dict(status="published", run_id=run_id, feature_rows=len(rows),
                    primary_inference_status=factorial["status"],
                    report=str((report_dir / "REPORT.md").relative_to(root)))


# The existing module CLI uses build; programmatic callers may use measure.
build = measure
