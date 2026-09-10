# Manuscript correction r1 — 2026-09-10

This correction applies to the paper accompanying release `pprv1-20260910`.
The original numerical archive remains unchanged, SHA256
`165ffbde2ba234e80a1da450f0e10453b127d79538317b6113ed8c145c6c6de4`.
The original `paper.pdf` asset and paper inside the archive are retained.

## Corrections

1. Appendix H originally stated that portable numerical replay requires exact
   p-values without qualification. The corrected text explains that recognized
   continuous Welch p-values and their Holm transforms use the documented
   1e-10 absolute/relative tolerance. Randomization and other p-values, identities,
   counts and scientific decisions remain exact. It identifies the comparator
   amendment made after cross-platform verification exposed final-bit differences.
   The release code and README already implemented and disclosed this policy.
2. Related Work corrects subject–verb agreement: “reports ... and probe” becomes
   “reports ... and probes” in the Asperti (2026) sentence.

No scientific result, data, inference implementation, hypothesis decision or
figure changes. This is an explicit manuscript correction, not a replacement
of any sealed archive or original release asset.

## Corrected manuscript

- `paper-r1.pdf` (32 pages), SHA256
  `dd7cca03dcd18a999b348577f65b28979d594654c577ec73037d8aa8456891bc`.
- `paper-r1.tex`, SHA256
  `4abff8f0b31110746eb6ab4a6de5cdc9992847fa0f0383c3ebb06d3abcbb5535`.

The original manuscript identities are PDF
`e78c56e664522bb1b9fc584319fe47615bc6b51dc3ed5c4cb40e483142817673`
and TeX `2b4dd5c04415300bee29977bf0762555f4af5e2b75490ca65ed90b4ba6fece71`.

Use `paper-r1.pdf` for reading. To compile the corrected source, place
`paper-r1.tex` alongside the original `paper.tex` in the extracted archive's
`paper/` directory and run `tectonic paper-r1.tex`, using the existing figures
and bibliography. Preserve the original archive files so their manifest hashes
and numerical replay remain verifiable.
