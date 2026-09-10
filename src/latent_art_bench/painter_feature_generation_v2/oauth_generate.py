"""Complete bounded OAuth service-alias pilot, with immutable requests and no rerolls."""

from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import io
import json
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    append_event,
    bindings,
    digest,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.corpus import PROMPTS
from latent_art_bench.painter_feature_generation_v2.model_assessment import classify_error

SELF = Path("src/latent_art_bench/painter_feature_generation_v2/oauth_generate.py")
PROTOCOL = Path("studies/painter_feature_generation_v2/PROTOCOL_1.2.md")
CONFIG = Path("configs/painter_feature_generation_v2/oauth_pilot.json")
BASE = "http://127.0.0.1:10532"


def request_grid(config: dict, library: dict) -> list[dict]:
    if (
        config["aliases"] != ["gpt-image-1", "gpt-image-2"]
        or config["repetitions"] != 1
        or config["maximum_requests"] != 160
        or config["base_url"] != BASE
    ):
        raise ValueError("this collector requires the exact bounded two-alias pilot")
    templates = library["templates"]
    if len(templates) != 16 or len({r["template_id"] for r in templates}) != 16:
        raise ValueError("complete unique template census required")
    cells = []
    for template in templates:
        if set(template["named_prompts"]) != set(PAINTER_IDS):
            raise ValueError("all named painter conditions required")
        prompts = {
            "artist_free": template["artist_free_prompt"],
            **{p: r["prompt"] for p, r in template["named_prompts"].items()},
        }
        for condition, prompt in prompts.items():
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError("prompt must be a nonempty exact string")
            key = f"b000-{template['template_id']}-{condition}"
            cells.append(
                dict(
                    cell_id=key,
                    block=0,
                    template_id=template["template_id"],
                    condition=condition,
                    prompt=prompt,
                    order_hash=digest([config["order_salt"], key]),
                )
            )
    rows = []
    for cell in sorted(cells, key=lambda r: r["order_hash"]):
        aliases = list(config["aliases"])
        if int(cell["order_hash"][-1], 16) % 2:
            aliases.reverse()
        for alias in aliases:
            payload = {k: config[k] for k in ("size", "quality", "output_format", "background")}
            payload.update(model=alias, prompt=cell["prompt"], n=1)
            rows.append(
                dict(
                    cell,
                    alias=alias,
                    request_id=f"{alias}-{cell['cell_id']}",
                    payload=payload,
                    sequence=len(rows),
                )
            )
    return rows


def prepare(root: Path, experiment_id: str) -> dict:
    output = root / MANIFESTS / identifier(experiment_id)
    if output.exists():
        raise FileExistsError(output)
    config = read_json(root / CONFIG)
    prior = MANIFESTS / identifier(config["predecessor_access_id"])
    paths = [
        SELF,
        CONFIG,
        PROTOCOL,
        PROMPTS,
        Path("uv.lock"),
        Path("pyproject.toml"),
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/model_assessment.py"),
        prior / "assessment_freeze.json",
        prior / "assessment_receipt.json",
        prior / "response_diagnostics.json",
    ]
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit exact OAuth input first: {path}")
    rows = request_grid(config, read_json(root / PROMPTS))
    publish(output / "requests.jsonl", rows, lines=True)
    frozen = dict(
        experiment_id=experiment_id,
        config=config,
        requests=len(rows),
        requests_sha256=hash_file(output / "requests.jsonl"),
        inputs=bindings(root, paths),
        recorded_git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
        authorization="2026-09-05 maintainer: keep implementing the analysis using Codex OAuth; "
        "160-request exploratory grid under amendment 1.2; no paid fallback.",
        reviewer_kind="operator_self_check_not_independent_review",
        prepared_at_utc=utc_now().isoformat(),
    )
    publish(output / "generation_freeze.json", frozen)
    return frozen


def _store(root: Path, experiment_id: str, body: bytes, branch: str) -> tuple[str, str]:
    sha = hashlib.sha256(body).hexdigest()
    relative = WORKSPACE / experiment_id / branch / sha
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if hash_file(target) != sha:
            raise ValueError("retained bytes changed")
    else:
        with target.open("xb") as handle:
            handle.write(body)
    return str(relative), sha


def decode(payload: dict, request: dict, minimum_short_side: int) -> tuple[bytes, dict]:
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("expected exactly one returned image")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str):
        raise ValueError("expected base64, output URLs are never followed")
    body = base64.b64decode(encoded, validate=True)
    with Image.open(io.BytesIO(body)) as image:
        image.load()
        if image.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
            raise ValueError("unsupported returned image format")
        if min(image.size) < minimum_short_side:
            raise ValueError("returned image would require upsampling")
        observed = dict(
            width=image.width,
            height=image.height,
            format=image.format,
            mode=image.mode,
            decoded_size=f"{image.width}x{image.height}",
        )
    reported = {
        k: payload.get(k)
        for k in ("model", "size", "quality", "output_format", "background", "usage")
    }
    mismatch = [
        k
        for k in ("size", "quality", "output_format", "background")
        if reported[k] is not None and reported[k] != request["payload"][k]
    ]
    if observed["decoded_size"] != request["payload"]["size"]:
        mismatch.append("decoded_size")
    return body, dict(
        **observed,
        reported=reported,
        requested_returned_mismatches=mismatch,
        model_snapshot_independently_verified=False,
    )


