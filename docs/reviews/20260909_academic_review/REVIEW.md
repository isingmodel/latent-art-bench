# Academic manuscript review and revision — 9–10 September 2026

This record implements the requested three-reviewer assessment using the
[DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md).
The [fixed rubric](RUBRIC.md) adapts it to three equally weighted 1–10 aspects:
scientific rigor, contribution and significance, and clarity and reproducibility.
The aggregate is the mean of all nine scores. The requested target is **strictly
above 9**; it is a user target, not an instruction to the reviewers to award a
particular score.

Three maintainer-run LLM subagents read the full paper, checked selected retained
evidence and consulted primary literature. These are not independent human or
institutional reviews. Their baseline reports were written separately without
access to each other's reports. The rubric did not change between rounds.
Between rounds, reviewer 1 checked a block-level derivation, reviewer 2 checked
the literature and coverage corrections, and reviewer 3 implemented the compact
replay. The coordinator and reviewer 1 independently inspected and checked that
implementation. Each round 2 report discloses revision involvement; it is not a
fresh external assessment by reviewers unconnected with the changes.

## Reviewed versions and scores

Round 1 reviewed the 23-page manuscript at commit `1fcbcc5`:

- TeX SHA-256: `8466d0374936f884371b3acfcb73db8a7311f8a10bd16a0689ade4284cdd0b90`.
- PDF SHA-256: `040e3f054314d0f1e0213eeffb32325da10bd43fcc342b6abf41759d1f6190ee`.

| Round 1 reviewer | Scientific rigor | Contribution and significance | Clarity and reproducibility | Mean |
| --- | ---: | ---: | ---: | ---: |
| [Reviewer 1](round1_reviewer1.md) — statistics and measurement | 7.8 | 7.2 | 8.0 | 7.6667 |
| [Reviewer 2](round1_reviewer2.md) — contribution and literature | 8.0 | 7.3 | 8.0 | 7.7667 |
| [Reviewer 3](round1_reviewer3.md) — reporting and reproducibility | 8.0 | 7.4 | 7.8 | 7.7333 |
| **Aggregate** | **7.9333** | **7.3000** | **7.9333** | **7.7222** |

Round 2 reviewed the substantive revision, with 25 pages and seven figures:

- TeX SHA-256: `83deb0b17af76c82d6a9899edaee9359a128ef0c31832746771fd87acda5539d`.
- PDF SHA-256: `d4f731b6487a932543b943f93b5cbb95b47126cff581f3bd5f8785c0f9f2ac4c`.

| Round 2 reviewer | Scientific rigor | Contribution and significance | Clarity and reproducibility | Mean |
| --- | ---: | ---: | ---: | ---: |
| [Reviewer 1](round2_reviewer1.md) | 7.8 | 7.2 | 8.4 | 7.8000 |
| [Reviewer 2](round2_reviewer2.md) | 8.0 | 7.5 | 8.4 | 7.9667 |
| [Reviewer 3](round2_reviewer3.md) | 8.0 | 7.4 | 8.3 | 7.9000 |
| **Aggregate** | **7.9333** | **7.3667** | **8.3667** | **7.8889** |

The mean increased from **7.7222 to 7.8889**, but the requested **>9 target is
not achieved**. No reviewer identified a remaining major numerical or
claim-reporting defect. Their remaining substantive concerns require actual
validation, replication or public access. The coordinator has not overridden
scores, changed the rubric or requested repeated ratings of unchanged evidence.
Minor layout corrections follow this scored revision and do not constitute a
new scientific review round.

## Responses to the reviews

