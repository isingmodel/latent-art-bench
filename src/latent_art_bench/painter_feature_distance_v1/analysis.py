"""Read sealed numeric evidence and compute distance tables without accessing images."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, features, statistics
from latent_art_bench.painter_feature_generation_v2.artifacts import MANIFESTS, digest, identifier

DEFAULT_METHOD = "pfg2-method-20260905"
SCHEMA = "painter-feature-distance/1.0"
CONDITIONS = (*PAINTER_IDS, "artist_free")


class Sources:
    """Hash the exact bytes parsed, with portable paths and optional prior bindings."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.hashes: dict[str, str] = {}

    def read(self, relative: Path | str, expected: str | None = None, *, lines=False):
        path = (self.root / relative).resolve()
        key = path.relative_to(self.root).as_posix()
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if expected is not None and actual != expected:
            raise ValueError(f"source hash mismatch: {key}")
        if key in self.hashes and self.hashes[key] != actual:
            raise ValueError(f"source changed while reading: {key}")
        self.hashes[key] = actual
        if lines:
            return [json.loads(line) for line in data.splitlines() if line.strip()]
        return json.loads(data)

    def bound(self, relative: Path | str, bindings: dict, *, lines=False):
        key = Path(relative).as_posix()
        if key not in bindings:
            raise ValueError(f"missing source binding: {key}")
        return self.read(relative, bindings[key], lines=lines)

    def records(self):
        return [{"path": path, "sha256": sha} for path, sha in sorted(self.hashes.items())]


def binding_map(records: list[dict]) -> dict[str, str]:
    result = {row["path"]: row["sha256"] for row in records}
    if len(result) != len(records):
        raise ValueError("duplicate source binding")
    return result


def read_stage(sources, directory, stage, frozen_hash, inputs, receipt=None):
    receipt = receipt or sources.read(directory / f"{stage}_receipt.json")
    if receipt["stage"] != stage or receipt["method_freeze_sha256"] != frozen_hash:
        raise ValueError("measurement receipt identifies a different stage or method")
    rows = sources.bound(directory / f"{stage}_features.jsonl", inputs, lines=True)
    file_hash = sources.hashes[(directory / f"{stage}_features.jsonl").as_posix()]
    if (
        file_hash != receipt["feature_file_sha256"]
        or len(rows) != receipt["terminal_records"]
        or len(rows) != receipt["expected_records"]
        or len({r["image_id"] for r in rows}) != len(rows)
        or dict(Counter(r["status"] for r in rows)) != receipt["statuses"]
    ):
        raise ValueError("measurement stage accounting mismatch")
    for row in rows:
        if row["stage"] != stage or row["status"] not in {"measured", "failed"}:
            raise ValueError("invalid measurement stage or status")
        if row["status"] == "measured":
            values = np.asarray(row["values"], dtype=float)
            if values.shape != (31,) or not np.isfinite(values).all():
                raise ValueError("expected 31 finite measured coordinates")
            if digest(row["values"]) != row["feature_sha256"]:
                raise ValueError("feature vector hash mismatch")
            if row["normalization"]["short_side"] != 512:
                raise ValueError("expected the sealed 512-pixel measurement")
    return rows


