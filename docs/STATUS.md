# Current status and research boundary

Operational date: 2026-09-02

This page is mutable operational state. Frozen historical protocols, ledgers, and receipts remain
authoritative for their own completed actions.

## Active research question

The active study is **Painter Feature Generation v1**:

> For one exact model and one pre-label common outdoor-place prompt census, do painter-name outputs
> reproduce the broad-scene-weighted distribution of color, spatial/orientation, and digital-texture
> features in authority-record-exactly-attributed paintings by Monet, Sisley, Pissarro, and Cézanne?

The only canonical plan is
[`studies/painter_feature_generation_v1/PROTOCOL.md`](../studies/painter_feature_generation_v1/PROTOCOL.md),
protocol ID `painter-feature-generation-v1/2.0`.

The claim is deliberately finite and technical: broad-scene-weighted digital-surrogate feature
reproduction in the closed accessible frame. It is not painter classification, authorship,
content-free style, physical brushwork, artistic intention, or a probability-sampled oeuvre claim.

## Current stage

The study completed the **R0 fixed-seed metadata follow-up** and remains **NO-GO for full R0 closure
and R1 image acquisition**.

Completed in the Protocol 2.0 redesign:

- corrected the estimand to generated-versus-real painter feature distributions;
- retired the unsupported equal 360-work quota, three-way active-real split, 24-template selection,
  and high-dimensional entropy weighting;
- fixed an exhaustive named source union and physical-work/capture identity graph;
- defined actual unequal painter populations with equal mass across every commonly supported broad
  scene group and all eligible works retained within group;
- defined screening floors of at least three common groups, at least 20 physical works per retained
  group, equal-scene ESS at least 100, crossed source workflows, and a 60-work independent-capture
  auxiliary panel, with whole-decision simulation still binding;
- restricted historically exposed works to development and fixed a prospective 20%/20%/60%
  development/qualification/confirmation assignment for every new eligible work;
- fixed all 16 candidate prompt strings and the render-independent contract before active visual
  labels; unsupported groups can only be removed by the deterministic count rule;
- specified three required feature families—color, spatial/orientation, and digital texture—with
  common normalization and no learned feature as primary;
- required all three families to qualify; no favourable family subset can produce the painter label;
- specified energy-distance estimation, margins, specificity, artist-free control improvement,
  coordinate coverage, per-scene coverage, source/work influence, simulation, and simultaneous
  inference;
- kept every off-topic generated output in its assigned primary cell; adherent-only analysis is a
  sensitivity, not a selection rule;
- required a complete technically analyzable generated grid and zero confirmed searched-corpus
  real-work copies for a positive claim; generated duplicates remain with full multiplicity; and
- defined role-separated acquisition, blind coding, method, generation, and confirmation access.

The first authorized fixed-seed audit was executed on 2026-09-02 and terminated exactly as
specified. Four Wikidata batches succeeded. The fifth returned HTTP 200 but exposed a valid
MediaWiki `languagefallback` term representation that the frozen parser did not support, producing
`terminal_stage_schema_failure`. Its 11-event hash-chained ledger and five response bodies are
preserved; no result manifest or execution receipt was issued, and none of its successes will be
spliced into the retry.

The complete, newly authorized R2 retry then:

- a fixed-seed metadata-only follow-up of 3,190 Wikidata items and 3,364 Commons filenames;
- 165 exact GET intents (80 Wikidata entity batches and 85 Commons file batches);
- a fail-closed collector that validates current P18 linkage, rights markers, reported geometry,
  exact member coverage, origin/redirect behaviour, retries, atomic receipts, and non-admission
  manifests; and
- a corrected fallback-term parser and focused regression tests;
- a new census ID, complete 165-request intent set, separate output paths, and explicit hash-bound
  linkage to the terminal first census; and
- passed neutral independent review with no blocking finding;
- completed all 165 requests on first attempt (80 Wikidata and 85 Commons), producing 331
  hash-chained events and 165 content-addressed raw responses (about 51 MiB locally); and
- emitted a 3,367-row non-admission candidate manifest and execution receipt.

