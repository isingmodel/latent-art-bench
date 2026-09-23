# Prospective family and wording controls: bounded experiment proposal

Prepared 19 September 2026. **Proposal only: no new images, API requests, purchases, model downloads, human evaluation, or collection restart.** This document follows the three completed round-02 reviews and preserves `prospective_replication_options.md` unchanged. It proposes an alternative to that document's allocations, not an additional authorized run. No review score or acceptance outcome is predicted.

## Recommendation and purpose

Collect **4,608 images** in a new namespace, `painter_family_controls_v1`: **six requested configurations × 12 new fixed scenes × eight prompt arms × eight separately interleaved sessions**. Every session contains one request for every configuration/scene/arm, for 576 requests per session. All four painters remain. The expected new charge at historical mean rates is **$200.166062**, taking the recorded cumulative accounting to **$312.459738**. The proposed cumulative ceiling is **strictly below $350**, an increase of $230 from the existing $120 ceiling. Neither increase nor execution is authorized by this proposal.

This allocation prioritizes eight observations of the full fixed scene panel at different times, rather than using authored scene variation as a substitute for fresh-request uncertainty. It adds separate controls for stylistic wording and for a shared painting family. It directly addresses two recurring review concerns:

- A generic oil-painting baseline omits the family information and stylistic framing carried by the four related painter names. Common movement can be an appropriate response to that information, rather than evidence of an artist-specific failure.
- Existing learned percentages and ranking changes come from one collection with two requests per cell. New interleaved sessions can measure their repeatability under a specified later collection schedule, while still not proving service independence.

The operational question is narrow: **Can a prompt containing no individual painter name reproduce at least half of the measured named-minus-generic prototype gain?** A positive answer would mean that this gain alone is unsuitable as evidence that individual painter identities caused most of the improvement for this workload. It would not mean that the shared style response is unwanted, that images are worse, or that lower contrast error is perceptual fidelity.

## Exact prompt contract

For each scene below, concatenate its exact text, one ASCII space, and the suffix from this table. One square image is requested per payload. No reference image, negative prompt, human judgment, or generated-image selection enters the experiment.

| Arm ID | Exact suffix |
|---|---|
| `free` | `No text or frame.` |
| `generic` | `Render as an oil painting. No text or frame.` |
| `style_frame` | `Render as an oil painting in the style of a generic oil painting. No text or frame.` |
| `shared_family` | `Render as an oil painting in the style of late-nineteenth-century French Impressionist and Post-Impressionist painting. No text or frame.` |
| `claude_monet` | `Render as an oil painting in the style of Claude Monet. No text or frame.` |
| `alfred_sisley` | `Render as an oil painting in the style of Alfred Sisley. No text or frame.` |
| `camille_pissarro` | `Render as an oil painting in the style of Camille Pissarro. No text or frame.` |
| `paul_cezanne` | `Render as an oil painting in the style of Paul Cezanne. No text or frame.` |

`style_frame` deliberately adds the same “in the style of” construction without an individual name or specified historical family. Its redundancy is intentional. It measures this exact paraphrase, not a universal, semantically empty syntax effect. `shared_family` supplies a broad combined family label; it does not assert that the four painters are interchangeable or all belong to a single school. The named-versus-family contrast removes this specified family instruction as a comparator, not every possible shared historical influence. The conditions cannot identify an internal mechanism or uniquely partition language semantics.

Use these 12 scenes, the first three from each group in the earlier proposal. They were authored before this proposed collection; none has been selected using new outputs. Check for duplicate or near-duplicate wording against the old scene manifests before the final freeze. Any replacement must be documented before the first request, preserving three scenes per group.

| ID | Exact scene text |
|---|---|
| W1 | A shallow stream divides around a mossy gravel island. A bare branch crosses the foreground, and a distant reed bank lies beneath thin evening clouds. |
| W2 | A flooded pasture surrounds a row of short wooden fence posts. Low willow bushes stand on the right, and the water reflects a strip of pale morning sky. |
| W3 | A tidal pool lies between dark rounded rocks. A narrow band of open sea crosses the background beneath a bright, cloudless sky. |
| B1 | A low railway platform stands beside two empty tracks. A red brick goods shed is set back on the left, with a line of hills beyond the station. |
| B2 | A narrow staircase climbs between plaster garden walls. A wooden door stands halfway up, and a small patch of sky is visible above the roofs. |
| B3 | A roadside bakery has closed wooden shutters and a striped awning. The empty pavement slopes gently toward a row of bare trees. |
| L1 | A harvested field contains several small stacks of straw. The rows run diagonally toward a distant belt of trees beneath a high, clear sky. |
| L2 | A wet heath is dotted with low flowering bushes. A line of exposed stones curves across the foreground, with a rounded hill in the distance. |
| L3 | A stand of slender birches grows on a sandy rise. Long shadows cross the open foreground and a dark evergreen wood fills the background. |
| M1 | An abandoned stone quarry contains a pool of green water. Rough steps descend from a grassy rim, and two small houses stand beyond the far wall. |
| M2 | A footpath follows the edge of a reservoir below a hillside village. A metal railing crosses the foreground and a patchwork of gardens climbs behind the roofs. |
| M3 | A sluice gate separates a narrow channel from a reed-filled basin. A dirt service track runs beside it toward a low brick building. |

