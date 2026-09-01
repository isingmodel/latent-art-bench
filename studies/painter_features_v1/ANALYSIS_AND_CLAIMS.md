# Analysis, estimands, and claims policy

Protocol version: `painter_features_v1/analysis/1.1`

Status: prospective design framework only; a separate execution-freeze artifact must fix all
numeric choices and terminal rules before data access or execution

## 1. What is estimated

The relaunch distinguishes three layers:

1. **coordinate measurement:** properties of a declared digital reproduction and preprocessing
   branch;
2. **painter-feature estimation:** the painter-associated part of a multivariate distribution
   after source, content, medium, date, and reproduction uncertainty are modeled; and
3. **future generator comparison:** whether named prompting changes output distributions toward
   a target painter feature, with adequate specificity and coverage.

Only layers 1 and 2 are designed here. Layer 3 is retained to ensure that the measurement is fit
for Pilot 2's scientific aim, but no generation is authorized.

## 2. Sampling units

- Physical work is the unit for real-corpus inference.
- Independent reproductions and delivery derivatives are observations nested within work.
- Patches, pixels, pyramid cells, and augmentation views are technical subsamples.
- Painter is a population/grouping factor when generalizing across painters; a four-painter
  convenience set cannot support a general statement about painters.
- In a future prompt study, content block is the top-level experimental sampling unit;
  repetitions/seeds are nested within content and do not inflate top-level \(n\).
- Model version, request path, and calendar execution window are explicit operational strata.

All intervals and randomization/permutation schemes respect these levels.

## 3. Real-corpus estimands

All confirmatory estimands are restricted to registered joint common support. For a painter
contrast set \(A\), define \(q=(c,m,t)\) for content/genre, medium/support, and career phase/date;
let \(\Omega_A^*\) contain only eligible cells shared by every painter required for that contrast,
and let \(\mathcal S_{Aq}^*\) contain only source/capture workflows shared by every painter within
\(q\). Let \(\omega_{Aq}^*\) be common, frozen target-population or equal-cell weights, and let
\(\nu_{A,s\mid q}^*\) be a common, frozen distribution over \(\mathcal S_{Aq}^*\). The standardized
real reference is

\[
P_a^*(z;A)=
\sum_{q\in\Omega_A^*}\omega_{Aq}^*
\sum_{s\in\mathcal S_{Aq}^*}\nu_{A,s\mid q}^*P_a(z\mid q,s).
\]

The support, weights, source distribution, eligibility rules, and any matching caliper are fixed
before outcomes. Exact conditional comparisons within \(q\), aggregated with the same
\(\omega^*\), may replace standardization when they avoid modeling assumptions. Convenience-sample
frequencies after exclusion or missingness never define the target distribution. Cells outside
\(\Omega_A^*\) are descriptive; neither regression nor representation similarity licenses
confirmatory extrapolation into them.

### R1. Reproduction error

For coordinate family \(f\), estimate the distribution of the within-work difference across
independent reproductions:

\[
E_f = z_{w,r_1,f} - z_{w,r_2,f}.
\]

Report variance components, repeatability coefficients, and vector-distance distributions by
source pair and preprocessing branch.

### R2. Painter-associated variance

Estimate how much residual variation is associated with painter on \(\Omega_A^*\) after accounting
for registered nuisance factors. For scalar coordinates, use a cross-classified hierarchical
model such as

\[
z_i = \alpha + u_{a[i]} + g(c_i,m_i,t_i) + v_{s[i]} + u_{a\times c[i]}
      + u_{a\times t[i]} + e_i,
\]

with partial pooling and uncertainty. The precise function \(g\), interactions, and priors or
estimation method are chosen by simulation and frozen. Variance shares are descriptive, not proof
of a painter's intentional choice.

For vector families, use a preregistered multilevel distance/kernel analogue or supervised model
with nested validation. Never fit a 95%-variance PCA on all works and then call separated clusters
confirmation.

### R3. Held-out painter specificity

For target painter \(a\), hard neighbor \(h\), broad-negative set \(B\), and held-out work \(x\)
on registered common support, estimate calibrated conditional or standardized log-score/distance
margins:

