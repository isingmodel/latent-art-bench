"""Post-result target diagnostics; read-only use of completed specificity vectors.

See studies/painter_specificity_review_v1/PLAN.md. No acquisition/extraction API.
"""

from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
from scipy.stats import t

from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_measurement_v1.workflow import load, reference_records
from latent_art_bench.painter_specificity_reference_v1.analysis import CLASSES, FRAME
from latent_art_bench.painter_specificity_v1.analysis import centered, energy
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_specificity_review_v1"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS
DEVELOPMENT = s.SCALER.with_name("development_features.jsonl")
CLASS_MAP = {"water": CLASSES[0], "built": CLASSES[1], "land": CLASSES[3]}


def metrics(d, r):
    """Centered contrasts: scenes, two repeats, artists, features; target fixed or per scene."""
    if d.ndim != 4 or d.shape[1] != 2 or not np.isfinite(d).all():
        raise ValueError("two complete repeats required")
    if r.ndim == 2:
        r = np.broadcast_to(r, (len(d), *r.shape))
    if r.shape != (len(d), *d.shape[2:]) or not np.isfinite(r).all():
        raise ValueError("target shape differs")
    h = np.square(r).sum(axis=(1, 2)).mean()
    if h <= 0:
        raise ValueError("nonzero reference contrast required")
    beta = np.einsum("skaj,saj->s", d, r) / (2 * h)
    q = (d[:, 0] * d[:, 1]).sum(axis=(1, 2)) / h
    error = ((d[:, 0] - r) * (d[:, 1] - r)).sum(axis=(1, 2)) / h
    return beta, q, error


def calibration(d, r):
    beta, q, error = metrics(d, r)
    b, magnitude = beta.mean(), q.mean()
    train_b = (beta.sum() - beta) / (len(beta) - 1)
    train_q = (q.sum() - q) / (len(q) - 1)
    available = bool((train_q > 0).all())
    scalars = np.maximum(0, train_b / train_q) if available else None
    held = 1 - 2 * scalars * beta + scalars**2 * q if available else None
    pooled = metrics(d.mean(axis=0, keepdims=True), r)[2].mean()
    residual = d - d.mean(axis=0, keepdims=True)
    heterogeneity = (residual[:, 0] * residual[:, 1]).sum() / (len(d) * (r * r).sum())
    if not np.allclose(error.mean(), pooled + heterogeneity, atol=1e-12):
        raise ValueError("scene decomposition failed")
    return dict(
        beta=float(b),
        q=float(magnitude),
        d=float(error.mean()),
        aggregate_d=float(pooled),
        scene_variation=float(heterogeneity),
        corrected_alignment=float(b / np.sqrt(magnitude)) if magnitude > 0 else None,
        held_out_d=float(held.mean()) if available else None,
        held_out_scene_d=held.tolist() if available else None,
        fitted_scalars=scalars.tolist() if available else None,
    )


def shared_within(x):
    h = x[:, :, 2:] - x[:, :, :1]
    c = h.mean(axis=2)
    d = h - c[:, :, None]
    common = 4 * (c[:, 0] * c[:, 1]).sum(axis=1).mean()
    specific = (d[:, 0] * d[:, 1]).sum(axis=(1, 2)).mean()
    return dict(
        common=float(common),
        specific=float(specific),
        fraction=float(common / (common + specific)) if common + specific > 0 else None,
    )


def stratified_energy(ref, y):
    """Fixed empirical reference vs equally weighted scene mixture, two outputs/scene.

    Only same-scene generated distances need correction: cross-scene pairs are
    independent already. Do not apply a pooled IID n/(n-1) multiplier.
    """
    if y.ndim != 3 or y.shape[1] != 2:
        raise ValueError("two repeats in every scene required")
    observed = energy(ref, y.reshape(-1, y.shape[-1]))
    correction = np.linalg.norm(y[:, 0] - y[:, 1], axis=1).sum() / (2 * len(y) ** 2)
    return dict(
        empirical=observed,
        corrected=float(observed - correction),
        generated_diagonal_bias=float(correction),
    )


def covariance_map(dev, weights):
    weights = weights / weights.sum()
    residual = dev - weights @ dev
    cov = (residual * weights[:, None]).T @ residual
    regularized = 0.5 * cov + 0.5 * np.trace(cov) / len(cov) * np.eye(len(cov))
    eigenvalues, vectors = np.linalg.eigh(regularized)
    if eigenvalues.min() <= 0:
        raise ValueError("nonpositive development covariance")
    return (vectors / np.sqrt(eigenvalues)) @ vectors.T


