"""Retrospective primary-D point sensitivity to assumed cross-repeat covariance.

Import and freeze do not compute real sensitivity outcomes. Analyze/check require
--execute-real after review of the versioned plan and synthetic tests.
"""

from __future__ import annotations

import argparse
import itertools
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from latent_art_bench import painter_specificity_review_v2 as review
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v1.analysis import centered, geometry
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_repeat_covariance_v1"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS
RHO_GRID = (0.0, 0.1, 0.25, 0.5, 0.75)
REPLAY_TOLERANCE = 1e-12
PRIMARY = s.DATA / "analysis.json"
PREVIOUS = review.OUT / "analysis.json"


def scene_statistics(named, reference_contrasts):
    """Pure numerical summary; no file access or dependence assumption fitting."""
    named = np.asarray(named, dtype=np.float64)
    r = np.asarray(reference_contrasts, dtype=np.float64)
    if (
        named.ndim != 4
        or named.shape[1:3] != (2, 4)
        or min(named.shape[0], named.shape[-1]) < 1
        or r.shape != (4, named.shape[-1])
        or not np.isfinite(named).all()
        or not np.isfinite(r).all()
    ):
        raise ValueError("finite scenes x two repeats x four artists x features required")
    if not np.allclose(r.mean(axis=0), 0, atol=REPLAY_TOLERANCE, rtol=0):
        raise ValueError("reference contrasts must be artist-centered")
    h = float(np.square(r).sum())
    if not np.isfinite(h) or h <= 0:
        raise ValueError("positive finite reference squared magnitude required")
    d = centered(named)
    errors = d - r
    scene_d = np.sum(errors[:, 0] * errors[:, 1], axis=(1, 2)) / h
    scene_q = np.square(d[:, 0] - d[:, 1]).sum(axis=(1, 2)) / (2 * h)
    if not np.isfinite(scene_d).all() or not np.isfinite(scene_q).all():
        raise ValueError("nonfinite scene statistic")
    return dict(
        reference_h=h, scene_d=scene_d.tolist(), scene_q=scene_q.tolist(),
        d=float(scene_d.mean()), q=float(scene_q.mean()),
    )


def sensitivity(d, q, rho):
    """Point scenario for a fixed assumed aggregate trace correlation."""
    d, q, rho = map(float, (d, q, rho))
    if not np.isfinite([d, q, rho]).all() or q < 0 or not 0 <= rho < 1:
        raise ValueError("finite D, nonnegative q, and 0 <= rho < 1 required")
    alpha = rho / (1 - rho)
    bias = alpha * q
    adjusted = d - bias
    if not np.isfinite([alpha, bias, adjusted]).all():
        raise ValueError("nonfinite sensitivity statistic")
    return dict(
        rho=rho, alpha=alpha, implied_bias=bias, adjusted_d=adjusted,
        negative_adjusted_d=bool(adjusted < 0),
    )


def model_curve(d, q):
    return [sensitivity(d, q, rho) for rho in RHO_GRID]


def pair_curve(d_a, q_a, d_b, q_b):
    """All sign cases use unrounded differences; no interval or testing claims."""
    a, b = model_curve(d_a, q_a), model_curve(d_b, q_b)
    delta_d, delta_q = float(d_a - d_b), float(q_a - q_b)
    if not np.isfinite([delta_d, delta_q]).all():
        raise ValueError("nonfinite pair difference")
    crossing = dict(
        status="no_positive_interior_crossing", rho=None, alpha=None,
        implied_bias_a=None, implied_bias_b=None,
    )
    if delta_d == 0:
        crossing["status"] = "tied_for_all_rho" if delta_q == 0 else "initial_tie_separates"
    elif delta_q != 0 and (delta_d > 0) == (delta_q > 0):
        alpha = delta_d / delta_q
        rho = abs(delta_d) / (abs(delta_d) + abs(delta_q))
        biases = alpha * q_a, alpha * q_b
        if not np.isfinite([alpha, rho, *biases]).all() or not 0 < rho < 1:
            raise ValueError("interior crossing exceeds representable float64 precision")
        crossing.update(
            status="positive_interior_crossing", rho=float(rho), alpha=float(alpha),
            implied_bias_a=float(biases[0]), implied_bias_b=float(biases[1]),
        )
    return dict(
        delta_d=delta_d, delta_q=delta_q,
        grid=[dict(
            rho=aa["rho"],
            implied_bias_difference=aa["alpha"] * delta_q,
            adjusted_difference=delta_d - aa["alpha"] * delta_q,
        ) for aa, _ in zip(a, b)],
        crossing=crossing,
    )


