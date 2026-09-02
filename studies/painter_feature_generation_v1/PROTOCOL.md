# Painter Feature Generation v1 — Protocol 2.0

Status: prospective redesign; no generated-versus-real result is authorized yet

Protocol ID: `painter-feature-generation-v1/2.0`

Operational date: 2026-09-02

Canonical document: this file

## 1. Research question

This study asks one question:

> When a frozen generative model is prompted with a painter's name, do its outputs reproduce the
> measurable distribution of visual features found in paintings exactly attributed to that painter
> by the frozen authority records, under the same broad subject-matter frame?

The unit of the real corpus is a **physical painting**. The unit of the generated experiment is a
**registered generation attempt**. A digital file is a measurement of a painting, not an additional
painting. The target is a distribution across works, not a classifier score, prototype, centroid,
single similarity value, or timeless essence of an artist.

The study panel is:

- Claude Monet (`Q296`);
- Alfred Sisley (`Q175130`);
- Camille Pissarro (`Q134741`); and
- Paul Cézanne (`Q35548`).

The comparison domain is authority-record-exactly-attributed oil-on-canvas paintings whose visible
subject is an outdoor place. This restriction is deliberate. All four painters have substantial
landscape output, and a common content frame reduces the easiest semantic shortcut without
pretending that content and painterly form can be completely separated.

## 2. What the study may and may not conclude

### 2.1 Primary claim

For one exact model, render contract, prompt frame, and seed/request population, the study may
conclude that the model reproduced a painter's feature distribution **within the frozen accessible
digital-surrogate frame** only if all prequalified primary feature families satisfy:

1. absolute target-fit equivalence;
2. painter specificity against every other painter in the panel;
3. improvement over the matched painter-name-free control;
4. distributional coverage without material contraction or mode omission; and
5. the availability, content-adherence, and copy-exclusion gates.

Failure of this conjunction means “reproduction was not demonstrated.” It does not prove that no
possible prompt, model, corpus, or feature space could resemble the painter.

The exact construct name is **broad-scene-weighted digital-surrogate feature reproduction**. Scene
group is standardized, but period, phase, detailed iconography, season, illumination, depth, and
source mixture remain part of the finite target. A pass is not described as content-free painterly
form; residual content mediation is reported with the nuisance and per-scene analyses.

### 2.2 Claim ceiling

The accessible web/museum corpus is not a probability sample of a painter's complete oeuvre. The
primary estimand is therefore the closed, documented finite population that this protocol can
lawfully identify and measure. A larger convenience corpus does not turn that frame into an oeuvre
sample. Oeuvre-wide inference would require a separate frame with known inclusion probabilities.

The study does not infer:

- artistic intention, quality, creativity, authorship, authenticity beyond the authority records,
  or expert connoisseurship;
- physical brushwork, impasto, pigment, underdrawing, or surface topography from RGB reproductions;
- superiority of one painter or model;
- a universal scalar “style score”; or
- generalization to another model version, service, prompt set, date, or rendering configuration.

## 3. Why this is a distribution-comparison study

Painter classification answers whether a decision boundary can separate labels. It can succeed
because of depicted objects, source watermarks, image borders, digitization pipelines, chronology,
or training-data leakage. A centroid can look close while a generator covers only one narrow mode.
This study instead compares complete empirical distributions and keeps five questions separate:

| Question | Endpoint |
|---|---|
| Is the generated distribution absolutely close to the painter's real target? | equivalence of a family-level distribution distance |
| Is it closer to the named painter than to every comparison painter? | all-neighbour specificity contrasts |
| Did the painter name cause the improvement? | named minus matched artist-free control contrast |
| Did generation preserve spread and modes? | coordinate spread and group-wise coverage |
| Is apparent fit caused by failures or copying? | availability, adherence, and near-copy rates |

No one row can substitute for the others.

## 4. Evidence from the literature and its role here

The protocol uses methods from adjacent research but does not treat any paper as direct validation
of this exact question.

### 4.1 Interpretable visual measurements

