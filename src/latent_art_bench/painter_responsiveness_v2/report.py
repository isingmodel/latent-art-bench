"""Deterministic presentation of supplied v2 numeric results, with no new analysis.

Full query predictions, exact split membership and long reference weight vectors
remain in their sealed JSON inputs. CSVs preserve every corresponding summary row.
No image files, service endpoints or external data are read by these renderers.
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

ROUTES = ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
ROUTE_LABELS = dict(zip(ROUTES, ("Nano Banana 2", "FLUX.2 Max", "OAuth")))
PAINTERS = ("claude_monet", "paul_cezanne")
PAINTER_LABELS = dict(zip(PAINTERS, ("Monet", "Cézanne")))
ARMS = ("free", "generic", "monet", "cezanne")
ARM_LABELS = dict(zip(ARMS, ("Artist-free", "Generic style", "Monet", "Cézanne")))
PIPELINES = ("primary512", "resolution256", "jpeg90_512")
VIEWS = ("original31", "color", "spatial", "texture", "no_texture19")
BLUE, ORANGE = "#246a9a", "#c05b20"
RC = {"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
      "axes.labelsize": 9, "svg.hashsalt": "painter-responsiveness-v2",
      "figure.facecolor": "white", "savefig.facecolor": "white"}


def _flat(row, prefix=""):
    result = {}
    for key, value in row.items():
        name = prefix + key
        if isinstance(value, dict):
            result.update(_flat(value, name + "."))
        else:
            result[name] = value
    return result


def _csv(path, rows):
    rows = [_flat(r) for r in rows]
    fields = sorted({k for r in rows for k in r}) or ["status"]
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False, sort_keys=True, allow_nan=False)
                         if isinstance(v, (list, dict)) else v for k, v in row.items()}
                        for row in rows)


def _clean(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)


def _save(fig, directory, name):
    paths = []
    for extension in ("png", "svg"):
        path = directory / "plots" / f"{name}.{extension}"
        metadata = {"Software": "LatentArtBench"} if extension == "png" else {
            "Date": None, "Creator": "LatentArtBench"}
        fig.savefig(path, dpi=180, bbox_inches="tight", metadata=metadata)
        paths.append(path.relative_to(directory).as_posix())
    plt.close(fig)
    return paths


def _start(output_dir):
    path = Path(output_dir)
    if path.exists() and any(path.iterdir()):
        raise ValueError("render into an empty directory; never overwrite report artifacts")
    path.mkdir(parents=True, exist_ok=True)
    (path / "plots").mkdir(exist_ok=True)
    return path


def _publish(directory, tables, text, figures):
    paths = []
    for name, rows in sorted(tables.items()):
        _csv(directory / f"{name}.csv", rows)
        paths.append(name + ".csv")
    for name, figure in figures:
        paths.extend(_save(figure, directory, name))
    text += ["", "## Complete numeric tables", "", "| Table | Rows |", "| --- | ---: |"]
    text += [f"| [{name}.csv]({name}.csv) | {len(rows)} |" for name, rows in sorted(tables.items())]
    text += ["", "Empty tables mean unavailable results. CSV list fields retain JSON arrays. "
             "Numbers are not recomputed by this renderer. The publication receipt binds input "
             "JSON and all report bytes; frozen numerical and report replay are separate from "
             "empirical validation. Reviews, unless explicitly identified otherwise, are "
             "maintainer-run LLM reviews, not independent human or institutional reviews.", ""]
    with (directory / "REPORT.md").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(text))
    return sorted(paths + ["REPORT.md"])


def _retrieval_figure(diagnostic):
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.1), sharey=True, layout="constrained")
    labels = [f"{ROUTE_LABELS[r]} / {PAINTER_LABELS[p]}" for r in ROUTES for p in PAINTERS]
    for ax, scope, title, chance in zip(axes, ("all_briefs", "same_content"),
                                      ("All 24 scene descriptions", "Within broad content class"),
                                      (1 / 24, 1 / 8)):
        rows = {(c["route"], c["painter_id"]): c for c in diagnostic["cells"]
                if (c["pipeline"], c["view"], c["candidate_scope"])
                == ("primary512", "original31", scope)}
        for y, key in enumerate((r, p) for r in ROUTES for p in PAINTERS):
            row = rows[key]
            values = [row[k]["top1_accuracy"] * 100 for k in ("before", "after")]
            ax.plot(values, [y, y], color="#a7afb5", linewidth=1.5)
            ax.scatter(values[0], y, facecolors="none", edgecolors=BLUE, linewidths=1.3,
                       s=58, label="Artist-free" if y == 0 else None)
            ax.scatter(values[1], y, color=ORANGE, s=19, marker="s",
                       label="Painter named" if y == 0 else None)
        ax.axvline(100 * chance, color="#656565", linestyle=":", linewidth=1)
        ax.set(title=title, xlabel="Top-1 retrieval accuracy (%)", xlim=(-2, 102))
        ax.grid(axis="x", alpha=0.15)
        _clean(ax)
    axes[0].set_yticks(range(6), labels)
    axes[0].invert_yaxis()
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2,
                   frameon=False, fontsize=8)
    return fig


def _retrieval_sensitivity(diagnostic):
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 5.0), layout="constrained")
    rows = {(c["route"], c["painter_id"], c["pipeline"], c["view"]): c
            for c in diagnostic["cells"] if c["candidate_scope"] == "all_briefs"}
    values = [100 * c["named_minus_free"]["top1_accuracy"] for c in rows.values()]
    bound = max([abs(v) for v in values] + [0.1])
    for col, route in enumerate(ROUTES):
        for row, painter in enumerate(PAINTERS):
            ax = axes[row, col]
            x = np.array([[100 * rows[route, painter, pipeline, view]["named_minus_free"][
                "top1_accuracy"] for view in VIEWS] for pipeline in PIPELINES])
            im = ax.imshow(x, cmap="RdBu", vmin=-bound, vmax=bound, aspect="auto")
            for y in range(3):
                for c in range(5):
                    ax.text(c, y, f"{x[y, c]:+.1f}", ha="center", va="center", fontsize=8,
                            color="white" if abs(x[y, c]) > bound * 0.60 else "#161616")
            ax.set_title(f"{ROUTE_LABELS[route]} / {PAINTER_LABELS[painter]}")
            ax.set_xticks(range(5), ("All 31", "Color", "Spatial", "Texture", "No texture"),
                          rotation=35, ha="right")
            ax.set_yticks(range(3), ("512", "256", "JPEG90"))
    fig.colorbar(im, ax=axes, shrink=0.78, label="Named − artist-free accuracy (percentage points)")
    return fig


def render_diagnostic(value, output_dir):
    """Render all diagnostic summary cells; detailed prediction records stay in JSON."""
    diagnostic = value["diagnostics"]
    directory = _start(output_dir)
    primary = [c for c in diagnostic["cells"] if
               (c["pipeline"], c["view"], c["candidate_scope"])
               == ("primary512", "original31", "all_briefs")]
    primary.sort(key=lambda c: (ROUTES.index(c["route"]), PAINTERS.index(c["painter_id"])))
    changes = [c["named_minus_free"]["top1_accuracy"] for c in primary]
    text = [
        "# Scene retrieval under painter naming", "",
        "This post-result diagnostic tests whether contraction of saved feature vectors also "
        "means poorer identification of repeated scene descriptions. It uses the already exposed "
        "generated-image vectors, with no new images or human judgments.", "",
        f"In the six primary route/painter comparisons, top-1 accuracy increased in "
        f"{sum(x > 0 for x in changes)}, decreased in {sum(x < 0 for x in changes)}, and was "
        f"unchanged in {sum(x == 0 for x in changes)} under naming. The table preserves both "
        "directions. Lower between-scene trace alone does not imply poorer repeat retrieval: "
        "uniform contraction preserves nearest-centroid geometry, and less within-scene noise "
        "can improve retrieval.", "",
        "| Route / painter | Free accuracy | Named accuracy | Free midrank | Named midrank | "
        "Named/free between trace |", "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for c in primary:
        ratio = c["named_free_between_brief_trace_ratio"]
        ratio_text = f"{ratio:.4f}" if ratio is not None else "unavailable"
        text.append(f"| {ROUTE_LABELS[c['route']]} / {PAINTER_LABELS[c['painter_id']]} | "
                    f"{c['before']['top1_accuracy']:.1%} | {c['after']['top1_accuracy']:.1%} | "
                    f"{c['before']['mean_midrank']:.3f} | {c['after']['mean_midrank']:.3f} | "
                    f"{ratio_text} |")
    text += ["", "![Primary retrieval accuracy](plots/retrieval_accuracy.png)", "",
             "Each query is held out by repetition; every candidate centroid uses only its other "
             "two repetitions. Training and querying use the same condition and the unchanged "
             "development feature scale. Dotted lines show 1/24 and 1/8 chance levels. "
             "Within-class retrieval removes broad prompt-class identification as an explanation "
             "for success; those classes are not independently verified visual annotations.", "",
             "![Feature-view and processing sensitivity](plots/retrieval_sensitivity.png)", "",
             "The sensitivity figure shows all-24-scene accuracy changes. The full 450-row table "
             "also includes within-class pooled and class-specific controls, midranks, all tie "
             "summaries and scope-matched traces. Positive accuracy changes favor named repeat "
             "retrieval. This is scene-associated feature geometry, not established prompt "
             "adherence, painter style, human perception or a causal mechanism.", "",
             "Exact computed-distance ties use lexical brief IDs for deterministic top-1 output. "
             "Fractional tie credit, best/worst ranks and midranks retain the ambiguity. The "
             "immutable diagnostic JSON preserves every prediction and exact split via query "
             "and prediction-set IDs; those large tables are not duplicated here.", "",
             "The simulation table is prospective sensitivity under retained noise proxies. "
             "Its effect grid is hypothetical; power and interval width are conditional on "
             "the stated noise and availability assumptions, not guarantees or perceptual margins."]
    noise = value.get("retained_noise", {})
    tables = {"retrieval_comparisons": diagnostic["cells"],
              "simulation": value.get("simulation", {}).get("results", []),
              "noise_groups": noise.get("groups", []),
              "noise_marginal_variances": [dict(arm=k, variance=v) for k, v in
                                           noise.get("marginal_variances", {}).items()]}
    with plt.rc_context(RC):
        return _publish(directory, tables, text, [
            ("retrieval_accuracy", _retrieval_figure(diagnostic)),
            ("retrieval_sensitivity", _retrieval_sensitivity(diagnostic)),
        ])


def _jitter(identity):
    return (int(hashlib.sha256(identity.encode()).hexdigest()[:8], 16) / (2**32 - 1) - 0.5) * 0.15


def _arms(value):
    fig, ax = plt.subplots(figsize=(7.5, 4.2), layout="constrained")
    rows = [r for r in value["generated_chroma"] if r["pipeline"] == "primary512"
            and r["status"] == "measured"]
    for i, arm in enumerate(ARMS):
        means = []
        for polarity, dx, color in (("muted", -0.18, BLUE), ("vivid", 0.18, ORANGE)):
            selected = [r for r in rows if r["arm"] == arm and r["polarity"] == polarity]
            ax.scatter([i + dx + _jitter(r["request_id"]) for r in selected],
                       [r["value"] for r in selected], s=14, alpha=0.60, color=color,
                       label=polarity.title() if i == 0 else None)
            means.append(next(r["mean"] for r in value["primary"]["arm_means"]
                              if r["arm"] == arm and r["polarity"] == polarity))
        if all(m is not None for m in means):
            ax.plot([i - 0.18, i + 0.18], means, color="#252525", marker="D", markersize=4)
    ax.set_xticks(range(4), [ARM_LABELS[a] for a in ARMS])
    ax.set_ylabel("Median chroma (primary-development IQR units)")
    ax.set_title("Muted and vivid instructions")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.15)
    _clean(ax)
    return fig


def _interactions(value):
    fig, ax = plt.subplots(figsize=(7.0, 2.7), layout="constrained")
    rows = value["primary"].get("primary")
    if not rows:
        ax.text(0.5, 0.5, "Primary inference withheld\nMissing planned measurements", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig
    for i, row in enumerate(rows):
        interval = row["family_interval"]
        if interval is not None:
            ax.plot(interval, [i, i], color=BLUE, linewidth=2)
        ax.scatter(row["estimate"], i, color=BLUE, s=40, marker="o" if interval else "x")
        if interval is None:
            ax.annotate("Interval unavailable", (row["estimate"], i), xytext=(6, 6),
                        textcoords="offset points", fontsize=8)
    ax.axvline(0, color="#656565", linestyle=":", linewidth=1)
    ax.set_yticks(range(2), ("Monet − generic", "Cézanne − generic"))
    ax.set_ylim(1.7, -0.7)
    ax.set_xlabel("Difference in vivid-minus-muted response (development IQR units)")
    ax.set_title("Two primary interactions and simultaneous intervals")
    _clean(ax)
    return fig


def _coordinates(value):
    fig, ax = plt.subplots(figsize=(6.5, 8.2), layout="constrained")
    rows = value["all_coordinate_responses"]["coordinates"]
    if rows is None:
        ax.text(0.5, 0.5, "Coordinate interactions withheld\nIncomplete primary grid", ha="center",
                va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return fig
    x = np.array([[r["interactions"][a + "_minus_generic"] for a in ("monet", "cezanne")]
                  for r in rows])
    bound = max(float(np.abs(x).max()), 0.01)
    im = ax.imshow(x, cmap="RdBu", vmin=-bound, vmax=bound, aspect="auto")
    ax.set_yticks(range(len(rows)), [r["feature_name"].replace("_", " ") for r in rows], fontsize=8)
    ax.set_xticks((0, 1), ("Monet − generic", "Cézanne − generic"))
    for line in (10.5, 18.5):
        ax.axhline(line, color="white", linewidth=1.5)
    ax.set_title("Feature interactions: descriptive point estimates")
    fig.colorbar(im, ax=ax, shrink=0.75, label="Difference in response (development IQR units)")
    return fig


def _reference(value):
    context = value["reference_context"]
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.4), sharey=True, sharex=True,
                             layout="constrained")
    labels = ("Originals: empirical", "Originals: equal class", "Generic: muted", "Generic: vivid",
              "Named: muted", "Named: vivid")
    for ax, painter, arm in zip(axes, PAINTERS, ("monet", "cezanne")):
        rows = []
        for weighting in ("empirical_reference_mixture", "equal_broad_class"):
            envelope = next(r for r in context["envelopes"] if r["pipeline"] == "primary512"
                            and r["painter_id"] == painter and r["weighting"] == weighting)
            rows.append((envelope.get("summary"), "#414141"))
        for selected_arm in ("generic", arm):
            for polarity, color in (("muted", BLUE), ("vivid", ORANGE)):
                comparison = next(r for r in context["comparisons"] if r["pipeline"] == "primary512"
                                  and r["painter_id"] == painter and r["arm"] == selected_arm
                                  and r["polarity"] == polarity
                                  and r["reference_weighting"] == "equal_broad_class")
                rows.append((comparison.get("generated_summary"), color))
        for i, (summary, color) in enumerate(rows):
            if summary is None:
                ax.text(0.5, i, "Unavailable", transform=ax.get_yaxis_transform(), ha="center")
            else:
                low, mid, high = summary["quantiles_10_50_90"]
                ax.plot([low, high], [i, i], color=color, linewidth=2)
                ax.scatter(mid, i, color=color, s=30)
        ax.set(title=PAINTER_LABELS[painter], xlabel="Chroma (primary-development IQR units)")
        ax.grid(axis="x", alpha=0.15)
        _clean(ax)
    axes[0].set_yticks(range(6), labels)
    axes[0].set_ylim(5.6, -0.6)
    return fig


def render_experiment(value, output_dir):
    """Render finite-template estimates without upgrading digital or human claim scope."""
    directory = _start(output_dir)
    primary, collection = value["primary"], value.get("collection", {})
    covariance = primary.get("primary_covariance")
    names = ("monet_minus_generic", "cezanne_minus_generic")
    tables = {
        "generated_chroma": value["generated_chroma"],
        "reference_chroma": value["reference_chroma"],
        "availability": primary["availability"], "cell_means": primary["cells"],
        "arm_means": primary["arm_means"], "primary": primary.get("primary") or [],
        "responses": primary.get("responses", []),
        "secondary_named_minus_free": primary.get("secondary_named_minus_free", []),
        "generic_minus_free": primary.get("generic_minus_free", []),
        "complete_block_survivors": primary.get("complete_block_descriptive", {}).get(
            "templates", []),
        "computational_interpretation": value["computational_interpretation"].get("painters", []),
        "primary_covariance": [dict(contrast=names[i], **dict(zip(names, row)))
                               for i, row in enumerate(covariance or [])],
        "processing_primary": [dict(pipeline=p, **row) for p, result in
                               value["processing_sensitivity"].items()
                               for row in result.get("primary") or []],
        "coordinate_responses": value["all_coordinate_responses"]["coordinates"] or [],
        "reference_envelopes": [{k: v for k, v in r.items() if k not in ("image_ids", "weights")}
                                for r in value["reference_context"]["envelopes"]],
        "reference_comparisons": [{k: v for k, v in r.items() if k not in
                                   ("request_ids", "unavailable_request_ids", "generated_weights")}
                                  for r in value["reference_context"]["comparisons"]],
        "collection_slots": collection.get("slots", []),
        "transport_attempts": collection.get("per_attempt_transport", []),
        "transport_summary": [collection["transport_summary"]]
                             if "transport_summary" in collection else [],
    }
    text = [
        "# Computational painter-name responsiveness", "",
        f"Primary inference status: `{primary['status']}`. Collection status: "
        f"`{collection.get('status', 'not supplied')}`; stop reason: "
        f"`{collection.get('stop_reason') or 'none recorded'}`. All "
        f"{value['counts']['planned_images']} allocated images remain in the status tables. "
        "Measured counts by pipeline: "
        f"`{json.dumps(value['counts']['measured_by_pipeline'], sort_keys=True)}`.",
        "", value["claim_scope"], "",
        "![Muted and vivid chroma outputs](plots/arm_chroma.png)", "",
        "Dots are available primary512 outputs; deterministic horizontal jitter only separates "
        "overlapping points. Diamonds and connecting lines are the supplied equal-template arm "
        "means. Missing outputs are not replaced by central or neutral values.", "",
        "![Primary interaction intervals](plots/primary_interactions.png)", "",
        "The two primary interactions are named-minus-generic differences in vivid-minus-muted "
        "chroma response. Simultaneous intervals use the prespecified Bonferroni allocation; "
        "Holm-adjusted p-values are reported separately. The shared generic draws are reflected "
        "in the retained two-by-two covariance matrix. These are approximate fixed-template, "
        "repeated-generation intervals, not exact weak-null randomization inference.", "",
    ]
    if primary.get("primary"):
        text += ["| Contrast | Estimate | Simultaneous interval | Holm p |",
                 "| --- | ---: | --- | ---: |"]
        for row in primary["primary"]:
            interval = row["family_interval"]
            rendered = (f"[{interval[0]:.5f}, {interval[1]:.5f}]" if interval is not None
                        else "unavailable")
            p = f"{row['p_holm']:.5g}" if row["p_holm"] is not None else "unavailable"
            text.append(f"| {row['contrast']} | {row['estimate']:.5f} | {rendered} | {p} |")
        text += ["", "Control and named responses (nominal intervals; "
                 "not separate confirmations):", "",
                 "| Arm | Vivid − muted | Nominal interval |", "| --- | ---: | --- |"]
        for row in primary["responses"]:
            ci = row["nominal_interval"]
            interval = f"[{ci[0]:.5f}, {ci[1]:.5f}]" if ci is not None else "unavailable"
            text.append(f"| {ARM_LABELS[row['contrast']]} | {row['estimate']:.5f} | {interval} |")
        text += ["", "Computational classifications preserve opposite and unresolved findings:", ""]
        for row in value["computational_interpretation"]["painters"]:
            wording = ("smaller measured response; the named point response is positive"
                       if row["verdict"] == "smaller_positive_named_chroma_response"
                       else row["verdict"].replace("_", " "))
            text.append(f"- {ARM_LABELS[row['arm']]}: {wording}.")
    else:
        text += ["Primary inference is withheld because a planned primary measurement is missing. "
                 "Available outputs and reference comparisons are selected descriptions; they "
                 "do not recover the originally allocated treatment effect."]
    text += ["", "![All-coordinate interaction estimates](plots/coordinate_interactions.png)", "",
             value["all_coordinate_responses"]["scope"], "The chroma endpoint is the primary "
             "coordinate; the other point estimates do not add a family of significance tests. "
             "Processing sensitivity estimates and intervals are supplied separately in CSV, "
             "not treated as independent confirmations.", "",
             "![Digital original chroma context](plots/original_chroma_context.png)", "",
             "Points mark weighted medians; horizontal segments are empirical 10th–90th "
             "percentile ranges, **not confidence intervals**. Generated ranges use equal broad "
             "class mass. An incomplete stratum remains unavailable; any partially observed "
             "distribution is explicitly marked selected in the comparison table.", "",
             value["reference_context"]["scope"], "Exact work/request memberships and weights "
             "are preserved in the sealed JSON; compact CSVs retain every numerical comparison. "
             "The explicit instruction intervention tests a digital feature response. "
             "No human ratings have been supplied, and no learned model architecture "
             "is identified.", "",
             "Attempt-level transport timing, delivery geometry and reported quality are exported "
             "when supplied. Missing metadata remains missing, "
             "not an assertion of matching quality.",
             "", "Recorded inferential assumptions:", ""]
    text.extend("- " + assumption for assumption in primary["assumptions"])
    with plt.rc_context(RC):
        return _publish(directory, tables, text, [
            ("arm_chroma", _arms(value)), ("primary_interactions", _interactions(value)),
            ("coordinate_interactions", _coordinates(value)),
            ("original_chroma_context", _reference(value)),
        ])
