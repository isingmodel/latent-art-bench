# Revised English paper: painter naming, proximity and variation

This is the current 23-page computational manuscript prototype. It incorporates the
[methodology review](../../docs/reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md)
through a separately frozen, explicitly post-result analysis of retained data.
The earlier [controlled-study paper](../painter_distribution_study_v1/paper.pdf)
remains a historical version.

## Scope and interpretation

The controlled dataset remains 1,006 generated images, 70 reference works and
221 development works. The original eight conditional randomization tests are
unchanged. The revision adds four feature views, within/between-brief variation,
reference and scaler influence, painter interactions and identical-payload
controls, coverage controls, metadata and cross-route detection, and timing
sensitivities. All new diagnostics are descriptive.

The paper supports finite-feature prompt effects, with explicit counterexamples
to universal contraction and route-invariant detection. It does not validate
perceptual style collapse. The [validation plan](../../studies/painter_distribution_revision_v1/VALIDATION_PLAN.md)
specifies future reference and human work; no participants, learned encoders or
new capture study were executed. Reviews are maintainer-run LLM reviews.

Additional generation was unnecessary for this diagnostic scope: **0 new images,
$0 new spending**, with conservative study accounting still **$45.6819185 of $75**.
The remaining accounting allowance is not a fresh provider balance query.

## Revision-plan disposition

| Review step | Disposition in this paper |
|---|---|
| 1. Claim and contribution | Finite prompt/feature-distribution claim, explicit original versus post-result evidence, and checked adjacent-work comparison. |
| 2. Retained-data diagnostics | Implemented and calculated in the new namespace, with full memberships, contradictions and unchanged primary-result checks. |
| 3. Reference/nuisance feasibility | Metadata support and annotation/acquisition design completed. The paper retains the finite-file target; no new-reference replication is claimed. |
| 4. Human constructs | Concrete study design prepared. Stimulus execution, recruitment, institutional determination and judgments are unperformed; perceptual claims are withheld. |
| 5. Learned representation | Optional branch deferred; no new encoder measurements or training. |
| 6. Final contribution and artifacts | Revised computational prototype and numeric replay package. Journal choice, external human review and public raw-image release remain future decisions. |

This is completion of the computational revision, not completion of the plan's
conditional human or new-reference validation branches.

## Reproduce

From the repository root, install the locked analysis/dev environment if needed:

```bash
uv sync --locked --extra analysis --extra dev --inexact
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.analysis check
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.report_publication check
uv run --locked ruff check .
uv run --locked pytest -q -m 'not live'
uv run --locked latent-art-bench verify-evidence
```

These numeric/report checks use committed vectors and metadata without image
access or provider calls. The evidence audit is the historical protocol audit;
the two revision commands verify this namespace separately. Retained image bytes
would be required for feature re-extraction, and mutable services cannot promise
bitwise regeneration. No completed collection or publication command should be
restarted to reproduce the paper.

Scientific source and 103 inputs were committed at `f7666ae`; the numeric freeze
was committed at `c505512` before calculation. The numeric receipt records the
full commit and hashes. Report provenance separately binds its renderer and
output files. The original analysis and paper are preserved.

Build with Tectonic from this directory, after the report figures exist:

```bash
mkdir -p ../../tmp/paper-build-revision
tectonic --outdir ../../tmp/paper-build-revision paper.tex
cp ../../tmp/paper-build-revision/paper.pdf paper.pdf
pdfinfo paper.pdf
mkdir -p ../../tmp/pdfs/painter-distribution-revision
pdftoppm -r 85 -png paper.pdf ../../tmp/pdfs/painter-distribution-revision/page
```

Inspect every rendered page after editing. The build requires Tectonic's LaTeX
bundle and uses the original controlled-study plots plus new revision plots.
The source, bibliography, figures and compact numeric records are available in
the repository; a raw-artwork release and journal submission are not claimed.

Verification completed on 2026-09-07: 886 offline tests, Ruff, both revision replay
commands, all 44 report bytes, and the 2,902-check historical evidence audit pass.
All final PDF pages were visually checked; the dense new figures use full landscape
pages for readability. Manuscript review was performed by maintainer-run LLM
subagents and the coordinator, not independent institutional reviewers.
