"""Display retained absolute gains and reference-recognition context.

This renders the completed original-source/primary-target learned analysis;
it performs no inference, fitting, outcome selection or scientific reanalysis.
``--check`` verifies bound inputs and exact generated TeX without writing.
"""

from __future__ import annotations

import argparse
import json
import math

from make_icml_learned_tables import (
    ARTISTS,
    MODELS,
    ROOT,
    TARGET_COUNTS,
    TITLES,
    captions_above_tables,
    rows_by_model,
    sha,
)

ANALYSIS = ROOT / "reports/painter_learned_audit_v1/analysis.json"
ANALYSIS_SHA = "06c77de4be133afc203dda122b2816d4f866e1389999f18bc94b3d9c668f28f7"
OUTPUT = ROOT / "paper/icml_learned_calibration.tex"
PAINTER_TITLES = ("Monet", "Sisley", "Pissarro", r"C\'ezanne")


def fmt(value, digits=5, *, percent=False):
    if value is None:
        return "--"
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("nonfinite or nonnumeric table value")
    scale, places = (100, 1) if percent else (1, digits)
    text = f"{scale * value:.{places}f}"
    if float(text) == 0:
        text = f"{0:.{places}f}"
    return f"${text}$"


def load():
    if sha(ANALYSIS) != ANALYSIS_SHA:
        raise ValueError("completed learned-analysis SHA differs from the bound input")
    data = json.loads(ANALYSIS.read_text())
    if set(data) != {"bindings", "clip", "csd"} or len(data["bindings"]) != 8:
        raise ValueError("expected the complete two-representation analysis and bindings")
    for path, expected in data["bindings"].items():
        local = (ROOT / path).resolve()
        if not local.is_relative_to(ROOT) or sha(local) != expected:
            raise ValueError(f"analysis input hash differs: {path}")
    for rep in ("clip", "csd"):
        view = data[rep]["original"]
        if not view["descriptive_only"] or view["axes"]["artists"] != list(ARTISTS):
            raise ValueError("unexpected analysis status or painter order")
        if view["axes"]["models"] != list(MODELS):
            raise ValueError("unexpected requested configurations")
        target = view["targets"]["primary"]
        if target["counts"] != TARGET_COUNTS["primary"] or target["reference_energy"] <= 0:
            raise ValueError("unexpected primary target")
        for row in rows_by_model(target["models"]).values():
            gain = row["prototype"]["common_vs_labeled_prototype_gain"]["named_minus_generic"]
            if not math.isclose(
                gain["common_term"] + gain["labeled_term"], gain["total"], abs_tol=1e-12
            ):
                raise ValueError("prototype decomposition is inconsistent")
            if not math.isclose(gain["total"], gain["direct_score_total"], abs_tol=1e-12):
                raise ValueError("prototype decomposition does not match direct gain")
            if not math.isclose(
                gain["labeled_term"],
                target["reference_energy"] * row["centered"]["beta"] / 4,
                abs_tol=1e-12,
            ):
                raise ValueError("prototype labeled term is inconsistent with H beta / 4")
            calibration = row["centered"]["calibration"]
            if (
                not calibration["available"]
                or len(calibration["train_q"]) != 14
                or any(value <= 0 for value in calibration["train_q"])
            ):
                raise ValueError("expected complete positive-Q calibration folds")
            generated = row["recognition"]
            if (
                not generated["available"]
                or generated["counts"] != [28] * 4
                or len(generated["confusion_counts"]) != 4
                or len(generated["per_painter_accuracy"]) != 4
            ):
                raise ValueError("complete generated painter recognition is required")
            for index, counts in enumerate(generated["confusion_counts"]):
                if (
                    len(counts) != 4
                    or sum(counts) != 28
                    or any(type(value) is not int or value < 0 for value in counts)
                    or not math.isclose(
                        counts[index] / 28,
                        generated["per_painter_accuracy"][index],
                        abs_tol=1e-12,
                    )
                ):
                    raise ValueError("generated confusion counts or recall are inconsistent")
            if not math.isclose(
                sum(generated["per_painter_accuracy"]) / 4,
                generated["macro_accuracy"],
                abs_tol=1e-12,
            ):
                raise ValueError("generated macro accuracy is inconsistent with painter recalls")
        recognition = view["development_recognition"]
        if recognition["counts"] != TARGET_COUNTS["development"] or not recognition["available"]:
            raise ValueError("complete development recognition is required")
        if len(recognition["confusion_counts"]) != 4:
            raise ValueError("expected four confusion rows")
        for counts, n in zip(recognition["confusion_counts"], recognition["counts"]):
            if (
                len(counts) != 4
                or sum(counts) != n
                or any(type(v) is not int or v < 0 for v in counts)
            ):
                raise ValueError("invalid confusion matrix or cohort")
    return data


