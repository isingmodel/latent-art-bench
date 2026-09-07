# Skeptical statistics and inference review

Reviewed 2026-09-07 at commit `744d7f779b0698ed8b9b384157894b341b432ccd`.
This is a maintainer-run LLM subagent review, not institutionally independent
statistical review. Scope: current `painter_distribution_study_v1`, with direct
inspection of its contracts, assignment generator, analysis primitives, inherited
kernel/randomization code, tests, completed report, manuscript and numeric evidence.
No collection, acquisition, feature extraction, frozen-file edit or result replacement
was performed. The only new file written by this reviewer is this review.

## Overall judgment

I found no confirmed arithmetic error in the primary weighted V-energy, paired
contribution formula, Monte Carlo p-value, Holm correction or classification split
implementation. Eighteen relevant offline tests pass. The principal problems are
identification, inferential scope and missing diagnostic decomposition, rather than
an obviously broken numerical calculation.

The current data demonstrate large differences between these finite recorded image
collections in this representation. Four paid-route prompt contrasts reject a
conditional sharp no-effect null under an unverified no-interference assumption.
Neither fact establishes population-level difference from a painter's oeuvre,
perceptual style deficiency, reduced randomness for every fixed prompt, or a
general model ranking. The manuscript already discloses many of these limits;
disclosure prevents overclaiming but does not experimentally resolve them.

## Ranked findings and required repairs

### S1 — Major: the available inference does not test the main population/style hypothesis

**Confirmed scope limitation, not a p-value implementation bug.** Absolute energy,
spread, coverage and detection are explicitly descriptive (`studies/painter_distribution_study_v1/INFERENCE.md:10–23`).
Only eight prompt contrasts are tested, under a sharp null covering availability
and every measured feature in every randomized slot (`INFERENCE.md:33–39`,
`src/latent_art_bench/painter_distribution_study_v1/analysis.py:165–181`).
Rejecting that sharp null is not a calibrated test that expected energy is lower,
that generated and original populations are different, or that population variance
is smaller. No-effect-on-all-outcomes is stronger than equality of mean discrepancy.

The current wording largely respects this distinction (`papers/painter_distribution_study_v1/paper.tex:316–330`,
`:443–457`). Nevertheless, interpreting its four adjusted p-values as confirmatory
evidence for the project's broad generated-versus-original hypothesis would be
incorrect. Positive empirical distance alone is expected even for independent
samples of a common continuous distribution.

**Repair:** choose one explicit primary claim for the revision: a finite-panel
computational case study, a generalization to a specified sampling frame, or a
perceptual/style claim. Keep existing finite-panel results intact. For a population
claim, define the reference and prompt populations and their sampling mechanisms
before collecting a separate validation panel; provide uncertainty for that target.
For a perceptual claim, a statistical test on these 31 coordinates cannot replace
construct validation.

**Acceptance:** every main claim states its population/finite target and endpoint;
no sharp-null p-value is described as an absolute distribution test, a weak-null
average-effect test, a style-equivalence test or a spread test. Secondary endpoint
selection and any new inferential family are frozen prospectively for new data.

### S2 — Major qualification: actual scheduler assumptions are not established by synthetic qualification

**Unverified assumption with concrete execution perturbations; invalidity is not
proved.** The condition permutation is correctly generated independently within
route × painter × brief × repetition groups (`study.py:78–108`). OAuth uniformly
permutes three conditions; conditioning on the third position makes each retained
pair exchangeable under the specified null (`INFERENCE.md:25–38`). Repeating 24
briefs three times does not itself invalidate the 72 independently randomized pair
assignments. Arbitrary dependence of fixed potential outcomes is permitted under
the correct sharp assignment null.

However, dispatch times are completion-dependent, with global locking, stop guards
and synchronous per-route retries (`parallel_collection.py:127–191`, `:261–307`).
The actual service state and later request times therefore can depend on prior
conditions through duration, failures and recovery. The synthetic experiment
constructs idealized independent assignment signs and chosen integer coefficient
magnitudes (`inference.py:57–105`); it does not simulate that live process or verify
its no-interference assumption. The reported qualification itself acknowledges
this (`INFERENCE.md:98–109`). More null simulations cannot validate unavailable
counterfactual service behavior.

