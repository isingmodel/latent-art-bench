# Skeptical methodology review: measurement, constructs and claims

Reviewed 2026-09-07 against commit `744d7f779b0698ed8b9b384157894b341b432ccd`.
This is a maintainer-run LLM subagent review, not independent human or institutional
peer review. Scope: the controlled `painter_distribution_study_v1` study, its
historical rationale, feature implementation, manuscript and proposed human
follow-up. No image was acquired, decoded, remeasured or generated. Existing
numeric features and normalization metadata were read for the two diagnostics
below. Frozen evidence and scientific source were not changed.

## Overall assessment

The work supports a reproducible, finite-panel result about particular image-file
distributions under an explicitly chosen representation. It does not yet identify
loss of painter style, perceptual diversity, a generator's internal concentration
mechanism, or representative failure to reproduce an artist's oeuvre. The paper
usually acknowledges those boundaries. Acknowledging them does not remove the
identification problem, however: the remaining substantive contribution needs
measurement and reference validation, not simply a longer limitations section.

The strongest existing contrast is the effect of adding a painter name to an
otherwise identical detailed prompt on the two paid routes. Keep that contrast
central, subject to the separate statistical review's conclusions. Absolute
original-versus-generated detection is substantially less diagnostic of style.
This review does not dispute that the published numerical values reproduce.

## Prioritized findings

### MC1 — Major: origin and image geometry are completely confounded on paid routes

**Evidence.** `paper.tex:181–190` reports all paid images as 1024-square and variable
OAuth geometry. `features.py:76–81` preserves aspect ratio at a common short side;
`features.py:137–180` includes rectangular-image spectra, orientations and quadrant
statistics. Reading the retained `primary512` normalization metadata establishes
that **zero of 38 Monet and zero of 32 Cézanne references are square**. Every one
of the 576 paid generated images is square. Reference width/height ratios range
0.641–2.021 for Monet and 0.725–1.905 for Cézanne. This result is available from
`data/manifests/painter_distribution_study_v1/pdsv1-main-parallel-20260906/reference_features.jsonl`
and the generated metadata without accessing image pixels.

**Consequence.** A square/non-square metadata rule perfectly separates the paid
generated files from the reference files. Aspect ratio is not explicitly an input
to the reported 31-feature classifier, so this is **not proof that its actual
decisions use shape**. It is decisive evidence that no observed shape overlap can
rule that explanation out. Geometry can change composition and the measurement
domain; resizing the short side and common JPEG encoding do not match it.
Because both paid named and artist-free images are square, this fact alone does
not explain their paired prompt contrast. It primarily undermines interpretation
of the absolute domain separation, with an asymmetric reference target still
present in the prompt energy comparison.

**Revision.** Publish this metadata-only negative control and report descriptor
associations with aspect ratio, native dimensions, encoding/profile metadata and
recorded border status. A future matched-geometry analysis must first establish
common support: an exact-square reference subset is empty here. Symmetric crops
or patches would define a new comparison target and discard composition; they
must be separately labeled sensitivity analyses, not advertised as recovery of
the original estimand. Removing texture coordinates is also not a complete fix.
Regression adjustment cannot establish an original/generated comparison at
matched square geometry when that overlap is absent; any such correction would
depend on extrapolation assumptions, not observed matched controls.

### MC2 — Major: the aggregate metric embeds redundant, unequally weighted visual information

**Evidence.** The representation has 11 color, eight spatial and 12 texture
coordinates (`features.py:17–29`). The included `deltae_slope` is computed from the
three included deltaE measurements (`features.py:121–130`). Included wavelet slope
and curvature are exact functions of the four included wavelet energies
(`features.py:183–208`). The scaler only centers and divides each coordinate by
its development IQR (`painter_feature_generation_v2/statistics.py:27–55`). Energy
uses ordinary Euclidean distances and spread sums squared coordinate deviations
(`painter_distribution_study_v1/statistics.py:45–69`).

**Consequence.** This is a valid prespecified metric, but it is not 31 independent
or equally informative measurements of style. Including a deterministic summary
changes the geometry and adds weight to information already present. Separating
scaler fitting from evaluation prevents leakage; it does not validate that
weighting. A read-only reconstruction from retained primary reference features
and scaler yields the following fractions of original total variance:

| Painter | Color | Spatial | Digital texture |
|---|---:|---:|---:|
| Monet | 27.52% | 23.47% | **49.01%** |
| Cézanne | 25.42% | 27.45% | **47.13%** |

