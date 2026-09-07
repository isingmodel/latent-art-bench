# Data, design, generation and provenance review

Review date: 2026-09-07. Scope: the completed `painter_distribution_study_v1`,
with historical evidence examined where it determines exposure or selection.
This is a maintainer-run LLM subagent review, not institutionally independent
review or expert art authentication. The reviewed baseline was clean commit
`744d7f779b0698ed8b9b384157894b341b432ccd`.

## Verdict

The records support a reproducible comparison of these collected digital files
and a prospectively assigned prompt intervention. They do **not** identify how
closely the models reproduce a painter's style independently of subject,
digitization and service behavior. The major weaknesses are selection and
measurement validity, rather than demonstrated corruption of the collection.
Disclosure of these weaknesses does not remove them.

Priority 1 means a blocker for a broad style-reproduction claim; priority 2 means
a material limitation or revision needed for a narrower empirical paper. No
claim of data fabrication, retrospective favorable-image selection or observed
exposure leakage was established in this audit.

## Findings and repairs

### D1 — Priority 1: the reference distribution is an availability-selected residual panel

**Confirmed.** The screen explicitly removes the previous 1,193-work frame and
recorded exposure identities, then samples from remaining metadata and further
filters on supported Wikimedia thumbnail delivery. The reference contract itself
explains that many new candidates were absent from the earlier frame because of
its 1,024-pixel threshold or title rules. The surviving panel consequently is not
a random fresh sample from the same population as the historical originals.
It is also restricted to outdoor oil-on-canvas works by two painters selected
after the historical results were known.

Evidence: `studies/painter_distribution_study_v1/REFERENCES.md:11–37,39–71`;
`studies/painter_distribution_study_v1/REFERENCE_DELIVERY_R2.md:20–39`;
`src/latent_art_bench/painter_distribution_study_v1/references.py:171–229`;
`papers/painter_distribution_study_v1/paper.tex:123–159`.

Metadata-only diagnostics show the median parent-surrogate short side is 826.5
pixels for Monet and 1,299.5 for Cézanne. Only 4/38 Monet parent surrogates satisfy
the old 1,024 threshold, against 19/32 Cézanne. This establishes selection-related
resolution imbalance; it does not establish that resolution caused the observed
feature differences. Source/capture confounding and its effect size remain
unresolved.

**Affected claims:** representative within-painter distributions; replication on
an exchangeable independent reference sample; general conclusions about painter
style or all model generations. Historical-versus-new effect changes cannot be
attributed solely to new model families.

**Repair with existing evidence:** describe the target as the finite eligible
outdoor-painting digital-surrogate panel. Add a selection-flow and source/geometry
table; keep historical and fresh-reference analyses separate. A separately
versioned sensitivity using exposed historical references is informative if
explicitly labeled exposed, not a new holdout.

**New data needed for broader claims:** an externally defined source frame,
verified work identities and a prospectively sampled validation panel with
documented content/source support. Choose sample allocation after a feasibility
audit; an arbitrary top-up count does not resolve this selection mechanism.

### D2 — Priority 1: weighting planned prompt classes does not establish matched image content

**Confirmed.** Original classes are visually coded, while generated membership
comes from the prompt's intended class. No generated-content adherence annotation
was performed. The classes also cover substantially different fine subjects.
Cézanne's three water references are a pond reflection, coastal houses and a
river-house reflection; the eight water briefs include lily pads, open sea below
cliffs, several rivers and coastal villages. Monet's four built references are
snowbound houses, a bridge, a misty village and rural cottages, while the built
briefs emphasize multiple house/garden/avenue configurations. Matching the three
class masses does not match scene, season, composition, depth, sky fraction or
palette-relevant subject matter.

Evidence: `studies/painter_distribution_study_v1/MAIN.md:16–39`;
`configs/painter_distribution_study_v1/research.json:12–27`;
`data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/reference_panel.jsonl:3,4,9,28,55,62,64`;
`src/latent_art_bench/painter_distribution_study_v1/study.py:53–60,95–107`.

**Affected claims:** content-adjusted style discrepancy, painter specificity
independent of subject, or naming as a purely stylistic mechanism. The randomized
text addition can still identify a total prompt effect under the statistical
assumptions; content changes caused by naming are part of that effect.

**Repair with retained images:** independently code actual generated and original
content using the same rubric, retain failures of adherence, report agreement and
support tables. Preserve the original assigned-class analysis; any observed-content
analysis is a new descriptive sensitivity and must not silently condition away
a treatment-induced mediator. Existing fine-content annotations can inform a
new common-support diagnostic, with sparse or unsupported cells marked clearly.

**New data if needed:** reference works in supported scene strata, or a small
new prospectively designed content benchmark. Adding repetitions of the same
24 briefs does not increase content breadth.

### D3 — Priority 1: capture and rendering differences remain unidentified

