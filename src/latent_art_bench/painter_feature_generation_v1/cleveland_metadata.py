"""Cleveland Museum of Art metadata route on the shared census engine.

One exact Open Access API request per painter, no authentication, no image request. The
parser validates only the fields the screen uses (creator identity and role, object type,
technique/support, accession, CC0 status, and reported rendition geometry) and retains the
rest of each record raw, so an unfamiliar representation is recorded rather than fatal.

Screened rows are Cleveland holding-record candidates. They are not physical works, they are
not reconciled against any other route, and nothing here downloads or admits an image.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence

import httpx

from latent_art_bench.painter_feature_generation_v1 import census_engine as engine
from latent_art_bench.painter_feature_generation_v1 import panel
from latent_art_bench.painter_feature_generation_v1.content_lexicon import fold as _fold

ROUTE_ID = "cleveland_metadata"
SCHEMA_PREFIX = "painter-feature-generation-v1-cleveland-metadata"
ENDPOINT = "https://openaccess-api.clevelandart.org/api/artworks/"
DEFAULT_CONFIG = "configs/painter_feature_generation_v1/cleveland_metadata_census.json"
PAINTERS = panel.ID_NAME_PAIRS
RETAINED_FIELDS = (
    "id",
    "accession_number",
    "title",
    "creation_date",
    "creation_date_earliest",
    "creation_date_latest",
    "creators",
    "type",
    "technique",
    "support_materials",
    "department",
    "collection",
    "culture",
    "measurements",
    "share_license_status",
    "copyright",
    "url",
    "images",
    "updated_at",
)
RENDITIONS = ("full", "print", "web")
# One unpaginated page per painter. The limit must exceed any single painter's total holding at
# Cleveland, prints and drawings included, or the response is not a complete one-page census and
# the run terminates. 100 was too close to AIC's observed 65-row Pissarro holding.
PAGE_LIMIT = 1000


class ClevelandError(engine.CensusError):
    """Raised when the Cleveland contract fails closed."""


def _tokens(value: str) -> set:
    return set(re.findall(r"[a-z]+", _fold(value)))


def validate_config(config: Mapping[str, Any]) -> None:
    painters = config.get("painters")
    if not isinstance(painters, list) or len(painters) != 4:
        raise ClevelandError("exactly four painters are required")
    observed = []
    for row in painters:
        if not isinstance(row, Mapping):
            raise ClevelandError("painter row is not an object")
        painter_id = row.get("painter_id")
        name = row.get("cma_artist_query")
        if not isinstance(painter_id, str) or not isinstance(name, str) or not name.strip():
            raise ClevelandError("painter identity is malformed")
        observed.append((painter_id, name))
    if observed != list(PAINTERS):
        raise ClevelandError("painter roster differs from the prospective contract")
    screening = config.get("screening_contract")
    if (
        not isinstance(screening, Mapping)
        or screening.get("painting_tokens") != ["painting"]
        or screening.get("required_medium_tokens") != ["oil", "canvas"]
        or screening.get("minimum_reported_short_side") != 1024
        or screening.get("required_share_license_status") != "CC0"
        or screening.get("page_limit") != PAGE_LIMIT
        or not isinstance(screening.get("candidate_gate"), str)
        or not isinstance(screening.get("authority_ceiling"), str)
        or not isinstance(screening.get("malformed_field_rule"), str)
    ):
        raise ClevelandError("screening contract is invalid")


def build_intents(config: Mapping[str, Any]) -> List[Dict[str, Any]]:
    endpoint = str(config["source_contract"]["endpoint"])
    limit = str(config["screening_contract"]["page_limit"])
    rows: List[Dict[str, Any]] = []
    for sequence, painter in enumerate(config["painters"], start=1):
        params = {"artists": painter["cma_artist_query"], "limit": limit, "skip": "0"}
        rows.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}-intent/1.0",
                "census_id": config["census_id"],
                "request_id": f"cma-artist-{sequence:04d}",
                "sequence": sequence,
                "method": "GET",
                "endpoint": endpoint,
                "params": params,
                "encoded_url": str(httpx.Request("GET", endpoint, params=params).url),
                "painter_id": painter["painter_id"],
                "cma_artist_query": painter["cma_artist_query"],
            }
        )
    return rows


def _creator_view(creator: Any) -> Dict[str, Any]:
    if not isinstance(creator, Mapping):
        return {"description": None, "role": None, "qualifier": None, "id": None, "raw": creator}
    return {
        "description": creator.get("description"),
        "role": creator.get("role"),
        "qualifier": creator.get("qualifier"),
        "id": creator.get("id"),
    }


def _support_strings(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, Mapping):
                out.extend(str(v) for v in item.values() if isinstance(v, str))
        return out
    return []


def _rendition_geometry(images: Any) -> Dict[str, Any]:
    """Largest reported short side among renditions that expose a URL."""
    best: Optional[int] = None
    view: Dict[str, Any] = {}
    if isinstance(images, Mapping):
        for name in RENDITIONS:
            rendition = images.get(name)
            if not isinstance(rendition, Mapping):
                continue
            width = engine.as_int(rendition.get("width"))
            height = engine.as_int(rendition.get("height"))
            url = rendition.get("url") if isinstance(rendition.get("url"), str) else None
            view[name] = {"url": url, "width": width, "height": height}
            if url and width and height and width > 0 and height > 0:
                short = min(width, height)
                best = short if best is None else max(best, short)
    return {"renditions": view, "largest_reported_short_side": best}


def parse_response(
    body: bytes, intent: Mapping[str, Any], config: Mapping[str, Any], response_sha256: str
) -> List[Dict[str, Any]]:
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClevelandError("Cleveland response is not JSON") from exc
    if not isinstance(payload, Mapping):
        raise ClevelandError("Cleveland response is not an object")
    data = payload.get("data")
    info = payload.get("info")
    if not isinstance(data, list) or not isinstance(info, Mapping):
        raise ClevelandError("Cleveland response lacks data or info")
    total = engine.as_int(info.get("total"))
    limit = int(intent["params"]["limit"])
    if total is None or total < 0:
        raise ClevelandError("Cleveland info.total is not an integer")
    if total > limit or len(data) != total:
        raise ClevelandError(
            f"Cleveland response is not a complete one-page census (total={total}, "
            f"rows={len(data)}, limit={limit})"
        )
    screening = config["screening_contract"]
    painting_tokens = set(screening["painting_tokens"])
    medium_tokens = set(screening["required_medium_tokens"])
    minimum_short_side = int(screening["minimum_reported_short_side"])
    required_license = _fold(str(screening["required_share_license_status"]))
    target = _fold(str(intent["cma_artist_query"]))
    records: List[Dict[str, Any]] = []
    for item in data:
        if not isinstance(item, Mapping):
            raise ClevelandError("Cleveland data row is not an object")
        artwork_id = engine.as_int(item.get("id"))
        if artwork_id is None or artwork_id <= 0:
            raise ClevelandError("Cleveland row lacks a positive integer id")
        creators_raw = item.get("creators")
        creators = (
            [_creator_view(c) for c in creators_raw] if isinstance(creators_raw, list) else []
        )
        exact_matches = []
        for creator in creators:
            description = creator["description"]
            if not isinstance(description, str):
                continue
            if _fold(description).startswith(target):
                role = creator["role"]
                qualifier = creator["qualifier"]
                exact_matches.append(
                    {
                        "description": description,
                        "role_is_artist_or_unstated": role in (None, "")
                        or (isinstance(role, str) and _fold(role) == "artist"),
                        "qualifier_empty": qualifier in (None, ""),
                    }
                )
        exact_creator = any(
            m["role_is_artist_or_unstated"] and m["qualifier_empty"] for m in exact_matches
        )
        object_type = item.get("type") if isinstance(item.get("type"), str) else ""
        technique = item.get("technique") if isinstance(item.get("technique"), str) else ""
        support = " ".join(_support_strings(item.get("support_materials")))
        painting = bool(painting_tokens & _tokens(object_type))
        oil_canvas = medium_tokens.issubset(_tokens(technique + " " + support))
        accession = item.get("accession_number")
        has_accession = isinstance(accession, str) and bool(accession.strip())
        license_status = item.get("share_license_status")
        cc0 = isinstance(license_status, str) and _fold(license_status) == required_license
        geometry = _rendition_geometry(item.get("images"))
        short_side = geometry["largest_reported_short_side"]
        has_image = any(r["url"] for r in geometry["renditions"].values())
        geometry_ok = short_side is not None and short_side >= minimum_short_side
        authority_candidate = exact_creator and painting and oil_canvas and has_accession
        media_candidate = authority_candidate and cc0 and has_image and geometry_ok
        record = {field: item.get(field) for field in RETAINED_FIELDS}
        record["id"] = artwork_id
        record["creators"] = creators
        record["images"] = geometry["renditions"]
        records.append(
            {
                "schema_version": f"{SCHEMA_PREFIX}-candidate/1.0",
                "census_id": intent["census_id"],
                "painter_id": intent["painter_id"],
                "cma_artist_query": intent["cma_artist_query"],
                "cma_artwork_id": artwork_id,
                "source_request_id": intent["request_id"],
                "raw_response_sha256": response_sha256,
                "field_presence": sorted(key for key in item if isinstance(key, str)),
                "cma_record": record,
                "screening": {
                    "exact_creator_match": exact_creator,
                    "creator_matches": exact_matches,
                    "painting_classification": painting,
                    "oil_and_canvas_tokens": oil_canvas,
                    "accession_present": has_accession,
                    "share_license_cc0": cc0,
                    "image_url_present": has_image,
                    "largest_reported_short_side": short_side,
                    "reported_short_side_at_least_minimum": geometry_ok,
                    "authority_record_candidate": authority_candidate,
                    "metadata_and_media_candidate": media_candidate,
                },
                "authority_status": "cma_holding_record_candidate_not_identity_reconciled",
                "image_status": "not_requested",
                "content_status": "not_blind_coded",
                "physical_work_identity_status": "not_reconciled",
                "active_study_admission": False,
            }
        )
    return records


def _counts(rows: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    return {
        "returned_rows": len(rows),
        "authority_record_candidates": sum(
            row["screening"]["authority_record_candidate"] for row in rows
        ),
        "metadata_and_media_candidates": sum(
            row["screening"]["metadata_and_media_candidate"] for row in rows
        ),
    }


def summarize(rows: Sequence[Mapping[str, Any]], config: Mapping[str, Any]) -> Dict[str, Any]:
    by_painter = {
        painter["painter_id"]: _counts(
            [row for row in rows if row["painter_id"] == painter["painter_id"]]
        )
        for painter in config["painters"]
    }
    return {**_counts(rows), "by_painter": by_painter}


CONTRACT = engine.RouteContract(
    route_id=ROUTE_ID,
    schema_prefix=SCHEMA_PREFIX,
    module_path="src/latent_art_bench/painter_feature_generation_v1/cleveland_metadata.py",
    script_path="scripts/collect_pfg_v1_cleveland_metadata.py",
    test_path="tests/painter_feature_generation_v1/test_cleveland_metadata.py",
    endpoint=ENDPOINT,
    user_agent="latent-art-bench/0.1 painter-feature-generation-v1 Cleveland metadata census",
    validate_config=validate_config,
    build_intents=build_intents,
    parse_response=parse_response,
    candidate_key=lambda row: row["cma_artwork_id"],
    sort_key=lambda row: (row["painter_id"], row["cma_artwork_id"]),
    summarize=summarize,
    limitations=[
        "Cleveland query rows are holding-record candidates, not reconciled physical works.",
        "share_license_status and rendition geometry are metadata, not delivery or rights "
        "receipts.",
        "No image endpoint or file was requested, no content label was assigned, and no work "
        "was admitted.",
        "Every other named Protocol 2.1 source route remains separately required.",
    ],
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    return engine.main(CONTRACT, DEFAULT_CONFIG, argv)
