# Painter Features v1: standalone measurement protocol

Protocol ID: `painter_features_v1/measurement/2.0`

Status: standalone prospective research protocol; scientifically specified but not
execution-frozen; no acquisition, feature extraction, model download, external-set access, or
image generation is authorized by this document

Normative scope: real, digitized paintings and their reproductions

## 0. Authority and use

This document is the canonical starting point for measuring painter-associated image features.
It defines the construct, sampling units, observation model, corpus design, preprocessing,
candidate measurements, qualification gates, inferential rules, outputs, claim ceilings, and
failure actions needed to conduct the real-image study.

An independent researcher should be able to understand the proposed method from this file alone.
Background evidence may explain why particular choices were made, but it does not supply a
missing requirement and cannot relax this protocol. If another document conflicts with this
protocol on real-image measurement, this protocol controls until a new numbered version
explicitly supersedes it.

The protocol separates two layers:

1. **Method specification**, fixed here: what the painter feature means, how observations are
   organized, which measurement families are admissible, how they are qualified, and which
   claims are allowed.
2. **Execution freeze**, still required: the named painters and works, rights, source workflows,
   common-support tables, sample-size simulation, exact software artifacts, final parameter
   values, smallest effects of scientific interest, multiplicity tree, missingness scenarios,
   partitions, and terminal decisions for one empirical run.

The execution freeze may instantiate choices that this protocol explicitly leaves to prospective
simulation or development-only calibration. It may not weaken a gate, change the construct, add an
outcome-guided exception, or authorize extrapolation. Such a change requires a new protocol
version.

This protocol does not evaluate generated images. A later generator study may use only painter
measurements that first qualify here and must receive its own frozen design.

### Protocol at a glance

| Element | Binding choice |
|---|---|
| Scientific target | Conditional painter-associated distribution across eligible physical works |
| Inferential unit | Physical work; reproductions, crops, pixels, patches, and ratings are nested |
| Primary candidate panel | Color, chromatic transitions, Fourier structure, gradients, wavelets, and ordinal patterns |
| Main identification requirement | One connected painter × content × medium × phase × workflow common support |
| Main validity requirement | Simultaneous hard-neighbor margins above positive SESOIs under source/content transfer |
| Human interpretation | Allowed only after blinded, held-work convergent and discriminant validation |
| Broadest claim | Requires one-use confirmation on an unopened institution/capture workflow |
| Final product | Versioned painter profiles containing distributions, uncertainty, coverage, and claim ceilings |
| Explicit non-product | No universal painter/style score and no physical-material or authenticity inference |

## 1. Research aim and claim target

### 1.1 Primary research question

Which measurements of digitized paintings form a reproducible, source-resistant, and
content-resistant distribution associated with an attributed painter across held physical works?

The aim is not to find one vector that summarizes an artist. The aim is to estimate a qualified
multidimensional profile whose variation across works is part of the result.

### 1.2 Target construct

The target construct is **painter-associated visual practice observable in declared digital
reproductions of eligible physical works**. The shorthand *painter feature* refers to a
conditional distribution of separately qualified measurement coordinates, not to:

- one painting;
- one downloaded file;
- a feature centroid;
- an artist-classifier score;
- an encoder embedding without construct validation;
- movement, period, genre, subject matter, or institution;
- the painter's intention, essence, quality, or total practice; or
- physical material properties not observable in ordinary RGB reproductions.

Painter attribution is historical metadata supplied by the frozen corpus policy. This protocol
tests whether declared image measurements contain transferable painter-associated structure; it
does not authenticate or reattribute works.

### 1.3 Core hypotheses

For a candidate family to contribute to the painter feature, all applicable hypotheses must
survive the registered decision process:

- **H-M measurement identity:** the implementation produces the declared coordinate within its
  computational tolerance.
- **H-R reproduction adequacy:** measurement error across eligible independent reproductions is
  smaller than the prespecified scientifically tolerable error.
- **H-P painter specificity:** held works are closer to the correct painter distribution than to
  every registered hard-neighbor distribution by more than neighbor-specific minimum effects.
- **H-T transfer:** H-P survives held source workflow, held content family, and their joint
  holdout.
- **H-N nuisance increment:** the painter result adds information beyond source, content, medium,
  phase/date, derivative, and visible attribution-cue baselines.
- **H-H human convergence:** when a perceptual painterly-similarity interpretation is claimed, the
  measurement predicts blinded human judgments beyond content and source baselines.
- **H-E external confirmation:** a core claim repeats once under the frozen method on an unopened
  institution/capture workflow.

Failure of one required hypothesis lowers the disposition or ends the claim. Success on an easier
hypothesis cannot compensate for failure on a harder one.

### 1.4 Claim ladder

Claims rise only in this order:

1. `digital_file` — a coordinate describes declared bytes and processing.
2. `digital_derivative` — it is repeatable across derivatives of one capture.
3. `reproduction_associated` — it is stable enough across independent reproductions in the tested
   domain.
4. `qualified_domain_limited` — it shows painter specificity and transfer only in a
   declared source, content, medium, or phase domain.
5. `qualified_core` — it passes all applicable measurement, transfer, human, missingness,
   multiplicity, and unopened-workflow external gates for the stated population.

No level inherits the language of the next level automatically.

## 2. Units, indices, and vocabulary

