"""Plan resources and freeze an explicitly authorized complete prompt experiment."""

from __future__ import annotations

import importlib.metadata
import json
import shutil
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_distance_v1.analysis import load_source
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    identifier,
    publish,
)
from latent_art_bench.painter_feature_generation_v2.model_assessment import PROXY_FILES

from .calibration_record import validate_calibration
from .common import CONFIG, MANIFESTS, PACKAGE, PROTOCOL, WORKSPACE, committed
from .prompts import METHOD_IDS, build_library

PROXY_BINDINGS = (*PROXY_FILES, "packages/openai-oauth/src/server.ts",
                  "packages/openai-oauth/src/shared.ts")
SOURCE_METHOD = "pfg2-method-20260905"
OLD_MANIFESTS = Path("data/manifests/painter_feature_generation_v2")


def validate_config(config: dict, *, authorized: bool = False) -> None:
    from .generation import _validate_config

    _validate_config(config)
    repetitions = config["repetitions"]
    method = config["primary_estimator"]
    if (config["maximum_requests"] != 480 * repetitions
            or config["aliases"] != ["gpt-image-1", "gpt-image-2"]
            or config["method_ids"] != list(METHOD_IDS)
            or config["base_url"] != "http://127.0.0.1:10532"
            or config["paid_fallback"] is not False
            or config["minimum_decoded_short_side"] != 512
            or method != "paired_randomization"
            or config["simultaneous_alpha"] != 0.05):
        raise ValueError("configuration does not describe the fixed repeated prompt design")
    expected = dict(size="1024x1024", quality="medium", output_format="png", background="opaque")
    if any(config[k] != v for k, v in expected.items()):
        raise ValueError("requested image settings changed")
    if (type(config["maximum_requests"]) is not int
            or type(config.get("approved_maximum_requests")) is not int
            or config["approved_maximum_requests"] < 0):
        raise ValueError("request ceilings must be nonnegative integers")
    if (
        type(config.get("permutation_seed")) is not int or config["permutation_seed"] < 0
        or config.get("permutation_draws") != 99999
        or config.get("multiplicity") != "holm"
    ):
        raise ValueError("small-study randomization requires fixed seeds, 99999 draws and Holm48")
    if authorized and (
        config.get("approved_maximum_requests", 0) < config["maximum_requests"]
        or not isinstance(config.get("authorization"), str)
        or not config["authorization"].strip()
    ):
        raise ValueError("the complete request budget requires explicit user authorization")


def validate_study_calibration(root: Path, config: dict) -> dict:
    if config["primary_estimator"] == "paired_randomization":
        from .randomization_record import validate_randomization_calibration
        decision = validate_randomization_calibration(root, config["calibration_id"])
    else:
        decision = validate_calibration(root, config["calibration_id"])
    if (
        decision["primary_estimator"] != config["primary_estimator"]
        or decision["simultaneous_alpha"] != config["simultaneous_alpha"]
        or config["repetitions"] not in decision["qualified_repetitions"]
        or decision["uses_empirical_outcomes_for_tuning"] is not False
    ):
        raise ValueError("the selected repetition count/inference lacks a qualified calibration")
    return decision


def plan(root: Path, config_path: Path = CONFIG) -> dict:
    config = read_json(root / config_path)
    validate_config(config)
    library = build_library(root)
    prior = read_jsonl(root / OLD_MANIFESTS / "pfg2-oauth-pilot-20260905/outputs.jsonl")
    mean_bytes = sum(r["bytes"] for r in prior) / len(prior)
    mean_seconds = sum(r["latency_seconds"] for r in prior) / len(prior)
    requests = config["maximum_requests"]
    workspace = root / WORKSPACE
    existing = workspace if workspace.exists() else root
    free = shutil.disk_usage(existing).free
    # Budget against the historical uncompressed mean, even though new bodies use lossless gzip.
    required = int(mean_bytes * requests) + config["reserve_disk_bytes"]
    return dict(
        status="planning_only_no_provider_calls", method_ids=list(METHOD_IDS),
        literal_prompts=len(library["prompts"]), aliases=config["aliases"],
        repetitions=config["repetitions"],
        matched_scene_pairs_per_contrast=16 * config["repetitions"],
        primary_estimator=config["primary_estimator"],
        requests=requests, generated_images_per_named_cell=16 * config["repetitions"],
        primary_prompt_contrasts=48, secondary_control_adjusted_contrasts=48,
        absolute_distance_endpoints=72, source_method_id=SOURCE_METHOD,
        historical_mean_response_bytes=mean_bytes, historical_mean_request_seconds=mean_seconds,
        estimated_serial_hours=requests * mean_seconds / 3600,
        estimated_uncompressed_response_gib=requests * mean_bytes / 1024**3,
        available_disk_gib=free / 1024**3, reserve_gib=config["reserve_disk_bytes"] / 1024**3,
        conservative_storage_preflight_passes=free >= required,
        conservative_runtime_budget_passes=(config["max_runtime_bytes"]
                                            >= int(mean_bytes * requests)),
        approved_maximum_requests=config["approved_maximum_requests"],
        budget_approved=(config["approved_maximum_requests"] >= requests
                         and isinstance(config.get("authorization"), str)
                         and bool(config["authorization"].strip())),
        assumptions="Historical throughput and raw-body mean only, not quota or size guarantees. "
                    "Raw responses will be losslessly compressed; no duplicate decoded images.",
    )