def load_source(root: Path, method_id: str):
    """Validate direct report/measurement bindings; the full evidence audit remains separate."""
    identifier(method_id)
    sources = Sources(root)
    directory = MANIFESTS / method_id
    receipt = sources.read(directory / "report_receipt.json")
    if receipt["method_id"] != method_id:
        raise ValueError("report identifies a different method")
    report_inputs = binding_map(receipt["inputs"])
    frozen = sources.bound(directory / "method_freeze.json", report_inputs)
    frozen_hash = sources.hashes[(directory / "method_freeze.json").as_posix()]
    if (
        frozen["method_id"] != method_id
        or frozen["feature_names"] != list(features.NAMES)
        or frozen["short_side"] != 512
    ):
        raise ValueError("unsupported source feature contract")
    original = sources.bound(directory / "empirical_analysis.json", report_inputs)
    if original["method_id"] != method_id:
        raise ValueError("empirical result identifies a different method")
    inputs = binding_map(original["inputs"])
    scaler = sources.bound(directory / "scaler.json", inputs)
    development = sources.bound(directory / "development_receipt.json", report_inputs)
    if (
        development["method_freeze_sha256"] != frozen_hash
        or scaler["method_freeze_sha256"] != frozen_hash
        or development["feature_file_sha256"] != scaler["development_feature_sha256"]
        or development["scaler_sha256"] != sources.hashes[(directory / "scaler.json").as_posix()]
        or np.shape(scaler["center"]) != (31,)
        or np.shape(scaler["scale"]) != (31,)
        or any(scaler["invalid_coordinates"].values())
    ):
        raise ValueError("scaler is not bound to the sealed development stage")
    confirmation_receipt = sources.bound(directory / "confirmation_receipt.json", report_inputs)
    confirmation = read_stage(
        sources, directory, "confirmation", frozen_hash, inputs, confirmation_receipt
    )
    if any(r["role"] != "confirmation" or r["painter_id"] not in PAINTER_IDS
           for r in confirmation):
        raise ValueError("invalid confirmation role or painter")
    real = {
        painter: statistics.transform(np.array([
            row["values"] for row in confirmation
            if row["status"] == "measured" and row["painter_id"] == painter
        ]), scaler)
        for painter in PAINTER_IDS
    }
    generated, by_service = {}, {}
    for experiment in frozen["experiment_ids"]:
        identifier(experiment)
        generation = sources.bound(MANIFESTS / experiment / "generation_receipt.json", inputs)
        if not generation["complete_generated_grid"]:
            raise ValueError("source generation grid is incomplete")
        experiment_path = directory / "experiments" / experiment
        stage_receipt = sources.read(experiment_path / "generated_receipt.json")
        if stage_receipt["experiment_id"] != experiment:
            raise ValueError("generated receipt identifies a different experiment")
        rows = read_stage(
            sources, experiment_path, "generated", frozen_hash, inputs, stage_receipt
        )
        groups = empirical.generated_groups(rows, scaler)
        if set(groups) & set(generated):
            raise ValueError("duplicate service alias across experiments")
        generated.update(groups)
        for alias in groups:
            by_service[alias] = [r for r in rows if r.get("alias", "sd-turbo") == alias]
    if set(generated) != set(original["comparisons"]):
        raise ValueError("service set differs from sealed comparison")
    return real, generated, by_service, scaler, original, {
        "report": receipt["files"][0]["path"],
        "report_sha256": receipt["files"][0]["sha256"],
        "inputs": sources.records(),
        "confirmation_statuses": confirmation_receipt["statuses"],
        "scaler_development_counts": scaler["development_counts"],
    }


def verify_comparisons(computed: dict, original: dict) -> None:
    """Fail if recomputation disagrees with any sealed endpoint or coordinate diagnostic."""
    for counts in ("real_counts", "generated_counts"):
        if computed[counts] != original[counts]:
            raise ValueError("recomputed population counts differ from sealed result")
    for group, keys, values in (
        ("endpoints", ("painter_id", "family", "endpoint", "comparison"), ("estimate",)),
        ("coordinate_diagnostics", ("painter_id", "family", "coordinate"),
         ("median_difference", "iqr_ratio")),
    ):
        old = {tuple(r[k] for k in keys): r for r in original[group]}
        new = {tuple(r[k] for k in keys): r for r in computed[group]}
        if set(old) != set(new) or len(old) != len(original[group]):
            raise ValueError("sealed comparison endpoint set changed")
        for key, row in new.items():
            for value in values:
                a, b = row[value], old[key][value]
                if (a is None or b is None):
                    equal = a is b
                else:
                    equal = bool(np.isclose(a, b, rtol=1e-10, atol=1e-10))
                if not equal:
                    raise ValueError(f"distance recomputation differs from sealed result: {key}")


