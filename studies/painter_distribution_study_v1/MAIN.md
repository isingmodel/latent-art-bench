# Controlled finite-reference study: main contract

Issued before research generation or new fidelity measurement. This implements
Stages D/E of the umbrella protocol and the user-authorized retry amendment.
The completed pilot and all historical studies remain separate evidence.

## Panel and content design

Use every visually eligible R2 reference: 38 Monet and 32 Cézanne works, in the
recorded candidate order. Retain all 71 annotations and the excluded figure-led
work. The coding is a single maintainer LLM's direct image review, not independent
expert validation. Water / built / land counts are 21/4/13 for Monet and 3/11/18
for Cézanne. Thin perimeter borders and ambiguous organization remain recorded;
no rescue cropping or outcome-based selection occurs.

The primary target is each painter's **finite collected content mixture**. Original
works have equal weight; generated observations receive the same fixed class masses
as that painter's reference. Each class has eight scene briefs and three repetitions
per condition (24 outputs per class). All three classes are required for the primary
weighted comparison. For attrition, distribute each class's fixed mass equally among
its available observations; report effective sample sizes and every disposition.
The collected generated mixture and a common one-third-per-class mixture are
mandatory sensitivities. The latter heavily weights Cézanne's three water works;
it is not a representative-oeuvre estimate.

Use the **same 24 detailed content briefs across both painters and all routes**.
This improves direct painter-name and cross-model controls without adding requests.
Briefs are constructed from shared visible subject types, without painting titles,
specific locations, artwork images or instructions for particular palettes or
brushwork. They control coarse content, not exact compositional equality. Source
paintings retain different fine subjects, seasons and viewpoints. Generated-image
content adherence is not assumed or used to discard unfavorable outputs.

`configs/painter_distribution_study_v1/research.json` contains the exact strings.
All prompts request an oil painting on canvas and the painting area without a
frame, signature, letters or watermark. The named condition adds only the painter
name to the detailed artist-free prompt. OAuth additionally receives a generic
named condition using a shorter content description. Removing detail is a compound
content-specificity intervention; it does not isolate word count or verbosity.

## Requests, assignment and timing

There are 1,008 research slots: 24 briefs × three repetitions × two painters ×
seven route/condition combinations (two each for Google and BFL, three for OAuth).
The exact rendering payloads reuse the technically qualified pilot transport.
Google and BFL request 1024-square-equivalent output but return different encodings;
OAuth is a service alias with observed geometry and quality deviations. Provider
pinning does not attest a frozen backend checkpoint or absence of prompt rewriting.

Use design seed 2026090617. Assign repetition r of brief index b to window
`(b % 8 + 3*r) % 8`. Every brief appears in three distinct windows. Each of eight
windows contains 126 slots. Within each window, independently permute route ×
painter × brief/repetition groups, then uniformly permute each group's two or
three conditions. Store every group and condition position before dispatch.

Window offsets are 0, 3, 6, 9, 24, 27, 30 and 33 hours from a recorded UTC origin
chosen prospectively at freeze preparation. These are earliest dispatch times,
not fabricated independent sessions. Late windows retain actual timing. Requests
are serial with a 15-second minimum inter-request delay. The collection remains
active between windows; a bounded command can return "waiting" without closing it.

Apply `RETRY_AMENDMENT.md`: one retry for a known-charge, complete explicit transient
error, at most 24 retries total. Each retry is a separate child census authorized
conditionally by this committed main design. Before its POST, a create-once child
authority record binds the parent's terminal event and main freeze; its payload
is identical. This is execution of a prospectively frozen conditional rule, not
a post-result change of method. The first valid image is the slot outcome; the
initial-only dataset remains a sensitivity. No valid output is regenerated.
Stop and diagnose systematic failures before a separately frozen successor. Keep
the $75 ceiling, $5 paid-request reserve, 5 GiB free-storage reserve and all ledgers.

## Measurement and fixed scaling

After the main freeze is committed, process the 70 references and eventual first
successful slot outputs under three fixed pipelines:

1. Primary: existing ICC/EXIF/opacity-aware aspect-preserving Lanczos normalization
   to a 512-pixel short side; the unchanged 31-feature extractor and existing scaler.
