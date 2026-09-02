# Distribution statistics, coverage, dependence, and missingness

## Review question

Once a candidate coordinate has passed reproduction and construct checks, how should the project
compare a painter's real oeuvre distribution with another painter or, in a later separately
authorized stage of the active study, with a generated set?

The statistical object is a distribution of measurements over physical works. It is not a cloud
of independent pixels, crops, pairwise distances, prompts, or seeds. The design must separately
estimate nine outcome families:

1. absolute fit to the eligible target-painter reference;
2. an all-neighbor specificity conjunction relative to every prospectively selected hard neighbor;
3. coordinate-level central coverage and spread;
4. neighborhood precision/recall and density/coverage sensitivities;
5. assigned-broad-scene-group adherence plus common-content and uniform-real sensitivity for the
   first four families;
6. availability, refusals, invalid outputs, and other missingness;
7. exact and near-copying;
8. contraction or expansion relative to real within-painter dispersion; and
9. prompt-induced movement relative to a paired painter-free control.

For a future canonical painter-fidelity claim, outcomes 1, 2, 3, 5, 6, and 7 are binding project
conjuncts. Neighborhood estimators are sensitivity diagnostics. Contraction and prompt movement are
mandatory nongating outcomes: they remain visible, but neither has an automatically favorable
direction and neither can rescue a failed conjunct. No reviewed statistic simultaneously identifies
all nine families.

## 1. Why one distance or one classifier is insufficient

Painter classification answers whether labels are recoverable under a particular sampling and
split design. It does not show that distances are calibrated, that all important career phases
are represented, or that a generated set occupies the target distribution. Likewise, a centroid
distance can be small for a collapsed set that reproduces only a narrow stereotype.

The distinction follows a broader measurement principle: a statistic inherits the construct and
biases of its representation, sampling frame, and estimator. Changing the encoder can reverse
model rankings; changing the reference sample can move a nonparametric score; changing the split
can turn source recognition into apparent painter recognition.

The reboot therefore treats every result as a tuple:

\[
(\text{representation},\ \text{reference population},\ \text{sampling unit},\
\text{discrepancy},\ \text{uncertainty method},\ \text{claim ceiling}).
\]

## 2. Set-level discrepancy estimators

| Method | What it estimates | Useful role | Central limitation for painter features | Disposition |
|---|---|---|---|---|
| Fréchet Inception Distance (FID) | Gaussian mean/covariance discrepancy in Inception space | Historical benchmark and sensitivity analysis at large equal sample sizes | ImageNet representation, Gaussian approximation, joint fidelity/diversity, strong finite-sample bias | Never primary |
| Kernel Inception Distance (KID) | Unbiased polynomial-kernel MMD estimate in a chosen feature space | Finite-sample sensitivity statistic | “Unbiased” applies to the estimator, not to construct validity; result is kernel/encoder dependent | Secondary |
| Maximum mean discrepancy (MMD) | Difference in kernel mean embeddings | Transparent set-level target discrepancy when kernel is justified | Kernel bandwidth and high-dimensional power must be calibrated; ordinary asymptotics may fail in clustered data | Candidate |
| Energy distance | Distance based on expected cross- and within-sample distances | Interpretable distribution equality statistic; can use qualified coordinates | Distance concentration and representation scaling matter; clustered works require clustered inference | Candidate |
| Conditional MMD (CMMD family) | Distribution discrepancy in a contextual embedding, potentially conditional | Semantic/context sensitivity | CLIP semantics and training exposure remain part of the construct | Separate diagnostic |
| Classifier two-sample test | Predict real versus generated or target versus comparison | Detects a broad distribution difference and can diagnose coordinates | Accuracy does not localize cause; overfitting and sample dependence can inflate evidence | Diagnostic |

