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
        r"Model & Reference slope $\beta$ & Error $D$ & $\Delta D$ versus GPT Image 2\\",
        r"\midrule",
    ]
    for m, row in enumerate(data["models"]):
        baseline = r"$0$ (baseline)"
        if m != 1:
            pair = next(
                c
                for c in data["comparisons"]
                if {c["model_a"], c["model_b"]} == {row["model"], s.MODELS[1]}
            )
            baseline = estimate(pair, reverse=pair["model_a"] != row["model"])
        rows.append(
            f"{s.TITLES[m]} & {estimate(row['beta'])} & "
            f"${fmt(row['distortion']['mean'])}$ & {baseline}\\\\[3pt]"
        )
    rows += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Reference-relative recovery and scene-paired model comparisons. "
        r"Lower $D$ indicates less conditional artist-geometry error; "
        r"larger $\beta$ is not necessarily better. Brackets give approximate simultaneous "
        r"intervals from the fixed family of six slopes and 15 model contrasts. "
        r"On a complete common panel, model differences equal the scene fixed-effects "
        r"regression contrasts. Inference uses paired scene differences.}",
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
        r"A negative contrast favors model A on the stated feature-geometry target. "
        r"Flare and Sunburst denote the corresponding GPT Image 2.5 models.}",
        r"\label{tab:all-specificity-pairs}\end{table}",
    ]
    artists = [
        r"\begin{table}[htbp]\centering\small",
        r"\begin{tabular}{lrrrr}\toprule",
        r"Model & Monet & Sisley & Pissarro & C\'ezanne\\\midrule",
    ]
    for row in data["models"]:
        lookup = {a["artist"]: a for a in row["artists"]}
        cells = []
        for a in s.ARTISTS:
            v = lookup.get(a)
            if v and v["generic_energy"] is not None:
                cells.append(
                    rf"${v['energy'] - v['generic_energy']:.3f}\; /\; {v['trace_ratio']:.3f}$"
                )
            else:
                cells.append("unavailable")
        artists.append(short[row["model"]] + " & " + " & ".join(cells) + r"\\")
    artists += [
        r"\bottomrule\end{tabular}",
        r"\caption{Complementary outcomes for all four painters: each cell gives "
        r"named-minus-generic reference energy / generated-to-reference total variance. "
        r"These are descriptive empirical distribution summaries, without additional tests. "
        r"Lower energy change favors naming over the generic clause; a variance ratio below "
        r"one indicates a narrower generated feature distribution.}",
        r"\label{tab:artist-distributions}\end{table}",
    ]
    return {
        "specificity_model_table.tex": "\n".join(rows) + "\n",
        "specificity_supplement_tables.tex": "\n".join(pairs + [""] + artists) + "\n",
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
