# Literature-search protocol and retrospective audit specification

Protocol version: `painter-feature-review/1.2`

Review snapshot date: 2026-09-01

## Registration status and evidentiary boundary

This document was assembled during the relaunch after legacy references and some anchor-source
checking were already available. There is no timestamped immutable registration demonstrating
that version 1.1 preceded every query, screening decision, eligibility decision, or stopping
decision in the completed review. The clusters, eligibility rules, extraction fields, grades,
and stopping heuristic below are therefore a **retrospective structured audit specification** for
the 2026-09-01 review snapshot, not a preregistered systematic-review protocol.

The specification is useful for making current judgments explicit and for auditing consistency.
It cannot support claims that reviewer discretion was eliminated prospectively. A future update
may use it prospectively only after committing a new version before searching and retaining the
query exports, result manifests, deduplication decisions, screening decisions, and exclusion
reasons needed to verify that use.

## Review questions

1. Which computable image measurements have been used to describe color, texture, marks,
   edges, composition, complexity, formal appearance, or context in paintings, and which retain
   painter-associated signal across held-out works?
2. What preprocessing, image-size, color-space, crop, frame, codec, and digitization choices
   define each measurement's actual input domain?
3. Has the measurement been functionally replicated, tested on held-out works, compared across
   independent digitizations, or validated against human judgments or material evidence?
4. Which methods distinguish fidelity, specificity, diversity, coverage, and memorization in
   generated-image distributions?
5. What claims are unsupported even when a feature predicts painter, period, or movement?
6. Which designs distinguish a painter feature from source, subject, genre, medium, chronology,
   artist-name, and training-set shortcuts?

## Source discovery

The completed review used OpenAlex/Crossref metadata, PubMed/PMC, arXiv, CVF Open Access, PMLR,
publisher pages, and exact public source repositories. It combined keyword search with backward
and forward citation chasing from the following anchors:

- Kim, Son, and Jeong (2014), large-scale quantitative painting analysis;
- Lee et al. (2018), chromatic-distance heterogeneity;
- Sigaki, Perc, and Ribeiro (2018), entropy and statistical complexity;
- Lee et al. (2020), information-theoretic landscape composition;
- Kim et al. (2026), Stable-Diffusion A-vectors and CLIP C-vectors;
- Gatys, Ecker, and Bethge (2016), neural style representations;
- Somepalli et al. (2024), contrastive style descriptors; and
- Naeem et al. (2020), generative fidelity and diversity metrics.

The synthesis was organized into the following search clusters. These clusters were formalized
during the review and must not be described as having been fixed before all completed screening:

| Cluster | Representative terms |
|---|---|
| Quantitative art history | painting, computational art history, color, chromatic distance, palette, brushstroke, texture, edge orientation, spatial frequency, composition, saliency, fractal, entropy, complexity |
| Learned representation | painting embedding, artist attribution, style classification, art representation, autoencoder, CLIP, DINO, self-supervised, content-style disentanglement |
| Generative evaluation | artist imitation, style similarity, style transfer metric, FID, KID, precision recall, density coverage, memorization, copying, prompt artist |
| Measurement validity | digitization, reproduction, color management, ICC profile, resolution, resampling, JPEG, domain shift, museum source, robustness, repeatability |
| Human and construct validity | art expertise, style perception, similarity judgment, aesthetic statistics, human alignment, psychometrics, construct validity |

`SEARCH_LOG.md` records the query strings or grouped traversals that could be reconstructed, their
session date, and how results were handled. It is not an export-backed query-by-query ledger:
several interfaces did not expose stable totals, and no complete result-page or screening manifest
was saved. Search results are not evidence by themselves; bibliographic and method claims must
resolve to a primary paper, supplement, dataset paper, or exact source repository.

## Eligibility

Include a source when it contributes at least one of the following:

- a defined image-level or set-level feature relevant to paintings;
- an empirical validation or failure analysis of such a feature;
- a painting corpus or annotation design that changes measurement validity;
- a primary method for distributional fidelity, diversity, or two-sample comparison;
- a primary study of digitization, source-domain, human-perception, leakage, or confounding
  relevant to interpreting painting features.

Reviews and surveys may support discovery and terminology, but they cannot be the sole evidence
for a retained measurement. Material-analysis methods using spectroscopy, topography, X-ray,
or microscopy are contextual comparators unless the relaunch has that modality; they must not
be represented as obtainable from ordinary RGB museum reproductions.

