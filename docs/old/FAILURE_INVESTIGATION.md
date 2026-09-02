# Pilot failure investigation and the prospective pilot_2 design

## Decision

`pilot_1` failed its scientific qualification gate. It must not be described as a pass,
a conditional scientific pass, or evidence that either requested image-model label is
better. The completed generation path is an engineering traversal only:

- the configuration was explicitly `api_integration_test_only` and disabled scientific
  claims;
- generation requested only `gpt-image-1` and `gpt-image-2` through the loopback
  `~/dev/openai-oauth` service;
- the real-image measurement gates did not qualify the scientific analysis;
- the OAuth transport proves the requested labels and returned files, not the model that
  the upstream service actually executed.

The durable failure evidence is the
[chromatic qualification result](../../reports/pilot_1/evidence/chromatic_qualification.json),
the
[learned-formal qualification result](../../reports/pilot_1/evidence/learned_formal_qualification.json),
the
[model-tensor verification](../../reports/pilot_1/evidence/learned_formal_model_verification.json),
and the
[generation-manifest attestation](../../reports/pilot_1/evidence/generation_manifest_attestation.json).
`pilot_0` remains a separate, earlier failed pilot. Nothing learned from either pilot may
be used to relabel its frozen outcome.

## Evidence boundaries

This investigation distinguishes four kinds of evidence:

1. Claims made by the cited papers.
2. Behavior recoverable from the authors' released source.
3. Results observed in the frozen project corpus and pipeline.
4. Capabilities and omissions of the local OAuth transport.

Passing a formula unit test is not the same as recovering a paper's empirical result.
Matching checkpoint tensors is not the same as reproducing unpublished latent vectors.
Forwarding a model string is not the same as proving which model ran. These boundaries
govern every conclusion below.

## What Lee et al. (2018) establish

