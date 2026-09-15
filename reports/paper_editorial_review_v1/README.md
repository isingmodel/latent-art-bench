# Editorial revision record

The user requested a fixed 1–10 editorial rubric, three independent fresh
reviewers per round, and revision until their mean overall score is strictly
above 9.25. The [rubric](RUBRIC.md) was fixed before the first review. Expression,
structure, new-reader understanding and engagement receive equal weight.

Each round evaluates one PDF snapshot. Reviewers receive the rubric and that
snapshot only, without the stopping threshold or earlier scores. All three
reviews count; none is discarded or replaced because of its score. A new set
of agents reviews each revised manuscript. Snapshot and review hashes bind the
records to the evaluated files. Original scientific evidence remains untouched.

These are internal language-model editorial assessments. They do not measure
human enjoyment, establish scientific validity, or predict journal acceptance.
Because reviewers change between rounds, score changes reflect both manuscript
revision and evaluator variation; they are not a controlled estimate of improvement.
No human evaluation was added. The original editing loop kept the paper within
22 pages and its abstract within 155 words. The user lifted the manuscript length
limit for the final update after `_04`; the fixed rubric and historical records
remain unchanged.

Subsequent user-requested independent assessments are recorded separately in
[Independent follow-up reviews](INDEPENDENT_REVIEWS.md): Claude Code / Opus 5
scored **8.3125**, and GPT-6 Astra / xhigh scored **8.9375**, on the preserved round-33
manuscript. Their raw opinions and host-verified factual corrections are retained;
these assessments do not replace any original round. Later user-requested
revisions are recorded separately in [paired review 03](paired_review_03/FIRST_REVISION.md).

The stopping criterion was met in **round 33** on 2026-09-15: scores **9.375,
9.0625 and 9.4375**, mean **9.2916666667**, strictly above 9.25. Across all
rounds, 99 distinct reviewing agents produced 99 retained reviews. The round-33
assessed PDF is 22 pages with a 151-word abstract and remains preserved unchanged.
Subsequent edits affect the canonical paper, not that graded snapshot.
The [final decision](round_33/DECISION.md)
records the remaining optional refinements and the exact PDF hash. The
[final audit](FINAL_AUDIT.json) verifies all 33 rounds, 99 unique reviewers,
the unchanged rubric, manuscript snapshot identity and scientific-file preservation.
That audit receipt records the state when the original goal was completed.

A later user-requested **revise → evaluate → revise again** sequence is recorded
in [paired review 03](paired_review_03/README.md). After the first revision,
fresh Claude and Astra assessments scored it **8.0625** and **8.8125**. Their
feedback then informed a second revision (22 pages, 151-word abstract,
9,593 extracted PDF words). Those scores do not apply to the final second
revision. Cancelled `_02` requests provide no accepted scores; the original
99 reviews and all graded snapshots remain intact.

The subsequent [final evaluation-only round `_04`](paired_review_04/README.md)
assessed that unchanged second revision: Claude Opus 5 **8.0625**, Astra xhigh
**8.8125**, mean **8.4375**. These are independent assessments of that frozen
PDF, not reused `_03` scores.

The subsequent [final update](final_update/README.md) incorporates selected `_04`
feedback and the repository cleanup. The canonical paper differs from the assessed
PDF; no earlier score is reassigned to it and no new review was requested.
Use `make editorial-check` to verify the portable historical record. The
[archive guide](ARCHIVE.md) documents retained assessments, narrowly ignored
execution traces and optional verification of local snapshots.

| Round-33 dimension | Equal weight | Mean score |
| --- | ---: | ---: |
| Expression | 25% | 9.4166666667 |
| Structure | 25% | 9.3333333333 |
| New-reader understanding | 25% | 9.1666666667 |
| Engagement | 25% | 9.2500000000 |

