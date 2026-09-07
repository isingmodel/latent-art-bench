# Methodology review and revision plan

Date: 2026-09-07. Reviewed research commit:
`744d7f779b0698ed8b9b384157894b341b432ccd`.

**Decision: major scientific revision before submission.** The completed study
provides reproducible evidence about finite image collections in a specified
feature space. It does not yet isolate painter-style fidelity, perceptual loss of
variation, or general failure to reproduce artists' distributions. The strongest
remaining result is the controlled painter-name intervention on the paid routes.
Preserve it, with its conditional inferential scope, while investigating the
measurement and reference alternatives below.

This is a maintainer-run review by three LLM subagents and the coordinating LLM,
not independent human or institutional peer review. Shared model/context biases
remain possible; agreement between agents is not external validation. The agents
reviewed distinct aspects of the protocol, implementation, evidence and manuscript:

- [Statistics and inference](statistics.md).
- [Data, design and provenance](data_design.md).
- [Measurement, constructs and publication claims](measurement_claims.md).

The coordinator checked critical findings against source and retained numeric
records, independently reproduced geometry counts and variance decomposition,
checked prompt-payload identity, and adjudicated a mistaken resolution-field
interpretation. This review reads already measured values and metadata. It does
not acquire, decode, remeasure or generate images, replace sealed results, or
implement the proposed scientific revision. All new diagnostics below are
explicitly post-result review calculations, not newly confirmatory endpoints.

## What survived the review

The reviewers found no confirmed arithmetic error in the weighted V-energy
calculation, its paired sign-swap identity, Monte Carlo p-value correction, or
Holm adjustment. The fixed classifier implementation keeps original works and
generated briefs disjoint under its whole-brief split. Fixed kernels can be
computed for all rows before selecting train/test blocks without fitting to test
outcomes; that operation alone is not leakage. Separate development scaling,
preserved failures, exact request records and premeasurement freezes are useful
strengths. The reviewed chronology supports a prospective main calculation,
although historical outcomes informed painter selection and later execution
amendments changed the realized schedule.

There are 72 independently randomized pairs for most prompt contrasts. Reusing
24 briefs does not by itself invalidate a randomization test conditional on those
briefs under the specified sharp null. Replacing its signs with arbitrary
brief-level or window-level permutations would change the assignment design and
is not an automatic repair. Population inference over new briefs, paintings or
service sessions is a different problem.

The published numerical tables remain evidence. The review does not establish
that shape, capture or a particular feature caused their observed values. It
establishes that the current design cannot exclude important alternative
explanations for a stronger style interpretation. No fabricated observations,
selective regeneration of successful images, or new freeze-hash mismatch was
identified by this review; that is a bounded review result, not proof that every
possible error has been excluded.

## Ranked findings and their consequences

Severity here refers to the claim being pursued, not a software bug classification.
R1–R6 block a strong style/distribution-generalization claim; they do not erase
the literal finite-feature observations. Details and source-line evidence are in
the three supporting reviews, against the reviewed commit.

### R1. Geometry and acquisition history are uncontrolled domain differences

**Confirmed design limitation.** None of the 70 reference images is square;
all 576 paid-route outputs are square. A square/non-square metadata rule therefore
perfectly distinguishes these two domains. Aspect ratio is not an explicit input
to the 31-feature classifier: this is not proof of what that classifier uses.
However, common-short-side normalization preserves the mismatch, and spatial and
frequency measurements have not been shown invariant to it. All paid within-route
named/free images share square geometry, so this finding is less damaging to
that intervention than to absolute original/generated detection.

There are no verified independent photographic capture pairs. Four reference
annotations retain dark perimeters, while every prompt prohibits frames and
signatures. Shared JPEG re-encoding does not undo pre-existing reproduction
history. More references with the same confounding cannot solve this merely by
increasing N. An exact-square original subset is empty: cropping or patching would
change the comparison target, not provide a matched version of the original one.

Evidence: [normalization and features](../../../src/latent_art_bench/painter_feature_generation_v2/features.py),
lines 42–87 and 137–208; MC1/MC4 in the measurement review; retained primary
normalization metadata in the reference and generated feature ledgers.

