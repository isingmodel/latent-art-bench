"""Offline Freeze-A1 construction for the Pilot 3 real-art corpus.

Only pinned JSON/JSONL metadata is read here.  Image URLs and prior local image
paths are treated as opaque strings: this module never opens, decodes, hashes,
or otherwise inspects an artwork file.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from latent_art_bench.io import canonical_json, hash_file, read_json, read_jsonl, stable_hash
from latent_art_bench.pilot3.feasibility import (
    CandidateArtist,
    MetadataRows,
    Pilot3FeasibilityConfig,
    audit_feasibility,
    verify_feasibility_result,
)

CORPUS_CONFIG_SCHEMA = "pilot3-corpus-freeze-config/1.0"
CORPUS_ROW_SCHEMA = "pilot3-corpus-selection-row/1.0"
CORPUS_SUMMARY_SCHEMA = "pilot3-corpus-selection/1.0"
REAL_SPLIT_ROW_SCHEMA = "pilot3-real-split-row/1.0"
HOLDOUT_SEAL_SCHEMA = "pilot3-holdout-seal/1.0"

DEFAULT_CORPUS_CONFIG = Path("configs/pilot_3/corpus_freeze.json")
DEFAULT_CORPUS_MANIFEST = Path("data/manifests/pilot_3/corpus_selection.jsonl")
DEFAULT_REAL_SPLITS = Path("data/manifests/pilot_3/real_splits.jsonl")
DEFAULT_CORPUS_EVIDENCE = Path("reports/pilot_3/evidence/corpus_selection.json")
DEFAULT_HOLDOUT_SEAL = Path("reports/pilot_3/evidence/holdout_seal.json")
DEFAULT_FEASIBILITY_EVIDENCE = Path("reports/pilot_3/evidence/artist_source_feasibility.json")

_SHA256_LENGTH = 64
_SOURCE_ORDER = ("aic", "met", "museum_balanced")
_PRIOR_CANDIDATE_IDS = (
    "alfred_sisley",
    "armand_guillaumin",
    "berthe_morisot",
    "camille_pissarro",
    "claude_monet",
    "eugene_boudin",
    "gustave_caillebotte",
    "paul_cezanne",
    "pierre_auguste_renoir",
)
_PARTITIONS = {
    "development_training",
    "development_calibration",
    "external_holdout",
}

# These identifiers describe the digital reproduction, not the depicted artwork.
# Legacy spellings are retained only where they are exact values in pinned
# authoritative metadata.  Adding another identifier is a code and
# test change; candidate prose cannot silently create a new allowed license.
PERMISSIVE_REPRODUCTION_LICENSE_IDS = frozenset(
    {
        "CC0",
        "CC0-1.0",
        "CC-BY-4.0",
        "CC-BY-SA-4.0",
        "open_access_public_domain",
        "public_domain",
    }
)
FILE_BACKED_PERMISSION_LICENSE_ID = "FILE_BACKED_PERMISSION"
INSTITUTIONAL_RESEARCH_USE_LICENSE_ID = "INSTITUTIONAL_RESEARCH_USE"
REPRODUCTION_PERMISSION_SCHEMA = "pilot3-reproduction-permission/1.0"
REQUIRED_REPRODUCTION_PERMISSION_SCOPE = frozenset(
    {
        "automated_acquisition",
        "cryptographic_hashing",
        "fixed_feature_extraction",
        "local_storage",
        "machine_learning_inference_no_weight_updates",
        "noncommercial_research",
        "research_verification_retention",
        "statistical_analysis",
        "technical_normalization",
    }
)


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _SHA256_LENGTH
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_mapping(value: object, *, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return dict(value)


def _require_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a trimmed non-blank string")
    return value


def _relative_path(value: object, *, label: str) -> Path:
    text = _require_text(value, label=label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must remain inside the repository")
    return path


def _resolve(root: Path, relative: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    result = (resolved_root / relative).resolve()
    try:
        result.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {relative}") from exc
    return result


def _verify_binding(root: Path, raw: object, *, label: str) -> Tuple[Path, Dict[str, Any]]:
    binding = _require_mapping(raw, label=label)
    relative = _relative_path(binding.get("path"), label=f"{label}.path")
    expected = binding.get("file_sha256")
    if not _is_sha256(expected):
        raise ValueError(f"{label}.file_sha256 is invalid")
    path = _resolve(root, relative)
    if not path.is_file():
        raise FileNotFoundError(path)
    observed = hash_file(path)
    if observed != expected:
        raise RuntimeError(f"{label} hash mismatch: expected {expected}, found {observed}")
    return path, binding


def _verify_self_hash(value: Mapping[str, Any], *, field: str, label: str) -> None:
    payload = dict(value)
    recorded = payload.pop(field, None)
    if not _is_sha256(recorded) or stable_hash(payload) != recorded:
        raise ValueError(f"{label} has a stale {field}")


def _jsonl_sha256(rows: Iterable[Mapping[str, Any]]) -> str:
    rendered = "".join(f"{canonical_json(row)}\n" for row in rows)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _rank_digest(namespace: str, *parts: str) -> str:
    return hashlib.sha256("\0".join((namespace, *parts)).encode("utf-8")).hexdigest()


def _http_host(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise ValueError("URL must use HTTP(S)")
    authority = value.split("://", 1)[1].split("/", 1)[0]
    return authority.rsplit("@", 1)[-1].split(":", 1)[0].casefold()


def _timestamp(value: object, *, label: str) -> datetime:
    text = _require_text(value, label=label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _permission_scope(value: object, *, label: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    scope = tuple(value)
    if not all(isinstance(item, str) and item.strip() == item and item for item in scope):
        raise ValueError(f"{label} entries must be trimmed non-blank strings")
    if tuple(sorted(set(scope))) != scope:
        raise ValueError(f"{label} must be sorted and contain no duplicates")
    missing = sorted(REQUIRED_REPRODUCTION_PERMISSION_SCOPE - set(scope))
    if missing:
        raise ValueError(f"{label} lacks required operations: {', '.join(missing)}")
    return scope


def validate_digital_reproduction_authorization(
    root: Path,
    row: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    evaluated_at: str,
) -> Dict[str, Any]:
    """Validate rights to operate on one digital reproduction, without asset I/O.

    Artwork public-domain status is deliberately checked elsewhere.  This gate
    accepts only an enumerated reproduction license/open-access assertion or a
    structured, hash-pinned permission file issued by the configured asset
    authority.  Free-form ``rights_basis`` prose is never authorization.
    """

    license_id = _require_text(row.get("asset_license"), label="asset_license")
    if license_id in PERMISSIVE_REPRODUCTION_LICENSE_IDS:
        return {
            "authorization_type": "enumerated_permissive_license",
            "evidence_path": None,
            "evidence_sha256": None,
            "expires_at": None,
            "license_id": license_id,
            "status": "authorized",
        }
    if license_id == INSTITUTIONAL_RESEARCH_USE_LICENSE_ID:
        evidence = _require_mapping(row.get("rights_evidence"), label="rights_evidence")
        if evidence.get("study_use") != (
            "internal_noncommercial_scholarly_research_measurement_only"
        ):
            raise ValueError("institutional rights evidence has an unsupported study use")
        if evidence.get("redistribution_allowed_by_study") is not False:
            raise ValueError("institutional source images must not be redistributed")
        if evidence.get("asset_url") != row.get("image_url"):
            raise ValueError("institutional rights evidence is bound to another asset")
        if evidence.get("authority") != row.get("collection_block_name"):
            raise ValueError("institutional rights authority does not match the block")
        policy_url = _require_text(evidence.get("policy_url"), label="rights_evidence.policy_url")
        _http_host(policy_url)
        _require_text(evidence.get("scope"), label="rights_evidence.scope")
        reviewed_at = _require_text(
            evidence.get("reviewed_at"), label="rights_evidence.reviewed_at"
        )
        try:
            reviewed_date = datetime.fromisoformat(reviewed_at).date()
        except ValueError as exc:
            raise ValueError("rights_evidence.reviewed_at must be an ISO date") from exc
        if reviewed_date > _timestamp(
            evaluated_at, label="rights evaluation timestamp"
        ).date():
            raise ValueError("institutional rights review postdates the metadata snapshot")
        semantic_sha256 = evidence.get("semantic_sha256")
        if not _is_sha256(semantic_sha256):
            raise ValueError("institutional rights evidence lacks a semantic SHA-256")
        binding = {
            key: evidence[key]
            for key in (
                "authority",
                "policy_url",
                "reviewed_at",
                "scope",
            )
        }
        if evidence.get("content_sha256") is not None:
            if not _is_sha256(evidence.get("content_sha256")):
                raise ValueError("institutional policy response hash is invalid")
            binding["content_sha256"] = evidence["content_sha256"]
        if evidence.get("review_method") is not None:
            binding["review_method"] = _require_text(
                evidence.get("review_method"), label="rights_evidence.review_method"
            )
        if stable_hash(binding) != semantic_sha256:
            raise ValueError("institutional rights evidence has a stale semantic hash")
        return {
            "authorization_type": "institutional_published_research_terms",
            "authority": evidence["authority"],
            "evidence_path": None,
            "evidence_sha256": semantic_sha256,
            "expires_at": None,
            "license_id": license_id,
            "policy_url": policy_url,
            "scope": evidence["scope"],
            "source_id": row["source_id"],
            "source_object_id": row["source_object_id"],
            "status": "authorized",
        }
    if license_id != FILE_BACKED_PERMISSION_LICENSE_ID:
        raise ValueError(
            f"asset_license is not an approved digital-reproduction authorization: {license_id}"
        )

    pointer = _require_mapping(row.get("asset_permission"), label="asset_permission")
    if pointer.get("status") != "authorized":
        raise ValueError("asset_permission.status must be authorized")
    relative = _relative_path(pointer.get("evidence_path"), label="asset_permission.evidence_path")
    if relative.suffix.casefold() != ".json" or relative.parts[:3] != (
        "configs",
        "pilot_3",
        "permissions",
    ):
        raise ValueError("asset permission evidence must be JSON under configs/pilot_3/permissions")
    expected_sha = pointer.get("evidence_sha256")
    if not _is_sha256(expected_sha):
        raise ValueError("asset_permission.evidence_sha256 is invalid")
    evidence_path = _resolve(root, relative)
    if not evidence_path.is_file():
        raise FileNotFoundError(evidence_path)
    if hash_file(evidence_path) != expected_sha:
        raise RuntimeError("asset permission evidence hash mismatch")
    evidence = _require_mapping(read_json(evidence_path), label="asset permission evidence")
    if evidence.get("schema_version") != REPRODUCTION_PERMISSION_SCHEMA:
        raise ValueError("asset permission evidence has the wrong schema")

    authority = _require_text(evidence.get("authority"), label="permission.authority")
    configured_authority = _require_text(
        source.get("asset_governance"), label="source.asset_governance"
    )
    if authority != configured_authority or pointer.get("authority") != authority:
        raise ValueError("asset permission authority does not match asset governance")
    if evidence.get("source_id") != row.get("source_id"):
        raise ValueError("asset permission is bound to another source")
    object_ids = evidence.get("source_object_ids")
    if (
        not isinstance(object_ids, list)
        or not object_ids
        or not all(isinstance(item, str) and item.strip() == item and item for item in object_ids)
        or sorted(set(object_ids)) != object_ids
    ):
        raise ValueError("permission.source_object_ids must be a sorted unique non-empty list")
    if row.get("source_object_id") not in object_ids:
        raise ValueError("asset permission does not cover this source object")

    scope = _permission_scope(evidence.get("scope"), label="permission.scope")
    pointer_scope = _permission_scope(pointer.get("scope"), label="asset_permission.scope")
    if pointer_scope != scope:
        raise ValueError("asset permission scope does not match its evidence")
    expires_at = _require_text(evidence.get("expires_at"), label="permission.expires_at")
    if pointer.get("expires_at") != expires_at:
        raise ValueError("asset permission expiry does not match its evidence")
    if _timestamp(expires_at, label="permission.expires_at") <= _timestamp(
        evaluated_at, label="rights evaluation timestamp"
    ):
        raise ValueError("asset permission is expired at the rights evaluation timestamp")

    return {
        "authorization_type": "file_backed_permission",
        "authority": authority,
        "evidence_path": relative.as_posix(),
        "evidence_sha256": str(expected_sha),
        "expires_at": expires_at,
        "license_id": license_id,
        "scope": list(scope),
        "source_id": row["source_id"],
        "source_object_id": row["source_object_id"],
        "status": "authorized",
    }


def _artist_config(config: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = config.get("artists")
    if not isinstance(raw, list) or len(raw) != 4:
        raise ValueError("Freeze A1 requires exactly four configured artists")
    result: Dict[str, Dict[str, Any]] = {}
    for position, item in enumerate(raw):
        row = _require_mapping(item, label=f"artists[{position}]")
        artist_id = _require_text(row.get("artist_id"), label="artist_id")
        artist_name = _require_text(row.get("artist_name"), label="artist_name")
        aliases = row.get("aliases")
        if (
            not isinstance(aliases, list)
            or not aliases
            or not all(isinstance(alias, str) and alias.strip() for alias in aliases)
        ):
            raise ValueError(f"{artist_id} requires explicit aliases")
        authority_ids = _require_mapping(
            row.get("authority_ids"), label=f"{artist_id}.authority_ids"
        )
        required_authorities = {
            "aic_agent_id",
            "met_constituent_id",
            "nga_constituent_id",
            "ulan",
            "wikidata",
        }
        if set(authority_ids) != required_authorities or not all(
            isinstance(value, str) and value.strip() for value in authority_ids.values()
        ):
            raise ValueError(f"{artist_id} authority identifiers are incomplete")
        if artist_id in result:
            raise ValueError(f"duplicate artist id: {artist_id}")
        result[artist_id] = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "aliases": list(aliases),
            "authority_ids": authority_ids,
        }
    if list(result) != sorted(result):
        raise ValueError("artists must be sorted by artist_id")
    return result


def _candidate_universe_disposition(config: Mapping[str, Any]) -> Dict[str, Any]:
    disposition = _require_mapping(
        config.get("candidate_universe_disposition"),
        label="candidate_universe_disposition",
    )
    if disposition.get("selection_type") != (
        "purposive_finite_pilot_roster_from_prior_research_not_probability_sampling"
    ):
        raise ValueError("candidate universe must preserve the purposive finite-roster claim")
    if disposition.get("fresh_authoritative_audit_scope") != "four_selected_finalists_only":
        raise ValueError("fresh authoritative audit scope must be explicit")
    if disposition.get("unselected_artist_feasibility_claim") is not False:
        raise ValueError("unselected artists cannot receive a feasibility claim")
    rows = disposition.get("artists")
    if not isinstance(rows, list) or len(rows) != len(_PRIOR_CANDIDATE_IDS):
        raise ValueError("candidate universe must contain exactly the nine prior candidates")
    ids = tuple(str(row.get("artist_id")) for row in rows if isinstance(row, Mapping))
    if ids != _PRIOR_CANDIDATE_IDS:
        raise ValueError("candidate universe must use the frozen sorted candidate order")
    selected = []
    for row in rows:
        candidate = _require_mapping(row, label="candidate universe artist")
        _require_text(candidate.get("artist_name"), label="candidate artist_name")
        _require_text(candidate.get("basis"), label="candidate basis")
        if candidate.get("disposition") == "selected_finalist":
            selected.append(candidate["artist_id"])
        elif candidate.get("disposition") != "not_advanced_to_fresh_audit":
            raise ValueError("candidate disposition is invalid")
    if tuple(sorted(selected)) != (
        "alfred_sisley",
        "camille_pissarro",
        "paul_cezanne",
        "pierre_auguste_renoir",
    ):
        raise ValueError("candidate disposition does not match the four frozen finalists")
    return disposition


def _source_config(config: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = config.get("sources")
    if not isinstance(raw, list):
        raise ValueError("sources must be a list")
    result: Dict[str, Dict[str, Any]] = {}
    collection_governance = set()
    for position, item in enumerate(raw):
        row = _require_mapping(item, label=f"sources[{position}]")
        source_id = _require_text(row.get("source_id"), label="source_id")
        for field in (
            "source_name",
            "source_role",
            "snapshot_id",
            "collection_governance",
            "asset_governance",
        ):
            _require_text(row.get(field), label=f"{source_id}.{field}")
        if row["source_role"] not in {"development", "external"}:
            raise ValueError(f"invalid source role for {source_id}")
        if source_id in result:
            raise ValueError(f"duplicate source id: {source_id}")
        result[source_id] = row
        collection_governance.add(row["collection_governance"])
    if tuple(result) != _SOURCE_ORDER:
        raise ValueError(f"sources must be ordered exactly as {_SOURCE_ORDER!r}")
    if len(collection_governance) != len(result):
        raise ValueError("collection sources must have independent governance")
    if [result[source]["source_role"] for source in _SOURCE_ORDER] != [
        "development",
        "development",
        "external",
    ]:
        raise ValueError("AIC/Met must be development and museum-balanced must be external")
    return result


def load_corpus_config(root: Path, config_path: Path = DEFAULT_CORPUS_CONFIG) -> Dict[str, Any]:
    """Load and validate the prospective, metadata-only Freeze-A1 contract."""

    path = _resolve(root, config_path)
    config = _require_mapping(read_json(path), label="corpus freeze config")
    if config.get("schema_version") != CORPUS_CONFIG_SCHEMA:
        raise ValueError("unexpected corpus freeze config schema")
    if config.get("status") != "freeze_a1_requested":
        raise ValueError("corpus freeze config must request Freeze A1")
    if config.get("content_domain") != "landscape_and_outdoor_place_scene":
        raise ValueError("Pilot 3 must use its frozen common content domain")
    _candidate_universe_disposition(config)
    _artist_config(config)
    _source_config(config)
    selection = _require_mapping(config.get("selection"), label="selection")
    if selection.get("development_works_per_artist_source") != 5:
        raise ValueError("the frozen design requires five development works per artist/source")
    if selection.get("external_works_per_artist") != 3:
        raise ValueError("the frozen design requires three external works per artist")
    if selection.get("replacement_eligible_reserves_included") is not False:
        raise ValueError("the frozen external design has no post-freeze substitutes")
    _require_text(selection.get("selection_namespace"), label="selection_namespace")
    split = _require_mapping(config.get("split"), label="split")
    if split.get("development_source_ids") != ["aic", "met"]:
        raise ValueError("development sources must be AIC and Met")
    if split.get("external_source_ids") != ["museum_balanced"]:
        raise ValueError("the external source must be museum-balanced")
    if split.get("calibration_works_per_artist_development_source") != 1:
        raise ValueError("one AIC and one Met work per artist must be calibration")
    if split.get("not_selected_partition", "not-present") is not None:
        raise ValueError("not-selected partition must be null")
    _require_text(split.get("partition_namespace"), label="partition_namespace")
    block_design = _require_mapping(
        selection.get("external_block_design"), label="selection.external_block_design"
    )
    if block_design != {
        "source_id": "museum_balanced",
        "primary_block_ids": ["minneapolis", "dallas", "toledo"],
        "replacement_eligible_reserve_block_ids": [],
        "replacement_unit": "none_after_freeze",
        "works_per_artist_per_block": 1,
        "permutation_unit": "complete_holding_institution_block",
    }:
        raise ValueError("the external collection-block design is not exactly frozen")
    _verify_binding(root, config.get("external_block_roster"), label="external_block_roster")
    prohibited = config.get("selection_prohibitions")
    if not isinstance(prohibited, list) or set(prohibited) != {
        "artwork_pixels",
        "generated_outputs",
        "feature_vectors",
        "embedding_distances",
        "effect_estimates",
        "inferential_results",
    }:
        raise ValueError("selection prohibitions are incomplete")
    return config


def _verify_snapshot_and_candidates(
    root: Path,
    config: Mapping[str, Any],
    artists: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
) -> Tuple[
    List[Dict[str, Any]],
    Dict[str, Any],
    Dict[str, Dict[str, Any]],
    Dict[str, Any],
]:
    candidate_path, candidate_binding = _verify_binding(
        root, config.get("candidate_manifest"), label="candidate_manifest"
    )
    snapshot_path, snapshot_binding = _verify_binding(
        root, config.get("source_snapshot"), label="source_snapshot"
    )
    snapshot = _require_mapping(read_json(snapshot_path), label="source snapshot")
    _verify_self_hash(snapshot, field="semantic_sha256", label="source snapshot")
    rights_evaluated_at = _require_text(snapshot.get("accessed_at"), label="snapshot.accessed_at")
    _timestamp(rights_evaluated_at, label="snapshot.accessed_at")
    if snapshot.get("semantic_sha256") != snapshot_binding.get("semantic_sha256"):
        raise RuntimeError("source snapshot semantic binding mismatch")
    if snapshot.get("artwork_or_image_bytes_requested") is not False:
        raise ValueError("source snapshot does not attest metadata-only collection")
    if snapshot.get("candidate_manifest_path") != candidate_path.relative_to(root).as_posix():
        raise ValueError("source snapshot points at another candidate manifest")
    if snapshot.get("artist_authorities") != {
        artist_id: {
            "artist_name": row["artist_name"],
            "aliases": row["aliases"],
            **row["authority_ids"],
        }
        for artist_id, row in artists.items()
    }:
        raise ValueError("source snapshot artist authority roster is stale")

    response_groups: Dict[str, List[str]] = {source_id: [] for source_id in sources}
    responses = snapshot.get("responses")
    if not isinstance(responses, list) or not responses:
        raise ValueError("source snapshot lacks raw-response evidence")
    for position, raw in enumerate(responses):
        row = _require_mapping(raw, label=f"responses[{position}]")
        method = row.get("request_method")
        if method == "GET":
            if row.get("response_status") != 200:
                raise ValueError("every direct metadata response must be a successful GET")
            response_digest = row.get("content_sha256")
            if not _is_sha256(response_digest):
                raise ValueError("every direct metadata response requires an exact SHA-256")
            if not isinstance(row.get("content_length"), int) or row["content_length"] <= 0:
                raise ValueError("every direct metadata response requires a positive byte length")
        elif method == "metadata_only_browser_review":
            if (
                row.get("source_id") != "museum_balanced"
                or row.get("response_status") != "reviewed"
                or not _is_sha256(row.get("semantic_sha256"))
                or row.get("content_sha256") is not None
                or row.get("content_length") is not None
            ):
                raise ValueError("manual metadata review evidence is malformed")
            response_digest = row["semantic_sha256"]
        else:
            raise ValueError("metadata evidence uses an unsupported review method")
        content_type = str(row.get("content_type") or "").casefold()
        if content_type.startswith("image/"):
            raise ValueError("source snapshot contains an image response")
        url = _require_text(row.get("url"), label="response.url")
        host = _http_host(url)
        source_id = _require_text(row.get("source_id"), label="response.source_id")
        allowed_hosts = {
            "aic": {"api.artic.edu", "www.artic.edu"},
            "met": {
                "media.githubusercontent.com",
                "www.wikidata.org",
                "commons.wikimedia.org",
            },
            "museum_balanced": {
                "commons.wikimedia.org",
                "emuseum.toledomuseum.org",
                "files.dma.org",
                "raw.githubusercontent.com",
                "search.artsmia.org",
                "shop.dma.org",
                "toledomuseum.org",
            },
        }
        if source_id not in sources or host not in allowed_hosts[source_id]:
            raise ValueError(
                f"metadata endpoint/source mismatch: source={source_id}, endpoint={url}"
            )
        response_groups[source_id].append(str(response_digest))
        _require_text(row.get("accessed_at"), label="response.accessed_at")
    if any(not values for values in response_groups.values()):
        raise ValueError("each configured source requires exact response-hash evidence")

    roster_path, roster_binding = _verify_binding(
        root, config.get("external_block_roster"), label="external_block_roster"
    )
    roster = _require_mapping(read_json(roster_path), label="external block roster")
    if stable_hash(roster) != roster_binding.get("semantic_sha256"):
        raise RuntimeError("external block roster semantic binding mismatch")
    if snapshot.get("external_museum_roster") != {
        "path": roster_path.relative_to(root).as_posix(),
        "file_sha256": hash_file(roster_path),
        "semantic_sha256": stable_hash(roster),
        "work_count": 12,
    }:
        raise RuntimeError("source snapshot external-roster binding mismatch")
    frozen_external = {}
    for block in roster.get("blocks") or []:
        if not isinstance(block, Mapping):
            raise ValueError("external block roster contains a non-object block")
        for work in block.get("works") or []:
            if not isinstance(work, Mapping):
                raise ValueError("external block roster contains a non-object work")
            source_object_id = (
                f"{block.get('block_id')}:{work.get('museum_object_id')}"
            )
            if not work.get("work_wikidata_id") or source_object_id in frozen_external:
                raise ValueError("external block roster work identity is missing or duplicated")
            frozen_external[source_object_id] = {
                "artist_id": work.get("artist_id"),
                "collection_block_id": block.get("block_id"),
                "collection_block_name": block.get("block_name"),
                "collection_block_role": block.get("role"),
                "collection_wikidata_id": block.get("collection_wikidata_id"),
                "delivery_height": work.get("delivery_height"),
                "delivery_width": work.get("delivery_width"),
                "image_url": work.get("image_url"),
                "museum_accession": work.get("museum_accession"),
                "title": work.get("title"),
                "wikidata_id": work.get("work_wikidata_id"),
            }
    if len(frozen_external) != 12:
        raise ValueError("external block roster must contain exactly twelve works")

    rows = [
        _require_mapping(row, label=f"candidate[{position}]")
        for position, row in enumerate(read_jsonl(candidate_path))
    ]
    if snapshot.get("candidate_row_count") != len(rows):
        raise ValueError("source snapshot candidate count is stale")
    if stable_hash(rows) != candidate_binding.get("semantic_sha256"):
        raise RuntimeError("candidate manifest semantic binding mismatch")
    if snapshot.get("candidate_manifest_semantic_sha256") != stable_hash(rows):
        raise RuntimeError("source snapshot does not bind the candidate rows")

    seen_source_objects = set()
    seen_canonical_ids = set()
    reproduction_authorizations: Dict[str, Dict[str, Any]] = {}
    for position, row in enumerate(rows):
        sealed = dict(row)
        recorded = sealed.pop("metadata_row_sha256", None)
        if not _is_sha256(recorded) or stable_hash(sealed) != recorded:
            raise ValueError(f"candidate row {position} has a stale metadata hash")
        artist_id = row.get("artist_id")
        source_id = row.get("source_id")
        if artist_id not in artists or source_id not in sources:
            raise ValueError("candidate row falls outside the frozen roster/source set")
        artist = artists[str(artist_id)]
        source = sources[str(source_id)]
        if row.get("artist_name") != artist["artist_name"]:
            raise ValueError(f"candidate artist name mismatch for {artist_id}")
        if row.get("artist_authority_ids") != artist["authority_ids"]:
            raise ValueError(f"candidate authority mismatch for {artist_id}")
        if row.get("source_snapshot_id") != source["snapshot_id"]:
            raise ValueError(f"candidate snapshot mismatch for {source_id}")
        if row.get("attribution_role") != "artist" or row.get("attribution_status") != (
            "confirmed_by_authority_id_and_artist_role"
        ):
            raise ValueError("candidate attribution is not authority-confirmed")
        if row.get("public_domain_status") != "confirmed":
            raise ValueError("candidate public-domain status is not confirmed")
        if "paint" not in str(row.get("classification") or "").casefold():
            raise ValueError("candidate is not classified as a painting")
        for field in ("rights_basis", "asset_license", "asset_provider"):
            _require_text(row.get(field), label=f"candidate.{field}")
        for field in ("source_url", "image_url"):
            url = _require_text(row.get(field), label=f"candidate.{field}")
            _http_host(url)
        width = row.get("native_width")
        height = row.get("native_height")
        delivery_width = row.get("delivery_width")
        delivery_height = row.get("delivery_height")
        if not isinstance(width, int) or not isinstance(height, int) or min(width, height) <= 0:
            raise ValueError("candidate requires declared positive native dimensions")
        if (
            not isinstance(delivery_width, int)
            or not isinstance(delivery_height, int)
            or min(delivery_width, delivery_height) <= 0
            or delivery_width > width
            or delivery_height > height
        ):
            raise ValueError("candidate requires a valid, non-upsamped delivery geometry")
        object_id = _require_text(row.get("source_object_id"), label="source_object_id")
        canonical_id = f"work-{source_id}-{object_id}"
        if row.get("canonical_work_id") != canonical_id:
            raise ValueError("candidate canonical identity must be source-object based")
        catalog_ids = _require_mapping(row.get("catalog_ids"), label="catalog_ids")
        if catalog_ids.get(source_id) != object_id:
            raise ValueError("candidate catalog identity disagrees with source object")
        accession_key = f"{source_id}_accession"
        _require_text(catalog_ids.get(accession_key), label=accession_key)
        identity = (source_id, object_id)
        if identity in seen_source_objects or canonical_id in seen_canonical_ids:
            raise ValueError("candidate manifest contains duplicate physical holdings")
        seen_source_objects.add(identity)
        seen_canonical_ids.add(canonical_id)
        if row.get("decision") == "include":
            if not row.get("genre_evidence") or int(row.get("genre_score", 0)) < 3:
                raise ValueError("included candidate lacks common-domain metadata evidence")
            if (
                min(delivery_width, delivery_height) < 512
                or max(delivery_width, delivery_height)
                / min(delivery_width, delivery_height)
                >= 2
            ):
                raise ValueError("included candidate fails the frozen geometry rule")
            reproduction_authorizations[canonical_id] = validate_digital_reproduction_authorization(
                root,
                row,
                source,
                evaluated_at=rights_evaluated_at,
            )
        if source_id == "museum_balanced":
            expected = frozen_external.get(object_id)
            observed = {
                "artist_id": artist_id,
                "collection_block_id": row.get("collection_block_id"),
                "collection_block_name": row.get("collection_block_name"),
                "collection_block_role": row.get("collection_block_role"),
                "collection_wikidata_id": row.get("collection_wikidata_id"),
                "delivery_height": delivery_height,
                "delivery_width": delivery_width,
                "image_url": row.get("image_url"),
                "museum_accession": catalog_ids.get("museum_accession"),
                "title": row.get("title"),
                "wikidata_id": row.get("wikidata_id"),
            }
            if expected is None or observed != expected:
                raise ValueError(
                    "official-museum candidate does not exactly match the frozen block roster"
                )
            attribution = _require_mapping(
                row.get("asset_attribution"), label="candidate.asset_attribution"
            )
            if attribution.get("required") is True and (
                not attribution.get("artist_or_creator")
                or not attribution.get("description_url")
                or not attribution.get("license_url")
            ):
                raise ValueError("official-museum reproduction lacks attribution evidence")
            capture = _require_mapping(
                row.get("capture_pipeline"), label="candidate.capture_pipeline"
            )
            if (
                capture.get("block_id") != row.get("collection_block_id")
                or capture.get("holding_institution") != row.get("collection_block_name")
                or capture.get("same_capture_session_claimed") is not False
            ):
                raise ValueError("external capture-pipeline claim is malformed")
        elif any(
            row.get(field) is not None
            for field in (
                "collection_block_id",
                "collection_block_name",
                "collection_block_role",
                "collection_wikidata_id",
                "rights_evidence",
            )
        ):
            raise ValueError("development candidate unexpectedly carries external-block fields")
    return (
        rows,
        snapshot,
        reproduction_authorizations,
        {
            "candidate_manifest": {
                "path": candidate_path.relative_to(root).as_posix(),
                "file_sha256": hash_file(candidate_path),
                "semantic_sha256": stable_hash(rows),
                "row_count": len(rows),
            },
            "source_snapshot": {
                "path": snapshot_path.relative_to(root).as_posix(),
                "file_sha256": hash_file(snapshot_path),
                "semantic_sha256": snapshot["semantic_sha256"],
                "accessed_at": snapshot["accessed_at"],
                "response_content_sha256_by_source": {
                    key: sorted(value) for key, value in response_groups.items()
                },
            },
        },
    )


def _deduplication_review(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    eligible = [row for row in rows if row.get("decision") == "include"]
    wikidata: Dict[str, List[str]] = defaultdict(list)
    title_year: Dict[Tuple[str, str, object], List[Mapping[str, Any]]] = defaultdict(list)
    for row in eligible:
        if row.get("wikidata_id"):
            wikidata[str(row["wikidata_id"])].append(str(row["canonical_work_id"]))
        title_key = " ".join(str(row["title"]).casefold().split())
        title_year[(str(row["artist_id"]), title_key, row.get("creation_year"))].append(row)
    duplicate_authority = {key: value for key, value in sorted(wikidata.items()) if len(value) > 1}
    if duplicate_authority:
        raise ValueError(
            "a Wikidata physical-work identity appears in multiple holdings: "
            f"{canonical_json(duplicate_authority)}"
        )
    reviewed_collisions = []
    for (artist_id, title, year), members in sorted(title_year.items()):
        if len(members) < 2:
            continue
        accessions = [str(row["catalog_ids"][f"{row['source_id']}_accession"]) for row in members]
        if len(accessions) != len(set(accessions)):
            raise ValueError("title/year collision lacks distinct accession identities")
        reviewed_collisions.append(
            {
                "artist_id": artist_id,
                "creation_year": year,
                "normalized_title": title,
                "canonical_work_ids": sorted(str(row["canonical_work_id"]) for row in members),
                "resolution": (
                    "distinct_physical_holdings_confirmed_by_unique_museum_object_and_accession_ids"
                ),
            }
        )
    return {
        "canonical_identity_policy": (
            "one physical museum holding per source-object/accession identity; shared "
            "Wikidata work identities would fail closed"
        ),
        "cross_source_distinctness_verified": True,
        "duplicate_authoritative_work_id_count": 0,
        "eligible_unique_physical_work_count": len(eligible),
        "title_year_collision_count": len(reviewed_collisions),
        "title_year_collisions_reviewed_as_distinct": reviewed_collisions,
        "title_year_used_for_automatic_union": False,
    }


def _prior_local_reproductions(
    root: Path, config: Mapping[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    section = _require_mapping(config.get("prior_local_corpus"), label="prior_local_corpus")
    canonical_relative = _relative_path(
        section.get("canonical_works_path"), label="canonical_works_path"
    )
    reproductions_relative = _relative_path(
        section.get("reproductions_path"), label="reproductions_path"
    )
    canonical_path = _resolve(root, canonical_relative)
    reproductions_path = _resolve(root, reproductions_relative)
    for path, expected, label in (
        (canonical_path, section.get("canonical_works_file_sha256"), "canonical works"),
        (
            reproductions_path,
            section.get("reproductions_file_sha256"),
            "reproductions",
        ),
    ):
        if not _is_sha256(expected) or hash_file(path) != expected:
            raise RuntimeError(f"prior local {label} manifest hash mismatch")
    canonical_ids = {row["canonical_work_id"] for row in read_jsonl(canonical_path)}
    indexed: Dict[str, Dict[str, Any]] = {}
    for raw in read_jsonl(reproductions_path):
        row = _require_mapping(raw, label="prior reproduction")
        # Pilot 0 also retained CMA alternate captures.  They are outside the
        # frozen AIC/Met/official-museum roster and are not candidate reuse records here.
        if row.get("source_id") not in _SOURCE_ORDER:
            continue
        work_id = row.get("canonical_work_id")
        if work_id not in canonical_ids:
            raise ValueError("prior reproduction lacks a canonical work")
        if work_id in indexed:
            raise ValueError(f"multiple prior reproductions for {work_id}")
        if not _is_sha256(row.get("sha256")):
            raise ValueError("prior reproduction lacks a valid file SHA-256")
        indexed[str(work_id)] = row
    return indexed, {
        "canonical_works_path": canonical_relative.as_posix(),
        "canonical_works_file_sha256": hash_file(canonical_path),
        "reproductions_path": reproductions_relative.as_posix(),
        "reproductions_file_sha256": hash_file(reproductions_path),
        "reuse_policy": section["reuse_policy"],
        "artwork_files_opened_or_hashed_by_freeze": False,
    }


def _selected_rows(
    candidates: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, Any]],
    prior_reproductions: Mapping[str, Mapping[str, Any]],
    reproduction_authorizations: Mapping[str, Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    selection = _require_mapping(config.get("selection"), label="selection")
    split = _require_mapping(config.get("split"), label="split")
    selection_namespace = str(selection["selection_namespace"])
    partition_namespace = str(split["partition_namespace"])
    required_by_source = {
        "aic": int(selection["development_works_per_artist_source"]),
        "met": int(selection["development_works_per_artist_source"]),
        "museum_balanced": int(selection["external_works_per_artist"]),
    }
    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in candidates:
        if row.get("decision") == "include":
            grouped[(str(row["artist_id"]), str(row["source_id"]))].append(row)

    ranked: Dict[Tuple[str, str], List[Tuple[Mapping[str, Any], str]]] = {}
    for key, rows in sorted(grouped.items()):
        ranked_rows = [
            (
                row,
                _rank_digest(
                    selection_namespace,
                    str(row["artist_id"]),
                    str(row["source_id"]),
                    str(row["canonical_work_id"]),
                ),
            )
            for row in rows
        ]
        ranked_rows.sort(
            key=lambda item: (
                -int(item[0]["genre_score"]),
                item[1],
                str(item[0]["canonical_work_id"]),
            )
        )
        required = required_by_source[key[1]]
        if len(ranked_rows) < required:
            raise RuntimeError(f"Freeze A1 cell {key!r} has fewer than {required} works")
        if key[1] == "museum_balanced" and len(ranked_rows) != required:
            raise RuntimeError("the external cell must exactly equal the frozen three-block roster")
        ranked[key] = ranked_rows

    selected_partitions: Dict[str, str] = {}
    for artist_id, source_id in sorted(ranked):
        required = required_by_source[source_id]
        selected = ranked[(artist_id, source_id)][:required]
        if sources[source_id]["source_role"] == "external":
            for row, _ in selected:
                selected_partitions[str(row["canonical_work_id"])] = "external_holdout"
            continue
        ordered = sorted(
            selected,
            key=lambda item: _rank_digest(
                partition_namespace,
                artist_id,
                source_id,
                str(item[0]["canonical_work_id"]),
            ),
        )
        calibration_count = int(split["calibration_works_per_artist_development_source"])
        calibration_ids = {str(row["canonical_work_id"]) for row, _ in ordered[:calibration_count]}
        for row, _ in selected:
            work_id = str(row["canonical_work_id"])
            selected_partitions[work_id] = (
                "development_calibration" if work_id in calibration_ids else "development_training"
            )

    corpus_rows: List[Dict[str, Any]] = []
    split_rows: List[Dict[str, Any]] = []
    for (artist_id, source_id), rows in sorted(ranked.items()):
        required = required_by_source[source_id]
        for selection_rank, (candidate, ranking_sha256) in enumerate(rows, start=1):
            selected = selection_rank <= required
            partition = (
                selected_partitions[str(candidate["canonical_work_id"])] if selected else None
            )
            prior = prior_reproductions.get(str(candidate["canonical_work_id"]))
            prior_mismatch = False
            if prior is not None and (
                prior.get("source_id") != source_id
                or prior.get("source_url") != candidate.get("image_url")
            ):
                # A matching museum object is not enough to reuse a different
                # derivative.  Freeze A1 records the mismatch and Phase A must
                # acquire the newly frozen URL; no old bytes are opened here.
                prior_mismatch = True
                prior = None
            common = {
                "artist_authority_ids": candidate["artist_authority_ids"],
                "artist_id": artist_id,
                "artist_name": candidate["artist_name"],
                "asset_license": candidate["asset_license"],
                "asset_provider": candidate["asset_provider"],
                "canonical_work_id": candidate["canonical_work_id"],
                "catalog_ids": candidate["catalog_ids"],
                "classification": candidate["classification"],
                "common_domain_decision": "include",
                "common_domain_evidence": candidate["genre_evidence"],
                "common_domain_score": candidate["genre_score"],
                "content_domain": config["content_domain"],
                "creation_year": candidate.get("creation_year"),
                "collection_block_id": candidate.get("collection_block_id") or source_id,
                "collection_block_name": candidate.get("collection_block_name"),
                "collection_block_role": candidate.get("collection_block_role"),
                "collection_wikidata_id": candidate.get("collection_wikidata_id"),
                "capture_pipeline": candidate.get("capture_pipeline"),
                "digital_reproduction_authorization": dict(
                    reproduction_authorizations[str(candidate["canonical_work_id"])]
                ),
                "image_url": candidate["image_url"],
                "delivery_height": candidate["delivery_height"],
                "delivery_width": candidate["delivery_width"],
                "museum_accession": (
                    candidate["catalog_ids"].get("museum_accession")
                    or candidate["catalog_ids"].get(f"{source_id}_accession")
                ),
                "native_height": candidate["native_height"],
                "native_width": candidate["native_width"],
                "partition": partition,
                "prior_local_reproduction_manifest_row_sha256": (
                    stable_hash(prior) if prior is not None else None
                ),
                "prior_local_reproduction_path": (
                    prior.get("local_path") if prior is not None else None
                ),
                "prior_local_reproduction_sha256": (
                    prior.get("sha256") if prior is not None else None
                ),
                "prior_local_reproduction_status": (
                    "metadata_pointer_only_pending_phase_a_rehash"
                    if prior is not None
                    else "same_work_different_derivative_not_reused"
                    if prior_mismatch
                    else "no_exact_prior_local_reproduction_recorded"
                ),
                "public_domain_status": candidate["public_domain_status"],
                "replacement_partition_policy": split["not_selected_replacement_policy"],
                "rights_basis": candidate["rights_basis"],
                "selection_rank": selection_rank,
                "selection_ranking_sha256": ranking_sha256,
                "selection_status": "selected" if selected else "not_selected",
                "source_id": source_id,
                "source_metadata_row_sha256": candidate["metadata_row_sha256"],
                "source_object_id": candidate["source_object_id"],
                "source_role": sources[source_id]["source_role"],
                "source_snapshot_id": candidate["source_snapshot_id"],
                "source_url": candidate["source_url"],
                "title": candidate["title"],
                "wikidata_id": candidate.get("wikidata_id"),
            }
            selection_projection = {
                key: common[key]
                for key in (
                    "artist_id",
                    "canonical_work_id",
                    "partition",
                    "selection_rank",
                    "selection_ranking_sha256",
                    "selection_status",
                    "source_id",
                    "source_metadata_row_sha256",
                )
            }
            common["selection_sha256"] = stable_hash(selection_projection)
            corpus_row = {
                "record_type": "pilot3_corpus_selection_row",
                "schema_version": CORPUS_ROW_SCHEMA,
                **common,
            }
            corpus_row["row_sha256"] = stable_hash(corpus_row)
            corpus_rows.append(corpus_row)
            split_row = {
                "record_type": "pilot3_real_split_row",
                "schema_version": REAL_SPLIT_ROW_SCHEMA,
                **common,
                "corpus_selection_row_sha256": corpus_row["row_sha256"],
            }
            split_row["row_sha256"] = stable_hash(split_row)
            split_rows.append(split_row)
    return corpus_rows, split_rows


def _promote_feasibility(
    candidates: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    artists: Mapping[str, Mapping[str, Any]],
    snapshot_binding: Mapping[str, Any],
    deduplication: Mapping[str, Any],
    corpus_rows: Sequence[Mapping[str, Any]],
    historical_binding: Mapping[str, Any],
) -> Dict[str, Any]:
    reproduction_rights_verified = bool(corpus_rows) and all(
        row.get("digital_reproduction_authorization", {}).get("status") == "authorized"
        for row in corpus_rows
    )
    if not reproduction_rights_verified:
        raise RuntimeError("Freeze A1 reproduction-rights gate is not satisfied")
    input_evidence = (
        {
            "manifest_path": snapshot_binding["candidate_manifest"]["path"],
            "manifest_bytes_sha256": snapshot_binding["candidate_manifest"]["file_sha256"],
            "format": "jsonl",
            "row_count": len(candidates),
            "referenced_asset_io_performed": False,
        },
        {
            "manifest_path": snapshot_binding["source_snapshot"]["path"],
            "manifest_bytes_sha256": snapshot_binding["source_snapshot"]["file_sha256"],
            "format": "json",
            "row_count": len(
                snapshot_binding["source_snapshot"]["response_content_sha256_by_source"]
            ),
            "referenced_asset_io_performed": False,
        },
    )
    feasibility_config = Pilot3FeasibilityConfig(
        candidate_artists=tuple(
            CandidateArtist(artist_id, row["artist_name"]) for artist_id, row in artists.items()
        ),
        min_unique_works_per_artist_source=3,
        min_artist_count=4,
        min_source_count=3,
        source_ids=_SOURCE_ORDER,
        eligible_decisions=("include",),
        require_confirmed_public_domain=True,
    )
    result = audit_feasibility(MetadataRows(tuple(candidates), input_evidence), feasibility_config)
    if result["configured_snapshot_threshold_result"] != ("meets_configured_snapshot_thresholds"):
        raise RuntimeError("authoritative snapshot does not support every frozen source cell")
    result.pop("semantic_sha256")
    result["status"] = (
        "authoritative_metadata_audit_complete_freeze_a1_ready"
        if reproduction_rights_verified
        else "authoritative_metadata_audit_complete_freeze_a1_blocked_by_reproduction_rights"
    )
    result["claim_boundary"] = {
        "cross_source_distinctness_verified": True,
        "external_catalog_coverage_claimed": False,
        "freeze_a1_ready": reproduction_rights_verified,
        "raw_response_hashes_and_access_dates_verified": True,
        "snapshot_scope": (
            "the exactly bound AIC, Met, and official holding-institution metadata responses"
        ),
        "source_governance_and_independence_verified": True,
        "visual_content_or_artwork_byte_integrity_verified": False,
        "scope_interpretation": (
            "Freeze A1 certifies this supplied authoritative metadata snapshot and "
            "selection only; Phase A must still acquire or rehash, decode, and visually QC "
            "the selected reproductions."
        ),
    }
    result["eligibility_scope"].update(
        {
            "artifact_reapplies_full_domain_rules": True,
            "rights_basis_reverified": reproduction_rights_verified,
            "trusted_snapshot_flag": None,
            (
                "upstream_attribution_object_type_common_domain_and_"
                "acquisition_eligibility_reverified"
            ): True,
            "domain_verification_level": (
                "authoritative_catalog_fields_plus_frozen_metadata_rule_no_pixel_review"
            ),
        }
    )
    result["freeze_readiness"] = {
        "freeze_a1_ready": reproduction_rights_verified,
        "readiness_decision": (
            "FREEZE_A1_READY_AUTHORITATIVE_METADATA_AND_SELECTION"
            if reproduction_rights_verified
            else "FREEZE_A1_BLOCKED_BY_REPRODUCTION_RIGHTS"
        ),
        "readiness_transition_supported_by_this_schema": True,
        "unverified_downstream_prerequisites": [
            "artwork-byte acquisition or exact prior-file rehash",
            "decode, color-profile, border, crop, corruption, and visual-domain QC",
            "feature extraction and Phase-A qualification",
        ],
    }
    result["authoritative_snapshot_binding"] = dict(snapshot_binding)
    result["deduplication_review"] = dict(deduplication)
    result["frozen_selection_binding"] = {
        "manifest_path": DEFAULT_CORPUS_MANIFEST.as_posix(),
        "manifest_file_sha256": _jsonl_sha256(corpus_rows),
        "row_count": len(corpus_rows),
        "selected_row_count": sum(row["selection_status"] == "selected" for row in corpus_rows),
        "selection_semantic_sha256": stable_hash([row["selection_sha256"] for row in corpus_rows]),
    }
    result["historical_planning_result"] = dict(historical_binding)
    result["candidate_universe_disposition"] = _candidate_universe_disposition(config)
    result["semantic_sha256"] = stable_hash(result)
    verify_feasibility_result(result)
    return result


def _seal(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(payload)
    result["semantic_sha256"] = stable_hash(result)
    return result


def _summary(
    *,
    config_path: Path,
    config_sha256: str,
    snapshot_binding: Mapping[str, Any],
    prior_binding: Mapping[str, Any],
    historical_binding: Mapping[str, Any],
    deduplication: Mapping[str, Any],
    corpus_rows: Sequence[Mapping[str, Any]],
    split_rows: Sequence[Mapping[str, Any]],
    feasibility: Mapping[str, Any],
    candidate_universe_disposition: Mapping[str, Any],
) -> Dict[str, Any]:
    selected = [row for row in corpus_rows if row["selection_status"] == "selected"]
    not_selected = [
        row for row in corpus_rows if row["selection_status"] == "not_selected"
    ]
    reproduction_rights_verified = bool(corpus_rows) and all(
        row.get("digital_reproduction_authorization", {}).get("status") == "authorized"
        for row in corpus_rows
    )
    cell_counts = Counter((row["artist_id"], row["source_id"]) for row in selected)
    partition_counts = Counter(row["partition"] for row in selected)
    payload = {
        "record_type": "pilot3_corpus_selection",
        "schema_version": CORPUS_SUMMARY_SCHEMA,
        "status": "freeze_a1_complete" if reproduction_rights_verified else "freeze_a1_blocked",
        "freeze_a1_ready": reproduction_rights_verified,
        "config_binding": {
            "path": config_path.as_posix(),
            "file_sha256": config_sha256,
        },
        "authoritative_snapshot_binding": dict(snapshot_binding),
        "historical_planning_result": dict(historical_binding),
        "candidate_universe_disposition": dict(candidate_universe_disposition),
        "feasibility_binding": {
            "path": DEFAULT_FEASIBILITY_EVIDENCE.as_posix(),
            "semantic_sha256": feasibility["semantic_sha256"],
            "status": feasibility["status"],
        },
        "manifests": {
            "corpus_selection": {
                "path": DEFAULT_CORPUS_MANIFEST.as_posix(),
                "file_sha256": _jsonl_sha256(corpus_rows),
                "row_count": len(corpus_rows),
                "rows_semantic_sha256": stable_hash(corpus_rows),
            },
            "real_splits": {
                "path": DEFAULT_REAL_SPLITS.as_posix(),
                "file_sha256": _jsonl_sha256(split_rows),
                "row_count": len(split_rows),
                "rows_semantic_sha256": stable_hash(split_rows),
            },
        },
        "selection": {
            "artist_count": 4,
            "source_count": 3,
            "development_works_per_artist_source": 5,
            "external_works_per_artist": 3,
            "selected_work_count": len(selected),
            "not_selected_work_count": len(not_selected),
            "replacement_eligible_reserve_work_count": 0,
            "selected_counts_by_artist_source": {
                artist_id: {
                    source_id: cell_counts[(artist_id, source_id)] for source_id in _SOURCE_ORDER
                }
                for artist_id in sorted({str(row["artist_id"]) for row in selected})
            },
            "partition_counts": dict(sorted(partition_counts.items())),
            "selection_basis": (
                "authoritative public-domain painting metadata, frozen outdoor-place "
                "metadata rule, coverage, then deterministic preregistered ranking"
            ),
            "forbidden_selection_inputs_used": [],
            "not_selected_partition": None,
            "not_selected_replacement_policy": corpus_rows[0][
                "replacement_partition_policy"
            ],
        },
        "deduplication_review": dict(deduplication),
        "prior_local_reproduction_reuse": {
            **dict(prior_binding),
            "selected_rows_with_prior_pointer": sum(
                row["selection_status"] == "selected"
                and row["prior_local_reproduction_path"] is not None
                for row in corpus_rows
            ),
        },
        "checks": {
            "artist_authority_ids_and_aliases_verified": True,
            "attribution_and_painting_classification_verified": True,
            "common_domain_metadata_rule_verified": True,
            "public_domain_and_asset_rights_basis_verified": reproduction_rights_verified,
            "raw_response_hashes_and_access_dates_bound": True,
            "independent_collection_governance_verified": True,
            "canonical_identity_and_duplicate_review_complete": True,
            "selected_cell_sizes_match_frozen_design": all(
                count == (3 if source_id == "museum_balanced" else 5)
                for (_, source_id), count in cell_counts.items()
            ) and len(cell_counts) == 12,
            "external_holdout_is_museum_balanced_only": all(
                row["source_id"] == "museum_balanced"
                for row in selected
                if row["partition"] == "external_holdout"
            ),
            "external_holdout_contains_three_complete_blocks": Counter(
                row["collection_block_id"]
                for row in selected
                if row["partition"] == "external_holdout"
            ) == {"dallas": 4, "minneapolis": 4, "toledo": 4},
            "no_artwork_or_generated_bytes_opened": True,
            "no_features_or_effect_estimates_used": True,
        },
        "claim_boundary": (
            "Freeze A1 fixes 40 development works (five per artist in each of AIC and "
            "Met) and a 12-work external holdout comprising three complete four-artist "
            "official-museum blocks. It does not claim that any artwork file has "
            "been acquired, rehashed, decoded, visually reviewed, or feature-qualified."
        ),
    }
    if not all(payload["checks"].values()):
        raise RuntimeError("Freeze A1 summary contains a failed prerequisite")
    return _seal(payload)


def _holdout_seal(
    corpus_rows: Sequence[Mapping[str, Any]], split_rows: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    selected = [row for row in split_rows if row["selection_status"] == "selected"]
    holdout = [row for row in selected if row["partition"] == "external_holdout"]
    development = [row for row in selected if row["partition"] != "external_holdout"]
    not_selected = [
        row for row in split_rows if row["selection_status"] == "not_selected"
    ]
    if len(holdout) != 12 or len(development) != 40:
        raise RuntimeError("frozen real split does not have 40 development/12 external works")
    if any(row["source_id"] != "museum_balanced" for row in holdout):
        raise RuntimeError("external holdout contains a non-museum-balanced work")
    if any(row["source_id"] == "museum_balanced" for row in development):
        raise RuntimeError("development contains an external museum-block work")
    block_counts = Counter(row.get("collection_block_id") for row in holdout)
    if block_counts != {"dallas": 4, "minneapolis": 4, "toledo": 4}:
        raise RuntimeError("external holdout does not contain three complete museum blocks")
    payload = {
        "record_type": "pilot3_holdout_seal",
        "schema_version": HOLDOUT_SEAL_SCHEMA,
        "status": "external_holdout_metadata_sealed_not_acquired",
        "external_source_id": "museum_balanced",
        "development_source_ids": ["aic", "met"],
        "selected_counts": {
            "development_training": sum(
                row["partition"] == "development_training" for row in selected
            ),
            "development_calibration": sum(
                row["partition"] == "development_calibration" for row in selected
            ),
            "external_holdout": len(holdout),
        },
        "external_holdout_work_ids": [row["canonical_work_id"] for row in holdout],
        "external_holdout_selection_sha256s": [row["selection_sha256"] for row in holdout],
        "external_block_ids": ["dallas", "minneapolis", "toledo"],
        "external_block_counts": dict(sorted(block_counts.items())),
        "external_permutation_unit": "complete_holding_institution_block",
        "external_exact_assignment_count": 13824,
        "not_selected_work_count": len(not_selected),
        "replacement_eligible_reserve_work_count": 0,
        "not_selected_partition": None,
        "not_selected_replacement_policy": corpus_rows[0][
            "replacement_partition_policy"
        ],
        "corpus_selection_manifest": {
            "path": DEFAULT_CORPUS_MANIFEST.as_posix(),
            "file_sha256": _jsonl_sha256(corpus_rows),
        },
        "real_splits_manifest": {
            "path": DEFAULT_REAL_SPLITS.as_posix(),
            "file_sha256": _jsonl_sha256(split_rows),
        },
        "separation_policy": (
            "AIC and Met are development sources; the three complete official-museum "
            "blocks are sealed as the external source. External works may not enter "
            "training, calibration, threshold selection, or model-choice decisions, and "
            "no post-freeze replacement is permitted."
        ),
        "artwork_bytes_opened": False,
        "claim_boundary": (
            "This seal fixes metadata identities and partitions only. External artwork "
            "bytes remain unacquired and uninspected until the authorized Phase-A step."
        ),
    }
    return _seal(payload)


def _verify_rows(rows: Sequence[Mapping[str, Any]], *, schema: str, record_type: str) -> None:
    seen = set()
    for row in rows:
        if row.get("schema_version") != schema or row.get("record_type") != record_type:
            raise ValueError("unexpected Pilot 3 manifest row schema")
        _verify_self_hash(row, field="row_sha256", label=record_type)
        selection_hash = row.get("selection_sha256")
        if not _is_sha256(selection_hash):
            raise ValueError("manifest row lacks a selection SHA-256")
        identity = (row.get("canonical_work_id"), row.get("selection_status"))
        if identity in seen:
            raise ValueError("manifest contains a duplicate work identity")
        seen.add(identity)
        if row.get("selection_status") == "selected":
            if row.get("partition") not in _PARTITIONS:
                raise ValueError("selected work lacks a valid partition")
        elif row.get("selection_status") == "not_selected":
            if row.get("partition") is not None:
                raise ValueError("not-selected work must have a null partition")
        else:
            raise ValueError("invalid selection status")
        authorization = row.get("digital_reproduction_authorization")
        if not isinstance(authorization, Mapping) or authorization.get("status") != "authorized":
            raise ValueError("manifest row lacks authorized digital-reproduction rights")
        license_id = authorization.get("license_id")
        authorization_type = authorization.get("authorization_type")
        if authorization_type == "enumerated_permissive_license":
            if license_id not in PERMISSIVE_REPRODUCTION_LICENSE_IDS:
                raise ValueError("manifest row has an unapproved reproduction license")
        elif authorization_type == "file_backed_permission":
            if (
                license_id != FILE_BACKED_PERMISSION_LICENSE_ID
                or not _is_sha256(authorization.get("evidence_sha256"))
                or not authorization.get("evidence_path")
                or not authorization.get("authority")
                or not authorization.get("expires_at")
            ):
                raise ValueError("manifest row has incomplete file-backed permission")
            _permission_scope(
                authorization.get("scope"),
                label="digital_reproduction_authorization.scope",
            )
        elif authorization_type == "institutional_published_research_terms":
            if (
                license_id != INSTITUTIONAL_RESEARCH_USE_LICENSE_ID
                or not _is_sha256(authorization.get("evidence_sha256"))
                or not authorization.get("authority")
                or not authorization.get("policy_url")
                or authorization.get("expires_at") is not None
                or authorization.get("source_id") != "museum_balanced"
            ):
                raise ValueError("manifest row has incomplete institutional-use evidence")
        else:
            raise ValueError("manifest row has an unknown reproduction authorization type")


def build_corpus_bundle(root: Path, config_path: Path = DEFAULT_CORPUS_CONFIG) -> Dict[str, Any]:
    """Build all Freeze-A1 objects deterministically, without writing or asset I/O."""

    resolved_root = root.expanduser().resolve()
    config = load_corpus_config(resolved_root, config_path)
    artists = _artist_config(config)
    sources = _source_config(config)
    candidates, snapshot, reproduction_authorizations, snapshot_binding = (
        _verify_snapshot_and_candidates(resolved_root, config, artists, sources)
    )
    deduplication = _deduplication_review(candidates)
    prior_reproductions, prior_binding = _prior_local_reproductions(resolved_root, config)
    corpus_rows, split_rows = _selected_rows(
        candidates,
        config,
        sources,
        prior_reproductions,
        reproduction_authorizations,
    )
    _verify_rows(
        corpus_rows,
        schema=CORPUS_ROW_SCHEMA,
        record_type="pilot3_corpus_selection_row",
    )
    _verify_rows(
        split_rows,
        schema=REAL_SPLIT_ROW_SCHEMA,
        record_type="pilot3_real_split_row",
    )
    historical_path, historical_binding = _verify_binding(
        resolved_root,
        config.get("historical_planning_feasibility"),
        label="historical_planning_feasibility",
    )
    historical = _require_mapping(
        read_json(historical_path), label="historical planning feasibility"
    )
    verify_feasibility_result(historical)
    portable_historical_binding = {
        "path": historical_path.relative_to(resolved_root).as_posix(),
        "file_sha256": historical_binding["file_sha256"],
        "semantic_sha256": historical["semantic_sha256"],
        "status": historical["status"],
        "preservation_role": "superseded_planning_snapshot_not_current_p3_t01",
    }
    feasibility = _promote_feasibility(
        candidates,
        config,
        artists,
        snapshot_binding,
        deduplication,
        corpus_rows,
        portable_historical_binding,
    )
    config_sha256 = hash_file(_resolve(resolved_root, config_path))
    summary = _summary(
        config_path=config_path,
        config_sha256=config_sha256,
        snapshot_binding=snapshot_binding,
        prior_binding=prior_binding,
        historical_binding=portable_historical_binding,
        deduplication=deduplication,
        corpus_rows=corpus_rows,
        split_rows=split_rows,
        feasibility=feasibility,
        candidate_universe_disposition=_candidate_universe_disposition(config),
    )
    holdout = _holdout_seal(corpus_rows, split_rows)
    _verify_self_hash(summary, field="semantic_sha256", label="corpus summary")
    _verify_self_hash(holdout, field="semantic_sha256", label="holdout seal")
    return {
        "config": config,
        "snapshot": snapshot,
        "corpus_rows": corpus_rows,
        "split_rows": split_rows,
        "feasibility": feasibility,
        "summary": summary,
        "holdout": holdout,
    }


def write_corpus_bundle(root: Path, config_path: Path = DEFAULT_CORPUS_CONFIG) -> Dict[str, Any]:
    """Write canonical P3-T01, P3-T05, and P3-T06 artifacts atomically."""

    from latent_art_bench.io import write_json, write_jsonl

    resolved_root = root.expanduser().resolve()
    bundle = build_corpus_bundle(resolved_root, config_path)
    write_jsonl(_resolve(resolved_root, DEFAULT_CORPUS_MANIFEST), bundle["corpus_rows"])
    write_jsonl(_resolve(resolved_root, DEFAULT_REAL_SPLITS), bundle["split_rows"])
    write_json(_resolve(resolved_root, DEFAULT_FEASIBILITY_EVIDENCE), bundle["feasibility"])
    write_json(_resolve(resolved_root, DEFAULT_CORPUS_EVIDENCE), bundle["summary"])
    write_json(_resolve(resolved_root, DEFAULT_HOLDOUT_SEAL), bundle["holdout"])
    return bundle["summary"]


def verify_corpus_bundle(root: Path, config_path: Path = DEFAULT_CORPUS_CONFIG) -> Dict[str, Any]:
    """Rebuild and verify every canonical artifact without network or artwork I/O."""

    resolved_root = root.expanduser().resolve()
    expected = build_corpus_bundle(resolved_root, config_path)
    observed_corpus = read_jsonl(_resolve(resolved_root, DEFAULT_CORPUS_MANIFEST))
    observed_splits = read_jsonl(_resolve(resolved_root, DEFAULT_REAL_SPLITS))
    if observed_corpus != expected["corpus_rows"]:
        raise RuntimeError("stale deterministic Pilot 3 corpus-selection manifest")
    if observed_splits != expected["split_rows"]:
        raise RuntimeError("stale deterministic Pilot 3 real-splits manifest")
    for path, key in (
        (DEFAULT_FEASIBILITY_EVIDENCE, "feasibility"),
        (DEFAULT_CORPUS_EVIDENCE, "summary"),
        (DEFAULT_HOLDOUT_SEAL, "holdout"),
    ):
        if read_json(_resolve(resolved_root, path)) != expected[key]:
            raise RuntimeError(f"stale deterministic Pilot 3 artifact: {path}")
    return expected["summary"]


__all__ = [
    "CORPUS_CONFIG_SCHEMA",
    "CORPUS_ROW_SCHEMA",
    "CORPUS_SUMMARY_SCHEMA",
    "DEFAULT_CORPUS_CONFIG",
    "DEFAULT_CORPUS_EVIDENCE",
    "DEFAULT_CORPUS_MANIFEST",
    "DEFAULT_FEASIBILITY_EVIDENCE",
    "DEFAULT_HOLDOUT_SEAL",
    "DEFAULT_REAL_SPLITS",
    "FILE_BACKED_PERMISSION_LICENSE_ID",
    "HOLDOUT_SEAL_SCHEMA",
    "PERMISSIVE_REPRODUCTION_LICENSE_IDS",
    "REAL_SPLIT_ROW_SCHEMA",
    "REPRODUCTION_PERMISSION_SCHEMA",
    "REQUIRED_REPRODUCTION_PERMISSION_SCOPE",
    "build_corpus_bundle",
    "load_corpus_config",
    "validate_digital_reproduction_authorization",
    "verify_corpus_bundle",
    "write_corpus_bundle",
]
