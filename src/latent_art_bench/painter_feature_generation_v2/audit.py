"""Read-only verification of the v2 evidence graph, including ignored runtime bytes."""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
from collections import Counter
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    digest,
    events,
)


def audit(root: Path) -> dict:
    checks, failures = 0, []
    cache = {}

    def check(condition: bool, label: str):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    def file_hash(relative: str | Path) -> str | None:
        path = (root / relative).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError:
            return None
        if path not in cache:
            cache[path] = hash_file(path) if path.is_file() else None
        return cache[path]

    for path in sorted((root / MANIFESTS).rglob("*.json")):
        label = str(path.relative_to(root))
        try:
            record = read_json(path)
            commit = record.get("recorded_git_commit")
            if commit:
                valid_commit = bool(re.fullmatch(r"[0-9a-f]{40}", str(commit)))
                if valid_commit:
                    valid_commit = (
                        subprocess.run(
                            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                            cwd=root,
                            capture_output=True,
                        ).returncode
                        == 0
                    )
                check(valid_commit, f"{label}: recording commit exists")
                if not valid_commit:
                    commit = None
            for bound in record.get("inputs", []) + record.get("files", []):
                relative, expected = bound["path"], bound["sha256"]
                observed = None
                if commit:
                    blob = subprocess.run(
                        ["git", "show", f"{commit}:{relative}"], cwd=root, capture_output=True
                    )
                    if blob.returncode == 0:
                        observed = hashlib.sha256(blob.stdout).hexdigest()
                if observed is None:
                    observed = file_hash(relative)
                check(observed == expected, f"{label}: bound {relative}")
            pairs = {
                "frame_sha256": "frame.jsonl",
                "acquisitions_sha256": "acquisitions.jsonl",
                "outputs_sha256": "outputs.jsonl",
                "renderings_sha256": "renderings.jsonl",
                "assessment_freeze_sha256": "assessment_freeze.json",
                "calibration_freeze_sha256": "calibration_freeze.json",
                "scaler_sha256": "scaler.json",
                "development_feature_sha256": "development_features.jsonl",
                "uncropped_feature_sha256": "uncropped_features.jsonl",
            }
            if "method_freeze_sha256" in record:
                parent = path.parent
                while parent != root and not (parent / "method_freeze.json").is_file():
                    parent = parent.parent
                check(
                    file_hash((parent / "method_freeze.json").relative_to(root))
                    == record["method_freeze_sha256"],
                    f"{label}: method freeze",
                )
            if "requests_sha256" in record:
                pairs["requests_sha256"] = (
                    "metadata_requests.jsonl" if "metadata" in path.name else "requests.jsonl"
                )
            if "feature_file_sha256" in record:
                pairs["feature_file_sha256"] = f"{record['stage']}_features.jsonl"
            if "freeze_sha256" in record:
                pairs["freeze_sha256"] = (
                    "generation_freeze.json"
                    if "generation" in path.name
                    else "acquisition_freeze.json"
                )
            if "ledger_sha256" in record:
                candidates = (
                    ["assessment_events.jsonl"]
                    if "assessment" in path.name
                    else ["generation_events.jsonl"]
                    if "generation" in path.name
                    else ["metadata_events.jsonl"]
                    if "metadata" in path.name
                    else ["image_events.jsonl", "acquisition_events.jsonl"]
                )
                ledger = next((name for name in candidates if (path.parent / name).exists()), None)
                check(ledger is not None, f"{label}: ledger exists")
                if ledger:
                    pairs["ledger_sha256"] = ledger
            for field, filename in pairs.items():
                if field in record:
                    check(
                        file_hash((path.parent / filename).relative_to(root)) == record[field],
                        f"{label}: {filename}",
                    )
            if "feature_file_sha256" in record:
                rows = read_jsonl(path.parent / f"{record['stage']}_features.jsonl")
                check(
                    len(rows) == record["terminal_records"] == record["expected_records"]
                    and dict(Counter(r["status"] for r in rows)) == record["statuses"],
                    f"{label}: complete feature accounting",
                )
            if path.name == "generation_receipt.json":
                rows = read_jsonl(path.parent / "outputs.jsonl")
                requests = read_jsonl(path.parent / "requests.jsonl")
                check(
                    len(rows)
                    == len(requests)
                    == record["terminal_requests"]
                    == record["expected_requests"]
                    and len({r["request_id"] for r in rows}) == len(rows)
                    and {r["request_id"] for r in rows} == {r["request_id"] for r in requests},
                    f"{label}: complete generation accounting",
                )
                check(
                    record["complete_generated_grid"]
                    == all(r["status"] == "generated" for r in rows),
                    f"{label}: complete grid claim",
                )
            if path.name == "assessment_receipt.json":
                outcomes = record["outcomes"]
                ledger_rows = events(path.parent / "assessment_events.jsonl")
                terminal = {
                    r["request_id"]: r for r in ledger_rows if r["kind"] == "model_terminal"
                }
                check(
                    all(
                        all(terminal.get(r["request_id"], {}).get(k) == v for k, v in r.items())
                        for r in outcomes
                    ),
                    f"{label}: outcomes agree with terminal ledger",
                )
                check(
                    record["image_attempts"]
                    == sum(
                        r["kind"] == "attempt" and r.get("method") == "POST" for r in ledger_rows
                    ),
                    f"{label}: attempt count agrees with ledger",
                )
                check(
                    len(outcomes) == 2
                    and {r["model"] for r in outcomes} == {"gpt-image-1", "gpt-image-2"},
                    f"{label}: complete model accounting",
                )
                check(
                    record["image_attempts"] == sum(r["attempted"] for r in outcomes) <= 2,
                    f"{label}: bounded attempts",
                )
                check(
                    record["images_generated"] == sum(r["status"] == "generated" for r in outcomes),
                    f"{label}: generated count",
                )
        except (ValueError, KeyError, OSError, TypeError) as exc:
            check(False, f"{label}: {type(exc).__name__}: {exc}")

    for path in sorted((root / MANIFESTS).rglob("*_events.jsonl")):
        try:
            rows = events(path)
            check(True, f"{path.name}: valid hash chain")
            for row in rows:
                if "raw_path" in row:
                    check(
                        file_hash(row["raw_path"]) == row["raw_sha256"],
                        f"{path.name}: raw {row['raw_path']}",
                    )
                elif "body_sha256" in row:
                    relative = WORKSPACE / path.parent.name / "raw" / row["body_sha256"]
                    check(file_hash(relative) == row["body_sha256"], f"{path.name}: {relative}")
                if "image_path" in row:
                    check(
                        file_hash(row["image_path"]) == row["sha256"],
                        f"{path.name}: image {row['image_path']}",
                    )
        except (ValueError, OSError, KeyError) as exc:
            check(False, f"{path.name}: {exc}")

    for path in sorted((root / MANIFESTS).rglob("*_features.jsonl")):
        try:
            rows = read_jsonl(path)
            check(len({r["image_id"] for r in rows}) == len(rows), f"{path}: unique measured IDs")
            for row in rows:
                if row["status"] == "measured":
                    check(
                        len(row["values"]) == 31
                        and all(math.isfinite(v) for v in row["values"])
                        and digest(row["values"]) == row["feature_sha256"],
                        f"{path}: feature {row['image_id']}",
                    )
        except (ValueError, OSError, KeyError, TypeError) as exc:
            check(False, f"{path.name}: {exc}")

    for path in sorted((root / MANIFESTS).rglob("frame.jsonl")):
        try:
            rows = read_jsonl(path)
            check(len({r["work_id"] for r in rows}) == len(rows), f"{path}: unique work IDs")
            check(
                all(
                    not r["exposure_matches"] or r["role"] == "historical_development" for r in rows
                ),
                f"{path}: historical exposure remains development-only",
            )
        except (ValueError, OSError, KeyError, TypeError) as exc:
            check(False, f"{path.name}: {exc}")
    return dict(
        overall="OK" if not failures else "FAIL",
        checks=checks,
        failed=len(failures),
        failures=failures,
        scope="commit-bound v2 inputs, immutable outputs, hash chains, runtime bytes, roles",
    )
