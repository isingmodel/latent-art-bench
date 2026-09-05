"""Read-only numerical replay and byte-for-byte report reproduction."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from latent_art_bench.io import canonical_json, hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    identifier,
    verify_bindings,
)

from . import analysis, randomization, report
from .common import MANIFESTS, PACKAGE


def reproduce(root: Path, run_id: str) -> dict:
    """Recompute all numeric results and rendered files without changing study evidence.

    The checkout must match the run's frozen implementation. Only the analysis creation
    timestamp is normalized; every other result value, list order and output byte is compared.
    This reads existing measured features, never image bytes or a generation transport.
    """
    root = Path(root).resolve()
    identifier(run_id)
    directory = root / MANIFESTS / run_id
    directory.resolve().relative_to(root)
    recorded = read_json(directory / "analysis.json")
    report._validate(recorded, run_id)
    verify_bindings(root, recorded["inputs"])

    # build_result validates current and historical freeze inputs through generation._load.
    rebuilt = analysis.build_result(root, run_id)
    if not isinstance(recorded.get("completed_at_utc"), str):
        raise ValueError("recorded analysis lacks its creation timestamp")
    rebuilt["completed_at_utc"] = recorded["completed_at_utc"]
    if canonical_json(rebuilt) != canonical_json(recorded):
        raise ValueError("recomputed analysis differs from the retained numeric result")

    freeze = read_json(directory / "generation_freeze.json")
    for source in [Path(module.__file__) for module in (analysis, randomization, report)] + [
        Path(__file__)
    ]:
        relative = PACKAGE / source.name
        expected = dict(path=relative.as_posix(), sha256=hash_file(source))
        if expected not in freeze["inputs"]:
            raise ValueError(f"loaded replay implementation differs from frozen source: {relative}")
    receipt = read_json(directory / "report_receipt.json")
    expected_inputs = bindings(
        root,
        [
            MANIFESTS / run_id / "analysis.json",
            PACKAGE / "report.py",
            MANIFESTS / run_id / "generation_freeze.json",
        ],
    )
    if (
        receipt["run_id"] != run_id
        or receipt["analysis_status"] != recorded["status"]
        or receipt["recorded_git_commit"] != freeze["recorded_git_commit"]
        or sorted(receipt["inputs"], key=lambda row: row["path"]) != expected_inputs
    ):
        raise ValueError("report receipt does not bind the retained analysis and implementation")
    verify_bindings(root, receipt["inputs"])

    target = root / report.REPORTS / run_id
    target.resolve().relative_to(root)
    if (
        target.is_symlink()
        or not target.is_dir()
        or any(path.is_symlink() for path in target.rglob("*"))
    ):
        raise ValueError("retained report is not a regular complete bundle")
    actual = {p.relative_to(target): p for p in target.rglob("*") if p.is_file()}
    expected_files = bindings(root, [path.relative_to(root) for path in actual.values()])
    if receipt["files"] != expected_files:
        raise ValueError("retained report inventory or bytes differ from its receipt")

    with tempfile.TemporaryDirectory(prefix="painter-prompt-replay-") as temporary:
        output = Path(temporary)
        # The publishing command serializes sorted JSON before report.execute reads it.
        # Reproduce that boundary so table/reference mapping display order is identical.
        report._write_bundle(json.loads(canonical_json(rebuilt)), output)
        reproduced = {p.relative_to(output): p for p in output.rglob("*") if p.is_file()}
        if set(actual) != set(reproduced) or any(
            actual[name].read_bytes() != reproduced[name].read_bytes() for name in actual
        ):
            raise ValueError("reproduced report differs from the retained output bytes")
    return dict(
        status="PASS",
        run_id=run_id,
        analysis_status=recorded["status"],
        primary_endpoints=len(recorded.get("primary", [])),
        report_files=len(actual),
        normalized_analysis_fields=["completed_at_utc"],
        read_only=True,
    )
