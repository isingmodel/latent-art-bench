"""Metadata-only artist/source feasibility audit for pilot 3.

This module deliberately operates on catalog metadata, never on referenced image
files or feature artifacts.  The exact search finds source subsets whose candidate
artists each have enough *distinct physical works* in every source.  A deterministic
bipartite matching check prevents one cross-catalogued work from filling more than
one source slot.
"""

from __future__ import annotations

import csv
import hashlib
import io
import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from latent_art_bench.io import canonical_json, stable_hash

SCHEMA_VERSION = "pilot3_artist_source_feasibility/1.0"
MAX_EXACT_SOURCE_COUNT = 12


@dataclass(frozen=True)
class CandidateArtist:
    """One prospect in the preregistered artist roster."""

    artist_id: str
    artist_name: str

    def __post_init__(self) -> None:
        if not self.artist_id.strip() or not self.artist_name.strip():
            raise ValueError("candidate artist identifiers and names must not be blank")
        if self.artist_id != self.artist_id.strip() or self.artist_name != self.artist_name.strip():
            raise ValueError("candidate artist identifiers and names must be trimmed")

    def as_dict(self) -> Dict[str, str]:
        return {"artist_id": self.artist_id, "artist_name": self.artist_name}


DEFAULT_CANDIDATE_ARTISTS: Tuple[CandidateArtist, ...] = (
    CandidateArtist("alfred_sisley", "Alfred Sisley"),
    CandidateArtist("armand_guillaumin", "Armand Guillaumin"),
    CandidateArtist("berthe_morisot", "Berthe Morisot"),
    CandidateArtist("camille_pissarro", "Camille Pissarro"),
    CandidateArtist("claude_monet", "Claude Monet"),
    CandidateArtist("eugene_boudin", "Eugène Boudin"),
    CandidateArtist("gustave_caillebotte", "Gustave Caillebotte"),
    CandidateArtist("paul_cezanne", "Paul Cezanne"),
    CandidateArtist("pierre_auguste_renoir", "Pierre-Auguste Renoir"),
)


@dataclass(frozen=True)
class Pilot3FeasibilityConfig:
    """Coverage thresholds and the candidate roster for the exact audit."""

    candidate_artists: Tuple[CandidateArtist, ...] = DEFAULT_CANDIDATE_ARTISTS
    min_unique_works_per_artist_source: int = 10
    min_artist_count: int = 8
    min_source_count: int = 3
    source_ids: Tuple[str, ...] = ()
    eligible_decisions: Tuple[str, ...] = ("include",)
    require_confirmed_public_domain: bool = True

    def __post_init__(self) -> None:
        if self.min_unique_works_per_artist_source <= 0:
            raise ValueError("min_unique_works_per_artist_source must be positive")
        if self.min_artist_count <= 0:
            raise ValueError("min_artist_count must be positive")
        if self.min_source_count <= 0:
            raise ValueError("min_source_count must be positive")
        if not self.candidate_artists:
            raise ValueError("candidate_artists must not be empty")

        artist_ids = [item.artist_id for item in self.candidate_artists]
        if len(artist_ids) != len(set(artist_ids)):
            raise ValueError("candidate artist identifiers must be unique")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("configured source identifiers must be unique")
        if any(not source_id.strip() for source_id in self.source_ids):
            raise ValueError("configured source identifiers must not be blank")
        if any(source_id != source_id.strip() for source_id in self.source_ids):
            raise ValueError("configured source identifiers must be trimmed")
        if len(self.source_ids) > MAX_EXACT_SOURCE_COUNT:
            raise ValueError(
                f"exact biclique search supports at most {MAX_EXACT_SOURCE_COUNT} sources"
            )
        normalized_decisions = [value.strip().casefold() for value in self.eligible_decisions]
        if any(not value for value in normalized_decisions):
            raise ValueError("eligible decisions must not be blank")
        if len(normalized_decisions) != len(set(normalized_decisions)):
            raise ValueError("eligible decisions must be unique after normalization")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "candidate_artists": [
                item.as_dict()
                for item in sorted(self.candidate_artists, key=lambda value: value.artist_id)
            ],
            "eligible_decisions": sorted(
                value.strip().casefold() for value in self.eligible_decisions
            ),
            "min_artist_count": self.min_artist_count,
            "min_source_count": self.min_source_count,
            "min_unique_works_per_artist_source": (self.min_unique_works_per_artist_source),
            "require_confirmed_public_domain": self.require_confirmed_public_domain,
            "source_ids": sorted(self.source_ids),
        }


