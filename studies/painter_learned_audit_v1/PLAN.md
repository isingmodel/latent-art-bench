# Same-image learned-representation audit, version 1

Recorded 2026-09-18 after the first independent scientific reviews, before any
learned embeddings or numerical outcomes from this cohort were inspected.
This is a retrospective extension, not a preregistered confirmation. The
31-feature findings and the reviewers' proposed direct naming decomposition
were already known. Preserve all earlier measurements and results.

## Question and fixed scope

Do conventional artist-prototype similarities and artist recognition describe
the same response as centered, labeled painter contrasts on the **same images
and in the same representation**? Does the descriptive Monet–Sisley pattern
persist or change with learned coordinates? Report agreement and disagreement;
neither representation adjudicates perceptual artistic fidelity.

Use every retained image from the completed six-configuration experiment:
1,008 generated outputs, 649 primary references and 221 development works.
No generation, new reference acquisition, human evaluation, training, fine
tuning or selection of a favorable subset. All four painters and all six
configurations remain. The development works provide a separate finite
reference-target sensitivity and a held-out prototype classification check;
they are not a newly acquired or historically unseen collection.

## Fixed representations and provenance

1. OpenAI CLIP ViT-L/14 from `openai/clip-vit-large-patch14`, revision
   `32bd64288804d66eefd0ccbe215aa642df71cc41`, `model.safetensors`, expected
   SHA-256 `a2bf730a0c7debf160f7a6b50b3aaf3703e7e88ac73de7a314903141db026dcb`.
2. Released CSD ViT-L/14 style head from `tomg-group-umd/CSD-ViT-L`, revision
   `5bc26a6fb0487f3f00a2a7313135103a005b1b67`, `pytorch_model.bin`, expected
   SHA-256 `40e92fad63a361b8136100cd234c42d401ef9b34ff1748234318929ebcc7e7a1`.
   Use `torch.load(weights_only=True)` and inspect/strictly validate tensor keys.
   The official CSD repository warns of a discrepancy between released weights
   and published numbers. This is a **public-checkpoint sensitivity**, not a
   reproduction of reported CSD benchmark performance. Model card license:
   CC-BY-4.0; implementation: MIT. Preserve source attribution.

The OpenAI vision-transformer implementation is fixed at commit
`a1d071733d7111c9c014f024669f959182114e33`; CSD architecture is documented at
`learn2phoenix/CSD` commit `3a9df32605b869eceb704897839be80977a9f1ea`.
Both output 768-dimensional unit vectors. Use native Euclidean/cosine geometry,
without coordinate IQR scaling, whitening or outcome-selected dimensions.
All four painters occur in the published CSD style-tag list. Unknown image
training overlap and artist exposure prevent any unseen-artist claim. CLIP
also has uncharacterized web-training overlap and content sensitivity.

Use models serially, evaluation mode, float32, MPS when available, batches of
four; a smaller batch/CPU fallback is allowed only for a recorded resource or
unsupported-operation failure, never because of scientific outcomes. No
alternative checkpoint may replace an unfavorable result.

## Pixels and preprocessing

Hash every retained source. Apply EXIF orientation and ICC-to-sRGB conversion
directly to original pixels, then each model's documented short-edge-224
bicubic resize, center crop to 224, and CLIP mean/std normalization. Do not
use the 512-pixel hand-feature thumbnail as an intermediate. Bind preprocessing
code, model files, model configurations, library versions, device and inputs
in immutable run records. Record SHA-256 of each processed tensor.

Primary learned view: native center crop of original source. Sensitivity:
native center crop of the previously audited painting region, replacing only
the 131 changed reference/development regions. These are not full-frame
measurements. Preserve the original AI-coded regions; this does not validate
them independently. Generated pixels have no region correction.

## Prespecified retrospective summaries

For each representation/view, compute all six configurations and all six
painter pairs, even where a result disagrees with the original findings:

- The 4×4 matrix of mean generated-name unit embeddings dotted with mean
  reference-painter unit embeddings. Prototypes are unnormalized means for
  average image-to-reference similarity. Report diagonal and off-diagonal
  similarity, and named-minus-generic/free changes in diagonal similarity.
- Nearest **unit-normalized** reference-prototype recognition and confusion,
  separately from unnormalized prototype similarity. Also classify the 221
  development works using the 649-work prototypes, macro-averaged over painters.
- Original centered cross-repeat beta, Q and D, scene-averaged D, and held-out
  scalar calibration. The normalizer is representation/view-specific reference
  contrast energy. Ratios across representations are descriptive, not a common
  perceptual scale. Report the reference energy and every painter-pair beta.
- Repeat-corrected common/specific fractions for both named-minus-free and
  named-minus-generic interventions. Negative cross-products are retained;
  ratios with a nonpositive denominator are undefined.
- Leave-one-scene-out ranges for aggregate beta/D, shared naming fraction and
  Monet–Sisley beta. These are influence ranges, not confidence intervals.
- Repeat the main summaries with the 221-work development panel as the target,
  using equal painter means. This changes the finite target; it is not an
  independent collection or service replication.
- Evaluate all 24 reference-label permutations for centered agreement and
  prototype diagonal score as diagnostic negative controls. Do not present
  post-result permutation ranks as confirmatory significance tests.

No new confirmatory p-values, population claim, expert agreement or service
independence claim. State which apparent discrepancies follow from definitions
and which are observed empirical patterns. Report failed loads or measurements
and partial coverage explicitly; complete coverage is required for a main result.

## Validation and outputs

Check exact input membership/hash coverage; finite unit vectors; strict model
tensor loading; CPU/MPS agreement on a fixed, preselected small sample; and
batch-size invariance within a recorded tolerance. Validate analysis using
constructed no-distinction, exact-match, doubled-contrast and label-swapped
cases, plus common-translation invariance. These are algebra checks, not
validation of artistic meaning. Numerical replay uses retained compact
embeddings; exact inference may vary slightly across library/device versions.

Write a new input manifest, extraction receipts, compressed feature arrays,
analysis JSON and report under `reports/painter_learned_audit_v1`. Do not rewrite
completed receipts. Subsequent corrections require a recorded new version.

## Primary sources

- https://github.com/openai/CLIP
- https://huggingface.co/openai/clip-vit-large-patch14
- https://github.com/learn2phoenix/CSD
- https://huggingface.co/tomg-group-umd/CSD-ViT-L
- https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/8294_ECCV_2024_paper.php
