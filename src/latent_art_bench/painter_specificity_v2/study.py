"""Versioned transport and accounting; unchanged scientific scene allocation."""

from __future__ import annotations

from latent_art_bench.painter_specificity_v1 import study as first
from latent_art_bench.painter_specificity_v1.study import (  # noqa: F401
    ACQUISITIONS,
    ARMS,
    ARTISTS,
    MODELS,
    NAMES,
    REF,
    ROOT,
    SCALER,
    TITLES,
    read,
    rows,
    sha,
    write_new,
)

NS = "painter_specificity_v2"
RUN = "psv2-20260911"
DATA = ROOT / "data/manifests" / NS / RUN
WORK = ROOT / "research_workspace" / NS / RUN
REPORT = ROOT / "reports" / NS / RUN
URL = "https://openrouter.ai/api/v1/images"
BASELINE = 68.507350000
RESERVE = 5.0
CEILING = 120.0

# Omit the final land and mixed brief before observing any feature outcomes.
SELECTED_SCENES = tuple(i for i in range(16) if i not in (11, 15))
SCENES = tuple(first.SCENES[i] for i in SELECTED_SCENES)


def assignments():
    items = [r for r in first.assignments() if r["scene"] in SELECTED_SCENES]
    for r in items:
        r["original_scene"] = r["scene"]
        r["scene"] = SELECTED_SCENES.index(r["scene"])
        r["id"] = r["id"].replace("psv1-", "psv2-")
        if r["model"].startswith("gpt-image"):
            old = r["payload"]
            r["payload"] = dict(
                model="openai/" + r["model"],
                prompt=old["prompt"],
                n=1,
                aspect_ratio="1:1",
                quality="medium",
                background="opaque",
                provider=dict(only=["openai"], allow_fallbacks=False),
            )
    return items


def accounted(events):
    amounts, settled = {}, set()
    for row in events:
        key = row["id"], row["attempt"]
        if row["kind"] == "start":
            if key in amounts:
                raise ValueError("duplicate attempt intent")
            amounts[key] = RESERVE
        elif row["kind"] == "end":
            if key not in amounts or key in settled:
                raise ValueError("terminal lacks unique intent")
            settled.add(key)
            cost = row["cost_usd"]
            if cost is not None:
                if not isinstance(cost, (int, float)) or not 0 <= cost < float("inf"):
                    raise ValueError("invalid charge")
                amounts[key] = cost
    return BASELINE + sum(amounts.values())
