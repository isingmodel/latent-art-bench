# Offline numerical replay for the third ICML draft

This local artifact preserves the original numeric observations, analysis code,
plans, dependency lock and input hashes. It is associated with the 8-main-page,
46-total-page manuscript whose SHA-256 is
`bbcc12901427538ed0938cdea510f848a0999d0edd08b4bc707c5b6fb8051472`.
It is not a new collection, a scientific validation or a public image release.

## What is included

The fixed launcher runs 16 read-only checks:

1. The primary painter-contrast analysis and three declared source/view
   sensitivities, using the existing measurement adapter.
2. The two retained post-result diagnostic analyses and the source-region
   numerical sensitivity.
3. Direct named-minus-generic decomposition and request-timing diagnostics.
4. CLIP/CSD analysis from all retained vectors and both learned-table renderers.
5. Held-scene transfer analysis and its complete table renderer.
6. Assumed cross-repeat covariance sensitivity and its complete table renderer.

Each command retains the frozen code's own hash and result-equality checks.
The package manifest also binds every included file. All 23 records in the
frozen round-03 evidence manifest and the exact reviewed PDF are included and
checked against that round's hashes. Dependencies were found by
observing actual file reads by these fixed checks, followed by replay from a
separate extracted directory. All package Python sources are supplied to avoid
relying on an editable installation from the original checkout. The selected
pixel inventory and per-file source attribution are documentation; the pixels
themselves are absent.

Historical supporting studies not called by this launcher, figure rendering,
PDF compilation, pixel extraction and model checkpoint verification are outside
this artifact's replay scope. No claim is made that these 16 commands exhaust
every appendix computation or that the supplied metadata makes pixels recoverable.

## Run

Extract the archive into a new directory, preserving paths. Use an existing
Python environment with the required packages, then run from that directory:

```sh
python -I -B scripts/icml_numeric_bundle.py verify
python -I -B scripts/icml_numeric_bundle.py run
```

The launcher verifies the complete manifest before and after replay. During each
numerical check, a Python audit hook rejects socket operations, process creation,
write-mode opens and filesystem mutation calls. It also rejects reads outside
the extracted directory, installed Python runtime/dependency prefixes and
specified operating-system version metadata. The `--execute-real` arguments in two fixed
commands mean recomputation on the retained real observations; these checks do
not make service requests. There is no collector or extractor entrypoint in the
launcher. This guard is an accidental-operation check, not a security sandbox
for untrusted Python extensions.

The extracted directory must contain exactly the manifest-listed files and the
manifest. Keep virtual environments, logs and Python bytecode outside it; `-I -B`
and the launcher disable bytecode generation. Do not run `freeze`, `extract`,
`collect` or write-mode `analyze` commands from other supplied modules.

## Environment and limits

Verified host environment: Python 3.13.11, NumPy 2.5.2, Pillow 11.3.0,
SciPy 1.18.1, scikit-image 0.26.0, PyWavelets 1.9.0, httpx 0.28.1,
pydantic 2.13.5, PyYAML 6.0.3 and typer 0.27.2. The original `pyproject.toml`
and `uv.lock` are included unchanged. Provision dependencies outside the extracted
directory before offline replay; dependency installers and wheels are not
bundled. For example, a connected environment can use the original lock with
`uv sync --locked --extra analysis` in a separate copy of the project files.
No learned-model weights, torch or transformers are needed for these commands.

The recorded extraction environment was macOS ARM64. This packaging check tests
relocation on the same machine with installed dependencies, not a clean operating
system installation or all numerical backends. Existing exact comparisons can
fail under a different numerical stack; do not silently loosen them or overwrite
the retained results. Record the discrepancy and environment instead.

The artifact excludes original/generated pixels, raw API responses, model
weights, credentials and unrelated workspace files. It cannot independently
validate image processing, source/crop judgments, served model identities,
session independence, perceptual fidelity, broader artist generalization or
scientific acceptance. A separate exact-pixel release and fresh independent
collection remain outstanding.

## Attribution

The repository's original `LICENSE` is included unchanged. Recorded source
licenses and credits are in `reports/icml_review_v1/artifact_attribution.json`;
the original-media records include public domain, CC0 and CC BY/BY-SA entries.
The numerical artifact does not purport to replace those terms or grant new
rights over source images. Scientific plans, frozen results and all adverse
findings remain byte-for-byte intact.
