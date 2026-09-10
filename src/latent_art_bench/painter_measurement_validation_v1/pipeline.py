"""Committed metadata-only preparation, one-shot pixel run and numeric replay."""

from __future__ import annotations

import base64
import hashlib
import json
import platform
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import PIL
import pywt
import scipy
import skimage

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_distribution_revision_v1 import common
from latent_art_bench.painter_distribution_study_v1.collection import read_response
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    events,
    identifier,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import statistics, transforms

NAMESPACE = "painter_measurement_validation_v1"
RUN_ID = "pmvv1-20260910"
PROTOCOL = Path("studies") / NAMESPACE / "PROTOCOL.md"


def locations(run_id):
    identifier(run_id)
    return (Path("data/manifests") / NAMESPACE / run_id,
            Path("research_workspace") / NAMESPACE / run_id,
            Path("reports") / NAMESPACE / run_id)


def config():
    return dict(
        conditions=list(transforms.CONDITIONS), normalized_short_side=512,
        square_size=512, reference_works=70, generated_images=1006,
        challenge_vectors=700, total_vectors=1706, tile_seed=transforms.TILE_SEED,
        bootstrap_seed=statistics.BOOTSTRAP_SEED, bootstrap_draws=statistics.BOOTSTRAP_DRAWS,
        interval_level=statistics.INTERVAL_LEVEL, new_collection_authorized=False,
        no_human_ratings=True, primary_comparisons=statistics.SIGNALS,
    )


def environment():
    return dict(python=platform.python_version(), numpy=np.__version__,
                pillow=PIL.__version__, scipy=scipy.__version__,
                scikit_image=skimage.__version__, pywavelets=pywt.__version__)


def source_paths(root):
    packages = (NAMESPACE, "painter_distribution_revision_v1", "painter_distribution_study_v1",
                "painter_distribution_exploration_v1", "painter_feature_generation_v2",
                "painter_prompt_study_v1")
    paths = {p.relative_to(root) for package in packages
             for p in root.glob(f"src/latent_art_bench/{package}/*.py")}
    paths |= {p.relative_to(root) for p in root.glob(f"tests/{NAMESPACE}/*.py")}
    paths |= set(common.INPUT_PATHS) | {
        PROTOCOL, Path("src/latent_art_bench/io.py"), Path("pyproject.toml"), Path("uv.lock"),
        Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
    }
    return sorted(paths)


def clean_commit(root, paths):
    commit = committed(root, paths)
    for arguments in ([], ["--cached"]):
        result = subprocess.run(["git", "diff", "--quiet", *arguments, "--",
                                 *[p.as_posix() for p in paths]], cwd=root, check=False)
        if result.returncode:
            raise ValueError("prospective inputs must be clean in index and working tree")
    return commit


def image_inventory(root, bundle):
    """Read compact metadata only; no stat/hash/open on any image or response file."""
    panel = {r["work_id"]: r for r in read_jsonl(root / common.MAIN / "reference_panel.jsonl")}
    result = []
    for stage in ("reference", "generated"):
        rows = [r for r in bundle[stage] if r["pipeline"] == "primary512"]
        for row in sorted(rows, key=lambda r: r["image_id"]):
            item = dict(
                image_id=row["image_id"], painter_id=row["painter_id"], stage=stage,
                raw_sha256=row["raw_sha256"],
                normalized_sha256=row["normalization"]["normalized_sha256"],
                primary_feature_sha256=row["feature_sha256"],
            )
            if stage == "reference":
                source = panel[row["image_id"]]
                if row["raw_sha256"] != source["response_sha256"]:
                    raise ValueError("reference metadata identity disagrees")
                item["source"] = {k: source[k] for k in ("response_path", "response_sha256")}
            else:
                terminal = bundle["terminals"][row["selected_request_id"]]
                item.update(request_id=row["request_id"],
                            selected_request_id=row["selected_request_id"])
                item["source"] = {k: terminal[k] for k in
                                  ("response_path", "response_sha256", "retained_sha256")}
            result.append(item)
    if len(result) != 1076 or len({r["image_id"] for r in result}) != 1076:
        raise ValueError("expected70distinct references and1006generated images")
    if sum(r["stage"] == "reference" for r in result) != 70:
        raise ValueError("reference inventory changed")
    for item in result:
        path = Path(item["source"]["response_path"])
        if path.is_absolute() or ".." in path.parts or path.parts[0] != "research_workspace":
            raise ValueError("raw source must have a portable research_workspace path")
    return result


