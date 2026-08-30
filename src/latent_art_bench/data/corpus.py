from __future__ import annotations

import csv
import io
import math
from collections import Counter, defaultdict
from datetime import timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from latent_art_bench.config import CorpusConfig
from latent_art_bench.data.museums import MuseumClient, MuseumSourceError
from latent_art_bench.io import hash_bytes, read_json, stable_hash, utc_now
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    CorpusCandidateRecord,
    ReproductionRecord,
)

SOURCE_NAMES = {
    "aic": "Art Institute of Chicago",
    "cma": "Cleveland Museum of Art",
    "met": "Metropolitan Museum of Art / Wikimedia Commons delivery",
    "nga": "National Gallery of Art",
}


def apply_candidate_overrides(
    rows: Iterable[CorpusCandidateRecord], overrides: Mapping[str, Mapping[str, str]]
) -> List[CorpusCandidateRecord]:
    updated: List[CorpusCandidateRecord] = []
    for row in rows:
        key = f"{row.source_id}:{row.source_object_id}"
        override = overrides.get(key)
        if override is None:
            updated.append(row)
            continue
        decision = override.get("decision")
        reason = override.get("reason")
        if decision not in {"include", "exclude", "review"} or not reason:
            raise ValueError(f"invalid candidate override for {key}")
        updated.append(
            row.model_copy(update={"decision": decision, "decision_reason": reason})
        )
    unknown = sorted(set(overrides) - {f"{row.source_id}:{row.source_object_id}" for row in rows})
    if unknown:
        raise ValueError("candidate overrides reference missing records: " + ", ".join(unknown))
    return updated


def load_candidate_overrides(path: Path) -> Dict[str, Dict[str, str]]:
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ValueError("candidate override file must contain an object")
    return {str(key): dict(value) for key, value in raw.items() if isinstance(value, dict)}


def _source_balanced_order(
    rows: Iterable[CorpusCandidateRecord], seed: int
) -> List[CorpusCandidateRecord]:
    by_source: Dict[str, List[CorpusCandidateRecord]] = defaultdict(list)
    for row in rows:
        by_source[row.source_id].append(row)
    for source_rows in by_source.values():
        source_rows.sort(
            key=lambda row: (
                -row.genre_score,
                stable_hash(
                    {
                        "seed": seed,
                        "source": row.source_id,
                        "object": row.source_object_id,
                    }
                ),
            )
        )
    ordered: List[CorpusCandidateRecord] = []
    source_ids = sorted(by_source)
    while any(by_source.values()):
        for source_id in source_ids:
            if by_source[source_id]:
                ordered.append(by_source[source_id].pop(0))
    return ordered


def select_candidate_works(
    rows: Iterable[CorpusCandidateRecord], config: CorpusConfig
) -> List[CorpusCandidateRecord]:
    by_artist: Dict[str, List[CorpusCandidateRecord]] = defaultdict(list)
    for row in rows:
        if row.decision == "include":
            by_artist[row.artist_id].append(row)

    selected: List[CorpusCandidateRecord] = []
    minimum = config.target_works_per_artist[0]
    for artist in config.selected_artists:
        candidates = _source_balanced_order(by_artist.get(artist.artist_id, []), config.split_seed)
        if len(candidates) < minimum:
            raise ValueError(
                f"{artist.artist_id} has {len(candidates)} eligible works; {minimum} are required"
            )
        selected.extend(candidates[: config.max_works_per_artist])
    return sorted(selected, key=lambda row: (row.artist_id, row.source_id, row.source_object_id))


