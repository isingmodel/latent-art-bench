"""Explicit prospective collection and offline computational-only study replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import collection, common, workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(
        "prepare", "verify", "diagnose", "check-diagnostic", "collect", "measure", "check",
    ))
    parser.add_argument("--run-id", default=common.RUN_ID)
    parser.add_argument("--proxy-root", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command in ("prepare", "collect") and args.proxy_root is None:
        parser.error("prepare/collect requires the actual --proxy-root directory")
    if args.command == "prepare":
        result = workflow.prepare(root, args.run_id, args.proxy_root.resolve())
    elif args.command == "verify":
        freeze = workflow.verify(root, args.run_id)
        result = dict(status="verified", run_id=args.run_id,
                      recorded_git_commit=freeze["recorded_git_commit"])
    elif args.command in ("diagnose", "check-diagnostic"):
        result = workflow.diagnose(root, args.run_id, check=args.command == "check-diagnostic")
    elif args.command == "collect":
        if not args.live:
            parser.error("collect sends generation requests; specify --live explicitly")
        result = collection.collect(root, args.run_id, args.proxy_root.resolve())
    else:
        result = workflow.measure(root, args.run_id, check=args.command == "check")
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
