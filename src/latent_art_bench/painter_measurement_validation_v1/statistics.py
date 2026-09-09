"""Paired work-level calibration summaries and unchanged Study 1 inference."""

from __future__ import annotations

import numpy as np

from latent_art_bench.painter_distribution_study_v1 import analysis as original
from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_prompt_study_v1.randomization import holm

from .transforms import CONDITIONS

PAINTERS = ("claude_monet", "paul_cezanne")
SIGNALS = {"color": "chroma80", "spatial": "tiles4", "texture": "blur1"}
BOOTSTRAP_SEED = 2026091002
BOOTSTRAP_DRAWS = 9999
INTERVAL_LEVEL = 1 - .05 / 3


def displacement(before, after, scaler):
    delta = transform(np.asarray(after), scaler) - transform(np.asarray(before), scaler)
    return {family: float(np.sqrt(np.mean(delta[section] ** 2)))
            for family, section in FAMILIES.items()}


def work_bootstrap(values, painters, *, draws=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED):
    """Reuse each sampled work index across all three paired responses."""
    x = np.asarray(values, dtype=float)
    labels = np.asarray(painters)
    if x.ndim != 2 or x.shape != (len(labels), 3) or not np.isfinite(x).all():
        raise ValueError("expected one finite three-response row per work")
    if set(labels) != set(PAINTERS):
        raise ValueError("both fixed painters required")
    rng = np.random.default_rng(seed)
    samples = np.zeros((draws, 3))
    estimate = np.zeros(3)
    for painter in PAINTERS:
        subset = x[labels == painter]
        indices = rng.integers(0, len(subset), size=(draws, len(subset)))
        samples += .5 * subset[indices].mean(axis=1)
        estimate += .5 * subset.mean(axis=0)
    alpha = .05 / 6
    intervals = np.quantile(samples, [alpha, 1 - alpha], axis=0)
    return estimate, intervals, samples


def summarize_challenge(rows, scaler):
    lookup = {}
    for row in rows:
        key = row["image_id"], row["condition"]
        if key in lookup or row["condition"] not in CONDITIONS:
            raise ValueError("duplicate or unexpected challenge record")
        lookup[key] = row
    ids = sorted({key[0] for key in lookup})
    if not ids or len(lookup) != len(ids) * len(CONDITIONS):
        raise ValueError("incomplete challenge grid")
    by_work, matrix_rows, principal = [], [], []
    for image_id in ids:
        baseline = lookup[image_id, "baseline"]
        values = {}
        for name in CONDITIONS:
            row = lookup[image_id, name]
            if row["painter_id"] != baseline["painter_id"]:
                raise ValueError("challenge painter identity changed")
            values[name] = displacement(baseline["values"], row["values"], scaler)
        differences = {}
        for family, signal in SIGNALS.items():
            processing = max(values["jpeg95"][family], values["resample384"][family])
            differences[family] = values[signal][family] - processing
        principal.append([differences[family] for family in FAMILIES])
        chroma = baseline["values"][2]
        signed_chroma = {name: dict(
            signed_change=lookup[image_id, name]["values"][2] - chroma,
            realized_ratio=lookup[image_id, name]["values"][2] / chroma if chroma else None,
            requested_ratio=factor,
            clipped_pixel_fraction=lookup[image_id, name]["transform"].get(
                "clipped_pixel_fraction", 0),
        ) for name, factor in (("chroma80", .8), ("chroma60", .6))}
        by_work.append(dict(image_id=image_id, painter_id=baseline["painter_id"],
                            displacement=values, signal_minus_processing=differences,
                            signed_chroma_response=signed_chroma))
    labels = [row["painter_id"] for row in by_work]
    estimate, intervals, samples = work_bootstrap(principal, labels)
    comparisons = []
    for index, family in enumerate(FAMILIES):
        constant = bool(np.ptp(samples[:, index]) == 0)
        comparisons.append(dict(
            family=family, signal=SIGNALS[family], processing="paired max(jpeg95,resample384)",
            estimate=float(estimate[index]),
            lower=None if constant else float(intervals[0, index]),
            upper=None if constant else float(intervals[1, index]),
            interval_level=INTERVAL_LEVEL, zero_bootstrap_variance=constant,
            painter_means={p: float(np.mean([r["signal_minus_processing"][family]
                                           for r in by_work if r["painter_id"] == p]))
                           for p in PAINTERS},
        ))
    for family in FAMILIES:
        for name in CONDITIONS:
            for painter in (*PAINTERS, "equal_painter"):
                subsets = {p: [r["displacement"][name][family] for r in by_work
                               if r["painter_id"] == p] for p in PAINTERS}
                if painter == "equal_painter":
                    mean = np.mean([np.mean(v) for v in subsets.values()])
                    # Explicitly an average of painter medians, not a pooled quantile.
                    median = np.mean([np.median(v) for v in subsets.values()])
                    count = len(by_work)
                else:
                    mean, median, count = (np.mean(subsets[painter]),
                                           np.median(subsets[painter]), len(subsets[painter]))
                matrix_rows.append(dict(family=family, condition=name, painter_id=painter,
                                        works=count, mean=float(mean),
                                        painter_median_summary=float(median)))
    doses = []
    for family, low, high in (("color", "chroma80", "chroma60"),
                              ("texture", "blur1", "blur2")):
        for p in PAINTERS:
            differences = [r["displacement"][high][family] - r["displacement"][low][family]
                           for r in by_work if r["painter_id"] == p]
            doses.append(dict(family=family, painter_id=p, low=low, high=high,
                              mean_high_minus_low=float(np.mean(differences)),
                              fraction_increasing=float(np.mean(np.array(differences) > 0))))
    return dict(comparisons=comparisons, family_matrix=matrix_rows, dose_responses=doses,
                by_work=by_work, bootstrap_draws=BOOTSTRAP_DRAWS, bootstrap_seed=BOOTSTRAP_SEED,
                interpretation="Bonferroni-three descriptive percentile intervals, "
                "nominal 98.3333% "
                "each; conditional on exposed works, not calibrated population coverage.")


