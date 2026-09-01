# Painter-feature validation protocol

Protocol version: `painter_features_v1/validation/1.0`

Status: prospective design; thresholds must be finalized by simulation before execution

## 1. Validation thesis

A painter feature is not established by artist-label prediction alone. Prediction can exploit
institution, codec, resolution, genre, subject, chronology, signature text, or training-set
memorization. Qualification instead requires a chain of evidence:

1. the coordinate is computationally repeatable;
2. its same-work reproduction and preprocessing error is known;
3. it contains painter-associated signal on held-out physical works;
4. that signal transfers across provider and content/genre partitions;
5. it is not better explained by nuisance variables or an artist-name shortcut;
6. its distance structure has convergent and discriminant evidence from humans; and
7. it generalizes to an external corpus before it supports a broad painter claim.

Failure at a gate changes the disposition or claim ceiling. A failed method is recorded; it is
not tuned on the confirmation set until it passes under a new versioned protocol.

## 2. Data partitions fixed before feature outcomes

The execution protocol must freeze nonoverlapping partitions at the physical-work and
derivative-family levels:

- **method fixtures:** redistributable synthetic or licensed images used only for formula and
  runtime tests;
- **development works:** used to select candidate coordinates, perturbations, binning, and
  model hyperparameters;
- **qualification works:** held-out real works used for the gates below;
- **external works:** a sealed institution/source and, where feasible, cultural/geographic
  domain used once after the painter-feature specification freezes; and
- **human-task works:** a balanced sample that does not reuse model-tuning judgments as final
  criterion validation.

All transforms, standardization, PCA, metric learning, thresholds, prototypes, and nuisance
models are fitted within the development side of each resampling split. The same physical work,
capture, derivative, or near duplicate never appears in both fit and test partitions.

## 3. Gate 0 — definition, provenance, and executable identity

For every coordinate or encoder, require:

- a construct/non-construct statement;
- exact formula, input color domain, scale, mask, resize, codec, and missingness rules;
- primary paper, supplement, and exact source revision where available;
- model architecture, weight URI, revision, cryptographic hash, license, and tensor mapping;
- software/runtime/hardware fingerprint;
- at least one independently checkable fixture with expected values and tolerances; and
- a documented result when the paper and released implementation disagree.

An inaccessible or discrepant artifact may remain a historical replication target, but it does
not qualify as the primary painter feature. In particular, Kim A/C vectors and current CSD
weights remain provisional until their artifact discrepancies are resolved locally.

## 4. Gate 1 — computational repeatability

Run each fixture and a stratified set of real development files repeatedly across process starts.
For deterministic methods, exact output identity is required after a fixed runtime and hardware
contract. For methods with unavoidable numerical nondeterminism, require a preregistered absolute
and relative tolerance and report the maximum coordinate deviation.

For stochastic encoders, distinguish three estimands:

- posterior mean or other deterministic statistic;
- a fixed, content-derived random draw used as a computational fixture; and
- the distribution across random draws.

A fixed seed makes a pipeline repeatable; it does not prove that it reproduces an author's
unpublished realization or that the random draw is a valid painter measurement.

**Pass.** All fixtures and repeats conform to the declared identity/tolerance, with no silent
fallback, download, or preprocessing branch.

## 5. Gate 2 — controlled perturbation response

### 5.1 Perturbation panel

Each eligible development reproduction is transformed one factor at a time, plus a small
preregistered factorial subset, using:

- supported long-edge resolutions and at least two antialiased resamplers;
- JPEG or WebP encode/decode levels spanning visually mild catalog delivery;
- bit-depth and quantization changes;
- embedded-profile conversion, profile removal, and an explicitly flagged assumed-sRGB branch;
- mild gamma/tone, white-balance, blur, sharpening, and sensor-noise perturbations;
- frame, mat, border, watermark, padding, and crop uncertainty;
- aspect-preserving versus method-required forced-square processing; and
- phase scrambling, pixel shuffling, and hue rotation as construct-specific negative controls.

Only transformations defensible for the coordinate's input domain are used. A color statistic is
expected to respond to hue rotation; an orientation statistic is expected to respond to phase
scrambling. Stability to a construct-changing perturbation would be a failure of sensitivity,
not a virtue.

### 5.2 Estimation

For scalar coordinates, fit a work-clustered variance-components or hierarchical model and report:

