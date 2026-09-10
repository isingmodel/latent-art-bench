"""Deterministic report and plot of the complete prespecified diagnostic grid."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

LABELS = {"nano_banana_2": "NB2", "flux_2_max": "FLUX", "oauth_gpt_image_2": "OAuth",
          "claude_monet": "Monet", "paul_cezanne": "Cézanne"}


def primary(result, key):
    return [r for r in result[key] if r["pipeline"] == "primary512" and r["view"] == "all31"]


def text_report(result):
    lines = ["# Global moment account of painter naming", "",
             "Post-result, fixed-panel descriptive analysis. No new images, tests or intervals.",
             "Negative residual energy favors actual named outputs; positive favors the fitted "
             "benchmark. Near zero is not equivalence. Fold energies are not the original "
             "72-query energies. All folds and deletion sensitivities are retained "
             "in analysis.json.",
             "", "## Held-scene primary metric", "",
             "| Service / painter | Free | Shift | Shift/scale | Named | Named−shift/scale "
             "| Four fold residuals | Delete-one range |",
             "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for r in primary(result, "original"):
        e = r["energy_mean"]
        folds = [f["residuals"]["translation_scale"] for f in r["folds"]]
        deletion = [d["residual_mean"]["translation_scale"] for d in r["delete_one_scene"]]
        cells = [f"{LABELS[r['route']]} / {LABELS[r['painter']]}"]
        cells += [f"{e[k]:.6f}" for k in ("identity", "translation", "translation_scale", "named")]
        cells += [f"{r['residual_mean']['translation_scale']:.6f}",
                  ", ".join(f"{x:.4f}" for x in folds),
                  f"[{min(deletion):.6f}, {max(deletion):.6f}]"]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Original-map transfer to later FLUX", "",
              "| Painter | Free | Shift | Shift/scale | Named | Named−shift/scale "
              "| Delete-one range |", "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for r in primary(result, "transfer"):
        e = r["energies"]
        deletion = [d["residuals"]["translation_scale"] for d in r["delete_one_scene"]]
        cells = [LABELS[r["painter"]]]
        cells += [f"{e[k]['energy']:.6f}" for k in
                  ("identity", "translation", "translation_scale", "named")]
        cells += [f"{r['residuals']['translation_scale']:.6f}",
                  f"[{min(deletion):.6f}, {max(deletion):.6f}]"]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Repeat-corrected conditional geometry", "",
              "B* is corrected fixed-scene variance; N* is unbiased repeat-noise trace. "
              "These estimates require independent, stable repeat errors. Negative estimates "
              "are retained. Ratios below are named/free; residual means are absolute IQR² units.",
              "", "| Cell | Weighting | B* ratio | N* ratio | (B*/N*) ratio | "
              "Corrected held-scene residual, shift/scale |",
              "| --- | --- | ---: | ---: | ---: | ---: |"]
    for r in primary(result, "original"):
        for weighting, value in r["variance"].items():
            v = value["named_free_ratios"]
            residual = r["conditional_residual_mean"]["translation_scale"]
            cells = [f"{LABELS[r['route']]} / {LABELS[r['painter']]}", weighting]
            cells += [f"{v[k]:.6f}" if v[k] is not None else "unavailable" for k in
                      ("corrected_between", "repeat_noise", "corrected_signal_to_noise")]
            cells += [f"{residual:.6f}" if weighting == "reference_content" else "not evaluated"]
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Fixed-reference ball occupancy", "",
              "Same complete reference anchors and k=3 for all maps. Equal-class query counts "
              "are 18 within a held-scene fold and 24 in the later cohort. This differs from "
              "the predecessor matched-real coverage design and has no real/real calibration.",
              "", "| Cohort / cell | Free | Shift | Shift/scale | Named |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for key in ("original", "transfer"):
        for r in primary(result, key):
            coverage = r["occupancy_mean"] if key == "original" else {
                k: v["coverage"] for k, v in r["occupancy"].items()}
            label = f"{key} / {LABELS[r.get('route', 'flux_2_max')]} / {LABELS[r['painter']]}"
            lines.append("| " + " | ".join([label] + [f"{coverage[k]:.6f}" for k in
                         ("identity", "translation", "translation_scale", "named")]) + " |")
    lines += ["", "## Complete metric and processing sensitivity", "",
              "No direction count is a hypothesis test. No views are selected for success.",
              "", "| Cohort | Pipeline | View | Service | Painter | Named−shift/scale |",
              "| --- | --- | --- | --- | --- | ---: |"]
    for key in ("original", "transfer"):
        for r in result[key]:
            residual = r["residual_mean" if key == "original" else "residuals"]
            cells = [key, r["pipeline"], r["view"], LABELS[r.get("route", "flux_2_max")],
                     LABELS[r["painter"]], f"{residual['translation_scale']:.6f}"]
            lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Interpretation boundary", "",
              "A map predicts measured proximity, not feasible image edits or internal model "
              "mechanisms. Its scalar is fitted from total observed traces, not a latent gain. "
              "Conditional residual correction concerns means, not full conditional distributions. "
              "The later cohort reuses templates and investigators. Capture differences, artistic "
              "judgment and new-scene generalization are not resolved by this analysis.", ""]
    return "\n".join(lines)


def plot(result, path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), gridspec_kw={"width_ratios": [1.25, 1]})
    rows = primary(result, "original")
    for index, row in enumerate(rows):
        points = [r["residuals"]["translation_scale"] for r in row["folds"]]
        axes[0].scatter(points, np.full(4, index), color="#999999", s=18, zorder=2)
        axes[0].scatter(row["residual_mean"]["translation_scale"], index,
                        marker="D", color="#2166ac", s=36, zorder=3)
        axes[0].scatter(row["residual_mean"]["translation"], index,
                        marker="x", color="#b2182b", s=36, zorder=3)
    axes[0].axvline(0, color="black", linewidth=.8)
    axes[0].set_yticks(range(len(rows)), [f"{LABELS[r['route']]} / {LABELS[r['painter']]}"
                                        for r in rows])
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Energy: actual named − fitted benchmark")
    axes[0].set_title("A  Held-scene proximity residual")
    axes[0].scatter([], [], marker="D", color="#2166ac", label="Shift/scale mean")
    axes[0].scatter([], [], marker="x", color="#b2182b", label="Shift mean")
    axes[0].scatter([], [], color="#999999", s=18, label="Shift/scale folds")
    axes[0].legend(fontsize=7, loc="lower right")
    colors = ("#777777", "#b2182b", "#2166ac", "#1b7837")
    later = primary(result, "transfer")
    for j, (kind, label, color) in enumerate(zip(
            ("identity", "translation", "translation_scale", "named"),
            ("Free", "Shift", "Shift/scale", "Actual named"), colors)):
        axes[1].bar(np.arange(2) + (j-1.5)*.18,
                    [r["energies"][kind]["energy"] for r in later],
                    width=.17, color=color, label=label)
    axes[1].set_xticks(range(2), [LABELS[r["painter"]] for r in later])
    axes[1].set_ylabel("Energy to fixed painting panel")
    axes[1].set_title("B  Original-map transfer to later FLUX")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(Path(path), metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
