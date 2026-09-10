# Cezanne versus generic clause: one prospective successor

**Status: fixed prospective design awaiting source qualification and freeze.
No successor live gate is open.** Namespace `painter_clause_successor_v1`;
run `pcsv1-20260910`. The availability-triggered rationale and involvement
disclosures are in [DESIGN_DECISION.md](DESIGN_DECISION.md).

## Question, allocation and unchanged inputs

This single successor asks whether actual Cezanne-clause outputs differ in
reference proximity from actual generic-clause outputs. The predecessor
`painter_clause_validation_v1/pcvv1-20260910` has a known nonretryable,
error-only HTTP 400 `moderation_blocked` refusal at
`c:pcv_built04:r00:cezanne`. Its original Cezanne endpoint remains unavailable.
This study neither reopens that collection nor fills its missing slot.

Generate **96 new outputs**: every one of the predecessor's 24 scene briefs,
eight per water/built/land class, with two repeats under each of `generic` and
`cezanne`. The 48 two-request scene/repetition blocks each contain both arms.
Randomize the two positions independently across blocks and randomize block
order, using a seed and full assignment table committed before freeze. Finish
each block, including any permitted retry, before admitting the next block.
Both arms are generated afresh; no predecessor output enters this comparison.

Use these unchanged source inputs, bound by path and SHA256:

| Repository-relative input | SHA256 |
| --- | --- |
| `studies/painter_clause_validation_v1/scenes.json` | `4e24a570336f2b6cd28ad1f9312a944e545ae811c5db8f353b01d257d349951e` |
| `studies/painter_clause_validation_v1/inputs.json` | `4bd002c9319410946e7bedc5b6397e019cd2485e15f16b693259e3a7675e0280` |
| `studies/painter_clause_validation_v1/PROTOCOL.md` | `87d6dfae4746f7bc4028c4ea5e7dc5678ef7874cce065bac5b75623dfe68a91e` |

Do not copy/edit the scene inventory, omit `pcv_built04`, rewrite any brief or
change its class. The scenes are fixed authored prompts, not a probability sample
or independently adjudicated content matches. Reuse the exact 32 Cezanne
reference vectors and development-only scalers in the numerical input for each
pipeline; verify equality of any successor input subset to these source objects.
No references are acquired, re-extracted, relabeled or used to refit a scaler.

Construct each prompt by joining with one ASCII space:

1. `Create an oil painting on canvas.`
2. `In a traditional landscape-painting style.` for generic, or
   `In the style of Paul Cezanne.` for Cezanne.
3. `Scene: ` followed by the unchanged brief's exact `detailed` text.
4. `Render only the painting area, without a surrounding frame, signature, letters or watermark.`

No palette instructions, extra layout sentence, reference images or rewritten
name spelling are added. The full 96 payloads and assignments are frozen inputs.

## One primary comparison

For fixed reference panel X and the new Cezanne/generic clouds C and G, estimate
`Delta = Ehat(X,C) - Ehat(X,G)` using the unchanged full weighted V-energy
statistic, including cross-distances and both within-cloud terms. References
receive weight 1/32. The fixed class masses are water 3/32, built 11/32 and
land 18/32; each generated observation in class c receives **q_c/16**.

Use all **48 allocated scene/repetition pairs** in `primary512`, with all
31 features. The existing weighted paired-contribution identity supplies
99,999 independent Monte Carlo sign draws, seed **2026091052**, two-sided
absolute extremeness, conservative ties and plus-one correction. Report the
unadjusted p-value and reject only when **raw p <= .025** and every eligibility
gate passes. Retain the 48 ordered pair identities and contributions. No effect
confidence interval, equivalence margin or meaningful-effect threshold is added.

The sharp null exchanges C/G labels without changing availability or measured
features at any assigned position, under the frozen transport/retry policy and
no interference. This is conditional assignment inference for fixed prompts and
references. Randomized positions do not establish independent backend states or
exclude duration-dependent carryover.

Original Monet retains its unchanged predecessor Holm-two procedure, with the
unavailable original Cezanne p-value represented as one; its applicable raw-p
threshold is therefore .025. A joint .05 bound for original Monet and successor
Cezanne uses their two .025 levels and the union bound, without independence
between collections. It requires valid null p-values under the relevant
conditioning, including the prior availability-triggered decision; nominal alpha
accounting alone does not establish service/randomization validity. Do not pool
observations, recompute the original family, test an across-cohort painter
difference, or identify an isolated time effect. The successor threshold stays
.025 even if original Monet also becomes unavailable. No alpha is recycled.

