# Painter Feature Generation v2 — prospective paper protocol

Protocol ID: `painter-feature-generation-v2/1.0`

Issued: 2026-09-05. Status: implementation in progress; no v2 image or generated result has
been inspected. The maintainer requested implementation of the complete analysis and research
paper and explicitly authorized prospective protocol improvements in the current session.

## 1. Continuation and claim

The question remains whether painter-name generation reproduces the distribution of interpretable
visual features of the corresponding painter's recorded outdoor-place paintings. All v1 protocols,
receipts, censuses, and ignored evidence remain unchanged. This is a disjoint prospective study,
not a retry of any terminal v1 census. V1's recorded determination is an input, not recomputed or
retrospectively relabelled evidence.

The construct remains **Wikidata-declared outdoor-place digital-surrogate feature reproduction**.
Attribution, object type, medium, support, and collection are timestamped Wikidata statements,
not institutional catalogue verification. Observational comparisons cannot establish content-free
style, physical brushwork, creativity, authorship, or oeuvre-wide representativeness.

The paper will report absolute discrepancy, each wrong-painter comparison, the matched artist-free
contrast, and location/spread diagnostics separately. Reproduction is **not demonstrated** unless
an independently justified, prospectively fixed equivalence margin and capture qualification are
available. A nonsignificant difference or improvement over control never establishes equivalence.
The absence of those calibrations does not prevent reporting the complete comparative experiment.

## 2. Explicit changes and reasons

1. The finite source frame is the 1,193 metadata-admitted v1 records, not an unfinished union of
   hypothetical future museum routes. Missing sources are a limitation; no top-ups are allowed.
2. Identity reconciliation joins QIDs only through explicit, unambiguous collection/accession
   matches. Identity ambiguity and crowd-maintained attribution are reported. A collection or
   URL hostname is never represented as an independently documented capture workflow.
3. Roles use 20/20/60 within painter rather than within painter × workflow. Very small collection
   cells otherwise create deterministic allocation losses unrelated to scientific information.
   Historical exposure remains development-only. Collection composition is reported by role.
4. Independent captures, workflow crossing, and calibrated equivalence remain requirements for
   a positive reproduction claim, but cease to be preconditions for a descriptive discrepancy
   paper. Synthetic image perturbations are robustness checks, never independent captures.
5. The prompt census and all three v1 feature families are retained. Generation resolution is
   selected from the chosen model's documented native contract before acquisition/feature
   execution; a common analysis resolution cannot exceed either source's native short side.
   The real-image admission floor stays 1,024 px. Lower analysis resolution does not admit new works.
6. No human or institutional independent review is claimed. The operator and any LLM assistance
   are disclosed. A self-check receipt is named as such, never an independent review.

## 3. Corpus and prospective roles

The v1 determination, recorded media census, exposure denylist, and prompt library are bound by
hash. Choose the already recorded primary surrogate, preserving its licence and Commons SHA-1.
Join only single-collection/single-inventory identities or identical QIDs. Conflicting painter
identities are excluded with a receipt. Multiple digital files are never added as independent works.

Match historical exposure by QID, collection/accession, canonical object URL, and conservatively by
normalized title within painter. The latter is an exposure flag, not proof of identity. Unresolved
denylist identities and their possible leakage are disclosed. No absence of a match proves that a
work was never seen by either the operator or model.

For new works, sort within painter by SHA256 of canonical JSON
`["pfg-v2/1.0-role", work_id]`; modulo-five ranks 0/1/2–4 receive development/qualification/
confirmation. Historical matches receive historical-development. No reassignment follows image
loss, feature failure, or statistical results. Fit the common transform on new development only.
Qualification is diagnostic without pipeline retuning. Confirmation is opened once after the
experiment contract, code, and scaling are frozen; each feature-read stage has a receipt.

## 4. Acquisition and retention

Before image acquisition, bind the clean committed code, protocol, environment lock, frame, exact
URLs, and acquisition configuration in a v2 execution freeze. The current session supplies the
maintainer's authorization for the research workflow. Live acquisition is a distinct command;
the standard tests never request network access.

Retrieve only the selected HTTPS `upload.wikimedia.org` originals. No redirect to another host,
alternative file, automatic source substitution, or silent top-up is allowed. Verify the recorded
Commons SHA-1, full decode, dimensions, format, and 1,024 px short side. Retain original bytes by
SHA-256 below the single ignored v2 workspace. Record each failed attempt and terminal outcome.
At most three attempts, only for transport errors, HTTP 429, or HTTP 5xx; respect Retry-After,
otherwise wait 5 and 15 seconds. Permanent failure is retained and never retried in place.
An interrupted acquisition may resume only unfinished downloads under the same immutable contract.
Insufficient disk space stops the run; it does not select a convenient prefix as the final corpus.

Retain profiles, alpha/border flags, provenance, and all exclusions. Automated flags are not expert
complete-view or watermark adjudication. Report complete-provider-file measurements with a uniform
1% crop sensitivity and explicitly disclose residual frame/watermark contamination.

## 5. Measurements

All real and generated images use exactly the same implementation. Decode without accepting
truncation; apply EXIF orientation; convert embedded ICC to sRGB with Pillow/LittleCMS perceptual
intent. Missing ICC is assumed sRGB and flagged. Reject invalid profiles and nonopaque alpha.
Preserve aspect ratio and downsample with Lanczos to the frozen short side; never upsample.
No per-image histogram, white balance, enhancement, or feature-dependent crop is allowed.

Compute linear RGB with the IEC sRGB transfer function, luminance with coefficients
0.2126/0.7152/0.0722, and CIELAB with the explicit D65/2-degree transform in scikit-image.
This resolves v1's ambiguous combination of LittleCMS's profile-connection Lab and D65 Lab.
Use float64 numerical arrays, half-up integer rounding, and pin the exact libraries in `uv.lock`.

