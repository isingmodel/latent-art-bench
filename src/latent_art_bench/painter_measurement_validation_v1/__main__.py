"""Run with python -m latent_art_bench.painter_measurement_validation_v1."""

import argparse
import json
from pathlib import Path

from . import pipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "run", "check", "report"))
    parser.add_argument("--run-id", default=pipeline.RUN_ID)
    args = parser.parse_args()
    if args.command == "report":
        from .report import build

        result = build(Path.cwd(), args.run_id)
    else:
        result = getattr(pipeline, args.command)(Path.cwd(), args.run_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
