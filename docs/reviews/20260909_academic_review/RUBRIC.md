# Academic review rubric — 9 September 2026

This review adapts the user-specified [DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md).
The skill was retrieved on 9 September 2026; its SHA-256 was
`a0285baaeacc916bf45751c06db37745b195ddd4ec30e271ec1472f6cd48e8aa`.
The user requests three aspects scored from 1 to 10, replacing the skill's six
1-to-5 subratings. Its requirements for complete reading, claim/evidence mapping,
literature context, specific strengths/weaknesses and actionable recommendations
are retained.

## Fixed criteria

Each reviewer independently scores all three aspects, using increments of 0.1
if useful. Criteria and weights remain unchanged across rounds.

1. **Scientific rigor:** validity of the design, statistical reasoning,
   measurements, comparisons and claim/evidence correspondence. Evaluate the
   finite-panel computational question actually studied, including the practical
   impact of acknowledged limitations. Candor does not eliminate a design weakness.
2. **Contribution and significance:** originality, substantive insight, utility
   and relation to the nearest literature. Distinguish a useful empirical
   application from a new general principle or validated explanation.
3. **Clarity and reproducibility:** coherent scientific narrative, precise
   definitions and reporting, readable figures, sufficient analysis detail,
   traceable evidence and realistic code/data access. Documentation of an access
   limitation is not equivalent to public reproducibility.

Anchors: 1–2 = fundamental deficiencies; 3–4 = major weaknesses; 5–6 = mixed or
limited; 7 = solid but materially limited; 8 = strong with remaining substantive
limitations; 9 = exceptional with only minor weaknesses for the stated empirical
contribution; 10 = outstanding and unusually complete. Use the full scale honestly.
A paper need not solve another research problem to score well, but precise
wording alone cannot create novelty, validation or new evidence.

The reported aggregate is the arithmetic mean of all nine aspect scores
(three reviewers × three aspects). Per-reviewer means are also reported.
No individual score or assessment may be overwritten by the coordinating agent.

## Review procedure

- Read the entire current manuscript, including appendices, and inspect the
  relevant evidence and figures. Record the manuscript hash reviewed.
- Use targeted primary-source literature search. Cite the sources actually read;
  state any retrieval limits. Avoid claims based on search snippets alone.
- Record metadata and an executive assessment; extract the principal claims
  with evidence locations and strength of support.
- Give at least three specific strengths and three genuine weaknesses or
  residual limitations, distinguishing major concerns from minor issues.
- Explain each score, state review confidence, and identify actionable changes.
  Separate changes possible using retained evidence from those requiring a new
  scientific study or public release.
- On subsequent rounds, reconsider the revised manuscript under this identical
  rubric. Explain every score change. Do not raise scores for compliance alone,
  repeat reviews without substantive changes, or award points to meet a target.

These are maintainer-run LLM subagent reviews, not independent human peer review,
editorial acceptance, or a prediction of publication outcome. No venue has been
selected. Reviewers assess an empirical computational paper, not a top-conference
submission assumed without evidence.
