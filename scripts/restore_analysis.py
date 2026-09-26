"""Restore the frozen transfer result from its lossless Git archive."""

import gzip
import hashlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = Path("reports/painter_prototype_transfer_v1/analysis.json")
SHA256 = "e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448"


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def restore(root=ROOT):
    target = root / RESULT
    if target.is_symlink():
        raise ValueError(f"Refusing a symlink at {target}")
    if target.exists():
        if digest(target) != SHA256:
            raise ValueError(f"Existing result has a different checksum; preserved {target}")
        return target

    # Validate before publishing, and never overwrite a concurrently created file.
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".analysis-", delete=False) as out:
        temporary = Path(out.name)
        try:
            with gzip.open(target.with_suffix(".json.gz"), "rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    out.write(block)
            out.flush()
            if digest(temporary) != SHA256:
                raise ValueError("Archive does not match the frozen analysis checksum")
            os.link(temporary, target)
        finally:
            temporary.unlink()
    return target


def main():
    try:
        path = restore()
    except (OSError, EOFError, ValueError) as error:
        print(f"Restore failed: {error}", file=sys.stderr)
        return 1
    print(f"Verified {path.relative_to(ROOT)} (SHA-256 {SHA256})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
