from __future__ import annotations

from pathlib import Path

import httpx

from latent_art_bench.io import read_jsonl
from latent_art_bench.painter_feature_generation_v2.renderings import (
    ENDPOINT,
    intents,
    select_rendering,
    wait_seconds,
)

ROOT = Path(__file__).resolve().parents[2]
FRAME = ROOT / "data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl"


def test_rendering_intents_cover_every_recorded_file_with_bounded_urls():
    frame = read_jsonl(FRAME)
    requests = intents(frame)
    titles = [name for r in requests for name in r["params"]["titles"].split("|")]
    assert set(titles) == {r["surrogate"]["commons_filename"] for r in frame}
    assert len(titles) == len(set(titles))
    assert all(len(str(httpx.URL(ENDPOINT, params=r["params"]))) <= 7000 for r in requests)
    assert all(len(r["params"]["titles"].split("|")) <= 20 for r in requests)


def test_rendered_file_is_bound_to_original_identity_not_original_file_hash():
    row = dict(
        work_id="Q1",
        painter_id="p",
        role="confirmation",
        surrogate=dict(expected_sha1="original", expected_width=10000, expected_height=8000),
    )
    page = dict(
        imageinfo=[
            dict(
                sha1="original",
                width=10000,
                height=8000,
                thumburl="https://upload.wikimedia.org/derived.jpg",
                thumbwidth=2048,
                thumbheight=1638,
                extmetadata={"LicenseShortName": {"value": "CC BY-SA 4.0"}},
            )
        ]
    )
    selected = select_rendering(row, page)
    assert selected["status"] == "rendering_registered"
    assert selected["source_sha1"] == "original"
    assert selected["provider_rendered"] is True
    page["imageinfo"][0]["sha1"] = "changed"
    assert select_rendering(row, page)["status"] == "metadata_rejected"


def test_provider_missing_file_and_malformed_retry_after_are_accounted_for():
    row = dict(
        work_id="Q1",
        painter_id="p",
        role="confirmation",
        surrogate=dict(expected_sha1="original", expected_width=10000, expected_height=8000),
    )
    assert select_rendering(row, {})["status"] == "metadata_rejected"
    assert wait_seconds("nonsense", 1) == 5
    assert wait_seconds("30", 1) == 30
