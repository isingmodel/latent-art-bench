"""Retrospective painting-region and content-label sensitivity, original data intact."""

from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps

from latent_art_bench.painter_feature_generation_v2.features import extract, half_up
from latent_art_bench.painter_feature_generation_v2.statistics import fit_scaler, transform
from latent_art_bench.painter_specificity_measurement_v1.workflow import load, reference_records
from latent_art_bench.painter_specificity_reference_v1.analysis import CLASSES, FRAME
from latent_art_bench.painter_specificity_review_v1 import (
    CLASS_MAP,
    DEVELOPMENT,
    calibration,
    metrics,
)
from latent_art_bench.painter_specificity_v1.analysis import centered, interval
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_reference_quality_v1"
OUT = s.ROOT / "reports" / NS
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
AUDITS = (OUT / "audit_monet.json", OUT / "audit_others.json")
FULL = [0, 0, 1, 1]


def source_records():
    return [dict(v, role="reference") for v in reference_records()] + [
        v for v in s.rows(DEVELOPMENT) if v["role"] == "development"
    ]


def validate_box(box):
    if len(box) != 4 or not np.isfinite(box).all():
        raise ValueError("four finite normalized region coordinates required")
    left, top, right, bottom = box
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError("invalid painting region")


def normalize_region(path, box, short_side=512):
    """Original orientation/color rules, with an explicitly audited pre-resize region."""
    validate_box(box)
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as original:
            if original.format not in {"JPEG", "PNG", "TIFF", "WEBP"}:
                raise ValueError("unsupported image format")
            original.load()
            image = ImageOps.exif_transpose(original)
            if "A" in image.getbands() and image.getchannel("A").getextrema() != (255, 255):
                raise ValueError("nonopaque alpha is not a painting area")
            if "transparency" in image.info:
                if image.convert("RGBA").getchannel("A").getextrema() != (255, 255):
                    raise ValueError("nonopaque palette transparency")
            width, height = image.size
            profile = image.info.get("icc_profile")
            if profile:
                image = ImageCms.profileToProfile(
                    image,
                    ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                    ImageCms.createProfile("sRGB"),
                    renderingIntent=ImageCms.Intent.PERCEPTUAL,
                    outputMode="RGB",
                )
            else:
                if image.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
                    raise ValueError("unprofiled non-RGB color space")
                image = image.convert("RGB")
            pixels = [half_up(v * n) for v, n in zip(box, (width, height, width, height))]
            image = image.crop(pixels)
            if min(image.size) < short_side:
                raise ValueError("region normalization would upsample")
            retained_area = image.width * image.height / (width * height)
            factor = short_side / min(image.size)
            target = tuple(half_up(v * factor) for v in image.size)
            rgb = np.asarray(image.resize(target, Image.Resampling.LANCZOS), dtype=float) / 255
    return rgb, dict(
        original_width=width,
        original_height=height,
        pixel_box=pixels,
        removed_area_fraction=1 - retained_area,
        normalized_width=target[0],
        normalized_height=target[1],
        short_side=short_side,
        color_profile="embedded_to_srgb" if profile else "missing_assumed_srgb",
        normalized_sha256=hashlib.sha256(rgb.astype("<f8").tobytes()).hexdigest(),
    )


def audit_records():
    records = [r for path in AUDITS for r in s.read(path)["records"]]
    source = {r["image_id"]: r for r in source_records()}
    if len(records) != 870 or len({v["image_id"] for v in records}) != 870:
        raise ValueError("audit must cover exactly 870 distinct works")
    if {v["image_id"] for v in records} != set(source):
        raise ValueError("audit membership differs")
    for row in records:
        original = source[row["image_id"]]
        if any(row[k] != original[k] for k in ("painter_id", "role", "raw_sha256")):
            raise ValueError("audit source identity differs")
        if not row["inspected"]:
            raise ValueError("audit has an uninspected work")
        validate_box(row["region_box"])
        if row["region_box"] != FULL and not row["region_note"]:
            raise ValueError("crop requires a reason")
        if row["visual_class"] not in (*CLASSES, "mixed_or_unclear", None):
            raise ValueError("invalid visual class")
        if row["role"] == "reference" and row["visual_class"] is None:
            raise ValueError("reference content must be assessed")
    return sorted(records, key=lambda v: (v["painter_id"], v["role"], v["image_id"]))


