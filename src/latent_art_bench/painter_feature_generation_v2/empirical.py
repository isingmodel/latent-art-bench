"""Common finite descriptive comparisons and acquisition/source diagnostics for every service."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features, statistics
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    bindings,
    identifier,
    publish,
    verify_bindings,
)


def load_stage(directory: Path, stage: str) -> list[dict]:
    receipt = read_json(directory / f"{stage}_receipt.json")
    file = directory / f"{stage}_features.jsonl"
    if hash_file(file) != receipt["feature_file_sha256"]:
        raise ValueError("measured stage bytes changed")
    rows = read_jsonl(file)
    if (
        len(rows) != receipt["terminal_records"]
        or len(rows) != receipt["expected_records"]
        or len({r["image_id"] for r in rows}) != len(rows)
        or dict(Counter(r["status"] for r in rows)) != receipt["statuses"]
    ):
        raise ValueError("measurement stage count or identities changed")
    return rows


def finite_comparisons(real: dict, generated: dict) -> dict:
    if set(real) != set(PAINTER_IDS) or set(generated) != {*PAINTER_IDS, "artist_free"}:
        raise ValueError("all painters and artist-free conditions are required")
    if any(
        np.ndim(x) != 2 or np.shape(x)[1] != 31 or len(x) < 1 or not np.isfinite(x).all()
        for x in [*real.values(), *generated.values()]
    ):
        raise ValueError("finite comparison requires nonempty finite 31-coordinate matrices")
    endpoints, coordinates = [], []
    for family, section in features.FAMILIES.items():
        distances = {
            (c, p): statistics.finite_energy(x[:, section], y[:, section])
            for c, y in generated.items()
            for p, x in real.items()
        }
        for painter in PAINTER_IDS:
            own = distances[painter, painter]
            values = [
                ("target_fit", None, own),
                ("control_improvement", "artist_free", own - distances["artist_free", painter]),
            ]
            values += [
                ("specificity", q, own - distances[painter, q]) for q in PAINTER_IDS if q != painter
            ]
            for endpoint, comparison, estimate in values:
                endpoints.append(
                    dict(
                        painter_id=painter,
                        family=family,
                        endpoint=endpoint,
                        comparison=comparison,
                        estimate=estimate,
                        status="descriptive",
                    )
                )
            x, y = real[painter], generated[painter]
            for i in range(section.start, section.stop):
                real_iqr = float(np.diff(np.quantile(x[:, i], [0.25, 0.75]))[0])
                gen_iqr = float(np.diff(np.quantile(y[:, i], [0.25, 0.75]))[0])
                coordinates.append(
                    dict(
                        painter_id=painter,
                        family=family,
                        coordinate=features.NAMES[i],
                        median_difference=float(np.median(y[:, i]) - np.median(x[:, i])),
                        iqr_ratio=gen_iqr / real_iqr if real_iqr > 0 else None,
                    )
                )
    return dict(
        endpoints=endpoints,
        coordinate_diagnostics=coordinates,
        real_counts={p: len(x) for p, x in real.items()},
        generated_counts={p: len(x) for p, x in generated.items()},
        estimator="finite_empirical_energy_V_statistic",
        confidence_intervals=None,
        inference="descriptive fixed observed populations; not a model ranking",
    )


def generated_groups(rows: list[dict], scaler: dict) -> dict[str, dict]:
    result = {}
    for alias in sorted({r.get("alias", "sd-turbo") for r in rows}):
        chosen = [r for r in rows if r.get("alias", "sd-turbo") == alias]
        if any(r["status"] != "measured" for r in chosen):
            raise ValueError("generated measurements incomplete")
        groups = {}
        expected_keys = None
        for condition in (*PAINTER_IDS, "artist_free"):
            samples = sorted(
                (r for r in chosen if r["condition"] == condition),
                key=lambda r: (r["block"], r["template_id"]),
            )
            keys = {(r["block"], r["template_id"]) for r in samples}
            if (
                not samples
                or len(keys) != len(samples)
                or len(samples) != 16 * len({r["block"] for r in samples})
                or len({r["template_id"] for r in samples}) != 16
                or (expected_keys is not None and keys != expected_keys)
            ):
                raise ValueError("not a complete condition/template/repetition grid")
            expected_keys = keys
            groups[condition] = statistics.transform(
                np.array([r["values"] for r in samples]), scaler
            )
        result[alias] = groups
    return result


def copy_diagnostics(references: list[dict], generated: list[dict]) -> dict:
    if not references:
        return dict(status="no_reference", candidates=[])
    by_raw = defaultdict(list)
    for row in references:
        by_raw[row["raw_sha256"]].append(row["image_id"])
    candidates = []
    reference_phashes = [int(r["phash"], 16) for r in references]
    for row in generated:
        distance, nearest = min(
            (bin(int(row["phash"], 16) ^ value).count("1"), i)
            for i, value in enumerate(reference_phashes)
        )
        exact = by_raw.get(row["raw_sha256"], [])
        if distance <= 8 or exact:
            candidates.append(
                dict(
                    request_id=row["image_id"],
                    nearest_phash_reference=references[nearest]["image_id"],
                    phash_hamming_distance=distance,
                    exact_file_references=exact,
                )
            )
    return dict(
        searched_real_records=len(references),
        candidates=candidates,
        generated_exact_duplicate_excess=len(generated) - len({r["raw_sha256"] for r in generated}),
        limitation="Uncalibrated 63-bit perceptual hash; not copying adjudication or "
        "evidence of training-data nonoverlap.",
    )


def metadata_diagnostics(frame: list, acquisitions: list, real_stages: dict) -> dict:
    acquired = {r["work_id"]: r for r in acquisitions}
    measured = {r["image_id"]: r for rows in real_stages.values() for r in rows}
    rows = []
    for painter in PAINTER_IDS:
        for role in ("development", "historical_development", "qualification", "confirmation"):
            chosen = [r for r in frame if r["painter_id"] == painter and r["role"] == role]
            good = [
                measured[r["work_id"]]
                for r in chosen
                if measured.get(r["work_id"], {}).get("status") == "measured"
            ]
            collections, content = Counter(), Counter()
            for r in chosen:
                collections.update(r["collections"] or ["unknown"])
                content.update([r.get("content_class", "unknown")])
            rows.append(
                dict(
                    painter_id=painter,
                    role=role,
                    frame_count=len(chosen),
                    acquired_count=sum(
                        acquired[r["work_id"]]["status"] == "acquired" for r in chosen
                    ),
                    measured_count=len(good),
                    collection_memberships=dict(collections),
                    content_memberships=dict(content),
                    profile_counts=dict(Counter(r["normalization"]["color_profile"] for r in good)),
                    acquisition_failure_reasons=dict(
                        Counter(
                            acquired[r["work_id"]].get("error")
                            for r in chosen
                            if acquired[r["work_id"]]["status"] != "acquired"
                        )
                    ),
                    measurement_failure_reasons=dict(
                        Counter(
                            measured[r["work_id"]].get("error", "unspecified")
                            for r in chosen
                            if measured.get(r["work_id"], {}).get("status") == "failed"
                        )
                    ),
                    measured_short_side_summary=(
                        np.quantile(
                            [
                                min(
                                    r["normalization"]["original_width"],
                                    r["normalization"]["original_height"],
                                )
                                for r in good
                            ],
                            [0, 0.5, 1],
                        ).tolist()
                        if good
                        else None
                    ),
                    measured_aspect_ratio_summary=(
                        np.quantile(
                            [
                                r["normalization"]["original_width"]
                                / r["normalization"]["original_height"]
                                for r in good
                            ],
                            [0, 0.5, 1],
                        ).tolist()
                        if good
                        else None
                    ),
                )
            )
    return dict(
        by_painter_and_role=rows,
        note="Collection memberships can be multiple; content class is single-valued. "
        "Collections are not capture workflows.",
    )


def stratified_distances(frame, confirmation, generated, scaler):
    lookup = {r["work_id"]: r for r in frame}
    output = []
    for alias, groups in generated.items():
        for painter in PAINTER_IDS:
            rows = [r for r in confirmation if r["painter_id"] == painter]
            strata = defaultdict(list)
            for row in rows:
                strata["profile", row["normalization"]["color_profile"]].append(row)
                content = lookup[row["image_id"]].get("content_class", "unknown")
                strata["content", content].append(row)
                native = row["normalization"]
                if "original_width" in native and "original_height" in native:
                    short = min(native["original_width"], native["original_height"])
                    resolution = (
                        "1024-2047" if short < 2048 else "2048-4095" if short < 4096 else "4096+"
                    )
                    strata["native_short_side", resolution].append(row)
            for (kind, label), selected in sorted(strata.items()):
                record = dict(
                    alias=alias,
                    painter_id=painter,
                    stratum_kind=kind,
                    stratum=label,
                    records=len(selected),
                    status="sparse_unresolved",
                )
                if len(selected) >= 10:
                    real = statistics.transform(np.array([r["values"] for r in selected]), scaler)
                    record.update(
                        status="descriptive_unmatched_generated_content",
                        families={
                            f: statistics.finite_energy(real[:, s], groups[painter][:, s])
                            for f, s in features.FAMILIES.items()
                        },
                    )
                output.append(record)
    return output


def service_diagnostics(rows: list[dict]) -> dict:
    output = {}
    for alias in sorted({r.get("alias", "sd-turbo") for r in rows}):
        chosen = [r for r in rows if r.get("alias", "sd-turbo") == alias]
        latencies = [r["latency_seconds"] for r in chosen if "latency_seconds" in r]
        mismatches = Counter(k for r in chosen for k in r.get("requested_returned_mismatches", []))
        output[alias] = dict(
            statuses=dict(Counter(r["status"] for r in chosen)),
            reported_settings={
                k: dict(Counter(str(r.get("reported", {}).get(k)) for r in chosen))
                for k in ("model", "quality", "size", "output_format")
            },
            decoded_sizes=dict(
                Counter(
                    r.get(
                        "decoded_size",
                        f"{r['width']}x{r['height']}"
                        if "width" in r and "height" in r
                        else "unreported",
                    )
                    for r in chosen
                )
            ),
            setting_mismatches=dict(mismatches),
            latency_seconds_min_median_max=np.quantile(latencies, [0, 0.5, 1]).tolist()
            if latencies
            else None,
        )
    return output


def analyze(root: Path, method_id: str) -> dict:
    identifier(method_id)
    output = root / MANIFESTS / method_id
    if (output / "empirical_analysis.json").exists():
        raise FileExistsError("empirical result is terminal")
    frozen = read_json(output / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    opening = read_json(output / "confirmation_opening.json")
    verify_bindings(root, opening["inputs"])
    scaler = read_json(output / "scaler.json")
    real_stages = {
        stage: load_stage(output, stage)
        for stage in ("development", "qualification", "confirmation")
    }
    confirmation = [r for r in real_stages["confirmation"] if r["status"] == "measured"]
    real = {
        p: statistics.transform(
            np.array([r["values"] for r in confirmation if r["painter_id"] == p]), scaler
        )
        for p in PAINTER_IDS
    }
    references = [r for rows in real_stages.values() for r in rows if r["status"] == "measured"]
    comparisons, generation, all_groups = {}, {}, {}
    inputs = [p.relative_to(root) for p in output.glob("*_features.jsonl")]
    for experiment in frozen["experiment_ids"]:
        directory = output / "experiments" / experiment
        receipt_path = MANIFESTS / experiment / "generation_receipt.json"
        receipt = read_json(root / receipt_path)
        inputs.append(receipt_path)
        raw_outputs = read_jsonl(root / MANIFESTS / experiment / "outputs.jsonl")
        generation[experiment] = dict(receipt, service_diagnostics=service_diagnostics(raw_outputs))
        if not receipt["complete_generated_grid"]:
            continue
        rows = load_stage(directory, "generated")
        inputs.append((directory / "generated_features.jsonl").relative_to(root))
        if any(r["status"] != "measured" for r in rows):
            generation[experiment] = dict(receipt, analysis_status="feature_grid_incomplete")
            continue
        groups = generated_groups(rows, scaler)
        if set(groups) & set(all_groups):
            raise ValueError("duplicate service alias across prospective experiments")
        all_groups.update(groups)
        for alias, matrix in groups.items():
            selected = [r for r in rows if r.get("alias", "sd-turbo") == alias]
            comparisons[alias] = dict(
                finite_comparisons(real, matrix),
                experiment_id=experiment,
                copy_diagnostics=copy_diagnostics(references, selected),
            )
    frame = read_jsonl(root / MANIFESTS / frozen["frame_id"] / "frame.jsonl")
    acquisitions = read_jsonl(root / MANIFESTS / frozen["acquisition_id"] / "acquisitions.jsonl")
    inputs += [
        MANIFESTS / method_id / name
        for name in ("method_freeze.json", "scaler.json", "confirmation_opening.json")
    ]
    result = dict(
        method_id=method_id,
        comparisons=comparisons,
        generation=generation,
        metadata_diagnostics=metadata_diagnostics(frame, acquisitions, real_stages),
        stratified_distances=stratified_distances(frame, confirmation, all_groups, scaler),
        inputs=bindings(root, inputs),
        completed_at_utc=utc_now().isoformat(),
        reproduction_status="not_demonstrated_no_independent_capture_calibration",
        model_identity_note="OAuth conditions identify requested service aliases, "
        "not independently verified distinct model snapshots.",
    )
    publish(output / "empirical_analysis.json", result)
    return result
