# pilot_2 frozen protocol

## Status and registration boundary

This document defines the prospective generated-output phase of `pilot_2`. The real
reference images and `pilot_1` measurements were already observed, so the 40-work real
atlas is a fixed **development/calibration reference**, not an independent confirmation
sample. The confirmatory boundary begins only after this protocol, its code, configuration,
prompt manifest, corpus manifest, and transport snapshot are committed. No generated
`pilot_2` output may be inspected before that commit.

The pilot is scientifically complete when the registered grid has been resolved under the
retry rule, every successful byte stream has passed the common normalization contract, the
complete registered analysis has run, and the report records both supported and unsupported
hypotheses. Scientific completion is distinct from a favorable hypothesis result. A null or
negative result completes the pilot; it must not trigger threshold, prompt, exclusion, or
sample-size changes.

## Claim boundary

The experimental condition is the exact model-label string in a request sent through the
captured `~/dev/openai-oauth` implementation:

- `gpt-image-1`
- `gpt-image-2`

The proxy forwards those strings but returns no authoritative executed-model identity.
Accordingly, all results are described as outputs returned after requests bearing a given
label. `pilot_2` makes no executed-model identity claim and no `gpt-image-1` versus
`gpt-image-2` model-superiority claim. The two requested-label strata are evaluated
separately.

The request uses `size: auto` because the proxy systematically failed the explicit
`1024x1024` contract in `pilot_1`, and it uses the common `quality: low` testing condition
for all cells. Returned dimensions are measured outcomes. Eligibility
requires a decodable PNG, aspect ratio below 2, and area greater than `410 * 410`. All real
and generated inputs are then converted through the same deterministic sRGB, alpha-flattened,
metadata-free, lossless PNG path before feature-specific resizing.

## Artists and real-reference atlas

The target remains the artist, not the era or movement. The previously researched neighbor
pairs remain frozen:

- Claude Monet / Alfred Sisley
- Camille Pissarro / Paul Cezanne

Era and movement remain metadata only. The fixed reference atlas is selected from the
existing eligible AIC and NGA records. Within each artist-by-source cell, records are ordered
by `sha256("pilot2-v1|20260901|" + canonical_work_id)`. The first five are retained; the
first three are training references and the next two are held references. This yields exactly
40 physical works: 4 artists x 2 sources x 5 works, with 24 training and 16 held references.
Every cell is complete, and every retained image satisfies the released Kim-code area rule
and the paper/source aspect-ratio rule.

The inferential scope is the exact frozen digital-reference atlas. Robustness across
independent digitizations of physical paintings is not claimed. Existing CMA alternates do
not have adequate independent-capture ancestry and remain development evidence only.

## Measurements and qualification

### Primary: harmonized learned-formal vector

The primary feature is a deterministic, project-defined harmonization of the Kim et al.
Stable Diffusion 2.0 A-vector:

1. verify the pinned VAE and its previously recovered checkpoint equivalence;
2. decode every origin through the common lossless normalization path;
3. resize the normalized RGB image to 512 x 512 with pinned OpenCV `INTER_LANCZOS4`;
4. use the content-derived deterministic posterior-sampling seed;
5. flatten the 4 x 64 x 64 latent in C order after the 0.18215 scale;
6. fit PCA on the 24 real training works only;
7. retain the smallest component count reaching 95% variance, capped at `n_train - 1`;
8. hash the mean and basis before any generated output is inspected.

This is not claimed to reproduce the authors' unpublished RNG realization. The original-
extension JPEG round trip is not used in the primary comparison because it confounded real
JPEG inputs with generated PNG inputs in `pilot_1`.

The frozen calibration gate requires all of the following:

- exact 5/3/2 artist-by-source total/train/held cell coverage;
- all inputs pass the Kim area and aspect rules;
- finite 16,384-value vectors and exact deterministic repeat probes;
- train-only PCA reaches at least 95% variance within `n_train - 1` components;
- held artist balanced accuracy is greater than the four-class chance level of 0.25;
- a 9,999-draw artist-label permutation test constrained within source and split has
  one-sided `p <= 0.05`;
- the same pooled classifier, without refitting its PCA or artist centroids, has balanced
  accuracy greater than 0.25 separately on the eight AIC held works and the eight NGA held
  works.

