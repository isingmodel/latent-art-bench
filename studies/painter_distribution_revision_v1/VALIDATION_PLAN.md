# Reference feasibility and human construct validation

Prepared 2026-09-07 from already retained metadata and the completed methodology
review. This is an operational follow-up design, **not executed validation**.
No new artwork has been acquired, no image has been generated or remeasured, no
human has been recruited or contacted, and no ethics determination is recorded.
The revised computational paper therefore retains a finite image/feature claim.

This document implements the design and feasibility parts of review steps 3–5.
It does not report their conditional acquisition, human, or encoder branches as
completed. It does not reopen any terminal census. The review and this design
were produced by maintainer-run LLM agents; they are not independent human review.

## 1. Data decision for the current revision

**Do not buy more generations for the current revision.** The existing 1,006
images suffice for its fixed numeric diagnostics and the human stimulus design
below. Conservative existing accounting is $45.6819185 against the authorized
$75 ceiling, leaving $29.3180815, including the retained $5 unresolved-charge
contingency in the amount already counted. This is an accounting remainder, not
a fresh account-balance query. The revision spends $0 on generation.

Extra outputs cannot supply independent photographs of paintings, independent
content annotations, or human judgments. The paid named/free arms already share
square geometry, so collecting more square examples would primarily repeat the
current design. The stronger interpretation is presently limited by design and
construct validity, not merely image count or significance.

A later geometry experiment is justified only if all of the following hold:

1. Its declared target is the effect of requested/delivered geometry on the
   prompt/feature relationship, with a fixed endpoint and a precision target.
2. A single provider route can deliver the chosen landscape and square formats
   while holding quality and other requested settings fixed; technical checks
   distinguish requested from delivered properties and are excluded from science.
3. A new randomized geometry × named/free factorial is collected concurrently.
   Old square files cannot serve as its contemporaneous randomized square arm.
4. Frozen counts, brief selection, stopping rules, bounded technical retries and
   failure accounting fit the remaining ceiling at freshly verified prices.
   Widespread transport failure stops collection for diagnosis; it is not a reason
   for unbounded retries. Successful outputs are never regenerated for quality.
5. Its report explicitly says that changing geometry does not reproduce a
   painting's photography, identify a pure style effect, or validate human meaning.

These conditions have not been established and this branch is not required for
the narrower revision. New painters, models and prompt variants are likewise
deferred until they answer a specific remaining question. More observations are
not a substitute for an identifiable comparison.

## 2. Metadata-only reference feasibility audit

Inputs are the unchanged compact records under
`data/manifests/painter_distribution_study_v1/`:

- `pdsv1-reference-candidates-20260906/candidates.jsonl` and `screening.jsonl`;
- `pdsv1-reference-delivery-r2-20260906/deliveries.jsonl`;
- `pdsv1-reference-coding-20260906/annotations.jsonl`;
- `pdsv1-main-20260906/reference_panel.jsonl`.

Join candidate, delivery and selected-panel rows by exact `work_id`; count selected
work IDs once. Geometry uses `delivery_width` and `delivery_height`. Parent
resolution uses `expected_width` and `expected_height`. This audit reads metadata,
not image pixels. Authority URLs and collection IDs are attribution/holding
metadata; neither is evidence of a photographic workflow.

| Retained metadata measure | Monet | Cézanne |
|---|---:|---:|
| Candidate work identities | 64 | 48 |
| Delivered identities | 38 | 33 |
| Selected eligible works | 38 | 32 |
| Candidates outside selected panel | 26 | 16 |
| Selected water / built / land | 21 / 4 / 13 | 3 / 11 / 18 |
| Selected landscape / portrait / square | 37 / 1 / 0 | 24 / 8 / 0 |
| Selected mixed/uncertain labels | 9 | 8 |
| Selected visible-border notes | 3 | 1 |
| Parent short side ≥1024: water / built / land | 2 / 0 / 2 | 2 / 6 / 11 |
| Delivered short side ≥1024: water / built / land | 2 / 0 / 2 | 2 / 5 / 11 |
| Selected with at least one authority URL | 27 | 31 |
| Selected with a collection ID | 38 | 32 |
| Selected with unresolved capture workflow | 38 | 32 |
| Selected with empty media-source text | 38 | 32 |
| Selected delivered through `thumb.wikimedia.org` | 38 | 32 |