- repeatability/reliability with uncertainty;
- within-work perturbation standard deviation and 95% repeatability coefficient;
- between-work and between-painter variance after nuisance adjustment;
- slope or response curve for each ordered perturbation; and
- fraction of painter-pair orderings reversed by the perturbation.

For vectors, report within-work and between-work distance distributions, same-work retrieval,
nearest-neighbor stability, and centered kernel alignment/Procrustes stability where appropriate.

### 5.3 Decision rule

Before execution, domain experts must set the smallest effect size of scientific interest (SESOI)
for every primary family. A coordinate passes for a proposed estimand only when the upper
confidence bound on its reproduction/perturbation error is below the SESOI and its expected
construct-changing controls move it in the correct direction. If no defensible SESOI exists, the
coordinate remains descriptive and its noise interval accompanies every result.

## 6. Gate 3 — same-work independent-reproduction reliability

This is the central distinction between file properties and painter features.

### 6.1 Required comparisons

Use independently produced captures where available, not two URLs pointing to the same master.
Test:

- same work, different independent capture/source;
- same capture, different delivery derivative;
- different work, same painter/source/content stratum;
- different painter, matched source/content/medium/date stratum; and
- different painter/source to expose easy domain shortcuts.

### 6.2 Metrics

Report scalar variance components and generalizability coefficients. For vector families, report
same-work top-1 and top-k retrieval with confidence intervals, median same-work distance relative
to matched different-work distance, and calibration curves. Work-level cluster bootstrap or
randomization respects all reproductions nested within the work.

### 6.3 Pass and fallback

A coordinate intended for a physical-work-associated painter feature must meet the Gate 2 SESOI
criterion across independent captures and show same-work identity beyond matched different works.
If it succeeds only across derivatives of the same capture, its ceiling is `digital_derivative`.
If it fails independent-capture reliability, it may remain a source-sensitive diagnostic but is
not admitted to the painter profile.

## 7. Gate 4 — real-only painter specificity and transfer

### 7.1 Painter representation

For painter \(a\), estimate a conditional distribution

\[
P_a(z \mid c,m,t,s),
\]

where \(z\) is the qualified coordinate profile, \(c\) is content/genre, \(m\) is
medium/support, \(t\) is date or career phase, and \(s\) is reproduction source. The implemented
model may be hierarchical, kernel-based, or another preregistered estimator, but it must propagate
finite-reference uncertainty. A simple centroid is retained only as a transparent baseline.

### 7.2 Painter-specificity tasks

All tasks hold out physical works and report uncertainty:

1. **Within-domain work holdout:** fit/test sources and content are balanced.
2. **Leave-source-out:** fit on one or more providers and test a provider never used in fitting.
3. **Leave-content-family-out:** test a genre/subject family absent from fitting for each painter.
4. **Matched hard-neighbor discrimination:** distinguish historically/visually close comparison
   painters under overlapping content, medium, and date.
5. **Broad-negative discrimination:** compare the target with a preregistered panel outside the
   hard-neighbor set to expose threshold calibration.
6. **Career transfer:** where sample size and historical metadata permit, fit one career interval
   and test another; otherwise the claim is explicitly interval-specific.

Painter-balanced accuracy, macro recall, log loss/Brier score, calibration, target ranks, and
effect sizes are reported. The physical work remains the unit of inference. A permutation test
shuffles painter labels only within valid exchangeability blocks defined by source, content,
medium, and split.

### 7.3 Nuisance and shortcut probes

Using the same fit/test discipline, attempt to predict:

- source/institution and delivery codec;
- content/genre and object labels;
- medium/support and date bin;
- visible signature/text presence;
- collection page or derivative family; and
- whether the painter name is likely represented in an encoder's pretraining data, where an
  auditable proxy exists.

Mask or audit signatures and text rather than assuming they are harmless. Painter success does
not pass if a nuisance-only baseline explains it, if leave-source-out performance collapses to the
preregistered chance/equivalence region, or if artist-name/image memorization is a plausible
unresolved mechanism.

### 7.4 Gate decision

The final numeric thresholds are selected by prospective simulation. At minimum, a core painter
feature must:

- exceed chance/equivalence bounds with multiplicity-controlled uncertainty on work-held-out,
  leave-source-out, and leave-content-family-out tasks;
