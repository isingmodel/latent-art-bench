# Public numerical reproduction — pprv1-20260910

The [versioned release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
is public. The numerical archive was anonymously downloaded, hash-checked and
replayed in a fresh locked environment. [PUBLICATION_VERIFICATION.json](PUBLICATION_VERIFICATION.json)
records actual access, source identities, hosted verification and the separately
identified manuscript correction.

## Verified artifact

- Archive: `pprv1-20260910.tar.gz`, 11,851,958 bytes, SHA256
  `165ffbde2ba234e80a1da450f0e10453b127d79538317b6113ed8c145c6c6de4`.
- Inventory: 299 manifest files, plus manifest and checksum file; 301 regular members.
  All 294 copied inputs match local source commit
  `b2884c3cbc1ec281dc9d4383b3aceed90d6eff90`; five generated files describe the release.
- Public branch/tag commit: `2592dfbe6667586e30d945119418bfefe24690ad`.
  Its history contains sanitized release candidates, excluding original local research history.
- Code, numerical inputs, prompts and eight figures cover all four painters,
  both original controlled studies, computational diagnostics, measurement challenges
  and the terminal 264-image temporal successor. `COVERAGE.json` distinguishes
  recomputed results from recorded metadata.

| Check | Result | Receipt |
| --- | --- | --- |
| Fresh locked macOS | 98 exact checks; all eight PDFs byte-identical; 54.41 seconds | [Local](LOCAL_REPLAY.json) |
| [Hosted Ubuntu](https://github.com/isingmodel/latent-art-bench/actions/runs/34425107886) | 98 checks under documented 1e-10 floating comparison; seven exact PDFs, challenge PDF rendered from verified inputs with different platform bytes; 106.20 seconds | [Hosted](HOSTED_VERIFICATION.json) |
| Anonymous archive download and fresh macOS replay | HTTP 200 without GitHub credentials; archive checksum matches; 98 exact checks and all eight PDF bytes; 52.62 seconds | [Anonymous](ANONYMOUS_REPLAY.json) |
| Corrected manuscript/erratum access | All three additive assets anonymously downloaded and hash-verified | [Publication receipt](PUBLICATION_VERIFICATION.json) |

Runtime: Python 3.13.11, uv 0.9.28 and the unchanged lockfile. The numerical guard
observed no network or subprocess attempts in any full replay. A macOS optional
system-file probe was blocked; Ubuntu reported no outside-file attempts. These
are Python audit-hook observations, not an operating-system security sandbox.

## Portability correction and manuscript r1

The first two hosted runs exposed exact comparisons of continuous Welch p-values.
An explicit post-CI adapter amendment applies the existing 1e-10 bound only to
recognized approximate Welch schemas and their Holm transforms. Unknown and
randomization p-values, counts, identities and scientific decisions remain exact.
The final hosted receipt records actual differences up to 1.1102230246251565e-16.
A third run exposed an inner exact comparison in the palette figure helper; its
portable adapter now uses the same reviewed comparator while its standalone
default remains strict. No frozen scientific output or expected hash was refreshed.

Use the additive [corrected paper](https://github.com/isingmodel/latent-art-bench/releases/download/pprv1-20260910/paper-r1.pdf)
and [corrected source](https://github.com/isingmodel/latent-art-bench/releases/download/pprv1-20260910/paper-r1.tex).
The [explicit erratum](PAPER_ERRATUM.md) clarifies Appendix H's portability wording
and corrects one subject–verb agreement. The original archive and original paper
asset remain unchanged. The local canonical `paper/paper.tex` and `paper/paper.pdf`
match r1; the manuscript remains 32 pages, with the same results and eight figures.

## Reproduction scope

The package supplies numerical reproduction from retained measurements. It excludes
raw artwork, generated pixels, private responses, credentials, weights, literature
full text and user-owned drafts. It does not provide public feature re-extraction,
independent transport authentication, human-perceptual validation, independent
capture equivalence or replication by independent investigators. Source URLs and
recorded license metadata do not guarantee current image access or redistribution
permission. The fresh cohort and these checks were performed by the same maintainer;
review agents were maintainer-run LLMs.
