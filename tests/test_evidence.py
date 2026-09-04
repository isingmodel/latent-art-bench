from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from latent_art_bench import evidence
from latent_art_bench.io import canonical_json

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=True, text=True
    ).stdout.strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _freeze(entries: list[dict], **extra: object) -> dict:
    return {
        "schema_version": "test-freeze/1.0",
        "frozen_inputs": entries,
        "frozen_input_set_sha256": hashlib.sha256(canonical_json(entries).encode()).hexdigest(),
        "preexecution_outputs": [{"path": "data/out.jsonl", "state": "absent"}],
        **extra,
    }


def _write_freeze(root: Path, name: str, freeze: dict) -> Path:
    path = root / evidence.MANIFEST_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    return path


def _repo_with_bound_file(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    _init_repo(root)
    bound = root / "src" / "bound.py"
    bound.parent.mkdir(parents=True)
    bound.write_text("VERSION = 1\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "bound v1")
    return root, bound


def test_commit_bound_verification_survives_later_edits(tmp_path: Path) -> None:
    root, bound = _repo_with_bound_file(tmp_path)
    entries = [{"path": "src/bound.py", "sha256": _sha256(bound)}]
    freeze_path = _write_freeze(root, "x_freeze.json", _freeze(entries))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "record freeze")

    bound.write_text("VERSION = 2\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "bound v2")

    report = evidence.verify_freeze(root, freeze_path)
    assert report.ok, report.as_dict()
    assert report.recording_commit_source == "blob_introduction_commit"
    assert report.working_tree_drift == ["src/bound.py"]


def test_declared_recorded_commit_takes_precedence(tmp_path: Path) -> None:
    root, bound = _repo_with_bound_file(tmp_path)
    entries = [{"path": "src/bound.py", "sha256": _sha256(bound)}]
    head = _git(root, "rev-parse", "HEAD")
    freeze_path = _write_freeze(
        root, "y_freeze.json", _freeze(entries, **{evidence.RECORDED_COMMIT_FIELD: head})
    )
    bound.write_text("VERSION = 2\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "freeze plus edit together")

    report = evidence.verify_freeze(root, freeze_path)
    assert report.ok
    assert report.recording_commit == head
    assert report.recording_commit_source == "declared_recorded_git_commit"


def test_bytes_never_committed_fail_unless_acknowledged(tmp_path: Path) -> None:
    root, bound = _repo_with_bound_file(tmp_path)
    bound.write_text("VERSION = 1.5  # never committed\n")
    entries = [{"path": "src/bound.py", "sha256": _sha256(bound)}]
    bound.write_text("VERSION = 2\n")
    freeze_path = _write_freeze(root, "z_freeze.json", _freeze(entries))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "freeze with unrecoverable input")

    report = evidence.verify_freeze(root, freeze_path)
    assert not report.ok
    failed = [check.subject for check in report.checks if not check.ok]
    assert failed == ["input:src/bound.py"]

    acknowledgements = {
        "unrecoverable_frozen_inputs": [
            {
                "freeze_path": str(evidence.MANIFEST_DIR / "z_freeze.json"),
                "frozen_input_path": "src/bound.py",
                "bound_sha256": entries[0]["sha256"],
            }
        ]
    }
    acknowledged = evidence.verify_freeze(root, freeze_path, acknowledgements)
    assert acknowledged.ok
    assert acknowledged.acknowledged_unrecoverable == ["src/bound.py"]


def test_tampered_frozen_input_hash_fails(tmp_path: Path) -> None:
    root, bound = _repo_with_bound_file(tmp_path)
    entries = [{"path": "src/bound.py", "sha256": "0" * 64}]
    freeze_path = _write_freeze(root, "t_freeze.json", _freeze(entries))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "bad freeze")
    report = evidence.verify_freeze(root, freeze_path)
    assert not report.ok


def _chain(rows: list[dict]) -> list[dict]:
    events = []
    previous = "0" * 64
    for sequence, fields in enumerate(rows, start=1):
        row = {"sequence": sequence, "previous_event_sha256": previous, **fields}
        row["event_sha256"] = hashlib.sha256(canonical_json(row).encode()).hexdigest()
        events.append(row)
        previous = row["event_sha256"]
    return events


def test_event_ledger_chain_verification(tmp_path: Path) -> None:
    ledger = tmp_path / "events.jsonl"
    events = _chain([{"event_type": "a"}, {"event_type": "b"}, {"event_type": "c"}])
    ledger.write_text("".join(canonical_json(row) + "\n" for row in events))
    assert evidence.verify_event_ledger(tmp_path, ledger).ok

    tampered = [dict(row) for row in events]
    tampered[1]["event_type"] = "B"
    ledger.write_text("".join(canonical_json(row) + "\n" for row in tampered))
    report = evidence.verify_event_ledger(tmp_path, ledger)
    assert not report.ok
    assert "event_2_self_hash" in {c.subject for c in report.checks if not c.ok}


@pytest.mark.skipif(
    not (REPOSITORY_ROOT / ".git").exists(), reason="repository history is required"
)
def test_repository_evidence_chain_verifies_with_documented_acknowledgements() -> None:
    result = evidence.audit(REPOSITORY_ROOT)
    assert result["ok"], [r["failed_checks"] for r in result["reports"] if not r["ok"]]
    assert result["counts"]["freezes"] >= 9
    assert result["counts"]["event_ledgers"] >= 8
    assert result["counts"]["execution_receipts"] >= 4
    assert result["counts"]["acknowledged_unrecoverable_inputs"] == 2

    strict = evidence.audit(REPOSITORY_ROOT, acknowledge=False)
    failed = {check["subject"] for report in strict["reports"] for check in report["failed_checks"]}
    assert failed == {
        "input:src/latent_art_bench/painter_feature_generation_v1/federated_census.py",
        "input:tests/painter_feature_generation_v1/test_federated_census.py",
    }
