"""Render a traceable empirical Markdown report; no manuscript or new statistical decisions."""

from __future__ import annotations

import os
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    bindings,
    identifier,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_feature_generation_v2.pipeline import _committed

REPORT = Path("reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md")
NAMES = dict(zip(PAINTER_IDS, ("Monet", "Sisley", "Pissarro", "Cézanne")))


def number(value) -> str:
    return "unresolved" if value is None else f"{value:.4f}"


def table(headers: list, rows: list) -> str:
    def line(values):
        return (
            "| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in values) + " |"
        )

    return (
        "\n"
        + "\n".join([line(headers), line(["---"] * len(headers)), *[line(row) for row in rows]])
        + "\n"
    )


def indexed(endpoints: list) -> dict:
    return {(r["painter_id"], r["family"], r["endpoint"], r["comparison"]): r for r in endpoints}


def render(
    method_id: str, empirical: dict, calibration: dict, robustness: dict, repeated: dict[str, dict]
) -> str:
    comparisons = empirical["comparisons"]
    metadata = empirical["metadata_diagnostics"]["by_painter_and_role"]
    total = sum(r["frame_count"] for r in metadata)
    acquired = sum(r["acquired_count"] for r in metadata)
    measured = sum(r["measured_count"] for r in metadata)
    confirmation = sum(r["measured_count"] for r in metadata if r["role"] == "confirmation")
    text = [
        "# Available image-generation services: empirical painter-feature analysis\n",
        f"Analysis report, not a manuscript. Recorded 2026-09-05. Method: `{method_id}`.\n",
        "## Outcome and interpretation\n",
        f"The fixed frame contains {total:,} works: {acquired:,} acquired, "
        f"{measured:,} successfully measured, and {confirmation:,} in the finite reference. "
        "Complete measured comparisons are available for "
        f"{', '.join(comparisons) or 'no service'}.\n",
        "**Painter-feature reproduction is not demonstrated.** The analysis measures discrepancy "
        "and painter-name/control contrasts, not equivalence. Independent-capture calibration and "
        "justified equivalence margins remain unavailable. The coverage check prevents "
        "treating nominal 95% intervals as validated confidence guarantees.\n",
    ]
    rows = []
    for alias, result in comparisons.items():
        endpoints = result["endpoints"]
        controls = [r for r in endpoints if r["endpoint"] == "control_improvement"]
        specific = indexed(endpoints)
        own_closest = sum(
            all(specific[p, f, "specificity", q]["estimate"] < 0 for q in PAINTER_IDS if q != p)
            for p in PAINTER_IDS
            for f in ("color", "spatial", "texture")
        )
        rows.append(
            [
                alias,
                result["generated_counts"]["artist_free"],
                f"{sum(r['estimate'] < 0 for r in controls)}/12",
                f"{own_closest}/12",
            ]
        )
    text += [
        table(
            [
                "Requested service / baseline",
                "Images per condition",
                "Negative named-minus-control contrasts",
                "Own target closer than all three others",
            ],
            rows,
        ),
        "These are descriptive sign counts, not significance tests or a ranking. Each denominator "
        "is four painters × three families. Unequal generated sample sizes affect the finite "
        "V-statistic; the OAuth aliases have one repetition and unverified underlying snapshots.\n",
        "## Registered experiment and observed service behavior\n",
        "SD-Turbo uses checkpoint `b261bac6fd2cf515557d5d0707481eafa0485ec2`, local FP16 MPS, "
        "512×512, one step, guidance 0, and 25 paired seed blocks. The OAuth pilot requests "
        "`gpt-image-1` and `gpt-image-2` through the dated local Codex OAuth proxy: all 16 exact "
        "templates × five conditions × one repetition per alias. It supplies no seed. "
        "No aesthetic selection, rerolls, or paid API fallback were used.\n",
    ]
    rows = []
    for experiment, record in empirical["generation"].items():
        for alias, diagnostic in record.get("service_diagnostics", {}).items():
            rows.append(
                [
                    alias,
                    diagnostic["statuses"],
                    diagnostic["decoded_sizes"],
                    diagnostic["reported_settings"]["quality"],
                    diagnostic["reported_settings"]["model"],
                ]
            )
        if not record["complete_generated_grid"]:
            text.append(
                f"Experiment `{experiment}` failed the complete-grid gate and receives "
                "availability reporting only; it is not included in fidelity tables.\n"
            )
    text += [
        table(
            ["Alias", "Terminal outcomes", "Decoded sizes", "Reported quality", "Reported model"],
            rows,
        ),
        "OAuth requests asked for 1024×1024 / medium / PNG. Actual returned geometry and quality "
        "are retained separately; normalization does not retroactively satisfy those requested "
        "controls. `None` means no model identifier was returned, not a verified shared model. "
        "SD-Turbo has a local checkpoint contract rather than response-reported settings. "
        "Latency and every requested/returned mismatch are in the numeric result.\n",
        "## Corpus, attrition and measurement\n",
        "The real frame is Wikidata-declared outdoor-place paintings, not institutionally verified "
        "attribution or a probability sample of a painter's oeuvre. Works retain their fixed "
        "roles after losses. Historical exposure matching placed 91 records in development-only; "
        "14 denylist records lacked crosswalk identifiers; absence of leakage is unproved.\n",
    ]
    text.append(
        table(
            ["Painter", "Role", "Frame", "Acquired", "Measured"],
            [
                [
                    NAMES[r["painter_id"]],
                    r["role"],
                    r["frame_count"],
                    r["acquired_count"],
                    r["measured_count"],
                ]
                for r in metadata
            ],
        )
    )
    failures = [
        f"{NAMES[r['painter_id']]} / {r['role']}: {r['acquisition_failure_reasons']}"
        for r in metadata
        if r["acquisition_failure_reasons"]
    ]
    if failures:
        text.append("Acquisition failures: " + "; ".join(failures) + ".\n")
    measurement_failures = [
        f"{NAMES[r['painter_id']]} / {r['role']}: {r['measurement_failure_reasons']}"
        for r in metadata
        if r.get("measurement_failure_reasons")
    ]
    text.append("Measurement failures: " + ("; ".join(measurement_failures) or "none") + ".\n")
    text += [
        "All real images come from the complete corrected R2 rendering run. Earlier original "
        "and first-rendering acquisitions are terminal; their partial successes were not spliced "
        "into R2. The correction recognizes Wikimedia's new thumbnail host and actual advertised "
        "thumbnail sizes; no work was added or threshold lowered. "
        "[Wikimedia host migration](https://phabricator.wikimedia.org/T434821); "
        "[Imageinfo size behavior](https://www.mediawiki.org/wiki/API:Imageinfo/en).\n",
        "The shared method fully decodes, applies EXIF, converts valid ICC profiles to sRGB, "
        "flags missing profiles as assumed sRGB, preserves aspect ratio, and downsamples without "
        "upsampling to short side 512. It measures 11 color, eight spatial/orientation, and 12 "
        "digital-texture coordinates. A common equal-painter median/IQR transform is fitted only "
        "on new development. Qualification is diagnostic and does not select a method.\n",
        "## Complete finite comparisons\n",
        "Energy distance is computed between the finite measured reference and finite generated "
        "sets, with both self terms including diagonals (V-statistic). Lower own-target distance "
        "means closer measured distributions; negative named-minus-artist-free values favor the "
        "named condition. Family distances are not comparable across different dimensions.\n",
    ]
    for alias, result in comparisons.items():
        lookup = indexed(result["endpoints"])
        rows = []
        for p in PAINTER_IDS:
            for f in ("color", "spatial", "texture"):
                rows.append(
                    [
                        NAMES[p],
                        f,
                        number(lookup[p, f, "target_fit", None]["estimate"]),
                        number(lookup[p, f, "control_improvement", "artist_free"]["estimate"]),
                    ]
                )
        text += [
            f"### {alias}\n",
            table(["Painter", "Family", "Own-target distance", "Named minus artist-free"], rows),
        ]
        rows = []
        for p in PAINTER_IDS:
            for f in ("color", "spatial", "texture"):
                rows.append(
                    [
                        NAMES[p],
                        f,
                        *[
                            "—" if q == p else number(lookup[p, f, "specificity", q]["estimate"])
                            for q in PAINTER_IDS
                        ],
                    ]
                )
        text += [
            "Own-target minus each wrong-painter distance; negatives favor own-target fit.\n",
            table(["Named painter", "Family", *NAMES.values()], rows),
        ]
    text += [
        "All 124 coordinate median differences and IQR ratios per available service are "
        "retained in `empirical_analysis.json`; none is thresholded into a reproduction label.\n",
        "## Repeated SD-Turbo uncertainty and calibration\n",
        "The SD-Turbo generator estimator excludes equal repetition blocks in its generated self "
        "term; it differs from the finite tables above and may be negative. The 9,999 bootstrap "
        "resamples jointly resample whole blocks across all 60 endpoints, conditioning on the "
        "finite real reference. Intervals are nominal and exploratory, not validated tests.\n",
    ]
    for experiment, result in repeated.items():
        text.append(
            f"Experiment `{experiment}`: {result['repetitions']} blocks; all "
            f"{result['simultaneous_endpoint_count']} intervals are retained in its "
            "`analysis.json`. The control intervals are shown below.\n"
        )
        text.append(
            table(
                ["Painter", "Family", "U-estimator contrast", "Nominal joint 95% interval"],
                [
                    [
                        NAMES[r["painter_id"]],
                        r["family"],
                        number(r["estimate"]),
                        f"[{number(r['lower'])}, {number(r['upper'])}]",
                    ]
                    for r in result["endpoints"]
                    if r["endpoint"] == "control_improvement"
                ],
            )
        )
    text.append(
        table(
            [
                "Synthetic scenario",
                "Joint coverage, nondegenerate endpoints",
                "Monte Carlo Wilson 95% interval",
                "Zero-variance endpoint counts",
            ],
            [
                [
                    r["scenario"],
                    number(r["joint_coverage_nondegenerate_endpoints"]),
                    f"[{number(r['coverage_mc_wilson_95'][0])}, "
                    f"{number(r['coverage_mc_wilson_95'][1])}]",
                    r["zero_variance_endpoint_counts"],
                ]
                for r in calibration["scenarios"]
            ],
        )
    )
    text += [
        "Calibration used 100 trials per scenario, eight possible synthetic blocks, 16 templates, "
        "31 coordinates, 25 blocks and 999 bootstrap draws per trial. Null coverage excludes "
        "48 zero-variance endpoints without intervals; it is not complete 60-endpoint coverage. "
        "The shift scenario's 0.86 coverage rules out presenting nominal 0.95 as demonstrated. "
        "Exact truths, bias and Monte Carlo uncertainty are retained. No active-outcome retuning "
        "was performed.\n",
        "## Crop and source sensitivity\n",
        f"Paired crop status: `{robustness['status']}`; {robustness['expected_records']:,} images "
        "per branch. Both uncropped and uniform 1% cropped images use short side 496, with the "
        "same transform fitted on uncropped-496 new development. This separates crop effects "
        "from changing the analysis scale and never upsamples SD-Turbo.\n",
    ]
    for alias, changes in robustness.get("endpoint_changes", {}).items():
        controls = [r for r in changes if r["endpoint"] == "control_improvement"]
        reversals = sum(r["uncropped"] * r["cropped"] < 0 for r in controls)
        text.append(f"{alias}: {reversals}/12 descriptive control-contrast sign reversals.\n")
        text.append(
            table(
                ["Painter", "Family", "Uncropped 496", "Cropped 496", "Change"],
                [
                    [
                        NAMES[r["painter_id"]],
                        r["family"],
                        number(r["uncropped"]),
                        number(r["cropped"]),
                        number(r["change"]),
                    ]
                    for r in controls
                ],
            )
        )
    text.append(
        "Crop results retain all target/specificity changes and paired feature-shift summaries "
        "in `robustness_analysis.json`. Crops are dependent versions of one capture, not "
        "independent reproductions of the physical painting.\n"
    )
    text.append(
        table(
            [
                "Painter (confirmation)",
                "Profiles",
                "Native short side min/median/max",
                "Aspect min/median/max",
                "Frame content composition",
            ],
            [
                [
                    NAMES[r["painter_id"]],
                    r["profile_counts"],
                    [round(x, 2) for x in r["measured_short_side_summary"]],
                    [round(x, 3) for x in r["measured_aspect_ratio_summary"]],
                    r["content_memberships"],
                ]
                for r in metadata
                if r["role"] == "confirmation"
            ],
        )
    )
    strata = empirical["stratified_distances"]
    sparse = sum(r["status"] == "sparse_unresolved" for r in strata)
    text += [
        f"The content/profile/resolution diagnostic contains {len(strata)} stratum "
        f"records; {sparse} are unresolved with fewer than ten works. Supported-stratum distances "
        "use the full generated condition, not matched generated subject matter. They cannot "
        "separate style from content. Collection memberships and all strata are retained in the "
        "numeric result; native-short-side bins are 1024–2047, 2048–4095 and ≥4096 pixels. "
        "Collections are not established capture workflows.\n",
        "## Duplicates and copying limitations\n",
    ]
    text.append(
        table(
            [
                "Service",
                "Exact generated duplicate excess",
                "Perceptual/exact candidates",
                "Exact real-file matches",
            ],
            [
                [
                    alias,
                    r["copy_diagnostics"]["generated_exact_duplicate_excess"],
                    len(r["copy_diagnostics"]["candidates"]),
                    sum(
                        bool(c["exact_file_references"])
                        for c in r["copy_diagnostics"]["candidates"]
                    ),
                ]
                for alias, r in comparisons.items()
            ],
        )
    )
    text += [
        "The search covers successfully measured development, qualification and confirmation "
        "images. The 63-bit perceptual-hash distance threshold of eight is uncalibrated screening, "
        "not adjudication. Finding no candidate cannot prove originality or training nonoverlap. "
        "Generated duplicates retain full statistical multiplicity.\n",
        "## What remains before a research-paper claim\n",
        "This completes the registered descriptive experiment only where the grid and measurement "
        "gates passed. A stronger model-level study still requires attested OAuth model identity "
        "and controllable settings, repeated GPT grids, better-validated uncertainty, "
        "and genuine independent captures with justified equivalence margins. Better control of "
        "subject matter, capture workflows, borders and training overlap is also needed. "
        "These data cannot establish physical brushwork, content-free style, artistic intent, "
        "authorship or oeuvre-wide reproduction. All checks are operator/LLM-assisted; no "
        "institutionally independent review is claimed.\n",
        "## Evidence and reproduction\n",
        f"The [method evidence directory](../../{MANIFESTS / method_id}/) contains the shared "
        "freeze, one-time confirmation opening, scaler, access ledger, stage receipts, "
        "`empirical_analysis.json`, per-experiment `analysis.json`, and crop evidence. "
        "Every report table is rendered from these numeric artifacts. Frozen input hashes "
        "are commit-bound; raw media, HTTP bodies and model weights remain in the ignored research "
        "workspace and are not redistributed. Terminal studies are never rerun in place.\n",
        "The [prospective empirical amendment](../../studies/"
        "painter_feature_generation_v2/PROTOCOL_1.2.md) "
        "defines the estimands and limits. The [earlier access report](AVAILABLE_IMAGE_MODELS.md) "
        "documents the neutral-image transport assessment, separate from this painter grid. "
        "Measurement rationale: [Székely and Rizzo's energy statistics]"
        "(https://doi.org/10.1016/j.jspi.2013.03.018); "
        "the [pinned SD-Turbo model card](https://huggingface.co/stabilityai/sd-turbo/blob/"
        "b261bac6fd2cf515557d5d0707481eafa0485ec2/README.md) defines the local model contract.\n",
        "```bash\nuv run --locked --extra analysis --extra learned ruff check .\n"
        'uv run --locked --extra analysis --extra learned pytest -q -m "not live"\n'
        "uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence\n"
        "uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit\n"
        "```\n",
    ]
    return "\n".join(text)