@dataclass(frozen=True)
class MetadataRows:
    """Rows loaded from catalog manifests plus byte-level manifest evidence."""

    rows: Tuple[Mapping[str, Any], ...]
    input_evidence: Tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def __iter__(self) -> Iterator[Mapping[str, Any]]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)


@dataclass(frozen=True)
class _AuditRow:
    artist_id: str
    artist_name: str
    source_id: str
    source_object_id: str
    decision: Optional[str]
    public_domain_status: Optional[str]
    identity_tokens: Tuple[str, ...]
    has_authoritative_identity_beyond_source_object: bool
    eligible: bool
    selection_projection: Mapping[str, Any]


_REQUIRED_FIELDS = ("artist_id", "artist_name", "source_id", "source_object_id")
_DEDUPLICATION_FIELDS = (
    "physical_work_id",
    "canonical_work_id",
    "wikidata_id",
    "catalog_ids",
    "source_id",
    "source_object_id",
)
_SELECTION_FIELDS = (
    "artist_id",
    "artist_name",
    "source_id",
    "source_object_id",
    "physical_work_id",
    "canonical_work_id",
    "wikidata_id",
    "catalog_ids",
    "decision",
    "public_domain_status",
)
_FORBIDDEN_EXACT_KEYS = {
    "analysis_result",
    "analysis_results",
    "confidence_interval",
    "distance",
    "distances",
    "effect",
    "effect_estimate",
    "effect_estimates",
    "effect_size",
    "embedding",
    "embeddings",
    "feature",
    "feature_id",
    "feature_name",
    "feature_vector",
    "features",
    "generated_output",
    "generated_outputs",
    "generation_result",
    "model",
    "model_comparison",
    "output_path",
    "p_value",
    "prompt",
    "prompt_id",
    "specificity",
    "target_improvement",
    "vector",
    "vectors",
}
_FORBIDDEN_RECORD_TYPES = {
    "analysis",
    "derived_view",
    "feature",
    "generation_call",
    "generation_result",
    "pilot2_generation_attempt",
    "pilot2_terminal_generation",
    "run",
}


def _json_clone(value: Any, *, label: str) -> Any:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return json.loads(rendered)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be canonical JSON-ready data") from exc


def _normalized_key(value: Any) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def _is_forbidden_key(key: str) -> bool:
    normalized = _normalized_key(key)
    return (
        normalized in _FORBIDDEN_EXACT_KEYS
        or normalized.startswith("effect_")
        or normalized.startswith("generated_")
        or normalized.startswith("generation_")
        or normalized.endswith("_effect")
        or normalized.endswith("_effect_estimate")
        or normalized.endswith("_feature_vector")
    )


