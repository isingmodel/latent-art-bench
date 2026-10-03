"""Fixed allocation for the v3 collection: September's scenes, routes and payloads; ten arms.

Only the painter names, the arm count and the randomization seed differ from ``psv2-20260911``.
The free and generic payloads are byte-identical to September's for the same model and scene.
"""

from __future__ import annotations

import numpy as np

from latent_art_bench.painter_specificity_v1 import study as first
from latent_art_bench.painter_specificity_v1.study import read, rows, sha, write_new  # noqa: F401
from latent_art_bench.painter_specificity_v2 import study as second
from latent_art_bench.painter_specificity_v3.panel import GROUPS, PAINTERS

ROOT = first.ROOT
NS = "painter_specificity_v3"
RUN = "psv3-r1"
DATA = ROOT / "data/manifests" / NS / RUN
WORK = ROOT / "research_workspace" / NS / RUN
URL = second.URL
MODELS, TITLES, PROVIDERS = first.MODELS, first.TITLES, first.PROVIDERS
SCENES, SELECTED_SCENES = second.SCENES, second.SELECTED_SCENES
ARTISTS = tuple(p.painter_id for p in PAINTERS)
NAMES = tuple(p.name for p in PAINTERS)
ARMS = ("free", "generic", *ARTISTS)
# Six-arm slices that the four-painter analysis functions read unchanged, one per group.
GROUP_ARMS = {g: (0, 1, *(2 + i for i, p in enumerate(PAINTERS) if p.group == g))
              for g in GROUPS}
SEED = 2026100217
PREDECESSOR = ROOT / "data/manifests/painter_specificity_v2/psv2-20260911/collection.json"
RESERVE = 5.0


def clause(arm: str) -> str:
    if arm == "free":
        return ""
    if arm == "generic":
        return "Render as an oil painting. "
    return f"Render as an oil painting in the style of {NAMES[ARTISTS.index(arm)]}. "


def payload(model: str, brief: str, arm: str) -> dict:
    """September's route fields (``psv1`` payload, ``psv2`` OpenAI override), new clause."""
    result = first.payload(model, brief, "free")
    result["prompt"] = clause(arm) + brief + " No text or frame."
    if model.startswith("gpt-image"):
        result = dict(model="openai/" + model, prompt=result["prompt"], n=1, aspect_ratio="1:1",
                      quality="medium", background="opaque",
                      provider=dict(only=["openai"], allow_fallbacks=False))
    return result


def assignments() -> list[dict]:
    """Scenes in random order; within a scene, all model x arm x repeat requests interleaved."""
    rng = np.random.default_rng(SEED)
    result = []
    for scene in rng.permutation(len(SCENES)):
        content, brief = SCENES[scene]
        block = [dict(scene=int(scene), original_scene=SELECTED_SCENES[scene], content=content,
                      model=model, arm=arm, repeat=repeat, payload=payload(model, brief, arm))
                 for model in MODELS for arm in ARMS for repeat in (0, 1)]
        for index in rng.permutation(len(block)):
            result.append(dict(id=f"psv3-{len(result):04d}", **block[index]))
    return result


def accounted(events: list[dict], baseline: float) -> float:
    """Cumulative spend: baseline, plus a $5 reservation per start until its charge is known."""
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
    return baseline + sum(amounts.values())


def forecast() -> dict:
    """Expected charge at September's observed mean cost per configuration."""
    model_of = {r["id"]: r["model"] for r in rows(PREDECESSOR.with_name("requests.jsonl"))}
    costs: dict[str, list[float]] = {m: [] for m in MODELS}
    for outcome in read(PREDECESSOR)["outcomes"]:
        if outcome["cost_usd"] is not None:
            costs[model_of[outcome["id"]]].append(outcome["cost_usd"])
    mean = {m: float(np.mean(v)) for m, v in costs.items()}
    per_model = len(SCENES) * len(ARMS) * 2
    return dict(images=per_model * len(MODELS), mean_cost_usd=mean,
                expected_usd=float(sum(mean[m] * per_model for m in MODELS)))
