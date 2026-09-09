"""Create-once numerical tables and scientific figures from measured compact records."""

from __future__ import annotations

import csv

import numpy as np

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, publish

from . import pipeline
from .transforms import CONDITIONS

CONDITION_LABELS = (
    "Baseline", "Lossless PNG", "JPEG 95", "JPEG 75", "Resample 384",
    "Chroma ×0.8", "Chroma ×0.6", "Blur σ=1", "Blur σ=2", "Tile rearrangement",
)
SERVICE_LABELS = {"nano_banana_2": "Nano Banana 2", "flux_2_max": "FLUX",
                  "oauth_gpt_image_2": "OAuth"}


def table(path, rows):
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def figures(directory, analysis):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    families = ("color", "spatial", "texture")
    lookup = {(r["condition"], r["family"]): r["mean"]
              for r in analysis["challenge"]["family_matrix"] if r["painter_id"] == "equal_painter"}
    values = np.array([[lookup[name, f] for f in families] for name in CONDITIONS])
    with plt.rc_context({"font.size": 10, "pdf.fonttype": 42}):
        fig, ax = plt.subplots(figsize=(5.4, 5.5), layout="constrained")
        artist = ax.imshow(values, cmap="Blues", aspect="auto", vmin=0)
        ax.set_xticks(range(3), [f.title() for f in families])
        ax.set_yticks(range(10), CONDITION_LABELS)
        ax.set_title("Known changes and processing challenges")
        for i in range(10):
            for j in range(3):
                ax.text(j, i, f"{values[i, j]:.3f}", ha="center", va="center",
                        color="white" if values[i, j] > values.max() * .6 else "black")
        fig.colorbar(artist, ax=ax, label="Mean RMS displacement in development-IQR units")
        for suffix in ("pdf", "png"):
            metadata = {"CreationDate": None, "ModDate": None} if suffix == "pdf" else None
            fig.savefig(directory / f"challenge_matrix.{suffix}", dpi=180, metadata=metadata)
        plt.close(fig)

        rows = analysis["geometry"]["comparisons"]
        fig, ax = plt.subplots(figsize=(8.3, 4.3), layout="constrained")
        y = np.arange(len(rows))
        full = [r["full_view_estimate"] for r in rows]
        square = [r["square_estimate"] for r in rows]
        ax.hlines(y, full, square, color="0.7", linewidth=1)
        ax.scatter(full, y, label="Original full view", marker="o", color="#235789")
        ax.scatter(square, y, label="Common central square", marker="s", color="#D1495B")
        labels = []
        for r in rows:
            service = SERVICE_LABELS.get(r["route"], r["route"])
            painter = "Monet" if r["painter_id"] == "claude_monet" else "Cézanne"
            comparison = "named − generic" if r["before"] == "generic_named" else "named − free"
            labels.append(f"{service} / {painter} / {comparison}")
        ax.set_yticks(y, labels, fontsize=8)
        ax.axvline(0, color="0.3", linewidth=.8)
        ax.set_xlabel("Paired energy-discrepancy contrast (same frozen scaler)")
        ax.set_title("Common field-of-view sensitivity")
        ax.invert_yaxis()
        ax.legend(loc="best", fontsize=8)
        for suffix in ("pdf", "png"):
            metadata = {"CreationDate": None, "ModDate": None} if suffix == "pdf" else None
            fig.savefig(directory / f"geometry_contrasts.{suffix}", dpi=180, metadata=metadata)
        plt.close(fig)


