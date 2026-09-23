"""Offline design preview and read-only preflight; deliberately no run command."""

import argparse
import json
from pathlib import Path

from . import preflight, protocol


def main():
    parser = argparse.ArgumentParser(__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("design")
    check = actions.add_parser("preflight")
    check.add_argument("--destination", type=Path)
    check.add_argument("--start", help="proposed explicit timezone-aware start; not a freeze")
    schedule = actions.add_parser("preview-schedule")
    schedule.add_argument("--start", required=True)
    args = parser.parse_args()
    if args.action == "design":
        result = protocol.design_record()
    elif args.action == "preflight":
        result = preflight.inspect(args.destination, args.start)
    else:
        rows = protocol.assignments(args.start)
        result = dict(status="draft preview only; no requests sent or authorization granted",
                      assignment_sha256=protocol.canonical_sha(rows), assignments=rows)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
