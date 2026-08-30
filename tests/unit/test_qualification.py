from latent_art_bench.evaluation.qualification import (
    qualification_card_from_evidence,
    qualification_gate,
)
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


def test_pass_and_conditional_pass_open_gate() -> None:
    allowed, _ = qualification_gate(
        ["chromatic", "learned_formal"],
        [card("chromatic", "pass"), card("learned_formal", "conditional_pass")],
    )
    assert allowed is True


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
