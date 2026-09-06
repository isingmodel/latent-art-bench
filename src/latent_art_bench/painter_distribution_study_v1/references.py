"""Prospective candidate identities and one-attempt reference acquisition, without features."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import time
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit

import httpx
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

NAMESPACE = "painter_distribution_study_v1"
RUN_ID = "pdsv1-reference-candidates-20260906"
DIRECTORY = Path("data/manifests") / NAMESPACE / RUN_ID
WORKSPACE = Path("research_workspace") / NAMESPACE / RUN_ID
SOURCE = Path(
    "data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl"
)
FRAME = Path("data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl")
DENYLIST = Path("data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl")
CONTRACT = Path("studies") / NAMESPACE / "REFERENCES.md"
MAX_BYTES = 64 * 1024**2
MIN_FREE = 5 * 1024**3
PAINTERS = {"claude_monet": "Q296", "paul_cezanne": "Q35548"}
EXCLUDE = re.compile(
    r"\b(portrait|self|madame|woman|women|man|bather|bathers|baigneu\w*|femme|homme|"
    r"still life|nature morte|vase|fruit|pommes|apple|basket|bouquet|jug|bottle|peaches|"
    r"joueur|card|onions|nude|nu|nue|harlequin|figure|statue|cupid)\b"
)
OUTDOOR = re.compile(
    r"\b(avenue|bosquet|forest|foret|undergrowth|montagne|mont|mountain|mountains|mount|hill|hills|"
    r"eau|water|sea|mer|seine|river|riverside|bank|banks|creek|pond|lilies|lily|nympheas|ocean|coast|"
    r"cliff|cliffs|beach|fishing|boat|boats|ships|port|harbour|harbor|bridge|pont|fontaine|route|road|"
    r"path|chemin|paysage|landscape|village|town|city|house|houses|maison|maisons|manor|domaine|rocher|"
    r"rocks|rock|ravine|cabin|cabane|cabanon|cistern|millstone|tranchee|bois|glade|meadow|field|fields|"
    r"farm|ferme|dam|trees|tree|arbres|arbre|promenade|rue|street|toits|rooftops|rooftop|copse|ridge|"
    r"peak|pilon|pigeonnier|campagne|garden|jardin|haystack|haystacks|hayrick|hayricks|meules|meule|"
    r"parliament|cathedral|cathedrale|palazzo|palace|palais|church|eglise|park|parc|poplars|peupliers|"
    r"willows|saule|willow|grove|orchard|snow|ice|sailing|regatta|detour)\b"
)


def normalized(value):
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", str(value or "").casefold())
        if not unicodedata.combining(c)
    ).strip()


def file_key(value):
    return normalized(unquote(value).removeprefix("File:").replace("_", " "))


def url_key(value):
    parsed = urlsplit(value)
    # Collection object identity often lives in ?id=; dropping all queries merges works.
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_")
    )
    return (
        (parsed.hostname or "").removeprefix("www.")
        + unquote(parsed.path).rstrip("/")
        + ("?" + urlencode(query) if query else "")
        + ("#" + parsed.fragment if parsed.fragment else "")
    )


def exposure_keys(frame, denylist):
    keys = set()
    for row in frame:
        keys.update(("qid", q) for q in row["item_qids"])
        keys.update(
            ("accession", c, normalized(a))
            for c in row["collections"]
            for a in row["accessions"]
            if a
        )
        keys.update(("url", url_key(u)) for u in row["object_urls"] if u)
        media = row["surrogate"] or {}
        if media.get("expected_sha1"):
            keys.add(("sha1", media["expected_sha1"]))
        if media.get("commons_filename"):
            keys.add(("file", file_key(media["commons_filename"])))
    for row in denylist:
        if row.get("wikidata_qid"):
            keys.add(("qid", row["wikidata_qid"]))
        if row.get("canonical_object_url"):
            keys.add(("url", url_key(row["canonical_object_url"])))
        keys.update(("file", file_key(f)) for f in row.get("commons_files", []))
    return keys


def candidate_keys(row):
    entity, media = row["entity"], row["media"]
    keys = {("qid", row["item_qid"])}
    keys.update(
        ("accession", c, normalized(a))
        for c in entity["collection_qids"]
        for a in entity["inventory_numbers"]
        if a
    )
    keys.update(("url", url_key(u)) for u in entity.get("described_at_urls", []) if u)
    keys.add(("file", file_key(media["canonical_title"])))
    keys.add(("sha1", media["mediawiki_sha1"]))
    return keys


def screen(row):
    """Title screening locates candidates only; pixels determine final content eligibility."""
    entity, media = row.get("entity") or {}, row.get("media") or {}
    painter = row.get("painter_id")
    if painter not in PAINTERS or entity.get("creator_qids") != [PAINTERS[painter]]:
        return "creator"
    if "Q3305213" not in entity.get("instance_qids", []) or not {"Q296955", "Q12321255"}.issubset(
        entity.get("material_qids", [])
    ):
        return "painting_oil_canvas"
    catalogue = any(
        (urlsplit(u).hostname or "").removeprefix("www.") == "cezannecatalogue.com"
        and urlsplit(u).path == "/catalogue/entry.php"
        and any(k == "id" and v.isdigit() for k, v in parse_qsl(urlsplit(u).query))
        for u in entity.get("described_at_urls", [])
    )
    if not entity.get("collection_qids") or not (entity.get("inventory_numbers") or catalogue):
        return "collection_work_identifier"
    if media.get("rights_candidate_status") != "commons_open_rights_marker_candidate":
        return "rights"
    if (media.get("original_short_side") or 0) < 512 or media.get("mime") not in (
        "image/jpeg",
        "image/png",
        "image/tiff",
        "image/webp",
    ):
        return "geometry_format"
    if not media.get("mediawiki_sha1") or not media.get("canonical_title"):
        return "delivery_identity"
    title = normalized(entity.get("label"))
    # The named house is a building, not a portrait; this explicit metadata exception
    # was specified before acquisition, not selected from feature outcomes.
    if row["item_qid"] == "Q3821663":
        return "candidate"
    if EXCLUDE.search(title) or not OUTDOOR.search(title):
        return "title_not_outdoor_candidate"
    return "candidate"


def select(rows, frame, denylist):
    exposed = exposure_keys(frame, denylist)
    audit, pool, known = [], [], set()
    # Resolve repeated discovery rows by stable metadata identity, not file aesthetics.
    for row in sorted(rows, key=lambda r: (r["item_qid"], r.get("commons_filename") or "")):
        if row.get("painter_id") not in PAINTERS:
            continue
        reason = screen(row)
        keys = candidate_keys(row) if reason == "candidate" else set()
        matches = sorted(keys & exposed)
        if matches:
            reason = "previous_exposure_identity"
        elif keys & known:
            reason = "duplicate_candidate_identity"
        if reason == "candidate":
            known.update(keys)
            pool.append(row)
        audit.append(
            dict(
                item_qid=row["item_qid"],
                painter_id=row["painter_id"],
                label=(row.get("entity") or {}).get("label"),
                disposition=reason,
                exposure_matches=matches,
            )
        )
    selected = []
    for painter in PAINTERS:
        candidates = [r for r in pool if r["painter_id"] == painter]
        candidates.sort(
            key=lambda r: digest(["pdsv1-reference-candidates-20260906", r["item_qid"]])
        )
        for row in candidates[:64]:
            entity, media = row["entity"], row["media"]
            selected.append(
                dict(
                    sequence=len(selected),
                    work_id="wikidata:" + row["item_qid"],
                    item_qid=row["item_qid"],
                    painter_id=painter,
                    label=entity["label"],
                    collections=entity["collection_qids"],
                    accessions=entity["inventory_numbers"],
                    authority_urls=entity.get("described_at_urls", []),
                    authority_basis="preserved Wikidata exact-creator oil-on-canvas record",
                    url=media["original_url"],
                    commons_filename=media["canonical_title"],
                    expected_sha1=media["mediawiki_sha1"],
                    expected_width=media["original_width"],
                    expected_height=media["original_height"],
                    license=media["license_short_name"],
                    license_url=media["license_url"],
                    rights_page=media["description_url"],
                    media_source_text=media.get("source_text"),
                    metadata_sha256=digest(row),
                    exposure="metadata_seen_pixels_and_features_not_in_recorded_prior_frame",
                    content_status="pending_visual_eligibility",
                    capture_workflow="unresolved",
                )
            )
    return audit, selected


def prepare(root):
    source_paths = [
        SOURCE,
        FRAME,
        DENYLIST,
        CONTRACT,
        Path("studies") / NAMESPACE / "PROTOCOL.md",
        Path("src/latent_art_bench") / NAMESPACE / "references.py",
        Path("tests") / NAMESPACE / "test_references.py",
        Path("src/latent_art_bench/io.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    commit = committed(root, source_paths)
    audit, selected = select(
        read_jsonl(root / SOURCE), read_jsonl(root / FRAME), read_jsonl(root / DENYLIST)
    )
    directory = root / DIRECTORY
    if directory.exists():
        raise FileExistsError("candidate stage identity already exists")
    if len(selected) > 128 or len({r["work_id"] for r in selected}) != len(selected):
        raise ValueError("candidate acquisition bound or work uniqueness failed")
    publish(directory / "screening.jsonl", audit, lines=True)
    publish(directory / "candidates.jsonl", selected, lines=True)
    freeze = dict(
        run_id=RUN_ID,
        recorded_git_commit=commit,
        inputs=bindings(root, source_paths),
        candidates_sha256=hash_file(directory / "candidates.jsonl"),
        screening_sha256=hash_file(directory / "screening.jsonl"),
        candidates_by_painter=dict(Counter(r["painter_id"] for r in selected)),
        dispositions=dict(Counter(r["disposition"] for r in audit)),
        authority="REFERENCES.md candidate acquisition only; no fidelity features",
    )
    publish(directory / "acquisition_freeze.json", freeze)
    return {k: v for k, v in freeze.items() if k not in ("inputs",)}


def acquire_one(root, candidate, *, transport=None):
    parsed = urlsplit(candidate["url"])
    if (
        parsed.scheme != "https"
        or parsed.hostname != "upload.wikimedia.org"
        or not parsed.path.startswith("/wikipedia/commons/")
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("acquisition URL is outside the frozen Commons media source")
    if not re.fullmatch(r"Q[1-9][0-9]*", candidate["item_qid"]):
        raise ValueError("invalid portable work identity")
    relative = WORKSPACE / "responses" / (candidate["item_qid"] + ".bin")
    target = root / relative
    if target.exists():
        raise FileExistsError("retained response already exists; no redispatch")
    body, status, complete, error = b"", None, False, None
    chunks, size = [], 0
    try:
        with httpx.Client(
            timeout=httpx.Timeout(90, connect=20),
            follow_redirects=False,
            transport=transport,
            headers={"User-Agent": "LatentArtBench/0.3 academic research"},
        ) as client:
            with client.stream("GET", candidate["url"]) as response:
                status = response.status_code
                for chunk in response.iter_bytes(chunk_size=65536):
                    if size + len(chunk) > MAX_BYTES:
                        error = "response_byte_limit"
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                else:
                    complete = True
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    body = b"".join(chunks)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    outcome, geometry = "failed_acquisition", None
    if complete and status == 200:
        if hashlib.sha1(body).hexdigest() != candidate["expected_sha1"]:
            outcome = "identity_hash_mismatch"
        else:
            try:
                with Image.open(io.BytesIO(body)) as im:
                    im.load()
                    geometry = dict(
                        width=im.width, height=im.height, mode=im.mode, format=im.format
                    )
                    outcome = "acquired" if min(im.size) >= 512 else "invalid_geometry"
            except (ValueError, OSError, Image.DecompressionBombError):
                outcome = "decode_failed"
    return dict(
        kind="terminal",
        work_id=candidate["work_id"],
        status=outcome,
        status_code=status,
        complete=complete,
        error=error,
        geometry=geometry,
        response_path=relative.as_posix(),
        response_sha256=hash_file(target),
        bytes=len(body),
    )


def acquire(root, *, transport=None, sleep=time.sleep):
    directory = root / DIRECTORY
    with stage_lock(root / WORKSPACE / ".acquisition.writer.lock"):
        freeze = read_json(directory / "acquisition_freeze.json")
        verify_bindings(root, freeze["inputs"])
        committed(
            root,
            [
                DIRECTORY / f
                for f in ("acquisition_freeze.json", "screening.jsonl", "candidates.jsonl")
            ],
        )
        if (directory / "acquisition_receipt.json").exists():
            raise ValueError("candidate acquisition is terminal")
        if hash_file(directory / "candidates.jsonl") != freeze["candidates_sha256"]:
            raise ValueError("candidate identity manifest changed")
        candidates = read_jsonl(directory / "candidates.jsonl")
        ledger = directory / "acquisition_events.jsonl"
        rows = events(ledger)
        attempts = {r["work_id"] for r in rows if r["kind"] == "attempt"}
        terminal = {r["work_id"] for r in rows if r["kind"] == "terminal"}
        if attempts != terminal:
            raise ValueError("unresolved acquisition intent; no automatic redispatch")
        for candidate in candidates:
            if candidate["work_id"] in terminal:
                continue
            if shutil.disk_usage(root).free < MIN_FREE + MAX_BYTES:
                raise OSError("storage reserve reached")
            sleep(2)
            append_event(
                ledger,
                dict(
                    kind="attempt",
                    work_id=candidate["work_id"],
                    url=candidate["url"],
                    candidate_sha256=digest(candidate),
                ),
            )
            row = acquire_one(root, candidate, transport=transport)
            append_event(ledger, row)
            print(json.dumps({k: row[k] for k in ("work_id", "status", "status_code")}), flush=True)
        receipt = dict(
            run_id=RUN_ID,
            candidates=len(candidates),
            dispositions=dict(
                Counter(r["status"] for r in events(ledger) if r["kind"] == "terminal")
            ),
            events_sha256=hash_file(ledger),
            freeze_sha256=hash_file(directory / "acquisition_freeze.json"),
            fidelity_features_extracted=0,
        )
        publish(directory / "acquisition_receipt.json", receipt)
        return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "acquire"))
    args = parser.parse_args()
    print(
        json.dumps(
            prepare(Path.cwd()) if args.command == "prepare" else acquire(Path.cwd()), indent=2
        )
    )


if __name__ == "__main__":
    main()
