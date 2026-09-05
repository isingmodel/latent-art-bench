"""Bounded serial OAuth generation with durable intents and lossless response retention."""

from __future__ import annotations

import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import time
import warnings
from collections import Counter
from pathlib import Path

import httpx
import numpy as np
from PIL import Image

from latent_art_bench.io import canonical_json, hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    digest,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.model_assessment import classify_error
from latent_art_bench.painter_feature_generation_v2.oauth_generate import decode
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS

from .calibration_record import _verify_commit

MANIFESTS = Path("data/manifests/painter_prompt_study_v1")
WORKSPACE = Path("research_workspace/painter_prompt_study_v1")
BASE = "http://127.0.0.1:10532"
ALIASES = ("gpt-image-1", "gpt-image-2")
MAX_RESPONSE_BYTES = 64 * 1024 * 1024
RESERVE_DISK_BYTES = 5 * 1024**3
RENDER = dict(size="1024x1024", quality="medium", output_format="png", background="opaque")
STOP_STATUSES = {"authentication_blocked", "quota_or_rate_limited", "resource_ceiling",
                 "outcome_uncertain"}
HEADER_NAMES = ("content-type", "content-encoding", "date", "x-request-id", "retry-after")


def _integer(value, minimum: int) -> bool:
    return type(value) is int and value >= minimum


def _validate_config(config: dict) -> None:
    repetitions = config["repetitions"]
    if config.get("primary_estimator") != "paired_randomization":
        raise ValueError("new generation requires the paired-randomization design")
    if not _integer(repetitions, 1) or repetitions not in (1, 2, 4):
        raise ValueError("small-grid randomization requires one, two, or four repetitions")
    if not _integer(config.get("order_seed"), 0):
        raise ValueError("method assignment requires a frozen nonnegative integer seed")
    if (tuple(config["aliases"]) != ALIASES or tuple(config["method_ids"]) != METHOD_IDS
            or config["maximum_requests"] != 480 * repetitions):
        raise ValueError("the complete two-alias, three-method grid is required")
    if config["base_url"] != BASE or any(config[k] != v for k, v in RENDER.items()):
        raise ValueError("the frozen loopback route and render settings are required")
    if (not _integer(config["maximum_response_bytes"], 1)
            or config["maximum_response_bytes"] > MAX_RESPONSE_BYTES
            or not _integer(config["max_runtime_bytes"], 1)
            or not _integer(config["reserve_disk_bytes"], RESERVE_DISK_BYTES)
            or type(config["timeout_seconds"]) not in (float, int)
            or not math.isfinite(config["timeout_seconds"])
            or not 0 < config["timeout_seconds"] <= 240
            or type(config["minimum_start_interval_seconds"]) not in (float, int)
            or not math.isfinite(config["minimum_start_interval_seconds"])
            or config["minimum_start_interval_seconds"] < 15
            or config.get("minimum_decoded_short_side", 512) != 512):
        raise ValueError("invalid transport or resource limits")


def request_grid(config: dict, library: dict) -> list[dict]:
    """Return the complete prospective assignment under the selected frozen experiment design."""
    _validate_config(config)
    if (tuple(library["method_ids"]) != METHOD_IDS
            or tuple(library["conditions"]) != CONDITIONS):
        raise ValueError("prompt-library method or condition roster changed")
    lookup = {}
    for row in library["prompts"]:
        key = row["method_id"], row["template_id"], row["condition"]
        prompt = row["prompt"]
        if (key in lookup or not isinstance(prompt, str) or not prompt.strip()
                or hashlib.sha256(prompt.encode()).hexdigest() != row["prompt_sha256"]):
            raise ValueError("duplicate, empty or changed literal prompt")
        lookup[key] = prompt
    expected = {(m, t, c) for m in METHOD_IDS for t in TEMPLATE_IDS for c in CONDITIONS}
    if set(lookup) != expected:
        raise ValueError("all 240 unique method/template/condition prompts are required")
    return _randomized_grid(config, lookup)


