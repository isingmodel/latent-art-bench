# Successor precollection method review

Recorded 2026-09-10 for `painter_clause_successor_v1/pcsv1-20260910`.
The fixed design was committed as `f0ab2d4`; this review examines the later
implementation snapshot identified below. It assigns no paper score and makes
no inference about unobserved successor results.

**Disposition:** no unresolved precollection methodological defect was found
at these bytes after the delivery-reporting correction described below. This
is evidence for source qualification, not a substitute for the required
predecessor terminal verification, full repository checks, committed
qualification/freeze, or explicit live admission.

## Role and scope

Reviewer 3 is a maintainer-run LLM agent who authored both clause protocols,
the predecessor scenes and the successor design decision, advised on manuscript
structure, and reviewed the predecessor implementation. The reviewer did not
implement the successor statistical or collection code. The calculations here
were performed separately from that implementation, but this is an involved
maintainer review, not independent human or institutional review. Reviewer 1
implements statistics and Reviewer 2 implements collection/workflow.

The review read the successor analysis, allocation and CLI, relevant terminal
and measurement workflow, statistical primitives and tests. It checked existing
reference/scaler inputs and prompt text, but did not inspect prospective image
pixels, extract features, read either new cohort's numerical outcomes, or make
live requests. All new numerical probes used artificial vectors. The known
predecessor refusal is an availability outcome; this review does not describe
the successor decision as wholly outcome-blind.

## Contract and numerical checks

- **Unchanged frame and fresh allocation.** All 96 prompts match the fixed
  ASCII construction and corresponding predecessor payloads exactly, including
  `Paul Cezanne` and the refused `pcv_built04` brief. All 24 scene IDs and their
  classes remain, with eight scenes per class, two repeats and two arms. There
  are 48 complete two-position blocks and disjoint successor request IDs. The
  seeded allocation is reproducible; independent position randomization does
  not require equal realized counts of first positions.
- **Exact retained numerical inputs.** All three successor Cezanne reference
  objects, each containing 32 vectors of 31 coordinates, equal their
  predecessor objects. Complete scaler objects and class masses also match,
  and the origin SHA256 verifies. The added runtime lineage gate checks the
  exact source projection, including metadata and numeric types, during prepare
  and verify. No scaler fit, reference substitution or new reference extraction
  enters this successor.
- **Primary statistic and weights.** Each reference receives 1/32; each
  generated observation receives its class mass divided by 16. The 48 pair
  weights sum to one. A separately calculated full V-energy difference agreed
  with the reported C-minus-G coefficient sum within `4.69e-16`. Recalculating
  the two weighted clouds after 100 arbitrary 48-pair swaps agreed with the
  corresponding signed coefficient sums within `3.81e-15`. Both within-cloud
  terms are retained; the statistic is not a mean-distance surrogate.
- **Randomization and decision.** The available primary uses 48 coefficients,
  exactly 99,999 Monte Carlo signs, seed `2026091052`, absolute two-sided
  extremeness, conservative numerical ties and the plus-one correction.
  Direct probes verified rejection at `.025` and non-rejection at `.02501`.
  The test module additionally checks exact small-pair swap enumeration,
  replay of the 48-pair Monte Carlo stream, and the finite sign/convolution law
  for constant, content-weighted, rare-large and zero coefficients. These are
  arithmetic checks under the stipulated sign law, not realized-service power
  calculations or validation of the availability-trigger conditioning.
- **Eligibility.** Missing either arm's primary measurement withholds the
  allocated-grid estimate and inference without complete-case renormalization.
  A missing nonprimary pipeline does not remove a complete primary endpoint.
  Separate probes of eight false/nonboolean duration or identity values retain
  a complete estimate only descriptively, with no p-value or rejection.
  Terminal tests cover final identity failures, refused outputs and complete
  slot accounting; the analysis cannot restore inference from a secondary
  pipeline. The CLI rejects collection without the required proxy argument
  and explicit live flag before attempting the operational gates.
- **Narrow secondary scope.** Independent calculations agree with all six
  arm summaries' observed population-form traces and generated/reference
  ratios, and all three C/G trace ratios. Complete-arm and positive-denominator
  rules are implemented, including explicit zero-denominator status. There
  are no new maps, Q, retrieval, conditional-variance corrections, feature
  deletion grids, palette tests, intervals or secondary hypothesis tests.

