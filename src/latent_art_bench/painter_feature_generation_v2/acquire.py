"""Explicit, resumable image acquisition against an immutable snapshot contract."""

from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    PROTOCOL,
    WORKSPACE,
    append_event,
    bindings,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)

SELF = Path("src/latent_art_bench/painter_feature_generation_v2/acquire.py")
ARTIFACTS = Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py")
MAX_FILE_BYTES = 64 * 1024 * 1024
RESERVE_DISK_BYTES = 5 * 1024 ** 3


def prepare(root: Path, frame_id: str, run_id: str) -> dict:
    identifier(frame_id)
    identifier(run_id)
    output = root / MANIFESTS / run_id
    if output.exists():
        raise FileExistsError(output)
    frame = MANIFESTS / frame_id / "frame.jsonl"
    frame_receipt = MANIFESTS / frame_id / "frame_receipt.json"
    receipt = read_json(root / frame_receipt)
    verify_bindings(root, receipt["inputs"])
    if hash_file(root / frame) != receipt["frame_sha256"]:
        raise ValueError("frame changed")
    paths = [PROTOCOL, SELF, ARTIFACTS, frame, frame_receipt, Path("uv.lock"),
             Path("pyproject.toml"), Path("src/latent_art_bench/io.py")]
    for path in paths:
        previous = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if previous.returncode or previous.stdout != (root / path).read_bytes():
            raise ValueError(f"commit the exact bound acquisition input first: {path}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    config = dict(
        schema_version="pfg-v2-acquisition-freeze/1.0", run_id=run_id, frame_id=frame_id,
        recorded_git_commit=commit, prepared_at_utc=utc_now().isoformat(),
        authorization="Maintainer's 2026-09-05 session request to implement the complete "
                      "research analysis and prospectively improve its protocol.",
        reviewer_kind="operator_self_check_not_independent_review",
        frame_path=str(frame), expected_records=len(read_jsonl(root / frame)),
        max_attempts=3, minimum_interval_seconds=1.0, max_file_bytes=MAX_FILE_BYTES,
        reserve_disk_bytes=RESERVE_DISK_BYTES, inputs=bindings(root, paths),
    )
    publish(output / "acquisition_freeze.json", config)
    return config


def inspect_body(body: bytes, surrogate: dict) -> dict:
    if len(body) > MAX_FILE_BYTES:
        raise ValueError("file_exceeds_frozen_size_limit")
    if hashlib.sha1(body).hexdigest() != surrogate["expected_sha1"]:
        raise ValueError("snapshot_sha1_mismatch")
    with Image.open(io.BytesIO(body)) as image:
        if image.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
            raise ValueError("unsupported_format")
        image.load()
        if image.size != (surrogate["expected_width"], surrogate["expected_height"]):
            raise ValueError("snapshot_dimensions_mismatch")
        if min(image.size) < 1024:
            raise ValueError("native_short_side_below_1024")
        return dict(width=image.width, height=image.height, format=image.format,
                    has_icc=bool(image.info.get("icc_profile")), mode=image.mode)


def fetch(client: httpx.Client, url: str) -> tuple[int, dict, bytes]:
    if urlsplit(url).scheme != "https" or urlsplit(url).hostname != "upload.wikimedia.org":
        raise ValueError("nonallowlisted_media_url")
    with client.stream("GET", url) as response:
        if str(response.url) != str(httpx.URL(url)):
            raise ValueError("response_url_drift")
        chunks, size = [], 0
        for part in response.iter_bytes():
            size += len(part)
            if size > MAX_FILE_BYTES:
                raise ValueError("file_exceeds_frozen_size_limit")
            chunks.append(part)
        return response.status_code, dict(response.headers), b"".join(chunks)


def execute(root: Path, run_id: str) -> dict:
    identifier(run_id)
    with stage_lock(root / WORKSPACE / run_id / ".acquisition.writer.lock"):
        return _execute(root, run_id)


