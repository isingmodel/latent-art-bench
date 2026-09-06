"""Render the sealed controlled analysis without selecting or changing its endpoints."""

from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    events,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import parallel_collection as p
from . import study as s

DIRECTORY = Path("reports") / "painter_distribution_study_v1" / p.RUN_ID
PAINTERS = dict(zip(s.PAINTERS, ("Monet", "Cézanne")))
ROUTES = dict(zip(s.ROUTES, ("Nano Banana 2", "FLUX.2 Max", "GPT Image 2 service")))
SHORT_ROUTES = dict(zip(s.ROUTES, ("Nano Banana 2", "FLUX.2 Max", "GPT Image 2*")))
CONDITIONS = dict(
    artist_free="Artist-free", named="Named, detailed", generic_named="Named, generic"
)
COLORS = dict(original="#333333", artist_free="#d87524", named="#187f91", generic_named="#92579c")
CELLS = [(route, condition) for route in s.ROUTES for condition in s.conditions(route)]
TABLES = (
    "cells",
    "endpoints",
    "sensitivity_contrasts",
    "baselines",
    "coverage",
    "classifiers",
    "specificity",
    "availability",
    "actual_slot_times",
    "transport_events",
)


def write_table(path, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, sort_keys=True, ensure_ascii=False)
                if isinstance(v, (dict, list))
                else v
                for k, v in row.items()
            }
            for row in rows
        )


def save(fig, output, name):
    fig.savefig(output / (name + ".png"), dpi=180, metadata={"Software": "LatentArtBench"})
    fig.savefig(output / (name + ".svg"), metadata={"Date": None, "Creator": "LatentArtBench"})
    plt.close(fig)


def primary_rows(data):
    return [
        r
        for r in data["cells"]
        if r["pipeline"] == "primary512"
        and r["feature_set"] == "all31"
        and r["weighting"] == "reference_content"
    ]


def metric_plot(data, output):
    metrics = [
        ("energy_distance", "Energy discrepancy"),
        ("population_variance_ratio", "Generated/original variance"),
        ("squared_iqr_sum_ratio", "Generated/original squared IQR sum"),
    ]
    fig, axes = plt.subplots(3, 2, figsize=(13, 10), layout="constrained")
    for j, painter in enumerate(s.PAINTERS):
        for i, (metric, title) in enumerate(metrics):
            ax = axes[i, j]
            for pipeline, label in zip(s.PIPELINES, ("Primary 512", "256 pixels", "Common JPEG")):
                lookup = {
                    (r["route"], r["condition"]): r
                    for r in data["cells"]
                    if r["painter_id"] == painter
                    and r["pipeline"] == pipeline
                    and r["weighting"] == "reference_content"
                    and r["feature_set"] == "all31"
                }
                yy = [lookup.get(k, {}).get(metric) for k in CELLS]
                ax.plot(
                    range(len(CELLS)),
                    [np.nan if y is None else y for y in yy],
                    marker="o",
                    markersize=4,
                    label=label,
                )
            if i:
                ax.axhline(1, color="gray", linewidth=0.8, linestyle="--")
            ax.set_title(f"{PAINTERS[painter]} · {title}")
            ax.set_xticks(
                range(len(CELLS)),
                [f"{SHORT_ROUTES[r]}\n{CONDITIONS[c]}" for r, c in CELLS],
                rotation=0,
                ha="center",
                fontsize=7,
            )
            ax.grid(axis="y", alpha=0.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        "Content-standardized distributions · all 31 features\n"
        "Descriptive estimates; development scaling per pipeline; *local service alias"
    )
    save(fig, output, "distribution_metrics")


