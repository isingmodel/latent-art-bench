"""Bounded finite-support qualification, not a guarantee about service coverage.

The only interval candidate is a paired, scene-stratified delete-one jackknife
with a deliberately large t critical value. Finite-support laws have exact
finite-R V-energy truths. No new image outcomes, map fitting, scene bootstrap,
map permutation, interval fallback or live transport is implemented here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy
from scipy.spatial.distance import cdist
from scipy.stats import beta, t

CLASSES = ("water", "built", "land")
MASSES = {"water": 3 / 32, "built": 11 / 32, "land": 18 / 32}
SHAPES = ("gaussian_shaped", "t5_shaped", "lognormal_shaped")
MEANS = ("T1", "midpoint", "T2")
REGIMES = ("baseline", "high_positive", "low_negative")
REPEATS = (4, 6, 8)
SUPPORT_SIZE, TRIALS, BATCH_SIZE = 64, 10000, 128
SUPPORT_SEED, TRIAL_SEED = 2026091061, 2026091062
MC_ALPHA, COVERAGE_MIN = 0.05 / 81, 0.94
WIDTH_LIMITS = np.array([0.25, 1.0])
INPUT_PATH = Path("data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json")
ANALYSIS_PATH = INPUT_PATH.with_name("analysis.json")
INPUT_HASH = "eeb3890268a85885f372bdb494e29ab558c271749667fb7e264a7e30881733de"
ANALYSIS_HASH = "f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324"
STUDY_PATH = Path("studies/painter_map_validation_v1")
OUTPUT_PATH = STUDY_PATH / "pmvqv1-20260910"
SOURCE_PATH = Path("src/latent_art_bench/painter_map_validation_v1/precision.py")
BINDINGS = (
    SOURCE_PATH,
    SOURCE_PATH.with_name("__init__.py"),
    Path("src/latent_art_bench/__init__.py"),
    Path("tests/painter_map_validation_v1/test_precision.py"),
    STUDY_PATH / "PRECISION_PROTOCOL.md",
    STUDY_PATH / "DESIGN.md",
    INPUT_PATH,
    ANALYSIS_PATH,
    INPUT_PATH.with_name("freeze.json"),
    INPUT_PATH.with_name("receipt.json"),
    Path("pyproject.toml"),
    Path("uv.lock"),
)


def finite(value, shape=None):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu" or not np.isfinite(raw).all():
        raise ValueError("finite real numeric arrays required")
    result = raw.astype(float)
    if shape is not None and result.shape != shape:
        raise ValueError(f"expected shape {shape}")
    return result


def integer(value, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError("integer required")
    if value < minimum:
        raise ValueError(f"integer must be >= {minimum}")
    return int(value)


def weights(value, count):
    result = finite(value, (count,))
    if np.any(result <= 0) or not np.isclose(result.sum(), 1, rtol=0, atol=1e-12):
        raise ValueError("positive normalized weights required")
    return result


def maps(free, fitted):
    d = free.shape[-1]
    fm, nm = (finite(fitted[k], (d,)) for k in ("free_mean", "named_mean"))
    a = finite(fitted["scale"])
    if a.shape or a <= 0:
        raise ValueError("positive scalar required")
    return free + nm - fm, nm + float(a) * (free - fm)


@dataclass
class Tables:
    """Uniform joint support; cached distances and within-scene Q kernels."""

    free: np.ndarray
    named: np.ndarray
    w: np.ndarray
    cross: np.ndarray
    distances: np.ndarray
    qkernel: np.ndarray
    contraction: float


def support_tables(free, named, reference, scene_weights, fitted, reference_weights=None):
    free, named, reference = map(finite, (free, named, reference))
    if free.ndim != 3 or named.shape != free.shape or min(free.shape) < 2:
        raise ValueError("paired J by S by D supports, all dimensions >=2, required")
    j, s, d = free.shape
    if reference.ndim != 2 or len(reference) < 1 or reference.shape[1] != d:
        raise ValueError("matching nonempty reference required")
    w = weights(scene_weights, j)
    p = weights(
        np.full(len(reference), 1 / len(reference))
        if reference_weights is None
        else reference_weights,
        len(reference),
    )
    t1, t2 = maps(free, fitted)
    cross = (
        2 * p @ (cdist(reference, t2.reshape(-1, d)) - cdist(reference, t1.reshape(-1, d)))
    ).reshape(j, s)
    distances = cdist(free.reshape(-1, d), free.reshape(-1, d))
    e1, e2 = named - t1, named - t2
    qkernel = np.einsum("jsd,jtd->jst", e2, e2) - np.einsum("jsd,jtd->jst", e1, e1)
    for value in (cross, distances, qkernel):
        finite(value)
    return Tables(free, named, w, cross, distances, qkernel, 1 - float(fitted["scale"]))


def exact_truth(table, repeats):
    """Exact uniform-support finite-R V target, Q mean and sampling variance."""
    r = integer(repeats, 2)
    j, s, _ = table.free.shape
    d = table.distances.reshape(j, s, j, s).mean(axis=(1, 3))
    energy = table.w @ table.cross.mean(1) + table.contraction * (
        table.w @ d @ table.w - np.sum(table.w**2 * np.diag(d)) / r
    )
    h = table.qkernel
    qmeans = h.mean(axis=(1, 2))
    zeta1 = np.mean((h.mean(2) - qmeans[:, None]) ** 2, axis=1)
    zeta2 = np.mean((h - qmeans[:, None, None]) ** 2, axis=(1, 2))
    qvariance = np.sum(table.w**2 * (4 * (r - 2) * zeta1 + 2 * zeta2) / (r * (r - 1)))
    return dict(
        estimate=[float(energy), float(table.w @ qmeans)], q_sampling_variance=float(qvariance)
    )


def statistics(table, draws):
    """Batch point estimates and exact delete-one values, not refitted maps.

    Distances are computed once per support. Each deletion changes only one
    scene's repeat weights; the quadratic weight update includes its cross term.
    """
    raw = np.asarray(draws)
    j, s, _ = table.free.shape
    if raw.dtype.kind not in "iu" or raw.ndim != 3 or raw.shape[1] != j:
        raise ValueError("integer batch by scene by repeat support indices required")
    b, _, r = raw.shape
    if b < 1 or r < 3 or np.any(raw < 0) or np.any(raw >= s):
        raise ValueError("nonempty batches, R>=3 and in-range support indices required")
    idx = (raw + np.arange(j)[None, :, None] * s).reshape(b, j * r)
    a = table.cross[np.arange(j)[None, :, None], raw]
    d = table.distances[idx[:, :, None], idx[:, None, :]]
    v = np.repeat(table.w / r, r)
    g = (d @ v).reshape(b, j, r)
    energy = np.sum(a * table.w[None, :, None] / r, axis=(1, 2))
    energy += table.contraction * np.sum(g * table.w[None, :, None] / r, axis=(1, 2))
    blocks = d.reshape(b, j, r, j, r)[:, np.arange(j), :, np.arange(j), :]
    # Advanced indexing moves the scene axis in front of the batch axis.
    blocks = np.moveaxis(blocks, 0, 1)
    rowmean = blocks.mean(3)
    factor = table.w[None, :, None] / (r - 1)
    edelete = energy[:, None, None] + factor * (a.mean(2, keepdims=True) - a)
    edelete += table.contraction * (
        2 * factor * (g.mean(2, keepdims=True) - g)
        + factor**2 * (rowmean.mean(2, keepdims=True) - 2 * rowmean)
    )
    h = table.qkernel[np.arange(j)[None, :, None, None], raw[:, :, :, None], raw[:, :, None, :]]
    rowoff = h.sum(3) - np.diagonal(h, axis1=2, axis2=3)
    total = rowoff.sum(2)
    qscene = total / (r * (r - 1))
    q = qscene @ table.w
    qdelete = q[:, None, None] + table.w[None, :, None] * (
        (total[:, :, None] - 2 * rowoff) / ((r - 1) * (r - 2)) - qscene[:, :, None]
    )
    deleted = np.stack((edelete, qdelete), axis=3)
    variance = (r - 1) / r * np.square(deleted - deleted.mean(2, keepdims=True)).sum((1, 2))
    estimate = np.stack((energy, q), axis=1)
    return dict(estimate=estimate, variance=variance, deleted=deleted)


def intervals(estimate, variance, repeats):
    """One fixed approximation. Nonpositive variance makes the family unavailable."""
    raw = [np.asarray(value) for value in (estimate, variance)]
    if any(value.dtype.kind not in "fiu" for value in raw):
        raise ValueError("numeric interval arrays required")
    estimate, variance = (value.astype(float) for value in raw)
    if estimate.ndim != 2 or estimate.shape[1] != 2 or variance.shape != estimate.shape:
        raise ValueError("batch by two estimate/variance arrays required")
    r = integer(repeats, 3)
    available = (
        np.isfinite(estimate).all(1) & np.isfinite(variance).all(1) & np.all(variance > 0, axis=1)
    )
    half = np.full_like(variance, np.inf)
    half[available] = t.ppf(0.9875, r - 1) * np.sqrt(variance[available])
    return half, available


def coverage_lower(successes, trials):
    """One-sided Clopper-Pearson bound, Bonferroni across all 81 planned cells."""
    n, k = integer(trials), integer(successes, 0)
    if k > n:
        raise ValueError("successes exceed trials")
    return 0.0 if k == 0 else float(beta.ppf(MC_ALPHA, k, n - k + 1))


def load_proxy(root):
    """Read only fixed historical vectors; never read proposed/new scene outputs."""
    values = []
    for path, expected in ((INPUT_PATH, INPUT_HASH), (ANALYSIS_PATH, ANALYSIS_HASH)):
        data = (Path(root) / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"sealed numerical input SHA256 mismatch: {path}")
        values.append(json.loads(data))
    inputs, analysis = values
    cell = inputs["original"]["primary512"]["flux_2_max"]["paul_cezanne"]
    old_ids = [f"{c}{i:02d}" for c in ("built", "land", "water") for i in range(1, 9)]
    if (
        cell["scene_ids"] != old_ids
        or cell["repeat_ids"] != [0, 1, 2]
        or cell["classes"] != [c for c in ("built", "land", "water") for _ in range(8)]
        or inputs["targets"]["paul_cezanne"] != MASSES
    ):
        raise ValueError("historical scene/weight/repeat identities differ")
    free, named = (finite(cell[k], (24, 3, 31)) for k in ("free", "named"))
    selected_ids = [f"{c}{i:02d}" for c in CLASSES for i in range(1, 5)]
    selected = [old_ids.index(s) for s in selected_ids]
    old_w = np.array([MASSES[c] / 8 for c in cell["classes"]])
    covariance = []
    for arm in (free, named):
        residual = arm - arm.mean(1, keepdims=True)
        covariance.append(np.einsum("j,jrd,jre->de", old_w, residual, residual) / 2)
    matched = [
        row
        for row in analysis["transfer"]
        if row["pipeline"] == "primary512"
        and row["view"] == "all31"
        and row["painter"] == "paul_cezanne"
    ]
    if len(matched) != 1:
        raise ValueError("unique unchanged full-cohort map required")
    fitted = matched[0]["fitted"]
    reference = inputs["reference"]["primary512"]["paul_cezanne"]
    if len(reference["ids"]) != 32 or len(set(reference["ids"])) != 32:
        raise ValueError("32 unique reference works required")
    scaler = inputs["scalers"]["primary512"]
    if scaler["status"] != "available":
        raise ValueError("fixed scaler unavailable")
    finite(scaler["scaler"]["center"], (31,))
    if np.any(finite(scaler["scaler"]["scale"], (31,)) <= 0):
        raise ValueError("positive fixed scaler required")
    proxy = dict(
        scene_ids=selected_ids,
        free_mean=free[selected].mean(1),
        cov_free=covariance[0],
        cov_named=covariance[1],
        fitted=fitted,
        reference=finite(reference["values"], (32, 31)),
        scene_weights=np.repeat([MASSES[c] / 4 for c in CLASSES], 4),
    )
    maps(proxy["free_mean"], fitted)
    return proxy


def covariance_root(value):
    """Symmetric PSD square root; only floating-point negative eigenvalues clipped."""
    covariance = finite(value)
    if covariance.ndim != 2 or covariance.shape[0] != covariance.shape[1]:
        raise ValueError("square covariance required")
    if not np.allclose(covariance, covariance.T, atol=1e-12, rtol=1e-12):
        raise ValueError("symmetric covariance required")
    eigenvalues, vectors = np.linalg.eigh((covariance + covariance.T) / 2)
    tolerance = 1e-12 * max(1.0, float(np.max(np.abs(eigenvalues))))
    if eigenvalues.min() < -tolerance:
        raise ValueError("positive semidefinite covariance required")
    return (vectors * np.sqrt(np.maximum(eigenvalues, 0))) @ vectors.T


def whiten_support(raw):
    """Center and whiten one finite support using its population covariance."""
    raw = finite(raw)
    centered = raw - raw.mean(0)
    covariance = centered.T @ centered / len(centered)
    eigenvalues, vectors = np.linalg.eigh(covariance)
    if eigenvalues.min() <= 1e-12 * max(1.0, float(eigenvalues.max())):
        raise ValueError("finite support covariance cannot be whitened")
    return centered @ ((vectors / np.sqrt(eigenvalues)) @ vectors.T)


def codebook(shape_index, dimensions=31):
    """Fixed uniform support; shaped draws are centered/scaled within this support."""
    if shape_index not in range(3):
        raise ValueError("unknown noise shape")
    d = integer(dimensions, 2)
    rng = np.random.default_rng(np.random.SeedSequence([SUPPORT_SEED, shape_index]))
    if shape_index == 1:
        raw = rng.standard_t(5, size=(SUPPORT_SIZE, 2 * d)) * np.sqrt(3 / 5)
    else:
        raw = rng.standard_normal((SUPPORT_SIZE, 2 * d))
        if shape_index == 2:
            raw = np.exp(raw)
    return whiten_support(raw[:, :d]), whiten_support(raw[:, d:])


def scenario(proxy, shape_index, mean_index, regime_index):
    """Construct one of 27 fixed hypothetical laws, not a fitted new-scene law."""
    if mean_index not in range(3) or regime_index not in range(3):
        raise ValueError("unknown scenario")
    mu = finite(proxy["free_mean"])
    if mu.shape != (12, 31):
        raise ValueError("the formal proxy uses exactly twelve 31-feature means")
    u, v = codebook(shape_index)
    mult, rho = ((1.0, 0.0), (2.0, 0.75), (0.5, -0.5))[regime_index]
    eta = rho * u + np.sqrt(1 - rho**2) * v
    eta = whiten_support(eta)
    hetero = np.ones(12)
    if regime_index:
        hetero = np.repeat([0.5, 1.0, 2.0], 4)
        hetero /= np.sqrt(proxy["scene_weights"] @ hetero**2)
    t1, t2 = maps(mu, proxy["fitted"])
    alpha = (0.0, 0.5, 1.0)[mean_index]
    nmean = (1 - alpha) * t1 + alpha * t2
    scale = mult * hetero[:, None, None]
    free = mu[:, None, :] + scale * (u @ covariance_root(proxy["cov_free"]).T)
    named = nmean[:, None, :] + scale * (eta @ covariance_root(proxy["cov_named"]).T)
    return support_tables(free, named, proxy["reference"], proxy["scene_weights"], proxy["fitted"])


def finite_summary(values, variance=False):
    """Do not serialize overflow or silently trim troublesome numerical trials."""
    with np.errstate(over="ignore", invalid="ignore"):
        summary = values.var(0, ddof=1) if variance else values.mean(0)
    return summary.tolist() if np.isfinite(summary).all() else None


def simulate_cell(table, repeats, trials, seed):
    """Small calls support artificial unit checks; build alone records qualification."""
    r, n = integer(repeats, 3), integer(trials, 2)
    rng = np.random.default_rng(seed)
    truth = exact_truth(table, r)
    estimates, widths, availability = [], [], []
    for start in range(0, n, BATCH_SIZE):
        draws = rng.integers(
            table.free.shape[1], size=(min(BATCH_SIZE, n - start), len(table.w), r)
        )
        result = statistics(table, draws)
        half, available = intervals(result["estimate"], result["variance"], r)
        estimates.append(result["estimate"])
        widths.append(half)
        availability.append(available)
    estimates, widths = np.concatenate(estimates), np.concatenate(widths)
    available = np.concatenate(availability)
    hits = available & np.all(np.abs(estimates - truth["estimate"]) <= widths, axis=1)
    k = int(hits.sum())
    medians = np.median(widths, axis=0)
    return dict(
        R=r,
        outputs=24 * r,
        trials=n,
        truth=truth,
        joint_covered=k,
        joint_coverage=k / n,
        coverage_lower=coverage_lower(k, n),
        unavailable=int((~available).sum()),
        median_half_width=[float(x) if np.isfinite(x) else None for x in medians],
        nonfinite_estimate_trials=int((~np.isfinite(estimates).all(1)).sum()),
        empirical_mean=finite_summary(estimates),
        empirical_variance=finite_summary(estimates, variance=True),
        negative_estimate_counts=(estimates < 0).sum(0).tolist(),
    )


def allocation_decision(records):
    """Coverage everywhere; widths only in nine baseline cells; no fallback."""
    if len(records) != 81:
        raise ValueError("all 81 allocation/scenario records required")
    expected = {(r, sh, m, rg) for r in REPEATS for sh in SHAPES for m in MEANS for rg in REGIMES}
    actual = {(v["R"], v["shape"], v["mean"], v["regime"]) for v in records}
    if actual != expected or any(v["trials"] != TRIALS for v in records):
        raise ValueError("complete fixed allocation/scenario/trial grid required")
    for row in records:
        if not isinstance(row["median_half_width"], list) or len(row["median_half_width"]) != 2:
            raise ValueError("exactly two half-width entries required")
        if not np.isfinite(row["coverage_lower"]) or not 0 <= row["coverage_lower"] <= 1:
            raise ValueError("finite probability coverage bound required")
    summaries = []
    for r in REPEATS:
        rows = [v for v in records if v["R"] == r]
        coverage = all(v["coverage_lower"] >= COVERAGE_MIN for v in rows)
        width = all(
            all(
                x is not None and 0 <= x <= limit
                for x, limit in zip(v["median_half_width"], WIDTH_LIMITS)
            )
            for v in rows
            if v["regime"] == "baseline"
        )
        summaries.append(
            dict(
                R=r,
                outputs=24 * r,
                coverage_pass=coverage,
                baseline_width_pass=width,
                qualified=coverage and width,
            )
        )
    selected = next((v["R"] for v in summaries if v["qualified"]), None)
    return dict(
        allocations=summaries,
        selected_R=selected,
        selected_outputs=None if selected is None else 24 * selected,
        decision="stop_inferential_proposal" if selected is None else "qualified_proxy_only",
    )


def qualify(proxy):
    """The fixed formal grid; callers must establish committed source beforehand."""
    records = []
    for sh in range(3):
        for m in range(3):
            for rg in range(3):
                table = scenario(proxy, sh, m, rg)
                support_hash = hashlib.sha256(
                    table.free.astype("<f8").tobytes() + table.named.astype("<f8").tobytes()
                ).hexdigest()
                for r in REPEATS:
                    seed = [TRIAL_SEED, sh, m, rg, r]
                    row = simulate_cell(table, r, TRIALS, np.random.SeedSequence(seed))
                    row.update(
                        shape=SHAPES[sh],
                        mean=MEANS[m],
                        regime=REGIMES[rg],
                        trial_seed=seed,
                        support_sha256=support_hash,
                    )
                    records.append(row)
    return dict(records=records, **allocation_decision(records))


def bindings_at_head(root):
    root = Path(root)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, check=True, text=True
    ).stdout.strip()
    records = []
    for relative in sorted(BINDINGS):
        path = root / relative
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("portable binding paths required")
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("symlink bindings forbidden")
        data = path.read_bytes()
        for revision in (f"{commit}:{relative.as_posix()}", f":{relative.as_posix()}"):
            blob = subprocess.run(["git", "show", revision], cwd=root, capture_output=True)
            if blob.returncode or blob.stdout != data:
                raise ValueError(f"commit clean source/input before qualification: {relative}")
        records.append(dict(path=relative.as_posix(), sha256=hashlib.sha256(data).hexdigest()))
    return commit, records


def report(value):
    result = value["qualification"]
    lines = [
        "# Fixed-map offline precision qualification",
        "",
        "Finite-support historical proxies; no new image outcomes or service-coverage guarantee.",
        "Maintainer-run LLM design/implementation/review; not independent human investigators.",
        f"Source commit: `{value['source_commit']}`.",
        "Coverage gates all 27 laws; width gates only nine baseline laws per allocation.",
        "Unavailable intervals count as coverage misses and infinite widths.",
        f"Decision: **{result['decision']}**; selected outputs: {result['selected_outputs']}.",
        "",
        "| R | Noise | Mean | Regime | Joint coverage | CP lower | Median E/Q half-width |"
        " Unavailable |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["records"]:
        lines.append(
            f"| {row['R']} | {row['shape']} | {row['mean']} | {row['regime']} | "
            f"{row['joint_coverage']:.5f} | {row['coverage_lower']:.5f} | "
            f"{row['median_half_width']} | {row['unavailable']} |"
        )
    lines += [
        "",
        "Passing concerns only these discrete proxy laws and fixed numerical tolerances;",
        "it opens no generation gate and guarantees neither actual precision nor coverage.",
        "The V-energy target is finite-R; Q targets conditional scene-mean mismatch.",
        "No reference, scene-population, latent-style or perceptual uncertainty is included.",
        "",
    ]
    return "\n".join(lines)


def build(root):
    """One create-once formal record, requiring clean committed bound bytes."""
    root = Path(root).resolve()
    output = root / OUTPUT_PATH
    if output.exists() or output.is_symlink():
        raise ValueError("qualification output directory is create-once")
    commit, bindings = bindings_at_head(root)
    proxy = load_proxy(root)
    environment = dict(
        python=platform.python_version(),
        numpy=np.__version__,
        scipy=scipy.__version__,
        platform=platform.platform(),
    )
    output.mkdir(parents=True, exist_ok=False)
    run = dict(
        schema="painter-map-precision-run/1",
        source_commit=commit,
        source_bindings=bindings,
        environment=environment,
    )
    with (output / "RUN.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(run, indent=2, sort_keys=True) + "\n")
    value = dict(run, proxy_scene_ids=proxy["scene_ids"], qualification=qualify(proxy))
    if bindings_at_head(root) != (commit, bindings):
        raise ValueError("source changed during formal qualification; preserve partial record")
    for name, content in (
        ("precision.json", json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"),
        ("PRECISION.md", report(value)),
    ):
        with (output / name).open("x", encoding="utf-8") as handle:
            handle.write(content)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    value = build(args.root)
    print(
        json.dumps(
            dict(
                output=str(OUTPUT_PATH),
                **{k: value["qualification"][k] for k in ("decision", "selected_outputs")},
            )
        )
    )


if __name__ == "__main__":
    main()