Direct timestamp inspection finds two assignment groups straddling collection
components despite sharing one assigned batch:

- NB2 / Monet / built06 / repetition 1: `slot0109` to `slot0110`, **915.340327 s**.
  Start evidence: `pdsv1-main-parallel-20260906/generation_events.jsonl:89` and
  `pdsv1-main-continuation-20260906/generation_events.jsonl:1`, beneath the study
  manifest directory.
- OAuth / Cézanne / water01 / repetition 0: `slot0035` to `slot0037`, **953.870954 s**,
  with refused `slot0036` between them. Evidence: parallel ledger `:81`, `:91`;
  continuation ledger `:3`.

Median named/free start gaps are 11.81 s NB2, 25.15 s FLUX and 28.60 s OAuth.
These long boundary groups do not explain the overall pattern: an explicitly
post-hoc descriptive deletion of both boundary groups and the FLUX retry group
changes NB2 Monet energy contrast from −0.846229 to **−0.852077**, FLUX Cézanne
from −0.895593 to **−0.893784**, and OAuth Cézanne from −0.056055 to **−0.060292**.
The other affected generic comparison already lacks that refused pair. This
deletion was not assigned prospectively and does not repair randomization validity.

**Repair:** publish actual request-position/order/duration and boundary diagnostics;
distinguish computational randomization correctness from service assumptions.
Preserve the original inference, labeling it conditional. If causal robustness is
essential, obtain a separately designed replication with a defensible scheduling
and interference model, rather than asserting that eight batch IDs are independent
days or sessions. Replication need not be the first revision step.

**Acceptance:** the retained condition order matches the frozen inventory; every
boundary, retry and schedule change is disclosed; results do not rely on treating
batches as independent sessions. Do **not** replace the valid 72-pair assignment
mechanism with arbitrary whole-brief or whole-window sign flips. Cluster sampling
for a new population estimand is a different problem from this assignment test.

### S3 — Major interpretive gap: aggregate contraction combines within-brief and between-brief variation

**Confirmed omitted distinction with a counterexample in retained data.** The
primary trace computes variance around one cell mean (`statistics.py:54–55`).
With 24 different briefs, it combines stochastic variation within a fixed brief
and variation between brief-specific means. It cannot identify either component
alone. The manuscript's empirical aggregate statements are accurate
(`paper.tex:363–408`), but interpreting them as reduced diversity of repeated
responses to the same prompt is unsupported.

A bounded post-hoc calculation uses the existing primary vectors, fixed scalers
and declared class weights. For each cell, total empirical variance is decomposed
exactly into weighted within-brief and between-brief sums. Named/free ratios are:

| Painter | Route | Total | Within brief | Between brief |
|---|---|---:|---:|---:|
| Monet | NB2 | 0.6967 | 0.7492 | 0.6849 |
| Monet | FLUX | 0.3308 | 0.3088 | 0.3373 |
| Monet | OAuth | 0.5538 | 0.8698 | 0.5115 |
| Cézanne | NB2 | 0.4662 | 0.7860 | 0.3776 |
| Cézanne | FLUX | 0.4604 | 0.4886 | 0.4507 |
| Cézanne | OAuth | 0.6513 | **1.1391** | 0.5831 |

OAuth Cézanne contracts in aggregate while its within-brief empirical variance
increases. Three repetitions make that component noisy; these are descriptive
finite-sample decompositions, not unbiased variance-component estimates or tests.

Reproduction recipe: read primary512 measured rows from
`data/manifests/painter_distribution_study_v1/pdsv1-main-immediate-20260907/generated_features.jsonl`,
transform with the primary scaler in `pdsv1-main-20260906/scalers.json`, and use
reference class masses from primary512 rows in
`pdsv1-main-parallel-20260906/reference_features.jsonl`. Within each painter/route/
condition, set image weight `w_i = reference_class_mass / generated_class_count`.
For each brief b, set `W_b = sum_i_in_b w_i` and
`mu_b = sum_i_in_b w_i * y_i / W_b`; let `mu = sum_i w_i * y_i`.
Compute `V_within = sum_b sum_i_in_b w_i * ||y_i - mu_b||^2` and
`V_between = sum_b W_b * ||mu_b - mu||^2`. These sum to
`V_total = sum_i w_i * ||y_i - mu||^2`; divide each named value by its artist-free
counterpart. Every detailed named/free cell has all three repetitions per brief.

