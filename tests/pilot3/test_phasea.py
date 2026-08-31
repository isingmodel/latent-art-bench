from __future__ import annotations

import copy
import io
import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import pytest
from PIL import Image, ImageCms, PngImagePlugin

from latent_art_bench.features.learned_formal import learned_formal_vector_sha256
from latent_art_bench.io import (
    canonical_json,
    hash_bytes,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
)
from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig
from latent_art_bench.pilot3.phasea import (
    _EXTRACTION_RUNTIME_KEYS,
    EXPECTED_ARTISTS,
    EXPECTED_EXTERNAL_BLOCKS,
    EXTERNAL_SOURCE,
    NORMALIZATION_REVALIDATION_LEDGER_PATH,
    PREPROCESSING_AMENDMENT_DOC_PATH,
    PREPROCESSING_AMENDMENT_PATH,
    PREPROCESSING_HISTORICAL_BLOB_PATHS,
    PREPROCESSING_INCIDENT_PATH,
    PREPROCESSING_INCIDENT_SHA256,
    PREPROCESSING_INCIDENT_WORK_ID,
    PREPROCESSING_PROSPECTIVE_FORBIDDEN_PATHS,
    Pilot3PhaseAError,
    _acquire_real_partition_locked,
    _acquisition_phase_lock,
    _aic_development_splits,
    _append_jsonl_fsync,
    _browser_attempt_start,
    _browser_attempt_terminal,
    _closure_paths,
    _decode_and_normalize,
    _directory_stat_evidence,
    _download_image_bytes,
    _effective_preprocessing_contract_sha256,
    _external_transaction_lock,
    _file_bindings,
    _freeze_a1_closure_paths,
    _git_introduction_commit,
    _holm_checks,
    _http_attempt_start,
    _parse_where_froms_binary_plist,
    _permutation_p_values,
    _preprocessing_amendment_payload,
    _read_canonical_http_attempt_events,
    _read_canonical_normalization_revalidations,
    _read_completed_browser_file,
    _require_strict_git_ancestor,
    _selected_feature_rows,
    _self_hash,
    _single_runtime_environment,
    _validate_browser_attempt_terminal,
    _validated_determinism_probes,
    _verified_browser_attempt_histories,
    _verified_http_attempt_histories,
    _verify_acquisition_http_history,
    _verify_historical_aic_browser_recovery_authorization,
    _write_exclusive_json,
    authorize_preprocessing_determinism_amendment,
    create_normalization_revalidations,
    effective_acquisition_rows,
    evaluate_external_holdout,
    import_aic_browser_recovery_directory,
    load_phase_a_config,
    load_real_splits,
    prepare_aic_browser_recovery,
    require_development_freeze,
    run_determinism_probes,
    validate_real_splits,
    verify_a_vector_protocol,
    verify_external_holdout_result,
    verify_self_hash,
)
from latent_art_bench.pilot3.preprocessing import (
    PILOT3_NORMALIZATION_PROTOCOL_VERSION,
    pilot3_common_png_bytes,
    png_chunk_types,
)

ROOT = Path(__file__).resolve().parents[2]


class _FakeHTTPClient:
    outcomes: list[object] = []
    call_count = 0
    init_kwargs: list[dict[str, object]] = []

    def __init__(self, **kwargs: object) -> None:
        type(self).init_kwargs.append(kwargs)

    def __enter__(self) -> _FakeHTTPClient:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def stream(self, method: str, _url: str) -> object:
        assert method == "GET"
        type(self).call_count += 1
        outcome = type(self).outcomes.pop(0)

        class _Stream:
            def __enter__(self) -> object:
                if isinstance(outcome, BaseException):
                    raise outcome
                return outcome

            def __exit__(self, *_args: object) -> None:
                return None

        return _Stream()


class _ChunkedResponse:
    def __init__(self, chunks: list[bytes], *, content_length: int | None = None) -> None:
        headers = {"content-type": "image/jpeg", "etag": '"frozen"'}
        if content_length is not None:
            headers["content-length"] = str(content_length)
        self.headers = httpx.Headers(headers)
        self.status_code = 200
        self.url = httpx.URL("https://images.invalid/work-1.jpg")
        self.history: list[httpx.Response] = []
        self.chunks = chunks
        self.iterated = False

    def iter_bytes(self, *, chunk_size: int) -> Iterator[bytes]:
        assert chunk_size == 64 * 1024
        self.iterated = True
        yield from self.chunks


def _attempt_fixture(tmp_path: Path) -> tuple[dict, dict]:
    config = {
        "acquisition_http": {
            "max_response_bytes": 1024,
            "trust_env": False,
        },
        "paths": {
            "development_acquisition_intents": "intents.jsonl",
            "development_acquisition_attempts": "attempts.jsonl",
            "raw_dir": "raw",
        }
    }
    config_path = tmp_path / "configs/pilot_3/phase_a.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    intent = {
        "record_type": "pilot3_real_acquisition_intent",
        "schema_version": "1.0",
        "canonical_work_id": "work-1",
        "intent_id": "p3-real-intent-test",
        "acquisition_route": "network",
        "image_url": "https://images.invalid/work-1.jpg",
        "source_url": "https://museum.invalid/work-1",
    }
    _append_jsonl_fsync(tmp_path / "intents.jsonl", intent)
    return config, intent


def _browser_integration_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict, dict, dict, dict]:
    config = copy.deepcopy(load_phase_a_config(ROOT))
    config["paths"] = {
        **config["paths"],
        "development_acquisition_intents": "artifacts/intents.jsonl",
        "development_acquisition_attempts": "artifacts/http.jsonl",
        "development_acquisitions": "artifacts/acquisitions.jsonl",
        "raw_dir": "artifacts/raw",
        "normalized_dir": "artifacts/normalized",
    }
    canonical_config = tmp_path / "configs/pilot_3/phase_a.json"
    canonical_config.parent.mkdir(parents=True)
    canonical_config.write_text("{}\n", encoding="utf-8")
    split = {
        "canonical_work_id": "work-aic-test",
        "artist_id": "alfred_sisley",
        "asset_provider": "Art Institute of Chicago IIIF",
        "collection_block_id": "aic",
        "museum_accession": "test.1",
        "source_id": "aic",
        "source_object_id": "test",
        "partition": "development_training",
        "source_url": "https://www.artic.edu/artworks/test",
        "image_url": (
            "https://www.artic.edu/iiif/2/frozen/full/640,512/0/default.jpg"
        ),
        "delivery_width": 640,
        "delivery_height": 512,
    }
    authorization = {"authorization_sha256": "a" * 64}
    amendment = {
        "authorization_sha256": "b" * 64,
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "effective_preprocessing_contract_sha256": (
            _effective_preprocessing_contract_sha256(config)
        ),
    }
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._verify_historical_aic_browser_recovery_authorization",
        lambda *_args, **_kwargs: authorization,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_preprocessing_incident_resolution",
        lambda *_args, **_kwargs: {"amendment": amendment, "corrections": {}},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_incident",
        lambda *_args, **_kwargs: {"incident_sha256": "c" * 64},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config",
        lambda *_args, **_kwargs: config,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._aic_development_splits",
        lambda *_args, **_kwargs: [split],
    )
    return config, split, authorization, amendment


def _response(status: int, content: bytes, content_type: str) -> httpx.Response:
    request = httpx.Request("GET", "https://images.invalid/work-1.jpg")
    return httpx.Response(
        status,
        request=request,
        content=content,
        headers={"content-type": content_type, "etag": '"frozen"'},
    )


def _split_rows():
    names = {
        "alfred_sisley": "Alfred Sisley",
        "camille_pissarro": "Camille Pissarro",
        "paul_cezanne": "Paul Cezanne",
        "pierre_auguste_renoir": "Pierre-Auguste Renoir",
    }
    rows = []
    for artist in EXPECTED_ARTISTS:
        for source in ("aic", "met"):
            for rank in range(5):
                object_id = f"{artist}-{source}-{rank}"
                rows.append(
                    {
                        "canonical_work_id": f"work-{object_id}",
                        "artist_id": artist,
                        "artist_name": names[artist],
                        "asset_provider": f"{source}-provider",
                        "collection_block_id": source,
                        "museum_accession": object_id,
                        "source_id": source,
                        "source_object_id": object_id,
                        "source_url": f"https://museum.invalid/{object_id}",
                        "image_url": f"https://images.invalid/{object_id}.jpg",
                        "delivery_width": 1024,
                        "delivery_height": 768,
                        "partition": (
                            "development_training"
                            if rank < 4
                            else "development_calibration"
                        ),
                        "record_type": "pilot3_real_split_row",
                        "schema_version": "pilot3-real-split-row/1.0",
                        "selection_status": "selected",
                    }
                )
        for block in EXPECTED_EXTERNAL_BLOCKS:
            object_id = f"{artist}-{block}"
            rows.append(
                {
                    "canonical_work_id": f"work-{object_id}",
                    "artist_id": artist,
                    "artist_name": names[artist],
                    "asset_provider": f"{block}-provider",
                    "collection_block_id": block,
                    "museum_accession": object_id,
                    "source_id": EXTERNAL_SOURCE,
                    "source_object_id": object_id,
                    "source_url": f"https://museum.invalid/{object_id}",
                    "image_url": f"https://images.invalid/{object_id}.jpg",
                    "delivery_width": 1024,
                    "delivery_height": 768,
                    "partition": "external_holdout",
                    "record_type": "pilot3_real_split_row",
                    "schema_version": "pilot3-real-split-row/1.0",
                    "selection_status": "selected",
                }
            )
    for row in rows:
        row["row_sha256"] = stable_hash(row)
    return rows


