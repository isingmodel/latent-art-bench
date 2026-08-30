from __future__ import annotations

import csv
import re
import subprocess
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

from latent_art_bench.config import ArtistConfig, CorpusConfig
from latent_art_bench.io import hash_file
from latent_art_bench.schemas import CorpusCandidateRecord

USER_AGENT = "latent-art-bench/0.1 (+https://github.com/isingmodel/latent-art-bench)"


class MuseumSourceError(RuntimeError):
    pass


class MuseumClient:
    """Small polite HTTP client with bounded retries for public collection APIs."""

    def __init__(self, timeout: float = 45.0, max_retries: int = 4) -> None:
        self.max_retries = max_retries
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json,image/*;q=0.9,*/*;q=0.1",
            },
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "MuseumClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_json(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response: Optional[httpx.Response] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)
            except httpx.HTTPError as exc:
                if attempt == self.max_retries:
                    raise MuseumSourceError(f"request failed for {url}: {exc}") from exc
                time.sleep(min(8.0, 2.0**attempt))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.max_retries:
                    retry_after = response.headers.get("retry-after")
                    try:
                        delay = float(retry_after) if retry_after else 2.0**attempt
                    except ValueError:
                        delay = 2.0**attempt
                    time.sleep(min(30.0, max(0.25, delay)))
                    continue
            break
        if response is None:
            raise MuseumSourceError(f"request produced no response for {url}")
        if not response.is_success:
            preview = response.text[:300].replace("\n", " ")
            raise MuseumSourceError(
                f"HTTP {response.status_code} from {response.url}: {preview}"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise MuseumSourceError(f"non-JSON response from {response.url}") from exc
        if not isinstance(payload, dict):
            raise MuseumSourceError(f"unexpected JSON response from {response.url}")
        return payload

    def get_bytes(self, url: str, max_bytes: int = 30 * 1024 * 1024) -> bytes:
        response: Optional[httpx.Response] = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(url, headers={"Accept": "image/*,*/*;q=0.1"})
            except httpx.HTTPError as exc:
                if attempt == self.max_retries:
                    raise MuseumSourceError(f"image request failed for {url}: {exc}") from exc
                time.sleep(min(8.0, 2.0**attempt))
                continue
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.max_retries:
                    time.sleep(min(15.0, 2.0**attempt))
                    continue
            break
        if response is None or not response.is_success:
            status = response.status_code if response is not None else "none"
            raise MuseumSourceError(f"image download returned HTTP {status}: {url}")
        content_type = response.headers.get("content-type", "").casefold()
        if content_type and "image" not in content_type and "octet-stream" not in content_type:
            raise MuseumSourceError(f"image URL returned {content_type or 'unknown type'}: {url}")
        if len(response.content) > max_bytes:
            raise MuseumSourceError(f"image exceeds {max_bytes} bytes: {url}")
        return response.content


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    collapsed = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return collapsed.casefold()


def _same_name(left: str, right: str) -> bool:
    return re.sub(r"[^a-z]+", " ", _normalized(left)).strip() == re.sub(
        r"[^a-z]+", " ", _normalized(right)
    ).strip()


def _int_or_none(value: object) -> Optional[int]:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _first_wikidata(values: Iterable[str]) -> Optional[str]:
    for value in values:
        match = re.search(r"(?:wiki/)?(Q\d+)$", value)
        if match:
            return match.group(1)
    return None


EXPLICIT_GENRE_TERMS = ("landscape", "seascape", "cityscape", "outdoor scene")
PLACE_TERMS = (
    "beach",
    "boulevard",
    "bridge",
    "canal",
    "cities",
    "cliff",
    "coast",
    "countryside",
    "field",
    "forest",
    "garden",
    "harbor",
    "harbour",
    "haystack",
    "hill",
    "lake",
    "meadow",
    "mountain",
    "orchard",
    "park",
    "path",
    "pond",
    "port",
    "quarry",
    "railway",
    "river",
    "road",
    "sea",
    "seine",
    "shore",
    "snow",
    "street",
    "town",
    "valley",
    "village",
    "water lilies",
    "wheat",
    "woods",
)
SCENE_TERMS = (
    "building",
    "cloud",
    "farm",
    "house",
    "outdoor",
    "sky",
    "tree",
    "water",
)
NON_LANDSCAPE_TITLE_TERMS = (
    "bather",
    "bathers",
    "interior",
    "madame",
    "portrait",
    "self-portrait",
    "still life",
    "woman",
    "women",
)


def _has_term(text: str, term: str) -> bool:
    normalized = _normalized(text)
    plural = r"(?:s|es)?" if " " not in term and not term.endswith("s") else ""
    return re.search(
        rf"(?<![a-z]){re.escape(term)}{plural}(?![a-z])", normalized
    ) is not None


def classify_landscape_candidate(
    title: str, subjects: Iterable[str], description: Optional[str]
) -> Tuple[int, List[str], str, str]:
    """Apply a source-blind metadata rule for the shared outdoor-place corpus view."""

    subject_text = " ".join(subjects)
    description_text = description or ""
    evidence: List[str] = []
    score = 0
    for term in EXPLICIT_GENRE_TERMS:
        if any(_has_term(text, term) for text in (title, subject_text, description_text)):
            score += 6
            evidence.append(f"explicit:{term}")
    for term in PLACE_TERMS:
        if _has_term(title, term):
            score += 3
            evidence.append(f"title:{term}")
        elif _has_term(subject_text, term):
            score += 3
            evidence.append(f"subject:{term}")
        elif _has_term(description_text, term):
            score += 1
            evidence.append(f"description:{term}")
    scene_hits = [term for term in SCENE_TERMS if _has_term(description_text, term)]
    if len(scene_hits) >= 2:
        score += min(3, len(scene_hits) - 1)
        evidence.append("description_scene:" + ",".join(scene_hits[:4]))
    if not evidence and any(_has_term(title, term) for term in NON_LANDSCAPE_TITLE_TERMS):
        score -= 4
        evidence.append("negative:title_subject")

    if score >= 3:
        return score, evidence, "include", "metadata supports landscape/outdoor-place eligibility"
    if score == 2:
        return score, evidence, "review", "borderline outdoor-place metadata requires review"
    return score, evidence, "exclude", "metadata does not support the frozen common genre"


def _candidate(**values: Any) -> CorpusCandidateRecord:
    score, evidence, decision, reason = classify_landscape_candidate(
        values["title"], values.get("subjects", []), values.get("description")
    )
    return CorpusCandidateRecord(
        **values,
        genre_score=score,
        genre_evidence=evidence,
        decision=decision,
        decision_reason=reason,
    )


def audit_aic(
    client: MuseumClient, artist: ArtistConfig, long_side: int
) -> List[CorpusCandidateRecord]:
    fields = ",".join(
        (
            "id",
            "title",
            "date_start",
            "date_end",
            "date_display",
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
        )
    )
    payload = client.get_json(
        "https://api.artic.edu/api/v1/artworks/search",
        params={
            "query[term][artist_id]": artist.authority_ids["aic_agent_id"],
            "limit": 100,
            "fields": fields,
        },
    )
    rows: List[CorpusCandidateRecord] = []
    for item in payload.get("data", []):
        if not _same_name(str(item.get("artist_title", "")), artist.artist_name):
            continue
        if not item.get("is_public_domain") or not item.get("image_id"):
            continue
        classification = " ".join(
            str(item.get(key) or "")
            for key in ("artwork_type_title", "classification_title", "medium_display")
        )
        if "paint" not in _normalized(classification) or "print" in _normalized(
            str(item.get("artwork_type_title") or "")
        ):
            continue
        image_id = str(item["image_id"])
        object_id = str(item["id"])
        thumbnail = item.get("thumbnail") or {}
        rows.append(
            _candidate(
                source_id="aic",
                source_object_id=object_id,
                artist_id=artist.artist_id,
                artist_name=artist.artist_name,
                title=str(item.get("title") or f"AIC object {object_id}"),
                creation_year=_int_or_none(item.get("date_start")),
                creation_year_text=str(item.get("date_display") or "") or None,
                classification=str(item.get("artwork_type_title") or "Painting"),
                medium=str(item.get("medium_display") or "") or None,
                source_url=f"https://www.artic.edu/artworks/{object_id}",
                image_url=(
                    f"https://www.artic.edu/iiif/2/{image_id}/full/{long_side},/0/default.jpg"
                ),
                image_width=_int_or_none(thumbnail.get("width")),
                image_height=_int_or_none(thumbnail.get("height")),
                rights_basis=(
                    "AIC is_public_domain=true; collection metadata CC0; "
                    "public-domain IIIF image"
                ),
                subjects=[str(value) for value in (item.get("subject_titles") or [])],
                description=str(thumbnail.get("alt_text") or "") or None,
                catalog_ids={
                    "aic": object_id,
                    "aic_accession": str(item.get("main_reference_number") or ""),
                },
            )
        )
    return rows


def audit_cma(client: MuseumClient, artist: ArtistConfig) -> List[CorpusCandidateRecord]:
    payload = client.get_json(
        "https://openaccess-api.clevelandart.org/api/artworks/",
        params={"artists": artist.artist_name, "limit": 100, "has_image": 1},
    )
    rows: List[CorpusCandidateRecord] = []
    expected_creator = artist.authority_ids.get("cma_creator_id")
    for item in payload.get("data", []):
        creators = item.get("creators") or []
        if not any(
            str(creator.get("id")) == expected_creator and creator.get("role") == "artist"
            for creator in creators
        ):
            continue
        if item.get("share_license_status") != "CC0" or item.get("type") != "Painting":
            continue
        image = (item.get("images") or {}).get("web") or {}
        if not image.get("url"):
            continue
        object_id = str(item["id"])
        external = item.get("external_resources") or {}
        alternate_urls = [
            str((alternate.get("web") or {}).get("url"))
            for alternate in (item.get("alternate_images") or [])
            if (alternate.get("web") or {}).get("url")
        ]
        description_parts = [
            str(item.get(key) or "")
            for key in ("description", "artlens_description", "did_you_know", "tombstone")
        ]
        rows.append(
            _candidate(
                source_id="cma",
                source_object_id=object_id,
                artist_id=artist.artist_id,
                artist_name=artist.artist_name,
                title=str(item.get("title") or f"CMA object {object_id}"),
                creation_year=_int_or_none(item.get("creation_date_earliest")),
                creation_year_text=str(item.get("creation_date") or "") or None,
                classification="Painting",
                medium=str(item.get("technique") or "") or None,
                source_url=str(
                    item.get("url")
                    or f"https://www.clevelandart.org/art/{item.get('accession_number')}"
                ),
                image_url=str(image["url"]),
                image_width=_int_or_none(image.get("width")),
                image_height=_int_or_none(image.get("height")),
                rights_basis="Cleveland Museum of Art share_license_status=CC0",
                subjects=[],
                description=" ".join(part for part in description_parts if part) or None,
                catalog_ids={
                    "cma": object_id,
                    "cma_accession": str(item.get("accession_number") or ""),
                },
                wikidata_id=_first_wikidata(external.get("wikidata") or []),
                alternate_image_urls=alternate_urls,
            )
        )
    return rows


def audit_met(client: MuseumClient, artist: ArtistConfig) -> List[CorpusCandidateRecord]:
    search = client.get_json(
        "https://collectionapi.metmuseum.org/public/collection/v1/search",
        params={"hasImages": "true", "artistOrCulture": "true", "q": artist.artist_name},
    )
    rows: List[CorpusCandidateRecord] = []
    for object_id_value in search.get("objectIDs") or []:
        item = client.get_json(
            f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id_value}"
        )
        time.sleep(0.09)
        if not _same_name(str(item.get("artistDisplayName") or ""), artist.artist_name):
            continue
        if not item.get("isPublicDomain") or not item.get("primaryImageSmall"):
            continue
        classification = " ".join(
            str(item.get(key) or "") for key in ("objectName", "classification", "medium")
        )
        if "paint" not in _normalized(classification) or "print" in _normalized(
            str(item.get("objectName") or "")
        ):
            continue
        object_id = str(item["objectID"])
        wikidata_url = str(item.get("objectWikidata_URL") or "")
        tags = [str(tag.get("term")) for tag in (item.get("tags") or []) if tag.get("term")]
        rows.append(
            _candidate(
                source_id="met",
                source_object_id=object_id,
                artist_id=artist.artist_id,
                artist_name=artist.artist_name,
                title=str(item.get("title") or f"Met object {object_id}"),
                creation_year=_int_or_none(item.get("objectBeginDate")),
                creation_year_text=str(item.get("objectDate") or "") or None,
                classification=str(
                    item.get("classification") or item.get("objectName") or "Painting"
                ),
                medium=str(item.get("medium") or "") or None,
                source_url=str(
                    item.get("objectURL")
                    or f"https://www.metmuseum.org/art/collection/search/{object_id}"
                ),
                image_url=str(item["primaryImageSmall"]),
                rights_basis="Metropolitan Museum of Art isPublicDomain=true; Open Access image",
                subjects=tags,
                description=" ".join(tags) or None,
                catalog_ids={
                    "met": object_id,
                    "met_accession": str(item.get("accessionNumber") or ""),
                },
                wikidata_id=_first_wikidata([wikidata_url]),
                alternate_image_urls=[str(value) for value in (item.get("additionalImages") or [])],
            )
        )
    return rows


