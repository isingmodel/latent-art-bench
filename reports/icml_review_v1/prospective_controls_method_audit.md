# Prospective controls: independent methods audit

**Scope:** Advisory design review of `prospective_controls_v2.md`, before any new outcomes. This is not a rescore. The completed round-03 review is unchanged. No paid requests, downloads, outcome reanalysis, manuscript edits, or original-science edits were performed.

## Assessment

**The proposed control addresses an important evidentiary gap directly, but the proposal needs several clarifications before it is frozen or collected.** A contemporaneous painter-name-free family prompt, compared with generic painting and the four named conditions on new scenes, is a meaningful empirical test of what prototype gain can establish. The linear primary endpoint is preferable to making an unstable ratio the test statistic. Fresh temporal blocks improve the evidence beyond adding further representations to the old cohort.

The full 4,608-image allocation is not necessary to answer that narrow question. It is also not executable under the current authorization and capacity: the ceiling remains strictly below $120, historical accounting is $112.293676, approximately 2.1 GiB is free, and external storage is unavailable. The pending budget/storage question need not be asked again. A proposed $350 ceiling is not an operative collector setting.

### Which objections it addresses

| Evidentiary issue | What this design would add | What would remain |
|---|---|---|
| Large common gain may reflect appropriate characteristics shared by these painters | Direct intervention using a named-painter-free historical-family instruction, plus an explicit wording comparator | One exact family phrase cannot identify a unique semantic mechanism or establish all family-level effects |
| Main findings come from reused images and fixed old prompts | Untouched requests on a declared new prompt panel, with contemporaneous controls | The four painters and reference panel remain fixed; no generalization to other artist groups follows |
| Single-session/two-repeat inference | Eight full-panel temporal blocks and their observed variability | Eight windows do not prove independence or separate all service-state and request-noise components |
| Retrospective recognition correction | Nothing directly, as currently specified: normalized-reference recognition alone is not a prospective test of the old translation rule | A frozen old-cohort transfer test can be added with no extra images; see below |
| Measurement reproducibility | More retained records, if capacity and archive contracts are implemented | Local retention still does not provide public exact-pixel access |

Retaining all four painters and excluding human evaluation are compatible with a sound finite-panel, nonperceptual claim. The design should not promise to remove the remaining artist-set or perception limitations.

## Fix before outcome collection

### 1. Make the claim an operational counterexample, not causal attribution

The formulas for `N`, `F`, `L` and `T = F - 0.5 N` are coherent. If both simultaneous lower bounds exceed zero, the experiment shows that **a prompt with no individual painter name produces more than half the aggregate prototype gain of the named condition, on this workload**. That is useful evidence that the scalar gain alone does not identify painter-specific influence.

It does **not** show that the family information mediated or caused most of the gain in the named prompts. Different interventions can reach similar scores through different changes. Replace wording such as “individual painter identities caused most of the improvement,” and the negative-result claim about weakening an “explanation,” with statements about this comparator's observed sufficiency for producing the measured gain. A negative result means this specified control failed to reproduce half the gain, not that a shared-family mechanism was excluded.

The 50% boundary is acceptable as a declared numerical majority threshold. It needs no human validation if kept separate from resemblance or artistic quality.

### 2. Decide whether the primary question concerns any name-free comparator or family information beyond wording

`F` compares the entire family suffix with generic oil painting. It therefore includes both historical-family information and the added style framing. `style_frame` makes the latter inspectable, but reporting it secondarily does not make `T` an isolated test of family information.

Choose the interpretation before outcomes:

- **Recommended minimal claim:** retain `N` and `T` as the 12 primary endpoints, and call this a test of the specified *name-free family prompt as a whole*. Retain `S` and `F-S` as complete descriptive controls. No unique semantic partition is claimed.
- If the intended primary claim is specifically about family information beyond this wording comparator, define `N_S = N-S`, `F_S = F-S`, and `T_S = F_S - 0.5 N_S = F - 0.5 N - 0.5 S`. Set the primary family and completeness rules accordingly before collection. Do not switch to this criterion after seeing which baseline is favorable.

The awkward redundant wording arm is not inherently invalid: it is an exact prompt intervention. Its interpretation must remain that exact paraphrase, as the proposal already largely acknowledges.

