"""Explicit stage commands; importing the repository CLI does not load analysis libraries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    frame = commands.add_parser("frame", help="Offline identity reconciliation and role assignment")
    frame.add_argument("--frame-id", required=True)
    prepare = commands.add_parser(
        "prepare-acquisition", help="Bind clean committed acquisition inputs"
    )
    prepare.add_argument("--frame-id", required=True)
    prepare.add_argument("--run-id", required=True)
    acquire = commands.add_parser("acquire", help="LIVE: fetch registered real images")
    acquire.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "frame":
        from .corpus import build_frame
        result = build_frame(root, args.frame_id)
    elif args.command == "prepare-acquisition":
        from .acquire import prepare
        result = prepare(root, args.frame_id, args.run_id)
    else:
        from .acquire import execute
        result = execute(root, args.run_id)
    print(json.dumps(result, indent=2))
    return 0
