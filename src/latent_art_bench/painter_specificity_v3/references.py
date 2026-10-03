"""Reference panels for the v3 painter groups: census to measured features, one stage at a time.

Each stage reads the previous stage's create-once record, writes its own, and binds its inputs
by SHA-256. The rules are ``studies/painter_specificity_v3/REFERENCES.md``; every rule that is
not listed there as a difference is the four-painter rule, reused from
``painter_feature_generation_v1`` and ``painter_feature_generation_v2`` where possible.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import httpx

from latent_art_bench.io import hash_file, read_jsonl, utc_now
from latent_art_bench.painter_feature_generation_v1 import federated_census as fc
from latent_art_bench.painter_feature_generation_v1.determine import (
    CANVAS,
    GATES,
    MINIMUM_SHORT_SIDE,
    OIL_PAINT,
    PAINTING,
    File,
)
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    identifier,
    publish,
    stage_lock,
)
from latent_art_bench.painter_feature_generation_v2.corpus import work_components
from latent_art_bench.painter_feature_generation_v2.renderings import (
    intents,
    select_rendering,
    wait_seconds,
)
from latent_art_bench.painter_feature_generation_v2.renderings_r2 import fetch, inspect_body
from latent_art_bench.painter_specificity_v3 import lexicon
from latent_art_bench.painter_specificity_v3.panel import ALL, BY_ID, FLOOR, PAINTERS

NAMESPACE = "painter_specificity_v3"
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
RULES = Path("studies/painter_specificity_v3/REFERENCES.md")
SELF = Path("src/latent_art_bench/painter_specificity_v3/references.py")
PANEL = Path("src/latent_art_bench/painter_specificity_v3/panel.py")
LEXICON = Path("src/latent_art_bench/painter_specificity_v3/lexicon.py")
# Wikimedia's robot policy asks for contact information; the four-painter pipeline sent the same.
USER_AGENT = ("LatentArtBench/0.3 research (painter specificity v3 references; "
              "+https://github.com/isingmodel/latent-art-bench)")
SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
# The four-painter discovery query (painter_feature_generation_v1.broad_wikidata).
QUERY = (
    "SELECT DISTINCT ?item ?image WHERE {{ ?item wdt:P170 wd:{qid}; "
    "wdt:P31 wd:Q3305213; wdt:P18 ?image. }} ORDER BY STR(?item) STR(?image)"
)
TRACKED = ("P18", "P170", "P31", "P186", "P195", "P217", "P973", "P276", "P571", "P6216")
EXTMETADATA = (
    "LicenseShortName|LicenseUrl|UsageTerms|Copyrighted|Restrictions|Permission|Artist|"
    "Institution|Credit|Source|ObjectName|ImageDescription"
)
BATCH = 40
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
RETRYABLE_API = {"internal_api_error", "maxlag", "ratelimited", "readonly"}


def run_dir(root: Path, run: str) -> Path:
    return root / MANIFESTS / identifier(run)


def _store(root: Path, run: str, body: bytes, subdir: str) -> tuple[str, str]:
    sha = hashlib.sha256(body).hexdigest()
    relative = WORKSPACE / run / subdir / sha
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if hash_file(path) != sha:
            raise ValueError("content-addressed evidence changed")
    else:
        with path.open("xb") as handle:
            handle.write(body)
    return str(relative), sha


def _api_error(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("error"), dict):
        return str(payload["error"].get("code") or "unknown")
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        codes = {str(e.get("code")) for e in errors if isinstance(e, dict)}
        return codes.pop() if len(codes) == 1 else "multiple"
    return None


def _get(
    client: httpx.Client,
    ledger: Path,
    root: Path,
    run: str,
    request_id: str,
    url: str,
    params: dict,
    *,
    accept: str = "application/json",
    attempts: int = 5,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[dict, str]:
    """One logged request: an attempt event before the call, a response event after it.

    A request that already has a successful, hash-intact response in the ledger is not repeated.
    """
    for row in reversed(events(ledger)):
        if (row["kind"] == "response" and row["request_id"] == request_id
                and row.get("http_status") == 200 and row.get("error") is None
                and hash_file(root / row["raw_path"]) == row["raw_sha256"]):
            return json.loads((root / row["raw_path"]).read_bytes()), row["raw_sha256"]
    for attempt in range(1, attempts + 1):
        append_event(ledger, dict(kind="attempt", request_id=request_id, attempt=attempt,
                                  url=url, params=params))
        delay = wait_seconds(None, min(attempt, 2))
        try:
            response = client.get(url, params=params, headers={"Accept": accept})
        except httpx.TransportError as exc:
            append_event(ledger, dict(kind="response", request_id=request_id, attempt=attempt,
                                      error=type(exc).__name__))
        else:
            path, sha = _store(root, run, response.content, "responses")
            payload, error = None, None
            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError:
                    error = "invalid_json"
                error = error or _api_error(payload)
            append_event(ledger, dict(kind="response", request_id=request_id, attempt=attempt,
                                      http_status=response.status_code, raw_path=path,
                                      raw_sha256=sha, error=error))
            if response.status_code == 200 and error is None and isinstance(payload, dict):
                return payload, sha
            if response.status_code not in RETRYABLE_HTTP and error not in RETRYABLE_API:
                raise RuntimeError(f"{request_id}: http {response.status_code}, {error}")
            delay = min(60.0, wait_seconds(response.headers.get("retry-after"), min(attempt, 2)))
        if attempt < attempts:
            sleep(delay)
    raise RuntimeError(f"{request_id}: no success after {attempts} attempts")


def _client(transport: httpx.BaseTransport | None = None, timeout: float = 60) -> httpx.Client:
    return httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False,
                        transport=transport, headers={"User-Agent": USER_AGENT})


def _receipt(root: Path, output: Path, name: str, inputs: list[Path], **fields: Any) -> dict:
    receipt = dict(stage=name, completed_at_utc=utc_now().isoformat(),
                   inputs=bindings(root, inputs), **fields)
    publish(output / f"{name}_receipt.json", receipt)
    return receipt


# Stage 1: discovery census --------------------------------------------------------------------


def filename(image_uri: str) -> str:
    marker = "/wiki/Special:FilePath/"
    parsed = urllib.parse.urlsplit(image_uri)
    if parsed.netloc != "commons.wikimedia.org" or not parsed.path.startswith(marker):
        raise ValueError(f"unexpected image URI: {image_uri}")
    raw = parsed.path.split(marker, 1)[1]
    return urllib.parse.unquote_to_bytes(raw).decode("utf-8").replace("_", " ")


def census(root: Path, run: str, *, transport=None, sleep=time.sleep) -> dict:
    output = run_dir(root, run)
    if (output / "census.jsonl").exists():
        raise FileExistsError("census is terminal")
    ledger = output / "census_events.jsonl"
    rows, seen = [], set()
    with stage_lock(root / WORKSPACE / run / ".census.lock"), _client(transport, 120) as client:
        for painter in ALL:
            payload, sha = _get(client, ledger, root, run, f"sparql-{painter.painter_id}", SPARQL,
                                {"query": QUERY.format(qid=painter.qid), "format": "json"},
                                accept="application/sparql-results+json", sleep=sleep)
            for binding in payload["results"]["bindings"]:
                item = binding["item"]["value"].rsplit("/", 1)[-1]
                key = (painter.painter_id, item, filename(binding["image"]["value"]))
                if key not in seen:
                    seen.add(key)
                    rows.append(dict(painter_id=key[0], creator_qid=painter.qid, item_qid=key[1],
                                     commons_filename=key[2], response_sha256=sha))
            sleep(5)
    rows.sort(key=lambda r: (r["painter_id"], int(r["item_qid"][1:]), r["commons_filename"]))
    publish(output / "census.jsonl", rows, lines=True)
    counts = {p.painter_id: len({r["item_qid"] for r in rows if r["painter_id"] == p.painter_id})
              for p in ALL}
    return _receipt(root, output, "census", [SELF, PANEL, RULES, MANIFESTS / run / "census.jsonl",
                                               MANIFESTS / run / "census_events.jsonl"],
                    rows=len(rows), items_by_painter=counts, query_template=QUERY)


# Stage 2: Wikidata entities and Commons file metadata -----------------------------------------


def _entity(entity: dict) -> dict:
    labels, descriptions = entity.get("labels", {}), entity.get("descriptions", {})
    first = lambda m: next((m[k]["value"] for k in ("en", "fr") if k in m), None)  # noqa: E731
    return dict(
        entity_status="resolved",
        resolved_entity_qid=entity.get("id"),
        label=first(labels),
        description=first(descriptions),
        best_rank_claims={p: fc._statement_records(entity, p) for p in TRACKED},
        collection_qids=[str(v) for v in fc._statement_values(entity, "P195")],
        inventory_numbers=[str(v) for v in fc._statement_values(entity, "P217")],
        described_at_urls=[str(v) for v in fc._statement_values(entity, "P973")],
        reference_urls=_reference_urls(entity),
    )


def _reference_urls(entity: dict) -> list[str]:
    """P854 reference URLs of best-rank claims; informational, so malformed ones are skipped."""
    urls = set()
    for claims in (entity.get("claims") or {}).values():
        preferred = [c for c in claims if c.get("rank") == "preferred"]
        for claim in preferred or [c for c in claims if c.get("rank", "normal") == "normal"]:
            for reference in claim.get("references", []):
                for snak in reference.get("snaks", {}).get("P854", []):
                    try:
                        urls.add(fc._p854_reference_url(snak))
                    except fc.CensusError:
                        continue
    return sorted(urls)


def _media(title: str, page: dict) -> dict:
    rows = page.get("imageinfo") or []
    if len(rows) != 1:
        return dict(media_status="missing", canonical_title=title)
    info, meta = rows[0], rows[0].get("extmetadata") or {}
    text = lambda key: fc._plain_text(fc._metadata_value(meta, key))  # noqa: E731
    width, height = int(info.get("width") or 0), int(info.get("height") or 0)
    return dict(
        media_status="resolved",
        canonical_title=page["title"],
        original_url=info.get("url"),
        description_url=info.get("descriptionurl"),
        original_width=width,
        original_height=height,
        original_short_side=min(width, height),
        mime=str(info.get("mime") or "").casefold(),
        mediawiki_sha1=str(info.get("sha1") or ""),
        media_timestamp=info.get("timestamp"),
        license_short_name=text("LicenseShortName"),
        license_url=text("LicenseUrl"),
        usage_terms=text("UsageTerms"),
        copyrighted=text("Copyrighted"),
        restrictions=text("Restrictions"),
        artist_text=text("Artist"),
        institution_text=text("Institution"),
        credit_text=text("Credit"),
        object_name=text("ObjectName"),
        metadata_urls=fc._metadata_urls(meta, ("Institution", "Credit", "Source",
                                               "ImageDescription")),
    )


def metadata(root: Path, run: str, *, transport=None, sleep=time.sleep) -> dict:
    output = run_dir(root, run)
    if (output / "metadata.jsonl").exists():
        raise FileExistsError("metadata is terminal")
    rows = read_jsonl(output / "census.jsonl")
    qids = sorted({r["item_qid"] for r in rows}, key=lambda q: int(q[1:]))
    titles = sorted({"File:" + r["commons_filename"] for r in rows},
                    key=lambda t: (t.casefold(), t))
    ledger = output / "metadata_events.jsonl"
    entities: dict[str, dict] = {}
    media: dict[str, dict] = {}
    with stage_lock(root / WORKSPACE / run / ".metadata.lock"), _client(transport) as client:
        for index in range(0, len(qids), BATCH):
            batch = qids[index: index + BATCH]
            payload, _ = _get(client, ledger, root, run, f"entities-{index // BATCH:04d}", WIKIDATA,
                              dict(action="wbgetentities", ids="|".join(batch), format="json",
                                   props="info|claims|labels|descriptions", languages="en|fr",
                                   languagefallback="1", maxlag="5"), sleep=sleep)
            found = payload.get("entities", {})
            for qid in batch:
                entity = found.get(qid) or next(
                    (e for e in found.values() if e.get("redirects", {}).get("from") == qid), None)
                entities[qid] = (dict(entity_status="missing") if not entity or "missing" in entity
                                 else _entity(entity))
            sleep(0.75)
        for index in range(0, len(titles), BATCH):
            batch = titles[index: index + BATCH]
            payload, _ = _get(client, ledger, root, run, f"imageinfo-{index // BATCH:04d}", COMMONS,
                              dict(action="query", prop="imageinfo", titles="|".join(batch),
                                   iiprop="url|size|mime|sha1|timestamp|extmetadata",
                                   iiextmetadatafilter=EXTMETADATA, iiextmetadatalanguage="en",
                                   format="json", formatversion="2", maxlag="5"), sleep=sleep)
            query = payload.get("query", {})
            renamed = {n["from"]: n["to"] for n in query.get("normalized", [])}
            pages = {p["title"]: p for p in query.get("pages", [])}
            for title in batch:
                page = pages.get(renamed.get(title, title))
                media[title] = _media(title, page) if page else dict(media_status="missing",
                                                                     canonical_title=title)
            sleep(0.75)
    out = [dict(r, entity=entities[r["item_qid"]], media=media["File:" + r["commons_filename"]])
           for r in rows]
    publish(output / "metadata.jsonl", out, lines=True)
    return _receipt(root, output, "metadata",
                    [SELF, MANIFESTS / run / "census.jsonl", MANIFESTS / run / "metadata.jsonl",
                     MANIFESTS / run / "metadata_events.jsonl"],
                    rows=len(out), entities=len(entities), files=len(media),
                    missing_entities=sum(e["entity_status"] != "resolved"
                                         for e in entities.values()),
                    missing_files=sum(m["media_status"] != "resolved" for m in media.values()))


# Stage 3: the seven gates ---------------------------------------------------------------------


def items(rows: list[dict]) -> list[dict]:
    """Group metadata rows into items: one label and claim set, every offered file."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["item_qid"]].append(row)
    result = []
    for qid, group in grouped.items():
        entity = group[0]["entity"]
        claims = {p: tuple(str(c["value"]) for c in v)
                  for p, v in (entity.get("best_rank_claims") or {}).items()}
        files = tuple(
            File(name=m["canonical_title"], licence=m.get("license_short_name", ""),
                 restriction=m.get("restrictions", ""), short_side=m.get("original_short_side", 0),
                 url=m.get("original_url") or "")
            for m in (r["media"] for r in group) if m.get("media_status") == "resolved"
        )
        result.append(dict(painter_id=group[0]["painter_id"], item_qid=qid,
                           label=entity.get("label") or "", claims=claims, files=files))
    return result


