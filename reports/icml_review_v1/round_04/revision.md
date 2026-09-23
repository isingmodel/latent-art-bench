# Substantive revision for scientific review round 04

This round adds two completed empirical analyses with definitions and code fixed
before their new outcomes. Both use previously exposed retained observations;
neither is a new prospective collection. No additional generation, paid service
calls, encoder execution or human evaluation was performed.

## Separate collection

The complete 2,000-image SD-Turbo collection crosses 25 paired-seed repeat blocks,
16 scenes, all four painters and a baseline already requesting oil painting.
Original pixel hashes are disjoint from the main 1,008-image collection. The
checkpoint, generation mechanism, resolution and exact prompt template differ,
while the 649 historical references and 221-work development scaling are reused.
The cross-block calculation preserves correlated arms within each block.

The complete metric has 64.18% pooled common naming change. Color and spatial
coordinates also have majority-common change; texture does not (36.58% pooled,
48.50% within scenes). All 25 block deletions retain these signs. Pooled and
scene-wise errors differ materially (.917 versus 1.637). All family/pair and
block-deletion outcomes remain in the bound numeric record and appendix tables.

## Reference-calibrated abstention

A fixed class-specific rank-calibration rule at alpha .10 uses historical
artworks to decide whether to issue an unchanged reference-prototype assignment.
An ordinary top-two-margin comparator accepts the same number of named queries.
All eight encoder/view/target settings, six configurations, four painters,
control arms and complete scene deletions are retained.

In the primary CSD/original/primary setting, accepted error falls by a mean
26.03 percentage points relative to unrestricted top-1 but by only .526 points
relative to matched-coverage margin filtering. Coverage is 24.11–57.14%; five
configurations miss the declared 50% floor, and three omit at least one painter.
GPT Image 1's zero-error accepted set has 30 images, including 28 Cezanne and
no Sisley. All eight settings fail the joint declared operating criterion.
The arbitrary 50% operating requirement is identified as such; continuous
metrics, adverse comparisons and undefined per-painter risks are displayed.
No rule or alpha was tuned after seeing these results.

## Verification and presentation

- Both implementations passed independent pre-outcome design/code audits and a
  combined 110 constructed tests.
- Independent raw-input replay verified 22,553 cross-cohort numeric values and
  435,066 selective-analysis values, including complete deletion calculations.
- Both exact analysis/report replays and all legacy ICML evidence checks pass.
- All 23 scientific bindings from round 03 remain unchanged.
- A question/readout/interpretation table clarifies the evaluation targets.
- Detailed original hand-feature comparisons move to the appendix; their values,
  negative results and conditional inferential scope are preserved.
- Related selective-classification and covariate-shift work is cited. The
  existing CSD-diagnostic prior-work correction is retained.

The limits concerning the same four painters, absent shared-family control,
closed-service dependence and incomplete public exact-pixel access remain.
The manuscript does not claim that common movement is artistically wrong,
that prompt recovery measures perceived fidelity, or that retained-code tests
are scientific validation. The final PDF and evidence will be frozen before
all three new independent reviewers inspect the same artifact under the
unchanged rubric. Prior reviews remain preserved; no recommendation is
requested or substituted based on its value.