def write_new(path, value):
    """Exclusive creation; no replacement of any prior artifact."""
    path = Path(path)
    text = value if isinstance(value, str) else json.dumps(
        value, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(text)


def verify_inherited_bindings():
    measured.verify()
    for item in s.read(PREVIOUS)["inputs"]:
        if s.sha(s.ROOT / item["path"]) != item["sha256"]:
            raise ValueError("inherited review-v2 binding changed: " + item["path"])


def binding_paths():
    """Hash inputs without assembling vectors or computing sensitivity outcomes."""
    tests = set((s.ROOT / "tests" / NS).glob("test_*.py"))
    if not tests:
        raise ValueError("synthetic tests must exist before freeze")
    paths = {
        PLAN, Path(__file__), PRIMARY, PREVIOUS,
        s.ROOT / "pyproject.toml", s.ROOT / "uv.lock", s.ROOT / "pytest.ini",
        s.DATA / "freeze.json", measured.DATA / "freeze.json",
        measured.ref_analysis.DATA / "freeze.json",
        s.DATA / "collection.json", s.DATA / "requests.jsonl",
        s.DATA / "measurement_receipt.json", s.DATA / "measurements.jsonl",
        s.DATA / "reference_windows.jsonl", s.REF, s.SCALER,
        Path(measured.__file__), Path(review.__file__),
        s.ROOT / "src/latent_art_bench/painter_specificity_v1/analysis.py",
        s.ROOT / "src/latent_art_bench/painter_specificity_v2/analysis.py",
        s.ROOT / "studies/painter_specificity_v2/PROTOCOL.md",
        s.ROOT / "studies/painter_specificity_measurement_v1/CORRECTION.md",
        *tests,
    }
    paths.update(s.ROOT / item["path"] for item in s.read(PREVIOUS)["inputs"])
    visited = set()
    while paths - visited:
        path = sorted(paths - visited)[0]
        visited.add(path)
        if path.name == "freeze.json":
            paths.update(s.ROOT / item["path"] for item in s.read(path)["inputs"])
    return sorted(visited)


def freeze():
    """Provenance only; no real sensitivity outcomes are computed."""
    if any((OUT / name).exists() for name in ("inputs.json", "analysis.json", "REPORT.md")):
        raise FileExistsError("covariance namespace already contains frozen inputs or outputs")
    verify_inherited_bindings()
    inputs = dict(
        schema_version=1, study=NS,
        created_utc=datetime.now(timezone.utc).isoformat(),
        status="retrospective; frozen before new covariance sensitivity outcomes",
        rho_grid=list(RHO_GRID), replay_tolerance=REPLAY_TOLERANCE,
        bindings={str(p.relative_to(s.ROOT)): s.sha(p) for p in binding_paths()},
        environment=dict(python=platform.python_version(), numpy=np.__version__),
    )
    write_new(OUT / "inputs.json", inputs)


def verify_freeze():
    inputs = s.read(OUT / "inputs.json")
    if (
        inputs["study"] != NS or inputs["rho_grid"] != list(RHO_GRID)
        or inputs["replay_tolerance"] != REPLAY_TOLERANCE
        or set(inputs["bindings"]) != {str(p.relative_to(s.ROOT)) for p in binding_paths()}
    ):
        raise ValueError("covariance frozen plan or binding membership changed")
    for path, expected in inputs["bindings"].items():
        if s.sha(s.ROOT / path) != expected:
            raise ValueError("frozen covariance input changed: " + path)
    verify_inherited_bindings()
    return inputs


def require_replay(actual, expected, label):
    actual, expected = np.asarray(actual), np.asarray(expected)
    if actual.shape != expected.shape or not np.allclose(
        actual, expected, atol=REPLAY_TOLERANCE, rtol=REPLAY_TOLERANCE
    ):
        raise ValueError("canonical replay differs: " + label)


def compute_real():
    """Only execute after method review; synthetic tests never call this function."""
    verify_freeze()
    x, refs = measured.load(square=False)
    if x.shape != (6, 14, 2, 6, 31) or not np.isfinite(x).all():
        raise ValueError("complete finite retained 1008-image panel required")
    if tuple(map(len, refs)) != (297, 106, 141, 105):
        raise ValueError("canonical 649-work reference membership required")
    primary, previous = s.read(PRIMARY), s.read(PREVIOUS)
    if [row["model"] for row in primary["models"]] != list(s.MODELS):
        raise ValueError("canonical primary model membership/order changed")
    if [row["model"] for row in previous["models"]] != list(s.TITLES):
        raise ValueError("review-v2 model membership/order changed")
    r = centered(np.array([ref.mean(axis=0) for ref in refs]))
    models = []
    for i, (model, title, named) in enumerate(zip(s.MODELS, s.TITLES, x[:, :, :, 2:])):
        stats = scene_statistics(named, r)
        canonical = geometry(named, refs)
        require_replay(stats["scene_d"], canonical["distortion"], "geometry scene D")
        require_replay(stats["scene_d"], primary["models"][i]["scene_distortion"], "frozen D")
        require_replay(stats["d"], primary["models"][i]["distortion"]["mean"], "mean D")
        require_replay(stats["q"], review.centered_noise_power(x[i], r)["direct"], "direct q")
        require_replay(
            stats["q"], previous["models"][i]["centered_repeat_noise_power"]["direct"],
            "frozen review-v2 q",
        )
        models.append(dict(
            model=model, title=title, **stats, grid=model_curve(stats["d"], stats["q"])
        ))
    pairs = [dict(
        model_a=models[a]["model"], title_a=models[a]["title"],
        model_b=models[b]["model"], title_b=models[b]["title"],
        **pair_curve(models[a]["d"], models[a]["q"], models[b]["d"], models[b]["q"]),
    ) for a, b in itertools.combinations(range(6), 2)]
    verify_freeze()
    return dict(
        schema_version=1, study=NS, status="retrospective_descriptive_point_sensitivity",
        inputs_sha256=s.sha(OUT / "inputs.json"), generated_shape=list(x.shape),
        reference_counts=list(map(len, refs)), rho_grid=list(RHO_GRID),
        assumption="same hypothetical aggregate trace correlation across configurations",
        uncertainty="none; no confidence intervals or tests; rho is not estimated",
        canonical_replay=dict(primary_d=True, review_v2_direct_q=True, tolerance=REPLAY_TOLERANCE),
        scenes=[
            dict(index=i, content=kind, brief=brief) for i, (kind, brief) in enumerate(s.SCENES)
        ],
        models=models, pairs=pairs,
    )


def report(result):
    lines = [
        "# Primary-D cross-repeat covariance sensitivity", "",
        "Retrospective point-estimate scenarios for the complete retained panel. The same "
        "hypothetical trace correlation rho is applied to all six configurations. "
        "No correlation is estimated from these data.", "",
        "Repeat differences estimate q = V − C, with marginal noise power V and "
        "cross-repeat covariance trace C, normalized by H. Assuming rho = C/V gives "
        "bias C = rho q/(1 − rho). The scenario curve subtracts this implied bias from D.",
        "", "## All configuration scenarios", "",
        "| Configuration | rho | Original D | q | Implied bias | Adjusted D | Negative |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for model in result["models"]:
        for row in model["grid"]:
            lines.append(
                f"| {model['title']} | {row['rho']:.2f} | {model['d']:.6f} | "
                f"{model['q']:.6f} | {row['implied_bias']:.6f} | "
                f"{row['adjusted_d']:.6f} | {'yes' if row['negative_adjusted_d'] else 'no'} |"
            )
    lines += [
        "", "## All paired point differences and analytic crossings", "",
        "Differences are first minus second. Thresholds use unrounded values, and refer "
        "only to point ordering under the common-rho assumption. They are not thresholds "
        "for statistical significance. A crossing can lie above the displayed grid.", "",
        "| Pair | Delta q | rho=0 | rho=.10 | rho=.25 | rho=.50 | rho=.75 | "
        "Crossing rho | Status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for pair in result["pairs"]:
        crossing = pair["crossing"]
        threshold = "—" if crossing["rho"] is None else f"{crossing['rho']:.6f}"
        cells = [f"{pair['title_a']} minus {pair['title_b']}", f"{pair['delta_q']:.6f}"]
        cells += [f"{row['adjusted_difference']:.6f}" for row in pair["grid"]]
        lines.append("| " + " | ".join([*cells, threshold, crossing["status"]]) + " |")
    lines += [
        "", "## Interpretation limits", "",
        "Equal trace correlation allows different covariance biases when q differs. Equal "
        "normalized covariance bias would instead shift all D values equally and preserve "
        "all paired differences. Model-specific correlations are outside this fixed scenario.",
        "",
        "These calculations assume stable conditional means and mean-zero errors with finite "
        "second moments. Two repeats do not identify covariance: a state shared by both "
        "repeats disappears from their difference, and no finite upper covariance bound "
        "follows from q alone. The grid is not a plausible-range estimate or a robustness "
        "guarantee. A state conditioned on as fixed changes the mean target relative to a "
        "state averaged over new collection sessions.", "",
        "Negative adjusted estimates are retained and flagged; they are not physical "
        "negative squared errors or formal rejections of an assumed rho. Uncertainty in "
        "q and its association with D are not quantified. No intervals are shifted or "
        "recomputed, and no significance, coverage, or correct-ordering claim is made. "
        "This analysis does not address mean drift, beta uncertainty, shared fractions, "
        "learned representations, or reference validity.", "",
        "## Replay", "",
        "`uv run --locked python -m latent_art_bench.painter_repeat_covariance_v1 "
        "check --execute-real`", "",
        "The create-once input binding and analysis JSON retain all source/input hashes, "
        "84 per-scene D and q values, every configuration/grid value, all 15 paired "
        "curves, unrounded crossings and implied covariance biases. Primary-D and "
        "review-v2 direct-q values are checked against preserved results. "
        f"Input binding SHA-256: `{result['inputs_sha256']}`.", "",
    ]
    return "\n".join(lines)


def execute(check=False):
    targets = OUT / "analysis.json", OUT / "REPORT.md"
    if not check and any(path.exists() for path in targets):
        raise FileExistsError("preserve existing covariance outputs; use check")
    result = compute_real()
    rendered = report(result)
    if check:
        if result != s.read(targets[0]) or rendered != targets[1].read_text():
            raise ValueError("exact covariance sensitivity replay differs")
        print("Exact primary-D covariance sensitivity replay passed")
    else:
        write_new(targets[0], result)
        write_new(targets[1], rendered)
        print("Primary-D covariance sensitivity saved; original results unchanged")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "analyze", "check"))
    parser.add_argument("--execute-real", action="store_true", help="execute after method review")
    args = parser.parse_args()
    if args.action == "freeze":
        freeze()
    elif not args.execute_real:
        parser.error("real sensitivity outcomes require method review and --execute-real")
    else:
        execute(check=args.action == "check")


if __name__ == "__main__":
    main()