| Round | Reviewer A | Reviewer B | Reviewer C | Mean | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 7.6875 | 7.7500 | 7.5000 | 7.6458333333 | Revise |
| 2 | 8.7500 | 8.6250 | 8.7500 | 8.7083333333 | Revise |
| 3 | 8.7500 | 8.7500 | 8.6250 | 8.7083333333 | Revise |
| 4 | 8.8750 | 8.8750 | 8.8750 | 8.8750000000 | Revise |
| 5 | 8.8750 | 9.0000 | 8.9375 | 8.9375000000 | Revise |
| 6 | 9.0625 | 9.0625 | 9.1250 | 9.0833333333 | Revise |
| 7 | 8.9375 | 9.0000 | 8.9375 | 8.9583333333 | Revise |
| 8 | 9.1250 | 8.8750 | 9.0625 | 9.0208333333 | Revise |
| 9 | 9.3125 | 9.0000 | 9.0000 | 9.1041666667 | Revise |
| 10 | 8.9375 | 9.0000 | 9.1250 | 9.0208333333 | Revise |
| 11 | 9.1250 | 9.0625 | 9.0000 | 9.0625000000 | Revise |
| 12 | 9.1250 | 9.2500 | 9.2500 | 9.2083333333 | Revise |
| 13 | 9.1875 | 9.1250 | 9.1250 | 9.1458333333 | Revise |
| 14 | 9.1250 | 9.1250 | 9.1250 | 9.1250000000 | Revise |
| 15 | 9.1250 | 9.3125 | 9.0625 | 9.1666666667 | Revise |
| 16 | 8.9375 | 8.9375 | 9.0000 | 8.9583333333 | Revise |
| 17 | 9.3750 | 9.2500 | 9.0625 | 9.2291666667 | Revise |
| 18 | 9.0625 | 9.1250 | 9.1250 | 9.1041666667 | Revise |
| 19 | 9.1875 | 9.2500 | 9.1875 | 9.2083333333 | Revise |
| 20 | 9.2500 | 9.1250 | 9.1875 | 9.1875000000 | Revise |
| 21 | 9.1250 | 9.1250 | 9.2500 | 9.1666666667 | Revise |
| 22 | 9.1250 | 9.2500 | 9.1250 | 9.1666666667 | Revise |
| 23 | 9.1875 | 9.0625 | 9.3125 | 9.1875000000 | Revise |
| 24 | 9.3125 | 9.1250 | 9.1250 | 9.1875000000 | Revise |
| 25 | 9.1250 | 9.2500 | 9.0625 | 9.1458333333 | Revise |
| 26 | 9.1875 | 9.1250 | 9.3125 | 9.2083333333 | Revise |
| 27 | 9.0000 | 9.1250 | 9.3125 | 9.1458333333 | Revise |
| 28 | 9.0000 | 9.3125 | 8.8750 | 9.0625000000 | Revise |
| 29 | 9.0000 | 9.1250 | 9.0625 | 9.0625000000 | Revise |
| 30 | 9.1250 | 9.2500 | 9.0000 | 9.1250000000 | Revise |
| 31 | 9.1250 | 9.2500 | 9.1875 | 9.1875000000 | Revise |
| 32 | 9.1250 | 9.1250 | 9.1875 | 9.1458333333 | Revise |
| 33 | 9.3750 | 9.0625 | 9.4375 | 9.2916666667 | Pass |

