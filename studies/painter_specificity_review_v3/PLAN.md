# Retrospective direct-naming and scene-stability diagnostics

Version 3, 2026-09-18. This is a **post-result analysis plan, not a
preregistration**. It preserves every earlier protocol, source file and result.
It uses only retained feature vectors; no images are acquired or generated.

## What was already inspected

The original primary and retrospective results were known before this plan.
A reviewer also computed the full-frame, scene-averaged named-minus-generic
shared fractions before writing this plan: approximately 0.713157, 0.709236,
0.711154, 0.666756, 0.691271 and 0.883905 in the existing six-model order.
The analysis choice is therefore exploratory. The square-window and
scene-deletion summaries below are additional retrospective sensitivities;
they do not expand the original confirmatory family or create new tests.

## Data and measurement target

Use the complete 6-model by 14-scene by 2-repeat by 6-arm retained panel and
the corrected 649-work reference reader. Analyze full-frame and central-square
vectors separately, each with its corresponding reference vectors and the
existing development-panel scaler. Keep all scenes, artists and coordinates.
The square window changes image content as well as geometry; it is not an
independent replication. No crops, new content labels or recalibrated scalers
are introduced here.

Model labels continue to identify requested service configurations, not
independently verified served checkpoints. Reference means are finite-panel
measurements, not estimates treated here as new withheld artist populations.

## Direct naming and exact decomposition

For one model, let z[s,k,a] be its feature vector; the first two arms are free
and generic, and the next four arms are named. Average each arm over the
retained scenes within repeat k. For baseline b, write

- h[a,k;b] = mean_s z[s,k,a] - mean_s z[s,k,b];
- c[k;b] = mean_a h[a,k;b];
- d[a,k] = h[a,k;b] - c[k;b].

Define common C[b] = 4 <c[1;b],c[2;b]>, specific B = sum_a <d[a,1],d[a,2]>,
and total T[b] = sum_a <h[a,1;b],h[a,2;b]>. Verify T[b] = C[b] + B and that
B is baseline-invariant. Report C, B, T and C/T for named-minus-free and
named-minus-generic. A shared fraction is unavailable when T <= 0; otherwise
retain it without clipping. Cross-product components can be negative, and
their ratios are neither unbiased nor guaranteed to lie in [0,1].

Let g[k] be generic-minus-free, n[k] be mean-named-minus-generic, and c[k]
be mean-named-minus-free. Verify c[k] = g[k] + n[k] and

    4<c[1],c[2]> = 4<g[1],g[2]> + 4<n[1],n[2]>
                    + 4(<g[1],n[2]> + <n[1],g[2]>).

Report all three right-hand terms, including the signed interaction. This
interaction is an algebraic cross term between measured shifts; it is not a
separate randomized factorial interaction or an identified internal mechanism.
No interpretation as additive percentages of causal contributions is made.

## Monet-Sisley alignment and scene deletion

For each view, let q be its finite-reference Monet mean minus Sisley mean.
The pair aligned response is mean_{s,k} <z[s,k,Monet]-z[s,k,Sisley],q>/||q||^2.
Keep q and the scaler fixed while deleting each scene in turn. Recompute the
entire scene-averaged shared decomposition, fractions and pair alignment on
the other 13 scenes. Store every deletion and summarize its minimum/maximum.
Do not average previously computed fractions or interpret deletion ranges as
confidence intervals. Report per-scene pair alignment as an additional
transparent view of this averaging operation.

## Interpretation and reproducibility

The finite collection describes the observed configuration/scene/template
combination. Independent, mean-zero repeat errors and stable conditional means
give cross-products their mean-shift squared-magnitude interpretation. This
analysis does not test actual service independence, validate perceptual style,
remove historical subject/capture confounding, or establish equivalence from
small pair-alignment estimates. Reference uncertainty is not integrated into
the deletion ranges. No significance tests or new confidence intervals are
added.

Create only new files in the v3 namespace. The deterministic JSON and Markdown
report bind SHA-256 hashes of this plan, implementation, tests, retained data,
the existing input freezes and their recursively named inputs, and the locked
runtime declarations. `analyze` refuses to overwrite either output; `check`
recomputes both outputs exactly. Analytical tests cover independent-repeat
noise correction, baseline invariance, constructive/destructive interaction,
unbounded/undefined ratios, pair normalization and true refitting after scene
deletion. Existing data and scientific code remain untouched.

Commands:

```sh
uv run --locked pytest -q tests/painter_specificity_review_v3
uv run --locked python -m latent_art_bench.painter_specificity_review_v3 analyze
uv run --locked python -m latent_art_bench.painter_specificity_review_v3 check
```
