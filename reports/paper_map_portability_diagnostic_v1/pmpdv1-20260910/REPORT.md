# Separate Ubuntu portability diagnostic: authenticated result

The distinct [diagnostic run 34479252271, attempt 1](https://github.com/isingmodel/latent-art-bench/actions/runs/34479252271)
completed and retained every comparison. **Its qualification comparison fails
only at the 27 reconstructed-support hashes. Its separately reached observed
analysis differs in floating-point values and fails the unchanged exact
JSON/report contract.** All differing numeric leaves are within the existing
1e−10 absolute/relative comparison. The scientific table is unchanged at its
published precision.

This is not a pass or rerun of the
[closed strict attempt](../../paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md).
That earlier attempt remains failed and never reached observed E/Q replay.
The new diagnostic supplies the missing comparison detail; its successful
execution status does not mean strict numerical agreement or a portability
repair.

## Actual identity and execution

The new workflow used sanitized branch
codex/diagnostic-pmpdv1-20260910 at commit
0cc7b64816cf59285ccfb740e639a5a07406a95b, through the registered reproduce.yml
dispatch entry point. API metadata records workflow_dispatch, attempt 1 and
successful diagnostic completion. The hosted driver ran from
2026-09-10T12:53:18.579921 to 12:53:46.072408 UTC; its numerical diagnostic
command took **21.024544 seconds**. All seven recorded commands returned zero:
pre-install verification, uv installation/version, locked dependency installation,
runtime reporting, diagnosis and final inventory. No public-test rerun was
performed in this diagnostic.

The archive remains pmv2r-20260910: **74 regular files, 3,059,166 bytes**, SHA256
8688085fe001e6b45ca34f6d39a5979e3e762a2678cd5ecb8169a698defb4eb6.
The frozen checker and all scientific inputs are unchanged. Python -I -S
verification preceded scientific imports; the exterior diagnostic used -I -B.
It reconstructed the same 27 qualification cells/270,000 deterministic trials
once in memory, then independently invoked the unchanged observed analysis.
No formal qualification output writer, new law, seed, target or allocation was
introduced.

Ubuntu 24.04.5 image 20260907.300.1 reported Linux x86_64, glibc 2.39,
CPython **3.13.11**, NumPy **2.5.2**, SciPy **1.18.1** and
OpenBLAS **0.3.34.0.0**. The retained [local diagnostic](LOCAL.json) records
exact qualification and observed JSON/report agreement on the Mac arm64 /
Apple Accelerate runtime, with the same package versions and diagnostic source.
These runtime differences provide context; this audit does not identify a
particular BLAS, eigensolver, SIMD or rounding operation as the cause.

## Complete saved-object comparison

I independently traversed both saved objects against the exact expected JSON
inside the authenticated original archive, without importing any scientific or
diagnostic production module. All container keys, list lengths/order positions
and leaf types agree. Every reported differing pointer/value and original
comparison disposition agrees with the separate traversal.

| Saved reconstruction | Leaves checked | Strict qualification-comparator failures | Other exact floating differences | Maximum absolute numeric difference |
| --- | ---: | ---: | ---: | ---: |
| Qualification | 764 | 27, all support hashes | 211, all tolerated | 3.552713678800501e−15 |
| Observed analysis | 955 | 0 under the supplemental 1e−10 comparison | 156, all tolerated | 2.6645352591003757e−15 |

The 27 failing qualification paths are exactly
/records/0/support_sha256 through /records/26/support_sha256, one in every law.
There are no differing integer counts, identities, seeds, availability flags,
allocation decisions or other nonfloating values apart from those hashes.
The largest qualification numeric difference is the Q median half-width in
record 16. The stored qualification report renders exactly. The comparison
therefore still fails its existing exact support-identity requirement even
though every numerical result passes its specified tolerance.

For the observed phase, **exact JSON=false and exact report=false**. Its
supplemental floating comparison is diagnostic only; that comparison cannot
satisfy the old exact observed contract. The largest absolute differences occur
in two stored paired-deletion Q estimates and the upper Q interval endpoint.
All other fields agree exactly, including the two negative directions and
resolved_other_ordering interpretation.

The entire displayed scientific table in the Markdown report is byte-identical:

| Endpoint | T2−T1 | Approximate simultaneous interval |
| --- | ---: | --- |
| deltaE | −0.390186879 | [−0.509032897, −0.271340860] |
| deltaQ | −5.046510453 | [−7.879516972, −2.213503934] |

The sole changed report line is the full-precision JSON display of component
point values. All observed floating fields also retain the same three-decimal
display, covering the manuscript's presentation precision. No scientific table,
decision, interval procedure or retained published number is amended here.

This localizes the failure sites in **this new diagnostic**. The original
strict attempt did not retain its reconstructed object, so its individual
leaves cannot be authenticated retrospectively. The same archive and reported
runtime family make the new result relevant to that failure, but do not recover
the discarded original object or prove the cause of each altered support bit.
No remedy or changed comparison threshold is selected by this report.

## Receipt, log and payload authentication

[HOSTED.json](HOSTED.json) and
[HOSTED_DIAGNOSTIC.json](HOSTED_DIAGNOSTIC.json) are byte-for-byte copies of
the actual hosted wrapper receipt and its nested diagnostic RECEIPT.json.
The latter binds all seven diagnostic output bodies. I verified:

- API run/head/branch/attempt identity, artifact ID **10152870944**, and the
  artifact's **49,967-byte** ZIP against both the API digest and upload log.
- All **24** artifact files against their ZIP bodies, all **14** command
  stdout/stderr hashes, all **seven** diagnostic output hashes and the nested
  receipt hash.
- Equality between HOSTED.json and the full receipt printed in the job log;
  the 187-line executed Python driver body matches the committed workflow body.
- Every one of the **74** input hashes against the original local archive,
  the same input inventory in LOCAL.json, and all **32** loaded module bindings
  before/after replay. The hosted pre/post inventory phases report all 74
  payload files verified and unchanged.
- Every saved comparison leaf, the generated report diff, and the scientific
  table's byte equality. The verification script reads saved public objects
  only; it does not repeat qualification or observed numerical computation.

The full logs, API snapshots, ZIP and complete reconstructed objects remain under
the ignored directory
tmp/paper-map-validation-release/portability-diagnostic-20260910/hosted-01/.
The small independent saved-object audit is retained there as audit_2.py and
audit_2.json. Source inputs, diagnostic outputs and both old failure receipts
were preserved.

## Scope and involvement

This is a maintainer-run LLM audit by reviewer 2. I contributed earlier
geometry/centering and operational study implementations, reviewed the numerical
exporter and diagnostic design/code, and performed the earlier local/strict
hosted audits. The coordinator dispatched this diagnostic; reviewer 1
implemented its tool and artificial tests. I was informed of its summarized
differences before independently checking the saved objects. This is not
independent human or institutional replication.

I did not dispatch, rerun, repair or cancel a workflow; change scientific
source/tolerances; generate or decode images; extract features; rerun a formal
qualification; or assign a new paper score. Public numerical agreement cannot
authenticate absent acquisition pixels, provider identity, private cost/timing
facts, capture validity or actual-service interval coverage. The historical
strict failure and original studies remain closed.

| Retained item | SHA256 |
| --- | --- |
| LOCAL.json | b9306bfe6f5f190dbfcba797ea915789339442c81736866af44a022a5092e3b9 |
| HOSTED.json | 9b1981c5affa45f8c2102676ef5a7e2eebd93ac0df89c40262249eac834a5272 |
| HOSTED_DIAGNOSTIC.json | 3ddabed2614bb70c97cedf8c5657b532997fde52fb369e480904b397179804b5 |
| Artifact ZIP | 3a0dffa3df73ed26fdbcec2f023194d2111c65f5c1a51cf9e53e7337407c1f35 |
| Diagnostic source | 827820d1039aa42376053a8b598d11a697df28f7f97f0e98c9e2e4a1b1f43042 |
| Workflow source | cbe2506cd848991f27d24155a993e50ca0a4371eff4920a07ada3dacfc1b8c3e |
| Full job log | 0f7067a51e0b07a0978e8376a532800b416dd6e106e22fd06274c509470c3280 |
| Qualification actual JSON | 43ad6c411d3c6a524d9ab95d9d2afd14179c02a3fc89a3e0674d53dc0ddbaf5e |
| Qualification diff JSON | 0f01e8972f77a30b4dc9b3e3cf21334ffc09fb332da3a663c9f6dd83e23c1198 |
| Observed actual JSON | a312a356b3c5d4f4c14fd61c83f23f3f5724fcfacab9f674c2f5f1babc318171 |
| Observed supplemental diff JSON | 1ccbc948f051600705d9fec114d1c9d99a130aeba11ac35725be5e290a6e0b79 |