def generated_confusion_tables(data):
    """Display every retained original/primary generated confusion matrix."""
    lines = [
        r"\subsection{Generated-image recognition by prompted painter}",
        r"Tables~\ref{tab:learned-generated-confusion-clip} and~"
        r"\ref{tab:learned-generated-confusion-csd} display all 12 retained "
        r"original-source, primary-reference confusion matrices. Each painter "
        r"prompt contains 14 scenes and two repeats ($n=28$). Complete counts "
        r"and recalls expose each painter's contribution to macro accuracy, "
        r"which weights the four painter rows equally.",
    ]
    for rep in ("clip", "csd"):
        lines += [
            r"\begin{table}[htbp]",
            r"\centering\small\setlength{\tabcolsep}{5pt}",
            r"\begin{tabularx}{\linewidth}{@{}Xr"
            r"*{4}{>{\centering\arraybackslash}p{.11\linewidth}}"
            r">{\centering\arraybackslash}p{.12\linewidth}@{}}",
            r"\toprule",
            r"& & \multicolumn{4}{c}{Predicted painter: counts} & \\",
            r"\cmidrule(lr){3-6}",
            r"Prompted painter & $n$ & Monet & Sisley & Pissarro "
            r"& C\'ezanne & Recall (\%)\\",
            r"\midrule",
        ]
        rows = rows_by_model(data[rep]["original"]["targets"]["primary"]["models"])
        for model, title in zip(MODELS, TITLES):
            rec = rows[model]["recognition"]
            lines.append(
                rf"\multicolumn{{7}}{{@{{}}l}}{{\textit{{{title}; "
                rf"macro accuracy {100 * rec['macro_accuracy']:.1f}\%}}}}\\[2pt]"
            )
            for index, painter in enumerate(PAINTER_TITLES):
                cells = [str(rec["counts"][index])]
                cells += [str(value) for value in rec["confusion_counts"][index]]
                cells.append(fmt(rec["per_painter_accuracy"][index], percent=True))
                lines.append(painter + " & " + " & ".join(cells) + r"\\")
            lines.append(r"\addlinespace[4pt]")
        lines += [
            r"\bottomrule\end{tabularx}",
            rf"\caption{{{rep.upper()}: all six generated-image confusion matrices "
            r"using unit-normalized prototypes from the 649 primary reference works. "
            r"Each panel contains 112 named generated images; its rows are the "
            r"prompted painter conditions and columns are prototype predictions. "
            r"Recall is the diagonal count divided by 28. Macro accuracy is the "
            r"mean of the four recalls and equals micro accuracy for these balanced "
            r"groups. All images use the encoder's native center crop of the "
            r"original source. Prompt labels do not constitute human judgments "
            r"of artistic fidelity; no new inference or uncertainty intervals are added.}",
            rf"\label{{tab:learned-generated-confusion-{rep}}}",
            r"\end{table}",
        ]
    return lines


