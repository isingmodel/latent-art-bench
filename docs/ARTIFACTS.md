# Artifact retention

Git contains compact scientific records and editable writing. Large local media
and some bound intermediate files are ignored. Ignore status does not establish
that a file can be deleted.

## Current writing and code organization

`paper/` contains the sole current manuscript, bibliography, plotting script and
three manuscript figures. These are editable presentation artifacts. Superseded
manuscripts and documentation snapshots live in Git history rather than duplicate
working-tree directories. For example, historical methodology-review citations
to the earlier paper can be resolved with:

```bash
git show 52fa1d6:papers/painter_distribution_study_v1/paper.tex
```

The [analysis map](ANALYSES.md) connects every study to its computation, plotting,
inputs, methods and replay command. Scientific packages remain versioned at
recorded paths. Rearranging a frozen package merely to shorten its name would
break the evidence's path identities.

## Preserve terminal scientific evidence

| Location | What is retained |
|---|---|
| `studies/` | Protocols, amendments, inference contracts and fixed validation/literature plans |
| `configs/` | Settings and inventories used by completed stages |
| `data/manifests/` | Freezes, input hashes, requests, append-only ledgers, metadata, measured vectors and result receipts |
| `reports/` | Published numerical results, memberships, tables, plots and provenance |
| `src/latent_art_bench/` and `tests/` | The implementations and tests that produced or qualified those results |
| `scripts/` | Historical bound launchers and compatibility entry points |
| `docs/reviews/20260907_methodology/` | Historical methodology review; the aggregate revision plan is a bound analysis input |
| `literature_reviews/` | Retained bibliography, evidence matrix, search audit and thematic reviews |

Do not rewrite, move, truncate, reorder or regenerate a terminal protocol, report,
ledger, receipt, bound source file or fixed review. Corrections require a successor
scope. Do not resume a closed collector or replace failed records in place.
Mutable status belongs in [STATUS.md](STATUS.md), not in old protocols.

Evidence verification resolves inputs at their recorded Git commits and verifies
local research bytes in place. Never refresh hashes to make an audit pass.
Exactly two historical unrecoverable inputs are recorded in
`data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json`;
that list must not be extended to conceal new damage.

## Preserve ignored research bytes

- `research_workspace/`: source image responses, full-resolution generated
  images, compressed transport bodies, failed requests and one-shot execution
  locks. Failures and pilot responses can be unique evidence even when excluded
  from scientific endpoints.
- `artifacts/models/` and `artifacts/sources/`: retained weights and source
  checkouts. Git does not back them up.
- `tmp/pdfs/`: retained literature PDFs, author sources and extracted text;
  `tmp/pdfs/kim2026/published.txt` is cited by a frozen literature comparison.
- Hash-bound calibration/randomization JSON and other referenced files under
  `tmp/`: a temporary-looking path does not make evidence disposable.
- Untracked user work and local configuration, including `.env`.

The new responsiveness workspace also retains hash-bound normalized reference
displays. Future human plans, exact submitted exports and free-text responses must
remain private under that ignored boundary; public scientific receipts contain
only deidentified summaries and hashes. Technical previews are not human results.
Do not overwrite pilot or validation session paths to change their interpretation.

The computational v2 workspace retains compressed response bodies for every attempt,
including technical errors, and its one-shot collection/measurement markers. Tracked
v2 manifests bind these raw responses and all 192 planned slots. Diagnostic JSON
also preserves normalized query, split and prediction identities; its size does not
make it a disposable report cache.

Before machine migration or deletion of unique local material, create a separate
checksum inventory and archive. No broad recursive deletion under `artifacts/`,
`data/`, `research_workspace/` or `tmp/pdfs/`; never use `git clean -xfd`.

## Disposable build state

Known manuscript builds, rendered-page previews and numeric report previews are
reproducible from retained sources. Current paper intermediates belong under
`tmp/paper/`. Python test/lint caches, bytecode and operating-system metadata are
also disposable when unused. Remove only inspected exact targets; do not infer
that an entire ignored directory is safe from its name. In particular, execution
locks and bound temporary JSON files must remain untouched.