def _validate_no_forbidden_signals(value: Any, *, location: str) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            if _is_forbidden_key(key):
                raise ValueError(
                    f"metadata-only audit rejects forbidden field {key!r} at {location}"
                )
            normalized_key = _normalized_key(key)
            if normalized_key == "record_type" and _normalized_key(child) in (
                _FORBIDDEN_RECORD_TYPES
            ):
                raise ValueError(
                    f"metadata-only audit rejects non-catalog record_type {child!r} at {location}"
                )
            if normalized_key == "origin" and _normalized_key(child) == "generated":
                raise ValueError(f"metadata-only audit rejects generated origin at {location}")
            _validate_no_forbidden_signals(child, location=f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_signals(child, location=f"{location}[{index}]")


def _parse_manifest_bytes(path: Path, raw: bytes) -> List[Mapping[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"metadata manifest is not UTF-8 text: {path}") from exc

    suffix = path.suffix.casefold()
    parsed: Any
    if suffix == ".jsonl":
        parsed = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    elif suffix == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON: {exc}") from exc
        if isinstance(parsed, Mapping) and isinstance(parsed.get("rows"), list):
            parsed = parsed["rows"]
    elif suffix == ".csv":
        parsed = list(csv.DictReader(io.StringIO(text)))
    else:
        raise ValueError(
            f"unsupported metadata manifest format {suffix!r}; use .jsonl, .json, or .csv"
        )

    if not isinstance(parsed, list):
        raise ValueError(f"metadata manifest must contain a list of rows: {path}")
    rows: List[Mapping[str, Any]] = []
    for index, row in enumerate(parsed):
        if not isinstance(row, Mapping):
            raise ValueError(f"metadata row {index} is not an object: {path}")
        cloned = _json_clone(row, label=f"metadata row {index} in {path}")
        _validate_no_forbidden_signals(cloned, location=f"{path}[{index}]")
        rows.append(cloned)
    return rows


def load_metadata_rows(paths: Iterable[Path]) -> MetadataRows:
    """Load JSON/JSONL/CSV catalog rows without resolving any referenced assets."""

    normalized_paths = sorted((Path(path) for path in paths), key=lambda path: path.as_posix())
    if not normalized_paths:
        raise ValueError("at least one metadata manifest path is required")
    path_strings = [path.as_posix() for path in normalized_paths]
    if len(path_strings) != len(set(path_strings)):
        raise ValueError("metadata manifest paths must be unique")

    rows: List[Mapping[str, Any]] = []
    evidence: List[Mapping[str, Any]] = []
    for path in normalized_paths:
        # The manifest itself is the only referenced path opened by this loader.
        raw = path.read_bytes()
        manifest_rows = _parse_manifest_bytes(path, raw)
        rows.extend(manifest_rows)
        evidence.append(
            {
                "format": path.suffix.casefold().lstrip("."),
                "manifest_bytes_sha256": hashlib.sha256(raw).hexdigest(),
                "manifest_path": path.as_posix(),
                "referenced_asset_io_performed": False,
                "row_count": len(manifest_rows),
            }
        )
    return MetadataRows(rows=tuple(rows), input_evidence=tuple(evidence))


def _required_text(row: Mapping[str, Any], field_name: str, row_number: int) -> str:
    raw = row.get(field_name)
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"metadata row {row_number} requires non-blank {field_name!r}")
    return raw.strip()


def _optional_identity_token(prefix: str, value: Any) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{prefix} identity must be a non-blank string when present")
    return f"{prefix}:{value.strip()}"


def _identity_tokens(
    row: Mapping[str, Any], source_id: str, source_object_id: str
) -> Tuple[str, ...]:
    tokens = {f"source_object:{source_id}:{source_object_id}"}
    for field_name, prefix in (
        ("physical_work_id", "physical"),
        ("canonical_work_id", "canonical"),
        ("wikidata_id", "wikidata"),
    ):
        token = _optional_identity_token(prefix, row.get(field_name))
        if token is not None:
            tokens.add(token)
    catalog_ids = row.get("catalog_ids")
    if catalog_ids is not None and not isinstance(catalog_ids, Mapping):
        raise ValueError("catalog_ids must be an object when present")
    if isinstance(catalog_ids, Mapping):
        for namespace, value in sorted(catalog_ids.items(), key=lambda item: str(item[0])):
            if not isinstance(namespace, str) or not namespace.strip():
                raise ValueError("catalog_ids keys must be non-blank strings")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("catalog_ids values must be non-blank strings")
            tokens.add(f"catalog:{namespace.strip()}:{value.strip()}")
    return tuple(sorted(tokens))


def _is_eligible(row: Mapping[str, Any], config: Pilot3FeasibilityConfig) -> bool:
    eligible_decisions = {value.strip().casefold() for value in config.eligible_decisions}
    if eligible_decisions:
        decision = row.get("decision")
        if not isinstance(decision, str) or decision.strip().casefold() not in eligible_decisions:
            return False
    if config.require_confirmed_public_domain:
        public_domain_status = row.get("public_domain_status")
        if (
            not isinstance(public_domain_status, str)
            or public_domain_status.strip().casefold() != "confirmed"
        ):
            return False
    return True


def _prepare_rows(
    raw_rows: Iterable[Mapping[str, Any]], config: Pilot3FeasibilityConfig
) -> Tuple[List[_AuditRow], List[str], str]:
    prepared: List[_AuditRow] = []
    observed_fields = set()
    for row_number, original in enumerate(raw_rows, start=1):
        if not isinstance(original, Mapping):
            raise ValueError(f"metadata row {row_number} is not an object")
        row = _json_clone(original, label=f"metadata row {row_number}")
        _validate_no_forbidden_signals(row, location=f"row[{row_number}]")
        observed_fields.update(str(key) for key in row)
        artist_id = _required_text(row, "artist_id", row_number)
        artist_name = _required_text(row, "artist_name", row_number)
        source_id = _required_text(row, "source_id", row_number)
        source_object_id = _required_text(row, "source_object_id", row_number)
        tokens = _identity_tokens(row, source_id, source_object_id)
        projection = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "catalog_ids": {
                str(key): value
                for key, value in sorted(
                    (row.get("catalog_ids") or {}).items(),
                    key=lambda item: str(item[0]),
                )
            }
            if isinstance(row.get("catalog_ids"), Mapping)
            else {},
            "canonical_work_id": row.get("canonical_work_id"),
            "decision": row.get("decision"),
            "physical_work_id": row.get("physical_work_id"),
            "public_domain_status": row.get("public_domain_status"),
            "source_id": source_id,
            "source_object_id": source_object_id,
            "wikidata_id": row.get("wikidata_id"),
        }
        prepared.append(
            _AuditRow(
                artist_id=artist_id,
                artist_name=artist_name,
                source_id=source_id,
                source_object_id=source_object_id,
                decision=(
                    str(row["decision"]).strip().casefold()
                    if isinstance(row.get("decision"), str)
                    else None
                ),
                public_domain_status=(
                    str(row["public_domain_status"]).strip().casefold()
                    if isinstance(row.get("public_domain_status"), str)
                    else None
                ),
                identity_tokens=tokens,
                has_authoritative_identity_beyond_source_object=any(
                    not token.startswith("source_object:") for token in tokens
                ),
                eligible=_is_eligible(row, config),
                selection_projection=projection,
            )
        )
    prepared.sort(key=lambda row: canonical_json(row.selection_projection))
    names_by_artist: Dict[str, set] = {}
    for row in prepared:
        names_by_artist.setdefault(row.artist_id, set()).add(row.artist_name)
    inconsistent_names = {
        artist_id: sorted(names) for artist_id, names in names_by_artist.items() if len(names) > 1
    }
    if inconsistent_names:
        raise ValueError(
            f"artist identifiers map to inconsistent names: {canonical_json(inconsistent_names)}"
        )
    configured_names = {
        candidate.artist_id: candidate.artist_name for candidate in config.candidate_artists
    }
    name_mismatches = sorted(
        {
            (row.artist_id, row.artist_name, configured_names[row.artist_id])
            for row in prepared
            if row.artist_id in configured_names
            and row.artist_name != configured_names[row.artist_id]
        }
    )
    if name_mismatches:
        rendered = [
            {
                "artist_id": artist_id,
                "configured_artist_name": expected_name,
                "observed_artist_name": observed_name,
            }
            for artist_id, observed_name, expected_name in name_mismatches
        ]
        raise ValueError(
            "candidate artist name does not exactly match the frozen roster: "
            f"{canonical_json(rendered)}"
        )
    projection_hash = stable_hash([row.selection_projection for row in prepared])
    return prepared, sorted(observed_fields), projection_hash


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        if left_root < right_root:
            self.parent[right_root] = left_root
        else:
            self.parent[left_root] = right_root


