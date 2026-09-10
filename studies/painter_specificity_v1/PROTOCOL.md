# Painter specificity beyond a shared painting effect

Version 1, 2026-09-10. New prospective experiment, authorized by the user.
All preceding studies and failed/closed cohorts remain unchanged. No protected
external holdout is opened. Retained reference data are an already exposed,
finite comparison panel, not new confirmation data.

## Question and contribution

Does artist naming recover the differences among Monet, Sisley, Pissarro and
Cezanne found in painting reproductions, beyond a common painting response?
Prior work already measures artist recognition, prototype similarity and
stereotyping. The proposed contribution is a controlled generic-painting contrast
plus repeat-corrected recovery of reference artist geometry, with comparable
model estimates and explicit alternatives to an artist-specific explanation.
The study tests observable consequences, not training-data or internal mechanisms.

## Fixed allocation

Six models: GPT Image 1, GPT Image 2, GPT Image 2.5 Flare, GPT Image 2.5 Sunburst,
Nano Banana 2 and FLUX.2 Max. Exact request IDs and rendering payloads are in
`requests.jsonl`. All use text only, one output, requested square approximately
1K resolution; OpenAI requests use medium quality. Delivered geometry and quality
are retained. Comparisons concern these model/configuration combinations.

Six clauses on each of 16 authored outdoor scenes: artist-free; generic oil
painting; oil painting in each of the four artists' styles. Two independently
requested repeats per cell: 1,152 new images, 192 per model. The scenes comprise
four water, four built, four land and four mixed compositions. They are fixed
briefs, not a probability sample of all possible scenes. No feature-driven scene
selection or pilot-image inclusion. Randomize all model/arm/repeat requests
within each scene and randomize scene order, seed 2026091017. Run at most three
concurrent requests, starts at least five seconds apart.

Sixteen scene clusters permit paired comparisons and explicit leave-scene-out
sensitivity. Two repeats support cross-product noise correction, not precise
per-cell variance estimation. This is a bounded comparative experiment, not a
power claim or proof of equivalence. Do not enlarge the sample after results.

## Reference and measurement

Reuse all 649 already measured reference works: Monet 297, Sisley 106, Pissarro
141, Cezanne 105. Reuse the separate 221-work equal-painter median/IQR scaler.
Use the unchanged 31-feature extractor with 512-pixel short side, sRGB conversion
and aspect preservation. New vectors never replace historical vectors.

Primary inference uses the complete 31-feature representation. Repeat the
estimates separately by color (11), spatial structure (8), texture (12), and
without texture (19); these are descriptive sensitivity analyses. Also remeasure a central 512-square window after normalization for every
new output and all 649 retained references, using the unchanged scaler. Recompute
all model comparisons as descriptive geometry sensitivity. This removes aspect
ratio differences in the measurement window but also removes peripheral content.
Existing color-intervention and resolution experiments are supporting
measurement evidence. They do not validate perceptual style or capture fidelity.

Let r_a be each reference artist's standardized mean minus the equally weighted
mean of the four reference means. Let H=sum_a ||r_a||^2. Each artist has equal
weight regardless of reference sample size. Reference means and scaler are fixed
for primary inference; stratified reference-work resampling is a secondary
sensitivity to this finite reference panel (1,000 stratified draws; seed 2026091019). No new real-painting acquisition.

## Primary outcomes and regression comparisons

For model m, scene s and repeat k, center the four named vectors over artist:
d_msak = z_msak - mean_b(z_msbk). This removes every common model/scene shift.

1. Reference-aligned response beta_ms = sum_a <mean_k d_msak,r_a>/H.
   Mean over scenes equals the least-squares slope of centered generated
   features on the reference artist contrasts, with model-specific slopes and
   scene/model/feature intercepts removed by centering. beta=0 means no aligned
   response, beta=1 matches its amplitude; larger is not necessarily better.
2. Repeat-corrected distortion D_ms = sum_a
   <d_msa1-r_a,d_msa2-r_a>/H. Independent output repeats remove the additive
   sampling-noise bias of squared error. Its expectation is scene-conditional
   mean-geometry error; an estimate can be negative. D=1 is the expected value
   for a purely shared response, D=0 for exact reference contrast recovery.
   This is mean-geometry recovery, not equality of full artist distributions.

