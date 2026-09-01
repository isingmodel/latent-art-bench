# Analysis, estimands, and claims policy

Protocol version: `painter_features_v1/analysis/1.0`

Status: design only; final numeric choices require prospective simulation

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

### R1. Reproduction error

For coordinate family \(f\), estimate the distribution of the within-work difference across
independent reproductions:

\[
E_f = z_{w,r_1,f} - z_{w,r_2,f}.
\]

Report variance components, repeatability coefficients, and vector-distance distributions by
source pair and preprocessing branch.

### R2. Painter-associated variance

Estimate how much residual variation is associated with painter after accounting for registered
nuisance factors. For scalar coordinates, use a cross-classified hierarchical model such as

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

For target painter \(a\), hard neighbor \(h\), broad-negative set \(B\), and held-out work \(x\),
estimate calibrated log-score or distance margins:

\[
M_{a,h}(x) = D(x, h) - D(x, a),
\]

where \(D\) integrates reference-distribution uncertainty and is fitted on training works only.
Positive margins favor the target. Report work-level margins, painter-balanced aggregates,
calibration, source/content transfer, and their uncertainty. Hard neighbors are a set when
possible; no conclusion rests on one favorable neighbor.

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

Let \(G^{named}_{a,c}\) and \(G^{control}_{c}\) be generated distributions for target painter
\(a\) and content block \(c\); let \(P_a\) be the qualified real painter distribution. Distances
below are evaluated within the frozen qualified profile and integrate real-reference uncertainty.

### G1. Target fidelity improvement

\[
\Delta_{target} = D(G^{control}_{c}, P_a) - D(G^{named}_{a,c}, P_a).
\]

Positive values mean named prompting moved the output distribution toward the target painter
feature. This retains Pilot 2's paired control logic.

### G2. Painter specificity difference-in-differences

For hard neighbor \(h\):

\[
\Delta_{specificity} =
[D(G^{named}_{a,c},P_h)-D(G^{named}_{a,c},P_a)]
-[D(G^{control}_{c},P_h)-D(G^{control}_{c},P_a)].
\]

Average only under a preregistered equal-painter/hard-neighbor rule. Report the entire neighbor
panel and broad-negative calibration; a single neighbor margin is not enough.

### G3. Within-painter coverage

Estimate which regions of the real painter distribution are represented across prompts and seeds.
Coverage is separate from proximity: a generator can be near a centroid while reproducing only
one narrow mode.

### G4. Contraction or expansion

Compare generated within-target dispersion with real within-painter dispersion after matching
content and accounting for finite real-reference uncertainty. Report direction and magnitude;
neither greater nor lower diversity is automatically better.

### G5. Content coherence and prompt interaction

Estimate whether painter-associated movement is consistent across content blocks and whether the
name effect interacts with particular subjects. The content block, not the seed, is the unit of
generalization.

### G6. Availability

Report the probability that a registered request yields an eligible analyzable output, including
refusals and terminal failures. Availability is a separate estimand. The scientific effect among
successful outputs is not silently described as intention-to-request when informative refusals
remove cells.

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
- k-nearest-neighbor precision/recall, density, and coverage are diagnostic in high-dimensional
  or small-sample settings; dimensionality and \(k\) sensitivity must be shown.
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
4. for future outputs, resample content blocks, then paired named/control seed sets within block.

The painter-source-content crossing is preserved. A cluster interval based on pixels, patches, or
seeds alone is invalid. Where the number of top-level units is small, use exact or restricted
randomization only when its exchangeability/symmetry assumptions are defensible; otherwise report
the limited precision without manufacturing a small \(p\)-value.

## 7. Multiplicity and decision policy

Primary families and estimands are frozen before qualification outcomes. Use simultaneous
confidence intervals or a max-statistic permutation procedure within each registered family. A
false-discovery-rate procedure may support clearly labeled exploratory coordinates. Do not select
the best feature, scale, encoder, neighbor, artist, or source after observing results and then
report its nominal interval.

The core decision is conjunctive:

1. measurement error is below the registered SESOI;
2. painter specificity transfers across source and content;
3. nuisance baselines do not explain the result;
4. human convergent/discriminant evidence supports the claimed perceptual interpretation; and
5. external confirmation succeeds.

Null and negative results are retained. A method family may be rejected while another qualifies;
this is not a failed study.

## 8. Missingness

Record why work metadata, reproductions, feature values, or future outputs are missing. Distinguish
rights/access failure, provider failure, corruption, preprocessing-domain exclusion, algorithm
failure, and policy refusal. Summarize missingness by painter, source, content, medium, date, and
condition before scientific estimates.

Complete-case inference is permitted only under its declared missingness estimand and with a
comparison to the registered sampling frame. In a future generation study, do not replace refused
cells or impute their visual features. Report availability and, if scientifically justified,
bounds or sensitivity analyses for the conditional successful-output effect.

## 9. Supported language

After the corresponding gates pass, acceptable statements include:

- “This coordinate describes the declared digital reproductions' color/spatial/ordinal profile.”
- “The coordinate was repeatable across the tested independent reproductions within the reported
  uncertainty.”
- “A painter-associated signal transferred across the tested sources and content families after
  adjustment for the registered nuisance variables.”
- “The learned appearance distance predicted painterly-manner judgments for the tested raters and
  works beyond content and source baselines.”
- “Named prompting moved the returned output distribution toward the qualified painter profile
  relative to a matched painter-free control,” for a future authorized study.

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
