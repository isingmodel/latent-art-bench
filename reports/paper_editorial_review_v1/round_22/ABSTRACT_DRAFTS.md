# Three independent abstract drafts for the following revision

These are authoring proposals, not editorial grades. Their authors were distinct
from the three independent round-22 reviewers and do not evaluate the next round.

## r23_abstract_a (149 words)

A painter’s name can produce a painting-like appearance without reproducing what distinguishes that painter. We test this distinction with six generators: 1,008 images crossing 14 fixed scenes, two repeats and artist-free, generic oil-painting and four painter-name prompts. Comparisons use 31 digital features and 649 reproductions of Monet, Sisley, Pissarro and Cézanne. After averaging scenes, 82.5–95.7% of repeat-corrected squared feature change from artist-free to named prompts is shared across names. Removing this shared response reveals alignment with reference painter differences in every model, but none demonstrably beats a predictor making no painter distinctions. FLUX.2 Max has the lowest uncalibrated error estimate. Retrospective checks find weak Monet–Sisley alignment in five models. Separate retrospective calibration shrinks measured differences using one factor per model fitted on the other 13 scenes, giving GPT Image 2 the lowest held-out error estimate. Allowing rescaling thus changes the lowest-error model without changing images or establishing perceptual fidelity.

## r23_abstract_b (148 words)

A painter's name can change an image without reproducing what distinguishes that painter. Six generators produced 1,008 images of 14 fixed outdoor scenes, using artist-free, generic oil-painting and Monet, Sisley, Pissarro or Cézanne prompts, with two repeats. We compare 31 color, spatial and texture features against 649 reproductions, subtracting four-painter means separately to isolate painter differences. After scene averaging, 82.5–95.7% of estimated repeat-corrected squared feature change from artist-free to named prompts is shared across names. All models partly align with reference differences, yet none demonstrably beats making no painter distinctions. FLUX.2 Max has the lowest uncalibrated error estimate. Retrospective checks find weak Monet–Sisley alignment in five models. Separate retrospective calibration uniformly rescales each model's measured contrasts using other scenes. Shrinking GPT Image 2's contrasts reduces off-target differences and gives it the lowest held-out error estimate without changing images. Response strength affects measured agreement; perceptual fidelity is not established.

## r23_abstract_c (149 words)

Painter names may evoke a common painting appearance without reproducing differences between painters. To test this, six generators produced 1,008 images across 14 fixed scenes, two repeats and artist-free, generic oil-painting or four named-painter prompts. We compare 31 color, spatial and texture features in these images and 649 Monet, Sisley, Pissarro and Cézanne reproductions, subtracting four-painter means separately to isolate painter differences. After scene averaging and repeat correction, 82.5–95.7% of squared feature change from artist-free to named prompts is shared across names. Every model partly follows reference painter differences, but none demonstrably beats a predictor making no painter distinctions; FLUX.2 Max has the lowest uncalibrated error estimate. Retrospective checks find weak Monet–Sisley alignment in five models. Separate retrospective calibration fits one multiplier per model on other scenes: shrinking GPT Image 2's measured differences gives the lowest held-out error estimate, with images unchanged. These measurements do not establish perceptual fidelity.

## Aggregation decision

The final abstract uses B's concrete opening and efficient placement of painter
names in the prompt design; C's explicit measurement in both image sets,
separate centering and scene-average/repeat-correction scope; and A/C's common
factor per model, with an explicit shrinkage-to-error link. It keeps a theoretical
predictor as the no-distinction benchmark. One retrospective setup introduces
the pair checks, followed by a separate calibration, avoiding the repeated
“retrospective” setup. The main methods continue to identify both as post-result
analyses. Calibration affects only measured differences, with unchanged images
and no perceptual-fidelity claim. The final abstract has 152 whitespace words.