def _png(width: int, height: int) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), (42, 84, 126)).save(output, format="PNG")
    return output.getvalue()


def test_phase_a_config_and_exact_split_contract() -> None:
    config = load_phase_a_config(ROOT)
    assert config["acquisition_http"]["max_response_bytes"] == 128 * 1024 * 1024
    assert config["acquisition_http"]["trust_env"] is False
    assert config["external_gate"]["permutation_assignment_count"] == 13_824
    assert "permutation_draws" not in config["external_gate"]
    assert "permutation_seed" not in config["external_gate"]
    rows = validate_real_splits(_split_rows(), config)
    assert len(rows) == 52
    assert sum(row["partition"] == "development_training" for row in rows) == 32
    assert sum(row["partition"] == "development_calibration" for row in rows) == 8
    assert sum(row["partition"] == "external_holdout" for row in rows) == 12


def test_canonical_external_split_binds_namespaced_roster_ids() -> None:
    config = load_phase_a_config(ROOT)
    rows = load_real_splits(ROOT, config)
    external = [row for row in rows if row["partition"] == "external_holdout"]
    roster = read_json(ROOT / "configs/pilot_3/external_museum_blocks.json")
    expected_ids = {
        f"{block['block_id']}:{work['museum_object_id']}"
        for block in roster["blocks"]
        for work in block["works"]
    }

    assert len(external) == 12
    assert {row["source_object_id"] for row in external} == expected_ids


def test_aic_browser_recovery_scope_is_only_exact_development_urls() -> None:
    config = load_phase_a_config(ROOT)
    rows = _aic_development_splits(ROOT, config)

    assert len(rows) == 20
    assert {row["source_id"] for row in rows} == {"aic"}
    assert {row["asset_provider"] for row in rows} == {
        "Art Institute of Chicago IIIF"
    }
    assert all(row["partition"].startswith("development_") for row in rows)
    assert all(
        row["image_url"].startswith("https://www.artic.edu/iiif/2/")
        and row["image_url"].endswith("/default.jpg")
        for row in rows
    )


def test_pilot3_v2_normalization_reproduces_exact_incident_difference_set() -> None:
    config = load_phase_a_config(ROOT)
    acquisitions = read_jsonl(
        ROOT / "artifacts/pilot_3/development_acquisitions.jsonl"
    )[:12]
    required_cas = [
        ROOT / acquisition[path_key]
        for acquisition in acquisitions
        for path_key in ("raw_path", "normalized_path")
    ]
    if not all(path.is_file() for path in required_cas):
        pytest.skip(
            "exact incident revalidation is an operational test requiring local ignored CAS"
        )
    splits = {
        row["canonical_work_id"]: row for row in load_real_splits(ROOT, config)
    }
    changed: list[str] = []
    for acquisition in acquisitions:
        split = splits[acquisition["canonical_work_id"]]
        raw = (ROOT / acquisition["raw_path"]).read_bytes()
        _decode, first = _decode_and_normalize(
            raw,
            config,
            expected_width=split["delivery_width"],
            expected_height=split["delivery_height"],
        )
        _decode, second = _decode_and_normalize(
            raw,
            config,
            expected_width=split["delivery_width"],
            expected_height=split["delivery_height"],
        )
        assert first == second
        assert png_chunk_types(first)[0] == "IHDR"
        assert png_chunk_types(first)[-1] == "IEND"
        with Image.open(io.BytesIO(first)) as effective, Image.open(
            ROOT / acquisition["normalized_path"]
        ) as historical:
            effective.load()
            historical.load()
            assert effective.info == {}
            assert effective.mode == historical.mode == "RGB"
            assert effective.size == historical.size
            assert effective.tobytes() == historical.tobytes()
        if hash_bytes(first) != acquisition["normalized_sha256"]:
            changed.append(acquisition["canonical_work_id"])
            assert hash_bytes(first) == (
                "45386bd86bbea9adfa200748ab795821f5a1ddc3ae1ebbc33b813b87723af2ee"
            )
            command = (
                "from pathlib import Path; "
                "from latent_art_bench.io import hash_bytes; "
                "from latent_art_bench.pilot3.phasea import "
                "_decode_and_normalize,load_phase_a_config; "
                f"r=Path({str(ROOT)!r}); c=load_phase_a_config(r); "
                f"p=(r/Path({str(acquisition['raw_path'])!r})).read_bytes(); "
                f"_,b=_decode_and_normalize(p,c,expected_width={split['delivery_width']},"
                f"expected_height={split['delivery_height']}); print(hash_bytes(b))"
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            fresh_hash = subprocess.run(
                [sys.executable, "-c", command],
                cwd=ROOT,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            assert fresh_hash == hash_bytes(first)
    assert changed == [PREPROCESSING_INCIDENT_WORK_ID]


def test_pilot3_v2_png_is_identical_in_a_fresh_process_with_icc_exif_alpha(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "synthetic-profiled.png"
    source = Image.new("RGBA", (37, 29), (17, 83, 149, 211))
    source.putpixel((3, 5), (250, 4, 99, 31))
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    exif = Image.Exif()
    exif[274] = 6
    text = PngImagePlugin.PngInfo()
    text.add_text("Creation Time", "changes-every-run")
    source.save(
        source_path,
        format="PNG",
        icc_profile=profile,
        exif=exif,
        pnginfo=text,
    )
    with Image.open(source_path) as image:
        local, _size = pilot3_common_png_bytes(
            image, Pilot2PreprocessingConfig()
        )
    command = (
        "from pathlib import Path; from PIL import Image; "
        "from latent_art_bench.io import hash_bytes; "
        "from latent_art_bench.pilot2.config import Pilot2PreprocessingConfig; "
        "from latent_art_bench.pilot3.preprocessing import pilot3_common_png_bytes; "
        f"p=Path({str(source_path)!r}); "
        "im=Image.open(p); b,_=pilot3_common_png_bytes(im,Pilot2PreprocessingConfig()); "
        "im.close(); print(hash_bytes(b))"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    fresh_hash = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert fresh_hash == hash_bytes(local)
    chunks = png_chunk_types(local)
    assert chunks[0] == "IHDR" and chunks[-1] == "IEND"
    assert set(chunks) == {"IHDR", "IDAT", "IEND"}
    with Image.open(io.BytesIO(local)) as verified:
        verified.load()
        assert verified.mode == "RGB"
        assert verified.info == {}


def test_normalization_revalidation_reader_rejects_torn_and_noncanonical_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "revalidations.jsonl"
    path.write_bytes(b'{"record_type":"test"}')
    with pytest.raises(Pilot3PhaseAError, match="torn final row"):
        _read_canonical_normalization_revalidations(path)
    path.write_bytes(b'{"record_type": "test"}\n')
    with pytest.raises(Pilot3PhaseAError, match="not canonical JSON"):
        _read_canonical_normalization_revalidations(path)


def test_preprocessing_evidence_commits_must_be_strictly_ordered(
    tmp_path: Path,
) -> None:
    with pytest.raises(Pilot3PhaseAError, match="strictly after"):
        _require_strict_git_ancestor(
            tmp_path,
            "a" * 40,
            "a" * 40,
            "normalization revalidation was not committed strictly after the amendment",
        )


def test_preprocessing_evidence_chronology_uses_real_git_commits(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repository, check=True)
    subprocess.run(
        ["git", "config", "user.email", "pilot3-test@example.invalid"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Pilot 3 Test"],
        cwd=repository,
        check=True,
    )

    commits = []
    for relative, content, message in (
        ("implementation.py", "v2 implementation\n", "implementation"),
        ("amendment.json", '{"authorized":true}\n', "amendment"),
        ("revalidations.jsonl", '{"sequence":1}\n', "revalidation"),
    ):
        path = repository / relative
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", relative], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "--quiet", "-m", message],
            cwd=repository,
            check=True,
        )
        commits.append(
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )

    implementation_commit, amendment_commit, revalidation_commit = commits
    assert _git_introduction_commit(repository, "amendment.json") == amendment_commit
    assert (
        _git_introduction_commit(repository, "revalidations.jsonl")
        == revalidation_commit
    )
    amendment_parent = subprocess.run(
        ["git", "rev-parse", f"{amendment_commit}^"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert amendment_parent == implementation_commit
    _require_strict_git_ancestor(
        repository,
        amendment_commit,
        revalidation_commit,
        "revalidation must follow amendment",
    )
    with pytest.raises(Pilot3PhaseAError, match="strictly later"):
        _require_strict_git_ancestor(
            repository,
            amendment_commit,
            amendment_commit,
            "correction must be committed strictly later",
        )


def test_preprocessing_amendment_rejects_changed_pilot2_serializer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    historical_sha = "a" * 64
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config",
        lambda *_args, **_kwargs: {
            "paths": {"split_manifest": "data/manifests/pilot_3/real_splits.jsonl"}
        },
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._aic_development_splits",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._git_blob_evidence",
        lambda _root, _commit, _relative: {
            "git_blob_object_id": "1" * 40,
            "file_sha256": historical_sha,
        },
    )

    def fake_hash(path: Path) -> str:
        if str(path).endswith("src/latent_art_bench/pilot2/preprocessing.py"):
            return "b" * 64
        return historical_sha

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.hash_file", fake_hash)
    assert "src/latent_art_bench/pilot2/preprocessing.py" in (
        PREPROCESSING_HISTORICAL_BLOB_PATHS
    )
    with pytest.raises(Pilot3PhaseAError, match="immutable base path"):
        _preprocessing_amendment_payload(
            tmp_path,
            original_authorization={
                "recovery_implementation_file_sha256": {},
                "phase_a_config_file_sha256": historical_sha,
                "split_manifest_file_sha256": historical_sha,
            },
            incident={"acquisition_bindings": []},
            remediation_implementation_git_commit="2" * 40,
        )


def test_amendment_authorizer_freeze_failure_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_incident",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            Pilot3PhaseAError("Freeze-A1 path is dirty")
        ),
    )
    with pytest.raises(Pilot3PhaseAError, match="dirty"):
        authorize_preprocessing_determinism_amendment(tmp_path)
    assert not (tmp_path / PREPROCESSING_AMENDMENT_PATH).exists()
    assert not (tmp_path / NORMALIZATION_REVALIDATION_LEDGER_PATH).exists()


def test_normalization_creator_freeze_failure_writes_no_cas_or_ledger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_amendment",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            Pilot3PhaseAError("Freeze-A1 path is dirty")
        ),
    )
    with pytest.raises(Pilot3PhaseAError, match="dirty"):
        create_normalization_revalidations(tmp_path)
    assert not (tmp_path / NORMALIZATION_REVALIDATION_LEDGER_PATH).exists()
    assert not (tmp_path / "artifacts/pilot_3/real_normalized").exists()


def test_normalization_revalidation_resumes_an_exact_partial_prefix_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    work_ids = [f"work-aic-{index}" for index in range(11)] + [
        PREPROCESSING_INCIDENT_WORK_ID
    ]
    config = {
        "common_preprocessing": {"protocol_version": "frozen-v1"},
        "paths": {"normalized_dir": "artifacts/pilot_3/real_normalized"},
    }
    base_sha = stable_hash(config["common_preprocessing"])
    originals = []
    splits = {}
    normalized_by_raw: dict[bytes, bytes] = {}
    for index, work_id in enumerate(work_ids):
        raw = f"raw-{index}".encode()
        effective = f"normalized-{index}".encode()
        historical = b"legacy-container" if work_id == PREPROCESSING_INCIDENT_WORK_ID else effective
        raw_path = tmp_path / "raw" / f"{index}.bin"
        old_path = tmp_path / "old" / f"{index}.png"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(raw)
        old_path.write_bytes(historical)
        originals.append(
            {
                "canonical_work_id": work_id,
                "record_sha256": f"{index + 1:064x}",
                "raw_path": raw_path.relative_to(tmp_path).as_posix(),
                "raw_sha256": hash_bytes(raw),
                "raw_byte_count": len(raw),
                "normalized_path": old_path.relative_to(tmp_path).as_posix(),
                "normalized_sha256": hash_bytes(historical),
                "normalized_byte_count": len(historical),
                "phase_a_config_file_sha256": "a" * 64,
                "common_preprocessing_config_sha256": base_sha,
            }
        )
        splits[work_id] = {
            "canonical_work_id": work_id,
            "delivery_width": 640,
            "delivery_height": 512,
        }
        normalized_by_raw[raw] = effective
    amendment = {
        "authorization_sha256": "b" * 64,
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
    }
    incident = {"incident_sha256": "c" * 64}
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_amendment",
        lambda *_args, **_kwargs: amendment,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_incident",
        lambda *_args, **_kwargs: incident,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config",
        lambda *_args, **_kwargs: config,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._incident_acquisition_rows",
        lambda *_args, **_kwargs: (originals, splits),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._decode_and_normalize",
        lambda payload, *_args, **_kwargs: ({}, normalized_by_raw[payload]),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._normalized_rgb_pixel_sha256",
        lambda _payload: "d" * 64,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.httpx.Client",
        lambda *_args, **_kwargs: pytest.fail("offline repair must not use HTTP"),
    )
    append_count = 0

    def crash_after_five(path: Path, row: dict) -> None:
        nonlocal append_count
        _append_jsonl_fsync(path, row)
        append_count += 1
        if append_count == 5:
            raise RuntimeError("simulated crash after durable append")

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._append_jsonl_fsync", crash_after_five
    )
    with pytest.raises(RuntimeError, match="simulated crash"):
        create_normalization_revalidations(tmp_path)
    assert len(
        _read_canonical_normalization_revalidations(
            tmp_path / NORMALIZATION_REVALIDATION_LEDGER_PATH
        )
    ) == 5
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._append_jsonl_fsync", _append_jsonl_fsync
    )
    rows = create_normalization_revalidations(tmp_path)
    assert len(rows) == 12
    assert sum(row["disposition"] == "revalidated_unchanged" for row in rows) == 11
    assert [
        row["canonical_work_id"]
        for row in rows
        if row["disposition"] == "superseded"
    ] == [PREPROCESSING_INCIDENT_WORK_ID]
    assert not any(
        (tmp_path / relative).exists()
        for relative in PREPROCESSING_PROSPECTIVE_FORBIDDEN_PATHS
    )