def decide(item: dict) -> dict:
    """The four-painter gates, in order, first failure wins (determine.decide), lexicon v3."""
    values = lambda p: item["claims"].get(p, ())  # noqa: E731
    painter = BY_ID[item["painter_id"]]
    verdict = dict(painter_id=item["painter_id"], item_qid=item["item_qid"],
                   label=item["label"], admitted=False, failed_gate=None, content_class=None,
                   surrogate=None)
    if values("P170") != (painter.qid,):
        return dict(verdict, failed_gate="creator")
    if PAINTING not in values("P31"):
        return dict(verdict, failed_gate="painting")
    if not {OIL_PAINT, CANVAS} <= set(values("P186")):
        return dict(verdict, failed_gate="medium")
    if not values("P195"):
        return dict(verdict, failed_gate="collection")
    licensed = [f for f in item["files"] if f.open_rights]
    if not licensed:
        return dict(verdict, failed_gate="rights")
    large = [f for f in licensed if f.short_side >= MINIMUM_SHORT_SIDE]
    if not large:
        return dict(verdict, failed_gate="geometry")
    best = max(large, key=lambda f: (f.short_side, f.name))
    surrogate = dict(commons_filename=best.name, licence=best.licence,
                     short_side=best.short_side, url=best.url)
    content = lexicon.classify(item["label"])
    if content["disposition"] != lexicon.ELIGIBLE:
        return dict(verdict, failed_gate="content", surrogate=surrogate,
                    content_disposition=content["disposition"])
    return dict(verdict, admitted=True, surrogate=surrogate, content_class=content["primary_class"])


