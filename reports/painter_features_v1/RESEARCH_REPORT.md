# Painter Features v1: relaunch process and research result

Report version: 1.7

Report date: 2026-09-01

Study status: literature synthesis and prospective design framework documented; not executable
or preregistered; no empirical execution authorized

Canonical-plan notice: this report is a historical account of the relaunch process and its
intermediate design decisions. It is supporting evidence, not an active protocol. The sole
current plan is
[`studies/painter_features_v1/MEASUREMENT_PROTOCOL.md`](../../studies/painter_features_v1/MEASUREMENT_PROTOCOL.md).

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
- a claims and analysis protocol separating real painter association, target fit, panel-wide
  specificity, precision, density, recall, coverage, content coherence, contraction, prompt
  movement, and availability.

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
- an intended detailed extraction schema that was not instantiated as 138 per-source evidence
  cards;
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
fixed Pilot 2 atlas**. A separate two-class task showed high source predictability, while painter
prediction failed to transfer convincingly across sources. Raw balanced accuracies from those
unlike tasks are not ranked against each other. Together, these diagnostics mean that Pilot 2
established no transferable painter feature. The label-prediction result must not be promoted to
painter association under the relaunch definition, which requires source and content transfer
across held physical works.

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

For work \(w\), provider/workflow \(s\), independent capture \(r\) nested in \((w,s)\), delivery
derivative \(d\) nested in \(r\), and analysis branch \(p\):

\[
y_{wsrdp}=\theta_w+b_s+b_{r(w,s)}+b_{d(r)}+b_p+\varepsilon_{wsrdp}.
\]

This is an organizing hierarchical measurement model; interactions and heteroscedasticity are
tested rather than assumed absent. Provider, capture, and delivery terms are collapsed when the
prospective incidence/rank audit cannot identify them separately.

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

At every required transfer endpoint \(e\), each target-versus-hard-neighbor margin \(M_{a,h,e}\) on
the immutable panel-wide support must have a simultaneously calibrated lower confidence bound above
its frozen positive SESOI \(\delta_{a,h,e}\). A one-number representation is
\(T_{a,e}^{panel}=\min_{h\in H_a}\{M_{a,h,e}-\delta_{a,h,e}\}\), whose simultaneously calibrated
lower bound must exceed zero. The SESOI is subtracted before the minimum, so neighbor-specific
thresholds are preserved. A merely positive point estimate is diagnostic and cannot qualify a
painter-associated coordinate.

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

If separately authorized, the canonical painter-fidelity claim is conjunctive: items 1 through 6
must each pass their frozen criterion. A favorable prompt contrast or average cannot compensate
for failure of a conjunct.

1. **Absolute target fit/equivalence:** discrepancy between the generated set and eligible
   target-painter reference, decided against a frozen real-to-real scale and an equivalence or
   noninferiority margin. Failure to reject a difference is not evidence of fit.
2. **Hard-neighbor specificity:** the full target-versus-each-eligible-competitor margin vector on
   one panel-wide common support. Subtract each frozen neighbor/cell SESOI before aggregation; both
   the adjusted panel-worst \(\min_h\{S_{a,h}-\delta_{a,h}\}\) and adjusted lower-tail
   \(Q_{\tau}\{S_{a,h,q}-\delta_{a,h,q}\}\) statistics require simultaneous lower bounds above
   zero. Raw minima and quantiles are descriptive only.
3. **Precision and density:** both generated-to-real target-support criteria meeting their frozen
   simultaneous lower bounds.
4. **Recall and coverage:** both real-to-generated support criteria meeting their independently
   frozen simultaneous lower bounds.
5. **Content coherence:** absolute agreement, specificity, and support meeting the frozen
   cross-content robustness rule.
6. **Availability:** registered refusals/failures meeting the frozen availability and missingness
   robustness rule.
7. **Contraction:** mandatory generated dispersion relative to real within-painter dispersion,
   without an automatically favorable direction.
8. **Prompt movement:** mandatory named-versus-painter-free paired movement, which remains a
   mechanistic prompt-effect outcome rather than a fidelity substitute.

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
interaction. For each target, the target and its complete frozen hard-neighbor panel must share one
support and one set of weights. Pairwise-only supports cannot be combined into a panel minimum,
lower quantile, omnibus specificity decision, or canonical fidelity claim. Estimands are restricted
to the valid frozen support. A painter outside it may be described but cannot support broad
painter-specificity inference.

## 14. Claims allowed and prohibited

### 14.1 Allowed after the relevant gates

- file-level color, spatial, ordinal, or learned-appearance profile;
- reproduction-associated coordinate under the tested capture domain;
- painter-associated coordinate under declared source/content/phase/medium limits;
- human-perceived painterly similarity under a declared task and rater population;
- named-prompt movement under one frozen generator and prompt protocol;
- absolute target-distribution equivalence, panel-wide hard-neighbor specificity, precision and
  density, recall and coverage, content coherence, and availability as separate reported results
  and, only if every one passes, a conjunctive canonical painter-fidelity claim;
