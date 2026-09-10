# Computational measurement challenges and common-view sensitivity — v1.0

Issued 2026-09-10 before this successor's image reads, transformations or feature
extraction. Namespace: `painter_measurement_validation_v1`; default run:
`pmvv1-20260910`. The user authorized real measurement validation, replication and
public reproducibility while retaining the preference for no human ratings. This
protocol implements the computational-validation portion only. Its design and
review are maintainer-run LLM work, not neutral external peer review.

## Scientific scope and immutable predecessors

The source paintings and prior numeric results are already exposed. This is a
prospectively fixed computational challenge on those retained images, not a new
unexposed reference sample or confirmation of painter-style reproduction. Known
transformations provide computational ground truth; there are no human aesthetic,
scene-adherence or painter-recognition judgments. No learned evaluator is added.

The canonical `studies/painter_feature_generation_v1/PROTOCOL_2.1.md` remains
unchanged. Its independent-capture qualification and equivalence gates are not
claimed to pass. This successor authorizes only the exact retained-image reads
listed below after its source and metadata freeze are committed. It authorizes
no collection, transport, new reference admission, retry, model invocation or
alteration of a terminal predecessor. Existing raw images, ledgers, protocols,
scalers and feature implementations retain their original paths and bytes.

Earlier 1% crop/496-pixel, resolution256, JPEG90 and synthetic-inference results
already exist. The new evidence here is the paired comparison of fixed known
changes with processing challenges on real paintings, the full cross-family
response matrix, and the common-square computation across the controlled cohort.
These results cannot establish invariance to unknown photographic workflows.

## Fixed input population and stage gates

Use all 70 Study 1 reference works (38 Monet, 32 Cézanne) from
`data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/reference_panel.jsonl`.
Use every one of the 1,006 generated images in the `primary512` rows of
`pdsv1-main-immediate-20260907/generated_features.jsonl`, including the selected
retry outcomes exactly as originally analyzed. The reference primary features
are in `pdsv1-main-parallel-20260906/reference_features.jsonl`. The five retained
generation-component ledgers identify each selected compressed response and
image hash. No content, quality, geometry or feature-based filtering is added.

The metadata-only `prepare` command:

1. Requires the protocol, all new source/tests, unchanged imported scientific
   dependencies, compact input evidence, `pyproject.toml` and `uv.lock` to equal
   committed HEAD and be clean in both index and working tree.
2. Reads only compact metadata/numeric records, reproduces all eight original
   inferential endpoint objects exactly, and resolves a unique 1,076-image
   inventory. It does not open, hash or inspect raw image/response bytes.
3. Creates `images.jsonl` with exact source paths, stored raw/response hashes,
   normalized-array hashes and image/work/request identities. The expected raw
   hashes are copied from bound predecessor evidence, not refreshed.
4. Creates `freeze.json` binding source/input hashes, the image-manifest hash,
   exact configuration, seeds, source commit and active environment (Python,
   NumPy, Pillow, SciPy, scikit-image and PyWavelets versions).

Commit both new manifests before invoking `run`. The runner re-verifies the
committed freeze, all bindings, source cleanliness, exact active package versions
and metadata-derived inventory,
and replays the old primary inference before any raw pixels are read. A persistent
create-once `started.json` then opens this run. Any error/interruption closes the
run permanently; partial records and a failure receipt remain. A correction needs
a disjoint run ID and a new prospective freeze, never silent continuation.

The runner verifies retained container, decoded-response and image hashes before
measurement, and requires the original normalization array hash to reproduce.
The extractor remains the unchanged
`painter_feature_generation_v2/features.py`; the primary 221-work development
scaler remains unchanged. There is no refitting, feature removal or weight tuning.

## Exactly ten reference conditions

For each reference, perform the original ICC-aware, aspect-preserving short-side
512 normalization. Then take the central 512×512 window, with top/left indices
`floor((dimension - 512)/2)`. Record coordinates and retained area. Do not resize
or normalize this square again. This common window is the challenge baseline,
not the original full-view primary measurement.

| ID | Transformation from the common baseline |
| --- | --- |
| baseline | Identity copy of the 512×512 RGB array |
| png | Lossless RGB PNG round trip |
| jpeg95 | Pillow JPEG quality 95, 4:4:4 (`subsampling=0`), no optimization/progression |
| jpeg75 | Same encoder/settings at quality 75 |
| resample384 | 8-bit Pillow Lanczos 512→384→512, quantized at each stored-image step |
| chroma80 | D65/2° Lab: multiply a and b by 0.8, preserve L; convert back to sRGB |
| chroma60 | Same operation with factor 0.6 |
| blur1 | Gaussian filter in linear RGB, σ=1 pixel, reflect boundary, truncate=4 |
| blur2 | Same operation with σ=2 pixels |
| tiles4 | Permute sixteen 128×128 tiles with NumPy seed 2026091001 |

Use the same seeded tile permutation for every work. Tile shuffling must preserve
the joint RGB pixel multiset exactly. PNG pixels and all 31 features must equal
the baseline exactly (zero tolerance); otherwise terminate. RGB conversions use
explicit clipping, with clipped-channel/pixel fractions retained for chroma
contraction. Preserve every derived-array hash and 31-vector. Chroma contraction
partly checks the chroma feature's own definition: retain signed median-chroma
changes, realized ratios, requested factors and clipping, without pretending this
is independent painter-style validation. No monotonic response of all features
is required. Tile edges can change neighboring-color distances, so preservation
of the pixel multiset does not imply invariance of the entire color family.