def prepare(root, run_id=RUN_ID):
    directory, workspace, _ = locations(run_id)
    if (root / directory).exists() or (root / workspace / "started.json").exists():
        raise ValueError("run namespace already exists; choose a disjoint successor")
    paths = source_paths(root)
    commit = clean_commit(root, paths)
    bundle = common.load(root)
    statistics.verify_primary(bundle)
    inventory = image_inventory(root, bundle)
    # No raw image/response hashing here: hashes are copied from the bound terminal evidence.
    publish(root / directory / "images.jsonl", inventory, lines=True)
    freeze = dict(
        schema_version="painter-measurement-validation/1.0", run_id=run_id,
        recorded_git_commit=commit, prepared_at_utc=utc_now().isoformat(), config=config(),
        inputs=bindings(root, paths),
        images_sha256=hash_file(root / directory / "images.jsonl"),
        expected_raw_hashes_basis="bound retained metadata, not pixel reads during prepare",
        original_primary_inference_exact=True,
        environment=environment(),
    )
    publish(root / directory / "freeze.json", freeze)
    return dict(status="prepared_no_pixels_read", run_id=run_id, images=len(inventory),
                next_step="Commit freeze.json and images.jsonl before run.")


def verify(root, run_id=RUN_ID):
    directory, _, _ = locations(run_id)
    freeze = read_json(root / directory / "freeze.json")
    if freeze["run_id"] != run_id or freeze["config"] != config():
        raise ValueError("run identity or frozen configuration differs")
    if freeze["environment"] != environment():
        raise ValueError("active extraction environment differs from prospective freeze")
    clean_commit(root, [directory / "freeze.json", directory / "images.jsonl"])
    verify_bindings(root, freeze["inputs"])
    clean_commit(root, [Path(r["path"]) for r in freeze["inputs"]])
    if hash_file(root / directory / "images.jsonl") != freeze["images_sha256"]:
        raise ValueError("frozen image manifest changed")
    return freeze


def normalized_item(root, workspace, item):
    """Called only after committed-freeze verification and the persistent run marker."""
    source = item["source"]
    if item["stage"] == "reference":
        path = root / source["response_path"]
        if hash_file(path) != item["raw_sha256"]:
            raise ValueError("reference raw bytes changed")
        return features.normalize(path, 512)
    body = read_response(root, source)
    payload = json.loads(body)
    if not isinstance(payload.get("data"), list) or len(payload["data"]) != 1:
        raise ValueError("expected the single retained generated image")
    raw = base64.b64decode(payload["data"][0]["b64_json"], validate=True)
    if hashlib.sha256(raw).hexdigest() != item["raw_sha256"]:
        raise ValueError("selected generated image bytes changed")
    temporary = root / workspace / "decode_tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="image-", dir=temporary) as d:
        path = Path(d) / "generated.bin"
        path.write_bytes(raw)
        return features.normalize(path, 512)


def measure_item(root, workspace, item):
    normalized = normalized_item(root, workspace, item)
    if normalized.metadata["normalized_sha256"] != item["normalized_sha256"]:
        raise ValueError("unchanged full-view normalization does not reproduce")
    baseline, window = transforms.square_window(normalized.rgb)
    names = transforms.CONDITIONS if item["stage"] == "reference" else ("baseline",)
    rows, baseline_vector = [], None
    for name in names:
        rgb, metadata = transforms.condition(baseline, name)
        if name == "png" and not np.array_equal(rgb, baseline):
            raise ValueError("lossless PNG pixel identity failed")
        values = features.extract(rgb)
        if name == "baseline":
            baseline_vector = values
        if name == "png" and not np.array_equal(values, baseline_vector):
            raise ValueError("lossless PNG feature identity failed")
        rows.append(dict(
            image_id=item["image_id"], painter_id=item["painter_id"], stage=item["stage"],
            condition=name, raw_sha256=item["raw_sha256"], window=window,
            transform=metadata, values=values.tolist(),
        ))
    return rows