This matters because reported texture contraction is much stronger than spatial
contraction; four detailed named spatial ratios exceed one (`paper.tex:403–408`).
The aggregate result cannot stand for uniform narrowing of visual properties.

**Revision.** Preserve the primary metric. In a newly versioned diagnostic report,
prespecify a small sensitivity set: remove the three derived summary coordinates;
weight each squared coordinate difference by the inverse of its family's
coordinate count, so family contribution is averaged within each family; omit
texture; and show
coordinate and family contributions to trace. Report the development correlation
matrix and uncertainty in scaling using development-only perturbations. Do not
choose a replacement metric because it preserves the headline. A covariance-aware
metric, if added, must use development-only regularization and acknowledge that
it changes the scientific definition of distance.

### MC3 — Major: neither the representation nor the proposed image-level human task validates the distribution-level construct

**Evidence.** The paper correctly says the features are not physical brushstroke
relief or a complete definition of style (`paper.tex:194–200`), and no human or
learned evaluation has been performed (`paper.tex:572–576`). The prepared human
task asks which individual image is closer in style to a displayed reference set
(`HUMAN_FOLLOWUP.md:14–19`); its predictor is a signed image-to-reference distance
(`HUMAN_FOLLOWUP.md:44–47`). It recognizes but does not yet operationalize the need
for a group-level task.

**Consequence.** Mathematical interpretability of descriptors is not construct
validity. An association between individual-image distance and style resemblance
would not establish that total variance measures perceived stylistic diversity,
that nearest-neighbor balls measure coverage of an oeuvre, or that increased
detectability represents worse imitation. One learned embedding would provide a
second measurement, not a ground-truth style instrument.

**Revision.** Define at least two separate human constructs before recruitment:
(1) resemblance to a displayed painter reference set and (2) within-set variation
or reference-set coverage. For the second, compare equal-sized sets balanced for
the same briefs, with multiple independently allocated sets and reference panels,
rather than treating many ratings of one pair of montages as independent stimuli.
Separate style, subject diversity, image quality and authenticity questions;
retain ties/uncertainty. Pilot task comprehension, then fix the estimand, stimulus
inventory, smallest relevant association and crossed-rater/stimulus analysis.
The present 24–36-rater/40-trial suggestion is a feasibility target, not a power
justification. If human results disagree with the features, report that as a
measurement finding and narrow the style interpretation.

### MC4 — Major: the remaining content and capture paths are alternatives to the intended style interpretation

**Evidence.** The main contract states that originals differ in subjects,
seasons and viewpoints and that adherence is not established (`MAIN.md:26–32`).
Generated content classes are copied from the brief (`study.py:95–107`), while
reference classes come from one maintainer LLM. The paper explicitly weights
intended generated content (`paper.tex:250–255`). Independent photographic capture
pairs are absent (`paper.tex:150–159`). Four retained references have recorded
dark perimeters, while every prompt requests no frame, signature, letters or
watermark (`MAIN.md:9–14,35–39` and the retained reference annotations).

The four border-flagged work IDs are `Q66126523`, `Q20538824`, `Q20538849` and
`Q64212455`. The native-1024 filter uses the expected **parent-surrogate**
dimensions (`study.py:125–127`). The delivery builder preserves candidate
`expected_width`/`expected_height` and records distinct `delivery_width` and
`delivery_height` fields (`reference_delivery.py:52–58,82–91`). The parent-size
filter retains four Monet and 19 Cézanne works; applying the threshold to actual
delivered dimensions instead would retain four and 18. Neither quantity
establishes independent capture-master quality. The four retained Monet works
are two water and two land scenes, with no built scene, so this sensitivity also
removes an entire content class and changes the target support.

**Consequence.** Three class masses do not equalize actual scene content or
composition. A name could change adherence, viewpoint or depicted objects and
thereby change low-level features. This remains part of the total prompt effect;
conditioning on post-treatment adherence would not isolate a pure style effect
automatically. Real reproductions also contain acquisition history absent from
synthetic outputs. More references from the same confounded source may amplify
precision without resolving validity.

**Revision.** Independently annotate an outcome-blinded, ID-selected sample of
existing generated and original images for content, composition and nuisance
attributes. Report adherence as an outcome, not an eligibility filter that
silently removes unfavorable results. Use labels to describe content shifts and
common support; any conditional comparisons are a separately justified estimand.
Audit reference source and physical-work metadata before committing to a larger
panel. Capture controls require demonstrated distinct capture events; JPEG
re-encoding or alternate thumbnails of one photograph are not such events.