def distance_tables(real: dict, generated: dict) -> tuple[list, list]:
    distances, contrasts = [], []
    for service in sorted(generated):
        for family, section in features.FAMILIES.items():
            matrix = {}
            for condition in CONDITIONS:
                for painter in PAINTER_IDS:
                    x, y = real[painter][:, section], generated[service][condition][:, section]
                    value = statistics.finite_energy(x, y)
                    matrix[condition, painter] = value
                    distances.append(dict(
                        service=service, condition=condition, painter_id=painter, family=family,
                        distance=value, reference_count=len(x), generated_count=len(y),
                    ))
            for painter in PAINTER_IDS:
                own, free = matrix[painter, painter], matrix["artist_free", painter]
                other = min((p for p in PAINTER_IDS if p != painter),
                            key=lambda p: matrix[painter, p])
                contrasts.append(dict(
                    service=service, painter_id=painter, family=family, target_distance=own,
                    artist_free_distance=free, control_difference=own - free,
                    nearest_other_painter=other, nearest_other_distance=matrix[painter, other],
                    specificity_margin=own - matrix[painter, other],
                ))
    return distances, contrasts


def block_tables(real, generated, rows, scaler):
    """Use every observed whole block, retaining all templates and paired conditions."""
    block_distances, summaries = [], []
    for service in sorted(rows):
        for block in sorted({r["block"] for r in rows[service]}):
            chosen = [r for r in rows[service] if r["block"] == block]
            groups = empirical.generated_groups(chosen, scaler)[service]
            for family, section in features.FAMILIES.items():
                for painter in PAINTER_IDS:
                    x = real[painter][:, section]
                    own = statistics.finite_energy(x, groups[painter][:, section])
                    free = statistics.finite_energy(x, groups["artist_free"][:, section])
                    block_distances.append(dict(
                        service=service, block=block, painter_id=painter, family=family,
                        distance=own, artist_free_distance=free, control_difference=own - free,
                        generated_count=len(groups[painter]),
                    ))
        for family, section in features.FAMILIES.items():
            for painter in PAINTER_IDS:
                chosen = [r for r in block_distances if r["service"] == service
                          and r["painter_id"] == painter and r["family"] == family]
                values = [r["distance"] for r in chosen]
                summaries.append(dict(
                    service=service, painter_id=painter, family=family, blocks=len(chosen),
                    images_per_condition=16, minimum=min(values), median=float(np.median(values)),
                    maximum=max(values), pooled_distance=statistics.finite_energy(
                        real[painter][:, section], generated[service][painter][:, section]),
                ))
    return block_distances, summaries


def analyze(root: Path, method_id: str = DEFAULT_METHOD) -> dict:
    real, generated, rows, scaler, original, source = load_source(root, method_id)
    coordinates = []
    for service in sorted(generated):
        comparison = empirical.finite_comparisons(real, generated[service])
        verify_comparisons(comparison, original["comparisons"][service])
        coordinates.extend(dict(service=service, **r) for r in comparison["coordinate_diagnostics"])
    distances, contrasts = distance_tables(real, generated)
    reference_distances = [
        dict(first_painter=p, second_painter=q, family=family,
             distance=statistics.finite_energy(real[p][:, section], real[q][:, section]))
        for family, section in features.FAMILIES.items() for p in PAINTER_IDS for q in PAINTER_IDS
    ]
    block_distances, block_summary = block_tables(real, generated, rows, scaler)
    return dict(
        schema_version=SCHEMA, method_id=method_id,
        analysis_kind="post_hoc_descriptive_analysis_of_exposed_numeric_evidence",
        estimator="finite_empirical_energy_V_statistic",
        confidence_intervals=None, painters=list(PAINTER_IDS), services=sorted(generated),
        feature_names=list(features.NAMES),
        families={k: list(v) for k, v in features.FAMILY_NAMES.items()},
        reference_counts={p: len(x) for p, x in real.items()},
        generated_counts={s: {c: len(x) for c, x in groups.items()}
                          for s, groups in generated.items()},
        distances=distances, contrasts=contrasts, coordinates=coordinates,
        reference_distances=reference_distances, block_distances=block_distances,
        block_summary=block_summary, source=source,
    )