def _chunks(values: List[str], size: int = 40) -> Iterable[List[str]]:
    for index in range(0, len(values), size):
        yield values[index : index + size]


def _wikidata_commons_images(
    client: MuseumClient, wikidata_ids: List[str], long_side: int
) -> Dict[str, Dict[str, Any]]:
    filename_by_entity: Dict[str, str] = {}
    for batch in _chunks(wikidata_ids):
        payload = client.get_json(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbgetentities",
                "ids": "|".join(batch),
                "props": "claims",
                "format": "json",
                "origin": "*",
            },
        )
        for entity_id, entity in (payload.get("entities") or {}).items():
            claims = entity.get("claims") or {}
            image_claims = claims.get("P18") or []
            if not image_claims:
                continue
            try:
                filename = image_claims[0]["mainsnak"]["datavalue"]["value"]
            except (KeyError, TypeError):
                continue
            if isinstance(filename, str) and filename:
                filename_by_entity[entity_id] = filename

    result: Dict[str, Dict[str, Any]] = {}
    entities_by_title = {f"File:{name}": entity for entity, name in filename_by_entity.items()}
    titles = list(entities_by_title)
    for batch in _chunks(titles):
        payload = client.get_json(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": long_side,
                "format": "json",
                "origin": "*",
            },
        )
        normalized_titles = {
            row["to"]: row["from"] for row in (payload.get("query", {}).get("normalized") or [])
        }
        for page in (payload.get("query", {}).get("pages") or {}).values():
            title = str(page.get("title") or "")
            original_title = normalized_titles.get(title, title)
            entity_id = entities_by_title.get(original_title) or entities_by_title.get(title)
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
            result[entity_id] = {
                "url": info.get("thumburl") or info.get("url"),
                "width": info.get("thumbwidth") or info.get("width"),
                "height": info.get("thumbheight") or info.get("height"),
                "license": license_name or usage_terms,
                "description_url": info.get("descriptionurl"),
                "filename": filename_by_entity[entity_id],
            }
    return result


