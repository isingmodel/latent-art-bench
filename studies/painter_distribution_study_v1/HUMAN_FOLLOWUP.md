# Human construct-validation follow-up

Prepared 2026-09-06. This is a research proposal, not completed human evidence.
No participant has been recruited, contacted or promised payment. Kim has not
been contacted or assigned an author role. Obtain the host institution's research
ethics determination before recruiting; the computational study can stand alone.

## Question and task

Test whether the 31-feature discrepancy predicts judgments of painter-style
similarity after controlling content, and distinguish that judgment from image
quality and real/generated detection. Agreement is empirical, not assumed.

Show a small reference set for one painter and two generated images with the same
scene brief. Ask which is closer to the reference set's visual style, with an
equally prominent "indistinguishable / cannot decide" option. In a separate block,
ask which image has higher visual quality. Do not label models or prompt methods.
Use separate participants or counterbalanced blocks for style and quality so the
questions do not become synonyms. A later authenticity task must be separate.

Use a fixed random sample of current successful outputs. Include named versus
artist-free pairs and a balanced subset of cross-model pairs. Selection uses
request IDs, scene class and availability only, never feature distance or visual
appeal. Retain all exclusions. Randomize left/right position, trial order and
reference-set order. Use identical display size and a neutral background; disclose
that processing and capture differences remain possible cues.

## Feasibility, sampling and analysis

A practical feasibility target is 24--36 consenting adult raters, including a
small separately labeled art-trained subgroup if recruitment permits. About 40
trials per rater is a burden estimate, not a power calculation. First conduct a
5--8-person usability pilot outside the final sample and examine completion time,
instruction comprehension and use of the uncertainty option. Do not tune the
metric or select favorable comparisons on that pilot.

After feasibility, preregister the final sample, exclusions, image inventory and
smallest relevant association. Simulate power with crossed rater and image/brief
effects; ratings are not independent images. Use a preregistered ordinal or
multinomial model that retains ties, with rater and brief effects and painter/model
covariates. Report uncertainty and agreement, including disagreement among trained
raters. Avoid presenting a small expert convenience sample as universal taste.

The principal predictor is the signed, fixed-metric difference between paired
images' distances to the displayed reference set, computed without fitting to
ratings. Distribution-level findings require group-level judgments as an additional
task; an image-level association alone does not validate distribution coverage.

## Materials to freeze before recruitment

- Consent and withdrawal text, compensation, expected duration and minimal data
  retention plan. Collect no unnecessary identifying or sensitive information.
- Exact reference and comparison image IDs, source rights, display processing,
  question text, randomization seed and trial allocation.
- Rater exclusion and attention-check rules, tied-response handling, model formula,
  multiplicity family, sample size and stopping rule.
- A clear separation between usability-pilot data and the final evaluation.

If human validation is deferred, the paper describes feature distributions and
perceptual limitations explicitly. It does not imply that participants would agree
with the measured distance or that separability means aesthetically poor images.