def _token_rank(token: str) -> Tuple[int, str]:
    prefix = token.split(":", 1)[0]
    ranks = {
        "physical": 0,
        "canonical": 1,
        "wikidata": 2,
        "catalog": 3,
        "source_object": 4,
    }
    return ranks.get(prefix, 5), token


def _deduplicate_rows(
    rows: Sequence[_AuditRow],
) -> Tuple[Dict[str, List[_AuditRow]], List[Dict[str, Any]]]:
    union_find = _UnionFind(len(rows))
    token_owner: Dict[str, int] = {}
    for index, row in enumerate(rows):
        for token in row.identity_tokens:
            previous = token_owner.setdefault(token, index)
            union_find.union(previous, index)

    grouped_indices: Dict[int, List[int]] = {}
    for index in range(len(rows)):
        grouped_indices.setdefault(union_find.find(index), []).append(index)

    groups: Dict[str, List[_AuditRow]] = {}
    duplicate_groups: List[Dict[str, Any]] = []
    for member_indices in grouped_indices.values():
        members = [rows[index] for index in member_indices]
        artist_ids = sorted({row.artist_id for row in members})
        if len(artist_ids) != 1:
            all_tokens = sorted({token for row in members for token in row.identity_tokens})
            raise ValueError(
                f"physical-work identity links multiple artists: {artist_ids} via {all_tokens}"
            )
        all_tokens = sorted({token for row in members for token in row.identity_tokens})
        physical_work_id = min(all_tokens, key=_token_rank)
        if physical_work_id in groups:
            raise AssertionError("deduplicated physical work identifier collision")
        groups[physical_work_id] = members
        if len(members) > 1:
            source_objects = sorted({f"{row.source_id}:{row.source_object_id}" for row in members})
            duplicate_groups.append(
                {
                    "artist_id": artist_ids[0],
                    "physical_work_id": physical_work_id,
                    "row_count": len(members),
                    "source_ids": sorted({row.source_id for row in members}),
                    "source_objects": source_objects,
                }
            )
    return dict(sorted(groups.items())), sorted(
        duplicate_groups, key=lambda item: str(item["physical_work_id"])
    )