## Defect found and final verification

The initial successor analysis retained delivery fields in measurement rows but
omitted the protocol-required summary by arm. This was a material reporting
gap because dimensions and reported quality are retained service outcomes.
Reviewer 1 added JSON and report summaries of status, dimensions, format and
reported quality, counting primary-pipeline rows once per allocated output.
The final regression verifies 48 outputs per arm, avoids counting three
pipelines as three deliveries, and leaves the scientific primary unchanged
when metadata changes. The omission is resolved at the hashes below.

The final workflow also requires exactly the four measurement-receipt output
paths and checks the terminal zero-paid budget against the ledger-derived
state. Artificial workflow tests reject omitted/duplicated measurement bindings
and altered budget fields. These checks strengthen evidence verification without
changing allocation, weights, analysis scope or the alpha threshold.

The reviewer ran:

```text
uv run --locked pytest -q -m "not live" tests/painter_clause_successor_v1
144 passed in 14.89s

uv run --locked ruff check src/latent_art_bench/painter_clause_successor_v1 tests/painter_clause_successor_v1
All checks passed!
```

This includes the full 96-slot artificial collection/measurement/replay for
complete and missing-arm cases. It is not a claim that live qualification or
the full repository audit has already completed.

## Remaining scientific limits

The 96-output choice answers the already specified C/G question with a bounded
fresh cohort; no passing test demonstrates useful power. Two repeats and a
fixed authored scene panel do not establish a population effect, human
stylistic similarity or precise equivalence. The sharp null includes joint
availability/feature invariance and no interference; equality of energy alone
is insufficient, and complete observations do not prove these assumptions.

The two applicable `.025` levels yield a joint `.05` bound only when the
original Monet and successor Cezanne tests are conditionally valid, including
the availability-triggered choice. The union bound does not require independent
collections, but it does not establish service or selection validity. Original
Cezanne stays unavailable; no pooling, across-cohort painter comparison, isolated
time effect, alpha recycling or further replacement is justified. The report
must retain contrary, unresolved or unavailable outcomes as specified.

## Examined snapshot

All paths are repository-relative; these hashes identify this review's scope.

| Path | SHA256 |
| --- | --- |
| `studies/painter_clause_successor_v1/PROTOCOL.md` | `e8a556c8d4abfae50d153d584e4374f622939b241f7598d971ee396670df0080` |
| `studies/painter_clause_successor_v1/DESIGN_DECISION.md` | `57a9b4260bf1393b6a39d5e7fe880fb337d0eef7985dae16a584b94e4ab309e6` |
| `studies/painter_clause_successor_v1/study.json` | `f31ceb0d3dbaeffa4663f8613f5071254e64bd6a4bf086509ec67b40ded6dbf3` |
| `studies/painter_clause_successor_v1/inputs.json` | `948680079fa8646dc0088808b6aced037d9050680bae63eb5086cf4acb2665cc` |
| `src/latent_art_bench/painter_clause_successor_v1/analysis.py` | `cf40a3f92601bd3a1822964fad78b35b19b2a016d6db3000af11d5384b792e44` |
| `src/latent_art_bench/painter_clause_successor_v1/common.py` | `bd1c1bf25cb72b32aa928947952f60b092e1780a6ec00f9bfe53d3301ca701e9` |
| `src/latent_art_bench/painter_clause_successor_v1/__main__.py` | `3f36f3705e71d8684ed629720983ed61aadfc5f219358195e736b342fbedf7fa` |
| `src/latent_art_bench/painter_clause_successor_v1/workflow.py` | `5c7b1723b73ae4857411456785a06f490ad9c21c11fb91fccc07e00b159cb427` |
| `src/latent_art_bench/painter_clause_successor_v1/collection.py` | `cb03b96aeaa3fc15017be7749031266656d7c8c94ad6fcc415e6c626c7365766` |
| `tests/painter_clause_successor_v1/test_analysis.py` | `67c9cfacaead351bf87c46e9b6a7b0df7bb7d3f442992f2f368be67b320e1e43` |
| `tests/painter_clause_successor_v1/test_collection.py` | `19774bae84b6047070f87627994935f9830a72ad67fedeef86ad7ccb9d7d3340` |
