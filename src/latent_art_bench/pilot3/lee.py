"""Machine-checkable retirement decision for the Lee et al. chromatic replication."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from latent_art_bench.io import hash_file, read_json, stable_hash, write_json

LEE_SCHEMA = "pilot3-lee-replication/1.0"
DEFAULT_REVIEW_CONFIG = Path("configs/pilot_3/lee_review.json")
DEFAULT_OUTPUT = Path("reports/pilot_3/evidence/lee_replication.json")
PAPER = Path("tmp/pdfs/lee2018-plosone.pdf")
SOURCE_TAR = Path("tmp/pdfs/lee2018-arxiv-source.tar")
SOURCE_TEX = Path("tmp/pdfs/lee2018-arxiv-source/manuscript.tex")
FIGURE_ONE = Path("tmp/pdfs/lee2018-arxiv-source/figure1.pdf")

EXPECTED_HASHES = {
    PAPER.as_posix(): "3980660b6df276ddbfd33a457a56135105c823a370c0326fb67dfd9938206e86",
    SOURCE_TAR.as_posix(): "d79e44f73ea84f3b639a3ab79a8731af34ca7382e193bcb16316524840fb16e1",
    SOURCE_TEX.as_posix(): "ece9c9b84fab4d03004b0791ec809a3fd7aa07d4e60e279a1e624082b9ea0350",
    FIGURE_ONE.as_posix(): "b333e37d3e587b1bd1a2e99e025d786edef383b405b874771b0c5cae649303e4",
}


class LeeEvidenceError(RuntimeError):
    pass


def _resolve(root: Path, relative: Path) -> Path:
    return (Path(root).expanduser().resolve() / relative).resolve()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _review_hash(review: Mapping[str, Any]) -> str:
    unsigned = dict(review)
    unsigned.pop("review_sha256", None)
    return stable_hash(unsigned)


def _validated_reviews(value: object) -> Sequence[Dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 2:
        raise LeeEvidenceError("Lee disposition requires exactly two reviewer records")
    reviews = [dict(item) for item in value if isinstance(item, dict)]
    if len(reviews) != 2 or len({review.get("reviewer_id") for review in reviews}) != 2:
        raise LeeEvidenceError("Lee reviewers must be two distinct identified records")
    for review in reviews:
        if review.get("decision") != "ineligible_retire":
            raise LeeEvidenceError("both reviewers must independently reach ineligible_retire")
        if review.get("independent") is not True:
            raise LeeEvidenceError("Lee reviewer record is not marked independent")
        if review.get("review_sha256") != _review_hash(review):
            raise LeeEvidenceError("Lee reviewer record hash is stale")
        if not str(review.get("reason", "")).strip():
            raise LeeEvidenceError("Lee reviewer reason is blank")
    return sorted(reviews, key=lambda review: str(review["reviewer_id"]))


def build_lee_replication(
    root: Path,
    *,
    review_config: Path = DEFAULT_REVIEW_CONFIG,
    output_path: Path = DEFAULT_OUTPUT,
) -> Dict[str, Any]:
    """Inspect the exact paper/source package and emit terminal P3-T09 evidence."""

    root = Path(root).expanduser().resolve()
    observed = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = _resolve(root, Path(relative))
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hash_file(path)
        if digest != expected:
            raise LeeEvidenceError(
                f"Lee input hash mismatch for {relative}: expected {expected}, found {digest}"
            )
        observed[relative] = digest

    config_path = _resolve(root, review_config)
    config = read_json(config_path)
    if not isinstance(config, dict) or config.get("schema_version") != "pilot3-lee-review/1.0":
        raise LeeEvidenceError("Lee review config has the wrong schema")
    reviews = _validated_reviews(config.get("reviews"))

    image_listing = subprocess.run(
        ["pdfimages", "-list", str(_resolve(root, FIGURE_ONE))],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    required_tokens = ("587   378", "112   109", "598   381", "125   121")
    if any(token not in image_listing for token in required_tokens):
        raise LeeEvidenceError("Figure 1 embedded-image inventory differs from reviewed evidence")
    tex = _resolve(root, SOURCE_TEX).read_text(encoding="utf-8")
    required_tex = (
        r"\includegraphics[width=0.9\textwidth]{figure1.pdf}",
        "Composition A",
        "Water Lilies and Japanese Bridge",
        "All images are obtained from Wiki Art and in the public domain",
    )
    if any(token not in tex for token in required_tex):
        raise LeeEvidenceError("publisher source manuscript no longer matches reviewed Figure 1")

    payload = {
        "record_type": "pilot3_lee_replication",
        "schema_version": LEE_SCHEMA,
        "todo_id": "P3-T09",
        "status": "ineligible_retire",
        "paper": {
            "citation": (
                "Lee, Kim, Sun, Jeong, and Park (2018), Heterogeneity in chromatic "
                "distance in images and characterization of massive painting data set"
            ),
            "doi": "10.1371/journal.pone.0204430",
            "input_file_sha256": observed[PAPER.as_posix()],
            "method_reviewed": {
                "color_space": "CIELab",
                "adjacency": "horizontal and vertical neighboring pixel pairs",
                "resolution_dependence": "raw distributions shown at 500 through 3000 px",
                "mean_rescaling": "distribution rescaled by mean adjacent-pixel distance",
            },
            "data_statement_scope": (
                "the paper states that relevant data are within the article, but does not "
                "provide the byte-identical WikiArt source fixtures used for Figure 1"
            ),
        },
        "source_package": {
            "archive_sha256": observed[SOURCE_TAR.as_posix()],
            "manuscript_sha256": observed[SOURCE_TEX.as_posix()],
            "figure1_pdf_sha256": observed[FIGURE_ONE.as_posix()],
            "figure1_role": "assembled manuscript figure containing plots and artwork insets",
            "embedded_raster_inventory": [
                {"width": 587, "height": 378, "role": "composite surface visualization"},
                {"width": 112, "height": 109, "role": "Mondrian artwork inset"},
                {"width": 598, "height": 381, "role": "composite surface visualization"},
                {"width": 125, "height": 121, "role": "Monet artwork inset"},
            ],
            "pdfimages_listing_sha256": stable_hash(image_listing),
        },
        "eligibility_review": {
            "exact_original_fixture_available": False,
            "author_confirmed_byte_identical_copy_available": False,
            "supports_native_500_to_3000_pixel_series_without_upsampling": False,
            "crop_border_damage_and_color_management_review_possible": False,
            "full_empirical_distribution_target_recoverable": False,
            "figure_crop_or_inset_permitted_as_substitute": False,
            "reason": (
                "the source archive supplies only a composed figure; its two artwork insets "
                "are 112x109 and 125x121 pixels and cannot supply the paper's native 500-3000 "
                "pixel resolution series, original color management, crop, or distribution"
            ),
        },
        "digitization_tolerances": {
            "status": "not_applicable_fixture_ineligible",
            "scalar_only_match_permitted": False,
            "look_alike_reproduction_permitted": False,
            "synthetic_formula_probe_permitted_as_replication": False,
        },
        "reviewers": reviews,
        "phase_b_effect": {
            "lee_measurement_included": False,
            "a_vector_gate_affected": False,
            "claim": (
                "Lee retirement removes the chromatic method; it cannot rescue or block "
                "A-vector qualification"
            ),
        },
    }
    payload["result_sha256"] = stable_hash(payload)
    write_json(_resolve(root, output_path), payload)
    return payload


def verify_lee_replication(payload: Mapping[str, Any]) -> str:
    if payload.get("schema_version") != LEE_SCHEMA:
        raise LeeEvidenceError("Lee evidence schema is stale")
    if payload.get("status") != "ineligible_retire":
        raise LeeEvidenceError("Lee terminal status must be ineligible_retire")
    _validated_reviews(payload.get("reviewers"))
    recorded = payload.get("result_sha256")
    if not _is_sha256(recorded):
        raise LeeEvidenceError("Lee result self-hash is missing")
    unsigned = dict(payload)
    unsigned.pop("result_sha256", None)
    if stable_hash(unsigned) != recorded:
        raise LeeEvidenceError("Lee result self-hash is stale")
    return str(recorded)
