# Round 2 → revision

Round 2 reviewed PDF `2837299e…` (23 pages). Recommendations: methods **minor revision**,
empirical **minor revision**, editor **minor revision**. Criterion 1 (claims and evidence) was
*partially* for all three; criterion 2 (audience and clarity) *yes*, *yes* and *partially*;
desk-rejection risk *low* for all three. The round does not pass the rubric.

## New analysis

[`painter_tmlr_diagnostics_v2`](../../painter_tmlr_diagnostics_v2/REPORT.md), under a
[plan](../../../studies/painter_tmlr_diagnostics_v2/PLAN.md) written before this project computed
any of its quantities; the plan lists the values the round-2 reviewers had already computed. It
adds the exact-differences benchmark N/(N+H) (and its proximity-gain analogue), scene-bootstrap and
reference-resampling intervals for the observed, faithful and exact fractions and for all painter
pairs, joint resampling of D, the 31-feature separability of the development works, per-painter
proximity, cross-configuration family means with intervals, and SD-Turbo benchmarks. Replayed by
`make retrospective-check`; 6 constructed-data tests in the routine suite.

## Critical issues and responses

| Issue (reviewers) | Response |
| --- | --- |
| Abstract: proximity would stay mostly shared "for a generator that reproduced each painter exactly" contradicts CSD 48.3%; "only a few points higher" wrong (all three) | Abstract and §5.2 rewritten with the actual differences (−2.8 to +6.5 points) and the exact-differences benchmark (60.6–73.0% CLIP, 52.5–67.4% CSD), plus the condition under which the shared term dominates (shared term > H/4) |
| "Texture is the least shared family" false per configuration (all three) | Replaced by per-configuration orderings and cross-configuration means with intervals; texture is least on average and the only family with minority values |
| No real uncertainty for observed vs faithful; FLUX.2 Max not resolved (methods, editor) | Scene-bootstrap intervals and observed<faithful frequencies in Table 1 and Figure 3; FLUX.2 Max stated as unresolved (84.1%) |
| Faithful benchmark mixes the domain gap; "below faithful" misread as more specific (methods, empirical) | Exact-differences benchmark added throughout; Nano Banana 2 example explains the decomposition into coverage and between-name size |
| D not interpreted; genuine controls not related (editor) | Three configurations have D intervals above 1 under both resamplings; joint P(D<1); FLUX.2 Max relative to the content-sampled genuine level (0.753/0.731); recommendations specify which statistics to report |
| Prespecified family-level β/D unreported (methods) | New Table 16; §5.6 notes Nano Banana 2 has the lowest texture error |
| Pair-level claims lack intervals; 31-feature separability unchecked (empirical) | Pair intervals (Table 15, supplement for all pairs); development-panel recognition 49.8% (Monet 39.6%, Sisley 30.6%) vs ~80% in embeddings, and the Monet–Sisley interpretation revised |
| Internal inconsistencies (editor) | Development-panel wording fixed; Q stated in norm (1.49×); static-figure wording fixed and the pair figure is now generated; "independent generations" reworded |
| Scope: "for related painters" and "common appearance" (all three) | Scoped to the four painters; "centroid of these reproductions"; alternatives named |

## Minor changes

Opening claim cited (CSD similarity; Frochte on its use as style fidelity); related work adds
Xing et al. 2026 and directional CLIP similarity (Gal et al.; Brooks et al.); collection history
(stopped first attempt, 16→14 scenes) disclosed; prespecified bootstrap distinguished from new
resampling; interval estimand stated; 0.04% coverage scenario explained; genuine-control
class/class value (0.731); SD-Turbo faithful/exact benchmarks; short configuration names in all
tables and figures; scene table placed after its heading; Commons citation replaced; PDF date fixed
to a neutral UTC value for anonymity.

## Not changed

No human verification of the AI crops, no image release in the submission, and no new generation
(distant painters or a group clause) — owner decisions, stated as limitations.