### 3. Specify the temporal estimand and avoid implying independence was measured

Define the primary target as an equal-weight average of the condition effects for the fixed scene panel over the eight scheduled windows. State that the simultaneous Student intervals require independent, suitably behaved session summaries; the proposed correlation multipliers are sensitivity calculations, not an empirical correction.

Two sessions on each of four days create a plausible day-level dependence structure. The proposal may retain that schedule with its explicit conditional assumptions, but should not describe the eight summaries as eight independently sampled days. If elapsed time is not restrictive, **eight separate days with one full-panel session per day** is a cleaner use of the same eight blocks and identical image budget. It still does not authenticate independent service states. Freeze absolute UTC times and the intended schedule before collection.

Do not shrink the number of temporal blocks first merely to save images: they supply the replication for the primary intervals. Fewer scenes or removal of an irrelevant arm is a more direct reduction for this fixed-panel question, with the narrower content scope stated.

### 4. Repair the cross-session squared-error specification

The secondary cross-session products need **stable conditional means as well as the specified covariance assumptions** if they are to estimate the original squared-error target. Suppose the scene's centered conditional mean in session `i` is `theta_i`. Even with zero cross-session error covariance, a product from sessions `i,j` targets

`<theta_i - r, theta_j - r> / H`,

not either session's squared error. Averaging all distinct session pairs targets squared error of the session-average mean **minus** a term for variation among the session means. Consequently a same-day/different-day product difference can reflect changing conditional means, covariance, or both.

Before collection, specify every pair, normalization and weight used in these summaries. Either explicitly assume stable conditional means and retain the limitations, or label the result as a cross-session product diagnostic rather than corrected `D`. Do not use its temporal differences to estimate repeat covariance. The linear primary gain endpoints do not require this added squared-error analysis; dropping it is a legitimate simplification.

Also define each Fieller target as a **ratio of session-averaged components**, using the paired numerator/denominator covariance. Do not average per-session ratios, discard sessions with negative denominators, or replace an unbounded confidence set with a finite interval. This can be tested on constructed arrays without viewing new outcomes.

### 5. Add a frozen prospective transfer test if that contribution remains central

The present secondary recognition table does not test whether the old common translation works on new queries. A direct extension needs no additional generated arms:

1. Before new outcomes, freeze one translation and one supervised generated centroid per painter/configuration/encoder fitted using the full **old** 14-scene named cohort and the already fixed references.
2. Apply the unchanged baseline, translation and generated-centroid rules to every new named image.
3. Retain all paired decisions, harm/correction counts, painter recalls and session summaries. Do not fit an offset or choose a variant using the new queries.

This would provide a prospective test of transport to the new content/later service setting. It would not isolate whether failures arose from content or service changes. Keep it explicitly secondary if the primary question remains the family comparator; do not add unadjusted confirmatory claims. This is analysis work on existing/newly planned bytes, not an additional acquisition requirement. I did not compute these old-cohort fits in this audit.

### 6. Build and qualify a new collector; the existing one does not implement the new contract

The retained `painter_specificity_v2` collector provides useful archive, reservation and create-once patterns, but it has no session-window dispatch or disk-capacity admission logic, hardcodes the old namespace/baseline and 24-retry cap, and assumes paths relative to the repository. It must not be restarted or treated as executable support for this proposal.

A new namespace needs mocked, no-network tests for:

- Exact arm/scene/session membership and full-session randomization; no automatic paid qualification pilots inherited from the old freeze routine.
- Start-time window admission, delayed retries remaining in the same window, and stragglers. A request started before the cutoff should be drained and retained with its assigned session; define the end policy explicitly instead of discarding late successful responses.
- The authorized cumulative ceiling and baseline, $5 outstanding reservations, unknown-charge retention, maximum concurrency, and global/per-slot retry limits. The old code infers zero cost for some error responses without a reported charge; the new implementation must use documented billing evidence for that inference or retain an unknown reservation. An unknown-charge transport failure must not become an automatically retried slot on resume.
- Crash recovery, durable intents, already-started requests, partial archives, content refusals, terminal incomplete census, and permanent terminal closure.
- Actual free bytes on every write volume and the per-active-request storage reservations. The proposal's 5 GiB floor is a required new enforcement rule, not something supplied by the inspected old collector. Keep unique existing evidence intact.
- Returned geometry/media type and any echoed model/provider metadata. The old decoder accepts much broader dimensions than the proposed square 1K contract. Decide what constitutes a technical mismatch before collection; preserve the response even when a mismatch blocks further dispatch.

