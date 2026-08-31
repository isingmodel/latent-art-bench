from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from latent_art_bench.io import hash_file, read_json, stable_hash, utc_now
from latent_art_bench.schemas import QualificationCard, QualificationEvidence


def qualification_card_from_evidence(evidence: QualificationEvidence) -> QualificationCard:
    checks = {
        "no independent real works were evaluated": evidence.real_work_count > 0,
        "no same-work reproduction pairs were evaluated": evidence.reproduction_pair_count > 0,
        "no evidence artifacts were supplied": bool(evidence.evidence_paths),
        "source behavior was not recovered": evidence.source_behavior_recovered,
        "stability exceeded the frozen margin": evidence.stable_within_frozen_margin,
        "held-out artist signal was not valid": evidence.held_out_artist_signal_valid,
        "source confounding was not controlled": evidence.source_confounding_controlled,
    }
    failures = [reason for reason, passed in checks.items() if not passed]
    explicit_status = evidence.qualification_result_status
    if explicit_status in {"pass", "conditional_pass"} and failures:
        raise ValueError(
            "qualification evidence status disagrees with its required boolean checks"
        )
    if explicit_status == "pass" and evidence.conditional_domains:
        raise ValueError(
            "qualification evidence cannot claim pass while declaring conditional domains"
        )
    if explicit_status == "fail" or failures:
        status = "fail"
        supported_scope: List[str] = []
        if explicit_status == "fail" and not failures and not evidence.notes:
            failures.append("qualification result artifact failed its overall contract")
    elif explicit_status == "conditional_pass" or evidence.conditional_domains:
        status = "conditional_pass"
        supported_scope = (
            evidence.supported_scope.copy()
            if evidence.supported_scope
            else evidence.conditional_domains.copy()
        )
    else:
        status = "pass"
        supported_scope = evidence.supported_scope or [
            "frozen corpus and preprocessing domain"
        ]
    return QualificationCard(
        measurement=evidence.measurement,
        status=status,
        feature_version=evidence.feature_version,
        feature_config_hash=evidence.feature_config_hash,
        qualification_contract_hash=evidence.qualification_contract_hash,
        qualification_result_sha256=evidence.qualification_result_sha256,
        evidence_artifact_sha256=evidence.evidence_artifact_sha256,
        input_feature_manifest_sha256=evidence.input_feature_manifest_sha256,
        source_behavior_recovered=evidence.source_behavior_recovered,
        stable_within_frozen_margin=evidence.stable_within_frozen_margin,
        held_out_artist_signal_valid=evidence.held_out_artist_signal_valid,
        source_confounding_controlled=evidence.source_confounding_controlled,
        real_work_count=evidence.real_work_count,
        reproduction_pair_count=evidence.reproduction_pair_count,
        conditional_domains=evidence.conditional_domains,
        supported_scope=supported_scope,
        evidence_paths=evidence.evidence_paths,
        reasons=failures + evidence.notes,
        decided_at=utc_now(),
    )


def qualification_artifact_result_sha256(artifact: Dict[str, object]) -> str:
    """Recompute the self-hash contract shared by both v2 qualification artifacts."""

    payload = {
        key: value
        for key, value in artifact.items()
        if key not in {"record_type", "schema_version", "result_sha256"}
    }
    return stable_hash(payload)


def validate_qualification_artifact_binding(
    evidence_or_card: QualificationEvidence | QualificationCard,
    root: Path,
) -> Path:
    """Require a content-addressed card/evidence link to a valid result artifact."""

    if evidence_or_card.qualification_contract_hash is None:
        if not evidence_or_card.evidence_paths:
            raise ValueError("qualification record has no evidence artifact")
        return root / evidence_or_card.evidence_paths[0]
    required = {
        "qualification_result_sha256": evidence_or_card.qualification_result_sha256,
        "evidence_artifact_sha256": evidence_or_card.evidence_artifact_sha256,
    }
    missing = sorted(name for name, value in required.items() if value is None)
    if missing:
        raise ValueError(
            "qualification record lacks content-addressed evidence: " + ", ".join(missing)
        )
    if not evidence_or_card.evidence_paths:
        raise ValueError("qualification record has no evidence artifact")
    artifact_path = Path(evidence_or_card.evidence_paths[0])
    if not artifact_path.is_absolute():
        artifact_path = root / artifact_path
    if not artifact_path.is_file():
        raise FileNotFoundError(f"missing qualification artifact: {artifact_path}")
    observed_artifact_hash = hash_file(artifact_path)
    if observed_artifact_hash != evidence_or_card.evidence_artifact_sha256:
        raise ValueError("qualification evidence artifact SHA-256 is stale")
    artifact = read_json(artifact_path)
    if not isinstance(artifact, dict):
        raise ValueError("qualification artifact must be a JSON object")
    recorded_result_hash = artifact.get("result_sha256")
    if recorded_result_hash != qualification_artifact_result_sha256(artifact):
        raise ValueError("qualification artifact has an invalid internal result hash")
    if recorded_result_hash != evidence_or_card.qualification_result_sha256:
        raise ValueError("qualification record points to a different result hash")
    if artifact.get("feature_config_sha256") != evidence_or_card.feature_config_hash:
        raise ValueError("qualification artifact feature identity is stale")
    if isinstance(evidence_or_card, QualificationCard) and (
        artifact.get("status") != evidence_or_card.status
    ):
        raise ValueError("qualification card status disagrees with its result artifact")
    return artifact_path


def load_qualification_cards(paths: Iterable[Path]) -> List[QualificationCard]:
    return [QualificationCard.model_validate(read_json(path)) for path in paths]


def qualification_gate(
    required_measurements: Iterable[str],
    cards: Iterable[QualificationCard],
    expected_identities: Optional[Dict[str, Tuple[str, str]]] = None,
) -> Tuple[bool, Dict[str, str]]:
    expected_identities = expected_identities or {}
    by_measurement = {card.measurement: card for card in cards}
    decisions: Dict[str, str] = {}
    allowed = True
    for measurement in required_measurements:
        card = by_measurement.get(measurement)
        if card is None:
            decisions[measurement] = "missing"
            allowed = False
        else:
            decisions[measurement] = card.status
            if card.status != "pass":
                allowed = False
            elif measurement in expected_identities:
                expected = expected_identities[measurement]
                expected_version, expected_hash = expected[:2]
                if (
                    card.feature_version != expected_version
                    or card.feature_config_hash != expected_hash
                ):
                    decisions[measurement] = "identity_mismatch"
                    allowed = False
                elif len(expected) >= 3 and (
                    card.qualification_contract_hash is None
                    or card.qualification_contract_hash != expected[2]
                ):
                    decisions[measurement] = "contract_mismatch"
                    allowed = False
                elif len(expected) >= 3 and (
                    card.qualification_result_sha256 is None
                    or card.evidence_artifact_sha256 is None
                ):
                    decisions[measurement] = "evidence_unbound"
                    allowed = False
    return allowed, decisions
