"""Regression tests for the findings of the PR #3 review."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from latent_art_bench import evidence
from latent_art_bench.io import canonical_json
from latent_art_bench.painter_feature_generation_v1 import (
    artifact_cli,
    exposure_denylist,
    panel,
    prompt_library,
    scene_prescreen,
)
from latent_art_bench.painter_feature_generation_v1 import census_engine as engine
from latent_art_bench.painter_feature_generation_v1 import cleveland_metadata as cma
from latent_art_bench.painter_feature_generation_v1 import content_lexicon as lex

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
needs_history = pytest.mark.skipif(
    shutil.which("git") is None or not (REPOSITORY_ROOT / ".git").exists(),
    reason="repository history is required",
)
FREEZE_RELATIVE = str(evidence.MANIFEST_DIR / "f_freeze.json")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=True, text=True
    ).stdout.strip()


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "test")
    _git(root, "config", "commit.gpgsign", "false")
    return root


def _commit(root: Path, message: str) -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _acknowledge(path: str, bound: str | None) -> dict:
    row = {"freeze_path": FREEZE_RELATIVE, "frozen_input_path": path}
    if bound is not None:
        row["bound_sha256"] = bound
    return {"unrecoverable_frozen_inputs": [row]}


def _freeze_for(root: Path, entries: list) -> Path:
    freeze = {
        "frozen_inputs": entries,
        "frozen_input_set_sha256": _sha(canonical_json(entries).encode()),
        "preexecution_outputs": [],
    }
    path = root / FREEZE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    return path


def _chain(rows: list[dict]) -> list[dict]:
    events = []
    previous = evidence.GENESIS_PREVIOUS
    for sequence, fields in enumerate(rows, start=1):
        row = {"sequence": sequence, "previous_event_sha256": previous, **fields}
        row["event_sha256"] = _sha(canonical_json(row).encode())
        events.append(row)
        previous = row["event_sha256"]
    return events


# ---------------------------------------------------------------- JSONL line splitting


def test_jsonl_readers_split_on_line_feed_only() -> None:
    row = {"label": "Bords de la Seine a Argenteuil", "note": "xy"}
    body = (canonical_json(row) + "\n").encode("utf-8")
    assert engine.jsonl_objects(body, "ledger") == [row]
    assert exposure_denylist._rows(body) == [row]


def test_scene_prescreen_reader_hashes_and_splits_once(tmp_path: Path) -> None:
    row = {"label": "Nymphéas reflets"}
    path = tmp_path / "rows.jsonl"
    path.write_bytes((canonical_json(row) + "\n").encode("utf-8"))
    rows, digest = scene_prescreen._read_jsonl(path)
    assert rows == [row]
    assert digest == _sha(path.read_bytes())


# ---------------------------------------------------------------- lexicon punctuation


def test_typographic_apostrophes_and_dashes_match_ascii_lexicon_entries() -> None:
    curly = lex.classify("Hémérocalles au bord de l’eau")
    plain = lex.classify("Hémérocalles au bord de l'eau")
    assert curly["disposition"] == plain["disposition"] == lex.ELIGIBLE
    assert lex.classify("The Artist’s Son")["disposition"] == lex.INELIGIBLE
    assert lex.classify("Self–portrait")["disposition"] == lex.INELIGIBLE
    assert lex.classify("Belle‐Île")["disposition"] == lex.ELIGIBLE


# ---------------------------------------------------------------- evidence: git batch


@needs_git
def test_bytes_at_commits_batches_and_reports_missing(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "a.txt").write_bytes(b"alpha\n")
    (root / "sub").mkdir()
    (root / "sub" / "b.txt").write_bytes(b"beta\n")
    head = _commit(root, "one")
    found = evidence.bytes_at_commits(
        root, [f"{head}:a.txt", f"{head}:sub/b.txt", f"{head}:missing.txt", f"{head}:sub"]
    )
    assert found[f"{head}:a.txt"] == b"alpha\n"
    assert found[f"{head}:sub/b.txt"] == b"beta\n"
    assert found[f"{head}:missing.txt"] is None
    assert found[f"{head}:sub"] is None
    assert evidence.git_blob_id(b"alpha\n") == _git(root, "rev-parse", f"{head}:a.txt")


# ---------------------------------------------------------------- evidence: acknowledgements


@needs_git
def test_acknowledgement_requires_the_exact_bound_hash(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    bound = root / "src" / "bound.py"
    bound.parent.mkdir()
    bound.write_text("VERSION = 1\n")
    _commit(root, "v1")
    never_committed = _sha(b"VERSION = 1.5\n")
    freeze_path = _freeze_for(root, [{"path": "src/bound.py", "sha256": never_committed}])
    _commit(root, "freeze")

    assert not evidence.verify_freeze(root, freeze_path).ok
    wrong = _acknowledge("src/bound.py", "0" * 64)
    assert not evidence.verify_freeze(root, freeze_path, wrong).ok
    missing = _acknowledge("src/bound.py", None)
    assert not evidence.verify_freeze(root, freeze_path, missing).ok

    report = evidence.verify_freeze(
        root, freeze_path, _acknowledge("src/bound.py", never_committed)
    )
    assert report.ok
    assert report.acknowledged_unrecoverable == ["src/bound.py"]


@needs_git
def test_history_is_preferred_over_an_acknowledgement(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    bound = root / "bound.txt"
    bound.write_text("old\n")
    _commit(root, "old")
    old_hash = _sha(b"old\n")
    bound.write_text("new\n")
    freeze_path = _freeze_for(root, [{"path": "bound.txt", "sha256": old_hash}])
    _commit(root, "freeze binding the older bytes")

    report = evidence.verify_freeze(root, freeze_path, _acknowledge("bound.txt", old_hash))
    assert report.ok
    assert report.acknowledged_unrecoverable == []
    assert any(check.subject == "input@history:bound.txt" for check in report.checks)


@needs_git
def test_untracked_input_can_be_acknowledged(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".gitignore").write_text("workspace/\n")
    _commit(root, "ignore the workspace")
    lost = _sha(b"regenerated later\n")
    freeze_path = _freeze_for(root, [{"path": "workspace/raw.bin", "sha256": lost}])
    _commit(root, "freeze")

    assert not evidence.verify_freeze(root, freeze_path).ok
    report = evidence.verify_freeze(root, freeze_path, _acknowledge("workspace/raw.bin", lost))
    assert report.ok
    assert report.acknowledged_unrecoverable == ["workspace/raw.bin"]


# ---------------------------------------------------------------- evidence: receipts


@needs_git
def test_receipt_falls_back_to_history_and_cross_checks_the_ledger(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    manifests = root / evidence.MANIFEST_DIR
    manifests.mkdir(parents=True)
    config = manifests / "config.json"
    config.write_text('{"v": 1}\n')
    events = _chain(
        [
            {"event_type": "execution_started", "census_id": "c"},
            {
                "event_type": "request_finished",
                "census_id": "c",
                "request_id": "r1",
                "outcome": "success",
            },
        ]
    )
    ledger = manifests / "x_request_events.jsonl"
    ledger.write_text("".join(canonical_json(event) + "\n" for event in events))
    receipt = {
        "census_id": "c",
        "config_path": str(evidence.MANIFEST_DIR / "config.json"),
        "config_sha256": _sha(b'{"v": 1}\n'),
        "request_event_ledger_path": str(evidence.MANIFEST_DIR / "x_request_events.jsonl"),
        "request_event_ledger_sha256": _sha(ledger.read_bytes()),
        "execution_genesis_event_sha256": events[0]["event_sha256"],
        "terminal_event_sha256": events[-1]["event_sha256"],
        "request_event_count": 2,
        "successful_requests": 1,
        "response_inventory": [],
    }
    receipt_path = manifests / "x_execution_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    _commit(root, "receipt")
    config.write_text('{"v": 2}\n')
    _commit(root, "config drift")

    report = evidence.verify_receipt(root, receipt_path)
    assert report.ok, report.as_dict()
    config_checks = [check for check in report.checks if "config_path" in check.subject]
    assert config_checks and "matches commit" in config_checks[0].detail

    receipt["terminal_event_sha256"] = "0" * 64
    receipt["request_event_count"] = 3
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    failed = {
        check.subject
        for check in evidence.verify_receipt(root, receipt_path).checks
        if not check.ok
    }
    assert failed == {"terminal_event_sha256", "request_event_count"}


def test_ledger_blank_lines_and_mixed_census_ids_fail(tmp_path: Path) -> None:
    events = _chain([{"census_id": "a"}, {"census_id": "b"}])
    ledger = tmp_path / "events.jsonl"
    ledger.write_text(canonical_json(events[0]) + "\n\n" + canonical_json(events[1]) + "\n")
    report = evidence.verify_event_ledger(tmp_path, ledger)
    failed = {check.subject for check in report.checks if not check.ok}
    assert "no_blank_lines" in failed
    assert "single_census_id" in failed


def test_response_bodies_are_found_anywhere_under_the_workspace(tmp_path: Path) -> None:
    digest = "ab" * 32
    directory = tmp_path / evidence.WORKSPACE_DIR / "media" / "run_1" / "response_bodies" / "ab"
    directory.mkdir(parents=True)
    (directory / f"{digest}.response").write_bytes(b"x")
    located = evidence._find_response_body(tmp_path, f"response_bodies/ab/{digest}.response")
    assert located is not None
    assert located.read_bytes() == b"x"


# ---------------------------------------------------------------- census engine


def _engine_repo(tmp_path: Path) -> tuple[Path, Path]:
    root = _repo(tmp_path)
    config = json.loads((REPOSITORY_ROOT / cma.DEFAULT_CONFIG).read_text())
    config["protocol_path"] = "protocol.md"
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
    config_path.write_text(canonical_json(config) + "\n")
    return root, config_path


@pytest.fixture
def small_freeze(monkeypatch: pytest.MonkeyPatch) -> None:
    paths = ["config.json", "data/intents.jsonl", "protocol.md"]
    monkeypatch.setattr(engine, "required_frozen_paths", lambda *_: list(paths))
    monkeypatch.setattr(engine, "declared_frozen_paths", lambda *_: list(paths))


@needs_git
def test_main_accepts_absolute_paths_inside_the_repository(
    tmp_path: Path, small_freeze: None, capsys: pytest.CaptureFixture
) -> None:
    root, config_path = _engine_repo(tmp_path)
    _commit(root, "contract")
    code = engine.main(
        cma.CONTRACT,
        cma.DEFAULT_CONFIG,
        ["--root", str(root), "--config", str(config_path), "prepare"],
    )
    assert code == 0
    assert (root / "data/freeze.json").is_file()

    outside = engine.main(
        cma.CONTRACT,
        cma.DEFAULT_CONFIG,
        ["--root", str(root), "--config", str(tmp_path / "x.json"), "prepare"],
    )
    assert outside == 1
    assert "error:" in capsys.readouterr().err


@needs_git
def test_prepare_refuses_a_tracked_intents_path_without_touching_it(
    tmp_path: Path, small_freeze: None
) -> None:
    root, config_path = _engine_repo(tmp_path)
    (root / "data").mkdir()
    (root / "data/intents.jsonl").write_text('{"frozen": "by an earlier census"}\n')
    _commit(root, "earlier intents are tracked")

    with pytest.raises(engine.CensusError, match="already tracked"):
        engine.prepare(cma.CONTRACT, root, config_path)
    assert (root / "data/intents.jsonl").read_text() == '{"frozen": "by an earlier census"}\n'
    assert not (root / "data/freeze.json").exists()


def test_success_event_audit_rejects_non_monotonic_timestamps() -> None:
    digest = "cd" * 32
    body_path = f"response_bodies/cd/{digest}.response"
    intents = [{"request_id": "r1", "encoded_url": "https://x/?a=1"}]
    finished = {
        "event_type": "request_finished",
        "request_id": "r1",
        "finished_at_utc": "2026-09-04T10:00:00Z",
        "outcome": "success",
        "status_code": 200,
        "final_url": "https://x/?a=1",
        "response_headers": {
            "date": ["Fri, 04 Sep 2026 10:00:00 GMT"],
            "content-type": ["application/json"],
        },
        "response_bytes": 3,
        "response_body_complete": True,
        "response_sha256": digest,
        "response_body_path": body_path,
        "candidate_rows": 1,
        "error": None,
    }
    events = [
        {"event_type": "execution_started", "started_at_utc": "2026-09-04T10:00:05Z"},
        {
            "event_type": "request_started",
            "request_id": "r1",
            "started_at_utc": "2026-09-04T10:00:06Z",
            "encoded_url": "https://x/?a=1",
        },
        finished,
    ]
    inventory = [
        {
            "request_id": "r1",
            "response_sha256": digest,
            "response_bytes": 3,
            "response_body_path": body_path,
            "candidate_rows": 1,
        }
    ]
    with pytest.raises(engine.CensusError, match="frozen request order"):
        engine._validate_success_events(events, intents, inventory, "application/json")
    finished["finished_at_utc"] = "2026-09-04T10:00:07Z"
    engine._validate_success_events(events, intents, inventory, "application/json")


# ---------------------------------------------------------------- artifact tools


@needs_history
def test_denylist_check_covers_the_receipt() -> None:
    expected = exposure_denylist.expected(REPOSITORY_ROOT)
    assert set(expected) == {exposure_denylist.OUTPUT_PATH, exposure_denylist.RECEIPT_PATH}
    assert artifact_cli.check(REPOSITORY_ROOT, expected)["in_sync"] is True

    drifted = dict(expected)
    drifted[exposure_denylist.RECEIPT_PATH] = expected[exposure_denylist.RECEIPT_PATH].replace(
        "2.1", "2.0"
    )
    result = artifact_cli.check(REPOSITORY_ROOT, drifted)
    assert result["in_sync"] is False
    assert result["outputs"][str(exposure_denylist.RECEIPT_PATH)] is False


def test_prescreen_refuses_to_run_without_its_inputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="pre-screen input is missing"):
        scene_prescreen.run(tmp_path)


def test_panel_is_the_single_roster_source() -> None:
    assert prompt_library.PAINTERS == panel.ID_NAME_PAIRS
    assert cma.PAINTERS == panel.ID_NAME_PAIRS
    assert scene_prescreen.PAINTERS == panel.PAINTER_IDS
    assert scene_prescreen.PAINTER_LABELS == panel.SHORT_LABELS
    assert exposure_denylist.PANEL == panel.PAINTER_IDS
