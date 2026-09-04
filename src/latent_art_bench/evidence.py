"""Commit-bound verification of the Painter Feature Generation v1 evidence chain.

A census freeze binds its inputs by repository path and SHA-256. Verifying those hashes
against the *working tree* fails as soon as any bound file evolves, even when the evidence
itself is intact: the fixed-seed R1 freeze already drifted this way after the R2 parser
repair, and every later dependency change to ``pyproject.toml`` or ``uv.lock`` would do the
same to every freeze at once.

This module resolves each freeze to the git commit that recorded it and verifies the bound
hashes against the file bytes at *that* commit. Hashes are never refreshed; the freeze file is
never modified. A bound path that git does not track (the ignored research workspace) is
verified against the working tree, because that is the only place those bytes exist.

Three evidence classes are checked:

- freezes: every ``frozen_inputs`` entry at the recording commit (or, failing that, at any
  commit in the path's history), plus the aggregate ``frozen_input_set_sha256``; inputs whose
  bytes were never committed can only be acknowledged, never re-verified;
- event ledgers: every event's self hash and its link to the previous event; and
- execution receipts: the event-ledger hash, the candidate-manifest hash, and every
  content-addressed raw response listed in the receipt inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence

from latent_art_bench.io import canonical_json, hash_file

MANIFEST_DIR = Path("data/manifests/painter_feature_generation_v1")
WORKSPACE_DIR = Path("research_workspace/painter_feature_generation_v1")
RECORDED_COMMIT_FIELD = "recorded_git_commit"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GENESIS_PREVIOUS = "0" * 64


class EvidenceError(RuntimeError):
    """Raised when evidence cannot be located or resolved at all."""


@dataclass
class Check:
    """One verifiable statement and its outcome."""

    subject: str
    ok: bool
    detail: str = ""


@dataclass
class Report:
    kind: str
    path: str
    checks: List[Check] = field(default_factory=list)
    recording_commit: Optional[str] = None
    recording_commit_source: Optional[str] = None
    working_tree_drift: List[str] = field(default_factory=list)
    acknowledged_unrecoverable: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def add(self, subject: str, ok: bool, detail: str = "") -> None:
        self.checks.append(Check(subject=subject, ok=ok, detail=detail))

    def as_dict(self) -> dict:
        data = asdict(self)
        data["ok"] = self.ok
        data["failed_checks"] = [asdict(check) for check in self.checks if not check.ok]
        return data


# --------------------------------------------------------------------------- git helpers


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=check,
    )


def is_git_repository(root: Path) -> bool:
    try:
        result = _git(root, "rev-parse", "--is-inside-work-tree", check=False)
    except FileNotFoundError:
        return False
    return result.returncode == 0 and result.stdout.strip() == b"true"


def head_commit(root: Path) -> str:
    return _git(root, "rev-parse", "HEAD").stdout.decode().strip()


def tracked_paths_dirty(root: Path, paths: Sequence[str]) -> List[str]:
    """Return the subset of ``paths`` whose working-tree bytes differ from HEAD."""
    if not paths:
        return []
    result = _git(root, "status", "--porcelain", "--untracked-files=all", "--", *paths, check=False)
    dirty: List[str] = []
    for line in result.stdout.decode().splitlines():
        if len(line) > 3:
            dirty.append(line[3:].strip())
    return sorted(dirty)


def bytes_at_commit(root: Path, commit: str, path: str) -> Optional[bytes]:
    """Bytes of ``path`` at ``commit``, or ``None`` when the commit does not track it."""
    result = _git(root, "show", f"{commit}:{path}", check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _blob_id(root: Path, path: Path) -> str:
    return _git(root, "hash-object", "--", str(path)).stdout.decode().strip()


def blob_introduction_commit(root: Path, path: str) -> Optional[str]:
    """Earliest commit whose tree holds ``path`` with exactly its current bytes."""
    absolute = root / path
    if not absolute.is_file():
        return None
    blob = _blob_id(root, absolute)
    listing = _git(
        root,
        "log",
        "--all",
        "--date-order",
        "--reverse",
        "--format=%H",
        f"--find-object={blob}",
        "--",
        path,
        check=False,
    )
    for commit in listing.stdout.decode().split():
        if bytes_at_commit(root, commit, path) == absolute.read_bytes():
            return commit
    return None


def freeze_recording_commit(root: Path, freeze_path: str, freeze: Mapping[str, Any]) -> tuple:
    """Resolve the commit a freeze speaks for, and say how it was resolved."""
    declared = freeze.get(RECORDED_COMMIT_FIELD)
    if isinstance(declared, str) and re.fullmatch(r"[0-9a-f]{7,40}", declared):
        resolved = _git(root, "rev-parse", "--verify", f"{declared}^{{commit}}", check=False)
        if resolved.returncode == 0:
            return resolved.stdout.decode().strip(), "declared_recorded_git_commit"
        return None, "declared_recorded_git_commit_unresolvable"
    commit = blob_introduction_commit(root, freeze_path)
    if commit is None:
        return None, "freeze_blob_not_found_in_history"
    return commit, "blob_introduction_commit"


# --------------------------------------------------------------------------- hashing


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


# --------------------------------------------------------------------------- freezes


def historical_commit_with_bytes(root: Path, path: str, sha256: str) -> Optional[str]:
    """Any commit in the path's history whose bytes hash to ``sha256`` (oldest first)."""
    listing = _git(root, "log", "--all", "--reverse", "--format=%H", "--", path, check=False)
    for commit in listing.stdout.decode().split():
        body = bytes_at_commit(root, commit, path)
        if body is not None and _sha256(body) == sha256:
            return commit
    return None


