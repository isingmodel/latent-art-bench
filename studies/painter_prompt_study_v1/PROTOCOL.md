# Painter Prompt Study v1 — repeated generation and prompt comparisons

Protocol ID: `painter-prompt-study-v1/1.0`. Prepared 2026-09-05 in response to the maintainer's
explicit goal of paper-ready generated-image feature-distance analysis, additional GPT image
generation, and alternative prompt methods. **Prospective execution contract; no new
generation is authorized by this document alone.** The complete request count, storage and runtime
resources must be selected and explicitly authorized before a clean-input generation freeze.

## 1. Scientific question and scope

How do image-generation prompt strategies change the distance between generated-image feature
distributions and the recorded paintings of Monet, Sisley, Pissarro and Cézanne? The primary
question concerns **differences in distance**, not an equivalence/reproduction label. It permits
negative, null and inconsistent prompt effects. No outcome may change the metric, reference,
prompt construction, sample count, or comparison inventory after new generation begins.

The reference is the existing finite population of 649 successfully measured confirmation
paintings in `pfg2-method-20260905`. These reference data and earlier generated results are already
exposed. This is prospective new generation against a fixed exposed reference, not a new blinded
confirmation sample or an oeuvre-wide probability sample. The 160 old OAuth outputs and 2,000
old SD-Turbo outputs remain separate historical descriptive evidence; none is inserted into a
new repetition or used to tune prompts/calibration.

The targets are the two requested aliases `gpt-image-1` and `gpt-image-2` on the dated local OAuth
service route. The route does not attest underlying model snapshots. A paper must identify this
limitation and cannot infer that the two aliases necessarily represent independently verified
model weights. Source inspection and request/response provenance describe the tested service.

## 2. Prospective prompt interventions

Use all 16 exact original scene templates, without selecting subjects or changing the stated
scene. Each method has four named-painter conditions and one matched artist-free condition:

1. **by_name:** preserve every original named and artist-free prompt byte-for-byte.
2. **style_instruction:** start with the unchanged artist-free scene sentence and append an
   explicit instruction to render the scene in the painting style of the named artist. The
   free counterpart requests a coherent painting style without naming an artist.
3. **style_aspects:** retain the second method and add the identical named/free instruction to
   attend to color relationships, organization of forms and handling of painted marks, while
   retaining the stated scene. Do not specify artist-specific stereotypes or target feature values.

`prompts.py` defines the literal suffixes. The frozen `prompts.json` records every exact string,
source hash and construction rule. There are 240 distinct prompts per alias/repetition, including
all 15 method/condition cells. With two aliases, each complete repetition contains 480 requests.
No reference painting is supplied as an image input in this text-prompt design.

The primary planned transitions are `style_instruction − by_name` and
`style_aspects − style_instruction`, in energy distance to the same painter's reference. Negative
effects favor the later method. There are 48 primary endpoints: two aliases × four painters ×
three feature families × two transitions. The comparison `style_aspects − by_name` is secondary.

Matched-control difference-in-differences uses the same transitions after subtracting each
method's own artist-free distance to that reference. This accounts descriptively for the generic
effect of the added instruction. Its 48 endpoints form a distinct secondary inventory; their
inferential qualification is not assumed merely because the primary inventory calibrates.

## 3. Bounded sample and randomized prompt assignment

The user subsequently required that the experiment not generate too many images. The active
small-study choices are 1, 2 or 4 complete repetitions: 480, 960 or 1,920 requests in total,
respectively 16, 32 or 64 images per alias/method/condition. Select and authorize one fixed count
before the first request; do not adapt it to outcomes. These are bounded exploratory experiments; no count
is claimed to guarantee narrow uncertainty, high power, equivalence or publication.

For each alias × condition × scene × repetition, define three consecutive request positions.
Assign the three prompt methods to these positions using an independent uniform permutation.
Randomize scene/condition order within each repetition and alias order within each scene/condition.
Use a single PCG64 allocation seed drawn from system randomness before any new generation;
record it in the committed config. Draw and record a separate permutation-test seed. Neither
seed is searched or reused to select favorable empirical results. Record the assignment unit,
method position, alias position and overall request sequence. Do not impose cross-repetition
reversal or other linked treatment assignments in this small-study mode. No model latent seed
is sent or claimed to be shared.

