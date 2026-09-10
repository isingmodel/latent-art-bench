"""Render/check a readable manuscript derivative of the sealed geometry figure.

Only layout changes: both panels use stored primary512/all31 values, in the
original order and with the original colors/markers. No model, statistic or
deletion summary is recomputed. The original report/figure remain untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.text import Text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/manifests/painter_naming_geometry_v1/pngv1-20260910/analysis.json"
SOURCE_SHA256 = "f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324"
TARGET = ROOT / "paper/figures/naming_geometry_presentation.pdf"
LABELS = {
    "nano_banana_2": "NB2", "flux_2_max": "FLUX", "oauth_gpt_image_2": "OAuth",
    "claude_monet": "Monet", "paul_cezanne": "Cézanne",
}
KINDS = ("identity", "translation", "translation_scale", "named")
COLORS = ("#777777", "#b2182b", "#2166ac", "#1b7837")
PANEL_WIDTH_INCHES = 160 / 25.4  # Full text width with A4 and 25 mm margins.


def read_result():
    content = SOURCE.read_bytes()
    if hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise ValueError("sealed geometry figure input changed")
    return json.loads(content)


def primary(result, key):
    return [r for r in result[key] if r["pipeline"] == "primary512" and r["view"] == "all31"]


def figure(result):
    rows, later = primary(result, "original"), primary(result, "transfer")
    expected = [(route, painter) for route in
                ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
                for painter in ("claude_monet", "paul_cezanne")]
    if [(r["route"], r["painter"]) for r in rows] != expected:
        raise ValueError("geometry primary cell order changed")
    if [r["painter"] for r in later] != ["claude_monet", "paul_cezanne"]:
        raise ValueError("geometry transfer cell order changed")
    if any(len(r["folds"]) != 4 for r in rows):
        raise ValueError("geometry figure requires four stored folds per cell")
    if any(len(r["delete_one_scene"]) != 24 for r in rows + later):
        raise ValueError("geometry source requires all stored deletion records")

    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.labelsize": 9,
        "axes.titlesize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
        "legend.fontsize": 8.5, "pdf.fonttype": 42, "axes.spines.top": False,
        "axes.spines.right": False,
    }):
        fig, axes = plt.subplots(2, 1, figsize=(PANEL_WIDTH_INCHES, 6.0),
                                 gridspec_kw={"height_ratios": [1.25, 1]})
        fig.subplots_adjust(left=.205, right=.98, top=.94, bottom=.13, hspace=.80)
        points_to_check = []
        for index, row in enumerate(rows):
            values = [fold["residuals"]["translation_scale"] for fold in row["folds"]]
            artist = axes[0].scatter(values, [index] * 4, color="#999999", s=18, zorder=2)
            points_to_check.append((artist, [[x, index] for x in values]))
            for kind, marker, color in (("translation_scale", "D", COLORS[2]),
                                         ("translation", "x", COLORS[1])):
                value = row["residual_mean"][kind]
                artist = axes[0].scatter(value, index, marker=marker, color=color,
                                         s=36, zorder=3)
                points_to_check.append((artist, [[value, index]]))
        axes[0].axvline(0, color="black", linewidth=.8)
        axes[0].set_yticks(range(6), [f"{LABELS[r['route']]} / {LABELS[r['painter']]}"
                                    for r in rows])
        axes[0].invert_yaxis()
        axes[0].set_xlabel("Energy: actual named − fitted benchmark")
        axes[0].set_title("A  Held-scene proximity residual", loc="left", pad=12)
        axes[0].scatter([], [], marker="D", color=COLORS[2], label="Shift/scale mean")
        axes[0].scatter([], [], marker="x", color=COLORS[1], label="Shift mean")
        axes[0].scatter([], [], color="#999999", s=18, label="Shift/scale folds")
        axes[0].legend(loc="upper center", bbox_to_anchor=(.5, -.25), ncol=3,
                       borderaxespad=0, columnspacing=1.0, handletextpad=.4)

        bars_to_check = []
        for j, (kind, label, color) in enumerate(zip(
                KINDS, ("Free", "Shift", "Shift/scale", "Actual named"), COLORS)):
            positions = np.arange(2) + (j - 1.5) * .18
            values = [r["energies"][kind]["energy"] for r in later]
            bars = axes[1].bar(positions, values, width=.17, color=color, label=label)
            bars_to_check.extend(zip(bars, values))
        axes[1].set_xticks(range(2), [LABELS[r["painter"]] for r in later])
        axes[1].set_ylabel("Energy to fixed painting panel")
        axes[1].set_title("B  Original-map transfer to later FLUX", loc="left", pad=12)
        axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.20), ncol=4,
                       borderaxespad=0, columnspacing=1.1, handletextpad=.4)

        fig.canvas.draw()
        # Compare actual artist coordinates/heights to the stored fields, not
        # rounded table values or a fresh statistical computation.
        for artist, stored in points_to_check:
            np.testing.assert_array_equal(artist.get_offsets(), stored)
        for artist, stored in bars_to_check:
            if artist.get_height() != stored:
                raise ValueError("geometry bar differs from its stored energy")
        visible_text = [t for t in fig.findobj(Text) if t.get_visible() and t.get_text()]
        if min(t.get_fontsize() for t in visible_text) < 8:
            raise ValueError("geometry figure has text smaller than eight points")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="require exact existing PDF bytes")
    args = parser.parse_args()
    result = read_result()
    original = json.dumps(result, sort_keys=True)
    fig = figure(result)
    output = io.BytesIO()
    with plt.rc_context({"pdf.fonttype": 42}):
        fig.savefig(output, format="pdf", metadata={"Creator": "Matplotlib",
                                                   "CreationDate": None, "ModDate": None})
    plt.close(fig)
    if json.dumps(result, sort_keys=True) != original:
        raise ValueError("geometry renderer changed stored values")
    read_result()  # Input bytes, including all deletion records, remain sealed.
    if args.check:
        if TARGET.read_bytes() != output.getvalue():
            raise ValueError("manuscript geometry presentation differs from its numeric source")
        print("Geometry presentation reproduces byte for byte.")
    else:
        TARGET.write_bytes(output.getvalue())
        print(TARGET.relative_to(ROOT))
    print("Exact plotted parity: 24 fold residuals, 12 stored means, eight energies; "
          "192 stored deletion records unchanged. Text is at least 8.5 pt at 160 mm width.")


if __name__ == "__main__":
    main()
