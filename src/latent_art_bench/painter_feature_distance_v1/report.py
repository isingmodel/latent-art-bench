"""Deterministic numeric reports and plots for the exposed-data distance analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from latent_art_bench.painter_feature_generation_v1.panel import SHORT_LABELS

FAMILY_LABELS = {"color": "Color", "spatial": "Spatial / orientation", "texture": "Digital texture"}
COLORS = ("#0072B2", "#D55E00", "#009E73", "#CC79A7")
STEMS = (
    "target_distances", "matrix_color", "matrix_spatial", "matrix_texture",
    "control_and_specificity", "coordinates_color", "coordinates_spatial", "coordinates_texture",
    "equal_count_blocks",
)
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
    "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "savefig.facecolor": "white", "svg.hashsalt": "pfg-distance-v1",
}


def _label(painter: str) -> str:
    return SHORT_LABELS.get(painter, painter.replace("_", " ").title())


def _table(headers: list[str], rows: list[list]) -> str:
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        + ["| " + " | ".join(map(str, row)) + " |" for row in rows]
    )


def _save(fig, output: Path, stem: str) -> None:
    try:
        for extension, metadata in (
            ("png", {"Software": "LatentArtBench"}),
            ("svg", {"Date": None, "Creator": "LatentArtBench"}),
        ):
            with (output / "plots" / f"{stem}.{extension}").open("xb") as handle:
                fig.savefig(handle, format=extension, dpi=150, metadata=metadata)
    finally:
        plt.close(fig)


def _plot_targets(result: dict, output: Path) -> None:
    painters, services = result["painters"], result["services"]
    lookup = {(r["service"], r["painter_id"], r["family"]): r for r in result["contrasts"]}
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), layout="constrained", sharey=True)
    for ax, family in zip(axes, result["families"]):
        for index, service in enumerate(services):
            offset = (index - (len(services) - 1) / 2) * 0.19
            values = [lookup[service, painter, family]["target_distance"] for painter in painters]
            counts = sorted(set(result["generated_counts"][service].values()))
            count = str(counts[0]) if len(counts) == 1 else "variable"
            ax.scatter(values, np.arange(len(painters)) + offset, color=COLORS[index],
                       label=f"{service} ({count} images / condition)", s=52, zorder=3)
        ax.set(title=FAMILY_LABELS[family], xlabel="Finite V-energy distance", xlim=(0, None))
        ax.set_yticks(range(len(painters)), [_label(p) for p in painters])
        ax.grid(axis="x", alpha=0.2)
    axes[0].invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center",
               ncols=len(services))
    fig.suptitle("Distance from painter-name outputs to that painter's reference paintings\n"
                 "All available images; lower values mean closer measured distributions",
                 fontsize=14)
    _save(fig, output, "target_distances")


def _annotate(ax, matrix: np.ndarray, limit: float, signed: bool = False) -> None:
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            white = abs(value) > limit * 0.65 if signed else value < limit * 0.45
            ax.text(column, row, f"{value:.2f}", ha="center", va="center",
                    fontsize=9, color="white" if white else "#151515")


def _plot_matrices(result: dict, output: Path) -> None:
    painters, services = result["painters"], result["services"]
    conditions = [*painters, "artist_free"]
    lookup = {(r["service"], r["condition"], r["painter_id"], r["family"]): r["distance"]
              for r in result["distances"]}
    for family in result["families"]:
        limit = max(r["distance"] for r in result["distances"] if r["family"] == family) or 1.0
        fig, axes = plt.subplots(1, len(services), figsize=(15, 5.5),
                                 layout="constrained", sharey=True, squeeze=False)
        for ax, service in zip(axes[0], services):
            matrix = np.array([[lookup[service, condition, p, family] for p in painters]
                               for condition in conditions])
            im = ax.imshow(matrix, cmap="viridis", vmin=0, vmax=limit, aspect="auto")
            _annotate(ax, matrix, limit)
            counts = result["generated_counts"][service]
            sizes = sorted(set(counts.values()))
            count_text = str(sizes[0]) if len(sizes) == 1 else "variable"
            ax.set(title=f"{service}\n{count_text} generated images / condition",
                   xlabel="Reference painter")
            ax.set_xticks(range(len(painters)), [_label(p) for p in painters], rotation=25)
            ax.set_yticks(range(len(conditions)), [*map(_label, painters), "Artist-free"])
            for i in range(len(painters)):
                ax.add_patch(plt.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                          fill=False, edgecolor="white", linewidth=2))
        axes[0, 0].set_ylabel("Generation prompt condition")
        fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85, label="Finite V-energy distance")
        fig.suptitle(f"{FAMILY_LABELS[family]}: every generated condition × reference painter\n"
                     "One color scale across services; outlined cells match the named painter",
                     fontsize=14)
        _save(fig, output, f"matrix_{family}")


def _plot_contrasts(result: dict, output: Path) -> None:
    painters, services = result["painters"], result["services"]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8.6), layout="constrained", sharey=True)
    lookup = {(r["service"], r["painter_id"], r["family"]): r for r in result["contrasts"]}
    for column, family in enumerate(result["families"]):
        limit = max(abs(r[key]) for r in result["contrasts"] if r["family"] == family
                    for key in ("control_difference", "specificity_margin")) * 1.12 or 1.0
        for row, (key, title) in enumerate((
            ("control_difference", "Named − artist-free distance"),
            ("specificity_margin", "Own-painter − nearest-other distance"),
        )):
            ax = axes[row, column]
            for index, service in enumerate(services):
                offset = (index - (len(services) - 1) / 2) * 0.19
                values = [lookup[service, painter, family][key] for painter in painters]
                ax.scatter(values, np.arange(len(painters)) + offset, color=COLORS[index],
                           label=service, s=44, zorder=3)
            ax.axvline(0, color="#505050", linewidth=1)
            ax.set(title=f"{FAMILY_LABELS[family]}\n{title}", xlim=(-limit, limit),
                   xlabel="Difference in finite V-energy distance")
            ax.set_yticks(range(len(painters)), [_label(p) for p in painters])
            ax.grid(axis="x", alpha=0.2)
    axes[0, 0].invert_yaxis()
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center",
               ncols=len(services))
    fig.suptitle("Painter-name benefit and painter specificity are separate comparisons\n"
                 "Negative values favor the painter-name condition / its own reference",
                 fontsize=14)
    _save(fig, output, "control_and_specificity")


def _plot_coordinates(result: dict, output: Path) -> None:
    painters, services = result["painters"], result["services"]
    lookup = {(r["service"], r["painter_id"], r["coordinate"]): r["median_difference"]
              for r in result["coordinates"]}
    for family, coordinates in result["families"].items():
        limit = max(abs(r["median_difference"]) for r in result["coordinates"]
                    if r["family"] == family) or 1.0
        fig, axes = plt.subplots(1, len(services), figsize=(15, 0.37 * len(coordinates) + 2.5),
                                 layout="constrained", sharey=True, squeeze=False)
        for ax, service in zip(axes[0], services):
            matrix = np.array([[lookup[service, p, coordinate] for p in painters]
                               for coordinate in coordinates])
            im = ax.imshow(matrix, cmap="RdBu_r", vmin=-limit, vmax=limit, aspect="auto")
            _annotate(ax, matrix, limit, signed=True)
            ax.set(title=service, xlabel="Named painter and its reference")
            ax.set_xticks(range(len(painters)), [_label(p) for p in painters], rotation=25)
            ax.set_yticks(range(len(coordinates)), coordinates)
        fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.85,
                     label="Median shift (development IQR units)")
        fig.suptitle(f"{FAMILY_LABELS[family]}: all {len(coordinates)} coordinate median shifts\n"
                     "Positive = higher generated median; shared family scale across services",
                     fontsize=14)
        _save(fig, output, f"coordinates_{family}")


def _plot_blocks(result: dict, output: Path) -> None:
    painters, services = result["painters"], result["services"]
    lookup = {(r["service"], r["painter_id"], r["family"]): r for r in result["block_summary"]}
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.6), layout="constrained", sharey=True)
    for ax, family in zip(axes, result["families"]):
        for index, service in enumerate(services):
            offset = (index - (len(services) - 1) / 2) * 0.19
            rows = [lookup[service, painter, family] for painter in painters]
            centers = np.array([r["median"] for r in rows])
            errors = np.array([centers - [r["minimum"] for r in rows],
                               [r["maximum"] for r in rows] - centers])
            repeats = max(r["blocks"] for r in rows)
            ax.errorbar(centers, np.arange(len(painters)) + offset, xerr=errors,
                        fmt="D" if repeats > 1 else "o", color=COLORS[index],
                        label=f"{service}: {repeats} block{'s' if repeats != 1 else ''}",
                        capsize=3, markersize=5, linewidth=1.6)
        ax.set(title=FAMILY_LABELS[family], xlabel="Finite V-energy distance", xlim=(0, None))
        ax.set_yticks(range(len(painters)), [_label(p) for p in painters])
        ax.grid(axis="x", alpha=0.2)
    axes[0].invert_yaxis()
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center",
               ncols=len(services))
    fig.suptitle("Equal generated-count view: 16 template images per condition in each block\n"
                 "SD-Turbo: block median and observed min–max; GPT: one observed block. No CI.",
                 fontsize=14)
    _save(fig, output, "equal_count_blocks")


def _markdown(result: dict) -> str:
    painters, services = result["painters"], result["services"]
    families = result["families"]
    contrasts = {(r["service"], r["painter_id"], r["family"]): r for r in result["contrasts"]}
    target_rows = [
        [_label(painter), FAMILY_LABELS[family]]
        + [f"{contrasts[service, painter, family]['target_distance']:.4f}" for service in services]
        for painter in painters for family in families
    ]
    reference_rows = [[_label(p), result["reference_counts"][p]] for p in painters]
    generated_rows = [[service] + [result["generated_counts"][service][c]
                                   for c in [*painters, "artist_free"]] for service in services]
    contrast_rows = []
    for service in services:
        for family in families:
            rows = [contrasts[service, painter, family] for painter in painters]
            contrast_rows.append([
                service, FAMILY_LABELS[family],
                f"{sum(r['control_difference'] < 0 for r in rows)}/{len(painters)}",
                f"{sum(r['specificity_margin'] < 0 for r in rows)}/{len(painters)}",
            ])
    reference_lookup = {
        (frozenset((r["first_painter"], r["second_painter"])), r["family"]): r["distance"]
        for r in result["reference_distances"]
    }
    between_rows = [
        [_label(first), _label(second)]
        + [f"{reference_lookup[frozenset((first, second)), family]:.4f}" for family in families]
        for index, first in enumerate(painters) for second in painters[index + 1:]
    ]
    pieces = [
        "# Generated-image feature distances from painters' reference paintings",
        "This analysis measures how far the existing generated-image distributions are from "
        "the existing reference paintings in 31 interpretable features. The table below gives "
        "the complete own-painter distances, using all available images. Smaller values mean "
        "closer measured distributions within the same feature family. Each service–painter–family "
        "comparison is retained; there is no combined model score or overall ranking.",
        _table(["Reference painter", "Feature family", *services], target_rows),
        "![Own-painter distance comparisons](plots/target_distances.png)",
        "## Data and estimand",
        "This is a post-hoc descriptive analysis of already exposed v2 features, authorized to "
        "reuse the existing painters, generated images and feature definitions. It does not "
        "reopen confirmation as a new holdout. The original stage evidence remains unchanged. "
        f"The frozen shared measurement method is `{result['method_id']}`.",
        _table(["Reference painter", "Measured confirmation works"], reference_rows),
        _table(["Requested service", *map(_label, painters), "Artist-free"], generated_rows),
        "Each reference work receives equal weight within its painter; each generated image "
        "receives equal weight within its service and prompt condition. Unequal reference and "
        "generation counts are retained. These are finite observed distributions, not "
        "probability samples of each painter's oeuvre or all outputs of an underlying model.",
        "The corpus consists of Wikidata-declared outdoor-place paintings and measured digital "
        "surrogates delivered through Wikimedia Commons. Attribution, object/media eligibility "
        "and outdoor-place selection derive from the recorded metadata rules. This is not an "
        "independent museum-level verification of attribution. Measurement succeeded for 649 "
        "confirmation works after recorded acquisition and normalization attrition; failed "
        "attempts remain in the original ledgers.",
        "For each coordinate, `z = (feature − frozen development median) / frozen development "
        "IQR`. The equal-painter scaler was fitted to 221 new-development works, excluding "
        "historical development and confirmation. It is reused without refitting. Euclidean "
        "distances are calculated separately in color (11 coordinates), spatial/orientation "
        "(8), and digital texture (12). No dimension normalization or family aggregation is used; "
        "absolute values should therefore not be compared across families.",
        "For transformed reference vectors `x₁ … xₙ` and generated vectors `y₁ … yₘ`, the "
        "reported finite V-energy statistic is:",
        "```text\nDᵥ(X,Y) = 2/(nm) ΣᵢΣⱼ ||xᵢ − yⱼ||₂\n"
        "          − 1/n² ΣᵢΣₖ ||xᵢ − xₖ||₂\n"
        "          − 1/m² ΣⱼΣₗ ||yⱼ − yₗ||₂\n```",
        "Both within-distribution sums include the zero diagonal terms. This is the energy "
        "statistic itself (sometimes called squared energy distance), without a square root. "
        "It compares both location and distributional spread, rather than only centroids. "
        "Zero denotes identical empirical feature distributions under this metric. Positive "
        "values have no calibrated equivalence cutoff. When interpreted as a population "
        "estimator, its finite-sample bias depends on sample sizes and dispersion; sample-size "
        "differences prevent interpreting small pooled cross-service gaps as general model gains.",
        "## Complete generated-condition × reference matrices",
        "Every painter-name condition and the matched artist-free condition is compared with "
        "all four references. White outlines mark own-painter cells. Each family has one color "
        "scale across services. Matrix numbers are rounded only for display; exports retain "
        "full numerical precision.",
    ]
    for family in families:
        pieces.append(f"![{FAMILY_LABELS[family]} complete matrix](plots/matrix_{family}.png)")
    pieces.extend([
        "## Artist-free benefit and painter specificity",
        "`control_difference = own-painter distance − artist-free distance to the same painter`. "
        "A negative value describes closer fit after adding that painter's name. "
        "`specificity_margin = own-painter distance − distance to the nearest other painter`. "
        "A negative value means the named condition is closer to its own reference than to "
        "each of the three other references. Neither comparison establishes equivalence.",
        _table(["Service", "Family", "Closer than artist-free", "Own reference strictly closest"],
               contrast_rows),
        "Counts above summarize the four painters within each family; ties do not count as "
        "strict improvement. They are descriptive signs, without significance tests or "
        "multiplicity-adjusted claims. All individual differences and nearest-other identities "
        "are available in [contrasts.csv](contrasts.csv).",
        "![Control benefit and specificity](plots/control_and_specificity.png)",
        "## Equal generated-count diagnostic",
        "Each SD-Turbo repetition block contains the same 16 templates for every condition; "
        "each GPT alias has one such block. Recomputing distances for each complete SD-Turbo "
        "block uses 16 generated images per condition for every service. All 25 SD-Turbo blocks "
        "are retained. Points are block medians and whiskers span the observed minimum to "
        "maximum; a GPT point is its single observed block. These ranges are **not confidence "
        "intervals**. The reference counts still differ by painter, and service settings, "
        "output geometry and repeated sampling differ. This diagnostic does not create a "
        "population-level ranking. A median of block distances need not equal the distance "
        "computed from all 400 pooled SD-Turbo images.",
        "![Equal-count block distances](plots/equal_count_blocks.png)",
        "## Coordinate diagnostics: all 31 features",
        "Every named-painter coordinate is shown, without feature selection. Values are "
        "generated median minus reference median after the frozen transform, so a value of "
        "+1 means a higher generated median by one development IQR. This signed diagnostic "
        "is separate from multivariate distance; compensating shifts cannot be summed into "
        "an overall fit score. [coordinates.csv](coordinates.csv) also contains generated / "
        "reference IQR ratios. Ratios above one indicate greater generated dispersion in that "
        "coordinate; an empty ratio means the reference IQR is zero and division is undefined.",
    ])
    for family in families:
        pieces.append(f"![All {FAMILY_LABELS[family]} median shifts]"
                      f"(plots/coordinates_{family}.png)")
    pieces.extend([
        "## Distances between the reference painters",
        "These comparisons use the same frozen transform and V-energy formula. They show "
        "how separated the four observed reference distributions are in each family. They "
        "are context, not a tolerance threshold or an independent-capture noise floor.",
        _table(["First painter", "Second painter", *[FAMILY_LABELS[f] for f in families]],
               between_rows),
        "## Interpretation limits",
        "SD-Turbo refers to the pinned revision recorded in the original freeze. `gpt-image-1` "
        "and `gpt-image-2` identify requested OAuth service aliases: neither response attested "
        "an underlying model snapshot. GPT responses reported low quality and variable, mostly "
        "landscape dimensions, despite requested 1024×1024 / medium settings. SD-Turbo generated "
        "512×512 squares. Comparisons therefore describe observed services under their actual "
        "recorded behavior.",
        "Subject content, composition, aspect ratio, source workflows, color profiles and "
        "digital reproduction can affect these measurements. The painters' outdoor-place "
        "content mixes differ. Digital texture measures do not measure physical brushwork, "
        "and these features do not isolate content-free style, authorship, intention, or "
        "artistic quality. Existing paired crop sensitivity and source/profile diagnostics "
        "remain in the original empirical report; this extension does not retune the features "
        "or regenerate those sealed analyses.",
        "Independent capture calibration is unnecessary to describe the observed feature "
        "distances. It is needed to separate capture disturbance from painter differences and "
        "support a calibrated reproduction/equivalence claim. No such threshold is inferred "
        "here. No confidence intervals are newly computed: the original repeated-block "
        "nominal intervals were exploratory because synthetic shift calibration covered only "
        "86% at a nominal 95% level. Historical neutral reviews were maintainer-run LLM review "
        "subagents, not institutionally independent reviews.",
        "## Reproduction and exports",
        "Run from the repository root with the locked analysis dependencies. Each build needs "
        "a new output directory; an existing report is never overwritten.",
        "```bash\nuv run --locked --extra analysis --extra learned "
        "latent-art-bench feature-distances build "
        f"\\\n  --method-id {result['method_id']} "
        "\\\n  --output tmp/feature-distance-reproduction\n"
        "uv run --locked --extra analysis --extra learned "
        "latent-art-bench feature-distances check "
        "\\\n  --output tmp/feature-distance-reproduction\n```",
        "The build reads sealed numeric feature records and their provenance. It performs "
        "no image acquisition, image reading, feature extraction, or generation requests. "
        "[analysis.json](analysis.json) contains the full result and [provenance.json]"
        "(provenance.json) records the inputs and exported artifacts. Figures are provided as "
        "PNG and SVG; [distances.csv](distances.csv), [contrasts.csv](contrasts.csv), "
        "[coordinates.csv](coordinates.csv), [reference_distances.csv](reference_distances.csv), "
        "[block_distances.csv](block_distances.csv) and [block_summary.csv](block_summary.csv) "
        "retain every comparison.",
        f"Original completed report (repository-relative): `{result['source']['report']}`. "
        "Input SHA-256 bindings are retained in the exported provenance, separately from "
        "the existing experiment's immutable evidence.",
    ])
    return "\n\n".join(pieces) + "\n"


def write_report(result: dict, output: Path) -> list[Path]:
    """Write a report and nine plotted comparisons, refusing to replace any existing file."""
    output = Path(output)
    if not output.is_dir():
        raise ValueError("report output directory must already exist")
    paths = [output / "REPORT.md"] + [
        output / "plots" / f"{stem}.{extension}" for stem in STEMS for extension in ("png", "svg")
    ]
    if any(path.exists() or path.is_symlink() for path in paths):
        raise FileExistsError("report or plot output already exists")
    markdown = _markdown(result)
    (output / "plots").mkdir(exist_ok=True)
    with plt.rc_context(STYLE):
        _plot_targets(result, output)
        _plot_matrices(result, output)
        _plot_contrasts(result, output)
        _plot_coordinates(result, output)
        _plot_blocks(result, output)
    with (output / "REPORT.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(markdown)
    return paths
