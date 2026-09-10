# Scientific implementation review — prospective clause validation v1

Date: 2026-09-10. Reviewer: maintainer-run LLM Reviewer 1.

## Assessment and disclosure

No remaining must-fix issue was identified in this bounded precollection review of the current source bytes listed below. This is a scientific and operational implementation assessment, not authorization to dispatch images. Clean source/design commitment, the final reviewed qualification record, a separately committed freeze and the live identity checks remain required. No new images, API calls, image extraction or prospective results were obtained for this review. Existing manuscript scores are unchanged; this report assigns no score.

I authored this namespace's precision-planning module and tests, and previously implemented the retained-data geometry namespace's variance and cross-repeat residual primitives. I also assisted with the local numerical release packager. I did not implement the collector or its workflow. The collector review is a separate examination by an implementation-involved maintainer-run LLM agent, not independent human or institutional review. Checks of my precision output below use direct arithmetic and source hashes; they are not a claim of independently authored statistical qualification software.

## Reviewed scientific contract

The allocation is exactly 24 prospectively authored fixed scenes, three repetitions and four actual arms: free, generic, Monet and Cezanne. This is 288 first-attempt slots in 72 randomized four-position blocks, with at most eight technical retries and 296 attempt intents. The generic output is shared across painter endpoints; its reference-content weights differ by painter. The two primary estimands are weighted full V-energy named-minus-generic contrasts, using fixed references and 31 existing scaled coordinates. Neither a random population of scenes nor a population of service dates is sampled.

Conditioning on the other two arm positions leaves equiprobable swaps of each named/generic pair under the sharp no-effect/no-interference null. The retained exact weighted-energy coefficient identity includes within-distribution terms. Holm adjustment applies to exactly two p-values, including unavailable endpoints as p=1. The two comparisons need not be independent, and the artificial qualification preserves their shared generic outcomes. Equality of population energy alone is not the tested sharp null.

The old OAuth maps remain fixed before new outcomes. Their energy and repeat-corrected conditional residuals are secondary descriptions, without map-label permutation tests, a new Q confidence interval, or optimization on the new panel. Cross-repeat Q retains its independent, stable, zero-mean repeat-error assumption conditional on the historical map; it does not remove uncertainty in historical fitting or guarantee a latent stylistic interpretation.

## Collection and evidence findings

- The current collection entry point requires explicit live=True unless the transport is an offline MockTransport. Dispatch uses the fixed OAuth URL/model and carries no paid-provider credentials. Historical accounting remains $50.7219185 with no artificial monetary assignment to subscription usage. The historical receipt's harmless floating-point tail is checked with a tight tolerance, while unresolved prior paid state is rejected.
- Full request regeneration in workflow verification, clean committed bindings and the fixed configuration establish the complete 288-slot allocation. The narrower inventory helper is not the sole allocation guard. Blocks remain contiguous and are drained before a later block is admitted. A ticketed two-worker start gate preserves admission order and spacing.
- Each intent is appended before worker submission, the active-future mapping is installed before callback registration, and terminal handling follows completion order. Stop handling cancels workers still waiting to post and drains in-flight workers. Worker exceptions become uncertain terminals; unresolved intents prevent scientific replay. Only complete recognized error-only technical responses can trigger an identical-payload retry, once per slot and under the global cap. Refusals, malformed success, uncertain/incomplete delivery and quality differences do not trigger replacement images.
- The first valid supported opaque output is retained, including valid requested/delivered size or reported-quality mismatches. Missing measurements retain their slot identities. An absent generic observation affects both primary endpoints, an absent named observation affects its endpoint, and an ordinary absent free observation affects secondary descriptions. A global identity failure or failed duration contract withholds both primary tests even if all named/generic measurements happen to be available.
- Source and local proxy identity are checked after the last drained block, in addition to earlier checks. The final operator event is hash-bound into the terminal receipt, and workflow verification recomputes identity eligibility from operator events, final source/proxy checks and terminal failures. This attests only the recorded local source/process checks, not a stable remote checkpoint or independent service state.
- Collection, response storage, measurement markers and reports are create-once. Closed runs cannot resume or refill. Response bytes are confined to the new namespace and checked at both compressed-storage and uncompressed-entity levels. Feature extraction starts only after terminal collection accounting; old reference vectors and scalers are consumed as bound numerical inputs.

### Resolved must-fix finding

The first identity patch had an ordered-stop edge case. A noninvalidating halt such as storage reserve could be recorded first, followed by an interruption during drainage. The collector would set identity_contract_met=False without recording the later invalidating reason; successful final checks and valid terminal rows could then cause workflow verification to recompute True and reject the receipt.

The current implementation records exactly one identity_contract_failure event at the first True-to-False identity transition, independently of the preserved first halt reason. The new regression retains a storage halt, then KeyboardInterrupt, then successful final source/proxy checks; its false identity receipt now verifies correctly. This was a conservative replay defect, not false primary acceptance. It is resolved in the reviewed bytes.

### Duration boundary

The httpx 240-second timeout is an inactivity timeout, not a total request wall-clock limit. The protocol explicitly stops admission five minutes before 24 hours, drains outstanding work, and withholds both primary tests if the recorded duration exceeds 24 hours. That eligibility contract matches the implementation. It should not be described as a guaranteed transport kill at exactly 24 hours.

