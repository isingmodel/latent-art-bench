"""Two randomized actual-clause contrasts and fixed historical-map diagnostics."""

from collections import Counter

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.painter_distribution_study_v1.inference import test_contrast
from latent_art_bench.painter_distribution_study_v1.statistics import distribution_summary
from latent_art_bench.painter_naming_geometry_v1 import geometry, variance
from latent_art_bench.painter_prompt_study_v1.randomization import holm

from . import common


def _matrix(value, shape):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.isfinite(array).all():
        raise ValueError("expected finite vectors with the fixed dimensions")
    return array


def validate_inputs(inputs):
    if inputs["schema"] != "painter-clause-validation-inputs/1":
        raise ValueError("unexpected numerical input schema")
    for field in ("reference", "original", "maps", "scalers"):
        if set(inputs[field]) != set(common.PIPELINES):
            raise ValueError("all three fixed pipelines required")
    expected_counts = {
        "claude_monet": dict(water=21, built=4, land=13),
        "paul_cezanne": dict(water=3, built=11, land=18),
    }
    for painter, counts in expected_counts.items():
        size = sum(counts.values())
        if inputs["targets"][painter] != {k: v / size for k, v in counts.items()}:
            raise ValueError("fixed reference content masses changed")
        for pipe in common.PIPELINES:
            ref = inputs["reference"][pipe][painter]
            if len(ref["ids"]) != size or len(set(ref["ids"])) != size:
                raise ValueError("fixed reference membership is incomplete or duplicated")
            _matrix(ref["values"], (size, 31))
            old = inputs["original"][pipe]["oauth_gpt_image_2"][painter]
            if (
                Counter(old["classes"]) != dict.fromkeys(common.CLASSES, 8)
                or len(set(old["scene_ids"])) != 24
                or old["repeat_ids"] != [0, 1, 2]
            ):
                raise ValueError("fixed original OAuth training allocation differs")
            train_weights = np.repeat(
                [inputs["targets"][painter][c] / 24 for c in old["classes"]], 3
            )
            fitted = geometry.fit_map(
                _matrix(old["free"], (24, 3, 31)).reshape(-1, 31),
                _matrix(old["named"], (24, 3, 31)).reshape(-1, 31),
                train_weights,
            )
            if fitted != inputs["maps"][pipe][painter]:
                raise ValueError("historical map differs from the frozen generated-only fit")
            scale = inputs["scalers"][pipe]["scaler"]
            _matrix(scale["center"], (31,))
            if np.any(_matrix(scale["scale"], (31,)) <= 0):
                raise ValueError("fixed scaler must have positive coordinates")


def validate_design(requests, config):
    if (
        len(requests) != config["maximum_images"]
        or len({r["request_id"] for r in requests}) != len(requests)
        or [r["sequence"] for r in requests] != list(range(len(requests)))
    ):
        raise ValueError("complete ordered prospective request inventory required")
    slots = {}
    scene_classes = {}
    for pos in range(0, len(requests), 4):
        group = requests[pos : pos + 4]
        first = group[0]
        if {r["arm"] for r in group} != set(common.ARMS) or [
            r["within_block"] for r in group
        ] != list(range(4)):
            raise ValueError("each randomized block must contain four clause positions")
        for row in group:
            if (
                row["route"] != "oauth_gpt_image_2"
                or row["experiment"] != "clause"
                or row["polarity"] is not None
                or row["block_order"] != pos // 4 + 1
                or any(
                    row[k] != first[k]
                    for k in ("block_id", "template_id", "content_class", "repetition")
                )
            ):
                raise ValueError("assigned block or route identity differs")
            key = row["template_id"], row["repetition"], row["arm"]
            if key in slots or row["repetition"] not in range(config["repetitions"]):
                raise ValueError("duplicate or unknown scene/repeat/clause")
            slots[key] = row
            old_class = scene_classes.setdefault(row["template_id"], row["content_class"])
            if old_class != row["content_class"]:
                raise ValueError("scene class changes across blocks")
    if Counter(scene_classes.values()) != dict.fromkeys(common.CLASSES, config["scenes_per_class"]):
        raise ValueError("all prospective scenes and classes are required")
    if len(slots) != len(scene_classes) * config["repetitions"] * 4:
        raise ValueError("missing allocated scene/repeat/clause")
    return slots, scene_classes