def _request(
    client: httpx.Client, root: Path, experiment_id: str, request: dict, config: dict
) -> dict:
    chunks, size, status, headers, error, partial = [], 0, None, {}, None, False
    started = time.monotonic()
    try:
        with client.stream(
            "POST",
            BASE + "/v1/images/generations",
            json=request["payload"],
            timeout=config["timeout_seconds"],
        ) as response:
            status = response.status_code
            headers = {
                k: response.headers[k]
                for k in ("content-type", "date", "x-request-id", "retry-after")
                if k in response.headers
            }
            for chunk in response.iter_bytes():
                remaining = config["maximum_response_bytes"] - size
                chunks.append(chunk[:remaining])
                size += min(len(chunk), remaining)
                if len(chunk) > remaining:
                    raise ValueError("response_ceiling")
    except (httpx.HTTPError, ValueError, OSError) as exc:
        error, partial = type(exc).__name__, True
    body = b"".join(chunks)
    raw_path, raw_sha = _store(root, experiment_id, body, "responses")
    result = dict(
        request_id=request["request_id"],
        http_status=status,
        latency_seconds=time.monotonic() - started,
        headers=headers,
        raw_path=raw_path,
        raw_sha256=raw_sha,
        partial_body=partial,
        bytes=len(body),
        outcome_uncertain=partial,
    )
    if error:
        return dict(result, status="transport_failure", error_kind=error)
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("response is not an object")
        if status != 200:
            return dict(result, status=classify_error(status, payload))
        image, info = decode(payload, request, config["minimum_decoded_short_side"])
        path, sha = _store(root, experiment_id, image, "generated")
        return dict(result, status="generated", image_path=path, sha256=sha, **info)
    except (ValueError, KeyError, OSError) as exc:
        return dict(result, status="invalid_output", error_kind=type(exc).__name__)


def execute(root: Path, experiment_id: str, *, transport=None, sleep=time.sleep) -> dict:
    identifier(experiment_id)
    output = root / MANIFESTS / experiment_id
    freeze = read_json(output / "generation_freeze.json")
    verify_bindings(root, freeze["inputs"])
    if hash_file(output / "requests.jsonl") != freeze["requests_sha256"]:
        raise ValueError("generation requests changed")
    for package, version in freeze["software"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"generation environment changed: {package}")
    config = freeze["config"]
    requests = read_jsonl(output / "requests.jsonl")
    if requests != request_grid(config, read_json(root / PROMPTS)):
        raise ValueError("registered grid differs from its contract")
    with stage_lock(root / WORKSPACE / experiment_id / ".generation.writer.lock"):
        if (output / "generation_receipt.json").exists():
            raise FileExistsError("generation is terminal")
        ledger = output / "generation_events.jsonl"
        prior = events(ledger)
        done = {r["request_id"]: r for r in prior if r["kind"] == "terminal"}
        attempted = {r["request_id"] for r in prior if r["kind"] == "attempt"}
        if attempted - set(done):
            raise ValueError("interrupted outcome uncertain; never automatically reroll")
        for row in done.values():
            if row.get("raw_path") and hash_file(root / row["raw_path"]) != row["raw_sha256"]:
                raise ValueError("retained response changed")
            if (
                row["status"] == "generated"
                and hash_file(root / row["image_path"]) != row["sha256"]
            ):
                raise ValueError("retained generated bytes changed")
        stop_statuses = {"authentication_blocked", "quota_or_rate_limited"}
        stopped = next((r["status"] for r in done.values() if r["status"] in stop_statuses), None)
        last_start = time.monotonic()
        with httpx.Client(follow_redirects=False, trust_env=False, transport=transport) as client:
            for request in requests:
                if request["request_id"] in done:
                    continue
                if shutil.disk_usage(root).free < config["reserve_disk_bytes"]:
                    raise OSError("disk reserve reached; never select a convenient prefix")
                result = {
                    k: request[k]
                    for k in (
                        "request_id",
                        "alias",
                        "block",
                        "template_id",
                        "condition",
                        "sequence",
                    )
                }
                if stopped:
                    result.update(status="not_attempted", blocker=stopped, attempted=False)
                else:
                    delay = config["minimum_start_interval_seconds"] - (
                        time.monotonic() - last_start
                    )
                    if delay > 0:
                        sleep(delay)
                    last_start = time.monotonic()
                    append_event(
                        ledger,
                        dict(
                            kind="attempt",
                            request_id=request["request_id"],
                            request_sha256=digest(request),
                        ),
                    )
                    result.update(
                        _request(client, root, experiment_id, request, config), attempted=True
                    )
                    if result["status"] in {"authentication_blocked", "quota_or_rate_limited"}:
                        stopped = result["status"]
                done[request["request_id"]] = append_event(ledger, dict(result, kind="terminal"))
                print(
                    f"OAuth generation {len(done)}/{len(requests)} "
                    f"{dict(Counter(r['status'] for r in done.values()))}",
                    flush=True,
                )
        ordered = [done[r["request_id"]] for r in requests]
        publish(output / "outputs.jsonl", ordered, lines=True)
        receipt = dict(
            experiment_id=experiment_id,
            analysis_kind=config["analysis_kind"],
            expected_requests=len(requests),
            terminal_requests=len(ordered),
            image_attempts=sum(r["attempted"] for r in ordered),
            statuses=dict(Counter(r["status"] for r in ordered)),
            complete_generated_grid=all(r["status"] == "generated" for r in ordered),
            stopped_on=stopped,
            freeze_sha256=hash_file(output / "generation_freeze.json"),
            ledger_sha256=hash_file(ledger),
            outputs_sha256=hash_file(output / "outputs.jsonl"),
            completed_at_utc=utc_now().isoformat(),
        )
        publish(output / "generation_receipt.json", receipt)
        return receipt