def test_historical_browser_authorization_requires_incident_commit_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authorization_path = (
        tmp_path / "reports/pilot_3/evidence/aic_browser_recovery_authorization.json"
    )
    authorization_path.parent.mkdir(parents=True)
    authorization_path.write_bytes(b"{}\n")
    calls = 0

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        nonlocal calls
        calls += 1
        return subprocess.CompletedProcess(
            args=[], returncode=0 if calls == 1 else 1, stdout=b"{}\n", stderr=b""
        )

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.subprocess.run", fake_run)
    with pytest.raises(Pilot3PhaseAError, match="exact historical Git blob"):
        _verify_historical_aic_browser_recovery_authorization(
            tmp_path,
            incident={
                "incident_sha256": PREPROCESSING_INCIDENT_SHA256,
                "original_browser_authorization": {"file_sha256": hash_bytes(b"{}\n")},
            },
            require_committed=True,
        )


def test_effective_acquisition_view_has_uniform_v2_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {"common_preprocessing": {"protocol_version": "frozen-v1"}}
    base_sha = stable_hash(config["common_preprocessing"])
    effective_sha = _effective_preprocessing_contract_sha256(config)
    amendment = {"authorization_sha256": "a" * 64}
    historical = {
        "canonical_work_id": "historical",
        "record_sha256": "1" * 64,
        "normalized_path": "old.png",
        "normalized_sha256": "2" * 64,
        "normalized_byte_count": 10,
        "common_preprocessing_config_sha256": base_sha,
    }
    correction = {
        "disposition": "superseded",
        "original_acquisition_record_sha256": historical["record_sha256"],
        "effective_normalized_path": "new.png",
        "effective_normalized_sha256": "3" * 64,
        "effective_normalized_byte_count": 9,
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "preprocessing_determinism_amendment_sha256": amendment[
            "authorization_sha256"
        ],
        "base_common_preprocessing_config_sha256": base_sha,
        "effective_preprocessing_contract_sha256": effective_sha,
        "effective_acquisition_sha256": "4" * 64,
        "record_sha256": "5" * 64,
    }
    current = {
        "canonical_work_id": "current",
        "record_sha256": "6" * 64,
        "normalized_path": "current.png",
        "normalized_sha256": "7" * 64,
        "normalized_byte_count": 8,
        "normalization_protocol_version": PILOT3_NORMALIZATION_PROTOCOL_VERSION,
        "preprocessing_determinism_amendment_sha256": amendment[
            "authorization_sha256"
        ],
        "base_common_preprocessing_config_sha256": base_sha,
        "common_preprocessing_config_sha256": effective_sha,
        "effective_preprocessing_contract_sha256": effective_sha,
    }
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_preprocessing_determinism_amendment",
        lambda *_args, **_kwargs: amendment,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_normalization_revalidations",
        lambda *_args, **_kwargs: {"historical": correction},
    )
    effective = effective_acquisition_rows(
        tmp_path,
        config,
        "development",
        {"historical": historical, "current": current},
    )
    assert effective["historical"]["normalized_path"] == "new.png"
    assert effective["current"]["normalized_path"] == "current.png"
    for row in effective.values():
        assert row["base_common_preprocessing_config_sha256"] == base_sha
        assert row["common_preprocessing_config_sha256"] == effective_sha
        assert row["effective_preprocessing_contract_sha256"] == effective_sha
        assert row["normalization_protocol_version"] == (
            PILOT3_NORMALIZATION_PROTOCOL_VERSION
        )


