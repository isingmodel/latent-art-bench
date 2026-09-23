# Offline reference panels and secondary embedding reports

19 September 2026. Implementation evidence only. No new images, weights,
network requests, generated outcomes, collection authorization or scientific
score were produced.

## Retained reference targets

`reference_panels.py` authenticates the existing prototype-transfer input
anchor (`bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf`),
its retained bindings, the learned-input bindings and the CSD adapter bindings
before loading either retained NPZ. Both extraction receipts must agree with
the anchored input, NPZ, model identity, shape and dtype. The adapter never
opens source image pixels or public checkpoint weights.

Both existing fixed encoders produce these four raw, unnormalized painter-mean
targets, in Monet, Sisley, Pissarro, Cezanne order:

| Target | Painter counts | Existing audited replacements |
|---|---|---|
| `primary_original` | 297, 106, 141, 105 | 0, 0, 0, 0 |
| `primary_audited_region` | 297, 106, 141, 105 | 41, 23, 13, 13 |
| `development_original` | 101, 36, 48, 36 | 0, 0, 0, 0 |
| `development_audited_region` | 101, 36, 48, 36 | 17, 7, 11, 6 |

An audited target uses the already declared region row when present, otherwise
the original row. It does not add or select crops. Every member retains its
source ID, source path/hash, selected view/box, original row index, selected row
index and painter identity. Duplicate IDs/views, changed painter counts, crop
counts, source/crop identity mismatches and nonunit/nonfinite embeddings fail
closed. The primary original means exactly equal the existing transport
adapter's means for both encoders.

The create-once candidate is
`reports/painter_family_controls_v1/reference_panels_candidate_v1.json`, SHA-256
`0e3cf3628118324c7526a9a01e3fa9195ee1ace55ea401fa569c595696bcbd82`.
It contains eight mean panels, memberships, both fixed checkpoint/preprocessing
contracts and 35 file bindings. Its loader requires a separately supplied
expected digest, verifies the full retained chain and all required implementation
bindings, and recomputes the means/memberships before returning the record.
A relocated evidence bundle can use `root=...` with the same relative paths;
missing bound files fail closed. Preparation is not a complete study freeze.

## Secondary reporting interface

`analyze_secondary(generated, reference_means, window_times, *, representation,
reference_panel, observed=None)` calls the unchanged `window_components` for
all six models, eight windows, twelve scenes and eight arms. It retains:

- N, F, S, T, L, C_G, C_F, F-S and N-F absolute window components;
- free-baseline N and common terms;
- aggregate beta `L/(H/4)` and all six painter-pair alignments/betas;
- paired Fieller sets for F/N, C_G/N and C_F/(N-F), including negative/weak
  denominators and disconnected/unbounded sets;
- each complete eight-window mean, SD and leave-one-window influence;
- sum H and painter-mean H/4 reference energies, timing records, assumed
  correlation sensitivities and model/scene/arm labels for every missing cell.

Actual required-arm missingness propagates component by component. No scene or
window is deleted or reweighted. Generic cancellation preserves C_F, N-F and
F-S when their required arms exist. Undefined zero-energy betas remain null.

The wrapper emits no primary intervals, decision or multiplicity critical value;
it explicitly labels its scope secondary and disclaims an added familywise
claim. The orchestration layer must reserve the unchanged `analyze_primary`
for CSD with `primary_original`. Supplied array labels alone are not provenance:
the separate prospective feature/assignment loader authenticates generated
membership before these pure numerical functions run.

## Verification

`pytest -q tests/painter_family_controls_v1/test_reference_panels.py
tests/painter_family_controls_v1/test_secondary_embeddings.py`: **26 passed**.
Ruff checks passed for the two modules and their tests. Tests use constructed
unit embeddings with network disabled; the subsequent retained-only preparation
checked all 35 bindings and equality to the existing primary transport means.

Constructed cases cover exact original/audited selection and raw mean values,
permutation consistency, membership corruption, source/mean tampering,
mandatory external digest and historical anchor, create-once writes, all eight
encoder/reference combinations, secondary/primary separation, selective
missingness, negative and weak denominators, zero-energy beta and explicit
observed masks. They establish those implementation behaviors only.

The frozen `analysis.py`, `protocol.py`, `transport_artifact.py`, historical
inputs, archives, prior reports and prior candidate were not modified. The
31-feature secondary estimand and complete prospective freeze remain outside
these adapters.
