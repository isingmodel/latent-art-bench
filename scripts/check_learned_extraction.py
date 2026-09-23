"""Supplemental four-image CPU/MPS and batching check; never loads paper outcomes.

Use --describe without model loading. Use --run --inference-idle only after the
main extraction jobs have stopped. The single per-model receipt is immutable.
The processor factory is obtained from the extractor at execution time, so a
model-aware native processor can replace the current zero-argument API.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import inspect
import json
import platform
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench import painter_learned_audit_v1 as extractor

TOLERANCE = 5e-5
BATCH_SIZE = 4
FULL = [0, 0, 1, 1]
ROOT = extractor.s.ROOT


def validate_rows(rows, require_cohort=True):
    """Check original/region identity membership before selecting any pixels."""
    keyed = {}
    for row in rows:
        key = row["id"], row["view"]
        if key in keyed:
            raise ValueError("duplicate image/view identity")
        keyed[key] = row
        if row["role"] not in {"generated", "reference", "development"}:
            raise ValueError("unknown source role")
        box = row["box"]
        if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
            raise ValueError("invalid normalized crop box")
        if row["view"] == "original":
            if box != FULL:
                raise ValueError("original row must use the full image")
        elif row["view"] == "audited_region":
            if row["role"] == "generated" or box == FULL:
                raise ValueError("audited region must be a changed historical region")
        else:
            raise ValueError("unknown measurement view")
    for row in rows:
        if row["view"] == "audited_region":
            original = keyed.get((row["id"], "original"))
            keys = ("role", "path", "sha256", "painter")
            if original is None or any(original.get(k) != row.get(k) for k in keys):
                raise ValueError("audited region does not match its original source")
    counts = Counter(row["role"] for row in rows if row["view"] == "original")
    regions = sum(row["view"] == "audited_region" for row in rows)
    if require_cohort and (counts != {"generated": 1008, "reference": 649, "development": 221}
                           or regions != 131 or len(rows) != 2009):
        raise ValueError("the complete original cohort and all 131 regions are required")
    return dict(original_counts=dict(counts), region_count=regions, input_rows=len(rows))


def oriented_dimensions(path):
    """Read dimensions without color transformation or neural processing."""
    with Image.open(path) as image:
        width, height = image.size
        orientation = image.getexif().get(274, 1)
    return (height, width) if orientation in {5, 6, 7, 8} else (width, height)


def odd_aspect_candidate(size):
    """Stress a non-square resize where floor and round center offsets differ."""
    width, height = size
    resized_long = int(224 * max(width, height) / min(width, height))
    offset = (resized_long - 224) / 2.0
    return width != height and int(np.floor(offset)) != int(round(offset))


def select_cases(rows, root=ROOT):
    """First eligible rows in frozen order; four fixed categories, no embeddings."""
    generated = next(i for i, r in enumerate(rows)
                     if r["role"] == "generated" and r["view"] == "original")
    reference = next(i for i, r in enumerate(rows)
                     if r["role"] == "reference" and r["view"] == "original")
    odd = next(i for i, r in enumerate(rows)
               if i != reference and r["role"] == "reference" and r["view"] == "original"
               and odd_aspect_candidate(oriented_dimensions(root / r["path"])))
    region = next(i for i, r in enumerate(rows)
                  if r["role"] == "reference" and r["view"] == "audited_region")
    labels = ("original_generated", "original_reference", "odd_aspect_reference", "audited_region")
    selected = []
    for label, index in zip(labels, (generated, reference, odd, region)):
        row = rows[index]
        path = root / row["path"]
        if extractor.digest(path) != row["sha256"]:
            raise ValueError("selected source hash differs: " + row["id"])
        selected.append(dict(case=label, index=index, row=row,
                             oriented_source_size=list(oriented_dimensions(path))))
    if len({case["index"] for case in selected}) != BATCH_SIZE:
        raise ValueError("four distinct input rows required")
    return selected


def make_processor(name):
    """Support both processor() and a model-aware processor(name) without fallback."""
    if name == "csd":
        from latent_art_bench.painter_learned_csd_v1 import CSDNativeProcessor

        return CSDNativeProcessor()
    factory = extractor.processor
    signature = inspect.signature(factory)
    if not signature.parameters:
        return factory()
    try:
        signature.bind(name)
    except TypeError as error:
        raise TypeError("processor must accept no arguments or the model name") from error
    return factory(name)


def source_path(obj):
    try:
        return Path(inspect.getfile(obj)).resolve()
    except (TypeError, OSError):
        return None


def file_bindings(paths):
    result = []
    for path in sorted({Path(p).resolve() for p in paths if p is not None}):
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            label = str(path.relative_to(ROOT))
        except ValueError:
            label = str(path)
        result.append(dict(path=label, sha256=extractor.digest(path)))
    return result


def package_versions():
    versions = {}
    for package in ("torch", "transformers", "numpy", "Pillow", "safetensors",
                    "torchvision", "huggingface-hub", "tokenizers"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def describe_processor(preprocess):
    cls = type(preprocess)
    return dict(
        type=cls.__module__ + "." + cls.__qualname__,
        serialized_configuration=preprocess.to_dict() if hasattr(preprocess, "to_dict") else None,
        configuration_scope=(
            "Factory and runtime source hashes bind native settings when no to_dict API exists."
        ),
    )


def tensor_digest(tensor):
    return hashlib.sha256(tensor.detach().cpu().numpy().astype("<f4").tobytes()).hexdigest()


def run_validation(name, manifest_path, extraction_path, selected):
    """One model in memory, fixed CPU threads and four-case batches on each device."""
    import torch

    previous = extractor.s.read(extraction_path)
    if previous["input_sha256"] != extractor.digest(manifest_path):
        raise ValueError("input manifest does not match the completed extraction receipt")
    if not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable; CPU-only validation cannot satisfy this check")
    info = extractor.MODELS[name]
    model_path = extractor.MODEL_ROOT / info["directory"] / info["file"]
    config_dir = extractor.MODEL_ROOT / "clip-vit-large-patch14"
    paths = [Path(__file__), Path(extractor.__file__), extractor.PLAN,
             ROOT / "uv.lock", ROOT / "pyproject.toml", manifest_path, extraction_path,
             config_dir / "config.json", config_dir / "preprocessor_config.json",
             extractor.MODEL_ROOT / "openai-clip-source/model.py", model_path,
             ROOT / "tests/painter_learned_audit_v1/test_pixels.py"]
    paths += sorted(model_path.parent.glob("*.json"))
    if name == "csd":
        from latent_art_bench import painter_learned_csd_v1 as adapter

        paths += [Path(adapter.__file__), extractor.OUT / "csd_adapter_inputs.json"]
    preprocess = make_processor(name)
    paths += [source_path(extractor.processor), source_path(type(preprocess))]
    batch = torch.stack([extractor.tensor_for(case["row"], preprocess) for case in selected])
    if batch.shape != (BATCH_SIZE, 3, 224, 224) or batch.dtype != torch.float32:
        raise ValueError("expected four float32 3x224x224 processor tensors")
    if not torch.isfinite(batch).all():
        raise ValueError("nonfinite processor tensor")
    tensor_hashes = [tensor_digest(tensor) for tensor in batch]
    expected = [previous["tensor_sha256"][case["index"]] for case in selected]
    if tensor_hashes != expected:
        raise ValueError("selected processor tensors differ from the recorded extraction")
    torch.set_num_threads(4)
    model, forward = extractor.load_model(name)
    model.eval()
    if any(p.is_floating_point() and p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError("validation requires the planned float32 model")
    paths += [source_path(type(model)), source_path(forward)]
    bindings = file_bindings(paths)
    try:
        with torch.inference_mode():
            cpu_batch = torch.nn.functional.normalize(forward(model, batch), dim=1).cpu().numpy()
            cpu_single = torch.cat([
                torch.nn.functional.normalize(forward(model, row[None]), dim=1)
                for row in batch
            ]).cpu().numpy()
        model.to("mps")
        with torch.inference_mode():
            device_batch = batch.to("mps")
            mps_batch = torch.nn.functional.normalize(
                forward(model, device_batch), dim=1
            ).cpu().numpy()
            mps_single = torch.cat([
                torch.nn.functional.normalize(forward(model, row[None]), dim=1)
                for row in device_batch
            ]).cpu().numpy()
        outputs = {"cpu_batch4": cpu_batch, "cpu_single": cpu_single,
                   "mps_batch4": mps_batch, "mps_single": mps_single}
        if any(v.shape != (4, 768) or not np.isfinite(v).all() for v in outputs.values()):
            raise ValueError("invalid normalized validation descriptors")
        comparisons = {}
        for left, right in [("cpu_batch4", "mps_batch4"), ("cpu_batch4", "cpu_single"),
                            ("mps_batch4", "mps_single"), ("cpu_single", "mps_single")]:
            per_case = np.abs(outputs[left] - outputs[right]).max(axis=1)
            comparisons[left + "_vs_" + right] = dict(
                max_abs=float(per_case.max()), per_case_max_abs=per_case.tolist(),
                passed=bool(per_case.max() <= TOLERANCE),
            )
        if bindings != file_bindings(paths):
            raise ValueError("a bound source or configuration changed during validation")
        return dict(
            status="passed" if all(r["passed"] for r in comparisons.values()) else "failed",
            model=name, checkpoint=extractor.MODELS[name], tolerance=TOLERANCE,
            batch_size=BATCH_SIZE, cpu_threads=4, dtype="float32",
            input_manifest_sha256=extractor.digest(manifest_path),
            extraction_receipt_sha256=extractor.digest(extraction_path),
            extraction_implementation_sha256=previous["implementation_sha256"],
            validation_extractor_sha256=extractor.digest(Path(extractor.__file__)),
            processor=describe_processor(preprocess), processed_tensor_sha256=tensor_hashes,
            processed_tensors_match_extraction=True, cases=selected,
            comparisons=comparisons, bindings=bindings,
            environment=dict(python=platform.python_version(), platform=platform.platform(),
                             machine=platform.machine(), packages=package_versions(),
                             mps_built=torch.backends.mps.is_built(), mps_available=True),
            scope=(
                "Four deterministic cases validate backend and batch consistency, "
                "not artistic fidelity or every cohort output."
            ),
        )
    finally:
        del model
        gc.collect()
        torch.mps.empty_cache()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--model", required=True, choices=tuple(extractor.MODELS))
    parser.add_argument("--input-manifest", type=Path, default=extractor.OUT / "inputs.json")
    parser.add_argument("--extraction-receipt", type=Path)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--describe", action="store_true", help="select cases; never load a model")
    action.add_argument("--run", action="store_true", help="load one model and write its receipt")
    parser.add_argument("--inference-idle", action="store_true",
                        help="explicit acknowledgement that main inference has stopped")
    args = parser.parse_args()
    if args.run and not args.inference_idle:
        parser.error("--run requires --inference-idle; do not overlap the main extraction")
    manifest = extractor.s.read(args.input_manifest)
    census = validate_rows(manifest["rows"])
    selected = select_cases(manifest["rows"])
    if args.describe:
        print(json.dumps(dict(census=census, cases=selected), indent=2))
        return
    target = extractor.OUT / f"validation_{args.model}.json"
    if target.exists():
        raise FileExistsError("supplemental validation receipt exists; never overwrite it")
    extraction_path = args.extraction_receipt or extractor.OUT / f"extraction_{args.model}.json"
    if not extraction_path.is_file():
        raise FileNotFoundError("completed extraction receipt required before model loading")
    started = extractor.now()
    try:
        result = run_validation(args.model, args.input_manifest, extraction_path, selected)
    except Exception as error:
        result = dict(status="failed", model=args.model, tolerance=TOLERANCE,
                      cases=selected, exception_type=type(error).__name__, error=str(error))
    result.update(
        schema_version=1, started_utc=started, ended_utc=extractor.now(), census=census,
        selection_rule=(
            "First original generated, first original reference, first distinct reference "
            "where floor/round center offsets differ after 224-short-edge resizing, "
            "first audited reference region; frozen row order."
        ),
    )
    extractor.s.write_new(target, result)
    print(json.dumps(dict(status=result["status"], receipt=str(target)), indent=2))
    if result["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
