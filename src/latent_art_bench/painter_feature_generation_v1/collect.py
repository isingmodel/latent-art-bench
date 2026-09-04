"""Protocol 2.2 R0 collection: fetch what a source returns, keep all of it, judge none of it.

One module serves every JSON source route. There is no per-route parser and no intent-generation
step, because the config lists every request literally: its URL and, where a query is long enough
that an encoded URL would be unreadable, its query parameters spelled out. The exact URL that went
out is recorded in the receipt. Running a census means replaying that committed list.

The four principles of Protocol 2.2 §1 are implemented as follows:

- **Write it down first.** The config names each request's exact URL and method. It is committed
  before the census runs, and its SHA-256 goes in the receipt.
- **Keep everything.** Each response body is stored verbatim under its SHA-256, and each record the
  provider returned enters the manifest with every field the provider sent.
- **Do not judge.** No eligibility flag, candidate flag, screening verdict, score, or disposition is
  computed here. Counts are counts of returned records.
- **The list is closed.** Enforced by the protocol, not by this code: a config may only name a route
  from the Protocol 2.1 §5.2 registry.

A failed request is recorded and the census continues; the receipt states whether it completed.
The only fields that can fail a request are the ones needed to find the records in the response.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import httpx

from latent_art_bench.io import hash_bytes, hash_file, write_json, write_jsonl

PROTOCOL_ID = "painter-feature-generation-v1/2.2"
MANIFEST_SCHEMA = "painter-feature-generation-v1-collection-record/2.2"
RECEIPT_SCHEMA = "painter-feature-generation-v1-collection-receipt/2.2"
DEFAULT_TIMEOUT = 60.0
DEFAULT_INTERVAL = 2.0
DEFAULT_MAX_BYTES = 25 * 1024 * 1024


class CollectionError(RuntimeError):
    """Raised when a config is unusable or an output path is already occupied."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CollectionError(f"{label} must be a repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise CollectionError(f"{label} escapes the repository")
    path = (root / declared).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise CollectionError(f"{label} escapes the repository") from exc
    return path


def load_config(root: Path, config_path: Path) -> Dict[str, Any]:
    """Read and minimally validate a collection config."""
    try:
        config = json.loads(config_path.read_bytes())
    except (OSError, ValueError) as exc:
        raise CollectionError(f"config cannot be read as JSON: {exc}") from exc
    if not isinstance(config, dict):
        raise CollectionError("config is not an object")
    if config.get("protocol_id") != PROTOCOL_ID:
        raise CollectionError(f"config protocol_id must be {PROTOCOL_ID}")
    for key in ("census_id", "source_id"):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise CollectionError(f"config lacks {key}")
    requests = config.get("requests")
    if not isinstance(requests, list) or not requests:
        raise CollectionError("config lists no requests")
    seen: set = set()
    for row in requests:
        if not isinstance(row, Mapping):
            raise CollectionError("request entry is not an object")
        request_id = row.get("request_id")
        url = row.get("url")
        if not isinstance(request_id, str) or request_id in seen:
            raise CollectionError(f"request_id is missing or duplicated: {request_id!r}")
        seen.add(request_id)
        if not isinstance(url, str) or not url.startswith("https://"):
            raise CollectionError(f"{request_id} needs an https URL")
        if row.get("params") is not None and not isinstance(row["params"], Mapping):
            raise CollectionError(f"{request_id} params must be an object")
        if row.get("method", "GET") not in ("GET", "POST"):
            raise CollectionError(f"{request_id} method must be GET or POST")
    paths = config.get("paths")
    if not isinstance(paths, Mapping) or set(paths) != {"manifest", "receipt", "workspace"}:
        raise CollectionError("paths must name exactly manifest, receipt, and workspace")
    for key, value in paths.items():
        _repo_path(root, value, f"paths.{key}")
    cutoff = config.get("execution_start_not_after_utc")
    if cutoff is not None:
        if not isinstance(cutoff, str) or not cutoff.endswith("Z"):
            raise CollectionError("execution_start_not_after_utc must be UTC")
        if datetime.now(timezone.utc) >= datetime.fromisoformat(cutoff.replace("Z", "+00:00")):
            raise CollectionError("execution-start cutoff has passed; write a new census ID")
    return config


def records_from(payload: Any, records_at: Optional[str]) -> List[Any]:
    """Locate the provider's record list.

    ``records_at`` is a dotted path, for example ``data`` or ``results.bindings``. When it is
    absent the whole payload is one record. This is the only structural assumption the collector
    makes about a response, and the only thing a request can legitimately fail on.
    """
    if records_at is None:
        return [payload]
    node = payload
    for segment in records_at.split("."):
        if not isinstance(node, Mapping) or segment not in node:
            raise CollectionError(f"response has no {records_at!r}")
        node = node[segment]
    if not isinstance(node, list):
        raise CollectionError(f"{records_at!r} is not a list")
    return node


def _store_body(workspace: Path, body: bytes) -> tuple:
    digest = hash_bytes(body)
    relative = Path("responses") / digest[:2] / f"{digest}.response"
    target = workspace / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return digest, str(relative)


