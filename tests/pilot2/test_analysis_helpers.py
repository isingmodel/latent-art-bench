from __future__ import annotations

from typing import Any, Dict, List

from latent_art_bench.pilot2.analysis import (
    REQUESTED_LABELS,
    Pilot2AnalysisResult,
    Pilot2GridSpec,
    analyze_requested_label_effects,
)

ARTISTS = [
    "alfred_sisley",
    "camille_pissarro",
    "claude_monet",
    "paul_cezanne",
]
POSITIONS = {
    "alfred_sisley": 0.0,
    "claude_monet": 10.0,
    "camille_pissarro": 20.0,
    "paul_cezanne": 30.0,
}
CONTENT_IDS = [f"content-{index:02d}" for index in range(8)]
PROJECTED_MANIFEST_SHA256 = "f" * 64


def synthetic_grid() -> Pilot2GridSpec:
    return Pilot2GridSpec(content_ids=CONTENT_IDS)


def synthetic_held_references() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for artist in ARTISTS:
        for source, source_shift in (("aic", -0.2), ("nga", 0.2)):
            for index, work_shift in enumerate((-0.05, 0.05)):
                rows.append(
                    {
                        "canonical_work_id": f"{artist}-{source}-held-{index}",
                        "artist_id": artist,
                        "source_id": source,
                        "split": "held_out",
                        "status": "ok",
                        "vector": [POSITIONS[artist] + source_shift + work_shift],
                    }
                )
    return rows


def synthetic_generated_observations() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for label in REQUESTED_LABELS:
        for content_id in CONTENT_IDS:
            for repetition in range(4):
                prefix = f"{label}-{content_id}-{repetition}"
                rows.append(
                    {
                        "cell_id": f"{prefix}-control",
                        "content_id": content_id,
                        "requested_model_label": label,
                        "repetition": repetition,
                        "target_artist_id": None,
                        "artist_free_control": True,
                        "outcome": "succeeded",
                        "vector": [15.0],
                    }
                )
                for artist in ARTISTS:
                    rows.append(
                        {
                            "cell_id": f"{prefix}-{artist}",
                            "content_id": content_id,
                            "requested_model_label": label,
                            "repetition": repetition,
                            "target_artist_id": artist,
                            "artist_free_control": False,
                            "outcome": "succeeded",
                            "vector": [POSITIONS[artist]],
                        }
                    )
    return rows


def synthetic_result(draws: int = 100) -> Pilot2AnalysisResult:
    return analyze_requested_label_effects(
        synthetic_grid(),
        synthetic_held_references(),
        synthetic_generated_observations(),
        bootstrap_draws=draws,
        random_seed=20260901,
        protocol_preconditions_met=True,
        projected_input_manifest_sha256=PROJECTED_MANIFEST_SHA256,
    )
