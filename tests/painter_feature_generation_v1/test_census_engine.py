from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from latent_art_bench import evidence
from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import census_engine as engine
from latent_art_bench.painter_feature_generation_v1 import cleveland_metadata as cma

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROUTE = cma.CONTRACT

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=True, text=True
    ).stdout.strip()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n")


def _repo(tmp_path: Path) -> tuple[Path, Path, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")
    source = REPOSITORY_ROOT / cma.DEFAULT_CONFIG
    config = json.loads(source.read_text())
    config["protocol_path"] = "protocol.md"
    config["source_contract"]["execution_start_not_after_utc"] = "2099-01-01T00:00:00Z"
    config["source_contract"]["minimum_interval_seconds"] = 0.5
    config["paths"] = {
        "request_intents": "data/intents.jsonl",
        "request_events": "data/events.jsonl",
        "freeze": "data/freeze.json",
        "publication_directory": "data/publication",
        "candidate_manifest": "data/publication/candidates.jsonl",
        "execution_receipt": "data/publication/execution_receipt.json",
        "workspace": "workspace/cma",
    }
    (root / "protocol.md").write_text("Protocol ID: `painter-feature-generation-v1/2.1`\n")
    config_path = root / "config.json"
    _write_json(config_path, config)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "contract")
    return root, config_path, config


@pytest.fixture
def small_freeze(monkeypatch: pytest.MonkeyPatch) -> None:
    def required(route, root, config_path, config):  # noqa: ANN001
        return sorted(["config.json", "data/intents.jsonl", "protocol.md"])

    monkeypatch.setattr(engine, "required_frozen_paths", required)
    monkeypatch.setattr(engine.time, "sleep", lambda _: None)


def _authorize(
    root: Path, config: dict, *, reviewer_kind: str = "llm_subagent"
) -> tuple[Path, str]:
    freeze_path = root / "data/freeze.json"
    review = {
        "schema_version": ROUTE.schema("review"),
        "decision": ROUTE.review_decision,
        "blocking_findings": [],
        "independent_reviewer": "neutral test reviewer",
        "reviewer_kind": reviewer_kind,
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "approved_scope": engine.METADATA_ONLY_SCOPE,
        "reviewed_freeze_path": "data/freeze.json",
        "reviewed_freeze_sha256": hash_file(freeze_path),
    }
    review_path = root / "data/review.json"
    _write_json(review_path, review)
    seal = {
        "schema_version": ROUTE.schema("authorization"),
        "status": ROUTE.authorization_status,
        "census_id": config["census_id"],
        "protocol_id": config["protocol_id"],
        "authorization_scope": engine.METADATA_ONLY_SCOPE,
        "freeze_path": "data/freeze.json",
        "freeze_sha256": hash_file(freeze_path),
        "review_path": "data/review.json",
        "review_sha256": hash_file(review_path),
    }
    seal_path = root / "data/authorization.json"
    _write_json(seal_path, seal)
    return seal_path, hash_file(seal_path)


def _item(artwork_id: int, name: str, **overrides: object) -> dict:
    item = {
        "id": artwork_id,
        "accession_number": f"1958.{artwork_id}",
        "title": f"Landscape {artwork_id}",
        "creation_date": "1880",
        "creators": [
            {
                "id": 7,
                "description": f"{name} (French, 1840-1926)",
                "role": "artist",
                "qualifier": "",
            }
        ],
        "type": "Painting",
        "technique": "oil on canvas",
        "support_materials": [],
        "department": "Modern European Painting and Sculpture",
        "share_license_status": "CC0",
        "url": f"https://clevelandart.org/art/{artwork_id}",
        "images": {
            "web": {"url": "https://example.invalid/web.jpg", "width": "893", "height": 600},
            "print": {"url": "https://example.invalid/print.jpg", "width": 3400, "height": 2200},
        },
        "unexpected_provider_field": {"nested": [1, 2, 3]},
    }
    item.update(overrides)
    return item


