# Future evidence options: fresh requests and new scenes

Prepared 19 September 2026. **Proposal only. No collection, API request, pricing lookup, reference acquisition, or human study has been performed for this proposal.** Current learned-representation outcomes were not inspected.

## Decision-ready summary

The existing terminal receipt accounts for **$112.293676** against the preserved **strictly less than $120 cumulative ceiling**, leaving **$7.706324**. Existing collection namespaces are permanently closed; their budget balance does not authorize reopening them or launching another collection.

| | Option A: smallest balanced fresh-request check | Option B: substantial prospective follow-up |
|---|---|---|
| New protocol namespace | `painter_specificity_fresh_check_v1` | `painter_specificity_prospective_v1` |
| Six requested configurations | All six, same recorded rendering settings | All six, same recorded rendering settings |
| Painter names | Monet, Sisley, Pissarro, Cézanne | Monet, Sisley, Pissarro, Cézanne |
| Scenes | 1 new common scene | 24 new common scenes: 6 each water/built/land/mixed |
| Arms | Four named-painter arms | Artist-free, generic oil painting, four named-painter arms |
| Repeats per cell | 2 separately requested outputs | 4 outputs: 2 in each of two sessions at least 24 hours apart |
| Planned outputs | 48 | 3,456 |
| Projected new charge at historical mean rates | **$2.085063** | **$150.124546** |
| Projected cumulative amount | **$114.378739** | **$262.418222** |
| Maximum technical retries | 8 total; at most 2 per failed slot | 72 total; at most 2 per failed slot |
| Proposed financial authorization | Keep cumulative ceiling below $120; new-run settled-charge stop threshold $2.65 | Raise cumulative ceiling to below **$300**; new-run settled-charge stop threshold **$170** |
| What it can establish | A very limited fresh-request observation on one new composition | A planned test of close-painter alignment across a new scene panel and temporally separated requests |

**Recommendation:** choose Option B if the objective is materially stronger transfer evidence. Option A fits the existing financial guards but is too small to settle the scientific-review concern. Neither option supplies new reference-source validation or perceptual ground truth.

These are concrete alternative scopes for later authorization. This document does not request permission or authorize spending.

## Cost evidence and the reservation constraint

The completed run has 1,008 successful attempts and no retries. Its observed charges total **$43.786326**, which adds to its frozen **$68.507350** starting accounting to reproduce **$112.293676**. The receipt's attempt-ledger binding was verified:

`b131798cd2b803d6d60569def72700bb35daacdd2c5602e0dc854b7bd77a3ffd`.

| Requested configuration | Completed outputs | Mean recorded charge/output | Maximum recorded charge/output |
|---|---:|---:|---:|
| GPT Image 1, medium | 168 | $0.042481667 | $0.042520 |
| GPT Image 2, medium | 168 | $0.052921667 | $0.052960 |
| GPT Image 2.5 Flare, medium | 168 | $0.013411667 | $0.013450 |
| GPT Image 2.5 Sunburst, medium | 168 | $0.013411667 | $0.013450 |
| Nano Banana 2, 1K | 168 | $0.068406226 | $0.068612 |
| FLUX.2 Max, PNG | 168 | $0.070000000 | $0.070000 |

One output from each of the six configurations therefore costs **$0.260632893** at historical mean rates. Multiply that quantity by scenes × arms × repeats. These are September 10 ledger estimates, **not guaranteed live prices, quotes, or upper bounds**. New prompt-token charges and service rates may differ.

The existing guard reserves **$5 per active paid attempt**, in addition to the historical uncertainty reserve already included in the cumulative accounting. Keeping that rule leaves only **$2.706324** of settled-charge room before a new $5 reservation would reach the ceiling. Thus a nominal three-scene named-only grid (144 outputs, approximately $6.255189) is *not dispatch-feasible under the unchanged reservation guard*, despite its projected settled total of $118.548865. Do not silently lower the reservation or recycle the historical reserve to make it fit.

- **Option A:** one active request at a time. Applying each model's historical maximum gives $2.087936 for 48 planned outputs. Eight retries at the largest observed charge, $0.07, add $0.56: projected cumulative accounting is $114.941612. A further $5 active reservation would remain below $120 at $119.941612. The $2.65 new-run settled-charge threshold is an additional dispatch stop, not a reservation-inclusive cap or a guarantee about unknown future charges.
- **Option B:** at most three active requests, starts at least five seconds apart. Historical model maxima give $150.331392; 72 retries at $0.07 add $5.04. Including all three $5 active reservations gives a projected cumulative $282.665068, leaving about $17.33 below the proposed $300 ceiling. A separate $170 new-run settled-charge threshold prevents using the entire increased ceiling for unplanned sampling. Admission must keep cumulative settled amounts plus outstanding reservations strictly below the authorized cumulative ceiling and stop once the new-run settled-charge threshold is reached. Pending requests can settle after that threshold is crossed; their reservations remain charged against the cumulative ceiling.

