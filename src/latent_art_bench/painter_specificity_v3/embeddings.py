"""CLIP and CSD embeddings for v3 images with the learned audit's pinned models and preprocessing.

``painter_learned_audit_v1`` (CLIP) and ``painter_learned_csd_v1`` (CSD) supply the loaders,
pixel reader and processors unchanged; this module only feeds them a new list of files and
repeats their device and batch validation.
"""

from __future__ import annotations

import hashlib
import platform
import time
from pathlib import Path

import numpy as np

from latent_art_bench import painter_learned_audit_v1 as base
from latent_art_bench import painter_learned_csd_v1 as csd
from latent_art_bench.io import hash_file, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import publish

TOLERANCE = 5e-5


def processor(name: str):
    return csd.CSDNativeProcessor() if name == "csd" else base.processor()


def embed(root: Path, rows: list[dict], name: str, device: str = "mps",
          batch_size: int = 4) -> tuple[np.ndarray, dict]:
    """Unit embeddings of full frames; rows carry a repository-relative path and its sha256."""
    import torch
    import transformers

    preprocess = processor(name)
    model, forward = csd.load_model(name)  # Delegates CLIP to the audit's original loader.
    torch.set_num_threads(4)

    def tensor(row: dict):
        image = base.load_rgb(root / row["path"], base.FULL)
        return preprocess(images=image, return_tensors="pt")["pixel_values"][0]

    sample = torch.stack([tensor(rows[i]) for i in range(min(3, len(rows)))])
    with torch.inference_mode():
        cpu = torch.nn.functional.normalize(forward(model, sample), dim=1).numpy()
    model.to(device)
    with torch.inference_mode():
        batched = torch.nn.functional.normalize(forward(model, sample.to(device)), dim=1)
        singles = torch.cat([torch.nn.functional.normalize(forward(model, x[None].to(device)),
                                                           dim=1) for x in sample])
    backend = float(np.abs(batched.cpu().numpy() - cpu).max())
    batching = float(np.abs(batched.cpu().numpy() - singles.cpu().numpy()).max())
    if backend > TOLERANCE or batching > TOLERANCE:
        raise ValueError(f"device/batch validation failed: {backend}, {batching}")
    vectors, hashes, started = [], [], time.monotonic()
    for begin in range(0, len(rows), batch_size):
        chunk = rows[begin: begin + batch_size]
        for row in chunk:
            if hash_file(root / row["path"]) != row["sha256"]:
                raise ValueError("pixels changed during extraction")
        batch = torch.stack([tensor(r) for r in chunk])
        hashes += [hashlib.sha256(x.numpy().astype("<f4").tobytes()).hexdigest() for x in batch]
        with torch.inference_mode():
            vectors.append(torch.nn.functional.normalize(
                forward(model, batch.to(device)), dim=1).cpu().numpy())
        if begin % 200 == 0:
            print(f"{name} {begin + len(chunk)}/{len(rows)} {time.monotonic() - started:.0f}s",
                  flush=True)
    values = np.concatenate(vectors).astype(np.float32)
    if values.shape != (len(rows), 768) or not np.isfinite(values).all():
        raise ValueError("incomplete or invalid vectors")
    if not np.allclose(np.linalg.norm(values, axis=1), 1, atol=1e-5):
        raise ValueError("nonunit vectors")
    record = dict(model=base.MODELS[name], tensor_sha256=hashes, shape=list(values.shape),
                  validation=dict(cpu_device_max_abs=backend, batched_single_max_abs=batching,
                                  tolerance=TOLERANCE),
                  environment=dict(python=platform.python_version(), torch=torch.__version__,
                                   transformers=transformers.__version__, numpy=np.__version__,
                                   device=device, batch_size=batch_size),
                  processor=preprocess.to_dict())
    return values, record


def extract_references(root: Path, run: str, name: str, device: str = "mps") -> dict:
    """Embeddings of every measured reference work of a v3 reference run, in feature order."""
    from latent_art_bench.painter_specificity_v3.references import MANIFESTS

    output = root / MANIFESTS / run
    target = output / f"embeddings_{name}.npz"
    if target.exists():
        raise FileExistsError("do not overwrite completed extraction")
    acquired = {r["work_id"]: r for r in read_jsonl(output / "acquisitions.jsonl")}
    measured = [r for r in read_jsonl(output / "features.jsonl") if r["status"] == "measured"]
    rows = [dict(work_id=r["work_id"], painter_id=r["painter_id"],
                 path=acquired[r["work_id"]]["raw_path"], sha256=r["raw_sha256"])
            for r in measured]
    started = utc_now().isoformat()
    values, record = embed(root, rows, name, device)
    with target.open("xb") as stream:
        np.savez_compressed(stream, embeddings=values)
    receipt = dict(record, started_utc=started, ended_utc=utc_now().isoformat(),
                   rows=[dict(work_id=r["work_id"], painter_id=r["painter_id"]) for r in rows],
                   features_sha256=hash_file(output / "features.jsonl"),
                   embeddings_sha256=hash_file(target),
                   implementation_sha256=hash_file(Path(__file__)))
    publish(output / f"extraction_{name}.json", receipt)
    return {k: v for k, v in receipt.items() if k not in ("tensor_sha256", "rows")}


def extract_generated(root: Path, name: str, device: str = "mps") -> dict:
    """Embeddings of every delivered v3 image, in request order."""
    from latent_art_bench.painter_specificity_v3 import study as s

    target = s.DATA / f"embeddings_{name}.npz"
    if target.exists():
        raise FileExistsError("do not overwrite completed extraction")
    receipt = s.read(s.DATA / "collection.json")
    rows = [dict(id=o["id"], path=o["image_path"], sha256=o["image_sha256"])
            for o in receipt["outcomes"] if o["success"]]
    started = utc_now().isoformat()
    values, record = embed(root, rows, name, device)
    with target.open("xb") as stream:
        np.savez_compressed(stream, embeddings=values)
    out = dict(record, started_utc=started, ended_utc=utc_now().isoformat(),
               rows=[dict(id=r["id"]) for r in rows],
               collection_sha256=hash_file(s.DATA / "collection.json"),
               embeddings_sha256=hash_file(target),
               implementation_sha256=hash_file(Path(__file__)))
    publish(s.DATA / f"extraction_{name}.json", out)
    return {k: v for k, v in out.items() if k not in ("tensor_sha256", "rows")}
