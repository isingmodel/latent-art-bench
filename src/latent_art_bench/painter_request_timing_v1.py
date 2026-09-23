"""Retrospective within-cell linear request drift; no collection or primary-score edits."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_measurement_v1.workflow import load
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_request_timing_v1"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS


def paired_arrays(requests, events, measurements, scaler):
    """Join actual start times to complete labeled repeat pairs, retaining signed gaps."""
    expected = 6 * len(s.SCENES) * 6 * 2
    starts = [v for v in events if v["kind"] == "start"]
    ends = [v for v in events if v["kind"] == "end"]
    req = {v["id"]: v for v in requests}
    start = {v["id"]: v for v in starts}
    end = {v["id"]: v for v in ends}
    measured = {v["id"]: v for v in measurements}
    if not (
        len(requests) == len(starts) == len(ends) == len(measurements) == expected
        and len(req) == len(start) == len(end) == len(measured) == expected
        and req.keys() == start.keys() == end.keys() == measured.keys()
    ):
        raise ValueError("exactly one complete attempt/measurement per request required")
    shape = (len(s.MODELS), len(s.SCENES), len(s.ARMS), 2)
    times = np.full(shape, np.nan)
    values = np.full((*shape, len(NAMES)), np.nan)
    ids = {}
    for key, r in req.items():
        if (
            start[key]["attempt"] != 1
            or end[key]["attempt"] != 1
            or not end[key]["success"]
            or measured[key]["status"] != "measured"
            or r["repeat"] not in (0, 1)
            or not 0 <= r["scene"] < len(s.SCENES)
        ):
            raise ValueError("incomplete or invalid request cell")
        cell = s.MODELS.index(r["model"]), r["scene"], s.ARMS.index(r["arm"]), r["repeat"]
        if cell in ids:
            raise ValueError("duplicate request cell")
        ids[cell] = key
        stamp = datetime.fromisoformat(start[key]["started_at"])
        if stamp.tzinfo is None:
            raise ValueError("timezone-aware request start required")
        times[cell] = stamp.timestamp() / 60
        values[cell] = transform(np.asarray(measured[key]["values"]), scaler)
    if not np.isfinite(times).all() or not np.isfinite(values).all():
        raise ValueError("all request cells must be present and finite")
    delta_t = times[..., 1] - times[..., 0]
    delta_z = values[..., 1, :] - values[..., 0, :]
    pair_records = [
        dict(
            model=s.MODELS[m], scene=scene, arm=s.ARMS[arm],
            repeat_0_id=ids[m, scene, arm, 0], repeat_1_id=ids[m, scene, arm, 1],
            gap_minutes=float(delta_t[m, scene, arm]),
        )
        for m in range(len(s.MODELS))
        for scene in range(len(s.SCENES))
        for arm in range(len(s.ARMS))
    ]
    return delta_t, delta_z, pair_records


def slope(gaps, differences):
    gaps, differences = np.asarray(gaps), np.asarray(differences)
    if (
        differences.shape[:-1] != gaps.shape
        or not np.isfinite(gaps).all()
        or not np.isfinite(differences).all()
        or np.square(gaps).sum() <= 0
    ):
        raise ValueError("finite paired differences with positive time variation required")
    return np.sum(gaps[..., None] * differences, axis=tuple(range(gaps.ndim))) / np.square(
        gaps
    ).sum()


def cross_validate(gaps, differences):
    """Each held-out scene has a slope fitted using only other scenes."""
    gaps, differences = np.asarray(gaps), np.asarray(differences)
    if gaps.ndim != 2 or differences.ndim != 3 or len(gaps) < 3:
        raise ValueError("at least three scenes of paired arm differences required")
    if differences.shape[:-1] != gaps.shape:
        raise ValueError("paired-difference dimensions disagree")
    predictions = np.empty_like(differences)
    folds = []
    for scene in range(len(gaps)):
        keep = np.arange(len(gaps)) != scene
        b = slope(gaps[keep], differences[keep])
        predictions[scene] = gaps[scene, :, None] * b
        folds.append(
            dict(
                held_out_scene_position=scene, training_pairs=int(keep.sum() * gaps.shape[1]),
                slope_iqr_per_minute=b.tolist(),
                mse_zero=float(np.square(differences[scene]).sum(axis=-1).mean()),
                mse_held_out=float(
                    np.square(differences[scene] - predictions[scene]).sum(axis=-1).mean()
                ),
            )
        )
    zero = float(np.square(differences).sum(axis=-1).mean())
    held = float(np.square(differences - predictions).sum(axis=-1).mean())
    return dict(
        mse_zero=zero, mse_held_out=held,
        predictive_gain_fraction=(zero - held) / zero if zero > 0 else None,
        observed_rms_repeat_difference=float(np.sqrt(zero)),
        held_out_rms_predicted_drift=float(np.sqrt(np.square(predictions).sum(axis=-1).mean())),
        folds=folds,
    )


def summarize(gaps, differences):
    result = cross_validate(gaps, differences)
    b = slope(gaps, differences)
    deletion = []
    for scene in range(len(gaps)):
        keep = np.arange(len(gaps)) != scene
        fit = cross_validate(gaps[keep], differences[keep])
        deletion.append(dict(deleted_scene=scene, gain_fraction=fit["predictive_gain_fraction"]))
    gains = [v["gain_fraction"] for v in deletion]
    return dict(
        pairs=int(gaps.size), slope_iqr_per_minute=b.tolist(),
        ten_minute_slope_norm=float(10 * np.linalg.norm(b)),
        absolute_gap_minutes=dict(
            minimum=float(np.abs(gaps).min()), median=float(np.median(np.abs(gaps))),
            maximum=float(np.abs(gaps).max()),
        ),
        scene_deletion_gain_range=[min(gains), max(gains)] if all(v is not None for v in gains)
        else None,
        scene_deletions=deletion, **result,
    )


def build():
    # Validate the original source bindings and complete feature census first.
    load()
    requests = s.rows(s.DATA / "requests.jsonl")
    events = s.rows(s.DATA / "attempts.jsonl")
    measured = s.rows(s.DATA / "measurements.jsonl")
    gaps, differences, pairs = paired_arrays(requests, events, measured, s.read(s.SCALER))
    starts = sorted((r for r in events if r["kind"] == "start"), key=lambda r: r["started_at"])
    request_lookup = {r["id"]: r for r in requests}
    blocks = []
    for event in starts:
        scene = request_lookup[event["id"]]["scene"]
        if not blocks or blocks[-1]["scene"] != scene:
            blocks.append(dict(scene=scene, count=0, first_start=event["started_at"]))
        blocks[-1]["count"] += 1
        blocks[-1]["last_start"] = event["started_at"]
    inputs = [
        PLAN, Path(__file__), s.DATA / "requests.jsonl", s.DATA / "attempts.jsonl",
        s.DATA / "measurements.jsonl", s.DATA / "collection.json", s.SCALER,
        s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/statistics.py",
        s.ROOT / "tests" / NS / "test_timing.py",
    ]
    return dict(
        schema="painter-request-timing/1.0", status="retrospective_descriptive",
        inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in inputs],
        feature_names=list(NAMES),
        timing=dict(
            planned_start_order_matches=[r["id"] for r in requests] == [r["id"] for r in starts],
            scene_blocks=blocks, positive_signed_gaps=int((gaps > 0).sum()),
            negative_signed_gaps=int((gaps < 0).sum()),
            global_time_confounded_with_scene=True,
        ),
        models=[dict(model=model, title=title, **summarize(gaps[m], differences[m]))
                for m, (model, title) in enumerate(zip(s.MODELS, s.TITLES))],
        pairs=pairs,
        interpretation=(
            "Held-out gain assesses a common linear short-window drift model; it does not "
            "test service independence or rule out nonlinear, arm-specific, or shared-state "
            "effects. "
            "Scene-deletion ranges are sensitivities, not confidence intervals. No primary scores "
            "are detrended or refit."
        ),
    )


def markdown(result):
    lines = [
        "# Retrospective within-cell request-timing diagnostic", "",
        "One common 31-coordinate linear drift vector is fitted per requested configuration. "
        "The 84 paired differences per configuration include all six arms. Stable scene/arm "
        "means cancel within each pair. Time is signed repeat-1 minus repeat-0 start time.", "",
        "| Configuration | 10-minute fitted slope norm | Repeat RMS | Predicted drift RMS | "
        "Held-out gain (%) | Scene-deletion gain range (%) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for m in result["models"]:
        low, high = m["scene_deletion_gain_range"]
        lines.append(
            f"| {m['title']} | {m['ten_minute_slope_norm']:.3f} | "
            f"{m['observed_rms_repeat_difference']:.3f} | "
            f"{m['held_out_rms_predicted_drift']:.3f} | "
            f"{100 * m['predictive_gain_fraction']:.2f} | {100 * low:.2f}, {100 * high:.2f} |"
        )
    lines += [
        "", "RMS quantities and the 10-minute slope norm use Euclidean combinations of "
        "development-IQR feature coordinates. The fitted slope norm can be inflated by noise. "
        "Predictive gain is `(MSE_zero - MSE_held_out) / MSE_zero`; negative values favor "
        "the zero-difference predictor. Each held-out scene uses a slope fitted on the other "
        "13 scenes. Scene deletion refits the entire procedure.", "",
        "## Interpretation limits", "", result["interpretation"], "",
        "The planned start order matches the observed start order. Scenes were contiguous "
        "blocks of 72 randomized requests, so global collection time is confounded with "
        "scene identity. Recorded repeat 1 was later in "
        f"{result['timing']['positive_signed_gaps']} pairs and earlier in "
        f"{result['timing']['negative_signed_gaps']} pairs. The dispatcher and service latency "
        "also affect elapsed gaps. These are descriptive associations, not causal time effects.",
        "",
        "There are no new hypothesis tests or confidence intervals. Overlapping folds are "
        "dependent, and the range of scene-deletion gains is not a confidence interval. "
        "A lack of predictive gain cannot establish stationarity or independent requests.", "",
        "## Replay", "", "`uv run --locked python -m "
        "latent_art_bench.painter_request_timing_v1 check`", "",
        "The adjacent analysis JSON retains plan/input hashes, all slopes, folds, deletions, "
        "signed gaps, and request-pair identities. No original data or primary score is changed.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("run", "check"))
    args = parser.parse_args()
    result = build()
    report = markdown(result)
    if args.action == "check":
        if result != s.read(OUT / "analysis.json") or report != (OUT / "REPORT.md").read_text():
            raise ValueError("timing diagnostic replay differs")
        print("Exact retrospective timing diagnostic replay passed")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        if (OUT / "analysis.json").exists() or (OUT / "REPORT.md").exists():
            raise FileExistsError("retain prior results; do not overwrite a completed diagnostic")
        with (OUT / "analysis.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        with (OUT / "REPORT.md").open("x") as stream:
            stream.write(report)
        print(report)


if __name__ == "__main__":
    main()