All 112 candidate geometries are nonsquare, including the 42 identities outside
the panel. Those 42 include the delivered Cézanne explicitly coded as figure-led
and ineligible. They are **not 42 additional eligible independent references**.
Unacquired candidates have no completed visual content/adherence adjudication.
The 2,052 screening rows record several screening stages/dispositions; they are
not a count of 2,052 unique eligible new paintings.

Four collection IDs occur for both painters. Their selected support is:

| Collection ID | Monet content counts | Cézanne content counts |
|---|---|---|
| `Q23402` | land 2, water 3 | built 1 |
| `Q106857407` | land 1, water 1 | land 1 |
| `Q812285` | water 1 | land 1 |
| `Q194622` | water 1 | land 1 |

Only `Q106857407` offers a same-class cross-painter entry (one land work per
painter). A work can have several collection memberships; memberships must not
be counted as independent images. This sparse overlap cannot support credible
photographic-source holdout, and the IDs do not document photography anyway.
Thirty-one Cézanne records include a catalogue authority URL; that is not proof
that the catalogue supplied their photographs. Creation-period and fine scene
support are not comprehensively coded in the selected compact panel.

Consequences: no exact-square original comparison is available in this retained
frame; the native-1024 Monet subset loses built scenes entirely; independently
documented capture pairs remain unavailable. Neither a parent resolution field
nor a different thumbnail encoding proves a better or independent capture.

## 3. A new reference study: target and stopping decision

The optional target is replication over a **declared eligible outdoor-painting
collection frame**, not each artist's entire oeuvre. Preserve the present panel as
exposed earlier evidence. A new namespace must identify separately which works
are genuinely new to the recorded exposure frame and which are repeat captures
of an existing physical work. Reusing historical images remains legitimate only
as explicitly exposed development or sensitivity evidence.

Before pixel acquisition, build a source manifest with physical work identity,
attribution authority, creation-date range, holding institution, documented
photographer/capture event where available, source asset identity, rights record,
delivered/parent dimensions, and missing-field flags. Deduplicate accession/QID
and provenance aliases. A crop, mirror, scan variant, or recompression is a new
file, not automatically a new painting or a new capture event. Source selection
must seek crossed painter/content support, rather than using one website per
painter and calling it controlled.

Two independent human coders, blind to metrics and model/prompt metadata, should
code broad content, fine scene, viewpoint, composition, visible borders, surface
damage and reproduction concerns for **both originals and generated outputs**.
Origin may be visually inferable; describe this as metadata blinding, not proof
of perceptual blinding. Preserve each coder's labels, uncertainty and disagreement
before adjudication. Report agreement and the unadjudicated sensitivity. Generated
prompt adherence is an outcome; retain failures rather than selecting a favorable
post-treatment subset as the new causal primary.

No acquisition N is justified yet. The earlier suggestion of 80–120 additional
paintings is a feasibility envelope, not a power result. After metadata and
annotation feasibility, simulate candidate designs with 40, 60, 80 and 120
independent works per painter where the declared frame can actually supply them.
Use plausible source/capture clustering and a range of effects including null and
small effects, not only the largest current effects. Estimate precision for a
declared reference-relative energy or spread target and separately for capture
variation. Repeated capture uncertainty is modeled at the work level. Report how
conclusions change across simulation assumptions; a bootstrap of the current
small frame alone cannot guarantee performance on unseen sources.

