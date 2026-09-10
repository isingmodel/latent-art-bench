"""Offline diagnosis of sealed access responses, without changing their terminal outcomes."""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    bindings,
    confined,
    identifier,
    publish,
    verify_bindings,
)

SELF = Path("src/latent_art_bench/painter_feature_generation_v2/assessment_diagnostics.py")


def inspect_payload(payload: dict, requested: dict) -> dict:
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1:
        raise ValueError("not a single-image response")
    raw = base64.b64decode(data[0]["b64_json"], validate=True)
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        decoded_size = f"{image.width}x{image.height}"
        decoded_format = image.format.lower()
        opaque = not (
            ("A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255))
            or (image.mode == "P" and "transparency" in image.info)
        )
        image_info = dict(
            decoded_width=image.width,
            decoded_height=image.height,
            decoded_format=decoded_format,
            mode=image.mode,
            opaque=opaque,
            image_sha256=hashlib.sha256(raw).hexdigest(),
            decoded_rgb_sha256=hashlib.sha256(image.convert("RGB").tobytes()).hexdigest(),
        )
    mismatches = []
    if decoded_size != requested["size"]:
        mismatches.append("decoded_size_differs_from_requested")
    if decoded_format != requested["output_format"]:
        mismatches.append("decoded_format_differs_from_requested")
    if not opaque and requested.get("background") == "opaque":
        mismatches.append("nonopaque_output")
    for field in ("quality", "size", "output_format", "background"):
        if field in payload and payload[field] != requested.get(field):
            mismatches.append(f"reported_{field}_differs_from_requested")
    return dict(
        **image_info,
        image_bytes_returned_and_decodable=True,
        requested={k: requested[k] for k in ("model", "quality", "size", "output_format")},
        reported={
            k: payload.get(k)
            for k in ("model", "quality", "size", "output_format", "background", "usage")
        },
        mismatches=mismatches,
        requested_contract_satisfied=not mismatches,
        model_identity_independently_verified=False,
        note="Reported quality is provider metadata, not a measured visual-quality score.",
    )


def diagnose(root: Path, run_id: str) -> dict:
    relative = MANIFESTS / identifier(run_id)
    receipt_path = relative / "assessment_receipt.json"
    frozen_path = relative / "assessment_freeze.json"
    requests_path = relative / "requests.jsonl"
    receipt, freeze = read_json(root / receipt_path), read_json(root / frozen_path)
    verify_bindings(root, freeze["inputs"])
    if hash_file(root / frozen_path) != receipt["assessment_freeze_sha256"]:
        raise ValueError("access freeze changed")
    if hash_file(root / requests_path) != freeze["requests_sha256"]:
        raise ValueError("access requests changed")
    requests = {r["request_id"]: r for r in read_jsonl(root / requests_path)}
    inputs, rows = [SELF, receipt_path, frozen_path, requests_path], []
    for outcome in receipt["outcomes"]:
        row = dict(
            model=outcome["model"],
            terminal_access_status=outcome["status"],
            attempted=outcome["attempted"],
        )
        response = outcome.get("response", {})
        if response.get("raw_path"):
            raw_path = confined(root, response["raw_path"], WORKSPACE / run_id)
            if hash_file(raw_path) != response["raw_sha256"]:
                raise ValueError("retained response changed")
            inputs.append(raw_path.relative_to(root))
            row.update(
                http_status=response["http_status"], latency_seconds=response["latency_seconds"]
            )
            if response["http_status"] == 200:
                row.update(
                    inspect_payload(read_json(raw_path), requests[outcome["request_id"]]["payload"])
                )
        rows.append(row)
    report = dict(
        run_id=run_id,
        analysis_kind="posthoc_transport_diagnosis_not_painter_fidelity",
        inputs=bindings(root, inputs),
        outcomes=rows,
        decoded_images=sum(r.get("image_bytes_returned_and_decodable", False) for r in rows),
        contract_compliant_images=sum(r.get("requested_contract_satisfied", False) for r in rows),
        terminal_evidence_rewritten=False,
        generated_at_utc=utc_now().isoformat(),
    )
    publish(root / relative / "response_diagnostics.json", report)
    return report
