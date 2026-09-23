# Independent numerical replay guard audit

## Result

**All 17 guard probes passed; no unresolved blocking defect found.** Fifteen forbidden operations were rejected and two legitimate reads succeeded. This is a bounded code audit, with no scientific rescoring.

Final audited launcher SHA-256: `f9fb24b62e2fb51ddfb33e8e8ed7b0659eaa7f3c71170b855d86b5b9e067e50f`. Environment: Python 3.13.11, macOS ARM64. Exact cases and the earlier failed descriptor probe are retained in `guard_audit.json`.

## Probes

Using disposable fixtures and mocked `runpy.run_module`, I redirected `ROOT` to a new scratch bundle and invoked `guarded_check(0)`. Unlink, mkdir, path write-mode open, outside-root read, original-checkout read, socket construction, process creation, rename, rmdir, chmod, truncate, utime, symlink, hardlink, and write-mode wrapping of a preopened descriptor all raised the intended `RuntimeError`. Reads inside the relocated bundle and installed runtime succeeded. Scratch contents and modes remained unchanged; no child process or socket was created, and no network request was made. All fixtures were removed.

## Fixed finding and retained history

The first inspected source (`5b61c3dac1cc6b6a975d28d5db393b27f49fb8733d844bd9a9036c4c3e96b12b`) returned for integer open names before checking write modes/flags. A scratch `open(fd, "w", closefd=False)` therefore changed bytes. The parent moved mode/flag validation before that return. I repeated the same probe and all other cases against the final source: every expected rejection and allowance passed. The original failed result is retained as history, rather than erased.

## Relocation and frozen association

I found no further same-host relocation blocker. Mock relocation rejected an original-checkout read while allowing relocated inputs and runtime code. The parent is separately running all 16 actual numerical checks from the extracted final archive; these mock probes do not replace that validation.

All 23 original frozen evidence records match their recorded hashes. The PDF matches the known review hash and round-03 `inputs.json`: `bbcc12901427538ed0938cdea510f848a0999d0edd08b4bc707c5b6fb8051472`. Discovery and verification explicitly require those records and that PDF.

On another host, dependencies outside `sys.prefix`/`sys.base_prefix`, additional operating-system metadata reads, or different numerical backends can cause legitimate failures. The README correctly limits its demonstrated claim to same-machine relocation and requires dependencies provisioned outside the extracted bundle. Do not relax scientific equality checks to hide differences.

This remains an accidental-operation guard, not an operating-system sandbox: Python audit hooks cannot cover every native I/O path, pre-hook startup, or direct I/O through existing descriptors. No claim of arbitrary-code containment follows from these probes.

No launcher, manuscript, science, prior scientific review or design-audit files were changed by this reviewer. No downloads, outcome reanalysis or paid calls occurred.