### R2. The reference frame is small, selective and incompletely content matched

**Confirmed design limitation.** The fresh panel contains 38 Monet works
(water/built/land 21/4/13) and 32 Cézanne works (3/11/18); 17 of 70 labels are
mixed or uncertain. Eligibility/content coding was performed by one maintainer
LLM, without independent human agreement. Freshness is relative to recorded
exposure indexes, not a probability sample of an oeuvre or assurance of absence
from model training. Excluding already exposed works and requiring successful
delivery changes the accessible reference frame.

Generated class labels describe the intended prompt, whereas original labels
describe viewed paintings. Actual generated adherence and fine subject,
composition, period and viewpoint support are not established. Reweighting three
class masses cannot equate those variables. Conversely, excluding generated
images after seeing poor adherence would select on a treatment outcome and would
not automatically identify a pure style effect.

The native-1024 sensitivity leaves Monet with only two water and two land works,
and **no built works**. Its reversal changes identities and class support together
with the resolution restriction; it is not an isolated resolution experiment.

Evidence: [main contract](../../../studies/painter_distribution_study_v1/MAIN.md),
lines 7–39; [variant implementation](../../../src/latent_art_bench/painter_distribution_study_v1/analysis.py),
lines 61–78; data review and MC4.

### R3. The aggregate metric is a choice of weighting, not a validated style instrument

**Confirmed measurement limitation.** Three coordinates summarize coordinates
already included: deltaE slope, wavelet slope and wavelet curvature. The last two
are linear functions of the four included wavelet energies. Median/IQR scaling
does not remove this repeated weighting or equalize conceptual information.
Eleven color, eight spatial and twelve texture dimensions receive one Euclidean
coordinate each. Texture accounts for approximately 49.01% of original Monet
trace and 47.13% of Cézanne trace after scaling.

This is a mathematically valid frozen metric. It is not evidence for 31
independent style measurements. Strong texture contraction and several expanding
spatial results mean the aggregate cannot stand for uniform narrowing. Distances,
PCA, coverage and detection reuse the same representation and do not supply four
independent validations of style.

Evidence: [feature definitions](../../../src/latent_art_bench/painter_feature_generation_v2/features.py),
lines 17–29, 121–130 and 183–208; MC2/MC3. No human validation or complementary
learned representation has been executed. Adding an embedding alone would not
turn it into a ground-truth evaluator.

### R4. Lower total variance does not imply lower variation for a fixed prompt

**Confirmed interpretation limit, with a new numeric review diagnostic.** Using
the primary scaler and each painter's reference content masses, decompose trace
as within-brief trace plus trace of brief means. The named/free ratios are:

| Route | Painter | Total trace | Within brief | Between brief means |
|---|---|---:|---:|---:|
| Nano Banana 2 | Monet | 0.696695 | 0.749157 | 0.684916 |
| Nano Banana 2 | Cézanne | 0.466240 | 0.785999 | 0.377645 |
| FLUX.2 Max | Monet | 0.330788 | 0.308776 | 0.337287 |
| FLUX.2 Max | Cézanne | 0.460412 | 0.488603 | 0.450693 |
| OAuth GPT Image 2 service | Monet | 0.553786 | 0.869789 | 0.511545 |
| OAuth GPT Image 2 service | Cézanne | 0.651325 | **1.139095** | 0.583099 |

These compare generated named/free collections, not generated/original spread.
With three repetitions per brief, the within-brief values are empirical summaries
with limited replication. The OAuth Cézanne case directly contradicts a uniform
interpretation as reduced repeat-to-repeat variation. It does not contradict the
published lower aggregate trace. The decomposition locates observed variation;
it does not identify an internal model mechanism.

Reproduction recipe: transform the retained `primary512` generated vectors with
the unchanged primary scaler; give each image its class mass divided by its class
count; compute the weighted global mean and weighted brief means. Sum weighted
squared residuals around brief means for within-brief trace, and subtract it from
total weighted trace for the between-brief term. All six named/free comparisons
have full 72-image support. The coordinator and statistics reviewer independently
reproduced these values. Exact inputs are listed under review validation below.

