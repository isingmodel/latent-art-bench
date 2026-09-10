"""Create-once inventory/freeze/results, then deterministic offline replay."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from . import analysis, inputs, report

NAME = "painter_naming_geometry_v1"
RUN = "pngv1-20260910"
DIRECTORY = Path("data/manifests") / NAME / RUN
REPORTS = Path("reports") / NAME / RUN


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    with path.open("x") as stream:
        stream.write(content)


def inventory(root):
    origins = [root / p for p in inputs.ORIGINS]
    value = inputs.assemble(read(origins[0])["study1"], read(origins[1]),
                            [json.loads(line) for line in origins[2].read_text().splitlines()])
    value["origins"] = {str(p): digest(root / p) for p in inputs.ORIGINS}
    publish(root / DIRECTORY / "inputs.json", value)
    return dict(status="inventoried", new_images=0)


def prepare(root):
    paths = [p.relative_to(root) for category in ("src/latent_art_bench", "tests", "studies")
             for p in (root / category / NAME).rglob("*")
             if p.is_file() and p.suffix in (".py", ".md")]
    paths += [DIRECTORY / "inputs.json", Path("uv.lock"), Path("pyproject.toml")]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for path in paths:
        committed = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root)
        if committed != (root / path).read_bytes():
            raise ValueError(f"bound input is not clean at recorded commit: {path}")
    publish(root / DIRECTORY / "freeze.json", dict(
        run_id=RUN, recorded_git_commit=commit, post_result=True,
        bindings={str(p): digest(root / p) for p in sorted(paths)},
        collection_authorized=False, hypothesis_tests_added=0,
    ))
    return dict(status="prepared", recorded_git_commit=commit, inputs=len(paths))


def verify(root):
    frozen = read(root / DIRECTORY / "freeze.json")
    for path, expected in frozen["bindings"].items():
        if digest(root / path) != expected:
            raise ValueError(f"frozen input changed: {path}")
    return frozen


def build(root, check=False):
    freeze = verify(root)
    output = root / DIRECTORY / "analysis.json"
    receipt = root / DIRECTORY / "receipt.json"
    report_dir = root / REPORTS
    if not check and (output.exists() or receipt.exists() or report_dir.exists()):
        raise ValueError("terminal output exists; a new census is required")
    value = analysis.compute(read(root / DIRECTORY / "inputs.json"))
    # Validate native, finite result before creating any terminal file.
    value = json.loads(json.dumps(value, allow_nan=False))
    narrative = report.text_report(value)
    if check:
        if read(output) != value or (report_dir / "REPORT.md").read_text() != narrative:
            raise ValueError("numerical/report replay mismatch")
        old = read(receipt)
        for path, expected in old["outputs"].items():
            if digest(root / path) != expected:
                raise ValueError(f"terminal output changed: {path}")
        if old["freeze_sha256"] != digest(root / DIRECTORY / "freeze.json"):
            raise ValueError("freeze receipt mismatch")
        return dict(status="verified", exact_numerical_replay=True, cells=60, transfer_cells=18)
    report_dir.mkdir(parents=True)
    (report_dir / "REPORT.md").write_text(narrative)
    report.plot(value, report_dir / "naming_geometry.pdf")
    publish(output, value)
    outputs = [DIRECTORY / "analysis.json", REPORTS / "REPORT.md", REPORTS / "naming_geometry.pdf"]
    publish(receipt, dict(recorded_git_commit=freeze["recorded_git_commit"],
                         freeze_sha256=digest(root / DIRECTORY / "freeze.json"),
                         outputs={str(p): digest(root / p) for p in outputs}, new_images=0))
    return dict(status="completed", cells=60, transfer_cells=18, new_images=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inventory", "prepare", "analyze", "verify"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if args.action == "inventory":
        result = inventory(args.root)
    elif args.action == "prepare":
        result = prepare(args.root)
    else:
        result = build(args.root, check=args.action == "verify")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
