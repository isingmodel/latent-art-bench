# Painter Features v1: relaunch process and research result

Report version: 1.1

Report date: 2026-09-01

Study status: literature synthesis and prospective design framework documented; not executable
or preregistered; no empirical execution authorized

## 1. Executive summary

This relaunch reframes the project around the research aim already present in Pilot 2:
**measure a painter-associated feature across works**. It does not attempt to assign a generic
feature vector to an individual painting and call that vector the painter's style.

The central result is a construct definition:

\[
\mathcal P_a =
P\{z(X)\mid a,\ \text{career phase},\ \text{genre/content},\
\text{medium/support},\ \text{source/reproduction}\},
\]

where \(a\) is the attributed painter and \(z\) is a panel of separately qualified measurements.
The painter feature is the conditional distribution across eligible physical works, with
uncertainty from work sampling, reproduction, processing, and measurement. It is not one image,
one encoder vector, one centroid, one classifier score, or one prompt effect.

The review and design produced:

- a retrospectively documented search and grading procedure;
- a search log with a retrospectively assessed stopping heuristic;
- an evidence matrix with 138 source-level records;
- an audited bibliography with 201 primary, standards, artifact, and marked
  background sources;
- a direct audit of Pilot 2's painter-feature evidence;
- five thematic critical reviews;
- an evidence synthesis and 39-decision method ledger;
- a prospective measurement-design document;
- an eight-gate validation protocol, numbered 0 through 7; and
- a claims and analysis protocol separating real painter association, target fit, specificity,
  coverage, contraction, prompt movement, and availability.

Despite their filenames, the study documents are a **prospective design framework**, not yet an
executable protocol or preregistration. They do not supply a separate execution-freeze artifact
fixing final corpus incidence and minima, exact estimators, simulations, smallest effects of
scientific interest, thresholds, multiplicity, missingness actions, and terminal gate decisions.
“Protocol” below refers to the intended design unless an execution-freeze artifact is explicitly
named.

The literature does not validate any existing learned representation as the painter feature.
Kim's A-vector, Kim's C-vector, CSD, ALADIN, CLIP, DINO-like, Gram, and diffusion-feature spaces
are model-specific candidate coordinates or diagnostics. Their training objectives and
preprocessing determine their meaning. Artist classification or retrieval establishes
label-associated signal, not source invariance, content independence, or coverage of a painter's
oeuvre.

The recommended next scientific step is to prepare, independently review, and freeze an
execution artifact for a real-only qualification study. The current work does not authorize image
acquisition, external-holdout access, feature extraction, model downloads, generation transport,
or image generation.

## 2. Request interpretation

### 2.1 User correction adopted

The phrase “features of the paintings” was initially broad. The user clarified that Pilot 2
should be the reference and that the aim is the **painter feature**. That correction controls the
entire relaunch.

The resulting question is:

> Which image-derived coordinates, measured across multiple held physical works, support a
> reproducible and confound-resistant distribution associated with a painter, and how can a later
> generated set be tested for absolute fit, specificity, and coverage relative to that
> distribution?

This is narrower than automatic art history, artist attribution, style classification, aesthetic
quality, authenticity, or general image similarity.

### 2.2 Construct distinctions

The design separates:

1. a property of one downloaded file;
2. a property stable across derivatives of the same capture;
3. a property stable across independent reproductions of one physical work;
4. a painter-associated distribution across held works;
5. a human-perceived painterly relation under a declared task;
6. semantic or contextual similarity;
7. prompted-name recoverability;
8. exact or near-copy evidence; and
9. materials or painter's-hand evidence from technical imaging.

Evidence at one level is not relabeled as evidence at another.

## 3. Project boundary and historical treatment

### 3.1 Frozen pilots

Pilots 0–3 remain historical evidence. This work does not:

- rewrite their protocols or reports;
- reorder or regenerate hash-bound evidence;
- retry Pilot 2 refusals;
- retry the terminal Pilot 3 Met R2 metadata request;
- use the incomplete Pilot 3 cohort for feature extraction;
- access the sealed external holdout;
- qualify generation transport; or
- generate images.

The relaunch uses a new namespace, painter_features_v1, and treats historical failures as design
constraints.

### 3.2 Type of work

This is a newly versioned scientific reboot study, not shared-library maintenance and not a
repair of a historical pilot. Its output is a research-evidence package and prospective design
framework. It is not an executable protocol or preregistration. No production feature extractor
was implemented because the reviewed candidates have not yet passed the qualification gates that
would determine what should be implemented.

## 4. Research process

### 4.1 Repository reconstruction

The work began by reading the mutable project status, artifact-retention policy, frozen Pilot 2
protocol, Pilot 2 failure investigation, Pilot 2 report, analysis summaries, qualification
evidence, and Pilot 3 boundary. Repository state and ignored evidence boundaries were inspected
before changes.

This established:

- the painter—not movement or era—as Pilot 2's target;
- the exact real-atlas sampling design;
- the learned-formal preprocessing and PCA rules;
- the painter and source classification diagnostics;
- the paired named-versus-control prompt design;
- the target and one-neighbor specificity estimands;
- the 320 assigned generation cells;
- the five terminal moderation refusals; and
- the resulting decision not to run four primary tests on incomplete grids.

### 4.2 Branch and namespace

