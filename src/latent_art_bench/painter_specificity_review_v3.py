"""Retrospective direct-naming decompositions; retained vectors only.

No acquisition, feature extraction, or modification of previous results occurs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_specificity_review_v3"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_decomposition.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "report.md"


def complete_panel(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 4 or x.shape[1:3] != (2, 6) or min(x.shape[0], x.shape[3]) < 1:
        raise ValueError("scenes x two repeats x six arms x features required")
    if not np.isfinite(x).all():
        raise ValueError("complete finite measurements required")
    return x


def shared_decomposition(x):
    """Cross-repeat products AFTER scene averaging; preserve signed components."""
    x = complete_panel(x)
    means = x.mean(axis=0)
    named_mean = means[:, 2:].mean(axis=1)
    centered = means[:, 2:] - named_mean[:, None]
    specific = float(np.sum(centered[0] * centered[1]))
    result = {}
    for baseline, index in (("named_minus_free", 0), ("named_minus_generic", 1)):
        shifts = means[:, 2:] - means[:, index, None]
        common = named_mean - means[:, index]
        common_ss = float(4 * (common[0] @ common[1]))
        total = float(np.sum(shifts[0] * shifts[1]))
        if not np.isclose(total, common_ss + specific, atol=1e-11, rtol=1e-11):
            raise ValueError("common/specific identity failed")
        result[baseline] = dict(
            common=common_ss,
            specific=specific,
            total=total,
            shared_fraction=common_ss / total if total > 0 else None,
            identity_residual=total - common_ss - specific,
        )
    generic = means[:, 1] - means[:, 0]
    naming = named_mean - means[:, 1]
    common = named_mean - means[:, 0]
    generic_ss = float(4 * (generic[0] @ generic[1]))
    naming_ss = float(4 * (naming[0] @ naming[1]))
    interaction = float(4 * (generic[0] @ naming[1] + naming[0] @ generic[1]))
    combined = result["named_minus_free"]["common"]
    residual = combined - generic_ss - naming_ss - interaction
    if not np.allclose(common, generic + naming, atol=1e-11, rtol=1e-11):
        raise ValueError("common-vector identity failed")
    if not np.isclose(combined, generic_ss + naming_ss + interaction, atol=1e-11, rtol=1e-11):
        raise ValueError("generic/naming interaction identity failed")
    result["common_shift_identity"] = dict(
        generic_component=generic_ss,
        additional_naming_component=naming_ss,
        signed_interaction=interaction,
        combined_common=combined,
        scalar_identity_residual=residual,
        vector_identity_max_abs_residual=float(np.max(np.abs(common - generic - naming))),
        generic_vectors_by_repeat=generic.tolist(),
        additional_naming_vectors_by_repeat=naming.tolist(),
        combined_vectors_by_repeat=common.tolist(),
    )
    return result


def monet_sisley_alignment(x, reference_means):
    """Finite-reference pair direction; not an equivalence or recognition test."""
    x = complete_panel(x)
    reference_means = np.asarray(reference_means, dtype=float)
    if reference_means.shape != (4, x.shape[-1]) or not np.isfinite(reference_means).all():
        raise ValueError("four finite reference means with matching feature dimension required")
    q = reference_means[0] - reference_means[1]
    h = float(q @ q)
    if h <= 0:
        raise ValueError("positive Monet-Sisley reference squared distance required")
    by_scene_repeat = np.einsum("skj,j->sk", x[:, :, 2] - x[:, :, 3], q) / h
    return dict(
        reference_pair_squared_distance=h,
        beta=float(by_scene_repeat.mean()),
        scene_beta=by_scene_repeat.mean(axis=1).tolist(),
    )


def value_range(values):
    available = [v for v in values if v is not None]
    return dict(
        available_deletions=len(available),
        range=[min(available), max(available)] if available else None,
    )


def summarize_model(x, reference_means):
    """Recompute each ratio after deletion; retain every omitted-scene value."""
    x = complete_panel(x)
    if len(x) < 2:
        raise ValueError("at least two scenes required for deletion diagnostics")
    base = shared_decomposition(x)
    pair = monet_sisley_alignment(x, reference_means)
    deletions = []
    for i in range(len(x)):
        retained = np.delete(x, i, axis=0)
        decomposition = shared_decomposition(retained)
        deletions.append(
            dict(
                omitted_scene=i,
                named_minus_free=decomposition["named_minus_free"],
                named_minus_generic=decomposition["named_minus_generic"],
                common_shift_identity={
                    key: value
                    for key, value in decomposition["common_shift_identity"].items()
                    if not key.endswith("vectors_by_repeat")
                },
                monet_sisley_beta=monet_sisley_alignment(retained, reference_means)["beta"],
            )
        )
    return dict(
        scene_averaged=base,
        monet_sisley=pair,
        scene_deletions=deletions,
        scene_deletion_summaries={
            **{
                key: value_range([d[key]["shared_fraction"] for d in deletions])
                for key in ("named_minus_free", "named_minus_generic")
            },
            "monet_sisley_beta": value_range([d["monet_sisley_beta"] for d in deletions]),
        },
    )


def input_bindings():
    """Bind the new analysis and all inputs named by existing scientific freezes."""
    paths = {
        PLAN,
        Path(__file__),
        TEST,
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "freeze.json",
        measured.DATA / "freeze.json",
        measured.ref_analysis.DATA / "freeze.json",
        s.DATA / "collection.json",
        s.DATA / "requests.jsonl",
        s.DATA / "measurement_receipt.json",
        s.DATA / "measurements.jsonl",
        s.DATA / "reference_windows.jsonl",
        s.REF,
        s.SCALER,
        Path(measured.__file__),
        Path(measured.ref_analysis.__file__),
    }
    visited = set()
    while paths - visited:
        path = sorted(paths - visited)[0]
        visited.add(path)
        if path.name == "freeze.json":
            for entry in s.read(path)["inputs"]:
                paths.add(s.ROOT / entry["path"])
    return [
        dict(path=str(path.relative_to(s.ROOT)), sha256=s.sha(path))
        for path in sorted(visited)
    ]


def compute():
    bindings = input_bindings()
    views = {}
    for key, square in (("full_frame", False), ("central_square", True)):
        x, refs = measured.load(square=square)
        if x.shape != (6, 14, 2, 6, 31):
            raise ValueError("the retained complete 1008-image panel is required")
        means = np.array([r.mean(axis=0) for r in refs])
        views[key] = dict(
            generated_shape=list(x.shape),
            reference_counts=[len(r) for r in refs],
            models=[
                dict(model=model, title=title, **summarize_model(row, means))
                for model, title, row in zip(s.MODELS, s.TITLES, x)
            ],
        )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; exploratory full-frame direct-naming values already inspected",
        uncertainty="descriptive scene-deletion ranges only; no tests or confidence intervals",
        aggregation="equal scenes within repeat, then cross-repeat products",
        inputs=bindings,
        scenes=[
            dict(index=i, content=kind, brief=brief) for i, (kind, brief) in enumerate(s.SCENES)
        ],
        views=views,
    )


def fmt(value, scale=1):
    return "unavailable" if value is None else f"{scale * value:.4f}"


def range_text(summary, scale=1):
    limits = summary["range"]
    if limits is None:
        return "unavailable"
    return f"[{fmt(limits[0], scale)}, {fmt(limits[1], scale)}]"


def report(result):
    lines = [
        "# Retrospective direct-naming and scene-stability diagnostics",
        "",
        "This is a post-result analysis, not a preregistration. The full-frame "
        "named-minus-generic shared fractions had already been inspected before "
        "the plan was written. Existing scientific files and results are preserved.",
        "",
        "## Estimands and limits",
        "",
        "Each arm is averaged over scenes within repeat before taking cross-repeat "
        "products. Common = 4 times the cross-product of the four-name mean shifts; "
        "specific = the summed cross-products of departures from those shifts. "
        "Their sum is total squared change. Changing the common baseline leaves "
        "the specific component unchanged. Fractions use common/total only for "
        "positive totals; signed components and unbounded fractions are retained.",
        "",
        "Let g = generic minus free, n = mean named minus generic, and c = mean "
        "named minus free, for each repeat. The exact vector identity is c = g+n. "
        "Thus 4<c1,c2> = 4<g1,g2> + 4<n1,n2> + 4(<g1,n2>+<n1,g2>). "
        "The final signed term is an algebraic interaction, not a causal factorial "
        "interaction. Squared generic and naming contributions cannot simply be added.",
        "",
        "Deletion ranges recompute the full statistic after omitting each scene, "
        "holding the finite reference and scaler fixed. They are sensitivity ranges, "
        "not confidence intervals. Cross-repeat noise correction requires stable "
        "conditional means and independent mean-zero repeat errors; it does not "
        "verify service independence. The finite reference includes subject and "
        "capture differences. Neither pair alignment nor these feature shifts "
        "validate perceptual style. Square windows change content and are not "
        "an independent replication. No new tests or image generation were added.",
    ]
    for view, data in result["views"].items():
        lines += [
            "",
            f"## {view.replace('_', ' ').title()}",
            "",
            "Shared fractions and deletion ranges are percentages. Pair beta uses "
            "the corresponding finite-reference Monet-minus-Sisley direction.",
            "",
            "| Configuration | Named-free shared % [deletion range] | "
            "Named-generic shared % [deletion range] | Monet-Sisley beta [deletion range] |",
            "|---|---:|---:|---:|",
        ]
        for row in data["models"]:
            base, stability = row["scene_averaged"], row["scene_deletion_summaries"]
            cells = [row["title"]]
            for key in ("named_minus_free", "named_minus_generic"):
                cells.append(
                    f"{fmt(base[key]['shared_fraction'], 100)} {range_text(stability[key], 100)}"
                )
            cells.append(
                f"{fmt(row['monet_sisley']['beta'])} "
                f"{range_text(stability['monet_sisley_beta'])}"
            )
            lines.append("| " + " | ".join(cells) + " |")
        lines += [
            "",
            "Signed squared-change terms in standardized feature units:",
            "",
            "| Configuration | Generic common G | Additional naming common N | "
            "Interaction I | Combined common C=G+N+I | Specific B |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for row in data["models"]:
            base = row["scene_averaged"]
            identity = base["common_shift_identity"]
            cells = [row["title"]] + [
                fmt(identity[key])
                for key in (
                    "generic_component", "additional_naming_component",
                    "signed_interaction", "combined_common",
                )
            ] + [fmt(base["named_minus_free"]["specific"])]
            lines.append("| " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Replay and input bindings",
        "",
        "All per-scene deletions, pair summaries, common vectors and identity "
        "residuals are retained in `analysis.json`. The commands below are offline:",
        "",
        "```sh",
        "uv run --locked pytest -q tests/painter_specificity_review_v3",
        "uv run --locked python -m latent_art_bench.painter_specificity_review_v3 check",
        "```",
        "",
        "SHA-256 bindings (including the plan, implementation and analytical tests):",
        "",
        "| Path | SHA-256 |",
        "|---|---|",
    ]
    lines += [f"| `{row['path']}` | `{row['sha256']}` |" for row in result["inputs"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("action", choices=("analyze", "check"))
    args = parser.parse_args()
    if args.action == "analyze" and (JSON_PATH.exists() or REPORT_PATH.exists()):
        raise FileExistsError("v3 outputs already exist; use check, never overwrite")
    result = compute()
    markdown = report(result)
    if args.action == "check":
        if result != s.read(JSON_PATH) or markdown != REPORT_PATH.read_text():
            raise ValueError("exact v3 JSON/Markdown replay differs")
        print("Exact v3 numerical and report replay passed")
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        with JSON_PATH.open("x") as stream:
            json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
        with REPORT_PATH.open("x") as stream:
            stream.write(markdown)
        print("New v3 analysis and bound report saved")


if __name__ == "__main__":
    main()