Unknown charges retain their reservations and pause dispatch. A charge above its reservation, route/contract error, or three consecutive technical failures requires reconciliation before proceeding. No automatic model fallback, refusal retry, quality reduction, or outcome-driven enlargement is proposed. Missing slots remain reported; budget exhaustion does not authorize reducing the balanced design and presenting it as complete.

## Fixed model and request contract

Both options are text-only, one image per request, square aspect ratio, with `provider.allow_fallbacks=false` and a sole explicit provider:

| Model identifier | Sole provider | Additional recorded rendering settings |
|---|---|---|
| `openai/gpt-image-1` | `openai` | `quality=medium`, `background=opaque` |
| `openai/gpt-image-2` | `openai` | `quality=medium`, `background=opaque` |
| `openai/gpt-image-2.5-flare` | `openai` | `quality=medium`, `background=opaque` |
| `openai/gpt-image-2.5-sunburst` | `openai` | `quality=medium`, `background=opaque` |
| `google/gemini-3.1-flash-image` | `google-ai-studio` | `resolution=1K` |
| `black-forest-labs/flux.2-max` | `black-forest-labs/us-3` | `output_format=png` |

Use the existing documented gateway route only after separate authorization and precollection checks. If a requested route is unavailable, stop rather than substituting a different model. Labels continue to identify requested configurations; fresh acceptance does not authenticate hidden checkpoints or prove they are unchanged since the earlier run.

The scene text is identical across configurations, painter names, and repeats. Prompt suffixes are fixed:

- Artist-free: `No text or frame.`
- Generic: `Render as an oil painting. No text or frame.`
- Named: `Render as an oil painting in the style of [Claude Monet / Alfred Sisley / Camille Pissarro / Paul Cezanne]. No text or frame.`

Option A contains only the four named arms. It therefore cannot independently estimate the common artist-free-to-named or generic-to-named change, and must not reuse old controls as if contemporaneous.

## Fresh scene wording

These authored prompts are proposed before new images exist. They are new compositions, not output-selected substitutes. The future freeze must check exact and near-duplicate wording against the retained prompt manifests without reading current learned scores. Any necessary replacement must be recorded before the first request. They remain a fixed authored panel, not a random sample of all scenes.

**Option A uses W1 only. Option B uses all 24.**

### Water

1. **W1:** A shallow stream divides around a mossy gravel island. A bare branch crosses the foreground, and a distant reed bank lies beneath thin evening clouds.
2. **W2:** A flooded pasture surrounds a row of short wooden fence posts. Low willow bushes stand on the right, and the water reflects a strip of pale morning sky.
3. **W3:** A tidal pool lies between dark rounded rocks. A narrow band of open sea crosses the background beneath a bright, cloudless sky.
4. **W4:** A straight drainage ditch runs beside a freshly cut field. A small culvert marks the middle distance, with poplar trees along the far boundary.
5. **W5:** A mountain lake occupies the lower half of the view. A pale scree slope rises on the left and a dark ridge is reflected in still water.
6. **W6:** Rainwater fills shallow ruts in a sandy clearing beside a river. A pile of driftwood lies in the foreground, and the opposite bank is partly hidden by mist.

### Built

1. **B1:** A low railway platform stands beside two empty tracks. A red brick goods shed is set back on the left, with a line of hills beyond the station.
2. **B2:** A narrow staircase climbs between plaster garden walls. A wooden door stands halfway up, and a small patch of sky is visible above the roofs.
3. **B3:** A roadside bakery has closed wooden shutters and a striped awning. The empty pavement slopes gently toward a row of bare trees.
4. **B4:** A small stone chapel stands at the edge of a harvested field. A bell opening interrupts its simple front wall, and a low hedge crosses the foreground.
5. **B5:** A timber boathouse stands above dry mud on short piles. A ladder rests beside its doorway and pale clouds gather beyond the roof.
6. **B6:** A covered market shelter stands in an empty village square. Sunlight falls between its wooden supports and a row of low houses encloses the background.

### Land

