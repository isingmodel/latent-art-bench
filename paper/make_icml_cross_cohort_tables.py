"""Render all frozen SD-Turbo decomposition summaries, without refitting.

--check verifies anchored source hashes, all 25 deletion records/ranges and exact
TeX replay. Only paper/icml_cross_cohort_results.tex is written by default.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/painter_cross_cohort_v1"
OUTPUT = ROOT / "paper/icml_cross_cohort_results.tex"
INPUT_SHA = "94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693"
ANALYSIS_SHA = "9488dfafa5779b8b065cc756804e67ad64c2841a5c62c2f9b0105f8fef13973e"
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
NAMES = ("Monet", "Sisley", "Pissarro", r"C\'ezanne")
FAMILIES = ("all31", "color", "spatial", "texture")
LABELS = ("All 31", "Color (11)", "Spatial (8)", "Texture (12)")
TARGETS = ("pooled", "within_scene")
TARGET_LABELS = ("Pooled", "Within scene")
METRICS = ("C", "L", "N", "T", "common_fraction", "beta", "D")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected, message):
    if actual is None or expected is None:
        require(actual is expected, message)
    else:
        require(math.isfinite(actual) and math.isfinite(expected), "nonfinite numeric result")
        require(math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-11), message)


def verify_summary(summary):
    require(set(summary) == set(FAMILIES), "all four fixed coordinate views required")
    for family in FAMILIES:
        data = summary[family]
        for target in TARGETS:
            row = data[target]
            close(row["N"], row["C"] + row["L"], "N decomposition")
            close(row["T"], row["C"] - row["L"], "common-majority contrast")
            close(
                row["common_fraction"],
                row["C"] / row["N"] if row["N"] > 0 else None,
                "common fraction",
            )
            require(
                row["common_majority_descriptive"] == (row["N"] > 0 and row["T"] > 0),
                "descriptive majority flag",
            )
            close(
                row["D"],
                row["L"] / row["H"] - 2 * row["beta"] + 1 if row["H"] > 0 else None,
                "D identity",
            )
        close(data["pooled"]["H"], data["within_scene"]["H"], "fixed reference denominator")
        close(data["pooled"]["beta"], data["within_scene"]["beta"], "linear alignment target")
        expected_gap = (
            data["within_scene"]["D"] - data["pooled"]["D"]
            if data["pooled"]["D"] is not None
            else None
        )
        close(data["scene_minus_pooled_D"], expected_gap, "scene-minus-pooled error")
        scenes = data["scene_records"]
        require([r["scene_index"] for r in scenes] == list(range(16)), "all scene records required")
        for key in ("C", "L", "N", "T", "beta", "D"):
            values = [r[key] for r in scenes]
            expected = sum(values) / 16 if all(v is not None for v in values) else None
            close(data["within_scene"][key], expected, "within-scene scalar averaging")
        pairs = data["pairs"]
        require(len(pairs) == 6, "all six pair results required")
        for row, expected in zip(pairs, itertools.combinations(ARTISTS, 2)):
            require(row["painters"] == list(expected), "pair identities/order changed")
            h = row["reference_squared_distance"]
            require(math.isfinite(h) and h >= 0, "invalid pair denominator")
            if h == 0:
                require(
                    row["aligned_amplitude"] is None
                    and row["scene_D"] is None
                    and row["reason"] == "zero_reference_pair_distance",
                    "undefined pair denominator must be explicit",
                )
            else:
                require(
                    all(math.isfinite(row[key]) for key in ("aligned_amplitude", "scene_D"))
                    and row["reason"] is None,
                    "complete finite pair outputs required",
                )
    for target in TARGETS:
        for key in ("C", "L", "N", "T", "H"):
            close(
                summary["all31"][target][key],
                sum(summary[family][target][key] for family in FAMILIES[1:]),
                "coordinate-family additivity",
            )


def load():
    require(sha(BASE / "inputs.json") == INPUT_SHA, "frozen input hash changed")
    require(sha(BASE / "analysis.json") == ANALYSIS_SHA, "frozen result hash changed")
    inputs = json.loads((BASE / "inputs.json").read_text())
    data = json.loads((BASE / "analysis.json").read_text())
    receipt = json.loads((BASE / "result_receipt.json").read_text())
    require(
        receipt["inputs_sha256"] == INPUT_SHA and receipt["analysis_sha256"] == ANALYSIS_SHA,
        "result receipt binding changed",
    )
    require(
        data["inputs_sha256"] == INPUT_SHA and data["study"] == "painter_cross_cohort_v1",
        "analysis provenance changed",
    )
    for item in inputs["bindings"]:
        local = (ROOT / item["path"]).resolve()
        require(
            local.is_relative_to(ROOT) and sha(local) == item["sha256"],
            "bound input changed: " + item["path"],
        )
    require(
        data["blocks"] == 25 and data["scenes"] == 16 and data["arms"] == ["artist_free", *ARTISTS],
        "finite census changed",
    )
    verify_summary(data["families"])
    deletions = data["leave_one_block_out"]
    require([row["block"] for row in deletions] == list(range(25)), "all 25 deletions required")
    for row in deletions:
        verify_summary(row["families"])
        for family in FAMILIES:
            close(
                row["families"][family]["pooled"]["H"],
                data["families"][family]["pooled"]["H"],
                "reference denominator changed on deletion",
            )
            for pair, full in zip(
                row["families"][family]["pairs"], data["families"][family]["pairs"]
            ):
                close(
                    pair["reference_squared_distance"],
                    full["reference_squared_distance"],
                    "pair denominator changed on deletion",
                )
    for family in FAMILIES:
        for target in TARGETS:
            for metric in METRICS:
                pairs = [(r["block"], r["families"][family][target][metric]) for r in deletions]
                values = [v for _, v in pairs if v is not None]
                expected = dict(
                    minimum=min(values) if values else None,
                    maximum=max(values) if values else None,
                    available=len(values),
                    unavailable_blocks=[b for b, v in pairs if v is None],
                )
                require(
                    data["sensitivity_ranges"][family][target][metric] == expected,
                    "range differs from the complete 25-deletion census",
                )
    return data


def number(value):
    return "--" if value is None else f"${value:.3f}$"


def interval(row):
    if row["minimum"] is None:
        return "--"
    result = f"$[{row['minimum']:.3f}, {row['maximum']:.3f}]$"
    if row["available"] != 25:
        result += f" ({row['available']}/25)"
    return result


def table_open(caption, label, spec, headings):
    return [
        r"\begin{table}[!htbp]",
        "\\caption{" + caption + "}",
        "\\label{" + label + "}",
        r"\centering\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\linewidth}{@{}" + spec + r"@{}}\toprule",
        " & ".join(headings) + r"\\\midrule",
    ]


def table_close():
    return [r"\bottomrule\end{tabularx}\end{table}"]


def render(data):
    lines = [
        "% Generated from frozen retrospective SD-Turbo results; no new analysis.",
        f"% analysis_sha256: {ANALYSIS_SHA}",
        f"% inputs_sha256: {INPUT_SHA}",
        r"\subsection{Complete separate-collection summaries}",
    ]
    lines += table_open(
        r"All fixed SD-Turbo decomposition summaries. Pooled averages each condition over the "
        r"16 scenes before cross-block products; within scene averages the resulting 16 scalar "
        r"summaries. $C$ is common additional naming change beyond generic oil painting, "
        r"$L$ is centered between-name change, $N=C+L$ and $T=C-L$. "
        r"Positive $N$ and $T$ define a descriptive common majority. Texture fails this "
        r"criterion under both targets. The ratio, alignment $\beta$ and normalized error $D$ "
        r"retain their signed values; none is a perceptual-fidelity score.",
        "tab:cross-cohort-components",
        "Xlrrrrrrr",
        ["Coordinates", "Target", "$C$", "$L$", "$N$", "$T$", "$C/N$", r"$\beta$", "$D$"],
    )
    for family, label in zip(FAMILIES, LABELS):
        for target, title in zip(TARGETS, TARGET_LABELS):
            row = data["families"][family][target]
            lines.append(" & ".join([label, title, *[number(row[key]) for key in METRICS]]) + r"\\")
        if family != FAMILIES[-1]:
            lines.append(r"\addlinespace[2pt]")
    lines += table_close()
    energies = ", ".join(
        f"{label}: ${data['families'][family]['pooled']['H']:.6f}$"
        for family, label in zip(FAMILIES, LABELS)
    )
    gaps = ", ".join(
        f"{label}: ${data['families'][family]['scene_minus_pooled_D']:.6f}$"
        for family, label in zip(FAMILIES, LABELS)
    )
    lines += [
        r"The fixed historical reference energy $H$ is " + energies + ".",
        r"The signed within-scene minus pooled $D$ difference is " + gaps + ".",
    ]
    lines += table_open(
        r"All six painter pairs in every coordinate view. Pair denominator "
        r"$H_{aj}=\|\mu_a-\mu_j\|^2$ uses that view's historical means. "
        r"Aligned amplitude is $\langle\overline{z_a-z_j},\mu_a-\mu_j\rangle/H_{aj}$. "
        r"Pair $D_{\rm scene}$ averages cross-block squared-error estimates within scenes "
        r"and divides by $H_{aj}$. Negative amplitudes are retained. "
        r"No pair hypothesis tests or perceptual-fidelity claims are made.",
        "tab:cross-cohort-pairs",
        "lXrrr",
        ["Coordinates", "Pair", "$H_{aj}$", "Amplitude", r"$D_{\rm scene}$"],
    )
    for family, label in zip(FAMILIES, LABELS):
        for row, (first, second) in zip(
            data["families"][family]["pairs"], itertools.combinations(NAMES, 2)
        ):
            lines.append(
                " & ".join(
                    [
                        label,
                        first + "--" + second,
                        number(row["reference_squared_distance"]),
                        number(row["aligned_amplitude"]),
                        number(row["scene_D"]),
                    ]
                )
                + r"\\"
            )
        if family != FAMILIES[-1]:
            lines.append(r"\addlinespace[3pt]")
    lines += table_close() + [r"\FloatBarrier"]
    for keys, label, headings, caption in (
        (
            ("C", "L", "N", "T"),
            "tab:cross-cohort-delete-energy",
            ["$C$", "$L$", "$N$", "$T$"],
            r"Finite ranges over all 25 delete-one-block analyses for the unnormalized "
            r"components. Each recomputation uses the remaining $K=24$ complete paired-seed "
            r"blocks and all 16 scenes. These are stability ranges, not confidence intervals. "
            r"All 25 values enter each displayed range; "
            r"negative texture contrasts remain negative.",
        ),
        (
            ("common_fraction", "beta", "D"),
            "tab:cross-cohort-delete-normalized",
            ["$C/N$", r"$\beta$", "$D$"],
            r"Finite ranges over the same complete 25 delete-one-block analyses for normalized "
            r"summaries. The 649-work historical target, 221-work development scaling and "
            r"view-specific denominators stay fixed. Every displayed range uses all 25 values. "
            r"These ranges quantify deletion sensitivity and provide no coverage guarantee.",
        ),
    ):
        lines += table_open(
            caption, label, "Xl" + "r" * len(keys), ["Coordinates", "Target", *headings]
        )
        for family, title in zip(FAMILIES, LABELS):
            for target, target_title in zip(TARGETS, TARGET_LABELS):
                ranges = data["sensitivity_ranges"][family][target]
                require(
                    all(ranges[key]["available"] == 25 for key in keys),
                    "caption requires 25 available deletions per range",
                )
                lines.append(
                    " & ".join([title, target_title, *[interval(ranges[key]) for key in keys]])
                    + r"\\"
                )
            if family != FAMILIES[-1]:
                lines.append(r"\addlinespace[2pt]")
        lines += table_close()
    lines += [
        r"\FloatBarrier",
        r"The retained numeric record includes all 25 individual deletion results, "
        r"all 16 scene records and full-precision endpoints. "
        r"These generated tables are checked by "
        r"\texttt{python paper/make\_icml\_cross\_cohort\_tables.py --check}; "
        r"the check verifies frozen hashes and recomputes every displayed range "
        r"from the complete deletion inventory.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render(load())
    if args.check:
        require(OUTPUT.read_text() == content, "generated cross-cohort TeX differs")
        print(
            "Cross-cohort tables: 8 target rows, 24 pair rows "
            "and 56 complete deletion ranges verified."
        )
    else:
        OUTPUT.write_text(content)


if __name__ == "__main__":
    main()
