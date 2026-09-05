"""Stage receipts connecting raw evidence, qualified transforms, and analysis results."""

from __future__ import annotations

import os
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fft import dctn

from latent_art_bench.io import canonical_json, hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features, statistics
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    PROTOCOL,
    WORKSPACE,
    append_event,
    bindings,
    digest,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.generate import CONFIG


def _committed(root: Path, paths: list[Path]) -> str:
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit the exact measurement input first: {path}")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def prepare(
    root: Path,
    method_id: str,
    frame_id: str,
    acquisition_id: str,
    experiment_ids: list[str],
    calibration_id: str,
) -> dict:
    for value in (method_id, frame_id, acquisition_id):
        identifier(value)
    output = root / MANIFESTS / method_id
    if output.exists():
        raise FileExistsError(output)
    if len(set(experiment_ids)) != len(experiment_ids) or not experiment_ids:
        raise ValueError("unique prospective experiment IDs required")
    for value in [*experiment_ids, calibration_id]:
        identifier(value)
    paths = [
        PROTOCOL,
        CONFIG,
        MANIFESTS / frame_id / "frame.jsonl",
        MANIFESTS / acquisition_id / "acquisitions.jsonl",
        MANIFESTS / acquisition_id / "acquisition_receipt.json",
        Path("uv.lock"),
        Path("pyproject.toml"),
        Path("src/latent_art_bench/io.py"),
    ]
    paths += [
        Path("studies/painter_feature_generation_v2") / f"PROTOCOL_1.{i}.md" for i in (1, 2, 3)
    ]
    paths += [
        Path("src/latent_art_bench/painter_feature_generation_v2") / name
        for name in (
            "features.py",
            "statistics.py",
            "pipeline.py",
            "artifacts.py",
            "empirical.py",
            "robustness.py",
            "calibration.py",
        )
    ]
    paths += [MANIFESTS / e / "generation_freeze.json" for e in experiment_ids]
    paths += [
        MANIFESTS / calibration_id / name
        for name in ("calibration.json", "calibration_freeze.json")
    ]
    paths += [
        Path("tests/painter_feature_generation_v2") / name
        for name in ("test_methods.py", "test_empirical.py", "test_pipeline.py")
    ]
    commit = _committed(root, paths)
    config = read_json(root / CONFIG)
    frame = {r["work_id"]: r for r in read_jsonl(root / MANIFESTS / frame_id / "frame.jsonl")}
    acquired = read_jsonl(root / MANIFESTS / acquisition_id / "acquisitions.jsonl")
    acquisition_receipt = read_json(root / MANIFESTS / acquisition_id / "acquisition_receipt.json")
    if (
        hash_file(root / MANIFESTS / acquisition_id / "acquisitions.jsonl")
        != acquisition_receipt["acquisitions_sha256"]
    ):
        raise ValueError("acquisition receipt does not attest to these records")
    if len(acquired) != len(frame) or {r["work_id"] for r in acquired} != set(frame):
        raise ValueError("acquisition does not account for the complete fixed frame")
    for row in acquired:
        if any(row[k] != frame[row["work_id"]][k] for k in ("role", "painter_id")):
            raise ValueError("acquisition changed frozen painter or role")
    receipt = dict(
        method_id=method_id,
        frame_id=frame_id,
        acquisition_id=acquisition_id,
        experiment_ids=experiment_ids,
        calibration_id=calibration_id,
        short_side=config["analysis_short_side"],
        feature_names=list(features.NAMES),
        feature_workers=3,
        inputs=bindings(root, paths),
        recorded_git_commit=commit,
        prepared_at_utc=utc_now().isoformat(),
        reviewer_kind="operator_self_check_not_independent_review",
    )
    publish(output / "method_freeze.json", receipt)
    return receipt