### R5. The inferential tests answer a narrower question than the main distribution claim

**Confirmed scope limit; live-service assumptions remain unvalidated.** The eight
tests concern a sharp null of no effect of prompt assignment on availability and
features under the fixed slot policy, conditional on the finite reference and no
interference. They are not tests of original/generated population equality, a
weak-null mean energy effect, perceptual equivalence, or reduced spread. A
negative observed estimate plus rejection can be reported; it is not a confidence
interval for a general average improvement.

Synthetic qualification checks idealized contribution-sign distributions. It
does not simulate or prove live service stability, treatment-dependent duration,
stopping, source sampling or validity of the feature construct. Two randomized
groups span collector boundaries: OAuth Cézanne water01 repetition 0 and Nano
Banana 2 Monet built06 repetition 1, with approximately 954 and 915 seconds between
first and last starts. The original multi-day schedule was not realized. These
are concrete timing concerns, not proof that randomization p-values are wrong.

Absolute energy is a V-statistic with a finite-sample baseline. The disjoint
real/real resampling is useful, but its 999 draws reuse a small panel; Cézanne water
contributes only one painting per split group. Those ranges are not independent
replications, population intervals or an equivalence margin. The current paper
largely discloses this correctly; the central hypothesis must use the same limits.

Evidence: [inference contract](../../../studies/painter_distribution_study_v1/INFERENCE.md),
[paired implementation](../../../src/latent_art_bench/painter_distribution_study_v1/inference.py),
and statistics review. Keep unavailable endpoints in the fixed multiplicity
family. Do not rerun generation to improve significance.

### R6. Service effects are not immutable-model effects

**Confirmed design limitation.** Provider slugs and pinning do not attest model
weights or server-side prompt processing. The OAuth comparator reports low
quality on 424 of 430 outputs and medium on six; all six medium images are
artist-free. Requested quality and shape were not uniformly honored. This can be
part of the total prompt-to-service outcome while preventing interpretation as a
pure painter-name semantic effect at fixed rendering quality. Dropping those six
after treatment is not an automatic causal repair.

Treat OAuth as a service comparison and the two paid routes as the cleaner
intervention examples, preserving the original eight-endpoint family. Two selected
painters and a limited collection
period cannot establish prevalence across artists, traditions, models or future
versions. Historical four-painter results are useful context, not independent
confirmation after they informed the design.

### R7. Coverage, specificity and classification need diagnostic controls

**Confirmed scope limitations.** k=3 coverage is an operating point in a small
reference geometry; sample-size matching alone does not validate artistic
coverage. Uniform generated subsampling does not match painter-specific class
masses. With only three Cézanne water originals, each water work's k=3 neighborhood
must include at least one reference from another class; the third nearest neighbor
itself need not be the cross-class one. Two-reference energy ranking also changes
the within-reference term, so it is not a calibrated painter-recognition score.
Whole-brief disjointness does not provide held-out photographic-workflow or
cross-generator validation.

Useful unused control: all **216** route × brief × repetition pairs of artist-free
requests have exactly identical payloads across their nominal painter labels.
Comparing those separately collected outputs under the same content weights can reveal
ordinary collection/label/timing differences before interpreting named painter
specificity. This is a proposed post-result placebo diagnostic, not a new
randomized confirmatory test or a guarantee of equivalence.

Evidence: [coverage and classifier code](../../../src/latent_art_bench/painter_distribution_study_v1/analysis.py),
lines 230–408; [prompt construction](../../../src/latent_art_bench/painter_distribution_study_v1/study.py),
lines 50–61; retained requests; statistics review and MC6.

### R8. The human-validation plan does not yet specify a distribution-level experiment

**Confirmed missing validation.** Individual-image style resemblance cannot
validate within-set perceptual variation or coverage of a painter reference set.
The [existing follow-up](../../../studies/painter_distribution_study_v1/HUMAN_FOLLOWUP.md)
acknowledges that distinction but does not yet operationalize the set-level task.
Many raters viewing one montage do not provide many independent image sets.
Style, content diversity, image quality and authenticity need separate questions.
The proposed 24–36 raters are a feasibility range, not a powered final design.