These conditions give 700 reference vectors. The reference baseline vectors are
reused by the geometry analysis; they are not separately counted observations.

## Fixed computational comparisons

For work i, family F and condition T, compute RMS standardized displacement:

`D(i,F,T) = sqrt(mean_j_in_F(((f_j(T(x_i)) - f_j(x_i)) / old_IQR_j)^2))`.

Do not center/refit per condition. Every feature family retains its complete
coordinate set (11 color, 8 spatial, 12 texture). Report all ten conditions across
all three families, per work, per painter, and as equal-painter mean summaries.
The displayed equal-painter median summary is explicitly the average of the two
painter medians, not a pooled weighted quantile.

The three principal paired responses are:

- Color: D(chroma80) minus max(D(jpeg95), D(resample384)).
- Spatial: D(tiles4) minus that same within-work, within-family processing maximum.
- Texture: D(blur1) minus that same processing maximum.

Call these **known-change versus processing-challenge comparisons**. Processing
changes are not assumed perceptually irrelevant. Negative or weak comparisons
are substantive outcomes; do not change doses or choose features to force success.
JPEG75 is a stronger processing stress, not part of the principal maximum.
Report paired chroma60−chroma80 and blur2−blur1 displacement differences and the
fraction increasing, with no new tests or all-coordinate monotonicity requirement.

Use all 70 physical works as the sampling units. Draw 9,999 bootstrap samples
with NumPy seed 2026091002, resampling whole works with replacement separately
within each painter at its actual count. Preserve all three responses together
for a sampled work. Average the two painter means with weights 1/2 each.
Report percentile intervals at quantiles 0.05/6 and 1−0.05/6: nominal 98.3333%
per comparison, using the Bonferroni-three convention. These are descriptive,
conditional-on-exposed-panel resampling intervals, without guaranteed population
coverage. Zero bootstrap variance yields no interval. Derivatives never increase
n. There is no perceptual pass margin, equivalence margin or qualification gate.

## Complete common-square geometry sensitivity

Apply the same post-normalization central square to all 1,006 primary generated
images. Extract each square once, with the unchanged 31-feature implementation
and primary scaler. There are 1,706 unique extracted vectors in total.

Recompute all eight original paired energy-discrepancy endpoints through the
unchanged Study 1 `analysis.paired` and inference functions, including the exact
conditions, brief/repetition pairing, content weights, excluded pairs, minimum
support rules, 99,999 randomization draws, original seeds and Holm family of eight.
Verify pair counts and missing-pair records against the original endpoint objects.
Report full-view versus square estimates, estimate changes, raw/Holm p-values,
per-image family displacement and retained area, with service/painter summaries.

The recalculated tests are sensitivity outputs under the existing conditional
null, not new confirmation or replacement primary results. Square views remove
the gross aspect-ratio difference but also alter visible content. Persistence or
change cannot identify photographic effects, painter mechanism or perceptual
style fidelity. Preserve the original full-view endpoints without modification.

## Outputs, resources and review

Compact freezes, feature vectors, analyses and receipts live under
`data/manifests/painter_measurement_validation_v1/<run_id>/`; source pixels are
read in place. New decode temporaries, run markers and failure records remain
under the ignored `research_workspace/painter_measurement_validation_v1/<run_id>/`.
One sequential writer processes one image at a time. No GPU, new learned weights,
network calls or additional OpenRouter spending are required. No wall-time result
or performance guarantee is assumed before execution.

`report` creates a readable report, complete family/geometry/dose tables, and two
scientific figure pairs (PDF/PNG) from compact output records. `check` verifies
input/output hashes and repeats the numerical analysis without reopening pixels.
Existing figures or reports are never overwritten. Report honest negative results
and full cross-family responses; do not retain only favorable conditions.

Offline tests use only artificial arrays and temporary files. They cover exact
PNG/tile invariants, chroma direction, blur and resampling, cropping order,
whole-work bootstrap dependence, manifest/source gates, cohort completeness,
and unchanged pairing/inference. They do not read retained image bytes.

Processing challenges are motivated by primary evidence that resampling and
encoding choices can materially affect generative-image evaluation:
[Parmar, Zhang and Zhu, arXiv v1](https://arxiv.org/html/2104.11222v1).
That evidence motivates measuring this extractor's behavior; it does not supply
validation results for these particular 31 features.

## Execution handoff

After source/protocol/tests are committed:

```bash
uv run --locked python -m latent_art_bench.painter_measurement_validation_v1 prepare
```

Review and commit the exact generated `freeze.json` and `images.jsonl`, then:

```bash
uv run --locked python -m latent_art_bench.painter_measurement_validation_v1 verify
uv run --locked python -m latent_art_bench.painter_measurement_validation_v1 run
uv run --locked python -m latent_art_bench.painter_measurement_validation_v1 check
uv run --locked python -m latent_art_bench.painter_measurement_validation_v1 report
```

An optional `--run-id` names a disjoint successor; it never resumes an earlier run.