The first prospective broad no-`P186` census (`pfg-v1-broad-wikidata-no-p186-20260902`) was
independently approved and executed on 2026-09-02. Monet completed with 1,317 discovery-only rows.
The next, Sisley, request returned provider HTTP 502 with `text/html`; the census therefore ended
terminally after five hash-chained events. Its one-shot lock and both raw responses are preserved,
and it emitted neither a candidate manifest nor an execution receipt. No R1 row is reusable.

The independently reviewed R2 census then repeated the same four exact queries and parser, scope,
cutoff, and all-or-none terminal rule under a new census ID and disjoint paths. Its only operational
change was a five-second rather than two-second minimum request interval. The retry gate binds the
exact R1 config, freeze, review, authorization, terminal ledger/event, one-shot lock, both raw
responses, absent candidate/receipt, and exact allowed config delta. Neutral quality review found
and closed two execution-boundary file-binding defects before approval. R2 then completed all four
requests on first attempt and emitted 3,722 discovery-only item-image rows: 3,543 distinct Wikidata
item IDs and 3,718 distinct Commons filenames. No image was downloaded and no work was admitted.

The separately reviewed broad-media follow-up then froze 182 exact metadata-only requests covering
all 3,543 item IDs and 3,718 filenames. Neutral review identified and closed deterministic ordering,
single-read CAS, terminalization, retry-ledger, cutoff/resume, path-confinement, and atomic-publication
defects before approval. Execution reached the first Wikidata batch once. The provider returned a
parser-complete HTTP 200 response together with `Retry-After: 5`; the frozen rule classified that
unexpected combination as `terminal_retry_after_new_census_required`. The three-event ledger and
one raw response are preserved. No candidate manifest, execution receipt, image, or admission was
issued, and this census must not be retried or spliced.

Still not completed:

- the other terminal source routes named in Protocol 2.0;
- authority, rights, physical-work, capture-family, and image-quality reconciliation;
- active image acquisition;
- masked double coding, reliability/adjudication, source crossing, corpus closure, or scene support;
- the frozen new-work role manifest and the 60-work capture panel;
- feature implementation/fixtures/qualification, margins, or simulation results;
- model/prompt/seed G0 freeze;
- generation; or
- confirmation and generated-versus-real results.

## Active counts

| Quantity | Count | Meaning |
|---|---:|---|
| exploratory Wikidata item candidates | 3,190 | material-constrained discovery identifiers, not verified works |
| distinct Commons filenames in that seed | 3,364 | file identifiers, not physical works |
| completed R2 metadata requests | 165 / 165 | all first-attempt successes; no R1 success reused |
| completed R1 metadata requests | 4 | verified success before the fifth request terminated R1 |
| terminal R1 requests | 1 | valid provider representation unsupported by the frozen parser |
| R2 metadata-qualified rows | 2,029 / 3,367 | fixed-seed discovery gate; not physical works |
| R2 distinct qualified item IDs | 1,967 | not identity-reconciled physical works |
| R2 distinct qualified filenames | 2,028 | files, not independent works or captures |
| broad no-P186 R1 successful requests | 1 / 4 | Monet response only; not reusable outside terminal R1 evidence |
| broad no-P186 R1 terminal requests | 1 | Sisley HTTP 502; whole R1 census incomplete |
| broad no-P186 R1 observed rows | 1,317 | discovery-only Monet rows inside an incomplete census; no manifest issued |
| broad no-P186 R2 requests | 4 / 4 | all first-attempt successes; R1 success was not reused |
| broad no-P186 R2 discovery rows | 3,722 | exact-creator painting+image rows; not physical works |
| broad no-P186 R2 distinct item IDs | 3,543 | current Wikidata identifiers before authority/identity reconciliation |
| broad no-P186 R2 distinct filenames | 3,718 | Commons filenames; not independent works or captures |
| broad-media follow-up planned requests | 182 | 89 entity + 93 media batches, metadata only |
| broad-media follow-up attempted requests | 1 | terminal HTTP 200 + advisory Retry-After representation |
| broad-media follow-up manifests/receipts | 0 / 0 | all-or-none publication correctly withheld |
| separately observed official-source all-content candidates | 43 | traceable live records, not a terminal source census |
| admitted active physical works | 0 | none has passed every gate |
| downloaded active-study image files | 0 | metadata collection cannot download images |
| sealed confirmation works | 0 | frame not closed |
| registered generation attempts | 0 | G0 closed |
| generated outputs | 0 | G1 closed |
| generated-versus-real results | 0 | no empirical painter claim authorized |

