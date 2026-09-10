# Precollection scientific implementation review

Date: 2026-09-10. Study: `painter_clause_validation_v1`, prospective run
`pcvv1-20260910`. Reviewer: Reviewer 3, a maintainer-run LLM agent.

## Role, scope and disposition

I authored this study's protocol and 24 scene briefs, and previously advised on
the manuscript's literature, structure and moment-map/centering diagnostics.
I did not implement the collection or analysis code. This review therefore has
direct design involvement and is neither investigator-independent nor an
independent human or institutional assessment. I read the current protocol,
`common.py`, `analysis.py`, `__main__.py` and the scientific tests in full, plus
the relevant workflow, terminal-gate and inherited statistical implementations.
The separate transport reviewer covers the remaining transport implementation.
No new service calls, artwork acquisition or scientific image extraction occurred.

**Disposition: the scientific implementation defects identified below have been
fixed and their fixes checked. I identify no remaining scientific implementation
blocker in this bounded snapshot. This is not terminal permission to collect.**
The complete qualification, source commitment, bound review/input inventory,
committed freeze and required offline/evidence checks must still pass. This
review does not replace those gates or the separate transport review. Later
changes to the reviewed scientific behavior require corresponding rechecking.

No paper scores are assigned or changed. A desired score, favorable hypothetical
result, or extra experiment volume is not a scientific justification. The actual
question adds a previously absent no-palette named-versus-generic comparison and
prospective fixed-map predictions; that is the justification assessed here.

## Snapshot checked

Repository HEAD while checking was `6dd1e80b7d998f39809bfa354c8f52b7dd439595`.
Some prospective files remained uncommitted; HEAD alone does not identify this
reviewed implementation. The hashes below identify the final inspected bytes.

| File, relative to repository root | SHA256 |
| --- | --- |
| `src/latent_art_bench/painter_clause_validation_v1/common.py` | `9972fb640f8f36b88079a4368ec45c267bcdfac0245e51aa8303587a1d4a725a` |
| `src/latent_art_bench/painter_clause_validation_v1/analysis.py` | `c5a8049bddb586b861f62a207399a63dcd1838ac8135f9ea5349e84f5335b35c` |
| `src/latent_art_bench/painter_clause_validation_v1/__main__.py` | `b5b741cd54a693422d1129491ebbc9a9106888deae63c02aab8e61c6dd2f5e98` |
| `src/latent_art_bench/painter_clause_validation_v1/collection.py` | `fa40aa9b5bf58d76507be92379fc116bc02833a61e41c4c6474b30111cdfe823` |
| `src/latent_art_bench/painter_clause_validation_v1/workflow.py` | `f97ca52dd6acc64c883e05bb7486bf89d2a1ce874f7e7a36c2dbe9b451f30ad0` |
| `tests/painter_clause_validation_v1/test_analysis.py` | `4967b89b8cd02145683c4f8c3ab90de8b16061ce7a78eaa0af46896ebdc69c1d` |
| `tests/painter_clause_validation_v1/test_collection.py` | `84dfb680e015021aa53c93143bcdd1935f54f682507acbaf8eaa61fce73e8a43` |
| `studies/painter_clause_validation_v1/PROTOCOL.md` | `87d6dfae4746f7bc4028c4ea5e7dc5678ef7874cce065bac5b75623dfe68a91e` |
| `studies/painter_clause_validation_v1/scenes.json` | `4e24a570336f2b6cd28ad1f9312a944e545ae811c5db8f353b01d257d349951e` |
| `studies/painter_clause_validation_v1/study.json` | `7d683d4e869827fbfc4e73756ab940a946bdca69346647df8befb75c643c4e84` |
| `studies/painter_clause_validation_v1/inputs.json` | `4bd002c9319410946e7bedc5b6397e019cd2485e15f16b693259e3a7675e0280` |
| `studies/painter_clause_validation_v1/precision.json` | `c1da41e3ff1f7cc1e42c44a48d3189f07309cc5d467b99078492341416469785` |

## Findings that required correction before freeze

1. **Global service/identity failure initially did not withhold inference.**
   The first analysis checked duration and planned count only. An executable
   artificial complete-grid probe with a `proxy_identity_changed` receipt still
   returned available, rejecting primary endpoints. The same occurred for an
   authentication/contract failure reason. Pair completeness cannot replace the
   protocol's global service/identity gate. The final analysis now requires
   literal `identity_contract_met=true`; the collector rechecks source and proxy
   identity after all responses drain. The workflow derives the flag from bound
   terminal and operator evidence instead of trusting an editable receipt value.
   The protocol now explicitly specifies the conservative global failure
   categories. Final-source and final-proxy failures retain complete outputs but
   disqualify the run in passing tests; an attempted receipt-only restoration of
   identity is rejected. Analysis tests show false, absent, numeric and string
   substitutes all withhold both primary tests while retaining descriptive
   estimates. A fresh complete-72-pair probe with the false identity flag retained
   both estimates but returned no raw p-values, Holm values of one and no
   rejections. A later identity failure also remains recorded when an earlier
   storage halt already supplied the collection's primary stop reason.
   **Resolved in the checked snapshot.**