def _randomized_grid(config: dict, lookup: dict) -> list[dict]:
    """Uniformly randomize all three methods independently inside every alias triplet.

    PCG64 draws separate cell, alias, and method permutations prospectively. Fixing the
    third method's slot leaves the other two methods exchangeable within that triplet;
    no reversal or common method permutation couples distinct assignment units.
    """
    rng = np.random.Generator(np.random.PCG64(config["order_seed"]))
    cells = [(template, condition) for template in TEMPLATE_IDS for condition in CONDITIONS]
    rows = []
    for block in range(config["repetitions"]):
        for cell_position, cell_index in enumerate(rng.permutation(len(cells))):
            template, condition = cells[int(cell_index)]
            for alias_position, alias_index in enumerate(rng.permutation(len(ALIASES))):
                alias = ALIASES[int(alias_index)]
                methods = [METHOD_IDS[int(index)] for index in rng.permutation(len(METHOD_IDS))]
                unit = f"b{block:04d}-{template}-{condition}-{alias}"
                order_hash = digest([config["order_seed"], block, cell_position, alias, methods])
                for method_position, method in enumerate(methods):
                    prompt = lookup[method, template, condition]
                    rows.append(dict(
                        sequence=len(rows),
                        request_id=f"b{block:04d}-{template}-{condition}-{method}-{alias}",
                        block=block, alias=alias, method_id=method, condition=condition,
                        template_id=template, prompt=prompt,
                        payload=dict(RENDER, model=alias, prompt=prompt, n=1),
                        assignment_unit_id=unit, cell_position=cell_position,
                        alias_position=alias_position, method_position=method_position,
                        treatment_position=3 * alias_position + method_position,
                        order_hash=order_hash,
                    ))
    return rows


def _load(root: Path, run_id: str) -> tuple[Path, dict, list[dict]]:
    directory = root / MANIFESTS / identifier(run_id)
    directory.resolve().relative_to(root.resolve())
    directory.resolve().relative_to((root / MANIFESTS).resolve())
    freeze = read_json(directory / "generation_freeze.json")
    if freeze["run_id"] != run_id:
        raise ValueError("generation freeze run identity changed")
    config_path = freeze.get("config_path")
    if not isinstance(config_path, str) or not config_path or "\\" in config_path:
        raise ValueError("generation freeze requires a portable bound configuration path")
    relative = Path(config_path)
    if (relative.is_absolute() or ".." in relative.parts or relative.as_posix() != config_path
            or sum(row["path"] == config_path for row in freeze["inputs"]) != 1):
        raise ValueError("configuration path must identify exactly one portable frozen input")
    configuration = root / relative
    configuration.resolve().relative_to(root.resolve())
    if read_json(configuration) != freeze["config"]:
        raise ValueError("embedded configuration differs from the frozen configuration source")
    _validate_authorization(root, freeze)
    verify_bindings(root, freeze["inputs"])
    _verify_commit(root, freeze["recorded_git_commit"], freeze["inputs"])
    for filename, key in (("requests.jsonl", "requests_sha256"),
                          ("prompts.json", "library_sha256")):
        if hash_file(directory / filename) != freeze[key]:
            raise ValueError(f"frozen {filename} changed")
    for package in freeze["software"]:
        if importlib.metadata.version(package) != freeze["software"][package]:
            raise ValueError(f"generation environment changed: {package}")
    requests = read_jsonl(directory / "requests.jsonl")
    if requests != request_grid(freeze["config"], read_json(directory / "prompts.json")):
        raise ValueError("requests differ from the exact frozen prompt grid")
    return directory, freeze, requests


def _validate_authorization(root: Path, freeze: dict) -> None:
    """Recheck the generation gate even when a freeze was supplied without prepare()."""
    from .design import validate_config, validate_study_calibration

    config = freeze["config"]
    validate_config(config, authorized=True)
    decision = validate_study_calibration(root, config)
    if (decision["primary_estimator"] != config["primary_estimator"]
            or decision["simultaneous_alpha"] != config["simultaneous_alpha"]
            or config["repetitions"] not in decision["qualified_repetitions"]
            or decision["uses_empirical_outcomes_for_tuning"] is not False):
        raise ValueError("frozen generation design lacks qualified prospective calibration")


def _process_output(arguments: list[str]) -> str:
    """Read only selected process fields, never command arguments or credentials."""
    result = subprocess.run(arguments, capture_output=True, text=True,
                            env=dict(os.environ, TZ="UTC", LC_ALL="C"))
    if result.returncode:
        raise ValueError("the frozen loopback proxy process is unavailable")
    return result.stdout.strip()


