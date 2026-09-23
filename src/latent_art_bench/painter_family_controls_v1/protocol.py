"""Exact proposed design, kept separate from every completed experiment.

These historical routes are not verified current availability or pricing. This
module constructs request descriptions; it contains no transport or credentials.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

NAMESPACE = "painter_family_controls_v1"
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
ARMS = ("free", "generic", "style_frame", "shared_family", *ARTISTS)
MODELS = (
    "gpt-image-1", "gpt-image-2", "gpt-image-2.5-flare", "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image", "black-forest-labs/flux.2-max",
)
SUFFIXES = {
    "free": "No text or frame.",
    "generic": "Render as an oil painting. No text or frame.",
    "style_frame": ("Render as an oil painting in the style of a generic oil painting. "
                    "No text or frame."),
    "shared_family": ("Render as an oil painting in the style of late-nineteenth-century "
                      "French Impressionist and Post-Impressionist painting. No text or frame."),
    "claude_monet": "Render as an oil painting in the style of Claude Monet. No text or frame.",
    "alfred_sisley": "Render as an oil painting in the style of Alfred Sisley. No text or frame.",
    "camille_pissarro": ("Render as an oil painting in the style of Camille Pissarro. "
                         "No text or frame."),
    "paul_cezanne": "Render as an oil painting in the style of Paul Cezanne. No text or frame.",
}
SCENES = (
    ("W1", "A shallow stream divides around a mossy gravel island. A bare branch crosses the "
     "foreground, and a distant reed bank lies beneath thin evening clouds."),
    ("W2", "A flooded pasture surrounds a row of short wooden fence posts. Low willow bushes "
     "stand on the right, and the water reflects a strip of pale morning sky."),
    ("W3", "A tidal pool lies between dark rounded rocks. A narrow band of open sea crosses "
     "the background beneath a bright, cloudless sky."),
    ("B1", "A low railway platform stands beside two empty tracks. A red brick goods shed is "
     "set back on the left, with a line of hills beyond the station."),
    ("B2", "A narrow staircase climbs between plaster garden walls. A wooden door stands "
     "halfway up, and a small patch of sky is visible above the roofs."),
    ("B3", "A roadside bakery has closed wooden shutters and a striped awning. The empty "
     "pavement slopes gently toward a row of bare trees."),
    ("L1", "A harvested field contains several small stacks of straw. The rows run diagonally "
     "toward a distant belt of trees beneath a high, clear sky."),
    ("L2", "A wet heath is dotted with low flowering bushes. A line of exposed stones curves "
     "across the foreground, with a rounded hill in the distance."),
    ("L3", "A stand of slender birches grows on a sandy rise. Long shadows cross the open "
     "foreground and a dark evergreen wood fills the background."),
    ("M1", "An abandoned stone quarry contains a pool of green water. Rough steps descend "
     "from a grassy rim, and two small houses stand beyond the far wall."),
    ("M2", "A footpath follows the edge of a reservoir below a hillside village. A metal "
     "railing crosses the foreground and a patchwork of gardens climbs behind the roofs."),
    ("M3", "A sluice gate separates a narrow channel from a reed-filled basin. A dirt service "
     "track runs beside it toward a low brick building."),
)
SESSION_OFFSETS_HOURS = (0, 8, 24, 32, 48, 56, 72, 80)
WINDOW_HOURS = 4
ORDER_SEED = 2026091908
HISTORICAL_ACCOUNTED = Decimal("112.293676")
CURRENT_CEILING = Decimal("120")
PROPOSED_CEILING = Decimal("350")
RESERVATION = Decimal("5")
NEW_SETTLED_STOP = Decimal("220")
DISK_FLOOR = 5 * 1024**3
INITIAL_CAPACITY = 40 * 1024**3
ACTIVE_STORAGE_RESERVATION = 256 * 1024**2
EXPECTED_OUTPUTS = 4608
URL = "https://openrouter.ai/api/v1/images"


def utc_datetime(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("an explicit timezone-aware start time is required")
    if value.microsecond:
        raise ValueError("use an exact whole-second start time")
    return value.astimezone(timezone.utc)


def payload(model, scene, arm):
    if model not in MODELS or not 0 <= scene < len(SCENES) or arm not in ARMS:
        raise ValueError("unknown fixed design cell")
    result = dict(model=model, prompt=SCENES[scene][1] + " " + SUFFIXES[arm],
                  n=1, aspect_ratio="1:1")
    if model.startswith("gpt-image"):
        result.update(model="openai/" + model, quality="medium", background="opaque")
        provider = "openai"
    elif model.startswith("google/"):
        result["resolution"] = "1K"
        provider = "google-ai-studio"
    else:
        result["output_format"] = "png"
        provider = "black-forest-labs/us-3"
    result["provider"] = dict(only=[provider], allow_fallbacks=False)
    return result


def assignments(start):
    """Build all slots; this is scheduling data, never a send operation."""
    start = utc_datetime(start)
    result = []
    for session, hours in enumerate(SESSION_OFFSETS_HOURS):
        window_start = start + timedelta(hours=hours)
        window_end = window_start + timedelta(hours=WINDOW_HOURS)
        group = []
        for model_index, model in enumerate(MODELS):
            for scene, (scene_id, _) in enumerate(SCENES):
                for arm in ARMS:
                    group.append(dict(
                        id=f"pfam1-s{session:02d}-m{model_index:02d}-{scene_id}-{arm}",
                        model=model, session=session, scene=scene, scene_id=scene_id, arm=arm,
                        window_start=window_start.isoformat(), window_end=window_end.isoformat(),
                        payload=payload(model, scene, arm),
                    ))
        random.Random(ORDER_SEED + session).shuffle(group)
        for order, row in enumerate(group):
            row["session_order"] = order
            row["global_order"] = len(result)
            result.append(row)
    return result


def verify_assignments(rows, start):
    """Require the exact order and payload, not merely the same row count."""
    if canonical_sha(rows) != canonical_sha(assignments(start)):
        raise ValueError("assignment membership, order, windows or payload changed")


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def design_record():
    """An unscheduled preview, which cannot be confused with a live freeze."""
    return dict(
        schema="painter-family-controls-design/1.0", namespace=NAMESPACE,
        status="draft; no live authorization, schedule, frozen study or observations",
        models=list(MODELS), artists=list(ARTISTS), arms=list(ARMS),
        scenes=[dict(id=key, text=text) for key, text in SCENES], suffixes=SUFFIXES.copy(),
        session_offsets_hours=list(SESSION_OFFSETS_HOURS), window_hours=WINDOW_HOURS,
        order_seed=ORDER_SEED, planned_outputs=EXPECTED_OUTPUTS,
        historical_accounted_usd=str(HISTORICAL_ACCOUNTED),
        current_approved_cumulative_ceiling_usd=str(CURRENT_CEILING),
        proposed_unapproved_ceiling_usd=str(PROPOSED_CEILING),
        primary=dict(representation="csd", endpoints=["N", "T"], family_size=12,
                     sessions=8, scenes=12, incomplete_model_decision="unresolved"),
        frozen_before_new_queries_required=True, network_transport_available=False,
    )