def determine(root: Path, run: str) -> dict:
    output = run_dir(root, run)
    if (output / "determination.jsonl").exists():
        raise FileExistsError("determination is terminal")
    publish(output / "content_lexicon.json", lexicon.render())
    decisions = [decide(i) for i in items(read_jsonl(output / "metadata.jsonl"))]
    decisions.sort(key=lambda r: (r["painter_id"], int(r["item_qid"][1:])))
    publish(output / "determination.jsonl", decisions, lines=True)
    funnel = {}
    for painter in ALL:
        mine = [d for d in decisions if d["painter_id"] == painter.painter_id]
        depth = Counter(len(GATES) if d["admitted"] else GATES.index(d["failed_gate"])
                        for d in mine)
        funnel[painter.painter_id] = dict(
            discovered=len(mine),
            **{f"passed_{g}": sum(n for k, n in depth.items() if k > i)
               for i, g in enumerate(GATES)},
            classes=dict(Counter(d["content_class"] for d in mine if d["admitted"])),
        )
    return _receipt(root, output, "determination",
                    [SELF, LEXICON, RULES, MANIFESTS / run / "metadata.jsonl",
                     MANIFESTS / run / "content_lexicon.json",
                     MANIFESTS / run / "determination.jsonl"],
                    gate_order=list(GATES), funnel=funnel)


