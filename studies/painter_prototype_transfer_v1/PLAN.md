# Held-scene prototype transfer audit v1

Written 2026-09-19 after the original and learned audits and round-02 review.
This is a retrospective analysis of existing images. Baseline recognition,
including painter confusion counts, has already been seen. Translated outcomes
have not been computed or inspected. Freeze this plan and implementation before
computing the real translated outcomes. Do not rewrite a completed binding.

## Question and task

Does a fixed, label-agnostic common translation learned on other scenes improve
closed-set identification of the painter name in a held-out generation prompt?
The four recorded prompt names are the criterion. This is a known-label
identification task, not identification of physical authorship or perceptual
fidelity. All six requested configurations, both learned encoders, all 14
scenes, both repeats, and all four painters remain; no new image or paid call.

This is an application of ordinary mean translation/domain adaptation, not a
new algorithm. A benefit would demonstrate a specific consequence of a shared
cross-domain offset for this closed candidate set. It would not establish that
the common painting response is unwanted, validate pooled contrast error D,
resolve the shared-family baseline confound, or establish independent service
replication. A negative result is equally retained. No rating is guaranteed.

## Fixed feature geometry and splits

Use the completed hash-bound CLIP and CSD unit embeddings without re-extraction
or coordinate fitting. Main target is the 649 original-view reference works.
Also report all original/audited-region × primary/development reference targets
as prespecified sensitivities; they do not add generated observations. No target
or representation is chosen based on translation performance.

For model m and held-out scene s, the training mixture contains all four named
arms and both repeats from the other 13 scenes (104 images). Compute its pooled
mean gbar_train with equal painter/scene/repeat weights. Its computation does
not use which painter label belongs to a training image; knowledge that the
training mixture is balanced over the declared four candidates is assumed.
Reference prototypes mu_a are unnormalized means of unit historical embeddings;
let mubar be their equal-painter mean and u_a = mu_a / ||mu_a||.

### Three fixed rules

1. Reference baseline: argmax_a x dot u_a, the existing normalized-prototype rule.
2. Common translation: t = mubar - gbar_train; argmax_a (x+t) dot u_a.
   Translation scale is exactly 1. It has no fitted hyperparameter or label-based
   adjustment. Normalizing the translated query does not change this argmax.
   Report its norm and reject nonfinite vectors. Retain an exactly zero query
   with all-zero linear scores, the fixed first-index tie rule and a zero-query
   count; its cosine is undefined. It is generally not a unit
   embedding on the encoder manifold; no image realizability claim follows.
3. Generated-prototype context: compute one training mean per known prompted
   painter from the same 13 scenes; normalize each and classify held-out x by
   largest dot product. This baseline uses per-painter generated labels, unlike
   the translation, and is explicitly supervised context rather than an equal-
   information zero-shot comparator. It must not be omitted if it is stronger.

Use deterministic first-index tie resolution in the fixed painter order and
report tie counts. Train separately for each model; do not pool generators.
Never include either repeat from the held-out scene in the training mean or
class prototype. Reference vectors stay fixed for every fold. No scale search,
threshold tuning, alternative correction, favorable artist selection or early
stopping based on outcomes. Every candidate rule must be reported.

## Output and interpretation

For every representation/view/target/configuration/rule retain: all 112 held-out
predictions; 4-by-4 confusion counts; per-painter recall and macro/micro accuracy;
all 14 scene accuracies; correct-prototype minus maximum incorrect-prototype
margin; and fold translation/prototype norms and tie counts. Report paired
translation-minus-baseline accuracy differences and counts of corrected and
newly incorrect decisions; report generated-prototype results alongside them.
Show the equal-configuration mean accuracy difference over all six configs;
this is a descriptive summary of the recorded set, not a population estimate.

This retrospective task has no new confirmatory significance family. Overlapping
training folds, fixed authored scenes and one service session do not supply
independent replications. Report scene-wise differences and all configurations;
no p-values, unqualified uncertainty intervals, or claims of significance from
fold wins. Improvement in name recovery can coexist with a poor reproduction
of historical painter features. Training-image overlap in CLIP/CSD remains
unknown and the development panel has been used before.

## Verification before real outcomes

Constructed-array tests must check: no held-out leakage; translation invariance
to permutation of training painter labels; exact fixed-rule predictions;
identity when the training mixture already equals the reference mean;
recovery in a known additive-offset example; retention of a constructed harmful
translation example; source-view and reference-target membership; complete
prediction/confusion accounting and baseline agreement with the retained audit.
The generated-centroid context must be trained only on the other scenes.

Bind this plan, implementation/tests, original row manifest, embeddings and
extraction/analysis receipts before real execution. Generate a create-once
analysis and a complete report, then verify exact replay. Never rewrite the
original learned audit or round-02 manuscript/reviews. If a technical correction
is needed after execution, preserve the original input/result and use a new
version or explicit correction record.

## Pre-outcome design clarification

The original pre-QA plan is preserved in PLAN_pre_design_qa.md. No real
translated outcome has been computed. The target mean remains the equal-artist
mean of UNNORMALIZED reference image centroids, matching actual source and
target first moments. A design reviewer suggested the mean of normalized
classification prototypes as an alternative; that is not adopted or evaluated.
Only the classification prototypes are normalized. Translation changes class
intercepts and leaves centered painter geometry unchanged within each fold.
It does not isolate the named-minus-generic causal component because its fit
uses no free or generic controls. This is a cross-domain decision diagnostic.
The zero-query rule above clarifies the existing linear argmax definition.
