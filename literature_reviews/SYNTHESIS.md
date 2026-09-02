# Evidence synthesis for generated-versus-real painter features

Version: 2.0
Aligned protocol: `painter-feature-generation-v1/2.0`

## 1. Bottom line

The literature does not provide a validated scalar that answers whether a generative model
reproduces a painter. It provides components:

- interpretable measurements of color, spatial frequency, orientation, self-similarity, and texture;
- learned representations that carry artist/style associations but also content, source, chronology,
  and training-data signals;
- two-sample distances and support diagnostics for generated distributions;
- evidence that image source, crop, color management, and duplicate works can dominate results; and
- strong reasons to separate absolute fit, specificity, prompt movement, coverage, copying,
  adherence, and availability.

The defensible research object is therefore a **distribution across physical works in a stated
digital-surrogate and content frame**. For Protocol 2.0, the exact construct is broad-scene-weighted
digital-surrogate feature reproduction. The project does not claim a content-free essence, physical
brushwork, authenticity, or a probability-sampled oeuvre.

## 2. Correct research question

The target is not:

- “Can a classifier tell Monet from Sisley?”
- “Does the painter name move CLIP/CSD in the expected direction?”
- “Is the generated centroid close to a real centroid?”
- “Does one evaluator assign a high style score?”

The target is:

> For one frozen model and one pre-label common prompt census, does each painter-name condition
> reproduce the corresponding real finite distribution of prequalified feature families, while
> remaining absolutely close, painter-specific, better than an artist-free control, adequately
> dispersed, complete, adherent, and not copied from the searched reference corpus?

This framing follows the most important lesson from the historical painter-label work: label signal
is necessary evidence that a coordinate can respond to painter-associated variation, but it is not
sufficient evidence of painter-feature reproduction.

## 3. Interpretable feature evidence

### 3.1 Color organization

Kim, Son, and Jeong (2014), Lee et al. (2018), Montagner et al. (2016), and related work show that
painting corpora differ in color distributions and spatial chromatic relationships. The useful
lesson is not that a mean hue defines an artist. It is that color should be measured as a structured
distribution:

- robust luminance and chroma location/spread;
- circular hue concentration and entropy;
- chromatic-pixel fraction; and
- multiscale CIEDE2000 distance across spatial lags.

These coordinates remain sensitive to capture, color profile, compression, varnish/age, and source
workflow. They require ICC/source sensitivity and independent-capture qualification.

### 3.2 Spatial/orientation organization

Graham and Field, Koch et al., Redies and colleagues, and PHOG studies support Fourier slope,
spectral anisotropy, gradient-orientation entropy, horizontal/vertical balance, and spatial
self-similarity as interpretable image statistics. Their limits are equally important:

- framing and crop change Fourier and composition measurements;
- depicted architecture, horizon, trees, and water affect orientation statistics;
- square warping can manufacture regularity; and
- one spectrum exponent is not a painter signature.

Protocol 2.0 therefore preserves aspect ratio, excludes frame-dominant assets, fixes one normalized
short side, uses a common scene frame, and treats the full family jointly.

### 3.3 Digital texture organization

Wavelet, sparse-coding, texton, and multifractal studies show that local/multiscale image structure
can distinguish some artist corpora. Ordinary catalogue RGB cannot establish physical brushstroke,
impasto, pigment, binder, or surface topography. The proper label is digital texture organization.
Stationary-wavelet energy, scale slope/curvature, rotation-invariant LBP entropy, and multiscale local
variation are plausible candidates only after crop/resampling and same-work capture tests.

### 3.4 Why all three families are required

Color alone can pass because of reproduction/source palettes. Spatial statistics can pass because
of subject matter and framing. Texture can pass because of resolution/compression. Requiring all
three does not remove confounding, but it prevents a favourable single family from defining the
answer. Protocol 2.0 stops before generation if any prespecified family fails qualification.

## 4. Kim et al. and learned representations

Kim et al. (2026) analyze 72,447 paintings by 2,354 painters across 128 style periods and 1500–1990.
Their A-vector is a flattened 16,384-dimensional Stable Diffusion 2 first-stage VAE latent; their
C-vector is a 1,024-dimensional LAION-CLIP image representation. The paper is valuable evidence that
large pretrained representations contain chronology, painter-label, and style-period signal.

It does not validate the present endpoint:

- A retains content, layout, color, codec/resizing, source, VAE-training, and posterior-sampling
  effects;
- C retains semantics, iconography, web text associations, chronology, source, and possible exact-
  work training exposure;
- A and C use different models and preprocessing, so their contrast is not a controlled form/context
  decomposition;