\[
M_{a,h}^*(x) = D^*(x, P_h^*) - D^*(x, P_a^*),
\]

where \(D^*\) either compares within the held work's registered \(q\) cell or uses the frozen
standardized references, integrates finite-reference uncertainty, and is fitted on training works
only. Positive margins favor the target. Report work-level margins, painter-balanced aggregates,
joint source-by-content transfer, and their uncertainty. Hard neighbors are a set; no conclusion
rests on one favorable neighbor or on a nuisance mixture that differs between painters.

### R4. Within-painter coverage and heterogeneity

Estimate the spread, multimodality, career/content strata, and reference coverage inside each
painter distribution. Report robust covariance or kernel spread only when sample size supports
it. Otherwise report coordinate-wise quantiles and explicitly decline a multivariate support
claim. A compact painter centroid is not evidence that the painter's practice is homogeneous.

### R5. Human alignment

Estimate out-of-sample association between a coordinate/distance and painterly-manner triplet or
pair judgments, conditional on content judgment and source. Report expert and nonexpert estimates
separately and jointly only when pooling is supported.

## 4. Future generated-output estimands inherited from Pilot 2

Let \(G^{named}_{a,q}\) and \(G^{control}_{q}\) be generated distributions for target painter
\(a\) and a promptable common-support cell \(q\). A shared control is shown here; if controls are
generated independently for each painter, they are instead indexed \(G^{control}_{a,q}\) and that
design is frozen before requests. Define

\[
G_a^{named,*}=\sum_{q\in\Omega_A^*}\omega_{Aq}^*G^{named}_{a,q},\qquad
G^{control,*}=\sum_{q\in\Omega_A^*}\omega_{Aq}^*G^{control}_{q}.
\]

Generated images have no museum-source variable. They pass through the frozen harmonized analysis
branch; comparison is allowed only for coordinates whose source/capture dependence qualified on
real images. Distances use \(P_a^*\), \(G_a^{named,*}\), and \(G^{control,*}\), the same support and
weights for all painters, and propagated real-reference uncertainty.

### G1. Absolute target agreement

\[
A_a=D(G_a^{named,*},P_a^*).
\]

The execution-freeze artifact calibrates an equivalence bound \(\epsilon_{abs}\) from held-out
real-versus-real reference splits. Absolute agreement passes only when the simultaneous upper
confidence bound for \(A_a\) is no larger than \(\epsilon_{abs}\). Report each \(q\) cell as well
as the frozen weighted summary. A relative improvement cannot establish target agreement.

### G2. Paired target movement

\[
\Delta_{move,a} = D(G^{control,*},P_a^*)-D(G_a^{named,*},P_a^*).
\]

Positive values retain Pilot 2's paired control question: named prompting moved returned outputs
toward the target relative to an artist-free control. This is a mechanistic prompt-effect estimand,
not sufficient evidence of painter fidelity.

### G3. Hard-neighbor specificity

For every frozen hard neighbor \(h\in H_a\), estimate

\[
S_{a,h}=D(G_a^{named,*},P_h^*)-D(G_a^{named,*},P_a^*),\qquad
S_a^{worst}=\min_{h\in H_a}S_{a,h}.
\]

Also report the frozen lower quantile \(Q_{\tau}\{S_{a,h,q}\}\) across eligible
content-by-neighbor cells, with \(\tau\) fixed by prospective simulation. Both the closest-neighbor
aggregate and the lower-tail criterion must exceed their registered SESOIs with simultaneous
uncertainty. Equal-painter averages and broad-negative calibration remain visible but cannot hide
a failed hard neighbor. The corresponding named-versus-control difference-in-differences is a
paired prompt-effect supplement, not a substitute for absolute specificity.

### G4. Target-support precision, density, recall, and coverage

Estimate generated-to-real **precision/density** and real-to-generated **recall/coverage** in each
qualified representation, calibrated against held-out real-real splits and reported across the
registered neighborhood sizes or kernel scales. Precision asks whether generated samples occupy
eligible target support; density asks how strongly they are supported. Recall/coverage asks which
eligible regions of the real painter distribution are represented. The execution-freeze artifact
sets simultaneous lower bounds and a robustness rule across scales. A generator can be close to a
centroid and still fail all four support questions.