# Stage 4: frame -------------------------------------------------------------------------------


def frame(root: Path, run: str) -> dict:
    output = run_dir(root, run)
    if (output / "frame.jsonl").exists():
        raise FileExistsError("frame is terminal")
    admitted = {d["item_qid"]: d for d in read_jsonl(output / "determination.jsonl")
                if d["admitted"]}
    by_item = defaultdict(list)
    for row in read_jsonl(output / "metadata.jsonl"):
        if row["item_qid"] in admitted:
            by_item[row["item_qid"]].append(row)
    records = []
    for qid, decision in sorted(admitted.items()):
        chosen = [r for r in by_item[qid]
                  if r["media"].get("canonical_title") == decision["surrogate"]["commons_filename"]]
        if len(chosen) != 1:
            raise ValueError(f"surrogate does not have exactly one metadata record: {qid}")
        entity, media = chosen[0]["entity"], chosen[0]["media"]
        if urllib.parse.urlsplit(media["original_url"]).hostname != "upload.wikimedia.org":
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
                           metadata_sha256=digest(media)),
        ))
    rows, conflicts = [], []
    for component in work_components(records):
        qids = sorted((r["item_qid"] for r in component), key=lambda q: int(q[1:]))
        if len({r["painter_id"] for r in component}) != 1:
            conflicts.append(dict(item_qids=qids, reason="conflicting_painter_identity"))
            continue
        winner = max(component, key=lambda r: (r["surrogate"]["short_side"],
                                               r["surrogate"]["commons_filename"]))
        rows.append(dict(
            work_id="wikidata:" + qids[0], item_qids=qids, painter_id=winner["painter_id"],
            labels=sorted({r["label"] for r in component}), content_class=winner["content_class"],
            collections=sorted({c for r in component for c in r["collections"]}),
            accessions=sorted({a for r in component for a in r["accessions"]}),
            object_urls=sorted({u for r in component for u in r["object_urls"]}),
            surrogate=winner["surrogate"], role="reference",
            identity_basis="recorded_qid_and_unambiguous_collection_accession",
        ))
    rows.sort(key=lambda r: (r["painter_id"], int(r["work_id"].split(":Q")[1])))
    publish(output / "frame.jsonl", rows, lines=True)
    return _receipt(root, output, "frame",
                    [SELF, MANIFESTS / run / "determination.jsonl",
                     MANIFESTS / run / "frame.jsonl"],
                    admitted_items=len(admitted), works=len(rows), conflicts=conflicts,
                    merged=len(records) - len(rows) - sum(len(c["item_qids"]) for c in conflicts),
                    works_by_painter=dict(Counter(r["painter_id"] for r in rows)))