- contraction and prompt movement as mandatory nongating results that cannot rescue a failed
  fidelity conjunct.

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
- studies/painter_features_v1/old/VALIDATION_PROTOCOL.md
- studies/painter_features_v1/old/ANALYSIS_AND_CLAIMS.md

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

A fresh skeptical researcher reviewed exact committed states of
[PR #1](https://github.com/isingmodel/latent-art-bench/pull/1) from the standpoint of measurement
theory, causal identification, statistical inference, citation identity, and reproducibility.
The process retained criticism rather than silently editing it away:

| Pass | Exact committed range | Verdict | Public record |
|---|---|---|---|
| 1 | `612d09e4..c70589fc` | request changes | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370) |
| 2 | `c70589fc..e93a8ece` | request changes | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488825142) |
| 3 | `e93a8ece..f3497b7d` | request changes | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489036477) |
| 4 | `f3497b7d..9561a99f` | approve | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489144824) |
| 5 | `9561a99f..17ed93db` | request changes | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489200986) |

The first pass found no basis for treating the package as ready for empirical execution and
identified the material defects below. By the third pass, the reviewer had verified closure of all
original and second-pass defects in the authoritative protocols, but found two stale false-positive
paths and three P2 integrity problems elsewhere in the package. Report version 1.3 corrected them;
the fourth pass verified every P1 and P2 closed and approved exact head `9561a99f` at the
prospective design-framework level. Report version 1.4 incorporates the reviewer's one nonblocking
notation clarification without relaxing the approved per-neighbor rule. The fifth pass then found
that canonical Analysis G3 had not received the corresponding generated-output formula. Report
version 1.5 records and propagates that final P2 correction.

| Priority | Skeptical finding | Required disposition | Recorded response before final closure |
|---|---|---|---|
| P2 | Pilot 2's 0.50 balanced accuracy was promoted to painter-associated signal despite failed source transfer. | Name the result only as pooled artist-label predictability within the fixed Pilot 2 atlas; state that no transferable painter feature or generated-output effect was established. | Implemented; reviewer verification pending. |
| P1 | Kim A/C were promised as exact replications although the released artifact contract lacks the checkpoint/RNG/fixtures and A is not executable unchanged. | Permit only a source-faithful, versioned compatibility reconstruction; call every repaired A extractor an adaptation and keep C provisional until its artifact contract is recovered. | Narrative corrected; artifact-card verification pending. |
| P1 | Painter distributions were not restricted to identifiable joint common support, allowing painter to remain aliased with source, content, medium, and phase. | Freeze a connected painter-by-joint-nuisance support table, hard cell minima, at least two painters per confirmatory exchangeability cell, shared-support weights, and joint source-by-content transfer; narrow or fail claims outside support. | Pending protocol verification. |
| P1 | Generator and real-reference estimands wrote unqualified \(P_a\), silently dropping the conditioning variables in the construct definition. | Define a standardized target distribution over frozen common nuisance support or use exact matched contrasts; declare weights, source handling, and behavior outside support. | Pending protocol verification. |
| P1 | Multiplicity control was only within family even though the project selects among families, coordinates, scales, encoders, painters, and validation endpoints. | Freeze one primary omnibus claim or a hierarchical/closed-testing tree with strong error control, and reuse the same tree for external confirmation. | Pending protocol verification. |
| P1 | Canonical generated-painter claims omitted binding absolute fit/equivalence, hard-neighbor tail specificity, and generated-to-real support. | Require conjunctive success on absolute equivalence/noninferiority, the worst and lower-quantile hard-neighbor rules, precision and density, recall and coverage, content coherence, and availability; no nongating outcome may rescue a failed conjunct. | Revised twice; final reviewer verification pending. |
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

### 18.1 Third-pass residuals and response

| Priority | Third-pass finding | Revision in report version 1.3 | Status |
|---|---|---|---|
| P1 | Review 05 retained unstandardized references, worst **or** lower-tail specificity, and an incomplete generated-success rule. | Rewrote it around one immutable target-plus-all-hard-neighbors support/weight system, prohibited pairwise aggregation, required both specificity rules, and used the canonical six binding plus two mandatory nongating outcomes. | Fourth pass verified closed. |
| P1 | Validation Gate 4 allowed real painter qualification from sign-only hard-neighbor margins. | Required, at every transfer endpoint, simultaneous lower bounds above frozen positive SESOIs for every neighbor; sign alone is diagnostic. | Fourth pass verified closed. |
| P2 | Review 05 permitted confirmatory FDR. | Reserved FDR for exploratory coordinates that cannot qualify a method or support a project-level claim; retained strong experiment-wide FWER for all confirmatory decisions. | Fourth pass verified closed. |
| P2 | Human gate H9 could be read as standalone generative success. | Restricted H9 to human prompt-movement evidence for G2 and stated that it cannot establish canonical fidelity or rescue any failed conjunct. | Fourth pass verified closed. |
| P2 | PF023 and PF029 had wrong short-citation author labels. | Corrected them to Qi, Taeb, and Hughes and to Redies and Brachmann, including the corresponding thematic-review label. | Fourth pass verified closed. |
| P3 | The living skeptical-review file showed only one reviewed range and called its edited prose immutable. | Added an exact pass table and located immutability in Git history and the linked public comments. | Fourth pass accepted. |

