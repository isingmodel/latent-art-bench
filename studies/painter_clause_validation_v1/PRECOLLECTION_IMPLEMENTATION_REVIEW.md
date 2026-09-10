# Precollection implementation review

Date: 2026-09-10. Reviewer: maintainer-run LLM subagent Reviewer 2.

## Conclusion and disclosure

I find no unresolved critical statistical or implementation defect in the
reviewed prospective 288-output contract after the corrections below. The source
is suitable for the coordinating maintainer's final qualification and committed
freeze workflow. This review does **not** open the live gate: the aggregate
qualification, clean source commitment, full offline suite/evidence checks,
prepared inventory/freeze and its separate commitment remain required.

I separately examined Reviewer 1's precision implementation and the coordinating
maintainer's analysis/common modules. I implemented this successor's collector,
workflow and transport tests, and earlier implemented geometry and centering
primitives used by the paper. I also repaired collector defects identified in
this review and by other agents. My assessment is therefore not independent of
the implementation as a whole. All reviewers are LLM agents operated by the same
maintainer; this is not independent human or institutional review. No paper score
is assigned or revised here.

## Scope and verification

I read the complete current protocol, common/configuration and analysis source,
precision source and tests, and the relevant frozen energy/randomization,
measurement and variance primitives. I inspected the new compact inputs against
their retained numerical predecessor without extracting pixels or computing new
scientific outcomes. The new targets and all three scalers are exactly equal to
their predecessor objects; reference and original OAuth cells are exactly equal
in each of the three pipelines. Six historical maps are checked by the analysis
against their original generated-only weighted fits.

The following checks passed in this review:

- Namespace Ruff: clean.
- Combined namespace tests: **127 passed in 12.56 seconds**. This includes 33
  precision tests, 28 analysis tests and 66 collection/workflow tests.
- An artificial complete workflow returned 288 mocked image responses, retained
  all assigned slots, created 864 synthetic measurement rows, ran the real
  analysis/report code and reproduced both numerical and mocked-extraction
  pixel checks. Transport was `httpx.MockTransport`; extraction returned
  deterministic synthetic vectors. This is an integration test, not a new
  image-service experiment or validation of the real extractor's accuracy.
- A temporary Git repository exercised scientific-source commitment,
  qualification at an earlier exact source commit, later qualification/evidence
  commitment, preparation, rejection of an uncommitted freeze, successful
  verification after its separate commitment, and rejection of changed source.
  It never prepared the actual study run.
- The real retained budget-schema test preserves the recorded floating-point
  amount `50.72191850000009`. The gate compares it with the conventional config
  total `50.7219185` using absolute tolerance `1e-10`, relative tolerance zero;
  it rejects unresolved/pending states and nonzero new reserves. No receipt is
  rewritten to change its number or hash.
- A static local-import traversal found 64 reachable Python files; all were
  included in the 143-path source inventory then returned by
  `workflow.source_paths`. This includes the 31-feature extractor,
  normalization/measurement code, four-painter panel, energy/randomization,
  geometry/variance and response/retry helpers. The common binding inventory
  also includes the separate reviews, precision records, original geometry
  lineage, replication freeze/receipt and preceding main collection receipt.

The older budget chain retains provider-reported `40.681918500000066` and its
historical $5 reserve, giving `45.68191850000009`; the replication freeze retains
that exact baseline, and its terminal receipt adds $5.04. The new collector makes
only OAuth POST requests and does not read paid credentials, pricing or balances.
Subscription usage has no assigned monetary value.

## Statistical assessment

The 72 four-position blocks each contain free, generic, Monet and Cezanne once.
Within-block and block-order permutations are determined from the bound seed.
The prompt renderer inserts only the selected clause into the unchanged detailed
core. Generic/free outputs are shared by the two painter comparisons. Each
endpoint uses its own reference class masses, with weight `q_c/(8*3)` for every
generated observation and equal weights within its fixed reference panel.

For each primary test, conditioning on the positions of the other two arms
leaves two equally likely orientations of the compared labels in each block.
The retained weighted V-energy contrast has the exact paired-contribution sign
identity, including its within-generated terms. The primary calls use 99,999
Monte Carlo assignments, conservative absolute ties and the plus-one rule, with
the two separately bound seeds. Holm needs valid marginal p-values, not
independence of the two endpoints; sharing G is therefore compatible with this
two-test adjustment. The exact small four-position enumeration and direct
energy-versus-sign tests meaningfully check this conditional construction.

Completeness is endpoint-specific: a missing generic primary measurement
withholds both tests, a missing named measurement withholds its painter's test,
and an ordinary missing free measurement does not discard otherwise complete
named/generic pairs. The implementation does not renormalize a complete-case
subset. Unavailable endpoints enter Holm with p=1. Explicit successful duration
and global identity flags are additionally required; descriptive estimates are
retained when these global gates fail. No effect confidence interval or new
test of Q or transformed-vector superiority is introduced.

