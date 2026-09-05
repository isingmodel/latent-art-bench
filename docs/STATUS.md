# Current status and research boundary — 2026-09-05

The maintainer has changed the immediate deliverable to an **analysis report of available image
models**, explicitly deferring a prototype research paper and offering GPT-Image-1 / GPT-Image-2
through the local Codex OAuth proxy. See the
[completed model-access analysis](../reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md).
**Painter Feature Generation v2** is the active implementation;
[its protocol](../studies/painter_feature_generation_v2/PROTOCOL.md) preserves the original research
question and the v1 evidence while enabling a complete comparative paper without asserting
uncalibrated equivalence. V1's strict reproduction claim remains unestablished.

Current v2 state:

- 1,193 recorded work identities retained; no additional works acquired from new metadata routes.
- Roles assigned prospectively within painter. Confirmation: Monet 303, Sisley 107, Pissarro 142,
  Cézanne 106 (658 total). Historical exposure matching restricts 91 records to development;
  incomplete exposure identifiers remain an explicit limitation.
- The 31-coordinate feature implementation, paired-block energy estimator, and immutable-stage
  artifact code exist and have focused offline tests.
- SD-Turbo revision `b261bac6fd2cf515557d5d0707481eafa0485ec2` is downloaded under the ignored v2
  workspace. Its prospective configuration is 512×512, one step, 25 blocks × 16 prompts × five
  conditions (2,000 attempts), running locally with no paid API spending.
- The registered 2,000-request SD-Turbo run is in progress. Its frozen configuration and append-only
  generation ledger are unchanged. No active painter-feature result or finished paper exists.
- Original-image acquisition is terminal-aborted under its 64 MiB resource contract: 41 terminal
  dispositions, 33 acquired and eight failed. Retain every byte and the terminal receipt; never
  resume this run in place or splice its successes into the replacement.
- Acquisition amendment 1.1 registered replacement Commons renderings for the same complete frame.
  All 191 metadata requests succeeded and all 1,193 works have registered renderings. Replacement
  image acquisition and active feature extraction have not begun.
- The current Codex credentials work. The old port-10531 proxy predates its source update and
  returns an expired-token error. A separate current-source instance on port 10532 authenticated
  and completed the two-request access experiment without restarting the original server.
- Both GPT Image aliases returned valid PNG bytes, but **1254×1254 / reported quality low**, despite
  requesting 1024×1024 / medium. Neither response identifies a model snapshot. The sealed access
  receipt retains `invalid_output`; a separate offline diagnosis records two decodable images and
  zero contract-compliant images. This is access evidence, not an artistic-quality comparison.
- No manuscript is being prepared. A larger GPT Image comparison has not been launched; actual
  parameter control, route identity, and a bounded execution design need to be resolved first.

Canonical frame: `data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/`.
CLI: `uv run --locked --extra analysis --extra learned latent-art-bench paper-study --help`.
Access CLI: `latent-art-bench model-assessment --help`; v2 audit: `latent-art-bench paper-study audit`.

Latest validation: Ruff passed; 298 offline tests passed; v1 audit 2,902 checks and v2 audit
1,525 checks, both with zero unacknowledged failures. The v2 audit covers an ongoing generation
prefix, not a completed grid. The two historical v1 acknowledgements remain unchanged.

Large runtime bytes remain under `research_workspace/painter_feature_generation_v2/`. Preserve all
v1 evidence and its ignored raw responses. V2 outputs have disjoint paths; none repairs or replaces
a terminal v1 census. Reviews performed by the operator or an LLM are not institutionally
independent reviews.

## Historical v1 status (retained context; superseded as current operational guidance)

Operational date: 2026-09-04

This page is mutable operational state. Frozen historical protocols, ledgers, and receipts remain
authoritative for their own completed actions.

## Active research question

The active study is **Painter Feature Generation v1**:

> For one exact model and one pre-label outdoor-place prompt census, do painter-name outputs
> reproduce the distribution of color, spatial/orientation, and digital-texture features in
> authority-record-exactly-attributed, metadata-declared outdoor-place paintings by Monet, Sisley,
> Pissarro, and Cézanne?

The canonical plan is 2.1 as amended by 2.2 and
[2.3](../studies/painter_feature_generation_v1/PROTOCOL_2.3.md). **2.2 replaces the R0 collection
rules; 2.3 makes Wikidata the authority layer and renames the construct. Every other section of 2.1
stands.**

