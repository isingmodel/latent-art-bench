from __future__ import annotations

import ast
import json
import shutil
import socket
from pathlib import Path

import pytest
from typer.testing import CliRunner

from latent_art_bench.cli import app as root_app
from latent_art_bench.io import read_json
from latent_art_bench.pilot3.planning import (
    DEFAULT_BASELINE_EVIDENCE,
    DEFAULT_DESIGN_EVIDENCE,
    DEFAULT_FEASIBILITY_EVIDENCE,
    DEFAULT_PLANNING_INDEX,
    PILOT2_BASELINE_SCHEMA,
    verify_planning_bundle,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PLANNING_FIXTURE_PATHS = (
    Path("configs/pilot_0/candidate_work_audit.jsonl"),
    Path("configs/pilot_0/manifests/canonical_works.jsonl"),
    Path("configs/pilot_0/manifests/reproductions.jsonl"),
    Path("configs/pilot_3/corpus_freeze.json"),
    Path("configs/pilot_3/external_museum_blocks.json"),
    Path("configs/pilot_3/metadata/authoritative_candidates.jsonl"),
    Path("configs/pilot_3/metadata/source_snapshots.json"),
    Path("configs/pilot_3/planning.json"),
    Path("docs/PILOT_3_PROTOCOL.md"),
    Path("reports/pilot_2/analysis.json"),
    Path("reports/pilot_2/evidence/generation_completion.json"),
    Path("reports/pilot_2/evidence/learned_formal_qualification.json"),
    Path("reports/pilot_3/evidence/historical/artist_source_feasibility_planning_snapshot.json"),
    Path("pyproject.toml"),
    Path("src/latent_art_bench/cli.py"),
    Path("src/latent_art_bench/io.py"),
    Path("src/latent_art_bench/pilot3/cli.py"),
    Path("src/latent_art_bench/pilot3/corpus.py"),
    Path("src/latent_art_bench/pilot3/design.py"),
    Path("src/latent_art_bench/pilot3/feasibility.py"),
    Path("src/latent_art_bench/pilot3/planning.py"),
    Path("tests/pilot3/test_design.py"),
    Path("tests/pilot3/test_pilot3_corpus.py"),
    Path("tests/pilot3/test_feasibility.py"),
    Path("tests/pilot3/test_planning.py"),
    Path("uv.lock"),
)


def _copy_planning_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "planning-root"
    for relative in PLANNING_FIXTURE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / relative, target)
    return root


