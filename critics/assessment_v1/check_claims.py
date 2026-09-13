"""Exploratory checks for adjudicating critics/; does not alter study outputs."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from latent_art_bench.painter_specificity_measurement_v1.workflow import load
from latent_art_bench.painter_specificity_review_v1 import (
    CLASS_MAP,
    CLASSES,
    calibration,
    class_targets,
    labels_and_development,
    metrics,
)
from latent_art_bench.painter_specificity_v1.analysis import centered, shared_diagnostics
from latent_art_bench.painter_specificity_v2 import study as s

x, refs = load()
r = centered(np.array([a.mean(axis=0) for a in refs]))
h = np.square(r).sum()
models = []
for name, a in zip(s.TITLES, x):
    means = a.mean(axis=0)
    g = means[:, 1] - means[:, 0]
    c = means[:, 2:].mean(axis=1) - means[:, 0]

    def aligned(v):
        m = v.mean(axis=0)
        gg = m[:, 1] - m[:, 0]
        cc = m[:, 2:].mean(axis=1) - m[:, 0]
        numerator = (gg[0] @ cc[1] + gg[1] @ cc[0]) / 2
        gnorm = gg[0] @ gg[1]
        cnorm = cc[0] @ cc[1]
        return float(numerator / np.sqrt(gnorm * cnorm)) if min(gnorm, cnorm) > 0 else None

    diag = shared_diagnostics(a)
    cal = calibration(centered(a[:, :, 2:]), r)
    traces = np.square(a[:, 0, 2:] - a[:, 1, 2:]).sum(axis=-1).mean(axis=0) / 2
    models.append(
        dict(
            model=name,
            cosine_plugin=diag["generic_common_cosine"],
            cosine_cross=aligned(a),
            cosine_cross_leave_scene_range=[
                min(aligned(np.delete(a, i, axis=0)) for i in range(14)),
                max(aligned(np.delete(a, i, axis=0)) for i in range(14)),
            ],
            plugin_numerator=float(g.mean(axis=0) @ c.mean(axis=0)),
            estimated_shared_free_noise=float(
                np.square(a[:, 0, 0] - a[:, 1, 0]).sum() / (4 * 14**2)
            ),
            g_cross_norm_squared=float(g[0] @ g[1]),
            c_cross_norm_squared=float(c[0] @ c[1]),
            centered_repeat_noise_power=float(0.75 * traces.sum() / h),
            beta=cal["beta"],
            q=cal["q"],
            d=cal["d"],
            held=cal["held_out_d"],
            fitted_optimum=1 - cal["beta"] ** 2 / cal["q"],
        )
    )

folds = [calibration(centered(a[:, :, 2:]), r)["held_out_scene_d"] for a in x]
difference = np.array(folds[1]) - np.array(folds[5])
outer = []
for i in range(14):
    outer.append(
        calibration(centered(np.delete(x[1], i, axis=0)[:, :, 2:]), r)["held_out_d"]
        - calibration(centered(np.delete(x[5], i, axis=0)[:, :, 2:]), r)["held_out_d"]
    )

# Replay the real-control RNG exactly, and also compute the conditional expected
# score of the held pool using its means instead of two sampled works per scene.
labels, _, _ = labels_and_development()
rng = np.random.default_rng(2026091201)
scene_classes = [CLASSES.index(CLASS_MAP[c]) for c, _ in s.SCENES if c in CLASS_MAP]
groups = [[np.flatnonzero(lab == c) for c in CLASSES] for lab in labels]
controls = {
    k: dict(observed=[], expected=[])
    for k in ("pooled_real", "class_real_pooled_target", "class_real_class_target")
}
for _ in range(1000):
    train, held, tl, hl = [], [], [], []
    for ref, artist_groups in zip(refs, groups):
        left, right, ll, rl = [], [], [], []
        for j, ix in enumerate(artist_groups):
            ix = rng.permutation(ix)
            n = len(ix) // 2
            left.extend(ix[:n])
            right.extend(ix[n:])
            ll.extend([CLASSES[j]] * n)
            rl.extend([CLASSES[j]] * (len(ix) - n))
        train.append(ref[left])
        held.append(ref[right])
        tl.append(np.array(ll))
        hl.append(np.array(rl))
    target = centered(np.array([a.mean(axis=0) for a in train]))
    pooled = np.stack([a[rng.integers(len(a), size=(14, 2))] for a in held], axis=2)
    conditional = np.array(
        [
            np.stack(
                [
                    a[lab == CLASSES[c]][rng.integers(np.sum(lab == CLASSES[c]), size=2)]
                    for a, lab in zip(held, hl)
                ],
                axis=1,
            )
            for c in scene_classes
        ]
    )
    target_c = centered(class_targets(train, tl))[scene_classes]
    mu = centered(np.array([a.mean(axis=0) for a in held]))
    mu_c = centered(class_targets(held, hl))[scene_classes]
    expected_inputs = [
        (mu[None, None].repeat(2, axis=1), target),
        (mu_c[:, None].repeat(2, axis=1), target),
        (mu_c[:, None].repeat(2, axis=1), target_c),
    ]
    observed_inputs = [
        (centered(pooled), target),
        (centered(conditional), target),
        (centered(conditional), target_c),
    ]
    for key, (ei, er), (oi, orr) in zip(controls, expected_inputs, observed_inputs):
        controls[key]["expected"].append(float(metrics(ei, er)[2].mean()))
        controls[key]["observed"].append(float(metrics(oi, orr)[2].mean()))
original = json.loads(Path("reports/painter_specificity_review_v1/analysis.json").read_text())[
    "real_controls"
]
summary = {}
for k, v in controls.items():
    assert np.array_equal(v["observed"], original[k]["draws"])
    summary[k] = {
        kind: dict(
            mean=float(np.mean(vals)),
            median=float(np.median(vals)),
            sd=float(np.std(vals, ddof=1)),
            range95=np.quantile(vals, [0.025, 0.975]).tolist(),
        )
        for kind, vals in v.items()
    }
    summary[k]["sampling_residual_sd"] = float(
        np.std(np.array(v["observed"]) - v["expected"], ddof=1)
    )

result = dict(
    reference_h=float(h),
    models=models,
    calibrated_gpt2_minus_flux=dict(
        mean=float(difference.mean()),
        gpt2_lower_folds=int((difference < 0).sum()),
        fold_differences=difference.tolist(),
        outer_scene_deletion_range=[min(outer), max(outer)],
        interpretation=(
            "Descriptive sensitivity; overlapping folds are not independent replications."
        ),
    ),
    real_controls=summary,
    interpretation=(
        "Post-result review audit from retained vectors. Conditional expectations refer "
        "to finite held pools; no new confirmatory tests or image-level validation."
    ),
)
result["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
result["source_sha256"] = {
    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [
        Path(__file__).resolve().relative_to(Path.cwd()),
        Path("paper/paper.tex"),
        Path("paper/specificity_results.tex"),
        Path("reports/painter_specificity_review_v1/analysis.json"),
        s.DATA.relative_to(Path.cwd()) / "analysis.json",
    ]
}
Path(__file__).with_name("checks.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