def _execute(root: Path, run_id: str) -> dict:
    identifier(run_id)
    output = root / MANIFESTS / run_id
    frozen_path = output / "acquisition_freeze.json"
    frozen = read_json(frozen_path)
    verify_bindings(root, frozen["inputs"])
    if (output / "acquisition_receipt.json").exists():
        raise FileExistsError("acquisition is terminal; do not retry it in place")
    frame = read_jsonl(root / frozen["frame_path"])
    ledger = output / "acquisition_events.jsonl"
    prior = events(ledger)
    completed = {r["work_id"]: r for r in prior if r["kind"] == "terminal"}
    attempts = Counter(r["work_id"] for r in prior if r["kind"] == "attempt")
    cas = root / WORKSPACE / run_id / "raw"
    cas.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=httpx.Timeout(90, connect=20), follow_redirects=False,
                      headers={"User-Agent": "LatentArtBench/0.2 research "
                               "(+https://github.com/isingmodel/latent-art-bench)"}) as client:
        for index, row in enumerate(frame):
            work_id = row["work_id"]
            if work_id in completed:
                prior_row = completed[work_id]
                if prior_row["status"] == "acquired":
                    if hash_file(root / prior_row["raw_path"]) != prior_row["raw_sha256"]:
                        raise ValueError("previously acquired evidence changed")
                continue
            if shutil.disk_usage(cas).free < frozen["reserve_disk_bytes"] + MAX_FILE_BYTES:
                raise OSError("disk reserve reached; acquisition remains incomplete")
            outcome = dict(kind="terminal", work_id=work_id, painter_id=row["painter_id"],
                           role=row["role"], status="failed", error="attempt_budget_exhausted")
            while attempts[work_id] < frozen["max_attempts"]:
                attempts[work_id] += 1
                append_event(ledger, dict(kind="attempt", work_id=work_id,
                                         attempt=attempts[work_id], url=row["surrogate"]["url"]))
                retry, wait = False, 5 if attempts[work_id] == 1 else 15
                try:
                    status, headers, body = fetch(client, row["surrogate"]["url"])
                    response_hash = hashlib.sha256(body).hexdigest()
                    response_path = cas / response_hash
                    if response_path.exists():
                        if hash_file(response_path) != response_hash:
                            raise ValueError("corrupt_content_address")
                    else:
                        with response_path.open("xb") as handle:
                            handle.write(body)
                    append_event(ledger, dict(kind="response", work_id=work_id, status=status,
                                             body_sha256=response_hash, bytes=len(body),
                                             content_type=headers.get("content-type"),
                                             retry_after=headers.get("retry-after")))
                    if status == 200:
                        metadata = inspect_body(body, row["surrogate"])
                        outcome.update(status="acquired", error=None,
                                       raw_sha256=response_hash,
                                       raw_path=str(response_path.relative_to(root)),
                                       bytes=len(body), **metadata)
                    else:
                        outcome["error"] = f"http_{status}"
                        retry = status == 429 or 500 <= status <= 599
                        if headers.get("retry-after", "").isdigit():
                            wait = max(wait, int(headers["retry-after"]))
                except httpx.TransportError as exc:
                    outcome["error"] = type(exc).__name__
                    append_event(ledger, dict(kind="transport_failure", work_id=work_id,
                                             error=type(exc).__name__))
                    retry = True
                except (ValueError, OSError, Image.DecompressionBombError) as exc:
                    outcome["error"] = str(exc)
                if not retry or attempts[work_id] == frozen["max_attempts"]:
                    break
                # Long server waits are explicit and interruptible; no busy polling.
                remaining = wait
                while remaining:
                    print(f"provider wait: {remaining}s for {work_id}", flush=True)
                    pause = min(remaining, 30)
                    time.sleep(pause)
                    remaining -= pause
            completed[work_id] = append_event(ledger, outcome)
            if (index + 1) % 10 == 0 or index + 1 == len(frame):
                print(f"acquisition {index + 1}/{len(frame)} "
                      f"{dict(Counter(r['status'] for r in completed.values()))}", flush=True)
            time.sleep(frozen["minimum_interval_seconds"])
    ordered = [completed[r["work_id"]] for r in frame]
    publish(output / "acquisitions.jsonl", ordered, lines=True)
    receipt = dict(
        schema_version="pfg-v2-acquisition-receipt/1.0", run_id=run_id,
        terminal_records=len(ordered), statuses=dict(Counter(r["status"] for r in ordered)),
        freeze_sha256=hash_file(frozen_path), ledger_sha256=hash_file(ledger),
        acquisitions_sha256=hash_file(output / "acquisitions.jsonl"),
        completed_at_utc=utc_now().isoformat(),
    )
    publish(output / "acquisition_receipt.json", receipt)
    return receipt