def audit_met_open_data(
    client: MuseumClient,
    artist: ArtistConfig,
    csv_path: Path,
    expected_sha256: str,
    long_side: int,
) -> List[CorpusCandidateRecord]:
    if not csv_path.is_file():
        raise MuseumSourceError(f"missing Met Open Access CSV: {csv_path}")
    actual_sha256 = hash_file(csv_path)
    if actual_sha256 != expected_sha256:
        raise MuseumSourceError(
            f"Met Open Access CSV hash mismatch: expected {expected_sha256}, found {actual_sha256}"
        )

    raw_rows: List[Dict[str, str]] = []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if not _same_name(row.get("Artist Display Name", ""), artist.artist_name):
                continue
            if row.get("Is Public Domain") != "True" or not row.get("Object Wikidata URL"):
                continue
            classification = " ".join(
                row.get(key, "") for key in ("Object Name", "Classification", "Medium")
            )
            if "paint" not in _normalized(classification) or "print" in _normalized(
                row.get("Object Name", "")
            ):
                continue
            raw_rows.append(row)

    entity_ids = [
        value
        for value in (_first_wikidata([row["Object Wikidata URL"]]) for row in raw_rows)
        if value
    ]
    images = _wikidata_commons_images(client, entity_ids, long_side)
    rows: List[CorpusCandidateRecord] = []
    for item in raw_rows:
        wikidata_id = _first_wikidata([item["Object Wikidata URL"]])
        image = images.get(wikidata_id or "")
        if wikidata_id is None or image is None or not image.get("url"):
            continue
        object_id = item["Object ID"]
        subjects = [value for value in item.get("Tags", "").split("|") if value]
        rows.append(
            _candidate(
                source_id="met",
                source_object_id=object_id,
                artist_id=artist.artist_id,
                artist_name=artist.artist_name,
                title=item.get("Title") or f"Met object {object_id}",
                creation_year=_int_or_none(item.get("Object Begin Date")),
                creation_year_text=item.get("Object Date") or None,
                classification=item.get("Classification") or item.get("Object Name") or "Painting",
                medium=item.get("Medium") or None,
                source_url=item.get("Link Resource")
                or f"https://www.metmuseum.org/art/collection/search/{object_id}",
                image_url=str(image["url"]),
                image_width=_int_or_none(image.get("width")),
                image_height=_int_or_none(image.get("height")),
                rights_basis=(
                    "Met Open Access CSV Is Public Domain=True; Wikimedia Commons "
                    f"P18 delivery license={image.get('license') or 'verified open license'}"
                ),
                subjects=subjects,
                description=" ".join(subjects) or None,
                catalog_ids={
                    "met": object_id,
                    "met_accession": item.get("Object Number", ""),
                    "commons_file": str(image.get("filename") or ""),
                },
                wikidata_id=wikidata_id,
            )
        )
    return rows


