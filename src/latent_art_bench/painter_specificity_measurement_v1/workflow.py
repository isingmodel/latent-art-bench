"""Measure and replay the intended valid reference panel, preserving source freezes."""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import json
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_reference_v1 import analysis as ref_analysis
from latent_art_bench.painter_specificity_v1.workflow import measure_one, now
from latent_art_bench.painter_specificity_v2 import study as s
from latent_art_bench.painter_specificity_v2.analysis import compute
from latent_art_bench.painter_specificity_v2.workflow import verify as verify_collection_source

NS = "painter_specificity_measurement_v1"
DATA = s.ROOT / "data/manifests" / NS / "psmv1-20260911"
COUNTS = dict(zip(s.ARTISTS, (297, 106, 141, 105)))
EXCLUDED = {"wikidata:Q19820260", "wikidata:Q26846569", "wikidata:Q63986323", "wikidata:Q98447005"}


def reference_records():
    rows = s.rows(s.REF)
    valid = [r for r in rows if r["status"] == "measured"]
    excluded = {r["image_id"] for r in rows if r["status"] != "measured"}
    if (
        len(rows) != 653
        or excluded != EXCLUDED
        or len(valid) != 649
        or len({r["image_id"] for r in valid}) != 649
        or Counter(r["painter_id"] for r in valid) != COUNTS
        or any(len(r["values"]) != 31 for r in valid)
    ):
        raise ValueError("reference membership differs from the declared 649-work panel")
    return valid


def freeze():
    reference_records()
    paths = [
        s.ROOT / "studies" / NS / "CORRECTION.md",
        Path(__file__),
        s.ROOT / "tests" / NS / "test_membership.py",
        s.REF,
        s.DATA / "freeze.json",
        ref_analysis.DATA / "freeze.json",
    ]
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--", *map(str, paths)], text=True
    )
    if dirty.strip():
        raise ValueError("commit corrected reader before freezing")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    s.write_new(
        DATA / "freeze.json",
        dict(
            recorded_git_commit=commit,
            created_at=now(),
            inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths],
        ),
    )


def verify():
    verify_collection_source()
    for freeze_path in (DATA / "freeze.json", ref_analysis.DATA / "freeze.json"):
        for r in s.read(freeze_path)["inputs"]:
            if s.sha(s.ROOT / r["path"]) != r["sha256"]:
                raise ValueError("measurement/reference adapter binding changed: " + r["path"])


def measure():
    verify()
    receipt = s.read(s.DATA / "collection.json")
    if (
        receipt["status"] != "completed"
        or s.sha(s.DATA / "attempts.jsonl") != receipt["ledger_sha256"]
    ):
        raise ValueError("collection is not intact and terminal")
    old = reference_records()
    # Validate all known reference paths before beginning the one-shot extraction.
    lookup = {r["work_id"]: r for r in s.rows(s.ACQUISITIONS)}
    items = []
    for r in old:
        original = lookup[r["image_id"]]
        if (
            original["raw_sha256"] != r["raw_sha256"]
            or not (s.ROOT / original["raw_path"]).is_file()
        ):
            raise ValueError("reference raw ancestry/path mismatch")
        items.append(
            dict(
                id=r["image_id"],
                success=True,
                image_path=original["raw_path"],
                image_sha256=r["raw_sha256"],
            )
        )
    with (
        (s.DATA / "measurements.jsonl").open("x") as stream,
        futures.ProcessPoolExecutor(max_workers=4) as pool,
    ):
        for row in pool.map(measure_one, receipt["outcomes"]):
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    with (
        (s.DATA / "reference_windows.jsonl").open("x") as stream,
        futures.ProcessPoolExecutor(max_workers=4) as pool,
    ):
        for row, original in zip(pool.map(measure_one, items), old):
            if row["status"] == "measured" and not np.allclose(
                row["values"], original["values"], atol=1e-10, rtol=1e-10
            ):
                raise ValueError("reference primary re-extraction differs")
            row["painter_id"] = original["painter_id"]
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    s.write_new(
        s.DATA / "measurement_receipt.json",
        dict(
            ended_at=now(),
            collection_sha256=s.sha(s.DATA / "collection.json"),
            measurements_sha256=s.sha(s.DATA / "measurements.jsonl"),
            reference_windows_sha256=s.sha(s.DATA / "reference_windows.jsonl"),
            reader_freeze_sha256=s.sha(DATA / "freeze.json"),
            reference_count=649,
            excluded_historical_failure_ids=sorted(EXCLUDED),
        ),
    )


def load(square=False):
    verify()
    receipt = s.read(s.DATA / "measurement_receipt.json")
    if receipt["reader_freeze_sha256"] != s.sha(DATA / "freeze.json"):
        raise ValueError("reader freeze differs")
    for name in ("collection", "measurements", "reference_windows"):
        ext = "json" if name == "collection" else "jsonl"
        if s.sha(s.DATA / f"{name}.{ext}") != receipt[f"{name}_sha256"]:
            raise ValueError("measurement binding changed")
    x = np.full((6, len(s.SCENES), 2, 6, 31), np.nan)
    scaler = s.read(s.SCALER)
    key = "square_values" if square else "values"
    requests = {r["id"]: r for r in s.rows(s.DATA / "requests.jsonl")}
    seen = set()
    rows = s.rows(s.DATA / "measurements.jsonl")
    if len(rows) != len(requests):
        raise ValueError("measurement census incomplete")
    for row in rows:
        if row["id"] in seen:
            raise ValueError("duplicate measurement")
        seen.add(row["id"])
        r = requests[row["id"]]
        if row["status"] == "measured":
            x[s.MODELS.index(r["model"]), r["scene"], r["repeat"], s.ARMS.index(r["arm"])] = (
                transform(np.array(row[key]), scaler)
            )
    old = reference_records()
    records = s.rows(s.DATA / "reference_windows.jsonl") if square else old
    if square and {r["id"] for r in records} != {r["image_id"] for r in old}:
        raise ValueError("square reference membership changed")
    if len(records) != 649 or any(r["status"] != "measured" for r in records):
        raise ValueError("reference measurement incomplete")
    refs = [
        transform(np.array([r[key] for r in records if r["painter_id"] == a]), scaler)
        for a in s.ARTISTS
    ]
    return x, refs


def analyze(square=False, reference=False, check=False):
    x, refs = load(square)
    if reference:
        frame = {r["work_id"]: r["content_class"] for r in s.rows(ref_analysis.FRAME)}
        records = reference_records()
        labels = [
            [frame[r["image_id"]] for r in records if r["painter_id"] == a] for a in s.ARTISTS
        ]
        result = ref_analysis.evaluate(x, refs, labels)
        result["measurement_receipt_sha256"] = s.sha(s.DATA / "measurement_receipt.json")
        result["freeze_sha256"] = s.sha(ref_analysis.DATA / "freeze.json")
        target = ref_analysis.DATA
    else:
        result = compute(x, refs)
        target = s.DATA
    path = target / ("analysis_square.json" if square else "analysis.json")
    if check:
        if result != s.read(path):
            raise ValueError("exact numerical replay differs")
        print("Exact numerical replay passed")
    else:
        s.write_new(path, result)
        print("Analysis saved")


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("freeze", "verify", "measure", "analyze"))
    parser.add_argument("--square", action="store_true")
    parser.add_argument("--reference", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.action == "analyze":
        analyze(args.square, args.reference, args.check)
    else:
        globals()[args.action]()


if __name__ == "__main__":
    main()