def test_plan_and_verify_are_offline_fail_closed_and_tamper_evident(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_planning_fixture(tmp_path)

    def reject_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError(f"Pilot 3 planning attempted socket I/O: {args!r} {kwargs!r}")

    monkeypatch.setattr(socket, "socket", reject_socket)
    runner = CliRunner()
    planned = runner.invoke(root_app, ["pilot3", "plan", "--root", str(root)])
    assert planned.exit_code == 0, planned.output
    command_result = json.loads(planned.stdout)
    assert command_result["generation_gate"] == "closed"
    assert command_result["design_decision"] == ("NO_DESIGN_SELECTED_CRITERIA_UNRESOLVED")
    assert command_result["successor_metadata_decision"] == (
        "SNAPSHOT_THRESHOLD_MET_FREEZE_A1_READY"
    )
    assert command_result["metadata_audit_decision"] == ("METADATA_AUDIT_COMPLETE_FREEZE_A1_READY")
    assert command_result["freeze_a1_ready"] is True
    assert command_result["phase_a_artwork_acquisition_authorized"] is True

    baseline = read_json(root / DEFAULT_BASELINE_EVIDENCE)
    assert baseline["schema_version"] == PILOT2_BASELINE_SCHEMA
    assert baseline["status"] == "pass"
    assert baseline["recovered_generation"]["cell_count"] == 320
    assert baseline["recovered_generation"]["successful_output_count"] == 315
    assert baseline["recovered_analysis"]["itt"]["complete_feature_pairs"] == 251
    assert baseline["recovered_analysis"]["itt"]["refused_pairs"] == 5
    assert baseline["recovered_analysis"]["incomplete_artist_ids"] == ["paul_cezanne"]
    assert baseline["recovered_learned_formal_qualification"]["status"] == "pass"
    assert all(
        row["test_status"] == "not_tested_incomplete_feature_grid"
        for row in baseline["recovered_analysis"]["primary_descriptive_estimates"]
    )

    design = read_json(root / DEFAULT_DESIGN_EVIDENCE)
    assert design["design_decision"] == "NO_DESIGN_SELECTED_CRITERIA_UNRESOLVED"
    assert design["prospective_acceptance_criteria_frozen"] is False
    assert design["recommended_feasible_designs"] == []
    feasibility = read_json(root / DEFAULT_FEASIBILITY_EVIDENCE)
    assert feasibility["status"] == ("authoritative_metadata_audit_complete_freeze_a1_ready")
    assert feasibility["configured_snapshot_threshold_result"] == (
        "meets_configured_snapshot_thresholds"
    )
    assert feasibility["freeze_readiness"]["freeze_a1_ready"] is True
    assert feasibility["unobserved_candidate_artist_ids"] == []

    index = read_json(root / DEFAULT_PLANNING_INDEX)
    assert index["status"] == ("offline_planning_and_freeze_a1_complete_generation_gate_closed")
    assert index["decision"]["planning_bundle_emitted"] is True
    assert index["decision"]["offline_evidence_bundle_verifiable"] is True
    assert index["decision"]["planning_prerequisites_resolved"] is True
    assert index["decision"]["metadata_audit_decision"] == (
        "METADATA_AUDIT_COMPLETE_FREEZE_A1_READY"
    )
    assert index["decision"]["successor_snapshot_threshold_result"] == (
        "meets_configured_snapshot_thresholds"
    )
    assert index["decision"]["p3_t01_freeze_ready"] is True
    assert index["decision"]["p3_t02_baseline_recovery_passed"] is True
    assert index["decision"]["p3_t04_final_design_selected"] is False
    assert index["decision"]["p3_t05_corpus_selection_emitted"] is True
    assert index["decision"]["p3_t06_real_split_and_holdout_seal_emitted"] is True
    assert index["decision"]["phase_a_artwork_acquisition_authorized"] is True
    assert index["offline_integrity"]["network_requests_made"] is False
    assert index["offline_integrity"]["image_requests_made"] is False
    assert (
        index["offline_integrity"]["feature_or_generated_outcomes_used_by_current_computation"]
        is False
    )
    assert index["offline_integrity"]["upstream_selection_provenance_verified"] is True
    assert set(index["verification_file_sha256"]) == {
        "tests/pilot3/test_design.py",
        "tests/pilot3/test_pilot3_corpus.py",
        "tests/pilot3/test_feasibility.py",
        "tests/pilot3/test_planning.py",
    }
    assert set(index["environment_lock_file_sha256"]) == {"pyproject.toml", "uv.lock"}

    verified = runner.invoke(root_app, ["pilot3", "verify", "--root", str(root)])
    assert verified.exit_code == 0, verified.output
    assert json.loads(verified.stdout)["status"] == "verified"

    feasibility["status"] = "tampered"
    (root / DEFAULT_FEASIBILITY_EVIDENCE).write_text(json.dumps(feasibility), encoding="utf-8")
    with pytest.raises(RuntimeError, match="stale deterministic"):
        verify_planning_bundle(root)


def test_pilot3_planning_modules_have_no_network_or_image_client_imports() -> None:
    forbidden_roots = {
        "PIL",
        "httpx",
        "playwright",
        "requests",
        "selenium",
        "urllib",
    }
    package = REPOSITORY_ROOT / "src/latent_art_bench/pilot3"
    planning_modules = ("design.py", "feasibility.py", "planning.py")
    violations = []
    for filename in planning_modules:
        path = package / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                if name.split(".", 1)[0] in forbidden_roots:
                    violations.append(f"{path.name}:{node.lineno}:{name}")
    assert violations == []
