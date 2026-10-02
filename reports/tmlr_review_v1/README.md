# TMLR manuscript review record

Internal review of the TMLR manuscript (`paper/tmlr/`) by language-model subagents under a
frozen [rubric](rubric.md). These are quality screens, not TMLR decisions, and do not
predict acceptance. Every reviewer is a fresh subagent that reads one frozen PDF; no review
is replaced or discarded. Any change to the reviewer prompts between rounds is disclosed in
the next revision record (round 3 added a calibration clause on answering the criteria).

| Round | Reviewed PDF | Methods | Empirical | Editor | Passes rubric |
| --- | --- | --- | --- | --- | --- |
| [01](round_01/) | `33c87a6f…`, 20 pages | major revision | major revision | major revision | no — [revision](round_01/revision.md) |
| [02](round_02/) | `2837299e…`, 23 pages | minor revision | minor revision | minor revision | no — [revision](round_02/revision.md) |
| [03](round_03/) | `7da8263c…`, 25 pages | minor revision | minor revision | minor revision | no — [revision](round_03/revision.md) |
| [04](round_04/) | `caa3b429…`, 29 pages | minor revision | minor revision | minor revision | no — [revision](round_04/revision.md) |
| [05](round_05/) | `764356d8…`, 30 pages | minor revision | minor revision | minor revision | no — [revision](round_05/revision.md) |
| [06](round_06/) | `4ae5600e…`, 32 pages | minor revision | minor revision | minor revision | no; review limit reached — [final revision, not reviewed](round_06/revision.md) |

The rubric allows at most six rounds. Criterion answers in round 6: methods yes/yes, empirical
partially/yes, editor yes/partially; each reported at least one factual error. The manuscript in
`paper/tmlr/` includes the unreviewed final revision described in the round-6 record.

Each round folder holds the frozen input (`input/`: PDF, text extraction, source snapshot and
`inputs.sha256`), the reviews (`reviewer_*.md` and `.json`) and the revision record written
afterwards. Reviewed PDFs are ignored by Git; their hashes are recorded here and in the
review files.
