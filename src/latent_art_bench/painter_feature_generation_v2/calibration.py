"""Known finite-population, joint-endpoint Monte Carlo diagnosis of block inference."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    bindings,
    publish,
    stage_lock,
)
from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_feature_generation_v2.statistics import (
    energy_terms,
    simultaneous_intervals,
)

SELF = Path("src/latent_art_bench/painter_feature_generation_v2/calibration.py")


def evaluate_counts(cross, self_real, pairs, counts, repetitions):
    """Aggregate repeated source states; equivalent to materializing sampled block positions."""
    counts = np.atleast_2d(counts)
    if not np.all(counts.sum(axis=1) == repetitions) or repetitions < 2:
        raise ValueError("counts must encode R block positions")
    quadratic = np.einsum("bi,eij,bj->be", counts, pairs, counts, optimize=True)
    diagonal = counts @ np.diagonal(pairs, axis1=1, axis2=2).T
    return (
        counts @ cross.T / repetitions
        - self_real
        - (quadratic - diagonal) / (repetitions * (repetitions - 1))
    )


def population(scenario: str, rng):
    base = rng.normal(size=(8, 16, 31))
    base += rng.normal(size=(8, 1, 1)) * 0.4
    real, generated = {}, {}
    for i, painter in enumerate(PAINTER_IDS):
        offset = 0 if scenario == "null" else 0.65 * i
        real[painter] = base.reshape(-1, 31) + offset
        generated[painter] = (
            base * (1.6 if scenario == "dispersion" else 1)
            + offset
            + (0.3 if scenario == "shift" else 0)
        )
    generated["artist_free"] = base if scenario == "null" else base + 0.975
    return real, generated


def endpoint_population(real, generated):
    cross, self_real, pairs, labels = [], [], [], []
    for family, section in FAMILIES.items():
        cache = {
            (c, p): energy_terms(x[:, section], generated[c][:, :, section])
            for c in generated
            for p, x in real.items()
        }
        for p in PAINTER_IDS:
            own = cache[p, p]
            comparisons = [("target_fit", None, None)]
            comparisons += [("specificity", q, cache[p, q]) for q in PAINTER_IDS if q != p]
            comparisons += [("control_improvement", "artist_free", cache["artist_free", p])]
            for name, other, term in comparisons:
                cross.append(own.cross_by_block - (term.cross_by_block if term else 0))
                self_real.append(own.real_self - (term.real_self if term else 0))
                pairs.append(
                    own.generated_block_pairs - (term.generated_block_pairs if term else 0)
                )
                labels.append(dict(family=family, painter_id=p, endpoint=name, comparison=other))
    return np.array(cross), np.array(self_real), np.array(pairs), labels


def wilson(successes, total):
    z = 1.959963984540054
    p = successes / total
    center = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * np.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [float(center - half), float(center + half)]


def simulate(*, trials=100, bootstrap_draws=999, seed=20260905) -> dict:
    rng = np.random.Generator(np.random.PCG64(seed))
    scenarios = []
    for scenario in ("null", "shift", "dispersion"):
        real, generated = population(scenario, rng)
        cross, real_self, pairs, labels = endpoint_population(real, generated)
        truth = cross.mean(axis=1) - real_self - pairs.mean(axis=(1, 2))
        biases, valid_coverage, full_coverage, zero_counts = [], [], [], []
        for _ in range(trials):
            indices = rng.integers(0, 8, size=25)
            counts = np.bincount(indices, minlength=8)
            point = evaluate_counts(cross, real_self, pairs, counts, 25)[0]
            bootstrap = rng.multinomial(25, np.full(25, 1 / 25), size=bootstrap_draws)
            aggregate = bootstrap @ np.eye(8, dtype=int)[indices]
            draws = evaluate_counts(cross, real_self, pairs, aggregate, 25)
            intervals, _ = simultaneous_intervals(point, draws)
            valid = [i for i, row in enumerate(intervals) if row["lower"] is not None]
            covered = bool(valid) and all(
                intervals[i]["lower"] <= truth[i] <= intervals[i]["upper"] for i in valid
            )
            valid_coverage.append(covered)
            full_coverage.append(covered and len(valid) == 60)
            zero_counts.append(60 - len(valid))
            biases.append(point - truth)
        bias = np.mean(biases, axis=0)
        scenarios.append(
            dict(
                scenario=scenario,
                trials=trials,
                joint_coverage_nondegenerate_endpoints=float(np.mean(valid_coverage)),
                coverage_mc_wilson_95=wilson(sum(valid_coverage), trials),
                trials_with_all_60_intervals_covering_truth=sum(full_coverage),
                zero_variance_endpoint_counts=sorted(set(zero_counts)),
                max_absolute_mc_bias=float(np.max(np.abs(bias))),
                endpoint_truth_and_mc_bias=[
                    dict(label, truth=float(t), mc_bias=float(b))
                    for label, t, b in zip(labels, truth, bias)
                ],
            )
        )
        print(
            f"synthetic calibration {scenario}: "
            f"joint coverage among nondegenerate endpoints {np.mean(valid_coverage):.3f}",
            flush=True,
        )
    return dict(
        seed=seed,
        trials_per_scenario=trials,
        bootstrap_draws_per_trial=bootstrap_draws,
        repetitions=25,
        templates=16,
        coordinates=31,
        source_block_states=8,
        scenarios=scenarios,
        scope="synthetic numerical calibration, not empirical painter evidence",
        interpretation="Coverage is a Monte Carlo diagnostic, not a guarantee. Zero-variance "
        "endpoints have no inferential interval. Near-null behavior can be poor.",
    )


def run(root: Path, run_id: str) -> dict:
    from .artifacts import identifier

    identifier(run_id)
    output = root / MANIFESTS / run_id
    with stage_lock(root / WORKSPACE / run_id / ".calibration.writer.lock"):
        if output.exists():
            raise FileExistsError("calibration already prepared; retain its prior evidence")
        paths = [
            SELF,
            Path("studies/painter_feature_generation_v2/PROTOCOL_1.2.md"),
            Path("src/latent_art_bench/painter_feature_generation_v2/statistics.py"),
            Path("src/latent_art_bench/painter_feature_generation_v2/features.py"),
            Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
            Path("src/latent_art_bench/io.py"),
            Path("uv.lock"),
        ]
        for path in paths:
            blob = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=root, capture_output=True)
            if blob.returncode or blob.stdout != (root / path).read_bytes():
                raise ValueError(f"commit exact calibration input first: {path}")
        frozen = dict(
            inputs=bindings(root, paths),
            recorded_git_commit=subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip(),
            prepared_at_utc=utc_now().isoformat(),
            seed=20260905,
            trials=100,
            bootstrap_draws=999,
        )
        publish(output / "calibration_freeze.json", frozen)
        result = simulate()
        result["calibration_freeze_sha256"] = hash_file(output / "calibration_freeze.json")
        result["completed_at_utc"] = utc_now().isoformat()
        publish(output / "calibration.json", result)
        return result
