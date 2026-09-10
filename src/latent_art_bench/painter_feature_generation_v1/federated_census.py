from __future__ import annotations

import argparse
import contextlib
import email.utils
import fcntl
import hashlib
import html
import json
import math
import os
import re
import tempfile
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import httpx

from latent_art_bench.io import canonical_json, hash_file


class CensusError(RuntimeError):
    """Raised when a frozen census contract is missing, invalid, or drifts."""


_EVENT_SCHEMA = "painter-feature-generation-v1-request-event/1.1"
_EXPECTED_SEMANTIC_OUTCOMES = {
    "wikidata_entities": "complete_wikidata_entity_batch",
    "commons_imageinfo": "complete_commons_current_revision_batch",
}


@dataclass(frozen=True)
class RequestSpec:
    request_id: str
    stage: str
    sequence: int
    endpoint: str
    params: dict[str, str]
    members: tuple[str, ...]

    def as_record(self, census_id: str) -> dict[str, Any]:
        return {
            "schema_version": "painter-feature-generation-v1-request-intent/1.0",
            "census_id": census_id,
            "request_id": self.request_id,
            "stage": self.stage,
            "sequence": self.sequence,
            "method": "GET",
            "endpoint": self.endpoint,
            "params": self.params,
            "members": list(self.members),
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _chunks(values: Sequence[str], size: int) -> Iterable[Sequence[str]]:
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def _entity_id(value: str) -> str:
    match = re.search(r"(Q\d+)$", value)
    if not match:
        raise CensusError(f"not a Wikidata entity URI or ID: {value!r}")
    return match.group(1)


def _commons_filename(value: str) -> str:
    marker = "Special:FilePath/"
    if marker not in value:
        raise CensusError(f"not a Commons Special:FilePath URL: {value!r}")
    filename = urllib.parse.unquote(value.split(marker, 1)[1]).replace("_", " ").strip()
    if not filename:
        raise CensusError("empty Commons filename")
    return filename


def _binding_value(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, Mapping) or not isinstance(value.get("value"), str):
        raise CensusError(f"discovery row lacks {key!r}")
    return str(value["value"])


def load_discovery_rows(
    path: Path,
    expected_sha256: str,
    painters: Mapping[str, str],
    expected_rows: int,
    expected_items: int,
    expected_files: int,
) -> list[dict[str, str]]:
    observed_hash = hash_file(path)
    if observed_hash != expected_sha256:
        raise CensusError(
            f"discovery input SHA-256 drift: expected {expected_sha256}, observed {observed_hash}"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    bindings = payload.get("results", {}).get("bindings", [])
    if not isinstance(bindings, list):
        raise CensusError("discovery input does not contain SPARQL bindings")
    rows: list[dict[str, str]] = []
    for raw in bindings:
        if not isinstance(raw, Mapping):
            raise CensusError("discovery binding is not an object")
        creator_qid = _entity_id(_binding_value(raw, "creator"))
        if creator_qid not in painters:
            raise CensusError(f"unfrozen creator in discovery input: {creator_qid}")
        item_qid = _entity_id(_binding_value(raw, "item"))
        filename = _commons_filename(_binding_value(raw, "image"))
        rows.append(
            {
                "painter_id": painters[creator_qid],
                "creator_qid": creator_qid,
                "item_qid": item_qid,
                "commons_filename": filename,
            }
        )
    rows.sort(
        key=lambda row: (
            row["painter_id"],
            int(row["item_qid"][1:]),
            row["commons_filename"].casefold(),
        )
    )
    if len(rows) != expected_rows:
        raise CensusError(f"expected {expected_rows} discovery rows, observed {len(rows)}")
    if len({row["item_qid"] for row in rows}) != expected_items:
        raise CensusError("distinct discovery-item count drifted")
    if len({row["commons_filename"] for row in rows}) != expected_files:
        raise CensusError("distinct discovery-file count drifted")
    if len({(row["item_qid"], row["commons_filename"]) for row in rows}) != len(rows):
        raise CensusError("duplicate item-file row in discovery input")
    return rows


def build_request_specs(
    config: Mapping[str, Any], rows: Sequence[Mapping[str, str]]
) -> list[RequestSpec]:
    request = config["request_contract"]
    size = int(request["batch_size"])
    if size < 1 or size > 50:
        raise CensusError("batch_size must be between 1 and 50")
    item_ids = sorted({row["item_qid"] for row in rows}, key=lambda value: int(value[1:]))
    file_titles = sorted({f"File:{row['commons_filename']}" for row in rows}, key=str.casefold)
    specs: list[RequestSpec] = []
    sequence = 0
    for index, batch in enumerate(_chunks(item_ids, size), start=1):
        sequence += 1
        specs.append(
            RequestSpec(
                request_id=f"wikidata-entities-{index:04d}",
                stage="wikidata_entities",
                sequence=sequence,
                endpoint=str(request["wikidata_endpoint"]),
                params={
                    "action": "wbgetentities",
                    "curtimestamp": "1",
                    "errorformat": "plaintext",
                    "format": "json",
                    "formatversion": "2",
                    "ids": "|".join(batch),
                    "languages": "en|fr",
                    "languagefallback": "1",
                    "maxlag": "5",
                    "props": str(request["wikidata_properties"]),
                    "servedby": "1",
                    "uselang": "en",
                },
                members=tuple(batch),
            )
        )
    for index, batch in enumerate(_chunks(file_titles, size), start=1):
        sequence += 1
        specs.append(
            RequestSpec(
                request_id=f"commons-imageinfo-{index:04d}",
                stage="commons_imageinfo",
                sequence=sequence,
                endpoint=str(request["commons_endpoint"]),
                params={
                    "action": "query",
                    "curtimestamp": "1",
                    "errorformat": "plaintext",
                    "format": "json",
                    "formatversion": "2",
                    "iiextmetadatalanguage": "en",
                    "iiextmetadatafilter": str(request["commons_extmetadata_fields"]),
                    "iilimit": "1",
                    "iimetadataversion": "1",
                    "iiprop": str(request["commons_imageinfo_properties"]),
                    "maxlag": "5",
                    "prop": "imageinfo",
                    "servedby": "1",
                    "titles": "|".join(batch),
                    "uselang": "en",
                },
                members=tuple(batch),
            )
        )
    return specs


def _statement_records(entity: Mapping[str, Any], property_id: str) -> list[dict[str, Any]]:
    claim_map = entity.get("claims")
    if not isinstance(claim_map, Mapping):
        raise CensusError("entity claims are not an object")
    claims = claim_map.get(property_id, [])
    if not isinstance(claims, list):
        raise CensusError(f"entity property {property_id} is not a claim list")
    if any(not isinstance(claim, Mapping) for claim in claims):
        raise CensusError(f"entity property {property_id} has a non-object claim")
    preferred = [claim for claim in claims if claim.get("rank") == "preferred"]
    selected = preferred or [claim for claim in claims if claim.get("rank", "normal") == "normal"]
    records: list[dict[str, Any]] = []
    for claim in selected:
        snak = claim.get("mainsnak", {})
        if not isinstance(snak, Mapping):
            raise CensusError(f"entity property {property_id} has a malformed mainsnak")
        if snak.get("snaktype") != "value":
            continue
        datavalue = snak.get("datavalue")
        if not isinstance(datavalue, Mapping) or "value" not in datavalue:
            raise CensusError(f"entity property {property_id} has a malformed datavalue")
        value = datavalue["value"]
        if isinstance(value, Mapping) and isinstance(value.get("id"), str):
            value = value["id"]
        elif isinstance(value, Mapping) and "text" in value:
            value = value.get("text")
        elif isinstance(value, Mapping) and "time" in value:
            value = value.get("time")
        elif isinstance(value, Mapping) and "amount" in value:
            value = {
                "amount": value.get("amount"),
                "unit": value.get("unit"),
                "lower_bound": value.get("lowerBound"),
                "upper_bound": value.get("upperBound"),
            }
        if value is not None:
            records.append({"value": value, "rank": str(claim.get("rank", "normal"))})
    return records


def _statement_values(entity: Mapping[str, Any], property_id: str) -> list[Any]:
    return [record["value"] for record in _statement_records(entity, property_id)]


def _p854_reference_url(snak: Mapping[str, Any]) -> str:
    if snak.get("snaktype") != "value":
        raise CensusError("P854 reference snak must have snaktype='value'")
    datavalue = snak.get("datavalue")
    if not isinstance(datavalue, Mapping):
        raise CensusError("P854 reference snak has a malformed datavalue")
    value = datavalue.get("value")
    if not isinstance(value, str):
        raise CensusError("P854 reference snak datavalue is not a URL string")
    try:
        parsed = urllib.parse.urlsplit(value)
        hostname = parsed.hostname
        parsed.port
    except ValueError as exc:
        raise CensusError("P854 reference snak datavalue is not a valid URL") from exc
    if (
        value != value.strip()
        or any(character.isspace() or not character.isprintable() for character in value)
        or re.search(r'''[\\"'<>|{}^`]''', value)
        or re.search(r"%(?![0-9A-Fa-f]{2})", value)
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or not hostname
    ):
        raise CensusError("P854 reference snak datavalue is not a valid HTTP(S) URL")
    return value


def _reference_urls(entity: Mapping[str, Any]) -> list[str]:
    urls: set[str] = set()
    claim_map = entity.get("claims", {})
    if not isinstance(claim_map, Mapping):
        raise CensusError("entity claims are not an object")
    for property_id in claim_map:
        selected_claims = claim_map[property_id]
        preferred = [claim for claim in selected_claims if claim.get("rank") == "preferred"]
        for claim in preferred or [
            claim for claim in selected_claims if claim.get("rank", "normal") == "normal"
        ]:
            for reference in claim.get("references", []):
                for snak in reference.get("snaks", {}).get("P854", []):
                    urls.add(_p854_reference_url(snak))
    return sorted(urls)


def parse_entity_batches(
    specs: Sequence[RequestSpec], response_paths: Mapping[str, Path]
) -> dict[str, dict[str, Any]]:
    entities: dict[str, dict[str, Any]] = {}
    for spec in specs:
        if spec.stage != "wikidata_entities":
            continue
        raw_path = response_paths[spec.request_id]
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        batch_entities = payload.get("entities", {})
        if not isinstance(batch_entities, Mapping):
            raise CensusError(f"{spec.request_id} lacks entities")
        raw_hash = hash_file(raw_path)
        for qid in spec.members:
            entity = batch_entities.get(qid)
            resolved_qid = (
                str(entity.get("id"))
                if isinstance(entity, Mapping) and re.fullmatch(r"Q\d+", str(entity.get("id")))
                else qid
            )
            if not isinstance(entity, Mapping) or entity.get("missing") is not None:
                entities[qid] = {
                    "entity_status": "missing",
                    "requested_entity_qid": qid,
                    "resolved_entity_qid": resolved_qid,
                    "redirected": resolved_qid != qid,
                    "raw_response_sha256": raw_hash,
                }
                continue
            labels = entity.get("labels", {})
            descriptions = entity.get("descriptions", {})
            creators = [str(value) for value in _statement_values(entity, "P170")]
            tracked_properties = (
                "P18",
                "P170",
                "P31",
                "P186",
                "P195",
                "P217",
                "P973",
                "P276",
                "P571",
                "P6216",
            )
            entities[qid] = {
                "entity_status": "resolved",
                "requested_entity_qid": qid,
                "resolved_entity_qid": resolved_qid,
                "redirected": resolved_qid != qid,
                "label": next(
                    (
                        labels[key].get("value")
                        for key in ("en", "fr")
                        if isinstance(labels.get(key), Mapping)
                    ),
                    None,
                ),
                "description": next(
                    (
                        descriptions[key].get("value")
                        for key in ("en", "fr")
                        if isinstance(descriptions.get(key), Mapping)
                    ),
                    None,
                ),
                "creator_qids": creators,
                "commons_filenames": [str(value) for value in _statement_values(entity, "P18")],
                "instance_qids": [str(value) for value in _statement_values(entity, "P31")],
                "material_qids": [str(value) for value in _statement_values(entity, "P186")],
                "collection_qids": [str(value) for value in _statement_values(entity, "P195")],
                "location_qids": [str(value) for value in _statement_values(entity, "P276")],
                "inventory_numbers": [str(value) for value in _statement_values(entity, "P217")],
                "described_at_urls": [str(value) for value in _statement_values(entity, "P973")],
                "inception_values": _statement_values(entity, "P571"),
                "copyright_status_qids": [
                    str(value) for value in _statement_values(entity, "P6216")
                ],
                "best_rank_claims": {
                    property_id: _statement_records(entity, property_id)
                    for property_id in tracked_properties
                },
                "reference_urls": _reference_urls(entity),
                "raw_response_sha256": raw_hash,
            }
    return entities


_TAG_RE = re.compile(r"<[^>]+>")
_HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']", re.IGNORECASE)


def _plain_text(value: str, limit: int = 2000) -> str:
    return " ".join(html.unescape(_TAG_RE.sub(" ", value)).split())[:limit]


def _metadata_value(metadata: Mapping[str, Any], key: str) -> str:
    value = metadata.get(key, {})
    if not isinstance(value, Mapping):
        return ""
    raw = value.get("value")
    return str(raw) if raw is not None else ""


def _metadata_urls(metadata: Mapping[str, Any], keys: Sequence[str]) -> list[str]:
    urls: set[str] = set()
    for key in keys:
        raw = html.unescape(_metadata_value(metadata, key))
        for url in _HREF_RE.findall(raw):
            if url.startswith(("http://", "https://")):
                urls.add(url)
        for url in re.findall(r"https?://[^\s<>\"']+", raw):
            urls.add(url.rstrip(".,;:)"))
    return sorted(urls)


def _is_http_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urllib.parse.urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_media_timestamp(value: Any) -> bool:
    return _parse_media_timestamp(value) is not None


def _parse_media_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def parse_media_batches(
    specs: Sequence[RequestSpec],
    response_paths: Mapping[str, Path],
    config: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    media: dict[str, dict[str, Any]] = {}
    screen = config["screening_contract"]
    allowed_urls = [
        str(value).casefold() for value in screen["allowed_commons_license_url_prefixes"]
    ]
    allowed_unlinked_names = {
        str(value).casefold() for value in screen["allowed_unlinked_license_short_names"]
    }
    nonfree_markers = [str(value).casefold() for value in screen["nonfree_markers"]]
    supported_mimes = {str(value).casefold() for value in screen["supported_image_mime_types"]}
    minimum_short = int(screen["minimum_short_side_pixels"])
    for spec in specs:
        if spec.stage != "commons_imageinfo":
            continue
        raw_path = response_paths[spec.request_id]
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        query = payload.get("query", {})
        pages = query.get("pages", [])
        if not isinstance(pages, list):
            raise CensusError(f"{spec.request_id} lacks pages")
        page_by_title = {
            str(page.get("title")): page
            for page in pages
            if isinstance(page, Mapping) and page.get("title")
        }
        raw_hash = hash_file(raw_path)
        for requested_title in spec.members:
            canonical_title = requested_title
            page = page_by_title.get(requested_title)
            if page is None:
                media[requested_title.removeprefix("File:")] = {
                    "media_status": "missing",
                    "raw_response_sha256": raw_hash,
                }
                continue
            info_rows = page.get("imageinfo") or []
            if len(info_rows) != 1:
                media[requested_title.removeprefix("File:")] = {
                    "media_status": "missing_or_ambiguous",
                    "canonical_title": canonical_title,
                    "raw_response_sha256": raw_hash,
                }
                continue
            info = info_rows[0]
            metadata = info.get("extmetadata") or {}
            license_short = _plain_text(_metadata_value(metadata, "LicenseShortName"))
            usage_terms = _plain_text(_metadata_value(metadata, "UsageTerms"))
            license_url = _plain_text(_metadata_value(metadata, "LicenseUrl"))
            copyrighted = _plain_text(_metadata_value(metadata, "Copyrighted"))
            restrictions = _plain_text(_metadata_value(metadata, "Restrictions"))
            permission = _plain_text(_metadata_value(metadata, "Permission"))
            normalized_license_url = license_url.casefold().replace("http://", "https://", 1)
            explicit_open_url = any(
                normalized_license_url.startswith(prefix) for prefix in allowed_urls
            )
            public_domain_url = "/publicdomain/" in normalized_license_url
            unlinked_public_domain = (
                not normalized_license_url
                and license_short.casefold() in allowed_unlinked_names
                and copyrighted.casefold() in {"false", "no"}
            )
            rights_text = " ".join(
                (
                    license_short,
                    usage_terms,
                    license_url,
                    copyrighted,
                    restrictions,
                    permission,
                )
            ).casefold()
            has_nonfree = any(marker in rights_text for marker in nonfree_markers)
            has_restriction = bool(restrictions and restrictions.casefold() not in {"none", "no"})
            copyrighted_value = copyrighted.casefold()
            copyrighted_is_consistent = copyrighted_value in {"", "false", "no", "true", "yes"}
            if public_domain_url:
                copyrighted_is_consistent = copyrighted_value in {"false", "no"}
            rights_candidate = (
                (explicit_open_url or unlinked_public_domain)
                and not has_nonfree
                and not has_restriction
                and copyrighted_is_consistent
            )
            width = int(info.get("width") or 0)
            height = int(info.get("height") or 0)
            mime = str(info.get("mime") or "").casefold()
            sha1 = str(info.get("sha1") or "")
            timestamp = info.get("timestamp")
            delivery_receipt_complete = (
                _is_http_url(info.get("url"))
                and _is_http_url(info.get("descriptionurl"))
                and bool(re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-z]{31})", sha1.casefold()))
                and _is_media_timestamp(timestamp)
            )
            media[requested_title.removeprefix("File:")] = {
                "media_status": "resolved",
                "canonical_title": canonical_title,
                "description_url": info.get("descriptionurl"),
                "original_url": info.get("url"),
                "original_width": width,
                "original_height": height,
                "original_short_side": min(width, height),
                "mime": mime,
                "mediawiki_sha1": sha1,
                "media_timestamp": timestamp,
                "license_short_name": license_short,
                "usage_terms": usage_terms,
                "license_url": license_url,
                "copyrighted": copyrighted,
                "restrictions": restrictions,
                "permission": permission,
                "artist_text": _plain_text(_metadata_value(metadata, "Artist")),
                "institution_text": _plain_text(_metadata_value(metadata, "Institution")),
                "credit_text": _plain_text(_metadata_value(metadata, "Credit")),
                "source_text": _plain_text(_metadata_value(metadata, "Source")),
                "object_name": _plain_text(_metadata_value(metadata, "ObjectName")),
                "image_description": _plain_text(_metadata_value(metadata, "ImageDescription")),
                "metadata_urls": _metadata_urls(
                    metadata, ("Institution", "Credit", "Source", "ImageDescription")
                ),
                "rights_candidate_status": (
                    "commons_open_rights_marker_candidate" if rights_candidate else "rights_review"
                ),
                "geometry_candidate_status": (
                    "reported_original_geometry_candidate"
                    if min(width, height) >= minimum_short
                    else "original_short_side_below_minimum"
                ),
                "decode_format_candidate_status": (
                    "supported_image_mime" if mime in supported_mimes else "unsupported_image_mime"
                ),
                "delivery_receipt_status": (
                    "complete_media_delivery_receipt_candidate"
                    if delivery_receipt_complete
                    else "incomplete_media_delivery_receipt"
                ),
                "raw_response_sha256": raw_hash,
            }
    return media


def build_candidate_manifest(
    rows: Sequence[Mapping[str, str]],
    entities: Mapping[str, Mapping[str, Any]],
    media: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for sequence, row in enumerate(rows, start=1):
        entity = dict(entities.get(row["item_qid"], {"entity_status": "missing"}))
        asset = dict(media.get(row["commons_filename"], {"media_status": "missing"}))
        creator_qids = entity.get("creator_qids", [])
        exact_creator = bool(creator_qids) and set(creator_qids) == {row["creator_qid"]}
        exact_discovery_claims = (
            exact_creator
            and "Q3305213" in entity.get("instance_qids", [])
            and {"Q296955", "Q12321255"}.issubset(entity.get("material_qids", []))
            and row["commons_filename"] in entity.get("commons_filenames", [])
        )
        combined_candidate = (
            entity.get("entity_status") == "resolved"
            and asset.get("media_status") == "resolved"
            and exact_discovery_claims
            and asset.get("rights_candidate_status") == "commons_open_rights_marker_candidate"
            and asset.get("geometry_candidate_status") == "reported_original_geometry_candidate"
            and asset.get("decode_format_candidate_status") == "supported_image_mime"
            and asset.get("delivery_receipt_status") == "complete_media_delivery_receipt_candidate"
        )
        output.append(
            {
                "schema_version": "painter-feature-generation-v1-federated-candidate/1.0",
                "census_id": config["census_id"],
                "candidate_sequence": sequence,
                **row,
                "entity": entity,
                "media": asset,
                "discovery_gate": (
                    "federated_metadata_candidate"
                    if combined_candidate
                    else "failed_or_unresolved_discovery_gate"
                ),
                "authority_status": "authoritative_holding_record_not_yet_verified",
                "content_status": "not_coded",
                "decode_status": "not_downloaded",
                "physical_work_identity_status": "not_reconciled",
                "active_study_admission": False,
            }
        )
    return output


def summarize_manifest(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    painters = sorted({str(row["painter_id"]) for row in rows})
    by_painter: dict[str, dict[str, int]] = {}
    for painter in painters:
        group = [row for row in rows if row["painter_id"] == painter]
        combined = [row for row in group if row["discovery_gate"] == "federated_metadata_candidate"]
        collection_counts: dict[str, int] = {}
        item_collections: dict[str, set[str]] = {}
        for row in group:
            item_collections.setdefault(str(row["item_qid"]), set()).update(
                str(value) for value in row["entity"].get("collection_qids", [])
            )
        for collections in item_collections.values():
            for collection in collections:
                collection_counts[collection] = collection_counts.get(collection, 0) + 1
        by_painter[painter] = {
            "item_image_rows": len(group),
            "distinct_items": len({row["item_qid"] for row in group}),
            "distinct_files": len({row["commons_filename"] for row in group}),
            "resolved_wikidata_entities": sum(
                row["entity"].get("entity_status") == "resolved" for row in group
            ),
            "resolved_commons_files": sum(
                row["media"].get("media_status") == "resolved" for row in group
            ),
            "open_media_candidates": sum(
                row["media"].get("rights_candidate_status")
                == "commons_open_rights_marker_candidate"
                for row in group
            ),
            "geometry_candidates": sum(
                row["media"].get("geometry_candidate_status")
                == "reported_original_geometry_candidate"
                for row in group
            ),
            "combined_discovery_candidates": sum(
                row["discovery_gate"] == "federated_metadata_candidate" for row in group
            ),
            "combined_discovery_distinct_items": len({row["item_qid"] for row in combined}),
            "rows_with_collection_qid": sum(
                bool(row["entity"].get("collection_qids")) for row in group
            ),
            "rows_with_inventory_number": sum(
                bool(row["entity"].get("inventory_numbers")) for row in group
            ),
            "rows_with_authority_url_candidate": sum(
                bool(
                    row["entity"].get("described_at_urls")
                    or row["entity"].get("reference_urls")
                    or row["media"].get("metadata_urls")
                )
                for row in group
            ),
            "distinct_collection_qids": len(collection_counts),
            "collection_qid_item_counts": dict(
                sorted(collection_counts.items(), key=lambda item: (-item[1], item[0]))
            ),
            "active_study_admissions": 0,
        }
    combined = [row for row in rows if row["discovery_gate"] == "federated_metadata_candidate"]
    return {
        "item_image_rows": len(rows),
        "distinct_items": len({row["item_qid"] for row in rows}),
        "distinct_files": len({row["commons_filename"] for row in rows}),
        "combined_discovery_candidates": sum(
            row["discovery_gate"] == "federated_metadata_candidate" for row in rows
        ),
        "combined_discovery_distinct_items": len({row["item_qid"] for row in combined}),
        "by_painter": by_painter,
        "active_study_admissions": 0,
    }


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    existing = path.read_bytes() if path.exists() else b""
    if existing and not existing.endswith(b"\n"):
        raise CensusError(f"refusing to append to torn JSONL file: {path}")
    rendered = (canonical_json(dict(row)) + "\n").encode("utf-8")
    _atomic_bytes(path, existing + rendered)


def _write_jsonl_atomic(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    body = "".join(canonical_json(dict(row)) + "\n" for row in rows).encode("utf-8")
    _atomic_bytes(path, body)


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    _atomic_bytes(path, (canonical_json(dict(value)) + "\n").encode("utf-8"))


def _repo_relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as exc:
        raise CensusError(f"path is outside the repository: {path}") from exc


def _repo_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise CensusError(f"{label} must be a non-empty repository-relative path")
    declared = Path(value)
    if declared.is_absolute() or ".." in declared.parts:
        raise CensusError(f"{label} escapes the repository: {value!r}")
    resolved = (root / declared).resolve()
    relative = _repo_relative(root, resolved)
    if relative in {"", "."}:
        raise CensusError(f"{label} cannot name the repository root")
    return resolved


def _declared_protocol_id(path: Path) -> str:
    match = re.search(r"^Protocol ID: `([^`]+)`$", path.read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        raise CensusError(f"protocol has no machine-readable Protocol ID: {path}")
    return match.group(1)


def _load_config(root: Path, path: Path) -> dict[str, Any]:
    path = path.resolve()
    _repo_relative(root, path)
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema_version") != (
        "painter-feature-generation-v1-federated-metadata-census-config/1.2"
    ):
        raise CensusError("unsupported census configuration")
    protocol = _repo_path(root, config["protocol_path"], "protocol_path")
    if not protocol.is_file():
        raise CensusError(f"missing protocol: {protocol}")
    declared_protocol_id = _declared_protocol_id(protocol)
    if config.get("protocol_id") != declared_protocol_id:
        raise CensusError(
            "configured protocol ID differs from the canonical protocol: "
            f"{config.get('protocol_id')!r} != {declared_protocol_id!r}"
        )
    source_frame = config.get("source_frame_contract", {})
    if source_frame.get("frame_class") != (
        "fixed_preexisting_exploratory_seed_followup_not_complete_r0_census"
    ):
        raise CensusError("unsupported or overstated source-frame class")
    evidence_path = _repo_path(
        root, source_frame["upstream_evidence_path"], "upstream_evidence_path"
    )
    if hash_file(evidence_path) != source_frame.get("upstream_evidence_sha256"):
        raise CensusError("upstream discovery evidence hash drift")
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence_contract = {
        "endpoint": evidence.get("endpoint"),
        "queried_at_utc": evidence.get("queried_at_utc"),
        "http_status": evidence.get("http_status"),
        "item_query": evidence.get("item_query"),
    }
    configured_contract = {
        "endpoint": source_frame.get("upstream_endpoint"),
        "queried_at_utc": source_frame.get("upstream_queried_at_utc"),
        "http_status": source_frame.get("upstream_http_status"),
        "item_query": source_frame.get("upstream_item_query"),
    }
    if evidence_contract != configured_contract:
        raise CensusError("upstream discovery contract differs from its frozen evidence")
    discovery_path = _repo_path(
        root, config.get("discovery_input", {}).get("path"), "discovery_input.path"
    )
    if not discovery_path.is_file():
        raise CensusError(f"missing discovery input: {discovery_path}")
    declared_paths = config.get("paths")
    if not isinstance(declared_paths, Mapping):
        raise CensusError("config lacks a path mapping")
    required_path_keys = {
        "planned_requests",
        "request_events",
        "candidate_manifest",
        "execution_receipt",
        "workspace",
    }
    if set(declared_paths) != required_path_keys:
        raise CensusError("config paths are not the exact expected path set")
    resolved_paths = [
        _repo_path(root, declared_paths[key], f"paths.{key}") for key in sorted(declared_paths)
    ]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise CensusError("config declares colliding output/workspace paths")
    return config


def prepare(root: Path, config_path: Path) -> dict[str, Any]:
    config = _load_config(root, config_path)
    discovery = config["discovery_input"]
    rows = load_discovery_rows(
        _repo_path(root, discovery["path"], "discovery_input.path"),
        str(discovery["sha256"]),
        config["painters"],
        int(discovery["expected_rows"]),
        int(discovery["expected_distinct_items"]),
        int(discovery["expected_distinct_files"]),
    )
    specs = build_request_specs(config, rows)
    intent_path = _repo_path(root, config["paths"]["planned_requests"], "paths.planned_requests")
    records = [spec.as_record(str(config["census_id"])) for spec in specs]
    _write_jsonl_atomic(intent_path, records)
    return {
        "census_id": config["census_id"],
        "discovery_rows": len(rows),
        "distinct_items": len({row["item_qid"] for row in rows}),
        "distinct_files": len({row["commons_filename"] for row in rows}),
        "planned_requests": len(specs),
        "wikidata_requests": sum(spec.stage == "wikidata_entities" for spec in specs),
        "commons_requests": sum(spec.stage == "commons_imageinfo" for spec in specs),
        "intent_path": str(config["paths"]["planned_requests"]),
        "intent_sha256": hash_file(intent_path),
    }


_METADATA_ONLY_SCOPE = {
    "metadata_requests": True,
    "image_downloads": False,
    "visual_coding": False,
    "active_study_admission": False,
    "feature_extraction": False,
    "generation": False,
}


def _required_frozen_paths(root: Path, config: Mapping[str, Any], config_path: Path) -> list[str]:
    declared = (
        (config["protocol_path"], "protocol_path"),
        (config["discovery_input"]["path"], "discovery_input.path"),
        (
            config["source_frame_contract"]["upstream_evidence_path"],
            "upstream_evidence_path",
        ),
        (config["paths"]["planned_requests"], "paths.planned_requests"),
    )
    fixed = {_repo_relative(root, config_path.resolve())}
    fixed.update(_repo_relative(root, _repo_path(root, value, label)) for value, label in declared)
    prior = config.get("prior_terminal_census")
    if prior is not None:
        if not isinstance(prior, Mapping):
            raise CensusError("prior_terminal_census must be an object")
        for key in (
            "config_path",
            "freeze_path",
            "review_path",
            "authorization_path",
            "event_ledger_path",
            "terminal_response_path",
        ):
            prior_path = _repo_path(root, prior.get(key), f"prior_terminal_census.{key}")
            expected_hash = prior.get(key.replace("_path", "_sha256"))
            if not isinstance(expected_hash, str) or not re.fullmatch(
                r"[0-9a-f]{64}", expected_hash
            ):
                raise CensusError(f"prior_terminal_census.{key} lacks a valid SHA-256")
            if hash_file(prior_path) != expected_hash:
                raise CensusError(f"prior_terminal_census.{key} hash mismatch")
            fixed.add(_repo_relative(root, prior_path))
    fixed.update(
        {
            ".gitignore",
            "src/latent_art_bench/__init__.py",
            "src/latent_art_bench/config.py",
            "src/latent_art_bench/io.py",
            "src/latent_art_bench/schemas.py",
            "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
            "src/latent_art_bench/painter_feature_generation_v1/federated_census.py",
            "scripts/collect_pfg_v1_federated_metadata.py",
            "tests/conftest.py",
            "tests/painter_feature_generation_v1/test_federated_census.py",
            "pyproject.toml",
            "uv.lock",
        }
    )
    return sorted(fixed)


def _expected_preexecution_outputs(root: Path, config: Mapping[str, Any]) -> list[dict[str, str]]:
    paths = config["paths"]
    response_bodies = Path(str(paths["workspace"])) / "response_bodies"
    declared = (
        (paths["request_events"], "paths.request_events"),
        (paths["candidate_manifest"], "paths.candidate_manifest"),
        (paths["execution_receipt"], "paths.execution_receipt"),
        (str(response_bodies), "paths.workspace.response_bodies"),
    )
    return [
        {"path": _repo_relative(root, _repo_path(root, value, label)), "state": "absent"}
        for value, label in declared
    ]


def _validate_seal(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    seal_path: Path,
    expected_sha256: str,
) -> dict[str, Any]:
    actual = hash_file(seal_path)
    if actual != expected_sha256:
        raise CensusError(
            f"authorization seal hash mismatch: expected {expected_sha256}, got {actual}"
        )
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("schema_version") != (
        "painter-feature-generation-v1-metadata-census-authorization/1.0"
    ):
        raise CensusError("unsupported metadata-census authorization schema")
    if seal.get("status") != "authorized_for_metadata_census_execution":
        raise CensusError("metadata census is not authorized")
    if seal.get("census_id") != config["census_id"]:
        raise CensusError("authorization seal names a different census")
    if seal.get("protocol_id") != config["protocol_id"]:
        raise CensusError("authorization seal names a different protocol")
    if seal.get("authorization_scope") != _METADATA_ONLY_SCOPE:
        raise CensusError("authorization seal scope is not exactly metadata-only")

    _repo_relative(root, seal_path.resolve())
    freeze_path = _repo_path(root, seal.get("freeze_path"), "authorization.freeze_path")
    if hash_file(freeze_path) != seal.get("freeze_sha256"):
        raise CensusError("metadata-census freeze hash mismatch")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("schema_version") != "painter-feature-generation-v1-metadata-census-freeze/1.0":
        raise CensusError("unsupported metadata-census freeze schema")
    if freeze.get("status") != "sealed_for_independent_metadata_census_review":
        raise CensusError("metadata-census freeze has not been sealed for review")
    if freeze.get("census_id") != config["census_id"]:
        raise CensusError("metadata-census freeze names a different census")
    if freeze.get("protocol_id") != config["protocol_id"]:
        raise CensusError("metadata-census freeze names a different protocol")
    if freeze.get("scope") != _METADATA_ONLY_SCOPE:
        raise CensusError("metadata-census freeze scope is not exactly metadata-only")
    entries = freeze.get("frozen_inputs")
    if not isinstance(entries, list) or not entries:
        raise CensusError("metadata-census freeze has no frozen inputs")
    if freeze.get("preexecution_outputs") != _expected_preexecution_outputs(root, config):
        raise CensusError("metadata-census freeze lacks the exact clean-output declaration")
    paths = [str(entry.get("path")) for entry in entries if isinstance(entry, Mapping)]
    required_paths = _required_frozen_paths(root, config, config_path)
    if (
        len(paths) != len(entries)
        or sorted(paths) != required_paths
        or len(set(paths)) != len(paths)
    ):
        raise CensusError("metadata-census freeze does not bind the exact required input set")
    for entry in entries:
        path = _repo_path(root, entry["path"], "frozen_inputs.path")
        observed = hash_file(path)
        if observed != entry.get("sha256"):
            raise CensusError(f"frozen input drift for {entry['path']}: {observed}")
    input_digest = _sha256_bytes(canonical_json(entries).encode("utf-8"))
    if freeze.get("frozen_input_set_sha256") != input_digest:
        raise CensusError("metadata-census frozen-input set digest mismatch")

    review_path = _repo_path(root, seal.get("review_path"), "authorization.review_path")
    if hash_file(review_path) != seal["review_sha256"]:
        raise CensusError("metadata-census review hash mismatch")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("schema_version") != "painter-feature-generation-v1-metadata-census-review/1.0":
        raise CensusError("unsupported metadata-census review schema")
    if review.get("decision") != "APPROVE_METADATA_CENSUS_ONLY":
        raise CensusError("independent review did not approve metadata-only execution")
    if (
        review.get("census_id") != config["census_id"]
        or review.get("protocol_id") != config["protocol_id"]
    ):
        raise CensusError("metadata-census review names a different census or protocol")
    if review.get("reviewed_freeze_path") != seal.get("freeze_path") or review.get(
        "reviewed_freeze_sha256"
    ) != seal.get("freeze_sha256"):
        raise CensusError("review does not bind the authorization freeze")
    if review.get("approved_scope") != _METADATA_ONLY_SCOPE:
        raise CensusError("independent review approved a different scope")
    if review.get("blocking_findings") != []:
        raise CensusError("metadata-census review retains blocking findings")
    if not str(review.get("independent_reviewer") or "").strip():
        raise CensusError("metadata-census review does not identify its reviewer")
    return {"seal": seal, "freeze": freeze, "review": review}


def _specs_from_intents(path: Path, census_id: str) -> list[RequestSpec]:
    rows = _read_jsonl(path)
    specs: list[RequestSpec] = []
    for row in rows:
        expected_keys = {
            "schema_version",
            "census_id",
            "request_id",
            "stage",
            "sequence",
            "method",
            "endpoint",
            "params",
            "members",
        }
        if set(row) != expected_keys:
            raise CensusError("request-intent row has an unexpected schema")
        if (
            row.get("schema_version") != "painter-feature-generation-v1-request-intent/1.0"
            or row.get("census_id") != census_id
            or row.get("method") != "GET"
        ):
            raise CensusError("request-intent census or method drift")
        if not (
            isinstance(row.get("request_id"), str)
            and row["request_id"]
            and row.get("stage") in _EXPECTED_SEMANTIC_OUTCOMES
            and isinstance(row.get("sequence"), int)
            and isinstance(row.get("endpoint"), str)
            and _is_http_url(row["endpoint"])
            and isinstance(row.get("params"), Mapping)
            and row["params"]
            and all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in row["params"].items()
            )
            and isinstance(row.get("members"), list)
            and row["members"]
            and all(isinstance(value, str) and value for value in row["members"])
        ):
            raise CensusError("request-intent row is not parser-complete")
        specs.append(
            RequestSpec(
                request_id=row["request_id"],
                stage=row["stage"],
                sequence=row["sequence"],
                endpoint=row["endpoint"],
                params=dict(row["params"]),
                members=tuple(row["members"]),
            )
        )
    if [spec.sequence for spec in specs] != list(range(1, len(specs) + 1)):
        raise CensusError("request-intent sequence is not exact and contiguous")
    if len({spec.request_id for spec in specs}) != len(specs):
        raise CensusError("duplicate request ID")
    return specs


def _validate_stage_payload(spec: RequestSpec, payload: Mapping[str, Any]) -> str:
    if "error" in payload or "warnings" in payload:
        raise CensusError(f"{spec.request_id} contains an API error or warning")
    if "curtimestamp" in spec.params and not _is_media_timestamp(payload.get("curtimestamp")):
        raise CensusError(f"{spec.request_id} lacks the requested provider timestamp")
    if "servedby" in spec.params and not str(payload.get("servedby") or "").strip():
        raise CensusError(f"{spec.request_id} lacks the requested provider host receipt")
    if spec.stage == "wikidata_entities":
        if "continue" in payload:
            raise CensusError(f"{spec.request_id} contains an unexpected continuation")
        if "redirects" in payload:
            raise CensusError(f"{spec.request_id} changed its redirect representation")
        if "servedby" in spec.params and payload.get("success") != 1:
            raise CensusError(f"{spec.request_id} lacks a Wikibase success marker")
        entities = payload.get("entities")
        if not isinstance(entities, Mapping):
            raise CensusError(f"{spec.request_id} lacks an entity mapping")
        if set(entities) != set(spec.members):
            raise CensusError(f"{spec.request_id} does not cover its exact entity members")
        for qid, entity in entities.items():
            if not isinstance(entity, Mapping):
                raise CensusError(f"{spec.request_id} entity {qid} is not an object")
            if entity.get("missing") is not None:
                if entity.get("id") != qid or entity.get("missing") is not True:
                    raise CensusError(f"{spec.request_id} missing-entity identity drift for {qid}")
                continue
            if entity.get("id") != qid:
                raise CensusError(f"{spec.request_id} entity {qid} redirected or changed identity")
            claims = entity.get("claims")
            if not isinstance(claims, Mapping):
                raise CensusError(f"{spec.request_id} entity {qid} lacks a claim mapping")
            if not isinstance(entity.get("labels"), Mapping) or not isinstance(
                entity.get("descriptions"), Mapping
            ):
                raise CensusError(f"{spec.request_id} entity {qid} lacks requested term mappings")
            for term_group in ("labels", "descriptions"):
                for language, term in entity[term_group].items():
                    term_language = term.get("language") if isinstance(term, Mapping) else None
                    fallback_language = (
                        term.get("for-language") if isinstance(term, Mapping) else None
                    )
                    if not (
                        isinstance(language, str)
                        and isinstance(term, Mapping)
                        and isinstance(term_language, str)
                        and isinstance(term.get("value"), str)
                        and (
                            term_language == language
                            or fallback_language == language
                        )
                        and (
                            fallback_language is None
                            or fallback_language == language
                        )
                    ):
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has malformed {term_group}"
                        )
            if not isinstance(entity.get("lastrevid"), int) or entity["lastrevid"] < 1:
                raise CensusError(f"{spec.request_id} entity {qid} lacks a revision receipt")
            if not _is_media_timestamp(entity.get("modified")):
                raise CensusError(f"{spec.request_id} entity {qid} lacks a modified timestamp")
            for property_id, claim_rows in claims.items():
                if not isinstance(property_id, str) or not isinstance(claim_rows, list):
                    raise CensusError(f"{spec.request_id} entity {qid} has malformed claims")
                for claim in claim_rows:
                    if not isinstance(claim, Mapping) or claim.get("rank") not in {
                        "preferred",
                        "normal",
                        "deprecated",
                    }:
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has a malformed ranked claim"
                        )
                    if not isinstance(claim.get("mainsnak"), Mapping):
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has a malformed claim snak"
                        )
                    snak = claim["mainsnak"]
                    if snak.get("snaktype") not in {"value", "somevalue", "novalue"}:
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has an invalid snak type"
                        )
                    if snak.get("snaktype") == "value" and not (
                        isinstance(snak.get("datavalue"), Mapping)
                        and "value" in snak["datavalue"]
                    ):
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has a malformed datavalue"
                        )
                    references = claim.get("references", [])
                    if not isinstance(references, list):
                        raise CensusError(
                            f"{spec.request_id} entity {qid} has malformed references"
                        )
                    for reference in references:
                        if not isinstance(reference, Mapping) or not isinstance(
                            reference.get("snaks"), Mapping
                        ):
                            raise CensusError(
                                f"{spec.request_id} entity {qid} has malformed reference snaks"
                            )
                        for reference_property_id, reference_snaks in reference["snaks"].items():
                            if not isinstance(reference_property_id, str) or not isinstance(
                                reference_snaks, list
                            ) or any(
                                not isinstance(reference_snak, Mapping)
                                for reference_snak in reference_snaks
                            ):
                                raise CensusError(
                                    f"{spec.request_id} entity {qid} has malformed reference snaks"
                                )
                            for reference_snak in reference_snaks:
                                if reference_property_id == "P854":
                                    _p854_reference_url(reference_snak)
                                elif reference_snak.get("snaktype") == "value" and not (
                                    isinstance(reference_snak.get("datavalue"), Mapping)
                                    and "value" in reference_snak["datavalue"]
                                ):
                                    raise CensusError(
                                        f"{spec.request_id} entity {qid} has malformed "
                                        "reference value"
                                    )
        return "complete_wikidata_entity_batch"
    if spec.stage == "commons_imageinfo":
        if payload.get("batchcomplete") is not True or "continue" in payload:
            raise CensusError(f"{spec.request_id} is not a complete one-response batch")
        query = payload.get("query")
        if not isinstance(query, Mapping) or not isinstance(query.get("pages"), list):
            raise CensusError(f"{spec.request_id} lacks a Commons page list")
        if "redirects" in query or "normalized" in query:
            raise CensusError(f"{spec.request_id} contains a redirect or title normalization")
        pages = query["pages"]
        page_titles = {
            str(page.get("title"))
            for page in pages
            if isinstance(page, Mapping) and page.get("title")
        }
        if len(page_titles) != len(pages):
            raise CensusError(f"{spec.request_id} has missing or duplicate page titles")
        if set(spec.members) != page_titles:
            raise CensusError(f"{spec.request_id} does not explicitly cover every requested file")
        for page in pages:
            assert isinstance(page, Mapping)
            title = str(page["title"])
            if page.get("missing") is not None:
                if page.get("missing") is not True or "imageinfo" in page:
                    raise CensusError(f"{spec.request_id} page {title} has malformed missing state")
                continue
            info_rows = page.get("imageinfo")
            if not isinstance(info_rows, list) or len(info_rows) != 1:
                raise CensusError(
                    f"{spec.request_id} page {title} lacks exactly one image revision"
                )
            info = info_rows[0]
            if not isinstance(info, Mapping):
                raise CensusError(f"{spec.request_id} page {title} has malformed imageinfo")
            if not (
                _is_http_url(info.get("url"))
                and _is_http_url(info.get("descriptionurl"))
                and isinstance(info.get("width"), int)
                and info["width"] > 0
                and isinstance(info.get("height"), int)
                and info["height"] > 0
                and isinstance(info.get("mime"), str)
                and bool(info["mime"])
                and isinstance(info.get("sha1"), str)
                and bool(re.fullmatch(r"(?:[0-9A-Fa-f]{40}|[0-9A-Za-z]{31})", info["sha1"]))
                and _is_media_timestamp(info.get("timestamp"))
                and isinstance(info.get("canonicaltitle"), str)
                and info["canonicaltitle"] == title
                and isinstance(info.get("extmetadata"), Mapping)
            ):
                raise CensusError(f"{spec.request_id} page {title} lacks parser-complete imageinfo")
            for field, metadata in info["extmetadata"].items():
                if not (
                    isinstance(field, str)
                    and isinstance(metadata, Mapping)
                    and isinstance(metadata.get("value"), str)
                ):
                    raise CensusError(
                        f"{spec.request_id} page {title} has malformed extended metadata"
                    )
        return "complete_commons_current_revision_batch"
    raise CensusError(f"unsupported request stage: {spec.stage}")