For each adjacent-method contrast, condition on the third method's allocated position and the
alias/scene allocation. Within each of the `16 × R` remaining position pairs, the two tested
methods have equal random assignment probabilities. The two-sided randomization statistic is
`finite_energy(real, later) − finite_energy(real, earlier)`, using equal template weights and
all generated images in the cell. Its observed sign describes which empirical distribution has
smaller measured distance.

The randomization null is the sharp absence of a prompt-method effect on these fixed request
positions, with no interference between requests, or under a justified joint invariance
under the allowed within-scene swaps. It is **not** merely equality of two population energy
distances. Random allocation permits arbitrary fixed scene/position drift under the sharp null;
it does not eliminate treatment-dependent timing, service changes induced by prior requests,
carryover, hidden conversation state or other interference. The local process check does not
attest remote model weights or prove these statistical assumptions.

Each test conditions on its own third-method positions and enumerates all `2^16` pair swaps for
one repetition. At two or four repetitions, draw 99,999 independent uniform pair-swap vectors
with replacement and include the observed assignment. Count ties inclusively and use
`(1 + extreme_random_draws) / 100000`; never report a zero p-value. A fixed endpoint-specific
seed derives from the independent frozen permutation seed. Apply Holm's step-down adjustment
across all 48 primary two-sided p-values at family alpha 0.05. Report raw and adjusted p-values,
Monte Carlo draw count or exact enumeration size, and the test assumptions for every endpoint.
Do not repeat a randomization analysis with different seeds to seek significance.

The finite V-energy contrast can be evaluated exactly through paired coefficients. If `A_i`
and `B_i` are earlier/later outputs, let `r(X)` be mean distance to the fixed real reference and
`s(X)` the sum of distances to the pooled `A ∪ B` set. With `n=16R`, define
`c_i = 2(r(B_i)−r(A_i))/n − (s(B_i)−s(A_i))/n²`.
The observed contrast is `sum(c_i)` and any permitted label swap changes only the corresponding
coefficient signs. Tests must verify this identity against brute-force energy recomputation.

These randomization tests provide no confidence interval for a population energy-distance
contrast. Absolute distances, complete wrong-painter matrices, coordinate shifts/IQR ratios,
matched-control difference-in-differences, overall nonadjacent prompt effects and scene/order
sensitivity are descriptive. In particular, a small adjusted p-value rejects the stronger null
under the assumptions; it does not alone prove that the later prompt is closer in the population.
No image, scene or painter is excluded based on its observed result.

## 4. Prospective qualification and retained development

The active randomization implementation is checked with algebraic/brute-force oracles, exact
small permutation groups, tie/degeneracy cases and known Holm examples. Synthetic qualification
uses complete 48-endpoint null inventories at 16, 32 and 64 matched positions, both coupled and
independent endpoint constructions, fixed magnitude drift and rare outliers. Development and
unseen validation use seeds 20260908 and 20260909, each with 2,000 trials per cell. The criterion
is fixed before these outputs: every prescribed valid-null validation cell must have a Wilson
95% Monte Carlo upper bound on family-wise false rejection at most 0.065. Deliberately invalid
interference cases are reported separately and cannot qualify the method.

For computational tractability, the contribution-space calibration can use exact conditional
weighted-sign tail probabilities and exact Binomial Monte Carlo exceedance sampling, with the
same plus-one p-value rule. This is a construction-specific shortcut, not a claim that the
full image-generation pipeline was simulated. Actual permutation-engine tests remain separate.
No empirical painting or generated-image outcomes are used to tune seeds, prompts, sample size,
metrics or inferential rules. The theoretical justification depends on the declared allocation
and null assumptions; a successful simulation cannot establish those assumptions for a service.

Earlier synthetic exploration of disjoint-repetition paired-t and jackknife intervals is retained
as development history. The large grids considered there were superseded by the user's image
budget constraint before any new generation. Those interval qualifications do not transfer to
this small-study analysis, and their power table is not a power claim for randomization tests.
No failed candidate, invalid case or incomplete endpoint may be hidden.

