"""Pure fixed-panel estimates; no images, transports, fitted scales or publication."""

from collections import Counter

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import t

from latent_art_bench.painter_distribution_study_v1.inference import test_contrast
from latent_art_bench.painter_distribution_study_v1.statistics import distribution_summary
from latent_art_bench.painter_distribution_study_v1.study import PIPELINES
from latent_art_bench.painter_prompt_study_v1.randomization import holm
from latent_art_bench.painter_responsiveness_v1.inference import analyze_factorial

from . import common


def validate_measurements(requests, rows):
    expected = {(r["request_id"], p) for r in requests for p in PIPELINES}
    by_id, design = {}, {r["request_id"]: r for r in requests}
    for row in rows:
        key = row["request_id"], row["pipeline"]
        if key not in expected or key in by_id:
            raise ValueError("unknown or duplicate measured slot/pipeline")
        source = design[row["request_id"]]
        if any(
            row.get(k) != source[k]
            for k in (
                "experiment",
                "route",
                "template_id",
                "repetition",
                "arm",
                "polarity",
                "block_id",
                "block_order",
                "content_class",
            )
        ):
            raise ValueError("measurement treatment identity differs from assignment")
        if not isinstance(row.get("status"), str) or not row["status"]:
            raise ValueError("measurement requires a terminal status")
        for field in ("values", "scaled"):
            if row["status"] == "measured":
                v = np.asarray(row[field], dtype=float)
                if v.shape != (31,) or not np.isfinite(v).all():
                    raise ValueError("measurement requires 31 finite coordinates")
            elif row.get(field) is not None:
                raise ValueError("unavailable slot carries an analysis vector")
        if row["status"] == "measured" and not np.isfinite(row["chroma_primary_iqr"]):
            raise ValueError("nonfinite primary-scale chroma")
        by_id[key] = row
    if set(by_id) != expected:
        raise ValueError("all planned slot/pipeline terminal measurements are required")
    return by_id


def _references(rows, painter, pipeline):
    selected = [r for r in rows if r["painter_id"] == painter and r["pipeline"] == pipeline]
    expected = 38 if painter == "claude_monet" else 32
    if len(selected) != expected or len({r["image_id"] for r in selected}) != expected:
        raise ValueError("fixed reference membership differs")
    values = np.asarray([r["scaled"] for r in selected])
    if values.shape != (expected, 31) or not np.isfinite(values).all():
        raise ValueError("invalid fixed reference vectors")
    masses = {k: v / expected for k, v in Counter(r["content_class"] for r in selected).items()}
    if set(masses) != {"water", "built", "land"}:
        raise ValueError("all fixed reference classes are required")
    return selected, values, masses


