# `pilot_3` protocol

## Status and hard stop

**Scientific-protocol status: redesigned Freeze-A1 real-corpus specification assembled / all
pixel, external, and generation gates closed until their separately specified prospective
commits.**

This file is the immutable scientific protocol. Its raw bytes are bound by P3-T07 and it is
never edited to represent a later operational gate state. The sole mutable generation-
authorization record is `configs/pilot_3/generation_authorization.json`: it begins at `closed`
and may change to `preregistered_generation_gate_open` only after the canonical P3-T01 through
P3-T13 evidence—including the one-shot P3-T11 lineage—recomputes successfully. That record
cannot authorize a request by itself. Analytic generation additionally requires the matching
P3-T14 gate and the complete status/gate closure to be committed and clean.

This document freezes the real-corpus acquisition design and the already resolved Phase-B
design. Freeze A1 authorizes only development-training and development-calibration artwork
acquisition and A-vector extraction after the freeze commit. In particular:

- do not call an image-generation API, an image-generation browser interface, or an image
  proxy;
- do not send the one-shot P3-T11 neutral transport-qualification request before the exact
  P3-T08 Phase-A result passes and the committed, file-backed production gate verifies the
  strict authorization, documentation, runtime-fingerprint, and pre-Freeze-B closure for only
  that qualification window;
- do not acquire, inspect, or extract the museum-block external-holdout pixels until a committed
  Freeze-A2/P3-T07 token authorizes the exact unseal command;
- do not send an analytic image request until P3-T11 passes and the later Freeze-B/P3-T14
  generation gate opens; and
- do not substitute another artist, source, requested label, prompt, threshold, or sample
  size after its applicable freeze.

The development artwork-byte gate opens only when this document, the final corpus with 25
metadata-only `not_selected` candidates and zero replacement-eligible reserves, splits,
acquisition-intent contract, code, and tests are committed together. The
external and generation gates remain closed until every listed prerequisite is resolved and
verified. The operational status change and matching P3-T14 must be one explicit prospective
commit; a script result, credentials, or an open status file on its own cannot open a gate.

## Why `pilot_3` is a redesign

`pilot_2` is complete and remains immutable. Its 320 intended cells all reached a terminal
disposition: 315 returned analyzable PNGs and five were policy refusals. The refusals all
occurred in Paul Cezanne cells, leaving 251 of 256 named/control pairs complete. Under the
frozen complete-grid rule, all four primary hypotheses were therefore not tested and not
supported. Positive available-pair estimates are descriptive because availability was
artist-dependent and conditioning on returned images can induce selection bias. See the
[`pilot_2` report](../reports/pilot_2/REPORT.md).

The `pilot_2` learned-formal qualification passed on its fixed 40-work development atlas, but
that atlas was not an independent confirmation corpus. It also showed substantial artist
heterogeneity: Monet's specificity estimates were negative while the other artist estimates
were positive. The correct next step is neither to replace the five refusals nor to generate
more repetitions. It is to qualify the measurement on new real data and to define refusal as
an outcome in the future generated study.

The design has two sequential phases:

1. **Phase A — real-only measurement qualification.** Select the corpus without pixels or
   feature outcomes, then freeze the representation and test it once on an independent,
   source-held-out real set.
2. **Phase B — future generated-output study.** This phase may be designed and frozen only
   after Phase A has a terminal result. It separates availability from A-vector proximity and never
   replaces unavailable outputs.

Phase A failure is a completed scientific result. It does not authorize opening Phase B.

## Target and claim boundaries

The target unit is the **individual artist**, not an era, movement, school, or style-period
label. Era and movement remain provenance-bearing, cross-classified metadata. They may be
used for description or prespecified blocking, but they may not be substituted for artist in
the estimand. This study cannot support a claim about “Impressionism” as a population from a
small roster of artists.

The domain is public-domain paintings of landscapes and outdoor-place scenes. This domain is
defined by the frozen authority-metadata rule, not by a later visual impression. It permits
people, bathing, work, leisure, and buildings when the museum record explicitly classifies the
painting as a landscape or otherwise supplies the required outdoor-place evidence; it is not a
figure-free-landscape corpus. A human figure, a figure-bearing title, or a title alone is not an
exclusion rule. This deliberately broad scene definition is a source of composition
heterogeneity that must be reported, and it may not be narrowed after pixels or outcomes are
seen.

The frozen finite roster is Alfred Sisley, Camille Pissarro, Paul Cezanne, and Pierre-Auguste
Renoir.
The development sources are the Art Institute of Chicago (AIC) and Metropolitan Museum of
Art (Met). The sealed `museum_balanced` external cohort contains one work per artist from each
of three holding-institution blocks: Minneapolis Institute of Art, Dallas Museum of Art, and
Toledo Museum of Art. Each block remains an analysis and permutation stratum; the aggregate
source ID does not imply a shared capture pipeline. The reciprocal neighbor pairs are
Sisley--Renoir and Pissarro--Cezanne. They were chosen from art-historical/content-domain
relationships before pixels or features, not from A-vector separation or generator outcomes.

Every corpus row binds the exact official museum image asset. Wikimedia Commons may not supply
Pilot 3 image bytes or act as a fallback delivery path. Source images are acquired only for
internal noncommercial scholarly research and are not redistributed. A complete external block
shares one holding institution and official asset provider, but the study does not claim that
its four works share a camera, operator, capture date, calibration, or conservation-imaging
session.

The roster is purposively selected from a metadata-qualified finite candidate universe. Unless
a future protocol defines and executes probability sampling of artists, all artist-level
inference is conditional on the frozen roster and content blocks; there is no artist-
superpopulation claim.

The intended claims are deliberately narrow:

- Phase A may establish that one frozen measurement distinguishes the retained artists on
  new digital reproductions across the three held museum/provider blocks, under the recorded
  corpus and acquisition conditions.
