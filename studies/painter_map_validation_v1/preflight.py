"""One-shot account/model metadata only; no image request or automatic retry."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx

from latent_art_bench.io import utc_now
from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier, publish

MODEL = "black-forest-labs/flux.2-max"
PROVIDER = "black-forest-labs/us-3"
CREDITS = "https://openrouter.ai/api/v1/credits"
ENDPOINTS = f"https://openrouter.ai/api/v1/images/models/{MODEL}/endpoints"
URLS = (CREDITS, ENDPOINTS)
MAX_BYTES = 8 * 1024**2
DIRECTORY = Path("data/manifests/painter_map_validation_v1/metadata")


def amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("unsupported money representation")
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError("invalid nonnegative amount")
    return result


def project(value, url):
    if not isinstance(value, dict):
        raise ValueError("metadata response must be an object")
    if url == CREDITS:
        data = value["data"]
        if not isinstance(data, dict):
            raise ValueError("credit data must be an object")
        available = amount(data["total_credits"]) - amount(data["total_usage"])
        return {"available_usd": str(available)}
    if url != ENDPOINTS or value["id"] != MODEL:
        raise ValueError("unexpected model identity")
    endpoints = value["endpoints"]
    if not isinstance(endpoints, list) or not all(isinstance(p, dict) for p in endpoints):
        raise ValueError("model endpoints must be an object list")
    matches = [p for p in endpoints if p.get("provider_slug") == PROVIDER]
    if len(matches) != 1 or matches[0].get("provider_tag") != PROVIDER:
        raise ValueError("expected provider identity is missing or ambiguous")
    selected = matches[0]
    prices = selected["pricing"]
    if not isinstance(prices, list) or not prices:
        raise ValueError("no endpoint pricing")
    projected = []
    for price in prices:
        if not isinstance(price, dict):
            raise ValueError("each endpoint price must be an object")
        billable, unit = price["billable"], price["unit"]
        if not all(isinstance(x, str) and 0 < len(x) <= 100 for x in (billable, unit)):
            raise ValueError("invalid pricing unit")
        projected.append(
            dict(billable=billable, unit=unit, cost_usd=str(amount(price["cost_usd"])))
        )
    return dict(id=MODEL, provider_slug=PROVIDER, provider_tag=PROVIDER, pricing=projected)


def fetch(client, url, secret):
    if url not in URLS:
        raise ValueError("URL is outside the exact two-GET contract")
    row = dict(method="GET", url=url, started_at_utc=utc_now().isoformat())
    headers = {"Authorization": "Bearer " + secret} if url == CREDITS else {}
    body = bytearray()
    try:
        with client.stream("GET", url, headers=headers) as response:
            row["http_status"] = response.status_code
            for chunk in response.iter_bytes(chunk_size=65536):
                if len(body) + len(chunk) > MAX_BYTES:
                    raise ValueError("response exceeds bound")
                body.extend(chunk)
            row.update(
                response_bytes=len(body), response_body_sha256=hashlib.sha256(body).hexdigest()
            )
            if response.status_code != 200:
                row["status"] = "http_error"
            elif secret.encode() in body:
                row["status"] = "credential_echo_suppressed"
            else:
                projection = project(json.loads(body, parse_float=Decimal), url)
                if secret in json.dumps(projection):
                    row["status"] = "credential_echo_suppressed"
                else:
                    row.update(status="ok", projection=projection)
    except (httpx.HTTPError, ValueError, KeyError, TypeError, InvalidOperation) as exc:
        # Exception messages and response bodies may contain secrets or account fields.
        row.update(status="unavailable", error_class=type(exc).__name__)
    row["ended_at_utc"] = utc_now().isoformat()
    return row


def run(root, receipt_id, *, live_metadata=False, transport=None):
    if live_metadata is not True:
        raise ValueError("explicit live-metadata flag required")
    root = Path(root).resolve()
    directory = root / DIRECTORY / identifier(receipt_id)
    if directory.exists():
        raise FileExistsError("metadata attempt is create-once; no automatic redispatch")
    secret = key_from_env(root)
    source = dict(
        script="studies/painter_map_validation_v1/preflight.py",
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        git_head=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        python=platform.python_version(),
        httpx=httpx.__version__,
        note="Metadata feasibility only; this is not a scientific source/assignment freeze.",
    )
    directory.mkdir(parents=True, exist_ok=False)
    publish(directory / "started.json", dict(
        schema="painter-map-validation-metadata-start/1", receipt_id=receipt_id,
        started_at_utc=utc_now().isoformat(), allowed_get_urls=list(URLS),
        maximum_gets=2, automatic_retries=0, redirects=False,
        maximum_response_bytes=MAX_BYTES, source=source,
    ))
    with httpx.Client(timeout=httpx.Timeout(30, connect=15), follow_redirects=False,
                      trust_env=False, transport=transport) as client:
        results = [fetch(client, url, secret) for url in URLS]
    receipt = dict(
        schema="painter-map-validation-metadata-receipt/1", receipt_id=receipt_id,
        status="complete" if all(r["status"] == "ok" for r in results) else "incomplete",
        ended_at_utc=utc_now().isoformat(), source=source, requests=results,
        started_sha256=hashlib.sha256((directory / "started.json").read_bytes()).hexdigest(),
        generation_requests=0, paid_image_requests=0,
    )
    publish(directory / "receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--receipt-id", required=True)
    parser.add_argument("--live-metadata", action="store_true")
    args = parser.parse_args()
    if not args.live_metadata:
        parser.error("--live-metadata is required; no requests were sent")
    try:
        result = run(args.root, args.receipt_id, live_metadata=True)
    except Exception as exc:
        parser.exit(1, f"Metadata preflight stopped ({type(exc).__name__}); no automatic retry.\n")
    print(json.dumps({"receipt": str(DIRECTORY / args.receipt_id / "receipt.json"),
                      "status": result["status"]}, sort_keys=True))
    raise SystemExit(0 if result["status"] == "complete" else 1)
