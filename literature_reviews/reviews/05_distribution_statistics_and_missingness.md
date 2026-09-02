# Distribution statistics, dependence, coverage, and missingness

## Review question

How should Painter Feature Generation v1 test whether outputs produced with a painter's name
reproduce the corresponding real painter's feature distributions?

The question is not whether a classifier recognizes the requested name, whether a generated image
looks plausible in isolation, or whether generated images are closer to one painter centroid than
another. It is whether a registered set of outputs reproduces a closed, broad-scene-weighted finite
distribution of digital-surrogate features for that same painter.

## 1. Statistical conclusion

No single statistic establishes reproduction. Protocol 2.0 correctly requires a conjunction, for
every painter and every one of the three prequalified feature families, of:

1. absolute equivalence to the named painter's real target;
2. specificity against each of the other three painters, not merely a favorable average;
3. improvement over the paired artist-free condition;
4. coordinate-level location and dispersion agreement;
5. acceptable fit within every retained broad scene group;
6. robustness to individual works and authority/capture workflows; and
7. complete output, content-adherence, and copy-exclusion gates.

These endpoints answer different failure questions. Small absolute discrepancy does not establish
specificity. Specificity does not establish absolute fit. Painter-name improvement does not show
that the named distribution was reached. An aggregate distribution distance can hide collapse in a
coordinate or scene group. All of them can be made misleading by selective failures or copying.

A positive result is therefore a project-specific decision under one frozen model, prompt census,
render contract, seed/request population, feature system, and accessible real frame. It is not a
literature-validated universal score of painter fidelity.

## 2. The target is a finite distribution of physical works

For painter \(a\), retained broad scene group \(s\), and feature family \(F\), let
\(x_{asiF}\) be the vector for physical work \(i\). Files, crops, mirrors, encodings, and multiple
resolutions of the same painting are measurements or derivatives, not additional works.

After corpus closure, every scene group supported by all painters with at least 20 confirmation
works per painter is retained. At least three groups must survive. If \(G\) groups remain, each
receives mass \(1/G\), and each of the \(n_{as}\) works within a group receives mass
\(1/(G n_{as})\). Thus the real target is

\[
P_{aF}=\frac{1}{G}\sum_{s=1}^{G}\frac{1}{n_{as}}
       \sum_{i=1}^{n_{as}}\delta_{x_{asiF}}.
\]

This construction uses every eligible confirmation work and permits unequal painter counts. It
standardizes only broad scene mass. Period, detailed iconography, season, illumination, depth, and
the observed source mixture remain features of the finite target rather than variables silently
balanced away.

The corresponding generated distribution gives equal mass to each retained scene group, each of
the four fixed prompt templates in that group, and each registered repetition. The four painter
conditions and the artist-free condition use the same templates, settings, repetition count, and
within-template seed. Chance repeats and generated-to-generated duplicates retain full
multiplicity. The retained template count is (T=4G), so five conditions require (20GR)
registered attempts.

The real population is a census conditional on the frozen accessible frame. Its empirical
real--real term and generated--real summation are exact for that finite target; the generator-side
expectation is still estimated from registered repetitions. Resampling the real works would invent
a sampling design that did not occur.

This distinction matters for interpretation. The accessible lawful digital corpus is not a
probability sample of a painter's complete oeuvre. Source noncoverage, missing digitization,
rights exclusions, and capture disturbance remain scientific limitations even though there is no
real-work sampling variance conditional on the closed frame.

## 3. Why generic generative metrics are secondary

| Method | Legitimate use here | Why it cannot decide reproduction |
|---|---|---|
| FID | historical or learned-space diagnostic | Gaussian summary in an ImageNet representation; finite-sample and model-dependent bias |
| KID or MMD | secondary kernel two-sample diagnostic | kernel, bandwidth, representation, dimension, and block design determine sensitivity |
| CMMD | semantic/context diagnostic | CLIP geometry and its training exposure remain part of the construct |
| classifier two-sample test | localization or alarm | discrimination can exploit source, content, border, or leakage shortcuts |
| neighborhood precision/recall or density/coverage | mode-support sensitivity | unstable with sample size, dimension, outliers, and neighborhood choice |
| energy distance | primary family-level discrepancy | still valid only in the prequalified coordinates, scaling, metric, and dependence design |

