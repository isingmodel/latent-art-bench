# Painter Feature Generation v1: prospective study protocol

Protocol ID: `painter-feature-generation-v1/1.7`

Status: **canonical research plan; not yet an execution freeze**

Date: 2026-09-02

## 1. The question this study will answer

This study asks:

> For a fixed generative model and one R0a-frozen 24-template common-content prompt frame, (a) do
> registered painter-name requests meet availability and content-adherence gates and (b), among
> technically analyzable near-copy-excluded returns, does the measurable-feature distribution
> reproduce the content-standardized distribution in that painter's R0a-randomized,
> sealed-confirmation population of eligible digital painting surrogates?

The unit of the claim is a **set of generated images**, not a cherry-picked image. The reference is
a **conditional distribution across physical works**, not a painter centroid, an artist classifier,
or a generic movement label.

The study separates five questions that must not be collapsed:

1. **target fit** — are generated and real target-painter distributions practically close?
2. **target specificity** — are the outputs closer to the intended painter than to prespecified
   close comparison painters?
3. **coverage** — do outputs cover the target distribution rather than reproduce one prototype?
4. **conditioning effect** — does adding the painter name move outputs toward the target relative
   to matched painter-free controls?
5. **copying and availability** — is apparent fit explained by near-copying, selective refusals, or
   missing outputs?

A positive conditioning effect alone is not painter-distribution reproduction. Classifier
recognition, raw cosine similarity, a small centroid distance, or a nonsignificant difference test
is also insufficient.

## 2. Claim domain and nonclaims

The primary claim concerns **digital image surrogates under the declared acquisition,
normalization, model, prompt, and feature pipelines**. It does not establish similarity of pigment,
binder, impasto, layering, underdrawing, physical brushwork, artistic intention, authorship,
authenticity, legal infringement, or inclusion of a work in model training.

“Painter feature” in this protocol means only the three prespecified digital image-statistic
families after real-only source/content qualification. It is not synonymous with whole style,
perceived painterly manner, or the full oeuvre. A later blinded human study may test perceptual
convergence, but its absence keeps the present claim at the digital-statistic level.

Common scene-group and five-contrast standardization does not identify a pure causal painter effect.
Unstandardized interactions among scene details, career phase, and the frozen source mixture may
remain. The protocol therefore asks whether two declared digital-surrogate distributions are close
under one mutually supported content design; it does not claim that painter identity alone caused
every observed difference.

The first study is restricted to paintings cataloged as exactly attributed to the named painter,
classified as paintings, and described as `oil on canvas`. Other supports, uncertain attributions,
works after or from a workshop, drawings, prints, photographs, and generated images are not pooled
with the primary reference. They may appear only in a separately frozen sensitivity analysis.

The initial comparison panel is:

- Claude Monet;
- Alfred Sisley;
- Camille Pissarro; and
- Paul Cézanne.

The first three form a deliberately difficult close-neighbor Impressionist group. Cézanne probes a
nearby but less interchangeable boundary. Every named condition is compared with all other painters
in the frozen panel; no favorable neighbor is selected after seeing results.

The panel is a target, not a promise. If the metadata census cannot support it, the study must
prospectively reduce the panel before any generation and issue a new protocol version. It must not
lower population or support floors, mix supports, or add low-provenance images merely to preserve
four names.

## 3. What prior work contributes—and does not contribute

Pilots 0–3 and `painter_features_v1` are historical precursors. They contribute failure evidence,
candidate data, acquisition receipts, and feature code. They do not answer this study question.

In particular:

- Pilot 2 issued 320 registered generation requests, but five refusals left both requested-label
  comparison grids incomplete. Its four primary tests were not run; descriptive prompt movement is
  not a fidelity result.
- `painter_features_v1/MEASUREMENT_PROTOCOL.md` is a real-image measurement-qualification protocol.
  It explicitly excludes generated images and remains hash-bound historical evidence.
- Collection Freeze 3 preserved four NGA files. Those files prove a narrow acquisition workflow;
  one work per painter-content cell cannot estimate a painter distribution.
- The repository currently retains 132 historical JPEG deliveries under an ignored Pilot 0
  boundary. Of these, 113 are primary-named deliveries with distinct byte hashes. They are useful
  development material, but physical-work deduplication and new eligibility adjudication are still
  required.

No historical failed endpoint will be retried or relabeled. In particular, the closed Pilot 3 Met
R2 request is not reopened and no alternate Met endpoint is introduced as a workaround.

## 4. Study architecture

The study has six sealed stages. One eligible real-work frame and all three disjoint populations are
fixed before any research feature is measured:

1. **R0a — census, corpus, and randomization freeze**: acquire and verify the finite eligible frame;
   reconcile physical works and capture families; complete firewalled content coding; make one
   painter-level random pool assignment; then select one shared 24-template byte-exact frame from a
   prospectively hashed candidate library using content labels only. Freeze its common-content
   target, every pool-level population weight, source-diversity receipt, CSPRNG seed, and a separate
   same-work reproduction census outside the randomized study frame. If optional external replication
   is intended, its unopened-source population is also acquired, coded, and ranked now. R0a releases
   only the complete development population and auxiliary reproduction census to feature analysts.
2. **R1a — development and simulation**: measure the complete development population, close the three
   prespecified feature definitions and coverage panels, qualify reproduction/source diagnostics,
   validate the already frozen content estimands, and run whole-decision simulations for generator
   repetitions and decision margins. Real qualification and confirmation populations are censuses,
   not subsamples.
3. **R0b — locked-access record**: release the complete frozen qualification populations while
   keeping complete confirmation populations sealed. R0b cannot add a candidate, change
   eligibility, acquire a new source, rerank a unit, or create a top-up population.
4. **R1b — untouched real qualification**: run the already frozen method once on the complete locked
   qualification population while the final reference remains sealed. A failed family is retained as a
   failed registered family and is not replaced after viewing qualification.
5. **G0 — generator and execution freeze**: bind exact model identity, verify the already frozen
   24-template text hashes, and freeze seeds, request order, failure handling, estimands, margins,
   and analysis code.
6. **G1 — registered generation and confirmation**, split without an intervening analytic choice:
   **G1a** executes every request and seals every attempt, failure, and output hash while the final
   analysis-resolution real-reference files remain unopened; **G1b** then opens that reference
   once, runs the frozen copy/feature pipelines, and publishes the complete locked analysis.

Each freeze is a tracked machine-readable artifact with a schema version, repository-relative
paths, input hashes, reviewer decision, and predecessor hash. A later stage cannot silently repair
an earlier stage. If the R0a frame or its preassigned populations cannot support the frozen design,
the study stops and starts a new protocol/R0a; it does not collect a convenient supplement. Any
change that can affect inclusion, measurement, or inference requires a new protocol version and a
new untouched confirmation set.

## 5. Real-painting corpus

### 5.1 Sampling unit and identity graph

The primary independent unit is the physical work. The manifest must keep separate identifiers for:

1. physical work;
2. capture event or capture family;
3. museum-published asset;
4. derivative service and requested geometry; and
5. delivered file.

Different IIIF sizes, re-encodes, thumbnails, mirrors, or Wikimedia copies of one museum photograph
are not independent paintings or independent captures. Physical-work identity is reconciled with
institution and accession identifiers, catalogue data where available, title/year/dimensions, and
exact plus perceptual-image checks. Ambiguous collisions are quarantined before partitioning.

### 5.2 Federated scale census and provisional population plan

The old 120-work scenario is retired: it cannot estimate tails, spread, or an energy-distance
reference. The equally sparse six-scene plan is also retired. A filename stress test of the 3,190
discovery candidates used the frozen multilingual token set `lake|pond|lac|étang|etang|bassin|pool`
and found only 5 Pissarro, 1 Sisley, and 6 Cézanne item rows, versus 46 Monet rows. These are noisy
discovery labels, not deduplicated works or content judgments, but they falsify
the assumption that 60 lawful works exist for every painter in every narrow scene cell. The active
design therefore collects a large painter-level frame and standardizes content with bounded
population weights instead of pretending that rare cells are abundant.

The working capacity plan per painter is:

- acquired and fully adjudicated internal frame: at least **360 physical works**;
- development population, measured in full: **72 works**;
- untouched qualification population and census: **108 works**;
- sealed confirmation population and census: every remaining work, at least **180**; and
- optional unopened-source population and census: at least **96 additional works**.

Across four painters, the minimum acquired and analyzed internal frame is 1,440 works: 288
development, 432 qualification, and at least 720 confirmation. Registering external replication
raises both acquired and analyzed real-work counts to at least 1,824. A separate auxiliary
reproduction census contains at least 32 physical works and is not part of either total. These are
prospective capacities, not proof of feasibility, power guarantees, or quotas to fill with inferior
records. Measuring every acquired work is simpler and more informative than acquiring reserves and
then discarding them from analysis. If a population cannot meet its frozen count or content/source
gate, the study stops and issues a new protocol/R0a; no post-feature census, source addition, or
top-up is allowed.

The retained direct-institution legacy frame is plainly insufficient. Its provider-specific working
counts were assembled during earlier exploratory work but were not preserved as a reproducible
source snapshot, so they are not evidence for a numeric corpus claim here. A new four-provider
traceable live-item audit (Yale, Paris Musées, Getty, and Minneapolis Institute of Art) recorded exact
record identifiers and found 43 all-content metadata candidates after strict attribution,
oil-on-canvas, rights, image, and 1,024-pixel checks. Those 43 records are not yet content-coded and
are not admitted experimental works.

