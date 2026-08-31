"""Deterministic construction and validation of the balanced pilot_2 atlas."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image

from latent_art_bench.io import hash_file, read_jsonl, stable_hash
from latent_art_bench.pilot2.config import Pilot2CorpusConfig
from latent_art_bench.pilot2.schemas import Pilot2AcquiredImage, Pilot2AtlasWork
from latent_art_bench.schemas import CorpusCandidateRecord


def pilot2_selection_digest(namespace: str, canonical_work_id: str) -> str:
    """Hash ``pilot2-v1|20260901|`` followed by the original work ID."""

    payload = f"{namespace}|{canonical_work_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def select_pilot2_atlas(
    candidates: Iterable[CorpusCandidateRecord], config: Pilot2CorpusConfig
) -> List[Pilot2AtlasWork]:
    """Select exactly five works per artist/source, then assign 3/2 splits.

    Only rows already marked ``include`` in the frozen candidate audit enter
    selection.  The lowest SHA-256 keys win, so input order cannot affect the
    atlas and no visual or outcome-based choice is possible.
    """

    by_cell: Dict[Tuple[str, str], List[Tuple[str, CorpusCandidateRecord]]] = defaultdict(list)
    allowed_artists = set(config.artist_ids)
    allowed_sources = set(config.source_ids)
    for candidate in candidates:
        if (
            candidate.decision != "include"
            or candidate.artist_id not in allowed_artists
            or candidate.source_id not in allowed_sources
        ):
            continue
        if candidate.image_width is None or candidate.image_height is None:
            continue
        if candidate.image_width * candidate.image_height <= 410 * 410:
            continue
        if max(candidate.image_width, candidate.image_height) / min(
            candidate.image_width, candidate.image_height
        ) >= 2.0:
            continue
        canonical_work_id = f"work-{candidate.source_id}-{candidate.source_object_id}"
        digest = pilot2_selection_digest(config.selection_namespace, canonical_work_id)
        by_cell[(candidate.artist_id, candidate.source_id)].append((digest, candidate))

    selected: List[Pilot2AtlasWork] = []
    for artist_id in sorted(config.artist_ids):
        for source_id in sorted(config.source_ids):
            rows = sorted(
                by_cell.get((artist_id, source_id), []),
                key=lambda item: (item[0], item[1].source_object_id),
            )
            if len(rows) < config.works_per_artist_source:
                raise ValueError(
                    f"pilot_2 atlas cell {artist_id}/{source_id} has {len(rows)} "
                    f"eligible works; {config.works_per_artist_source} are required"
                )
            for zero_index, (digest, candidate) in enumerate(
                rows[: config.works_per_artist_source]
            ):
                rank = zero_index + 1
                split = "train" if rank <= config.train_per_artist_source else "held_out"
                selected.append(
                    Pilot2AtlasWork(
                        canonical_work_id=(
                            f"work-{candidate.source_id}-{candidate.source_object_id}"
                        ),
                        artist_id=candidate.artist_id,
                        artist_name=candidate.artist_name,
                        source_id=candidate.source_id,
                        source_object_id=candidate.source_object_id,
                        title=candidate.title,
                        image_url=candidate.image_url,
                        source_url=candidate.source_url,
                        native_width=candidate.image_width,
                        native_height=candidate.image_height,
                        split=split,
                        selection_rank=rank,
                        selection_digest=digest,
                        selection_namespace=config.selection_namespace,
                    )
                )
    validate_pilot2_atlas(selected, config)
    return sorted(
        selected,
        key=lambda row: (row.artist_id, row.source_id, row.selection_rank),
    )


def build_pilot2_atlas(path: Path, config: Pilot2CorpusConfig) -> List[Pilot2AtlasWork]:
    candidates = [CorpusCandidateRecord.model_validate(row) for row in read_jsonl(Path(path))]
    return select_pilot2_atlas(candidates, config)


def validate_pilot2_atlas(
    rows: Sequence[Pilot2AtlasWork], config: Pilot2CorpusConfig
) -> None:
    if len(rows) != 40:
        raise ValueError(f"pilot_2 atlas must contain exactly 40 works, found {len(rows)}")
    work_ids = [row.canonical_work_id for row in rows]
    if len(work_ids) != len(set(work_ids)):
        raise ValueError("pilot_2 atlas contains duplicate canonical work identifiers")
    object_keys = [(row.source_id, row.source_object_id) for row in rows]
    if len(object_keys) != len(set(object_keys)):
        raise ValueError("pilot_2 atlas contains duplicate source objects")

    counts = Counter((row.artist_id, row.source_id, row.split) for row in rows)
    expected = {}
    for artist_id in config.artist_ids:
        for source_id in config.source_ids:
            expected[(artist_id, source_id, "train")] = 3
            expected[(artist_id, source_id, "held_out")] = 2
    if counts != Counter(expected):
        raise ValueError("pilot_2 atlas is not exactly balanced at 3 train + 2 held per cell")

    for row in rows:
        expected_digest = pilot2_selection_digest(
            config.selection_namespace, row.canonical_work_id
        )
        expected_split = "train" if row.selection_rank <= 3 else "held_out"
        if row.selection_digest != expected_digest or row.split != expected_split:
            raise ValueError(
                f"pilot_2 atlas row has stale selection evidence: {row.canonical_work_id}"
            )


def atlas_manifest_sha256(rows: Sequence[Pilot2AtlasWork]) -> str:
    ordered = sorted(
        (row.model_dump(mode="json") for row in rows),
        key=lambda row: str(row["canonical_work_id"]),
    )
    return stable_hash(ordered)


def acquired_image_from_file(
    work: Pilot2AtlasWork, path: Path, root: Optional[Path] = None
) -> Pilot2AcquiredImage:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"missing acquired pilot_2 image: {path}")
    with Image.open(path) as image:
        image.load()
        width, height = image.size
        decoded_format = (image.format or "unknown").casefold()
    stored_path = str(path)
    if root is not None:
        try:
            stored_path = str(path.resolve().relative_to(Path(root).resolve()))
        except ValueError:
            stored_path = str(path.resolve())
    return Pilot2AcquiredImage(
        canonical_work_id=work.canonical_work_id,
        artist_id=work.artist_id,
        source_id=work.source_id,
        source_object_id=work.source_object_id,
        local_path=stored_path,
        sha256=hash_file(path),
        decoded_width=width,
        decoded_height=height,
        decoded_format=decoded_format,
        atlas_selection_digest=work.selection_digest,
    )


def validate_pilot2_acquired_images(
    rows: Sequence[Pilot2AcquiredImage],
    atlas: Sequence[Pilot2AtlasWork],
    *,
    root: Optional[Path] = None,
) -> None:
    if len(rows) != 40:
        raise ValueError(f"pilot_2 requires exactly 40 acquired images, found {len(rows)}")
    by_work = {row.canonical_work_id: row for row in rows}
    if len(by_work) != len(rows):
        raise ValueError("pilot_2 acquired-image manifest contains duplicate works")
    atlas_by_work = {work.canonical_work_id: work for work in atlas}
    if set(by_work) != set(atlas_by_work):
        raise ValueError("pilot_2 acquired images do not cover the selected atlas exactly")
    for work_id, row in by_work.items():
        work = atlas_by_work[work_id]
        if (
            row.artist_id,
            row.source_id,
            row.source_object_id,
            row.atlas_selection_digest,
        ) != (
            work.artist_id,
            work.source_id,
            work.source_object_id,
            work.selection_digest,
        ):
            raise ValueError(f"acquired image does not bind to atlas row: {work_id}")
        if root is not None:
            path = Path(row.local_path)
            if not path.is_absolute():
                path = Path(root) / path
            if hash_file(path) != row.sha256:
                raise ValueError(f"acquired image hash is stale: {work_id}")
            with Image.open(path) as image:
                image.load()
                observed = (image.width, image.height, (image.format or "unknown").casefold())
            expected = (row.decoded_width, row.decoded_height, row.decoded_format)
            if observed != expected:
                raise ValueError(f"acquired image decode metadata is stale: {work_id}")


def acquired_image_manifest_sha256(rows: Sequence[Pilot2AcquiredImage]) -> str:
    return stable_hash(
        [
            row.model_dump(mode="json")
            for row in sorted(rows, key=lambda item: item.canonical_work_id)
        ]
    )