- retain the sign of target-versus-hard-neighbor effects across eligible sources;
- show calibrated uncertainty rather than only rank accuracy;
- add out-of-sample information beyond source/content/medium/date baselines; and
- avoid a source-prediction advantage that can account for painter performance.

Pilot 2's criterion of pooled held balanced accuracy merely greater than four-class chance is not
reused. Its source-stratified signs are retained as a minimum diagnostic, but cross-source transfer
is now gating.

## 8. Gate 5 — convergent and discriminant human validity

### 8.1 Judgment task

Use pairwise or triplet comparisons instead of asking raters to invent a scalar definition. The
primary triplet asks which of two candidates is closer to an anchor in **visible painterly manner,
ignoring depicted subject as far as possible**. Separate tasks ask about content similarity,
color organization, mark/texture, and overall appearance. This separates constructs instead of
forcing raters to use one ambiguous word.

Stimuli include:

- content-matched cross-painter works;
- same-painter cross-content works;
- same-work independent reproductions;
- hard-neighbor and broad-negative pairs;
- crops/details and whole works as separate conditions; and
- controlled color, phase, crop, and scale variants.

Experts (art historians, conservators, or practicing painters, roles recorded separately) and
nonexperts form preregistered strata. Display calibration, image size, viewing duration, device,
instructions, attention checks, exclusions, and compensation are fixed. Raters and works are
crossed, and neither number of ratings nor patches is treated as the number of paintings.

### 8.2 Model and criteria

Fit a hierarchical Bradley–Terry/Thurstone or ordinal model with random effects for work and
rater. Report inter-rater/generalizability estimates, expert/nonexpert differences, posterior or
confidence intervals, and held-out prediction of judgments.

A learned or interpretable painter distance has convergent evidence when it predicts painterly-
manner judgments on held-out works beyond content, source, color-only, and low-level baselines.
It has discriminant evidence when it does not simply reproduce the separate content-similarity
judgments. Human disagreement is part of the construct; majority vote is not treated as error-free
ground truth.

### 8.3 Claim ceiling

Without this gate, use `painter-associated image profile` or `learned appearance profile`.
`Human-perceived painterly similarity` is permitted only for the tested task, rater population,
display condition, and domain.

## 9. Gate 6 — external confirmation

Freeze the retained feature coordinates, transforms, distances, nuisance model, missingness
rules, and thresholds before opening the external set. The external set must change at least one
meaningful domain axis: institution/capture workflow, geography/canon, medium, period, or content.
Report every registered method, including failures.

A method that fails external confirmation is not tuned on the external set and relabeled a
success. It remains domain-limited or becomes a new development candidate under a new version.

## 10. Gate 7 — freeze before any generation study

Only after Gates 0-6 may the project freeze a generated-image comparison. The frozen package must
contain:

- qualified painter distributions and their real-reference uncertainty;
- feature and preprocessing artifact hashes;
- prompt/content blocks and matched painter-free controls;
- hard-neighbor and broad-negative panels;
- target fidelity, specificity, coverage, contraction, and coherence estimands;
- availability/refusal/missingness estimands;
- top-level sampling unit and simulation-based sample size;
- multiplicity family and decision thresholds; and
- a prohibition on output selection or reference-set changes after inspection.

The historical Pilot 2 and Pilot 3 generation/acquisition authorizations remain closed. This gate
defines requirements for a future study; it does not reopen them.

## 11. Dispositions

| Disposition | Meaning |
|---|---|
| `qualified_core` | passes computational, perturbation, reproduction, painter-transfer, human, and external gates for the stated domain |
| `qualified_domain_limited` | passes only for a declared source, phase, content, medium, or other narrower domain |
| `reproduction_associated` | stable across the tested reproduction domain but not painter-specific under transfer |
| `diagnostic_only` | useful for sensitivity, source/content checks, or method comparison but lacks painter construct validity |
| `digital_derivative` | stable only for derivatives of the same capture |
| `replication_only` | retained to reproduce a paper under its native input and artifact assumptions |
| `failed` | fails a gate essential to its intended use or has irrecoverable provenance/artifact defects |
| `not_executed` | required inputs, rights, artifacts, or eligible observations were unavailable |

Each disposition is attached to a version and a claim domain, not permanently to an algorithm
name. The same vocabulary is defined in `../../literature_reviews/METHOD_DECISIONS.md`.
