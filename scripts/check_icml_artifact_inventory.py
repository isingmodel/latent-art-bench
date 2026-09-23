"""Build/check the selected local ICML pixel inventory; no copy, upload, or download."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

from latent_art_bench.painter_feature_generation_v2.artifacts import digest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/icml_review_v1"
GENERATED = "data/manifests/painter_specificity_v2/psv2-20260911"
METHOD = "data/manifests/painter_feature_generation_v2/pfg2-method-20260905"
ACQUISITIONS = (
    "data/manifests/painter_feature_generation_v2/pfg2-renderings-r2-20260905/"
    "acquisitions.jsonl"
)
FRAME = "data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl"
CANDIDATES = (
    "data/manifests/painter_feature_generation_v1/"
    "broad_media_followup_publication_r2/candidates.jsonl"
)
AUDITS = [
    "reports/painter_reference_quality_v1/audit_monet.json",
    "reports/painter_reference_quality_v1/audit_others.json",
]
ALLOWED_GENERATED = Path("research_workspace/painter_specificity_v2/psv2-20260911/images")
ALLOWED_HISTORICAL = Path(
    "research_workspace/painter_feature_generation_v2/pfg2-renderings-r2-20260905/raw"
)
MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp", "TIFF": "image/tiff"}


def read(path):
    return json.loads((ROOT / path).read_text())


def rows(path):
    return [json.loads(line) for line in (ROOT / path).read_text().splitlines() if line]


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def unique(rows_, key):
    result = {r[key]: r for r in rows_}
    if len(result) != len(rows_):
        raise ValueError(f"duplicate {key}")
    return result


def verify_pixel(path, expected_sha, cohort):
    relative = Path(path)
    allowed = ALLOWED_GENERATED if cohort == "generated" else ALLOWED_HISTORICAL
    if relative.is_absolute() or relative.parent != allowed:
        raise ValueError("pixel is outside the selected-cohort path allowlist")
    full = ROOT / relative
    if full.is_symlink() or full.resolve().parent != (ROOT / allowed).resolve():
        raise ValueError("pixel path escapes its cohort directory")
    if cohort != "generated" and relative.name != expected_sha:
        raise ValueError("historical content-addressed filename differs")
    if sha(full) != expected_sha:
        raise ValueError("original pixel hash differs: " + path)
    with Image.open(full) as image:
        if image.format not in MIME:
            raise ValueError("unrecognized original media type")
        metadata = dict(
            detected_format=image.format, media_type=MIME[image.format],
            width=image.width, height=image.height,
        )
    return dict(source_path=path, sha256=expected_sha, bytes=full.stat().st_size, **metadata)


def build():
    requests = unique(rows(GENERATED + "/requests.jsonl"), "id")
    collection = read(GENERATED + "/collection.json")
    outcomes = unique(collection["outcomes"], "id")
    if len(requests) != 1008 or outcomes.keys() != requests.keys():
        raise ValueError("generated membership differs from the complete selected cohort")
    reference = [r for r in rows(METHOD + "/confirmation_features.jsonl")
                 if r["status"] == "measured"]
    development = [r for r in rows(METHOD + "/development_features.jsonl")
                   if r["role"] == "development"]
    if len(reference) != 649 or len(development) != 221:
        raise ValueError("reference/development membership changed")
    source = unique(reference + development, "image_id")
    audit = unique([r for p in AUDITS for r in read(p)["records"]], "image_id")
    acquisitions = unique(rows(ACQUISITIONS), "work_id")
    frame = unique(rows(FRAME), "work_id")
    if source.keys() != audit.keys() or len(source) != 870:
        raise ValueError("audit and selected source membership disagree")
    media = {}
    for candidate in rows(CANDIDATES):
        record = candidate["media"]
        key = digest(record)
        if key in media and media[key] != record:
            raise ValueError("ambiguous media metadata binding")
        media[key] = record
    inventory, attribution = [], []
    for id_, outcome in sorted(outcomes.items()):
        request = requests[id_]
        if not outcome["success"] or outcome["attempt"] != 1:
            raise ValueError("unexpected generated outcome")
        pixels = verify_pixel(outcome["image_path"], outcome["image_sha256"], "generated")
        if pixels["width"] != outcome["width"] or pixels["height"] != outcome["height"]:
            raise ValueError("generated dimensions differ")
        inventory.append(dict(
            id=id_, cohort="generated", **pixels, model=request["model"],
            scene=request["scene"], arm=request["arm"], repeat=request["repeat"],
            attribution_id=None,
        ))
    for id_, record in sorted(source.items()):
        a, acquisition, f = audit[id_], acquisitions[id_], frame[id_]
        cohort = "reference" if record["role"] == "confirmation" else "development"
        if (
            a["role"] != cohort or record["status"] != "measured"
            or a["raw_sha256"] != record["raw_sha256"]
            or acquisition["raw_sha256"] != record["raw_sha256"]
            or a["raw_path"] != acquisition["raw_path"]
            or a["painter_id"] != record["painter_id"]
        ):
            raise ValueError("selected historical source ancestry differs")
        pixels = verify_pixel(acquisition["raw_path"], record["raw_sha256"], cohort)
        if (
            pixels["width"] != acquisition["width"]
            or pixels["height"] != acquisition["height"]
            or pixels["bytes"] != acquisition["bytes"]
            or pixels["detected_format"] != acquisition["format"]
        ):
            raise ValueError("historical original metadata differs")
        metadata_sha = f["surrogate"]["metadata_sha256"]
        if metadata_sha not in media:
            raise ValueError("richer original media record is unavailable")
        m = media[metadata_sha]
        if (
            m["canonical_title"] != f["surrogate"]["commons_filename"]
            or m["license_short_name"] != acquisition["licence"]
        ):
            raise ValueError("source title/license metadata do not agree")
        inventory.append(dict(
            id=id_, cohort=cohort, **pixels, painter=record["painter_id"],
            attribution_id=id_, audited_region_box=a["region_box"],
        ))
        attribution.append(dict(
            id=id_, cohort=cohort, painter=record["painter_id"],
            source_path=pixels["source_path"], raw_sha256=pixels["sha256"],
            commons_filename=m["canonical_title"], source_page_url=m["description_url"],
            source_url=acquisition["url"], original_source_url=m["original_url"],
            source_kind=acquisition["source_kind"],
            source_timestamp=acquisition["source_timestamp"],
            recorded_license=m["license_short_name"], license_url=m["license_url"],
            artist_text=m["artist_text"], credit_text=m["credit_text"],
            audited_region_box=a["region_box"],
            metadata_sha256=metadata_sha, media_metadata=m,
        ))
    inventory.sort(key=lambda r: (r["cohort"], r["id"]))
    attribution.sort(key=lambda r: (r["cohort"], r["id"]))
    if len(inventory) != 1878 or len(attribution) != 870:
        raise ValueError("artifact inventory coverage changed")
    if len({r["sha256"] for r in inventory}) != 1878:
        raise ValueError("original payload identities are no longer distinct")
    inputs = [
        GENERATED + "/requests.jsonl", GENERATED + "/collection.json",
        METHOD + "/confirmation_features.jsonl", METHOD + "/development_features.jsonl",
        ACQUISITIONS, FRAME, CANDIDATES, *AUDITS,
        "src/latent_art_bench/painter_feature_generation_v2/artifacts.py",
        str(Path(__file__).relative_to(ROOT)),
    ]
    binding = {p: sha(ROOT / p) for p in inputs}
    availability = "local_only; no public archive or live URL recovery verified"
    return (
        dict(
            schema="icml-local-artifact-inventory/1.0", availability=availability,
            inputs=binding, counts=dict(Counter(r["cohort"] for r in inventory)),
            total_bytes=sum(r["bytes"] for r in inventory),
            excluded="response archives, credentials, unrelated cohorts, and all pixel copies",
            records=inventory,
        ),
        dict(
            schema="icml-local-artifact-attribution/1.0", availability=availability,
            inputs=binding, counts=dict(Counter(r["cohort"] for r in attribution)),
            license_counts=dict(Counter(r["recorded_license"] for r in attribution)),
            caveat=("Recorded source-file metadata, not a new rights determination. "
                    "The original media metadata is retained and canonically hash-bound."),
            records=attribution,
        ),
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--write", action="store_true", help="write only if both outputs are new")
    args = parser.parse_args()
    paths = [OUT / "artifact_inventory.json", OUT / "artifact_attribution.json"]
    if args.write and any(p.exists() for p in paths):
        raise FileExistsError("refusing to replace an existing artifact inventory")
    if not args.write and not all(p.is_file() for p in paths):
        raise FileNotFoundError("inventory files are missing; --write creates a new pair")
    results = build()
    for path, result in zip(paths, results):
        if args.write:
            with path.open("x") as stream:
                json.dump(result, stream, sort_keys=True, indent=2,
                          ensure_ascii=False, allow_nan=False)
                stream.write("\n")
        elif json.loads(path.read_text()) != result:
            raise ValueError("deterministic inventory replay differs: " + str(path))
    action = "Created" if args.write else "Verified"
    print(f"{action} 1,878 selected local originals and 870 hash-bound attribution records.")
    print(f"Original bytes: {results[0]['total_bytes']:,}; no copies, uploads, or downloads.")


if __name__ == "__main__":
    main()
