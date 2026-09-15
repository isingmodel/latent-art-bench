# Fixed editorial rubric: expression, structure and reader experience

Version 1, established 2026-09-15 before scoring. This assesses the English
manuscript's communication, not its publication acceptance probability or
independent scientific validity. The intended reader has general graduate-level
scientific literacy, but no prior knowledge of this project, its feature
representation or its statistical notation. Treat technical appendices as
optional depth; the main text must convey the study and findings on its own.

## Four equally weighted dimensions

| Dimension | What to assess |
| --- | --- |
| Expression | Clear, precise and fluent English; manageable sentences; consistent terminology; useful transitions; economical qualifications and minimal repetition. |
| Structure | A coherent progression from question to design, measurement, results and interpretation; visible hierarchy of primary findings and diagnostics; effective section order and main-text/appendix division. |
| New-reader understanding | Standalone abstract; concrete motivation; understandable experimental arms and reference target; intuition before or alongside notation; interpretable metrics, figures and numerical results; clear limits and distinctions without having to consult the repository. |
| Engagement | A consequential question, concrete examples and a discernible narrative; figures that reward inspection; findings explained through what they reveal; sufficient pace and emphasis to sustain attention without hype or exaggerated conclusions. |

Each dimension is scored from 1 to 10 in 0.25-point increments. Apply the same
anchors to every dimension and explain scores with manuscript evidence.
The overall score is the arithmetic mean of the four dimension scores. Do not
round the overall score before aggregation across reviewers.

## Score anchors

| Score | Editorial standard |
| ---: | --- |
| 1 | The intended reader cannot recover the central meaning; the dimension is substantially absent or broken. |
| 2 | Only fragments are understandable; severe obstacles dominate. |
| 3 | The central subject is recognizable, but major reconstruction is required. |
| 4 | A determined reader can reconstruct the argument, with frequent serious obstacles. |
| 5 | Basic communication works, but substantial editing is needed across much of the manuscript. |
| 6 | Mostly understandable; several substantial weaknesses interrupt comprehension or momentum. |
| 7 | Competent and coherent, with recurrent friction or one important communication gap. |
| 8 | Strong overall; a few concrete, material editorial weaknesses remain. |
| 9 | Excellent; the main narrative and findings are readily understood, with only localized refinements needed. |
| 10 | Exemplary for the intended audience; no consequential editorial improvement is apparent within the paper's legitimate scope and length. |

Intermediate values represent positions between adjacent anchors. High scores
are permitted when supported; do not manufacture defects to appear skeptical.
Equally, do not inflate scores for effort, number of analyses, an inferred desired
outcome or agreement with the authors. Score what the supplied manuscript does.

## Evaluation boundaries

- Read the entire supplied manuscript. Inspect the PDF's main figures and tables;
  use source files to resolve notation or cross-references. Record what was read.
- Assess the scientific story as a bounded comparison of measured digital
  reference contrasts. Do not require human evaluation, new experiments, a new
  feature representation or a larger model panel as editorial improvements.
- Do flag wording that overstates the results, obscures uncertainty, confuses
  primary and retrospective findings, or implies unperformed perceptual validation.
  Explain its actual reader-facing consequence.
- Distinguish a technical appendix from unnecessary technical burden in the main
  narrative. Reader accessibility does not require deleting necessary methods.
- Recommend concrete replacements, moves or cuts that preserve evidence. The
  paper must not grow beyond 22 pages; its abstract must not exceed 155 words.
- Review independently. Do not inspect other reviewers' files, earlier scores,
  earlier draft assessments, editorial progress reports or evaluation goals.
  Do not contact other reviewers or spawn additional agents.

## Required review record

Write only the assigned JSON file, using these fields:

```json
{
  "reviewer_id": "assigned identifier",
  "rubric_version": 1,
  "manuscript_pdf_sha256": "sha256 of the supplied PDF",
  "read_scope": {"full_manuscript": true, "pdf_pages_inspected": [], "notes": ""},
  "scores": {"expression": 0, "structure": 0, "new_reader_understanding": 0, "engagement": 0},
  "overall": 0,
  "score_reasons": {"expression": "", "structure": "", "new_reader_understanding": "", "engagement": ""},
  "strengths": ["specific strength"],
  "findings": [{"priority": "high|medium|low", "location": "section/page/source line", "issue": "", "reader_effect": "", "suggested_change": ""}],
  "claim_fidelity_issues": ["specific misleading or unsupported wording, if any"],
  "summary": "brief independent editorial verdict"
}
```

Scores and review records are internal editorial judgments by language-model
agents, not human-reader evidence or scientific acceptance ratings.