def _load_event_ledger(path: Path, census_id: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    previous = "0" * 64
    for sequence, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            raise CensusError(f"event ledger contains a blank line at {sequence}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CensusError(f"event ledger line {sequence} is invalid JSON") from exc
        if not isinstance(row, Mapping):
            raise CensusError(f"event ledger line {sequence} is not an object")
        if row.get("schema_version") != _EVENT_SCHEMA:
            raise CensusError(f"event ledger line {sequence} has the wrong schema")
        if row.get("census_id") != census_id:
            raise CensusError(f"event ledger line {sequence} names another census")
        if row.get("sequence") != sequence or row.get("previous_event_sha256") != previous:
            raise CensusError(f"event ledger chain breaks at line {sequence}")
        unhashed = dict(row)
        observed = str(unhashed.pop("event_sha256", ""))
        expected = _sha256_bytes(canonical_json(unhashed).encode("utf-8"))
        if observed != expected:
            raise CensusError(f"event ledger hash mismatch at line {sequence}")
        previous = observed
        events.append(dict(row))
    return events


def _append_event(
    path: Path,
    census_id: str,
    events: list[dict[str, Any]],
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    row = {
        "schema_version": _EVENT_SCHEMA,
        "census_id": census_id,
        "sequence": len(events) + 1,
        "previous_event_sha256": events[-1]["event_sha256"] if events else "0" * 64,
        **fields,
    }
    row["event_sha256"] = _sha256_bytes(canonical_json(row).encode("utf-8"))
    _append_jsonl(path, row)
    events.append(row)
    return row


def _encoded_request_url(spec: RequestSpec) -> str:
    return str(httpx.Request("GET", spec.endpoint, params=spec.params).url)


def _execution_binding(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    seal_path: Path,
    expected_seal_sha256: str,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    seal = authorization["seal"]
    freeze = authorization["freeze"]
    review = authorization["review"]
    protocol_path = _repo_path(root, config["protocol_path"], "protocol_path")
    intent_path = _repo_path(root, config["paths"]["planned_requests"], "paths.planned_requests")
    return {
        "authorization_seal_path": _repo_relative(root, seal_path.resolve()),
        "authorization_seal_sha256": expected_seal_sha256,
        "freeze_path": str(seal["freeze_path"]),
        "freeze_sha256": str(seal["freeze_sha256"]),
        "review_path": str(seal["review_path"]),
        "review_sha256": str(seal["review_sha256"]),
        "config_path": _repo_relative(root, config_path.resolve()),
        "config_sha256": hash_file(config_path),
        "protocol_path": _repo_relative(root, protocol_path),
        "protocol_sha256": hash_file(protocol_path),
        "request_intents_path": _repo_relative(root, intent_path),
        "request_intents_sha256": hash_file(intent_path),
        "frozen_input_set_sha256": str(freeze["frozen_input_set_sha256"]),
        "authorization_scope": _METADATA_ONLY_SCOPE,
        "preexecution_outputs": freeze["preexecution_outputs"],
        "workspace_path": str(config["paths"]["workspace"]),
        "output_paths": {
            key: str(config["paths"][key])
            for key in ("request_events", "candidate_manifest", "execution_receipt")
        },
        "review_decision": str(review["decision"]),
    }


def _ensure_execution_genesis(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    seal_path: Path,
    expected_seal_sha256: str,
    authorization: Mapping[str, Any],
    event_path: Path,
) -> list[dict[str, Any]]:
    events = _load_event_ledger(event_path, str(config["census_id"]))
    binding = _execution_binding(
        root,
        config,
        config_path,
        seal_path,
        expected_seal_sha256,
        authorization,
    )
    if not events:
        for row in authorization["freeze"]["preexecution_outputs"]:
            path = _repo_path(root, row["path"], "preexecution_outputs.path")
            if path.exists():
                raise CensusError(f"pre-execution output was not clean: {row['path']}")
        return [
            _append_event(
                event_path,
                str(config["census_id"]),
                [],
                {
                    "event_type": "execution_started",
                    "started_at_utc": _utc_now(),
                    **binding,
                },
            )
        ]
    genesis = events[0]
    if genesis.get("event_type") != "execution_started":
        raise CensusError("event ledger does not begin with an authorization-bound genesis")
    observed = {key: genesis.get(key) for key in binding}
    if observed != binding:
        raise CensusError("event-ledger genesis differs from the current frozen authorization")
    if sum(row.get("event_type") == "execution_started" for row in events) != 1:
        raise CensusError("event ledger contains multiple execution genesis events")
    if not _is_media_timestamp(genesis.get("started_at_utc")):
        raise CensusError("event-ledger genesis lacks a valid start timestamp")
    return events


def _response_cas_path(workspace: Path, event: Mapping[str, Any]) -> Path:
    relative = str(event.get("response_body_path") or "")
    digest = str(event.get("response_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise CensusError("response event lacks a valid SHA-256 receipt")
    expected = Path("response_bodies") / digest[:2] / f"{digest}.response"
    if Path(relative) != expected:
        raise CensusError("response event does not name its canonical CAS location")
    path = (workspace / expected).resolve()
    try:
        path.relative_to(workspace.resolve())
    except ValueError as exc:
        raise CensusError("response CAS path escapes its workspace") from exc
    return path


def _validate_terminal_event(row: Mapping[str, Any], spec: RequestSpec, workspace: Path) -> None:
    outcome = str(row.get("outcome") or "")
    status = row.get("status_code")
    retryable = row.get("retryable")
    response_outcomes = {
        "success",
        "retryable_api_error",
        "terminal_api_error",
        "terminal_malformed_json_200",
        "terminal_stage_schema_failure",
        "retryable_http_error",
        "terminal_http_error",
        "terminal_retry_after_new_census_required",
    }
    if outcome in {"transport_error", "terminal_interrupted_new_census_required"}:
        expected_retryable = outcome == "transport_error"
        if not (
            retryable is expected_retryable
            and status is None
            and row.get("final_url") is None
            and row.get("response_bytes") is None
            and row.get("response_sha256") is None
            and row.get("response_body_path") is None
            and row.get("semantic_outcome") is None
            and row.get("api_error_code") is None
            and isinstance(row.get("error"), str)
            and bool(row["error"])
        ):
            raise CensusError(f"inconsistent {outcome} event for {spec.request_id}")
        return
    if outcome not in response_outcomes:
        raise CensusError(f"unknown terminal outcome for {spec.request_id}: {outcome!r}")
    if not isinstance(status, int) or not isinstance(row.get("response_bytes"), int):
        raise CensusError(f"response event lacks status/size for {spec.request_id}")
    headers = row.get("response_headers")
    history = row.get("redirect_history")
    if not isinstance(headers, Mapping) or not isinstance(history, list):
        raise CensusError(f"response event lacks header/redirect receipts for {spec.request_id}")
    if history or row.get("final_url") != _encoded_request_url(spec):
        raise CensusError(f"response event redirected or changed origin for {spec.request_id}")
    path = _response_cas_path(workspace, row)
    if not path.is_file() or hash_file(path) != row.get("response_sha256"):
        raise CensusError(f"response CAS is missing or corrupt for {spec.request_id}")
    if path.stat().st_size != row.get("response_bytes"):
        raise CensusError(f"response byte count drift for {spec.request_id}")
    retry_after_header = headers.get("retry-after")
    retry_after_receipt = row.get("retry_after_seconds")
    if retry_after_receipt is not None and not _is_finite_nonnegative_number(
        retry_after_receipt
    ):
        raise CensusError(f"invalid Retry-After receipt for {spec.request_id}")
    if retry_after_header is None and retry_after_receipt is not None:
        raise CensusError(f"Retry-After receipt lacks its response header for {spec.request_id}")
    if (
        retry_after_header is not None
        and outcome != "terminal_retry_after_new_census_required"
        and retry_after_receipt is None
    ):
        raise CensusError(
            f"Retry-After response header lacks its parsed receipt for {spec.request_id}"
        )
    if (
        retry_after_header is not None
        and retry_after_receipt is not None
        and re.fullmatch(r"[0-9]+", str(retry_after_header).strip())
        and float(int(str(retry_after_header).strip())) != float(retry_after_receipt)
    ):
        raise CensusError(f"Retry-After header and receipt disagree for {spec.request_id}")
    if (
        retry_after_header is not None
        and retry_after_receipt is not None
        and not re.fullmatch(r"[0-9]+", str(retry_after_header).strip())
    ):
        try:
            retry_at = email.utils.parsedate_to_datetime(str(retry_after_header).strip())
        except (TypeError, ValueError) as exc:
            raise CensusError(
                f"Retry-After header and receipt disagree for {spec.request_id}"
            ) from exc
        finished_at = _parse_media_timestamp(row.get("finished_at_utc"))
        if retry_at is None or retry_at.tzinfo is None or finished_at is None:
            raise CensusError(f"Retry-After header and receipt disagree for {spec.request_id}")
        expected_at_finish = max(
            0.0,
            (retry_at.astimezone(timezone.utc) - finished_at).total_seconds(),
        )
        receipt = float(retry_after_receipt)
        # Parsing happens immediately before the terminal event is persisted.  The
        # receipt can therefore exceed the remaining delay at finish by a small
        # amount, but it must never be shorter or differ by an implausible interval.
        if receipt < expected_at_finish or receipt - expected_at_finish > 5.0:
            raise CensusError(f"Retry-After header and receipt disagree for {spec.request_id}")
    if outcome == "success":
        if not (
            status == 200
            and retryable is False
            and row.get("semantic_outcome") == _EXPECTED_SEMANTIC_OUTCOMES[spec.stage]
            and row.get("api_error_code") is None
            and row.get("error") is None
            and row.get("retry_after_seconds") is None
        ):
            raise CensusError(f"inconsistent success event for {spec.request_id}")
    elif outcome in {"retryable_api_error", "terminal_api_error"}:
        if not (
            status == 200
            and isinstance(row.get("api_error_code"), str)
            and bool(row["api_error_code"])
            and retryable is (outcome == "retryable_api_error")
            and row.get("semantic_outcome") is None
        ):
            raise CensusError(f"inconsistent API-error event for {spec.request_id}")
    elif outcome in {"retryable_http_error", "terminal_http_error"}:
        if not (
            status != 200
            and retryable is (outcome == "retryable_http_error")
            and row.get("semantic_outcome") is None
        ):
            raise CensusError(f"inconsistent HTTP-error event for {spec.request_id}")
    elif outcome == "terminal_retry_after_new_census_required":
        if not (
            retryable is False
            and row.get("semantic_outcome") is None
            and isinstance(row.get("error"), str)
            and bool(row["error"])
        ):
            raise CensusError(f"inconsistent Retry-After event for {spec.request_id}")
    elif not (status == 200 and retryable is False and row.get("semantic_outcome") is None):
        raise CensusError(f"inconsistent terminal response event for {spec.request_id}")


def _attempt_maps(
    events: Sequence[Mapping[str, Any]], specs: Mapping[str, RequestSpec], workspace: Path
) -> tuple[dict[tuple[str, int], Mapping[str, Any]], dict[tuple[str, int], Mapping[str, Any]]]:
    if not events or events[0].get("event_type") != "execution_started":
        raise CensusError("request events lack an authorization-bound execution genesis")
    starts: dict[tuple[str, int], Mapping[str, Any]] = {}
    finishes: dict[tuple[str, int], Mapping[str, Any]] = {}
    successful: set[str] = set()
    blocked: set[str] = set()
    pending: tuple[str, int] | None = None
    previous_event_time = _parse_media_timestamp(events[0].get("started_at_utc"))
    if previous_event_time is None:
        raise CensusError("event-ledger genesis lacks a valid start timestamp")
    ordered_specs = sorted(specs.values(), key=lambda item: item.sequence)
    for row in events[1:]:
        request_id = str(row.get("request_id") or "")
        if request_id not in specs or row.get("stage") != specs[request_id].stage:
            raise CensusError(
                f"event ledger contains an unknown or stage-drifted request: {request_id}"
            )
        attempt = int(row.get("attempt") or 0)
        if attempt < 1:
            raise CensusError(f"event ledger has an invalid attempt for {request_id}")
        key = (request_id, attempt)
        event_type = row.get("event_type")
        if event_type == "attempt_started":
            event_time = _parse_media_timestamp(row.get("started_at_utc"))
            expected = next(
                (spec for spec in ordered_specs if spec.request_id not in successful), None
            )
            if pending is not None or key in starts or key in finishes:
                raise CensusError(f"duplicate or out-of-order attempt start: {key}")
            if expected is None or request_id != expected.request_id or request_id in blocked:
                raise CensusError(f"attempt start violates frozen request order: {key}")
            prior_attempts = sum(existing[0] == request_id for existing in starts)
            if attempt != prior_attempts + 1:
                raise CensusError(f"attempt numbers are not contiguous for {request_id}")
            if not (
                row.get("method") == "GET"
                and row.get("intent_sequence") == specs[request_id].sequence
                and row.get("encoded_request_url") == _encoded_request_url(specs[request_id])
                and event_time is not None
            ):
                raise CensusError(f"attempt start differs from frozen intent: {key}")
            if event_time < previous_event_time:
                raise CensusError(f"attempt start timestamp precedes the event ledger: {key}")
            starts[key] = row
            pending = key
            previous_event_time = event_time
        elif event_type == "attempt_finished":
            if key not in starts or key in finishes or pending != key:
                raise CensusError(f"attempt finish lacks one preceding start: {key}")
            event_time = _parse_media_timestamp(row.get("finished_at_utc"))
            if event_time is None:
                raise CensusError(f"attempt finish lacks a timestamp: {key}")
            if event_time < previous_event_time:
                raise CensusError(f"attempt finish timestamp precedes its start: {key}")
            _validate_terminal_event(row, specs[request_id], workspace)
            finishes[key] = row
            pending = None
            previous_event_time = event_time
            if row.get("outcome") == "success":
                successful.add(request_id)
            elif row.get("retryable") is False:
                blocked.add(request_id)
        else:
            raise CensusError(f"unknown event type in ledger: {event_type!r}")
    return starts, finishes


def _store_response_body(workspace: Path, body: bytes) -> tuple[Path, str]:
    digest = _sha256_bytes(body)
    path = workspace / "response_bodies" / digest[:2] / f"{digest}.response"
    if path.exists():
        if hash_file(path) != digest:
            raise CensusError(f"response CAS corruption at {path}")
    else:
        _atomic_bytes(path, body)
    return path, digest


def _success_response_path(
    workspace: Path, event: Mapping[str, Any]
) -> tuple[Path, dict[str, Any]]:
    path = _response_cas_path(workspace, event)
    if not path.is_file() or hash_file(path) != event.get("response_sha256"):
        raise CensusError(f"successful response CAS is missing or corrupt: {path}")
    try:
        payload = json.loads(path.read_bytes())
    except json.JSONDecodeError as exc:
        raise CensusError(f"successful response CAS is not JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise CensusError(f"successful response CAS is not an object: {path}")
    return path, dict(payload)


@contextlib.contextmanager
def _exclusive_execution_lock(workspace: Path) -> Iterable[None]:
    workspace.mkdir(parents=True, exist_ok=True)
    lock_path = workspace / ".execution.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CensusError("another metadata-census execution holds the exclusive lock") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _retry_after_seconds(value: str, now: datetime | None = None) -> float:
    rendered = value.strip()
    if re.fullmatch(r"[0-9]+", rendered):
        try:
            seconds = float(int(rendered))
        except OverflowError as exc:
            raise CensusError(f"invalid Retry-After value: {value!r}") from exc
    else:
        try:
            parsed = email.utils.parsedate_to_datetime(rendered)
        except (TypeError, ValueError, OverflowError) as exc:
            raise CensusError(f"invalid Retry-After value: {value!r}") from exc
        if parsed is None or parsed.tzinfo is None:
            raise CensusError(f"invalid Retry-After value: {value!r}")
        reference = now or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            raise CensusError("Retry-After reference time must be timezone-aware")
        seconds = (
            parsed.astimezone(timezone.utc) - reference.astimezone(timezone.utc)
        ).total_seconds()
    return max(0.0, seconds)


def _is_finite_nonnegative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _remaining_retry_delay_seconds(
    terminal: Mapping[str, Any],
    *,
    retry_backoff_base: float,
    minimum_interval: float,
    maximum_wait: float,
    now: datetime | None = None,
) -> float:
    attempt = terminal.get("attempt")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
        raise CensusError("retryable terminal event has an invalid attempt number")
    retry_after = terminal.get("retry_after_seconds")
    if retry_after is not None and not _is_finite_nonnegative_number(retry_after):
        raise CensusError("retryable terminal event has an invalid Retry-After receipt")
    retry_delay = max(
        float(retry_after or 0.0), retry_backoff_base * float(2 ** (attempt - 1))
    )
    if retry_delay > maximum_wait:
        raise CensusError(
            "persisted retry backoff exceeds the frozen wait ceiling; start a newly "
            "authorized census with a new census ID"
        )
    finished_at = terminal.get("finished_at_utc")
    if not isinstance(finished_at, str):
        raise CensusError("retryable terminal event lacks a finish timestamp")
    try:
        finished = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CensusError("retryable terminal event has an invalid finish timestamp") from exc
    if finished.tzinfo is None:
        raise CensusError("retryable terminal event finish timestamp is not timezone-aware")
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        raise CensusError("retry-delay reference time must be timezone-aware")
    elapsed = max(
        0.0,
        (
            reference.astimezone(timezone.utc) - finished.astimezone(timezone.utc)
        ).total_seconds(),
    )
    return max(0.0, max(retry_delay, minimum_interval) - elapsed)


def _execute_specs(
    root: Path,
    config: Mapping[str, Any],
    specs: Sequence[RequestSpec],
    workspace: Path,
    events: list[dict[str, Any]],
    transport: httpx.BaseTransport | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    event_path = _repo_path(root, config["paths"]["request_events"], "paths.request_events")
    request = config["request_contract"]
    timeout = float(request["timeout_seconds"])
    interval = float(request["minimum_interval_seconds"])
    retry_backoff_base = float(request["retry_backoff_base_seconds"])
    maximum_attempts = int(request["maximum_attempts"])
    maximum_wait = float(request["maximum_retry_wait_seconds"])
    retryable_http = {int(value) for value in request["retryable_http_status_codes"]}
    retryable_api = {str(value).casefold() for value in request["retryable_api_error_codes"]}
    receipts: list[dict[str, Any]] = []
    response_paths: dict[str, Path] = {}
    last_access = 0.0
    if events != _load_event_ledger(event_path, str(config["census_id"])):
        raise CensusError("event ledger changed after authorization genesis validation")
    spec_by_id = {spec.request_id: spec for spec in specs}
    starts, finishes = _attempt_maps(events, spec_by_id, workspace)
    for key, start in list(starts.items()):
        if key not in finishes:
            _append_event(
                event_path,
                str(config["census_id"]),
                events,
                {
                    "event_type": "attempt_finished",
                    "request_id": key[0],
                    "stage": start["stage"],
                    "attempt": key[1],
                    "finished_at_utc": _utc_now(),
                    "outcome": "terminal_interrupted_new_census_required",
                    "semantic_outcome": None,
                    "retryable": False,
                    "status_code": None,
                    "final_url": None,
                    "redirect_history": [],
                    "response_headers": {},
                    "response_bytes": None,
                    "response_sha256": None,
                    "response_body_path": None,
                    "api_error_code": None,
                    "error": (
                        "A start event existed without a terminal event; its network outcome is "
                        "unknowable. Start a newly authorized census with a new census ID."
                    ),
                },
            )
    starts, finishes = _attempt_maps(events, spec_by_id, workspace)
    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        transport=transport,
        headers={
            "User-Agent": str(request["user_agent"]),
            "Api-User-Agent": str(request["user_agent"]),
            "Accept": "application/json",
        },
    ) as client:
        for spec in specs:
            successful = [
                row
                for (request_id, _), row in finishes.items()
                if request_id == spec.request_id and row.get("outcome") == "success"
            ]
            if len(successful) > 1:
                raise CensusError(f"multiple successful terminal events for {spec.request_id}")
            if successful:
                path, payload = _success_response_path(workspace, successful[0])
                _validate_stage_payload(spec, payload)
                response_paths[spec.request_id] = path
                receipts.append(
                    {
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "status": "verified_success_event",
                        "attempt": successful[0]["attempt"],
                        "response_sha256": successful[0]["response_sha256"],
                        "response_bytes": successful[0]["response_bytes"],
                        "response_body_path": successful[0]["response_body_path"],
                    }
                )
                continue
            prior_finishes = [
                row for (request_id, _), row in finishes.items() if request_id == spec.request_id
            ]
            if any(row.get("retryable") is False for row in prior_finishes):
                raise CensusError(
                    f"request {spec.request_id} already has a non-retryable terminal outcome"
                )
            attempts_used = sum(request_id == spec.request_id for request_id, _ in starts)
            terminal: dict[str, Any] | None = None
            if attempts_used < maximum_attempts and prior_finishes:
                latest_finish = max(prior_finishes, key=lambda row: int(row["attempt"]))
                remaining_delay = _remaining_retry_delay_seconds(
                    latest_finish,
                    retry_backoff_base=retry_backoff_base,
                    minimum_interval=interval,
                    maximum_wait=maximum_wait,
                )
                if remaining_delay > 0:
                    time.sleep(remaining_delay)
            while attempts_used < maximum_attempts:
                attempt = attempts_used + 1
                delay = interval - (time.monotonic() - last_access)
                if delay > 0:
                    time.sleep(delay)
                prepared = client.build_request("GET", spec.endpoint, params=spec.params)
                if str(prepared.url) != _encoded_request_url(spec):
                    raise CensusError(f"HTTP client encoded {spec.request_id} unexpectedly")
                _append_event(
                    event_path,
                    str(config["census_id"]),
                    events,
                    {
                        "event_type": "attempt_started",
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "attempt": attempt,
                        "started_at_utc": _utc_now(),
                        "method": "GET",
                        "encoded_request_url": str(prepared.url),
                        "intent_sequence": spec.sequence,
                    },
                )
                attempts_used += 1
                response: httpx.Response | None = None
                error: str | None = None
                try:
                    response = client.send(prepared)
                    body = response.content
                except httpx.HTTPError as exc:
                    body = b""
                    error = f"{type(exc).__name__}: {exc}"
                last_access = time.monotonic()
                response_path: Path | None = None
                response_digest: str | None = None
                payload: Mapping[str, Any] | None = None
                if response is not None:
                    response_path, response_digest = _store_response_body(workspace, body)
                outcome = "transport_error"
                retryable = response is None
                api_error_code: str | None = None
                semantic_outcome: str | None = None
                if response is not None and response.status_code == 200:
                    try:
                        parsed = json.loads(body)
                    except json.JSONDecodeError:
                        parsed = None
                    if not isinstance(parsed, Mapping):
                        outcome = "terminal_malformed_json_200"
                        retryable = False
                    elif "error" in parsed:
                        api_error = parsed.get("error")
                        api_error_code = (
                            str(api_error.get("code") or "").casefold()
                            if isinstance(api_error, Mapping)
                            else "unknown"
                        )
                        retryable = api_error_code in retryable_api
                        outcome = "retryable_api_error" if retryable else "terminal_api_error"
                    else:
                        payload = parsed
                        try:
                            semantic_outcome = _validate_stage_payload(spec, payload)
                        except CensusError as exc:
                            error = str(exc)
                            outcome = "terminal_stage_schema_failure"
                            retryable = False
                        else:
                            outcome = "success"
                            retryable = False
                elif response is not None:
                    retryable = response.status_code in retryable_http
                    outcome = "retryable_http_error" if retryable else "terminal_http_error"
                retry_after_seconds: float | None = None
                if response is not None and retryable and "retry-after" in response.headers:
                    try:
                        retry_after_seconds = _retry_after_seconds(response.headers["retry-after"])
                    except (TypeError, ValueError, CensusError) as exc:
                        outcome = "terminal_retry_after_new_census_required"
                        retryable = False
                        error = str(exc)
                    else:
                        if retry_after_seconds > maximum_wait:
                            outcome = "terminal_retry_after_new_census_required"
                            retryable = False
                            error = (
                                f"Retry-After requires {retry_after_seconds:.3f}s, exceeding the "
                                f"frozen {maximum_wait:.3f}s wait ceiling; start a newly "
                                "authorized census with a new census ID."
                            )
                selected_headers = {}
                if response is not None:
                    for key in (
                        "age",
                        "cache-control",
                        "content-encoding",
                        "content-length",
                        "content-type",
                        "date",
                        "etag",
                        "last-modified",
                        "retry-after",
                        "server",
                        "server-timing",
                        "x-cache",
                        "x-cache-status",
                        "x-database-lag",
                        "x-request-id",
                    ):
                        if key in response.headers:
                            selected_headers[key] = response.headers[key]
                terminal = _append_event(
                    event_path,
                    str(config["census_id"]),
                    events,
                    {
                        "event_type": "attempt_finished",
                        "request_id": spec.request_id,
                        "stage": spec.stage,
                        "attempt": attempt,
                        "finished_at_utc": _utc_now(),
                        "outcome": outcome,
                        "semantic_outcome": semantic_outcome,
                        "retryable": retryable,
                        "status_code": response.status_code if response is not None else None,
                        "final_url": str(response.url) if response is not None else None,
                        "redirect_history": (
                            [
                                {"status_code": item.status_code, "url": str(item.url)}
                                for item in response.history
                            ]
                            if response is not None
                            else []
                        ),
                        "response_headers": selected_headers,
                        "response_bytes": len(body) if response is not None else None,
                        "response_sha256": response_digest,
                        "response_body_path": (
                            str(response_path.relative_to(workspace))
                            if response_path is not None
                            else None
                        ),
                        "api_error_code": api_error_code,
                        "retry_after_seconds": retry_after_seconds,
                        "error": error,
                    },
                )
                starts, finishes = _attempt_maps(events, spec_by_id, workspace)
                if outcome == "success":
                    assert response_path is not None
                    response_paths[spec.request_id] = response_path
                    break
                if not retryable:
                    raise CensusError(
                        f"request {spec.request_id} ended with non-retryable {outcome}"
                    )
                if attempts_used < maximum_attempts:
                    exponential = retry_backoff_base * float(2 ** (attempt - 1))
                    delay_seconds = max(retry_after_seconds or 0.0, exponential)
                    if delay_seconds > maximum_wait:
                        raise CensusError(
                            f"retry backoff for {spec.request_id} exceeds the frozen wait ceiling; "
                            "start a newly authorized census with a new census ID"
                        )
                    time.sleep(delay_seconds)
            if terminal is None or terminal.get("outcome") != "success":
                raise CensusError(
                    f"request {spec.request_id} failed after {maximum_attempts} lifetime attempts; "
                    "start a newly authorized census with a new census ID"
                )
            receipts.append(
                {
                    "request_id": spec.request_id,
                    "stage": spec.stage,
                    "status": "verified_success_event",
                    "attempt": terminal["attempt"],
                    "response_sha256": terminal["response_sha256"],
                    "response_bytes": terminal["response_bytes"],
                    "response_body_path": terminal["response_body_path"],
                }
            )
    return receipts, response_paths


def _verified_success_inventory(
    specs: Sequence[RequestSpec],
    events: Sequence[Mapping[str, Any]],
    workspace: Path,
) -> tuple[list[dict[str, Any]], dict[str, Path], list[str]]:
    spec_by_id = {spec.request_id: spec for spec in specs}
    starts, finishes = _attempt_maps(events, spec_by_id, workspace)
    if set(starts) != set(finishes):
        raise CensusError("completion state contains a dangling request attempt")
    inventory: list[dict[str, Any]] = []
    response_paths: dict[str, Path] = {}
    provider_times: list[str] = []
    for spec in specs:
        successes = [
            event
            for (request_id, _), event in finishes.items()
            if request_id == spec.request_id and event.get("outcome") == "success"
        ]
        if len(successes) != 1:
            raise CensusError(f"completion state lacks one success for {spec.request_id}")
        event = successes[0]
        path, payload = _success_response_path(workspace, event)
        _validate_stage_payload(spec, payload)
        provider_times.append(str(payload["curtimestamp"]))
        response_paths[spec.request_id] = path
        inventory.append(
            {
                "request_id": spec.request_id,
                "stage": spec.stage,
                "status": "verified_success_event",
                "attempt": event["attempt"],
                "response_sha256": event["response_sha256"],
                "response_bytes": event["response_bytes"],
                "response_body_path": event["response_body_path"],
            }
        )
    return inventory, response_paths, provider_times


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            raise CensusError(f"blank JSONL line at {path}:{number}")
        value = json.loads(line)
        if not isinstance(value, Mapping):
            raise CensusError(f"non-object JSONL row at {path}:{number}")
        rows.append(dict(value))
    return rows


def _completion_receipt(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    seal_path: Path,
    expected_seal_sha256: str,
    authorization: Mapping[str, Any],
    completed_at_utc: str,
    intent_path: Path,
    event_path: Path,
    events: Sequence[Mapping[str, Any]],
    inventory: Sequence[Mapping[str, Any]],
    manifest_path: Path,
    manifest: Sequence[Mapping[str, Any]],
    provider_times: Sequence[str],
) -> dict[str, Any]:
    seal = authorization["seal"]
    if not provider_times:
        raise CensusError("completion receipt lacks provider observation times")
    return {
        "schema_version": "painter-feature-generation-v1-federated-metadata-execution/1.2",
        "census_id": config["census_id"],
        "status": "fixed_seed_metadata_audit_complete_not_full_r0_source_census",
        "completed_at_utc": completed_at_utc,
        "protocol_id": config["protocol_id"],
        "source_frame_class": config["source_frame_contract"]["frame_class"],
        "authorization_seal_path": _repo_relative(root, seal_path.resolve()),
        "authorization_seal_sha256": expected_seal_sha256,
        "authorization_freeze_path": str(seal["freeze_path"]),
        "authorization_freeze_sha256": str(seal["freeze_sha256"]),
        "authorization_review_path": str(seal["review_path"]),
        "authorization_review_sha256": str(seal["review_sha256"]),
        "config_path": _repo_relative(root, config_path.resolve()),
        "config_sha256": hash_file(config_path),
        "request_intents_path": str(config["paths"]["planned_requests"]),
        "request_intents_sha256": hash_file(intent_path),
        "request_event_ledger_path": str(config["paths"]["request_events"]),
        "request_event_ledger_sha256": hash_file(event_path),
        "execution_genesis_event_sha256": events[0]["event_sha256"],
        "terminal_request_event_sha256": events[-1]["event_sha256"],
        "request_event_count": len(events),
        "provider_observation_window_utc": {
            "first_batch_timestamp": min(provider_times),
            "last_batch_timestamp": max(provider_times),
            "definition": (
                "The interval spans per-batch Action API curtimestamp receipts; it is not a "
                "single atomic database snapshot."
            ),
        },
        "raw_response_inventory": list(inventory),
        "candidate_manifest_path": str(config["paths"]["candidate_manifest"]),
        "candidate_manifest_sha256": hash_file(manifest_path),
        "counts": summarize_manifest(manifest),
        "limitations": [
            (
                "This is a complete follow-up of one fixed preexisting exploratory seed, not an "
                "exhaustive current R0 source census."
            ),
            (
                "Wikidata and Commons are discovery and delivery layers, not authoritative work "
                "records."
            ),
            (
                "No candidate is admitted until authoritative attribution, medium/support, work "
                "identity, and item/media rights are independently verified."
            ),
            "No image bytes were downloaded by this metadata-only audit.",
            (
                "No visual content label, decode result, physical-work deduplication, or "
                "active-study admission is claimed."
            ),
        ],
        "active_study_counts": {
            "downloaded_images": 0,
            "eligibility_derivatives": 0,
            "admitted_physical_works": 0,
        },
    }


def _validate_completion_receipt(
    root: Path,
    config: Mapping[str, Any],
    config_path: Path,
    receipt_path: Path,
    seal_path: Path,
    expected_seal_sha256: str,
    authorization: Mapping[str, Any],
    specs: Sequence[RequestSpec],
    rows: Sequence[Mapping[str, str]],
    workspace: Path,
    events: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, Mapping) or not _is_media_timestamp(receipt.get("completed_at_utc")):
        raise CensusError("existing completion receipt is malformed")
    intent_path = _repo_path(root, config["paths"]["planned_requests"], "paths.planned_requests")
    event_path = _repo_path(root, config["paths"]["request_events"], "paths.request_events")
    manifest_path = _repo_path(
        root, config["paths"]["candidate_manifest"], "paths.candidate_manifest"
    )
    inventory, response_paths, provider_times = _verified_success_inventory(
        specs, events, workspace
    )
    entities = parse_entity_batches(specs, response_paths)
    media = parse_media_batches(specs, response_paths, config)
    recomputed_manifest = build_candidate_manifest(rows, entities, media, config)
    if not manifest_path.is_file() or _read_jsonl(manifest_path) != recomputed_manifest:
        raise CensusError("existing candidate manifest differs from raw-response recomputation")
    if any(row.get("active_study_admission") is not False for row in recomputed_manifest):
        raise CensusError("existing candidate manifest overstates active-study admission")
    expected = _completion_receipt(
        root,
        config,
        config_path,
        seal_path,
        expected_seal_sha256,
        authorization,
        str(receipt["completed_at_utc"]),
        intent_path,
        event_path,
        events,
        inventory,
        manifest_path,
        recomputed_manifest,
        provider_times,
    )
    if dict(receipt) != expected:
        raise CensusError("existing completion receipt differs from full evidence recomputation")
    return dict(receipt)


def execute(
    root: Path, config_path: Path, seal_path: Path, expected_seal_sha256: str
) -> dict[str, Any]:
    root = root.resolve()
    config_path = config_path.resolve()
    seal_path = seal_path.resolve()
    config = _load_config(root, config_path)
    discovery = config["discovery_input"]
    rows = load_discovery_rows(
        _repo_path(root, discovery["path"], "discovery_input.path"),
        str(discovery["sha256"]),
        config["painters"],
        int(discovery["expected_rows"]),
        int(discovery["expected_distinct_items"]),
        int(discovery["expected_distinct_files"]),
    )
    intent_path = _repo_path(root, config["paths"]["planned_requests"], "paths.planned_requests")
    specs = _specs_from_intents(intent_path, str(config["census_id"]))
    rebuilt = build_request_specs(config, rows)
    if [spec.as_record(str(config["census_id"])) for spec in specs] != [
        spec.as_record(str(config["census_id"])) for spec in rebuilt
    ]:
        raise CensusError("frozen request intents differ from deterministic reconstruction")
    workspace = _repo_path(root, config["paths"]["workspace"], "paths.workspace")
    receipt_path = _repo_path(root, config["paths"]["execution_receipt"], "paths.execution_receipt")
    event_path = _repo_path(root, config["paths"]["request_events"], "paths.request_events")
    with _exclusive_execution_lock(workspace):
        locked_config = _load_config(root, config_path)
        if locked_config != config:
            raise CensusError("census config changed while acquiring the execution lock")
        authorization = _validate_seal(root, config, config_path, seal_path, expected_seal_sha256)
        events = _ensure_execution_genesis(
            root,
            config,
            config_path,
            seal_path,
            expected_seal_sha256,
            authorization,
            event_path,
        )
        if receipt_path.exists():
            return _validate_completion_receipt(
                root,
                config,
                config_path,
                receipt_path,
                seal_path,
                expected_seal_sha256,
                authorization,
                specs,
                rows,
                workspace,
                events,
            )
        receipts, response_paths = _execute_specs(root, config, specs, workspace, events)
        if set(response_paths) != {spec.request_id for spec in specs}:
            raise CensusError("not every frozen request has one verified successful response")
        events = _load_event_ledger(event_path, str(config["census_id"]))
        verified_inventory, verified_paths, provider_times = _verified_success_inventory(
            specs, events, workspace
        )
        if receipts != verified_inventory or response_paths != verified_paths:
            raise CensusError("in-process response inventory differs from ledger recomputation")
        entities = parse_entity_batches(specs, response_paths)
        media = parse_media_batches(specs, response_paths, config)
        manifest = build_candidate_manifest(rows, entities, media, config)
        manifest_path = _repo_path(
            root, config["paths"]["candidate_manifest"], "paths.candidate_manifest"
        )
        _write_jsonl_atomic(manifest_path, manifest)
        receipt = _completion_receipt(
            root,
            config,
            config_path,
            seal_path,
            expected_seal_sha256,
            authorization,
            _utc_now(),
            intent_path,
            event_path,
            events,
            verified_inventory,
            manifest_path,
            manifest,
            provider_times,
        )
        _write_json_atomic(receipt_path, receipt)
        return _validate_completion_receipt(
            root,
            config,
            config_path,
            receipt_path,
            seal_path,
            expected_seal_sha256,
            authorization,
            specs,
            rows,
            workspace,
            events,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="repository root (default: cwd)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/painter_feature_generation_v1/federated_metadata_census.json"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare", help="write deterministic request intents without networking")
    execute_parser = subparsers.add_parser("execute", help="run the authorized metadata census")
    execute_parser.add_argument("--seal", type=Path, required=True)
    execute_parser.add_argument("--seal-sha256", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = args.root.resolve()
    config_path = args.config if args.config.is_absolute() else root / args.config
    if args.command == "prepare":
        print(json.dumps(prepare(root, config_path), indent=2, sort_keys=True))
        return 0
    seal_path = args.seal if args.seal.is_absolute() else root / args.seal
    result = execute(root, config_path, seal_path, str(args.seal_sha256))
    print(json.dumps(result["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