Protocol 2.3 records the maintainer's decision of 2026-09-04 to accept Wikidata's own statements as
authority. The collection-identity census that day found the 3,543 discovered items spread across
**449 institutions**, with the ten largest covering 28.7% of item-collection links and the fifty
largest 56.1%. Reaching institutional catalogue records at that spread would take roughly fifty
museum routes. The construct is therefore now **Wikidata-declared outdoor-place digital-surrogate
feature reproduction**, and no report may describe the corpus as authority-verified.

**The R1 determination was carried out on 2026-09-04** and is the study's first recorded corpus.
Applying 2.3 Sections 2 and 3 with 2.1 Sections 7.3 and 7.4 to the recorded census admitted
**1,193 physical works**: Monet 538, Sisley 196, Pissarro 259, Cézanne 200, against a floor of 179.
All four clear it. **Sisley clears by seventeen works**, which makes him the binding constraint on
every subsequent decision; no later rule may be adopted without checking his count first. The
determination downloaded nothing and assigned no role.

- receipt: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination_receipt.json`
- determination: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination.jsonl` (3,543 rows)
- Korean summary: [R1 판정](../reports/painter_feature_generation_v1/R1_DETERMINATION_KO.md)
- judge: `src/latent_art_bench/painter_feature_generation_v1/determine.py`

The counts in Protocol 2.3 Section 6 (Monet 521, Sisley 187, Pissarro 252, Cézanne 197) came from
an exploratory script written while drafting that version; an erratum in Section 6 records the
supersession. The determination receipt is the authority.

Protocol 2.0 (`PROTOCOL.md`) and 2.1 (`PROTOCOL_2.1.md`) stay at their paths as the
frozen authority for the censuses executed under them; neither is edited.

Protocol 2.2 was issued on 2026-09-04 after the Cleveland census showed the cost of judging at
collection time. It reduces R0 to four principles: write the request down first, keep everything,
do not judge at collection, and keep the source list closed. The freeze of every input file, the
neutral review, the authorization seal, the one-shot lock, the hash-chained ledger, and
termination of the whole census on any anomaly are no longer required at R0. They remain required
from R1 onward, and the hash-chained ledger is retained at G1 where dropping an unfavourable
attempt is a real temptation.

The claim is deliberately finite and technical: metadata-declared outdoor-place digital-surrogate
feature reproduction in the closed accessible frame. It is not painter classification, authorship,
content-free style, physical brushwork, artistic intention, or a probability-sampled oeuvre claim.

## Current stage

The study completed R0 metadata collection and the **R1 metadata determination**, and remains
**NO-GO for image acquisition** until the Protocol 2.2 Section 4 freeze and authorization seal are
issued. Zero images have been downloaded, zero roles assigned, zero generation attempts made, and
zero results produced.

The next authorized action is **role assignment under 2.1 Section 8.1**: apply
`SHA256("pfg-v1/2.1-role" ‖ physical_work_id)` to the 1,193 admitted works to split development,
qualification, and sealed confirmation, and pin the 122-work exposure denylist to development only.
That step needs no image either. Image acquisition follows, and the freeze and seal fall due before
its first byte.

Two facts from the determination bind later work:

- **geometry is the largest single loss (784 works).** Commons scan resolution, not authority or
  content, sets the corpus size. The 1,024 px floor is 2.1 Section 7.3 and is not to be lowered to
  buy works.
- **the admitted content mix differs sharply by painter.** 64% of Monet's admitted works are
  water-organized against 22% of Pissarro's. Section 13.4's specificity contrast must report this,
  because part of any cross-painter feature difference is subject matter rather than style.

**Protocol 2.1 was issued on 2026-09-04.** The decision it records: the study runs without
coders or an adjudicator. Every human coding step is removed and content eligibility is declared
by a frozen metadata lexicon (§7.4); scene-group stratification is gone and the real target is
uniform over works; all 16 prompt templates are always rendered; adherence is an automated
diagnostic; copy adjudication is a deterministic two-threshold rule; and one operator may hold the
custodian, method-analyst, and generation-operator roles sequentially under technical sealing with
an access ledger, a limitation every report must disclose. Section 0 of the protocol lists every
change.