def _verify_nga_revision(data_dir: Path, expected_revision: str) -> None:
    repository = data_dir.parent
    if not (repository / ".git").is_dir():
        return
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repository),
        capture_output=True,
        text=True,
        check=True,
    )
    actual = result.stdout.strip()
    if actual != expected_revision:
        raise MuseumSourceError(
            f"NGA data revision mismatch: expected {expected_revision}, found {actual}"
        )


def audit_nga(
    artist: ArtistConfig, data_dir: Path, expected_revision: str, long_side: int
) -> List[CorpusCandidateRecord]:
    required = {
        "objects": data_dir / "objects.csv",
        "links": data_dir / "objects_constituents.csv",
        "images": data_dir / "published_images.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise MuseumSourceError("missing NGA open-data CSV files: " + ", ".join(missing))
    _verify_nga_revision(data_dir, expected_revision)

    constituent_id = artist.authority_ids["nga_constituent_id"]
    object_ids = set()
    with required["links"].open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["constituentid"] == constituent_id and row["roletype"] == "artist":
                object_ids.add(row["objectid"])

    objects: Dict[str, Dict[str, str]] = {}
    with required["objects"].open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["objectid"] in object_ids and row["classification"].casefold() == "painting":
                objects[row["objectid"]] = row

    primary_images: Dict[str, Dict[str, str]] = {}
    alternates: Dict[str, List[str]] = defaultdict(list)
    with required["images"].open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            object_id = row["depictstmsobjectid"]
            if object_id not in objects or row["openaccess"] != "1":
                continue
            iiif = row["iiifurl"].rstrip("/")
            url = f"{iiif}/full/!{long_side},{long_side}/0/default.jpg"
            if row["viewtype"] == "primary" and object_id not in primary_images:
                primary_images[object_id] = {**row, "download_url": url}
            elif row["viewtype"] != "primary":
                alternates[object_id].append(url)

    rows: List[CorpusCandidateRecord] = []
    for object_id, item in objects.items():
        image = primary_images.get(object_id)
        if image is None:
            continue
        rows.append(
            _candidate(
                source_id="nga",
                source_object_id=object_id,
                artist_id=artist.artist_id,
                artist_name=artist.artist_name,
                title=item["title"] or f"NGA object {object_id}",
                creation_year=_int_or_none(item.get("beginyear")),
                creation_year_text=item.get("displaydate") or None,
                classification=item.get("classification") or "Painting",
                medium=item.get("medium") or None,
                source_url=f"https://www.nga.gov/artworks/{object_id}",
                image_url=image["download_url"],
                image_width=_int_or_none(image.get("width")),
                image_height=_int_or_none(image.get("height")),
                rights_basis="NGA published_images openaccess=1; NGA Open Access image",
                subjects=[],
                description=image.get("assistivetext") or None,
                catalog_ids={"nga": object_id, "nga_accession": item.get("accessionnum", "")},
                wikidata_id=item.get("wikidataid") or None,
                alternate_image_urls=alternates.get(object_id, []),
            )
        )
    return rows


def audit_museum_sources(
    config: CorpusConfig,
    nga_data_dir: Path,
    met_csv_path: Path,
    client: Optional[MuseumClient] = None,
) -> List[CorpusCandidateRecord]:
    owns_client = client is None
    client = client or MuseumClient()
    try:
        rows: List[CorpusCandidateRecord] = []
        for artist in config.selected_artists:
            rows.extend(audit_aic(client, artist, config.aic_image_width))
            rows.extend(audit_cma(client, artist))
            rows.extend(
                audit_met_open_data(
                    client,
                    artist,
                    met_csv_path,
                    config.met_open_data_sha256,
                    config.image_long_side,
                )
            )
            rows.extend(
                audit_nga(
                    artist,
                    nga_data_dir,
                    config.nga_open_data_revision,
                    config.image_long_side,
                )
            )
        return sorted(
            rows,
            key=lambda row: (row.artist_id, row.source_id, row.title, row.source_object_id),
        )
    finally:
        if owns_client:
            client.close()