def test_determinism_probe_writer_round_trips_through_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sources = ("aic", "met")
    splits = []
    acquisitions: dict[str, dict] = {}
    effective: dict[str, dict] = {}
    features: dict[str, dict] = {}
    vector = np.asarray([1.25, -2.5, 5.0], dtype=np.float32)
    vector_sha = learned_formal_vector_sha256(vector)
    base_sha = "1" * 64
    effective_contract_sha = "2" * 64
    amendment_sha = "3" * 64
    for index, (artist, source) in enumerate(
        (artist, source) for artist in EXPECTED_ARTISTS for source in sources
    ):
        work_id = f"work-{index:02d}"
        split = {
            "canonical_work_id": work_id,
            "artist_id": artist,
            "source_id": source,
            "partition": "development_training",
        }
        splits.append(split)
        acquisitions[work_id] = {"canonical_work_id": work_id}
        effective[work_id] = {
            "canonical_work_id": work_id,
            "normalized_path": f"normalized/{work_id}.png",
            "normalized_sha256": f"{index + 10:064x}",
            "normalization_protocol_version": (
                PILOT3_NORMALIZATION_PROTOCOL_VERSION
            ),
            "base_common_preprocessing_config_sha256": base_sha,
            "common_preprocessing_config_sha256": effective_contract_sha,
            "preprocessing_determinism_amendment_sha256": amendment_sha,
            "effective_preprocessing_contract_sha256": effective_contract_sha,
            "effective_acquisition_sha256": f"{index + 100:064x}",
            "normalization_revalidation_record_sha256": f"{index + 200:064x}",
        }
        features[work_id] = {
            **split,
            "vector_sha256": vector_sha,
            "extraction_metadata": {"seed": 7000 + index},
        }
    config = {
        "paths": {
            "development_acquisitions": "ledgers/acquisitions.jsonl",
            "development_features": "ledgers/features.jsonl",
            "determinism_probes": "ledgers/determinism_probes.jsonl",
        },
        "a_vector": {"base_seed": 17, "device": "cpu"},
    }
    for row in acquisitions.values():
        _append_jsonl_fsync(
            tmp_path / config["paths"]["development_acquisitions"], row
        )
    for row in features.values():
        _append_jsonl_fsync(tmp_path / config["paths"]["development_features"], row)

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_preprocessing_incident_resolution",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config",
        lambda *_args, **_kwargs: config,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_real_splits",
        lambda *_args, **_kwargs: splits,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.effective_acquisition_rows",
        lambda *_args, **_kwargs: effective,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._verify_existing_acquisition",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._verify_feature",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._load_vae",
        lambda *_args, **_kwargs: object(),
    )

    class _Repeated:
        def __init__(self) -> None:
            self.vector = vector

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.extract_learned_formal",
        lambda *_args, **_kwargs: _Repeated(),
    )

    written = run_determinism_probes(tmp_path)
    validated = _validated_determinism_probes(
        tmp_path, config, list(features.values())
    )

    assert validated == written
    assert len(validated) == len(EXPECTED_ARTISTS) * len(sources)
    assert all(
        row["base_common_preprocessing_config_sha256"] == base_sha for row in written
    )
    assert all(
        row["common_preprocessing_config_sha256"] == effective_contract_sha
        for row in written
    )


@pytest.mark.parametrize("relative", PREPROCESSING_PROSPECTIVE_FORBIDDEN_PATHS)
def test_preprocessing_amendment_boundary_rejects_every_downstream_path(
    tmp_path: Path, relative: str
) -> None:
    from latent_art_bench.pilot3.phasea import (
        _require_preprocessing_amendment_prospective_boundary,
    )

    candidate = tmp_path / relative
    candidate.mkdir(parents=True)
    state = {
        "determinism_probe_path": "absent/determinism.jsonl",
        "development_feature_path": "absent/features.jsonl",
        "external_unseal_receipt_path": "absent/receipt.json",
        "p3_t07_path": "absent/protocol.json",
        "determinism_probes_exist": False,
        "development_features_exist": False,
        "external_unseal_receipt_exists": False,
        "external_acquisition_attempts_exist": False,
        "external_acquisition_intents_exist": False,
        "external_acquisitions_exist": False,
        "external_features_exist": False,
        "external_result_exists": False,
        "gpt_image_requests_made": False,
        "gpt_image_transport_opened": False,
        "p3_t07_exists": False,
    }
    with pytest.raises(Pilot3PhaseAError, match="no longer prospective"):
        _require_preprocessing_amendment_prospective_boundary(
            tmp_path, {"state_boundary": state}
        )


def test_post_incident_http_start_is_rejected_before_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    incident = tmp_path / PREPROCESSING_INCIDENT_PATH
    incident.parent.mkdir(parents=True)
    incident.write_text("{}\n", encoding="utf-8")
    _FakeHTTPClient.call_count = 0
    _FakeHTTPClient.outcomes = [_response(200, b"must-not-run", "image/jpeg")]
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    with pytest.raises(Pilot3PhaseAError, match="requires the committed v2 amendment"):
        _download_image_bytes(tmp_path, config, "development", intent)
    assert _FakeHTTPClient.call_count == 0
    assert (tmp_path / "attempts.jsonl").read_bytes() == b""


def test_generic_resume_cannot_create_a_remaining_aic_network_intent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    splits = [
        {
            "canonical_work_id": f"work-aic-{index}",
            "partition": "development_training",
            "source_id": "aic",
        }
        for index in range(40)
    ]
    config = {
        "paths": {
            "development_acquisition_intents": "intents.jsonl",
            "development_acquisition_attempts": "attempts.jsonl",
            "development_acquisitions": "acquisitions.jsonl",
        }
    }
    config_path = tmp_path / "configs/pilot_3/phase_a.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config",
        lambda *_args, **_kwargs: config,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_real_splits",
        lambda *_args, **_kwargs: splits,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_preprocessing_incident_resolution",
        lambda *_args, **_kwargs: {"amendment": {}, "corrections": {}},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.httpx.Client",
        lambda *_args, **_kwargs: pytest.fail("network request must not start"),
    )
    with pytest.raises(Pilot3PhaseAError, match="browser-recovery prepare"):
        _acquire_real_partition_locked(tmp_path, phase="development")
    assert not (tmp_path / "intents.jsonl").exists()
    assert (tmp_path / "attempts.jsonl").read_bytes() == b""


def test_where_froms_parser_requires_a_bounded_binary_url_array() -> None:
    url = "https://www.artic.edu/iiif/2/frozen/full/900,700/0/default.jpg"
    payload = plistlib.dumps([url, url], fmt=plistlib.FMT_BINARY, sort_keys=False)

    assert _parse_where_froms_binary_plist(payload) == [url, url]
    with pytest.raises(Pilot3PhaseAError, match="binary plist"):
        _parse_where_froms_binary_plist(
            plistlib.dumps([url], fmt=plistlib.FMT_XML, sort_keys=False)
        )
    with pytest.raises(Pilot3PhaseAError, match="URL array"):
        _parse_where_froms_binary_plist(
            plistlib.dumps({"url": url}, fmt=plistlib.FMT_BINARY, sort_keys=False)
        )


def test_browser_file_reads_xattr_and_jpeg_from_same_nofollow_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = load_phase_a_config(ROOT)
    buffer = io.BytesIO()
    Image.new("RGB", (640, 512), (20, 40, 60)).save(buffer, format="JPEG")
    source = tmp_path / "default.jpg"
    source.write_bytes(buffer.getvalue())
    exact_url = (
        "https://www.artic.edu/iiif/2/frozen/full/640,512/0/default.jpg"
    )
    raw_xattr = plistlib.dumps(
        [exact_url, exact_url], fmt=plistlib.FMT_BINARY, sort_keys=False
    )
    observed_descriptors: list[int] = []

    def fake_fgetxattr(descriptor: int, name: str) -> bytes:
        assert name == "com.apple.metadata:kMDItemWhereFroms"
        os.fstat(descriptor)
        observed_descriptors.append(descriptor)
        return raw_xattr

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._fgetxattr_bytes", fake_fgetxattr
    )
    payload, observed_xattr, urls, source_stat, decode, normalized = (
        _read_completed_browser_file(
            source,
            config,
            {
                "image_url": exact_url,
                "delivery_width": 640,
                "delivery_height": 512,
            },
        )
    )

    assert observed_descriptors
    assert payload == buffer.getvalue()
    assert observed_xattr == raw_xattr
    assert urls == [exact_url, exact_url]
    assert source_stat["size"] == len(payload)
    assert decode["decoded_format"] == "jpeg"
    assert decode["decoded_width"] == 640
    assert normalized.startswith(b"\x89PNG\r\n\x1a\n")

    link = tmp_path / "linked.jpg"
    link.symlink_to(source)
    with pytest.raises(Pilot3PhaseAError, match="non-symlink"):
        _read_completed_browser_file(
            link,
            config,
            {
                "image_url": exact_url,
                "delivery_width": 640,
                "delivery_height": 512,
            },
        )