def execute(root: Path, method_id: str) -> dict:
    identifier(method_id)
    output = root / MANIFESTS / method_id
    if (root / REPORT).exists() or (output / "report_receipt.json").exists():
        raise FileExistsError(
            "empirical report is terminal; use a new report version for amendments"
        )
    frozen = read_json(output / "method_freeze.json")
    verify_bindings(root, frozen["inputs"])
    empirical = read_json(output / "empirical_analysis.json")
    if "sd-turbo" in empirical["comparisons"]:
        experiment = empirical["comparisons"]["sd-turbo"]["experiment_id"]
        if not (output / "experiments" / experiment / "analysis.json").exists():
            raise ValueError("the registered repeated SD-Turbo analysis is not complete")
    robustness = read_json(output / "robustness" / "robustness_analysis.json")
    for value in (empirical, robustness):
        verify_bindings(root, value["inputs"])
    calibration_path = MANIFESTS / frozen["calibration_id"] / "calibration.json"
    calibration = read_json(root / calibration_path)
    repeated, paths = (
        {},
        [
            calibration_path,
            (output / "empirical_analysis.json").relative_to(root),
            (output / "robustness" / "robustness_analysis.json").relative_to(root),
            Path("src/latent_art_bench/painter_feature_generation_v2/report.py"),
        ],
    )
    paths += [
        (output / name).relative_to(root)
        for name in (
            "method_freeze.json",
            "confirmation_opening.json",
            "access_events.jsonl",
            "development_receipt.json",
            "qualification_receipt.json",
            "confirmation_receipt.json",
        )
    ]
    for experiment in frozen["experiment_ids"]:
        path = output / "experiments" / experiment / "analysis.json"
        if path.exists():
            value = read_json(path)
            verify_bindings(root, value["inputs"])
            repeated[experiment] = value
            paths.append(path.relative_to(root))
    commit = _committed(root, paths)
    rendered = render(method_id, empirical, calibration, robustness, repeated)
    (root / REPORT).parent.mkdir(parents=True, exist_ok=True)
    with (root / REPORT).open("x", encoding="utf-8") as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
    receipt = dict(
        method_id=method_id,
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        files=[dict(path=str(REPORT), sha256=hash_file(root / REPORT))],
        completed_at_utc=utc_now().isoformat(),
        deliverable="analysis_report_not_manuscript",
    )
    publish(output / "report_receipt.json", receipt)
    return receipt
