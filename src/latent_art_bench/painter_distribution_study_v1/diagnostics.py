"""Stage A: auditable diagnostics of existing numeric evidence, without image access."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench import painter_prompt_retry_v1 as retry
from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_distribution_exploration_v1.analysis import (
    FEATURE_SETS,
    METHOD,
    load,
)
from latent_art_bench.painter_distribution_exploration_v1.statistics import (
    heldout_scores,
    metrics,
    pca_fit,
    project,
    work_folds,
)
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS, SHORT_LABELS
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.calibration_record import _verify_commit
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_prompt_study_v1.generation import ALIASES
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS, TEMPLATE_IDS

from .statistics import (
    content_weights,
    disjoint_splits,
    distribution_summary,
    rng_for,
    transfer_fold,
    transfer_scores,
)

NAMESPACE = "painter_distribution_study_v1"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
METHODS = Path("studies") / NAMESPACE
CONFIG = Path("configs") / NAMESPACE / "diagnostics.json"
MANIFESTS = Path("data/manifests") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
FRAME = Path("data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl")
PROMPTS = Path("data/manifests/painter_feature_generation_v1/prompt_library.json")
CLASSES = ("water_organized", "built_place_organized", "route_organized", "open_or_wooded_land")


def inputs(root):
    painters, records = load(root)
    frame = {r["work_id"]: r for r in read_jsonl(root / FRAME)}
    _, source = retry.load(root)
    combined = retry.combine(
        read_jsonl(source / "measured_features.jsonl"),
        read_jsonl(root / retry.DIRECTORY / "measured_features.jsonl"),
    )
    scaler = read_json(
        root / "data/manifests/painter_feature_generation_v2" / METHOD / "scaler.json"
    )
    scenes = {r["template_id"]: r["scene_group"] for r in read_json(root / PROMPTS)["templates"]}
    free = sorted(
        [r for r in combined if r["condition"] == "artist_free"],
        key=lambda r: r["request_sequence"],
    )
    required_ids = {
        r["image_id"] for p in painters.values() for r in p["items"] if r["domain"] == "original"
    }
    if len(free) != 384 or not required_ids <= set(frame):
        raise ValueError("missing frame identity or artist-free records")
    for data in painters.values():
        for item in data["items"]:
            item["condition"] = "named" if item["domain"] == "generated" else "original"
            item["content_class"] = (
                frame[item["image_id"]]["content_class"]
                if item["domain"] == "original"
                else scenes[item["template_id"]]
            )
        data["values"] = np.concatenate(
            [data["values"], transform(np.array([r["values"] for r in free]), scaler)]
        )
        data["items"].extend(
            dict(
                image_id=r["image_id"],
                domain="generated",
                alias=r["alias"],
                method_id=r["method_id"],
                condition="artist_free",
                template_id=r["template_id"],
                block=r["block"],
                retried=False,
                content_class=scenes[r["template_id"]],
            )
            for r in free
        )
    paths = [Path(r["path"]) for r in records] + [FRAME, PROMPTS]
    return painters, frame, bindings(root, paths)


def selected(data, alias, method, condition):
    return [
        i
        for i, r in enumerate(data["items"])
        if (r["alias"], r["method_id"], r["condition"]) == (alias, method, condition)
    ]


def small_summary(row):
    return {
        k: row[k] for k in ("energy_distance", "sample_variance_ratio", "squared_iqr_sum_ratio")
    }


def classify(x, y, original_ids, generated_items, kernels=("linear", "rbf")):
    labels = np.r_[np.zeros(len(x), dtype=int), np.ones(len(y), dtype=int)]
    folds = np.r_[
        work_folds(original_ids, 16),
        [TEMPLATE_IDS.index(r["template_id"]) for r in generated_items],
    ]
    scores = {kind: heldout_scores(np.r_[x, y], labels, folds, kind) for kind in kernels}
    return labels, folds, scores


def transfer(painters, config):
    summaries, predictions = [], []
    pairs = [
        (p, q, a, a, "cross_painter")
        for p in PAINTER_IDS
        for q in PAINTER_IDS
        if p != q
        for a in ALIASES
    ]
    pairs += [
        (p, p, a, b, "cross_alias") for p in PAINTER_IDS for a in ALIASES for b in ALIASES if a != b
    ]
    count = config["transfer_folds"]
    for source, target, source_alias, target_alias, kind in pairs:
        blocks = []
        for painter, alias in ((source, source_alias), (target, target_alias)):
            data = painters[painter]
            n = data["reference_count"]
            indices = list(range(n)) + selected(data, alias, "by_name", "named")
            items = [dict(data["items"][i]) for i in indices]
            ids = [r["image_id"] for r in items[:n]]
            folds = dict(zip(ids, work_folds(ids, count)))
            for item in items[n:]:
                item["scene_fold"] = TEMPLATE_IDS.index(item["template_id"]) % count
            blocks.append(
                (
                    data["values"][indices],
                    items,
                    folds,
                    np.r_[np.zeros(n, dtype=int), np.ones(64, dtype=int)],
                )
            )
        sx, si, sf, sy = blocks[0]
        tx, ti, tf, ty = blocks[1]
        scores = {k: np.full(len(tx), np.nan) for k in ("linear", "rbf")}
        assigned = np.full(len(tx), -1, dtype=int)
        for fold in range(count):
            train, test = transfer_fold(si, ti, sf, tf, fold)
            if np.any(assigned[test] != -1):
                raise ValueError("target was scored twice")
            for k in scores:
                scores[k][test] = transfer_scores(sx[train], sy[train], tx[test], k)
            assigned[test] = fold
        cell = dict(
            transfer_kind=kind,
            source_painter=source,
            target_painter=target,
            source_alias=source_alias,
            target_alias=target_alias,
        )
        for k in scores:
            summaries.append(dict(**cell, classifier=k, **metrics(ty, scores[k])))
        predictions.extend(
            dict(
                **cell,
                image_id=r["image_id"],
                fold=int(assigned[i]),
                label=int(ty[i]),
                linear_score=float(scores["linear"][i]),
                rbf_score=float(scores["rbf"][i]),
            )
            for i, r in enumerate(ti)
        )
    return summaries, predictions


def compute(painters, frame, config):
    cells, splits, comparisons, classifiers, predictions, mixtures, capture = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    baseline_classifiers, split_members = [], []
    for painter, data in painters.items():
        print(f"Stage A: {painter}", flush=True)
        n = data["reference_count"]
        real, items = data["values"][:n], data["items"][:n]
        ids = [r["image_id"] for r in items]
        classes = [r["content_class"] for r in items]
        counts = Counter(classes)
        mixtures.extend(
            dict(
                painter_id=painter,
                content_class=c,
                original_count=counts[c],
                original_fraction=counts[c] / n,
                intended_generated_fraction=0.25,
            )
            for c in CLASSES
        )
        capture.append(
            dict(
                painter_id=painter,
                original_count=n,
                capture_workflows=dict(Counter(frame[i]["capture_workflow"] for i in ids)),
                collection_ids=dict(Counter(c for i in ids for c in frame[i]["collections"])),
            )
        )
        wx = content_weights(classes, CLASSES)
        group_size = min(config["maximum_matched_group_size"], n // 2)
        draws = disjoint_splits(
            n,
            group_size,
            config["split_draws"],
            rng_for(config["seed"], painter, "reference-splits"),
        )
        for draw, (left, right) in enumerate(draws):
            split_members.append(
                dict(
                    painter_id=painter,
                    draw=draw,
                    left_ids=[ids[i] for i in left],
                    right_ids=[ids[i] for i in right],
                )
            )
            for family, section in FEATURE_SETS.items():
                result = small_summary(
                    distribution_summary(real[left, section], real[right, section])
                )
                splits.append(
                    dict(
                        painter_id=painter,
                        family=family,
                        draw=draw,
                        group_size=group_size,
                        **result,
                    )
                )
            if draw < config["classifier_baseline_draws"]:
                folds = np.r_[
                    work_folds([ids[i] for i in left], 4), work_folds([ids[i] for i in right], 4)
                ]
                labels = np.r_[np.zeros(group_size), np.ones(group_size)]
                for k in ("linear", "rbf"):
                    s = heldout_scores(np.r_[real[left], real[right]], labels, folds, k)
                    baseline_classifiers.append(
                        dict(painter_id=painter, draw=draw, classifier=k, **metrics(labels, s))
                    )
        for alias in ALIASES:
            for method in METHOD_IDS:
                for condition in ("named", "artist_free"):
                    indices = selected(data, alias, method, condition)
                    chosen = [data["items"][i] for i in indices]
                    y = data["values"][indices]
                    if len(y) != 64:
                        raise ValueError("expected 64 generated images per cell")
                    wy = content_weights([r["content_class"] for r in chosen], CLASSES)
                    base = dict(
                        painter_id=painter, alias=alias, method_id=method, condition=condition
                    )
                    subset_rng = rng_for(
                        config["seed"], painter, alias, method, condition, "subset"
                    )
                    subsets = [subset_rng.permutation(len(y))[:group_size] for _ in draws]
                    for family, section in FEATURE_SETS.items():
                        cell = dict(**base, family=family)
                        x, z = real[:, section], y[:, section]
                        for weighting, rw, gw in (
                            ("collected", None, None),
                            ("content_equal", wx, wy),
                        ):
                            result = distribution_summary(x, z, rw, gw)
                            cells.append(
                                dict(
                                    **cell,
                                    weighting=weighting,
                                    original_count=n,
                                    generated_count=len(y),
                                    **result,
                                )
                            )
                        labels, folds, scores = classify(x, z, ids, chosen)
                        for k, values in scores.items():
                            classifiers.append(
                                dict(**cell, classifier=k, **metrics(labels, values))
                            )
                        if family == "all31":
                            all_items = items + chosen
                            predictions.extend(
                                dict(
                                    **cell,
                                    image_id=r["image_id"],
                                    fold=int(folds[i]),
                                    label=int(labels[i]),
                                    linear_score=float(scores["linear"][i]),
                                    rbf_score=float(scores["rbf"][i]),
                                )
                                for i, r in enumerate(all_items)
                            )
                        for draw, ((left, _), subset) in enumerate(zip(draws, subsets)):
                            result = small_summary(distribution_summary(x[left], z[subset]))
                            comparisons.append(
                                dict(**cell, draw=draw, group_size=group_size, **result)
                            )
    transfer_results, transfer_predictions = transfer(painters, config)
    return dict(
        cells=cells,
        reference_splits=splits,
        matched_comparisons=comparisons,
        classifiers=classifiers,
        predictions=predictions,
        content_mixtures=mixtures,
        capture_inventory=capture,
        reference_classifier_baselines=baseline_classifiers,
        transfer=transfer_results,
        transfer_predictions=transfer_predictions,
        split_members=split_members,
    )


def csv_write(path, rows):
    if not rows:
        raise ValueError("empty output table")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v, separators=(",", ":")) if isinstance(v, (list, dict)) else v
                for k, v in row.items()
            }
            for row in rows
        )


def plots(data, painters, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": NAMESPACE})
    directory = output / "plots"
    directory.mkdir()

    def save(fig, name):
        for ext in ("png", "svg"):
            metadata = (
                {"Software": NAMESPACE} if ext == "png" else {"Date": None, "Creator": NAMESPACE}
            )
            fig.savefig(directory / f"{name}.{ext}", dpi=150, metadata=metadata)
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for ax, painter in zip(axes.flat, PAINTER_IDS):
        rows = [r for r in data["cells"] if r["painter_id"] == painter and r["family"] == "all31"]
        for condition, color, marker in (
            ("named", "#0072B2", "o"),
            ("artist_free", "#D55E00", "^"),
        ):
            collected = [
                r for r in rows if r["condition"] == condition and r["weighting"] == "collected"
            ]
            equal = [
                r for r in rows if r["condition"] == condition and r["weighting"] == "content_equal"
            ]
            ax.scatter(
                [r["population_variance_ratio"] for r in collected],
                [r["population_variance_ratio"] for r in equal],
                label=condition.replace("_", " "),
                color=color,
                marker=marker,
                s=48,
            )
        high = max(1.05, max(r["population_variance_ratio"] for r in rows) * 1.1)
        ax.plot([0, high], [0, high], color="#777777", linewidth=1, linestyle="--")
        ax.set(
            xlim=(0, high),
            ylim=(0, high),
            title=SHORT_LABELS[painter],
            xlabel="Collected-mixture variance ratio",
            ylabel="Content-equal variance ratio",
        )
        ax.legend()
    fig.suptitle(
        "Does matching the intended content mixture change feature spread?\n"
        "All 31 features; original content metadata versus assigned prompt categories"
    )
    save(fig, "content_standardization")

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout="constrained")
    for ax, painter in zip(axes.flat, PAINTER_IDS):
        groups = [
            [
                r["energy_distance"]
                for r in data["reference_splits"]
                if r["painter_id"] == painter and r["family"] == "all31"
            ]
        ]
        labels = ["Real / real"]
        for alias in ALIASES:
            for condition in ("named", "artist_free"):
                groups.append(
                    [
                        r["energy_distance"]
                        for r in data["matched_comparisons"]
                        if (
                            r["painter_id"],
                            r["family"],
                            r["alias"],
                            r["method_id"],
                            r["condition"],
                        )
                        == (painter, "all31", alias, "by_name", condition)
                    ]
                )
                labels.append(f"Alias {alias[-1]}\n{condition.replace('_', ' ')}")
        ax.boxplot(groups, tick_labels=labels, showfliers=True)
        ax.set(title=SHORT_LABELS[painter], ylabel="Energy discrepancy in all 31 features")
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle(
        "Equal-size disjoint reference splits and generated comparisons\n"
        "128 subsampling draws; boxes are descriptive, not confidence intervals"
    )
    save(fig, "matched_reference_baselines")

    fig, axes = plt.subplots(4, 2, figsize=(12, 19), layout="constrained")
    for row, painter in enumerate(PAINTER_IDS):
        item = painters[painter]
        n = item["reference_count"]
        groups = {
            (a, c): selected(item, a, "by_name", c)
            for a in ALIASES
            for c in ("named", "artist_free")
        }
        indices = list(range(n)) + [i for g in groups.values() for i in g]
        weights = np.r_[np.full(n, 1 / (3 * n)), np.full(256, 1 / 384)]
        fit = pca_fit(item["values"][indices], weights)
        xy = project(item["values"], fit)
        chosen_xy = xy[indices]
        limits = []
        for j in (0, 1):
            low, high = chosen_xy[:, j].min(), chosen_xy[:, j].max()
            margin = max(0.05, (high - low) * 0.06)
            limits.append((low - margin, high + margin))
        for col, alias in enumerate(ALIASES):
            ax = axes[row, col]
            ax.scatter(xy[:n, 0], xy[:n, 1], color="#666666", alpha=0.45, s=12, label="Original")
            for condition, color, marker in (
                ("named", "#0072B2", "o"),
                ("artist_free", "#D55E00", "^"),
            ):
                coords = xy[groups[alias, condition]]
                ax.scatter(
                    coords[:, 0],
                    coords[:, 1],
                    color=color,
                    marker=marker,
                    alpha=0.65,
                    s=23,
                    label=condition.replace("_", " "),
                )
            ratio = fit["explained_variance_ratio"]
            ax.set(
                title=f"{SHORT_LABELS[painter]} | {alias}",
                xlim=limits[0],
                ylim=limits[1],
                xlabel=f"PC1 ({ratio[0]:.1%})",
                ylabel=f"PC2 ({ratio[1]:.1%})",
            )
            ax.set_aspect("equal", adjustable="box")
            ax.legend(fontsize=8)
    fig.suptitle(
        "Original, painter-name and artist-free feature distributions\n"
        "By-name method; common PCA axes within painter; all points retained"
    )
    save(fig, "named_artist_free_pca")


def report_text(data):
    original = [
        r for r in data["cells"] if r["family"] == "all31" and r["weighting"] == "collected"
    ]
    equal = [
        r for r in data["cells"] if r["family"] == "all31" and r["weighting"] == "content_equal"
    ]
    classify_rows = [r for r in data["classifiers"] if r["family"] == "all31"]
    text = [
        "# Existing-data explanation of painter-feature distribution gaps",
        "Stage A of Painter Distribution Study v1. Post-hoc numeric diagnostics; "
        "no new images, image opening, feature extraction, generation, or human ratings.",
        "## Findings",
        "| Condition | Collected variance ratio | Content-equal variance ratio | "
        "Squared-IQR spread ratio | RBF balanced accuracy |",
        "| --- | --- | --- | --- | --- |",
    ]
    for condition in ("named", "artist_free"):
        ranges = []
        for rows, key in (
            (original, "sample_variance_ratio"),
            (equal, "population_variance_ratio"),
            (original, "squared_iqr_sum_ratio"),
            ([r for r in classify_rows if r["classifier"] == "rbf"], "balanced_accuracy"),
        ):
            vals = [r[key] for r in rows if r["condition"] == condition and r[key] is not None]
            ranges.append(f"{min(vals):.3f}-{max(vals):.3f}")
        text.append("| " + " | ".join([condition, *ranges]) + " |")
    text += [
        "Ranges span all four painters, two aliases and three prompt methods. "
        "Ordinary sample variance and weighted population variance have different finite-N "
        "denominators; the content plot compares population definitions on both axes.",
        "![Content standardization](plots/content_standardization.png)",
        "## Sample-size baseline",
        "| Painter | Equal group size | Real/real median energy | "
        "Named median energy | Artist-free median energy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for painter in PAINTER_IDS:
        baseline = [
            r
            for r in data["reference_splits"]
            if r["painter_id"] == painter and r["family"] == "all31"
        ]
        vals = [np.median([r["energy_distance"] for r in baseline])]
        for condition in ("named", "artist_free"):
            vals.append(
                np.median(
                    [
                        r["energy_distance"]
                        for r in data["matched_comparisons"]
                        if (r["painter_id"], r["family"], r["condition"])
                        == (painter, "all31", condition)
                    ]
                )
            )
        text.append(
            f"| {SHORT_LABELS[painter]} | {baseline[0]['group_size']} | "
            + " | ".join(f"{v:.4f}" for v in vals)
            + " |"
        )
    text += [
        "The generated medians pool aliases and methods descriptively; the figure shows "
        "by-name cells separately. Draws reuse the corpus and are not independent experiments.",
        "![Reference baselines](plots/matched_reference_baselines.png)",
        "## Distribution geometry",
        "![Named and artist-free PCA](plots/named_artist_free_pca.png)",
        "PCA is descriptive and unsupervised. Full-space classifiers are fixed and evaluated "
        "on held-out scene families and original works. The two service aliases do not attest "
        "two distinct model snapshots.",
        "## Transfer diagnostics",
        "| Transfer | Classifier | Balanced accuracy range | Median |",
        "| --- | --- | ---: | ---: |",
    ]
    for kind in ("cross_painter", "cross_alias"):
        for classifier in ("linear", "rbf"):
            v = [
                r["balanced_accuracy"]
                for r in data["transfer"]
                if r["transfer_kind"] == kind and r["classifier"] == classifier
            ]
            text.append(
                f"| {kind} | {classifier} | {min(v):.3f}-{max(v):.3f} | {np.median(v):.3f} |"
            )
    text += [
        "Transfer excludes target scene families from training and holds out physical works. "
        "A transferable detector is compatible with generic synthetic/capture signatures; "
        "it does not show that painter-specific cues are absent.",
        "## Interpretation and next stage",
        "The content adjustment uses recorded original categories and assigned prompt categories. "
        "Actual depicted content and viewpoint were not independently annotated. Consequently "
        "it is a mixture sensitivity, not a completed content-matched validation. The four broad "
        "categories cannot remove all composition differences. Capture remains unresolved; "
        "collection identifiers do not demonstrate independent photographic events.",
        "No p-values, population confidence intervals, artistic-equivalence margin or aesthetic "
        "ranking is asserted. Source counts, all family effects, individual subsampling draws, "
        "split membership and held-out predictions are retained. The new reference and endpoint "
        "audit is required before the prospective generation stage.",
        "[Fixed methods](../../../studies/painter_distribution_study_v1/DIAGNOSTICS.md). "
        "Run from the repository root:",
        "```bash",
        "uv run --locked --extra analysis --extra learned python -m "
        "latent_art_bench.painter_distribution_study_v1.diagnostics check",
        "```",
        "Validation is performed by the maintainer agent, without institutional independence.",
    ]
    rendered = text[0]
    for previous, line in zip(text, text[1:]):
        separator = "\n" if previous.startswith("|") and line.startswith("|") else "\n\n"
        rendered += separator + line
    return rendered + "\n"


def render(data, painters, output):
    output.mkdir(parents=True)
    for name, rows in data.items():
        if name in {"capture_inventory", "split_members"}:
            publish(output / f"{name}.json", rows)
        else:
            csv_write(output / f"{name}.csv", rows)
    plots(data, painters, output)
    (output / "REPORT.md").write_text(report_text(data), encoding="utf-8")


def prepare(root):
    config = read_json(root / CONFIG)
    _, _, evidence = inputs(root)
    paths = [Path(r["path"]) for r in evidence] + [
        CONFIG,
        METHODS / "PROTOCOL.md",
        METHODS / "DIAGNOSTICS.md",
        PACKAGE / "__init__.py",
        PACKAGE / "statistics.py",
        PACKAGE / "diagnostics.py",
        Path("tests") / NAMESPACE / "test_statistics.py",
        Path("tests") / NAMESPACE / "test_diagnostics.py",
    ]
    for name, module in list(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if name.startswith("latent_art_bench") and filename and filename.endswith(".py"):
            paths.append(Path(filename).resolve().relative_to(root.resolve()))
    paths = sorted(set(paths))
    commit = committed(root, paths)
    freeze = dict(
        schema_version="painter-distribution-stage-a-freeze/1.0",
        run_id=config["run_id"],
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
    )
    publish(root / MANIFESTS / config["run_id"] / "freeze.json", freeze)
    return freeze


def run(root, check=False):
    config = read_json(root / CONFIG)
    directory = root / MANIFESTS / config["run_id"]
    freeze = read_json(directory / "freeze.json")
    verify_bindings(root, freeze["inputs"])
    _verify_commit(root, freeze["recorded_git_commit"], freeze["inputs"])
    committed(root, [(directory / "freeze.json").relative_to(root)])
    output = root / REPORTS / config["run_id"]
    if not check and output.exists():
        raise FileExistsError("diagnostic report already exists; use check")
    if check:
        receipt = read_json(directory / "report_receipt.json")
        if receipt["freeze_sha256"] != hash_file(directory / "freeze.json"):
            raise ValueError("report freeze binding mismatch")
        verify_bindings(root, receipt["files"])
    painters, frame, _ = inputs(root)
    data = compute(painters, frame, config)
    if check:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "report"
            render(data, painters, target)
            replay_paths = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
            recorded_paths = {p.relative_to(output) for p in output.rglob("*") if p.is_file()}
            if replay_paths != recorded_paths:
                raise ValueError("replayed report file inventory differs")
            for path in target.rglob("*"):
                if (
                    path.is_file()
                    and path.read_bytes() != (output / path.relative_to(target)).read_bytes()
                ):
                    raise ValueError(f"replay differs: {path.name}")
        return dict(status="reproduced", files=len(receipt["files"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".stage-a-build-", dir=output.parent) as temp:
        target = Path(temp) / "report"
        render(data, painters, target)
        target.rename(output)
    receipt = dict(
        schema_version="painter-distribution-stage-a-report/1.0",
        run_id=config["run_id"],
        recorded_git_commit=freeze["recorded_git_commit"],
        freeze_sha256=hash_file(directory / "freeze.json"),
        files=bindings(root, [p.relative_to(root) for p in output.rglob("*") if p.is_file()]),
    )
    publish(directory / "report_receipt.json", receipt)
    return dict(status="built", files=len(receipt["files"]), report=str(output.relative_to(root)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "check"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = (
        prepare(args.root) if args.command == "prepare" else run(args.root, args.command == "check")
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
