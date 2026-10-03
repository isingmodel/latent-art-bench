"""v3 reference stages (``python -m latent_art_bench.painter_specificity_v3``)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from latent_art_bench.painter_specificity_v3 import references


def _embed(name):
    def stage(root, run):
        from latent_art_bench.painter_specificity_v3.embeddings import extract_references

        return extract_references(root, run, name)
    return stage


def _predict(root, run):
    from latent_art_bench.painter_specificity_v3.predict import run as predict

    return predict(root, run)


STAGES = {
    "census": references.census,
    "metadata": references.metadata,
    "determine": references.determine,
    "frame": references.frame,
    "renderings": references.renderings,
    "acquire": references.acquire,
    "measure": references.measure,
    "embed-clip": _embed("clip"),
    "embed-csd": _embed("csd"),
    "predict": _predict,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=sorted(STAGES))
    parser.add_argument("--run", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    receipt = STAGES[args.stage](args.root.resolve(), args.run)
    print(json.dumps({k: v for k, v in receipt.items() if k != "inputs"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
