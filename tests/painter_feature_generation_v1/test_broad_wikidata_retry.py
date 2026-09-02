import json
from pathlib import Path

import httpx
import pytest
from test_broad_wikidata import _build_authorized_tree

from latent_art_bench.io import canonical_json, hash_file
from latent_art_bench.painter_feature_generation_v1 import broad_wikidata as broad
from latent_art_bench.painter_feature_generation_v1 import broad_wikidata_retry as retry
from latent_art_bench.painter_feature_generation_v1.broad_wikidata_retry import (
    RetryGateError,
    _paths_overlap,
    _validate_config_delta,
)


def _config(census: str, workspace: str) -> dict:
    return {
        "census_id": census,
        "source_contract": {"minimum_interval_seconds": 2.0},
        "paths": {
            "request_intents": f"data/{census}-intents.jsonl",
            "request_events": f"data/{census}-events.jsonl",
            "candidate_manifest": f"data/{census}-candidates.jsonl",
            "execution_receipt": f"data/{census}-receipt.json",
            "workspace": workspace,
        },
        "stable": "same",
    }


def test_paths_overlap_rejects_equal_and_nested_paths() -> None:
    assert _paths_overlap([Path("a"), Path("a")])
    assert _paths_overlap([Path("a"), Path("a/b")])
    assert not _paths_overlap([Path("a"), Path("b")])


def test_config_delta_accepts_only_declared_changes() -> None:
    previous = _config("r1", "workspace/r1")
    current = _config("r2", "workspace/r2")
    current["source_contract"]["minimum_interval_seconds"] = 5.0
    current["predecessor_terminal_census"] = {"bound": True}
    _validate_config_delta(previous, current)
    current["stable"] = "changed"
    with pytest.raises(RetryGateError, match="outside"):
        _validate_config_delta(previous, current)


def test_config_delta_rejects_current_internal_nesting() -> None:
    previous = _config("r1", "workspace/r1")
    current = _config("r2", "workspace/r2")
    current["paths"]["candidate_manifest"] = "workspace/r2/candidates.jsonl"
    current["source_contract"]["minimum_interval_seconds"] = 5.0
    current["predecessor_terminal_census"] = {"bound": True}
    with pytest.raises(RetryGateError, match="overlap"):
        _validate_config_delta(previous, current)


