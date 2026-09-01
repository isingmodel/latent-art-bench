# Distribution statistics, coverage, dependence, and missingness

## Review question

Once a candidate coordinate has passed reproduction and construct checks, how should the project
compare a painter's real oeuvre distribution with another painter or, in a later separately
authorized study, with a generated set?

The statistical object is a distribution of measurements over physical works. It is not a cloud
of independent pixels, crops, pairwise distances, prompts, or seeds. The design must separately
estimate eight outcome families:

1. absolute fit to the eligible target-painter reference;
2. panel-wide specificity relative to every prospectively selected hard neighbor;
3. generated-to-real precision and density;
4. real-to-generated recall and coverage;
5. content coherence of the first four families;
6. availability, refusals, invalid outputs, and other missingness;
7. contraction or expansion relative to real within-painter dispersion; and
8. prompt-induced movement relative to a paired painter-free control.

For a future canonical painter-fidelity claim, the first six families are binding conjuncts.
Contraction and prompt movement are mandatory nongating outcomes: they remain visible, but neither
has an automatically favorable direction and neither can rescue a failed conjunct. No reviewed
statistic simultaneously identifies all eight families.

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

The primary set-level discrepancy, if the candidate panel qualifies, will be MMD or energy
distance on real-only standardized, interpretable coordinates. Kernel, bandwidth, coordinate
weights, and any dimension reduction are fitted inside development folds and frozen before
confirmation. Learned-space MMD/CMMD values remain named secondary outcomes. Sample-size curves
and equal-size subsampling accompany every set comparison.

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

## 4. Painter specificity is one-versus-many

Pilot 2's target-versus-one-neighbor difference-in-differences is a useful paired effect, but one
favorable comparison cannot establish specificity. A reboot comparison panel must contain:

- historically and visually close painters;
- painters with overlapping subjects, dates, media, and sources;
- broader negatives for calibration; and
- prospectively fixed exclusions and abstention rules.

For target painter \(a\), freeze the complete hard-neighbor set \(H_a\) before support or feature
outcomes and define the panel contrast set \(A_a^{panel}=\{a\}\cup H_a\). Every target and
neighbor reference, generated comparison, margin, minimum, and lower quantile uses one immutable
joint common support, source/capture-workflow distribution, and set of target weights for
\(A_a^{panel}\). With \(P_j^*(\cdot;A_a^{panel})\) denoting those standardized real references and
\(Q_a^*\) the generated distribution standardized over the corresponding promptable cells, report

\[
S_{a,h}=D\!\left(Q_a^*,P_h^*(\cdot;A_a^{panel})\right)
       -D\!\left(Q_a^*,P_a^*(\cdot;A_a^{panel})\right),\qquad h\in H_a,
\]

and retain the full vector. The binding decision requires **both** the panel-worst margin and the
prespecified lower quantile across eligible content-by-neighbor cells to have simultaneous lower
confidence bounds above their separately frozen SESOIs. A favorable average, minimum, or quantile
cannot substitute for the other rule. If only pairwise supports exist, their margins may be
reported with explicit domains, but they cannot be combined into a panel minimum, lower quantile,
omnibus specificity decision, or canonical painter-fidelity claim. Broad negatives are diagnostic
calibrators and never replace a failed hard neighbor.

The named-versus-control prompt effect remains a separate causal estimand under a frozen
generator, prompt, and seed policy:

\[
\Delta_a =
D\!\left(Q_{\mathrm{control}}^*,P_a^*(\cdot;A_a^{panel})\right)
-D\!\left(Q_{\mathrm{named}}^*,P_a^*(\cdot;A_a^{panel})\right).
\]

A positive \(\Delta_a\) says that adding the name moved outputs toward the same standardized target
reference on the frozen panel support. It does not by itself show absolute fit, specificity, any
support metric, content coherence, or availability robustness.

## 5. Dependence and the unit of inference

The following are not independent observations when they arise from the same physical work:

- multiple digitizations or derivatives;
- crops, tiles, and patches;
- color or resolution perturbations;
- multiple feature coordinates;
- repeated pairwise distances involving the work; and
- multiple raters judging that work.

