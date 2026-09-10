"""Equalize recorded reference content classes without changing generated data."""

from __future__ import annotations

import argparse
import itertools
import subprocess
from pathlib import Path

import numpy as np

from latent_art_bench.painter_specificity_v1.analysis import centered, geometry, interval
from latent_art_bench.painter_specificity_v2 import study as s
from latent_art_bench.painter_specificity_v2.analysis import load

NS = "painter_specificity_reference_v1"
DATA = s.ROOT / "data/manifests" / NS / "psrv1-20260911"
FRAME = s.ROOT / "data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl"
CLASSES = ("water_organized", "built_place_organized", "route_organized", "open_or_wooded_land")


def class_means(values, labels):
    labels = np.asarray(labels)
    if len(values) != len(labels) or set(labels) != set(CLASSES):
        raise ValueError("all four recorded content classes are required")
    return np.array([values[labels == c].mean(axis=0) for c in CLASSES])


def evaluate(x, refs, labels):
    if np.shape(x) != (6, len(s.SCENES), 2, 6, 31) or len(refs) != 4 or len(labels) != 4:
        raise ValueError("incomplete model/scene/reference layout")
    means = np.array([class_means(v, c).mean(axis=0) for v, c in zip(refs, labels)])
    r = centered(means)
    old = centered(np.array([v.mean(axis=0) for v in refs]))
    h, old_h = np.sum(r * r), np.sum(old * old)
    if h <= 0 or old_h <= 0:
        raise ValueError("reference target has zero artist contrast")
    result = dict(
        counts=[{c: int(np.sum(np.asarray(lab) == c)) for c in CLASSES} for lab in labels],
        reference_means=means.tolist(),
        reference_sum_squares=float(h),
        unweighted_reference_sum_squares=float(old_h),
        target_cosine=float(np.sum(r * old) / np.sqrt(h * old_h)),
        models=[],
        comparisons=[],
        interpretation="descriptive target sensitivity; no new confirmatory family",
    )
    errors = np.full((6, len(s.SCENES)), np.nan)
    for m in range(6):
        good = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
        g = geometry(x[m, good, :, 2:], [a[None] for a in means]) if good.any() else None
        if g:
            errors[m, good] = g["distortion"]
        result["models"].append(
            dict(
                model=s.MODELS[m],
                complete_scenes=np.flatnonzero(good).tolist(),
                beta=interval(g["beta"]) if g else None,
                distortion=interval(g["distortion"]) if g else None,
                amplitude_error=float(g["amplitude_error"].mean()) if g else None,
                off_axis_error=float(g["off_axis_error"].mean()) if g else None,
            )
        )
    for a, b in itertools.combinations(range(6), 2):
        good = np.isfinite(errors[[a, b]]).all(axis=0)
        result["comparisons"].append(
            dict(
                model_a=s.MODELS[a],
                model_b=s.MODELS[b],
                **interval(errors[a, good] - errors[b, good]),
            )
        )
    # Reference uncertainty conditional on the recorded class coding; generated outputs fixed.
    rng = np.random.default_rng(2026091101)
    draws = []
    for ref, lab in zip(refs, labels):
        lab = np.asarray(lab)
        cls = []
        for c in CLASSES:
            values = ref[lab == c]
            cls.append(
                rng.multinomial(len(values), np.ones(len(values)) / len(values), size=1000)
                @ values
                / len(values)
            )
        draws.append(np.mean(cls, axis=0))
    targets = centered(np.stack(draws, axis=1))
    hs = np.sum(targets * targets, axis=(1, 2))
    for m, item in enumerate(result["models"]):
        good = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
        if not good.any():
            item["reference_resampling"] = None
            continue
        d = centered(x[m, good, :, 2:])
        mean_sum = d.sum(axis=1).mean(axis=0)
        cross = np.sum(d[:, 0] * d[:, 1], axis=(1, 2)).mean()
        beta = np.einsum("aj,baj->b", mean_sum / 2, targets) / hs
        distortion = (cross - np.einsum("aj,baj->b", mean_sum, targets) + hs) / hs
        item["reference_resampling"] = dict(
            beta_ci95=np.quantile(beta, [0.025, 0.975]).tolist(),
            distortion_ci95=np.quantile(distortion, [0.025, 0.975]).tolist(),
        )
    return result


def freeze():
    paths = [
        s.ROOT / "studies" / NS / "PROTOCOL.md",
        FRAME,
        s.REF,
        s.SCALER,
        s.DATA / "freeze.json",
        Path(__file__),
        s.ROOT / "tests" / NS / "test_reference.py",
    ]
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *map(str, paths)], text=True
    )
    if dirty.strip():
        raise ValueError("commit inputs before freeze")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    s.write_new(
        DATA / "freeze.json",
        dict(
            recorded_git_commit=commit,
            inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths],
        ),
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("freeze", "run", "check"))
    parser.add_argument("--square", action="store_true")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
        return
    for row in s.read(DATA / "freeze.json")["inputs"]:
        if s.sha(s.ROOT / row["path"]) != row["sha256"]:
            raise ValueError("reference sensitivity input changed")
    x, refs = load(args.square)
    records = s.rows(s.REF)
    frame = {r["work_id"]: r["content_class"] for r in s.rows(FRAME)}
    labels = [[frame[r["image_id"]] for r in records if r["painter_id"] == a] for a in s.ARTISTS]
    result = evaluate(x, refs, labels)
    result["measurement_receipt_sha256"] = s.sha(s.DATA / "measurement_receipt.json")
    result["freeze_sha256"] = s.sha(DATA / "freeze.json")
    path = DATA / ("analysis_square.json" if args.square else "analysis.json")
    if args.action == "check":
        if s.read(path) != result:
            raise ValueError("reference sensitivity replay differs")
        print("Exact reference sensitivity replay passed")
    else:
        s.write_new(path, result)
        print("Reference sensitivity saved")


if __name__ == "__main__":
    main()