Work was isolated on the branch codex/relaunch-literature-methods. The versioned study namespace
is studies/painter_features_v1. The literature evidence is under literature_reviews, and this
report is under reports/painter_features_v1.

No unrelated modified project files were intentionally overwritten. Historical report and
evidence directories were not moved or regenerated.

### 4.3 Documented literature-review procedure

The review package records:

- six review questions;
- five search clusters;
- primary-source preference;
- eligibility and exclusion rules;
- review-depth labels;
- an extraction schema;
- evidence grades A, B, C, D, and X;
- synthesis rules; and
- a retrospectively assessed stopping heuristic.

The search protocol and search log were created in the same research worktree, and no timestamped
registration or saved title/abstract screening manifests precede the review. The rules are
therefore an auditable retrospective account of the procedure used, not evidence of a
prospectively registered systematic review. This limits auditability of exclusions and any claim
that the stopping decision was insulated from observed results.

The clusters were:

1. quantitative art history and interpretable features;
2. learned art and painter representations;
3. generated-image evaluation and memorization;
4. digitization and measurement validity; and
5. human and construct validity.

### 4.4 Discovery and verification

Discovery used repository references, backward and forward citation chaining, OpenAlex metadata,
publisher and DOI pages, PMC, CVF Open Access, PMLR, OpenReview, official standards pages,
primary repositories, and targeted web search.

Anchor sources included:

- Kim, Son, and Jeong (2014);
- Lee et al. (2018);
- Sigaki, Perc, and Ribeiro (2018);
- Lee et al. (2020);
- Kim et al. (2026);
- Gatys, Ecker, and Bethge (2016);
- Somepalli et al. (2024); and
- Naeem et al. (2020).

Search hits were not treated as evidence until a primary or official source was resolved.
Preprints were marked. Paper and repository versions were reconciled. Unreported methods were
recorded as unreported rather than inferred.

The final four-cluster stopping pass added four new decision-relevant records, 2.9% of the final
138-record evidence matrix, and no new method family. That is a descriptive retrospective
calculation, not proof that a less-than-10% rule was prespecified or that saturation was achieved:
the rule lacks a prior registration, the pre-pass denominator was not independently frozen, and
the project preserved no screening manifest. The review is broad but is neither exhaustive,
saturated, nor a PRISMA-grade systematic review.

Several web interfaces did not provide a stable export or total-result count. The log preserved
their queries and handling but not a numeric screened-hit total. The project reports this as a
review limitation and does not reconstruct a PRISMA-like denominator after the fact.
The auditable counts are the structured matrix and bibliography, not every search-engine hit.

### 4.5 Parallel skeptical source audits

Three independent research streams were conducted:

- interpretable color, spatial, ordinal, composition, and physical-measurement methods;
- learned art/style representations, Kim A/C, CSD/CSD+, and memorization boundaries; and
- digitization, measurement validity, human construct evidence, robustness, inference, and
  missingness.

The primary agent integrated those streams and checked their decisions against the exact Pilot 2
evidence. A separate skeptical review of the opened pull request is recorded in Section 18.

## 5. Evidence corpus

### 5.1 Structured evidence matrix

The final matrix has 138 unique rows and 11 fields per row:

- stable source identifier;
- year and short citation;
- construct cluster;
- review depth;
- main evidence;
- central limitation;
- project-specific evidence grade;
- disposition; and
- concrete protocol consequence.

At final evidence reconciliation:

| Review depth | Records |
|---|---:|
| Full text | 121 |
| Methods and results | 10 |
| Full text plus exact code | 3 |
| Official standard | 1 |
| Official guideline | 2 |
| Abstract only | 1 |
| **Total** | **138** |

| Evidence grade | Records |
|---|---:|
| A | 31 |
| B | 74 |
| C | 32 |
| D | 1 |
| X | 0 |

Grades describe support for this project's proposed use, not the overall quality or importance
of a paper.

| Prospective disposition | Records |
|---|---:|
| Core candidate or required design evidence | 37 |
| Secondary candidate | 41 |
| Diagnostic only | 38 |
| Background only | 19 |
| Reject for proposed use | 3 |

No individual A-graded paper automatically qualifies a painter coordinate. Local prospective
qualification remains necessary.

### 5.2 Bibliography

The bibliography contains 201 unique entries, more than the evidence matrix because it also records
foundational algorithms, standards, data/model artifacts, additional statistical methods, and
marked background sources that help reproduce or delimit a method. It is organized into:

- Pilot 2 and quantitative-art anchors;
- interpretable measurements;
- learned representations and datasets;
- digitization and technical measurement;
- human perception and construct validity;
- generative evaluation and distribution statistics;
- missingness, resampling, and confirmatory design; and
- primary data, code, and model artifacts.

The evidence matrix remains the authoritative list for project dispositions.

## 6. Pilot 2 result audit

### 6.1 What Pilot 2 observed

Pilot 2 used four painters, two museum sources, and five works per painter-source cell:
40 physical works. Twenty-four works were used for training and 16 were held out. It created a
deterministic project adaptation of Kim's A-vector and fit PCA only on real training works.

The exact real-only results were:

