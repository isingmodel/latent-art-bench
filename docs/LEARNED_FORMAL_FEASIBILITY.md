# Learned-formal feasibility: recovered method, failed pilot, and next study

## Current disposition

The learned-formal measurement is technically runnable but scientifically unqualified.
`pilot_1` is a **fail**, not a conditional pass:

- the 32-component PCA retained 61.5214% rather than the frozen 95% target;
- the same-work reproduction interval exceeded the frozen margin;
- all 108 primaries passed the released source's strict native-area rule, but one
  primary input violated its separate aspect-ratio domain;
- the artist-by-source split was incomplete; and
- the source-faithful preprocessing created a perfect real-JPEG/generated-PNG codec
  confound.

Generated-image traversal may continue only under the explicit test-only engineering
scope. The durable scientific result is the
[learned-formal qualification evidence](../reports/pilot_1/evidence/learned_formal_qualification.json).

## What the paper actually establishes

Kim et al. (2026),
["Context-aware multimodal AI navigates hidden pathways in five centuries of art evolution"](https://doi.org/10.1073/pnas.2517969123),
analyze 72,447 paintings by 2,354 painters across 128 conventional style periods. The
[public full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/) distinguishes two
representations:

- the A-vector, a 16,384-dimensional Stable Diffusion 2.0 autoencoder latent intended to
  emphasize formal visual properties; and
- the C-vector, a 1,024-dimensional CLIP representation intended to emphasize contextual
  and semantic properties.

The paper finds that C-vectors have substantially stronger temporal, artist, and
style-period structure than A-vectors. The A-vector is therefore a formal baseline, not
a paper-backed guarantee of artist separability.

The paper uses `512-base-ema.ckpt`, forces retained images to 512 x 512, excludes images
whose longer dimension is at least twice the shorter dimension, removes low-resolution
images around the 410 x 410 scale, and restricts the final study to 1500-1990. It does
not publish:

- the extracted A-vector array;
- an input/reference-vector fixture;
- the VAE posterior RNG state or per-image seed;
- a checksum or custody record for the exact checkpoint used by the authors;
- a 32-component cap or 95% PCA target; or
- a claim that A-vector distances are invariant to independent digitization or codec.

The project's PCA and stability gates are additional benchmark requirements. Their
failure must not be attributed to Kim et al., and their thresholds must not be changed
after seeing `pilot_1`.

## Exact behavior of the released source

The source revision is frozen at
[`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0).
Review of the checkout establishes the following execution path.

### Corpus screen

`01_data_preprocessing.ipynb`:

1. reads native dimensions with OpenCV;
2. computes `r = h / w if h > w else w / h`;
3. keeps only `r < 2`;
4. computes `size = h * w`; and
5. keeps only `size > 410 * 410`.

The article's prose describes a 410 x 410 resolution rule in terms of dimensions, while
the source uses area. They are not mathematically identical. A replication must record
both and state prospectively which domain it uses.

### Source-file preprocessing

[`make_resize_img.py`](https://github.com/aljinny/art-history/blob/7da12358cf34dad2184f357a048c2cf114b3c4e0/001_Scripts/make_resize_img.py):

1. loads with `cv2.imread`;
2. applies the script's RGB/BGR conversions;
3. resizes to exactly 512 x 512 with `cv2.INTER_LANCZOS4`;
4. converts channels again; and
5. writes the resized image using the original filename and therefore the original
   extension.

This last step is scientifically consequential. JPEG input produces a newly encoded
JPEG intermediate, while PNG input produces a PNG intermediate.

### Latent extraction

[`make-a-vector.py`](https://github.com/aljinny/art-history/blob/7da12358cf34dad2184f357a048c2cf114b3c4e0/001_Scripts/make-a-vector.py):

1. reopens the resized file with Pillow and converts it to RGB;
2. resizes dimensions down to multiples of 64 with Pillow Lanczos, a no-op for 512 x 512;
3. maps uint8 RGB to float values in `[-1, 1]` and forms NCHW input;
4. calls `model.encode_first_stage` and `model.get_first_stage_encoding`;
5. receives a sampled, scaled `4 x 64 x 64` latent from the referenced Stable Diffusion
   path; and
6. flattens the latent to 16,384 values.

The released file is not directly executable. Its model initialization is indented after
the return in `load_img`, so module-level code references an undefined `model`. It also
contains author-local absolute paths and depends on an external Stable Diffusion checkout,
configuration, and checkpoint. The repository names selected package versions but does
not provide a complete lock, and no explicit license file is present.

## What the clean-room recovery proves

Because the upstream repository has no explicit reuse license, the project implements the
public method contract without copying its code. The source-replication feature path:

- applies the recovered OpenCV same-extension resize/write behavior;
- reopens with Pillow RGB;
- maps to float32 `[-1, 1]`;
- encodes with the pinned SD2-base VAE;
- samples the posterior using a content-derived deterministic seed;
- applies latent scale `0.18215` explicitly;
- requires shape `4 x 64 x 64`; and
- flattens in C order to 16,384 float32 values.

The deterministic seed is a necessary repair because the authors did not publish their
RNG realization. Its representation version must remain distinct from the unrecoverable
author realization and from a posterior-mode deviation.

The [model verification report](../reports/pilot_1/evidence/learned_formal_model_verification.json)
establishes that the recovered Diffusers VAE and the mapped first-stage state in the
recovered full checkpoint from
[`Manojb/stable-diffusion-2-base@64bf7b4f10eee35494b38d55c06c0c78cf8b44d0`](https://huggingface.co/Manojb/stable-diffusion-2-base/tree/64bf7b4f10eee35494b38d55c06c0c78cf8b44d0)
contain exactly equal tensor payloads:

| Item | Verified value |
|---|---:|
| Mapped tensors | `248 / 248` exact |
| Float32 values | `83,653,863` |
| Logical tensor bytes | `334,615,452` |
| Attention conversions | 8 exact trailing-singleton squeezes |
| Full checkpoint SHA-256 | `d635794c1fedfdfa261e065370bea59c651fc9bfa65dc6d67ad29e11869a1824` |
| VAE safetensors SHA-256 | `a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815` |

This closes a container-equivalence question. It does not prove that the public mirror is
the exact author-used checkpoint, reproduce unpublished A-vectors, or guarantee
cross-environment inference identity.

The current extraction provenance is stronger than the earlier spike: all 119 real rows
record the verified source checkout and exact revision, input and intermediate hashes,
checkpoint artifacts, per-image seed, OpenCV/Pillow/JPEG versions, and Python/OS/CPU,
NumPy, PyTorch, Diffusers, and MPS state. Exact repeatability is claimed only under that
recorded environment.

## Frozen pilot_1 results

The evaluator processed 119 JPEG inputs representing 108 primary works plus 11 alternate
files. PCA was fitted on 76 real training primaries and applied without refitting to 32
held-out primaries and all alternates. Every leave-source-out fold refitted its own PCA.

| Diagnostic | Frozen result | Frozen rule | Disposition |
|---|---:|---:|---|
| Deterministic extraction probes | exact in the recorded environment | all exact | passed implementation check |
| PCA retained variance | `0.6152142296` with 32 components | `>= 0.95` | **failed** |
| Held-out artist balanced accuracy | `0.53125` | `>= 0.35` | passed diagnostic |
| Held-out source balanced accuracy | `0.5375` | `<= 0.55` | passed narrowly; not proof of no confounding |
| Nested leave-source-out artist accuracy | `0.4126566416` | `>= 0.30` | passed pooled diagnostic |
| Reproduction ratio | `0.7423170871` | upper 95% bound `<= 1.0` | **failed** |
| Reproduction 95% interval | `[0.5108065957, 1.1001825090]` | upper `<= 1.0` | **failed** |
| Released-source native-area eligibility | `108 / 108` | all strictly above `410 * 410` pixels | passed |
| Released-source aspect-ratio eligibility | `107 / 108` | all strictly below `2` | **failed** |
| Complete artist-by-source split | no | complete train and held-out support | **failed** |

The point reproduction ratio is below 1.0, but the frozen decision uses its bootstrap
upper bound. `1.1001825090 > 1.0`; it is a failure. Re-running bootstrap draws until a
lower bound appears would be optional stopping.

### PCA failure

The 95% target was not close: 32 components retained 61.5214%. The paper does not supply
the project's 32-component cap, and the project cannot retroactively reinterpret the cap
as success. The correct `pilot_1` action is to fail the learned measurement.

For a new study, component selection must be a prespecified algorithm fitted on real
training data only. If the retained-variance target cannot be met within the frozen
resource limit, that new study must also fail before generated results are opened.

### Aspect-ratio failure

All 108 primaries satisfy the released source's strict `width * height > 410 * 410`
screen. That result does not establish complete source-domain eligibility because the
aspect rule is independently conjunctive.

`reproduction-cma-136510-primary` is 900 x 419, giving aspect ratio about 2.148. Kim et
al. exclude ratios greater than or equal to 2 before square resizing. The input is outside
the cited domain, so a pipeline that includes it cannot claim complete Kim-domain
eligibility. The five alternate files for the same work do not make the ineligible
primary eligible.

### Artist-by-source failure

The four artist-by-four source grid is incomplete:

- Alfred Sisley has no CMA training work;
- Claude Monet has no CMA training work; and
- Claude Monet has no Met work in either training or held-out data.

These missing cells make artist and source partially aliased. The `0.5375` source
classification score and pooled leave-source-out artist score cannot identify what would
happen under a complete crossed design.

### Codec-by-origin failure

The source-faithful path preserves the source extension. In this corpus:

```text
119 real inputs:      JPEG -> OpenCV resize -> JPEG encode -> Pillow -> VAE
40 generated inputs: PNG  -> OpenCV resize -> PNG encode  -> Pillow -> VAE
```

The extra lossy encode is perfectly associated with `real`, while the lossless
intermediate is perfectly associated with `generated`. This is a deterministic design
confound, not noise. Neither more generated repetitions nor a classifier covariate can
recover the counterfactual feature values that were never measured.

## Prospective pilot_2 feasibility design

The A-vector can be reconsidered only in a new, preregistered study with new or sealed
real data. The following items are minimum conditions, not optional enhancements.

### 1. Freeze the representation contract

Before unsealing, freeze and hash:

- the Kim source revision and clean-room mapping;
- full checkpoint, VAE config, and VAE tensor hashes;
- Python, OS, architecture, OpenCV build, Pillow/JPEG, NumPy, PyTorch, Diffusers, device,
  and backend settings;
- posterior policy, base seed, content-hash seed derivation, latent scale, shape, dtype,
  and flatten order;
- the input eligibility rules and the handling of the article/source low-resolution
  discrepancy.

Retain the statement that the seeded vector is method-compatible but not the authors'
unknown realization.

### 2. Build a complete crossed corpus

Keep Monet, Sisley, Pissarro, and Cezanne as fixed artist targets and movement/era as
metadata. Before feature extraction, acquire equal planned numbers of independent works
for every retained artist-by-source cell, with both training and held-out support. Keep
every reproduction of a physical work in one split. If a complete common source roster
cannot be assembled, revise the roster before extracting features and issue a new frozen
protocol; do not analyze a structurally empty grid.

Every primary must have known native dimensions, ratio `< 2`, the frozen resolution rule,
an accepted crop/border review, and documented acquisition lineage.

### 3. Cross codec with origin

Generate three separately named feature tracks from both real and generated files:

1. a primary lossless track using the same pinned PNG intermediate for both origins;
2. a sensitivity track using the same pinned JPEG encoder, quality, and subsampling for
   both origins; and
3. the original-extension source-replication track as a secondary method audit.

Only tracks in which codec is independent of origin may support real/generated
comparisons. The primary track must be selected before generated features exist.

### 4. Select PCA on training data only

Preserve the 95% target rather than weakening it in response to `pilot_1`. Increase the
prospective training corpus and allow up to the preregistered rank/resource limit. On real
training primaries only:

1. fit the mean;
2. fit PCA;
3. select the smallest component count reaching 95%;
4. hash the mean, ordered basis, signs, component count, and library environment; and
5. freeze that state before held-out real or generated transformation.

Refit the entire operation within every resampling or held-source fold. If the 95% target
is unreachable, stop. Do not choose a count based on artist accuracy or generated-model
separation. This rule treats PCA as information-preserving compression: choose the
smallest training-only basis that leaves at most 5% of training variance outside the
primary representation. Record training-only reconstruction error and pairwise-distance
distortion as diagnostics, but do not use them after unsealing to choose a result-favorable
component count.

### 5. Expand independent reproduction evidence

Obtain independently captured or independently scanned reproductions with verified
lineage. Multiple derivatives from one institutional master do not count as independent
captures. Balance matched works across artists and sources, and treat one physical work
as one bootstrap unit.

Choose the required number through a preregistered simulation that targets precision of
the upper confidence bound at the frozen margin. Finish collection at the planned count,
not when the bound first passes.

### 6. Use paired artist-free controls

For every content prompt and requested model label, pair the named-artist prompt with an
otherwise identical artist-free prompt. Do not use an era or movement label as a
surrogate. Randomize call order in content blocks and preserve refusals and retries.
Analyze the within-block named-minus-control contrast before between-artist or
between-requested-label contrasts.

### 7. Use hierarchical uncertainty

The primary uncertainty unit is the physical work for real calibration and the content
block for generation. Captures are nested within work; repetitions and HTTP attempts are
nested within logical generation cells. Source is crossed with artist. With four
handpicked artists, inference is conditional on those artists, not a population of
artists.

Report intervals by artist and source and require every preregistered source fold to pass.
A pooled statistic cannot mask a zero or underpowered fold.

### 8. Require transport evidence before model-label comparison

The current OAuth path records the requested label but not authoritative executed-model
identity, and none of its 40 successful `1024x1024` requests returned 1024 x 1024. A
scientific generated-image comparison therefore requires an instrumented proxy trace that
captures the outbound body hash, per-send request ID, upstream path/status/safe headers,
actual dimensions, response schema, output hash, and any authoritative executed-model
field.

If the upstream service cannot prove executed identity, the result remains a comparison
of requested-label endpoint behavior only. If dimension behavior remains nonconformant,
freeze a common actual-dimension eligibility and harmonization policy during a non-study
conformance phase; do not invent it after seeing study outputs.

## Reopening rule

The learned-formal scientific gate may reopen only when a new sealed qualification shows
all of the following:

- all inputs satisfy the frozen Kim domain;
- artist-by-source train and held-out coverage is complete;
- the primary codec track is identical across real and generated origins;
- the training-only PCA reaches 95%;
- the reproduction upper bound is at or below the frozen margin;
- every required source-held-out fold passes; and
- transport evidence supports the exact generated-data claim being made.

Until then, the clean-room extractor is a useful engineering artifact and the tensor
equivalence result is valid, but the learned-formal measurement is not qualified for a
scientific comparison of `gpt-image-1` and `gpt-image-2`.
