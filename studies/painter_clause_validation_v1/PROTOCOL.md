# Prospective painter-clause validation — version 1

**At issuance: prospective protocol awaiting offline qualification, review and source/input freeze. Live collection is permitted only after all qualification and committed-freeze gates below have passed; mutable operational status is recorded separately.**

## Scientific question and scope

The user authorizes one new bounded OAuth-only experiment, with no human ratings
and no additional paid image calls. The scientific question is whether a named
painter clause improves the proximity of generated images to a fixed painting
panel beyond an actual generic landscape-painting clause. Earlier Study 1 compared
named with artist-free prompts; the generic clause appeared only in the separate
palette experiment. This study adds that actual-clause comparison without palette
instructions, on new fixed scene briefs.

The two primary endpoints are Monet-minus-generic and Cezanne-minus-generic
weighted V-energy differences. Actual generic outputs are attainable service
outcomes, whereas the historical feature maps are diagnostic coordinate objects.
The experiment can support either named or generic superiority, or leave the
comparison unresolved. A generic clause is not assumed equally informative or
equally constraining as an artist name. This is not a mediation experiment, a
test of internal model mechanisms, or an equivalence design.

The scene frame and analysis were selected after earlier project findings, but
before any images from these new prompts are generated or inspected. Historical
results motivated the hypotheses. Only the new outcomes are prospective; neither
references nor the choice of question are unexposed. No old/new observations are
pooled. All four painters remain in the existing paper; this new controlled
comparison concerns Monet and Cezanne only and does not replace the four-painter
exploration. Nothing in this successor qualifies the unfulfilled full reproduction
gates of canonical Protocol 2.1 or reopens an earlier terminal collection.

All study design, implementation and reviews are by LLM agents operated by the
same maintainer. The protocol/scenes author previously supplied literature,
structure and methodological advice for the manuscript, including the moment-map
and centering diagnostics. This is not independent human or institutional review.
No guaranteed power, publication outcome or review score is claimed.

## Fixed scene frame and selected allocation

Use every one of the 24 briefs in [scenes.json](scenes.json), eight in each of
`water`, `built` and `land`. Each brief has three repetitions under four arms:
`free`, `generic`, `monet`, `cezanne`. The allocated total is therefore
24 x 3 x 4 = **288 outputs**, forming 72 four-request scene/repetition blocks.
Free and generic observations are shared across both painter comparisons.

A candidate ceiling of 24 scenes x four repetitions x four arms (384 outputs)
was considered before collection. The selected 288-output design preserves all
24 scenes and uses three repeats. Its selection is based on a separate offline
precision comparison using historical proxy observations; the qualification
record must preserve that comparison and its assumptions before freeze. This
protocol makes no numerical power claim. Proxy noise need not describe the new
generic arm or new scenes. No new outcomes may select sample size, endpoints,
scene exclusions, processing pipelines or stopping rules.

The author read all 24 original detailed and short Study 1 briefs in
`configs/painter_distribution_study_v1/research.json` and all six palette scenes
in `configs/painter_responsiveness_v2/study.json`. The new briefs avoid exact
repetitions and substantive restatements of those scene layouts. They omit
painter/place names, iconic identifying cues such as water lilies, and style,
brushwork or palette instructions. Generic subject terms shared with historical
landscape painting cannot make a brief artist-neutral in every model.

New subjects and arrangements include tidal pools, a frozen lake, exposed
landforms and outdoor structures other than the earlier houses and village
streets. These changes are intentional scene transfer within a fixed three-class
frame; they are not verified content matching to individual reference paintings.
The briefs are authored, not randomly sampled from a defined scene population.
Class labels describe requested content and are not independently adjudicated
image-adherence labels. No images were inspected to select or revise these briefs.

Every brief record has exactly `brief_id`, `content_class` and `detailed` fields.
The top-level scene file declares schema `painter-clause-validation-scenes/1`
and status `prospective-fixed`. IDs, spelling, punctuation and order are source
inputs. All 24 IDs are used; no balanced-prefix selection remains active.

## Exact prompt construction

Use the detailed Study 1 prompt core, without the palette experiment's additional
layout-preservation sentence. Construct the UTF-8 string by joining these parts
with one ASCII space, omitting an empty style clause:

1. `Create an oil painting on canvas.`
2. The arm clause below, if nonempty.
3. `Scene: ` immediately followed by the brief's exact `detailed` text.
4. `Render only the painting area, without a surrounding frame, signature, letters or watermark.`

