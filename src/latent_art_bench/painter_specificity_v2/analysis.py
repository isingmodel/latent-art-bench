"""Replay the unchanged scientific estimands on the qualified model routes."""

from __future__ import annotations

import argparse
import itertools

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_v1.analysis import (
    clean,
    energy,
    fixed_effects,
    geometry,
    interval,
    reference_resampling,
    shared_diagnostics,
)

from . import study as s
from .workflow import verify


def compute(vectors, reference_values):
    """All model comparisons use identical retained reference coordinates."""
    x = np.asarray(vectors, dtype=float)
    if x.shape != (6, len(s.SCENES), 2, 6, 31):
        raise ValueError("expected six models, fourteen scenes, two repeats and six arms")
    result = dict(
        models=[],
        comparisons=[],
        sensitivities={},
        inference_family=21,
        uncertainty="paired scene t; fixed reference panel; Bonferroni 21",
    )
    beta = np.full((6, len(s.SCENES)), np.nan)
    distortion = np.full_like(beta, np.nan)
    rng = np.random.default_rng(2026091018)
    for m, model in enumerate(s.MODELS):
        good = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
        g = geometry(x[m, good, :, 2:], reference_values) if good.any() else None
        if g is not None:
            beta[m, good] = g["beta"]
            distortion[m, good] = g["distortion"]
        item = dict(
            model=model,
            title=s.TITLES[m],
            complete_scenes=np.flatnonzero(good).tolist(),
            beta=interval(beta[m]),
            distortion=interval(distortion[m]),
            global_distortion=g["global_distortion"] if g else None,
            amplitude_error=float(g["amplitude_error"].mean()) if g else None,
            off_axis_error=float(g["off_axis_error"].mean()) if g else None,
            scene_distortion=distortion[m].tolist(),
            scene_beta=beta[m].tolist(),
            shared=shared_diagnostics(x[m]),
            artists=[],
        )
        for a, artist in enumerate(s.ARTISTS):
            named = x[m, :, :, a + 2].reshape(-1, 31)
            named = named[np.isfinite(named).all(axis=1)]
            generic = x[m, :, :, 1].reshape(-1, 31)
            generic = generic[np.isfinite(generic).all(axis=1)]
            original = reference_values[a]
            if len(named) > 1:
                item["artists"].append(
                    dict(
                        artist=artist,
                        n=len(named),
                        energy=energy(named, original),
                        trace_ratio=float(
                            np.var(named, axis=0, ddof=1).sum()
                            / np.var(original, axis=0, ddof=1).sum()
                        ),
                        generic_energy=energy(generic, original) if len(generic) else None,
                    )
                )
        result["models"].append(item)
    common = np.isfinite(distortion).all(axis=0)
    result["reference_resampling"] = reference_resampling(x, reference_values)
    result["common_complete_scenes"] = np.flatnonzero(common).tolist()
    result["common_panel_distortion"] = [interval(row[common]) for row in distortion]
    result["scene_fixed_effects_regression"] = fixed_effects(distortion[:, common])
    for a, b in itertools.combinations(range(6), 2):
        good = np.isfinite(distortion[[a, b]]).all(axis=0)
        delta = distortion[a, good] - distortion[b, good]
        entry = dict(
            model_a=s.MODELS[a],
            model_b=s.MODELS[b],
            scenes=np.flatnonzero(good).tolist(),
            **interval(delta),
        )
        if len(delta) >= 12:
            draws = delta[rng.integers(0, len(delta), size=(5000, len(delta)))].mean(axis=1)
            entry["bootstrap_ci95"] = np.quantile(draws, [0.025, 0.975]).tolist()
        result["comparisons"].append(entry)
    for label, columns in {**FAMILIES, "without_texture": slice(0, 19)}.items():
        output = []
        for m in range(6):
            good = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
            if not good.any():
                output.append(None)
                continue
            g = geometry(x[m, good, :, 2:, columns], [r[:, columns] for r in reference_values])
            output.append(
                dict(beta=float(g["beta"].mean()), distortion=float(g["distortion"].mean()))
            )
        result["sensitivities"][label] = output
    return clean(result)


def load(square=False):
    verify()
    receipt = s.read(s.DATA / "measurement_receipt.json")
    for name in ("collection", "measurements", "reference_windows"):
        ext = "json" if name == "collection" else "jsonl"
        if s.sha(s.DATA / f"{name}.{ext}") != receipt[f"{name}_sha256"]:
            raise ValueError("measurement binding changed")
    x = np.full((6, len(s.SCENES), 2, 6, 31), np.nan)
    scaler = s.read(s.SCALER)
    key = "square_values" if square else "values"
    requests = {r["id"]: r for r in s.rows(s.DATA / "requests.jsonl")}
    seen = set()
    for row in s.rows(s.DATA / "measurements.jsonl"):
        if row["id"] in seen:
            raise ValueError("duplicate measurement")
        seen.add(row["id"])
        if row["status"] != "measured":
            continue
        r = requests[row["id"]]
        x[s.MODELS.index(r["model"]), r["scene"], r["repeat"], s.ARMS.index(r["arm"])] = transform(
            np.array(row[key]), scaler
        )
    records = s.rows(s.DATA / "reference_windows.jsonl") if square else s.rows(s.REF)
    if len(records) != 649 or any(r["status"] != "measured" for r in records):
        raise ValueError("reference measurement is incomplete")
    refs = [
        transform(np.array([r[key] for r in records if r["painter_id"] == a]), scaler)
        for a in s.ARTISTS
    ]
    return x, refs


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--square", action="store_true")
    args = parser.parse_args()
    result = compute(*load(args.square))
    path = s.DATA / ("analysis_square.json" if args.square else "analysis.json")
    if args.check:
        if result != s.read(path):
            raise ValueError("replayed analysis differs")
        print("Exact numerical replay passed")
    else:
        s.write_new(path, result)
        print("Analysis saved")


if __name__ == "__main__":
    main()