Fit D_ms = scene_s + model_m + error_ms (equal weights). Report all 15 paired
model differences and the six mean beta values. Use scene-level standard errors
and t(n-1) intervals (15 degrees of freedom on the full panel); Bonferroni coverage for the fixed family of 21 contrasts
(alpha .05). These are approximate scene-variation intervals for fixed authored
briefs, not claims about arbitrary scene populations. Supply nominal 95% intervals
alongside simultaneous intervals, all 16 leave-one-scene estimates and paired
scene bootstrap sensitivity (5,000 draws, seed 2026091018). Rank models only on
D and label differences unresolved if the simultaneous interval contains zero.
No universal quality winner follows from a single feature target.

## Explanatory diagnostics

- For named-versus-free mean shifts h_ma, decompose h_ma=c_m+d_ma. Compare c_m
  with the generic-minus-free shift. Report their norms, cosine and residual,
  and shared/specific squared magnitudes with cross-repeat noise correction.
  Compare with the reference geometry: a large common component alone is not
  evidence of failed specificity among four related artists.
- Separate scene-conditioned artist contrast recovery from cross-scene average
  recovery. Their difference identifies scene-dependent artist responses in
  these measurements, not a hidden neural representation.
- Report each model/artist's generated-reference V-energy and observed trace
  ratio, named versus generic energy, and within-scene repeat variation. A model
  may recover artist contrasts yet fail to recover within-artist diversity.
- Decompose distortion exactly into aligned-amplitude error and orthogonal
  error using the two repeat-specific projection slopes. This distinguishes
  weak/strong aligned responses from painter differences in the wrong direction.
- Feature-family decomposition identifies which measured properties account for
  distortion. Existing controlled palette and moment-map evidence supplies
  complementary proxy explanations; preserve its contrary prospective result.
- Reference-only PCA displays all four reference and generated distributions;
  held-scene artist recognition is optional exploratory analysis, never the
  primary novelty or a substitute for reference geometry recovery.

## Collection, cost and missingness

The reconciled conservative historical total is $67.5219185, including the
unchanged $5 historical uncertainty reserve. Total project spending must remain
strictly below $120. Never query remaining credit. Paid calls use pinned provider
routes without fallback, and reserve $5 before each outstanding request; reported
charges settle the reservation, unknown charges retain it. Planned paid outputs
are 384; current FLUX quote is $0.07/Mpixel and Nano Banana 2 $0.00006/image token.
A typical 1K output is expected below $0.10; this is a forecast, not the guard.
Stop dispatch if actual charges or reservations prevent the next admission.

Append exact payload, start/end time, status, raw response and image hashes,
reported model/quality/geometry and charge for every attempt. Keep raw media
under the ignored namespace. Model IDs pass through unchanged, with no substitute
model on error. OpenAI responses do not currently echo model identity; claims
are about the requested models, with this evidence limit in technical metadata.

Retry at most twice for a completed 429/500/502/503/504 or network error, same
payload, at 20/60-second delays, maximum 24 retries overall. Do not retry policy
refusals or other client rejections. Three consecutive technical failures pause
for diagnosis; repairs preserve payload and endpoints. Crash recovery retains
in-flight attempts as unknown, never silently resubmits them. A terminal receipt
closes the run; any further collection requires a disjoint run and decision.

For a missing named output, its model/scene's repeat-corrected primary outcome is
unavailable. Pairwise comparisons use the intersection of complete scene cells,
report each omitted cell and its cause; also report the common complete-scene
panel across all six models. Missingness can bias these available-scene estimates:
no complete-grid or intention-to-generate claim is made. Fewer than 12 paired
scenes makes that inferential comparison unavailable. Generic/free failures
remove only their corresponding diagnostics. No replacing scenes or pooling
old cohorts to fill missing cells.

Freeze this protocol, exact assignments, analysis implementation, source
identities, scaler and reference-vector hashes before scientific generation.
Transport pilots only test connectivity and returned structure; their feature
outcomes are never inspected. Analysis begins after terminal collection.