| Term | Definition |
|---|---|
| Painter \(a\) | Attributed painter under the frozen attribution policy |
| Physical work \(w\) | The underlying painting; highest-level real-image sampling unit |
| Nuisance cell \(q\) | Joint content/genre \(c\), medium/support \(m\), and career-phase/date band \(t\) |
| Provider/workflow \(s\) | Institution plus capture/digitization workflow when separable; otherwise the narrowest identified workflow unit |
| Capture \(r\) | One independently produced photographic or scanning event |
| Delivery derivative \(d\) | A resize, recompression, crop, or delivery object derived from one capture |
| Processing branch \(p\) | Deterministic analysis transform applied by the study |
| Reproduction | A capture or a declared derivative of a capture; its independence class must be known |
| Derivative family | All files descended from one capture/master, including URLs, crops, and recompressions |
| Feature coordinate \(z_f\) | A versioned numerical measurement with a declared input, formula, unit, and interpretation |
| Feature family \(F\) | Related coordinates answering one construct question |
| Painter profile | A standardized conditional distribution of qualified coordinates across eligible works |
| Hard neighbor \(h\) | A historically or visually plausible comparison painter fixed before feature outcomes |
| Broad negative | A comparison outside the hard-neighbor panel, used for calibration and diagnostics |
| Common support | The frozen joint nuisance and workflow cells observed for every painter in a registered contrast |
| SESOI | Smallest effect size of scientific interest, fixed before qualification outcomes |
| Qualification | Evidence that a coordinate meets every gate required for its stated claim |

Pixels, patches, crops, pyramid cells, augmentations, ratings, and repeated model runs are
subsamples. They never increase the number of independent physical works.

## 3. Formal measurement model

### 3.1 Observation model

Let \(X_{awsrdp}\) be the processed observation for work \(w\), attributed to painter \(a\), in
workflow \(s\), capture \(r\), delivery derivative \(d\), and processing branch \(p\). For
coordinate \(f\),

\[
z_f(X_{awsrdp}) =
\theta_{awf}
+ b_{sf}
+ b_{r(w,s)f}
+ b_{d(r)f}
+ b_{pf}
+ \eta_{q(w)f}
+ \gamma_{a,q(w),f}
+ \varepsilon_{awsrdpf}.
\]

\(\theta_{awf}\) is work-associated variation; \(b_s\), \(b_r\), and \(b_d\) describe the
identified observation hierarchy; \(b_p\) describes analysis processing; \(\eta_q\) describes
registered nuisance structure; \(\gamma_{a,q}\) permits painter practice to vary across content,
medium, and phase; and \(\varepsilon\) is residual error.

This equation is an identification map, not an assumption that all effects are additive,
homoscedastic, or independently estimable. Interactions and nonlinear terms are included when
chosen by prospective simulation. Provider, capture, and delivery effects may be collapsed into a
narrower `source/capture workflow` term when the incidence matrix cannot separate them.
Deterministic processing branches must instead be crossed over every eligible reproduction; an
unidentified processing effect is a design failure, not a term to absorb into painter signal.

### 3.2 Standardized painter distribution

For a registered painter contrast set \(A\), define \(q=(c,m,t)\). Let
\(\Omega_A^*\) contain only nuisance cells eligible for every painter in \(A\), and let
\(\mathcal S_{Aq}^*\) contain only source/capture workflows shared by every painter in cell \(q\).
Freeze one set of target-population or equal-cell weights \(\omega_{Aq}^*\) and one common workflow
distribution \(\nu_{A,s\mid q}^*\). The painter profile is

\[
\mathcal P_a^*(z;A)=
\sum_{q\in\Omega_A^*}\omega_{Aq}^*
\sum_{s\in\mathcal S_{Aq}^*}
\nu_{A,s\mid q}^*P\{z(X)\mid a,q,s\}.
\]

All painters in a contrast use the same support and weights. Observed post-exclusion frequencies
do not replace the frozen weights. Cells outside common support are descriptive and are never
recovered by regression extrapolation.

### 3.3 Hard-neighbor panel

For target painter \(a\), freeze the complete panel \(H_a\) before support construction or feature
outcomes and define

\[
A_a^{panel}=\{a\}\cup H_a.
\]

The target and every hard neighbor use one panel-wide support, workflow set, and weight system.
The panel is not pruned after overlap or outcomes are seen. If only pairwise supports exist,
pairwise domain-limited margins may be reported, but they cannot be aggregated into a panel
minimum, omnibus specificity decision, or core painter claim.

### 3.4 Painter specificity margin

For held work \(x\) attributed to target \(a\), define a frozen family-specific scoring rule
\(D_F\) and margin against hard neighbor \(h\):

\[
M_{a,h,F}(x)=
D_F\{x,\mathcal P_h^*(\cdot;A_a^{panel})\}
-D_F\{x,\mathcal P_a^*(\cdot;A_a^{panel})\}.
\]

Positive values favor the target. The score is estimated entirely from training works and
propagates finite-reference uncertainty. Every family reports work-level margins, not only
aggregate accuracy.

## 4. Study design

### 4.1 Target population and sampling frame

The execution freeze must define a target population before images are selected. For every
physical work in the intended frame it records:

- attribution status and allowed uncertainty;
- title or stable work identifier;
- date or date interval and career-phase rule;
- medium/support;
- subject, genre, or content-family rule;
- dimensions and collection/institution;
- known capture/provider options;
- rights, access, and redistributability; and
- eligibility, exclusion, and missingness status.

Works are sampled from this frame. The study does not collect until a convenient number is
reached. Painter, source, content, medium, and phase may not be perfectly aliased.

### 4.2 Common-support eligibility

Before feature outcomes, publish the complete painter × content × medium × phase × workflow ×
physical-work incidence table. Confirmatory support must satisfy all of the following:

- the painter-by-joint-nuisance incidence graph is connected for every registered contrast;
- each exchangeability block contains at least two painter labels;
- every painter-by-\((q,s)\) cell contains at least two independent physical works;
- the simulation-selected minimum, when greater than two, replaces that floor;
- every painter is observed under at least two independent source/capture workflows for a core
  transfer claim;
- every hard-neighbor panel uses one connected support and one fixed weight table; and
- no confirmatory result depends on a cell unique to one painter.

Two works per cell is an identifiability floor, not a claim of adequate precision. If support or
simulation requirements fail, the painter set or claim domain is narrowed before outcomes.
Otherwise the affected comparison is `failed` or `not_executed`.

### 4.3 Reproduction panel

