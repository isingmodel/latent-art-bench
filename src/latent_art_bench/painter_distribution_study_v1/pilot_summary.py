"""Verify raw technical pilot evidence and publish its cost/rendering qualification."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    digest,
    events,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import pilot
from . import transport as t

OUTPUT = Path("reports") / t.NAMESPACE / pilot.RUN_ID


def summarize(requests, rows):
    t.validate_requests(requests)
    attempts, terminal = {}, {}
    known = {r["request_id"]: r for r in requests}
    for row in rows:
        rid = row["request_id"]
        if rid not in known or rid in terminal or row["route"] != known[rid]["route"]:
            raise ValueError("unknown or multiply terminal pilot request")
        if row["kind"] == "attempt":
            if rid in attempts or row["request_sha256"] != digest(known[rid]):
                raise ValueError("duplicate or changed pilot request")
            attempts[rid] = row
        elif row["kind"] == "terminal" and rid in attempts:
            terminal[rid] = row
        else:
            raise ValueError("terminal without an attempt")
    if set(terminal) != set(known) or len(known) != 18:
        raise ValueError("pilot inventory is incomplete")
    cells = []
    for route in t.ROUTES:
        cell = [r for r in terminal.values() if r["route"] == route]
        valid = [r for r in cell if r["status"] == "image_returned"]
        costs = [r["cost_usd"] for r in cell]
        resolved = all(v is not None for v in costs)
        cells.append(
            dict(
                route=route,
                attempts=len(cell),
                decodable=len(valid),
                cost_resolved=resolved,
                total_cost_usd=sum(costs) if resolved else None,
                maximum_cost_usd=max(costs) if resolved else None,
                geometries=dict(
                    Counter(f"{r['observed']['width']}x{r['observed']['height']}" for r in valid)
                ),
                formats=dict(Counter(r["observed"]["format"] for r in valid)),
                mean_latency_seconds=sum(r["latency_seconds"] for r in cell) / len(cell),
                dispositions=dict(Counter(r["status"] for r in cell)),
            )
        )
    cost_resolved = all(c["cost_resolved"] for c in cells)
    pilot_cost = sum(c["total_cost_usd"] for c in cells) if cost_resolved else None
    # The prespecified remaining paid research allocation is 288 requests per paid route.
    projected = 288 * sum(c["maximum_cost_usd"] for c in cells) if cost_resolved else None
    qualified = all(c["decodable"] >= 5 for c in cells) and cost_resolved
    qualified = qualified and pilot_cost + 1.25 * projected <= 75
    return dict(
        run_id=pilot.RUN_ID,
        requests=18,
        routes=cells,
        pilot_cost_usd=pilot_cost,
        research_projection_usd=projected,
        projection_with_25_percent_headroom_and_pilot_usd=(
            pilot_cost + 1.25 * projected if cost_resolved else None
        ),
        technical_qualification=bool(qualified),
        fidelity_features_extracted=0,
        matching="Paid routes share observed 1024-square geometry, but JPEG/PNG differ. "
        "OAuth geometry and quality deviate; no fully matched rendering claim.",
    )


def verified_summary(root):
    directory = root / t.MANIFESTS / pilot.RUN_ID
    freeze = read_json(directory / "generation_freeze.json")
    verify_bindings(root, freeze["inputs"])
    for record in freeze["inputs"]:
        if not record["path"].startswith("research_workspace/"):
            blob = subprocess.check_output(
                ["git", "show", f"{freeze['recorded_git_commit']}:{record['path']}"], cwd=root
            )
            if hashlib.sha256(blob).hexdigest() != record["sha256"]:
                raise ValueError("pilot recorded-commit binding differs")
    receipt = read_json(directory / "generation_receipt.json")
    if receipt["events_sha256"] != hash_file(directory / "generation_events.jsonl"):
        raise ValueError("terminal pilot ledger changed")
    if receipt["freeze_sha256"] != hash_file(directory / "generation_freeze.json"):
        raise ValueError("terminal pilot freeze changed")
    rows = events(directory / "generation_events.jsonl")
    for row in rows:
        if row["kind"] != "terminal":
            continue
        path = root / row["response_path"]
        if hash_file(path) != row["retained_sha256"]:
            raise ValueError("retained pilot response changed")
        body = gzip.decompress(path.read_bytes())
        if hashlib.sha256(body).hexdigest() != row["response_sha256"]:
            raise ValueError("raw pilot response changed")
        if row["observed"] is not None and t.inspect_response(body) != row["observed"]:
            raise ValueError("pilot geometry replay differs")
        paid = t.ROUTES[row["route"]][1] is not None
        if t.cost_from_response(body, row["status_code"], paid) != row["cost_usd"]:
            raise ValueError("pilot cost replay differs")
    return summarize(read_jsonl(directory / "requests.jsonl"), rows)


def build(root):
    result = verified_summary(root)
    sources = [
        Path("src/latent_art_bench") / t.NAMESPACE / "pilot_summary.py",
        Path("tests") / t.NAMESPACE / "test_pilot_summary.py",
    ]
    paths = sources + [
        t.MANIFESTS / pilot.RUN_ID / f
        for f in (
            "generation_freeze.json",
            "generation_receipt.json",
            "generation_events.jsonl",
            "requests.jsonl",
        )
    ]
    commit = committed(root, paths)
    publish(root / OUTPUT / "summary.json", result)
    lines = [
        "# Technical pilot results",
        "",
        "All 18 requests returned decodable images. "
        "The pilot is excluded from research outcomes and no fidelity features were extracted.",
        "",
        "| Route | Images | Cost (USD) | Geometry | Encoding |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for row in result["routes"]:
        lines.append(
            f"| {row['route']} | {row['decodable']}/{row['attempts']} | "
            f"{row['total_cost_usd']:.7f} | {json.dumps(row['geometries'])} | "
            f"{json.dumps(row['formats'])} |"
        )
    lines += [
        "",
        f"Total pilot charge: **${result['pilot_cost_usd']:.7f}**. "
        "The remaining 576 paid research requests project to "
        f"${result['research_projection_usd']:.4f} "
        "using each route's maximum observed pilot cost. Adding 25% headroom and the pilot "
        f"gives **${result['projection_with_25_percent_headroom_and_pilot_usd']:.4f}**, below $75.",
        "",
        "All three routes pass the prospective technical criterion. This qualifies "
        "transport and estimated affordability, not statistical power or painter fidelity.",
        "",
        result["matching"],
        "Retain the paid geometry comparison and separate OAuth "
        "service comparison. The main analysis must include common-JPEG and resize "
        "sensitivities; they cannot erase unknown capture or earlier encoding histories.",
        "",
        "Google and BFL provider pins were requested with fallback disabled. The "
        "responses do not attest immutable model snapshots. All six OAuth responses "
        "reported low quality despite medium requests. No route was changed or retried.",
        "",
        "Verification replays the raw-response hashes, costs and decoded container "
        "metadata. This is maintainer/LLM self-review, not institutional independence.",
        "",
        "Recheck with `uv run --locked python -m "
        "latent_art_bench.painter_distribution_study_v1.pilot_summary check`.",
        "",
    ]
    output = root / OUTPUT / "REPORT.md"
    with output.open("x") as stream:
        stream.write("\n".join(lines))
    publish(
        root / OUTPUT / "receipt.json",
        dict(
            recorded_git_commit=commit,
            inputs=bindings(root, paths),
            outputs=bindings(root, [OUTPUT / "summary.json", OUTPUT / "REPORT.md"]),
        ),
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "build":
        result = build(root)
    else:
        result = verified_summary(root)
        if read_json(root / OUTPUT / "summary.json") != result:
            raise ValueError("pilot summary replay differs")
        receipt = read_json(root / OUTPUT / "receipt.json")
        verify_bindings(root, receipt["inputs"] + receipt["outputs"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
