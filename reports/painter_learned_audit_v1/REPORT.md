# Same-image learned-representation audit: implementation report

Completed descriptive analysis; implementation summary, not an independent scientific review.
The [plan](../../studies/painter_learned_audit_v1/PLAN.md) was fixed after the
hand-feature results were known and before learned outcomes were inspected.
The completed [analysis](analysis.json) has SHA-256
`06c77de4be133afc203dda122b2816d4f866e1389999f18bc94b3d9c668f28f7`.

## Complete census and representations

Both extractions contain **2,009 finite unit vectors with 768 coordinates each**: 1,878
original sources (1,008 generated, 649 primary-reference and 221 development
images), plus 131 audited-region views (90 primary, 41 development). Region
sensitivities replace those originals rather than adding works. Every requested
configuration, scene, repeat, prompt arm and painter remains. No new images were
generated or acquired. Each original source and processed tensor is hash-bound.

| Encoder | Public checkpoint | Revision prefix | Raw weight SHA-256 prefix |
|---|---|---|---|
| CLIP ViT-L/14 | `openai/clip-vit-large-patch14`, `model.safetensors` | `32bd64288804` | `a2bf730a0c7d` |
| CSD ViT-L/14 style head | `tomg-group-umd/CSD-ViT-L`, `pytorch_model.bin` | `5bc26a6fb048` | `40e92fad63a3` |

Full identifiers, software versions and configuration hashes are in
[inputs.json](inputs.json), the [CLIP receipt](extraction_clip.json), the
[CSD receipt](extraction_csd.json) and [CSD adapter v2 binding](csd_adapter_inputs_v2.json).
Models used evaluation mode, float32 and MPS batches of four. Native unit-vector
geometry was retained without IQR scaling, whitening or fitting.

Preprocessing begins with original pixels, EXIF orientation and valid ICC-to-sRGB
conversion, followed by the optional audited region, bicubic short-edge resize
to 224, a 224-square center crop and CLIP channel normalization. CLIP uses the
Hugging Face floor-offset crop; CSD uses the official torchvision-equivalent
rounded offset. Odd resized dimensions can therefore differ by one pixel.
These learned views are not the full-frame hand-feature measurement.

Strict loading verifies CLIP's legacy deterministic position buffer before
omitting that nonpersistent buffer. CSD selects the released training checkpoint's
`model_state_dict`, verifies tensor keys/dtypes and the style projection, and uses
its style head followed by normalization. The separately bound v2 adapter preserves
completed CLIP provenance. Preflight versions and corrections remain recorded in
[implementation notes](IMPLEMENTATION_NOTES.md) and the
[extraction implementation review](EXTRACTION_REVIEW.md). CSD's released weights
carry an upstream warning that they do not reproduce the published benchmark
numbers; this audit characterizes that fixed public checkpoint.

## Original-source, primary-target findings

The following points use all 649 primary references and each encoder's native
crop. Macro accuracy classifies the 112 named generated images per configuration
with four unit-normalized reference prototypes.

| Requested configuration | CLIP MS β | CSD MS β | CLIP common prototype gain % | CSD common prototype gain % | CLIP macro % | CSD macro % |
|---|---:|---:|---:|---:|---:|---:|
| GPT Image 1 | 0.301 | 0.446 | 74.5 | 72.7 | 60.7 | 72.3 |
| GPT Image 2 | 0.532 | 0.587 | 73.2 | 54.2 | 68.8 | 75.9 |
| GPT Image 2.5 Flare | 0.339 | 0.451 | 78.8 | 65.0 | 59.8 | 62.5 |
| GPT Image 2.5 Sunburst | 0.385 | 0.323 | 77.7 | 67.4 | 58.9 | 61.6 |
| Nano Banana 2 | 0.318 | 0.400 | 83.8 | 79.7 | 51.8 | 50.9 |
| FLUX.2 Max | 0.299 | 0.414 | 81.7 | 77.6 | 41.1 | 39.3 |

