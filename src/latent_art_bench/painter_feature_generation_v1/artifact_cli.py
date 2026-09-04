"""Shared ``--root/--check`` command line for the deterministic R0 artifact renderers.

Each renderer supplies ``expected(root)``, a mapping from repository-relative output path to
the exact text a fresh render would produce, and ``write(root)``, which writes those outputs
atomically and returns a summary. ``--check`` compares every expected output with the tracked
file and exits 1 on any drift, so a stale receipt is caught as readily as a stale artifact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

ExpectedFn = Callable[[Path], Mapping[Path, str]]
WriteFn = Callable[[Path], Mapping[str, Any]]


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any tracked output differs from a fresh render",
    )
    return parser


def check(root: Path, expected: Mapping[Path, str]) -> Dict[str, Any]:
    outputs = {}
    for path, text in expected.items():
        target = root / path
        observed = target.read_text(encoding="utf-8") if target.is_file() else None
        outputs[str(path)] = observed == text
    return {"in_sync": all(outputs.values()), "outputs": outputs}


def run(
    description: str,
    expected: ExpectedFn,
    write: WriteFn,
    argv: Optional[Sequence[str]] = None,
) -> int:
    args = build_parser(description).parse_args(argv)
    root = args.root.resolve()
    if args.check:
        result = check(root, expected(root))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["in_sync"] else 1
    print(json.dumps(write(root), indent=2, sort_keys=True, ensure_ascii=False))
    return 0
