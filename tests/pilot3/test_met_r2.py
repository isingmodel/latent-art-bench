from __future__ import annotations

import io
import json
import shutil
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Mapping

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import read_json, read_jsonl, stable_hash, write_json, write_jsonl
from latent_art_bench.pilot3 import met_r2
from latent_art_bench.pilot3.cli import _met_r2_requester
from latent_art_bench.pilot3.met_r2 import (
    AUTHORIZATION_SCHEMA,
    DEFAULT_AUTHORIZATION,
    DEFAULT_IMAGE_ACQUISITIONS,
    DEFAULT_IMAGE_ATTEMPTS,
    DEFAULT_INCIDENT,
    DEFAULT_METADATA_ATTEMPTS,
    DEFAULT_METADATA_FREEZE,
    DEFAULT_SPLITS,
    DEFAULT_TARGET_MANIFEST,
    EXPECTED_OBJECT_IDS,
    IMPLEMENTATION_PATHS,
    NAMESPACE,
    OFFICIAL_IMAGE_HOST,
    Pilot3MetR2Error,
    TransportResponse,
    acquire_official_images,
    build_offline_authorization,
    capture_official_metadata,
    freeze_metadata_targets,
    require_committed_image_acquisitions,
    verify_authorization,
    verify_image_acquisitions,
    verify_incident,
    verify_metadata_freeze,
    verify_target_manifest,
    write_offline_authorization,
)

REPOSITORY = Path(__file__).resolve().parents[2]
def _committed(_root: Path, _relative: str) -> bool:
    return True


@pytest.fixture(autouse=True)
def committed_closure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(met_r2, "_git_path_committed_and_clean", _committed)
    monkeypatch.setattr(
        met_r2,
        "_require_committed_normalization_scope_for_images",
        lambda _root, _authorization, _targets, _freeze: {},
    )


@pytest.fixture
def r2_root(tmp_path: Path) -> Path:
    for relative in (DEFAULT_INCIDENT, DEFAULT_SPLITS, *map(Path, IMPLEMENTATION_PATHS)):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY / relative, destination)
    write_offline_authorization(tmp_path)
    return tmp_path


def _authorization(root: Path) -> Dict[str, Any]:
    value = read_json(root / DEFAULT_AUTHORIZATION)
    assert isinstance(value, dict)
    return value


def _metadata_body(target: Mapping[str, Any], **updates: Any) -> bytes:
    value: Dict[str, Any] = {
        "objectID": int(str(target["object_id"])),
        "accessionNumber": target["accession_number"],
        "artistConstituentID": int(str(target["artist_constituent_id"])),
        "artistDisplayName": target["artist_name"],
        "isPublicDomain": True,
        "primaryImage": (
            f"https://{OFFICIAL_IMAGE_HOST}/CRDImages/ep/original/"
            f"DP-{target['object_id']}.jpg"
        ),
        # These fields exist in the Met schema.  R2 proves that it never selects them.
        "primaryImageSmall": (
            f"https://{OFFICIAL_IMAGE_HOST}/CRDImages/ep/web-large/"
            f"DP-{target['object_id']}.jpg"
        ),
        "additionalImages": [
            f"https://{OFFICIAL_IMAGE_HOST}/CRDImages/ep/additional/"
            f"DP-{target['object_id']}.jpg"
        ],
    }
    value.update(updates)
    return json.dumps(value, sort_keys=True).encode("utf-8")


def _metadata_response(target: Mapping[str, Any], **updates: Any) -> TransportResponse:
    return TransportResponse(
        status_code=200,
        body=_metadata_body(target, **updates),
        headers={"Content-Type": "application/json; charset=utf-8"},
        final_url=str(target["object_endpoint"]),
    )


def _capture_and_freeze(root: Path) -> Dict[str, Any]:
    authorization = _authorization(root)
    by_endpoint = {target["object_endpoint"]: target for target in authorization["targets"]}

    def request(url: str) -> TransportResponse:
        events = read_jsonl(root / DEFAULT_METADATA_ATTEMPTS)
        assert events[-1]["event_type"] == "metadata_request_start"
        assert events[-1]["request_url"] == url
        return _metadata_response(by_endpoint[url])

    terminals = capture_official_metadata(
        root,
        request,
    )
    assert len(terminals) == 20
    freeze = freeze_metadata_targets(root)
    assert verify_metadata_freeze(root) == freeze
    return freeze


def _jpeg(
    width: int = 500,
    height: int = 420,
    color: tuple[int, int, int] = (22, 44, 66),
) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), color).save(output, format="JPEG")
    return output.getvalue()


