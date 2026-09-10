"""Isolated CLI for the prospective prompt study; old study commands stay sealed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from latent_art_bench.io import read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import publish

from .common import CONFIG, MANIFESTS


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    commands = result.add_subparsers(dest="command", required=True)
    planning = commands.add_parser("plan", help="offline grid, storage and throughput estimate")
    planning.add_argument("--config", type=Path, default=CONFIG)
    freeze = commands.add_parser("prepare", help="freeze a committed, authorized complete grid")
    freeze.add_argument("run_id")
    freeze.add_argument("--proxy-root", required=True, type=Path)
    freeze.add_argument("--config", type=Path, default=CONFIG)
    generate = commands.add_parser("generate", help="dispatch only unattempted registered requests")
    generate.add_argument("run_id")
    generate.add_argument("--proxy-root", required=True, type=Path)
    generate.add_argument("--max-new-requests", type=int, default=None,
                          help="pause after this batch; does not alter the complete grid")
    measuring = commands.add_parser("measure", help="measure terminal retained generated responses")
    measuring.add_argument("run_id")
    measuring.add_argument("--max-new-records", type=int, default=None)
    for name in ("status", "analyze", "report", "check-run"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
    auditing = commands.add_parser("audit", help="read-only commit and retained-evidence audit")
    auditing.add_argument("--proxy-root", type=Path)
    simulation = commands.add_parser("simulate", help="offline synthetic calibration")
    simulation.add_argument("--seed", type=int, required=True)
    simulation.add_argument("--trials", type=int, required=True)
    simulation.add_argument("--pairs", nargs="+", type=int, required=True)
    simulation.add_argument("--alpha", type=float, required=True)
    simulation.add_argument("--dependence", choices=("shared_state", "independent_conditions"),
                            default="shared_state")
    simulation.add_argument("--output", type=Path, required=True)
    recording = commands.add_parser("publish-calibration", help="publish four synthetic runs")
    recording.add_argument("calibration_id")
    recording.add_argument("sources", nargs=4, type=Path,
                           help="original development, conservative development, two validations")
    checking = commands.add_parser("check-calibration")
    checking.add_argument("calibration_id")
    small_simulation = commands.add_parser("simulate-randomization")
    small_simulation.add_argument("--seed", required=True, type=int)
    small_simulation.add_argument("--trials", type=int, default=2000)
    small_simulation.add_argument("--output", required=True, type=Path)
    small_recording = commands.add_parser("publish-randomization-calibration")
    small_recording.add_argument("calibration_id")
    small_recording.add_argument("sources", nargs=2, type=Path)
    small_reproduction = commands.add_parser("reproduce-randomization")
    small_reproduction.add_argument("calibration_id")
    legacy_reproduction = commands.add_parser("reproduce-interval-development")
    legacy_reproduction.add_argument("calibration_id")
    return result


def dispatch(args) -> dict:
    root = args.root.resolve()
    if not (root / "pyproject.toml").is_file():
        raise ValueError("run from the repository root or supply --root")
    if args.command == "plan":
        from .design import plan
        return plan(root, args.config)
    if args.command == "prepare":
        from .design import prepare
        return prepare(root, args.run_id, args.proxy_root.resolve(), args.config)
    if args.command == "generate":
        from .generation import execute
        return execute(root, args.run_id, max_new_requests=args.max_new_requests,
                       proxy_root=args.proxy_root.resolve())
    if args.command == "measure":
        from .measurement import measure
        return measure(root, args.run_id, max_new_records=args.max_new_records)
    if args.command == "status":
        from .generation import status
        return status(root, args.run_id)
    if args.command == "analyze":
        from .analysis import analyze
        return analyze(root, args.run_id)
    if args.command == "report":
        from .report import execute
        return execute(root, args.run_id)
    if args.command == "check-run":
        from .reproduction import reproduce
        return reproduce(root, args.run_id)
    if args.command == "audit":
        from .audit import audit
        return audit(root, proxy_root=args.proxy_root)
    if args.command == "simulate":
        from .calibration import simulate
        result = simulate(seed=args.seed, trials=args.trials, pair_counts=tuple(args.pairs),
                          alpha=args.alpha, dependence=args.dependence)
        output = root / args.output
        publish(output, result)
        return dict(output=str(args.output), scenarios=len(result["scenarios"]),
                    provider_calls=0, seed=args.seed, trials_per_cell=args.trials)
    if args.command == "publish-calibration":
        from .calibration_record import publish_calibration
        return publish_calibration(root, args.calibration_id, args.sources)
    if args.command == "check-calibration":
        decision = read_json(root / MANIFESTS / args.calibration_id / "decision.json")
        if decision["primary_estimator"] == "paired_randomization":
            from .randomization_record import validate_randomization_calibration
            return validate_randomization_calibration(root, args.calibration_id)
        from .calibration_record import validate_calibration
        return validate_calibration(root, args.calibration_id)
    if args.command == "simulate-randomization":
        from .randomization import simulate_randomization
        result = simulate_randomization(seed=args.seed, trials=args.trials)
        publish(root / args.output, result)
        return dict(output=str(args.output), null_cells=len(result["null_cells"]),
                    provider_calls=0, seed=args.seed, trials_per_cell=args.trials)
    if args.command == "publish-randomization-calibration":
        from .randomization_record import publish_randomization_calibration
        return publish_randomization_calibration(root, args.calibration_id, args.sources)
    if args.command == "reproduce-randomization":
        from .randomization import simulate_randomization
        from .randomization_record import validate_randomization_calibration
        decision = validate_randomization_calibration(root, args.calibration_id)
        for source in decision["files"]:
            stored = read_json(root / source["path"])
            computed = simulate_randomization(seed=stored["seed"],
                                              trials=stored["trials_per_cell"])
            if computed != stored:
                raise ValueError(f"synthetic calibration does not reproduce: {source['path']}")
        return dict(calibration_id=args.calibration_id, reproduces=True, provider_calls=0,
                    files=len(decision["files"]))
    if args.command == "reproduce-interval-development":
        from .calibration_record import reproduce_calibration
        return reproduce_calibration(root, args.calibration_id)
    raise ValueError("unknown command")


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        result = dispatch(args)
    except (ValueError, OSError, KeyError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if args.command == "audit" and result.get("failures") else 0


if __name__ == "__main__":
    raise SystemExit(main())