**Confirmed.** Every reference candidate has unresolved capture workflow.
The acquisition retains Wikimedia derivatives, often of unprofiled parent files.
Primary reference measurement records show missing-assumed-sRGB for 33/38 Monet
and 23/32 Cézanne files. No reference parent is exactly square; all 576 paid
generations are square. Google produces JPEG; FLUX produces PNG. Common resizing
and a shared additional JPEG pass cannot reverse previous photography,
white-balance, color grading, compression or composition decisions.

Evidence: `src/latent_art_bench/painter_distribution_study_v1/references.py:204–228`;
`src/latent_art_bench/painter_distribution_study_v1/reference_delivery.py:82–91`;
`studies/painter_distribution_study_v1/REFERENCES.md:124–132`;
`studies/painter_distribution_study_v1/MAIN.md:75–95`;
`src/latent_art_bench/painter_distribution_study_v1/transport.py:66–76`.
Counts were recomputed from the retained metadata and normalization records,
without opening artwork or rerunning extraction.

**Affected claims:** painter-style failure, intrinsic loss of diversity, physical
brushstroke conclusions, and a model-quality ranking. These nuisance dimensions
may contribute to separation; the audit does not quantify their contribution.

**Repair:** explicitly separate total digital-file distribution discrepancy from
style interpretation. Add geometry/profile/source diagnostics and seek a
same-work nuisance benchmark. Two proven independent photographic captures of a
subset of works would be valuable; alternate encodings of one capture answer a
different question. If genuine capture pairs cannot be obtained, retain that
limitation rather than calling synthetic JPEG processing a capture control.

### D4 — Priority 2: the native-size sensitivity changes the target and loses a content class

**Confirmed.** The implementation correctly defines `native_short_side` using
the **recorded parent-surrogate dimensions**, not the downloaded thumbnail
dimensions. `reference_delivery.py` copies `expected_width/height` from the
candidate and adds separate `delivery_width/height`; `study.py:127` uses the
former. These dimensions are metadata about a digital parent, not proof of an
independent photographic event or the highest-resolution capture in existence.

| Painter | Full works | Parent short side ≥1,024 | Delivered short side ≥1,024 | Parent-filter classes: water / built / land |
|---|---:|---:|---:|---|
| Monet | 38 | 4 | 4 | 2 / 0 / 2 |
| Cézanne | 32 | 19 | 18 | 2 / 6 / 11 |

`analysis.py:66–78` recalculates class masses from the filtered references and
drops generated classes with zero target mass. The Monet sensitivity therefore
compares four different works and excludes built generations; it is not a
controlled experiment changing only resolution. The variance reversal cannot
be causally attributed to file resolution, nor can four works establish
high-resolution robustness.

Evidence: `src/latent_art_bench/painter_distribution_study_v1/reference_delivery.py:54–91`;
`src/latent_art_bench/painter_distribution_study_v1/study.py:118–142`;
`src/latent_art_bench/painter_distribution_study_v1/analysis.py:61–78`.

**Repair now:** correct the previous conversational description of this field;
report parent dimensions, delivered dimensions, surviving class counts and target
changes separately. Retain the frozen results. A new same-work resolution or
capture diagnostic must use a distinct scope and stable work membership.

### D5 — Priority 2: independent annotation and physical-work authentication are absent

**Confirmed.** The annotation receipt identifies one maintainer LLM and no
independent human review. Seventeen of 70 included works are mixed/uncertain
(9 Monet, 8 Cézanne); excluding them removes almost one quarter of the panel.
The content rubric is explicit, but its reproducibility and error rate have not
been measured. Attribution and physical-work identity rely on recorded
Wikidata/Commons/counted collection or catalogue identifiers, not a complete
independent inspection of museum and catalogue authority pages.

Evidence: `data/manifests/painter_distribution_study_v1/pdsv1-reference-coding-20260906/receipt.json:15–23`;
`studies/painter_distribution_study_v1/REFERENCES.md:39–71,94–122`;
`src/latent_art_bench/painter_distribution_study_v1/references.py:92–129,132–168`.

**Affected claims:** reliable content balancing, oeuvre identity, independent
validation. Residual mistaken identity or annotation error is plausible, not
demonstrated by this review.

**Repair:** obtain blind duplicate annotation and adjudication under an explicit
rubric; audit every current work against a physical-work authority record,
recording provenance and unresolved items. Do not silently edit sealed
annotations or drop inconvenient works. Publish corrections as a successor audit
and show the consequences. More generated images do not fix this weakness.

### D6 — Priority 2: OAuth contrasts include treatment-dependent service handling

**Confirmed.** All requests ask for medium-quality 1024-square PNGs. Of 430 OAuth
images, 424 report low quality and six medium; all six medium are artist-free
(three per painter). Only eight OAuth outputs are square. The local proxy source
is bound, but a requested service alias does not identify an immutable upstream
checkpoint. Neither provider pinning nor local source hashes prove absence of
upstream prompt rewriting.

Evidence: `src/latent_art_bench/painter_distribution_study_v1/transport.py:44–58,66–76,105–131,165–168`;
`papers/painter_distribution_study_v1/paper.tex:181–190`;
the terminal `observed.reported` fields in the four generation event ledgers.

