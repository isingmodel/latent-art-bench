"""Genuine controls with distinct works, embedding agreement intervals, family contrasts.

See studies/painter_tmlr_diagnostics_v3/PLAN.md. Retrospective; retained vectors and
embeddings only. Extends versions 1 and 2 without modifying their outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from latent_art_bench import painter_learned_audit_v1 as learned_audit
from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench import painter_tmlr_diagnostics_v1 as v1
from latent_art_bench import painter_tmlr_diagnostics_v2 as v2
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_tmlr_diagnostics_v3"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_diagnostics_v3.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
CONTROL_SEED, SCENE_SEED, REF_SEED, JOINT_SEED = 20261005, 20261006, 20261007, 20261008
FAMILY_SEED = v2.SCENE_SEED
CONTROL_DRAWS, SCENE_DRAWS, REF_DRAWS, JOINT_DRAWS = 1000, 5000, 1000, 2000
FAMILY_DRAWS = v2.SCENE_DRAWS


def distinct_pair(rng, pool):
    """Two different works from a pool of indices (or rows)."""
    return pool[rng.choice(len(pool), size=2, replace=False)]


def real_controls_distinct(refs, labels, draws=CONTROL_DRAWS, seed=CONTROL_SEED):
    """Genuine-painting controls whose two pseudo-repeats are distinct works."""
    rng = np.random.default_rng(seed)
    classes = review.CLASSES
    scene_classes = [
        classes.index(review.CLASS_MAP[c]) for c, _ in s.SCENES if c in review.CLASS_MAP
    ]
    groups = [[np.flatnonzero(lab == c) for c in classes] for lab in labels]
    keys = ("pooled_real", "class_real_pooled_target", "class_real_class_target")
    values = {k: [] for k in keys}
    for _ in range(draws):
        train, held, train_labs, held_labs = [], [], [], []
        for ref, artist_groups in zip(refs, groups, strict=True):
            left, right, ll, rl = [], [], [], []
            for j, ix in enumerate(artist_groups):
                ix = rng.permutation(ix)
                n = len(ix) // 2
                if n < 2:
                    raise ValueError("insufficient class support for disjoint halves")
                left.extend(ix[:n])
                right.extend(ix[n:])
                ll.extend([classes[j]] * n)
                rl.extend([classes[j]] * (len(ix) - n))
            train.append(ref[left])
            held.append(ref[right])
            train_labs.append(np.array(ll))
            held_labs.append(np.array(rl))
        r = review.centered(np.array([a.mean(axis=0) for a in train]))
        pooled = np.stack(
            [np.stack([distinct_pair(rng, a) for _ in range(14)]) for a in held], axis=2
        )
        values["pooled_real"].append(float(review.metrics(review.centered(pooled), r)[2].mean()))
        conditional = np.array(
            [
                np.stack(
                    [
                        distinct_pair(rng, a[lab == classes[c]])
                        for a, lab in zip(held, held_labs, strict=True)
                    ],
                    axis=1,
                )
                for c in scene_classes
            ]
        )
        rc = review.centered(review.class_targets(train, train_labs))[scene_classes]
        values["class_real_pooled_target"].append(
            float(review.metrics(review.centered(conditional), r)[2].mean())
        )
        values["class_real_class_target"].append(
            float(review.metrics(review.centered(conditional), rc)[2].mean())
        )
    return {
        k: dict(
            mean=float(np.mean(v)),
            interval95=np.quantile(v, [0.025, 0.975]).tolist(),
            above_one=float(np.mean(np.array(v) > 1)),
        )
        for k, v in values.items()
    }


def agreement(x, means):
    """Aligned amplitude and scene-wise error of the centered named differences."""
    named = np.asarray(x, dtype=float)[:, :, 2:]
    d = named - named.mean(axis=2, keepdims=True)
    r = means - means.mean(axis=0)
    h = float(np.sum(r * r))
    beta = float(np.mean(np.einsum("skaj,aj->sk", d, r)) / h)
    error = float(np.mean(np.sum((d[:, 0] - r) * (d[:, 1] - r), axis=(1, 2))) / h)
    return beta, error


def embedding_agreement(x, refs):
    means = np.stack([v.mean(axis=0) for v in refs])
    beta, error = agreement(x, means)
    rng = np.random.default_rng(SCENE_SEED)
    scene = [
        agreement(x[rng.integers(0, x.shape[0], size=x.shape[0])], means)
        for _ in range(SCENE_DRAWS)
    ]
    rng = np.random.default_rng(REF_SEED)
    ref = [agreement(x, v2.resample_refs(refs, rng)) for _ in range(REF_DRAWS)]
    rng = np.random.default_rng(JOINT_SEED)
    joint = []
    for _ in range(JOINT_DRAWS):
        idx = rng.integers(0, x.shape[0], size=x.shape[0])
        joint.append(agreement(x[idx], v2.resample_refs(refs, rng))[1] < 1)
    return dict(
        beta=beta,
        d=error,
        beta_scene=v2.interval([b for b, _ in scene]),
        d_scene=v2.interval([e for _, e in scene]),
        beta_reference=v2.interval([b for b, _ in ref]),
        d_reference=v2.interval([e for _, e in ref]),
        d_below_one_scene=float(np.mean([e < 1 for _, e in scene])),
        d_below_one_joint=float(np.mean(joint)),
    )


def normalized_prototype_share(x, means):
    units = means / np.linalg.norm(means, axis=1, keepdims=True)
    m = np.asarray(x, dtype=float).mean(axis=(0, 1))
    generic, named = m[1], m[2:]
    u_bar = units.mean(axis=0)
    gain = float(np.mean(np.sum(named * units, axis=1)) - generic @ u_bar)
    shared = float((named.mean(axis=0) - generic) @ u_bar)
    return v1.ratio(shared, gain)


def aligned_embedding_refs(name):
    """Reference embeddings per painter in the order of the 31-feature reference records."""
    _, refs_manifest, _ = learned_audit.arrays(name)
    manifest = s.read(learned_audit.OUT / "inputs.json")
    embeddings = np.load(learned_audit.OUT / f"embeddings_{name}.npz", allow_pickle=False)[
        "embeddings"
    ].astype(np.float64)
    lookup = {(r["id"], r["view"]): v for r, v in zip(manifest["rows"], embeddings, strict=True)}
    records = measured.reference_records()
    refs = [
        np.array([lookup[(r["image_id"], "original")] for r in records if r["painter_id"] == a])
        for a in s.ARTISTS
    ]
    for aligned, original in zip(refs, refs_manifest, strict=True):
        if aligned.shape != np.asarray(original).shape or not np.allclose(
            aligned.mean(axis=0), np.asarray(original).mean(axis=0), atol=1e-12
        ):
            raise ValueError("aligned reference embeddings differ from the audited panel")
    return refs


def family_contrasts(x, means):
    rng = np.random.default_rng(FAMILY_SEED)
    draws = [rng.integers(0, 14, size=14) for _ in range(FAMILY_DRAWS)]
    names = ("color", "spatial", "texture")

    def family_means(xs):
        out = {}
        for name in names:
            cut = v1.FAMILIES[name]
            vals = [v2.fractions(xs[m][..., cut], means[:, cut])["observed"] for m in range(6)]
            if any(v is None for v in vals):
                return None
            out[name] = float(np.mean(vals))
        return out

    point = family_means(x)
    boot = [family_means(x[:, idx]) for idx in draws]
    kept = [b for b in boot if b is not None]
    pairs = (("texture", "color"), ("texture", "spatial"), ("color", "spatial"))
    return dict(
        point={f"{a}-{b}": point[a] - point[b] for a, b in pairs},
        interval={f"{a}-{b}": v2.interval([k[a] - k[b] for k in kept]) for a, b in pairs},
        below_zero={f"{a}-{b}": float(np.mean([k[a] < k[b] for k in kept])) for a, b in pairs},
        dropped_draws=len(boot) - len(kept),
    )


def input_bindings():
    paths = [
        PLAN,
        Path(__file__),
        TEST,
        Path(v1.__file__),
        Path(v2.__file__),
        Path(review.__file__),
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "measurements.jsonl",
        s.REF,
        s.SCALER,
        review.DEVELOPMENT,
        learned_audit.OUT / "inputs.json",
    ]
    for name in ("clip", "csd"):
        paths += [
            learned_audit.OUT / f"embeddings_{name}.npz",
            learned_audit.OUT / f"extraction_{name}.json",
        ]
    return [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in sorted(set(paths))]


def compute():
    bindings = input_bindings()
    x, refs = measured.load(square=False)
    refs = [np.asarray(v, dtype=float) for v in refs]
    means = np.stack([v.mean(axis=0) for v in refs])
    labels, _, _ = review.labels_and_development()
    recorded = s.read(review.OUT / "analysis.json")["real_controls"]
    replay = review.real_controls(refs, labels)
    for key in recorded:
        if not np.isclose(replay[key]["mean"], recorded[key]["mean"], atol=1e-12):
            raise ValueError("with-replacement control replay differs from the record")
    controls = {"hand31": real_controls_distinct(refs, labels)}
    replacement = {}
    learned = {}
    reference = s.read(learned_audit.OUT / "analysis.json")
    for name in ("clip", "csd"):
        xe, _, _ = learned_audit.arrays(name)
        refs_e = aligned_embedding_refs(name)
        means_e = np.stack([v.mean(axis=0) for v in refs_e])
        controls[name] = real_controls_distinct(refs_e, labels)
        replacement[name] = {
            k: dict(mean=v["mean"], interval95=v["interval95"])
            for k, v in review.real_controls(refs_e, labels).items()
        }
        rows = []
        for m, model in enumerate(s.MODELS):
            row = embedding_agreement(xe[m], refs_e)
            expected = reference[name]["original"]["targets"]["primary"]["models"][m]["centered"]
            if not np.allclose(
                [row["beta"], row["d"]], [expected["beta"], expected["d"]], atol=1e-10
            ):
                raise ValueError(f"embedding agreement identity differs: {name} {model}")
            row["normalized_prototype_share"] = normalized_prototype_share(xe[m], means_e)
            rows.append(dict(model=model, **row))
        learned[name] = rows
    result = dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; post-result diagnostics requested by round-3 reviews",
        uncertainty="percentile intervals and shares from resampling; no tests",
        seeds=dict(
            control=CONTROL_SEED,
            scene=SCENE_SEED,
            reference=REF_SEED,
            joint=JOINT_SEED,
            family=FAMILY_SEED,
        ),
        inputs=bindings,
        models=list(s.MODELS),
        genuine_controls_distinct=controls,
        genuine_controls_with_replacement_embeddings=replacement,
        learned=learned,
        family_contrasts=family_contrasts(x, means),
    )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return result


def fmt(v, places=3):
    return "n/a" if v is None else f"{v:.{places}f}"


def report(result):
    lines = [
        "# TMLR revision diagnostics, version 3",
        "",
        "Retrospective analysis under",
        "[the plan](../../studies/painter_tmlr_diagnostics_v3/PLAN.md).",
        "",
        "## Genuine-painting controls with distinct works (mean error D, share above 1)",
        "",
    ]
    for rep, block in result["genuine_controls_distinct"].items():
        lines.append(
            f"- {rep}: "
            + "; ".join(
                f"{k} {fmt(v['mean'])} ({100 * v['above_one']:.1f}% > 1)" for k, v in block.items()
            )
        )
    lines += ["", "## Embedding agreement", ""]
    for rep, rows in result["learned"].items():
        for title, row in zip(s.TITLES, rows):
            lines.append(
                f"- {rep} {title}: beta {fmt(row['beta'])}, D {fmt(row['d'])} "
                f"[{fmt(row['d_scene'][0])}, {fmt(row['d_scene'][1])}], "
                f"P(D<1) joint {fmt(row['d_below_one_joint'])}, normalized-prototype share "
                f"{fmt(row['normalized_prototype_share'])}"
            )
    fc = result["family_contrasts"]
    lines += ["", "## Family contrasts (mean over configurations)", ""]
    for key in fc["point"]:
        lines.append(
            f"- {key}: {fmt(fc['point'][key])} [{fmt(fc['interval'][key][0])}, "
            f"{fmt(fc['interval'][key][1])}], below zero {100 * fc['below_zero'][key]:.1f}%"
        )
    lines += [f"- dropped draws: {fc['dropped_draws']}", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("analyze", "check"))
    args = parser.parse_args()
    if args.action == "analyze" and (JSON_PATH.exists() or REPORT_PATH.exists()):
        raise FileExistsError("outputs already exist; use check, never overwrite")
    result = compute()
    markdown = report(result)
    if args.action == "check":
        if result != s.read(JSON_PATH) or markdown != REPORT_PATH.read_text():
            raise ValueError("exact replay differs")
        print("Exact TMLR diagnostics v3 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v3 written")


if __name__ == "__main__":
    main()
