# Independent ICLR-style scientific review protocol

Frozen before the first scientific review of the ICML draft, 2026-09-18.

This is a local AI review simulation guided by ICLR's substantive review guidance,
not an official conference review or a prediction of acceptance. The formatting
target is the official ICML 2026 anonymous review template. ICML 2027 instructions
were not found; the 2026 style is a documented provisional format target, not a
claim that a September 2026 experiment was submitted to ICML 2026.

## Common review instructions

Read the complete frozen manuscript, main text and appendices. Judge scientific
soundness, contribution, clarity, reproducibility, relevant prior work and the
importance of the supported conclusions. Be rigorous, constructive and open to
empirical contributions; novelty need not be a new algorithm. Explicitly
separate an editing problem from a limitation that requires new evidence.

Do not use historical AI editorial scores, another reviewer's report, or the
user's desired threshold. Do not infer credit for work proposed but not done.
A narrow claim can be sound but not sufficiently significant. Conversely, do not
demand an experiment unrelated to the actual claim. Justify the recommendation
from the manuscript and inspected evidence.

Use this fixed six-level overall recommendation scale for the simulation:

- 0: strong reject
- 2: reject
- 4: marginally below acceptance
- 6: marginally above acceptance
- 8: accept, a good scientific paper
- 10: strong accept, should be highlighted

The scale is an explicitly fixed ICLR-style simulation rubric; it is not asserted
to be the unpublished ICLR 2027 form. Give soundness, presentation and
contribution subscores on 1 (poor) through 4 (excellent), and confidence 1–5.
The stopping statistic is the unweighted arithmetic mean of the three overall
recommendations, not a mean of presentation subscores. Preserve every completed
review, including low scores and superseded rounds. No reviewer may be replaced
because of their rating. A new round requires a substantive documented revision.

Each review must include: summary; strengths; weaknesses with locations;
questions; soundness, presentation and contribution subscores; ethics concerns
if evidenced; overall rating; confidence; concrete revision priorities; and the
SHA-256 of the inspected PDF. Each reviewer must write their own JSON and prose.

## Sources consulted

- https://iclr.cc/Conferences/2027/ReviewerGuidelines
- https://iclr.cc/Conferences/2026/ReviewerGuide
- https://icml.cc/Conferences/2026/AuthorInstructions
- https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip
