"""Fixed missingness-triggered two-arm allocation and disjoint evidence paths."""

from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json
from latent_art_bench.painter_clause_validation_v1 import common as predecessor
from latent_art_bench.painter_distribution_study_v1.transport import payload
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier

NAMESPACE = "painter_clause_successor_v1"
RUN_ID = "pcsv1-20260910"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
CONFIG = STUDIES / "study.json"
SCENES = predecessor.SCENES
INPUTS = STUDIES / "inputs.json"
QUALIFICATION = STUDIES / "qualification.json"
BUDGET_RECEIPT = predecessor.BUDGET_RECEIPT
PREDECESSOR_RUN_ID = predecessor.RUN_ID
PREDECESSOR_DIR = predecessor.directory(PREDECESSOR_RUN_ID)
REFUSED_REQUEST_ID = "c:pcv_built04:r00:cezanne"
ARMS = ("generic", "cezanne")
CLASSES = ("built", "land", "water")
PIPELINES = predecessor.PIPELINES
PAINTER_ID = "paul_cezanne"


def directory(run_id):
    if identifier(run_id) != RUN_ID:
        raise ValueError("only the single designated successor is authorized")
    return MANIFESTS / run_id


def configuration(root):
    config = read_json(Path(root) / CONFIG)
    expected = dict(
        schema="painter-clause-successor/1",
        run_id=RUN_ID,
        assignment_seed=2026091051,
        analysis_seed=2026091052,
        repetitions=2,
        scenes_per_class=8,
        maximum_images=96,
        maximum_attempts=104,
        maximum_technical_retries=8,
        maximum_in_flight=2,
        minimum_start_interval_seconds=5,
        maximum_collection_seconds=86400,
        overall_spending_ceiling_usd=75,
        historical_accounted_usd=50.7219185,
        minimum_free_bytes=5 * 1024**3,
        alpha=0.025,
    )
    if config != expected or any(type(config[k]) is not type(v) for k, v in expected.items()):
        raise ValueError("configuration differs from the single fixed successor")
    return config


def scenes(root):
    """Keep every predecessor scene, including the refused scene, unchanged."""
    return predecessor.scenes(root)


def requests(root, config=None):
    config = config or configuration(root)
    rng = np.random.default_rng(config["assignment_seed"])
    blocks = []
    for brief in scenes(root):
        for repetition in range(config["repetitions"]):
            block_id = f"cs:{brief['brief_id']}:r{repetition:02d}"
            block = []
            for arm in rng.permutation(ARMS):
                arm = str(arm)
                block.append(
                    dict(
                        request_id=f"{block_id}:{arm}",
                        block_id=block_id,
                        experiment="clause_successor",
                        route="oauth_gpt_image_2",
                        template_id=brief["brief_id"],
                        content_class=brief["content_class"],
                        repetition=repetition,
                        arm=arm,
                        polarity=None,
                        payload=payload("oauth_gpt_image_2", predecessor.prompt(brief, arm)),
                    )
                )
            blocks.append(block)
    result = []
    for order, index in enumerate(rng.permutation(len(blocks)), start=1):
        for position, row in enumerate(blocks[index]):
            result.append(
                dict(row, sequence=len(result), block_order=order, within_block=position)
            )
    if len(result) != config["maximum_images"]:
        raise ValueError("successor allocation is incomplete")
    return result


def binding_paths(root):
    return [
        CONFIG,
        SCENES,
        INPUTS,
        QUALIFICATION,
        STUDIES / "PROTOCOL.md",
        STUDIES / "DESIGN_DECISION.md",
        STUDIES / "PRECOLLECTION_REVIEW.md",
        STUDIES / "PRECOLLECTION_METHOD_REVIEW.md",
        STUDIES / "PRECOLLECTION_IMPLEMENTATION_REVIEW.md",
        STUDIES / "SCIENTIFIC_IMPLEMENTATION_REVIEW.md",
        predecessor.INPUTS,
        predecessor.STUDIES / "precision.json",
        predecessor.STUDIES / "PRECISION.md",
        BUDGET_RECEIPT,
        *(PREDECESSOR_DIR / name for name in (
            "freeze.json", "planned_requests.jsonl", "collection_receipt.json",
            "generation_events.jsonl", "slot_outcomes.jsonl", "operator_events.jsonl",
        )),
    ]
