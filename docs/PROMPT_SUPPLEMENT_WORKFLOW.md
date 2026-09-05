# Available-output prompt supplement

`painter_prompt_supplement_v1` is a separate, explicitly **post-registration** analysis of
`pps1-gpt-prompts-20260905`. Its [contract](../studies/painter_prompt_supplement_v1/PROTOCOL.md)
and [configuration](../configs/painter_prompt_supplement_v1/study.json) were specified after the
first service refusal, at zero-based request sequence `415`, and before measurement of the new
generated images. The retained response is a service moderation refusal, not a decoding failure.

The original study and its workers continue unchanged. Its complete-grid primary remains
unavailable for an incomplete grid; this supplement does not restore it. The cap stays at
**1,920 requests**, including refusals. The supplement adds no retries, replacements, provider
calls or feature extractions; it reads features from the original authorized measurement stage.
Do not launch competing generation, measurement or report workers.

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

**Qualification passed and the supplement design is frozen.** No empirical supplement result
has been published yet. See [current status](STATUS.md) for execution checkpoints.

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

## Build and reproduce

A separate completion worker is already running. Its process identity is recorded in
`tmp/ppss1-missingness-20260905/completion/worker.json` (started as PID `1571`). It waits for
`tmp/pps1-gpt-prompts-20260905/completion/completed.json`, which records the original companion's
successful terminal measurement, unavailable-primary analysis, report and checks. It then runs
supplement `build ppss1-missingness-20260905`, `check ppss1-missingness-20260905` and `audit` in
order, with logs under its own completion directory. It stops on failure and never generates
images, retries requests or extracts features. Do not start a second supplement writer while it
is alive. The original workers continue unchanged.

**The empirical report remains pending.** Once the worker has published it, verify its numbers
and all report bytes with:

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