- within-label closeness and classification do not measure coverage of a painter's work distribution;
  and
- the released A implementation/artifacts do not support exact replication without repairs.

The exact released code commit is recorded in the Kim review. Protocol 2.0 uses Kim A/C as named
diagnostics only. A diagnostic can reveal evaluator dependence; it cannot rescue a failed
interpretable family.

CSD, ALADIN, GOYA, ArtFID, and related work similarly demonstrate useful style-associated spaces and
content/style objectives. Their artist tags, web corpora, generative teachers, checkpoints, and
human-task definitions limit construct claims. CSD in particular is trained from caption-derived
artist/medium/movement labels and its repository reports a checkpoint/result discrepancy. Raw cosine
similarity is not calibrated painter fidelity.

## 5. Corpus and digitization evidence

### 5.1 Physical work, capture, asset, and file are different units

The same painting may appear through a museum master, Commons mirror, thumbnail, crop, re-encoding,
book scan, or alternate capture. Exact hashes detect identical bytes, not identical physical works.
Perceptual hashes flag review candidates but cannot establish identity alone. Protocol 2.0 therefore
uses:

```text
source row
  -> authority object/accession
  -> physical_work_id
  -> capture/master family
  -> provider asset
  -> delivered file
```

Only the physical work counts. A second capture enters the auxiliary disturbance panel only when its
provenance demonstrates a distinct digitization event.

### 5.2 Authority, discovery, and media layers

Wikidata/Commons and Europeana are efficient discovery/crosswalk layers. They do not independently
establish exact attribution, support/medium, or the authority of a physical object. Official museum
and catalogue records supply authority. Official or Commons assets can supply lawful media when
their item-level rights and technical receipts pass.

Source counts cannot simply be added: one work may occur in a museum API, POP/Europeana, Wikidata,
and Commons. The relevant capacity quantity is the deduplicated authority-backed physical-work
union after rights, quality, content, exposure, and auxiliary reservation.

### 5.3 Why the equal 360 quota was rejected

No reviewed paper supplies a universal 360-work requirement for painter-feature distribution
comparison. The value was a reverse-engineered capacity target from a previous three-way role split,
not an effect-size, precision, or power result. A complete finite real frame does not require equal
painter counts: its real self/cross terms can be calculated exactly at the actual count.

Equalizing counts can make the design worse by adding weak-provenance candidates for a scarce
painter or discarding lawful works for an abundant painter. Protocol 2.0 exhausts the source union,
keeps every eligible work, and decides adequacy from common-scene support, effective weight,
source/capture crossing, influence, and whole-decision simulation.

### 5.4 Source is a claim boundary, not a cosmetic quota

Historical results showed high source predictability and poor opposite-source transfer. Source
dominance cannot be fixed merely by deleting works until a percentage looks balanced. Protocol 2.0
requires a connected painter × authority/capture-workflow graph, at least two workflows per painter,
cross-painter overlap, and a maximum workflow mass. Supported leave-workflow results must preserve
the final decision. Otherwise no painter-reproduction label is allowed.

## 6. Content control and prompt design

Painter and content are entangled in real art. Exact content matching can erase genuine practice or
create sparse cells; ignoring content lets objects and scene types dominate. Protocol 2.0 uses a
middle position:

- one outdoor-place domain;
- four broad visible scene groups;
- deterministic retention of every group with at least 20 confirmation works for every painter;
- equal group mass and uniform works within group;
- 16 exact prompt strings frozen before active labels; and
- season, illumination, depth, and per-scene results as binding diagnostics/sensitivities.

This design does not isolate painterly form. Residual detailed content and period remain in the
estimand. An off-topic generated image stays in its assigned scene cell, because filtering it out
would select the answer. Adherent-only analysis is explicitly secondary.

## 7. Distribution metrics and decision logic

### 7.1 Why energy distance is primary

Energy distance is zero only for equal distributions under its standard finite-moment conditions
and can be estimated directly in low-dimensional common-scaled feature families. Protocol 2.0 uses:

- the exact complete-real self term;
- the exact real–generated cross sum for observed generator draws;
- a generated U term across different seed blocks; and
- equal averaging across the retained scene groups.

Real works are not bootstrapped because the target is the observed finite population. Generator
uncertainty resamples complete seed/common-shock blocks while the real census and prompt census stay
fixed.

### 7.2 Why FID and neighbourhood metrics are secondary

FID compresses each distribution to a Gaussian mean/covariance in a chosen encoder and has
finite-sample bias. KID changes the estimator but not encoder/construct dependence. Improved
precision/recall, density/coverage, and related nearest-neighbour measures depend on dimension,
sample size, neighbourhood choice, hubness, and outliers. They are useful diagnostics, not universal
painter-fidelity gates.