def write_new(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def measurement_bindings():
    return bindings(
        [
            PLAN,
            Path(__file__),
            *AUDITS,
            s.REF,
            DEVELOPMENT,
            s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/features.py",
            s.ROOT / "tests/painter_reference_quality_v1/test_regions.py",
        ]
    )


def measure():
    target = OUT / "measurements.json"
    if target.exists():
        raise FileExistsError("measurement record exists; do not overwrite")
    original = {v["image_id"]: v for v in source_records()}
    rows = []
    for record in audit_records():
        path = s.ROOT / record["raw_path"]
        if s.sha(path) != record["raw_sha256"]:
            raise ValueError("retained source bytes differ")
        if record["region_box"] == FULL:
            values = original[record["image_id"]]["values"]
            metadata = dict(removed_area_fraction=0.0, reused_original=True)
        else:
            rgb, metadata = normalize_region(path, record["region_box"])
            values = extract(rgb).tolist()
            metadata["reused_original"] = False
        rows.append(dict(image_id=record["image_id"], values=values, normalization=metadata))
        if len(rows) % 50 == 0:
            print(f"Verified/measured {len(rows)}/870 source works", flush=True)
    write_new(target, dict(inputs=measurement_bindings(), records=rows))


def bindings(paths):
    return [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths]


def summarize(x, raw_refs, scaler, original_refs):
    refs = [transform(v, scaler) for v in raw_refs]
    r = centered(np.array([v.mean(axis=0) for v in refs]))
    baseline = centered(np.array([transform(v, scaler).mean(axis=0) for v in original_refs]))
    h = float(np.square(r).sum())
    rows, errors = [], []
    for title, values in zip(s.TITLES, x):
        d = centered(values[:, :, 2:])
        cal = calibration(d, r)
        beta, _, error = metrics(d, r)
        errors.append(error)
        pairs = []
        for a, b in itertools.combinations(range(4), 2):
            pair_b, _, pair_e = metrics(
                (values[:, :, a + 2] - values[:, :, b + 2])[:, :, None],
                (r[a] - r[b])[None],
            )
            pairs.append(
                dict(
                    artists=[s.ARTISTS[a], s.ARTISTS[b]],
                    beta=float(pair_b.mean()),
                    d=float(pair_e.mean()),
                )
            )
        rows.append(
            dict(
                model=title,
                **cal,
                beta_interval=interval(beta),
                d_interval=interval(error),
                artist_pairs=pairs,
            )
        )
    return dict(
        reference_h=h,
        target_cosine_same_scaler=float(
            np.sum(r * baseline) / np.sqrt(h * np.square(baseline).sum())
        ),
        target_displacement_over_original_h=float(
            np.square(r - baseline).sum() / np.square(baseline).sum()
        ),
        models=rows,
        comparisons=[
            dict(model_a=s.TITLES[a], model_b=s.TITLES[b], **interval(errors[a] - errors[b]))
            for a, b in itertools.combinations(range(6), 2)
        ],
    )


def conditional(x, refs, labels):
    keep = [i for i, (c, _) in enumerate(s.SCENES) if c in CLASS_MAP]
    classes = [CLASS_MAP[s.SCENES[i][0]] for i in keep]
    counts = [{c: int(np.sum(np.array(lab) == c)) for c in CLASSES} for lab in labels]
    target = centered(
        np.array(
            [[v[np.array(lab) == c].mean(axis=0) for v, lab in zip(refs, labels)] for c in classes]
        )
    )
    if not np.isfinite(target).all():
        raise ValueError("revised class has no reference support")
    return dict(
        counts=counts,
        scenes=keep,
        reference_h=float(np.square(target).sum(axis=(1, 2)).mean()),
        models=[
            dict(model=name, beta=float(b.mean()), d=float(e.mean()))
            for name, (b, _, e) in zip(
                s.TITLES, [metrics(centered(v[keep, :, 2:]), target) for v in x]
            )
        ],
    )


def compute():
    x, _ = load()
    old_scaler = s.read(s.SCALER)
    records = source_records()
    audit = {v["image_id"]: v for v in audit_records()}
    measurement = s.read(OUT / "measurements.json")
    if measurement["inputs"] != measurement_bindings():
        raise ValueError("region measurement inputs changed")
    measured = {v["image_id"]: v for v in measurement["records"]}
    if len(measured) != 870 or set(measured) != set(audit):
        raise ValueError("region measurement membership differs")
    original_refs, corrected_refs, corrected_dev = [], [], {}
    frame = {v["work_id"]: v for v in s.rows(FRAME)}
    old_labels, new_labels = [], []
    for artist in s.ARTISTS:
        rr = [v for v in records if v["painter_id"] == artist and v["role"] == "reference"]
        dd = [v for v in records if v["painter_id"] == artist and v["role"] == "development"]
        original_refs.append(np.array([v["values"] for v in rr]))
        corrected_refs.append(np.array([measured[v["image_id"]]["values"] for v in rr]))
        corrected_dev[artist] = np.array([measured[v["image_id"]]["values"] for v in dd])
        old_labels.append([frame[v["image_id"]]["content_class"] for v in rr])
        new_labels.append(
            [
                audit[v["image_id"]]["visual_class"]
                if audit[v["image_id"]]["visual_class"] in CLASSES
                else frame[v["image_id"]]["content_class"]
                for v in rr
            ]
        )
    new_scaler = fit_scaler(corrected_dev)
    # Affine change of coordinates only; the generated measurements are unchanged.
    raw_x = x * np.asarray(old_scaler["scale"]) + np.asarray(old_scaler["center"])
    new_x = transform(raw_x, new_scaler)
    views = {
        "original": summarize(x, original_refs, old_scaler, original_refs),
        "regions_original_scaler": summarize(x, corrected_refs, old_scaler, original_refs),
        "regions_refitted_scaler": summarize(new_x, corrected_refs, new_scaler, original_refs),
    }
    prevalence = []
    for artist in s.ARTISTS:
        for role in ("reference", "development"):
            group = [v for v in audit.values() if v["painter_id"] == artist and v["role"] == role]
            removed = [
                measured[v["image_id"]]["normalization"]["removed_area_fraction"]
                for v in group
                if v["region_box"] != FULL
            ]
            changed = [
                v
                for v in group
                if role == "reference"
                and v["visual_class"] in CLASSES
                and v["visual_class"] != frame[v["image_id"]]["content_class"]
            ]
            prevalence.append(
                dict(
                    painter=artist,
                    role=role,
                    n=len(group),
                    flagged=sum(bool(v["flags"]) for v in group),
                    flag_counts=dict(Counter(flag for v in group for flag in v["flags"])),
                    cropped=len(removed),
                    crop_area_range=[min(removed), max(removed)] if removed else [],
                    class_changes=len(changed),
                    unclear_content=sum(v["visual_class"] == "mixed_or_unclear" for v in group),
                )
            )
    conditional_views = {}
    for name, xx, raw, scaler, labels in (
        ("original_title", x, original_refs, old_scaler, old_labels),
        ("original_visual", x, original_refs, old_scaler, new_labels),
        ("regions_title", x, corrected_refs, old_scaler, old_labels),
        ("regions_refit_title", new_x, corrected_refs, new_scaler, old_labels),
        ("regions_refit_visual", new_x, corrected_refs, new_scaler, new_labels),
    ):
        conditional_views[name] = conditional(xx, [transform(v, scaler) for v in raw], labels)
    return dict(
        interpretation="Retrospective assistant visual audit and descriptive sensitivity; "
        "original primary family unchanged; no artistic-fidelity validation.",
        prevalence=prevalence,
        views=views,
        conditional=conditional_views,
        corrected_scaler=new_scaler,
        scale_ratios=(np.array(new_scaler["scale"]) / old_scaler["scale"]).tolist(),
    )


def analysis_bindings():
    return bindings(
        [
            PLAN,
            Path(__file__),
            *AUDITS,
            OUT / "measurements.json",
            s.REF,
            DEVELOPMENT,
            s.SCALER,
            FRAME,
            s.DATA / "measurements.jsonl",
            s.DATA / "measurement_receipt.json",
            s.DATA / "requests.jsonl",
            s.DATA / "analysis.json",
            s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/features.py",
            s.ROOT / "src/latent_art_bench/painter_feature_generation_v2/statistics.py",
            s.ROOT / "src/latent_art_bench/painter_specificity_review_v1.py",
            s.ROOT / "src/latent_art_bench/painter_specificity_v1/analysis.py",
        ]
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("measure", "run", "check", "check-images"))
    args = parser.parse_args()
    if args.action == "measure":
        measure()
        return
    if args.action == "check-images":
        record = s.read(OUT / "measurements.json")
        if record["inputs"] != measurement_bindings():
            raise ValueError("region measurement inputs changed")
        measured = {v["image_id"]: v for v in record["records"]}
        if len(record["records"]) != 870 or set(measured) != {
            v["image_id"] for v in source_records()
        }:
            raise ValueError("region measurement membership differs")
        for row in audit_records():
            if s.sha(s.ROOT / row["raw_path"]) != row["raw_sha256"]:
                raise ValueError("source bytes differ")
            if row["region_box"] != FULL:
                rgb, metadata = normalize_region(s.ROOT / row["raw_path"], row["region_box"])
                expected = measured[row["image_id"]]
                if metadata["normalized_sha256"] != expected["normalization"]["normalized_sha256"]:
                    raise ValueError("normalized region differs")
                if extract(rgb).tolist() != expected["values"]:
                    raise ValueError("region features differ")
        print("Reference-quality image hashes and cropped features verified")
        return
    result = dict(inputs=analysis_bindings(), **compute())
    path = OUT / "analysis.json"
    if args.action == "run":
        write_new(path, result)
    elif s.read(path) != result:
        raise ValueError("reference-quality numerical replay differs")
    print("Reference-quality numerical result verified")


if __name__ == "__main__":
    main()