The decision followed a non-binding pre-screen
([Korean summary](../reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md),
[evidence](../reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json)) that
applied the corpus arithmetic to the completed R0 manifests. Under Protocol 2.0 the four-way scene
cells needed 57 newly eligible works each and no scene cleared that floor for all four painters at
the metadata upper bound. Under Protocol 2.1 each painter needs 179 newly eligible works (100
confirmation at uniform weights, 10 development, 10 qualification, 12 auxiliary). The lexicon
upper bound of eligible items that carry a collection QID is Monet 529, Sisley 193, Pissarro 256,
and Cézanne 200, so all four clear the floor at the upper bound and Sisley is the binding risk:
authority verification, deduplication, complete-view checks, and private-collection exclusion can
only lower these counts, and NO-GO after R2 remains possible.

That pre-screen has since been superseded by the R1 determination above, and one of its claims did
not hold: it called its counts an upper bound, but the determination admitted 538 Monets against
the pre-screen's 529. The pre-screen read one row per item, so it missed works whose only
sufficiently large Commons file sat on a second row. A figure is an upper bound only for the exact
rule that produced it.

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

The complete, newly authorized R2 retry then repeated that follow-up under a new census ID:

- a metadata-only follow-up of 3,190 Wikidata items and 3,364 Commons filenames across 165 exact
  GET intents (80 Wikidata entity batches and 85 Commons file batches);
- a fail-closed collector with a corrected fallback-term parser and focused regression tests, which
  validates current P18 linkage, rights markers, reported geometry, exact member coverage,
  origin/redirect behaviour, retries, atomic receipts, and non-admission manifests;
- separate output paths and explicit hash-bound linkage to the terminal first census;
- maintainer-run LLM subagent review with no blocking finding (not institutional independence); and
- all 165 requests completed on first attempt, producing 331 hash-chained events, 165
  content-addressed raw responses (about 51 MiB locally), and a 3,367-row non-admission candidate
  manifest with its execution receipt.

The first prospective broad no-`P186` census (`pfg-v1-broad-wikidata-no-p186-20260902`) was
approved after maintainer-run LLM subagent review and executed on 2026-09-02. Monet completed with
1,317 discovery-only rows.
The next, Sisley, request returned provider HTTP 502 with `text/html`; the census therefore ended
terminally after five hash-chained events. Its one-shot lock and both raw responses are preserved,
and it emitted neither a candidate manifest nor an execution receipt. No R1 row is reusable.

The R2 census, reviewed by a maintainer-run LLM subagent, repeated the same four queries and parser, scope,
cutoff, and all-or-none terminal rule under a new census ID and disjoint paths. Its only operational
change was a five-second rather than two-second minimum request interval. The retry gate binds the
exact R1 config, freeze, review, authorization, terminal ledger/event, one-shot lock, both raw
responses, absent candidate/receipt, and exact allowed config delta. Neutral quality review found
and closed two execution-boundary file-binding defects before approval. R2 then completed all four
requests on first attempt and emitted 3,722 discovery-only item-image rows: 3,543 distinct Wikidata
item IDs and 3,718 distinct Commons filenames. No image was downloaded and no work was admitted.

The separately reviewed broad-media follow-up R1 then froze 182 exact metadata-only requests
covering all 3,543 item IDs and 3,718 filenames. Neutral review identified and closed deterministic
ordering, single-read CAS, terminalization, retry-ledger, cutoff/resume, path-confinement, and
atomic-publication defects before approval. Its first Wikidata response was HTTP 200 with
`Retry-After: 5`, but the body was a plural MediaWiki `errors` envelope containing `maxlag`, not a
parser-complete success. Because R1 did not recognize that error representation, it terminated
fail-closed after one request. Its three-event ledger and raw response remain frozen; no partial
manifest or receipt was issued or reused.

Broad-media R2 was then prospectively frozen under a new census ID and disjoint workspace. Its
only semantic change was strict recognition of a nonempty top-level plural `errors` array whose
entries carry one unambiguous nonblank error code; existing retry classifications and ceilings were
unchanged. The freeze bound 28 inputs, the complete R1 CAS/lock/event lineage, 182 deterministic
intents, and six absent pre-execution outputs. Maintainer-run LLM subagent review approved the exact
freeze with no blocker. R2 completed all 182 requests on their first R2 attempt: 89 Wikidata entity
batches and 93 Commons media batches, 365 hash-chained events, 182 content-addressed raw responses
(55,899,277 bytes locally), and a 3,722-row non-admission manifest. Of those rows, 2,029 pass the
federated metadata discovery gate, representing 1,967 distinct item IDs; none is yet an
authority-verified physical work, downloaded image, or active-study admission.

