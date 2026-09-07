"""Publish the unchanged fixed analysis with native JSON decision Booleans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import immediate as p
from . import immediate_results as results
from . import parallel_collection as reference
from . import study as s

RUN_ID = "pdsv1-analysis-20260907"
DIRECTORY = p.DIRECTORY.parent / RUN_ID
CONTRACT = Path("studies/painter_distribution_study_v1/ANALYSIS_PUBLICATION.md")


def native_payload(value):
    """Convert only decision flags; reject other unsupported/nonfinite values."""
    converted = dict(value)
    converted["endpoints"] = []
    for row in value["endpoints"]:
        flag = row["reject_at_05"]
        if not isinstance(flag, (bool, np.bool_)):
            raise TypeError("rejection flag must be a Boolean")
        converted["endpoints"].append(dict(row, reject_at_05=bool(flag)))
    decoded = json.loads(json.dumps(converted, allow_nan=False))
    if decoded != value:
        raise ValueError("JSON conversion changed an analysis value")
    return decoded


def prepare(root):
    p.verify(root)
    for name in ("generated_measurement_receipt.json", "collection_receipt.json"):
        verify_bindings(root, read_json(root / p.DIRECTORY / name)["outputs"])
    paths = [
        CONTRACT,
        s.PACKAGE / "analysis_publication.py",
        Path("tests/painter_distribution_study_v1/test_analysis_publication.py"),
        DIRECTORY / "serialization_diagnosis.json",
        s.DIRECTORY / "scalers.json",
        reference.DIRECTORY / "reference_features.jsonl",
    ] + [
        p.DIRECTORY / name
        for name in (
            "execution_freeze.json",
            "generated_features.jsonl",
            "generated_measurement_receipt.json",
            "collection_receipt.json",
            "slot_events.jsonl",
        )
    ]
    freeze = dict(
        run_id=RUN_ID,
        recorded_git_commit=committed(root, paths),
        inputs=bindings(root, paths),
        scientific_calculation="unchanged immediate_results.analyze / analysis.compute",
        correction="Convert only endpoints[*].reject_at_05 from NumPy to native bool.",
        timing="Publication correction after measurement; no scientific endpoint amendment.",
    )
    publish(root / DIRECTORY / "publication_freeze.json", freeze)
    return freeze


def verify(root):
    p.verify(root)
    freeze = read_json(root / DIRECTORY / "publication_freeze.json")
    verify_bindings(root, freeze["inputs"])
    committed(root, [DIRECTORY / "publication_freeze.json"])
    return freeze


def analysis(root, *, check=False):
    freeze = verify(root)
    directory = root / DIRECTORY
    output = directory / "analysis.json"
    receipt_path = directory / "analysis_receipt.json"
    if check:
        receipt = read_json(receipt_path)
        verify_bindings(root, receipt["inputs"])
        if hash_file(output) != receipt["analysis_sha256"]:
            raise ValueError("published analysis changed")
    elif output.exists() or receipt_path.exists():
        raise ValueError("analysis publication is terminal")
    value = native_payload(results.analyze(root))
    if check:
        if value != read_json(output):
            raise ValueError("unchanged calculation does not reproduce published values")
        return dict(status="verified", numeric_replay=True)
    publish(output, value)
    publish(
        receipt_path,
        dict(
            inputs=bindings(root, [DIRECTORY / "publication_freeze.json"]),
            analysis_sha256=hash_file(output),
            publication_source_commit=freeze["recorded_git_commit"],
            scientific_execution_freeze_sha256=hash_file(
                root / p.DIRECTORY / "execution_freeze.json"
            ),
            correction=freeze["correction"],
        ),
    )
    return dict(
        status="published",
        cells=len(value["cells"]),
        inferential_endpoints=len(value["endpoints"]),
        output=(DIRECTORY / "analysis.json").as_posix(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "build", "check"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare(root)
    elif args.command == "verify":
        result = verify(root)
    else:
        result = analysis(root, check=args.command == "check")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
