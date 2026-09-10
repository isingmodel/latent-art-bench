# Portable view of the terminal capture ledger

The original append-only ledger is retained unchanged at
`data/manifests/painter_capture_audit_v1/pcav1-20260910/attempts.jsonl`, SHA256
`63dfaacb3176a5f622a815aa8e4c9c9d690fb3930b842751dddb8f6b66311951`.
It is kept locally and ignored because two helper-path fields recorded the
maintainer's absolute workspace prefix. The terminal report and receipt bind
that original file; neither the file nor those bindings have been changed.

The committed [portable view](../../../data/manifests/painter_capture_audit_v1/pcav1-20260910/attempts.portable.json)
contains all 44 records in original order, each with its original line number
and SHA256 including the newline. Only `transport_source_path` at source lines
11 and 12 is changed to the repository-relative path of the same retained v3
helper. The view records both normalized fields and hashes of their original
string values. All other fields, including the original correction references,
are unchanged. This is a disclosed derivative, not a replacement ledger or a
new source hash for the terminal result.

The coordinator independently verified all 28 terminal bindings, 15 matched
actual request pairs, three actual requests per work, all HTTP counts and the
zero-pair result. The raw nonchargeable preflight entry remains visible in the
portable view. Public readers can inspect the complete metadata-event content
through this view; byte verification of the original ledger and retained page
bodies requires the local originals. No image bytes are part of this audit.
