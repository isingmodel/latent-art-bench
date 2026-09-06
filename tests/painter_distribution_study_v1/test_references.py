import hashlib
import io

import httpx
import pytest
from PIL import Image

from latent_art_bench.painter_distribution_study_v1 import references as r


def candidate(qid="Q90000001", title="Forest Interior", sha="a" * 40):
    return dict(
        item_qid=qid,
        painter_id="paul_cezanne",
        commons_filename=qid + ".png",
        entity=dict(
            creator_qids=["Q35548"],
            instance_qids=["Q3305213"],
            material_qids=["Q296955", "Q12321255"],
            collection_qids=["Q123"],
            inventory_numbers=[qid],
            described_at_urls=[],
            label=title,
        ),
        media=dict(
            rights_candidate_status="commons_open_rights_marker_candidate",
            original_short_side=1024,
            mime="image/png",
            mediawiki_sha1=sha,
            canonical_title="File:" + qid + ".png",
            original_width=1024,
            original_height=1024,
            original_url="https://upload.wikimedia.org/wikipedia/commons/a/a1/x.png",
            license_short_name="Public domain",
            license_url="",
            description_url="https://commons.wikimedia.org/wiki/File:" + qid + ".png",
        ),
    )


def test_work_url_identity_keeps_catalogue_query_and_drops_tracking_only():
    a = "https://www.cezannecatalogue.com/catalogue/entry.php?id=100&utm_source=example"
    b = "http://cezannecatalogue.com/catalogue/entry.php?id=100"
    c = "https://cezannecatalogue.com/catalogue/entry.php?id=101"
    assert r.url_key(a) == r.url_key(b)
    assert r.url_key(a) != r.url_key(c)
    assert r.url_key("https://example.org/app#work/1") != r.url_key(
        "https://example.org/app#work/2"
    )


def test_title_screen_is_not_place_name_classifier():
    assert r.screen(candidate(title="Forest Interior")) == "candidate"
    assert r.screen(candidate(title="Still Life with a Water Jug")) == "title_not_outdoor_candidate"
    assert (
        r.screen(candidate(title="Madame Cezanne in the Garden")) == "title_not_outdoor_candidate"
    )
    assert r.screen(candidate(title="Vétheuil")) == "title_not_outdoor_candidate"
    assert r.screen(candidate("Q3821663", "The Hanged Man's House")) == "candidate"


def test_collection_requires_recorded_work_identifier():
    item = candidate()
    item["entity"]["inventory_numbers"] = []
    assert r.screen(item) == "collection_work_identifier"
    item["entity"]["described_at_urls"] = [
        "https://www.cezannecatalogue.com/catalogue/entry.php?id=100"
    ]
    assert r.screen(item) == "candidate"
    item["entity"]["collection_qids"] = []
    assert r.screen(item) == "collection_work_identifier"


def test_identity_screen_excludes_aliases_without_collapsing_same_titles():
    a, b = candidate(), candidate("Q90000002", sha="b" * 40)
    audit, chosen = r.select([a, b], [], [])
    assert len(chosen) == 2
    b["media"]["mediawiki_sha1"] = a["media"]["mediawiki_sha1"]
    audit, chosen = r.select([a, b], [], [])
    assert len(chosen) == 1
    assert any(x["disposition"] == "duplicate_candidate_identity" for x in audit)
    audit, chosen = r.select([a], [], [dict(wikidata_qid=a["item_qid"], commons_files=[])])
    assert not chosen and audit[0]["disposition"] == "previous_exposure_identity"


def test_acquisition_retains_identity_mismatch_without_refreshing_hash(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (512, 600)).save(buffer, format="PNG")
    body = buffer.getvalue()
    item = dict(
        item_qid="Q1",
        work_id="wikidata:Q1",
        expected_sha1="0" * 40,
        url="https://upload.wikimedia.org/wikipedia/commons/a/a1/x.png",
    )
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        return httpx.Response(200, content=body)

    result = r.acquire_one(tmp_path, item, transport=httpx.MockTransport(handler))
    assert result["status"] == "identity_hash_mismatch" and len(calls) == 1
    assert (tmp_path / result["response_path"]).read_bytes() == body
    assert item["expected_sha1"] == "0" * 40
    with pytest.raises(FileExistsError):
        r.acquire_one(tmp_path, item, transport=httpx.MockTransport(handler))
    assert len(calls) == 1


def test_successful_acquisition_records_geometry_without_features(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (512, 600)).save(buffer, format="PNG")
    body = buffer.getvalue()
    item = dict(
        item_qid="Q2",
        work_id="wikidata:Q2",
        expected_sha1=hashlib.sha1(body).hexdigest(),
        url="https://upload.wikimedia.org/wikipedia/commons/a/a1/y.png",
    )
    result = r.acquire_one(
        tmp_path, item, transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    )
    assert result["status"] == "acquired"
    assert result["geometry"] == {"width": 512, "height": 600, "mode": "RGB", "format": "PNG"}
    assert "features" not in result


def test_acquisition_url_cannot_change_provider(tmp_path):
    item = dict(url="https://example.org/image.png")
    with pytest.raises(ValueError, match="outside"):
        r.acquire_one(tmp_path, item)