def labels_and_development():
    if s.sha(DEVELOPMENT) != s.read(s.SCALER)["development_feature_sha256"]:
        raise ValueError("development vectors differ from the original scaler input")
    frame = {v["work_id"]: v for v in s.rows(FRAME)}
    records = reference_records()
    labels = [
        np.array([frame[v["image_id"]]["content_class"] for v in records if v["painter_id"] == a])
        for a in s.ARTISTS
    ]
    dev_rows = [v for v in s.rows(DEVELOPMENT) if v["role"] == "development"]
    if len(dev_rows) != 221 or any(v["status"] != "measured" for v in dev_rows):
        raise ValueError("development membership differs")
    if {v["image_id"] for v in dev_rows} & {v["image_id"] for v in records}:
        raise ValueError("reference/development overlap")
    dev = transform(np.array([v["values"] for v in dev_rows]), s.read(s.SCALER))
    counts = s.read(s.SCALER)["development_counts"]
    weights = np.array([1 / (4 * counts[v["painter_id"]]) for v in dev_rows])
    return labels, dev, weights


def class_targets(refs, labels):
    return np.array([[v[lab == c].mean(axis=0) for v, lab in zip(refs, labels)] for c in CLASSES])


def real_controls(refs, labels, draws=1000):
    rng = np.random.default_rng(2026091201)
    scene_classes = [CLASSES.index(CLASS_MAP[c]) for c, _ in s.SCENES if c in CLASS_MAP]
    groups = [[np.flatnonzero(lab == c) for c in CLASSES] for lab in labels]
    values = {k: [] for k in ("pooled_real", "class_real_pooled_target", "class_real_class_target")}
    for _ in range(draws):
        train, held, train_labs, held_labs = [], [], [], []
        for ref, artist_groups in zip(refs, groups):
            left, right, ll, rl = [], [], [], []
            for j, ix in enumerate(artist_groups):
                ix = rng.permutation(ix)
                n = len(ix) // 2
                if n < 2:
                    raise ValueError("insufficient class support for disjoint halves")
                left.extend(ix[:n])
                right.extend(ix[n:])
                ll.extend([CLASSES[j]] * n)
                rl.extend([CLASSES[j]] * (len(ix) - n))
            if set(left) & set(right):
                raise ValueError("real control split overlap")
            train.append(ref[left])
            held.append(ref[right])
            train_labs.append(np.array(ll))
            held_labs.append(np.array(rl))
        r = centered(np.array([a.mean(axis=0) for a in train]))
        pooled = np.stack([a[rng.integers(len(a), size=(14, 2))] for a in held], axis=2)
        values["pooled_real"].append(float(metrics(centered(pooled), r)[2].mean()))
        conditional = np.array(
            [
                np.stack(
                    [
                        a[lab == CLASSES[c]][rng.integers(np.sum(lab == CLASSES[c]), size=2)]
                        for a, lab in zip(held, held_labs)
                    ],
                    axis=1,
                )
                for c in scene_classes
            ]
        )
        rc = centered(class_targets(train, train_labs))[scene_classes]
        values["class_real_pooled_target"].append(
            float(metrics(centered(conditional), r)[2].mean())
        )
        values["class_real_class_target"].append(
            float(metrics(centered(conditional), rc)[2].mean())
        )
    return {
        k: dict(
            mean=float(np.mean(v)),
            median=float(np.median(v)),
            interval95=np.quantile(v, [0.025, 0.975]).tolist(),
            draws=v,
        )
        for k, v in values.items()
    }


