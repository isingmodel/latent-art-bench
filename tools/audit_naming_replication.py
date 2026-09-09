"""Read-only, post-collection integrity descriptions; never filter or change inference.

Run only after both receipts exist:
    uv run --locked python tools/audit_naming_replication.py
JSON goes to stdout. This script creates no report or other file and opens no pixels.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import events, verify_bindings
from latent_art_bench.painter_naming_replication_v1 import common, workflow

OLD_NAMING = Path("data/manifests/painter_distribution_study_v1") / (
    "pdsv1-main-immediate-20260907/generated_features.jsonl"
)
OLD_NAMING_FREEZE = Path("data/manifests/painter_distribution_study_v1") / (
    "pdsv1-analysis-20260907/publication_freeze.json"
)
OLD_PALETTE = Path("data/manifests/painter_responsiveness_v2") / (
    "prv2-oauth-recovery-20260908/generated_features.jsonl"
)
OLD_PALETTE_RECEIPT = OLD_PALETTE.parent / "analysis_receipt.json"


def duplicates(images, old_cohorts, *, normalized=False):
    """Images are physical returned bytes, not repeated feature-pipeline records."""
    fields = (("normalized_sha256", "normalized_width", "normalized_height") if normalized
              else ("image_sha256",))

    def key(row):
        return tuple(row[f] for f in fields)

    grouped = defaultdict(list)
    for row in images:
        grouped[key(row)].append(row)
    within = [dict(zip(fields, h), images=items) for h, items in sorted(grouped.items())
              if len(items) > 1]
    cross = {}
    for name, old in old_cohorts.items():
        lookup = defaultdict(list)
        for row in old:
            lookup[key(row)].append(row["image_id"])
        matches = [dict(zip(fields, h), new_images=items, old_image_ids=lookup[h])
                   for h, items in sorted(grouped.items()) if h in lookup]
        cross[name] = dict(old_images=len(old), old_unique_hash_and_shape_keys=len(lookup),
                           matched_new_images=sum(len(r["new_images"]) for r in matches),
                           matches=matches)
    return dict(compared_images=len(images), unique_hash_and_shape_keys=len(grouped),
                within_new_duplicate_groups=within, cross_cohort=cross,
                basis="primary512 normalized float64 RGB array plus shape" if normalized
                else "encoded raw image SHA256",
                scope="Exact duplicates only. Raw file bytes can differ only in metadata. "
                "Normalized arrays are after ICC/EXIF conversion and short-side512 resizing, "
                "not original decoded pixels. Neither comparison proves absence of "
                "near-duplicates, novel content or independent backend states. "
                "Old cohorts are the 1,006 Study 1 and 192 primary Study 2 images; "
                "the ancillary 49-image predecessor is excluded.")


def delivery_counts(requests, slots):
    """Keep complete requested/reported/decoded joint profiles, including missing fields."""
    groups = defaultdict(list)
    for request, slot in zip(requests, slots, strict=True):
        if request["request_id"] != slot["request_id"]:
            raise ValueError("slot identities do not match")
        groups[request["experiment"], request["arm"]].append((request, slot))
    result = []
    for (experiment, arm), members in sorted(groups.items()):
        profiles = Counter()
        for request, slot in members:
            observed = slot.get("observed") or {}
            payload = request["payload"]
            profile = dict(
                polarity=request.get("polarity"), status=slot["status"],
                requested={k: payload.get(k) for k in
                           ("size", "aspect_ratio", "quality", "output_format")},
                requested_fields_present=[k for k in
                                          ("size", "aspect_ratio", "quality", "output_format")
                                          if k in payload],
                decoded={k: observed.get(k) for k in ("width", "height", "format", "mode")},
                reported=observed.get("reported"),
            )
            profiles[json.dumps(profile, sort_keys=True)] += 1
        result.append(dict(experiment=experiment, arm=arm, planned=len(members),
                           statuses=dict(Counter(s["status"] for _, s in members)),
                           profiles=[dict(json.loads(p), count=n)
                                     for p, n in sorted(profiles.items())]))
    return result


def ranges(values):
    return dict(count=len(values), minimum=min(values) if values else None,
                median=median(values) if values else None, maximum=max(values) if values else None)


def timing_summary(ledger, config, receipt):
    intents, terminals, outstanding = {}, {}, set()
    maximum_outstanding = 0
    for row in ledger:
        key = row["request_id"], row["attempt"]
        if row["kind"] == "attempt":
            if key in intents:
                raise ValueError("duplicate transport intent")
            intents[key] = row
            outstanding.add(key)
            maximum_outstanding = max(maximum_outstanding, len(outstanding))
        elif row["kind"] == "terminal":
            if key not in outstanding or key in terminals:
                raise ValueError("unpaired transport terminal")
            terminals[key] = row
            outstanding.remove(key)
        else:
            raise ValueError("unknown transport event")
    if outstanding:
        raise ValueError("unresolved transport intents")
    posts, unknown, cancelled = [], [], []
    for key, row in terminals.items():
        if row.get("post_started") is False:
            cancelled.append(dict(request_id=key[0], attempt=key[1]))
            continue
        fields = ("transport_started_monotonic", "latency_seconds", "post_started_at_utc")
        if row.get("post_started") is not True or any(row.get(f) is None for f in fields):
            unknown.append(dict(request_id=key[0], attempt=key[1]))
            continue
        start, latency = row[fields[0]], row[fields[1]]
        if not all(math.isfinite(v) for v in (start, latency)) or latency < 0:
            raise ValueError("invalid monotonic timing")
        post_time = datetime.fromisoformat(row[fields[2]])
        if post_time.tzinfo is None:
            raise ValueError("unqualified wall-clock timestamp")
        posts.append(dict(request_id=key[0], attempt=key[1],
                          dispatch_ticket=intents[key]["dispatch_ticket"],
                          slot_sequence=row["slot_sequence"], route=row["route"],
                          admitted_monotonic=start, operation_ended_monotonic=start + latency,
                          pre_post_utc=row[fields[2]], pre_post_epoch=post_time.timestamp(),
                          latency_seconds=latency, status=row["status"]))
    posts.sort(key=lambda r: r["admitted_monotonic"])
    gaps = [b["admitted_monotonic"] - a["admitted_monotonic"]
            for a, b in zip(posts, posts[1:])]
    wall_gaps = [b["pre_post_epoch"] - a["pre_post_epoch"] for a, b in zip(posts, posts[1:])]
    nonempty = [r for r in posts if r["latency_seconds"] > 0]
    intervals = [(r["admitted_monotonic"], 1) for r in nonempty]
    intervals += [(r["operation_ended_monotonic"], -1) for r in nonempty]
    active, maximum_active = 0, 0
    for _, change in sorted(intervals):  # Completion before admission at an equal instant.
        active += change
        maximum_active = max(maximum_active, active)
    tickets = [r["dispatch_ticket"] for r in posts]
    initial_sequences = [r["slot_sequence"] for r in posts if r["attempt"] == 1]
    minimum = config["minimum_start_interval_seconds"]
    spacing = [dict(previous=posts[i]["request_id"], current=posts[i + 1]["request_id"],
                    seconds=gap) for i, gap in enumerate(gaps) if gap < minimum - 1e-9]
    return dict(
        attempts=len(intents), timed_posts=len(posts), cancelled_before_post=cancelled,
        missing_timing=unknown, admitted_start_spacing_seconds=ranges(gaps),
        pre_post_wall_clock_spacing_seconds=ranges(wall_gaps),
        latency_seconds=ranges([r["latency_seconds"] for r in posts]),
        spacing_below_configured_minimum=spacing,
        timing_complete=not unknown,
        dispatch_ticket_order_preserved=None if unknown else (
            tickets == sorted(tickets) and len(set(tickets)) == len(tickets)),
        first_attempt_slot_order_preserved=(None if unknown
                                            else initial_sequences == sorted(initial_sequences)),
        maximum_outstanding_ledger_intents=maximum_outstanding,
        maximum_timed_operations=maximum_active,
        configured_maximum_in_flight=config["maximum_in_flight"],
        configured_minimum_start_interval_seconds=minimum,
        receipt_elapsed_seconds=receipt["elapsed_seconds"],
        receipt_duration_contract_met=receipt["duration_contract_met"],
        observed_operation_span_seconds=(max(r["operation_ended_monotonic"] for r in posts)
                                         - posts[0]["admitted_monotonic"]) if posts else None,
        first_pre_post_utc=posts[0]["pre_post_utc"] if posts else None,
        receipt_ended_at_utc=receipt["ended_at_utc"], posts=posts,
        scope="Monotonic starts are gate admission, not observed socket writes. UTC is "
        "recorded immediately before HTTP-client construction. Timed operations include "
        "transport, response inspection and retention; their concurrency bounds actual "
        "network concurrency but does not measure provider execution. Missing timings "
        "remain unknown; UTC clock behavior is reported separately from monotonic pacing.",
    )


def historical_images(root):
    freeze = read_json(root / OLD_NAMING_FREEZE)
    bound = [r for r in freeze["inputs"] if r["path"] == OLD_NAMING.as_posix()]
    if len(bound) != 1:
        raise ValueError("original Study 1 feature binding is absent")
    verify_bindings(root, bound)
    palette_receipt = read_json(root / OLD_PALETTE_RECEIPT)
    if hash_file(root / OLD_PALETTE) != palette_receipt["features_sha256"]:
        raise ValueError("original Study 2 feature binding changed")
    result = {}
    for name, rows, count in (("study1", events(root / OLD_NAMING), 1006),
                              ("study2_primary", read_jsonl(root / OLD_PALETTE), 192)):
        selected = [r for r in rows if r["pipeline"] == "primary512" and r["status"] == "measured"]
        if len(selected) != count or len({r["image_id"] for r in selected}) != count:
            raise ValueError("original primary cohort identities changed")
        result[name] = [dict(image_id=r["image_id"],
                             image_sha256=r.get("raw_sha256") or r["observed"]["image_sha256"],
                             **normalization_identity(r))
                        for r in selected]
    return result


def normalization_identity(row):
    metadata = row["normalization"]
    if metadata["short_side"] != 512 or metadata["crop_fraction"] != 0:
        raise ValueError("normalized duplicate comparison requires unchanged primary512 geometry")
    return {k: metadata[k] for k in
            ("normalized_sha256", "normalized_width", "normalized_height")}


def audit(root):
    root = Path(root)
    directory = common.directory(common.RUN_ID)
    # Both guards precede any access to the new collection ledger or measured outcomes.
    required = (directory / "collection_receipt.json", directory / "measurement_receipt.json")
    if not all((root / p).is_file() for p in required):
        raise ValueError("wait for both terminal collection and measurement receipts")
    freeze, requests, slots, terminals, receipt = workflow.collection_inputs(root, common.RUN_ID)
    measurement = read_json(root / required[1])
    if measurement["collection_receipt_sha256"] != hash_file(root / required[0]):
        raise ValueError("measurement receipt collection binding changed")
    verify_bindings(root, measurement["outputs"])
    rows = read_jsonl(root / directory / "measurements.jsonl")
    primary = [r for r in rows if r["pipeline"] == "primary512"]
    if len(primary) != len(requests) or len({r["request_id"] for r in primary}) != len(requests):
        raise ValueError("complete unique primary measurement slots required")
    measured = {r["request_id"]: r for r in primary}
    for slot in slots:
        if slot["status"] == "image_returned":
            row = measured[slot["request_id"]]
            if row["raw_sha256"] != slot["observed"]["image_sha256"]:
                raise ValueError("measured raw image hash differs from delivered hash")
    lookup = {r["request_id"]: r for r in requests}
    images = []
    for (request_id, attempt), row in terminals.items():
        if row.get("observed") and row["observed"].get("image_sha256"):
            images.append(dict(request_id=request_id, attempt=attempt, status=row["status"],
                               experiment=lookup[request_id]["experiment"],
                               arm=lookup[request_id]["arm"],
                               image_sha256=row["observed"]["image_sha256"]))
    normalized = [dict(image_id=r["image_id"], request_id=r["request_id"],
                        image_sha256=r["raw_sha256"],
                        experiment=r["experiment"], arm=r["arm"], **normalization_identity(r))
                  for r in primary if r["status"] == "measured"]
    historical = historical_images(root)
    paths = [directory / p for p in ("freeze.json", "planned_requests.jsonl",
             "generation_events.jsonl", "slot_outcomes.jsonl", "collection_receipt.json",
             "measurement_receipt.json", "measurements.jsonl")]
    paths += [OLD_NAMING, OLD_NAMING_FREEZE, OLD_PALETTE, OLD_PALETTE_RECEIPT]
    return dict(
        schema="painter-naming-replication-descriptive-integrity/1", run_id=common.RUN_ID,
        scope="Post-result metadata audit. No exclusions, relabeling, inference changes, "
        "pixel rereads or backend-independence claim. All terminal observed image hashes "
        "are included, even if a delivery is ineligible for analysis.",
        inputs=[dict(path=p.as_posix(), sha256=hash_file(root / p)) for p in paths],
        script_sha256=hash_file(Path(__file__)),
        raw_duplicate_audit=duplicates(images, historical),
        normalized_array_duplicate_audit=duplicates(normalized, historical, normalized=True),
        normalized_array_unavailable=[dict(request_id=r["request_id"], status=r["status"])
                                      for r in primary if r["status"] != "measured"],
        delivery_counts=delivery_counts(requests, slots),
        timing=timing_summary(events(root / directory / "generation_events.jsonl"),
                              freeze["config"], receipt),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(audit(args.root), indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