- Kim, Son, and Jeong's large-scale painting analysis and Lee et al.'s chromatic-distance work
  motivate multiscale color organization rather than a palette mean alone
  ([Kim et al. 2014](https://doi.org/10.1038/srep07370),
  [Lee et al. 2018](https://doi.org/10.1371/journal.pone.0204430)).
- Fourier spectra, orientation distributions, and self-similarity have an established image-
  statistical literature in art, but they remain properties of reproductions
  ([Graham & Field 2007](https://doi.org/10.1163/156856807782753877),
  [Koch et al. 2010](https://doi.org/10.1371/journal.pone.0012268),
  [Redies et al. 2017](https://doi.org/10.1016/j.visres.2017.02.004)).
- Wavelet and textural methods can distinguish some painter corpora, but RGB files cannot justify a
  physical-brushstroke claim
  ([Lyu et al. 2004](https://doi.org/10.1073/pnas.0406398101),
  [Qi et al. 2013](https://doi.org/10.1016/j.sigpro.2012.09.025)).

These papers motivate the three primary families in Section 10. They do not supply a universal
sample size or an automatic painter-fidelity threshold.

### 4.2 Kim's 2026 A/C representations

Kim et al. analyze 72,447 paintings by 2,354 painters from 1500–1990 with a 16,384-dimensional
Stable Diffusion 2 VAE latent (A) and a 1,024-dimensional LAION-CLIP feature (C)
([paper](https://doi.org/10.1073/pnas.2517969123),
[full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/),
[audited code commit](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0)).
Their results establish chronology and label-associated signal in those coordinates. They do not
validate generated-versus-real painter-distribution equivalence. A mixes color, content, layout,
resizing, codec, VAE training, and a stochastic posterior draw; C mixes semantic content, web
associations, chronology, and possible training exposure. Both are secondary diagnostics here.

### 4.3 Learned style and generative metrics

CSD, ALADIN, GOYA, and ArtFID show that learned spaces can emphasize artistic appearance or separate
some content/style signals
([CSD](https://doi.org/10.1007/978-3-031-72848-8_9),
[ALADIN](https://openaccess.thecvf.com/content/ICCV2021/html/Ruta_ALADIN_All_Layer_Adaptive_Instance_Normalization_for_Fine-Grained_Style_Similarity_ICCV_2021_paper.html),
[GOYA](https://doi.org/10.3390/jimaging10070156),
[ArtFID](https://arxiv.org/abs/2207.12280)). Their supervision, web data, and evaluator assumptions
also create shortcuts. They are used only after source/content/copy audits and remain diagnostic.

FID is biased at finite sample sizes and assumes a Gaussian summary. Nearest-neighbour precision,
recall, density, and coverage are sensitive to sample size, dimension, neighbourhood choice, and
outliers. They may illuminate a result but do not decide it. The primary distance is energy distance
in low-dimensional, prequalified, robustly scaled feature families
([Székely & Rizzo 2013](https://doi.org/10.1016/j.jspi.2013.03.018)).

### 4.4 Measurement validity lesson

The same painting can appear as different crops, color transforms, files, and resolutions. Physical
work identity and capture ancestry must therefore be separated from file identity. Same-work
independent captures are used to measure reproduction disturbance; mirrors and re-encodings are not
counted as independent works or captures.

## 5. Real-corpus source frame

### 5.1 Three source layers

The source frame has three non-interchangeable layers:

| Layer | Examples | Permitted use |
|---|---|---|
| authority | official museum collection systems, POP/Joconde | identity, attribution, object type, medium/support, accession, provenance |
| discovery | Wikidata, Commons, Europeana | find and crosswalk candidates; never establish authenticity alone |
| media/capture | official IIIF/media service or lawfully reusable Commons file | deliver a measurable image with rights and technical receipts |

A provider may occupy more than one layer, but each required assertion must still have an explicit
field and source. An aggregator row is not a new physical work, and a delivery host is not a new
holding institution.

### 5.2 Closed Protocol 2.0 source registry

The Protocol 2.0 candidate union is exactly the terminal union of these routes:

1. a Wikidata/Commons exact-creator + painting + image census without a material-field requirement;
2. an exact-creator Europeana census;
3. the Art Institute of Chicago, National Gallery of Art, Cleveland Museum of Art, Yale University
   Art Gallery, Getty Museum, Minneapolis Institute of Art, and Paris Musées collection APIs/exports;
4. POP/Joconde; and
5. the 3,190-item fixed historical seed, used only to quantify current metadata attrition and to
   reconcile items that remain in the broader census.

This named list is the complete source registry, not a minimum. An official holding page linked from
a returned candidate may verify authority or media rights, but it cannot introduce a new physical
work that was absent from every terminal route. Adding a route or a work discovered elsewhere
requires a new protocol version before its pixels or features are viewed.

For every source, the pre-request registry must freeze:

- exact endpoint, query or export body, creator identifier, API/data version, and requested fields;
- UTC cutoff, sort order, pagination rule, and terminal condition;
- canonicalization and duplicate handling;
- item-level rights fields and media endpoint;
- retry, rate-limit, redirect, and failure semantics; and
- the raw-response storage and hashing rule.

Collection does not stop when a desired count is reached. Every declared source must reach its
terminal condition. A nonterminal source makes the census incomplete; it does not license a silent
replacement.

### 5.3 Current scale evidence and the retired quota

The former target of 360 works per painter is retired. It came from a role-allocation plan, not from
the literature, precision, effect size, or power. The committed exploratory seed contains 3,190
Wikidata item identifiers and 3,364 Commons filenames, but the prior small Commons follow-up ended in
HTTP 429 and establishes no rights, resolution, or quality yield. The prospective fixed-seed audit
must therefore measure that attrition before any capacity statement is allowed. Source-layer counts
will not be added because direct museum, aggregator, Wikidata, and Commons records can describe the
same physical work. The new rule is an exhaustive, deduplicated physical-work union with actual
unequal painter counts, followed by the adequacy gates in Section 9.

### 5.4 Broader discovery rule

The initial Wikidata query required `P186` oil and canvas statements. Wikidata material fields are
incomplete, so that query is a fixed-seed attrition audit, not the complete source frame. The
prospective discovery census removes the `P186` requirement, retrieves exact creator + painting +
image candidates, and then verifies oil-on-canvas against an authority record. Missing Wikidata
material is neither inclusion nor exclusion evidence.

## 6. Candidate-to-work identity graph

Each record follows this graph:

```text
source row
  -> authoritative object/accession
  -> canonical physical_work_id
  -> capture/master family
  -> provider asset
  -> delivered file
```

The identity reconciliation order is frozen before visual coding:

1. identical authority object/accession ID or explicit catalogue cross-reference;
2. documented cross-institution provenance for the same object;
3. compatible creator, title variants, date, dimensions, support, and provenance, sent to review;
4. exact/perceptual image similarity as a review flag only, never sole proof of work identity.

One physical work contributes at most once to the primary corpus. Multiple mirrors, resolutions,
crops, filenames, URLs, encodings, or hashes do not increase the work count.

If a work has multiple assets, the primary asset is chosen without viewing painter features, in
this order:

1. item-level lawful reuse basis;
2. documented capture/master ancestry;
3. complete-painting view without frame, watermark, or material crop;
4. valid embedded ICC profile or documented color space;
5. larger native short side; and
6. stable provider asset ID, with lexical ID as the final tie-break.

A work with at least two demonstrably independent captures is reserved for the reproduction-
disturbance auxiliary set and excluded from the primary confirmation frame. Re-encodings or crops
from one master are not independent captures.

An `authority/capture_workflow_id` is the tuple of the authority institution and the documented
digitization master/capture programme. A Commons mirror inherits the originating workflow when it is
known; an unknown origin is `unresolved` and cannot satisfy a source-crossing gate. Different CDN,
API, hostname, file size, encoding, or delivery time never creates a workflow. Independence requires
separate capture provenance or an institution statement identifying a distinct digitization event.

## 7. Inclusion, exclusion, rights, and image quality

### 7.1 Metadata inclusion

A candidate can advance only when an authority record supports all of the following:

- exact painter attribution, not “after,” “school of,” “circle of,” “attributed to,” or workshop;
- object type painting;
- oil as the paint medium and canvas as the support; mixed techniques advance only if oil and canvas
  are explicit and no incompatible primary support is stated;
- a stable object/accession identifier; and
- no authority-record conflict left unresolved.

Titles, dates, and dimensions are retained with uncertainty rather than silently normalized into
false precision.

### 7.2 Media rights

The analysis file must have an item/asset-level public-domain, CC0, CC BY, or CC BY-SA basis that
permits the intended local research processing. “Downloadable,” a thumbnail URL, or a collection-
wide statement does not substitute for an item-level rights receipt. Rights conflicts, permission
requirements, noncommercial/no-derivatives restrictions, or missing rights are terminal exclusions
for acquisition in this protocol.

The repository commits metadata, hashes, and compact reports, not restricted full-resolution image
bytes. Image bytes live under the ignored active-study workspace.

### 7.3 Technical image gate

The delivered file must:

- decode completely as JPEG, PNG, TIFF, or WebP;
- show the complete painting rather than a detail, gallery view, page scan, frame-dominant view, or
  watermarked surrogate;
- have a native short side of at least 1,024 pixels; 2,048 pixels is preferred and recorded;
- preserve aspect ratio and have both dimensions, MIME type, byte size, and cryptographic hashes;
- retain the source URL, provider asset ID, retrieval timestamp, HTTP receipt, rights record, and
  color-profile status; and
- pass exact-file and perceptual-duplicate checks.

Resolution is a qualification gate, not evidence of faithful color. Capture/source disturbance is
measured separately.

### 7.4 Blind visual eligibility

Two independent coders view only a frozen derivative whose long side is at most 512 pixels. Painter,
title, institution, accession, filename, and source are masked. They assign:

1. `eligible_outdoor_place`;
2. `ineligible_non_outdoor_or_nonplace`;
3. `ambiguous`; and
4. one broad scene group if eligible:
   - `water_organized`;
   - `built_place_organized`;
   - `route_organized`; or
   - `open_or_wooded_land`.

The codebook uses visible dominance, not the title. Water must organize the composition; incidental
water does not. A built place must be spatially organizing; a distant house in a field does not.
Route means a road/path/track outside a dominant settlement. The final group covers fields,
hillsides, forests, orchards, gardens, and other land-organized scenes.

Coders also record three nuisance descriptors—season, illumination/weather, and depth structure—
using prespecified categories plus `indeterminate`. These are diagnostics and sensitivity variables,
not reasons to curate a favourable corpus.

Before active coding, both coders must pass a separate calibration set whose works are permanently
excluded. Every active candidate is double-coded; missing labels remain explicit failures. Before
adjudication, each painter separately must satisfy:

- eligibility raw agreement at least 0.90 and nominal Krippendorff alpha at least 0.80 across the
  three labels `eligible`, `ineligible`, and `ambiguous`;
- each coder's `ambiguous` share at most 0.10;
- on the union of rows called eligible by either coder, scene-group raw agreement at least 0.85 and
  nominal alpha at least 0.80, with `not_called_eligible`, missing, and all four scenes retained as
  distinct categories; and
- for season, illumination/weather, and depth, raw agreement at least 0.80 and each coder's
  `indeterminate` share at most 0.20 on that same union denominator.

The receipt reports every denominator and confidence interval by painter. If any gate fails, this
protocol version stops before adjudication. Only after the two raw streams and receipt are sealed
does a third blinded coder independently label disputed fields without seeing either response.
Two-of-three agreement is the consensus; three different labels or any missing adjudicator label is
unresolved and excluded. Adjudication cannot retroactively repair a failed reliability gate.

When both coders give one identical constant label in a required scope, alpha is mathematically
undefined; that scope passes the alpha component only with raw agreement exactly 1.00 and is reported
as `constant_complete_agreement_alpha_not_estimable`. Every other undefined/nonfinite alpha fails.

## 8. Corpus closure and exposure control

Every candidate receives one terminal disposition. The per-painter attrition table must report:

```text
retrieved source rows
-> exact creator
-> authority record resolved
-> painting + oil on canvas
-> reusable media rights
-> geometry/decode/complete-view qualified
-> distinct physical works
-> blind outdoor-place union eligible
-> adjudicated eligible
-> independent-capture auxiliary reservation
-> historical-pixel-exposure exclusion
-> sealed confirmation finite population
```

Previously viewed or feature-exposed physical works are placed on a permanent development denylist.
They may be used to design and test measurement code but cannot enter qualification or confirmation.
Every newly eligible work is assigned once to development, qualification, or confirmation by the
deterministic rule below. No favourable prefix is sampled and no work is discarded to equalize
painter counts. The complete assigned confirmation set is the finite target.

The resulting counts `N_a` may differ. The source mixture is part of the finite-frame estimand.
Source imbalance is reported and tested; it is not cosmetically repaired by deleting works. If a
feature conclusion changes under supported leave-one-source analyses, it is labelled
`source_sensitive`. A painter supported by only one source/capture workflow cannot enter generation
or receive a painter-reproduction label: painter and source would be inseparable.

### 8.1 Development, qualification, confirmation, and auxiliary data

All historically pixel- or feature-exposed works are development-only after identity resolution.
They may help implement the pipeline but never enter qualification or confirmation. Synthetic
fixtures carry no painter claim. Same-work independent-capture auxiliary works are also assigned
before feature calculation and are excluded from all three primary real populations.

After R2 consensus and auxiliary reservation, but before any Protocol 2.0 feature is calculated,
newly eligible works are ordered within painter × broad scene group × authority/capture workflow by
`SHA256("pfg-v1/2.0-role" || physical_work_id)`. In each ordered cell, zero-based ranks modulo five
are assigned as follows:

- remainder `0`: `new_development`;
- remainder `1`: `new_qualification`; and
- remainders `2`, `3`, or `4`: `sealed_confirmation`.

Thus every cell uses an approximately 20%/20%/60% split without a random redraw or count-based
stopping rule. Historical development works supplement only the development role; they do not alter
the new-work assignment. If a workflow cell contains fewer than five works, its assignments still
follow the same modulo rule and the later role-specific support gates decide feasibility.

M0a fits preprocessing tolerances, common scaling, copy thresholds, and margins using development
only. M0b applies the already frozen pipeline once to qualification. Confirmation-resolution pixels,
arrays, and features remain inaccessible until C0. No failure can be repaired by moving a work,
changing a coordinate, or widening a margin.

The role manifest, auxiliary manifest, and exposure-denylist hash are frozen before M0. Missing
historical bytes are reported and not replaced with confirmation work. No work can change role
because a method, source test, margin, or simulation is inconvenient.

### 8.2 Access roles and meaning of “sealed”

The acquisition custodian can access raw files and identifying metadata but cannot calculate painter
features. Coder 1, coder 2, and the adjudicator can access only masked 512-pixel derivatives and
cannot access raw files, authority/source fields, or feature arrays. M0 analysts can access
development, qualification only at its one-time gate, and the auxiliary
captures; they cannot access active confirmation-resolution pixels or arrays. The generation
operator can access only the G0 prompt/model/request artifacts and generated outputs.

R2 visual eligibility is therefore acknowledged pixel exposure by the coders, not “unopened” data.
“Sealed confirmation” means that identifying metadata, analysis-resolution pixels, normalized
arrays, and primary feature vectors remain inaccessible to M0/G0/G1 analysts until C0. Role-specific
access events and hashes are compact tracked receipts. One person or account cannot occupy
incompatible roles in the same protocol version.

## 9. “Enough data” rule

There is no arbitrary equal-work quota. A painter can enter generation only when all of the following
are true for the actual closed confirmation frame:

1. at least three broad scene groups are supported by every painter in the panel;
2. the equal-scene mixture defined below has Kish effective sample size at least 100 per painter;
3. each retained scene group has at least 20 physical works per painter;
4. the largest design weight of one work is at most 0.02; this is checkable from group counts without
   opening confirmation features;
5. the painter × authority/capture-workflow incidence graph is connected, every painter is supported
   by at least two independent workflows, every workflow used for the binding cross-painter claim
   contains at least two painters, and no workflow carries more than 0.80 of a painter's equal-scene
   weight;
6. the complete auxiliary independent-capture set contains at least 60 physical works, at least 12
   per painter, at least three scene groups, at least two capture workflows per painter, and two
   provenance-independent captures per work; and
7. within every retained painter × scene group there are at least 10 new-development, 10
   qualification, and 20 confirmation works; development and qualification each contain at least
   two authority/capture workflows per painter; and
8. whole-decision simulation using the actual group sizes and seed-block design achieves:
   - at least 80% probability of passing the full conjunction under a registered favourable model;
   - at least 95% rejection probability for every registered adverse alternative;
   - at most 5% probability of an unsupported painter-family claim; and
   - a simultaneous target-fit interval no wider than half its equivalence margin.

The retained set is deterministic: after R2 consensus, retain every one of the four named scene
groups for which **each** painter has at least 20 confirmation works; retain no other group and make
no tie choice. If fewer than three groups remain, the study stops. If exactly three remain, every
claim is explicitly narrowed to that three-group domain; the fourth group is not silently
generalized back into the conclusion.

The ESS 100 and 20-per-group values are screening floors, not power guarantees. ESS 100 corresponds
roughly to a 95% half-width near 0.25 standard deviations for a well-behaved mean and prevents a
nominally large but highly unequal scene-weighted frame from masquerading as large. Energy-distance,
tail, and conjunction behaviour is still decided by simulation, which may require more data.

For each auxiliary work and family, compute the RMS distance between its two independently captured
feature vectors after common scaling. With at least 59 exchangeable works, the observed maximum is a
nonparametric one-sided 95%/95% tolerance bound for the disturbance distribution because
`1 - 0.95^59 > 0.95`; Protocol 2.0 requires 60 and uses every available auxiliary work. This bound is
`B_F` in Section 13.3 and contributes prospectively to the equivalence margin; it is not tested
against a margin that it helped define. Results are also reported by painter, scene, and workflow.
Failure of the count/crossing rule or the later discriminability rule stops M0 rather than deleting
an inconvenient capture pair.

For `G` retained common groups with `n_as` works for painter `a` and group `s`, every group receives
mass `1/G` and every work within a group receives mass `1/(G*n_as)`. Thus

\[
ESS_a = \frac{1}{\sum_{s=1}^{G}\sum_{i=1}^{n_{as}}(1/(G n_{as}))^2}
      = \frac{G^2}{\sum_{s=1}^{G}1/n_{as}}.
\]

This transparent equal-scene target replaces the former high-dimensional entropy-weighting plan.
It uses every eligible work, gives each supported subject group equal scientific importance, and
does not create sparse exact content cells. Season, illumination, and depth are reported by group
and used in a prespecified sensitivity analysis. If their generated and real distributions differ,
that discrepancy counts against reproduction rather than being weighted away.

If one painter fails a gate, the four-painter protocol is NO-GO. The panel may be reduced only in a
new prospective version before generation; painters cannot be swapped or removed after seeing
generated or confirmation features.

## 10. Image normalization and primary painter features

### 10.1 Normalization

The same byte-identical pipeline is applied to real and generated images. It is frozen on historical
development and same-work capture fixtures before confirmation-resolution images are accessible. It
must:

1. decode with pinned Pillow/libjpeg/libpng/libtiff versions and fail on truncation;
2. transform an embedded ICC profile to IEC 61966-2-1 sRGB with pinned LittleCMS perceptual intent;
   a missing profile is interpreted as sRGB but flagged, never silently treated as calibrated;
3. use the complete borderless provider view; the primary pipeline performs no per-image crop or
   mask, and an image with a visible frame/watermark or non-painting border wider than 1% of either
   dimension is excluded at the technical gate;
4. preserve aspect ratio and downsample, never upsample, to exactly 1,024 pixels on the short side
   with the pinned Lanczos implementation; the long side is `round_half_up(original_long *
   1024/original_short)`;
5. retain gamma-encoded sRGB and convert to linear light with the exact IEC sRGB transfer function;
6. calculate luminance as `Y=0.2126R+0.7152G+0.0722B` in linear light and CIELAB under D65 with the
   pinned LittleCMS transform; and
7. hash the raw file, normalized array, software lock, and feature vector.

No per-image histogram equalization, white balancing, saturation correction, square warping,
background removal, or learned enhancement is allowed. Those operations can manufacture or erase a
painter difference. A uniform one-percent inward crop is a robustness analysis only.

### 10.2 Primary family A — color organization

Calculated on every pixel of the normalized painting area:

- median and IQR of CIELAB `L*`;
- median and IQR of chroma `C* = sqrt(a*^2+b*^2)`;
- fraction of pixels with `C* >= 5`;
- chroma-weighted circular hue concentration and normalized Shannon entropy in 24 half-open,
  15-degree bins for pixels with `C* >= 5`; if fewer than 1% of pixels qualify, both values are
  exactly zero and the low-chroma flag is retained;
- one median CIEDE2000 distance at each of the lags `round_half_up(0.01S)`,
  `round_half_up(0.04S)`, and `round_half_up(0.16S)`, where `S=1024`; at each lag the pool is the
  union of every valid rightward and downward pixel pair, border pairs with no counterpart are
  omitted, and no random pair sampling is allowed; and
- ordinary-least-squares slope of `log(median_DeltaE00 + 1e-6)` on the natural logarithm of the three
  exact integer lags.

Family A therefore has exactly 11 coordinates.

This family measures palette spread and spatial color interaction. It is not reduced to mean color.

### 10.3 Primary family B — spatial and orientation organization

Calculated on linear-light luminance after subtracting the image mean:

- radial Fourier power-spectrum slope over 4–128 cycles per image after a separable Tukey window with
  `alpha=0.10`; power is pooled in 32 fixed log-spaced radial bins, empty bins fail the image, and a
  deterministic Theil–Sen fit on `log(frequency)` and `log(mean_power + 1e-12)` supplies the slope;
- RMS log-power residual around that fit;
- spectral anisotropy, defined as the magnitude of the second circular moment over 36 equal
  half-open axial angle bins on Fourier coefficients in the same 4–128-cycle radial band, weighted
  by power;
- normalized entropy of an 18-bin axial (`0` to `pi`) orientation histogram from a 3×3 Scharr
  gradient, weighted by magnitude and excluding the outermost pixel;
- horizontal-versus-vertical balance, defined as cosine second moment of that histogram;
- median and IQR of Scharr magnitude; and
- four-quadrant PHOG self-similarity, expressed as the mean Jensen–Shannon divergence between each
  quadrant's same 18-bin weighted histogram and the full-image histogram, using base-2 logs and
  `1e-12` additive smoothing followed by renormalization. Rows and columns are split at their floor
  midpoint; the lower/right quadrant receives the center row or column when a dimension is odd.

Family B therefore has exactly 8 coordinates.

This family measures scale, edge, and compositional organization. It does not claim semantic
understanding.

### 10.4 Primary family C — multiscale texture organization

Calculated on linear-light luminance:

- log energy `log(mean(H^2+V^2+D^2)+1e-12)` from a four-level stationary `db2` wavelet transform;
  luminance is reflect-padded on the bottom/right to the next multiple of 16 and the padding is
  excluded from coefficient aggregation;
- ordinary-least-squares slope of the four log energies against levels `1,2,3,4`, plus one curvature
  coordinate equal to the mean of the two second finite differences
  `(E3-2E2+E1)` and `(E4-2E3+E2)`;
- normalized entropy of scikit-image rotation-invariant uniform LBP at `(P,R)=(8,1),(16,2),(32,4)`,
  with reflect boundary handling and the exact `uniform` code alphabet; and
- median local coefficient of variation in square reflect-padded windows of side
  `round_half_up(0.01S)`, `round_half_up(0.04S)`, and `round_half_up(0.16S)`, forced to the next odd
  integer, with denominator `max(local_mean_Y,1e-6)`.

Family C therefore has exactly 12 coordinates.

The output is called digital texture organization, not brushstroke measurement. The exact package
versions, array dtypes, rounding helper, fixture arrays, and expected numeric outputs are bound at
M0; changing one of these definitions requires a new protocol version.

### 10.5 Family qualification

M0a fixes the pipeline on development. M0b opens the new qualification partition
once. Qualification requires every prespecified coordinate and all of the following:

- deterministic fixtures within `atol=1e-8, rtol=1e-6` in float64;
- no dependence on labels, signatures, frames, or metadata;
- the auxiliary tolerance-bound rule in Section 9;
- under one-pixel translation, uniform one-percent crop, and one extra downsample/upscale cycle,
  median absolute coordinate change no greater than 0.05 pooled development IQR and 95th percentile
  no greater than 0.20 IQR;
- in every supported leave-one-workflow qualification comparison, same-painter distance below the
  frozen family margin and below every wrong-painter distance; and
- the largest same-painter workflow-versus-complement shift no greater than one half of the nearest
  wrong-painter separation in new qualification; and
- successful registered favourable/adverse simulations.

All three declared families must qualify on the untouched new qualification partition before
G0. A family is never dropped to make the conjunction easier. If any family fails, Protocol 2.0
stops before generation; a new protocol may ask a narrower family-specific question prospectively.

One common coordinate transform is fitted from new development: each coordinate is centred by
the equal-painter pooled median and divided by the pooled IQR. A missing/nonfinite or zero-IQR
coordinate fails its entire family; coordinates are not dropped after inspection. Painter-specific
scaling is forbidden.

Kim A/C, CSD, ALADIN, CLIP, FID/KID, classifier accuracy, and nearest-neighbour precision/recall are
secondary diagnostics. They cannot rescue a failed primary family or define the sample size.

## 11. Prompt and generation design

### 11.1 Common-content prompt frame

The complete 16-template library below is part of Protocol 2.0 and must be rendered into an exact
UTF-8 JSON artifact, reviewed, and hash-frozen before any active R2 visual label is read. The later
selection rule only removes unsupported whole scene groups using sealed group counts; it cannot
rewrite or choose among strings. Retain all groups supported by every painter, with at least three
groups required.

For each artist-free string, the named string is formed by inserting the exact bytes
` by {PAINTER}` immediately after `An oil painting on canvas`. `{PAINTER}` is replaced by exactly one
of `Claude Monet`, `Alfred Sisley`, `Camille Pissarro`, or `Paul Cézanne`.

| ID | Scene group | Exact artist-free prompt |
|---|---|---|
| W1 | `water_organized` | `An oil painting on canvas of a riverbank landscape, with water organizing the composition.` |
| W2 | `water_organized` | `An oil painting on canvas of a coastal or harbor landscape, with water as the main spatial element.` |
| W3 | `water_organized` | `An oil painting on canvas of a canal or lakeside landscape viewed from outdoors.` |
| W4 | `water_organized` | `An oil painting on canvas of an outdoor waterside place, with both land and water visible.` |
| B1 | `built_place_organized` | `An oil painting on canvas of an outdoor town street, with buildings organizing the composition.` |
| B2 | `built_place_organized` | `An oil painting on canvas of a village or settlement viewed from outdoors.` |
| B3 | `built_place_organized` | `An oil painting on canvas of an outdoor square or built place, with architecture as the main spatial element.` |
| B4 | `built_place_organized` | `An oil painting on canvas of buildings in an outdoor landscape, with the built place visually dominant.` |
| R1 | `route_organized` | `An oil painting on canvas of a country road passing through an outdoor landscape.` |
| R2 | `route_organized` | `An oil painting on canvas of a path or lane organizing a rural landscape.` |
| R3 | `route_organized` | `An oil painting on canvas of an outdoor track receding through fields or trees.` |
| R4 | `route_organized` | `An oil painting on canvas of a landscape structured around a visible road or path.` |
| L1 | `open_or_wooded_land` | `An oil painting on canvas of open fields and distant land viewed outdoors.` |
| L2 | `open_or_wooded_land` | `An oil painting on canvas of a wooded hillside or forest landscape.` |
| L3 | `open_or_wooded_land` | `An oil painting on canvas of an orchard or garden landscape viewed outdoors.` |
| L4 | `open_or_wooded_land` | `An oil painting on canvas of an open or wooded landscape with no dominant building, road, or body of water.` |

The exact negative prompt is
`text, lettering, signature, watermark, frame, border, photograph, collage` when the frozen model
supports a negative-prompt field. If it does not, G0 records `negative_prompt_not_supported` and does
not append equivalent words to the positive prompt.

The pre-label render contract is one landscape output per request at exactly `1536×1024` pixels,
no post-generation crop/upscale, and no image-to-image or reference-image input.
The eventual model must support that native size and the exact positive-prompt field. Scheduler,
steps, guidance, and other model-specific constants are frozen at G0 without consulting active real
pixels/features or generated trial images; a model that cannot meet the pre-label contract requires a
new protocol rather than a rewritten prompt/render frame.

Each retained template therefore has:

- one artist-free string;
- one byte-exact insertion point for the painter name;
- no title, known work, museum, year, or idiosyncratic masterpiece reference;
- no quality-ranking language such as “best” or “masterpiece”;
- a fixed negative prompt, aspect-ratio policy, and render configuration; and
- a hash and human-readable scene-group label.

Thus `T = 4G`, where `G` is the number of retained scene groups. Four paraphrases make prompt wording
a small fixed census rather than a single convenient sentence. Templates are not selected using
generated images or painter features.

### 11.2 Conditions

Every template is rendered under five conditions:

1. artist-free control;
2. Monet;
3. Sisley;
4. Pissarro; and
5. Cézanne.

All conditions receive the same repetitions, settings, and attempt policy. G0 obtains one 256-bit
master seed from the operating-system CSPRNG and records it before any generation. For template ID
`t` and repetition `r`, derive a candidate integer from
`HMAC-SHA256(master, "pfg-v1/2.0|seed|" || t || "|" || r)` and use rejection sampling into the
model's documented seed domain. Template domains are separate; the resulting list is an IID-uniform-
with-replacement design assumption and chance repeats are retained. The same derived seed for one
template/repetition is shared across all five conditions. No seed is tested or replaced because of
its output.

For a local deterministic model, repetition `r` is the resampling block containing all templates and
all five conditions, although its template seeds are domain-separated. For a remote/opaque service,
repetition `r` is sent as one complete balanced wave containing every template × condition request,
in an HMAC-derived random order. Provider version, region, account, moderation state, and request
timestamps are recorded. A detected provider change inside a wave, a shock crossing only part of a
wave, or fewer than 25 defensibly independent complete blocks makes inference inconclusive. Adjacent
complete waves sharing a documented outage/backend episode are merged into one resampling block;
their constituent requests are never resampled separately.

### 11.3 Model freeze

G0 freezes one exact model artifact or service identity, checkpoint/hash, VAE, scheduler, sampler,
precision, library versions, safety/moderation behaviour, resolution, aspect ratio, guidance,
steps, seed semantics, prompt strings, negative prompt, and request order. A silent model update or
unverifiable service identity terminates the run; it does not trigger a fallback model.

### 11.4 Generation count

The repetition count `R` is chosen before generation from the grid `{25, 50, 75, 100}`. Use the
smallest value whose whole-decision simulation meets all Section 9 operating criteria under the
actual real-frame sizes, feature dimensions, and registered block-dependence scenarios. Total planned
attempts are:

\[
T \times 5 \times R = 20 G R.
\]

Real-work count and generated repetition solve different uncertainty problems and cannot compensate
for one another.

### 11.5 Attempt accounting

Every attempt receives a terminal state: success, provider rejection, safety refusal, timeout,
transport failure, decode failure, or missing/corrupt output. There is no output cherry-picking,
rerolling, aesthetic screening, replacement, or top-up. Retries follow a frozen transport rule and
remain linked to the original attempt.

## 12. Generated-output gates

Two blinded coders apply the same scene codebook to every analyzable generated image and record
whether it adheres to its assigned broad scene. They also code season, illumination, and depth.
Raw streams are sealed before adjudication. For each painter-name condition and the artist-free
control separately, assigned-scene adherence raw agreement must be at least 0.90, nominal alpha at
least 0.80, and each nuisance field must meet 0.80 raw agreement with at most 0.20 indeterminate per
coder. Missing labels fail the affected condition. Only then does a third coder apply the same
independent two-of-three rule; failure makes the condition ineligible for a positive claim and is
not repaired by pooling conditions. The constant-complete-agreement exception in Section 7.4 applies
without change.

Four denominators remain separate:

- all registered attempts for availability;
- successfully decoded outputs for assigned-scene adherence; and
- every technically analyzable, real-copy-excluded output for the primary continuous feature
  comparison, whether or not it adheres to its assigned scene.

An off-topic output remains assigned to its registered template and counts in the primary feature
distribution; `adherent_only` is a labelled sensitivity. A high conditional similarity among a
convenient surviving subset cannot hide low availability or adherence.

Exact-file hashes, whole-image/crop similarity, and a pinned copy detector are compared with every
lawfully acquired development, qualification, auxiliary, and confirmation work. Soft near-copy
candidates receive blind review. A confirmed real-work copy makes the positive reproduction claim
fail; the searched-corpus copy rate and finite search boundary are reported. Generated-to-generated
duplicates are never deduplicated or excluded: they retain full multiplicity and therefore reduce
the coverage/spread result.

M0 freezes the detector architecture, checkpoint hash, preprocessing, whole-image and sliding-crop
search, crop scales, and two thresholds. On new-development transformations (resize, JPEG,
small crop, mirror, and mild colour change), the candidate threshold must achieve at least 0.95
sensitivity; on unrelated painter-balanced pairs it must have at most 0.01 false-positive rate.
Those requirements must repeat on new qualification without threshold change. Every flagged
generated–real pair is independently reviewed by two masked reviewers; agreement is required for
`confirmed_copy`, with a third reviewer resolving disagreement. The detector only bounds copying of
the searched corpus and transformations; it cannot prove absence of copying from opaque training
data or an unavailable work.

## 13. Statistical estimands and tests

### 13.1 Real and generated distributions

For painter `a`, retained scene group `s`, primary family `F`, and confirmation feature vectors
`x_aiF`, the real target gives each scene group mass `1/G` and each physical work within group equal
mass. The generated target gives each group equal mass, each of its four templates equal mass, and
each registered seed within template equal mass. A positive claim requires a complete technically
analyzable grid and zero confirmed real-work copies, so the primary distribution has no survivor
renormalization. Off-topic and generated-duplicate outputs remain in their assigned cells.

### 13.2 Primary distance

Let `x_asi` be the scaled real vector for painter `a`, scene `s`, work `i`; let `y_astr` be
the output vector for named condition `a`, one of four templates `t`, and repetition block `r`.
With `n_as` real works and a complete `4R` generated cell, the scene-level unbiased generator-side
energy estimator is

\[
\widehat D_{asF}=
\frac{2}{4Rn_{as}}\sum_{i,t,r}\lVert x_{asi}-y_{astr}\rVert
-\frac{1}{n_{as}^2}\sum_{i,j}\lVert x_{asi}-x_{asj}\rVert
-\frac{1}{16R(R-1)}\sum_{r\ne r'}\sum_{t,t'}
\lVert y_{astr}-y_{ast'r'}\rVert .
\]

The real self-term is exact for the complete finite target, including zero diagonal distances. The
generated self-term excludes equal repetition blocks so it estimates two independent registered seed
draws while averaging the complete template census. Its raw U-statistic value is retained even if
slightly negative; it is not clipped before inference. Generated duplicates remain as zero distances.
The painter-family statistic is `D_aF = mean_s(D_asF)` over the retained scene census.

The same formula replaces `x_a` with each comparison painter's real population for specificity and
replaces `y_a` with the artist-free control for the prompt-effect contrast. No real-work bootstrap is
used for the accessible-finite-frame claim.

### 13.3 Equivalence margin

Margins are calculated once at M0b and are never jointly tuned with `R`. For family `F`:

1. perform 2,000 fixed-seed stratified repetitions on new-development works only; within each
   painter × scene, randomly partition the works without replacement into two halves whose sizes
   differ by at most one, calculate every same-painter scene distance, and retain the maximum across
   painter × scene in that repetition; historically exposed works may support implementation but do
   not enter this margin calculation;
2. let `W_F` be the 95th percentile of those 2,000 replicate maxima using the conservative order
   statistic at index
   `ceil(0.95*(2000+1))-1` after zero-based sorting;
3. let `B_F` be the auxiliary 95%/95% tolerance bound from Section 9; and
4. freeze `epsilon_F = max(W_F, 2*B_F)`.

M0b then applies the frozen margin once to untouched new qualification. The family qualifies only
if every same-painter development-versus-qualification distance, both scene-specific and
painter-averaged, is at most `epsilon_F` and
`epsilon_F` is no greater than one half of the smallest supported wrong-painter qualification
distance. This discriminability rule prevents an enormous same-painter margin from making
equivalence trivial. Specificity and artist-name-control improvement
use the fixed minimum `delta_F = 0.25*epsilon_F`. Confirmation cannot widen either value. The exact
bootstrap seed, cell eligibility, missing-cell failure, order statistic, and resulting values are
bound in the M0b receipt.

After those margins are frozen, `R` is selected lexicographically from `{25,50,75,100}`. For each
candidate `R`, 2,000 whole-decision simulations use the actual scene counts and these fixed DGPs:

- favourable: within-scene resampling from the matching painter's new qualification plus a
  resampled auxiliary capture-difference vector with random sign;
- wrong-painter: resampling from each of the other three painters;
- pooled-control proxy: equal-painter resampling with the named painter excluded;
- central-mode collapse: resampling only from the central 50% of matching-painter vectors ranked by
  Euclidean distance to the within-scene geometric median;
- dispersion collapse: multiply every centred vector by 0.50;
- coordinate shift: add `0.50` common-scaled units to every coordinate in turn; and
- source disturbance: add the largest observed workflow-versus-complement shift vector.

Use the smallest `R` for which the exact Clopper–Pearson 95% lower bound on favourable full-
conjunction pass probability is at least 0.80 and the 95% upper bound on false pass under every
adverse DGP is at most 0.05 (equivalently, rejection lower bound at least 0.95). If no value passes,
Protocol 2.0 stops. There is no alternative margin, DGP, family deletion, or `R>100` fallback.

### 13.4 Required contrasts

For every painter and each of the three required families:

1. the simultaneous 95% upper bound for named-output distance to its own real target must be at most
   `epsilon_F`;
2. its distance to its own target must be smaller than its distance to each of the other three real
   targets by at least `delta_F` using simultaneous upper bounds for
   `D_own - D_other + delta_F`;
3. it must improve over the matched artist-free control by at least `delta_F` using the simultaneous
   upper bound for `D_named - D_control + delta_F`;
4. for every coordinate, the simultaneous absolute median difference must be at most 0.25 common-
   scaled units and the generated/real IQR ratio must lie in `[0.80,1.25]`; a zero real IQR fails;
5. every retained scene group separately must have an energy-distance upper bound at most
   `epsilon_F`; an aggregate pass cannot hide a missing group;
6. deleting any one confirmation work must not change the pass/fail decision or move a primary
   statistic by more than 10% of its frozen margin; and
7. every estimable leave-one-workflow analysis must preserve the direction and pass/fail decision.

Items 6–7 are confirmation robustness conditions evaluated only at C0. They are not inspected to
decide whether generation starts. Failure prevents the painter-reproduction label.

Inference uses exactly 9,999 resamples of whole repetition/common-shock blocks while keeping the
prompt-template census and real finite population fixed. It recomputes every binding continuous
endpoint. For each endpoint, bootstrap SD supplies its studentizer; zero or nonfinite SD makes that
endpoint inconclusive. The simultaneous critical value is the conservative 95th order statistic of
the replicate-wise maximum absolute studentized deviation across the complete frozen endpoint
inventory. One-sided or two-sided intervals then follow the endpoint's declared direction. The G0
analysis receipt records the dynamic inventory count after `G` is known, RNG algorithm/seed,
critical-index formula, tie-to-failure rule, and all zero-denominator rules.

The positive claim additionally requires exact empirical quality gates: 100% of registered outputs
must be present, decodable, and feature-analyzable; assigned-scene adherence must be at least 0.90
under equal-template weighting and at least 0.75 in every template × condition cell; and confirmed
copies of any searched real work must equal zero. Because completeness is 100%, the binding
continuous analysis has no generated missingness or MNAR renormalization. Runs failing a quality
gate are reported completely but cannot receive a conditional reproduction label.

### 13.5 Decision language

Results are reported at three levels:

- `family_reproduced` or `family_not_demonstrated` for each painter × family;
- `painter_reproduced_on_all_three_primary_families` only when all three families and every gate pass;
- `panel_reproduction_demonstrated` only when all four painters pass.

An inconclusive, unqualified, source-sensitive, or failed family is shown explicitly. No averaging
across failed and successful families creates a global score.

## 14. Bias and robustness analyses

The following are mandatory and cannot rescue a failed primary result:

- uniform-work rather than equal-scene real weighting;
- per-scene results;
- leave-one-authority/source-group results where estimable;
- ICC-present versus ICC-missing files;
- native short side ≥2,048 versus 1,024–2,047;
- same-work independent-capture disturbance;
- season, illumination, and depth distribution differences;
- border/crop-mask sensitivity;
- diagnostic Kim A/C, CSD, and CLIP spaces;
- learned evaluator nearest-neighbour and source-prediction alarms; and
- removal of reviewed near-copy candidates.

If a result depends on one source, crop policy, capture family, learned evaluator, or unsupported
content subset, the claim is narrowed or rejected.

## 15. Stages, freezes, and stopping rules

| Stage | Work | Output required before proceeding |
|---|---|---|
| R0 | exhaustive metadata census and pre-label prompt library | exact intents, raw-response hashes, terminal receipts, candidate manifest, 16-template hash |
| R1 | authority/rights/identity acquisition | physical-work graph, rights/quality manifest, raw-file hashes, attrition table |
| R2 | blind eligibility and scene coding | two raw code streams, reliability receipt, adjudicated finite frame, exposure denylist |
| M0 | measurement qualification | fixtures, auxiliary-capture results, qualified families, scaling, margins, simulation code/results |
| G0 | prompt/model/seed preregistration | exact prompt/model hashes, `G`, `T`, `R`, request order, analysis freeze |
| G1 | generation | append-only attempt ledger, outputs and hashes, no reference opening |
| C0 | one-time confirmation | reference opening receipt, frozen analysis execution, complete report |

Each freeze is hash-bound and independently reviewed. A failure does not permit a silent change of
source, painter, prompt, model, feature, margin, or endpoint. The choices are: repair the same
contract if the failure is purely technical and prospectively allowed; stop; or issue a new protocol
version before viewing protected outcomes.

## 16. Current authorized state

At Protocol 2.0 issuance:

- 3,190 Wikidata item candidates from a material-constrained exploratory query exist;
- 3,364 distinct Commons filenames are in the fixed seed;
- no completed current Commons rights/geometry audit exists; the earlier sample terminated with
  HTTP 429 and supports no reusable-file yield claim;
- 43 direct official-source all-content candidates have been item-resolved in a separate audit;
- zero active-study physical works are admitted;
- zero active-study image files are downloaded;
- zero confirmation works are opened;
- zero generation attempts are registered; and
- zero generated-versus-real results exist.

The next authorized action is metadata-only: repair and independently review the fixed-seed
Wikidata/Commons attrition collector, execute it without image download or admission, then freeze and
run the broader no-`P186` discovery census. Image acquisition begins only under a separate R1
authorization that binds authority, rights, identity, and technical gates.

## 17. Required reports and reproducibility artifacts

The project must preserve:

- source registry and exact request intents;
- raw response hashes and terminal provider receipts;
- candidate and exclusion manifests with one terminal reason per row;
- authority crosswalk and canonical physical-work/capture graph;
- rights, geometry, ICC, decode, and complete-view receipts;
- raw and normalized image hashes without committing restricted bytes;
- both blind code streams, calibration and reliability receipts, and adjudication decisions;
- exposure denylist and sealed confirmation manifest;
- feature specification, fixtures, software lock, and vector hashes;
- prompt/model/seed/request freeze;
- full generation attempt ledger and output hashes;
- simulation inputs, code, results, and decision thresholds; and
- a complete Korean methods/data/results report that distinguishes candidates, downloaded assets,
  eligible physical works, confirmation works, generated outputs, and analyzable results.

Every count must name its denominator. “Collected paintings” is not used for unresolved metadata
rows, duplicate files, or unverified candidates.

## 18. Protocol-level quality checks

Before any panel-level claim, the independent review must be able to answer “yes” to all of these:

- Does the analysis compare generated and real distributions rather than painter classifiers?
- Was subject matter held to one common, explicitly weighted frame?
- Was every declared source exhausted without target-count stopping?
- Does every real row resolve to one authority-backed physical work and one lawful primary asset?
- Were previously exposed works excluded from confirmation?
- Were primary features qualified against independent-capture and source disturbance?
- Were model, prompts, seeds, margins, `R`, and analysis frozen before generation/reference opening?
- Did named outputs fit absolutely, beat every wrong painter, improve over artist-free control, and
  retain coverage without copying?
- Are source, content, availability, adherence, and missingness limitations visible rather than
  averaged away?

If any answer is no, the strongest permitted statement is that painter-feature reproduction has not
been demonstrated under this protocol.
