from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from latent_art_bench.pilot3.feasibility import (
    DEFAULT_CANDIDATE_ARTISTS,
    CandidateArtist,
    Pilot3FeasibilityConfig,
    audit_feasibility,
    audit_metadata_files,
    verify_feasibility_result,
)


def _row(
    artist_id: str,
    source_id: str,
    source_object_id: str,
    *,
    artist_name: str | None = None,
    wikidata_id: str | None = None,
    decision: str = "include",
) -> dict:
    row = {
        "artist_id": artist_id,
        "artist_name": artist_name or artist_id.replace("_", " ").title(),
        "decision": decision,
        "description": "Ignored catalog prose.",
        "image_width": 1024,
        "image_url": f"https://invalid.example/{source_object_id}.jpg",
        "local_path": f"/must/not/be-opened/{source_object_id}.png",
        "public_domain_status": "confirmed",
        "source_id": source_id,
        "source_object_id": source_object_id,
        "title": f"Work {source_object_id}",
    }
    if wikidata_id is not None:
        row["wikidata_id"] = wikidata_id
    return row


def _config(
    artists: tuple[CandidateArtist, ...],
    *,
    works: int = 2,
    artist_count: int = 2,
    source_count: int = 2,
) -> Pilot3FeasibilityConfig:
    return Pilot3FeasibilityConfig(
        candidate_artists=artists,
        min_unique_works_per_artist_source=works,
        min_artist_count=artist_count,
        min_source_count=source_count,
    )


def _balanced_rows(artist_ids: tuple[str, ...], source_ids: tuple[str, ...]) -> list[dict]:
    rows = []
    for artist_id in artist_ids:
        for source_id in source_ids:
            rows.extend(
                _row(artist_id, source_id, f"{artist_id}-{source_id}-{index}") for index in range(2)
            )
    return rows


def test_feasible_biclique_is_coverage_based_and_deterministic() -> None:
    artists = (
        CandidateArtist("artist_a", "Artist A"),
        CandidateArtist("artist_b", "Artist B"),
        CandidateArtist("artist_c", "Artist C"),
    )
    rows = _balanced_rows(("artist_a", "artist_b"), ("museum_x", "museum_y"))
    rows.extend(
        [
            _row("artist_c", "museum_x", "c-x-0"),
            _row("artist_c", "museum_x", "c-x-1"),
            _row("artist_c", "museum_y", "c-y-0"),
        ]
    )
    # A rich artist outside the configured roster must not displace candidates.
    rows.extend(_balanced_rows(("artist_z",), ("museum_x", "museum_y")))
    config = _config(artists)

    forward = audit_feasibility(rows, config)
    reverse = audit_feasibility(list(reversed(rows)), config)

    assert forward == reverse
    assert forward["status"] == "metadata_snapshot_audit_complete_not_freeze_ready"
    assert forward["configured_snapshot_threshold_result"] == (
        "meets_configured_snapshot_thresholds"
    )
    assert forward["threshold_meeting_biclique"]["qualifying_artist_ids"] == [
        "artist_a",
        "artist_b",
    ]
    assert forward["out_of_scope_observed_artists"][0]["artist_id"] == "artist_z"
    assert verify_feasibility_result(forward)


def test_default_candidate_roster_contains_only_named_artist_candidates() -> None:
    assert {artist.artist_name for artist in DEFAULT_CANDIDATE_ARTISTS} == {
        "Alfred Sisley",
        "Armand Guillaumin",
        "Berthe Morisot",
        "Camille Pissarro",
        "Claude Monet",
        "Eugène Boudin",
        "Gustave Caillebotte",
        "Paul Cezanne",
        "Pierre-Auguste Renoir",
    }