1. **L1:** A harvested field contains several small stacks of straw. The rows run diagonally toward a distant belt of trees beneath a high, clear sky.
2. **L2:** A wet heath is dotted with low flowering bushes. A line of exposed stones curves across the foreground, with a rounded hill in the distance.
3. **L3:** A stand of slender birches grows on a sandy rise. Long shadows cross the open foreground and a dark evergreen wood fills the background.
4. **L4:** A dry vineyard covers a broad slope in parallel rows. A single overturned basket lies near the lower edge, and clouds cast wide shadows over distant hills.
5. **L5:** A patch of melting snow remains in the hollow of a grassy plateau. Scattered stones catch the afternoon light, with layered ridges on the horizon.
6. **L6:** A narrow strip of wildflowers borders a freshly ploughed field. The furrows lead toward a solitary hay barn far in the distance under a low cloud bank.

### Mixed

1. **M1:** An abandoned stone quarry contains a pool of green water. Rough steps descend from a grassy rim, and two small houses stand beyond the far wall.
2. **M2:** A footpath follows the edge of a reservoir below a hillside village. A metal railing crosses the foreground and a patchwork of gardens climbs behind the roofs.
3. **M3:** A sluice gate separates a narrow channel from a reed-filled basin. A dirt service track runs beside it toward a low brick building.
4. **M4:** A wooden footbridge crosses a gully at the edge of an orchard. A stone boundary wall and a small farmhouse occupy the distant slope.
5. **M5:** A disused waterwheel stands beside a shallow millrace. Sunlit grass fills the foreground and a wooded hillside rises behind the tiled mill roof.
6. **M6:** A coastal road passes between a grassy bluff and a row of pale houses. A short stairway descends toward a sheltered beach at the edge of the view.

## Randomization, temporal separation, and irreversible closure

Create a completely new namespace, run ID, request IDs, manifests, ledger, and pixel directory for the chosen option. Existing terminal receipts, request lists, images, and protocols remain immutable. There is no continuation of `psv2-20260911`.

Before the first request, freeze and hash: exact prompts and payloads; configuration/provider metadata; all assignments; randomized order; retry and admission code; feature extraction and numerical tests; fixed reference pixels/regions/scaler; endpoint definitions; analysis code; locked dependencies; budget baseline and caps; and the planned session times. Local hashes/timestamps do not become third-party preregistration. Save a create-once terminal receipt before any scientific feature measurement. No interim learned or 31-feature scores may determine collection changes.

- **Option A:** randomly permute all 48 model × painter × repeat slots together using seed `2026091901`. Repeat labels are interleaved, not collected as two contiguous repeat batches. Because there is only one scene, this option cannot satisfy an across-scene temporal-balance objective; that is an explicit limitation of its affordable scope.
- **Option B:** use two prescheduled collection sessions at least 24 hours apart, each containing two requests per model × scene × arm. Within each session, randomize the full assignment list using seed `2026091902` plus the session index. Interleave model, scene, arm, and repeat assignments; do not finish all conditions for one scene before moving to the next, and do not collect repeats in contiguous waves. Freeze the actual start order rather than merely a seed. Retries join a delayed queue with identical payloads and preserve their original slot IDs. The second session is fixed before the first begins and cannot depend on its appearance or scientific measurements.

Randomization reduces alignment between scene/condition and elapsed time. It does not prove service independence, eliminate caching or hidden state, or authenticate unchanged checkpoints. Two sessions permit a temporal check but are too few to characterize arbitrary service drift. New scenes and later service state also change together; this design does not identify which caused any disagreement with the old panel.

## Prospective targets and analysis

### Shared finite target

Use the original 649-work reference panel, 221-work development scaler, 31 coordinates, artist order, and original full-frame processing as the primary measurement, fixed before collection. This directly targets the earlier finite-reference result. The previously audited regions and development-target substitution are fixed secondary sensitivities. No new reference work, crop selection, or human assessment is proposed.

CLIP and the public CSD checkpoint may be run as prespecified secondary representation sensitivities with their already fixed hashes and preprocessing. They are not used to select the scenes, service configurations, primary representation, or endpoints. CSD's published-weight discrepancy and training-artist overlap must remain disclosed. The ongoing retained-data learned audit and either prospective collection are different evidence sources.

### Option A: descriptive fresh-request check only