def _jpeg_for_url(url: str) -> bytes:
    digest = stable_hash(url)
    return _jpeg(
        color=(
            int(digest[0:2], 16),
            int(digest[2:4], 16),
            int(digest[4:6], 16),
        )
    )


def _png(width: int = 500, height: int = 420) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), (22, 44, 66)).save(output, format="PNG")
    return output.getvalue()


def _rehash(value: Dict[str, Any], field: str) -> Dict[str, Any]:
    result = deepcopy(value)
    result.pop(field, None)
    result[field] = stable_hash(result)
    return result


def test_cli_request_adapter_performs_one_get_and_preserves_first_response() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[tuple[str, Dict[str, str]]] = []

        def get(self, url: str, *, headers: Dict[str, str]) -> Any:
            self.calls.append((url, headers))
            return SimpleNamespace(
                status_code=200,
                content=b"first-response",
                headers={"Content-Type": "application/json"},
                url=httpx.URL(url),
                history=[],
            )

    client = FakeClient()
    request = _met_r2_requester(client, accept="application/json")  # type: ignore[arg-type]
    response = request("https://collectionapi.metmuseum.org/example")

    assert client.calls == [
        (
            "https://collectionapi.metmuseum.org/example",
            {"Accept": "application/json"},
        )
    ]
    assert response.body == b"first-response"
    assert response.final_url == "https://collectionapi.metmuseum.org/example"
    assert response.redirect_chain == ()


def test_offline_authorization_binds_exact_frozen_work_identities(r2_root: Path) -> None:
    authorization = build_offline_authorization(r2_root)

    assert authorization["schema_version"] == AUTHORIZATION_SCHEMA
    assert authorization["namespace"] == NAMESPACE
    assert tuple(row["object_id"] for row in authorization["targets"]) == EXPECTED_OBJECT_IDS
    assert len({row["r2_asset_id"] for row in authorization["targets"]}) == 20
    assert all(
        row["r2_asset_id"].startswith("met-r2-primaryimage-")
        for row in authorization["targets"]
    )
    assert all(
        row["object_endpoint"].endswith("/" + row["object_id"])
        and "/search" not in row["object_endpoint"]
        for row in authorization["targets"]
    )
    assert authorization["metadata_policy"]["selected_image_field"] == "primaryImage"
    assert authorization["metadata_policy"]["fallback_allowed"] is False
    assert verify_authorization(r2_root, authorization) == authorization


def test_self_hashed_policy_or_target_substitution_is_still_rejected(r2_root: Path) -> None:
    authorization = _authorization(r2_root)
    authorization["targets"][0]["object_id"] = "999999"
    authorization = _rehash(authorization, "authorization_sha256")

    with pytest.raises(Pilot3MetR2Error, match="deterministic reconstruction"):
        verify_authorization(r2_root, authorization)


def test_incident_must_be_the_exact_quarantining_incident(r2_root: Path) -> None:
    incident = read_json(r2_root / DEFAULT_INCIDENT)
    incident["authorization_effect"]["incident_authorizes_metadata_access"] = True
    incident = _rehash(incident, "incident_sha256")
    write_json(r2_root / DEFAULT_INCIDENT, incident)

    with pytest.raises(Pilot3MetR2Error, match="exact committed Met provider incident"):
        verify_incident(r2_root)


def test_metadata_transport_stays_closed_when_implementation_binding_is_stale(
    r2_root: Path,
) -> None:
    doc = r2_root / IMPLEMENTATION_PATHS[1]
    doc.write_text(doc.read_text(encoding="utf-8") + "\nstale\n", encoding="utf-8")
    calls = []

    def request(url: str) -> TransportResponse:
        calls.append(url)
        raise AssertionError("stale implementation must not open transport")

    with pytest.raises(Pilot3MetR2Error, match="deterministic reconstruction"):
        capture_official_metadata(
            r2_root,
            request,
        )

    assert calls == []
    assert not (r2_root / DEFAULT_METADATA_ATTEMPTS).exists()