def verify_freeze(
    root: Path, freeze_path: Path, acknowledgements: Optional[Mapping[str, Any]] = None
) -> Report:
    relative = str(freeze_path.resolve().relative_to(root.resolve()))
    report = Report(kind="freeze", path=relative)
    acknowledged = {
        str(row.get("frozen_input_path"))
        for row in (acknowledgements or {}).get("unrecoverable_frozen_inputs", [])
        if isinstance(row, Mapping) and row.get("freeze_path") == relative
    }
    try:
        freeze = _read_json(freeze_path)
    except (OSError, ValueError) as exc:
        report.add("freeze_readable", False, str(exc))
        return report
    inputs = freeze.get("frozen_inputs")
    if not isinstance(inputs, list) or not inputs:
        report.add("frozen_inputs_present", False, "frozen_inputs missing or empty")
        return report
    aggregate = _sha256(canonical_json(inputs).encode("utf-8"))
    report.add(
        "frozen_input_set_sha256",
        aggregate == freeze.get("frozen_input_set_sha256"),
        "aggregate hash of frozen_inputs",
    )

    commit, source = freeze_recording_commit(root, relative, freeze)
    report.recording_commit = commit
    report.recording_commit_source = source
    report.add("recording_commit_resolved", commit is not None, source)

    for entry in inputs:
        path = entry.get("path") if isinstance(entry, Mapping) else None
        expected = entry.get("sha256") if isinstance(entry, Mapping) else None
        if (
            not isinstance(path, str)
            or not isinstance(expected, str)
            or not _SHA256_RE.fullmatch(expected)
        ):
            report.add("frozen_input_entry", False, f"malformed entry: {entry!r}")
            continue
        committed = bytes_at_commit(root, commit, path) if commit else None
        working = root / path
        working_hash = hash_file(working) if working.is_file() else None
        if committed is not None:
            observed = _sha256(committed)
            if working_hash != expected:
                report.working_tree_drift.append(path)
            if observed == expected:
                report.add(f"input@commit:{path}", True, "git show <recording commit>:<path>")
            elif path in acknowledged:
                report.acknowledged_unrecoverable.append(path)
                report.add(
                    f"input@commit:{path}",
                    True,
                    "acknowledged: bound bytes were never committed; see acknowledgements",
                )
            else:
                elsewhere = historical_commit_with_bytes(root, path, expected)
                if elsewhere is not None:
                    report.add(
                        f"input@history:{path}",
                        True,
                        f"bytes differ at the recording commit but match commit {elsewhere[:12]}",
                    )
                else:
                    report.add(
                        f"input@commit:{path}",
                        False,
                        "bound bytes match neither the recording commit nor any commit in history",
                    )
        elif working_hash == expected:
            # Not tracked at the recording commit (ignored research bytes, or an artifact that
            # prepare wrote and a later commit recorded): verified in place.
            report.add(f"input@worktree:{path}", True, "not tracked at the recording commit")
        else:
            elsewhere = historical_commit_with_bytes(root, path, expected)
            if elsewhere is not None:
                report.add(
                    f"input@history:{path}",
                    True,
                    f"not tracked at the recording commit; matches commit {elsewhere[:12]}",
                )
            else:
                report.add(
                    f"input:{path}",
                    False,
                    "not tracked at the recording commit, absent or drifted in the working "
                    "tree, and matching no commit in history",
                )

    for entry in freeze.get("preexecution_outputs", []) or []:
        path = entry.get("path") if isinstance(entry, Mapping) else None
        state = entry.get("state") if isinstance(entry, Mapping) else None
        if not isinstance(path, str) or state != "absent":
            report.add("preexecution_output_entry", False, f"malformed entry: {entry!r}")
    # Pre-execution absence was a condition at execution time. Every completed census committed
    # its freeze together with its ledger and receipt, so absence is not re-checkable from history.
    return report


