# Artifact retention policy

The repository contains both compact committed evidence and large ignored local bytes. Git ignore
status alone does not mean a file is disposable: several ignored roots hold bytes whose hashes are
tracked as evidence and which exist nowhere else.

## Canonical tracked material

Preserve and review normally:

- Painter Feature Generation v2 protocols, source, request freezes, frame, ledgers, terminal
  receipts, shared method freeze, feature/scaling records, calibration, crop diagnostics,
  response diagnostics, and available-model analysis reports; v2 access experiments do
  not replace or rewrite earlier terminal evidence;
- source, tests, configs, documentation, and compact reports; and
- Painter Feature Generation v1 protocols (2.1 canonical; 2.0 frozen at its path), R0 freezes,
  reviews, authorization seals, hash-chained
  request ledgers, candidate manifests, execution receipts, and the future R1/R2/M0/G0/G1/C0
  freezes and seals, complete-population assignments, population-calibration vectors, and
  auxiliary-reproduction-census manifests;
- the rendered §11.1 prompt library, the §7.4 content lexicon, the rebuilt §8 exposure denylist and
  its receipt, the evidence acknowledgement file, and the non-binding corpus pre-screen evidence.

Much of this material is hash-bound by path and SHA-256 at the commit that recorded each freeze.
Verification is commit-bound (see [the status page](STATUS.md)), so a later edit to a shared file
does not invalidate earlier evidence. Terminal collectors, their configs, tests, and adapter scripts
are nevertheless kept unmodified as policy: they are the record of what actually ran.

## Ignored but valuable local evidence

Archive before removing:

- `research_workspace/painter_feature_generation_v2/`, including pinned SD-Turbo weights,
  completed generated images, original-image acquisition responses, rendering metadata responses,
  and GPT Image access response bodies with embedded base64 image bytes;
- `research_workspace/painter_feature_generation_v1/`, the active study's content-addressed raw
  provider responses and one-shot locks — these are the bytes the tracked hashes attest to;
- `artifacts/models/sd2-base-vae/` pinned model weights;
- `artifacts/sources/kim-art-history/` pinned source checkout; and
- `tmp/pdfs/` retained literature PDFs.

The model weights, source checkout, and PDFs have no consumer in the current codebase; they are
retained research inputs for later stages, not live dependencies. Removing them costs re-download
time, not evidence.

Some of these bytes are copyrighted or expensive to reproduce. Their hashes are retained in
compact evidence, but the repository does not distribute them.

A Git commit or tag preserves only tracked history, not this full evidence graph. Before a
machine migration or broad local cleanup, create a separate checksum inventory and archive of
the ignored media, content-addressed stores, model/source artifacts, and outputs that must
remain byte-verifiable.

## Safe disposable state

The following may be removed whenever no process is using them:

- `.pytest_cache/`, `.ruff_cache/`, and `__pycache__/`;
- `.venv/`, after validation, because `uv.lock` can rebuild it; and
- unreferenced one-off diagnostics in `tmp/`.

A census's `.execution.lock` is never disposable even when zero-byte: it is the one-shot marker
proving that census ran exactly once.

Delete exact targets only. Do not use `git clean -xfd` and do not recursively delete `artifacts/`,
`data/`, or `research_workspace/`: each contains a mixture of tracked records and ignored research
bytes.

## Active study boundary

The active v2 continuation uses `research_workspace/painter_feature_generation_v2/`. Acquisition
and generation have produced ignored evidence; the model-access diagnosis found two decodable
images that did not satisfy the requested settings. Preserve their HTTP bodies even though their
terminal outcomes are `invalid_output`. See [current status](STATUS.md) for mutable stage state.

### Historical v1 boundary

The historical Painter Feature Generation v1 Protocol 2.1 uses the ignored
`research_workspace/painter_feature_generation_v1/` root. It contains exploratory metadata, the
completed fixed-seed audit's 165 content-addressed raw responses (about 51 MiB), the terminal broad
R1 responses, the completed broad R2 census's four raw responses (1,163,447 bytes), and the
completed broad-media R2 follow-up's 182 raw responses (55,899,277 bytes), and the completed AIC
R2 route census's four raw responses (308,569 bytes); compact hashes, events,
candidate manifests, and limitations are tracked. No active-study image,
eligibility derivative, normalized array, feature vector, registered generation request, generated
output, or result exists yet.