### 18.2 Fourth-pass verdict and nonblocking clarification

The [fourth-pass approval](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489144824)
states that no P0-P2 finding remains. It does **not** qualify a coordinate, establish an empirical
painter feature, or authorize acquisition, extraction, holdout access, transport, or generation.

The reviewer made one P3 notation suggestion: when hard neighbors have different SESOIs, an
unadjusted minimum margin is not interchangeable with testing every margin against its own
threshold. The final protocol therefore defines

\[
T_{a,e}^{panel}=\min_{h\in H_a}\{M_{a,h,e}-\delta_{a,h,e}\}
\]

and requires its simultaneous lower bound to exceed zero. Review 05 applies the corresponding
subtract-before-aggregation rule to both generated worst and lower-tail specificity summaries.
This makes the approved fail-closed rule explicit; it does not weaken it. The final closure-only
commit receives a narrow exact-head check recorded externally on PR #1 so that recording the check
does not create an endless sequence of new metadata commits.

### 18.3 Fifth-pass generated-rule alignment

The reviewer inspected exact head `17ed93db2f5b5f3282a4cd2af9cc8756c9648690` and posted one
[P2 request for changes](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489200986).
The real Gate 4 formula, review provenance, QA record, and all previous P0-P2 closures remained
sound. The sole defect was that canonical Analysis G3 still bound raw generated minima and
quantiles against aggregate SESOIs while review 05 correctly subtracted heterogeneous
neighbor/cell SESOIs before aggregation.

Analysis protocol 1.3 now defines

\[
T_a^{worst}=\min_{h\in H_a}\{S_{a,h}-\delta_{a,h}\},\qquad
T_a^{tail}=Q_{\tau}\{S_{a,h,q}-\delta_{a,h,q}\}.
\]

Both require simultaneous lower bounds above zero; raw minima and quantiles are descriptive only.
Validation protocol 1.5, the synthesis, method-decision ledger 1.3, review 05, and report 1.5 now
state the same rule. The final exact-head decision is recorded externally on PR #1.

## 19. Quality assurance record

At initial report creation:

- the evidence matrix parsed as a valid 11-column CSV;
- all 138 source IDs were unique;
- evidence-grade and disposition counts reconciled to 138;
- no absolute user path appeared in the new research artifacts;
- no unresolved drafting marker appeared in the protocols or reviews; and
- the project remained documentation-only, with no artwork, model, or generated-image operation.

After the fourth-pass approval and final P3 clarification, the evidence-bearing workspace passed:

- `git diff --check` on the closure revision;
- a valid 138-row, 11-column evidence matrix with 138 unique source IDs and 138 unique stable
  identifiers;
- the reconciled review-depth, evidence-grade, and disposition totals;
- 201 bibliography entries, 201 links, and 201 unique links;
- all 102 DOI-keyed matrix-to-bibliography joins after URL decoding;
- the corrected Qi–Taeb–Hughes and Redies–Brachmann identities across the matrix, bibliography,
  and thematic review;
- all repository-local Markdown links, with no absolute user path or unresolved drafting marker;
- targeted assertions for immutable panel support, both hard-neighbor rules, six binding outcomes,
  exploratory-only FDR, G2-only H9, and subtract-before-aggregation SESOI statistics;
- `uv run --locked ruff check .`; and
- `uv run --locked pytest -q -m "not live"`: **490 passed in 50.02 seconds**.

The skeptical reviewer independently passed diff, matrix, identity, DOI, link, and Ruff checks at
approved head `9561a99f`. Its isolated exact-commit checkout reported 487 passed and one skipped;
the only two failures required the intentionally uncommitted historical Lee PDF. The local
evidence-bearing workspace retains that byte and passed all 490 tests. The project does not mask
the clean-checkout limitation by altering frozen historical evidence or committing the ignored
PDF.

The final closure commit contains documentation, the adjusted-SESOI clarification, and the
fifth-pass propagation fix only. Its narrow exact-head reviewer confirmation is kept in the public
PR record rather than added recursively to this file. No empirical operation occurred during QA
or review.

## 20. Concrete execution and change ledger

This section is the audit-oriented account of what was actually done. It fixes the scope,
inputs, transformations, outputs, review iterations, and non-actions at named repository states.
It adds reporting detail only; it does not change the approved construct, measurement candidates,
validation gates, estimands, thresholds policy, or authorization boundary described above.

### 20.1 Exact repository scope

