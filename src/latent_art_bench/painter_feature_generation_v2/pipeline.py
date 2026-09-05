"""Stage receipts connecting raw evidence, qualified transforms, and paper results."""

from __future__ import annotations

import os
import subprocess
from collections import Counter
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
    append_event,
    bindings,
    digest,
    identifier,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.generate import CONFIG


def _committed(root: Path, paths: list[Path]) -> str:
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit the exact measurement input first: {path}")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def prepare(root: Path, method_id: str, frame_id: str, acquisition_id: str) -> dict:
    for value in (method_id, frame_id, acquisition_id):
        identifier(value)
    output = root / MANIFESTS / method_id
    if output.exists():
        raise FileExistsError(output)
    paths = [PROTOCOL, CONFIG, MANIFESTS / frame_id / "frame.jsonl",
             MANIFESTS / acquisition_id / "acquisitions.jsonl",
             MANIFESTS / acquisition_id / "acquisition_receipt.json", Path("uv.lock"),
             Path("pyproject.toml"), Path("src/latent_art_bench/io.py")]
    paths += [Path("src/latent_art_bench/painter_feature_generation_v2") / name
              for name in ("features.py", "statistics.py", "pipeline.py", "artifacts.py")]
    commit = _committed(root, paths)
    config = read_json(root / CONFIG)
    receipt = dict(method_id=method_id, frame_id=frame_id, acquisition_id=acquisition_id,
                   short_side=config["analysis_short_side"], feature_names=list(features.NAMES),
                   inputs=bindings(root, paths), recorded_git_commit=commit,
                   prepared_at_utc=utc_now().isoformat(),
                   reviewer_kind="operator_self_check_not_independent_review")
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