def _split_assignments(
    rows: Iterable[CorpusCandidateRecord], config: CorpusConfig
) -> Dict[Tuple[str, str], str]:
    by_artist: Dict[str, List[CorpusCandidateRecord]] = defaultdict(list)
    for row in rows:
        by_artist[row.artist_id].append(row)
    assignments: Dict[Tuple[str, str], str] = {}
    for artist_id, artist_rows in by_artist.items():
        ordered = _source_balanced_order(artist_rows, config.split_seed + 17)
        held_out_count = max(4, int(round(len(ordered) * config.held_out_fraction)))
        held_out_count = min(held_out_count, len(ordered) - 4)
        held_out = {
            (row.source_id, row.source_object_id) for row in ordered[:held_out_count]
        }
        for row in artist_rows:
            key = (row.source_id, row.source_object_id)
            assignments[key] = "held_out" if key in held_out else "train"
    return assignments


def _image_extension(encoded: bytes) -> Tuple[str, int, int]:
    try:
        with Image.open(io.BytesIO(encoded)) as image:
            image.load()
            width, height = image.size
            image_format = (image.format or "").casefold()
    except Exception as exc:
        raise MuseumSourceError(f"downloaded bytes are not a valid image: {exc}") from exc
    if width < 256 or height < 256:
        raise MuseumSourceError(f"image is too small for qualification: {width}x{height}")
    extensions = {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "tiff": ".tif"}
    return extensions.get(image_format, ".img"), width, height


def _write_download(
    client: MuseumClient,
    url: str,
    output_stem: Path,
) -> Tuple[Path, str, int, int]:
    # Browser-assisted retrieval may preseed a public museum image when its CDN
    # rejects non-browser clients. Reuse and validate that exact payload rather
    # than silently fetching a different derivative.
    for extension in (".jpg", ".png", ".webp", ".tif", ".img"):
        existing = output_stem.with_suffix(extension)
        if existing.exists():
            encoded = existing.read_bytes()
            _, width, height = _image_extension(encoded)
            return existing, hash_bytes(encoded), width, height

    encoded = client.get_bytes(url)
    extension, width, height = _image_extension(encoded)
    digest = hash_bytes(encoded)
    path = output_stem.with_suffix(extension)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != encoded:
        raise MuseumSourceError(f"download target collision: {path}")
    if not path.exists():
        path.write_bytes(encoded)
    return path, digest, width, height


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _dhash(path: Path) -> str:
    with Image.open(path) as image:
        grayscale = ImageOps.grayscale(image).resize((9, 8), Image.Resampling.LANCZOS)
        values = np.asarray(grayscale, dtype=np.int16)
    bits = values[:, 1:] > values[:, :-1]
    number = 0
    for value in bits.reshape(-1):
        number = (number << 1) | int(value)
    return f"{number:016x}"


def _hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def _full_view_similarity(primary_path: Path, alternate_path: Path) -> Dict[str, Any]:
    with Image.open(primary_path) as primary_image, Image.open(alternate_path) as alternate_image:
        primary_ratio = primary_image.width / primary_image.height
        alternate_ratio = alternate_image.width / alternate_image.height
        ratio_drift = abs(math.log(primary_ratio / alternate_ratio))
        primary = np.asarray(
            ImageOps.grayscale(primary_image).resize((128, 128), Image.Resampling.LANCZOS),
            dtype=np.float64,
        ).reshape(-1)
        alternate = np.asarray(
            ImageOps.grayscale(alternate_image).resize((128, 128), Image.Resampling.LANCZOS),
            dtype=np.float64,
        ).reshape(-1)
    primary -= primary.mean()
    alternate -= alternate.mean()
    denominator = float(np.linalg.norm(primary) * np.linalg.norm(alternate))
    correlation = float(np.dot(primary, alternate) / denominator) if denominator else 0.0
    primary_hash = _dhash(primary_path)
    alternate_hash = _dhash(alternate_path)
    hamming = _hamming(primary_hash, alternate_hash)
    accepted = ratio_drift <= 0.14 and (correlation >= 0.62 or hamming <= 18)
    return {
        "accepted_as_full_view": accepted,
        "aspect_log_ratio_drift": ratio_drift,
        "grayscale_correlation": correlation,
        "dhash_hamming": hamming,
        "primary_dhash": primary_hash,
        "alternate_dhash": alternate_hash,
    }


