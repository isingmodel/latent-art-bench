# Prospective measurement protocol

Protocol version: `painter_features_v1/measurement/1.0`

Status: design only; not execution authorization

## 1. Target construct and measurement model

The target construct is **painter-associated visual practice as observable across a corpus of
digitized works**. The study abbreviates this as a *painter feature*. It is a population-level
construct: no single work is the painter feature, and a feature that separates painter labels
only because one museum, genre, medium, or time interval is unique to a painter has failed.

The observed image is not the painting. For physical work \(w\), reproduction \(r\), source
\(s\), and processing branch \(p\), a measured feature is treated as

\[
y_{wrsp}=\theta_w + b_s + b_r + b_p + \varepsilon_{wrsp},
\]

where \(\theta_w\) is the work-associated signal within the feature's stated construct,
\(b_s\) is a provider or imaging-workflow effect, \(b_r\) is reproduction-specific variation,
\(b_p\) is processing variation, and \(\varepsilon\) is residual error. The decomposition is a
study model, not a claim that these components are always additive. Interactions and
heteroscedasticity are estimated where the data support them.

Candidate image coordinates first pass the reproduction model above. They then enter a
cross-classified painter model containing painter, subject/content, genre, medium/support, date,
institution/source, and their justified interactions. A coordinate contributes to a painter
feature only when held-out painter signal remains under the validation protocol's source- and
content-transfer tests.

Any retained coordinate must therefore say which of the following it can describe:

1. the bytes of one digital file;
2. a repeatable property of color-managed digital reproductions;
3. an observable property that is stable enough across reproductions to associate with a
   physical work; or
4. a human-perceived relation under a specified viewing and judgment task.

Ordinary RGB reproductions do not identify pigments, binders, layering, surface topography,
underdrawing, restoration history, or microscopic brushwork. Those require calibrated
spectral, topographic, radiographic, or microscopic evidence and are outside this protocol.

## 2. Construct map for the painter feature

The feature profile is organized by painter-specific questions rather than by algorithms.

| Family | Painter-feature question | Initial status |
|---|---|---|
| Color/luminance | Does a painter show repeatable color and transition distributions beyond subject, period, and capture source? | core candidate, conditional on color/source qualification |
| Spatial structure | Does multiscale contrast/orientation structure generalize across a painter's held-out contents and sources? | core candidate, multiscale only |
| Ordinal complexity | Are local rank-pattern distributions painter-associated rather than codec-, resolution-, or genre-associated? | core candidate, multiscale only |
| Composition | Does coarse spatial organization contribute painter specificity after subject matching? | secondary candidate |
| Learned appearance | Does a frozen mixed visual representation identify held-out painter practice without learning source or content shortcuts? | diagnostic until construct validation |
| Context/semantics | How close are depicted content and contextual concepts in a vision-language model? | separate diagnostic |
| Human-perceived style | Which images are judged similar under a defined task and rater population? | criterion construct, not assumed ground truth |

No family is collapsed into a universal score. A painter feature is a profile or conditional
distribution with coordinate-level uncertainty and a record of which coordinates qualified.

### 2.1 Pilot 2 inheritance and correction

Pilot 2 correctly fixed the artist—not era or movement—as the target; balanced painter by two
sources; fit PCA on real training works only; held out physical works; paired named prompts with
artist-free controls; and defined both target improvement and target-versus-neighbor specificity.
Those principles are retained.

Pilot 2's learned-formal gate is not sufficient for the relaunch. Its pooled four-painter held
balanced accuracy was 0.50, while source balanced accuracy was 0.8125. Training on one source and
testing the other yielded painter balanced accuracy of 0.25 and 0.375. The fitted PCA used 22
components from only 24 training works, and each painter's generated-output target was a centroid
of four held works. Those facts were properly bounded as development evidence, but they show that
the qualified vector could encode source and that the painter reference was too small and too
centroid-dependent for a general painter feature.

The relaunch therefore makes leave-source-out, leave-content-family-out, and reproduction-panel
performance gating rather than descriptive. It models a painter distribution, uses multiple hard
and broad non-targets, and carries uncertainty in the real reference into every later distance.

## 3. Corpus and observation design requirements

### 3.1 Physical-work sampling

The corpus must be sampled from an explicit target population, not collected until a convenient
count is reached. A committed execution protocol must state:

- inclusion and exclusion criteria for physical works;
- collection and provider frames;
- artist-attribution status and uncertainty;
- date or date interval, medium/support, genre/subject, dimensions, and institution when known;
- licensing and redistributability;
- missingness and provider-selection mechanisms; and
- precision or simulation analysis used to choose the number of works per inferential group.

Artist, movement, and period labels are attributed historical metadata, not visually pure
classes. Medium, genre, date, geography, and source must be sampled or modeled so they are not
perfectly aliased with a target label.

Every painter must span more than one eligible source and more than one content or genre stratum.
The design must include overlapping media and dates among comparison painters where historically
defensible. A painter with only one source or one content stratum may be described but cannot enter
confirmatory painter-specificity inference.

### 3.2 Reproduction panel

At least two independently produced reproductions are required for a preregistered subset of
works, with representation across every inferential group and provider. More than one URL for
the same derivative does not count as independent reproduction. The execution protocol must
distinguish:

- independent captures;
- derivatives of the same capture;
- catalog scans;
- screenshots or display-rendered copies; and
- unknown provenance.

Unknown-provenance files may support sensitivity analysis but cannot establish cross-capture
repeatability. The reproduction-panel size is selected by confidence-interval precision for
variance components rather than by an arbitrary percentage alone.

### 3.3 Independence and duplication

The physical work is the highest-level unit. Recto/verso views, tiles, crops, restored
versions, color variants, and resized copies share a derivative-family identifier. No fold or
bootstrap replicate may place related derivatives on both sides of a held-out comparison.
Perceptual hashes are screening aids, followed by manual provenance review; they do not replace
work identifiers.

## 4. Required provenance record

Every file must have a compact manifest row containing, when available:

- study ID, physical-work ID, reproduction ID, derivative-family ID, and provider ID;
- canonical source page and exact asset URL;
- acquisition timestamp, access terms, and HTTP/content metadata;
- original byte hash, byte length, MIME type, codec, bit depth, dimensions, and orientation;
- embedded ICC profile name and hash, EXIF/XMP presence, and alpha channel;
- stated capture workflow, illumination, target, calibration, and pixels-per-unit;
- visible frame, mat, border, watermark, label, crop, stitching, glare, damage, and restoration
  flags;
- metadata values and their source, including uncertainty or conflict; and
- normalized derivative hashes linked to an immutable preprocessing receipt.

No absent ICC profile is silently interpreted as proof that sRGB was intended. A separately
flagged assumed-sRGB derivative may be produced for sensitivity analysis.

## 5. Image-domain branches

### 5.1 Preservation branch

The original acquired bytes and embedded metadata are retained unchanged in the ignored study
workspace. Decoding software and color-management library versions are recorded. This branch is
evidence and is never overwritten by a normalized image.

### 5.2 Color-managed harmonized branch

For files with a valid embedded profile:

1. decode without automatic enhancement, orientation surprises, or display-dependent color;
2. transform through an ICC-aware library using the embedded profile, a fixed rendering intent,
   and a recorded profile-connection space;
3. produce a linear-light working representation for signal measurements and a CIELAB D50
   representation for perceptual color measurements;
4. preserve aspect ratio and the entire confirmed painted field;
5. mask, rather than crop opportunistically, frames, mats, labels, watermarks, and transparent
   padding; and
6. serialize deterministic lossless derivatives with a receipt containing every parameter and
   hash.

Files without usable profiles form a separate provenance stratum. Their assumed-sRGB results
cannot be pooled with color-managed results until cross-source validation supports that choice.

### 5.3 Source-faithful replication branches

Published methods are reproduced with their reported image domain, even when it is scientifically
undesirable, because a replication question differs from a harmonized measurement question.
Forced square resize, grayscale conversion, exact-equality ties, or model-native crops remain
confined to the named replication branch. They are paired with harmonized controls and never
quietly replace the main branch.

### 5.4 Multiscale pyramid

Spatial measurements are evaluated on aspect-preserving, antialiased downsampling levels defined
by painted-field long edge. Only levels at or below the native resolution are used. The default
candidate grid is 2048, 1024, and 512 pixels, subject to qualification and corpus availability;
unsupported levels are missing, not upsampled. Filter choice, boundary mode, linear/perceptual
domain, and mask treatment are part of the feature definition.

Response curves across scale are retained. A coordinate may be reported at a single scale only
after the validation study shows that scale has an interpretable observation domain and an
acceptable error profile.