- Phase B may estimate availability and, among usable matched pairs, frozen A-vector proximity
  under one frozen request/transport condition.
- Neither phase establishes artistic quality, authorship, copying, training-data inclusion,
  movement-level style, or performance on artists outside the frozen roster.

## Stage A0: metadata-only candidate and source audit

### Audited candidate universe and selected roster

The prior research supplies four anchor artists and five expansion candidates:

- anchors: Claude Monet, Alfred Sisley, Camille Pissarro, and Paul Cezanne;
- expansion candidates: Armand Guillaumin, Eugene Boudin, Gustave Caillebotte, Berthe
  Morisot, and Pierre-Auguste Renoir.

Before fresh authoritative collection and before any Pilot 3 pixels or features, the project
made the user-authorized purposive choice to advance four finalists: Sisley,
Pissarro, Cezanne, and Renoir. This retains two reciprocal, historically defensible comparison
pairs and uses prior project metadata research—not Pilot 2 effects, refusals, or feature
separation—to target a small real-data pilot. Monet was not advanced because prior project
metadata had no eligible Met cell under the common acquisition design. Guillaumin, Morisot,
Boudin, and Caillebotte were outside the two chosen pairs at the fixed four-artist budget.
Those five dispositions are not catalog-absence or source-feasibility claims.

The fresh authoritative audit therefore covers the four declared finalists, not all nine
earlier candidates. It normalizes their names and authority identifiers. The frozen design is
40 development works in a 4-artist x 2-source x 5-work grid plus 12 external works in three
complete one-work-per-artist holding-institution blocks. Neither the
older 8-artist x 3-source x 10-work aspiration nor the five unadvanced artists receive a fresh
feasibility result. This is a purposive finite pilot, not evidence of real-world absence or an
artist-population sample.

### Permitted inputs

Only metadata from authoritative collection or archive records may affect feasibility:

- artist authority identifier and attribution status;
- canonical work/accession identifier, title, creation-date interval, medium, and object type;
- source institution and stable landing-page or API identifier;
- source genre/subject terms needed to apply the common content-domain rule;
- rights statement, license, and public-domain status;
- physical dimensions and native pixel dimensions when published as metadata;
- image-service availability and declared file format, without downloading the image; and
- source access date and exact raw metadata-response hash.

The audit must not download artwork bytes, take screenshots, derive thumbnails, compute pixel
or embedding features, inspect visual quality, query a generator, or use any `pilot_2`
artist-specific effect/refusal result as a selection weight. A source's metadata API may be
queried; an endpoint that returns image bytes may not.

### Metadata eligibility and deterministic selection

A candidate record is eligible only if its metadata supports all frozen fields needed to
establish a distinct public-domain painting, the target artist attribution, the common content
domain, a research-permissible acquisition path, and a stable source identity. Ambiguous
attributions, fragments, studies after another artist, photographs, prints, and records whose
domain cannot be decided from metadata are excluded with reason codes. These rules must be
expressed in a versioned config before the audit result is emitted.

Canonical-work auto-union at this stage is permitted only through an authoritative identity:
a shared physical/canonical-work ID, Wikidata work ID, namespaced catalog ID, or authoritative
source-object cross-reference. Normalized artist, title, date, medium, and dimensions may flag
a pair for explicit review but may never auto-union it. The result remains provisional because
no image hashes are permitted. Suspected duplicates remain review groups and cannot be split
across later partitions until adjudicated. Pixel-based duplicate checking, when eventually
allowed, may remove or merge a group but may not choose among groups based on measurement
outcomes.

The development audit deterministically ranks eligible AIC and Met records by the frozen
metadata rule and selects exactly five works per artist/source cell. The external audit binds
the separately frozen official object record, accession, image-service identity, dimensions,
rights evidence, and exact asset URL for one work per artist in each of the Minneapolis,
Dallas, and Toledo blocks. All 52 selected physical works must be disjoint.

P3-T01 re-runs the eligibility decision over hashed authoritative AIC and Met metadata plus
the three official museum-block records, records source revisions/access evidence, and verifies
attribution, painting domain, public-domain or research-use status, governance, and acquisition
independence. Discovery metadata never authorizes Commons image delivery. The historic metadata
snapshot is retained only as a regression input. No threshold was changed after pixel
inspection.

### Phase-A corpus architecture

The development design is a complete 4 x 2 x 5 artist-by-source grid. The external design is
three complete four-row holding-institution blocks with exactly one work per artist in each
block. Artist labels are permuted independently within blocks, and confusion and performance
diagnostics are reported by block and asset provider. Sources that merely expose the same
upstream digital file through different URLs would count as one source.

After Stage A0 succeeds and a separate Phase-A acquisition plan is frozen, the real corpus is
partitioned at the physical-work level:

- **development-training:** fits preprocessing parameters, the learned representation's PCA,
  and artist reference centroids/classifier;
- **development-calibration:** chooses only choices explicitly left tunable by the Phase-A
  freeze and then closes them; and
- **external holdout:** 12 works in three complete, independently governed museum/provider
  blocks, excluded from every fitting, threshold, representation, and artist-roster decision.
  Its metadata may determine prospective roster feasibility and balance.

No physical work, alternate reproduction, crop, or likely derivative may cross partitions.
The finite artist roster, neighbor graph, content-domain construction rule, source roles, and
work allocation must be frozen from metadata before any Phase-A pixels or feature outcomes are
opened. The neighbor graph may not be selected later from A-vector separability because it
defines the future specificity contrast. The external holdout's metadata may be used to
establish eligibility and balance, but its
artwork pixels, feature vectors, and labels joined to predictions remain sealed until the
Phase-A analysis code and decision thresholds are frozen. Its source is selected by the
metadata-only deterministic rule, not by feature performance.