All six Monet–Sisley alignments are positive in both learned representations.
Thus the weak/reversed hand-feature pattern does not generalize across these
measurement choices. All-painter β ranges from 0.438–0.770 in CLIP and
0.526–0.936 in CSD; scene-conditional D ranges from 0.847–1.136 and
0.714–0.999, respectively. Their reference contrast energies differ
(0.138801 versus 0.325001), so these normalized quantities are not a common
perceptual scale. Classification of the existing development works with primary
prototypes has macro accuracy 79.8% in CLIP and 79.6% in CSD.

### Two different common fractions

The table's **prototype-gain common fraction** divides a common shift's inner
product with the mean reference prototype by the named-minus-generic diagonal
similarity gain. With unnormalized mean prototypes, that gain is exactly
`common contribution + H × β / 4`. This fraction is 73.2–83.8% in CLIP and
54.2–79.7% in CSD. It describes a decomposition of average cosine-similarity gain,
not a fraction of squared movement.

The **squared-change common fraction** instead uses scene-averaged changes and
cross-repeat products. It is 90.4–94.3% relative to artist-free prompts and
76.1–82.3% relative to generic painting in CLIP; corresponding CSD ranges are
86.4–91.0% and 68.8–77.4%. These fractions depend only on generated embeddings,
whereas prototype-gain fractions also depend on the reference target. Negative
cross-products remain signed; nonpositive denominators yield undefined fractions.

The complete JSON retains original/audited views, primary/development targets,
all six painter pairs, recognition confusion matrices, centered geometry,
calibration, scene deletion and label-permutation summaries. The generated
[appendix tables](../../paper/icml_learned_results.tex) cover every
representation/view/target/configuration combination without selecting favorable
outcomes.

## Verification and storage

The [CLIP](validation_clip.json) and [CSD](validation_csd.json) supplemental receipts
both pass their four-case CPU/MPS and batch-four/single comparisons at tolerance
`5e-5`. Cases cover an original generated image, an original reference, an
odd-aspect reference and an audited region. Maximum absolute normalized-coordinate
differences are `8.111819624900818e-7` and `1.2516975402832031e-6`; MPS batch/single
differences are zero for both. Processed-tensor hashes match extraction. This
verifies those numerical cases, not every possible image or artistic meaning.

Verification run for this report: exact learned-vector replay passed; all **25
tests** passed, including constructed geometry/identity cases, input validation,
orientation, color-profile handling and region semantics. Numerical table replay
also passes with analysis input hashes verified:

```sh
uv run --locked python -m latent_art_bench.painter_learned_audit_v1 check
uv run --locked pytest -q tests/painter_learned_audit_v1
uv run --locked python paper/make_icml_learned_tables.py --check
```

Only the newly downloaded public weight caches were evicted after their
extraction and validation, as recorded for [CLIP](checkpoint_cache_eviction.json)
and [CSD](checkpoint_cache_eviction_csd.json). **No research pixels were lost.**
Embeddings, model identities/hashes, configurations, source code and receipts
remain. Numerical replay needs no weight download; fresh inference requires the
specified public checkpoint bytes and may vary slightly across environments.
The local [pixel inventory](../icml_review_v1/artifact_inventory.json) and
[attribution inventory](../icml_review_v1/artifact_attribution.json) make retained
contents reviewable without claiming public pixel access or a published release.

## Interpretation limits

This is a retrospective, same-image sensitivity, not a fresh generation or
service replication. CLIP and CSD are related representations; CSD derives from
CLIP and all four painters occur in its published style-tag list. Uncharacterized
training-image overlap and content sensitivity remain. The 221-work development
panel was already used in the project, and audited regions remain AI-coded.
There is no human perceptual ground truth or unseen-artist claim. Leave-one-scene
deletion ranges measure influence, not confidence intervals. Prototype-score,
β and D rankings under reference-label permutations are algebraically linked,
not independent corroboration or confirmatory significance tests.