Exclude or mark `background_only` when a source:

- offers no reproducible method or empirical evidence relevant to the review questions;
- evaluates only visual appeal without a separable painting-feature construct;
- reports only training accuracy, an unheld visualization, or a convenience split vulnerable
  to work, artist, source, or near-duplicate leakage;
- conflates semantic content, artist identity, style label, authenticity, and quality;
- cannot be bibliographically verified; or
- is superseded by a version of record, in which case the earlier version remains a provenance
  link rather than a separate study.

Language is not an exclusion criterion when an English abstract and interpretable method are
available. Publication venue is not an automatic quality score; evidence is graded from the
actual design.

## Current matrix and uninstantiated detailed extraction schema

The current 138-row matrix records only 11 fields: ID, year, short citation, stable identifier,
cluster, review depth, main evidence, central limit, evidence grade, disposition, and protocol
consequence. The thematic reviews provide richer method detail for selected decision-relevant
sources, but the project did **not** create a 138-record evidence-card artifact containing every
field below. It therefore cannot claim that every retained source received a complete detailed
extraction. This is a current audit limitation, not a field silently stored elsewhere.

For a future prospectively registered update, every newly retained source must receive a saved
record-level evidence card containing:

- stable identifier, citation, year, and version reviewed;
- review depth: `full_text`, `methods_and_results`, `abstract_only`, or `metadata_only`;
- construct family and intended claim;
- input modality, corpus, independent-work count, and grouping structure;
- exact preprocessing and feature definition where reported;
- fitting, dimensionality reduction, classifier, or distance rule;
- validation design, held-out unit, uncertainty, and human comparison;
- digitization, content, source, training-data, and label confounds;
- availability of code, data, checkpoints, and reference fixtures;
- reproducibility and external-validity judgment;
- protocol disposition: `core_candidate`, `secondary_candidate`, `diagnostic_only`,
  `background_only`, or `reject`; and
- rationale and concrete protocol consequence.

Unreported details in those future cards must be recorded as unreported, not inferred. Until such
cards exist for the current 138 sources, the 11-column matrix and the cited thematic-review tables
are the complete auditable extraction artifacts.

## Evidence grades

Grades describe support for this project's measurement use, not the overall quality of a paper.

| Grade | Minimum interpretation |
|---|---|
| A | Explicit construct, reproducible method, independent held-out validation, relevant robustness or external validation, and uncertainty appropriate to the sampling unit |
| B | Clear method with useful held-out or perturbation evidence, but one important validity dimension remains unresolved |
| C | Defined and potentially useful measurement with limited validation, convenience sampling, or substantial untested confounding |
| D | Background or hypothesis-generating evidence only; cannot qualify a measurement |
| X | Rejected for this protocol because the method, provenance, or validation cannot support the proposed use |

No paper alone can qualify a core feature. Qualification requires converging source evidence and
a prospective local validation battery.

## Synthesis rules

- Separate properties of a physical painting from properties of one digital surrogate.
- Separate formal appearance from semantic/contextual content; acknowledge overlap rather than
  forcing a false binary.
- Treat artist and movement labels as attributed, historically contingent grouping variables.
- Treat classification as a sensitivity test for group signal, not construct validity.
- Fit transforms and tune thresholds on real development data only.
- Require work-level, source-level, prompt-level, and generator-level independence where each is
  the relevant sampling unit.
- Report feature profiles and uncertainty; do not select a single scalar after viewing results.
- Record negative and null findings, inaccessible details, and incompatible input domains.

## Retrospective stopping assessment and future rule

For the completed snapshot, the team stopped after a final cross-cluster pass yielded four records
that were retained as decision-relevant and did not add a new method family. Four is 2.9% of the
final 138-row evidence matrix. That calculation is a retrospective description, not proof that a
less-than-10% stopping rule was prespecified or independently satisfied: the rule was not
demonstrably registered before searching, the pre-pass eligible set was not frozen independently,
and the returned-result and screening manifests were not retained. The review therefore claims
broad structured coverage, not saturation or exhaustiveness.

For a future update, a prospective stopping rule may be activated only by committing a new
protocol version before the first new query. Each cluster must then have anchor-paper backward
chaining and at least two separately logged forward/keyword passes; every pass must retain an
export or result manifest and screening disposition. A final pass may stop the update if it adds
less than 10% new decision-relevant sources relative to the evidence set frozen before that pass
and adds no new method family. The report must state reconstructable screened and included counts
and must not call an open literature exhaustive.