The first Art Institute of Chicago route census (`pfg-v1-aic-metadata-20260902`) received
maintainer-run LLM subagent review and was authorized and executed on 2026-09-02. Its first
request returned HTTP 200 with a
schema-valid body, but AIC returns `classification_id` as a nonblank string identifier such as
`TM-66` while the frozen parser required an integer. The census therefore terminated fail-closed
after one request with `terminal_delivery_or_schema_failure`. Its three-event hash-chained ledger,
one-shot lock, and single 129,424-byte raw response are preserved; it issued neither a candidate
manifest nor an execution receipt, and none of its rows was reused.

AIC R2 (`pfg-v1-aic-metadata-r2-20260902`) was then frozen under a new census ID with disjoint
manifest, publication, workspace, and CAS paths. Its only semantic change is that `classification_id`
is an optional nonblank string identifier; every source, query, transport, screening, retention, and
publication rule is unchanged. The freeze binds 25 inputs, six absent pre-execution outputs, and the
complete R1 config/freeze/review/authorization/intent/ledger/lock/CAS lineage together with the
exact allowed config delta. Maintainer-run LLM subagent review verified every frozen hash and
absence, reconstructed the four intents identically under five hash seeds, replayed the exact R1
terminal body — the R1 parser still fails with the recorded error while the R2 parser returns 46
rows — and passed a production-gate mock over the exact committed seal. It approved with no blocking
finding.

R2 then completed all four exact artist-ID requests on their first attempt on 2026-09-03: 9
hash-chained events, four content-addressed raw responses (308,569 bytes locally), and a 153-row
non-admission candidate manifest. No R1 response body was reused. Of those rows, 57 pass both the
AIC authority-record screen and the metadata/media screen, across 57 distinct accession numbers:
Monet 33 of 46 rows, Sisley 6 of 8, Pissarro 9 of 65, and Cézanne 9 of 34. The Pissarro and Cézanne
row counts are dominated by prints and works on paper, which the painting and oil-on-canvas screens
reject. No image endpoint was requested, no work was admitted, and the AIC rows are not yet
reconciled against the Wikidata/Commons census.

Still not completed:

- neutral review and freeze of the prompt library, content lexicon, and exposure denylist;
- an Europeana API key and a Paris Musées API token — both are absent from the repository and the
  environment, so those two routes will be recorded `not_executed_missing_authorized_credential`
  unless credentials are obtained before their freezes;
- the remaining terminal source routes named in Protocol 2.1 — Europeana, NGA, Cleveland, Yale,
  Getty, Minneapolis, Paris Musées, and POP/Joconde;
- authority, rights, physical-work, capture-family, and image-quality reconciliation;
- active image acquisition;
- the R2 metadata eligibility run, source crossing, and corpus closure;
- the frozen new-work role manifest and the 60-work capture panel;
- feature implementation/fixtures/qualification, margins, or simulation results;
- model/prompt/seed G0 freeze;
- generation; or
- confirmation and generated-versus-real results.

## R0 artifacts added 2026-09-04

