"""Render artist-specificity results from the terminal, verified numerical inputs.

The artist-contrast projection is a descriptive reference-centroid SVD, with
fixed orientation. Inference always uses all 31 coordinates. This presentation
script does not acquire images, fit an evaluator or change the frozen analysis.
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from matplotlib.patheffects import Normal, Stroke  # noqa: E402

from latent_art_bench.painter_specificity_measurement_v1.workflow import load  # noqa: E402
from latent_art_bench.painter_specificity_v1.analysis import centered  # noqa: E402
from latent_art_bench.painter_specificity_v2 import study as s  # noqa: E402

OUT = Path(__file__).parent / "figures"
COLORS = ("#0072B2", "#E69F00", "#009E73", "#CC79A7")
PAINTERS = ("Monet", "Sisley", "Pissarro", "Cézanne")
SHORT = ("GPT Image 1", "GPT Image 2", "2.5 Flare", "2.5 Sunburst", "Nano Banana 2", "FLUX.2 Max")
META = {"Creator": "Matplotlib", "CreationDate": None, "ModDate": None}


def style():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9,
            "legend.fontsize": 7.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )


def comparison(result):
    fig, axes = plt.subplots(1, 2, figsize=(6.45, 3.0), sharey=True)
    for m, row in enumerate(result["models"]):
        y = 5 - m
        for ax, metric, key in zip(axes, ("beta", "distortion"), ("simultaneous_ci", "ci95")):
            cell = row[metric]
            if cell["mean"] is None:
                continue
            ax.scatter(cell["mean"], y, color="#0072B2", s=24, zorder=3)
            if cell["available"]:
                ax.plot(cell[key], [y, y], color="#0072B2", lw=1.1)
    axes[0].set_yticks(range(6), SHORT[::-1])
    for ax in axes:
        ax.grid(axis="x", color="#e5e5e5", lw=0.6)
        ax.set_axisbelow(True)
        ax.axvline(0, color="#888888", lw=0.7)
        ax.axvline(1, color="#888888", lw=0.7, linestyle="--")
        ax.set_ylim(-0.6, 5.6)
    axes[0].set(xlabel="Reference-aligned slope β", title="(a) Artist response")
    axes[1].set(xlabel="Corrected error D", title="(b) Reference-contrast mismatch")
    fig.subplots_adjust(left=0.19, right=0.985, bottom=0.19, top=0.87, wspace=0.2)
    return fig


def artist_geometry(x, refs):
    r = centered(np.array([a.mean(axis=0) for a in refs]))
    _, singular, vt = np.linalg.svd(r, full_matrices=False)
    basis = vt[:2].T
    for j in range(2):
        if basis[np.argmax(abs(basis[:, j])), j] < 0:
            basis[:, j] *= -1
    target = r @ basis
    d = centered(x[:, :, :, 2:]) @ basis
    for m in range(6):
        complete = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
        d[m, ~complete] = np.nan
    values = np.concatenate([d.reshape(-1, 2), target])
    lo, hi = np.nanmin(values, axis=0), np.nanmax(values, axis=0)
    pad = (hi - lo) * 0.09
    means = np.full((6, 4, 2), np.nan)
    for m in range(6):
        for a in range(4):
            cloud = d[m, :, :, a].reshape(-1, 2)
            good = np.isfinite(cloud).all(axis=1)
            if good.any():
                means[m, a] = cloud[good].mean(axis=0)
    detail_points = np.concatenate([means[:, :3].reshape(-1, 2), target[:3]])
    detail_lo = np.nanmin(detail_points, axis=0) - 0.16
    detail_hi = np.nanmax(detail_points, axis=0) + 0.16
    fig = plt.figure(figsize=(6.45, 4.4))
    grid = fig.add_gridspec(
        2, 3, left=0.09, right=0.94, bottom=0.10, top=0.88, wspace=0.08, hspace=0.28
    )
    for m in range(6):
        cell = grid[m // 3, m % 3]
        pair = cell.subgridspec(1, 2, width_ratios=(1.4, 1), wspace=0.08)
        ax = fig.add_subplot(pair[0])
        detail = fig.add_subplot(pair[1])
        ax.set_gid(f"overview-{m}")
        detail.set_gid(f"centroid-detail-{m}")
        for a, color in enumerate(COLORS):
            cloud = d[m, :, :, a].reshape(-1, 2)
            good = np.isfinite(cloud).all(axis=1)
            if good.any():
                ax.scatter(*cloud[good].T, color=color, alpha=0.13, s=10, linewidths=0, zorder=1)
                mean = means[m, a]
                ax.plot(
                    [target[a, 0], mean[0]], [target[a, 1], mean[1]], color=color, lw=0.8, zorder=2
                )
                ax.scatter(
                    *mean,
                    s=70,
                    marker="o",
                    facecolors="white",
                    edgecolors=color,
                    linewidths=1.4,
                    zorder=4,
                )
            ax.scatter(
                *target[a],
                color=color,
                s=50,
                marker="X",
                edgecolors="#333333",
                linewidths=0.5,
                zorder=5,
            )
            if a < 3:
                mean = means[m, a]
                detail.plot(
                    [target[a, 0], mean[0]],
                    [target[a, 1], mean[1]],
                    color=color,
                    lw=1.3,
                    path_effects=[Stroke(linewidth=2.7, foreground="white"), Normal()],
                    zorder=2,
                )
                detail.scatter(
                    *mean,
                    s=58,
                    marker="o",
                    facecolors="white",
                    edgecolors=color,
                    linewidths=1.5,
                    zorder=4,
                )
                detail.scatter(
                    *target[a],
                    color=color,
                    s=38,
                    marker="X",
                    edgecolors="#333333",
                    linewidths=0.6,
                    zorder=5,
                )
                label_dx, label_dy = ((-8, 0), (11, -6), (-11, -2))[a]
                detail.annotate(
                    ("M", "S", "P")[a],
                    target[a],
                    xytext=(label_dx, label_dy),
                    textcoords="offset points",
                    ha="right" if label_dx < 0 else "left",
                    va="center",
                    fontsize=8,
                    fontweight="bold",
                    color="#333333",
                    zorder=6,
                    gid=f"reference-label-{m}-{a}",
                )
        bounds = cell.get_position(fig)
        fig.text(
            (bounds.x0 + bounds.x1) / 2,
            bounds.y1 + 0.013,
            SHORT[m],
            ha="center",
            va="bottom",
            fontsize=9,
        )
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(lo[0] - pad[0], hi[0] + pad[0])
        ax.set_ylim(lo[1] - pad[1], hi[1] + pad[1])
        ax.set_title("Overview", fontsize=8, pad=4)
        ax.axhline(0, color="#dedede", lw=0.5, zorder=0)
        ax.axvline(0, color="#dedede", lw=0.5, zorder=0)
        ax.set_xticks([-2, 0, 2, 4])
        ax.set_yticks([-2, 0, 2, 4])
        ax.tick_params(labelsize=7.5, length=3, pad=2)
        if m % 3:
            ax.tick_params(labelleft=False)
        if m < 3:
            ax.tick_params(labelbottom=False)
        detail.set_aspect("equal", adjustable="box")
        detail.set_xlim(detail_lo[0], detail_hi[0])
        detail.set_ylim(detail_lo[1], detail_hi[1])
        detail.set_title("M/S/P detail", fontsize=8, pad=4)
        detail.set_xticks([-1, 0])
        detail.set_yticks([-0.5, 0.5])
        detail.tick_params(labelsize=8, length=2, pad=1.5)
        detail.yaxis.tick_right()
        detail.tick_params(labelright=m % 3 == 2, labelbottom=m >= 3)
        for spine in detail.spines.values():
            spine.set_visible(True)
            spine.set_color("#777777")
            spine.set_linewidth(0.8)
        # Ticks can expand view limits; mark the final detail bounds beneath the data.
        detail_x0, detail_x1 = detail.get_xlim()
        detail_y0, detail_y1 = detail.get_ylim()
        ax.add_patch(
            Rectangle(
                (detail_x0, detail_y0),
                detail_x1 - detail_x0,
                detail_y1 - detail_y0,
                fill=False,
                edgecolor="#777777",
                linewidth=0.8,
                zorder=1.5,
                gid=f"detail-region-{m}",
            )
        )
    explained = singular[:2] ** 2 / np.sum(singular**2)
    fig.supxlabel(
        f"Reference-contrast axis 1 ({100 * explained[0]:.1f}% of reference-mean variation)",
        fontsize=8,
    )
    fig.supylabel(f"Reference-contrast axis 2 ({100 * explained[1]:.1f}%)", fontsize=8)
    handles = [
        Line2D([], [], marker="o", color=c, linestyle="", markersize=5, label=p)
        for c, p in zip(COLORS, PAINTERS)
    ]
    handles += [
        Line2D(
            [],
            [],
            marker="X",
            color="#555555",
            linestyle="",
            markersize=5,
            label="Reference contrast",
        ),
        Line2D(
            [],
            [],
            marker="o",
            color="#555555",
            markerfacecolor="white",
            markeredgewidth=1.4,
            markersize=6.5,
            linestyle="",
            label="Centered generated mean",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="upper center",
        ncol=6,
        frameon=False,
        bbox_to_anchor=(0.53, 1.002),
        fontsize=7.3,
        handlelength=1,
        handletextpad=0.35,
        columnspacing=0.9,
    )
    # Outer scale labels free space for larger details without shrinking the
    # overview plots. Separate detail axes preserve the entire observation cloud.
    # All overviews share their original limits; all centroid details share a
    # second set of limits, with equal x/y scaling in both views.
    return fig


def diagnostics(result):
    fig, axes = plt.subplots(1, 2, figsize=(6.45, 3.1))
    y = np.arange(6)
    for field, label, color in (
        ("amplitude_error", "Aligned-amplitude error", "#0072B2"),
        ("off_axis_error", "Orthogonal residual", "#D55E00"),
    ):
        vals = [r[field] for r in result["models"]]
        offset = -0.12 if field == "amplitude_error" else 0.12
        axes[0].scatter(vals, y + offset, label=label, color=color, s=23)
    axes[0].set(
        yticks=y,
        yticklabels=SHORT,
        xlabel="Component of repeat-corrected error D",
        title="(a) Reference-mismatch components",
    )
    axes[0].axvline(0, color="#888888", lw=0.7)
    axes[0].invert_yaxis()
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False)
    ratios = []
    for m, row in enumerate(result["models"]):
        lookup = {a["artist"]: a for a in row["artists"]}
        ratios.append([lookup.get(a, {}).get("trace_ratio", np.nan) for a in s.ARTISTS])
    values = np.array(ratios)
    im = axes[1].imshow(values, cmap="Blues", vmin=0, vmax=max(1, np.nanmax(values)), aspect="auto")
    for m in range(6):
        for a in range(4):
            value = values[m, a]
            axes[1].text(
                a,
                m,
                f"{value:.2f}" if np.isfinite(value) else "—",
                ha="center",
                va="center",
                fontsize=7.5,
                color="white" if value > 0.6 * im.norm.vmax else "#222222",
            )
    axes[1].set(
        xticks=range(4),
        xticklabels=PAINTERS,
        yticks=[],
        title="(b) Within-painter spread",
        xlabel="Generated / reference total variance",
    )
    axes[1].tick_params(axis="x", rotation=30)
    fig.subplots_adjust(left=0.19, right=0.985, bottom=0.31, top=0.85, wspace=0.25)
    return fig


def distribution_basis(refs):
    bases = []
    for ref in refs:
        mean = ref.mean(axis=0)
        _, singular, vt = np.linalg.svd(ref - mean, full_matrices=False)
        basis = vt[:2].T
        for j in range(2):
            if basis[np.argmax(abs(basis[:, j])), j] < 0:
                basis[:, j] *= -1
        bases.append((mean, basis, singular[:2] ** 2 / np.sum(singular**2)))
    return bases


def distribution_panel(ax, x, ref, painter, basis):
    mean, directions, fractions = basis
    original = (ref - mean) @ directions
    ax.scatter(*original.T, s=10, color="#777777", alpha=0.3, linewidths=0, zorder=1)
    for arm, color, marker, label in (
        (0, "#D55E00", "x", "Artist-free"),
        (1, "#0072B2", "+", "Generic"),
        (painter + 2, "#009E73", "o", "Named"),
    ):
        vectors = x[:, :, arm].reshape(-1, 31)
        points = (vectors[np.isfinite(vectors).all(axis=1)] - mean) @ directions
        ax.scatter(
            *points.T,
            s=17,
            color=color,
            alpha=0.65,
            marker=marker,
            linewidths=0.6,
            label=label,
            zorder=2,
        )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"Reference PC1 ({100 * fractions[0]:.1f}%)", fontsize=7.5)
    ax.set_ylabel(f"Reference PC2 ({100 * fractions[1]:.1f}%)", fontsize=7.5)
    ax.tick_params(labelsize=7)


def distribution_figures(x, refs):
    bases = distribution_basis(refs)
    figures = {}
    for a, painter in enumerate(PAINTERS):
        fig, axes = plt.subplots(2, 3, figsize=(6.45, 4.5), sharex=True, sharey=True)
        for m, ax in enumerate(axes.flat):
            distribution_panel(ax, x[m], refs[a], a, bases[a])
            ax.set_title(SHORT[m])
        fig.suptitle(painter + ": reference and generated distributions", fontsize=10, y=0.99)
        fig.legend(
            handles=distribution_legend(),
            loc="upper center",
            ncol=4,
            bbox_to_anchor=(0.52, 0.95),
            frameon=False,
        )
        fig.subplots_adjust(left=0.1, right=0.98, bottom=0.12, top=0.79, hspace=0.44, wspace=0.38)
        figures["specificity_distribution_" + s.ARTISTS[a]] = fig
    # The newest requested variant is selected for illustration before feature inspection.
    fig, axes = plt.subplots(2, 2, figsize=(6.45, 4.8))
    for a, ax in enumerate(axes.flat):
        distribution_panel(ax, x[3], refs[a], a, bases[a])
        ax.set_title(PAINTERS[a])
    fig.legend(
        handles=distribution_legend(),
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.53, 1),
        frameon=False,
    )
    fig.subplots_adjust(left=0.1, right=0.98, bottom=0.11, top=0.88, hspace=0.42, wspace=0.3)
    figures["specificity_sunburst_distributions"] = fig
    return figures


def distribution_legend():
    return [
        Line2D([], [], color=c, marker=m, linestyle="", label=label, markersize=4)
        for c, m, label in (
            ("#777777", "o", "References"),
            ("#D55E00", "x", "Artist-free"),
            ("#0072B2", "+", "Generic"),
            ("#009E73", "o", "Named"),
        )
    ]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    x, refs = load()
    result = s.read(s.DATA / "analysis.json")
    style()
    figures = {
        "specificity_comparison": comparison(result),
        "specificity_geometry": artist_geometry(x, refs),
        "specificity_diagnostics": diagnostics(result),
    }
    figures.update(distribution_figures(x, refs))
    for name, fig in figures.items():
        buf = io.BytesIO()
        fig.savefig(buf, format="pdf", metadata=META)
        data = buf.getvalue()
        path = OUT / f"{name}.pdf"
        if args.check:
            if path.read_bytes() != data:
                raise ValueError("figure replay differs: " + name)
        else:
            path.write_bytes(data)
        plt.close(fig)
    print("Eight specificity figures " + ("verified" if args.check else "rendered"))


if __name__ == "__main__":
    main()
