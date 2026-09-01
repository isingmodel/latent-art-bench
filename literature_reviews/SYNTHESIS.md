# Evidence synthesis: measuring a painter-associated feature

## Executive finding

The review does not support a single universal “style vector.” It supports a stricter object:

\[
\mathcal P_a =
P\{z(X)\mid a,\ \text{career phase},\ \text{genre/content},\
\text{medium/support},\ \text{source/reproduction}\},
\]

where \(a\) is the attributed painter and \(z\) is a panel of separately qualified coordinates.
The painter feature is the conditional, uncertainty-bearing distribution across eligible works.
It is not one file, one centroid, one encoder, one classifier, or the visual effect of inserting
an artist name into a prompt.

This definition preserves Pilot 2's scientific aim while correcting its central weakness.
Pilot 2 established only **pooled artist-label predictability within the fixed Pilot 2 atlas** in
a deterministic adaptation of Kim's A-vector. A separate two-class task showed high source
predictability, and the painter task failed true opposite-source transfer. These unlike tasks are
not ranked by their raw balanced accuracies. Pilot 2 therefore established neither a transferable
painter feature nor any generated-output effect. The relaunch makes
reproduction reliability, source/content transfer, hard-neighbor specificity, and
within-painter coverage mandatory before either claim can be made.

The present artifact is a prospective **design framework**, not an executable or preregistered
study protocol. It identifies constructs, candidate measurements, gates, and claim boundaries.
A separate execution-freeze artifact must still set corpus incidence and minimum counts, exact
estimators, simulations, smallest effects of scientific interest, thresholds, multiplicity,
missingness actions, and terminal decisions before any data are acquired or analyzed.

## 1. Scope and evidential posture

The review covers six linked literatures:

1. interpretable image measurements used in computational studies of paintings;
2. art-specific and general learned representations;
3. Kim et al.'s A- and C-vector methods and exact released implementation;
4. digitization, color management, and same-work reproduction variability;
5. human perception and construct validation; and
6. distributional statistics, dependence, robustness, and missingness.

Primary papers, official standards, supplements, and released code are preferred. Reviews and
surveys are used for discovery, not as the sole authority for a method decision. “Works on an art
dataset” is not equivalent to “validly measures painter practice.” Evidence grades and review
depth appear in the evidence matrix; search procedures and stopping logic appear in the search
protocol and log.

The review uses four claim levels:

- **file-descriptive:** describes bytes under a named decode/preprocessing path;
- **reproduction-associated:** stable enough across controlled derivatives or captures to
  describe digitized reproductions;
- **painter-associated:** retains painter information on held physical works under source and
  content transfer;
- **human-perceived painterly relation:** predicts judgments under a specified task, population,
  display, and image domain.

A paper's terminology does not determine the reboot's claim level.

## 2. What Pilot 2 contributes

Pilot 2 made several decisions worth preserving:

- painter, not movement or period, was the target;
- physical works were held out;
- two sources were balanced in the small atlas;
- PCA was fit on real training works only;
- named prompts had matched painter-free controls; and
- target movement and target-versus-neighbor specificity were distinct estimands.

Its negative evidence is equally important:

| Diagnostic | Pilot 2 result | Interpretation |
|---|---:|---|
| Held four-painter balanced accuracy | 0.50 | Pooled artist-label predictability within the fixed Pilot 2 atlas |
| Source balanced accuracy | 0.8125 | High source predictability on a separate two-class task; do not rank raw BA against the four-class painter task |
| Train NGA, test AIC painter accuracy | 0.25 | Chance-level cross-source transfer |
| Train AIC, test NGA painter accuracy | 0.375 | Weak, inconclusive cross-source transfer |
| PCA components / training works | 22 / 24 | Nearly saturated reference geometry |
| Held works defining each painter centroid | 4 | Inadequate oeuvre distribution and coverage estimate |