Report all six configurations' one-scene four-painter beta and D, all six pairwise betas, raw repeat disagreement, failures, and exact prompts. The two requests allow a cross-repeat point estimate under the same assumptions as the original study. **One scene supplies no between-scene precision estimate or generalization claim.** Do not perform model-ranking significance tests, equivalence tests, or claim that this option confirms a service-level Monet–Sisley failure. Its practical role is detecting a gross discrepancy on a newly collected common composition.

### Option B: a focused prospective close-painter test

The primary family is **six model-specific Monet–Sisley aligned-response coefficients**, in the fixed original 31-feature metric and relative to the same reference-pair difference. Aggregate each over all 24 common scenes and four requests. All four painters remain in collection; Monet–Sisley is selected in advance because it is the explicit outstanding hypothesis. Report the other five painter pairs and aggregate four-painter scores regardless of result as secondary descriptive outcomes.

For each primary coefficient, report a scene-paired Student interval using Bonferroni adjustment across these six endpoints, explicitly as an approximation conditional on this authored scene design and the request assumptions. An operational weak-alignment region is **[-0.25, 0.25] of reference-pair amplitude**. This is a declared measurement criterion, not a perceptually validated tolerance. Only an interval wholly within that region supports the corresponding bounded weak-alignment claim; a point estimate inside it or an interval containing zero does not. Do not add a separate unplanned family of 15 model-ranking tests.

For secondary repeat-corrected D, average the two requests within each session and cross the two session means. This reduces independent request noise and avoids treating within-session pairs as the sole basis for correction, while still assuming zero cross-session error covariance and stable relevant means. Report session-specific beta, the all-six-unordered-repeat-pair D estimate, and their discrepancy descriptively. These checks do not certify independence. Also report scene-averaged D, scalar-calibrated contrasts, and both free-to-named and generic-to-named common/specific decompositions using formulas frozen for the four-repeat design.

Keep this collection separate from the old run. Report prospective estimates and the earlier point estimates side by side; any pooled result is secondary and cannot create a new prospective sample size. Retain contrary results and close at the declared allocation or a documented failure, with no significance-driven continuation.

## Precision limits: the larger option is not a power guarantee

Additional repeats reduce some generation noise; 24 scenes supply the variation used by scene-based intervals. Neither improvements in noise nor temporal independence can be guaranteed from historical costs. For the proposed six-endpoint Student procedure, an interval half-width is approximately **0.5892 × the observed scene-level SD** when all 24 scenes are complete. Illustrative half-widths are:

| Scene-level SD of pair beta | Approximate simultaneous half-width, 24 scenes |
|---:|---:|
| 0.25 | 0.1473 |
| 0.50 | 0.2946 |
| 1.00 | 0.5892 |

Thus a ±0.20 half-width would require scene-level SD around 0.3395 or smaller. These are algebraic planning illustrations, not estimates obtained from current learned outcomes or a promised achieved precision. With only three scenes the corresponding multiplier would be 6.285, which further explains why the nominal $6.26 grid would not be adequate even if the reservation were changed. Option A cannot estimate this scene SD at all.

Option B funds a substantively stronger design, but may still leave individual weak-alignment claims unresolved. Report achieved widths and missingness. The fixed reference panel, authored scene selection, two temporal sessions, hidden service state, and absence of perceptual validation remain limitations.

## What each evidence source adds

| Evidence | Adds | Does not add |
|---|---|---|
| Learned descriptors on the retained 1,008 images | Same-image comparison across representations and evaluation summaries | New service draws, new scenes, independent checkpoint identity, perceptual truth |
| Option A | A small later set of separately requested images on one new scene | Useful scene-transfer precision, new generic/free controls, a general replication claim |
| Option B | A complete new scene panel, more repeats, separated sessions, contemporaneous controls, an explicitly prospective primary family | Independent reference acquisition, verified service independence, population-wide scene coverage, human fidelity judgments |

## Local evidence inspected

- `data/manifests/painter_specificity_v2/psv2-20260911/collection.json`: terminal accounting and membership metadata only.
- `data/manifests/painter_specificity_v2/psv2-20260911/attempts.jsonl`: settled charges and terminal outcomes; SHA-256 verified against the terminal receipt.
- `data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl`: map request IDs to requested configurations for cost aggregation.
- `studies/painter_specificity_v2/PROTOCOL.md` and `src/latent_art_bench/painter_specificity_v2/{study,workflow}.py`: cumulative accounting, active reservation, fixed routes, and permanent terminal closure.
- `src/latent_art_bench/painter_specificity_v1/study.py`: earlier scene wording and painter/configuration order.

No current learned-analysis result or another reviewer's report was consulted in preparing this proposal.