### MC5 — Major for interpretation: total spread does not locate the contraction

**Evidence.** Generated images arise from three repetitions of only 24 fixed
briefs (`paper.tex:131–138`), with variation summarized across the combined
collection (`statistics.py:54–59`). The discussion suggests narrowing of the
model's output distribution but correctly says no internal mechanism is
identified (`paper.tex:541–546`).

**Consequence.** Lower total trace can result from smaller differences between
brief-specific means, lower variation within the same brief, or both. Those
possibilities correspond to different scientific stories. It also compares a
fixed, deliberately bounded prompt library to paintings produced across many
contexts. Moreover, energy and spread are not independent validations: energy
already contains a within-generated pairwise-distance term.

**Revision.** Using existing vectors, decompose weighted generated trace into
between-brief and within-brief components, and also show within/between coarse
content components for both domains. Retain finite-library interpretation and
three-repetition uncertainty. Decompose prompt energy changes into cross-domain
and within-generated terms. Do not infer a latent mechanism from either
decomposition; it identifies where measured variation changes. Treat the
proximity/spread relationship as the joint behavior of related statistics.

### MC6 — Important: neighborhood coverage and two-painter specificity are descriptive operating points

**Evidence.** Coverage uses each reference's third nearest distinct work and
100 generated subsamples (`paper.tex:274–282`). Specificity compares each named
collection with only two reference painters (`paper.tex:507–512`). The same
finite low-level representation underlies energy, coverage, detection and PCA.

**Consequence.** With only 32/38 references, neighborhoods can be broad and
irregular; a few central synthetic images can cover multiple balls. High coverage
with contraction need not mean successful recovery of rare painter attributes.
Own-versus-one-other distance can reflect source, content or collection properties
and is not multiartist recognition. Multiple metrics on the same representation
are complementary summaries, not independent confirmation of painter style.

**Revision.** Show the already available radius distribution and a small
prespecified k sensitivity (for example 1, 3 and 5), sample-size coverage curves,
and per-reference coverage with source/content labels. Treat these as diagnostic
operating points, not a search for the best coverage number. If claiming painter
specificity, require a reference-only discrimination control with genuinely
independent work/source splits and additional negative painter references in a
separately scoped extension; otherwise retain the literal two-reference result.

### MC7 — Important: the novelty comparison omits directly adjacent work

**Evidence.** The manuscript contrasts mainly quantitative art history, Kim 2026
and Asperti's 2026 CLIP preprint (`paper.tex:64–89`); neither AI-Pastiche's style
replication study nor AI-WikiArt's attribution study appears in `references.bib`.
Primary-source checks during this review establish relevant nearby work:

- Asperti et al.'s [AI-Pastiche style-replication study](https://arxiv.org/abs/2502.15856)
  evaluates generated artistic imitation with user judgments of authenticity,
  adherence and defects. Therefore cross-model style evaluation with human
  responses is already an occupied contribution category.
- Fu et al.'s [AI-WikiArt attribution study](https://arxiv.org/abs/2508.01408)
  examines painter attribution and generated-image detection with approximately
  40,000 real paintings from 128 artists. It is a relevant comparison for painter
  specificity and dataset breadth, even though its main target differs.
- Asperti's [2026 preprint](https://arxiv.org/html/2608.25609v1) investigates
  human/generated separation, processing controls, interpretable multiscale
  structure and low-salience perturbations. The present paper appropriately
  acknowledges that scatter separation alone is not new.

Kim's [2026 bibliographic record](https://pubmed.ncbi.nlm.nih.gov/42497200/) was
verified. The publisher returned 403 and PMC presented a browser challenge in
this review, so this review does not claim a fresh full-text reappraisal of Kim's
methods or supplement. The manuscript's distinction from an art-evolution study
is plausible; it is not sufficient on its own to establish novelty here.

**Revision.** Add a concise contribution matrix covering task, sample unit,
prompt intervention, reference controls, representation, human validation and
release accessibility. State the potential new contribution as a controlled
prompt-conditioned proximity/variation result with measured boundary conditions.
Do not claim the first AI-versus-painting distribution separation, first painter
imitation benchmark or a new general style metric.

