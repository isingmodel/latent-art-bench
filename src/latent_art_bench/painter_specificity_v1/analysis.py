"""Paired scene regressions and repeat-corrected artist geometry."""

from __future__ import annotations

import itertools

import numpy as np
from scipy import stats
from scipy.spatial.distance import cdist

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_feature_generation_v2.statistics import transform

from . import study as s


def reference(square=False):
    scaler = s.read(s.SCALER)
    records = s.rows(s.DATA / "reference_windows.jsonl") if square else s.rows(s.REF)
    key = "square_values" if square else "values"
    if any(r["status"] != "measured" for r in records):
        raise ValueError("incomplete reference measurement")
    return [
        transform(np.array([r[key] for r in records if r["painter_id"] == artist]), scaler)
        for artist in s.ARTISTS
    ]


def centered(values):
    """Artist axis is penultimate: (..., artists, features)."""
    return values - values.mean(axis=-2, keepdims=True)


def geometry(x, ref):
    """x: scenes x 2 independent repeats x 4 artists x features."""
    r = centered(np.array([v.mean(axis=0) for v in ref]))
    h = np.sum(r * r)
    if h <= 0 or not np.isfinite(h):
        raise ValueError("reference artists must have distinct finite means")
    d = centered(x)
    slopes = np.einsum("skaj,aj->sk", d, r) / h
    beta = slopes.mean(axis=1)
    orthogonal = d - slopes[:, :, None, None] * r
    amplitude = (slopes[:, 0] - 1) * (slopes[:, 1] - 1)
    off_axis = np.sum(orthogonal[:, 0] * orthogonal[:, 1], axis=(1, 2)) / h
    error = d - r
    distortion = np.sum(error[:, 0] * error[:, 1], axis=(1, 2)) / h
    global_error = error.mean(axis=0)
    global_distortion = np.sum(global_error[0] * global_error[1]) / h
    return dict(
        beta=beta,
        distortion=distortion,
        amplitude_error=amplitude,
        off_axis_error=off_axis,
        global_distortion=float(global_distortion),
        reference_sum_squares=float(h),
        reference_contrasts=r,
    )


def interval(values, family=21):
    x = np.asarray(values)
    x = x[np.isfinite(x)]
    n = len(x)
    mean = float(x.mean()) if n else None
    if n < 12:
        return dict(n=n, mean=mean, available=False)
    se = float(x.std(ddof=1) / np.sqrt(n))
    return dict(
        n=n,
        mean=mean,
        se=se,
        available=True,
        ci95=(mean + np.array([-1, 1]) * stats.t.ppf(0.975, n - 1) * se).tolist(),
        simultaneous_ci=(
            mean + np.array([-1, 1]) * stats.t.ppf(1 - 0.05 / (2 * family), n - 1) * se
        ).tolist(),
        leave_one_scene_means=((x.sum() - x) / (n - 1)).tolist(),
    )


def energy(x, y):
    return float(2 * cdist(x, y).mean() - cdist(x, x).mean() - cdist(y, y).mean())


def shared_diagnostics(x):
    """x: scenes x repeats x six arms x features; use only fully observed scenes."""
    x = x[np.isfinite(x).all(axis=(1, 2, 3))]
    if not len(x):
        return dict(available=False, n_scenes=0)
    means = x.mean(axis=0)
    h = means[:, 2:] - means[:, :1]
    common = h.mean(axis=1)
    specific = h - common[:, None]
    generic = means[:, 1] - means[:, 0]
    common_ss = float(4 * np.sum(common[0] * common[1]))
    specific_ss = float(np.sum(specific[0] * specific[1]))
    g, c = generic.mean(axis=0), common.mean(axis=0)
    denom = np.linalg.norm(g) * np.linalg.norm(c)
    return dict(
        available=True,
        n_scenes=len(x),
        common_ss=common_ss,
        specific_ss=specific_ss,
        common_fraction=common_ss / (common_ss + specific_ss)
        if common_ss + specific_ss > 0
        else None,
        generic_common_cosine=float(np.dot(g, c) / denom) if denom > 0 else None,
        generic_shift_norm=float(np.linalg.norm(g)),
        common_shift_norm=float(np.linalg.norm(c)),
        generic_common_residual_norm=float(np.linalg.norm(c - g)),
    )


