"""Present the separate post-result diagnostics and a rule-selected image panel."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

from latent_art_bench.painter_specificity_measurement_v1.workflow import reference_records
from latent_art_bench.painter_specificity_reference_v1.analysis import FRAME
from latent_art_bench.painter_specificity_review_v1 import OUT
from latent_art_bench.painter_specificity_v2 import study as s

ROOT = Path(__file__).parent
META = {"Creator": "Matplotlib", "CreationDate": None, "ModDate": None}
SHORT = ("GPT Image 1", "GPT Image 2", "2.5 Flare", "2.5 Sunburst", "Nano Banana 2", "FLUX.2 Max")
PAINTERS = ("Monet", "Sisley", "Pissarro", "Cézanne")


def save(path, data, check):
    if check:
        if path.read_bytes() != data:
            raise ValueError("presentation replay differs: " + str(path))
    else:
        path.write_bytes(data)


def figure(path, fig, check):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", metadata=META, dpi=160)
    save(path, buf.getvalue(), check)
    plt.close(fig)


def tables(result, check):
    lines = [
        r"\begin{table}[tbp]\centering\small",
        r"\begin{tabular}{@{}lrrrrr@{}}\toprule",
        r"Model & $D_{\rm aggregate}$ & $V_{\rm scene}$ & $Q$ & $\beta/\sqrt Q$ & $D_{\rm held}$\\",
        r"\midrule",
    ]
    for name, row in zip(SHORT, result["models"]):
        vals = [
            row[k]
            for k in ("aggregate_d", "scene_variation", "q", "corrected_alignment", "held_out_d")
        ]
        lines.append(name + " & " + " & ".join(f"{v:.3f}" for v in vals) + r"\\")
    lines += [
        r"\bottomrule\end{tabular}",
        r"\caption{Post-result decomposition and scalar calibration. "
        r"$D=D_{\rm aggregate}+V_{\rm scene}$, whereas $D=1-2\beta+Q$ separates "
        r"alignment and response magnitude. $D_{\rm held}$ evaluates a scalar "
        r"fitted on the other 13 scenes. These are descriptive feature-space "
        r"counterfactuals, without new significance tests or realizability claims.}",
        r"\label{tab:review-calibration}\end{table}",
    ]
    save(ROOT / "specificity_review_table.tex", ("\n".join(lines) + "\n").encode(), check)
    lines = [
        r"\begin{table}[htbp]\centering\small",
        r"\begin{tabular}{@{}lrrrr@{}}\toprule",
        r" & \multicolumn{2}{c}{11 common briefs} & \multicolumn{2}{c}{14 briefs}\\",
        r"Model & Pooled target & Class target & Equal family & Covariance\\\midrule",
    ]
    for m, name in enumerate(SHORT):
        c = result["content"]["models"][m]
        vals = [
            c["pooled_d"],
            c["conditional_d"],
            result["weighting"]["equal_family"][m]["d"],
            result["weighting"]["development_covariance"][m]["d"],
        ]
        lines.append(name + " & " + " & ".join(f"{v:.3f}" for v in vals) + r"\\")
    lines += [
        r"\bottomrule\end{tabular}",
        r"\caption{Descriptive error under alternative targets and metrics. "
        r"The class target uses title-derived water, built and land strata; "
        r"the three mixed briefs are excluded. Each column uses its own reference "
        r"normalizer; absolute values across columns are not directly comparable. "
        r"Covariance is fitted only on development works, with fixed 50\% shrinkage.}",
        r"\label{tab:review-targets}\end{table}",
        r"\begin{table}[htbp]\centering\small",
        r"\begin{tabular}{@{}lrrr|rrrr@{}}\toprule",
        r" & \multicolumn{3}{c}{Reference-component slopes} "
        r"& \multicolumn{4}{c}{Slope after omitting}\\",
        r"Model & First & Second & Third & Monet & Sisley & Pissarro & C\'ezanne\\\midrule",
    ]
    for name, row in zip(SHORT, result["models"]):
        vals = row["reference_component_slopes"] + [r["beta"] for r in row["leave_artist_out"]]
        lines.append(name + " & " + " & ".join(f"{v:.3f}" for v in vals) + r"\\")
    lines += [
        r"\bottomrule\end{tabular}",
        r"\caption{Artist coverage of the aligned response. Reference components "
        r"account for 66.3\%, 20.6\% and 13.0\% of centroid variation. "
        r"Each omission recomputes the target and recenters the other three artists. "
        r"These slopes are descriptive, not artist-level significance tests.}",
        r"\label{tab:review-components}\end{table}",
    ]
    save(ROOT / "specificity_review_supplement.tex", ("\n".join(lines) + "\n").encode(), check)


def pairs(result, check):
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.35))
    labels = ("M–S", "M–P", "M–C", "S–P", "S–C", "P–C")
    for ax, field, title, lim in zip(
        axes, ("beta", "d"), ("(a) Pair slope β", "(b) Pair error D"), ((-0.3, 1.5), (0, 4))
    ):
        values = np.array([[v[field] for v in m["artist_pairs"]] for m in result["models"]])
        im = ax.imshow(
            values,
            aspect="auto",
            cmap="coolwarm" if field == "beta" else "Blues",
            vmin=lim[0],
            vmax=lim[1],
        )
        for (i, j), val in np.ndenumerate(values):
            ax.text(
                j,
                i,
                f"{val:.2f}",
                ha="center",
                va="center",
                fontsize=6.4,
                color="white" if (val > (1.2 if field == "beta" else 2.3)) else "#111111",
            )
        ax.set_xticks(range(6), labels, fontsize=7)
        ax.set_yticks(range(6), SHORT if field == "beta" else [""] * 6, fontsize=7)
        ax.set_title(title, fontsize=9)
        fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.15, fraction=0.06)
    fig.subplots_adjust(left=0.15, right=0.985, top=0.87, bottom=0.13, wspace=0.15)
    figure(ROOT / "figures/specificity_artist_pairs.pdf", fig, check)


def inspectable_images(check):
    # First declared scene and first repeat; selection uses no feature values.
    requests = [
        r for r in s.rows(s.DATA / "requests.jsonl") if r["scene"] == 0 and r["repeat"] == 0
    ]
    outcomes = {r["id"]: r for r in s.read(s.DATA / "collection.json")["outcomes"]}
    lookup = {(r["model"], r["arm"]): r for r in requests}
    manifest = {
        "selection": "first declared scene, first repeat, all models and clauses",
        "scene": s.SCENES[0][1],
        "generated": [],
        "references": [],
    }
    fig, axes = plt.subplots(6, 6, figsize=(7.1, 7.6))
    for m, model in enumerate(s.MODELS):
        for a, arm in enumerate(s.ARMS):
            req = lookup[model, arm]
            output = outcomes[req["id"]]
            path = s.ROOT / output["image_path"]
            if s.sha(path) != output["image_sha256"]:
                raise ValueError("generated image hash differs")
            with Image.open(path) as im:
                axes[m, a].imshow(ImageOps.exif_transpose(im).convert("RGB"))
            axes[m, a].set_xticks([])
            axes[m, a].set_yticks([])
            axes[m, a].set_xlabel(req["id"], fontsize=5.5, labelpad=2)
            if m == 0:
                axes[m, a].set_title(("Free", "Generic", *PAINTERS)[a], fontsize=8)
            if a == 0:
                axes[m, a].set_ylabel(SHORT[m], fontsize=7)
            manifest["generated"].append(
                dict(
                    id=req["id"],
                    model=s.TITLES[m],
                    arm=arm,
                    prompt=req["payload"]["prompt"],
                    path=output["image_path"],
                    sha256=output["image_sha256"],
                )
            )
    fig.subplots_adjust(left=0.10, right=0.99, bottom=0.035, top=0.96, hspace=0.20, wspace=0.06)
    figure(ROOT / "figures/specificity_image_examples.pdf", fig, check)
    frame = {r["work_id"]: r for r in s.rows(FRAME)}
    acquisitions = {r["work_id"]: r for r in s.rows(s.ACQUISITIONS)}
    records = reference_records()
    fig, axes = plt.subplots(1, 4, figsize=(6.7, 2.0))
    for a, artist in enumerate(s.ARTISTS):
        candidates = sorted(
            [
                r
                for r in records
                if r["painter_id"] == artist
                and frame[r["image_id"]]["content_class"] == "water_organized"
                and "public domain" in acquisitions[r["image_id"]]["licence"].lower()
            ],
            key=lambda r: r["image_id"],
        )
        ref = candidates[0]
        item = acquisitions[ref["image_id"]]
        path = s.ROOT / item["raw_path"]
        if s.sha(path) != ref["raw_sha256"]:
            raise ValueError("reference image hash differs")
        with Image.open(path) as im:
            axes[a].imshow(ImageOps.exif_transpose(im).convert("RGB"))
        axes[a].set_xticks([])
        axes[a].set_yticks([])
        axes[a].set_title(PAINTERS[a], fontsize=9)
        axes[a].set_xlabel(ref["image_id"].split(":")[1], fontsize=7)
        manifest["references"].append(
            dict(
                id=ref["image_id"],
                artist=artist,
                selection=(
                    "lexicographically first measured water-class work "
                    "with recorded public-domain status"
                ),
                title=frame[ref["image_id"]]["labels"],
                url=item["url"],
                licence=item["licence"],
                path=item["raw_path"],
                sha256=ref["raw_sha256"],
            )
        )
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.17, top=0.87, wspace=0.1)
    figure(ROOT / "figures/specificity_reference_examples.pdf", fig, check)
    save(
        OUT / "inspection.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
        check,
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--images",
        action="store_true",
        help="also render/check example panels from retained raw images",
    )
    args = parser.parse_args()
    result = s.read(OUT / "analysis.json")
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    tables(result, args.check)
    pairs(result, args.check)
    if args.images:
        inspectable_images(args.check)
    print("Review presentation " + ("verified" if args.check else "rendered"))


if __name__ == "__main__":
    main()
