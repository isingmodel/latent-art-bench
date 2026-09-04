"""Rebuild the historical pixel-exposure denylist required by Protocol 2.1 §8 and §8.1.

Pilots 0–3 and the retired Painter Features v1 namespace downloaded, normalized, and measured
real paintings from AIC, NGA, CMA, and the Met. Protocol 2.1 restricts every such work to the
development role. The retired namespace's 118-work denylist and the pilot manifests that give
those works their provider identifiers were deleted from the working tree in the refactoring
commit; they survive only in git history. This module reads exactly pinned commits, unions the
evidence, and writes one tracked denylist in the active namespace together with a receipt that
records every source blob by commit, path, and SHA-256.

The rebuild is deterministic and offline. It never touches image bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from latent_art_bench.io import canonical_json, hash_file

OUTPUT_PATH = Path("data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl")
RECEIPT_PATH = Path("data/manifests/painter_feature_generation_v1/exposure_denylist_receipt.json")
SCHEMA_VERSION = "painter-feature-generation-v1-exposure-denylist/1.0"
RECEIPT_SCHEMA = "painter-feature-generation-v1-exposure-denylist-receipt/1.0"
PANEL = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")

# Exact commits and paths. Each row is (source key, commit, path, exposure class, pixel?).
SOURCES: List[tuple] = [
    (
        "painter_features_v1_denylist",
        "0e85050ebf625d610c10b3c5b1443eb817eb2336",
        "data/manifests/painter_features_v1/historical_pixel_exposure_denylist.jsonl",
        None,
        True,
    ),
    (
        "pilot_0_canonical_works",
        "7f84765338eb55333fbfbbd911937c7a7f36b019",
        "configs/pilot_0/manifests/canonical_works.jsonl",
        "pilot0_canonical_work_manifest",
        False,
    ),
    (
        "pilot_2_real_images",
        "6a08483ce0049e307247c1897083cfdc2f0022ba",
        "configs/pilot_2/manifests/real_images.jsonl",
        "pilot2_acquired_image_manifest",
        True,
    ),
    (
        "pilot_3_corpus_selection",
        "0e85050ebf625d610c10b3c5b1443eb817eb2336",
        "data/manifests/pilot_3/corpus_selection.jsonl",
        "pilot3_corpus_selection_metadata_only",
        False,
    ),
    (
        "pilot_3_authoritative_candidates",
        "dbabde357520226fa7e6c0153af59ed3003e703a",
        "configs/pilot_3/metadata/authoritative_candidates.jsonl",
        "pilot3_authoritative_candidate_metadata_only",
        False,
    ),
    (
        "pilot_3_development_acquisitions",
        "0e85050ebf625d610c10b3c5b1443eb817eb2336",
        "artifacts/pilot_3/development_acquisitions.jsonl",
        "pilot3_development_acquisition_ledger",
        True,
    ),
    (
        "painter_features_v1_acquired_files",
        "0e85050ebf625d610c10b3c5b1443eb817eb2336",
        "data/manifests/painter_features_v1/acquired_files.jsonl",
        "painter_features_v1_acquisition_ledger",
        True,
    ),
    (
        "painter_features_v1_development_references",
        "0e85050ebf625d610c10b3c5b1443eb817eb2336",
        "data/manifests/painter_features_v1/development_references.jsonl",
        "painter_features_v1_development_reference",
        True,
    ),
]
_WORK_ID = re.compile(r"^work-(?P<provider>[a-z]+)-(?P<id>[A-Za-z0-9.\-]+)$")
_OBJECT_URL = re.compile(
    r"https://(?:www\.)?(?P<host>artic\.edu/artworks|nga\.gov/artworks|nga\.gov/collection/art-object-page|"
    r"clevelandart\.org/art|metmuseum\.org/art/collection/search)/(?P<id>[0-9]+)"
)
_HOST_PROVIDER = {
    "artic.edu/artworks": "aic",
    "nga.gov/artworks": "nga",
    "nga.gov/collection/art-object-page": "nga",
    "clevelandart.org/art": "cma",
    "metmuseum.org/art/collection/search": "met",
}


class DenylistError(RuntimeError):
    """Raised when a pinned source cannot be read exactly as recorded."""


def _git_show(root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"], capture_output=True
    )
    if result.returncode != 0:
        detail = result.stderr.decode().strip()
        raise DenylistError(f"cannot read {path} at {commit[:12]}: {detail}")
    return result.stdout


def _rows(body: bytes) -> List[dict]:
    return [json.loads(line) for line in body.decode("utf-8").splitlines() if line.strip()]


def _work_id_from_row(row: Mapping[str, Any]) -> Optional[str]:
    for key in ("physical_work_id", "canonical_work_id"):
        value = row.get(key)
        if isinstance(value, str):
            if _WORK_ID.match(value):
                return value
            if ":" in value:  # development_references use "aic:16633"
                provider, identifier = value.split(":", 1)
                return f"work-{provider}-{identifier}"
    url = row.get("canonical_object_url")
    if isinstance(url, str):
        match = _OBJECT_URL.search(url)
        if match:
            return f"work-{_HOST_PROVIDER[match.group('host')]}-{match.group('id')}"
    return None


def _merge(target: Dict[str, Any], key: str, value: Any) -> None:
    if value in (None, "", [], {}):
        return
    if key.endswith("s") and isinstance(target.get(key), list):
        values = value if isinstance(value, list) else [value]
        for item in values:
            if item not in target[key]:
                target[key].append(item)
    elif target.get(key) in (None, ""):
        target[key] = value


def _new_entry(work_id: str) -> Dict[str, Any]:
    match = _WORK_ID.match(work_id)
    return OrderedDict(
        schema_version=SCHEMA_VERSION,
        physical_work_id=work_id,
        provider=match.group("provider") if match else None,
        provider_object_id=match.group("id") if match else None,
        artist_id=None,
        title=None,
        accession=None,
        canonical_object_url=None,
        wikidata_qid=None,
        commons_files=[],
        raw_file_sha256s=[],
        exposure_classes=[],
        sources=[],
        pixel_exposed=False,
        denylisted=False,
        allowed_role=None,
    )


def build(root: Path) -> Dict[str, Any]:
    entries: Dict[str, Dict[str, Any]] = {}
    receipts: List[Dict[str, Any]] = []
    excluded_non_panel = 0
    for key, commit, path, exposure_class, pixel in SOURCES:
        body = _git_show(root, commit, path)
        rows = _rows(body)
        receipts.append(
            {
                "source": key,
                "commit": commit,
                "path": path,
                "blob_sha256": hashlib.sha256(body).hexdigest(),
                "rows": len(rows),
                "pixel_exposure_evidence": pixel,
            }
        )
        for index, row in enumerate(rows):
            artist = row.get("artist_id")
            if isinstance(artist, str) and artist not in PANEL:
                excluded_non_panel += 1
                continue
            work_id = _work_id_from_row(row)
            if work_id is None:
                raise DenylistError(f"{key} row {index} has no resolvable physical work id")
            entry = entries.setdefault(work_id, _new_entry(work_id))
            classes = row.get("evidence_classes") if exposure_class is None else [exposure_class]
            for name in classes or []:
                _merge(entry, "exposure_classes", name)
            entry["sources"].append({"source": key, "row_index": index})
            if pixel:
                entry["pixel_exposed"] = True
            _merge(entry, "artist_id", artist)
            _merge(entry, "title", row.get("title"))
            catalog = row.get("catalog_ids") if isinstance(row.get("catalog_ids"), Mapping) else {}
            _merge(entry, "accession", row.get("museum_accession") or catalog.get("aic_accession"))
            _merge(
                entry,
                "canonical_object_url",
                row.get("canonical_object_url") or row.get("source_url"),
            )
            _merge(entry, "wikidata_qid", row.get("wikidata_id"))
            _merge(entry, "commons_files", row.get("commons_file"))
            for sha_key in ("sha256", "raw_sha256", "normalized_sha256", "raw_file_sha256"):
                _merge(entry, "raw_file_sha256s", row.get(sha_key))
    for entry in entries.values():
        entry["denylisted"] = entry["pixel_exposed"]
        entry["allowed_role"] = (
            "development_only" if entry["pixel_exposed"] else "unrestricted_metadata_only_exposure"
        )
        entry["exposure_classes"].sort()
    ordered = [entries[key] for key in sorted(entries)]
    return {"rows": ordered, "sources": receipts, "excluded_non_panel_rows": excluded_non_panel}


def summarize(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_painter: Dict[str, Dict[str, int]] = {}
    for row in rows:
        painter = str(row.get("artist_id") or "unknown")
        bucket = by_painter.setdefault(painter, {"works": 0, "denylisted": 0})
        bucket["works"] += 1
        bucket["denylisted"] += int(bool(row["denylisted"]))
    providers: Dict[str, int] = {}
    for row in rows:
        if row["denylisted"]:
            providers[row["provider"]] = providers.get(row["provider"], 0) + 1
    return {
        "works": len(rows),
        "denylisted": sum(1 for row in rows if row["denylisted"]),
        "metadata_only": sum(1 for row in rows if not row["denylisted"]),
        "denylisted_by_provider": dict(sorted(providers.items())),
        "by_painter": dict(sorted(by_painter.items())),
        "with_wikidata_qid": sum(1 for row in rows if row["wikidata_qid"]),
    }


def write(root: Path) -> Dict[str, Any]:
    built = build(root)
    output = root / OUTPUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(canonical_json(row) + "\n" for row in built["rows"]), encoding="utf-8"
    )
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "rebuilt_from_pinned_git_history_not_yet_frozen_for_m0",
        "rule": (
            "every pixel- or feature-exposed physical work is development-only under Protocol "
            "2.1 §8; rows marked metadata-only record pilot-3 selection exposure and carry no "
            "role restriction"
        ),
        "output_path": str(OUTPUT_PATH),
        "output_sha256": hash_file(output),
        "sources": built["sources"],
        "excluded_non_panel_rows": built["excluded_non_panel_rows"],
        "counts": summarize(built["rows"]),
    }
    receipt_path = root / RECEIPT_PATH
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return receipt


def load(root: Path) -> List[Dict[str, Any]]:
    path = root / OUTPUT_PATH
    if not path.is_file():
        return []
    return _rows(path.read_bytes())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the tracked denylist differs from a fresh rebuild",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.check:
        expected = "".join(canonical_json(row) + "\n" for row in build(root)["rows"])
        target = root / OUTPUT_PATH
        observed = target.read_text(encoding="utf-8") if target.is_file() else None
        print(json.dumps({"in_sync": observed == expected, "path": str(OUTPUT_PATH)}))
        return 0 if observed == expected else 1
    receipt = write(root)
    print(json.dumps({"output_sha256": receipt["output_sha256"], **receipt["counts"]}, indent=2))
    return 0
