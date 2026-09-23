"""Retained-pixel CLIP/CSD audit; no acquisition or generation operations."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import io
import platform
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

from latent_art_bench.painter_reference_quality_v1 import AUDITS, audit_records
from latent_art_bench.painter_specificity_measurement_v1.workflow import verify
from latent_art_bench.painter_specificity_review_v1 import DEVELOPMENT
from latent_art_bench.painter_specificity_v2 import study as s

OUT = s.ROOT / "reports/painter_learned_audit_v1"
PLAN = s.ROOT / "studies/painter_learned_audit_v1/PLAN.md"
MODEL_ROOT = s.ROOT / "artifacts/models"
FULL = [0, 0, 1, 1]
MODELS = {
    "clip": {
        "directory": "clip-vit-large-patch14",
        "file": "model.safetensors",
        "sha256": "a2bf730a0c7debf160f7a6b50b3aaf3703e7e88ac73de7a314903141db026dcb",
        "repository": "openai/clip-vit-large-patch14",
        "revision": "32bd64288804d66eefd0ccbe215aa642df71cc41",
    },
    "csd": {
        "directory": "csd-vit-large",
        "file": "pytorch_model.bin",
        "sha256": "40e92fad63a361b8136100cd234c42d401ef9b34ff1748234318929ebcc7e7a1",
        "repository": "tomg-group-umd/CSD-ViT-L",
        "revision": "5bc26a6fb0487f3f00a2a7313135103a005b1b67",
    },
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def bindings(paths):
    return {str(p.relative_to(s.ROOT)): digest(p) for p in paths}


def freeze():
    verify()
    requests = {r["id"]: r for r in s.rows(s.DATA / "requests.jsonl")}
    outcomes = s.read(s.DATA / "collection.json")["outcomes"]
    rows = []
    for o in outcomes:
        r = requests[o["id"]]
        if not o["success"]:
            raise ValueError("incomplete generated cohort")
        rows.append(dict(id=o["id"], role="generated", view="original", box=FULL,
                         path=o["image_path"], sha256=o["image_sha256"],
                         model=r["model"], scene=r["scene"], repeat=r["repeat"], arm=r["arm"]))
    for a in audit_records():
        row = dict(id=a["image_id"], role=a["role"], painter=a["painter_id"],
                   path=a["raw_path"], sha256=a["raw_sha256"], view="original", box=FULL)
        rows.append(row)
        if a["region_box"] != FULL:
            rows.append(dict(row, view="audited_region", box=a["region_box"]))
    counts = Counter(r["role"] for r in rows if r["view"] == "original")
    if counts != {"generated": 1008, "reference": 649, "development": 221}:
        raise ValueError("cohort changed")
    if len(rows) != 2009 or len({(r["id"], r["view"]) for r in rows}) != len(rows):
        raise ValueError("expected all originals and 131 additional regions")
    seen = set()
    for i, r in enumerate(rows):
        if r["path"] not in seen:
            if digest(s.ROOT / r["path"]) != r["sha256"]:
                raise ValueError("pixel hash differs: " + r["id"])
            seen.add(r["path"])
        if i % 200 == 0:
            print(f"Verified inputs {i}/{len(rows)}", flush=True)
    source = MODEL_ROOT / "openai-clip-source/model.py"
    paths = [PLAN, Path(__file__), *AUDITS, s.REF, DEVELOPMENT, s.DATA / "collection.json",
             s.DATA / "requests.jsonl", source, source.with_name("LICENSE")]
    s.write_new(OUT / "inputs.json", dict(created_utc=now(), counts=dict(counts),
                region_count=131, models=MODELS, bindings=bindings(paths), rows=rows))


def load_rgb(path, box):
    """Orientation/ICC correction and region, with no intermediate resize."""
    with Image.open(path) as original:
        original.load()
        image = ImageOps.exif_transpose(original)
        if image.convert("RGBA").getchannel("A").getextrema() != (255, 255):
            raise ValueError("nonopaque image")
        profile = image.info.get("icc_profile")
        if profile:
            image = ImageCms.profileToProfile(
                image, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile("sRGB"), renderingIntent=ImageCms.Intent.PERCEPTUAL,
                outputMode="RGB")
        else:
            if image.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                raise ValueError("unprofiled non-RGB color space")
            image = image.convert("RGB")
        if box != FULL:
            width, height = image.size
            coords = [int(np.floor(v * n + .5))
                      for v, n in zip(box, (width, height, width, height))]
            image = image.crop(coords)
        return image.copy()


def processor():
    from transformers import CLIPImageProcessor
    return CLIPImageProcessor.from_pretrained(
        MODEL_ROOT / "clip-vit-large-patch14", local_files_only=True)


def tensor_for(row, preprocess):
    image = load_rgb(s.ROOT / row["path"], row["box"])
    return preprocess(images=image, return_tensors="pt")["pixel_values"][0]


def load_model(name):
    import torch
    from safetensors import safe_open
    from transformers import CLIPVisionConfig, CLIPVisionModelWithProjection

    info = MODELS[name]
    path = MODEL_ROOT / info["directory"] / info["file"]
    if digest(path) != info["sha256"]:
        raise ValueError("checkpoint hash differs")
    if name == "clip":
        config = s.read(path.with_name("config.json"))["vision_config"]
        model = CLIPVisionModelWithProjection(CLIPVisionConfig(**config))
        with safe_open(path, framework="pt", device="cpu") as f:
            state = {k: f.get_tensor(k) for k in f.keys()
                     if k.startswith(("vision_model.", "visual_projection."))}
        model.load_state_dict(state, strict=True)
        del state
        return model.eval(), lambda model, x: model(pixel_values=x).image_embeds
    source = MODEL_ROOT / "openai-clip-source/model.py"
    spec = importlib.util.spec_from_file_location("retained_openai_clip", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.VisionTransformer(224, 14, 1024, 24, 16, 768)
    raw = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
    if "state_dict" in raw:
        raw = raw["state_dict"]
    state = {k.removeprefix("module."): v for k, v in raw.items()}
    backbone = {k.removeprefix("backbone."): v for k, v in state.items()
                if k.startswith("backbone.")}
    if "proj" in backbone or "last_layer_style" not in state:
        raise ValueError("CSD architecture differs")
    backbone["proj"] = state["last_layer_style"]
    model.load_state_dict(backbone, strict=True)
    if set(state) - {"last_layer_style", "last_layer_content"} - {
            "backbone." + k for k in backbone if k != "proj"}:
        raise ValueError("unexpected CSD state keys")
    del raw, state, backbone
    return model.eval(), lambda model, x: model(x)


def extract(name, device="mps", batch_size=4):
    import torch
    import transformers

    target = OUT / f"embeddings_{name}.npz"
    receipt_path = OUT / f"extraction_{name}.json"
    if target.exists() or receipt_path.exists():
        raise FileExistsError("do not overwrite completed extraction")
    manifest = s.read(OUT / "inputs.json")
    for p, sha in manifest["bindings"].items():
        if digest(s.ROOT / p) != sha:
            raise ValueError("frozen measurement input changed: " + p)
    preprocess = processor()
    start = now()
    model, forward = load_model(name)
    torch.set_num_threads(4)
    # IDs selected by input position before outcomes; include two generated and
    # one primary source. Validate backend and batching before cohort extraction.
    ix = [0, 1, next(i for i, r in enumerate(manifest["rows"])
                    if r["role"] == "reference")]
    sample = torch.stack([tensor_for(manifest["rows"][i], preprocess) for i in ix])
    with torch.inference_mode():
        cpu = torch.nn.functional.normalize(forward(model, sample), dim=1).numpy()
    model.to(device)
    with torch.inference_mode():
        actual = torch.nn.functional.normalize(forward(model, sample.to(device)), dim=1)
        singles = torch.cat([torch.nn.functional.normalize(
            forward(model, x[None].to(device)), dim=1) for x in sample])
        actual, singles = actual.cpu().numpy(), singles.cpu().numpy()
    backend_diff = float(np.abs(actual - cpu).max())
    batch_diff = float(np.abs(actual - singles).max())
    if backend_diff > 5e-5 or batch_diff > 5e-5:
        raise ValueError(f"device/batch validation failed: {backend_diff}, {batch_diff}")
    print(f"{name} validation: CPU/device {backend_diff:.3g}; batch {batch_diff:.3g}",
          flush=True)
    vectors, tensor_hashes = [], []
    elapsed_start = time.monotonic()
    for begin in range(0, len(manifest["rows"]), batch_size):
        rows = manifest["rows"][begin:begin + batch_size]
        for r in rows:
            if digest(s.ROOT / r["path"]) != r["sha256"]:
                raise ValueError("raw pixels changed during extraction")
        batch = torch.stack([tensor_for(r, preprocess) for r in rows])
        tensor_hashes.extend(hashlib.sha256(x.numpy().astype("<f4").tobytes()).hexdigest()
                             for x in batch)
        with torch.inference_mode():
            v = torch.nn.functional.normalize(forward(model, batch.to(device)), dim=1)
            vectors.append(v.cpu().numpy())
        if begin % 100 == 0:
            print(f"{name} {begin + len(rows)}/{len(manifest['rows'])} "
                  f"{time.monotonic() - elapsed_start:.1f}s", flush=True)
    values = np.concatenate(vectors).astype(np.float32)
    if values.shape != (2009, 768) or not np.isfinite(values).all():
        raise ValueError("incomplete or invalid vectors")
    if not np.allclose(np.linalg.norm(values, axis=1), 1, atol=1e-5):
        raise ValueError("nonunit vectors")
    with target.open("xb") as f:
        np.savez_compressed(f, embeddings=values)
    s.write_new(receipt_path, dict(started_utc=start, ended_utc=now(), model=MODELS[name],
        input_sha256=digest(OUT / "inputs.json"), plan_sha256=digest(PLAN),
        implementation_sha256=digest(Path(__file__)), embeddings_sha256=digest(target),
        tensor_sha256=tensor_hashes, shape=list(values.shape), dtype="float32",
        validation=dict(sample_indices=ix, cpu_device_max_abs=backend_diff,
                        batched_single_max_abs=batch_diff, tolerance=5e-5),
        environment=dict(python=platform.python_version(), torch=torch.__version__,
                         transformers=transformers.__version__, numpy=np.__version__,
                         device=device, batch_size=batch_size),
        processor=preprocess.to_dict()))
    del model
    gc.collect()
    if device == "mps":
        torch.mps.empty_cache()


def arrays(name, region=False):
    manifest = s.read(OUT / "inputs.json")
    receipt = s.read(OUT / f"extraction_{name}.json")
    path = OUT / f"embeddings_{name}.npz"
    if digest(path) != receipt["embeddings_sha256"]:
        raise ValueError("embedding archive changed")
    if digest(OUT / "inputs.json") != receipt["input_sha256"]:
        raise ValueError("input manifest changed")
    e = np.load(path, allow_pickle=False)["embeddings"].astype(np.float64)
    lookup = {(r["id"], r["view"]): v for r, v in zip(manifest["rows"], e)}
    x = np.full((6, 14, 2, 6, 768), np.nan)
    refs, devs = [[] for _ in range(4)], [[] for _ in range(4)]
    for row in manifest["rows"]:
        if row["view"] != "original":
            continue
        key = (row["id"], "audited_region") if region else (row["id"], "original")
        v = lookup.get(key, lookup[(row["id"], "original")])
        if row["role"] == "generated":
            x[s.MODELS.index(row["model"]), row["scene"], row["repeat"],
              s.ARMS.index(row["arm"])] = v
        else:
            (refs if row["role"] == "reference" else devs)[s.ARTISTS.index(
                row["painter"])].append(v)
    if not np.isfinite(x).all():
        raise ValueError("missing generated cell")
    return x, list(map(np.array, refs)), list(map(np.array, devs))


def analyze(check=False):
    from latent_art_bench import painter_learned_analysis_v1 as analysis

    result = {name: {view: analysis.analyze_arrays(*arrays(name, region))
                     for view, region in [("original", False), ("audited_region", True)]}
              for name in MODELS}
    paths = [PLAN, Path(__file__), Path(analysis.__file__), OUT / "inputs.json"]
    paths += [OUT / f"extraction_{name}.json" for name in MODELS]
    paths += [OUT / f"embeddings_{name}.npz" for name in MODELS]
    result["bindings"] = bindings(paths)
    if check:
        if result != s.read(OUT / "analysis.json"):
            raise ValueError("numerical replay differs")
        print("Exact learned-vector numerical replay passed")
    else:
        s.write_new(OUT / "analysis.json", result)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("action", choices=["freeze", "extract", "analyze", "check"])
    p.add_argument("--model", choices=list(MODELS))
    p.add_argument("--device", choices=["cpu", "mps"], default="mps")
    p.add_argument("--batch-size", type=int, default=4)
    args = p.parse_args()
    if args.action == "extract":
        if not args.model:
            p.error("extract requires --model")
        extract(args.model, args.device, args.batch_size)
    elif args.action in {"analyze", "check"}:
        analyze(args.action == "check")
    else:
        freeze()


if __name__ == "__main__":
    main()
