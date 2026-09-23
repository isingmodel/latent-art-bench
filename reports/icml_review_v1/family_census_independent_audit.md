# Independent audit: prospective feature-census adapter

19 September 2026. Read-only review of `feature_census.py` and its tests,
independent of their author. Audited implementation SHA-256:
`5d47088fe846e6df368070ae7c70a81685d48379f30ea294b79a2375e4c3049a`.

**Finding: the fixed design and ordinary tamper checks work, but the adapter
needs further structural validation before it is described as a fully verified
terminal-to-feature handoff.** Four substantive gaps were reproduced. The
separate absence of an actual encoder-execution receipt is an acknowledged
pipeline boundary, not evidence of an encoder having run.

## Scope and reproducibility

- Existing suite: `pytest -q tests/painter_family_controls_v1/test_feature_census.py`
  passed **11 tests**.
- Independent script: `scripts/audit_family_feature_census.py`; run with
  `.venv/bin/python scripts/audit_family_feature_census.py`.
- Retained probe results: `family_census_independent_audit.json` beside this note.
- Every probe creates a new temporary full 4,608-assignment fixture, executes
  four mock successful attempts, and deletes only that temporary fixture.
  Solid-color PNGs, mock charges and a synthetic clock are constructed data.
  No source/test files, historical observations, checkpoints or source images
  were modified; no model inference or network operation was performed.

Except for the stale-hash probe, structural ledger mutations recompute the event
chain, terminal binding and externally supplied file digests. Those probes test
whether an internally inconsistent but hash-bound input is rejected. They are
**not SHA-256 bypasses**, and do not show that a previously frozen external
digest can be silently changed.

## Findings

### 1. Image bytes are not cross-checked against the bound raw response

At the audited `load_terminal_census` image/response checks (lines 217–237),
each artifact is verified against its own receipt. The response is never decoded
to establish that its one returned image equals the retained original bytes.

The `image_response_mismatch` probe replaced one original with a different valid
1,024×1,024 PNG, updated its receipt/chain and left the raw response unchanged.
Both terminal loading and embedding consumption accepted all four observations.
Thus a receipt can bind different pixels to the request whose response is retained.

The related `claimed_geometry` probe substituted a valid 2×3 PNG while retaining
the receipt's declared 1,024×1,024 dimensions. Terminal loading accepted it.
Geometry is checked from receipt numbers rather than detected bytes.

**Suggested remediation:** decode the bounded response offline, verify the
number and identity of its retained image bytes, then decode original bytes to
check detected media type and actual geometry. Preserve technical mismatches as
missing evidence rather than accepting them as successful feature inputs.

### 2. A later success can replace an earlier successful attempt

The start/end checks verify each attempt's identity but do not reject a new
attempt after the same slot has already succeeded. Each completion assigns
`last[id] = event` (audited line 168).

`retry_after_success` appended a valid-looking second successful attempt for an
already successful slot, with matching files and revised accounting. The loader
accepted it and selected `pfam1-s00-m04-L2-shared_family-a2` instead of the retained
successful `a1`. This permits an input history inconsistent with the fixed
request/retry rule to choose the observation used downstream.

**Suggested remediation:** replay per-slot admissibility as well as hash order:
consecutive attempt numbers, one open attempt per slot, no attempt after success
or permanent refusal, and the declared retry eligibility/delay rules. This audit
does not assert that the actual collector currently produces such a history.

### 3. Terminal closure can precede retained completions

Completion timestamps are checked against starts, but `terminal.ended_at` is not
checked against those events. `early_terminal` set closure to 00:00:00 while
retaining completions through 00:00:16. The loader accepted four successful
observations and a permanently closed census.

**Suggested remediation:** require closure to be at or after every recorded
start/completion and relevant terminal event; preserve the specified handling of
unclosed intents explicitly. This matters for the requirement to extract only
after terminal closure, even though this module itself does not run extraction.

### 4. Public `TerminalCensus` construction can bypass simulation identity checks

The dataclass is immutable after construction, but its public constructor accepts
arbitrary `evidence_json`. `feature_manifest` and `load_embedding_census` trust
that JSON as if it came from `load_terminal_census`.

`forged_object` took a validated simulation census, changed only its in-memory
`simulation_only` value to false, and constructed a new `TerminalCensus` pointing
at the same run. Feature creation and consumption accepted it, returning false
while the unchanged on-disk `run.json` still reported true.

**Suggested remediation:** reauthenticate the source collector records and
compare the complete derived census at the consumption boundary, or use an
equivalent validated-construction design. The default file loader correctly
rejects simulation inputs; this finding concerns callers of the public
manifest/embedding functions with a manually constructed census. It does not
show a bypass of an orchestrator that always reloads external files itself.

## Checks that held

Independent probes confirmed rejection of a changed assignment/prompt even with
updated hashes, altered native encoder preprocessing metadata, reordered vector
IDs, changed bytes under a stale external digest, and simulation records passed
to the default terminal loader.

Code inspection and the existing tests support the complete 4,608-cell design
check, explicit missing census, per-attempt request/payload binding, chain and
accounting reconciliation, original-file rehash at consumption, fixed
6×8×12×8×768 assembly and NaN representation of missing cells. The tests exercise
four successful observations plus 4,604 missing assignments, not real outcomes
or a complete scientific cohort.

## Bound row identity is not proof of encoder execution

`encoder_contract` authenticates the fixed historical extraction receipt and
copies the named checkpoint/native preprocessing contract. The vector archive
is externally hash-bound, row IDs must match the image manifest, and vectors must
be finite unit vectors of length 768. These checks establish the identities
claimed by a supplied artifact and its axis mapping.

They do **not** establish that those vectors were computed from those images by
that checkpoint/preprocessor. `fabricated_vectors` supplied arbitrary basis
vectors with valid IDs and newly supplied archive hashes; consumption accepted
them without any encoder execution. This is expected for the current input
adapter and must remain an explicit limitation.

A prospective extraction execution receipt still needs to bind the actual
checkpoint bytes, preprocessing implementation/tensor identities, runtime,
terminal source identity, execution times, and produced vector archive. A
historical contract or a matching row count cannot substitute for that receipt.
No primary result, scientific score, live authorization or complete freeze
follows from this audit.
