# Artist-specificity experiment

The terminal experiment compares reference artist contrasts after removing the common named response.
All four painters, all six models and every assigned scene remain in the census.

## Collection and accounting

Returned 1008 of 1008 planned images in 1008 attempts.
Additional reported charges: $43.786326; cumulative conservative accounting: $112.293676.
The cumulative figure includes the historical $5 reserve and all earlier cost probes; no remaining-credit query was made.
Raw-response hashes: 1008; image hashes: 1008.
Peak concurrent requests: 3; shortest start spacing: 5.001 seconds.

## Primary recovery outcomes

Beta 0 means no reference-aligned response; beta 1 matches its amplitude.
Expected D=0 is exact conditional mean-geometry recovery; expected D=1 is a purely common response.
The fixed 21-comparison family contains six slopes and 15 model contrasts. Absolute D intervals are nominal descriptive summaries.

| Model | Scenes | Beta (simultaneous CI) | D (nominal CI) | Amplitude error | Other-direction error |
| --- | ---: | --- | --- | ---: | ---: |
| gpt-image-1 | 14 | 0.938422 [0.708659, 1.168186] | 1.572416 [1.128880, 2.015952] | 0.028995 | 1.543421 |
| gpt-image-2 | 14 | 0.998650 [0.892823, 1.104478] | 1.225931 [0.957048, 1.494814] | -0.003006 | 1.228937 |
| gpt-image-2.5-flare | 14 | 0.771609 [0.679713, 0.863506] | 1.737719 [1.476903, 1.998536] | 0.054402 | 1.683318 |
| gpt-image-2.5-sunburst | 14 | 0.823899 [0.679875, 0.967924] | 1.641417 [1.311743, 1.971092] | 0.043693 | 1.597724 |
| google/gemini-3.1-flash-image | 14 | 0.442127 [0.255605, 0.628649] | 1.109451 [0.582408, 1.636494] | 0.316635 | 0.792816 |
| black-forest-labs/flux.2-max | 14 | 0.470020 [0.239269, 0.700770] | 0.800928 [0.586004, 1.015853] | 0.304350 | 0.496578 |

## Paired model regression comparisons

A negative difference favors model A on corrected artist-geometry error.
Comparisons use paired scene differences, with the actual n-1 degrees of freedom.
The common-panel OLS uses scene intercepts and GPT Image 2 as baseline. It is recorded in analysis.json.

| A | B | Scenes | D(A)-D(B) | Simultaneous interval |
| --- | --- | ---: | ---: | --- |
| gpt-image-1 | gpt-image-2 | 14 | 0.346485 | [-0.399607, 1.092577] |
| gpt-image-1 | gpt-image-2.5-flare | 14 | -0.165303 | [-1.027285, 0.696679] |
| gpt-image-1 | gpt-image-2.5-sunburst | 14 | -0.069001 | [-1.180694, 1.042692] |
| gpt-image-1 | google/gemini-3.1-flash-image | 14 | 0.462965 | [-0.602338, 1.528269] |
| gpt-image-1 | black-forest-labs/flux.2-max | 14 | 0.771488 | [-0.037184, 1.580160] |
| gpt-image-2 | gpt-image-2.5-flare | 14 | -0.511788 | [-1.149719, 0.126143] |
| gpt-image-2 | gpt-image-2.5-sunburst | 14 | -0.415486 | [-1.180985, 0.350012] |
| gpt-image-2 | google/gemini-3.1-flash-image | 14 | 0.116480 | [-0.921807, 1.154767] |
| gpt-image-2 | black-forest-labs/flux.2-max | 14 | 0.425003 | [-0.161452, 1.011458] |
| gpt-image-2.5-flare | gpt-image-2.5-sunburst | 14 | 0.096302 | [-0.285607, 0.478211] |
| gpt-image-2.5-flare | google/gemini-3.1-flash-image | 14 | 0.628268 | [-0.283162, 1.539698] |
| gpt-image-2.5-flare | black-forest-labs/flux.2-max | 14 | 0.936791 | [0.255552, 1.618030] |
| gpt-image-2.5-sunburst | google/gemini-3.1-flash-image | 14 | 0.531966 | [-0.435867, 1.499799] |
| gpt-image-2.5-sunburst | black-forest-labs/flux.2-max | 14 | 0.840489 | [0.058186, 1.622791] |
| google/gemini-3.1-flash-image | black-forest-labs/flux.2-max | 14 | 0.308523 | [-0.846665, 1.463710] |

## Scope and sensitivity

Reference contrast H=5.915007480; its color/spatial/texture shares are 0.3595/0.2533/0.3872.
Equal-class-weight reference target cosine with the original: 0.956905.
The reweighted target uses four historical title-lexicon classes and is conditional on that metadata classification.
models.csv includes common-square and reference-content sensitivity estimates. The separate JSONs retain all intervals, resampling summaries and reference counts.
artists.csv retains energy, generic energy and spread for every model/painter cell. Within-scene trace is the mean squared distance between the two repeats divided by two: the sample variance trace within a scene. It is also divided by the reference trace for comparison in common units. These are descriptive summaries, not additional hypothesis tests.
The four geometry-error contributions sum to each model's primary D. They are additive diagnostics of that existing endpoint, not separate artist-fidelity scores: centering couples the four named conditions and finite contributions can be negative.
A large common fraction is not evidence against artist recovery by itself. Reference-relative slopes/errors test that separate question.
The primary target is conditional mean geometry in 31 fixed digital features, not full distributional or perceptual style recovery.
Reference content/capture differences, feature weighting, the fixed outdoor scenes and uncertain repeat independence limit interpretation.
The class-balanced reference target has its own H; absolute D values across targets are not in the same units.

## Figures

All figures are generated from the recorded vectors and results by `paper/make_specificity_figures.py`. Projections are descriptive; numerical inference uses all 31 coordinates.

- [Model comparison](../../../paper/figures/specificity_comparison.pdf)
- [Centered artist geometry](../../../paper/figures/specificity_geometry.pdf)
- [Error decomposition and distribution spread](../../../paper/figures/specificity_diagnostics.pdf)
- [Monet distributions, all models](../../../paper/figures/specificity_distribution_claude_monet.pdf)
- [Sisley distributions, all models](../../../paper/figures/specificity_distribution_alfred_sisley.pdf)
- [Pissarro distributions, all models](../../../paper/figures/specificity_distribution_camille_pissarro.pdf)
- [Cézanne distributions, all models](../../../paper/figures/specificity_distribution_paul_cezanne.pdf)
- [Sunburst distributions, all four painters](../../../paper/figures/specificity_sunburst_distributions.pdf)

The four-painter Sunburst illustration was selected before inspecting new feature outcomes; it does not designate the best-performing model. Each painter's raw distribution projection is fitted to that painter's reference images only and is held fixed across model panels.

## Reproduction

Use the canonical commands in studies/painter_specificity_measurement_v1/CORRECTION.md.
Append --check for exact numerical replay; the report command also verifies raw response/image hashes.
The frozen original reader remains unchanged; the explicit adapter selects the protocol's 649 measured reference works from a manifest also retaining four older failures.
No terminated predecessor image or technical pilot enters scientific analysis.

```bash
make specificity-check  # four exact numerical replays, no image generation
make specificity-audit  # additionally requires retained local raw responses/pixels
uv run --locked python paper/make_specificity_figures.py --check
uv run --locked python paper/make_specificity_tables.py --check
```