A preregistered subset of works must have at least two independently produced captures, covering
every inferential group and workflow. Two URLs or recompressions of one master are not independent.
The execution freeze classifies every reproduction as:

- independent capture;
- derivative of a known capture;
- catalog scan;
- screenshot/display-rendered copy; or
- unknown provenance.

Unknown-provenance files may enter sensitivity analysis but cannot establish cross-capture
reliability.

Before acquisition, freeze a physical-work × provider × capture × delivery × processing incidence
matrix and audit its design rank. To estimate separate terms:

- repeated works must connect provider/capture workflows;
- every provider-pair edge must contain at least two works or the larger simulation minimum;
- a capture needs repeated delivery derivatives to identify delivery variation; and
- every deterministic processing branch must be applied to every eligible reproduction.

If provider, capture, and delivery remain inseparable, collapse them into the identified workflow
term and restrict the claim to that workflow domain. Statistical regularization does not repair a
rank-deficient design.

### 4.4 Data partitions

Freeze nonoverlapping partitions at both physical-work and derivative-family levels:

| Partition | Permitted use |
|---|---|
| Method fixtures | Formula, serialization, and runtime identity tests only |
| Development | Select coordinate options, scales, masks, tolerances, and estimator settings |
| Qualification | Run the locked measurement and transfer gates |
| Human criterion | Final blinded judgment validation; no metric tuning |
| External confirmation | Opened once after the full method and decision tree freeze |

The same physical work, capture, derivative family, or near duplicate cannot cross partitions.
Final human works and raters cannot tune the metric.

For leave-source claims, the entire selection algorithm is nested at the source-workflow level.
The held workflow contributes no images, labels, transformations, normalization statistics,
thresholds, or outcome summaries to selection. Refitting after global source inspection does not
remove leakage.

### 4.5 Sample-size determination

The execution freeze must include prospective simulation using the planned incidence structure,
plausible reproduction error, within-painter heterogeneity, nuisance effects, missingness, and
multiple-testing procedure. It selects:

- works per painter and joint-support cell;
- independently reproduced works per workflow pair;
- qualification and external-set sizes;
- human works, raters, and judgments per work;
- precision targets for variance and margin estimates; and
- minimum completion proportions.

No number of pixels, patches, derivatives, or ratings compensates for too few physical works.

### 4.6 Attribution, duplication, and leakage

Recto/verso views, tiles, crops, restored derivatives, color variants, and resized copies share a
derivative-family identifier. Perceptual hashes are screening aids followed by provenance review;
they do not replace stable work and capture identifiers. Near-duplicate screening occurs before
partition freeze and again before external opening.

Disputed or workshop attributions are included only under a predeclared policy. Sensitivity
analyses may vary the attribution set, but the primary set is not changed after feature outcomes.

## 5. Provenance and preservation

### 5.1 Required manifest row

Each acquired file must have one immutable manifest row containing, when applicable:

- study, painter, physical-work, reproduction, capture, derivative-family, provider, and workflow
  identifiers;
- canonical object page and exact asset URL;
- acquisition timestamp, access terms, license, and HTTP/content metadata;
- original byte hash, length, MIME type, codec, bit depth, dimensions, and orientation;
- ICC profile name and hash, EXIF/XMP presence, alpha channel, and declared color space;
- stated capture device/workflow, illumination, target, calibration, and pixels-per-unit;
- frame, mat, border, label, watermark, signature, crop, stitching, glare, damage, and restoration
  flags;
- content, medium, phase/date, dimensions, and attribution values with source and uncertainty;
- exclusion/missingness reason; and
- hashes of every normalized derivative and its preprocessing receipt.

An absent ICC profile is recorded as unknown, not interpreted as proof of sRGB.

### 5.2 Preservation rules

Original bytes and metadata are immutable. Normalized images are new derivatives and never
overwrite a source file. The decoder, color library, profiles, operating system, and software
versions are recorded. Large or restricted bytes remain in the designated research workspace;
only compact redistributable manifests, hashes, definitions, and reports enter version control.

### 5.3 Terminal file outcomes

Every intended file ends in exactly one state:

- acquired and eligible;
- acquired but excluded by a prespecified rule;
- unavailable because of rights/access;
- unavailable because of provider failure;
- corrupt or undecodable;
- outside the declared color/scale domain; or
- not attempted because an earlier terminal condition closed the operation.

There is no silent replacement with another work, provider, or derivative after the frame freezes.

## 6. Image-domain and preprocessing contract

### 6.1 General invariants

All preprocessing is deterministic, versioned, and receipt-producing. The painted field is
preserved at its native aspect ratio. No primary branch:

- stretches an image to a square;
- upsamples an unsupported scale;
- treats masked pixels as black observations;
- applies automatic enhancement;
- guesses an undocumented color profile without a separate sensitivity label; or
- selects a crop after viewing feature outcomes.

### 6.2 Preservation branch

The preservation branch contains the original bytes and decoded metadata only. It is used for
provenance and decoder checks, never as a mutable analysis image.

### 6.3 Harmonized analysis branch

For a valid embedded profile:

1. decode with recorded orientation and no automatic enhancement;
2. convert through an ICC-aware library using the embedded profile, frozen rendering intent, and
   D50 profile-connection space;
3. create a linear-light luminance representation for signal measurements;
4. create a CIELAB D50 representation for perceptual-color measurements;
5. preserve the confirmed painted-field aspect ratio;
6. apply the frozen frame/label/watermark/signature mask; and
7. serialize a deterministic lossless derivative and receipt.

Files without a usable profile form a separate provenance stratum. An assumed-sRGB sensitivity
branch is allowed, clearly labeled, and never pooled with color-managed files unless it passes the
same reproduction and transfer gates.

### 6.4 Source-faithful diagnostic branch

A published method may require grayscale conversion, forced-square resizing, model-native crop,
codec round-trip, or stochastic sampling. Those operations remain confined to a named diagnostic
branch. Missing code, weights, hashes, environment, fixtures, or stochastic realization prevents
an exact-replication claim. A repaired implementation is labeled an adaptation.

