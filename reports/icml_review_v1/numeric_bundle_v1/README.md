# Numerical bundle: verified local artifact

The final artifact is
[`icml_numeric_round03_final.tar.gz`](../../../output/artifacts/icml_numeric_round03_final.tar.gz):
**59,716,929 bytes**, 306 archive members, 217,449,989 uncompressed payload bytes.
SHA-256: `892a35046f11b70cdc1d74fb0aead95eb46422e869d204d3ec2edcf18d67da4b`.
The [archive receipt](archive.json) and [verification](verification.json) bind
the actual artifact and each independent-directory replay trace.

## Verification

- Extracted into a separate temporary directory with no links to the checkout.
- Verified 305 manifest-listed inputs plus the manifest, all 23 round-03
  scientific evidence bindings and the exact reviewed PDF.
- Passed all **16 fixed numerical/table checks** from the extracted copy,
  with project source and data read only from that copy. Runtime dependencies
  came from the already installed environment; no clean-OS claim is made.
- Rejected four integration probes: changed embedding bytes, a missing member,
  an extra member and a symlink outside the bundle. Original copied bytes were
  restored and the complete manifest was reverified before numerical replay.
- The independent [guard audit](guard_audit.md) passed **17 constructed probes**.
  Earlier filesystem-mutation and descriptor-write defects were fixed; the
  preserved audit history and candidate records document those failures.

The [included instructions](BUNDLE_README.md) describe the fixed commands,
dependencies and exact scope. The bundle is local, not a public deposit. It
does not contain original pixels, model weights or raw responses, and does not
resolve independent image access, source/crop judgments, fresh-request evidence
or scientific significance. No review score is assigned to packaging work.

## Version boundary

The bundled PDF is the **reviewed round-03** version with SHA-256
`bbcc12901427538ed0938cdea510f848a0999d0edd08b4bc707c5b6fb8051472`.
The subsequent [literature correction](../post_round_03_reporting/README.md)
changes prose/bibliography only and remains unscored. Frozen numeric results
and tables are identical. This bundle does not transfer the round-03 ratings
to that later PDF.

Candidate archives and discovery/relocation records are preserved to distinguish
initial defects from final verification. Disposable extracted copies were
removed after verification to recover local disk space; the final transport
archive and all verification records remain.
