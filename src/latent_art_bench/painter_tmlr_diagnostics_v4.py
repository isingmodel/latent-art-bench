"""Content-matched agreement of the between-name differences in CLIP and CSD.

See studies/painter_tmlr_diagnostics_v4/PLAN.md. Retrospective; retained vectors and
embeddings only. Extends versions 1-3 without modifying their outputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from latent_art_bench import painter_learned_audit_v1 as learned_audit
from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench import painter_tmlr_diagnostics_v3 as v3
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_tmlr_diagnostics_v4"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_diagnostics_v4.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
SCENE_SEED, SCENE_DRAWS = 20261009, 5000


def content_scenes():
    """Indices of the non-mixed scenes and the class index of each."""
    keep = [i for i, (c, _) in enumerate(s.SCENES) if c in review.CLASS_MAP]
    classes = [review.CLASSES.index(review.CLASS_MAP[s.SCENES[i][0]]) for i in keep]
    return keep, classes


def interval(values):
    return np.quantile(np.asarray(values, dtype=float), [0.025, 0.975]).tolist()


def content_agreement(x, refs, labels, keep, classes, draws=0, seed=SCENE_SEED):
    """β and D against the pooled and the class targets on the content-classed scenes.

    ``x``: scenes, repeats, arms (free, generic, four painters), features.
    """
    d = review.centered(np.asarray(x, dtype=float)[:, :, 2:])[keep]
    r = review.centered(np.stack([v.mean(axis=0) for v in refs]))
    target = review.centered(review.class_targets(refs, labels))[classes]
    h = float(np.square(r).sum())
    pooled_beta, _, pooled_error = review.metrics(d, r)
    beta, _, error = review.metrics(d, target)
    out = dict(
        pooled_beta=float(pooled_beta.mean()),
        pooled_d=float(pooled_error.mean()),
        class_beta=float(beta.mean()),
        class_d=float(error.mean()),
        class_vs_pooled=float(np.square(target - r).sum(axis=(1, 2)).mean() / h),
        class_h_over_h=float(np.square(target).sum(axis=(1, 2)).mean() / h),
    )
    if draws:
        rng = np.random.default_rng(seed)
        boot = []
        for _ in range(draws):
            idx = rng.integers(0, len(keep), size=len(keep))
            b, _, e = review.metrics(d[idx], target[idx])
            boot.append((float(b.mean()), float(e.mean())))
        out.update(
            class_beta_scene=interval([b for b, _ in boot]),
            class_d_scene=interval([e for _, e in boot]),
            class_d_below_one=float(np.mean([e < 1 for _, e in boot])),
        )
    return out


def input_bindings():
    paths = [
        PLAN,
        Path(__file__),
        TEST,
        Path(v3.__file__),
        Path(review.__file__),
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "measurements.jsonl",
        s.REF,
        s.SCALER,
        review.DEVELOPMENT,
        review.OUT / "analysis.json",
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
    keep, classes = content_scenes()
    labels, _, _ = review.labels_and_development()
    x, refs = measured.load(square=False)
    refs = [np.asarray(v, dtype=float) for v in refs]
    recorded = s.read(review.OUT / "analysis.json")["content"]
    if recorded["scenes"] != keep:
        raise ValueError("content scene set differs from the record")
    hand = []
    for m, model in enumerate(s.MODELS):
        row = content_agreement(x[m], refs, labels, keep, classes)
        rec = recorded["models"][m]
        if not np.allclose(
            [row["pooled_d"], row["class_d"], row["class_beta"]],
            [rec["pooled_d"], rec["conditional_d"], rec["conditional_beta"]],
            atol=1e-12,
        ):
            raise ValueError(f"31-feature content replay differs: {model}")
        hand.append(dict(model=model, **row))
    learned = {}
    for name in ("clip", "csd"):
        xe, _, _ = learned_audit.arrays(name)
        refs_e = v3.aligned_embedding_refs(name)
        learned[name] = [
            dict(
                model=model,
                **content_agreement(xe[m], refs_e, labels, keep, classes, draws=SCENE_DRAWS),
            )
            for m, model in enumerate(s.MODELS)
        ]
    result = dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; post-result diagnostics requested by round-4 reviews",
        uncertainty="percentile intervals and shares from scene resampling; no tests",
        seeds=dict(scene=SCENE_SEED),
        inputs=bindings,
        models=list(s.MODELS),
        scenes=keep,
        scene_classes=[review.CLASSES[c] for c in classes],
        hand31=hand,
        learned=learned,
    )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return result


def fmt(v, places=3):
    return "n/a" if v is None else f"{v:.{places}f}"


def report(result):
    lines = [
        "# TMLR revision diagnostics, version 4",
        "",
        "Retrospective analysis under",
        "[the plan](../../studies/painter_tmlr_diagnostics_v4/PLAN.md).",
        "",
        "## Agreement on the 11 content-classed scenes (pooled vs class targets)",
        "",
    ]
    blocks = [("31 features", result["hand31"])] + [
        (name.upper(), rows) for name, rows in result["learned"].items()
    ]
    for label, rows in blocks:
        for title, row in zip(s.TITLES, rows):
            line = (
                f"- {label} {title}: pooled beta {fmt(row['pooled_beta'])}, D "
                f"{fmt(row['pooled_d'])}; class beta {fmt(row['class_beta'])}, D "
                f"{fmt(row['class_d'])}"
            )
            if "class_d_scene" in row:
                line += (
                    f" [{fmt(row['class_d_scene'][0])}, {fmt(row['class_d_scene'][1])}], "
                    f"P(D<1) {fmt(row['class_d_below_one'])}"
                )
            lines.append(line)
        lines.append(
            f"- {label} class-vs-pooled target distance / H "
            f"{fmt(rows[0]['class_vs_pooled'])}; class spread / H {fmt(rows[0]['class_h_over_h'])}"
        )
        lines.append("")
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
        print("Exact TMLR diagnostics v4 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v4 written")


if __name__ == "__main__":
    main()