The source is Lee et al.,
["Heterogeneity in chromatic distance in images and characterization of massive painting data set"](https://doi.org/10.1371/journal.pone.0204430).

The paper analyzes 179,853 images from Web Gallery of Art, WikiArt, and BBC Your
Paintings. It defines the Euclidean CIE 1976 L*a*b* distance `d` between adjacent pixels,
forms the full inter-pixel distribution `pi(d)`, and rescales that distribution by the
image-specific mean distance. In Figure 1, the raw distributions vary with image size,
while the mean-rescaled distributions for two example paintings collapse across the
tested resolutions. That full distributional collapse is the paper's empirical
resolution result.

The paper then derives the scalar seamlessness statistic from the coefficient of
variation:

```text
S = (sigma_d / mean_d - 1) / (sigma_d / mean_d + 1)
  = (sigma_d - mean_d) / (sigma_d + mean_d).
```

Delta-like, exponential, and heavy-tailed distributions correspond to values near
`-1`, `0`, and `1`. Monte Carlo reconstructions with a target `pi(d)` support the
interpretation of the distribution as a representation of color contrast. The paper
uses `S` to study historical variation, individual change, and singularity. It does not
establish any of the following:

- invariance to JPEG quality or chroma subsampling;
- equivalence across independent digitizations of one physical work;
- an artist classifier, an ICC rule, or the project's practical-equivalence margins;
- validity for partial paintings, nonrectangular frames, serious damage, or photographs.
  The paper says such inputs were excluded.

Consequently, the source behavior to recover is not only the algebraic behavior of `S`.
A faithful qualification must also test the full normalized `pi(d)` collapse on eligible
real images across a preregistered resolution grid.

## What Kim et al. (2026) establish

The source is Kim et al.,
["Context-aware multimodal AI navigates hidden pathways in five centuries of art evolution"](https://doi.org/10.1073/pnas.2517969123),
with [public full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/) and released
source at commit
[`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0).

The paper's final corpus contains 72,447 Western paintings from 2,354 painters and 128
conventional style periods, dated 1500-1990. It distinguishes:

- a 16,384-dimensional A-vector from the Stable Diffusion 2.0 autoencoder, intended to
  retain formal visual information; and
- a 1,024-dimensional CLIP C-vector, intended to emphasize contextual information.

The paper forces retained images to 512 x 512 for the `512-base-ema.ckpt` model. It
excludes images whose longer dimension is at least twice the shorter dimension and
describes removing low-resolution images around the 410 x 410 scale. Its principal
scientific result is comparative: C-vectors encode artist, style-period, and temporal
structure more strongly than A-vectors. The A-vector is useful but deliberately a weaker
baseline for those tasks.

Kim et al. do not publish A-vector bytes, a checksum for the checkpoint they used, the
VAE posterior RNG state, or a reference input/vector pair. The paper also does not set a
32-component PCA cap or a 95% retained-variance gate. Those are project design choices,
not claims inherited from Kim et al.

## Faithful behavior recovered from the Kim source

The exact checkout exposes details that the article alone does not:

1. `01_data_preprocessing.ipynb` computes `max(h/w, w/h)` and retains only ratios
   strictly below 2. It implements the low-resolution screen as image area greater than
   `410 * 410`, which is not identical to requiring both dimensions to exceed 410.
2. `make_resize_img.py` reads with OpenCV, performs the script's RGB/BGR swaps, resizes
   to exactly 512 x 512 with `cv2.INTER_LANCZOS4`, and writes to the original filename.
   The original extension therefore controls the intermediate codec.
3. `make-a-vector.py` reopens the resized file with Pillow, converts to RGB, maps it to
   `[-1, 1]`, calls `encode_first_stage` and `get_first_stage_encoding`, flattens the
   resulting latent, and stores it. Under the referenced Stable Diffusion code path,
   `get_first_stage_encoding` samples the posterior and applies the latent scale.
4. The released script cannot run unchanged: its model-initialization block is indented
   after a function return, `model` is then referenced at module scope, and paths point
   to the authors' local filesystem. The repository also has no explicit license file.
5. The README names Python 3.8.5, NumPy 1.23.1, PyTorch 2.0.1, scikit-learn 1.1.3,
   SciPy 1.9.3, CUDA 12.6, and Stable Diffusion 2.0, but it is not a complete environment
   lock.

The project therefore uses a clean-room extractor and a content-derived seed to make
the omitted posterior-sampling policy deterministic. This is a versioned repair. It is
not the authors' unknown RNG realization.

The recovered full checkpoint and the Diffusers VAE were checked independently. All
248 mapped first-stage tensors - 83,653,863 float32 values - are bit-for-bit equal after
the eight documented singleton-dimension conversions. This establishes equality between
those two recovered model containers. It does not establish that the public mirror is
the exact file used by Kim et al., nor that another PyTorch/Diffusers/backend stack will
produce identical vectors.

## Confirmed pilot_1 scientific failures

The values below are outcomes under the frozen `pilot_1` rules. A favorable point
estimate does not override a failed interval rule, an ineligible input, a missing design
cell, or a missing source-behavior test.

### Chromatic measurement

| Check | Frozen observation | Scientific disposition |
|---|---:|---|
| Formula probes for `S` | passed | Necessary but insufficient |
| Adapted full normalized-distribution diagnostic | 91/108 images pass both 500-vs-400 and 500-vs-256 comparisons at the frozen project margin `K-S D <= 0.05`; 17/108 fail at least one pair | diagnostic ran, but **did not recover the source behavior** |
| Exact Lee Figure 1 resolution domain | 0/108 primaries support the 500-3000 px grid without upsampling; 0/108 are border-cleared, and partial-capture/damage reviews are absent | **ineligible and unsupported** |
| Eligible primary images after border/frame review | `0 / 108`; all 108 were `not_reviewed` | **failed source-input eligibility** |
| Same-work reproduction ratio | point `0.5882766278`; 95% interval `[0.2433774343, 1.8285907947]` | **failed** because upper bound exceeds `1.0` |
| Matched Q85 4:2:0 codec ratio | point `0.4325558376`; 95% interval `[0.2634302557, 0.6231027032]` | **failed** because upper bound exceeds `0.5` |
| Held-out artist balanced accuracy | `0.3506944444` | only narrowly meets the aggregate floor |
| Artist recall by class | Sisley `0.8333`, Monet `0.4444`, Pissarro `0.0`, Cezanne `0.125` | artist signal is not uniform |
| Leave-source-out artist accuracy | pooled `0.3369674185`; folds AIC `0.3277`, CMA `0.0` (`n=2`), Met `0.2`, NGA `0.3729` | **failed the every-fold source-robustness rule** |

The full normalized-distribution collapse and the scalar formula probe answer different
questions. The adapted diagnostic was frozen before its first evaluation and did run,
but it neither reproduced Lee's 500-3000 px branch set nor passed for every image. More
fundamentally, none of the inputs met the complete paper-domain review and native-size
requirements. The source behavior was therefore not recovered, so the chromatic result
is `fail` even though some lossless resolution branches and the scalar algebra behaved
as expected.

### Learned-formal measurement

| Check | Frozen observation | Scientific disposition |
|---|---:|---|
| Source-method extraction | 119 finite vectors of length 16,384 | implementation path ran |
| PCA retained variance | 32 components retained `0.6152142296` (61.5214%) against a frozen 95% target | **failed** |
| Same-work reproduction ratio | point `0.7423170871`; 95% interval `[0.5108065957, 1.1001825090]` | **failed** because upper bound exceeds `1.0` |
| Kim released-source native-area domain | `108 / 108` primaries satisfy `width * height > 410 * 410` | passed this screen; it does not override other failures |
| Kim aspect-ratio domain | `107 / 108` primaries eligible | **failed**; `reproduction-cma-136510-primary` is 900 x 419, ratio 2.148 |
| Artist-by-source coverage | incomplete | **failed source-confounding control** |
| Held-out artist/source accuracy | `0.53125` / `0.5375` | diagnostics only; incomplete joint support prevents a clean interpretation |
| Nested leave-source-out artist accuracy | `0.4126566416` | pooled diagnostic, not a cure for missing artist-by-source cells |

The missing split cells are substantive, not cosmetic. Sisley has no CMA training work;
Monet has no CMA training work and no Met work in either split. A classifier can therefore
learn artist-source availability. A global source-prediction score below a chosen ceiling
does not prove that source confounding is controlled.

### The source-extension codec confound

All 119 real inputs are JPEG files. All 40 generated outputs are PNG files. The faithful
Kim preprocessing script writes its 512 x 512 intermediate using the source extension,
so the real path incurs a JPEG encode while the generated path retains a lossless PNG
intermediate. Origin and preprocessing codec are perfectly associated:

```text
real image      -> 512 x 512 JPEG intermediate -> VAE
generated image -> 512 x 512 PNG intermediate  -> VAE
```

Any real/generated latent difference can therefore include the codec difference. The
source-faithful path is useful for reproducing the released script, but it is not an
unconfounded primary comparison of real and generated images. Repeating the same run
cannot identify or remove this confound.

## OAuth transport investigation

The local service was launched from `~/dev/openai-oauth/packages/openai-oauth` on
`127.0.0.1:10531` without a `--base-url` override. Its source therefore uses the default
upstream `https://chatgpt.com/backend-api/codex`, not the official API host. The local
`POST /v1/images/generations` route validates the requested string against the two-item
allowlist and forwards the body to upstream `/images/generations`.

What the evidence establishes:

- 41 logical attempt records were preserved: 40 successes and one moderation refusal;
- the one refused `gpt-image-1` cell was later resent with the same frozen identity and
  succeeded; the refusal itself was not erased;
- 20 resolved files were requested with `gpt-image-1` and 20 with `gpt-image-2`;
- all successful outputs are content-addressed PNG files.

What the evidence does not establish:

- The 40 requests asked for `1024x1024`, but `0 / 40` outputs had those dimensions.
  Returned widths ranged from 1392 to 1412 and heights from 1114 to 1130, across nine
  observed dimension pairs. This is a systematic contract mismatch, not a transient
  failure that warrants blind retries.
- The proxy response and stored call record do not contain an authoritative executed
  model identifier. The local `/v1/models` endpoint appends the two image labels to its
  catalog, which establishes local availability declarations only.
- The stored calls do not preserve a contemporaneous wire-body digest, upstream target,
  upstream response ID/status headers, or a distinct record for every lower-level HTTP
  send. Existing request identities were reconstructed from legacy run evidence.
- Generic PNG provenance does not distinguish the executed image model.

Accordingly, the current data may be described only as outputs obtained after requesting
two labels through the local OAuth facade. They cannot support a scientific
`gpt-image-1` versus `gpt-image-2` comparison.

## Why more retries are not the remedy

Retries are appropriate for a transient transport error, rate limit, or an unresolved
frozen cell. They do not fix:

- ineligible inputs and the missing exact Lee 500-3000 px resolution domain;
- unreviewed borders and frames;
- an input outside Kim's aspect-ratio domain;
- an unattained PCA target;
- a confidence bound above the frozen reproduction margin;
- absent artist-by-source cells;
- a real-JPEG/generated-PNG preprocessing confound;
- missing proof of the executed upstream model; or
- a systematic 40-of-40 requested-size mismatch.

Those failures require a new design and new or sealed evidence. Retrying until a random
interval or point estimate crosses a threshold would be optional stopping and is
prohibited.

## Prospective pilot_2 design

`pilot_2` must receive a new protocol version and must be frozen before any new held-out
real features or generated outputs are inspected. It is not a repair label attached to
the existing results.

### 1. Preregistration and immutable boundaries

Before acquisition or unsealing, commit and hash:

- the exact hypotheses, estimands, equivalence margins, confidence level, multiplicity
  policy, stopping rules, and failure behavior;
- artist, source, medium, genre, phase, aspect, resolution, crop, border, and rights
  eligibility rules;
- checkpoint, source revision, environment fingerprint, preprocessing implementation,
  RNG policy, and feature schemas;
- the PCA selection algorithm and maximum permitted dimension;
- prompts, artist-free controls, requested model labels, repetitions, output-selection
  rule, and transport conformance tests;
- the complete analysis code and simulation-based sample-size justification.

No threshold, exclusion, PCA count, prompt, or source roster changes are permitted after
the relevant held-out data are visible. A necessary change creates `pilot_3`.

### 2. Artist-level target, not era as a substitute

Retain the previously researched artist set - Claude Monet, Alfred Sisley, Camille
Pissarro, and Paul Cezanne - as fixed artist-level targets. Era and movement remain
recorded covariates and stratification variables, not interchangeable target labels.
The shared landscape/outdoor-place domain controls content. Claims are conditional on
these four artists unless a larger, prospectively sampled artist roster is added.

### 3. Balanced artist-by-source real corpus

Construct the sampling table before computing either feature. For every retained source:

- every artist must have independent training and held-out works;
- use the same planned counts per artist-by-source cell, or prespecify weighting before
  feature extraction;
- deduplicate at the physical-work level before splitting;
- keep all captures of one physical work in one split;
- require every held-source fold to contain every target artist and require its training
  complement to contain every target artist.

If the four artists cannot be populated across a common source intersection, acquire
additional sources or prospectively narrow the source roster. Do not retain structurally
empty cells and then average over them.

### 4. Input-domain, border, and codec controls

For every real capture, record native dimensions, file format, color profile, crop,
frame/mat/caption status, damage, and acquisition lineage. Two reviewers should inspect
borders independently, with adjudication before inclusion. `unknown` is ineligible for
the Lee primary analysis.

For Kim eligibility, require ratio `< 2` before square resizing. Because the article's
low-resolution prose and source's area test are not identical, record both rules and use
their intersection for the primary source-compatible domain. Freeze this choice before
feature extraction.

Break the codec confound with a crossed preprocessing experiment applied identically to
both origins:

- primary track: decoded RGB written to one lossless PNG intermediate before the VAE;
- sensitivity track: both real and generated images encoded with the same pinned JPEG
  library, quality, and subsampling before the VAE;
- source-replication track: original-extension behavior reported separately and never
  used as the sole real/generated comparison.

The codec track must be crossed with origin, never determined by origin.

### 5. Recover Lee's actual source behavior

Preregister a distributional collapse statistic for normalized `pi(d)` before examining
held-out results. Evaluate it over a fixed resolution grid on eligible real images, with
the same anti-aliasing and no upsampling. Validate the scalar `S` probes as a separate
unit test. The scientific gate requires both:

- the formula behavior; and
- the frozen full-distribution collapse criterion on held-out real images.

Report per-artist and per-source results as well as the aggregate. Every required
held-source fold must pass; a favorable pooled value cannot mask a failed fold.

### 6. Qualify the A-vector and PCA without generated-data feedback

Use the pinned, verified VAE, exact environment fingerprint, source-compatible input
path, and a preregistered deterministic posterior policy. Maintain the honest claim that
this is a repaired, method-compatible A-vector, not the authors' unpublished realization.

Fit centering and PCA only on real training primaries. Preserve the frozen 95% retained-
variance target in `pilot_2`, and permit enough components to reach it. The exact count
and basis are selected from training data, hashed, and frozen before held-out real or
generated features are transformed. If 95% cannot be reached within the preregistered
resource cap, the learned measurement fails and generation remains scientifically
closed. The justification is information preservation rather than artist prediction: the
smallest training-only basis that reaches 95% leaves at most 5% of training variance
outside the primary representation without tuning to a class label. Record training-only
reconstruction error and pairwise-distance distortion as diagnostics, not post hoc ways
to choose a more favorable component count. Every source-held-out analysis refits PCA
inside its training fold.

### 7. Independent reproduction study

Acquire independent digitizations with documented capture ancestry, not merely multiple
derivatives from one museum master. Balance reproduction works across artist and source.
Treat the physical work as the top-level unit regardless of the number of captures.

Choose the number of work pairs by simulation using the frozen margin and development
variance, targeting a preregistered precision for the upper confidence bound. Stop at the
planned count, not when the result passes. Apply the same crop, border, aspect, and codec
eligibility checks to both captures.

### 8. Paired artist-free generation controls

Each named-artist prompt must have an artist-free prompt with identical content wording
apart from the artist clause. Do not replace the artist with an era or movement. Block
and randomize calls by content, requested model label, and repetition. Preserve every
attempt, refusal, and output; do not select outputs visually.

Analyze the named-minus-artist-free contrast within each content block before any
between-artist contrast. Use enough prospectively chosen content blocks for content to be
an uncertainty level rather than relying on the two `pilot_1` scenes.

### 9. Instrument and gate the OAuth transport

Before study generation, freeze a clean commit of `~/dev/openai-oauth` and add a
redacted append-only transport trace. For every logical cell and every physical HTTP send,
record:

- proxy revision, launch arguments, upstream base URL and path;
- canonical outbound body hash and the requested model/size/quality/format;
- a unique client request ID propagated through the proxy;
- attempt number, timing, HTTP status, safe upstream request/trace headers, response
  schema hash, and a canonical metadata-body hash with image payloads omitted;
- returned format, actual dimensions, output hash, and any authoritative upstream model
  field.

Never log OAuth tokens or account secrets. Distinguish a logical retry from the adapter's
lower-level HTTP retries.

Run a non-study conformance suite before unsealing prompts. The scientific model-comparison
gate requires authoritative executed-model evidence for both requested labels. It also
requires either exact requested dimensions or a prospectively frozen actual-dimension
eligibility and harmonization policy with common support across both labels. If the
upstream service does not expose executed identity, `pilot_2` may still test the
engineering behavior of requested labels, but it must stop before a model-comparison
claim.

### 10. Hierarchical uncertainty and decision rule

The inferential hierarchy must match the data-generating process:

```text
fixed target artist
  -> source
    -> physical work
      -> independent capture

requested model label
  -> content block
    -> named vs artist-free prompt
      -> generation repetition / transport attempt
```

Use work-clustered uncertainty for real reliability and reproduction tests. For generated
contrasts, resample content blocks and successful generation units while preserving named
and artist-free pairing. Treat the four artists as fixed; do not claim population-wide
artist effects from four handpicked targets. Report per-artist, per-source, and per-model-
request-label intervals, not only a pooled mean.

## Pilot_2 opening gates

Scientific generation can open only if all of the following are true on new or sealed
real data:

- Lee's formula and preregistered full-distribution behavior are recovered;
- every Lee input has an accepted border/crop review;
- every Kim primary satisfies the frozen aspect and resolution domain;
- the crossed codec design shows that the primary result is not an origin-codec artifact;
- the PCA reaches the frozen 95% target using training data only;
- the reproduction upper bound is within the frozen margin for both measurements;
- the artist-by-source table is complete and every required held-source fold passes;
- the OAuth conformance trace verifies executed-model identity and the frozen dimension
  contract or harmonization policy.

Failure of any item produces another failure report and stops the scientific branch. It
does not authorize more prompts, more retries, a new threshold, or a different PCA rule
inside the same version.

## Current scientific non-claims

Until those gates pass, this project does not claim:

- that either feature is qualified for real/generated scientific comparison;
- that requested artist names caused artist-specific changes;
- that `gpt-image-1` and `gpt-image-2` were the models executed upstream;
- that either requested label is more faithful to an artist;
- that the results generalize beyond the four artists, selected genre, museum sources,
  or recorded processing environment.

The proper outcome of `pilot_1` is therefore **redesign**, with the completed API path
retained as engineering evidence and the scientific gate closed.