def validate_measurements(requests, rows, inputs):
    design = {r["request_id"]: r for r in requests}
    expected = {(r["request_id"], p) for r in requests for p in common.PIPELINES}
    result = {}
    for row in rows:
        key = row["request_id"], row["pipeline"]
        if key not in expected or key in result:
            raise ValueError("unknown or duplicate terminal slot/pipeline")
        source = design[row["request_id"]]
        if any(
            row.get(k) != source[k]
            for k in (
                "sequence",
                "experiment",
                "route",
                "template_id",
                "content_class",
                "repetition",
                "arm",
                "polarity",
                "block_id",
                "block_order",
                "within_block",
            )
        ):
            raise ValueError("measurement differs from assigned request identity")
        if not isinstance(row.get("status"), str) or not row["status"]:
            raise ValueError("a terminal measurement status is required")
        if row["status"] == "measured":
            raw, scaled = _matrix(row["values"], (31,)), _matrix(row["scaled"], (31,))
            scaler = inputs["scalers"][row["pipeline"]]["scaler"]
            if not np.array_equal(scaled, (raw - scaler["center"]) / scaler["scale"]):
                raise ValueError("measurement uses a changed scaler")
        elif row.get("values") is not None or row.get("scaled") is not None:
            raise ValueError("unavailable outcome carries a measurement")
        result[key] = row
    if result.keys() != expected:
        raise ValueError("every allocated slot/pipeline needs terminal accounting")
    return result


def retrieval(cube, scene_ids, classes):
    """Leave-one-repetition centroid retrieval; deterministic sorted-ID tie rule."""
    n, repeats, _ = cube.shape
    predicted, within = [], []
    for repeat in range(repeats):
        centers = (cube.sum(axis=1) - cube[:, repeat]) / (repeats - 1)
        distances = cdist(cube[:, repeat], centers)
        full = np.argmin(distances, axis=1)
        masked = np.where(np.equal.outer(classes, classes), distances, np.inf)
        local = np.argmin(masked, axis=1)
        for scene in range(n):
            predicted.append(
                dict(
                    scene_id=scene_ids[scene],
                    repeat=repeat,
                    predicted_id=scene_ids[int(full[scene])],
                )
            )
            within.append(
                dict(
                    scene_id=scene_ids[scene],
                    repeat=repeat,
                    predicted_id=scene_ids[int(local[scene])],
                )
            )
    return dict(
        status="descriptive",
        queries=n * repeats,
        all_scenes_accuracy=sum(r["scene_id"] == r["predicted_id"] for r in predicted)
        / (n * repeats),
        within_class_accuracy=sum(r["scene_id"] == r["predicted_id"] for r in within)
        / (n * repeats),
        predictions=predicted,
        within_class_predictions=within,
        tie_rule="first centroid in lexicographic scene-ID order; no label-aware tie break",
    )


def trace_ratio(arms, numerator, denominator):
    if any(arms[a]["status"] != "descriptive" for a in (numerator, denominator)):
        return dict(status="unavailable_incomplete_arm", ratio=None)
    top = arms[numerator]["variance_reference_weight"]["observed_total"]
    bottom = arms[denominator]["variance_reference_weight"]["observed_total"]
    if bottom <= 0:
        return dict(status="unavailable_zero_denominator", ratio=None)
    return dict(status="descriptive", ratio=top / bottom)


def delivery_summary(rows):
    """One metadata count per allocated output; quality is a service field."""
    result = {}
    for arm in common.ARMS:
        selected = [r for r in rows if r["arm"] == arm and r["pipeline"] == "primary512"]
        observed = [r.get("observed") for r in selected if r.get("observed") is not None]
        result[arm] = dict(
            planned=len(selected),
            statuses=dict(Counter(r["status"] for r in selected)),
            observed_outputs=len(observed),
            dimensions=dict(Counter(f"{r['width']}x{r['height']}" for r in observed)),
            formats=dict(Counter(r["format"] for r in observed)),
            reported_quality=dict(
                Counter(str(r.get("reported", {}).get("quality") or "unreported") for r in observed)
            ),
            scope="Recorded delivery metadata, without quality measurement or filtering",
        )
    return result