Freeze A1 retains 25 metadata-only candidates as `not_selected`, but contains zero
replacement-eligible reserves and no replacement path for either partition. After that
freeze, any metadata, rights, acquisition, corruption, input-domain, or provenance failure
closes the affected Pilot 3 path rather than authorizing a substitution. A new allocation
requires a new protocol and untouched holdout; an unfavorable distance, classifier error, or
source-shift result can never trigger replacement.

No eligible, authority-linked, independently produced same-work reproduction subset exists
for every corpus cell. Nor do the external institutions publish common camera/session ancestry
for all four works in a block. The study therefore makes neither a same-session nor a cross-
digitization-robustness claim. Every A-vector result is conditional on the exact content-hashed
official museum bytes and frozen preprocessing pipeline.

## Phase A: real-only measurement qualification

### Common safeguards

Before external-holdout unsealing, Phase A must freeze and hash:

- every source response and selected metadata row;
- canonical identities, deduplication adjudications, and work-level splits;
- rights and input-domain reviews;
- native and standardized-image byte hashes after acquisition is authorized;
- all preprocessing, feature, model-weight, dependency, device, and RNG provenance;
- the expected width and height of the exact delivered representation for every selected
  work; acquisition fails before persistence if decoded bytes disagree with either value;
- every museum GET uses bounded streaming with ambient proxy discovery disabled
  (`trust_env=false`); the frozen response limit is 134,217,728 bytes (128 MiB), and either
  an oversized `Content-Length` or streamed overflow terminates the attempt as the
  non-retryable `response_too_large` outcome without persisting partial bytes;
- all dimensionality-reduction, classifier, distance, resampling, and test code;
- every qualification threshold and failure rule; and
- the exact external-holdout unseal command and expected input manifest hash.

Any learned transform is fitted on development-training data only. Calibration data may be
used only as declared in the frozen tuning plan. External-holdout results are evaluated once.
A qualification failure cannot be repaired against the same opened holdout; a redesign needs
a new protocol version and a new untouched external holdout.

### Primary candidate: harmonized A-vector

The primary representation candidate is the project-defined, deterministic harmonization of
the Kim et al. A-vector used in `pilot_2`: common lossless sRGB normalization, pinned 512 x 512
resizing, a pinned Stable Diffusion 2.0 VAE state, content-derived posterior seed, explicit
latent scale, a 4 x 64 x 64 float vector flattened in C order, and PCA fitted only on real
development-training works. This is a method-compatible project representation, not the
authors' unpublished RNG realization.

Kim et al. report materially stronger artist, style-period, and temporal structure for their
CLIP-family contextual vector than for the A-vector. The A-vector is therefore a deliberately
weak formal baseline, not a paper-backed measure of broad artistic style or artist identity.
Without a separately frozen independent evaluator or blinded-human validation, Phase-B claims
must use the operational term **A-vector proximity**, not “artist fidelity” or “style fidelity.”

The exact representation version is not inherited silently. Phase A must rebind the source
revision, checkpoint/tensor hashes, environment, preprocessing code, seed derivation, dtype,
and PCA algorithm. All 40 development vectors must carry one identical extraction-runtime
fingerprint; every external and generated vector must match that complete P3-T07 fingerprint,
not merely the model hashes or device label. The PCA component rule must reach its frozen
variance target without using the external holdout and without a post-result component-cap
change.

The prospective harmonized primary input rule resolves the paper/source low-resolution
discrepancy conservatively: native width and height must each be strictly greater than 410
pixels, the native long/short aspect ratio must be strictly below 2, and the released-code
predicate `width * height > 410 * 410` must also be recorded. The two-dimensional rule is a
project choice based on the paper's dimensional description; the area predicate is behavior of
the released source. Neither may be attributed to the other or relaxed after acquisition.

At minimum, the A-vector gate requires:

- exact repeatability for a prespecified, artist- and source-stratified probe set;
- complete eligible support for every selected artist in every retained source and split;
- finite vectors and exact provenance for every retained work;
- a frozen development classifier and distance geometry that beat `1 / K` artist chance on
  the untouched external blocks, where `K` is the frozen number of artists;
- validation on untouched held-block real works of the exact downstream `d(x, a)`, distance
  normalization, reference-source weighting, centroid/distribution estimator, and every frozen
  target-versus-neighbor contrast that Phase B would use. Every reference is fitted only from
  development-training works; the held-block query work and its reproductions are never
  included in their own or any other validation reference;
- the prespecified exact block-constrained permutation result and effect-size requirement on
  the external holdout;
- no artist's external-held performance falling below a prospectively frozen floor;
- reported block/provider diagnostics and per-block confusion matrices; and
- an explicit cross-digitization disposition. Independent same-work reproductions, if an
  eligible balanced set exists, receive a prespecified distance analysis. If they do not,
  the gate may qualify only proximity conditional on the exact frozen acquisition bytes; it
  may not support cross-digitization robustness, broad artist/style fidelity, or authorship
  attribution. Pooled artist classification never substitutes for cross-acquisition validity.

The external gate uses a 0.25 strict chance floor for balanced accuracy, a 0.20 minimum recall
for every artist, and a strictly positive mean target-versus-neighbor margin. Its exact null
permutes the four artist labels independently within each complete holding-institution block:
`4! = 24` assignments per block and `24^3 = 13,824` assignments overall, exhaustively including
the observed assignment. No global shuffle, Monte Carlo draw count, or permutation seed may
replace that enumeration. Classification and neighbor-margin tests use Holm familywise alpha
0.05. PCA reaches 95% development-training variance subject to the
`n_training - 1` rank cap. Eight exact repeat probes cross every artist with each development
source. Calibration must exceed 0.25 balanced accuracy and have a positive mean
target-neighbor margin before Freeze A2. Passing qualifies only the frozen A-vector proximity
construct for the finite roster, sources, and exact digital-image contract.

### Lee chromatic method: standalone pass or retire

