# Implementation and interpretation notes

These notes preserve implementation clarifications without rewriting the frozen
measurement plan or completed extraction records. Scientific learned outcomes
had not been inspected when the clarifications below were selected.

## Model loading and storage

The first CLIP preflight stopped before inference because the older Hugging Face
checkpoint contains a deterministic `position_ids` buffer that modern
Transformers makes nonpersistent. Its original source and input bindings are
preserved in `preflight_01/`. The corrected loader verifies this buffer equals
`arange(257)` before omitting it, then strictly loads every model parameter.

Downloading both public checkpoints together exhausted local free disk space.
Only the newly created failed CSD partial download was removed. Checkpoints are
therefore used serially: retain CLIP until extraction and supplementary
validation finish, then evict this re-downloadable public weight file before
fetching CSD. Keep the immutable checkpoint identity/hash, configurations,
embeddings and receipts. No original research image or response is deleted.

## Native preprocessing

The Hugging Face CLIP processor floors center-crop offsets. The official CSD
Torchvision transform rounds half-offsets instead. For odd resized long-side
dimensions these can differ by one pixel. CLIP retains its released HF
preprocessing. `painter_learned_csd_v1` explicitly implements the official CSD
resize and round-center-crop convention with PIL and Torch, bound by
`csd_adapter_inputs.json`. Both begin from the orientation/ICC-corrected original
pixels. No representation result selected either convention.

The public CSD file is a full training checkpoint rather than a flat parameter
dictionary. Static inspection found only `numpy.dtype`,
`numpy.core.multiarray.scalar` and `argparse.Namespace` as non-default metadata
globals. The version-2 adapter retains `weights_only=True`, allowlists these
standard data constructors plus the explicit NumPy float64 dtype class, selects
`model_state_dict`, and checks all 297 parameter keys/dtypes and the 1024×768
style projection before strict loading. Optimizer and training arguments are
discarded. `csd_adapter_inputs_v2.json` binds this implementation; the first
preflight adapter/input remains preserved. General unsafe unpickling is never used.

## Algebraic interpretation clarified before analysis

With four painters, reference contrast energy H and aligned response beta:

- Mean diagonal minus mean off-diagonal prototype similarity equals H beta / 3.
- Mean named-minus-baseline diagonal similarity gain equals a common-shift
  inner product plus H beta / 4, for either free or generic baseline.

These exact identities explain what conventional proximity includes. They are
not independent empirical validation. The analysis exposes both terms and
does not clip opposing terms or their fractions. The empirical question is the
observed sizes of those terms and the behavior of recognition and painter pairs.

Reference-label permutation rankings of beta, D and prototype diagonal similarity
are also algebraically dependent. One beta-scale tolerance grouping supplies
their rank intervals, avoiding artificial differences from different score units.
They are descriptive negative controls, not post-result significance tests.

The plan's phrase “aggregate beta/D” was ambiguous: results include both the
mean scene-conditional D and a separately recomputed scene-averaged D for every
scene deletion. All deletion ranges are influence summaries, not confidence
intervals or fresh-request uncertainty.

## Supplemental verification

The base extractor checks CPU/MPS and batched/single agreement on three fixed
images. A separate four-image receipt verifies the actual batch size, including
a reference and an audited region, and adds explicit configuration, lockfile,
Pillow and preprocessing provenance. Completed extraction bindings remain
unchanged. See the read-only extraction review and supplementary validation
receipts for the precise coverage and numerical tolerances.