## 6. Candidate feature cards

These are candidates, not a frozen qualified panel. The validation protocol decides which
survive.

### PF-C1: perceptual color distribution

**Input.** Masked CIELAB D50 harmonized image and provenance stratum.

**Coordinates.** Fixed quantiles of \(L^*\) and \(C^*_{ab}\); circular first and second moments
of hue for pixels above a preregistered low-chroma threshold; and a fixed-bin joint lightness,
chroma, and hue occupancy vector. Bin edges and the threshold are fitted or fixed on development
data and then frozen. Mass in masked pixels is excluded, not coded as black.

**Comparison.** Coordinate differences are reported directly. Distribution comparisons use a
preregistered distance, such as sliced Wasserstein distance, with a real-real reproduction noise
distribution and bootstrap interval.

**Meaning.** Encoded perceptual-color organization of the digital surrogate under the declared
color workflow; after cross-classified validation, it may contribute to a painter-associated
color profile.

**Not meaning.** Pigment palette, original appearance under historical illumination, or physical
color truth when capture calibration is unavailable.

### PF-C2: adjacent chromatic-transition distribution

**Input.** CIELAB image at every supported scale.

**Coordinates.** The complete horizontal and vertical adjacent-pixel color-distance distributions,
their fixed quantiles, direction contrast, and the mean-rescaled distributions used in the Lee et
al. lineage. The source-faithful color-distance formula and seamlessness statistic are retained
separately from any modern \(\Delta E_{00}\) sensitivity variant.

**Controls.** Same-image scale collapse, resampler, JPEG, sharpening, ICC, and direction tests.
If normalization removes resolution effects but also meaningful magnitude, both raw response curves
and normalized shapes are reported.

**Meaning.** Local chromatic transition structure at an observation scale and, only after
content/source transfer, a candidate painter-associated transition profile.

### PF-S1: multiscale spatial-frequency profile

**Input.** Masked linear-light luminance image at supported scales, with a preregistered boundary
window and mask rule.

**Coordinates.** Radially averaged Fourier power by fixed octave bands, robust spectral slope over
a justified frequency interval, horizontal/vertical anisotropy, and residual lack-of-fit to a
single power law. A slope is not reported when the fitted interval fails the preregistered fit
diagnostics.

**Controls.** Crop, border, resize, sharpening, compression, and aspect-ratio perturbations.

**Meaning.** Distribution of luminance contrast energy across spatial scales and directions.

**Not meaning.** Fractality, artistic quality, or brushstroke physics from a fitted slope alone.

### PF-S2: oriented-gradient organization

**Input.** Luminance and, in a sensitivity branch, color-gradient magnitude.

**Coordinates.** Edge density above a development-frozen threshold, first-order orientation
entropy, anisotropy, and PHOG-like cross-scale self-similarity. The pairwise relative-orientation
entropy studied by Redies and colleagues is an optional secondary coordinate with a fixed spatial
sampling rule.

**Controls.** Threshold-response curves, blur/noise, framing, reproduction, and content strata.

**Meaning.** Edge and orientation organization in the digital image. The coordinates are not
automatically equivalent to composition or visual rightness.

### PF-S3: wavelet-energy and texture profile

**Input.** Linear-light luminance at supported scales.

**Coordinates.** Normalized energy and entropy in fixed multiscale, multi-orientation wavelet
bands; cross-scale ratios; and a local-energy distribution. Wavelet family, level, padding, and
normalization are fixed before qualification. Multifractal estimates remain secondary because
their fit ranges and image-size requirements are especially consequential.

**Meaning.** Scale- and orientation-specific texture energy, not direct physical brushstroke
measurement.

### PF-O1: two-by-two ordinal-pattern profile

**Input.** Declared grayscale mapping at every supported scale.

**Coordinates.** The full 75-state two-by-two ordinal-pattern distribution that retains ties,
the corresponding pattern groups, normalized permutation entropy, and statistical complexity.
An exact-tie source branch and a noise-tolerant, preregistered tie branch are compared because
quantization and compression create or destroy equalities.

**Controls.** Grayscale definition, codec, bit depth, downsampling, tie tolerance, image size,
and same-work reproduction.

**Meaning.** Diversity and disequilibrium of very local rank patterns at specified scales.

