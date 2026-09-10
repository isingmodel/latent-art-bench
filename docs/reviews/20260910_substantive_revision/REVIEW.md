# Substantive academic revision: review record

This cycle follows the requested [DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md) and the unchanged [three-aspect rubric](../20260909_academic_review/RUBRIC.md). The arithmetic mean weights all nine scores equally. The user target is strictly greater than 9; it has not been reached in either completed round. Scores are preserved as assigned, without target-driven revision or credit for unperformed work.

Every reviewer is an LLM subagent operated by the maintainer. These are not independent human/institutional peer reviews or publication decisions. After the fresh baseline, reviewers 1/2 contributed statistical implementation and packaging, while reviewer 3 supplied literature and structural advice. Later experiment design and implementation involvement is disclosed in the separate precollection reviews.

| Round | Reviewer | Rigor | Contribution | Clarity/reproducibility | Reviewer mean |
|---|---|---:|---:|---:|---:|
| 1 | 1 | 8.1 | 7.7 | 8.8 | 8.2000 |
| 1 | 2 | 8.2 | 7.8 | 9.0 | 8.3333 |
| 1 | 3 | 8.4 | 7.4 | 8.7 | 8.1667 |
| 2 | 1 | 8.7 | 8.4 | 8.8 | 8.6333 |
| 2 | 2 | 8.8 | 8.6 | 9.0 | 8.8000 |
| 2 | 3 | 8.8 | 8.3 | 8.8 | 8.6333 |

Round 1 mean: **8.2333333333**. Round 2 mean: **8.6888888889**.

The baseline snapshot is in BASELINE.json and the complete reports are REVIEWER_1_ROUND1.md through REVIEWER_3_ROUND2.md. Round 2 reviewed TeX SHA256 `8973d78ceb7d4f81a05010e118454eabc210ecdaa4885ad85eec1e3e41cff0e5` and PDF `ca291f0e0b04ebfa740240d697be89bbe78cfdaecae5b47b61f06acb636d3b9b` (36 pages, nine figures). Each reviewer read the full manuscript/appendices, inspected all pages and figures, checked primary literature and recorded claim/evidence judgments.

## Substantive changes between rounds

The separately frozen geometry analysis evaluates generated-only translation and translation/scaling on whole held-out scenes, applies original maps unchanged to later FLUX outputs, and estimates repeat-corrected scene geometry and conditional-mean mismatch. Its centering successor separates a scalar change at a common evaluation mean from displacement due to the old fitting center. Both run the full specified grid, with no new images or feature extraction.

The main finding is disagreement between explicit prediction targets: adding the scalar improves corrected prediction of named scene means in all six primary cells while worsening reference energy in five. On the later FLUX cohort, translation scores better than actual naming in both primary views, but this is not representation-invariant. At a shared mean, scalar contraction worsens energy in all 60 original and 18 later cell means. These are empirical diagnostic findings, not a new general theorem or internal mechanism.

## Corrections after round 2

The manuscript restores Study 2’s actual geometry/quality delivery counts, qualifies summary claims as fold averages, explains the cross-distance/within-distance terms behind the centered-scale penalty, identifies both new namespaces/run IDs/replay commands, and removes avoidable float barriers. Closest literature now includes Su et al.’s fixed-content artist substitutions and held-out-prompt benchmark, alongside the previously added conditional evaluation work. No result or score was overwritten.

The corrected 34-page paper and both complete numerical analyses were published as the [additive geometry release](https://github.com/isingmodel/latent-art-bench/releases/tag/ppgv1-20260910), source `5485e36`. Both new analyses replay exactly from fresh local and anonymous-download environments, with 95 scientific tests passing; the prior 1,394-test full suite and 2,902-check historical audit also passed. See [release verification](../../../reports/paper_geometry_reproducibility_v1/ppgv1-20260910/REPORT.md). Earlier public archives remain unchanged. This corrected snapshot has not been assigned new full-paper scores.

## Next discriminating experiment

Reviewer consultation identified an actual generic-clause control on newly specified scenes as a useful missing intervention. Merely adding more retained-data grids would not resolve new-scene selection or reference validity. A separate 288-output OAuth experiment is under qualification, comparing free/generic/Monet/Cezanne clauses on 24 new fixed scenes with 3 repeats and two primary named-minus-generic energy tests. It uses no paid calls or human ratings. Its old-map/conditional summaries are secondary; it does not substitute OAuth for a claimed FLUX replication or establish scene-population generalization.

No outcome or score improvement is assumed. The original metric/capture limitations, single generic wording and established conceptual antecedents remain material. A new paper review requires the completed result, manuscript and verified access, with its own snapshot and honest unchanged rubric.
