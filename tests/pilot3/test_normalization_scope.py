from __future__ import annotations

import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Mapping

import pytest

from latent_art_bench.io import read_json, stable_hash, write_json
from latent_art_bench.pilot3.met_r2 import (
    DEFAULT_INCIDENT,
    DEFAULT_METADATA_FREEZE,
    DEFAULT_SPLITS,
    IMPLEMENTATION_PATHS,
    OFFICIAL_IMAGE_HOST,
    TransportResponse,
    capture_official_metadata,
    freeze_metadata_targets,
    write_offline_authorization,
)
from latent_art_bench.pilot3.normalization_scope import (
    DEFAULT_AUTHORIZATION,
    EXPECTED_GENERATED_COUNT,
    EXPECTED_GENERATED_MODEL,
    EXPECTED_LEGACY_AMENDMENT_SHA256,
    EXPECTED_MET_COUNT,
    EXPECTED_PREPROCESSING_IMPLEMENTATION_FILE_SHA256,
    LEGACY_AMENDMENT_PATH,
    MET_R2_IMPLEMENTATION_PATH,
    NAMESPACE,
    PHASE_A_CONFIG_PATH,
    PREPROCESSING_IMPLEMENTATION_PATH,
    SCHEDULE_MANIFEST_PATH,
    SCHEMA_VERSION,
    SCOPE_IMPLEMENTATION_PATH,
    SCOPE_TEST_PATH,
    Pilot3NormalizationScopeError,
    build,
    load,
    require_committed,
    verify,
    write,
)

REPOSITORY = Path(__file__).resolve().parents[2]


def _git(root: Path, *arguments: str) -> None:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def _commit_all(root: Path, message: str) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)


def _metadata_body(target: Mapping[str, Any]) -> bytes:
    value = {
        "objectID": int(str(target["object_id"])),
        "accessionNumber": target["accession_number"],
        "artistConstituentID": int(str(target["artist_constituent_id"])),
        "artistDisplayName": target["artist_name"],
        "isPublicDomain": True,
        "primaryImage": (
            f"https://{OFFICIAL_IMAGE_HOST}/CRDImages/ep/original/DP-{target['object_id']}.jpg"
        ),
        "primaryImageSmall": (
            f"https://{OFFICIAL_IMAGE_HOST}/CRDImages/ep/web-large/DP-{target['object_id']}.jpg"
        ),
        "additionalImages": [],
    }
    return json.dumps(value, sort_keys=True).encode("utf-8")


@pytest.fixture
def scope_root(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.name", "Pilot 3 Test")
    _git(tmp_path, "config", "user.email", "pilot3-test@example.invalid")
    prerequisites = {
        DEFAULT_INCIDENT,
        DEFAULT_SPLITS,
        LEGACY_AMENDMENT_PATH,
        PHASE_A_CONFIG_PATH,
        SCHEDULE_MANIFEST_PATH,
        PREPROCESSING_IMPLEMENTATION_PATH,
        MET_R2_IMPLEMENTATION_PATH,
        SCOPE_IMPLEMENTATION_PATH,
        SCOPE_TEST_PATH,
        *(Path(relative) for relative in IMPLEMENTATION_PATHS),
    }
    for relative in prerequisites:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY / relative, destination)
    _commit_all(tmp_path, "freeze implementation prerequisites")

    authorization = write_offline_authorization(tmp_path)
    _commit_all(tmp_path, "authorize R2 metadata capture")
    by_endpoint = {target["object_endpoint"]: target for target in authorization["targets"]}

    def request(url: str) -> TransportResponse:
        target = by_endpoint[url]
        return TransportResponse(
            status_code=200,
            body=_metadata_body(target),
            headers={"Content-Type": "application/json"},
            final_url=url,
        )

    capture_official_metadata(
        tmp_path,
        request,
    )
    freeze_metadata_targets(tmp_path)
    _commit_all(tmp_path, "freeze R2 metadata targets")
    return tmp_path