def render(data):
    lines = [
        "% Generated by paper/make_icml_learned_calibration_tables.py.",
        "% Display-only extension of retained original/primary outcomes; no new experiment.",
        f"% analysis_sha256: {ANALYSIS_SHA}",
        f"% shared_renderer_sha256: {sha(ROOT / 'paper/make_icml_learned_tables.py')}",
    ]
    lines.extend(
        f"% input_sha256 {path}: {value}" for path, value in sorted(data["bindings"].items())
    )
    lines += [
        r"\subsection{Absolute gains and reference-recognition context}",
        r"These tables expose additional retained quantities from the same completed "
        r"learned audit. They use original sources with native encoder center crops "
        r"and the 649-work primary target; they add no observations, fitted "
        r"representations or inferential claims. Prototype gains use unnormalized "
        r"means of unit reference embeddings, whereas recognition normalizes each "
        r"prototype before assigning the largest dot product.",
        r"\begin{table}[htbp]",
        r"\centering\small\setlength{\tabcolsep}{5pt}",
        r"\begin{tabularx}{\linewidth}{@{}X*{5}{>{\centering\arraybackslash}p{.115\linewidth}}@{}}",
        r"\toprule",
        r"Requested configuration & Total gain & Common & Labeled "
        r"& Common (\%) & Labeled (\%)\\",
        r"\midrule",
    ]
    for rep in ("clip", "csd"):
        target = data[rep]["original"]["targets"]["primary"]
        lines.append(
            rf"\multicolumn{{6}}{{@{{}}l}}{{\textit{{{rep.upper()}; reference contrast energy "
            rf"$H={target['reference_energy']:.6f}$}}}}\\[2pt]"
        )
        rows = rows_by_model(target["models"])
        for model, title in zip(MODELS, TITLES):
            gain = rows[model]["prototype"]["common_vs_labeled_prototype_gain"][
                "named_minus_generic"
            ]
            cells = [fmt(gain[k]) for k in ("total", "common_term", "labeled_term")]
            cells += [fmt(gain[k], percent=True) for k in ("common_fraction", "labeled_fraction")]
            lines.append(title + " & " + " & ".join(cells) + r"\\")
        lines.append(r"\addlinespace[4pt]")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Absolute named-minus-generic diagonal prototype-similarity gains "
        r"and both component fractions for every configuration. The total is "
        r"common plus labeled; the labeled term is exactly $H\widehat\beta/4$. "
        r"Displayed components can differ from the displayed total by rounding. "
        r"These are cosine-similarity gains, not squared-change fractions; the "
        r"representations' reference energies and scales differ. Signed estimates "
        r"are retained, and fractions would be -- for a nonpositive total.}",
        r"\label{tab:learned-absolute-gains}",
        r"\end{table}",
        r"\begin{table}[htbp]",
        r"\centering\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xr*{4}{>{\centering\arraybackslash}p{.065\linewidth}}"
        r"*{3}{>{\centering\arraybackslash}p{.115\linewidth}}@{}}",
        r"\toprule",
        r"& & \multicolumn{4}{c}{Predicted painter: counts} "
        r"& \multicolumn{3}{c}{Recognition context}\\",
        r"\cmidrule(lr){3-6}\cmidrule(l){7-9}",
        r"True painter & $n$ & Monet & Sisley & Pissarro & C\'ezanne "
        r"& Recall (\%) & \shortstack{Mean score\\margin} & $\|\mu_a\|$\\",
        r"\midrule",
    ]
    for rep in ("clip", "csd"):
        view = data[rep]["original"]
        rec = view["development_recognition"]
        lines.append(
            rf"\multicolumn{{9}}{{@{{}}l}}{{\textit{{{rep.upper()}; "
            rf"macro accuracy {100 * rec['macro_accuracy']:.1f}\%; "
            rf"micro accuracy {100 * rec['micro_accuracy']:.1f}\%}}}}\\[2pt]"
        )
        for index, title in enumerate(PAINTER_TITLES):
            cells = [str(rec["counts"][index])]
            cells += [str(value) for value in rec["confusion_counts"][index]]
            cells += [
                fmt(rec["per_painter_accuracy"][index], percent=True),
                fmt(rec["mean_correct_minus_best_other_margin"][index]),
                fmt(view["targets"]["primary"]["prototype_norms"][index]),
            ]
            lines.append(title + " & " + " & ".join(cells) + r"\\")
        lines.append(r"\addlinespace[4pt]")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Classifying all 221 development works with the 649-work primary "
        r"prototypes. Rows are recorded painter labels and columns are predictions. "
        r"Macro accuracy gives each painter equal weight; micro accuracy weights "
        r"each work equally. The mean score margin is the correct normalized-prototype "
        r"score minus the largest incorrect score. The last column gives the "
        r"unnormalized primary prototype norm, before recognition normalizes it. "
        r"These values contextualize finite-panel separability; they do not "
        r"calibrate perceptual fidelity or probabilistic confidence. The development "
        r"panel was already used in this project, and its labels do not establish "
        r"human agreement on the generated images.}",
        r"\label{tab:learned-development-confusion}",
        r"\end{table}",
        r"\begin{table}[htbp]",
        r"\centering\small\setlength{\tabcolsep}{5pt}",
        r"\begin{tabularx}{\linewidth}{@{}X*{4}{>{\centering\arraybackslash}p{.14\linewidth}}@{}}",
        r"\toprule",
        r"& \multicolumn{2}{c}{CLIP} & \multicolumn{2}{c}{CSD}\\",
        r"\cmidrule(lr){2-3}\cmidrule(l){4-5}",
        r"Requested configuration & Original $\widehat D$ & Held-out $\widehat D$ "
        r"& Original $\widehat D$ & Held-out $\widehat D$\\",
        r"\midrule",
    ]
    rows = {
        rep: rows_by_model(data[rep]["original"]["targets"]["primary"]["models"])
        for rep in ("clip", "csd")
    }
    for model, title in zip(MODELS, TITLES):
        cells = []
        for rep in ("clip", "csd"):
            centered = rows[rep][model]["centered"]
            cells.extend((fmt(centered["d"], 3), fmt(centered["calibration"]["held_out_d"], 3)))
        lines.append(title + " & " + " & ".join(cells) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Separate scalar-calibration diagnostic on generated contrasts. "
        r"For each held-out scene, a nonnegative multiplier "
        r"$c=\max(0,\widehat\beta_{-s}/\widehat Q_{-s})$ is selected using the "
        r"other 13 fixed scenes, then the cross-repeat error is evaluated on scene "
        r"$s$ and averaged. Training $\widehat Q_{-s}$ is positive in all retained "
        r"folds. Original $\widehat D$ uses multiplier one on every scene. "
        r"This is within-panel scalar rescaling, distinct from development-work "
        r"recognition; it supplies neither new requests nor uncertainty intervals. "
        r"The reference target and its representation-specific normalizer remain fixed.}",
        r"\label{tab:learned-scalar-calibration}",
        r"\end{table}",
    ]
    lines.extend(generated_confusion_tables(data))
    return "\n".join(captions_above_tables(lines)) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render(load())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != text:
            raise SystemExit("learned calibration table replay differs")
        print("Learned calibration tables: bound inputs and exact TeX replay verified.")
    else:
        OUTPUT.write_text(text)
        print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
