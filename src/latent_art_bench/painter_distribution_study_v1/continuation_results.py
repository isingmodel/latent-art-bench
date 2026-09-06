"""Combined fixed-slot outcomes and unchanged scientific analysis after a refusal stop."""

from __future__ import annotations

import argparse
import base64
import json
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    events,
    publish,
    stage_lock,
    verify_bindings,
)

from . import analysis as a
from . import collection as c
from . import continuation as p
from . import measurement as m
from . import parallel_collection as predecessor
from . import study as s
from . import transport as t


def component_slots(root):
    return [
        row
        for directory in (predecessor.DIRECTORY, p.DIRECTORY)
        for row in events(root / directory / "slot_events.jsonl")
    ]


def combine(root):
    p.verify(root)
    components = []
    paths = []
    for directory in (predecessor.DIRECTORY, p.DIRECTORY):
        receipt = read_json(root / directory / "generation_receipt.json")
        verify_bindings(root, receipt["outputs"])
        paths.extend(Path(r["path"]) for r in receipt["outputs"])
        paths.append(directory / "generation_receipt.json")
        components.append(
            dict(
                run_id=receipt["run_id"],
                status=receipt["status"],
                terminal_slots=receipt["terminal_slots"],
            )
        )
    if components[-1]["status"] != "completed":
        raise ValueError("finish the authorized remaining inventory before combined measurement")
    slots = component_slots(root)
    expected = {r["request_id"] for r in read_jsonl(root / s.DIRECTORY / "requests.jsonl")}
    observed = [r["request_id"] for r in slots]
    if len(observed) != len(set(observed)) or set(observed) != expected:
        raise ValueError("combined slots must cover the exact original inventory once")
    budget = t.budget_state(root)
    if budget["unresolved"] or budget["uncertain"]:
        raise ValueError("unresolved collection accounting")
    receipt_path = root / p.DIRECTORY / "collection_receipt.json"
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        verify_bindings(root, receipt["outputs"])
        return receipt
    receipt = dict(
        run_id=p.RUN_ID,
        status="completed",
        terminal_slots=len(slots),
        slots=len(expected),
        dispositions=dict(Counter(r["status"] for r in slots)),
        component_runs=components,
        budget=budget,
        outputs=bindings(root, paths),
        execution_freeze_sha256=hash_file(root / p.DIRECTORY / "execution_freeze.json"),
        scope="derived fixed-slot view; predecessor census remains stopped",
    )
    publish(receipt_path, receipt)
    return receipt


def inventory(root, stage):
    if stage != "generated":
        raise ValueError("reference and development measurement are already complete")
    receipt = read_json(root / p.DIRECTORY / "collection_receipt.json")
    verify_bindings(root, receipt["outputs"])
    requests = read_jsonl(root / s.DIRECTORY / "requests.jsonl")
    slots = {r["request_id"]: r for r in component_slots(root)}
    selected = []
    for request in requests:
        row = slots[request["request_id"]]
        if row["status"] != "image_returned":
            continue
        selected.append(
            dict(
                request,
                image_id="generated:" + request["request_id"],
                selected_request_id=row["selected_request_id"],
                selected_response=row["selected_response"],
                initial_only_eligible=row["initial_status"] == "image_returned",
            )
        )
    return selected


def measure_item(root, stage, item):
    body = c.read_response(root, item["selected_response"])
    observed = t.inspect_response(body)
    if observed != item["selected_response"]["observed"]:
        raise ValueError("successor image metadata differs from its terminal evidence")
    raw = base64.b64decode(json.loads(body)["data"][0]["b64_json"], validate=True)
    metadata = {
        k: item[k]
        for k in (
            "image_id",
            "painter_id",
            "content_class",
            "request_id",
            "selected_request_id",
            "route",
            "brief_id",
            "brief_index",
            "condition",
            "repetition",
            "window",
            "initial_only_eligible",
        )
    }
    metadata.update(stage=stage, raw_sha256=observed["image_sha256"])
    temporary = root / p.WORKSPACE / "measurement_tmp"
    temporary.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="decode-", dir=temporary) as directory:
        path = Path(directory) / "image.bin"
        path.write_bytes(raw)
        return m.measure_path(path, metadata, s.PIPELINES)


