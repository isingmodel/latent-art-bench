from __future__ import annotations

import json
from pathlib import Path

import pytest

from latent_art_bench.painter_feature_generation_v1 import prompt_library as pl

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_render_reads_the_exact_sixteen_templates_from_the_protocol() -> None:
    library = pl.render(REPOSITORY_ROOT)
    assert library["counts"] == {
        "templates": 16,
        "scene_groups": 4,
        "artist_free_strings": 16,
        "named_strings": 64,
        "total_strings": 80,
    }
    by_id = {row["template_id"]: row for row in library["templates"]}
    assert by_id["W1"]["artist_free_prompt"] == (
        "An oil painting on canvas of a riverbank landscape, with water organizing the composition."
    )
    assert by_id["W1"]["named_prompts"]["paul_cezanne"]["prompt"] == (
        "An oil painting on canvas by Paul Cézanne of a riverbank landscape, with water "
        "organizing the composition."
    )
    assert library["negative_prompt"]["text"] == (
        "text, lettering, signature, watermark, frame, border, photograph, collage"
    )
    assert library["render_contract"]["width"] == 1536
    assert library["render_contract"]["height"] == 1024
    assert [row["template_id"] for row in library["templates"]] == [
        f"{prefix}{index}" for prefix in "WBRL" for index in range(1, 5)
    ]


def test_named_insertion_is_byte_exact_and_only_at_the_anchor() -> None:
    prompt = "An oil painting on canvas of an oil painting on canvas."
    assert pl.named_prompt(prompt, "Alfred Sisley") == (
        "An oil painting on canvas by Alfred Sisley of an oil painting on canvas."
    )


def test_tracked_artifact_matches_a_fresh_render() -> None:
    target = REPOSITORY_ROOT / pl.OUTPUT_PATH
    assert target.is_file(), "render it with scripts/render_pfg_v1_prompt_library.py"
    assert target.read_text(encoding="utf-8") == pl.serialize(pl.render(REPOSITORY_ROOT))
    stored = json.loads(target.read_text(encoding="utf-8"))
    assert stored["protocol_sha256"] == pl.render(REPOSITORY_ROOT)["protocol_sha256"]


def test_parse_rejects_a_protocol_with_a_painter_name_in_an_artist_free_prompt() -> None:
    text = (REPOSITORY_ROOT / pl.PROTOCOL_PATH).read_text(encoding="utf-8")
    poisoned = text.replace(
        "of a riverbank landscape, with water organizing the composition.",
        "of a riverbank landscape by Monet, with water organizing the composition.",
    )
    with pytest.raises(pl.PromptLibraryError):
        pl.parse_protocol(poisoned)


def test_parse_rejects_a_missing_row() -> None:
    text = (REPOSITORY_ROOT / pl.PROTOCOL_PATH).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if not line.startswith("| L4 |")]
    with pytest.raises(pl.PromptLibraryError):
        pl.parse_protocol("\n".join(lines))
