from __future__ import annotations

import json
import shutil
import socket
from collections import Counter
from pathlib import Path

import pytest

from latent_art_bench.io import hash_file, read_json, read_jsonl, stable_hash
from latent_art_bench.pilot3.corpus import (
    CORPUS_ROW_SCHEMA,
    DEFAULT_CORPUS_EVIDENCE,
    DEFAULT_CORPUS_MANIFEST,
    DEFAULT_FEASIBILITY_EVIDENCE,
    DEFAULT_HOLDOUT_SEAL,
    DEFAULT_REAL_SPLITS,
    FILE_BACKED_PERMISSION_LICENSE_ID,
    REAL_SPLIT_ROW_SCHEMA,
    REPRODUCTION_PERMISSION_SCHEMA,
    REQUIRED_REPRODUCTION_PERMISSION_SCOPE,
    build_corpus_bundle,
    validate_digital_reproduction_authorization,
    verify_corpus_bundle,
    write_corpus_bundle,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_PATHS = (
    Path("configs/pilot_0/manifests/canonical_works.jsonl"),
    Path("configs/pilot_0/manifests/reproductions.jsonl"),
    Path("configs/pilot_3/corpus_freeze.json"),
    Path("configs/pilot_3/external_museum_blocks.json"),
    Path("configs/pilot_3/metadata/authoritative_candidates.jsonl"),
    Path("configs/pilot_3/metadata/source_snapshots.json"),
    Path("reports/pilot_3/evidence/historical/artist_source_feasibility_planning_snapshot.json"),
)


def _fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "corpus-root"
    for relative in _FIXTURE_PATHS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY_ROOT / relative, target)
    return root


def _verify_row_hash(row: dict[str, object]) -> None:
    payload = dict(row)
    recorded = payload.pop("row_sha256")
    assert stable_hash(payload) == recorded


def _rights_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        "asset_license": "CC0",
        "source_id": "museum",
        "source_object_id": "object-1",
    }
    row.update(updates)
    return row


def _rights_source(**updates: object) -> dict[str, object]:
    source: dict[str, object] = {"asset_governance": "Museum Rights Authority"}
    source.update(updates)
    return source


def _permission_pointer(
    root: Path,
    *,
    authority: str = "Museum Rights Authority",
    expires_at: str = "2027-01-01T00:00:00Z",
    evidence_authority: str | None = None,
    evidence_expires_at: str | None = None,
    evidence_scope: list[str] | None = None,
    pointer_scope: list[str] | None = None,
    source_id: str = "museum",
    source_object_ids: list[str] | None = None,
) -> dict[str, object]:
    path = root / "configs/pilot_3/permissions/museum.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    scope = sorted(REQUIRED_REPRODUCTION_PERMISSION_SCOPE)
    evidence = {
        "schema_version": REPRODUCTION_PERMISSION_SCHEMA,
        "authority": evidence_authority or authority,
        "source_id": source_id,
        "source_object_ids": source_object_ids or ["object-1"],
        "scope": evidence_scope or scope,
        "expires_at": evidence_expires_at or expires_at,
    }
    path.write_text(json.dumps(evidence), encoding="utf-8")
    return {
        "status": "authorized",
        "authority": authority,
        "evidence_path": "configs/pilot_3/permissions/museum.json",
        "evidence_sha256": hash_file(path),
        "scope": pointer_scope or scope,
        "expires_at": expires_at,
    }


def test_digital_reproduction_rights_accept_only_enumerated_license(tmp_path: Path) -> None:
    result = validate_digital_reproduction_authorization(
        tmp_path,
        _rights_row(),
        _rights_source(),
        evaluated_at="2026-09-01T00:00:00Z",
    )
    assert result == {
        "authorization_type": "enumerated_permissive_license",
        "evidence_path": None,
        "evidence_sha256": None,
        "expires_at": None,
        "license_id": "CC0",
        "status": "authorized",
    }

    for invalid in (
        "pending",
        "looks permissive to us",
        "CC-BY-NC-4.0",
        "CC_BY-NC-ND_4.0",
    ):
        with pytest.raises(ValueError, match="not an approved digital-reproduction"):
            validate_digital_reproduction_authorization(
                tmp_path,
                _rights_row(asset_license=invalid),
                _rights_source(),
                evaluated_at="2026-09-01T00:00:00Z",
            )


