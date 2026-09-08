# Computational responsiveness: implementation review

The user explicitly requested continuation without human reference ratings on
2026-09-08. The resulting v2 study tests a deployed service's measured response to
six scenes and two color instructions. It preserves the earlier v1 scope and does
not manufacture human ratings, a perceptual threshold or reference qualification.

## Review provenance

Three maintainer-run LLM subagents reviewed the numerical design, retained-data
retrieval diagnostic, transport and publication workflow. The coordinator reviewed
the integrated implementation and documentation. These are maintainer-coordinated
LLM reviews, not independent human or institutional validation. Synthetic tests
check implementation behavior; they are not empirical support for the hypothesis.

## Findings resolved before prospective collection

| Finding | Resolution |
| --- | --- |
| A direct collector entry point could bypass recorded runtime-version verification. | The collector checks all recorded runtime keys and installed versions before admission. |
| Protocol prose omitted several implemented immediate stop conditions. | The prospective protocol now declares malformed/minimum-size delivery, authentication/quota/contract, retry-delay, storage and source/process failures. |
| Calling every negative interaction attenuation could hide failed controls or response reversal. | Classification requires positive free/generic control intervals and a positive named point response; the report preserves all estimates and qualifiers. |
| Shared generic outputs induce dependence between the two painter effects. | Factorial inference retains shared-control covariance, simultaneous intervals and the fixed two-endpoint multiplicity adjustment. |
| Missing slots could be obscured by available-output summaries. | All 192 slots and all three measurement rows per slot remain; any missing primary value withholds primary inference. |
| Geometry/quality filtering could select favorable post-request outputs. | Retain supported delivered images, record actual fields, and expose normalization failure without regeneration or adjustment. |
| Report replay could verify vectors while overlooking the collection that produced them. | Measurement binds the terminal ledger, slot inventory and retained attempt bytes; offline replay checks identities, costs, retries, numerical results and rendered report bytes. |

The retained-scene retrieval review checked exclusion of the held repetition from
every centroid, exact cross-pipeline identities, 24-scene and within-class candidate
sets, deterministic and fractional tie handling, and class-centered variance
summaries. No material train/test leakage was found. The coordinate scaler is the
old fixed development scaler and is never fitted to generated outcomes.

## Scientific limits retained

Two color instructions estimate a contrast, not a full response curve. A smaller
contrast may reflect shifted operating range or saturation as well as reduced
responsiveness. One generic painting clause is an imperfect semantic control for
painter naming. Randomized scheduling does not establish stable or independent
service errors; the small-repeat t approximation remains model based.

Scene retrieval measures distinguishability within this fixed feature space and
scene inventory. It does not measure whether the correct objects or composition
were painted. Uniform contraction can preserve retrieval, and improved retrieval
would weaken a claim that contraction itself means lost scene information.

The original-reference comparison uses an already exposed panel of digital
reproductions. Broad content classes were assigned by a maintainer-run LLM.
One-coordinate chroma overlap cannot establish artistic fidelity, oeuvre coverage,
content matching, capture equivalence or an explanation of the full 31-feature gap.
The experiment can provide a useful computational intervention while leaving those
questions unresolved.

## Live transport finding and prospective correction

The initial live run exposed an untested response form: a complete plain-text 503
proxy error was excluded by the JSON-envelope-only retry rule. The maintainer
terminated the allocation with 49 images, one technical failure and 142 unstarted
slots. Its data and ledger remain intact. Successful images had not been visually
reviewed and no scientific features had been extracted when the decision was made.

The separately versioned [correction](../../../studies/painter_responsiveness_recovery_v1/PROTOCOL.md)
recognizes only those exact 95 error bytes under complete 503/text/plain delivery.
It preserves raw responses, payloads, retry limits and scientific procedures. Thirteen
additional offline tests verify exact qualification, identical-payload retry,
negative cases and preservation of predecessor evidence. A fresh 192-slot run was
prospectively designated as primary; the predecessor remains ancillary. The full
suite passes 1,125 tests. This correction and its scientific scope received a
maintainer-run LLM review before the replacement's first request.

## Actual results and delivery review

The replacement completed 192/192 outputs without failures or retries. All 576
primary-run image/pipeline rows were measured. The predecessor's 49 outputs were
measured only after replacement collection became terminal; its primary inference
remains withheld and no images are pooled between runs. The retained-vector and
byte checks reproduce the nine diagnostic and 28 files in each experiment bundle.

Three maintainer-run LLM subagents reviewed the actual results with coordinator
checks. The statistical reviewer emphasized the substantial secondary
generic-minus-free contrast (−0.853) and both unresolved primary
painter-minus-generic effects. Monet's JPEG sensitivity narrowly crosses a
significance boundary while the primary pipeline does not; the report does not
promote that descriptive pipeline to confirmation. The numerical and visual
reviewer checked all 19 primary CSV tables against the sealed JSON and inspected
all four actual primary plots, finding no clipping or table discrepancies.

The transport reviewer independently verified all 242 response hashes and 241
unique embedded image hashes, without opening artwork pixels. The replacement's
minimum start spacing was 5.229 seconds, maximum concurrency two, and median
latency 27.309 seconds. No incremental OpenRouter spending occurred. All primary
outputs were nonsquare despite the square request; reported medium quality
occurred in 10/48 free, 4/48 generic, 3/48 Monet and 1/48 Cézanne images, with all
remaining outputs reporting low. The synthesis states these delivery differences
in its design and limitations and interprets the complete service response.

The scientific synthesis was revised to label the generic contrast as secondary,
identify the named arm behind each original-reference comparison, preserve the
retrieval counterexample and improved named-versus-generic chroma distances, and
avoid describing earlier prompted images as unprompted. The replacement reused
the same fixed dispatch order under a new collection identity. Reviews are LLM
reviews run by the maintainer, not independent human or institutional assessments.

## Descriptive quantile correction

Actual-result inspection also found a floating-point CDF boundary defect in the
frozen weighted empirical quantile routine. With 48 equal-weight observations
numbered 0 through 47, its median can be observation 24 instead of observation 23
under the declared inverse-CDF convention. This can move a mixture median across
the muted/vivid gap. Primary interactions, arm means and Wasserstein distances do
not use this quantile selection and are unaffected.

The original numerical/report bundles remain immutable and still replay their
recorded computation. A separately versioned, exact-rational-weight correction
identifies every changed quantile and dependent range-occupancy value and publishes
corrected reference-context displays. Replaying the original
bytes alone does not validate the original quantile convention. This review finding
remains visible alongside the corrected display in the scientific synthesis.

The [exact-weight corrigendum](../../../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md)
is now published from source commit `2062eab` and freeze `7380f80`. A second
maintainer-run LLM subagent independently reconstructed the rational CDFs before
publication and found the same 51 affected primary-run records and 15 ancillary
records. All changes concern medians; no actual 10th/90th percentile endpoints or
central-80 inclusion memberships change. Ten new offline tests cover exact
boundaries, unequal weights, missing strata, synthetic endpoint/coverage dependency
changes, protected results, commit bindings, immutability and byte replay. The
corrected numerical audit and all nine report files reproduce exactly.

The independent computational reconstruction matched every published before/after
triple, changed probability, member ID and rational weight in all 66 correction
records. Both corrected PNGs were visually checked and remained legible. The final
full offline suite passes **1,135 tests in 115.88 seconds**; Ruff passes. This
cross-check is another maintainer-run LLM review, not independent human validation.
