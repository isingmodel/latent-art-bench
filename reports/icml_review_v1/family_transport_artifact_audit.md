# Independent audit of the old-only transport parameter candidate

19 September 2026. **Read-only provenance and parameter-equality audit.**
This audit inspected the retained old CLIP/CSD embedding arrays solely to
verify the declared parameter construction. It computed no recognition scores,
new empirical contrasts, scientific rating or prospective outcome. No new
data, extraction, model download or service call occurred. The implementation,
tests, candidate, receipt, historical artifacts and earlier audit reports were
not edited by this auditor.

## Result

**The prepared candidate has the declared old-only membership and its fitted
parameters match independent recomputation exactly for both encoders.**
The eight constructed provenance tests pass. No blocking defect was found
in the inspected candidate or its stated prepare/load workflow. This is a
parameter candidate, **not a complete prospective study freeze or permission
to collect**.

| Artifact | SHA-256 |
|---|---|
| `src/latent_art_bench/painter_family_controls_v1/transport_artifact.py` | `7f2787e801d485178654da3ec266ec613a105cc76a92dc9073cd4d8672dd4639` |
| `tests/painter_family_controls_v1/test_transport_artifact.py` | `b672a97c3d84ddc3117804402029a0f56332754486cb7cb1e43e3c4003e8e93c` |
| `reports/painter_family_controls_v1/old_transport_candidate_v1.json` | `fd6e80de75b7578059ecaee602b4ea5fc9e74f06d7711e52e8bd532cddbabac2` |
| Retained transfer input anchor | `bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf` |
| Retained learned input manifest | `bd9cb00279fffb741b3579e3234ad034bb593884925ea40893c717612eccca57` |

The candidate's separate receipt names the same candidate digest and reports
672 old named images, 649 references, CLIP/CSD, zero new observations and no live
authorization. The candidate itself has these values and explicitly says it
is not a complete precollection freeze.

## Membership, order and reference weighting

The retained manifest has 2,009 rows: 1,008 original generated images, 649
original references, 221 original development images, 90 audited reference
regions and 41 audited development regions. The constructor selects only
`view == "original"` and the four named generated arms for old fitting.
Generic/free arms, development images and audited regions are excluded.

The resulting old census is exactly **6 configurations × 14 scenes × 2 repeats
× 4 painters = 672 unique named images**, with a 768-feature axis in each
retained encoder. Tuple identities, rather than manifest row order, select each
cell. The configuration order is:

1. `gpt-image-1`
2. `gpt-image-2`
3. `gpt-image-2.5-flare`
4. `gpt-image-2.5-sunburst`
5. `google/gemini-3.1-flash-image`
6. `black-forest-labs/flux.2-max`

Scenes are integers 0–13 and repeats are integers 0–1. Painter order is Monet,
Sisley, Pissarro, Cezanne. The reference census in this order is exactly
**297, 106, 141, 105** original works, totaling 649. Each painter's raw mean is
computed over its own works; the four means then receive equal weight in the
translation. References are not pooled with weights proportional to their
unequal counts. Normalization is applied only to classifier prototypes.

Constructed tests reject missing/duplicate named cells, duplicate reference
identities, boolean scene identities and nonunit embeddings, and show that
reversing manifest rows preserves selected values. Actual source membership
was also checked independently through an explicit tuple-index lookup and
unique selected image identifiers.

## Independent parameter comparison

The replay oracle does **not** call `old_arrays` or
`fit_transport_parameters`. It constructs the old tensor independently from
explicit model/scene/repeat/painter tuples, collects original reference rows
independently, and uses these direct formulas:

```text
class_mean[m,a] = sum(old[m,:,:,a]) / 28
generated_grand_mean[m] = sum_a(class_mean[m,a]) / 4
raw_reference_mean[a] = mean(original_reference_rows[a])
translation[m] = sum_a(raw_reference_mean[a]) / 4 - generated_grand_mean[m]
reference_prototype[a] = raw_reference_mean[a] / norm(raw_reference_mean[a])
generated_prototype[m,a] = class_mean[m,a] / norm(class_mean[m,a])
```

For **both CLIP and CSD**, all six recorded arrays match element-for-element
with **maximum absolute difference 0.0**. The independently computed old-array
and raw-reference-array hashes also match the candidate. Encoder checkpoint
contracts equal the retained input manifest, and corresponding extraction
metadata names those same checkpoints. This is a construction check, not a
new evaluation of those representations.

## Source bindings and digest loader

Preparation first verifies the fixed SHA-256 of the retained transfer-input
anchor, then verifies the anchor's bindings before reading the old arrays.
The prepared candidate includes **14 direct file bindings**, including that
anchor, retained learned inputs/embedding archives/extraction and validation
receipts, the family analysis/protocol/artifact code and runtime lock. Every
direct binding matched at load time in this audit. Path-escape and changed-file
checks are covered by the constructed tests.

`load_prepared` requires a caller-supplied expected SHA-256 before parsing the
candidate, checks its schema/anchor/model/painter identities, and verifies its
listed source bindings. A mismatched expected digest is rejected. This closes
the prior bare-parameter mapping's accidental file substitution gap **when the
caller uses the externally fixed expected digest**.

The trust boundary remains explicit: a caller must obtain that expected
digest from the separately frozen study manifest. Computing the expected
digest from whatever file happens to be present does not establish identity.
The current receipt and this audit record identify the candidate for later
freezing; neither substitutes for the still-pending complete study freeze.
The loader is not a general validator for arbitrary trusted-but-malformed JSON
or a proof of internal provider/checkpoint authenticity. The independently
checked candidate is the concrete artifact covered by this audit.

## Preserved executable replay and machine-readable results

- Parameter oracle: `scripts/audit_family_transport_parameters.py`
- Parameter results: `reports/icml_review_v1/family_transport_artifact_verification.json`
- Earlier numerical oracle: `scripts/audit_family_analysis_decimal.py`
- Numerical results, including **all 46 exact boundary-exclusion records**:
  `reports/icml_review_v1/family_analysis_decimal_verification.json`

The numerical replay reproduces the previously reported **309 cases, 2,751
decisive Decimal comparisons, 46 precision-boundary exclusions and zero
failures**. These additions preserve executable evidence without changing
either earlier prose audit. Each machine-readable summary binds its oracle
script and inspected implementation by hash. Both replay scripts pass Ruff.

Replay commands (omit `--output` to print results; the optional output path
must not already exist):

```sh
.venv/bin/pytest -q tests/painter_family_controls_v1/test_transport_artifact.py
# 8 passed in 0.50s on the inspected snapshot.

.venv/bin/python scripts/audit_family_transport_parameters.py \
  --expected-sha256 fd6e80de75b7578059ecaee602b4ea5fc9e74f06d7711e52e8bd532cddbabac2

.venv/bin/python scripts/audit_family_analysis_decimal.py
```

No new-query pool, new outcome or prospective tuning enters these checks.
The pending collection authorization, source/extraction contracts for future
features, absolute windows and other complete-study requirements remain
outside this old-only artifact audit.