def analyze(requests, rows, references, config):
    by_id = validate_measurements(requests, rows)
    naming = [r for r in requests if r["experiment"] == "naming"]
    primary, contributions, distributions = [], [], []
    blocks = sorted({r["block_id"] for r in naming})
    if len(blocks) != 24 * config["naming_repetitions"]:
        raise ValueError("the naming allocation requires every prospectively fixed triplet")
    slots = {(r["block_id"], r["arm"]): r for r in naming}
    complete = all(by_id[r["request_id"], "primary512"]["status"] == "measured" for r in naming)
    for index, (arm, painter) in enumerate(common.PAINTERS.items()):
        endpoint = "naming_" + arm
        record = dict(
            endpoint=endpoint,
            experiment="naming",
            painter_id=painter,
            estimate=None,
            raw_p=None,
            interval=None,
            status="withheld_incomplete_allocated_grid",
        )
        for pipeline in PIPELINES:
            refs, x, masses = _references(references, painter, pipeline)
            weights = np.array(
                [
                    masses[slots[b, "free"]["content_class"]] / (8 * config["naming_repetitions"])
                    for b in blocks
                ]
            )
            generated = {}
            for selected_arm in ("free", "monet", "cezanne"):
                selected = [by_id[slots[b, selected_arm]["request_id"], pipeline] for b in blocks]
                if any(r["status"] != "measured" for r in selected):
                    distributions.append(
                        dict(
                            painter_id=painter,
                            pipeline=pipeline,
                            arm=selected_arm,
                            status="withheld_incomplete_allocated_arm",
                        )
                    )
                    continue
                y = np.asarray([r["scaled"] for r in selected])
                generated[selected_arm] = y
                summary = distribution_summary(x, y, generated_weights=weights)
                distances = cdist(x, x)
                np.fill_diagonal(distances, np.inf)
                radii = np.partition(distances, 2, axis=1)[:, 2]
                coverage = float((cdist(x, y).min(axis=1) <= radii).mean())
                distributions.append(
                    dict(
                        painter_id=painter,
                        pipeline=pipeline,
                        arm=selected_arm,
                        status="descriptive",
                        original_n=len(x),
                        generated_n=len(y),
                        reference_ids=[r["image_id"] for r in refs],
                        generated_ids=[r["request_id"] for r in selected],
                        generated_weights=weights.tolist(),
                        coverage_k3=coverage,
                        **summary,
                    )
                )
            if pipeline == "primary512" and complete:
                tested, values = test_contrast(
                    x,
                    generated["free"],
                    generated[arm],
                    seed=config["analysis_seed"] + index,
                    pair_weights=weights,
                )
                record.update(
                    estimate=tested["estimate"],
                    raw_p=tested["raw_p"],
                    status="conditional_randomization",
                    randomization=tested,
                )
                other = "cezanne" if arm == "monet" else "monet"
                for block, weight, value in zip(blocks, weights, values, strict=True):
                    contributions.append(
                        dict(
                            endpoint=endpoint,
                            block_id=block,
                            block_order=slots[block, arm]["block_order"],
                            weight=float(weight),
                            contribution=float(value),
                            free_id=slots[block, "free"]["request_id"],
                            named_id=slots[block, arm]["request_id"],
                            conditioned_third_id=slots[block, other]["request_id"],
                            conditioned_third_position=slots[block, other]["within_block"],
                        )
                    )
        primary.append(record)
    schedule = common.palette_schedule(requests)
    palette_results = {}
    for pipeline in PIPELINES:
        outcomes = [
            dict(
                request_id=r["request_id"],
                status=by_id[r["request_id"], pipeline]["status"],
                value=by_id[r["request_id"], pipeline].get("chroma_primary_iqr"),
            )
            for r in schedule
        ]
        palette_results[pipeline] = analyze_factorial(
            schedule, outcomes, alpha=config["alpha"], manipulation_margin=0
        )
    main = palette_results["primary512"]
    for index, arm in enumerate(common.PAINTERS):
        old = main["primary"][index] if main["primary"] is not None else None
        record = dict(
            endpoint="palette_" + arm,
            experiment="palette",
            painter_id=common.PAINTERS[arm],
            estimate=old["estimate"] if old else None,
            raw_p=old["p_two_sided"] if old else None,
            interval=None,
            status=old["inference_status"] if old else main["status"],
        )
        if old and old["p_two_sided"] is not None:
            critical = float(t.ppf(1 - config["alpha"] / 8, old["welch_df"]))
            record.update(
                standard_error=old["standard_error"],
                welch_df=old["welch_df"],
                interval=[
                    old["estimate"] - critical * old["standard_error"],
                    old["estimate"] + critical * old["standard_error"],
                ],
                interval_coverage=1 - config["alpha"] / 4,
            )
        primary.append(record)
    adjusted = holm([r["raw_p"] if r["raw_p"] is not None else 1 for r in primary])
    for row, pvalue in zip(primary, adjusted, strict=True):
        row.update(
            holm_p=float(pvalue),
            reject=bool(row["raw_p"] is not None and pvalue <= config["alpha"]),
        )
        estimate = row["estimate"]
        row["direction"] = (
            "unavailable"
            if estimate is None
            else "negative"
            if estimate < 0
            else "positive"
            if estimate > 0
            else "zero"
        )
        if row["experiment"] == "naming":
            row["directional_replication"] = bool(row["reject"] and estimate < 0)
        else:
            row["interpretation"] = "new measured interaction; historical result was unresolved"
    return dict(
        primary=primary,
        naming_contributions=contributions,
        distributions=distributions,
        palette=palette_results,
        primary_family_size=4,
        alpha=config["alpha"],
        component_diagnostics_scope="Nested randomization and palette records retain unchanged "
        "primitive diagnostics, including the palette primitive's two-endpoint adjustments. "
        "Only top-level primary records, after collection-scope gating, declare successor "
        "four-endpoint inference or replication claims.",
        availability=dict(Counter(r["status"] for r in rows if r["pipeline"] == "primary512")),
        scope="One fresh collection; no independent-backend, session-population, "
        "perceptual or original/new equality claim.",
    )