def test_browser_attempt_terminal_binds_start_prefix_xattr_and_cas(
    tmp_path: Path,
) -> None:
    config = load_phase_a_config(ROOT)
    config["paths"] = {
        **config["paths"],
        "raw_dir": "raw",
        "normalized_dir": "normalized",
    }
    exact_url = (
        "https://www.artic.edu/iiif/2/frozen/full/640,512/0/default.jpg"
    )
    split = {
        "canonical_work_id": "work-aic-test",
        "artist_id": "alfred_sisley",
        "asset_provider": "Art Institute of Chicago IIIF",
        "source_id": "aic",
        "partition": "development_training",
        "source_url": "https://www.artic.edu/artworks/test",
        "image_url": exact_url,
        "delivery_width": 640,
        "delivery_height": 512,
    }
    intent = {
        "intent_id": "p3-real-intent-browser-test",
        "canonical_work_id": split["canonical_work_id"],
        "acquisition_route": "browser_recovery",
        "image_url": exact_url,
    }
    authorization = {"authorization_sha256": "a" * 64}
    download_directory = tmp_path / "download"
    download_directory.mkdir()
    directory_identity = {
        "authorization_sha256": authorization["authorization_sha256"],
        "canonical_work_id": split["canonical_work_id"],
        "download_directory_path": str(download_directory),
    }
    directory_intent = _self_hash(
        {
            "directory_intent_id": (
                f"p3-browser-dir-{stable_hash(directory_identity)[:24]}"
            ),
            **directory_identity,
        },
        "record_sha256",
    )
    start_wall_time_ns = time.time_ns()
    start = _browser_attempt_start(
        authorization=authorization,
        split=split,
        intent=intent,
        directory_intent=directory_intent,
        download_directory_stat=_directory_stat_evidence(download_directory.stat()),
        start_not_before_wall_time_ns=start_wall_time_ns,
        start_not_before_monotonic_ns=time.monotonic_ns(),
        event_sequence=1,
        previous_event_sha256=None,
        prior_events=[],
    )
    buffer = io.BytesIO()
    Image.new("RGB", (640, 512), (80, 100, 120)).save(buffer, format="JPEG")
    payload = buffer.getvalue()
    decode, normalized = _decode_and_normalize(
        payload, config, expected_width=640, expected_height=512
    )
    raw_sha = hash_bytes(payload)
    normalized_sha = hash_bytes(normalized)
    raw_path = tmp_path / "raw" / raw_sha[:2] / f"{raw_sha}.bin"
    normalized_path = (
        tmp_path / "normalized" / normalized_sha[:2] / f"{normalized_sha}.png"
    )
    raw_path.parent.mkdir(parents=True)
    normalized_path.parent.mkdir(parents=True)
    raw_path.write_bytes(payload)
    normalized_path.write_bytes(normalized)
    source = download_directory / "default.jpg"
    source.write_bytes(payload)
    raw_xattr = plistlib.dumps(
        [exact_url], fmt=plistlib.FMT_BINARY, sort_keys=False
    )
    opened = _directory_stat_evidence(source.stat())
    raw_quarantine = (
        f"0281;{start_wall_time_ns // 1_000_000_000:08x};;"
        "5A0245E5-C0F0-4870-AEE3-CF5F1D34B8CB"
    ).encode("ascii")
    terminal = _browser_attempt_terminal(
        start,
        source_file=source,
        source_file_stat=opened,
        raw_xattr=raw_xattr,
        where_froms_urls=[exact_url],
        raw_quarantine_xattr=raw_quarantine,
        quarantine_evidence={
            "flags_hex": "0281",
            "download_time_unix_seconds": start_wall_time_ns // 1_000_000_000,
            "agent": "",
            "uuid": "5a0245e5-c0f0-4870-aee3-cf5f1d34b8cb",
        },
        download_directory_stat_at_import=_directory_stat_evidence(
            download_directory.stat()
        ),
        payload=payload,
        raw_path=raw_path,
        decode=decode,
        normalized=normalized,
        normalized_path=normalized_path,
        root=tmp_path,
        prior_events=[start],
    )

    _validate_browser_attempt_terminal(tmp_path, config, start, terminal, [start])
    assert terminal["httpx_success_claimed"] is False
    assert terminal["expected_ledger_prefix_sha256"] == stable_hash([start])

    tampered = {
        **terminal,
        "quarantine_evidence": {
            **terminal["quarantine_evidence"],
            "download_time_unix_seconds": 0,
        },
    }
    tampered = _self_hash(tampered, "event_sha256")
    with pytest.raises(Pilot3PhaseAError, match="quarantine/freshness"):
        _validate_browser_attempt_terminal(
            tmp_path, config, start, tampered, [start]
        )


def test_browser_prepare_rejects_a_preexisting_download_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, split, _authorization, _amendment = _browser_integration_fixture(
        tmp_path, monkeypatch
    )
    download_directory = tmp_path / "downloads" / "attempt"
    download_directory.mkdir(parents=True)
    (download_directory / "preexisting.jpg").write_bytes(b"not a fresh download")

    with pytest.raises(Pilot3PhaseAError, match="must not already exist"):
        prepare_aic_browser_recovery(
            tmp_path, split["canonical_work_id"], download_directory
        )


def test_browser_prepare_freeze_failure_has_no_durable_side_effect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, split, _authorization, _amendment = _browser_integration_fixture(
        tmp_path, monkeypatch
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_development_freeze",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            Pilot3PhaseAError("Freeze-A1 path is dirty")
        ),
    )
    download_directory = tmp_path / "downloads" / "attempt"
    with pytest.raises(Pilot3PhaseAError, match="dirty"):
        prepare_aic_browser_recovery(
            tmp_path, split["canonical_work_id"], download_directory
        )
    assert not download_directory.exists()
    assert not (tmp_path / "artifacts/intents.jsonl").exists()
    assert not (
        tmp_path / "artifacts/pilot_3/development_browser_recoveries.jsonl"
    ).exists()
    assert not (
        tmp_path / "artifacts/pilot_3/development_browser_directory_intents.jsonl"
    ).exists()


def test_browser_prepare_rejects_an_already_acquired_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, split, _authorization, _amendment = _browser_integration_fixture(
        tmp_path, monkeypatch
    )
    acquisition_path = tmp_path / config["paths"]["development_acquisitions"]
    _append_jsonl_fsync(
        acquisition_path,
        {"canonical_work_id": split["canonical_work_id"], "record_sha256": "a" * 64},
    )
    download_directory = tmp_path / "downloads" / "attempt"
    with pytest.raises(Pilot3PhaseAError, match="already acquired"):
        prepare_aic_browser_recovery(
            tmp_path, split["canonical_work_id"], download_directory
        )
    assert not download_directory.exists()
    assert not (tmp_path / "artifacts/intents.jsonl").exists()


def test_browser_prepare_import_and_crash_resume_are_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, split, _authorization, _amendment = _browser_integration_fixture(
        tmp_path, monkeypatch
    )
    download_parent = tmp_path / "downloads"
    download_parent.mkdir()
    download_directory = download_parent / "attempt-1"
    start = prepare_aic_browser_recovery(
        tmp_path, split["canonical_work_id"], download_directory
    )
    assert download_directory.is_dir()
    assert list(download_directory.iterdir()) == []
    assert start["download_directory_path"] == str(download_directory)

    buffer = io.BytesIO()
    Image.new("RGB", (640, 512), (25, 50, 75)).save(buffer, format="JPEG")
    candidate = download_directory / "default.jpg"
    candidate.write_bytes(buffer.getvalue())
    where_froms = plistlib.dumps(
        [split["image_url"]], fmt=plistlib.FMT_BINARY, sort_keys=False
    )
    quarantine_seconds = max(
        int(time.time()), start["start_not_before_wall_time_ns"] // 1_000_000_000
    )
    quarantine = (
        f"0281;{quarantine_seconds:08x};;"
        "5A0245E5-C0F0-4870-AEE3-CF5F1D34B8CB"
    ).encode("ascii")

    def fake_fgetxattr(_descriptor: int, name: str) -> bytes:
        if name == "com.apple.metadata:kMDItemWhereFroms":
            return where_froms
        if name == "com.apple.quarantine":
            return quarantine
        raise AssertionError(name)

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._fgetxattr_bytes", fake_fgetxattr
    )
    materialized: list[str] = []

    def fake_materialize(
        _root: Path,
        _config: dict,
        row: dict,
        *_args: object,
        **_kwargs: object,
    ) -> dict:
        materialized.append(str(row["canonical_work_id"]))
        return {
            "canonical_work_id": row["canonical_work_id"],
            "record_sha256": "b" * 64,
        }

    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._materialize_real_acquisition",
        fake_materialize,
    )
    first = import_aic_browser_recovery_directory(tmp_path, download_directory)
    assert first[0]["canonical_work_id"] == split["canonical_work_id"]
    ledger = tmp_path / "artifacts/pilot_3/development_browser_recoveries.jsonl"
    assert [row["event_type"] for row in read_jsonl(ledger)] == ["start", "terminal"]

    # Simulate a crash after terminal persistence but before durable acquisition materialization:
    # re-importing the unchanged bound file must not append another terminal.
    second = import_aic_browser_recovery_directory(tmp_path, download_directory)
    assert second == first
    assert len(read_jsonl(ledger)) == 2
    assert materialized == [split["canonical_work_id"], split["canonical_work_id"]]
    assert config["paths"]["development_acquisition_attempts"] == "artifacts/http.jsonl"