def compute(vectors, reference_values):
    """All model comparisons use identical retained reference coordinates."""
    x = np.asarray(vectors, dtype=float)
    if x.shape != (6, 16, 2, 6, 31):
        raise ValueError("expected six models, sixteen scenes, two repeats and six arms")
    result = dict(
        models=[],
        comparisons=[],
        sensitivities={},
        inference_family=21,
        uncertainty="paired scene t; fixed reference panel; Bonferroni 21",
    )
    beta = np.full((6, 16), np.nan)
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


def reference_resampling(x, ref):
    """Stratified work bootstrap, holding generated measurements fixed; sensitivity only."""
    rng = np.random.default_rng(2026091019)
    means = np.stack(
        [rng.multinomial(len(r), np.ones(len(r)) / len(r), size=1000) @ r / len(r) for r in ref],
        axis=1,
    )
    r = centered(means)
    h = np.sum(r * r, axis=(1, 2))
    result = []
    for m in range(6):
        good = np.isfinite(x[m, :, :, 2:]).all(axis=(1, 2, 3))
        if not good.any():
            result.append(None)
            continue
        d = centered(x[m, good, :, 2:])
        sum_rep = d.sum(axis=1).mean(axis=0)
        cross = np.sum(d[:, 0] * d[:, 1], axis=(1, 2)).mean()
        beta = np.einsum("aj,baj->b", sum_rep / 2, r) / h
        distortion = (cross - np.einsum("aj,baj->b", sum_rep, r) + h) / h
        result.append(
            dict(
                beta_ci95=np.quantile(beta, [0.025, 0.975]).tolist(),
                distortion_ci95=np.quantile(distortion, [0.025, 0.975]).tolist(),
            )
        )
    return result


def fixed_effects(values):
    """OLS on the common panel, with scene intercepts and GPT Image 2 as baseline."""
    models, scenes = values.shape
    if scenes < 12:
        return dict(available=False, n_scenes=scenes)
    model_columns = [m for m in range(models) if m != 1]
    design = np.zeros((models * scenes, scenes + models - 1))
    for m in range(models):
        for scene in range(scenes):
            row = m * scenes + scene
            design[row, scene] = 1
            if m != 1:
                design[row, scenes + model_columns.index(m)] = 1
    coefficients, _, rank, _ = np.linalg.lstsq(design, values.ravel(), rcond=None)
    if rank != design.shape[1]:
        raise ValueError("rank-deficient regression")
    return dict(
        available=True,
        n_scenes=scenes,
        baseline=s.MODELS[1],
        scene_intercepts=coefficients[:scenes].tolist(),
        model_coefficients={
            s.MODELS[m]: float(coefficients[scenes + i]) for i, m in enumerate(model_columns)
        },
        residual_sum_squares=float(np.sum((values.ravel() - design @ coefficients) ** 2)),
        inference="paired scene contrasts, not independent feature/image residuals",
    )


def clean(value):
    if isinstance(value, dict):
        return {key: clean(v) for key, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def load_vectors(square=False):
    result = np.full((6, 16, 2, 6, 31), np.nan)
    scaler = s.read(s.SCALER)
    requests = {r["id"]: r for r in s.rows(s.DATA / "requests.jsonl")}
    seen = set()
    for row in s.rows(s.DATA / "measurements.jsonl"):
        rid = row["id"]
        if rid in seen:
            raise ValueError("duplicate measured request")
        seen.add(rid)
        if row["status"] != "measured":
            continue
        r = requests[rid]
        result[s.MODELS.index(r["model"]), r["scene"], r["repeat"], s.ARMS.index(r["arm"])] = (
            transform(np.array(row["square_values" if square else "values"]), scaler)
        )
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--square", action="store_true")
    args = parser.parse_args()
    from .workflow import verify

    verify()
    receipt = s.read(s.DATA / "measurement_receipt.json")
    for name in ("collection", "measurements", "reference_windows"):
        extension = "json" if name == "collection" else "jsonl"
        if s.sha(s.DATA / f"{name}.{extension}") != receipt[f"{name}_sha256"]:
            raise ValueError("measurement receipt binding changed: " + name)
    result = compute(load_vectors(args.square), reference(args.square))
    target = s.DATA / ("analysis_square.json" if args.square else "analysis.json")
    if args.check:
        if result != s.read(target):
            raise ValueError("numerical replay differs")
        print("Exact numerical replay passed")
    else:
        s.write_new(target, result)
        print("Analysis saved")


if __name__ == "__main__":
    main()
