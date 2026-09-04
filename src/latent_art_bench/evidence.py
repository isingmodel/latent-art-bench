"""Commit-bound verification of the Painter Feature Generation v1 evidence chain.

A census freeze binds its inputs by repository path and SHA-256. Verifying those hashes
against the *working tree* fails as soon as any bound file evolves, even when the evidence
itself is intact: the fixed-seed R1 freeze already drifted this way after the R2 parser
repair, and every later dependency change to ``pyproject.toml`` or ``uv.lock`` would do the
same to every freeze at once.

This module resolves each freeze to the git commit that recorded it and verifies the bound
hashes against the file bytes at *that* commit, falling back to any commit in the path's
history. Hashes are never refreshed; the freeze file is never modified. A bound path that git
does not track (the ignored research workspace) is verified against the working tree, because
that is the only place those bytes exist. Inputs whose bytes were never committed can only be
acknowledged, by path and by the exact bound hash, never re-verified.

Three evidence classes are checked:

- freezes: every ``frozen_inputs`` entry and the aggregate ``frozen_input_set_sha256``;
- event ledgers: every event's self hash, its link to the previous event, its sequence, and a
  single census identity across the ledger; and
- execution receipts: the tracked files they name (with the same history fallback), the
  genesis/terminal event hashes and counts they claim against the ledger, and every
  content-addressed raw response in the receipt inventory.

All git reads go through one ``git cat-file --batch`` process per verification step.
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
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from latent_art_bench.io import hash_bytes, hash_file, read_json, stable_hash

MANIFEST_DIR = Path("data/manifests/painter_feature_generation_v1")
WORKSPACE_DIR = Path("research_workspace/painter_feature_generation_v1")
ACKNOWLEDGEMENTS = MANIFEST_DIR / "evidence_acknowledgements.json"
RECORDED_COMMIT_FIELD = "recorded_git_commit"
GENESIS_PREVIOUS = "0" * 64
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


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
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=check)


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


def bytes_at_commits(root: Path, specs: Sequence[str]) -> Dict[str, Optional[bytes]]:
    """Resolve ``<commit>:<path>`` specs in one ``git cat-file --batch`` call.

    A spec that names nothing, or names a tree rather than a blob, maps to ``None``.
    """
    unique = list(dict.fromkeys(specs))
    if not unique:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=("\n".join(unique) + "\n").encode("utf-8"),
        capture_output=True,
    )
    out = proc.stdout
    result: Dict[str, Optional[bytes]] = {}
    position = 0
    for spec in unique:
        newline = out.find(b"\n", position)
        if newline < 0:
            result[spec] = None
            continue
        header = out[position:newline].decode("utf-8", "replace")
        position = newline + 1
        parts = header.split()
        if header.endswith(" missing") or len(parts) != 3 or not parts[2].isdigit():
            result[spec] = None
            continue
        size = int(parts[2])
        result[spec] = out[position : position + size] if parts[1] == "blob" else None
        position += size + 1
    return result


def bytes_at_commit(root: Path, commit: str, path: str) -> Optional[bytes]:
    """Bytes of ``path`` at ``commit``, or ``None`` when the commit does not track it."""
    spec = f"{commit}:{path}"
    return bytes_at_commits(root, [spec]).get(spec)


def git_blob_id(data: bytes) -> str:
    """The SHA-1 object name git assigns to ``data`` stored as a blob."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def blob_introduction_commit(root: Path, path: str) -> Optional[str]:
    """Earliest commit whose tree holds ``path`` with exactly its current bytes."""
    absolute = root / path
    if not absolute.is_file():
        return None
    data = absolute.read_bytes()
    listing = _git(
        root,
        "log",
        "--all",
        "--date-order",
        "--reverse",
        "--format=%H",
        f"--find-object={git_blob_id(data)}",
        "--",
        path,
        check=False,
    )
    commits = listing.stdout.decode().split()
    found = bytes_at_commits(root, [f"{commit}:{path}" for commit in commits])
    for commit in commits:
        if found.get(f"{commit}:{path}") == data:
            return commit
    return None


