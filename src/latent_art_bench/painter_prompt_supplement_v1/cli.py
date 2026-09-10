"""Isolated supplement CLI; the running source-study implementation is unchanged."""

import argparse
import json
import sys
from pathlib import Path

from . import artifacts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("qualify", "check-qualification", "prepare", "build", "check"):
        commands.add_parser(command).add_argument("identifier")
    commands.add_parser("audit")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not (root / "pyproject.toml").is_file():
        parser.error("run from the repository root or supply --root")
    try:
        if args.command == "check-qualification":
            result = artifacts.check_qualification(root, args.identifier, replay=True)
        elif args.command == "audit":
            result = artifacts.audit(root)
        else:
            result = getattr(artifacts, args.command)(root, args.identifier)
    except (ValueError, OSError, KeyError, RuntimeError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
    return int(result.get("overall") == "FAIL" or result.get("qualified") is False)


if __name__ == "__main__":
    raise SystemExit(main())