def simulation(r, repetitions=5000):
    """Known fixed-panel truths; intentionally includes violated repeat assumptions."""
    rng = np.random.default_rng(2026091202)
    r = r / np.linalg.norm(r)
    n = 14
    slopes = np.array([0.95, 1, 0.77, 0.82, 0.44, 0.47])
    residual = centered(rng.normal(size=(6, 4, 31)))
    residual -= np.einsum("maj,aj->m", residual, r)[:, None, None] * r
    residual /= np.linalg.norm(residual, axis=(1, 2))[:, None, None]
    theta = np.broadcast_to(
        slopes[:, None, None, None] * r
        + np.sqrt([1.54, 1.23, 1.68, 1.60, 0.79, 0.50])[:, None, None, None] * residual[:, None],
        (6, n, 4, 31),
    ).copy()
    interaction = centered(rng.normal(size=theta.shape))
    interaction -= interaction.mean(axis=1, keepdims=True)
    interaction *= 0.5 / np.sqrt(np.square(interaction).sum(axis=(2, 3)).mean())
    pairs = list(itertools.combinations(range(6), 2))
    critical = t.ppf(1 - 0.05 / (2 * 21), 13)
    output = []
    for mode in ("gaussian", "heavy_heteroskedastic", "scene_interaction", "shared_state"):
        truth = theta + interaction if mode == "scene_interaction" else theta
        true_beta = np.einsum("msaj,aj->ms", truth, r).mean(axis=1)
        true_d = np.square(truth - r).sum(axis=(2, 3)).mean(axis=1)
        target = np.r_[true_beta, [true_d[a] - true_d[b] for a, b in pairs]]
        covered = np.zeros(21)
        joint = 0
        bias = np.zeros(6)
        # Total independent-repeat centered noise power is .5 when homoskedastic.
        scale = np.sqrt(0.5 / (3 * 31))
        for start in range(0, repetitions, 100):
            size = min(100, repetitions - start)
            shape = (size, 6, n, 2, 4, 31)
            noise = (
                rng.standard_t(3, size=shape) / np.sqrt(3)
                if mode == "heavy_heteroskedastic"
                else rng.normal(size=shape)
            )
            if mode == "heavy_heteroskedastic":
                factors = np.linspace(0.5, 2, n)
                factors /= np.sqrt(np.mean(factors**2))
                noise *= factors[None, None, :, None, None, None]
            if mode == "shared_state":
                state = rng.normal(size=(size, 6, 1, 1, 4, 31))
                noise = np.sqrt(0.5) * (noise + state)
            d = truth[None, :, :, None] + scale * centered(noise)
            beta = np.einsum("bmskaj,aj->bms", d, r) / 2
            error = ((d[:, :, :, 0] - r) * (d[:, :, :, 1] - r)).sum(axis=(3, 4))
            endpoints = np.concatenate(
                [beta, np.stack([error[:, a] - error[:, b] for a, b in pairs], axis=1)], axis=1
            )
            means = endpoints.mean(axis=2)
            half = critical * endpoints.std(axis=2, ddof=1) / np.sqrt(n)
            includes = abs(means - target) <= half
            covered += includes.sum(axis=0)
            joint += includes.all(axis=1).sum()
            bias += (error.mean(axis=2) - true_d).sum(axis=0)
        output.append(
            dict(
                scenario=mode,
                repetitions=repetitions,
                family_coverage=float(joint / repetitions),
                marginal_coverage=(covered / repetitions).tolist(),
                mean_error_bias=(bias / repetitions).tolist(),
            )
        )
    return output