Choose the smallest feasible design meeting a prospectively stated interval-width
or power target and freeze all selected IDs, substitutions for technical
unavailability, counts and stopping rules before measuring new outcomes. No
significance-based stopping or topping up a closed panel is allowed. If no design
fits available work/source support, retain the finite-file claim. Captures that
remain undocumented remain unknown rather than being imputed independent.

## 4. Human study target and stimulus inventory

The primary human construct is **perceived variation among generated image sets
under named versus artist-free prompting**. Secondary image-level resemblance
asks whether a feature discrepancy tracks resemblance to a displayed painting
panel. These are different questions. The primary comparisons are the four
paid-route × painter cells; the two OAuth cells are secondary service comparisons
because delivered quality is treatment-associated.

The retained 24 briefs, three repeats and six route/painter cells provide 864
successful named/free images. OAuth generic images are outside this human design;
their two missing outcomes therefore do not induce selection between the included
arms. No selection uses feature distance, visual appeal or an agent's impression.

For reproducible ID allocation, define `H(parts)` as SHA-256 of the UTF-8 encoding
of `"pdsv1-human-design-20260907|" + "|".join(parts)`. Sort by hexadecimal digest,
breaking collisions by lexical full ID. Parts are literal strings; integer parts
use unsigned base-10 without padding. Before implementation freeze the exact
six cell IDs, paid/OAuth membership, successful selected request IDs and resolved
payload hashes from the completed collection; payload identity and availability
are eligibility fields. This prose defines an algorithm, **not a completed
stimulus manifest or human-study registration**.

### 4.1 Primary six-image sets

1. Within each of water, built and land, sort its eight brief IDs by
   `H(["brief", class_id, brief_id])`. Consecutive pairs form blocks `b=0,1,2,3`.
   Block `b` therefore contains six briefs: two from each class.
2. For each repeat `r=0,1,2`, each block, route and painter, form one named set
   and its artist-free comparator using those same six briefs and repeat index.
   Set index is `t=3*b+r`, from 0 to 11. A set's numeric trace uses equal weight
   1/6 per image and the unchanged primary scaler; this is a new equal-content
   set estimand, not the painter-weighted full-collection result.
3. There are 12 set pairs per cell and 72 overall, with no image reused across
   sets within a cell. They are disjoint physical-image sets, **not 72 independent
   samples of content**: all cells reuse 24 briefs in four common blocks, and
   repeats share brief definitions. Analysis must preserve these dependencies.
4. Randomize within-set layout using `H(["layout", rater_id, set_id, request_id])`.
   Both arms use equal-size 2×3 layouts, neutral background, aspect-preserving
   fit into equal display boxes, and identical zoom availability. Never crop an
   original or generated file silently to fill a box. Freeze display processing
   and browser dimensions; record device/viewport and failed image loads.

No original anchor is shown for variation. The question is: **“Which set shows
more variation in visual treatment, such as colour handling, marks and spatial
arrangement?”** Explain that this differs from which set is better or contains
more kinds of objects. Responses are left, about equal, right, and cannot judge;
“about equal” and “cannot judge” remain distinct.

This task can validate a generated-only prompt/variation association. It cannot
validate original/generated perceptual contraction. With six-image sets requiring
two works per class, the current Cézanne water group supplies only one disjoint
original set. More raters on that one set do not create reference replication.
A primary original/generated set comparison therefore awaits adequate reference
support and its own allocation/power freeze.

### 4.2 Assignment to raters and image-level resemblance

The feasibility candidates are **24 or 36 final adult raters**, plus a separate
6-person usability pilot. They are convenience recruitment designs, not a claim
of representative taste or adequate power. Consent, institution, compensation
and responsible human investigator are unresolved; final recruitment is closed.

