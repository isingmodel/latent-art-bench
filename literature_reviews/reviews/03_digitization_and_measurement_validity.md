# Digitization, reproduction, and measurement validity for painter-associated features

Review depth: 17 primary studies or method papers and one official cultural-heritage imaging
standard, selected for direct implications for the prospective painter-feature protocol

Question: when can a feature measured from image files support an inference about a painter's
recurring visual signature across physical works, rather than about a file, reproduction source,
subject, medium, or preprocessing pipeline?

## 1. Conclusion

A digital file is not a painting, and a second file of the same painting is not a second work.
The physical work must be the sampling and split unit. Files, crops, augmentations, tiles, and
repeated extractions are technical observations nested within that work. They may improve
measurement precision; they do not increase the number of independent works.

The literature does not justify a universal correction that converts heterogeneous web images
into faithful measurements of painted surfaces. Color can change with capture, illumination,
profiling, gamut mapping, browser behavior, embedded-profile handling, compression, and display.
Gradient, entropy, texture, and learned features also change with crop, border, resolution,
resampling, and codec. Some image statistics survive some reproduction routes, but that is an
empirical result for a particular feature and corpus, not a transferable guarantee.

Accordingly, the prospective study should make three successively stronger claims:

1. **File validity:** an implementation measures a declared property of exact decoded bytes.
2. **Reproduction validity:** that property is sufficiently stable under prespecified, plausible
   reproduction and preprocessing variation.
3. **Painter validity:** after the first two gates, the property distinguishes the target painter
   from matched non-target painters and characterizes the target's within-painter distribution on
   held physical works, including held-source tests.

Failure at a stronger level does not erase a weaker result. It narrows the claim. A descriptor
that reliably distinguishes AIC files from NGA files, for example, may be a valid source feature
and an invalid painter feature.

## 2. Inferential object and measurement model

Let (a) index painter, (w) a physical work nested within painter, (r) a reproduction of that
work, and (p) a frozen decoding/preprocessing branch. The measured vector is

\[
z_{awrp}=f_p(\text{file}_{awr}).
\]

A useful design-level decomposition is

\[
z_{awrp}=\mu+A_a+W_{w(a)}+X_w\beta+S_r+(A\!\times\!S)_{ar}+P_p+\epsilon_{awrp},
\]

where (X_w) contains declared content/genre, medium/support, date, scale, and condition variables;
(S_r) contains institution, capture, derivative, profile, resolution, crop, and codec effects;
and (P_p) is preprocessing. This is not a promise that every term is identifiable. It is a
statement of what the corpus must cross or match before a painter component can be interpreted.

The primary objects are therefore:

- the target painter's distribution across works, not a single centroid;
- its within-painter covariance, tails, modes, and content interactions, not residual noise to be
  normalized away;
- target-versus-matched-non-target separation on held physical works; and
- stability of those quantities across reproduction source and allowed preprocessing.

The relevant population is also explicit. With a small, purposively selected painter set, the
study can make painter-specific claims about those painters and the sampled work domain. It cannot
estimate a universal variance component for “all painters.”

## 3. Pilot 2 as a falsification case

Pilot 2 usefully demonstrated why work-level separation alone is not enough. Its atlas contained
40 physical works: four painters, two sources, and five works in each painter-source cell. The PCA
fit used 24 works and the held set contained 16, only four held works per painter. The generated
primary comparisons were never run because refusal-created cells were incomplete, so the valid
historical conclusion was `REDESIGN`.

| Frozen Pilot 2 result | What it rules out | Prospective correction |
|---|---|---|
| Painter held balanced accuracy 0.50 versus chance 0.25; Monet and Pissarro recall 0.25 | a pooled score does not imply reliable identification of each painter | report each target's sensitivity, false-positive pattern, hard neighbors, and uncertainty across works |
| AIC held balanced accuracy 0.625; NGA 0.375 | source-stratum performance was heterogeneous and based on eight held works per source | balance sources within painter and report source-specific intervals, not only a pooled estimate |
| Train NGA/test AIC painter accuracy 0.25; train AIC/test NGA 0.375 | the apparent painter signal did not transfer convincingly across source | make leave-source-out transfer and same-work independent-reproduction reliability mandatory gates |
| Source balanced accuracy 0.8125 | high acquisition-source predictability occurred on a separate two-class task; its raw balanced accuracy is not directly comparable to the four-class painter task | freeze a source probe; quarantine source-predictive coordinates unless painter evidence survives without them |
| Source-stratified permutation (p=0.0216) | stratifying one nuisance cannot establish reproduction, content, medium, or construct validity | constrain inference at physical-work level and test each prespecified nuisance and interaction |
| Forced square resize and one seeded VAE posterior draw | the vector included choices with unknown stability and a stochastic measurement step | preserve aspect ratio; prefer deterministic measures; if stochastic extraction remains, estimate repeatability over repeated draws |
| No independent files of the same work | within-work reproduction variance was unidentifiable | prospectively acquire or locate independent reproductions before claiming physical-work generalization |

