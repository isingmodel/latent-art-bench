"""Two fixed-map endpoints on a complete prospectively allocated scene panel.

The unchanged qualified primitives operate on observed paired draws here; those
draws are not treated as a fitted discrete population and no exact-truth function
is called. Maps, references and standardization remain fixed historical inputs.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import t

from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_map_validation_v1 import precision as primitive

PIPELINE = "primary512"
PAINTER = "paul_cezanne"
REPEATS = 10
SCENE_IDS = tuple(f"pmv2_{c}{i:02d}" for c in primitive.CLASSES for i in range(1, 5))
IDENTITY_FIELDS = (
    "sequence",
    "experiment",
    "route",
    "template_id",
    "content_class",
    "repetition",
    "arm",
    "painter_id",
    "block_id",
    "block_order",
    "within_block",
)
ORIGINS = {
    str(primitive.INPUT_PATH): primitive.INPUT_HASH,
    str(primitive.ANALYSIS_PATH): primitive.ANALYSIS_HASH,
}


def load_inputs(root):
    """Extract compact old inputs after checking both immutable origin hashes."""
    values = []
    for relative, expected in ORIGINS.items():
        data = (Path(root) / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"historical input hash differs: {relative}")
        values.append(json.loads(data))
    old, results = values
    selected = [
        row
        for row in results["transfer"]
        if row["pipeline"] == PIPELINE and row["view"] == "all31" and row["painter"] == PAINTER
    ]
    if len(selected) != 1 or old["scalers"][PIPELINE]["status"] != "available":
        raise ValueError("unique available original full-cohort map and scaler required")
    result = dict(
        schema="painter-map-validation-inputs/2",
        origins=ORIGINS.copy(),
        pipeline=PIPELINE,
        painter_id=PAINTER,
        features=list(NAMES),
        targets=old["targets"][PAINTER],
        reference=old["reference"][PIPELINE][PAINTER],
        scaler=old["scalers"][PIPELINE]["scaler"],
        fitted=selected[0]["fitted"],
    )
    validate_inputs(result)
    return result


def validate_inputs(value):
    if (
        set(value)
        != {
            "schema",
            "origins",
            "pipeline",
            "painter_id",
            "features",
            "targets",
            "reference",
            "scaler",
            "fitted",
        }
        or value["schema"] != "painter-map-validation-inputs/2"
        or value["origins"] != ORIGINS
        or value["pipeline"] != PIPELINE
        or value["painter_id"] != PAINTER
        or value["features"] != list(NAMES)
        or value["targets"] != primitive.MASSES
    ):
        raise ValueError("fixed compact historical input contract differs")
    reference = value["reference"]
    ids = reference["ids"]
    if (
        set(reference) != {"ids", "values"}
        or len(ids) != 32
        or len(set(ids)) != 32
        or any(not isinstance(i, str) or not i for i in ids)
    ):
        raise ValueError("exactly 32 unique reference identities required")
    primitive.finite(reference["values"], (32, 31))
    primitive.finite(value["scaler"]["center"], (31,))
    if np.any(primitive.finite(value["scaler"]["scale"], (31,)) <= 0):
        raise ValueError("positive unchanged development scales required")
    primitive.maps(np.zeros((1, 31)), value["fitted"])
    if value["fitted"]["scale"] != 0.6785365094757265:
        raise ValueError("historical Cezanne scalar differs")


def _component_scores(free, named, reference, scene_weights, fitted):
    j, r, d = free.shape
    b = np.repeat(scene_weights / r, r)
    p = np.full(len(reference), 1 / len(reference))
    fixed = p @ cdist(reference, reference) @ p
    result = {}
    for key, transformed in zip(("T1", "T2"), primitive.maps(free, fitted), strict=True):
        y = transformed.reshape(j * r, d)
        result["energy_" + key] = float(
            2 * p @ cdist(reference, y) @ b - b @ cdist(y, y) @ b - fixed
        )
        residual = named - transformed
        dot = np.einsum("jrd,jsd->jrs", residual, residual)
        off_diagonal = dot.sum((1, 2)) - np.trace(dot, axis1=1, axis2=2)
        result["Q_" + key] = float(scene_weights @ off_diagonal / (r * (r - 1)))
    return result


def _empty_numerical(status):
    return dict(
        status=status,
        components=dict.fromkeys(("energy_T1", "energy_T2", "Q_T1", "Q_T2")),
        primary=[
            dict(
                endpoint=k,
                estimate=None,
                jackknife_variance=None,
                half_width=None,
                interval=None,
                status=status,
                direction="unavailable",
            )
            for k in ("deltaE", "deltaQ")
        ],
        deleted_estimates=None,
        joint_direction="unavailable",
        interval_family_size=2,
        nominal_simultaneous_coverage=0.95,
        degrees_of_freedom=9,
        critical_value=float(t.ppf(0.9875, 9)),
    )


def analyze_arrays(free, named, reference, scene_weights, fitted):
    """Observed R10 points and all paired deletions; no simulations or map refit.

    Smaller invented scene/dimension counts are supported for independent oracle
    tests. The study-facing wrapper enforces the actual 12 x 10 x 31 allocation.
    """
    free, named, reference = map(primitive.finite, (free, named, reference))
    if (
        free.ndim != 3
        or named.shape != free.shape
        or free.shape[1] != REPEATS
        or free.shape[0] < 2
        or free.shape[2] < 2
        or reference.ndim != 2
        or len(reference) < 1
        or reference.shape[1] != free.shape[2]
    ):
        raise ValueError("paired scene by ten by feature arrays and matching reference required")
    w = primitive.weights(scene_weights, free.shape[0])
    primitive.maps(np.zeros((1, free.shape[2])), fitted)
    result = _empty_numerical("unavailable_numerical_calculation")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            table = primitive.support_tables(free, named, reference, w, fitted)
            draws = np.broadcast_to(np.arange(REPEATS), (1, len(w), REPEATS)).copy()
            calculated = primitive.statistics(table, draws)
            components = _component_scores(free, named, reference, w, fitted)
            half, available = primitive.intervals(
                calculated["estimate"], calculated["variance"], REPEATS
            )
    except (FloatingPointError, ValueError):
        # Inputs were validated before this block. Extreme finite coordinates can
        # overflow intermediate norms; this is recorded, not silently trimmed.
        return result
    result["components"] = {k: float(v) if np.isfinite(v) else None for k, v in components.items()}
    result["status"] = (
        "approximate_simultaneous_intervals" if available[0] else "descriptive_points_only"
    )
    result["deleted_estimates"] = (
        calculated["deleted"][0].tolist() if np.isfinite(calculated["deleted"]).all() else None
    )
    for i, row in enumerate(result["primary"]):
        point, variance = calculated["estimate"][0, i], calculated["variance"][0, i]
        row.update(
            estimate=float(point) if np.isfinite(point) else None,
            jackknife_variance=float(variance) if np.isfinite(variance) else None,
            status=result["status"],
        )
        if available[0]:
            width = float(half[0, i])
            bounds = [float(point - width), float(point + width)]
            row.update(
                half_width=width,
                interval=bounds,
                direction="positive"
                if bounds[0] > 0
                else "negative"
                if bounds[1] < 0
                else "unresolved",
            )
    signs = [r["direction"] for r in result["primary"]]
    if signs == ["positive", "negative"]:
        result["joint_direction"] = "higher_reference_energy_lower_conditional_mean_error"
    elif available[0] and "unresolved" not in signs:
        result["joint_direction"] = "resolved_other_ordering"
    elif available[0]:
        result["joint_direction"] = "unresolved"
    return result


def validate_measurements(requests, rows, inputs):
    by_id, expected = {}, {r["request_id"]: r for r in requests}
    if len(expected) != 240 or len(rows) != 240:
        raise ValueError("all 240 allocated terminal measurement records required")
    center = primitive.finite(inputs["scaler"]["center"], (31,))
    scale = primitive.finite(inputs["scaler"]["scale"], (31,))
    for row in rows:
        rid = row["request_id"]
        if rid not in expected or rid in by_id or row["pipeline"] != PIPELINE:
            raise ValueError("unknown, duplicate or unexpected pipeline measurement")
        if any(
            type(row.get(k)) is not type(expected[rid][k]) or row.get(k) != expected[rid][k]
            for k in IDENTITY_FIELDS
        ):
            raise ValueError("measurement identity differs from prospective assignment")
        if row.get("feature_names") != list(NAMES):
            raise ValueError("measurement feature order differs")
        if not isinstance(row.get("status"), str) or not row["status"]:
            raise ValueError("terminal measurement status required")
        if row["status"] == "measured":
            raw = primitive.finite(row["values"], (31,))
            scaled = primitive.finite(row["scaled"], (31,))
            if not np.array_equal(scaled, (raw - center) / scale):
                raise ValueError(
                    "scaled measurement differs from unchanged development transformation"
                )
        elif row.get("values") is not None or row.get("scaled") is not None:
            raise ValueError("unavailable measurement carries a feature vector")
        by_id[rid] = row
    return by_id


def analyze(requests, rows, inputs, config, *, collection_receipt):
    from . import common

    common.validate_design(requests, config)
    validate_inputs(inputs)
    by_id = validate_measurements(requests, rows, inputs)
    eligible = collection_receipt.get("analysis_eligible")
    reasons = collection_receipt.get("analysis_unavailability_reasons")
    if (
        type(eligible) is not bool
        or not isinstance(reasons, list)
        or any(not isinstance(v, str) or not v for v in reasons)
        or eligible != (len(reasons) == 0)
    ):
        raise ValueError("verified collection eligibility and reasons required")
    reasons = reasons.copy()
    if any(row["status"] != "measured" for row in rows):
        reasons.append("incomplete_allocated_primary_vectors")
    numerical = _empty_numerical("unavailable_complete_grid")
    w = np.repeat([primitive.MASSES[c] / 4 for c in primitive.CLASSES], 4)
    slots = {(r["template_id"], r["repetition"], r["arm"]): r["request_id"] for r in requests}
    if len(slots) != 240:
        raise ValueError("duplicate scene/repeat/arm allocation")
    membership = [
        dict(
            scene_id=s,
            content_class=s.removeprefix("pmv2_")[:-2],
            weight=float(w[j]),
            pairs=[
                dict(
                    repetition=r,
                    artist_free_id=slots[s, r, "artist_free"],
                    named_id=slots[s, r, "named"],
                    image_weight=float(w[j] / REPEATS),
                )
                for r in range(REPEATS)
            ],
        )
        for j, s in enumerate(SCENE_IDS)
    ]
    if not reasons:
        arrays = [
            np.array(
                [[by_id[slots[s, r, arm]]["scaled"] for r in range(REPEATS)] for s in SCENE_IDS]
            )
            for arm in ("artist_free", "named")
        ]
        if any(a.shape != (12, 10, 31) for a in arrays):
            raise ValueError("complete planned scene arrays required")
        numerical = analyze_arrays(*arrays, inputs["reference"]["values"], w, inputs["fitted"])
    return dict(
        schema="painter-map-validation-analysis/2",
        run_id=config["run_id"],
        pipeline=PIPELINE,
        painter_id=PAINTER,
        features=list(NAMES),
        allocated_images=240,
        allocated_pairs=120,
        fixed_scenes=12,
        repeats=REPEATS,
        availability=dict(Counter(r["status"] for r in rows)),
        collection_eligible=eligible,
        unavailability_reasons=reasons,
        reference_ids=inputs["reference"]["ids"],
        reference_weights=[1 / 32] * 32,
        memberships=membership,
        fitted=inputs["fitted"],
        **numerical,
        targets=dict(
            deltaE="expected finite-R10 weighted empirical V-energy contrast",
            deltaQ="fixed-scene squared conditional-mean mismatch contrast",
        ),
        interpretation="Conditional on the old maps/scaler/references and these authored scenes. "
        "Approximate intervals assume independent stationary repeats; proxy "
        "qualification does not establish actual service coverage. No perceptual, "
        "capture, scene-population or internal-mechanism inference.",
    )


def report_text(value):
    lines = [
        "# Prospective fixed-map comparison on twelve new scene briefs",
        "",
        f"Run `{value['run_id']}`; status **{value['status']}**.",
        "240 allocated images, 120 pairs, ten repetitions per scene; FLUX/Cezanne, "
        "primary512 and all 31 unchanged features.",
        f"Terminal measurement counts: `{json.dumps(value['availability'], sort_keys=True)}`.",
        f"Unavailability reasons: `{json.dumps(value['unavailability_reasons'])}`.",
        "",
        "| Endpoint | T2−T1 | Approximate simultaneous 95% interval | Direction |",
        "| --- | ---: | --- | --- |",
    ]
    for row in value["primary"]:
        point = "unavailable" if row["estimate"] is None else f"{row['estimate']:.9f}"
        interval = (
            "unavailable"
            if row["interval"] is None
            else "[" + ", ".join(f"{x:.9f}" for x in row["interval"]) + "]"
        )
        lines.append(f"| {row['endpoint']} | {point} | {interval} | {row['direction']} |")
    lines += [
        "",
        f"Joint interpretation: `{value['joint_direction']}`.",
        "",
        "Component point values (interpretation aids; no component inference):",
        f"`{json.dumps(value['components'], sort_keys=True)}`.",
        "",
        "E uses unsquared standardized distance and targets expected finite-R10 empirical "
        "V-energy. Q uses squared standardized coordinates and the distinct-repeat "
        "correction for conditional scene means; negative values are retained.",
        "",
        "The paired within-scene delete-one jackknife preserves each scene's weight. "
        "Both intervals use t(9,.9875), with a nominal simultaneous 95% target. "
        "Nonpositive/nonfinite variance withholds both intervals. "
        "Incomplete or ineligible collection withholds all scientific summaries.",
        "",
        value["interpretation"],
        "",
        "Maintainer-run LLM design, implementation and review; not an independent "
        "human or institutional replication. Numerical replay does not authenticate "
        "absent image acquisition.",
        "",
    ]
    return "\n".join(lines)
