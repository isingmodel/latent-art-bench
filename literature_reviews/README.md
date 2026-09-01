# Painter-feature literature review

This directory is the evidence base for the prospective `painter_features_v1` relaunch of
LatentArtBench. Following Pilot 2, the target is the painter rather than the era or movement. It
asks a narrower question than the historical benchmark:

> Which measurements can support a reproducible painter-associated feature distribution across
> held-out works, under what preprocessing and sampling conditions, and after which source,
> content, medium, date, and reproduction confounds are excluded?

The review does not assume that artist, movement, quality, authenticity, or "style" is a
single image property. It separates at least six construct families:

1. color and luminance organization;
2. local texture, mark, edge, and spatial-frequency structure;
3. composition and multiscale spatial organization;
4. entropy, complexity, and distributional structure;
5. learned formal or appearance representations; and
6. semantic, contextual, iconographic, and affective representations.

It also reviews digitization effects, corpus construction, human validation, statistical
inference, and generative-distribution evaluation. A method is not promoted merely because it
classifies artists or appears in a highly cited paper. The evidence extraction records what
was measured, on which digital surrogates, with which validation, and with which unresolved
confounds. Individual-image properties are candidate coordinates; they are not called painter
features until held-out painter specificity transfers across sources and content strata.

## Contents

- `SEARCH_PROTOCOL.md` fixes the search, screening, extraction, and evidence-grading rules.
- `SEARCH_LOG.md` records executed searches and citation-chasing passes.
- EVIDENCE_MATRIX.csv contains 138 auditable primary-source or standard records, including
  review depth, evidence grade, disposition, and a concrete protocol consequence.
- `BIBLIOGRAPHY.md` gives 201 unique checked citations and stable primary-source links.
- reviews/ contains the Pilot 2 audit and five thematic critical reviews: interpretable
  features; Kim and learned representations; digitization; human construct validation; and
  distribution statistics and missingness.
- `SYNTHESIS.md` compares results across feature families.
- `METHOD_DECISIONS.md` records which methods are retained, diagnostic-only, or rejected.

## Boundary

This review authorizes no artwork acquisition, external-holdout access, feature extraction,
model download, or image generation. Pilots 0-3 remain historical. Any empirical study based
on this review requires its own committed protocol, fresh corpus/provider authorization, and
prospective validation gates.