def test_file_backed_reproduction_permission_is_exactly_bound(tmp_path: Path) -> None:
    pointer = _permission_pointer(tmp_path)
    result = validate_digital_reproduction_authorization(
        tmp_path,
        _rights_row(
            asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
            asset_permission=pointer,
        ),
        _rights_source(),
        evaluated_at="2026-09-01T00:00:00Z",
    )
    assert result["authorization_type"] == "file_backed_permission"
    assert result["authority"] == "Museum Rights Authority"
    assert result["evidence_sha256"] == pointer["evidence_sha256"]
    assert result["scope"] == sorted(REQUIRED_REPRODUCTION_PERMISSION_SCOPE)


def test_file_backed_reproduction_permission_rejects_missing_or_stale_evidence(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="asset_permission must be a JSON object"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(asset_license=FILE_BACKED_PERMISSION_LICENSE_ID),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )

    pending = _permission_pointer(tmp_path)
    pending["status"] = "pending"
    with pytest.raises(ValueError, match="status must be authorized"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=pending,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )

    missing = {
        "status": "authorized",
        "authority": "Museum Rights Authority",
        "evidence_path": "configs/pilot_3/permissions/missing.json",
        "evidence_sha256": "0" * 64,
        "scope": sorted(REQUIRED_REPRODUCTION_PERMISSION_SCOPE),
        "expires_at": "2027-01-01T00:00:00Z",
    }
    with pytest.raises(FileNotFoundError):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=missing,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )

    pointer = _permission_pointer(tmp_path)
    pointer["evidence_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="evidence hash mismatch"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=pointer,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )


def test_file_backed_reproduction_permission_rejects_expired_scope_and_authority(
    tmp_path: Path,
) -> None:
    expired = _permission_pointer(
        tmp_path,
        expires_at="2026-08-31T23:59:59Z",
    )
    with pytest.raises(ValueError, match="permission is expired"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=expired,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )

    incomplete_scope = sorted(REQUIRED_REPRODUCTION_PERMISSION_SCOPE - {"statistical_analysis"})
    scope_pointer = _permission_pointer(
        tmp_path,
        evidence_scope=incomplete_scope,
        pointer_scope=incomplete_scope,
    )
    with pytest.raises(ValueError, match="lacks required operations: statistical_analysis"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=scope_pointer,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )

    authority_pointer = _permission_pointer(
        tmp_path,
        authority="Different Authority",
    )
    with pytest.raises(ValueError, match="authority does not match"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=authority_pointer,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )


def test_file_backed_reproduction_permission_rejects_mismatched_asset(tmp_path: Path) -> None:
    pointer = _permission_pointer(tmp_path, source_object_ids=["other-object"])
    with pytest.raises(ValueError, match="does not cover this source object"):
        validate_digital_reproduction_authorization(
            tmp_path,
            _rights_row(
                asset_license=FILE_BACKED_PERMISSION_LICENSE_ID,
                asset_permission=pointer,
            ),
            _rights_source(),
            evaluated_at="2026-09-01T00:00:00Z",
        )


def test_build_is_deterministic_balanced_and_metadata_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture_root(tmp_path)
    original_open = Path.open

    def guarded_open(path: Path, *args: object, **kwargs: object):
        if path.suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp"}:
            raise AssertionError(f"Freeze A1 attempted artwork I/O: {path}")
        return original_open(path, *args, **kwargs)

    def reject_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError(f"Freeze A1 attempted network I/O: {args!r} {kwargs!r}")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", reject_socket)
    first = build_corpus_bundle(root)
    second = build_corpus_bundle(root)
    assert first == second

    rows = first["corpus_rows"]
    assert len(rows) == 77
    selected = [row for row in rows if row["selection_status"] == "selected"]
    not_selected = [row for row in rows if row["selection_status"] == "not_selected"]
    assert len(selected) == 52
    assert len(not_selected) == 25
    assert all(row["digital_reproduction_authorization"]["status"] == "authorized" for row in rows)
    assert all(row["partition"] is None for row in not_selected)
    assert all(
        row["replacement_partition_policy"]
        == (
            "development_unselected_candidates_are_not_automatic_substitutes; "
            "external_has_no_post_freeze_replacement_and_any_failed_block_retires_"
            "external_validation"
        )
        for row in not_selected
    )
    assert first["summary"]["selection"]["not_selected_work_count"] == 25
    assert (
        first["summary"]["selection"]["replacement_eligible_reserve_work_count"] == 0
    )
    assert first["holdout"]["not_selected_work_count"] == 25
    assert first["holdout"]["replacement_eligible_reserve_work_count"] == 0
    cell_counts = Counter((row["artist_id"], row["source_id"]) for row in selected)
    assert len(cell_counts) == 12
    assert {
        source_id: {
            count
            for (_, observed_source), count in cell_counts.items()
            if observed_source == source_id
        }
        for source_id in {"aic", "met", "museum_balanced"}
    } == {"aic": {5}, "met": {5}, "museum_balanced": {3}}
    assert Counter(row["partition"] for row in selected) == {
        "development_training": 32,
        "development_calibration": 8,
        "external_holdout": 12,
    }
    assert all(
        row["source_id"] in {"aic", "met"}
        for row in selected
        if row["partition"].startswith("development_")
    )
    assert all(
        row["source_id"] == "museum_balanced"
        for row in selected
        if row["partition"] == "external_holdout"
    )
    assert sum(row["prior_local_reproduction_path"] is not None for row in selected) == 0
    assert first["feasibility"]["freeze_readiness"]["freeze_a1_ready"] is True
    disposition = first["feasibility"]["candidate_universe_disposition"]
    assert disposition["fresh_authoritative_audit_scope"] == "four_selected_finalists_only"
    assert disposition["unselected_artist_feasibility_claim"] is False
    assert Counter(row["disposition"] for row in disposition["artists"]) == {
        "selected_finalist": 4,
        "not_advanced_to_fresh_audit": 5,
    }
    assert first["summary"]["checks"]["no_artwork_or_generated_bytes_opened"] is True


def test_manifest_rows_expose_acquisition_contract_and_are_self_hashed() -> None:
    bundle = build_corpus_bundle(REPOSITORY_ROOT)
    required = {
        "canonical_work_id",
        "artist_id",
        "artist_name",
        "source_id",
        "source_object_id",
        "source_url",
        "image_url",
        "native_width",
        "native_height",
        "delivery_width",
        "delivery_height",
        "public_domain_status",
        "digital_reproduction_authorization",
        "rights_basis",
        "selection_rank",
        "source_role",
        "partition",
        "source_metadata_row_sha256",
        "selection_sha256",
        "row_sha256",
        "prior_local_reproduction_path",
        "prior_local_reproduction_sha256",
    }
    for row in bundle["corpus_rows"]:
        assert row["schema_version"] == CORPUS_ROW_SCHEMA
        assert required <= set(row)
        _verify_row_hash(row)
    for row in bundle["split_rows"]:
        assert row["schema_version"] == REAL_SPLIT_ROW_SCHEMA
        assert required | {"corpus_selection_row_sha256"} <= set(row)
        _verify_row_hash(row)


def test_write_and_verify_bundle_and_reject_tampering(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    summary = write_corpus_bundle(root)
    assert summary["status"] == "freeze_a1_complete"
    assert verify_corpus_bundle(root) == summary
    assert len(read_jsonl(root / DEFAULT_CORPUS_MANIFEST)) == 77
    assert len(read_jsonl(root / DEFAULT_REAL_SPLITS)) == 77
    assert read_json(root / DEFAULT_CORPUS_EVIDENCE)["freeze_a1_ready"] is True
    assert read_json(root / DEFAULT_HOLDOUT_SEAL)["external_source_id"] == "museum_balanced"
    assert read_json(root / DEFAULT_FEASIBILITY_EVIDENCE)["status"] == (
        "authoritative_metadata_audit_complete_freeze_a1_ready"
    )

    path = root / DEFAULT_REAL_SPLITS
    rows = read_jsonl(path)
    rows[0]["partition"] = "external_holdout"
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="real-splits"):
        verify_corpus_bundle(root)


def test_authoritative_input_hashes_fail_closed(tmp_path: Path) -> None:
    root = _fixture_root(tmp_path)
    candidate_path = root / "configs/pilot_3/metadata/authoritative_candidates.jsonl"
    candidate_path.write_text(candidate_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="candidate_manifest hash mismatch"):
        build_corpus_bundle(root)


def test_external_holdout_seal_contains_only_complete_selected_museum_blocks() -> None:
    bundle = build_corpus_bundle(REPOSITORY_ROOT)
    selected_external = [
        row
        for row in bundle["split_rows"]
        if row["selection_status"] == "selected" and row["source_id"] == "museum_balanced"
    ]
    seal = bundle["holdout"]
    assert seal["external_holdout_work_ids"] == [
        row["canonical_work_id"] for row in selected_external
    ]
    assert seal["external_holdout_selection_sha256s"] == [
        row["selection_sha256"] for row in selected_external
    ]
    assert seal["external_block_counts"] == {"dallas": 4, "minneapolis": 4, "toledo": 4}
    assert seal["external_exact_assignment_count"] == 13_824
    assert seal["artwork_bytes_opened"] is False
