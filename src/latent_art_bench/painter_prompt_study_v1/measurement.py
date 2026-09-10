"""Measure new retained responses with the sealed 512-pixel, 31-coordinate pipeline."""

from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.io import canonical_json, hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2 import features, pipeline
from latent_art_bench.painter_feature_generation_v2.artifacts import digest, publish, stage_lock
from latent_art_bench.painter_feature_generation_v2.oauth_generate import decode

from . import generation
from .common import MANIFESTS, WORKSPACE

SHORT_SIDE = 512
SOURCE_FILES = (
    "generation_freeze.json", "generation_receipt.json", "generation_events.jsonl",
    "requests.jsonl", "outputs.jsonl", "prompts.json",
)


def _source(root: Path, run_id: str):
    directory, freeze, requests = generation._load(root, run_id)
    receipt = read_json(directory / "generation_receipt.json")
    journal = generation._Journal(directory / "generation_events.jsonl")
    attempts, terminals = generation._state(journal.rows, requests)
    outputs = read_jsonl(directory / "outputs.jsonl")
    if (
        receipt["run_id"] != run_id or receipt["terminal"] is not True
        or receipt["freeze_sha256"] != hash_file(directory / "generation_freeze.json")
        or receipt["ledger_sha256"] != hash_file(journal.path)
        or receipt["outputs_sha256"] != hash_file(directory / "outputs.jsonl")
        or receipt["expected_requests"] != len(requests)
        or receipt["terminal_requests"] != len(requests)
        or len(terminals) != len(requests)
        or len({r["request_id"] for r in requests}) != len(requests)
        or receipt["image_attempts"] != len(attempts)
        or outputs != [terminals[r["request_id"]] for r in requests]
        or receipt["statuses"] != dict(Counter(r["status"] for r in outputs))
        or receipt["complete_generated_grid"] is not all(
            r["status"] == "generated" for r in outputs)
    ):
        raise ValueError("terminal generation evidence or accounting changed")
    config = freeze["config"]
    if (config.get("short_side", SHORT_SIDE) != SHORT_SIDE
            or config["minimum_decoded_short_side"] != SHORT_SIDE
            or type(config["maximum_response_bytes"]) is not int
            or not 0 < config["maximum_response_bytes"] <= generation.MAX_RESPONSE_BYTES):
        raise ValueError("measurement requires the frozen 512-pixel and bounded-response contract")
    sources = [{"path": (MANIFESTS / run_id / name).as_posix(),
                "sha256": hash_file(directory / name)} for name in SOURCE_FILES]
    return directory, freeze, requests, outputs, sources


def _response_bytes(root: Path, run_id: str, row: dict, limit: int) -> bytes:
    path = generation._response_path(root, run_id, row)
    if hash_file(path) != row["stored_sha256"]:
        raise ValueError("retained compressed response changed")
    with gzip.open(path, "rb") as handle:
        body = handle.read(limit + 1)
    if len(body) > limit:
        raise ValueError("retained response exceeds the frozen byte ceiling")
    if (len(body) != row["bytes"] or path.stat().st_size != row["stored_bytes"]
            or hashlib.sha256(body).hexdigest() != row["response_sha256"]):
        raise ValueError("retained raw response bytes or digest changed")
    return body


def _identity(request: dict, output: dict, run_id: str) -> dict:
    return dict(
        generation._identity(request), sequence=request["sequence"],
        image_id=request["request_id"], stage="generated", domain="generated", run_id=run_id,
        generation_status=output["status"], source_output_sha256=digest(output),
    )


def _measure(root: Path, run_id: str, request: dict, output: dict, limit: int) -> dict:
    result = _identity(request, output, run_id)
    if output["status"] != "generated":
        return dict(result, status="not_generated")
    body = _response_bytes(root, run_id, output, limit)
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("generated response must remain a JSON object")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        image, _ = decode(payload, request, SHORT_SIDE)
    if hashlib.sha256(image).hexdigest() != output["sha256"]:
        raise ValueError("decoded image hash differs from terminal generation evidence")
    if len(image) != output["decoded_bytes"]:
        raise ValueError("decoded image size differs from terminal generation evidence")
    temporary = root / WORKSPACE / run_id / "measurement_tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=temporary, suffix=".image") as handle:
        handle.write(image)
        handle.flush()
        measured = pipeline.measure_one(
            dict(result, path=handle.name, raw_sha256=output["sha256"]), SHORT_SIDE
        )
    # The shared function intentionally knows no prompt-method fields; retain them here.
    return dict(result, **{k: v for k, v in measured.items() if k not in result})