def compute(rows, bundle):
    reference = [r for r in rows if r["stage"] == "reference"]
    square = [r for r in rows if r["condition"] == "baseline"]
    if len(rows) != 1706 or len(reference) != 700 or len(square) != 1076:
        raise ValueError("complete1706-vector experiment required")
    if len({(r["image_id"], r["condition"]) for r in rows}) != len(rows):
        raise ValueError("duplicate measured identity")
    return dict(
        counts=dict(reference_works=70, generated_images=1006, challenge_conditions=10,
                    challenge_vectors=700, total_vectors=1706, new_generation_calls=0),
        primary_replay_exact=(statistics.verify_primary(bundle) ==
                              bundle["old_analysis"]["endpoints"]),
        challenge=statistics.summarize_challenge(
            reference, bundle["scalers"]["primary512"]["scaler"]),
        geometry=statistics.geometry_analysis(square, bundle),
        scope="New computational measurements on exposed retained images; no independent "
        "captures, human ratings, new reference sample or perceptual-equivalence conclusion.",
    )


def run(root, run_id=RUN_ID):
    directory, workspace, _ = locations(run_id)
    with stage_lock(root / workspace / ".writer.lock"):
        freeze = verify(root, run_id)
        bundle = common.load(root)
        inventory = read_jsonl(root / directory / "images.jsonl")
        if inventory != image_inventory(root, bundle):
            raise ValueError("image inventory differs from bound compact evidence")
        statistics.verify_primary(bundle)
        # Create once: a failed/interrupted run remains closed and cannot silently resume.
        publish(root / workspace / "started.json", dict(
            run_id=run_id, at_utc=utc_now().isoformat(),
            freeze_sha256=hash_file(root / directory / "freeze.json"),
        ))
        ledger = root / directory / "features.jsonl"
        if ledger.exists() or (root / directory / "run_receipt.json").exists():
            raise ValueError("measurement output already exists")
        try:
            for index, item in enumerate(inventory):
                for row in measure_item(root, workspace, item):
                    append_event(ledger, row)
                if (index + 1) % 25 == 0:
                    progress = dict(processed_images=index + 1, total_images=1076)
                    print(json.dumps(progress), flush=True)
            analysis = compute(events(ledger), bundle)
            publish(root / directory / "analysis.json", analysis)
        except BaseException as exc:
            publish(root / workspace / "failure.json", dict(
                error_type=type(exc).__name__, at_utc=utc_now().isoformat(),
                terminal=True, completed_feature_rows=len(events(ledger)),
            ))
            raise
        receipt = dict(
            status="complete", run_id=run_id, source_commit=freeze["recorded_git_commit"],
            freeze_sha256=hash_file(root / directory / "freeze.json"),
            outputs=bindings(root, [directory / "features.jsonl", directory / "analysis.json"]),
            raw_images_verified=1076, feature_vectors=1706, new_generation_calls=0,
        )
        publish(root / directory / "run_receipt.json", receipt)
        return receipt


def check(root, run_id=RUN_ID):
    """Compact numeric replay, not an implicit second pixel run."""
    directory, _, _ = locations(run_id)
    verify(root, run_id)
    receipt = read_json(root / directory / "run_receipt.json")
    if receipt["freeze_sha256"] != hash_file(root / directory / "freeze.json"):
        raise ValueError("run receipt freeze mismatch")
    verify_bindings(root, receipt["outputs"])
    value = compute(events(root / directory / "features.jsonl"), common.load(root))
    if value != read_json(root / directory / "analysis.json"):
        raise ValueError("numeric analysis replay differs")
    return dict(status="verified", numeric_replay=True, raw_pixels_reread=False, run_id=run_id)