# Stage 5: rendering metadata (the documented Commons thumbnail sizes) -------------------------


def renderings(root: Path, run: str, painters: tuple[str, ...] | None = None, *,
               transport=None, sleep=time.sleep) -> dict:
    output = run_dir(root, run)
    if (output / "renderings.jsonl").exists():
        raise FileExistsError("renderings are terminal")
    wanted = set(painters or (p.painter_id for p in PAINTERS))
    works = [r for r in read_jsonl(output / "frame.jsonl") if r["painter_id"] in wanted]
    requests = intents(works)
    ledger = output / "rendering_events.jsonl"
    pages = {}
    with stage_lock(root / WORKSPACE / run / ".renderings.lock"), _client(transport) as client:
        for request in requests:
            payload, _ = _get(client, ledger, root, run, request["request_id"], COMMONS,
                              request["params"], sleep=sleep)
            for page in payload["query"]["pages"]:
                pages[request["width"], page["title"].replace("_", " ")] = page
            sleep(1)
    rows = []
    for work in works:
        source = work["surrogate"]
        width, height = source["expected_width"], source["expected_height"]
        desired = min(width, math.ceil(width * 1536 / min(width, height) / 512) * 512)
        page = pages.get((desired, source["commons_filename"].replace("_", " ")), {})
        rows.append(select_rendering(work, page))
    publish(output / "renderings.jsonl", rows, lines=True)
    return _receipt(root, output, "renderings",
                    [SELF, MANIFESTS / run / "frame.jsonl", MANIFESTS / run / "renderings.jsonl",
                     MANIFESTS / run / "rendering_events.jsonl"],
                    painters=sorted(wanted), requests=len(requests),
                    statuses=dict(Counter(r["status"] for r in rows)))


