"""Small immutable artifacts and append-only event records for the paper pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from latent_art_bench.io import canonical_json, hash_file, read_json, utc_now

NAMESPACE = "painter_feature_generation_v2"
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
PROTOCOL = Path("studies") / NAMESPACE / "PROTOCOL.md"


@contextmanager
def stage_lock(path: Path):
    """One writer per stage; a process crash releases the OS lock without deleting evidence."""
    import fcntl

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another process is executing this stage") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def identifier(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,99}", value):
        raise ValueError("identifier must be a short, portable path component")
    return value


def confined(root: Path, relative: str | Path, boundary: Path) -> Path:
    path = (root / relative).resolve()
    path.relative_to((root / boundary).resolve())
    return path


def publish(path: Path, value: Any, *, lines: bool = False) -> None:
    """Create once. Existing artifacts, even identical ones, are never overwritten."""
    rendered = (
        "".join(canonical_json(row) + "\n" for row in value)
        if lines else json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())


def bindings(root: Path, paths: Iterable[Path]) -> list[dict]:
    return [{"path": str(p), "sha256": hash_file(root / p)} for p in sorted(set(paths))]


def verify_bindings(root: Path, records: Iterable[dict]) -> None:
    for record in records:
        path = (root / record["path"]).resolve()
        path.relative_to(root.resolve())
        if hash_file(path) != record["sha256"]:
            raise ValueError(f"bound input changed: {record['path']}")


def load_bound(root: Path, path: Path) -> dict:
    value = read_json(root / path)
    verify_bindings(root, value["inputs"])
    return value


def events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    result, previous = [], None
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line:
            continue
        row = json.loads(line)
        expected = row.pop("event_sha256")
        if row["previous_sha256"] != previous or digest(row) != expected:
            raise ValueError(f"broken event chain: {path}")
        row["event_sha256"] = expected
        result.append(row)
        previous = expected
    return result


def append_event(path: Path, payload: dict) -> dict:
    rows = events(path)
    row = dict(payload, sequence=len(rows), at_utc=utc_now().isoformat(),
               previous_sha256=rows[-1]["event_sha256"] if rows else None)
    row["event_sha256"] = digest(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return row