def historical_commit_with_bytes(root: Path, path: str, sha256: str) -> Optional[str]:
    """Any commit in the path's history whose bytes hash to ``sha256`` (oldest first)."""
    listing = _git(root, "log", "--all", "--reverse", "--format=%H", "--", path, check=False)
    commits = listing.stdout.decode().split()
    found = bytes_at_commits(root, [f"{commit}:{path}" for commit in commits])
    for commit in commits:
        body = found.get(f"{commit}:{path}")
        if body is not None and hash_bytes(body) == sha256:
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


# --------------------------------------------------------------------------- hash chains


def event_self_hash(event: Mapping[str, Any]) -> Tuple[Optional[str], str]:
    """Return the event's stored hash and the hash recomputed over everything else."""
    body = dict(event)
    observed = body.pop("event_sha256", None)
    return (observed if isinstance(observed, str) else None), stable_hash(body)


def chain_error(events: Sequence[Mapping[str, Any]], allow_null_genesis: bool) -> Optional[str]:
    """First hash-chain defect in ``events``, or ``None`` when the chain is intact."""
    previous = GENESIS_PREVIOUS
    for index, event in enumerate(events, start=1):
        observed, recomputed = event_self_hash(event)
        if observed != recomputed:
            return f"event {index} self hash is invalid"
        link = event.get("previous_event_sha256")
        if index == 1 and allow_null_genesis and link is None:
            pass
        elif link != previous:
            return f"event {index} does not link to its predecessor"
        previous = str(observed)
    return None


def _read_ledger(path: Path) -> Tuple[List[Optional[dict]], List[int]]:
    """Parse a JSONL ledger line by line; blank lines are reported, never skipped."""
    raw = path.read_bytes().split(b"\n")
    if raw and raw[-1] == b"":
        raw.pop()
    rows: List[Optional[dict]] = []
    blank: List[int] = []
    for number, line in enumerate(raw, start=1):
        if not line.strip():
            blank.append(number)
            continue
        try:
            value = json.loads(line)
        except ValueError:
            value = None
        rows.append(value if isinstance(value, dict) else None)
    return rows, blank


# --------------------------------------------------------------------------- freezes


def _acknowledged_inputs(
    acknowledgements: Optional[Mapping[str, Any]], freeze_relative: str
) -> Dict[str, str]:
    """Map frozen-input path to the exact hash an acknowledgement excuses for this freeze."""
    result: Dict[str, str] = {}
    for row in (acknowledgements or {}).get("unrecoverable_frozen_inputs", []):
        if not isinstance(row, Mapping) or row.get("freeze_path") != freeze_relative:
            continue
        path = row.get("frozen_input_path")
        bound = row.get("bound_sha256")
        if isinstance(path, str) and isinstance(bound, str) and _SHA256_RE.fullmatch(bound):
            result[path] = bound
    return result


def _verify_bound_input(
    root: Path,
    report: Report,
    path: str,
    expected: str,
    committed: Optional[bytes],
    acknowledged: Mapping[str, str],
) -> None:
    working = root / path
    working_hash = hash_file(working) if working.is_file() else None
    if committed is not None:
        if working_hash != expected:
            report.working_tree_drift.append(path)
        if hash_bytes(committed) == expected:
            report.add(f"input@commit:{path}", True, "git show <recording commit>:<path>")
            return
        location = "bytes differ at the recording commit"
    elif working_hash == expected:
        # Not tracked at the recording commit: ignored research bytes, or an artifact that
        # prepare wrote and a later commit recorded. Verified in place.
        report.add(f"input@worktree:{path}", True, "not tracked at the recording commit")
        return
    else:
        location = "not tracked at the recording commit and absent or drifted in the working tree"
    elsewhere = historical_commit_with_bytes(root, path, expected)
    if elsewhere is not None:
        report.add(f"input@history:{path}", True, f"{location}; matches commit {elsewhere[:12]}")
        return
    if acknowledged.get(path) == expected:
        report.acknowledged_unrecoverable.append(path)
        report.add(
            f"input@acknowledged:{path}",
            True,
            f"{location}; matches no commit; acknowledged for exactly this hash",
        )
        return
    report.add(f"input:{path}", False, f"{location}; matches no commit in history")