### 6.5 Painted-field mask

The execution freeze defines who creates masks, what evidence is visible, the quality-control
sample, and the adjudication rule. Frames, mats, labels, watermarks, transparent padding, and
nonpainting backgrounds are masked. Signature handling has two branches:

- primary painter-association measurement reports the unaltered painted field with a
  signature-presence nuisance indicator; and
- human painterly-manner validation and attribution-cue sensitivity use a frozen signature/text
  mask where identity could be disclosed.

Mask geometry is fixed without using painter-classification or feature outcomes. Masked mass and
geometry are reported so a family sensitive to mask boundaries can be failed or limited.

### 6.6 Multiscale pyramid

The default long-edge grid is 2048, 1024, and 512 pixels, using aspect-preserving antialiased
downsampling. A level above native resolution is missing, never upsampled. The execution freeze
records the resampler, boundary rule, color domain, and mask handling. Primary results retain the
response curve across supported scales. A single scale may become primary only through
development-only selection nested inside every outer source split.

## 7. Candidate measurement panel

### 7.1 Rules shared by every feature card

Each implementation must publish:

- feature ID and semantic version;
- construct and non-construct statement;
- exact input branch, scale, mask rule, and units;
- equations and every constant;
- software and dependency versions;
- a redistributable fixture with expected output and tolerance;
- missingness and unsupported-input behavior;
- coordinate names and ordering;
- family-specific distance or scoring rule; and
- perturbations expected to preserve or change the coordinate.

Unless a card states otherwise, scalar summaries use the fixed quantile grid
\(Q=\{0.01,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.99\}\). Bins, thresholds, kernels, projection
directions, dimension reduction, and combination weights are selected on development data only,
then frozen. Coordinate standardization uses development medians and robust scales inside each
training fold. A zero development scale makes the coordinate degenerate and therefore
nonqualifying.

The primary candidate panel is PF-C1, PF-C2, PF-S1, PF-S2, PF-S3, and PF-O1. PF-M1 is secondary.
PF-L1 and PF-X1 are diagnostics unless they independently pass every applicable gate. Families
remain separately visible; no universal painter score is constructed.

### 7.2 PF-C1 — perceptual color distribution

**Question.** Does the painter show a transferable distribution of perceptual lightness, chroma,
and hue organization?

**Input.** Masked CIELAB D50 harmonized image at every supported scale.

**Algorithm.**

1. Compute \(L^*\), \(C_{ab}^*=\sqrt{a^{*2}+b^{*2}}\), and
   \(h=\operatorname{atan2}(b^*,a^*)\) for valid painted-field pixels.
2. Report the \(Q\)-quantiles of \(L^*\) and \(C_{ab}^*\).
3. Use \(C_{ab}^*=5\) as the primary low-chroma threshold; report low-chroma mass separately and
   compute chroma-weighted circular first and second hue moments only above the threshold.
   Thresholds 2 and 10 are frozen sensitivity branches, not alternative primary outcomes.
4. Compute a fixed-bin joint \(L^*\)-\(C^*\)-hue occupancy distribution. Edges are fixed from
   physically valid ranges or development-only calibration and are identical across painters.
5. Normalize histogram mass over valid painted-field pixels.

**Comparison.** Coordinate-wise differences remain visible. Distributional comparison uses
one-dimensional Wasserstein distances for lightness/chroma and a frozen circular or histogram
distance for hue/joint occupancy. Any family aggregation is fixed before qualification.

**Required controls.** ICC conversion, profile removal, assumed-sRGB, white balance, gamma/tone,
JPEG, resampling, masking, and independent reproduction.

**Claim ceiling.** Digital-surrogate color organization under the declared workflow. It is not a
pigment palette, original illumination reconstruction, or physical color truth.

### 7.3 PF-C2 — adjacent chromatic-transition distribution

**Question.** Is local color-transition organization stable and painter-associated across source
and content?

**Input.** CIELAB D50 image at every supported scale.

**Algorithm.**

1. Compute horizontal and vertical adjacent-pixel \(\Delta E_{00}\) values only where both pixels
   are inside the painted-field mask.
2. Retain the full empirical horizontal and vertical distributions.
3. Report \(Q\)-quantiles, mean, robust spread, horizontal–vertical contrast, and valid-pair count.
4. Report raw response curves and a separate mean-rescaled shape branch. The normalized branch
   never replaces the raw magnitude.
5. A source-faithful historical color-distance formula, when implemented, receives a separate
   feature ID and cannot silently replace \(\Delta E_{00}\).

**Comparison.** Use frozen Wasserstein or energy distance on the empirical transition
distributions, with horizontal and vertical components separately visible.

**Required controls.** Scale, resampler, codec, sharpening, ICC, mask boundary, and direction.

**Claim ceiling.** Local digital chromatic-transition structure at declared observation scales.

### 7.4 PF-S1 — multiscale spatial-frequency profile

**Question.** Does luminance contrast energy across scale and orientation transfer across painter
works, contents, and workflows?

**Input.** Masked linear-light luminance at every supported scale.

**Algorithm.**

1. Require a complete rectangular painted-field analysis domain. A file with an internal mask is
   missing for PF-S1 rather than inpainted; a frame mask may define the rectangle but contributes
   no pixels.
2. Apply a separable Tukey window with \(\alpha=0.25\). A different window is a separately
   counted candidate.
3. Compute the two-dimensional discrete Fourier transform and power spectrum.
4. Aggregate power into octave bands expressed in cycles per painted-field width.
5. Report band-power proportions, horizontal/vertical anisotropy, and robust spectral slope over
   a prospectively fixed frequency interval.
6. Report curvature or residual lack-of-fit to a single power law. Do not report a slope when
   support, mask leakage, or fit diagnostics fail.

**Comparison.** Use standardized coordinate differences and the family margin model; retain every
band and the fit-failure indicator.

