"""Paired full-population 496-pixel crop sensitivity; never an independent-capture panel."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features, statistics
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    bindings,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.empirical import (
    finite_comparisons,
    generated_groups,
    load_stage,
)
from latent_art_bench.painter_feature_generation_v2.pipeline import (
    _access_writer,
    _append_row,
    measure_one,
)


def paired_changes(uncropped: list[dict], cropped: list[dict], scaler: dict) -> dict:
    left = {r["image_id"]: r for r in uncropped}
    right = {r["image_id"]: r for r in cropped}
    if len(left) != len(uncropped) or len(right) != len(cropped) or set(left) != set(right):
        raise ValueError("robustness branches do not have the same unique population")
    failures = [
        key for key in left if any(side[key]["status"] != "measured" for side in (left, right))
    ]
    if failures:
        return dict(
            status="incomplete_paired_features",
            failed_image_ids=failures,
            expected_records=len(left),
            comparisons=None,
        )
    result, shifts, incomplete_aliases = {}, [], set()
    for label, records in (("uncropped", uncropped), ("cropped", cropped)):
        real = {
            p: statistics.transform(
                np.array(
                    [
                        r["values"]
                        for r in records
                        if r["domain"] == "real"
                        and r["role"] == "confirmation"
                        and r["painter_id"] == p
                    ]
                ),
                scaler,
            )
            for p in PAINTER_IDS
        }
        generated = [r for r in records if r["domain"] == "generated"]
        groups = {}
        for alias in sorted({r.get("alias", "sd-turbo") for r in generated}):
            selected = [r for r in generated if r.get("alias", "sd-turbo") == alias]
            try:
                groups.update(generated_groups(selected, scaler))
            except ValueError:
                incomplete_aliases.add(alias)
        result[label] = {a: finite_comparisons(real, g) for a, g in groups.items()}
    differences = {}
    for alias, original in result["uncropped"].items():
        changes = []
        for a, b in zip(original["endpoints"], result["cropped"][alias]["endpoints"]):
            keys = ("painter_id", "family", "endpoint", "comparison")
            if any(a[k] != b[k] for k in keys):
                raise ValueError("crop endpoint alignment changed")
            changes.append(
                dict(
                    {k: a[k] for k in keys},
                    uncropped=a["estimate"],
                    cropped=b["estimate"],
                    change=b["estimate"] - a["estimate"],
                )
            )
        differences[alias] = changes
    group_keys = sorted(
        {
            (
                r["domain"],
                r.get("alias", "sd-turbo") if r["domain"] == "generated" else r["role"],
                r.get("condition", r.get("painter_id")),
            )
            for r in uncropped
        }
    )
    for domain, group, condition in group_keys:
        ids = [
            r["image_id"]
            for r in uncropped
            if r["domain"] == domain
            and (r.get("alias", "sd-turbo") if domain == "generated" else r["role"]) == group
            and r.get("condition", r.get("painter_id")) == condition
        ]
        a = statistics.transform(np.array([left[k]["values"] for k in ids]), scaler)
        b = statistics.transform(np.array([right[k]["values"] for k in ids]), scaler)
        shifts.append(
            dict(
                domain=domain,
                group=group,
                condition=condition,
                records=len(ids),
                family_l2_median_max={
                    f: np.quantile(np.linalg.norm((b - a)[:, s], axis=1), [0.5, 1]).tolist()
                    for f, s in features.FAMILIES.items()
                },
            )
        )
    return dict(
        status="complete_paired_features",
        expected_records=len(left),
        comparisons=result,
        endpoint_changes=differences,
        paired_feature_shifts=shifts,
        incomplete_comparison_aliases=sorted(incomplete_aliases),
        note="Both branches use the uncropped-496 development scaler. No CIs; "
        "these are dependent crops of the same captures, not capture calibration.",
    )


def _population(root: Path, base: Path, frozen: dict) -> tuple[list[dict], list[Path]]:
    inputs, population = [], []
    raw = {
        r["work_id"]: r
        for r in read_jsonl(root / MANIFESTS / frozen["acquisition_id"] / "acquisitions.jsonl")
    }
    for stage in ("development", "qualification", "confirmation"):
        rows = load_stage(base, stage)
        inputs += [
            (base / f"{stage}_{suffix}").relative_to(root)
            for suffix in ("features.jsonl", "receipt.json")
        ]
        for row in rows:
            if row["status"] != "measured":
                continue
            source = raw[row["image_id"]]
            if row["raw_sha256"] != source["raw_sha256"]:
                raise ValueError("primary/acquisition source hash mismatch")
            population.append(
                dict(
                    source, image_id=row["image_id"], source_image_id=row["image_id"], domain="real"
                )
            )
    for experiment in frozen["experiment_ids"]:
        gen_dir = MANIFESTS / experiment
        receipt = read_json(root / gen_dir / "generation_receipt.json")
        if not receipt["complete_generated_grid"]:
            continue
        directory = base / "experiments" / experiment
        rows = load_stage(directory, "generated")
        inputs += [
            (directory / f"generated_{suffix}").relative_to(root)
            for suffix in ("features.jsonl", "receipt.json")
        ]
        outputs = {r["request_id"]: r for r in read_jsonl(root / gen_dir / "outputs.jsonl")}
        for row in rows:
            if row["status"] != "measured":
                continue
            source = outputs[row["image_id"]]
            if row["raw_sha256"] != source["sha256"]:
                raise ValueError("primary/generation source hash mismatch")
            population.append(
                dict(
                    source,
                    image_id=f"{experiment}:{row['image_id']}",
                    source_image_id=row["image_id"],
                    raw_path=source["image_path"],
                    raw_sha256=source["sha256"],
                    domain="generated",
                    experiment_id=experiment,
                )
            )
    if not population or len({r["image_id"] for r in population}) != len(population):
        raise ValueError("robustness requires a unique nonempty population")
    return population, inputs


def execute(root: Path, method_id: str) -> dict:
    identifier(method_id)
    with stage_lock(root / WORKSPACE / method_id / ".measurement.writer.lock"):
        return _execute(root, method_id)


def _execute(root: Path, method_id: str) -> dict:
    base = root / MANIFESTS / method_id
    output = base / "robustness"
    if (output / "robustness_analysis.json").exists():
        raise FileExistsError("robustness is terminal")
    frozen = read_json(base / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    verify_bindings(root, read_json(base / "confirmation_opening.json")["inputs"])
    population, inputs = _population(root, base, frozen)
    inputs += [
        (base / name).relative_to(root)
        for name in ("method_freeze.json", "confirmation_opening.json")
    ]
    output.mkdir(parents=True, exist_ok=True)
    append_access = _access_writer(base / "access_events.jsonl")
    all_rows = {}
    for stage, crop in (("uncropped", 0.0), ("cropped", 0.01)):
        if (output / f"{stage}_receipt.json").exists():
            all_rows[stage] = load_stage(output, stage)
            continue
        path = output / f"{stage}_features.jsonl"
        prior = read_jsonl(path) if path.exists() else []
        done = {r["image_id"]: r for r in prior}
        expected = {r["image_id"]: r for r in population}
        if len(done) != len(prior) or not set(done) <= set(expected):
            raise ValueError("prior crop population changed")

        def pending():
            for item in population:
                if item["image_id"] in done:
                    if item["raw_sha256"] != done[item["image_id"]]["raw_sha256"]:
                        raise ValueError("prior crop source hash changed")
                    continue
                raw = (root / item["raw_path"]).resolve()
                raw.relative_to((root / WORKSPACE).resolve())
                append_access(
                    dict(
                        kind="feature_read",
                        stage=f"robustness_{stage}",
                        image_id=item["image_id"],
                        raw_sha256=item["raw_sha256"],
                        experiment_id=item.get("experiment_id"),
                    ),
                )
                if hash_file(raw) != item["raw_sha256"]:
                    raise ValueError("raw image changed before crop measurement")
                yield dict(item, path=str(raw), stage=stage)

        with ThreadPoolExecutor(max_workers=frozen["feature_workers"]) as pool:
            for row in pool.map(lambda item: measure_one(item, 496, crop), pending()):
                _append_row(path, row)
                done[row["image_id"]] = row
                if len(done) % 50 == 0 or len(done) == len(population):
                    print(f"{stage} crop features {len(done)}/{len(population)}", flush=True)
        all_rows[stage] = [done[r["image_id"]] for r in population]
        publish(
            output / f"{stage}_receipt.json",
            dict(
                stage=stage,
                expected_records=len(population),
                terminal_records=len(done),
                statuses=dict(Counter(r["status"] for r in done.values())),
                short_side=496,
                crop_fraction=crop,
                feature_file_sha256=hash_file(path),
                inputs=bindings(root, inputs),
                completed_at_utc=utc_now().isoformat(),
            ),
        )
    scaler_path = output / "scaler.json"
    if scaler_path.exists():
        scaler = read_json(scaler_path)
        if scaler["uncropped_feature_sha256"] != hash_file(output / "uncropped_features.jsonl"):
            raise ValueError("crop scaler source changed")
    else:
        new = {
            p: np.array(
                [
                    r["values"]
                    for r in all_rows["uncropped"]
                    if r["domain"] == "real"
                    and r["role"] == "development"
                    and r["painter_id"] == p
                    and r["status"] == "measured"
                ]
            )
            for p in PAINTER_IDS
        }
        scaler = statistics.fit_scaler(new)
        scaler["uncropped_feature_sha256"] = hash_file(output / "uncropped_features.jsonl")
        publish(scaler_path, scaler)
    result = paired_changes(all_rows["uncropped"], all_rows["cropped"], scaler)
    inputs += [
        (output / name).relative_to(root)
        for name in (
            "uncropped_features.jsonl",
            "cropped_features.jsonl",
            "uncropped_receipt.json",
            "cropped_receipt.json",
            "scaler.json",
        )
    ]
    result.update(inputs=bindings(root, inputs), completed_at_utc=utc_now().isoformat())
    publish(output / "robustness_analysis.json", result)
    return result
