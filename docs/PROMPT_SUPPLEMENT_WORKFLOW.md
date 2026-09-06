# Available-output prompt supplement

`painter_prompt_supplement_v1` is a separate, explicitly **post-registration** analysis of
`pps1-gpt-prompts-20260905`. Its [contract](../studies/painter_prompt_supplement_v1/PROTOCOL.md)
and [configuration](../configs/painter_prompt_supplement_v1/study.json) were specified after the
first service refusal, at zero-based request sequence `415`, and before measurement of the new
generated images. The retained response is a service moderation refusal, not a decoding failure.

The original study and supplement are complete. All **1,920 approved requests** were attempted:
**1,918 images generated and measured, two moderation refusals**, with no measurement failures
among generated images. The second refusal was sequence `1718`, also `gpt-image-1`/`by_name`
(Cézanne; the first was Pissarro). The original complete-grid primary remains unavailable; this
supplement does not restore it. Neither refusal was retried or replaced. The supplement added
no provider calls or feature extractions; it read the original authorized measurements.

Read the [completed report with plots and exports](../reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md).
All generation, measurement and report writers have finished successfully. Terminal evidence
must not be rebuilt or resumed in place.

## Analysis and limits

The supplement reads terminal numeric features from the original run. It retains the same
649 exposed reference paintings, 221-painting development scaler and all 31 features. It reports:

- All-available descriptive distances, giving each of the 16 scenes weight `1/16` and dividing
  that weight equally among its measured outputs. A cell missing an entire scene is unavailable.
- Coordinate medians and IQRs using weighted empirical inverse-CDF quantiles for **both**
  reference and generated distributions. This differs from the earlier linear-interpolation rule.
- All 48 adjacent prompt comparisons on common measured scene/repetition pairs, with equal scene
  weights for both methods. Their before/after distances use that common support; they generally
  differ from differences between the all-available distances.
- All 72 secondary control-adjusted and overall contrasts as descriptive results on all-available
  support, plus every planned pair, exclusion, availability count and chronological diagnostic.

The exploratory tests address a **joint sharp null of no method effect on availability AND
measured features**, with no interference between requests. Conditional on the third method's
slots, this null preserves common-pair eligibility and weights under the allowed swaps. It is
stronger than a feature-only or equal-distance null. Prompt-dependent moderation can violate it;
rejection cannot be attributed specifically to feature differences rather than availability.

Use exact enumeration for up to 16 eligible pairs and 99,999 seeded Monte Carlo swaps otherwise.
Holm adjustment retains the full 48-test family at alpha `0.05`. An unavailable endpoint uses
`holm_input=1` only for adjustment; its reported raw and adjusted p-values remain unavailable.
There are **no confidence intervals**, equivalence claims or verified underlying model snapshots.
Requested OAuth aliases, image geometry, source capture and subject content limit interpretation.
Reviews are maintainer-run LLM subagent reviews, not institutionally independent reviews.

## Published qualification and preparation — 2026-09-06

**Qualification passed, the design is frozen and the empirical report is complete.** See
[current status](STATUS.md) for terminal accounting and verification.

| Published record | Identity | Commit |
| --- | --- | --- |
| Exact supplement implementation and tests | `painter_prompt_supplement_v1` | `b029031` |
| Passing qualification | `ppss1-qualification-20260905` | `ea6ee7b` |
| Supplement design freeze | `ppss1-missingness-20260905` | `f877cf0` |

All eight development and eight unseen-validation valid-null cells passed. The maximum observed
family-wise rejection rates were `0.0475` and `0.043`; maximum Wilson 95% upper bounds were
`0.0577209072` and `0.0528011087`, respectively. Published qualification records are identical to
the retained fixed-seed outputs, and full numerical replay passed.

Qualification includes independent weighted-energy and counterfactual assignment oracles, then
2,000 trials in each of eight prescribed valid-null cells for **each** of development and unseen
validation. Every cell in both runs must have a Wilson 95% upper bound on family-wise rejection
at most `0.065`. Retain the separate method-dependent-availability stress result. Do not change
the threshold, cases or seeds after seeing results. Synthetic qualification does not establish
the remote service's null assumptions or make the supplement preregistered.

