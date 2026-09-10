"""Create a complete numeric report without reading any generated or reference image."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from latent_art_bench.io import canonical_json, hash_file, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS, SHORT_LABELS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)

from . import generation, randomization
from .common import MANIFESTS, PACKAGE, WORKSPACE
from .prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS

REPORTS = Path("reports/painter_prompt_study_v1")
METHOD_LABELS = {
    "by_name": "By name",
    "style_instruction": "Style instruction",
    "style_aspects": "Style + aspects",
}
TRANSITIONS = (("by_name", "style_instruction"), ("style_instruction", "style_aspects"))
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.hashsalt": "painter-prompt-study-v1",
}
NUMERIC_TABLES = (
    "absolute",
    "primary",
    "secondary",
    "coordinates",
    "distances",
    "scene_contributions",
    "time_diagnostics",
)


def _number(value):
    return "unresolved" if value is None else f"{value:.4f}"


def _label(value):
    return SHORT_LABELS.get(value, METHOD_LABELS.get(value, value))


def _table(headers, rows):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    return "\n".join(
        [
            "| " + " | ".join(map(cell, headers)) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
        ]
        + ["| " + " | ".join(map(cell, row)) + " |" for row in rows]
    )


def _csv(rows):
    stream = io.StringIO(newline="")
    fields = sorted({key for row in rows for key in row})
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        {k: canonical_json(v) if isinstance(v, (dict, list)) else v for k, v in row.items()}
        for row in rows
    )
    return stream.getvalue()


def _availability(result):
    return [
        [
            row["alias"],
            _label(row["method_id"]),
            _label(row["condition"]),
            row["expected"],
            row["statuses"].get("measured", 0) + row["statuses"].get("failed", 0),
            row["statuses"].get("measured", 0),
            row["statuses"].get("failed", 0),
            row["statuses"].get("not_generated", 0),
        ]
        for row in result["availability"]
    ]


def _validate(result, run_id):
    if result["run_id"] != run_id or result["schema_version"] != "painter-prompt-analysis/1.0":
        raise ValueError("analysis identifies a different prompt study")
    if result["status"] not in {"complete", "unavailable_incomplete_grid"}:
        raise ValueError("analysis is not a terminal complete or unavailable result")
    repetitions = result["repetitions"]
    if (
        type(repetitions) is not int
        or repetitions not in (1, 2, 4)
        or result["aliases"] != list(generation.ALIASES)
        or result["methods"] != list(METHOD_IDS)
        or result["painters"] != list(PAINTER_IDS)
        or result["families"] != {k: list(v) for k, v in features.FAMILY_NAMES.items()}
    ):
        raise ValueError("report roster differs from the fixed prompt design")

    def inventory(name, fields, expected):
        rows = result[name]
        keys = [tuple(row[k] for k in fields) for row in rows]
        if len(keys) != len(expected) or set(keys) != expected:
            raise ValueError(f"report requires the complete {name} inventory")
        return {key: row for key, row in zip(keys, rows)}

    cells = {(a, m, c) for a in generation.ALIASES for m in METHOD_IDS for c in CONDITIONS}
    availability = inventory("availability", ("alias", "method_id", "condition"), cells)
    templates = inventory(
        "template_availability",
        ("alias", "method_id", "condition", "template_id"),
        {(*key, t) for key in cells for t in TEMPLATE_IDS},
    )
    for table, count in ((availability, 16 * repetitions), (templates, repetitions)):
        for row in table.values():
            statuses = row["statuses"]
            if (
                type(row["expected"]) is not int
                or row["expected"] != count
                or not set(statuses) <= {"measured", "failed", "not_generated"}
                or any(type(v) is not int or v < 0 for v in statuses.values())
                or sum(statuses.values()) != count
            ):
                raise ValueError("invalid planned or terminal availability counts")
    for key, row in availability.items():
        for disposition in ("measured", "failed", "not_generated"):
            if row["statuses"].get(disposition, 0) != sum(
                templates[(*key, t)]["statuses"].get(disposition, 0) for t in TEMPLATE_IDS
            ):
                raise ValueError("template availability does not sum to its condition cell")
    expected_services = {f"{a}/{m}" for a in generation.ALIASES for m in METHOD_IDS}
    if set(result["service_diagnostics"]) != expected_services:
        raise ValueError("report requires every service and method diagnostic")
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            statuses = result["service_diagnostics"][f"{alias}/{method}"][alias]["statuses"]
            generated = sum(
                availability[alias, method, c]["statuses"].get(k, 0)
                for c in CONDITIONS
                for k in ("measured", "failed")
            )
            if (
                any(type(v) is not int or v < 0 for v in statuses.values())
                or sum(statuses.values()) != 80 * repetitions
                or statuses.get("generated", 0) != generated
            ):
                raise ValueError("service generation counts differ from measurement availability")
    if result["status"] != "complete":
        if any(result.get(key) for key in (*NUMERIC_TABLES, "pair_contributions", "inference")):
            raise ValueError("incomplete grid cannot carry primary or selected numerical results")
        return
    if any(row["statuses"].get("measured", 0) != row["expected"] for row in availability.values()):
        raise ValueError("complete analysis has incomplete availability")
    endpoint_fields = ("alias", "painter_id", "family", "before", "after")
    endpoints = {
        (a, p, f, before, after)
        for a in generation.ALIASES
        for p in PAINTER_IDS
        for f in features.FAMILIES
        for before, after in TRANSITIONS
    }
    primary = inventory("primary", endpoint_fields, endpoints)
    absolute = inventory(
        "absolute",
        ("alias", "method_id", "painter_id", "family"),
        {
            (a, m, p, f)
            for a in generation.ALIASES
            for m in METHOD_IDS
            for p in PAINTER_IDS
            for f in features.FAMILIES
        },
    )
    distances = inventory(
        "distances",
        ("alias", "method_id", "condition", "painter_id", "family"),
        {(a, m, c, p, f) for a, m, c in cells for p in PAINTER_IDS for f in features.FAMILIES},
    )
    inventory(
        "coordinates",
        ("alias", "method_id", "painter_id", "family", "coordinate"),
        {
            (a, m, p, f, coordinate)
            for a in generation.ALIASES
            for m in METHOD_IDS
            for p in PAINTER_IDS
            for f, names in features.FAMILY_NAMES.items()
            for coordinate in names
        },
    )
    scenes = inventory(
        "scene_contributions",
        (*endpoint_fields, "block", "template_id"),
        {(*key, b, t) for key in endpoints for b in range(repetitions) for t in TEMPLATE_IDS},
    )
    inventory("time_diagnostics", endpoint_fields, endpoints)
    inventory(
        "secondary",
        (*endpoint_fields, "endpoint"),
        {(*key, "control_adjusted_transition") for key in endpoints}
        | {
            (a, p, f, "by_name", "style_aspects", "overall_transition")
            for a in generation.ALIASES
            for p in PAINTER_IDS
            for f in features.FAMILIES
        },
    )
    inference = result["inference"]
    if any(
        inference.get(k) != v
        for k, v in dict(
            method="paired_randomization",
            family_size=48,
            alpha=0.05,
            multiplicity="Holm",
            slot_pair_count=16 * repetitions,
            confidence_intervals=False,
        ).items()
    ):
        raise ValueError("report requires the frozen 48-endpoint randomization contract")
    for name in NUMERIC_TABLES:
        for row in result[name]:
            if any(isinstance(v, float) and not np.isfinite(v) for v in row.values()):
                raise ValueError(f"nonfinite value in {name}")
    for row in result["coordinates"]:
        if not np.isfinite(row["median_difference"]):
            raise ValueError("nonfinite coordinate diagnostic")
    for row in distances.values():
        if not np.isfinite(row["distance"]) or row["distance"] < -1e-10:
            raise ValueError("invalid finite distance")
    for row in result["secondary"]:
        if not np.isfinite(row["estimate"]):
            raise ValueError("nonfinite secondary estimate")
    for row in scenes.values():
        before, after = row["before_request_sequence"], row["after_request_sequence"]
        if (
            any(type(v) is not int or not 0 <= v < 480 * repetitions for v in (before, after))
            or before == after
            or row["order_sequence"] != min(before, after)
        ):
            raise ValueError("invalid physical slot chronology")
    for key, row in absolute.items():
        a, m, p, f = key
        distance = distances[a, m, p, p, f]["distance"]
        if not np.isfinite(row["finite_distance"]) or not np.isclose(
            row["finite_distance"], distance
        ):
            raise ValueError("absolute distance differs from the full distance matrix")
    for key, row in primary.items():
        a, p, f, before, after = key
        difference = (
            absolute[a, after, p, f]["finite_distance"]
            - absolute[a, before, p, f]["finite_distance"]
        )
        total = sum(
            scenes[(*key, b, t)]["contribution"] for b in range(repetitions) for t in TEMPLATE_IDS
        )
        if (
            not np.isfinite([row["estimate"], row["raw_p"], row["holm_p"]]).all()
            or not 0 <= row["raw_p"] <= row["holm_p"] <= 1
            or row["status"] != "conditional_randomization"
            or row.get("lower") is not None
            or row.get("upper") is not None
            or not np.isclose(row["estimate"], difference, atol=1e-10)
            or not np.isclose(row["estimate"], total, atol=1e-10)
        ):
            raise ValueError("invalid finite primary contrast or randomization result")
    adjusted = randomization.holm([r["raw_p"] for r in result["primary"]])
    if not np.allclose(adjusted, [r["holm_p"] for r in result["primary"]], rtol=0, atol=1e-14):
        raise ValueError("primary Holm adjustment does not cover all 48 endpoints")


def _save(fig, output, name):
    try:
        for extension, metadata in (
            ("png", {"Software": "LatentArtBench"}),
            ("svg", {"Date": None, "Creator": "LatentArtBench"}),
        ):
            fig.savefig(
                output / "plots" / f"{name}.{extension}",
                format=extension,
                dpi=150,
                metadata=metadata,
            )
    finally:
        plt.close(fig)


def _plots(result, output):
    aliases, families, painters = result["aliases"], list(result["families"]), result["painters"]
    fig, axes = plt.subplots(
        len(aliases),
        len(families),
        figsize=(15, 9),
        squeeze=False,
        sharex="col",
        layout="constrained",
    )
    targets = {
        (r["alias"], r["method_id"], r["family"], r["painter_id"]): r["finite_distance"]
        for r in result["absolute"]
    }
    for i, alias in enumerate(aliases):
        for j, family in enumerate(families):
            ax = axes[i, j]
            for k, method in enumerate(result["methods"]):
                ax.scatter(
                    [targets[alias, method, family, p] for p in painters],
                    np.arange(len(painters)) + (k - 1) * 0.2,
                    color=COLORS[k],
                    label=_label(method),
                    s=42,
                )
            ax.set(title=f"{alias} · {family}", xlabel="Finite V-energy distance")
            ax.set_xlim(left=0)
            ax.set_yticks(range(len(painters)), [_label(p) for p in painters])
            ax.invert_yaxis()
            ax.grid(axis="x", alpha=0.2)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
    fig.suptitle(
        "Generated distributions versus their named painter's reference\n"
        "Every method and painter; smaller distances mean closer measured distributions"
    )
    _save(fig, output, "target_distances")

    fig, axes = plt.subplots(
        len(aliases),
        len(families),
        figsize=(16, 11),
        squeeze=False,
        sharex="col",
        layout="constrained",
    )
    for i, alias in enumerate(aliases):
        for j, family in enumerate(families):
            ax = axes[i, j]
            rows = [r for r in result["primary"] if r["alias"] == alias and r["family"] == family]
            for k, row in enumerate(rows):
                color = COLORS[painters.index(row["painter_id"]) % len(COLORS)]
                ax.scatter(
                    row["estimate"],
                    k,
                    color=color,
                    marker="o" if row["holm_p"] <= 0.05 else "x",
                    zorder=3,
                )
            labels = [
                f"{_label(r['painter_id'])}: "
                + ("name → style" if r["before"] == "by_name" else "style → aspects")
                for r in rows
            ]
            ax.set_yticks(range(len(rows)), labels)
            ax.invert_yaxis()
            ax.axvline(0, color="#444444", linewidth=0.8)
            ax.set(title=f"{alias} · {family}", xlabel="Later − earlier prompt distance")
            ax.grid(axis="x", alpha=0.2)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    fig.suptitle(
        "All 48 finite prompt transitions: conditional randomization tests\n"
        "● Holm p ≤ 0.05; × Holm p > 0.05. No confidence intervals; negative means closer"
    )
    _save(fig, output, "primary_transitions")

    fig, axes = plt.subplots(
        len(aliases), len(families), figsize=(15, 9), squeeze=False, layout="constrained"
    )
    for i, alias in enumerate(aliases):
        for j, family in enumerate(families):
            ax = axes[i, j]
            for p, painter in enumerate(painters):
                for t, (before, after) in enumerate(TRANSITIONS):
                    rows = sorted(
                        (
                            r
                            for r in result["scene_contributions"]
                            if (r["alias"], r["family"], r["painter_id"], r["before"], r["after"])
                            == (alias, family, painter, before, after)
                        ),
                        key=lambda r: r["order_sequence"],
                    )
                    transition = "name → style" if t == 0 else "style → aspects"
                    label = f"{_label(painter)}: {transition}"
                    ax.plot(
                        [r["order_sequence"] + 1 for r in rows],
                        [r["contribution"] for r in rows],
                        color=COLORS[p],
                        linestyle="-" if t == 0 else "--",
                        linewidth=1,
                        marker="." if len(rows) < 10 else None,
                        label=label,
                    )
            ax.axhline(0, color="#444444", linewidth=0.8)
            ax.set(
                title=f"{alias} · {family}",
                xlabel="Earlier physical request slot in each scene pair",
                ylabel="Finite-contrast scene contribution",
            )
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.grid(alpha=0.2)
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=4)
    fig.suptitle(
        "Every primary scene contribution in physical request order\n"
        "Descriptive chronology; these traces do not establish absence of service carryover"
    )
    _save(fig, output, "scene_order")


def _markdown(result, tables):
    complete = result["status"] == "complete"
    expected = sum(row["expected"] for row in result["availability"])
    measured = sum(row["statuses"].get("measured", 0) for row in result["availability"])
    generated = sum(
        row["statuses"].get("measured", 0) + row["statuses"].get("failed", 0)
        for row in result["availability"]
    )
    parts = [
        "# Prompt methods and feature distances from artists' paintings",
        "This study compares generated-image distributions with the fixed original-painting "
        "reference for Monet, Sisley, Pissarro and Cézanne, separately in color, spatial "
        "structure and digital texture. It asks whether explicit style instructions and "
        "additional attention to broad visual aspects change those distances.",
    ]
    if complete:
        parts += [
            "All registered images were measured. The tables and plots retain every "
            "service, painter, feature family and prompt method. A smaller distance means "
            "closer distributions in the measured feature family; no combined score, "
            "model winner or reproduction verdict is assigned.",
            "![All own-target distances](plots/target_distances.png)",
        ]
        for alias in result["aliases"]:
            lookup = {
                (r["method_id"], r["painter_id"], r["family"]): r["finite_distance"]
                for r in result["absolute"]
                if r["alias"] == alias
            }
            parts += [
                f"## Own-target finite distances: {alias}",
                _table(
                    ["Painter", "Family", *map(_label, result["methods"])],
                    [
                        [_label(p), f] + [_number(lookup[m, p, f]) for m in result["methods"]]
                        for p in result["painters"]
                        for f in result["families"]
                    ],
                ),
            ]
    else:
        parts += [
            "**Primary prompt inference is unavailable because the registered grid is "
            "incomplete.** No distance comparison, primary randomization test, selected "
            "complete-case analysis or inference plot is reported. Every planned condition "
            "and its terminal availability counts appear below."
        ]
    parts += [
        "## Population and availability",
        f"Run `{result['run_id']}` registered **{expected:,} requests**: "
        f"**{generated:,} generated images** and **{measured:,} measured images**. "
        f"There are {result['repetitions']} repetition blocks, with all 16 original scene "
        "templates in every method × painter/artist-free × requested-service cell. "
        "The original by-name strings remain verbatim. Style instruction and style plus "
        "aspects each have their own artist-free control. No earlier generated images "
        "are pooled with these new draws.",
        _table(
            [
                "Requested service",
                "Method",
                "Condition",
                "Planned",
                "Generated",
                "Measured",
                "Normalization failures",
                "Not generated",
            ],
            _availability(result),
        ),
        "These counts distinguish generation availability from measurement success; every "
        "failure remains in the complete availability export and terminal ledgers.",
    ]
    if "template_availability" in result:
        parts.append(
            "[Template-level availability](template_availability.csv) retains every "
            "one of the 480 service × method × condition × template cells, including "
            "all failures and ungenerated dispositions."
        )
    if "reference_counts" in result:
        parts.append(
            _table(
                ["Reference painter", "Fixed measured paintings"],
                [[_label(p), n] for p, n in result["reference_counts"].items()],
            )
        )
    if "scaler_development_counts" in result:
        parts.append(
            _table(
                ["Scaler painter", "Frozen new-development paintings"],
                [[_label(p), n] for p, n in result["scaler_development_counts"].items()],
            )
        )
    parts += [
        f"The source method is `{result['source_method_id']}`. Its already exposed fixed "
        "reference contains 649 measured digital surrogates of Wikidata-declared "
        "outdoor-place paintings. These are not a new holdout or a probability sample of "
        "the artists' complete oeuvres. New prompt wording and inference were fixed before "
        "new generation, after the earlier reference and generated results were exposed.",
        "The original 512-pixel normalization and all 31 raw features are reused. The "
        "unchanged scaler was fitted to 221 new-development paintings using equal painter "
        "weights: each coordinate subtracts its frozen median and divides by its frozen "
        "IQR. Color has 11 coordinates, spatial/orientation 8, and digital texture 12. "
        "Family magnitudes are not directly comparable and are never combined. No scaler "
        "is fitted to the new generated outputs.",
        "## Distance and prompt-effect estimands",
        "The own-target tables use the finite empirical V-energy statistic: twice the "
        "mean Euclidean reference–generated distance, minus the mean reference–reference "
        "and generated–generated distances, including zero diagonals. This compares "
        "location and distributional spread. It has no calibrated reproduction threshold. "
        "Absolute distances and prompt-effect magnitudes are finite descriptions of these "
        "observed images. No confidence intervals are reported.",
    ]
    if not complete:
        parts[-1] = (
            "Finite empirical energy distances and randomized prompt comparisons were planned. "
            "They remain unavailable for this incomplete grid, and no corresponding numerical "
            "result tables or confidence intervals are emitted."
        )
    if complete:
        primary_rows = [
            [
                r["alias"],
                _label(r["painter_id"]),
                r["family"],
                f"{_label(r['before'])} → {_label(r['after'])}",
                _number(r["estimate"]),
                f"{r['raw_p']:.6g}",
                f"{r['holm_p']:.6g}",
                r["status"],
            ]
            for r in result["primary"]
        ]
        parts += [
            "## All 48 primary prompt transitions",
            "Each contrast is **later-method distance minus earlier-method distance to "
            "the same painter**. Negative values favor the later instruction. The two "
            "planned transitions are by-name → style instruction and style instruction → "
            "style plus aspects, for every service, painter and family.",
            "Within each service × condition × scene × repetition, the three methods "
            "were independently randomized to three fixed request slots. For each transition, "
            "the test conditions on the third method's slot and exchanges the other two "
            "labels independently across all 16 × repetition scene pairs. The tested null "
            "is the **sharp absence of any prompt-method effect, with no interference across "
            "requests** (or joint invariance under these label swaps). Equality of two "
            "population energy distances alone does not imply this null. A small p-value "
            "is evidence against that sharp null, not a population distance confidence bound.",
            f"There are **{16 * result['repetitions']} matched scene pairs per endpoint**. "
            "With one repetition, all 65,536 sign assignments are enumerated. With two or "
            "four repetitions, 99,999 seeded Monte Carlo assignments use the conservative "
            "(exceedances + 1)/(draws + 1) p-value. Ties count toward the tail. "
            "**Holm adjustment across all 48 primary endpoints** controls the family error "
            "rate at 0.05 when these randomization null assumptions hold, without requiring "
            "independent endpoints. No confidence intervals or equivalence conclusions are "
            "reported. A nonsignificant result does not establish equal styles or distances.",
            "![Every primary transition](plots/primary_transitions.png)",
            _table(
                [
                    "Service",
                    "Painter",
                    "Family",
                    "Transition",
                    "Finite effect",
                    "Raw p",
                    "Holm p",
                    "Test status",
                ],
                primary_rows,
            ),
            "## Secondary controls, coordinates and time diagnostics",
            "The 48 control-adjusted transitions subtract the corresponding artist-free "
            "transition from each named transition. The other 24 secondary comparisons "
            "compare style plus aspects directly with by-name. All 72 are descriptive, "
            "without separately qualified confidence intervals; see [secondary.csv]"
            "(secondary.csv). All 744 coordinate diagnostics and all 360 generated-condition "
            "× reference-painter × family distances are exported without feature selection.",
            "![Every chronological scene contribution](plots/scene_order.png)",
            "The scene-order figure includes every primary contribution; the contributions "
            "sum to each finite distance contrast. The 48 first-half and second-half means "
            "and contribution standard deviations are in [time_diagnostics.csv]"
            "(time_diagnostics.csv). These are descriptive order checks. Random assignment "
            "can accommodate fixed slot or scene heterogeneity under the sharp null, but "
            "service carryover or interference can invalidate label exchangeability. "
            "A multiday run can experience changing service behavior. Repetitions are "
            "acquisition blocks, not a claim of independent population draws; matching "
            "scenes does not establish shared latent seeds.",
        ]
    calibration_id = result.get("calibration_id")
    if calibration_id:
        decision = f"../../../{MANIFESTS.as_posix()}/{identifier(calibration_id)}/decision.json"
        parts += [
            "## Prospective randomization calibration",
            f"The frozen [calibration decision and numerical tables]({decision}) record "
            "method qualification at one, two and four repetitions using synthetic contribution "
            "magnitudes and randomized assignment signs, without tuning on new empirical "
            "outcomes. The numerical tables include family error, sign-alignment power "
            "diagnostics and deliberately invalid persistent-sign stress. These are "
            "contribution-space simulations; they do not establish no interference in a "
            "remote service or guarantee power for real prompt effects. The small image "
            "budget limits precision and population generalization.",
        ]
    service_rows = []
    for key, nested in result.get("service_diagnostics", {}).items():
        alias, method = key.split("/", 1)
        info = nested.get(alias, nested)
        reported = info.get("reported_settings", {})
        service_rows.append(
            [
                alias,
                _label(method),
                canonical_json(info.get("statuses", {})),
                canonical_json(reported.get("quality", {})),
                len(info.get("decoded_sizes", {})),
                canonical_json(info.get("setting_mismatches", {})),
            ]
        )
    parts += [
        "## Observed service behavior and interpretation limits",
        "`gpt-image-1` and `gpt-image-2` are requested OAuth service aliases with no "
        "independently attested underlying model snapshots. Requested 1024×1024, medium, "
        "opaque PNG settings are distinct from reported quality and decoded geometry. "
        "The table records provider metadata, not visual-quality rankings; complete "
        "reported model/settings, geometry counts and latency summaries are retained in "
        "[service_diagnostics.json](service_diagnostics.json).",
        _table(
            [
                "Service",
                "Method",
                "Generation statuses",
                "Reported quality counts",
                "Distinct decoded sizes",
                "Setting mismatch counts",
            ],
            service_rows,
        ),
        "Subject content, aspect ratio, color profiles, source workflows and digital "
        "reproduction may alter these measurements. The 31 features do not isolate "
        "content-free style, artistic quality, intention or physical brushwork. Independent "
        "capture calibration and a validated equivalence margin are absent. No comparison "
        "here establishes reproduction, authorship or broad model superiority.",
    ]
    if "copy_diagnostics" in result:
        parts.append(
            "[Copy-screen diagnostics](copy_diagnostics.json) retain the complete "
            "available exact-file and nearest perceptual-hash results. Perceptual-hash "
            "candidates are uncalibrated similarity screens, not copying adjudications; "
            "no hit cannot establish absence of training-data overlap. No image is "
            "excluded from an endpoint because of its screen result."
        )
    parts += [
        "Reviews were maintainer-run LLM subagent reviews, not institutionally independent "
        "reviews. No manuscript or artistic-quality winner is produced by this report.",
        "## Complete exports and provenance",
        ", ".join(f"[{name}.csv]({name}.csv)" for name in tables) + ". "
        "CSV files retain full floating-point precision; nested counts remain JSON cells. "
        "No confidence-interval columns are manufactured. Figures are provided as PNG "
        "and SVG. The report command reads only numeric evidence and metadata.",
        f"The complete [analysis.json](../../../{MANIFESTS.as_posix()}/{result['run_id']}"
        f"/analysis.json) and [report receipt](../../../{MANIFESTS.as_posix()}/"
        f"{result['run_id']}"
        "/report_receipt.json) bind the source analysis, implementation and every report "
        "file by SHA-256. Existing reports are never overwritten.",
    ]
    return "\n\n".join(parts) + "\n"


def _write_bundle(result, output):
    tables = []
    for name, value in result.items():
        if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
            (output / f"{name}.csv").write_text(_csv(value), encoding="utf-8", newline="\n")
            tables.append(name)
    for name in ("service_diagnostics", "copy_diagnostics"):
        if name in result:
            publish(output / f"{name}.json", result[name])
    if result["status"] == "complete":
        (output / "plots").mkdir()
        with plt.rc_context(STYLE):
            _plots(result, output)
    (output / "REPORT.md").write_text(_markdown(result, tables), encoding="utf-8", newline="\n")


def execute(root: Path, run_id: str) -> dict:
    """Verify numeric source bindings and publish a fresh report, without image access."""
    root = Path(root).resolve()
    identifier(run_id)
    directory = root / MANIFESTS / run_id
    target = root / REPORTS / run_id
    target.resolve().relative_to((root / REPORTS).resolve())
    with stage_lock(root / WORKSPACE / run_id / ".report.writer.lock"):
        if target.is_symlink() or (directory / "report_receipt.json").exists():
            raise FileExistsError("prompt report output already exists")
        source_bytes = (directory / "analysis.json").read_bytes()
        result = json.loads(source_bytes)
        _validate(result, run_id)
        verify_bindings(root, result["inputs"])
        implementation = PACKAGE / "report.py"
        implementation_hash = hash_file(root / implementation)
        if implementation_hash != hash_file(Path(__file__)):
            raise ValueError("report implementation differs from the recorded root")
        freeze_path = directory / "generation_freeze.json"
        freeze = json.loads(freeze_path.read_bytes())
        frozen_code = [row for row in freeze["inputs"] if row["path"] == implementation.as_posix()]
        commit = freeze["recorded_git_commit"]
        blob = subprocess.run(
            ["git", "show", f"{commit}:{implementation.as_posix()}"], cwd=root, capture_output=True
        )
        if (
            len(frozen_code) != 1
            or frozen_code[0]["sha256"] != implementation_hash
            or blob.returncode
            or hashlib.sha256(blob.stdout).hexdigest() != implementation_hash
        ):
            raise ValueError("report implementation is not bound to the recorded generation commit")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".report-", dir=target.parent) as name:
            temporary = Path(name) / "bundle"
            temporary.mkdir()
            _write_bundle(result, temporary)
            if target.exists():
                if not target.is_dir() or any(path.is_symlink() for path in target.rglob("*")):
                    raise ValueError("unreceipted report is not a regular bundle")
                old = {
                    p.relative_to(target).as_posix(): hash_file(p)
                    for p in target.rglob("*")
                    if p.is_file()
                }
                new = {
                    p.relative_to(temporary).as_posix(): hash_file(p)
                    for p in temporary.rglob("*")
                    if p.is_file()
                }
                if old != new:
                    raise ValueError("unreceipted report differs from complete source reproduction")
            else:
                temporary.rename(target)
        receipt = dict(
            schema_version="painter-prompt-study-report-receipt/1.0",
            run_id=run_id,
            recorded_git_commit=commit,
            analysis_status=result["status"],
            inputs=[
                dict(
                    path=(MANIFESTS / run_id / "analysis.json").as_posix(),
                    sha256=hashlib.sha256(source_bytes).hexdigest(),
                ),
                dict(path=implementation.as_posix(), sha256=implementation_hash),
                dict(
                    path=(MANIFESTS / run_id / "generation_freeze.json").as_posix(),
                    sha256=hash_file(freeze_path),
                ),
            ],
            files=[
                dict(path=path.relative_to(root).as_posix(), sha256=hash_file(path))
                for path in sorted(target.rglob("*"))
                if path.is_file()
            ],
            completed_at_utc=utc_now().isoformat(),
        )
        publish(directory / "report_receipt.json", receipt)
        return receipt
