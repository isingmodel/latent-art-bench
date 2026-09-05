"""Exact provider-URL acquisition with documented standard thumbnail sizes and migrated host."""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    append_event,
    bindings,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.renderings import _sleep, _store, wait_seconds

SELF = Path("src/latent_art_bench/painter_feature_generation_v2/renderings_r2.py")
PROTOCOL = Path("studies/painter_feature_generation_v2/PROTOCOL_1.3.md")
PREDECESSOR = MANIFESTS / "pfg2-renderings-20260905"
FRAME = MANIFESTS / "pfg2-frame-20260905" / "frame.jsonl"
MAX_BYTES, RESERVE = 64 * 1024**2, 5 * 1024**3


def url_kind(url: str) -> tuple[str, int | None]:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"upload.wikimedia.org", "thumb.wikimedia.org"}
        or parsed.port not in {None, 443}
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("nonallowlisted_media_url")
    if parsed.path.startswith("/wikipedia/commons/thumb/"):
        width = re.search(r"(?:^|-)(\d+)px-", unquote(parsed.path.rsplit("/", 1)[-1]))
        if not width:
            raise ValueError("no_advertised_thumbnail_width")
        return "thumbnail", int(width[1])
    if parsed.hostname == "upload.wikimedia.org" and parsed.path.startswith("/wikipedia/commons/"):
        return "original", None
    raise ValueError("nonallowlisted_media_path")


def inspect_body(body: bytes, request: dict) -> dict:
    kind, advertised_width = url_kind(request["url"])
    with Image.open(io.BytesIO(body)) as image:
        image.load()
        if image.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
            raise ValueError("unsupported_format")
        if min(image.size) < 1024:
            raise ValueError("short_side_below_1024")
        if kind == "original":
            if hashlib.sha1(body).hexdigest() != request["source_sha1"]:
                raise ValueError("source_original_sha1_mismatch")
            if image.size != (request["source_width"], request["source_height"]):
                raise ValueError("source_original_dimensions_mismatch")
        else:
            expected_height = image.width * request["source_height"] / request["source_width"]
            if image.width != advertised_width:
                raise ValueError("advertised_thumbnail_width_mismatch")
            if abs(image.height - expected_height) > max(2, 0.002 * expected_height):
                raise ValueError("thumbnail_aspect_ratio_mismatch")
        return dict(
            width=image.width,
            height=image.height,
            format=image.format,
            has_icc=bool(image.info.get("icc_profile")),
            source_kind=kind,
            advertised_thumbnail_width=advertised_width,
            differs_from_reported_dimensions=(
                image.size != (request["expected_width"], request["expected_height"])
            ),
        )


def prepare(root: Path, run_id: str) -> dict:
    output = root / MANIFESTS / identifier(run_id)
    if output.exists():
        raise FileExistsError(output)
    paths = [
        SELF,
        PROTOCOL,
        FRAME,
        Path("uv.lock"),
        Path("pyproject.toml"),
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/renderings.py"),
    ]
    paths += [
        PREDECESSOR / name
        for name in (
            "terminal_receipt.json",
            "image_events.jsonl",
            "images_freeze.json",
            "metadata_receipt.json",
            "renderings.jsonl",
        )
    ]
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit exact acquisition input first: {path}")
    frame = {r["work_id"]: r for r in read_jsonl(root / FRAME)}
    records = read_jsonl(root / PREDECESSOR / "renderings.jsonl")
    if len(records) != len(frame) or {r["work_id"] for r in records} != set(frame):
        raise ValueError("replacement must cover the identical complete frame")
    requests = []
    for row in records:
        source = frame[row["work_id"]]["surrogate"]
        if row["status"] == "rendering_registered":
            url_kind(row["url"])
        requests.append(
            dict(
                row, source_width=source["expected_width"], source_height=source["expected_height"]
            )
        )
    publish(output / "requests.jsonl", requests, lines=True)
    frozen = dict(
        run_id=run_id,
        frame_id=FRAME.parent.name,
        predecessor=PREDECESSOR.name,
        requests=len(requests),
        requests_sha256=hash_file(output / "requests.jsonl"),
        inputs=bindings(root, paths),
        recorded_git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        prepared_at_utc=utc_now().isoformat(),
        authorization="2026-09-05 maintainer: continue empirical analysis; "
        "complete disjoint acquisition correction under amendment 1.3",
        reviewer_kind="operator_self_check_not_independent_review",
    )
    publish(output / "acquisition_freeze.json", frozen)
    return frozen