def build(root, run_id=pipeline.RUN_ID):
    pipeline.check(root, run_id)
    directory, _, report = pipeline.locations(run_id)
    destination = root / report
    if destination.exists():
        raise ValueError("report already exists; do not overwrite retained output")
    destination.mkdir(parents=True)
    analysis = read_json(root / directory / "analysis.json")
    table(destination / "family_matrix.csv", analysis["challenge"]["family_matrix"])
    table(destination / "geometry_contrasts.csv", analysis["geometry"]["comparisons"])
    table(destination / "dose_responses.csv", analysis["challenge"]["dose_responses"])
    area_rows = [{k: v for k, v in r.items() if k != "mean_displacement"}
                 for r in analysis["geometry"]["groups"]]
    table(destination / "retained_area.csv", area_rows)
    figures(destination, analysis)
    lines = [
        "# Computational measurement validation", "",
        "This successor measures ten fixed conditions on all 70 previously exposed reference "
        "works and a common central square on all 1,006 retained Study 1 generated images. "
        "There are 1,706 unique feature vectors; the 70 reference-square vectors are reused. "
        "No new images were collected and no human ratings were obtained.", "",
        "The unchanged full-view eight-endpoint inference replays exactly. Square-window "
        "results are post-result sensitivities and preserve the original pairing, "
        "missingness, weights, randomization seeds and Holm family. They do not replace "
        "the original primary results.", "",
        "## Known-change versus processing challenges", "",
        "Positive differences indicate that the fixed known change displaced the specified "
        "feature family more than the per-work maximum of JPEG 95 and resampling. "
        "Neither processing operation is assumed perceptually irrelevant. Intervals are "
        "descriptive whole-work bootstrap summaries conditional on the exposed panel, "
        "with nominal 98.3333% per comparison (Bonferroni-three adjustment); "
        "population coverage is unqualified.", "",
        "| Family | Equal-painter mean difference | Descriptive interval |",
        "| --- | ---: | --- |",
    ]
    for row in analysis["challenge"]["comparisons"]:
        interval = ("unavailable: zero bootstrap variance" if row["lower"] is None else
                    f"[{row['lower']:.6f}, {row['upper']:.6f}]")
        lines.append(f"| {row['family']} | {row['estimate']:.6f} | {interval} |")
    lines += ["", "![All-family displacement matrix](challenge_matrix.png)", "",
              "The matrix retains cross-family responses: tile boundaries can change "
              "neighboring-color measurements despite exact preservation of the pixel "
              "multiset. Chroma contraction partially tests its own measurement definition; "
              "signed chroma responses and gamut clipping are retained per work. No "
              "all-feature monotonicity requirement or perceptual pass margin is imposed.", "",
              "## Common central field of view", "",
              "![Eight geometry contrasts](geometry_contrasts.png)", "",
              "The central square is cropped after the unchanged 512-pixel short-side "
              "normalization, without a second normalization or anisotropic warp. "
              "Cropping changes visible content and does not isolate photographic capture. "
              "The square-condition p-values are sensitivity outputs, not new confirmation.", "",
              "All 31 feature coordinates, normalization/window metadata, work-level "
              "processing contrasts, signed chroma responses, and per-image geometry "
              "shifts are in the bound feature/analysis records. The scaler is unchanged. "
              "These results cannot establish painter-style, physical-brushwork or "
              "independent-capture equivalence.", "",
              "| Source | Painter | Images | Retained area: min / median / max |",
              "| --- | --- | ---: | --- |"]
    for row in area_rows:
        source = SERVICE_LABELS.get(row["group"], row["group"].title())
        painter = "Monet" if row["painter_id"] == "claude_monet" else "Cézanne"
        area = " / ".join(f"{row[name + '_retained_area_fraction']:.1%}"
                          for name in ("min", "median", "max"))
        lines.append(f"| {source} | {painter} | {row['images']} | {area} |")
    lines.append("")
    (destination / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    outputs = [p.relative_to(root) for p in destination.iterdir() if p.is_file()]
    receipt = dict(run_id=run_id, analysis_sha256=hash_file(root / directory / "analysis.json"),
                   outputs=bindings(root, outputs))
    publish(destination / "report_receipt.json", receipt)
    return dict(status="published", report=(report / "REPORT.md").as_posix(), files=len(outputs))
