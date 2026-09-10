"""One-attempt image transport with committed requests, cost accounting and raw evidence.

This layer inspects container geometry only. It neither extracts fidelity features nor
selects images, and it never retries or switches providers.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import importlib.metadata
import io
import json
import math
import os
import shutil
import subprocess
import time
import warnings
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from .discovery import key_from_env

NAMESPACE = "painter_distribution_study_v1"
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
OPENROUTER_URL = "https://openrouter.ai/api/v1/images"
OAUTH_URL = "http://127.0.0.1:10532/v1/images/generations"
ROUTES = {
    "nano_banana_2": ("google/gemini-3.1-flash-image", "google-ai-studio"),
    "flux_2_max": ("black-forest-labs/flux.2-max", "black-forest-labs/us-3"),
    "oauth_gpt_image_2": ("gpt-image-2", None),
}
PROXY_FILES = (
    "README.md",
    "packages/openai-oauth/src/images.ts",
    "packages/openai-oauth-core/src/image-models.ts",
    "packages/openai-oauth-core/src/transport.ts",
    "packages/openai-oauth-core/src/auth.ts",
    "packages/openai-oauth/src/server.ts",
    "packages/openai-oauth/src/shared.ts",
)
MAX_RESPONSE = 64 * 1024**2
MIN_FREE = 5 * 1024**3
SPENDING_CEILING = 75.0
REQUEST_RESERVATION = 5.0


def payload(route, prompt):
    model, provider = ROUTES[route]
    result = dict(model=model, prompt=prompt, n=1)
    if provider:
        result.update(aspect_ratio="1:1", provider=dict(only=[provider], allow_fallbacks=False))
        if route == "nano_banana_2":
            result["resolution"] = "1K"
        else:
            result["output_format"] = "png"
    else:
        result.update(size="1024x1024", quality="medium", output_format="png", background="opaque")
    return result


def validate_requests(requests):
    if not requests or len(requests) > 1008:
        raise ValueError("invalid bounded request inventory")
    seen = set()
    for sequence, request in enumerate(requests):
        rid, route = identifier(request["request_id"]), request["route"]
        prompt = request["payload"].get("prompt")
        if rid in seen or request["sequence"] != sequence or route not in ROUTES:
            raise ValueError("duplicate or disordered request identity")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
            raise ValueError("prompt is missing or exceeds the fixed text bound")
        if request["payload"] != payload(route, prompt):
            raise ValueError("request differs from the pinned single-image rendering contract")
        seen.add(rid)


def _process(args):
    result = subprocess.run(
        args, capture_output=True, text=True, env=dict(os.environ, TZ="UTC", LC_ALL="C")
    )
    if result.returncode:
        raise ValueError("local proxy identity unavailable")
    return result.stdout.strip()


def proxy_snapshot(proxy_root):
    """Read source identity and selected process fields, never arguments or credentials."""
    source = Path(proxy_root)
    paths = [Path(p) for p in PROXY_FILES]
    commit = committed(source, paths)
    listing = _process(["lsof", "-nP", "-iTCP:10532", "-sTCP:LISTEN", "-Fpn"])
    pids = [line[1:] for line in listing.splitlines() if line.startswith("p")]
    addresses = [line[1:] for line in listing.splitlines() if line.startswith("n")]
    if len(pids) != 1 or not pids[0].isdigit() or addresses != ["127.0.0.1:10532"]:
        raise ValueError("require one IPv4 loopback-only OAuth listener")
    pid = pids[0]
    dirs = _process(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"])
    dirs = [line[1:] for line in dirs.splitlines() if line.startswith("n")]
    if dirs != [str((source / "packages/openai-oauth").resolve())]:
        raise ValueError("OAuth listener source checkout differs")
    executable = Path(_process(["ps", "-p", pid, "-o", "comm="])).name
    if executable != "bun":
        raise ValueError("OAuth listener is not Bun")
    return dict(
        recorded_git_commit=commit,
        files=bindings(source, paths),
        pid=int(pid),
        started_utc=_process(["ps", "-p", pid, "-o", "lstart="]),
        executable=executable,
        address="127.0.0.1",
        port=10532,
        source_directory="packages/openai-oauth",
    )


def inspect_response(body):
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    entries = data.get("data")
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise ValueError("expected exactly one embedded image")
    encoded = entries[0].get("b64_json")
    if not isinstance(encoded, str):
        raise ValueError("expected base64; returned URLs are never fetched")
    raw = base64.b64decode(encoded, validate=True)
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as im:
            if (
                im.format not in ("PNG", "JPEG", "WEBP", "TIFF")
                or im.width * im.height > 20_000_000
            ):
                raise ValueError("unsupported image container or geometry")
            im.load()
            result = dict(
                image_sha256=hashlib.sha256(raw).hexdigest(),
                image_bytes=len(raw),
                width=im.width,
                height=im.height,
                format=im.format,
                mode=im.mode,
                minimum_512=min(im.size) >= 512,
                square_1024=im.size == (1024, 1024),
            )
    # Known rendering fields only; arbitrary provider text is not promoted to trusted metadata.
    result["reported"] = {
        k: data.get(k) for k in ("model", "size", "quality", "output_format", "background")
    }
    return result


def cost_from_response(body, status, paid):
    if not paid:
        return 0.0
    try:
        data = json.loads(body)
        usage = data.get("usage") or {}
        value = usage.get("cost")
        if type(value) in (int, float) and math.isfinite(value) and value >= 0:
            return float(value)
        # A fully received explicit client rejection is non-billable under Image API terms.
        if status in (400, 401, 402, 403, 404, 422, 429) and data.get("error"):
            return 0.0
    except (ValueError, AttributeError):
        pass
    return None


def budget_state(root):
    attempts, terminals, accounted = {}, {}, 0.0
    for path in sorted((root / MANIFESTS).glob("*/generation_events.jsonl")):
        for row in events(path):
            key = path.parent.name, row["request_id"]
            if row["kind"] == "attempt":
                if key in attempts or key in terminals:
                    raise ValueError("duplicate global request attempt")
                attempts[key] = row
            elif row["kind"] == "terminal":
                if key not in attempts or key in terminals:
                    raise ValueError("invalid global terminal accounting")
                terminals[key] = row
                cost = row.get("cost_usd")
                if cost is not None and (
                    type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0
                ):
                    raise ValueError("invalid recorded cost")
                accounted += cost if cost is not None else REQUEST_RESERVATION
            else:
                raise ValueError("unrecognized generation event")
    unresolved = set(attempts) - set(terminals)
    uncertain = [
        k
        for k, r in terminals.items()
        if r["status"] == "outcome_uncertain" or r.get("cost_usd") is None
    ]
    accounted += sum(REQUEST_RESERVATION for k in unresolved if attempts[k]["paid"])
    return dict(
        attempts=len(attempts),
        paid_attempts=sum(r["paid"] for r in attempts.values()),
        accounted_usd=accounted,
        unresolved=len(unresolved),
        uncertain=len(uncertain),
    )


def _send(root, run_id, request, *, transport=None):
    paid = ROUTES[request["route"]][1] is not None
    secret = key_from_env(root) if paid else None
    headers = {"User-Agent": "LatentArtBench/0.3 academic research"}
    if secret:
        headers["Authorization"] = "Bearer " + secret
    url = OPENROUTER_URL if paid else OAUTH_URL
    chunks, size, status, error, complete = [], 0, None, None, False
    started = time.monotonic()
    selected_headers = {}
    try:
        with httpx.Client(
            timeout=httpx.Timeout(240, connect=20),
            follow_redirects=False,
            transport=transport,
            headers=headers,
        ) as client:
            with client.stream("POST", url, json=request["payload"]) as response:
                status = response.status_code
                selected_headers = {
                    k: response.headers[k]
                    for k in ("content-type", "date", "x-request-id", "retry-after")
                    if k in response.headers
                }
                for chunk in response.iter_bytes(chunk_size=65536):
                    if size + len(chunk) > MAX_RESPONSE:
                        error = "response_byte_limit"
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                else:
                    complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    if secret and (secret.encode() in body or any(secret in v for v in selected_headers.values())):
        # A credential echo is quarantined from research logs, never printed or distributed.
        body, selected_headers, error, complete = (
            b'{"credential_echo_suppressed":true}',
            {},
            "credential_echo",
            False,
        )
    sha = hashlib.sha256(body).hexdigest()
    relative = WORKSPACE / run_id / "responses" / (request["request_id"] + ".json.gz")
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(gzip.compress(body, mtime=0))
        handle.flush()
        os.fsync(handle.fileno())
    cost = cost_from_response(body, status, paid) if complete else (None if paid else 0.0)
    outcome = "outcome_uncertain" if not complete else "http_error"
    observed = None
    if complete and status is not None and 200 <= status < 300:
        try:
            observed = inspect_response(body)
            outcome = "image_returned" if observed["minimum_512"] else "invalid_geometry"
        except (
            ValueError,
            TypeError,
            OSError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            outcome, error = "invalid_response", type(exc).__name__
    return dict(
        kind="terminal",
        request_id=request["request_id"],
        route=request["route"],
        status=outcome,
        status_code=status,
        complete=complete,
        error=error,
        cost_usd=cost,
        observed=observed,
        response_headers=selected_headers,
        response_path=relative.as_posix(),
        response_sha256=sha,
        retained_sha256=hash_file(path),
        retained_bytes=path.stat().st_size,
        received_bytes=size,
        latency_seconds=time.monotonic() - started,
    )


def run(root, run_id, proxy_root, *, transport=None, sleep=time.sleep):
    """Run an already committed finite inventory; returning does not authorize retries."""
    run_id = identifier(run_id)
    directory = root / MANIFESTS / run_id
    with stage_lock(root / WORKSPACE / ".generation.writer.lock"):
        freeze = read_json(directory / "generation_freeze.json")
        requests = read_jsonl(directory / "requests.jsonl")
        validate_requests(requests)
        if freeze["run_id"] != run_id or freeze["requests_sha256"] != hash_file(
            directory / "requests.jsonl"
        ):
            raise ValueError("generation inventory changed")
        verify_bindings(root, freeze["inputs"])
        committed(
            root,
            [MANIFESTS / run_id / name for name in ("generation_freeze.json", "requests.jsonl")],
        )
        for package, version in freeze["software"].items():
            if importlib.metadata.version(package) != version:
                raise ValueError("generation software version changed")
        if (directory / "generation_receipt.json").exists():
            raise ValueError("generation run is terminal")
        if freeze.get("authority") != "PILOT.md: 18 technical requests; no research measurement":
            raise ValueError("this execution entry point is restricted to the technical pilot")
        if len(requests) != 18 or any(
            sum(r["route"] == route for r in requests) != 6 for route in ROUTES
        ):
            raise ValueError("pilot requires exactly six requests per route")
        ledger = directory / "generation_events.jsonl"
        rows = events(ledger)
        known = {r["request_id"]: r for r in requests}
        for row in rows:
            if row["request_id"] not in known:
                raise ValueError("event is outside the frozen inventory")
            if row["kind"] == "attempt" and row["request_sha256"] != digest(
                known[row["request_id"]]
            ):
                raise ValueError("recorded attempt differs from the frozen request")
        completed = {r["request_id"]: r for r in rows if r["kind"] == "terminal"}
        for request in requests:
            if request["request_id"] in completed:
                continue
            budget = budget_state(root)
            if budget["unresolved"] or budget["uncertain"]:
                raise ValueError("unresolved outcome/cost prevents further dispatch")
            paid = ROUTES[request["route"]][1] is not None
            if budget["attempts"] >= 1026 or (paid and budget["paid_attempts"] >= 588):
                raise ValueError("study request allocation exhausted")
            if paid and budget["accounted_usd"] + REQUEST_RESERVATION > SPENDING_CEILING:
                raise ValueError("study spending reserve reached")
            if shutil.disk_usage(root).free < MIN_FREE + MAX_RESPONSE:
                raise OSError("storage reserve reached")
            if not paid and proxy_snapshot(proxy_root) != freeze["proxy_source"]:
                raise ValueError("OAuth proxy identity changed")
            sleep(15)
            append_event(
                ledger,
                dict(
                    kind="attempt",
                    request_id=request["request_id"],
                    route=request["route"],
                    paid=paid,
                    request_sha256=digest(request),
                    reservation_usd=REQUEST_RESERVATION if paid else 0.0,
                ),
            )
            result = _send(root, run_id, request, transport=transport)
            append_event(ledger, result)
            print(
                json.dumps(
                    {k: result[k] for k in ("request_id", "status", "status_code", "cost_usd")}
                ),
                flush=True,
            )
            if result["status"] == "outcome_uncertain" or result["cost_usd"] is None:
                raise ValueError("request outcome/cost uncertain; no redispatch")
            if paid and result["cost_usd"] > REQUEST_RESERVATION:
                raise ValueError("cost exceeded conservative reservation; no further dispatch")
            if result["status_code"] in (401, 402, 403, 429):
                raise ValueError("authentication, quota or rate limit stopped this run")
        receipt = dict(
            run_id=run_id,
            requests=len(requests),
            freeze_sha256=hash_file(directory / "generation_freeze.json"),
            events_sha256=hash_file(ledger),
            budget=budget_state(root),
        )
        publish(directory / "generation_receipt.json", receipt)
        return receipt