def fetch(client: httpx.Client, url: str) -> tuple[int | None, dict, bytes, str | None]:
    url_kind(url)
    chunks, length, status, headers, error = [], 0, None, {}, None
    try:
        with client.stream("GET", url) as response:
            status, headers = response.status_code, dict(response.headers)
            for chunk in response.iter_bytes():
                remaining = MAX_BYTES - length
                chunks.append(chunk[:remaining])
                length += min(len(chunk), remaining)
                if len(chunk) > remaining:
                    error = "response_ceiling"
                    break
    except httpx.TransportError as exc:
        error = type(exc).__name__
    return status, headers, b"".join(chunks), error


def execute(root: Path, run_id: str, *, transport=None, sleep=time.sleep) -> dict:
    output = root / MANIFESTS / identifier(run_id)
    frozen = read_json(output / "acquisition_freeze.json")
    verify_bindings(root, frozen["inputs"])
    if hash_file(output / "requests.jsonl") != frozen["requests_sha256"]:
        raise ValueError("acquisition request frame changed")
    with stage_lock(root / WORKSPACE / run_id / ".acquisition.writer.lock"):
        if (output / "acquisition_receipt.json").exists():
            raise FileExistsError("acquisition is terminal")
        rows = read_jsonl(output / "requests.jsonl")
        ledger = output / "acquisition_events.jsonl"
        previous = events(ledger)
        attempts = Counter(r["work_id"] for r in previous if r["kind"] == "attempt")
        done = {r["work_id"]: r for r in previous if r["kind"] == "terminal"}
        with httpx.Client(
            timeout=90,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={
                "User-Agent": "LatentArtBench/0.2 research "
                "(+https://github.com/isingmodel/latent-art-bench)"
            },
        ) as client:
            for index, row in enumerate(rows):
                if row["work_id"] in done:
                    prior = done[row["work_id"]]
                    if (
                        prior.get("raw_path")
                        and hash_file(root / prior["raw_path"]) != prior["raw_sha256"]
                    ):
                        raise ValueError("acquired evidence changed")
                    continue
                if shutil.disk_usage(root).free < RESERVE + MAX_BYTES:
                    raise OSError("disk reserve reached; acquisition incomplete")
                outcome = dict(row, kind="terminal", status="failed", error="metadata_unavailable")
                if row["status"] == "rendering_registered":
                    outcome["error"] = "attempt_budget_exhausted"
                    for attempt in range(attempts[row["work_id"]] + 1, 4):
                        append_event(
                            ledger, dict(kind="attempt", work_id=row["work_id"], attempt=attempt)
                        )
                        status, headers, body, error = fetch(client, row["url"])
                        path, sha = _store(root, run_id, body, "raw")
                        append_event(
                            ledger,
                            dict(
                                kind="response",
                                work_id=row["work_id"],
                                attempt=attempt,
                                http_status=status,
                                raw_path=path,
                                raw_sha256=sha,
                                partial_body=error is not None,
                                error=error,
                            ),
                        )
                        outcome.update(
                            raw_path=path,
                            raw_sha256=sha,
                            http_status=status,
                            bytes=len(body),
                            error=error or f"http_{status}",
                        )
                        if error == "response_ceiling":
                            break
                        if not error and status == 200:
                            try:
                                outcome.update(
                                    inspect_body(body, row), status="acquired", error=None
                                )
                            except (ValueError, OSError) as exc:
                                outcome["error"] = str(exc)
                            break
                        if not error and status != 429 and status < 500:
                            break
                        if attempt < 3:
                            _sleep(wait_seconds(headers.get("retry-after"), attempt))
                done[row["work_id"]] = append_event(ledger, outcome)
                if (index + 1) % 20 == 0 or index + 1 == len(rows):
                    print(
                        f"rendering R2 {index + 1}/{len(rows)} "
                        f"{dict(Counter(r['status'] for r in done.values()))}",
                        flush=True,
                    )
                sleep(1)
        ordered = [done[r["work_id"]] for r in rows]
        publish(output / "acquisitions.jsonl", ordered, lines=True)
        receipt = dict(
            run_id=run_id,
            terminal_records=len(ordered),
            statuses=dict(Counter(r["status"] for r in ordered)),
            acquisitions_sha256=hash_file(output / "acquisitions.jsonl"),
            freeze_sha256=hash_file(output / "acquisition_freeze.json"),
            ledger_sha256=hash_file(ledger),
            completed_at_utc=utc_now().isoformat(),
        )
        publish(output / "acquisition_receipt.json", receipt)
        return receipt
