import base64
import gzip
import hashlib
import io
import json

from PIL import Image

from latent_art_bench.io import hash_file
from latent_art_bench.painter_distribution_study_v1 import measurement as m
from latent_art_bench.painter_distribution_study_v1 import parallel_collection as p
from latent_art_bench.painter_distribution_study_v1 import parallel_results as r
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, bindings, publish


def test_completion_order_does_not_change_slot_order_or_retry_membership(tmp_path):
    publish(
        tmp_path / s.DIRECTORY / "requests.jsonl",
        [dict(request_id="slot0000"), dict(request_id="slot0001")],
        lines=True,
    )
    ledger = tmp_path / p.DIRECTORY / "slot_events.jsonl"
    for slot, initial, selected in (
        ("slot0001", "http_error", "slot0001-retry1"),
        ("slot0000", "image_returned", "slot0000"),
    ):
        append_event(
            ledger,
            dict(
                kind="slot_terminal",
                request_id=slot,
                initial_status=initial,
                status="image_returned",
                selected_request_id=selected,
                selected_response={},
            ),
        )
    publish(
        tmp_path / p.DIRECTORY / "generation_receipt.json",
        dict(status="completed", outputs=bindings(tmp_path, [ledger.relative_to(tmp_path)])),
    )
    items = r.inventory(tmp_path, "generated")
    assert [item["request_id"] for item in items] == ["slot0000", "slot0001"]
    assert [item["initial_only_eligible"] for item in items] == [True, False]
    assert items[1]["selected_request_id"] == "slot0001-retry1"


def test_successor_decodes_selected_image_under_disjoint_workspace(tmp_path, monkeypatch):
    buffer = io.BytesIO()
    Image.new("RGB", (512, 512), (10, 20, 30)).save(buffer, format="PNG")
    raw = buffer.getvalue()
    body = json.dumps(dict(data=[dict(b64_json=base64.b64encode(raw).decode())])).encode()
    path = tmp_path / p.WORKSPACE / "responses" / "slot0000-retry1.json.gz"
    path.parent.mkdir(parents=True)
    path.write_bytes(gzip.compress(body, mtime=0))
    response = dict(
        response_path=path.relative_to(tmp_path).as_posix(),
        retained_sha256=hash_file(path),
        response_sha256=hashlib.sha256(body).hexdigest(),
        observed=t.inspect_response(body),
    )
    item = dict(
        image_id="generated:slot0000",
        painter_id=s.PAINTERS[0],
        content_class="water",
        request_id="slot0000",
        selected_request_id="slot0000-retry1",
        route=s.ROUTES[0],
        brief_id="water01",
        brief_index=0,
        condition="named",
        repetition=0,
        window=0,
        initial_only_eligible=False,
        selected_response=response,
    )

    def inspect(path, metadata, pipelines):
        path.relative_to(tmp_path / p.WORKSPACE)
        assert path.read_bytes() == raw
        assert metadata["raw_sha256"] == hashlib.sha256(raw).hexdigest()
        assert metadata["selected_request_id"] == "slot0000-retry1"
        assert not metadata["initial_only_eligible"]
        assert pipelines == s.PIPELINES
        return [dict(status="inspected")]

    monkeypatch.setattr(m, "measure_path", inspect)
    assert r.measure_item(tmp_path, "generated", item) == [dict(status="inspected")]
    assert not list((tmp_path / p.WORKSPACE / "measurement_tmp").iterdir())
