"""Retrospective fixed-rule held-scene prompt-name identification.

No real outcomes are computed on import or by ``freeze``. Real ``analyze`` and
``check`` require an explicit --execute-real flag after the method-design audit.
The three fixed rules and all memberships are specified in the versioned plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from latent_art_bench.painter_learned_analysis_v1 import ARTISTS, MODELS

ROOT = Path(__file__).resolve().parents[2]
NS = "painter_prototype_transfer_v1"
PLAN = ROOT / "studies" / NS / "PLAN.md"
OUT = ROOT / "reports" / NS
LEARNED = ROOT / "reports/painter_learned_audit_v1"
RULES = ("reference_baseline", "common_translation", "generated_prototype")
REFERENCE_COUNTS = (297, 106, 141, 105)
DEVELOPMENT_COUNTS = (101, 36, 48, 36)
UNIT_ATOL = 1e-4


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        value
        if isinstance(value, str)
        else json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    with path.open("x") as stream:
        stream.write(text)


def unit_vectors(values, label):
    values = np.asarray(values, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError(f"{label}: nonfinite embedding")
    if not np.allclose(np.linalg.norm(values, axis=-1), 1, rtol=0, atol=UNIT_ATOL):
        raise ValueError(f"{label}: nonunit embedding")
    return values


def normalized_prototypes(values, label):
    norms = np.linalg.norm(values, axis=-1)
    if not np.isfinite(values).all() or not np.isfinite(norms).all() or np.any(norms <= 0):
        raise ValueError(f"{label}: zero or invalid prototype")
    return values / norms[..., None], norms


def summarize_scores(scores, query_norms):
    """Rows retain scene/repeat/true-prompt order; ties choose first candidate."""
    predictions = scores.argmax(axis=-1)
    truth = np.broadcast_to(np.arange(4), predictions.shape)
    correct = predictions == truth
    confusion = np.zeros((4, 4), dtype=np.int64)
    for painter in range(4):
        confusion[painter] = np.bincount(predictions[..., painter].ravel(), minlength=4)
    counts = confusion.sum(axis=1)
    recall = np.diag(confusion) / counts
    correct_scores = np.diagonal(scores, axis1=-2, axis2=-1)
    other_scores = scores.copy()
    other_scores[..., np.arange(4), np.arange(4)] = -np.inf
    margins = correct_scores - other_scores.max(axis=-1)
    ties = (scores == scores.max(axis=-1, keepdims=True)).sum(axis=-1) > 1
    zero_queries = query_norms == 0
    return dict(
        predictions=predictions.tolist(),
        scores=scores.tolist(),
        correct=correct.tolist(),
        confusion_counts=confusion.tolist(),
        counts=counts.tolist(),
        per_painter_recall=recall.tolist(),
        macro_accuracy=float(recall.mean()),
        micro_accuracy=float(correct.mean()),
        scene_accuracy=correct.mean(axis=(1, 2)).tolist(),
        margins=margins.tolist(),
        mean_margin=float(margins.mean()),
        query_norms=query_norms.tolist(),
        top_ties=ties.tolist(),
        tie_counts=dict(total=int(ties.sum()), per_scene=ties.sum(axis=(1, 2)).tolist()),
        zero_queries=zero_queries.tolist(),
        zero_query_counts=dict(
            total=int(zero_queries.sum()), per_scene=zero_queries.sum(axis=(1, 2)).tolist()
        ),
    )


def paired_summary(candidate, baseline):
    correct = np.asarray(candidate["correct"])
    base_correct = np.asarray(baseline["correct"])
    return dict(
        accuracy_difference=float(candidate["macro_accuracy"] - baseline["macro_accuracy"]),
        corrected_count=int(np.sum(correct & ~base_correct)),
        newly_incorrect_count=int(np.sum(~correct & base_correct)),
        unchanged_correct_count=int(np.sum(correct & base_correct)),
        unchanged_incorrect_count=int(np.sum(~correct & ~base_correct)),
        scene_accuracy_difference=(
            correct.mean(axis=(1, 2)) - base_correct.mean(axis=(1, 2))
        ).tolist(),
    )


def evaluate_model(named, prototypes):
    """Apply exactly three fixed rules; accepts small constructed dimensions."""
    named = np.asarray(named, dtype=np.float64)
    prototypes = np.asarray(prototypes, dtype=np.float64)
    if named.ndim != 4 or named.shape[0] < 2 or named.shape[1:3] != (2, 4) or named.shape[-1] < 1:
        raise ValueError("named embeddings require (scenes>=2, 2, 4, features>=1)")
    if prototypes.shape != (4, named.shape[-1]):
        raise ValueError("four reference prototypes with matching features required")
    named = unit_vectors(named, "named")
    reference_unit, reference_norms = normalized_prototypes(prototypes, "reference")
    reference_mean = prototypes.mean(axis=0)
    n = len(named)
    score_arrays = {rule: np.empty((*named.shape[:-1], 4)) for rule in RULES}
    norm_arrays = {rule: np.empty(named.shape[:-1]) for rule in RULES}
    folds = []
    for scene in range(n):
        train_scenes = [i for i in range(n) if i != scene]
        train = named[train_scenes]
        training_mean = train.mean(axis=(0, 1, 2))
        translation = reference_mean - training_mean
        query = named[scene]
        translated = query + translation
        translated_norms = np.linalg.norm(translated, axis=-1)
        if not np.isfinite(translated).all() or not np.isfinite(translated_norms).all():
            raise ValueError("invalid translated query")
        generated_means = train.mean(axis=(0, 1))
        generated_unit, generated_norms = normalized_prototypes(generated_means, "generated")
        score_arrays["reference_baseline"][scene] = query @ reference_unit.T
        score_arrays["common_translation"][scene] = translated @ reference_unit.T
        score_arrays["generated_prototype"][scene] = query @ generated_unit.T
        norm_arrays["reference_baseline"][scene] = np.linalg.norm(query, axis=-1)
        norm_arrays["common_translation"][scene] = translated_norms
        norm_arrays["generated_prototype"][scene] = np.linalg.norm(query, axis=-1)
        folds.append(
            dict(
                held_out_scene=scene,
                train_scenes=train_scenes,
                training_image_count=int(np.prod(train.shape[:-1])),
                training_mean=training_mean.tolist(),
                reference_mean=reference_mean.tolist(),
                translation=translation.tolist(),
                translation_norm=float(np.linalg.norm(translation)),
                reference_prototype_norms=reference_norms.tolist(),
                generated_prototype_norms=generated_norms.tolist(),
                generated_prototypes=generated_means.tolist(),
            )
        )
    rules = {rule: summarize_scores(score_arrays[rule], norm_arrays[rule]) for rule in RULES}
    return dict(
        rules=rules,
        folds=folds,
        paired_translation_vs_baseline=paired_summary(
            rules["common_translation"], rules["reference_baseline"]
        ),
        paired_generated_prototype_vs_baseline=paired_summary(
            rules["generated_prototype"], rules["reference_baseline"]
        ),
    )


def assemble_rows(
    rows,
    embeddings,
    *,
    use_regions,
    model_names=MODELS,
    scenes=14,
    reference_counts=REFERENCE_COUNTS,
    development_counts=DEVELOPMENT_COUNTS,
):
    """Strict row assembly; pure array function, with explicit synthetic census overrides."""
    embeddings = np.asarray(embeddings, dtype=np.float64)
    if embeddings.ndim != 2 or embeddings.shape[0] != len(rows) or embeddings.shape[1] < 1:
        raise ValueError("embedding archive must match manifest rows exactly")
    embeddings = unit_vectors(embeddings, "archive")
    keyed = {}
    for row, vector in zip(rows, embeddings):
        key = (row["id"], row["view"])
        if key in keyed or row["view"] not in {"original", "audited_region"}:
            raise ValueError("duplicate or invalid source view")
        if row["role"] not in {"generated", "reference", "development"}:
            raise ValueError("unknown source role")
        keyed[key] = (row, vector)
    for (image_id, view), (row, _) in keyed.items():
        if view == "audited_region":
            original = keyed.get((image_id, "original"))
            if original is None or row["role"] == "generated":
                raise ValueError("region requires a historical original")
            for field in ("role", "painter", "path", "sha256"):
                if row[field] != original[0][field]:
                    raise ValueError("region identity differs from original")
    arms = ("free", "generic", *ARTISTS)
    shape = (len(model_names), scenes, 2, 6)
    x = np.full((*shape, embeddings.shape[1]), np.nan)
    ids = np.empty(shape, dtype=object)
    ids.fill(None)
    panels = {role: [[] for _ in ARTISTS] for role in ("reference", "development")}
    selections = {role: [[] for _ in ARTISTS] for role in panels}
    for (image_id, view), (row, vector) in keyed.items():
        if view != "original":
            continue
        selected_view = "original"
        if use_regions and (image_id, "audited_region") in keyed:
            vector = keyed[(image_id, "audited_region")][1]
            selected_view = "audited_region"
        if row["role"] == "generated":
            if (
                row["repeat"] not in (0, 1)
                or not isinstance(row["scene"], int)
                or not 0 <= row["scene"] < scenes
            ):
                raise ValueError("invalid generated scene/repeat")
            cell = (
                model_names.index(row["model"]),
                row["scene"],
                row["repeat"],
                arms.index(row["arm"]),
            )
            if ids[cell] is not None:
                raise ValueError("duplicate generated request cell")
            x[cell], ids[cell] = vector, image_id
        else:
            painter = ARTISTS.index(row["painter"])
            panels[row["role"]][painter].append(vector)
            selections[row["role"]][painter].append(dict(id=image_id, view=selected_view))
    if not np.isfinite(x).all() or any(v is None for v in ids.flat):
        raise ValueError("incomplete generated census")
    for role, expected in (("reference", reference_counts), ("development", development_counts)):
        if tuple(map(len, panels[role])) != tuple(expected):
            raise ValueError(f"unexpected {role} painter membership")
    return dict(
        named=x[:, :, :, 2:],
        generated_image_ids=ids[:, :, :, 2:].tolist(),
        reference=[np.asarray(group) for group in panels["reference"]],
        development=[np.asarray(group) for group in panels["development"]],
        source_selections=selections,
    )


def binding_paths():
    paths = {PLAN, Path(__file__), ROOT / "pyproject.toml", ROOT / "uv.lock"}
    preserved_plan = PLAN.with_name("PLAN_pre_design_qa.md")
    if preserved_plan.exists():
        paths.add(preserved_plan)
    tests = sorted((ROOT / "tests" / NS).glob("test_*.py"))
    if not tests:
        raise ValueError("synthetic tests must exist before freeze")
    paths.update(tests)
    paths.update(
        LEARNED / name
        for name in (
            "inputs.json",
            "analysis.json",
            "extraction_clip.json",
            "extraction_csd.json",
            "embeddings_clip.npz",
            "embeddings_csd.npz",
            "validation_clip.json",
            "validation_csd.json",
            "csd_adapter_inputs_v2.json",
        )
    )
    paths.update(ROOT / path for path in read(LEARNED / "analysis.json")["bindings"])
    paths.add(ROOT / "src/latent_art_bench/painter_learned_csd_v1.py")
    return sorted(paths)


def verify_original_bindings():
    for path, expected in read(LEARNED / "analysis.json")["bindings"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"original learned binding changed: {path}")


def freeze():
    """Hash only; never assembles data or computes translated predictions."""
    if (OUT / "inputs.json").exists():
        raise FileExistsError("transfer input binding already exists")
    verify_original_bindings()
    inputs = dict(
        schema_version=1,
        study=NS,
        created_utc=datetime.now(timezone.utc).isoformat(),
        status="frozen before real translated outcomes; retrospective known-label task",
        bindings={str(path.relative_to(ROOT)): sha(path) for path in binding_paths()},
        environment=dict(python=platform.python_version(), numpy=np.__version__),
        rules=list(RULES),
        translation_scale=1,
        translated_scores=(
            "raw translated query dot unit reference prototype; no query normalization"
        ),
        split="leave both repeats of one scene out; training separately per configuration",
        invalid_policy=(
            "fail on nonfinite/nonunit inputs or exactly zero prototype norm; "
            "zero translated queries retain all-zero linear scores, first-index tie, "
            "and explicit zero-query counts; cosine is undefined"
        ),
    )
    write_new(OUT / "inputs.json", inputs)


def verify_freeze():
    inputs = read(OUT / "inputs.json")
    expected_paths = {str(path.relative_to(ROOT)) for path in binding_paths()}
    if set(inputs["bindings"]) != expected_paths or inputs["rules"] != list(RULES):
        raise ValueError("transfer binding membership changed")
    for path, expected in inputs["bindings"].items():
        if sha(ROOT / path) != expected:
            raise ValueError(f"frozen transfer input changed: {path}")
    verify_original_bindings()
    return inputs


def assert_baseline_matches(result, retained):
    base = result["rules"]["reference_baseline"]
    for key in ("confusion_counts", "counts", "macro_accuracy", "micro_accuracy"):
        if base[key] != retained[key]:
            raise ValueError(f"baseline differs from retained learned audit: {key}")
    if base["per_painter_recall"] != retained["per_painter_accuracy"]:
        raise ValueError("baseline painter recalls differ from retained learned audit")


def compute_real():
    """Only called after explicit execution authorization; never from synthetic tests."""
    verify_freeze()
    manifest = read(LEARNED / "inputs.json")
    retained = read(LEARNED / "analysis.json")
    rows = manifest["rows"]
    if len(rows) != 2009 or sum(r["view"] == "audited_region" for r in rows) != 131:
        raise ValueError("complete 1878-original plus 131-region census required")
    result = dict(
        schema_version=1,
        study=NS,
        descriptive_only=True,
        inputs_sha256=sha(OUT / "inputs.json"),
        axes=dict(
            models=list(MODELS),
            artists=list(ARTISTS),
            rules=list(RULES),
            scenes=list(range(14)),
            repeats=[0, 1],
        ),
        prediction_axes=["scene", "repeat", "prompted_painter"],
        interpretation=(
            "retrospective held-scene closed-set prompt-name identification; "
            "no perceptual validation or independent replication"
        ),
        representations={},
    )
    for rep in ("clip", "csd"):
        archive = LEARNED / f"embeddings_{rep}.npz"
        with np.load(archive, allow_pickle=False) as npz:
            if set(npz.files) != {"embeddings"}:
                raise ValueError("unexpected embedding archive arrays")
            embeddings = npz["embeddings"]
        if embeddings.shape != (2009, 768):
            raise ValueError("unexpected learned embedding shape")
        result["representations"][rep] = {}
        for view, regions in (("original", False), ("audited_region", True)):
            assembled = assemble_rows(rows, embeddings, use_regions=regions)
            per_view = dict(
                generated_image_ids=assembled["generated_image_ids"],
                source_selections=assembled["source_selections"],
                targets={},
            )
            result["representations"][rep][view] = per_view
            for target, role in (("primary", "reference"), ("development", "development")):
                prototypes = np.array([group.mean(axis=0) for group in assembled[role]])
                known_rows = {
                    row["model"]: row for row in retained[rep][view]["targets"][target]["models"]
                }
                model_results = []
                for model, named in zip(MODELS, assembled["named"]):
                    outcome = evaluate_model(named, prototypes)
                    assert_baseline_matches(outcome, known_rows[model]["recognition"])
                    model_results.append(dict(model=model, **outcome))
                per_view["targets"][target] = dict(
                    counts=list(map(len, assembled[role])),
                    reference_prototypes=prototypes.tolist(),
                    models=model_results,
                    equal_configuration_mean_accuracy_difference={
                        key: float(
                            np.mean([row[key]["accuracy_difference"] for row in model_results])
                        )
                        for key in (
                            "paired_translation_vs_baseline",
                            "paired_generated_prototype_vs_baseline",
                        )
                    },
                )
    verify_freeze()
    return result


def report(result):
    lines = [
        "# Held-scene prototype transfer audit v1",
        "",
        "Retrospective prompt-name identification using existing embeddings; ordinary mean "
        "translation, not a new algorithm or a perceptual-fidelity test.",
        "",
        f"Input binding SHA-256: `{result['inputs_sha256']}`.",
        "",
        "All two encoders × two source views × two reference targets × six configurations "
        "are retained. Each model/fold trains on 104 named images from the other 13 scenes, "
        "excluding both held-out repeats. Translation scale is exactly one. Reference "
        "prototypes are fixed. Generated-prototype context uses painter labels and is "
        "a supervised comparator.",
        "",
        "The target mean averages unnormalized historical centroids, not normalized "
        "classification prototypes. Translation changes class intercepts and leaves "
        "centered painter geometry unchanged within each fold. Its fit uses no free or "
        "generic controls, so it does not isolate the named-minus-generic causal component.",
        "",
        "All 112 predictions per rule/configuration, raw scores, correct-minus-best-incorrect "
        "margins, query/fold norms, tie/zero-query counts, confusion matrices and source "
        "identities are retained in analysis.json. Scores use raw translated queries. A "
        "zero translated query has all-zero linear scores and a first-index tie; its cosine "
        "is undefined. No p-values or uncertainty intervals are reported. Overlapping folds "
        "and the reused development panel are not independent replications.",
        "",
        "Accuracy differences below are percentage points. Scene differences are ordered "
        "0–13. B/T/G denote reference baseline, common translation and supervised generated "
        "prototypes. Painter recall lists follow Monet, Sisley, Pissarro, Cézanne.",
        "",
    ]
    for rep, views in result["representations"].items():
        for view, content in views.items():
            for target, group in content["targets"].items():
                lines += [
                    f"## {rep.upper()} / {view} / {target}",
                    "",
                    "| Configuration | B % | T % | G % | T−B pp | Corrected "
                    "| Newly incorrect | G−B pp |",
                    "|---|---:|---:|---:|---:|---:|---:|---:|",
                ]
                for row in group["models"]:
                    r, p, q = (
                        row["rules"],
                        row["paired_translation_vs_baseline"],
                        row["paired_generated_prototype_vs_baseline"],
                    )
                    cells = [
                        row["model"],
                        *[f"{100 * r[k]['macro_accuracy']:.1f}" for k in RULES],
                        f"{100 * p['accuracy_difference']:+.1f}",
                        str(p["corrected_count"]),
                        str(p["newly_incorrect_count"]),
                        f"{100 * q['accuracy_difference']:+.1f}",
                    ]
                    lines.append("| " + " | ".join(cells) + " |")
                means = group["equal_configuration_mean_accuracy_difference"]
                lines += [
                    "",
                    "Equal-configuration mean differences: "
                    + "; ".join(f"{key}: {100 * value:+.2f} pp" for key, value in means.items())
                    + ".",
                    "",
                ]
                for row in group["models"]:
                    lines += [f"### {row['model']}", ""]
                    for rule in RULES:
                        r = row["rules"][rule]
                        recalls = ", ".join(f"{100 * v:.1f}" for v in r["per_painter_recall"])
                        lines.append(
                            f"- {rule}: painter recalls (%) [{recalls}]; "
                            f"top ties {r['tie_counts']['total']}; "
                            f"zero queries {r['zero_query_counts']['total']}; "
                            f"mean margin {r['mean_margin']:.6f}."
                        )
                    for key in (
                        "paired_translation_vs_baseline",
                        "paired_generated_prototype_vs_baseline",
                    ):
                        differences = ", ".join(
                            f"{100 * v:+.1f}" for v in row[key]["scene_accuracy_difference"]
                        )
                        lines.append(f"- {key}, scene differences (pp): [{differences}].")
                    translation_norms = ", ".join(
                        f"{fold['translation_norm']:.6f}" for fold in row["folds"]
                    )
                    lines.append(
                        f"- Translation L2 norms by held-out scene: [{translation_norms}]."
                    )
                    lines.append("")
    lines += [
        "## Replay",
        "",
        "```sh",
        "uv run --locked python -m latent_art_bench.painter_prototype_transfer_v1 "
        "check --execute-real",
        "```",
        "",
        "Improved prompt-name recovery would not establish physical authorship, human "
        "fidelity, validity of pooled contrast error, an unwanted common painting effect, "
        "unseen-artist generalization, or independence from service drift. CLIP/CSD training "
        "overlap is unknown and the encoders are related. Every adverse outcome is retained.",
        "",
    ]
    return "\n".join(lines)


def execute(check=False):
    targets = (OUT / "analysis.json", OUT / "REPORT.md")
    if not check and any(path.exists() for path in targets):
        raise FileExistsError("completed result/report cannot be overwritten; use a new version")
    result = compute_real()
    rendered = report(result)
    if check:
        if read(targets[0]) != result or targets[1].read_text() != rendered:
            raise ValueError("exact transfer result/report replay differs")
        print("Exact prototype-transfer result and report replay passed")
    else:
        write_new(targets[0], result)
        write_new(targets[1], rendered)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "analyze", "check"))
    parser.add_argument(
        "--execute-real",
        action="store_true",
        help="explicitly authorize real execution after method-design review",
    )
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    elif not args.execute_real:
        parser.error("real outcomes require method-design authorization and --execute-real")
    else:
        execute(check=args.action == "check")


if __name__ == "__main__":
    main()