| Diagnostic | Result |
|---|---:|
| Four-painter held balanced accuracy | 0.500 |
| Monet recall | 0.250 |
| Pissarro recall | 0.250 |
| Sisley recall | 0.750 |
| Cézanne recall | 0.750 |
| AIC held balanced accuracy | 0.625 |
| NGA held balanced accuracy | 0.375 |
| Source balanced accuracy | 0.8125 |
| Train NGA / test AIC painter balanced accuracy | 0.250 |
| Train AIC / test NGA painter balanced accuracy | 0.375 |
| Constrained permutation p-value | 0.0216 |
| Retained PCA components | 22 |
| Real training works | 24 |
| PCA cumulative variance | 0.97074 |

The defensible positive conclusion is limited to **pooled artist-label predictability within the
fixed Pilot 2 atlas**. The stronger source signal and near-chance opposite-source transfer mean
that Pilot 2 established no transferable painter feature. The label-prediction result must not be
promoted to painter association under the relaunch definition, which requires source and content
transfer across held physical works.

### 6.2 Why the original qualification gate was insufficient

Pilot 2's pooled accuracy criterion could pass even if the vector used provider-specific
reproduction cues. A PCA retaining 22 components from 24 training works scarcely regularizes a
16,384-dimensional latent. Four held works per painter cannot estimate a phase-, genre-, and
medium-varying oeuvre distribution. A centroid suppresses heterogeneity and cannot measure
coverage.

The new design therefore upgrades the following from descriptive checks to gates:

- same-work independent-reproduction reliability;
- leave-source-out painter transfer;
- leave-content-family-out transfer;
- increment beyond source/content/medium/date baselines;
- several matched hard-neighbor comparisons; and
- within-painter coverage and contraction.

### 6.3 Generated-output result

Pilot 2 defined a target movement:

\[
d(\text{control},a)-d(\text{named},a),
\]

and a target-versus-one-neighbor difference-in-differences. Those are useful paired prompt
effects under a frozen generator and prompt protocol.

Five moderation refusals made both requested-label grids incomplete. All four primary tests were
correctly not run, and the study decision was REDESIGN. The relaunch does not impute, retry, or
replace those cells. Pilot 2 therefore established no generated-output or named-prompt effect.

## 7. Kim et al. method audit

### 7.1 Corpus

Kim et al. analyze 72,447 Western paintings attributed to 2,354 painters, dated 1500–1990 and
assigned to 128 conventional style periods, derived from ART500K. ART500K aggregates heterogeneous
sources such as Google Arts & Culture, WikiArt, and Web Gallery of Art.

Key corpus limitations are:

- approximate and interval dates are collapsed;
- source, physical-work identity, capture workflow, crop, and alternate reproduction are not
  modeled;
- aspect ratios of two or more are removed;
- paper prose and code implement different interpretations of the 410-size rule;
- retained images are forced to a square for A extraction; and
- possible exact-work or near-work encoder pretraining overlap is not audited.

### 7.2 A-vector

The A-vector path:

1. loads through OpenCV;
2. applies its channel-conversion path;
3. forces a 512 by 512 Lanczos resize;
4. writes under the original filename extension, making re-encoding codec dependent;
5. reopens through Pillow and converts to RGB;
6. maps values to minus one through one;
7. encodes with the Stable Diffusion 2.0 first-stage VAE;
8. samples and scales the posterior latent; and
9. flattens a 4 by 64 by 64 tensor to 16,384 dimensions.

The exact released script is not executable unchanged: model initialization is unreachable after
a return, a module-level reference uses an undefined model, and author-local paths remain. The
paper's exact checkpoint hash, RNG state, extracted vectors, posterior realization, reference
fixture, and complete environment are not released.

The A-vector is a sampled reconstruction code. It contains color, content, spatial layout,
texture, composition, crop/border, forced-square warp, interpolation, codec, and VAE
training-domain information. The proper name is Kim A-vector or SD2-VAE appearance coordinate.
It is not an isolated formal or painter feature.

### 7.3 C-vector

The C-vector uses CLIP Interrogator with ViT-H-14/laion2b_s32b_b79k and produces 1,024
dimensions from the original image path. A and C therefore do not share preprocessing.

C can carry subject, scene, object, iconography, text-like marks, chronology, attribution-related
web signals, and possible exact-work exposure. Strong painter or year prediction does not prove
that it isolates context from form. C remains a contextual/semantic diagnostic.

### 7.4 Published validation

Kim et al. report:

| Task | A-vector | C-vector |
|---|---:|---:|
| Year regression R-squared | 0.2024 | 0.8687 |
| Year Pearson correlation | 0.4505 | 0.9324 |
| Ten-painter balanced accuracy | 0.3268 | 0.8226 |
| Ten-style balanced accuracy | 0.2507 | 0.7495 |
| Artist-disjoint year R-squared | 0.189 | 0.850 |

These results establish predictive signal under the paper's splits. They do not control source,
duplicate physical works, capture pipeline, content, phase, or pretraining overlap. Pairwise
same-painter distances also reuse each work many times, so the number of pairs is not the number
of independent observations.

The released artifacts do not support an exact A- or C-vector replication claim. The reboot can
retain a source-faithful, versioned **compatibility reconstruction** as a diagnostic, recording
every recoverable paper/code choice and every unresolved artifact. Repairing A's unreachable
model initialization or supplying a checkpoint makes that extractor an adaptation. A
posterior-mean or repeated-draw VAE coordinate is also a methodological adaptation, not a recovery
of the authors' unpublished posterior realization. C remains provisional until its full artifact
contract—including weights, dependency versions, preprocessing, a reference fixture, and
tolerance—is recovered.