The added secondary fields now explicitly retain population-form observed
traces, reference-content G/F and N/G trace ratios, T2-minus-T1 differences in
both reference energy and conditional residual, and delivery metadata by arm.
Both equal-scene and reference-content conditional variance summaries are
available. Undefined ratios and negative corrected estimates are preserved.
Map reference energy remains available with complete free outputs even if its
named conditional-residual target is unavailable. The historical maps are fixed
before this cohort, so the earlier evaluation-mean dependence problem does not
apply: there is no T2c or fitting to these new free observations. The stated
repeat-error assumptions remain necessary for interpreting corrected Q/B/N.

## Precision and numerical qualification

The saved precision record binds commit
`6dd1e80b7d998f39809bfa354c8f52b7dd439595`. I verified all eight recorded bindings
against both current bytes and that commit. I did not rerun or overwrite its
create-once production calculation.

The proxy correctly pools six original free repeats per scene and centers named
residuals within painter before pooling. Scaling centered free residuals by
sqrt(6/5) and named residuals by sqrt(3/2) matches their empirical resampling
covariance to the corresponding unbiased sample covariance. A single hypothetical
generic draw is shared by both endpoints. The nine mean/noise scenarios and
three allocations are fixed; the 12-scene comparison uses one disclosed balanced
subset, not a selected best subset. The code reports scenario means as well as
SDs and does not use significance or an assumed desired effect to select 288.

For the selected 24-scene/three-repeat allocation, retained proxy SD ranges are
approximately .103–.150 for Monet and .089–.125 for Cezanne. These are conditional
empirical-proxy dispersion estimates, not confidence intervals, observed generic
variance, guaranteed power or uncertainty over new scenes. Holding noisy old
means fixed and resampling only six/three residuals omits uncertainty in that
law, service drift, carryover and most possible high-dimensional tails. The
report says this explicitly. The 288 allocation is a reasonable bounded
precision/coverage compromise; this calculation cannot certify its adequacy
for a meaningful effect that has not been specified.

The artificial randomization qualification fixes position outcomes before
random assignment, retains shared G, and includes complete and partial sharp
nulls, position drift and a rare large outcome. The five retained true-null
family-error rates are .0490, .0486, .0472, .0428 and .0446. Their Wilson upper
bounds are approximately .05534, .05491, .05343, .04877 and .05068, all below the
prespecified .065 numerical criterion. The bounded simulation uses 999 draws
per endpoint, whereas the primary uses 99,999; both implement the same
conservative plus-one/tie rule. This empirical check, supported by exact small
tests and comparison with frozen primitives, detects numerical mistakes. It
does not establish no interference or the sharp availability/feature null for
the actual service, and is not a proof of error control for all possible
service processes.

## Defects corrected before qualification

1. **Global identity gate:** analysis originally checked only duration/planned
   counts. A late source/process or contract failure could therefore leave a
   complete named/generic endpoint eligible. The collector also lacked a final
   source/process check after the last block drained. The protocol and source
   now require explicit global `identity_contract_met=true`, verified after
   drain and against terminal/operator evidence. Unknown/unsupported delivery,
   unrecognized backend errors, authentication/account/contract failures and
   interruptions conservatively invalidate both tests. Tests retain all
   successful outputs while withholding inference after a final-only identity
   failure.
2. **Ordered-stop replay:** Reviewer 1 found that a later identity-invalidating
   interruption following an earlier storage/deadline halt could change the
   receipt flag without recording its reason. A single first-transition
   `identity_contract_failure` event now preserves that reason without replacing
   the first halt. The retained-storage-halt → interruption → successful-final-
   checks test verifies that this stopped receipt remains replayable.
3. **Budget and retry boundaries:** a predecessor-schema/exact-float assumption
   would have rejected the valid retained accounting record; it now uses the
   actual schema and explicit numerical tolerance without altering evidence.
   A ninth needed retry now halts, while a successful eighth retry alone does
   not cancel remaining first attempts. Qualified second failures retain their
   slot and the completed-attempt cluster rule still applies.
4. **Cross-module test isolation:** the combined suite exposed a test that
   replaced `sys.modules` while the package's analysis attribute was already
   cached. It now patches the actual function. The complete 127-test namespace
   pass, rather than only separate file passes, verifies the correction.

## Remaining scope limits

This study still compares four authored clauses on one fixed scene panel and
requested OAuth service. It does not isolate physical capture effects, supply
independent institutions or backend dates, establish semantic adherence, validate
human-perceived style, or generalize the two controlled painter comparisons to
all four painters. A generic clause is a substantive actual comparator, but is
not matched to an artist name in information or constraint strength. Random
ordering does not eliminate treatment-dependent timing, retries or carryover.
None of these limits is concealed by the numerical qualification.

I ran no live request, actual-run preparation/freeze, feature extraction from
retained or new research images, repository-wide suite or historical evidence
audit in this review. The latter two checks and the final source/evidence
commitments are the coordinator's remaining stage gates. Review approval must
refer to the final bound source, not to this prose alone.