2. Resolution: identical procedure at a 256-pixel short side.
3. Encoding: primary normalized 512 RGB encoded once using Pillow JPEG quality 90,
   4:2:0 subsampling, no optimization/progressive encoding, then decoded for extraction.

The JPEG operation is a shared additional encoding, not recovery of an original
uncompressed capture. No palette, histogram or texture matching is performed.
For pipelines 2/3, remeasure only the **same 221 previously measured development
works** and fit the existing equal-painter-weighted empirical median/IQR scaler.
Never fit a scaler to new reference or generated outcomes. Preserve all failures;
if development remeasurement fails or any coordinate scale is invalid, withhold
that whole sensitivity. The primary scaler and historical feature records remain
unchanged. Process development first, publish its scalers, then measure new data.

Record raw hashes, normalized hashes, processing metadata, feature vectors and
membership. Generated images require complete raw-response verification and the
frozen slot-selection policy. Duplicate image hashes are flagged and retained,
not replaced; they do not count as evidence of independent sampling.

## Endpoints and inference

Use weighted V-energy in Euclidean scaled feature space, including cross and both
within-distribution terms. It is a full-distribution discrepancy, not distance to
a painter centroid. Report all 31 features as the primary representation and the
11 color / 8 spatial / 12 texture subsets descriptively. Include total weighted
variance and summed squared coordinate-IQR ratios, labeled feature spread.

The eight all-31 prompt contrasts and their complete-pair/availability rules are
fixed in `INFERENCE.md`. Use endpoint seed `2026090817 + endpoint_index` in ordered
route × painter named-versus-free comparisons, then painter generic-versus-detailed
OAuth comparisons. Keep all eight p-values in Holm adjustment. Qualification must
pass before inferential labels are used. These tests concern a sharp joint null
for the assigned slot policy, conditional on the finite references, and require no
interference. Retry delays, duration differences and unobserved service state may
challenge that assumption. The test is not a calibrated absolute style-equality test.

Additional mandatory descriptive analyses:

- Collected-mixture and equal-class results; exclude ambiguous reference labels
  with masses renormalized to that subset's empirical class frequencies; and
  restrict original source native short side to at least 1024 pixels.
- All-31 energy contrasts after leaving each collection window and each brief out;
  report sensitivity ranges, not confidence intervals.
- Disjoint real/real baselines with 999 fixed-seed draws. Within each content class,
  draw two disjoint groups of `floor(class_count/2)` originals. Draw the same class
  counts of generated images without replacement for a matched original/generated
  comparison. Both groups retain the declared class masses. If a class cannot
  support the draw, report unavailable. These are finite subsampling summaries.
- Secondary reference coverage: fraction of original-centered balls containing
  at least one generated image, using the third nearest other original as radius.
  Also report 100 generated subsamples of size `min(n_original,n_generated)` with
  fixed seed, without replacement. This neighborhood statistic is sample- and
  representation-dependent, not a calibrated measure of artistic completeness.
- Group-disjoint original/generated linear and RBF kernel-ridge detection, with
  fixed existing kernels/ridge and six whole-brief folds, disjoint original works,
  and content/label-balanced training weights. Report content-weighted out-of-fold
  balanced accuracy and AUC, retaining predictions and memberships. An eight-window
  split is an additional service-time sensitivity, not an independent-session claim.
- Painter-specific common PCA views of all groups with half the mass on originals
  and half equally divided among generated cells, using the primary content weights.
  Add original-only PCA. Keep every point, group-independent limits and explained
  variance. PCA is visualization, never classifier input or a separation test.
- Compare each named group's distances to both painter references under the same
  equal-class mixture. Report painter specificity separately from absolute distance.

Use analysis seed 2026090817 with deterministic named substreams for all descriptive
draws. Report availability, requested/returned settings, cost, actual time span and
source processing alongside outcomes. No post-hoc effect-based retry or sample-size
extension. The paper must distinguish completed findings from any pending outputs.

The exact code, tests, configuration, contracts, reference annotations, acquired
raw hashes, pilot qualification, synthetic decision and historical scaler inputs
must be committed and bound before dispatch or fidelity extraction. New report
rendering may be implemented later if it cannot alter these frozen estimands.