## 8. Interpretable feature findings

### 8.1 Color and chromatic transitions

The evidence supports candidate coordinates for:

- CIELAB D50 lightness and chroma quantiles;
- hue circular moments above a frozen low-chroma threshold;
- fixed lightness-chroma-hue occupancy;
- full adjacent chromatic-distance distributions;
- direction contrasts; and
- raw and mean-normalized multiscale response profiles.

These measure digital-surrogate color organization under a declared color workflow. They do not
identify pigment palette or original appearance. They remain conditional on source and
independent-reproduction validation.

### 8.2 Spatial frequency and edge organization

Supported candidate coordinates include:

- fixed octave-band luminance power;
- robust spectral slope over a justified interval;
- lack-of-fit to a single power law;
- horizontal/vertical anisotropy;
- edge-density response curves;
- orientation entropy and anisotropy; and
- PHOG-like multiscale self-similarity.

Crop, border, aspect ratio, resize, sharpening, compression, blur, and content strongly affect
these quantities. A fitted slope is not proof of fractality or aesthetic quality.

### 8.3 Wavelet and local texture

The retained proposal uses a fixed wavelet family, levels, orientation bands, padding, and
normalization to produce:

- normalized band energies;
- band entropies;
- cross-scale ratios; and
- local-energy distributions.

Ordinary reproductions do not support claims about microscopic brushstroke physics. Multifractal
estimates remain secondary because scaling-range and image-size choices are unusually
consequential.

### 8.4 Ordinal organization

The core candidate is the complete tie-aware two-by-two ordinal-pattern distribution, evaluated
across supported scales. Permutation entropy and statistical complexity are derived secondary
summaries. Quantization, codec, grayscale rule, and resize are explicit perturbations.

### 8.5 Composition

Coarse spatial mass, symmetry, centroid, saliency, and layout statistics are secondary. They can
be driven by subject, crop, frame, and motif. Any painter claim requires cross-content transfer
and incremental prediction of human painterly-manner judgments beyond content.

### 8.6 Rejected RGB claims

The following are outside the ordinary RGB protocol:

- pigment or binder identification;
- layering and underdrawing;
- restoration history;
- impasto height and surface topography;
- microscopic brushwork;
- physical authenticity; and
- attribution as an authorship verdict.

These require calibrated technical modalities and domain experts.

## 9. Learned representation findings

### 9.1 CSD

CSD fine-tunes CLIP backbones using 511,921 deduplicated LAION-Aesthetics images and 3,840
caption-derived artist, medium, and movement tags, plus spatial self-supervision. Its WikiArt
evaluation uses artist identity as a proxy and random work splits. The human task is a constrained
same-artist choice among untrained participants.

This is promising evidence for painter-label retrieval, but the supervisory signal itself
contains artist and art-category text. Source, exact-work exposure, content, and within-painter
coverage remain unresolved. The official repository warns that uploaded weights produce results
that differ from the paper.

CSD is blocked from primary status until the exact checkpoint reproduces a reference suite and
passes the local validity gates.

### 9.2 Raw cosine and CSD+

The CSD+ diagnostic preprint reports negative same-painter-versus-nearest-other gaps for 23 of 91
painters under raw CSD cosine, with two bootstrap intervals wholly below zero. Pooled painter
representations failed for 15 painters; CSLS reduced pooled failures but made scores depend on
the candidate reference pool.

The preprint is useful negative evidence but is not a validated replacement. Raw cosine is not a
calibrated painter-fidelity score. Candidate-pool-dependent scores cannot be compared across
different painter panels.

### 9.3 Other learned spaces

Gram/AdaIN, ALADIN, GOYA, art-trained classifiers, CLIP, DINO-like, DreamSim, DiffSim, and related
spaces are retained only for named diagnostics or evaluator-family sensitivity. Their upstream
training changes what they measure. Recognition and retrieval do not establish oeuvre coverage.

### 9.4 Memorization and copying

SSCD, training-data extraction, data replication, prompt-risk, local-memorization, and attribution
methods form a separate audit layer. Near-copy evidence is neither painter similarity nor proof
of broad painter-feature fidelity. Conversely, style-like similarity cannot rule out local or
exact copying.

## 10. Digitization and observation model

### 10.1 Observation hierarchy

The protocol distinguishes:

\[
\text{physical work} \supset \text{capture} \supset
\text{delivery derivative} \supset \text{analysis transform}.
\]

Two URLs or sizes from one master do not constitute two independent reproductions.

For work \(w\), reproduction \(r\), source \(s\), and processing branch \(p\):

\[
y_{wrsp} = \theta_w + b_s + b_r + b_p + \varepsilon_{wrsp}.
\]

This is an organizing measurement model; interactions and heteroscedasticity are tested rather
than assumed absent.

### 10.2 Required reproduction panel