**Required controls.** Crop, frame, aspect ratio, mask, resize, resampler, blur, sharpening,
compression, and independent reproduction.

**Claim ceiling.** Digital luminance energy organization. A slope alone is not fractality,
brushstroke physics, or artistic quality.

### 7.5 PF-S2 — oriented-gradient organization

**Question.** Is edge and orientation organization painter-associated beyond content and
reproduction effects?

**Input.** Linear-light luminance; color-gradient magnitude is a separately identified
sensitivity branch.

**Algorithm.**

1. Apply the 3×3 Scharr derivative with reflect boundary handling.
2. Freeze a gradient-magnitude threshold using development data only and retain the entire
   threshold-response curve as a robustness output.
3. Compute edge density, an 18-bin equal-width unsigned orientation distribution over
   \([0,\pi)\), orientation entropy, and anisotropy.
4. Compute PHOG-like profiles on fixed 1×1, 2×2, and 4×4 spatial grids.
5. Compute cross-scale self-similarity only from identically defined pyramid cells.

**Comparison.** Compare the complete orientation and spatial-pyramid profiles with a frozen
histogram distance; report scalar summaries separately.

**Required controls.** Threshold, blur/noise, framing, crop, resampling, content family, and
independent reproduction.

**Claim ceiling.** Edge and orientation organization in the declared digital images, not
composition, visual rightness, or physical mark direction by itself.

### 7.6 PF-S3 — wavelet energy and texture profile

**Question.** Does multiscale, multi-orientation texture energy form a transferable painter
profile?

**Input.** Linear-light luminance at every supported scale.

**Default candidate algorithm.** Use a four-level two-dimensional discrete wavelet transform with
the Symlet-4 wavelet and symmetric boundary handling. At each level, report horizontal, vertical,
and diagonal squared-coefficient energy normalized by total detail energy across all retained
bands; Shannon entropy of the within-band normalized squared coefficients; adjacent-level energy
ratios; and \(Q\)-quantiles of local squared-coefficient energy. Images that cannot support all
four levels, a complete rectangular painted field, or nonzero total detail energy at a registered
scale are missing at that scale. A different wavelet, level count, padding rule, or normalization
is a separate candidate counted in multiplicity.

**Required controls.** Wavelet family, padding, level, scale, codec, blur/sharpening, crop, mask,
and independent reproduction.

**Claim ceiling.** Reproduction-visible texture energy, not literal brushstroke geometry,
impasto, or material texture.

### 7.7 PF-O1 — tie-aware ordinal-pattern profile

**Question.** Are very local order relations reproducible and painter-associated rather than
quantization or codec artifacts?

**Input.** Linear-light Rec. 709 luminance
\(Y=0.2126R+0.7152G+0.0722B\) at every supported scale. Any source-faithful grayscale conversion
is a separate diagnostic feature version.

**Algorithm.**

1. For every valid 2×2 block, convert the four values to their weak-order rank pattern, retaining
   equalities. The 75 possible weak orders are the primary state space.
2. Report the normalized 75-state distribution. A reduced grouping is secondary and may be
   reported only when its complete state-to-group mapping is published in the feature-definition
   artifact before qualification; no unnamed grouping is part of PF-O1.
3. For state probabilities \(p_i\), report normalized permutation entropy
   \(H=-\sum_i p_i\log p_i/\log 75\). Let \(u\) be the uniform 75-state distribution and
   \(J(p,u)\) their Jensen–Shannon divergence. Report statistical complexity
   \(C=H\,J(p,u)/J_{\max}\), where \(J_{\max}\) is the divergence between \(u\) and a point mass
   under the same log base.
4. Run an exact-equality branch and one frozen tolerance branch. The tolerance is selected on
   development reproductions, not on painter separation.
5. Report the number of valid blocks and exact-tie rate.

**Comparison.** Use Jensen–Shannon distance for state distributions and retain entropy,
complexity, and tie rate as separate coordinates.

**Required controls.** Grayscale definition, bit depth, quantization, codec, tolerance, scale,
resampler, mask, and independent reproduction.

**Claim ceiling.** Local rank-pattern diversity and disequilibrium at declared scales, not
creativity, aesthetic complexity, or historical progress.

### 7.8 PF-M1 — coarse composition maps

**Question.** Does coarse spatial organization add painter specificity after subject matching?

**Input.** Aspect-preserved painted field.

**Algorithm.** On fixed 1×1, 2×2, and 4×4 grids, compute valid-area-normalized luminance mass,
chroma mass, edge density, orientation profile, spectral salience, and normalized center-of-mass
and balance summaries. A learned saliency map is never substituted into PF-M1; it receives its own
model-specific diagnostic ID.

**Required controls.** Crop/frame uncertainty, aspect ratio, mask geometry, content, source, and
independent reproduction.

**Status and ceiling.** Secondary. It enters a painter profile only if it adds held-out painter
and human-judgment information beyond content and source. It does not encode a universal rule of
good composition.

### 7.9 PF-L1 — learned appearance diagnostics

**Question.** Does a named frozen representation add transferable painter-associated information,
and what shortcuts does it encode?

**Input.** The encoder's exact native preprocessing plus an aspect-preserving control when
technically possible.

**Artifact contract.** Record architecture, source revision, weight URI and hash, license,
dependency lock, device/runtime, preprocessing graph, tensor mapping, stochastic rule, and at
least one reference fixture. If any essential artifact is missing, the result is an adaptation or
diagnostic, not an exact replication.

**Analysis.** Fit all standardization, dimension reduction, metric learning, prototypes, and
thresholds inside training folds. Raw cosine similarity has no universal painter threshold.
Embeddings are not interpreted dimension by dimension.

**Required probes.** Same-work cross-reproduction retrieval; content-matched painter retrieval;
painter-matched content retrieval; source, medium, content, date, signature/text, and derivative
prediction; perturbations; nearest-neighbor/near-copy audit; and blinded human alignment.

