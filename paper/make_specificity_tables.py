"""Render complete model comparisons for the paper from recorded result JSONs."""

from __future__ import annotations

import argparse
from pathlib import Path

from latent_art_bench.painter_specificity_measurement_v1.workflow import verify
from latent_art_bench.painter_specificity_v2 import study as s


def fmt(value):
    return "--" if value is None else f"{value:.3f}"


def estimate(cell, key="simultaneous_ci", reverse=False):
    if cell is None or not cell["available"]:
        return "unavailable"
    mean = cell["mean"]
    lo, hi = cell[key]
    if reverse:
        mean, lo, hi = -mean, -hi, -lo
    return f"${fmt(mean)}\\;[{fmt(lo)},{fmt(hi)}]$"


def build():
    verify()
    data = s.read(s.DATA / "analysis.json")
    rows = [
        r"\begin{table}[tbp]",
        r"\centering\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}p{.24\linewidth}"
        r">{\raggedright\arraybackslash}Xr>{\raggedright\arraybackslash}X@{}}",
        r"\toprule",
        r"Model & Aligned response $\beta$ & \shortstack{Uncalibrated\\error $D$} "
        r"& $\Delta D$ versus FLUX\\",
        r"\midrule",
    ]
    for m, row in enumerate(data["models"]):
        baseline = r"$0$ (baseline)"
        if row["model"] != s.MODELS[-1]:
            pair = next(
                c
                for c in data["comparisons"]
                if {c["model_a"], c["model_b"]} == {row["model"], s.MODELS[-1]}
            )
            baseline = estimate(pair, reverse=pair["model_a"] != row["model"])
        rows.append(
            f"{s.TITLES[m]} & {estimate(row['beta'])} & "
            f"${fmt(row['distortion']['mean'])}$ & {baseline}\\\\[3pt]"
        )
    flux = next(row for row in data["models"] if row["model"] == s.MODELS[-1])
    absolute_lo, absolute_hi = flux["distortion"]["ci95"]
    rows += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Agreement with the full-frame reference target. "
        r"$\beta=1$ matches its aligned amplitude; larger is not necessarily better. "
        r"Expected $D$ is 0 for exact agreement and 1 for no painter distinctions. "
        r"Positive $\Delta D$ favors FLUX.2 Max. "
        r"Table brackets give approximate 95\% simultaneous intervals from the prespecified family "
        r"of six aligned responses and 15 scene-paired model contrasts. "
        r"FLUX's lowest $D$ estimate has an unadjusted 95\% interval "
        f"$[{fmt(absolute_lo)},{fmt(absolute_hi)}]$, "
        r"spanning the no-distinction value 1; this interval is descriptive.}",
        r"\label{tab:specificity-models}\end{table}",
    ]
    pairs = [
        r"\begin{table}[htbp]\centering\small",
        r"\begin{tabular}{llr}\toprule",
        r"Model A & Model B & $D_A-D_B$ [simultaneous interval]\\\midrule",
    ]
    short = dict(
        zip(
            s.MODELS,
            (
                "GPT Image 1",
                "GPT Image 2",
                "2.5 Flare",
                "2.5 Sunburst",
                "Nano Banana 2",
                "FLUX.2 Max",
            ),
        )
    )
    for c in data["comparisons"]:
        pairs.append(f"{short[c['model_a']]} & {short[c['model_b']]} & {estimate(c)}\\\\")
    pairs += [
        r"\bottomrule\end{tabular}",
        r"\caption{All 15 paired model comparisons in the prespecified inferential family. "
        r"Intervals are approximate 95\% simultaneous intervals adjusted across all 21 endpoints. "
        r"A negative contrast favors model A on the stated feature-geometry target.}",
        r"\label{tab:all-specificity-pairs}\end{table}",
    ]
    artists = [
        r"\begin{table}[htbp]\centering\small",
        r"\begin{tabular}{llrrrr}\toprule",
        r"Model & Measure & Monet & Sisley & Pissarro & C\'ezanne\\\midrule",
    ]
    for m, row in enumerate(data["models"]):
        lookup = {a["artist"]: a for a in row["artists"]}
        energy_cells = []
        variance_cells = []
        for a in s.ARTISTS:
            v = lookup.get(a)
            if v and v["generic_energy"] is not None:
                energy_cells.append(f"${v['energy'] - v['generic_energy']:.3f}$")
                variance_cells.append(f"${v['trace_ratio']:.3f}$")
            else:
                energy_cells.append("unavailable")
                variance_cells.append("unavailable")
        artists.append(
            short[row["model"]] + " & Energy change & " + " & ".join(energy_cells) + r"\\"
        )
        artists.append("& Variance ratio & " + " & ".join(variance_cells) + r"\\")
        if m < len(data["models"]) - 1:
            artists.append(r"\addlinespace[2pt]")
    artists += [
        r"\bottomrule\end{tabular}",
        r"\caption{Complementary empirical distribution summaries. Energy change is "
        r"named-minus-generic reference energy; variance ratios are generated-to-reference. "
        r"Negative changes favor naming; ratios below one indicate narrower generated "
        r"feature distributions.}",
        r"\label{tab:artist-distributions}\end{table}",
    ]
    # These retained components average feature changes over scenes before
    # taking cross-repeat products; they are not the within-scene diagnostic.
    shared_percent = [100 * row["shared"]["common_fraction"] for row in data["models"]]
    diagnostics = s.read(s.ROOT / "reports/painter_specificity_review_v2/analysis.json")
    alignment = {row["model"]: row["alignment"] for row in diagnostics["models"]}
    controls = [alignment[title] for title in s.TITLES]
    shared = [
        r"\begin{table}[htbp]\centering\small\setlength{\tabcolsep}{3pt}",
        r"\begin{tabularx}{\linewidth}{@{}l*{6}{>{\centering\arraybackslash}X}@{}}",
        r"\toprule",
        r"& \shortstack{GPT Image\\1} & \shortstack{GPT Image\\2} "
        r"& Flare & Sunburst & \shortstack{Nano\\Banana 2} "
        r"& \shortstack{FLUX.2\\Max}\\\midrule",
        r"Shared (\%) & " + " & ".join(f"{value:.1f}" for value in shared_percent) + r"\\",
        r"Between-name (\%) & "
        + " & ".join(f"{100 - value:.1f}" for value in shared_percent)
        + r"\\",
        r"\midrule",
        r"Corrected cosine & "
        + " & ".join(fmt(row["ratio"]) for row in controls)
        + r"\\",
        r"Squared-size ratio & "
        + " & ".join(
            fmt(row["common_cross_norm_squared"] / row["generic_cross_norm_squared"])
            for row in controls
        )
        + r"\\",
        r"\bottomrule\end{tabularx}",
        r"\caption{Shares of scene-averaged, repeat-corrected squared change "
        r"from artist-free to named prompts, including the painting clause. "
        r"Shared is the four-name mean shift; between-name is departure from it. "
        r"The lower rows give retrospective comparisons of the shared named shift with "
        r"the generic oil-painting shift, using the same artist-free baseline. "
        r"The noise-corrected cosine measures their directional agreement (1 means parallel); "
        r"the ratio divides their repeat-corrected squared magnitudes, shared by generic.}",
        r"\label{tab:shared-change}\end{table}",
    ]
    return {
        "specificity_model_table.tex": "\n".join(rows) + "\n",
        "specificity_supplement_tables.tex": "\n".join(pairs + [""] + artists) + "\n",
        "specificity_shared_table.tex": "\n".join(shared) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in build().items():
        path = Path(__file__).parent / name
        if args.check:
            if path.read_text() != content:
                raise ValueError("paper table differs: " + name)
        else:
            path.write_text(content)
    print("Specificity tables " + ("verified" if args.check else "rendered"))


if __name__ == "__main__":
    main()
