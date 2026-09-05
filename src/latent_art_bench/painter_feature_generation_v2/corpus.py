"""Reconcile the recorded metadata and prospectively assign analysis roles; no pixels."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from latent_art_bench.io import hash_file, read_jsonl
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    PROTOCOL,
    bindings,
    digest,
    identifier,
    publish,
)

V1 = Path("data/manifests/painter_feature_generation_v1")
DETERMINATION = V1 / "pfg_v1_r1_20260904_determination.jsonl"
CENSUS = V1 / "broad_media_followup_publication_r2/candidates.jsonl"
DENYLIST = V1 / "exposure_denylist.jsonl"
PROMPTS = V1 / "prompt_library.json"
PROVIDER_COLLECTIONS = {
    "aic": "Q239303", "nga": "Q214867", "met": "Q160236", "cma": "Q657415",
}


def normalize(value: str) -> str:
    return re.sub(r"[^\w]+", "", unicodedata.normalize("NFKC", value).casefold())


def work_components(records: list[dict]) -> list[list[dict]]:
    """Join only explicit collection/accession identities or the same resolved QID."""
    parent = list(range(len(records)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    seen: dict[tuple, int] = {}
    for index, row in enumerate(records):
        keys = [("qid", row["item_qid"])]
        # Multiple unpaired collection/inventory lists do not license a Cartesian identity join.
        if len(row["collections"]) == len(row["accessions"]) == 1:
            keys.append(("accession", row["collections"][0], normalize(row["accessions"][0])))
        for key in keys:
            if key in seen:
                parent[find(index)] = find(seen[key])
            seen[key] = index
    groups: dict[int, list] = defaultdict(list)
    for i, row in enumerate(records):
        groups[find(i)].append(row)
    return list(groups.values())


def exposure_matches(row: dict, denylist: list[dict]) -> list[str]:
    matches = []
    for exposed in denylist:
        if not exposed.get("denylisted"):
            continue
        exact = exposed.get("wikidata_qid") in row["item_qids"]
        provider = exposed.get("provider")
        same_collection = PROVIDER_COLLECTIONS.get(provider) in row["collections"]
        accession = exposed.get("accession")
        same_accession = bool(accession) and normalize(accession) in {
            normalize(x) for x in row["accessions"]
        }
        # Conservative title matching flags possible exposure; it never establishes identity.
        title = normalize(exposed.get("title") or "")
        title_match = (bool(title) and exposed.get("artist_id") == row["painter_id"]
                       and title in {normalize(x) for x in row["labels"]})
        url = exposed.get("canonical_object_url")
        url_match = bool(url) and url in row["object_urls"]
        if exact or (same_collection and same_accession) or title_match or url_match:
            matches.append(exposed["physical_work_id"])
    return sorted(set(matches))


def assign_roles(rows: list[dict]) -> None:
    """20/20/60 within painter, without fragments caused by sparse collection cells."""
    for painter in PAINTER_IDS:
        eligible = sorted(
            (r for r in rows if r["painter_id"] == painter and not r["exposure_matches"]),
            key=lambda r: (r["role_hash"], r["work_id"]),
        )
        for rank, row in enumerate(eligible):
            row["role"] = ("development", "qualification", "confirmation", "confirmation",
                           "confirmation")[rank % 5]
            row["role_rank"] = rank
    for row in rows:
        if row["exposure_matches"]:
            row["role"] = "historical_development"
            row["role_rank"] = None


def build_frame(root: Path, frame_id: str) -> dict:
    identifier(frame_id)
    output = root / MANIFESTS / frame_id
    if output.exists():
        raise FileExistsError(output)
    admitted = {r["item_qid"]: r for r in read_jsonl(root / DETERMINATION) if r["admitted"]}
    source: dict[str, list] = defaultdict(list)
    for row in read_jsonl(root / CENSUS):
        if row["item_qid"] in admitted:
            source[row["item_qid"]].append(row)
    records = []
    for qid, decision in sorted(admitted.items()):
        candidates = source[qid]
        selected = [r for r in candidates if r["media"].get("canonical_title")
                    == decision["surrogate"]["commons_filename"]]
        if len(selected) != 1:
            raise ValueError(f"surrogate does not have exactly one metadata record: {qid}")
        record = selected[0]
        entity, media = record["entity"], record["media"]
        if urlsplit(media["original_url"]).hostname != "upload.wikimedia.org":
            raise ValueError("unexpected media host")
        records.append(dict(
            item_qid=qid, painter_id=decision["painter_id"], label=decision["label"],
            content_class=decision["content_class"],
            collections=sorted(set(entity["collection_qids"])),
            accessions=sorted(set(entity["inventory_numbers"])),
            object_urls=sorted(set(entity["described_at_urls"] + entity["reference_urls"])),
            surrogate=dict(decision["surrogate"], expected_sha1=media["mediawiki_sha1"],
                           expected_width=media["original_width"],
                           expected_height=media["original_height"],
                           metadata_sha256=digest(media),
                           origin_urls=sorted(set(media["metadata_urls"])),
                           profile_status="not_yet_decoded"),
        ))
    denylist = read_jsonl(root / DENYLIST)
    frame, conflicts = [], []
    for group in work_components(records):
        qids = sorted(r["item_qid"] for r in group)
        if len({r["painter_id"] for r in group}) != 1:
            conflicts.append({"item_qids": qids, "reason": "conflicting_painter_identity"})
            continue
        winner = max(group, key=lambda r: (r["surrogate"]["short_side"],
                                           r["surrogate"]["commons_filename"]))
        work_id = "wikidata:" + qids[0]
        row = dict(
            work_id=work_id, item_qids=qids, painter_id=winner["painter_id"],
            labels=sorted({r["label"] for r in group}), content_class=winner["content_class"],
            collections=sorted({c for r in group for c in r["collections"]}),
            accessions=sorted({a for r in group for a in r["accessions"]}),
            object_urls=sorted({u for r in group for u in r["object_urls"]}),
            surrogate=winner["surrogate"],
            identity_basis="recorded_qid_and_unambiguous_collection_accession",
            capture_workflow="unresolved",  # A collection is not a capture programme.
            role_hash=digest(["pfg-v2/1.0-role", work_id]),
        )
        row["exposure_matches"] = exposure_matches(row, denylist)
        frame.append(row)
    assign_roles(frame)
    counts = {p: dict(Counter(r["role"] for r in frame if r["painter_id"] == p))
              for p in PAINTER_IDS}
    report = dict(
        schema_version="pfg-v2-frame/1.0", frame_id=frame_id,
        input_admissions=len(admitted), reconciled_records=len(frame), role_counts=counts,
        identity_conflicts=conflicts, merged_record_count=len(records) - len(frame)
        - sum(len(x["item_qids"]) for x in conflicts),
        exposure_matched_records=sum(bool(r["exposure_matches"]) for r in frame),
        unresolved_denylist_entries=[r["physical_work_id"] for r in denylist
                                    if r.get("denylisted") and not r.get("wikidata_qid")
                                    and not r.get("title") and not r.get("accession")],
        limitation="Capture origin and complete physical-work identity are not verified. "
                   "Exposure matches are conservative but incomplete where identifiers are absent.",
        inputs=bindings(root, [DETERMINATION, CENSUS, DENYLIST, PROMPTS, PROTOCOL,
                              Path(__file__).resolve().relative_to(root.resolve())]),
    )
    publish(output / "frame.jsonl", frame, lines=True)
    report["frame_sha256"] = hash_file(output / "frame.jsonl")
    publish(output / "frame_receipt.json", report)
    return report