def proxy_identity(proxy_root: Path) -> dict:
    """Identify the macOS loopback listener without network requests or secret-bearing argv."""
    listing = _process_output(["lsof", "-nP", "-iTCP:10532", "-sTCP:LISTEN", "-Fpn"])
    processes = [line[1:] for line in listing.splitlines() if line.startswith("p")]
    addresses = [line[1:] for line in listing.splitlines() if line.startswith("n")]
    if (len(processes) != 1 or not processes[0].isdigit()
            or addresses != ["127.0.0.1:10532"]):
        raise ValueError("require one IPv4 loopback-only proxy listener on port 10532")
    pid = processes[0]
    cwd = _process_output(["lsof", "-a", "-p", pid, "-d", "cwd", "-Fn"])
    directories = [line[1:] for line in cwd.splitlines() if line.startswith("n")]
    expected = (Path(proxy_root) / "packages/openai-oauth").resolve()
    if len(directories) != 1 or Path(directories[0]).resolve() != expected:
        raise ValueError("proxy listener is not running from the bound source checkout")
    started = _process_output(["ps", "-p", pid, "-o", "lstart="])
    executable = Path(_process_output(["ps", "-p", pid, "-o", "comm="])).name
    if not started or executable != "bun":
        raise ValueError("proxy listener is not the expected Bun process")
    return dict(pid=int(pid), started_utc=started, executable=executable,
                address="127.0.0.1", port=10532, source_directory="packages/openai-oauth")


def _verify_proxy(freeze: dict, proxy_root: Path, *, verify_commit: bool = True) -> None:
    from .design import PROXY_BINDINGS

    source = freeze["proxy_source"]
    records = source["files"]
    if (source["repository"] != "openai-oauth" or len(records) != len(PROXY_BINDINGS)
            or {r["path"] for r in records} != set(PROXY_BINDINGS)):
        raise ValueError("proxy source input inventory differs from the frozen route")
    verify_bindings(proxy_root, records)
    if verify_commit:
        _verify_commit(proxy_root, source["recorded_git_commit"], records)
    if proxy_identity(proxy_root) != source["listener"]:
        raise ValueError("proxy listener identity changed; no further request is authorized")


class _Journal:
    """One validated chain per execution, then O(1) durable appends under the stage lock."""

    def __init__(self, path: Path):
        self.path = path
        self.rows = events(path)
        if any(row["sequence"] != index for index, row in enumerate(self.rows)):
            raise ValueError("journal sequence changed")
        if path.exists() and path.stat().st_size:
            with path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    raise ValueError("journal lacks a complete final newline")
        self.previous = self.rows[-1]["event_sha256"] if self.rows else None
        self.sequence = len(self.rows)

    def append(self, payload: dict) -> dict:
        row = dict(payload, sequence=self.sequence, at_utc=utc_now().isoformat(),
                   previous_sha256=self.previous)
        row["event_sha256"] = digest(row)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.previous, self.sequence = row["event_sha256"], self.sequence + 1
        return row


def _identity(request: dict) -> dict:
    identity = dict(request_sequence=request["sequence"], **{k: request[k] for k in
                    ("request_id", "block", "alias", "method_id", "condition", "template_id")})
    identity.update({key: request[key] for key in
                     ("assignment_unit_id", "cell_position", "alias_position", "method_position",
                      "treatment_position", "order_hash") if key in request})
    return identity


def _state(rows: list[dict], requests: list[dict]) -> tuple[dict, dict]:
    known = {r["request_id"]: r for r in requests}
    attempts, terminal = {}, {}
    for row in rows:
        key = row["request_id"]
        if key not in known or key in terminal:
            raise ValueError("unknown or multiply terminal journal request")
        if row["kind"] == "attempt":
            if key in attempts or row["request_sha256"] != digest(known[key]):
                raise ValueError("duplicate attempt or changed request intent")
            attempts[key] = row
        elif row["kind"] == "terminal":
            if (any(row.get(k) != v for k, v in _identity(known[key]).items())
                    or row.get("attempted") is not (key in attempts)
                    or (row["status"] == "not_attempted") == (key in attempts)):
                raise ValueError("terminal accounting disagrees with request intent")
            terminal[key] = row
        else:
            raise ValueError("unrecognized generation journal event")
    return attempts, terminal


