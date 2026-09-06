"""Freeze the shared-scene, finite-reference main study before collecting outcomes."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import time
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import reference_delivery as delivery
from . import transport as t
from .inference import DIRECTORY as INFERENCE

RUN_ID = "pdsv1-main-20260906"
DIRECTORY = t.MANIFESTS / RUN_ID
WORKSPACE = t.WORKSPACE / RUN_ID
PACKAGE = Path("src/latent_art_bench") / t.NAMESPACE
CONFIG = Path("configs") / t.NAMESPACE / "research.json"
CONTRACT = Path("studies") / t.NAMESPACE / "MAIN.md"
CODING = t.MANIFESTS / "pdsv1-reference-coding-20260906"
OLD_METHOD = Path("data/manifests/painter_feature_generation_v2/pfg2-method-20260905")
ACQUISITIONS = Path(
    "data/manifests/painter_feature_generation_v2/pfg2-renderings-r2-20260905/acquisitions.jsonl"
)
PAINTERS = ("claude_monet", "paul_cezanne")
PAINTER_NAMES = dict(zip(PAINTERS, ("Claude Monet", "Paul Cezanne")))
CLASSES = ("water", "built", "land")
ROUTES = tuple(t.ROUTES)
PIPELINES = ("primary512", "resolution256", "jpeg90_512")


def conditions(route):
    return (
        ("artist_free", "named", "generic_named")
        if route == ROUTES[2]
        else ("artist_free", "named")
    )


def prompt(brief, painter, condition):
    result = "Create an oil painting on canvas."
    if condition != "artist_free":
        result += f" In the style of {PAINTER_NAMES[painter]}."
    result += " Scene: " + brief["generic" if condition == "generic_named" else "detailed"]
    return (
        result + " Render only the painting area, without a surrounding frame, "
        "signature, letters or watermark."
    )


def request_inventory(config):
    if (
        config["run_id"] != RUN_ID
        or config["repetitions"] != 3
        or len(config["window_offsets_hours"]) != 8
        or config["window_offsets_hours"] != [0, 3, 6, 9, 24, 27, 30, 33]
        or Counter(b["content_class"] for b in config["briefs"]) != dict.fromkeys(CLASSES, 8)
        or len({b["brief_id"] for b in config["briefs"]}) != 24
        or config["spending_ceiling_usd"] != 75
        or config["maximum_retry_attempts"] != 24
        or config["maximum_total_attempts_including_pilot"] != 1050
        or config["maximum_paid_attempts_including_pilot"] != 612
    ):
        raise ValueError("main inventory differs from the fixed bounded design")
    rng = np.random.default_rng(config["design_seed"])
    windows = [[] for _ in range(8)]
    for painter in PAINTERS:
        for index, brief in enumerate(config["briefs"]):
            for repetition in range(3):
                window = (index % 8 + 3 * repetition) % 8
                for route in ROUTES:
                    windows[window].append((painter, index, repetition, route))
    requests = []
    for window, groups in enumerate(windows):
        for group_position, chosen in enumerate(rng.permutation(len(groups))):
            painter, index, repetition, route = groups[chosen]
            brief = config["briefs"][index]
            for condition_position, condition in enumerate(rng.permutation(conditions(route))):
                sequence = len(requests)
                requests.append(
                    dict(
                        sequence=sequence,
                        request_id=f"slot{sequence:04d}",
                        route=route,
                        painter_id=painter,
                        brief_id=brief["brief_id"],
                        brief_index=index,
                        content_class=brief["content_class"],
                        repetition=repetition,
                        window=window,
                        group_position=group_position,
                        condition_position=condition_position,
                        condition=str(condition),
                        payload=t.payload(route, prompt(brief, painter, condition)),
                    )
                )
    t.validate_requests(requests)
    if len(requests) != 1008 or Counter(r["window"] for r in requests) != dict.fromkeys(
        range(8), 126
    ):
        raise ValueError("unexpected main slot count")
    return requests


def panel(root):
    annotations = read_jsonl(root / CODING / "annotations.jsonl")
    source = {r["work_id"]: r for r in read_jsonl(root / delivery.DIRECTORY / "deliveries.jsonl")}
    selected = []
    for row in annotations:
        if not row["eligible"]:
            continue
        item = source[row["work_id"]]
        selected.append(
            dict(row, native_short_side=min(item["expected_width"], item["expected_height"]))
        )
    if Counter(r["painter_id"] for r in selected) != {"claude_monet": 38, "paul_cezanne": 32}:
        raise ValueError("unexpected visually eligible panel")
    weights = {
        p: {
            c: sum(r["content_class"] == c for r in selected if r["painter_id"] == p)
            / sum(r["painter_id"] == p for r in selected)
            for c in CLASSES
        }
        for p in PAINTERS
    }
    for r in selected:
        if hash_file(root / r["response_path"]) != r["response_sha256"]:
            raise ValueError("reference bytes changed")
    return selected, weights


def development(root):
    rows = [
        r
        for r in read_jsonl(root / OLD_METHOD / "development_features.jsonl")
        if r["role"] == "development" and r["status"] == "measured"
    ]
    acquired = {r["work_id"]: r for r in read_jsonl(root / ACQUISITIONS)}
    if len(rows) != 221:
        raise ValueError("require the exact 221 development works")
    selected = []
    for row in rows:
        raw = acquired[row["image_id"]]
        if (
            raw["raw_sha256"] != row["raw_sha256"]
            or hash_file(root / raw["raw_path"]) != row["raw_sha256"]
        ):
            raise ValueError("development source image differs")
        selected.append(
            dict(
                image_id=row["image_id"],
                painter_id=row["painter_id"],
                response_path=raw["raw_path"],
                response_sha256=row["raw_sha256"],
            )
        )
    return selected


def source_paths():
    paths = [CONFIG, CONTRACT, ACQUISITIONS, Path("pyproject.toml"), Path("uv.lock")]
    paths += [
        Path("studies") / t.NAMESPACE / n
        for n in (
            "PROTOCOL.md",
            "REFERENCES.md",
            "REFERENCE_DELIVERY_R2.md",
            "RETRY_AMENDMENT.md",
            "INFERENCE.md",
        )
    ]
    paths += [
        PACKAGE / n
        for n in (
            "__init__.py",
            "study.py",
            "collection.py",
            "measurement.py",
            "analysis.py",
            "statistics.py",
            "inference.py",
            "transport.py",
            "discovery.py",
            "references.py",
            "reference_delivery.py",
        )
    ]
    paths += [
        Path("tests") / t.NAMESPACE / n
        for n in (
            "test_study.py",
            "test_collection.py",
            "test_measurement.py",
            "test_main_analysis.py",
        )
    ]
    paths += [
        Path("src/latent_art_bench") / p
        for p in (
            "io.py",
            "painter_feature_generation_v1/panel.py",
            "painter_feature_generation_v2/features.py",
            "painter_feature_generation_v2/statistics.py",
            "painter_feature_generation_v2/artifacts.py",
            "painter_distribution_exploration_v1/statistics.py",
            "painter_prompt_study_v1/common.py",
            "painter_prompt_study_v1/randomization.py",
            "painter_prompt_study_v1/calibration.py",
            "painter_prompt_study_v1/statistics.py",
        )
    ]
    paths += [
        OLD_METHOD / n for n in ("scaler.json", "development_features.jsonl", "method_freeze.json")
    ]
    paths += [CODING / n for n in ("annotations.jsonl", "receipt.json")]
    paths += [
        delivery.DIRECTORY / n
        for n in (
            "deliveries.jsonl",
            "acquisition_freeze.json",
            "acquisition_events.jsonl",
            "acquisition_receipt.json",
        )
    ]
    paths += [
        INFERENCE / n
        for n in ("freeze.json", "development.json", "validation.json", "decision.json")
    ]
    paths += [
        Path("reports") / t.NAMESPACE / "pdsv1-pilot-20260906" / n
        for n in ("summary.json", "receipt.json")
    ]
    return paths


def prepare(root, proxy_root, *, now=time.time):
    config = read_json(root / CONFIG)
    requests = request_inventory(config)
    references, weights = panel(root)
    devel = development(root)
    paths = source_paths()
    commit = committed(root, paths)
    directory = root / DIRECTORY
    if directory.exists():
        raise FileExistsError("main study identity already exists")
    if not read_json(root / INFERENCE / "decision.json")["qualified"]:
        raise ValueError("conditional prompt inference qualification did not pass")
    proxy = t.proxy_snapshot(proxy_root)
    for name, value in (
        ("requests", requests),
        ("reference_panel", references),
        ("development", devel),
    ):
        publish(directory / (name + ".jsonl"), value, lines=True)
    raw = [Path(r["response_path"]) for r in references + devel]
    freeze = dict(
        run_id=RUN_ID,
        recorded_git_commit=commit,
        inputs=bindings(root, paths + raw),
        inventories=bindings(
            root,
            [DIRECTORY / (n + ".jsonl") for n in ("requests", "reference_panel", "development")],
        ),
        window_origin_unix=math.ceil((now() + 300) / 900) * 900,
        window_offsets_hours=config["window_offsets_hours"],
        content_weights=weights,
        proxy_source=proxy,
        software={
            p: importlib.metadata.version(p)
            for p in ("httpx", "Pillow", "numpy", "scipy", "scikit-image", "PyWavelets")
        },
        budget=t.budget_state(root),
        total_slots=len(requests),
        inferential_endpoints=8,
        pipelines=list(PIPELINES),
        review_kind="single_maintainer_llm_self_review",
    )
    publish(directory / "main_freeze.json", freeze)
    return {k: v for k, v in freeze.items() if k not in ("inputs", "inventories", "proxy_source")}


def verify(root):
    freeze = read_json(root / DIRECTORY / "main_freeze.json")
    verify_bindings(root, freeze["inputs"] + freeze["inventories"])
    committed(
        root,
        [
            DIRECTORY / n
            for n in (
                "main_freeze.json",
                "requests.jsonl",
                "reference_panel.jsonl",
                "development.jsonl",
            )
        ],
    )
    if read_jsonl(root / DIRECTORY / "requests.jsonl") != request_inventory(
        read_json(root / CONFIG)
    ):
        raise ValueError("frozen request assignment differs")
    for package, version in freeze["software"].items():
        if importlib.metadata.version(package) != version:
            raise ValueError(f"main software version changed: {package}")
    return freeze


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "check"))
    parser.add_argument("--proxy-root", type=Path, default=Path("../openai-oauth"))
    args = parser.parse_args()
    root = Path.cwd()
    result = prepare(root, args.proxy_root.resolve()) if args.command == "prepare" else verify(root)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("inputs", "inventories", "proxy_source")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