The `qualify ppss1-qualification-20260905` and `prepare ppss1-missingness-20260905` creation
commands have already been executed. These immutable IDs reject reuse. The
[design freeze](../data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905/design_freeze.json)
was prepared at **2026-09-05 15:06:53 UTC** and committed at **15:06:57 UTC**, while source
measurement was absent. It binds 83 inputs and the observed generation-ledger prefix of 579
generated outcomes and one refusal. These counts describe that checkpoint, not current progress.
The supplement audit passed, and all 62 original generation-freeze inputs remain unchanged.

Publication must remain strictly earlier than the original measurement stage start; verification
checks the committed freeze and the measurement event chain. The absence of a measurement ledger
records a stage boundary, not institutional blinding. The qualification and freeze cannot be
backdated, edited or regenerated.

The current records can be checked now from the repository root. Keep both extras to preserve
the shared environment:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli check-qualification ppss1-qualification-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli audit
```

Ruff and all **722 offline tests** passed. This includes a full synthetic 1,920-disposition
numeric build and byte-for-byte replay of all 18 report files. Historical v1/v2 audits passed
2,902/15,809 checks. Synthetic validation does not constitute an empirical supplement result.

## Empirical result — 2026-09-06

All 48 exploratory endpoints are available. Forty-two have 64 common measured pairs and six
have 63; every scene remains represented. The full exports contain 360 distance cells, 72 target
summaries, 744 coordinate diagnostics, 1,024 pair records, 3,072 family contribution records,
72 secondary contrasts, 48 chronology diagnostics, 30 availability cells and 480 scene cells.

Explicit style instruction increased finite distance relative to by-name prompting in all 24
artist × alias × feature-family comparisons on the observed paired supports. Three reject the
declared joint sharp null after correction across all 48 tests:

| Requested service | Painter / family | Paired distance increase | Raw p | Holm p |
| --- | --- | ---: | ---: | ---: |
| `gpt-image-1` | Monet / color | 0.2246521525 | 0.00052 | 0.02444 |
| `gpt-image-2` | Monet / color | 0.3580528744 | 0.00001 | 0.00048 |
| `gpt-image-2` | Pissarro / texture | 0.2933245456 | 0.00058 | 0.02668 |

Adding aspects to style instruction had mixed directions (13 decreases, 11 increases) and no
Holm rejection. Nonsignificance does not establish equivalence or absence of an effect. Distances
are comparable within each feature family only; these results do not rank artistic quality or
verified underlying models. Joint-null rejection cannot isolate feature changes from availability.

All generated images had decoded geometry different from requested 1024×1024; reported quality
was low for 1,906 images and medium for 12. Both aliases lack attested model snapshots. The
reference consists of already exposed digital surrogates, not a probability sample of entire
oeuvres. No exact generated duplicates or reference perceptual-hash candidates were found,
but the uncalibrated hash screen cannot establish originality or training-data nonoverlap.

## Reproduce the completed report

The original measurement and report worker completed successfully. The supplement worker then
completed `build`, `check` and `audit` at **2026-09-06 00:23:39 UTC**. Diagnostic logs remain under
`tmp/pps1-gpt-prompts-20260905/completion/` and
`tmp/ppss1-missingness-20260905/completion/`; durable receipts and hash-bound reports are the
authority. Do not rerun creation commands against these terminal IDs.

Final verification repeated Ruff, all 722 offline tests, source/supplement audits and both
historical evidence audits successfully. All 18 empirical report files reproduce byte-for-byte.
A separate maintainer-run LLM subagent implementation reproduced all 360 distances within
1.56e-15, all 744 coordinate records exactly, and all 48 raw/Holm p-values exactly; actual plots
and every CSV inventory were reviewed. All 62 original, 79 qualification and 83 supplement
bindings match current bytes and their recorded commits. These reviews are not institutionally
independent. See [current status](STATUS.md) for the complete audit and retention accounting.

Verify the empirical numbers and all 18 report files with:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli check ppss1-missingness-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli audit
```

Compact qualification and source records live under `data/manifests/painter_prompt_supplement_v1/`;
the report, full-precision CSV tables and deterministic PNG/SVG plots live under
`reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/`. Existing outputs are never
overwritten. `check` recomputes all supplemental numbers and report bytes in temporary storage;
`audit` verifies source commits, the retained generation prefix and output hashes. Both use
numeric evidence and metadata without image access, provider calls or source-ledger changes.