An exploratory Wikidata/Commons scale query on 2026-09-02 found 3,190 distinct Wikidata painting
items with a creator in the four-painter panel, a Commons image, and both `oil paint` and `canvas`
material statements: Pissarro 685, Sisley 705, Monet 1,132, and Cézanne 668. The query returned 3,367
item-image links and 3,364 distinct file links. These are **discovery candidates, not admitted
works**: Wikidata statements may be incomplete or wrong, multiple images may represent one work,
Commons file rights and geometry are not yet verified, and an authoritative holding record and
capture ancestry remain mandatory. The result defines a candidate universe large enough to warrant
an R0a census; it does **not** establish that the required pass yield is feasible. R0a must publish
an exact painter-by-gate attrition funnel before any feasibility claim. The query, timestamp, counts,
and response hashes are recorded in the data-readiness evidence.

R0a must freeze at least 360 fully acquired and adjudicated internal candidates per painter and at
least 24 works in each of the four broad scene groups defined below. The 24-work floor is a support
alarm, not a sampling quota or a claim that 24 is inferentially sufficient. If external replication
is registered, R0a must also freeze at least 96 candidates per painter from its prospectively
declared unopened-source component, including at least eight per broad scene group. The combined
gate is 456 candidates per painter. Raw candidate volume cannot compensate for failed identity,
rights, content, source-diversity, calibration-feasibility, or image-quality gates.

R0a makes one randomization per painter and never redraws it to improve content balance or later
results. A recorded domain-separated CSPRNG permutation assigns ranks 1–72 to development, ranks
73–180 to the 108-work qualification population, and ranks 181 onward to the sealed confirmation
population. Independent random ranks are retained inside the latter two populations only as audit
receipts; they do not select subsamples. Every development, qualification, confirmation, and
registered external work is measured when its access stage opens. No work moves between
populations.

The common content domain is one finite `outdoor_place_landscape` frame, following Pilot 2's intent
to hold broad subject matter comparable while painter remains the target. Every admitted work
receives exactly one broad principal-setting group:

1. `water_organized`: sea, coast, harbor, river, canal, lake, pond, or stream organizes the scene;
2. `built_place_organized`: buildings, a settlement, street, square, or industrial place organizes
   the scene and water does not;
3. `route_organized`: a road, path, lane, or track outside a dominant settlement organizes the scene;
   or
4. `open_or_wooded_land`: field, hillside, mountain, forest, orchard, garden, or other terrestrial
   landscape organizes the scene.

`Outdoor-place landscape` means that an exterior place—not a person, still-life arrangement,
interior, animal study, or narrative event—is the principal depicted subject. A small landscape
background behind a portrait does not qualify. Coders first identify the visually dominant spatial
organizer without using painter name, title, or a needed count. Water wins only when its surface,
channel, or coastline organizes the composition; a small incidental stream does not. Built place is
tested next, route next, and the residual qualifying terrestrial setting enters open/wooded land.
If no principal setting wins under the frozen area/focal-organization rubric, the work is coded
`ambiguous_multiple` and excluded rather than adjudicated toward a needed group. The former six
narrow categories remain recorded as nonbinding diagnostics when determinable; they are not sample
cells. Career date is eligible-domain variation and is reported by phase, not standardized away.

Before coding the active frame, the codebook is calibrated on historical or dedicated
development-only works that can never enter qualification or confirmation. Only those works supply
positive, boundary, and exclusion examples. Within every broad scene group, eligibility coders also
record five variables with frozen categories:

1. season or foliage state: `leafless_or_winter`, `spring_or_blossom`,
   `full_green_foliage`, `autumn_or_senescent`, or `indeterminate`;
2. illumination or weather: `clear_direct_light`, `diffuse_or_overcast`,
   `fog_rain_or_snow`, `dawn_dusk_or_night`, or `indeterminate`;
3. built-element prominence: `absent`, `incidental`, or `organizing_or_dominant`;
4. people, animal, boat, or vehicle prominence: `absent`, `incidental`, or
   `organizing_or_dominant`; and
5. view depth: `shallow`, `middle`, `deep`, or `indeterminate`.

`Incidental` means visible but not responsible for the scene's principal focal organization;
`organizing_or_dominant` means that removing the element would change that organization. Depth is
coded from the depicted spatial structure, not canvas dimensions. Templates never use an
`indeterminate` value.

These variables do **not** create 24 real-work cells. Before active frame labels are read, R0a-intent
must hash exactly 12 candidate **complete prompt frames**, each containing 24 semantically coherent
templates and at least two templates from every broad scene group, plus the selection code. A
complete candidate includes each template's byte-exact UTF-8 artist-free text, byte-exact named
rendering with one `<target_painter>` placeholder, the exact painter-name substitution table,
punctuation, language, negative-prompt string, condition insertion point, broad scene group, and
five content values. An independent wording and
codebook review also ends before active labels; no later stage may rewrite a candidate string. After
the one pool assignment, R0a evaluates those 12 frames. It derives each frame's four scene
proportions and five contrast means, solves the population projections below for every painter and
intended development, qualification, confirmation, and external population, and discards any frame
that fails a gate. Among survivors it maximizes the minimum Kish-ESS fraction; ties minimize the
maximum relative weight, then squared deviation of the four scene proportions from 1/4, then the
lexicographic frame ID. This finite, outcome-blind common-support step uses only frozen content
labels. It never reads a research feature, generated image, title, painter-favorable distance, or
source-quality outcome.

To avoid an underidentified 13-contrast rake, the primary common-content standardization uses
exactly five prespecified binary contrasts—one per coded variable:

1. visibly `leafless_or_winter` versus every other recorded season state;
2. visibly diffuse, adverse, or low light (`diffuse_or_overcast`, `fog_rain_or_snow`, or
   `dawn_dusk_or_night`) versus every other recorded illumination state;
3. `organizing_or_dominant` built elements versus `absent` or `incidental`;
4. any visible person, animal, boat, or vehicle (`incidental` or `organizing_or_dominant`) versus
   `absent`; and
5. visibly `deep` view versus every other recorded depth state.

Here an `indeterminate` category contributes zero only to the named **visible-property** contrast;
it is not silently recoded as a determinate category. Full categorical tables, including every
indeterminate rate, remain mandatory diagnostics. The selected 24 templates define one common
eight-dimensional content target $m$: three nonredundant broad-scene proportions plus the five
contrast means.

After the one pool assignment and before any research feature is opened, R0a defines a fixed
finite-population entropy projection separately for every painter's development, qualification,
sealed-confirmation, and registered external population. For population $U$ with size $N$ and
eight-vector $z_i$,

\[
q^*=\arg\min_{q_i\ge0}\sum_{i\in U}q_i\log(q_i/(1/N)),\qquad
\sum_iq_i=1,\qquad\sum_iq_i z_i=m.
\]