def scatter_plot(data, output, basis):
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    for i, painter in enumerate(s.PAINTERS):
        projection = data["projections"].get(painter, {})
        if projection.get("status") != "available":
            for ax in axes[i]:
                ax.text(0.5, 0.5, "Projection unavailable", ha="center", transform=ax.transAxes)
            continue
        fitted = projection["bases"][basis]
        points = fitted["points"]
        xx, yy = np.array([r["pc1"] for r in points]), np.array([r["pc2"] for r in points])
        margins = (max(float(np.ptp(xx)), 1e-6) * 0.06, max(float(np.ptp(yy)), 1e-6) * 0.06)
        explained = fitted["fit"]["explained_variance_ratio"]
        for j, route in enumerate(s.ROUTES):
            ax = axes[i, j]
            for condition in (*s.conditions(route), "original"):
                selected = [
                    r
                    for r in points
                    if r["condition"] == condition
                    and (condition == "original" or r["route"] == route)
                ]
                ax.scatter(
                    [r["pc1"] for r in selected],
                    [r["pc2"] for r in selected],
                    s=20 if condition == "original" else 13,
                    marker="x" if condition == "original" else "o",
                    alpha=0.65,
                    color=COLORS[condition],
                    label="Original" if condition == "original" else CONDITIONS[condition],
                )
            ax.set(
                xlim=(xx.min() - margins[0], xx.max() + margins[0]),
                ylim=(yy.min() - margins[1], yy.max() + margins[1]),
                xlabel=f"PC1 ({explained[0]:.1%})",
                ylabel=f"PC2 ({explained[1]:.1%})",
                title=f"{PAINTERS[painter]} · {ROUTES[route]}",
            )
            ax.legend(fontsize=7)
    fig.suptitle(
        f"Original and generated distributions · {basis.replace('_', ' ')} PCA\n"
        "Every point retained; common basis and limits within painter; "
        "no inference from visual overlap"
    )
    save(fig, output, "pca_" + basis)


def endpoint_plot(data, output):
    fig, ax = plt.subplots(figsize=(11, 6), layout="constrained")
    labels = []
    for i, row in enumerate(data["endpoints"]):
        labels.append(
            f"{PAINTERS[row['painter_id']]} · {ROUTES[row['route']]}\n"
            f"{CONDITIONS[row['before']]} → {CONDITIONS[row['after']]}"
        )
        estimate = row.get("estimate")
        if estimate is None:
            ax.text(0, i, "Unavailable", fontsize=8)
            continue
        reduced = [
            r["estimate"]
            for r in data["sensitivity_contrasts"]
            if r["endpoint_index"] == row["endpoint_index"]
            and r["excluded_kind"] == "window"
            and r["estimate"] is not None
        ]
        if reduced:
            ax.hlines(i, min(reduced), max(reduced), color="#187f91", linewidth=3)
        ax.plot(estimate, i, "o", color="#222222")
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.set_ylim(len(labels) - 0.5, -0.5)
    ax.set_xlabel("After-minus-before energy discrepancy (negative means closer)")
    ax.set_title(
        "Paired prompt contrasts\n"
        "Dots: complete-pair estimates; lines: leave-one-window range, NOT confidence intervals"
    )
    save(fig, output, "prompt_contrasts")


def baseline_plot(data, output):
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), layout="constrained")
    for ax, painter in zip(axes, s.PAINTERS):
        labels = []
        for i, (route, condition) in enumerate(CELLS):
            labels.append(f"{SHORT_ROUTES[route]}\n{CONDITIONS[condition]}")
            row = next(
                (
                    r
                    for r in data["baselines"]
                    if r["painter_id"] == painter
                    and r["route"] == route
                    and r["condition"] == condition
                ),
                {},
            )
            if row.get("status") != "available":
                continue
            for offset, key, color in [
                (-0.17, "real_real_energy", "#777777"),
                (0.17, "original_generated_energy", "#187f91"),
            ]:
                q = np.quantile(row[key], [0.05, 0.5, 0.95])
                ax.vlines(i + offset, q[0], q[2], color=color, linewidth=2)
                ax.plot(i + offset, q[1], "o", color=color, markersize=4)
        ax.set_xticks(range(len(CELLS)), labels, rotation=0, ha="center", fontsize=8)
        ax.set(title=PAINTERS[painter], ylabel="Energy discrepancy")
    fig.suptitle(
        "Matched finite-reference subsamples\n"
        "Gray: original/original; teal: original/generated\n"
        "Median and 5th–95th percentiles, NOT confidence intervals"
    )
    save(fig, output, "matched_baselines")