Five moderation refusals made the registered generated-output grids incomplete, so none of the
four primary tests ran. That is a valid scientific result, not a software defect to erase.

Accordingly, Pilot 2 did not establish a transferable painter feature and did not establish any
named-prompt or generated-output effect. Its real-only result is confined to the fixed atlas and
its incomplete generator phase is a non-result for the registered effect estimands.

The reboot retains Pilot 2 as historical evidence and creates a new prospective namespace. It
does not recompute Pilot 2, retry missing cells, refresh hashes, or acquire any closed holdout.

## 3. Interpretable coordinates: supported uses and limits

### 3.1 Color and luminance

Across studies of paintings and natural images, distributions of lightness, chroma, hue, and
local color transitions are empirically informative. Kim, Son, and Jeong (2014) provide RGB
color-rank, gamut-box-count, brightness-roughness, and weighted-entropy baselines; Lee et al.
(2018) provide adjacent CIELAB color-distance distributions; and Seo et al. (2018) provide a small
multiscale spatial color-interaction analysis. The ordinal-pattern lineage instead comes from
Sigaki, Perc, and Ribeiro (2018) and the tie-aware extension of Tarozo et al. (2025).
Nascimento et al. and Nakauchi and Tamura show that gamut orientation, color moments, and hue
rotation can affect preference judgments. Those are perceptual color-organization results, not
evidence of painter identity, color constancy, or physical-color fidelity.

The evidence supports fixed, interpretable coordinates such as CIELAB lightness/chroma
quantiles, circular hue moments above a low-chroma threshold, fixed-bin occupancy, and adjacent
chromatic-transition distributions. It does not support claims about pigments, original
appearance, or physical palette from uncontrolled RGB downloads.

Color coordinates are conditional on capture, ICC metadata, illumination, gamut mapping,
white point, tone response, and delivery processing. They cannot become core painter coordinates
until they pass same-work independent-reproduction and leave-source-out gates.

### 3.2 Spatial frequency, edges, and texture

Fourier spectra, wavelets, and edge-orientation statistics capture complementary multiscale
structure. Research by Graham and Field, Redies and colleagues, Koch et al., Braun et al., Lyu
et al., Hughes et al., and wavelet/stylometry studies shows that these measurements can
differentiate image groups or expose processing history.

The defensible coordinates are response profiles rather than talismanic exponents:

- octave-band luminance power, slope with fit diagnostics, anisotropy, and residual curvature;
- edge density threshold curves, orientation entropy, anisotropy, and multiscale self-similarity;
- fixed wavelet-band energy and entropy, cross-scale ratios, and local-energy distributions.

A spectral slope is not proof of fractality or aesthetic quality. Ordinary catalog images do
not preserve the microscopic scale needed to infer physical brushstroke mechanics. Crop,
border, resampling, sharpening, compression, and resolution sensitivity must be quantified.

### 3.3 Ordinal complexity

Tie-aware \(2\times2\) ordinal-pattern distributions and derived entropy/complexity measures are
compact and interpretable. They are sensitive to local organization, but also to quantization,
codec, grayscale conversion, and scale. The complete state distribution should be retained; a
single entropy or complexity number is secondary.

### 3.4 Composition

Coarse saliency, spatial mass, symmetry, and centroid statistics can describe global
organization. Empirical composition studies show modest, context-dependent relations rather
than universal laws. These coordinates are secondary because subject, crop, frame, and motif can
dominate them. They must be tested on whole works and details separately and under content
matching.

### 3.5 Physical painter's-hand methods

Topography, spectroscopy, microscopy, radiography, and technical imaging can sometimes support
claims about materials, layering, or handling that RGB catalog images cannot. These studies are
important comparators because they define the boundary of the current evidence. The reboot will
not use digital-image texture as a proxy for pigment, binder, impasto height, or authentication.

## 4. Learned representations

### 4.1 Kim A-vector

