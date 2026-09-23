# Independent read-only extraction implementation review

Reviewed the v1 extraction implementation, plan, input manifest, local model
configuration/preprocessing files, retained OpenAI vision code, and pinned
primary CSD source. No learned embeddings, similarity scores, or other learned
numerical outcomes were read. No frozen extraction source was modified. This
review is an implementation audit, not an independent scientific validation of
CLIP/CSD as measures of artistic fidelity.

## Inspected identities

- `src/latent_art_bench/painter_learned_audit_v1.py`:
  `156750d6d7099fb0a87b6ca789f5892d555ebca04fc58195aec85a8ea2a1c0c8`
- `studies/painter_learned_audit_v1/PLAN.md`:
  `c4af957b1922853b9541c02041d3a1b887a2f660dff709d3efb70710025766c0`
- `reports/painter_learned_audit_v1/inputs.json`:
  `bd9cb00279fffb741b3579e3234ad034bb593884925ea40893c717612eccca57`

The input manifest already records the legacy CLIP `position_ids` preflight
correction. The explicit deterministic-buffer check before omission is reasonable:
it does not discard an arbitrary learned tensor or relax strict weight loading.

## Findings and priorities

### 1. Membership and source handling are correct in the inspected manifest

There are 2,009 rows: 1,008 generated originals, 649 reference originals, 221
development originals, 90 additional reference regions, and 41 additional
development regions. All 1,008 generated model/scene/repeat/arm cells are unique.
The painter counts match the primary and scaler panels, and the historical
failed/reference and historical-development records do not enter this manifest.

Original versus audited views are paired by `(id, view)`. The region view replaces
only the 131 existing crop decisions, using the original embedding for other
works. Generated inputs are unchanged. EXIF/ICC conversion and crop rounding
match the declared source-region rules, and inference begins from the retained
original pixels rather than the hand-feature 512-pixel thumbnails. Native model
center crops must be described as center crops, not full-frame representations.

### 2. The proposed CSD style-head reconstruction is faithful

At the pinned official CSD commit, the visual backbone has its original
projection removed; a separate matrix projects backbone features into the style
embedding, then unit normalization is applied. Putting that style matrix in the
OpenAI `VisionTransformer.proj` field and normalizing its output is algebraically
equivalent for evaluation. The content head is unnecessary for this style-output
path. The 224/14, width-1024, 24-block, 16-head, 768-output architecture matches
the documented ViT-L/14 construction. See the pinned [CSD model implementation](https://raw.githubusercontent.com/learn2phoenix/CSD/3a9df32605b869eceb704897839be80977a9f1ea/CSD/model.py).

The CSD binary checkpoint was not yet present locally at the time of this
inspection, so this review does not attest to its actual keys or strict load.
When it arrives, validate the pinned hash, style matrix shape `(1024, 768)`, all
backbone keys/shapes, and absence of an extra backbone projection. The loader
currently accepts raw state dictionaries or a `state_dict` wrapper. Official
training-checkpoint code uses a `model_state_dict` wrapper; the Hugging Face
release may instead be raw model state. Inspect the actual release before adding
wrapper support, preserve any correction, and retain strict loading. See the
pinned [CSD loading example](https://raw.githubusercontent.com/learn2phoenix/CSD/3a9df32605b869eceb704897839be80977a9f1ea/main_sim.py).

### 3. Known CSD preprocessing correction is necessary and should be versioned

V1 uses the Hugging Face CLIP processor for both models. Official CSD inference
uses torchvision bicubic short-edge resize, center crop, tensor conversion, and
CLIP mean/std normalization. The known center-crop floor versus round difference
can change the selected pixel boundary when the resized long side is odd. Use
an explicit CSD-native adapter, with tensor-level equivalence checks against the
official transform on both odd/even aspect cases and an audited region. Preserve
the running/completed CLIP implementation and manifest; bind the adapter and its
validation in a separate versioned receipt. See the pinned [CSD inference transform](https://raw.githubusercontent.com/learn2phoenix/CSD/3a9df32605b869eceb704897839be80977a9f1ea/CSD/loss_utils.py).

### 4. Configuration/environment provenance is incomplete

`freeze()` binds the extraction source, plan, primary manifests, audit records,
and OpenAI model source/license. Model weight hashes are pinned and checked.
However, the current bindings omit the CLIP `config.json` and
`preprocessor_config.json`, `uv.lock`, and the installed Pillow/torchvision color
and image-processing environment. The receipt records the processor dictionary,
Torch/Transformers/NumPy versions, and device, but not the full vision config,
Pillow version, torchvision version, or LittleCMS version. Strict tensor shapes
do not constrain all behavior-affecting configuration values, such as activation
or layer-normalization settings.

Add a clearly timed provenance supplement with hashes of those files and
runtime/version details; do not rewrite the already frozen CLIP input as if the
additional bindings preceded execution. The current local vision config uses
QuickGELU, layer-norm epsilon `1e-5`, 224 inputs and patch size 14, consistent with
the intended model. This is an auditability gap, not evidence that those settings
were wrong during inference.

### 5. Preflight validates batch 3, whereas extraction uses batch 4

The current fixed sample contains two generated inputs and one reference. Its
batched-versus-single comparison is therefore **3 versus 1**, not the actual
extraction **4 versus 1**. A later partial batch has size one. Preserve the
existing validation record and add a fixed four-input comparison at the same
`5e-5` tolerance, including an audited/odd-aspect source, with CPU/device outputs
explicitly required to be finite before the tolerance check. This is a small
validation gap; the inspected architecture has no batch normalization and its
intended mathematical forward path is per-image.

Comparing normalized outputs is appropriate for the unit-vector estimand. Such a
small preflight is a backend/batching check, not proof that all image cases or
all devices produce identical measurements.

### 6. Add explicit invariants to a standalone numerical replay validator

`arrays()` verifies archive and input-manifest hashes, then joins positional
rows using `zip(manifest_rows, embeddings)`. For the present frozen archive,
hashes protect against accidental changes. A separate validator should also
assert exact `(2009, 768)` shape, finite unit vectors, row count, unique IDs/views,
reference/development painter counts, all generated cells, receipt/model identity,
and processed-tensor hash count. `zip` would otherwise ignore extra rows, and
only the generated tensor receives an explicit finite check in this loader.

Keep retained-vector replay distinct from inference replay: a later CSD adapter
must not make the original CLIP extraction source impossible to recover. Preserve
v1 source/input files, bind all later implementations explicitly, and document
which reader/adapter corresponds to each receipt. No need to rerun or select
scientific results merely to repair an archival description.

## Scientific interpretation

The plan correctly labels this as a retrospective same-image representation
sensitivity. Unit embeddings, a distinct finite development target, and full
coverage can test whether the original coordinate system explains particular
observations. They do not independently validate painter fidelity, remove content
sensitivity, establish service independence, create an unseen-artist evaluation,
or exclude training-image overlap. The plan acknowledges all four artists occur
in the CSD tag list and distinguishes released-checkpoint behavior from reported
CSD benchmark performance. Preserve those qualifications when reporting results.

## Overall assessment

Apart from the already identified CSD preprocessing mismatch, no additional
substantive membership or style-head mapping defect was found. The priority is
versioned native preprocessing plus completed strict checkpoint validation,
followed by supplemental configuration provenance, actual-batch validation, and
explicit archive invariants. These findings were communicated before reading
learned scientific outcomes.