# --------------------------------------------------------------------------- ledgers


def verify_event_ledger(root: Path, ledger_path: Path) -> Report:
    relative = str(ledger_path.resolve().relative_to(root.resolve()))
    report = Report(kind="event_ledger", path=relative)
    try:
        events = _read_jsonl(ledger_path)
    except (OSError, ValueError) as exc:
        report.add("ledger_readable", False, str(exc))
        return report
    if not events:
        report.add("ledger_nonempty", False, "no events")
        return report
    previous = _GENESIS_PREVIOUS
    for index, event in enumerate(events, start=1):
        body = dict(event)
        observed = body.pop("event_sha256", None)
        recomputed = _sha256(canonical_json(body).encode("utf-8"))
        report.add(f"event_{index}_self_hash", observed == recomputed)
        link = event.get("previous_event_sha256")
        if index == 1:
            # The first broad-Wikidata collector omitted the field on its genesis event.
            ok = link in (None, _GENESIS_PREVIOUS)
        else:
            ok = link == previous
        report.add(f"event_{index}_chain_link", ok)
        sequence = event.get("sequence")
        report.add(f"event_{index}_sequence", sequence == index)
        previous = str(observed)
    report.add("event_count", True, str(len(events)))
    return report


# --------------------------------------------------------------------------- receipts


def _find_response_body(root: Path, relative_body_path: str) -> Optional[Path]:
    """Locate a content-addressed response body anywhere under the metadata workspace."""
    candidates = sorted((root / WORKSPACE_DIR / "metadata").glob(f"*/{relative_body_path}"))
    return candidates[0] if candidates else None


def verify_receipt(root: Path, receipt_path: Path) -> Report:
    relative = str(receipt_path.resolve().relative_to(root.resolve()))
    report = Report(kind="execution_receipt", path=relative)
    try:
        receipt = _read_json(receipt_path)
    except (OSError, ValueError) as exc:
        report.add("receipt_readable", False, str(exc))
        return report
    for path_key, sha_key in (
        ("request_event_ledger_path", "request_event_ledger_sha256"),
        ("candidate_manifest_path", "candidate_manifest_sha256"),
        ("request_intents_path", "request_intents_sha256"),
        ("config_path", "config_sha256"),
    ):
        path = receipt.get(path_key)
        expected = receipt.get(sha_key)
        if path is None and expected is None:
            continue
        target = root / str(path)
        ok = target.is_file() and hash_file(target) == expected
        report.add(f"{path_key}:{path}", ok, "tracked file hash")
    inventory = receipt.get("raw_response_inventory")
    if inventory is None:
        inventory = receipt.get("response_inventory")
    if not isinstance(inventory, list):
        report.add("response_inventory_present", False, "no inventory list")
        return report
    for item in inventory:
        body_path = item.get("response_body_path") if isinstance(item, Mapping) else None
        expected = item.get("response_sha256") if isinstance(item, Mapping) else None
        if not isinstance(body_path, str) or not isinstance(expected, str):
            report.add("inventory_entry", False, f"malformed entry: {item!r}")
            continue
        located = _find_response_body(root, body_path)
        if located is None:
            report.add(f"cas:{body_path}", False, "raw response body missing from workspace")
            continue
        body = located.read_bytes()
        ok = _sha256(body) == expected
        declared_bytes = item.get("response_bytes")
        if isinstance(declared_bytes, int) and not isinstance(declared_bytes, bool):
            ok = ok and len(body) == declared_bytes
        report.add(f"cas:{body_path}", ok, "content-addressed body")
    report.add("inventory_count", True, str(len(inventory)))
    return report