[Round 1 revision decisions](round_01/REVISION.md) explain the changes made in
response to the first three reviews; [round 2 decisions](round_02/REVISION.md)
record the subsequent terminology, visual and scope refinements.
[Round 3 decisions](round_03/REVISION.md) cover the measured-coordinate example,
combined gallery, aggregation/provenance clarification and shorter discussion.
[Round 4 decisions](round_04/REVISION.md) record the abstract rewrite, enlarged
geometry panels and terminology/order corrections.
[Round 5 decisions](round_05/REVISION.md) document the centroid details,
source-comparison table and narrower summary wording.
[Round 6 decisions](round_06/REVISION.md) cover the common-share definition,
figure takeaways, larger annotations and explicit error/interval benchmarks.
[Round 7 decisions](round_07/REVISION.md) record the conclusion emphasis,
notation key, consistent response terminology and visual benchmark guidance.
[Round 8 decisions](round_08/REVISION.md) document the explicit calibration
objective and interpretation, reference labels and appendix terminology.
[Round 9 decisions](round_09/REVISION.md) cover generated-contrast calibration,
noise-correction wording, source-sensitivity focus and explanation-before-table order.
[Round 10 decisions](round_10/REVISION.md) record the exact robustness-score scope,
shorter abstract sentences and removal of an unnecessary historical aside.
[Round 11 decisions](round_11/REVISION.md) record the plain-language calibration
objective, restored shared-response conclusion, source-label clarification and
verified timing of the primary inferential specification.
[Round 12 decisions](round_12/REVISION.md) document distinct calibration/reference
labels, pair and content-target definitions, selective table emphasis and repaired
paragraph flow.
[Round 13 decisions](round_13/REVISION.md) cover explicit contrast error and
retrospective linkage in the abstract, direct model-comparison wording, centered
figure labels and a concrete discussion synthesis.
[Round 14 decisions](round_14/REVISION.md) record plain introductory language,
calibration rationale in the abstract, a declarative discussion, clear historical
palette labels, precise appendix pointers and unambiguous two-value cells.
[Round 15 decisions](round_15/REVISION.md) separate retrospective calibration from
pair diagnostics in the abstract, remove introductory repetition and state the
source-corrected Sunburst comparison directly.
[Round 16 decisions](round_16/REVISION.md) shorten the abstract's calibration
passage, enlarge Figure 2's detail labels, explain the observed shrinkage
tradeoff and replace the Discussion's model recap with evaluation implications.
[Round 17 decisions](round_17/REVISION.md) split the abstract's calibration
sentence, move the exact stability range to its technical appendix, distinguish
linear from squared scaling, repair figure tick spacing and refine the conclusion.
[Round 18 decisions](round_18/REVISION.md) rewrite the abstract in plainer terms,
separate uncertainty construction from interpretation, relocate collection-level
results, tabulate genuine-painting control ranges and unify variance terminology.
[Round 19 decisions](round_19/REVISION.md) make the abstract's two rankings
explicit, label reference works by title, clarify display/scoring regions and
scene-averaged geometry, relocate the energy definition and simplify reporting advice.
[Round 20 decisions](round_20/REVISION.md) order the abstract's findings, give
the pair colors explicit benchmarks, label paired table metrics, clarify crop
and historical-map wording, and reconnect the lightness example to pair results.
[Round 21 decisions](round_21/REVISION.md) add the six-model shared-change
comparison, distinguish positive and negative pair alignment, shorten calibration
and repeated qualifications, and clarify the Discussion's reporting implications.
[Round 22 decisions](round_22/REVISION.md) aggregate three fresh abstract
drafts, explain the normalization scale, label calibrated scene error, remove
Discussion repetition and signpost the supplemental figures.
[Round 23 decisions](round_23/REVISION.md) connect pair alignment to pair error,
match the calibration discussion to table order, separate the supplementary
metrics into labeled rows, clarify the geometry axis and reduce repeated intervals.
[Round 24 decisions](round_24/REVISION.md) clarify the abstract's error criterion,
noise correction and signed alignment; repair the complete-comparison reference;
and explain why shared-change percentages and aligned response are compatible.
[Round 25 decisions](round_25/REVISION.md) clarify abstract centering and
uncertainty, make table/figure captions independently interpretable, shorten
the feature introduction and tie the Discussion to three evaluation choices.
[Round 26 decisions](round_26/REVISION.md) make benchmark uncertainty visible in
the primary table, explain the shared-change calculation, distinguish contrast
magnitude from aligned strength and simplify the abstract and Discussion.
[Round 27 decisions](round_27/REVISION.md) trim the closing recap, distinguish
between-name change from reference agreement, clarify abstract centering and
scene error, explain additive components and identify the historical generator.
[Round 28 decisions](round_28/REVISION.md) explain calibration before its abstract
ranking, distinguish common named change from the generic shift, sharpen the
Discussion synthesis and refine Figure 2 within its existing area.
[Round 29 decisions](round_29/REVISION.md) replace the Discussion recap with
practical reporting requirements and connect the abstract ranking change to
verified shrinkage across all 84 fitted calibration factors.
[Round 30 decisions](round_30/REVISION.md) ground reporting advice in the model
findings, simplify the abstract, label the two evaluation operations and quantify
the common/generic squared-magnitude ratio from retained control components.
[Round 31 decisions](round_31/REVISION.md) give the common/generic comparison
a plain-language interpretation, reduce the closing recap and explain the
residual component in the supplemental figure caption.
[Round 32 decisions](round_32/REVISION.md) identify the corrected cosine and
magnitude denominator, name the evaluation choices, shorten the conclusion and
repair the declared-sensitivity evidence pointer.
Each round directory retains the original
review JSON, snapshot manifest, arithmetic aggregation and validation record
where applicable. Working PDF/source snapshots and rendered previews are under
`tmp/paper/editorial-review-v1/`; their hashes are recorded here.