| Arm | Exact clause |
| --- | --- |
| `free` | Empty string |
| `generic` | `In a traditional landscape-painting style.` |
| `monet` | `In the style of Claude Monet.` |
| `cezanne` | `In the style of Paul Cezanne.` |

The ASCII spelling `Paul Cezanne` deliberately matches the original Study 1
renderer and the historical OAuth maps. The palette study used an accented
spelling; its generic clause is reused exactly, but its palette text and extra
closing sentence are not. Do not silently normalize names or punctuation,
rewrite briefs, expand prompts, add negative prompts, or supply reference images.

The example free prompt for `pcv_water01` is:

> Create an oil painting on canvas. Scene: A waterfall descends through a cleft in a rock face into a pool below. The falling water and pool occupy the center of the view, with ledges on either side and loose stones at the near edge. Render only the painting area, without a surrounding frame, signature, letters or watermark.

The named and generic variants insert only the corresponding style sentence
between the opening and `Scene:`. The frozen inventory contains every complete
payload, not just its construction recipe.

## Service, assignment and measurement

Use only the source/process-bound local OAuth route `oauth_gpt_image_2`, requested
model `gpt-image-2`, with the existing request contract: one image, requested
1024 x 1024, medium quality, PNG, opaque. The route is a requested service, not
an attested immutable checkpoint. No OpenRouter or other paid fallback is allowed.

Independently randomize the four condition positions within each scene/repetition
block and randomize the order of the 72 complete blocks. Use a bound design seed
and retain the generated assignment table. Finish the current block, including
any permitted technical retry, before admitting a request from another block.
The concrete seed, run ID, endpoint/process identity and full assignment order
must be present in the source-bound configuration before inventory freeze.

At most two requests may be active, with starts at least five seconds apart.
Random order does not establish independent backend states. Treatment-dependent
duration or service carryover can violate the no-interference assumption below.
Record intent, admission, completion and retry timestamps and actual order.

Use the exact 38 Monet and 32 Cezanne Study 1 reference observations and existing
development-only scalers, bound by their numerical input hashes. The corresponding
reference content masses are 21/38, 4/38, 13/38 for Monet and 3/32, 11/32, 18/32
for Cezanne, in water/built/land order. Do not acquire new reference images,
re-extract old reference pixels, refit scalers or reannotate the panels.

Measure the first valid output from every successful slot using the unchanged
extractor in exactly three existing pipelines: `primary512`, `resolution256`
and `jpeg90_512`, with all 31 coordinates in each. Only primary512 supports the
two primary tests. The other two pipelines are fixed descriptive processing
sensitivities. No feature omissions, family rescaling, common-square view,
learned representation or further grid is part of this protocol.

Retain supported opaque delivered images with both dimensions at least 512 even
if delivered size, aspect ratio, supported format or reported quality differs
from the request. Delivery is part of the service-response estimand. Report those
fields by arm; do not filter, match, adjust or retry based on visual appeal,
style, requested-scene adherence, feature values or valid delivery differences.
Retain raw response, encoded image and normalization hashes. Container/contract
validation is operational; scientific feature extraction starts only after the
collection is terminal. No human ratings or scientific visual selection occur.

## Two primary estimands and conditional inference

For painter p, let X_p be the fixed reference panel, N_p the new named outputs
and G the shared new generic outputs. The two primary estimates are

`Delta_p = Ehat(X_p, N_p) - Ehat(X_p, G)`.

Use the unchanged weighted V-energy statistic, including all reference/generated
cross-distances and both within-distribution terms. References receive equal
weight within their painter panel. Each generated observation in class c receives
weight q_pc/(8 x 3), where q_pc is the reference panel's fixed class mass. Thus
G has the same pixels in both comparisons but different painter-specific energy
weights. Retain this dependence; do not create independent copies of controls.

Each endpoint uses the 72 allocated named/generic pairs sharing scene and
repetition. Condition on the positions of the other two arms in each four-request
block. Under independent randomized positions, the two compared labels are
uniformly assigned to the remaining positions. Use the existing exact
paired-contribution identity for energy, 99,999 Monte Carlo sign assignments,
two-sided absolute extremeness with conservative ties, and the plus-one
correction. Bind separate endpoint seeds before collection. Apply Holm to exactly
these two p-values at family level .05; an unavailable endpoint occupies its
position with p=1. Retain raw and adjusted p-values and paired contributions.

