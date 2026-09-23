"""CSD native crop adapter; preserves the completed CLIP extractor and inputs.

Torchvision CenterCrop rounds half-offsets; the Hugging Face CLIP processor
floors them. Use the documented native CSD convention explicitly, without
installing torchvision or changing CLIP embeddings. This adapter is bound in
the CSD processor record and its separate pre-extraction provenance supplement.
"""

from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench import painter_learned_audit_v1 as base

BINDING_NAME = "csd_adapter_inputs_v2.json"
ORIGINAL_LOADER = base.load_model


def load_model(name):
    """Strict CSD state loading from the authors' complete training checkpoint.

    Retain weights_only=True. The inspected payload includes optimizer metadata,
    NumPy scalars and an argparse Namespace; allow only these standard data
    types, then select the model_state_dict and discard training metadata.
    """
    if name != "csd":
        return ORIGINAL_LOADER(name)
    import argparse
    import importlib.util

    import torch

    info = base.MODELS[name]
    path = base.MODEL_ROOT / info["directory"] / info["file"]
    if base.digest(path) != info["sha256"]:
        raise ValueError("CSD checkpoint hash differs")
    unsafe = set(torch.serialization.get_unsafe_globals_in_checkpoint(path))
    if unsafe != {"numpy.dtype", "numpy.core.multiarray.scalar", "argparse.Namespace"}:
        raise ValueError("unexpected CSD metadata types")
    allowed = [argparse.Namespace, np.dtype, np.dtypes.Float64DType,
               (np._core.multiarray.scalar, "numpy.core.multiarray.scalar")]
    with torch.serialization.safe_globals(allowed):
        raw = torch.load(path, map_location="cpu", weights_only=True, mmap=True)
    if set(raw) != {"model_state_dict", "opt_bb", "opt_proj", "iter", "args", "fp16_scaler"}:
        raise ValueError("unexpected training checkpoint structure")
    state = {k.removeprefix("module."): v for k, v in raw["model_state_dict"].items()}
    if len(state) != 297 or state["last_layer_style"].shape != (1024, 768):
        raise ValueError("unexpected style model structure")
    if any(v.dtype != torch.float32 for v in state.values()):
        raise ValueError("expected float32 model parameters")
    source = base.MODEL_ROOT / "openai-clip-source/model.py"
    spec = importlib.util.spec_from_file_location("retained_openai_clip_csd", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    model = module.VisionTransformer(224, 14, 1024, 24, 16, 768)
    backbone = {k.removeprefix("backbone."): v for k, v in state.items()
                if k.startswith("backbone.")}
    if "proj" in backbone or set(state) - {"last_layer_style", "last_layer_content"} - {
            "backbone." + k for k in backbone}:
        raise ValueError("unexpected CSD tensor keys")
    backbone["proj"] = state["last_layer_style"]
    model.load_state_dict(backbone, strict=True)
    del raw, state, backbone
    return model.eval(), lambda model, x: model(x)


# This explicit adapter registration is shared by the CSD extraction entrypoint
# and the supplemental checker, which imports this module only for CSD.
# The frozen base source, CLIP model loader and completed CLIP records are intact.
base.load_model = load_model


class CSDNativeProcessor:
    def __call__(self, images, return_tensors="pt"):
        import torch

        if return_tensors != "pt":
            raise ValueError("only torch tensors supported")
        width, height = images.size
        if width <= height:
            target = (224, int(224 * height / width))
        else:
            target = (int(224 * width / height), 224)
        image = images.resize(target, resample=Image.Resampling.BICUBIC)
        left, top = [int(round((value - 224) / 2.0)) for value in image.size]
        image = image.crop((left, top, left + 224, top + 224)).convert("RGB")
        tensor = torch.from_numpy(np.array(image, copy=True)).permute(2, 0, 1).float().div(255)
        mean = torch.tensor([.48145466, .4578275, .40821073])[:, None, None]
        std = torch.tensor([.26862954, .26130258, .27577711])[:, None, None]
        return {"pixel_values": ((tensor - mean) / std)[None]}

    def to_dict(self):
        return dict(
            kind="official CSD torchvision-equivalent PIL resize/round-center-crop",
            shortest_edge=224, crop_size=224, interpolation="PIL bicubic",
            crop_offset="int(round((resized_dimension - 224) / 2.0))",
            conversion="uint8 RGB -> float32 / 255",
            mean=[.48145466, .4578275, .40821073],
            std=[.26862954, .26130258, .27577711],
            adapter_sha256=base.digest(Path(__file__)),
            binding_path=BINDING_NAME,
            binding_sha256=base.digest(base.OUT / BINDING_NAME),
            loader="CSD model_state_dict; weights_only=True with fixed standard metadata types",
        )


def freeze():
    paths = [Path(__file__), Path(base.__file__), base.PLAN, base.OUT / "inputs.json",
             base.s.ROOT / "uv.lock",
             base.MODEL_ROOT / "clip-vit-large-patch14/config.json",
             base.MODEL_ROOT / "clip-vit-large-patch14/preprocessor_config.json",
             base.MODEL_ROOT / "openai-clip-source/model.py",
             base.MODEL_ROOT / "openai-clip-source/LICENSE"]
    base.s.write_new(base.OUT / BINDING_NAME, dict(
        created_utc=base.now(), bindings=base.bindings(paths),
        explanation="Native CSD uses rounded center offsets; completed HF CLIP uses floors. "
                    "This implementation clarification precedes CSD outcomes. No outcome selected "
                    "the convention. Both follow their respective released preprocessing. "
                    "The public CSD file is a training checkpoint: model_state_dict is selected "
                    "with strict tensor checks; only fixed NumPy/argparse metadata types are "
                    "allowlisted under weights_only=True. Prior adapter/input is preserved.",
        storage_note="Initial simultaneous download exhausted local disk. The failed partial CSD "
                     "download was removed. Models are downloaded and used serially; downloaded "
                     "public CLIP weights may be evicted after extraction/validation. Exact "
                     "checkpoint revision/hash and embeddings remain. No research pixels removed.",
    ))


def main():
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=["freeze", "extract"])
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
        return
    for p, sha in base.s.read(base.OUT / BINDING_NAME)["bindings"].items():
        if base.digest(base.s.ROOT / p) != sha:
            raise ValueError("CSD adapter input differs: " + p)
    base.processor = CSDNativeProcessor
    base.extract("csd", device="mps", batch_size=4)


if __name__ == "__main__":
    main()
