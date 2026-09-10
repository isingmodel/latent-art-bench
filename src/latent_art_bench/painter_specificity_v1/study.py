"""Fixed allocation and portable source identities for the specificity experiment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
NS = "painter_specificity_v1"
RUN = "psv1-20260910"
DATA = ROOT / "data/manifests" / NS / RUN
WORK = ROOT / "research_workspace" / NS / RUN
REPORT = ROOT / "reports" / NS / RUN
REF = ROOT / (
    "data/manifests/painter_feature_generation_v2/pfg2-method-20260905/confirmation_features.jsonl"
)
SCALER = REF.with_name("scaler.json")
ACQUISITIONS = ROOT / (
    "data/manifests/painter_feature_generation_v2/pfg2-renderings-r2-20260905/acquisitions.jsonl"
)
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
NAMES = ("Claude Monet", "Alfred Sisley", "Camille Pissarro", "Paul Cezanne")
ARMS = ("free", "generic", *ARTISTS)
MODELS = (
    "gpt-image-1",
    "gpt-image-2",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image",
    "black-forest-labs/flux.2-max",
)
TITLES = (
    "GPT Image 1",
    "GPT Image 2",
    "GPT Image 2.5 Flare",
    "GPT Image 2.5 Sunburst",
    "Nano Banana 2",
    "FLUX.2 Max",
)
PROVIDERS = {
    "google/gemini-3.1-flash-image": "google-ai-studio",
    "black-forest-labs/flux.2-max": "black-forest-labs/us-3",
}
LOCAL_URL = "http://127.0.0.1:10533/v1/images/generations"
PAID_URL = "https://openrouter.ai/api/v1/images"
BASELINE = 67.5219185
CEILING = 120.0
RESERVE = 5.0
SCENES = (
    (
        "water",
        "A broad river bends past a gravel bank. Three tall trees stand on the far bank, "
        "with a low hill behind them under a pale overcast sky.",
    ),
    (
        "water",
        "A small pond lies between reeds and a grassy slope. A wooden landing extends "
        "from the left bank, with scattered clouds reflected on the water.",
    ),
    (
        "water",
        "A narrow canal passes beneath a low stone bridge. Garden walls line one side "
        "and leafy trees line the other in soft afternoon light.",
    ),
    (
        "water",
        "A quiet inlet meets a flat sandy shore. Two small boats rest near the water "
        "and distant headlands sit beneath a light grey sky.",
    ),
    (
        "built",
        "A village street curves past modest stone houses. A low wall and a single tree "
        "occupy the foreground, with hills visible beyond the roofs.",
    ),
    (
        "built",
        "A country house stands beside an orchard. A gravel path crosses the foreground "
        "and a small shed stands on the right under a clear morning sky.",
    ),
    (
        "built",
        "A square stone tower rises behind a cluster of low tiled roofs. An open field "
        "fills the foreground, with a few shrubs along a narrow footpath.",
    ),
    (
        "built",
        "A courtyard is enclosed by two simple farm buildings. A gate opens toward "
        "distant fields and a patch of sunlight falls across the bare ground.",
    ),
    (
        "land",
        "An open meadow slopes gently toward distant wooded hills. A narrow path crosses "
        "the grass and a few irregular clouds fill the upper sky.",
    ),
    (
        "land",
        "A rocky hillside carries scattered pine trees. A broad valley extends behind "
        "the foreground rocks, with distant mountains in hazy daylight.",
    ),
    (
        "land",
        "Rows of fruit trees stretch across a gently rising field. Tall grass borders "
        "the nearest row and a dark wood lies at the horizon.",
    ),
    (
        "land",
        "A dirt road climbs between two grassy banks. A solitary tree stands near the "
        "bend and distant fields are visible beneath broken cloud.",
    ),
    (
        "mixed",
        "A river passes a small village at the foot of a hill. A stone wall crosses "
        "the foreground, with open grass and two trees beside the water.",
    ),
    (
        "mixed",
        "A farmhouse stands above a shallow stream. A footbridge connects two grassy "
        "banks and an orchard spreads behind the house in diffuse daylight.",
    ),
    (
        "mixed",
        "A lakeside path passes a low stone building and a cluster of trees. Water "
        "occupies the left half and a gentle ridge crosses the background.",
    ),
    (
        "mixed",
        "A village lane reaches a small bridge over a canal. Vegetable gardens flank "
        "the lane, with a wooded slope behind the houses under a pale sky.",
    ),
)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def payload(model, scene, arm):
    clause = (
        ""
        if arm == "free"
        else (
            "Render as an oil painting. "
            if arm == "generic"
            else f"Render as an oil painting in the style of {NAMES[ARTISTS.index(arm)]}. "
        )
    )
    result = dict(model=model, prompt=clause + scene + " No text or frame.", n=1)
    if model in PROVIDERS:
        result.update(
            aspect_ratio="1:1", provider=dict(only=[PROVIDERS[model]], allow_fallbacks=False)
        )
        result.update(
            {"resolution": "1K"} if model.startswith("google/") else {"output_format": "png"}
        )
    else:
        result.update(size="1024x1024", quality="medium", output_format="png", background="opaque")
    return result


def assignments():
    rng = np.random.default_rng(2026091017)
    result = []
    for scene in rng.permutation(len(SCENES)):
        content, brief = SCENES[scene]
        block = [
            dict(
                scene=int(scene),
                content=content,
                model=model,
                arm=arm,
                repeat=repeat,
                payload=payload(model, brief, arm),
            )
            for model in MODELS
            for arm in ARMS
            for repeat in (0, 1)
        ]
        for index in rng.permutation(len(block)):
            result.append(dict(id=f"psv1-{len(result):04d}", **block[index]))
    return result