def number(value):
    return "unavailable" if value is None else f"{value:.4f}"


def markdown(data):
    accounting = data["generation_accounting"]
    budget = accounting["budget"]
    lines = [
        "# Controlled painter-distribution results",
        "",
        f"Execution: `{p.RUN_ID}`; status **{accounting['status']}**. "
        f"Terminal slots: {accounting['terminal_slots']}/1,008. "
        f"Dispositions: `{json.dumps(accounting['dispositions'], sort_keys=True)}`.",
        "",
        f"Total study accounting including pilot and retries: ${budget['accounted_usd']:.7f}; "
        f"{budget['attempts']} attempts, {budget['paid_attempts']} paid. "
        f"Unresolved intents: {budget['unresolved']}; uncertain charges: {budget['uncertain']}.",
        "",
        "Three concurrent route workers use at most one call per route, with globally "
        "recorded starts at least five seconds apart. Actual timing and availability remain "
        "part of the evidence. GPT Image 2 is a local service alias, not an attested snapshot.",
        "",
        "The primary comparison uses all 31 features, the fixed historical development "
        "scaler, and generated content masses matched to each finite reference panel. "
        "Original works receive equal weight. These are distribution comparisons, not "
        "distances solely to an artist mean. Energy, spread, coverage and detection are "
        "descriptive; they do not establish aesthetic quality or oeuvre equivalence.",
        "",
        "## Primary distribution comparisons",
        "",
        "| Painter | Route | Condition | Original / generated | Energy | "
        "Variance ratio | Squared IQR sum ratio |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in primary_rows(data):
        lines.append(
            f"| {PAINTERS[r['painter_id']]} | {ROUTES[r['route']]} | "
            f"{CONDITIONS[r['condition']]} | "
            f"{r.get('n_original', '—')} / {r.get('n_generated', '—')} | "
            f"{number(r.get('energy_distance'))} | {number(r.get('population_variance_ratio'))} | "
            f"{number(r.get('squared_iqr_sum_ratio'))} |"
        )
    lines += [
        "",
        "![Distribution metrics](distribution_metrics.png)",
        "",
        "Each processing sensitivity has its own scaler fitted to the same 221 development "
        "works. Comparisons across pipelines assess processing sensitivity, not calibrated "
        "aesthetic change. Family and content-weighting sensitivities are retained in `cells.csv`.",
        "",
        "## Scatter plots and distribution diagnostics",
        "",
        "![Common PCA](pca_balanced_joint.png)",
        "",
        "![Original-only PCA](pca_original_only.png)",
        "",
        "Every image is retained. PCA is fitted once per painter with half the weight on "
        "originals and half shared across seven generated cells; the original-only basis "
        "is a projection sensitivity. The classifiers operate on full features and hold "
        "out entire briefs or windows and disjoint original works. `classifiers.csv` "
        "retains scores, predictions and split membership. "
        "Separability alone does not isolate style.",
        "",
        "![Matched baselines](matched_baselines.png)",
        "",
        "Subsample ranges reflect resampling of this finite collection, not population "
        "confidence intervals. `coverage.csv` retains k=3 original-neighborhood coverage "
        "for all available images and equal-size generated subsets. `specificity.csv` "
        "compares named outputs against both painters under equal content masses.",
        "",
        "## Paired prompt contrasts",
        "",
        "| Painter | Route | Before → after | Pairs | Energy change | Raw p | Holm p |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in data["endpoints"]:
        lines.append(
            f"| {PAINTERS[r['painter_id']]} | {ROUTES[r['route']]} | "
            f"{CONDITIONS[r['before']]} → {CONDITIONS[r['after']]} | {r['pairs']} | "
            f"{number(r.get('estimate'))} | {number(r['raw_p'])} | {number(r['holm_p'])} |"
        )
    lines += [
        "",
        "![Prompt contrasts](prompt_contrasts.png)",
        "",
        "Negative change means the after condition is closer on the matched measured pairs. "
        "Eight prospectively fixed endpoints use 99,999 Monte Carlo sign draws and Holm "
        "adjustment. The conditional sharp null concerns availability and features under "
        "the fixed slot/retry policy, with no interference. Shared service state and concurrent "
        "gateway traffic can violate that assumption. Unavailable endpoints remain in the "
        "family with p=1. Leave-window and leave-brief ranges are descriptive, "
        "not confidence intervals.",
        "",
        "## Scope and reproduction",
        "",
        "The reference panel has 38 Monet and 32 Cézanne works. Its visual content coding "
        "was performed by one maintainer LLM, not independent human experts. Digital "
        "capture, encoding, residual composition and service identity remain possible "
        "explanations. No human assessment or learned-feature validation is claimed.",
        "",
        "Full-precision tables retain unavailable rows, excluded pairs, coefficients, "
        "classification membership and subsample draws. Frozen scientific and execution "
        "inputs, raw-response hashes and terminal receipts remain "
        "under the study manifest directory.",
        "",
        "```bash",
        "uv run --locked --extra analysis python -m "
        "latent_art_bench.painter_distribution_study_v1.parallel_results analysis --check",
        "uv run --locked --extra analysis python -m "
        "latent_art_bench.painter_distribution_study_v1.main_report check",
        "```",
        "",
    ]
    return "\n".join(lines)


def render(data, output):
    output.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "svg.hashsalt": "pdsv1-controlled-report",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    ):
        for name in TABLES:
            write_table(output / (name + ".csv"), data[name])
        points = [
            dict(painter_id=painter, basis=basis, **row)
            for painter, projection in data["projections"].items()
            for basis, fitted in projection.get("bases", {}).items()
            for row in fitted["points"]
        ]
        write_table(output / "projection_points.csv", points)
        metric_plot(data, output)
        for basis in ("balanced_joint", "original_only"):
            scatter_plot(data, output, basis)
        endpoint_plot(data, output)
        baseline_plot(data, output)
        (output / "REPORT.md").write_text(markdown(data))


def run(root, *, check=False):
    p.verify(root)
    analysis_path = p.DIRECTORY / "analysis.json"
    source_receipt = read_json(root / p.DIRECTORY / "analysis_receipt.json")
    verify_bindings(root, source_receipt["inputs"])
    if hash_file(root / analysis_path) != source_receipt["analysis_sha256"]:
        raise ValueError("analysis differs from its receipt")
    data = read_json(root / analysis_path)
    verify_bindings(root, data["generation_accounting"]["outputs"])
    data["transport_events"] = [
        dict(run_id=Path(bound["path"]).parent.name, **row)
        for bound in data["generation_accounting"]["outputs"]
        if Path(bound["path"]).name == "generation_events.jsonl"
        for row in events(root / bound["path"])
    ]
    output = root / DIRECTORY
    if check:
        receipt = read_json(output / "provenance.json")
        verify_bindings(root, receipt["inputs"])
        verify_bindings(root, receipt["outputs"])
        with tempfile.TemporaryDirectory(prefix="pdsv1-report-") as directory:
            replay = Path(directory)
            render(data, replay)
            for path in replay.iterdir():
                if hash_file(path) != hash_file(output / path.name):
                    raise ValueError(f"report replay differs: {path.name}")
        return dict(status="verified", files=len(receipt["outputs"]))
    if output.exists():
        raise ValueError("report already exists; never overwrite a published bundle")
    paths = [
        s.PACKAGE / "main_report.py",
        Path("tests") / "painter_distribution_study_v1" / "test_main_report.py",
        analysis_path,
        p.DIRECTORY / "analysis_receipt.json",
    ]
    commit = committed(root, paths)
    render(data, output)
    publish(
        output / "provenance.json",
        dict(
            recorded_git_commit=commit,
            inputs=bindings(root, paths),
            outputs=bindings(root, [f.relative_to(root) for f in sorted(output.iterdir())]),
        ),
    )
    return dict(status="built", output=DIRECTORY.as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    print(json.dumps(run(Path.cwd(), check=parser.parse_args().command == "check"), indent=2))


if __name__ == "__main__":
    main()
