# Learned-formal checkpoint feasibility spike

## Decision

Status: **pending; not eligible for pilot generation qualification**.

The intended source-faithful evaluator is the A-vector from Kim et al. (2026), [“Context-aware multimodal AI navigates hidden pathways in five centuries of art evolution”](https://doi.org/10.1073/pnas.2517969123). The pilot freezes the public code at commit [`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0).

## Recovered contract

The paper and released code agree on the following core construction:

- Stable Diffusion 2.0 `512-base-ema.ckpt`;
- forced `512 x 512` input for the paper-faithful path;
- first-stage autoencoder encoding via `encode_first_stage` followed by `get_first_stage_encoding`;
- a `4 x 64 x 64` latent flattened in NumPy/PyTorch C order to 16,384 values.

The source preprocessing and harmonized project preprocessing must remain different tracks because the source uses OpenCV `INTER_LANCZOS4` to stretch every image to a square, while the harmonized path preserves aspect ratio.

## Blocking findings at the frozen revision

- [`make_a-vector.py`](https://github.com/aljinny/art-history/blob/7da12358cf34dad2184f357a048c2cf114b3c4e0/001_Scripts/make_a-vector.py) contains the model-initialization block after a function return at the wrong indentation, so `model` is referenced before it is defined.
- The script embeds absolute author-local paths and requires an external Stable Diffusion checkout, configuration, dataset, and checkpoint layout.
- The repository lists several package versions but provides no complete lock file or environment specification.
- No license file was present in the audited source-code revision. That prevents this MIT-licensed project from copying the source implementation.
- The model checkpoint is not included, and its exact independently acquired bytes have not yet been hashed and recorded.

These are feasibility findings, not evidence that an A-vector implementation is impossible. The next legitimate step is to obtain and hash the exact checkpoint, resolve source-code reuse terms, repair the extractor in an isolated reproduction environment, and compare its output with a published or author-supplied reference vector. The pilot will not silently substitute a different VAE, checkpoint, layer, pooling rule, or generic embedding.