Kim et al.'s A-vector is a sampled Stable Diffusion 2.0 VAE latent after a forced \(512\times512\)
resize, flattened from \(4\times64\times64\) to 16,384 values. The exact released script has an
unreachable model initialization and undefined model reference; it does not release the exact
checkpoint hash, RNG realization, reference vectors, or complete environment. The resize path
distorts aspect ratio and re-encodes files according to their original extensions.

The vector jointly contains color, luminance, objects, composition, texture, border/crop,
interpolation, codec, and SD2 training-distribution effects. It is properly named a Kim
A-vector or SD2-VAE appearance coordinate. It is not, without qualification, a formal or painter
feature.

The incomplete artifact contract does not permit a claim of exact replication. A future
source-faithful, versioned **compatibility reconstruction** may preserve the published resize,
codec, tensor, and posterior-sampling path as far as the released sources permit. Repairing the
unreachable model initialization or supplying a checkpoint necessarily creates an adaptation,
which must be named and reported as such. A posterior-mean or repeated-draw branch with
propagated variance is a separate methodological adaptation, not a recovery of the authors'
unreleased realization.

### 4.2 Kim C-vector

The C-vector is a 1,024-dimensional CLIP Interrogator image feature from
ViT-H-14/laion2b_s32b_b79k, applied to the original image path rather than A's forced-square
derivative. It is strongly capable of encoding subject, objects, iconography, text-like marks,
period, attribution-associated web signals, and possible training overlap.

It is retained only as a contextual/semantic and leakage-sensitive diagnostic. A and C are not
two clean halves of one “form/context” decomposition because their encoders, training corpora,
and preprocessing differ.

The C-vector is likewise provisional until its complete artifact contract—including resolved
model weights, dependency versions, preprocessing behavior, and a reference fixture with
tolerance—is recovered. Until then, a versioned implementation can only be called a
compatibility reconstruction, not an exact Kim C replication.

### 4.3 CSD and other style-oriented embeddings

CSD is promising because it was designed for style similarity and evaluated on artist
retrieval. Its training used more than half a million LAION-Aesthetics images with thousands of
caption-derived artist, medium, and movement tags plus spatial self-supervision. Artist identity
is therefore part of its supervisory ecology; painter recognition may include web-label and
content signals. The official repository currently warns that released weights produce
discrepancies from paper results.

CSD remains diagnostic until the exact checkpoint is reconciled and it passes local:

- independent-capture reliability;
- leave-source-out and leave-content-out transfer;
- hard-neighbor discrimination;
- candidate-pool and cosine calibration tests;
- within-painter phase/genre coverage; and
- pretraining/near-copy audits.

ALADIN, Gram/AdaIN representations, GOYA, DINO-like features, CLIP variants, and diffusion-model
features offer useful evaluator-family sensitivity. Their labels and training objectives define
what they recover; none supplies an independent painter ground truth.

### 4.4 Recognition is not coverage

Artist classification, retrieval, or prompted-name recovery can show artist-label predictability
within the tested corpus and split.
It cannot show that a representation covers early and late practice, rare genres, multiple
media, or atypical works. A generated set can be readily recognized because it repeats a narrow
stereotype. A later canonical painter-fidelity claim therefore requires conjunctive absolute
fit/equivalence, panel-wide worst and lower-quantile hard-neighbor specificity, precision, density,
recall, coverage, content coherence, and availability robustness. Contraction and prompt movement
remain mandatory nongating outcomes.

## 5. Reproduction and source are part of the measurement

ISO 19264-1, FADGI, Metamorfoze, and color-management research provide requirements for
evaluating imaging systems and preservation reproductions. They do not retroactively calibrate
uncalibrated web images. Embedded profiles, capture targets, tone response, sharpening, gamut,
codec, crop, and display transformations can alter measured features.

The unit hierarchy is:

\[
\text{physical work} \supset \text{capture} \supset \text{delivery derivative}
\supset \text{analysis transform}.
\]

