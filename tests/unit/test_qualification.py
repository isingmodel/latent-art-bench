from pathlib import Path

import pytest

from latent_art_bench.evaluation.qualification import (
    qualification_card_from_evidence,
    qualification_gate,
    validate_qualification_artifact_binding,
)
from latent_art_bench.io import hash_file, stable_hash, write_json
from latent_art_bench.schemas import QualificationCard, QualificationEvidence


def card(measurement: str, status: str) -> QualificationCard:
    return QualificationCard(
        measurement=measurement,
        status=status,
        feature_version="v1",
        feature_config_hash="hash",
    )


def test_pending_card_keeps_gate_closed() -> None:
    allowed, decisions = qualification_gate(
        ["chromatic", "learned_formal"],
        [card("chromatic", "pass"), card("learned_formal", "pending")],
    )
    assert allowed is False
    assert decisions == {"chromatic": "pass", "learned_formal": "pending"}


def test_only_unconditional_pass_cards_open_gate() -> None:
    allowed, decisions = qualification_gate(
        ["chromatic", "learned_formal"],
        [card("chromatic", "pass"), card("learned_formal", "conditional_pass")],
    )
    assert allowed is False
    assert decisions == {
        "chromatic": "pass",
        "learned_formal": "conditional_pass",
    }


def test_passing_card_for_different_feature_identity_keeps_gate_closed() -> None:
    allowed, decisions = qualification_gate(
        ["chromatic"],
        [card("chromatic", "pass")],
        {"chromatic": ("v2", "different-hash")},
    )
    assert allowed is False
    assert decisions == {"chromatic": "identity_mismatch"}


def test_evidence_failure_is_machine_readable() -> None:
    evidence = QualificationEvidence(
        measurement="chromatic",
        feature_version="v1",
        feature_config_hash="hash",
        real_work_count=30,
        reproduction_pair_count=15,
        source_behavior_recovered=True,
        stable_within_frozen_margin=True,
        held_out_artist_signal_valid=True,
        source_confounding_controlled=False,
    )
    result = qualification_card_from_evidence(evidence)
    assert result.status == "fail"
    assert any("confounding" in reason for reason in result.reasons)


def test_conditional_card_keeps_supported_scope_distinct_from_limitations() -> None:
    evidence = QualificationEvidence(
        measurement="chromatic",
        feature_version="v2",
        feature_config_hash="hash",
        real_work_count=30,
        reproduction_pair_count=7,
        source_behavior_recovered=True,
        stable_within_frozen_margin=True,
        held_out_artist_signal_valid=True,
        source_confounding_controlled=True,
        conditional_domains=["JPEG is unsupported"],
        supported_scope=["lossless primary files"],
        evidence_paths=["artifact.json"],
    )

    result = qualification_card_from_evidence(evidence)

    assert result.status == "conditional_pass"
    assert result.conditional_domains == ["JPEG is unsupported"]
    assert result.supported_scope == ["lossless primary files"]


def test_explicit_artifact_failure_controls_card_when_boolean_checks_pass() -> None:
    evidence = QualificationEvidence(
        measurement="learned_formal",
        qualification_result_status="fail",
        feature_version="v2",
        feature_config_hash="hash",
        real_work_count=30,
        reproduction_pair_count=7,
        source_behavior_recovered=True,
        stable_within_frozen_margin=True,
        held_out_artist_signal_valid=True,
        source_confounding_controlled=True,
        conditional_domains=["PCA target is unsupported"],
        notes=["Unsupported: frozen 95% PCA variance target"],
        evidence_paths=["artifact.json"],
    )

    result = qualification_card_from_evidence(evidence)

    assert result.status == "fail"
    assert result.supported_scope == []
    assert result.reasons == ["Unsupported: frozen 95% PCA variance target"]


def test_current_contract_gate_requires_content_addressed_result() -> None:
    current = card("chromatic", "pass").model_copy(
        update={"qualification_contract_hash": "c" * 64}
    )

    allowed, decisions = qualification_gate(
        ["chromatic"], [current], {"chromatic": ("v1", "hash", "c" * 64)}
    )

    assert allowed is False
    assert decisions == {"chromatic": "evidence_unbound"}


def test_qualification_artifact_binding_detects_tampering(tmp_path: Path) -> None:
    payload = {
        "status": "fail",
        "feature_config_sha256": "f" * 64,
        "reason": "frozen failure",
    }
    result_hash = stable_hash(payload)
    artifact_path = tmp_path / "qualification.json"
    write_json(
        artifact_path,
        {
            "record_type": "chromatic_v2_qualification",
            "schema_version": "2.0",
            **payload,
            "result_sha256": result_hash,
        },
    )
    evidence = QualificationEvidence(
        measurement="chromatic",
        feature_version="v2",
        feature_config_hash="f" * 64,
        qualification_contract_hash="c" * 64,
        qualification_result_sha256=result_hash,
        evidence_artifact_sha256=hash_file(artifact_path),
        real_work_count=1,
        reproduction_pair_count=1,
        source_behavior_recovered=False,
        stable_within_frozen_margin=False,
        held_out_artist_signal_valid=False,
        source_confounding_controlled=False,
        evidence_paths=[str(artifact_path)],
    )
    assert validate_qualification_artifact_binding(evidence, tmp_path) == artifact_path

    write_json(artifact_path, {"tampered": True})
    with pytest.raises(ValueError, match="artifact SHA-256"):
        validate_qualification_artifact_binding(evidence, tmp_path)