# Stage 6: image acquisition -------------------------------------------------------------------


def acquire(root: Path, run: str, *, transport=None, sleep=time.sleep) -> dict:
    output = run_dir(root, run)
    if (output / "acquisitions.jsonl").exists():
        raise FileExistsError("acquisition is terminal")
    frame_rows = {r["work_id"]: r for r in read_jsonl(output / "frame.jsonl")}
    ledger = output / "acquisition_events.jsonl"
    previous = events(ledger)
    attempts = Counter(r["work_id"] for r in previous if r["kind"] == "attempt")
    done = {r["work_id"]: r for r in previous if r["kind"] == "terminal"}
    rows = read_jsonl(output / "renderings.jsonl")
    with stage_lock(root / WORKSPACE / run / ".acquisition.lock"), _client(transport, 90) as client:
        for index, row in enumerate(rows):
            if row["work_id"] in done:
                continue
            source = frame_rows[row["work_id"]]["surrogate"]
            request = dict(row, source_width=source["expected_width"],
                           source_height=source["expected_height"])
            outcome = dict(row, kind="terminal", status="failed", error=row.get("error"))
            if row["status"] == "rendering_registered":
                outcome["error"] = "attempt_budget_exhausted"
                for attempt in range(attempts[row["work_id"]] + 1, 4):
                    append_event(ledger, dict(kind="attempt", work_id=row["work_id"],
                                              attempt=attempt))
                    status, headers, body, error = fetch(client, row["url"])
                    path, sha = _store(root, run, body, "raw")
                    append_event(ledger, dict(kind="response", work_id=row["work_id"],
                                              attempt=attempt, http_status=status, raw_path=path,
                                              raw_sha256=sha, error=error))
                    outcome.update(raw_path=path, raw_sha256=sha, http_status=status,
                                   bytes=len(body), error=error or f"http_{status}")
                    if error == "response_ceiling":
                        break
                    if not error and status == 200:
                        try:
                            outcome.update(inspect_body(body, request), status="acquired",
                                           error=None)
                        except (ValueError, OSError) as exc:
                            outcome["error"] = str(exc)
                        break
                    if not error and status != 429 and status < 500:
                        break
                    if attempt < 3:
                        sleep(wait_seconds(headers.get("retry-after"), attempt))
            done[row["work_id"]] = append_event(ledger, outcome)
            if (index + 1) % 25 == 0 or index + 1 == len(rows):
                print(f"acquired {index + 1}/{len(rows)} "
                      f"{dict(Counter(r['status'] for r in done.values()))}", flush=True)
            sleep(1)
    ordered = [done[r["work_id"]] for r in rows]
    publish(output / "acquisitions.jsonl", ordered, lines=True)
    return _receipt(root, output, "acquisition",
                    [SELF, MANIFESTS / run / "renderings.jsonl",
                     MANIFESTS / run / "acquisitions.jsonl",
                     MANIFESTS / run / "acquisition_events.jsonl"],
                    statuses=dict(Counter(r["status"] for r in ordered)),
                    acquired_by_painter=dict(Counter(r["painter_id"] for r in ordered
                                                     if r["status"] == "acquired")))