This is a blocker for perceptual claims, not a requirement to call a literal
feature-space observation a feature-space observation.

### R9. Novelty and external reproducibility require further work

**Confirmed publication gaps.** The bibliography omits directly adjacent work:
[AI-Pastiche](https://arxiv.org/abs/2502.15856) evaluates artistic imitation using
user surveys, and [AI-WikiArt](https://arxiv.org/abs/2508.01408) studies attribution
and generated-image detection across many painters. The already cited
[2026 CLIP separation preprint](https://arxiv.org/abs/2608.25609) also investigates
why separation need not match human perception. These records were checked during
this review. Comparison to Kim's art-history study alone cannot establish novelty;
fresh full-text access to Kim was unavailable to the construct reviewer, so no
new full-method replication assessment is claimed.

Local hashes and tests are not external reproducibility. Numeric reanalysis,
pixel-to-feature replay, and regeneration are three different promises: public
numeric artifacts can support the first; retained images and the environment are
needed for the second; unattested changing services prevent exact regeneration
guarantees. Prepare an appropriate stable data-access/release plan without
pretending a Git checkout recreates ignored images. Preserve source rights and
do not claim a broad benchmark solely because collection is well logged.

## Corrections to earlier planning advice

The previously suggested 80–120 additional paintings should be treated only as a
possible feasibility envelope. The review does not establish it as sufficient or
necessary. Sample size must follow a declared target, common support, capture
controls and a precision or power calculation appropriate to the actual units.
More generated images are not currently justified by this review.

The prior conversational wording that `native1024` uses retained delivered-file
dimensions was incorrect. [Delivery selection](../../../src/latent_art_bench/painter_distribution_study_v1/reference_delivery.py),
lines 82–91, retains parent-surrogate `expected_width/height` and stores thumbnail
dimensions separately; [panel construction](../../../src/latent_art_bench/painter_distribution_study_v1/study.py),
line 127, uses the parent metadata. Parent short-side ≥1024 counts are Monet 4 /
Cézanne 19; delivered-file counts are 4 / 18. Neither field documents photographic
capture quality or an original capture master. The published calculation is
unchanged; the correction concerns its explanation.

## Revision plan, with explicit completion criteria

The following is a plan, not authorization to reopen a closed census. Use one
new versioned diagnostic scope for new analyses and separate scopes for any
future acquisition or measurement. Preserve every existing protocol, ledger,
feature vector and published result. The editable manuscript can later point to
both the original report and clearly labeled revision evidence.

### Step 1 — Reframe the claims and complete the novelty comparison

**Cost/data:** writing and existing records only; no provider calls.

Build a claim-to-evidence table for the abstract, results and discussion. Retain
the literal 31-feature results, the observed paid-route named/free changes and
their exact sharp-null interpretation. Remove any implication of perceptual
diversity collapse, whole-oeuvre sampling, independent service sessions, or
universal generation behavior. Explain that energy and spread are related
summaries, and distinguish generated-only prompt changes from reference-relative
differences. Add a focused prior-work matrix: task, unit, prompt intervention,
representation, reference/capture control, human evidence and accessible data.

**Done when:** every headline has an explicit target and evidence type; the paper
can state a contribution beyond detecting AI files without relying on model
recency or test counts. Keep scientific findings in the foreground and move
incidental transport history into reproducibility material.

### Step 2 — Run one fixed diagnostic package on existing numeric data

**Cost/data:** zero generation and zero new pixel measurements. Declare these
analyses post-result, choose the finite grid before running it, and report every
specified result. Do not select a new primary metric based on favorable outcomes.

| Diagnostic | Concrete output | Question answered |
|---|---|---|
| Metadata controls | Domain/geometry/profile/source/border table; square-rule result; descriptor associations | Which nuisances are separable from domain, and where is common support absent? |
| Metric weighting | Original metric plus nonredundant 28-coordinate, family-balanced and no-texture views; coordinate/family trace contributions | Does the headline depend on repeated or texture-heavy weighting? |
| Variation decomposition | Within/between brief and content trace; cross-domain and within-generated energy terms | Where does naming change measured variation and energy? |
| Reference influence | Leave-one-work and feasible source/content deletions with support counts | Which works or sparse cells control conclusions? These are sensitivities, not population intervals. |
| Timing/attrition | Actual pair start gaps; leave-boundary-group and initial-only estimates; all missing dispositions | Are conclusions sensitive to documented execution boundaries? |
| Placebo/specificity | Identical artist-free payload groups under common weights; own/other energy-term decomposition | Is apparent painter specificity distinguishable from reference or collection effects? |
| Coverage controls | Fixed k=1/3/5, sample-size curves, content-stratified equal-size generated subsamples matching reference class counts, class-support/radius tables, held-out real controls where feasible | How much do content mixture, sparse references and the coverage operating point determine the result? |
| Detector controls | Metadata baselines and feasible cross-route transfer with disjoint works and briefs | Does detection generalize beyond one route? Source holdout is unavailable without source support. |

For family-balanced Euclidean geometry, specify the squared-distance contribution
of each family before computing results; dividing coordinates by the square root
of family size is one transparent choice, not a style calibration. Do not add an
open-ended menu of metrics or inflate claims by counting agreeing variants.

**Done when:** every comparison has an ID manifest, exact definition, complete
results and preserved contradictions; base results replay unchanged; patterns
sensitive to a specified restriction, metric or boundary are labeled accordingly.
Nuisance association is not causal attribution or correction. Without geometry
or source overlap, a regression adjustment would require unsupported extrapolation.
A failed robustness check is a scientific result. It is not a reason
to tune the metric or discard the problematic images.

### Step 3 — Establish reference and nuisance feasibility before setting N

**Dependency:** Step 2, plus a separately defined scope before any new image
access or measurement. Metadata feasibility is not a generation campaign.

Declare the scientific target: the current finite panel, a new eligible
collection frame, or a wider artist claim. Audit independent work identities,
source/capture provenance, periods, depicted content and usable geometry support.
Design independent blinded content/nuisance coding for original and generated
images, preserving disagreement. Use adherence as an outcome; separately justify
any conditional analysis. Distinct filenames or websites do not prove distinct
capture events.

Specify a bounded geometry/reproduction validation: genuine same-work capture
pairs where available and symmetric processing sensitivities where meaningful.
New crops or patches must be evaluated as altered targets. They cannot recreate
missing whole-painting geometry support. If compatible references or independently
documented captures cannot be found, retain the narrower image-file claim and
mark the stronger interpretation unresolved.

**Done when:** a source-by-painter-by-content/geometry support table, independent
annotation plan, inclusion rules and stated inferential target establish what
new observations can actually resolve. Only then set acquisition counts using
precision/power simulations over physical works, briefs and capture dependence.
Use conservative plausible effects, not only the largest observed effects. Do
not stop acquisition when significance appears. Keep new validation works separate
from the exposed historical collection and report any combined analysis explicitly.

**Conditional execution after feasibility:** if a new-reference claim is retained,
freeze the sampling frame, counts, selection and stopping rules, measurements and
analysis before new outcomes are inspected. Then acquire the selected works,
perform independent coding/adjudication, measure under the fixed processing
contract and run the separate replication. Archive every disposition and report
all prespecified results. Design completion alone is not completed validation;
Step 6's stronger-reference branch requires this replication's actual evidence.

### Step 4 — Validate perceptual constructs using retained generations

**Dependency:** a fixed human-study protocol and usable reference/display design;
no new generations are required. This step is needed for a perceptual claim and
may run alongside the new-reference feasibility work once its stimuli are fixed.

Operationalize image-level painter resemblance and **perceived set-level
variation**, the latter being the primary distribution construct for the
contraction hypothesis. Reference coverage, if included, needs a distinct
secondary task and outcome. Freeze specific metric–outcome mappings and their
multiplicity treatment rather than correlating every metric with every rating.
Equal-size sets should share brief composition,
use multiple separately allocated stimulus sets, hide route/prompt labels and
retain ties. Separate quality, content diversity and authenticity from style.
Pilot comprehension and burden, then determine the final rater/stimulus sample
using crossed effects and a smallest relevant association. Follow the host
institution's ethics determination before recruitment, as the existing follow-up
requires. Do not use LLM judges as independent human validation.

**Done when:** a blinded, prespecified analysis estimates the relation of each
metric to its intended human construct with appropriate uncertainty. Disagreement
narrows or changes the interpretation rather than being excluded. Many ratings
of the same images must not masquerade as more independent image evidence.

Before collecting validation outcomes, record what would defeat each proposed
interpretation. For example, divergence between aggregate and within-brief trace
already defeats a uniform fixed-prompt contraction claim; lack of a meaningful
metric–human association would withhold the corresponding perceptual claim.
Confounded source/geometry support leaves attribution unidentified, regardless
of how small a p-value becomes. Specify effect or precision thresholds for the
new validation target prospectively; do not replace these decisions with a count
of favorable sensitivity results or interpret a nonsignificant result as proof
of equality.

### Step 5 — Add one complementary representation, if it addresses the remaining question

**Cost/data:** existing images; local inference feasibility first, no encoder
training or generation necessary. This requires a new measurement scope.

Fix encoder/version, feature layer, processing, scaling and endpoint definitions
before examining comparisons. Report agreement and disagreement with interpretable
features and, when available, human judgments. Check geometry/content sensitivities
for the encoder too. Do not interpret a learned embedding as intrinsically more
valid, or choose among encoders after observing which preserves the hypothesis.

**Done when:** the second representation contributes an interpretable triangulation
result instead of another uncalibrated score. It remains optional for a carefully
scoped interpretable-feature paper.

### Step 6 — Choose the final claim, venue and release package

| Outcome of revision | Defensible paper direction | Further generation |
|---|---|---|
| Differences survive only as file/representation properties | Narrow empirical measurement case study, emphasizing limits and confounds | Not required to report that result |
| Paid-route prompt changes survive fixed diagnostics, without human evidence | Controlled finite-reference prompt/feature-distribution paper | Not initially required |
| Reference controls and human set-level judgments support the same interpretation | Stronger computational-art study of painter-conditioned proximity and variation | Only a specific unresolved design gap could justify a small new study |
| Goal changes to prevalence across artists or general model evaluation | Prospectively selected additional artists, independent sources and broader validation | A new design and budget are required; more repetitions alone are inadequate |

Scientific Reports, a computational-creativity venue, or a humanities journal
remain conditional options from the previous discussion, not readiness or
acceptance judgments. Venue choice must follow the verified contribution; a
humanities submission needs an actual humanities argument, while a major AI
submission needs a contribution that generalizes beyond this selected case study.
Have a human statistician and relevant domain researcher review the final target
and assumptions; this LLM review cannot stand in for them.

Before submission, distinguish public numeric replay, image-to-feature replay and
unrepeatable service-state reproduction. Provide a stable, rights-appropriate
artifact-access path for the evidence claimed as reproducible. Do not spend the
remaining generation budget without identifying a question existing images and
better references cannot answer.

## Review validation and preservation

The coordinator ran the smallest relevant offline statistics/inference/main-analysis
tests: **16 passed**. Subagent test results are recorded in their supporting
reviews; overlapping runs are not added together as distinct tests. The historical
evidence audit at the reviewed HEAD passes **2,902 checks, zero failures**, retaining
its two previously acknowledged unrecoverable inputs and informational historic
working-tree drift. That audit is evidence-integrity support, not a methodological
validation of the new study or the scientific claims.

Ruff and whitespace checks pass. All 154 local Markdown links in the review
documents and updated status/index resolve.

Read-only review diagnostics use these committed inputs:

- `data/manifests/painter_distribution_study_v1/pdsv1-main-parallel-20260906/reference_features.jsonl`
- `data/manifests/painter_distribution_study_v1/pdsv1-main-immediate-20260907/generated_features.jsonl`
- `data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/scalers.json`
- `data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/requests.jsonl`
- The frozen reference delivery metadata and append-only collection events cited
  in the supporting reviews.

No frozen source, protocol, ledger, image, feature record, numerical publication,
report figure or manuscript was edited for this review. Only review documents
and mutable navigation/status are changed. The research implementation and full
846-test result reported at study completion remain historical evidence; this
documentation-only review does not claim to have rerun that full suite.