## Precision and artificial-null record audit

The planning record is bound to source commit 6dd1e80b7d998f39809bfa354c8f52b7dd439595. All eight bound files were checked against their recorded SHA-256 values and that commit. Its 27 rows preserve nine hypothetical generic scenarios, three allocations, 250 trials per scenario and seed 120260910. One generic cloud is shared by both endpoints. These are old estimated means and empirical residual laws; they are not observations from the new generic arm.

The SD ranges reproduce the earlier disclosed proxy computation:

| Allocation | Monet SD range | Cezanne SD range |
| --- | --- | --- |
| 12 x 3 x 4 = 144 | .149475–.266775 | .133636–.200511 |
| 24 x 3 x 4 = 288 | .102835–.150203 | .088634–.125109 |
| 24 x 4 x 4 = 384 | .093402–.136339 | .074883–.104309 |

All range endpoints were checked against the nine component rows. The selected 288 preserves 24-scene breadth while avoiding the additional 96 outputs of a fourth repeat. The record correctly reports all hypothetical effect means, including unfavorable signs, rather than selecting a favorable alternative for a power claim. Its conditional empirical SD cannot establish new-arm power, meaningful-effect resolution, an equivalence margin or population precision.

The artificial complete-grid check uses seed 120260911, 5,000 independently assigned 72-block four-position trials per case and 999 Monte Carlo sign draws per endpoint. The actual primary analysis will use 99,999 draws with the same conservative plus-one/tie rule. Each artificial case holds position outcomes fixed before labels. Partial-null cases shift only the non-null named arm; the other named/generic sharp null is preserved. Their true-null masks and family-error counts are correct.

| Artificial case | True-null family errors / 5,000 | Rate | Wilson upper 95% |
| --- | --- | --- | --- |
| No added position drift | 245 | .0490 | .055337 |
| Position drift | 243 | .0486 | .054915 |
| Rare large outcome | 236 | .0472 | .053434 |
| Monet null; Cezanne shifted | 214 | .0428 | .048770 |
| Cezanne null; Monet shifted | 223 | .0446 | .050680 |

I independently recomputed all five rates and Wilson intervals using the normal quantile and direct binomial formulas; agreement with the saved intervals is within 2e-16. Counts are consistent with the reported per-endpoint rejections and true-null masks. Every upper bound is below the prespecified .065 criterion. This supplies a useful numerical shared-control/global-and-partial-null check; it does not qualify service no-interference, availability invariance or delivered-feature stability.

## Bounded verification performed

- 23 selected offline collector tests passed in 3.41 seconds, covering retry limits, recognized/unrecognized errors, worker exceptions, one-shot operation, commit/qualification gates and preparation/verification boundaries.
- After the identity fix, 10 selected collector/analysis tests passed in 5.98 seconds. They cover final source/proxy failures, forged identity restoration, the ordered-stop regression, analysis identity/duration gating and the complete 288-slot artificial workflow.
- The complete-grid test uses mock image responses and a synthetic feature provider, then executes the real downstream analysis and numerical replay. It qualifies orchestration, identities, denominators and replay under artificial inputs; it is not a fresh validation of the pixel extractor or actual service behavior.
- Ruff passed for the reviewed collection, workflow and analysis source and their tests. I did not duplicate the coordinating agent's full offline suite or evidence audit.

All qualification claims above are limited to the reviewed source, tests and records. Material changes before freezing require renewed targeted review. The final qualification/freeze procedure must bind this report along with the other required precollection reviews; the current common binding inventory includes it.

## Reviewed byte identities

| Path | SHA-256 |
| --- | --- |
| `src/latent_art_bench/painter_clause_validation_v1/collection.py` | `fa40aa9b5bf58d76507be92379fc116bc02833a61e41c4c6474b30111cdfe823` |
| `src/latent_art_bench/painter_clause_validation_v1/workflow.py` | `f97ca52dd6acc64c883e05bb7486bf89d2a1ce874f7e7a36c2dbe9b451f30ad0` |
| `src/latent_art_bench/painter_clause_validation_v1/common.py` | `9972fb640f8f36b88079a4368ec45c267bcdfac0245e51aa8303587a1d4a725a` |
| `src/latent_art_bench/painter_clause_validation_v1/analysis.py` | `c5a8049bddb586b861f62a207399a63dcd1838ac8135f9ea5349e84f5335b35c` |
| `src/latent_art_bench/painter_clause_validation_v1/precision.py` | `a3ba7a21d46dee06efe28177a6a279a773e79b406a0120abb4f00f17c7939cec` |
| `studies/painter_clause_validation_v1/PROTOCOL.md` | `87d6dfae4746f7bc4028c4ea5e7dc5678ef7874cce065bac5b75623dfe68a91e` |
| `studies/painter_clause_validation_v1/precision.json` | `c1da41e3ff1f7cc1e42c44a48d3189f07309cc5d467b99078492341416469785` |
| `studies/painter_clause_validation_v1/PRECISION.md` | `fcc2feb31336b2a28189e3367d9d4c68f9174ec6319b35fc637b5de5f39e0fd5` |
