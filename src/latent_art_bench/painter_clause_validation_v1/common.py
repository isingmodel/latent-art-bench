"""Fixed prospective clause allocation; no generation or new measurements."""

from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import study, transport
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier

NAMESPACE = "painter_clause_validation_v1"
RUN_ID = "pcvv1-20260910"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
CONFIG = STUDIES / "study.json"
SCENES = STUDIES / "scenes.json"
INPUTS = STUDIES / "inputs.json"
QUALIFICATION = STUDIES / "qualification.json"
BUDGET_RECEIPT = Path("data/manifests/painter_naming_replication_v1") / (
    "pnrv1-20260910/collection_receipt.json"
)
PAINTERS = {"monet": "claude_monet", "cezanne": "paul_cezanne"}
ARMS = ("free", "generic", "monet", "cezanne")
CLASSES = ("built", "land", "water")
PIPELINES = ("primary512", "resolution256", "jpeg90_512")


def directory(run_id):
    if identifier(run_id) != RUN_ID:
        raise ValueError("only the prospectively designated clause run is authorized")
    return MANIFESTS / run_id


def configuration(root):
    config = read_json(Path(root) / CONFIG)
    expected = dict(
        schema="painter-clause-validation/1",
        run_id=RUN_ID,
        assignment_seed=2026091041,
        analysis_seed=2026091042,
        repetitions=3,
        scenes_per_class=8,
        maximum_images=288,
        maximum_attempts=296,
        maximum_technical_retries=8,
        maximum_in_flight=2,
        minimum_start_interval_seconds=5,
        maximum_collection_seconds=86400,
        overall_spending_ceiling_usd=75,
        historical_accounted_usd=50.7219185,
        minimum_free_bytes=5 * 1024**3,
        alpha=0.05,
    )
    if config != expected or any(type(config[k]) is not type(v) for k, v in expected.items()):
        raise ValueError("configuration differs from the prospective allocation")
    return config


def scenes(root):
    value = read_json(Path(root) / SCENES)
    rows = value["briefs"]
    if (
        value["schema"] != "painter-clause-validation-scenes/1"
        or len(rows) != 24
        or len({r["brief_id"] for r in rows}) != 24
        or Counter(r["content_class"] for r in rows) != dict.fromkeys(CLASSES, 8)
        or any(not isinstance(r["detailed"], str) or not r["detailed"].strip() for r in rows)
    ):
        raise ValueError("complete fixed new-scene panel required")
    old = read_json(Path(root) / study.CONFIG)["briefs"]
    if {r["brief_id"] for r in rows} & {r["brief_id"] for r in old}:
        raise ValueError("new scene IDs overlap training scenes")
    if {r["detailed"].strip().lower() for r in rows} & {r["detailed"].strip().lower() for r in old}:
        raise ValueError("new scene text repeats a training prompt")
    return sorted(rows, key=lambda r: r["brief_id"])


def prompt(brief, arm):
    if arm not in ARMS:
        raise ValueError("unknown prospective clause")
    clause = {
        "free": "",
        "generic": " In a traditional landscape-painting style.",
        "monet": " In the style of Claude Monet.",
        "cezanne": " In the style of Paul Cezanne.",
    }[arm]
    return (
        "Create an oil painting on canvas."
        + clause
        + " Scene: "
        + brief["detailed"]
        + " Render only the painting area, without a surrounding frame, "
        "signature, letters or watermark."
    )


def requests(root, config=None):
    config = config or configuration(root)
    rng = np.random.default_rng(config["assignment_seed"])
    blocks = []
    for brief in scenes(root):
        for repetition in range(config["repetitions"]):
            block_id = f"c:{brief['brief_id']}:r{repetition:02d}"
            block = []
            for arm in rng.permutation(ARMS):
                arm = str(arm)
                block.append(
                    dict(
                        request_id=f"{block_id}:{arm}",
                        block_id=block_id,
                        experiment="clause",
                        route="oauth_gpt_image_2",
                        template_id=brief["brief_id"],
                        content_class=brief["content_class"],
                        repetition=repetition,
                        arm=arm,
                        polarity=None,
                        payload=transport.payload("oauth_gpt_image_2", prompt(brief, arm)),
                    )
                )
            blocks.append(block)
    result = []
    for block_order, index in enumerate(rng.permutation(len(blocks)), 1):
        for within, row in enumerate(blocks[int(index)]):
            result.append(
                dict(row, sequence=len(result), block_order=block_order, within_block=within)
            )
    if len(result) != config["maximum_images"]:
        raise ValueError("prospective clause allocation is incomplete")
    return result


def binding_paths(root):
    """Exact retained numeric lineage plus prospective design/qualification records."""
    return [
        CONFIG,
        SCENES,
        INPUTS,
        QUALIFICATION,
        STUDIES / "PROTOCOL.md",
        STUDIES / "precision.json",
        STUDIES / "PRECISION.md",
        STUDIES / "PRECOLLECTION_REVIEW.md",
        STUDIES / "PRECOLLECTION_METHOD_REVIEW.md",
        STUDIES / "PRECOLLECTION_IMPLEMENTATION_REVIEW.md",
        STUDIES / "SCIENTIFIC_IMPLEMENTATION_REVIEW.md",
        BUDGET_RECEIPT,
        Path("data/manifests/painter_naming_replication_v1/pnrv1-20260910/freeze.json"),
        Path("data/manifests/painter_distribution_study_v1")
        / "pdsv1-main-immediate-20260907/collection_receipt.json",
        study.CONFIG,
        Path("configs/painter_responsiveness_v2/study.json"),
        Path("data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json"),
        Path("data/manifests/painter_naming_geometry_v1/pngv1-20260910/freeze.json"),
        Path("data/manifests/painter_naming_geometry_v1/pngv1-20260910/receipt.json"),
    ]
