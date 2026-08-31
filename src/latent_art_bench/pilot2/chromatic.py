"""Secondary Lee-derived chromatic descriptors for pilot_2.

Lee et al. define the adjacent-pixel CIE Lab distance distribution and its
seamlessness scalar.  They do not establish an artist classifier or a universal
K-S equivalence margin, so this module is deliberately descriptive and never
opens the pilot_2 generation gate.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Literal

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from latent_art_bench.config import ChromaticConfig
from latent_art_bench.features.chromatic import (
    adjacent_chromatic_distances,
    chromatic_summary,
)
from latent_art_bench.io import hash_file, stable_hash

FEATURE_VERSION = "lee2018-seamlessness-histogram-fixed500-secondary-v1"
LONG_SIDE = 500
HISTOGRAM_LOWER_EDGES = (
    0.0,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.00,
    1.20,
    1.40,
    1.60,
    1.80,
    2.00,
    2.25,
    2.50,
    2.75,
    3.00,
    3.50,
    4.00,
    4.50,
    5.00,
    6.00,
    7.00,
    8.00,
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Pilot2ChromaticFeature(_StrictModel):
    record_type: Literal["pilot2_chromatic_feature"] = "pilot2_chromatic_feature"
    schema_version: Literal["2.0"] = "2.0"
    record_id: str
    source_record_id: str
    source_png_sha256: str
    feature_version: Literal["lee2018-seamlessness-histogram-fixed500-secondary-v1"] = (
        FEATURE_VERSION
    )
    feature_config_sha256: str
    width: int = Field(gt=0, le=500)
    height: int = Field(gt=0, le=500)
    vector: List[float]
    scalars: Dict[str, float]
    role: Literal["secondary_descriptive"] = "secondary_descriptive"

    @field_validator("source_png_sha256", "feature_config_sha256")
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("chromatic identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def exact_analysis_long_side(self) -> "Pilot2ChromaticFeature":
        if max(self.width, self.height) != LONG_SIDE:
            raise ValueError("pilot_2 chromatic features require an exact 500-pixel long side")
        return self


def chromatic_config() -> ChromaticConfig:
    """Return the immutable secondary feature definition."""

    return ChromaticConfig(
        enabled=True,
        feature_version=FEATURE_VERSION,
        source_doi="10.1371/journal.pone.0204430",
        adjacency="horizontal_and_vertical",
        standard_deviation_ddof=0,
        degenerate_epsilon=1.0e-12,
        normalized_histogram_lower_edges=list(HISTOGRAM_LOWER_EDGES),
        vector_representation="seamlessness_plus_hellinger",
    )


def _fixed_500_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as source:
        source.load()
        if source.format != "PNG" or source.mode != "RGB":
            raise ValueError("pilot_2 chromatic input must be a normalized RGB PNG")
        image = source.copy()
    longest = max(image.size)
    if longest != LONG_SIDE:
        scale = LONG_SIDE / float(longest)
        target = tuple(max(1, round(dimension * scale)) for dimension in image.size)
        image = image.resize(target, Image.Resampling.LANCZOS, reducing_gap=3.0)
    return np.asarray(image, dtype=np.uint8)


def extract_chromatic_secondary(
    path: Path,
    source_record_id: str,
    *,
    expected_sha256: str,
) -> Pilot2ChromaticFeature:
    """Extract S plus a Hellinger histogram at one common 500-pixel scale."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = hash_file(path)
    if observed != expected_sha256:
        raise ValueError("pilot_2 chromatic input hash is stale")
    rgb = _fixed_500_rgb(path)
    config = chromatic_config()
    summary = chromatic_summary(adjacent_chromatic_distances(rgb), config)
    config_sha256 = stable_hash(config.model_dump(mode="json", exclude_none=True))
    identity = stable_hash(
        {
            "source_record_id": source_record_id,
            "source_png_sha256": observed,
            "feature_version": FEATURE_VERSION,
            "feature_config_sha256": config_sha256,
            "analysis_long_side": LONG_SIDE,
        }
    )
    return Pilot2ChromaticFeature(
        record_id=f"pilot2-chromatic-{identity[:24]}",
        source_record_id=source_record_id,
        source_png_sha256=observed,
        feature_config_sha256=config_sha256,
        width=int(rgb.shape[1]),
        height=int(rgb.shape[0]),
        vector=[float(value) for value in summary["vector"]],
        scalars={
            **{name: float(value) for name, value in summary["scalars"].items()},
            "degenerate": 1.0 if summary["degenerate"] else 0.0,
        },
    )


def formula_probe_evidence() -> Dict[str, object]:
    """Verify the published algebra independently of image preprocessing."""

    config = chromatic_config()
    fixtures = {
        "constant_positive": np.ones(128, dtype=np.float64),
        "exponential_cv_one": np.asarray([0.0, 2.0] * 64, dtype=np.float64),
        "heavy_tail": np.asarray([0.0] * 127 + [128.0], dtype=np.float64),
    }
    observed = {
        name: float(chromatic_summary(values, config)["scalars"]["seamlessness"])
        for name, values in fixtures.items()
    }
    checks = {
        "constant_maps_to_minus_one": abs(observed["constant_positive"] + 1.0) <= 1e-12,
        "cv_one_maps_to_zero": abs(observed["exponential_cv_one"]) <= 1e-12,
        "heavy_tail_is_positive": observed["heavy_tail"] > 0.0,
    }
    payload: Dict[str, object] = {
        "feature_version": FEATURE_VERSION,
        "paper_formula": "(sigma_d - mean_d) / (sigma_d + mean_d)",
        "observed": observed,
        "checks": checks,
        "status": "pass" if all(checks.values()) else "fail",
        "claim_boundary": (
            "functional formula evidence only; not a corpus-wide replication of Lee et al. Figure 1"
        ),
    }
    payload["evidence_sha256"] = stable_hash(payload)
    return payload
