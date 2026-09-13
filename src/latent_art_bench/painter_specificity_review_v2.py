"""Post-result clarification diagnostics; no acquisition or measurement API.

See studies/painter_specificity_review_v2/PLAN.md. Frozen v1 results are inputs.
"""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
from scipy.stats import t

from latent_art_bench import painter_specificity_review_v1 as previous
from latent_art_bench.painter_specificity_measurement_v1.workflow import load
from latent_art_bench.painter_specificity_v1.analysis import centered, shared_diagnostics
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_specificity_review_v2"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS
ORIGINAL = previous.OUT / "analysis.json"
CONTROL_KEYS = ("pooled_real", "class_real_pooled_target", "class_real_class_target")
PAIRS = tuple(itertools.combinations(range(6), 2))
POWERS = (0.5, 1.5, 3.0)
NOISE_FORMS = ("isotropic", "reference_aligned_rank3")


def cross_repeat_alignment(x):
    """Ratio of symmetric cross moments, not an unbiased or bounded cosine."""
    if x.ndim != 4 or x.shape[1:3] != (2, 6) or not np.isfinite(x).all():
        raise ValueError("complete scenes with two repeats and six arms required")
    if len(x) < 1:
        raise ValueError("at least one scene required")
    means = x.mean(axis=0)
    g = means[:, 1] - means[:, 0]
    c = means[:, 2:].mean(axis=1) - means[:, 0]
    numerator = (g[0] @ c[1] + g[1] @ c[0]) / 2
    gnorm, cnorm = g[0] @ g[1], c[0] @ c[1]
    plugin_numerator = g.mean(axis=0) @ c.mean(axis=0)
    correction = (g[0] - g[1]) @ (c[0] - c[1]) / 4
    if not np.isclose(plugin_numerator - correction, numerator, atol=1e-12, rtol=1e-12):
        raise ValueError("symmetric cross-moment identity differs")
    return dict(
        plugin_cosine=shared_diagnostics(x)["generic_common_cosine"],
        ratio=float(numerator / np.sqrt(gnorm * cnorm)) if min(gnorm, cnorm) > 0 else None,
        cross_numerator=float(numerator),
        generic_cross_norm_squared=float(gnorm),
        common_cross_norm_squared=float(cnorm),
        plugin_numerator=float(plugin_numerator),
        observed_numerator_correction=float(correction),
        free_arm_noise_contribution_estimate=float(
            np.square(x[:, 0, 0] - x[:, 1, 0]).sum() / (4 * len(x) ** 2)
        ),
    )


def centered_noise_power(x, r):
    """Per-repeat power / H, using independent repeat differences in fixed scenes."""
    h = float(np.square(r).sum())
    if h <= 0 or x.ndim != 4 or x.shape[1:3] != (2, 6):
        raise ValueError("positive H and two repeats of six arms required")
    difference = x[:, 0, 2:] - x[:, 1, 2:]
    direct = np.square(centered(difference)).sum(axis=(1, 2)).mean() / (2 * h)
    marginal = 0.75 * np.square(difference).sum(axis=(1, 2)).mean() / (2 * h)
    return dict(direct=float(direct), independent_artist_approximation=float(marginal))


def expected_control_error(held_means, target):
    """Exact conditional E[D] for independent repeat draws from finite held pools.

    Inputs are already artist-centered. `held_means` is artists x features or
    scenes x artists x features. The normalization is the original mean target H.
    """
    held_means = np.asarray(held_means)
    if held_means.ndim == 2:
        held_means = held_means[None]
    if held_means.ndim != 3:
        raise ValueError("held means must have artist and feature axes")
    repeated_means = np.repeat(held_means[:, None], 2, axis=1)
    return float(previous.metrics(repeated_means, target)[2].mean())


def summarize(values):
    a = np.asarray(values)
    return dict(
        mean=float(a.mean()),
        median=float(np.median(a)),
        sd=float(a.std(ddof=1)),
        central95=np.quantile(a, [0.025, 0.975]).tolist(),
        draws=a.tolist(),
    )


