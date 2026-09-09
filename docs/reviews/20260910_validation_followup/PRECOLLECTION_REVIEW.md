# Bounded pre-collection replication review

Date: 2026-09-10 (maintainer's Korean calendar date). Reviewer: academic reviewer 1,
a maintainer-run LLM subagent. This is an implementation/design review, not external
peer review, institutional independence, or empirical validation of the service.
The reviewer also designed and implemented the separate computational-measurement
successor. No new replication outcomes were inspected and no live request was made
by this reviewer.

## Scope and disposition

Read the complete new protocol, allocation and endpoint metadata, all six package
modules, and the complete offline test file. Checked assignment identity, shared
controls, weighted energy, palette covariance/multiplicity, transport ordering,
retry/accounting stops, committed-before-outcome gates and replay boundaries.

**No outstanding must-fix finding in the version hashed below.** It is ready for
the coordinator's source commit and prospective preparation/freeze sequence.
This finding does not waive live metadata, credit, proxy/runtime, disk or committed
freeze checks. No collection is authorized merely by this review record.

Metadata-only reconstruction found 264 unique slots in 48 complete blocks:
72 FLUX outputs (24 shared-free/Monet/Cézanne triplets) and 192 OAuth palette
outputs. Each naming arm has eight briefs in each of the three content classes.
The palette schedule passes the unchanged factorial design validator.

## Findings and resolutions

| Finding | Resolution checked before collection |
| --- | --- |
| Concurrent workers could acquire the original unticketed start gate in a different order from the frozen assignment. | Coordinator-issued dispatch tickets now order admission, including retries. An adversarial test starts the later-ticket worker first and verifies ordered admission timestamps and spacing; cancellation and deadline tests also pass. Server-side execution order remains outside this guarantee. |
| Live configuration accepted four naming repetitions despite the selected one-repetition, 264-slot protocol. | Live configuration now requires exactly one repetition. A larger inventory remains accessible only to the pure offline builder/test; the live configuration rejection test passes. |
| The source inventory omitted the shared `painter_feature_generation_v1/panel.py` dependency. | The missing source path is included in the prospective bindings. |
| A queued retry was counted as a retry even if a subsequent halt prevented its POST. | Receipts distinguish retry decisions, dispatched retry intents, actual retry POSTs and total posted attempts. An event-synchronized error/stop test verifies one queued retry and zero executed retries. The first version of that test raced and failed because a retry actually dispatched; synchronization was repaired without weakening the accounting expectation. |
| A fully measured grid could otherwise retain primary claims after drainage exceeded the fixed duration. | Dispatch stops five minutes before the deadline; the receipt records actual duration. `apply_collection_scope` propagates duration failure to both measurement and replay, withholding top-level primary p-values, intervals, rejection and directional-replication flags while retaining descriptive estimates. |

Additional checks support the final design: durable paid reservations retain
unknown-cost amounts; actual credit admission is separate from the cumulative
$75 accounting ceiling; recognized retries are bounded and payload-preserving;
slot receipts preserve all planned denominators and first-valid-output identities.
The naming tests share the same free images without treating them as independent
controls, and Holm handles dependence across the four primary comparisons. The
direct weighted-energy oracle agrees with the paired-contribution calculation.
The palette code preserves shared-control covariance and allocates 98.75% marginal
intervals to its two effects within the four-endpoint family. Nested unchanged
primitive results are explicitly labeled diagnostics; only the scoped top-level
primary records declare successor inference.

## Verification

The reviewer's final independent run passed **33 tests in 6.48 seconds**, after the
last diagnostic-label changes. Namespace Ruff passed. Tests include the complete
264-slot mocked collection → measurement → analysis → numeric/raw/pixel replay,
missing-grid withholding, identity tampering, conservative accounting, actual
credit shortfall, ordered admission, selected allocation, deadline and retry-stop
cases. These use artificial images and mocked HTTP, not real service outcomes.
The coordinator remains responsible for the repository-wide suite and evidence
audit before handoff.

Runtime convention: the measurement successor freezes imported module versions;
the replication environment records installed distribution metadata. The
coordinator checked that this environment reports PyWavelets distribution 1.9.0
but `pywt.__version__` 1.8.0 in the same process. Each verifier consistently uses
its declared convention; this difference alone is not observed runtime drift.
Compare conventions when presenting receipts, rather than equating their strings.

## Remaining scientific limits

This is one fresh maintainer-run collection, not a sample of independent dates,
institutions or known backend states. The hidden OAuth snapshot remains unverified.
Naming has only one output per brief/arm; the smaller sample and shared controls
change finite-sample V-energy behavior relative to the old 72-output cells.
Old/new effect sizes therefore are descriptive comparisons. Randomization relies
on the stated availability and no-interference conditions; palette uncertainty
retains its repeat-block independence and approximate distributional assumptions.
The 31 features, exposed reference panel and capture/geometry limitations remain.
No human-perceived style or independent-capture validity is established, and local
replay does not establish public reproducibility. Missing outcomes or failed
controls cannot be rescued by dropping images or changing the primary family.

## Exact reviewed file versions

SHA-256 values cover the final stable files inspected and tested. Paths are
repository-relative. Shared historical dependency hashes belong in the subsequent
prospective freeze; these are the new files specifically covered by this review.

```text
584adb7794b111991ff311dd5540e7c48faa6eddef98c76f4092d806eea5ca03  src/latent_art_bench/painter_naming_replication_v1/__init__.py
ee456b463b140f890d5bab8145a3fa133260108dc04f64b6f72a4b3d043393c6  src/latent_art_bench/painter_naming_replication_v1/__main__.py
a6d2c535d9d554e1a0ea626c36dbaa91f4386d795f1dc781df7cb39c89313c32  src/latent_art_bench/painter_naming_replication_v1/analysis.py
a3f0459264d4bb75cbbad47a4b3f1b3ec51d900dbdeafbc780caeba3f85d1907  src/latent_art_bench/painter_naming_replication_v1/collection.py
0396169bd60dec27050830445f841f9cc9b11e4becb599362810ec7de00a1c37  src/latent_art_bench/painter_naming_replication_v1/common.py
472e166b3e3cb85934f7b75a93fa88246dc00c22cdfad25011db9916f4f7c137  src/latent_art_bench/painter_naming_replication_v1/workflow.py
c352a3bac3489784c987d65d0d3acd3f0c4141da61624abea06ca71ba8504054  studies/painter_naming_replication_v1/PROTOCOL.md
aff9ff42694085830b576987f4a583efd501784b69912063c894b5ef2a23ea20  studies/painter_naming_replication_v1/endpoint_metadata.json
ee74d96a8064c5ddcd0299941221a9ebd9eddf0585ad49c0a4522a5d69eb49d0  studies/painter_naming_replication_v1/study.json
207f33361d5ec0c8322d59ec357f1a092a02cee1575f96d340f7b1d3aa7fc773  tests/painter_naming_replication_v1/test_replication.py
```