The failure is informative: if a target painter is only recognizable when painter and source travel
together, the measurement has learned a catalog signature. That is not a near miss. It is a
different construct.

## 4. Source-verified evidence

### 4.1 Cultural-heritage reproduction and color

| Source | Method and decision-relevant evidence | Assumptions and limitations | Protocol disposition |
|---|---|---|---|
| [MacDonald, Morovic & Saunders 1995, *Evaluation of colour fidelity for reproductions of fine art paintings*](https://doi.org/10.1016/0260-4779%2895%2900052-6) (journal DOI alias: [10.1080/09647779509515446](https://doi.org/10.1080/09647779509515446)) | High-resolution digital captures and printed reproductions of three National Gallery paintings were compared with originals by pair comparison under multiple illuminants and gamut mappings. The preferred mapping depended on pictorial content. | Three paintings and print-era technology; perceptual preference is not physical fidelity. | Reject one universal gamut transform. Record the transform and test feature stability by content; do not tune on the target painter. |
| [Szücs & Sik-Lányi 2016, *Color Rendering of Images in the Internet and Print Reproductions of the Sistine Chapel's Frescos*](https://doi.org/10.1080/15502724.2014.1000495) | Colored patches in web files and two albums for four frescoes were compared with Vatican and in-situ measurements. Significant differences arose from several stages, including browser rendering, JPEG, implicit color spaces, EXIF, and display. | Four frescoes; patch comparisons do not describe every spatial feature. | Treat provider, file profile, codec, and presentation path as measured provenance. Web RGB cannot be silently treated as physical color. |
| [Kirchner et al. 2021, *Exploring the limits of color accuracy in technical photography*](https://doi.org/10.1186/s40494-021-00536-x) | In a Rijksmuseum technical-photography workflow, black ColorChecker SG patches made a major contribution to error. Spectrophotometric data versus generic references already produced average CIEDE2000 0.82 overall and 0.59 without black patches; manual profile tweaking against generic data could worsen dark rendition. | Results concern reflective targets and a high-end workflow; they do not calibrate legacy web files retrospectively. | For new capture, retain chart identity/version and custom measurements. Never equate software “pass” or manual visual adjustment with unbiased truth. Include dark-tone diagnostics. |
| [Amano, Linhares & Nascimento 2018, *Color constancy of color reproductions in art paintings*](https://doi.org/10.1364/JOSAA.35.00B324) | Hyperspectral data for originals and postcard reproductions were rendered under several illuminants. Relational color-constancy indices were much higher for skin regions (about 0.76–0.81) than for many non-skin regions (about 0.19–0.68). | Five paintings and specific regions/illuminants; observer constancy is not colorimetric equivalence. | Do not use human tolerance of a reproduction as proof that color coordinates are stable. Stratify color diagnostics by luminance/chroma and content region. |
| [Sharma, Wu & Dalal 2005, *The CIEDE2000 color-difference formula: implementation notes, supplementary test data, and mathematical observations*](https://doi.org/10.1002/col.20070) | Provides reference pairs, implementation notes, and discontinuity/edge cases for CIEDE2000. | Validates implementation, not the provenance of input Lab values and not painter style. | Unit-test color-difference code against the published data; label CIEDE2000 a sensitivity measure, never a style score. |
| [Federal Agencies Digital Guidelines Initiative, *Technical Guidelines for Digitizing Cultural Heritage Materials*, 3rd ed., 2023](https://www.digitizationguidelines.gov/guidelines/digitize-technical.html) | Official performance-oriented guidance couples master-file practice, targets, metadata, quality management, and conformance evaluation. | A normative workflow, not an experiment; mainly addresses controlled digitization, not heterogeneous downloaded derivatives. | Use as the minimum documentation model for any new acquisition. A legacy file without those records remains legacy evidence and must be tested rather than “upgraded” by assumption. |

### 4.2 Art-image features and reproduction sensitivity

| Source | Method and evidence | Assumptions and limitations | Protocol disposition |
|---|---|---|---|
| [Redies & Groß 2013, *Frames as visual links between paintings and the museum environment*](https://doi.org/10.3389/fpsyg.2013.00831) | PHOG-derived complexity, self-similarity, and anisotropy were compared for paintings, frames, museum scenes, and three reproduction routes. For the 27 Painting Gallery and 31 National Gallery works available in museum photographs, book scans, and Google Art Project files, the authors reported no significant within-museum differences among reproduction groups after reducing every image to 100,000 pixels. Frames themselves changed measured structure. | Absence of a significant aggregate difference is not an equivalence result and does not quantify same-work repeatability or limits of agreement. Technical ancestry for downloaded files was unavailable; the analysis did not report a paired work-level error distribution, and standardization to 100,000 pixels was chosen partly to suppress scan halftone dots. | Evidence that these three PHOG summaries can sometimes yield similar group means after aggressive standardization, not evidence of reproduction invariance. Remove or model frames and require paired same-work equivalence, repeatability, and resolution-response tests for every retained feature family. |
| [Kim, Son & Jeong 2014, *Large-scale quantitative analysis of painting arts*](https://doi.org/10.1038/srep07370) | RGB color-use, color-gamut box counts, brightness roughness, and weighted local entropy were computed for 8,798 Web Gallery of Art images; entropy used a declared 500×500 Lanczos transformation. | One web catalog; period, painter, subject, medium, and source can covary. Exact-size transformation changes spatial statistics. | Retain only as a source-faithful historical baseline. Reproduce its formula, then separately test aspect-preserving and source-robust variants before any painter claim. |
| [Lee et al. 2018, *Heterogeneity in chromatic distance in images and characterization of a massive painting data set*](https://doi.org/10.1371/journal.pone.0204430) | Adjacent-pixel CIELAB distance distributions were evaluated across 179,853 images assembled from WGA, WikiArt, and BBC. Distributional color-transition measurements are transparent and potentially interpretable. | Source/color pipelines are heterogeneous; adjacent distances change with resolution and resampling. Large (n) does not solve those confounds. | Preserve the full distribution, but require declared color conversion and resolution curves, leave-source tests, and same-work reproduction tests. |
| [Sigaki, Perc & Ribeiro 2018, *History of art paintings through the lens of entropy and complexity*](https://doi.org/10.1073/pnas.1800083115) | Two-by-two ordinal patterns, permutation entropy, and statistical complexity were computed for 137,364 WikiArt images and related to chronology/style. | One platform; exact ties, grayscale conversion, codec, resolution, and metadata taxonomy can influence the coordinates. Classification explained only part of the variation. | Treat ordinal profiles as D0/D1 candidates. Explicitly perturb codec, bit depth, tie handling, scale, and source; do not read entropy as creativity or painter essence. |
| [Ji et al. 2021, *An objective method to identify the painter's hand through surface topography*](https://doi.org/10.1186/s40494-021-00618-w) | Nine painters made triplicate paintings under shared subject, materials, tools, and palette. Optical topography separated painter hand more robustly than photographs under subject/color shifts, with fine height scales informative. | Small controlled experiment; physical topography is a different modality from ordinary RGB reproductions. | Use as the comparator for what literal painter's-hand evidence requires. RGB gradients may be called spatial image structure, not impasto, surface relief, or physical brushstroke width. |

### 4.3 General robustness, domain shift, and leakage

| Source | Method and evidence | Assumptions and limitations | Protocol disposition |
|---|---|---|---|
| [Dodge & Karam 2016, *Understanding how image quality affects deep neural networks*](https://doi.org/10.1109/QoMEX.2016.7498955) | Four image classifiers were evaluated under blur, noise, contrast, JPEG, and JPEG2000 changes; accuracy could deteriorate substantially. | Natural-image classification and older networks; no art-specific construct. | Use the corruption families as diagnostics, with art-appropriate severity ranges. A clean-file score is not evidence of stable measurement. |
| [Hendrycks & Dietterich 2019, *Benchmarking neural network robustness to common corruptions and perturbations*](https://openreview.net/forum?id=HJz6tiCqYm) | ImageNet-C and ImageNet-P separate clean accuracy from corruption and perturbation robustness. | Benchmark corruptions are not a probability model for museum reproduction. | Report clean validity and perturbation stability separately. Calibrate severities to observed source differences rather than importing benchmark defaults. |
| [Parmar, Zhang & Zhu 2022, *On Aliased Resizing and Surprising Subtleties in GAN Evaluation*](https://openaccess.thecvf.com/content/CVPR2022/html/Parmar_On_Aliased_Resizing_and_Surprising_Subtleties_in_GAN_Evaluation_CVPR_2022_paper.html) | Different resize implementations and lossy compression caused large changes in FID, KID, IS, and related features; matching JPEG artifacts could spuriously improve FID. | Focuses on generative metrics, not painter coordinates, but the signal-processing failure is general. | Freeze library/version/kernel/antialias behavior, preserve aspect ratio, and run cross-implementation sentinels. Never match codecs merely to improve an evaluation score. |
| [Torralba & Efros 2011, *Unbiased look at dataset bias*](https://doi.org/10.1109/CVPR.2011.5995347) | Dataset-of-origin recognition and cross-dataset transfer experiments showed strong dataset signatures even among nominally similar natural-image collections. | Older object datasets; not art-specific. | Include a blinded source classifier and leave-source evaluation. If source is easier to decode than painter, investigate or remove the implicated coordinates. |
| [Recht et al. 2019, *Do ImageNet classifiers generalize to ImageNet?*](https://proceedings.mlr.press/v97/recht19a.html) | New test sets collected to mimic the original protocol produced sizeable accuracy drops despite efforts to match sampling. | Natural-image classification; residual sampling differences remained. | Treat a new institution or capture route as a genuine external validation, not an interchangeable test split. Report the transfer decrement. |
| [Barz & Denzler 2020, *Do we train on test data? Purging CIFAR of near-duplicates*](https://doi.org/10.3390/jimaging6060041) | Near-duplicate audit found duplicate contamination in standard benchmarks; removing duplicates reduced reported performance. | Tiny natural-image benchmarks; duplicate definition is representation-dependent. | Deduplicate at accession/physical-work level before perceptual hashing. All derivatives, details, mirrored files, and alternate crops of one work remain in one split. |
| [Northcutt, Athalye & Mueller 2021, *Pervasive label errors in test sets destabilize machine learning benchmarks*](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/f2217062e9a397a1dca429e7d70bc6ca-Abstract-round1.html) | A systematic confident-learning and human-review audit found substantial label errors across common test sets, including ImageNet. | Automated flags and annotator adjudication are imperfect; natural-image labels differ from artwork attribution. | Require accession-linked attribution provenance, uncertainty states, and blinded adjudication. Exclude disputed attributions from confirmatory painter tests or analyze them prospectively as a separate stratum. |

## 5. Prospective corpus and provenance protocol

### 5.1 Work first, file second

Assign an immutable `physical_work_id` from museum accession identity or a documented crosswalk.
Every downloaded or captured object receives a separate `reproduction_id`; every derivative receives
a `derivative_id` and parent hash. Split and resample only at `physical_work_id`.

The compact manifest should include, where available:

- painter attribution and its status, accession, title, date/range, medium, support, dimensions,
  genre/content tags, institution, and collection;
- provider URL and retrieval date, rights statement, original filename, byte hash, pixel dimensions,
  bit depth, codec, orientation metadata, embedded ICC/profile state, EXIF state, and visible frame,
  label, watermark, or background;
- declared provider derivative class, if known, and whether the file is an independent capture or a
  derivative of another file; and
- every decode, profile conversion, crop/mask, resize, channel conversion, and feature version.

A perceptual hash may find likely duplicates; it cannot define independence. Curatorial review must
resolve whether similar files depict one physical work, a series, a copy, a study, or distinct works.
Unresolved identity is a declared exclusion or sensitivity stratum.

### 5.2 Independent-reproduction panel

Before confirmatory analysis, obtain at least two demonstrably independent digitizations for a
prospectively selected subset of physical works, balanced across painter, content, medium/date, and
tonal range. “Independent” means separate capture or documented digitization lineage, not the same
JPEG mirrored by two websites. Select the panel without inspecting feature agreement.

This panel identifies reproduction variance separately from between-work variance. If independent
lineage cannot be established, the highest permissible conclusion is about declared digital
reproductions, not the physical works.

### 5.3 Source crossing and matching

No painter may be represented by only one provider in a comparison where provider varies. Every
confirmatory painter contrast should either cross painter and source or use an explicitly matched
design. Content/genre and medium/support must overlap; date and dimensions should be matched or
modeled within a prospectively bounded common-support region. A covariate model cannot rescue
complete separation, such as all target works being oil landscapes from one institution and all
controls being drawings from another.

Primary target comparisons use multiple hard non-target painters selected by declared historical,
medium, date, and subject-matter criteria. The comparison is not “target versus the rest of art.”

## 6. Color-managed and geometry-preserving analysis

1. Preserve and hash the received bytes. Never overwrite them with a normalized image.
2. Decode orientation and ICC/profile metadata with pinned software. Tagged files are converted by
   a frozen color-managed path into a declared working space/white point. Untagged files remain a
   separate assumption stratum; assigning sRGB is recorded as an assumption, not recovered fact.
3. Maintain a native-decoding diagnostic branch alongside the color-managed branch. Agreement
   between branches supports robustness; disagreement defines the scope of the coordinate.
4. Preserve aspect ratio. Analyze a fixed physical/pixel-scale curve where scale metadata permits;
   otherwise report resolution-indexed curves and restrict literal spatial claims.
5. Use antialiased resizing whose implementation, kernel, boundary rule, and library version are
   frozen. Mask frames, labels, watermarks, and non-painting backgrounds by a reproducible rule;
   retain mask area and a no-mask sensitivity branch.
6. Use lossless analysis derivatives. Codec perturbations are generated only as diagnostics, never
   substituted for the master.
7. Verify CIEDE2000 against Sharma et al.'s reference pairs. A small color difference between two
   derivatives says nothing about absolute fidelity to the unmeasured painting.

Legacy web inputs cannot be made FADGI-conforming after download. Their uncertainty should be
represented by provenance strata, independent-reproduction comparisons, and perturbation envelopes.

## 7. Reliability and perturbation study

### 7.1 Four distinct questions

| Study | Resampling unit | Question | Required report |
|---|---|---|---|
| Exact rerun | identical bytes | is the implementation deterministic and version-locked? | byte/feature hashes and maximum absolute deviation |
| Stochastic rerun | same bytes, repeated draws if any | how much measurement noise is introduced by the extractor? | coordinate and distance variance over draws; frozen aggregation rule |
| Plausible perturbation | same file, prespecified transformations | which coordinates react to codec, resize, crop/border, profile assumption, luminance/chroma, blur, or noise? | response curve and equivalence interval by coordinate/family |
| Independent digitization | distinct reproductions of the same physical work | does the representation survive the real acquisition/source process? | within-work reproduction distance and variance components versus between-work distances |

Perturbation ranges must be calibrated from observed inter-source differences or acquisition
specifications without looking at target-painter success. An implausibly tiny perturbation creates a
decorative robustness test; an extreme corruption tests a different domain.

### 7.2 Reliability estimands

For each scalar coordinate, estimate work, reproduction-within-work, source, preprocessing, and
residual variance where the crossing permits it. Report the variance components and a
generalizability/reliability coefficient for the exact intended use; do not present a generic ICC
without specifying facets, fixed/random status, and whether the target is one reproduction or an
average over reproductions.

For the vector as a whole, report at least:

- the distribution of same-work/different-reproduction distances;
- the distribution of different-work/same-painter distances;
- the distribution of target-to-matched-non-target distances;
- reproduction agreement of the work-by-work representational distance matrix; and
- coordinate-wise and family-wise perturbation response curves with simultaneous uncertainty.

The desired ordering is not merely “same-work is closest.” Technical variation must be small enough
relative to the painter comparisons that the substantive conclusion is unchanged. Equivalence
margins are specified before confirmatory results from an external reliability panel or a smallest
effect that would change a painter decision. They are not chosen as a convenient fraction of the
observed effect.

## 8. Painter-specific validity estimands

The prospective protocol should estimate a distribution, not reward a classifier for finding one
shortcut.

### 8.1 Held-work specificity

For target painter (a), define distributions of distances among held works from (a), from held
works of (a) to each matched non-target painter, and among the matched non-target works themselves.
Report:

- target-versus-each-neighbor discrimination and calibrated probabilities, not only a pooled score;
- within-painter spread, tail behavior, multimodality, and changes across content/medium/date;
- leave-one-work-out influence, so one canonical work cannot define the painter;
- coverage: the fraction and type of held target works represented by the reference distribution;
  and
- false matches, with their source, content, medium, date, resolution, and provenance inspected
  under a frozen diagnostic plan.

A narrow within-target cluster is not automatically desirable. It may indicate good measurement,
a narrow corpus, duplicated works, or loss of legitimate within-painter evolution. The result must
be interpreted against corpus coverage.

### 8.2 Nuisance falsification

Run prespecified probes for provider/source, codec, resolution bin, border/frame status, content,
genre, medium/support, and date bin. Then perform:

- train-source/test-other-source painter inference;
- source-balanced held-work inference;
- held-content and, where supported, held-medium/date inference;
- same-work cross-source nearest-neighbor and distance stability;
- removal or residualization sensitivity for coordinates strongly associated with source; and
- cue-conflict tests in which same-source non-target works compete with different-source target
  works.

Chance-level nuisance decoding is strong evidence only when the probe has adequate power. Above-
chance source decoding is a warning, not an automatic proof that every coordinate is invalid; the
decisive question is whether painter conclusions transfer across and remain stable after source
control. Pilot 2 failed that stronger test.

## 9. Prospective decision gates

Thresholds and smallest effects of interest must be preregistered before evaluating the held works.
The gates are conjunctive: later success cannot compensate for an earlier measurement failure.

| Gate | Passing evidence | Failure disposition |
|---|---|---|
| M0 — identity and provenance | unique physical-work crosswalk; disputed attribution handled; complete file lineage and hashes | stop or restrict to an explicitly auditable subset |
| M1 — leakage control | all derivatives/crops/copies of one physical work remain in one split; near-duplicate audit adjudicated | rebuild splits; no confirmatory result |
| M2 — computational repeatability | exact reruns reproduce outputs; stochastic variance is below prespecified use-specific bounds | repair or remove extractor |
| M3 — preprocessing robustness | substantive decisions are equivalent across plausible decode/resize/crop/codec/profile branches | restrict the coordinate's domain or remove it |
| M4 — independent-digitization reliability | same-work reproduction variation is below the prespecified decision margin and painter result replicates by reproduction | claim only exact-file or declared-reproduction validity |
| M5 — nuisance control | painter evidence survives source-balanced, leave-source, content, and supported medium/date tests; source cues do not drive the result | label source/content/medium association; do not call it painter-associated |
| M6 — held-work painter specificity | target separates from each relevant matched neighbor with uncertainty; result is not carried by one work | redesign reference corpus or reject the candidate feature |
| M7 — within-painter coverage | reference distribution represents declared content/medium/date scope and reports heterogeneity | narrow the claim to the covered subdomain |
| M8 — human construct validation | the qualified coordinates converge with painter-manner judgments and discriminate from content, liking, source, and quality | retain as reproducible image statistics, not painter-style measures |

## 10. Evidence dispositions and rejected shortcuts

| Lead or common practice | Disposition | Reason |
|---|---|---|
| Kim/Lee/Sigaki large web-catalog trends | `background_or_D1_candidate` | large sample size does not cross painter with provider or recover physical color/surface |
| Museum-grade color targets | `required_for_new_capture_but_not_infallible` | Kirchner et al. show chart/reference/version and dark-patch errors remain |
| Visual inspection of “good” reproductions | `diagnostic_only` | preference and color constancy can mask objective reproduction differences |
| One file per work from one source | `insufficient_for_physical_work_claim` | reproduction variance and painter-by-source interaction are unidentified |
| Multiple crops/tiles as more samples | `prohibited_as_independent_n` | they share work, capture, and most visual structure |
| Random image-level train/test split | `prohibited` | permits same-work derivatives and source shortcuts to cross the split |
| Forced square resize | `rejected_for_primary` | changes geometry and local statistics; Pilot 2 did not establish robustness |
| Source-stratified permutation alone | `insufficient` | it controls one label structure but not content, medium, date, work identity, or reproduction transfer |
| High painter classification accuracy | `necessary_in_some_uses_not_sufficient` | classifiers can exploit source, borders, content, duplicates, or imbalance |
| RGB “brushstroke,” pigment, impasto, or surface claims | `rejected_without_physical_modality` | Ji et al. show that physical topography contains information ordinary photographs do not |
| Cleaning legacy files into a common RGB space | `sensitivity_branch_not_retroactive_calibration` | missing capture/profile facts cannot be reconstructed by conversion |

The measurement review therefore authorizes no extraction from an incomplete historical cohort and
no reinterpretation of Pilot 2. It specifies the evidence a new, versioned study must collect before
an image coordinate can support the phrase **painter-associated feature across works**.
