"""Deterministic numeric-only reporting of the separately specified missingness supplement."""

from __future__ import annotations

import csv
import html
import io
import json
import shlex
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS, SHORT_LABELS
from latent_art_bench.painter_feature_generation_v2.features import FAMILY_NAMES

ALIASES = ("gpt-image-1", "gpt-image-2")
METHODS = ("by_name", "style_instruction", "style_aspects")
METHOD_LABELS = dict(zip(METHODS, ("By name", "Style instruction", "Style + aspects")))
TRANSITIONS = (("by_name", "style_instruction"), ("style_instruction", "style_aspects"))
TEMPLATES = tuple(f"{prefix}{i}" for prefix in "WBRL" for i in range(1, 5))
TABLES = (
    "distances",
    "absolute",
    "coordinates",
    "exploratory_contrasts",
    "pair_support",
    "scene_contributions",
    "secondary",
    "time_diagnostics",
    "availability",
    "template_availability",
)
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.hashsalt": "painter-prompt-supplement-v1",
}


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + "\n"


def _csv(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=sorted({key for row in rows for key in row}), lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(
        {
            key: json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
            if isinstance(value, (dict, list))
            else value
            for key, value in row.items()
        }
        for row in rows
    )
    return stream.getvalue()


def _cell(value):
    return (
        html.escape(str(value), quote=False)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(map(_cell, headers)) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        + ["| " + " | ".join(map(_cell, row)) + " |" for row in rows]
    )


def _label(value):
    return SHORT_LABELS.get(value, METHOD_LABELS.get(value, value))


def _number(value):
    return "Unavailable" if value is None else f"{value:.5g}"


def _inventory(rows, keys, expected, name):
    actual = [tuple(row[key] for key in keys) for row in rows]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError(f"report requires the full {name} inventory, including unavailable rows")


def _validate(result):
    _json(result)  # Fail before writing on nonfinite/non-JSON data.
    if (
        result["registered_primary_status"] != "unavailable_incomplete_grid"
        or result["inference"]["confidence_intervals"] is not False
    ):
        raise ValueError("supplement must retain the unavailable registered primary and no CIs")
    if (
        tuple(result["aliases"]) != ALIASES
        or tuple(result["methods"]) != METHODS
        or tuple(result["painters"]) != PAINTER_IDS
        or result["families"] != {key: list(value) for key, value in FAMILY_NAMES.items()}
        or type(result["repetitions"]) is not int
        or result["repetitions"] not in (1, 2, 4)
    ):
        raise ValueError("supplement report population or feature inventory changed")
    families, painters = tuple(FAMILY_NAMES), tuple(PAINTER_IDS)
    conditions = (*painters, "artist_free")
    endpoints = {
        (a, p, f, before, after)
        for a in ALIASES
        for p in painters
        for f in families
        for before, after in TRANSITIONS
    }
    _inventory(
        result["exploratory_contrasts"],
        ("alias", "painter_id", "family", "before", "after"),
        endpoints,
        "48-endpoint",
    )
    _inventory(
        result["absolute"],
        ("alias", "method_id", "painter_id", "family"),
        {(a, m, p, f) for a in ALIASES for m in METHODS for p in painters for f in families},
        "72 absolute-distance",
    )
    _inventory(
        result["distances"],
        ("alias", "method_id", "condition", "painter_id", "family"),
        {
            (a, m, c, p, f)
            for a in ALIASES
            for m in METHODS
            for c in conditions
            for p in painters
            for f in families
        },
        "360 distance-matrix",
    )
    _inventory(
        result["coordinates"],
        ("alias", "method_id", "painter_id", "family", "coordinate"),
        {
            (a, m, p, f, name)
            for a in ALIASES
            for m in METHODS
            for p in painters
            for f, names in FAMILY_NAMES.items()
            for name in names
        },
        "744 coordinate",
    )
    supports = {
        (a, p, before, after, block, template)
        for a in ALIASES
        for p in painters
        for before, after in TRANSITIONS
        for block in range(result["repetitions"])
        for template in TEMPLATES
    }
    _inventory(
        result["pair_support"],
        ("alias", "painter_id", "before", "after", "block", "template_id"),
        supports,
        "paired-support",
    )
    _inventory(
        result["scene_contributions"],
        ("alias", "painter_id", "family", "before", "after", "block", "template_id"),
        {
            (*endpoint, block, template)
            for endpoint in endpoints
            for block in range(result["repetitions"])
            for template in TEMPLATES
        },
        "scene-contribution",
    )
    _inventory(
        result["time_diagnostics"],
        ("alias", "painter_id", "family", "before", "after"),
        endpoints,
        "order-diagnostic",
    )
    secondary = {(*endpoint, "control_adjusted_transition") for endpoint in endpoints}
    secondary |= {
        (a, p, f, "by_name", "style_aspects", "overall_transition")
        for a in ALIASES
        for p in painters
        for f in families
    }
    _inventory(
        result["secondary"],
        ("alias", "painter_id", "family", "before", "after", "endpoint"),
        secondary,
        "72 secondary-comparison",
    )
    _inventory(
        result["availability"],
        ("alias", "method_id", "condition"),
        {(a, m, c) for a in ALIASES for m in METHODS for c in conditions},
        "availability",
    )
    _inventory(
        result["template_availability"],
        ("alias", "method_id", "condition", "template_id"),
        {(a, m, c, t) for a in ALIASES for m in METHODS for c in conditions for t in TEMPLATES},
        "template-availability",
    )
    for row in result["exploratory_contrasts"]:
        if row["status"] == "unavailable_missing_template":
            if (
                row["raw_p"] is not None
                or row["holm_p"] is not None
                or row["reject_holm"] is not False
                or row["holm_input"] != 1.0
            ):
                raise ValueError(
                    "unavailable endpoint must disclose missing p-values and placeholder"
                )
        elif row["status"] != "conditional_joint_randomization":
            raise ValueError("unknown exploratory endpoint status")
        elif (
            any(row[key] is None for key in ("before_distance", "after_distance", "estimate"))
            or not 0 <= row["raw_p"] <= row["holm_p"] <= 1
        ):
            raise ValueError("invalid available exploratory comparison")
    for name in TABLES:
        if not isinstance(result[name], list) or any(
            not isinstance(row, dict) for row in result[name]
        ):
            raise ValueError(f"report requires complete tabular data: {name}")


def _save(fig, output, name):
    try:
        for extension, metadata in (
            ("png", {"Software": "LatentArtBench"}),
            ("svg", {"Date": None, "Creator": "LatentArtBench"}),
        ):
            fig.savefig(
                output / "plots" / f"{name}.{extension}",
                format=extension,
                dpi=140,
                metadata=metadata,
            )
    finally:
        plt.close(fig)


def _plots(result, output):
    painters, families = result["painters"], list(result["families"])
    targets = {
        (r["alias"], r["method_id"], r["painter_id"], r["family"]): r for r in result["absolute"]
    }
    maxima = {
        family: max(
            (
                r["finite_distance"]
                for r in result["absolute"]
                if r["family"] == family and r["finite_distance"] is not None
            ),
            default=0,
        )
        for family in families
    }
    fig, axes = plt.subplots(
        2, 3, figsize=(15, 8), squeeze=False, sharex="col", layout="constrained"
    )
    for i, alias in enumerate(ALIASES):
        for j, family in enumerate(families):
            ax = axes[i, j]
            for method_index, method in enumerate(METHODS):
                for painter_index, painter in enumerate(painters):
                    row = targets[alias, method, painter, family]
                    y = painter_index + (method_index - 1) * 0.22
                    if row["finite_distance"] is None:
                        ax.text(
                            0.02,
                            y,
                            "Unavailable",
                            transform=ax.get_yaxis_transform(),
                            color=COLORS[method_index],
                            fontsize=7,
                            va="center",
                        )
                    else:
                        ax.scatter(row["finite_distance"], y, color=COLORS[method_index], s=34)
                ax.scatter([], [], color=COLORS[method_index], label=METHOD_LABELS[method])
            ax.set(title=f"{alias} · {family}", xlabel="All-available weighted finite distance")
            ax.set_xlim(0, max(maxima[family] * 1.08, 0.01))
            ax.set_yticks(range(4), [_label(p) for p in painters])
            ax.set_ylim(3.5, -0.5)
            ax.grid(axis="x", alpha=0.2)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
    fig.suptitle(
        "Exploratory distances conditioned on successful measurement\n"
        "All available images; each scene has total weight 1/16. No confidence intervals"
    )
    _save(fig, output, "target_distances")

    fig, axes = plt.subplots(
        2, 3, figsize=(16, 10), squeeze=False, sharex="col", layout="constrained"
    )
    for i, alias in enumerate(ALIASES):
        for j, family in enumerate(families):
            ax = axes[i, j]
            rows = [
                r
                for r in result["exploratory_contrasts"]
                if r["alias"] == alias and r["family"] == family
            ]
            for k, row in enumerate(rows):
                if row["status"] == "unavailable_missing_template":
                    ax.text(
                        0.02,
                        k,
                        "Unavailable: missing scene support",
                        transform=ax.get_yaxis_transform(),
                        va="center",
                        fontsize=8,
                    )
                else:
                    ax.scatter(
                        row["estimate"],
                        k,
                        color=COLORS[painters.index(row["painter_id"])],
                        s=37,
                        zorder=3,
                    )
            labels = [
                f"{_label(r['painter_id'])}: "
                + ("name → style" if r["before"] == "by_name" else "style → aspects")
                for r in rows
            ]
            ax.set_yticks(range(len(rows)), labels)
            ax.set_ylim(len(rows) - 0.5, -0.5)
            ax.axvline(0, color="#444444", linewidth=0.8)
            ax.set(title=f"{alias} · {family}", xlabel="Paired-support distance difference")
            formatter = ScalarFormatter(useMathText=True, useOffset=False)
            formatter.set_powerlimits((-3, 3))
            ax.xaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
            ax.grid(axis="x", alpha=0.2)
    fig.suptitle(
        "All 48 exploratory paired-support transitions\n"
        "Second − first method; matched successful pairs; no confidence intervals"
    )
    _save(fig, output, "paired_transitions")

    fig, axes = plt.subplots(2, 1, figsize=(15, 8), squeeze=False, layout="constrained")
    support = result["pair_support"]
    planned = 16 * result["repetitions"]
    for i, alias in enumerate(ALIASES):
        ax = axes[i, 0]
        labels = []
        for k, (painter, (before, after)) in enumerate(
            (p, transition) for p in painters for transition in TRANSITIONS
        ):
            chosen = [
                r
                for r in support
                if (r["alias"], r["painter_id"], r["before"], r["after"])
                == (alias, painter, before, after)
            ]
            included = sum(r["included"] for r in chosen)
            both = sum(r["both_measured"] for r in chosen)
            ax.barh(
                k, included, color=COLORS[0], label="Included successful pairs" if k == 0 else None
            )
            ax.barh(
                k,
                both - included,
                left=included,
                color=COLORS[1],
                label="Successful pairs; endpoint lacks a scene" if k == 0 else None,
            )
            ax.barh(
                k,
                planned - both,
                left=both,
                color="#cccccc",
                label="At least one outcome unavailable" if k == 0 else None,
            )
            ax.text(planned + 0.6, k, f"{included}/{planned}", va="center", fontsize=9)
            labels.append(
                f"{_label(painter)}: "
                + ("name → style" if before == "by_name" else "style → aspects")
            )
        ax.set_yticks(range(8), labels)
        ax.invert_yaxis()
        ax.set(xlim=(0, planned * 1.12), title=alias, xlabel="Matched scene/repetition positions")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
    fig.suptitle(
        "Availability retained for every planned paired-support comparison\n"
        "All 16 scenes must have a successful pair; excluded outcomes remain in the exports"
    )
    _save(fig, output, "pair_availability")


def _markdown(result, exports):
    exploratory = result["exploratory_contrasts"]
    available = sum(r["status"] == "conditional_joint_randomization" for r in exploratory)
    parts = [
        "# Missingness supplement: exploratory painter-feature distances",
        "**The original registered primary analysis remains unavailable because its required "
        "complete measured grid is missing.** This separate supplement was specified after "
        "the first service refusal and before new-image feature measurement. It is "
        "exploratory and was not preregistered before generation; it does not replace, repair "
        "or relabel the original primary result.",
        _table(
            ["Record", "Value"],
            [
                ["Supplement", result["analysis_id"]],
                ["Source generation", result["source_run_id"]],
                ["Original primary status", result["registered_primary_status"]],
                [
                    "Exploratory endpoints",
                    f"{available} available; {48 - available} unavailable; 48 retained",
                ],
                ["Repetitions", result["repetitions"]],
            ],
        ),
        "## Distances conditioned on successful measurement",
        "These descriptive distances use every successfully measured output in each "
        "method/condition. A scene with mₜ available images gives each image weight "
        "1/(16 mₜ), so every scene retains total weight 1/16. Every one of the 16 scenes "
        "must be represented; an unsupported endpoint is shown as unavailable. This "
        "conditions on success and does not describe missing potential outputs.",
        "For a family of scaled features, the reported V-energy is "
        "D = (2/N) Σᵢⱼ wⱼ ‖xᵢ − yⱼ‖₂ − (1/N²) Σᵢₖ ‖xᵢ − xₖ‖₂ "
        "− Σⱼₗ wⱼwₗ ‖yⱼ − yₗ‖₂, including diagonal pairs. The xᵢ are the "
        "N fixed reference works and the yⱼ are available generated outputs. "
        "Smaller values mean closer finite feature distributions; scales are consistent "
        "within each feature family and are not comparable across families.",
        "![All-available target distances](plots/target_distances.png)",
    ]
    for alias in ALIASES:
        lookup = {
            (r["method_id"], r["painter_id"], r["family"]): r["finite_distance"]
            for r in result["absolute"]
            if r["alias"] == alias
        }
        parts += [
            f"### {_cell(alias)}",
            _table(
                ["Painter", "Family", *map(_label, METHODS)],
                [
                    [_label(p), f] + [_number(lookup[m, p, f]) for m in METHODS]
                    for p in result["painters"]
                    for f in result["families"]
                ],
            ),
        ]
    parts += [
        "## Exploratory comparisons on matched successful pairs",
        "Each transition uses only scene/repetition positions where both tested methods "
        "were measured. Its own before and after distributions share weights "
        "1/(16 mₜ), with mₜ now counting successful pairs for that scene. Their distance "
        "difference is the tested statistic. These paired supports and weights can differ "
        "from the all-available distances above; subtracting entries in the first table "
        "need not reproduce the tested contrast.",
        "![Exploratory paired transitions](plots/paired_transitions.png)",
        "The randomization test addresses the **joint sharp null for availability and "
        "measured feature outcomes**, conditional on the third method's assigned position "
        "and the permitted paired swaps, with no interference between requests. A rejection "
        "does not isolate a feature change from an availability change. It also does not "
        "establish a population distance improvement. Negative observed contrasts mean "
        "the second method named in the transition has smaller distance on the reported "
        "paired support. This method ordering does not assert chronological request order.",
        "All 48 comparisons remain in the Holm family at alpha 0.05. An unavailable test "
        "has no observed raw or adjusted p-value; its internal Holm input of 1 is only an "
        "adjustment placeholder, recorded as holm_input in the CSV. No confidence intervals, "
        "equivalence claim, combined score or overall model ranking is supplied.",
        _table(
            [
                "Service",
                "Painter",
                "Family",
                "Transition",
                "Pairs",
                "Before distance",
                "After distance",
                "Difference",
                "Raw p",
                "Holm p",
                "Status",
            ],
            [
                [
                    r["alias"],
                    _label(r["painter_id"]),
                    r["family"],
                    f"{_label(r['before'])} → {_label(r['after'])}",
                    r["pairs"],
                    *[
                        _number(r[k])
                        for k in (
                            "before_distance",
                            "after_distance",
                            "estimate",
                            "raw_p",
                            "holm_p",
                        )
                    ],
                    r["status"],
                ]
                for r in exploratory
            ],
        ),
        "## Availability, measurement and limits",
        "![Paired availability](plots/pair_availability.png)",
        "Every planned pair and scene contribution is retained, including unsuccessful or "
        "excluded positions. The availability and template-availability exports retain "
        "all registered conditions. Order diagnostics are descriptive and do not prove "
        "absence of drift, carryover, treatment-dependent timing or hidden service state.",
        _table(
            ["Painter", "Fixed measured reference", "New-development scaler works"],
            [
                [_label(p), result["reference_counts"][p], result["scaler_development_counts"][p]]
                for p in result["painters"]
            ],
        ),
        "The 31 color, spatial and digital-texture features, original 512-short-side "
        "normalization, exposed 649-painting reference and frozen development-only scaler "
        "remain unchanged. The reference consists of metadata-declared outdoor-place "
        "digital surrogates, not an authority-verified or probability-sampled oeuvre. "
        "This supplement newly specifies weighted inverse empirical-CDF quantiles for "
        "both reference and generated coordinate summaries; it does not mix these with "
        "the original analysis's quantile convention. Reference works retain equal weight "
        "1/N; each quantile is the smallest value whose cumulative weight reaches the "
        "requested probability.",
        "The requested service aliases do not attest model snapshots or distinct model "
        "weights. Returned geometry, quality and profile differences can affect measured "
        "distances; scene content and digital capture also remain confounds. The numeric "
        "diagnostics retain requested/returned settings, availability, and duplicate screens. "
        "Perceptual hashes are candidate screens, not a copying or originality verdict.",
        "Synthetic qualification checks the declared numerical construction and joint null; "
        "it cannot establish the actual service's no-interference assumptions or guarantee "
        "power for image outcomes. Reviews are maintainer-run LLM subagents and are not "
        "institutionally independent.",
        "## Full-precision exports and provenance",
        "Displayed numbers are rounded only for reading. CSV exports preserve full "
        "floating-point precision, all endpoint statuses and supports. The diagnostic JSON "
        "retains qualification, source hashes, inference assumptions, service and copy "
        "diagnostics, and reference/scaler metadata. This renderer reads numeric results "
        "only; it neither generates images nor extracts their features.",
        "\n".join(f"- [{name.replace('_', ' ')}]({name}.csv)" for name in exports),
        "[Diagnostics and provenance](diagnostics.json)",
        "From the repository root, reproduce the numerical result and every report byte "
        "without image access or ledger writes:",
        "```bash\nuv run --locked --extra analysis --extra learned python -m "
        "latent_art_bench.painter_prompt_supplement_v1.cli check "
        + shlex.quote(str(result["analysis_id"]))
        + "\n```",
    ]
    return "\n\n".join(parts) + "\n"


def write_bundle(result: dict, output: Path) -> None:
    """Write an absent/empty directory once; caller owns stage binding and publication."""
    _validate(result)
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("supplement report output must be empty; existing files are retained")
    output.mkdir(parents=True, exist_ok=True)
    exports = list(TABLES)
    exports += sorted(
        key
        for key, value in result.items()
        if key not in TABLES
        and isinstance(value, list)
        and value
        and all(isinstance(r, dict) for r in value)
        and key not in {"inputs"}
    )
    if any(Path(name).name != name or name in {".", ".."} for name in exports):
        raise ValueError("table export names must remain inside the report directory")
    for name in exports:
        with (output / f"{name}.csv").open("x", encoding="utf-8", newline="") as handle:
            handle.write(_csv(result[name]))
    diagnostics = {key: value for key, value in result.items() if key not in exports}
    with (output / "diagnostics.json").open("x", encoding="utf-8") as handle:
        handle.write(_json(diagnostics))
    with (output / "REPORT.md").open("x", encoding="utf-8") as handle:
        handle.write(_markdown(result, exports))
    (output / "plots").mkdir()
    with plt.rc_context(STYLE):
        _plots(result, output)
