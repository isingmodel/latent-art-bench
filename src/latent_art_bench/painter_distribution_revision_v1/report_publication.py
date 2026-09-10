"""Create-once report publication and byte replay without rerunning numeric analysis."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import analysis, common

RECEIPT = common.DIRECTORY / "report_receipt.json"


def source_paths(root, freeze):
    """Include the already bound dependency closure plus the new rendering sources."""
    paths = {Path(r["path"]) for r in freeze["inputs"]}
    paths.update(common.PACKAGE / name for name in (
        "__init__.py", "report.py", "report_publication.py", "common.py", "analysis.py",
    ))
    paths.update(p.relative_to(root) for p in root.glob(
        "tests/painter_distribution_revision_v1/test_report*.py"
    ))
    paths.update(common.DIRECTORY / name for name in (
        "freeze.json", "analysis.json", "analysis_receipt.json",
    ))
    return sorted(paths)


def verify_numeric(root):
    freeze = analysis.verify(root)
    receipt = read_json(root / common.DIRECTORY / "analysis_receipt.json")
    if receipt["freeze_sha256"] != hash_file(root / common.DIRECTORY / "freeze.json"):
        raise ValueError("numeric freeze receipt mismatch")
    if receipt["recorded_git_commit"] != freeze["recorded_git_commit"]:
        raise ValueError("numeric source commit receipt mismatch")
    if receipt["analysis_sha256"] != hash_file(root / common.DIRECTORY / "analysis.json"):
        raise ValueError("numeric analysis receipt mismatch")
    return freeze


def render(root, directory):
    from . import report

    return report.render(root, directory)


def output_paths(directory, returned):
    """Reject path escapes, symlinks, duplicates and undeclared rendered files."""
    paths = [Path(p) for p in returned]
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("report output list is empty or duplicated")
    if any(p.is_absolute() or ".." in p.parts or p == Path(".") for p in paths):
        raise ValueError("report output path must be portable and confined")
    entries = list(directory.rglob("*"))
    if any(p.is_symlink() for p in entries):
        raise ValueError("report output must not contain symlinks")
    actual = {p.relative_to(directory) for p in entries if p.is_file()}
    if actual != set(paths):
        raise ValueError("report output inventory differs from renderer declaration")
    return sorted(paths)


def build(root, check=False):
    freeze = verify_numeric(root)
    final, receipt_path = root / common.REPORT, root / RECEIPT
    if check:
        receipt = read_json(receipt_path)
        verify_bindings(root, receipt["inputs"])
        verify_bindings(root, receipt["outputs"])
        recorded_paths = output_paths(final, [
            Path(r["path"]).relative_to(common.REPORT) for r in receipt["outputs"]
        ])
        inputs = receipt["inputs"]
    else:
        if final.exists() or final.is_symlink() or receipt_path.exists():
            raise ValueError("report publication is terminal; do not overwrite")
        paths = source_paths(root, freeze)
        source_commit = committed(root, paths)
        inputs = bindings(root, paths)
    with tempfile.TemporaryDirectory(prefix="pdrv1-report-") as temporary:
        staged = Path(temporary) / "report"
        staged.mkdir()
        paths = output_paths(staged, render(root, staged))
        verify_bindings(root, inputs)  # Source and numeric inputs must stay fixed while rendering.
        if check:
            if paths != recorded_paths or any(
                (staged / p).read_bytes() != (final / p).read_bytes() for p in paths
            ):
                raise ValueError("report byte replay differs")
            return dict(status="verified", byte_replay=True, outputs=len(paths),
                        run_id=common.RUN_ID)
        # The complete render is validated before reserving any terminal report path.
        final.parent.mkdir(parents=True, exist_ok=True)
        final.mkdir(exist_ok=False)
        for path in paths:
            destination = final / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            with (staged / path).open("rb") as source, destination.open("xb") as target:
                shutil.copyfileobj(source, target)
        publish(receipt_path, dict(
            run_id=common.RUN_ID, recorded_git_commit=source_commit,
            inputs=inputs,
            outputs=bindings(root, [common.REPORT / p for p in paths]),
            numeric_recomputed=False,
            interpretation="Report bytes derived from the sealed numeric analysis; "
                           "numeric recomputation is a separate check command.",
        ))
    return dict(status="published", run_id=common.RUN_ID, outputs=len(paths),
                report=common.REPORT.as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    command = parser.parse_args().command
    print(json.dumps(build(Path.cwd(), check=command == "check"), indent=2))


if __name__ == "__main__":
    main()
