"""Frozen 31-feature pipelines with development-only scaling and retained failures."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.statistics import fit_scaler, transform

from . import study as s
from . import transport as t
from .collection import read_response


def jpeg_sensitivity(rgb):
    pixels = np.floor(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(
        buffer, format="JPEG", quality=90, subsampling=2, optimize=False, progressive=False
    )
    raw = buffer.getvalue()
    with Image.open(io.BytesIO(raw)) as image:
        decoded = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    return decoded, hashlib.sha256(raw).hexdigest()


def measure_path(path, item, pipelines):
    rows = []
    for pipeline in pipelines:
        row = dict(kind="measurement", **item, pipeline=pipeline)
        try:
            normalized = features.normalize(path, 256 if pipeline == "resolution256" else 512)
            rgb, metadata = normalized.rgb, dict(normalized.metadata)
            if pipeline == "jpeg90_512":
                rgb, encoding_sha = jpeg_sensitivity(rgb)
                metadata.update(
                    pre_encoding_normalized_sha256=metadata["normalized_sha256"],
                    encoding="JPEG quality 90, subsampling 2, nonprogressive, no optimization",
                    encoding_sha256=encoding_sha,
                )
                metadata["normalized_sha256"] = hashlib.sha256(
                    rgb.astype("<f8").tobytes()
                ).hexdigest()
            if pipeline not in s.PIPELINES:
                raise ValueError("unknown fixed pipeline")
            values = features.extract(rgb)
            if values.shape != (31,) or not np.isfinite(values).all():
                raise ValueError("invalid fidelity vector")
            row.update(
                status="measured",
                values=values.tolist(),
                feature_sha256=digest(values.tolist()),
                normalization=metadata,
            )
        except (ValueError, OSError, Image.DecompressionBombError) as exc:
            row.update(status="failed", error_type=type(exc).__name__)
        rows.append(row)
    return rows


def measure_item(root, stage, item):
    pipelines = s.PIPELINES[1:] if stage == "development" else s.PIPELINES
    metadata = {
        k: item[k]
        for k in (
            "image_id",
            "painter_id",
            "content_class",
            "native_short_side",
            "mixed_uncertain",
            "request_id",
            "selected_request_id",
            "route",
            "brief_id",
            "brief_index",
            "condition",
            "repetition",
            "window",
            "initial_only_eligible",
            "raw_sha256",
        )
        if k in item
    }
    metadata["stage"] = stage
    if stage != "generated":
        if hash_file(root / item["response_path"]) != item["response_sha256"]:
            raise ValueError("source image changed before measurement")
        metadata["raw_sha256"] = item["response_sha256"]
        return measure_path(root / item["response_path"], metadata, pipelines)
    body = read_response(root, item["selected_response"])
    observed = t.inspect_response(body)
    if observed != item["selected_response"]["observed"]:
        raise ValueError("returned image metadata differs from the terminal record")
    raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
    metadata["raw_sha256"] = observed["image_sha256"]
    temporary = root / s.WORKSPACE / "measurement_tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="decode-", dir=temporary) as directory:
        path = Path(directory) / "image.bin"
        path.write_bytes(raw)
        return measure_path(path, metadata, pipelines)


def inventory(root, stage):
    directory = root / s.DIRECTORY
    if stage == "development":
        return read_jsonl(directory / "development.jsonl")
    if stage == "reference":
        return [
            dict(r, image_id=r["work_id"]) for r in read_jsonl(directory / "reference_panel.jsonl")
        ]
    if stage != "generated":
        raise ValueError("unknown measurement stage")
    receipt = read_json(directory / "generation_receipt.json")
    if receipt["status"] not in ("completed", "stopped_for_diagnosis"):
        raise ValueError("research generation must be terminal before outcome measurement")
    if hash_file(directory / "slot_events.jsonl") != receipt["slot_events_sha256"]:
        raise ValueError("terminal slots differ from their receipt")
    requests = {r["request_id"]: r for r in read_jsonl(directory / "requests.jsonl")}
    result = []
    for row in events(directory / "slot_events.jsonl"):
        if row["status"] != "image_returned":
            continue
        request = requests[row["request_id"]]
        result.append(
            dict(
                request,
                image_id="generated:" + row["request_id"],
                selected_request_id=row["selected_request_id"],
                selected_response=row["selected_response"],
                initial_only_eligible=row["initial_status"] == "image_returned",
            )
        )
    return result


def build_scalers(root, rows):
    result = {
        "primary512": dict(
            status="available",
            scaler=read_json(root / s.OLD_METHOD / "scaler.json"),
            basis="unchanged existing 221-work development scaler",
        )
    }
    for pipeline in s.PIPELINES[1:]:
        selected = [r for r in rows if r["pipeline"] == pipeline]
        if len(selected) != 221 or any(r["status"] != "measured" for r in selected):
            result[pipeline] = dict(
                status="unavailable", reason="incomplete fixed development remeasurement"
            )
            continue
        scaler = fit_scaler(
            {
                p: np.array([r["values"] for r in selected if r["painter_id"] == p])
                for p in PAINTER_IDS
            }
        )
        try:
            transform(np.zeros((1, 31)), scaler)
        except ValueError:
            result[pipeline] = dict(
                status="unavailable", reason="invalid development scale", scaler=scaler
            )
        else:
            result[pipeline] = dict(
                status="available",
                scaler=scaler,
                basis="same 221 development works remeasured under this processing pipeline",
            )
    return result


def measure(root, stage):
    with stage_lock(root / s.WORKSPACE / ".measurement.writer.lock"):
        s.verify(root)
        directory = root / s.DIRECTORY
        receipt_path = directory / (stage + "_measurement_receipt.json")
        if receipt_path.exists():
            raise ValueError("measurement stage is terminal")
        if stage != "development":
            verify_bindings(
                root, read_json(directory / "development_measurement_receipt.json")["outputs"]
            )
            read_json(directory / "scalers.json")
        items = inventory(root, stage)
        expected = s.PIPELINES[1:] if stage == "development" else s.PIPELINES
        ledger = directory / (stage + "_features.jsonl")
        rows = events(ledger)
        known = {(r["image_id"], r["pipeline"]): r for r in rows}
        if len(known) != len(rows) or not set(known) <= {
            (r["image_id"], p) for r in items for p in expected
        }:
            raise ValueError("duplicate or unexpected measurement record")
        pending = [r for r in items if any((r["image_id"], p) not in known for p in expected)]
        if not items and not ledger.exists():
            ledger.touch(exist_ok=False)
        with ThreadPoolExecutor(max_workers=2) as executor:
            batches = executor.map(lambda item: measure_item(root, stage, item), pending)
            for index, batch in enumerate(batches):
                for row in batch:
                    key = row["image_id"], row["pipeline"]
                    if key in known:
                        if {k: known[key][k] for k in row} != row:
                            raise ValueError("resumed deterministic measurement differs")
                        continue
                    known[key] = append_event(ledger, row)
                if (index + 1) % 25 == 0:
                    print(
                        json.dumps(
                            dict(
                                stage=stage,
                                newly_processed_images=index + 1,
                                remaining_at_start=len(pending),
                            )
                        ),
                        flush=True,
                    )
        rows = events(ledger)
        output_paths = [s.DIRECTORY / ledger.name]
        if stage == "development":
            publish(directory / "scalers.json", build_scalers(root, rows))
            output_paths.append(s.DIRECTORY / "scalers.json")
        receipt = dict(
            stage=stage,
            images=len(items),
            pipelines=list(expected),
            dispositions=dict(Counter(r["status"] for r in rows)),
            source_freeze_sha256=hash_file(directory / "main_freeze.json"),
            outputs=bindings(root, output_paths),
            duplicate_raw_hashes={
                h: n
                for h, n in Counter(
                    r["raw_sha256"] for r in rows if r["pipeline"] == expected[0]
                ).items()
                if n > 1
            },
        )
        publish(receipt_path, receipt)
        return receipt


def check(root, stage):
    s.verify(root)
    directory = root / s.DIRECTORY
    receipt = read_json(directory / (stage + "_measurement_receipt.json"))
    verify_bindings(root, receipt["outputs"])
    recorded = {
        (r["image_id"], r["pipeline"]): r for r in events(directory / (stage + "_features.jsonl"))
    }
    checked = 0
    with ThreadPoolExecutor(max_workers=2) as executor:
        for batch in executor.map(
            lambda item: measure_item(root, stage, item), inventory(root, stage)
        ):
            for row in batch:
                stored = recorded[row["image_id"], row["pipeline"]]
                if {k: stored[k] for k in row} != row:
                    raise ValueError("raw-to-feature replay differs")
                checked += 1
    if checked != len(recorded):
        raise ValueError("measurement replay inventory differs")
    return dict(stage=stage, status="verified", replayed_feature_records=checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("development", "reference", "generated"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = check(Path.cwd(), args.stage) if args.check else measure(Path.cwd(), args.stage)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
