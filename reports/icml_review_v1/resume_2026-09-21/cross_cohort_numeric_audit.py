#!/usr/bin/env python3
"""Separate arithmetic replay of frozen retrospective SD-Turbo evidence.

No production analysis code is imported. Each U uses the actual products for
every ordered pair of distinct blocks. Inputs remain read-only. --write creates
the audit JSON/Markdown once; ordinary replay only prints the audit summary.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import hmac
import itertools
import json
import math
from pathlib import Path
import platform

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).with_suffix("")
INPUTS = "reports/painter_cross_cohort_v1/inputs.json"
ANALYSIS = "reports/painter_cross_cohort_v1/analysis.json"
EXPECTED_INPUTS = "94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693"
EXPECTED_ANALYSIS = "9488dfafa5779b8b065cc756804e67ad64c2841a5c62c2f9b0105f8fef13973e"
RUN = "data/manifests/painter_feature_generation_v2/pfg2-sd-turbo-20260905"
METHOD = "data/manifests/painter_feature_generation_v2/pfg2-method-20260905"
FEATURES = f"{METHOD}/experiments/pfg2-sd-turbo-20260905/generated_features.jsonl"
ARTISTS = ["claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne"]
ARMS = ["artist_free", *ARTISTS]
SCENES = [f"{group}{i}" for group in "WBRL" for i in range(1, 5)]
FAMILIES = {
    "color": ["lightness_median", "lightness_iqr", "chroma_median", "chroma_iqr",
              "chromatic_fraction", "hue_concentration", "hue_entropy", "deltae_01",
              "deltae_04", "deltae_16", "deltae_slope"],
    "spatial": ["spectral_slope", "spectral_residual", "spectral_anisotropy",
                "orientation_entropy", "horizontal_vertical_balance", "gradient_median",
                "gradient_iqr", "quadrant_jsd"],
    "texture": ["wavelet_energy_1", "wavelet_energy_2", "wavelet_energy_3",
                "wavelet_energy_4", "wavelet_slope", "wavelet_curvature", "lbp_entropy_8",
                "lbp_entropy_16", "lbp_entropy_32", "local_cv_01", "local_cv_04", "local_cv_16"],
}
NAMES = sum(FAMILIES.values(), [])
VIEWS = {"all31": list(range(31)), **{
    name: [NAMES.index(feature) for feature in features]
    for name, features in FAMILIES.items()
}}
ATOL, RTOL = 1e-10, 1e-11


def unique_object(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(text):
    def reject(value):
        raise ValueError(f"nonfinite JSON number: {value}")
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject)


def read(path):
    return decode((ROOT / path).read_text())


def rows(path):
    return [decode(line) for line in (ROOT / path).read_text().splitlines()]


def sha(path):
    with (ROOT / path).open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def verify_record(record):
    path = record["path"]
    require(not Path(path).is_absolute() and (ROOT / path).resolve().is_relative_to(ROOT),
            "unsafe binding path")
    actual = sha(path)
    require(actual == record["sha256"], f"hash mismatch: {path}")
    return {"path": path, "sha256": actual}


def unique_by(items, key):
    result = {row[key]: row for row in items}
    require(len(result) == len(items), f"duplicate {key}")
    return result


def ordered_u(vectors):
    """Direct pair multiplication: no centered or squared-sum U identity."""
    vectors = np.asarray(vectors, dtype=np.float64)
    k = len(vectors)
    require(k >= 2 and np.isfinite(vectors).all(), "invalid ordered-product input")
    left, right = np.where(~np.eye(k, dtype=bool))
    require(len(left) == k * (k - 1), "ordered-pair census")
    products = (vectors[left] * vectors[right]).sum(axis=-1)
    return products.sum(axis=0) / (k * (k - 1))


def response_records(delta, reference):
    """One or many scene records; painter axis is next-to-last."""
    common = delta.mean(axis=-2)
    centered = delta - common[..., None, :]
    c = 4 * ordered_u(common)
    l = ordered_u(centered).sum(axis=-1)
    n = ordered_u(delta).sum(axis=-1)
    h = float(np.square(reference).sum())
    beta = (centered.mean(axis=0) * reference).sum(axis=(-2, -1)) / h if h > 0 else None
    d = ordered_u(centered - reference).sum(axis=-1) / h if h > 0 else None
    count = 1 if np.ndim(c) == 0 else len(c)
    def scalar(value, i):
        return None if value is None else float(value if np.ndim(value) == 0 else value[i])
    result = []
    for i in range(count):
        cc, ll, nn, bb, dd = [scalar(v, i) for v in (c, l, n, beta, d)]
        result.append({
            "C": cc, "L": ll, "N": nn, "T": cc - ll, "H": h,
            "beta": bb, "D": dd,
            "common_fraction": cc / nn if nn > 0 else None,
            "common_fraction_reason": None if nn > 0 else "nonpositive_total_naming_change",
            "common_majority_descriptive": bool(nn > 0 and cc - ll > 0),
            "alignment_reason": None if h > 0 else "zero_reference_energy",
            "decomposition_residual": nn - cc - ll,
            "D_identity_residual": None if h <= 0 else dd - (ll / h - 2 * bb + 1),
        })
    return result


def family_summary(generated, means):
    reference = means - means.mean(axis=0)
    delta = generated[:, :, 1:, :] - generated[:, :, 0, None, :]
    pooled = response_records(delta.mean(axis=1), reference)[0]
    scenes = response_records(delta, reference)
    within = {key: (None if scenes[0][key] is None else
                    math.fsum(row[key] for row in scenes) / len(scenes))
              for key in ("C", "L", "N", "T", "beta", "D",
                          "decomposition_residual", "D_identity_residual")}
    within.update({
        "H": pooled["H"], "alignment_reason": pooled["alignment_reason"],
        "common_fraction": within["C"] / within["N"] if within["N"] > 0 else None,
        "common_fraction_reason": None if within["N"] > 0 else "nonpositive_total_naming_change",
        "common_majority_descriptive": bool(within["N"] > 0 and within["T"] > 0),
    })
    pairs = []
    for a, j in itertools.combinations(range(4), 2):
        q = means[a] - means[j]
        denominator = float(np.dot(q, q))
        generated_difference = generated[:, :, a + 1] - generated[:, :, j + 1]
        pairs.append({
            "painters": [ARTISTS[a], ARTISTS[j]],
            "reference_squared_distance": denominator,
            "aligned_amplitude": float(np.dot(generated_difference.mean(axis=(0, 1)), q)
                                       / denominator) if denominator > 0 else None,
            "scene_D": float(ordered_u(generated_difference - q).mean() / denominator)
                       if denominator > 0 else None,
            "reason": None if denominator > 0 else "zero_reference_pair_distance",
        })
    return {"pooled": pooled, "within_scene": within,
            "scene_minus_pooled_D": None if pooled["D"] is None else within["D"] - pooled["D"],
            "scene_records": [dict(scene_index=i, **row) for i, row in enumerate(scenes)],
            "pairs": pairs}


def compare(actual, expected):
    numeric = []
    mismatch = []
    categorical = [0]
    def visit(a, e, path):
        if isinstance(e, dict):
            if not isinstance(a, dict) or set(a) != set(e):
                mismatch.append({"path": path, "reason": "dictionary keys"})
                return
            for key in e:
                visit(a[key], e[key], f"{path}.{key}")
        elif isinstance(e, list):
            if not isinstance(a, list) or len(a) != len(e):
                mismatch.append({"path": path, "reason": "list length"})
                return
            for i, (av, ev) in enumerate(zip(a, e)):
                visit(av, ev, f"{path}[{i}]")
        elif isinstance(e, (int, float)) and not isinstance(e, bool):
            if not isinstance(a, (int, float)) or isinstance(a, bool) or not math.isfinite(a):
                mismatch.append({"path": path, "reason": "numeric type"})
                return
            error = abs(a - e)
            numeric.append({"path": path, "absolute_error": error,
                            "scaled_error": error / max(1.0, abs(a), abs(e))})
            if not math.isclose(a, e, abs_tol=ATOL, rel_tol=RTOL):
                mismatch.append({"path": path, "actual": a, "expected": e})
        else:
            categorical[0] += 1
            if a != e or type(a) is not type(e):
                mismatch.append({"path": path, "actual": a, "expected": e})
    visit(actual, expected, "result")
    return {"numeric_leaves_compared": len(numeric),
            "categorical_or_null_leaves_compared": categorical[0],
            "absolute_tolerance": ATOL, "relative_tolerance": RTOL,
            "maximum_absolute_error": max(numeric, key=lambda row: row["absolute_error"]),
            "maximum_scaled_error": max(numeric, key=lambda row: row["scaled_error"]),
            "mismatches": mismatch}


def run():
    require(sha(INPUTS) == EXPECTED_INPUTS, "external frozen input anchor changed")
    require(sha(ANALYSIS) == EXPECTED_ANALYSIS, "external frozen analysis anchor changed")
    frozen, expected = read(INPUTS), read(ANALYSIS)
    require(expected["inputs_sha256"] == EXPECTED_INPUTS, "result-to-input binding")
    require(len({row["path"] for row in frozen["bindings"]}) == len(frozen["bindings"]),
            "duplicate frozen binding")
    with ThreadPoolExecutor(max_workers=8) as pool:
        bindings = list(pool.map(verify_record, frozen["bindings"]))
    requests, outputs, features = [rows(path) for path in
                                  (f"{RUN}/requests.jsonl", f"{RUN}/outputs.jsonl", FEATURES)]
    reqs = unique_by(requests, "request_id")
    outs = unique_by(outputs, "request_id")
    feats = unique_by(features, "image_id")
    cells = {(b, s, a) for b in range(25) for s in SCENES for a in ARMS}
    require(len(reqs) == 2000 and set(reqs) == set(outs) == set(feats), "complete joined census")
    require({(r["block"], r["template_id"], r["condition"]) for r in requests} == cells,
            "complete 25 by 16 by 5 cell census")
    method = read(f"{METHOD}/method_freeze.json")
    require(method["feature_names"] == NAMES == expected["feature_names"], "31-feature order")
    require(method["short_side"] == 512, "historical normalization size")
    config = read(f"{RUN}/generation_freeze.json")["config"]
    require(config == frozen["provenance"]["generation_config"], "generation config binding")
    for key, value in {"model_id": "stabilityai/sd-turbo",
                       "revision": "b261bac6fd2cf515557d5d0707481eafa0485ec2",
                       "device": "mps", "dtype": "float16", "height": 512, "width": 512,
                       "num_inference_steps": 1, "guidance_scale": 0.0,
                       "negative_prompt": None, "repetitions": 25}.items():
        require(config[key] == value, f"generation contract {key}")
    library = read("data/manifests/painter_feature_generation_v1/prompt_library.json")
    templates = unique_by(library["templates"], "template_id")
    painter_names = {r["painter_id"]: r["painter_name"] for r in library["painters"]}
    scaler = read(f"{METHOD}/scaler.json")
    center, scale = [np.asarray(scaler[key], dtype=np.float64) for key in ("center", "scale")]
    require(center.shape == scale.shape == (31,) and np.isfinite(center).all()
            and np.isfinite(scale).all() and (scale > 0).all(), "fixed finite scaler")
    require(scaler["development_counts"] == dict(zip(ARTISTS, (101, 36, 48, 36)))
            and scaler["quantile_rule"] == "equal_painter_weighted_empirical_inverse_cdf"
            and not any(scaler["invalid_coordinates"].values()), "221-work scaler contract")
    require(scaler["method_freeze_sha256"] == sha(f"{METHOD}/method_freeze.json")
            and scaler["development_feature_sha256"] ==
            read(f"{METHOD}/development_receipt.json")["feature_file_sha256"], "scaler receipts")
    raw = np.full((25, 16, 5, 31), np.nan)
    seeds = {}
    for i, req in enumerate(requests):
        identity = req["request_id"]
        b, s, a = req["block"], req["template_id"], req["condition"]
        require(type(b) is int and identity == f"b{b:03d}-{s}-{a}", "request ID")
        out, feature = outs[identity], feats[identity]
        require(out["status"] == "generated" and feature["status"] == "measured", "admission")
        for record in (out, feature):
            require(all(record[key] == req[key] and type(record[key]) is type(req[key])
                        for key in ("block", "template_id", "condition")), "cell join identity")
        require(out["sha256"] == feature["raw_sha256"], "feature to image source")
        require(out["width"] == out["height"] == 512 and out["image_path"] ==
                f"research_workspace/painter_feature_generation_v2/pfg2-sd-turbo-20260905/generated/{identity}.png",
                "generated image path and dimensions")
        require(all(feature["normalization"][key] == value for key, value in {
            "short_side": 512, "crop_fraction": 0.0, "original_width": 512,
            "original_height": 512, "normalized_width": 512, "normalized_height": 512,
            "color_profile": "missing_assumed_srgb"}.items()), "full-frame feature normalization")
        values = np.asarray(feature["values"], dtype=np.float64)
        require(values.shape == (31,) and np.isfinite(values).all(), "raw generated vector")
        raw[b, SCENES.index(s), ARMS.index(a)] = values
        baseline = templates[s]["artist_free_prompt"]
        prompt = baseline if a == "artist_free" else baseline.replace(
            "An oil painting on canvas", "An oil painting on canvas by " + painter_names[a], 1)
        require(req["prompt"] == prompt and req["sequence"] == i, "exact name insertion/order")
        seed = int.from_bytes(hmac.new(bytes.fromhex(config["master_seed"]),
            f"pfg-v2/1.0-seed|{s}|{b}".encode(), hashlib.sha256).digest()[:8], "big") >> 1
        require(req["seed"] == seed, "HMAC scene/block seed")
        seeds[b, s] = seed
    require(len(seeds) == len(set(seeds.values())) == 400, "400 distinct paired seeds")
    require(np.isfinite(raw).all(), "no unfilled generated cells")
    reference_rows = rows(f"{METHOD}/confirmation_features.jsonl")
    require(Counter(row["status"] for row in reference_rows) == {"measured": 649, "failed": 4},
            "historical admission count")
    references = [row for row in reference_rows if row["status"] == "measured"]
    require(Counter(row["painter_id"] for row in references) ==
            dict(zip(ARTISTS, (297, 106, 141, 105))), "historical painter count")
    learned = read("reports/painter_learned_audit_v1/inputs.json")["rows"]
    primary = [row for row in learned if row["view"] == "original" and row["role"] == "reference"]
    main = [row for row in learned if row["view"] == "original" and row["role"] == "generated"]
    require(len(primary) == 649 and len(main) == 1008, "main target/image counts")
    require({(r["image_id"], r["painter_id"], r["raw_sha256"]) for r in references} ==
            {(r["id"], r["painter"], r["sha256"]) for r in primary}, "exact historical membership")
    require(len({row["image_id"] for row in references}) == 649, "unique historical identity")
    for row in references:
        require(row["normalization"]["short_side"] == 512 and
                row["normalization"]["crop_fraction"] == 0.0 and
                np.asarray(row["values"]).shape == (31,) and
                np.isfinite(row["values"]).all(), "historical normalization and values")
    pixels = [{"path": row["image_path"], "sha256": row["sha256"]} for row in outputs]
    require({(r["id"], r["path"], r["sha256"]) for r in frozen["provenance"]["original_pixels"]} ==
            {(r["request_id"], r["image_path"], r["sha256"]) for r in outputs}, "frozen pixel roster")
    require(frozen["provenance"]["references"] == primary, "frozen historical roster")
    with ThreadPoolExecutor(max_workers=8) as pool:
        image_checks = list(pool.map(verify_record, pixels + primary + main))
    overlap = {row["sha256"] for row in pixels} & {row["sha256"] for row in main}
    require(not overlap, "main/SD-Turbo original image overlap")
    z = (raw - center) / scale
    # Average raw historical coordinates first, using compensated scalar sums;
    # then apply the retained affine scaler. Nothing is fitted or resampled.
    means = np.asarray([[math.fsum(row["values"][i] for row in references
                                  if row["painter_id"] == artist) /
                         sum(row["painter_id"] == artist for row in references)
                         for i in range(31)] for artist in ARTISTS])
    means = (means - center) / scale
    def all_families(data):
        return {name: family_summary(data[..., indices], means[:, indices])
                for name, indices in VIEWS.items()}
    families = all_families(z)
    deletions = [{"block": b, "families": all_families(z[np.arange(25) != b])}
                 for b in range(25)]
    ranges = {}
    for family in VIEWS:
        ranges[family] = {}
        for view in ("pooled", "within_scene"):
            ranges[family][view] = {}
            for key in ("C", "L", "N", "T", "common_fraction", "beta", "D"):
                values = [(r["block"], r["families"][family][view][key]) for r in deletions]
                finite = [v for _, v in values if v is not None and math.isfinite(v)]
                ranges[family][view][key] = {
                    "minimum": min(finite) if finite else None,
                    "maximum": max(finite) if finite else None, "available": len(finite),
                    "unavailable_blocks": [b for b, v in values if v is None or not math.isfinite(v)]}
    numerical = {"families": families, "leave_one_block_out": deletions, "sensitivity_ranges": ranges}
    comparison = compare(numerical, {key: expected[key] for key in numerical})
    all_records = [row for collection in [families, *(r["families"] for r in deletions)]
                   for summary in collection.values()
                   for row in [summary["pooled"], summary["within_scene"], *summary["scene_records"]]]
    identities = {key: max(abs(row[key]) for row in all_records if row[key] is not None)
                  for key in ("decomposition_residual", "D_identity_residual")}
    require(all(value < ATOL for value in identities.values()), "independent identity residual")
    require(not comparison["mismatches"], "retained numerical replay mismatch")
    require(expected["arms"] == ARMS and expected["blocks"] == 25 and expected["scenes"] == 16,
            "retained analysis dimensions")
    result = {
        "status": "passed", "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Separate computational replay of retrospective, previously analyzed images and shared historical references; not independent scientific validation.",
        "method": "Raw retained feature rows; fixed development scaler; compensated historical means; direct products over all ordered distinct-block pairs. No production analysis imports.",
        "inference": "Descriptive only; deletion ranges are sensitivities, not confidence intervals; no p-values.",
        "script_sha256": sha(Path(__file__).relative_to(ROOT)),
        "inputs_sha256": EXPECTED_INPUTS, "analysis_sha256": EXPECTED_ANALYSIS,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "frozen_bindings_verified": bindings,
        "provenance_checks": {"generated_cells": 2000, "paired_seed_blocks": 25,
            "scenes": SCENES, "arms": ARMS, "unique_scene_block_seeds": len(seeds),
            "generated_original_file_hashes_verified": 2000,
            "historical_original_file_hashes_verified": 649,
            "main_original_file_hashes_verified": 1008,
            "all_original_file_hashes_verified": len(image_checks),
            "main_image_hash_overlap": len(overlap), "historical_counts": dict(Counter(
                row["painter_id"] for row in references)), "development_counts": scaler["development_counts"],
            "feature_names": NAMES, "coordinate_family_counts": {k: len(v) for k, v in VIEWS.items()},
            "exact_prompt_insertion": "An oil painting on canvas of ... -> An oil painting on canvas by [painter] of ...",
            "configuration": config, "prior_exposure": frozen["provenance"]["prior_exposure"],
            "pixel_hash_definition": "SHA-256 of original image file bytes; no feature re-extraction or image decoding performed."},
        "coverage": {"families": 4, "full_cohort_scenes_per_family": 16,
            "full_cohort_pairs_per_family": 6, "deletions": 25, "blocks_per_deletion": 24,
            "every_deletion_recomputes_all_scenes_and_pairs": True, "range_endpoints": 56},
        "comparison": comparison, "maximum_independent_identity_residuals": identities,
        "recomputed": numerical,
    }
    return result


def markdown(result):
    text = ["# Retrospective cross-cohort numerical audit", "", "Status: **passed**.", "",
        "This is a separate computational replay of retained, previously analyzed SD-Turbo images. "
        "It is not independent scientific validation or prospective replication. The same four painters "
        "and exposed historical target remain in use. No p-values or confidence intervals are calculated.", "",
        "## Verification", "",
        f"- Frozen input SHA-256: `{EXPECTED_INPUTS}`.",
        f"- Frozen analysis SHA-256: `{EXPECTED_ANALYSIS}`.",
        f"- All {len(result['frozen_bindings_verified'])} frozen source bindings match.",
        "- Original image file hashes match for 2,000 SD-Turbo outputs, 649 historical works, and 1,008 main-experiment images. Main/SD-Turbo hash overlap is zero.",
        "- Reconstructed the complete 25-block × 16-scene × 5-arm × 31-coordinate array from raw retained rows. Verified exact cells, names, normalization, painter membership, fixed 221-work scaler, prompt insertion, and 400 paired HMAC seeds.",
        "- Recomputed all four families, pooled and within-scene summaries, all 16 scene records, six painter pairs per family, all 25 block deletions (K=24), and all 56 sensitivity ranges. Pair records and scene records were also recomputed within every deletion.",
        "- Each cross-block statistic directly multiplies every ordered distinct-block pair. The production analysis module is not imported. Historical raw means use compensated scalar sums before fixed standardization.",
        f"- Compared {result['comparison']['numeric_leaves_compared']:,} numeric leaves and {result['comparison']['categorical_or_null_leaves_compared']:,} categorical/null leaves; no mismatches. Maximum absolute numeric difference: {result['comparison']['maximum_absolute_error']['absolute_error']:.3g}; tolerance: abs={ATOL:g}, rel={RTOL:g}.",
        "", "## Full-cohort results", "",
        "| Family | Pooled C/N | Pooled T | Scene C/N | Scene T | beta | Pooled D | Scene D |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, values in result["recomputed"]["families"].items():
        p, s = values["pooled"], values["within_scene"]
        text.append(f"| {name} | {p['common_fraction']:.9f} | {p['T']:.9f} | {s['common_fraction']:.9f} | {s['T']:.9f} | {p['beta']:.9f} | {p['D']:.9f} | {s['D']:.9f} |")
    text.extend(["", "The all-coordinate descriptive common-majority condition (N > 0 and T > 0) holds, "
        "as do color and spatial sensitivities. **Texture fails that condition in both pooled and within-scene summaries**, "
        "and its T stays negative in all 25 deletions. All denominators are positive in these retained results. "
        "Positive alignment and smaller error do not establish artistic fidelity; a common response is not thereby unwanted or non-stylistic.",
        "", "The generic control already requests oil painting. The exact named prompt inserts ` by [painter]` "
        "after `An oil painting on canvas`. All five arms share each scene/block seed. SD-Turbo revision "
        "`b261bac6fd2cf515557d5d0707481eafa0485ec2` uses fp16/MPS, 512×512, one denoising step, guidance zero, "
        "and null negative prompt. Prior energy-distance, coordinate, qualification, and copy diagnostics exposed the cohort. "
        "Stable independent block errors remain an assumption; this replay does not establish them or validate closed-service independence.",
        "", "The companion JSON retains every recomputed numeric record, comparison counts, maximum identity residuals, source bindings, and provenance checks. "
        "Original-image SHA-256 checks hash file bytes; this audit does not re-extract features or decode images.",
        "", "## Replay", "", "Run from the repository root (ordinary replay is read-only):", "", "```sh",
        ".venv/bin/python reports/icml_review_v1/resume_2026-09-21/cross_cohort_numeric_audit.py", "```", "",
        "The original invocation used `--write` to create this JSON/Markdown pair once; existing audit artifacts are never overwritten.", ""])
    return "\n".join(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        require(not BASE.with_suffix(".json").exists() and not BASE.with_suffix(".md").exists(),
                "create-once audit output already exists")
    report = run()
    if args.write:
        with BASE.with_suffix(".json").open("x") as file:
            json.dump(report, file, indent=2, sort_keys=True, allow_nan=False)
            file.write("\n")
        with BASE.with_suffix(".md").open("x") as file:
            file.write(markdown(report))
    print(json.dumps({key: report[key] for key in ("status", "coverage", "comparison",
          "maximum_independent_identity_residuals")}, indent=2))
