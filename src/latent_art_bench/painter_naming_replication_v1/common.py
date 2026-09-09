"""Fixed identities, exact historical prompts, and a new randomized inventory."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_study_v1 import study, transport
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier
from latent_art_bench.painter_responsiveness_v2 import common as palette

NAMESPACE = "painter_naming_replication_v1"
RUN_ID = "pnrv1-20260910"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
CONFIG = STUDIES / "study.json"
METADATA = STUDIES / "endpoint_metadata.json"
BUDGET_RECEIPT = retained.BASE / "pdsv1-main-immediate-20260907/collection_receipt.json"
OLD_NAMING = Path("reports/painter_distribution_study_v1/pdsv1-analysis-20260907/endpoints.csv")
OLD_PALETTE = Path("reports/painter_responsiveness_v2") / (
    "prv2-oauth-recovery-20260908/experiment/primary.csv"
)
PAINTERS = {"monet": "claude_monet", "cezanne": "paul_cezanne"}


def directory(run_id):
    if identifier(run_id) != RUN_ID:
        raise ValueError("only the single prospectively designated replication is authorized")
    return MANIFESTS / run_id


def configuration(root):
    config = read_json(root / CONFIG)
    expected = dict(
        schema="painter-naming-replication/1",
        run_id=RUN_ID,
        assignment_seed=2026091031,
        analysis_seed=2026091032,
        naming_repetitions=1,
        palette_repetitions=4,
        maximum_images=264,
        maximum_attempts=272,
        maximum_technical_retries=8,
        maximum_in_flight=2,
        minimum_start_interval_seconds=5,
        maximum_collection_seconds=86400,
        overall_spending_ceiling_usd=75,
        historical_accounted_usd=45.6819185,
        request_reservation_usd=5,
        minimum_free_bytes=5 * 1024**3,
        alpha=0.05,
    )
    if (
        config != expected
        or type(config["naming_repetitions"]) is not int
        or config["naming_repetitions"] != 1
    ):
        raise ValueError("configuration differs from the prospectively fixed allocation")
    return config


def endpoint_record(root):
    receipt = read_json(root / METADATA)
    body = receipt["response_body"].encode()
    if (
        receipt["status_code"] != 200
        or hashlib.sha256(body).hexdigest() != receipt["response_sha256"]
    ):
        raise ValueError("public endpoint metadata binding changed")
    value = json.loads(body)
    matches = [e for e in value["endpoints"] if e["provider_tag"] == "black-forest-labs/us-3"]
    if value["id"] != "black-forest-labs/flux.2-max" or len(matches) != 1:
        raise ValueError("the pinned paid endpoint is unavailable")
    endpoint = matches[0]
    parameters = endpoint["supported_parameters"]
    if (
        "1:1" not in parameters["aspect_ratio"]["values"]
        or "png" not in parameters["output_format"]["values"]
        or parameters["n"] != dict(type="range", min=1, max=1)
        or endpoint["pricing"] != [dict(billable="output_image", unit="megapixel", cost_usd=0.07)]
    ):
        raise ValueError("pinned endpoint capabilities or pricing differ")
    return endpoint


def requests(root, config=None):
    config = config or configuration(root)
    old = read_json(root / study.CONFIG)
    if len(old["briefs"]) != 24:
        raise ValueError("all 24 original detailed briefs are required")
    rng = np.random.default_rng(config["assignment_seed"])
    blocks = []
    for brief in old["briefs"]:
        for repetition in range(config["naming_repetitions"]):
            block = []
            for arm in rng.permutation(("free", "monet", "cezanne")):
                arm = str(arm)
                painter = PAINTERS.get(arm, "claude_monet")
                prompt = study.prompt(brief, painter, "artist_free" if arm == "free" else "named")
                block_id = f"n:{brief['brief_id']}:r{repetition:02d}"
                block.append(
                    dict(
                        request_id=f"{block_id}:{arm}",
                        block_id=block_id,
                        experiment="naming",
                        route="flux_2_max",
                        template_id=brief["brief_id"],
                        content_class=brief["content_class"],
                        repetition=repetition,
                        arm=arm,
                        polarity=None,
                        payload=transport.payload("flux_2_max", prompt),
                    )
                )
            blocks.append(block)
    old_palette = palette.configuration(root)
    old_palette = dict(old_palette, seed=config["assignment_seed"] + 1)
    p = palette.requests(old_palette)
    for start in range(0, len(p), 8):
        blocks.append(
            [
                dict(
                    r,
                    request_id=r["request_id"].replace("prv2:", "p:", 1),
                    block_id=r["block_id"].replace("prv2:", "p:", 1),
                    experiment="palette",
                )
                for r in p[start : start + 8]
            ]
        )
    result = []
    for block_order, index in enumerate(rng.permutation(len(blocks)), 1):
        for within, row in enumerate(blocks[int(index)]):
            result.append(
                dict(row, sequence=len(result), block_order=block_order, within_block=within)
            )
    if Counter(r["route"] for r in result) != {
        "flux_2_max": 72 * config["naming_repetitions"],
        "oauth_gpt_image_2": 192,
    }:
        raise ValueError("replication allocation is incomplete")
    return result


def palette_schedule(requests):
    return [
        dict(row, sequence=i)
        for i, row in enumerate(r for r in requests if r["experiment"] == "palette")
    ]
