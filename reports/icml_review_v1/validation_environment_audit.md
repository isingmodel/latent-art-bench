# Storage-dependent test verification

**Status: supplemental verification complete.** Vanilla `make check` recorded
**881 passed, 10 failed**
([original receipt](validation_environment_first.json)). This result is preserved;
the supplemental run is not a vanilla `make check` pass.

Both affected modules create artificial collector roots and mock HTTP transport,
but retain the production 5 GiB storage reserve and read the real host's free
space. Their fixtures do not supply a deterministic disk state. The production
guard therefore correctly stops before dispatch on this host. The original
receipt's suggestion that evicting the new checkpoint alone would resolve this
is insufficient: root reported approximately 3.7 GiB free before model downloads.

The explicit [supplemental plugin](storage_fixture.py) supplies 10 GiB free only
to the selected collector module at that test's exact temporary root. It delegates
all other paths and operations to the original `shutil` module. Production guards,
configuration, and frozen tests remain unchanged. Existing per-test overrides
remain effective. Real network I/O is prohibited in this pytest process.

Both entire affected modules were rerun because six unavailable-slot tests could
otherwise pass when storage stops before their mocked handler executes. All six
now recorded one mocked POST and their intended terminal disposition. The
unchanged zero-storage test recorded `storage_reserve` and zero attempts.

The [first supplemental receipt](validation_environment_supplemental.json)
records **84 passed, 1 setup error** (85 collected). The error was solely in the
new plugin: it compared two real disk readings while unrelated writes changed
free space by 4 KiB. The plugin now audits delegation without comparing changing
snapshots. Its initial bytes are archived in [storage_fixture_initial.py](storage_fixture_initial.py)
and match the first receipt's hash. Both test/collector bindings were unchanged;
no real network call was attempted. The outcome and command are preserved in the
[run log](validation_environment_supplemental.log).

After root completed CSD extraction/validation and evicted its downloaded
checkpoint, the [targeted rerun](validation_environment_supplemental_retry.json)
passed **2 tests in 1.09 seconds**: the interrupted retry case and the repeated
zero-storage control. It used the corrected helper with sufficient actual disk
space, unchanged frozen test/production hashes, and no real network attempts.

Across supplemental runs, **85 unique cases passed**: 84 first-run passes plus
2 targeted passes, minus the repeated zero-storage control. This includes all
10 originally failing cases. No additional frozen-test defect was found.
Only the two synthetic temporary directories created by this helper were removed,
after preserving receipts and logs. These are implementation and test-environment
verification results, not an independent scientific review or a vanilla full-suite
pass.
