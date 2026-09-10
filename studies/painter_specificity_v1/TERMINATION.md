# Model-selection diagnosis and termination

The 1,152-slot collection stopped before feature extraction. The original
protocol, assignments, source and ledger are unchanged. Three completed workers
had written response/image files when the collector was interrupted; their
terminal records were recovered from those exact bytes and marked explicitly.
Their original completion times are unavailable. All started requests returned
images; see `collection.json` for counts and reconciled charges. This cohort is
permanently closed and is excluded from the new model comparison.

The initial success probes established that requests were accepted and model IDs
were forwarded. They did not establish upstream selection. A subsequent negative
control requested `invalid-image-model-specificity-control` through the upstream
Image API: it returned HTTP 200 and an image. An independent request placing the
same invalid identifier in the Responses image-generation tool also returned an
image. Neither returned the image-model identity. The receipts retain both calls.

These observations do not prove that every valid ID selects the same model.
They invalidate acceptance alone as the qualification criterion for newly
released model variants. The paper must not infer a distinct checkpoint from
these transport probes. The local adapter's whitelist change remains a forwarding
capability, without verified upstream model selection.

The next attempt uses explicit OpenAI provider routes with a documented model
catalogue and low quality to stay below the user's $120 cumulative ceiling.
Its costs, rendering contract and assignments require a new namespace/freeze;
none of these 31 images will be used to fill its cells. The scientific question,
all four painters and six intended models remain the goal.
