"""Render descriptive learned-audit tables from the complete, bound analysis.

Run with ``uv run --locked python paper/make_icml_learned_tables.py``.
``--check`` verifies input hashes and exact TeX equality without writing files.
No inference, image access, outcome selection, or changes to frozen inputs occur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "reports/painter_learned_audit_v1/analysis.json"
HAND_ANALYSIS = ROOT / "reports/painter_specificity_review_v3/analysis.json"
HAND_SHA = "79fa5ca28900e852c072e2a52d35f3cb400ee053935d857729b4ad4aa3bc542c"
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
    "GPT Image 2.5 Flare",
    "GPT Image 2.5 Sunburst",
    "Nano Banana 2",
    "FLUX.2 Max",
)
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
TARGET_COUNTS = {"primary": [297, 106, 141, 105], "development": [101, 36, 48, 36]}
COUNTS = dict(development=221, features=768, generated=1008, reference=649, repeats=2, scenes=14)
OUTPUTS = (ROOT / "paper/icml_learned_table.tex", ROOT / "paper/icml_learned_results.tex")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fmt(value, *, percent=False):
    """Retain signed/unbounded estimates; only null values become dashes."""
    if value is None:
        return "--"
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"invalid numerical table entry: {value!r}")
    digits, scale = (1, 100) if percent else (3, 1)
    rendered = f"{scale * value:.{digits}f}"
    if float(rendered) == 0:
        rendered = f"{0:.{digits}f}"
    return f"${rendered}$"


def rows_by_model(rows):
    if len(rows) != len(MODELS) or {r["model"] for r in rows} != set(MODELS):
        raise ValueError("expected exactly one row for each requested configuration")
    return {r["model"]: r for r in rows}


def monet_sisley(row):
    matches = [r for r in row["painter_pairs"] if r["artists"] == list(ARTISTS[:2])]
    if len(matches) != 1:
        raise ValueError("expected one explicitly labeled Monet--Sisley pair")
    return matches[0]["beta"]


def gain_share(row, baseline="generic"):
    return row["prototype"]["common_vs_labeled_prototype_gain"][f"named_minus_{baseline}"][
        "common_fraction"
    ]


def load_inputs():
    data = json.loads(ANALYSIS.read_text())
    hand = json.loads(HAND_ANALYSIS.read_text())
    if sha(HAND_ANALYSIS) != HAND_SHA:
        raise ValueError("frozen hand-feature review-v3 analysis hash changed")
    if set(data) != {"bindings", "clip", "csd"}:
        raise ValueError("the complete two-representation analysis is required")
    required_bindings = {
        "reports/painter_learned_audit_v1/embeddings_clip.npz",
        "reports/painter_learned_audit_v1/embeddings_csd.npz",
        "reports/painter_learned_audit_v1/extraction_clip.json",
        "reports/painter_learned_audit_v1/extraction_csd.json",
        "reports/painter_learned_audit_v1/inputs.json",
        "src/latent_art_bench/painter_learned_analysis_v1.py",
        "src/latent_art_bench/painter_learned_audit_v1.py",
        "studies/painter_learned_audit_v1/PLAN.md",
    }
    if not required_bindings <= set(data["bindings"]):
        raise ValueError("missing learned-analysis input bindings")
    for path, expected in data["bindings"].items():
        local = (ROOT / path).resolve()
        if not local.is_relative_to(ROOT) or sha(local) != expected:
            raise ValueError(f"learned-analysis binding mismatch: {path}")
    for representation in ("clip", "csd"):
        if set(data[representation]) != {"original", "audited_region"}:
            raise ValueError("both source views must be present")
        for view in data[representation].values():
            if view["counts"] != COUNTS or view["descriptive_only"] is not True:
                raise ValueError("unexpected cohort or inferential status")
            if view["axes"]["models"] != list(MODELS):
                raise ValueError("unexpected requested-configuration axis")
            if view["axes"]["artists"] != list(ARTISTS):
                raise ValueError("unexpected painter axis")
            rows_by_model(view["shared_change"])
            for target, counts in TARGET_COUNTS.items():
                if view["targets"][target]["counts"] != counts:
                    raise ValueError("unexpected finite-reference membership")
                for row in rows_by_model(view["targets"][target]["models"]).values():
                    monet_sisley(row)
                    if len(row["painter_pairs"]) != 6:
                        raise ValueError("incomplete painter-pair analysis")
                    if row["recognition"]["counts"] != [28] * 4:
                        raise ValueError("unexpected named-generation recognition cohort")
    if hand["views"]["full_frame"]["reference_counts"] != TARGET_COUNTS["primary"]:
        raise ValueError("hand-feature table must use the same primary membership")
    rows_by_model(hand["views"]["full_frame"]["models"])
    return data, hand


def provenance(data):
    comments = [
        "% Generated by paper/make_icml_learned_tables.py; do not edit numerical cells.",
        "% Descriptive same-image audit; no cross-representation perceptual ranking.",
        f"% analysis_sha256: {sha(ANALYSIS)}",
        f"% hand_review_v3_sha256: {HAND_SHA}",
    ]
    comments.extend(
        f"% input_sha256 {path}: {value}" for path, value in sorted(data["bindings"].items())
    )
    return comments


def captions_above_tables(lines):
    """Apply ICML's table-caption placement without changing table contents."""
    output = []
    block = None
    for line in lines:
        if line.startswith(r"\begin{table}") or line.startswith(r"\begin{table*}"):
            if block is not None:
                raise ValueError("nested generated table")
            block = [line]
        elif block is not None:
            block.append(line)
            if line in (r"\end{table}", r"\end{table*}"):
                caption = [v for v in block if v.startswith(r"\caption{")]
                labels = [v for v in block if v.startswith(r"\label{")]
                if len(caption) != 1 or len(labels) != 1:
                    raise ValueError("expected one caption and label per generated table")
                output.extend([block[0], *caption, *labels])
                output.extend(v for v in block[1:] if v not in caption + labels)
                block = None
        else:
            output.append(line)
    if block is not None:
        raise ValueError("unclosed generated table")
    return output


