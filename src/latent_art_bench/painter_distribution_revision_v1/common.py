"""Read sealed numeric inputs without opening artwork or generation responses."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.painter_distribution_study_v1 import study
from latent_art_bench.painter_feature_generation_v2.artifacts import events
from latent_art_bench.painter_feature_generation_v2.statistics import transform

NAMESPACE = "painter_distribution_revision_v1"
RUN_ID = "pdrv1-numeric-20260907"
DIRECTORY = Path("data/manifests") / NAMESPACE / RUN_ID
REPORT = Path("reports") / NAMESPACE / RUN_ID
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
BASE = Path("data/manifests/painter_distribution_study_v1")
MAIN = BASE / "pdsv1-main-20260906"
REFERENCE = BASE / "pdsv1-main-parallel-20260906/reference_features.jsonl"
GENERATED = BASE / "pdsv1-main-immediate-20260907/generated_features.jsonl"
OLD_DEVELOPMENT = Path(
    "data/manifests/painter_feature_generation_v2/pfg2-method-20260905/development_features.jsonl"
)
GENERATION_COMPONENTS = (
    "pdsv1-main-parallel-20260906",
    "pdsv1-main-continuation-20260906",
    "pdsv1-main-recovery-20260907",
    "pdsv1-main-recovery-20260907-retry-slot0108",
    "pdsv1-main-immediate-20260907",
)
INPUT_PATHS = (
    REFERENCE,
    GENERATED,
    MAIN / "scalers.json",
    MAIN / "main_freeze.json",
    MAIN / "development_features.jsonl",
    MAIN / "development.jsonl",
    MAIN / "reference_panel.jsonl",
    MAIN / "requests.jsonl",
    OLD_DEVELOPMENT,
    BASE / "pdsv1-reference-candidates-20260906/candidates.jsonl",
    BASE / "pdsv1-reference-candidates-20260906/screening.jsonl",
    BASE / "pdsv1-reference-delivery-r2-20260906/deliveries.jsonl",
    BASE / "pdsv1-reference-coding-20260906/annotations.jsonl",
    BASE / "pdsv1-main-immediate-20260907/collection_receipt.json",
    BASE / "pdsv1-analysis-20260907/analysis.json",
    BASE / "pdsv1-analysis-20260907/analysis_receipt.json",
    Path("configs/painter_distribution_study_v1/research.json"),
    Path("docs/reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md"),
) + tuple(BASE / c / "generation_events.jsonl" for c in GENERATION_COMPONENTS)


def validate_rows(rows, stage):
    identities = [(r["pipeline"], r["image_id"]) for r in rows]
    if len(set(identities)) != len(identities):
        raise ValueError(f"duplicate {stage} image/pipeline")
    for row in rows:
        if row["status"] != "measured" or row["pipeline"] not in study.PIPELINES:
            raise ValueError(f"unexpected {stage} measurement status or pipeline")
        for field in ("values", "scaled"):
            values = np.asarray(row[field], dtype=float)
            if values.shape != (31,) or not np.isfinite(values).all():
                raise ValueError(f"invalid {stage} {field}")


def load(root):
    """Return JSON-native annotated vectors and provenance-only nuisance attributes."""
    scalers = read_json(root / MAIN / "scalers.json")
    panel = {r["work_id"]: r for r in read_jsonl(root / MAIN / "reference_panel.jsonl")}
    deliveries = {
        r["work_id"]: r
        for r in read_jsonl(root / BASE / "pdsv1-reference-delivery-r2-20260906/deliveries.jsonl")
    }
    terminals, timings = {}, {}
    for component in GENERATION_COMPONENTS:
        for event in events(root / BASE / component / "generation_events.jsonl"):
            request_id = event["request_id"]
            if event["kind"] == "attempt":
                if request_id in timings:
                    raise ValueError("duplicate physical attempt identity")
                timings[request_id] = dict(
                    started_at_utc=event["at_utc"], component=component, route=event["route"]
                )
            elif event["kind"] == "terminal":
                if request_id in terminals or request_id not in timings:
                    raise ValueError("unpaired or repeated terminal request")
                terminals[request_id] = event
                timings[request_id].update(
                    completed_at_utc=event["at_utc"], status=event["status"],
                    latency_seconds=event.get("latency_seconds"),
                )
            else:
                raise ValueError("unexpected generation event kind")
    reference, generated = events(root / REFERENCE), events(root / GENERATED)
    wanted = {r["image_id"] for r in read_jsonl(root / MAIN / "development.jsonl")}
    development = [
        dict(r, pipeline="primary512")
        for r in read_jsonl(root / OLD_DEVELOPMENT)
        if r["role"] == "development" and r["image_id"] in wanted
    ] + events(root / MAIN / "development_features.jsonl")
    for rows in (reference, generated, development):
        for row in rows:
            row["scaled"] = transform(
                np.asarray(row["values"]), scalers[row["pipeline"]]["scaler"]
            ).tolist()
            n = row["normalization"]
            row.update(width=n["normalized_width"], height=n["normalized_height"])
    for row in reference:
        p, d = panel[row["image_id"]], deliveries[row["image_id"]]
        collections = sorted(set(d.get("collections", [])))
        row.update(
            source_id="collection:" + "+".join(collections) if collections else "unknown",
            source_basis="recorded holding collection proxy, not a photographic workflow",
            capture_workflow=d.get("capture_workflow", "unresolved"),
            border_flag=bool(p.get("visible_border_note")),
            visible_border_note=p.get("visible_border_note"),
            parent_width=d["expected_width"], parent_height=d["expected_height"],
            delivered_width=d["delivery_width"], delivered_height=d["delivery_height"],
            file_extension=Path(d["commons_filename"]).suffix.lower(),
            image_format="unknown", subject_subcategory=p.get("subject_subcategory"),
            content_description=p.get("content_description"),
        )
    for row in generated:
        outcome = terminals[row["selected_request_id"]]
        observed = outcome["observed"]
        if outcome["status"] != "image_returned" or observed["image_sha256"] != row["raw_sha256"]:
            raise ValueError("generated vector does not match selected terminal image identity")
        row.update(
            source_id="route:" + row["route"],
            capture_workflow="not_applicable_generated",
            border_flag=None,
            image_format=observed["format"],
            reported_quality=observed.get("reported", {}).get("quality"),
            slot_id=row["request_id"],
        )
    for name, rows, count in (
        ("reference", reference, 70), ("generated", generated, 1006),
        ("development", development, 221),
    ):
        validate_rows(rows, name)
        if Counter(r["pipeline"] for r in rows) != dict.fromkeys(study.PIPELINES, count):
            raise ValueError(f"unexpected {name} pipeline counts")
    requests = read_jsonl(root / MAIN / "requests.jsonl")
    if len(requests) != 1008 or len(terminals) != 1009 or set(terminals) != set(timings):
        raise ValueError("research request accounting changed")
    return dict(
        reference=reference, generated=generated, development=development,
        requests=requests, timings=timings, terminals=terminals,
        targets=read_json(root / MAIN / "main_freeze.json")["content_weights"],
        scalers=scalers,
        config=read_json(root / "configs/painter_distribution_study_v1/research.json"),
        old_analysis=read_json(root / BASE / "pdsv1-analysis-20260907/analysis.json"),
        collection_receipt=read_json(
            root / BASE / "pdsv1-main-immediate-20260907/collection_receipt.json"
        ),
    )
