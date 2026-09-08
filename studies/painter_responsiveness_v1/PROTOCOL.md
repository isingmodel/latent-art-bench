# Painter responsiveness v1

Prospective implementation of the [mechanism proposal](../../docs/RESEARCH_IDEA_20260908.md).
Issued 2026-09-08 after the user requested implementation and a test of the hypothesis.
New namespace: `painter_responsiveness_v1`. Earlier censuses remain terminal.

## Question and claim

Does a painter-name clause attenuate a requested muted/vivid color difference
relative to an additional generic style clause, and does any attenuation make
independently supported reference properties harder to reach?

The hypothesis can fail. Evidence of a feature interaction is not proof of an
internal model prior, human-perceived style failure, or an explanation of the
entire original/generated discrepancy. Findings will be reported regardless of
direction, including failed manipulations and imprecise results.

This protocol follows Protocol 2.1's separation of metadata, reference access,
measurement qualification, prospective generation and confirmation. It defines a
new finite-response study, not a resumption of v1's four-painter equivalence claim.
All retained references and vectors are already exposed development evidence.
They cannot be relabelled as unseen confirmation. The latest user instruction
authorizes implementation and bounded research execution; scientific prerequisites
below still have to be supported by actual evidence.

## Stages

| Stage | Allowed work and output | Requirement for following stage |
| --- | --- | --- |
| D0 | Read saved numeric vectors/metadata; publish descriptive diagnostics, simulation and all failed feasibility checks | Source/config/input bindings from a clean committed tree |
| R0 | GET-only current provider contract and budget; no image API POST | Retained timestamped responses and a closed preflight receipt |
| H0 | Prepare blinded tasks and normalized previews of the already exposed 70 references; open no new reference images | Exact source identities/hashes and task/codebook freeze before materializing previews |
| H1 | Actual consenting human reference annotation and vividness ratings | Named responsible human, declared recruitment/consent/storage plan, raters and assignments; no invented or LLM-substituted judgments |
| M0 | Establish fine-content-supported reference ranges and meaningful response margin; evaluate precision | Independent coding, reproducible target membership, capture limitations, fixed margin and a proceed decision |
| G0 | Freeze all 192 requests, order, transport, retry, budget and inference contracts | R0/H1/M0 evidence and feasible blinded generated-image assessment |
| G1 | Execute bounded, staggered parallel generation; preserve every attempt | G0 committed, no unresolved predecessor state, remaining budget |
| C0 | Measure every returned output, analyze the frozen factorial, prepare/collect human judgments | Terminal collection receipt; missing outputs remain missing; no visual selection |

No newly acquired paintings or independent capture pairs are authorized by this
initial implementation. Such acquisition requires a successor scope with exact
source/identity/rights/capture bindings. A derivative of a retained photograph is
not an independent capture. H0's preview processing is solely stimulus preparation,
not a new scientific feature extraction or visual eligibility decision.

## D0: exposed-data diagnosis

Read the unchanged, hash-bound controlled and revision inputs. Use the frozen
31-feature transform. Main descriptive comparisons use primary512/original31,
equal brief weights, and the same 24 briefs on each route. This differs deliberately
from the previous painter-specific broad-content weights. Export every brief's
named-minus-free mean displacement and coordinate/family contributions.

Report empirical within/between-brief components. Distinct-repetition cross-products
are additional signed diagnostics: under independent zero-mean repeat errors and
a stable service they estimate stable between-brief signal, but those assumptions
are unverified. Never clip negative cross-products or label them population
variances. No naive OLS attenuation coefficient, new confirmatory p-value or claim
of deconvolved painter style is permitted for this post-result stage.

Reference chroma support includes raw values and one common primary-development
scale across all three retained pipelines, exact work IDs, content labels and
per-work processing changes. Sparse free-text labels are not independent fine
content validation. Source/capture/human status must be explicit.

## M0 and the planned generation design

The config fixes six prospective templates, two in each broad scene class, one
route (FLUX.2 Max through the named provider, no fallback), four styles and two
polarity instructions. All eight style × polarity cells are randomized jointly
inside each of 24 template/repetition blocks; block order is also randomized.
The total cap is 192 images, not a power justification. Painter-free and generic
controls are shared across the two painter contrasts. No seeds are claimed to be
supported by this endpoint unless its inspected contract explicitly supports them.