Multiple URLs or resolutions derived from one master are not independent reproductions. The
prospective corpus must include a panel of independently produced captures of the same physical
works. A coordinate intended to describe a work must show same-work agreement across those
captures beyond matched different-work agreement.

The project keeps:

- original bytes and metadata unchanged;
- a deterministic color-managed harmonized branch when profiles permit;
- separately flagged assumed-sRGB results;
- source-faithful compatibility branches used only to reconstruct published methods under an
  explicit versioned artifact contract; and
- multiscale aspect-preserving analysis without unsupported upsampling.

Provider and source remain modeled variables. Harmonization is not proof that source effects
have disappeared.

## 6. Human construct evidence

“Style” is not an error-free label. Judgments can depend on expertise, instructions, subject,
color, familiarity, display, and cultural context. The validation target must therefore be a
specified observable relation.

The primary proposed task is a triplet judgment: given an anchor work, which candidate is closer
in visible painterly manner while attempting to ignore depicted subject? Separate tasks measure
content, color organization, mark/texture, and overall appearance. This creates convergent and
discriminant evidence rather than one ambiguous style rating.

The stimulus design crosses:

- same-painter/cross-content and cross-painter/content-matched comparisons;
- hard-neighbor and broad-negative painters;
- whole works and details;
- same-work independent captures; and
- controlled color, scale, crop, and phase perturbations.

Experts and nonexperts are separate execution-frozen populations. A hierarchical Bradley–Terry,
Thurstone, or ordinal model crosses raters and physical works. Agreement, heterogeneity, and
expertise effects are results; majority vote is not treated as truth.

Attribution and source interfaces are blinded, signature/text handling is frozen, and recognition
is measured after the primary judgment. Unfamiliar-work judgments are primary; recognized-work
and unmasked branches are reported as sensitivities. Final criterion works and raters remain
independent of metric selection.

No method may use the phrase human-perceived painterly similarity unless it predicts held-out
judgments under the stated task, population, display, and domain beyond content and source
baselines.

## 7. Statistical synthesis

### 7.1 Real-only qualification precedes generation

The empirical sequence is:

1. specify the corpus, connected joint common support, fixed target weights, reproduction
   incidence/rank audit, and candidate coordinate cards;
2. test computational identity;
3. estimate controlled perturbation response;
4. test independent-reproduction reliability;
5. test held-work painter association and nuisance increment;
6. test leave-source, leave-content, joint source-by-content, career, and unopened-workflow
   external transfer;
7. obtain human convergent/discriminant evidence; and
8. freeze the painter distribution before any generated image is viewed.

Opening generated outcomes before the feature freezes would allow the measurement to be tuned
toward the desired conclusion.

### 7.2 Generated-image outcomes remain plural

If a later execution-freeze artifact authorizes generation, a canonical painter-fidelity claim
requires a **conjunction**, not success on a convenient single score:

- absolute target fit demonstrated by a prespecified equivalence or noninferiority decision
  against an eligible real-to-real reference scale, rather than failure to reject a difference;
- the full target-versus-hard-neighbor margin vector evaluated on one panel-wide common support,
  with the binding specificity decision made on the prespecified worst and lower-quantile eligible
  margins;
- generated-to-real precision **and** density each meeting its frozen support criterion;
- real-to-generated recall **and** coverage each meeting its independently frozen support
  criterion;
- content coherence meeting its frozen cross-cell robustness rule; and
- refusal, failure, and valid-output availability meeting the frozen availability rule.

The study must additionally report, without assigning an automatically favorable direction:

- phase/genre/medium-stratified coverage where estimable;
- contraction relative to real within-painter dispersion;
- named-versus-control prompt movement; and
- the separate contextual content coordinate.

No weighted composite is planned. Failure of any conjunct in the canonical claim prevents the
painter-fidelity conclusion even if prompt movement or another nongating outcome is positive.
Each outcome also remains visible because the components have different failure modes and
evidential meaning.

### 7.3 Dependence and missingness

