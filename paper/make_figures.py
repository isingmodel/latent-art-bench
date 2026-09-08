"""Render manuscript figures from hash-checked, sealed presentation tables.

Run from the repository root with ``uv run --locked --extra analysis python
paper/make_figures.py``. Add ``--check`` for
byte replay or ``--preview-dir tmp/paper/preview`` for temporary PNGs.
No images/features are opened, no PCA is fitted, and no statistic is recomputed:
all plotted endpoints, component ratios and coordinates are extracted as saved.
The source hashes below deliberately reject changes to the underlying evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "figures"
REVISION = "reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/"
CONTROLLED = "reports/painter_distribution_study_v1/pdsv1-analysis-20260907/"
RESPONSIVENESS = "reports/painter_responsiveness_v2/"
SOURCES = {
    REVISION + "metric_cells.csv":
        "2cef4ce86a8201691963329e46c6e0a014c5c9c1d215e3c5c73bcfd2bdf05a06",
    REVISION + "prompt_contrasts.csv":
        "a045602d1192f0fc13df7eb61774e9ebcd6562ffcd955d5dcd58eab25b9ffc5a",
    CONTROLLED + "projection_points.csv":
        "22c983e36decd4031549124bc2114512a1c0e23a7875909c2526d861913481cf",
    RESPONSIVENESS + "prv2-oauth-20260908/diagnostics/retrieval_comparisons.csv":
        "8c5b8d25f20e8b48864ebc35f498d4227f3eec3e9a26b31274c3d6520065f0af",
    RESPONSIVENESS + "prv2-oauth-recovery-20260908/experiment/arm_means.csv":
        "e88efd4d1266650db11632d7b9e5f779a34bda624787eb6f8711d39af5cc00b0",
    RESPONSIVENESS + "prv2-oauth-recovery-20260908/experiment/primary.csv":
        "6476d8f24e36eae1b5357811a8971a5510ad9f620acd577ce49565b0c7db1d80",
}
PAINTERS = {"claude_monet": "Monet", "paul_cezanne": "Cézanne"}
ROUTES = {"nano_banana_2": "NB2", "flux_2_max": "FLUX", "oauth_gpt_image_2": "OAuth"}
ROUTE_TITLES = ("Nano Banana 2", "FLUX.2 Max", "OAuth service")
GROUPS = [(p, r) for p in PAINTERS for r in ROUTES]
LABELS = [f"{PAINTERS[p]} · {ROUTES[r]}" for p, r in GROUPS]
Y = [6, 5, 4, 2, 1, 0]
BLUE, ORANGE, PURPLE, INK = "#0072B2", "#D55E00", "#8D5AA0", "#252525"
PDF_METADATA = {"Creator": "Matplotlib", "CreationDate": None, "ModDate": None}


def read_tables():
    tables = {}
    for relative, expected in SOURCES.items():
        raw = (ROOT / relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"sealed figure input changed: {relative}")
        tables[Path(relative).name] = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
    return tables


def style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.2, "axes.labelsize": 8.2,
        "axes.titlesize": 9, "xtick.labelsize": 7.5, "ytick.labelsize": 8.2,
        "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0,
        "pdf.fonttype": 42, "pdf.compression": 6, "savefig.facecolor": "white",
    })


def row_axis(ax, labels=True):
    ax.set_yticks(Y, LABELS if labels else [""] * len(Y))
    ax.set_ylim(-0.6, 6.7)
    ax.axhline(3, color="#dedede", linewidth=0.6)
    ax.grid(axis="x", color="#ececec", linewidth=0.6)
    ax.set_axisbelow(True)


def primary_comparison(tables):
    selected = [r for r in tables["metric_cells.csv"]
                if r["pipeline"] == "primary512" and r["metric_view"] == "original31"
                and r["condition"] in ("artist_free", "named")]
    cells = {(r["painter_id"], r["route"], r["condition"]): r for r in selected}
    if len(cells) != 12:
        raise ValueError("primary figure requires exactly twelve named/free cells")
    fig, axes = plt.subplots(1, 2, figsize=(160 / 25.4, 3.1))
    for panel, (ax, field, title) in enumerate(zip(
        axes, ("energy", "trace_ratio"), ("(a) Energy discrepancy", "(b) Total trace"),
    )):
        row_axis(ax, labels=panel == 0)
        for y, (painter, route) in zip(Y, GROUPS):
            free, named = [float(cells[painter, route, c][field])
                           for c in ("artist_free", "named")]
            ax.plot([free, named], [y, y], color="#a0a0a0", linewidth=1.1, zorder=2)
            ax.scatter(free, y, color=BLUE, marker="o", s=25, zorder=3)
            ax.scatter(named, y, color=ORANGE, marker="D", s=25, zorder=4)
        ax.set_title(title, loc="left", pad=8)
        ax.set_xlim(0, 5.0 if panel == 0 else 1.65)
        ax.set_xlabel("Energy discrepancy" if panel == 0 else "Generated / reference trace")
        if panel == 1:
            ax.axvline(1, color="#777777", linewidth=0.8, linestyle=(0, (3, 3)), zorder=1)
    fig.legend(handles=[
        Line2D([], [], color=BLUE, marker="o", linestyle="", label="Artist-free", markersize=5),
        Line2D([], [], color=ORANGE, marker="D", linestyle="", label="Named", markersize=5),
    ], loc="upper center", bbox_to_anchor=(0.61, 1), ncol=2, frameon=False)
    fig.subplots_adjust(left=0.215, right=0.985, bottom=0.17, top=0.81, wspace=0.17)
    return fig


def variation_ratios(tables):
    rows = [r for r in tables["prompt_contrasts.csv"]
            if r["pipeline"] == "primary512" and r["metric_view"] == "original31"]
    cells = {(r["painter_id"], r["route"]): r for r in rows}
    if len(cells) != 6:
        raise ValueError("variation figure requires exactly six named/free contrasts")
    fig, ax = plt.subplots(figsize=(160 / 25.4, 3.0))
    row_axis(ax)
    for field, label, color, marker, offset in (
        ("total_trace", "Total", INK, "D", 0.17),
        ("within_brief", "Within descriptions", ORANGE, "o", 0),
        ("between_brief_means", "Between descriptions", BLUE, "s", -0.17),
    ):
        x = [float(cells[g]["generated_decomposition_ratios." + field]) for g in GROUPS]
        ax.scatter(x, [y + offset for y in Y], color=color, marker=marker, s=25, label=label,
                   zorder=3)
    ax.axvline(1, color="#777777", linewidth=0.8, linestyle=(0, (3, 3)))
    ax.set_xlim(0.2, 1.22)
    ax.set_xlabel("Named / artist-free trace")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.035), ncol=3, frameon=False,
              columnspacing=1.8, handletextpad=0.5)
    fig.subplots_adjust(left=0.215, right=0.985, bottom=0.17, top=0.83)
    return fig


def common_pca(tables):
    rows = [r for r in tables["projection_points.csv"] if r["basis"] == "balanced_joint"]
    if len(rows) != 1076 or len({r["image_id"] for r in rows}) != 1076:
        raise ValueError("saved common projection requires all seventy originals and 1006 outputs")
    fig, axes = plt.subplots(2, 3, figsize=(160 / 25.4, 4.45), sharex="row", sharey="row")
    groups = (
        ("artist_free", "Artist-free", BLUE, "o", 11, 0.50),
        ("named", "Named", ORANGE, "s", 11, 0.58),
        ("generic_named", "Short-scene named", PURPLE, "^", 14, 0.58),
        ("original", "Originals", INK, "x", 18, 0.95),
    )
    for ri, painter in enumerate(PAINTERS):
        painter_rows = [r for r in rows if r["painter_id"] == painter]
        for ci, route in enumerate(ROUTES):
            ax = axes[ri, ci]
            for condition, _, color, marker, size, alpha in groups:
                chosen = [r for r in painter_rows if r["condition"] == condition
                          and (r["route"] == route or condition == "original")]
                if not chosen:
                    continue
                ax.scatter([float(r["pc1"]) for r in chosen],
                           [float(r["pc2"]) for r in chosen], c=color, marker=marker,
                           s=size, alpha=alpha, linewidths=0.65 if marker == "x" else 0)
            ax.axhline(0, color="#e7e7e7", linewidth=0.6, zorder=0)
            ax.axvline(0, color="#e7e7e7", linewidth=0.6, zorder=0)
            ax.set_xlabel("PC1", labelpad=2)
            if ci == 0:
                ax.set_ylabel(f"{PAINTERS[painter]}\nPC2", labelpad=3)
            if ri == 0:
                ax.set_title(ROUTE_TITLES[ci], pad=7)
            ax.tick_params(axis="both", labelsize=7, pad=2)
        for coord, setter in (("pc1", "set_xlim"), ("pc2", "set_ylim")):
            values = [float(r[coord]) for r in painter_rows]
            lo, hi = min(values), max(values)
            getattr(axes[ri, 0], setter)(lo - (hi - lo) * 0.06, hi + (hi - lo) * 0.06)
    handles = [Line2D([], [], color=color, marker=marker, linestyle="", markersize=4.5,
                      label=label) for _, label, color, marker, _, _ in groups]
    fig.legend(handles=[handles[3], *handles[:3]], loc="upper center", ncol=4,
               bbox_to_anchor=(0.54, 1), frameon=False, columnspacing=1.4, handletextpad=0.4)
    fig.subplots_adjust(left=0.105, right=0.99, top=0.855, bottom=0.105,
                        wspace=0.16, hspace=0.35)
    return fig


def scene_retrieval(tables):
    selected = [r for r in tables["retrieval_comparisons.csv"]
                if r["pipeline"] == "primary512" and r["view"] == "original31"
                and r["candidate_scope"] in ("all_briefs", "same_content")]
    cells = {(r["painter_id"], r["route"], r["candidate_scope"]): r for r in selected}
    if len(selected) != 12 or len(cells) != 12:
        raise ValueError("retrieval figure requires twelve primary named/free comparisons")
    fig, axes = plt.subplots(1, 2, figsize=(160 / 25.4, 3.1))
    for panel, (ax, scope, title) in enumerate(zip(
        axes, ("all_briefs", "same_content"),
        ("(a) All 24 scenes", "(b) Eight within-class scenes"),
    )):
        row_axis(ax, labels=panel == 0)
        chances = set()
        for y, (painter, route) in zip(Y, GROUPS):
            row = cells[painter, route, scope]
            if (row["before.queries"] != "72" or row["after.queries"] != "72"
                    or row["before.condition"] != "artist_free"
                    or row["after.condition"] != "named"
                    or row["before.chance_top1"] != row["after.chance_top1"]):
                raise ValueError("retrieval panel has inconsistent query or condition metadata")
            chances.add(float(row["before.chance_top1"]) * 100)
            free, named = [float(row[side + ".top1_accuracy"]) * 100
                           for side in ("before", "after")]
            ax.plot([free, named], [y, y], color="#a0a0a0", linewidth=1.1, zorder=2)
            ax.scatter(free, y, edgecolors=BLUE, facecolors="white", marker="o", s=31,
                       linewidths=1.0, zorder=3)
            ax.scatter(named, y, color=ORANGE, marker="D", s=18, zorder=4)
        if len(chances) != 1:
            raise ValueError("retrieval panel must share a single chance probability")
        ax.axvline(chances.pop(), color="#777777", linewidth=0.8, linestyle=(0, (2, 2)))
        ax.set(xlim=(-2, 102), xticks=(0, 25, 50, 75, 100), xlabel="Top-1 accuracy (%)")
        ax.set_title(title, loc="left", pad=8)
    fig.legend(handles=[
        Line2D([], [], color=BLUE, marker="o", markerfacecolor="white", linestyle="",
               label="Artist-free", markersize=5),
        Line2D([], [], color=ORANGE, marker="D", linestyle="", label="Named", markersize=4),
        Line2D([], [], color="#777777", linestyle=(0, (2, 2)), label="Chance", linewidth=0.8),
    ], loc="upper center", bbox_to_anchor=(0.60, 1), ncol=3, frameon=False,
               columnspacing=1.4, handletextpad=0.5)
    fig.subplots_adjust(left=0.215, right=0.985, bottom=0.17, top=0.81, wspace=0.17)
    return fig


def color_responsiveness(tables):
    arms = ("free", "generic", "monet", "cezanne")
    means = {(r["arm"], r["polarity"]): float(r["mean"]) for r in tables["arm_means.csv"]}
    primary = {r["contrast"]: r for r in tables["primary.csv"]}
    if (len(tables["arm_means.csv"]) != 8 or len(means) != 8
            or set(means) != {(a, p) for a in arms for p in ("muted", "vivid")}
            or len(tables["primary.csv"]) != 2
            or set(primary) != {"monet_minus_generic", "cezanne_minus_generic"}):
        raise ValueError("color figure requires eight arm means and two primary contrasts")
    fig, axes = plt.subplots(1, 2, figsize=(160 / 25.4, 2.9),
                             gridspec_kw={"width_ratios": (1.1, 1)})
    ax = axes[0]
    for i, arm in enumerate(arms):
        ax.plot([i - 0.12, i + 0.12], [means[arm, "muted"], means[arm, "vivid"]],
                color="#a0a0a0", linewidth=1.1, zorder=2)
    for polarity, color, marker, offset in (
        ("muted", BLUE, "o", -0.12), ("vivid", ORANGE, "D", 0.12),
    ):
        ax.scatter([i + offset for i in range(4)], [means[a, polarity] for a in arms],
                   color=color, marker=marker, s=28, label=polarity.capitalize(), zorder=3)
    ax.set(xticks=range(4), xticklabels=("Artist-\nfree", "Generic", "Monet", "Cézanne"),
           xlim=(-0.45, 3.45), ylim=(-1, 3.7), yticks=(-1, 0, 1, 2, 3),
           ylabel="Arm mean of median chroma\n(development IQR units)")
    ax.tick_params(axis="x", labelsize=7.3)
    ax.set_title("(a) Muted and vivid arm means", loc="left", pad=8)
    ax.legend(loc="upper left", bbox_to_anchor=(-0.12, 1.29), ncol=2, frameon=False,
              columnspacing=0.8, handletextpad=0.25)
    ax.grid(axis="y", color="#ececec", linewidth=0.6)
    ax.set_axisbelow(True)
    ax = axes[1]
    scene_offsets = (-0.24, -0.16, -0.08, 0.08, 0.16, 0.24)
    for y, arm in zip((1, 0), ("monet", "cezanne")):
        row = primary[arm + "_minus_generic"]
        interval = json.loads(row["family_interval"])
        scenes = json.loads(row["template_estimates"])
        if len(interval) != 2 or not interval[0] <= float(row["estimate"]) <= interval[1]:
            raise ValueError("primary interaction interval must bracket its saved estimate")
        if len(scenes) != len(scene_offsets):
            raise ValueError("primary interaction must retain all six saved scene estimates")
        ax.scatter(scenes, [y + offset for offset in scene_offsets], facecolors="white",
                   edgecolors="#7a7a7a", linewidths=0.8, s=16, zorder=2)
        ax.plot(interval, [y, y], color=BLUE, linewidth=1.3, zorder=2)
        ax.scatter(float(row["estimate"]), y, color=BLUE, s=27, zorder=3)
    ax.axvline(0, color="#777777", linewidth=0.8, linestyle=(0, (2, 2)), zorder=1)
    ax.set(yticks=(1, 0), yticklabels=("Monet", "Cézanne"), ylim=(-0.55, 1.55),
           xlim=(-0.85, 0.45), xticks=(-0.8, -0.4, 0, 0.4),
           xlabel="Named - generic response κ\n(development IQR units)")
    ax.set_title("(b) Scene estimates and mean", loc="left", pad=8)
    ax.legend(handles=[
        Line2D([], [], color="#7a7a7a", marker="o", markerfacecolor="white", linestyle="",
               label="Scene estimate", markersize=3.5),
        Line2D([], [], color=BLUE, marker="o", linewidth=1.3, markersize=4,
               label="Mean + 95% family CI"),
    ], loc="upper left", bbox_to_anchor=(-0.03, 1.4), frameon=False, fontsize=7.3,
              handletextpad=0.5, labelspacing=0.4)
    ax.grid(axis="x", color="#ececec", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.23, top=0.78, wspace=0.47)
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tables = read_tables()
    style()
    for maker in (primary_comparison, variation_ratios, common_pca,
                  scene_retrieval, color_responsiveness):
        fig = maker(tables)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="pdf", metadata=PDF_METADATA)
        destination = args.output_dir / (maker.__name__ + ".pdf")
        if args.check:
            if destination.read_bytes() != buffer.getvalue():
                raise ValueError(f"figure replay differs: {destination.name}")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(buffer.getvalue())
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True, exist_ok=True)
            fig.savefig(args.preview_dir / (maker.__name__ + ".png"), dpi=180)
        plt.close(fig)
        print(("verified " if args.check else "rendered ") + destination.name)


if __name__ == "__main__":
    main()