def test_metadata_starts_are_durable_and_only_primaryimage_is_frozen(r2_root: Path) -> None:
    _capture_and_freeze(r2_root)
    authorization = _authorization(r2_root)
    targets = verify_target_manifest(r2_root, authorization)

    assert len(read_jsonl(r2_root / DEFAULT_METADATA_ATTEMPTS)) == 40
    assert len(targets) == 20
    assert not (r2_root / DEFAULT_IMAGE_ATTEMPTS).exists()
    assert all(row["selected_image_field"] == "primaryImage" for row in targets)
    assert all("primaryImageSmall" not in row and "additionalImages" not in row for row in targets)
    assert all(row["image_dimensions_at_freeze"] is None for row in targets)
    assert all(
        row["primary_image_url"].startswith("https://images.metmuseum.org/")
        for row in targets
    )


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"objectID": 999999}, "objectID mismatch"),
        ({"accessionNumber": "wrong"}, "accession mismatch"),
        ({"artistConstituentID": 999999}, "artist authority mismatch"),
        ({"isPublicDomain": False}, "isPublicDomain is not true"),
        (
            {
                "primaryImage": "",
                "primaryImageSmall": (
                    "https://images.metmuseum.org/CRDImages/ep/web-large/valid.jpg"
                ),
            },
            "primaryImage must be a non-blank URL",
        ),
        (
            {
                "primaryImage": (
                    "https://upload.wikimedia.org/wikipedia/commons/not-official.jpg"
                )
            },
            "not an exact official images.metmuseum.org",
        ),
    ],
)
def test_metadata_identity_rights_and_no_fallback_fail_closed(
    r2_root: Path, updates: Dict[str, Any], message: str
) -> None:
    target = _authorization(r2_root)["targets"][0]

    with pytest.raises(Pilot3MetR2Error, match=message):
        capture_official_metadata(
            r2_root,
            lambda _url: _metadata_response(target, **updates),
        )

    events = read_jsonl(r2_root / DEFAULT_METADATA_ATTEMPTS)
    assert [event["event_type"] for event in events] == [
        "metadata_request_start",
        "metadata_request_terminal",
    ]
    assert events[-1]["outcome"] == "protocol_rejected"
    assert not (r2_root / DEFAULT_TARGET_MANIFEST).exists()


def test_metadata_redirect_or_search_final_url_is_never_accepted(r2_root: Path) -> None:
    target = _authorization(r2_root)["targets"][0]
    response = TransportResponse(
        status_code=200,
        body=_metadata_body(target),
        headers={"content-type": "application/json"},
        final_url="https://collectionapi.metmuseum.org/public/collection/v1/search?q=art",
        redirect_chain=(str(target["object_endpoint"]),),
    )

    with pytest.raises(Pilot3MetR2Error, match="final URL changed"):
        capture_official_metadata(
            r2_root,
            lambda _url: response,
        )


def test_metadata_failure_prevents_partial_manifest_eligibility(r2_root: Path) -> None:
    authorization = _authorization(r2_root)
    calls = 0

    def request(_url: str) -> TransportResponse:
        nonlocal calls
        target = authorization["targets"][calls]
        calls += 1
        if calls == 2:
            return _metadata_response(target, isPublicDomain=False)
        return _metadata_response(target)

    with pytest.raises(Pilot3MetR2Error, match="isPublicDomain"):
        capture_official_metadata(
            r2_root,
            request,
        )
    with pytest.raises(Pilot3MetR2Error, match="all twenty terminals"):
        freeze_metadata_targets(r2_root)
    assert calls == 2
    assert not (r2_root / DEFAULT_TARGET_MANIFEST).exists()
    assert not (r2_root / DEFAULT_METADATA_FREEZE).exists()


def test_duplicate_primary_image_url_closes_metadata_freeze(r2_root: Path) -> None:
    authorization = _authorization(r2_root)
    shared_url = json.loads(_metadata_body(authorization["targets"][0]))["primaryImage"]
    by_endpoint = {
        target["object_endpoint"]: target for target in authorization["targets"]
    }

    def request(url: str) -> TransportResponse:
        target = by_endpoint[url]
        updates = {"primaryImage": shared_url} if target is authorization["targets"][1] else {}
        return _metadata_response(target, **updates)

    capture_official_metadata(
        r2_root,
        request,
    )
    with pytest.raises(Pilot3MetR2Error, match="one primaryImage URL"):
        freeze_metadata_targets(r2_root)