def analyze(requests, rows, inputs, config, *, collection_receipt=None):
    validate_inputs(inputs)
    slots, scene_classes = validate_design(requests, config)
    by_id = validate_measurements(requests, rows, inputs)
    scene_ids = sorted(scene_classes)
    classes = [scene_classes[s] for s in scene_ids]
    repeats = config["repetitions"]
    primary, views = [], []
    collection_ok = (
        collection_receipt is not None
        and collection_receipt.get("duration_contract_met") is True
        and collection_receipt.get("identity_contract_met") is True
        and collection_receipt.get("planned") == len(requests)
    )
    for index, (named_arm, painter) in enumerate(common.PAINTERS.items()):
        endpoint = dict(
            endpoint="named_minus_generic_" + named_arm,
            painter_id=painter,
            estimate=None,
            raw_p=None,
            interval=None,
            status="withheld_incomplete_allocated_grid",
            pairs=len(scene_ids) * repeats,
        )
        for pipe in common.PIPELINES:
            ref = inputs["reference"][pipe][painter]
            x = np.asarray(ref["values"])
            masses = inputs["targets"][painter]
            sw = np.array([masses[c] / config["scenes_per_class"] for c in classes])
            weights = np.repeat(sw / repeats, repeats)
            cubes, arm_summaries = {}, {}
            for arm in common.ARMS:
                selected = [
                    [by_id[slots[s, r, arm]["request_id"], pipe] for r in range(repeats)]
                    for s in scene_ids
                ]
                if any(r["status"] != "measured" for group in selected for r in group):
                    arm_summaries[arm] = dict(status="withheld_incomplete_allocated_arm")
                    continue
                cube = np.asarray([[r["scaled"] for r in group] for group in selected])
                cubes[arm] = cube
                y = cube.reshape(-1, 31)
                arm_summaries[arm] = dict(
                    status="descriptive",
                    generated_n=len(y),
                    generated_ids=[[r["request_id"] for r in group] for group in selected],
                    distribution=distribution_summary(x, y, generated_weights=weights),
                    energy_terms=geometry.energy_terms(x, y, np.full(len(x), 1 / len(x)), weights),
                    variance_reference_weight=variance.corrected_variance(cube, sw),
                    variance_equal_scene=variance.corrected_variance(
                        cube, np.full(len(sw), 1 / len(sw))
                    ),
                    retrieval=retrieval(cube, scene_ids, classes),
                )
            view = dict(
                painter_id=painter,
                pipeline=pipe,
                scene_ids=scene_ids,
                scene_classes=classes,
                generated_weights=weights.tolist(),
                reference_ids=ref["ids"],
                arms=arm_summaries,
                contrasts={},
                maps={},
                trace_ratios={
                    "generic_over_free": trace_ratio(arm_summaries, "generic", "free"),
                    "named_over_generic": trace_ratio(arm_summaries, named_arm, "generic"),
                },
                map_target_differences=dict(status="unavailable_incomplete_free_arm"),
            )
            for before, after in (("generic", named_arm), ("free", "generic"), ("free", named_arm)):
                if before in cubes and after in cubes:
                    view["contrasts"][after + "_minus_" + before] = (
                        arm_summaries[after]["distribution"]["energy_distance"]
                        - arm_summaries[before]["distribution"]["energy_distance"]
                    )
            if "free" in cubes:
                fitted = inputs["maps"][pipe][painter]
                view["historical_fit"] = fitted
                for kind in ("translation", "translation_scale"):
                    y = geometry.apply(cubes["free"].reshape(-1, 31), fitted, kind)
                    view["maps"][kind] = dict(
                        status="descriptive_fixed_historical_map",
                        energy_terms=geometry.energy_terms(
                            x, y, np.full(len(x), 1 / len(x)), weights
                        ),
                    )
                    view["maps"][kind]["conditional_residual"] = (
                        dict(
                            status="descriptive",
                            **variance.cross_repeat_residual(
                                cubes[named_arm] - y.reshape(cubes["free"].shape), sw
                            ),
                        )
                        if named_arm in cubes
                        else dict(status="unavailable_incomplete_named_arm")
                    )
                t1, t2 = (view["maps"][k] for k in ("translation", "translation_scale"))
                view["map_target_differences"] = dict(
                    status="descriptive"
                    if named_arm in cubes
                    else "conditional_target_unavailable",
                    energy_t2_minus_t1=t2["energy_terms"]["energy"] - t1["energy_terms"]["energy"],
                    conditional_residual_t2_minus_t1=(
                        t2["conditional_residual"]["cross_repeat_mean_square"]
                        - t1["conditional_residual"]["cross_repeat_mean_square"]
                        if named_arm in cubes
                        else None
                    ),
                )
            if pipe == "primary512" and "generic" in cubes and named_arm in cubes:
                tested, contributions = test_contrast(
                    x,
                    cubes["generic"].reshape(-1, 31),
                    cubes[named_arm].reshape(-1, 31),
                    seed=config["analysis_seed"] + index,
                    pair_weights=weights,
                )
                endpoint.update(
                    status="available",
                    estimate=float(contributions.sum()),
                    raw_p=tested["raw_p"],
                    randomization=tested,
                    contributions=contributions.tolist(),
                    ordered_pairs=[
                        slots[s, r, named_arm]["block_id"]
                        for s in scene_ids
                        for r in range(repeats)
                    ],
                )
            views.append(view)
        if not collection_ok:
            endpoint.update(status="withheld_collection_contract", raw_p=None)
            endpoint.pop("randomization", None)
        primary.append(endpoint)
    adjusted = holm([r["raw_p"] if r["raw_p"] is not None else 1.0 for r in primary])
    for row, p in zip(primary, adjusted, strict=True):
        row.update(
            holm_p=float(p), reject=bool(row["status"] == "available" and p <= config["alpha"])
        )
    return dict(
        schema="painter-clause-validation-analysis/1",
        run_id=config["run_id"],
        scope="Prospective fixed new-scene actual-clause comparison; two primary paired "
        "sharp-null tests with Holm adjustment. No population or perceptual inference. "
        "Fixed historical maps, variance and retrieval are descriptive secondary analyses.",
        config=config,
        primary=primary,
        views=views,
        collection=collection_receipt,
        delivery=delivery_summary(rows),
        planned=len(requests),
        measured_by_pipeline={
            p: sum(r["pipeline"] == p and r["status"] == "measured" for r in rows)
            for p in common.PIPELINES
        },
    )