def phash(rgb: np.ndarray) -> str:
    image = Image.fromarray(np.floor(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
    gray = np.asarray(image.convert("L").resize((32, 32), Image.Resampling.LANCZOS), dtype=float)
    low = dctn(gray, norm="ortho")[:8, :8].ravel()[1:]
    bits = np.packbits(low > np.median(low))
    return bits.tobytes().hex()


def _append_row(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def measure_one(item: dict, short_side: int, crop_fraction: float = 0.0) -> dict:
    result = {
        k: item[k]
        for k in (
            "image_id",
            "raw_sha256",
            "stage",
            "painter_id",
            "role",
            "condition",
            "template_id",
            "block",
            "alias",
            "experiment_id",
            "source_image_id",
            "domain",
        )
        if k in item
    }
    try:
        normalized = features.normalize(Path(item["path"]), short_side, crop_fraction)
        values = features.extract(normalized.rgb)
        result.update(
            status="measured",
            values=values.tolist(),
            feature_sha256=digest(values.tolist()),
            phash=phash(normalized.rgb),
            normalization=normalized.metadata,
        )
    except (ValueError, OSError) as exc:
        result.update(status="failed", error=str(exc))
    return result


def measure(root: Path, method_id: str, stage: str, experiment_id: str | None = None) -> dict:
    identifier(method_id)
    with stage_lock(root / WORKSPACE / method_id / ".measurement.writer.lock"):
        return _measure(root, method_id, stage, experiment_id)


def open_confirmation(root: Path, method_id: str, frozen: dict) -> None:
    from .empirical import load_stage

    output = root / MANIFESTS / method_id
    opening = output / "confirmation_opening.json"
    if opening.exists():
        verify_bindings(root, read_json(opening)["inputs"])
        return
    paths = [
        MANIFESTS / method_id / name
        for name in (
            "method_freeze.json",
            "scaler.json",
            "development_receipt.json",
            "qualification_receipt.json",
            "development_features.jsonl",
            "qualification_features.jsonl",
        )
    ]
    any_complete = False
    for stage in ("development", "qualification"):
        load_stage(output, stage)
    if (
        hash_file(output / "scaler.json")
        != read_json(output / "development_receipt.json")["scaler_sha256"]
    ):
        raise ValueError("development scaler changed before confirmation")
    statistics.transform(np.zeros((1, 31)), read_json(output / "scaler.json"))
    for experiment in frozen["experiment_ids"]:
        directory = MANIFESTS / experiment
        receipt = read_json(root / directory / "generation_receipt.json")
        if receipt["expected_requests"] != receipt["terminal_requests"]:
            raise ValueError("every planned generation must have complete terminal accounting")
        if hash_file(root / directory / "outputs.jsonl") != receipt["outputs_sha256"]:
            raise ValueError("generation output evidence changed")
        any_complete |= receipt["complete_generated_grid"]
        paths += [
            directory / name
            for name in ("generation_freeze.json", "generation_receipt.json", "outputs.jsonl")
        ]
    if not any_complete:
        raise ValueError("no complete generated grid warrants opening confirmation")
    paths += [MANIFESTS / frozen["calibration_id"] / "calibration.json"]
    commit = _committed(root, paths)
    publish(
        opening,
        dict(
            opened_at_utc=utc_now().isoformat(),
            experiment_ids=frozen["experiment_ids"],
            recorded_git_commit=commit,
            inputs=bindings(root, paths),
        ),
    )


def _measure(root: Path, method_id: str, stage: str, experiment_id: str | None = None) -> dict:
    identifier(method_id)
    if stage not in {"development", "qualification", "confirmation", "generated"}:
        raise ValueError("unknown measurement stage")
    base = root / MANIFESTS / method_id
    frozen = read_json(base / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    output = base
    if stage == "generated":
        if experiment_id not in frozen["experiment_ids"]:
            raise ValueError("experiment was not bound before feature access")
        identifier(experiment_id)
        output = base / "experiments" / experiment_id
        output.mkdir(parents=True, exist_ok=True)
    terminal = output / f"{stage}_receipt.json"
    if terminal.exists():
        raise FileExistsError(f"measurement stage {stage} is terminal")
    if stage != "development" and not (base / "scaler.json").exists():
        raise ValueError("development scaling must be frozen first")
    if stage != "development":
        receipt = read_json(base / "development_receipt.json")
        if hash_file(base / "scaler.json") != receipt["scaler_sha256"]:
            raise ValueError("development scaler changed")
        statistics.transform(np.zeros((1, 31)), read_json(base / "scaler.json"))
    if stage in {"confirmation", "generated"}:
        if not (base / "qualification_receipt.json").exists():
            raise ValueError("qualification must be recorded before confirmation")
        if stage == "generated":
            generation_dir = MANIFESTS / experiment_id
            generation_receipt = read_json(root / generation_dir / "generation_receipt.json")
            if not generation_receipt["complete_generated_grid"]:
                raise ValueError("incomplete generated grid: availability reporting only")
        open_confirmation(root, method_id, frozen)
    if stage == "generated":
        population = [
            dict(
                row,
                image_id=row["request_id"],
                raw_path=row["image_path"],
                raw_sha256=row["sha256"],
            )
            for row in read_jsonl(root / MANIFESTS / experiment_id / "outputs.jsonl")
        ]
    else:
        frame = {
            r["work_id"]: r
            for r in read_jsonl(root / MANIFESTS / frozen["frame_id"] / "frame.jsonl")
        }
        roles = {stage, "historical_development"} if stage == "development" else {stage}
        population = [
            dict(row, **{"frame": frame[row["work_id"]], "image_id": row["work_id"]})
            for row in read_jsonl(
                root / MANIFESTS / frozen["acquisition_id"] / "acquisitions.jsonl"
            )
            if row["status"] == "acquired" and row["role"] in roles
        ]
    rows_path, ledger = output / f"{stage}_features.jsonl", base / "access_events.jsonl"
    prior = read_jsonl(rows_path) if rows_path.exists() else []
    done = {r["image_id"]: r for r in prior}
    if len(done) != len(prior):
        raise ValueError("duplicate prior measurement IDs")
    expected = {r["image_id"] for r in population}
    if len(expected) != len(population) or not set(done) <= expected:
        raise ValueError("measurement population or prior IDs changed")
    if not population:
        raise ValueError("no acquired images in this frozen role")

    def pending():
        for item in population:
            if item["image_id"] in done:
                if done[item["image_id"]]["raw_sha256"] != item["raw_sha256"]:
                    raise ValueError("prior measurement source hash changed")
                continue
            path = (root / item["raw_path"]).resolve()
            path.relative_to((root / WORKSPACE).resolve())
            append_event(
                ledger,
                dict(
                    kind="feature_read",
                    stage=stage,
                    image_id=item["image_id"],
                    experiment_id=experiment_id,
                    raw_sha256=item["raw_sha256"],
                ),
            )
            if hash_file(path) != item["raw_sha256"]:
                raise ValueError("raw image changed since acquisition/generation")
            yield dict(item, path=str(path), stage=stage)

    with ThreadPoolExecutor(max_workers=frozen["feature_workers"]) as pool:
        for result in pool.map(lambda item: measure_one(item, frozen["short_side"]), pending()):
            _append_row(rows_path, result)
            done[result["image_id"]] = result
            if len(done) % 20 == 0 or len(done) == len(population):
                print(
                    f"{stage} features {len(done)}/{len(population)} "
                    f"{dict(Counter(r['status'] for r in done.values()))}",
                    flush=True,
                )
    rows = [done[item["image_id"]] for item in population]
    receipt = dict(
        stage=stage,
        expected_records=len(population),
        terminal_records=len(rows),
        statuses=dict(Counter(r["status"] for r in rows)),
        feature_file_sha256=hash_file(rows_path),
        method_freeze_sha256=hash_file(base / "method_freeze.json"),
        experiment_id=experiment_id,
        completed_at_utc=utc_now().isoformat(),
    )
    if stage == "development":
        new = {
            p: np.array(
                [
                    r["values"]
                    for r in rows
                    if r.get("painter_id") == p
                    and r.get("role") == "development"
                    and r["status"] == "measured"
                ]
            )
            for p in PAINTER_IDS
        }
        scaler = statistics.fit_scaler(new)
        scaler["development_feature_sha256"] = receipt["feature_file_sha256"]
        scaler["method_freeze_sha256"] = receipt["method_freeze_sha256"]
        publish(output / "scaler.json", scaler)
        receipt["scaler_sha256"] = hash_file(output / "scaler.json")
    publish(terminal, receipt)
    return receipt


def analyze(root: Path, method_id: str, experiment_id: str) -> dict:
    identifier(method_id)
    identifier(experiment_id)
    output = root / MANIFESTS / method_id
    opening = read_json(output / "confirmation_opening.json")
    verify_bindings(root, opening["inputs"])
    frozen = read_json(output / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    if experiment_id not in opening["experiment_ids"]:
        raise ValueError("wrong experiment for this confirmation opening")
    result_dir = output / "experiments" / experiment_id
    if (result_dir / "analysis.json").exists():
        raise FileExistsError("analysis is already recorded")
    scaler = read_json(output / "scaler.json")
    datasets = {}
    for stage in ("development", "qualification", "confirmation", "generated"):
        stage_dir = result_dir if stage == "generated" else output
        receipt = read_json(stage_dir / f"{stage}_receipt.json")
        file = stage_dir / f"{stage}_features.jsonl"
        if hash_file(file) != receipt["feature_file_sha256"]:
            raise ValueError("measured evidence changed")
        datasets[stage] = [r for r in read_jsonl(file) if r["status"] == "measured"]
        if stage == "generated" and len(datasets[stage]) != receipt["expected_records"]:
            raise ValueError("generated feature grid is incomplete")
    real = {
        p: statistics.transform(
            np.array([r["values"] for r in datasets["confirmation"] if r["painter_id"] == p]),
            scaler,
        )
        for p in PAINTER_IDS
    }
    generated = {}
    for condition in (*PAINTER_IDS, "artist_free"):
        rows = sorted(
            (r for r in datasets["generated"] if r["condition"] == condition),
            key=lambda r: (r["block"], r["template_id"]),
        )
        keys = {(r["block"], r["template_id"]) for r in rows}
        if len(keys) != len(rows):
            raise ValueError("duplicate generated grid cell")
        values = statistics.transform(np.array([r["values"] for r in rows]), scaler)
        generated[condition] = values.reshape(-1, 16, 31)
    result = statistics.analyze(real, generated)
    qualification = []
    for painter in PAINTER_IDS:
        dev = statistics.transform(
            np.array(
                [
                    r["values"]
                    for r in datasets["development"]
                    if r["painter_id"] == painter and r["role"] == "development"
                ]
            ),
            scaler,
        )
        qual = statistics.transform(
            np.array(
                [r["values"] for r in datasets["qualification"] if r["painter_id"] == painter]
            ),
            scaler,
        )
        for family, section in features.FAMILIES.items():
            qualification.append(
                dict(
                    painter_id=painter,
                    family=family,
                    finite_energy=statistics.finite_energy(dev[:, section], qual[:, section]),
                )
            )
    result["qualification_diagnostics"] = qualification
    from .empirical import copy_diagnostics

    references = datasets["development"] + datasets["qualification"] + datasets["confirmation"]
    result["copy_diagnostic"] = copy_diagnostics(references, datasets["generated"])
    result["inputs"] = bindings(
        root,
        [p.relative_to(root) for p in output.glob("*_features.jsonl")]
        + [
            MANIFESTS / method_id / "scaler.json",
            MANIFESTS / method_id / "confirmation_opening.json",
            (result_dir / "generated_features.jsonl").relative_to(root),
        ],
    )
    publish(result_dir / "analysis.json", result)
    return result
