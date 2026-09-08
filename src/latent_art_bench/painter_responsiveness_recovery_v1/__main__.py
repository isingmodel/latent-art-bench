"""Prepare one corrected transport run; reuse unchanged v2 scientific analysis."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
from pathlib import Path

from latent_art_bench.io import hash_file
from latent_art_bench.painter_distribution_study_v1.transport import proxy_snapshot
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, events, publish
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_responsiveness_v2 import common, workflow

from . import collection

RUN_ID = "prv2-oauth-recovery-20260908"
PREDECESSOR = "prv2-oauth-20260908"
PACKAGE = Path("src/latent_art_bench/painter_responsiveness_recovery_v1")
PROTOCOL = Path("studies/painter_responsiveness_recovery_v1/PROTOCOL.md")


def prepare(root, proxy_root):
    target = root / common.directory(RUN_ID)
    if target.exists():
        raise ValueError("replacement namespace already exists")
    _, _, slots, prior = workflow.collection_inputs(root, PREDECESSOR)
    if prior["status"] != "stopped" or prior["status_counts"] != {
            "image_returned": 49, "http_error": 1, "never_started": 142}:
        raise ValueError("this correction binds the documented terminal predecessor")
    directory = common.directory(PREDECESSOR)
    ledger = events(root / directory / "generation_events.jsonl")
    failures = [r for r in ledger if r["kind"] == "terminal" and r["status"] == "http_error"]
    if len(failures) != 1 or len(slots) != 192:
        raise ValueError("the recorded technical failure is not unique")
    failed = failures[0]
    body = workflow._response_entity(root, PREDECESSOR, failed, failed["attempt"])
    if (body != collection.EXACT_BODY or failed["status_code"] != 503
            or failed["complete"] is not True
            or failed.get("response_headers", {}).get("content-type") != "text/plain"):
        raise ValueError("observed failure differs from the prospective correction")
    paths = set(workflow.source_paths(root)) | {PROTOCOL}
    paths.update(p.relative_to(root) for p in (root / PACKAGE).glob("*.py"))
    paths.update(p.relative_to(root) for p in root.glob(
        "tests/painter_responsiveness_recovery_v1/*.py"))
    paths.update(directory / name for name in (
        "freeze.json", "planned_requests.jsonl", "collection_receipt.json",
        "generation_events.jsonl", "slot_outcomes.jsonl", "operator_events.jsonl",
        "diagnostic_receipt.json",
    ))
    commit = committed(root, sorted(paths))
    config = common.configuration(root)
    requests = common.requests(config)
    freeze = dict(
        schema="painter-responsiveness-freeze/2", run_id=RUN_ID,
        recorded_git_commit=commit, inputs=bindings(root, paths), config=config,
        proxy_snapshot=proxy_snapshot(proxy_root),
        environment=dict(python=platform.python_version(), **{
            name: importlib.metadata.version(name) for name in workflow.RUNTIME}),
        scope="One prospectively designated replacement; unchanged computational experiment.",
        new_openrouter_spending_authorized_usd=0, planned_images=192,
        recovery=dict(
            predecessor_run_id=PREDECESSOR,
            predecessor_receipt_path=str(directory / "collection_receipt.json"),
            predecessor_receipt_sha256=hash_file(root / directory / "collection_receipt.json"),
            policy="exact_proxy_503_text_v1",
            qualifying_error={key: failed[key] for key in (
                "request_id", "attempt", "response_path", "response_sha256",
                "stored_response_sha256")},
            successful_images_visually_reviewed_before_decision=False,
            scientific_features_extracted_before_decision=False,
            sole_primary_dataset=True,
        ),
    )
    publish(target / "planned_requests.jsonl", requests, lines=True)
    freeze["requests_sha256"] = hash_file(target / "planned_requests.jsonl")
    publish(target / "freeze.json", freeze)
    return dict(status="prepared", run_id=RUN_ID, recorded_git_commit=commit, inputs=len(paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "collect", "measure", "check"))
    parser.add_argument("--proxy-root", type=Path)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.command in ("prepare", "collect") and args.proxy_root is None:
        parser.error("prepare/collect requires the actual --proxy-root")
    if args.command == "collect" and not args.live:
        parser.error("collect sends generation requests; specify --live explicitly")
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare(root, args.proxy_root.resolve())
    elif args.command == "collect":
        result = collection.collect(root, RUN_ID, args.proxy_root.resolve())
    else:
        result = workflow.measure(root, RUN_ID, check=args.command == "check")
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