def test_physical_work_deduplication_requires_disjoint_source_assignment() -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    rows = [
        _row("artist_a", "museum_x", "x-shared", wikidata_id="Q1"),
        _row("artist_a", "museum_y", "y-shared", wikidata_id="Q1"),
        _row("artist_a", "museum_x", "x-only", wikidata_id="Q2"),
        _row("artist_a", "museum_y", "y-only", wikidata_id="Q3"),
        # Repeated source metadata cannot inflate the museum_x count.
        _row("artist_a", "museum_x", "x-only", wikidata_id="Q2"),
    ]
    config = _config(artists, artist_count=1)

    result = audit_feasibility(rows, config)

    assert result["configured_snapshot_threshold_result"] == (
        "does_not_meet_configured_snapshot_thresholds"
    )
    counts = result["artist_source_counts"][0]["sources"]
    assert [item["eligible_unique_physical_work_count"] for item in counts] == [2, 2]
    best_artist = result["best_available_biclique"]["artist_coverage"][0]
    assert best_artist["maximum_disjoint_balanced_works_per_source"] == 1
    assert result["deduplication"]["duplicate_rows_removed"] == 2
    assert result["deduplication"]["cross_source_duplicate_group_count"] == 1


def test_title_and_year_are_never_used_to_infer_duplicate_works() -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    rows = [
        _row("artist_a", "museum_x", "x-1"),
        _row("artist_a", "museum_x", "x-2"),
    ]
    for row in rows:
        row["title"] = "Repeated title from a series"
        row["creation_year"] = 1890
    config = _config(artists, works=2, artist_count=1, source_count=1)

    result = audit_feasibility(rows, config)

    assert result["configured_snapshot_threshold_result"] == (
        "meets_configured_snapshot_thresholds"
    )
    assert result["deduplication"]["unique_physical_work_count"] == 2


def test_ignored_asset_metadata_cannot_change_selection() -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    rows = _balanced_rows(("artist_a",), ("museum_x", "museum_y"))
    config = _config(artists, artist_count=1)
    first = audit_feasibility(rows, config)
    mutated = copy.deepcopy(rows)
    for index, row in enumerate(mutated):
        row["image_url"] = f"file:///different-toxic-image-{index}.png"
        row["local_path"] = f"/different/path/{index}.tiff"
        row["description"] = "This ignored prose must not influence coverage."
        row["image_width"] = 1 + index
    second = audit_feasibility(mutated, config)

    assert first == second
    assert "local_path" in first["input_summary"]["ignored_field_names"]
    assert first["metadata_only_guarantee"]["image_or_referenced_asset_io"] == "none"


def test_loader_never_reads_toxic_referenced_image_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    toxic_image = tmp_path / "toxic.png"
    manifest = tmp_path / "catalog.jsonl"
    row = _row("artist_a", "museum_x", "x-1")
    row["local_path"] = str(toxic_image)
    manifest.write_text(json.dumps(row) + "\n", encoding="utf-8")

    real_read_bytes = Path.read_bytes
    paths_read = []

    def guarded_read_bytes(path: Path) -> bytes:
        paths_read.append(path)
        if path == toxic_image:
            raise AssertionError("referenced image path was opened")
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    config = _config(artists, works=1, artist_count=1, source_count=1)

    result = audit_metadata_files([manifest], config)

    assert paths_read == [manifest]
    assert result["configured_snapshot_threshold_result"] == (
        "meets_configured_snapshot_thresholds"
    )
    assert result["input_evidence"] == [
        {
            "format": "jsonl",
            "manifest_bytes_sha256": result["input_evidence"][0]["manifest_bytes_sha256"],
            "manifest_path": str(manifest),
            "referenced_asset_io_performed": False,
            "row_count": 1,
        }
    ]