def _response_path(root: Path, run_id: str, row: dict) -> Path:
    expected = WORKSPACE / run_id / "responses" / f"{row['response_sha256']}.json.gz"
    if row["response_path"] != expected.as_posix():
        raise ValueError("retained response path changed")
    target = root / expected
    target.resolve().relative_to((root / WORKSPACE / run_id).resolve())
    return target


def _verify_retained(root: Path, run_id: str, terminal: dict,
                     maximum_bytes: int = MAX_RESPONSE_BYTES) -> None:
    checked = set()
    for row in terminal.values():
        if "response_path" not in row:
            continue
        key = row["response_path"], row["response_sha256"], row["stored_sha256"]
        if key in checked:
            continue
        path = _response_path(root, run_id, row)
        if hash_file(path) != row["stored_sha256"]:
            raise ValueError("retained compressed response changed")
        with gzip.open(path, "rb") as handle:
            raw = handle.read(maximum_bytes + 1)
        if len(raw) > maximum_bytes or hashlib.sha256(raw).hexdigest() != row["response_sha256"]:
            raise ValueError("retained raw response changed")
        checked.add(key)


def _runtime_bytes(workspace: Path) -> int:
    total = 0
    for path in workspace.rglob("*"):
        if path.is_symlink():
            raise ValueError("runtime workspace must not contain symlinks")
        if path.is_file():
            total += path.stat().st_size
    return total


def _retain(root: Path, run_id: str, body: bytes, available: int) -> tuple[dict, int]:
    raw_sha = hashlib.sha256(body).hexdigest()
    compressed = gzip.compress(body, mtime=0)
    stored_sha = hashlib.sha256(compressed).hexdigest()
    relative = WORKSPACE / run_id / "responses" / f"{raw_sha}.json.gz"
    target = root / relative
    if target.exists():
        if hash_file(target) != stored_sha:
            raise ValueError("retained response CAS collision or changed bytes")
        added = 0
    else:
        if len(compressed) > available:
            raise OSError("compressed response would exceed the frozen runtime byte cap")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(compressed)
            handle.flush()
            os.fsync(handle.fileno())
        added = len(compressed)
    return dict(response_path=relative.as_posix(), response_sha256=raw_sha,
                stored_sha256=stored_sha, stored_bytes=len(compressed), bytes=len(body)), added


def _error_status(status_code, payload):
    classified = classify_error(status_code, payload)
    return ("authentication_blocked" if status_code == 403 and classified != "refused"
            else classified)


