"""Reject staged Git blobs above GitHub's 100 MiB file limit."""

import os
import subprocess
import sys

LIMIT = 100 * 1024 * 1024


def oversized_staged_blobs(limit=LIMIT):
    entries = subprocess.check_output(["git", "ls-files", "--stage", "-z"])
    paths = {}
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        mode, oid, stage = metadata.split()
        if stage != b"0":
            raise ValueError("Resolve unmerged index entries before committing")
        if mode != b"160000":  # Submodule commit IDs are not file blobs.
            paths.setdefault(oid, []).append(os.fsdecode(path))
    if not paths:
        return []
    result = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        input=b"\n".join(paths) + b"\n", capture_output=True, check=True,
    )
    oversized = []
    for row in result.stdout.splitlines():
        oid, kind, size = row.split()
        if kind != b"blob":
            raise ValueError(f"Cannot inspect staged object {os.fsdecode(oid)}")
        if int(size) > limit:
            oversized.extend((path, int(size)) for path in paths[oid])
    return oversized


def main():
    try:
        oversized = oversized_staged_blobs()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Git size check failed: {error}", file=sys.stderr)
        return 1
    if oversized:
        print("Commit blocked: staged files exceed 100 MiB:", file=sys.stderr)
        for path, size in oversized:
            print(f"  {path!r}: {size / 1024**2:.2f} MiB", file=sys.stderr)
        print("Store a lossless archive or use Git LFS before staging.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