def measure(root, stage, *, check=False):
    with stage_lock(root / p.WORKSPACE / ".measurement.writer.lock"):
        p.verify(root)
        directory = root / p.DIRECTORY
        ledger = directory / (stage + "_features.jsonl")
        receipt_path = directory / (stage + "_measurement_receipt.json")
        if stage != "generated":
            raise ValueError("only generated measurement remains")
        combine(root)
        items = inventory(root, stage)
        if check:
            verify_bindings(root, read_json(receipt_path)["outputs"])
        elif receipt_path.exists():
            raise ValueError("successor measurement is terminal")
        known = {(r["image_id"], r["pipeline"]): r for r in events(ledger)}
        expected = {(r["image_id"], pipeline) for r in items for pipeline in s.PIPELINES}
        if len(known) != len(events(ledger)) or not set(known) <= expected:
            raise ValueError("successor measurement inventory differs")
        if check and set(known) != expected:
            raise ValueError("terminal measurement membership is incomplete")
        pending = (
            items
            if check
            else [
                r for r in items if any((r["image_id"], pipe) not in known for pipe in s.PIPELINES)
            ]
        )
        if not items and not ledger.exists() and not check:
            ledger.touch(exist_ok=False)
        with ThreadPoolExecutor(max_workers=2) as executor:
            for index, batch in enumerate(
                executor.map(lambda item: measure_item(root, stage, item), pending)
            ):
                for row in batch:
                    key = row["image_id"], row["pipeline"]
                    if key in known:
                        if {k: known[key][k] for k in row} != row:
                            raise ValueError("successor raw-to-feature replay differs")
                    elif not check:
                        known[key] = append_event(ledger, row)
                if (index + 1) % 25 == 0:
                    print(
                        json.dumps(dict(stage=stage, processed_images=index + 1, replay=check)),
                        flush=True,
                    )
        if check:
            return dict(stage=stage, status="verified", replayed_records=len(known))
        rows = events(ledger)
        receipt = dict(
            stage=stage,
            images=len(items),
            pipelines=list(s.PIPELINES),
            dispositions=dict(Counter(r["status"] for r in rows)),
            source_freeze_sha256=hash_file(directory / "execution_freeze.json"),
            outputs=bindings(root, [p.DIRECTORY / ledger.name]),
            scalers_sha256=hash_file(root / s.DIRECTORY / "scalers.json"),
            duplicate_raw_hashes={
                h: n
                for h, n in Counter(
                    r["raw_sha256"] for r in rows if r["pipeline"] == "primary512"
                ).items()
                if n > 1
            },
        )
        publish(receipt_path, receipt)
        return receipt


def analyze(root):
    freeze = p.verify(root)
    collection = combine(root)
    directory = root / p.DIRECTORY
    verify_bindings(
        root,
        read_json(root / predecessor.DIRECTORY / "reference_measurement_receipt.json")["outputs"],
    )
    verify_bindings(root, read_json(directory / "generated_measurement_receipt.json")["outputs"])
    result = a.compute(
        events(root / predecessor.DIRECTORY / "reference_features.jsonl"),
        events(directory / "generated_features.jsonl"),
        read_json(root / s.DIRECTORY / "scalers.json"),
        freeze["content_weights"],
        read_json(root / s.CONFIG),
    )
    result["generation_accounting"] = collection
    result["actual_slot_times"] = [
        dict(request_id=r["request_id"], window=r["window"], completed_at_utc=r["at_utc"])
        for r in component_slots(root)
    ]
    result["claim_scope"] = (
        "finite recorded reference panel; feature-distribution results, "
        "no aesthetic or oeuvre-equivalence conclusion"
    )
    result["execution"] = dict(
        run_id=p.RUN_ID,
        maximum_in_flight=3,
        maximum_per_route=1,
        minimum_start_interval_seconds=5,
        scientific_predecessor=s.RUN_ID,
    )
    return result


def analysis(root, *, check=False):
    directory = root / p.DIRECTORY
    if check:
        receipt = read_json(directory / "analysis_receipt.json")
        verify_bindings(root, receipt["inputs"])
        if hash_file(directory / "analysis.json") != receipt["analysis_sha256"]:
            raise ValueError("successor analysis changed")
        if analyze(root) != read_json(directory / "analysis.json"):
            raise ValueError("successor numeric replay differs")
        return dict(status="verified", numeric_replay=True)
    result = analyze(root)
    publish(directory / "analysis.json", result)
    paths = [
        p.DIRECTORY / n
        for n in (
            "execution_freeze.json",
            "generated_features.jsonl",
            "collection_receipt.json",
            "slot_events.jsonl",
        )
    ]
    paths.extend([s.DIRECTORY / "scalers.json", predecessor.DIRECTORY / "reference_features.jsonl"])
    receipt = dict(
        inputs=bindings(root, paths),
        analysis_sha256=hash_file(directory / "analysis.json"),
        method_source_commit=read_json(directory / "execution_freeze.json")["recorded_git_commit"],
    )
    publish(directory / "analysis_receipt.json", receipt)
    return dict(
        cells=len(result["cells"]),
        inferential_endpoints=len(result["endpoints"]),
        output=(p.DIRECTORY / "analysis.json").as_posix(),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("combine", "generated", "analysis"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.stage == "combine":
        print(json.dumps(combine(root), indent=2))
        return
    result = (
        analysis(root, check=args.check)
        if args.stage == "analysis"
        else measure(root, args.stage, check=args.check)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
