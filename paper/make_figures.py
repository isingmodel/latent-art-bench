"""Render manuscript figures from three hash-checked, sealed presentation tables.

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
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "figures"
REVISION = "reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/"
CONTROLLED = "reports/painter_distribution_study_v1/pdsv1-analysis-20260907/"
SOURCES = {
    REVISION + "metric_cells.csv":
        "2cef4ce86a8201691963329e46c6e0a014c5c9c1d215e3c5c73bcfd2bdf05a06",
    REVISION + "prompt_contrasts.csv":
        "a045602d1192f0fc13df7eb61774e9ebcd6562ffcd955d5dcd58eab25b9ffc5a",
    CONTROLLED + "projection_points.csv":
        "22c983e36decd4031549124bc2114512a1c0e23a7875909c2526d861913481cf",
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
        ("generic_named", "Generic named", PURPLE, "^", 14, 0.58),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--preview-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    tables = read_tables()
    style()
    for maker in (primary_comparison, variation_ratios, common_pca):
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
