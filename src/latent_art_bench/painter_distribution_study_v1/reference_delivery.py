"""Prospective successor using Wikimedia standard thumbnails after original-delivery limits."""

from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import discovery as d
from . import references as r

RUN_ID = "pdsv1-reference-delivery-r2-20260906"
DIRECTORY = Path("data/manifests") / r.NAMESPACE / RUN_ID
WORKSPACE = Path("research_workspace") / r.NAMESPACE / RUN_ID
CONTRACT = Path("studies") / r.NAMESPACE / "REFERENCE_DELIVERY_R2.md"
MAX_BYTES = 16 * 1024**2


def select(root):
    candidates = read_jsonl(root / r.DIRECTORY / "candidates.jsonl")
    by_file = {r.file_key(c["commons_filename"]): c for c in candidates}
    deliveries, records = {}, []
    for event in events(root / d.DIRECTORY / "events.jsonl"):
        if event["kind"] != "response" or "iiurlwidth" not in event["url"]:
            continue
        records.append(Path(event["retained_path"]))
        for page in json.loads(d.read_cached(root, event))["query"]["pages"]:
            candidate = by_file[r.file_key(page["title"])]
            info = page["imageinfo"][0]
            if info["sha1"] != candidate["expected_sha1"]:
                raise ValueError("parent image SHA-1 changed; never refresh it")
            if (info["width"], info["height"]) != (
                candidate["expected_width"],
                candidate["expected_height"],
            ):
                raise ValueError("parent image geometry changed")
            url, width, height = info["thumburl"], info["thumbwidth"], info["thumbheight"]
            basis = "imageinfo_returned_thumbnail_url"
            parsed = urlsplit(url)
            if "/thumb/" not in parsed.path:
                # At native width imageinfo returns the original, which was rate-limited.
                # For the four JPEG cases, derive the next smaller standard-size URL
                # using the same Commons file/hash path and observed thumbnail host.
                sizes = [
                    s
                    for s in (960, 1280, 1920)
                    if s < info["width"]
                    and min(s, round(s * info["height"] / info["width"])) >= 512
                ]
                if not sizes or not parsed.path.lower().endswith((".jpg", ".jpeg")):
                    continue
                width = max(sizes)
                height = round(width * info["height"] / info["width"])
                tail = parsed.path.removeprefix("/wikipedia/commons/")
                filename = tail.rsplit("/", 1)[-1]
                url = f"https://thumb.wikimedia.org/wikipedia/commons/thumb/{tail}/{width}px-{filename}"
                basis = "standard_width_derived_from_verified_parent_file_path"
            if min(width, height) < 512 or width > info["width"] or height > info["height"]:
                continue
            deliveries[candidate["work_id"]] = dict(
                candidate,
                delivery_url=url,
                delivery_basis=basis,
                delivery_width=width,
                delivery_height=height,
                parent_sha1=info["sha1"],
                current_media_metadata_sha256=event["body_sha256"],
                current_media_page_id=page["pageid"],
                processing_history="Wikimedia standard thumbnail of the recorded surrogate",
            )
    ordered = [deliveries[c["work_id"]] for c in candidates if c["work_id"] in deliveries]
    omitted = [
        dict(work_id=c["work_id"], reason="no_supported_nonupsampled_standard_width_ge_512")
        for c in candidates
        if c["work_id"] not in deliveries
    ]
    return ordered, omitted, records


