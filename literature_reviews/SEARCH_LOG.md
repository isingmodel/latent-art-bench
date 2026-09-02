# Search log

All dates use Asia/Seoul calendar dates. This table is a retrospective reconstruction of the
2026-09-01 review session from retained notes, included records, and source history; it is not a
contemporaneous export-backed screening ledger or a preregistration. The strings shown for the
first search passes are recorded query strings, while several later entries summarize grouped
exact-title, DOI, citation-chaining, and publisher traversals rather than one reproducible query.
No complete result-page snapshots, search exports, deduplicated candidate manifest, per-record
screening ledger, or exclusion-reason manifest was saved. Consequently, returned and screened
counts cannot be reconstructed. Duplicate preprints and versions of record were reconciled in the
evidence matrix, but the path from every viewed result to its final disposition is not auditable.

| Date | Source | Recorded query or reconstructed traversal | Result handling |
|---|---|---|---|
| 2026-09-01 | Existing repository bibliography and frozen source evidence | Reviewed `docs/old/REFERENCES.md`, `docs/old/SOURCE_METHOD_MATRIX.md`, `docs/old/FAILURE_INVESTIGATION.md`, the Kim et al. paper/supplement, and exact source revision `7da12358cf34dad2184f357a048c2cf114b3c4e0` | Seeded anchor set; historical project interpretations are treated as leads and rechecked against primary sources |
| 2026-09-01 | Web search | `computational analysis paintings visual features color texture composition entropy artist attribution primary research papers` | Screened for primary quantitative-art and measurement papers |
| 2026-09-01 | Web search | `digitized paintings feature robustness resolution compression color management museum image computational art history paper` | Screened for reproduction, source-domain, and robustness evidence |
| 2026-09-01 | Web search | `artistic style similarity evaluation diffusion models artist style metric paper CLIP DINO CSD ArtFID` | Screened for generative-style and learned-metric evidence |
| 2026-09-01 | Web search | `painting representation learning artist style classification dataset CLIP DINO art primary paper` | Screened for learned representations and dataset designs |
| 2026-09-01 | OpenAlex | `computational analysis painting features artist style`, years 1990-2026, nominal retrieval cap 50 by relevance | Title/identifier screening; no result export was retained, so 50 is an API/request cap rather than a verified screened count |
| 2026-09-01 | OpenAlex | `painting image entropy color texture composition art history`, years 1990-2026, nominal retrieval cap 50 by relevance | Title/identifier screening; no result export was retained, so 50 is an API/request cap rather than a verified screened count |
| 2026-09-01 | Frozen Pilot 2 records | Read the Pilot 2 protocol, failure investigation, report, analysis, chromatic secondary report, and qualification evidence | Reconstructed the exact painter target, real atlas, source probe, cross-source results, PCA geometry, registered prompt contrasts, missing grid, and claim boundary |
| 2026-09-01 | PNAS, PMC, supplement, and exact GitHub revision | Exact-title/DOI search for Kim et al. (2026); inspected paper, supplement, and repository revision 7da12358cf34dad2184f357a048c2cf114b3c4e0 | Audited 72,447-work corpus, A/C preprocessing, tensor dimensions, stochasticity, validation splits, released-code defects, absent hashes/fixtures, and claims |
| 2026-09-01 | Web search and citation chaining | painting color distribution chromatic distance CIELAB artist; painting ordinal pattern entropy complexity; exact DOI/title queries from Kim (2014), Lee (2018), Sigaki (2018), and Lee (2020) | Verified primary color, ordinal, entropy, and information-theoretic methods; reconciled versions and removed duplicate preprints |
| 2026-09-01 | Web search and citation chaining | painting Fourier spectrum edge orientation PHOG wavelet visual stylometry brushstroke; exact-title/DOI searches | Verified spatial-frequency, edge, wavelet, stylometry, technical-imaging, and falsification sources; physical-surface papers retained only as modality boundaries |
| 2026-09-01 | Web search | painting composition saliency visual balance rule of thirds eye tracking primary study | Verified composition and perception studies; universal-rule claims downgraded or rejected |
| 2026-09-01 | Official standards and publisher sources | ISO 19264-1 cultural heritage imaging; FADGI 2023 technical guidelines; Metamorfoze 2025; painting digitization ICC color management reproduction | Inspected official standard/guideline records and primary color-reproduction studies; translated capture requirements into reproduction and provenance gates |
| 2026-09-01 | CVF, ECCV, ICLR, arXiv, and exact repositories | art style embedding painter retrieval CSD ALADIN ArtFID CLIP DINO diffusion style metric; exact CSD paper/repository and CSD+ searches | Audited training data, supervision, split units, human tasks, checkpoint status, cosine calibration, and painter-coverage evidence |
| 2026-09-01 | CVF, USENIX, NeurIPS, and ICLR | diffusion memorization art copying artist prompt training data attribution SSCD | Kept exact/near-copy, extraction, prompt-risk, local-memorization, and attribution methods as a separate audit layer rather than painter similarity |
| 2026-09-01 | JMLR, PMLR, NeurIPS, CVF, and OpenReview | FID KID MMD precision recall density coverage conditional MMD metric bias sample size | Verified set-level estimators, finite-sample failures, encoder dependence, and precision/coverage decomposition |
| 2026-09-01 | PubMed/PMC, Journal of Vision, Nature, and psychometrics sources | human artistic style similarity judgment triplet painting expertise content control; exact DOI/title searches | Verified style-perception, expert/nonexpert, comparative-judgment, and construct-validity evidence; separated painterly manner, content, affect, and preference |
| 2026-09-01 | Statistics and research-design citation chaining | crossed random effects bootstrap exchangeability blocks missing outcomes preregistration registered reports | Verified work/rater dependence, blocked permutation, missingness, intent-to-generate, and prospective freeze sources |
| 2026-09-01 | Final four-cluster stopping pass | 2025–2026 painter style similarity metric generated art; computational painting features; artwork digitization reproducibility; human perception of painter style | Reviewed the result pages visible in the session and retained four decision-relevant 2025 studies; no export or page snapshot was saved, so completeness of the returned set and dispositions of all other viewed hits cannot be reverified |
| 2026-09-01 | Identifier reconciliation | DOI-keyed title, author, year, and method-summary cross-check between the evidence matrix, bibliography, review tables, publisher pages, and primary full text where needed | All 102 DOI-keyed matrix records join to a bibliography item after correction; the matrix remains 138 unique records, and inaccessible or abstract-only depth remains explicitly labeled rather than inferred |