2. **Promised secondary summaries were only partly reported.**
   The first JSON retained observed total traces within its variance records but
   omitted explicit generic/free and named/generic trace ratios and T2-minus-T1
   differences for reference energy and corrected conditional residual Q.
   Recoverability by readers was insufficient for the prospective reporting
   contract. Those quantities now have explicit JSON fields and report columns.
   Zero trace denominators and incomplete arms have unavailable states, not
   invented ratios. Report text identifies the ratios as observed traces under
   reference-content weights. Arm-level delivery dimensions, formats, statuses
   and reported quality are now summarized once per output, rather than counted
   three times across pipelines. Tests and direct matrix calculations checked
   these additions. **Resolved in the checked snapshot.**

3. **Missing named observations unnecessarily suppressed an available map target.**
   The initial outer free-and-named condition removed map reference energies
   whenever a named arm was incomplete, although those energies require only
   the fixed historical map, new free outputs and references. It now retains
   both map reference energies and their difference when free is complete,
   while marking the named-dependent Q quantities unavailable. A targeted
   missing-Monet probe and regression test verify this separation.
   **Resolved in the checked snapshot.**

## Claim-to-implementation checks

| Prospective claim or requirement | Checked implementation and implication |
| --- | --- |
| Two actual-clause endpoints | Exactly Monet-minus-generic and Cezanne-minus-generic; no palette clauses, map-label tests or third primary comparison. |
| Fixed 288-output allocation | 24 distinct scenes, eight per class, three repetitions and four arms; 72 contiguous four-position blocks. Each block contains every arm once. |
| Same scene text across arms | Prompt construction changes only the exact clause; free/Monet/Cezanne variants were compared with the original detailed Study 1 renderer, including ASCII `Paul Cezanne`. |
| Weighted full-distribution statistic | Full V-energy retains reference/generated cross-distances and both within-cloud terms. Equal reference weights and generated weights `q_c/(8*3)` are used. This is not a mean-vector-distance surrogate. |
| 72 matched pairs | Scene/repetition IDs order the generic and named arrays identically; every pair contributes once. The same generic request memberships are used for both painters, with different fixed painter weights. |
| Conditional pair swaps | Conditioning on the other two arm positions leaves the named and generic labels equiprobable in the two remaining positions. Exhausting the 24 four-arm permutations gives 12 conditioning strata, each containing both pair signs once. Independent block assignments give the stated sign design under the sharp null and no interference. |
| Primary family and processing | Only `primary512` supplies the two primary p-values. Each uses 99,999 sign draws, conservative absolute ties and plus-one correction; Holm has exactly two entries, with unavailable entries set to one. `resolution256` and `jpeg90_512` remain descriptive and use all 31 features. |
| Allocated-pair completeness | Missing primary generic measurements withhold both endpoints; missing named measurements withhold that painter; missing free measurements do not by themselves remove an otherwise complete primary endpoint. No complete-case renormalization occurs. |
| Global duration/identity gate | Both tests require valid literal-boolean terminal duration and service/identity flags. Over-duration observations remain descriptive. A nonprimary-pipeline failure cannot rescue or invalidate an otherwise complete primary comparison. |
| Conditional variation | The inherited corrected-variance primitive returns observed total/between/within traces, B*, N*, correction and per-scene terms for both reference-content and equal-scene weights. Negative corrected estimates remain present. |
| Retrieval | Each held repeat is queried against centroids formed from the other two repeats. All 24 and same-class eight candidates are evaluated, with equal query weights and deterministic sorted-ID ties. There is no image-wise training/test leakage, binomial interval or independence claim for overlapping centroids. |
| Unchanged historical predictions | Full original OAuth fits are applied directly to new free vectors, separately by painter and pipeline. There is no new-cohort fit, evaluation centering, averaged-fold substitution, FLUX substitution or reference-energy optimization. |
| Q target | The residual is actual named minus fixed-map free for each scene/repetition. The cross-repeat correction uses distinct-repeat inner products, allows within-repeat named/free dependence, and retains negative estimates. Neither map target receives a randomization p-value. |
| Reporting and replay | JSON retains arm memberships, both weighting systems, pair contributions, retrieval predictions, map fits, target differences, availability and collection metadata. The artificial full workflow writes 864 measurement rows and exactly replays the numerical/report output. |

The class-weight totals were independently checked as Monet
`built=.10526315789473684`, `land=.34210526315789475`,
`water=.5526315789473685`; Cezanne `built=.34375`, `land=.5625`,
`water=.09375`. They sum to one per endpoint; shared controls do not imply
equal reference-content weighting across painters.

