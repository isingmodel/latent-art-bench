"""One fresh Cezanne/generic finite-panel contrast and limited descriptive summaries.

The 48 independently assigned two-position blocks support a paired sharp-null
test, conditional on the fixed panel, references, weights and prior availability
trigger. Neither equal energy alone nor complete observations establishes that
null's joint availability/feature and no-interference assumptions. No latent
style interpretation, population interval, refilling or predecessor pooling is
implemented here. All traces are observed population-form weighted traces.
"""

import re
from collections import Counter

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.painter_distribution_study_v1.inference import paired_contributions
from latent_art_bench.painter_prompt_study_v1.randomization import randomization_pvalue

from . import common

DRAW_COUNT = 99999
TARGET = dict(built=11 / 32, land=18 / 32, water=3 / 32)
IDENTITY_FIELDS = (
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


def _matrix(value, shape):
    array = np.asarray(value)
    if array.dtype.kind not in "iuf" or array.shape != shape:
        raise ValueError("expected finite numeric vectors with the fixed dimensions")
    array = array.astype(float)
    if not np.isfinite(array).all():
        raise ValueError("expected finite numeric vectors with the fixed dimensions")
    return array


def validate_inputs(inputs):
    if (
        set(inputs) != {"schema", "origin", "targets", "reference", "scalers"}
        or inputs["schema"] != "painter-clause-successor-inputs/1"
    ):
        raise ValueError("unexpected successor numerical input schema")
    origin = inputs["origin"]
    if (
        not isinstance(origin, dict)
        or set(origin) != {"path", "sha256"}
        or origin["path"] != "studies/painter_clause_validation_v1/inputs.json"
        or not isinstance(origin["sha256"], str)
        or not re.fullmatch("[a-f0-9]{64}", origin["sha256"])
    ):
        raise ValueError("fixed predecessor numerical origin required")
    if inputs["targets"] != {common.PAINTER_ID: TARGET}:
        raise ValueError("fixed Cezanne reference content masses changed")
    for field in ("reference", "scalers"):
        if set(inputs[field]) != set(common.PIPELINES):
            raise ValueError("all three fixed pipelines required")
    for pipe in common.PIPELINES:
        if set(inputs["reference"][pipe]) != {common.PAINTER_ID}:
            raise ValueError("only the fixed Cezanne reference is allowed")
        ref = inputs["reference"][pipe][common.PAINTER_ID]
        ids = ref["ids"]
        if (
            len(ids) != 32
            or any(not isinstance(i, str) or not i for i in ids)
            or len(set(ids)) != 32
            or ("n" in ref and (type(ref["n"]) is not int or ref["n"] != 32))
        ):
            raise ValueError("fixed reference membership is incomplete or duplicated")
        _matrix(ref["values"], (32, 31))
        scaler = inputs["scalers"][pipe]["scaler"]
        _matrix(scaler["center"], (31,))
        if np.any(_matrix(scaler["scale"], (31,)) <= 0):
            raise ValueError("fixed scaler must have positive coordinates")


def validate_design(requests, config):
    fixed = dict(
        run_id=common.RUN_ID,
        maximum_images=96,
        repetitions=2,
        scenes_per_class=8,
        assignment_seed=2026091051,
        analysis_seed=2026091052,
        alpha=0.025,
    )
    if any(config.get(k) != v or type(config.get(k)) is not type(v) for k, v in fixed.items()):
        raise ValueError("the single fixed 96-output successor configuration is required")
    if (
        len(requests) != 96
        or any(not isinstance(r["request_id"], str) or not r["request_id"] for r in requests)
        or len({r["request_id"] for r in requests}) != 96
        or [r["sequence"] for r in requests] != list(range(96))
    ):
        raise ValueError("complete ordered prospective request inventory required")
    slots, scene_classes, block_ids = {}, {}, set()
    for pos in range(0, 96, 2):
        group = requests[pos : pos + 2]
        first = group[0]
        if (
            {r["arm"] for r in group} != set(common.ARMS)
            or [r["within_block"] for r in group] != [0, 1]
            or not isinstance(first["block_id"], str)
            or not first["block_id"]
            or first["block_id"] in block_ids
        ):
            raise ValueError("each randomized block must have two unique clause positions")
        block_ids.add(first["block_id"])
        for row in group:
            if (
                row["route"] != "oauth_gpt_image_2"
                or row["experiment"] != "clause_successor"
                or row["polarity"] is not None
                or row["block_order"] != pos // 2 + 1
                or not isinstance(row["template_id"], str)
                or not row["template_id"]
                or any(
                    type(row[k]) is not int
                    for k in ("sequence", "block_order", "within_block", "repetition")
                )
                or any(
                    row[k] != first[k]
                    for k in ("block_id", "template_id", "content_class", "repetition")
                )
            ):
                raise ValueError("assigned block or route identity differs")
            key = row["template_id"], row["repetition"], row["arm"]
            if key in slots or row["repetition"] not in range(2):
                raise ValueError("duplicate or unknown scene/repeat/clause")
            slots[key] = row
            old_class = scene_classes.setdefault(row["template_id"], row["content_class"])
            if old_class != row["content_class"]:
                raise ValueError("scene class changes across blocks")
    if Counter(scene_classes.values()) != dict.fromkeys(common.CLASSES, 8):
        raise ValueError("all 24 prospective scenes and classes are required")
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
            row.get(k) != source[k] or type(row.get(k)) is not type(source[k])
            for k in IDENTITY_FIELDS
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


def summary(reference, generated, weights):
    """Weighted V-energy and observed traces; self distances remain in the V sums."""
    reference_weights = np.full(len(reference), 1 / len(reference))
    energy = (
        2 * reference_weights @ cdist(reference, generated) @ weights
        - reference_weights @ cdist(reference, reference) @ reference_weights
        - weights @ cdist(generated, generated) @ weights
    )
    reference_trace = float(
        reference_weights @ np.square(reference - reference_weights @ reference).sum(axis=1)
    )
    generated_trace = float(weights @ np.square(generated - weights @ generated).sum(axis=1))
    if not np.isfinite([energy, reference_trace, generated_trace]).all():
        raise ValueError("nonfinite weighted energy or observed trace")
    return dict(
        energy_distance=float(energy),
        reference_trace=reference_trace,
        generated_trace=generated_trace,
        generated_reference_trace_ratio=(
            generated_trace / reference_trace if reference_trace > 0 else None
        ),
        reference_trace_ratio_status=(
            "descriptive" if reference_trace > 0 else "unavailable_zero_denominator"
        ),
    )


def trace_ratio(arms):
    if any(arms[a]["status"] != "descriptive" for a in common.ARMS):
        return dict(status="unavailable_incomplete_arm", ratio=None)
    bottom = arms["generic"]["generated_trace"]
    if bottom <= 0:
        return dict(status="unavailable_zero_denominator", ratio=None)
    return dict(status="descriptive", ratio=arms["cezanne"]["generated_trace"] / bottom)


def delivery_summary(rows):
    """Count each output once; reported quality is only a service metadata field."""
    result = {}
    for arm in common.ARMS:
        selected = [r for r in rows if r["arm"] == arm and r["pipeline"] == "primary512"]
        observed = [r["observed"] for r in selected if r.get("observed") is not None]
        result[arm] = dict(
            planned=len(selected),
            statuses=dict(Counter(r["status"] for r in selected)),
            observed_outputs=len(observed),
            dimensions=dict(Counter(f"{r['width']}x{r['height']}" for r in observed)),
            formats=dict(Counter(r["format"] for r in observed)),
            reported_quality=dict(
                Counter(str(r.get("reported", {}).get("quality") or "unreported") for r in observed)
            ),
            scope="Recorded delivery metadata without quality measurement or filtering",
        )
    return result


def analyze(requests, rows, inputs, config, *, collection_receipt=None):
    validate_inputs(inputs)
    slots, scene_classes = validate_design(requests, config)
    by_id = validate_measurements(requests, rows, inputs)
    scene_ids = sorted(scene_classes)
    classes = [scene_classes[s] for s in scene_ids]
    weights = np.repeat([TARGET[c] / 16 for c in classes], 2)
    collection_ok = (
        isinstance(collection_receipt, dict)
        and collection_receipt.get("duration_contract_met") is True
        and collection_receipt.get("identity_contract_met") is True
        and type(collection_receipt.get("planned")) is int
        and collection_receipt["planned"] == 96
    )
    endpoint = dict(
        endpoint="cezanne_minus_generic",
        painter_id=common.PAINTER_ID,
        estimate=None,
        raw_p=None,
        status="withheld_incomplete_allocated_grid",
        pairs=48,
        alpha=config["alpha"],
        reject=False,
    )
    views = []
    for pipe in common.PIPELINES:
        ref = inputs["reference"][pipe][common.PAINTER_ID]
        x = np.asarray(ref["values"], dtype=float)
        matrices, arm_summaries = {}, {}
        for arm in common.ARMS:
            selected = [
                by_id[slots[s, r, arm]["request_id"], pipe] for s in scene_ids for r in range(2)
            ]
            if any(r["status"] != "measured" for r in selected):
                arm_summaries[arm] = dict(status="withheld_incomplete_allocated_arm")
                continue
            y = np.asarray([r["scaled"] for r in selected], dtype=float)
            matrices[arm] = y
            arm_summaries[arm] = dict(
                status="descriptive",
                generated_n=48,
                generated_ids=[r["request_id"] for r in selected],
                **summary(x, y, weights),
            )
        views.append(
            dict(
                painter_id=common.PAINTER_ID,
                pipeline=pipe,
                scene_ids=scene_ids,
                scene_classes=classes,
                generated_weights=weights.tolist(),
                reference_ids=ref["ids"],
                arms=arm_summaries,
                named_generic_trace_ratio=trace_ratio(arm_summaries),
            )
        )
        if pipe == "primary512" and set(matrices) == set(common.ARMS):
            contributions = paired_contributions(
                x,
                matrices["generic"],
                matrices["cezanne"],
                pair_weights=weights,
            )
            estimate = float(contributions.sum())
            if not np.isfinite(contributions).all() or not np.isfinite(estimate):
                raise ValueError("nonfinite energy contributions")
            endpoint.update(
                estimate=estimate,
                contributions=contributions.tolist(),
                ordered_pairs=[
                    slots[s, r, "cezanne"]["block_id"] for s in scene_ids for r in range(2)
                ],
            )
            if collection_ok:
                tested = randomization_pvalue(
                    contributions,
                    seed=config["analysis_seed"],
                    draws=DRAW_COUNT,
                )
                endpoint.update(
                    status="available",
                    raw_p=tested["raw_p"],
                    randomization=tested,
                    reject=bool(tested["raw_p"] <= config["alpha"]),
                )
    if not collection_ok:
        endpoint.update(status="withheld_collection_contract")
    return dict(
        schema="painter-clause-successor-analysis/1",
        run_id=config["run_id"],
        scope="Fresh, fixed-panel Cezanne versus generic clause comparison, triggered by "
        "predecessor Cezanne availability failure before feature inspection. One 48-pair "
        "two-sided sharp-null test at alpha 0.025; no new-family Holm adjustment, pooling, "
        "refilling, population or perceptual inference. Only observed weighted energy and "
        "trace summaries are secondary.",
        config=config,
        input_origin=inputs["origin"],
        primary=[endpoint],
        views=views,
        collection=collection_receipt,
        delivery=delivery_summary(rows),
        planned=96,
        measured_by_pipeline={
            p: sum(r["pipeline"] == p and r["status"] == "measured" for r in rows)
            for p in common.PIPELINES
        },
    )


def report_text(value):
    def number(value, digits=6):
        return "unavailable" if value is None else f"{value:.{digits}f}"

    row = value["primary"][0]
    lines = [
        "# Fresh Cezanne–generic clause successor",
        "",
        value["scope"],
        "",
        "All 24 predecessor scene briefs are retained, including the refused scene. "
        "Both clauses are generated afresh in two independently randomized blocks per "
        "scene; 96 outputs and 48 matched pairs. No further replacement is permitted.",
        "",
        "| Contrast | Cezanne minus generic energy | Raw p | Alpha | Reject | Status |",
        "|---|---:|---:|---:|---|---|",
        f"| Cezanne − generic | {number(row['estimate'], 9)} | {number(row['raw_p'], 5)} "
        f"| {row['alpha']:.3f} | {row['reject']} | {row['status']} |",
        "",
        "The original Cezanne primary remains unavailable permanently; its missing cell "
        "is neither filled nor pooled with this cohort. Original Monet Holm-two inference "
        "remains unchanged. A joint error bound of 0.05 for the original Monet decision "
        "and this test requires both applicable tests to be valid at level 0.025, including "
        "validity conditional on the prior availability-triggered decision. The sum of "
        "nominal levels does not establish these assumptions.",
        "",
        "Inference requires the sharp joint availability/feature no-clause-effect null "
        "and no interference, or joint invariance under all independent within-block "
        "clause swaps. Equal energy alone is insufficient. Complete measurements do not "
        "validate service or selection assumptions. No non-rejection establishes "
        "equivalence. No effect interval is provided.",
        "",
        "| Pipeline | Arm | Energy | Reference trace | Generated trace | Gen/ref trace |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for view in value["views"]:
        for arm in common.ARMS:
            summary = view["arms"][arm]
            cells = [
                number(summary.get(k))
                for k in (
                    "energy_distance",
                    "reference_trace",
                    "generated_trace",
                    "generated_reference_trace_ratio",
                )
            ]
            lines.append(f"| {view['pipeline']} | {arm} | " + " | ".join(cells) + " |")
    lines += ["", "| Pipeline | Cezanne/generic trace | Status |", "|---|---:|---|"]
    for view in value["views"]:
        ratio = view["named_generic_trace_ratio"]
        lines.append(f"| {view['pipeline']} | {number(ratio['ratio'])} | {ratio['status']} |")
    lines += [
        "",
        "Each generated observation has its reference class mass divided by 16; "
        "reference observations have equal weight 1/32. These are all-31-coordinate "
        "V-energy and observed population-form trace summaries, conditional on this "
        "finite scene/reference panel. They are not corrected latent variances or "
        "perceptual style measures. Each arm summary needs its complete allocated arm; "
        "ratios with incomplete inputs or zero denominators remain unavailable. No "
        "secondary test or interval is added.",
        "",
        "The JSON retains assigned-pair contributions, reference and generated IDs, "
        "weights, terminal measurement counts and the collection receipt. A complete "
        "primary estimate survives a failed global collection gate descriptively, but "
        "its p-value and rejection are withheld.",
        "",
    ]
    lines += ["## Recorded delivery by arm", ""]
    for arm, delivered in value["delivery"].items():
        lines.append(
            f"- {arm}: {delivered['planned']} allocated; statuses {delivered['statuses']}; "
            f"dimensions {delivered['dimensions']}; formats {delivered['formats']}; "
            f"reported quality {delivered['reported_quality']}."
        )
    lines += [
        "",
        "Reported quality is a service field; no output is adjusted or excluded using it.",
        "",
    ]
    return "\n".join(lines)
