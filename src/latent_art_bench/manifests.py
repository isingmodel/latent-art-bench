from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Type, Union

from pydantic import BaseModel, ValidationError

from latent_art_bench.io import hash_file, read_jsonl
from latent_art_bench.schemas import (
    CanonicalWorkRecord,
    CorpusCandidateRecord,
    DerivedViewRecord,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    ReproductionRecord,
    RunRecord,
)

ManifestRecord = Union[
    CanonicalWorkRecord,
    CorpusCandidateRecord,
    ReproductionRecord,
    DerivedViewRecord,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    RunRecord,
]

RECORD_TYPES: Dict[str, Type[BaseModel]] = {
    "canonical_work": CanonicalWorkRecord,
    "corpus_candidate": CorpusCandidateRecord,
    "reproduction": ReproductionRecord,
    "derived_view": DerivedViewRecord,
    "feature": FeatureRow,
    "generation_call": GenerationCallRecord,
    "prompt": PromptRecord,
    "run": RunRecord,
}


def parse_manifest(path: Path) -> List[ManifestRecord]:
    records: List[ManifestRecord] = []
    errors: List[str] = []
    for line_number, raw in enumerate(read_jsonl(path), start=1):
        record_type = raw.get("record_type") if isinstance(raw, dict) else None
        model = RECORD_TYPES.get(record_type)
        if model is None:
            errors.append(f"{path}:{line_number}: unknown record_type {record_type!r}")
            continue
        try:
            records.append(model.model_validate(raw))
        except ValidationError as exc:
            errors.append(f"{path}:{line_number}: {exc}")
    if errors:
        raise ValueError("\n".join(errors))
    return records


def _record_identity(record: ManifestRecord) -> Tuple[str, str]:
    if isinstance(record, CorpusCandidateRecord):
        return record.record_type, f"{record.source_id}:{record.source_object_id}"
    fields = {
        "canonical_work": "canonical_work_id",
        "reproduction": "reproduction_id",
        "derived_view": "derived_view_id",
        "feature": "feature_id",
        "generation_call": "call_id",
        "prompt": "prompt_id",
        "run": "run_id",
    }
    record_type = record.record_type
    return record_type, str(getattr(record, fields[record_type]))


def validate_records(
    records: Iterable[ManifestRecord], root: Path, check_files: bool = False
) -> Dict[str, int]:
    rows = list(records)
    errors: List[str] = []
    seen = set()
    counts: Dict[str, int] = defaultdict(int)
    work_splits: Dict[str, set] = defaultdict(set)
    hash_owners: Dict[str, set] = defaultdict(set)
    perceptual_hash_owners: Dict[str, set] = defaultdict(set)
    canonical_ids = set()
    reproduction_ids = set()
    derived_ids = set()

    for record in rows:
        identity = _record_identity(record)
        if identity in seen:
            errors.append(f"duplicate {identity[0]} identifier: {identity[1]}")
        seen.add(identity)
        counts[record.record_type] += 1
        if isinstance(record, CanonicalWorkRecord):
            canonical_ids.add(record.canonical_work_id)
            work_splits[record.canonical_work_id].add(record.split)
        elif isinstance(record, ReproductionRecord):
            reproduction_ids.add(record.reproduction_id)
            work_splits[record.canonical_work_id].add(record.split)
            if record.sha256:
                hash_owners[record.sha256].add(record.canonical_work_id)
            if record.perceptual_hash:
                perceptual_hash_owners[record.perceptual_hash].add(
                    record.canonical_work_id
                )
            if check_files:
                local_path = Path(record.local_path)
                if not local_path.is_absolute():
                    local_path = root / local_path
                if not local_path.is_file():
                    errors.append(f"missing reproduction file: {local_path}")
                elif record.sha256 and hash_file(local_path) != record.sha256:
                    errors.append(f"sha256 mismatch: {record.reproduction_id} ({local_path})")
        elif isinstance(record, DerivedViewRecord):
            derived_ids.add(record.derived_view_id)
            if check_files:
                output_path = Path(record.output_path)
                if not output_path.is_absolute():
                    output_path = root / output_path
                if not output_path.is_file():
                    errors.append(f"missing derived-view file: {output_path}")
                elif hash_file(output_path) != record.output_sha256:
                    errors.append(f"sha256 mismatch: {record.derived_view_id} ({output_path})")
        elif isinstance(record, GenerationCallRecord):
            if check_files and record.status == "succeeded":
                if not record.output_path or not record.output_sha256:
                    errors.append(f"successful call lacks output provenance: {record.call_id}")
                else:
                    output_path = Path(record.output_path)
                    if not output_path.is_absolute():
                        output_path = root / output_path
                    if not output_path.is_file():
                        errors.append(f"missing generated file: {output_path}")
                    elif hash_file(output_path) != record.output_sha256:
                        errors.append(f"sha256 mismatch: {record.call_id} ({output_path})")

    for work_id, splits in work_splits.items():
        effective = splits - {"unassigned"}
        if len(effective) > 1:
            errors.append(f"canonical-work split leakage for {work_id}: {sorted(effective)}")
    for digest, owners in hash_owners.items():
        if len(owners) > 1:
            errors.append(f"byte-identical reproduction assigned to multiple works: {digest}")
    perceptual_items = sorted(perceptual_hash_owners.items())
    for perceptual_hash, owners in perceptual_items:
        if len(owners) > 1:
            errors.append(
                "identical perceptual hash assigned to multiple works "
                f"({perceptual_hash}): {', '.join(sorted(owners))}"
            )
    for index, (left_hash, left_owners) in enumerate(perceptual_items):
        for right_hash, right_owners in perceptual_items[index + 1 :]:
            if left_owners == right_owners:
                continue
            hamming = (int(left_hash, 16) ^ int(right_hash, 16)).bit_count()
            if hamming <= 4:
                owners = sorted(left_owners | right_owners)
                errors.append(
                    "near-identical perceptual hashes cross canonical works "
                    f"(distance={hamming}): {', '.join(owners)}"
                )

    if canonical_ids:
        for record in rows:
            if (
                isinstance(record, ReproductionRecord)
                and record.canonical_work_id not in canonical_ids
            ):
                errors.append(
                    f"reproduction {record.reproduction_id} references missing work "
                    f"{record.canonical_work_id}"
                )
    if reproduction_ids:
        for record in rows:
            if (
                isinstance(record, DerivedViewRecord)
                and record.reproduction_id not in reproduction_ids
            ):
                errors.append(
                    f"derived view {record.derived_view_id} references missing reproduction "
                    f"{record.reproduction_id}"
                )
    if derived_ids:
        for record in rows:
            if isinstance(record, FeatureRow) and record.derived_view_id not in derived_ids:
                errors.append(
                    f"feature {record.feature_id} references missing view {record.derived_view_id}"
                )

    if errors:
        raise ValueError("\n".join(errors))
    return dict(sorted(counts.items()))


def validate_manifests(
    paths: Iterable[Path], root: Path, check_files: bool = False
) -> Dict[str, int]:
    records: List[ManifestRecord] = []
    for path in paths:
        records.extend(parse_manifest(path))
    return validate_records(records, root=root, check_files=check_files)