**Repair:** add an explicitly post-hoc, newly versioned decomposition for all
routes and pipelines, separating within brief, between brief within content class,
and between content class. Distinguish actual content adherence from intended
brief categories. A future design can choose more briefs or repetitions based on
which component is scientifically targeted.

**Acceptance:** total variance equals the sum of the declared components to numeric
tolerance; every route is retained; no component is called painter-style diversity
without corresponding validation. No new generation is necessary for this repair.

### S4 — Moderate: V-energy is a legitimate empirical target, not a bias-free population distance

**Design limitation, not a confirmed bug.** The code correctly includes cross and
both within-set terms (`statistics.py:53`, `analysis.py:57–58`). Reference and
generated weight-effective sample sizes differ; one 72-image Monet cell has weight
effective size **55.36**, and repeated briefs do not create 72 distinct content
samples. Effective weight size is not an estimate of statistical independence.

The V-statistic's diagonal terms induce sample-size/spread-dependent bias if it is
reinterpreted as an estimator of distance between unknown populations. The same
fixed reference term cancels in prompt contrasts, but finite generated within-set
terms need not cancel when spread changes. The paper explicitly acknowledges the
nonzero baseline (`paper.tex:221–228`). Its disjoint original/original baseline
correctly matches generated counts within class (`analysis.py:230–260`) but uses
small reused groups: 18 Monet and 15 Cézanne, including one Cézanne water work.
Its 999 draws do not supply 999 independent validation sets.

An exploratory iid diagonal-normalization check preserves all six named/free
directions; paid contrasts change by only approximately 0.02–0.05 energy units.
That is a sanity check, **not** a justified replacement estimator under this
fixed unequal-content, repeated-brief design.

**Repair:** retain V-energy for its declared finite empirical target. Add a
design-specific estimator/size-learning diagnostic only after defining the
population target and dependence model. In a new benchmark, use identical
reference splits and matched brief/repetition selections across routes when
comparing baseline-normalized effects. The current route-specific random seeds
produce slightly different original/original medians for identical references
(`analysis.py:471–480`), adding avoidable Monte Carlo noise to such comparisons.

**Acceptance:** disjoint baseline ranges remain finite subsampling descriptions;
no zero-energy threshold, equivalence boundary or population interval is inferred
from them. Any proposed correction derives its weights and sampling assumptions
for the actual design rather than applying an iid formula by habit.

### S5 — Moderate: coverage does not use the same generated content target as weighted energy

**Confirmed estimand mismatch, prospectively disclosed rather than a coding error.**
All-available coverage counts whether *any* generated point reaches each reference
ball; generated probability weights do not enter. Equal-size subsamples are
uniform over the generated rows (`analysis.py:264–287`), so their expected content
mixture is approximately one-third each, not the painter's empirical mixture.
Reference weights alone do not correct that. Neighborhoods are global: because
Cézanne has only three water references, every water work's third-other-reference
radius necessarily reaches another content class. This is the specified
secondary statistic (`MAIN.md:126–130`), not a primary content-standardized
coverage probability.

**Repair:** label the current score precisely. Add a new stratified equal-size
coverage diagnostic with generated class counts matching the reference counts,
plus an original-only held-out positive control under the same anchor/radius
construction. Investigate class-conditioned radii only where enough works exist;
do not silently change k or fabricate support for Cézanne water.

**Acceptance:** all-available support, sampling-size effects and content mixture
are reported separately. A coverage increase is not called greater artistic
completeness or uniform painter-style coverage.

### S6 — Moderate: the own-painter minimum is not a calibrated specificity test

**Interpretive limitation.** `analysis.py:506–517` compares generated V-energy to
two differently shaped finite references under equal coarse content masses.
For one generated set, its within-generated term cancels, but the two references'
within-reference terms differ. The energy difference therefore combines relative
cross-distance with reference dispersion and sampling effects. Choosing the
smaller value is legitimate distribution-distance ranking, but it is not a
validated painter recognizer. The paper appropriately labels the result
descriptive (`paper.tex:507–512`).

**Repair:** report the cross and within terms explicitly; add a painter-prompt ×
reference-painter interaction comparing Monet-named and Cézanne-named outputs
under the same briefs. The double contrast cancels reference-only and
generated-only within terms. Include the identical artist-free payloads in the
two painter-labeled groups as a negative control. Treat this as post-hoc until a
new validation design is fixed.

