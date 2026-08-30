import io

from PIL import Image

from latent_art_bench.data.corpus import _write_download, select_candidate_works
from latent_art_bench.data.museums import classify_landscape_candidate
from latent_art_bench.schemas import CorpusCandidateRecord


def _candidate(artist_id: str, source_id: str, object_id: str, score: int):
    return CorpusCandidateRecord(
        source_id=source_id,
        source_object_id=object_id,
        artist_id=artist_id,
        artist_name=artist_id.replace("_", " ").title(),
        title=f"Landscape {object_id}",
        source_url=f"https://example.test/{object_id}",
        image_url=f"https://example.test/{object_id}.jpg",
        rights_basis="public-domain fixture",
        genre_score=score,
        genre_evidence=["explicit:landscape"],
        decision="include",
        decision_reason="test fixture",
    )


def test_landscape_rule_is_metadata_based() -> None:
    score, evidence, decision, _ = classify_landscape_candidate(
        "Road beside the Seine", ["trees"], "Clouds above a village"
    )
    assert score >= 3
    assert decision == "include"
    assert "title:road" in evidence

    _, _, portrait_decision, _ = classify_landscape_candidate(
        "Portrait of a Woman", [], None
    )
    assert portrait_decision == "exclude"


def test_selection_is_deterministic_and_source_balanced(pilot_config) -> None:
    config = pilot_config.corpus.model_copy(
        update={"target_works_per_artist": [1, 2], "max_works_per_artist": 2}
    )
    rows = []
    for artist in config.selected_artists:
        rows.extend(
            [
                _candidate(artist.artist_id, "aic", "1", 9),
                _candidate(artist.artist_id, "nga", "2", 8),
                _candidate(artist.artist_id, "aic", "3", 7),
            ]
        )
    first = select_candidate_works(rows, config)
    second = select_candidate_works(reversed(rows), config)
    assert [row.model_dump() for row in first] == [row.model_dump() for row in second]
    for artist in config.selected_artists:
        sources = {row.source_id for row in first if row.artist_id == artist.artist_id}
        assert sources == {"aic", "nga"}


def test_preseeded_browser_image_is_reused_without_network(tmp_path) -> None:
    output_stem = tmp_path / "source" / "aic-1-primary"
    output_stem.parent.mkdir(parents=True)
    payload = io.BytesIO()
    Image.new("RGB", (300, 280), "cornflowerblue").save(payload, format="JPEG")
    expected = payload.getvalue()
    output_stem.with_suffix(".jpg").write_bytes(expected)

    class NoNetwork:
        def get_bytes(self, _url):
            raise AssertionError("network should not be used for a preseeded image")

    path, digest, width, height = _write_download(
        NoNetwork(), "https://blocked.example/image.jpg", output_stem
    )
    assert path.read_bytes() == expected
    assert len(digest) == 64
    assert (width, height) == (300, 280)