def _validate_row(row: dict, request: dict, output: dict, run_id: str) -> None:
    if any(row.get(k) != v for k, v in _identity(request, output, run_id).items()):
        raise ValueError("measurement prefix differs from its ordered source outputs")
    if output["status"] != "generated":
        if row.get("status") != "not_generated" or "values" in row:
            raise ValueError("nongenerated source acquired an invalid measurement disposition")
        return
    if row.get("status") not in {"measured", "failed"} or row.get("raw_sha256") != output["sha256"]:
        raise ValueError("invalid generated measurement disposition or source image digest")
    if row["status"] == "failed":
        if "values" in row or not isinstance(row.get("error"), str):
            raise ValueError("failed measurement has invalid feature or error fields")
        return
    values = np.asarray(row["values"], dtype=float)
    if (values.shape != (31,) or not np.isfinite(values).all()
            or row["feature_sha256"] != digest(row["values"])
            or row["normalization"]["short_side"] != SHORT_SIDE):
        raise ValueError("measurement feature digest or 31-coordinate contract changed")


def measure(root: Path, run_id: str, *, max_new_records: int | None = None) -> dict:
    """Complete or resume a nonterminal measurement stage; never rerun terminal dispositions."""
    if max_new_records is not None and (type(max_new_records) is not int or max_new_records < 0):
        raise ValueError("max_new_records must be a nonnegative integer")
    root = Path(root).resolve()
    directory, freeze, requests, outputs, sources = _source(root, run_id)
    limit = freeze["config"]["maximum_response_bytes"]
    with stage_lock(root / WORKSPACE / run_id / ".measurement.writer.lock"):
        terminal_path = directory / "measurement_receipt.json"
        if terminal_path.exists():
            raise FileExistsError("measurement stage is permanently terminal")
        journal = generation._Journal(directory / "measurement_events.jsonl")
        binding = dict(kind="stage_start", run_id=run_id, inputs=sources,
                       short_side=SHORT_SIDE, feature_names=list(features.NAMES))
        if journal.rows:
            if any(journal.rows[0].get(k) != v for k, v in binding.items()):
                raise ValueError("measurement source bindings changed during a nonterminal stage")
        else:
            journal.append(binding)
        prior_events = journal.rows[1:]
        if len(prior_events) > len(outputs):
            raise ValueError("measurement prefix exceeds the registered population")
        measured = []
        for index, event in enumerate(prior_events):
            if event.get("kind") != "terminal" or not isinstance(event.get("row"), dict):
                raise ValueError("invalid measurement terminal event")
            row = event["row"]
            _validate_row(row, requests[index], outputs[index], run_id)
            if outputs[index]["status"] == "generated":
                _response_bytes(root, run_id, outputs[index], limit)
            measured.append(row)
        start = len(measured)
        for index in range(start, len(outputs)):
            if max_new_records is not None and index - start >= max_new_records:
                return dict(run_id=run_id, terminal=False, status="paused_batch_limit",
                            expected_records=len(outputs), terminal_records=len(measured),
                            statuses=dict(Counter(row["status"] for row in measured)))
            row = _measure(root, run_id, requests[index], outputs[index], limit)
            _validate_row(row, requests[index], outputs[index], run_id)
            journal.append(dict(kind="terminal", row=row))
            measured.append(row)
        feature_path = directory / "measured_features.jsonl"
        if feature_path.exists():
            expected = "".join(canonical_json(row) + "\n" for row in measured).encode("utf-8")
            if feature_path.read_bytes() != expected:
                raise ValueError("unreceipted feature file differs from measurement ledger")
        else:
            publish(feature_path, measured, lines=True)
        receipt = dict(
            schema_version="painter-prompt-study-measurement-receipt/1.0",
            run_id=run_id, stage="generated", terminal=True, status="complete",
            expected_records=len(outputs), terminal_records=len(measured),
            statuses=dict(Counter(row["status"] for row in measured)),
            complete_measured_grid=all(row["status"] == "measured" for row in measured),
            short_side=SHORT_SIDE, feature_names=list(features.NAMES), inputs=sources,
            freeze_sha256=hash_file(directory / "generation_freeze.json"),
            generation_receipt_sha256=hash_file(directory / "generation_receipt.json"),
            outputs_sha256=hash_file(directory / "outputs.jsonl"),
            feature_file_sha256=hash_file(feature_path), ledger_sha256=hash_file(journal.path),
            completed_at_utc=utc_now().isoformat(),
        )
        publish(terminal_path, receipt)
        return receipt