def real_control_decomposition(refs, labels, draws=1000, original=None):
    """Preserve v1 RNG order exactly, retaining the expected value of each split."""
    rng = np.random.default_rng(2026091201)
    classes = previous.CLASSES
    scene_classes = [
        classes.index(previous.CLASS_MAP[c]) for c, _ in s.SCENES if c in previous.CLASS_MAP
    ]
    groups = [[np.flatnonzero(lab == c) for c in classes] for lab in labels]
    values = {k: dict(observed=[], conditional_expected=[]) for k in CONTROL_KEYS}
    for _ in range(draws):
        train, held, train_labs, held_labs = [], [], [], []
        for ref, artist_groups in zip(refs, groups):
            left, right, ll, rl = [], [], [], []
            for j, indices in enumerate(artist_groups):
                indices = rng.permutation(indices)
                n = len(indices) // 2
                if n < 2:
                    raise ValueError("insufficient class support for disjoint halves")
                left.extend(indices[:n])
                right.extend(indices[n:])
                ll.extend([classes[j]] * n)
                rl.extend([classes[j]] * (len(indices) - n))
            if set(left) & set(right):
                raise ValueError("real control split overlap")
            train.append(ref[left])
            held.append(ref[right])
            train_labs.append(np.array(ll))
            held_labs.append(np.array(rl))
        target = centered(np.array([a.mean(axis=0) for a in train]))
        pooled = np.stack([a[rng.integers(len(a), size=(14, 2))] for a in held], axis=2)
        conditional = np.array(
            [
                np.stack(
                    [
                        a[lab == classes[c]][rng.integers(np.sum(lab == classes[c]), size=2)]
                        for a, lab in zip(held, held_labs)
                    ],
                    axis=1,
                )
                for c in scene_classes
            ]
        )
        target_c = centered(previous.class_targets(train, train_labs))[scene_classes]
        mu = centered(np.array([a.mean(axis=0) for a in held]))
        mu_c = centered(previous.class_targets(held, held_labs))[scene_classes]
        observed = (
            (centered(pooled), target),
            (centered(conditional), target),
            (centered(conditional), target_c),
        )
        expected = ((mu, target), (mu_c, target), (mu_c, target_c))
        for key, (d, r), (m, er) in zip(CONTROL_KEYS, observed, expected):
            values[key]["observed"].append(float(previous.metrics(d, r)[2].mean()))
            values[key]["conditional_expected"].append(expected_control_error(m, er))
    result = {}
    for key, row in values.items():
        if original is not None and not np.array_equal(row["observed"], original[key]["draws"]):
            raise ValueError("original real-control sampled draws differ: " + key)
        residual = np.array(row["observed"]) - row["conditional_expected"]
        result[key] = dict(
            **{kind: summarize(v) for kind, v in row.items()},
            sampling_residual=summarize(residual),
        )
    return result


def calibration_stability(a, b, r):
    """A minus B; every deletion refits all inner training folds from scratch."""
    if len(a) != len(b) or len(a) < 3:
        raise ValueError("at least three matched scenes required")
    base_a, base_b = previous.calibration(a, r), previous.calibration(b, r)
    if base_a["held_out_d"] is None or base_b["held_out_d"] is None:
        raise ValueError("original calibration unavailable")
    differences = np.array(base_a["held_out_scene_d"]) - base_b["held_out_scene_d"]
    deletions = []
    for i in range(len(a)):
        fitted_a = previous.calibration(np.delete(a, i, axis=0), r)
        fitted_b = previous.calibration(np.delete(b, i, axis=0), r)
        available = fitted_a["held_out_d"] is not None and fitted_b["held_out_d"] is not None
        deletions.append(
            dict(
                omitted_scene=i,
                a=fitted_a,
                b=fitted_b,
                difference=fitted_a["held_out_d"] - fitted_b["held_out_d"] if available else None,
            )
        )
    available_values = [v["difference"] for v in deletions if v["difference"] is not None]
    return dict(
        original_a=base_a,
        original_b=base_b,
        mean_difference=float(differences.mean()),
        a_lower_folds=int((differences < 0).sum()),
        fold_differences=differences.tolist(),
        scene_deletions=deletions,
        available_deletions=len(available_values),
        deletion_range=[min(available_values), max(available_values)] if available_values else None,
    )