This is a finite-distribution I-projection in the sense of
[Csiszár (1975)](https://doi.org/10.1214/aop/1176996454): it minimizes KL/I-divergence from uniform
mass under prespecified linear moment constraints. That mathematical foundation does not validate
the eight chosen content moments, the painter construct, or any gate below.

The complete eight-dimensional target must lie in the population's joint convex hull. The unique
solution must meet a frozen numeric tolerance, put no more than four times uniform mass on any
work, retain Kish effective sample size of at least 60% of $N$, and satisfy Section 5.2's
$q^*$-weighted source-share ceilings. These checks are joint, not
separate marginal-support checks. The selected template frame, population weights $q^*$, and solver
receipts are sealed in R0a and never refit to a realized sample or bootstrap replicate. If no single
template subset passes every intended population, R0a is NO-GO: no redraw, regularization,
same-version top-up, or painter-specific target is permitted. Because every retained population is
measured as a census, estimators use $q_i^*$ directly; there is no real-work inclusion probability
or inverse-probability correction. The content-standardized $q^*$ distribution is primary
because it matches the same prompt-content target for every painter; the uniform finite-population
distribution is a mandatory secondary sensitivity. Neither matches interactions or exact joint
profiles.

Two independent eligibility coders view only a frozen, at-most-512-pixel-long-side derivative with
painter, title, institution, accession, and source masked. This is real pixel exposure and is logged
honestly. The derivatives are held in a role-separated store: feature/method/generation analysts
cannot view them, coder notes, or adjudication imagery before G1b. Analysts receive only frozen
eligibility, scene-group and five-variable labels, counts, and agreement statistics needed for the
registered design. Labels and adjudication are completed before randomization; analysis-resolution
qualification and confirmation files remain inaccessible. Only the excluded codebook-calibration
set supplies visible examples outside the coding role.

Every metadata-, rights-, geometry-, and decode-qualified derivative is in the **visual-eligibility
denominator**, whether either coder ultimately excludes it. Each coder independently records one of
`eligible_outdoor_place_landscape`, `ineligible`, or `ambiguous_multiple`; a blank or missing label is
an explicit disagreement, not a removable row. The content-label reliability denominator is the
**union-eligible set**: every derivative called eligible by at least one coder. Within that set, an
ineligible, ambiguous, or missing response is retained as its own value in the confusion table rather
than dropping the item. Adjudication occurs only after these raw tables and their hashes are sealed.

Before metadata are revealed, each coder records whether the image or painter was recognized.
Recognition flags, disagreement rates, and results excluding recognized items are reported; a coder
cannot silently substitute title or attribution knowledge for the visible-content rule.

As prospective project quality floors rather than literature universals, preadjudication exact
three-way visual-eligibility agreement must be at least 0.90 within every painter's complete
visual-screening denominator, and each coder's `ambiguous_multiple` share must be no more than 0.10
there. On the union-eligible denominator, raw agreement must be at least 0.85 for the four-way broad
scene label and for each of the five three-state visible-property contrasts (`visible`,
`not_visible`, `indeterminate`). The same 0.85 gates are recomputed from the unchanged raw coder
labels in every painter's assigned development, qualification, confirmation, and, when registered,
external population. Each coder separately—not their pooled or adjudicated labels—must have season,
illumination, and depth `indeterminate` rates no greater than 0.20 in every such denominator. Full
denominators, missing-label counts, confusion tables, raw agreement, Cohen's kappa, and
category-specific agreement are reported; kappa alone is not a gate because prevalence can make it
unstable. If an agreement or indeterminate ceiling fails, the current R0a is NO-GO. Adjudication may
resolve unit labels under the frozen codebook but cannot erase the failed reliability receipt, drop
a difficult variable, or revise a threshold to rescue the same version.

In G1b, two independent blinded coders audit every sealed-confirmation image and every technically
analyzable generated image with the same codebook, with painter identity, real/generated status,
source, prompt assignment, and condition masked as far as the pixels permit. Before adjudication,
their complete raw labels are sealed and the 0.85 broad-scene and five three-state-contrast agreement
gates are applied separately within every real-painter confirmation population and every generated
named-painter or shared-control condition for each model. Each coder's season, illumination, and depth
`indeterminate` rate must also be no greater than 0.20 in those same collections. A failed G1b coding
gate makes the affected adherence, realized-content, and feature-reproduction endpoint inconclusive;
adjudication cannot repair the reliability receipt. When the gates pass, a third blinded adjudicator
resolves disagreements under the frozen codebook, and the resulting deterministic consensus label is
the single realized label used for $J_r$, $z_{tj}$, and $r^*$. Original scene-group and prompt
assignments are never changed. The primary real standard
is the R0a-frozen $q^*$ content target. The primary generated standard is the equal-weight census of
the selected 24 prompt templates. Uniform-real, five-variable categorical, per-template,
per-scene-group, and leave-one-scene-group-out results are mandatory diagnostics; none licenses
post-outcome regrouping.

Source is not a quota cell and no museum is forced to fill a target count. The R0a internal frame
and each of its development, qualification, and confirmation populations must contain at least four
holding/capture groups per painter. No group may exceed 30% of the unweighted internal frame. Within
each assigned population, no group may exceed 30% of either its unweighted count or its final $q^*$
mass. The frame must contain at least two groups within each broad scene group where the authoritative
federation makes that possible. Where two or more source groups exist in a frame scene group, no
group may exceed 70% of its unweighted count; within an assigned population's multi-source scene
group, no group may exceed 70% of either its unweighted count or its scene-conditional $q^*$ mass. A
registered external population requires at least two unopened holding/capture groups per painter and
the same 70% overall unweighted and $q^*$ ceiling. No full-frame $q^*$ is defined or implied. A
structurally single-source scene group is explicitly
`source_domain_limited`; it cannot be described as provider-general. All incidence and weighted-share
tables are frozen after the one random assignment; a failure is not repaired by redrawing.

The primary population is therefore a **common-content-standardized, frozen-source-mixture digital
surrogate**, not a source-neutral latent oeuvre. The observed holding/capture composition after the
frozen content weights remains part of the estimand. Source-specific, leave-one-source-group-out,
and held-group real-only qualification tests are binding before generation. Exact common
holding/capture-group×scene-group comparisons between painter pairs are mandatory diagnostics
wherever both painters have the R1a-frozen minimum support. Missing common cells are reported and
never imputed; they are not primary sampling cells and there is no requirement that every pair share
all holding/capture groups.

### 5.3 Source hierarchy

Primary candidates come only from authoritative open-access museum records with traceable image
delivery and work identity:

- Art Institute of Chicago public-domain API records and IIIF;
- National Gallery of Art open data and Open Access images;
- Cleveland Museum of Art CC0 records and image assets; and
- Smithsonian Open Access records and media, after painter-specific census;
- Yale University Art Gallery LUX records and IIIF;
- Paris Musées collection records and IIIF;
- Getty Museum collection data and item-level CC0 media; and
- Minneapolis Institute of Art records and eligible public-domain images, with its publication
  caveat retained rather than inferred away.

Other official institutional open collections may be added only in R0a with their exact data
version, rights statement, query, image-delivery contract, and provider code. Existing Met files may
remain development evidence, but no new Met request is permitted by this protocol.

Wikidata and Wikimedia Commons form a scalable **federated discovery and delivery layer**, not an
authority by themselves. A Commons asset may enter the primary corpus only when its Wikidata item is
reconciled to an authoritative holding or catalogue record, exact attribution and support are
confirmed there, the file page carries an admissible reuse statement, the delivered geometry passes,
and source/capture ancestry is recorded. Otherwise it remains discovery-only. Europeana, Paris
Musées, and other federated or institutional open channels may be added under the same record-level
rule; an aggregator-wide rights statement never substitutes for the item and media rights fields.

WikiArt and ART500K supply literature-comparable development or benchmark views only. Scraped search
results, Pinterest, auction previews, and unattributed mirrors never enter a confirmatory reference.

### 5.4 Admission and exclusion

R0a freezes source snapshots and acquisition intents, then acquires, verifies, content-codes, and
freezes the **one complete eligible frame** before any research feature is measured. The R0a ranks
assign exposure roles once; R0b later releases the complete preassigned qualification population,
and G1b later opens the complete preassigned confirmation population. Admission uses a controlled
medium/support ontology rather than
cross-institution literal string equality; the raw museum wording and normalized decision are both
retained. The ontology admits oil paint on textile canvas and excludes board, panel, paper, academy
board, mixed support, and unresolved `fabric` descriptions unless a museum record establishes
canvas. Admission requires:

- exact painter attribution in the artist role;
- `Painting` classification;
- normalized `oil_on_canvas` support under the frozen ontology;
- public-domain or institutionally open image status recorded at collection time;
- a resolvable authoritative work page and image endpoint;
- minimum delivered short side of 1,024 pixels without upsampling;
- decodable complete image, credible geometry, and retained color-profile metadata; and
- membership in exactly one of the four frozen broad outdoor-place scene groups, with all five
  content variables coded.

Exclusions are recorded with reason before randomization. Because delivery and decode are frame
eligibility conditions, a post-randomization missing or corrupt file is unit nonresponse, not an
invitation to add a candidate. It remains in the ledger; if the frozen minimum cannot be met under
the prespecified missingness rule, the affected analysis is inconclusive or a new protocol/R0a is
required.

### 5.5 Acquisition and preservation

For every request, store the intent before network access and then record timestamp, exact URL,
provider object and asset IDs, response status, redirects, content type, byte count, pixel geometry,
ICC profile state, and SHA-256. Preserve every R0a-frame source file unchanged under the ignored
`research_workspace/painter_feature_generation_v1/` boundary. The acquisition/coding role may
handle those bytes; feature analysts receive only the development selection until later gates open
the locked selections. Git receives only compact metadata, hashes, rights evidence, codebooks, and
reports.

Collection is single-threaded and provider-throttled according to official documentation. Two
qualification objects per provider are fetched first. Their delivery and decode contracts must pass
before the provider's main queue starts. There is no cross-provider fallback for a frozen
acquisition intent.

### 5.6 Partitioning and historical exposure

Partition by physical work and capture family before feature extraction. Related captures or
derivatives cannot cross populations. Broad scene group, source, career phase, and the five content
variables are recorded design variables, not tiny sample cells. The auxiliary reproduction census is
outside this frame and never contributes a real-reference observation.

R0a freezes one domain-separated CSPRNG algorithm, seed, painter-level permutation, and pool
assignment. Development, qualification, and sealed confirmation contain different physical works.
Ranks 1–72 form development; 73–180 form the 108-work qualification population; and 181 onward form
the sealed confirmation population $P^C$, whose size is at least 180. The permutation creates
disjoint exposure roles, not a later probability subsample. R0b releases all 108 qualification
works; G1b opens all confirmation works once. For every painter and population, the freeze records
the population size, every membership and rank, the randomization receipt, content target, and
population weight. Outcome-informed weights, modeled values for missing units, and post-feature
population changes are forbidden. If attrition invalidates a complete population census, the
affected endpoint is inconclusive or the study starts a new protocol/R0a; no replacement is drawn.

Eligibility-thumbnail exposure is not called a sealed pixel set. R1b qualification is not reused as
the final reference. Analysis-resolution final-reference source files remain access-controlled
through G1a: the feature method, G0 analysis package, generation requests, attempts, failures, and
output hashes are all fixed before those files are opened once in G1b.

Historically feature-exposed Pilot 2 works may be used only for code fixtures or codebook
calibration outside the randomized study populations. They cannot be inserted into the R0a
development population after ranks are drawn. Any historical delivery admitted to the one frame must meet the same
prospectively declared exposure rule and must have had no pixel or feature role in choosing formulas,
thresholds, content rules, sample size, or margins. Confirmation-population works must be untouched
by project feature development.

External replication is optional for the primary internal claim. It exists under version 1.7 only
if its candidate component, eligibility labels, and painter-level ranks are frozen in the same
R0a before development features. It requires unopened holding/capture groups, previously unopened
physical-work families, no prior analysis-resolution pixel or feature access by the analysis team,
and the same firewalled low-resolution coding. A new capture of a development work estimates
reproduction error; it is not a new external physical work. External results are analyzed
separately and never pooled to rescue the internal conclusion.

Before any randomized-study feature is measured, R0a freezes a separate auxiliary
same-work-reproduction **census**. Its eligible frame is every lawfully usable work found in the
R0a source snapshot that belongs to a retained painter, lies in the outdoor-place domain, is outside
all randomized study populations, and has at least two demonstrably independent capture workflows.
All eligible works enter; none is selected by appearance or feature value. The census must contain
at least eight physical works per painter—at least 32 total—span at least three broad scene groups
per painter and at least two holding/capture-workflow pair types per painter. Two sizes, crops,
re-encodes, mirrors, or deliveries from one capture are labeled as dependent and do not qualify.

Auxiliary-census works and captures do not count toward the 1,440-work minimum internal frame or
any randomized-study population size. After the one common pooled-development median/IQR
scaling, a work's family-level capture disturbance is the maximum, over its independent capture
pairs, of the root-mean-square coordinate difference. The observed-workflow disturbance bound
$\eta_F$ is the maximum across all census works; every coordinate's maximum absolute paired shift
is also reported. A family qualifies only if $\eta_F\le0.5$ scaled-IQR units and every coordinate's
maximum shift is at most 0.5 IQR. These are exact bounds for the observed census, not confidence
bounds for all digitization workflows. If the census, workflow diversity, or bound fails, the
family is `source_domain_limited`, fails, or requires a new protocol/R0a; no same-version top-up is
allowed.

## 6. Image preparation

The immutable source file is never overwritten. The primary analysis branch:

1. decodes the image with a frozen library version;
2. converts an embedded valid ICC profile to sRGB and records the transform;
3. admits an untagged image to the primary color branch only when the provider contract explicitly
   declares sRGB; otherwise it is excluded from primary color analysis and an assumed-sRGB result is
   sensitivity-only;
4. detects frame, mat, border, signature, watermark, and text regions with a frozen procedure;
5. preserves aspect ratio—no forced-square warp—and creates a 1,024-pixel-long-side derivative
   only when this is downsampling; and
6. maps valid artwork pixels to normalized canvas coordinates without cropping composition.

The sensitivity branches vary interpolation, long-side size, border mask, color-profile handling,
and JPEG recompression within declared perturbation ranges. A coordinate that changes more under
plausible reproduction perturbations than between real works cannot be called painter-associated.

Generated and real images receive the same resize, mask, color, and feature code. A generated fake
signature or written painter name is masked and reported; it cannot support specificity.

## 7. Feature measurement

### 7.1 Primary candidate families

Three complementary digital-image-statistic families are primary from the outset:

1. **color organization** — valid artwork pixels are converted from sRGB to CIELAB under D65;
   record the 10th, 25th, 50th, 75th, and 90th percentiles of \(L^*\) and chroma, plus a normalized
   low-chroma mass below chroma 5 and the first three sine/cosine Fourier coefficients of hue among
   the remaining pixels;
2. **spatial and orientation organization** — compute relative luminance, Gaussian scales
   \(\sigma\in\{1,2,4\}\), Sobel gradients, edge density at a development-frozen normalized
   gradient-magnitude threshold, gradient-weighted axial-orientation entropy and the first three
   sine/cosine axial Fourier coefficients, and Hann-windowed radial Fourier slope plus angular
   anisotropy; and
3. **texture organization** — compute four-level undecimated `db2` wavelet detail bands and record
   total log detail energy, normalized log energy in horizontal, vertical, and diagonal bands at
   every level, coarse/fine energy ratio, horizontal/vertical asymmetry, and scale entropy.

Raw ordered hue and orientation bins do not enter Euclidean energy distance: their wrap-around
geometry is represented by the circular and axial Fourier coefficients above. R1a feature cards fix
the Fourier frequency interval in cycles per canvas, mask-boundary treatment, wavelet boundary mode,
and masked-pixel behavior before qualification.

Tie-aware ordinal patterns, local color transitions, spatial pyramids, and alternative scales are
prespecified sensitivities, not candidate replacements. This fixed choice avoids selecting the
family that happens to separate painters best.

Every formula, mask behavior, scale, threshold, interpolation method, normalization, and software
artifact is closed in R1a feature cards with numeric fixtures. One common transform per coordinate
is fit to the equal-painter mixture of the four complete, $q^*$-weighted development populations:
its weighted median is the center and its weighted IQR is the scale. The same transform is then
applied unchanged to every painter, control, generated, qualification, confirmation, and external
vector; painter-specific scaling is forbidden because it would invalidate pairwise specificity. A
coordinate whose pooled development IQR does not exceed twice its maximum registered
reproduction-perturbation shift is nonidentifying and fails before R1b; it is not regularized after
qualification. No outcome-selected dimensional reduction is used in the primary analysis.

Coverage does not gate on every feature coordinate. Before R1b, four interpretable coverage
coordinates per family are fixed:

- color: median \(L^*\), median chroma, low-chroma mass, and first-harmonic hue resultant magnitude;
- spatial: \(\sigma=2\) edge density, \(\sigma=2\) orientation entropy, Fourier slope, and Fourier
  anisotropy; and
- texture: total detail energy, coarse/fine ratio, horizontal/vertical asymmetry, and scale entropy.

The remaining coordinates contribute to the geometry-aware family energy distance and descriptive
plots but are not thousands of independent coverage gates.

The families remain separate in inference. There is no universal weighted painter-style score.

### 7.2 Real-only qualification

A family qualifies only if R1a development tests and one untouched R1b result jointly show:

- deterministic repeatability within a numeric tolerance;
- stability under declared resize, compression, border, and profile perturbations;
- painter separation that transfers to held works;
- binding source robustness under held holding/capture groups and leave-one-source-group-out
  analyses;
- specificity inside the complete close-neighbor panel;
- no dependence on signatures, labels, frames, or one broad scene group; and
- stable uncertainty and acceptable power in disjoint-population and generator simulations.

For source robustness, R1a uses development-real data and the frozen same-work census to retain the
family-specific source-shift bound \(\eta_F\), a minimum positive-weight count and ESS per side, and
a leave-one-group alarm before R1b. For painter $a$, broad scene $s$, source group $c$, and a
$d_F$-coordinate family, R1b normalizes the frozen $q^*$ weights separately inside $c$ and its
same-painter/same-scene complement and computes

\[
R_{a,s,c,F}=\left\{d_F^{-1}\sum_{\ell=1}^{d_F}
\left[Q^{q^*}_{a,s,c,\ell}(.5)-Q^{q^*}_{a,s,\neg c,\ell}(.5)\right]^2\right\}^{1/2}.
\]

The quantiles use Section 10.1's exact left-quantile rule after the one pooled development scaling.
Uniform-real values use the same functional with uniform conditional weights. R1b also recomputes
target-versus-neighbor separation after leaving each group out. A family passes only if every
supported exact finite-population $R_{a,s,c,F}\le\eta_F$, no uniform-real source alarm fires, no
leave-one-group-out separation reverses the frozen direction or crosses its alarm boundary, and the
result survives the registered capture perturbations. An unsupported comparison is reported and the
corresponding source-general claim fails; it is not imputed. This is a real-only gate: generated images never set
\(\eta_F\), select a source group, or decide whether a family qualifies.

Source classification accuracy remains diagnostic rather than a substitute gate. If the qualification
source support is too thin to run the frozen robustness analysis, the family is `domain_limited` or
fails; source effects are not assumed absent. Exact gates and smallest effects of interest are set
from development-real cross-fitting and controlled perturbations, then sealed before locked
qualification. Each family is a separate registered claim. A failed family remains labeled
`failed`, `reproduction_associated`, or `domain_limited` and cannot be replaced or promoted after
generation. G0 may proceed when at least one prespecified family qualifies and all source/content
identification gates pass; an omnibus statement across all three families is allowed only if all
three qualify and later pass. If none qualifies, the study stops.

### 7.3 Secondary diagnostics

The following are reported separately and cannot determine the primary conclusion:

- Kim et al. A-vector compatibility reconstruction;
- Kim et al. C-vector or another named CLIP semantic coordinate;
- Contrastive Style Descriptors (CSD), after exact checkpoint reconciliation;
- artist-attribution classifiers and tag-based recognition; and
- FID, KID, UMAP, t-SNE, or raw cosine summaries.

Kim's paper analyzes chronology and context in 72,447 paintings; it does not validate A or C as a
generated-to-real painter-fidelity metric. CSD and attribution papers validate constrained
recognizability or retrieval, not full target distribution coverage. These methods are useful for
triangulation and shortcut diagnosis, not as oracles.

## 8. Generation experiment

### 8.1 Generator identity

Before G0, candidate transport is tested only with frozen non-art, non-painter conformance prompts.
Those outputs are quarantined from research analysis. Candidate order and operational scoring
(identity recordability, seed behavior, receipt completeness, error rate, and cost ceiling) are set
before the test; visual painter resemblance cannot select the model.

G0 selects exactly one primary generator by those operational criteria—not by favorable research
output. It binds:

- provider and endpoint or local checkpoint;
- marketed model name, requested label, revision, weight hash when available, and runtime version;
- sampler, steps, guidance, size, quality, negative prompt, safety settings, and seed behavior;
- execution window and regional/account context where relevant;
- moderation, timeout, retry, and malformed-output rules; and
- the exact claim label. If backend identity is opaque, the claim names only the endpoint, requested
  label, parameters, and execution dates; it does not generalize to the marketed model family.

A second exact generator may run the same sealed design as a replication. Results are never pooled
across models. Replication starts only after its own identity and resource freeze.

### 8.2 Prompt templates

The generation frame is the single byte-exact 24-template frame selected from the 12 R0a-intent
candidates. It contains at least two templates in every broad scene group. R0a freezes every
template's text hash, group, and five coded content values, which together define the common
eight-dimensional real-content target in Section 5.2. G0 verifies the selected hashes and substitutes
only the registered painter name into the frozen placeholder; it cannot change wording. Template
attributes come only from the frozen codebook, not from titles, descriptions, or compositions of
evaluation works. They contain no living artist, artwork title, museum, collector, or distinctive
object. They are supported marginally under the bounded population-weight gate; no exact joint
profile is asserted to exist in every painter's real corpus.

R1a may audit the already frozen rendering and hashes but cannot edit them. G0 uses the entire
24-template frame rather than sampling a favorable subset. Inference is
limited to this fixed prompt frame and the matched common-content real standard, not to all possible
prompts or the painters' unrestricted oeuvres.

Within a template, the named and control prompts are identical except for the frozen condition phrase:

- `named`: `... in the style of <target painter>`; and
- `artist_free`: the same content with no artist, movement, period, or style phrase.

The exact templates, punctuation, language, negative prompt, condition insertion point, and render
function are therefore sealed before active real labels or features. Painter and condition order is
randomized within prompt templates. If an endpoint requires a wording or syntax adaptation, that
endpoint is ineligible for this version or the study begins a new protocol/R0a.

### 8.3 Registered request count

The primary paired design requires the same repetition count $R$ for every named condition and its
shared painter-free control inside a template. For $A$ retained painters and $B$ prompt templates:

\[
N_{requests}=BR(A+1).
\]

The earlier $R=16$ capacity—1,920 requests per model—is retired in version 1.7 because it cannot
clear the boundary-safe availability gate even with perfect returns. In the mathematically most
favorable case where every registered repetition is its own auditable independent unit, if scene
group $s$ contains $B_s$ templates its all-success lower bound is

\[
1-\left\{\frac{\log(1/\alpha_e)}{2B_sR}\right\}^{1/2}.
\]

Thus a gate $\tau$ requires

\[
R\ge \max_s\left\lceil
\frac{\log(1/\alpha_e)}{2B_s(1-\tau)^2}
\right\rceil,
\]

before adherence, copy, distance, coverage, missingness, and whole-decision power are considered.
Because the endpoint inventory determines $\alpha_e$ and the selected frame determines $B_s$, R1a
must set $R$ after both are frozen. For scale only, even an impossible best case with
$\alpha_e=.05$ and six templates in every group requires $R\ge25$, or at least 3,000 requests; the
actual Bonferroni allocation and any common-shock clustering will require more and may make the bound
uninformative. G0 cannot freeze a design for which a perfect-return
endpoint cannot mathematically clear its bound. A second exact generator repeats the final frozen
design rather than reusing favorable outputs. G0 may raise $R$ but may not create unequal
named/control counts or supplementary unpaired primary blocks.

The 24 prompt templates are a finite census, not a random sample of possible prompts. Each template
has fixed weight 1/24 in the primary prompt-frame estimand; a scene group's weight is its selected
template count divided by 24.
Uncertainty therefore never bootstraps templates as though they were sampled from a prompt
superpopulation. Primary inferential uncertainty comes from generator repetitions; the frozen real
population is measured completely.

For a fixed deterministic local execution map, when deterministic seeds exist, G0 draws each
template's ordered seed list independently **with
replacement** from one declared finite integer seed space, using domain-separated randomization
seeds. No duplicate is deliberately added or rejected; any chance duplicate and the seed-space size
are recorded. A common realized list is not reused across templates. Within a template, each seed
indexes the full correlated request vector containing all retained painter-named conditions plus the
shared artist-free control. G0 freezes this matrix; inference resamples the whole condition vector
inside each template, never painter components independently. Conditional on the fixed deterministic
map, this targets independent uniform seed draws for the fixed templates. A seed field exposed by an
opaque remote endpoint does not by itself establish that fixed-map contract. For an opaque or remote
endpoint, with or without a seed field, G0 instead schedules $C$ equal-size balanced candidate
common-shock units. Each contains $L$ complete execution waves, and every wave contains exactly one
registered request for every selected template×named/control condition; request order is randomized
inside the wave and $R=CL$. Units are separated and backend/account/region/batch/moderation receipts
are recorded under a prospective independence argument. This structure lets a unit be resampled
without changing any template or condition count. If a plausible common shock crosses the frozen
unit boundaries, or a balanced unit cannot be executed and retained with failures in place, the
remote endpoint is ineligible or inconclusive rather than treated as request-level replication. In
every execution mode, Section 10.4's independence audit is binding for rate **and continuous**
inference. Copying a file or deliberately repeating a registered seed outside the frozen random draw
does not increase sample size.

### 8.4 Intention-to-generate and outcome handling

Every request is written before it is sent. There is no curator selection and no best-of-N.
Technical retry is allowed only for a frozen list of transient conditions and preserves every
attempt. Moderation refusals, empty responses, corrupt returns, and policy errors remain in the
denominator and are never replaced to complete a favorable grid.

Feature distances are necessarily conditional on a technically analyzable return; a refusal has no
feature vector and is never imputed. The primary result is therefore two-part:

1. intention-to-generate availability over every registered request; and
2. the feature distribution conditional on an analyzable return.

Both are binding. Availability is reported for every named painter×scene-group cell and every shared
artist-free×scene-group cell; a global fraction cannot hide differential failure. R1a freezes an MNAR
sensitivity rule and the minimum analyzable repetition count required inside every fixed prompt
template.

Content is coded blind to painter, provider, and prompt condition. Primary grouping always uses the
**assigned prompt template** and its broad scene group, so an off-topic output is not reassigned after
treatment. This intention-to-prompt rule is primary; it does not condition on exact realization of
the template's five attributes. Blind visual coding supplies a separate binding scene-group-adherence
endpoint plus five-variable marginal and confusion-table diagnostics. Realized-content and
generated-output reweighting to the five visible-property contrasts are sensitivities. Off-topic
but technically valid images remain in
their assigned feature distribution and availability denominator.

## 9. Copy and leakage audit

After the G1a request/attempt/output ledger is sealed, copying is measured in G1b before painter-fit
analysis is unblinded:

1. exact byte and decoded-pixel hashes;
2. perceptual hashes across simple transforms;
3. calibrated SSCD or another frozen copy-detection descriptor;
4. whole-image and crop-level nearest-neighbor search; and
5. manual adjudication of flagged pairs while blinded, where possible, to primary distance, prompt
   condition, and painter identity.

The search covers the registered real corpus and any lawful same-work derivatives available to the
project. Thresholds are calibrated before generation on known same-work transformations, different
works by the same painter, same-content works, close-neighbor works, and unrelated pairs. A flag
means similarity within this searched universe; absence of a flag does not prove that an image was
absent from unknown training data.

Flagged outputs remain in availability and the immutable output ledger. Confirmatory fit,
specificity, and coverage are computed on the near-copy-excluded set; all-output estimates are
descriptive. The copy-excluded result must retain the frozen minimum effective sample in every
template or the painter result is inconclusive. The binding soft near-copy rate and interval are
computed over all named outputs for each painter; scene-group-specific rates and intervals are mandatory
heterogeneity diagnostics. Exact/crop reconstruction is also listed by scene group. This aggregation is
fixed before generation and cannot hide a localized cluster: any exact/crop event blocks an
unqualified no-reconstruction statement, and any frozen scene-group heterogeneity alarm makes the
painter result inconclusive. Near-copying cannot count as evidence of distribution reproduction,
and the study never infers training-set membership from image similarity alone.

## 10. Primary estimands

Development and method-qualification works never define the final reference. For painter \(a\) and
qualified family \(F\), let $U^C_a$ be every physical work in that painter's R0a-randomized,
sealed-confirmation population and let $q^*_{ai}$ be its R0a-frozen common-content population
weight. The primary real standard is the finite distribution

\[
P^{C,*}_{a,F}=\sum_{i\in U^C_a}q^*_{ai}\,\delta_{x_{ai,F}},
\qquad \sum_iq^*_{ai}=1.
\]

It matches the same selected prompt-frame scene proportions and five visible-property means for
every painter. Exact interactions and joint profiles are not matched or imputed. The uniform
finite-population distribution $P^{C,u}_{a,F}=N_a^{-1}\sum_i\delta_{x_{ai,F}}$ is a mandatory
secondary sensitivity; it describes the frozen observed frame mixture, not the unrestricted oeuvre.
The observed holding/capture mixture after either declared weighting remains part of the
digital-surrogate estimand.

Analysis-resolution confirmation files are opened only in G1b, after the G1a
request/attempt/output ledger and hashes are sealed. If optional external replication was included
in R0a, \(P^{E,*}_{a,F}\) defines its separate unopened-source content-standardized distribution and
is never pooled with \(P^{C,*}\). The claim is limited to these frozen outdoor-place
digital-surrogate frames.

Let \(t\in\{1,\ldots,24\}\) index the fixed prompt templates and let $g(t)$ map each template to
its broad scene group. For each template, define the conditional distribution induced by the G0-frozen
uniform seed draw or, where seeds are unavailable, the registered execution-block mechanism. Every
template receives weight 1/24, defining \(G^N_{a,F}\) and \(G^0_F\)
from near-copy-excluded, technically analyzable outputs under the **assigned template**. A template
with fewer than the frozen
minimum analyzable repetitions makes the painter-family result inconclusive; successful templates
are never renormalized to hide it. Availability and content adherence remain separate estimands.

The selected prompt frame and $q^*$ weights are part of the primary estimand, not a post-outcome
repair. Intention-to-prompt grouping remains primary even when a generated image is blindly coded
into another scene group. Realized-content and uniform-real results are mandatory sensitivities; no
joint-profile equality is claimed.

### 10.1 Absolute target fit

The primary discrepancy is energy distance on the development-frozen, robust-scaled coordinates.
Because the full sealed-confirmation population is measured, no real-work sampling estimator or
real-work bootstrap is needed. Let $U$ contain its $N$ works. Set $p_i=q_i^*$ for the
common-content primary target and $p_i=1/N$ only for the uniform-real sensitivity.

Let $m_t\ge2$ be the analyzable repetitions for template $t$, $g_{tj}$ a generated vector,
$x_i$ a real vector, and $d(u,v)=\lVert u-v\rVert_2$. The generated–real cross term is

\[
\widehat D_{GP}=\frac{1}{24}
\sum_{t=1}^{24}\frac{1}{m_t}
\sum_{j=1}^{m_t}\sum_{i\in U}p_i d(g_{tj},x_i).
\]

The real self term is exact for the frozen finite population:

\[
\widehat D_{PP}=
\sum_{i\in U}\sum_{k\in U}p_ip_k d(x_i,x_k).
\]

Diagonal terms contribute zero distance. With uniform $p$, every ordered population pair has
coefficient $1/N^2$.

Because generator repetitions sample the frozen seed or execution-block mechanism, the generated
self term is the equal-template mixture U-statistic:

\[
\widehat D_{GG}=\frac{1}{24^2}\left[
\sum_t\frac{1}{m_t(m_t-1)}\sum_{j\ne k}d(g_{tj},g_{tk})+
\sum_{t\ne u}\frac{1}{m_tm_u}\sum_{j=1}^{m_t}\sum_{k=1}^{m_u}d(g_{tj},g_{uk})
\right].
\]

The point estimate is

\[
\widehat E=2\widehat D_{GP}-\widehat D_{GG}-\widehat D_{PP}.
\]

It may be slightly negative because the generated terms are sample estimators and is reported
without truncation. For scalar coordinate $v_i$, real weighted quantiles use the exact finite CDF

\[
F_P(v)=\sum_{i\in U}p_i\mathbf 1(v_i\le v),\qquad
Q_P(\alpha)=\inf\{v:F_P(v)\ge\alpha\}.
\]

Ties use this left-quantile definition with no interpolation; IQR is
$Q_P(.75)-Q_P(.25)$. A binding tail quantile is unavailable if fewer than three positive-weight
works determine it, and the affected endpoint is inconclusive. Population-weight effective sample
size and maximum weight are binding R0a diagnostics; an unstable population fails rather than being
regularized after inspection.

Generated coverage uses the same left-quantile convention and preserves the fixed equal-template
estimand. For scalar coordinate $v_{tj}$,

\[
F_G(v)=\frac1{24}\sum_{t=1}^{24}\frac1{m_t}
\sum_{j=1}^{m_t}\mathbf1(v_{tj}\le v),\qquad
Q_G(\alpha)=\inf\{v:F_G(v)\ge\alpha\}.
\]

Thus each analyzable output has weight $1/(24m_t)$ inside its template; pooling outputs with equal
image weights when template return counts differ is forbidden. Replicates recompute these weights.

MMD is a sensitivity analysis and cannot replace a failed energy-distance result. The primary
energy estimate uses all eligible observations and permits unequal real and generated set sizes.
For finite-size diagnostics only, the fixed real census and generated set are repeatedly thinned to
matched diagnostic sizes; these curves do not replace the full-census primary estimate or add a
real-work sampling uncertainty term.

\[
A_{a,F}=E_F(G^N_{a,F},P^{C,*}_{a,F}).
\]

R1a defines the practical margin from explicit population-level adverse alternatives, not from
sampling noise. For each family it enumerates: each coverage coordinate shifted separately by
\(\pm0.25\) development IQR; coherent positive and negative family-location shifts; each coverage
spread contracted to 0.80 or expanded to 1.25; a 20% tail contamination; a 20% mixture with the
development-selected closest comparison painter; and registered correlation/dependence changes.
The closest painter is the one with the smallest cross-fitted development real-real energy distance
under the common-content-standardized development target. Large Monte Carlo draws approximate the
population energy distance for every transformation; the smallest registered adverse distance defines provisional
\(\epsilon_{a,F}\). Disjoint development/qualification comparisons and full-population controlled
perturbations calibrate real-reference stability separately and are never added to the margin. Every
transformation, direction, random seed, and population approximation tolerance is frozen in R1a.

The family is nonidentifying if its disjoint-population and registered-perturbation stability
envelope cannot distinguish \(\epsilon/2\) from \(\epsilon\), if \(\epsilon\) overlaps
target-versus-neighbor separation, or if the selected design cannot detect the registered tail and
dependence failures.

A target-fit component passes only if its upper simultaneous confidence bound is no larger than the
frozen margin. Failure to reject equality is never called equivalence. R1a may make the margin more
stringent or increase the generator repetition count before G0; if the frozen real populations are
insufficient, the family fails or a new protocol/R0a begins. R1a may not relax the stated adverse
alternatives after R1b.

### 10.2 Support and contraction

Primary coverage uses the twelve interpretable coverage coordinates fixed in Section 7.1 rather
than every feature coordinate. For each, the simultaneous interval for the
generated-versus-confirmatory median difference divided by the confirmatory IQR must lie inside
\([-0.25,0.25]\), and the generated/confirmatory IQR ratio interval must lie inside
\([0.80,1.25]\). Tenth and 90th percentiles are mandatory descriptive tail checks, while the family
energy distance carries the registered tail alternatives. R1a simulation must show that the median,
IQR, and tail diagnostics are stable for the frozen real populations and registered generator
repetitions; otherwise generator repetitions are increased before G0 or the family fails
qualification. No real population is enlarged after R0a.

Density/coverage and precision/recall are reported as sample-size- and \(k\)-sensitivity diagnostics
only. They are not four independent gates and cannot rescue failed median or spread coverage.

### 10.3 All-neighbor pairwise specificity conjunction

Primary specificity uses the same frozen-source-mixture targets as absolute fit. For every other
registered painter \(h\):

\[
S_{a,h,F}=E_F(G^N_{a,F},P^{C,*}_{h,F})-
E_F(G^N_{a,F},P^{C,*}_{a,F}).
\]

R1a fixes
\(\delta_{a,h,F}=0.10L_{a,h,F}\), where \(L\) is the smallest positive cross-fitted development
target-versus-neighbor energy separation across the frozen source leave-outs and registered
reproduction perturbations under the common-content standard. It is a conservative robustness
bound for the observed development population, not a confidence bound for an oeuvre. A family-pair
with nonpositive \(L\) fails real-only qualification. Specificity requires
the lower simultaneous bound for every registered competitor to exceed \(\delta\). The 10% fraction
is a project SESOI, not a literature universal, and its operating characteristics are included in
R1a simulation. A generic Impressionist-looking distribution equally close to Monet, Sisley, and
Pissarro fails specificity.

This estimand compares explicitly frozen content-standardized digital-surrogate source mixtures, so it is interpreted
only after the binding source-robustness gate passes. For every painter pair, exact common
holding/capture-group×scene-group analyses are also mandatory wherever both sides meet the
R1a-frozen minimum count. Every supported cell, its count, and its contrast is reported; absent
cells are listed and never imputed. These matched-source analyses are diagnostics, not an alternate
primary estimand, and they need not cover every broad scene group. A contradiction that crosses the
R1a-frozen source-sensitivity alarm makes the primary specificity conclusion source-sensitive or
inconclusive; a favorable matched subset cannot rescue a failed primary conjunction.

### 10.4 Content robustness, availability, and copy rate

The primary comparison uses the common-content-standardized real populations and equal-24-template generated
frame. Per-template, per-scene-group, and leave-one-scene-group-out estimates are mandatory heterogeneity
diagnostics; they cannot be searched for a favorable subgroup. Career phase is target eligible-domain
variation, reported as heterogeneity rather than used to make unlike painters artificially
contemporaneous. The claim is not uniform fidelity over every possible subject or an unrestricted
oeuvre.

The report includes the complete two-coder confusion table and marginal table for each of the five
content variables, separately by painter and broad scene group, for real eligibility and G1b audit
coding. For generated images it also cross-tabulates each template-assigned category against the
blinded realized category, separately for every named painter and shared control. Simultaneous
intervals are shown at both scene-group and template levels. No joint-profile success rate is a primary
endpoint: the selected templates do not assert that an exact joint real profile exists.

Primary generated analysis remains intention-to-prompt, using the assigned template even when blind
coding disagrees. Mandatory sensitivities include realized-scene-group analysis and the uniform-real
finite populations described in Section 5.2. For the binding realized-content alarm, let
$b_{tj}=1/(24m_t)$ be the base mass of every analyzable near-copy-excluded output and let $z_{tj}$ be
its blindly coded eight-vector. Before outputs exist, R1a freezes the entropy projection

\[
r^*=\arg\min_{r\ge0}\sum_{t,j}r_{tj}\log(r_{tj}/b_{tj}),\qquad
\sum_{t,j}r_{tj}=1,\qquad \sum_{t,j}r_{tj}z_{tj}=m.
\]

It must meet the same joint-convex-hull tolerance, no-more-than-four-times-base-mass cap, and Kish
ESS of at least 60% of the base-weight ESS. For output indices $u$, its generated self term is the
prespecified weighted distinct-pair U-statistic

\[
\widehat D^{r}_{GG}=
\frac{\sum_{u\ne v}r_u^*r_v^*d(g_u,g_v)}{1-\sum_u(r_u^*)^2},
\]

with $r^*$ used directly in generated–real terms and exact weighted coverage quantiles. R1a must
validate this sensitivity estimator and recompute $r^*$ inside each generator replicate; an
infeasible replicate is retained as a failed sensitivity decision, never dropped. Infeasible or
unstable realized weights, or reversal of any passed target-fit, coverage, or specificity margin,
makes the result content-sensitive or inconclusive. The sensitivity can never rescue a failed
intention-to-prompt result. All real and realized-output weight vectors, maximum weights, Kish ESS,
and residual target error are reported.

Availability is:

\[
V=\frac{\text{technically analyzable returned images}}
        {\text{all registered requests}}.
\]

Rate gates do not use an empirical bootstrap, which would have zero width after all successes or no
observed copies. For each fixed rate endpoint, index all of its registered requests by $i$, give
every template equal total mass and every registered repetition within a template equal mass $w_i$,
and keep $\sum_iw_i=1$. Define $A_i=1$ for an analyzable return, $J_i=1$ when that return is also
blindly coded into its assigned broad scene group, and $K_i=1$ when it is also a soft near-copy.
Thus the point rates are

\[
\widehat V=\sum_iw_iA_i,\qquad
\widehat H=\frac{\sum_iw_iJ_i}{\widehat V},\qquad
\widehat C=\frac{\sum_iw_iK_i}{\widehat V}.
\]

Before execution, G0 must partition those requests into **auditable independence units** $c$. Set

\[
W_c=\sum_{i\in c}w_i,\qquad
\bar X_c=W_c^{-1}\sum_{i\in c}w_iX_i\in[0,1],\quad X\in\{A,J,K\}.
\]

Then $\widehat X=\sum_cW_c\bar X_c$. For a fixed local deterministic model/runtime, one independent
IID seed draw can define a unit; the whole paired painter/control condition vector stays together
whenever an endpoint spans conditions. For an opaque or remote service, distinct request IDs,
timestamps, or the word `block` do not establish independence. G0 must group every request sharing a
plausible provider episode, batch, backend revision, moderation state, outage, retry cascade, or other
common shock into one unit, document why different units are independent for the target mechanism,
and freeze the grouping before returns. If a common shock cannot be separated, the conservative unit
may be the whole affected run. Random request order and a null autocorrelation diagnostic are useful
checks but are not, by themselves, an independence argument.

Before G0, R1a enumerates every **unique directional one-sided tail event** needed by every binding or
reported rate endpoint. In particular, an endpoint that uses availability, adherence, and copy
requires four events—$A$ lower, $A$ upper, $J$ lower, and $K$ upper—not three means. Duplicate use of
the same directional bound is counted once, but opposite tails are distinct. R1a allocates a fixed
$\alpha_{rate}$, defines $M_{rate}$ as the resulting number of directional events, and uses
$\alpha_e=\alpha_{rate}/M_{rate}$ for every event. For a requested lower or upper event on
$X\in\{A,J,K\}$, the independent-bounded-unit weighted-Hoeffding radius and bound are

\[
h_e=\left\{\tfrac12\log(1/\alpha_e)\sum_cW_c^2\right\}^{1/2},\quad
L_X=\max(0,\widehat X-h_e)\ \text{or}\ U_X=\min(1,\widehat X+h_e).
\]

The radius applies the independent-bounded-variable inequality of
[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830) to the registered weighted block
unit contributions. Hoeffding's result does not choose this project's endpoint inventory, alpha split,
ratio construction, or scientific rate thresholds; those remain prospective project decisions and
must pass R1a coverage simulation under the actual dependence design.

Only the direction actually enumerated is licensed. The binding availability lower bound is $L_A$;
the adherence lower bound is $L_J/U_A$; and the
conditional soft-copy upper bound is $U_K/L_A$. A zero denominator bound makes the endpoint
inconclusive. The union bound does not assume independence across painter/control conditions, but the
Hoeffding step does require independence across the registered units $c$. If G0 cannot give an
auditable argument for that partition, or one conservative common-shock unit makes the bound
uninformative, the affected rate endpoint is ineligible or inconclusive; request-level pseudo-
replication is forbidden. R1a must validate coverage under heterogeneous template probabilities,
the complete shared-vector dependence design, registered cluster sizes, batch outages, moderation
episodes, and backend common shocks. It may replace these displayed conservative bounds only in a
new protocol version, not after seeing research outputs.

For each named painter×scene-group and shared artist-free×scene-group endpoint, $L_A$ must be at
least 0.90 and $L_J/U_A$ at least 0.80. R1a also sets a minimum analyzable repetition count in every
fixed prompt template. Template-level availability, scene-group adherence, each of the five
realized-variable marginals, and all denominators receive the same frozen familywise treatment when
an interval is reported. A template below its frozen minimum return count makes the enclosing
scene-group endpoint fail. Differential-failure MNAR bounds that reverse a conclusion make that
endpoint inconclusive.

For the sealed real reference, the exact finite-population blind-agreement fraction with the frozen
eligibility scene group must be at least 0.90 per painter. Exact painter×scene-group agreement
fractions and all five-variable confusion tables remain mandatory diagnostics. Disagreements stay in
their frozen populations and appear in realized-content sensitivity; a failed threshold makes
the painter reference inconclusive rather than authorizing post-unblinding reassignment.

Copy rate uses the boundary-safe construction above and is binding at the painter level; scene-group rates are
mandatory diagnostics. Any exact or crop-level reconstruction prevents an unqualified `without
observed reconstruction` statement but does not erase the separately reported near-copy-excluded
distribution result. The simultaneous conditional upper bound $U_K/L_A$ for soft near-copy rate
must be no higher than 10% per painter and its point estimate no higher than 5%; both thresholds are finalized
before generation from detector operating
characteristics and R1a power. A stronger `copy rate below 5%` claim requires its upper bound, not
only its point estimate, to be below 5%.

### 10.5 Secondary prompt effect

The named-versus-painter-free distance change is secondary:

\[
\Delta^0_{a,F}=E_F(G^0_F,P^{C,*}_{a,F})-
E_F(G^N_{a,F},P^{C,*}_{a,F}).
\]

A positive value shows that the name moved the output distribution toward the target under this
prompt design. It cannot rescue failed absolute fit, coverage, or specificity.

## 11. Inference and generator-repetition simulation

The primary real reference is the fully measured sealed-confirmation finite population. Conditional
on that declared population there is no real-work sampling error, no inverse-probability weight, and
no real-work bootstrap. Digitization and source uncertainty are handled by the binding reproduction,
held-source, perturbation, and uniform-real analyses; they are not disguised as IID sampling noise.

Continuous feature and distance uncertainty uses 9,999 frozen nonparametric replicates and the same
auditable independence partition as Section 10.4. For a fixed deterministic local map, resample
complete seed condition vectors with replacement within each template; each vector carries all
painter-named conditions, the shared artist-free control, availability, content, copy status, and
features, and the independently seeded template lists are resampled separately. For an opaque or
remote endpoint, resample only the complete balanced common-shock unit vectors from Section 8.3;
each unit carries all $L$ waves and every template×condition outcome, failure, label, copy status,
and feature together. Never resample its requests, waves, templates, or conditions independently.
Both constructions preserve every fixed template's count; the 24 templates themselves remain a
finite census and are never sampled as prompt-superpopulation units.

Every replicate recomputes rate point values, the generated U-statistic, generated–real cross term,
coverage coordinates, specificity, copy outcomes, realized-content weights, and the complete joint
decision while the real population and its $q^*$ weights remain fixed. Binding availability,
adherence, and copy bounds nevertheless use Section 10.4's boundary-safe construction rather than
empirical-bootstrap quantiles. If the independence units cannot be aligned with this fixed-template
resampler, their independence cannot be defended, or a common shock crosses their frozen boundaries,
both the affected continuous and rate endpoints are ineligible or inconclusive; request-level
pseudoreplication is forbidden.

For endpoint $e$, let $T_e^{(r)}$ be its replicate value, $\bar T_e^*$ the replicate mean, and
$s_e^*$ the replicate standard deviation. The registered max statistic uses
$(T_e^{(r)}-\bar T_e^*)/s_e^*$ with the prespecified one- or two-sided direction. A zero empirical
variance is exact only when algebra proves that the endpoint is structurally fixed by design. Any
other zero or numerically degenerate variance makes that endpoint inconclusive and triggers more
prospectively registered repetitions or a stop; it is never assigned zero-width uncertainty.
Simultaneous bounds are centered on the observed $T_e$ with the frozen max-statistic critical value
and $s_e^*$. R1a freezes endpoint studentization, centering, degeneracy tolerance, quantile
convention, seed, and Monte Carlo error report before R1b.

This generated-resampling construction is prospective, not validated evidence. Before G0, R1a must
pass deterministic U-statistic and dependence fixtures and demonstrate point bias, simultaneous
interval coverage, equivalence power, copy/availability error control, and robustness to unequal
template return counts and registered pixel/feature common shocks under the full missingness
scenarios. If a fixture or operating-characteristic
simulation fails, the study increases registered generator repetitions within the frozen resource
ceiling or stops and issues a new protocol version; it does not switch to an unspecified analogue.
Development analyses remain developmental and cannot borrow the complete qualification or
confirmation populations.

The R1a simulation implements the entire R1b-gate-to-G1 decision path for each registered family,
not one endpoint at a time. It includes:

- exact target-distribution draws;
- location shifts;
- scale, tail, and multimodality changes;
- prototype collapse and neighbor mixtures;
- holding/capture-source shifts and reproduction noise;
- 5%, 10%, and 15% nonrandom refusal, including registered batch/outage/moderation common shocks,
  conservative independence-unit sizes, and common-shock location, scale, tail, and copy changes in
  the returned feature distributions; and
- near-copy contamination.

The qualification and confirmatory real population sizes, generator repetitions on the fixed
24-template frame, and margins must achieve:

- at least 80% joint probability, per painter-family, of passing its complete registered conjunction
  when every target-fit distance is at most \(\epsilon/2\), median shifts are at most 0.125 IQR,
  spread ratios lie in \([0.90,1.11]\), and availability/content/copy criteria hold;
- at least 90% probability of rejecting **every** margin-defining adverse alternative separately:
  coordinate and coherent location shifts, spread contraction/expansion, tail contamination,
  closest-neighbor mixture, prototype collapse, and registered dependence changes;
- at most 5% probability of any unsupported painter-family reproduction claim across the registered
  family, with a separate optional omnibus four-painter/all-family claim; and
- simultaneous confidence-interval width no larger than \(\epsilon/2\) for target fit and the
  corresponding half-margin for coordinate coverage.

Primary multiplicity control preallocates $\alpha_{cont}+\alpha_{rate}\le0.05$. One max statistic
over the continuous full-vector generated replicates controls the painter, qualified-family,
scene-group/template, competitor, distance, and coverage endpoints at $\alpha_{cont}$ while the
finite real populations remain fixed. Section 10.4's Bonferroni-Hoeffding construction controls all
registered availability, adherence, and copy-rate bounds at $\alpha_{rate}$; the union bound gives
strong control for their conjunction without assuming cross-condition independence. R1a freezes
the allocation, endpoint inventory, studentization, direction of each one- or two-sided endpoint,
and simultaneous critical-value construction. A closed/Holm analysis may be reported as sensitivity
but cannot replace or rescue a failed primary construction. R1a simulations include selection caused by the R1b qualification
gate, although the separately sealed final reference prevents qualification-reference reuse. Plots
and learned diagnostics do not enter winner selection.

## 12. Decision rule and reporting language

The literature does not validate a universal painter-fidelity score or this project's exact
conjunction. The following is therefore a **prospectively justified project decision rule**, whose
margins and operating characteristics must first pass R1a simulation.

For a given painter, model, and qualified feature family, the primary report may say that the model
reproduced that measured painter-feature distribution only when all of the following hold:

1. that prespecified family qualified on real-only data;
2. absolute target-fit equivalence passed for the common-content-standardized real population versus
   the fixed equal-24-template generated frame;
3. the prespecified median-coverage and spread limits passed;
4. every registered pair-specific neighbor margin passed;
5. the binding real-only source/reproduction gates, uniform-real sensitivity, and prespecified
   realized-content reweighting did not fail, become infeasible, or reverse the conclusion;
6. per-scene-group availability/adherence and per-template analyzable-repetition support passed;
7. the soft-copy-rate ceiling and the confirmatory near-copy-excluded analysis passed; and
8. experiment-wide error control and MNAR sensitivity passed.

If one component fails, report the components. Examples of allowed conclusions are:

- “Named prompts moved color features toward Monet, but did not reach the real-work equivalence
  margin.”
- “The generated center was close, but coverage and spread showed prototype contraction.”
- “Outputs resembled the Impressionist panel but were not specific to Sisley.”
- “The result is inconclusive because registered refusals reduced prompt-template support below the
  frozen minimum.”

Results are reported per painter, family, and exact model. “Across all three measured families” is
allowed only when all three families qualify and pass. A success for one family, painter, prompt
frame, or model does not generalize to untested features, painters, prompts, or generators.

## 13. Required artifacts

### R0a frame/randomization freeze and R0b locked-access record

- source snapshot and rights ledger;
- complete candidate and exclusion frame;
- content codebook, hashed eligibility derivatives, role firewall, and blinded adjudication;
- physical-work/capture/asset/derivative identity graph;
- four-scene/five-variable categorical, eight-constraint convex-hull, source-incidence, and frozen
  confirmation-population tables;
- development, qualification, sealed final-reference, and optional external partitions with
  historical-exposure labels;
- exact painter-level population assignments, CSPRNG ranks, and complete-census access receipts;
- the 12 byte-exact hashed candidate prompt frames and render functions, selected common-content
  target, nonnegative population weights, weight-cap/effective-sample-size diagnostics, and failure
  status;
- acquisition intents, attempts, and file inventory; and
- independent review with terminal go/no-go decision.

### R1a measurement/simulation freeze and R1b qualification result

- primary feature cards and deterministic fixtures;
- perturbation and source-transfer results;
- fixed-family qualification table;
- exact energy-distance, median, spread, tail-quantile, and diagnostic support estimators;
- exact generated-vector resampling, realized-content weighting, boundary-safe rate-bound
  implementation, fixtures, simulation code, scenarios, alpha allocation, margins, error-control
  rule, and required repetition count; and
- locked analysis package hash.

### G0 generation freeze

- exact model and runtime identity;
- verified selected 24-template text and render hashes, final scene-group counts, independent
  template-specific seed lists, within-template condition-sharing matrix, and request order;
- retry, refusal, admission, content-coding, and copy-audit rules;
- complete estimand table and report templates; and
- independent review stating whether generation may begin.

### G1a execution seal and G1b result package

- append-only request and attempt ledgers sealed before final-reference access;
- ignored raw-output inventory with hashes sealed before final-reference access;
- one-time final-reference unsealing record;
- blind content and copy adjudication;
- intention-to-generate availability, conditional-on-analyzable features, and content adherence;
- all primary, sensitivity, negative, and missing outcomes; and
- a claim-audit table mapping every sentence to a passed rule or explicit limitation.

## 14. Immediate next actions

1. R0a: freeze and run a reproducible metadata-only census across direct institutions plus the
   federated Wikidata/Commons discovery frame; verify item-level authority, rights, geometry, and
   capture ancestry, then acquire and seal the complete candidate frame before feature measurement.
2. Before active labels are read, hash 12 byte-exact candidate 24-template frames, including both
   renderings, placeholder/insertion contract, punctuation, language, and negative prompt. Create
   firewalled low-resolution eligibility derivatives; double-code four broad scene groups, the six
   narrow diagnostic categories, and five content variables; freeze source rules and the
   physical-work identity graph. Do not construct exact joint-profile real cells.
3. Keep the four-painter design **NO-GO** until at least 360 eligible internal candidates per painter,
   at least 24 in every broad scene group, the source-diversity gates, a shared candidate prompt
   frame whose eight-constraint weights pass in every population, and one valid CSPRNG partition.
   External replication is not a primary GO condition and requires 96 additional candidates per
   painter, at least eight per broad scene group, or 456 combined per painter.
4. Freeze the one finite frame, all populations, every content-standardization vector, and the
   separate at-least-32-work reproduction census; then release only the complete 288-work
   development population and auxiliary census. Preserve every sealed frame byte, exposure role,
   and tracked receipt.
5. R1a: freeze feature fixtures, reproduction/source-robustness margins, coverage panels, and the
   generated-vector resampling implementation; validate the frozen content estimands and simulate
   the full family-level decision to set generator repetitions.
6. R0b: release and measure all 432 qualification works while every confirmation work remains
   sealed. If the population census is incomplete, stop and begin a new protocol/R0a.
7. R1b: run untouched method qualification once while final-reference analysis files remain sealed. Continue
   only for prespecified families that pass; stop if none pass.
8. G0: select the exact primary generator with quarantined conformance prompts, verify the selected
   24-template hashes without editing them, and register the simulation-selected equal paired
   request count. The retired 1,920-request scenario is not executable under version 1.7; the exact
   count is $120R$ for four painters and must exceed the boundary and simulation floors.
9. G1a: while final-reference analysis files remain sealed, execute every request without output selection
   and seal all attempts, failures, outputs, and hashes.
10. G1b: open the final reference once, run the locked copy and feature pipelines, and report the
    two-part, near-copy-excluded confirmation.

Until R0a/R1a/R0b/R1b are complete, no generated-image request is authorized. That delay is not a change
of research question: it is the shortest defensible route to answering it without turning four
files, a classifier, or a prompt effect into a false painter-fidelity result.
