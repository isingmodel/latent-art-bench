"""Descriptive execution sensitivities; never reinterpret assigned batches as sessions."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import numpy as np

from latent_art_bench.painter_distribution_study_v1.analysis import paired


def group_key(row):
    return row["route"], row["painter_id"], row["brief_id"], row["repetition"]


def group_records(requests, timings):
    groups = defaultdict(list)
    for row in requests:
        groups[group_key(row)].append(row)
    result = []
    for key, slots in sorted(groups.items()):
        starts = [timings[r["request_id"]] for r in slots]
        seconds = [datetime.fromisoformat(r["started_at_utc"]).timestamp() for r in starts]
        result.append(dict(
            route=key[0], painter_id=key[1], brief_id=key[2], repetition=key[3],
            request_ids=[r["request_id"] for r in slots],
            condition_order=[r["condition"] for r in slots],
            start_gap_seconds=max(seconds) - min(seconds),
            components=sorted({r["component"] for r in starts}),
            crosses_component=len({r["component"] for r in starts}) > 1,
            gap_above_120_seconds=max(seconds) - min(seconds) > 120,
        ))
    return result


def analyze(bundle):
    records = group_records(bundle["requests"], bundle["timings"])
    boundaries = {group_key(r) for r in records if r["crosses_component"]}
    long_gaps = {group_key(r) for r in records if r["gap_above_120_seconds"]}
    generated = [r for r in bundle["generated"] if r["pipeline"] == "primary512"]
    reference = [r for r in bundle["reference"] if r["pipeline"] == "primary512"]
    retry_groups = {group_key(r) for r in generated if not r["initial_only_eligible"]}
    strategies = {
        "all_selected": set(),
        "exclude_retry_groups": retry_groups,
        "exclude_component_boundaries": boundaries,
        "exclude_gap_above_120_seconds": long_gaps,
        "exclude_boundaries_and_retry_groups": boundaries | retry_groups,
    }
    contrasts = []
    old = bundle["old_analysis"]["endpoints"]
    for strategy, excluded in strategies.items():
        fake = [r for r in generated if group_key(r) not in excluded]
        for endpoint in old:
            painter = endpoint["painter_id"]
            result = paired(
                [r for r in reference if r["painter_id"] == painter], fake,
                bundle["targets"][painter], endpoint["route"], painter,
                endpoint["before"], endpoint["after"], bundle["config"],
                endpoint["endpoint_index"], run_test=False,
            )
            contrasts.append(dict(
                strategy=strategy, endpoint_index=endpoint["endpoint_index"],
                painter_id=painter, route=endpoint["route"], before=endpoint["before"],
                after=endpoint["after"], status=result["status"], pairs=result["pairs"],
                distinct_briefs=result["distinct_briefs"], estimate=result.get("estimate"),
                excluded_groups=[list(k) for k in sorted(excluded)],
                matched_image_ids=[
                    [r["before_image_id"], r["after_image_id"]]
                    for r in result.get("contributions", [])
                ],
            ))
    start_times = [datetime.fromisoformat(t["started_at_utc"]).timestamp()
                   for t in bundle["timings"].values()]
    end_times = [datetime.fromisoformat(t["completed_at_utc"]).timestamp()
                 for t in bundle["timings"].values()]
    routes = sorted({r["route"] for r in records})
    return dict(
        groups=records, contrasts=contrasts,
        physical_research_attempts=len(bundle["timings"]),
        elapsed_hours=(max(end_times) - min(start_times)) / 3600,
        route_group_gaps=[dict(
            route=route,
            median_seconds=float(np.median([r["start_gap_seconds"] for r in records
                                             if r["route"] == route])),
            maximum_seconds=max(r["start_gap_seconds"] for r in records if r["route"] == route),
        ) for route in routes],
        disposition_records=[dict(
            request_id=key, status=t["status"], status_code=t["status_code"],
            cost_usd=t["cost_usd"], reported_quality=(t.get("observed") or {}).get(
                "reported", {}).get("quality"),
        ) for key, t in sorted(bundle["terminals"].items())],
        interpretation="Post-result deletions are sensitivities, not a causal repair or new test.",
    )
