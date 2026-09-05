"""Reproducible, offline distance reports from existing painter-feature measurements."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import tempfile
from pathlib import Path

DEFAULT_OUTPUT = "reports/painter_feature_distance_v1"
TABLES = (
    "distances", "contrasts", "coordinates", "reference_distances",
    "block_distances", "block_summary",
)


def encoded(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
            + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_records(base: Path, paths) -> list[dict]:
    return [{"path": p.relative_to(base).as_posix(), "sha256": sha256(p)}
            for p in sorted(paths)]


def resolve_output(root: Path, output: str | Path) -> Path:
    path = (root / output).resolve()
    relative = path.relative_to(root)
    if len(relative.parts) < 2 or relative.parts[0] not in {"reports", "tmp"}:
        raise ValueError("output must be a new directory beneath reports/ or tmp/")
    return path


def code_paths(root: Path) -> list[Path]:
    package = root / "src/latent_art_bench"
    return [
        *sorted((package / "painter_feature_distance_v1").glob("*.py")),
        package / "cli.py", package / "io.py",
        package / "painter_feature_generation_v1/panel.py",
        *(package / "painter_feature_generation_v2" / name for name in
          ("features.py", "statistics.py", "empirical.py", "artifacts.py")),
        root / "pyproject.toml", root / "uv.lock",
    ]


def write_bundle(result: dict, output: Path) -> None:
    from .report import write_report

    (output / "analysis.json").write_bytes(encoded(result))
    for name in TABLES:
        rows = result[name]
        with (output / f"{name}.csv").open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    write_report(result, output)


def build(root: Path, output: str | Path, method_id: str) -> dict:
    from .analysis import analyze

    root = root.resolve()
    destination = resolve_output(root, output)
    if destination.exists():
        raise FileExistsError("output already exists; use check or choose a new output directory")
    code = file_records(root, code_paths(root))
    result = analyze(root, method_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Render in a temporary sibling before reserving the final directory. Failed rendering
    # leaves neither a partial report nor a path that blocks a corrected build.
    with tempfile.TemporaryDirectory(prefix=".feature-distance-", dir=destination.parent) as tmp:
        staging = Path(tmp)
        write_bundle(result, staging)
        verify_files(root, result["source"]["inputs"])
        verify_files(root, code)
        provenance = dict(
            schema_version=result["schema_version"], method_id=method_id,
            kind="derived_report_provenance_not_a_new_study_freeze",
            source_inputs=result["source"]["inputs"], code_inputs=code,
            runtime=dict(python=platform.python_version(), packages={
                name: importlib.metadata.version(name)
                for name in ("numpy", "scipy", "matplotlib", "Pillow")
            }),
            outputs=file_records(staging, [p for p in staging.rglob("*") if p.is_file()]),
        )
        (staging / "provenance.json").write_bytes(encoded(provenance))
        destination.mkdir()  # Exclusive: never replace an existing output, including an empty one.
        for child in sorted(staging.iterdir()):
            child.rename(destination / child.name)
    return dict(status="complete", output=destination.relative_to(root).as_posix(),
                distances=len(result["distances"]), coordinates=len(result["coordinates"]),
                block_distances=len(result["block_distances"]))


def verify_files(base: Path, records: list[dict]) -> None:
    seen = set()
    for row in records:
        path = (base / row["path"]).resolve()
        key = path.relative_to(base.resolve()).as_posix()
        if key in seen:
            raise ValueError(f"duplicate provenance path: {key}")
        seen.add(key)
        if sha256(path) != row["sha256"]:
            raise ValueError(f"provenance hash mismatch: {key}")


def check(root: Path, output: str | Path) -> dict:
    from .analysis import analyze

    root = root.resolve()
    directory = resolve_output(root, output)
    provenance = json.loads((directory / "provenance.json").read_bytes())
    for base, key in ((root, "source_inputs"), (root, "code_inputs"), (directory, "outputs")):
        verify_files(base, provenance[key])
    actual_files = {
        p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()
    }
    expected_files = {r["path"] for r in provenance["outputs"]} | {"provenance.json"}
    if actual_files != expected_files:
        raise ValueError("report bundle file set differs from provenance")
    result = analyze(root, provenance["method_id"])
    if encoded(result) != (directory / "analysis.json").read_bytes():
        raise ValueError("numeric analysis does not reproduce byte-for-byte")
    # Re-render all tables, prose and plots in isolation; never run the sealed v2 report writer.
    with tempfile.TemporaryDirectory(prefix="feature-distance-check-") as tmp:
        reproduced = Path(tmp)
        write_bundle(result, reproduced)
        expected = {r["path"]: r["sha256"] for r in provenance["outputs"]}
        actual = {r["path"]: r["sha256"] for r in file_records(
            reproduced, [p for p in reproduced.rglob("*") if p.is_file()])}
        if actual != expected:
            raise ValueError("report/tables/plots differ; check recorded code and runtime")
    return dict(status="PASS", outputs_verified=len(expected),
                reproduction="numeric results, CSV tables, Markdown and plots match byte-for-byte")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    build_parser = commands.add_parser("build", help="Create a new report; never access raw images")
    build_parser.add_argument("--method-id", default="pfg2-method-20260905")
    build_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    check_parser = commands.add_parser("check", help="Verify inputs and reproduce every output")
    check_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        result = (build(args.root, args.output, args.method_id) if args.command == "build"
                  else check(args.root, args.output))
    except (ValueError, FileNotFoundError, FileExistsError, KeyError) as exc:
        parser.exit(1, f"feature-distances: {exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