def _eligible_work_sets(
    groups: Mapping[str, Sequence[_AuditRow]],
) -> Dict[Tuple[str, str], set]:
    work_sets: Dict[Tuple[str, str], set] = {}
    for physical_work_id, rows in groups.items():
        eligible_cells = {(row.artist_id, row.source_id) for row in rows if row.eligible}
        for cell in eligible_cells:
            work_sets.setdefault(cell, set()).add(physical_work_id)
    return work_sets


def _disjoint_allocation(
    artist_id: str,
    source_ids: Sequence[str],
    required_per_source: int,
    work_sets: Mapping[Tuple[str, str], set],
) -> Optional[Dict[str, List[str]]]:
    """Return a deterministic source-slot matching or ``None`` if impossible."""

    slots = [
        (source_id, slot_index)
        for source_id in sorted(source_ids)
        for slot_index in range(required_per_source)
    ]
    candidates = {slot: sorted(work_sets.get((artist_id, slot[0]), set())) for slot in slots}
    work_to_slot: Dict[str, Tuple[str, int]] = {}

    def assign(slot: Tuple[str, int], visited: set) -> bool:
        for work_id in candidates[slot]:
            if work_id in visited:
                continue
            visited.add(work_id)
            prior_slot = work_to_slot.get(work_id)
            if prior_slot is None or assign(prior_slot, visited):
                work_to_slot[work_id] = slot
                return True
        return False

    for slot in slots:
        if not assign(slot, set()):
            return None

    allocation: Dict[str, List[str]] = {source_id: [] for source_id in sorted(source_ids)}
    for work_id, slot in sorted(work_to_slot.items()):
        allocation[slot[0]].append(work_id)
    for source_id in allocation:
        allocation[source_id].sort()
        if len(allocation[source_id]) != required_per_source:
            raise AssertionError("matching returned an incomplete source allocation")
    return allocation


def _maximum_balanced_works_per_source(
    artist_id: str,
    source_ids: Sequence[str],
    work_sets: Mapping[Tuple[str, str], set],
) -> int:
    if not source_ids:
        return 0
    upper_bound = min(len(work_sets.get((artist_id, source_id), set())) for source_id in source_ids)
    for candidate in range(upper_bound, 0, -1):
        if _disjoint_allocation(artist_id, source_ids, candidate, work_sets) is not None:
            return candidate
    return 0


def _biclique_candidate(
    source_ids: Sequence[str],
    config: Pilot3FeasibilityConfig,
    work_sets: Mapping[Tuple[str, str], set],
) -> Dict[str, Any]:
    required = config.min_unique_works_per_artist_source
    artist_coverage: List[Dict[str, Any]] = []
    qualifying_artist_ids: List[str] = []
    allocations: Dict[str, Dict[str, List[str]]] = {}
    for candidate in sorted(config.candidate_artists, key=lambda item: item.artist_id):
        maximum_balanced = _maximum_balanced_works_per_source(
            candidate.artist_id, source_ids, work_sets
        )
        qualifies = maximum_balanced >= required
        cell_counts = {
            source_id: len(work_sets.get((candidate.artist_id, source_id), set()))
            for source_id in sorted(source_ids)
        }
        artist_coverage.append(
            {
                "artist_id": candidate.artist_id,
                "cell_unique_work_counts": cell_counts,
                "maximum_disjoint_balanced_works_per_source": maximum_balanced,
                "qualifies": qualifies,
            }
        )
        if qualifies:
            qualifying_artist_ids.append(candidate.artist_id)
            allocation = _disjoint_allocation(candidate.artist_id, source_ids, required, work_sets)
            if allocation is None:
                raise AssertionError("qualified artist lacks required allocation")
            allocations[candidate.artist_id] = allocation

    artist_count = len(qualifying_artist_ids)
    coverage_numerator = sum(
        min(required, int(item["maximum_disjoint_balanced_works_per_source"]))
        for item in artist_coverage
    )
    qualifying_cell_counts = [
        len(work_sets.get((artist_id, source_id), set()))
        for artist_id in qualifying_artist_ids
        for source_id in source_ids
    ]
    return {
        "allocated_physical_work_ids": allocations,
        "artist_count": artist_count,
        "artist_coverage": artist_coverage,
        "cell_count": artist_count * len(source_ids),
        "coverage_score_denominator": len(config.candidate_artists) * required,
        "coverage_score_numerator": coverage_numerator,
        "meets_min_artist_count": artist_count >= config.min_artist_count,
        "minimum_observed_unique_works_per_qualifying_cell": (
            min(qualifying_cell_counts) if qualifying_cell_counts else None
        ),
        "qualifying_artist_ids": qualifying_artist_ids,
        "source_count": len(source_ids),
        "source_ids": sorted(source_ids),
    }


