# Explicit refusal classification and remaining-slot continuation

Issued 2026-09-06 after the first staggered parallel census closed permanently.
This correction changes transport error classification; it does not change a
prompt, reference, feature, scientific endpoint or spending ceiling.

`pdsv1-main-parallel-20260906` attempted 48 slots: 47 returned images and one
OAuth request (`slot0036`) returned a complete HTTP 400 body with error type
`image_generation_user_error`, code `moderation_blocked`, input-stage moderation,
and recorded charge zero. The generic HTTP 400 stop treated it as an
administrative/payload contract failure. The operator stop and all 48 outcomes
remain terminal evidence. All retained raw responses and image metadata verified.
The total study charge including the pilot is $3.3797815, with no unresolved intents
or unknown charges. No generated fidelity vector has been measured or inspected.

## Corrected rule

Recognize only a complete, zero-charge HTTP 400 explicit error envelope with
`error.type=image_generation_user_error` and `error.code=moderation_blocked`,
without returned image data, as an observed moderation refusal. Verify the retained
response hashes before this decision. Preserve it as a failed slot; do not retry,
rewrite its prompt, or send that blocked slot through a different route. Other
HTTP 400 bodies retain the administrative/payload stop. Unknown outcomes and charges
still stop. Existing bounded transient-error retries remain unchanged.

Count refusals as failed initial attempts for the existing per-route failure-cluster
rule, including predecessor history: three consecutive failed initial attempts or
four among the last 20 stop further dispatch. This distinguishes an isolated
recorded refusal from a widespread service failure without claiming why moderation
occurred or attempting to bypass it.

## Successor inventory and execution

The successor `pdsv1-main-continuation-20260906` executes exactly the **960
unattempted slots** from the original 1,008-slot inventory, at disjoint paths.
Its freeze binds the predecessor's terminal ledgers, receipt, diagnosis, unchanged
scientific freeze, completed reference features and development scalers. The 48
attempted IDs, including the refusal, cannot be dispatched again.

Keep the original window origin (2026-09-06 14:30 UTC), eight offsets and within-route
order. Actual resumed timestamps remain recorded; do not fabricate a continuous
first window. Continue with three route workers, at most one active call per route,
and at least five seconds between recorded starts. Preserve the $75 study ceiling,
1,050-total/612-paid attempt caps, $5 paid-call reservation and at most 24 technical
retry children. Prior attempts and charges count toward all study-wide limits.

Commit the corrected source and tests before preparing the continuation freeze,
and commit that freeze before the next POST. The predecessor is not reopened.

## Combined scientific record

The final derived study view retains all 1,008 original slot identities: the 48
predecessor outcomes plus the 960 successor outcomes, including failures and every
conditional retry. It does not claim that the first census completed. The original
scientific randomization and estimands remain fixed; this continuation was specified
before generated-feature measurement. All original outcomes remain in availability
accounting. No favorable prefix, replacement image or additional slot is selected.

After successor collection is terminal, create a combined receipt binding both
censuses, and measure selected successful images in the continuation workspace.
Reuse the 210 completed reference vectors and three fixed development scalers.
Call the frozen analysis primitives for all endpoints. The one known refusal remains
missing, reduces the affected matched-pair supports, and is not imputed. Existing
minimum-support and Holm-family rules apply. Publish analysis and reports under the
successor's new directory. Explain the actual interruption, error classification,
refusal, retries, available sample sizes and no-interference limitation in the paper.
