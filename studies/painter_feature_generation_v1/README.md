# Painter Feature Generation v1

This is the active study. It asks:

> When a frozen generative model is prompted with a painter's name, do its outputs reproduce the
> measurable feature distribution of that painter's authentic paintings within the same
> metadata-declared outdoor-place content frame?

The only canonical plan is [`PROTOCOL_2.1.md`](PROTOCOL_2.1.md), protocol ID
`painter-feature-generation-v1/2.1`, issued 2026-09-04. [`PROTOCOL.md`](PROTOCOL.md) is the frozen
Protocol 2.0 text bound by the completed census freezes; it is superseded, not edited.

## Design in one page

- **Unit:** one physical painting, not one file or museum row.
- **Painters:** Monet, Sisley, Pissarro, and Cézanne.
- **Real domain:** authority-verified oil-on-canvas paintings whose metadata declares an outdoor
  place under a frozen lexicon, with lawfully reusable, technically adequate digital surrogates.
  No human codes any image.
- **Content control:** one outdoor-place domain with uniform work weights; scene type is a
  generated-side diagnostic only.
- **Primary measurement:** three separately qualified interpretable families—color organization,
  spatial/orientation organization, and multiscale digital texture organization.
- **Generated experiment:** all 16 outdoor-place prompts under four painter-name conditions and one
  artist-free control, with paired seeds and no rerolling or output selection.
- **Decision:** absolute distributional equivalence, all-painter specificity, improvement over the
  artist-free control, coverage, availability, and copy exclusion must all pass; prompt adherence
  is an automated diagnostic.
- **Operator:** one person may hold the custodian, method-analyst, and generation-operator roles
  sequentially under technical sealing with an access ledger, a disclosed limitation.
- **Claim ceiling:** the result concerns the closed accessible digital-surrogate frame, not a
  probability sample of each painter's complete oeuvre.

Painter classification, centroid similarity, FID, CLIP, CSD, Kim A/C, and human preference cannot
alone establish painter-feature reproduction. They are diagnostics only.

## Corpus rule

The retired 360-work-per-painter target had no literature or power basis and was infeasible for
the current evidentiary state. Protocol 2.1 instead:

1. exhausts every prospectively declared source;
2. reconciles all rows into one physical-work union;
3. declares outdoor-place eligibility from metadata with a frozen lexicon;
4. preserves actual unequal painter counts;
5. restricts every historically pixel/feature-exposed work to development; and
6. assigns every new eligible work once to development, qualification, or confirmation by the
   frozen 20%/20%/60% hash rule within painter × workflow.

Generation is allowed only if every painter has at least 10 new-development, 10 qualification, and
100 confirmation works (uniform weights, so ESS equals the count); the 60-work auxiliary capture
panel and workflow-crossing gates hold; and the whole-decision simulation succeeds. These are
conjunction gates, not a target-count stopping rule. In practice each painter needs about 179
newly eligible works.

## Current evidence

- The material-constrained exploratory Wikidata seed contains 3,190 item candidates and 3,364
  distinct Commons filenames.
- The reviewed fixed-seed audit completed all 165 metadata requests. Of 3,367 item–file rows, 2,029
  rows (1,967 distinct item IDs; 2,028 distinct Commons filenames) passed the exact-creator,
  current-P18, open-rights-marker, supported-format, and short-side ≥1,024 discovery gate. They are
  candidates, not authority-verified physical works or downloaded paintings.
- A separate official-source audit contains 43 all-content candidates. It is not a complete source
  census and none is admitted.
- The independently reviewed no-`P186` discovery census completed four of four painter queries and
  produced 3,722 item–image rows, 3,543 distinct Wikidata item IDs, and 3,718 distinct Commons
  filenames. These remain discovery candidates rather than verified or downloaded works.
- The reviewed 182-request broad-media follow-up R1 reached a terminal first response when Wikidata
  returned an HTTP 200 plural `errors` envelope containing `maxlag` plus `Retry-After: 5`; the R1
  parser did not recognize that representation. It published no partial manifest or receipt and
  cannot be retried under the same census ID.
- A separately frozen and neutrally reviewed R2 added only strict support for that observed plural
  MediaWiki error envelope. Under a new census ID and disjoint paths it completed all 182 requests
  on their first R2 attempt, preserving 365 hash-chained events and 182 raw responses. The resulting
  3,722-row manifest contains 2,029 metadata-qualified candidates, but zero images or admissions.
- The reviewed Art Institute of Chicago route census terminated fail-closed on its first request
  because AIC returns `classification_id` as a nonblank string identifier while the R1 parser
  required an integer. It published no manifest or receipt.
- A separately frozen and neutrally reviewed AIC R2 changed only that field's type rule. Under a new
  census ID and disjoint paths it completed all four exact artist-ID requests on their first attempt,
  preserving nine hash-chained events and four raw responses. Of its 153 holding-record rows, 57
  across 57 distinct accession numbers pass both the AIC authority-record screen and the
  metadata/media screen — Monet 33, Sisley 6, Pissarro 9, and Cézanne 9. The Pissarro and Cézanne row
  totals are dominated by prints and works on paper. These rows are not reconciled against the
  Wikidata/Commons census and are not added to it as independent works.
- The §11.1 prompt library has been rendered from the protocol text as an exact JSON artifact and
  the §8 exposure denylist has been rebuilt from pinned git history (122 pixel-exposed physical
  works, development-only). Neither is yet neutrally reviewed or frozen.
- A non-binding corpus pre-screen
  ([Korean summary](../../reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md))
  found that Protocol 2.0's four-way scene cells could not be supported even at the metadata upper
  bound, which is why 2.1 removed scene stratification. Under 2.1 the lexicon upper bound of
  eligible items with a collection QID is Monet 529, Sisley 193, Pissarro 256, and Cézanne 200
  against a floor of 179; all clear at the upper bound and Sisley is the binding risk.
- Active-study admitted works, downloaded image files, confirmation features, generation attempts,
  and results are all zero.

The next actions are the neutral review and freeze of the prompt library, content lexicon, and
exposure denylist, then the remaining named source censuses — Europeana, NGA, Cleveland, Yale,
Getty, Minneapolis, Paris Musées, and POP/Joconde — on the shared census engine, and
authority/rights/identity reconciliation across their union. Image acquisition is a separate later
gate.

## Supporting material

- [Korean research and data report](../../reports/painter_feature_generation_v1/RESEARCH_PLAN_AND_DATA_REPORT_KO.md)
- [Literature package](../../literature_reviews/README.md)
- [Focused generated-versus-real review](../../literature_reviews/reviews/06_generated_vs_real_painter_fidelity.md)
- [Current project status](../../docs/STATUS.md)

This study's own sealed evidence — freezes, neutral reviews, authorization seals, append-only
request ledgers, and published manifests — must not be rewritten to match a later reading of
either protocol version. A terminal census stays terminal.