Any missing/invalid primary measurement withholds the allocated-grid endpoint;
no complete-case renormalization is permitted. Complete estimates remain
descriptive if a global terminal gate fails. Primary inference additionally
requires literal `duration_contract_met=true` and `identity_contract_met=true`,
validated against the retained terminal/operator evidence. No secondary pipeline
can rescue an unavailable primary result. Negative/positive estimates with
rejection support the corresponding measured ordering; non-rejection establishes
neither equivalence nor generic sufficiency.

## Delimited secondary reporting

For C and G in `primary512`, `resolution256` and `jpeg90_512`, always using all
31 coordinates and the same reference-content weights, report only:

- Each arm's absolute reference energy, observed population-form total trace and
  generated/reference trace ratio.
- The C/G observed-trace ratio.

There are no secondary tests or intervals. An arm summary requires that arm's
complete allocated inputs; a ratio requires both relevant quantities and a
positive denominator, otherwise it is explicitly unavailable. Preserve all
measured observations and statuses. Do not add free-arm comparisons, maps/Q,
corrected conditional-variance components, retrieval, palette tests, new feature
views, reference perturbations or outcome-dependent diagnostics. This two-arm
study cannot restore the predecessor's Cezanne/free map target.

## Transport, terminality and reporting

Use only the source/process-bound `oauth_gpt_image_2` route, requested
`gpt-image-2`, one 1024-by-1024 medium-quality PNG with opaque background. Retain
the first valid supported opaque output with both dimensions at least 512;
valid geometry/format/reported-quality differences remain service outcomes,
without filtering, adjustment or aesthetic retries. No human ratings occur.
Measure only after this successor is terminal, in the three fixed pipelines.

At most two requests are active, starts are at least five seconds apart, and
the 5 GiB disk reserve applies. Permit 96 first attempts plus at most eight
technical retries, at most one per slot: **104 maximum attempt intents**.
Inherit the exact qualified error/retry contract of the unchanged predecessor
protocol: complete error-only matching numeric 429/500/502/503/504 responses or
its qualified plain-text 503; delay at least 60 seconds and honor supported
Retry-After up to 300 seconds. Refusals, uncertain delivery, unsupported success
and malformed responses are not retried. A ninth needed retry stops admission;
using the eighth does not cancel remaining first attempts. A second technical
failure in one slot does not permit a third attempt.

Retain the predecessor's stop/drain rules for unsupported retry delays, three
failures in the latest eight completions, insufficient disk, identity/account/
endpoint changes, uncertain/unsupported delivery, unrecognized errors and
interruptions. Final source/process checks occur after all active responses
drain. Source/process changes, authentication/account/endpoint contract failures,
uncertain/unsupported delivery, unrecognized backend errors and interruptions
require a false identity flag and globally withhold inference even if the pairs
are complete. Disk, deadline or recognized technical-error stopping does not by
itself invalidate identity; duration and completeness gates still apply.

The terminal elapsed duration must not exceed 24 hours from first dispatch.
Stop admission five minutes before that deadline and drain accepted requests.
The inactivity timeout does not guarantee timely drainage; actual elapsed time
determines eligibility. Preserve all raw responses, attempt/slot/operator
records and hashes, with delivery fields summarized by arm. No paid API or
fallback is allowed: the cumulative ceiling remains $75 and historical
conservative accounting remains $50.7219185, with **zero new paid calls** and
no assigned monetary price for OAuth subscription use.

## Required gates and final limit

Commit this protocol and decision before any predecessor feature extraction.
Before successor live collection, require the predecessor's verified terminal
receipt and complete slot accounting, including the recorded missing Cezanne
slot. Bind that terminal lineage; an unverifiable or still-running predecessor
does not satisfy this gate. Preserve all earlier evidence and its unavailable
endpoint regardless of the successor outcome.

Qualify the exact successor source and analysis with offline allocation,
48-pair weighted-statistic, alpha, completeness/identity/duration, narrow-secondary
and full artificial 96-slot workflow tests, plus transport tests and disclosed
maintainer-run LLM reviews. Complete required Ruff, full offline tests and
applicable evidence verification. Commit clean source/configuration/inputs and
qualification, prepare a create-once freeze binding those commits, reused inputs,
runtime/proxy identity and all requests, then commit and verify that freeze
before live dispatch. Public replay claims require an actually released and
verified new package; retained vectors do not authenticate absent pixels.

This is **one final successor**, not a replacement loop. A terminal, failed,
interrupted or incomplete run cannot resume or refill. No further cohort is
planned if this successor fails, if original Monet fails, or if either available
result is contrary or unresolved. No outcome changes allocation, prompts,
threshold, pipeline or this stopping commitment.
