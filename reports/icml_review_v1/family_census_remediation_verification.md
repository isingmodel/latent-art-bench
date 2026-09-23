# Terminal-to-feature census remediation verification

19 September 2026. Offline fixtures only. Preserve the
[initial independent audit](family_census_independent_audit.md) and its accepted
adverse cases; this document records the subsequent fixes and their limits.

The independent auditor's retained probe script was rerun against the corrected
implementation. Its [machine result](family_census_remediation_verification.json)
rejects all ten invalid-input probes: response/image mismatch, claimed geometry,
early closure, a retry after success, forged detached simulation identity,
changed preprocessing, changed row order, changed assignment, default simulation
loading and a stale external digest. Root verified that both source and probe
hashes in that result match the current files. The auditor's later turn ended
at an execution quota before completing a prose report; the retained machine
result is the available independent evidence. This summary is authored by root.

The root regression suite adds a stricter geometry case: it changes both the
raw response and decoded original to a2×3 image while retaining a1024×1024
receipt. Rejection therefore tests actual geometry after the response/image
bytes match, in addition to the auditor's mismatch case. All16 census tests
pass. Existing exact-assignment, missingness, feature-ID, vector-norm and
hash checks remain present.

Implemented corrections:

- Decode the one inline image from the retained raw response and compare its
  exact original bytes; decode actual geometry/format/MIME against the receipt.
- Check terminal time against all retained starts, completions and pauses.
- Validate first-dispatch order, global spacing, open attempts and allowed
  retries. A completed success cannot be replaced by a later preferred result.
- Reload bound collector evidence and compare it to a detached census before
  making feature inputs. Constructing a Python object cannot remove a
  simulation marker or substitute a different image list.

## Deliberately unresolved execution-provenance boundary

The eleventh probe supplies arbitrary unit vectors under an otherwise valid
feature manifest and digest. It remains accepted **as a supplied numeric
artifact**. No encoder ran. Hashes, row identity and dimension/norm checks cannot
prove that an encoder produced those values from the pixels. The raw31 loader
has the same distinction and explicitly records it.

The combined reporting adapter preserves `simulation_only` and
`actual_extractor_execution_authenticated=false`; its partial-census fixture
report cannot become empirical evidence. Production extraction must still bind
the executed implementation, checkpoints/preprocessing, input pixels, output
vectors, runtime and verification/replay. No actual-weight qualification,
full precollection freeze, live dispatch or scientific score is claimed.
