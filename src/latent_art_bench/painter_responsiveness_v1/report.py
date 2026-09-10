"""Deterministic presentation of saved responsiveness results; no numeric fitting."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROUTES = {"nano_banana_2": "Nano Banana 2", "flux_2_max": "FLUX.2 Max",
          "oauth_gpt_image_2": "OAuth"}
PAINTERS = {"claude_monet": "Monet", "paul_cezanne": "Cézanne"}
PIPELINES = {"primary512": "512", "resolution256": "256", "jpeg90_512": "JPEG 90"}
COLORS = ("#0072B2", "#D55E00", "#009E73")


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
    keys = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False, allow_nan=False,
                                            separators=(",", ":"))
                             if isinstance(value, (list, dict)) else value
                             for key, value in row.items()})


def _tables(result):
    diagnostic = result["diagnostics"]
    tables = {key: [] for key in (
        "brief_coordinates", "brief_summaries", "brief_memberships", "scope_summaries",
        "scope_coordinates", "scope_families", "cross_repeat_pairs",
        "reference_chroma_works", "reference_chroma_groups", "quality_groups",
        "simulation", "gate_checks", "reference_feasibility", "subject_label_inventory",
    )}
    for cell in diagnostic["cells"]:
        labels = {key: cell[key] for key in ("cell_id", "route", "painter_id")}
        for brief in cell["briefs"]:
            ids = dict(labels, brief_id=brief["brief_id"], content_class=brief["content_class"])
            tables["brief_summaries"].append(dict(ids, **{
                key: value for key, value in brief.items()
                if key not in ("before_mean", "after_mean", "mean_displacement")
            }))
            for i, name in enumerate(diagnostic["feature_names"]):
                tables["brief_coordinates"].append(dict(
                    ids, feature=name, before_mean=brief["before_mean"][i],
                    after_mean=brief["after_mean"][i],
                    mean_displacement=brief["mean_displacement"][i],
                ))
            for side, condition in (("before", "artist_free"), ("after", "named")):
                for repetition, image_id in zip(
                    brief["repetitions"], brief[side + "_image_ids"], strict=True
                ):
                    tables["brief_memberships"].append(dict(
                        ids, condition=condition, repetition=repetition, image_id=image_id))
        for scope in cell["scopes"]:
            ids = dict(labels, scope=scope["scope"])
            tables["scope_summaries"].append(dict(ids, **_flat({
                key: value for key, value in scope.items()
                if key not in ("coordinates", "families")
            })))
            tables["scope_coordinates"].extend(dict(ids, **r) for r in scope["coordinates"])
            tables["scope_families"].extend(dict(ids, **r) for r in scope["families"])
            for side, condition in (("before", "artist_free"), ("after", "named")):
                tables["cross_repeat_pairs"].extend(
                    dict(ids, condition=condition, **r)
                    for r in scope[side]["cross_repeat_pairs"])
    reference = diagnostic["reference_chroma"]
    tables["reference_chroma_works"] = [_flat(r) for r in reference["works"]]
    tables["reference_chroma_groups"] = [_flat(r) for r in reference["groups"]]
    tables["reference_feasibility"] = [_flat(reference["fine_content_feasibility"])]
    tables["subject_label_inventory"] = reference["subject_label_inventory"]
    tables["quality_groups"] = [_flat(r) for r in diagnostic["service_quality"]["groups"]]
    tables["simulation"] = [_flat(r) for r in result.get("simulation", {}).get("results", [])]
    tables["gate_checks"] = [dict(check=key, passed=value)
                             for key, value in result["gates"].get("checks", {}).items()]
    if result.get("factorial") is not None:
        tables["factorial"] = [_flat(result["factorial"])]
    return tables


def _scope(cell):
    matches = [s for s in cell["scopes"] if s["scope"] == "all_briefs"]
    if len(matches) != 1:
        raise ValueError("one all-brief scope required per cell")
    return matches[0]


def _label(cell):
    return ROUTES.get(cell["route"], cell["route"]) + " / " + PAINTERS.get(
        cell["painter_id"], cell["painter_id"])


def _save(fig, directory, name):
    paths = []
    for extension in ("png", "svg"):
        path = directory / "plots" / f"{name}.{extension}"
        metadata = ({"Software": "Painter responsiveness v1"} if extension == "png"
                    else {"Date": None, "Creator": "Painter responsiveness v1"})
        fig.savefig(path, dpi=180, bbox_inches="tight", metadata=metadata)
        paths.append(path.relative_to(directory).as_posix())
    plt.close(fig)
    return paths


def _variation(diagnostic):
    cells = diagnostic["cells"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True, layout="constrained")
    for ax, key, title, color in zip(
        axes, ("between_brief_trace", "cross_repeat_between_trace"),
        ("Empirical between-brief change", "Signed cross-repetition change"), COLORS, strict=False
    ):
        values = [_scope(cell)["changes"][key] for cell in cells]
        ax.barh(np.arange(len(cells)), values, color=color, height=0.65)
        ax.axvline(0, color="#444444", lw=0.8)
        ax.set_title(title, fontsize=12, pad=12)
        ax.set_xlabel("Named minus artist-free (scaled coordinate sum)")
        ax.set_yticks(np.arange(len(cells)), [_label(cell) for cell in cells])
        ax.grid(axis="x", alpha=0.2)
    axes[0].invert_yaxis()
    fig.suptitle("Equal brief weights; cross-repeat products are not identified latent variances",
                 fontsize=12)
    return fig


def _displacements(diagnostic):
    cells = diagnostic["cells"]
    values = np.asarray([_scope(cell)["displacement"]["grand_mean"] for cell in cells]).T
    bound = max(float(np.abs(values).max()), 1e-12)
    fig, ax = plt.subplots(figsize=(9, 10), layout="constrained")
    chart = ax.imshow(values, cmap="RdBu_r", vmin=-bound, vmax=bound, aspect="auto")
    ax.set_xticks(np.arange(len(cells)), [_label(cell) for cell in cells],
                  rotation=30, ha="right", fontsize=9)
    ax.set_yticks(np.arange(len(diagnostic["feature_names"])), diagnostic["feature_names"],
                  fontsize=9)
    for boundary in (10.5, 18.5):
        ax.axhline(boundary, color="#555555", lw=0.8)
    ax.set_title("All 31 coordinates: mean named-minus-free displacement\n"
                 "Every brief contributes equally; means do not measure variation", pad=14)
    fig.colorbar(chart, ax=ax, label="Fixed development-scale units", shrink=0.7)
    return fig


def _chroma(diagnostic):
    reference = diagnostic["reference_chroma"]
    groups = [g for g in reference["groups"] if g["level"] == "broad_content"]
    identities = sorted({(g["painter_id"], g["label"]) for g in groups})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    for i, pipeline in enumerate(PIPELINES):
        for j, (painter, content) in enumerate(identities):
            match = [g for g in groups if (g["pipeline"], g["painter_id"], g["label"])
                     == (pipeline, painter, content)]
            if len(match) != 1:
                raise ValueError("reference broad-content pipeline summary missing")
            values = match[0]["raw"]
            y = j + (i - 1) * 0.18
            axes[0].plot([values["minimum"], values["maximum"]], [y, y],
                         color=COLORS[i], lw=1, alpha=0.8)
            axes[0].plot([values["q25"], values["q75"]], [y, y], color=COLORS[i], lw=4)
            axes[0].plot(values["median"], y, "o", color=COLORS[i], markersize=4,
                         label=PIPELINES[pipeline] if j == 0 else None)
    axes[0].set_yticks(range(len(identities)),
                      [PAINTERS.get(p, p) + " / " + c for p, c in identities])
    axes[0].set_xlabel("chroma_median (raw feature units)")
    axes[0].set_title("Finite reference ranges by broad content\n"
                      "Line: min/max; thick: IQR; dot: median", pad=12)
    axes[0].legend(title="Processing", fontsize=8)
    works = reference["works"]
    for i, painter in enumerate(PAINTERS):
        ix = [j for j, work in enumerate(works) if work["painter_id"] == painter]
        axes[1].scatter([j + 1 for j in ix],
                        [works[j]["pipeline_span_primary_iqr_units"] for j in ix],
                        s=14, color=COLORS[i], label=PAINTERS[painter])
    axes[1].set_xlabel("Reference work (saved identity order)")
    axes[1].set_ylabel("Range across processing / primary development IQR")
    axes[1].set_title("Same-work processing sensitivity\n"
                      "These are not independent captures", pad=12)
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.2)
    return fig


def _markdown(result, tables):
    diagnostic, gates = result["diagnostics"], result["gates"]
    missing = gates.get("missing", [])
    feasibility = diagnostic["reference_chroma"]["fine_content_feasibility"]
    text = [
        "# Painter responsiveness: retained-data diagnostics and readiness", "",
        f"**Generation gate: `{gates['status']}`.** "
        + ("Unmet prerequisites: " + ", ".join(f"`{x}`" for x in missing) + "."
           if missing else "Read individual gate checks; readiness is not a scientific result."),
        "", "This is the D0 readiness snapshot before live metadata and actual human stages. "
        "Later provider and human receipts record their own status; they do not rewrite D0.",
        "", "Independent fine-content reference support and human interpretation remain "
        "unvalidated in the retained-data diagnostic. Its numerical patterns cannot establish "
        "a perceptual or internal-model mechanism. No generation occurred in this analysis.", "",
        "## What the saved vectors can and cannot show", "",
        "The main summaries use primary512/original31 and equal brief/repetition weights. "
        "They therefore have a different target from the earlier painter-reference-content "
        "weighted comparison. Every named/free cell and every brief is retained.", "",
        "| Cell | Empirical between-brief change | Cross-repeat change | Within-brief change |",
        "| --- | ---: | ---: | ---: |",
    ]
    for cell in diagnostic["cells"]:
        changes = _scope(cell)["changes"]
        text.append(f"| {_label(cell)} | {changes['between_brief_trace']:+.6f} | "
                    f"{changes['cross_repeat_between_trace']:+.6f} | "
                    f"{changes['within_brief_trace']:+.6f} |")
    text += [
        "", "![Observed and cross-repetition changes](plots/brief_variation.png)", "",
        "Negative changes describe contraction in these coordinates. A cross-repeat product "
        "can be negative and is not a variance constrained to be nonnegative. Interpreting it "
        "as stable between-brief signal requires stable brief means and independent zero-mean "
        "errors across repetition cohorts. Service state and timing do not establish those "
        "assumptions. All pair products and the separate content-only scopes are exported. "
        "There are no new p-values, population intervals or attenuation regressions.", "",
        "![Every coordinate displacement](plots/coordinate_displacements.png)", "",
        "This figure shows mean shifts, not variance changes or perceptual style axes. "
        "Individual brief vectors, including contrary movements, are in `brief_coordinates.csv`; "
        "exact generated memberships are in `brief_memberships.csv`. Shared shifts can reflect "
        "rendering consistency without loss of requested content. The current prompts do not "
        "randomize a visual attribute, so they cannot establish response attenuation.", "",
        "## Reference chroma and feasibility", "",
        f"**Fine-content support: `{feasibility['status']}`.** " + feasibility["reason"], "",
        "![Reference support and processing spread](plots/reference_chroma.png)", "",
        "Reference ranges are finite empirical summaries, not validated targets, tolerance "
        "intervals or independently confirmed reachability. Each work is compared across the "
        "three existing processing pipelines using one primary-development chroma scale. "
        "Alternate processing of the same file is not an alternate photographic capture. "
        "Singleton subject labels provide no within-stratum range evidence. All exact labels, "
        "IDs and values remain in the reference tables.", "",
        "## Service metadata and proposed-design simulation", "",
        diagnostic["service_quality"]["interpretation"], "",
        "`quality_groups.csv` retains all requested/reported groups and their exact request IDs. "
        "A prompt-associated quality report can reflect rendering, routing or reporting; it "
        "does not identify the setting actually used. Failed requests are not quietly redefined "
        "as measured images in this successful-output inventory.", "",
    ]
    simulation = result.get("simulation", {})
    if simulation:
        text += [f"Simulation: {simulation.get('planned_images', 'unavailable')} planned images, "
                 f"{simulation.get('fixed_templates', 'unavailable')} fixed templates, "
                 f"{simulation.get('trials_per_scenario', 'unavailable')} Monte Carlo trials "
                 "per scenario/effect setting. All scenario results are in `simulation.csv`.", "",
                 simulation.get("scope", "No simulation scope was supplied."), "",
                 "Monte Carlo intervals describe simulation precision. They are not intervals "
                 "for a future experiment. The generic arm uses an unvalidated historical "
                 "artist-free noise proxy. An effect grid and a nominal image count do not "
                 "supply a meaningful margin or demonstrate human/reference validation.", ""]
    if simulation:
        text += [
            "| Noise scenario | Monet power at −0.5 | Cézanne power at −0.5 | "
            "Monet median interval half-width | Cézanne median interval half-width |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for row in simulation.get("results", []):
            if row["true_interactions"] == [-0.5, -0.5]:
                power = row["rejection_probability"]
                width = row["median_family_interval_halfwidth"]
                text.append(f"| {row['scenario']} | {power[0]:.3f} | {power[1]:.3f} | "
                            f"{width[0]:.3f} | {width[1]:.3f} |")
        text += ["", "The −0.5 interaction is hypothetical, in primary-development IQR units. "
                 "Power means rejection of the corresponding zero interaction after "
                 "Holm adjustment; "
                 "interval widths refer to Bonferroni simultaneous intervals. Monte Carlo bounds, "
                 "null/partial-null errors and all effect settings remain in `simulation.csv`.", ""]
    text += [
        "## Reproduction and complete tables", "",
        "This renderer reads the supplied numeric result only. It performs no image access, "
        "feature extraction, sampling, regression or statistical testing. List-valued CSV "
        "fields preserve their full values as JSON; blank fields mean unavailable. "
        "The publication receipt binds this report and its numeric input separately. "
        "All review is maintainer-run LLM review unless separately documented otherwise.", "",
        "| Table | Rows |", "| --- | ---: |",
    ]
    text += [f"| [{name}.csv]({name}.csv) | {len(rows)} |" for name, rows in sorted(tables.items())]
    return "\n".join(text) + "\n"


def render(result, output_dir):
    """Write presentation files and return paths relative to output_dir.

    Publication, freezing and input hash verification are the caller's concern.
    The renderer can be replayed in an empty temporary directory without the repo.
    """
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "plots").mkdir(exist_ok=True)
    tables = _tables(result)
    paths = []
    for name, rows in sorted(tables.items()):
        _csv(directory / f"{name}.csv", rows)
        paths.append(f"{name}.csv")
    with plt.rc_context({"font.family": "DejaVu Sans", "svg.hashsalt": "responsiveness-v1",
                         "figure.facecolor": "white", "savefig.facecolor": "white"}):
        for name, figure in (("brief_variation", _variation),
                             ("coordinate_displacements", _displacements),
                             ("reference_chroma", _chroma)):
            paths.extend(_save(figure(result["diagnostics"]), directory, name))
    (directory / "REPORT.md").write_text(_markdown(result, tables), encoding="utf-8")
    paths.append("REPORT.md")
    return sorted(paths)
