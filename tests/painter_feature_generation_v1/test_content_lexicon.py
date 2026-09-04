from __future__ import annotations

from pathlib import Path

from latent_art_bench.painter_feature_generation_v1 import content_lexicon as lex

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_disposition_order_is_override_then_exclusion_then_positive() -> None:
    assert lex.classify("Water Lilies")["disposition"] == lex.ELIGIBLE
    assert lex.classify("Nymphéas, reflets de saule")["disposition"] == lex.ELIGIBLE
    assert lex.classify("Madame Cézanne in a Yellow Chair")["disposition"] == lex.INELIGIBLE
    assert lex.classify("Woman with a Parasol on the Cliffs")["disposition"] == lex.INELIGIBLE
    assert lex.classify("The Seine at Port-Marly")["disposition"] == lex.ELIGIBLE
    assert lex.classify("Untitled")["disposition"] == lex.UNRESOLVED


def test_primary_class_follows_the_diagnostic_priority() -> None:
    assert lex.classify("A Turn in the Road")["primary_class"] == "route_organized"
    assert lex.classify("Street in Moret")["primary_class"] == "built_place_organized"
    assert lex.classify("Stack of Wheat (Thaw, Sunset)")["primary_class"] == "open_or_wooded_land"
    bridge = lex.classify("Bridge at Villeneuve-la-Garenne")
    assert bridge["primary_class"] == "water_organized"
    assert bridge["class_matches"]["water_organized"] is True
    assert lex.classify("Portrait")["primary_class"] is None


def test_matching_is_whole_word_and_accent_insensitive() -> None:
    assert lex.classify("Étretat")["disposition"] == lex.ELIGIBLE
    assert lex.classify("Etretat")["disposition"] == lex.ELIGIBLE
    assert lex.classify("Overpainting")["disposition"] == lex.UNRESOLVED
    assert lex.classify("The Manor")["disposition"] == lex.UNRESOLVED


def test_rendered_artifact_is_in_sync_and_self_describing() -> None:
    target = REPOSITORY_ROOT / lex.OUTPUT_PATH
    assert target.is_file(), "render it with scripts/render_pfg_v1_content_lexicon.py"
    assert target.read_text(encoding="utf-8") == lex.serialize(lex.render())
    rendered = lex.render()
    assert rendered["protocol_id"] == "painter-feature-generation-v1/2.1"
    assert rendered["counts"]["positive_tokens"] == sum(
        len(tokens) for tokens in rendered["lists"]["positive_tokens_by_class"].values()
    )
    assert set(rendered["lists"]["positive_tokens_by_class"]) == set(lex.CLASS_PRIORITY)