The Lee et al. method is not a co-primary rescue metric. It receives one standalone,
paper-compatible replication decision before Phase B:

1. identify and provenance the exact Figure 1 source bytes (or author-confirmed byte-identical
   copies); a merely similar or independently digitized reproduction may support an explicitly
   adapted validation but can never earn a Lee-replication `pass`;
2. require native support for the frozen resolution series without upsampling and complete
   border, partial-capture, damage, painting-medium, color-management, and crop review;
3. freeze CIE Lab conversion, horizontal/vertical adjacency, mean rescaling, full empirical
   distribution comparison, scalar seamlessness, numerical tolerances, and aggregation;
4. have two independent reviewers record concordance between the implementation, the paper's
   stated method, and the digitized Figure 1 targets before the result is opened; and
5. run the frozen replication once.

The status must be exactly one of `pass`, `retire`, or `ineligible_retire`. `pass` requires the
exact source fixture and the prespecified full-distribution behavior—not merely the scalar
formula, a look-alike reproduction, or synthetic unit tests. If the source fixture is
unavailable, the status is `ineligible_retire`; if the exact eligible fixture fails, it is
`retire`. A separate adapted validation may be reported under that name but cannot replace the
Lee result. Lee retirement does not convert an A-vector pass into a failure; it removes Lee
from Phase B's measurement package.

### Optional blinded human validation

Human validation is optional only until the Phase-A freeze. The protocol must then bind one
of two terminal choices:

- `excluded`: no human-validity claim is made; or
- `included`: a separately approved, consented, power-checked, and preregistered blinded
  protocol is completed as specified.

A real-only module may ask raters, blinded to source and computational scores, to match held
works to target versus neighbor reference sets. If a generated-output module is planned, its
sample, randomization, questions, exclusions, rater-quality rules, analysis, and multiplicity
must be frozen before any generated output is unsealed; raters must be blinded to named versus
control assignment and transport condition. Human results are convergent-validity evidence.
They cannot rescue a failed A-vector gate or be added after observing automated Phase-B
effects.

## Design sensitivity and final sample-size selection

The selected Phase-A allocation is 52 works: for every artist, four AIC plus four Met works
are development-training, one AIC plus one Met work is development-calibration, and one work
from each of the Minneapolis, Dallas, and Toledo blocks forms the external holdout. It is
justified as a block-restricted external-transport qualification design, not an 80%-power
claim.

The initial deterministic sensitivity artifact remains an assumption-labeled diagnostic. The
final P3-T04 resolution selects a budget-constrained estimation pilot rather than making a
power claim. Its design maximizes distinct content blocks subject to the 320-request budget,
four frozen artists, one shared artist-free control, four nested repetitions, and one requested
label. It retains the following requirements:

- enumerate candidate numbers of artists, content blocks, and repetitions rather than report
  only the favored grid;
- preserve artist and content-block clustering and treat repetitions as nested precision
  units, not independent top-level observations;
- include artist heterogeneity at least as large as the qualitative `pilot_2` pattern;
- simulate artist-dependent refusal/availability, including concentration in one artist;
- require every frozen artist to contribute usable pairs and diagnose both the minimum
  per-artist availability and cross-artist availability disparity;
- show null calibration, familywise error, Monte Carlo uncertainty, exact-test resolution,
  expected usable-pair counts, and power/precision across a declared scenario grid;
- apply the exact proposed multiplicity and overall-decision algorithm inside every draw;
- replace raw per-artist availability/disparity and point-estimate reversal diagnostics with
  the final simultaneous one-sided interval or hierarchical decision rules inside every draw;
- label all quantities borrowed from `pilot_2` as development inputs rather than confirmatory
  estimates; and
- use a fixed seed, a frozen draw count, and a self-hashed result.

For the single requested-label stratum with one shared artist-free control, the request count
is `(4 + 1) * 16 * 4 = 320`. The 16 content blocks maximize content diversity under the frozen
budget. The study reports uncertainty and finite-schedule sensitivity; it does not assert a
minimum detectable effect or 80% power.

The simulation addresses the generated-output grid only. The real-corpus allocation is
separately bound by P3-T05 through P3-T08 and the exact external classifier, permutation,
effect-size, and per-artist rules above.

## Phase B: future generated-output design

### Frozen requested label and transport claim boundary