def endpoints(reference, generated, bundle):
    """Reuse the exact original eight pairing, weighting and randomization contracts."""
    result = []
    for old in bundle["old_analysis"]["endpoints"]:
        p = old["painter_id"]
        row = original.paired(
            [r for r in reference if r["painter_id"] == p], generated, bundle["targets"][p],
            old["route"], p, old["before"], old["after"], bundle["config"],
            old["endpoint_index"],
        )
        if row["pairs"] != old["pairs"] or row["excluded_pairs"] != old["excluded_pairs"]:
            raise ValueError("original missingness or pairing changed")
        result.append(row)
    if len(result) != 8:
        raise ValueError("expected eight original endpoints")
    for row, adjusted in zip(result, holm([r["raw_p"] for r in result])):
        row["holm_p"] = float(adjusted)
        row["reject_at_05"] = bool(adjusted <= .05 and row["status"] != "unavailable")
    return result


def verify_primary(bundle):
    reference = [r for r in bundle["reference"] if r["pipeline"] == "primary512"]
    generated = [r for r in bundle["generated"] if r["pipeline"] == "primary512"]
    result = endpoints(reference, generated, bundle)
    if result != bundle["old_analysis"]["endpoints"]:
        raise ValueError("unchanged primary inference does not replay exactly")
    return result


def geometry_analysis(rows, bundle):
    scaler = bundle["scalers"]["primary512"]["scaler"]
    lookup = {r["image_id"]: r for r in rows}
    if len(lookup) != len(rows):
        raise ValueError("duplicate geometry measurement")
    original_rows = [r for key in ("reference", "generated") for r in bundle[key]
                     if r["pipeline"] == "primary512"]
    if set(lookup) != {r["image_id"] for r in original_rows}:
        raise ValueError("complete original geometry inventory required")
    reference, generated, shifts = [], [], []
    for old in original_rows:
        new = lookup[old["image_id"]]
        updated = dict(old, values=new["values"],
                       scaled=transform(np.array(new["values"]), scaler).tolist())
        (reference if old["stage"] == "reference" else generated).append(updated)
        shifts.append(dict(image_id=old["image_id"], painter_id=old["painter_id"],
                           group=old.get("route", "reference"),
                           retained_area_fraction=new["window"]["retained_area_fraction"],
                           displacement=displacement(old["values"], new["values"], scaler)))
    square = endpoints(reference, generated, bundle)
    comparisons = [dict(endpoint_index=new["endpoint_index"], route=new["route"],
                        painter_id=new["painter_id"], before=new["before"], after=new["after"],
                        pairs=new["pairs"], full_view_estimate=old["estimate"],
                        square_estimate=new["estimate"],
                        estimate_change=new["estimate"] - old["estimate"],
                        full_view_holm_p=old["holm_p"], square_holm_p=new["holm_p"])
                   for old, new in zip(bundle["old_analysis"]["endpoints"], square)]
    groups = []
    for group, painter in sorted({(r["group"], r["painter_id"]) for r in shifts}):
        selected = [r for r in shifts if (r["group"], r["painter_id"]) == (group, painter)]
        area = [r["retained_area_fraction"] for r in selected]
        groups.append(dict(group=group, painter_id=painter, images=len(selected),
                           mean_retained_area_fraction=float(np.mean(area)),
                           min_retained_area_fraction=float(np.min(area)),
                           median_retained_area_fraction=float(np.median(area)),
                           max_retained_area_fraction=float(np.max(area)),
                           mean_displacement={f: float(np.mean([r["displacement"][f]
                                                               for r in selected]))
                                              for f in FAMILIES}))
    return dict(endpoints=square, comparisons=comparisons, by_image=shifts, groups=groups,
                interpretation="Post-result common central field-of-view sensitivity; "
                "unchanged conditional randomization machinery, not new confirmation or "
                "independent-capture validation. Cropping changes visible content.")