@pytest.mark.parametrize(
    "forbidden",
    [
        {"feature_vector": [0.1, 0.2]},
        {"effect_estimate": 0.4},
        {"generated_output": "/tmp/result.png"},
        {"record_type": "generation_call"},
        {"nested": {"p_value": 0.01}},
        {"origin": "generated"},
    ],
)
def test_generated_feature_and_effect_signals_are_rejected(forbidden: dict) -> None:
    row = _row("artist_a", "museum_x", "x-1")
    row.update(forbidden)
    config = _config(
        (CandidateArtist("artist_a", "Artist A"),),
        works=1,
        artist_count=1,
        source_count=1,
    )

    with pytest.raises(ValueError, match="metadata-only audit rejects"):
        audit_feasibility([row], config)


def test_unobserved_candidates_and_infeasibility_are_explicit() -> None:
    artists = (
        CandidateArtist("artist_a", "Artist A"),
        CandidateArtist("artist_missing", "Artist Missing"),
    )
    rows = [_row("artist_a", "museum_x", "x-1")]
    config = _config(artists, works=2, artist_count=2, source_count=2)

    result = audit_feasibility(rows, config)

    assert result["status"] == "metadata_snapshot_audit_complete_not_freeze_ready"
    assert result["configured_snapshot_threshold_result"] == (
        "does_not_meet_configured_snapshot_thresholds"
    )
    assert result["threshold_meeting_biclique"] is None
    assert result["observed_candidate_artist_ids"] == ["artist_a"]
    assert result["unobserved_candidate_artist_ids"] == ["artist_missing"]
    assert result["claim_boundary"]["external_catalog_coverage_claimed"] is False
    assert result["claim_boundary"]["freeze_a1_ready"] is False
    assert result["eligibility_scope"]["artifact_reapplies_full_domain_rules"] is False
    assert result["eligibility_scope"]["trusted_snapshot_flag"] == ("upstream decision=include")
    assert result["freeze_readiness"]["freeze_a1_ready"] is False
    assert result["freeze_readiness"]["readiness_transition_supported_by_this_schema"] is False
    assert (
        "source governance and acquisition-source independence"
        in result["freeze_readiness"]["unverified_prerequisites"]
    )
    assert (
        "supplied local metadata snapshot"
        in result["claim_boundary"]["threshold_not_met_interpretation"]
    )
    missing_summary = next(
        item for item in result["candidate_artists"] if item["artist_id"] == "artist_missing"
    )
    assert missing_summary["coverage_interpretation"] == (
        "unknown_no_local_metadata_not_zero_works"
    )
    assert {reason["code"] for reason in result["threshold_result_reasons"]} == {
        "observed_candidate_artist_shortfall",
        "source_count_shortfall",
    }


def test_in_scope_artist_name_must_match_frozen_roster_exactly() -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    row = _row(
        "artist_a",
        "museum_x",
        "x-1",
        artist_name="Artist A (attributed spelling)",
    )
    config = _config(artists, works=1, artist_count=1, source_count=1)

    with pytest.raises(ValueError, match="does not exactly match the frozen roster"):
        audit_feasibility([row], config)


def test_self_hash_is_canonical_json_and_detects_tampering() -> None:
    artists = (CandidateArtist("artist_a", "Artist A"),)
    config = _config(artists, works=1, artist_count=1, source_count=1)
    result = audit_feasibility([_row("artist_a", "museum_x", "x-1")], config)

    json.dumps(result, allow_nan=False)
    assert verify_feasibility_result(result)
    tampered = copy.deepcopy(result)
    tampered["status"] = "tampered"
    with pytest.raises(ValueError, match="semantic_sha256 mismatch"):
        verify_feasibility_result(tampered)


def test_identity_collision_across_artists_fails_closed() -> None:
    artists = (
        CandidateArtist("artist_a", "Artist A"),
        CandidateArtist("artist_b", "Artist B"),
    )
    rows = [
        _row("artist_a", "museum_x", "x-1", wikidata_id="Q-SHARED"),
        _row("artist_b", "museum_y", "y-1", wikidata_id="Q-SHARED"),
    ]

    with pytest.raises(ValueError, match="links multiple artists"):
        audit_feasibility(rows, _config(artists, works=1, source_count=1))