Sort the six cell IDs lexically, index `c=0..5`, and assign eligible consenting
raters sequential opaque indices `i=0..R-1`, without using their judgments.
Each rater sees set indices `(2*i+j+2*c) mod 12`, `j=0,1`, for cell `c`: 12 set
trials total. At R=24 every set pair receives four ratings; at R=36 it receives
six. Each rater sees a particular image at most once in the primary block.
For each trial ID, sort its assigned raters by `H(["side", trial_id, rater_id])`;
put named on the left for the first half and on the right for the rest. Randomize
trial order by a separate `H(["order", rater_id, trial_id])` ranking.

Image resemblance is a separate block of 12 trials, two per cell. For `j=0,1`,
choose content class index `(i+c+j) mod 3` in the fixed order water/built/land.
Within the target class, hash-rank complete named/free request pairs by
`H(["image", rater_id, cell_id, str(j), brief_id, str(repeat)])` and take the first
whose image IDs were not shown in that rater's set block or earlier image trial.
If no pair remains, mark the planned trial unavailable; never substitute by
appearance. Record the exact resolved per-rater allocation before recruitment.

For each painter, hash-rank reference work IDs separately by content using
`H(["anchor", painter_id, class_id, work_id])`. The first three in each class
form three disjoint three-image anchor panels, one work per class per panel.
Trial `(i,c,j)` uses panel `(i+c+j) mod 3`. Original annotations and display
suitability need independent coding before this material is frozen. Do not
replace a displeasing work after ratings or metric inspection. A missing/corrupt
or rights-ineligible stimulus changes the planned inventory through a documented
prefield amendment, never through concealed substitution during collection.

Hide painter names, route, prompt method, file names and metadata. Ask which
generated image more closely resembles the **visual treatment in the examples**,
with the same four response options. This operationalizes similarity to the
displayed finite panel, not recognition of a named painter or authenticity.
Counterbalance block order by even/odd rater index. Compute the fixed predictor
as the named/free difference of mean Euclidean distances to the three displayed
anchors; all vectors use the unchanged primary scaler. An image-to-panel score
is not energy between full distributions.

### 4.3 Separate nuisance tasks and optional coverage

After both construct blocks, choose six already judged trial pairs by hash order,
three for visual quality and three for depicted-content diversity, with no
overlap between these two nuisance questions. Preserve selection IDs and the
prior response association. These are secondary descriptive outcomes; they do
not become exclusions or “controls” that erase treatment-induced content/quality.
Include four simple instruction/device checks unrelated to agreement with the
research hypothesis. Total planned burden is 34 trials per rater, subject to the
usability pilot; actual montage viewing may make this burdensome.

Coverage is **not active in this protocol**. If later included, it needs a separate
inventory: multiple disjoint original anchor panels, equal-size generated sets,
and an original-to-set question for each anchor (“Is there a comparable visual
treatment represented in this set?”). The endpoint would be the proportion of
displayed anchors judged represented, not image resemblance, set variation, or
the number of distinct subjects. The present sparse reference classes do not
justify a primary painter-distribution coverage claim.

## 5. Pilot, sample size, exclusions and analysis freeze

The six-person pilot checks comprehension, successful image loading, duration,
and whether participants distinguish variation, resemblance and quality. Use
separately ID-listed historical-study examples outside the 864-image final
named/free inventory; pilot reference works must likewise be disjoint from the
final nine-anchor inventory per painter. Its stimuli and responses stay outside
the final analysis. Do not inspect a
metric–human association to choose the final metric, favorable images or sample
size. As operational thresholds, revise instructions/display and repeat a
separately labeled usability pilot if more than one of six participants cannot
explain the variation task, if any systematic display failure occurs, or if
median duration exceeds 30 minutes. A revised pilot is not additional research
evidence and may not be pooled with the final sample.

