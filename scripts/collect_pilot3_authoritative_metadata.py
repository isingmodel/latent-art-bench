#!/usr/bin/env python3
"""Collect Pilot 3 catalog metadata without requesting artwork bytes.

The collector contacts only metadata endpoints. Every response is content-type
checked, and frozen image URLs are recorded but never fetched. The large Met
snapshot is downloaded to a temporary directory, hashed exactly, filtered, and
discarded. The external roster is exact and prospective: official museum
records, official image-service metadata, and the narrow published research-use
scope are bound without acquiring artwork bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import httpx

from latent_art_bench.data.museums import classify_landscape_candidate
from latent_art_bench.io import hash_file, read_json, stable_hash, write_json, write_jsonl

USER_AGENT = "latent-art-bench-pilot3-metadata/1.0"
MET_REVISION = "6fa206f0df6cf349d4fe558028d4c08e95f44eb6"
MET_FILE_SHA256 = "de617b9c947458e426111207f81a65bd1379a151c0077d3ce29cfc22fc0b9183"
EXTERNAL_ROSTER = Path("configs/pilot_3/external_museum_blocks.json")
EXTERNAL_ROSTER_SCHEMA = "pilot3-official-museum-block-roster/1.0"
ARTISTS: Mapping[str, Mapping[str, Any]] = {
    "alfred_sisley": {
        "artist_name": "Alfred Sisley",
        "aliases": ["Alfred Sisley"],
        "aic_agent_id": "36707",
        "met_constituent_id": "165111",
        "nga_constituent_id": "1877",
        "ulan": "500027485",
        "wikidata": "Q175130",
    },
    "camille_pissarro": {
        "artist_name": "Camille Pissarro",
        "aliases": ["Camille Pissarro", "Camille Jacob Pissarro"],
        "aic_agent_id": "36211",
        "met_constituent_id": "162257",
        "nga_constituent_id": "1791",
        "ulan": "500001924",
        "wikidata": "Q134741",
    },
    "paul_cezanne": {
        "artist_name": "Paul Cezanne",
        "aliases": ["Paul Cezanne", "Paul Cézanne"],
        "aic_agent_id": "40482",
        "met_constituent_id": "161761",
        "nga_constituent_id": "1115",
        "ulan": "500004793",
        "wikidata": "Q35548",
    },
    "pierre_auguste_renoir": {
        "artist_name": "Pierre-Auguste Renoir",
        "aliases": ["Pierre-Auguste Renoir", "Pierre Auguste Renoir", "Auguste Renoir"],
        "aic_agent_id": "36351",
        "met_constituent_id": "162302",
        "nga_constituent_id": "1823",
        "ulan": "500115467",
        "wikidata": "Q39931",
    },
}

AIC_FIELDS = (
    "id",
    "title",
    "date_start",
    "date_end",
    "date_display",
    "artist_id",
    "artist_title",
    "is_public_domain",
    "image_id",
    "artwork_type_title",
    "classification_title",
    "subject_titles",
    "style_titles",
    "medium_display",
    "thumbnail",
    "main_reference_number",
    "dimensions",
    "source_updated_at",
    "updated_at",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _int_or_none(value: object) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _normalized(value: str) -> str:
    return value.casefold().replace("é", "e")


def _is_painting(*values: object) -> bool:
    combined = " ".join(str(value or "") for value in values)
    normalized = _normalized(combined)
    return "paint" in normalized and "print" not in normalized


def _checked_response(response: httpx.Response, *, expected: str) -> bytes:
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").casefold()
    if content_type.startswith("image/"):
        raise RuntimeError(f"artwork/image bytes were returned by {response.url}")
    if expected == "json" and not any(
        marker in content_type for marker in ("json", "octet-stream")
    ):
        raise RuntimeError(f"expected JSON metadata from {response.url}, got {content_type}")
    if expected == "csv" and not any(
        marker in content_type for marker in ("text/", "csv", "octet-stream")
    ):
        raise RuntimeError(f"expected text/CSV metadata from {response.url}, got {content_type}")
    if expected == "html" and "html" not in content_type:
        raise RuntimeError(f"expected HTML metadata from {response.url}, got {content_type}")
    return response.content


def _response_evidence(
    response: httpx.Response,
    body: bytes,
    *,
    accessed_at: str,
    purpose: str,
) -> Dict[str, Any]:
    return {
        "accessed_at": accessed_at,
        "content_length": len(body),
        "content_sha256": _sha256_bytes(body),
        "content_type": response.headers.get("content-type"),
        "etag": response.headers.get("etag"),
        "last_modified": response.headers.get("last-modified"),
        "purpose": purpose,
        "request_method": "GET",
        "response_status": response.status_code,
        "url": str(response.url),
    }


def _sealed_row(values: Mapping[str, Any]) -> Dict[str, Any]:
    row = dict(values)
    row["metadata_row_sha256"] = stable_hash(row)
    return row


def _candidate_row(
    *,
    artist_id: str,
    source_id: str,
    source_object_id: str,
    title: str,
    creation_year: int | None,
    creation_year_text: str | None,
    classification: str,
    medium: str | None,
    physical_dimensions: str | None,
    source_url: str,
    image_url: str,
    native_width: int,
    native_height: int,
    rights_basis: str,
    subjects: Sequence[str],
    description: str | None,
    catalog_ids: Mapping[str, str],
    wikidata_id: str | None,
    source_snapshot_id: str,
    raw_source_row: Mapping[str, Any],
    asset_provider: str,
    asset_license: str,
    delivery_width: int | None = None,
    delivery_height: int | None = None,
    collection_block_id: str | None = None,
    collection_block_name: str | None = None,
    collection_wikidata_id: str | None = None,
    collection_block_role: str | None = None,
    commons_file: str | None = None,
    commons_original_file_sha1: str | None = None,
    commons_original_height: int | None = None,
    commons_original_width: int | None = None,
    commons_page_id: int | None = None,
    commons_license_url: str | None = None,
    asset_attribution_required: bool | None = None,
    asset_attribution: Mapping[str, Any] | None = None,
    rights_evidence: Mapping[str, Any] | None = None,
    capture_pipeline: Mapping[str, Any] | None = None,
    source_governance: str = "independent_museum_collection",
) -> Dict[str, Any]:
    delivery_width = native_width if delivery_width is None else delivery_width
    delivery_height = native_height if delivery_height is None else delivery_height
    score, evidence, decision, reason = classify_landscape_candidate(title, subjects, description)
    technical_reasons = []
    if min(delivery_width, delivery_height) < 512:
        technical_reasons.append("delivery_short_side_below_512")
    if max(delivery_width, delivery_height) / min(delivery_width, delivery_height) >= 2.0:
        technical_reasons.append("delivery_aspect_ratio_at_least_2")
    if technical_reasons:
        decision = "exclude"
        reason = "; ".join(technical_reasons)
    artist = ARTISTS[artist_id]
    eligibility_projection = {
        "artist_authority_ids": {
            "aic_agent_id": artist["aic_agent_id"],
            "met_constituent_id": artist["met_constituent_id"],
            "nga_constituent_id": artist["nga_constituent_id"],
            "ulan": artist["ulan"],
            "wikidata": artist["wikidata"],
        },
        "artist_id": artist_id,
        "asset_license": asset_license,
        "asset_provider": asset_provider,
        "classification": classification,
        "decision": decision,
        "delivery_height": delivery_height,
        "delivery_width": delivery_width,
        "genre_evidence": evidence,
        "genre_score": score,
        "native_height": native_height,
        "native_width": native_width,
        "public_domain_status": "confirmed",
        "source_id": source_id,
        "source_object_id": source_object_id,
    }
    return _sealed_row(
        {
            "artist_authority_ids": eligibility_projection["artist_authority_ids"],
            "artist_id": artist_id,
            "artist_name": artist["artist_name"],
            "asset_attribution": dict(asset_attribution) if asset_attribution else None,
            "asset_attribution_required": asset_attribution_required,
            "asset_license": asset_license,
            "asset_provider": asset_provider,
            "attribution_role": "artist",
            "attribution_status": "confirmed_by_authority_id_and_artist_role",
            "canonical_work_id": f"work-{source_id}-{source_object_id}",
            "catalog_ids": dict(sorted(catalog_ids.items())),
            "classification": classification,
            "collection_block_id": collection_block_id,
            "collection_block_name": collection_block_name,
            "collection_block_role": collection_block_role,
            "collection_wikidata_id": collection_wikidata_id,
            "commons_file": commons_file,
            "commons_license_url": commons_license_url,
            "commons_page_id": commons_page_id,
            "commons_original_file_sha1": commons_original_file_sha1,
            "commons_original_height": commons_original_height,
            "commons_original_width": commons_original_width,
            "creation_year": creation_year,
            "creation_year_text": creation_year_text,
            "capture_pipeline": dict(capture_pipeline) if capture_pipeline else None,
            "decision": decision,
            "decision_reason": reason,
            "description": description,
            "eligibility_semantic_sha256": stable_hash(eligibility_projection),
            "genre_evidence": evidence,
            "genre_score": score,
            "image_url": image_url,
            "delivery_height": delivery_height,
            "delivery_width": delivery_width,
            "medium": medium,
            "native_height": native_height,
            "native_width": native_width,
            "physical_dimensions": physical_dimensions,
            "public_domain_status": "confirmed",
            "raw_source_row_semantic_sha256": stable_hash(raw_source_row),
            "record_type": "pilot3_authoritative_candidate",
            "rights_basis": rights_basis,
            "rights_evidence": dict(rights_evidence) if rights_evidence else None,
            "schema_version": "1.0",
            "source_governance": source_governance,
            "source_id": source_id,
            "source_object_id": source_object_id,
            "source_snapshot_id": source_snapshot_id,
            "source_url": source_url,
            "subjects": list(subjects),
            "title": title,
            "wikidata_id": wikidata_id,
        }
    )


def _collect_aic(
    client: httpx.Client, accessed_at: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    candidates = []
    evidence = []
    fields = ",".join(AIC_FIELDS)
    for artist_id, artist in sorted(ARTISTS.items()):
        response = client.get(
            "https://api.artic.edu/api/v1/artworks/search",
            params={
                "query[term][artist_id]": artist["aic_agent_id"],
                "limit": 100,
                "fields": fields,
            },
            headers={"AIC-User-Agent": USER_AGENT},
        )
        body = _checked_response(response, expected="json")
        response_row = _response_evidence(
            response,
            body,
            accessed_at=accessed_at,
            purpose=f"AIC catalog metadata for {artist_id}",
        )
        response_row["artist_id"] = artist_id
        evidence.append(response_row)
        payload = json.loads(body)
        if int(payload["pagination"]["total_pages"]) != 1:
            raise RuntimeError(f"AIC query unexpectedly requires pagination for {artist_id}")
        for item in payload.get("data", []):
            if str(item.get("artist_id")) != artist["aic_agent_id"]:
                continue
            if not item.get("is_public_domain") or not item.get("image_id"):
                continue
            if not _is_painting(
                item.get("artwork_type_title"),
                item.get("classification_title"),
                item.get("medium_display"),
            ):
                continue
            thumbnail = item.get("thumbnail") or {}
            width = _int_or_none(thumbnail.get("width"))
            height = _int_or_none(thumbnail.get("height"))
            if width is None or height is None:
                continue
            object_id = str(item["id"])
            image_id = str(item["image_id"])
            info_response = client.get(
                f"https://www.artic.edu/iiif/2/{image_id}/info.json",
                headers={"AIC-User-Agent": USER_AGENT},
            )
            info_body = _checked_response(info_response, expected="json")
            info = json.loads(info_body)
            iiif_width = _int_or_none(info.get("width"))
            iiif_height = _int_or_none(info.get("height"))
            if iiif_width is None or iiif_height is None:
                raise RuntimeError(f"AIC IIIF lacks native dimensions for object {object_id}")
            sizes = [
                (_int_or_none(row.get("width")), _int_or_none(row.get("height")))
                for row in info.get("sizes") or []
                if isinstance(row, Mapping)
            ]
            exact_sizes = [
                (candidate_width, candidate_height)
                for candidate_width, candidate_height in sizes
                if candidate_width is not None
                and candidate_height is not None
                and min(candidate_width, candidate_height) >= 512
                and max(candidate_width, candidate_height) <= 2048
                and max(candidate_width, candidate_height)
                / min(candidate_width, candidate_height)
                < 2
            ]
            if not exact_sizes:
                raise RuntimeError(
                    f"AIC IIIF lacks a frozen exact size satisfying geometry for {object_id}"
                )
            # Use the smallest advertised derivative that meets the feature-input
            # gate.  This avoids both upsampling and an arbitrary long-edge rule
            # that previously excluded valid landscapes solely because the next
            # lower IIIF pyramid level had a 390--511 px short side.
            delivery_width, delivery_height = min(
                exact_sizes, key=lambda pair: pair[0] * pair[1]
            )
            evidence.append(
                {
                    **_response_evidence(
                        info_response,
                        info_body,
                        accessed_at=accessed_at,
                        purpose=f"AIC IIIF exact delivery dimensions for object {object_id}",
                    ),
                    "artist_id": artist_id,
                }
            )
            candidates.append(
                _candidate_row(
                    artist_id=artist_id,
                    source_id="aic",
                    source_object_id=object_id,
                    title=str(item.get("title") or f"AIC object {object_id}"),
                    creation_year=_int_or_none(item.get("date_start")),
                    creation_year_text=str(item.get("date_display") or "") or None,
                    classification=str(item.get("artwork_type_title") or "Painting"),
                    medium=str(item.get("medium_display") or "") or None,
                    physical_dimensions=str(item.get("dimensions") or "") or None,
                    source_url=f"https://www.artic.edu/artworks/{object_id}",
                    image_url=(
                        f"https://www.artic.edu/iiif/2/{image_id}/full/"
                        f"{delivery_width},{delivery_height}/0/default.jpg"
                    ),
                    # The exact IIIF service governs the frozen reproduction.  The
                    # search API's thumbnail dimensions can describe an older crop,
                    # so retain them in raw_source_row but do not substitute them for
                    # the service's own native geometry.
                    native_width=iiif_width,
                    native_height=iiif_height,
                    delivery_width=delivery_width,
                    delivery_height=delivery_height,
                    rights_basis=(
                        "AIC is_public_domain=true; AIC API collection metadata CC0; "
                        "public-domain IIIF asset"
                    ),
                    subjects=[str(value) for value in item.get("subject_titles") or []],
                    description=str(thumbnail.get("alt_text") or "") or None,
                    catalog_ids={
                        "aic": object_id,
                        "aic_accession": str(item.get("main_reference_number") or ""),
                        "aic_image_id": image_id,
                    },
                    wikidata_id=None,
                    source_snapshot_id=f"aic-live-{accessed_at}",
                    raw_source_row=item,
                    asset_provider="Art Institute of Chicago IIIF",
                    asset_license="public_domain",
                    capture_pipeline={
                        "holding_institution": "Art Institute of Chicago",
                        "image_service": "AIC IIIF v2",
                        "delivery_size_source": "exact_info_json_advertised_size",
                    },
                    source_governance="aic_collection_and_aic_iiif",
                )
            )
    return candidates, evidence


def _download_metadata_file(
    client: httpx.Client,
    url: str,
    path: Path,
    *,
    accessed_at: str,
    purpose: str,
    expected_sha256: str | None = None,
) -> Dict[str, Any]:
    digest = hashlib.sha256()
    byte_count = 0
    content_type = None
    headers: Mapping[str, str] = {}
    with client.stream("GET", url, headers={"Accept": "text/csv"}) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").casefold()
        if content_type.startswith("image/"):
            raise RuntimeError(f"image bytes were returned by metadata URL {response.url}")
        headers = dict(response.headers)
        with path.open("wb") as handle:
            for chunk in response.iter_bytes():
                digest.update(chunk)
                byte_count += len(chunk)
                handle.write(chunk)
    observed = digest.hexdigest()
    if expected_sha256 is not None and observed != expected_sha256:
        raise RuntimeError(
            f"metadata snapshot hash mismatch for {url}: expected {expected_sha256}, "
            f"found {observed}"
        )
    return {
        "accessed_at": accessed_at,
        "content_length": byte_count,
        "content_sha256": observed,
        "content_type": content_type,
        "etag": headers.get("etag"),
        "last_modified": headers.get("last-modified"),
        "purpose": purpose,
        "request_method": "GET",
        "response_status": 200,
        "url": url,
    }


def _met_artist_ids(row: Mapping[str, str]) -> Iterable[str]:
    ulans = [value.rsplit("/", 1)[-1] for value in row.get("Artist ULAN URL", "").split("|")]
    roles = row.get("Artist Role", "").split("|")
    for index, ulan in enumerate(ulans):
        if index < len(roles) and roles[index].strip().casefold() != "artist":
            continue
        for artist_id, artist in ARTISTS.items():
            if ulan == artist["ulan"]:
                yield artist_id


def _wikimedia_metadata(
    client: httpx.Client,
    object_ids: Sequence[str],
    accessed_at: str,
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    evidence = []
    filename_by_entity: Dict[str, str] = {}
    for offset in range(0, len(object_ids), 40):
        batch = list(object_ids[offset : offset + 40])
        response = client.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "claims",
                "format": "json",
                "origin": "*",
            },
        )
        body = _checked_response(response, expected="json")
        evidence.append(
            _response_evidence(
                response,
                body,
                accessed_at=accessed_at,
                purpose="Wikidata P18 metadata for Met public-domain paintings",
            )
        )
        for entity_id, entity in (json.loads(body).get("entities") or {}).items():
            claims = (entity.get("claims") or {}).get("P18") or []
            if not claims:
                continue
            try:
                filename = claims[0]["mainsnak"]["datavalue"]["value"]
            except (KeyError, TypeError):
                continue
            if isinstance(filename, str) and filename:
                filename_by_entity[entity_id] = filename

    result: Dict[str, Dict[str, Any]] = {}
    entity_by_title = {
        f"File:{filename}": entity_id for entity_id, filename in filename_by_entity.items()
    }
    titles = sorted(entity_by_title)
    for offset in range(0, len(titles), 40):
        batch = titles[offset : offset + 40]
        response = client.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": 1024,
                "format": "json",
                "origin": "*",
            },
        )
        body = _checked_response(response, expected="json")
        evidence.append(
            _response_evidence(
                response,
                body,
                accessed_at=accessed_at,
                purpose="Wikimedia Commons file rights and dimension metadata",
            )
        )
        payload = json.loads(body)
        normalized = {
            row["to"]: row["from"] for row in payload.get("query", {}).get("normalized") or []
        }
        for page in (payload.get("query", {}).get("pages") or {}).values():
            title = str(page.get("title") or "")
            original_title = normalized.get(title, title)
            entity_id = entity_by_title.get(original_title) or entity_by_title.get(title)
            info_rows = page.get("imageinfo") or []
            if entity_id is None or not info_rows:
                continue
            info = info_rows[0]
            metadata = info.get("extmetadata") or {}
            license_name = str((metadata.get("LicenseShortName") or {}).get("value") or "")
            usage_terms = str((metadata.get("UsageTerms") or {}).get("value") or "")
            license_text = f"{license_name} {usage_terms}".casefold()
            if not any(
                marker in license_text
                for marker in ("public domain", "cc0", "cc by", "creative commons")
            ):
                continue
            original_width = _int_or_none(info.get("width"))
            original_height = _int_or_none(info.get("height"))
            thumb_width = _int_or_none(info.get("thumbwidth"))
            thumb_height = _int_or_none(info.get("thumbheight"))
            use_thumb = bool(info.get("thumburl")) and (original_width or 0) > 1024
            result[entity_id] = {
                "description_url": info.get("descriptionurl"),
                "delivery_height": thumb_height if use_thumb else original_height,
                "delivery_url": info.get("thumburl") if use_thumb else info.get("url"),
                "delivery_width": thumb_width if use_thumb else original_width,
                "filename": filename_by_entity[entity_id],
                "height": original_height,
                "license": license_name or usage_terms,
                "thumb_height": thumb_height,
                "thumb_url": info.get("thumburl"),
                "thumb_width": thumb_width,
                "width": original_width,
            }
    return result, evidence


def _collect_met(
    client: httpx.Client,
    temporary: Path,
    accessed_at: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    url = (
        "https://media.githubusercontent.com/media/metmuseum/openaccess/"
        f"{MET_REVISION}/MetObjects.csv"
    )
    path = temporary / "MetObjects.csv"
    evidence = [
        _download_metadata_file(
            client,
            url,
            path,
            accessed_at=accessed_at,
            purpose="Met Open Access authoritative collection snapshot",
            expected_sha256=MET_FILE_SHA256,
        )
    ]
    evidence[0].update(
        {
            "git_blob_sha": "1823d4b43c2cd0825483a31763711253e6651453",
            "git_revision": MET_REVISION,
            "source": "Metropolitan Museum of Art Open Access",
        }
    )
    raw_rows: List[Tuple[str, Dict[str, str]]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            artist_ids = sorted(set(_met_artist_ids(row)))
            if not artist_ids or row.get("Is Public Domain") != "True":
                continue
            if not _is_painting(
                row.get("Object Name"), row.get("Classification"), row.get("Medium")
            ):
                continue
            for artist_id in artist_ids:
                raw_rows.append((artist_id, dict(row)))
    object_wikidata_ids = sorted(
        {
            str(row.get("Object Wikidata URL") or "").rstrip("/").rsplit("/", 1)[-1]
            for _, row in raw_rows
            if row.get("Object Wikidata URL")
        }
    )
    images, image_evidence = _wikimedia_metadata(client, object_wikidata_ids, accessed_at)
    evidence.extend(image_evidence)

    candidates = []
    for artist_id, item in raw_rows:
        wikidata_id = (
            str(item.get("Object Wikidata URL") or "").rstrip("/").rsplit("/", 1)[-1] or None
        )
        image = images.get(wikidata_id or "")
        if image is None or not image.get("delivery_url"):
            continue
        width = _int_or_none(image.get("width"))
        height = _int_or_none(image.get("height"))
        if width is None or height is None:
            continue
        delivery_width = _int_or_none(image.get("delivery_width"))
        delivery_height = _int_or_none(image.get("delivery_height"))
        if delivery_width is None or delivery_height is None:
            continue
        object_id = str(item["Object ID"])
        tags = [value for value in (item.get("Tags") or "").split("|") if value]
        raw_license = str(image.get("license") or "")
        normalized_license = (
            "public_domain"
            if "public domain" in raw_license.casefold()
            else "CC0"
            if "cc0" in raw_license.casefold()
            else None
        )
        if normalized_license is None:
            # The metadata fetcher may encounter other permissive Commons licenses,
            # but this pilot deliberately narrows Met delivery to unambiguous PD/CC0.
            continue
        candidates.append(
            _candidate_row(
                artist_id=artist_id,
                source_id="met",
                source_object_id=object_id,
                title=item.get("Title") or f"Met object {object_id}",
                creation_year=_int_or_none(item.get("Object Begin Date")),
                creation_year_text=item.get("Object Date") or None,
                classification=item.get("Classification") or item.get("Object Name") or "Painting",
                medium=item.get("Medium") or None,
                physical_dimensions=item.get("Dimensions") or None,
                source_url=item.get("Link Resource")
                or f"https://www.metmuseum.org/art/collection/search/{object_id}",
                image_url=str(image["delivery_url"]),
                native_width=width,
                native_height=height,
                delivery_width=delivery_width,
                delivery_height=delivery_height,
                rights_basis=(
                    "Met Open Access Is Public Domain=True; Wikimedia Commons P18 "
                    f"file metadata license={image.get('license') or 'open'}"
                ),
                subjects=tags,
                description=" ".join(tags) or None,
                catalog_ids={
                    "commons_file": str(image.get("filename") or ""),
                    "met": object_id,
                    "met_accession": item.get("Object Number") or "",
                },
                wikidata_id=wikidata_id,
                source_snapshot_id=f"met-openaccess-{MET_REVISION}",
                raw_source_row=item,
                asset_provider="Wikimedia Commons P18 delivery for Met work",
                asset_license=normalized_license,
                capture_pipeline={
                    "holding_institution": "Metropolitan Museum of Art",
                    "delivery_provider": "Wikimedia Commons P18",
                    "delivery_variant": "1024px_or_unscaled_original",
                },
                source_governance="met_collection_with_commons_delivery",
            )
        )
    return candidates, evidence


def _validated_museum_roster(root: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    path = (root / EXTERNAL_ROSTER).resolve()
    roster = read_json(path)
    if not isinstance(roster, dict) or roster.get("schema_version") != EXTERNAL_ROSTER_SCHEMA:
        raise RuntimeError("official-museum roster schema is missing or stale")
    if roster.get("source_id") != "museum_balanced":
        raise RuntimeError("official-museum roster has the wrong source id")
    if roster.get("study_use") != "internal_noncommercial_scholarly_research_measurement_only":
        raise RuntimeError("official-museum roster has an unsupported use scope")
    if roster.get("redistribution_of_source_images") is not False:
        raise RuntimeError("official-museum source images must not be redistributed")
    blocks = roster.get("blocks")
    if not isinstance(blocks, list) or [row.get("block_id") for row in blocks] != [
        "minneapolis",
        "dallas",
        "toledo",
    ]:
        raise RuntimeError("official-museum roster requires the three frozen blocks")
    policy = roster.get("block_policy") or {}
    if policy != {
        "primary_block_count": 3,
        "replacement_eligible_reserve_block_count": 0,
        "works_per_artist_per_block": 1,
        "replacement_unit": "none_after_freeze",
        "replacement_order": [],
        "analysis_unit": "holding_institution_block",
        "permutation_rule": (
            "permute_the_four_artist_labels_independently_within_each_complete_block"
        ),
    }:
        raise RuntimeError("official-museum block policy is stale")

    expected_artists = sorted(ARTISTS)
    seen_works: set[str] = set()
    seen_accessions: set[Tuple[str, str]] = set()
    seen_urls: set[str] = set()
    rows: List[Dict[str, Any]] = []
    required_work_fields = {
        "artist_id",
        "work_wikidata_id",
        "museum_object_id",
        "museum_accession",
        "title",
        "creation_year",
        "classification",
        "object_name",
        "medium",
        "physical_dimensions",
        "object_url",
        "metadata_url",
        "image_identifier",
        "image_url",
        "delivery_width",
        "delivery_height",
        "institutional_rights_status",
        "common_domain_terms",
    }
    for block in blocks:
        if not isinstance(block, dict) or block.get("role") != "primary":
            raise RuntimeError("official-museum block must be a primary object")
        if block.get("asset_license") != "INSTITUTIONAL_RESEARCH_USE":
            raise RuntimeError("official-museum block lacks the scoped rights enum")
        if not str(block.get("rights_policy_url") or "").startswith("https://"):
            raise RuntimeError("official-museum block lacks an HTTPS rights policy")
        if block.get("rights_reviewed_at") != "2026-08-31T18:00:00+00:00":
            raise RuntimeError("official-museum rights review date is stale")
        works = block.get("works")
        if (
            not isinstance(works, list)
            or [row.get("artist_id") for row in works] != expected_artists
        ):
            raise RuntimeError(
                f"museum block {block.get('block_id')} must contain one sorted work per artist"
            )
        for work in works:
            if not isinstance(work, dict) or not required_work_fields.issubset(work):
                raise RuntimeError("official-museum work metadata is incomplete")
            work_id = str(work["work_wikidata_id"])
            accession_key = (str(block["block_id"]), str(work["museum_accession"]))
            image_url = str(work["image_url"])
            if (
                not work_id.startswith("Q")
                or work_id in seen_works
                or accession_key in seen_accessions
                or image_url in seen_urls
                or not image_url.startswith("https://")
                or not str(work["metadata_url"]).startswith("https://")
                or int(work["delivery_width"]) <= 0
                or int(work["delivery_height"]) <= 0
                or not isinstance(work["common_domain_terms"], list)
                or not work["common_domain_terms"]
            ):
                raise RuntimeError("official-museum work identity or delivery is invalid")
            seen_works.add(work_id)
            seen_accessions.add(accession_key)
            seen_urls.add(image_url)
            rows.append(
                {
                    **work,
                    **{
                        key: block[key]
                        for key in (
                            "block_id",
                            "block_name",
                            "collection_wikidata_id",
                            "role",
                            "metadata_kind",
                            "asset_provider",
                            "asset_license",
                            "rights_policy_url",
                            "rights_scope",
                            "rights_reviewed_at",
                            "attribution",
                        )
                    },
                }
            )
    if len(rows) != 12:
        raise RuntimeError("official-museum roster must contain exactly twelve works")
    return roster, rows


def _external_policy_evidence(
    client: httpx.Client,
    blocks: Sequence[Mapping[str, Any]],
    accessed_at: str,
) -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    evidence: List[Dict[str, Any]] = []
    bindings: Dict[str, Dict[str, Any]] = {}
    for block in blocks:
        block_id = str(block["block_id"])
        policy_url = str(block["rights_policy_url"])
        if block_id == "toledo":
            projection = {
                "authority": block["block_name"],
                "policy_url": policy_url,
                "reviewed_at": block["rights_reviewed_at"],
                "scope": block["rights_scope"],
                "review_method": "metadata_only_browser_review_of_official_page",
            }
            semantic_sha256 = stable_hash(projection)
            bindings[block_id] = {
                **projection,
                "semantic_sha256": semantic_sha256,
            }
            evidence.append(
                {
                    "accessed_at": accessed_at,
                    "block_id": block_id,
                    "content_length": None,
                    "content_sha256": None,
                    "content_type": "reviewed_official_policy_projection",
                    "etag": None,
                    "last_modified": None,
                    "purpose": "Toledo official image-policy scope review",
                    "request_method": "metadata_only_browser_review",
                    "response_status": "reviewed",
                    "semantic_sha256": semantic_sha256,
                    "source_id": "museum_balanced",
                    "url": policy_url,
                }
            )
            continue
        response = client.get(policy_url, headers={"Accept": "text/html,text/plain"})
        response.raise_for_status()
        body = response.content
        content_type = response.headers.get("content-type", "").casefold()
        if content_type.startswith("image/"):
            raise RuntimeError(f"image bytes were returned by policy URL {response.url}")
        normalized_body = _plain_html(body.decode(response.encoding or "utf-8", errors="replace"))
        normalized_lower = normalized_body.casefold()
        if block_id == "minneapolis" and not all(
            marker in normalized_lower
            for marker in ("public domain", "images", "no restrictions")
        ):
            raise RuntimeError("Mia open-access policy markers are missing")
        if block_id == "dallas" and not all(
            marker in normalized_lower
            for marker in ("non-commercial", "educational", "fair use")
        ):
            raise RuntimeError("DMA research-use policy markers are missing")
        binding = {
            "authority": block["block_name"],
            "content_sha256": _sha256_bytes(body),
            "policy_url": str(response.url),
            "reviewed_at": block["rights_reviewed_at"],
            "scope": block["rights_scope"],
        }
        binding["semantic_sha256"] = stable_hash(binding)
        bindings[block_id] = binding
        evidence.append(
            {
                **_response_evidence(
                    response,
                    body,
                    accessed_at=accessed_at,
                    purpose=f"{block['block_name']} official image-use policy",
                ),
                "block_id": block_id,
                "source_id": "museum_balanced",
            }
        )
    return evidence, bindings


def _dallas_source_bridges(
    client: httpx.Client,
    rows: Sequence[Mapping[str, Any]],
    accessed_at: str,
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    by_title = {
        f"File:{row['source_bridge_commons_filename']}": row
        for row in rows
        if row.get("block_id") == "dallas"
    }
    response = client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "format": "json",
            "formatversion": 2,
            "iiprop": "size|sha1|mime|user|timestamp|comment|canonicaltitle",
            "prop": "imageinfo",
            "titles": "|".join(by_title),
        },
    )
    body = _checked_response(response, expected="json")
    payload = json.loads(body)
    aliases = {
        str(row["to"]): str(row["from"])
        for row in (payload.get("query") or {}).get("normalized") or []
    }
    found: Dict[str, Dict[str, Any]] = {}
    for page in (payload.get("query") or {}).get("pages") or []:
        title = str(page.get("title") or "")
        roster_title = aliases.get(title, title)
        if roster_title not in by_title and title in by_title:
            roster_title = title
        info_rows = page.get("imageinfo") or []
        if roster_title not in by_title or len(info_rows) != 1:
            raise RuntimeError("DMA official-source bridge is missing or ambiguous")
        row = by_title[roster_title]
        info = info_rows[0]
        comment = str(info.get("comment") or "")
        if (
            str(info.get("sha1") or "") != row["source_bridge_commons_sha1"]
            or _int_or_none(info.get("width")) != int(row["delivery_width"])
            or _int_or_none(info.get("height")) != int(row["delivery_height"])
            or str(row["image_url"]) not in comment
            or str(info.get("mime") or "") != "image/jpeg"
        ):
            raise RuntimeError(f"DMA source bridge drifted for {roster_title}")
        found[str(row["museum_object_id"])] = {
            "commons_filename": roster_title.removeprefix("File:"),
            "commons_file_sha1": info["sha1"],
            "official_source_url": row["image_url"],
            "upload_comment": comment,
            "upload_timestamp": info.get("timestamp"),
            "uploader": info.get("user"),
        }
    if len(found) != 4:
        raise RuntimeError("DMA source bridges do not cover the complete block")
    return found, {
        **_response_evidence(
            response,
            body,
            accessed_at=accessed_at,
            purpose="DMA exact official-file URL to museum-object source bridges",
        ),
        "block_id": "dallas",
        "source_id": "museum_balanced",
    }


def _collect_museum_balanced(
    client: httpx.Client, root: Path, accessed_at: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    roster, roster_rows = _validated_museum_roster(root)
    blocks = [row for row in roster["blocks"] if isinstance(row, Mapping)]
    policy_rows, policy_bindings = _external_policy_evidence(client, blocks, accessed_at)
    source_bridges, source_bridge_evidence = _dallas_source_bridges(
        client, roster_rows, accessed_at
    )
    evidence = [*policy_rows, source_bridge_evidence]
    candidates: List[Dict[str, Any]] = []
    snapshot_id = f"museum-balanced-live-{accessed_at}"

    for row in roster_rows:
        block_id = str(row["block_id"])
        artist_id = str(row["artist_id"])
        kind = str(row["metadata_kind"])
        raw_source: Dict[str, Any]
        if kind == "mia_json":
            response = client.get(str(row["metadata_url"]))
            body = _checked_response(response, expected="json")
            value = json.loads(body)
            expected_artists = {
                _normalized(str(value))
                for value in (
                    ARTISTS[artist_id]["artist_name"],
                    *ARTISTS[artist_id]["aliases"],
                )
            }
            expected_image = f"{row['image_identifier']}.jpg"
            if (
                str(value.get("id")) != str(row["museum_object_id"])
                or value.get("accession_number") != row["museum_accession"]
                or value.get("title") != row["title"]
                or _normalized(str(value.get("artist") or "")) not in expected_artists
                or value.get("object_name") != "Painting"
                or not _is_painting(value.get("object_name"), value.get("medium"))
                or value.get("image") != "valid"
                or value.get("public_access") != 1
                or value.get("rights_type") != "Public Domain"
                or value.get("Rights_Image_Display") != "Full"
                or value.get("Primary_RenditionNumber") != expected_image
                or _int_or_none(value.get("image_width")) != int(row["delivery_width"])
                or _int_or_none(value.get("image_height")) != int(row["delivery_height"])
            ):
                raise RuntimeError(f"Mia official metadata drifted for {row['museum_object_id']}")
            raw_source = value
            evidence.append(
                {
                    **_response_evidence(
                        response,
                        body,
                        accessed_at=accessed_at,
                        purpose=f"Mia official object metadata {row['museum_object_id']}",
                    ),
                    "block_id": block_id,
                    "source_id": "museum_balanced",
                }
            )
        elif kind == "dma_json_with_commons_source_bridge":
            response = client.get(str(row["metadata_url"]))
            body = _checked_response(response, expected="json")
            value = json.loads(body)
            artist_rows = [
                item
                for item in value.get("constituents") or []
                if isinstance(item, Mapping) and item.get("role") == "Artist"
            ]
            expected_artists = {
                _normalized(str(value))
                for value in (
                    ARTISTS[artist_id]["artist_name"],
                    *ARTISTS[artist_id]["aliases"],
                )
            }
            if (
                str(value.get("id")) != str(row["museum_object_id"])
                or value.get("number") != row["museum_accession"]
                or value.get("title") != row["title"]
                or value.get("classification") != "Paintings"
                or value.get("object_name") != "Painting"
                or not _is_painting(value.get("object_name"), value.get("medium"))
                or (value.get("copyright") or {}).get("type") != "Public domain"
                or (value.get("copyright") or {}).get("credit_line")
                != "Image courtesy Dallas Museum of Art"
                or len(artist_rows) != 1
                or _normalized(str(artist_rows[0].get("name") or "")) not in expected_artists
            ):
                raise RuntimeError(f"DMA official metadata drifted for {row['museum_object_id']}")
            raw_source = {
                "museum_object": value,
                "official_source_bridge": source_bridges[str(row["museum_object_id"])],
            }
            evidence.append(
                {
                    **_response_evidence(
                        response,
                        body,
                        accessed_at=accessed_at,
                        purpose=f"DMA official object metadata {row['museum_object_id']}",
                    ),
                    "block_id": block_id,
                    "source_id": "museum_balanced",
                }
            )
        elif kind == "toledo_emuseum_html_and_iiif2_manifest":
            raw_source = {
                "metadata_review_method": (
                    "metadata_only_browser_review_of_official_object_and_manifest"
                ),
                "object_projection": {
                    key: row[key]
                    for key in (
                        "museum_object_id",
                        "museum_accession",
                        "title",
                        "creation_year",
                        "classification",
                        "medium",
                        "physical_dimensions",
                        "object_url",
                    )
                },
                "iiif_manifest_projection": {
                    "manifest_url": row["image_metadata_url"],
                    "resource_url": row["image_url"],
                    "service_image_id": row["image_identifier"],
                    "width": row["delivery_width"],
                    "height": row["delivery_height"],
                    "format": "image/jpeg",
                    "profile": "http://iiif.io/api/image/2/level2.json",
                },
            }
            projection_hash = stable_hash(raw_source)
            evidence.append(
                {
                    "accessed_at": accessed_at,
                    "block_id": block_id,
                    "content_length": None,
                    "content_sha256": None,
                    "content_type": "reviewed_official_metadata_projection",
                    "etag": None,
                    "last_modified": None,
                    "purpose": (
                        "Toledo official object and IIIF metadata "
                        f"{row['museum_object_id']}"
                    ),
                    "request_method": "metadata_only_browser_review",
                    "response_status": "reviewed",
                    "semantic_sha256": projection_hash,
                    "source_id": "museum_balanced",
                    "url": row["image_metadata_url"],
                }
            )
        else:
            raise RuntimeError(f"unsupported official-museum metadata kind: {kind}")

        rights_evidence = {
            **policy_bindings[block_id],
            "asset_status": row["institutional_rights_status"],
            "asset_url": row["image_url"],
            "redistribution_allowed_by_study": False,
            "study_use": roster["study_use"],
        }
        candidates.append(
            _candidate_row(
                artist_id=artist_id,
                source_id="museum_balanced",
                source_object_id=f"{block_id}:{row['museum_object_id']}",
                title=str(row["title"]),
                creation_year=int(row["creation_year"]),
                creation_year_text=str(row["creation_year"]),
                classification=(
                    "Painting"
                    if row.get("classification_override")
                    else str(row["classification"])
                ),
                medium=str(row["medium"]),
                physical_dimensions=str(row["physical_dimensions"]),
                source_url=str(row["object_url"]),
                image_url=str(row["image_url"]),
                native_width=int(row["delivery_width"]),
                native_height=int(row["delivery_height"]),
                delivery_width=int(row["delivery_width"]),
                delivery_height=int(row["delivery_height"]),
                rights_basis=(
                    f"{row['block_name']} official record/policy; exact asset status="
                    f"{row['institutional_rights_status']}; scope={row['rights_scope']}; "
                    "internal noncommercial scholarly measurement only; no redistribution"
                ),
                subjects=[str(value) for value in row["common_domain_terms"]],
                description=(
                    "Prospectively frozen outdoor-place classification from metadata-only "
                    "art-historical and official museum record review"
                ),
                catalog_ids={
                    "museum_balanced": f"{block_id}:{row['museum_object_id']}",
                    "museum_balanced_accession": str(row["museum_accession"]),
                    "museum_accession": str(row["museum_accession"]),
                    "museum_object_id": str(row["museum_object_id"]),
                    "work_wikidata": str(row["work_wikidata_id"]),
                },
                wikidata_id=str(row["work_wikidata_id"]),
                source_snapshot_id=snapshot_id,
                raw_source_row=raw_source,
                asset_provider=str(row["asset_provider"]),
                asset_license=str(row["asset_license"]),
                collection_block_id=block_id,
                collection_block_name=str(row["block_name"]),
                collection_wikidata_id=str(row["collection_wikidata_id"]),
                collection_block_role=str(row["role"]),
                asset_attribution_required=True,
                asset_attribution={
                    "artist_or_creator": ARTISTS[artist_id]["artist_name"],
                    "attribution": row["attribution"],
                    "description_url": row["object_url"],
                    "license_id": row["asset_license"],
                    "license_url": row["rights_policy_url"],
                    "required": True,
                },
                rights_evidence=rights_evidence,
                capture_pipeline={
                    "block_id": block_id,
                    "delivery_provider": row["asset_provider"],
                    "holding_institution": row["block_name"],
                    "metadata_kind": kind,
                    "same_capture_session_claimed": False,
                },
                source_governance="holding_institution_object_record_and_official_asset_service",
            )
        )

    roster_path = (root / EXTERNAL_ROSTER).resolve()
    roster_binding = {
        "path": EXTERNAL_ROSTER.as_posix(),
        "file_sha256": hash_file(roster_path),
        "semantic_sha256": stable_hash(roster),
        "work_count": len(roster_rows),
    }
    return candidates, evidence, roster_binding


def _plain_html(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def collect(root: Path) -> Dict[str, Any]:
    accessed_at = _utc_now()
    headers = {
        "Accept": "application/json,text/csv;q=0.9,text/plain;q=0.8",
        "User-Agent": USER_AGENT,
    }
    timeout = httpx.Timeout(300.0, read=300.0)
    with tempfile.TemporaryDirectory(prefix="pilot3-metadata-") as temporary_name:
        temporary = Path(temporary_name)
        with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
            aic_rows, aic_evidence = _collect_aic(client, accessed_at)
            met_rows, met_evidence = _collect_met(client, temporary, accessed_at)
            external_rows, external_evidence, external_roster_binding = (
                _collect_museum_balanced(client, root, accessed_at)
            )

    for row in aic_evidence:
        row["source_id"] = "aic"
    for row in met_evidence:
        row["source_id"] = "met"

    rows = sorted(
        aic_rows + met_rows + external_rows,
        key=lambda row: (
            str(row["artist_id"]),
            str(row["source_id"]),
            str(row["source_object_id"]),
        ),
    )
    identities = [(row["source_id"], row["source_object_id"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise RuntimeError("authoritative metadata contains duplicate source objects")
    evidence_rows = aic_evidence + met_evidence + external_evidence
    evidence_rows.sort(key=lambda row: (str(row["purpose"]), str(row["url"])))
    snapshot = {
        "accessed_at": accessed_at,
        "artist_authorities": {
            artist_id: dict(artist) for artist_id, artist in sorted(ARTISTS.items())
        },
        "artwork_or_image_bytes_requested": False,
        "candidate_manifest_path": "configs/pilot_3/metadata/authoritative_candidates.jsonl",
        "candidate_manifest_semantic_sha256": stable_hash(rows),
        "candidate_row_count": len(rows),
        "claim_boundary": (
            "This snapshot verifies catalog metadata, rights flags, declared dimensions, "
            "and metadata-only acquisition references. It does not attest artwork bytes, "
            "color profiles, crops, borders, corruption, or learned features."
        ),
        "external_museum_roster": external_roster_binding,
        "record_type": "pilot3_authoritative_metadata_snapshot",
        "responses": evidence_rows,
        "schema_version": "1.0",
        "source_governance": {
            "aic": "Art Institute of Chicago collection and IIIF service",
            "met": (
                "Metropolitan Museum of Art collection metadata; Wikimedia Commons P18 "
                "is the asset-delivery provider and is recorded separately"
            ),
            "museum_balanced": (
                "Three complete holding-institution blocks use official museum object "
                "records and official museum asset services; each block is indivisible, "
                "and inference permutes labels only within blocks"
            ),
        },
    }
    snapshot["semantic_sha256"] = stable_hash(snapshot)
    candidate_path = root / "configs/pilot_3/metadata/authoritative_candidates.jsonl"
    evidence_path = root / "configs/pilot_3/metadata/source_snapshots.json"
    write_jsonl(candidate_path, rows)
    write_json(evidence_path, snapshot)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    result = collect(args.root.resolve())
    print(json.dumps({"status": "complete", **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
