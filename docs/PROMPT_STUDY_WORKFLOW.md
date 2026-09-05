# Repeated GPT image generation and prompt comparisons

The new `painter_prompt_study_v1` namespace implements the user's extension: more generated
images, prospectively fixed prompt methods, and analysis of distance from original paintings.
The [protocol](../studies/painter_prompt_study_v1/PROTOCOL.md) defines the scientific contract.
The older descriptive and empirical reports remain sealed source evidence.

## Design and resource decision

The three methods are the exact original “by artist” prompts, an explicit style instruction,
and that same instruction with added attention to color, composition and painted marks.
Each includes four artists and a matched artist-free control for all 16 original scenes.
Two requested OAuth aliases, `gpt-image-1` and `gpt-image-2`, give **480 requests per repetition**.
The tested service does not attest the underlying model snapshot.

The fixed reference is 649 already exposed measured paintings. Analysis retains the original
31 features and development-only scaler. No prior generated image is pooled into new blocks.
The 48 primary comparisons are adjacent prompt transitions in each alias × painter × feature
family. Negative estimates mean closer observed distributions for the later prompt method.
Matched-control effects and absolute distances are also reported.

The user asked for a modest image count. The former large-grid interval proposal was superseded
before any new generation. These complete-grid choices all fit the current local storage:

| Repetitions | New images, both aliases combined | Images per alias/method/condition | Estimated serial time | Raw-body estimate plus 5 GiB reserve |
| --- | ---: | ---: | ---: | ---: |
| 1 | 480 | 16 | 3.1 h | 6.8 GiB |
| 2 | 960 | 32 | 6.3 h | 8.6 GiB |
| 4 | 1,920 | 64 | 12.5 h | 12.1 GiB |

The proposed config uses four repetitions, pending the user's preferred cap. Its approved request
ceiling remains zero until that choice is resolved. The estimates use the previous mean response
size and latency, not guaranteed provider quota, output size or speed. All raw responses are
losslessly compressed; decoded images exist only temporarily during measurement. About 24.7 GiB
was available when the reduced design was prepared, so an external volume is no longer required
for these options. Preserve all historical evidence bytes.

Within each alias/scene/condition/repetition triplet, independently assign the three prompt
methods to three chronological request positions using a uniform random permutation. Allocation
and permutation-test seeds are separately drawn once from system randomness, committed before
new generation and never searched against outcomes. All 16 scenes and all painter/free conditions
remain represented. The smaller design does not treat only two repetition pairs as enough for
precise confidence intervals.

The primary statistic remains the difference of finite energy distances from the same artist's
paintings. For each adjacent comparison, conditional on the third method's position, swap the two
method labels within each scene/repetition pair. Use exact enumeration for 16 pairs and 99,999
uniform random swaps plus the observed assignment for 32 or 64 pairs. Apply Holm correction to
all 48 two-sided p-values. This method tests a sharp no-prompt-effect/no-interference null, or
justified joint swap invariance. It does not test only equality of population energy distances
and produces no distance confidence interval. A point estimate's direction remains descriptive.
The small design is suitable for a transparent exploratory comparison; it does not promise high
power for subtle differences or equivalence. The [protocol](../studies/painter_prompt_study_v1/PROTOCOL.md)
records the formulas, assignment design, test interpretation and interference limitations.

The [randomization qualification decision](../data/manifests/painter_prompt_study_v1/pps1-randomization-20260905/decision.json)
binds prospective synthetic development, unseen validation, actual engine tests and source
commits. Calibration exercises the stated null construction; it does not prove the remote service
has no carryover or that requested aliases identify model snapshots. Earlier paired-t/jackknife
synthetic candidates remain development history, not the inference used for this reduced design.
Source inspection and review were maintainer-run LLM work, not institutionally independent reviews.

The [superseded interval-development record](../data/manifests/painter_prompt_study_v1/pps1-calibration-20260905/decision.json)
preserves all four larger-grid candidate jobs, including failed calibration cases. Its four
published jobs also replay every retained value at tolerance 1e-12 using the
`reproduce-interval-development pps1-calibration-20260905` command. It is not an active generation
option. Both calibration records bind source commit `5ba1339`; no empirical run is registered.

## Commands

Run from the repository root with the locked environment. The separate module CLI avoids
changing the historical main CLI that is bound by the previous report.

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli plan
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli check-calibration pps1-randomization-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli reproduce-randomization pps1-randomization-20260905
```

Before preparing a run, choose and record the complete resource authorization in
`configs/painter_prompt_study_v1/study.json`, provide sufficient workspace storage, and commit
the exact protocol/config/source/tests/calibration inputs. No generation freeze can be prepared
from uncommitted bound inputs or an unqualified sample count. The `RUN_ID` below is a new unique
ID, and `PROXY_CHECKOUT` is the local inspected proxy repository path; neither is inferred from
a historic terminal run.

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli prepare RUN_ID --proxy-root PROXY_CHECKOUT
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli generate RUN_ID --proxy-root PROXY_CHECKOUT --max-new-requests 480
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli status RUN_ID
```

The batch ceiling pauses the fixed grid at a request boundary. Repeating `generate` sends only
unattempted requests, in the original order. It does not increase the frozen budget or select
outcomes. Generation retains all response bodies and outcome accounting, performs no rerolls,
and closes permanently on authentication/quota failure or uncertain dispatch. It does not use
a paid API fallback. The normal local OAuth route is the only configured transport.

After generation is terminal, measure new retained responses and build the report:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli measure RUN_ID
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli analyze RUN_ID
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli report RUN_ID
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli check-run RUN_ID
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli audit --proxy-root PROXY_CHECKOUT
```

Every registered request gets one measurement disposition. If any grid cell is unavailable,
primary inference is explicitly unavailable and the report contains complete missingness
accounting. Complete runs produce 360 finite distance cells, 744 feature-coordinate diagnostics,
72 descriptive absolute estimates, all 48 primary randomization tests, 72 secondary contrasts,
scene-level contributions and sensitivity, chronology plots, service geometry/profile summaries and a duplicate screen against
the 649 reference paintings. All tabular outputs are exported at full precision.

Reports appear under `reports/painter_prompt_study_v1/RUN_ID/`, compact study evidence under
`data/manifests/painter_prompt_study_v1/RUN_ID/`, and raw responses only under the ignored
`research_workspace/painter_prompt_study_v1/RUN_ID/`. Audit checks the original recorded source
commits and current retained evidence. Omitting the proxy checkout explicitly leaves external
source verification unresolved.

`check-run` recomputes the complete analysis from the retained numeric features, using the frozen
test seeds, and renders the report in temporary storage for byte comparison. It does not request
or remeasure images or append to any study ledger. Run it from the frozen source checkout and
locked environment. The original analysis completion timestamp is retained for comparison.

For separate synthetic experiments, `simulate` accepts explicit seeds, trial counts, pair
counts, family alpha and condition dependence and writes a fresh output path. It never reads
empirical feature arrays or contacts the provider. Use `--help` for each command's options.

## Remaining empirical work

No new generation has run in this extension. Selecting the bounded image cap is the current external requirement; these smaller choices fit
local storage. After approval, freeze and execute the complete grid,
audit and measure it, inspect the full comparison report, and document any service drift or
missingness before treating the results as suitable for a paper. The previous 160 OAuth images
remain the only empirical GPT Image sample until then.
