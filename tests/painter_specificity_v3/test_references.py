"""Offline checks for the v3 reference stages (no network: httpx.MockTransport)."""

from __future__ import annotations

import json

import httpx
import pytest

from latent_art_bench.io import read_jsonl
from latent_art_bench.painter_feature_generation_v1 import content_lexicon as v1
from latent_art_bench.painter_feature_generation_v1.determine import File
from latent_art_bench.painter_specificity_v3 import lexicon, references
from latent_art_bench.painter_specificity_v3.panel import ALL, PAINTERS


def test_panel_is_two_groups_of_four_with_distinct_names():
    assert [p.group for p in PAINTERS].count("century") == 4
    assert [p.group for p in PAINTERS].count("hudson") == 4
    assert len({p.qid for p in ALL}) == len({p.name for p in ALL}) == len(ALL) == 11


@pytest.mark.parametrize("title", [
    "The Seine at Argenteuil", "Portrait of Madame Cézanne", "Water Lilies", "Haystacks, Snow",
    "Still Life with Apples", "The Card Players", "Boulevard Montmartre at Night", "Untitled",
])
def test_lexicon_keeps_the_four_painter_decisions(title):
    if not any(lexicon.ADDED_POSITIVE.values()) and not lexicon.ADDED_EXCLUSIONS:
        assert lexicon.classify(title) == v1.classify(title)
    old, new = v1.classify(title), lexicon.classify(title)
    if old["disposition"] == v1.INELIGIBLE:  # Exclusions are only ever added.
        assert new["disposition"] == v1.INELIGIBLE


def test_filename_decodes_commons_file_path():
    uri = "http://commons.wikimedia.org/wiki/Special:FilePath/Jacob_van_Ruisdael%20-%20Mill.jpg"
    assert references.filename(uri) == "Jacob van Ruisdael - Mill.jpg"


def _item(**claims):
    base = dict(P170=("Q213612",), P31=("Q3305213",), P186=("Q296955", "Q12321255"),
                P195=("Q190804",))
    base.update(claims)
    files = (File("File:a.jpg", "Public domain", "", 2000, "https://upload.wikimedia.org/a.jpg"),)
    return dict(painter_id="jacob_van_ruisdael", item_qid="Q1", label="Wheat Fields",
                claims=base, files=files)


@pytest.mark.parametrize("change, gate", [
    (dict(P170=("Q213612", "Q5582")), "creator"),
    (dict(P31=("Q93184",)), "painting"),
    (dict(P186=("Q296955", "Q106857709")), "medium"),
    (dict(P195=()), "collection"),
])
def test_gates_fail_in_order(change, gate):
    assert references.decide(_item(**change))["failed_gate"] == gate


def test_rights_geometry_and_content_gates():
    item = _item()
    assert references.decide(item)["admitted"]
    closed = dict(item, files=(File("File:a.jpg", "CC BY-NC 4.0", "", 2000, "u"),))
    assert references.decide(closed)["failed_gate"] == "rights"
    small = dict(item, files=(File("File:a.jpg", "Public domain", "", 900, "u"),))
    assert references.decide(small)["failed_gate"] == "geometry"
    assert references.decide(dict(item, label="Portrait of a Man"))["failed_gate"] == "content"


def _transport():
    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        if request.url.host == "query.wikidata.org":
            qid = params["query"].split("wd:")[1].split(";")[0]
            bindings = [] if qid != "Q213612" else [{
                "item": {"value": "http://www.wikidata.org/entity/Q7"},
                "image": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Mill.jpg"},
            }]
            return httpx.Response(200, json={"results": {"bindings": bindings}})
        if params.get("action") == "wbgetentities":
            claim = lambda v: {"rank": "normal", "mainsnak": {  # noqa: E731
                "snaktype": "value", "datavalue": {"value": {"id": v}}}}
            entity = {"id": "Q7", "labels": {"en": {"value": "The Mill at Wijk"}},
                      "descriptions": {}, "claims": {
                          "P170": [claim("Q213612")], "P31": [claim("Q3305213")],
                          "P186": [claim("Q296955"), claim("Q12321255")],
                          "P195": [claim("Q190804")]}}
            return httpx.Response(200, json={"entities": {"Q7": entity}})
        page = {"title": "File:Mill.jpg", "imageinfo": [{
            "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Mill.jpg",
            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Mill.jpg",
            "width": 3000, "height": 2400, "mime": "image/jpeg", "sha1": "a" * 40,
            "timestamp": "2020-01-01T00:00:00Z",
            "extmetadata": {"LicenseShortName": {"value": "Public domain"}}}]}
        return httpx.Response(200, json={"query": {"pages": [page]}})
    return httpx.MockTransport(handler)


def test_census_metadata_determination_and_frame_offline(tmp_path):
    for path in (references.SELF, references.PANEL, references.LEXICON, references.RULES):
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("bound\n")
    kwargs = dict(transport=_transport(), sleep=lambda _: None)
    receipt = references.census(tmp_path, "test-run", **kwargs)
    assert receipt["items_by_painter"]["jacob_van_ruisdael"] == 1
    references.metadata(tmp_path, "test-run", **kwargs)
    receipt = references.determine(tmp_path, "test-run")
    assert receipt["funnel"]["jacob_van_ruisdael"]["passed_content"] == 1
    receipt = references.frame(tmp_path, "test-run")
    assert receipt["works_by_painter"] == {"jacob_van_ruisdael": 1}
    work = read_jsonl(tmp_path / references.MANIFESTS / "test-run" / "frame.jsonl")[0]
    assert work["content_class"] == "built_place_organized"
    assert work["surrogate"]["expected_width"] == 3000
    with pytest.raises(FileExistsError):
        references.census(tmp_path, "test-run", **kwargs)
    ledger = tmp_path / references.MANIFESTS / "test-run" / "census_events.jsonl"
    assert all("event_sha256" in json.loads(line) for line in ledger.read_text().splitlines())
