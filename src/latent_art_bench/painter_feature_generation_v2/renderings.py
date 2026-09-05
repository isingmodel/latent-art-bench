"""Documented Commons renderings for the same frozen works, under acquisition amendment 1.1."""

from __future__ import annotations

import hashlib
import io
import math
import shutil
import subprocess
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1.determine import File
from latent_art_bench.painter_feature_generation_v2.acquire import (
    MAX_FILE_BYTES,
    RESERVE_DISK_BYTES,
    fetch,
)
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

AMENDMENT = Path("studies/painter_feature_generation_v2/PROTOCOL_1.1.md")
SELF = Path("src/latent_art_bench/painter_feature_generation_v2/renderings.py")
ENDPOINT = "https://commons.wikimedia.org/w/api.php"
PREDECESSOR = MANIFESTS / "pfg2-acquisition-20260905"


def intents(frame: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in frame:
        source = row["surrogate"]
        width, height = source["expected_width"], source["expected_height"]
        desired = min(width, math.ceil(width * 1536 / min(width, height) / 512) * 512)
        grouped[desired].append(source["commons_filename"])
    result = []
    for width, names in sorted(grouped.items()):
        batch = []
        for name in sorted(set(names)):
            candidate = batch + [name]
            params = _params(width, candidate)
            if batch and (
                len(candidate) > 20 or len(str(httpx.URL(ENDPOINT, params=params))) > 7000
            ):
                result.append(
                    dict(
                        request_id=f"metadata-{len(result):03d}",
                        width=width,
                        params=_params(width, batch),
                    )
                )
                batch = []
            batch.append(name)
        if batch:
            result.append(
                dict(
                    request_id=f"metadata-{len(result):03d}",
                    width=width,
                    params=_params(width, batch),
                )
            )
    return result


def _params(width: int, titles: list[str]) -> dict:
    return dict(
        action="query",
        format="json",
        formatversion="2",
        prop="imageinfo",
        iiprop="url|size|sha1|timestamp|extmetadata",
        iiurlwidth=str(width),
        iiextmetadatafilter="LicenseShortName|Restrictions",
        maxlag="5",
        titles="|".join(titles),
    )


def _commit(root: Path, paths: list[Path]) -> str:
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit the bound rendering input first: {path}")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def prepare(root: Path, frame_id: str, run_id: str) -> dict:
    identifier(frame_id)
    identifier(run_id)
    output = root / MANIFESTS / run_id
    if output.exists():
        raise FileExistsError(output)
    frame_path = MANIFESTS / frame_id / "frame.jsonl"
    paths = [
        SELF,
        AMENDMENT,
        frame_path,
        PREDECESSOR / "acquisition_freeze.json",
        PREDECESSOR / "acquisition_events.jsonl",
        PREDECESSOR / "terminal_receipt.json",
        Path("uv.lock"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/acquire.py"),
        Path("src/latent_art_bench/painter_feature_generation_v1/determine.py"),
        Path("src/latent_art_bench/io.py"),
    ]
    commit = _commit(root, paths)
    requests = intents(read_jsonl(root / frame_path))
    publish(output / "metadata_requests.jsonl", requests, lines=True)
    freeze = dict(
        run_id=run_id,
        frame_id=frame_id,
        frame_path=str(frame_path),
        requests_sha256=hash_file(output / "metadata_requests.jsonl"),
        requests=len(requests),
        inputs=bindings(root, paths),
        recorded_git_commit=commit,
        prepared_at_utc=utc_now().isoformat(),
        authorization="2026-09-05 maintainer authorization to implement the research "
        "and revise its protocol; resource correction under amendment 1.1",
        reviewer_kind="operator_self_check_not_independent_review",
    )
    publish(output / "metadata_freeze.json", freeze)
    return freeze


def wait_seconds(value: str | None, attempt: int) -> float:
    minimum = 5 if attempt == 1 else 15
    if not value:
        return minimum
    try:
        return max(minimum, float(value))
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
            return max(minimum, seconds)
        except (ValueError, TypeError):
            return minimum


def _store(root: Path, run_id: str, body: bytes, subdir: str) -> tuple[str, str]:
    sha = hashlib.sha256(body).hexdigest()
    relative = WORKSPACE / run_id / subdir / sha
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if hash_file(path) != sha:
            raise ValueError("content-addressed evidence changed")
    else:
        with path.open("xb") as handle:
            handle.write(body)
    return str(relative), sha


def _sleep(seconds: float) -> None:
    while seconds > 0:
        print(f"provider wait {seconds:.0f}s", flush=True)
        pause = min(seconds, 30)
        time.sleep(pause)
        seconds -= pause


def select_rendering(row: dict, page: dict) -> dict:
    info = (page.get("imageinfo") or [{}])[0]
    source = row["surrogate"]
    result = dict(
        work_id=row["work_id"],
        painter_id=row["painter_id"],
        role=row["role"],
        source_sha1=source["expected_sha1"],
        status="metadata_rejected",
    )
    if info.get("sha1") != source["expected_sha1"] or (info.get("width"), info.get("height")) != (
        source["expected_width"],
        source["expected_height"],
    ):
        return dict(result, error="source_snapshot_mismatch_or_missing")
    metadata = info.get("extmetadata", {})
    licence = metadata.get("LicenseShortName", {}).get("value", "")
    restriction = metadata.get("Restrictions", {}).get("value", "")
    if not File("", licence, restriction, 0, "").open_rights:
        return dict(result, error="current_rights_not_open")
    rendered = "thumburl" in info
    width = info.get("thumbwidth") if rendered else info["width"]
    height = info.get("thumbheight") if rendered else info["height"]
    if not isinstance(width, int) or not isinstance(height, int) or min(width, height) < 1024:
        return dict(result, error="rendering_below_1024_short_side")
    return dict(
        result,
        status="rendering_registered",
        error=None,
        url=info["thumburl"] if rendered else info["url"],
        expected_width=width,
        expected_height=height,
        licence=licence,
        provider_rendered=rendered,
        source_timestamp=info.get("timestamp"),
    )


def collect_metadata(root: Path, run_id: str) -> dict:
    identifier(run_id)
    output = root / MANIFESTS / run_id
    frozen = read_json(output / "metadata_freeze.json")
    verify_bindings(root, frozen["inputs"])
    if (output / "metadata_receipt.json").exists():
        raise FileExistsError("rendering metadata census is terminal")
    if hash_file(output / "metadata_requests.jsonl") != frozen["requests_sha256"]:
        raise ValueError("metadata request frame changed")
    requests = read_jsonl(output / "metadata_requests.jsonl")
    ledger = output / "metadata_events.jsonl"
    existing = events(ledger)
    prior = {r["request_id"]: r for r in existing if r["kind"] == "terminal"}
    attempts = Counter(r["request_id"] for r in existing if r["kind"] == "attempt")
    with (
        stage_lock(root / WORKSPACE / run_id / ".metadata.writer.lock"),
        httpx.Client(
            timeout=60,
            follow_redirects=False,
            headers={
                "User-Agent": "LatentArtBench/0.2 research (+https://github.com/isingmodel/latent-art-bench)"
            },
        ) as client,
    ):
        for request in requests:
            key = request["request_id"]
            if key in prior:
                continue
            outcome = dict(kind="terminal", request_id=key, status="failed")
            for attempt in range(attempts[key] + 1, 4):
                append_event(ledger, dict(kind="attempt", request_id=key, attempt=attempt))
                try:
                    response = client.get(ENDPOINT, params=request["params"])
                    path, sha = _store(root, run_id, response.content, "metadata")
                    append_event(
                        ledger,
                        dict(
                            kind="response",
                            request_id=key,
                            raw_path=path,
                            raw_sha256=sha,
                            http_status=response.status_code,
                        ),
                    )
                    payload = response.json() if response.status_code == 200 else {}
                    if not isinstance(payload, dict):
                        raise ValueError("metadata response is not an object")
                    valid = response.status_code == 200 and isinstance(
                        payload.get("query", {}).get("pages"), list
                    )
                    outcome.update(
                        status="success" if valid else "failed",
                        raw_path=path,
                        raw_sha256=sha,
                        http_status=response.status_code,
                    )
                    if valid or (
                        response.status_code not in {200, 429} and response.status_code < 500
                    ):
                        break
                    delay = wait_seconds(response.headers.get("retry-after"), attempt)
                except (httpx.TransportError, ValueError) as exc:
                    outcome["error"] = type(exc).__name__
                    delay = wait_seconds(None, attempt)
                if attempt < 3:
                    _sleep(delay)
            prior[key] = append_event(ledger, outcome)
            print(f"rendering metadata {len(prior)}/{len(requests)}", flush=True)
            time.sleep(1)
    pages = {}
    for request in requests:
        outcome = prior[request["request_id"]]
        if outcome["status"] == "success":
            if hash_file(root / outcome["raw_path"]) != outcome["raw_sha256"]:
                raise ValueError("metadata bytes changed")
            payload = read_json(root / outcome["raw_path"])
            for page in payload["query"]["pages"]:
                pages[request["width"], page["title"].replace("_", " ")] = page
    rows = []
    for row in read_jsonl(root / frozen["frame_path"]):
        source = row["surrogate"]
        width, height = source["expected_width"], source["expected_height"]
        desired = min(width, math.ceil(width * 1536 / min(width, height) / 512) * 512)
        page = pages.get((desired, source["commons_filename"].replace("_", " ")), {})
        rows.append(select_rendering(row, page))
    publish(output / "renderings.jsonl", rows, lines=True)
    receipt = dict(
        run_id=run_id,
        statuses=dict(Counter(r["status"] for r in rows)),
        metadata_requests=len(requests),
        request_statuses=dict(Counter(r["status"] for r in prior.values())),
        renderings_sha256=hash_file(output / "renderings.jsonl"),
        ledger_sha256=hash_file(ledger),
        completed_at_utc=utc_now().isoformat(),
    )
    publish(output / "metadata_receipt.json", receipt)
    return receipt


def prepare_images(root: Path, run_id: str) -> dict:
    identifier(run_id)
    output = root / MANIFESTS / run_id
    paths = [
        MANIFESTS / run_id / name
        for name in ("metadata_freeze.json", "metadata_receipt.json", "renderings.jsonl")
    ]
    commit = _commit(root, paths + [SELF, AMENDMENT])
    frozen = dict(
        run_id=run_id,
        recorded_git_commit=commit,
        inputs=bindings(root, paths + [SELF, AMENDMENT]),
        prepared_at_utc=utc_now().isoformat(),
        reviewer_kind="operator_self_check_not_independent_review",
    )
    publish(output / "images_freeze.json", frozen)
    return frozen


def collect_images(root: Path, run_id: str) -> dict:
    identifier(run_id)
    output = root / MANIFESTS / run_id
    frozen = read_json(output / "images_freeze.json")
    verify_bindings(root, frozen["inputs"])
    verify_bindings(root, read_json(output / "metadata_freeze.json")["inputs"])
    if (output / "acquisition_receipt.json").exists():
        raise FileExistsError("rendering acquisition is terminal")
    rows = read_jsonl(output / "renderings.jsonl")
    ledger = output / "image_events.jsonl"
    existing = events(ledger)
    done = {r["work_id"]: r for r in existing if r["kind"] == "terminal"}
    attempts = Counter(r["work_id"] for r in existing if r["kind"] == "attempt")
    with (
        stage_lock(root / WORKSPACE / run_id / ".images.writer.lock"),
        httpx.Client(
            timeout=90,
            follow_redirects=False,
            headers={
                "User-Agent": "LatentArtBench/0.2 research (+https://github.com/isingmodel/latent-art-bench)"
            },
        ) as client,
    ):
        for index, row in enumerate(rows):
            if row["work_id"] in done:
                prior = done[row["work_id"]]
                if (
                    prior["status"] == "acquired"
                    and hash_file(root / prior["raw_path"]) != prior["raw_sha256"]
                ):
                    raise ValueError("acquired rendering changed")
                continue
            outcome = dict(row, kind="terminal", status="failed")
            if row["status"] == "rendering_registered":
                if shutil.disk_usage(root).free < RESERVE_DISK_BYTES + MAX_FILE_BYTES:
                    raise OSError("disk reserve reached; run remains incomplete")
                for attempt in range(attempts[row["work_id"]] + 1, 4):
                    append_event(
                        ledger, dict(kind="attempt", work_id=row["work_id"], attempt=attempt)
                    )
                    try:
                        status, headers, body = fetch(client, row["url"])
                        path, sha = _store(root, run_id, body, "raw")
                        append_event(
                            ledger,
                            dict(
                                kind="response",
                                work_id=row["work_id"],
                                raw_path=path,
                                raw_sha256=sha,
                                http_status=status,
                            ),
                        )
                        outcome.update(
                            raw_path=path, raw_sha256=sha, bytes=len(body), http_status=status
                        )
                        if status == 200:
                            with Image.open(io.BytesIO(body)) as image:
                                image.load()
                                if image.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
                                    raise ValueError("unsupported_format")
                                if image.size != (row["expected_width"], row["expected_height"]):
                                    raise ValueError("rendering_dimensions_mismatch")
                                if min(image.size) < 1024:
                                    raise ValueError("short_side_below_1024")
                                outcome.update(
                                    status="acquired",
                                    error=None,
                                    width=image.width,
                                    height=image.height,
                                    format=image.format,
                                    has_icc=bool(image.info.get("icc_profile")),
                                )
                            break
                        outcome["error"] = f"http_{status}"
                        if status != 429 and status < 500:
                            break
                        delay = wait_seconds(headers.get("retry-after"), attempt)
                    except httpx.TransportError as exc:
                        outcome["error"] = type(exc).__name__
                        delay = wait_seconds(None, attempt)
                    except (ValueError, OSError) as exc:
                        outcome["error"] = str(exc)
                        break
                    if attempt < 3:
                        _sleep(delay)
            done[row["work_id"]] = append_event(ledger, outcome)
            if (index + 1) % 20 == 0 or index + 1 == len(rows):
                print(
                    f"rendering acquisition {index + 1}/{len(rows)} "
                    f"{dict(Counter(r['status'] for r in done.values()))}",
                    flush=True,
                )
            time.sleep(1)
    ordered = [done[r["work_id"]] for r in rows]
    publish(output / "acquisitions.jsonl", ordered, lines=True)
    receipt = dict(
        run_id=run_id,
        terminal_records=len(ordered),
        statuses=dict(Counter(r["status"] for r in ordered)),
        acquisitions_sha256=hash_file(output / "acquisitions.jsonl"),
        ledger_sha256=hash_file(ledger),
        completed_at_utc=utc_now().isoformat(),
    )
    publish(output / "acquisition_receipt.json", receipt)
    return receipt