A future frozen corpus must include independently produced captures of a registered subset of
physical works across painters and providers. Its provider-by-capture incidence matrix must be
connected and pass a rank/identifiability audit. Repeated physical works must bridge provider
pairs, multiple works must occur in each estimable pair, and repeated delivery derivatives must
occur within captures. Otherwise inseparable provider, capture, derivative, and work terms are
collapsed and the claim ceiling is narrowed rather than interpreted as distinct variance
components. The goal is to distinguish:

- capture variation;
- delivery-derivative variation;
- analysis-transform variation;
- within-painter between-work variation; and
- between-painter variation.

Hard eligibility minima and the reproduction-panel size must be selected through frozen
variance-component precision simulations, not as an arbitrary percentage.

### 10.3 Processing branches

The protocol specifies:

- immutable original-byte preservation;
- deterministic ICC-aware harmonization when profiles are valid;
- linear-light luminance for signal measurements;
- CIELAB D50 for perceptual color measurements;
- aspect-preserving painted-field handling;
- explicit masks for frame, mat, border, watermark, and padding;
- a separately flagged assumed-sRGB stratum;
- source-faithful, versioned compatibility-reconstruction branches; and
- 2048, 1024, and 512 long-edge candidate scales without upsampling.

Harmonization is a declared transformation, not proof that source effects have disappeared.

## 11. Validation architecture

### Gate 0 — construct and artifact identity

Require exact formula, input domain, source revision, model/checkpoint hash, license, software
identity, fixture, tolerance, and a paper-code discrepancy record.

### Gate 1 — computational repeatability

Require exact deterministic output or a prospectively justified numeric tolerance. Separate a
posterior mean, a fixed random fixture, and the distribution across stochastic draws.

### Gate 2 — controlled perturbation response

Estimate response to:

- scale and resampler;
- codec and quality;
- bit depth and quantization;
- ICC transformation and missing profile;
- tone, gamma, white balance, blur, sharpening, and noise;
- frame, border, watermark, padding, and crop;
- forced-square versus aspect-preserving processing; and
- construct-changing controls such as hue rotation, phase scrambling, or pixel shuffling.

A coordinate must be stable to nuisance perturbations relative to an execution-frozen smallest
effect of scientific interest while remaining sensitive to transformations that should change
its construct.

### Gate 3 — independent-reproduction reliability

Same-work retrieval under independent captures is diagnostic because it can reward work identity,
content, or defects without preserving painter relations. The gate instead requires paired-capture
stability of painter margins and painter-profile geometry on a connected, identifiable
provider/capture panel. A coordinate stable only across derivatives of one capture is labeled
digital_derivative, not painter-associated.

### Gate 4 — real-only painter specificity and transfer

All tasks hold out physical works:

1. balanced within-domain holdout;
2. leave-source-out;
3. leave-content-family-out;
4. joint leave-source-by-content-out transfer on connected common support;
5. matched hard-neighbor discrimination;
6. broad-negative calibration; and
7. career-phase transfer where historically supported.

Source, codec, content, genre, medium, date, visible signature/text, derivative family, and
pretraining exposure proxies are nuisance probes. Painter performance must add information beyond
nuisance-only baselines. Coordinate and hyperparameter selection for leave-source claims must be
nested at the source level; selection that sees all sources limits the claim to seen-source
performance. Confirmatory distributions are standardized over a frozen shared-support nuisance
distribution rather than silently changing composition by painter.

### Gate 5 — human convergent and discriminant evidence

The primary triplet asks which candidate is closer to an anchor in visible painterly manner while
attempting to ignore depicted subject. Separate tasks assess content, color organization,
mark/texture, and overall appearance.

Experts and nonexperts are separate execution-frozen strata. Whole works, details, content-matched
cross-painter works, same-painter cross-content works, hard neighbors, independent captures, and
controlled variants are crossed. A hierarchical Bradley–Terry, Thurstone, or ordinal model
crosses raters and physical works. Interfaces blind painter and source labels, use a frozen policy
for masking visible signatures/text, measure familiarity and recognition after the primary
judgment, treat unfamiliar-work judgments as primary, and report recognized-work and unmasked
sensitivities.

### Gate 6 — external confirmation

After coordinates, transforms, distances, thresholds, nuisance rules, and missingness handling
freeze, open an institution/capture workflow with no derivative-family overlap for a core
confirmation claim. A confirmation that changes another axis while retaining the same capture
workflow supports only a domain-limited claim. Do not retune on failure under the same protocol.

### Gate 7 — freeze before any generation study

Only a qualified, frozen real painter distribution may be used in a new generated-image
protocol. That protocol separately freezes generator/model identity, prompt blocks, controls,
competitor panels, sample size, refusal rules, and every estimand.

## 12. Analysis and claim architecture

### 12.1 Real-only estimands

The protocol distinguishes:

- painter-associated variance after nuisance adjustment;
- standardized painter distributions over a frozen joint source/content/medium/phase support;
- held-work painter discrimination;
- leave-source, leave-content, and joint source-by-content transfer;
- same-work independent-reproduction reliability;
- hard-neighbor specificity;
- incremental information beyond nuisance baselines; and
- human convergent/discriminant prediction.

The physical work is the unit of inference. Derivatives, patches, pairwise distances, and rater
trials do not inflate the work count.

### 12.2 Later generator estimands

If separately authorized, the canonical painter-fidelity claim is conjunctive: items 1 through 4
must each pass their frozen criterion. A favorable prompt contrast or average cannot compensate
for failure of a conjunct.

