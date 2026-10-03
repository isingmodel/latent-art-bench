"""Build the TMLR manuscript's generated tables and figure from retained analyses.

Run ``uv run --locked python paper/tmlr/build_assets.py`` to write the files in
``paper/tmlr/generated/``. ``--check`` writes nothing: it verifies the recorded
input hashes, exact equality of every generated file, and that each number quoted
in the manuscript prose matches its source analysis and appears in the sentence
context registered for it in ``claims.json``.

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
import statistics
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
    "diagnostics3": (
        "reports/painter_tmlr_diagnostics_v3/analysis.json",
        "2aa36a87cd6d23ee909cdf94bd9f512d5743138f1d8a8f7c236d56f33fbceb57",
    ),
    "diagnostics4": (
        "reports/painter_tmlr_diagnostics_v4/analysis.json",
        "67431bd384586f294651136b214b9649cfd911059133ec79181eec7527d6b67b",
    ),
    "diagnostics5": (
        "reports/painter_tmlr_diagnostics_v5/analysis.json",
        "5747902e4fae5ff111a52b5f2b8da112bc26c611555e82314b278de953981f6b",
    ),
    "timing": (
        "reports/painter_request_timing_v1/analysis.json",
        "80807c9ce3167ee853c354899a3fc750d8d330e17e5569135eb46e627819cceb",
    ),
    "primary": (
        "data/manifests/painter_specificity_v2/psv2-20260911/analysis.json",
        "c1d21b16f840a10fd253c1d558743a09671acf3d4e48601ddcc96625a5a90be0",
    ),
    "requests": (
        "data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl",
        "0aa60f491be08dbd48f1f018e225b22bcae2aacd724abf3371a6312d59acc679",
    ),
    "v3_determination": (
        "data/manifests/painter_specificity_v3/refs-20261002/determination_receipt.json",
        "39e289f1ba44c7d5fe8ae18d59d076a07eb1cefd6d105859b3565bb6576fa982",
    ),
    "v3_references": (
        "data/manifests/painter_specificity_v3/refs-20261002/measurement_receipt.json",
        "debf37377410a96cd64f1714a277ade667d959714c0c13bbd7af986de0795c16",
    ),
    "v3_predictions": (
        "data/manifests/painter_specificity_v3/refs-20261002/predictions.json",
        "65a12c297f2f2e0c2d6d7afbb313e590bf7360001cbe82c5edc5fed20040414f",
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
V3_GROUPS = (
    ("century", "Century group", (
        ("jacob_van_ruisdael", "van Ruisdael"), ("canaletto", "Canaletto"),
        ("vincent_van_gogh", "van Gogh"), ("ernst_ludwig_kirchner", "Kirchner"))),
    ("hudson", "Hudson River School", (
        ("albert_bierstadt", "Bierstadt"), ("frederic_edwin_church", "Church"),
        ("thomas_cole", "Cole"), ("asher_brown_durand", "Durand"))),
)
V3_PAINTERS = tuple(p for _, _, painters in V3_GROUPS for p in painters)
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


def diagnostics3(data) -> dict:
    d3 = data["diagnostics3"]
    require(d3["models"] == list(MODELS), "diagnostics v3 model order changed")
    return d3


def diagnostics4(data) -> dict:
    d4 = data["diagnostics4"]
    require(d4["models"] == list(MODELS), "diagnostics v4 model order changed")
    return d4


def diagnostics5(data) -> dict:
    d5 = data["diagnostics5"]
    require(d5["models"] == list(MODELS), "diagnostics v5 model order changed")
    return d5


def pairwise_intervals(data) -> dict:
    out = {}
    for row in data["contrasts"]:
        out[(row["model_a"], row["model_b"])] = dict(
            diff=float(row["difference"]),
            sim=parse_interval(row["simultaneous_ci"]),
            nominal=parse_interval(row["nominal_ci"]),
            boot=tuple(json.loads(row["bootstrap_ci95"])),
        )
    return out


def six_way_d_intervals(data) -> list[tuple[float, float]]:
    from scipy.stats import t as student

    rows = data["primary"]["models"]
    crit = float(student.ppf(1 - 0.05 / 12, 13))
    return [
        (
            r["distortion"]["mean"] - crit * r["distortion"]["se"],
            r["distortion"]["mean"] + crit * r["distortion"]["se"],
        )
        for r in rows
    ]


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
# Two further painter groups (painter_specificity_v3)


def table_v3_panels(det, meas) -> str:
    gates = ("passed_creator", "passed_medium", "passed_collection", "passed_rights",
             "passed_geometry", "passed_content")
    body = []
    for group, title, painters in V3_GROUPS:
        body.append(f"\\multicolumn{{10}}{{l}}{{\\emph{{{title}}}}} \\\\")
        for pid, name in painters:
            f = det["funnel"][pid]
            classes = f["classes"]
            mix = "/".join(str(classes.get(c, 0)) for c in (
                "water_organized", "built_place_organized", "route_organized",
                "open_or_wooded_land"))
            body.append(" & ".join([name, str(f["discovered"]), *(str(f[g]) for g in gates),
                                    str(meas["measured_by_painter"][pid]), mix]) + " \\\\")
    total = sum(meas["measured_by_painter"][p] for p, _ in V3_PAINTERS)
    require(total == 788, "v3 reference panel size")
    return table(
        "tab:v3-panels",
        "Reference panels of the two further painter groups: Wikidata paintings with a Commons "
        "image, and how many remain after each gate, applied in order as for the four-painter "
        "panel (single creator, oil on canvas, a collection, an open licence, a short side of at "
        "least 1,024 pixels, an outdoor title); then works measured after merging duplicates and "
        "excluding unreadable files. Classes are water/built/route/land by title.",
        "lrrrrrrrrr",
        "Painter & Found & Creator & Medium & Coll. & Rights & Size & Title & Measured & "
        "W/B/R/L \\\\",
        body, "v3_determination", "v3_references", size="\\footnotesize")


def table_v3_predictions(pred) -> str:
    names = {"impressionists": "Four Impressionists", "century": "Century group",
             "hudson": "Hudson River School"}
    reps = (("hand31", "31 features", f2), ("clip", "CLIP", m3), ("csd", "CSD", m3))
    body = []
    for key, title in names.items():
        cells = [title]
        for rep, _, fmt in reps:
            v = pred[rep][key]
            cells += [fmt(v["H"]), span(v["faithful_shared_fraction"], pct)]
        body.append(" & ".join(cells) + " \\\\")
    return table(
        "tab:v3-predictions",
        "Predictions recorded before the second collection: the reference spread $H$ of each "
        "group and the faithful benchmark $N^*/(N^*+H)$ over the six configurations, with "
        "September's generic outputs. The four-painter rows reproduce the paper's values.",
        "lrrrrrr",
        "& \\multicolumn{2}{c}{31 features} & \\multicolumn{2}{c}{CLIP} & "
        "\\multicolumn{2}{c}{CSD} \\\\\n\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n"
        "Group & $H$ & Faithful & $H$ & Faithful & $H$ & Faithful \\\\",
        body, "v3_predictions")


AQUA = "#1baf7a"  # validated categorical slot 3 (light surface); relief by marker shape
V3_REPS = (("hand31", "31 features"), ("hand31_square", "31 features, central square"),
           ("clip", "CLIP"), ("csd", "CSD"))


def v3rep(v3, rep):
    out = v3["representations"][rep]
    require(out["available"], f"v3 {rep} analysis unavailable")
    return out


def table_v3_shared(v3, diag2) -> str:
    hand = v3rep(v3, "hand31")
    close = hand["closeness"]
    body = []
    for m, name in enumerate(SHORT):
        imp = diag2["hand31"][m]["point"]["all31"]
        cen, hud = hand["groups"]["century"][m], hand["groups"]["hudson"][m]
        diff = close["difference_by_configuration"][m]
        require(abs(diff - (cen["shared_fraction"] - hud["shared_fraction"])) < 1e-12,
                "v3 closeness difference")
        lo, hi = close["simultaneous_ci_by_configuration"][m]
        body.append(
            f"{name} & {pct(imp['observed'])} & {pct(imp['faithful'])}"
            f" & {pct(cen['shared_fraction'])} & {pct(cen['faithful_shared_fraction'])}"
            f" & {pct(hud['shared_fraction'])} & {pct(hud['faithful_shared_fraction'])}"
            f" & {signed_pct(diff)} & {rng((lo, hi), signed_pct)}\\\\"
        )
    lo, hi = close["pooled_ci95"]
    body.append("\\midrule")
    body.append(
        f"Mean & & & & & & & {signed_pct(close['pooled_difference'])} & {rng((lo, hi), signed_pct)}"
        "\\\\"
    )
    header = (
        " & \\multicolumn{2}{c}{Impressionists} & \\multicolumn{2}{c}{Century group}"
        " & \\multicolumn{2}{c}{Hudson River} & \\multicolumn{2}{c}{Century $-$ Hudson}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(l){8-9}\n"
        "Configuration & obs. & faithful & obs. & faithful & obs. & faithful & diff. & 95\\%\\\\"
    )
    caption = (
        "Shared fraction $N/(N+B)$ (\\%) of what the four names add beyond the generic clause, "
        "observed and for a faithful imitator, in the 31 features, for the four Impressionists "
        "(first collection) and the two further groups (second collection, each with its own "
        "generic arm). Last columns: the century group's fraction minus the Hudson River "
        "School's, with Bonferroni-adjusted (six configurations) percentile intervals from "
        "5,000 paired scene resamples; the mean row is the prespecified test H1, with its "
        "95\\% interval."
    )
    return table("tab:v3-shared", caption, "@{}lrrrrrrrc@{}", header, body, "diagnostics2", "v3",
                 size="\\small\\setlength{\\tabcolsep}{3.5pt}")


def table_v3_tests(v3) -> str:
    body = []
    for rep, title in V3_REPS:
        out = v3rep(v3, rep)
        c, d, u = out["closeness"], out["dose_response"], out["dose_response_uncorrected"]
        spread = out["reference_spread"]
        hfmt = f2 if rep.startswith("hand31") else m3
        body.append(
            f"{title} & {signed_pct(c['pooled_difference'])} & {rng(c['pooled_ci95'], signed_pct)}"
            f" & {f2(d['pooled_spearman'])} & {pvalue(d['exact_p_one_sided'])}"
            f" & {f2(u['pooled_spearman'])} & {pvalue(u['exact_p_one_sided'])}"
            f" & {hfmt(spread['century']['H_corrected'])} & {hfmt(spread['hudson']['H_corrected'])}"
            "\\\\"
        )
    header = (
        " & \\multicolumn{2}{c}{H1: century $-$ Hudson} & \\multicolumn{2}{c}{H2: Mantel}"
        " & \\multicolumn{2}{c}{H2, uncorrected} & \\multicolumn{2}{c}{$H$, noise-corrected}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(l){8-9}\n"
        "Representation & diff. & 95\\% & $\\rho$ & $p$ & $\\rho$ & $p$ & century & Hudson\\\\"
    )
    caption = (
        "The two prespecified tests in every representation (the 31 features in the full view "
        "are primary). H1: mean over configurations of the century group's shared fraction "
        "minus the Hudson River School's (percentage points), with a 95\\% interval from 5,000 "
        "paired scene resamples. H2: Spearman correlation over the 28 painter pairs between the "
        "name distance and the reference distance, averaged over configurations, with the exact "
        "one-sided $p$-value over all 40,320 relabellings of the eight painters; the reference "
        "distances are corrected for panel size, and the uncorrected test is shown beside it. "
        "Last columns: reference spread corrected for panel size."
    )
    return table("tab:v3-tests", caption, "@{}lrcrrrrrr@{}", header, body, "v3",
                 size="\\small\\setlength{\\tabcolsep}{4pt}")


def table_v3_detail(v3) -> str:
    hand = v3rep(v3, "hand31")
    body = []
    for group, title, _ in V3_GROUPS:
        body.append(f"\\multicolumn{{9}}{{l}}{{\\emph{{{title}}}}}\\\\")
        for name, row in zip(SHORT, hand["groups"][group], strict=True):
            body.append(
                f"{name} & {f2(row['beta'])} & {rng(row['beta_ci95'], f2)} & {f2(row['Q'])}"
                f" & {f2(row['alignment_ratio'])} & {f2(row['D'])} & {rng(row['D_ci95'], f2)}"
                f" & {f2(row['D_held'])} & {opt(row['centroid_gain_shared_fraction'], pct)}\\\\"
            )
    header = (
        "Configuration & $\\beta$ & 95\\% & $Q$ & $\\beta/\\sqrt{Q}$ & $D$ & 95\\%"
        " & $D_{\\mathrm{held}}$ & shared gain (\\%)\\\\"
    )
    caption = (
        "Agreement of the between-name differences with each group's reference differences "
        "(31 features, second collection), as in Table~\\ref{tab:agreement}: aligned amplitude "
        "$\\beta$ and error $D$ with unadjusted paired-scene Student intervals, relative size "
        "$Q$, alignment ratio, held-out rescaled error, and the share of the centroid proximity "
        "gain (Eq.~\\ref{eq:prototype-gain}, here in the features) carried by the shared term."
    )
    return table("tab:v3-detail", caption, "@{}lrcrrrcrr@{}", header, body, "v3",
                 size="\\small\\setlength{\\tabcolsep}{4pt}")


def table_v3_drift(v3) -> str:
    body = []
    reps = (("hand31", "31 features"), ("clip", "CLIP"), ("csd", "CSD"))
    for m, name in enumerate(SHORT):
        cells = [name]
        for rep, _ in reps:
            drift = v3rep(v3, rep)["drift"][m]
            cells += [f2(drift["free"]["ratio"]), f2(drift["generic"]["ratio"])]
        body.append(" & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{2}{c}{31 features} & \\multicolumn{2}{c}{CLIP}"
        " & \\multicolumn{2}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(l){6-7}\n"
        "Configuration & none & generic & none & generic & none & generic\\\\"
    )
    caption = (
        "Change between the two collections for identical requests: the squared distance "
        "between the September and October scene means of the no-clause and generic arms, "
        "estimated without repeat noise, divided by September's repeat noise (0 means no "
        "change; values near or above 1 mean a change as large as two repeats differ)."
    )
    return table("tab:v3-drift", caption, "@{}lrrrrrr@{}", header, body, "v3")


def figure_v3_pairs(v3) -> bytes:
    """Name distance against reference distance for the 28 pairs of the eight new painters."""
    plt = _matplotlib()
    import numpy as np

    group_of = [g for g, _, painters in V3_GROUPS for _ in painters]
    pairs = [(a, b) for a in range(8) for b in range(a + 1, 8)]
    kinds = ["century" if group_of[a] == group_of[b] == "century"
             else "hudson" if group_of[a] == group_of[b] == "hudson" else "cross"
             for a, b in pairs]
    style = {"century": (BLUE, "o", "within century group"),
             "hudson": (ORANGE, "s", "within Hudson River School"),
             "cross": (AQUA, "^", "across groups")}
    reps = (("hand31", "31 features"), ("clip", "CLIP"), ("csd", "CSD"))
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.4))
    for ax, (rep, title) in zip(axes, reps, strict=True):
        d = v3rep(v3, rep)["dose_response"]
        x = np.array(d["reference_pairs"])
        y = np.array(d["name_pairs_by_configuration"]).mean(axis=0)
        for kind, (color, marker, label) in style.items():
            keep = [i for i, k in enumerate(kinds) if k == kind]
            ax.scatter(x[keep], y[keep], s=16, c=color, marker=marker, label=label,
                       edgecolors="white", linewidths=0.5)
        ax.set_title(f"{title}: $\\rho$ = {d['pooled_spearman']:.2f}", fontsize=8, color=INK)
        ax.set_xlabel("reference distance$^2$", fontsize=7, color=MUTED)
        if ax is axes[0]:
            ax.set_ylabel("name distance$^2$", fontsize=7, color=MUTED)
        ax.tick_params(labelsize=6, colors=MUTED)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].legend(fontsize=6, frameon=False, loc="upper left")
    fig.subplots_adjust(left=0.08, right=0.99, bottom=0.18, top=0.88, wspace=0.3)
    return _pdf_bytes(fig, plt)


def pvalue(p: float) -> str:
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def opt(value, fmt) -> str:
    return "--" if value is None else fmt(value)


# ---------------------------------------------------------------------------
# Main-text tables


def table_shared(diag, diag2) -> str:
    body = []
    for name, d, d2 in zip(SHORT, diag["hand31"], diag2["hand31"], strict=True):
        a = d["families"]["all31"]
        p, b = d2["point"]["all31"], d2["scene_bootstrap"]["all31"]
        require(abs(p["observed"] - a["shared_fraction"]) < 1e-12, "v1/v2 shared fraction")
        require(abs(p["exact"] - a["N_over_H"] / (a["N_over_H"] + 1)) < 1e-12, "exact = N/(N+H)")
        body.append(
            f"{name} & {pct(p['observed'])} & {rng(b['observed'])} & {f2(a['N_over_H'])}"
            f" & {f2(a['B_over_H'])} & {pct(p['faithful'])} & {pct(p['exact'])}"
            f" & {pct(b['observed_below_faithful'])}\\\\"
        )
    header = (
        " & \\multicolumn{4}{c}{Observed} & \\multicolumn{3}{c}{Benchmarks}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-8}\n"
        "Configuration & fraction (\\%) & scene 95\\% & $N/H$ & $B/H$ & faithful (\\%)"
        " & exact diff.\\ (\\%) & obs.$<$faithful (\\%)\\\\"
    )
    caption = (
        "Shared fraction $N/(N+B)$ of what the four names add beyond the generic clause (31"
        " features), with a 95\\% interval from 5,000 scene resamples, and the squared sizes of"
        " the shared change ($N$) and of the between-name differences ($B$) relative to the"
        " reference painter spread $H$. Faithful: the fraction if each named mean equalled the"
        " painter's reference mean, from the same generic outputs. Exact differences: the"
        " fraction if the observed shared change were kept and $B/H$ were 1, $N/(N+H)$."
        " Obs.$<$faithful: share of scene resamples in which the observed fraction is below the"
        " faithful one. Appendix Table~\\ref{tab:direction} gives the direction of the shared"
        " change."
    )
    return table(
        "tab:shared",
        caption,
        "@{}lrcrrrrr@{}",
        header,
        body,
        "diagnostics",
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_direction(diag) -> str:
    body = []
    for name, d in zip(SHORT, diag["hand31"], strict=True):
        a = d["families"]["all31"]
        require(
            abs(a["fraction_along_generic"] - a["generic_cosine"] ** 2) < 1e-9,
            "along-generic share should equal the squared cosine",
        )
        body.append(
            f"{name} & {f2(a['direction_cosine'])} & {pct(a['projection_ratio'])}"
            f" & {f2(a['generic_cosine'])} & {pct(a['fraction_along_generic'])}\\\\"
        )
    header = (
        "Configuration & $\\cos(c,t)$ & covered, $\\lambda$ (\\%) & $\\cos(c,g)$"
        " & along generic (\\%)\\\\"
    )
    caption = (
        "Direction of the shared change $c$ in the 31 features, with cosines corrected by"
        " cross-repeat products. $\\cos(c,t)$: cosine with the vector $t$ from the generic mean"
        " to the reference centroid. Covered: $\\lambda=\\langle c,t\\rangle/\\|t\\|^2$, the"
        " fraction of $t$ covered along its direction. $\\cos(c,g)$: cosine with the"
        " artist-free-to-generic shift $g$. Along generic: the share of $N$ along $g$,"
        " $\\cos^2(c,g)$."
    )
    return table("tab:direction", caption, "@{}lrrrr@{}", header, body, "diagnostics")


def table_agreement(rows, resample, diag2) -> str:
    body = []
    joint = diag2["joint_d_below_one"]
    for name, r, ref, j in zip(SHORT, rows, resample, joint, strict=True):
        body.append(
            f"{name} & {f3(r['beta'])} & {interval(r['beta_ci'])} & {interval(ref['beta'])}"
            f" & {f3(r['q'])} & {f3(r['align'])} & {f3(r['d'])} & {interval(r['d_ci'])}"
            f" & {interval(ref['d'])} & {pct(j)}\\\\"
        )
    header = (
        " & \\multicolumn{3}{c}{Aligned amplitude $\\beta$} & & &"
        " \\multicolumn{4}{c}{Error $D$}\\\\\n"
        "\\cmidrule(lr){2-4}\\cmidrule(l){7-10}\n"
        "Configuration & est. & scenes & references & $Q$ & $\\beta/\\sqrt{Q}$ & est. & scenes"
        " & references & $D<1$ (\\%)\\\\"
    )
    caption = (
        "Agreement of the between-name differences with the reference painter differences"
        " (31 features). $\\beta=1$ matches the reference pattern's size along its direction;"
        " $Q$ is the squared size of the generated differences relative to the reference, and"
        " $\\beta/\\sqrt{Q}$ their alignment with the reference pattern, unaffected by rescaling"
        " the differences (1 for a scaled copy of the reference pattern); $D=1-2\\beta+Q$ is 0"
        " for exact agreement and 1 when names produce"
        " no differences. Scenes: for $\\beta$, prespecified 95\\% simultaneous Student intervals"
        " over 21 endpoints; for $D$, unadjusted 95\\% Student intervals. References:"
        " prespecified 95\\% percentile intervals from resampling reference works within painter;"
        " resampling adds a second finite-sample bias to $H$, so these intervals for $\\beta$ lie"
        " slightly low. $D<1$: share of 2,000 joint resamples of scenes and reference works with"
        " $D$ below 1."
    )
    return table(
        "tab:agreement",
        caption,
        "@{}lrccrrrccr@{}",
        header,
        body,
        "models",
        "review_v1",
        "primary",
        "diagnostics2",
        size="\\small\\setlength{\\tabcolsep}{3pt}",
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
        " Faithful: the same share if every named mean embedding equalled the painter's mean"
        " reference embedding. Exact"
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


def table_readouts(clip, csd, diag5) -> str:
    body = []
    for rows, label, rep in ((clip, "CLIP", "clip"), (csd, "CSD", "csd")):
        if body:
            body.append("\\midrule")
        body.append(f"\\multicolumn{{7}}{{@{{}}l}}{{\\textit{{{label}}}}}\\\\")
        shared = [r["gain"] * r["common_gain"] for r in rows]
        specific = [r["gain"] * (1 - r["common_gain"]) for r in rows]
        cols = [
            bold_best([r["gain"] for r in rows], f3, True),
            [f3(v) for v in shared],
            bold_best(specific, f3, True),
            bold_best([r["accuracy"] for r in rows], pct, True),
            bold_best([r["alignment"] for r in diag5["agreement"][rep]], f3, True),
            bold_best([r["d"] for r in rows], f3, False),
        ]
        body += [
            f"{title} & " + " & ".join(col[i] for col in cols) + "\\\\"
            for i, title in enumerate(SHORT)
        ]
    header = (
        " & \\multicolumn{3}{c}{Proximity gain} & Recognition & \\multicolumn{2}{c}{Agreement}"
        "\\\\\n\\cmidrule(lr){2-4}\\cmidrule(l){6-7}\n"
        "Configuration & total & shared & painter-specific & (\\%) & $\\beta/\\sqrt{Q}$"
        " & $D$\\\\"
    )
    caption = (
        "Readouts of the same images in each embedding. Proximity: named-minus-generic"
        " gain in mean cosine similarity to the prompted painter's reference works, split by"
        " Equation~\\ref{eq:prototype-gain} into the shared term and the painter-specific term"
        " $H\\beta/4$. Recognition: macro accuracy of assigning each of the 112 named images to"
        " its prompted painter by the nearest reference prototype (chance 25\\%). Agreement:"
        " alignment ratio (higher is better) and error $D$ (lower is better);"
        " Table~\\ref{tab:agreement} gives the 31-feature values. Bold marks the largest value"
        " in each column and embedding (the lowest for $D$); Appendix"
        " Table~\\ref{tab:stability} shows how often each"
        " configuration is best under scene resampling."
    )
    return table(
        "tab:readouts",
        caption,
        "@{}lrrrrrr@{}",
        header,
        body,
        "learned",
        "diagnostics5",
        size="\\small",
    )


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


def table_stability(diag, diag5) -> str:
    body = [
        f"{r['label']} & {r['best']} & {pct(r['best_freq'])} & {r['second']}"
        f" & {pct(r['second_freq'])}\\\\"
        for r in stability_rows(diag)
    ]
    body.append("\\midrule")
    names = {"hand31": "31 features", "clip": "CLIP", "csd": "CSD"}
    for key, label in (("alignment", "Alignment ratio"), ("held_out_d", "$D_{\\mathrm{held}}$")):
        for rep, rep_label in names.items():
            freq = diag5["stability"][rep][key]
            ranked = sorted(freq.items(), key=lambda kv: -kv[1])
            body.append(
                f"{label}, {rep_label} & {SHORT[MODELS.index(ranked[0][0])]}"
                f" & {pct(ranked[0][1])} & {SHORT[MODELS.index(ranked[1][0])]}"
                f" & {pct(ranked[1][1])}\\\\"
            )
    header = "Readout & Most often best & \\% & Next & \\%\\\\"
    caption = (
        "Which configuration is best on each readout when the 14 scenes are resampled with"
        " replacement (5,000 paired resamples; the same scenes for every configuration)."
        " The percentages describe dependence on the authored scenes. Ties, which occur for"
        " recognition, are credited to the configuration listed first. Lower rows: alignment"
        " ratio and $D_{\\mathrm{held}}$ (separate resamples)."
    )
    return table(
        "tab:stability", caption, "@{}llrlr@{}", header, body, "diagnostics", "diagnostics5"
    )


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
    fams = [[d["families"][k] for d in diag["hand31"]] for k in keys]
    body.append(
        "\\quad faithful, mean & "
        + " & ".join(pct(sum(r["faithful_shared_fraction"] for r in f) / 6) for f in fams)
        + " & &\\\\"
    )
    body.append(
        "\\quad exact differences, mean & "
        + " & ".join(pct(sum(r["N_over_H"] / (r["N_over_H"] + 1) for r in f) / 6) for f in fams)
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
        " intervals for the mean over the six configurations from 5,000 scene resamples; the"
        " faithful and exact-differences rows average the six configurations' benchmark values"
        " in each family. The SD-Turbo row uses its own baseline, which already requests an oil"
        " painting."
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


def table_embedding_agreement(diag3, diag4, diag5) -> str:
    body = []
    for rep, label in (("clip", "CLIP"), ("csd", "CSD")):
        if body:
            body.append("\\midrule")
        body.append(f"\\multicolumn{{10}}{{@{{}}l}}{{\\textit{{{label}}}}}\\\\")
        held = bold_best([r["held_out_d"] for r in diag5["agreement"][rep]], f3, False)
        align = bold_best([r["alignment"] for r in diag5["agreement"][rep]], f3, True)
        for i, name in enumerate(SHORT):
            r3 = diag3["learned"][rep][i]
            r5 = diag5["agreement"][rep][i]
            c = diag4["learned"][rep][i]
            require(abs(r3["d"] - r5["d"]) < 1e-10, "v3/v5 embedding D")
            body.append(
                f"{name} & {f3(r5['beta'])} & {f3(r5['q'])} & {align[i]} & {f3(r5['d'])}"
                f" & {interval(r5['d_student'])} & {pct(r3['d_below_one_joint'])}"
                f" & {held[i]} & {f3(c['pooled_d'])} & {f3(c['class_d'])}\\\\"
            )
    header = (
        " & & & & \\multicolumn{3}{c}{Error $D$} & & \\multicolumn{2}{c}{11 scenes}\\\\\n"
        "\\cmidrule(lr){5-7}\\cmidrule(l){9-10}\n"
        "Configuration & $\\beta$ & $Q$ & $\\beta/\\sqrt{Q}$ & est. & scenes & $D<1$ (\\%)"
        " & $D_{\\mathrm{held}}$ & pooled & class\\\\"
    )
    caption = (
        "Agreement of the between-name differences with the reference differences in the"
        " embeddings. $\\beta/\\sqrt{Q}$ (alignment ratio) and $D_{\\mathrm{held}}$ (error after"
        " a held-out rescaling) are unaffected by rescaling the differences; bold marks the best in"
        " each embedding. Scenes: unadjusted paired-scene Student 95\\% intervals, as for $D$ in"
        " Table~\\ref{tab:agreement}. $D<1$: share of 2,000 joint scene and reference resamples."
        " 11 scenes: $D$ on the non-mixed scenes against the pooled target and against"
        " title-derived content-class targets."
    )
    return table(
        "tab:embedding-agreement",
        caption,
        "@{}lrrrrcrrrr@{}",
        header,
        body,
        "diagnostics3",
        "diagnostics4",
        "diagnostics5",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def table_genuine_controls(diag3, real) -> str:
    labels = {
        "pooled_real": "pooled sampling, pooled target",
        "class_real_pooled_target": "class sampling, pooled target",
        "class_real_class_target": "class sampling, class targets",
    }
    body = []
    for key, label in labels.items():
        cells = []
        for rep in ("hand31", "clip", "csd"):
            v = diag3["genuine_controls_distinct"][rep][key]
            cells += [f3(v["mean"]), interval(v["interval95"])]
        body.append(f"{label} & {f3(real[key]['mean'])} & " + " & ".join(cells) + "\\\\")
    header = (
        " & with repl. & \\multicolumn{6}{c}{Distinct works}\\\\\n"
        "\\cmidrule(l){3-8}\n"
        " & 31 features & \\multicolumn{2}{c}{31 features} & \\multicolumn{2}{c}{CLIP}"
        " & \\multicolumn{2}{c}{CSD}\\\\\n"
        "Control & mean & mean & 95\\% range & mean & 95\\% range & mean & 95\\% range\\\\"
    )
    caption = (
        "Error $D$ of held-out genuine paintings sampled like the generated images (1,000 random"
        " half-splits; two works per painter for each of 14 pseudo-scenes, or 11 with content"
        " classes). With repl.: the recorded control, whose two pseudo-repeats can be the same"
        " work. Distinct works: the two pseudo-repeats are different paintings, as the two"
        " generated repeats are different images."
    )
    return table(
        "tab:genuine",
        caption,
        "@{}lrrcrcrc@{}",
        header,
        body,
        "diagnostics3",
        "review_v1",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
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
            cells = [interval(r["sim"]), interval(r["nominal"]), interval(r["boot"])]
            body.append(
                f"{SHORT[i]} & {SHORT[j]} & {f3(r['diff'])} & " + " & ".join(cells) + "\\\\"
            )
    header = (
        "Configuration A & Configuration B & $D_A-D_B$ & simultaneous & nominal & bootstrap\\\\"
    )
    caption = (
        "All 15 prespecified pairwise error comparisons in the 31 features (positive values favor"
        " configuration B). Simultaneous: the prespecified 95\\% intervals adjusted over the"
        " 21-endpoint family. Nominal: unadjusted paired-scene Student intervals. Bootstrap:"
        " the protocol's descriptive, unadjusted 95\\% intervals from 5,000 paired scene resamples."
    )
    return table(
        "tab:pairs",
        caption,
        "@{}llrccc@{}",
        header,
        body,
        "contrasts",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_calibration(rows, primary) -> str:
    held = bold_best([r["d_held"] for r in rows], f3, False)
    body = []
    for title, r, hc, p in zip(SHORT, rows, held, primary, strict=True):
        require(abs(p["amplitude_error"] + p["off_axis_error"] - r["d"]) < 1e-9, "D split")
        body.append(
            f"{title} & {f3(r['d'])} & {f3(p['amplitude_error'])} & {f3(p['off_axis_error'])}"
            f" & {f3(r['d_agg'])} & {f3(r['v_scene'])} & {f3(r['align'])}"
            f" & {f3(min(r['scalars']))}--{f3(max(r['scalars']))} & {hc}\\\\"
        )
    header = (
        " & & \\multicolumn{2}{c}{Split of $D$} & \\multicolumn{2}{c}{Scene split}"
        " & & &\\\\\n\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\n"
        "Configuration & $D$ & along & off-pattern & $D_{\\mathrm{agg}}$ & $V_{\\mathrm{scene}}$"
        " & $\\beta/\\sqrt{Q}$ & fitted scalar & $D_{\\mathrm{held}}$\\\\"
    )
    caption = (
        "Parts of the error and contrast magnitude in the 31 features. Along and off-pattern:"
        " the prespecified exact split of $D$ into the error of the amplitude along the reference"
        " pattern, $(s_1-1)(s_2-1)$ with repeat-specific slopes $s_k$, and the cross-repeat"
        " product of the residuals orthogonal to that pattern, relative to $H$."
        " $D=D_{\\mathrm{agg}}+V_{\\mathrm{scene}}$; $\\beta/\\sqrt{Q}$ is the alignment ratio."
        " $D_{\\mathrm{held}}$: error after multiplying every centered"
        " generated contrast by a nonnegative scalar fitted on the other 13 scenes; the fitted"
        " range covers the 14 folds. Rescaling acts on feature vectors only."
    )
    return table(
        "tab:calibration",
        caption,
        "@{}lrrrrrrcr@{}",
        header,
        body,
        "review_v1",
        "primary",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def table_coverage(rows, hand, square, clip, csd, spectrum) -> str:
    shares = ", ".join(f"{pct(v)}\\%" for v in spectrum[:2]) + f" and {pct(spectrum[2])}\\%"
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
        f" along each singular component of the centered reference means ({shares} of their"
        " spread). Omitting a painter recenters the other three and recomputes"
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
    square = [float(row["square_distortion"]) for row in by_model(data["models"])]
    deletions = [r["distortion"]["leave_one_scene_means"] for r in data["primary"]["models"]]
    body = []
    for i, name in enumerate(SHORT):
        c = content[TITLES[i]]
        body.append(
            f"{name} & {f3(orig[i]['d'])} & {f3(min(deletions[i]))}--{f3(max(deletions[i]))}"
            f" & {f3(square[i])} & {f3(c['pooled_d'])} & {f3(c['conditional_d'])}"
            f" & {f3(weighting['equal_family'][i]['d'])}"
            f" & {f3(weighting['development_covariance'][i]['d'])}"
            f" & {f3(crop[i]['d'])} & {f3(refit[i]['d'])}\\\\"
        )
    header = (
        " & & & & \\multicolumn{2}{c}{11 scenes} & \\multicolumn{2}{c}{Weighting}"
        " & \\multicolumn{2}{c}{Source correction}\\\\\n"
        "\\cmidrule(lr){5-6}\\cmidrule(lr){7-8}\\cmidrule(l){9-10}\n"
        "Configuration & Primary & deletions & square & pooled & class & equal & covar."
        " & cropped & refit\\\\"
    )
    caption = (
        "Error $D$ (31 features) under alternative scene sets, windows, targets, weightings and"
        " source corrections. Deletions: range over the 14 single-scene deletions. Square:"
        " central-square measurement windows. Class target: title-derived water, built and land"
        " reference means for the 11 matching scenes (pooled: the same 11 scenes against the"
        " pooled target). Equal: each feature family has equal weight; covar.: shrunk inverse"
        " covariance of the development panel. Cropped: AI-audited painting regions with the"
        " original scaling; refit: also refitting the development scaling."
    )
    return table(
        "tab:sensitivity",
        caption,
        "@{}lrcrrrrrrr@{}",
        header,
        body,
        "review_v1",
        "quality",
        "models",
        "primary",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


def h_scale(diag) -> float:
    """Ratio of the bias-corrected to the estimated reference spread H."""
    return 1 - diag["h_correction"]["bias"] / diag["h_correction"]["H"]


def table_robustness(diag, agree) -> str:
    bias = pct(diag["h_correction"]["bias"] / diag["h_correction"]["H"])
    k = h_scale(diag)
    body = []
    for title, d, r in zip(SHORT, diag["hand31"], agree, strict=True):
        a = d["families"]["all31"]
        require(abs(d["beta_with_corrected_h"] - r["beta"] / k) < 1e-6, "corrected beta")
        body.append(
            f"{title} & {f2(d['repeat_noise_over_h'])} & {f3(d['beta_with_corrected_h'])}"
            f" & {f3(1 + (r['d'] - 1) / k)} & {f3(a['centroid_gain'])}"
            f" & {f3(a['centroid_gain_shared'])} & {f3(a['centroid_gain_between'])}\\\\"
        )
    header = (
        " & Repeat noise & \\multicolumn{2}{c}{Corrected $H$} & \\multicolumn{3}{c}{Centroid"
        " proximity gain}\\\\\n\\cmidrule(lr){3-4}\\cmidrule(l){5-7}\n"
        "Configuration & $/H$ & $\\beta$ & $D$ & total & shared & between-name\\\\"
    )
    caption = (
        "Further diagnostics in the 31 features. Repeat noise: half the squared difference between"
        " the two repeats' centered contrasts, relative to $H$. Corrected $H$: $\\beta$ and $D$"
        f" after removing the finite-sample bias of $H$ ({bias}\\%); $\\beta$, $Q$ and $D-1$ all"
        " scale by the same factor, so no ordering changes. Centroid proximity gain: mean"
        " reduction in squared distance from the generated mean to each painter's reference"
        " mean, from the generic to the named clause, split exactly into shared and"
        " between-name parts (Appendix~\\ref{app:estimators})."
    )
    return table("tab:robustness", caption, "@{}lrrrrrr@{}", header, body, "diagnostics", "models")


def table_sdturbo(cross, sd) -> str:
    labels = {
        "all31": "All 31",
        "color": "Color (11)",
        "spatial": "Spatial (8)",
        "texture": "Texture (12)",
    }
    body = []
    for fam, label in labels.items():
        c = cross[fam]
        body.append(
            f"{label} & {pct(c['share'])} & {span(c['share_range'], pct)} & {pct(c['within'])}"
            f" & {pct(sd[fam]['faithful'])} & {pct(sd[fam]['exact'])}\\\\"
        )
    header = "Features & shared (\\%) & block deletions & within scene & faithful & exact diff.\\\\"
    caption = (
        "Shared fraction (\\%) in the SD-Turbo collection by feature family: pooled over scenes,"
        " its range over the 25 single-block deletions, computed within scenes, and the faithful"
        " and exact-differences benchmarks."
    )
    return table("tab:sdturbo", caption, "@{}lrcrrr@{}", header, body, "cross", "diagnostics2")


LEARNED_SETTINGS = [
    ("original", "primary"),
    ("audited_region", "primary"),
    ("original", "development"),
    ("audited_region", "development"),
]


def table_learned_settings(data, diag3) -> str:
    cols = {
        rep: [[r["common_gain"] for r in learned(data, rep, v, t)] for v, t in LEARNED_SETTINGS]
        for rep in ("clip", "csd")
    }
    body = []
    for i, name in enumerate(SHORT):
        cells = []
        for rep in ("clip", "csd"):
            cells += [pct(col[i]) for col in cols[rep]]
            cells.append(pct(diag3["learned"][rep][i]["normalized_prototype_share"]))
        body.append(f"{name} & " + " & ".join(cells) + "\\\\")
    header = (
        " & \\multicolumn{5}{c}{CLIP} & \\multicolumn{5}{c}{CSD}\\\\\n"
        "\\cmidrule(lr){2-6}\\cmidrule(l){7-11}\n"
        "Configuration & prim. & crop & dev. & both & unit & prim. & crop & dev. & both"
        " & unit\\\\"
    )
    caption = (
        "Share (\\%) of the proximity gain supplied by the shared term under alternative"
        " reference settings. Prim.: full reproductions of the primary reference collection"
        " (Table~\\ref{tab:learned}). Crop: reference reproductions replaced by their audited"
        " painting regions. Dev.: the development panel as the reference target. Both: audited"
        " regions of the development panel. Unit: primary prototypes normalized to unit length,"
        " as in recognition."
    )
    return table(
        "tab:learned-settings",
        caption,
        "@{}lrrrrrrrrrr@{}",
        header,
        body,
        "learned",
        "diagnostics3",
        size="\\small\\setlength{\\tabcolsep}{3.5pt}",
    )


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
        5.4, 1.2, "$t$: to reference centroid $\\bar\\mu$", fontsize=7.5, color=MUTED, rotation=14
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


def table_embedding_calibration(diag5) -> str:
    body = []
    names = (("hand31", "31 features"), ("clip", "CLIP"), ("csd", "CSD"))
    for rep, label in names:
        if body:
            body.append("\\midrule")
        body.append(f"\\multicolumn{{8}}{{@{{}}l}}{{\\textit{{{label}}}}}\\\\")
        for name, r in zip(SHORT, diag5["agreement"][rep], strict=True):
            rho = "---" if r["rho_at_one"] is None else f2(r["rho_at_one"])
            body.append(
                f"{name} & {interval(r['beta_student'])} & {f3(r['d'])}"
                f" & {f3(r['amplitude_error'])} & {f3(r['off_axis_error'])}"
                f" & {pct(r['off_axis_error'] / r['d'])} & {f2(r['repeat_noise'])} & {rho}\\\\"
            )
    header = (
        " & $\\beta$ & & \\multicolumn{3}{c}{Split of $D$} & Repeat &\\\\\n"
        "\\cmidrule(lr){4-6}\n"
        "Configuration & scenes & $D$ & along & off-pattern & off (\\%) & noise $/H$"
        " & $\\rho$ at $D=1$\\\\"
    )
    caption = (
        "Error parts and repeat dependence in each representation. $\\beta$: unadjusted"
        " paired-scene Student 95\\% intervals. Split of $D$: the prespecified parts along and"
        " off the reference pattern (Table~\\ref{tab:calibration}) and the off-pattern share."
        " Repeat noise: half the squared difference between the repeats' centered contrasts,"
        " relative to $H$. $\\rho$ at $D=1$: common repeat correlation at which an error above 1"
        " would fall to 1 if the repeats shared that fraction of their noise"
        " (Appendix~\\ref{app:provenance}); errors below 1 would only fall further."
    )
    return table(
        "tab:embedding-calibration",
        caption,
        "@{}lcrrrrrr@{}",
        header,
        body,
        "diagnostics5",
        size="\\small\\setlength{\\tabcolsep}{4pt}",
    )


def table_diversity(primary) -> str:
    body = []
    for name, m in zip(SHORT, primary, strict=True):
        arts = m["artists"]
        require([a["artist"] for a in arts] == list(ARTISTS), "painter order")
        named = sum(a["energy"] for a in arts) / 4
        generic = sum(a["generic_energy"] for a in arts) / 4
        closer = sum(a["energy"] < a["generic_energy"] for a in arts)
        body.append(
            f"{name} & "
            + " & ".join(f2(a["trace_ratio"]) for a in arts)
            + f" & {f2(named)} & {f2(generic)} & {closer}\\\\"
        )
    header = (
        " & \\multicolumn{4}{c}{Trace ratio} & \\multicolumn{3}{c}{Energy distance}\\\\\n"
        "\\cmidrule(lr){2-5}\\cmidrule(l){6-8}\n"
        "Configuration & Mon. & Sis. & Pis. & C\\'ez. & named & generic & named closer\\\\"
    )
    caption = (
        "Prespecified distribution diagnostics in the 31 features. Trace ratio: total variance of"
        " the 28 images named for a painter (14 scenes, two repeats) relative to that of the"
        " painter's reference works. Energy distance: between those images and the painter's"
        " reference works, averaged over painters, for the named and for the generic images;"
        " named closer: number of painters (of four) for which the named images are closer."
    )
    return table("tab:diversity", caption, "@{}lrrrrrrr@{}", header, body, "primary")


def figure_projection(diag5) -> bytes:
    """Reference differences and generated centered named means on the first two
    principal axes of the 31-feature reference differences (point values)."""
    plt = _matplotlib()
    import numpy as np

    proj = diag5["projection"]
    ref = np.array(proj["reference"])
    letters = ["M", "S", "P", "C"]
    fig, axes = plt.subplots(2, 3, figsize=(6.3, 4.1), sharex=True, sharey=True)
    allpts = np.vstack([ref] + [np.array(m) for m in proj["models"]])
    lim = 1.12 * float(np.abs(allpts).max())
    for ax, name, gen in zip(axes.flat, SHORT, proj["models"], strict=True):
        gen = np.array(gen)
        for a in range(4):
            ax.plot([ref[a, 0], gen[a, 0]], [ref[a, 1], gen[a, 1]], color="#c9c8c3", lw=0.8)
        ax.plot(ref[:, 0], ref[:, 1], "s", color=INK, ms=4.5, label="reference $r_a$")
        ax.plot(gen[:, 0], gen[:, 1], "o", color=BLUE, ms=4.5, label="generated")
        for a in range(4):
            ax.text(
                ref[a, 0] - 0.05 * lim,
                ref[a, 1] + 0.05 * lim,
                letters[a],
                fontsize=6.5,
                color=INK,
                ha="right",
            )
            ax.text(
                gen[a, 0] + 0.05 * lim,
                gen[a, 1] - 0.12 * lim,
                letters[a],
                fontsize=6.5,
                color=BLUE,
                ha="left",
            )
        ax.axhline(0, color="#e2e1dc", lw=0.6, zorder=0)
        ax.axvline(0, color="#e2e1dc", lw=0.6, zorder=0)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_title(name, fontsize=8, color=INK)
        ax.tick_params(labelsize=6.5, length=2)
    axes[0, 0].legend(fontsize=6.5, frameon=False, loc="lower right")
    for ax in axes[1]:
        ax.set_xlabel("reference axis 1", fontsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel("reference axis 2", fontsize=7)
    fig.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.95, wspace=0.12, hspace=0.25)
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
            vmin=None if norm else min(0.0, float(values.min())),
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
        ax.set_xlim(0.38, 1.03)
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
    diag3 = diagnostics3(data)
    genuine = diag3["genuine_controls_distinct"]
    emb = diag3["learned"]
    clip_above = sum(r["d"] > 1 for r in emb["clip"])
    require(clip_above == 5 and all(r["d"] < 1 for r in emb["csd"]), "embedding D pattern changed")
    csd_below = [r["d_scene"][1] < 1 for r in emb["csd"]]
    require(csd_below == [True, True, True, False, False, True], "CSD D intervals changed")
    require(emb["clip"][gpt1]["d_scene"][1] < 1, "CLIP GPT Image 1 D interval changed")
    worst_config_min = min(r["d"] for rep in ("clip", "csd") for r in emb[rep])
    require(
        worst_config_min > max(genuine[rep][k]["mean"] for rep in genuine for k in genuine[rep]),
        "every configuration should exceed the genuine controls",
    )
    require(
        min(r["d"] for r in agree) > max(genuine["hand31"][k]["mean"] for k in genuine["hand31"]),
        "31-feature configurations should exceed the genuine controls",
    )
    norm_diff = max(
        abs(r["normalized_prototype_share"] - p["observed"])
        for rep in ("clip", "csd")
        for r, p in zip(emb[rep], proto[rep], strict=True)
    )
    fc = diag3["family_contrasts"]
    pw = pairwise_intervals(data)
    boot_resolved = sum(not (r["boot"][0] <= 0 <= r["boot"][1]) for r in pw.values())
    nominal_resolved = sum(not (r["nominal"][0] <= 0 <= r["nominal"][1]) for r in pw.values())
    six = six_way_d_intervals(data)
    require(six[gpt1][0] < 1 and all(six[i][0] > 1 for i in worse[1:]), "six-way pattern changed")
    crop_comps = sc["regions_original_scaler"]["comparisons"]
    crop_resolved = sorted(
        k
        for k, c in crop_comps.items()
        if c["available"] and not (c["simultaneous_ci"][0] <= 0 <= c["simultaneous_ci"][1])
    )
    require(
        crop_resolved == [("GPT Image 2.5 Flare", "FLUX.2 Max")], f"cropped pairs {crop_resolved}"
    )
    timing = data["timing"]
    gaps = sorted(abs(p["gap_minutes"]) for p in timing["pairs"])
    require(len(gaps) == 504, "timing pairs")
    drift_gain = [m["predictive_gain_fraction"] for m in timing["models"]]
    require(all(g < 0 for g in drift_gain), "linear drift should not predict repeat differences")
    k = h_scale(diag)
    exact_corr = [
        a["N_over_H"] / (a["N_over_H"] + k)
        for a in (d["families"]["all31"] for d in diag["hand31"])
    ]
    d_corr = [1 + (r["d"] - 1) / k for r in agree]
    genuine_above = [genuine["hand31"][key]["above_one"] for key in genuine["hand31"]]
    emb_upper = max(genuine[r][key]["interval95"][1] for r in ("clip", "csd") for key in genuine[r])
    require(
        all(genuine[r][key]["above_one"] == 0 for r in ("clip", "csd") for key in genuine[r]),
        "embedding genuine controls should never exceed 1",
    )
    fam1 = [d["families"]["all31"] for d in diag["hand31"]]
    gpt_idx = [i for i, t in enumerate(TITLES) if t.startswith("GPT")]
    other_idx = [nb2, flux]
    proto_rows = {rep: [r["prototype"] for r in diag2["learned"][rep]] for rep in ("clip", "csd")}
    proto_obs = [r["point"]["observed"] for rep in proto_rows for r in proto_rows[rep]]
    proto_low = [r["scene_bootstrap"]["observed"][0] for rep in proto_rows for r in proto_rows[rep]]
    require(sorted(proto_low)[0] < 0.5 < sorted(proto_low)[1], "one proximity interval below 50%")
    cez_csd = [r["per_painter"][3]["shared_fraction"] for r in proto_rows["csd"]]
    emb_beta = [r["beta"] for rep in ("clip", "csd") for r in emb[rep]]
    require(
        min(r["beta_scene"][0] for rep in ("clip", "csd") for r in emb[rep]) > 0,
        "embedding amplitudes should have scene intervals above zero",
    )
    calib = agree
    fm = diag2["family_means"]
    import numpy as np

    def corr(a, b):
        return float(np.corrcoef(a, b)[0, 1])

    def ranks(v):
        return list((-np.asarray(v)).argsort().argsort() + 1)

    decomp = {}
    for rep, rows in (("clip", clip), ("csd", csd)):
        g = np.array([r["gain"] for r in rows])
        sh = g * np.array([r["common_gain"] for r in rows])
        decomp[rep] = dict(gain=g, shared=sh, specific=g - sh)
    dc, ds = decomp["clip"], decomp["csd"]
    require(ranks(dc["gain"]) == ranks(dc["shared"]), "CLIP gain should rank as its shared term")
    require(ranks(dc["gain"])[nb2] == 1 and ranks(dc["specific"])[nb2] == 5, "NB2 CLIP ranks")
    require(ranks(ds["gain"])[gpt2] == 6 and ranks(ds["specific"])[gpt2] == 1, "GPT2 CSD ranks")
    cov_models = data["covariance"]["models"]

    def rho_at(level, row):
        k = next(g for g in row["grid"] if g["rho"] == 0.5)["implied_bias"]
        a = (row["d"] - level) / k
        return a / (1 + a)

    rho_one = [rho_at(1.0, r) if r["d"] > 1 else None for r in cov_models]
    rho_zero = [rho_at(0.0, r) for r in cov_models]
    require(
        min(rho_zero) == rho_zero[nb2] and sorted(rho_zero)[1] == rho_zero[flux],
        "NB2 and FLUX should reach zero first",
    )
    fams1 = {k: [d["families"][k] for d in diag["hand31"]] for k in ("color", "spatial", "texture")}
    fam_exact = {
        k: sum(r["N_over_H"] / (r["N_over_H"] + 1) for r in v) / 6 for k, v in fams1.items()
    }
    fam_faith = {k: sum(r["faithful_shared_fraction"] for r in v) / 6 for k, v in fams1.items()}
    fam_obs = {k: sum(r["shared_fraction"] for r in v) / 6 for k, v in fams1.items()}
    below_exact = {k: fam_obs[k] - fam_exact[k] for k in fam_obs}
    require(all(v < 0 for v in below_exact.values()), "families should be below exact benchmarks")
    tex1 = fams1["texture"][gpt1]
    d4 = diagnostics4(data)
    content_shift = max(
        abs(r["class_d"] - r["pooled_d"]) for rep in ("clip", "csd") for r in d4["learned"][rep]
    )
    for rep, best in (("clip", gpt1), ("csd", flux)):
        vals = [r["class_d"] for r in d4["learned"][rep]]
        require(vals.index(min(vals)) == best, f"content-matched best changed: {rep}")
    csd_lows = [r["d_scene"][0] for r in emb["csd"]]
    require(max(csd_lows) < 1, "no CSD interval should lie above 1")
    proto_csd_diff = [p["point"]["observed"] - p["point"]["faithful"] for p in proto_rows["csd"]]
    require(all(v > 0 for v in proto_csd_diff), "CSD shares should exceed faithful in all six")
    flux_pairs = diag2["hand31"][flux]["pairs"]
    d5 = diagnostics5(data)
    ag5 = d5["agreement"]
    off_share = [r["off_axis_error"] / r["d"] for r in ag5["hand31"]]
    for rep in ("hand31", "clip", "csd"):
        al = [r["alignment"] for r in ag5[rep]]
        ho = [r["held_out_d"] for r in ag5[rep]]
        require(al.index(max(al)) == gpt2 and ho.index(min(ho)) == gpt2, f"direction best {rep}")
    csd_student = [r["d_student"] for r in ag5["csd"]]
    require(
        [hi < 1 for _, hi in csd_student] == [True, True, True, False, False, True],
        "CSD Student intervals changed",
    )
    require(all(lo < 1 for lo, _ in csd_student), "no CSD Student interval above 1")
    clip_student = [r["d_student"] for r in ag5["clip"]]
    above = [i for i, (lo, _) in enumerate(clip_student) if lo > 1]
    require(above == [idx["GPT Image 2.5 Sunburst"]], "only Sunburst above 1 in CLIP")
    clip_rho = [r["rho_at_one"] for r in ag5["clip"] if r["rho_at_one"] is not None]
    sp = d5["spearman"]
    prox5 = d5["proximity"]
    fs = f"{MODELS[2]}|{MODELS[3]}"
    distinct_min = min(v for rep in d5["distinct"] for v in d5["distinct"][rep].values())
    require(distinct_min == d5["distinct"]["clip"][fs], "Flare-Sunburst CLIP is the minimum")
    content_shift11 = max(
        abs(r["class_d"] - r["pooled_d"]) for rep in ("clip", "csd") for r in d4["learned"][rep]
    )
    for rep in ("clip", "csd"):
        pooled = [r["pooled_d"] for r in d4["learned"][rep]]
        cls = [r["class_d"] for r in d4["learned"][rep]]
        require(ranks(pooled) == ranks(cls), f"content-matched order changed: {rep}")
    prim = data["primary"]["models"]
    trace = [a["trace_ratio"] for m in prim for a in m["artists"]]
    closer = sum(a["energy"] < a["generic_energy"] for m in prim for a in m["artists"])
    sun_ms = diag2["hand31"][idx["GPT Image 2.5 Sunburst"]]["pairs"][0]
    require(sun_ms["beta_scene"][1] < 0 < sun_ms["beta_reference"][1], "Sunburst MS pattern")
    sa_align = {"hand31": [r["beta"] / math.sqrt(r["q"] - r["v_scene"]) for r in agree]}
    for rep in ("clip", "csd"):
        models = data["learned"][rep]["original"]["targets"]["primary"]["models"]
        sa_align[rep] = [
            t["centered"]["beta"] / math.sqrt(t["centered"]["q"] - t["centered"]["scene_variation"])
            for t in models
        ]
    require(all(v.index(max(v)) == gpt2 for v in sa_align.values()), "scene-averaged alignment")
    clip_dagg = [
        t["centered"]["aggregate_d"]
        for t in data["learned"]["clip"]["original"]["targets"]["primary"]["models"]
    ]
    require(max(clip_dagg) < 1, "CLIP scene-averaged errors below 1")
    return {
        "H": f3(h),
        "sa_align_gpt2": ", ".join(f3(sa_align[r][gpt2]) for r in ("hand31", "clip", "csd")),
        "clip_dagg": span(clip_dagg, f3),
        "off_share_worse": span(
            [
                off_share[i]
                for i in (gpt1, idx["GPT Image 2.5 Flare"], idx["GPT Image 2.5 Sunburst"])
            ],
            pct,
        ),
        "off_share_nb2": pct(off_share[nb2]),
        "off_share_flux": pct(off_share[flux]),
        "align_best_31": pct(d5["stability"]["hand31"]["alignment"][MODELS[gpt2]]),
        "align_best_clip": pct(d5["stability"]["clip"]["alignment"][MODELS[gpt2]]),
        "align_best_csd": pct(d5["stability"]["csd"]["alignment"][MODELS[gpt2]]),
        "align_gpt2": ", ".join(
            f3(ag5[rep][gpt2]["alignment"]) for rep in ("hand31", "clip", "csd")
        ),
        "held_gpt2_emb": ", ".join(f3(ag5[rep][gpt2]["held_out_d"]) for rep in ("clip", "csd")),
        "sp_recog_clip": f2(sp["alignment_recognition_clip"]),
        "sp_recog_csd": f2(sp["alignment_recognition_csd"]),
        "sp_align_reps": span(
            [sp[k] for k in sp if k.startswith("alignment_") and "recognition" not in k], f2
        ),
        "sp_d_reps": " to ".join(
            f2(v).replace("-", "$-$")
            for v in (
                min(sp[k] for k in sp if k.startswith("d_")),
                max(sp[k] for k in sp if k.startswith("d_")),
            )
        ),
        "prox_clip_interval": rng(prox5["clip"]["scene_interval"]["corr_shared"], f2),
        "prox_csd_interval": rng(prox5["csd"]["scene_interval"]["corr_shared"], f2),
        "var_ratio_csd": f"{prox5['csd']['point']['variance_ratio']:.1f}",
        "var_ratio_clip_interval": rng(
            prox5["clip"]["scene_interval"]["variance_ratio"], lambda v: f"{v:.1f}"
        ),
        "var_ratio_csd_interval": rng(
            prox5["csd"]["scene_interval"]["variance_ratio"], lambda v: f"{v:.1f}"
        ),
        "clip_rho_range": span(clip_rho, f2),
        "clip_sunburst_rho": f2(ag5["clip"][idx["GPT Image 2.5 Sunburst"]]["rho_at_one"]),
        "clip_gpt1_student": interval(clip_student[gpt1]),
        "clip_sunburst_student": interval(clip_student[idx["GPT Image 2.5 Sunburst"]]),
        "distinct_fs": ", ".join(pct(d5["distinct"][rep][fs]) for rep in ("hand31", "clip", "csd")),
        "distinct_min": pct(distinct_min),
        "content_shift11": f3(content_shift11),
        "trace_range": span(trace, f2),
        "ref_two_axes": pct(sum(data["review_v1"]["reference_spectrum"][:2])),
        "named_closer": str(closer),
        "sunburst_ms": f3(sun_ms["beta"]).replace("-", "$-$"),
        "sunburst_ms_scene": interval(sun_ms["beta_scene"]).replace("-", "$-$"),
        "corr_clip_shared": f2(corr(dc["gain"], dc["shared"])),
        "corr_csd_shared": f2(corr(ds["gain"], ds["shared"])),
        "corr_csd_specific": f2(corr(ds["gain"], ds["specific"])).replace("-", "$-$"),
        "clip_var_ratio": f"{np.var(dc['shared']) / np.var(dc['specific']):.0f}",
        "rho_gpt1": f2(rho_one[gpt1]),
        "rho_flare": f2(rho_one[idx["GPT Image 2.5 Flare"]]),
        "rho_sunburst": f2(rho_one[idx["GPT Image 2.5 Sunburst"]]),
        "rho_zero": span([rho_zero[nb2], rho_zero[flux]], f2),
        "fam_exact_color": pct(fam_exact["color"]),
        "fam_exact_spatial": pct(fam_exact["spatial"]),
        "fam_exact_texture": pct(fam_exact["texture"]),
        "fam_faithful_texture_color": signed_pct(fam_faith["texture"] - fam_faith["color"]),
        "fam_exact_texture_color": signed_pct(fam_exact["texture"] - fam_exact["color"]),
        "fam_below_exact": span([-v for v in below_exact.values()], lambda v: f"{100 * v:.1f}"),
        "gpt1_texture_bh": f2(tex1["B_over_H"]),
        "gpt1_texture_exact": pct(tex1["N_over_H"] / (tex1["N_over_H"] + 1)),
        "content_shift": f3(content_shift),
        "clip_gpt1_class_d": f3(d4["learned"]["clip"][gpt1]["class_d"]),
        "csd_flux_class_d": f3(d4["learned"]["csd"][flux]["class_d"]),
        "content_distance": ", ".join(
            f2(x[0]["class_vs_pooled"])
            for x in (d4["hand31"], d4["learned"]["clip"], d4["learned"]["csd"])
        ),
        "flux_impressionist_beta": span([flux_pairs[j]["beta"] for j in (0, 1, 3)], f2),
        "flux_ms_d": f2(flux_pairs[0]["d"]),
        "flux_align": f3(agree[flux]["align"]),
        "csd_nb2_joint": pct(emb["csd"][nb2]["d_below_one_joint"]),
        "genuine_hand_upper": span(
            [genuine["hand31"][k]["interval95"][1] for k in genuine["hand31"]], f2
        ),
        "flux_mp_d": f2(flux_pairs[1]["d"]),
        "bh_gpt": span([fam1[i]["B_over_H"] for i in gpt_idx], f2),
        "bh_other": span([fam1[i]["B_over_H"] for i in other_idx], f2),
        "proto_share_all": span(proto_obs, pct),
        "proto_above_half": str(sum(v > 0.5 for v in proto_low)),
        "gpt2_csd_interval": rng(proto_rows["csd"][gpt2]["scene_bootstrap"]["observed"]),
        "gpt2_csd_faithful": pct(proto_rows["csd"][gpt2]["point"]["faithful"]),
        "cezanne_csd_min": pct(min(cez_csd)),
        "worse_q": span([agree[i]["q"] for i in worse], f2),
        "worse_beta": span([agree[i]["beta"] for i in worse], f3),
        "worse_ratio": span([calib[i]["align"] for i in worse], f3),
        "gpt1_d_held": f3(calib[gpt1]["d_held"]),
        "sunburst_d_held": f3(calib[idx["GPT Image 2.5 Sunburst"]]["d_held"]),
        "clip_sunburst_d_interval": interval(emb["clip"][idx["GPT Image 2.5 Sunburst"]]["d_scene"]),
        "csd_d_range": span([r["d"] for r in emb["csd"]], f3),
        "emb_beta_range": span(emb_beta, f3),
        "texture_color_interval": rng(
            fc["interval"]["texture-color"], lambda v: f"{100 * v:.1f}".replace("-", "$-$")
        ),
        "fam_spatial_interval": rng(fm["spatial"]["scene_interval"]),
        "fam_unavail_spatial": str(fm["spatial"]["unavailable_draws"]),
        "fam_unavail_texture": str(fm["texture"]["unavailable_draws"]),
        "gap_median": f"{statistics.median(gaps):.1f}",
        "gap_max": f"{gaps[-1]:.0f}",
        "drift_error_rise": span([-g for g in drift_gain], lambda v: f"{100 * v:.1f}"),
        "drift_gain": f"{signed_pct(min(drift_gain))} to {signed_pct(max(drift_gain))}",
        "exact_corrected": span(exact_corr, pct),
        "flux_d_corrected": f3(d_corr[flux]),
        "genuine_above": span([100 * v for v in genuine_above], lambda v: f"{v:.1f}"),
        "genuine_emb_upper": f2(emb_upper),
        "genuine_hand": span([genuine["hand31"][k]["mean"] for k in genuine["hand31"]], f3),
        "genuine_emb": span(
            [genuine[r][k]["mean"] for r in ("clip", "csd") for k in genuine[r]], f3
        ),
        "clip_gpt1_d_interval": interval(emb["clip"][gpt1]["d_scene"]),
        "norm_diff": f"{100 * norm_diff:.1f}",
        "texture_color": signed_pct(fc["point"]["texture-color"]),
        "texture_color_below": pct(fc["below_zero"]["texture-color"]),
        "texture_spatial_below": pct(fc["below_zero"]["texture-spatial"]),
        "family_dropped": str(fc["dropped_draws"]),
        "boot_resolved": str(boot_resolved),
        "nominal_resolved": str(nominal_resolved),
        "gpt1_six_way": interval(six[gpt1]),
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
        "tab_readouts.tex": table_readouts(clip, csd, diagnostics5(data)),
        "tab_stability.tex": table_stability(diag, diagnostics5(data)),
        "tab_families.tex": table_families(diag, diag2, cross_cohort(data)),
        "tab_learned_squared.tex": table_learned_squared(diag),
        "tab_pair_intervals.tex": table_pair_intervals(diag2),
        "tab_per_painter.tex": table_per_painter(diag2),
        "tab_family_agreement.tex": table_family_agreement(family_agreement(data)),
        "tab_decomposition_full.tex": table_decomposition_full(hand, diag),
        "tab_pairs.tex": table_pairs(pairwise_intervals(data)),
        "tab_calibration.tex": table_calibration(agree, data["primary"]["models"]),
        "tab_coverage.tex": table_coverage(
            agree,
            hand,
            square_monet_sisley(data),
            clip,
            csd,
            data["review_v1"]["reference_spectrum"],
        ),
        "tab_embedding_agreement.tex": table_embedding_agreement(
            diagnostics3(data), diagnostics4(data), diagnostics5(data)
        ),
        "tab_embedding_calibration.tex": table_embedding_calibration(diagnostics5(data)),
        "tab_diversity.tex": table_diversity(data["primary"]["models"]),
        "fig_projection.pdf": figure_projection(diagnostics5(data)),
        "tab_genuine.tex": table_genuine_controls(diagnostics3(data), real_controls(data)),
        "tab_sensitivity.tex": table_sensitivity(data, source_correction(data)),
        "tab_robustness.tex": table_robustness(diag, agree),
        "tab_direction.tex": table_direction(diag),
        "tab_sdturbo.tex": table_sdturbo(cross_cohort(data), diag2["sd_turbo"]),
        "tab_learned_settings.tex": table_learned_settings(data, diagnostics3(data)),
        "tab_transfer.tex": table_transfer(transfer(data, "clip"), transfer(data, "csd")),
        "tab_scenes.tex": table_scenes(scenes_from_requests(data["requests"])),
        "fig_schematic.pdf": figure_schematic(),
        "fig_benchmark.pdf": figure_benchmark(diag2),
        "fig_pairs.pdf": figure_pairs(diag2),
        "tab_v3_panels.tex": table_v3_panels(data["v3_determination"], data["v3_references"]),
        "tab_v3_predictions.tex": table_v3_predictions(data["v3_predictions"]),
    }


def manuscript_text() -> str:
    """Manuscript prose with comments removed and whitespace collapsed."""
    text = "\n".join(path.read_text() for path in MANUSCRIPT if path.exists())
    text = re.sub(r"(?m)^%.*$", "", text)
    return re.sub(r"\s+", " ", text)


def check_claims(values: dict[str, str], registry_path: Path) -> list[str]:
    """Every registered claim must equal its recomputed value and appear in its
    registered sentence context ("{}" marks the value)."""
    text = manuscript_text()
    registry = json.loads(registry_path.read_text())
    problems = []
    for key, entry in registry.items():
        literal, context = entry["value"], entry["context"]
        if key not in values:
            problems.append(f"unknown claim key {key}")
            continue
        if literal != values[key]:
            problems.append(f"{key}: manuscript registry {literal!r} != computed {values[key]!r}")
        elif context.count("{}") != 1 or context.replace("{}", literal) not in text:
            problems.append(f"{key}: {literal!r} not found in context {context!r}")
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
