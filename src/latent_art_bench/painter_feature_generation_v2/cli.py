"""Explicit stage commands; importing the repository CLI does not load analysis libraries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("audit", help="Offline verification of v2 evidence and retained bytes")
    frame = commands.add_parser("frame", help="Offline identity reconciliation and role assignment")
    frame.add_argument("--frame-id", required=True)
    prepare = commands.add_parser(
        "prepare-acquisition", help="Bind clean committed acquisition inputs"
    )
    prepare.add_argument("--frame-id", required=True)
    prepare.add_argument("--run-id", required=True)
    acquire = commands.add_parser("acquire", help="LIVE: fetch registered real images")
    acquire.add_argument("--run-id", required=True)
    method = commands.add_parser("prepare-method", help="Freeze the shared empirical method")
    method.add_argument("--method-id", required=True)
    method.add_argument("--frame-id", required=True)
    method.add_argument("--acquisition-id", required=True)
    method.add_argument("--experiment-id", action="append", required=True)
    method.add_argument("--calibration-id", required=True)
    measure = commands.add_parser("measure", help="Measure one authorized frozen image stage")
    measure.add_argument("--method-id", required=True)
    measure.add_argument(
        "--stage",
        choices=("development", "qualification", "confirmation", "generated"),
        required=True,
    )
    measure.add_argument("--experiment-id")
    analysis = commands.add_parser("analyze", help="Repeated-block SD-Turbo analysis")
    analysis.add_argument("--method-id", required=True)
    analysis.add_argument("--experiment-id", required=True)
    for name, help_text in (
        ("empirical", "Common finite comparisons and source diagnostics"),
        ("robustness", "Complete paired 496-pixel crop sensitivity"),
        ("report", "Write the empirical Markdown analysis report from sealed results"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--method-id", required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "audit":
        from .audit import audit

        result = audit(root)
    elif args.command == "frame":
        from .corpus import build_frame

        result = build_frame(root, args.frame_id)
    elif args.command == "prepare-acquisition":
        from .acquire import prepare

        result = prepare(root, args.frame_id, args.run_id)
    elif args.command == "acquire":
        from .acquire import execute

        result = execute(root, args.run_id)
    elif args.command == "prepare-method":
        from .pipeline import prepare

        result = prepare(
            root,
            args.method_id,
            args.frame_id,
            args.acquisition_id,
            args.experiment_id,
            args.calibration_id,
        )
    elif args.command == "measure":
        from .pipeline import measure

        result = measure(root, args.method_id, args.stage, args.experiment_id)
    elif args.command == "analyze":
        from .pipeline import analyze

        result = analyze(root, args.method_id, args.experiment_id)
    elif args.command == "empirical":
        from .empirical import analyze

        result = analyze(root, args.method_id)
    elif args.command == "robustness":
        from .robustness import execute

        result = execute(root, args.method_id)
    else:
        from .report import execute

        result = execute(root, args.method_id)
    print(json.dumps(result, indent=2))
    return 1 if result.get("overall") == "FAIL" else 0