def _headers(response: httpx.Response) -> Dict[str, str]:
    keys = ("date", "content-type", "content-length", "retry-after", "server")
    return {key: response.headers[key] for key in keys if key in response.headers}


def run(
    root: Path,
    config_path: Path,
    authorized_by: str,
    transport: Optional[httpx.BaseTransport] = None,
) -> Dict[str, Any]:
    """Execute a census: fetch every request, keep every record, judge nothing."""
    root = root.resolve()
    config = load_config(root, config_path)
    paths = config["paths"]
    manifest_path = _repo_path(root, paths["manifest"], "paths.manifest")
    receipt_path = _repo_path(root, paths["receipt"], "paths.receipt")
    workspace = _repo_path(root, paths["workspace"], "paths.workspace")
    for label, path in (("manifest", manifest_path), ("receipt", receipt_path)):
        if path.exists():
            raise CollectionError(f"{label} already exists; a re-run needs a new census ID")

    records_at = config.get("records_at")
    interval = float(config.get("minimum_interval_seconds", DEFAULT_INTERVAL))
    timeout = float(config.get("timeout_seconds", DEFAULT_TIMEOUT))
    max_bytes = int(config.get("maximum_response_bytes", DEFAULT_MAX_BYTES))
    user_agent = str(
        config.get("user_agent")
        or "latent-art-bench/0.1 painter-feature-generation-v1 metadata collection"
        " (+https://github.com/isingmodel/latent-art-bench)"
    )

    started = _utc_now()
    rows: List[Dict[str, Any]] = []
    receipts: List[Dict[str, Any]] = []
    last_access = 0.0

    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        transport=transport,
        headers={"Accept": str(config.get("accept", "application/json")), "User-Agent": user_agent},
    ) as client:
        for request in config["requests"]:
            delay = interval - (time.monotonic() - last_access)
            if delay > 0:
                time.sleep(delay)
            entry: Dict[str, Any] = {
                "request_id": request["request_id"],
                "painter_id": request.get("painter_id"),
                "method": request.get("method", "GET"),
                "url": request["url"],
                "requested_at_utc": _utc_now(),
            }
            try:
                response = client.request(
                    entry["method"],
                    request["url"],
                    params=request.get("params"),
                    json=request.get("body"),
                )
                body = response.read()[: max_bytes + 1]
                last_access = time.monotonic()
                digest, relative = _store_body(workspace, body[:max_bytes])
                entry.update(
                    {
                        "status_code": response.status_code,
                        "final_url": str(response.url),
                        "response_headers": _headers(response),
                        "response_bytes": len(body[:max_bytes]),
                        "response_truncated": len(body) > max_bytes,
                        "response_sha256": digest,
                        "response_body_path": relative,
                    }
                )
                if response.status_code != 200:
                    raise CollectionError(f"HTTP {response.status_code}")
                if entry["response_truncated"]:
                    raise CollectionError(f"response exceeded {max_bytes} bytes")
                found = records_from(json.loads(body), records_at)
                for index, record in enumerate(found):
                    rows.append(
                        {
                            "schema_version": MANIFEST_SCHEMA,
                            "census_id": config["census_id"],
                            "source_id": config["source_id"],
                            "painter_id": request.get("painter_id"),
                            "request_id": request["request_id"],
                            "response_sha256": digest,
                            "record_index": index,
                            "record": record,
                        }
                    )
                entry.update({"outcome": "success", "records": len(found), "error": None})
            except Exception as exc:  # noqa: BLE001 - every failure is recorded, never fatal
                entry.setdefault("status_code", None)
                entry.update(
                    {
                        "outcome": "failed",
                        "records": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            receipts.append(entry)

    by_painter: Dict[str, int] = {}
    for row in rows:
        key = str(row["painter_id"])
        by_painter[key] = by_painter.get(key, 0) + 1
    succeeded = sum(1 for entry in receipts if entry["outcome"] == "success")

    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "census_id": config["census_id"],
        "source_id": config["source_id"],
        "config_path": str(config_path.resolve().relative_to(root)),
        "config_sha256": hash_file(config_path),
        "started_at_utc": started,
        "finished_at_utc": _utc_now(),
        "complete": succeeded == len(receipts),
        "authorized_by": authorized_by,
        "requests": receipts,
        "counts": {
            "requests_planned": len(receipts),
            "requests_succeeded": succeeded,
            "returned_records": len(rows),
            "returned_records_by_painter": dict(sorted(by_painter.items())),
        },
        "manifest_path": str(paths["manifest"]),
        "note": (
            "Counts are returned provider records, not works and not candidates. This census "
            "assigned no eligibility, no screening verdict, and no score. Attribution, medium and "
            "support, rights, geometry, and outdoor-place eligibility are decided at R1 and R2 "
            "from the retained raw fields. No image was requested and no work was admitted."
        ),
    }
    write_jsonl(manifest_path, rows)
    receipt["manifest_sha256"] = hash_file(manifest_path)
    write_json(receipt_path, receipt)
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--authorized-by",
        required=True,
        help="who authorized this census, recorded verbatim in the receipt",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        receipt = run(root, _repo_path(root, str(args.config), "config"), args.authorized_by)
    except CollectionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: receipt[k] for k in ("census_id", "complete", "counts")}, indent=2))
    return 0 if receipt["complete"] else 1