| Artifact | Path | State |
|---|---|---|
| §11.1 prompt library | `data/manifests/painter_feature_generation_v1/prompt_library.json` | rendered from `PROTOCOL_2.1.md` by `latent-art-bench prompt-library`; 16 artist-free + 64 named strings; `strings_sha256` `c0d305dd…`; not yet neutrally reviewed or sealed |
| §7.4 content lexicon | `data/manifests/painter_feature_generation_v1/content_lexicon.json` | rendered by `latent-art-bench content-lexicon`; 5 override phrases, 106 exclusion tokens, 281 positive tokens; must be reviewed and frozen before R2 |
| §8 exposure denylist | `data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl` + `exposure_denylist_receipt.json` | rebuilt by `latent-art-bench exposure-denylist` from eight pinned git blobs; 122 pixel-exposed physical works are development-only (AIC 40, NGA 45, Met 27, CMA 10); 39 pilot-3 metadata-only selections carry no restriction; 5 works lack a resolved painter; not yet frozen for M0 |
| corpus-adequacy pre-screen | `reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json` + `SCENE_SUPPORT_PRESCREEN_KO.md` | non-binding lexicon proxy against the 2.1 floors, with the retired 2.0 scene-cell arithmetic kept for the record; regenerate with `latent-art-bench scene-prescreen` |
| commit-bound evidence audit | `latent-art-bench verify-evidence` | 9 freezes, 8 ledgers, 4 receipts verify; 2 acknowledged unrecoverable inputs |
| review fixes (PR #3) | `panel.py`, `artifact_cli.py`, and fixes across the new modules | the acknowledgement file now excuses only the exact bound hash it names; receipts cross-check their ledger and fall back to git history; the content lexicon folds typographic apostrophes; `--check` covers the denylist receipt; the pre-screen refuses to run without its inputs |
| shared census engine + Cleveland route | `census_engine.py`, `cleveland_metadata.py` | executed 2026-09-04 under Protocol 2.1; retained as evidence, superseded for new routes |
| Protocol 2.2 collector | `collect.py`, `latent-art-bench collect` | one module for every JSON route, 304 lines, no per-route parser, no collection-time verdict |
| Getty route contract | `configs/painter_feature_generation_v1/getty_collection.json` | written and offline-validated; not executed. The recorded exploratory query's object-type and material filters are deliberately removed |

The denylist already intersects the AIC R2 screened candidates: 17 of Monet's 33, all 6 of
Sisley's, 6 of Pissarro's 9, and 5 of Cézanne's 9 were pixel-exposed in the pilots and can only be
development works.

## Review provenance and staffing

Every neutral independent review under `data/manifests/painter_feature_generation_v1/*review*.json`
was produced by a large-language-model review subagent (recorded, for example, as
`Mencius (independent neutral quality review subagent)`) run by the single maintainer of this
repository. The reviews are procedurally separate from the freeze author and did find and close
real defects, but they are not institutionally independent, and every report must say so. Reviews
produced on the shared census engine must state `reviewer_kind` (`human` or `llm_subagent`).

Protocol 2.1 §8.2 has no coder or adjudicator role. The repository has one maintainer, who may
hold the acquisition-custodian, method-analyst, and generation-operator roles sequentially only
under technical sealing: confirmation-resolution bytes go into a sealed store whose manifest is
committed before M0, every read of a sealed path is ledgered, and any ledgered read before the C0
opening voids the affected confirmation claim. This cannot exclude covert access and is a stated
limitation of the study.

## Active counts

| Quantity | Count | Meaning |
|---|---:|---|
| exploratory Wikidata item candidates | 3,190 | material-constrained discovery identifiers, not verified works |
| distinct Commons filenames in that seed | 3,364 | file identifiers, not physical works |
| fixed-seed R1 completed requests | 4 / 165 | verified successes before the fifth request terminated R1 |
| fixed-seed R1 terminal requests | 1 | valid provider representation unsupported by the frozen parser |
| fixed-seed R2 completed requests | 165 / 165 | all first-attempt successes; no R1 success reused |
| fixed-seed R2 metadata-qualified rows | 2,029 / 3,367 | discovery gate only; not physical works |
| fixed-seed R2 distinct qualified item IDs | 1,967 | not identity-reconciled physical works |
| fixed-seed R2 distinct qualified filenames | 2,028 | files, not independent works or captures |
| broad no-P186 R1 successful requests | 1 / 4 | Monet response only; not reusable outside terminal R1 evidence |
| broad no-P186 R1 terminal requests | 1 | Sisley HTTP 502; whole R1 census incomplete |
| broad no-P186 R1 observed rows | 1,317 | discovery-only Monet rows inside an incomplete census; no manifest issued |
| broad no-P186 R2 requests | 4 / 4 | all first-attempt successes; R1 success was not reused |
| broad no-P186 R2 discovery rows | 3,722 | exact-creator painting+image rows; not physical works |
| broad no-P186 R2 distinct item IDs | 3,543 | current Wikidata identifiers before authority/identity reconciliation |
| broad no-P186 R2 distinct filenames | 3,718 | Commons filenames; not independent works or captures |
| broad-media R1 attempted requests | 1 / 182 | terminal plural `errors:[maxlag]` representation; no result publication |
| broad-media R2 completed requests | 182 / 182 | 89 entity + 93 media batches; all first-R2-attempt successes |
| broad-media R2 candidate rows | 3,722 | current entity/media metadata rows; not physical works |
| broad-media R2 metadata-qualified rows | 2,029 | discovery gate only; 1,967 distinct item IDs |
| broad-media R2 raw responses/events | 182 / 365 | content-addressed responses / hash-chained events |
| AIC R1 attempted requests | 1 / 4 | terminal string `classification_id`; no result publication |
| AIC R2 completed requests | 4 / 4 | one exact request per frozen AIC agent ID; all first-R2-attempt successes |
| AIC R2 candidate rows | 153 | returned holding records; not physical works |
| AIC R2 screened candidates | 57 | painting + oil/canvas + accession + public-domain flag + image ID + short side ≥ 1,024 |
| AIC R2 raw responses/events | 4 / 9 | content-addressed responses / hash-chained events |
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

Protocol 2.1 keeps the Protocol 2.0 candidate union unchanged:

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

0. Done 2026-09-04: Protocol 2.1 issued; the prompt library, content lexicon, and exposure
   denylist rendered. Their neutral review and freeze remain.
1. Preserve and report the completed fixed-seed, broad no-`P186`, broad-media, and AIC censuses
   without calling any of them a complete source frame or an acquired image corpus.
2. Freeze and execute the remaining named source routes to their terminal conditions, then
   reconcile the whole union to physical works.
3. Under a separate R1 authorization, verify authority/rights/capture identity and acquire lawful
   technically adequate image bytes.
4. Run the R2 metadata eligibility rule with the frozen lexicon, reserve the auxiliary panel, apply
   the denylist, assign roles by the hash rule, and close the unequal finite frame; generation
   remains NO-GO until every corpus adequacy gate passes.
5. Run M0a/M0b, auxiliary capture qualification, margins, copy calibration, and whole-decision
   simulation. All three families must pass.
6. Freeze one exact model, the 16 prompts, render settings, seeds, `R`, request order, the
   adherence classifier, and analysis at G0; then generate and seal G1 while confirmation features
   remain inaccessible.
7. Open the confirmation reference once at C0 and execute the frozen decision.

## Terminal evidence boundary

Three R1 censuses reached a terminal condition and stay terminal: the broad no-`P186` discovery
census on a provider HTTP 502, the broad-media follow-up on an unrecognized plural
`errors:[maxlag]` envelope, and the Art Institute route on a string `classification_id`. Each
retains its config, module, tests, ledger, and raw response, and each is bound both by the freeze
that authorized it and by the successor freeze that records its terminal evidence.

These outcomes are evidence. Do not repair them with new data, retry them in place, splice their
responses into a successor, or refresh their hashes.

## Explicitly closed actions

Under the historical v1 procedure, until the corresponding Protocol 2.1 freeze is reviewed
(past reviews were maintainer-run LLM subagents, not institutional independence), do not:

- retry, replace, or splice any terminal R1 census;
- treat metadata rows or files as an active painter distribution;
- download active-study images under the metadata-only census;
- read any sealed confirmation path before the C0 opening receipt;
- tune prompts, features, thresholds, margins, or source rules on generated/confirmation outcomes;
- send generation requests; or
- rewrite or move frozen evidence.

## Repository health boundary

The standard offline checks are:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

Evidence verification is commit-bound:

```bash
uv run --locked latent-art-bench verify-evidence
```

The audit resolves each freeze to the git commit that recorded it (a declared
`recorded_git_commit`, or the commit that introduced the freeze blob), verifies every bound input
against the bytes at that commit, verifies untracked research bytes in the working tree, and checks
every event ledger's hash chain and every execution receipt's ledger, manifest, and content-
addressed responses. Hashes are never refreshed. Later edits to `pyproject.toml`, `uv.lock`, or a
shared module therefore no longer invalidate earlier freezes; they are reported only as informational
working-tree drift.

Exactly two bound inputs can never re-verify. The fixed-seed R1 freeze bound the pre-repair
`federated_census.py` and its test module, and the R2 retry replaced those bytes before the first
commit that contains either freeze, so no commit holds them. They are recorded in
`data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json` with the cause and the
remaining evidence, and `tests/test_evidence.py` asserts that these are the only failures. Do not add
to that file to hide a new mismatch. New freezes must record `recorded_git_commit` and be prepared
from a tree whose bound inputs are clean against that commit.
