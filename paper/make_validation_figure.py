"""Render or check the manuscript's computational challenge matrix."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from latent_art_bench.painter_measurement_validation_v1.report import figures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "data/manifests/painter_measurement_validation_v1/pmvv1-20260910/analysis.json"
    target = root / "paper/figures/challenge_matrix.pdf"
    analysis = json.loads(source.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="paper-validation-") as temporary:
        figures(Path(temporary), analysis)
        content = (Path(temporary) / target.name).read_bytes()
    if args.check:
        if target.read_bytes() != content:
            raise ValueError("manuscript challenge figure differs from its numeric source")
        print("Challenge matrix reproduces byte for byte.")
    else:
        target.write_bytes(content)
        print(target.relative_to(root))


if __name__ == "__main__":
    main()