### 7.3 A positive result is conjunctive

For every painter and every primary family, Protocol 2.0 requires:

1. absolute energy-distance equivalence under a pre-confirmation margin;
2. superiority to every wrong-painter real target;
3. improvement over the matched artist-free control;
4. simultaneous coordinate median/IQR coverage;
5. per-scene coverage;
6. leave-one-work and leave-workflow robustness;
7. complete technical output, adequate adherence, and zero confirmed searched-corpus real copies.

All three families and all four painters must pass for the panel statement. There is no average score
that cancels a failure.

### 7.4 Margins and generation count

No literature-claimed universal equivalence margin exists. Protocol 2.0 fixes each family margin
from new-development split stability and an independent-capture tolerance bound, then
requires that margin to remain below half the nearest wrong-painter qualification separation. The
margin is frozen before the untouched qualification gate and cannot be widened using confirmation or
generated outcomes.

Only after margins are fixed does a whole-decision simulation choose the smallest
`R` in `{25,50,75,100}`. Favourable and adverse DGPs include matching-painter resampling, wrong
painter, pooled control, central-mode/dispersion collapse, coordinate shift, and source disturbance.
If none passes the registered operating criteria, generation stops.

## 8. Missingness, copying, and dependence

Historical generation showed that refusals can leave requested-label cells incomplete. An
adherent/successful subset is not automatically representative. Protocol 2.0 chooses a strict and
simple positive-claim rule: the entire registered grid must be present, decodable, and analyzable.
Incomplete runs are reported but cannot receive a conditional reproduction label.

Copy detection searches every lawfully acquired development, qualification, auxiliary, and
confirmation work with exact hashes and a locally calibrated whole/crop detector. Confirmed real-
work copying fails the positive claim. This is only a searched-corpus statement; opaque training
copy from an unavailable work cannot be ruled out. Generated-to-generated duplicates remain in the
distribution and penalize coverage.

Paired seeds create dependence across named/control conditions. Remote systems may add batch,
backend, moderation, or outage dependence. Local inference resamples complete repetition blocks.
Remote execution uses complete balanced waves; partial-wave changes or fewer than 25 defensible
blocks make inference inconclusive.

## 9. Human coding

Visible outdoor eligibility and scene group cannot be established reliably from titles alone. Two
coders therefore view masked 512-pixel derivatives, with painter, title, institution, accession, and
source hidden. Raw streams and per-painter reliability receipts are sealed before a third coder
adjudicates. Missing/ambiguous and union-eligible denominators remain visible. Generated images use
condition-scoped receipts. Consensus cannot retroactively repair poor agreement.

Human preference or “looks like Monet” ratings are not primary. Such ratings conflate familiarity,
content, labels, and stereotypes unless separately validated with crossed works/raters and blinded
tasks.

## 10. Current evidence boundary

The committed material-constrained exploratory seed contains 3,190 Wikidata item identifiers and
3,364 Commons filenames. The earlier small Commons follow-up terminated with HTTP 429 and supports
no current rights/resolution/quality yield. A separate 43-record official-source artifact is
traceable all-content live-item evidence, not a terminal source census. Active admissions,
downloads, confirmation works, generation attempts, outputs, and results are all zero.

The fixed-seed metadata audit can quantify current P18 linkage, rights markers, reported geometry,
and delivery metadata for that seed only. It cannot establish the complete no-material-field source
frame, authority, outdoor eligibility, physical-work identity, active admission, or image quality by
visual inspection.

## 11. Recommended sequence

1. Independently review and execute the metadata-only fixed-seed audit.
2. Freeze and exhaust the broader closed source registry without `P186` count stopping.
3. Resolve authority, rights, physical works, capture ancestry, and lawful image acquisition.
4. Double-code masked content eligibility and close the unequal finite frames.
5. Freeze the prospectively assigned development/qualification roles and the independent-capture panel.
6. Implement and qualify all three primary families; freeze margins and simulation results.
7. Freeze one model, exact retained prompt census, seeds, `R`, request order, and analysis.
8. Generate while confirmation-resolution data remain inaccessible.
9. Open the reference once and run the frozen conjunctive decision.

## 12. Evidence-based conclusion

The literature supports a rigorous experiment, not a present claim that a model reproduces a
painter. The decisive risks are source/capture confounding, residual content, work/file duplicates,
measurement instability, missing generated outputs, evaluator dependence, mode contraction, and
copying. Protocol 2.0 makes those risks explicit and often fail-closed. If that makes the study hard
to pass, that is preferable to answering an easier classifier or centroid question while calling it
painter-feature reproduction.