def test_browser_journal_rejects_two_unmatched_starts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, split, authorization, amendment = _browser_integration_fixture(
        tmp_path, monkeypatch
    )
    download_parent = tmp_path / "downloads"
    download_parent.mkdir()
    download_directory = download_parent / "attempt-1"
    first = prepare_aic_browser_recovery(
        tmp_path, split["canonical_work_id"], download_directory
    )
    ledger = tmp_path / "artifacts/pilot_3/development_browser_recoveries.jsonl"
    forged = {
        **first,
        "event_sequence": 2,
        "previous_event_sha256": first["event_sha256"],
        "expected_ledger_prefix_sha256": stable_hash([first]),
    }
    forged = _self_hash(forged, "event_sha256")
    _append_jsonl_fsync(ledger, forged)
    intents = {
        row["intent_id"]: row
        for row in read_jsonl(tmp_path / "artifacts/intents.jsonl")
    }
    with pytest.raises(Pilot3PhaseAError, match="multiple unmatched starts"):
        _verified_browser_attempt_histories(
            tmp_path,
            config,
            authorization,
            intents,
            normalization_amendment=amendment,
        )


def test_p3_t07_closure_requires_all_browser_recovery_evidence(
    tmp_path: Path,
) -> None:
    config = load_phase_a_config(ROOT)
    closure = set(_closure_paths(config))
    required = {
        "reports/pilot_3/evidence/aic_browser_recovery_authorization.json",
        "artifacts/pilot_3/development_browser_directory_intents.jsonl",
        "artifacts/pilot_3/development_browser_recoveries.jsonl",
        "docs/PILOT_3_AIC_BROWSER_RECOVERY.md",
        "scripts/import_pilot3_browser_acquisition.py",
        str(PREPROCESSING_INCIDENT_PATH),
        str(PREPROCESSING_AMENDMENT_PATH),
        str(NORMALIZATION_REVALIDATION_LEDGER_PATH),
        str(PREPROCESSING_AMENDMENT_DOC_PATH),
        "src/latent_art_bench/pilot3/preprocessing.py",
    }
    assert required.issubset(closure)
    with pytest.raises(Pilot3PhaseAError, match="closure path is missing"):
        _file_bindings(tmp_path, required)


def test_p3_t07_feature_selection_reverifies_acquisition_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    split = {
        "canonical_work_id": "work-aic-test",
        "partition": "development_training",
    }
    acquisition = {"canonical_work_id": "work-aic-test"}
    feature = {"canonical_work_id": "work-aic-test"}
    calls: list[str] = []
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_real_splits",
        lambda *_args: [split],
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._combined_phase_rows",
        lambda _root, _config, kind, *_args: {
            "work-aic-test": feature if kind == "features" else acquisition
        },
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._verify_existing_acquisition",
        lambda *_args, **_kwargs: calls.append("acquisition"),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._verify_feature",
        lambda *_args, **_kwargs: calls.append("feature"),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.effective_acquisition_rows",
        lambda *_args, **_kwargs: {"work-aic-test": acquisition},
    )

    assert _selected_feature_rows(
        tmp_path, {"paths": {}}, {"development_training"}
    ) == [feature]
    assert calls == ["acquisition", "feature"]


def test_development_gate_requires_committed_freeze_a1_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closure = set(_freeze_a1_closure_paths())
    assert {
        "docs/PILOT_3_AIC_BROWSER_RECOVERY.md",
        "docs/PILOT_3_PROTOCOL.md",
        "configs/pilot_3/generation_authorization.json",
        "src/latent_art_bench/pilot3/analysis.py",
        "src/latent_art_bench/pilot3/design.py",
        "src/latent_art_bench/pilot3/feasibility.py",
        "src/latent_art_bench/pilot3/planning.py",
        "tests/pilot3/test_design.py",
        "tests/pilot3/test_feasibility.py",
        "tests/pilot3/test_planning.py",
        "scripts/import_pilot3_browser_acquisition.py",
        "configs/pilot_3/external_museum_blocks.json",
    }.issubset(closure)
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_planning_bundle", lambda *_args: {}
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_phase_b_freeze_bundle", lambda *_args: {}
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._git_path_committed_and_clean",
        lambda *_args: False,
    )
    with pytest.raises(Pilot3PhaseAError, match="not committed and clean"):
        require_development_freeze(ROOT)


def _write_self_hashed_closed_development_gate(root: Path) -> None:
    write_json(
        root / "reports/pilot_3/evidence/corpus_selection.json",
        _self_hash(
            {
                "record_type": "pilot3_corpus_selection",
                "status": "freeze_a1_complete",
            },
            field="semantic_sha256",
        ),
    )
    write_json(
        root / "reports/pilot_3/planning_index.json",
        _self_hash(
            {
                "record_type": "pilot3_planning_index",
                "generation_gate": "closed",
                "stale_but_self_hashed": True,
            },
            field="result_sha256",
        ),
    )


def test_development_gate_recomputes_planning_before_git_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_self_hashed_closed_development_gate(tmp_path)
    git_checks: list[str] = []
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_planning_bundle",
        lambda *_args: (_ for _ in ()).throw(
            RuntimeError("stale deterministic Pilot 3 planning artifact")
        ),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._git_path_committed_and_clean",
        lambda _root, relative: git_checks.append(relative) or True,
    )

    with pytest.raises(Pilot3PhaseAError, match="deterministic planning verification failed"):
        require_development_freeze(tmp_path)
    assert git_checks == []


def test_development_gate_recomputes_phase_b_before_git_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_self_hashed_closed_development_gate(tmp_path)
    git_checks: list[str] = []
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_planning_bundle", lambda *_args: {}
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_phase_b_freeze_bundle",
        lambda *_args: (_ for _ in ()).throw(
            ValueError("phase_b design does not recompute exactly")
        ),
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._git_path_committed_and_clean",
        lambda _root, relative: git_checks.append(relative) or True,
    )

    with pytest.raises(Pilot3PhaseAError, match="deterministic Phase-B verification failed"):
        require_development_freeze(tmp_path)
    assert git_checks == []


def test_freeze_a2_binds_immutable_development_ledgers_only() -> None:
    config = load_phase_a_config(ROOT)
    closure = set(_closure_paths(config))
    assert config["paths"]["development_acquisition_intents"] in closure
    assert config["paths"]["development_acquisition_attempts"] in closure
    assert config["paths"]["development_acquisitions"] in closure
    assert config["paths"]["development_features"] in closure
    assert config["paths"]["external_acquisition_intents"] not in closure
    assert config["paths"]["external_acquisition_attempts"] not in closure
    assert config["paths"]["external_acquisitions"] not in closure
    assert config["paths"]["external_features"] not in closure
    assert "docs/PILOT_3_PROTOCOL.md" in closure
    assert "configs/pilot_3/generation_authorization.json" not in closure


def test_split_contract_rejects_source_leakage() -> None:
    config = load_phase_a_config(ROOT)
    rows = _split_rows()
    rows[0]["partition"] = "external_holdout"
    rows[0].pop("row_sha256")
    rows[0]["row_sha256"] = stable_hash(rows[0])
    with pytest.raises(Pilot3PhaseAError, match=r"8\+2\+3"):
        validate_real_splits(rows, config)


def test_split_contract_requires_canonical_schema_and_self_hash() -> None:
    config = load_phase_a_config(ROOT)
    rows = _split_rows()
    rows[0].pop("row_sha256")
    with pytest.raises(Pilot3PhaseAError, match="hash is stale"):
        validate_real_splits(rows, config)


def test_phase_a_rejects_alternate_config_path(tmp_path: Path) -> None:
    canonical = tmp_path / "configs/pilot_3/phase_a.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_bytes((ROOT / "configs/pilot_3/phase_a.json").read_bytes())
    alternate = tmp_path / "alternate.json"
    alternate.write_bytes(canonical.read_bytes())
    with pytest.raises(Pilot3PhaseAError, match="canonical config"):
        load_phase_a_config(tmp_path, Path("alternate.json"))


@pytest.mark.parametrize(
    ("field", "value"),
    (("max_response_bytes", 0), ("trust_env", True)),
)
def test_phase_a_rejects_unfrozen_http_response_policy(
    tmp_path: Path, field: str, value: object
) -> None:
    config = read_json(ROOT / "configs/pilot_3/phase_a.json")
    config["acquisition_http"][field] = value
    write_json(tmp_path / "configs/pilot_3/phase_a.json", config)

    with pytest.raises(Pilot3PhaseAError, match="HTTP acquisition policy is not frozen"):
        load_phase_a_config(tmp_path)