The earlier 40-file Commons follow-up ended with HTTP 429 and remains superseded evidence. The R2
fixed-seed result establishes current metadata attrition only. It does not establish a reusable-file
corpus, authority-verified work count, complete source frame, or outdoor-place content yield.

## Data and source policy

Protocol 2.0 closes the candidate union to:

1. the broader exact-creator Wikidata/Commons painting+image census without material filtering;
2. Europeana exact creator;
3. AIC, NGA, Cleveland, Yale, Getty, Minneapolis, and Paris Musées APIs/exports;
4. POP/Joconde; and
5. the material-constrained fixed seed for current attrition/reconciliation only.

Discovery records locate candidates. Authority records establish work identity, exact attribution,
object type, medium/support, and accession. Media/capture records establish lawful reuse, geometry,
and delivery. These layers can describe the same work and are never added as independent counts.

Every source must reach its frozen terminal condition. Reaching a capacity number is not a stop
rule. A source is not replaced or topped up after results. One physical work contributes once;
mirrors, crops, filenames, encodings, or hashes do not increase the work count. Only provenance-
demonstrated distinct capture events enter the auxiliary capture panel.

The active source mixture must be crossed with painter: every painter requires at least two
authority/capture workflows, the incidence graph must be connected, and no workflow may carry more
than 0.80 of a painter's equal-scene weight. Otherwise painter and source are inseparable and no
painter-reproduction label is allowed.

## Required next sequence

1. Preserve and report the completed fixed-seed result without calling it a complete source frame.
2. Preserve the completed broad no-`P186` census, then freeze and execute the other named source
   routes to terminal conditions; reconcile their union to physical works.
3. Under a separate R1 authorization, verify authority/rights/capture identity and acquire lawful
   technically adequate image bytes.
4. Run role-separated R2 coding and close the unequal finite frame; generation remains NO-GO until
   every corpus adequacy gate passes.
5. Run M0a/M0b, auxiliary capture qualification, margins, copy calibration, and whole-decision
   simulation. All three families must pass.
6. Freeze one exact model, prompts, render settings, seeds, `R`, request order, and analysis at G0;
   then generate and seal G1 while confirmation features remain inaccessible.
7. Open the confirmation reference once at C0 and execute the frozen decision.

## Historical evidence boundary

### Painter Features v1

`studies/painter_features_v1/MEASUREMENT_PROTOCOL.md` is a frozen real-image measurement precursor,
not the active plan. Collection Freeze 3 acquired four exact NGA files (two Pissarro and two Monet),
all on first-attempt HTTP 200. Its protocol, seal, ledgers, report, paths, and hashes must not be
rewritten or moved.

### Pilots 0–3

- Pilot 0 is a failed historical qualification path.
- Pilot 1 completed engineering traversal but failed both scientific measurement gates.
- Pilot 2 executed 320 assigned requests; refusals left both requested-label feature grids
  incomplete, so the four primary tests were not run and the decision was `REDESIGN`.
- Pilot 3 acquired its AIC development half. Its Met R2 path closed on the first terminal HTTP 403
  metadata response before any Met image request.

These outcomes are evidence. Do not repair them with new data or refresh historical hashes.

## Explicitly closed actions

Until the corresponding Protocol 2.0 freeze is independently reviewed, do not:

- retry or replace Pilot 3 Met R2;
- access the sealed Pilot 3 external holdout;
- extract features from the incomplete Pilot 3 cohort;
- treat metadata rows, files, or the four historical NGA files as an active painter distribution;
- download active-study images under the metadata-only census;
- view confirmation-resolution pixels/features as a method or generation analyst;
- tune prompts, features, thresholds, margins, or source rules on generated/confirmation outcomes;
- send generation requests; or
- rewrite/move frozen historical evidence.

## Repository health boundary

The standard offline checks are:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

Historical `pilot2 verify` and planning-era `pilot3 verify` intentionally expose old source-hash
drift or unavailable ignored evidence. Do not regenerate frozen bundles merely to make those
historical checks green.