Method references: [Hemerik and Goeman, exact testing with random permutations](https://doi.org/10.1007/s11749-017-0571-1)
for the identity-plus-random-transform p-value, and
[their distinction between randomization and permutation inference](https://arxiv.org/abs/1912.02633).
These support the testing principles; they do not validate this service or establish image counts.

## 5. Generation and preservation

Use the inspected `127.0.0.1:10532` local proxy, its normal credential handling, and the exact
frozen source hashes including routing/shared transport code. The research client does not read,
copy or print credentials. No public paid-API fallback or use of the stale port-10531 instance.
Request `n=1`, `1024x1024`, medium quality, PNG and opaque background, preserving the previous
requested settings. Actual returned settings are measured and reported separately.

Serial execution retains at least 15 seconds between starts, a 240-second per-I/O timeout, a 64-MiB
response ceiling and a 5-GiB disk reserve, plus the approved runtime-byte cap. The full design
receives storage preflight before freezing. Historical throughput/size estimates are planning
evidence, not guaranteed provider speed, quota or response size. Provider quota remains unknown
until observed; this authorization does not imply unlimited account usage.

Bind the inspected listening process identity and start time, and verify the process and proxy
source before each dispatch. A process replacement is a stop for operator review, not permission
to route to another server. Per-I/O timeouts are not a total request wall-clock deadline.

Before each dispatch, fsync an exact request-intent event. Retain every loopback response body, including
partial bodies and failed requests, in a lossless gzip store under the new ignored workspace.
Bind both stored and decompressed body hashes. Decode only to validate format/short side and
record the returned image hash; do not store a redundant durable decoded copy. Measurement
later derives temporary decoded bytes from the retained response. Record status, timing,
allowlisted headers, usage, requested/returned differences and available model identifiers.
These are the bytes received from the local proxy; its upstream transport may already have
decoded HTTP content encoding. The record does not claim to retain original provider wire bytes.

Accept exactly one fully decodable allowed-format image with short side at least 512; this
service-output acceptance does not claim that requested settings were honored. No URL following,
redirect, aesthetic selection, reference-image replacement, retry or reroll. Keep duplicates,
off-topic outputs, refusals and measurement failures in their original slots.

Batch pauses occur only at request boundaries and leave the run nonterminal. Resumption dispatches
only never-attempted rows in the same fixed order. Disk reserve/runtime-cap pauses send nothing.
Each resume verifies all retained response bytes; full-repetition batches avoid excessive repeated
I/O from tiny batches. This verification has a cost and is included in operational scheduling.
Authentication/quota failure or an unresolved crash intent closes the run permanently, records
all remaining requests as unattempted, and never retries the uncertain request. A terminal run
is never resumed, topped up or spliced into a successor. Any deliberate retry requires a new
complete disjoint design and explicit predecessor binding.

Primary prompt inference requires complete measured randomized grids for the declared inventory.
Incomplete generation or measurement produces full availability/missingness accounting and an
explicit unavailable primary result; it never silently deletes inconvenient blocks or templates.

## 6. Measurement, analysis and reporting

Reuse the original 512-short-side normalization, all 31 feature definitions and the frozen
equal-painter median/IQR scaler fitted on 221 new-development paintings. No refitting and no
new real-image extraction. Normalize/extract each newly generated image once after terminal
generation, with an append-only ledger and one retained disposition per request. Temporary
decoded files are removed only after their original response bytes remain safely retained.

The final report must include request and feature availability by alias/method/template/painter,
finite target and wrong-painter distances, all 31 coordinate diagnostics, primary prompt contrasts,
matched-control contrasts, synthetic validation and precision assumptions, complete request order,
time/geometry/profile diagnostics, exact/perceptual duplicate screens, and links to reproducible
tables/code/provenance. Perceptual screens are not proof of originality or absent training overlap.

All original v1/v2 protocols, bytes, ledgers and reports stay unchanged. New compact evidence uses
`data/manifests/painter_prompt_study_v1/`; runtime responses use the single ignored boundary
`research_workspace/painter_prompt_study_v1/`. Frozen inputs are clean and committed before
publication and record `recorded_git_commit`. Reviews are maintainer-run LLM subagents, not
institutionally independent review. Paper-ready is a quality objective, not guaranteed publication
or license to conceal failed calibration, model identity, corpus provenance or availability limits.