The sharp null for each contrast is that exchanging its named and generic labels
changes neither availability nor measured features at any assigned position,
under the fixed transport/retry policy and no interference. This is conditional
randomization inference for these assignments and references, not a random-scene,
oeuvre-wide, session-population or internal-mechanism test. Do not manufacture an
energy-effect confidence interval or invoke the palette Welch estimator here.

A negative contrast with a Holm rejection supports named superiority over this
generic clause; a positive contrast with rejection supports generic superiority.
Unresolved positive and negative estimates are reported separately. Non-rejection
does not establish equivalence, generic sufficiency, or absence of a name effect.
No meaningful-effect or equivalence threshold is introduced after results.

Any missing or invalid planned primary measurement withholds the endpoint that
requires it: a missing generic observation affects both endpoints; a missing
named observation affects that painter. Do not infer the allocated-grid result
from a renormalized complete subset. A missing free observation affects its
secondary diagnostics, not an otherwise complete named/generic endpoint.
All planned denominators and statuses remain reported. Duration and identity
gates apply to the entire collection. Nonprimary pipelines cannot rescue a
failed or unavailable primary comparison.

Both primary tests additionally require the terminal receipt's explicit
`identity_contract_met=true`. This is a conservative global service/identity
contract: final source/process checks must pass after all active responses drain,
and no source/process change, authentication/account/endpoint contract failure,
uncertain or unsupported delivery, unrecognized backend error or collector
interruption may have occurred. These failures withhold both tests even when
the named/generic measurement pairs happen to be complete. Ordinary missing
measurements retain the pair-specific rule above. Deadline/storage or recognized
technical-error stopping does not by itself assert an identity failure; its
duration and completeness consequences remain applicable. The numerical replay
checks the receipt against the retained terminal and operator records.

## Controlled secondary descriptions and fixed historical predictions

These analyses are specified before new collection but introduce no additional
confirmatory test family, selected thresholds, equivalence claims or optimized
feature view. Report them for all four arms in all three all31 pipelines when
their allocated inputs are complete. Otherwise mark the affected summary
unavailable and preserve the available observations separately.

1. **Absolute energy and spread:** report each arm's energy to each painter panel,
   generic-minus-free and named-minus-free energy changes, population-form total
   trace, generated/reference trace ratio, and generic/free and named/generic
   trace ratios. These additional energy comparisons have no randomization
   p-values. Distinguish equal-scene summaries from reference-content weighting.
2. **Conditional variation and retrieval:** report observed within/between-scene
   trace decomposition and the existing finite-repeat-corrected B* and N* under
   both reference-content and equal-scene weights. Use R=3, unbiased within-scene
   covariance and the established correction; retain negative estimates without
   truncation. Its conditional-mean interpretation assumes stable zero-mean
   errors independent across repeats and scenes. Retrieve each held-out repeat
   against centroids from the other two repeats, with all 24 scene candidates
   and the eight same-class candidates. Queries have equal scene weight and
   overlapping centroid-training sets; they are not independent Bernoulli trials.
3. **Fixed original OAuth maps:** before collection, fit one historical T1/T2 pair
   per painter and pipeline from all 72 original detailed OAuth outputs per arm
   under the original reference-content weights. T1(y)=y+mu_N-mu_F;
   T2(y)=mu_N+a(y-mu_F), a=sqrt(V_N/V_F)>0. Bind fitted means, traces, scalars,
   input memberships and source before generating any new image. These full
   OAuth fits must not be substituted by existing FLUX transfer maps, averaged
   fold maps or fits to the new cohort. Reference feature vectors do not fit the
   maps; reference-derived class masses remain explicit.
4. **Map evaluation targets:** apply these unchanged maps to all new free outputs
   and report their reference energies beside actual free/generic/named energy.
   Compute the established cross-repeat corrected conditional-mean residual Q_T
   against the corresponding actual named arm for T1 and T2. Record T2-minus-T1
   differences for both targets. The correction removes held-out repeat noise
   under its assumptions, not uncertainty in historical map fitting. Map scores
   are prospective predictions on new scenes, but maps are not randomized
   treatments: do not permute map labels or reuse clause randomization p-values
   as tests of their difference. No evaluation-dependent centering, scalar
   optimization, new fit, cross-validation search or map selection is permitted.

Do not add a redundant joint own/cross-painter alignment claim for the common G
cloud: identical generic outputs used for both names make its joint interaction
cancel algebraically. Individual energy and conditional comparisons above are
the scientific targets. Coverage, new classifiers, palette interventions,
post-hoc scene deletion grids and additional model families are outside this
prospective protocol. Any later diagnostic would require a disclosed successor.

