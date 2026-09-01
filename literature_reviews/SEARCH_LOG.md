# Search log

All dates use Asia/Seoul calendar dates. Counts describe returned or screened records, not
independent studies. Duplicate preprints and versions of record are reconciled in the evidence
matrix.

| Date | Source | Query or traversal | Result handling |
|---|---|---|---|
| 2026-09-01 | Existing repository bibliography and frozen source evidence | Reviewed `docs/REFERENCES.md`, `docs/SOURCE_METHOD_MATRIX.md`, `docs/FAILURE_INVESTIGATION.md`, the Kim et al. paper/supplement, and exact source revision `7da12358cf34dad2184f357a048c2cf114b3c4e0` | Seeded anchor set; historical project interpretations are treated as leads and rechecked against primary sources |
| 2026-09-01 | Web search | `computational analysis paintings visual features color texture composition entropy artist attribution primary research papers` | Screened for primary quantitative-art and measurement papers |
| 2026-09-01 | Web search | `digitized paintings feature robustness resolution compression color management museum image computational art history paper` | Screened for reproduction, source-domain, and robustness evidence |
| 2026-09-01 | Web search | `artistic style similarity evaluation diffusion models artist style metric paper CLIP DINO CSD ArtFID` | Screened for generative-style and learned-metric evidence |
| 2026-09-01 | Web search | `painting representation learning artist style classification dataset CLIP DINO art primary paper` | Screened for learned representations and dataset designs |
| 2026-09-01 | OpenAlex | `computational analysis painting features artist style`, years 1990-2026, top 50 by relevance | Title/identifier screening; candidates moved to primary-source verification |
| 2026-09-01 | OpenAlex | `painting image entropy color texture composition art history`, years 1990-2026, top 50 by relevance | Title/identifier screening; candidates moved to primary-source verification |

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
| 2026-09-01 | Final four-cluster saturation search | 2025–2026 painter style similarity metric generated art; computational painting features; artwork digitization reproducibility; human perception of painter style | Screened the full returned result pages; added four decision-relevant 2025 studies while the other eligible hits duplicated existing anchors or remained background |
| 2026-09-01 | Identifier reconciliation | DOI, publisher, repository, and version checks for every retained evidence-matrix row | Final matrix contains 138 unique records; exact variants were merged and inaccessible or abstract-only depth was labeled rather than inferred |

The final saturation pass added four records (2.9% of the 138-record matrix) and no new method
family, satisfying the prespecified less-than-10% stopping rule. This is a broad structured
review, not a claim of exhaustive coverage of an open and rapidly changing literature.

Later passes append rows; previous searches are never rewritten to imply prospective coverage
that did not occur.

## Protocol deviation and count boundary

The search interfaces used for several web passes did not expose a stable export or total-result
count, and the contemporaneous log recorded the query and handling rather than a numeric count for
every returned page. A defensible total number of title/abstract hits screened therefore cannot
be reconstructed and is not invented retrospectively. The auditable included counts are 138
structured evidence records and 201 unique bibliography entries. Future updates
should use exportable search APIs or save result manifests if a PRISMA-style screened-total claim
is intended.

This is a deviation from the protocol's intended per-query result-count field. It does not change
the stopping rule: the recorded final saturation pass added four decision-relevant records and no
method family.