Each per-source held score is based on only eight works and is therefore a coarse discrete
calibration check, not evidence of broad domain robustness. Opposite-source transfer scores,
obtained by fitting on one source and testing on the other, are retained as explicitly
non-gating development diagnostics because those refits do not match the pooled transform
used by the registered generated-output analysis.

Source-label predictability is reported, not used as a failure rule: exact crossing and
source-stratified reference estimates control the estimand, while the score diagnoses how
much acquisition source remains visible.

### Secondary: Lee chromatic seamlessness

Lee et al. define the adjacent-pixel CIE Lab distance distribution and seamlessness statistic

`S = (sigma_d - mean_d) / (sigma_d + mean_d)`.

Their Figure 1 shows mean-rescaled distribution collapse for two example paintings, not for
every painting in a corpus, and the paper supplies neither the project's earlier K-S margin
nor an artist-classification gate. `pilot_2` therefore retains formula tests, a fixed 500-pixel
long-side S value, and a Hellinger-embedded histogram of the mean-rescaled distribution as
secondary descriptive measurements. Chromatic results cannot open or close the generation
gate and do not enter learned-formal completion or hypothesis decisions. A zero-mean-distance
(uniform) image uses the registered deterministic limit `S = -1`, a unit mass in the first
normalized-histogram bin, and an explicit degenerate flag; it is not an extraction failure.
No other chromatic extraction absence is silently accepted: missing, hash-mismatched, or
non-RGB normalized inputs and software errors remain provenance failures that stop the pipeline.
Exact replication of the two Figure 1 images over 500--3000 pixels is outside this pilot's claim.

## Sample-size sensitivity and pilot scope

The top-level inferential sample size is eight content blocks; four repetitions stabilize each
block mean but do not turn the design into 32 independent top-level units. With eight blocks,
the exact sign-flip test has 256 assignments and minimum attainable `p = 1/256 = 0.00390625`.
Under the strict `p < 0.0125` sensitivity threshold implied by four equally small Holm tests,
the largest attainable passing value is `3/256 = 0.01171875`. Six or fewer blocks could not
make four equal minimum p-values pass strict familywise 0.05; seven is the mathematical minimum,
and eight retains one additional content cluster and a finer reference distribution.

Because the preceding generated pilot used a codec-confounded feature path, it does not provide
a defensible effect-size estimate for power. The pinned design artifact therefore reports an
assumption-labeled sensitivity, not an estimated minimum detectable effect: 100,000 draws per
point, seed 20260901, with independent standardized block means
`X_b ~ Normal(delta, 1)`. For standardized effects 0.50, 0.75, 1.00, 1.25, and 1.50, the
estimated probability of exact one-sided sign-flip `p < 0.0125` is respectively 0.13056,
0.28740, 0.49231, 0.69519, and 0.84778. This simulation omits the bootstrap-lower-bound and
source-sign requirements, so it is not a claim about the full decision rule.

The registered `8 x 4` design is consequently a resource-bounded feasibility pilot with useful
exact-test resolution, not a study asserted to have at least 80% power for modest effects. An
unsupported result must not be interpreted as proof that artist conditioning is absent.

## Frozen generated grid

There are eight content blocks. Each block contains four named-artist prompts and one
artist-free control with otherwise matched content. Every prompt is sent under both requested
labels with four repetitions:

`8 blocks x 5 prompts x 2 labels x 4 repetitions = 320 logical cells`.

The prompt manifest fixes the exact wording, identifiers, target annotations, and ordering.
Outputs are never selected by visual quality. A logical cell stops after its first successful
decodable response. Every physical send is retained. Identical retries are permitted only
for transport errors, HTTP 408/409/425/429, and HTTP 5xx under the frozen maximum-attempt
rule; prompt text, request label, and generation parameters remain unchanged. Content-policy
refusals, other HTTP 4xx responses, and malformed successful responses are terminal outcomes
and are never retried to select a more favorable image.

The execution schedule is also frozen. Logical cells are grouped into batches sharing content
block, requested label, and repetition; serial batch order and deterministic within-batch
submission/queue priority are determined by the registered SHA-256 schedule namespace and seed.
Batches execute serially, with at most four physical requests in flight. Thread scheduling and
network latency can reorder actual within-batch POST start or completion chronology; those facts
are retained in durable intent/attempt timestamps rather than misrepresented as a fixed physical
send order. The lexicographically first repetition-zero artist-free cell for each requested label
is preregistered as a transport-conformance check and marked in the schedule. When these cells
succeed, their outputs are the registered outputs for those cells rather than extra test images;
when either check terminates unsuccessfully, its terminal record still counts toward the fixed
grid and the remaining image sends do not begin.

