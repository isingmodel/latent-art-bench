"""The replacement is prepared prospectively, from the exact observed error scope."""

from pathlib import Path

import pytest

from latent_art_bench.io import read_json, read_jsonl
from latent_art_bench.painter_responsiveness_recovery_v1 import __main__ as cli


@pytest.fixture
def setup(tmp_path, monkeypatch):
    config = read_json(Path(__file__).resolve().parents[2] / cli.common.CONFIG)
    prior = tmp_path / cli.common.directory(cli.PREDECESSOR)
    prior.mkdir(parents=True)
    for name in ("freeze.json", "planned_requests.jsonl", "collection_receipt.json",
                 "generation_events.jsonl", "slot_outcomes.jsonl", "operator_events.jsonl",
                 "diagnostic_receipt.json"):
        (prior / name).write_text("{}\n")
    protocol = tmp_path / cli.PROTOCOL
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Synthetic protocol\n")
    failed = dict(kind="terminal", status="http_error", status_code=503, complete=True,
                  response_headers={"content-type": "text/plain"}, request_id="synthetic-error",
                  attempt=1, response_path="synthetic.gz", response_sha256="a" * 64,
                  stored_response_sha256="b" * 64)
    monkeypatch.setattr(cli.workflow, "collection_inputs", lambda *_: (
        {}, {}, [{} for _ in range(192)], dict(status="stopped", status_counts={
            "image_returned": 49, "http_error": 1, "never_started": 142})))
    monkeypatch.setattr(cli.workflow, "_response_entity", lambda *_: cli.collection.EXACT_BODY)
    monkeypatch.setattr(cli, "events", lambda _: [failed])
    monkeypatch.setattr(cli.workflow, "source_paths", lambda _: [])
    monkeypatch.setattr(cli.common, "configuration", lambda _: config)
    monkeypatch.setattr(cli, "proxy_snapshot", lambda _: {"pid": 123})

    def clean_commit(root, paths):
        assert not (root / cli.common.directory(cli.RUN_ID)).exists()
        assert cli.PROTOCOL in paths
        return "c" * 40

    monkeypatch.setattr(cli, "committed", clean_commit)
    return tmp_path


def test_prepare_binds_error_and_preserves_identical_design(setup):
    root = setup
    result = cli.prepare(root, root / "proxy")
    target = root / cli.common.directory(cli.RUN_ID)
    freeze = read_json(target / "freeze.json")
    requests = read_jsonl(target / "planned_requests.jsonl")
    assert result["status"] == "prepared" and len(requests) == 192
    assert requests == cli.common.requests(freeze["config"])
    assert freeze["recovery"]["qualifying_error"]["response_sha256"] == "a" * 64
    assert freeze["recovery"]["successful_images_visually_reviewed_before_decision"] is False
    with pytest.raises(ValueError, match="already exists"):
        cli.prepare(root, root / "proxy")


def test_different_error_cannot_prepare_a_replacement(setup, monkeypatch):
    monkeypatch.setattr(cli.workflow, "_response_entity", lambda *_: b"arbitrary error")
    with pytest.raises(ValueError, match="differs"):
        cli.prepare(setup, setup / "proxy")
    assert not (setup / cli.common.directory(cli.RUN_ID)).exists()


def test_cli_refuses_implicit_live(monkeypatch):
    monkeypatch.setattr("sys.argv", ["recovery", "collect", "--proxy-root", "unused"])
    with pytest.raises(SystemExit) as result:
        cli.main()
    assert result.value.code == 2