def test_kim_intersection_is_strict_and_normalizes_losslessly() -> None:
    config = load_phase_a_config(ROOT)
    evidence, normalized = _decode_and_normalize(
        _png(411, 411), config, expected_width=411, expected_height=411
    )
    assert all(evidence["domain_checks"].values())
    with Image.open(io.BytesIO(normalized)) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (411, 411)
    with pytest.raises(Pilot3PhaseAError, match="outside the frozen Kim intersection"):
        _decode_and_normalize(_png(410, 411), config)
    with pytest.raises(Pilot3PhaseAError, match="outside the frozen Kim intersection"):
        _decode_and_normalize(
            _png(411, 412), config, expected_width=411, expected_height=411
        )


def test_split_contract_requires_positive_frozen_delivery_dimensions() -> None:
    config = load_phase_a_config(ROOT)
    rows = _split_rows()
    rows[0].pop("delivery_width")
    rows[0].pop("row_sha256")
    rows[0]["row_sha256"] = stable_hash(rows[0])
    with pytest.raises(Pilot3PhaseAError, match="lacks delivery_width"):
        validate_real_splits(rows, config)


def test_exact_runtime_fingerprint_must_match_every_feature() -> None:
    runtime = {key: f"frozen-{key}" for key in _EXTRACTION_RUNTIME_KEYS}
    rows = [
        {"canonical_work_id": "work-1", "extraction_metadata": dict(runtime)},
        {"canonical_work_id": "work-2", "extraction_metadata": dict(runtime)},
    ]
    assert _single_runtime_environment(rows) == runtime
    rows[1]["extraction_metadata"]["torch_version"] = "different"
    with pytest.raises(Pilot3PhaseAError, match="multiple extraction runtimes"):
        _single_runtime_environment(rows)


def test_external_unseal_receipt_is_create_once(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    _write_exclusive_json(path, {"receipt": "first"})
    with pytest.raises(FileExistsError):
        _write_exclusive_json(path, {"receipt": "second"})
    assert path.read_text(encoding="utf-8") == '{"receipt":"first"}\n'


def test_external_transaction_lock_rejects_concurrent_runner(tmp_path: Path) -> None:
    with _external_transaction_lock(tmp_path):
        with pytest.raises(Pilot3PhaseAError, match="already running"):
            with _external_transaction_lock(tmp_path):
                pytest.fail("a concurrent external transaction acquired the lock")


def test_acquisition_phase_lock_rejects_concurrent_runner(tmp_path: Path) -> None:
    with _acquisition_phase_lock(tmp_path, "development"):
        with pytest.raises(Pilot3PhaseAError, match="already running"):
            with _acquisition_phase_lock(tmp_path, "development"):
                pytest.fail("a concurrent development acquisition acquired the lock")


def test_http_attempt_ledger_records_failures_and_resumes_success_without_get(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    request = httpx.Request("GET", intent["image_url"])
    _FakeHTTPClient.outcomes = [
        _response(503, b"temporarily unavailable", "text/plain"),
        httpx.ConnectError("offline", request=request),
        _response(200, b"frozen-image-bytes", "image/jpeg"),
    ]
    _FakeHTTPClient.call_count = 0
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.time.sleep", lambda _value: None)

    payload, evidence, history = _download_image_bytes(
        tmp_path, config, "development", intent
    )
    assert payload == b"frozen-image-bytes"
    assert _FakeHTTPClient.call_count == 3
    assert [event["outcome"] for event in history[1::2]] == [
        "http_status_failure",
        "exception_failure",
        "success",
    ]
    assert evidence["technical_attempt_count"] == 3
    events = _read_canonical_http_attempt_events(tmp_path / "attempts.jsonl")
    assert [event["event_sequence"] for event in events] == list(range(1, 7))
    assert events[-1]["response_sha256"] == events[-1]["raw_path"].split("/")[-1][:-4]

    class _GetTrap:
        def __init__(self, **_kwargs: object) -> None:
            raise AssertionError("a completed success must never issue another GET")

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _GetTrap)
    resumed_payload, resumed_evidence, resumed_history = _download_image_bytes(
        tmp_path, config, "development", intent
    )
    assert resumed_payload == payload
    assert resumed_evidence == evidence
    assert resumed_history == history


def test_http_acquisition_ignores_ambient_proxy_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    _FakeHTTPClient.outcomes = [_response(200, b"frozen-image-bytes", "image/jpeg")]
    _FakeHTTPClient.call_count = 0
    _FakeHTTPClient.init_kwargs = []
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)

    _download_image_bytes(tmp_path, config, "development", intent)

    assert len(_FakeHTTPClient.init_kwargs) == 1
    assert _FakeHTTPClient.init_kwargs[0]["trust_env"] is False


def test_http_acquisition_rejects_oversized_content_length_without_read_or_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    config["acquisition_http"]["max_response_bytes"] = 8
    response = _ChunkedResponse([b"body-must-not-be-read"], content_length=9)
    _FakeHTTPClient.outcomes = [response]
    _FakeHTTPClient.call_count = 0
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)

    with pytest.raises(Pilot3PhaseAError, match="exceeds the frozen byte limit"):
        _download_image_bytes(tmp_path, config, "development", intent)

    terminal = _read_canonical_http_attempt_events(tmp_path / "attempts.jsonl")[-1]
    assert terminal["outcome"] == "response_too_large"
    assert terminal["retryable"] is False
    assert terminal["response_size_limit_source"] == "content_length"
    assert terminal["declared_content_length"] == 9
    assert terminal["response_byte_count"] == 0
    assert terminal["response_sha256"] == hash_bytes(b"")
    assert terminal["response_complete"] is False
    assert terminal["raw_path"] is None
    assert response.iterated is False
    assert not (tmp_path / "raw").exists()


def test_http_acquisition_rejects_streamed_oversize_without_partial_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    config["acquisition_http"]["max_response_bytes"] = 8
    response = _ChunkedResponse([b"1234", b"56789"])
    _FakeHTTPClient.outcomes = [response]
    _FakeHTTPClient.call_count = 0
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)

    with pytest.raises(Pilot3PhaseAError, match="exceeds the frozen byte limit"):
        _download_image_bytes(tmp_path, config, "development", intent)

    terminal = _read_canonical_http_attempt_events(tmp_path / "attempts.jsonl")[-1]
    assert terminal["outcome"] == "response_too_large"
    assert terminal["retryable"] is False
    assert terminal["response_size_limit_source"] == "streamed_bytes"
    assert terminal["declared_content_length"] is None
    assert terminal["response_byte_count"] == 9
    assert terminal["response_sha256"] == hash_bytes(b"123456789")
    assert terminal["response_complete"] is False
    assert terminal["raw_path"] is None
    assert response.iterated is True
    assert not (tmp_path / "raw").exists()


def test_http_attempt_ledger_fails_closed_on_indeterminate_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    start = _http_attempt_start(
        phase="development",
        intent=intent,
        attempt_number=1,
        event_sequence=1,
        previous_event_sha256=None,
        max_response_bytes=config["acquisition_http"]["max_response_bytes"],
    )
    _append_jsonl_fsync(tmp_path / "attempts.jsonl", start)

    class _GetTrap:
        def __init__(self, **_kwargs: object) -> None:
            raise AssertionError("an indeterminate GET must not be resent")

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _GetTrap)
    with pytest.raises(Pilot3PhaseAError, match="indeterminate start"):
        _download_image_bytes(tmp_path, config, "development", intent)


def test_http_attempt_ledger_fails_closed_after_nonretryable_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    _FakeHTTPClient.outcomes = [_response(404, b"not found", "text/plain")]
    _FakeHTTPClient.call_count = 0
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    with pytest.raises(Pilot3PhaseAError, match="HTTP 404"):
        _download_image_bytes(tmp_path, config, "development", intent)
    assert _FakeHTTPClient.call_count == 1

    class _GetTrap:
        def __init__(self, **_kwargs: object) -> None:
            raise AssertionError("a non-retryable failure must not be resent")

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _GetTrap)
    with pytest.raises(Pilot3PhaseAError, match="non-retryable"):
        _download_image_bytes(tmp_path, config, "development", intent)


def test_http_attempt_ledger_enforces_durable_retry_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    _FakeHTTPClient.outcomes = [
        _response(503, f"failure-{index}".encode(), "text/plain")
        for index in range(4)
    ]
    _FakeHTTPClient.call_count = 0
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.time.sleep", lambda _value: None)
    with pytest.raises(Pilot3PhaseAError, match="HTTP 503"):
        _download_image_bytes(tmp_path, config, "development", intent)
    assert _FakeHTTPClient.call_count == 4
    assert len(_read_canonical_http_attempt_events(tmp_path / "attempts.jsonl")) == 8

    class _GetTrap:
        def __init__(self, **_kwargs: object) -> None:
            raise AssertionError("an exhausted history must not be retried")

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _GetTrap)
    with pytest.raises(Pilot3PhaseAError, match="exhausted 4 recorded attempts"):
        _download_image_bytes(tmp_path, config, "development", intent)