def _search_bicliques(
    source_ids: Sequence[str],
    config: Pilot3FeasibilityConfig,
    work_sets: Mapping[Tuple[str, str], set],
) -> List[Dict[str, Any]]:
    candidates = []
    for source_count in range(config.min_source_count, len(source_ids) + 1):
        for subset in itertools.combinations(sorted(source_ids), source_count):
            candidates.append(_biclique_candidate(subset, config, work_sets))

    def rank(item: Mapping[str, Any]) -> Tuple[Any, ...]:
        if item["meets_min_artist_count"]:
            within_status = (
                -(int(item["artist_count"]) * int(item["source_count"])),
                -int(item["artist_count"]),
                -int(item["source_count"]),
                -int(item["coverage_score_numerator"]),
            )
        else:
            within_status = (
                -int(item["artist_count"]),
                -int(item["coverage_score_numerator"]),
                -int(item["source_count"]),
                0,
            )
        return (
            -int(bool(item["meets_min_artist_count"])),
            *within_status,
            tuple(item["source_ids"]),
        )

    return sorted(candidates, key=rank)


def _seal_result(payload: Mapping[str, Any]) -> Dict[str, Any]:
    result = _json_clone(payload, label="feasibility result")
    result["semantic_sha256"] = stable_hash(result)
    return result


def verify_feasibility_result(result: Mapping[str, Any]) -> bool:
    """Verify schema and self-hash, raising on tampering or non-JSON data."""

    cloned = _json_clone(result, label="feasibility result")
    if cloned.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unexpected pilot-3 feasibility schema version")
    observed = cloned.pop("semantic_sha256", None)
    if not isinstance(observed, str) or len(observed) != 64:
        raise ValueError("feasibility result lacks a valid semantic_sha256")
    expected = stable_hash(cloned)
    if observed != expected:
        raise ValueError("feasibility result semantic_sha256 mismatch")
    return True