Runtime revalidation is durable execution evidence, not an in-memory log. A check is appended
and `fsync`-persisted before conformance and before every scheduled batch, and a final check is
persisted after the invocation. Each record binds the frozen grid and schedule plus the exact
attempt-ledger prefix visible at that boundary. After interruption, generation resumes only
after validating the full append-only revalidation journal and attempt ledger; a new invocation
appends its own contiguous checks, and no new image request may precede its persisted boundary.
Immediately before each physical `POST`, the runner also appends and `fsync`-persists a unique
send-intent row binding the cell, attempt number, canonical request bytes, endpoint, and OAuth
fingerprint. Every durable attempt must match exactly one earlier intent. If interruption leaves
an intent without an observed exchange/attempt row, resume deterministically records that attempt
as terminal `indeterminate_after_interruption` because the physical request may have executed;
the runner never blindly resends it or selects a replacement output.
After an exchange is observed, the exact sanitized attempt row is atomically written and
`fsync`-persisted as a self-hashed receipt before its append to the attempt JSONL. Receipt creation
and append share the ledger lock; the receipt binds the exact attempt plus the pre-append ledger
row count and semantic prefix. Any unresolved receipt blocks later appends. On resume, recovery is
limited to exactly one missing attempt row backed by a receipt at the current ledger end, or one
torn final byte tail that uniquely prefix-matches that same immutable receipt. Existing valid rows and terminal
dispositions are never altered; ambiguous, non-final, or mismatched evidence fails closed, and
recovery never sends a replacement request. A canonical receipt manifest binds every receipt's
path, file hash, ledger prefix, and normalized attempt-payload hash, plus every recovered tail's
path, file hash, and byte count, without retaining raw response bytes.

## Primary estimands

For each requested-label, artist, content block, and repetition, the artist-free output is
paired with the named-artist output. Let `d(x, a)` be Euclidean distance in the frozen PCA
space from generated vector `x` to the held-reference centroid for artist `a`, and let `n(a)`
be the preregistered neighbor artist.

Target improvement is:

`Delta_target = d(control, a) - d(named, a)`.

Artist-versus-neighbor specificity improvement is:

`Delta_specificity = [d(named, n(a)) - d(named, a)]
                     - [d(control, n(a)) - d(control, a)]`.

Positive values mean the named request moves the returned output toward its target reference,
and toward that target relative to its paired neighbor, compared with the matched control.
The primary estimate averages artists equally, then repetitions within content block, then
the eight content blocks. Each requested-label stratum is estimated separately.

The same estimates are repeated with AIC-only and NGA-only held-reference centroids. Their
signs are required diagnostics for a supported primary result; pooled estimates cannot hide
a sign reversal by source.

## Uncertainty, multiplicity, and decisions

The registered bootstrap has 10,000 draws and a fixed seed. It resamples held real works
within artist-by-source cells, content blocks as the top generated sampling unit, and
repetitions within selected blocks while preserving each named/control pair. The preregistered
PCA basis remains fixed: inference is conditional on the frozen development atlas and its
training transform.

An exact one-sided sign-flip test uses the eight block-level means (`2^8 = 256` sign
assignments), under the registered block-level symmetry/exchangeability assumption. This is
not described as a randomized-assignment test because request conditions were not randomly
assigned. Holm adjustment controls the family of four primary tests: two requested-label
strata x two estimands. Familywise 95% lower bounds use the more conservative Bonferroni
one-sided level. Per-artist estimates are secondary.

A requested-label stratum supports the artist-conditioning hypothesis only when both primary
estimands have positive familywise lower bounds, Holm-adjusted `p < 0.05`, and positive AIC-
only and NGA-only estimates. A result that misses any criterion is reported as unsupported,
not retried or redesigned inside `pilot_2`.

## Stopping and mutation rules

- Generation count never increases in response to an observed effect or interval.
- No prompt, artist, neighbor, source, threshold, feature, PCA rule, exclusion, or retry
  identity changes after registration.
- Technical retries preserve exact request identity and all attempts.
- Missing cells, refusals, and decoding failures are reported under the intention-to-request
  ledger. They are never replaced by hand-selected outputs.
- Any estimand-changing correction after the prospective commit creates `pilot_3`.
