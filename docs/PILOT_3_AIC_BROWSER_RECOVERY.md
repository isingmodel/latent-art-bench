# Pilot 3 AIC browser-recovery amendment

## Scope and trigger

This operational amendment was created after the first frozen development acquisition,
`work-aic-100026`, produced a durable scripted-client terminal response: HTTP 403, HTML body,
exact requested/resolved AIC IIIF URL, and no accepted artwork bytes. That evidence supports
only the statement **observed AIC scripted-client 403**. It does not identify Cloudflare or
another upstream component.

During diagnosis, the same exact URL was loaded and downloaded once in a controlled browser.
That diagnostic file had SHA-256
`1703506070e75a50978132507031ec04693aa776a0e437afa238fb3227545fd5` and 699,009 bytes. It
was not visually inspected, feature-extracted, normalized, or admitted to analytic artifacts.
It was quarantined, lost its source xattr after being moved, is permanently ineligible for
import, and must be replaced by a fresh download after the corresponding durable start.

The recovery changes no artist, work, partition, URL, provider, or frozen delivery dimension.
It applies uniformly to the 20 selected AIC development works and never authorizes access to
the sealed external holdout. Met and external acquisition retain their ordinary frozen paths.

## Prospective sequence

Run commands with `PYTHONPATH=src .venv/bin/python` from the repository root.

1. `scripts/import_pilot3_browser_acquisition.py --root . authorize` writes a create-once,
   self-hashed provider authorization. It binds the exact failed network intent/terminal,
   response hash, all 20 frozen AIC split rows, the pre-amendment Freeze-A1 commit, unchanged
   Phase-A config and split manifest, and this recovery implementation. It performs no fresh
   navigation, download, or image admission. Commit the authorization and amendment before
   continuing.
2. For one work only, choose a dedicated path that does not exist and run
   `scripts/import_pilot3_browser_acquisition.py --root . prepare --work-id WORK_ID
   --download-directory NEW_DIRECTORY`. Before creating the directory, this fsyncs a
   create-once directory intent. It then creates the directory exclusively with mode 0700,
   binds its device and inode, verifies an exactly empty direct-entry snapshot, records a
   wall-clock/monotonic not-before barrier, and fsyncs the exact append-only browser start.
   The trigger work keeps its failed network intent. Each other work receives a first-route
   `browser_recovery` intent. Browser attempt events must strictly alternate start/terminal;
   a final unmatched start prevents preparing another work.
3. Configure the controlled browser to download into the exact new directory, navigate to the
   exact `image_url` printed by `prepare`, and let the browser finish its download. If browser
   automation can download only to the directory's existing parent (for example the default
   `~/Downloads`), use this bounded alternative: prepare a fresh subdirectory under that same
   parent, complete the one download after the start, then perform one same-volume atomic rename
   of that completed file into the prepared subdirectory. Do not copy it, cross a filesystem,
   open another URL, or begin the next work first. The rename must preserve both xattrs and the
   post-start birth time; otherwise import fails closed.
4. Run
   `scripts/import_pilot3_browser_acquisition.py --root . import --directory DOWNLOAD_DIR`.
   The importer accepts only the directory bound by that start, reopens it without following
   links, verifies its original device/inode, and requires exactly one newly appearing direct
   regular file. It rejects `.crdownload`, extra entries, replacement directories, and any
   preexisting candidate. From the same no-follow file descriptor used to hash and read the
   image, it reads both `com.apple.metadata:kMDItemWhereFroms` and `com.apple.quarantine`.
   WhereFroms must be a bounded binary plist containing the exact frozen URL. Quarantine must
   contain a strict hexadecimal download timestamp and canonical UUID. The file birth time,
   ctime, and quarantine time must be no earlier than the prepared start (same-second values
   are accepted because the quarantine timestamp has one-second precision). The file must
   remain unchanged during the read, stay under the frozen 128 MiB cap, decode as JPEG at the
   frozen dimensions, and pass the existing input-domain checks.
5. A successful import stages raw and normalized bytes in content-addressed storage, appends
   a self-hashed terminal bound to the directory identity, baseline, both raw xattrs, start,
   and ledger-prefix CAS, and appends the ordinary
   acquisition row with `acquisition_completion_route=browser_download_import` and
   `httpx_success_claimed=false`. Only then prepare the next work.

The HTTP attempt journal is never rewritten. The original 403 remains a terminal HTTP result;
browser-derived bytes are never represented as an HTTPX success. Re-running prepare/import is
idempotent for the same evidence and fails closed on conflicts or tampering. After all AIC
imports, the ordinary `pilot3 acquire-real --phase development` resume verifies those records
and continues with Met.

P3-T07 re-runs acquisition provenance verification for every development feature and binds the
authorization, directory-intent journal, browser start/terminal journal, amendment, and importer
implementation into its immutable closure. Missing or tampered browser evidence therefore
prevents Freeze A2 and later external unsealing.