def prepare(root):
    predecessor = read_json(root / r.DIRECTORY / "acquisition_receipt.json")
    if predecessor["status"] != "operator_stopped_rate_limit":
        raise ValueError("require the closed original-delivery predecessor")
    deliveries, omitted, raw = select(root)
    paths = [
        CONTRACT,
        Path("src/latent_art_bench") / r.NAMESPACE / "reference_delivery.py",
        Path("tests") / r.NAMESPACE / "test_reference_delivery.py",
        Path("src/latent_art_bench") / r.NAMESPACE / "references.py",
        Path("src/latent_art_bench") / r.NAMESPACE / "discovery.py",
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    paths += [
        r.DIRECTORY / f
        for f in (
            "acquisition_receipt.json",
            "acquisition_events.jsonl",
            "acquisition_freeze.json",
            "candidates.jsonl",
        )
    ]
    paths += [d.DIRECTORY / f for f in ("events.jsonl", "freeze.json", "terminal_receipt.json")]
    commit = committed(root, paths)
    if not deliveries or len(deliveries) > 112:
        raise ValueError("bounded successor delivery inventory required")
    directory = root / DIRECTORY
    if directory.exists():
        raise FileExistsError("successor acquisition identity already exists")
    publish(directory / "deliveries.jsonl", deliveries, lines=True)
    publish(directory / "omissions.jsonl", omitted, lines=True)
    previous_events = events(root / r.DIRECTORY / "acquisition_events.jsonl")
    last = datetime.fromisoformat(previous_events[-1]["at_utc"]).timestamp()
    freeze = dict(
        run_id=RUN_ID,
        recorded_git_commit=commit,
        inputs=bindings(root, paths + raw),
        deliveries_sha256=hash_file(directory / "deliveries.jsonl"),
        predecessor_id=r.RUN_ID,
        earliest_dispatch_unix=last + 600,
        minimum_interval_seconds=10,
        maximum_response_bytes=MAX_BYTES,
        deliveries_by_painter=dict(Counter(c["painter_id"] for c in deliveries)),
        omitted=len(omitted),
        source_pixels_or_features_used_for_selection=False,
    )
    publish(directory / "acquisition_freeze.json", freeze)
    return {k: v for k, v in freeze.items() if k != "inputs"}


def receive(root, candidate, *, transport=None):
    url = candidate["delivery_url"]
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ("thumb.wikimedia.org", "upload.wikimedia.org")
        or not parsed.path.startswith("/wikipedia/commons/thumb/")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("expected a standard Commons thumbnail URL")
    relative = WORKSPACE / "responses" / (candidate["item_qid"] + ".bin")
    target = root / relative
    if target.exists():
        raise FileExistsError("response already exists; no redispatch")
    chunks, size, status, complete, error, headers = [], 0, None, False, None, {}
    try:
        with httpx.Client(
            timeout=httpx.Timeout(90, connect=20),
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": "LatentArtBench/0.3 academic research"},
        ) as client:
            with client.stream("GET", url) as response:
                status = response.status_code
                headers = {
                    k: response.headers[k]
                    for k in ("content-type", "date", "retry-after")
                    if k in response.headers
                }
                for chunk in response.iter_bytes(chunk_size=65536):
                    if size + len(chunk) > MAX_BYTES:
                        error = "response_byte_limit"
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                else:
                    complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    outcome, observed = "failed_delivery", None
    if complete and status == 200:
        try:
            with Image.open(io.BytesIO(body)) as im:
                im.load()
                observed = dict(width=im.width, height=im.height, format=im.format, mode=im.mode)
                valid = (
                    im.format in ("JPEG", "PNG", "WEBP")
                    and min(im.size) >= 512
                    and im.width == candidate["delivery_width"]
                    and abs(im.height - candidate["delivery_height"]) <= 1
                    and im.width <= candidate["expected_width"]
                    and im.height <= candidate["expected_height"]
                )
                outcome = "acquired" if valid else "invalid_geometry"
        except (ValueError, OSError, Image.DecompressionBombError):
            outcome = "decode_failed"
    return dict(
        kind="terminal",
        work_id=candidate["work_id"],
        status=outcome,
        status_code=status,
        complete=complete,
        error=error,
        response_headers=headers,
        response_path=relative.as_posix(),
        response_sha256=hash_file(target),
        bytes=len(body),
        geometry=observed,
        parent_sha1=candidate["parent_sha1"],
    )


def acquire(root, *, transport=None, sleep=time.sleep, now=time.time):
    directory = root / DIRECTORY
    with stage_lock(root / WORKSPACE / ".acquisition.writer.lock"):
        freeze = read_json(directory / "acquisition_freeze.json")
        verify_bindings(root, freeze["inputs"])
        committed(
            root,
            [
                DIRECTORY / name
                for name in ("acquisition_freeze.json", "deliveries.jsonl", "omissions.jsonl")
            ],
        )
        if (directory / "acquisition_receipt.json").exists():
            raise ValueError("successor acquisition is terminal")
        if now() < freeze["earliest_dispatch_unix"]:
            raise ValueError("the provider cooldown has not elapsed")
        if hash_file(directory / "deliveries.jsonl") != freeze["deliveries_sha256"]:
            raise ValueError("delivery inventory changed")
        deliveries = read_jsonl(directory / "deliveries.jsonl")
        ledger = directory / "acquisition_events.jsonl"
        rows = events(ledger)
        attempts = {x["work_id"] for x in rows if x["kind"] == "attempt"}
        terminal = {x["work_id"] for x in rows if x["kind"] == "terminal"}
        if attempts != terminal:
            raise ValueError("unresolved delivery intent; no automatic redispatch")
        status = "completed"
        for candidate in deliveries:
            if candidate["work_id"] in terminal:
                continue
            if shutil.disk_usage(root).free < r.MIN_FREE + MAX_BYTES:
                raise OSError("storage reserve reached")
            sleep(10)
            append_event(
                ledger,
                dict(
                    kind="attempt",
                    work_id=candidate["work_id"],
                    url=candidate["delivery_url"],
                    delivery_sha256=digest(candidate),
                ),
            )
            result = receive(root, candidate, transport=transport)
            append_event(ledger, result)
            print(
                json.dumps({k: result[k] for k in ("work_id", "status", "status_code")}), flush=True
            )
            if result["status_code"] in (403, 429, 503) or not result["complete"]:
                status = "stopped_provider_or_transport"
                break
        rows = events(ledger)
        attempted = {x["work_id"] for x in rows if x["kind"] == "attempt"}
        receipt = dict(
            run_id=RUN_ID,
            status=status,
            attempted=len(attempted),
            dispositions=dict(Counter(x["status"] for x in rows if x["kind"] == "terminal")),
            unattempted_work_ids=[
                c["work_id"] for c in deliveries if c["work_id"] not in attempted
            ],
            freeze_sha256=hash_file(directory / "acquisition_freeze.json"),
            events_sha256=hash_file(ledger),
            fidelity_features_extracted=0,
            completed_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        publish(directory / "acquisition_receipt.json", receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "acquire"))
    args = parser.parse_args()
    print(
        json.dumps(
            prepare(Path.cwd()) if args.command == "prepare" else acquire(Path.cwd()), indent=2
        )
    )


if __name__ == "__main__":
    main()
