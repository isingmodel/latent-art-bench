# TMLR manuscript review record, second series

This is an internal review of the TMLR manuscript (`paper/tmlr/`) after its revision for the second
collection. The reviewers are language-model subagents working under a frozen [rubric](rubric.md).
That rubric keeps the criteria of the [first record](../tmlr_review_v1/README.md), which ended after
its six allowed rounds without a pass. These reviews are quality screens. They are not TMLR
decisions and do not predict acceptance. Every reviewer is a fresh subagent that reads one frozen
PDF, and no review is replaced or discarded. A round runs only when the owner asks for it.

| Round | Reviewed PDF | Methods | Empirical | Editor | Passes rubric |
| --- | --- | --- | --- | --- | --- |
| [01](round_01/) | `af4eea64…`, 38 pages | minor revision | minor revision | minor revision | no: criterion 1 *partially* for all three; 4 factual errors confirmed ([triage](round_01/triage.md)) |

Each round folder holds:

- the frozen input (`input/`): PDF, text extraction, source snapshot and `inputs.sha256`;
- the exact reviewer prompts (`prompts.json`);
- the reviews (`reviewer_*.md` and `.json`);
- the triage of the reviewers' claims, and any revision record written afterwards.

Reviewed PDFs are ignored by Git. Their hashes are recorded here and in the review files.