The primary coordinate is development-scaled `chroma_median`. Let d(c) denote
vivid-minus-muted response in a condition. The primary family comprises
kappa(Monet)=d(Monet)-d(generic) and kappa(Cézanne)=d(Cézanne)-d(generic), averaged
equally over six fixed templates. Named-minus-free and generic-minus-free are
secondary diagnostic links. The generic clause is a particular added instruction,
not a perfectly neutral or semantically matched control.

With complete outcomes, calculate four repeated block contrasts per template,
then template means and the equal-template mean. Use template-stratified variance
and shared-control covariance. Approximate Welch–Satterthwaite t inference assumes
independent repeat blocks within fixed templates. Report Bonferroni simultaneous
two-endpoint intervals and Holm-adjusted p-values, clearly labelled approximate
model-based inference. This is not an exact randomization test of a weak interaction
null, and does not generalize six templates into a population of prompts.

Show every arm distribution, template contrast and availability count. A negative
interaction is attenuation in median chroma over these two instructions only if
the generic control responds positively and the free condition confirms that the
manipulation works. Do not delete templates on that basis. Baseline shifts,
nonlinearity, median aggregation and service state remain rivals. The ultimate
interpretation requires reference reachability and human judgments. The functioning
check uses a zero response threshold; the human-defined meaningful margin refers
to the named-minus-generic interaction. Compare its simultaneous interval with
minus that margin descriptively, without introducing another p-value family.

If any scheduled endpoint is missing, withhold primary numerical inference.
Report availability for all slots and complete-block *selected* descriptions with
no inferential p-values/intervals. A successful technical retry of the identical
payload under the prospective policy is part of its registered slot; both attempts
remain visible. Refusals are never rewritten into successes by altering the prompt.

A responsible human must declare minimum endpoint power and maximum p90
simultaneous-interval half-width before G0. The implementation requires the lower
Monte Carlo power bound and the width criterion to pass in all three declared
noise scenarios when both painter interactions equal the negative meaningful
margin. Partial-null simulations remain reported; this power gate does not
guarantee that power when only one painter changes. Current provider/key/credit
metadata must be no older than
24 hours when preparing G0 and starting collection; this age limit does not
invalidate retrospective measurement or replay.

The initial effect grid (0.25, 0.5, 1 primary-development IQR units) is a sensitivity
analysis, not an established meaningful margin. Simulate from centered retained
within-brief residuals with small-repeat variance correction, disclose the generic
arm's artist-free noise proxy, and include larger-noise and partial-null scenarios.
Actual human/reference validation must fix a meaningful margin and a precision
decision before paid generation. Insufficient precision can stop the study; it
does not authorize a larger unbounded sample or a weaker success criterion.

## Transport and cost

Use at most two concurrent requests with at least five seconds between starts,
all through one frozen provider. Each slot receives at most one identical-payload
technical retry, with at most six retries overall. Only completely received
429/500/502/503/504 technical errors with understood cost are eligible; no retry
of refusals, malformed successes, uncertain delivery or unknown charges. Stop
dispatch after three failures among the most recent eight completed attempts,
or any unresolved billing/delivery outcome, and diagnose before a successor.

The earlier recorded conservative amount is $45.6819185 of a $75 overall ceiling.
This study additionally caps new spending at $20, subject to current account
credit, current prices and a conservative $5 reservation for each in-flight paid
request. Reservations protect uncertain outcomes and are released only when a
terminal cost is known. No provider fallback, quality-regeneration or night schedule.
Every collection is terminal when its receipt is written; a stopped collection
is not resumed in place. Source, config and all request bytes are committed before
the first POST. Standard tests are offline; any live call is explicit execution.

## Human and reference interpretation

Use the separate codebook and blinded task generator. Human answers must be actual
responses with consent, registered rater/task assignment and provenance; synthetic
test records, maintainer pilots and independent validation remain distinguishable.
No messages or recruitment invitations are sent by this implementation. The
responsible human must determine applicable institutional requirements before
recruitment; software does not certify an ethics determination.

Compare perceived vividness without prompts, adherence with scene instructions,
and painter resemblance with identified reference panels. Do not reveal generated
condition or source identity through filenames. Period and capture provenance
require documentation, not visual guesses. Ranges used to specify the experiment
cannot simultaneously be described as independent held-out confirmation.

Reports separate computational support, human support, capture support and overall
mechanistic interpretation. Any unavailable component remains pending. Reviewers
of this implementation are maintainer-run LLM subagents, not independent human
or institutional reviewers. No paper conclusion will be upgraded without results.