Generated images are likewise nested in prompt/content block, generator, model version, painter
condition, and seed or repetition. Treating all pairs or all crops as independent produces
pseudoreplication and overly narrow intervals.

The protocol uses the physical work as the highest real-image sampling unit. Depending on the
estimand, it uses:

- work-cluster bootstrap or permutation for one-level designs;
- multiway clustering when both work and another crossed factor contribute dependence;
- hierarchical models with work, rater, painter, source, content block, and prompt effects when
  estimable; and
- randomization inference aligned with the actual paired prompt assignment.

[Owen and Eckles (2012)](https://doi.org/10.1214/12-AOAS547) provides a foundation for bootstrap
procedures in crossed random-effects data.
[Winkler et al. (2015)](https://doi.org/10.1016/j.neuroimage.2015.05.092) explains why
permutations must respect exchangeability blocks. These principles forbid shuffling painter
labels across source/content strata that were not exchangeable.

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

Every qualification, winner-selection, external-confirmation, and generated-success decision uses
the frozen hierarchical/closed-testing or jointly calibrated max-statistic procedure that strongly
controls experiment-wide family-wise error across feature families, coordinates, preprocessing
branches, scales, encoders, painters, neighbors, transfer endpoints, and human endpoints.
False-discovery-rate procedures are permitted only for clearly labeled exploratory coordinates
that cannot qualify a method or support a project-level claim. Neither multiplicity procedure
substitutes for limiting the number of claims. Results are reported with simultaneous intervals
and painter-level heterogeneity even when a multiplicity-adjusted decision is made.

## 7. Small samples and reference uncertainty

The real oeuvre is finite, incomplete, and selectively digitized. A standardized reference such
as \(P_a^*(\cdot;A_a^{panel})\) is therefore an estimate of an explicitly eligible population, not
the painter's metaphysical total practice. Every target distance includes uncertainty from the
real reference sample.

Required reporting includes:

- number of physical works, independent captures, and derivative files separately;
- eligible source/content/phase cells and empty cells;
- resampling at the work level;
- sample-size or accumulation curves for distances and coverage;
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
held-work information, joint source/content/phase transfer, hard-neighbor separation, and nuisance
increment before generated results may be interpreted in that coordinate.

| Generated outcome | Primary meaning | Required qualification | Decision role |
|---|---|---|---|
| Absolute target fit | set discrepancy to eligible target reference | qualified coordinates, finite-reference uncertainty, equal-size curves, and frozen real-real equivalence/noninferiority scale | binding |
| Panel-wide specificity | target margins against every hard neighbor | one immutable panel support/weight system; simultaneous worst and lower-tail rules; no pairwise aggregation | binding |
| Precision and density (separate) | generated outputs supported by target reference | both frozen neighborhood/sample-sensitivity criteria pass | binding |
| Recall and coverage (separate) | eligible target modes represented by outputs | both frozen criteria pass, with phase/genre/medium robustness where estimable | binding |
| Content coherence | fit, specificity, and all four support outcomes across promptable content cells | frozen worst-cell or lower-tail robustness rule | binding |
| Availability | probability that a registered cell yields an eligible output | all attempts retained; frozen refusal/failure and missingness robustness rule | binding |
| Contraction or expansion | difference from real within-painter dispersion | real-reference uncertainty and mode-aware analysis | mandatory, nongating; no favored direction |
| Prompt movement | causal effect of adding a name under one frozen system | paired assignment and intent-to-generate denominator | mandatory, nongating; cannot substitute for fidelity |

A canonical painter-fidelity claim is allowed only when every one of the six binding rows passes
under the strong experiment-wide FWER hierarchy. Contraction and prompt movement must still be
reported, but neither can compensate for failure of absolute fit, either hard-neighbor rule, any
of the four support metrics, content coherence, or availability.

This decomposition is deliberately stricter than Pilot 2. It preserves Pilot 2's paired prompt
logic while preventing centroid proximity, one favorable neighbor, or available-case filtering
from being relabeled as a painter feature.
