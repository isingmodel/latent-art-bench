# Generated-versus-real painter fidelity: focused evidence audit

Review status: full-text or official-method audit of the closest available studies

Review question:

> Which published methods can support a claim that a set of painter-name-conditioned generated
> images reproduces the measurable distribution of a painter's real works?

## 1. Bottom line

No reviewed paper supplies a validated universal measure of generated-to-real painter-distribution
fidelity. The closest work measures one of four adjacent constructs:

1. representation geometry in a large art-history corpus;
2. artist/style retrieval or prompted-name recognition;
3. method-level neural-style-transfer quality; or
4. generic distribution fidelity, coverage, or copying.

The defensible protocol must therefore assemble—but not conflate—the following evidence:

- real-only qualification of the feature space;
- absolute generated-to-real distribution discrepancy;
- comparison with every close painter on the primary `q*` common-content construction;
- support coverage and contraction;
- content-matched named-versus-control effects;
- availability and missingness; and
- a separate near-copy audit.

This is a proposed measurement architecture. Its exact margins and conjunctive rule are not already
validated by the literature. They require real-development-calibrated simulation plus explicit
generator-side refusal, copying, dependence, and missingness scenarios; real-only data cannot by
itself validate generator operating characteristics.

## 2. Direct method audit

| Study | Actual data and task | What it contributes | What it cannot establish |
|---|---|---|---|
| [Kim et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/) | 72,447 paintings, 2,354 painters, 128 periods; 16,384-D SD2-VAE A and 1,024-D CLIP C coordinates for chronology/context geometry | a named appearance-sensitive and semantic-sensitive diagnostic; a warning that representation directions mix multiple art-historical factors | generated-to-real painter fidelity, source-invariant painter measurement, or oeuvre coverage |
| [Somepalli et al. 2024](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf) | CSD trained on 511,921 images/3,840 tags; WikiArt artist retrieval over 80,096 works/1,119 artists; generated prompt studies | set prototypes, content-constrained prompts, close-painter confusions, style-oriented sensitivity | a calibrated universal raw-cosine threshold or complete target-distribution reproduction |
| [Moayeri et al. 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/63ef323523f3be8b58ed9277cc747485-Paper-Conference.pdf) | about 91k WikiArt works/372 artists; CLIP-based DeepMatch and 260-tag TagMatch; generated sets from three models | set-level voting, explicit comparison painters, interpretable cue audit, prompt-dependence warning | that recognized painter names imply unique painterly manner or within-painter coverage |
| [Wright & Ommer 2022](https://arxiv.org/abs/2207.12280) | art-trained encoder, LPIPS content term, style-distribution FID, 13 NST methods, 31,200 crowd pairwise tasks | separate content preservation from style distribution; pairwise human-evaluation precedent | free text-to-image painter specificity at small per-painter samples |
| [Asperti et al. 2025](https://www.mdpi.com/2504-2289/9/9/231) | 953 generated images, 73 prompts, 12 models; period/style/authenticity probes | cross-model warning that style judgments depend on model and evaluator | a high-powered painter-conditional distribution test; diagnostic only |

### 2.1 Kim is a compatibility diagnostic, not the primary measure

Kim et al. resize eligible images to a forced 512×512 input for the A path and sample a scaled
`4×64×64` posterior latent from the Stable Diffusion 2 first-stage autoencoder. The release forces a
square warp, and neither the paper nor code establishes that this 16,384-D code is invariant to
content, source, codec, crop, or that warp. The C coordinate is a CLIP-family
semantic/context representation. Artist-label discrimination and short within-artist distances do
not isolate painterly manner or source-independent coverage.

The released repository at commit
[`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0)
does not provide a complete reproducible artifact contract. The A script contains unreachable model
setup and an undefined `model` reference. The paper's C description and released CLIP Interrogator
configuration also do not establish one exact identical checkpoint contract. A repaired local
extractor is therefore a named adaptation, never the authors' unreleased vector realization.

Protocol consequence: report Kim A compatibility and Kim C/CLIP context as secondary evaluator
families. They cannot select the winning result or rescue a failed interpretable primary family.

### 2.2 CSD and attribution methods test recognizability

CSD deliberately learns style-sensitive cues and is more relevant than generic CLIP. Its WikiArt
evaluation nevertheless uses random work splits and treats painter identity as a proxy. Its
generated validation generally treats the prompted artist as the expected style label. ArtSavant's
set-level DeepMatch and TagMatch provide a useful one-versus-many design, but recognition may be
driven by subject, period, source, a signature, or encoder exposure.

Protocol consequence: use CSD and attribution/tag diagnostics to explain agreements and failures.
Require the primary interpretable representation to pass held-work, held-source, content, signature,
and close-neighbor tests independently.

### 2.3 ArtFID separates content and style but studies another task

ArtFID combines an art-domain Fréchet term with LPIPS content preservation for neural style
transfer, where a content input and stylized output form a natural pair. Free text-to-image outputs
have no source content image, so LPIPS cannot be transported directly. FID also has strong
finite-sample and representation dependence in painter-sized cells.

Protocol consequence: preserve the conceptual separation between content adherence and
distribution fit, but do not use raw ArtFID or FID as the painter conclusion.

## 3. Distribution statistics: what each result means

### 3.1 MMD or energy distance

[Gretton et al. 2012](https://www.jmlr.org/papers/v13/gretton12a.html) provides the kernel MMD
two-sample framework; kernel and bandwidth choices define its sensitivity.
[Székely and Rizzo 2013](https://doi.org/10.1016/j.jspi.2013.03.018) provides the distance-based
energy-statistics foundation; its behavior depends on metric, coordinate scaling, dimension, and
sample design. Both compare distributions only in the chosen coordinate system; neither validates
that the coordinates measure a painter. Clustering and finite-sample power must be handled by the
registered design and simulation.

Use one primary discrepancy, selected before generated outputs. Define practical equivalence from
explicit population-level adverse alternatives; do not infer equivalence from failure to reject a
difference. Protocol 1.7 measures every declared real population as a census, so the summation over
the real side of the generated–real term and the real–real term are exact conditional on that finite
population; the generated-side expectation remains estimated from registered generator draws. No
real-work bootstrap or inverse-probability estimator is used. Under a fixed deterministic local map,
generator uncertainty resamples complete painter/control seed vectors within template. An
opaque/remote endpoint instead resamples only complete balanced common-shock units carrying every
template×condition wave together. Both keep the real census and its `q*` weights fixed.
Horvitz–Thompson and Rao–Wu are retained in the literature package
only as rejected contingencies for a future protocol that genuinely probability-subsamples real
works.

Protocol 1.7 also fixes one coordinate geometry: each coordinate uses the weighted median and IQR
from the equal-painter mixture of the four complete `q*`-weighted development populations, and that
single transform is applied unchanged to every real, control, and generated vector. Painter-specific
scaling would change pairwise distances and is forbidden.

### 3.2 Precision/recall and density/coverage

[Kynkäänniemi et al. 2019](https://proceedings.neurips.cc/paper_files/paper/2019/hash/0234c510bc6d908b28c70ff313743079-Abstract.html)
and [Naeem et al. 2020](https://proceedings.mlr.press/v119/naeem20a.html) separate fidelity-like and
coverage-like support behavior. Density/coverage were proposed in part to repair failure modes of
earlier neighborhood estimators; the four numbers are not four independent validated constructs.

Protocol 1.7 keeps both neighborhood-estimator families as sample-size-, dimension-, outlier-, and
\(k\)-sensitivity diagnostics; neither is a primary gate or may rescue a failed result. Primary
coverage instead uses the frozen twelve-coordinate median-difference and IQR-ratio panel, with
10th/90th percentiles descriptive and family energy carrying the registered tail alternatives.

### 3.3 All-neighbor specificity

Generated images may be close to several painters in a shared movement. Target specificity must
therefore compare the target with every painter in a fixed close-neighbor panel, and every frozen
neighbor margin must pass. Before any active content label is read, R0a freezes and hashes every
prompt/render byte in 12 candidate complete 24-template frames; independent wording review ends
then, and G0 may verify hashes and substitute painter names but cannot rewrite a string. After
painter-level population assignment it selects one common frame using only
three nonredundant proportions over four broad scene groups plus five visible-property means. The
primary real construction is the `q*`-
weighted complete sealed-confirmation census matching that same target, and the generated
construction weights each selected template equally. The former six narrow submotifs are
nonbinding diagnostics. The result is specific to the observed real-source mixture. The full frame
caps groups at 30% and multi-source scenes at 70% under unweighted shares only; each assigned
internal population applies the same ceilings to unweighted and applicable `q*` shares. Optional
external populations require two unopened groups and a 70% overall unweighted/`q*` ceiling. No full-
frame `q*` exists. Source-specific
and leave-one-source analyses are binding robustness checks, including the exact within-painter×scene
source-versus-complement median-shift RMS compared with the independent-capture bound and repeated
under uniform weights; exact common
source×broad-scene-group comparisons are mandatory diagnostics where supported, not primary cells
or a license to impute absent cells. A broad-negative victory is not enough.

[Csiszár (1975)](https://doi.org/10.1214/aop/1176996454) supplies the I-projection foundation for
minimizing KL/I-divergence from a base distribution under linear moment constraints. It does not
validate this study's eight content moments, four-times unit-mass cap, 60% ESS floor, source caps, or
painter-fidelity construct. Those are project-specific feasibility and robustness gates whose
operating behavior must be checked before feature access.

### 3.4 Copying is not fidelity

[Pizzi et al. 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Pizzi_A_Self-Supervised_Descriptor_for_Image_Copy_Detection_CVPR_2022_paper.html),
[Somepalli et al. 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Somepalli_Diffusion_Art_or_Digital_Forgery_Investigating_Data_Replication_in_Diffusion_CVPR_2023_paper.html),
and [Carlini et al. 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/carlini)
support a separate exact/near-copy search. A close copy can reduce target distance while reducing
evidence for distributional generalization. Conversely, no hit in a finite searchable corpus cannot
prove absence from an opaque training set.

Protocol consequence: generated quantiles preserve the equal-template estimand with per-output
weight `1/(24 m_t)`. A blind realized-content entropy projection is a binding sensitivity under the
same convex-hull, weight-cap, and ESS gates, is recomputed inside every generator replicate, and may
make a result content-sensitive or inconclusive but cannot rescue the intention-to-prompt primary.
Continuous feature/distance endpoints use the generator-vector max statistic; availability,
adherence, and copy are excluded from it and use separately allocated Bonferroni weighted-Hoeffding
bounds plus conservative conditional-rate ratios. A full rate endpoint contributes four directional
events—`A` lower, `A` upper, `J` lower, and `K` upper—to `M_rate`. Before execution, G0 aggregates
request weights into auditable independence units and the bound uses `sum_c W_c^2`. Independent
local seeds may define units; remote IDs/timestamps do not, so plausible provider episodes, batches,
backend/moderation states, outages, retries, and common shocks stay together. An unjustifiable or
uninformative partition, crossed shock, or unusable balanced unit makes both affected rate and
continuous endpoints ineligible or inconclusive; simulation includes pixel/feature common shocks. A
nonstructural zero replicate variance is inconclusive, not exact certainty.

[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830) is the mathematical source for
the one-sided bounds on independent weighted bounded unit contributions. The same prospective
independence units bind continuous inference: remote endpoints resample whole balanced units, never
their constituent requests, waves, templates, or conditions. An independence or alignment failure
makes both rate and continuous endpoints ineligible or inconclusive. Hoeffding does not supply the
study's alpha allocation, endpoint inventory, ratio construction, or .90/.80/.10 scientific gates;
the protocol must freeze and simulate those choices under its actual shared-vector design.

## 4. Evidence-grounded study stack

1. Define the two-part estimand as availability/content adherence over every registered request and,
   among technically analyzable near-copy-excluded returns, the equal-weight distribution for one
   exact model, selected 24-template frame, and seed/request population versus the primary `q*`-
   content-standardized complete R0a-frozen sealed-confirmation population; disclose its observed
   source mixture.
2. Before any active content label is read, freeze and hash every prompt/render byte of 12 candidate
   complete 24-template frames; G0 cannot rewrite them. Build a physical-work identity graph, acquire
   and verify the 1,440-work internal finite frame, and keep captures and derivatives nested inside
   works. Optional external replication adds a complete 96-work population per painter (384 overall),
   while an auxiliary independent-capture census of at least 32 works remains outside both totals.
3. Firewalled-code the four broad scene groups, narrow diagnostics, and five visible properties;
   retain every screening/union-eligible denominator and preserve pre-adjudication 0.90 eligibility,
   0.10 ambiguity, 0.85 three-state content, and coder-specific 0.20 indeterminate receipts; make one painter-
   level exposure-role permutation assigning 72 development, 108 qualification, and at least 180
   confirmation works per painter; then select one candidate prompt frame and freeze every complete
   real population's primary `q*` and applicable source shares. Forbid R0b population redefinition.
4. Fit one equal-painter pooled-development median/IQR transform. Qualify three interpretable feature
   families on the complete development and qualification populations with the exact source-versus-
   complement gate and independent-capture bound. Freeze energy, the twelve-coordinate median/spread
   panel, margins, generator-only resampling, and the generator repetition count through whole-
   decision simulation; compute the exact real-side cross-term summation and real–real component,
   keep generator expectations estimated, and hold every real population fixed.
5. Generate the full selected 24-template named and painter-free grid without output selection or
   exact joint-profile matching. Every condition uses the same `R`. A fixed deterministic local map
   uses independent template-specific IID-uniform seed lists with replacement and retains chance
   duplicates. Opaque/remote execution uses `C` equal-size common-shock units, each with `L` complete
   template×condition waves, so `R=CL`. The active four-painter request count is `120R`. The former
   `R=16`/1,920-request design is retired; even the impossible all-independent best case requires
   `R>=25` and at least 3,000 requests, while clustering and whole-decision simulation determine the
   larger actual `R`. G0 freezes the same unit map for rate bounds and continuous resampling; a
   cross-boundary shock or indefensible/uninformative partition means no eligible rate or continuous
   conclusion.
6. In G1b double-code every sealed-confirmation and technically analyzable generated image, seal raw
   condition-scoped 0.85/0.20 receipts, and create third-coder consensus only after passing; failure
   makes affected endpoints inconclusive. Test absolute fit, the conjunction of all prespecified
   pairwise-neighbor specificity contrasts, coverage/contraction, broad-scene, realized-content, and
   uniform-real robustness, availability, and copying as separate outcomes under intention-to-prompt.
   Keep the continuous max statistic separate from the boundary-safe rate-bound family.
7. Use Kim, CSD, CLIP, attribution, FID, and human judgments as named diagnostics or extensions.
8. Report per-painter, per-model component results; do not manufacture one universal style score.

## 5. Skeptical conclusion

The strongest claim justified today is not that the project has a validated painter-fidelity metric.
It is that the project now has a preregisterable proposal assembled from adjacent evidence, with
explicit failure modes and a plan to validate its operating characteristics. Direct empirical
validation still has to be earned: active admissions, downloads, generated outputs, and results are
all zero, and R0a remains NO-GO.
