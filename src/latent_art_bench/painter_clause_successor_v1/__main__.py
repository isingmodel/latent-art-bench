"""Single successor commands; collection needs qualified commits and --live."""

import argparse
import json
from pathlib import Path

from . import common


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("prepare", "collect", "measure", "check", "verify-responses", "check-pixels"),
    )
    parser.add_argument("--run-id", default=common.RUN_ID)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--proxy-root", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.command in ("prepare", "collect") and args.proxy_root is None:
        parser.error("--proxy-root is required for the bound local service")
    if args.command == "collect" and not args.live:
        parser.error("collection requires --live after predecessor closure and qualification")
    from . import collection, workflow

    root = args.root.resolve()
    if args.command == "prepare":
        value = workflow.prepare(root, args.run_id, args.proxy_root)
    elif args.command == "collect":
        value = collection.collect(root, args.run_id, args.proxy_root, live=True)
    elif args.command == "measure":
        value = workflow.measure(root, args.run_id)
    elif args.command == "verify-responses":
        value = workflow.verify_responses(root, args.run_id)
    else:
        value = workflow.check(root, args.run_id, pixels=args.command == "check-pixels")
    print(json.dumps(value, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