def prepare(root: Path, run_id: str, proxy_root: Path, config_path: Path = CONFIG) -> dict:
    from .generation import proxy_identity, request_grid

    identifier(run_id)
    output = root / MANIFESTS / run_id
    if output.exists():
        raise FileExistsError("choose a new run ID; existing runs are never replaced")
    config = read_json(root / config_path)
    validate_config(config, authorized=True)
    calibration_path = MANIFESTS / identifier(config["calibration_id"]) / "decision.json"
    decision = validate_study_calibration(root, config)
    resource = plan(root, config_path)
    if not resource["conservative_storage_preflight_passes"]:
        raise OSError("insufficient storage for the complete planned experiment and disk reserve")
    if not resource["conservative_runtime_budget_passes"]:
        raise ValueError("runtime byte ceiling is smaller than the complete size estimate")
    _, _, _, _, _, reference = load_source(root, SOURCE_METHOD)
    paths = [PROTOCOL, config_path, calibration_path, Path("uv.lock"), Path("pyproject.toml")]
    paths += [Path(r["path"]) for r in decision["files"]]
    paths += [(p.relative_to(root)) for p in sorted((root / PACKAGE).glob("*.py"))]
    paths += [p.relative_to(root) for p in sorted((root / "tests" / PACKAGE.name).glob("*.py"))]
    paths += [Path(r["path"]) for r in reference["inputs"]]
    paths += [Path(build_library(root)["source"]["path"])]
    paths += [Path("src/latent_art_bench/io.py"),
              Path("src/latent_art_bench/painter_feature_generation_v1/panel.py"),
              Path("src/latent_art_bench/painter_feature_generation_v1/prompt_library.py"),
              Path("src/latent_art_bench/painter_feature_distance_v1/analysis.py")]
    paths += [Path("src/latent_art_bench/painter_feature_generation_v2") / name for name in
              ("features.py", "statistics.py", "empirical.py", "artifacts.py", "pipeline.py",
               "oauth_generate.py", "model_assessment.py")]
    paths = sorted(set(paths))
    commit = committed(root, paths)
    proxy_paths = [Path(path) for path in PROXY_BINDINGS]
    proxy_commit = committed(proxy_root, proxy_paths)
    listener = proxy_identity(proxy_root)
    library = build_library(root)
    rows = request_grid(config, library)
    publish(output / "prompts.json", library)
    publish(output / "requests.jsonl", rows, lines=True)
    frozen = dict(
        schema_version="painter-prompt-study/1.0", run_id=run_id, config=config,
        config_path=config_path.as_posix(),
        source_method_id=SOURCE_METHOD, reference_inputs=reference["inputs"],
        requests=len(rows), requests_sha256=hash_file(output / "requests.jsonl"),
        library_sha256=hash_file(output / "prompts.json"), inputs=bindings(root, paths),
        recorded_git_commit=commit,
        proxy_source=dict(repository="openai-oauth", recorded_git_commit=proxy_commit,
                          files=bindings(proxy_root, proxy_paths), listener=listener),
        software={p: importlib.metadata.version(p) for p in
                  ("httpx", "Pillow", "numpy", "scipy", "scikit-image", "PyWavelets",
                   "matplotlib")},
        authorization=config["authorization"], resource_plan=resource,
        reviewer_kind="maintainer_run_llm_review_not_institutionally_independent",
        prepared_at_utc=utc_now().isoformat(),
    )
    publish(output / "generation_freeze.json", frozen)
    return frozen


def print_plan(root: Path, config_path: Path = CONFIG) -> None:
    print(json.dumps(plan(root, config_path), indent=2))