def measure(root: Path, method_id: str, stage: str, experiment_id: str | None = None) -> dict:
    identifier(method_id)
    if stage not in {"development", "qualification", "confirmation", "generated"}:
        raise ValueError("unknown measurement stage")
    output = root / MANIFESTS / method_id
    frozen = read_json(output / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    terminal = output / f"{stage}_receipt.json"
    if terminal.exists():
        raise FileExistsError(f"measurement stage {stage} is terminal")
    if stage != "development" and not (output / "scaler.json").exists():
        raise ValueError("development scaling must be frozen first")
    if stage in {"confirmation", "generated"}:
        if experiment_id is None:
            raise ValueError("a terminal generation experiment is required")
        identifier(experiment_id)
        generation_dir = MANIFESTS / experiment_id
        generation_receipt = read_json(root / generation_dir / "generation_receipt.json")
        if not generation_receipt["complete_generated_grid"]:
            raise ValueError("incomplete generated grid: only availability reporting is authorized")
        if not (output / "qualification_receipt.json").exists():
            raise ValueError("qualification must be recorded before confirmation")
        opening = output / "confirmation_opening.json"
        if not opening.exists():
            paths = [MANIFESTS / method_id / "scaler.json",
                     MANIFESTS / method_id / "qualification_receipt.json",
                     generation_dir / "generation_receipt.json", generation_dir / "outputs.jsonl",
                     generation_dir / "generation_freeze.json"]
            commit = _committed(root, paths)
            publish(opening, dict(opened_at_utc=utc_now().isoformat(),
                                  experiment_id=experiment_id, recorded_git_commit=commit,
                                  inputs=bindings(root, paths)))
        else:
            record = read_json(opening)
            if record["experiment_id"] != experiment_id:
                raise ValueError("confirmation was assigned to a different experiment")
            verify_bindings(root, record["inputs"])
    if stage == "generated":
        population = [dict(row, image_id=row["request_id"], raw_path=row["image_path"],
                           raw_sha256=row["sha256"])
                      for row in read_jsonl(root / MANIFESTS / experiment_id / "outputs.jsonl")]
    else:
        frame = {r["work_id"]: r for r in read_jsonl(
            root / MANIFESTS / frozen["frame_id"] / "frame.jsonl")}
        roles = {stage, "historical_development"} if stage == "development" else {stage}
        population = [dict(row, **{"frame": frame[row["work_id"]], "image_id": row["work_id"]})
                      for row in read_jsonl(root / MANIFESTS / frozen["acquisition_id"]
                                           / "acquisitions.jsonl")
                      if row["status"] == "acquired" and row["role"] in roles]
    rows_path, ledger = output / f"{stage}_features.jsonl", output / "access_events.jsonl"
    done = {r["image_id"]: r for r in read_jsonl(rows_path)} if rows_path.exists() else {}
    for index, item in enumerate(population):
        if item["image_id"] in done:
            continue
        path = (root / item["raw_path"]).resolve()
        path.relative_to((root / "research_workspace/painter_feature_generation_v2").resolve())
        if hash_file(path) != item["raw_sha256"]:
            raise ValueError("raw image changed since acquisition/generation")
        append_event(ledger, dict(kind="feature_read", stage=stage, image_id=item["image_id"],
                                 raw_sha256=item["raw_sha256"]))
        result = dict(image_id=item["image_id"], raw_sha256=item["raw_sha256"], stage=stage)
        for key in ("painter_id", "role", "condition", "template_id", "block"):
            if key in item:
                result[key] = item[key]
        try:
            normalized = features.normalize(path, frozen["short_side"])
            values = features.extract(normalized.rgb)
            result.update(status="measured", values=values.tolist(),
                          feature_sha256=digest(values.tolist()), phash=phash(normalized.rgb),
                          normalization=normalized.metadata)
        except (ValueError, OSError) as exc:
            result.update(status="failed", error=str(exc))
        _append_row(rows_path, result)
        done[item["image_id"]] = result
        if (index + 1) % 20 == 0 or index + 1 == len(population):
            print(f"{stage} features {index + 1}/{len(population)} "
                  f"{dict(Counter(r['status'] for r in done.values()))}", flush=True)
    rows = list(done.values())
    receipt = dict(stage=stage, expected_records=len(population), terminal_records=len(rows),
                   statuses=dict(Counter(r["status"] for r in rows)),
                   feature_file_sha256=hash_file(rows_path),
                   method_freeze_sha256=hash_file(output / "method_freeze.json"),
                   completed_at_utc=utc_now().isoformat())
    if stage == "development":
        new = {p: np.array([r["values"] for r in rows if r.get("painter_id") == p
                            and r.get("role") == "development" and r["status"] == "measured"])
               for p in PAINTER_IDS}
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
    if (output / "analysis.json").exists():
        raise FileExistsError("analysis is already recorded")
    opening = read_json(output / "confirmation_opening.json")
    verify_bindings(root, opening["inputs"])
    if opening["experiment_id"] != experiment_id:
        raise ValueError("wrong experiment for this confirmation opening")
    scaler = read_json(output / "scaler.json")
    datasets = {}
    for stage in ("development", "qualification", "confirmation", "generated"):
        receipt = read_json(output / f"{stage}_receipt.json")
        file = output / f"{stage}_features.jsonl"
        if hash_file(file) != receipt["feature_file_sha256"]:
            raise ValueError("measured evidence changed")
        datasets[stage] = [r for r in read_jsonl(file) if r["status"] == "measured"]
        if stage == "generated" and len(datasets[stage]) != receipt["expected_records"]:
            raise ValueError("generated feature grid is incomplete")
    real = {p: statistics.transform(np.array([r["values"] for r in datasets["confirmation"]
                                              if r["painter_id"] == p]), scaler)
            for p in PAINTER_IDS}
    generated = {}
    for condition in (*PAINTER_IDS, "artist_free"):
        rows = sorted((r for r in datasets["generated"] if r["condition"] == condition),
                      key=lambda r: (r["block"], r["template_id"]))
        keys = {(r["block"], r["template_id"]) for r in rows}
        if len(keys) != len(rows):
            raise ValueError("duplicate generated grid cell")
        values = statistics.transform(np.array([r["values"] for r in rows]), scaler)
        generated[condition] = values.reshape(-1, 16, 31)
    result = statistics.analyze(real, generated)
    qualification = []
    for painter in PAINTER_IDS:
        dev = statistics.transform(np.array([r["values"] for r in datasets["development"]
                                             if r["painter_id"] == painter
                                             and r["role"] == "development"]), scaler)
        qual = statistics.transform(np.array([r["values"] for r in datasets["qualification"]
                                              if r["painter_id"] == painter]), scaler)
        for family, section in features.FAMILIES.items():
            qualification.append(dict(painter_id=painter, family=family,
                                      finite_energy=statistics.finite_energy(dev[:, section],
                                                                            qual[:, section])))
    result["qualification_diagnostics"] = qualification
    references = datasets["development"] + datasets["qualification"] + datasets["confirmation"]
    reference_hashes = {r["raw_sha256"] for r in references}
    reference_phashes = [int(r["phash"], 16) for r in references]
    candidates = []
    for row in datasets["generated"]:
        distance, nearest = min((bin(int(row["phash"], 16) ^ value).count("1"), i)
                                for i, value in enumerate(reference_phashes))
        if distance <= 8 or row["raw_sha256"] in reference_hashes:
            candidates.append(dict(request_id=row["image_id"],
                                   reference_id=references[nearest]["image_id"],
                                   phash_hamming_distance=distance,
                                   exact_file_match=row["raw_sha256"] in reference_hashes))
    result["copy_diagnostic"] = dict(
        searched_real_records=len(references), phash_candidate_threshold=8,
        candidates=candidates, limitation="63-bit perceptual hash screening is uncalibrated; "
        "neither a confirmed-copy detector nor evidence of training-data nonoverlap.")
    result["generated_exact_duplicate_excess"] = len(datasets["generated"]) - len({
        r["raw_sha256"] for r in datasets["generated"]})
    result["inputs"] = bindings(root, [p.relative_to(root) for p in output.glob("*_features.jsonl")]
                                + [MANIFESTS / method_id / "scaler.json",
                                   MANIFESTS / method_id / "confirmation_opening.json"])
    publish(output / "analysis.json", result)
    return result