def _transport(*, bad_total: bool = False, shared_id: bool = False) -> tuple:
    calls: list[str] = []
    names = {name: painter_id for painter_id, name in cma.PAINTERS}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        query = parse_qs(urlsplit(str(request.url)).query)
        name = query["artists"][0]
        artwork_id = 424242 if shared_id else 100000 + list(names).index(name)
        payload = {
            "info": {"total": 2 if bad_total else 1, "parameters": {"artists": name}},
            "data": [_item(artwork_id, name)],
        }
        return httpx.Response(
            200,
            request=request,
            headers={
                "Date": "Fri, 04 Sep 2098 12:00:00 GMT",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
        )

    return httpx.MockTransport(handler), calls


def test_prepare_writes_intents_and_a_commit_bound_freeze(
    tmp_path: Path, small_freeze: None
) -> None:
    root, config_path, config = _repo(tmp_path)
    result = engine.prepare(ROUTE, root, config_path)
    assert result["requests"] == 4
    freeze = json.loads((root / "data/freeze.json").read_text())
    assert freeze[evidence.RECORDED_COMMIT_FIELD] == _git(root, "rev-parse", "HEAD")
    assert [row["path"] for row in freeze["frozen_inputs"]] == [
        "config.json",
        "data/intents.jsonl",
        "protocol.md",
    ]
    assert freeze["preexecution_outputs"] == engine.expected_outputs(config)
    intents = [json.loads(line) for line in (root / "data/intents.jsonl").read_text().splitlines()]
    assert [row["params"]["artists"] for row in intents] == [n for _, n in cma.PAINTERS]
    with pytest.raises(engine.CensusError, match="freeze already exists"):
        engine.prepare(ROUTE, root, config_path)


def test_prepare_refuses_a_dirty_tracked_input(tmp_path: Path, small_freeze: None) -> None:
    root, config_path, config = _repo(tmp_path)
    changed = copy.deepcopy(config)
    changed["source_contract"]["timeout_seconds"] = 61.0
    _write_json(config_path, changed)
    with pytest.raises(engine.CensusError, match="dirty against HEAD"):
        engine.prepare(ROUTE, root, config_path)
    assert not (root / "data/freeze.json").exists()


def test_execute_publishes_after_four_complete_responses(
    tmp_path: Path, small_freeze: None
) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config)
    transport, calls = _transport()
    receipt = engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 4
    assert receipt["successful_requests"] == 4
    assert receipt["request_event_count"] == 9
    assert receipt["reviewer_kind"] == "llm_subagent"
    assert receipt["counts"]["metadata_and_media_candidates"] == 4
    assert receipt["counts"]["image_downloads"] == 0
    candidates = [
        json.loads(line)
        for line in (root / "data/publication/candidates.jsonl").read_text().splitlines()
    ]
    assert [row["painter_id"] for row in candidates] == sorted(p for p, _ in cma.PAINTERS)
    assert candidates[0]["cma_record"]["images"]["web"]["width"] == 893
    assert "unexpected_provider_field" in candidates[0]["field_presence"]
    assert len(list((root / "workspace/cma/response_bodies").rglob("*.response"))) == 4
    events = [json.loads(line) for line in (root / "data/events.jsonl").read_text().splitlines()]
    engine.validate_events(events, config["census_id"], ROUTE.schema("event"))
    assert events[0]["freeze_recorded_git_commit"] == _git(root, "rev-parse", "HEAD")
    audit = evidence.verify_receipt(root, root / "data/publication/execution_receipt.json")
    assert [c for c in audit.checks if not c.ok and not c.subject.startswith("cas:")] == []
    with pytest.raises(engine.CensusError, match="preexecution output is not absent"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)


def test_pagination_overflow_is_terminal_without_publication(
    tmp_path: Path, small_freeze: None
) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config)
    transport, calls = _transport(bad_total=True)
    with pytest.raises(engine.CensusError, match="terminal_delivery_or_schema_failure"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 1
    assert not (root / "data/publication").exists()
    events = [json.loads(line) for line in (root / "data/events.jsonl").read_text().splitlines()]
    assert events[-1]["outcome"] == "terminal_delivery_or_schema_failure"
    assert (root / "workspace/cma/.execution.lock").is_file()
    with pytest.raises(engine.CensusError, match="preexecution output is not absent"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)


def test_cross_painter_duplicate_is_terminal(tmp_path: Path, small_freeze: None) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config)
    transport, calls = _transport(shared_id=True)
    with pytest.raises(engine.CensusError, match="terminal_delivery_or_schema_failure"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert len(calls) == 2
    assert not (root / "data/publication").exists()


def test_review_without_reviewer_kind_or_with_findings_is_refused(
    tmp_path: Path, small_freeze: None
) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config, reviewer_kind="committee")
    transport, calls = _transport()
    with pytest.raises(engine.CensusError, match="review is invalid"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert calls == []
    review_path = root / "data/review.json"
    review = json.loads(review_path.read_text())
    review["reviewer_kind"] = "human"
    review["blocking_findings"] = ["open finding"]
    _write_json(review_path, review)
    with pytest.raises(engine.CensusError, match="hash mismatch"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert calls == []


def test_frozen_config_drift_blocks_before_network(tmp_path: Path, small_freeze: None) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config)
    changed = copy.deepcopy(config)
    changed["source_contract"]["timeout_seconds"] = 61.0
    _write_json(config_path, changed)
    transport, calls = _transport()
    with pytest.raises(engine.CensusError, match="frozen input hash mismatch"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, transport)
    assert calls == []


def test_non_json_content_type_is_terminal(tmp_path: Path, small_freeze: None) -> None:
    root, config_path, config = _repo(tmp_path)
    engine.prepare(ROUTE, root, config_path)
    seal_path, seal_sha = _authorize(root, config)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            502,
            request=request,
            headers={"Date": "Fri, 04 Sep 2098 12:00:00 GMT", "Content-Type": "text/html"},
            content=b"<html>bad gateway</html>",
        )

    with pytest.raises(engine.CensusError, match="terminal_delivery_or_schema_failure"):
        engine.execute(ROUTE, root, config_path, seal_path, seal_sha, httpx.MockTransport(handler))
    events = [json.loads(line) for line in (root / "data/events.jsonl").read_text().splitlines()]
    assert events[-1]["status_code"] == 502
    assert len(list((root / "workspace/cma/response_bodies").rglob("*.response"))) == 1


def test_as_int_accepts_decimal_strings_only() -> None:
    assert engine.as_int(5) == 5
    assert engine.as_int("893") == 893
    assert engine.as_int(" 12 ") == 12
    assert engine.as_int(True) is None
    assert engine.as_int(3.0) is None
    assert engine.as_int("3.0") is None
    assert engine.as_int(None) is None