The broad-media follow-up R1 additionally retains one ignored content-addressed HTTP 200 response
and one lock file. Its tracked three-event ledger is terminal because the body was a plural
MediaWiki `errors:[maxlag]` envelope that R1 did not recognize, accompanied by `Retry-After: 5`.
It has no candidate manifest or execution receipt; do not delete, retry, or splice its response.
R2 is a distinct completed census with its own lock, CAS, 365-event ledger, candidate manifest, and
execution receipt. The R2 candidate rows remain non-admissions and its CAS must be archived before
any workspace cleanup.

The AIC route repeats that pattern. R1 retains one ignored content-addressed HTTP 200 response and
one lock file; its tracked three-event ledger is terminal because AIC returns `classification_id`
as a nonblank string identifier that the R1 parser rejected. It has no candidate manifest or
execution receipt; do not delete, retry, or splice its response. AIC R2 is a distinct completed
census under `metadata/aic_metadata_r2_20260902/` with its own lock, CAS, nine-event ledger,
153-row candidate manifest, and execution receipt, and its CAS must likewise be archived before any
workspace cleanup.

The metadata-audit layer may retain exact request intents, raw provider responses, hashes, terminal
receipts, and a compact non-admission candidate manifest. Raw responses remain ignored where their
size or terms make redistribution inappropriate. A metadata row never increments the admitted-work
or downloaded-image count. Every frozen source must reach its declared terminal condition; a target
count, favourable prefix, provider substitution, or later top-up is not a terminal rule.

Later R1 acquisition bytes must stay beneath the same ignored workspace. The tracked counterpart is
one compact physical-work/capture graph containing authority IDs, rights receipts, provider asset
IDs, canonical work IDs, capture ancestry, raw/normalized hashes, and one terminal disposition per
candidate. Multiple files, crops, mirrors, hosts, encodings, or hashes from one painting do not
create additional works. Only provenance-demonstrated independent captures enter the auxiliary
reproduction-disturbance set, and those works remain outside confirmation.

Protocol 2.1 has no coding derivatives. R2 produces per-candidate eligibility receipts from the
frozen content lexicon, all compact and tracked. Confirmation-resolution bytes and arrays live in
an ignored sealed store whose manifest of paths and hashes is committed before M0; every read of a
sealed path is recorded in a tracked append-only access ledger, which must be empty before the C0
opening receipt. Previously viewed or feature-exposed works remain on the tracked denylist and are
development-only. Every new eligible work receives the fixed painter × workflow 20%/20%/60%
development/qualification/confirmation assignment; no fixed 360-work quota exists.

M0 artifacts must bind the exact normalization and three feature families, fixtures, common pooled
median/IQR transform, same-work capture results, source/crop sensitivity, margins, copy-detector
thresholds, and whole-decision simulations. G0 artifacts bind the 16-template prompt census, model
identity, paired seeds, `R` selected from `{25,50,75,100}`, request order, failure policy, the
adherence classifier, and analysis. G1 retains every attempt/output/hash while confirmation
features remain unopened. C0 records the one-time reference opening and complete frozen analysis.

All committed paths are repository-relative. Add an ignored runtime subdirectory only when the
corresponding reviewed freeze authorizes that stage; directory existence alone is never permission.

## Fixed-path exceptions

A freeze records its inputs by path and sha256 and is verified at its recording commit, so git
history is what keeps the bound bytes. Freeze files, reviews, authorization seals, ledgers,
candidate manifests, and execution receipts must never be rewritten, reordered, truncated, moved,
or regenerated. Terminal collectors, their configs, and their tests stay at their paths and
unmodified as policy, because each is bound both by the freeze that authorized it and by the
successor freeze that binds its terminal evidence. Ignored research bytes under
`research_workspace/` are verified in the working tree and must stay byte-identical in place.

The two bound inputs that can never re-verify are recorded in
`data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json`, each with the exact
`bound_sha256` it excuses; the audit honours an entry only for that hash, and only after the git
history fallback finds nothing. Do not resolve a new mismatch by refreshing hashes or by extending
that file.
