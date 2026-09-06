"""Reproducible scatter plots and full-space separability, without new image access."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS, SHORT_LABELS
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, verify_bindings
from latent_art_bench.painter_prompt_study_v1.calibration_record import _verify_commit
from latent_art_bench.painter_prompt_study_v1.generation import ALIASES
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS
from latent_art_bench.painter_prompt_supplement_v1.report import (
    METHOD_LABELS,
    STYLE,
    _csv,
    _table,
    plt,
)

from .analysis import FEATURE_SETS, NAMESPACE, compute, load

OUTPUT = Path("reports") / NAMESPACE
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
METHODS = Path("studies") / NAMESPACE / "METHODS.md"
COLORS = {"original": "#525866", "gpt-image-1": "#0072B2", "gpt-image-2": "#D55E00"}
LABELS = {
    "all31": "All 31 features",
    "color": "Color",
    "spatial": "Spatial structure",
    "texture": "Digital texture",
}


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def save(fig, target, name):
    for extension in ("png", "svg"):
        metadata = (
            {"Software": NAMESPACE} if extension == "png" else {"Date": None, "Creator": NAMESPACE}
        )
        fig.savefig(target / "plots" / f"{name}.{extension}", dpi=150, metadata=metadata)
    plt.close(fig)


def projection(data, painter, family, basis="balanced_joint"):
    key = f"{painter}/{family}/{basis}"
    fit = next(r for r in data["projections"] if r["projection_id"] == key)
    points = [r for r in data["points"] if r["projection_id"] == key]
    return fit, points


def scatter(ax, fit, points, method, aliases):
    selected = [
        r
        for r in points
        if r["domain"] == "original" or (r["method_id"] == method and r["alias"] in aliases)
    ]
    for alias in ("original", *aliases):
        rows = [r for r in selected if r["alias"] == alias]
        ax.scatter(
            [r["pc1"] for r in rows],
            [r["pc2"] for r in rows],
            s=12 if alias == "original" else 24,
            alpha=0.38 if alias == "original" else 0.8,
            marker="o" if alias == "original" else ("^" if alias == ALIASES[0] else "s"),
            color=COLORS[alias],
            linewidths=0,
            label=f"{'Original' if alias == 'original' else alias} (n={len(rows)})",
        )
    retried = [r for r in selected if r["retried"]]
    if retried:
        ax.scatter(
            [r["pc1"] for r in retried],
            [r["pc2"] for r in retried],
            s=65,
            facecolors="none",
            edgecolors="#111111",
            linewidths=0.8,
        )
    # Shared limits include every method and alias; no clipped/trimmed outliers.
    for coordinate, setter in (("pc1", ax.set_xlim), ("pc2", ax.set_ylim)):
        low, high = min(r[coordinate] for r in points), max(r[coordinate] for r in points)
        margin = max((high - low) * 0.06, 0.01)
        setter(low - margin, high + margin)
    ratio = fit["explained_variance_ratio"]
    ax.set(xlabel=f"PC1 ({ratio[0]:.1%})", ylabel=f"PC2 ({ratio[1]:.1%})")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.15)
    return selected


def painter_figure(data, painter, basis):
    fit, points = projection(data, painter, "all31", basis)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5), layout="constrained")
    for i, alias in enumerate(ALIASES):
        for j, method in enumerate(METHOD_IDS):
            ax = axes[i, j]
            scatter(ax, fit, points, method, (alias,))
            ax.set_title(f"{alias} | {METHOD_LABELS[method]}")
            ax.legend(fontsize=8, loc="upper right", framealpha=0.8)
    basis_label = "balanced joint PCA" if basis == "balanced_joint" else "original-only PCA"
    fig.suptitle(
        f"{SHORT_LABELS[painter]}: originals and generated images | {basis_label}\n"
        "All 31 features; common axes across six panels; rings mark later retries"
    )
    return fig


def family_figure(data, painter):
    fig, axes = plt.subplots(3, 3, figsize=(14, 13), layout="constrained")
    for i, family in enumerate(f for f in FEATURE_SETS if f != "all31"):
        fit, points = projection(data, painter, family)
        for j, method in enumerate(METHOD_IDS):
            ax = axes[i, j]
            scatter(ax, fit, points, method, ALIASES)
            ax.set_title(f"{LABELS[family]} | {METHOD_LABELS[method]}")
            if j == 0:
                ax.legend(fontsize=7, loc="upper right", framealpha=0.8)
    fig.suptitle(
        f"{SHORT_LABELS[painter]}: feature-family views | balanced joint PCA\n"
        "Common axes within each row; gray originals, blue gpt-image-1, orange gpt-image-2"
    )
    return fig


def overview(data):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout="constrained")
    for ax, painter in zip(axes.flat, PAINTER_IDS):
        fit, points = projection(data, painter, "all31")
        scatter(ax, fit, points, "by_name", ALIASES)
        ax.set_title(SHORT_LABELS[painter], fontweight="bold")
        ax.legend(fontsize=8, loc="upper right", framealpha=0.8)
    fig.suptitle(
        "Original paintings vs artist-name generations\n"
        "All 31 features; balanced joint PCA fitted separately for each painter"
    )
    return fig


def heatmap(data):
    cells = [(p, a, m) for p in PAINTER_IDS for a in ALIASES for m in METHOD_IDS]
    columns = [(f, k) for f in FEATURE_SETS for k in ("linear", "rbf")]
    lookup = {
        (r["painter_id"], r["alias"], r["method_id"], r["family"], r["classifier"]): r[
            "balanced_accuracy"
        ]
        for r in data["separability"]
        if r["split"] == "scene"
    }
    values = np.array([[lookup[(*cell, *column)] for column in columns] for cell in cells])
    fig, ax = plt.subplots(figsize=(12, 12), layout="constrained")
    graphic = ax.imshow(values, vmin=0, vmax=1, cmap="RdBu", aspect="auto")
    for i, j in np.ndindex(values.shape):
        ax.text(
            j,
            i,
            f"{values[i, j]:.2f}",
            ha="center",
            va="center",
            fontsize=9,
            color="white" if values[i, j] > 0.82 or values[i, j] < 0.18 else "black",
        )
    ax.set_xticks(
        range(len(columns)),
        [f"{LABELS[f]}\n{k.upper()}" for f, k in columns],
        rotation=30,
        ha="right",
    )
    ax.set_yticks(
        range(len(cells)),
        [f"{SHORT_LABELS[p]} | {a[-1]} | {METHOD_LABELS[m]}" for p, a, m in cells],
    )
    for boundary in (5.5, 11.5, 17.5):
        ax.axhline(boundary, color="white", linewidth=2)
    fig.colorbar(graphic, ax=ax, label="Out-of-fold balanced accuracy (chance reference 0.50)")
    ax.set_title(
        "Can the original feature space distinguish originals from generations?\n"
        "Held-out generated scenes and original works; descriptive scores, no p-values",
        pad=16,
    )
    return fig


def markdown(data):
    full = [r for r in data["separability"] if r["family"] == "all31"]
    lookup = {
        (r["painter_id"], r["alias"], r["method_id"], r["split"], r["classifier"]): r for r in full
    }
    rows = []
    for p in PAINTER_IDS:
        for a in ALIASES:
            scores = [
                lookup[p, a, "by_name", split, kind]["balanced_accuracy"]
                for split, kind in (("scene", "linear"), ("scene", "rbf"), ("block", "rbf"))
            ]
            rows.append([SHORT_LABELS[p], a, *[f"{s:.3f}" for s in scores]])
    scenes = [r for r in full if r["split"] == "scene"]
    ranges = []
    for kind in ("linear", "rbf"):
        vals = [r["balanced_accuracy"] for r in scenes if r["classifier"] == kind]
        ranges.append(
            f"{kind.upper()}: {min(vals):.3f}–{max(vals):.3f}, median {np.median(vals):.3f}"
        )
    variance_ratios = [
        r["generated_to_original_variance_ratio"] for r in data["spread"] if r["family"] == "all31"
    ]
    projected_variance = [
        sum(r["explained_variance_ratio"])
        for r in data["projections"]
        if r["family"] == "all31" and r["basis"] == "balanced_joint"
    ]
    text = [
        "# Original versus generated painter-feature distributions",
        "Post-hoc exploration of existing measurements, 2026-09-06. No new images or features.",
        "## Main observations",
        "The scatter plots show overlapping point clouds with differences in location and "
        "concentration. In the by-name overview, Monet generations form a compact band within "
        "a broader original cloud; Sisley is shifted upward, Pissarro downward/rightward, and "
        "Cézanne leftward in their respective plotted axes. These directions belong to these "
        "PCA bases, not to intrinsic artistic dimensions. The plots do not show perfectly "
        "disjoint groups.",
        f"The first two PCs retain {min(projected_variance):.1%}–"
        f"{max(projected_variance):.1%} of balanced all-31 variance. Most variation is therefore "
        "outside the displayed plane; full-space discrimination is needed to complement the view.",
        f"Across the 24 all-31 cells, generated/original total within-group variance ratios "
        f"range from {min(variance_ratios):.3f} to {max(variance_ratios):.3f} "
        f"(median {np.median(variance_ratios):.3f}). This separately centered sum of sample "
        "variances quantifies spread in the original standardized feature space, rather than "
        "inferring spread from unequal point counts or two-dimensional plot ranges. It remains "
        "outlier-sensitive and does not establish reduced artistic diversity.",
        "The all-31, held-out-scene balanced accuracy across all 24 alias/painter/method cells is "
        + "; ".join(ranges)
        + ". These are descriptive scores, not significance tests.",
        _table(["Painter", "Service alias", "Scene: linear", "Scene: RBF", "Block: RBF"], rows),
        "The table uses **by-name** prompts only. Both classifiers and all methods/families are "
        "retained in `separability.csv` and the overview heatmap. A balanced accuracy of 0.5 is "
        "the chance reference; 1 means every held-out image was classified correctly. "
        "Below-chance values are reported without reversing scores. AUC and class-specific "
        "recall/specificity are also exported.",
        "![By-name overview](plots/by_name_overview.png)",
        "Each point is one image. Gray circles: originals; blue triangles: gpt-image-1; "
        "orange squares: gpt-image-2. Black rings mark the two later retry outputs. "
        "All points and outliers are retained. Axes show the two explained-variance fractions, "
        "and each painter uses its own PCA basis. White space is retained to preserve equal "
        "geometric scaling. Dense overlap may hide points; exact coordinates are exported.",
        "## How to interpret separation",
        "Energy distance already compares feature distributions, rather than only mean vectors. "
        "This analysis adds visible structure and out-of-fold discrimination. PCA optimizes "
        "variance, not class separation: overlap in two PCs does not establish equality in "
        "31 dimensions. High full-space discrimination supports a detectable dataset difference; "
        "it does not establish non-overlapping populations or isolate artistic style.",
        "Reference capture, color profiles, resolution, subject/composition and service processing "
        "can drive separation. Original works and generated scenes are not content-matched "
        "pairs. Aliases are not attested model snapshots. These references were already exposed; "
        "the analysis is exploratory, with no new confidence intervals, p-values, equivalence "
        "margin or aesthetic ranking. A fresh independent work/capture and service-session study "
        "would be needed for stronger population claims.",
        "![Separability](plots/separability.png)",
        "## Fixed analysis choices",
        "649 originals (Monet 297, Sisley 106, Pissarro 141, Cézanne 105), and 1,536 named-painter "
        "generations: two aliases × three methods × four painters × 64 images. The 384 "
        "artist-free images are excluded from this specific comparison. All 1,920 generated "
        "measurements were validated before selection. No source evidence was modified.",
        "The original 221-work median/IQR scaler is reused. PCA balances total original and "
        "generated mass 50/50, with equal mass for the six generated groups. Every panel for "
        "one painter/feature set shares its basis and limits. Original-only PCA is also shown "
        "for all 31 features as a projection sensitivity. No classifier uses plotted PCs.",
        "Linear and RBF kernel ridge classifiers have fixed regularization 0.01 and equal "
        "training-class weights. Primary validation holds out one complete generated scene "
        "and a disjoint fold of original works (16 folds). The all-31 sensitivity instead "
        "holds out one nominal generation block (four folds). These splits address different "
        "dependencies; neither is an independent-session or source-held-out validation. The "
        "later retries retain original scene labels; their nominal block labels do not denote "
        "their actual generation time. No classifier or parameter was selected by best score.",
        "See [the exact methods](../../studies/painter_distribution_exploration_v1/METHODS.md). "
        "Background: [PCA](https://scikit-learn.org/stable/modules/decomposition.html#pca), "
        "[kernel ridge](https://scikit-learn.org/stable/modules/kernel_ridge.html), and "
        "[grouped validation](https://scikit-learn.org/stable/modules/cross_validation.html).",
        "## Painter-specific scatter plots",
    ]
    for p in PAINTER_IDS:
        text.extend(
            [
                f"### {SHORT_LABELS[p]}",
                f"![All 31 features](plots/{p}_all31.png)",
                f"![Feature families](plots/{p}_families.png)",
                f"[Original-only PCA sensitivity](plots/{p}_original_only.png) · "
                f"[Vector all-31 figure](plots/{p}_all31.svg)",
            ]
        )
    text.extend(
        [
            "## Reproduction and exported records",
            "```bash\nuv run --locked --extra analysis --extra learned python -m "
            "latent_art_bench.painter_distribution_exploration_v1.report check\n```",
            "`build` creates a new bundle without overwriting. `check` verifies input/output "
            "hashes against their recorded implementation commit and recomputes all tables and "
            "PNG/SVG figures. `--output` selects a different new directory inside the repository. "
            "Plotting and replay operate on numeric records only.",
            "- `projections.json`: 20 bases, centers, loadings and explained variance.\n"
            "- `points.csv`: 10,925 point coordinates and source identities; originals stored once "
            "per basis, although drawn in multiple panels.\n"
            "- `separability.csv`: 240 classifier/feature/split results.\n"
            "- `spread.csv`: 96 within-group variance comparisons.\n"
            "- `predictions.csv`: 10,860 all-31 out-of-fold scores and retry provenance.\n"
            "- `provenance.json`: consumed inputs, implementation commit and output hashes.\n"
            "- `plots/`: 14 figures, each in PNG and SVG.",
            "No subagent or external independent review was performed for this exploration.",
        ]
    )
    return "\n\n".join(text) + "\n"


def render(data, target):
    target.mkdir(parents=True, exist_ok=False)
    (target / "plots").mkdir()
    for name in ("points", "separability", "predictions", "spread"):
        (target / f"{name}.csv").write_text(_csv(data[name]), encoding="utf-8")
    write_json(target / "projections.json", data["projections"])
    (target / "REPORT.md").write_text(markdown(data), encoding="utf-8")
    with plt.rc_context({**STYLE, "svg.hashsalt": NAMESPACE}):
        save(overview(data), target, "by_name_overview")
        save(heatmap(data), target, "separability")
        for painter in PAINTER_IDS:
            save(painter_figure(data, painter, "balanced_joint"), target, f"{painter}_all31")
            save(painter_figure(data, painter, "original_only"), target, f"{painter}_original_only")
            save(family_figure(data, painter), target, f"{painter}_families")


def implementation_paths(root):
    return [
        METHODS,
        Path("pyproject.toml"),
        Path("uv.lock"),
        *[p.relative_to(root) for p in (root / PACKAGE).glob("*.py")],
        *[p.relative_to(root) for p in (root / "tests" / NAMESPACE).glob("*.py")],
    ]


def build(root, output=OUTPUT):
    target = root / output
    target.resolve().relative_to(root.resolve())
    if target.exists():
        raise FileExistsError("report is immutable; choose a new output directory")
    painters, inputs = load(root)
    inputs = bindings(root, [Path(r["path"]) for r in inputs] + implementation_paths(root))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    _verify_commit(root, commit, inputs)
    data = compute(painters)
    render(data, target)
    outputs = bindings(root, [p.relative_to(root) for p in target.rglob("*") if p.is_file()])
    write_json(
        target / "provenance.json",
        dict(
            schema_version="painter-distribution-exploration/1.0",
            recorded_git_commit=commit,
            inputs=inputs,
            outputs=outputs,
            interpretation="post-hoc descriptive exploration",
            new_images=0,
            new_feature_extraction=False,
        ),
    )
    return dict(status="published", report=str(output / "REPORT.md"), files=len(outputs) + 1)


def check(root, output=OUTPUT):
    target = root / output
    receipt = read_json(target / "provenance.json")
    verify_bindings(root, receipt["inputs"])
    verify_bindings(root, receipt["outputs"])
    _verify_commit(root, receipt["recorded_git_commit"], receipt["inputs"])
    painters, _ = load(root)
    with tempfile.TemporaryDirectory() as temporary:
        fresh = Path(temporary) / "report"
        render(compute(painters), fresh)
        expected = {p.relative_to(fresh) for p in fresh.rglob("*") if p.is_file()}
        actual = {
            p.relative_to(target)
            for p in target.rglob("*")
            if p.is_file() and p.name != "provenance.json"
        }
        if expected != actual or any(
            (fresh / p).read_bytes() != (target / p).read_bytes() for p in expected
        ):
            raise ValueError("numerical or figure reproduction differs")
    return dict(status="PASS", report_files=len(expected) + 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(globals()[args.command](Path.cwd().resolve(), args.output), indent=2))


if __name__ == "__main__":
    main()