def test_gate_a_review_is_rejected_by_direct_base_execution(tmp_path: Path) -> None:
    config_path, seal_path, _ = _build_authorized_tree(tmp_path)
    review_path = tmp_path / "data/review.json"
    review = json.loads(review_path.read_text())
    review.update(
        {
            "decision": "APPROVE_BROAD_WIKIDATA_BASE_COLLECTION_ONLY",
            "review_gate": "A_BASE_COLLECTION",
            "retry_lineage_approved": False,
            "execution_authorized": False,
        }
    )
    review_path.write_text(canonical_json(review) + "\n")
    seal = json.loads(seal_path.read_text())
    seal["review_sha256"] = hash_file(review_path)
    seal_path.write_text(canonical_json(seal) + "\n")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    with pytest.raises(broad.BroadDiscoveryError, match="does not approve"):
        broad.execute(
            tmp_path,
            config_path,
            seal_path,
            hash_file(seal_path),
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    assert not (tmp_path / "data/events.jsonl").exists()


def _combined_config() -> dict:
    return {
        "census_id": "r2",
        "protocol_id": "protocol",
        "scope": retry._SCOPE,
        "paths": {"request_intents": "intents.jsonl"},
    }


def _combined_seal(retry_path: str, retry_sha: str) -> dict:
    return {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-authorization/1.0",
        "status": "authorized_for_broad_wikidata_metadata_execution",
        "census_id": "r2",
        "protocol_id": "protocol",
        "authorization_scope": retry._SCOPE,
        "freeze_path": "collection-freeze.json",
        "freeze_sha256": "freeze-sha",
        "review_path": "collection-review.json",
        "review_sha256": "review-sha",
        "retry_gate_authorization_path": retry_path,
        "retry_gate_authorization_sha256": retry_sha,
    }


def test_wrapper_rejects_retry_seal_tamper_before_executor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retry_seal = tmp_path / "retry-seal.json"
    retry_seal.write_text("{}\n")
    combined_path = tmp_path / "combined.json"
    combined_path.write_text("{}\n")
    calls = 0

    def reject(*args: object, **kwargs: object) -> dict:
        raise RetryGateError("retry authorization hash mismatch")

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    monkeypatch.setattr(retry, "validate_retry_authorization", reject)
    with pytest.raises(RetryGateError, match="hash mismatch"):
        retry._execute_authorized_retry(
            tmp_path,
            tmp_path / "config.json",
            combined_path,
            "combined-sha",
            retry_seal,
            "tampered",
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    assert not (tmp_path / "workspace").exists()


@pytest.mark.parametrize("use_symlink", [False, True])
def test_authorized_executor_rejects_outside_seal_before_workspace(
    tmp_path: Path, use_symlink: bool
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside-combined.json"
    outside.write_text("{}\n")
    combined = outside
    if use_symlink:
        combined = root / "escaping-link.json"
        combined.symlink_to(outside)
    retry_seal = root / "retry-seal.json"
    retry_seal.write_text("{}\n")
    with pytest.raises(RetryGateError, match="outside the repository"):
        retry._execute_authorized_retry(
            root,
            root / "config.json",
            combined,
            hash_file(outside),
            retry_seal,
            hash_file(retry_seal),
        )
    assert not (root / "workspace").exists()
    assert not (root / "data/events.jsonl").exists()


def test_wrapper_rejects_cross_combined_seal_before_executor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retry_seal = tmp_path / "retry-seal.json"
    retry_seal.write_text("{}\n")
    combined_path = tmp_path / "combined.json"
    combined = _combined_seal("retry-seal.json", "wrong-sha")
    combined_path.write_text(canonical_json(combined) + "\n")
    calls = 0

    monkeypatch.setattr(
        retry,
        "validate_retry_authorization",
        lambda *args, **kwargs: {
            "freeze": {
                "collection_freeze_path": "collection-freeze.json",
                "collection_freeze_sha256": "freeze-sha",
                "collection_review_path": "collection-review.json",
                    "collection_review_sha256": "review-sha",
                    "frozen_inputs": [
                        {"path": "config.json", "sha256": "config-sha"},
                        {"path": "intents.jsonl", "sha256": "intent-sha"}
                    ],
                }
            },
        )
    monkeypatch.setattr(
        retry,
        "_read_hashed_json",
        lambda path, expected, label: (
            combined
            if label == "combined collection seal"
            else _combined_config()
            if label == "retry config"
            else {}
        ),
    )
    monkeypatch.setattr(retry, "_read_hashed_jsonl", lambda *args: [])
    monkeypatch.setattr(retry.broad, "build_intents", lambda *args: [])

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    with pytest.raises(RetryGateError, match="combined"):
        retry._execute_authorized_retry(
            tmp_path,
            tmp_path / "config.json",
            combined_path,
            "combined-sha",
            retry_seal,
            "retry-sha",
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0


def test_execution_context_returns_explicit_capability_without_global_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    retry_seal = tmp_path / "retry-seal.json"
    retry_seal.write_text("{}\n")
    combined_path = tmp_path / "combined.json"
    combined = _combined_seal("retry-seal.json", "retry-sha")
    combined_path.write_text(canonical_json(combined) + "\n")
    (tmp_path / "collection-freeze.json").write_text("{}\n")
    (tmp_path / "collection-review.json").write_text("{}\n")
    original = broad.validate_authorization
    monkeypatch.setattr(
        retry,
        "validate_retry_authorization",
        lambda *args, **kwargs: {
            "freeze": {
                "collection_freeze_path": "collection-freeze.json",
                "collection_freeze_sha256": "freeze-sha",
                "collection_review_path": "collection-review.json",
                "collection_review_sha256": "review-sha",
                "frozen_inputs": [
                    {"path": "config.json", "sha256": "config-sha"},
                    {"path": "intents.jsonl", "sha256": "intent-sha"}
                ],
            }
        },
    )
    monkeypatch.setattr(
        retry,
        "_read_hashed_json",
        lambda path, expected, label: (
            combined
            if label == "combined collection seal"
            else _combined_config()
            if label == "retry config"
            else {}
        ),
    )
    monkeypatch.setattr(retry, "_read_hashed_jsonl", lambda *args: [])
    monkeypatch.setattr(retry.broad, "build_intents", lambda *args: [])

    result = retry._validated_execution_context(
        tmp_path,
        tmp_path / "config.json",
        combined_path,
        "combined-sha",
        retry_seal,
        "retry-sha",
    )
    assert result["seal"] == combined
    assert result["config"] == _combined_config()
    assert result["intents"] == []
    assert broad.validate_authorization is original


def test_executor_aborts_if_in_root_config_symlink_retargets_after_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reviewed = tmp_path / "reviewed.json"
    reviewed.write_text("{}\n")
    unreviewed = tmp_path / "unreviewed.json"
    unreviewed.write_text("{}\n")
    config_link = tmp_path / "config-link.json"
    config_link.symlink_to(reviewed)
    combined = tmp_path / "combined.json"
    combined.write_text("{}\n")
    retry_seal = tmp_path / "retry-seal.json"
    retry_seal.write_text("{}\n")
    calls = 0

    def validated(*args: object, **kwargs: object) -> dict:
        config_link.unlink()
        config_link.symlink_to(unreviewed)
        return {
            "seal": {"freeze_path": "freeze.json", "freeze_sha256": "f" * 64},
            "freeze": {},
            "review": {},
            "config": {"paths": {"workspace": "workspace"}},
            "intents": [],
            "request_intents_sha256": "i" * 64,
        }

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    monkeypatch.setattr(retry, "_validated_execution_context", validated)
    with pytest.raises(RetryGateError, match="changed after validation"):
        retry._execute_authorized_retry(
            tmp_path,
            config_link,
            combined,
            "c" * 64,
            retry_seal,
            "r" * 64,
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    assert not (tmp_path / "workspace").exists()
    assert not (tmp_path / "data/events.jsonl").exists()


def test_executor_aborts_on_same_path_config_replacement_after_gate_b(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(canonical_json(_combined_config()) + "\n")
    reviewed_sha = hash_file(config_path)
    combined = tmp_path / "combined.json"
    combined.write_text("{}\n")
    retry_seal = tmp_path / "retry-seal.json"
    retry_seal.write_text("{}\n")
    calls = 0

    def validated(*args: object, **kwargs: object) -> dict:
        replacement = tmp_path / "replacement.json"
        changed = _combined_config()
        changed["paths"] = {
            "request_intents": "unreviewed/intents.jsonl",
            "workspace": "unreviewed/workspace",
        }
        replacement.write_text(canonical_json(changed) + "\n")
        replacement.replace(config_path)
        return {
            "freeze": {
                "collection_freeze_path": "collection-freeze.json",
                "collection_freeze_sha256": "freeze-sha",
                "collection_review_path": "collection-review.json",
                "collection_review_sha256": "review-sha",
                "frozen_inputs": [
                    {"path": "config.json", "sha256": reviewed_sha}
                ],
            }
        }

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, request=request)

    monkeypatch.setattr(retry, "validate_retry_authorization", validated)
    with pytest.raises(RetryGateError, match="retry config hash mismatch"):
        retry._execute_authorized_retry(
            tmp_path,
            config_path,
            combined,
            hash_file(combined),
            retry_seal,
            hash_file(retry_seal),
            transport=httpx.MockTransport(handler),
        )
    assert calls == 0
    assert not (tmp_path / "unreviewed/workspace").exists()
    assert not (tmp_path / "data/events.jsonl").exists()


def test_execute_retry_binds_combined_seal_to_genesis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = tmp_path / "studies/painter_feature_generation_v1/PROTOCOL.md"
    protocol.parent.mkdir(parents=True)
    protocol.write_text("Protocol ID: `painter-feature-generation-v1/2.0`\n")
    config = {
        "schema_version": "painter-feature-generation-v1-broad-wikidata-config/1.0",
        "census_id": "explicit-capability-r2",
        "protocol_id": "painter-feature-generation-v1/2.0",
        "protocol_path": "studies/painter_feature_generation_v1/PROTOCOL.md",
        "scope": retry._SCOPE,
        "source_contract": {
            "endpoint": "https://query.wikidata.org/sparql",
            "method": "GET",
            "accept": "application/sparql-results+json",
            "timeout_seconds": 1.0,
            "minimum_interval_seconds": 0.0,
            "redirects": "forbidden",
            "api_version": "test",
            "data_version": "test",
            "request_not_after_utc": "2099-01-01T00:00:00Z",
            "canonicalization_rule": "test",
            "duplicate_rule": "test",
            "raw_response_rule": "test",
            "rights_and_media_rule": "test",
        },
        "painters": [
            {"painter_id": "monet", "creator_qid": "Q296"},
            {"painter_id": "sisley", "creator_qid": "Q175130"},
            {"painter_id": "pissarro", "creator_qid": "Q134741"},
            {"painter_id": "cezanne", "creator_qid": "Q35548"},
        ],
        "query_template": (
            "SELECT DISTINCT ?item ?image WHERE { ?item wdt:P170 "
            "wd:{creator_qid}; wdt:P31 wd:Q3305213; wdt:P18 ?image. } "
            "ORDER BY STR(?item) STR(?image)"
        ),
        "paths": {
            "request_intents": "data/intents.jsonl",
            "request_events": "data/events.jsonl",
            "candidate_manifest": "data/candidates.jsonl",
            "execution_receipt": "data/receipt.json",
            "workspace": "workspace/r2",
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    broad.prepare(tmp_path, config_path)
    seal_path = tmp_path / "data/combined.json"
    seal_path.write_text("{}\n")
    combined_sha = "c" * 64

    def handler(request: httpx.Request) -> httpx.Response:
        query = request.url.params["query"]
        qid = next(
            value
            for value in ("Q296", "Q175130", "Q134741", "Q35548")
            if value in query
        )
        number = {"Q296": "1", "Q175130": "2", "Q134741": "3", "Q35548": "4"}[
            qid
        ]
        payload = {
            "head": {"vars": ["item", "image"]},
            "results": {
                "bindings": [
                    {
                        "item": {
                            "type": "uri",
                            "value": f"http://www.wikidata.org/entity/Q{number}",
                        },
                        "image": {
                            "type": "uri",
                            "value": (
                                "http://commons.wikimedia.org/wiki/Special:FilePath/"
                                f"{qid}.jpg"
                            ),
                        },
                    }
                ]
            },
        }
        return httpx.Response(
            200,
            headers={
                "Content-Type": "application/sparql-results+json",
                "Date": "Wed, 02 Sep 2026 12:00:00 GMT",
            },
            json=payload,
            request=request,
        )

    retry_seal = tmp_path / "data/retry-seal.json"
    retry_seal.write_text("{}\n")
    monkeypatch.setattr(
        retry,
        "_validated_execution_context",
        lambda *args, **kwargs: {
            "seal": {"freeze_path": "data/freeze.json", "freeze_sha256": "f" * 64},
            "freeze": {},
            "review": {},
            "config": config,
            "intents": broad.load_intents(tmp_path, config),
            "request_intents_sha256": hash_file(tmp_path / "data/intents.jsonl"),
        },
    )
    receipt = retry.execute_retry(
        tmp_path,
        config_path,
        seal_path,
        combined_sha,
        retry_seal,
        "r" * 64,
        transport=httpx.MockTransport(handler),
    )
    events = [
        json.loads(line) for line in (tmp_path / "data/events.jsonl").read_text().splitlines()
    ]
    lock = json.loads((tmp_path / "workspace/r2/execution.lock").read_text())
    assert receipt["successful_requests"] == 4
    assert events[0]["authorization_seal_sha256"] == combined_sha
    assert lock["authorization_seal_sha256"] == combined_sha
