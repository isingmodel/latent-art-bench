# Prospective painter-clause numerical addendum: pcrv1-20260910

Final local build; publication is a separate action.
This standalone package replays only painter_clause_validation_v1 and its fixed painter_clause_successor_v1 cohort
from retained compact vectors, using unchanged qualified analysis and report functions. The
original pprv1-20260910 and naming-geometry releases remain necessary to reproduce
historical results. No original release is modified or replaced. Paper assets
are separate and are not needed for this numerical replay.

Verify before installing, then run the dedicated adapter (not the study CLI):

```sh
python tools/paper_clause_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_clause_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_clause_release.py \
  tests/painter_clause_validation_v1/test_analysis.py \
  tests/painter_clause_validation_v1/test_precision.py \
  tests/painter_clause_successor_v1/test_analysis.py
```

The optional tests also require a Git executable for temporary provenance
fixtures; maintainer-only terminal-workflow tests are explicitly skipped in this
compact package. Public verify/check require neither Git nor its history.

Each cohort's descriptor freeze_environment records its runtime. Python 3.13.11
matches its recorded interpreter. Installation may download dependencies.
Public verify uses only Python's standard library. Public check performs local
numerical computation: no Git, proxy,
network, response bodies, feature extraction, or image files are required.
The extra collection/workflow source is provided for inspection, not as a
supported generation entry point in this numerical package.

Every allocated slot/pipeline status, primary test and its withholding,
secondary summary, delivery record and report is checked exactly within its
own cohort. The original and optional successor are never pooled; the original
identity flag and unavailable results remain unchanged. The successor's .025
threshold is not recycled when the predecessor is unavailable.
For unavailable predecessor endpoints, the retained Holm value 1 is family
bookkeeping, not a computed p-value or evidence of non-rejection. Read the
withheld status and raw_p=null as unavailable inference.
No numerical tolerance or post-result correction is introduced. Cross-platform
floating differences fail exact replay and must be reported, not normalized away.

The export descriptor binds source commits, original terminal hashes and the
explicit projection. The original private freeze/proxy content is omitted;
its fingerprints and safe source bindings are provenance only. Collection and
measurement receipt path/hash metadata are retained verbatim where safe; absent
referenced workspaces are intentionally not copied or traversed by public check.
Checksums authenticate bytes relative to a trusted release checksum, not absent
raw responses or paintings. Code/numerical-export licensing grants no rights to
absent underlying artwork. No perceptual validity, independent capture, stable
remote checkpoint or independent-investigator claim follows from replay.

Only explicit allowlisted files are present. No Git history, media, credentials,
local proxy state, model weights, source checkouts or Korean drafts are included.
Reviews and implementation were maintainer-run LLM work with disclosed assistance.
