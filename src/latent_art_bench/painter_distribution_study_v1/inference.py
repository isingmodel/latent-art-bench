"""Weighted finite-reference prompt contrasts and prospective conditional-null checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial.distance import cdist

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_exploration_v1.statistics import matrix
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, publish
from latent_art_bench.painter_prompt_study_v1.calibration import wilson
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_prompt_study_v1.randomization import (
    _exact_absolute_tail,
    holm,
    randomization_pvalue,
)

from .statistics import probability_weights

NAMESPACE = "painter_distribution_study_v1"
DIRECTORY = Path("data/manifests") / NAMESPACE / "pdsv1-inference-20260906"
CONTRACT = Path("studies") / NAMESPACE / "INFERENCE.md"
DRAW_COUNT = 99999
ENDPOINTS = 8
SCENARIOS = ("constant", "content_weights", "window_drift", "rare_large")


def paired_contributions(reference, before, after, reference_weights=None, pair_weights=None):
    """Coefficients sum to weighted V-energy(after,R) minus weighted V-energy(before,R).

    The same reference and matched-pair weights are used in both conditions. Under
    complementary within-pair swaps the exact contrast is sign @ coefficients.
    All within-set terms are retained; this is not a mean-vector distance.
    """
    real, first, second = map(matrix, (reference, before, after))
    if first.shape != second.shape or real.shape[1] != first.shape[1]:
        raise ValueError("paired matrices must have matching dimensions")
    a = probability_weights(len(real), reference_weights)
    b = probability_weights(len(first), pair_weights)
    n = len(first)
    pooled = np.concatenate((first, second))
    cross = cdist(pooled, real) @ a
    within = cdist(pooled, pooled) @ np.concatenate((b, b))
    return b * (2 * (cross[n:] - cross[:n]) - (within[n:] - within[:n]))


def test_contrast(reference, before, after, *, seed, reference_weights=None, pair_weights=None):
    values = paired_contributions(reference, before, after, reference_weights, pair_weights)
    return randomization_pvalue(values, seed=seed, draws=DRAW_COUNT), values


def magnitude_weights(size, scenario):
    index = np.arange(size)
    if scenario == "constant":
        return np.ones(size, dtype=int)
    if scenario == "content_weights":
        return 1 + (index // 3) % 4
    if scenario == "window_drift":
        return 1 + index % 8
    if scenario == "rare_large":
        weights = np.ones(size, dtype=int)
        weights[-1] = 32
        return weights
    raise ValueError("unknown qualification scenario")


def synthetic_cell(rng, size, scenario, coupled, trials, positive=0.5, invalid_window_signs=False):
    weights = magnitude_weights(size, scenario)
    groups = 1 if coupled else ENDPOINTS
    if invalid_window_signs:
        window_weights = np.bincount(np.arange(size) % 8, weights=weights).astype(int)
        signs = 2 * rng.binomial(1, positive, size=(trials, groups, 8)) - 1
        totals = np.einsum("tgw,w->tg", signs, window_weights)
    else:
        totals = np.zeros((trials, groups), dtype=int)
        for weight in np.unique(weights):
            count = int(np.count_nonzero(weights == weight))
            totals += int(weight) * (
                2 * rng.binomial(count, positive, size=(trials, groups)) - count
            )
    tail = _exact_absolute_tail(weights)[np.abs(totals)]
    # Conditional on a statistic, B independent random sign draws have exactly
    # Binomial(B, p_exact) exceedances. No Gaussian tail approximation is used.
    pvalues = (1 + rng.binomial(DRAW_COUNT, tail)) / (DRAW_COUNT + 1)
    if coupled:
        pvalues = np.repeat(pvalues, ENDPOINTS, axis=1)
    rejected = np.array([holm(p) <= 0.05 for p in pvalues])
    count = int(rejected.any(axis=1).sum())
    return dict(
        pairs=size,
        scenario=scenario,
        endpoint_dependence="shared" if coupled else "independent",
        trials=trials,
        family_size=ENDPOINTS,
        family_rejections=count,
        rejection_rate=count / trials,
        wilson_95=wilson(count, trials),
        mean_rejected_endpoints=float(rejected.sum(axis=1).mean()),
        positive_sign_probability=positive,
        invalid_window_signs=invalid_window_signs,
    )


def simulate(seed, trials=10000):
    rng = np.random.default_rng(seed)
    null = [
        synthetic_cell(rng, size, scenario, coupled, trials)
        for size in (24, 48, 72)
        for scenario in SCENARIOS
        for coupled in (False, True)
    ]
    power = [
        synthetic_cell(rng, 72, "constant", False, trials, positive=p) for p in (0.55, 0.65, 0.75)
    ]
    invalid = synthetic_cell(rng, 72, "constant", False, trials, invalid_window_signs=True)
    return dict(
        seed=seed,
        trials=trials,
        monte_carlo_draws=DRAW_COUNT,
        null_cells=null,
        hypothetical_sign_bias_power=power,
        invalid_window_synchronized_assignments=invalid,
        qualified=all(row["wilson_95"][1] <= 0.065 for row in null),
        scope="Conditional sharp joint null of no prompt effect on availability and "
        "features, with no interference; not an absolute distribution-equality test, "
        "population confidence interval or proof of actual service assumptions.",
    )


def source_paths():
    return [
        CONTRACT,
        Path("src/latent_art_bench") / NAMESPACE / "inference.py",
        Path("src/latent_art_bench") / NAMESPACE / "statistics.py",
        Path("tests") / NAMESPACE / "test_inference.py",
        Path("src/latent_art_bench/painter_prompt_study_v1/randomization.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/calibration.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/statistics.py"),
        Path("src/latent_art_bench/painter_prompt_study_v1/common.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/statistics.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/features.py"),
        Path("src/latent_art_bench/painter_distribution_exploration_v1/statistics.py"),
        Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
        Path("src/latent_art_bench/io.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]


def prepare(root):
    paths = source_paths()
    commit = committed(root, paths)
    freeze = dict(
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        development_seed=2026090601,
        validation_seed=2026090701,
        trials_per_cell=10000,
        maximum_wilson_upper=0.065,
    )
    publish(root / DIRECTORY / "freeze.json", freeze)
    return freeze


def build(root):
    from latent_art_bench.painter_feature_generation_v2.artifacts import verify_bindings

    freeze = read_json(root / DIRECTORY / "freeze.json")
    verify_bindings(root, freeze["inputs"])
    committed(root, [DIRECTORY / "freeze.json"])
    for phase in ("development", "validation"):
        result = simulate(freeze[phase + "_seed"], freeze["trials_per_cell"])
        publish(root / DIRECTORY / (phase + ".json"), result)
    decision = dict(
        qualified=all(
            read_json(root / DIRECTORY / (p + ".json"))["qualified"]
            for p in ("development", "validation")
        ),
        multiplicity="Holm 8",
        monte_carlo_draws=DRAW_COUNT,
        reference_scope="conditional on the fixed finite reference and weights",
        absolute_distance_confidence_intervals_qualified=False,
        population_style_equivalence_qualified=False,
        image_level_power_established=False,
        evidence=bindings(
            root, [DIRECTORY / f for f in ("freeze.json", "development.json", "validation.json")]
        ),
    )
    publish(root / DIRECTORY / "decision.json", decision)
    return decision


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "check"))
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare(root)
    elif args.command == "build":
        result = build(root)
    else:
        freeze = read_json(root / DIRECTORY / "freeze.json")
        for phase in ("development", "validation"):
            if simulate(freeze[phase + "_seed"], freeze["trials_per_cell"]) != read_json(
                root / DIRECTORY / (phase + ".json")
            ):
                raise ValueError("qualification replay differs")
        result = read_json(root / DIRECTORY / "decision.json")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