### G5. Contraction or expansion

Compare generated within-target dispersion with real within-painter dispersion after exact
conditioning or common-support standardization and finite-reference uncertainty. Report direction
and magnitude; neither greater nor lower diversity is automatically better.

### G6. Content coherence and prompt interaction

Estimate whether movement, absolute agreement, specificity, and support are consistent across
content cells and whether the name effect interacts with particular subjects. The common-support
cell, not the seed, is the unit of generalization. Aggregation always uses \(\omega^*\); favorable
cells are not selected after inspection.

### G7. Availability

Report the probability that a registered request yields an eligible analyzable output, including
refusals and terminal failures. Availability is a separate estimand with a frozen robustness rule.
The scientific effect among successful outputs is not silently described as intention-to-request
when informative refusals remove cells.

### G8. Conjunctive success rule

A future claim of target painter-feature reproduction requires all of G1, G3, G4, G6, and the
registered G7 robustness rule to pass under the experiment-wide multiplicity policy. G2 describes
relative prompt movement and must also be reported, but a favorable G2 cannot rescue failed
absolute agreement, closest-neighbor/lower-tail specificity, target support, coverage, content
coherence, or availability robustness. G5 is a mandatory plural outcome and is not labeled good or
bad by direction alone.

## 5. Distance and distribution rules

### 5.1 No universal distance

Each feature family has a distance appropriate to its scale and construct. Standardization uses
real development data only. Combining families requires either a preregistered transparent weight
rule or a learned metric qualified on held-out human judgments. Results from each family remain
visible even when a combined distance is used.

### 5.2 Small-sample safeguards

- Do not use ordinary FID for small painter reference sets. Its Gaussian assumption, model- and
  sample-dependent finite-sample bias, and preprocessing sensitivity are incompatible with the
  likely study sizes.
- KID/MMD or energy distance may be used only in a validated, frozen representation with a
  preregistered kernel/bandwidth or aggregated-kernel test and work/content-level inference.
- k-nearest-neighbor precision/recall, density, and coverage are unstable in high-dimensional or
  small-sample settings. For a future generator claim they are mandatory target-support estimands,
  so their dimensionality, sample-size, and neighborhood-sensitivity prerequisites must first pass
  simulation and held-out real-real calibration. If they cannot be estimated reliably, that
  feature family cannot support a confirmatory generated-output claim; exploratory values remain
  diagnostic.
- PCA or other dimension reduction is fit inside training data. UMAP/t-SNE plots are descriptive
  illustrations, never inferential evidence.
- A learned style cosine is not assigned a universal cutoff. Thresholds are calibrated against
  matched real pairs and human tasks in the target domain.

## 6. Uncertainty and resampling

Use a hierarchy-preserving bootstrap or a fitted multilevel model:

1. resample painters when the claim generalizes beyond named painters;
2. resample physical works within painter and design strata;
3. resample independent reproductions within selected work where reproduction uncertainty is
   part of the estimand; and
4. for future outputs using a shared artist-free control, resample the entire
   content-cell × model/version × request-path × seed/repetition bundle containing that control and
   every named-painter target together; and
5. resample each real-reference work jointly across every painter and neighbor contrast in which
   it appears.

If controls are independently generated for each painter, index them by painter and keep each
named/control pair together inside its registered bundle. A shared control is never copied into
independent painter-specific bootstrap units.

The painter-source-content crossing is preserved. A cluster interval based on pixels, patches, or
seeds alone is invalid. Where the number of top-level units is small, use exact or restricted
randomization only when its exchangeability/symmetry assumptions are defensible; otherwise report
the limited precision without manufacturing a small \(p\)-value.

## 7. Multiplicity and decision policy

The execution-freeze artifact must define one experiment-wide primary hierarchy before any
qualification outcome. Its root is the omnibus claim that at least one registered representation
supports a painter feature on common support. Beneath the root are all primary feature families;
beneath each family are every coordinate, preprocessing branch, scale, resampler, encoder,
combination rule, painter or painter-population claim, hard-neighbor panel, transfer endpoint, and
human-validation endpoint that could make that family a reported success. Learned representations
remain outside the primary tree unless the freeze artifact explicitly promotes—and therefore
counts—them.