**Affected claims:** fixed-quality naming effects or a GPT-checkpoint leaderboard.
The study can report the total behavior of the requested OAuth service route.

**Repair:** preserve all eight originally specified tests and all quality levels,
while separating service-level interpretations. A low-quality-only post-hoc
subset cannot restore randomization at fixed quality. A new fixed-rendering
experiment requires an endpoint that actually honors the contract, if that
mechanism becomes a central research claim; it is not needed to describe this
service's observed behavior.

### D7 — Priority 2: eight assigned batches are not eight independent sessions or days

**Confirmed.** All three route subsequences preserve their frozen randomized
request order. The initial four batches ran near their scheduled starts; the last
four ran consecutively under the user-authorized prospective timing amendment.
The full generation span is approximately 11.53 hours, not the planned 33 hours.
Requests within a route wait for previous completion, so treatment-dependent
latency and service carryover can influence later actual dispatch times.

Evidence: `studies/painter_distribution_study_v1/PARALLEL_COLLECTION.md:14–35`;
`studies/painter_distribution_study_v1/IMMEDIATE_COLLECTION.md:23–34,52–61`;
`studies/painter_distribution_study_v1/INFERENCE.md:25–39`;
generation event timestamps and the frozen `requests.jsonl` inventory.

**Affected claims:** temporal robustness, independent batch replication or a
causal mechanism without the specified no-interference assumption. Actual
interference was not demonstrated.

**Repair:** retain actual timeline and assigned-batch labels. An additional
separate-day replication would be useful only if temporal generalization is a
claimed result; many extra within-session images would not supply it.

### D8 — Priority 2: provenance supports local auditing, but compact Git evidence is not the full measurement archive

**Confirmed.** Committed manifests retain portable paths, hashes, prompt payloads
and numeric feature evidence. Original image bodies, generated responses and the
separate proxy checkout are outside the tracked research archive. Numeric
analysis can be examined from retained vectors; independent verification that
those vectors match image bytes requires the corresponding retained raw archive.
Reissuing stochastic generation requests cannot reconstruct the original bytes.
Local Git timestamps/freezes establish an internally auditable sequence, not
external preregistration or institutional review.

Evidence: `docs/ARTIFACTS.md:5–20,63–100`;
`src/latent_art_bench/painter_distribution_study_v1/transport.py:105–131`;
`src/latent_art_bench/painter_distribution_study_v1/study.py:249–289`.

**Repair before publication:** specify separate numeric-replay and raw-to-feature
verification packages, archive the raw evidence with checksums and a practical
access/redistribution arrangement, and test reproduction from a clean checkout.
Document which bytes can be shared and which require mediated access. Do not
describe hashes alone as independent verification of image measurements.

## Checks that passed and chronology

- Candidate selection replay returns the same 112 work records. All 2,052
  screening records match after ordinary tuple-to-JSON-list serialization. The
  check uses the same 1,193-work earlier frame and 6,718 recorded exposure keys;
  no recorded-key leakage was found. This is not proof against unrecorded aliases
  or model-training exposure.
- The 13 relevant offline reference, delivery and study tests pass. No live
  request, image access, extraction, generation or frozen-file mutation occurred.
- Original-acquisition freeze commit `1d7eadc` precedes its first GET; delivery
  successor freeze `e339a9d` precedes its first GET. The latter followed the
  recorded rate-limit stop and preserved earlier bodies rather than replacing them.
- Main freeze commit `a03503b` was recorded at 13:52:52 UTC, before development
  sensitivity measurement at 13:53:22. Parallel freeze `7ead740` was recorded at
  14:21:41, before reference measurement at 14:22:04 and research dispatch at
  14:30:00. Later continuation, recovery and immediate freezes precede their
  respective new dispatches.
- The immediate timing change was committed at 00:28:55 UTC on 2026-09-07;
  dispatch began at 00:29:19. Final collection ended 02:01:37; the first generated
  feature event is 02:01:54. The inspected records support outcome-blind timing
  changes with respect to generated fidelity vectors. Technical status, returned
  settings and reference features were already available at some amendments;
  do not call every amendment blind to all outcomes.
- The two refusals, single failed FLUX request and its exact technical retry
  remain separately recorded. No successful-image reroll or favorable-result
  replacement was found. The failures and changes are methodological history,
  not themselves evidence of selective reporting.

## Recommended revision order

1. Narrow the central claim and distinguish parent/file/capture dimensions;
   publish selection, support, annotation and service-rendering tables.
2. Audit current work identity and obtain independent original/generated content
   coding; evaluate nuisance sensitivity using a new, explicitly labeled scope.
3. Define a feasible source-based validation panel and capture-pair audit before
   assigning an additional painting count. Preserve the existing panel as closed.
4. Add a modest expert-informed perceptual validation of resemblance and
   within-set variation using existing images; do not assume feature spread is
   already a validated style-diversity measure.
5. Decide whether temporal replication, new painters or fixed-quality OAuth
   generation is required by the final claim. Broad extra generation should not
   precede these decisions.
