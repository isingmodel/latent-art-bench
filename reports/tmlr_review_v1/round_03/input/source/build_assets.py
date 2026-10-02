"""Build the TMLR manuscript's generated tables and figure from retained analyses.

Run ``uv run --locked python paper/tmlr/build_assets.py`` to write the files in
``paper/tmlr/generated/``. ``--check`` writes nothing: it verifies the recorded
input hashes, exact equality of every generated file, and that each number quoted
in the manuscript prose (``CLAIMS``) matches its source analysis.

Inputs are completed, hash-recorded analysis outputs. No images, model requests,
new inference or outcome selection are involved.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "generated"
MANUSCRIPT = (HERE / "main.tex", HERE / "appendix.tex")

INPUTS = {
    "review_v3": (
        "reports/painter_specificity_review_v3/analysis.json",
        "79fa5ca28900e852c072e2a52d35f3cb400ee053935d857729b4ad4aa3bc542c",
    ),
    "review_v1": (
        "reports/painter_specificity_review_v1/analysis.json",
        "2fabb78e15dfcc7b027a73170f6ad0c87af0196c754b4e6f45275269c2c961e2",
    ),
    "models": (
        "reports/painter_specificity_v2/psv2-20260911/models.csv",
        "eed121f77626d8a37235b5bb19e370e3fbd7b6bae44b559d1b866e27e9cac41c",
    ),
    "contrasts": (
        "reports/painter_specificity_v2/psv2-20260911/model_contrasts.csv",
        "0d0b722750e657b83658ccffbc7cb093d7b0ae577896904c45c02ababe31665b",
    ),
    "learned": (
        "reports/painter_learned_audit_v1/analysis.json",
        "06c77de4be133afc203dda122b2816d4f866e1389999f18bc94b3d9c668f28f7",
    ),
    "transfer": (
        "reports/painter_prototype_transfer_v1/analysis.json",
        "e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448",
    ),
    "cross": (
        "reports/painter_cross_cohort_v1/analysis.json",
        "9488dfafa5779b8b065cc756804e67ad64c2841a5c62c2f9b0105f8fef13973e",
    ),
    "quality": (
        "reports/painter_reference_quality_v1/analysis.json",
        "089f636335129d6377328088ccc9fdc763488aba2a88463939322326707052b4",
    ),
    "covariance": (
        "reports/painter_repeat_covariance_v1/analysis.json",
        "e5031ccad955b289b0d8dec110e8ee6b2ec39b43dfd8a6f2e150cc1dea1ce0c9",
    ),
    "diagnostics": (
        "reports/painter_tmlr_diagnostics_v1/analysis.json",
        "76792fa35f90e3d8fec1a75b0eec27d69cac14ed875fce8b64096b8e2525a4d4",
    ),
    "diagnostics2": (
        "reports/painter_tmlr_diagnostics_v2/analysis.json",
        "bed891f767a98f4b281b6783b1021956f4d2c3ff80becbf6b2693ee45987ef1a",
    ),
    "primary": (
        "data/manifests/painter_specificity_v2/psv2-20260911/analysis.json",
        "c1d21b16f840a10fd253c1d558743a09671acf3d4e48601ddcc96625a5a90be0",
    ),
    "requests": (
        "data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl",
        "0aa60f491be08dbd48f1f018e225b22bcae2aacd724abf3371a6312d59acc679",
    ),
}

STYLE = json.loads((HERE / "STYLE_PROVENANCE.json").read_text())["sha256"]
STATIC_FIGURES = json.loads((HERE / "figures/PROVENANCE.json").read_text())["files"]

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
SHORT = ("GPT Image 1", "GPT Image 2", "Flare", "Sunburst", "Nano Banana 2", "FLUX.2 Max")
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
PAINTERS = ("Monet", "Sisley", "Pissarro", "C\\'ezanne")
CLAUSES = {
    "free": "",
    "generic": "Render as an oil painting. ",
    "claude_monet": "Render as an oil painting in the style of Claude Monet. ",
    "alfred_sisley": "Render as an oil painting in the style of Alfred Sisley. ",
    "camille_pissarro": "Render as an oil painting in the style of Camille Pissarro. ",
    "paul_cezanne": "Render as an oil painting in the style of Paul Cezanne. ",
}
SUFFIX = " No text or frame."
BLUE, ORANGE = "#2a78d6", "#eb6834"  # validated categorical slots 1-2 (light surface)
INK, MUTED = "#0b0b0b", "#52514e"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"check failed: {message}")


def f3(value: float) -> str:
    require(math.isfinite(value), f"non-finite value {value!r}")
    text = f"{value:.3f}"
    return "0.000" if float(text) == 0 else text


def f2(value: float) -> str:
    return f"{value:.2f}"


def pct(value: float, places: int = 1) -> str:
    return f"{100 * value:.{places}f}"


def signed_pct(value: float) -> str:
    text = f"{100 * value:+.1f}"
    return text.replace("-", "$-$") if text.startswith("-") else text


def interval(pair) -> str:
    low, high = pair
    return f"[{f3(low)}, {f3(high)}]"


def parse_interval(text: str) -> tuple[float, float]:
    low, high = json.loads(text)
    return float(low), float(high)


def m3(value: float) -> str:
    """Three decimals with a typeset minus sign for prose."""
    text = f3(value)
    return f"$-${text[1:]}" if text.startswith("-") else text


def span(values, fmt, sep="--") -> str:
    return f"{fmt(min(values))}{sep}{fmt(max(values))}"


# ---------------------------------------------------------------------------
# Loading


def load_inputs(verify: bool) -> dict:
    data = {}
    for key, (rel, expected) in INPUTS.items():
        path = ROOT / rel
        require(path.exists(), f"missing input {rel}; run `make restore-analysis` first")
        if verify:
            require(sha256(path) == expected, f"input hash changed: {rel}")
        if rel.endswith(".json"):
            data[key] = json.loads(path.read_text())
        elif rel.endswith(".csv"):
            data[key] = list(csv.DictReader(io.StringIO(path.read_text())))
        else:
            data[key] = [json.loads(line) for line in path.read_text().splitlines() if line]
    return data


def by_model(rows, key="model", values=MODELS):
    lookup = {row[key]: row for row in rows}
    require(set(values) <= set(lookup), f"missing models in {sorted(lookup)}")
    return [lookup[m] for m in values]


def scenes_from_requests(requests) -> list[dict]:
    require(len(requests) == 1008, "expected 1,008 requests")
    briefs: dict[int, tuple[str, str]] = {}
    for row in requests:
        prompt = row["payload"]["prompt"]
        clause = CLAUSES[row["arm"]]
        require(prompt.startswith(clause) and prompt.endswith(SUFFIX), f"template: {row['id']}")
        brief = prompt[len(clause) : -len(SUFFIX)]
        previous = briefs.setdefault(row["scene"], (brief, row["content"]))
        require(previous == (brief, row["content"]), f"scene text differs: {row['id']}")
    cells = {(r["model"].split("/")[-1], r["scene"], r["arm"], r["repeat"]) for r in requests}
    require(len(cells) == 1008, "design cells are not unique")
    return [dict(index=k, brief=v[0], content=v[1]) for k, v in sorted(briefs.items())]


# ---------------------------------------------------------------------------
# Derived quantities


def hand_decomposition(data) -> list[dict]:
    h = data["review_v1"]["content"]["primary_h"]
    rows = []
    for record in by_model(data["review_v3"]["views"]["full_frame"]["models"]):
        avg = record["scene_averaged"]
        ident = avg["common_shift_identity"]
        free, generic = avg["named_minus_free"], avg["named_minus_generic"]
        require(abs(free["specific"] - generic["specific"]) < 1e-9, "B must not depend on baseline")
        deletion = record["scene_deletion_summaries"]
        rows.append(
            dict(
                model=record["model"],
                H=h,
                G=ident["generic_component"],
                N=ident["additional_naming_component"],
                I=ident["signed_interaction"],
                C=ident["combined_common"],
                B=free["specific"],
                share_free=free["shared_fraction"],
                share_generic=generic["shared_fraction"],
                range_free=deletion["named_minus_free"]["range"],
                range_generic=deletion["named_minus_generic"]["range"],
                ms_beta=record["monet_sisley"]["beta"],
                ms_range=deletion["monet_sisley_beta"]["range"],
            )
        )
    return rows


def square_monet_sisley(data) -> list[dict]:
    rows = by_model(data["review_v3"]["views"]["central_square"]["models"])
    return [
        dict(
            beta=r["monet_sisley"]["beta"],
            range=r["scene_deletion_summaries"]["monet_sisley_beta"]["range"],
        )
        for r in rows
    ]


def agreement(data) -> list[dict]:
    csv_rows = by_model(data["models"])
    review = by_model(data["review_v1"]["models"], values=TITLES)
    out = []
    for row, rev in zip(csv_rows, review, strict=True):
        require(abs(float(row["beta"]) - rev["beta"]) < 1e-9, "beta sources disagree")
        require(abs(float(row["distortion"]) - rev["d"]) < 1e-9, "D sources disagree")
        omit = {x["omitted"]: x["beta"] for x in rev["leave_artist_out"]}
        out.append(
            dict(
                beta=float(row["beta"]),
                beta_ci=parse_interval(row["beta_simultaneous_ci"]),
                d=float(row["distortion"]),
                d_ci=parse_interval(row["distortion_nominal_ci"]),
                q=rev["q"],
                align=rev["corrected_alignment"],
                d_agg=rev["aggregate_d"],
                v_scene=rev["scene_variation"],
                d_held=rev["held_out_d"],
                scalars=rev["fitted_scalars"],
                within_share=rev["shared_within"]["fraction"],
                components=rev["reference_component_slopes"],
                omit=[omit[a] for a in ARTISTS],
                pairs={tuple(p["artists"]): p for p in rev["artist_pairs"]},
            )
        )
    return out


def contrasts(data) -> dict:
    out = {}
    for row in data["contrasts"]:
        out[(row["model_a"], row["model_b"])] = dict(
            diff=float(row["difference"]),
            sim=parse_interval(row["simultaneous_ci"]),
        )
    require(len(out) == 15, "expected 15 model contrasts")
    return out


def learned(data, rep: str, view: str = "original", target: str = "primary") -> list[dict]:
    block = data["learned"][rep][view]
    shared = by_model(block["shared_change"])
    targets = by_model(block["targets"][target]["models"])
    rows = []
    for sh, t in zip(shared, targets, strict=True):
        gain = t["prototype"]["common_vs_labeled_prototype_gain"]["named_minus_generic"]
        pair = next(
            p for p in t["painter_pairs"] if p["artists"] == ["claude_monet", "alfred_sisley"]
        )
        rows.append(
            dict(
                gain=t["prototype"]["mean_named_minus_generic"],
                common_gain=gain["common_fraction"],
                change_generic=sh["named_minus_generic"]["scene_averaged"]["common_fraction"],
                change_free=sh["named_minus_free"]["scene_averaged"]["common_fraction"],
                accuracy=t["recognition"]["macro_accuracy"],
                beta=t["centered"]["beta"],
                d=t["centered"]["d"],
                ms_beta=pair["beta"],
            )
        )
    return rows


def development_accuracy(data, rep: str) -> float:
    return data["learned"][rep]["original"]["development_recognition"]["macro_accuracy"]


def transfer(data, rep: str, view="original", target="primary") -> dict:
    group = data["transfer"]["representations"][rep][view]["targets"][target]
    rows = by_model(group["models"])
    table = []
    for row in rows:
        rules = row["rules"]
        table.append(
            dict(
                B=rules["reference_baseline"]["macro_accuracy"],
                T=rules["common_translation"]["macro_accuracy"],
                G=rules["generated_prototype"]["macro_accuracy"],
                dT=row["paired_translation_vs_baseline"]["accuracy_difference"],
                fixed=row["paired_translation_vs_baseline"]["corrected_count"],
                broken=row["paired_translation_vs_baseline"]["newly_incorrect_count"],
            )
        )
    means = group["equal_configuration_mean_accuracy_difference"]
    return dict(
        rows=table,
        mean_T=means["paired_translation_vs_baseline"],
        mean_G=means["paired_generated_prototype_vs_baseline"],
    )


def cross_cohort(data) -> dict:
    fams = data["cross"]["families"]
    ranges = data["cross"]["sensitivity_ranges"]
    out = {}
    for fam in ("all31", "color", "spatial", "texture"):
        pooled, within = fams[fam]["pooled"], fams[fam]["within_scene"]
        pair = next(
            p for p in fams[fam]["pairs"] if p["painters"] == ["claude_monet", "alfred_sisley"]
        )
        out[fam] = dict(
            C=pooled["C"],
            L=pooled["L"],
            H=pooled["H"],
            share=pooled["common_fraction"],
            share_range=(
                ranges[fam]["pooled"]["common_fraction"]["minimum"],
                ranges[fam]["pooled"]["common_fraction"]["maximum"],
            ),
            within=within["common_fraction"],
            beta=pooled["beta"],
            d=pooled["D"],
            d_scene=within["D"],
            ms=pair["aligned_amplitude"],
        )
    return out


def source_correction(data) -> dict:
    views = data["quality"]["views"]
    out = {}
    for name in ("original", "regions_original_scaler", "regions_refitted_scaler"):
        view = views[name]
        models = by_model(view["models"], values=TITLES)
        comps = {(c["model_a"], c["model_b"]): c for c in view["comparisons"]}
        out[name] = dict(models=models, comparisons=comps)
    return out


def diagnostics(data) -> dict:
    d = data["diagnostics"]
    require(d["models"] == list(MODELS), "diagnostics model order changed")
    d2 = data["diagnostics2"]
    require(d2["models"] == list(MODELS), "diagnostics v2 model order changed")
    return d


def diagnostics2(data) -> dict:
    return data["diagnostics2"]


def family_agreement(data) -> dict:
    sens = data["primary"]["sensitivities"]
    require(set(sens) == {"color", "spatial", "texture", "without_texture"}, "family keys")
    return {
        key: [dict(beta=r["beta"], d=r["distortion"]) for r in rows] for key, rows in sens.items()
    }


def reference_resampling(data) -> list[dict]:
    rows = data["primary"]["reference_resampling"]
    require(len(rows) == 6, "expected six reference-resampling rows")
    return [dict(beta=r["beta_ci95"], d=r["distortion_ci95"]) for r in rows]


def real_controls(data) -> dict:
    controls = data["review_v1"]["real_controls"]
    return {key: dict(mean=v["mean"], interval=v["interval95"]) for key, v in controls.items()}


# ---------------------------------------------------------------------------
# Rendering helpers


MINUS = re.compile(r"(?<![\w$\-])-(?=\d)")


def rows_tex(rows) -> str:
    """Join table rows, typesetting leading minus signs in math mode."""
    return MINUS.sub("$-$", "\n".join(rows))


def provenance(*keys) -> str:
    lines = ["% Generated by paper/tmlr/build_assets.py; do not edit by hand."]
    for key in keys:
        rel, digest = INPUTS[key]
        lines.append(f"% input {rel} sha256 {digest}")
    return "\n".join(lines) + "\n"


def bold_best(values, fmt, higher: bool):
    """Bold every value whose displayed text equals the best displayed text."""
    texts = [fmt(v) for v in values]
    best = fmt(max(values) if higher else min(values))
    return [f"\\textbf{{{t}}}" if t == best else t for t in texts]


def table(label, caption, spec, header, body, *keys, size="\\small") -> str:
    return (
        provenance(*keys)
        + "\\begin{table}[t]\n"
        + f"\\caption{{{caption}}}\n\\label{{{label}}}\n\\vspace{{2pt}}\n"
        + f"\\centering{size}\n\\begin{{tabular}}{{{spec}}}\n\\toprule\n"
        + header
        + "\n\\midrule\n"
        + rows_tex(body)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def rng(pair, fmt=pct) -> str:
    return f"[{fmt(pair[0])}, {fmt(pair[1])}]"


# ---------------------------------------------------------------------------
# Main-text tables


def table_shared(diag, diag2) -> str:
    body = []
    for name, d, d2 in zip(SHORT, diag["hand31"], diag2["hand31"], strict=True):
        a = d["families"]["all31"]
        p, b = d2["point"]["all31"], d2["scene_bootstrap"]["all31"]
        require(abs(p["observed"] - a["shared_fraction"]) < 1e-12, "v1/v2 shared fraction")
        body.append(
            f"{name} & {pct(p['observed'])} & {rng(b['observed'])} & {pct(p['faithful'])}"
            f" & {pct(p['exact'])} & {pct(b['observed_below_faithful'], 0)}"
            f" & {f2(a['direction_cosine'])} & {pct(a['projection_ratio'])}"
            f" & {pct(a['fraction_along_generic'])}\\\\"
        )
    header = (
        " & \\multicolumn{2}{c}{Observed (\\%)} & \\multicolumn{3}{c}{Benchmarks (\\%)}"
        " & \\multicolumn{3}{c}{Direction of the shared change}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-6}\\cmidrule(l){7-9}\n"
        "Configuration & fraction & scene 95\\% & faithful & exact diff. & obs.$<$faithful"
        " & $\\cos(c,t)$ & covered & along generic\\\\"
    )
    caption = (
        "Shared fraction $N/(N+B)$ of what the four names add beyond the generic clause (31"
        " features), with a 95\\% interval from 5,000 scene resamples. Faithful: the fraction if"
        " each named mean equalled the painter's reference mean, from the same generic outputs."
        " Exact differences: the fraction if the observed shared change were kept and the"
        " between-name differences equalled the reference differences, $N/(N+H)$."
        " Obs.$<$faithful: share of scene resamples in which the observed fraction is below the"
        " faithful one. Direction: cosine between the shared change $c$ and the vector $t$ from"
        " the generic mean to the reference centroid, the fraction of $t$ covered along its"
        " direction, and the share of $N$ along the artist-free-to-generic shift (\\%)."
    )
    return table(
        "tab:shared",
        caption,
        "@{}lrcrrrrrr@{}",
        header,
        body,
        "diagnostics",
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def table_agreement(rows, resample, diag2) -> str:
    body = []
    joint = diag2["joint_d_below_one"]
    for name, r, ref, j in zip(SHORT, rows, resample, joint, strict=True):
        body.append(
            f"{name} & {f3(r['beta'])} & {interval(r['beta_ci'])} & {interval(ref['beta'])}"
            f" & {f3(r['q'])} & {f3(r['d'])} & {interval(r['d_ci'])} & {interval(ref['d'])}"
            f" & {pct(j)}\\\\"
        )
    header = (
        " & \\multicolumn{3}{c}{Aligned amplitude $\\beta$} & &"
        " \\multicolumn{4}{c}{Error $D$}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(l){6-9}\n"
        "Configuration & est. & scenes & references & $Q$ & est. & scenes & references"
        " & $D<1$ (\\%)\\\\"
    )
    caption = (
        "Agreement of the between-name differences with the reference painter differences"
        " (31 features). $\\beta=1$ matches the reference pattern's size along its direction;"
        " $Q$ is the squared size of the generated differences relative to the reference;"
        " $D=1-2\\beta+Q$ is 0 for exact agreement and 1 when names produce no differences."
        " Scenes: for $\\beta$, prespecified 95\\% simultaneous intervals over 21 endpoints; for"
        " $D$, unadjusted 95\\% intervals. References: prespecified 95\\% intervals from"
        " resampling reference works within painter. $D<1$: share of 2,000 joint resamples of"
        " scenes and reference works with $D$ below 1."
    )
    return table(
        "tab:agreement",
        caption,
        "@{}lrccrrccr@{}",
        header,
        body,
        "models",
        "review_v1",
        "primary",
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def table_learned(diag2) -> str:
    body = []
    for i, name in enumerate(SHORT):
        cells = []
        for rep in ("clip", "csd"):
            proto = diag2["learned"][rep][i]["prototype"]
            p, b = proto["point"], proto["scene_bootstrap"]
            cells += [pct(p["observed"]), rng(b["observed"]), pct(p["faithful"]), pct(p["exact"])]
        body.append(f"{name} & " + " & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{4}{c}{CLIP} & \\multicolumn{4}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-9}\n"
        "Configuration & obs. & scene 95\\% & faithful & exact diff. & obs. & scene 95\\%"
        " & faithful & exact diff.\\\\"
    )
    caption = (
        "Shared part (\\%) of the named-minus-generic proximity gain in CLIP and CSD"
        " (Equation~\\ref{eq:prototype-gain}), with a 95\\% interval from 5,000 scene resamples."
        " Faithful: the same share if every named mean equalled its reference prototype. Exact"
        " differences: the share if the observed shared term were kept and the painter-specific"
        " term had its reference value $H/4$."
    )
    return table(
        "tab:learned",
        caption,
        "@{}lrcrrrcrr@{}",
        header,
        body,
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def table_readouts(agree, clip, csd) -> str:
    cols = [
        bold_best([r["gain"] for r in clip], f3, True),
        bold_best([r["gain"] for r in csd], f3, True),
        bold_best([r["accuracy"] for r in clip], pct, True),
        bold_best([r["accuracy"] for r in csd], pct, True),
        bold_best([r["d"] for r in agree], f3, False),
        bold_best([r["d"] for r in clip], f3, False),
        bold_best([r["d"] for r in csd], f3, False),
    ]
    body = [
        f"{title} & " + " & ".join(col[i] for col in cols) + "\\\\" for i, title in enumerate(SHORT)
    ]
    header = (
        " & \\multicolumn{2}{c}{Proximity gain} & \\multicolumn{2}{c}{Recognition (\\%)}"
        " & \\multicolumn{3}{c}{Agreement error $D$}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(l){6-8}\n"
        "Configuration & CLIP & CSD & CLIP & CSD & 31 features & CLIP & CSD\\\\"
    )
    caption = (
        "Three readouts of the same images. Proximity: named-minus-generic gain in cosine"
        " similarity to the prompted painter's reference prototype. Recognition: macro"
        " accuracy of assigning each of the 112 named images to its prompted painter by the"
        " nearest reference prototype (chance 25\\%). Agreement: error $D$ of the"
        " between-name differences in each representation (lower is better). Bold marks the"
        " best displayed value in each column; Table~\\ref{tab:stability} shows how often each"
        " configuration is best under scene resampling. Values are not comparable across"
        " representations."
    )
    return table("tab:readouts", caption, "@{}lrrrrrrr@{}", header, body, "learned", "models")


READOUTS = (
    ("clip", "gain", "Proximity gain, CLIP"),
    ("csd", "gain", "Proximity gain, CSD"),
    ("clip", "accuracy", "Recognition, CLIP"),
    ("csd", "accuracy", "Recognition, CSD"),
    ("hand31", "d", "Error $D$, 31 features"),
    ("clip", "d", "Error $D$, CLIP"),
    ("csd", "d", "Error $D$, CSD"),
)


def stability_rows(diag) -> list[dict]:
    rows = []
    for rep, key, label in READOUTS:
        freq = diag["stability"][rep]["bootstrap"][key]["best_frequency"]
        ranked = sorted(freq.items(), key=lambda kv: -kv[1])
        rows.append(
            dict(
                rep=rep,
                key=key,
                label=label,
                best=SHORT[MODELS.index(ranked[0][0])],
                best_freq=ranked[0][1],
                second=SHORT[MODELS.index(ranked[1][0])],
                second_freq=ranked[1][1],
            )
        )
    return rows


def table_stability(diag) -> str:
    body = [
        f"{r['label']} & {r['best']} & {pct(r['best_freq'])} & {r['second']}"
        f" & {pct(r['second_freq'])}\\\\"
        for r in stability_rows(diag)
    ]
    header = "Readout & Most often best & \\% & Next & \\%\\\\"
    caption = (
        "Which configuration is best on each readout when the 14 scenes are resampled with"
        " replacement (5,000 paired resamples; the same scenes for every configuration)."
        " The percentages describe dependence on the authored scenes, not confidence for new"
        " scenes."
    )
    return table("tab:stability", caption, "@{}llrlr@{}", header, body, "diagnostics")


def table_families(diag, diag2, cross) -> str:
    body = []
    lofo = [v for d in diag["hand31"] for v in d["leave_one_feature_out"]["shared_fraction"]]
    for name, d in zip(SHORT, diag["hand31"], strict=True):
        f = d["families"]
        w = d["weighted_shared_fraction"]
        body.append(
            f"{name} & {pct(f['all31']['shared_fraction'])} & {pct(f['color']['shared_fraction'])}"
            f" & {pct(f['spatial']['shared_fraction'])} & {pct(f['texture']['shared_fraction'])}"
            f" & {pct(w['equal_family'])} & {pct(w['development_covariance'])}\\\\"
        )
    means = diag2["family_means"]
    keys = ("all31", "color", "spatial", "texture")
    body.append(
        "\\midrule\nMean of the six & "
        + " & ".join(pct(means[k]["mean"]) for k in keys)
        + " & &\\\\"
    )
    body.append(
        "\\quad scene 95\\% interval & "
        + " & ".join(rng(means[k]["scene_interval"]) for k in keys)
        + " & &\\\\"
    )
    body.append(
        "SD-Turbo (separate) & " + " & ".join(pct(cross[f]["share"]) for f in keys) + " & &\\\\"
    )
    header = (
        " & \\multicolumn{4}{c}{Feature family} & \\multicolumn{2}{c}{Weighting}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-7}\n"
        "Configuration & all 31 & color & spatial & texture & equal family & covariance\\\\"
    )
    caption = (
        "Shared fraction $N/(N+B)$ (\\%) of what the names add beyond the generic clause, by"
        " feature family and under two alternative weightings of all 31 features; deleting any"
        f" one feature keeps it within {span(lofo, pct)}\\%. The interval row gives 95\\%"
        " intervals for the mean over the six configurations from 5,000 scene resamples. The"
        " SD-Turbo row uses its own baseline, which already requests an oil painting."
    )
    return table(
        "tab:families",
        caption,
        "@{}lcccccc@{}",
        header,
        body,
        "diagnostics",
        "diagnostics2",
        "cross",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


# ---------------------------------------------------------------------------
# Appendix tables


def table_learned_squared(diag) -> str:
    body = []
    for i, name in enumerate(SHORT):
        cells = []
        for rep in ("clip", "csd"):
            row = diag["learned"][rep][i]["decomposition"]
            cells += [pct(row["shared_fraction"]), pct(row["faithful_shared_fraction"])]
        body.append(f"{name} & " + " & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{2}{c}{CLIP} & \\multicolumn{2}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(l){4-5}\n"
        "Configuration & observed & faithful & observed & faithful\\\\"
    )
    caption = (
        "Shared fraction $N/(N+B)$ (\\%) of the squared change added by the names, computed in"
        " each embedding, with its faithful-imitation value."
    )
    return table("tab:learned-squared", caption, "@{}lrrrr@{}", header, body, "diagnostics")


def table_pair_intervals(diag2) -> str:
    body = []
    for i, name in enumerate(SHORT):
        h = diag2["hand31"][i]["pairs"][0]
        c = diag2["learned"]["clip"][i]["pairs"][0]
        s = diag2["learned"]["csd"][i]["pairs"][0]
        require(h["painters"] == ["claude_monet", "alfred_sisley"], "pair order")
        body.append(
            f"{name} & {f3(h['beta'])} & {interval(h['beta_scene'])}"
            f" & {interval(h['beta_reference'])} & {f3(c['beta'])} & {interval(c['beta_scene'])}"
            f" & {f3(s['beta'])} & {interval(s['beta_scene'])}\\\\"
        )
    header = (
        " & \\multicolumn{3}{c}{31 features} & \\multicolumn{2}{c}{CLIP}"
        " & \\multicolumn{2}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-6}\\cmidrule(l){7-8}\n"
        "Configuration & $\\beta$ & scenes & references & $\\beta$ & scenes & $\\beta$"
        " & scenes\\\\"
    )
    caption = (
        "Monet--Sisley aligned amplitude with 95\\% intervals from 5,000 scene resamples and"
        " 1,000 reference resamples (the latter shown for the 31 features; all six pairs and both"
        " interval types for every representation are in the supplementary analysis output)."
    )
    return table(
        "tab:pair-intervals",
        caption,
        "@{}lrccrcrc@{}",
        header,
        body,
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_per_painter(diag2) -> str:
    body = []
    for i, name in enumerate(SHORT):
        cells = []
        for rep in ("clip", "csd"):
            rows = diag2["learned"][rep][i]["prototype"]["per_painter"]
            cells += [pct(r["shared_fraction"]) for r in rows]
        body.append(f"{name} & " + " & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{4}{c}{CLIP} & \\multicolumn{4}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-9}\n"
        "Configuration & " + " & ".join(["Mon.", "Sis.", "Pis.", "C\\'ez."] * 2) + "\\\\"
    )
    caption = (
        "Shared part (\\%) of the proximity gain for each prompted painter separately:"
        " $(\\bar g-g_{\\mathrm g})^\\top\\mu_a$ divided by $(g_a-g_{\\mathrm g})^\\top\\mu_a$."
        " Values above 100\\% mean that the painter-specific term is negative for that painter."
    )
    return table(
        "tab:per-painter",
        caption,
        "@{}lrrrrrrrr@{}",
        header,
        body,
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_family_agreement(fam) -> str:
    body = []
    for i, name in enumerate(SHORT):
        cells = []
        for key in ("color", "spatial", "texture", "without_texture"):
            cells += [f3(fam[key][i]["beta"])]
        for key in ("color", "spatial", "texture", "without_texture"):
            cells += [f3(fam[key][i]["d"])]
        body.append(f"{name} & " + " & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{4}{c}{Aligned amplitude $\\beta$} & \\multicolumn{4}{c}{Error $D$}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-9}\n"
        "Configuration & color & spatial & texture & no texture & color & spatial & texture"
        " & no texture\\\\"
    )
    caption = (
        "Prespecified feature-family sensitivity of the agreement scores: $\\beta$ and $D$ computed"
        " within each family (with its own $H$) and without the texture family."
    )
    return table(
        "tab:family-agreement",
        caption,
        "@{}lrrrrrrrr@{}",
        header,
        body,
        "primary",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_decomposition_full(hand, diag) -> str:
    body = []
    for title, r, d in zip(SHORT, hand, diag["hand31"], strict=True):
        h = r["H"]
        body.append(
            f"{title} & {f2(r['G'] / h)} & {f2(r['N'] / h)} & {f2(r['I'] / h)} & {f2(r['C'] / h)}"
            f" & {f2(r['B'] / h)} & {pct(r['share_free'])} & {pct(r['share_generic'])}"
            f" & {pct(d['within_scene_shared_fraction'])}\\\\"
        )
    header = (
        " & \\multicolumn{5}{c}{Squared change $/H$}"
        " & \\multicolumn{3}{c}{Shared fraction (\\%)}\\\\\n"
        "\\cmidrule(lr){2-6}\\cmidrule(l){7-9}\n"
        "Configuration & $G$ & $N$ & $I$ & $N_{\\mathrm{free}}$ & $B$ & vs.\\ free & vs.\\ generic"
        " & within scene\\\\"
    )
    caption = (
        f"Complete decomposition in the 31 features, in units of $H={f3(hand[0]['H'])}$."
        " $G$: artist-free-to-generic shift. $N$: shared change beyond the generic clause."
        " $I$: cross term. $N_{\\mathrm{free}}=G+N+I$: shared change against the artist-free"
        " baseline. $B$: between-name differences (identical for both baselines). Within"
        " scene: $N/(N+B)$ with both components computed in each scene before averaging."
    )
    return table(
        "tab:decomposition-full",
        caption,
        "@{}lrrrrrrrr@{}",
        header,
        body,
        "review_v3",
        "review_v1",
        "diagnostics",
    )


def table_pairs(pairs) -> str:
    body = []
    for i in range(6):
        for j in range(i + 1, 6):
            r = pairs[(MODELS[i], MODELS[j])]
            mark = "" if r["sim"][0] <= 0 <= r["sim"][1] else "$^{*}$"
            body.append(f"{SHORT[i]} & {SHORT[j]} & {f3(r['diff'])} {interval(r['sim'])}{mark}\\\\")
    header = "Configuration A & Configuration B & $D_A-D_B$ [simultaneous interval]\\\\"
    caption = (
        "All 15 prespecified pairwise error comparisons in the 31 features. Brackets are"
        " approximate 95\\% simultaneous intervals over the 21-endpoint family; a positive"
        " difference favors configuration B. $^{*}$: interval excludes zero."
    )
    return table("tab:pairs", caption, "@{}llc@{}", header, body, "contrasts")


def table_calibration(rows) -> str:
    held = bold_best([r["d_held"] for r in rows], f3, False)
    body = [
        f"{title} & {f3(r['d'])} & {f3(r['d_agg'])} & {f3(r['v_scene'])} & {f3(r['align'])}"
        f" & {f3(min(r['scalars']))}--{f3(max(r['scalars']))} & {hc}\\\\"
        for title, r, hc in zip(SHORT, rows, held, strict=True)
    ]
    header = (
        "Configuration & $D$ & $D_{\\mathrm{agg}}$ & $V_{\\mathrm{scene}}$"
        " & $\\beta/\\sqrt{Q}$ & fitted scalar & $D_{\\mathrm{held}}$\\\\"
    )
    caption = (
        "Scene aggregation and contrast magnitude in the 31 features."
        " $D=D_{\\mathrm{agg}}+V_{\\mathrm{scene}}$; $\\beta/\\sqrt{Q}$ is the alignment ratio"
        " (direction only). $D_{\\mathrm{held}}$: error after multiplying every centered"
        " generated contrast by a nonnegative scalar fitted on the other 13 scenes; the fitted"
        " range covers the 14 folds. Rescaling changes feature vectors, not images."
    )
    return table("tab:calibration", caption, "@{}lrrrrcr@{}", header, body, "review_v1")


def table_coverage(rows, hand, square, clip, csd) -> str:
    body = []
    for i, (title, r) in enumerate(zip(SHORT, rows, strict=True)):
        body.append(
            f"{title} & "
            + " & ".join(f3(v) for v in r["components"])
            + " & "
            + " & ".join(f3(v) for v in r["omit"])
            + f" & {f3(hand[i]['ms_beta'])} & {f3(square[i]['beta'])}"
            + f" & {f3(clip[i]['ms_beta'])} & {f3(csd[i]['ms_beta'])}\\\\"
        )
    header = (
        " & \\multicolumn{3}{c}{Component} & \\multicolumn{4}{c}{$\\beta$ after omitting}"
        " & \\multicolumn{4}{c}{Monet--Sisley $\\beta$}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-8}\\cmidrule(l){9-12}\n"
        "Configuration & 1st & 2nd & 3rd & Mon. & Sis. & Pis. & C\\'ez."
        " & 31 & square & CLIP & CSD\\\\"
    )
    caption = (
        "Which painter differences carry the aligned response. Components: aligned amplitude"
        " along each singular component of the centered reference means (66.3\\%, 20.6\\% and"
        " 13.0\\% of their spread). Omitting a painter recenters the other three and recomputes"
        " $\\beta$. Monet--Sisley $\\beta$: aligned amplitude for that pair alone, in the 31"
        " features (full frame and central-square reference windows) and in each embedding."
    )
    return table(
        "tab:coverage",
        caption,
        "@{}l*{11}{r}@{}",
        header,
        body,
        "review_v1",
        "review_v3",
        "learned",
        size="\\footnotesize",
    )


def table_sensitivity(data, sc) -> str:
    content = {row["model"]: row for row in data["review_v1"]["content"]["models"]}
    weighting = data["review_v1"]["weighting"]
    orig = sc["original"]["models"]
    crop = sc["regions_original_scaler"]["models"]
    refit = sc["regions_refitted_scaler"]["models"]
    body = []
    for i, title in enumerate(TITLES):
        c = content[title]
        body.append(
            f"{SHORT[i]} & {f3(orig[i]['d'])} & {f3(c['pooled_d'])} & {f3(c['conditional_d'])}"
            f" & {f3(weighting['equal_family'][i]['d'])}"
            f" & {f3(weighting['development_covariance'][i]['d'])}"
            f" & {f3(crop[i]['d'])} & {f3(refit[i]['d'])}\\\\"
        )
    header = (
        " & & \\multicolumn{2}{c}{11 scenes} & \\multicolumn{2}{c}{Weighting}"
        " & \\multicolumn{2}{c}{Source correction}\\\\\n"
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\\cmidrule(l){7-8}\n"
        "Configuration & Primary & pooled & class & equal family & covariance"
        " & cropped & refit\\\\"
    )
    caption = (
        "Error $D$ under alternative targets, weightings and source corrections. Class target:"
        " title-derived water, built and land reference means for the 11 matching scenes"
        " (pooled: the same 11 scenes against the pooled target). Equal family: each feature"
        " family has equal total weight. Covariance: shrunk inverse covariance of the"
        " development panel. Cropped: AI-audited painting regions with the original scaling;"
        " refit: also refitting the development scaling. Each column has its own normalizer."
    )
    return table("tab:sensitivity", caption, "@{}lrrrrrrr@{}", header, body, "review_v1", "quality")


def table_robustness(diag, agree) -> str:
    bias = pct(diag["h_correction"]["bias"] / diag["h_correction"]["H"])
    body = []
    for title, d in zip(SHORT, diag["hand31"], strict=True):
        a = d["families"]["all31"]
        body.append(
            f"{title} & {f2(d['repeat_noise_over_h'])} & {f3(d['beta_with_corrected_h'])}"
            f" & {f2(a['generic_cosine'])} & {f3(a['centroid_gain'])}"
            f" & {f3(a['centroid_gain_shared'])} & {f3(a['centroid_gain_between'])}\\\\"
        )
    header = (
        " & Repeat noise & $\\beta$ with & $\\cos(c,g)$ & \\multicolumn{3}{c}{Centroid proximity"
        " gain}\\\\\n\\cmidrule(l){5-7}\n"
        "Configuration & $/H$ & corrected $H$ & & total & shared & between-name\\\\"
    )
    caption = (
        "Further diagnostics in the 31 features. Repeat noise: squared difference between"
        " the two repeats' centered contrasts, relative to $H$. $\\beta$ with corrected $H$:"
        f" aligned amplitude after removing the finite-sample bias of $H$ ({bias}\\%)."
        " $\\cos(c,g)$: corrected cosine between the shared naming change and the"
        " artist-free-to-generic shift. Centroid proximity gain: mean reduction in squared"
        " distance from the generated mean to each painter's reference mean, from the generic"
        " to the named clause, split exactly into shared and between-name parts"
        " (Appendix~\\ref{app:estimators})."
    )
    return table("tab:robustness", caption, "@{}lrrrrrr@{}", header, body, "diagnostics")


def table_transfer(clip, csd) -> str:
    body = []
    for i, title in enumerate(SHORT):
        c, s = clip["rows"][i], csd["rows"][i]
        body.append(
            f"{title} & {pct(c['B'])} & {pct(c['T'])} & {pct(c['G'])}"
            f" & {pct(s['B'])} & {pct(s['T'])} & {pct(s['G'])}\\\\"
        )
    body.append(
        "\\midrule\nMean change vs.\\ Ref.\\ (pp) & & "
        f"{signed_pct(clip['mean_T'])} & {signed_pct(clip['mean_G'])} & & "
        f"{signed_pct(csd['mean_T'])} & {signed_pct(csd['mean_G'])}\\\\"
    )
    header = (
        " & \\multicolumn{3}{c}{CLIP} & \\multicolumn{3}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(l){5-7}\n"
        "Configuration & Ref. & Shift & Gen. & Ref. & Shift & Gen.\\\\"
    )
    caption = (
        "Held-scene recognition of the prompted painter (\\%, 112 named images per"
        " configuration, chance 25\\%). Ref.: nearest reference prototype. Shift: the same"
        " after adding one fixed translation that aligns the generated and reference mixture"
        " means, fitted on the other 13 scenes without painter labels. Gen.: nearest"
        " generated-image prototype fitted with painter labels on the other 13 scenes."
        " Shift and Gen.\\ use more information than Ref., and Gen.\\ more than Shift."
    )
    return table("tab:transfer", caption, "@{}lrrrrrr@{}", header, body, "transfer")


def table_scenes(scenes) -> str:
    body = [f"{s['index'] + 1} & {s['content']} & {s['brief']}\\\\" for s in scenes]
    header = "\\# & Class & Scene description\\\\"
    caption = (
        "The 14 scene descriptions, with their fixed content class. Each prompt is the"
        " clause, the description and ``No text or frame.''"
    )
    text = table("tab:scenes", caption, "@{}rlp{0.78\\linewidth}@{}", header, body, "requests")
    return text.replace("\\begin{table}[t]", "\\begin{table}[h!]")


# ---------------------------------------------------------------------------
# Figures


def _matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams.update(
        {"pdf.fonttype": 42, "font.family": "DejaVu Sans", "font.size": 8, "path.simplify": False}
    )
    import matplotlib.pyplot as plt

    return plt


def _pdf_bytes(fig, plt) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="pdf",
        metadata={"CreationDate": None, "ModDate": None, "Creator": None, "Producer": None},
    )
    plt.close(fig)
    return buffer.getvalue()


def figure_schematic() -> bytes:
    """Conceptual geometry of the decomposition; illustrative positions, not data."""
    plt = _matplotlib()
    fig, ax = plt.subplots(figsize=(6.3, 2.9))
    refs = {
        "Monet": ((6.95, 3.55), (-0.62, 0.12)),
        "Sisley": ((7.75, 3.95), (0.14, 0.02)),
        "Pissarro": ((7.3, 2.7), (-0.95, -0.28)),
        "C\u00e9zanne": ((8.95, 2.55), (0.12, -0.05)),
    }
    points = [p for p, _ in refs.values()]
    centroid = (sum(p[0] for p in points) / 4, sum(p[1] for p in points) / 4)
    generic = (1.2, 0.9)
    named_center = (4.3, 2.0)
    offsets = [(-0.35, 0.45), (0.2, 0.62), (-0.1, -0.5), (0.75, -0.35)]
    arrow = dict(arrowstyle="-|>", lw=1.2, shrinkA=3, shrinkB=3)
    ax.annotate(
        "",
        xy=centroid,
        xytext=generic,
        arrowprops=dict(arrow, color=MUTED, linestyle=(0, (3, 2)), lw=1),
    )
    ax.annotate("", xy=named_center, xytext=generic, arrowprops=dict(arrow, color=BLUE, lw=1.8))
    for (name, (ref, label)), off in zip(refs.items(), offsets, strict=True):
        point = (named_center[0] + off[0], named_center[1] + off[1])
        ax.annotate(
            "",
            xy=point,
            xytext=named_center,
            arrowprops=dict(arrow, color=ORANGE, lw=1.1, shrinkA=1),
        )
        ax.plot(*point, "o", color=BLUE, ms=5, zorder=4)
        ax.plot(*ref, "s", color=INK, ms=5, zorder=4)
        ax.annotate(
            "",
            xy=ref,
            xytext=centroid,
            arrowprops=dict(arrow, color="#9a9994", lw=0.8, shrinkA=1),
        )
        ax.text(ref[0] + label[0], ref[1] + label[1], name, fontsize=7, color=INK)
    ax.plot(*centroid, "+", color=INK, ms=9, mew=1.5, zorder=5)
    ax.plot(*generic, "o", color=MUTED, ms=6, zorder=4)
    ax.plot(*named_center, "+", color=BLUE, ms=8, mew=1.5, zorder=5)
    ax.text(
        generic[0] - 0.1, generic[1] - 0.42, "generic clause", fontsize=7, color=MUTED, ha="left"
    )
    ax.text(2.55, 1.12, "shared change $c$", fontsize=7.5, color=BLUE, rotation=19)
    ax.text(3.35, 2.97, "between-name $e_a$", fontsize=7.5, color=ORANGE)
    ax.text(
        4.9, 1.45, "$t$: to reference centroid $\\bar\\mu$", fontsize=7.5, color=MUTED, rotation=14
    )
    ax.text(8.1, 3.25, "differences $r_a$", fontsize=7, color="#6f6e69")
    ax.text(3.2, 0.25, "named clauses (generated)", fontsize=7, color=BLUE)
    ax.text(6.6, 4.35, "reference means (paintings)", fontsize=7, color=INK)
    ax.set_xlim(0.6, 10.2)
    ax.set_ylim(0.0, 4.6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.2)
    return _pdf_bytes(fig, plt)


def figure_pairs(diag2) -> bytes:
    """Painter-pair aligned amplitude and error in the 31 features (point values)."""
    plt = _matplotlib()
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm

    labels = ["M-S", "M-P", "M-C", "S-P", "S-C", "P-C"]
    beta = np.array([[p["beta"] for p in r["pairs"]] for r in diag2["hand31"]])
    err = np.array([[p["d"] for p in r["pairs"]] for r in diag2["hand31"]])
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.6))
    panels = [
        (beta, "Pair aligned amplitude $\\beta$", "RdBu_r", TwoSlopeNorm(0, -1.5, 1.5)),
        (err, "Pair error $D$", "Blues", None),
    ]
    for ax, (values, title, cmap, norm) in zip(axes, panels, strict=True):
        image = ax.imshow(
            values,
            cmap=cmap,
            norm=norm,
            vmin=None if norm else 0,
            vmax=None if norm else 4,
            aspect="auto",
        )
        for (i, j), v in np.ndenumerate(values):
            dark = (norm is not None and abs(v) > 1.0) or (norm is None and v > 2.4)
            ax.text(
                j,
                i,
                f"{v:.2f}",
                ha="center",
                va="center",
                fontsize=6.5,
                color="white" if dark else INK,
            )
        ax.set_xticks(range(6), labels, fontsize=7)
        ax.set_yticks(range(6), SHORT if ax is axes[0] else [""] * 6, fontsize=7)
        ax.set_title(title, fontsize=8, color=INK)
        ax.tick_params(length=0)
        for side in ax.spines.values():
            side.set_visible(False)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03).ax.tick_params(labelsize=6)
    fig.subplots_adjust(left=0.15, right=0.93, bottom=0.12, top=0.88, wspace=0.3)
    return _pdf_bytes(fig, plt)


def figure_benchmark(diag2) -> bytes:
    plt = _matplotlib()
    panels = [
        (
            "31 features: squared change",
            [(r["point"]["all31"], r["scene_bootstrap"]["all31"]) for r in diag2["hand31"]],
        ),
        (
            "CLIP: proximity gain",
            [
                (r["prototype"]["point"], r["prototype"]["scene_bootstrap"])
                for r in diag2["learned"]["clip"]
            ],
        ),
        (
            "CSD: proximity gain",
            [
                (r["prototype"]["point"], r["prototype"]["scene_bootstrap"])
                for r in diag2["learned"]["csd"]
            ],
        ),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.6), sharey=True)
    ys = list(range(len(SHORT)))[::-1]
    for ax, (title, rows) in zip(axes, panels, strict=True):
        for y, (point, boot) in zip(ys, rows, strict=True):
            low, high = boot["observed"]
            ax.plot([low, high], [y + 0.12, y + 0.12], color=BLUE, lw=1.2, zorder=2)
            ax.plot(point["observed"], y + 0.12, "o", color=BLUE, ms=5, zorder=3)
            ax.plot(
                point["faithful"], y - 0.12, "o", mfc="white", mec=ORANGE, mew=1.5, ms=5, zorder=3
            )
            ax.plot(point["exact"], y - 0.12, "D", color=MUTED, ms=3.8, zorder=3)
        ax.axvline(0.5, color="#9a9994", linestyle=(0, (3, 2)), lw=0.8)
        ax.set_xlim(0.4, 1.0)
        ax.set_xticks([0.5, 0.75, 1.0], ["50%", "75%", "100%"])
        ax.set_title(title, fontsize=7.5, color=INK)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(MUTED)
        ax.tick_params(axis="x", colors=MUTED, labelsize=7)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#e4e3df", lw=0.6)
        ax.set_axisbelow(True)
    axes[0].set_yticks(ys, SHORT)
    from matplotlib.lines import Line2D

    fig.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color=BLUE,
                ms=5,
                lw=1.2,
                label="observed (scene 95% interval)",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="white",
                markeredgecolor=ORANGE,
                mew=1.5,
                ms=5,
                label="faithful imitator",
            ),
            Line2D(
                [0],
                [0],
                marker="D",
                color="w",
                markerfacecolor=MUTED,
                ms=4,
                label="exact differences",
            ),
        ],
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=7,
        bbox_to_anchor=(0.57, 1.0),
    )
    fig.supxlabel("Shared part of the change added by the names", fontsize=7.5, color=INK, y=0.01)
    fig.subplots_adjust(left=0.16, right=0.985, bottom=0.2, top=0.8, wspace=0.2)
    return _pdf_bytes(fig, plt)


# ---------------------------------------------------------------------------
# Claims quoted in the prose


def learned_setting_spread(data) -> float:
    """Largest change (percentage points) of the shared part of prototype gain
    across source views and reference targets, relative to the primary setting."""
    worst = 0.0
    for rep in ("clip", "csd"):
        base = [r["common_gain"] for r in learned(data, rep)]
        for view in ("original", "audited_region"):
            for target in ("primary", "development"):
                rows = [r["common_gain"] for r in learned(data, rep, view, target)]
                worst = max(worst, max(abs(a - b) for a, b in zip(rows, base, strict=True)))
    return 100 * worst


def transfer_setting_means(data, rep: str) -> list[float]:
    return [
        transfer(data, rep, view, target)["mean_T"]
        for view in ("original", "audited_region")
        for target in ("primary", "development")
    ]


def covariance_crossings(data) -> dict:
    out = {}
    for pair in data["covariance"]["pairs"]:
        if pair["crossing"]["status"] == "positive_interior_crossing":
            out[(pair["title_a"], pair["title_b"])] = pair["crossing"]["rho"]
    return out


def pair_frequency(diag, rep, key, first, second) -> float:
    pairs = diag["stability"][rep]["bootstrap"][key]["first_better_frequency"]
    a, b = MODELS[TITLES.index(first)], MODELS[TITLES.index(second)]
    if f"{a}|{b}" in pairs:
        return pairs[f"{a}|{b}"]
    return 1 - pairs[f"{b}|{a}"]


def claims(data) -> dict[str, str]:
    hand = hand_decomposition(data)
    agree = agreement(data)
    pairs = contrasts(data)
    clip, csd = learned(data, "clip"), learned(data, "csd")
    tclip, tcsd = transfer(data, "clip"), transfer(data, "csd")
    cross = cross_cohort(data)
    sc = source_correction(data)
    diag = diagnostics(data)
    resample = reference_resampling(data)
    real = real_controls(data)
    h = hand[0]["H"]
    idx = {t: i for i, t in enumerate(TITLES)}
    gpt2, nb2, flux, gpt1 = (
        idx[t] for t in ("GPT Image 2", "Nano Banana 2", "FLUX.2 Max", "GPT Image 1")
    )
    resolved = sorted(
        (TITLES[MODELS.index(a)], TITLES[MODELS.index(b)])
        for (a, b), r in pairs.items()
        if not (r["sim"][0] <= 0 <= r["sim"][1])
    )
    require(
        resolved
        == [("GPT Image 2.5 Flare", "FLUX.2 Max"), ("GPT Image 2.5 Sunburst", "FLUX.2 Max")],
        f"resolved pairs changed: {resolved}",
    )
    require(all(r["beta_ci"][0] > 0 for r in agree), "all beta intervals above zero")
    require(all(r["beta"][0] > 0 for r in resample), "reference-resampling beta above zero")
    fam = [d["families"] for d in diag["hand31"]]
    faithful = [f["all31"]["faithful_shared_fraction"] for f in fam]
    observed = [f["all31"]["shared_fraction"] for f in fam]
    require(
        all(o < fth for o, fth in zip(observed, faithful, strict=True)),
        "faithful fraction should exceed the observed one in every configuration",
    )
    for rep in ("clip", "csd"):
        rows = diag["learned"][rep]
        require(
            all(
                r["decomposition"]["shared_fraction"]
                < r["decomposition"]["faithful_shared_fraction"]
                for r in rows
            ),
            f"{rep}: faithful should exceed observed",
        )
    between_negative = [f["all31"]["centroid_gain_between"] < 0 for f in fam]
    require(
        between_negative == [True, True, True, True, False, False],
        "between-name centroid-gain signs changed",
    )
    require(all(f["all31"]["centroid_gain"] > 0 for f in fam), "centroid gain positive")
    texture = [f["texture"]["shared_fraction"] for f in fam]
    require(min(texture) == texture[gpt1] and texture[gpt1] < 0.5, "GPT Image 1 texture minority")
    require(all(texture[i] > 0.5 for i in range(6) if i != gpt1), "other textures majority")
    stab = {(r["rep"], r["key"]): r for r in stability_rows(diag)}
    require(stab[("clip", "gain")]["best"] == "Nano Banana 2", "CLIP gain best changed")
    require(stab[("clip", "accuracy")]["best"] == "GPT Image 2", "CLIP accuracy best changed")
    require(stab[("hand31", "d")]["best"] == "FLUX.2 Max", "hand D best changed")
    require(stab[("clip", "d")]["best"] == "GPT Image 1", "CLIP D best changed")
    crossings = covariance_crossings(data)
    require(
        len(crossings) == 3 and all(0 < v < 1 for v in crossings.values()),
        "covariance crossings changed",
    )
    content = {row["model"]: row for row in data["review_v1"]["content"]["models"]}
    weighting = data["review_v1"]["weighting"]
    columns = [
        [content[t]["conditional_d"] for t in TITLES],
        [row["d"] for row in weighting["equal_family"]],
        [row["d"] for row in weighting["development_covariance"]],
        [m["d"] for m in sc["regions_original_scaler"]["models"]],
        [m["d"] for m in sc["regions_refitted_scaler"]["models"]],
        [float(row["square_distortion"]) for row in by_model(data["models"])],
    ]
    for column in columns:
        require(min(column) == column[flux], "FLUX.2 Max should keep the lowest D everywhere")
    refit = sc["regions_refitted_scaler"]
    resolved_refit = sorted(
        k
        for k, c in refit["comparisons"].items()
        if c["available"] and not (c["simultaneous_ci"][0] <= 0 <= c["simultaneous_ci"][1])
    )
    require(
        resolved_refit
        == sorted([("GPT Image 1", "FLUX.2 Max"), ("GPT Image 2.5 Flare", "FLUX.2 Max")]),
        f"source-corrected resolved pairs changed: {resolved_refit}",
    )
    require(
        all(m["beta_interval"]["simultaneous_ci"][0] > 0 for m in refit["models"]),
        "corrected beta intervals must stay positive",
    )
    tclip_d = [r["dT"] for r in tclip["rows"]]
    tcsd_d = [r["dT"] for r in tcsd["rows"]]
    require(
        all(r["G"] > max(r["B"], r["T"]) for r in tclip["rows"] + tcsd["rows"]),
        "generated prototypes should win all 12 combinations",
    )
    along = [f["all31"]["fraction_along_generic"] for f in fam]
    sims = {row["scenario"]: row["family_coverage"] for row in data["review_v1"]["simulation"]}
    lofo = [v for d in diag["hand31"] for v in d["leave_one_feature_out"]["shared_fraction"]]
    hc = diag["h_correction"]
    equal = [d["weighted_shared_fraction"]["equal_family"] for d in diag["hand31"]]
    cov = [d["weighted_shared_fraction"]["development_covariance"] for d in diag["hand31"]]
    diag2 = diagnostics2(data)
    h31 = diag2["hand31"]
    exact31 = [r["point"]["all31"]["exact"] for r in h31]
    proto = {
        rep: [r["prototype"]["point"] for r in diag2["learned"][rep]] for rep in ("clip", "csd")
    }
    proto_diff = [p["observed"] - p["faithful"] for rep in proto for p in proto[rep]]
    below = [r["scene_bootstrap"]["all31"]["observed_below_faithful"] for r in h31]
    require(
        all(v == 1.0 for i, v in enumerate(below) if i != flux) and below[flux] < 0.9,
        "observed-below-faithful frequencies changed",
    )
    dev31 = diag2["development_recognition_31"]
    joint = diag2["joint_d_below_one"]
    sd = diag2["sd_turbo"]
    fam_means = diag2["family_means"]
    fam_agree = family_agreement(data)
    require(
        min(r["d"] for r in fam_agree["texture"]) == fam_agree["texture"][nb2]["d"],
        "Nano Banana 2 should have the lowest texture D",
    )
    worse = [gpt1, idx["GPT Image 2.5 Flare"], idx["GPT Image 2.5 Sunburst"]]
    require(
        all(agree[i]["d_ci"][0] > 1 and resample[i]["d"][0] > 1 for i in worse),
        "three configurations should have D intervals above 1",
    )
    ms_hand_zero = [
        r["pairs"][0]["beta_scene"][0] <= 0 <= r["pairs"][0]["beta_scene"][1] for r in h31
    ]
    require(ms_hand_zero == [True, False, True, False, True, True], "31-feature MS intervals")
    require(
        all(
            r["pairs"][0]["beta_scene"][0] > 0 and r["pairs"][0]["beta_reference"][0] > 0
            for rep in ("clip", "csd")
            for r in diag2["learned"][rep]
        ),
        "embedding MS intervals should exclude zero",
    )
    cez_least = sum(
        min(range(4), key=lambda a: r["prototype"]["per_painter"][a]["shared_fraction"]) == 3
        for rep in ("clip", "csd")
        for r in diag2["learned"][rep]
    )
    return {
        "H": f3(h),
        "exact_hand": span(exact31, pct),
        "exact_clip_proto": span([p["exact"] for p in proto["clip"]], pct),
        "exact_csd_proto": span([p["exact"] for p in proto["csd"]], pct),
        "exact_nb2": pct(exact31[nb2]),
        "proto_diff": span(proto_diff, signed_pct, sep=" to "),
        "flux_obs_below": pct(below[flux]),
        "flux_obs_interval": rng(h31[flux]["scene_bootstrap"]["all31"]["observed"]),
        "dev31_macro": pct(dev31["macro_accuracy"]),
        "dev31_monet": pct(dev31["per_painter"][0]),
        "dev31_sisley": pct(dev31["per_painter"][1]),
        "joint_flux": pct(joint[flux]),
        "joint_nb2": pct(joint[nb2]),
        "sd_faithful": pct(sd["all31"]["faithful"]),
        "sd_exact": pct(sd["all31"]["exact"]),
        "sd_texture_exact": pct(sd["texture"]["exact"]),
        "fam_color": pct(fam_means["color"]["mean"]),
        "fam_spatial": pct(fam_means["spatial"]["mean"]),
        "fam_texture": pct(fam_means["texture"]["mean"]),
        "fam_texture_interval": rng(fam_means["texture"]["scene_interval"]),
        "fam_color_interval": rng(fam_means["color"]["scene_interval"]),
        "texture_d_nb2": f3(fam_agree["texture"][nb2]["d"]),
        "texture_d_flux": f3(fam_agree["texture"][flux]["d"]),
        "worse_scene_low": f3(min(agree[i]["d_ci"][0] for i in worse)),
        "worse_ref_low": f3(min(resample[i]["d"][0] for i in worse)),
        "real_class_class_mean": f3(real["class_real_class_target"]["mean"]),
        "gpt2_q_linear": f2(math.sqrt(agree[gpt2]["q"])),
        "cez_least": str(cez_least),
        "shared_free": span([r["share_free"] for r in hand], pct),
        "shared_generic": span([r["share_generic"] for r in hand], pct),
        "shared_generic_deletion": span([v for r in hand for v in r["range_generic"]], pct),
        "shared_within_free": span([r["within_share"] for r in agree], pct),
        "shared_within_generic": span(
            [d["within_scene_shared_fraction"] for d in diag["hand31"]], pct
        ),
        "faithful_hand": span(faithful, pct),
        "faithful_clip": span(
            [r["decomposition"]["faithful_shared_fraction"] for r in diag["learned"]["clip"]], pct
        ),
        "faithful_csd": span(
            [r["decomposition"]["faithful_shared_fraction"] for r in diag["learned"]["csd"]], pct
        ),
        "observed_clip": span(
            [r["decomposition"]["shared_fraction"] for r in diag["learned"]["clip"]], pct
        ),
        "observed_csd": span(
            [r["decomposition"]["shared_fraction"] for r in diag["learned"]["csd"]], pct
        ),
        "proto_faithful_clip": span(
            [r["prototype_faithful_shared_fraction"] for r in diag["learned"]["clip"]], pct
        ),
        "proto_faithful_csd": span(
            [r["prototype_faithful_shared_fraction"] for r in diag["learned"]["csd"]], pct
        ),
        "direction_cos": span([f["all31"]["direction_cosine"] for f in fam], f2),
        "gap_covered": span([f["all31"]["projection_ratio"] for f in fam], pct),
        "along_generic_gpt": span(along[:4], pct),
        "along_generic_nb2": pct(along[nb2]),
        "along_generic_flux": pct(along[flux]),
        "B_over_H": span([r["B"] / h for r in hand], lambda v: f"{v:.1f}"),
        "B_linear": span([math.sqrt(r["B"] / h) for r in hand], f2),
        "N_linear": span([math.sqrt(r["N"] / h) for r in hand], f2),
        "texture_main": span(texture, pct),
        "texture_gpt1": pct(texture[gpt1]),
        "color_main": span([f["color"]["shared_fraction"] for f in fam], pct),
        "spatial_main": span([f["spatial"]["shared_fraction"] for f in fam], pct),
        "equal_family": span(equal, pct),
        "covariance": span(cov, pct),
        "lofo": span(lofo, pct),
        "gpt2_share_generic": pct(hand[gpt2]["share_generic"]),
        "gpt2_beta": f3(agree[gpt2]["beta"]),
        "gpt2_beta_ci": interval(agree[gpt2]["beta_ci"]),
        "gpt2_q": f3(agree[gpt2]["q"]),
        "gpt2_d": f3(agree[gpt2]["d"]),
        "flux_d": f3(agree[flux]["d"]),
        "flux_d_ci": interval(agree[flux]["d_ci"]),
        "flux_d_ref": interval(resample[flux]["d"]),
        "flux_beta": f3(agree[flux]["beta"]),
        "flux_q": f3(agree[flux]["q"]),
        "beta_range": span([r["beta"] for r in agree], f3),
        "beta_ref_min": f3(min(r["beta"][0] for r in resample)),
        "real_pooled_mean": f3(real["pooled_real"]["mean"]),
        "real_pooled_interval": "["
        + ", ".join(m3(v) for v in real["pooled_real"]["interval"])
        + "]",
        "real_class_mean": f3(real["class_real_pooled_target"]["mean"]),
        "ms_hand_other": span(
            [r["ms_beta"] for i, r in enumerate(hand) if i != gpt2], m3, sep=" to "
        ),
        "ms_hand_gpt2": f3(hand[gpt2]["ms_beta"]),
        "ms_clip": span([r["ms_beta"] for r in clip], f3),
        "ms_csd": span([r["ms_beta"] for r in csd], f3),
        "flux_omit_cezanne": f3(agree[flux]["omit"][3]),
        "gpt2_omit_cezanne": f3(agree[gpt2]["omit"][3]),
        "nb2_d_agg": f3(agree[nb2]["d_agg"]),
        "flux_d_agg": f3(agree[flux]["d_agg"]),
        "gpt2_d_held": f3(agree[gpt2]["d_held"]),
        "flux_d_held": f3(agree[flux]["d_held"]),
        "clip_common_gain": span([r["common_gain"] for r in clip], pct),
        "csd_common_gain": span([r["common_gain"] for r in csd], pct),
        "nb2_clip_gain": f3(clip[nb2]["gain"]),
        "nb2_clip_acc": pct(clip[nb2]["accuracy"]),
        "gpt2_clip_acc": pct(clip[gpt2]["accuracy"]),
        "flux_clip_acc": pct(clip[flux]["accuracy"]),
        "flux_csd_acc": pct(csd[flux]["accuracy"]),
        "gpt1_clip_d": f3(clip[gpt1]["d"]),
        "stab_clip_gain": pct(stab[("clip", "gain")]["best_freq"]),
        "stab_clip_acc": pct(stab[("clip", "accuracy")]["best_freq"]),
        "stab_hand_d": pct(stab[("hand31", "d")]["best_freq"]),
        "stab_clip_d": pct(stab[("clip", "d")]["best_freq"]),
        "stab_csd_gain": pct(stab[("csd", "gain")]["best_freq"]),
        "stab_csd_d": pct(stab[("csd", "d")]["best_freq"]),
        "flux_below_nb2_clip": pct(
            pair_frequency(diag, "clip", "accuracy", "Nano Banana 2", "FLUX.2 Max")
        ),
        "flux_below_nb2_csd": pct(
            pair_frequency(diag, "csd", "accuracy", "Nano Banana 2", "FLUX.2 Max")
        ),
        "dev_clip": pct(development_accuracy(data, "clip")),
        "dev_csd": pct(development_accuracy(data, "csd")),
        "transfer_clip_range": span(tclip_d, signed_pct, sep=" to "),
        "transfer_csd_range": span(tcsd_d, signed_pct, sep=" to "),
        "transfer_clip_mean": signed_pct(tclip["mean_T"]),
        "transfer_csd_mean": signed_pct(tcsd["mean_T"]),
        "transfer_csd_flux": (
            f"{tcsd['rows'][flux]['fixed']} and harms {tcsd['rows'][flux]['broken']}"
        ),
        "sd_share": pct(cross["all31"]["share"]),
        "sd_share_range": span(cross["all31"]["share_range"], pct),
        "sd_color": pct(cross["color"]["share"]),
        "sd_spatial": pct(cross["spatial"]["share"]),
        "sd_texture": pct(cross["texture"]["share"]),
        "sd_texture_range": span(cross["texture"]["share_range"], pct),
        "sd_within": pct(cross["all31"]["within"]),
        "sd_texture_within": pct(cross["texture"]["within"]),
        "sd_beta": f3(cross["all31"]["beta"]),
        "sd_d": f3(cross["all31"]["d"]),
        "sd_d_scene": f3(cross["all31"]["d_scene"]),
        "sd_ms": f3(cross["all31"]["ms"]),
        "flux_d_refit": f3(refit["models"][flux]["d"]),
        "flux_d_crop": f3(sc["regions_original_scaler"]["models"][flux]["d"]),
        "cov_nb2_flux": f3(crossings[("Nano Banana 2", "FLUX.2 Max")]),
        "cov_gpt1_gpt2": f3(crossings[("GPT Image 1", "GPT Image 2")]),
        "cov_gpt1_flux": f3(crossings[("GPT Image 1", "FLUX.2 Max")]),
        "sim_gaussian": pct(sims["gaussian"]),
        "sim_heavy": pct(sims["heavy_heteroskedastic"]),
        "sim_interaction": pct(sims["scene_interaction"]),
        "sim_shared": pct(sims["shared_state"], 2),
        "h_bias": pct(hc["bias"] / hc["H"]),
        "beta_corrected_range": span([d["beta_with_corrected_h"] for d in diag["hand31"]], f3),
        "repeat_noise": span([d["repeat_noise_over_h"] for d in diag["hand31"]], f2),
        "learned_setting_spread": f"{learned_setting_spread(data):.1f}",
        "transfer_clip_settings": span(
            transfer_setting_means(data, "clip"), lambda v: f"{100 * v:.1f}"
        ),
        "transfer_csd_settings": span(
            transfer_setting_means(data, "csd"), lambda v: f"{100 * v:.1f}"
        ),
    }


def all_outputs(data) -> dict[str, str | bytes]:
    hand = hand_decomposition(data)
    agree = agreement(data)
    clip, csd = learned(data, "clip"), learned(data, "csd")
    diag = diagnostics(data)
    diag2 = diagnostics2(data)
    return {
        "tab_shared.tex": table_shared(diag, diag2),
        "tab_agreement.tex": table_agreement(agree, reference_resampling(data), diag2),
        "tab_learned.tex": table_learned(diag2),
        "tab_readouts.tex": table_readouts(agree, clip, csd),
        "tab_stability.tex": table_stability(diag),
        "tab_families.tex": table_families(diag, diag2, cross_cohort(data)),
        "tab_learned_squared.tex": table_learned_squared(diag),
        "tab_pair_intervals.tex": table_pair_intervals(diag2),
        "tab_per_painter.tex": table_per_painter(diag2),
        "tab_family_agreement.tex": table_family_agreement(family_agreement(data)),
        "tab_decomposition_full.tex": table_decomposition_full(hand, diag),
        "tab_pairs.tex": table_pairs(contrasts(data)),
        "tab_calibration.tex": table_calibration(agree),
        "tab_coverage.tex": table_coverage(agree, hand, square_monet_sisley(data), clip, csd),
        "tab_sensitivity.tex": table_sensitivity(data, source_correction(data)),
        "tab_robustness.tex": table_robustness(diag, agree),
        "tab_transfer.tex": table_transfer(transfer(data, "clip"), transfer(data, "csd")),
        "tab_scenes.tex": table_scenes(scenes_from_requests(data["requests"])),
        "fig_schematic.pdf": figure_schematic(),
        "fig_benchmark.pdf": figure_benchmark(diag2),
        "fig_pairs.pdf": figure_pairs(diag2),
    }


def check_claims(values: dict[str, str], registry_path: Path) -> list[str]:
    """Every registered claim must appear verbatim in the manuscript."""
    text = "\n".join(path.read_text() for path in MANUSCRIPT if path.exists())
    text = re.sub(r"(?m)^%.*$", "", text)
    text = re.sub(r"\s+", " ", text)
    registry = json.loads(registry_path.read_text())
    problems = []
    for key, literal in registry.items():
        if key not in values:
            problems.append(f"unknown claim key {key}")
            continue
        if literal != values[key]:
            problems.append(f"{key}: manuscript registry {literal!r} != computed {values[key]!r}")
        elif literal not in text:
            problems.append(f"{key}: {literal!r} not found in manuscript")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--print-claims", action="store_true")
    args = parser.parse_args()
    data = load_inputs(verify=True)
    values = claims(data)
    if args.print_claims:
        print(json.dumps(values, indent=1, ensure_ascii=False))
        return 0
    outputs = all_outputs(data)
    registry = HERE / "claims.json"
    if args.check:
        problems = []
        expected_names = set(outputs)
        present = {p.name for p in OUT.iterdir()} if OUT.exists() else set()
        for extra in sorted(present - expected_names):
            problems.append(f"unexpected generated file: {extra}")
        for name, content in outputs.items():
            path = OUT / name
            current = path.read_bytes() if path.exists() else None
            expected = content if isinstance(content, bytes) else content.encode()
            if current != expected:
                problems.append(f"generated file differs: {path.relative_to(ROOT)}")
        problems += check_claims(values, registry)
        for name, digest in STYLE.items():
            if sha256(HERE / name) != digest:
                problems.append(f"TMLR style file modified: {name}")
        for name, meta in STATIC_FIGURES.items():
            if sha256(HERE / "figures" / name) != meta["sha256"]:
                problems.append(f"static figure changed: figures/{name}")
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        count = len(json.loads(registry.read_text()))
        print(f"ok: {len(outputs)} generated files and {count} claims")
        return 0
    OUT.mkdir(exist_ok=True)
    for stale in OUT.iterdir():
        if stale.name not in outputs:
            stale.unlink()
    for name, content in outputs.items():
        path = OUT / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content)
    print(f"wrote {len(outputs)} files to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