def report_text(value):
    lines = [
        "# Prospective painter-clause validation",
        "",
        value["scope"],
        "",
        "All four clauses retain the same new scene text. No palette extremes are used.",
        "",
        "| Painter | Named minus generic energy | Holm p | Status |",
        "|---|---:|---:|---|",
    ]
    for row in value["primary"]:
        estimate = "unavailable" if row["estimate"] is None else f"{row['estimate']:.9f}"
        lines.append(
            f"| {row['painter_id']} | {estimate} | {row['holm_p']:.5f} | {row['status']} |"
        )
    lines += [
        "",
        "No non-rejection establishes equivalence. Randomization inference assumes the "
        "sharp joint availability/feature null and no interference, conditional on the "
        "other two clause positions. It is not a fixed-map superiority test.",
        "",
        "| Pipeline | Painter | Free energy | Generic energy | Named energy | Shift | Scale |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for view in value["views"]:
        arm = next(k for k, v in common.PAINTERS.items() if v == view["painter_id"])
        energies = [
            view["arms"][k].get("distribution", {}).get("energy_distance")
            for k in ("free", "generic", arm)
        ]
        energies += [
            view["maps"].get(k, {}).get("energy_terms", {}).get("energy")
            for k in ("translation", "translation_scale")
        ]
        cells = ["unavailable" if e is None else f"{e:.6f}" for e in energies]
        lines.append(f"| {view['pipeline']} | {view['painter_id']} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Historical maps use only the original OAuth training outputs, not the new "
        "generated images or reference-feature objectives. No map is refitted. Corrected "
        "variance/residual estimates assume stable independent repeat errors; negative "
        "estimates are retained. Retrieval has equal scene/query weights. The complete JSON "
        "retains contributions, per-scene terms, predictions and missingness.",
        "",
    ]
    lines += [
        "| Pipeline | Painter | G/F trace | N/G trace | T2 minus T1 energy | T2 minus T1 Q |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for view in value["views"]:
        numbers = [
            view["trace_ratios"][k]["ratio"] for k in ("generic_over_free", "named_over_generic")
        ]
        numbers += [
            view["map_target_differences"].get(k)
            for k in ("energy_t2_minus_t1", "conditional_residual_t2_minus_t1")
        ]
        cells = ["unavailable" if n is None else f"{n:.6f}" for n in numbers]
        lines.append(f"| {view['pipeline']} | {view['painter_id']} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Observed-trace ratios use reference-content weights. No secondary test or interval "
        "is added. Undefined ratios and incomplete inputs remain unavailable.",
        "",
        "## Recorded delivery by arm",
        "",
    ]
    for arm, row in value["delivery"].items():
        lines.append(
            f"- {arm}: {row['planned']} allocated; statuses {row['statuses']}; "
            f"dimensions {row['dimensions']}; formats {row['formats']}; "
            f"reported quality {row['reported_quality']}."
        )
    lines += [
        "",
        "Reported quality is a service field; no output is adjusted or excluded using it.",
        "",
    ]
    return "\n".join(lines)
