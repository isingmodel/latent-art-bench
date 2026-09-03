# Painter Feature Generation v1

This is the active study. It asks:

> When a frozen generative model is prompted with a painter's name, do its outputs reproduce the
> measurable feature distribution of that painter's authentic paintings under the same broad
> outdoor-place content frame?

The only canonical plan is [`PROTOCOL.md`](PROTOCOL.md), protocol ID
`painter-feature-generation-v1/2.0`.

## Design in one page

- **Unit:** one physical painting, not one file or museum row.
- **Painters:** Monet, Sisley, Pissarro, and Cézanne.
- **Real domain:** authority-verified oil-on-canvas outdoor-place paintings with lawfully reusable,
  technically adequate digital surrogates.
- **Content control:** retain at least three broad scene groups supported by all painters and give
  every retained group equal mass. Within a group, use every eligible work.
- **Primary measurement:** three separately qualified interpretable families—color organization,
  spatial/orientation organization, and multiscale digital texture organization.
- **Generated experiment:** the same scene prompts under four painter-name conditions and one
  artist-free control, with paired seeds and no rerolling or output selection.
- **Decision:** absolute distributional equivalence, all-painter specificity, improvement over the
  artist-free control, coverage, availability/adherence, and copy exclusion must all pass.
- **Claim ceiling:** the result concerns the closed accessible digital-surrogate frame, not a
  probability sample of each painter's complete oeuvre.

Painter classification, centroid similarity, FID, CLIP, CSD, Kim A/C, and human preference cannot
alone establish painter-feature reproduction. They are diagnostics only.

## Corpus rule

The retired 360-work-per-painter target had no literature or power basis and was infeasible for
the current evidentiary state. Protocol 2.0 instead:

1. exhausts every prospectively declared source;
2. reconciles all rows into one physical-work union;
3. preserves actual unequal painter counts;
4. restricts every historically pixel/feature-exposed work to development; and
5. assigns every new eligible work once to development, qualification, or confirmation by the
   frozen 20%/20%/60% hash rule.

Generation is allowed only if every painter has at least three common scene groups; every retained
painter × scene group has at least 10 new-development, 10 qualification, and 20 confirmation works;
the confirmation equal-scene Kish ESS is at least 100; work/source/capture influence is acceptable;
and the whole-decision simulation succeeds. These are conjunction gates, not a target-count stopping
rule.

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
- Active-study admitted works, downloaded image files, confirmation features, generation attempts,
  and results are all zero.

The next actions are the remaining named source censuses — Europeana, NGA, Cleveland, Yale, Getty,
Minneapolis, Paris Musées, and POP/Joconde — and authority/rights/identity reconciliation across
their union. Image acquisition is a separate later gate.

## Supporting material

- [Korean research and data report](../../reports/painter_feature_generation_v1/RESEARCH_PLAN_AND_DATA_REPORT_KO.md)
- [Literature package](../../literature_reviews/README.md)
- [Focused generated-versus-real review](../../literature_reviews/reviews/06_generated_vs_real_painter_fidelity.md)
- [Current project status](../../docs/STATUS.md)

Historical pilots and the real-only `painter_features_v1` study remain frozen evidence. They are not
alternative active plans and must not be rewritten to match Protocol 2.0.