def main_table(data, hand):
    learned = {
        rep: rows_by_model(data[rep]["original"]["targets"]["primary"]["models"])
        for rep in ("clip", "csd")
    }
    hand_rows = rows_by_model(hand["views"]["full_frame"]["models"])
    lines = provenance(data) + [
        r"\begin{table*}[t]",
        r"\centering\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\textwidth}{@{}X*{7}{>{\centering\arraybackslash}p{.081\textwidth}}@{}}",
        r"\toprule",
        r"& \multicolumn{3}{c}{Monet--Sisley $\widehat\beta$} "
        r"& \multicolumn{2}{c}{\shortstack{Common prototype\\gain (\%)}} "
        r"& \multicolumn{2}{c}{\shortstack{Macro accuracy\\(\%)}}\\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}\cmidrule(l){7-8}",
        r"Requested configuration & Hand-31 & CLIP & CSD & CLIP & CSD & CLIP & CSD\\",
        r"\midrule",
    ]
    for model, title in zip(MODELS, TITLES):
        clip, csd = learned["clip"][model], learned["csd"][model]
        values = [
            fmt(hand_rows[model]["monet_sisley"]["beta"]),
            fmt(monet_sisley(clip)),
            fmt(monet_sisley(csd)),
            fmt(gain_share(clip), percent=True),
            fmt(gain_share(csd), percent=True),
            fmt(clip["recognition"]["macro_accuracy"], percent=True),
            fmt(csd["recognition"]["macro_accuracy"], percent=True),
        ]
        lines.append(title + " & " + " & ".join(values) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\caption{Same-image descriptive comparison using 649 primary references. "
        r"Hand-31 uses full-frame features; CLIP and CSD use their native center crops of "
        r"the original sources. Pair $\widehat\beta=1$ matches each representation's "
        r"Monet--Sisley reference amplitude. Common prototype gain is the common "
        r"contribution divided by named-minus-generic diagonal prototype gain "
        r"(Eq.~\ref{eq:learned-prototype-gain}), not a squared-change share. "
        r"Accuracy uses unit-normalized prototypes to classify the 112 named images "
        r"per configuration (four painters; 25\% chance under uniform guessing). "
        r"All cells are descriptive points; representations do not share a perceptual scale.}",
        r"\label{tab:learned-main}",
        r"\end{table*}",
    ]
    return "\n".join(captions_above_tables(lines)) + "\n"


def supplemental_tables(data):
    lines = provenance(data)
    lines += [
        r"\subsection{Complete learned-audit descriptive summaries}",
        r"Tables~\ref{tab:learned-clip-complete} and~\ref{tab:learned-csd-complete} "
        r"retain all six requested configurations, both source views and both finite "
        r"reference targets. Original sources undergo the encoder's native center crop; "
        r"audited regions first replace the recorded 90 primary and 41 development "
        r"source regions. Development targets reuse the existing 221-work panel. "
        r"Generated images are identical across these sensitivities. All values are "
        r"descriptive points, with no confidence intervals or perceptual ranking.",
    ]
    for rep, title in (("clip", "CLIP"), ("csd", "CSD")):
        lines += [
            r"\begin{table}[htbp]",
            r"\centering\small\setlength{\tabcolsep}{4pt}",
            r"\begin{tabularx}{\linewidth}{@{}X*{8}{>{\centering\arraybackslash}p{.072\linewidth}}@{}}",
            r"\toprule",
            r"& \multicolumn{3}{c}{Centered agreement} & "
            r"\multicolumn{1}{c}{Accuracy} & "
            r"\multicolumn{2}{c}{\shortstack{Common gain\\(\%)}} & "
            r"\multicolumn{2}{c}{\shortstack{Common change\\(\%)}}\\",
            r"\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-7}\cmidrule(l){8-9}",
            r"Requested configuration & $\widehat\beta$ & $\widehat D$ "
            r"& MS $\widehat\beta$ & Macro (\%) & Free & Generic & Free & Generic\\",
            r"\midrule",
        ]
        for view, view_title in (
            ("original", "Original sources"),
            ("audited_region", "Audited regions"),
        ):
            shared = rows_by_model(data[rep][view]["shared_change"])
            for target, target_title in (("primary", "Primary"), ("development", "Development")):
                count = sum(TARGET_COUNTS[target])
                lines.append(
                    rf"\multicolumn{{9}}{{@{{}}l}}{{\textit{{{view_title}; "
                    rf"{target_title} target, $n={count}$}}}}\\[2pt]"
                )
                rows = rows_by_model(data[rep][view]["targets"][target]["models"])
                for model, model_title in zip(MODELS, TITLES):
                    row = rows[model]
                    values = [
                        fmt(row["centered"]["beta"]),
                        fmt(row["centered"]["d"]),
                        fmt(monet_sisley(row)),
                        fmt(row["recognition"]["macro_accuracy"], percent=True),
                        fmt(gain_share(row, "free"), percent=True),
                        fmt(gain_share(row, "generic"), percent=True),
                        *[
                            fmt(
                                shared[model][f"named_minus_{baseline}"]["scene_averaged"][
                                    "common_fraction"
                                ],
                                percent=True,
                            )
                            for baseline in ("free", "generic")
                        ],
                    ]
                    lines.append(model_title + " & " + " & ".join(values) + r"\\")
                lines.append(r"\addlinespace[4pt]")
        lines += [
            r"\bottomrule\end{tabularx}",
            rf"\caption{{{title}: all source-view and reference-target sensitivities. "
            r"$\widehat\beta$ and $\widehat D$ use all four centered painter contrasts; "
            r"MS restricts alignment to Monet--Sisley. Macro accuracy classifies "
            r"generated named images using normalized prototypes. Common gain is "
            r"the common fraction of the diagonal prototype-similarity gain relative "
            r"to the indicated control. Common change is the common fraction of "
            r"scene-averaged, cross-repeat squared feature change relative to that "
            r"control. Common change depends only on generated images and therefore "
            r"repeats across source-view/target panels. Fractions are not clipped; "
            r"a nonpositive denominator would be shown as --.}",
            rf"\label{{tab:learned-{rep}-complete}}",
            r"\end{table}",
        ]
    return "\n".join(captions_above_tables(lines)) + "\n"


def build():
    data, hand = load_inputs()
    return dict(zip(OUTPUTS, (main_table(data, hand), supplemental_tables(data))))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="compare exact regenerated TeX; do not write"
    )
    args = parser.parse_args()
    outputs = build()
    if args.check:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_text() != expected:
                raise SystemExit(f"table replay mismatch: {path.relative_to(ROOT)}")
        print("Learned tables: input bindings and exact TeX replay verified.")
    else:
        for path, content in outputs.items():
            path.write_text(content)
            print(f"Wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