# --------------------------------------------------------------------------- audit


def discover(root: Path) -> dict:
    manifests = root / MANIFEST_DIR
    freezes = sorted(manifests.glob("*freeze*.json"))
    ledgers = sorted(manifests.glob("*request_events*.jsonl"))
    receipts = sorted(manifests.glob("*execution_receipt*.json")) + sorted(
        manifests.glob("*/execution_receipt.json")
    )
    return {"freezes": freezes, "ledgers": ledgers, "receipts": sorted(set(receipts))}


ACKNOWLEDGEMENTS = MANIFEST_DIR / "evidence_acknowledgements.json"


def load_acknowledgements(root: Path, acknowledge: bool) -> Optional[dict]:
    path = root / ACKNOWLEDGEMENTS
    if not acknowledge or not path.is_file():
        return None
    value = _read_json(path)
    if not isinstance(value, dict):
        raise EvidenceError("evidence acknowledgements must be a JSON object")
    return value


def audit(root: Path, acknowledge: bool = True) -> dict:
    root = root.resolve()
    if not is_git_repository(root):
        raise EvidenceError("commit-bound verification requires a git checkout")
    found = discover(root)
    acknowledgements = load_acknowledgements(root, acknowledge)
    reports = (
        [verify_freeze(root, path, acknowledgements) for path in found["freezes"]]
        + [verify_event_ledger(root, path) for path in found["ledgers"]]
        + [verify_receipt(root, path) for path in found["receipts"]]
    )
    return {
        "schema_version": "painter-feature-generation-v1-evidence-audit/1.0",
        "head_commit": head_commit(root),
        "verification_rule": (
            "frozen inputs tracked by git are verified at the freeze's recording commit; "
            "untracked research bytes are verified in the working tree; hashes are never refreshed"
        ),
        "acknowledgements_path": str(ACKNOWLEDGEMENTS) if acknowledgements else None,
        "ok": all(report.ok for report in reports),
        "counts": {
            "freezes": len(found["freezes"]),
            "event_ledgers": len(found["ledgers"]),
            "execution_receipts": len(found["receipts"]),
            "checks": sum(len(report.checks) for report in reports),
            "failed_checks": sum(1 for report in reports for c in report.checks if not c.ok),
            "acknowledged_unrecoverable_inputs": sum(
                len(report.acknowledged_unrecoverable) for report in reports
            ),
        },
        "reports": [report.as_dict() for report in reports],
    }


def _summary_lines(result: Mapping[str, Any]) -> List[str]:
    lines = [
        f"HEAD {result['head_commit']}  overall={'OK' if result['ok'] else 'FAIL'}  "
        f"checks={result['counts']['checks']} failed={result['counts']['failed_checks']}"
    ]
    for report in result["reports"]:
        drift = report.get("working_tree_drift") or []
        commit = (report.get("recording_commit") or "-")[:12]
        status = "OK  " if report["ok"] else "FAIL"
        extra = f"  commit={commit}" if report["kind"] == "freeze" else ""
        if drift:
            extra += f"  working-tree drift (informational): {len(drift)} file(s)"
        acknowledged = report.get("acknowledged_unrecoverable") or []
        if acknowledged:
            extra += f"  acknowledged unrecoverable inputs: {len(acknowledged)}"
        lines.append(f"{status} {report['kind']:17s} {report['path']}{extra}")
        for check in report["failed_checks"]:
            lines.append(f"       x {check['subject']} {check['detail']}")
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", type=Path, help="write the full audit report to this path")
    parser.add_argument(
        "--no-acknowledgements",
        action="store_true",
        help="ignore the tracked acknowledgement file and report every mismatch as a failure",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = audit(args.root, acknowledge=not args.no_acknowledgements)
    except EvidenceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\n".join(_summary_lines(result)))
    return 0 if result["ok"] else 1