1. **Absolute target fit/equivalence:** discrepancy between the generated set and eligible
   target-painter reference, decided against a frozen real-to-real scale and an equivalence or
   noninferiority margin. Failure to reject a difference is not evidence of fit.
2. **Hard-neighbor specificity:** full target-versus-each-eligible-competitor margin vector, with
   the binding decision made on a frozen worst or lower-quantile hard-neighbor margin.
3. **Precision or density:** generated-to-real target support meeting its frozen criterion.
4. **Recall or coverage:** real-to-generated support meeting its independently frozen criterion.
5. **Contraction:** generated dispersion relative to real within-painter dispersion.
6. **Prompt movement:** named versus painter-free paired movement toward the target.
7. **Content coherence:** separate semantic/prompt behavior.
8. **Availability:** probability that a registered cell produces an eligible output.

No universal weighted score is proposed.

### 12.3 Distribution statistics

Raw FID is nonprimary because it assumes Gaussian feature distributions, inherits ImageNet
semantics, combines fidelity and diversity, and is biased at finite and unequal sample sizes.

MMD or energy distance on qualified real-only coordinates is the primary candidate set
discrepancy. Kernel, bandwidth, standardization, dimension, and coordinate weights are fit inside
development folds and frozen. Learned-space KID or CMMD remains secondary. Equal-size
subsampling and sample-size curves are mandatory.

Neighborhood precision, recall, density, and coverage require sensitivity to neighborhood size,
outliers, dimension, and sample size. Transparent stratified occupancy is preferred when the
reference is too small for high-dimensional support estimation.

### 12.4 Dependence, multiplicity, and missingness

Inference uses work-cluster resampling or crossed hierarchical methods, and permutation only
within valid joint source/content/medium exchangeability blocks on common support. A frozen
omnibus or hierarchical closed-testing tree must control selection across primary feature
families, coordinates, scales, encoders, painters, and validation endpoints; within-family
adjustment alone cannot support a project-level painter-feature claim. The same tree is reused in
external confirmation.

For a later generated study, resampling preserves the entire shared-control bundle: content,
model/version, request path, seed/repetition, the common control, and all named-painter outputs
move together. Real reference works are also jointly resampled across contrasts. A design using
independent controls instead must index and freeze a separate control for every target.

Missingness is classified as:

- structural ineligibility;
- source noncoverage;
- acquisition failure;
- measurement failure;
- generation refusal;
- invalid output; or
- missing human rating.

Intent-to-generate denominators include every registered cell. An incomplete confirmatory paired
grid is not replaced by an unregistered available-case test. The execution freeze must also set
crossed-cell completeness minima and denominators, report differential selection by painter and
nuisance strata, and define pattern-mixture, tipping-point, or worst-case missing-not-at-random
sensitivities. Failure to retain the decision across registered sensitivity bounds narrows or
fails the claim.

## 13. Corpus requirements for an execution study

Before acquisition, a new execution protocol must freeze:

- painter and comparison-painter selection;
- attribution status policy;
- eligible physical works;
- source/provider sampling frames;
- career phase, content/genre, medium, date, and motif strata;
- a connected painter-by-source-by-content-by-medium-by-phase common-support table;
- hard cell minima, at least two painters per confirmatory exchangeability cell, and frozen
  shared-support weights;
- independent reproduction panel;
- work and derivative-family identifiers;
- rights and redistributability;
- exact provenance fields;
- development, qualification, human-task, and external partitions;
- precision or power simulation;
- feature-card formulas and artifacts;
- SESOIs and gate thresholds;
- missingness and terminal transport rules; and
- ignored runtime storage boundary.

Every painter used for confirmatory specificity must lie in the connected common-support graph,
span multiple eligible sources and content strata, and avoid perfect aliasing with their joint
interaction. Estimands are restricted to that frozen support with frozen weights. A painter
outside it may be described but cannot support broad painter-specificity inference.

## 14. Claims allowed and prohibited

### 14.1 Allowed after the relevant gates

- file-level color, spatial, ordinal, or learned-appearance profile;
- reproduction-associated coordinate under the tested capture domain;
- painter-associated coordinate under declared source/content/phase/medium limits;
- human-perceived painterly similarity under a declared task and rater population;
- named-prompt movement under one frozen generator and prompt protocol;
- absolute target-distribution equivalence, hard-neighbor specificity, precision/density, and
  recall/coverage as separate reported results and, only if all pass, a conjunctive canonical
  painter-fidelity claim;
- contraction, prompt movement, content coherence, and availability as secondary results that
  cannot rescue a failed fidelity conjunct.

### 14.2 Prohibited

- a single universal painter style vector;
- artistic essence or intention from image statistics;
- authorship or authenticity verdict from a convenience classifier;
- pigment, binder, layering, or impasto claims from catalog RGB;
- source invariance inferred from harmonization alone;
- formal/context separation inferred from A-versus-C architecture;
- oeuvre coverage inferred from recognition or centroid proximity;
- specificity inferred from one convenient neighboring painter;
- painter fidelity inferred from a positive named-prompt contrast alone;
- independent evidence counts based on all dependent pairs or patches;
- universal art claims from a Western canonical web corpus; and
- evidence of training inclusion inferred solely from visual similarity.