Before recruitment, a human investigator must approve a smallest meaningful
association and desired precision. A candidate for discussion is a change of
0.10 in predicted preference probability over a one-standard-deviation change
in the within-cell metric contrast; it is a design preference, not an empirical
fact. Simulate the actual crossed allocation with null and positive/negative
associations, plausible tie rates, rater heterogeneity, set effects, four shared
brief-block effects and original-panel reuse. Compare R=24 and R=36; report
coverage, interval widths and power rather than relying on total ratings. If
neither supports the agreed target, report a feasibility study or enlarge an
approved design before collection. Do not promise confirmatory validity from
these counts alone.

Prespecify the following before any final response is seen:

- Primary association: the slope between perceived set variation and the
  **within-cell centered log trace ratio** for named/free sets, in the four paid
  cells. Center using all frozen stimulus contrasts, not human responses. A
  zero-trace set makes its predictor unavailable; keep and report its judgments
  separately rather than injecting a tuned epsilon.
- Primary analysis: cumulative-logit mixed model of the ordered response
  free-more / equal / named-more, with the fixed metric predictor, cell terms,
  named-left term and block-order term, and crossed rater, set-pair and shared
  brief-block effects. The four block levels limit variance-component precision;
  simulation must include this limitation. A predeclared Bayesian regularized
  fit is an option for stability, with priors, diagnostics and interval decision
  rules fixed before outcomes. Do not select between models for significance.
- “Cannot judge” is missing for the ordered construct response, not a tie or
  half vote. Report its rate by cell and metric contrast, plus a predeclared
  sensitivity treating its directional preference as unresolved. Report a high
  or condition-dependent cannot-judge rate as a construct/display limitation.
- Secondary resemblance uses the analogous signed image-distance predictor with
  crossed rater, image-pair/brief and anchor-panel dependence. The three anchor
  panels limit generalization. OAuth, quality and content-diversity results are
  explicitly exploratory. Do not convert the secondary image task into support
  for the primary distribution construct.
- One primary slope is the only confirmatory human endpoint. If a confirmatory
  resemblance endpoint is also desired, freeze a two-endpoint Holm family at
  0.05 before collection; otherwise report its interval descriptively. Do not
  test each route/painter and each feature family without a declared family.
- Exclude only no consent/ineligible age, a verifiable duplicate enrollment,
  unrecoverable display failure, withdrawal, or failure of at least two of four
  explicit instruction checks. Report all reasons and retain an eligible-rater
  sensitivity including attention-check failures. Do not exclude ties, an
  unexpected preference, lack of art training, or disagreement with features.
  Timing alone is a flag; any speed rule must be numerically fixed using pilot
  usability information before final collection.
- Freeze the final target R, an eligible-completion definition, maximum total
  recruitment, closing date, compensation and replacement policy. Stop at that
  target or declared deadline, not a p-value. Partial/withdrawn dispositions and
  unavailable trials remain in the flow report. Record display failures as
  technical outcomes without changing the successful stimulus inventory.

Before recruitment the host institution's ethics determination, consent and
withdrawal materials, responsible human investigator, recruitment channel,
compensation and secure response storage must be recorded. These are unavailable
now. The existing study's [human follow-up](../painter_distribution_study_v1/HUMAN_FOLLOWUP.md)
already requires the institutional determination. No participant contact or
institutional approval is implied by this specification, and LLM judgments are
not substitutes for the proposed participants.

## 6. What would change the interpretation

A precise null or reversed metric–judgment association would withhold the matching
perceptual interpretation even if numeric prompt contrasts remain reproducible.
An imprecise association leaves validation unresolved; a nonsignificant estimate
does not prove equivalence. Opposite within-brief and aggregate changes already
exclude a universal repeat-to-repeat contraction claim. Lack of reference/source
overlap leaves source attribution unidentified irrespective of more ratings or
smaller p-values.

One complementary frozen encoder may later measure the retained files under a
new measurement scope, after local resource and geometry-processing feasibility.
Choose one model/version/layer and fixed endpoints before seeing its results;
do not train an evaluator or select whichever embedding agrees best. Its agreement
with the 31 features would be triangulation, not independent human validation.
The present revision does not require this optional branch or new API images.