**Initial status and ceiling.** Diagnostic only. A named representation may become
domain-limited or core only by passing the same full gate sequence as the interpretable panel.

### 7.10 PF-X1 — contextual and semantic diagnostics

**Question.** How much of an apparent painter relation is explained by depicted content,
iconography, affective concepts, or text-conditioned model associations?

**Input.** One frozen vision-language image encoder and, when used, a frozen text-prompt set.

**Algorithm.** Report image–image and image–text similarities for preregistered content, genre,
iconographic, and affective concepts. Prompt text, negative controls, pooling, and aggregation are
part of the feature identity.

**Status and ceiling.** Diagnostic only. PF-X1 is used as a nuisance baseline and discriminant
construct. It is not merged with appearance families and called painterly style.

### 7.11 Methods excluded from ordinary RGB measurement

Ordinary catalog RGB cannot identify:

- pigment, binder, elemental composition, or material palette;
- underdrawing, pentimenti, layers, or restoration history;
- microscopic brushstroke topology or impasto;
- authorship, authenticity, or forgery status;
- artistic quality, beauty, originality, intention, or influence; or
- conservation condition beyond visible-file annotations.

Those questions require a separately designed technical-imaging or expert-examination protocol.

## 8. Qualification gates

Every coordinate receives a result at every applicable gate. A failed candidate remains in the
ledger; it is not silently removed.

### Gate 0 — executable identity

Require the complete feature card, source/artifact identities, software lock, fixtures, expected
values, tolerances, and explicit behavior for every unsupported input. Paper/code disagreement
and every local adaptation are documented.

**Pass:** an independent implementation can reproduce the fixture and map every output coordinate
to its definition.

### Gate 1 — computational repeatability

Run fixtures and stratified development files across repeated process starts. Deterministic
methods require exact identity under the frozen runtime. Unavoidable numerical nondeterminism
requires prespecified absolute and relative tolerances. Stochastic methods define whether the
estimand is a posterior mean, repeated-draw distribution, or fixed-draw fixture; a seed alone does
not define scientific meaning.

**Pass:** all repetitions fall within tolerance with no silent download, fallback, or branch
change.

Passing only Gates 0–1 supports the `digital_file` disposition and nothing higher.

### Gate 2 — controlled perturbation response

Apply one-factor perturbations and a small frozen factorial subset:

- supported resolutions and at least two antialiased resamplers;
- mild JPEG/WebP delivery compression;
- bit-depth and quantization changes;
- profile conversion, profile removal, and assumed-sRGB sensitivity;
- mild gamma/tone, white balance, blur, sharpening, and sensor noise;
- frame, border, watermark, padding, and crop uncertainty;
- native aspect ratio versus a method-required diagnostic resize; and
- construct-changing controls such as hue rotation, phase scrambling, or pixel shuffling.

For scalar coordinates, estimate within-work perturbation deviation, repeatability coefficient,
response curves, and painter-order reversals. For vectors, estimate distance changes, margin
changes, nearest-neighbor stability, and geometry stability. A coordinate must respond to
construct-changing controls in the expected direction.

**Pass:** the simultaneous upper confidence bound on relevant measurement error is below the
family-specific SESOI, expected sensitivities are present, and no unmodeled perturbation reverses
the intended interpretation. Without a defensible SESOI, the result stays descriptive.

### Gate 3 — independent-reproduction reliability

Compare:

- same work across independent captures;
- same capture across delivery derivatives;
- different works by the same painter in a matched nuisance cell;
- different painters in the same matched nuisance cell; and
- different painter/workflow pairs as a shortcut diagnostic.

Same-work retrieval is diagnostic because it may reward content or work-specific defects. The
binding outcomes are paired-capture equivalence of registered painter margins and stability of
painter-profile location and spread.

**Pass:** Gate 2 error criteria hold across independent captures, and simultaneous intervals for
paired-capture margin/profile changes lie within the frozen equivalence tolerances.

**Failure ceiling:** success only within one capture family is `digital_derivative`; unstable
cross-capture results are `diagnostic_only` or `failed` for painter use.

### Gate 4 — held-work painter specificity and transfer

Run all tasks with physical-work holdout:

1. within-domain held-work evaluation;
2. leave-source-workflow-out evaluation with source-level nested selection;
3. leave-content-family-out evaluation;
4. joint leave-source-by-content-out evaluation;
5. complete hard-neighbor panel discrimination on one panel-wide support;
6. broad-negative calibration; and
7. career-phase transfer when the frozen frame supports it.

Report painter-balanced accuracy, painter recalls, log loss or Brier score, calibration, ranks,
work-level margins, nuisance baselines, and uncertainty. Classification is diagnostic; the
binding result is the family-specific margin.

For endpoint \(e\), every target–neighbor margin \(M_{a,h,F,e}\) has a separately frozen positive
SESOI \(\delta_{a,h,F,e}\). Define

\[
T_{a,F,e}^{panel}=
\min_{h\in H_a}
\{M_{a,h,F,e}-\delta_{a,h,F,e}\}.
\]

**Pass:** at every required transfer endpoint, the simultaneously calibrated lower confidence
bound for every adjusted neighbor margin—and therefore for \(T^{panel}\)—exceeds zero; the family
adds out-of-sample information beyond source/content/medium/phase baselines; and the registered
experiment-wide testing path passes. Sign retention or pooled accuracy alone is diagnostic.

### Gate 5 — human convergent and discriminant validity

Use blinded pair or triplet judgments. The primary task asks which candidate is closer to an
anchor in visible painterly manner while asking the rater to ignore depicted subject as far as
possible. Separate tasks measure content, color organization, texture/mark organization, and
overall appearance.

Stimuli cross same-painter/different-content, different-painter/matched-content, independent
reproductions, hard neighbors, broad negatives, whole works, details, and controlled variants.
Attribution, filenames, provider UI, condition, and feature outcomes are hidden. Recognition and
familiarity are asked after the primary response. Unrecognized works are primary; recognized and
unmasked works are sensitivities. Experts and nonexperts are separate prespecified strata.