Physical works, not patches, derivatives, raters, or all pairwise distances, are the primary real
sampling units. Work-clustered or crossed hierarchical inference respects nested and crossed
dependencies. Randomization tests preserve joint source/content/medium/phase exchangeability
blocks that contain at least two painters. An experiment-wide omnibus or closed-testing hierarchy
covers selection among primary families, coordinates, scales, encoders, painters, and validation
endpoints; family-local adjustment cannot support the project-level claim.

In a future generated study, the shared control and all painter targets in a content-by-model-by-
seed bundle are resampled together, and shared real references are jointly resampled across
contrasts.

Missing works, failed measurements, generation refusals, invalid outputs, and rater exclusions
are separately classified. Sampling-frame denominators, joint-cell minima, and completion rules
remain fixed. Differential selection and registered missing-not-at-random bounds or tipping
analyses are mandatory; a nonrobust decision is narrowed, failed, or left unexecuted. An incomplete
confirmatory pair grid is not repaired with an unregistered available-case substitute.

## 8. Final disposition of method families

| Family | Reboot disposition | Highest claim before qualification |
|---|---|---|
| CIELAB distribution and chromatic transitions | Core candidate | file/reproduction-associated color profile |
| Multiscale Fourier and edge/orientation | Core candidate | file/reproduction-associated spatial structure |
| Wavelet energy/entropy | Core candidate | file/reproduction-associated texture energy |
| Tie-aware ordinal patterns | Core candidate | file/reproduction-associated ordinal organization |
| Coarse composition/saliency | Secondary candidate | file-level spatial organization |
| Kim A | Versioned compatibility reconstruction; any repaired extractor is an adaptation | SD2-VAE appearance coordinate |
| Kim C / CLIP | Provisional compatibility reconstruction until artifact contract recovery | semantic/contextual similarity |
| CSD | Provisional learned painter-association diagnostic | CSD similarity under pinned artifact |
| ALADIN/GOYA/DINO/diffusion features | Evaluator-family sensitivity | model-specific appearance relation |
| FID | Historical sensitivity only | encoder-specific aggregate discrepancy |
| MMD/energy distance | Candidate set discrepancy | distribution difference in qualified coordinates |
| Precision and density, recall and coverage | Four required support outcomes | support relation in qualified coordinates |
| Human triplets/attributes | Criterion evidence | task- and population-specific perception |
| Microscopy/spectroscopy/topography | Out of current RGB scope | none from ordinary catalog RGB |

## 9. What the literature cannot justify

The project will not claim:

- that a single vector contains a painter's style;
- that visual classification establishes artistic essence or authorship;
- that a catalog RGB image reveals pigment, binder, impasto, or microscopic brushwork;
- that chronology, movement, nationality, and painter are interchangeable;
- that CLIP semantics cleanly separate context from form;
- that source normalization erases capture bias;
- that centroid proximity establishes oeuvre coverage;
- that one neighboring painter establishes specificity;
- that a positive named-prompt contrast establishes absolute fidelity;
- that a very small pairwise \(p\)-value represents independent evidence when works recur across
  pairs; or
- that a Western canonical web corpus supports universal claims about art.

## 10. Research recommendation

Proceed only to development of a **real-only qualification execution plan** from the versioned
painter_features_v1 design framework. Before acquisition or feature extraction, add and
independently review a frozen execution artifact that identifies painters, sources,
physical-work eligibility, connected common support, reproduction-panel incidence and minima,
exact estimators, power or precision simulations, smallest effects of scientific interest,
thresholds, multiplicity, missingness actions, and the sealed confirmation boundary. Until that
artifact exists, this package is neither executable nor preregistered.

Do not yet authorize external-holdout access, generated-image transport, image generation, or
analysis of the incomplete Pilot 3 cohort. The current work proposes a defensible method and
claim architecture for later freezing and testing; it does not claim that any candidate has
already qualified as the painter feature.