**Acceptance:** claimed specificity must be an effect of changing the painter
instruction, not merely one reference receiving smaller energy from most image
sets. Neither a two-way minimum nor a small interaction alone establishes human
recognition of painter style.

### S7 — Moderate: classifiers estimate within-corpus detectability, not external transfer

**No confirmed split leakage; limited generalization.** Reference folds are
content-stratified identity hashes; generated folds hold out entire briefs
(`analysis.py:305–358`). Kernel scaling and ridge are fixed, with no test-set
hyperparameter fitting (`painter_distribution_exploration_v1/statistics.py:83–101`).
Computing the full fixed kernel matrix first does not itself leak labels when
training uses only the training submatrix. Positive evidence is the explicit
split-membership test (`tests/painter_distribution_study_v1/test_main_analysis.py:102–123`).

Nevertheless, all folds share the same source/rendering regimes and painter cases.
Balanced accuracy has no external capture/source transfer guarantee and no
population interval. Pooled out-of-fold AUC compares margins from separately
fitted models (`analysis.py:292–300`, `:363`); its meaning should be checked against
within-fold AUC because different fitted scores need not have common calibration.
This concern does not invalidate the fixed-threshold balanced accuracy.

**Repair:** retain current split scores as internal diagnostics; add metadata-only
baselines, source/capture-disjoint validation when feasible, and per-fold domain
counts, error counts and AUC. Use external reference replication to test transfer
instead of attaching a naive binomial interval to all pooled files.

**Acceptance:** the revised paper clearly separates within-corpus detection from
transfer to new sources and from style recognition; no unsupported independence
assumption is introduced merely to obtain narrow error bars.

## More-reference recommendation: no defensible power basis yet

The earlier suggestion of **80–120 additional original paintings** is a practical
planning range, not a statistically established requirement. The prospective
contract explicitly says count does not establish power (`PROTOCOL.md:111–117`);
qualification power concerns chosen coefficient-sign probabilities, not images or
reference sampling (`INFERENCE.md:103–109`, `inference.py:117–131`). It cannot justify
that range, 72 generated images per cell, or a particular reference count.

Before setting N, define (1) the scientific effect or precision target,
(2) the reference sampling frame and source/capture strata, (3) the role of fresh
works versus additional captures of existing works, (4) brief/repetition dependence,
and (5) the prospective analysis. Use existing data for conditional learning curves
and design simulations over plausible between-source and between-work variation;
show sensitivity to assumptions instead of one pseudo-precise power calculation.
The current finite convenience panel cannot estimate unobserved source/capture
heterogeneity reliably. More paintings of the same confounded provenance could
make a misleading contrast more precise.

There is no statistical reason yet to purchase more generations. The variance
decomposition, prompt/reference interaction, metadata controls, matched-support
coverage, boundary diagnostics and revised claim map all reuse retained data.
Reference acquisition should follow the revised target and feasibility audit,
with a fixed new stopping rule, rather than filling an arbitrary numeric quota or
topping up the closed panel until an effect is significant.

## Validation performed

Command:

```bash
uv run --locked pytest -q -m 'not live' \
  tests/painter_distribution_study_v1/test_statistics.py \
  tests/painter_distribution_study_v1/test_inference.py \
  tests/painter_distribution_study_v1/test_main_analysis.py \
  tests/painter_distribution_study_v1/test_study.py
```

Result: **18 passed in 1.63 seconds**. Additional bounded in-memory calculations
read retained JSON/JSONL only: assignment timestamps, unique prompt strings
(24/24 generic and detailed), variance decomposition, descriptive boundary-group
deletion and the explicitly non-inferential iid diagonal sanity check. No new
analysis bundle, p-value family or scientific result replaced the sealed outputs.

The complete-pair exclusion rule is not intrinsically an inferential bug: under
the stated sharp joint availability/features null, pair eligibility is invariant
to condition swaps. It does not establish a feature-only effect with
treatment-dependent failure. The completed fixed slot inventory and withholding
of generated fidelity measurements until collection ended also provide no
evidence of effect-based optional stopping. Such accusations should not be
substituted for the specific assumption and target limitations above.
