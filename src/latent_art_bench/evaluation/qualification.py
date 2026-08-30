from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from latent_art_bench.io import read_json, utc_now
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
    if failures:
        status = "fail"
        supported_scope: List[str] = []
    elif evidence.conditional_domains:
        status = "conditional_pass"
        supported_scope = evidence.conditional_domains.copy()
    else:
        status = "pass"
        supported_scope = ["pilot_0 frozen corpus and preprocessing domain"]
    return QualificationCard(
        measurement=evidence.measurement,
        status=status,
        feature_version=evidence.feature_version,
        feature_config_hash=evidence.feature_config_hash,
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
            if card.status not in {"pass", "conditional_pass"}:
                allowed = False
            elif measurement in expected_identities:
                expected_version, expected_hash = expected_identities[measurement]
                if (
                    card.feature_version != expected_version
                    or card.feature_config_hash != expected_hash
                ):
                    decisions[measurement] = "identity_mismatch"
                    allowed = False
    return allowed, decisions