Use a closed-testing procedure or a jointly calibrated max-statistic/simultaneous-interval scheme
that strongly controls the experiment-wide family-wise error rate at the registered level. A node
can qualify only if the omnibus root and every node on its path pass, together with all conjunctive
equivalence and nuisance gates. Family-local adjustment alone cannot support “at least one painter
feature.” If no defensible omnibus test is frozen, the project may report adjusted coordinate-level
results but cannot make that winner-selection claim.

The sealed external confirmation reuses the identical hierarchy, support, directions, thresholds,
and terminal rules; no branch is added or reweighted after qualification. A separate, similarly
closed hierarchy is required for any future generated-output success claim. False-discovery-rate
procedures may support clearly labeled exploratory coordinates only. Do not select the best
feature, scale, encoder, neighbor, artist, source, or human endpoint after observing results and
then report its nominal interval.

The core decision is conjunctive:

1. measurement error is below the registered SESOI;
2. painter specificity transfers across source and content;
3. nuisance baselines do not explain the result;
4. human convergent/discriminant evidence supports the claimed perceptual interpretation; and
5. external confirmation succeeds.

Null and negative results are retained. A family may fail while another passes its fully adjusted
path; this is a valid study outcome, not permission to reinterpret a nominal family-local result.

## 8. Missingness

Before outcomes, freeze the intended sampling-frame denominator, eligibility rule,
simulation-selected minimum count, and minimum completion proportion for every
painter-by-common-support-by-source cell. Record why work metadata, reproductions, feature values,
or future outputs are missing. Distinguish rights/access failure, provider failure, corruption,
preprocessing-domain exclusion, algorithm failure, and policy refusal. Summarize denominators and
missingness by painter, source, content, medium, date, condition, and their registered joint cells
before scientific estimates.

Model the inclusion/observability indicator using available frame metadata and report differential
selection by painter and every registered nuisance factor. The execution-freeze artifact must
specify complete-case, weighting/standardization, pattern-mixture, worst-case bound, and tipping-
point analyses appropriate to the available metadata. Assumptions that inaccessible works are
missing at random are not inferred from the observed subset.

`qualified_core` requires every inferential cell to retain its frozen minimum and the qualification
decision to survive all registered scientifically plausible missing-not-at-random scenarios. If it
does not, the domain is narrowed without inspecting favorable feature outcomes, or the disposition
becomes `qualified_domain_limited`, `failed`, or `not_executed` as appropriate. In a future
generation study, refused cells are not replaced and their visual features are not imputed;
availability, conditional-success effects, and registered bounds are all reported.

## 9. Supported language

After the corresponding gates pass, acceptable statements include:

- “This coordinate describes the declared digital reproductions' color/spatial/ordinal profile.”
- “The coordinate was repeatable across the tested independent reproductions within the reported
  uncertainty.”
- “A painter-associated signal transferred across the tested sources and content families after
  adjustment for the registered nuisance variables.”
- “The learned appearance distance predicted painterly-manner judgments for the tested raters and
  works beyond content and source baselines.”
- “For the future authorized study, returned named-prompt outputs met the frozen absolute,
  hard-neighbor, target-support, coverage, content-coherence, and availability criteria, while the
  paired comparison quantified movement relative to a matched painter-free control.”

Every statement names the corpus, reproduction domain, method version, and uncertainty.

## 10. Prohibited or unsupported language

Ordinary RGB results do not justify:

- “the painter's true style,” “style essence,” or a universal style score;
- physical pigment, binder, brushstroke topology, impasto, or conservation-state claims;
- authorship, authenticity, forgery, or attribution decisions;
- artistic quality, beauty, creativity, originality, intent, or historical influence;
- legal copyright infringement or substantial-similarity conclusions;
- causal historical evolution from cross-sectional image correlations;
- proof that a model trained on an artist's work or memorized a work; or
- claims about untested painters, cultures, media, institutions, or generated-model identities.

Painter and movement labels are historically contingent metadata. The study measures whether a
specified digital-image representation contains transferable painter-associated signal—not the
totality of an artist's practice.