FID was introduced by
[Heusel et al. (2017)](https://papers.nips.cc/paper_files/paper/2017/hash/8a1d694707eb0fefe65871369074926d-Abstract.html).
[Chong and Forsyth (2020)](https://openaccess.thecvf.com/content_CVPR_2020/html/Chong_Effectively_Unbiased_FID_and_Inception_Score_and_Where_to_Find_Them_CVPR_2020_paper.html)
show that its finite-sample bias can depend on the evaluated model. Raw FID is consequently unsafe
as the primary comparison for unequal painter cells.

KID was proposed by
[Bińkowski et al. (2018)](https://openreview.net/forum?id=r1lUOzWCW) using the MMD framework
developed by [Gretton et al. (2012)](https://www.jmlr.org/papers/v13/gretton12a.html).
An unbiased estimator does not make its feature representation or kernel construct-valid.

[Jayasumana et al. (2024)](https://openaccess.thecvf.com/content/CVPR2024/html/Jayasumana_Rethinking_FID_Towards_a_Better_Evaluation_Metric_for_Image_Generation_CVPR_2024_paper.html)
propose CMMD to address weaknesses of FID, but the result remains conditional on a semantic encoder.
[Stein et al. (2023)](https://papers.nips.cc/paper_files/paper/2023/hash/0bc795afae289ed465a65a3b4b1f4eb7-Abstract-Conference.html)
show more generally that evaluator and representation choices can change model comparisons.
Protocol 2.0 therefore keeps learned metrics diagnostic and does not select whichever evaluator
produces the most favorable painter result.

## 4. Primary energy-distance estimator

All primary coordinates are transformed once using the equal-painter pooled median and IQR fitted
on prospectively assigned new-development data. A zero, missing, or nonfinite pooled IQR fails the entire family;
coordinates are not deleted after inspection, and painter-specific scaling is forbidden.

For one painter, scene, and family, let \(y_{astrF}\) be the named output under template \(t\) and
repetition block \(r\). There are four templates per retained scene and \(R\) repetitions. Protocol
2.0 uses

\[
\widehat D_{asF}=
\frac{2}{4Rn_{as}}\sum_{i,t,r}\lVert x_{asiF}-y_{astrF}\rVert
-\frac{1}{n_{as}^{2}}\sum_{i,j}\lVert x_{asiF}-x_{asjF}\rVert
-\frac{1}{16R(R-1)}\sum_{r\ne r'}\sum_{t,t'}
  \lVert y_{astrF}-y_{ast'r'F}\rVert .
\]

The real self-term includes all ordered work pairs and their zero diagonals because it describes the
complete finite empirical target. The generated self-term excludes equal repetition blocks: outputs
from the same block are not treated as independent generator draws. The raw U-statistic is retained
even if finite-sample variation makes it slightly negative; clipping it to zero would alter its
sampling behavior.

The painter-family discrepancy is the unweighted mean of the scene-level discrepancies,
\(D_{aF}=G^{-1}\sum_s\widehat D_{asF}\). The same construction compares named outputs with each wrong
painter's scene-matched real target and compares the artist-free outputs with the named painter's
target.

Energy distance is not self-validating. Distance concentration, poorly scaled coordinates, source
signals, or unqualified features can still yield an answer to the wrong question. Its primary role
is justified only after all three interpretable feature families pass deterministic fixtures,
capture/source disturbance checks, untouched qualification, and registered adverse simulations.

## 5. Equivalence is not failure to reject a difference

Absolute fit requires a prospectively calibrated family margin \(\epsilon_F\), not a nonsignificant
difference test. Historical development supplies a fixed-seed distribution of same-painter
half-sample distances. The family margin is the larger of its specified upper percentile and twice
the independent-capture disturbance tolerance bound.

Prospectively assigned qualification then has one chance to show that the frozen margin is neither too narrow
for same-painter reproduction variation nor so wide that wrong painters become equivalent. Every
same-painter development-versus-qualification distance must be at most \(\epsilon_F\), and
\(\epsilon_F\) must be no greater than half the smallest supported wrong-painter qualification
distance. Confirmation cannot widen it.

The minimum specificity and artist-name improvement margin is
\(\delta_F=0.25\epsilon_F\). For every painter and family, the binding contrasts are:

- absolute fit: the simultaneous upper confidence bound for \(D_{aF}^{\text{named}\to a}\) is at
  most \(\epsilon_F\);
- all-wrong-painter specificity: for every \(h\ne a\), the simultaneous upper bound for
  \(D_{aF}^{\text{named}\to a}-D_{aF}^{\text{named}\to h}+\delta_F\) is at most zero; and
- artist-free improvement: the simultaneous upper bound for
  \(D_{aF}^{\text{named}\to a}-D_{aF}^{\text{free}\to a}+\delta_F\) is at most zero.

Averaging the three wrong painters is forbidden. The easiest comparison cannot compensate for a
failure against the closest one. Likewise, artist-free improvement is causal evidence about adding
the name under the paired frozen system, but it cannot rescue failure of absolute fit.

## 6. Dispersion and per-scene coverage are binding

A generator can achieve a modest average distance while contracting onto a central stereotype.
Protocol 2.0 therefore makes coordinate and scene coverage part of the decision, rather than a
nongating illustration.

For every coordinate in every required family:

- the simultaneous absolute generated--real median difference must be at most 0.25 common-scaled
  units;
- the generated-to-real IQR ratio must lie in \([0.80,1.25]\); and
- a zero real IQR fails rather than producing an undefined or favorable ratio.

For every retained scene group separately, the simultaneous upper bound on energy distance must be
at most \(\epsilon_F\). Passing the equal-scene aggregate cannot hide a failed or missing scene.
Season, illumination, and depth imbalances are reported as nuisance sensitivities; they are not
removed through outcome-dependent weighting.

Deleting one confirmation work must neither change the decision nor move a primary statistic by
more than ten percent of its frozen margin. Every estimable leave-one-workflow analysis must also
preserve direction and decision. These checks do not create a superpopulation inference; they ask
whether the finite-frame conclusion is hostage to one work or digitization workflow.

Precision and recall were separated by
[Sajjadi et al. (2018)](https://papers.nips.cc/paper_files/paper/2018/hash/f7696a9b362ac5a51c3dc8f098b73923-Abstract.html).
[Kynkäänniemi et al. (2019)](https://proceedings.neurips.cc/paper/2019/hash/0234c510bc6d908b28c70ff313743079-Abstract.html)
use local neighborhoods, while
[Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a.html) propose density and coverage
to address failure modes of earlier estimators. Those methods remain useful sensitivity analyses,
including across neighborhood and sample-size choices, but they do not replace the binding
coordinate-dispersion and per-scene rules.

## 7. Dependence determines the uncertainty calculation

Pixels, coordinates, tiles, pairwise distances, and multiple derivatives are not independent units.
Nor are five prompt conditions sharing a seed and execution episode. Treating either collection as
independent would manufacture precision.

For a deterministic local generator, repetition \(r\) is one resampling block containing every
retained template and all five conditions. For an opaque or remote service, one complete balanced
wave of all template-by-condition requests is the minimum candidate block. Adjacent waves exposed
to the same outage, backend revision, moderation state, or other documented episode are merged.
Request IDs, timestamps, random order, and a failure to detect autocorrelation do not establish
independence.

[Owen and Eckles (2012)](https://doi.org/10.1214/12-AOAS547) provide a foundation for bootstrap
reasoning in crossed random-effects data.
[Winkler et al. (2015)](https://doi.org/10.1016/j.neuroimage.2015.05.092) explain why permutation
and resampling procedures must respect exchangeability blocks. Applied here, those principles mean
that the prompt-template census and all real finite-population vectors stay fixed while complete
registered generator blocks are resampled.

The confirmatory analysis uses exactly 9,999 whole-block resamples and recomputes every binding
continuous endpoint in each replicate. Each endpoint is studentized by its bootstrap standard
deviation. The critical value is the prespecified conservative 95th order statistic of the
replicate-wise maximum absolute studentized deviation over the complete frozen endpoint inventory.

This single max-statistic construction supplies simultaneous intervals for absolute fit, all
wrong-painter contrasts, artist-free contrasts, coordinate medians and IQR ratios, and per-scene
distances. A zero or nonfinite bootstrap standard deviation is inconclusive, not zero-width
certainty. The endpoint inventory, critical-index formula, tie-to-failure rule, random-number
algorithm, and seed must be frozen at G0 after \(G\) is known.

The simultaneous system is deliberately severe because the decision spans four painters, three
families, many coordinates, all wrong-painter contrasts, and every retained scene. Additional
coordinate or learned-space summaries are descriptive; no alternative multiplicity adjustment can
support a reproduction label.

## 8. Missingness, refusals, and intention-to-prompt

Missingness can arise before or after generation:

| State | Example | Required interpretation |
|---|---|---|
| source noncoverage | eligible works were never digitized or lawfully reusable | limitation of the accessible finite frame |
| acquisition or measurement failure | terminal transport failure, corrupt file, inadequate geometry | explicit attrition; no convenient replacement |
| generation failure | refusal, timeout, transport failure, missing or corrupt output | failure of a registered attempt |
| content departure | decoded output depicts the wrong broad scene | retained in its assigned primary cell |
| coding failure | missing or unreliable human label | affected condition cannot support a positive claim |

[Rubin (1976)](https://doi.org/10.1093/biomet/63.3.581) distinguishes missingness mechanisms, but
the labels MCAR, MAR, and MNAR do not make their assumptions true. Provider refusals, safety
filters, transport episodes, and decode failures may depend on painter name, prompt, or latent image
content. Source availability may likewise depend on properties of paintings and institutions.

[White, Horton, Carpenter, and Pocock (2011)](https://doi.org/10.1136/bmj.d40) discuss
intention-to-treat strategy in another domain. The transferable principle here is to preserve the
registered assignment and denominator. An off-topic output stays in its assigned scene template and
in the primary feature distribution. An `adherent_only` analysis is a labeled sensitivity and
cannot replace intention-to-prompt.

Protocol 2.0 avoids a particularly fragile MNAR correction by requiring an exact output gate:
100% of registered outputs must be present, decodable, and feature-analyzable for any positive
claim. There is no complete-case renormalization, imputation, output replacement, reroll, or top-up.
If even one registered output fails, the run and its failures are still reported, but
reproduction is not demonstrated.

The denominators remain explicit: all registered attempts define completeness; successfully decoded
outputs define adherence; and every analyzable, real-copy-excluded output defines the continuous
comparison. Off-topic outputs remain in that last denominator.

Because a passing run has no generated missingness in the binding continuous grid, it requires no
MNAR survivor model. This does not establish that the generator has universally perfect
availability; it establishes completeness only for the frozen registered request population.

Assigned-scene adherence remains a separate gate: at least 0.90 under equal-template weighting and
at least 0.75 in every template-by-condition cell, after the frozen blind coding and reliability
procedure. High fit among adherent images cannot conceal off-topic outputs.

[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830) provides tail bounds for sums of
independent bounded variables. Such bounds can be useful for a future rate estimand with defensible
independence units, but Protocol 2.0 does not use a bound to soften its exact completeness gate or to
turn a failed empirical adherence threshold into a pass.

## 9. Copying is adverse evidence, not excellent fit

A copied or near-copied real work can make distribution distance look unusually small without
showing generative coverage. Protocol 2.0 therefore searches every output against every lawfully
acquired development, qualification, auxiliary, and confirmation work using exact hashes
and a frozen whole-image and sliding-crop detector.

On registered resize, JPEG, small-crop, mirror, and mild-color transformations, the detector must
reach at least 0.95 sensitivity; on unrelated painter-balanced pairs, its false-positive rate must
be at most 0.01. Those requirements are fitted on development and repeated without
threshold change on qualification. Masked reviewers adjudicate flagged generated--real
pairs.

Any confirmed copy of a searched real work fails the positive claim; the required count is exactly
zero. Removing a copy and reporting the remaining outputs as though it never occurred is not
allowed. Generated-to-generated duplicates are also retained with full multiplicity, so repetition
or mode collapse degrades rather than disappears from the spread and coverage endpoints.

Zero detected copies has a finite-search interpretation only. It cannot prove that an output was
not copied from an unavailable work or from opaque training data, and it is not a legal conclusion
about model training or infringement.

## 10. Finite-frame inference and unavailable inclusion probabilities

[Horvitz and Thompson (1952)](https://doi.org/10.1080/01621459.1952.10483446) concern estimation
under known inclusion probabilities, and
[Rao and Wu (1988)](https://doi.org/10.1080/01621459.1988.10478591) concern resampling for complex
survey designs. Neither supplies active machinery for Protocol 2.0 because the confirmation target
is the complete closed accessible population, not a probability subsample from a known oeuvre
frame.

Unknown web availability cannot be repaired by inventing inclusion probabilities. A real-work
bootstrap likewise cannot turn a convenience frame into a probability sample. Required responses
are a transparent attrition funnel, separate counts of works and files, source-incidence reporting,
same-work capture analysis, uniform-work sensitivity, and leave-one-workflow robustness.

The resulting claim remains conditional on authority-record exact attribution, lawful and adequate
digital capture, outdoor-place eligibility, supported common scene groups, and the observed source
mixture. It does not generalize to undigitized, inaccessible, differently attributed, or physically
examined paintings. Oeuvre-wide inference would require a new sampling frame with known inclusion
probabilities and a newly justified estimator.

## 11. Adequacy and whole-decision simulation

No equal per-painter work quota is justified by the literature. Protocol 2.0 first applies design
floors to the actual closed frame:

- every painter must support at least three common broad scene groups and at least 20 physical works
  in each retained group;
- equal-scene Kish effective sample size must be at least 100 per painter, with maximum individual
  work weight at most 0.02;
- painter and authority/capture workflow must be crossed in a connected incidence graph, with at
  least two workflows per painter, at least two painters per workflow used in the binding
  cross-painter claim, and no workflow carrying more than 0.80 of a painter's weight; and
- the independent-capture auxiliary set must contain at least 60 works, at least 12 per painter,
  at least three scene groups, two workflows per painter, and two provenance-independent captures
  per work.

These are screening floors, not power proofs. Real-work count and generator repetition count govern
different uncertainties. After family margins are frozen, \(R\) is selected from
\(\{25,50,75,100\}\) by 2,000 simulations of the complete decision using the actual scene counts,
feature dimensions, prompt pairing, and proposed dependence blocks.

The simulated data-generating processes include a favorable matching-painter model, every wrong
painter, a pooled artist-free proxy, central-mode collapse, 50% dispersion collapse, a 0.50
common-scaled shift in each coordinate, and the largest observed workflow disturbance. Simulation
must exercise the complete conjunction and simultaneous procedure, not a convenient single test.

Use the smallest candidate \(R\) whose exact Clopper--Pearson lower bound for favorable
full-conjunction pass probability is at least 0.80 and whose upper bound for false pass is at most
0.05 under every adverse process. The detailed selection rule is stricter than the preliminary 90%
rejection screening statement and therefore controls. The design must also keep unsupported
painter-family claims at or below 0.05 and make the simultaneous target-fit interval no wider than
half its equivalence margin.

If no candidate \(R\) passes, the protocol stops. It does not widen margins, delete a family, add an
unregistered repetition count, or substitute a weaker decision. Simulation can show adequate
operating behavior under specified alternatives; it cannot prove that those alternatives exhaust
the ways a generator or corpus may fail.

## 12. Registration and Protocol 2.0 disposition

Registered reports, as proposed by
[Chambers (2013)](https://doi.org/10.1016/j.cortex.2012.12.016), separate evaluation of a question
and method from knowledge of its result. The transparency principles in
[Nosek et al. (2018)](https://doi.org/10.1073/pnas.1708274114) support preserving hypotheses,
materials, exclusions, outcomes, and deviations rather than selecting a successful narrative.

For this study, registration means that the following are fixed before generation and confirmation
opening: the model and render contract; supported prompt-template census; seeds and request order;
all three feature families and common scaling; margins; block map; complete endpoint inventory;
simulation results; multiplicity rule; copying thresholds; and failure semantics.

The allowed decision language is deliberately granular:

- `family_reproduced` only when one painter-family passes every binding endpoint and gate;
- `painter_reproduced_on_all_three_primary_families` only when all three families pass; and
- `panel_reproduction_demonstrated` only when all four painters pass.

An unqualified, inconclusive, source-sensitive, missing, copied, off-topic, or failed family remains
visible. No average across families or painters creates a global success.

The concrete Protocol 2.0 disposition is prospective NO-GO for generation at present. There are no
admitted active-study physical works, no sealed confirmation population, no registered generation
attempts, and no generated-versus-real results. The next authorized work is metadata census and
frame construction, followed by blind eligibility, method qualification, margin calibration, and
whole-decision simulation.

Only after every corpus, workflow, auxiliary-capture, family-qualification, and simulation gate
passes may G0 freeze the generator experiment. If any prerequisite fails, the four-painter study
stops or begins a new prospective protocol; it does not repair the question after seeing protected
outcomes.

Accordingly, the strongest current statistical conclusion is not that painter-name outputs do or
do not reproduce real painter distributions. It is that Protocol 2.0 specifies a falsifiable
finite-frame test of that question. Empirical reproduction remains entirely undemonstrated.