### MC8 — Important: publication readiness depends on scientific and external reproducibility, not the test count

**Evidence.** The abstract emphasizes replay completeness and cost
(`paper.tex:36–37`), while raw images remain only in ignored local evidence and
cannot be reconstructed by a Git checkout (`paper.tex:565–570`). Model snapshots
are not attested (`paper.tex:557–563`). Historical outcomes informed painter
selection (`paper.tex:124–129`).

**Consequence.** Extensive tests and hashes give valuable computational assurance;
they do not establish source validity, measurement validity, external access or
generality. Two selected painters across one set of live services support a case
study. Increasing the number of files or documenting transport in greater detail
does not itself convert that into a general AI benchmark.

**Revision.** Keep acquisition/retry accounting reproducible but move incidental
transport detail out of the scientific foreground. Prepare a rights-reviewed,
stable artifact package or explicitly documented access mechanism for all bytes
needed to verify the core measurements. State separately what can be reproduced
from public numeric data, retained images, and unavailable model state. For an
empirical journal, prioritize validated interpretation and reference robustness.
A stronger AI main-conference claim would additionally need a generalizable
evaluation contribution or broader independent replication, not only SOTA model
names. A humanities venue would require an explicit art-historical argument and
domain collaboration rather than adding that framing after the analysis.

## Recommended revision package and decision gates

1. **No-generation diagnostic package first.** Freeze a new numeric-only scope
   for metadata negative controls, metric-weight sensitivities, variance/energy
   decomposition, reference influence and coverage operating points. Preserve
   the published primary bundle. All revised interpretations must report
   contradictions and state that these are post-result diagnostics.
   Keep this a bounded diagnostic set, not a Cartesian product of every feature,
   source, content and processing option. No observed sensitivity may be promoted
   to a replacement confirmatory endpoint because it yields a favorable result.
2. **Make scientific alternatives visible.** Add a diagram or table distinguishing
   intended name intervention, actual depicted content, service rendering,
   source/capture, geometry and measured features. Audit whether the strongest
   paid-route signal remains meaningful under plausible metric definitions.
   If it does not, revise the main result to metric sensitivity rather than
   selecting a favorable representation.
3. **Specify human set-level validation before recruiting.** Complete the
   image-level and set-level stimulus designs; use a feasibility pilot only to
   establish comprehension/burden, then determine final precision or power using
   crossed stimulus/rater effects. All stimuli can come from existing outputs.
4. **Determine original-data needs from common support, not a round number.** A
   new panel should be selected for source provenance, painter-period/content
   coverage and geometry/capture overlap under a declared target. If the same
   source imbalance persists, simply adding 80–120 works is not a sufficient
   revision. Distinct captures are a separate data type and do not increase work N.
5. **Use one complementary learned representation only after its scope is fixed.**
   It can operate on existing images without generation calls. Specify model,
   layer, processing and similarity before viewing its comparative outcomes;
   test human agreement instead of calling the embedding a style gold standard.
6. **Choose final claim and venue after the first two validation results.** If
   only file-level separation is robust, publish that narrower measurement case
   study. If name-induced proximity and perceptual set variation agree after
   reference controls, pursue the stronger computational-art interpretation.
   Do not make acceptance or generalization claims from the present evidence.

## Local evidence path key

All line references above are against the reviewed commit. Shorthand paths:

- `paper.tex`: `papers/painter_distribution_study_v1/paper.tex`
- `references.bib`: `papers/painter_distribution_study_v1/references.bib`
- `features.py`: `src/latent_art_bench/painter_feature_generation_v2/features.py`
- `statistics.py` unless otherwise qualified:
  `src/latent_art_bench/painter_distribution_study_v1/statistics.py`
- `study.py`: `src/latent_art_bench/painter_distribution_study_v1/study.py`
- `reference_delivery.py`:
  `src/latent_art_bench/painter_distribution_study_v1/reference_delivery.py`
- `MAIN.md`, `REFERENCES.md`, `HUMAN_FOLLOWUP.md`:
  `studies/painter_distribution_study_v1/`

The trace-fraction calculation uses `numpy.var(z, axis=0)` with population
denominators, `z=(values-center)/scale`, the retained `primary512` reference rows,
and `pdsv1-main-20260906/scalers.json`. Family fractions sum each coordinate block
and divide by the full trace. This is a read-only descriptive review diagnostic,
not an additional frozen inferential result.