## Transport, terminality and accounting

The cumulative paid ceiling remains $75 and the preceding conservative project
accounting of $50.7219185 remains historical. This study allows **zero new paid
calls**, uses OAuth only, and assigns no artificial monetary price to subscription
usage. It does not use the remaining paid credit or alter old budget ledgers.

The allocation is 288 first attempts plus at most eight qualified technical
retries, giving **at most 296 attempt intents**. Permit at most one identical-
payload technical retry for a slot. Retry only a complete error-only response
with a matching numeric 429/500/502/503/504 code, or the exact previously qualified
OAuth plain-text 503 contract. Preserve failed bodies. Refusals, uncertain
delivery, malformed/unsupported success and image-quality preferences do not
qualify. Delay at least 60 seconds and honor a supported Retry-After of up to
300 seconds; larger/invalid requirements stop the run rather than alter policy.
Keep retry decisions, intent admissions and actual POST counts distinct.

Stop new admission and drain active requests after uncertain delivery,
unsupported success, authentication/account/endpoint errors, source/process
identity changes, three failures in the latest eight completed attempts,
inadequate 5 GiB disk reserve, an unsupported retry delay, or exhaustion of the
attempt/retry limits. Preserve every intended and completed attempt. Do not
silently switch endpoint, provider, model or payload to complete the grid.

A ninth needed technical retry stops admission. Successfully using the eighth
retry does not cancel remaining first attempts. A slot's second technical failure
is retained without a third attempt; other slots may continue unless the global
failure-cluster or another stop rule applies.

The collection must finish within 24 hours of its first dispatch. Stop admission
five minutes before that deadline; drain in-flight requests and report actual
elapsed time. If drainage exceeds 24 hours, withhold both primary tests while
retaining observed estimates descriptively. A closed, failed, interrupted or
timed-out collection cannot resume, refill missing slots, or restart under the
same run ID. A future retry of the scientific study requires a new reviewed
namespace/run and disjoint paths, not repaired evidence in this one.

The 24-hour limit is an inference-eligibility and admission contract, not a
guaranteed wall-clock termination time. The HTTP client's 240-second timeout is
an inactivity timeout; a response that continues arriving can take longer. The
five-minute reserve cannot guarantee timely drainage, and the actual terminal
duration determines eligibility.

## Required qualification before any live action

The coordinating maintainer must complete and record all of the following:

- Preserve the offline design/precision assessment and its proxy assumptions,
  including why 288 rather than 144 or 384 outputs was selected. Do not treat
  simulation as observed new-arm variance or guaranteed power.
- Review the fixed scenes for substantive reuse of the two specified old prompt
  inventories, exact prompt construction and the interpretation of class labels.
- Implement meaningful offline tests for assignment and conditional pair positions,
  exact prompt strings, two-endpoint Holm behavior, missingness/duration gates,
  accounting, technical retry/terminal boundaries, fixed-map binding and the
  existing measurement/analysis contracts. An artificial full 288-slot workflow
  must qualify without network or image-service access.
- Obtain precollection methodological and implementation reviews with explicit
  maintainer-run LLM and implementation-involvement disclosures. Resolve material
  failures before source commitment and preparation.
- Commit clean protocol, fixed scenes, configuration, source and tests. Prepare
  a create-once freeze binding that source commit, runtime/proxy identity,
  historical numeric inputs, full original OAuth maps and all 288 payloads and
  assignments. Commit the resulting inventory/freeze before opening the live gate.
- Run the appropriate targeted offline tests, Ruff, full offline suite and
  applicable evidence verification. Verify that no old bound inputs changed.
  A direct live action requires the recorded successful stage gates, not merely
  the prospective status of this document.

## Reporting and reproduction

Keep append-only request/attempt/slot records and create-once terminal results in
the new namespace. Measure only after collection closes. Report both primary
endpoints irrespective of direction or availability, all specified secondary
descriptions, delivery fields by arm, exact exclusions/statuses, source/input
hashes, assignments and timing. Separate request-contract verification, raw-byte
authentication and numerical replay.

Public numerical reproduction must identify the exact new archive and replay
entry point only after actual release and verification. Retained vectors cannot
authenticate absent raw pixels. Existing public assets, scientific protocols,
hash-bound reports and ledgers remain unchanged. A positive outcome does not
validate human-perceived style, semantic adherence, physical brushwork or a
population of artists, scenes or backend states. An unresolved outcome must not
be converted into a claim that the experiment established generic sufficiency.