def verify_freeze(
    root: Path, freeze_path: Path, acknowledgements: Optional[Mapping[str, Any]] = None
) -> Report:
    relative = str(freeze_path.resolve().relative_to(root.resolve()))
    report = Report(kind="freeze", path=relative)
    try:
        freeze = read_json(freeze_path)
    except (OSError, ValueError) as exc:
        report.add("freeze_readable", False, str(exc))
        return report
    inputs = freeze.get("frozen_inputs") if isinstance(freeze, dict) else None
    if not isinstance(inputs, list) or not inputs:
        report.add("frozen_inputs_present", False, "frozen_inputs missing or empty")
        return report
    report.add(
        "frozen_input_set_sha256",
        stable_hash(inputs) == freeze.get("frozen_input_set_sha256"),
        "aggregate hash of frozen_inputs",
    )
    commit, source = freeze_recording_commit(root, relative, freeze)
    report.recording_commit = commit
    report.recording_commit_source = source
    report.add("recording_commit_resolved", commit is not None, source)

    entries: List[Tuple[str, str]] = []
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
        entries.append((path, expected))
    committed = (
        bytes_at_commits(root, [f"{commit}:{path}" for path, _ in entries]) if commit else {}
    )
    acknowledged = _acknowledged_inputs(acknowledgements, relative)
    for path, expected in entries:
        _verify_bound_input(
            root, report, path, expected, committed.get(f"{commit}:{path}"), acknowledged
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
        rows, blank = _read_ledger(ledger_path)
    except OSError as exc:
        report.add("ledger_readable", False, str(exc))
        return report
    report.add("no_blank_lines", not blank, f"blank lines at {blank}" if blank else "")
    if not rows:
        report.add("ledger_nonempty", False, "no events")
        return report
    events: List[dict] = []
    for index, row in enumerate(rows, start=1):
        if row is None:
            report.add(f"event_{index}_is_json_object", False)
        else:
            events.append(row)
    if len(events) != len(rows):
        return report
    previous = GENESIS_PREVIOUS
    for index, event in enumerate(events, start=1):
        observed, recomputed = event_self_hash(event)
        report.add(f"event_{index}_self_hash", observed == recomputed)
        link = event.get("previous_event_sha256")
        if index == 1:
            # The first broad-Wikidata collector omitted the field on its genesis event.
            ok = link in (None, GENESIS_PREVIOUS)
        else:
            ok = link == previous
        report.add(f"event_{index}_chain_link", ok)
        report.add(f"event_{index}_sequence", event.get("sequence") == index)
        previous = str(observed)
    census_ids = {event.get("census_id") for event in events}
    schemas = {event.get("schema_version") for event in events}
    report.add("single_census_id", len(census_ids) == 1, ", ".join(map(str, census_ids)))
    report.add("single_event_schema", len(schemas) == 1, ", ".join(map(str, schemas)))
    report.add("event_count", True, str(len(events)))
    return report


# --------------------------------------------------------------------------- receipts


def workspace_index(root: Path) -> Dict[str, List[Path]]:
    """Index every file under the research workspace by name, in one walk.

    A route sets its own ``paths.workspace``, so a receipt's ``response_body_path`` is relative
    to a directory this module does not know. Indexing by file name and matching on the path
    suffix locates the body wherever the route put it, without a recursive glob per entry.
    """
    index: Dict[str, List[Path]] = {}
    for path in (root / WORKSPACE_DIR).rglob("*"):
        if path.is_file():
            index.setdefault(path.name, []).append(path)
    return index


def _find_response_body(
    root: Path, relative_body_path: str, index: Optional[Mapping[str, List[Path]]] = None
) -> Optional[Path]:
    """Locate a content-addressed response body anywhere under the research workspace."""
    if index is None:
        index = workspace_index(root)
    tail = Path(relative_body_path)
    candidates = sorted(path for path in index.get(tail.name, []) if str(path).endswith(str(tail)))
    return candidates[0] if candidates else None


def _tracked_hash_check(root: Path, report: Report, subject: str, path: str, expected: Any) -> None:
    target = root / path
    if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
        report.add(subject, False, "malformed sha256")
        return
    if target.is_file() and hash_file(target) == expected:
        report.add(subject, True, "working tree")
        return
    elsewhere = historical_commit_with_bytes(root, path, expected)
    if elsewhere is not None:
        report.add(subject, True, f"working tree drifted; matches commit {elsewhere[:12]}")
        return
    report.add(subject, False, "matches neither the working tree nor any commit in history")


def _ledger_cross_checks(root: Path, report: Report, receipt: Mapping[str, Any]) -> None:
    ledger_path = receipt.get("request_event_ledger_path")
    if not isinstance(ledger_path, str) or not (root / ledger_path).is_file():
        return
    rows, _ = _read_ledger(root / ledger_path)
    events = [row for row in rows if row is not None]
    if not events or len(events) != len(rows):
        report.add("ledger_parseable_for_cross_check", False)
        return
    census_ids = {event.get("census_id") for event in events}
    report.add("receipt_census_matches_ledger", census_ids == {receipt.get("census_id")})
    genesis = receipt.get("execution_genesis_event_sha256")
    if genesis is not None:
        report.add("genesis_event_sha256", genesis == events[0].get("event_sha256"))
    terminal = receipt.get("terminal_event_sha256", receipt.get("terminal_request_event_sha256"))
    if terminal is not None:
        report.add("terminal_event_sha256", terminal == events[-1].get("event_sha256"))
    count = receipt.get("request_event_count")
    if count is not None:
        report.add("request_event_count", count == len(events), f"ledger has {len(events)}")
    successful = receipt.get("successful_requests")
    outcomes = [event for event in events if event.get("outcome") is not None]
    if successful is not None and outcomes:
        success_ids = {
            event.get("request_id")
            for event in outcomes
            if str(event.get("outcome")).endswith("success") and event.get("request_id")
        }
        report.add(
            "successful_requests",
            successful == len(success_ids),
            f"ledger shows {len(success_ids)} request IDs with a success outcome",
        )


def verify_receipt(
    root: Path, receipt_path: Path, index: Optional[Mapping[str, List[Path]]] = None
) -> Report:
    relative = str(receipt_path.resolve().relative_to(root.resolve()))
    report = Report(kind="execution_receipt", path=relative)
    try:
        receipt = read_json(receipt_path)
    except (OSError, ValueError) as exc:
        report.add("receipt_readable", False, str(exc))
        return report
    if not isinstance(receipt, dict):
        report.add("receipt_is_object", False)
        return report
    for path_key, sha_key in (
        ("request_event_ledger_path", "request_event_ledger_sha256"),
        ("candidate_manifest_path", "candidate_manifest_sha256"),
        ("request_intents_path", "request_intents_sha256"),
        ("config_path", "config_sha256"),
        ("authorization_seal_path", "authorization_seal_sha256"),
    ):
        path = receipt.get(path_key)
        expected = receipt.get(sha_key)
        if path is None and expected is None:
            continue
        if not isinstance(path, str):
            report.add(f"{path_key}", False, "malformed path")
            continue
        _tracked_hash_check(root, report, f"{path_key}:{path}", path, expected)
    _ledger_cross_checks(root, report, receipt)
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
        located = _find_response_body(root, body_path, index)
        if located is None:
            report.add(f"cas:{body_path}", False, "raw response body missing from workspace")
            continue
        body = located.read_bytes()
        ok = hash_bytes(body) == expected
        declared_bytes = item.get("response_bytes")
        if isinstance(declared_bytes, int) and not isinstance(declared_bytes, bool):
            ok = ok and len(body) == declared_bytes
        report.add(f"cas:{body_path}", ok, "content-addressed body")
    report.add("inventory_count", True, str(len(inventory)))
    return report


# --------------------------------------------------------------------------- determinations


BOUND_DETERMINATION_INPUTS = (
    "census",
    "protocol",
    "content_lexicon",
    "determiner",
    "determination",
)


def verify_determination(root: Path, receipt_path: Path) -> Report:
    """Verify an R1 determination receipt.

    A determination fetches nothing, so there is no ledger and no content-addressed body to
    check. What must hold instead is that every input which could change the answer is bound by
    SHA-256, and that the funnel the receipt reports is arithmetically possible: monotone across
    the gates in the declared order, ending exactly at the admitted counts, and summing to the
    number of items determined.
    """
    relative = str(receipt_path.resolve().relative_to(root.resolve()))
    report = Report(kind="determination", path=relative)
    try:
        receipt = read_json(receipt_path)
    except (OSError, ValueError) as exc:
        report.add("receipt_readable", False, str(exc))
        return report
    if not isinstance(receipt, dict):
        report.add("receipt_is_object", False)
        return report

    for name in BOUND_DETERMINATION_INPUTS:
        path = receipt.get(f"{name}_path")
        expected = receipt.get(f"{name}_sha256")
        if not isinstance(path, str):
            report.add(f"{name}_path", False, "missing or malformed path")
            continue
        _tracked_hash_check(root, report, f"{name}:{path}", path, expected)

    gates = receipt.get("gate_order")
    funnel = receipt.get("funnel")
    admitted = receipt.get("admitted")
    if not isinstance(gates, list) or not isinstance(funnel, Mapping):
        report.add("funnel_present", False, "no gate order or funnel")
        return report
    stages = ["discovered"] + [f"passed_{gate}" for gate in gates]
    for painter, total in (receipt.get("funnel", {}).get("discovered") or {}).items():
        counts = []
        for stage in stages:
            row = funnel.get(stage)
            if not isinstance(row, Mapping) or not isinstance(row.get(painter), int):
                report.add(f"funnel:{painter}:{stage}", False, "missing count")
                counts = []
                break
            counts.append(row[painter])
        if not counts:
            continue
        report.add(
            f"funnel_monotone:{painter}",
            counts == sorted(counts, reverse=True),
            " >= ".join(str(count) for count in counts),
        )
        if isinstance(admitted, Mapping):
            report.add(
                f"funnel_ends_at_admitted:{painter}",
                counts[-1] == admitted.get(painter),
                f"{counts[-1]} vs {admitted.get(painter)}",
            )
        report.add(f"discovered_is_total:{painter}", counts[0] == total)

    failures = receipt.get("failed_gate_counts")
    determined = receipt.get("items_determined")
    if isinstance(failures, Mapping) and isinstance(admitted, Mapping):
        accounted = sum(failures.values()) + sum(admitted.values())
        report.add("every_item_is_accounted_for", accounted == determined, f"{accounted}")
        report.add(
            "failed_gates_are_declared_gates",
            set(failures).issubset(set(gates)),
            ", ".join(sorted(set(failures) - set(gates))),
        )
    return report


# --------------------------------------------------------------------------- audit


def discover(root: Path) -> dict:
    manifests = root / MANIFEST_DIR
    freezes = sorted(manifests.glob("*freeze*.json"))
    ledgers = sorted(manifests.glob("*request_events*.jsonl"))
    receipts = sorted(manifests.glob("*execution_receipt*.json")) + sorted(
        manifests.glob("*/execution_receipt.json")
    )
    determinations = sorted(manifests.glob("*determination_receipt*.json"))
    return {
        "freezes": freezes,
        "ledgers": ledgers,
        "receipts": sorted(set(receipts) - set(determinations)),
        "determinations": determinations,
    }


def load_acknowledgements(root: Path, acknowledge: bool) -> Optional[dict]:
    path = root / ACKNOWLEDGEMENTS
    if not acknowledge or not path.is_file():
        return None
    value = read_json(path)
    if not isinstance(value, dict):
        raise EvidenceError("evidence acknowledgements must be a JSON object")
    return value


def audit(root: Path, acknowledge: bool = True) -> dict:
    root = root.resolve()
    if not is_git_repository(root):
        raise EvidenceError("commit-bound verification requires a git checkout")
    found = discover(root)
    acknowledgements = load_acknowledgements(root, acknowledge)
    index = workspace_index(root) if found["receipts"] else {}
    reports = (
        [verify_freeze(root, path, acknowledgements) for path in found["freezes"]]
        + [verify_event_ledger(root, path) for path in found["ledgers"]]
        + [verify_receipt(root, path, index) for path in found["receipts"]]
        + [verify_determination(root, path) for path in found["determinations"]]
    )
    return {
        "schema_version": "painter-feature-generation-v1-evidence-audit/1.1",
        "head_commit": head_commit(root),
        "verification_rule": (
            "frozen inputs and receipt-named files tracked by git are verified at the freeze's "
            "recording commit or at any commit in the path's history; untracked research bytes "
            "are verified in the working tree; hashes are never refreshed; acknowledgements "
            "excuse only the exact bound hash they name"
        ),
        "acknowledgements_path": str(ACKNOWLEDGEMENTS) if acknowledgements else None,
        "ok": all(report.ok for report in reports),
        "counts": {
            "freezes": len(found["freezes"]),
            "event_ledgers": len(found["ledgers"]),
            "execution_receipts": len(found["receipts"]),
            "determinations": len(found["determinations"]),
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