Official OpenAI documentation accessed on 2026-08-31 lists a dated GPT Image 2 snapshot, but
the audited local OAuth implementation accepts only the aliases `gpt-image-1` and
`gpt-image-2`. Pilot 3 therefore freezes exactly one scheduled requested label,
`gpt-image-2`. The dated snapshot is not silently substituted. The estimand is the exact
requested-label pipeline, not attested upstream execution identity. See the official
[GPT Image 2 model page](https://developers.openai.com/api/docs/models/gpt-image-2).

The official [`gpt-image-1` model page](https://developers.openai.com/api/docs/models/gpt-image-1)
labels it deprecated and describes it as the previous image-generation model. It is retained
only as historical `pilot_2` context and is not a prospective `pilot_3` condition.

Every `pilot_3` GPT Image request must use the pinned `/Users/fred/dev/openai-oauth` checkout
through a dedicated loopback listener at `http://127.0.0.1:10533/v1/images/generations`. The
transport recognizes no image-model aliases beyond `gpt-image-1` and `gpt-image-2`, while the
Pilot 3 primary analytic schedule is restricted to exactly 320 `gpt-image-2` calls. No direct-
API, browser, second analytic stratum, or silent alias/snapshot fallback is permitted. A
successful response establishes only that the requested label was accepted through this route.
P3-T11 binds request bytes, source/runtime fingerprints, account authorization, and that claim
boundary. The dedicated launcher's `--models gpt-image-2` value controls its advertised model
catalog; it is not endpoint-level allowlisting. The endpoint implementation accepts both image
aliases, while Pilot 3's canonical client validation permits only `gpt-image-2` study requests.

P3-T11 is exactly one separately ledgered, non-analytic transport-qualification request. It
may occur only after the exact self-hashed P3-T08 result is `pass`, while the Freeze-B/P3-T14
generation-gate artifact is still absent, and after the canonical committed file-backed gate
recomputes P3-T07/P3-T08, verifies the strict self-hashed authorization/documentation records,
and returns literal `True`. The supported production path is `pilot3 authorize-transport`,
`pilot3 capture-oauth-runtime`, commit those exact evidence files, then
`pilot3 qualify-transport`; an arbitrary caller assertion is not a production authorization.
It uses request ID
`p3-t11-neutral-transport-qualification-v1`, requested label `gpt-image-2`, the frozen
`pilot3-generation-v1` transport configuration and runtime fingerprint, the dedicated
`127.0.0.1:10533` listener, and the following prompt:

> Create one original abstract image composed only of a centered blue circle, a small red
> square, and two pale gray horizontal bars on a plain white background. Use flat colors and
> simple clean edges. Do not depict a landscape, a person, an artist, an artistic style, or a
> recognizable existing artwork. Do not include text, lettering, a signature, a watermark, a
> border, a frame, or a collage.

The canonical request SHA-256 is
`dc887cb518e2df74f0ca150cb5545569300dfe0a060cc3ca6b55e2a19ea5d1df`. Its sole durable
pre-POST intent is written to
`artifacts/pilot_3/transport_qualification_post_intents.jsonl`; its sole terminal attempt is
written to `artifacts/pilot_3/transport_qualification_attempts.jsonl`; a qualifying PNG is
stored content-addressed below `outputs/pilot_3/transport_qualification`; and the self-hashed
result is `reports/pilot_3/evidence/transport_qualification.json`. The physical POST budget is
one. No response or transport failure is retried. Interruption after the intent is
indeterminate and prohibits blind resend. The request is outside the artist/content grid,
does not count in the 320 analytic requests, and can never enter feature fitting or outcome
selection. A pass establishes requested-label acceptance and strict output eligibility only;
it does not attest an upstream snapshot or authorize analytic generation by itself.

### Frozen prompts and grid

Phase B will use matched named-artist and artist-free prompts within content blocks. Prompt
wording, negative constraints, content annotations, repetition identities, request parameters,
and deterministic schedule must be fixed before the first analytic request. Outputs are never
selected by visual quality. The artist-free control is shared within a content-block,
repetition, and request-condition cell only when the frozen pairing map explicitly does so.

Artists are crossed with content blocks. Content blocks and artists are independent top-level
sampling dimensions; repetitions stabilize cells but do not create new artists or contents.
The roster and neighbor graph are frozen above. Sixteen content blocks, four repetitions,
the exact named/control template, one `gpt-image-2` requested-label stratum, and all 320
requests are frozen in P3-T12. Prompts differ only by insertion of the named-artist clause;
outputs are never visually selected.

The frozen `p3-b16-r01-control` row is the first of those 320 analytic requests after P3-T14
opens. It is a fail-stop runtime image preflight/revalidation and remains an assigned analytic
artist-free control. It is not a transport-qualification request and cannot resolve P3-T11. If
that cell reaches any terminal result that fails the preflight, no later grid request is sent.
Its real intent/attempt rows are retained, while every untouched scheduled cell receives a
separate `not_sent_global_stop` row in
`artifacts/pilot_3/generation_global_stop_dispositions.jsonl`. Those rows explicitly record
zero physical POSTs and cannot be represented by synthetic attempt rows.

### Terminal outcomes and retry identity

Every logical request receives exactly one final category in an intention-to-request ledger:

- usable image;
- policy refusal;
- non-retryable client response;
- malformed or ineligible successful response;
- retry-cap technical failure;
- indeterminate after interruption; or
- not sent because a prospectively defined global safety/transport stop fired.

Policy refusals and other non-retryable 4xx responses are substantive availability outcomes.
They are never retried, paraphrased, or replaced. Technical retries are permitted only for the
exact transient exception/status classes, maximum attempts, delays, and jitter rule frozen
before unsealing. Every retry repeats byte-identical semantic request content; all intents,
attempts, responses, request IDs, timings, and terminal dispositions are retained. An unmatched
durable send intent after interruption becomes `indeterminate_after_interruption` and is never
blindly resent because the request may have executed.

Immediately before every physical POST, including every technical retry, the runner performs a
fresh live OAuth process/source/health/catalog revalidation against the frozen fingerprint. The
complete self-hashed revalidation evidence is embedded in the append-only send intent and copied
into its attempt record. The committed per-request gate then runs as the final check immediately
before that intent is fsynced; any failed or mismatched revalidation produces no intent and no
image POST.

Execution evidence counts observed POST exchanges separately from durable intents whose POST is
indeterminate. Only a cell with no durable intent may be labeled as having zero physical POSTs.

The global-stop ledger is an immutable, self-hashed no-POST ledger, not an attempt ledger. Its
cell identities, T12 schedule hashes, generation-grid/schedule hashes, failed-preflight hash,
and attempt/intent prefix counts must recompute exactly. A stopped cell must have neither a
POST intent nor an attempt receipt/row. After the ledger exists—even when the preflight is the
only scheduled cell and the ledger is therefore zero bytes—the generation runner and every
per-request gate remain permanently closed for that Pilot-3 schedule.

Retry success may be reported separately from first-attempt success, but it is not converted
into evidence that a refusal was “fixed.” Any safety-wide stop rule must apply without looking
at artist-proximity outcomes.

## Two-part generated estimand

Phase B separates whether a request produces usable evidence from what that evidence shows.
It does not require a complete feature grid and does not pretend unavailable images have
feature vectors.

### Part 1: availability

For each assigned cell, let `U = 1` only when a response passes the frozen decode, format,
geometry, and provenance contract; otherwise `U = 0`. Report cell availability and matched-pair
availability (`U_named * U_control`) under the full intention-to-request denominator.

The primary availability estimand is the artist-equally-weighted probability that a matched
named/control pair is usable under the frozen request condition. Artist-specific probabilities,
refusal categories, first-attempt availability, and content-block effects are required
secondary results. The 16 content-block values are the top-level units; repetitions are first
averaged within artist/content cells. One-sided Bonferroni Student-t bounds cover one aggregate
lower bound, four artist lower bounds, and twelve ordered artist-difference upper bounds
(family size 17, alpha 0.05, 15 df, critical value 3.206719988802892). The aggregate lower
bound must be at least 0.90, every artist lower bound at least 0.80, and every ordered
cross-artist availability-difference upper bound at most 0.15. High proximity among a
selectively available subset cannot compensate for failure of an availability rule.

### Part 2: A-vector proximity conditional on availability

For a usable named/control pair targeting artist `a`, let `d(x, a)` be distance from generated
output `x` to the frozen Phase-A development-training reference distribution or centroid for
`a`, and let
`n(a)` be the frozen neighbor. Retaining the `pilot_2` orientation:

`Delta_target = d(control, a) - d(named, a)`

`Delta_specificity = [d(named, n(a)) - d(named, a)]
                     - [d(control, n(a)) - d(control, a)]`.

Positive values favor the named request. The co-primary conditional-proximity estimands are the
artist-equally-weighted means of these quantities among usable matched pairs. They must be
reported explicitly as conditional on availability, with usable/assigned denominators for
every artist and content block. A conditional estimate is not an intention-to-request effect.

Reference-source inclusion, source weighting, centroid/distribution estimator, and distance
normalization must be fitted on Phase-A development-training data only and frozen before the
external holdout is opened. Neither holdout performance nor generated outputs may select or
refit the representation, PCA, scale, neighbor map, reference sources, or reference geometry.
The external holdout validates this exact fixed query-to-development-reference operation; it is
never merged into the later Phase-B reference.

### Missingness bounds

Raw Euclidean improvements are unbounded, so finite worst/best-case bounds cannot honestly be
claimed for their full-grid means. Before Phase B, each proximity outcome will therefore also
have a monotone bounded sensitivity score

`Z_j = tanh(Delta_j / tau_j)`, for `j` in `{target, specificity}`,

where each positive scale `tau_j` is computed by an exact, frozen rule from Phase-A
development-only real distances. Thus `-1 <= Z_j <= 1` without estimating a missing image's
feature.

With prespecified nonnegative cell weights `w_i` summing to one, observed usable set `O`, and
unavailable set `M`, the full-assignment partial-identification bounds are

`lower_j = sum(i in O) w_i * Z_ij - sum(i in M) w_i`

`upper_j = sum(i in O) w_i * Z_ij + sum(i in M) w_i`.

Weights must preserve equal artist and content-block contribution and be frozen before any
output. Report these deterministic worst/best bounds for the realized finite assignment
schedule plus prespecified artist-pattern and
refusal-reason sensitivity analyses. Do not impute A-vectors, assume missing at random, replace
refusals, or present a complete-case confidence interval as a full-grid interval.

If the worst-case bound crosses zero, any favorable conclusion is limited to usable outputs.
Only a positive worst-case lower bound can support a missingness-robust claim for bounded `Z`
over the realized finite assignment schedule. It never establishes a bound for the unbounded
raw Euclidean improvement, broad artist/style fidelity, or expected behavior over new generator
draws or prompts. A stochastic-generator claim would additionally require a frozen one-sided
sampling procedure and multiplicity adjustment around the partial-identification lower bound,
with its operating characteristics included in the final simulation.

## Inference, multiplicity, and decision rule

The unit structure is crossed, not flat: artist and content block are top-level dimensions;
repetitions are nested within their cells; matched named/control outputs remain paired. The
analysis uses equal artist and content-block weighting. For each conditional endpoint its
standard error is the root-sum-square of artist- and content-block marginal standard errors.
The two one-sided co-primary lower bounds use Bonferroni alpha 0.025 each and 3 df (critical
value 3.18244630528371). This is a finite-roster, finite-content estimation rule; it does not
generalize to an artist superpopulation.

The two conditional-proximity hypotheses form one co-primary family and receive the frozen
familywise adjustment (the design-sensitivity implementation currently evaluates a
Bonferroni family of size two). Availability is a separate primary requirement against a
prespecified minimum, not a favorable proximity observation and not a denominator chosen after
seeing refusals. If more than one request condition, contrast, human endpoint, or confirmatory
subgroup is added before freeze, the multiplicity family must expand before power simulation.
Artist-specific, source-specific, chromatic, prompt-category, and first-attempt analyses are
secondary unless explicitly promoted before freeze.

At minimum, an overall conditional A-vector-proximity result is supported only if:

1. the A-vector passed Phase A on the untouched external real source;
2. the frozen aggregate, per-artist, and artist-disparity availability rules pass;
3. both conditional target and specificity improvements have positive familywise lower bounds
   and multiplicity-adjusted tests passing the frozen alpha;
4. no prospectively designated source or artist diagnostic violates its frozen reversal rule;
5. all assigned requests have a terminal, verified ledger disposition; and
6. claim wording states whether the finite-schedule missingness bounds pass or whether the
   result is limited to usable outputs; no stochastic missingness-robust claim is made unless
   its separate one-sided procedure was frozen and simulated.

Artist-harm diagnostics use eight one-sided simultaneous bounds (four artists x two endpoints),
Bonferroni familywise alpha 0.05, 15 df, and critical value 2.836627476094133. Harm is present
only when an artist/endpoint upper bound is strictly below zero; a negative point estimate is
not enough. The terminal decision is `supported` only when availability passes, both adjusted
conditional lower bounds are positive, no simultaneous harm rule fires, and both bounded
finite-schedule lower bounds are positive. `mixed` and `unsupported` are defined in P3-T13.
Any terminal result is scientifically complete and cannot trigger more samples, changed
prompts, new exclusions, or a second model in this pilot.

## Freeze, unseal, and amendment rules

### Freeze 0 — metadata audit

Before running the metadata-only audit, freeze its source list, query snapshots or response
hashes, authority normalization, inclusion/exclusion rules, deduplication, development-ranking
rule, exact external block roster, tie-break, and result schema. Running this audit does not
authorize pixel acquisition or image generation.

### Freeze A1 — real-corpus acquisition

After a feasible metadata result and before any artwork pixels are acquired or inspected,
commit the exact corpus (including the 25 metadata-only `not_selected` candidates and zero
replacement-eligible reserves), work-level partitions, independent-provider block
assignments, rights and acquisition rules, technical input-domain checks, deduplication
procedure, finite-roster estimand, neighbor graph, content-block construction rule, justified
Phase-A sample allocation, and intention-to-acquire ledger contract. Freeze A1 permits
acquisition and development-only work
for the development-training and development-calibration partitions. It does not permit
access to external-holdout pixels or features. No selected row or complete external block may
be replaced after this freeze.

### Freeze A2 — external real validation

After development-only measurement work is complete and before external-holdout pixels or
features are acquired, opened, or joined to outcomes, commit the final representation, Lee
rule, human-validation disposition, thresholds, reference-source inclusion/weighting and
centroid/distribution estimator, design-sensitivity result, analysis code, tests,
environment/evidence contract, and all development inputs and results. A machine-
readable Phase-A validation gate must bind their semantic and file hashes plus the expected
external metadata manifest. Before unsealing, the verifier reconstructs the PCA, centroids,
development metrics, thresholds, and P3-T07 payload from the immutable development ledgers and
requires bit-exact state arrays and an exact self-hashed result.

The only command that may begin external access is `pilot3 unseal-external` with the exact
committed P3-T07 self-hash. Before its first network request it creates, with create-once
semantics and an `fsync`, `artifacts/pilot_3/external_unseal_receipt.json`, binding the token,
configuration, expected external identities, manifest hash, and Freeze-A2 Git commit. The same
process then performs external acquisition, A-vector extraction, and P3-T08 evaluation without
an intermediate operator decision. Separate external acquire, extract, or first-evaluation
commands fail closed, and a process-lifetime exclusive lock prevents concurrent runners from
issuing duplicate GETs or interleaving ledgers. After interruption, only the exact receipt-bound transaction may resume;
the token cannot be consumed for a changed configuration, manifest, code closure, or holdout.
P3-T08 is accepted only when it is reconstructed from the frozen state and exact external
ledgers, including its permutation results and gate checks. Any outcome-driven change after
unseal is a new protocol version with a new untouched holdout.

### Freeze B — generated-output study

Freeze B is permitted only after Phase A records an A-vector `pass`, P3-T11 records `pass`, and
Lee records `pass`, `retire`, or `ineligible_retire`. P3-T11 occurs in its narrow post-P3-T08,
pre-Freeze-B window; it is not an analytic grid request. Before the first analytic generation
request, commit:

- the exact model/request-label string and authorized route;
- model-documentation capture, the shared runtime fingerprint, and the separate one-shot
  transport-qualification evidence;
- prompt and pairing manifests, schedule, request parameters, and total grid;
- runtime fingerprint and allowed retry/terminal classification;
- all preprocessing, feature, reference, estimand, bounds, inference, multiplicity, stopping,
  and report code;
- the frozen sample-size/design artifact and approved request budget; and
- the exact open `configs/pilot_3/generation_authorization.json` transition record and a
  generation-gate artifact binding it, this immutable protocol, all hashes, and every verified
  prerequisite.

No analytical generated output may be inspected before that commit. After unseal, outputs and
terminal failures are accepted in the frozen schedule without visual selection. Changes to an
estimand, roster, prompt, model, retry class, sample size, feature, threshold, or exclusion
create `pilot_4`; they do not amend an opened `pilot_3`.

## Binding artifact obligations

Each row below is a binding obligation. The authoritative metadata rerun resolves `P3-T01`,
the machine recovery resolves `P3-T02`, and the final Phase-B design artifact resolves the
sample-allocation decision required by `P3-T04`; the older sensitivity artifact remains
diagnostic evidence rather than the final selection. `P3-T03` continues to record a closed
generation gate. Presence of an artifact is not the same as satisfying its downstream gate.
A path names the sole canonical artifact that may resolve the item; prose or an uncommitted
console result is insufficient.
Each JSON artifact must carry a schema/version, normalized input identities, deterministic
self-hash, and explicit status. `P3-T03` binds their file/semantic hashes to the planning
implementation file hashes; later freeze/gate artifacts must bind the narrower code closure
they execute. No deterministic artifact may contain a live wall-clock creation time; a source
timestamp is allowed only when supplied as an externally pinned input.

| ID | Required resolution | Canonical artifact | Required before |
|---|---|---|---|
| `P3-T01` | Metadata sources, query evidence, eligibility config, observed/unobserved candidate universe, dedup summary, development artist-by-source counts, exact external museum-block roster, deterministic selection result, and separate Freeze-A1 readiness | `reports/pilot_3/evidence/artist_source_feasibility.json` (`pilot3_artist_source_feasibility/1.0`) | any artwork-byte acquisition |
| `P3-T02` | Machine-check recovery of every `pilot_2` quantity reused by planning, plus the key terminal counts, refusal pattern, available-pair estimates/test statuses, and qualification result; no manual or favorable-result substitution | `reports/pilot_3/evidence/pilot2_baseline_recovery.json` (`pilot3-pilot2-baseline-recovery/1.0`) | accepting any `pilot_2`-derived design input |
| `P3-T03` | Self-hashed planning index binding this draft and every planning artifact, its semantic/file hash, verification status, and the still-closed generation state | `reports/pilot_3/planning_index.json` (`pilot3-planning-index/1.0`) | declaring the planning computation complete |
| `P3-T04` | Generated-output candidate grid, conservative scenario grid, clustering/refusal model, exact-test resolution, familywise simulation, request budget, and either a criterion-passing design or an explicitly budget-constrained estimation design with no power claim | `reports/pilot_3/evidence/design_sensitivity.json` plus the resolving `reports/pilot_3/evidence/phase_b_design.json` | final request-grid selection |
| `P3-T05` | Final artist roster, authority IDs, development sources, three complete official external museum/provider blocks, common domain, exact selected works, 25 metadata-only `not_selected` candidates, zero replacement-eligible reserves, no-replacement rule, rights boundary, deterministic selection explanation, and justified Phase-A allocation | `data/manifests/pilot_3/corpus_selection.jsonl` plus `reports/pilot_3/evidence/corpus_selection.json` | Freeze A1 |
| `P3-T06` | Physical-work deduplication, development/calibration/external split, three complete one-work-per-artist blocks, official-asset binding, exact within-block permutation space, and holdout seal | `data/manifests/pilot_3/real_splits.jsonl` plus `reports/pilot_3/evidence/holdout_seal.json` | Freeze A1 and any artwork-byte acquisition |
| `P3-T07` | Rebound A-vector representation, paper/source input-domain discrepancy and frozen intersection, development-only reference estimator, weights/environment hashes, exact thresholds, external analysis code, and Phase-A validation gate | `reports/pilot_3/evidence/a_vector_protocol.json` | Freeze A2 and external-holdout unseal |
| `P3-T08` | One-shot external A-vector result with pooled, artist, museum-block/provider, exhaustive `24^3 = 13,824` within-block permutation, reproduction, leakage, and provenance results | `reports/pilot_3/evidence/a_vector_external_validation.json` | any Phase-B design freeze |
| `P3-T09` | Exact Lee inputs/reproduction mismatch, native resolution/domain review, digitization tolerances, two reviewer records, and terminal `pass`/`retire`/`ineligible_retire` | `reports/pilot_3/evidence/lee_replication.json` | Freeze B |
| `P3-T10` | Human-validation terminal choice; if included, approval, sampling, blinding, instrument, power, exclusions, analysis, and multiplicity | `reports/pilot_3/evidence/human_validation_disposition.json` | applicable phase unseal |
| `P3-T11` | One separately ledgered neutral request after P3-T08 pass and before Freeze B: exact `gpt-image-2` canonical request bytes, dedicated port 10533 route, account authorization, documentation capture, shared analytic transport configuration/runtime fingerprint, output hash/PNG/strict-geometry evidence, one-POST/no-retry rule, interruption handling, and requested-label-only claim boundary | `reports/pilot_3/evidence/transport_qualification.json` plus `artifacts/pilot_3/transport_qualification_post_intents.jsonl` and `artifacts/pilot_3/transport_qualification_attempts.jsonl` | Freeze B/P3-T14; no request is authorized by this draft |
| `P3-T12` | Frozen prompts, artist-free pair map, binding to the already-frozen neighbor graph and content-block rule, exact blocks, repetitions, parameters, and deterministic schedule | `data/manifests/pilot_3/prompts.jsonl` plus `data/manifests/pilot_3/schedule.jsonl` | first analytic image request |
| `P3-T13` | Exact aggregate/per-artist/disparity availability rules, `tau` rules, cell weights, conditional-proximity tests, finite-schedule versus stochastic missingness target, reversal rules, simultaneous intervals, alpha, and multiplicity | `reports/pilot_3/evidence/analysis_contract.json` | Freeze B |
| `P3-T14` | Hash closure over the raw immutable protocol, exact open operational-authorization record, code, tests, configs, Phase-A result, transport evidence, manifests, design artifact, analysis contract, and budget approval; both the status record and gate must be committed and clean | `configs/pilot_3/generation_authorization.json` plus `reports/pilot_3/evidence/generation_gate.json` | first analytic image request |

`P3-T01` through `P3-T04` are offline planning/design artifacts and may be produced
independently or concurrently, but none by itself authorizes artwork-byte acquisition. Freeze
A1 requires their relevant inputs to be reconciled and verified plus `P3-T05` and `P3-T06` in
one committed closure. The generation gate remains closed until `P3-T01` through `P3-T13`
recompute, the operational authorization record is deterministically transitioned to
`preregistered_generation_gate_open`, and that exact record plus P3-T14 are committed together.
The scientific protocol file never changes status. A missing artifact, hash mismatch,
ambiguous status, dirty path, or undocumented mutation means closed.

## Current decision

The authoritative metadata work froze 52 selected works. AIC and Met supply 32
development-training and eight development-calibration works; 12 works in the three complete
Minneapolis, Dallas, and Toledo blocks remain the sealed external holdout. The manifest retains
25 metadata-only candidates as `not_selected`, with zero replacement-eligible reserves and no
post-freeze replacement. The exact external null exhausts `24^3 = 13,824` label assignments by
permuting artist labels independently within each block. The generated study is a
budget-constrained 320-request estimation pilot with 16 content blocks, four nested
repetitions, four named conditions, one shared control, and one requested label. It makes no
80%-power claim.

The immediate authorized action after—and only after—the Freeze-A1 closure is committed is to
acquire and extract the 40 development works, run the eight exact repeat probes, and fit the
development-only frozen state. The external museum-block bytes, neutral transport
qualification, and all analytic generation remain closed. A qualifying development result plus
the Lee and human
dispositions may form Freeze A2; only a one-shot external pass can open the separately
authorized P3-T11 window, and only a P3-T11 pass can then enter the Freeze-B/P3-T14 closure.