| Item | Concrete state |
|---|---|
| Historical baseline used for the relaunch | main at 612d09e4c84e4b34eed769455c569b93864d2b53, the commit recording the terminal Pilot 3 Met R2 metadata denial |
| Relaunch branch (merged) | codex/relaunch-literature-methods |
| Reporting follow-up branch | codex/painter-feature-full-report |
| Approved methodological head before this reporting expansion | 88e14efff48fe4350bf6891444bf01645040deec |
| Merged methodological pull request | [PR #1, Relaunch painter-feature measurement research](https://github.com/isingmodel/latent-art-bench/pull/1), merged 2026-09-01 08:30:59 UTC into main as ad2417e11ae42ceec3b3c26f8388e8d4e767d07d |
| Research classification | Newly versioned prospective design framework under painter_features_v1 |
| Historical boundary | Pilots 0–3 read as evidence and left unchanged |
| Change type through approved head | Documentation and structured research evidence only; no source-code, configuration, test, model, artwork, or generated-image change |
| Scoped output at approved head | 20 new tracked research files, 5,929 lines, and 59,246 whitespace-delimited words relative to historical baseline 612d09e |

The worktree also contained pre-existing documentation and configuration edits outside this
research package; none was staged as relaunch work. Two untracked local governance files,
docs/STATUS.md and docs/ARTIFACTS.md, were read for task-start operational safety. Neither exists
at the historical baseline, approved methodological head, or merge commit, so neither is counted
below as commit-reconstructable research evidence or support for a scientific claim. Ignored
artwork, model, source-checkout, generated-output, and historical PDF bytes were preserved. No
broad cleanup command was used.

### 20.2 Repository evidence reconstructed before designing the method

| Evidence input | Exact material inspected | Facts taken forward | Design consequence |
|---|---|---|---|
| Pilot 2 registered intent | docs/PILOT_2_PROTOCOL.md and configs/pilot_2/pilot.yaml | Painter was the target; the design crossed four painters, two sources, and registered named-versus-control generation cells | Kept painter, not era or movement, as the scientific target |
| Pilot 2 real corpus and split | configs/pilot_2/manifests/atlas.jsonl, configs/pilot_2/manifests/real_images.jsonl, and reports/pilot_2/analysis.json | 40 works = 4 painters × 2 sources × 5 works; 24 training and 16 held works | Defined the new construct across held physical works and required crossed nuisance support |
| Pilot 2 method and qualification | configs/pilot_2/qualification/learned_formal.json and reports/pilot_2/evidence/learned_formal_qualification.json | The project used an adapted Kim A-vector, fitted PCA only on real training works, and retained 22 components against a centered training-data rank cap of 23 | Treated the vector as a high-dimensional appearance diagnostic rather than an isolated painter feature |
| Pilot 2 real-only outcomes | reports/pilot_2/evidence/learned_formal_qualification.json | Pooled painter balanced accuracy was 0.50; source balanced accuracy was 0.8125 on a different task; opposite-source painter accuracies were 0.25 and 0.375 | Restricted the positive statement to pooled artist-label predictability within the fixed atlas and made source/content transfer gating |
| Pilot 2 generation closure | reports/pilot_2/evidence/generation_completion.json, generation_attempt_receipts.json, generation_gate.json, and successful_output_manifest.json | 320 cells were assigned, 315 succeeded, and five terminal refusals made both requested-label grids incomplete | Preserved the missing cells, did not rerun or impute them, and stated that no generated-output effect was established |
| Pilot 3 boundary | docs/PILOT_3_R2_OFFICIAL_MET.md, reports/pilot_3/evidence/met_r2_authorization.json, and artifacts/pilot_3/met_r2_metadata_attempts.jsonl | The first official Met R2 metadata request returned terminal HTTP 403 and closed that cohort | Did not use Pilot 3 as a source of new images or features and did not invent a fallback |

This reconstruction was interpretive research work, not a rerun of the historical studies. The
historical numerical records were read and reconciled; their hash-bound protocols, ledgers,
receipts, and outputs were not regenerated.

### 20.3 Literature work performed

The literature work proceeded in five concrete stages:

1. Seeded the search from repository references and the methods cited by Pilots 2 and 3.
2. Ran targeted searches across quantitative art history, interpretable image measurement,
   learned art representations, digitization validity, human construct validity, generative-set
   evaluation, memorization, missingness, and confirmatory inference.
3. Resolved search leads to primary papers, publisher pages, official standards, repositories,
   or model/data artifacts before using them as evidence.
4. Extracted a compact source-level record into the 11-column evidence matrix and wrote deeper
   method-family critiques for sources that changed the proposed protocol.
5. Reconciled identities, DOI joins, method descriptions, dispositions, and downstream protocol
   consequences, then ran a final four-cluster search pass.

Discovery and verification used repository references, targeted web search, OpenAlex, DOI and
publisher pages, PMC, CVF Open Access, PMLR, OpenReview, official ISO/FADGI/Metamorfoze pages,
primary GitHub repositories, and backward/forward citation chaining. The exact reconstructable
queries and the distinction between literal query strings and grouped traversals are retained in
literature_reviews/SEARCH_LOG.md.

The auditable endpoint was:

| Audit quantity | Result | Interpretation |
|---|---:|---|
| Evidence-matrix rows | 138 | Unique included source/standard/artifact records with one protocol consequence each |
| Matrix columns | 11 | id, year, citation, stable identifier, cluster, depth, evidence, limitation, grade, disposition, consequence |
| Bibliography entries | 201 | Unique primary, official, artifact, statistical, foundational, or marked background entries |
| DOI-keyed matrix rows joined to bibliography | 102/102 | Identity join after URL decoding |
| Full-text reviews | 121 | Main review-depth category |
| Methods-and-results reviews | 10 | Used when that was the verified accessible depth |
| Full-text-plus-code audits | 3 | Includes exact released-code inspection |
| Official standards/guidelines | 3 | One standard and two guidelines |
| Abstract-only records | 1 | Kept explicitly labeled rather than upgraded by inference |
| Evidence grades | A 31; B 74; C 32; D 1; X 0 | Grade is fitness for the proposed project use, not paper prestige |
| Prospective dispositions | core 37; secondary 41; diagnostic 38; background 19; reject 3 | No disposition itself qualifies a coordinate |
| Final search-pass additions | 4/138 = 2.9% | Descriptive only; no new method family, but not proof of saturation |

The audit did more than collect citations. Examples of source-specific corrections that changed
the research record include:

| Matrix record | Concrete correction | Consequence |
|---|---|---|
| PF001 | Separated RGB color-use ranks, occupied-gamut box counts, grayscale roughness, and weighted entropy instead of calling them a generic color feature | Retained only source-faithful historical baselines and required new source/scale qualification |
| PF003 | Recorded a three-painting, eight-template color-interaction study rather than evidence of painter specificity | Kept multiscale partition logic diagnostic only |
| PF006 | Identified the corpus as contemporary DeviantArt/Behance user-generated visual art | Prevented transfer of its platform-level result to historical-painter qualification |
| PF007 | Recorded the tie-aware 75-state two-by-two ordinal distribution and 11 smoothness groups | Retained full distributions and explicit tie/scale perturbations rather than only entropy scalars |
| PF017 | Corrected the method to learned sparse coding with kurtosis, not a wavelet painter feature | Reclassified it as a learned diagnostic requiring independent work-level validation |
| PF020 | Corrected the method to iterative grayscale region growing with shape constraints, not wavelet analysis or literal physical-stroke measurement | Required scale evidence and human annotation before any visible-mark claim |
| PF023 | Corrected the short-citation identity to Qi, Taeb, and Hughes | Reconciled the matrix and thematic review |
| PF026 | Recorded windowed two-dimensional Fourier power slope and anisotropy, including the authors' necessary/sufficient limitation | Prevented an aesthetic-quality or painter claim from category-level spectra |
| PF027 | Recorded PHOG-derived complexity, self-similarity, and anisotropy | Required fixed pyramid settings and content/source/reproduction tests |
| PF029 | Corrected the short-citation identity to Redies and Brachmann | Removed a cross-document author mismatch |
| PF030 | Replaced “reproduction invariance” with the narrower absence of a significant aggregate group difference | Required paired same-work equivalence/repeatability tests |
| PF041 | Marked hyperspectral color statistics as a modality boundary, not evidence recoverable from ordinary catalog RGB | Prohibited physical-surface inference from RGB |

The literature result is deliberately not called exhaustive, saturated, systematic, or
prospectively registered. No stable export, complete returned-hit manifest, deduplicated screening
file, per-record exclusion ledger, or pre-search timestamped protocol exists. Returned, screened,
and excluded denominators therefore were not reconstructed after the fact. The defensible
quantity is the 138-record structured endpoint plus the 201-entry bibliography.

### 20.4 Pilot 2 calculations and their use

The Pilot 2 audit separated arithmetic facts from scientific interpretations:

| Calculation or record | Exact result | What it supports | What it does not support |
|---|---:|---|---|
| Real-corpus cells | 4 painters × 2 sources × 5 works = 40 works | A small crossed historical atlas | Oeuvre-level coverage |
| Real split | 24 train; 16 held | A held-work pooled diagnostic | External institution or phase/content transfer |
| Held painter task | balanced accuracy 0.500 | Artist-label predictability inside the fixed atlas | A transferable painter feature |
| Painter recalls | Monet 0.250; Pissarro 0.250; Sisley 0.750; Cézanne 0.750 | Descriptive recall spread with four held works per painter | Uniform painter performance |
| Held-by-source painter results | AIC 0.625; NGA 0.375 | Source-stratified diagnostic variation | A source-invariant effect |
| Separate source task | balanced accuracy 0.8125 | Descriptive provider/source-label predictability in the 16 held works | A directly rankable advantage over the four-class painter task |
| Opposite-source painter transfer | NGA→AIC 0.250; AIC→NGA 0.375 | Failure to show convincing source transfer | Confound-resistant painter association |
| Constrained permutation | p = 0.0216 | The observed pooled statistic's tail probability under the constrained permutation scheme | Independence from source/content or a large/stable effect |
| PCA geometry | 22 components from 24 real training works against centered rank cap 23; cumulative variance 0.9707404656 | Nearly saturated training geometry | Meaningful low-dimensional regularization |
| Generation completion | 320 assigned; 315 successful; 5 terminal refusals | Exact availability record and nongating complete-pair descriptive estimates | The four registered confirmatory primary tests, which were not run |

Pilot 2 did compute four available-complete-pair descriptive estimates before withholding
confirmation:

| Requested model label | Descriptive estimand | Estimate | Confirmatory status |
|---|---|---:|---|
| gpt-image-1 | Target improvement | 8.6492391997 | Not tested: incomplete feature grid; no confidence interval or exact sign-flip p-value |
| gpt-image-1 | Specificity difference-in-differences | 5.6107138440 | Not tested: incomplete feature grid; no confidence interval or exact sign-flip p-value |
| gpt-image-2 | Target improvement | 9.9262685683 | Not tested: incomplete feature grid; no confidence interval or exact sign-flip p-value |
| gpt-image-2 | Specificity difference-in-differences | 6.5012713053 | Not tested: incomplete feature grid; no confidence interval or exact sign-flip p-value |

These positive descriptive values are not four tested effects. Their analysis population is
explicitly available_complete_pairs_descriptive; the familywise lower bounds are absent and every
test status is not_tested_incomplete_feature_grid. They therefore do not change the REDESIGN
decision or establish a generated-output effect.

The new method responds directly to those observations: it requires several hard-neighbor
comparisons, common nuisance support, source-workflow-level method selection, leave-source and
leave-content transfer, independent reproductions, and separate coverage/contraction assessment.
It does not reinterpret the permutation p-value as proof that these requirements were met.

### 20.5 Kim paper and artifact audit performed

The Kim audit covered the 2026 PNAS paper, supplement, artifact references, and exact released
repository revision 7da12358cf34dad2184f357a048c2cf114b3c4e0.

| Audit question | Concrete finding | Research decision |
|---|---|---|
| Corpus | 72,447 Western paintings, 2,354 painters, 128 conventional styles, dates 1500–1990, derived from heterogeneous ART500K sources | Treat reported predictions as corpus/split-specific and require physical-work/source/capture controls locally |
| A preprocessing | OpenCV load/channel path; forced 512 × 512 Lanczos square; write under original extension; Pillow RGB reload; map to −1…1 | Record interpolation, warp, codec, channel, and derivative effects in the artifact contract |
| A representation | Sample SD2 first-stage VAE posterior, scale it, and flatten 4 × 64 × 64 to 16,384 values | Name it an SD2-VAE appearance coordinate, not a formal or painter feature |
| A reproducibility | Released script has unreachable initialization, an undefined module-level model reference, and author-local paths; checkpoint hash, RNG state, extracted vectors, fixture, and full environment are absent | Exact reproduction is unsupported; any executable repair is an adaptation |
| C representation | CLIP Interrogator ViT-H-14/laion2b_s32b_b79k, 1,024 dimensions, read from the original path rather than A's square derivative | Keep it separate as a contextual/semantic diagnostic with a provisional artifact contract |
| Published prediction | A/C year \(R^2\) 0.2024/0.8687; year correlation 0.4505/0.9324; ten-painter balanced accuracy 0.3268/0.8226; ten-style balanced accuracy 0.2507/0.7495; artist-disjoint year \(R^2\) 0.189/0.850 | Accept predictive signal under the paper's splits, but not source invariance, painterly construct validity, or oeuvre coverage |

No A or C vectors were extracted in this relaunch. The work product is an artifact and claim
audit plus a protocol for a future compatibility reconstruction, should a separate execution
freeze authorize it.

### 20.6 How the proposed painter-feature method was built

The method was assembled as a chain from observed failure mode to a binding prospective control:

| Observed problem or evidence | Binding design response | Canonical location |
|---|---|---|
| A single image or centroid cannot represent a changing oeuvre | Define the target as a standardized conditional distribution across eligible physical works | Measurement protocol construct definition; MD-01 and MD-31 |
| Painter can be aliased with source, content, medium, and phase | Freeze one connected joint common-support table, hard cell minima, at least two painters per exchangeability cell, and one target-plus-all-hard-neighbors weighting system | Measurement protocol corpus tables; Validation Gate 4; MD-06, MD-19, MD-31 |
| Provider, capture, and delivery can be nested, while uncrossed processing choices can create a separate confound | Freeze the provider/capture/delivery incidence matrix, require bridges and a rank audit, and cross every deterministic processing branch over every eligible reproduction; collapse only unidentified provider/capture/delivery effects into a narrowed source/capture-workflow term | Measurement protocol observation model; MD-32 |
| Interpretable coordinates can still be reproduction-sensitive | Qualify CIELAB/transition, Fourier/edge, wavelet, ordinal, and composition candidates through repeatability, perturbation, capture, source, and content gates | Measurement and validation protocols; MD-07 through MD-10 |
| Learned coordinates inherit training objectives and exposure | Label Kim A, Kim C, CSD, ALADIN/CLIP/DINO/Gram/diffusion spaces separately and use unqualified spaces only diagnostically | Synthesis and method ledger; MD-12 through MD-16 |
| Pooled artist classification can exploit shortcuts | Require outer source-workflow nested selection and simultaneous hard-neighbor margins above neighbor-specific SESOIs at every transfer endpoint | Validation Gate 4; MD-18 and MD-34 |
| Same-work retrieval can reward content or unique defects | Make retrieval diagnostic; gate paired-capture stability of painter margins and painter-profile geometry | Validation Gate 3 |
| Human judgments can use labels, signatures, source UI, familiarity, or content | Blind labels/source/condition, freeze signature/text masking, measure recognition after judgment, and make unfamiliar works primary | Validation Gate 5; MD-24, MD-25, and MD-35 |
| One favorable family or endpoint can be selected after inspection | Freeze a primary omnibus/closed-testing hierarchy with strong experiment-wide FWER; use FDR only for labeled exploration | Analysis protocol multiplicity tree; MD-33 |
| Missing complete cases can create an easier corpus | Freeze denominators and minima, report differential selection, and require registered MNAR bounds/tipping analyses | Analysis protocol missingness rules; MD-26 and MD-37 |
| Relative prompt movement can improve while outputs remain wrong or collapsed | Make later success conjunctive on absolute fit; adjusted worst and tail panel specificity; precision and density; recall and coverage; content coherence; and availability | Analysis G1–G8, Validation Gate 7, and MD-19, MD-20, MD-22, MD-23, MD-38 |
| Shared controls and real references induce dependence | Resample the whole content/model/version/path/seed bundle and joint real-reference structure | Analysis resampling unit; MD-39 |

The validation sequence is explicitly fail-closed:

1. Gate 0 fixes construct and artifact identity.
2. Gate 1 tests computational repeatability.
3. Gate 2 tests controlled perturbation response.
4. Gate 3 tests independent-reproduction reliability.
5. Gate 4 tests real-only painter specificity and source/content transfer.
6. Gate 5 tests human convergent and discriminant evidence.
7. Gate 6 uses an unopened institution/capture workflow for external confirmation.
8. Gate 7 freezes every later generated-image estimand and stopping rule before generation.

At real Gate 4, every required painter–neighbor–endpoint margin must exceed its own frozen
positive SESOI using simultaneous lower confidence bounds. With heterogeneous thresholds, the
panel statistic is formed after subtraction:

\[
T_{a,e}^{panel}=\min_{h\in H_a}\{M_{a,h,e}-\delta_{a,h,e}\}.
\]

For a later generated study, the adjusted worst and lower-tail specificity summaries are:

\[
T_a^{worst}=\min_{h\in H_a}\{S_{a,h}-\delta_{a,h}\},\qquad
T_a^{tail}=Q_{\tau}\{S_{a,h,q}-\delta_{a,h,q}\}.
\]

Both require simultaneous lower bounds above zero. Raw minima and quantiles are descriptive.
Prompt movement and contraction must be reported but cannot rescue failure of any of the six
binding outcome families.

### 20.7 Concrete deliverables produced

At the approved methodological head 88e14ef, the branch contained the following scoped output:

| Package | Files | Lines | Concrete function |
|---|---:|---:|---|
| Literature evidence backbone | 7 | 1,184 | Review boundary, retrospective search protocol/log, 138-row matrix, 201-entry bibliography, cross-family synthesis, and 39 method decisions |
| Critical reviews | 6 | 1,798 | Pilot 2 audit plus interpretable, Kim/learned, digitization, human-validity, and distribution/missingness reviews |
| Prospective design framework | 4 | 1,317 | Study boundary, measurement design, eight validation gates, and confirmatory analysis/claims architecture |
| Process and skeptical-review record | 3 | 1,630 | Full research report, living skeptical review, and finding-by-finding response |
| **Total** | **20** | **5,929** | **One linked, documentation-only research package** |

Section 16 lists every file at that historical head. At that stage, the evidence matrix was the
source-level disposition authority, the thematic reviews supplied method detail, the synthesis
compared families, the method ledger fixed prospective decisions, and three study documents
jointly formed the design framework. That multi-document arrangement was later retired. The
current sole canonical plan is the version 2.0 measurement protocol named at the top of this
report; the two predecessor study documents now live under `studies/painter_features_v1/old/`.

### 20.8 Git and skeptical-review revision history

| Commit | Concrete work recorded | Skeptical outcome |
|---|---|---|
| c70589fc7ff92e62e4d1fefd1df8e6f4ffa417c9 | Created the 18-file initial evidence and design package: 4,655 inserted lines | First pass requested changes: 7 P1 and 10 P2 findings |
| e93a8ece83a14924cafcd6bfe5a1d92640c36c48 | Added common support, conditioned estimands, strong multiplicity control, generated conjunction, reproduction identification, citation repairs, Kim adaptation language, human/source/missingness controls, and retrospective-search limits | Second pass retained two P1, two partial P2, and one residual P2 |
| f3497b7d0d376b1a581b2701dec74892fe6af6b7 | Bound one panel-wide support, reconciled the generated-success rule, removed cross-task accuracy ranking, corrected the evidence-schema promise, and expanded the observation hierarchy | Third pass verified canonical closures but found two stale P1 paths and three P2 consistency defects |
| 9561a99f741e04216279d34183993f25985ac289 | Fixed review 05, made positive neighbor-specific SESOIs binding at Gate 4, restricted FDR to exploration, limited H9 to G2, and corrected PF023/PF029 identities | Fourth pass approved; no P0–P2 remained |
| 17ed93db2f5b5f3282a4cd2af9cc8756c9648690 | Incorporated the nonblocking heterogeneous-SESOI notation clarification and improved exact-pass provenance | Fifth pass found one P2: Analysis G3 had not received the generated subtract-before-aggregation rule |
| 88e14efff48fe4350bf6891444bf01645040deec | Propagated adjusted generated worst/tail statistics through Analysis, Validation, Synthesis, review 05, method decisions, response, skeptical record, and this report | [Exact-head approval](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489256222): no P0, P1, or P2 remained at the design-framework level |

The reviewer was instructed to act as a professional skeptical researcher, not as a friendly code
reviewer. It checked construct validity, causal identification, sampling support, reproduction
effects, statistical dependence, multiplicity, missingness, source identity, artifact
reproducibility, and claim ceilings. Each request-changes verdict was followed by a new exact-head
inspection; no failed review was silently replaced by a different goal.

After that exact-head approval, PR #1 was merged as ad2417e11ae42ceec3b3c26f8388e8d4e767d07d.
Report version 1.6 is a reporting-only follow-up to the merge; it does not reopen or alter any
approved methodological rule.

### 20.9 Verification performed

QA occurred at different repository states and by different actors. The records are not
interchangeable:

| Actor and exact state | Concrete check | Result |
|---|---|---|
| Local evidence-bearing workspace recorded in report 1.5 | git diff check; matrix/count/DOI/link/identity/method-invariant audits; Ruff | Passed |
| Same local method-closure workspace | uv run --locked pytest -q -m "not live" | 490 passed in 50.02 seconds |
| Skeptical reviewer at exact head 9561a99f | Diff, 138×11 matrix, unique ids, 102 DOI joins, 36 non-DOI identities, local links, and Ruff | Passed |
| Same reviewer in an isolated 9561a99f checkout | Offline suite without the ignored historical Lee PDF | 487 passed, 1 skipped, 2 historical-evidence-dependent failures |
| Closing exact-head reviewer at 88e14eff | Incremental and cumulative diff checks, adjusted G3 assertions, 138×11 matrix identity checks, and scoped local links | Passed; the reviewer explicitly did not rerun Ruff or the suite for this documentation-only range |
| Local pre-commit report-1.6 pass on codex/painter-feature-full-report | git diff check; matrix structure/counts; 201 unique bibliography links; 102/102 DOI joins; scoped paths and local links; hygiene markers; named report inputs; Ruff | Passed |
| Same local report-1.6 pass | uv run --locked pytest -q -m "not live" | 490 passed in 52.98 seconds |

The two isolated-checkout failures were reported rather than “fixed”: they require a unique
ignored historical PDF still present in the evidence-bearing workspace. Committing that
copyrighted/local evidence or refreshing frozen hashes would have crossed the artifact boundary.

### 20.10 What was deliberately not done

This relaunch did not:

- implement a production feature extractor;
- download or alter model weights;
- acquire or normalize a new artwork;
- open the sealed external holdout;
- extract a Pilot 3 or painter_features_v1 feature;
- repair and run Kim's released A-vector code;
- rerun Pilot 2 refusals or run the withheld confirmatory primary tests;
- retry the terminal Pilot 3 Met R2 request or substitute a provider;
- contact a generation service or create an image;
- fit a painter classifier or estimate a new painter distribution;
- declare a coordinate qualified;
- claim a systematic-review screening denominator that was not retained;
- call the design framework executable or preregistered; or
- modify frozen protocols, ledgers, hashes, receipts, or historical reports.

The concrete result is therefore a reviewed research foundation and decision system, not an
empirical painter-feature estimate. The next authorized work product is a separate real-only
execution-freeze artifact fixing the painter set, eligible-work frame, common-support and
provider/capture incidence tables, independent reproductions, exact feature cards and artifact
versions, simulations, minima, SESOIs, multiplicity tree, missingness actions, rights, storage,
and external-confirmation partition. Only after that artifact is independently reviewed and
committed can acquisition or measurement be considered.
