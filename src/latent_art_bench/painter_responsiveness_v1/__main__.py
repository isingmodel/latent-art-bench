"""Explicit offline and gated live entry points for the responsiveness study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import common, human_package, preflight, workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(
        "prepare", "build", "check", "preflight", "human-prepare", "human-preview",
        "human-session", "import-ratings", "generation-prepare", "collect", "measure",
    ))
    parser.add_argument("--run-id", default=common.DIAGNOSTIC_ID)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--submissions", type=Path, nargs="+")
    parser.add_argument("--phase", choices=("validation", "usability_pilot"),
                        default="validation")
    parser.add_argument("--diagnostic-run-id", default=common.DIAGNOSTIC_ID)
    parser.add_argument("--decision", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = workflow.prepare(root, args.run_id)
    elif args.command in ("build", "check"):
        result = workflow.build(root, args.run_id, check=args.command == "check")
    elif args.command == "preflight":
        if not args.live:
            parser.error("preflight makes three GET requests; specify --live explicitly")
        result = preflight.build(root, args.run_id)
    elif args.command == "human-prepare":
        result = human_package.prepare(root, args.run_id)
    elif args.command == "human-preview":
        result = human_package.materialize(root, args.run_id)
    elif args.command == "human-session":
        if args.plan is None:
            parser.error("human-session requires an actual --plan JSON path")
        result = human_package.create_session(root, args.run_id, args.plan)
    elif args.command == "import-ratings":
        if not args.submissions:
            parser.error("import-ratings requires actual --submissions JSON exports")
        result = human_package.import_ratings(root, args.run_id, args.submissions, phase=args.phase)
    elif args.command == "generation-prepare":
        from . import generation_prepare

        if args.decision is None:
            parser.error("generation-prepare requires an actual --decision JSON path")
        result = generation_prepare.prepare(
            root, args.run_id, args.diagnostic_run_id, args.decision)
    else:
        from . import collection

        if args.command == "collect":
            if not args.live:
                parser.error("collect requires --live and a committed, qualified generation freeze")
            result = collection.collect(root, args.run_id)
        else:
            from . import measurement

            result = measurement.build(root, args.run_id)
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