def _rehash(value: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(value)
    result.pop("authorization_sha256", None)
    result["authorization_sha256"] = stable_hash(result)
    return result


def test_build_enumerates_only_the_three_exact_extension_scopes(
    scope_root: Path,
) -> None:
    value = build(scope_root)

    assert value["schema_version"] == SCHEMA_VERSION
    assert value["namespace"] == NAMESPACE
    assert "authorized_at" not in value
    assert build(scope_root) == value
    assert value["legacy_aic_amendment_boundary"]["authorization_sha256"] == (
        EXPECTED_LEGACY_AMENDMENT_SHA256
    )
    assert value["legacy_aic_amendment_boundary"]["legacy_authority_modified_or_broadened"] is False
    assert value["legacy_aic_amendment_boundary"]["external_holdout_access_authorized"] is False

    membership = value["eligible_membership"]
    assert membership["extension_member_count"] == 352
    assert membership["met_r2"]["count"] == EXPECTED_MET_COUNT
    assert len(membership["met_r2"]["members"]) == EXPECTED_MET_COUNT
    assert all(
        member["primary_image_url"].startswith(f"https://{OFFICIAL_IMAGE_HOST}/")
        for member in membership["met_r2"]["members"]
    )
    assert membership["external_official_assets"]["count"] == 12
    assert len(membership["external_official_assets"]["members"]) == 12
    assert membership["generated_outputs"]["count"] == EXPECTED_GENERATED_COUNT
    assert len(membership["generated_outputs"]["members"]) == EXPECTED_GENERATED_COUNT
    assert {
        member["requested_model_label"] for member in membership["generated_outputs"]["members"]
    } == {EXPECTED_GENERATED_MODEL}
    assert value["explicit_exclusions"]["gpt-image-1_analytic_outputs"] is True
    assert value["authorization_boundary"]["generation_authorized"] is False
    implementation = value["normalization_implementation"]
    assert implementation["file_sha256"] == (EXPECTED_PREPROCESSING_IMPLEMENTATION_FILE_SHA256)
    assert (
        implementation["runtime_fingerprint"]
        == implementation["effective_preprocessing_contract"]["normalization_runtime"]
    )
    assert implementation["effective_preprocessing_contract_sha256"] == stable_hash(
        implementation["effective_preprocessing_contract"]
    )
    assert verify(scope_root, value) == value


def test_build_requires_the_committed_met_r2_metadata_freeze(
    scope_root: Path,
) -> None:
    _git(
        scope_root,
        "rm",
        "--cached",
        "--",
        DEFAULT_METADATA_FREEZE.as_posix(),
    )

    with pytest.raises(Pilot3NormalizationScopeError, match="committed and clean path"):
        build(scope_root)


def test_build_requires_its_implementation_and_other_prerequisites_committed(
    scope_root: Path,
) -> None:
    _git(
        scope_root,
        "rm",
        "--cached",
        "--",
        SCOPE_IMPLEMENTATION_PATH.as_posix(),
    )

    with pytest.raises(Pilot3NormalizationScopeError, match="committed and clean path"):
        build(scope_root)


def test_self_hashed_membership_substitutions_still_fail_reconstruction(
    scope_root: Path,
) -> None:
    value = build(scope_root)
    value["eligible_membership"]["met_r2"]["members"][0]["primary_image_url"] = (
        f"https://{OFFICIAL_IMAGE_HOST}/substitute.jpg"
    )
    value["eligible_membership"]["generated_outputs"]["members"][0]["request_id"] = (
        "substitute-request"
    )
    value = _rehash(value)

    with pytest.raises(Pilot3NormalizationScopeError, match="reconstruction"):
        verify(scope_root, value)


def test_canonical_preprocessing_implementation_drift_fails_closed(
    scope_root: Path,
) -> None:
    implementation = scope_root / PREPROCESSING_IMPLEMENTATION_PATH
    implementation.write_text(
        implementation.read_text(encoding="utf-8") + "\n# drift\n",
        encoding="utf-8",
    )
    _commit_all(scope_root, "commit preprocessing drift")

    with pytest.raises(Pilot3NormalizationScopeError, match="absent or changed"):
        build(scope_root)


def test_schedule_membership_cannot_admit_gpt_image_1(
    scope_root: Path,
) -> None:
    schedule = scope_root / SCHEDULE_MANIFEST_PATH
    schedule.write_text(
        schedule.read_text(encoding="utf-8").replace(
            '"requested_model_label":"gpt-image-2"',
            '"requested_model_label":"gpt-image-1"',
            1,
        ),
        encoding="utf-8",
    )
    _commit_all(scope_root, "commit ineligible schedule drift")

    with pytest.raises(Pilot3NormalizationScopeError, match="absent or changed"):
        build(scope_root)


def test_write_load_and_final_commit_gate(scope_root: Path) -> None:
    value = write(scope_root)
    assert read_json(scope_root / DEFAULT_AUTHORIZATION) == value
    assert load(scope_root) == value

    with pytest.raises(Pilot3NormalizationScopeError, match="committed and clean path"):
        require_committed(scope_root)
    _commit_all(scope_root, "commit normalization scope authority")
    assert require_committed(scope_root) == value


def test_write_never_replaces_a_different_existing_authority(
    scope_root: Path,
) -> None:
    value = write(scope_root)
    changed = deepcopy(value)
    changed["status"] = "changed"
    write_json(scope_root / DEFAULT_AUTHORIZATION, changed)

    with pytest.raises(Pilot3NormalizationScopeError, match="refusing to replace"):
        write(scope_root)
