"""Render the sealed revision JSON as tables, scientific figures and readable text.

This is presentation code. It does not load image bytes, fit models, draw new
samples, or change the frozen calculations. Publication is handled separately.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

INPUT = Path("data/manifests/painter_distribution_revision_v1/pdrv1-numeric-20260907/analysis.json")
ROUTES = ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
PAINTERS = ("claude_monet", "paul_cezanne")
VIEWS = ("original31", "nonredundant28", "family_balanced31", "no_texture19")
PIPELINES = ("primary512", "resolution256", "jpeg90_512")
ROUTE_NAMES = dict(zip(ROUTES, ("Nano Banana 2", "FLUX.2 Max", "OAuth Image 2 service")))
SHORT_ROUTES = dict(zip(ROUTES, ("NB2", "FLUX", "OAuth")))
PAINTER_NAMES = dict(zip(PAINTERS, ("Monet", "Cézanne")))
VIEW_NAMES = dict(
    zip(VIEWS, ("Original 31", "Nonredundant 28", "Family-balanced 31", "No texture 19"))
)
PIPELINE_NAMES = dict(zip(PIPELINES, ("512", "256", "JPEG 90")))
COLORS = ("#0072B2", "#D55E00", "#009E73")
FAMILY_COLORS = ("#0072B2", "#E69F00", "#009E73")
FAMILIES = ("color", "spatial", "texture")


def select(rows, **labels):
    return [r for r in rows if all(r.get(k) == v for k, v in labels.items())]


def one(rows, **labels):
    matches = select(rows, **labels)
    if len(matches) != 1:
        raise ValueError(f"expected one sealed result for {labels}; got {len(matches)}")
    return matches[0]


def scalars(row, prefix=""):
    """Flatten dictionaries; retain list lengths while identities stay in source JSON."""
    result = {}
    for key, value in row.items():
        name = prefix + key
        if isinstance(value, dict):
            result.update(scalars(value, name + "."))
        elif isinstance(value, list):
            result[name + ".n"] = len(value)
        else:
            result[name] = value
    return result


def labels(row):
    return {
        k: row[k]
        for k in (
            "pipeline",
            "metric_view",
            "painter_id",
            "route",
            "condition",
            "domain",
            "source_route",
            "target_route",
            "cell_id",
        )
        if k in row
    }


def _tables(analysis):
    metric, diagnostic, timing = (analysis[k] for k in ("metrics", "diagnostics", "timing"))
    tables = {
        "metric_cells": [scalars(r) for r in metric["cells"]],
        "prompt_contrasts": [scalars(r) for r in metric["prompt_contrasts"]],
        "reference_influence": [scalars(r) for r in metric["reference_influence"]],
        "original_endpoints": [scalars(r) for r in analysis["original_endpoints"]],
        "timing_groups": [scalars(r) for r in timing["groups"]],
        "timing_contrasts": [scalars(r) for r in timing["contrasts"]],
        "attempt_dispositions": [scalars(r) for r in timing["disposition_records"]],
        "cell_memberships": [dict(membership_id=k, **scalars(v))
                             for k, v in metric["memberships"].items()],
        "heldout_reference_designs": [scalars(r) for r in diagnostic["heldout_reference_designs"]],
        "study_accounting": [
            dict(
                analysis["source_counts"],
                physical_research_attempts=timing["physical_research_attempts"],
                elapsed_hours=timing["elapsed_hours"],
                run_id=analysis["run_id"],
                status="descriptive",
                new_generation_calls=0,
            )
        ],
    }
    contributions = []
    for row in metric["trace_contributions"]:
        for domain in row["domains"]:
            for level in ("coordinates", "families"):
                for value in domain[level]:
                    contributions.append(
                        dict(
                            labels(row),
                            domain=domain["domain"],
                            level=level,
                            total_trace=domain["total_trace"],
                            **value,
                        )
                    )
    tables["trace_contributions"] = contributions
    correlations = []
    for row in metric["development_correlations"]:
        if row["status"] == "unavailable":
            correlations.append(scalars(row))
            continue
        for i, first in enumerate(row["feature_names"]):
            for j, second in enumerate(row["feature_names"]):
                correlations.append(
                    dict(
                        pipeline=row["pipeline"],
                        status=row["status"],
                        first_feature=first,
                        second_feature=second,
                        pearson=row["correlation"][i][j],
                        n_development=row["n_development"],
                        weighting=row["weighting"],
                    )
                )
    tables["development_correlations"] = correlations
    scales, scale_cells, scale_contrasts = [], [], []
    feature_names = metric["development_correlations"][0]["feature_names"]
    for row in metric["development_scaler_sensitivity"]:
        omitted = row.get("omitted_development_painter")
        for name, value in zip(feature_names, row.get("iqr_relative_to_frozen_scale", [])):
            scales.append(
                dict(
                    omitted_development_painter=omitted,
                    feature=name,
                    iqr_relative_to_frozen_scale=value,
                    status=row["status"],
                    reason=row.get("reason"),
                )
            )
        scale_cells.extend(
            dict(omitted_development_painter=omitted, **scalars(r)) for r in row.get("cells", [])
        )
        scale_contrasts.extend(
            dict(omitted_development_painter=omitted, **scalars(r))
            for r in row.get("prompt_contrasts", [])
        )
        if row["status"] == "unavailable":
            scale_cells.append(scalars(row))
            scale_contrasts.append(scalars(row))
    tables.update(
        development_scales=scales,
        development_scale_cells=scale_cells,
        development_scale_contrasts=scale_contrasts,
    )
    matrices, interactions, placebos = [], [], []
    for row in metric["specificity"]:
        header = labels(row)
        matrices.extend(dict(header, **scalars(value)) for value in row.get("energy_matrix", []))
        interactions.append(
            scalars(
                {
                    k: v
                    for k, v in row.items()
                    if k
                    not in ("energy_matrix", "generated_membership", "identical_payload_placebo")
                }
            )
        )
        if "identical_payload_placebo" in row:
            placebos.append(dict(header, **scalars(row["identical_payload_placebo"])))
    tables.update(
        specificity_matrices=matrices,
        specificity_interactions=interactions,
        identical_payload_placebos=placebos,
    )
    coverage, neighbors, draws, heldout, heldout_draws, metadata_rules = [], [], [], [], [], []
    for row in diagnostic["coverage"]:
        header = labels(row)
        metadata_rules.append(dict(header, **scalars(row["square_metadata_baseline"])))
        designs = row.get("sample_designs", [])
        for value in row.get("k_results", []):
            base = dict(header, k=value["k"], status=value["status"])
            coverage.append(
                dict(
                    base,
                    mode="all_available",
                    sample_size=row["n_generated"],
                    reference_n=row["n_original"],
                    coverage=value.get("all_available"),
                    reason=value.get("reason"),
                )
            )
            for neighbor in value.get("per_reference", []):
                neighbors.append(dict(base, **scalars(neighbor)))
            for curve in value.get("curves", []):
                design = designs[curve["sample_design_index"]]
                label = dict(
                    base,
                    mode=design["mode"],
                    size_label=design["size_label"],
                    sample_size=design["sample_size"],
                    reference_n=row["n_original"],
                )
                coverage.append(dict(label, **scalars(curve)))
                for i, value_ in enumerate(curve.get("coverage", [])):
                    draws.append(
                        dict(
                            label,
                            draw=i,
                            coverage=value_,
                            **scalars(design["observed_class_counts"][i], "class_n."),
                        )
                    )
            for i, design in enumerate(designs):
                if design["status"] == "unavailable":
                    coverage.append(dict(base, sample_design_index=i, **scalars(design)))
        control = row["heldout_real_control"]
        if control["status"] == "unavailable":
            heldout.append(dict(header, **scalars(control)))
        for value in control.get("k_results", []):
            base = dict(header, k=value["k"])
            heldout.append(dict(base, **scalars(value)))
            for i, (real, generated, difference, radius) in enumerate(
                zip(
                    value.get("real_query_coverage", []),
                    value.get("generated_query_coverage", []),
                    value.get("paired_generated_minus_real", []),
                    value.get("median_anchor_radius", []),
                )
            ):
                heldout_draws.append(
                    dict(
                        base,
                        draw=i,
                        real_query_coverage=real,
                        generated_query_coverage=generated,
                        generated_minus_real=difference,
                        median_anchor_radius=radius,
                    )
                )
    tables.update(
        coverage_summary=coverage,
        coverage_neighborhoods=neighbors,
        coverage_draws=draws,
        heldout_real_controls=heldout,
        heldout_real_draws=heldout_draws,
        metadata_square_rule=metadata_rules,
    )
    descriptor_ranges, counts, associations = [], [], []
    for row in diagnostic["metadata"]:
        header = labels(row)
        for key, value in row["metadata"].items():
            if key == "descriptor_ranges":
                descriptor_ranges.extend(
                    dict(header, descriptor=k, **scalars(v)) for k, v in value.items()
                )
            elif isinstance(value, dict):
                counts.extend(dict(header, descriptor=key, value=k, n=v) for k, v in value.items())
        for value in row["associations"]:
            base = dict(
                header, **scalars({k: v for k, v in value.items() if k != "feature_spearman"})
            )
            if "feature_spearman" in value:
                associations.extend(
                    dict(base, feature=k, spearman=v) for k, v in value["feature_spearman"].items()
                )
            else:
                associations.append(base)
    tables.update(
        metadata_counts=counts,
        metadata_descriptor_ranges=descriptor_ranges,
        metadata_feature_associations=associations,
    )
    transfer, folds, scores = [], [], []
    for row in diagnostic["cross_route_transfer"]:
        header = labels(row)
        if row["split"]["status"] == "unavailable":
            transfer.append(dict(header, **scalars(row["split"])))
        for name, value in row.get("kernels", {}).items():
            base = dict(header, kernel=name, status=value["status"])
            transfer.append(
                dict(base, **scalars({k: v for k, v in value.items() if k != "fold_metrics"}))
            )
            folds.extend(dict(base, **scalars(fold)) for fold in value.get("fold_metrics", []))
            for domain, id_key, score_key in (
                ("original", "reference_image_ids", "original_scores"),
                ("generated", "target_image_ids", "target_generated_scores"),
            ):
                scores.extend(
                    dict(base, domain=domain, image_id=image_id, score=score)
                    for image_id, score in zip(row[id_key], value.get(score_key, []))
                )
    tables.update(cross_route_transfer=transfer, cross_route_folds=folds, cross_route_scores=scores)
    tables["availability"] = [
        dict(section="capture_workflow_holdout", **diagnostic["source_holdout"])
    ]
    return tables


def _csv(path, rows):
    if not rows:
        rows = [dict(status="unavailable", reason="empty declared result section")]
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _save(fig, output, name):
    fig.savefig(
        output / (name + ".png"),
        dpi=180,
        bbox_inches="tight",
        metadata={"Software": "painter_distribution_revision_v1"},
    )
    fig.savefig(
        output / (name + ".svg"),
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "painter_distribution_revision_v1"},
    )
    plt.close(fig)


def _metric_sensitivity(analysis, output):
    contrasts = analysis["metrics"]["prompt_contrasts"]
    row_labels = [(p, r) for p in PAINTERS for r in ROUTES]
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.3), layout="constrained")
    for ax, view in zip(axes.flat, VIEWS):
        values = np.array(
            [
                [
                    one(contrasts, painter_id=p, route=r, metric_view=view, pipeline=pipe)[
                        "energy_change"
                    ]
                    for pipe in PIPELINES
                ]
                for p, r in row_labels
            ]
        )
        bound = max(float(np.abs(values).max()), 0.01)
        shown = ax.imshow(values, cmap="RdBu_r", vmin=-bound, vmax=bound, aspect="auto")
        ax.set_xticks(range(3), [PIPELINE_NAMES[p] for p in PIPELINES])
        ax.set_yticks(range(6), [PAINTER_NAMES[p] + " · " + SHORT_ROUTES[r] for p, r in row_labels])
        ax.set_title(VIEW_NAMES[view])
        for (i, j), value in np.ndenumerate(values):
            ax.text(
                j,
                i,
                f"{value:+.3f}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if abs(value) > 0.58 * bound else "#222222",
            )
        fig.colorbar(shown, ax=ax, fraction=0.035, pad=0.025, label="Energy change")
    fig.suptitle(
        "Named minus artist-free energy across the fixed diagnostic grid\n"
        "Negative is closer; each panel uses its own metric units and color scale",
        fontsize=13,
    )
    _save(fig, output, "metric_sensitivity")


def _variance_decomposition(analysis, output):
    metric = analysis["metrics"]
    groups = [(p, r) for p in PAINTERS for r in ROUTES]
    parts = ("within_brief", "between_brief_within_class", "between_class")
    part_labels = ("Within brief", "Between briefs within content", "Between content classes")
    fig, axes = plt.subplots(
        1, 2, figsize=(12, 7.2), gridspec_kw={"width_ratios": [1.2, 1]}, layout="constrained"
    )
    for i, (painter, route) in enumerate(groups):
        cell = dict(
            pipeline="primary512", metric_view="original31", painter_id=painter, route=route
        )
        free = one(metric["cells"], **cell, condition="artist_free")
        named = one(metric["cells"], **cell, condition="named")
        for position, row, hatch in ((i - 0.18, free, "///"), (i + 0.18, named, None)):
            left = 0
            for key, color in zip(parts, FAMILY_COLORS):
                value = row["generated_decomposition"][key] / free["generated_trace"]
                axes[0].barh(
                    position,
                    value,
                    left=left,
                    height=0.3,
                    color=color,
                    edgecolor="white",
                    linewidth=0.7,
                    hatch=hatch,
                    alpha=0.55 if hatch else 1,
                )
                left += value
        contrast = one(metric["prompt_contrasts"], **cell)
        ratios = contrast["generated_decomposition_ratios"]
        for j, (key, color, marker) in enumerate(
            zip(
                ("total_trace", "within_brief", "between_brief_means"),
                ("#333333", COLORS[0], COLORS[1]),
                ("o", "s", "^"),
            )
        ):
            value = ratios[key]
            axes[1].scatter(value, i + (j - 1) * 0.17, color=color, marker=marker, s=40, zorder=3)
            axes[1].text(value + 0.025, i + (j - 1) * 0.17, f"{value:.2f}", va="center", fontsize=8)
    for ax in axes:
        ax.set_yticks(range(6), [PAINTER_NAMES[p] + " · " + SHORT_ROUTES[r] for p, r in groups])
        ax.invert_yaxis()
        ax.axvline(1, color="#777777", linestyle="--", linewidth=1)
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)
    axes[0].set(
        xlim=(0, 1.06),
        title="Finite trace decomposition",
        xlabel="Trace / total trace of the corresponding artist-free collection",
    )
    axes[0].legend(
        handles=[Patch(facecolor=c, label=t) for c, t in zip(FAMILY_COLORS, part_labels)],
        loc="upper left",
        bbox_to_anchor=(0, -0.18),
        fontsize=8,
        frameon=False,
    )
    axes[1].set(xlim=(0, 1.31), title="Named / artist-free component ratios", xlabel="Ratio")
    axes[1].legend(
        handles=[
            Line2D([], [], color=c, marker=s, linestyle="", label=t)
            for c, s, t in zip(
                ("#333333", COLORS[0], COLORS[1]),
                ("o", "s", "^"),
                ("Total", "Within brief", "Between brief means"),
            )
        ],
        loc="upper left",
        bbox_to_anchor=(0, -0.18),
        fontsize=8,
        frameon=False,
    )
    fig.suptitle(
        "Primary 512 / original 31: contraction can occur between briefs\n"
        "Left: hatched artist-free and solid named bars; no population variance claim",
        fontsize=12,
    )
    _save(fig, output, "variance_decomposition")


def _specificity_plot(analysis, output):
    rows = select(
        analysis["metrics"]["specificity"], pipeline="primary512", metric_view="original31"
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.8), layout="constrained")
    x = np.arange(3)
    for shift, condition, color in ((-0.18, "artist_free", "#777777"), (0.18, "named", COLORS[0])):
        values = [
            one(rows, route=r, condition=condition)["interaction_terms"]["energy"] for r in ROUTES
        ]
        bars = axes[0].bar(
            x + shift,
            values,
            width=0.33,
            color=color,
            label="Artist-free" if condition == "artist_free" else "Named",
        )
        axes[0].bar_label(bars, labels=[f"{v:+.3f}" for v in values], padding=3, fontsize=8)
    placebo = [
        one(rows, route=r, condition="artist_free")["identical_payload_placebo"]["energy"]
        for r in ROUTES
    ]
    bars = axes[1].bar(x, placebo, width=0.55, color=COLORS)
    axes[1].bar_label(bars, labels=[f"{v:.3f}" for v in placebo], padding=3, fontsize=9)
    for ax in axes:
        ax.set_xticks(x, [SHORT_ROUTES[r] for r in ROUTES])
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
    axes[0].axhline(0, color="#555555", linewidth=0.8)
    axes[0].set(
        title="Painter prompt × reference interaction",
        ylabel="Double energy contrast",
        ylim=(-2.15, 0.35),
    )
    axes[0].legend(frameon=False)
    axes[1].set(
        title="Identical-payload artist-free collections",
        ylabel="Between-collection V-energy",
        ylim=(0, max(placebo) * 1.3),
    )
    fig.suptitle(
        "Equal content masses, primary 512 / original 31\n"
        "Negative interaction favors own painter; placebo distances are not null thresholds",
        fontsize=12,
    )
    _save(fig, output, "specificity")


def _coverage_curve(row, mode):
    values = []
    for k in (1, 3, 5):
        value = one(row["k_results"], k=k)
        if mode == "all_available":
            values.append(value["all_available"])
        else:
            index = next(
                i
                for i, d in enumerate(row["sample_designs"])
                if d["size_label"] == "reference_n" and d["mode"] == "reference_class_counts"
            )
            values.append(one(value["curves"], sample_design_index=index)["median"])
    return values


def _coverage_controls(analysis, output):
    rows = analysis["diagnostics"]["coverage"]
    fig, axes = plt.subplots(2, 2, figsize=(10.7, 7), layout="constrained")
    for column, painter in enumerate(PAINTERS):
        original = None
        for route, color in zip(ROUTES, COLORS):
            row = one(rows, painter_id=painter, route=route, condition="named")
            axes[0, column].plot(
                (1, 3, 5),
                _coverage_curve(row, "matched"),
                "o-",
                color=color,
                linewidth=1.6,
                markersize=4,
                label=SHORT_ROUTES[route],
            )
            axes[0, column].plot(
                (1, 3, 5), _coverage_curve(row, "all_available"), ":", color=color, linewidth=1.4
            )
            control = row["heldout_real_control"]["k_results"]
            axes[1, column].plot(
                (1, 3, 5),
                [one(control, k=k)["generated_summary"]["median"] for k in (1, 3, 5)],
                "o-",
                color=color,
                linewidth=1.6,
                markersize=4,
            )
            if original is None:
                original = control
        axes[1, column].plot(
            (1, 3, 5),
            [one(original, k=k)["real_summary"]["median"] for k in (1, 3, 5)],
            "s--",
            color="#333333",
            linewidth=1.6,
        )
        axes[1, column].fill_between(
            (1, 3, 5),
            [one(original, k=k)["real_summary"]["quantile05"] for k in (1, 3, 5)],
            [one(original, k=k)["real_summary"]["quantile95"] for k in (1, 3, 5)],
            color="#888888",
            alpha=0.15,
        )
        axes[0, column].set_title(PAINTER_NAMES[painter] + ": full reference anchors")
        axes[1, column].set_title(PAINTER_NAMES[painter] + ": disjoint real controls")
    for ax in axes.flat:
        ax.set(xticks=(1, 3, 5), xlabel="Neighborhood k", ylim=(0, 1.04), ylabel="Coverage")
        ax.grid(alpha=0.2)
    axes[0, 0].legend(frameon=False, fontsize=8, loc="upper left")
    axes[0, 1].legend(
        handles=[
            Line2D([], [], color="#333333", marker="o", label="Class-count-matched median"),
            Line2D([], [], color="#333333", linestyle=":", label="All available"),
        ],
        frameon=False,
        fontsize=8,
        loc="upper left",
    )
    axes[1, 0].legend(
        handles=[
            Line2D([], [], color="#333333", marker="s", linestyle="--", label="Real-query median"),
            Patch(facecolor="#888888", alpha=0.15, label="Real-query 5–95% draw range"),
        ],
        frameon=False,
        fontsize=8,
        loc="lower right",
    )
    fig.suptitle(
        "Named collections: coverage depends on sampling, anchors and k\n"
        "100 fixed draws; ranges are not confidence intervals; lower-row anchors differ",
        fontsize=12,
    )
    _save(fig, output, "coverage_controls")


def _cross_route_detection(analysis, output):
    rows = analysis["diagnostics"]["cross_route_transfer"]
    fig, axes = plt.subplots(2, 4, figsize=(12.4, 6.2), layout="constrained")
    cmap = plt.get_cmap("viridis").copy()
    cmap.set_bad("#e9e9e9")
    for i, painter in enumerate(PAINTERS):
        for j, (kind, condition) in enumerate(
            (
                ("linear", "artist_free"),
                ("linear", "named"),
                ("rbf", "artist_free"),
                ("rbf", "named"),
            )
        ):
            ax = axes[i, j]
            values = np.full((3, 3), np.nan)
            for source, route in enumerate(ROUTES):
                for target, other in enumerate(ROUTES):
                    if route != other:
                        row = one(
                            rows,
                            painter_id=painter,
                            source_route=route,
                            target_route=other,
                            condition=condition,
                        )
                        values[source, target] = row["kernels"][kind]["pooled_threshold_metrics"][
                            "balanced_accuracy"
                        ]
            shown = ax.imshow(values, vmin=0.4, vmax=1, cmap=cmap)
            for (source, target), value in np.ndenumerate(values):
                ax.text(
                    target,
                    source,
                    "—" if np.isnan(value) else f"{value:.2f}",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if value < 0.68 else "#222222",
                )
            ax.set_xticks(range(3), [SHORT_ROUTES[r] for r in ROUTES], rotation=35, ha="right")
            ax.set_yticks(range(3), [SHORT_ROUTES[r] for r in ROUTES])
            ax.set_title(kind.upper() + " · " + ("free" if condition == "artist_free" else "named"))
            ax.set_xlabel("Test route" if i == 1 else "")
            ax.set_ylabel(PAINTER_NAMES[painter] + " · train route")
    fig.colorbar(
        shown,
        ax=axes.ravel().tolist(),
        shrink=0.8,
        pad=0.025,
        label="Pooled fixed-threshold balanced accuracy",
    )
    fig.suptitle(
        "Cross-route detection with disjoint reference works and content briefs\n"
        "Six fixed folds; diagonal transfer not part of this diagnostic",
        fontsize=12,
    )
    _save(fig, output, "cross_route_detection")


def _coordinate_weights(analysis, output):
    rows = analysis["metrics"]["trace_contributions"]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.9), layout="constrained")
    for i, painter in enumerate(PAINTERS):
        row = one(
            rows,
            pipeline="primary512",
            metric_view="original31",
            painter_id=painter,
            route=ROUTES[0],
            condition="named",
        )
        domain = one(row["domains"], domain="reference")
        bottom = 0
        for family, color in zip(FAMILIES, FAMILY_COLORS):
            fraction = one(domain["families"], family=family)["fraction"]
            axes[0].bar(i, fraction, bottom=bottom, color=color, width=0.57)
            axes[0].text(
                i,
                bottom + fraction / 2,
                f"{100 * fraction:.1f}%",
                color="white",
                va="center",
                ha="center",
                fontsize=10,
            )
            bottom += fraction
    axes[0].set(
        xticks=range(2),
        xticklabels=[PAINTER_NAMES[p] for p in PAINTERS],
        ylabel="Share of original total trace",
        ylim=(0, 1),
        title="Reference family weighting",
    )
    axes[0].legend(
        handles=[Patch(facecolor=c, label=f.title()) for f, c in zip(FAMILIES, FAMILY_COLORS)],
        loc="lower left",
        bbox_to_anchor=(0, 1.01),
        frameon=False,
        fontsize=8,
    )
    development = one(analysis["metrics"]["development_correlations"], pipeline="primary512")
    shown = axes[1].imshow(development["correlation"], vmin=-1, vmax=1, cmap="RdBu_r")
    for location in (10.5, 18.5):
        axes[1].axvline(location, color="#333333", linewidth=0.7)
        axes[1].axhline(location, color="#333333", linewidth=0.7)
    axes[1].set(
        xticks=(0, 10, 18, 30),
        yticks=(0, 10, 18, 30),
        xticklabels=(1, 11, 19, 31),
        yticklabels=(1, 11, 19, 31),
        xlabel="Feature index",
        ylabel="Feature index",
        title="Development correlations",
    )
    fig.colorbar(
        shown, ax=axes[1], fraction=0.045, label="Equal-painter-weighted Pearson correlation"
    )
    fig.suptitle(
        "Primary 512: coordinate counts do not equal conceptual information\n"
        "Correlation and trace weights describe this representation, not validated style",
        fontsize=12,
    )
    _save(fig, output, "coordinate_weights")


def _md_table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *("| " + " | ".join(str(value) for value in row) + " |" for row in rows),
        ]
    )


def _markdown(analysis, table_manifest, digest):
    metric = analysis["metrics"]
    primary = select(metric["prompt_contrasts"], pipeline="primary512", metric_view="original31")
    summary_rows = []
    for painter in PAINTERS:
        for route in ROUTES:
            value = one(primary, painter_id=painter, route=route)
            ratios = value["generated_decomposition_ratios"]
            summary_rows.append(
                (
                    PAINTER_NAMES[painter],
                    ROUTE_NAMES[route],
                    f"{value['energy_change']:+.4f}",
                    f"{ratios['total_trace']:.3f}",
                    f"{ratios['within_brief']:.3f}",
                    f"{ratios['between_brief_means']:.3f}",
                )
            )
    no_texture = one(
        metric["cells"],
        painter_id=PAINTERS[0],
        route=ROUTES[0],
        condition="named",
        pipeline="primary512",
        metric_view="no_texture19",
    )["trace_ratio"]
    flip = one(
        metric["prompt_contrasts"],
        painter_id=PAINTERS[0],
        route=ROUTES[0],
        pipeline="resolution256",
        metric_view="no_texture19",
    )["energy_change"]
    within = one(primary, painter_id=PAINTERS[1], route=ROUTES[2])[
        "generated_decomposition_ratios"
    ]["within_brief"]
    matching = select(metric["specificity"], pipeline="primary512", metric_view="original31")
    specificity_rows = []
    for route in ROUTES:
        free, named = (one(matching, route=route, condition=c) for c in ("artist_free", "named"))
        specificity_rows.append(
            (
                ROUTE_NAMES[route],
                f"{free['interaction_terms']['energy']:+.4f}",
                f"{named['interaction_terms']['energy']:+.4f}",
                f"{free['identical_payload_placebo']['energy']:.4f}",
            )
        )
    transfer_rows = []
    for kind in ("linear", "rbf"):
        for condition in ("artist_free", "named"):
            values = [
                r["kernels"][kind]["pooled_threshold_metrics"]["balanced_accuracy"]
                for r in select(
                    analysis["diagnostics"]["cross_route_transfer"], condition=condition
                )
            ]
            transfer_rows.append((kind.upper(), condition, f"{min(values):.3f}–{max(values):.3f}"))
    influence_rows = []
    for painter in PAINTERS:
        for route in ROUTES:
            selected = select(metric["reference_influence"], painter_id=painter, route=route)
            for kind in ("work", "content_class", "source_id"):
                rows = select(selected, deletion_kind=kind)
                values = [r["energy_change"] for r in rows if r["status"] == "descriptive"]
                influence_rows.append(
                    (
                        PAINTER_NAMES[painter],
                        SHORT_ROUTES[route],
                        kind,
                        f"{min(values):+.4f} to {max(values):+.4f}" if values else "unavailable",
                        sum(r["status"] == "unavailable" for r in rows),
                    )
                )
    timing_rows = []
    for endpoint in analysis["original_endpoints"]:
        rows = select(analysis["timing"]["contrasts"], endpoint_index=endpoint["endpoint_index"])
        available = [r["estimate"] for r in rows if r["status"] == "descriptive"]
        timing_rows.append(
            (
                endpoint["endpoint_index"],
                PAINTER_NAMES[endpoint["painter_id"]],
                SHORT_ROUTES[endpoint["route"]],
                endpoint["before"] + " → " + endpoint["after"],
                f"{min(available):+.4f} to {max(available):+.4f}",
                f"{min(r['pairs'] for r in rows)}–{max(r['pairs'] for r in rows)}",
            )
        )
    original_rows = [
        (
            r["endpoint_index"],
            PAINTER_NAMES[r["painter_id"]],
            SHORT_ROUTES[r["route"]],
            r["before"] + " → " + r["after"],
            f"{r['estimate']:+.4f}",
            f"{r['holm_p']:.5g}",
        )
        for r in analysis["original_endpoints"]
    ]
    csv_rows = [(f"[{name}.csv]({name}.csv)", count) for name, count in table_manifest]
    auc_example = [
        one(
            analysis["diagnostics"]["cross_route_transfer"], painter_id=PAINTERS[0],
            source_route=ROUTES[1], target_route=ROUTES[2], condition=condition,
        )["kernels"]["linear"]
        for condition in ("artist_free", "named")
    ]
    return (
        "\n\n".join(
            [
                "# Painter-distribution methodology revision: retained-data results",
                "Run `pdrv1-numeric-20260907`. These are **post-result descriptive "
                "diagnostics** of the "
                "completed 70-reference/1,006-generation study. The original eight sharp-null "
                "prompt tests "
                "remain unchanged. No new images, pixel measurements, population confidence "
                "intervals, "
                "or confirmatory tests are introduced.",
                "The revision supports a narrower account: painter naming changes finite feature "
                "distributions, often reducing differences between content briefs. The "
                "direction and "
                "magnitude of some effects depend on representation and reference choices. The "
                "evidence "
                "does not identify perceptual style diversity or eliminate geometry and capture "
                "confounding.",
                "## Results that change the interpretation",
                f"Removing texture makes Nano Banana 2 Monet's primary named/original trace ratio "
                f"**{no_texture:.3f}**, above one. Its 256-pixel/no-texture named-minus-free "
                f"energy is "
                f"**{flip:+.4f}**, a direction reversal. FLUX retains negative energy changes "
                f"across "
                "the fixed views and pipelines. Sensitivity variants are related summaries, not "
                "independent confirmations, and no new primary metric is selected.",
                f"All primary total named/free trace ratios are below one, while OAuth Cézanne's "
                f"within-brief ratio is **{within:.3f}**. Lower aggregate variation therefore "
                f"does not "
                "mean lower repeat-to-repeat variation for every fixed brief. Three repetitions "
                "per "
                "brief support empirical decomposition, not unbiased population variance "
                "components.",
                _md_table(
                    (
                        "Painter",
                        "Route",
                        "Energy change",
                        "Total trace ratio",
                        "Within brief",
                        "Between brief means",
                    ),
                    summary_rows,
                ),
                "![Fixed metric and processing sensitivities](plots/metric_sensitivity.png)",
                "The four panels have different metric units and independent color scales. "
                "Negative "
                "values mean lower energy to the same finite reference distribution; absolute "
                "magnitudes should not be ranked across panels. Every cell uses the unchanged "
                "development scale before its declared coordinate omission or family weighting.",
                "![Trace decomposition and component ratios](plots/variance_decomposition.png)",
                "Trace equals within-brief trace plus between-brief trace within content plus "
                "between-content trace. Original paintings have no brief labels and are decomposed "
                "only into within/between content. Energy includes twice the cross-domain mean "
                "distance minus both within-domain mean distances; those terms are exported "
                "separately.",
                "## Reference influence and development scaling",
                "Leave-one-work and source-proxy deletions retain the original content masses. "
                "Deleting a content class renormalizes the remaining masses and changes the "
                "target. "
                "These ranges summarize prescribed deletions; they are not confidence intervals. "
                "A source group is an exact recorded collection-ID set, including combined IDs; "
                "it is not a verified photographic capture workflow.",
                _md_table(
                    ("Painter", "Route", "Deletion", "Energy-change range", "Unavailable"),
                    influence_rows,
                ),
                "Development correlations and all four leave-one-development-painter IQR refits "
                "are exported. Refits use development works only. They change a measurement "
                "choice; "
                "they do not validate its artistic meaning. The original 31-coordinate view "
                "assigns repeated weight to some derived summaries and substantial variance to "
                "texture.",
                "![Reference weighting and development correlations](plots/coordinate_weights.png)",
                "## Painter-label controls and specificity",
                "The double contrast is E(A,A) + E(B,B) − E(A,B) − E(B,A), where the first index "
                "denotes the generated prompt painter and the second denotes the reference "
                "painter. "
                "Both reference-only and generated-only within-distribution terms cancel. All "
                "three content classes receive mass one third. Negative interaction favors own "
                "painter pairing in this feature geometry; it is not calibrated painter "
                "recognition.",
                _md_table(
                    (
                        "Route",
                        "Artist-free interaction",
                        "Named interaction",
                        "Identical-free V-energy",
                    ),
                    specificity_rows,
                ),
                "For each route, 72 cross-label brief/repetition pairs have verified identical "
                "artist-free payloads: 216 pairs in total. Their separate collected distributions "
                "provide a post-result collection-label diagnostic. The nonzero V-energies have "
                "finite-sample baselines and are neither equivalence margins nor significance "
                "thresholds.",
                "![Painter interaction and identical-payload controls](plots/specificity.png)",
                "## Coverage and detection controls",
                "Coverage is reported for k=1/3/5, all available images, uniform samples, and "
                "samples matching reference content counts at half and full reference N. "
                "The 100 fixed draws and per-reference radii/hits are retained. Uniform sample "
                "size matching does not match the painter-specific content composition.",
                "![Coverage and held-out real controls](plots/coverage_controls.png)",
                "The lower panels use identical anchors for disjoint real queries and generated "
                "queries at identical class counts. Those anchor panels differ from the upper "
                "panels. Full-panel matched query N is 38 Monet / 32 Cézanne; reduced "
                "anchor and query N is 18 Monet / 15 Cézanne. Their 5–95% draw ranges "
                "reuse the finite panel and are not population "
                "intervals. Coverage can saturate at larger k; coincident values at saturation "
                "do not establish distributional or perceptual equivalence. For OAuth Monet, "
                "the named/free coverage direction at k=3 changes between all-available and "
                "class-count-matched sampling; all conditions are retained in the tables.",
                _md_table(
                    ("Kernel", "Condition", "Cross-route balanced-accuracy range"), transfer_rows
                ),
                "![Directed cross-route detection](plots/cross_route_detection.png)",
                "Transfer uses the fixed scaler, linear/RBF kernel, ridge 0.01, six whole-brief "
                "folds and disjoint original works. Each cell reports pooled fixed-threshold "
                "balanced accuracy; AUC is retained per fold, with its arithmetic mean labeled "
                "descriptive. Cross-route fixed-threshold balanced accuracy is lower for "
                "named than artist-free conditions in all 12 directions for each kernel. "
                "This is a threshold-performance result, not a uniform decline in ranking "
                "discrimination: mean within-fold AUC can rise. Threshold calibration and "
                "domain shift can contribute. "
                "Cross-route success alone would not isolate painter style because nuisance "
                "properties may transfer too.",
                "For example, Monet FLUX→OAuth linear transfer has mean within-fold AUC "
                f"{auc_example[0]['mean_fold_auc']:.4f} → {auc_example[1]['mean_fold_auc']:.4f} "
                "from artist-free to named, while its fixed-threshold balanced accuracy is "
                f"{auc_example[0]['pooled_threshold_metrics']['balanced_accuracy']:.4f} → "
                f"{auc_example[1]['pooled_threshold_metrics']['balanced_accuracy']:.4f}. "
                "No pooled AUC is reported across the differently fitted fold scores.",
                "The square metadata rule perfectly distinguishes all paid-route outputs from "
                "these originals: the paid outputs are square, and no reference is square. "
                "This is not proof that the feature classifier uses shape. Capture-workflow "
                "holdout remains explicitly unavailable. Original content coding is from one "
                "maintainer LLM; generated content labels describe intended prompts, not "
                "independently verified adherence. Descriptor associations do not correct these "
                "gaps.",
                "## Execution sensitivities and preserved inference",
                "The five timing views retain all selected images or exclude component-crossing "
                "groups, groups spanning over 120 seconds, technical-retry groups, or boundary "
                "plus retry groups. Spans refer to initial randomized groups; OAuth groups have "
                "three conditions. These post-result exclusions do not establish no interference "
                "or transform assigned windows into independent sessions.",
                _md_table(
                    (
                        "Endpoint",
                        "Painter",
                        "Route",
                        "Contrast",
                        "Five-view estimate range",
                        "Pairs",
                    ),
                    timing_rows,
                ),
                "The following adjusted p-values belong exclusively to the original frozen "
                "eight-endpoint family. They test the conditional sharp null of no "
                "prompt-assignment "
                "effect on availability and measured features under the fixed slot policy and "
                "no-interference assumption. They do not test original/generated population "
                "equality, "
                "reduced variance, perceptual similarity, or a mean-effect confidence interval.",
                _md_table(
                    (
                        "Endpoint",
                        "Painter",
                        "Route",
                        "Original contrast",
                        "Estimate",
                        "Original Holm p",
                    ),
                    original_rows,
                ),
                "All initial dispositions and the exact technical retry are preserved. OAuth "
                "reported-quality differences remain part of the observed service outcome; "
                "removing treatment-associated low/medium quality differences would not "
                "automatically "
                "isolate a fixed-rendering semantic effect.",
                "## Reproducibility, tables and remaining validation",
                "All figures and CSV tables below derive solely from the sealed revision "
                "[analysis JSON](../../../" + INPUT.as_posix() + "). List memberships and exact "
                "payload checks remain there. CSV list-length columns end in `.n`; blank scalar "
                "fields mean unavailable/not applicable, never zero. Coverage draw tables retain "
                "all prescribed numeric draw outcomes without duplicating image payloads.",
                "Input SHA-256: `" + digest + "`.",
                _md_table(("Table", "Rows"), csv_rows),
                "The [revision "
                "protocol](../../../studies/painter_distribution_revision_v1/PROTOCOL.md) "
                "declared this bounded diagnostic grid after the original results and before "
                "this full package was computed. The original 14 primary energy/trace/IQR cells "
                "and six corresponding original-view prompt changes reproduce within the recorded "
                "bridge tolerance; the original calculation itself reproduces exactly. The "
                "remaining two original generic/detailed endpoints are preserved and replayed "
                "by the timing all-selected view.",
                "This scope makes no new generation call. The next scientific requirements "
                "for a stronger claim are reference/source/geometry common support and independent "
                "human assessment of both painter resemblance and variation across multiple image "
                "sets. Those validations have not occurred. A new encoder would be complementary "
                "measurement, not automatic ground truth. The methodological review and follow-up "
                "checks were maintainer-run LLM reviews, not independent human or institutional "
                "peer review.",
                "Numerical replay, pixel-to-feature replay and service regeneration are separate "
                "promises. These compact artifacts support numerical replay; ignored image bytes "
                "and the environment are needed for pixel replay, and mutable service aliases "
                "prevent a guarantee of exact regeneration.",
            ]
        )
        + "\n"
    )


def render(root, output_dir):
    """Render a caller-controlled preview/staging directory; return paths relative to it."""
    root, output = Path(root), Path(output_dir)
    raw = (root / INPUT).read_bytes()
    analysis = json.loads(raw)
    output.mkdir(parents=True, exist_ok=True)
    plot_dir = output / "plots"
    plot_dir.mkdir(exist_ok=True)
    tables = _tables(analysis)
    paths = []
    for name, rows in sorted(tables.items()):
        _csv(output / (name + ".csv"), rows)
        paths.append(name + ".csv")
    with plt.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "svg.hashsalt": "pdrv1-report-20260907",
            "svg.fonttype": "path",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    ):
        for function, name in (
            (_metric_sensitivity, "metric_sensitivity"),
            (_variance_decomposition, "variance_decomposition"),
            (_specificity_plot, "specificity"),
            (_coverage_controls, "coverage_controls"),
            (_cross_route_detection, "cross_route_detection"),
            (_coordinate_weights, "coordinate_weights"),
        ):
            function(analysis, plot_dir)
            paths.extend(("plots/" + name + ".png", "plots/" + name + ".svg"))
    manifest = [(name, len(rows)) for name, rows in sorted(tables.items())]
    (output / "REPORT.md").write_text(
        _markdown(analysis, manifest, hashlib.sha256(raw).hexdigest()), encoding="utf-8"
    )
    paths.append("REPORT.md")
    return sorted(paths)
