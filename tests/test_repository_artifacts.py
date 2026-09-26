"""Storage safeguards preserve frozen bytes and inspect the actual Git index."""

import gzip
import hashlib
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


restore = load_script("restore_analysis")
sizes = load_script("check_git_sizes")


@pytest.fixture
def archived_result(tmp_path, monkeypatch):
    payload = b'{\n  "result": [1, 2, 3]\n}\n'
    monkeypatch.setattr(restore, "SHA256", hashlib.sha256(payload).hexdigest())
    target = tmp_path / restore.RESULT
    target.parent.mkdir(parents=True)
    target.with_suffix(".json.gz").write_bytes(gzip.compress(payload))
    return tmp_path, target, payload


def test_restore_exact_bytes_and_existing_result_is_not_rewritten(archived_result):
    root, target, payload = archived_result
    assert restore.restore(root).read_bytes() == payload
    before = target.stat()
    restore.restore(root)
    assert target.stat().st_mtime_ns == before.st_mtime_ns
    assert not list(target.parent.glob(".analysis-*"))


def test_restore_preserves_differing_local_work(archived_result):
    root, target, _ = archived_result
    target.write_bytes(b"local work")
    with pytest.raises(ValueError, match="different checksum"):
        restore.restore(root)
    assert target.read_bytes() == b"local work"


@pytest.mark.parametrize("archive", [gzip.compress(b"wrong result"), b"not gzip"])
def test_bad_archive_does_not_publish_partial_result(archived_result, archive):
    root, target, _ = archived_result
    target.with_suffix(".json.gz").write_bytes(archive)
    with pytest.raises((OSError, ValueError)):
        restore.restore(root)
    assert not target.exists()
    assert not list(target.parent.glob(".analysis-*"))


def test_restore_refuses_symlink(archived_result):
    root, target, payload = archived_result
    other = root / "other.json"
    other.write_bytes(payload)
    target.symlink_to(other)
    with pytest.raises(ValueError, match="symlink"):
        restore.restore(root)
    assert other.read_bytes() == payload


@pytest.fixture
def git_repo(tmp_path, monkeypatch):
    # Git sets these when invoking hooks; do not inherit a parent index in tests.
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_size_check_uses_staged_bytes_and_handles_unusual_names(git_repo):
    name = "result with\ttab and\nnewline.json"
    path = git_repo / name
    path.write_bytes(b"x" * 11)
    subprocess.run(["git", "add", "--", name], check=True)
    path.write_bytes(b"small")
    assert sizes.oversized_staged_blobs(limit=10) == [(name, 11)]
    subprocess.run(["git", "add", "--", name], check=True)
    path.write_bytes(b"x" * 11)
    assert sizes.oversized_staged_blobs(limit=10) == []


def test_size_check_accepts_boundary_and_ignores_untracked_or_removed_files(git_repo):
    assert sizes.oversized_staged_blobs(limit=10) == []
    path = git_repo / "result"
    path.write_bytes(b"x" * 11)
    assert sizes.oversized_staged_blobs(limit=10) == []
    path.write_bytes(b"x" * 10)
    subprocess.run(["git", "add", "result"], check=True)
    assert sizes.oversized_staged_blobs(limit=10) == []
    subprocess.run(["git", "rm", "--cached", "result"], check=True, capture_output=True)
    assert sizes.oversized_staged_blobs(limit=10) == []