Retain v1 §10's 11 color, 8 spatial/orientation, and 12 texture coordinates, evaluated at the
frozen short side S. Color uses all valid right/down CIEDE2000 pairs at 1%, 4%, 16% of S.
Spectral frequencies are cycles per short-side field of view, radial bins are log spaced from
4 to 128 inclusive, bin centers are geometric means, and the Theil–Sen intercept is median
`y - slope*x`. Use a Tukey 0.1 window. Scharr uses scipy's explicit 3×3 kernel divided by 16,
reflect edges, and excludes the outermost pixel from gradient histograms and summaries.
Texture uses stationary db2 levels ordered finest to coarsest, reflect padding to multiples of
16, uniform LBP on rounded 8-bit linear luminance with explicit reflect padding, and local
coefficient of variation with reflect filters. Zero-energy histograms have zero entropy/moment.

Each family uses a common equal-painter weighted development median/IQR transform, with empirical
inverse-CDF weighted quantiles. Zero/nonfinite IQR invalidates the whole family; no coordinates
are dropped or replaced. Family failure is reported and cannot support a reproduction conclusion.
Fixture tests cover colors, rotations, flat images, textures, normalization, and formula oracles.

## 6. Generation

Before any generated image, freeze one exact model identity/checkpoint revision, dependencies,
native dimensions, inference settings, negative-prompt handling, seeds, complete request order,
repetition count, and output accounting. The initial local configuration is Stability AI SD-Turbo,
revision `b261bac6fd2cf515557d5d0707481eafa0485ec2`, one inference step, float16 on Apple MPS,
512×512 native output, guidance 0, no negative prompt as specified by its model card
(<https://huggingface.co/stabilityai/sd-turbo>). Common analysis short side is 512 pixels; the
uniform 1% crop sensitivity uses 496 pixels for both its cropped and uncropped comparison so it
never upsamples a generated image. The smaller distilled model is selected for available local
compute, not by trial output quality. No model or inference setting is selected after inspecting
an active generated image. A different model requires a new prospectively frozen experiment.

Keep the 16 exact v1 templates and five conditions (four painter names, artist-free). Use 25 paired
repetition blocks initially: 2,000 registered requests. This is a prespecified computational design,
not a claimed power guarantee. Any different repetition count must be registered before generation.
Within each template/block the same seed is used for every condition where the model supports it.
Keep balanced blocks in randomized request order. An opaque API without reproducible seed semantics
must record that limitation and cannot claim deterministic paired latent interventions.

Every request has one immutable terminal disposition. Interrupted or uncertain generation attempts
are not silently rerun. Do not replace refusals, failed outputs, duplicates, or off-topic images.
No generated output is aesthetically selected. A complete analyzable grid is necessary for primary
inference; incomplete runs receive availability results and explicitly conditional descriptive
summaries only. No paid API or rented compute is used without a specified spending authorization.

## 7. Statistical analysis

The real reference is the complete successfully measured confirmation population, uniform over
works, conditional on the closed accessible frame and reported acquisition attrition. Do not
bootstrap real works to imply probability sampling of the oeuvre. The generated distribution is
uniform over the fixed 16 templates and registered repetitions. Keep duplicate multiplicity.

Use v1 §13.2's energy estimator: exact finite real self term and generator U-term excluding equal
repetition blocks. Retain negative estimates. Report each painter × family own-target distance,
three own-minus-other distances, and named-minus-artist-free distance (60 endpoints in total).
Negative contrast values favor specificity/control improvement; they do not establish equivalence.

Use 9,999 bootstrap resamples of complete repetition blocks, shared across templates, conditions,
families, and contrasts. Report simultaneous 95% intervals from the maximum absolute standardized
bootstrap deviation across the complete primary endpoint set. Zero/nonfinite bootstrap SD makes
an endpoint inconclusive. The finite-sample procedure is approximate and can be unstable near a
degenerate zero-distance null; report this and synthetic calibration, not a guaranteed error rate.

Report coordinate median differences and IQR ratios descriptively without threshold-based
reproduction labels. Report content-group and collection distributions, development-to-qualification
distances, resolution/profile stratification, and uniform 1% crop sensitivity. Sparse groups remain
unresolved rather than being represented as validated independent workflows. Exact-file and
perceptual near-neighbour screens are copy diagnostics; a simple perceptual hash cannot establish
absence of copying or certify originality.

## 8. Paper and reproducibility

The manuscript must distinguish completed corpus results, completed generated-image results, and
unexecuted work. No simulated fixture or mock transport output enters an empirical result table.
Bind all result tables to manifests and numeric outputs; produce figures from the same outputs.
Report failures and negative findings as fully as positive contrasts. Preserve all earlier evidence
and publish compact redistributable metadata/code only. Raw media and weights stay ignored.

The paper must disclose: crowd-edited attribution; finite convenience-frame coverage; metadata-only
content labels and painter-dependent content mix; incomplete identity/exposure crosswalks; capture,
profile, border, and resolution confounding; single-operator/LLM assistance; possible model training
overlap; approximate block inference; and lack of validated equivalence margins where applicable.

Primary methodological references: Székely and Rizzo (2013),
<https://doi.org/10.1016/j.jspi.2013.03.018>; Gretton et al. (2012),
<https://jmlr.org/papers/v13/gretton12a.html>; Kim et al. (2014),
<https://doi.org/10.1038/srep07370>; Lyu et al. (2004),
<https://doi.org/10.1073/pnas.0406398101>. These motivate measurements and comparisons, not
universal painter-fidelity thresholds.
