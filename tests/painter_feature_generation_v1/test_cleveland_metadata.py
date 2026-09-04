from __future__ import annotations

import json
from pathlib import Path

import pytest

from latent_art_bench.painter_feature_generation_v1 import census_engine as engine
from latent_art_bench.painter_feature_generation_v1 import cleveland_metadata as cma

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _config() -> dict:
    return json.loads((REPOSITORY_ROOT / cma.DEFAULT_CONFIG).read_text())


def _intent(painter_id: str = "paul_cezanne", name: str = "Paul Cézanne") -> dict:
    return {
        "census_id": "pfg-v1-test",
        "request_id": "cma-artist-0004",
        "painter_id": painter_id,
        "cma_artist_query": name,
        "params": {"artists": name, "limit": "100", "skip": "0"},
    }


def _payload(*items: dict) -> bytes:
    return json.dumps({"info": {"total": len(items)}, "data": list(items)}).encode()


def _item(**overrides: object) -> dict:
    item = {
        "id": 1953,
        "accession_number": "1958.31",
        "title": "Mont Sainte-Victoire",
        "creators": [
            {"description": "Paul Cézanne (French, 1839-1906)", "role": "artist", "qualifier": ""}
        ],
        "type": "Painting",
        "technique": "oil on fabric",
        "support_materials": [{"description": "canvas"}],
        "share_license_status": "CC0",
        "images": {
            "full": {"url": "https://example.invalid/full.tif", "width": 5000, "height": 4000}
        },
    }
    item.update(overrides)
    return item


def test_tracked_config_validates_against_the_contract() -> None:
    config = _config()
    cma.validate_config(config)
    intents = cma.build_intents(config)
    assert len(intents) == 4
    assert intents[3]["params"]["artists"] == "Paul Cézanne"
    assert "C%C3%A9zanne" in intents[3]["encoded_url"]
    assert intents == cma.build_intents(config)


def test_full_engine_config_load_accepts_the_tracked_contract() -> None:
    config_path = REPOSITORY_ROOT / cma.DEFAULT_CONFIG
    loaded = engine.load_config(cma.CONTRACT, REPOSITORY_ROOT, config_path)
    assert loaded["census_id"] == "pfg-v1-cleveland-metadata-20260904"
    assert loaded["protocol_id"] == "painter-feature-generation-v1/2.1"


def test_parse_screens_exact_creator_medium_license_and_geometry() -> None:
    row = cma.parse_response(_payload(_item()), _intent(), _config(), "a" * 64)[0]
    screening = row["screening"]
    assert screening["exact_creator_match"] is True
    assert screening["painting_classification"] is True
    assert screening["oil_and_canvas_tokens"] is True
    assert screening["share_license_cc0"] is True
    assert screening["largest_reported_short_side"] == 4000
    assert screening["metadata_and_media_candidate"] is True
    assert row["cma_record"]["creators"][0]["role"] == "artist"
    assert row["active_study_admission"] is False


def test_parse_keeps_failed_rows_and_unknown_fields() -> None:
    item = _item(
        technique="etching",
        type="Print",
        share_license_status="Copyrighted",
        images=None,
        provider_added_this_field_yesterday={"a": 1},
    )
    row = cma.parse_response(_payload(item), _intent(), _config(), "b" * 64)[0]
    assert row["screening"]["authority_record_candidate"] is False
    assert row["screening"]["metadata_and_media_candidate"] is False
    assert row["screening"]["image_url_present"] is False
    assert "provider_added_this_field_yesterday" in row["field_presence"]


def test_qualified_or_wrong_role_creator_fails_the_creator_screen() -> None:
    attributed = _item(
        creators=[
            {"description": "Paul Cézanne (French)", "role": "artist", "qualifier": "attributed to"}
        ]
    )
    engraver = _item(creators=[{"description": "Paul Cézanne (French)", "role": "printmaker"}])
    unstated = _item(creators=[{"description": "Paul Cézanne (French)"}])
    other = _item(creators=[{"description": "Claude Monet (French)", "role": "artist"}])
    config = _config()
    assert (
        cma.parse_response(_payload(attributed), _intent(), config, "c" * 64)[0]["screening"][
            "exact_creator_match"
        ]
        is False
    )
    assert (
        cma.parse_response(_payload(engraver), _intent(), config, "c" * 64)[0]["screening"][
            "exact_creator_match"
        ]
        is False
    )
    assert (
        cma.parse_response(_payload(unstated), _intent(), config, "c" * 64)[0]["screening"][
            "exact_creator_match"
        ]
        is True
    )
    assert (
        cma.parse_response(_payload(other), _intent(), config, "c" * 64)[0]["screening"][
            "exact_creator_match"
        ]
        is False
    )


def test_numeric_strings_and_accent_variants_are_tolerated() -> None:
    item = _item(
        id="77",
        creators=[{"description": "Paul Cezanne (French, 1839-1906)", "role": "Artist"}],
        images={"web": {"url": "u", "width": "1200", "height": "1024"}},
    )
    row = cma.parse_response(_payload(item), _intent(), _config(), "d" * 64)[0]
    assert row["cma_artwork_id"] == 77
    assert row["screening"]["exact_creator_match"] is True
    assert row["screening"]["reported_short_side_at_least_minimum"] is True


def test_only_id_and_pagination_are_terminal() -> None:
    config = _config()
    with pytest.raises(cma.ClevelandError, match="positive integer id"):
        cma.parse_response(_payload(_item(id="x")), _intent(), config, "e" * 64)
    with pytest.raises(cma.ClevelandError, match="not a complete one-page census"):
        cma.parse_response(
            json.dumps({"info": {"total": 3}, "data": [_item()]}).encode(),
            _intent(),
            config,
            "e" * 64,
        )
    with pytest.raises(cma.ClevelandError, match="not a complete one-page census"):
        cma.parse_response(
            json.dumps({"info": {"total": 101}, "data": [_item()] * 101}).encode(),
            _intent(),
            config,
            "e" * 64,
        )
    empty = cma.parse_response(
        json.dumps({"info": {"total": 0}, "data": []}).encode(), _intent(), config, "e" * 64
    )
    assert empty == []


def test_summarize_reports_every_painter() -> None:
    config = _config()
    rows = cma.parse_response(_payload(_item()), _intent(), config, "f" * 64)
    summary = cma.summarize(rows, config)
    assert summary["returned_rows"] == 1
    assert summary["by_painter"]["paul_cezanne"]["metadata_and_media_candidates"] == 1
    assert summary["by_painter"]["claude_monet"]["returned_rows"] == 0
