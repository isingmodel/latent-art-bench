"""Predictions recorded before collection: H and the faithful benchmark of each painter group.

The generic arm is September's (``psv2-20260911``): its 31 features in the four-painter scaler,
and its CLIP and CSD embeddings from the learned audit. The four Impressionists are included,
computed the same way, so that the new groups can be read against the paper's values.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import publish
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_v3.analysis import predictions
from latent_art_bench.painter_specificity_v3.panel import GROUPS, PAINTERS
from latent_art_bench.painter_specificity_v3.references import MANIFESTS

SCALER = Path("data/manifests/painter_feature_generation_v2/pfg2-method-20260905/scaler.json")


def reference_vectors(root: Path, run: str) -> dict[str, np.ndarray]:
    """Scaled full-view feature vectors of the measured references, by painter."""
    scaler = read_json(root / SCALER)
    rows = [r for r in read_jsonl(root / MANIFESTS / run / "features.jsonl")
            if r["status"] == "measured"]
    return {p.painter_id: transform(np.array([r["values"] for r in rows
                                              if r["painter_id"] == p.painter_id]), scaler)
            for p in PAINTERS}


def reference_embeddings(root: Path, run: str, name: str) -> dict[str, np.ndarray] | None:
    output = root / MANIFESTS / run
    if not (output / f"embeddings_{name}.npz").exists():
        return None
    receipt = read_json(output / f"extraction_{name}.json")
    if hash_file(output / f"embeddings_{name}.npz") != receipt["embeddings_sha256"]:
        raise ValueError("embedding archive changed")
    values = np.load(output / f"embeddings_{name}.npz")["embeddings"].astype(np.float64)
    painters = np.array([r["painter_id"] for r in receipt["rows"]])
    return {p.painter_id: values[painters == p.painter_id] for p in PAINTERS}


def group_means(vectors: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {g: np.array([vectors[p.painter_id].mean(axis=0) for p in PAINTERS if p.group == g])
            for g in GROUPS}


def run(root: Path, run_id: str) -> dict:
    from latent_art_bench import painter_learned_audit_v1 as learned
    from latent_art_bench.painter_specificity_measurement_v1.workflow import load

    output = root / MANIFESTS / run_id
    x, refs = load(square=False)
    impressionists = np.array([r.mean(axis=0) for r in refs])
    result = dict(
        generic_source="psv2-20260911 generic arm (September)",
        hand31=predictions(x[:, :, :, 1], dict(impressionists=impressionists,
                                                **group_means(reference_vectors(root, run_id)))),
        counts={p: len(v) for p, v in reference_vectors(root, run_id).items()},
    )
    for name in ("clip", "csd"):
        embedded = reference_embeddings(root, run_id, name)
        if embedded is None:
            continue
        xe, refs_e, _ = learned.arrays(name)
        old = np.array([r.mean(axis=0) for r in refs_e])
        result[name] = predictions(xe[:, :, :, 1], dict(impressionists=old,
                                                        **group_means(embedded)))
    result["inputs"] = {str(p): hash_file(root / p) for p in (
        MANIFESTS / run_id / "features.jsonl", SCALER,
        Path("data/manifests/painter_specificity_v2/psv2-20260911/measurements.jsonl"),
        Path("src/latent_art_bench/painter_specificity_v3/analysis.py"),
        Path("src/latent_art_bench/painter_specificity_v3/predict.py"))}
    publish(output / "predictions.json", result)
    return result