Fit a work- and rater-crossed Bradley–Terry, Thurstone, or ordinal model. Report reliability,
stratum differences, intervals, and held-out judgment prediction.

**Pass for a perceptual claim:** the family predicts painterly-manner judgments on held-out,
unfamiliar works beyond content, source, and low-level baselines, while not merely reproducing the
separate content-similarity task.

Without this gate, the maximum language is `painter-associated image profile`, not
`human-perceived painterly similarity`.

### Gate 6 — unopened-workflow external confirmation

Freeze the feature set, parameters, estimator, support, weights, nuisance model, missingness
rules, thresholds, and multiplicity tree before opening the external set. A core confirmation set
uses an institution/capture workflow not present in development or qualification and contains no
physical-work, capture, derivative, or near-duplicate overlap.

**Pass:** the unchanged decision tree passes once on the external set and every registered method,
including failures, is reported.

Changing only geography, medium, period, or content while keeping a seen capture workflow supports
only the corresponding domain-limited claim. A failure is not tuned on the external set and
renamed success.

## 9. Statistical and decision rules

### 9.1 Units and dependence

Physical work is the real-corpus inferential unit. Reproductions are nested observations.
Human analyses cross work and rater. Resampling proceeds at the highest applicable level:

1. painters, only when generalizing beyond named painters;
2. physical works within painter and frozen design cells;
3. independent reproductions within work; and
4. raters and works jointly for human tasks.

Pixel-, patch-, derivative-, or rating-only intervals are invalid for a painter claim.

### 9.2 Primary real-image estimands

Every qualified family reports:

- **R1 reproduction error:** within-work changes across independent reproductions, by workflow
  pair and processing branch;
- **R2 painter-associated variation:** painter-associated location/scale or distributional
  variation after registered nuisance adjustment;
- **R3 held-work specificity:** every \(M_{a,h,F,e}\) and adjusted panel statistic under each
  transfer endpoint;
- **R4 within-painter heterogeneity and coverage:** coordinate quantiles, spread, multimodality,
  phase/content strata, and reference support; and
- **R5 human alignment:** out-of-sample association with the frozen human tasks when claimed.

A centroid is a transparent baseline only. It cannot replace R4.

### 9.3 Estimator and distance selection

The execution freeze selects estimators by prospective simulation and development-only
calibration. Requirements are:

- scalar/low-dimensional models are cross-classified over painter and registered nuisances;
- vector or histogram models use a frozen distance, kernel, or predictive score appropriate to
  the feature geometry;
- all transforms, PCA, covariance shrinkage, bandwidths, and metric learning occur inside
  training folds;
- finite-reference uncertainty is propagated;
- family components remain visible even when an omnibus statistic is used;
- ordinary FID is not used for small painter cells;
- UMAP and t-SNE are descriptive only; and
- raw cosine similarity receives no universal threshold.

If simulation cannot support a multivariate distributional estimator, report coordinate-wise
quantiles and decline the multivariate claim.

### 9.4 Permutation and uncertainty

Painter-label permutation is permitted only within frozen exchangeability blocks containing at
least two painters and the simulation-selected independent-work minimum. Otherwise the
permutation estimand is undefined. Hierarchy-preserving bootstrap or multilevel intervals keep
all derivatives of a work together and all uses of a reference work jointly resampled.

Small top-level samples are reported as low precision; they are not converted into large \(n\) by
counting pixels, patches, or pairs.

### 9.5 Multiplicity

Before outcomes, freeze one experiment-wide primary hierarchy. Its root is the claim that at least
one registered family supports a painter feature. Descendants include every family, coordinate,
scale, processing branch, resampler, encoder, combination rule, painter/population claim,
hard-neighbor panel, transfer endpoint, and human endpoint capable of making that family a
success.

Use closed testing or a jointly calibrated max-statistic/simultaneous-interval procedure that
strongly controls experiment-wide family-wise error. A coordinate qualifies only if the root and
every node on its path pass together with all conjunctive gates. Family-local correction cannot
support a project-level winner claim. False-discovery-rate procedures are exploratory only and
cannot qualify a method.

### 9.6 Missingness and selection

Freeze the intended denominator, eligibility rule, work minimum, and completion proportion for
every painter × common-support × workflow cell. Record rights/access failure, provider failure,
corruption, preprocessing exclusion, algorithm failure, and metadata absence separately.

Before scientific estimates:

- report denominators and missingness by every registered factor and joint cell;
- model observability from frame metadata;
- report differential selection by painter and nuisance factors; and
- run the frozen complete-case, weighting, pattern-mixture, bound, and tipping-point analyses.

A core disposition requires every inferential cell to retain its minimum and the conclusion to
survive all scientifically plausible registered missing-not-at-random scenarios. Otherwise narrow
the domain before favorable outcomes are inspected, fail the method, or mark it not executed.

## 10. Dispositions and failure actions

| Disposition | Required meaning |
|---|---|
| `qualified_core` | Passes Gates 0–6 for the stated target population and unopened workflow |
| `qualified_domain_limited` | Passes only in a precisely named source, content, medium, phase, or other domain |
| `reproduction_associated` | Stable across tested independent reproductions but not painter-specific under transfer |
| `digital_derivative` | Stable only among derivatives of one capture |
| `digital_file` | Repeatable only for the declared bytes and processing branch; no derivative or reproduction claim |
| `diagnostic_only` | Useful for nuisance, semantic, sensitivity, or evaluator-family analysis but not painter qualification |
| `replication_only` | Retained only under a named published method's input/artifact assumptions |
| `failed` | Fails a required gate or contains an irrecoverable measurement/artifact defect |
| `not_executed` | Required rights, artifacts, support, precision, or observations are unavailable |

Failure actions are fixed:

- do not tune on qualification or external failures;
- do not drop a hard neighbor to recover significance or overlap;
- do not replace missing works or reproductions after the frame freezes;
- do not promote a diagnostic because a classifier performs well;
- do not merge failed coordinates into a composite that masks failure;
- do not change weights to favor observed cells; and
- do not erase a failed method from the ledger.

Any redesign begins a new version and treats the failed result as prior evidence.

## 11. Required outputs

### 11.1 Feature-definition artifact

For every attempted coordinate, publish a compact definition containing:

- feature ID/version and disposition;
- construct and non-construct statement;
- formula, constants, units, scale, input branch, and mask rule;
- coordinate schema and ordering;
- dependency/model artifacts and hashes;
- fixture inputs, expected values, and tolerances;
- unsupported-input and missingness behavior;
- distance/scoring rule; and
- expected perturbation directions.

### 11.2 Observation-level feature table

One row per physical-work × reproduction × processing branch × scale × feature version, with:

- all unit/provenance identifiers;
- source and derivative hashes;
- feature vector or content-addressed feature path;
- validity/missingness code;
- runtime fingerprint;
- preprocessing receipt hash; and
- extraction timestamp.

Rows are never overwritten. Corrections supersede earlier rows and retain lineage.

### 11.3 Qualification report

For every gate and family, report:

- eligible and observed denominators;
- point estimates and simultaneous intervals;
- SESOI/equivalence thresholds and how they were frozen;
- work-level and painter-level results;
- nuisance and leakage diagnostics;
- missingness sensitivities;
- multiplicity path;
- external result when applicable;
- disposition and claim ceiling; and
- every failed or not-executed outcome.

### 11.4 Painter profile

For each qualified painter and family, publish:

- the exact target population and common support;
- frozen nuisance/workflow weights;
- coordinate distributions, quantiles, and uncertainty;
- reproduction-error contribution;
- within-painter heterogeneity and coverage;
- every hard-neighbor margin;
- unsupported cells/domains; and
- versioned claim language.

The profile is a set of distributions and uncertainty statements, not a universal scalar score.

### 11.5 Storage boundary

Large raw images, derivatives, vectors, model weights, and caches live under one ignored research
workspace. Version control contains compact redistributable manifests, hashes, schemas,
definition cards, decisions, and reports. Recorded paths are relative to the repository or
declared workspace root.

## 12. Execution-freeze checklist

No empirical operation begins until one reviewed, immutable execution-freeze artifact supplies
all of the following:

1. research question, target population, painters, attribution policy, and claim domain;
2. hard-neighbor and broad-negative panels with historical rationale;
3. eligible-work frame, rights, providers, and terminal acquisition rules;
4. complete joint-support incidence table and frozen weights;
5. reproduction-panel incidence matrix and design-rank audit;
6. development, qualification, human, and sealed external partitions;
7. exact preprocessing parameters, profiles, masks, scales, and resamplers;
8. exact feature-card parameters and the complete attempted-family list;
9. source/model revisions, hashes, licenses, runtime locks, and fixtures;
10. estimators, distances, standardization, and nested-selection algorithm;
11. prospective simulations and minimum work/reproduction/rater counts;
12. coordinate-, neighbor-, and endpoint-specific SESOIs/equivalence bounds;
13. experiment-wide closed-testing or simultaneous-interval hierarchy;
14. denominator, completion, missingness, MNAR, and tipping-point rules;
15. human-task wording, blinding, signature/text, familiarity, display, and exclusion rules;
16. external-opening authorization and one-use decision procedure;
17. output schemas, workspace paths, retention, and redistributability;
18. terminal actions for provider, artifact, fixture, support, precision, and gate failure; and
19. independent review record approving the exact frozen object.

The freeze must explicitly mark each item present and provide its value or artifact hash.
Narrative promises that a value will be chosen later do not satisfy the checklist.

## 13. Permitted and prohibited conclusions

### 13.1 Permitted after the corresponding gates

- “This coordinate describes the declared digital reproduction's color, spatial, ordinal, or
  learned-appearance profile.”
- “The coordinate was repeatable across the tested independent reproductions within the reported
  uncertainty.”
- “The painter-associated margin exceeded every registered hard-neighbor SESOI on the tested
  common support and transfer endpoints.”
- “The measurement predicted blinded painterly-manner judgments for the tested works, raters, and
  display conditions beyond content and source baselines.”
- “The unchanged measurement confirmed on the unopened institution/capture workflow.”

Every conclusion names the feature version, painter/work population, source/reproduction domain,
common support, uncertainty, and failed or unsupported domains.

### 13.2 Prohibited

The study must not claim:

- the painter's true style, style essence, or a universal style score;
- physical pigment, binder, layering, topography, or microscopic brushwork from RGB;
- authorship, authenticity, forgery, or legal infringement;
- artistic quality, beauty, creativity, originality, intention, or historical influence;
- causal development from cross-sectional associations;
- model training exposure or memorization without a separate audit; or
- generalization to untested painters, media, cultures, institutions, workflows, or periods.

## 14. Change control

Protocol version 2.0 is a prospective foundation, not evidence that any coordinate has passed.
The execution freeze may narrow scope but cannot loosen measurement identity, common support,
reproduction crossing, source-level nested selection, hard-neighbor, multiplicity, missingness,
human, or external-confirmation requirements.

After any qualification or external outcome is visible:

- a formula, parameter, feature family, estimator, support set, weight, SESOI, threshold,
  partition, exclusion, or decision-rule change creates a new protocol version;
- the earlier result remains in the ledger;
- the external set cannot return to development status; and
- the new version receives new fixtures, simulations, and independent review.

The complete research sequence is therefore:

\[
\text{protocol}
\rightarrow \text{execution freeze}
\rightarrow \text{fixtures}
\rightarrow \text{development}
\rightarrow \text{qualification}
\rightarrow \text{human validation}
\rightarrow \text{external confirmation}
\rightarrow \text{versioned painter profiles}.
\]

Stopping at any failed or unavailable step is a valid research result.