FID was introduced by
[Heusel et al. (2017)](https://papers.nips.cc/paper_files/paper/2017/hash/8a1d694707eb0fefe65871369074926d-Abstract.html).
[Chong and Forsyth (2020)](https://openaccess.thecvf.com/content_CVPR_2020/html/Chong_Effectively_Unbiased_FID_and_Inception_Score_and_Where_to_Find_Them_CVPR_2020_paper.html)
showed model-dependent finite-sample bias, so the project will not compare small or unequal
painter cells with raw FID. KID comes from
[Bińkowski et al. (2018)](https://openreview.net/forum?id=r1lUOzWCW), building on the general
two-sample MMD framework of
[Gretton et al. (2012)](https://www.jmlr.org/papers/v13/gretton12a.html).

Recent work does not yield a universal replacement.
[Jayasumana et al. (2024)](https://openaccess.thecvf.com/content/CVPR2024/html/Jayasumana_Rethinking_FID_Towards_a_Better_Evaluation_Metric_for_Image_Generation_CVPR_2024_paper.html)
proposes CMMD with a CLIP encoder, improving several estimator properties while retaining CLIP's
semantic and web-training domain.
[Stein et al. (2023)](https://papers.nips.cc/paper_files/paper/2023/hash/0bc795afae289ed465a65a3b4b1f4eb7-Abstract-Conference.html)
demonstrates that metric and encoder choices can materially change conclusions. The protocol
therefore reports evaluator-family sensitivity instead of selecting the metric that favors a
hypothesis.

### Protocol consequence

The primary set-level discrepancy, if the candidate panel qualifies, is energy distance on
interpretable coordinates transformed once by the weighted median/IQR of the equal-painter mixture
of the four complete `q*`-weighted development populations. That one transform is applied unchanged
to every painter, control, generated, qualification, confirmation, and external vector; painter-
specific scaling is forbidden. Kernel, bandwidth, coordinate weights, and any dimension reduction
are fitted inside development data and frozen before confirmation. Learned-
space MMD/CMMD values remain named secondary outcomes. Finite-size thinning curves are diagnostics;
they do not replace the full-real-census primary estimate or create real-work sampling error.

## 3. Precision, density, recall, and coverage are different estimands

[Sajjadi et al. (2018)](https://papers.nips.cc/paper_files/paper/2018/hash/f7696a9b362ac5a51c3dc8f098b73923-Abstract.html)
formalized separate precision and recall aspects of generative distributions.
[Kynkäänniemi et al. (2019)](https://proceedings.neurips.cc/paper/2019/hash/0234c510bc6d908b28c70ff313743079-Abstract.html)
uses local neighborhoods, and
[Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a.html)
proposes density and coverage to address failure cases.

For this project:

- **generated-to-real precision** asks whether generated outputs lie in supported regions of the
  eligible real target reference;
- **generated-to-real density** asks how strongly the eligible real reference supports those
  generated outputs;
- **real-to-generated recall** asks what share of the eligible real distribution is represented
  by the generated set;
- **real-to-generated coverage** asks whether the generated set reaches the target reference's
  supported regions under Naeem et al.'s complementary neighborhood construction;
- **contraction** asks whether within-generated dispersion is materially smaller than eligible
  real dispersion after accounting for reference uncertainty; and
- **stratified coverage** repeats coverage across career phase, genre/content, motif, and medium
  when the historical sampling frame supports those strata.

Neighborhood estimators can be unstable with small samples, outliers, dimension, and the choice
of \(k\). The project will show \(k\)- and sample-size sensitivity and will not turn a single
neighborhood estimate into a binary fidelity label. A transparent stratified occupancy analysis
is preferred when the painter reference is too small for credible high-dimensional neighborhoods.

## 4. Painter specificity is an all-neighbor conjunction

Pilot 2's target-versus-one-neighbor difference-in-differences is a useful paired effect, but one
favorable comparison cannot establish specificity. The reboot freezes every hard neighbor before
feature or generated outcomes. Broad negatives remain diagnostic calibrators and never replace a
failed close neighbor.

The real construction is a complete sealed-confirmation census with four broad scene groups, not a
set of 24 exact microcontent cells. The former six narrow submotifs remain nonbinding diagnostics.
Before any active content label is read, R0a freezes and hashes every prompt/render byte in 12
candidate complete 24-template frames; G0 may verify hashes and substitute painter names but cannot
rewrite them. After painter-level population assignment R0a selects one using only three
nonredundant broad-scene proportions and five visible-property means. For painter
\(j\), let \(U_j^C\) be the complete sealed-confirmation population and let \(q_{ji}^*\) be the
R0a-frozen entropy-projection mass matching that shared eight-dimensional target. Define
\(P_j^{C,*}=\sum_{i\in U_j^C}q_{ji}^*\delta_{x_{ji}}\). Its source composition is the observed
composition inside the frozen finite frame; the estimand is source-mixture-specific rather than
source-standardized. The uniform complete population is a mandatory sensitivity. Let \(Q_{a,t}\)
be the analyzable, near-copy-excluded return distribution for target condition \(a\) under selected
template \(t\), and define \(Q_a^{(24)}=\sum_t Q_{a,t}/24\). Exact interactions and joint profiles
are neither matched nor imputed.

For target painter \(a\), freeze the complete hard-neighbor set \(H_a\), the discrepancy, and one
SESOI \(\delta_{a,h}\) per neighbor, then retain the full vector

\[
S_{a,h}=D\!\left(Q_a^{(24)},P_h^{C,*}\right)
       -D\!\left(Q_a^{(24)},P_a^{C,*}\right),\qquad h\in H_a.
\]

Every \(S_{a,h}-\delta_{a,h}\) must have a simultaneous lower confidence bound above zero. A
favorable average, one favorable neighbor, or an easier broad negative cannot substitute for that
conjunction. The full internal frame caps each group's unweighted share at 30% and each multi-source
scene at 70%, while each development, qualification, and confirmation population caps group shares
at 30% and multi-source scene shares at 70% under both unweighted and applicable `q*` mass. Optional
external populations require two unopened groups and a 70% overall unweighted/`q*` cap. No full-
frame `q*` exists. Source-specific and leave-one-source results are
binding, including the exact within-painter×scene RMS of commonly scaled `q*`-weighted source-versus-
complement median shifts against the independent-capture bound and its uniform-weight repeat. Exact
common source×broad-scene-group contrasts are mandatory diagnostics only for cells with
prespecified adequate support in both painters; absent cells are neither imputed nor allowed to
redefine the primary common-content construction.

The named-versus-control prompt effect remains a separate causal estimand under a frozen generator,
24-template frame, and seed policy:

\[
\Delta_a =
D\!\left(Q_{\mathrm{control}}^{(24)},P_a^{C,*}\right)
-D\!\left(Q_{\mathrm{named},a}^{(24)},P_a^{C,*}\right).
\]

Generated analyses retain the assigned template and broad scene group even when blind coding finds
an off-topic return: this is intention-to-prompt. A positive \(\Delta_a\) says only that adding the name
moved analyzable outputs toward the frozen target reference. It does not by itself show absolute
fit, specificity, coverage, content adherence, or availability robustness.

Every named condition and shared painter-free control uses the same repetition count `R` in every
template. For a fixed deterministic local map, template seed lists are independent IID uniform draws
with replacement; chance duplicates are retained and one common realized list is not reused across
templates. An opaque/remote endpoint instead uses `C` equal-size common-shock units, each with `L`
complete balanced template×condition waves and `R=CL`. The four-painter grid therefore costs `120R`
requests. The retired `R=16`/1,920-request design cannot clear its availability lower bound; even the
impossible perfect-return/all-independent case requires `R>=25` and at least 3,000 requests, and the
larger actual `R` must be frozen only after the unit audit, full rate inventory, and whole-decision
simulation.

Content reliability is itself gated. Before R0a adjudication, every screened derivative and missing
label remains in its denominator: per-painter three-way visual-eligibility agreement must reach 0.90,
each coder's ambiguous share must not exceed 0.10, broad-scene and each five-property three-state
contrast must reach 0.85 on the union-eligible set and every assigned internal or registered-external
population, and each coder's applicable indeterminate share must not exceed 0.20. Failure is R0a NO-
GO and consensus cannot erase it. G1b separately double-codes every sealed-confirmation and
technically analyzable generated image; condition-scoped 0.85/0.20 receipts are sealed before third-
coder consensus, and a failed receipt makes the affected endpoint inconclusive.

## 5. Dependence and the unit of inference

The following are not independent observations when they arise from the same physical work:

- multiple digitizations or derivatives;
- crops, tiles, and patches;
- color or resolution perturbations;
- multiple feature coordinates;
- repeated pairwise distances involving the work; and
- multiple raters judging that work.

Generated images are likewise nested in assigned prompt template and broad scene group, generator,
model version, painter condition, and seed or repetition. Treating all pairs or all crops as independent
produces pseudoreplication and overly narrow intervals.

The physical work is the highest real-image unit. Depending on a study's design, valid options can
include:

- work-cluster bootstrap or permutation for one-level designs;
- multiway clustering when both work and another crossed factor contribute dependence;
- hierarchical models with work, rater, painter, source, broad scene group, and prompt-template
  effects when estimable; and
- randomization inference aligned with the actual paired prompt assignment.

[Owen and Eckles (2012)](https://doi.org/10.1214/12-AOAS547) provides a foundation for bootstrap
procedures in crossed random-effects data.
[Winkler et al. (2015)](https://doi.org/10.1016/j.neuroimage.2015.05.092) explains why
permutations must respect exchangeability blocks. These principles forbid shuffling painter labels
across source or content groups that were not exchangeable; they do not turn source into a sampling
stratum.

These principles do not authorize inventing sampling variance for a fully observed finite
population. Protocol 1.7 freezes one complete eligible frame per painter and one CSPRNG permutation:
ranks 1–72 are development, 73–180 are the complete qualification population, and 181 onward are
the complete sealed-confirmation population. The permutation controls exposure; it does not create
later probability subsamples. R0b releases all qualification works, G1b measures all confirmation
works, and neither stage may add or redefine population units.

The real-census components are therefore exact. For real masses \(p_i=q_i^*\), the generated–real
term sums over every real work and the real–real term sums \(p_ip_kd(x_i,x_k)\) over every ordered
population pair, including zero diagonals; the generated expectation is still estimated from
registered draws. The generated self term remains an equal-template U-statistic over distinct
repetitions within template and product means across templates. In each of 9,999 prospective
uncertainty replicates, a fixed deterministic local map resamples complete seed condition vectors
within template. An opaque/remote endpoint instead resamples only complete equal-size balanced
common-shock units, each carrying every template×condition wave, failure, label, copy status, and
feature together. Both keep all real census values and `q*` weights fixed, preserve each template's
count, and never resample templates as prompt-superpopulation units. Independence or alignment
failure makes both rate and continuous endpoints ineligible or inconclusive. This construction must
pass deterministic fixtures and whole-decision generator-side common-shock simulation before G0.

Generated quantiles preserve equal template mass by assigning every analyzable output in template
`t` weight `1/(24 m_t)`; equal-image pooling is forbidden when return counts differ. A binding blind
realized-content entropy projection starts from those base weights, must satisfy the same joint
convex-hull, cap, and ESS gates, and is recomputed inside every generator replicate. Infeasibility,
instability, or reversal makes the result content-sensitive or inconclusive; this sensitivity cannot
rescue an intention-to-prompt failure.

[Horvitz and Thompson (1952)](https://doi.org/10.1080/01621459.1952.10483446) remains the reviewed
inclusion-probability reference, and
[Rao and Wu (1988)](https://doi.org/10.1080/01621459.1988.10478591) remains the reviewed complex-
survey resampling reference. They are rejected as active machinery because Protocol 1.7 does not
subsample any declared real population. If a future protocol introduces probability subsampling,
it must newly specify inclusion probabilities, finite-population estimation, and validated
design-consistent replication; it cannot silently import those methods into this census design.

## 6. Multiplicity and researcher degrees of freedom

The candidate panel includes many coordinates, scales, perturbations, painters, competitor
margins, and evaluator families. A nominal \(p<.05\) filter over this garden of comparisons would
select unstable stories.

Before confirmation the execution protocol must identify:

- a small set of primary feature families and family-level hypotheses;
- the aggregation rule within each family;
- primary painters or a painter-population estimand;
- the confirmatory competitor summary;
- a multiplicity method suited to the dependence structure;
- effect-size and equivalence regions; and
- which analyses are descriptive or sensitivity-only.

For the active generated decision, Protocol 1.7 preallocates
`alpha_cont + alpha_rate <= 0.05`. The continuous feature/distance family uses one jointly calibrated
max statistic over generator-vector replicates. Rate endpoints are excluded from that max statistic:
availability, adherence, and copy use a separately enumerated Bonferroni family of directional
weighted-Hoeffding bounds and conservative ratios. `M_rate` counts unique one-sided events: a full
endpoint needs `A` lower, `A` upper, `J` lower, and `K` upper, with opposite availability tails
counted separately. The same G0-frozen independence partition governs the continuous resampler and
rate bounds; the latter aggregates request weights into unit weights `W_c` and uses `sum_c W_c^2`.
False-discovery-rate procedures are permitted
only for clearly labeled exploratory coordinates that cannot qualify a method or support a project-
level claim. No multiplicity procedure substitutes for limiting the number of claims. Results are
reported with simultaneous intervals and painter-level heterogeneity even when an adjusted decision
is made; a nonstructural zero or numerically degenerate replicate variance is inconclusive rather
than zero-width certainty.

## 7. Finite reference populations and claim scope

The digitized real oeuvre is finite, incomplete, and selectively available. The primary
\(P_a^{C,*}\) is the exactly measured, content-standardized distribution in one explicitly eligible,
source-mixture-specific sealed-confirmation population, not an estimate of the painter's
metaphysical total practice. Conditional on that declared finite population, target distances have
no real-work sampling error. Source, reproduction, and eligibility limitations remain scientific
uncertainties handled by binding robustness checks and claim narrowing, not by a real-work
bootstrap.

Required reporting includes:

- number of physical works, independent captures, and derivative files separately;
- eligible painter×broad-scene-group counts, source incidence, microcontent marginals, and empty
  diagnostics;
- pre-adjudication visual-screening and union-eligible denominators, three-way eligibility agreement,
  coder-specific ambiguous and indeterminate shares, and broad-scene/five-contrast agreement receipts,
  with failures retained rather than repaired by consensus;
- G1b real/generated raw double-code receipts, third-coder consensus only after passing, and affected-
  endpoint inconclusive dispositions;
- the frozen `q*` masses, maximum mass, Kish effective sample size, target residual, and uniform-real
  sensitivity;
- unweighted and applicable `q*` source shares, exact source-versus-complement shift values, and the
  independent-capture disturbance bound;
- finite-size thinning or accumulation curves for distances and coverage, labeled diagnostic;
- leave-one-work and leave-one-source influence diagnostics;
- sensitivity to rare modes and outliers; and
- a claim ceiling when a painter's reference lacks the overlap required for inference.

No percentage-of-variance PCA rule is sufficient. Dimension reduction is tuned by nested
real-only validation, distance stability, and source/content transfer. Pilot 2's 22 retained
components from 24 training works is treated as a warning about a nearly saturated reference
geometry.

## 8. Missingness, refusals, and availability

Pilot 2 executed all 320 assigned generation requests but five moderation refusals made both
requested-label feature grids incomplete. The four primary tests were correctly not run. A reboot
must preserve that lesson: missing outputs are outcomes, not housekeeping.

The missingness taxonomy is:

| State | Example | Required treatment |
|---|---|---|
| Structural ineligibility | No historically defensible work in a required phase/medium cell | Define the narrower target population; do not impute an artwork |
| Source noncoverage | Museum or collection does not digitize eligible works | Report selection frame and source dependence |
| Acquisition failure | Terminal transport, rights, or metadata failure | Preserve attempt evidence; no unregistered fallback |
| Measurement failure | Unsupported resolution, bad profile, corrupted decode, failed encoder | Report by painter/source/condition; do not silently replace preprocessing |
| Generation refusal | Moderation or provider refuses a registered prompt | Availability estimand and intent-to-generate denominator |
| Invalid generated output | Blank, duplicate, corrupted, or protocol-ineligible image | Predefined validity rule; count and characterize |
| Human-rating missingness | Rater dropout, failed attention check, device failure | Predefined exclusions and crossed-model handling |

[Rubin (1976)](https://doi.org/10.1093/biomet/63.3.581) supplies the standard distinction among
missingness mechanisms; its assumptions are not automatically satisfied here.
[White, Horton, Carpenter, and Pocock (2011)](https://doi.org/10.1136/bmj.d40) emphasizes
intention-to-treat strategy and sensitivity analysis in a different application domain. The
transferable lesson is to define denominators and departures before seeing favorable outcomes.

Generated-image analysis will report:

1. intent-to-generate estimates over every registered cell;
2. available-case feature estimates only when their scientific target is explicit;
3. refusal/failure rates and risk differences by painter and condition;
4. worst-case or bounded sensitivity when missing outcomes could reverse the conclusion; and
5. no complete-pair confirmatory test when the frozen test requires complete pairs and that
  condition is not met.

The binding availability/adherence/copy intervals are not empirical-bootstrap percentiles, which
can collapse to zero width at all-success or zero-copy boundaries. R1a freezes every elementary
one-sided mean bound, counts it in the Bonferroni rate family, applies the
[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830) independent-bounded-unit bound,
and constructs conservative ratios for conditional adherence and copy rates. Request weights `w_i`
give each template equal total mass. Before execution G0 freezes auditable units `c`, unit weight
`W_c=sum_{i in c} w_i`, and bounded within-unit `A/J/K` means; the radius uses `sum_c W_c^2`. One full endpoint
therefore contributes four directional events—`A` lower, `A` upper, `J` lower, and `K` upper—to
`M_rate`; duplicate use of the same direction is counted once, but opposite tails are distinct.

For a fixed deterministic local map, one independent seed draw and its complete painter/control
condition vector may define a unit. An opaque/remote endpoint instead schedules `C` equal-size
common-shock units, each with `L` complete waves of every template×condition and `R=CL`; continuous
inference resamples those whole units only. Request IDs, timestamps, random order, or null
autocorrelation do not establish independence. Provider episodes, batches, backend revisions,
moderation states, outages, retry cascades, and other plausible common shocks stay together. A
crossed shock, unusable balanced unit, or partition not aligned with the fixed-template continuous
resampler makes both affected rate and continuous endpoints ineligible or inconclusive. R1a stress-
tests registered unit sizes, batch/outage/moderation events, and pixel/feature common shocks. Any zero
denominator bound is inconclusive. Template-level minimum returns, differential-failure MNAR
scenarios, and the full shared painter/control dependence design enter simulation before G0.

## 9. Registration, confirmation, and negative results

The empirical execution protocol is frozen before any sealed external set or generated outputs
are examined. Registered reports, as proposed by
[Chambers (2013)](https://doi.org/10.1016/j.cortex.2012.12.016), separate evaluation of the
question and method from knowledge of the result. The broader reproducibility principles in
[Nosek et al. (2018)](https://doi.org/10.1073/pnas.1708274114) support transparent hypotheses,
materials, and deviations.

Every registered feature and estimand is reported, including:

- gate failures;
- negative and equivocal painter effects;
- failed external transfer;
- source or content shortcut success;
- availability/refusal imbalance;
- estimator disagreement; and
- deviations, with timing and rationale.

Failures open a new versioned development study; they do not cause the confirmation set to become
development data under the same protocol.

## 10. Decision for the reboot

The project adopts a multi-output analysis rather than a universal painter-fidelity score. A
real-only painter association is a prerequisite, not a generated-fidelity outcome; it requires
held-work information, binding source robustness, broad-scene and career-phase heterogeneity checks,
hard-neighbor separation, and nuisance
increment before generated results may be interpreted in that coordinate.

| Generated outcome | Primary meaning | Required qualification | Decision role |
|---|---|---|---|
| Absolute target fit | set discrepancy to eligible target reference | qualified coordinates, exact complete real census, diagnostic finite-size curves, and frozen population-level adverse-alternative margin | binding |
| All-neighbor specificity | target margins against every hard neighbor | one primary `q*` common-content construction; every simultaneous neighbor margin passes; supported exact source×broad-scene-group diagnostics and binding source robustness | binding |
| Coordinate coverage and spread | generated central coverage and contraction/expansion | simultaneous median differences and IQR ratios for four frozen interpretable coordinates per family; 10th/90th percentiles remain tail diagnostics | binding project rule |
| Neighborhood support estimators | estimator-family sensitivity | report precision/recall and density/coverage across sample size and tuning without treating four related estimates as independent confirmation | sensitivity |
| Content coherence | assigned-scene adherence plus common-content, realized-content, and uniform-real robustness | frozen broad-scene and five-variable rules; generated `1/(24 m_t)` mass and blind entropy-projection sensitivity; no exact joint-profile claim | binding project rule |
| Availability | probability that a registered prompt yields an eligible output | all attempts retained under intention-to-prompt; boundary-safe Bonferroni weighted-Hoeffding lower bound and frozen MNAR rule | binding |
| Copying | whether apparent fit is driven by exact or calibrated near-copy events | all registered outputs retained; frozen whole-image and crop thresholds plus conservative conditional-rate upper bound | binding |
| Contraction or expansion | difference from real within-painter dispersion | complete real reference and mode-aware analysis | mandatory, nongating; no favored direction |
| Prompt movement | causal effect of adding a name under one frozen system | paired assignment and intent-to-generate denominator | mandatory, nongating; cannot substitute for fidelity |

A painter-fidelity conclusion may be allowed only when every prospectively simulated binding row
passes under the strong experiment-wide error hierarchy. This exact conjunction is a project rule,
not a literature-validated universal metric. Contraction and prompt movement must still be reported,
but neither can compensate for failure of absolute fit, specificity, median/spread coverage,
content coherence, copying, or availability.

This decomposition is deliberately stricter than Pilot 2. It preserves Pilot 2's paired prompt
logic while preventing centroid proximity, one favorable neighbor, or available-case filtering
from being relabeled as a painter feature.