## Actual historical-input probe

I loaded the full prospective `inputs.json` and its stated predecessor
`data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json` without
opening any image bytes. The recorded predecessor SHA256 matches its file.
Targets match exactly. For every painter in all three pipelines, the complete
reference object, historical OAuth object (including image/scene/repetition
memberships) and scaler object match the predecessor exactly.

I recomputed all six maps from each full historical 24-by-3-by-31 free/named
array, with observation weights `q_c/24`. Every full map dictionary equals the
bound prospective dictionary exactly, not just within a tolerance.

| Pipeline | Monet fitted scale | Cezanne fitted scale |
| --- | ---: | ---: |
| `primary512` | 0.744167754888127 | 0.8070471043882522 |
| `resolution256` | 0.7967694718442373 | 0.7874891535000432 |
| `jpeg90_512` | 0.7502145505078479 | 0.8134148068096727 |

The historical free allocations are distinct repeated samples of the same
free prompts; they were not forcibly made identical. The new free and generic
arms are genuinely shared request memberships across the two painter views.
This distinction is preserved by the implementation.

## Executed verification

The first scientific suite had 20 passing tests. After the corrections, I ran:

```text
uv run --locked pytest -q tests/painter_clause_validation_v1/test_analysis.py -m 'not live'
28 passed in 1.82s

uv run --locked pytest -q tests/painter_distribution_study_v1/test_inference.py tests/painter_naming_geometry_v1/test_geometry.py tests/painter_naming_geometry_v1/test_variance.py -m 'not live'
68 passed in 1.16s

uv run --locked pytest -q tests/painter_clause_validation_v1/test_collection.py -k 'final_identity_failure or receipt_cannot_restore_identity or full_288_slot_artificial or measure_uses_each_retained_scaler or later_identity_failure or stopped_receipt_passed' -m 'not live'
7 passed, 59 deselected in 6.15s
```

These are 103 final targeted checks, not a claim to have rerun the entire
repository suite. The full artificial workflow uses a mock transport and a
synthetic measurement function; it verifies plumbing and real analysis, not
new image-service behavior or scientific validity of extracted features.

Additional read-only executable probes compared ten arbitrary 72-pair swaps
per endpoint with independently computed full V-energy. The maximum discrepancy
was `8.423817199343375e-15`. Direct weighted matrix totals for all 24 arm/view
summaries agreed within `7.105427357601002e-15`. Direct off-diagonal repeat
inner products for all 12 map Q estimates agreed within
`3.552713678800501e-15`; explicit ratios and Q differences also matched.
Missing generic measurements separately in either nonprimary pipeline preserved
both complete primary endpoints. Shared new free/generic request memberships
were equal across painter views in each pipeline.

## Scene and interpretation limits

As the unblinded scene author, I checked every new brief against all old 24
short/detailed Study 1 briefs and all six palette briefs. No exact repetition
or substantive restatement was identified. The closest thematic cases are
new ploughed furrows versus old fields, a channel between low islands versus
old coast views, and terrace stairs versus old village-slope paths. Their
principal objects and spatial arrangements differ. This is a manual author
judgment, not an independently adjudicated or artist-neutral scene benchmark.
Broader thematic overlap is expected within the three requested content classes.
No image inspection selected the briefs. New scenes are a fixed authored panel,
not a probability sample or verified per-painting content match.

I read the completed offline precision report. It transparently conditions on
noisy historical scene means and hypothetical generic noise/mean scenarios.
The selected 288 allocation preserves the 24-scene panel and avoids the extra
96 images of four repeats. Its reported SD comparisons do not establish power,
an equivalence threshold, new-scene variance or the eventual sign of N-G.
The artificial randomization qualification checks its stated numerical null
design, not the service's no-interference or availability assumptions.

The generic clause is an actual attainable prompt control, which addresses a
real gap in the earlier comparison with artist-free prompts and feature-space
maps. It is not matched to the names in semantic specificity or information.
Even a negative contrast with a Holm rejection would support a measured
clause-associated proximity gain within this fixed assignment/reference scope;
it would not identify an internal artist representation or prove perceived
stylistic fidelity. A positive result has the corresponding measured direction;
non-rejection is not equivalence or generic sufficiency. Fixed-map prediction
success or failure adds prospective evidence about those maps, not a new theorem
about marginal and conditional evaluation. None of these limitations is repaired
by adding more tests, views, rhetoric or review-score targets.

## Remaining precollection handoff requirements

Record this review in the qualification/freeze lineage, directly or through a
bound consolidated review containing its exact content hash. Complete the
separate implementation review and all remaining required offline checks; bind
the actual final source, protocol, inputs, precision record and full request
inventory. Commit source and qualification before preparing the create-once
freeze, and commit/verify the freeze before live collection. No result-dependent
scene, endpoint, pipeline, map or sample-size change is justified by this review.
