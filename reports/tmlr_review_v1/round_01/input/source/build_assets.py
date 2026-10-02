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
    "requests": (
        "data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl",
        "0aa60f491be08dbd48f1f018e225b22bcae2aacd724abf3371a6312d59acc679",
    ),
}

STYLE = json.loads((HERE / "STYLE_PROVENANCE.json").read_text())["sha256"]

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


def bold_min(values, fmt):
    best = min(values)
    return [f"\\textbf{{{fmt(v)}}}" if v == best else fmt(v) for v in values]


def bold_max(values, fmt):
    best = max(values)
    return [f"\\textbf{{{fmt(v)}}}" if v == best else fmt(v) for v in values]


def table_decomposition(rows) -> str:
    h = rows[0]["H"]
    body = []
    for title, r in zip(TITLES, rows, strict=True):
        body.append(
            f"{title} & {f2(r['G'] / h)} & {f2(r['N'] / h)} & {f2(r['I'] / h)} & {f2(r['B'] / h)}"
            f" & {pct(r['share_free'])} & {pct(r['share_generic'])}"
            f" & [{pct(r['range_generic'][0])}, {pct(r['range_generic'][1])}]\\\\"
        )
    return (
        provenance("review_v3", "review_v1") + "\\begin{table}[t]\n"
        "\\caption{What a painter name adds in the 31 image features. Scene-averaged,"
        " repeat-corrected squared change, in units of the reference painter spread"
        f" $H={f3(h)}$. $G$: shift from the artist-free to the generic oil-painting prompt."
        " $N$: shift shared by the four names beyond the generic prompt. $I$: cross term,"
        " so that the shared named-minus-free shift is $C=G+N+I$. $B$: between-name"
        " differences, which do not depend on the baseline. Shared shares are $C/(C+B)$"
        " and $N/(N+B)$; brackets give the range over the 14 single-scene deletions.}\n"
        "\\label{tab:decomposition}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrrc@{}}\n\\toprule\n"
        " & \\multicolumn{4}{c}{Squared change $/H$}"
        " & \\multicolumn{3}{c}{Shared share (\\%)}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-8}\n"
        "Configuration & $G$ & $N$ & $I$ & $B$ & vs.\\ free & vs.\\ generic & deletion range\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_agreement(rows) -> str:
    body = []
    ds = [r["d"] for r in rows]
    d_cells = bold_min(ds, f3)
    agg_cells = bold_min([r["d_agg"] for r in rows], f3)
    for title, r, dc, ac in zip(TITLES, rows, d_cells, agg_cells, strict=True):
        body.append(
            f"{title} & {f3(r['beta'])} {interval(r['beta_ci'])} & {f3(r['q'])} & {dc} & {ac}\\\\"
        )
    return (
        provenance("models", "review_v1") + "\\begin{table}[t]\n"
        "\\caption{Agreement of the between-name differences with the reference painter"
        " differences in the 31 features. $\\beta$: aligned amplitude (1 matches the"
        " reference; brackets are prespecified 95\\% simultaneous intervals over 21"
        " endpoints). $Q$: squared size of the generated painter differences relative"
        " to the reference ($Q=1$ matches). $D$: repeat-corrected error of the"
        " scene-wise differences ($D=0$ exact, $D=1$ no painter distinctions);"
        " $D_{\\mathrm{agg}}$ scores the scene-averaged differences instead. Bold marks"
        " the lowest value in a column, not a significant difference.}\n"
        "\\label{tab:agreement}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lcrrr@{}}\n\\toprule\n"
        "Configuration & $\\beta$ [simultaneous interval] & $Q$ & $D$ & $D_{\\mathrm{agg}}$\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_learned(hand, clip, csd) -> str:
    body = []
    for i, title in enumerate(TITLES):
        c, s = clip[i], csd[i]
        body.append(
            f"{title} & {pct(c['common_gain'])} & {pct(s['common_gain'])}"
            f" & {pct(c['change_generic'])} & {pct(s['change_generic'])}"
            f" & {f3(hand[i]['ms_beta'])} & {f3(c['ms_beta'])} & {f3(s['ms_beta'])}\\\\"
        )
    return (
        provenance("learned", "review_v3") + "\\begin{table}[t]\n"
        "\\caption{The same split in CLIP and CSD embeddings of the same images. Shared"
        " part of prototype gain: the common term's share of the named-minus-generic gain"
        " in similarity to the prompted painter's reference prototype"
        " (Equation~\\ref{eq:prototype-gain}). Shared share of squared change: as"
        " $N/(N+B)$ in Table~\\ref{tab:decomposition}, computed in each embedding."
        " Monet--Sisley $\\beta$: aligned amplitude for that pair alone (1 matches the"
        " reference, negative values point the opposite way).}\n"
        "\\label{tab:learned}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrrr@{}}\n\\toprule\n"
        " & \\multicolumn{2}{c}{Shared part of gain (\\%)}"
        " & \\multicolumn{2}{c}{Shared share of change (\\%)}"
        " & \\multicolumn{3}{c}{Monet--Sisley $\\beta$}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(l){6-8}\n"
        "Configuration & CLIP & CSD & CLIP & CSD & 31 features & CLIP & CSD\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_readouts(agree, clip, csd) -> str:
    cols = [
        bold_max([r["gain"] for r in clip], f3),
        bold_max([r["gain"] for r in csd], f3),
        bold_max([r["accuracy"] for r in clip], pct),
        bold_max([r["accuracy"] for r in csd], pct),
        bold_min([r["d"] for r in agree], f3),
        bold_min([r["d"] for r in clip], f3),
        bold_min([r["d"] for r in csd], f3),
    ]
    body = [
        f"{title} & " + " & ".join(col[i] for col in cols) + "\\\\"
        for i, title in enumerate(TITLES)
    ]
    return (
        provenance("learned", "models") + "\\begin{table}[t]\n"
        "\\caption{Three readouts of the same images rank the configurations differently."
        " Proximity: named-minus-generic gain in cosine similarity to the prompted"
        " painter's reference prototype. Recognition: macro accuracy of assigning each"
        " of the 112 named images to its prompted painter by the nearest reference"
        " prototype (chance 25\\%). Agreement: error $D$ of the between-name differences"
        " in each representation (lower is better; 1 means no painter distinctions)."
        " Bold marks the best value in each column. Values are not comparable across"
        " representations.}\n"
        "\\label{tab:readouts}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrrr@{}}\n\\toprule\n"
        " & \\multicolumn{2}{c}{Proximity gain} & \\multicolumn{2}{c}{Recognition (\\%)}"
        " & \\multicolumn{3}{c}{Agreement error $D$}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(l){6-8}\n"
        "Configuration & CLIP & CSD & CLIP & CSD & 31 features & CLIP & CSD\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_sdturbo(cross) -> str:
    names = {
        "all31": "All 31",
        "color": "Color (11)",
        "spatial": "Spatial (8)",
        "texture": "Texture (12)",
    }
    body = []
    for fam, label in names.items():
        r = cross[fam]
        body.append(
            f"{label} & {f2(r['C'] / r['H'])} & {f2(r['L'] / r['H'])} & {pct(r['share'])}"
            f" & [{pct(r['share_range'][0])}, {pct(r['share_range'][1])}] & {pct(r['within'])}"
            f" & {f3(r['beta'])}\\\\"
        )
    return (
        provenance("cross") + "\\begin{table}[t]\n"
        "\\caption{A separate collection: 2,000 SD-Turbo images (16 scenes, 25 matched-seed"
        " blocks). The baseline already requests an oil painting, so the shared change is"
        " comparable to $N$ in Table~\\ref{tab:decomposition}. Components are in units of"
        " each feature family's own reference spread $H$. The deletion range covers the"
        " 25 single-block deletions; the within-scene share computes both components in"
        " each scene before averaging.}\n"
        "\\label{tab:sdturbo}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrcrr@{}}\n\\toprule\n"
        "Features & Shared $/H$ & Between-name $/H$ & Shared (\\%) & deletion range"
        " & within scene (\\%) & $\\beta$\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_pairs(pairs) -> str:
    body = []
    for i in range(6):
        for j in range(i + 1, 6):
            r = pairs[(MODELS[i], MODELS[j])]
            mark = "" if r["sim"][0] <= 0 <= r["sim"][1] else "$^{*}$"
            body.append(
                f"{TITLES[i]} & {TITLES[j]} & {f3(r['diff'])} {interval(r['sim'])}{mark}\\\\"
            )
    return (
        provenance("contrasts") + "\\begin{table}[ht]\n"
        "\\caption{All 15 prespecified pairwise error comparisons in the 31 features."
        " Brackets are approximate 95\\% simultaneous intervals over the 21-endpoint"
        " family; a positive difference favors configuration B. $^{*}$: interval"
        " excludes zero.}\n"
        "\\label{tab:pairs}\n\\centering\\small\n"
        "\\begin{tabular}{@{}llc@{}}\n\\toprule\n"
        "Configuration A & Configuration B & $D_A-D_B$ [simultaneous interval]\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_calibration(rows) -> str:
    body = []
    held = bold_min([r["d_held"] for r in rows], f3)
    for title, r, hc in zip(TITLES, rows, held, strict=True):
        body.append(
            f"{title} & {f3(r['d'])} & {f3(r['d_agg'])} & {f3(r['v_scene'])} & {f3(r['align'])}"
            f" & {f3(min(r['scalars']))}--{f3(max(r['scalars']))} & {hc}\\\\"
        )
    return (
        provenance("review_v1") + "\\begin{table}[ht]\n"
        "\\caption{Scene aggregation and contrast magnitude in the 31 features."
        " $D=D_{\\mathrm{agg}}+V_{\\mathrm{scene}}$. Alignment is $\\beta/\\sqrt{Q}$."
        " Rescaling multiplies every centered generated contrast by a nonnegative scalar"
        " fitted on the other 13 scenes and scores the held-out scene; the fitted range"
        " covers the 14 folds. Rescaling changes feature vectors, not images.}\n"
        "\\label{tab:calibration}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrcr@{}}\n\\toprule\n"
        "Configuration & $D$ & $D_{\\mathrm{agg}}$ & $V_{\\mathrm{scene}}$ & $\\beta/\\sqrt{Q}$"
        " & fitted scalar & $D_{\\mathrm{held}}$\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_coverage(rows, hand, square) -> str:
    body = []
    for title, r, hnd, sq in zip(TITLES, rows, hand, square, strict=True):
        body.append(
            f"{title} & "
            + " & ".join(f3(v) for v in r["components"])
            + " & "
            + " & ".join(f3(v) for v in r["omit"])
            + f" & {f3(hnd['ms_beta'])} & {f3(sq['beta'])}\\\\"
        )
    return (
        provenance("review_v1", "review_v3") + "\\begin{table}[ht]\n"
        "\\caption{Which painter differences carry the aligned response. Components: aligned"
        " amplitude along each of the three singular components of the centered reference"
        " means (66.3\\%, 20.6\\% and 13.0\\% of their spread). Omitting a painter recenters"
        " the other three and recomputes $\\beta$. Monet--Sisley $\\beta$ is shown for full"
        " frames and for central-square reference windows.}\n"
        "\\label{tab:coverage}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrrrrr@{}}\n\\toprule\n"
        " & \\multicolumn{3}{c}{Component} & \\multicolumn{4}{c}{$\\beta$ after omitting}"
        " & \\multicolumn{2}{c}{Monet--Sisley $\\beta$}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-8}\\cmidrule(l){9-10}\n"
        "Configuration & 1st & 2nd & 3rd & " + " & ".join(PAINTERS) + " & full & square\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_sensitivity(data, sc) -> str:
    content = {row["model"]: row for row in data["review_v1"]["content"]["models"]}
    weighting = data["review_v1"]["weighting"]
    body = []
    orig = sc["original"]["models"]
    crop = sc["regions_original_scaler"]["models"]
    refit = sc["regions_refitted_scaler"]["models"]
    for i, title in enumerate(TITLES):
        c = content[title]
        body.append(
            f"{title} & {f3(orig[i]['d'])} & {f3(c['pooled_d'])} & {f3(c['conditional_d'])}"
            f" & {f3(weighting['equal_family'][i]['d'])}"
            f" & {f3(weighting['development_covariance'][i]['d'])}"
            f" & {f3(crop[i]['d'])} & {f3(refit[i]['d'])}\\\\"
        )
    return (
        provenance("review_v1", "quality") + "\\begin{table}[ht]\n"
        "\\caption{Error $D$ under alternative targets, weightings and source corrections."
        " Class target: title-derived water, built and land reference means for the 11"
        " matching scenes (pooled: the same 11 scenes against the pooled target)."
        " Equal family: each feature family has equal total weight. Covariance:"
        " shrunk inverse covariance of the development panel. Cropped: AI-audited"
        " painting regions with the original scaler; refit: also refitting the"
        " development scaling. Each column has its own normalizer.}\n"
        "\\label{tab:sensitivity}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrrr@{}}\n\\toprule\n"
        " & & \\multicolumn{2}{c}{11 scenes} & \\multicolumn{2}{c}{Weighting}"
        " & \\multicolumn{2}{c}{Source correction}\\\\\n"
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\\cmidrule(l){7-8}\n"
        "Configuration & Primary & pooled & class & equal family & covariance"
        " & cropped & refit\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_transfer(clip, csd) -> str:
    body = []
    for i, title in enumerate(TITLES):
        c, s = clip["rows"][i], csd["rows"][i]
        body.append(
            f"{title} & {pct(c['B'])} & {pct(c['T'])} & {pct(c['G'])}"
            f" & {pct(s['B'])} & {pct(s['T'])} & {pct(s['G'])}\\\\"
        )
    body.append(
        "\\midrule\nMean change vs.\\ B (pp) & & "
        f"{signed_pct(clip['mean_T'])} & {signed_pct(clip['mean_G'])} & & "
        f"{signed_pct(csd['mean_T'])} & {signed_pct(csd['mean_G'])}\\\\"
    )
    return (
        provenance("transfer") + "\\begin{table}[ht]\n"
        "\\caption{Held-scene recognition of the prompted painter (\\%, 112 named images per"
        " configuration, chance 25\\%). B: nearest reference prototype. T: the same after"
        " adding one fixed translation that aligns the generated and reference mixture"
        " means, fitted on the other 13 scenes without painter labels. G: nearest"
        " generated-image prototype fitted with painter labels on the other 13 scenes."
        " T and G use more information than B, and G more than T.}\n"
        "\\label{tab:transfer}\n\\centering\\small\n"
        "\\begin{tabular}{@{}lrrrrrr@{}}\n\\toprule\n"
        " & \\multicolumn{3}{c}{CLIP} & \\multicolumn{3}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(l){5-7}\n"
        "Configuration & B & T & G & B & T & G\\\\\n"
        "\\midrule\n" + rows_tex(body) + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def table_scenes(scenes) -> str:
    body = [f"{s['index'] + 1} & {s['content']} & {s['brief']}\\\\" for s in scenes]
    return (
        provenance("requests") + "\\begin{table}[ht]\n"
        "\\caption{The 14 scene descriptions, with their fixed content class. Each prompt is"
        " the clause, the description and ``No text or frame.''}\n"
        "\\label{tab:scenes}\n\\centering\\small\n"
        "\\begin{tabular}{@{}rlp{0.78\\linewidth}@{}}\n\\toprule\n"
        "\\# & Class & Scene description\\\\\n\\midrule\n"
        + "\n".join(body)
        + "\n\\bottomrule\n\\end{tabular}\n\\end{table}\n"
    )


def figure_components(rows, path: Path | None) -> bytes:
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams.update(
        {
            "pdf.fonttype": 42,
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "svg.hashsalt": "tmlr",
            "path.simplify": False,
        }
    )
    import matplotlib.pyplot as plt

    h = rows[0]["H"]
    shared = [r["N"] / h for r in rows]
    between = [r["B"] / h for r in rows]
    fig, ax = plt.subplots(figsize=(6.3, 2.7))
    n = len(rows)
    ys = list(range(n))[::-1]
    height = 0.36
    for y, s, b in zip(ys, shared, between, strict=True):
        ax.barh(y + height / 2 + 0.02, s, height=height, color=BLUE, linewidth=0)
        ax.barh(y - height / 2 - 0.02, b, height=height, color=ORANGE, linewidth=0)
        ax.text(
            s + 0.06,
            y + height / 2 + 0.02,
            f"{s:.2f}",
            va="center",
            color=INK,
            fontsize=7,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.6),
            zorder=4,
        )
        ax.text(
            b + 0.06,
            y - height / 2 - 0.02,
            f"{b:.2f}",
            va="center",
            color=INK,
            fontsize=7,
            bbox=dict(facecolor="white", edgecolor="none", pad=0.6),
            zorder=4,
        )
    ax.axvline(1.0, color=MUTED, linestyle=(0, (3, 2)), linewidth=1, zorder=3)
    ax.set_yticks(ys, SHORT)
    ax.set_xlim(0, max(shared) * 1.1)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xlabel("Repeat-corrected squared change, in units of $H$")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=MUTED)
    ax.grid(axis="x", color="#e4e3df", linewidth=0.6)
    ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    ax.legend(
        handles=[
            Patch(color=BLUE, label="shared by the four names ($N$)"),
            Patch(color=ORANGE, label="between names ($B$)"),
            Line2D(
                [0],
                [0],
                color=MUTED,
                linestyle=(0, (3, 2)),
                linewidth=1,
                label="reference painter spread ($H$)",
            ),
        ],
        loc="lower left",
        bbox_to_anchor=(0, 1.0),
        ncol=3,
        frameon=False,
        fontsize=7,
        handlelength=1.6,
        borderaxespad=0.2,
    )
    fig.tight_layout(pad=0.3)
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="pdf",
        metadata={"CreationDate": None, "ModDate": None, "Creator": None, "Producer": None},
    )
    plt.close(fig)
    content = buffer.getvalue()
    if path is not None:
        path.write_bytes(content)
    return content


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


# ---------------------------------------------------------------------------
# Claims quoted in the prose


def claims(data) -> dict[str, str]:
    hand = hand_decomposition(data)
    agree = agreement(data)
    pairs = contrasts(data)
    clip, csd = learned(data, "clip"), learned(data, "csd")
    tclip, tcsd = transfer(data, "clip"), transfer(data, "csd")
    cross = cross_cohort(data)
    sc = source_correction(data)
    scenes = scenes_from_requests(data["requests"])
    h = hand[0]["H"]
    idx = {t: i for i, t in enumerate(TITLES)}
    gpt2, nb2, flux, gpt1 = (
        idx["GPT Image 2"],
        idx["Nano Banana 2"],
        idx["FLUX.2 Max"],
        idx["GPT Image 1"],
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
    ms_hand = [r["ms_beta"] for r in hand]
    ms_other = [v for i, v in enumerate(ms_hand) if i != gpt2]
    require(
        max(ms_hand) == ms_hand[gpt2], "GPT Image 2 should have the largest hand Monet-Sisley beta"
    )
    tclip_d = [r["dT"] for r in tclip["rows"]]
    tcsd_d = [r["dT"] for r in tcsd["rows"]]
    require(
        all(r["G"] > max(r["B"], r["T"]) for r in tclip["rows"] + tcsd["rows"]),
        "generated prototypes should win all 12 combinations",
    )
    require(all(v > 0 for v in tcsd_d), "all CSD translation changes should be positive")
    signs = [(v > 1e-12) - (v < -1e-12) for v in tclip_d]
    require(sorted(signs) == [-1, -1, 0, 1, 1, 1], f"CLIP translation signs changed: {signs}")
    ref_orig = sc["original"]["models"][flux]["d"]
    refit = sc["regions_refitted_scaler"]
    comps = refit["comparisons"]
    resolved_refit = sorted(
        k
        for k, c in comps.items()
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
    require(
        abs(ref_orig - agree[flux]["d"]) < 1e-9, "source-quality original view must equal primary D"
    )
    interaction_signs = [r["I"] > 0 for r in hand]
    require(interaction_signs == [False, True, True, True, True, True], "cross-term signs changed")
    require(min(r["d"] for r in agree) == agree[flux]["d"], "FLUX should have the lowest primary D")
    require(
        min(r["accuracy"] for r in clip) == clip[flux]["accuracy"], "FLUX lowest CLIP recognition"
    )
    require(min(r["accuracy"] for r in csd) == csd[flux]["accuracy"], "FLUX lowest CSD recognition")
    require(max(r["gain"] for r in clip) == clip[nb2]["gain"], "Nano Banana 2 largest CLIP gain")
    require(min(r["gain"] for r in csd) == csd[gpt2]["gain"], "GPT Image 2 smallest CSD gain")
    require(
        max(r["accuracy"] for r in csd) == csd[gpt2]["accuracy"], "GPT Image 2 best CSD recognition"
    )
    require(
        max(r["accuracy"] for r in clip) == clip[gpt2]["accuracy"],
        "GPT Image 2 best CLIP recognition",
    )
    require(all(r["beta_ci"][0] > 0 for r in agree), "all beta intervals above zero")
    require(all(r["ms_beta"] > 0 for r in clip + csd), "learned Monet-Sisley betas positive")
    crossings = covariance_crossings(data)
    require(
        len(crossings) == 3 and all(0 < v < 1 for v in crossings.values()),
        "covariance crossings changed",
    )
    sims = {row["scenario"]: row["family_coverage"] for row in data["review_v1"]["simulation"]}
    for rep in ("clip", "csd"):
        for view in ("original", "audited_region"):
            for target in ("primary", "development"):
                gains = learned(data, rep, view, target)
                require(
                    all(r["common_gain"] > 0 for r in gains),
                    "shared prototype-gain term must be positive",
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
        require(
            min(column) == column[flux],
            "FLUX.2 Max should keep the lowest D in every sensitivity column",
        )
    return {
        "H": f3(h),
        "shared_free": span([r["share_free"] for r in hand], pct),
        "shared_generic": span([r["share_generic"] for r in hand], pct),
        "shared_generic_deletion": span([v for r in hand for v in r["range_generic"]], pct),
        "shared_within": span([r["within_share"] for r in agree], pct),
        "N_over_H": span([r["N"] / h for r in hand], lambda v: f"{v:.1f}"),
        "B_over_H": span([r["B"] / h for r in hand], lambda v: f"{v:.1f}"),
        "G_over_H": span([r["G"] / h for r in hand], lambda v: f"{v:.1f}"),
        "gpt2_share_generic": pct(hand[gpt2]["share_generic"]),
        "gpt2_beta": f3(agree[gpt2]["beta"]),
        "gpt2_beta_ci": interval(agree[gpt2]["beta_ci"]),
        "gpt2_q": f3(agree[gpt2]["q"]),
        "gpt2_d": f3(agree[gpt2]["d"]),
        "gpt2_B_over_H": f2(hand[gpt2]["B"] / h),
        "flux_d": f3(agree[flux]["d"]),
        "flux_d_ci": interval(agree[flux]["d_ci"]),
        "flux_beta": f3(agree[flux]["beta"]),
        "flux_q": f3(agree[flux]["q"]),
        "flux_share_generic": pct(hand[flux]["share_generic"]),
        "beta_range": span([r["beta"] for r in agree], f3),
        "ms_hand_other": span(ms_other, m3, sep=" to "),
        "ms_hand_gpt2": f3(ms_hand[gpt2]),
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
        "clip_change_generic": span([r["change_generic"] for r in clip], pct),
        "csd_change_generic": span([r["change_generic"] for r in csd], pct),
        "nb2_clip_gain": f3(clip[nb2]["gain"]),
        "nb2_clip_acc": pct(clip[nb2]["accuracy"]),
        "gpt2_clip_gain": f3(clip[gpt2]["gain"]),
        "gpt2_clip_acc": pct(clip[gpt2]["accuracy"]),
        "gpt2_csd_gain": f3(csd[gpt2]["gain"]),
        "gpt2_csd_acc": pct(csd[gpt2]["accuracy"]),
        "flux_clip_acc": pct(clip[flux]["accuracy"]),
        "flux_csd_acc": pct(csd[flux]["accuracy"]),
        "flux_csd_d": f3(csd[flux]["d"]),
        "gpt1_clip_d": f3(clip[gpt1]["d"]),
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
        "sd_C_over_H": f2(cross["all31"]["C"] / cross["all31"]["H"]),
        "sd_L_over_H": f2(cross["all31"]["L"] / cross["all31"]["H"]),
        "sd_beta": f3(cross["all31"]["beta"]),
        "sd_d": f3(cross["all31"]["d"]),
        "sd_d_scene": f3(cross["all31"]["d_scene"]),
        "sd_ms": f3(cross["all31"]["ms"]),
        "flux_d_refit": f3(refit["models"][flux]["d"]),
        "flux_d_crop": f3(sc["regions_original_scaler"]["models"][flux]["d"]),
        "scene_count": str(len(scenes)),
        "flux_N_over_H": f2(hand[flux]["N"] / h),
        "flux_B_over_H": f2(hand[flux]["B"] / h),
        "cov_nb2_flux": f3(crossings[("Nano Banana 2", "FLUX.2 Max")]),
        "cov_gpt1_gpt2": f3(crossings[("GPT Image 1", "GPT Image 2")]),
        "sim_gaussian": pct(sims["gaussian"]),
        "sim_heavy": pct(sims["heavy_heteroskedastic"]),
        "sim_interaction": pct(sims["scene_interaction"]),
        "sim_shared": pct(sims["shared_state"], 2),
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
    outputs: dict[str, str | bytes] = {
        "tab_decomposition.tex": table_decomposition(hand),
        "tab_agreement.tex": table_agreement(agree),
        "tab_learned.tex": table_learned(hand, clip, csd),
        "tab_readouts.tex": table_readouts(agree, clip, csd),
        "tab_sdturbo.tex": table_sdturbo(cross_cohort(data)),
        "tab_pairs.tex": table_pairs(contrasts(data)),
        "tab_calibration.tex": table_calibration(agree),
        "tab_coverage.tex": table_coverage(agree, hand, square_monet_sisley(data)),
        "tab_sensitivity.tex": table_sensitivity(data, source_correction(data)),
        "tab_transfer.tex": table_transfer(transfer(data, "clip"), transfer(data, "csd")),
        "tab_scenes.tex": table_scenes(scenes_from_requests(data["requests"])),
    }
    outputs["fig_components.pdf"] = figure_components(hand, None)
    return outputs


def check_claims(values: dict[str, str], registry_path: Path) -> list[str]:
    """Every registered claim must appear verbatim in the manuscript."""
    text = "\n".join(path.read_text() for path in MANUSCRIPT if path.exists())
    text = re.sub(r"(?m)^%.*$", "", text)
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
        if problems:
            print("\n".join(problems), file=sys.stderr)
            return 1
        print(
            f"ok: {len(outputs)} generated files and {len(json.loads(registry.read_text()))} claims"
        )
        return 0
    OUT.mkdir(exist_ok=True)
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
