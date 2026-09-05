"""Bounded, one-shot localhost image-model access assessment; never reads credentials."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import importlib.metadata
import io
import json
import shutil
import subprocess
import time
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    append_event,
    bindings,
    digest,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)

BASE = "http://127.0.0.1:10532"
MODELS = ("gpt-image-1", "gpt-image-2")
PROTOCOL = Path("studies/painter_feature_generation_v2/MODEL_ASSESSMENT_PROTOCOL_1.0.md")
SELF = Path("src/latent_art_bench/painter_feature_generation_v2/model_assessment.py")
MAX_BYTES = 64 * 1024 * 1024
PROMPT = "A single red circle centered on a plain white background, no text."
PROXY_FILES = (
    "README.md", "packages/openai-oauth/src/images.ts",
    "packages/openai-oauth-core/src/image-models.ts",
    "packages/openai-oauth-core/src/transport.ts", "packages/openai-oauth-core/src/auth.ts",
)


def request_frame() -> list[dict]:
    return [dict(request_id=f"access-{model}", model=model, payload=dict(
        model=model, prompt=PROMPT, size="1024x1024", quality="medium", n=1,
        output_format="png", background="opaque")) for model in MODELS]


def _committed(root: Path, paths: list[Path]) -> str:
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit exact input first: {path}")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def prepare(root: Path, run_id: str, proxy_root: Path, predecessor: str | None = None) -> dict:
    output = root / MANIFESTS / identifier(run_id)
    if output.exists():
        raise FileExistsError(output)
    paths = [PROTOCOL, SELF, Path("uv.lock"), Path("pyproject.toml"),
             Path("src/latent_art_bench/io.py"),
             Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py")]
    if predecessor:
        paths.append(MANIFESTS / identifier(predecessor) / "assessment_receipt.json")
    commit = _committed(root, paths)
    proxy_paths = [Path(p) for p in PROXY_FILES]
    proxy_commit = _committed(proxy_root, proxy_paths)
    publish(output / "requests.jsonl", request_frame(), lines=True)
    receipt = dict(
        schema_version="image-model-access-freeze/1.0", run_id=run_id,
        recorded_git_commit=commit, inputs=bindings(root, paths),
        requests_sha256=hash_file(output / "requests.jsonl"),
        proxy_source=dict(repository="openai-oauth", recorded_git_commit=proxy_commit,
                          files=bindings(proxy_root, proxy_paths)),
        base_url=BASE, maximum_image_attempts=2, predecessor=predecessor,
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
        authorization="2026-09-05 maintainer: use GPT-Image-1 and GPT-Image-2 via local OAuth; "
                      "bounded access assessment only, no paid public API fallback.",
        reviewer_kind="operator_self_check_not_independent_review",
        prepared_at_utc=utc_now().isoformat(),
    )
    publish(output / "assessment_freeze.json", receipt)
    return receipt


def classify_error(status: int | None, payload: object) -> str:
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        error = {}
    message = str(error.get("message", "")).lower()
    if status == 401 or "token is expired" in message or "token refresh failed" in message:
        return "authentication_blocked"
    if status == 429 or error.get("code") in {"rate_limit_exceeded", "insufficient_quota"}:
        return "quota_or_rate_limited"
    if error.get("code") == "moderation_blocked":
        return "refused"
    return "transport_or_schema_failure"


def decode_image(payload: dict) -> tuple[bytes, dict]:
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("expected exactly one image item")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str):
        raise ValueError("expected base64; output URLs are not fetched")
    body = base64.b64decode(encoded, validate=True)
    with Image.open(io.BytesIO(body)) as image:
        image.load()
        if image.format != "PNG" or image.size != (1024, 1024):
            raise ValueError("output format or dimensions differ from frozen request")
        if "A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255):
            raise ValueError("opaque background request not satisfied")
        info = dict(width=image.width, height=image.height, format=image.format,
                    returned_model=payload.get("model"),
                    requested_alias_is_not_snapshot_attestation=True)
    return body, info


def _fetch(client: httpx.Client, root: Path, run_id: str, method: str, endpoint: str,
           request_id: str, payload: dict | None = None) -> tuple[dict, dict]:
    ledger = root / MANIFESTS / run_id / "assessment_events.jsonl"
    append_event(ledger, dict(kind="attempt", request_id=request_id, method=method,
                             endpoint=endpoint, payload_sha256=digest(payload)))
    started = time.monotonic()
    try:
        with client.stream(method, BASE + endpoint, json=payload,
                           timeout=240 if method == "POST" else 30) as response:
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ValueError("response exceeds registered byte ceiling")
                chunks.append(chunk)
            raw = b"".join(chunks)
            relative = WORKSPACE / run_id / "raw" / hashlib.sha256(raw).hexdigest()
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError("content-addressed bytes changed")
            else:
                with target.open("xb") as handle:
                    handle.write(raw)
            try:
                parsed = json.loads(raw)
            except (ValueError, UnicodeError):
                parsed = {}
            parsed = parsed if isinstance(parsed, dict) else {}
            result = dict(kind="response", request_id=request_id,
                          http_status=response.status_code,
                          latency_seconds=time.monotonic() - started,
                          raw_path=str(relative), raw_sha256=hashlib.sha256(raw).hexdigest(),
                          headers={k: response.headers[k] for k in
                                   ("content-type", "date", "x-request-id", "retry-after")
                                   if k in response.headers})
    except (httpx.HTTPError, ValueError, OSError) as exc:
        parsed = {}
        result = dict(kind="response", request_id=request_id, http_status=None,
                      latency_seconds=time.monotonic() - started,
                      error_kind=type(exc).__name__, outcome_uncertain=(method == "POST"))
    append_event(ledger, result)
    return result, parsed


def execute(root: Path, run_id: str, *, transport=None) -> dict:
    identifier(run_id)
    output, workspace = root / MANIFESTS / run_id, root / WORKSPACE / run_id
    freeze = read_json(output / "assessment_freeze.json")
    verify_bindings(root, freeze["inputs"])
    if hash_file(output / "requests.jsonl") != freeze["requests_sha256"]:
        raise ValueError("request frame changed")
    if read_jsonl(output / "requests.jsonl") != request_frame():
        raise ValueError("unexpected access experiment")
    if freeze["base_url"] != BASE or freeze["maximum_image_attempts"] != 2:
        raise ValueError("access scope changed")
    for package, version in freeze["software"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"environment changed: {package}")
    with stage_lock(workspace / ".writer.lock"):
        ledger = output / "assessment_events.jsonl"
        if ledger.exists() or (output / "assessment_receipt.json").exists():
            raise FileExistsError("one-shot assessment already started; never rerun in place")
        if shutil.disk_usage(root).free < 5 * 1024**3:
            raise OSError("less than registered 5 GiB disk reserve")
        with httpx.Client(follow_redirects=False, trust_env=False, transport=transport) as client:
            health, health_data = _fetch(client, root, run_id, "GET", "/health", "health")
            catalog, catalog_data = _fetch(client, root, run_id, "GET", "/v1/models", "catalog")
            ids = [row.get("id") for row in catalog_data.get("data", [])
                   if isinstance(row, dict)] if isinstance(catalog_data.get("data"), list) else []
            ready = (health["http_status"] == 200 and health_data.get("ok") is True
                     and catalog["http_status"] == 200 and all(m in ids for m in MODELS))
            blocker = None if ready else classify_error(catalog["http_status"], catalog_data)
            outcomes = []
            for request in request_frame():
                result = dict(request_id=request["request_id"], model=request["model"],
                              attempted=False, status="not_attempted", blocker=blocker)
                if not blocker:
                    response, payload = _fetch(client, root, run_id, "POST",
                                               "/v1/images/generations", request["request_id"],
                                               request["payload"])
                    result.update(attempted=True, response=response)
                    if response["http_status"] == 200:
                        try:
                            body, info = decode_image(payload)
                            relative = WORKSPACE / run_id / "images" / f"{request['model']}.png"
                            target = root / relative
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with target.open("xb") as handle:
                                handle.write(body)
                            result.update(status="generated", image_path=str(relative),
                                          sha256=hash_file(target), **info)
                        except (ValueError, OSError, binascii.Error) as exc:
                            result.update(status="invalid_output", error_kind=type(exc).__name__)
                    else:
                        result["status"] = classify_error(response["http_status"], payload)
                        stop_statuses = {"authentication_blocked", "quota_or_rate_limited"}
                        if result["status"] in stop_statuses:
                            blocker = result["status"]
                append_event(ledger, dict(kind="model_terminal", **result))
                outcomes.append(result)
        receipt = dict(
            run_id=run_id, scope="access_only_not_artistic_quality_or_fidelity",
            health=health, catalog=catalog, authenticated_catalog=ready,
            catalog_is_not_image_access_proof=True, outcomes=outcomes,
            image_attempts=sum(r["attempted"] for r in outcomes),
            images_generated=sum(r["status"] == "generated" for r in outcomes),
            blocker=blocker, completed_at_utc=utc_now().isoformat(),
            assessment_freeze_sha256=hash_file(output / "assessment_freeze.json"),
            ledger_sha256=hash_file(ledger),
        )
        publish(output / "assessment_receipt.json", receipt)
        return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser(
        "prepare", help="Offline, freeze at most two image requests"
    )
    prepare_parser.add_argument("--run-id", required=True)
    prepare_parser.add_argument("--proxy-root", type=Path, required=True)
    prepare_parser.add_argument("--predecessor")
    execute_parser = commands.add_parser("execute", help="LIVE: readiness and at most two images")
    execute_parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    result = (prepare(args.root.resolve(), args.run_id, args.proxy_root.resolve(), args.predecessor)
              if args.command == "prepare" else execute(args.root.resolve(), args.run_id))
    print(json.dumps(result, indent=2))
    return 0
