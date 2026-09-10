"""Create or exactly replay the compact terminal report; no new scientific fits."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_specificity_reference_v1 import analysis as ref_analysis
from latent_art_bench.painter_specificity_v1.analysis import centered
from latent_art_bench.painter_specificity_v2 import study as s

from .workflow import DATA as READER_DATA
from .workflow import load


def number(value):
    return "NA" if value is None else f"{value:.6f}"


def ci(cell, simultaneous=False):
    if not cell or not cell["available"]:
        return "unavailable"
    pair = cell["simultaneous_ci" if simultaneous else "ci95"]
    return "[" + ", ".join(number(v) for v in pair) + "]"


def audit_raw():
    collection = s.read(s.DATA / "collection.json")
    events = s.rows(s.DATA / "attempts.jsonl")
    starts = {(r["id"], r["attempt"]): r for r in events if r["kind"] == "start"}
    ends = {(r["id"], r["attempt"]): r for r in events if r["kind"] == "end"}
    if len(starts) + len(ends) != len(events) or starts.keys() != ends.keys():
        raise ValueError("attempt identities are incomplete or duplicated")
    active = 0
    peak = 0
    timeline = []
    for r in starts.values():
        timeline.append((datetime.fromisoformat(r["started_at"]), 1))
    for r in ends.values():
        timeline.append((datetime.fromisoformat(r["ended_at"]), -1))
        if r["cost_usd"] is None:
            raise ValueError("unresolved cost")
        raw = gzip.decompress((s.ROOT / r["response_path"]).read_bytes())
        if hashlib.sha256(raw).hexdigest() != r["response_sha256"]:
            raise ValueError("raw response differs")
        if r["success"] and s.sha(s.ROOT / r["image_path"]) != r["image_sha256"]:
            raise ValueError("raw image differs")
    for _, delta in sorted(timeline):
        active += delta
        peak = max(peak, active)
    times = sorted(datetime.fromisoformat(r["started_at"]) for r in starts.values())
    spacing = min((b - a).total_seconds() for a, b in zip(times, times[1:]))
    accounted = s.accounted(events)
    if active != 0 or peak > 3 or spacing < 4.99 or accounted >= 120:
        raise ValueError("dispatch or cost contract differs")
    if abs(accounted - collection["accounted_usd"]) > 1e-10:
        raise ValueError("terminal accounting differs")
    requests = s.rows(s.DATA / "requests.jsonl")
    if len(requests) != 1008 or len({r["id"] for r in requests}) != 1008:
        raise ValueError("assignment census differs")
    outcomes = collection["outcomes"]
    if [r["id"] for r in outcomes] != [r["id"] for r in requests]:
        raise ValueError("outcome census/order differs")
    latest = {r["id"]: r for r in events if r["kind"] == "end"}
    if any(r != latest[r["id"]] for r in outcomes):
        raise ValueError("outcome is not the terminal attempt")
    measurement = {r["id"]: r for r in s.rows(s.DATA / "measurements.jsonl")}
    paired = {}
    for req in requests:
        row = measurement[req["id"]]
        if row["status"] == "measured":
            key = req["model"], req["scene"], req["arm"]
            paired.setdefault(key, []).append(row["normalization"]["normalized_sha256"])
    identical_pairs = sum(len(v) == 2 and v[0] == v[1] for v in paired.values())
    return dict(
        identical_normalized_repeat_pairs=identical_pairs,
        planned=1008,
        successful=sum(r["success"] for r in outcomes),
        attempts=len(starts),
        retries=len(starts) - 1008,
        peak_active=peak,
        minimum_start_spacing_seconds=spacing,
        baseline_usd=s.BASELINE,
        incremental_charges_usd=accounted - s.BASELINE,
        cumulative_accounted_usd=accounted,
        statuses=dict(Counter(str(r["status"]) for r in ends.values())),
        raw_response_hashes_verified=len(ends),
        raw_image_hashes_verified=sum(r["success"] for r in ends.values()),
    )


def csv_bytes(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def artist_diagnostics(named, references):
    """Prespecified repeat spread and additive contributions to the existing D."""
    named = np.asarray(named, dtype=float)
    r = centered(np.array([a.mean(axis=0) for a in references]))
    h = np.sum(r * r)
    complete = np.isfinite(named).all(axis=(1, 2, 3))
    contributions = [None] * 4
    if complete.any():
        error = centered(named[complete]) - r
        contributions = (np.sum(error[:, 0] * error[:, 1], axis=-1).mean(axis=0) / h).tolist()
    result = []
    for a, reference in enumerate(references):
        pairs = named[:, :, a]
        pairs = pairs[np.isfinite(pairs).all(axis=(1, 2))]
        within = (
            float(np.mean(np.sum((pairs[:, 0] - pairs[:, 1]) ** 2, axis=-1)) / 2)
            if len(pairs)
            else None
        )
        reference_trace = float(np.var(reference, axis=0, ddof=1).sum())
        result.append(
            dict(
                complete_repeat_scenes=len(pairs),
                within_scene_trace=within,
                within_reference_trace_ratio=(
                    within / reference_trace if within is not None else None
                ),
                geometry_complete_scenes=int(complete.sum()),
                geometry_error_contribution=contributions[a],
            )
        )
    return result


def build():
    x, refs = load()
    audit = audit_raw()
    primary = s.read(s.DATA / "analysis.json")
    square = s.read(s.DATA / "analysis_square.json")
    balanced = s.read(ref_analysis.DATA / "analysis.json")
    balanced_square = s.read(ref_analysis.DATA / "analysis_square.json")
    r = centered(np.array([a.mean(axis=0) for a in refs]))
    h = np.sum(r * r)
    shares = {k: float(np.sum(r[:, v] ** 2) / h) for k, v in FAMILIES.items()}
    models = []
    artists = []
    for m, item in enumerate(primary["models"]):
        models.append(
            dict(
                model=item["model"],
                scenes=item["beta"]["n"],
                beta=item["beta"]["mean"],
                beta_simultaneous_ci=ci(item["beta"], True),
                distortion=item["distortion"]["mean"],
                distortion_nominal_ci=ci(item["distortion"]),
                amplitude_error=item["amplitude_error"],
                off_axis_error=item["off_axis_error"],
                global_distortion=item["global_distortion"],
                shared_complete_scenes=item["shared"].get("n_scenes", 0),
                common_fraction=item["shared"].get("common_fraction"),
                generic_common_cosine=item["shared"].get("generic_common_cosine"),
                square_beta=square["models"][m]["beta"]["mean"],
                square_distortion=square["models"][m]["distortion"]["mean"],
                balanced_beta=balanced["models"][m]["beta"]["mean"],
                balanced_distortion=balanced["models"][m]["distortion"]["mean"],
                balanced_square_distortion=balanced_square["models"][m]["distortion"]["mean"],
            )
        )
        diagnostics = dict(zip(s.ARTISTS, artist_diagnostics(x[m, :, :, 2:], refs)))
        contributions = [a["geometry_error_contribution"] for a in diagnostics.values()]
        if all(v is not None for v in contributions) and not np.isclose(
            sum(contributions), item["distortion"]["mean"], rtol=1e-10, atol=1e-10
        ):
            raise ValueError("artist contributions do not sum to primary geometry error")
        artists.extend(
            dict(model=item["model"], **a, **diagnostics[a["artist"]]) for a in item["artists"]
        )
    contrasts = [
        dict(
            model_a=r["model_a"],
            model_b=r["model_b"],
            scenes=r["n"],
            difference=r["mean"],
            simultaneous_ci=ci(r, True),
            nominal_ci=ci(r),
            bootstrap_ci95=r.get("bootstrap_ci95"),
        )
        for r in primary["comparisons"]
    ]
    lines = [
        "# Artist-specificity experiment",
        "",
        "The terminal experiment compares reference artist contrasts after removing the common "
        "named response.",
        "All four painters, all six models and every assigned scene remain in the census.",
        "",
        "## Collection and accounting",
        "",
        f"Returned {audit['successful']} of {audit['planned']} planned images in "
        f"{audit['attempts']} attempts.",
        f"Additional reported charges: ${audit['incremental_charges_usd']:.6f}; cumulative "
        f"conservative accounting: ${audit['cumulative_accounted_usd']:.6f}.",
        "The cumulative figure includes the historical $5 reserve and all earlier cost probes; "
        "no remaining-credit query was made.",
        f"Raw-response hashes: {audit['raw_response_hashes_verified']}; image hashes: "
        f"{audit['raw_image_hashes_verified']}.",
        f"Peak concurrent requests: {audit['peak_active']}; shortest start spacing: "
        f"{audit['minimum_start_spacing_seconds']:.3f} seconds.",
        "",
        "## Primary recovery outcomes",
        "",
        "Beta 0 means no reference-aligned response; beta 1 matches its amplitude.",
        "Expected D=0 is exact conditional mean-geometry recovery; expected D=1 is a purely "
        "common response.",
        "The fixed 21-comparison family contains six slopes and 15 model contrasts. Absolute D "
        "intervals are nominal descriptive summaries.",
        "",
        "| Model | Scenes | Beta (simultaneous CI) | D (nominal CI) | Amplitude error | "
        "Other-direction error |",
        "| --- | ---: | --- | --- | ---: | ---: |",
    ]
    for row in models:
        lines.append(
            f"| {row['model']} | {row['scenes']} | {number(row['beta'])} "
            f"{row['beta_simultaneous_ci']} | {number(row['distortion'])} "
            f"{row['distortion_nominal_ci']} | {number(row['amplitude_error'])} | "
            f"{number(row['off_axis_error'])} |"
        )
    lines += [
        "",
        "## Paired model regression comparisons",
        "",
        "A negative difference favors model A on corrected artist-geometry error.",
        "Comparisons use paired scene differences, with the actual n-1 degrees of freedom.",
        "The common-panel OLS uses scene intercepts and GPT Image 2 as baseline. It is recorded "
        "in analysis.json.",
        "",
        "| A | B | Scenes | D(A)-D(B) | Simultaneous interval |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in contrasts:
        lines.append(
            f"| {row['model_a']} | {row['model_b']} | {row['scenes']} | "
            f"{number(row['difference'])} | {row['simultaneous_ci']} |"
        )
    lines += [
        "",
        "## Scope and sensitivity",
        "",
        f"Reference contrast H={h:.9f}; its color/spatial/texture shares are "
        f"{shares['color']:.4f}/{shares['spatial']:.4f}/{shares['texture']:.4f}.",
        f"Equal-content reference target cosine with the original: "
        f"{balanced['target_cosine']:.6f}.",
        "models.csv includes common-square and reference-content sensitivity estimates. The "
        "separate JSONs retain all intervals, resampling summaries and reference counts.",
        "artists.csv retains energy, generic energy and spread for every model/painter cell. "
        "Within-scene trace is the mean squared distance between the two repeats divided by "
        "two: the sample variance trace within a scene. It is also divided by the reference "
        "trace for comparison in common units. These are descriptive summaries, not additional "
        "hypothesis tests.",
        "The four geometry-error contributions sum to each model's primary D. They are "
        "additive diagnostics of that existing endpoint, not separate artist-fidelity scores: "
        "centering couples the four named conditions and finite contributions can be negative.",
        "A large common fraction is not evidence against artist recovery by itself. "
        "Reference-relative slopes/errors test that separate question.",
        "The primary target is conditional mean geometry in 31 fixed digital features, not full "
        "distributional or perceptual style recovery.",
        "Reference content/capture differences, feature weighting, the fixed outdoor scenes and "
        "uncertain repeat independence limit interpretation.",
        "The class-balanced reference target has its own H; absolute D values across targets "
        "are not in the same units.",
        "",
        "## Figures",
        "",
        "All figures are generated from the recorded vectors and results by "
        "`paper/make_specificity_figures.py`. Projections are descriptive; numerical inference "
        "uses all 31 coordinates.",
        "",
        "- [Model comparison](../../../paper/figures/specificity_comparison.pdf)",
        "- [Centered artist geometry](../../../paper/figures/specificity_geometry.pdf)",
        "- [Error decomposition and distribution spread]"
        "(../../../paper/figures/specificity_diagnostics.pdf)",
        "- [Monet distributions, all models]"
        "(../../../paper/figures/specificity_distribution_claude_monet.pdf)",
        "- [Sisley distributions, all models]"
        "(../../../paper/figures/specificity_distribution_alfred_sisley.pdf)",
        "- [Pissarro distributions, all models]"
        "(../../../paper/figures/specificity_distribution_camille_pissarro.pdf)",
        "- [Cézanne distributions, all models]"
        "(../../../paper/figures/specificity_distribution_paul_cezanne.pdf)",
        "- [Sunburst distributions, all four painters]"
        "(../../../paper/figures/specificity_sunburst_distributions.pdf)",
        "",
        "The four-painter Sunburst illustration was selected before inspecting new feature "
        "outcomes; it does not designate the best-performing model. Each painter's raw "
        "distribution projection is fitted to that painter's reference images only and is "
        "held fixed across model panels.",
        "",
        "## Reproduction",
        "",
        "Use the canonical commands in studies/painter_specificity_measurement_v1/CORRECTION.md.",
        "Append --check for exact numerical replay; the report command also verifies raw "
        "response/image hashes.",
        "The frozen original reader remains unchanged; the explicit adapter selects the "
        "protocol's 649 measured reference works from a manifest also retaining four older "
        "failures.",
        "No terminated predecessor image or technical pilot enters scientific analysis.",
        "",
        "```bash",
        "make specificity-check  # four exact numerical replays, no image generation",
        "make specificity-audit  # additionally requires retained local raw responses/pixels",
        "uv run --locked python paper/make_specificity_figures.py --check",
        "uv run --locked python paper/make_specificity_tables.py --check",
        "```",
        "",
    ]
    paths = [
        s.DATA / name
        for name in (
            "freeze.json",
            "collection.json",
            "attempts.jsonl",
            "measurement_receipt.json",
            "measurements.jsonl",
            "reference_windows.jsonl",
            "analysis.json",
            "analysis_square.json",
        )
    ]
    paths += [
        ref_analysis.DATA / name
        for name in ("freeze.json", "analysis.json", "analysis_square.json")
    ]
    paths += [READER_DATA / "freeze.json", Path(__file__)]
    inventory = dict(
        inputs=[dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in paths], audit=audit
    )
    return {
        "REPORT.md": "\n".join(lines).encode(),
        "models.csv": csv_bytes(models),
        "model_contrasts.csv": csv_bytes(contrasts),
        "artists.csv": csv_bytes(artists),
        "inputs.json": (json.dumps(inventory, sort_keys=True, indent=2) + "\n").encode(),
    }


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    s.REPORT.mkdir(parents=True, exist_ok=True)
    for name, raw in outputs.items():
        path = s.REPORT / name
        if args.check:
            if path.read_bytes() != raw:
                raise ValueError("report replay differs: " + name)
        else:
            with path.open("xb") as stream:
                stream.write(raw)
    print("Report and raw-byte audit " + ("verified" if args.check else "saved"))


if __name__ == "__main__":
    main()
