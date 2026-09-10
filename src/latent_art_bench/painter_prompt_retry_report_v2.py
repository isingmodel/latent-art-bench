"""Correct shared plot limits in a separate report revision; all retry evidence is preserved."""

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from latent_art_bench import painter_prompt_retry_v1 as retry
from latent_art_bench.io import read_json, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)

OUTPUT = retry.REPORT.with_name(retry.RUN + "-r2")
RECEIPT = retry.DIRECTORY / "report_revision_2.json"
CODE = Path("src/latent_art_bench/painter_prompt_retry_report_v2.py")
TEST = Path("tests/test_painter_prompt_retry_report_v2.py")


def figure(data):
    """Derive shared bounds from both aliases before drawing either row."""
    lookup = {
        (r["alias"], r["method_id"], r["painter_id"], r["family"]): r["distance"]
        for r in data["absolute"]
    }
    maxima = {
        f: max(r["distance"] for r in data["absolute"] if r["family"] == f)
        for f in retry.features.FAMILIES
    }
    fig, axes = retry.plt.subplots(2, 3, figsize=(15, 8), sharex="col", layout="constrained")
    for i, alias in enumerate(retry.generation.ALIASES):
        for j, family in enumerate(retry.features.FAMILIES):
            ax = axes[i, j]
            for k, method in enumerate(retry.METHOD_IDS):
                ax.scatter(
                    [lookup[alias, method, p, family] for p in retry.PAINTER_IDS],
                    np.arange(4) + (k - 1) * 0.22,
                    c=retry.COLORS[k],
                    label=retry.METHOD_LABELS[method],
                    s=34,
                )
            ax.set(title=f"{alias} · {family}", xlabel="Finite feature distance")
            ax.set_yticks(range(4), [retry.SHORT_LABELS[p] for p in retry.PAINTER_IDS])
            ax.set_ylim(3.5, -0.5)
            ax.set_xlim(0, max(0.01, 1.08 * maxima[family]))
            ax.grid(axis="x", alpha=0.2)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
    fig.suptitle(
        "Generated images versus original-painting reference\n"
        "Later retry completion; descriptive distances, no confidence intervals"
    )
    return fig


def render(root, target):
    data = read_json(root / retry.DIRECTORY / "analysis.json")
    target.mkdir(parents=True, exist_ok=False)
    (target / "plots").mkdir()
    for name in ["REPORT.md", *[f"{t}.csv" for t in retry.TABLES]]:
        shutil.copyfile(root / retry.REPORT / name, target / name)
    markdown = target / "REPORT.md"
    markdown.write_text(
        markdown.read_text(encoding="utf-8").replace(
            "painter_prompt_retry_v1 check", "painter_prompt_retry_report_v2 check"
        ),
        encoding="utf-8",
    )
    with retry.plt.rc_context(retry.STYLE):
        retry._save(figure(data), target, "target_distances")


def build(root):
    retry.check(root)
    paths = [CODE, TEST, retry.DIRECTORY / "analysis.json", retry.DIRECTORY / "report_receipt.json"]
    paths += [p.relative_to(root) for p in (root / retry.REPORT).rglob("*") if p.is_file()]
    inputs = bindings(root, paths)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    retry._verify_commit(root, commit, inputs)
    if (root / RECEIPT).exists() or (root / OUTPUT).exists():
        raise FileExistsError("report revision is immutable")
    render(root, root / OUTPUT)
    outputs = bindings(
        root, [p.relative_to(root) for p in (root / OUTPUT).rglob("*") if p.is_file()]
    )
    publish(
        root / RECEIPT,
        dict(
            recorded_git_commit=commit,
            inputs=inputs,
            outputs=outputs,
            created_at_utc=utc_now().isoformat(),
            reason="Original figure could clip lower-row points after upper-row shared-axis "
            "autoscale "
            "was disabled. Revision sets the family maximum from both aliases plus 8% margin.",
            numeric_changes=False,
            original_report_preserved=True,
        ),
    )
    return dict(status="published", report=str(OUTPUT / "REPORT.md"))


def check(root):
    retry.check(root)
    receipt = read_json(root / RECEIPT)
    verify_bindings(root, receipt["inputs"])
    verify_bindings(root, receipt["outputs"])
    retry._verify_commit(root, receipt["recorded_git_commit"], receipt["inputs"])
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "report"
        render(root, target)
        files = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        actual = {p.relative_to(root / OUTPUT) for p in (root / OUTPUT).rglob("*") if p.is_file()}
        if files != actual or any(
            (target / p).read_bytes() != (root / OUTPUT / p).read_bytes() for p in files
        ):
            raise ValueError("report revision reproduction differs")
    return dict(status="PASS", numeric_changes=False, report_files=len(files))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    print(json.dumps(globals()[args.command](Path.cwd().resolve()), indent=2))


if __name__ == "__main__":
    main()