def test_http_attempt_ledger_rejects_tampered_staged_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    _FakeHTTPClient.outcomes = [_response(200, b"frozen-image-bytes", "image/jpeg")]
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    _payload, _evidence, history = _download_image_bytes(
        tmp_path, config, "development", intent
    )
    (tmp_path / history[-1]["raw_path"]).write_bytes(b"tampered")

    class _GetTrap:
        def __init__(self, **_kwargs: object) -> None:
            raise AssertionError("stale staged bytes must not trigger a new GET")

    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _GetTrap)
    with pytest.raises(Pilot3PhaseAError, match="raw bytes are missing or stale"):
        _download_image_bytes(tmp_path, config, "development", intent)


def test_acquisition_record_must_bind_exact_http_attempt_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, intent = _attempt_fixture(tmp_path)
    _FakeHTTPClient.outcomes = [_response(200, b"frozen-image-bytes", "image/jpeg")]
    monkeypatch.setattr("latent_art_bench.pilot3.phasea.httpx.Client", _FakeHTTPClient)
    payload, evidence, history = _download_image_bytes(
        tmp_path, config, "development", intent
    )
    terminal = history[-1]
    row = {
        "canonical_work_id": intent["canonical_work_id"],
        "partition": "development_training",
        "intent_id": intent["intent_id"],
        "acquisition_route": "network",
        "acquisition_completion_route": "httpx_get",
        "raw_path": terminal["raw_path"],
        "raw_sha256": terminal["response_sha256"],
        "raw_byte_count": len(payload),
        "response_evidence": evidence,
        "http_attempt_ids": [history[0]["attempt_id"]],
        "http_attempt_count": 1,
        "http_attempt_event_count": 2,
        "http_attempt_history_semantic_sha256": stable_hash(history),
        "successful_http_attempt_id": terminal["attempt_id"],
        "successful_http_terminal_event_sha256": terminal["event_sha256"],
        "browser_attempt_id": None,
        "browser_terminal_event_sha256": None,
        "browser_authorization_sha256": None,
    }
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_preprocessing_incident_resolution",
        lambda *_args, **_kwargs: {"amendment": {}, "corrections": {}},
    )
    _verify_acquisition_http_history(row, tmp_path, config, intent)
    row["http_attempt_history_semantic_sha256"] = "0" * 64
    with pytest.raises(Pilot3PhaseAError, match="binding is stale"):
        _verify_acquisition_http_history(row, tmp_path, config, intent)


def test_http_attempt_ledger_rejects_local_route_and_torn_rows(tmp_path: Path) -> None:
    config, intent = _attempt_fixture(tmp_path)
    local_intent = {**intent, "acquisition_route": "prior_local_reproduction"}
    start = _http_attempt_start(
        phase="development",
        intent=local_intent,
        attempt_number=1,
        event_sequence=1,
        previous_event_sha256=None,
        max_response_bytes=config["acquisition_http"]["max_response_bytes"],
    )
    (tmp_path / "attempts.jsonl").write_text(
        canonical_json(start) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(Pilot3PhaseAError, match="network intent"):
        _verified_http_attempt_histories(
            tmp_path,
            config,
            "development",
            {str(local_intent["intent_id"]): local_intent},
        )
    (tmp_path / "attempts.jsonl").write_bytes(b'{"event_type":"start"}')
    with pytest.raises(Pilot3PhaseAError, match="torn final row"):
        _read_canonical_http_attempt_events(tmp_path / "attempts.jsonl")


def test_standalone_external_evaluation_cannot_start_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {"paths": {"external_result": "external.json"}}
    protocol = {"result_sha256": "a" * 64}
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config", lambda *_args: config
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_external_unseal",
        lambda *_args: protocol,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_external_unseal_receipt",
        lambda *_args: {"receipt_sha256": "b" * 64},
    )
    with pytest.raises(Pilot3PhaseAError, match="only inside"):
        evaluate_external_holdout(
            tmp_path, external_unseal_token=str(protocol["result_sha256"])
        )


def test_external_result_verifier_rejects_self_hashed_forged_statistics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = {"paths": {"external_result": "external.json"}}
    token = "a" * 64
    observed = _self_hash(
        {"a_vector_protocol_result_sha256": token, "balanced_accuracy": 1.0}
    )
    write_json(tmp_path / "external.json", observed)
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config", lambda *_args: config
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_external_unseal",
        lambda *_args: {"result_sha256": token},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.verify_external_unseal_receipt",
        lambda *_args: {"receipt_sha256": "b" * 64},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._external_holdout_result_payload",
        lambda *_args: {
            "a_vector_protocol_result_sha256": token,
            "balanced_accuracy": 0.25,
        },
    )
    with pytest.raises(Pilot3PhaseAError, match="deterministic recomputation"):
        verify_external_holdout_result(tmp_path, external_unseal_token=token)


def test_protocol_verifier_rejects_self_hashed_forged_statistics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    mean = np.asarray([1.0], dtype=np.float64)
    components = np.asarray([[1.0]], dtype=np.float64)
    centroids = np.asarray([[1.0]], dtype=np.float64)
    np.save(state_dir / "pca_mean.npy", mean, allow_pickle=False)
    np.save(state_dir / "pca_components.npy", components, allow_pickle=False)
    np.save(state_dir / "artist_centroids.npy", centroids, allow_pickle=False)
    config = {
        "paths": {
            "protocol_evidence": "protocol.json",
            "state_dir": "state",
        }
    }
    observed = _self_hash({"balanced_accuracy": 1.0})
    write_json(tmp_path / "protocol.json", observed)
    computed = {
        "pca": type("PCA", (), {"mean": mean, "components": components})(),
        "centroids": centroids,
    }
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.load_phase_a_config", lambda *_args: config
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._selected_feature_rows", lambda *_args: []
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._validated_determinism_probes",
        lambda *_args: [],
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._compute_development_state",
        lambda *_args: computed,
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea._a_vector_protocol_payload",
        lambda *_args: {"balanced_accuracy": 0.25},
    )
    monkeypatch.setattr(
        "latent_art_bench.pilot3.phasea.require_preprocessing_incident_resolution",
        lambda *_args, **_kwargs: {},
    )
    with pytest.raises(Pilot3PhaseAError, match="deterministic recomputation"):
        verify_a_vector_protocol(tmp_path)


def test_self_hash_detects_mutation() -> None:
    artifact = _self_hash({"schema_version": "test/1", "status": "pass"})
    assert verify_self_hash(artifact) == artifact["result_sha256"]
    artifact["status"] = "fail"
    with pytest.raises(Pilot3PhaseAError, match="stale"):
        verify_self_hash(artifact)


def test_holm_stepdown_requires_both_external_results() -> None:
    passing = _holm_checks({"classification": 0.01, "neighbor": 0.04})
    assert passing["all_rejected"] is True
    failing = _holm_checks({"classification": 0.03, "neighbor": 0.04})
    assert failing["all_rejected"] is False


def test_external_permutation_is_deterministic_and_detects_clear_geometry() -> None:
    label_order = list(EXPECTED_ARTISTS)
    neighbor_map = {
        "alfred_sisley": "pierre_auguste_renoir",
        "camille_pissarro": "paul_cezanne",
        "paul_cezanne": "camille_pissarro",
        "pierre_auguste_renoir": "alfred_sisley",
    }
    centroids = np.asarray([[0.0, 0.0], [0.0, 10.0], [10.0, 10.0], [10.0, 0.0]])
    scores = np.concatenate([centroids for _ in EXPECTED_EXTERNAL_BLOCKS], axis=0)
    labels = [label for _ in EXPECTED_EXTERNAL_BLOCKS for label in label_order]
    blocks = [
        block for block in EXPECTED_EXTERNAL_BLOCKS for _ in range(len(label_order))
    ]
    first = _permutation_p_values(
        scores,
        labels,
        blocks,
        centroids,
        label_order,
        neighbor_map,
    )
    second = _permutation_p_values(
        scores,
        labels,
        blocks,
        centroids,
        label_order,
        neighbor_map,
    )
    assert first == second
    assert first["assignment_count"] == 13_824
    assert first["assignment_space"] == "24^3"
    assert first["classification_exceedance_count"] == 1
    assert first["classification_p_value"] == 1 / 13_824
    assert first["classification_p_value"] == (
        first["classification_exceedance_count"] / first["assignment_count"]
    )
    assert first["neighbor_margin_p_value"] == (
        first["neighbor_margin_exceedance_count"] / first["assignment_count"]
    )
    broken_blocks = list(blocks)
    broken_blocks[0] = EXPECTED_EXTERNAL_BLOCKS[1]
    with pytest.raises(Pilot3PhaseAError, match="one-per-artist complete"):
        _permutation_p_values(
            scores,
            labels,
            broken_blocks,
            centroids,
            label_order,
            neighbor_map,
        )
