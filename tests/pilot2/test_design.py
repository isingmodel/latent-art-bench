from __future__ import annotations

from pathlib import Path

from latent_art_bench.io import hash_file, read_json, stable_hash
from latent_art_bench.pilot2.config import load_pilot2_config
from latent_art_bench.pilot2.design import build_sample_size_sensitivity

ROOT = Path(__file__).resolve().parents[2]


def test_frozen_sample_size_sensitivity_is_reproducible_and_pinned() -> None:
    config = load_pilot2_config(ROOT / "configs/pilot_2/pilot.yaml")
    path = ROOT / config.design.sensitivity_artifact
    observed = read_json(path)
    expected = build_sample_size_sensitivity(
        draws=config.design.simulation_draws,
        seed=config.design.simulation_seed,
    )

    assert observed == expected
    assert hash_file(path) == config.design.sensitivity_artifact_sha256
    unsigned = {key: value for key, value in observed.items() if key != "evidence_sha256"}
    assert stable_hash(unsigned) == observed["evidence_sha256"]


def test_design_records_exact_resolution_and_honest_scope() -> None:
    evidence = build_sample_size_sensitivity(draws=1_000, seed=20_260_901)
    exact = evidence["exact_sign_flip_resolution"]
    assert exact["minimum_attainable_p"] == 1 / 256
    assert exact["maximum_passing_exceedance_count_under_strict_0_0125"] == 3
    assert exact["largest_attainable_p_below_strict_0_0125"] == 3 / 256
    by_block = {row["block_count"]: row for row in exact["block_count_sensitivity"]}
    assert not by_block[6]["four_equal_minimum_can_pass_strict_0_05"]
    assert by_block[7]["four_equal_minimum_can_pass_strict_0_05"]
    assert "not an empirical effect estimate" in evidence["claim_boundary"]
    assert "top-level n remains eight" in evidence["decision"]