def test_image_request_gate_runs_before_transport(
    r2_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture_and_freeze(r2_root)
    calls = []

    def request(url: str) -> TransportResponse:
        calls.append(url)
        raise AssertionError("transport must remain unopened")

    def dirty_manifest(_root: Path, relative: str) -> bool:
        return relative != str(DEFAULT_TARGET_MANIFEST)

    monkeypatch.setattr(met_r2, "_git_path_committed_and_clean", dirty_manifest)
    with pytest.raises(Pilot3MetR2Error, match="committed and clean"):
        acquire_official_images(
            r2_root,
            request,
        )
    assert calls == []
    assert not (r2_root / DEFAULT_IMAGE_ATTEMPTS).exists()


def test_normalization_scope_gate_runs_before_image_transport(
    r2_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture_and_freeze(r2_root)
    calls = []

    def closed_scope(*_args: Any) -> Dict[str, Any]:
        raise Pilot3MetR2Error("normalization scope is closed")

    monkeypatch.setattr(
        met_r2, "_require_committed_normalization_scope_for_images", closed_scope
    )
    with pytest.raises(Pilot3MetR2Error, match="normalization scope is closed"):
        acquire_official_images(r2_root, lambda url: calls.append(url))  # type: ignore[arg-type,return-value]
    assert calls == []
    assert not (r2_root / DEFAULT_IMAGE_ATTEMPTS).exists()


@pytest.mark.parametrize("phase", ["metadata", "image"])
def test_process_lock_prevents_duplicate_one_shot_runner(
    r2_root: Path, phase: str
) -> None:
    calls = []
    with met_r2._r2_phase_lock(r2_root, phase):
        with pytest.raises(Pilot3MetR2Error, match="already holds the one-shot lock"):
            if phase == "metadata":
                capture_official_metadata(
                    r2_root,
                    lambda url: calls.append(url),  # type: ignore[arg-type,return-value]
                )
            else:
                acquire_official_images(
                    r2_root,
                    lambda url: calls.append(url),  # type: ignore[arg-type,return-value]
                )
    assert calls == []


def test_image_first_responses_are_durable_and_admitted_only_as_all_20(
    r2_root: Path,
) -> None:
    freeze = _capture_and_freeze(r2_root)
    calls = []

    def request(url: str) -> TransportResponse:
        events = read_jsonl(r2_root / DEFAULT_IMAGE_ATTEMPTS)
        assert events[-1]["event_type"] == "image_request_start"
        assert events[-1]["request_url"] == url
        calls.append(url)
        return TransportResponse(
            status_code=200,
            body=_jpeg_for_url(url),
            headers={"content-type": "image/jpeg"},
            final_url=url,
        )

    rows = acquire_official_images(
        r2_root,
        request,
    )

    assert len(calls) == 20
    assert len(rows) == 20
    assert len(read_jsonl(r2_root / DEFAULT_IMAGE_ATTEMPTS)) == 40
    assert len({row["cohort_observation_sha256"] for row in rows}) == 1
    assert all(
        row["cohort_eligibility"] == "eligible_only_as_complete_20_asset_cohort"
        and row["decoded_width"] == 500
        and row["decoded_height"] == 420
        and row["decoded_format"] == "JPEG"
        and row["metadata_freeze_sha256"] == freeze["freeze_sha256"]
        for row in rows
    )

    authorization = _authorization(r2_root)
    targets = verify_target_manifest(r2_root, authorization)
    verified = verify_image_acquisitions(r2_root, authorization, targets, freeze)
    assert verified == rows

    def no_second_request(_url: str) -> TransportResponse:
        raise AssertionError("a completed R2 cohort must not be requested again")

    assert acquire_official_images(
        r2_root,
        no_second_request,
    ) == rows

    committed = require_committed_image_acquisitions(
        r2_root,
    )
    assert committed[2]["freeze_sha256"] == freeze["freeze_sha256"]
    assert committed[3] == rows


def test_complete_image_cohort_must_be_committed_before_phasea_use(
    r2_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _capture_and_freeze(r2_root)
    acquire_official_images(
        r2_root,
        lambda url: TransportResponse(
            status_code=200,
            body=_jpeg_for_url(url),
            headers={"content-type": "image/jpeg"},
            final_url=url,
        ),
    )

    def uncommitted_acquisition(_root: Path, relative: str) -> bool:
        return relative != str(DEFAULT_IMAGE_ACQUISITIONS)

    monkeypatch.setattr(
        met_r2, "_git_path_committed_and_clean", uncommitted_acquisition
    )
    with pytest.raises(Pilot3MetR2Error, match="committed and clean"):
        require_committed_image_acquisitions(
            r2_root,
        )


def test_duplicate_image_bytes_close_atomic_cohort(r2_root: Path) -> None:
    _capture_and_freeze(r2_root)
    payload = _jpeg()

    with pytest.raises(Pilot3MetR2Error, match="duplicate bytes"):
        acquire_official_images(
            r2_root,
            lambda url: TransportResponse(
                status_code=200,
                body=payload,
                headers={"content-type": "image/jpeg"},
                final_url=url,
            ),
        )

    assert len(read_jsonl(r2_root / DEFAULT_IMAGE_ATTEMPTS)) == 40
    assert not (r2_root / DEFAULT_IMAGE_ACQUISITIONS).exists()


def test_image_cas_or_acquisition_manifest_tampering_is_rejected(
    r2_root: Path,
) -> None:
    freeze = _capture_and_freeze(r2_root)
    rows = acquire_official_images(
        r2_root,
        lambda url: TransportResponse(
            status_code=200,
            body=_jpeg_for_url(url),
            headers={"content-type": "image/jpeg"},
            final_url=url,
        ),
    )
    authorization = _authorization(r2_root)
    targets = verify_target_manifest(r2_root, authorization)

    manifest = read_jsonl(r2_root / DEFAULT_IMAGE_ACQUISITIONS)
    manifest[0]["decoded_width"] = 999
    manifest[0] = _rehash(manifest[0], "record_sha256")
    write_jsonl(r2_root / DEFAULT_IMAGE_ACQUISITIONS, manifest)
    with pytest.raises(Pilot3MetR2Error, match="manifest is stale"):
        verify_image_acquisitions(r2_root, authorization, targets, freeze)

    write_jsonl(r2_root / DEFAULT_IMAGE_ACQUISITIONS, rows)
    raw_path = r2_root / rows[0]["raw_image_path"]
    raw_path.write_bytes(b"tampered")
    with pytest.raises(Pilot3MetR2Error, match="CAS hash or byte count changed"):
        verify_image_acquisitions(r2_root, authorization, targets, freeze)


@pytest.mark.parametrize(
    ("response_factory", "message"),
    [
        (
            lambda url: TransportResponse(
                status_code=200,
                body=_jpeg(),
                headers={"content-type": "image/jpeg"},
                final_url="https://upload.wikimedia.org/not-official.jpg",
                redirect_chain=(url,),
            ),
            "cross-provider image redirect",
        ),
        (
            lambda url: TransportResponse(
                status_code=200,
                body=_jpeg(),
                headers={"content-type": "image/jpeg"},
                final_url=url + "?redirected=1",
                redirect_chain=(url,),
            ),
            "final-URL change",
        ),
        (
            lambda url: TransportResponse(
                status_code=503,
                body=b"unavailable",
                headers={"content-type": "text/plain"},
                final_url=url,
            ),
            "HTTP 503",
        ),
        (
            lambda url: TransportResponse(
                status_code=200,
                body=_jpeg(),
                headers={"content-type": "image/png"},
                final_url=url,
            ),
            "content type is not JPEG",
        ),
        (
            lambda url: TransportResponse(
                status_code=200,
                body=_jpeg(410, 500),
                headers={"content-type": "image/jpeg"},
                final_url=url,
            ),
            "outside the unchanged Kim intersection",
        ),
        (
            lambda url: TransportResponse(
                status_code=200,
                body=_png(),
                headers={"content-type": "image/jpeg"},
                final_url=url,
            ),
            "outside the unchanged Kim intersection",
        ),
    ],
)
def test_image_redirect_derivative_failure_or_non_jpeg_closes_atomic_cohort(
    r2_root: Path,
    response_factory: Any,
    message: str,
) -> None:
    _capture_and_freeze(r2_root)

    with pytest.raises(Pilot3MetR2Error, match=message):
        acquire_official_images(
            r2_root,
            response_factory,
        )

    events = read_jsonl(r2_root / DEFAULT_IMAGE_ATTEMPTS)
    assert len(events) == 2
    assert events[-1]["outcome"] == "protocol_rejected"
    assert not (r2_root / DEFAULT_IMAGE_ACQUISITIONS).exists()


def test_self_hashed_manifest_row_cannot_change_selected_provider(r2_root: Path) -> None:
    _capture_and_freeze(r2_root)
    manifest = read_jsonl(r2_root / DEFAULT_TARGET_MANIFEST)
    manifest[0]["primary_image_url"] = (
        "https://upload.wikimedia.org/wikipedia/commons/substitution.jpg"
    )
    manifest[0] = _rehash(manifest[0], "row_sha256")
    write_jsonl(r2_root / DEFAULT_TARGET_MANIFEST, manifest)

    with pytest.raises(Pilot3MetR2Error, match="stale or was not deterministically built"):
        verify_target_manifest(r2_root, _authorization(r2_root))