# Stage 7: features ----------------------------------------------------------------------------


def measure_file(path: Path) -> dict:
    """Full view and central 512 square, as for the four-painter references and outputs."""
    normalized = features.normalize(path, short_side=512)
    rgb = normalized.rgb
    height, width = rgb.shape[:2]
    top, left = (height - 512) // 2, (width - 512) // 2
    return dict(
        values=[float(v) for v in features.extract(rgb)],
        square_values=[float(v) for v in features.extract(rgb[top: top + 512, left: left + 512])],
        normalization=normalized.metadata,
    )


def measure(root: Path, run: str) -> dict:
    output = run_dir(root, run)
    if (output / "features.jsonl").exists():
        raise FileExistsError("measurement is terminal")
    frame_rows = {r["work_id"]: r for r in read_jsonl(output / "frame.jsonl")}
    rows = []
    for row in read_jsonl(output / "acquisitions.jsonl"):
        if row["status"] != "acquired":
            continue
        record = dict(work_id=row["work_id"], painter_id=row["painter_id"],
                      content_class=frame_rows[row["work_id"]]["content_class"],
                      raw_sha256=row["raw_sha256"])
        path = root / row["raw_path"]
        if hash_file(path) != row["raw_sha256"]:
            raise ValueError(f"acquired evidence changed: {row['work_id']}")
        try:
            record.update(measure_file(path), status="measured")
        except Exception as exc:  # Recorded and excluded, as for the four-painter panel.
            record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        rows.append(record)
    publish(output / "features.jsonl", rows, lines=True)
    measured = Counter(r["painter_id"] for r in rows if r["status"] == "measured")
    return _receipt(root, output, "measurement",
                    [SELF, Path("src/latent_art_bench/painter_feature_generation_v2/features.py"),
                     MANIFESTS / run / "acquisitions.jsonl", MANIFESTS / run / "features.jsonl"],
                    measured_by_painter=dict(measured),
                    failures=[dict(work_id=r["work_id"], error=r["error"])
                              for r in rows if r["status"] != "measured"],
                    below_floor=sorted(p.painter_id for p in PAINTERS
                                       if measured[p.painter_id] < FLOOR))
