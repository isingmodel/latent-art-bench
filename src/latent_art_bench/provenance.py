from __future__ import annotations

import subprocess
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional

from latent_art_bench.io import hash_file, stable_hash, utc_now, write_json
from latent_art_bench.schemas import RunRecord


def git_revision(root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def git_dirty(root: Path) -> Optional[bool]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=str(root),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(result.stdout.strip())


def implementation_hash(root: Path) -> Optional[str]:
    source_root = root / "src/latent_art_bench"
    if not source_root.is_dir():
        return None
    paths = sorted(source_root.rglob("*.py"))
    paths.extend(path for path in (root / "pyproject.toml", root / "uv.lock") if path.is_file())
    hashes = {str(path.relative_to(root)): hash_file(path) for path in paths}
    return stable_hash(hashes)


def _path_hashes(paths: Iterable[Path]) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for path in paths:
        hashes[str(path)] = hash_file(path) if path.is_file() else "MISSING"
    return hashes


@contextmanager
def recorded_run(
    root: Path,
    run_dir: Path,
    command: str,
    arguments: Dict[str, Any],
    config_path: Optional[Path] = None,
    resolved_config: Optional[Dict[str, Any]] = None,
    input_paths: Iterable[Path] = (),
    random_seeds: Optional[Dict[str, int]] = None,
) -> Iterator[RunRecord]:
    now = utc_now()
    run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:12]}"
    lock_path = root / "uv.lock"
    record = RunRecord(
        run_id=run_id,
        command=command,
        arguments=arguments,
        status="running",
        started_at=now,
        git_revision=git_revision(root),
        git_dirty=git_dirty(root),
        implementation_sha256=implementation_hash(root),
        dependency_lock_path=str(lock_path) if lock_path.is_file() else None,
        dependency_lock_sha256=hash_file(lock_path) if lock_path.is_file() else None,
        config_path=str(config_path) if config_path else None,
        config_sha256=hash_file(config_path) if config_path and config_path.is_file() else None,
        resolved_config=resolved_config,
        resolved_config_sha256=stable_hash(resolved_config) if resolved_config else None,
        input_hashes=_path_hashes(input_paths),
        random_seeds=random_seeds or {},
    )
    record_path = run_dir / f"{run_id}.json"
    write_json(record_path, record)
    try:
        yield record
    except BaseException as exc:
        record.status = "failed"
        record.completed_at = utc_now()
        record.failure_reasons.append(f"{type(exc).__name__}: {exc}")
        write_json(record_path, record)
        raise
    else:
        record.status = "complete"
        record.completed_at = utc_now()
        write_json(record_path, record)
