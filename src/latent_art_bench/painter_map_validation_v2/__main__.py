"""Explicit commands; proxy qualification alone never starts live access."""

import argparse
import json
from pathlib import Path

from . import common


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "inputs",
            "metadata",
            "prepare",
            "verify",
            "collect",
            "measure",
            "check",
            "verify-responses",
        ),
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", default=common.RUN_ID)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.command in ("metadata", "collect") and not args.live:
        parser.error("explicit --live is required; no requests were sent")
    from . import collection, metadata, workflow

    root = args.root.resolve()
    if args.command == "metadata":
        value = metadata.run(root, common.PREFLIGHT_ID, live_metadata=True)
        value = dict(status=value["status"], receipt=str(common.METADATA))
    elif args.command == "inputs":
        value = workflow.write_inputs(root)
    elif args.command == "collect":
        value = collection.collect(root, args.run_id, live=True)
    else:
        function = {
            "prepare": workflow.prepare,
            "verify": workflow.verify,
            "measure": workflow.measure,
            "check": workflow.check,
            "verify-responses": workflow.verify_responses,
        }[args.command]
        value = function(root, args.run_id)
    print(json.dumps(value, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
