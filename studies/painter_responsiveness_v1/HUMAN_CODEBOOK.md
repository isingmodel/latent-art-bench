# Human reference and image assessment

Instrument version: `draft-v1`, fixed with this study's source freeze. This document
is a task specification, not a report of completed human work or an institutional
ethics determination. No raters have been recruited by the software.

## Before an actual human session

A responsible human supplies the study purpose, recruitment and institutional
requirements determination, voluntary consent/withdrawal information, storage
policy, actual pseudonymous rater IDs, task assignments, rater roles and consent
text. Use `independent` only for an actual non-maintainer human. A maintainer's
usability pilot is recorded separately and cannot qualify independent validation.
No model judgments or synthetic fixture exports are human data.

The initial local page is a **technical preview**. Its exports are intentionally
rejected by the validation importer. An actual session is prepared only from the
recorded human plan. Do not share the private asset map, raw source directory or
repository with raters. Share only the generated public session directory.
Pseudonymous IDs should not contain a participant's name, email or other identifiers.
Notes should contain image observations, not personal information.

## Task pools

Assign pools separately when exposure to one task could bias another. In particular,
do not reveal painter reference panels before prompt-free generated-image vividness
ratings. Reference annotation concerns already selected originals; its labels do
not retrospectively alter the old study's eligibility.

| Task | Information provided | Response |
| --- | --- | --- |
| Vividness / reference vividness | Image only; no prompt, condition, source filename or painter label | Integer 1 (very muted) to 7 (very vivid) |
| Scene adherence | Image plus scene description, with the artist clause removed | Integer 1 (not at all) to 7 (very closely) |
| Painter resemblance | Image plus identified painter's fixed reference panel | Integer 1 (not at all) to 7 (very closely) |
| Reference annotation | Original's normalized image with no source/painter fields | Structured scene codes below; uncertainty is an acceptable answer |

These are distinct questions, not one style score. The display uses aspect-preserving
512-short-side normalization and metadata-free PNGs. Browser/monitor color is not
calibrated by the software. Use a consistent display setup within a session and
record display limitations; color judgments cannot recover the paintings' physical
pigments or undocumented capture conditions.

## Scene codes

Select the dominant visible outdoor-place subject. Mixed or uncertain cases remain
explicit; do not force them into a convenient class.

- `outdoor_place`: yes / no / uncertain.
- `content_class`: water / built / land / other / mixed_uncertain. Water means a
  water body organizes the scene; built means buildings or constructed space
  organize it; land means primarily fields, vegetation or terrain.
- `fine_content`: lily_pond; other_pond_lake; river_stream; coast_harbor;
  buildings_street; bridge_road; fields_garden; woods_trees; hills_mountains;
  other; mixed_uncertain. Choose `mixed_uncertain` if no single code describes the
  dominant subject reliably.
- `viewpoint`: near / middle / distant / mixed_uncertain, describing the dominant
  scene organization rather than the historical artist's actual viewing position.
- `visible_border`: present / absent / uncertain. This records a visible image
  border, not a claim about the physical support.

Do not guess creation date, period, capture author, color management, restoration
or photographic ancestry from appearance. These require documentary evidence.

## Reference range decision

An independently coded candidate requires at least two distinct independent humans
who each supply vividness and scene annotation. Available independent coders must
agree on outdoor eligibility and broad/fine subject for group inclusion. Report
all disagreements; the implementation does not automatically adjudicate them.
All 70 selected works remain in the completeness accounting, avoiding selection of
a convenient rated subset after seeing responses.

The prospective scene groups are river_stream/water, buildings_street/built and
fields_garden/land, for Monet and Cézanne separately. Two distinct works permit
only an empirical span, not a credible distribution or power claim. Groups with
fewer than five works receive a thin-support warning; five is not an adequacy
threshold. Ranges and processing sensitivity are returned for every group.

Even complete annotation yields only `ready_for_responsible_human_margin_decision`.
A responsible human must decide whether these sources support the chosen reference
target and a meaningful chroma-response margin before generation. The simulation's
0.25/0.5/1 IQR values are hypothetical, not perceptual thresholds. Already exposed
works used for this decision are not held-out confirmation.

## Import and missingness

Exports contain the package ID, pseudonymous registered rater ID, phase, consent,
actual-human declaration, answers and display failures. Unknown or duplicate
task/rater pairs, changed packages, out-of-range answers, wrong phases and synthetic
exports are rejected. An empty import remains pending. Display failures and
unanswered assignments are recorded, not converted into neutral ratings.

Raw validated responses and the human plan stay in the ignored research workspace.
Only compact, deidentified scientific summaries and hashes belong in Git. Actual
participants must be told the agreed retention/withdrawal policy before responding.