Keep the previously recorded requested configurations and settings, with `provider.allow_fallbacks=false`, one sole provider, and no silent substitution:

| Exact model ID | Sole provider | Rendering settings |
|---|---|---|
| `openai/gpt-image-1` | `openai` | square, medium quality, opaque background |
| `openai/gpt-image-2` | `openai` | square, medium quality, opaque background |
| `openai/gpt-image-2.5-flare` | `openai` | square, medium quality, opaque background |
| `openai/gpt-image-2.5-sunburst` | `openai` | square, medium quality, opaque background |
| `google/gemini-3.1-flash-image` | `google-ai-studio` | square, 1K resolution |
| `black-forest-labs/flux.2-max` | `black-forest-labs/us-3` | square, PNG output |

Before later execution, verify current documented route availability and pricing without spending on pilots unless separately authorized. Current price verification has not been performed. Preserve actual reported model/provider metadata and timestamps; acceptance alone does not authenticate hidden checkpoints or establish unchanged service state.

## Timing, randomization, and freeze

The proposed session starts are **T0 + {0, 8, 24, 32, 48, 56, 72, 80} hours**, spanning four days. T0 and its time zone must become an absolute timestamp before the precollection freeze. Each session has a four-hour dispatch window. At five seconds between starts, the theoretical lower bound for 576 starts is about 48 minutes; API latency, the three-active limit, retries and pauses can increase it. The prior 1,008-output collection took about 167 minutes, suggesting about 95 minutes per new session at the same throughput, not guaranteeing it.

Within each session, randomize the entire 576-slot list across configurations, scenes and arms using seed `2026091908 + session_index`, with indices 0–7. Save the exact resulting order. Do not finish one scene before moving to another, and do not execute painter arms or configurations as contiguous batches. Each cell receives exactly one assigned request per session; session identity is the repeat block. Identical prompts remain identical: there is no changing seed/text tag that creates an extra prompt intervention. Record any available service seed or caching metadata without treating their presence as proof of independence.

Freeze and hash the new protocol, all 4,608 payloads, assignment order, session windows, failure/admission rules, endpoint formulas, analysis code and constructed-case checks, reference/scaler identities, checkpoints, preprocessing, runtime lock, cost baseline and storage destination before the first request. Use new request IDs, paths, ledgers and a new create-once terminal receipt. **No old collector, receipt, image, frozen analysis, or manuscript changes.** A local hash/timestamp is not a third-party preregistration. Scientific feature extraction and visual selection must not influence ongoing collection; measure after terminal closure.

Eight scheduled sessions do not provide eight proven independent service states. They make temporal variation inspectable and reduce scene/time confounding. The experiment remains conditional on these windows; it cannot identify hidden checkpoint changes, caching, persistent shared state, or arbitrary cross-session covariance.

## Primary analysis and concrete decision rule

Use the existing 649-work primary reference panel, with equal weight to each painter. The primary representation is the **already fixed public CSD checkpoint and its native preprocessing**, chosen to address the learned prototype-gain claim directly. It is a measurement choice, not ground truth. Its released-weight discrepancy, all-four-painter training-tag overlap, and unknown training-image overlap remain disclosed. Use the fixed CLIP checkpoint and 31-feature pipeline as prespecified secondary sensitivities, with no representation selected after new results. Preserve original/audited-region and development-panel sensitivities as secondary; do not introduce new crops or reference works.

For one model and session, average over the 12 fixed scenes. Let `g_a` be the named mean unit embedding, `g_G`, `g_S`, and `g_F` the generic, style-frame and family means, and `mu_a` the **unnormalized** reference prototype. Bars are equal-painter averages. Define the following absolute cosine-gain quantities before any ratios:

```
N = mean_a dot(g_a, mu_a) - dot(g_G, mean_a mu_a)
F = dot(g_F - g_G, mean_a mu_a)
S = dot(g_S - g_G, mean_a mu_a)
L = mean_a dot(g_a - mean_a g_a, mu_a - mean_a mu_a)
C_G = dot(mean_a g_a - g_G, mean_a mu_a)
C_F = C_G - F
T = F - 0.5 * N
```

`N = C_G + L` is the named-minus-generic diagonal prototype gain. `F` is gain caused by the painter-name-free family condition relative to the contemporaneous generic control, averaged over the four reference prototypes. `S` measures the specified style-framing condition, and `F-S` compares family with framing. The remaining named-minus-family gain is `N-F = C_F+L`. The labeled term is unchanged by subtraction of any common control **by algebra**; that invariance is not independent validation.

The **primary family contains 12 endpoints: N and T for each of six configurations in CSD**. Compute one value per complete session, then average the eight session values, always keeping the fixed scene panel equally weighted. Report approximate two-sided 95% simultaneous Student intervals with Bonferroni adjustment over these 12 endpoints and seven degrees of freedom. This uses variation between full-panel sessions, not a scene bootstrap or 12 authored scenes treated as population draws.

The operational decision is prespecified:

- If the simultaneous lower bounds of both `N` and `T` exceed zero for a configuration, a no-individual-name family instruction reproduces more than half its positive named-minus-generic gain. **For this configuration and workload, do not treat that aggregate gain as evidence that most of the gain required individual painter identity.** Report a family-matched comparator and labeled alignment when making an individual-name evaluation claim. Common historical-family movement may still be a legitimate style benefit.
- If `N` is clearly positive but the upper bound of `T` is below zero, this family clause does not reproduce half that gain. Retain this outcome: it weakens the proposed explanation that the headline finding mainly reflects the omitted family instruction. It does not prove general perceptual fidelity or eliminate other common effects.
- If either required interval crosses its decision boundary, report the question as unresolved. A positive point estimate, a non-significant difference or failure to reject zero is not evidence of equivalence.

The 50% boundary is a declared **majority-attribution decision threshold**, not a perceptual tolerance. Linear `T` avoids unstable inference from a small ratio denominator. Report `F/N`, `C_G/N`, `(C_G-F)/(N-F)` and the corresponding raw common/labeled/total terms only with denominators displayed; undefined/nonpositive-denominator shares remain unavailable, and signed absolute terms and fractions outside [0,1] are retained. Do not clip inconvenient outcomes.

This is a controlled prompt-intervention test of whether one aggregate measurement can specifically support an individual-name claim. The family arm has no manipulated individual-painter label by design. Its measured size is new empirical evidence; manufacturing four copies with arbitrary painter labels would only force a centered zero and is not proposed as validation. Neither a lower D nor higher real-painter recognition determines the correct answer to this decision task.

### Prespecified secondary reporting

Report all arms, all configurations and all sessions, including:

- Absolute `S`, `F-S`, `N-F`, `C_G`, `C_F`, and `L`; reference contrast energy; original and family-baseline gains. These show whether wording, family information, or residual named response supplies the measured change. They do not provide a unique causal partition of semantics.
- The same quantities in CLIP; free-baseline contrasts; 31-feature common/specific squared changes. **Prototype cosine-gain fractions and cross-repeat squared-change fractions remain different quantities.**
- All six pairwise aligned responses, including Monet–Sisley; normalized-prototype recognition and per-painter confusions; the existing real-development recognition baseline. A positive beta is not successful perceptual discrimination.
- Session-by-session original-headline quantities and repeat variability, not just one pooled percentage. Report approximate, explicitly secondary Fieller intervals for positive-denominator common-gain ratios from the eight paired session values; unbounded/disconnected sets must remain so. These are conditional approximations, not additional familywise claims.
- Contrast D and squared-change decompositions using cross-session products as secondary diagnostics, retaining negative estimates. Compare cross-products from sessions on different days with same-day sessions and report the difference descriptively. These products require zero relevant cross-session error covariance; measured temporal separation does not establish it. No new D-based winner or fidelity claim is proposed.

No secondary result may replace the primary criterion. A control that explains little, reversed labeled effects, unstable signs, or incompatible representations must remain in the report. New data may weaken the manuscript's current claim. Do not pool old and new cohorts to manufacture the prospective sample size or continue sampling until a favorable result appears.

## Precision and uncertainty limits

The Student procedure is approximate and assumes independent, suitably behaved full-panel session summaries. With eight sessions and 12 simultaneous endpoints, the half-width is **1.4758 × the observed between-session SD** of the endpoint. For example, SDs of 0.005, 0.010 and 0.020 cosine-gain units yield half-widths of about 0.0074, 0.0148 and 0.0295. These illustrate the formula; they are not estimates of new-service variability or a promised power calculation. A small positive `T` can remain unresolved.