def compute():
    x, refs = load()
    labels, dev, weights = labels_and_development()
    means = np.array([v.mean(axis=0) for v in refs])
    r = centered(means)
    d = centered(x[:, :, :, 2:])
    h = np.square(r).sum()
    u, singular, vt = np.linalg.svd(r, full_matrices=False)
    axes = np.array([singular[j] * np.outer(u[:, j], vt[j]) for j in range(3)])
    result = dict(
        interpretation="post-result descriptive diagnostics; primary analysis unchanged",
        reference_spectrum=(singular[:3] ** 2 / h).tolist(),
        models=[],
    )
    for m, name in enumerate(s.TITLES):
        row = dict(model=name, **calibration(d[m], r), shared_within=shared_within(x[m]))
        original = s.read(s.DATA / "analysis.json")["models"][m]
        if not np.allclose(
            [row["beta"], row["d"], row["aggregate_d"]],
            [
                original["beta"]["mean"],
                original["distortion"]["mean"],
                original["global_distortion"],
            ],
            atol=1e-12,
            rtol=1e-12,
        ):
            raise ValueError("primary numerical identity differs")
        row["reference_component_slopes"] = [
            float(np.sum(d[m].mean(axis=(0, 1)) * a) / np.square(a).sum()) for a in axes
        ]
        row["artist_pairs"] = []
        for a, b in itertools.combinations(range(4), 2):
            contrast = (x[m, :, :, a + 2] - x[m, :, :, b + 2])[:, :, None]
            target = (means[a] - means[b])[None]
            beta, _, error = metrics(contrast, target)
            row["artist_pairs"].append(
                dict(
                    artists=[s.ARTISTS[a], s.ARTISTS[b]],
                    beta=float(beta.mean()),
                    d=float(error.mean()),
                )
            )
        row["leave_artist_out"] = []
        for a in range(4):
            keep = [i for i in range(4) if i != a]
            beta, _, error = metrics(centered(x[m, :, :, 2:][:, :, keep]), centered(means[keep]))
            row["leave_artist_out"].append(
                dict(omitted=s.ARTISTS[a], beta=float(beta.mean()), d=float(error.mean()))
            )
        row["label_permutations"] = [
            dict(order=list(p), d=float(metrics(d[m][:, :, list(p)], r)[2].mean()))
            for p in itertools.permutations(range(4))
        ]
        row["correct_label_rank"] = 1 + sum(
            p["d"] < row["d"] - 1e-12 for p in row["label_permutations"]
        )
        error = d[m] - r
        contributions = (error[:, 0] * error[:, 1]).mean(axis=0).sum(axis=0) / h
        row["coordinates"] = []
        for j, feature in enumerate(NAMES):
            keep = np.arange(31) != j
            row["coordinates"].append(
                dict(
                    feature=feature,
                    contribution=float(contributions[j]),
                    deleted_d=float(metrics(d[m][..., keep], r[:, keep])[2].mean()),
                )
            )
        row["energy"] = []
        for a in range(4):
            row["energy"].append(
                dict(
                    artist=s.ARTISTS[a],
                    named=stratified_energy(refs[a], x[m, :, :, a + 2]),
                    generic=stratified_energy(refs[a], x[m, :, :, 1]),
                )
            )
        result["models"].append(row)
    maps = {
        "equal_family": np.diag(np.repeat(np.sqrt(1 / np.array([11.0, 8.0, 12.0])), [11, 8, 12])),
        "development_covariance": covariance_map(dev, weights),
    }
    result["weighting"] = {}
    for name, matrix in maps.items():
        result["weighting"][name] = [
            dict(beta=float(b.mean()), d=float(e.mean()))
            for b, _, e in [metrics(a @ matrix, r @ matrix) for a in d]
        ]
    class_means = class_targets(refs, labels)
    class_r = centered(class_means)
    keep = [i for i, (c, _) in enumerate(s.SCENES) if c in CLASS_MAP]
    classes = [CLASSES.index(CLASS_MAP[s.SCENES[i][0]]) for i in keep]
    target = class_r[classes]
    result["content"] = dict(
        scenes=keep,
        classes=list(CLASSES),
        reference_counts=[[int(np.sum(lab == c)) for c in CLASSES] for lab in labels],
        class_target_h=[float(np.square(a).sum()) for a in class_r],
        primary_h=float(h),
        conditional_h=float(np.square(target).sum(axis=(1, 2)).mean()),
        real_class_vs_pooled=float(np.square(class_r - r).sum(axis=(1, 2)).mean() / h),
        models=[
            dict(
                model=s.TITLES[m],
                pooled_d=float(metrics(d[m, keep], r)[2].mean()),
                conditional_d=float(metrics(d[m, keep], target)[2].mean()),
                conditional_beta=float(metrics(d[m, keep], target)[0].mean()),
            )
            for m in range(6)
        ],
    )
    result["real_controls"] = real_controls(refs, labels)
    result["simulation"] = simulation(r)
    return result


def input_paths():
    return [
        PLAN,
        Path(__file__),
        s.SCALER,
        DEVELOPMENT,
        s.REF,
        FRAME,
        s.DATA / "requests.jsonl",
        s.DATA / "measurement_receipt.json",
        s.DATA / "measurements.jsonl",
        s.DATA / "analysis.json",
        s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/statistics.py",
        s.ROOT / "src/latent_art_bench/painter_specificity_v1/analysis.py",
        s.ROOT / "src/latent_art_bench/painter_specificity_measurement_v1/workflow.py",
    ]


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("run", "check"))
    args = parser.parse_args()
    paths = input_paths()
    inputs = [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths]
    target = OUT / "analysis.json"
    if args.action == "run" and target.exists():
        raise FileExistsError("diagnostic output exists; use check, never overwrite")
    if args.action == "check" and s.read(target)["inputs"] != inputs:
        raise ValueError("diagnostic source/input binding differs")
    result = dict(inputs=inputs, **compute())
    if args.action == "check":
        if s.read(target) != result:
            raise ValueError("diagnostic numerical replay differs")
        print("Exact post-result diagnostic replay passed")
    else:
        s.write_new(target, result)
        print("Review diagnostics saved; primary results unchanged")


if __name__ == "__main__":
    main()
