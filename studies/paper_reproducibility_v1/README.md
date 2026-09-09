# Public numerical reproduction package

This new namespace prepares a versioned, hash-identified, history-free public
release of the paper's retained measurements and computations. It does not change
any sealed scientific source or evidence. It does not constitute measurement
validation, an independently collected replication, or an audit of private media.

The export contains numerical vectors, their fixed scalers, image and request
identities, treatment/content labels, weights, seeds, folds, and nuisance grouping
metadata required by the unchanged scientific functions. Unused response bodies,
paths, ledger fields and duplicate scaled coordinates are omitted. Payload hashes
retain the existing cross-painter control matching. The transformation and every
source hash are recorded in the export manifest.

From the retained maintainer checkout:

```sh
uv run --locked python tools/paper_release.py export --release-id pprv1-20260910
uv run --locked python tools/paper_release.py check --release-id pprv1-20260910
uv run --locked python tools/paper_release.py build --release-id pprv1-20260910 --destination tmp/paper-release/pprv1-20260910
```

Export, archive and verification outputs are create-once. Use a new release ID or
new output directory for a successor; never refresh a scientific evidence hash.
`COVERAGE.json` records which result families are recomputed and which are retained
descriptions. Six figures use saved tables whose numerical analyses are separately
recomputed; the seventh computes all palette block interactions. The eighth renders
the measurement challenge matrix, whose unchanged computation is separately
replayed within the measurement extension. Acquisition counts
and transport history do not become independently verified because numeric replay
passes. Full archive verification remains a separate command in the original repo.

The release builder copies an explicit allowlist, not the working directory or Git
history. It includes no raw image pixels, provider responses, credentials, local
configuration, model weights, literature full text or Korean user drafts. MIT
licensing of code and author-produced numerical exports grants no rights to absent
underlying artwork. The original local commit is provenance, not a promise that the
old commit is publicly accessible.

Before publishing, inspect the staged manifest and artifact, install its locked
dependencies with the tested Python 3.13.11 and uv 0.9.28 into a fresh environment,
and run the complete isolated check without
the original checkout or archive. After publishing, anonymously download the exact
versioned archive and repeat the check; record archive hash, environment, commands,
scope and results. A maintainer or hosted-runner replay is computational verification,
not an independent research investigator's replication.

Future validation and independently collected study results belong in separate
versioned namespaces. Add their compact inputs, unchanged computation entry points,
source hashes and explicit coverage to a successor release; do not pool cohorts or
retroactively label a pending study complete.

The completed core export is retained once. `export-measurement` adds a separate
create-once 1706-vector extension, its expected result and original source hashes
after the measurement run's complete receipt exists. It calls the frozen
`pipeline.compute(rows, bundle)` and restores each old row's reference/generated
stage from its containing collection. No frozen measurement code is modified.

`export-replication` similarly adds the terminal fresh generation cohort's assigned
requests, all slot/pipeline outcomes, configuration, historical comparison rows and
collection receipt. Replay calls unchanged `analysis.analyze` and
`apply_collection_scope`, preserving missing-output and duration-based withholding.
An explicit metadata-only table retains every allocated slot and attempt event,
selected attempt, actual recorded UTC, delivered dimensions/format and reported
quality. Missing fields stay null; requested settings never substitute for actual
delivery. It contains no response body, header or local path and does not establish
independent authentication of service transport.
Neither extension can be exported before its bound output receipt exists; pending
studies are absent from completed replay coverage.

Final `build` verifies that every copied original source/data/design/manuscript file
matches the final local Git commit. The manifest distinguishes that build commit
from the earlier input-export commit and from the history-free public branch's own
commit. `--draft` permits a clearly labeled uncommitted development artifact only.
The public workflow exports the tracked tree without `.git`, installs the locked
runtime and runs the isolated checker on Ubuntu. It uses a fixed 1e-10 float
tolerance, preserving exact identities, counts, seeds, decisions and p-values.
Cross-platform PDF byte differences are labeled explicitly; local strict replay
requires byte identity. The workflow retains its verification receipt as an artifact.
The isolation flag installs a Python audit-hook guard for socket creation/use,
subprocesses and file access outside the release/runtime roots. It is not an OS
sandbox or hostile-code containment boundary; receipts retain blocked attempts.

Runtime receipts distinguish installed-distribution versions from module strings.
In the retained environment, PyWavelets distribution metadata is 1.9.0 while
`pywt.__version__` is 1.8.0. This is not by itself evidence of environment drift;
the measurement study consistently uses its frozen module-version convention.