Always show the eight session values, timestamps, block missingness and leave-one-session influence. Under a simple equal-positive-correlation sensitivity model, report uncertainty multipliers for session correlation rho = 0, 0.1, 0.25 and 0.5. Relative to the naive SE from the observed sample SD, use `sqrt((1+7*rho)/(1-rho))`; these are assumptions, not estimated corrections or a guaranteed bound. Persistent common state can remain unidentifiable even with eight sessions. Do not call ordinary intervals valid under arbitrary dependence.

The new scenes are a fixed authored panel of outdoor compositions. This design measures repeated requests on that panel; it does not estimate a distribution over all scenes, extend to different painter groupings, or disentangle new-content effects from later service changes relative to the old collection. The retained learned audit supplies same-image representation sensitivity; this proposal supplies fresh requests with new contemporaneous controls. Neither supplies independent reference-source acquisition or perceptual truth.

## Historical cost and spending gates

The terminal collection record remains **$112.293676**, including its carried historical uncertainty reserve. Its 1,008 settled attempts cost $43.786326, with 168 outputs per configuration. The terminal ledger SHA-256 is `b131798cd2b803d6d60569def72700bb35daacdd2c5602e0dc854b7bd77a3ffd`. The existing cumulative ceiling is **strictly below $120**; the remaining $7.706324 does not authorize new collection. An unchanged $5 active reservation leaves only $2.706324 of settled headroom for further admission under that ceiling. This design cannot run under it.

| Requested configuration | Historical mean/output | Historical maximum/output | Planned outputs |
|---|---:|---:|---:|
| GPT Image 1 | $0.042481667 | $0.042520 | 768 |
| GPT Image 2 | $0.052921667 | $0.052960 | 768 |
| GPT Image 2.5 Flare | $0.013411667 | $0.013450 | 768 |
| GPT Image 2.5 Sunburst | $0.013411667 | $0.013450 | 768 |
| Nano Banana 2 | $0.068406226 | $0.068612 | 768 |
| FLUX.2 Max | $0.070000000 | $0.070000 | 768 |

The new allocation is 32/7 times the old balanced grid. Historical means give **$200.166061714** in new charges and **$312.459737714 cumulative**. Historical model maxima give **$200.441856**. Allow at most **96 total technical retries**, no more than two retries per slot; at the largest observed $0.07 charge, this adds $6.72. Adding all three active $5 reservations to that maximum-rate projection gives **$334.455532 cumulative**, $15.544468 below the proposed $350 ceiling. The rates are historical estimates, not live prices or upper bounds; the longer family clause can change token charges.

Proposed gates after separate authorization:

- Preserve **$5 per active paid attempt**, at most three active attempts and starts at least five seconds apart. Existing historical reservations are not released or recycled.
- Before each start, require cumulative settled accounting plus outstanding reservations plus the new $5 reservation to be strictly below $350. Stop new starts if new-run settled charges reach **$220**, a separate operating stop threshold rather than a reservation-inclusive cap. Pending charges still settle and retain their reservations until known.
- Unknown charges, a charge above $5, or an unmatched start after a crash pause dispatch and require evidence reconciliation. An unknown is never treated as zero. No silent ceiling increase or balance inquiry substitutes for accounting.

## Storage: capacity, not just a free-space threshold

Historical files were measured read-only; no raw-response contents were printed. The existing collector retains both decoded image files and gzip-compressed raw JSON responses containing the base64 image. Therefore counting pixels alone understates disk use by roughly a factor of two. Byte totals from the completed 1,008 outputs are:

| Retained component | Historical bytes | Projected bytes for 4,608 | Projected GiB |
|---|---:|---:|---:|
| Image payloads | 2,079,642,175 | 9,506,935,657 | 8.854 |
| Gzip raw-response archives | 2,073,483,308 | 9,478,780,837 | 8.828 |
| Combined persistent collection | 4,153,125,483 | 18,985,716,494 | **17.682** |

The historical **uncompressed** response JSON totals 2,773,296,145 bytes; scaled to this design it is 12,677,925,234 bytes, or 11.807 GiB. It is already represented by the gzip row, not an additional persistent copy. Do not write a second full uncompressed archive. If that storage contract changes, recompute capacity: images plus uncompressed JSON alone would be 20.661 GiB. The historical allocated disk blocks are slightly larger than logical file sizes (scaled persistent total approximately 17.699 GiB).

Plan additional space for:

- **0.368 GiB** for 96 retry artifacts at historical average combined size. This is an estimate, not a maximum; failed responses and changed formats can differ.
- **3.864 GiB** for both public extraction weights: CLIP safetensors 1,710,540,580 bytes plus CSD bin 2,438,228,893 bytes. Their previously fixed revisions and hashes must be reused and verified. No download has been made for this proposal.
- **2 GiB** for bounded temporary downloads, per-file decompression, manifests, features and reports. Avoid a full duplicate image archive; extra packaging or duplicated model caches needs a separately accounted allowance.
- A **25% allowance on collection and retry storage** for image-size variation, plus the **unchanged 5 GiB actual free-space floor**.

Together these sum to about **33.43 GiB**. Require a user-provided destination with **at least 40 GiB actually free at preflight**, covering outputs, response archives, cache and temporary files. This is a planning requirement, not a guarantee for arbitrarily large service responses. Existing references can be read in place; copying the 870 reference/development images would add about 2.120 GiB and must be counted on the destination. Do not duplicate all previous outputs unless separately budgeted.

The current filesystem check found **2,674,827,264 free bytes: 2.67 decimal GB, 2.49 GiB**, consistent with the reported approximately 2.6 GB and already below the 5 GiB floor. Collection and weight retrieval are therefore blocked pending additional user-provided storage or space. Merely reaching 5 GiB would satisfy only the stop floor, not this collection's capacity. A larger destination must be real and writable, not a nominal quota or purgeable-space estimate; do not delete unique artifacts to make room.

Before each start, preserve at least 5 GiB actual free space on every volume receiving run files. For the new collector also reserve 256 MiB of destination capacity per active request, including the proposed start, consistent with retaining the existing 64 MiB raw-response limit and decoded payload. If actual free space minus these outstanding storage reservations would fall below 5 GiB, pause before sending another paid request. A cache/temp directory on another volume must independently pass its space check; directing outputs externally does not excuse an undersized volume still receiving writes. Recheck before downloading weights or writing derived artifacts. Do not remove raw responses, unique images or old evidence to evade the guard.

## Failure, missingness, and completion

Retry only completed 429/500/502/503/504 or network failures, with identical payloads, 20/60-second minimum delays, at most two retries per slot and 96 across the run. Retries enter a delayed queue within their assigned session; do not backfill a missing session observation in another time window. No automatic retry for content refusal or other client rejection, no fallback configuration, no quality reduction and no aesthetically motivated replacement.

Three consecutive technical failures, request/route mismatch, budget uncertainty, an operator pause or disk-floor violation stops new dispatch and drains active requests. The four-hour window and future session schedule are frozen; unresolved slots remain missing. Repairs require a recorded technical explanation and cannot change the scientific allocation or consume extra slots. A material route/model change terminates this protocol rather than being mixed silently into the cohort.

For the declared primary fixed-panel estimand, a model/session requires all 12 scenes and the needed generic, family and four named arms; framing/free failures are separately reported. **A resolved primary decision requires all eight primary-complete sessions for that model.** If any are missing, report the incomplete census and available-block estimates descriptively, without claiming the original fixed-panel decision was resolved. No imputation, outcome-dependent subset, adaptive sample-size increase or replacement scene is permitted. Report all six configurations even when incomplete; a failure cannot silently remove a difficult configuration from the stated population.

Close generation permanently with a new terminal receipt after the frozen windows or documented terminal failure. Retain every attempt, payload, successful original pixel, response archive, hash, timing record and exception. The final report must include all primary endpoints and contrary findings. A reviewable exact-pixel/attribution release remains separate work; local retention alone does not resolve public reproducibility.

## Evidence read for this proposal

- All three completed `round_02/reviewer_{contribution,empirical,method}.md` reports; their scores are not targets for this plan.
- `reports/icml_review_v1/prospective_replication_options.md`, preserved unchanged.
- Terminal collection, requests and attempt ledgers under `data/manifests/painter_specificity_v2/psv2-20260911/` for historical costs, timing and local file paths.
- `studies/painter_specificity_v2/PROTOCOL.md` and existing collector code for route, financial, archive and failure contracts; no collector was invoked.
- `reports/icml_review_v1/artifact_inventory.json` and local image/response file sizes for capacity planning; the raw JSON byte counts use gzip's retained length metadata.
- Previously retained learned checkpoint metadata for weight sizes. No live pricing lookup or external service query was needed or performed.

The main scientific limitation remaining after this proposed experiment would be the finite historical reference target and its relation to perception. The experiment is designed to clarify one evaluation decision and its fresh-request uncertainty, not to manufacture a better model ranking or guarantee a higher review score.