## 15. Principal risks that remain

1. **Selection bias.** Digitized museum works are not a random sample of a painter's production.
2. **Attribution uncertainty.** Historical painter labels can be disputed or workshop-level.
3. **Incomplete cross-classification.** Source, phase, medium, content, and painter may lack
   sufficient overlap.
4. **Reference size.** Oeuvre distributions may be too sparse for high-dimensional support
   estimation.
5. **Capture provenance.** Many public derivatives lack profiles and independent capture records.
6. **Pretraining exposure.** Learned encoders may have seen exact works or attribution-rich
   near-duplicates.
7. **Human task ambiguity.** Raters may not fully ignore content even under careful instruction.
8. **Expert heterogeneity.** Expertise is not one population and may change which cues count as
   painterly.
9. **Estimator dependence.** Metric, kernel, scale, and encoder choices can change rankings.
10. **Generator dependence.** A later prompt effect belongs to a generator/model/policy version,
    not to the painter in general.
11. **Availability bias.** Refusal and failure can differ by painter name or content.
12. **Cultural scope.** The reviewed and historical corpora overrepresent Western canonical art.

These are not reasons to abandon the study. They define the conditions a credible execution must
measure and report.

## 16. Artifact inventory

### Literature evidence

- literature_reviews/README.md
- literature_reviews/SEARCH_PROTOCOL.md
- literature_reviews/SEARCH_LOG.md
- literature_reviews/EVIDENCE_MATRIX.csv
- literature_reviews/BIBLIOGRAPHY.md
- literature_reviews/SYNTHESIS.md
- literature_reviews/METHOD_DECISIONS.md

### Critical reviews

- literature_reviews/reviews/00_pilot_2_painter_feature_audit.md
- literature_reviews/reviews/01_interpretable_painter_features.md
- literature_reviews/reviews/02_kim_and_learned_painter_features.md
- literature_reviews/reviews/03_digitization_and_measurement_validity.md
- literature_reviews/reviews/04_human_construct_validation.md
- literature_reviews/reviews/05_distribution_statistics_and_missingness.md

### Prospective design-framework package

- studies/painter_features_v1/README.md
- studies/painter_features_v1/MEASUREMENT_PROTOCOL.md
- studies/painter_features_v1/VALIDATION_PROTOCOL.md
- studies/painter_features_v1/ANALYSIS_AND_CLAIMS.md

### Review and response

- reports/painter_features_v1/SKEPTICAL_REVIEW.md
- reports/painter_features_v1/RESPONSE_TO_REVIEW.md

The exact first-pass review is also preserved in its linked GitHub comment. Section 18 summarizes
the consolidated findings and their required dispositions in this process report.

## 17. Result and present decision

### 17.1 Positive result

The project now has an evidence-backed proposed definition of a painter feature, candidate
measurements with explicit construct limits, a reproduction-aware observation model, and a gated
design for moving from digital files to painter-associated and human-perceived claims. This is a
substantive research-design result, but it is not executable without the separate execution
freeze.

### 17.2 Negative result

No existing candidate is presently qualified as the painter feature. In particular:

- Pilot 2's adapted Kim A-vector remains source-confounded;
- Pilot 2 established only pooled artist-label predictability within its fixed atlas, no
  transferable painter feature and no generated-output effect;
- Kim A and C do not provide a controlled formal/context decomposition;
- the released Kim artifacts do not support an exact A- or C-vector replication claim;
- CSD has unresolved artifact and construct-validity issues;
- artist classification does not establish coverage;
- raw cosine and raw FID are not calibrated painter-fidelity measures; and
- ordinary RGB cannot support physical-material claims.

### 17.3 Operational decision

Proceed only to writing and independently reviewing a real-only painter-feature execution-freeze
artifact. Do not begin data acquisition or extraction until the connected common-support and
provider/capture incidence tables, minimum counts, exact estimators, simulations, smallest
effects of scientific interest, thresholds, multiplicity tree, missingness actions, rights, and
external boundaries are frozen. The present package must not be cited as a preregistration.

## 18. Independent skeptical review and response

