"""Freeze, publish and replay one bounded post-result diagnostic package."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import common, diagnostics, metrics, timing


def source_paths(root):
    # Bind executable scientific dependencies, including their imported primitives.
    paths = list(root.glob("src/latent_art_bench/painter_distribution_revision_v1/*.py"))
    paths += list(root.glob("tests/painter_distribution_revision_v1/*.py"))
    paths += list(root.glob("studies/painter_distribution_revision_v1/*.md"))
    for directory in (
        "painter_distribution_study_v1", "painter_distribution_exploration_v1",
        "painter_feature_generation_v2", "painter_prompt_study_v1",
    ):
        paths += list(root.glob(f"src/latent_art_bench/{directory}/*.py"))
    return sorted({p.relative_to(root) for p in paths} | {
        Path("src/latent_art_bench/io.py"), Path("pyproject.toml"), Path("uv.lock"),
        Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
    } | set(common.INPUT_PATHS))


def prepare(root):
    paths = source_paths(root)
    freeze = dict(
        run_id=common.RUN_ID,
        recorded_git_commit=committed(root, paths),
        inputs=bindings(root, paths),
        diagnostic_seed=2026090719,
        scope="Post-result numerical diagnostics on retained measured vectors and metadata.",
        collection_authorized_by_this_freeze=False,
        new_confirmatory_tests=False,
        environment=dict(python=platform.python_version(), numpy=np.__version__),
    )
    publish(root / common.DIRECTORY / "freeze.json", freeze)
    return dict(status="prepared", run_id=common.RUN_ID,
                recorded_git_commit=freeze["recorded_git_commit"], inputs=len(paths))


def verify(root):
    path = common.DIRECTORY / "freeze.json"
    freeze = read_json(root / path)
    committed(root, [path])
    verify_bindings(root, freeze["inputs"])
    return freeze


def primary_consistency(bundle):
    """Recompute the original primary table independently of the new metric views."""
    from latent_art_bench.painter_distribution_study_v1.analysis import weights
    from latent_art_bench.painter_distribution_study_v1.statistics import distribution_summary

    checks = []
    for cell in bundle["old_analysis"]["cells"]:
        if (cell["pipeline"], cell["weighting"], cell["feature_set"]) != (
            "primary512", "reference_content", "all31"
        ):
            continue
        real = [r for r in bundle["reference"]
                if r["pipeline"] == "primary512" and r["painter_id"] == cell["painter_id"]]
        fake = [r for r in bundle["generated"] if all(r[k] == cell[k] for k in (
            "pipeline", "painter_id", "route", "condition"
        ))]
        target = bundle["targets"][cell["painter_id"]]
        value = distribution_summary(
            [r["scaled"] for r in real], [r["scaled"] for r in fake],
            weights(real, target), weights(fake, target),
        )
        for key in ("energy_distance", "population_variance_ratio", "squared_iqr_sum_ratio"):
            if value[key] != cell[key]:
                raise ValueError(f"primary base result changed: {key}")
        checks.append(dict(painter_id=cell["painter_id"], route=cell["route"],
                           condition=cell["condition"], exact_match=True))
    if len(checks) != 14:
        raise ValueError("unexpected original primary cell count")
    return checks


def compute(bundle):
    baseline = primary_consistency(bundle)
    revised_metrics = metrics.analyze(bundle)
    bridge = metric_consistency(bundle["old_analysis"], revised_metrics)
    result = dict(
        run_id=common.RUN_ID, interpretation="Descriptive post-result methodological diagnostics",
        primary_consistency=baseline, metric_consistency=bridge, metrics=revised_metrics,
        diagnostics=diagnostics.analyze(bundle), timing=timing.analyze(bundle),
        source_counts=dict(reference_works=70, generated_images=1006, development_works=221,
                           pipelines=3, initial_research_slots=1008, new_generated_images=0),
        original_endpoints=bundle["old_analysis"]["endpoints"],
    )
    for row in result["timing"]["contrasts"]:
        if row["strategy"] == "all_selected":
            old = result["original_endpoints"][row["endpoint_index"]]
            if not np.isclose(row["estimate"], old["estimate"], atol=1e-12, rtol=0):
                raise ValueError("original endpoint estimate changed")
    # Reject a non-native/nonfinite result before creating any terminal output.
    return json.loads(json.dumps(result, allow_nan=False))


def metric_consistency(old, revised):
    checks = []
    for row in revised["cells"]:
        if (row["pipeline"], row["metric_view"]) != ("primary512", "original31"):
            continue
        candidates = [r for r in old["cells"] if all(r[k] == row[k] for k in (
            "pipeline", "painter_id", "route", "condition"
        )) and r["weighting"] == "reference_content" and r["feature_set"] == "all31"]
        if len(candidates) != 1:
            raise ValueError("metric bridge cannot resolve original cell")
        for new_key, old_key in (
            ("energy", "energy_distance"), ("trace_ratio", "population_variance_ratio"),
            ("squared_iqr_sum_ratio", "squared_iqr_sum_ratio"),
        ):
            if not np.isclose(row[new_key], candidates[0][old_key], atol=1e-12, rtol=0):
                raise ValueError(f"revision metric bridge changed: {new_key}")
        checks.append(row["cell_id"])
    contrast_checks = 0
    for row in revised["prompt_contrasts"]:
        if (row["pipeline"], row["metric_view"]) != ("primary512", "original31"):
            continue
        candidates = [r for r in old["endpoints"] if all(r[k] == row[k] for k in (
            "painter_id", "route", "before", "after"
        ))]
        if len(candidates) != 1 or not np.isclose(
            row["energy_change"], candidates[0]["estimate"], atol=1e-12, rtol=0
        ):
            raise ValueError("revision prompt metric bridge changed")
        contrast_checks += 1
    if len(checks) != 14 or contrast_checks != 6:
        raise ValueError("incomplete metric bridge grid")
    return dict(cell_ids=checks, prompt_contrasts=contrast_checks, absolute_tolerance=1e-12)


def build(root, check=False):
    freeze = verify(root)
    directory = root / common.DIRECTORY
    output = directory / "analysis.json"
    receipt_path = directory / "analysis_receipt.json"
    if check:
        receipt = read_json(receipt_path)
        if hash_file(directory / "freeze.json") != receipt["freeze_sha256"]:
            raise ValueError("revision freeze receipt mismatch")
        if receipt["recorded_git_commit"] != freeze["recorded_git_commit"]:
            raise ValueError("revision source commit receipt mismatch")
        if hash_file(output) != receipt["analysis_sha256"]:
            raise ValueError("revision analysis bytes changed")
    elif output.exists() or receipt_path.exists():
        raise ValueError("revision analysis is terminal; do not overwrite")
    value = compute(common.load(root))
    if check:
        if value != read_json(output):
            raise ValueError("revision numerical replay differs")
        return dict(status="verified", numeric_replay=True, run_id=common.RUN_ID)
    publish(output, value)
    publish(receipt_path, dict(
        recorded_git_commit=freeze["recorded_git_commit"],
        publication_git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
        freeze_sha256=hash_file(directory / "freeze.json"),
        analysis_sha256=hash_file(output),
        new_generation_calls=0,
    ))
    return dict(status="published", run_id=common.RUN_ID,
                output=output.relative_to(root).as_posix())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify", "build", "check"))
    command = parser.parse_args().command
    root = Path.cwd()
    if command == "prepare":
        result = prepare(root)
    elif command == "verify":
        result = dict(status="verified", run_id=verify(root)["run_id"])
    else:
        result = build(root, check=command == "check")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