Live route/pricing verification and executable storage/budget admission must precede dispatch, after the applicable authorization and adequate local space exist. Historical means and maxima are forecasts, not future price bounds.

## A smaller defensible allocation

For the stated primary test, the essential arms are the four individual painters, generic painting and the family comparator. The wording arm is valuable to the paper's interpretation. **The artist-free arm is not needed for either primary endpoint.** Remove it unless fresh artist-free results are a separately justified objective.

A reasonable smaller design is **six configurations × eight fixed new scenes × seven arms × eight temporal blocks = 2,688 images**, selecting two scenes from each declared content group by a documented rule before outcomes. It preserves all four painters, both controls relevant to the new question, all six configurations and eight full-panel blocks. It narrows content coverage and may increase block variability; it does not guarantee a resolved result.

Historical-rate planning comparisons, computed only from the proposal's rounded rates and archive totals:

| Allocation | Outputs | Estimated new charges | Estimated cumulative charges | Images plus gzip responses |
|---|---:|---:|---:|---:|
| Proposed 12 scenes, 8 arms, 8 blocks | 4,608 | $200.17 | $312.46 | 17.68 GiB |
| 12 scenes, 7 arms, 8 blocks | 4,032 | $175.15 | $287.44 | 15.47 GiB |
| **8 scenes, 7 arms, 8 blocks** | **2,688** | **$116.76** | **$229.06** | **10.31 GiB** |
| 4 scenes, 7 arms, 8 blocks | 1,344 | $58.38 | $170.68 | 5.16 GiB |

These exclude retry allowance, active financial reservations, weights, temporary space, storage variability and the 5 GiB free-space floor. None is authorized under the existing ceiling or feasible with current free space. The four-scene option is an existence test on four compositions, with weaker content coverage, rather than an equivalent substitute for the eight-scene option. Choosing fewer configurations could reduce cost further, but would explicitly change the cross-configuration claim; select them by a declared intended use, not favorable old outcomes.

Do not exploit the small residual budget for an underpowered fragment or quietly relax the storage/retention contract. Since external storage is unavailable, any later capacity plan must use genuinely available local space with all retained archives and caches accounted for. The resource gate remains even for the smaller allocation.

## Work that can proceed without paid collection or downloads

- Revise the claim, select the primary baseline/endpoint family, and specify all temporal and ratio estimands.
- Finalize the scene list, check overlap with old prompt text, and freeze exact payload construction and ordering.
- Implement and test the analysis on constructed vectors, including negative gains, shared-control covariance, zero/near-zero denominators, contradictory encoders and incomplete sessions.
- Implement a new collector behind an explicit no-network default, with the mocked admission/recovery tests above; preserve the old collector and receipts.
- Specify the frozen old-to-new transfer control and complete output schema.
- Prepare a release manifest and attribution checklist from retained metadata. This preparation does not itself establish public pixel accessibility.

The new empirical answers require new authorized requests and enough storage. The planning and verification work above can make that decision concrete without running the experiment. No human evaluation is required for the recommended narrow claim, and no change in any review score is asserted.

## Inspected sources and preservation record

Read `reports/icml_review_v1/prospective_controls_v2.md` in full; the v1/v2 specificity protocols; `painter_specificity_v2/{workflow,study}.py`; relevant v1 prompt/decoder/archive routines; and the v2 route-test locations. No prior reviewer outputs were opened for this advisory audit, and no existing outcome arrays were analyzed.

At audit time:

- Proposal SHA-256: `979d2eb6f12c3ce52b332874125afa424f0f9c4f5b3682078577f70dfe2ba485`.
- Immutable round-03 method prose SHA-256: `eec0451602dd8047c36241cd47ede3e941ae551e1f6f522b31df421540dea35c`.
- Immutable round-03 method JSON SHA-256: `41232fb1b68f84b39213c1e575631456671e5fe458872c1aa98640010f0d2ced`.