A fresh skeptical researcher reviewed the exact
[PR #1](https://github.com/isingmodel/latent-art-bench/pull/1) diff and preserved the first verdict
in a [GitHub review comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370).
The review assessed the work from the standpoint of
measurement theory, causal identification, statistical inference, and reproducibility. The
review found no basis for treating the package as ready for empirical execution and identified
the following material defects. The table records the required response rather than silently
editing away criticism.

At this report revision, the requested corrections are implemented locally, but **no item is
marked resolved until the changed documents have been inspected in the updated PR diff and the
reviewer has completed a fresh re-review**. “Pending verification” means that closure has not yet
been granted.

| Priority | Skeptical finding | Required disposition | Status at this report revision |
|---|---|---|---|
| P2 | Pilot 2's 0.50 balanced accuracy was promoted to painter-associated signal despite failed source transfer. | Name the result only as pooled artist-label predictability within the fixed Pilot 2 atlas; state that no transferable painter feature or generated-output effect was established. | Implemented; reviewer verification pending. |
| P1 | Kim A/C were promised as exact replications although the released artifact contract lacks the checkpoint/RNG/fixtures and A is not executable unchanged. | Permit only a source-faithful, versioned compatibility reconstruction; call every repaired A extractor an adaptation and keep C provisional until its artifact contract is recovered. | Narrative corrected; artifact-card verification pending. |
| P1 | Painter distributions were not restricted to identifiable joint common support, allowing painter to remain aliased with source, content, medium, and phase. | Freeze a connected painter-by-joint-nuisance support table, hard cell minima, at least two painters per confirmatory exchangeability cell, shared-support weights, and joint source-by-content transfer; narrow or fail claims outside support. | Pending protocol verification. |
| P1 | Generator and real-reference estimands wrote unqualified \(P_a\), silently dropping the conditioning variables in the construct definition. | Define a standardized target distribution over frozen common nuisance support or use exact matched contrasts; declare weights, source handling, and behavior outside support. | Pending protocol verification. |
| P1 | Multiplicity control was only within family even though the project selects among families, coordinates, scales, encoders, painters, and validation endpoints. | Freeze one primary omnibus claim or a hierarchical/closed-testing tree with strong error control, and reuse the same tree for external confirmation. | Pending protocol verification. |
| P1 | Canonical generated-painter claims omitted binding absolute fit/equivalence, hard-neighbor tail specificity, and generated-to-real support. | Require conjunctive success on absolute equivalence/noninferiority, the worst or lower-quantile hard-neighbor margin, precision/density, and recall/coverage; no secondary outcome may rescue a failed conjunct. | Narrative corrected; protocol verification pending. |
| P1 | The reproduction variance decomposition was not identifiable from the stated sampling prose. | Require a connected provider/capture incidence matrix, rank audit, repeated works bridging provider pairs, multiple works per pair, and repeated derivatives per capture; otherwise collapse inseparable effects and lower the claim ceiling. | Narrative corrected; protocol verification pending. |
| P1 | Several evidence-matrix rows materially misdescribed the cited method or corpus, making the table inconsistent with the thematic reviews. | Rebuild disputed rows from primary methods and run a DOI-keyed identity audit across the matrix, bibliography, and review tables. | Citation audit implemented; reviewer verification pending. |
| P2 | Same-work independent-capture retrieval can reward content or work-specific defects and was treated as a gate for painter structure. | Keep same-work retrieval diagnostic; gate on paired-capture stability of painter margins and painter-profile geometry. | Narrative corrected; protocol verification pending. |
| P2 | Feature and hyperparameter selection could see held sources before a leave-source evaluation. | Nest method selection at the source level or explicitly limit the result to seen-source performance. | Narrative corrected; protocol verification pending. |
| P2 | External confirmation could change any one axis while reusing the same capture workflow. | Require an unopened institution/capture workflow with no derivative overlap for a core claim; confirmation on another axis alone supports only a domain-limited claim. | Narrative corrected; protocol verification pending. |
| P2 | Complete-case analysis lacked frozen crossed-cell completeness and selection-sensitivity rules. | Freeze denominators and minima, report differential selection, run registered missing-not-at-random bounds/tipping analyses, and narrow or fail claims that are not robust. | Narrative corrected; protocol verification pending. |
| P2 | Future resampling ignored dependence induced by a shared painter-free control across named-painter contrasts. | Resample the whole content-by-model/version-by-seed bundle containing the shared control and all named targets, and jointly resample real references; otherwise freeze independent target-specific controls. | Narrative corrected; protocol verification pending. |
| P2 | The human gate omitted binding label/source blinding, signature/text controls, and familiarity/recognition handling. | Blind labels and source, freeze masking, measure recognition after the main judgment, make unfamiliar works primary, and report recognized/unmasked sensitivities. | Narrative corrected; protocol verification pending. |
| P2 | The package described itself as executable or preregistered without frozen corpus minima, estimators, simulations, SESOIs, thresholds, and terminal actions. | Call it a prospective design framework and require a separate, independently reviewed execution-freeze artifact before any operation. | Narrative corrected; final package verification pending. |
| P2 | The literature search/stopping process was called prospective although protocol and log appeared together and no saved screening manifests exist. | Describe the review as a broad, retrospectively documented critical review; do not claim preregistration, exhaustive systematic coverage, or a prospective stopping decision. | Narrative corrected; search-artifact verification pending. |
| P2 | A digitization-review statement paraphrased Redies/Groß as invariance when the reported result was absence of a significant aggregate difference. | Use the narrower statistical wording and avoid converting a null aggregate comparison into evidence of invariance. | Citation-review correction pending verification. |

The response strategy is fail-closed. If common support, reproduction identifiability, source-level
nested selection, or external independence cannot be achieved, the framework requires a narrower
domain-limited or diagnostic claim; it does not substitute a more convenient estimand. Exact
closure status belongs in the final review-response artifact after the reviewer inspects the
revised diff.

## 19. Quality assurance record

At initial report creation:

- the evidence matrix parsed as a valid 11-column CSV;
- all 138 source IDs were unique;
- evidence-grade and disposition counts reconciled to 138;
- no absolute user path appeared in the new research artifacts;
- no unresolved drafting marker appeared in the protocols or reviews; and
- the project remained documentation-only, with no artwork, model, or generated-image operation.

Final whitespace, link, repository, test, PR, and skeptical re-review checks are appended only
after the review/revision cycle; this report does not predeclare them successful.
