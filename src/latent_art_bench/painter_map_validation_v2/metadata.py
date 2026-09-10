"""Disjoint create-once metadata wrapper around the sealed two-GET primitive."""

import hashlib
import importlib.util
import subprocess
from decimal import Decimal
from pathlib import Path

import httpx

from latent_art_bench.io import hash_file, read_json, utc_now
from latent_art_bench.painter_distribution_study_v1.discovery import key_from_env
from latent_art_bench.painter_feature_generation_v2.artifacts import publish

from . import common

ENDPOINT_HASH = "765c865e57488f2620f6860c6562b4d4696460e442f596c24bdb89895f7ea99d"


def primitive(root):
    spec = importlib.util.spec_from_file_location(
        "_pmv2_sealed_metadata", Path(root) / common.PREFLIGHT_SOURCE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def directory(receipt_id):
    if receipt_id not in (common.PREFLIGHT_ID, common.DISPATCH_ID):
        raise ValueError("only prefreeze and dispatch metadata attempts are authorized")
    return common.MANIFESTS / "metadata" / receipt_id


def run(root, receipt_id, *, live_metadata=False, transport=None):
    if live_metadata is not True and not isinstance(transport, httpx.MockTransport):
        raise ValueError("metadata requires explicit live_metadata=True")
    root = Path(root).resolve()
    destination = root / directory(receipt_id)
    if destination.exists():
        raise ValueError("metadata attempt is create-once")
    # Authentication is used only in the private request header and never recorded.
    source_paths = [
        common.PREFLIGHT_SOURCE,
        common.PACKAGE / "metadata.py",
        common.PACKAGE / "common.py",
    ]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    source = []
    for path in source_paths:
        data = (root / path).read_bytes()
        for revision in (f"{head}:{path}", f":{path}"):
            blob = subprocess.run(["git", "show", revision], cwd=root, capture_output=True)
            if blob.returncode or blob.stdout != data:
                raise ValueError("commit exact metadata source before access")
        source.append(dict(path=str(path), sha256=hashlib.sha256(data).hexdigest()))
    api = primitive(root)
    secret = key_from_env(root)
    destination.mkdir(parents=True, exist_ok=False)
    publish(
        destination / "started.json",
        dict(
            schema="painter-map-validation-metadata-start/2",
            receipt_id=receipt_id,
            started_at_utc=utc_now().isoformat(),
            source_commit=head,
            source_bindings=source,
            allowed_get_urls=list(api.URLS),
            maximum_gets=2,
            redirects=False,
            automatic_retries=0,
        ),
    )
    with httpx.Client(
        timeout=httpx.Timeout(30, connect=15),
        follow_redirects=False,
        trust_env=False,
        transport=transport,
    ) as client:
        rows = [api.fetch(client, url, secret) for url in api.URLS]
    value = dict(
        schema="painter-map-validation-metadata-receipt/2",
        receipt_id=receipt_id,
        status="complete" if all(r["status"] == "ok" for r in rows) else "incomplete",
        ended_at_utc=utc_now().isoformat(),
        source_commit=head,
        source_bindings=source,
        requests=rows,
        started_sha256=hash_file(destination / "started.json"),
        generation_requests=0,
        paid_image_requests=0,
    )
    publish(destination / "receipt.json", value)
    return value


def validate(root, receipt_id):
    root = Path(root)
    path = root / directory(receipt_id)
    value, started = read_json(path / "receipt.json"), read_json(path / "started.json")
    api = primitive(root)
    if (
        value["schema"] != "painter-map-validation-metadata-receipt/2"
        or value["receipt_id"] != receipt_id
        or value["status"] != "complete"
        or value["started_sha256"] != hash_file(path / "started.json")
        or started["source_commit"] != value["source_commit"]
        or started["source_bindings"] != value["source_bindings"]
        or len(value["requests"]) != 2
        or [r["url"] for r in value["requests"]] != list(api.URLS)
        or any(
            r["status"] != "ok" or r["http_status"] != 200 or r["method"] != "GET"
            for r in value["requests"]
        )
    ):
        raise ValueError("complete exact two-GET metadata receipt required")
    for row in value["source_bindings"]:
        blob = subprocess.run(
            ["git", "show", f"{value['source_commit']}:{row['path']}"],
            cwd=root,
            capture_output=True,
        )
        if (
            blob.returncode
            or hashlib.sha256(blob.stdout).hexdigest() != row["sha256"]
            or hash_file(root / row["path"]) != row["sha256"]
        ):
            raise ValueError("metadata source binding differs")
    endpoint = value["requests"][1]
    expected = dict(
        id=common.MODEL,
        provider_slug=api.PROVIDER,
        provider_tag=api.PROVIDER,
        pricing=[dict(billable="output_image", unit="megapixel", cost_usd="0.07")],
    )
    if endpoint["response_body_sha256"] != ENDPOINT_HASH or endpoint["projection"] != expected:
        raise ValueError("exact retained endpoint identity, capabilities and quote required")
    available = Decimal(value["requests"][0]["projection"]["available_usd"])
    if not available.is_finite() or available < Decimal("18.60"):
        raise ValueError("actual credits cannot support the conditional full-plan allowance")
    return value, available