def simulation_geometry(r):
    """Original fixed means and a trace-one, rank-three reference-aligned noise map."""
    r = r / np.linalg.norm(r)
    rng = np.random.default_rng(2026091202)
    slopes = np.array([0.95, 1, 0.77, 0.82, 0.44, 0.47])
    residual = centered(rng.normal(size=(6, 4, 31)))
    residual -= np.einsum("maj,aj->m", residual, r)[:, None, None] * r
    residual /= np.linalg.norm(residual, axis=(1, 2))[:, None, None]
    theta = slopes[:, None, None] * r + np.sqrt(
        [1.54, 1.23, 1.68, 1.60, 0.79, 0.50]
    )[:, None, None] * residual
    u, singular, vt = np.linalg.svd(r, full_matrices=False)
    axes = np.array([np.outer(u[:, j], vt[j]) for j in range(3)])
    weights = singular[:3] ** 2 / np.square(singular[:3]).sum()
    if singular[2] <= 1e-12 or not np.allclose(centered(axes), axes, atol=1e-12):
        raise ValueError("rank-three artist-centered reference required")
    return r, theta, axes, weights


def simulation_endpoints(d, r):
    """Samples x six models x 14 scenes x two repeats x four artists x features."""
    if d.ndim != 6 or d.shape[1:5] != (6, 14, 2, 4):
        raise ValueError("six models, 14 scenes, two repeats and four artists required")
    beta = np.einsum("bmskaj,aj->bms", d, r) / 2
    error = ((d[:, :, :, 0] - r) * (d[:, :, :, 1] - r)).sum(axis=(3, 4))
    endpoints = np.concatenate(
        [beta, np.stack([error[:, a] - error[:, b] for a, b in PAIRS], axis=1)], axis=1
    )
    return endpoints, error


def simulation_sweep(r, repetitions=5000):
    if repetitions < 2:
        raise ValueError("at least two simulation repetitions required")
    r, theta, axes, weights = simulation_geometry(r)
    true_beta = np.einsum("maj,aj->m", theta, r)
    true_d = np.square(theta - r).sum(axis=(1, 2))
    target = np.r_[true_beta, [true_d[a] - true_d[b] for a, b in PAIRS]]
    critical = float(t.ppf(1 - 0.05 / (2 * 21), 13))
    rng = np.random.default_rng(2026091302)
    rows = []
    for power, form in itertools.product(POWERS, NOISE_FORMS):
        covered, joint, bias = np.zeros(21), 0, np.zeros(6)
        total_power, noise_count = 0.0, 0
        for start in range(0, repetitions, 100):
            size = min(100, repetitions - start)
            shape = (size, 6, 14, 2)
            if form == "isotropic":
                noise = centered(rng.normal(size=(*shape, 4, 31))) * np.sqrt(power / 93)
            else:
                coefficients = rng.normal(size=(*shape, 3)) * np.sqrt(power * weights)
                noise = np.einsum("bmskl,laj->bmskaj", coefficients, axes)
            total_power += np.square(noise).sum()
            noise_count += np.prod(shape)
            d = theta[None, :, None, None] + noise
            endpoints, error = simulation_endpoints(d, r)
            means = endpoints.mean(axis=2)
            half = critical * endpoints.std(axis=2, ddof=1) / np.sqrt(14)
            includes = abs(means - target) <= half
            covered += includes.sum(axis=0)
            joint += int(includes.all(axis=1).sum())
            bias += (error.mean(axis=2) - true_d).sum(axis=0)
        coverage = float(joint / repetitions)
        marginal = covered / repetitions
        rows.append(
            dict(
                centered_noise_power=power,
                covariance=form,
                repetitions=repetitions,
                observed_mean_noise_power=float(total_power / noise_count),
                family_coverage=coverage,
                family_coverage_mcse=float(np.sqrt(coverage * (1 - coverage) / repetitions)),
                marginal_coverage=marginal.tolist(),
                marginal_coverage_mcse=(np.sqrt(marginal * (1 - marginal) / repetitions)).tolist(),
                mean_error_bias=(bias / repetitions).tolist(),
            )
        )
    return dict(
        seed=2026091302,
        critical=critical,
        endpoint_labels=["beta: " + name for name in s.TITLES]
        + ["D: " + s.TITLES[a] + " minus " + s.TITLES[b] for a, b in PAIRS],
        endpoint_truth=target.tolist(),
        low_rank_covariance_weights=weights.tolist(),
        scenarios=rows,
        interpretation="Specified independent Gaussian noise laws; no fitted model of API errors.",
    )