def _request(client, root, run_id, request, config, available):
    """Retain raw bytes with a per-I/O timeout; elapsed checks occur between received chunks."""
    chunks, size, status_code, headers = [], 0, None, {}
    partial, error, exceeded = False, None, False
    started = time.monotonic()
    try:
        with client.stream("POST", BASE + "/v1/images/generations", json=request["payload"],
                           timeout=config["timeout_seconds"]) as response:
            status_code = response.status_code
            headers = {k: response.headers[k] for k in HEADER_NAMES if k in response.headers}
            for chunk in response.iter_raw():
                remaining = config["maximum_response_bytes"] - size
                chunks.append(chunk[:remaining])
                size += min(len(chunk), remaining)
                if len(chunk) > remaining:
                    exceeded = True
                    raise ValueError("response_ceiling")
                if time.monotonic() - started > config["timeout_seconds"]:
                    raise httpx.ReadTimeout("response duration exceeded at a received chunk")
    except (httpx.HTTPError, ValueError, OSError) as exc:
        partial, error = True, type(exc).__name__
    raw = b"".join(chunks)
    retained, added = _retain(root, run_id, raw, available)
    result = dict(retained, http_status=status_code, headers=headers,
                  latency_seconds=time.monotonic() - started, partial_body=partial,
                  outcome_uncertain=partial)
    if error:
        failure = "resource_ceiling" if exceeded else "transport_failure"
        if status_code in (401, 403, 429):
            failure = _error_status(status_code, {})
        return dict(result, status=failure,
                    error_kind=error), added
    if status_code != 200:
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            payload = {}
        return dict(result, status=_error_status(status_code, payload)), added
    try:
        if headers.get("content-encoding", "identity") != "identity":
            raise ValueError("unexpected encoded response; raw representation retained")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("response must be a JSON object")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image, info = decode(payload, request, config.get("minimum_decoded_short_side", 512))
        return dict(result, status="generated", sha256=hashlib.sha256(image).hexdigest(),
                    decoded_bytes=len(image), **info), added
    except (ValueError, KeyError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        return dict(result, status="invalid_output", error_kind=type(exc).__name__), added


def _publish_or_verify(path: Path, value, *, lines: bool = False) -> None:
    if path.exists():
        original = read_jsonl(path) if lines else read_json(path)
        if original != value:
            raise ValueError(f"existing terminal artifact differs: {path.name}")
    else:
        publish(path, value, lines=lines)


def _finish(directory, freeze, requests, terminal, stopped):
    ordered = [terminal[r["request_id"]] for r in requests]
    _publish_or_verify(directory / "outputs.jsonl", ordered, lines=True)
    receipt = dict(
        schema_version="painter-prompt-study-generation-receipt/1.0", run_id=freeze["run_id"],
        terminal=True, status="aborted" if stopped else "complete", stopped_on=stopped,
        expected_requests=len(requests), terminal_requests=len(ordered),
        image_attempts=sum(r["attempted"] for r in ordered),
        statuses=dict(Counter(r["status"] for r in ordered)),
        complete_generated_grid=all(r["status"] == "generated" for r in ordered),
        freeze_sha256=hash_file(directory / "generation_freeze.json"),
        ledger_sha256=hash_file(directory / "generation_events.jsonl"),
        outputs_sha256=hash_file(directory / "outputs.jsonl"),
        completed_at_utc=utc_now().isoformat(),
    )
    publish(directory / "generation_receipt.json", receipt)
    return receipt


def _snapshot(run_id, requests, attempts, terminal, reason=None, runtime_bytes=None):
    return dict(
        run_id=run_id, terminal=False, status=reason or "ready", expected_requests=len(requests),
        image_attempts=len(attempts), terminal_requests=len(terminal),
        remaining_requests=len(requests) - len(terminal),
        pending_intents=sorted(set(attempts) - set(terminal)),
        statuses=dict(Counter(r["status"] for r in terminal.values())),
        runtime_bytes=runtime_bytes,
    )


def status(root: Path, run_id: str) -> dict:
    """Read current accounting and verify the journal without creating any file or request."""
    root = Path(root).resolve()
    directory, freeze, requests = _load(root, run_id)
    journal = _Journal(directory / "generation_events.jsonl")
    attempts, terminal = _state(journal.rows, requests)
    receipt_path = directory / "generation_receipt.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        ordered = [terminal.get(r["request_id"]) for r in requests]
        if (receipt["freeze_sha256"] != hash_file(directory / "generation_freeze.json")
                or receipt["ledger_sha256"] != hash_file(journal.path)
                or receipt["outputs_sha256"] != hash_file(directory / "outputs.jsonl")
                or len(terminal) != len(requests)
                or read_jsonl(directory / "outputs.jsonl") != ordered
                or receipt["expected_requests"] != len(requests)
                or receipt["terminal_requests"] != len(terminal)
                or receipt["image_attempts"] != len(attempts)
                or receipt["statuses"] != dict(Counter(r["status"] for r in terminal.values()))
                or receipt["complete_generated_grid"] is not
                all(r["status"] == "generated" for r in terminal.values())):
            raise ValueError("terminal generation evidence changed")
        return receipt
    return _snapshot(run_id, requests, attempts, terminal,
                     "in_flight_or_interrupted" if set(attempts) - set(terminal) else "ready",
                     _runtime_bytes(root / WORKSPACE / run_id))


def execute(root: Path, run_id: str, *, transport=None, sleep=time.sleep,
            max_new_requests: int | None = None, proxy_root: Path | None = None) -> dict:
    """Dispatch each prospective request at most once; batches resume only unattempted cells."""
    if max_new_requests is not None and not _integer(max_new_requests, 0):
        raise ValueError("max_new_requests must be a nonnegative integer")
    root = Path(root).resolve()
    directory, freeze, requests = _load(root, run_id)
    if transport is None and proxy_root is None:
        raise ValueError("live generation requires the explicitly bound proxy source checkout")
    frozen_digest = digest(freeze)
    config = freeze["config"]
    workspace = root / WORKSPACE / run_id
    workspace.resolve().relative_to((root / WORKSPACE).resolve())
    with stage_lock(workspace / ".generation.writer.lock"):
        if digest(read_json(directory / "generation_freeze.json")) != frozen_digest:
            raise ValueError("generation freeze changed before the writer lock")
        verify_bindings(root, freeze["inputs"])
        _validate_authorization(root, freeze)
        if (directory / "generation_receipt.json").exists():
            raise FileExistsError("generation run is permanently terminal")
        journal = _Journal(directory / "generation_events.jsonl")
        attempts, terminal = _state(journal.rows, requests)
        _verify_retained(root, run_id, terminal, config["maximum_response_bytes"])
        runtime_bytes = _runtime_bytes(workspace)
        pending = set(attempts) - set(terminal)
        stopped = "outcome_uncertain" if pending else next(
            (r["status"] if r["status"] in STOP_STATUSES else "outcome_uncertain"
             for r in terminal.values() if r["status"] in STOP_STATUSES
             or r.get("outcome_uncertain")), None)
        if pending:
            for request in requests:
                if request["request_id"] in pending:
                    terminal[request["request_id"]] = journal.append(dict(
                        _identity(request), kind="terminal", status="outcome_uncertain",
                        attempted=True, outcome_uncertain=True, partial_body=True,
                        blocker="interrupted_after_durable_attempt_intent",
                    ))
        if transport is None and not stopped and max_new_requests != 0:
            _verify_proxy(freeze, proxy_root)
        dispatched = 0
        status_counts = Counter(row["status"] for row in terminal.values())
        last_start = time.monotonic()
        # gzip framing and worst-case deflate overhead fit inside this conservative allowance.
        allowance = config["maximum_response_bytes"] + 65536
        with httpx.Client(follow_redirects=False, trust_env=False, transport=transport,
                          headers={"Accept-Encoding": "identity"}) as client:
            for request in requests:
                key = request["request_id"]
                if key in terminal:
                    continue
                identity = _identity(request)
                if stopped:
                    terminal[key] = journal.append(dict(
                        identity, kind="terminal", status="not_attempted", attempted=False,
                        blocker=stopped, outcome_uncertain=False,
                    ))
                    status_counts["not_attempted"] += 1
                    continue
                if max_new_requests is not None and dispatched >= max_new_requests:
                    return _snapshot(run_id, requests, attempts, terminal,
                                     "paused_batch_limit", runtime_bytes)
                if runtime_bytes + allowance > config["max_runtime_bytes"]:
                    return _snapshot(run_id, requests, attempts, terminal,
                                     "paused_runtime_budget", runtime_bytes)
                if shutil.disk_usage(workspace).free < config["reserve_disk_bytes"] + allowance:
                    return _snapshot(run_id, requests, attempts, terminal,
                                     "paused_disk_reserve", runtime_bytes)
                delay = config["minimum_start_interval_seconds"] - (time.monotonic() - last_start)
                if delay > 0:
                    sleep(delay)
                if digest(read_json(directory / "generation_freeze.json")) != frozen_digest:
                    raise ValueError("generation freeze changed before dispatch")
                if transport is None:
                    _verify_proxy(freeze, proxy_root, verify_commit=False)
                attempts[key] = journal.append(dict(
                    kind="attempt", request_id=key, request_sha256=digest(request),
                ))
                last_start = time.monotonic()
                result, added = _request(client, root, run_id, request, config,
                                         config["max_runtime_bytes"] - runtime_bytes)
                runtime_bytes += added
                terminal[key] = journal.append(dict(identity, **result, kind="terminal",
                                                     attempted=True))
                status_counts[result["status"]] += 1
                dispatched += 1
                if result["status"] in STOP_STATUSES:
                    stopped = result["status"]
                elif result.get("outcome_uncertain"):
                    stopped = "outcome_uncertain"
                print(f"OAuth prompt study {len(terminal)}/{len(requests)} "
                      f"{dict(status_counts)}", flush=True)
        return _finish(directory, freeze, requests, terminal, stopped)
