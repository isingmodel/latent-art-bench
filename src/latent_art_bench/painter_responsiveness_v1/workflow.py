"""Commit-bound publication and replay of the new study, without implicit live calls."""

from __future__ import annotations

import importlib.metadata
import platform
import tempfile
from pathlib import Path

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_revision_v1.analysis import source_paths as old_paths
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import analysis, common, design, inference


def source_paths(root):
    paths = set(old_paths(root))
    paths.update(p.relative_to(root) for p in (root / common.PACKAGE).glob("*") if p.is_file())
    paths.update(p.relative_to(root) for p in root.glob("tests/test_painter_responsiveness_*.py"))
    paths.update(p.relative_to(root) for p in root.glob("tests/painter_responsiveness_v1/*.py"))
    paths.update(p.relative_to(root) for p in (root / common.STUDIES).glob("*.md"))
    paths.update((common.CONFIG, Path("docs/RESEARCH_IDEA_20260908.md")))
    return sorted(paths)


def prepare(root, run_id):
    config = common.configuration(root)
    paths = source_paths(root)
    commit = committed(root, paths)
    freeze = dict(
        schema="painter-responsiveness-freeze/1", run_id=run_id,
        recorded_git_commit=commit, inputs=bindings(root, paths),
        scope="Post-result diagnostics; prospective design/simulation; human/collection gates.",
        generation_authorized_by_freeze=False, config=config,
        environment=dict(python=platform.python_version(), **{
            name: importlib.metadata.version(name) for name in
            ("numpy", "scipy", "Pillow", "matplotlib", "httpx", "PyWavelets", "scikit-image")}),
    )
    publish(root / common.directory(run_id) / "freeze.json", freeze)
    return dict(status="prepared", run_id=run_id, recorded_git_commit=commit, inputs=len(paths))


def verify(root, run_id):
    freeze = read_json(root / common.directory(run_id) / "freeze.json")
    committed(root, [common.directory(run_id) / "freeze.json"])
    if freeze["run_id"] != run_id:
        raise ValueError("run identity mismatch")
    verify_bindings(root, freeze["inputs"])
    if freeze["config"] != common.configuration(root):
        raise ValueError("configuration mismatch")
    for name, version in freeze["environment"].items():
        actual = platform.python_version() if name == "python" else importlib.metadata.version(name)
        if actual != version:
            raise ValueError("bound numerical runtime changed: " + name)
    return freeze


def compute(root):
    config = common.configuration(root)
    bundle = retained.load(root)
    diagnostics = analysis.analyze(bundle)
    schedule = design.make_schedule([r["template_id"] for r in config["templates"]],
                                    seed=config["seed"], repetitions=config["repetitions"])
    requests = common.requests_from_schedule(schedule, config)
    noise = inference.retained_noise(bundle["generated"], feature_index=config["feature_index"],
                                     route=config["route"], pipeline=config["primary_pipeline"])
    effects = [[0, 0]] + [[-d, -d] for d in config["meaningful_effect_grid"]]
    effects += [[-0.5, 0], [0, -0.5]]
    simulation = inference.simulate_design(
        noise, seed=config["simulation_seed"], trials=config["simulation_trials"],
        effects=effects, repetitions=config["repetitions"], alpha=config["alpha"])
    gates = common.generation_gate(
        dict(status="pending_independent_reference_validation"),
        dict(status="pending_human_coordinator_and_raters"),
        dict(margin_status=config["margin_status"], decision="pending_validation"), {},
    )
    return dict(schema="painter-responsiveness-results/1", diagnostics=diagnostics,
                simulation=simulation, retained_noise=noise, gates=gates,
                schedule=requests, factorial=None, human=dict(status="pending", ratings=0),
                claim="Hypothesis not established; D0 diagnoses old data and design feasibility.")


def build(root, run_id, *, check=False):
    from . import report

    freeze = verify(root, run_id)
    directory = root / common.directory(run_id)
    analysis_path = directory / "analysis.json"
    receipt_path = directory / "analysis_receipt.json"
    report_path = root / common.REPORTS / run_id
    if not check and (analysis_path.exists() or receipt_path.exists() or report_path.exists()):
        raise ValueError("analysis is terminal; never overwrite or rerun it in place")
    value = compute(root)
    if check:
        receipt = read_json(receipt_path)
        if (hash_file(analysis_path) != receipt["analysis_sha256"]
                or hash_file(directory / "freeze.json") != receipt["freeze_sha256"]):
            raise ValueError("analysis receipt mismatch")
        if value != read_json(analysis_path):
            raise ValueError("numeric replay changed")
        verify_bindings(root, receipt["reports"])
        with tempfile.TemporaryDirectory(prefix="responsiveness-replay-") as temporary:
            preview = Path(temporary)
            report.render(value, preview)
            published = root / common.REPORTS / run_id
            files = sorted(p.relative_to(preview) for p in preview.rglob("*") if p.is_file())
            if files != sorted(p.relative_to(published) for p in published.rglob("*")
                               if p.is_file()):
                raise ValueError("report replay inventory changed")
            if any(hash_file(preview / p) != hash_file(published / p) for p in files):
                raise ValueError("report replay bytes changed")
        return dict(status="verified", run_id=run_id, numeric_replay=True,
                    published_report_hashes=len(receipt["reports"]), report_byte_replay=True)
    publish(analysis_path, value)
    publish(directory / "planned_requests.jsonl", value["schedule"], lines=True)
    report.render(value, report_path)
    publish(receipt_path, dict(
        recorded_git_commit=freeze["recorded_git_commit"],
        freeze_sha256=hash_file(directory / "freeze.json"),
        analysis_sha256=hash_file(analysis_path),
        reports=bindings(root, [p.relative_to(root) for p in report_path.rglob("*")
                               if p.is_file()]),
        new_generated_images=0, new_human_ratings=0,
    ))
    return dict(status="published", run_id=run_id, report=str(report_path.relative_to(root)))
