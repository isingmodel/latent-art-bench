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
            binding_sha256=base.digest(base.OUT / "csd_adapter_inputs.json"),
        )


def freeze():
    paths = [Path(__file__), Path(base.__file__), base.PLAN, base.OUT / "inputs.json",
             base.s.ROOT / "uv.lock",
             base.MODEL_ROOT / "clip-vit-large-patch14/config.json",
             base.MODEL_ROOT / "clip-vit-large-patch14/preprocessor_config.json",
             base.MODEL_ROOT / "openai-clip-source/model.py",
             base.MODEL_ROOT / "openai-clip-source/LICENSE"]
    base.s.write_new(base.OUT / "csd_adapter_inputs.json", dict(
        created_utc=base.now(), bindings=base.bindings(paths),
        explanation="Native CSD uses rounded center offsets; completed HF CLIP uses floors. "
                    "This implementation clarification precedes CSD outcomes. No outcome selected "
                    "the convention. Both follow their respective released preprocessing.",
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
    for p, sha in base.s.read(base.OUT / "csd_adapter_inputs.json")["bindings"].items():
        if base.digest(base.s.ROOT / p) != sha:
            raise ValueError("CSD adapter input differs: " + p)
    base.processor = CSDNativeProcessor
    base.extract("csd", device="mps", batch_size=4)


if __name__ == "__main__":
    main()