def compute():
    x, refs = load()
    labels, _, _ = previous.labels_and_development()
    r = centered(np.array([a.mean(axis=0) for a in refs]))
    original = s.read(ORIGINAL)
    models = []
    for name, a in zip(s.TITLES, x):
        alignment = cross_repeat_alignment(a)
        deletions = [
            dict(omitted_scene=i, **cross_repeat_alignment(np.delete(a, i, axis=0)))
            for i in range(len(a))
        ]
        available = [v["ratio"] for v in deletions if v["ratio"] is not None]
        alignment.update(
            scene_deletions=deletions,
            available_deletions=len(available),
            deletion_range=[min(available), max(available)] if available else None,
        )
        models.append(
            dict(
                model=name,
                alignment=alignment,
                centered_repeat_noise_power=centered_noise_power(a, r),
            )
        )
    # All original calibrated values are recomputed with the preserved function.
    for a, old in zip(x, original["models"]):
        replayed = previous.calibration(centered(a[:, :, 2:]), r)
        if replayed != {k: old[k] for k in replayed}:
            raise ValueError("original calibration replay differs")
    return dict(
        interpretation=(
            "Post-result descriptive diagnostics from retained vectors; primary endpoints, "
            "family and images unchanged. No perceptual validation or new model-ranking test."
        ),
        reference_h=float(np.square(r).sum()),
        models=models,
        calibrated_gpt2_minus_flux=calibration_stability(
            centered(x[1, :, :, 2:]), centered(x[5, :, :, 2:]), r
        ),
        real_controls=real_control_decomposition(refs, labels, original=original["real_controls"]),
        original_real_control_draws_replayed_exactly=True,
        original_calibration_replayed_exactly=True,
        simulation=simulation_sweep(r),
    )


def input_paths():
    paths = [
        PLAN,
        Path(__file__),
        s.ROOT / "tests" / NS / "test_diagnostics.py",
        ORIGINAL,
        Path(previous.__file__),
        s.ROOT / "critics/assessment_v1/check_claims.py",
        s.ROOT / "src/latent_art_bench/painter_specificity_v1/study.py",
        s.ROOT / "src/latent_art_bench/painter_specificity_v2/study.py",
        *previous.input_paths(),
    ]
    return list(dict.fromkeys(paths))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("run", "check"))
    args = parser.parse_args()
    inputs = [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in input_paths()]
    target = OUT / "analysis.json"
    if args.action == "run" and target.exists():
        raise FileExistsError("diagnostic output exists; use check, never overwrite")
    if args.action == "check" and s.read(target)["inputs"] != inputs:
        raise ValueError("diagnostic source/input binding differs")
    result = dict(inputs=inputs, **compute())
    if args.action == "check":
        if s.read(target) != result:
            raise ValueError("diagnostic numerical replay differs")
        print("Exact v2 review diagnostic replay passed, including all original real-control draws")
    else:
        s.write_new(target, result)
        print("V2 review diagnostics saved; original outputs unchanged")


if __name__ == "__main__":
    main()