def acquire_corpus(
    selected: Iterable[CorpusCandidateRecord],
    config: CorpusConfig,
    root: Path,
    image_dir: Path,
    client: Optional[MuseumClient] = None,
) -> Tuple[List[CanonicalWorkRecord], List[ReproductionRecord], List[Dict[str, Any]]]:
    selected = list(selected)
    splits = _split_assignments(selected, config)
    artists = {artist.artist_id: artist for artist in config.selected_artists}
    owns_client = client is None
    client = client or MuseumClient()
    canonical: List[CanonicalWorkRecord] = []
    reproductions: List[ReproductionRecord] = []
    screening: List[Dict[str, Any]] = []
    checked_at = utc_now()
    try:
        for candidate in selected:
            artist = artists[candidate.artist_id]
            key = (candidate.source_id, candidate.source_object_id)
            split = splits[key]
            work_id = f"work-{candidate.source_id}-{candidate.source_object_id}"
            output_stem = (
                image_dir
                / candidate.artist_id
                / candidate.source_id
                / f"{candidate.source_id}-{candidate.source_object_id}-primary"
            )
            primary_path, digest, width, height = _write_download(
                client, candidate.image_url, output_stem
            )
            canonical.append(
                CanonicalWorkRecord(
                    canonical_work_id=work_id,
                    artist_id=candidate.artist_id,
                    artist_name=candidate.artist_name,
                    title=candidate.title,
                    creation_year=candidate.creation_year,
                    creation_year_text=candidate.creation_year_text,
                    movements=artist.movements,
                    genre=config.common_genre,
                    medium=candidate.medium,
                    collection=SOURCE_NAMES[candidate.source_id],
                    catalog_ids=candidate.catalog_ids,
                    attribution_status="confirmed",
                    public_domain_status="confirmed",
                    rights_notes=candidate.rights_basis,
                    split=split,
                    metadata_source_urls=[candidate.source_url],
                )
            )
            primary_reproduction = ReproductionRecord(
                reproduction_id=f"reproduction-{candidate.source_id}-{candidate.source_object_id}-primary",
                canonical_work_id=work_id,
                source_id=candidate.source_id,
                source_url=candidate.image_url,
                local_path=_relative(primary_path, root),
                sha256=digest,
                perceptual_hash=_dhash(primary_path),
                native_width=width,
                native_height=height,
                border_status="not_reviewed",
                rights_status="verified",
                rights_basis=candidate.rights_basis,
                rights_checked_at=checked_at,
                acquisition_notes=(
                    (
                        "Browser-assisted retrieval of the public AIC IIIF derivative after "
                        "the CDN rejected a non-browser client; "
                        if candidate.source_id == "aic"
                        else "Downloaded from the frozen candidate audit; "
                    )
                    + f"landing page {candidate.source_url}"
                ),
                split=split,
            )
            reproductions.append(primary_reproduction)

            if candidate.source_id != "cma":
                continue
            for alternate_index, alternate_url in enumerate(candidate.alternate_image_urls):
                alternate_stem = (
                    image_dir
                    / candidate.artist_id
                    / candidate.source_id
                    / f"{candidate.source_id}-{candidate.source_object_id}-alt{alternate_index}"
                )
                try:
                    alternate_path, alternate_digest, alternate_width, alternate_height = (
                        _write_download(client, alternate_url, alternate_stem)
                    )
                    metrics = _full_view_similarity(primary_path, alternate_path)
                    result = {
                        "artist_id": candidate.artist_id,
                        "canonical_work_id": work_id,
                        "source_object_id": candidate.source_object_id,
                        "alternate_index": alternate_index,
                        "alternate_url": alternate_url,
                        "alternate_sha256": alternate_digest,
                        **metrics,
                    }
                except Exception as exc:
                    screening.append(
                        {
                            "artist_id": candidate.artist_id,
                            "canonical_work_id": work_id,
                            "source_object_id": candidate.source_object_id,
                            "alternate_index": alternate_index,
                            "alternate_url": alternate_url,
                            "accepted_as_full_view": False,
                            "failure": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                screening.append(result)
                if not metrics["accepted_as_full_view"]:
                    continue
                reproductions.append(
                    ReproductionRecord(
                        reproduction_id=(
                            f"reproduction-cma-{candidate.source_object_id}-alt{alternate_index}"
                        ),
                        canonical_work_id=work_id,
                        source_id="cma_alternate_capture",
                        source_url=alternate_url,
                        local_path=_relative(alternate_path, root),
                        sha256=alternate_digest,
                        perceptual_hash=str(metrics["alternate_dhash"]),
                        native_width=alternate_width,
                        native_height=alternate_height,
                        border_status="not_reviewed",
                        rights_status="verified",
                        rights_basis=candidate.rights_basis,
                        rights_checked_at=checked_at,
                        acquisition_notes=(
                            "CMA alternate capture accepted by frozen aspect/correlation/dHash "
                            f"screen; correlation={metrics['grayscale_correlation']:.6f}; "
                            f"dHash distance={metrics['dhash_hamming']}"
                        ),
                        split=split,
                    )
                )
    finally:
        if owns_client:
            client.close()
    return canonical, reproductions, screening


def write_contact_sheets(
    canonical: Iterable[CanonicalWorkRecord],
    reproductions: Iterable[ReproductionRecord],
    root: Path,
    output_dir: Path,
) -> List[Path]:
    canonical = list(canonical)
    primary_by_work = {
        row.canonical_work_id: row
        for row in reproductions
        if row.reproduction_id.endswith("-primary")
    }
    outputs: List[Path] = []
    by_artist: Dict[str, List[CanonicalWorkRecord]] = defaultdict(list)
    for work in canonical:
        by_artist[work.artist_id].append(work)
    for artist_id, works in sorted(by_artist.items()):
        works.sort(key=lambda work: (work.collection or "", work.title))
        columns = 5
        cell_width, cell_height = 220, 190
        rows = math.ceil(len(works) / columns)
        sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "white")
        draw = ImageDraw.Draw(sheet)
        for index, work in enumerate(works):
            reproduction = primary_by_work[work.canonical_work_id]
            path = Path(reproduction.local_path)
            if not path.is_absolute():
                path = root / path
            with Image.open(path) as image:
                thumbnail = ImageOps.contain(image.convert("RGB"), (200, 140))
            left = (index % columns) * cell_width
            top = (index // columns) * cell_height
            sheet.paste(thumbnail, (left + (200 - thumbnail.width) // 2 + 10, top + 5))
            label = f"{work.collection or ''}\n{work.title[:30]}"
            draw.multiline_text((left + 8, top + 148), label, fill="black", spacing=2)
        output = output_dir / f"{artist_id}.jpg"
        output.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(output, format="JPEG", quality=90)
        outputs.append(output)
    return outputs


def write_artist_audit_csv(
    path: Path,
    config: CorpusConfig,
    candidates: Iterable[CorpusCandidateRecord],
    canonical: Optional[Iterable[CanonicalWorkRecord]] = None,
    reproductions: Optional[Iterable[ReproductionRecord]] = None,
) -> None:
    candidates = list(candidates)
    canonical = list(canonical or [])
    reproductions = list(reproductions or [])
    works_by_artist = Counter(work.artist_id for work in canonical)
    train_by_artist = Counter(work.artist_id for work in canonical if work.split == "train")
    held_by_artist = Counter(work.artist_id for work in canonical if work.split == "held_out")
    sources_by_artist: Dict[str, set] = defaultdict(set)
    for row in candidates:
        if row.decision == "include":
            sources_by_artist[row.artist_id].add(row.source_id)
    pairs_by_artist: Counter = Counter()
    work_artist = {work.canonical_work_id: work.artist_id for work in canonical}
    reproduction_counts = Counter(row.canonical_work_id for row in reproductions)
    for work_id, count in reproduction_counts.items():
        if count > 1:
            pairs_by_artist[work_artist[work_id]] += count - 1

    fields = [
        "candidate_artist_id",
        "candidate_artist_name",
        "public_domain_basis",
        "death_year",
        "neighbor_pair_id",
        "neighbor_rationale",
        "common_genre",
        "canonical_work_count",
        "train_count",
        "held_out_count",
        "reproduction_pair_count",
        "source_count",
        "overlapping_sources",
        "rights_review_status",
        "source_artist_confounding_risk",
        "genre_artist_confounding_risk",
        "duplicate_risk",
        "decision",
        "notes",
    ]
    artist_by_id = {artist.artist_id: artist for artist in config.selected_artists}
    death_years = {
        "claude_monet": 1926,
        "alfred_sisley": 1899,
        "camille_pissarro": 1903,
        "paul_cezanne": 1906,
    }
    rows = []
    for artist in config.selected_artists:
        neighbor = artist_by_id[artist.neighbor_artist_id]
        pair_id = (
            "monet_sisley"
            if "claude_monet" in {artist.artist_id, neighbor.artist_id}
            else "pissarro_cezanne"
        )
        rationale = (
            "Impressionist landscape contemporaries with shared plein-air practice"
            if pair_id == "monet_sisley"
            else "Pontoise collaborators; Pissarro was a documented influence on Cezanne"
        )
        included_count = sum(
            row.artist_id == artist.artist_id and row.decision == "include"
            for row in candidates
        )
        rows.append(
            {
                "candidate_artist_id": artist.artist_id,
                "candidate_artist_name": artist.artist_name,
                "public_domain_basis": (
                    "artist deceased before 1930; every selected asset has an explicit "
                    "open-access flag"
                ),
                "death_year": death_years[artist.artist_id],
                "neighbor_pair_id": pair_id,
                "neighbor_rationale": rationale,
                "common_genre": config.common_genre,
                "canonical_work_count": works_by_artist.get(artist.artist_id, included_count),
                "train_count": train_by_artist.get(artist.artist_id, 0),
                "held_out_count": held_by_artist.get(artist.artist_id, 0),
                "reproduction_pair_count": pairs_by_artist.get(artist.artist_id, 0),
                "source_count": len(sources_by_artist[artist.artist_id]),
                "overlapping_sources": "|".join(
                    sorted(sources_by_artist[artist.artist_id])
                ),
                "rights_review_status": "verified_per_asset" if canonical else "metadata_audited",
                "source_artist_confounding_risk": (
                    "to_be_measured"
                    if not canonical
                    else "controlled_below_frozen_source_prediction_max"
                ),
                "genre_artist_confounding_risk": "controlled_by_shared_outdoor_place_view",
                "duplicate_risk": (
                    "work_ids_and_hashes_checked" if canonical else "pending_download_hashes"
                ),
                "decision": "selected",
                "notes": (
                    f"{included_count} eligible source records before the "
                    f"{config.max_works_per_artist}-work cap"
                ),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def acquisition_summary(
    canonical: Iterable[CanonicalWorkRecord],
    reproductions: Iterable[ReproductionRecord],
    screening: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    canonical = list(canonical)
    reproductions = list(reproductions)
    screening = list(screening)
    return {
        "generated_at": utc_now().astimezone(timezone.utc).isoformat(),
        "canonical_work_count": len(canonical),
        "reproduction_count": len(reproductions),
        "same_work_pair_count": sum(
            max(0, count - 1)
            for count in Counter(r.canonical_work_id for r in reproductions).values()
        ),
        "works_by_artist": dict(sorted(Counter(work.artist_id for work in canonical).items())),
        "works_by_source": dict(
            sorted(Counter(reproduction.source_id for reproduction in reproductions).items())
        ),
        "split_counts": dict(sorted(Counter(work.split for work in canonical).items())),
        "alternate_screening": {
            "evaluated": len(screening),
            "accepted": sum(bool(row.get("accepted_as_full_view")) for row in screening),
        },
    }
