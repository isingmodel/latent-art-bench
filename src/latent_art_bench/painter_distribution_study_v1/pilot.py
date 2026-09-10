"""Freeze and execute the technical pilot, without fidelity feature measurement."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, publish
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import transport as t

RUN_ID = "pdsv1-pilot-20260906"
CONFIG = Path("configs") / t.NAMESPACE / "pilot.json"
ENDPOINTS = Path("configs") / t.NAMESPACE / "pilot_endpoints.json"
CONTRACT = Path("studies") / t.NAMESPACE / "PILOT.md"
SOURCE = (
    [CONFIG, ENDPOINTS, CONTRACT, Path("studies") / t.NAMESPACE / "PROTOCOL.md"]
    + [
        Path("src/latent_art_bench") / t.NAMESPACE / name
        for name in ("pilot.py", "transport.py", "discovery.py", "__init__.py")
    ]
    + [
        Path("tests") / t.NAMESPACE / "test_transport.py",
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
)


def request_grid(config):
    rows = []
    for painter in ("Claude Monet", "Paul Cezanne"):
        for scene in config["scenes"]:
            prompt = f"An oil painting by {painter}. {scene}"
            for route in t.ROUTES:
                sequence = len(rows)
                rows.append(
                    dict(
                        sequence=sequence,
                        request_id=f"technical-{sequence:02d}",
                        route=route,
                        painter=painter,
                        payload=t.payload(route, prompt),
                    )
                )
    t.validate_requests(rows)
    return rows


def prepare(root, proxy_root):
    config = read_json(root / CONFIG)
    if (
        config["run_id"] != RUN_ID
        or config["spending_ceiling_usd"] != 75
        or len(config["scenes"]) != 3
    ):
        raise ValueError("pilot contract changed")
    paths = list(SOURCE)
    for snapshot in read_json(root / ENDPOINTS):
        paths.append(Path(snapshot["retained_path"]))
        if hash_file(root / snapshot["retained_path"]) != snapshot["retained_sha256"]:
            raise ValueError("endpoint snapshot evidence changed")
    commit = committed(root, SOURCE)
    rows = request_grid(config)
    directory = root / t.MANIFESTS / RUN_ID
    if directory.exists():
        raise FileExistsError("pilot identity already prepared")
    proxy = t.proxy_snapshot(proxy_root)
    publish(directory / "requests.jsonl", rows, lines=True)
    freeze = dict(
        run_id=RUN_ID,
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        requests_sha256=hash_file(directory / "requests.jsonl"),
        proxy_source=proxy,
        authority="PILOT.md: 18 technical requests; no research measurement",
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
    )
    publish(directory / "generation_freeze.json", freeze)
    return dict(run_id=RUN_ID, requests=len(rows), inputs=len(paths), recorded_git_commit=commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "run"))
    parser.add_argument("--proxy-root", type=Path, required=True)
    args = parser.parse_args()
    result = (
        prepare(Path.cwd(), args.proxy_root)
        if args.command == "prepare"
        else t.run(Path.cwd(), RUN_ID, args.proxy_root)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
