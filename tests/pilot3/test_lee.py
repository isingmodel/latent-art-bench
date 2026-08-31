from __future__ import annotations

from pathlib import Path

import pytest

from latent_art_bench.pilot3.lee import (
    LeeEvidenceError,
    build_lee_replication,
    verify_lee_replication,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_lee_fixture_review_terminates_as_ineligible_retire(tmp_path: Path) -> None:
    result = build_lee_replication(REPOSITORY_ROOT, output_path=tmp_path / "lee.json")
    assert result["status"] == "ineligible_retire"
    assert result["eligibility_review"]["exact_original_fixture_available"] is False
    assert result["eligibility_review"][
        "supports_native_500_to_3000_pixel_series_without_upsampling"
    ] is False
    assert [row["decision"] for row in result["reviewers"]] == [
        "ineligible_retire",
        "ineligible_retire",
    ]
    assert result["phase_b_effect"]["lee_measurement_included"] is False
    assert verify_lee_replication(result) == result["result_sha256"]


def test_lee_verifier_rejects_tampering(tmp_path: Path) -> None:
    result = build_lee_replication(REPOSITORY_ROOT, output_path=tmp_path / "lee.json")
    result["status"] = "pass"
    with pytest.raises(LeeEvidenceError, match="terminal status"):
        verify_lee_replication(result)
