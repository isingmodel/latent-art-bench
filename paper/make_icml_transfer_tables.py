"""Render complete fixed-rule transfer tables from frozen results, without refitting.

Default writes only the two named generated TeX files. --check verifies input
hashes, reconstructs all displayed accounting from predictions and compares TeX.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/painter_prototype_transfer_v1"
ANALYSIS_SHA = "e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448"
INPUT_SHA = "bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf"
MODELS = (
    "gpt-image-1",
    "gpt-image-2",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image",
    "black-forest-labs/flux.2-max",
)
TITLES = (
    "GPT Image 1",
    "GPT Image 2",
    "GPT 2.5 Flare",
    "GPT 2.5 Sunburst",
    "Nano Banana 2",
    "FLUX.2 Max",
)
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
RULES = ("reference_baseline", "common_translation", "generated_prototype")
SETTINGS = (
    ("original", "primary", "Original sources / primary target"),
    ("original", "development", "Original sources / development target"),
    ("audited_region", "primary", "Audited regions / primary target"),
    ("audited_region", "development", "Audited regions / development target"),
)
PAIRS = ("paired_translation_vs_baseline", "paired_generated_prototype_vs_baseline")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b, message):
    require(np.allclose(a, b, rtol=0, atol=1e-12), message)


def group(data, rep, view, target):
    return data["representations"][rep][view]["targets"][target]


def rows(data, rep, view, target):
    values = group(data, rep, view, target)["models"]
    require(
        len(values) == 6 and {v["model"] for v in values} == set(MODELS), "configuration membership"
    )
    return {row["model"]: row for row in values}


def verify_rule(rule):
    predictions = np.asarray(rule["predictions"])
    scores = np.asarray(rule["scores"])
    require(
        predictions.shape == (14, 2, 4) and predictions.dtype.kind in "iu",
        "112 integer predictions required",
    )
    require(np.all((predictions >= 0) & (predictions < 4)), "prediction outside candidate set")
    require(
        scores.shape == (14, 2, 4, 4) and np.isfinite(scores).all(), "complete finite score array"
    )
    require(
        np.array_equal(predictions, scores.argmax(axis=-1)),
        "prediction / first-index argmax mismatch",
    )
    truth = np.broadcast_to(np.arange(4), predictions.shape)
    correct = predictions == truth
    # Independently reconstruct every confusion cell from retained predictions.
    confusion = [
        [sum(int(predictions[s, r, a] == b) for s in range(14) for r in range(2)) for b in range(4)]
        for a in range(4)
    ]
    require(confusion == rule["confusion_counts"], "confusion does not match predictions")
    require(rule["counts"] == [28] * 4, "each prompted painter must have 28 images")
    recall = np.array([confusion[a][a] / 28 for a in range(4)])
    close(recall, rule["per_painter_recall"], "painter recall mismatch")
    close(recall.mean(), rule["macro_accuracy"], "macro accuracy mismatch")
    close(correct.mean(), rule["micro_accuracy"], "micro accuracy mismatch")
    close(correct.mean(axis=(1, 2)), rule["scene_accuracy"], "scene accuracy mismatch")
    require(np.array_equal(correct, rule["correct"]), "correctness mask mismatch")
    ties = (scores == scores.max(axis=-1, keepdims=True)).sum(axis=-1) > 1
    require(np.array_equal(ties, rule["top_ties"]), "tie mask mismatch")
    require(
        rule["tie_counts"] == dict(total=int(ties.sum()), per_scene=ties.sum(axis=(1, 2)).tolist()),
        "tie counts mismatch",
    )
    norms = np.asarray(rule["query_norms"])
    require(
        norms.shape == (14, 2, 4) and np.isfinite(norms).all() and (norms >= 0).all(),
        "query norm mismatch",
    )
    zero = norms == 0
    require(np.array_equal(zero, rule["zero_queries"]), "zero mask mismatch")
    require(
        rule["zero_query_counts"]
        == dict(total=int(zero.sum()), per_scene=zero.sum(axis=(1, 2)).tolist()),
        "zero counts mismatch",
    )
    return correct


def load():
    require(sha(BASE / "analysis.json") == ANALYSIS_SHA, "frozen result hash changed")
    require(sha(BASE / "inputs.json") == INPUT_SHA, "frozen input hash changed")
    data = json.loads((BASE / "analysis.json").read_text())
    inputs = json.loads((BASE / "inputs.json").read_text())
    require(
        data["inputs_sha256"] == INPUT_SHA and data["descriptive_only"],
        "analysis provenance mismatch",
    )
    require(
        data["axes"]["models"] == list(MODELS)
        and data["axes"]["artists"] == list(ARTISTS)
        and data["axes"]["rules"] == list(RULES),
        "analysis axes mismatch",
    )
    for path, expected in inputs["bindings"].items():
        local = (ROOT / path).resolve()
        require(
            local.is_relative_to(ROOT) and sha(local) == expected,
            f"frozen binding mismatch: {path}",
        )
    for rep in ("clip", "csd"):
        reference_g = rows(data, rep, "original", "primary")
        for view, target, _ in SETTINGS:
            current = rows(data, rep, view, target)
            expected_counts = [297, 106, 141, 105] if target == "primary" else [101, 36, 48, 36]
            require(
                group(data, rep, view, target)["counts"] == expected_counts,
                "reference census mismatch",
            )
            for model in MODELS:
                row = current[model]
                require(set(row["rules"]) == set(RULES), "all three rules must remain")
                correctness = {rule: verify_rule(row["rules"][rule]) for rule in RULES}
                require(
                    row["rules"][RULES[2]] == reference_g[model]["rules"][RULES[2]],
                    "G cannot be consolidated: full outputs differ by source view/target",
                )
                for key, rule in zip(PAIRS, RULES[1:]):
                    base, candidate = correctness[RULES[0]], correctness[rule]
                    paired = row[key]
                    for field, value in (
                        ("corrected_count", int(np.sum(candidate & ~base))),
                        ("newly_incorrect_count", int(np.sum(~candidate & base))),
                        ("unchanged_correct_count", int(np.sum(candidate & base))),
                        ("unchanged_incorrect_count", int(np.sum(~candidate & ~base))),
                    ):
                        require(paired[field] == value, f"paired {field} mismatch")
                    close(
                        candidate.mean() - base.mean(),
                        paired["accuracy_difference"],
                        "paired accuracy mismatch",
                    )
                    close(
                        candidate.mean(axis=(1, 2)) - base.mean(axis=(1, 2)),
                        paired["scene_accuracy_difference"],
                        "paired scene mismatch",
                    )
                require(len(row["folds"]) == 14, "complete held-scene folds required")
                for scene, fold in enumerate(row["folds"]):
                    require(
                        fold["held_out_scene"] == scene
                        and fold["train_scenes"] == [s for s in range(14) if s != scene]
                        and fold["training_image_count"] == 104,
                        "held-scene training census mismatch",
                    )
            for key in PAIRS:
                close(
                    np.mean([current[m][key]["accuracy_difference"] for m in MODELS]),
                    group(data, rep, view, target)["equal_configuration_mean_accuracy_difference"][
                        key
                    ],
                    "equal-configuration mean mismatch",
                )
    return data, inputs


def percent(value, signed=False, places=1):
    scaled = 100 * value
    if round(scaled, places) == 0:
        scaled = 0.0
    return f"${scaled:+.{places}f}$" if signed else f"${scaled:.{places}f}$"


def provenance(inputs):
    result = [
        "% Generated by paper/make_icml_transfer_tables.py; retained outcomes only.",
        f"% analysis_sha256: {ANALYSIS_SHA}",
        f"% inputs_sha256: {INPUT_SHA}",
        f"% generator_sha256: {sha(Path(__file__))}",
    ]
    result += [f"% bound_input_sha256 {p}: {v}" for p, v in sorted(inputs["bindings"].items())]
    return result


def captions_above(text):
    """Place each numbered caption above its table, following ICML convention."""

    def move(match):
        block = match.group()
        opening = re.match(r"\\begin\{table\}\[[^]]+\]", block).group()
        captions = re.findall(r"\\caption\{[^\n]+\}", block)
        labels = re.findall(r"\\label\{[^}]+\}", block)
        require(len(captions) == len(labels) == 1, "one caption and label per generated table")
        remainder = block[len(opening) :].replace(captions[0], "").replace(labels[0], "")
        return opening + "\n" + captions[0] + "\n" + labels[0] + "\n" + remainder

    return re.sub(r"\\begin\{table\}\[[^]]+\].*?\\end\{table\}", move, text, flags=re.S)


def main_table(data, inputs):
    lines = provenance(inputs) + [
        r"\begin{table}[t]\centering\footnotesize\setlength{\tabcolsep}{2pt}",
        r"\begin{tabularx}{\linewidth}{@{}X*{6}{>{\centering\arraybackslash}p{.095\linewidth}}@{}}",
        r"\toprule",
        r"& \multicolumn{3}{c}{CLIP} & \multicolumn{3}{c}{CSD}\\",
        r"\cmidrule(lr){2-4}\cmidrule(l){5-7}",
        r"Configuration & B & T & G & B & T & G\\\midrule",
    ]
    lookup = {rep: rows(data, rep, "original", "primary") for rep in ("clip", "csd")}
    for model, title in zip(MODELS, TITLES):
        cells = [
            percent(lookup[rep][model]["rules"][rule]["macro_accuracy"])
            for rep in ("clip", "csd")
            for rule in RULES
        ]
        lines.append(title + " & " + " & ".join(cells) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Held-scene prompt-name accuracy (\%), original sources and primary "
        r"references. B: reference prototypes; T: fixed common translation; G: "
        r"supervised generated prototypes. T and G train on the other 13 scenes, "
        r"excluding both held-out repeats. G uses painter labels and has more "
        r"information than T. Each configuration has 112 named images. GPT 2.5 "
        r"abbreviates GPT Image 2.5. These retrospective results concern prompt-name "
        r"recovery, not perceptual fidelity.}",
        r"\label{tab:transfer-main}\end{table}",
    ]
    return captions_above("\n".join(lines) + "\n")


def confusion_cell(rule, painter):
    counts = "/".join(str(v) for v in rule["confusion_counts"][painter])
    return rf"${counts}\mid {100 * rule['per_painter_recall'][painter]:.1f}$"


def confusion_table(data, view, target, title):
    lines = [
        r"\begin{table}[!htbp]\centering\small\setlength{\tabcolsep}{2pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xl*{4}{>{\centering\arraybackslash}p{.183\linewidth}}@{}}",
        r"\toprule",
        rf"\multicolumn{{6}}{{@{{}}l}}{{\textit{{{title}}}}}\\",
        r"Configuration & Rule & Monet & Sisley & Pissarro & C\'ezanne\\\midrule",
    ]
    for rep in ("clip", "csd"):
        lines.append(rf"\multicolumn{{6}}{{@{{}}l}}{{{rep.upper()}}}\\")
        current = rows(data, rep, view, target)
        for model, model_title in zip(MODELS, TITLES):
            for label, rule in zip(("B", "T"), RULES[:2]):
                cells = [confusion_cell(current[model]["rules"][rule], a) for a in range(4)]
                lines.append(
                    (model_title if label == "B" else "")
                    + " & "
                    + label
                    + " & "
                    + " & ".join(cells)
                    + r"\\"
                )
    lines += [
        r"\bottomrule\end{tabularx}",
        rf"\caption{{{title}: all baseline and translated confusion rows. "
        r"Each painter column is one prompted class: predicted counts in "
        r"Monet/Sisley/Pissarro/C\'ezanne order, followed by $\mid$ recall (\%). "
        r"Every four-count cell totals 28.}",
        rf"\label{{tab:transfer-confusions-{view}-{target}}}\end{{table}}",
    ]
    return lines


def appendix(data, inputs):
    lines = provenance(inputs) + [
        r"\clearpage\subsection{Complete held-scene transfer results}\label{app:transfer-results}",
        r"\begin{table}[!htbp]\centering\footnotesize\setlength{\tabcolsep}{3pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xlrrrrrrr@{}}\toprule",
        r"Configuration & Encoder & B (\%) & T (\%) & G (\%) & $T-B$ & C/H & $G-B$ & C/H\\\midrule",
    ]
    for view, target, title in SETTINGS:
        lines.append(rf"\multicolumn{{9}}{{@{{}}l}}{{\textit{{{title}}}}}\\")
        for rep in ("clip", "csd"):
            current = rows(data, rep, view, target)
            for model, name in zip(MODELS, TITLES):
                row = current[model]
                cells = [
                    name,
                    rep.upper(),
                    *[percent(row["rules"][rule]["macro_accuracy"]) for rule in RULES],
                ]
                for key in PAIRS:
                    pair = row[key]
                    cells += [
                        percent(pair["accuracy_difference"], True),
                        f"{pair['corrected_count']}/{pair['newly_incorrect_count']}",
                    ]
                lines.append(" & ".join(cells) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{All rules, configurations, encoders and reference settings. "
        r"Accuracies are macro averages over four equally sized painter groups "
        r"and equal micro accuracy (112 predictions per rule/configuration). "
        r"Differences are percentage points; C/H counts decisions corrected/newly "
        r"incorrect relative to B. Negative and unchanged outcomes are retained.}",
        r"\label{tab:transfer-all-accuracy}\end{table}",
        r"\clearpage",
        r"\subsection{Complete B/T confusions and painter recalls}",
    ]
    for index, (view, target, title) in enumerate(SETTINGS):
        if index:
            lines.append(r"\clearpage")
        lines.extend(confusion_table(data, view, target, title))
    lines += [
        r"\clearpage\subsection{Supervised context and configuration means}",
        r"B denotes normalized historical reference prototypes; T applies the fixed "
        r"unit-scale mean translation before reference scoring; G uses supervised "
        r"generated prototypes. Each held-out scene excludes both repeats from "
        r"training (104 training and eight test images per configuration). The "
        r"same 672 named images are reused across all settings. All quantities "
        r"come from the frozen retrospective transfer analysis; no additional "
        r"fit, tuning, selection or inferential test is introduced.",
        "",
        r"G is independent of the historical source view and target: it trains "
        r"only on generated images. The generator verifies exact equality of "
        r"its complete retained rule outputs across all four settings before "
        r"consolidating these confusions. Its accuracy is nevertheless repeated "
        r"in the complete table above. G is supervised context, not an "
        r"equal-information comparator for T.",
        "",
        r"\begin{table}[!htbp]\centering\small\setlength{\tabcolsep}{2pt}",
        r"\begin{tabularx}{\linewidth}{@{}X*{4}{>{\centering\arraybackslash}p{.18\linewidth}}@{}}\toprule",
        r"Configuration & Monet & Sisley & Pissarro & C\'ezanne\\\midrule",
    ]
    for rep in ("clip", "csd"):
        lines.append(rf"\multicolumn{{5}}{{@{{}}l}}{{{rep.upper()} / G}}\\")
        current = rows(data, rep, "original", "primary")
        for model, title in zip(MODELS, TITLES):
            lines.append(
                title
                + " & "
                + " & ".join(confusion_cell(current[model]["rules"][RULES[2]], a) for a in range(4))
                + r"\\"
            )
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{All G confusion counts and recalls. Cell format and fixed "
        r"painter order match the B/T tables; each cell totals 28 test images.}",
        r"\label{tab:transfer-g-confusions}\end{table}",
        r"\begin{table}[!htbp]\centering\small\setlength{\tabcolsep}{5pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xlrr@{}}\toprule",
        r"Reference setting & Encoder & Mean $T-B$ (pp) & Mean $G-B$ (pp)\\\midrule",
    ]
    for view, target, title in SETTINGS:
        for rep in ("clip", "csd"):
            means = group(data, rep, view, target)["equal_configuration_mean_accuracy_difference"]
            lines.append(
                title
                + " & "
                + rep.upper()
                + " & "
                + " & ".join(percent(means[k], True, 2) for k in PAIRS)
                + r"\\"
            )
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Equal-weight means over the six recorded configurations. "
        r"These are descriptive summaries of this set, not population estimates.}",
        r"\label{tab:transfer-means}\end{table}",
        "",
        r"The reference targets and generated observations are reused; overlapping "
        r"training folds, related CLIP/CSD encoders and the previously used "
        r"development panel do not supply independent replications. Translation "
        r"changes decision intercepts while leaving centered painter contrasts "
        r"unchanged within a fold. The fit contains no free/generic controls and "
        r"does not identify a named-minus-generic causal component. The full "
        r"hash-bound record retains predictions, raw margins, translation and "
        r"prototype norms, and deterministic first-index tie/zero-query accounting.",
    ]
    for rep in ("clip", "csd"):
        lines += [
            r"\clearpage",
            rf"\subsection{{{rep.upper()}: all paired scene differences}}",
            r"Entries are differences in correct predictions among the eight "
            r"held-out images of each scene. Multiply by 12.5 for percentage "
            r"points. A zero records no net accuracy change, not necessarily "
            r"identical predictions. Scene indices are the fixed manifest indices.",
            r"\begin{table}[!htbp]\centering\footnotesize\setlength{\tabcolsep}{2pt}",
            r"\begin{tabularx}{\linewidth}{@{}ll*{14}{>{\centering\arraybackslash}X}@{}}\toprule",
            "Configuration & Pair & " + " & ".join(str(i) for i in range(14)) + r"\\\midrule",
        ]
        for view, target, title in SETTINGS:
            lines.append(rf"\multicolumn{{16}}{{@{{}}l}}{{\textit{{{title}}}}}\\")
            current = rows(data, rep, view, target)
            for model, name in zip(MODELS, TITLES):
                for key, label in zip(PAIRS, ("T-B", "G-B")):
                    values = 8 * np.array(current[model][key]["scene_accuracy_difference"])
                    close(values, np.round(values), "scene deltas must be integer decisions")
                    cells = [f"${int(round(v)):+d}$" if v else "$0$" for v in values]
                    lines.append(
                        (name if label == "T-B" else "")
                        + f" & ${label}$ & "
                        + " & ".join(cells)
                        + r"\\"
                    )
        lines += [
            r"\bottomrule\end{tabularx}",
            rf"\caption{{{rep.upper()}: complete paired scene differences for T and G "
            r"relative to B, including every adverse or zero scene outcome. "
            r"These descriptive folds are not independent trials or uncertainty intervals.}",
            rf"\label{{tab:transfer-scenes-{rep}}}\end{{table}}",
        ]
    return captions_above("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, inputs = load()
    outputs = {
        ROOT / "paper/icml_transfer_table.tex": main_table(data, inputs),
        ROOT / "paper/icml_transfer_results.tex": appendix(data, inputs),
    }
    for path, content in outputs.items():
        if args.check:
            require(
                path.is_file() and path.read_text() == content, f"TeX replay mismatch: {path.name}"
            )
        else:
            path.write_text(content)
    print(
        "Transfer tables: 144 rule summaries / 16,128 reused-setting predictions verified; "
        + ("exact TeX replay passed." if args.check else "generated TeX written.")
    )


if __name__ == "__main__":
    main()