def audit_feasibility(
    rows: Iterable[Mapping[str, Any]],
    config: Optional[Pilot3FeasibilityConfig] = None,
    *,
    input_evidence: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Audit whether local catalog metadata supports a balanced pilot-3 corpus.

    Selection depends only on pre-existing eligibility metadata, authoritative work
    identifiers, and artist/source coverage.  Generated outputs, feature values,
    model labels, prompts, effect estimates, and inferential results are rejected.
    """

    resolved_config = config or Pilot3FeasibilityConfig()
    if isinstance(rows, MetadataRows):
        if input_evidence is not None:
            raise ValueError("input_evidence must not be repeated for MetadataRows")
        input_evidence = rows.input_evidence
        raw_rows = list(rows.rows)
    else:
        raw_rows = list(rows)
    evidence = sorted(
        _json_clone(list(input_evidence or []), label="metadata input evidence"),
        key=canonical_json,
    )
    prepared, observed_fields, projection_hash = _prepare_rows(raw_rows, resolved_config)
    groups, duplicate_groups = _deduplicate_rows(prepared)
    work_sets = _eligible_work_sets(groups)

    roster = {candidate.artist_id: candidate for candidate in resolved_config.candidate_artists}
    observed_candidate_ids = sorted({row.artist_id for row in prepared if row.artist_id in roster})
    unobserved_candidate_ids = sorted(set(roster) - set(observed_candidate_ids))
    observed_source_ids = sorted({row.source_id for row in prepared if row.artist_id in roster})
    if resolved_config.source_ids:
        source_ids = sorted(resolved_config.source_ids)
    else:
        source_ids = observed_source_ids
    if len(source_ids) > MAX_EXACT_SOURCE_COUNT:
        raise ValueError(
            f"exact biclique search supports at most {MAX_EXACT_SOURCE_COUNT} sources; "
            "set source_ids explicitly"
        )

    candidate_summaries = []
    for artist_id, candidate in sorted(roster.items()):
        artist_rows = [row for row in prepared if row.artist_id == artist_id]
        eligible_rows = [row for row in artist_rows if row.eligible]
        candidate_summaries.append(
            {
                "artist_id": artist_id,
                "artist_name": candidate.artist_name,
                "coverage_interpretation": (
                    "observed_snapshot_counts"
                    if artist_rows
                    else "unknown_no_local_metadata_not_zero_works"
                ),
                "eligible_row_count": len(eligible_rows),
                "eligible_source_ids": sorted({row.source_id for row in eligible_rows}),
                "observed_metadata": bool(artist_rows),
                "observed_row_count": len(artist_rows),
                "observed_source_ids": sorted({row.source_id for row in artist_rows}),
            }
        )

    out_of_scope = []
    for artist_id in sorted({row.artist_id for row in prepared} - set(roster)):
        artist_rows = [row for row in prepared if row.artist_id == artist_id]
        names = sorted({row.artist_name for row in artist_rows})
        out_of_scope.append(
            {
                "artist_id": artist_id,
                "artist_names": names,
                "observed_row_count": len(artist_rows),
                "observed_source_ids": sorted({row.source_id for row in artist_rows}),
            }
        )

    matrix = []
    for artist_id, candidate in sorted(roster.items()):
        source_rows = []
        for source_id in source_ids:
            observed_rows = [
                row for row in prepared if row.artist_id == artist_id and row.source_id == source_id
            ]
            eligible_rows = [row for row in observed_rows if row.eligible]
            unique_work_count = len(work_sets.get((artist_id, source_id), set()))
            source_rows.append(
                {
                    "duplicate_eligible_rows_removed": max(
                        0, len(eligible_rows) - unique_work_count
                    ),
                    "eligible_row_count": len(eligible_rows),
                    "eligible_unique_physical_work_count": unique_work_count,
                    "observed_row_count": len(observed_rows),
                    "source_id": source_id,
                }
            )
        matrix.append(
            {
                "artist_id": artist_id,
                "artist_name": candidate.artist_name,
                "sources": source_rows,
            }
        )

    bicliques = _search_bicliques(source_ids, resolved_config, work_sets)
    best_available = bicliques[0] if bicliques else None
    selected = next(
        (candidate for candidate in bicliques if candidate["meets_min_artist_count"]),
        None,
    )
    threshold_met = selected is not None
    threshold_result = (
        "meets_configured_snapshot_thresholds"
        if threshold_met
        else "does_not_meet_configured_snapshot_thresholds"
    )
    threshold_result_reasons: List[Dict[str, Any]] = []
    if not threshold_met:
        if len(observed_candidate_ids) < resolved_config.min_artist_count:
            threshold_result_reasons.append(
                {
                    "code": "observed_candidate_artist_shortfall",
                    "observed_candidate_artist_count": len(observed_candidate_ids),
                    "required_candidate_artist_count": resolved_config.min_artist_count,
                }
            )
        if len(source_ids) < resolved_config.min_source_count:
            threshold_result_reasons.append(
                {
                    "code": "source_count_shortfall",
                    "observed_or_configured_source_count": len(source_ids),
                    "required_source_count": resolved_config.min_source_count,
                }
            )
        if len(source_ids) >= resolved_config.min_source_count:
            threshold_result_reasons.append(
                {
                    "best_available_artist_count": (
                        int(best_available["artist_count"]) if best_available else 0
                    ),
                    "code": "balanced_biclique_not_found",
                    "required_artist_count": resolved_config.min_artist_count,
                    "required_unique_works_per_artist_source": (
                        resolved_config.min_unique_works_per_artist_source
                    ),
                }
            )

    ignored_fields = sorted(set(observed_fields) - set(_SELECTION_FIELDS))
    payload = {
        "artist_source_counts": matrix,
        "best_available_biclique": best_available,
        "biclique_search": {
            "candidate_source_set_count": len(bicliques),
            "exact_search": True,
            "ranking_basis": [
                "meets_min_artist_count",
                "if threshold meeting: artist_source_cell_count, artist_count, source_count",
                "if threshold not meeting: artist_count, coverage_score, source_count",
                "source_ids_lexicographic_tiebreak",
            ],
            "searched_source_sets": bicliques,
        },
        "candidate_artists": candidate_summaries,
        "claim_boundary": {
            "cross_source_distinctness_verified": False,
            "external_catalog_coverage_claimed": False,
            "freeze_a1_ready": False,
            "threshold_not_met_interpretation": (
                "only the supplied local metadata snapshot cannot satisfy the configured thresholds"
            ),
            "raw_response_hashes_and_access_dates_verified": False,
            "snapshot_scope": "only manifests listed in input_evidence or supplied in memory",
            "source_governance_and_independence_verified": False,
            "unobserved_candidate_interpretation": (
                "unknown coverage; absence from supplied metadata is not evidence of zero works"
            ),
        },
        "config": resolved_config.as_dict(),
        "deduplication": {
            "cross_source_duplicate_group_count": sum(
                len(item["source_ids"]) > 1 for item in duplicate_groups
            ),
            "duplicate_group_count": len(duplicate_groups),
            "duplicate_groups": duplicate_groups,
            "duplicate_rows_removed": len(prepared) - len(groups),
            "identity_fields": list(_DEDUPLICATION_FIELDS),
            "identity_policy": (
                "transitive union of authoritative metadata identifiers; no title/year, "
                "path, URL, image hash, pixel, feature, or outcome inference"
            ),
            "rows_without_authoritative_identity_beyond_source_object_count": sum(
                not row.has_authoritative_identity_beyond_source_object for row in prepared
            ),
            "unique_physical_work_count": len(groups),
        },
        "eligibility_scope": {
            "artifact_reapplies_full_domain_rules": False,
            "confirmed_public_domain_flag_required": (
                resolved_config.require_confirmed_public_domain
            ),
            "decision_values_accepted": sorted(
                value.strip().casefold() for value in resolved_config.eligible_decisions
            ),
            "rights_basis_reverified": False,
            "trusted_snapshot_flag": "upstream decision=include",
            (
                "upstream_attribution_object_type_common_domain_and_"
                "acquisition_eligibility_reverified"
            ): False,
        },
        "freeze_readiness": {
            "freeze_a1_ready": False,
            "readiness_decision": "BLOCKED_UNVERIFIED_METADATA_GOVERNANCE_AND_IDENTITY",
            "readiness_transition_supported_by_this_schema": False,
            "unverified_prerequisites": [
                "upstream attribution, painting/object-type, common-domain, and "
                "acquisition-rights eligibility",
                "source governance and acquisition-source independence",
                "raw authoritative metadata-response hashes and access dates",
                "cross-source distinctness beyond shared catalog identifiers",
            ],
        },
        "input_evidence": evidence,
        "input_summary": {
            "ignored_field_names": ignored_fields,
            "observed_field_names": observed_fields,
            "row_count": len(prepared),
            "selection_projection_semantic_sha256": projection_hash,
            "source_ids_considered": source_ids,
        },
        "metadata_only_guarantee": {
            "forbidden_signal_policy": "reject",
            "forbidden_signal_types": [
                "generated outputs",
                "generation/model/prompt records",
                "feature vectors or embeddings",
                "distances and effect estimates",
                "inferential results",
            ],
            "image_or_referenced_asset_io": "none",
            "manifest_loader_io": "manifest bytes only",
            "selection_fields_used": list(_SELECTION_FIELDS),
            "status": "pass",
        },
        "observed_candidate_artist_ids": observed_candidate_ids,
        "out_of_scope_observed_artists": out_of_scope,
        "schema_version": SCHEMA_VERSION,
        "configured_snapshot_threshold_result": threshold_result,
        "status": "metadata_snapshot_audit_complete_not_freeze_ready",
        "threshold_meeting_biclique": selected,
        "threshold_result_reasons": threshold_result_reasons,
        "unobserved_candidate_artist_ids": unobserved_candidate_ids,
    }
    result = _seal_result(payload)
    verify_feasibility_result(result)
    return result


def audit_metadata_files(
    paths: Iterable[Path],
    config: Optional[Pilot3FeasibilityConfig] = None,
) -> Dict[str, Any]:
    """Load and audit catalog manifests, preserving exact input byte evidence."""

    loaded = load_metadata_rows(paths)
    return audit_feasibility(loaded, config)


__all__ = [
    "CandidateArtist",
    "DEFAULT_CANDIDATE_ARTISTS",
    "MAX_EXACT_SOURCE_COUNT",
    "MetadataRows",
    "Pilot3FeasibilityConfig",
    "SCHEMA_VERSION",
    "audit_feasibility",
    "audit_metadata_files",
    "load_metadata_rows",
    "verify_feasibility_result",
]
