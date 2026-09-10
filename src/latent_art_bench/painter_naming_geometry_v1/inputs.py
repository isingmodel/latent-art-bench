"""Compact numerical inventory; never open pixels, responses or model endpoints."""

from collections import Counter
from pathlib import Path

import numpy as np

PAINTERS = ("claude_monet", "paul_cezanne")
ROUTES = ("nano_banana_2", "flux_2_max", "oauth_gpt_image_2")
PIPELINES = ("primary512", "resolution256", "jpeg90_512")
ORIGINS = (
    Path("data/manifests/paper_reproducibility_v1/pprv1-20260910/inputs.json"),
    Path("data/manifests/paper_reproducibility_v1/pprv1-20260910/replication_inputs.json"),
    Path("data/manifests/painter_measurement_validation_v1/pmvv1-20260910/features.jsonl"),
)


def scale(values, scaler):
    center, spread = np.asarray(scaler["center"]), np.asarray(scaler["scale"])
    values = np.asarray(values, dtype=float)
    if (center.shape != (31,) or spread.shape != (31,) or np.any(spread <= 0)
            or not np.isfinite(center).all() or not np.isfinite(spread).all()):
        raise ValueError("invalid fixed scaler")
    if values.ndim < 1 or values.shape[-1] != 31 or not np.isfinite(values).all():
        raise ValueError("invalid feature vectors")
    result = (values - center) / spread
    if not np.isfinite(result).all():
        raise ValueError("invalid feature vectors")
    return result.tolist()


def cube(rows, scene_field, repetitions, scaler):
    scenes = sorted({r[scene_field] for r in rows})
    if len(scenes) != 24 or len(rows) != 24 * repetitions:
        raise ValueError("complete fixed 24-scene allocation required")
    by_key = {(r[scene_field], r["repetition"]): r for r in rows}
    if (len(by_key) != len(rows) or len({r["image_id"] for r in rows}) != len(rows)
            or any(r["status"] != "measured" for r in rows)):
        raise ValueError("duplicate scene/repeat identity")
    repeat_ids = sorted({r["repetition"] for r in rows})
    if repeat_ids != list(range(repetitions)):
        raise ValueError("unexpected repeat allocation")
    ordered = [[by_key[s, r] for r in repeat_ids] for s in scenes]
    classes = [group[0]["content_class"] for group in ordered]
    if Counter(classes) != dict.fromkeys(("built", "land", "water"), 8):
        raise ValueError("unexpected fixed class allocation")
    if any(r["content_class"] != c for group, c in zip(ordered, classes) for r in group):
        raise ValueError("scene content class changed within repeats")
    return dict(
        scene_ids=scenes, classes=classes, repeat_ids=repeat_ids,
        ids=[[r["image_id"] for r in group] for group in ordered],
        values=scale([[r["values"] for r in group] for group in ordered], scaler),
    )


def paired(free, named):
    for key in ("scene_ids", "classes", "repeat_ids"):
        if free[key] != named[key]:
            raise ValueError("free/named scene-repeat mismatch")
    return {**{k: free[k] for k in ("scene_ids", "classes", "repeat_ids")},
            "free": free["values"], "named": named["values"],
            "free_ids": free["ids"], "named_ids": named["ids"]}


def assemble(study, later, square):
    """Select every detailed pair, without feature-dependent admission."""
    pipelines = tuple(study["scalers"])
    if set(pipelines) != set(PIPELINES):
        raise ValueError("three fixed pipelines required")
    baseline = [r for r in square if r["condition"] == "baseline"]
    square_by_id = {(r["stage"], r["image_id"]): r for r in baseline}
    expected_square = {(stage, r["image_id"]): r["painter_id"]
                       for stage in ("reference", "generated")
                       for r in study[stage] if r["pipeline"] == "primary512"}
    if (len(baseline) != 1076 or len(square_by_id) != 1076
            or set(square_by_id) != set(expected_square)
            or any(square_by_id[k]["painter_id"] != p for k, p in expected_square.items())):
        raise ValueError("incomplete common-square inventory")
    result = dict(schema="painter-naming-geometry-inputs/1", targets=study["targets"],
                  original={}, later={}, reference={}, scalers=study["scalers"])
    for pipeline in (*pipelines, "common_square"):
        base = "primary512" if pipeline == "common_square" else pipeline
        scaler = study["scalers"][base]["scaler"]
        refs = [r for r in study["reference"] if r["pipeline"] == base]
        generated = [r for r in study["generated"] if r["pipeline"] == base]
        if pipeline == "common_square":
            refs = [dict(r, values=square_by_id["reference", r["image_id"]]["values"])
                    for r in refs]
            generated = [dict(r, values=square_by_id["generated", r["image_id"]]["values"])
                         for r in generated]
        result["reference"][pipeline] = {}
        result["original"][pipeline] = {}
        for painter in PAINTERS:
            selected = sorted([r for r in refs if r["painter_id"] == painter],
                              key=lambda r: r["image_id"])
            if (len(selected) != (38 if painter == PAINTERS[0] else 32)
                    or len({r["image_id"] for r in selected}) != len(selected)):
                raise ValueError("reference membership count changed")
            result["reference"][pipeline][painter] = dict(
                ids=[r["image_id"] for r in selected],
                values=scale([r["values"] for r in selected], scaler),
            )
        for route in ROUTES:
            result["original"][pipeline][route] = {}
            for painter in PAINTERS:
                arms = {}
                for condition, key in (("artist_free", "free"), ("named", "named")):
                    rows = [r for r in generated if r["route"] == route
                            and r["painter_id"] == painter and r["condition"] == condition]
                    arms[key] = cube(rows, "brief_id", 3, scaler)
                result["original"][pipeline][route][painter] = paired(**arms)
        if pipeline == "common_square":
            continue
        result["later"][pipeline] = {}
        for arm, painter in zip(("monet", "cezanne"), PAINTERS):
            arms = {}
            for source, key in (("free", "free"), (arm, "named")):
                rows = [r for r in later["rows"] if r["pipeline"] == pipeline
                        and r["experiment"] == "naming" and r["arm"] == source]
                if any(r["route"] != "flux_2_max" for r in rows):
                    raise ValueError("later naming requires the fixed FLUX route")
                arms[key] = cube(rows, "template_id", 1, scaler)
            result["later"][pipeline][painter] = paired(**arms)
            for key in ("scene_ids", "classes"):
                if (result["later"][pipeline][painter][key]
                        != result["original"][pipeline]["flux_2_max"][painter][key]):
                    raise ValueError("later cohort changed fixed scene identities/classes")
    return result
