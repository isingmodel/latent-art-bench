from __future__ import annotations

import io
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import canonical_json, hash_bytes, read_json, stable_hash, write_json
from latent_art_bench.pilot3.phasea import (
    _EXTRACTION_RUNTIME_KEYS,
    EXPECTED_ARTISTS,
    EXPECTED_EXTERNAL_BLOCKS,
    EXTERNAL_SOURCE,
    Pilot3PhaseAError,
    _acquisition_phase_lock,
    _append_jsonl_fsync,
    _closure_paths,
    _decode_and_normalize,
    _download_image_bytes,
    _external_transaction_lock,
    _freeze_a1_closure_paths,
    _holm_checks,
    _http_attempt_start,
    _permutation_p_values,
    _read_canonical_http_attempt_events,
    _self_hash,
    _single_runtime_environment,
    _verified_http_attempt_histories,
    _verify_acquisition_http_history,
    _write_exclusive_json,
    evaluate_external_holdout,
    load_phase_a_config,
    load_real_splits,
    require_development_freeze,
    validate_real_splits,
    verify_a_vector_protocol,
    verify_external_holdout_result,
    verify_self_hash,
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


def test_development_gate_requires_committed_freeze_a1_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closure = set(_freeze_a1_closure_paths())
    assert {
        "docs/PILOT_3_PROTOCOL.md",
        "configs/pilot_3/generation_authorization.json",
        "src/latent_art_bench/pilot3/analysis.py",
        "src/latent_art_bench/pilot3/design.py",
        "src/latent_art_bench/pilot3/feasibility.py",
        "src/latent_art_bench/pilot3/planning.py",
        "tests/pilot3/test_design.py",
        "tests/pilot3/test_feasibility.py",
        "tests/pilot3/test_planning.py",
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
    }
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
