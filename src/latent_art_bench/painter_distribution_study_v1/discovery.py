"""Bounded, cached GET-only metadata discovery; this module cannot generate images."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.calibration_record import _verify_commit
from latent_art_bench.painter_prompt_study_v1.common import committed

NAMESPACE = "painter_distribution_study_v1"
RUN_ID = "pdsv1-metadata-20260906"
DIRECTORY = Path("data/manifests") / NAMESPACE / RUN_ID
WORKSPACE = Path("research_workspace") / NAMESPACE / RUN_ID
PROTOCOL = Path("studies") / NAMESPACE / "PROTOCOL.md"
MAX_REQUESTS = 1000
MAX_TOTAL_BYTES = 250 * 1024**2
MAX_RESPONSE_BYTES = 128 * 1024**2
MIN_FREE_BYTES = 5 * 1024**3
ALLOWED = {
    "openrouter.ai": ("/api/v1/images/models", "/api/v1/models", "/api/v1/credits", "/api/v1/key"),
    "api.artic.edu": ("/api/v1/",),
    "collectionapi.metmuseum.org": ("/public/collection/v1/",),
    "api.github.com": ("/repos/NationalGalleryOfArt/opendata/",),
    "raw.githubusercontent.com": ("/NationalGalleryOfArt/opendata/",),
    "api.clevelandart.org": ("/api/artworks",),
    "commons.wikimedia.org": ("/w/api.php",),
    "www.wikidata.org": ("/w/api.php",),
    "query.wikidata.org": ("/sparql",),
}
SOURCE_PATHS = [
    PROTOCOL,
    Path("src/latent_art_bench") / NAMESPACE / "discovery.py",
    Path("tests") / NAMESPACE / "test_discovery.py",
    Path("src/latent_art_bench/io.py"),
    Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
    Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
    Path("src/latent_art_bench/painter_prompt_study_v1/calibration_record.py"),
    Path("pyproject.toml"),
    Path("uv.lock"),
]


def key_from_env(root):
    """Read the single user-specified key without executing shell or dotenv expressions."""
    for line in (root / ".env").read_text().splitlines():
        match = re.fullmatch(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*(.*?)\s*", line)
        if match:
            value = match[1].strip().strip("\"'")
            if not re.fullmatch(r"[A-Za-z0-9_.-]{20,200}", value):
                raise ValueError("OPENROUTER_API_KEY has an unsupported configuration format")
            return value
    raise ValueError("OPENROUTER_API_KEY is not configured in .env")


def validate_url(url):
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.hostname not in ALLOWED
        or parts.username
        or parts.password
        or parts.port not in (None, 443)
        or parts.fragment
    ):
        raise ValueError("metadata URL is outside the declared HTTPS sources")
    if not any(
        parts.path == p or parts.path.startswith(p if p.endswith("/") else p + "/")
        for p in ALLOWED[parts.hostname]
    ):
        raise ValueError("metadata URL path is outside the declared endpoints")
    query = parse_qs(parts.query)
    if set(query) & {"key", "api_key", "token", "access_token", "authorization"}:
        raise ValueError("credentials must never appear in a metadata URL")
    if parts.path == "/w/api.php" and query.get("action") not in (["query"], ["wbgetentities"]):
        raise ValueError("only read-only Wikimedia actions are permitted")
    return parts


def account_projection(body):
    """Keep budget numbers only, never an account label, key hash or user identifier."""
    try:
        data = json.loads(body).get("data", {})
    except (ValueError, AttributeError):
        return {"body_suppressed": True}
    if not isinstance(data, dict):
        return {"body_suppressed": True}
    fields = (
        "total_credits",
        "total_usage",
        "limit",
        "limit_remaining",
        "usage",
        "usage_daily",
        "usage_weekly",
        "usage_monthly",
        "is_free_tier",
    )
    return {
        key: data[key]
        for key in fields
        if key in data and (data[key] is None or isinstance(data[key], (int, float, bool)))
    }


def prepare(root):
    commit = committed(root, SOURCE_PATHS)
    freeze = dict(
        schema_version="painter-distribution-metadata-freeze/1.0",
        run_id=RUN_ID,
        recorded_git_commit=commit,
        allowed_sources=ALLOWED,
        max_requests=MAX_REQUESTS,
        max_total_bytes=MAX_TOTAL_BYTES,
        max_response_bytes=MAX_RESPONSE_BYTES,
        inputs=bindings(root, SOURCE_PATHS),
        authority="PROTOCOL.md Stage B; GET only",
    )
    publish(root / DIRECTORY / "freeze.json", freeze)
    return {"run_id": RUN_ID, "recorded_git_commit": commit, "inputs": len(freeze["inputs"])}


def read_cached(root, row):
    path = root / row["retained_path"]
    if hash_file(path) != row["retained_sha256"]:
        raise ValueError("metadata response cache changed")
    body = gzip.decompress(path.read_bytes())
    if hashlib.sha256(body).hexdigest() != row["body_sha256"]:
        raise ValueError("decompressed metadata response changed")
    return body


def fetch(root, url, *, transport=None, sleep=time.sleep):
    parts = validate_url(url)
    with stage_lock(root / WORKSPACE / ".metadata.writer.lock"):
        directory = root / DIRECTORY
        freeze = read_json(directory / "freeze.json")
        verify_bindings(root, freeze["inputs"])
        committed(root, [DIRECTORY / "freeze.json"])
        if (directory / "terminal_receipt.json").exists():
            raise ValueError("metadata census is terminal")
        ledger = directory / "events.jsonl"
        rows = events(ledger)
        prior = [r for r in rows if r.get("url") == url]
        terminal = [r for r in prior if r["kind"] == "response"]
        if terminal:
            return terminal[-1], read_cached(root, terminal[-1])
        if prior:
            raise ValueError("metadata request has an unresolved attempt; do not redispatch")
        used_requests = sum(r["kind"] == "attempt" for r in rows)
        used_bytes = sum(r.get("received_bytes", 0) for r in rows if r["kind"] == "response")
        if used_requests >= MAX_REQUESTS or used_bytes >= MAX_TOTAL_BYTES:
            raise ValueError("metadata discovery budget exhausted")
        if shutil.disk_usage(root).free < MIN_FREE_BYTES + MAX_RESPONSE_BYTES:
            raise OSError("local storage reserve reached")
        account = parts.hostname == "openrouter.ai" and parts.path in (
            "/api/v1/credits",
            "/api/v1/key",
        )
        secret = key_from_env(root) if account else None
        headers = {"User-Agent": "LatentArtBench/0.3 academic research"}
        if secret:
            headers["Authorization"] = "Bearer " + secret
        # Every network request follows an fsynced event; neither headers nor key enter the ledger.
        append_event(ledger, dict(kind="attempt", url=url, method="GET"))
        body, status, content_type, error, complete = b"", None, None, None, False
        limit = min(MAX_RESPONSE_BYTES, MAX_TOTAL_BYTES - used_bytes)
        chunks, size = [], 0
        try:
            sleep(1.05)
            with httpx.Client(
                timeout=httpx.Timeout(90, connect=20),
                follow_redirects=False,
                headers=headers,
                transport=transport,
            ) as client:
                with client.stream("GET", url) as response:
                    status = response.status_code
                    content_type = response.headers.get("content-type")
                    for chunk in response.iter_bytes(chunk_size=65536):
                        if size + len(chunk) > limit:
                            error = "response_byte_limit"
                            break
                        chunks.append(chunk)
                        size += len(chunk)
                    else:
                        complete = True
        except httpx.HTTPError as exc:
            error = type(exc).__name__
        body = b"".join(chunks)
        received_bytes = len(body)
        if account:
            body = json.dumps(account_projection(body), sort_keys=True).encode()
        if secret and secret.encode() in body:
            body = b'{"body_suppressed":true}'
            error = "credential_echo_suppressed"
        digest = hashlib.sha256(body).hexdigest()
        relative = WORKSPACE / "responses" / (digest + ".body.gz")
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        compressed = gzip.compress(body, mtime=0)
        if path.exists():
            if path.read_bytes() != compressed:
                raise ValueError("metadata content-address collision")
        else:
            with path.open("xb") as stream:
                stream.write(compressed)
        row = append_event(
            ledger,
            dict(
                kind="response",
                url=url,
                status_code=status,
                content_type=content_type,
                complete=complete,
                error=error,
                received_bytes=received_bytes,
                body_sha256=digest,
                account_budget_projection=account,
                retained_path=relative.as_posix(),
                retained_sha256=hash_file(path),
            ),
        )
        return row, body


def close(root):
    with stage_lock(root / WORKSPACE / ".metadata.writer.lock"):
        directory = root / DIRECTORY
        freeze = read_json(directory / "freeze.json")
        _verify_commit(root, freeze["recorded_git_commit"], freeze["inputs"])
        rows = events(directory / "events.jsonl")
        attempts = [r for r in rows if r["kind"] == "attempt"]
        responses = [r for r in rows if r["kind"] == "response"]
        if len(attempts) != len(responses):
            raise ValueError("unresolved metadata attempts prevent terminal closure")
        for row in responses:
            read_cached(root, row)
        receipt = dict(
            run_id=RUN_ID,
            requests=len(attempts),
            received_bytes=sum(r["received_bytes"] for r in responses),
            freeze_sha256=hash_file(directory / "freeze.json"),
            events_sha256=hash_file(directory / "events.jsonl"),
            generation_requests=0,
            recorded_git_commit=freeze["recorded_git_commit"],
        )
        publish(directory / "terminal_receipt.json", receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "get", "close"))
    parser.add_argument("url", nargs="?")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare(root)
    elif args.command == "close":
        result = close(root)
    elif args.url:
        result, _ = fetch(root, args.url)
    else:
        parser.error("get requires an allowed metadata URL")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