**Not meaning.** A general measure of creativity, aesthetic complexity, or historical progress.

### PF-M1: coarse composition maps

**Input.** Aspect-preserved painted field.

**Coordinates.** A fixed spatial pyramid of luminance/chroma mass, edge density/orientation,
spectral salience, and segmentation-free center-of-mass/balance summaries. Any learned saliency
map is labeled by model and analyzed separately.

**Status.** Secondary. This family is retained only if it is stable to crop/frame uncertainty
and contributes to human composition or similarity judgments beyond content and source.

### PF-L1: learned appearance descriptors

**Input.** Each encoder's exact, versioned native preprocessing plus an aspect-preserving control
where technically possible.

**Candidate encoders.** Contrastive Style Descriptors (CSD), a frozen self-supervised visual
encoder such as DINOv2, diffusion-feature descriptors, and the Kim et al. A-vector replication.
Every model requires an exact repository revision, weight hash, license, runtime fingerprint, and
reference fixture.

**Coordinates.** Embeddings are not interpreted dimension-by-dimension. Analyses use frozen
distances, work-level prototypes only where sampling supports them, and real-only development
transforms. Raw cosine cutoffs are never borrowed as universal style thresholds.

**Required probes.** Same-work cross-reproduction retrieval; content-matched style retrieval;
style-matched content retrieval; source prediction; medium, genre, artist-name, and date prediction;
synthetic perturbations; nearest-neighbor audit; and expert/nonexpert human alignment.

**Meaning.** Model-dependent learned appearance proximity after qualification. Painter
specificity is assessed against a distribution with uncertainty, not inferred from artist-label
classification or a nearest centroid alone.

### PF-K1 and PF-K2: Kim et al. replication diagnostics

The 2026 Kim et al. paper is treated as a particularly important reference and as a caution
against construct collapse.

- **PF-K1 A-vector:** the reported Stable Diffusion 2.0 autoencoder path uses a forced 512 by 512
  image and produces a 16,384-dimensional latent representation. The released code samples a
  posterior rather than necessarily using its mean. It has a model-initialization defect and lacks
  a complete executable artifact contract. A clean-room repair is an adaptation, not the authors'
  exact realized computation.
- **PF-K2 C-vector:** the contextual path uses a CLIP-family image representation through a
  separate preprocessing path and produces a 1,024-dimensional vector in the audited release.

The A/C terminology is operational, not proof that one vector contains only formal properties
and the other only context. Both models can encode content, period, source, and training-data
associations. PF-K1 and PF-K2 remain diagnostic unless their exact artifacts are recoverable and
they pass the same gates as every other learned descriptor.

### PF-X1: contextual/semantic descriptors

**Input.** Frozen vision-language image encoder and, where used, a separately frozen text-prompt
set.

**Coordinates.** Image-image and image-text similarities for preregistered semantic, genre,
iconographic, and affective concepts. Prompt wording and aggregation are part of the measurement.

**Meaning.** Model-dependent contextual or semantic alignment. These results are never merged
with learned appearance coordinates to imply perceptual style.

## 7. Methods not admitted as RGB painting features

The following are rejected for the ordinary-reproduction protocol:

- pigment, binder, and material identification;
- microscopic brushstroke or impasto topology;
- underdrawing, pentimenti, or layer structure;
- authorship, authenticity, or forgery decisions;
- conservation-state inference beyond visible-file annotations; and
- direct historical influence or causal chronology.

Surface topography, hyperspectral imaging, XRF, OCT, radiography, microscopy, and conservator
examination can support those questions in a different multimodal protocol. Their existence does
not make the claims recoverable from web RGB files.

## 8. Output contract

For every qualified coordinate, an execution report must publish:

1. construct and non-construct statement;
2. exact formula, preprocessing, units, range, and missingness rule;
3. source and model artifact identities;
4. fixture values and repeatability tolerance;
5. perturbation and cross-reproduction error distributions;
6. content/source/medium confounding diagnostics;
7. held-out and human-validation results where required;
8. eligible populations and unsupported domains; and
9. disposition from the shared ledger:
   `qualified_core`, `qualified_domain_limited`, `reproduction_associated`,
   `digital_derivative`, `diagnostic_only`, `replication_only`, `failed`, or
   `not_executed`.

Qualification is version-specific. A model, preprocessing, corpus, or threshold change creates a
new measurement version rather than silently inheriting the old evidence.