The final pass added four records, which is 2.9% of the final 138-record matrix, and no new method
family was recorded. This is a descriptive retrospective calculation. It does **not** demonstrate
that a less-than-10% rule was prespecified or that literature saturation was reached because the
protocol was not demonstrably frozen before searching, the denominator was not independently
frozen before the pass, and the search and screening manifests are missing. The defensible claim
is broad structured coverage of the reviewed sources, not exhaustive or saturated coverage of an
open and rapidly changing literature.

Future passes must append dated records and retained manifests; previous searches must not be
rewritten to imply prospective coverage that did not occur.

## Count and audit boundary

The search interfaces used for several web passes did not expose a stable export or total-result
count. More importantly, no complete result manifests or record-level screening ledger was
retained. A defensible total number of title/abstract hits returned, deduplicated, screened,
excluded, or assessed in full text therefore cannot be reconstructed and is not invented
retrospectively. The auditable endpoint counts are 138 unique structured evidence records and 201
unique bibliography entries; they are included-source counts, not a PRISMA flow.

Because `SEARCH_PROTOCOL.md` was itself structured during the relaunch rather than demonstrably
registered in advance, this limitation is not characterized as a deviation from a prespecified
protocol. Future updates must use exportable search APIs or save result manifests and screening
decisions if they intend to report screened totals, exclusions, saturation, or prospective
adherence.
