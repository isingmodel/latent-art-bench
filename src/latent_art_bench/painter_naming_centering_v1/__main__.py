"""Commit-bound centering successor with create-once output and exact replay."""

import argparse
import json
import subprocess
from pathlib import Path

from latent_art_bench.painter_naming_geometry_v1.__main__ import (
    DIRECTORY as PREDECESSOR,
)
from latent_art_bench.painter_naming_geometry_v1.__main__ import digest, publish, read
from latent_art_bench.painter_naming_geometry_v1.__main__ import verify as verify_predecessor

from .analysis import compute

NAME = "painter_naming_centering_v1"
RUN = "pncv1-20260910"
DIRECTORY = Path("data/manifests") / NAME / RUN
REPORTS = Path("reports") / NAME / RUN


def narrative(value):
    lines = ["# Evaluation-centered scaling of painter-naming feature clouds", "",
             "Post-result successor to pngv1-20260910. The added map uses the evaluation-free "
             "mean and unchanged original training displacement/scalar. It is cohort adaptation, "
             "not unchanged pointwise transfer. No new data or hypothesis tests.", "",
             "The centered-minus-shift comparison changes scale at an identical weighted mean. "
             "Old-scale-minus-centered changes only the origin-induced mean offset at identical "
             "centered shape. These add along a specified algebraic path, not a unique causal "
             "decomposition. Positive values mean the first map has greater energy.", "",
             "No corrected conditional-mean residual is estimated for the new map: evaluation-"
             "free centering induces dependence across residual repetitions.", "",
             "| Cohort | Pipeline | View | Service | Painter | Shift | Old scale | "
             "Centered scale | Named | Centered−shift | Old−centered | Named−centered |",
             "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for key in ("original", "transfer"):
        for r in value[key]:
            energies = r["energy_mean"] if key == "original" else {
                k: v["energy"] for k, v in r["energies"].items()}
            contrast = r["centering_contrast_mean" if key == "original"
                         else "centering_contrasts"]
            cells = [key, r["pipeline"], r["view"], r.get("route", "flux_2_max"), r["painter"]]
            cells += [f"{energies[k]:.6f}" for k in
                      ("translation", "translation_scale", "centered_scale", "named")]
            cells += [f"{contrast[k]:.6f}" for k in
                      ("centered_minus_translation", "old_scale_minus_centered")]
            cells += [f"{energies['named']-energies['centered_scale']:.6f}"]
            lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def prepare(root):
    old = verify_predecessor(root)
    paths = [Path(p) for p in old["bindings"]]
    paths += [PREDECESSOR / name for name in ("freeze.json", "analysis.json", "receipt.json")]
    paths += [p.relative_to(root) for category in ("src/latent_art_bench", "tests", "studies")
              for p in (root / category / NAME).rglob("*")
              if p.is_file() and p.suffix in (".py", ".md")]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for path in paths:
        if subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=root) != (
                root / path).read_bytes():
            raise ValueError(f"unclean bound source/input: {path}")
    publish(root / DIRECTORY / "freeze.json", dict(
        run_id=RUN, recorded_git_commit=commit, post_result=True,
        predecessor_run="pngv1-20260910", hypothesis_tests_added=0,
        bindings={str(p): digest(root / p) for p in sorted(set(paths))},
    ))
    return dict(status="prepared", recorded_git_commit=commit)


def build(root, check=False):
    freeze = read(root / DIRECTORY / "freeze.json")
    for path, expected in freeze["bindings"].items():
        if digest(root / path) != expected:
            raise ValueError(f"bound input changed: {path}")
    output, receipt = root / DIRECTORY / "analysis.json", root / DIRECTORY / "receipt.json"
    report = root / REPORTS / "REPORT.md"
    if not check and (output.exists() or receipt.exists() or report.parent.exists()):
        raise ValueError("terminal centering output exists")
    value = compute(read(root / PREDECESSOR / "inputs.json"),
                    read(root / PREDECESSOR / "analysis.json"))
    text = narrative(value)
    if check:
        if read(output) != value or report.read_text() != text:
            raise ValueError("centering numerical/report replay mismatch")
        recorded = read(receipt)
        if digest(root / DIRECTORY / "freeze.json") != recorded["freeze_sha256"]:
            raise ValueError("centering freeze receipt mismatch")
        for path, expected in recorded["outputs"].items():
            if digest(root / path) != expected:
                raise ValueError(f"centering output changed: {path}")
        return dict(status="verified", exact_numerical_replay=True, predecessor_exact=True)
    report.parent.mkdir(parents=True)
    report.write_text(text)
    publish(output, value)
    publish(receipt, dict(
        recorded_git_commit=freeze["recorded_git_commit"],
        freeze_sha256=digest(root / DIRECTORY / "freeze.json"), new_images=0,
        outputs={str(p): digest(root / p) for p in
                 (DIRECTORY / "analysis.json", REPORTS / "REPORT.md")},
    ))
    return dict(status="completed", original_cells=60, transfer_cells=18, new_images=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "analyze", "verify"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = prepare(args.root) if args.action == "prepare" else build(
        args.root, check=args.action == "verify")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