| Finding | Revision and evidential limit |
| --- | --- |
| R1 W5, R3 W5: abbreviated feature specification | Expanded Appendix A with the existing color thresholds, histogram bins, spatial scales, spectral fit, gradient and wavelet choices, LBP parameters and normalization. Added the development-painter counts and identified the exact frozen implementation and scaler. This improves specification; it does not validate the measurements as artistic resemblance. |
| R2 W3: missing artist-free coverage comparison | Added all six artist-free/named/matched-real medians at k=3 to the main results. Named median coverage increases in five comparisons and ties in one despite reduced spread; all six remain below matched real medians. The k=1/5 sensitivity is retained. These are reused finite-panel summaries, with no new significance tests. |
| R2 contribution comments, R3 W6: inaccurate nearest-work distinction | Corrected Deliège et al.'s historical target to expert-knowledge reference ranges, without a presented fixed historical-image corpus. Distinguished the present fixed reference panels and repeated scene intervention. Attributed the existing coverage definition directly to Naeem et al. The contribution is an empirical characterization, not a new metric or general explanation. |
| R1/R3 prompt and reference reproducibility | Added exact exploratory named/control constructions and stated that the scaler uses separate works by the same four painters. Preserved all four artists and the distinction between exploratory and controlled cohorts. |
| R1 W2: inspect Study 2 repeat variation and order | Added a post-result display of all 24 within-block interactions per painter from retained numeric outcomes, with scene and collection order identified. Monet has 17 negative blocks despite six negative scene means; the largest scene variance shares are 25.7% for Monet/garden and 44.5% for Cézanne/fields. Every block and the original primary inference are retained. These new descriptive summaries cannot establish independence or service stability. |
| R1 W4, R2 W5, R3 W2: separate numerical replay from archive verification | Added `paper/replay_palette.py` and `make palette-check`, calling the unchanged inference primitive and verifying exact agreement with saved primary results from three pinned compact files. The existing full archive verification is retained. Current manuscript code is distinguished from scientific snapshot `28a9eb6`. External archival release and access to response/pixel bytes remain unresolved. |
| R2 optional own/cross table | Retained the joint alignment definition, full three-service interaction table and the explicit NB2/Monet cross-painter preference in the main results. The underlying individual distances remain in the indexed numerical tables; another table would repeat the already illustrated limitation. |
| R3 optional raw-image illustration | Not added. It is optional and does not resolve measurement validity; the current paper-correction scope uses retained numeric evidence and does not reopen image access. |

## Remaining scientific and release work

The reviewers agree that substantive limitations remain beyond manuscript
wording. None is retrospectively repaired by adding caveats, diagnostics or a
second implementation of the same calculation.

1. **Validate what the feature gap measures.** A prospectively selected reference
   design with capture/geometry common support and independent content/style
   validation would address whether these image statistics track the intended
   painter resemblance. Another encoder would provide a complementary view,
   not ground truth. Human ratings remain unperformed and are not silently added
   to the user-authorized computational scope.
2. **Test transfer and repeat-error assumptions.** A new, separately versioned
   study could sample independent service collections and new scenes, compare
   several generic phrasings, and choose a relevant precision target in advance.
   Intermediate palette levels are needed if response shape becomes a claim.
   The closed cohorts cannot supply this replication or be resumed in place.
3. **Release an externally usable scientific package.** Archive the exact compact
   inputs and code with a durable version, test the numerical commands from that
   release, and state an actual response/pixel access policy. The new local replay
   does not itself publish a repository, release media, or arrange external access.

Further manuscript-only rounds should follow substantive unresolved editorial
findings, not repeated requests for higher scores on unchanged evidence.

## Validation and preservation

The substantive revision passed:

- Ruff and **1,149 offline tests**, including 14 new compact-input replay tests
  (114.10 seconds for the full suite). Initial targeted runs passed 19 and 31 tests.
- Exact replay of both saved Study 2 primary rows, covering estimates, standard
  errors, degrees of freedom, intervals, p-values and decision fields. The new
  tests independently calculate scalar Welch intervals and exercise damaged,
  duplicate, missing, nonfinite, mislabeled and reordered inputs. A temporary
  input root containing only three files demonstrates no data-archive dependency.
- Independent reviewer derivation of all 48 block contrasts, variance shares,
  shared-control covariance and order matching against collection/transport
  records. The new coverage table matches all six retained k=3 comparisons.
- All **eight existing equation bodies**, **ten existing table bodies** and the
  citation-key set remain unchanged from `1fcbcc5`. There is one added table.
  All six pre-existing figure PDFs remain byte-unchanged; all seven current
  figure PDFs reproduce byte for byte.
- Historical evidence audit: **2,902 checks, zero failures**, with the same two
  existing acknowledgements. This audit does not register responsiveness v2;
  the new compact replay does not replace that study's full archive checks.
- Warning-free 25-page PDF build and inspection of every page by the review
  team. Remaining paragraph/float interruptions are recorded in round 2 and
  addressed in the final layout pass.

No image collection, transport request, feature extraction or paid API call is
part of this revision. Frozen scientific code, protocols, ledgers and numerical
evidence remain unchanged. The user-owned Korean source and PDF are preserved.
