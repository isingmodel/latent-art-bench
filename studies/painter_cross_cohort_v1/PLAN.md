# Separate-collection common-response audit v1

Written 21 September 2026, before computing this diagnostic on the selected
SD-Turbo feature arrays. This is an explicitly retrospective analysis of an
existing, previously analyzed cohort. It is not a prospective replication or
an untouched holdout. Old energy-distance, coordinate and copy diagnostics were
already reported; the present common/centered decomposition was not found in
those analyses during the metadata inventory.

## Question and selection

Does the common majority of additional naming change also occur in the complete
retained SD-Turbo collection, which uses a different generator, prompt wording
and request mechanism from the six-configuration main experiment?

Use all 2,000 outputs from `pfg2-sd-turbo-20260905`: 25 blocks, 16 scenes and five
conditions (four named painters plus artist-free). The artist-free prompt is
already generic oil painting: `An oil painting on canvas of ...`. A named prompt
inserts only ` by [painter]` after `canvas`. There is no shared-family prompt.
Keep Monet, Sisley, Pissarro and Cezanne, every scene, every block and every
coordinate. The cohort was selected by its complete four-painter census and
compatible retained measurements, not by the new diagnostic's outcomes.

The main experiment remains unchanged and separate. No pooling, new image,
checkpoint download, model rerun or paid request is allowed in this audit.

## Input provenance and chronology

Bind this plan, implementation, tests, the original generation freeze, request
and output ledgers, generated-feature receipt/file, original prompt library,
historical method freeze and fixed development-only scaler before execution.
Verify the complete cell census, all input identities and raw-pixel hashes;
check non-overlap with the main experiment by retained original-image hashes.
Use the same original full-frame 649-reference target and 221-work scaler as
the main 31-feature analysis. Verify exact painter membership, feature order
and normalization contract rather than trusting matching dimensions.

SD-Turbo is frozen at revision
`b261bac6fd2cf515557d5d0707481eafa0485ec2`, fp16/MPS, 512-square output,
one denoising step and guidance scale zero. The negative prompt is null.
The same seed is intentionally used across the five arms within a scene/block.
There are 400 distinct HMAC-derived scene/block seeds. Preserve that pairing:
arms are not independent sampling units. The 25 block vectors are the repeat
units. Stable deterministic generation and distinct pseudo-random seed streams
motivate, but do not prove, the independent-block expectation calculations.
This cannot estimate dependence in the closed services used by the main study.

## Fixed quantities

Let z[b,s,a] be the standardized 31-vector, where b indexes 25 blocks, s indexes
16 scenes, a=0 is generic oil painting and a=1..4 are the four painter names.
Apply only the retained development center and IQR scale; no new fitting.

For any block-indexed vectors v[b], define the cross-block product

    U(v) = (||sum_b v[b]||^2 - sum_b ||v[b]||^2) / (K*(K-1)).

It averages every ordered pair of distinct blocks. Under stable independent
block errors, its expectation is the squared norm of the conditional mean.
The computation allows correlated artist arms within each block. Retain signed
estimates; do not clip them into squared norms or probabilities.

First average each condition over all 16 scenes within a block. Define
delta[b,a] = mean_s(z[b,s,a] - z[b,s,0]), c[b] = mean_a(delta[b,a]), and
d[b,a] = delta[b,a] - c[b]. The prespecified all-coordinate summaries are:

- C = 4 U(c): common naming change beyond generic painting.
- L = sum_a U(d[a]): centered, between-name change.
- N = sum_a U(delta[a]): total naming change; verify N = C + L.
- T = C - L: signed common-majority contrast.
- C/N only when N > 0, retaining values outside [0,1] if they occur.

The descriptive cross-cohort check supports common majority in this setting
only if N > 0 and T > 0. These are descriptive conditions, not significance
tests. Report failure or nonpositive denominator as prominently as success.
They do not establish that a common response is unwanted or non-stylistic.

Repeat the same decomposition within scenes, then average the 16 scalar
components. Report it separately; do not substitute it for the scene-averaged
primary. Repeat all summaries within each of the three fixed coordinate
families (11 color, 8 spatial, 12 texture) as mandatory sensitivities. Do not
select a favorable family or redefine the primary.

## Alignment and error context

Let r[a] be the centered original historical painter means and
H=sum_a ||r[a]||^2. Report beta=sum_a <mean_b d[b,a],r[a]>/H, pooled
D=sum_a U(d[a]-r[a])/H, and scene-wise D obtained before averaging scenes.
Verify pooled D = sum_a U(d[a])/H - 2 beta + 1. Retain the signed difference
between scene-wise and pooled D without clipping. Zero H makes normalized
quantities unavailable with an explicit reason, not zero.

For all six unordered painter pairs, report aligned amplitude and cross-block
scene-error normalized by the corresponding squared historical pair distance.
Precisely, for pair (a,j), let q=mu[a]-mu[j] in the selected coordinates and
g[b,s]=z[b,s,a]-z[b,s,j]. Report beta_pair=<mean_bs(g),q>/||q||^2 and
D_pair_scene=mean_s(U_b(g[b,s]-q))/||q||^2. Do not add a pooled pair-error
endpoint. Each coordinate family uses its own H and pair denominator; a zero
denominator makes its normalized endpoints unavailable with an explicit reason.
These are descriptive context, not six new hypothesis tests. Do not interpret
positive alignment or smaller error as artistic fidelity.

## Stability and reporting

Delete each of the 25 blocks once and recompute C, L, N, T, C/N, beta and both
D values. Save all 25 results and their finite ranges; these are sensitivity
ranges, not confidence intervals. No p-values, independent-investigator claims
or unseen-scene generalization are permitted. The same fixed four painters and
historical references limit external reach, despite separate generated images.
Each deletion uses K=24. Historical reference membership, means, coordinate
scales and denominators remain fixed; none is refitted or resampled.

Report every frozen endpoint, including adverse and undefined results. Include
the exact prompt difference, seed pairing, configuration, prior outcome
exposure, membership counts, pixel/source hashes and numerical replay command.
Use a new create-once input/result namespace; never rewrite completed evidence.

## Qualification before real execution

Constructed tests must cover ordered-pair U equivalence, K=2 agreement with
the original two-repeat formula, paired-arm dependence, N=C+L, the D identity,
known common-only and contrast-only responses, negative finite estimates,
denominator failures, coordinate-family selection, all six pair identities,
25 deletion records, and rejection of incomplete/duplicate or foreign cells.
An independent design/code audit must finish before real outcomes are run.
