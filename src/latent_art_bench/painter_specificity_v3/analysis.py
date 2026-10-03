"""Prespecified v3 analysis, fixed before collection (see the v3 PROTOCOL.md).

Every per-group quantity is the four-painter quantity of the paper, computed by the paper's own
functions on a six-arm slice (free, generic, four names). Only the two cross-group tests and the
drift check are new:

* H1, closeness: the century group's shared fraction minus the Hudson River School's, paired
  by scene resampling, averaged over configurations.
* H2, dose-response: a Mantel test across the 28 pairs of the eight new painters, of name
  distance against reference distance, with an exact permutation of painter labels.
* Drift: the September (``psv2-20260911``) free and generic outputs against the new ones,
  whose payloads are identical.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import stats

from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench.painter_specificity_v1.analysis import geometry
from latent_art_bench.painter_tmlr_diagnostics_v1 import corrected_h, decomposition, xrep
from latent_art_bench.painter_tmlr_diagnostics_v5 import alignment, held_out, scene_metrics, student

SEED = 20261003
DRAWS = 5000
MINIMUM_SCENES = 12


def group_summary(x: np.ndarray, means: np.ndarray) -> dict:
    """One configuration, one group. ``x``: (scenes, 2, 6 arms, p); ``means``: (4, p)."""
    dec = decomposition(x, means)
    beta, q, error = scene_metrics(x, means)
    geo = geometry(x[:, :, 2:], [m[None] for m in means])
    return dict(
        H=dec["H"], N=dec["N"], B=dec["B"],
        shared_fraction=dec["shared_fraction"],
        faithful_shared_fraction=dec["faithful_shared_fraction"],
        exact_shared_fraction=dec["N"] / (dec["N"] + dec["H"]),
        B_over_H=dec["B_over_H"],
        beta=float(np.mean(beta)), beta_ci95=student(beta),
        Q=float(np.mean(q)),
        D=float(np.mean(error)), D_ci95=student(error),
        alignment_ratio=alignment(beta, q),
        D_held=held_out(beta, q),
        along_pattern=float(geo["amplitude_error"].mean()),
        off_pattern=float(geo["off_axis_error"].mean()),
        centroid_gain=dec["centroid_gain"],
        centroid_gain_shared_fraction=dec["centroid_gain_shared_fraction"],
    )


def shared_fraction(x: np.ndarray) -> float:
    """N/(N+B) of the paper, from the scene-averaged arms of one six-arm slice."""
    z = x.mean(axis=0)
    named = z[:, 2:]
    c = named.mean(axis=1) - z[:, 1]
    e = named - named.mean(axis=1, keepdims=True)
    n = 4 * xrep(c, c)
    b = sum(xrep(e[:, a], e[:, a]) for a in range(4))
    return n / (n + b)


def closeness_test(x: np.ndarray, arms: dict, draws: int = DRAWS, seed: int = SEED) -> dict:
    """H1. ``x``: (configurations, scenes, 2, arms, p). Century minus Hudson shared fraction."""
    configs, scenes = x.shape[:2]
    observed = np.array([shared_fraction(x[m][:, :, arms["century"]])
                         - shared_fraction(x[m][:, :, arms["hudson"]]) for m in range(configs)])
    rng = np.random.default_rng(seed)
    boot = np.empty((draws, configs))
    for i in range(draws):
        idx = rng.integers(0, scenes, scenes)
        for m in range(configs):
            boot[i, m] = (shared_fraction(x[m][idx][:, :, arms["century"]])
                          - shared_fraction(x[m][idx][:, :, arms["hudson"]]))
    pooled = boot.mean(axis=1)
    alpha = 0.05 / configs
    return dict(
        difference_by_configuration=observed.tolist(),
        pooled_difference=float(observed.mean()),
        pooled_ci95=np.percentile(pooled, [2.5, 97.5]).tolist(),
        simultaneous_ci_by_configuration=np.percentile(
            boot, [100 * alpha / 2, 100 * (1 - alpha / 2)], axis=0).T.tolist(),
        supported=bool(np.percentile(pooled, 97.5) < 0),
        draws=draws, seed=seed,
    )


def pair_matrices(x: np.ndarray, means: np.ndarray,
                  noise: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Reference and cross-repeat name squared distances for every painter pair.

    ``x``: (scenes, 2, K arms of names only, p); ``means``: (K, p). ``noise``, if given, is each
    painter's tr(S)/n, the expected inflation of a squared distance from a finite panel; it is
    subtracted so that small panels do not look farther apart than they are.
    """
    k = means.shape[0]
    noise = np.zeros(k) if noise is None else np.asarray(noise, dtype=float)
    z = x.mean(axis=0)  # (2, K, p): scene-averaged, per repeat
    reference, names = np.zeros((k, k)), np.zeros((k, k))
    for a, b in itertools.combinations(range(k), 2):
        distance = float(np.sum((means[a] - means[b]) ** 2)) - noise[a] - noise[b]
        reference[a, b] = reference[b, a] = distance
        d = z[:, a] - z[:, b]
        names[a, b] = names[b, a] = xrep(d, d)
    return reference, names


def mantel(x: np.ndarray, means: np.ndarray, noise: np.ndarray | None = None) -> dict:
    """H2. ``x``: (configurations, scenes, 2, K names, p). Exact label permutation, one-sided.

    The statistic is the Spearman correlation, over painter pairs, of the cross-repeat squared
    distance between two names' outputs and the squared distance between their reference
    means, averaged over configurations. Its null permutes painter labels of the references.
    """
    k = means.shape[0]
    upper = np.triu_indices(k, 1)
    matrices = [pair_matrices(x[m], means, noise) for m in range(x.shape[0])]
    reference = matrices[0][0]
    names = np.array([n[upper] for _, n in matrices])
    orders = np.array(list(itertools.permutations(range(k))))
    if len(orders) != math.factorial(k):
        raise ValueError("permutation census incomplete")
    permuted = reference[orders[:, :, None], orders[:, None, :]][:, upper[0], upper[1]]

    def standardized_ranks(values: np.ndarray) -> np.ndarray:
        ranks = stats.rankdata(values, axis=-1)
        ranks = ranks - ranks.mean(axis=-1, keepdims=True)
        return ranks / np.sqrt(np.sum(ranks**2, axis=-1, keepdims=True))

    null = standardized_ranks(permuted) @ standardized_ranks(names).T  # (orders, configurations)
    observed = null[0]  # The identity permutation comes first.
    pooled = float(observed.mean())
    p_value = float(np.mean(null.mean(axis=1) >= pooled - 1e-12))
    return dict(spearman_by_configuration=observed.tolist(), pooled_spearman=pooled,
                exact_p_one_sided=p_value, permutations=len(orders),
                supported=bool(p_value < 0.05),
                reference_pairs=reference[upper].tolist(),
                name_pairs_by_configuration=names.tolist())


def panel_noise(values: np.ndarray) -> float:
    """tr(S)/n: the expected inflation of a squared distance between finite-panel means."""
    values = np.asarray(values, dtype=float)
    return float(np.trace(np.atleast_2d(np.cov(values, rowvar=False, ddof=1))) / len(values))


def drift(new: np.ndarray, old: np.ndarray) -> dict:
    """Free and generic arms, new collection against September, one configuration.

    ``new``, ``old``: (scenes, 2, 2 arms, p). The cross-collection squared distance of scene means
    is estimated without repeat-noise bias and compared with the September repeat noise.
    """
    out = {}
    for index, arm in enumerate(("free", "generic")):
        a, b = new[:, :, index], old[:, :, index]
        between = 0.5 * (np.sum((a[:, 0] - b[:, 0]) * (a[:, 1] - b[:, 1]), axis=1)
                         + np.sum((a[:, 0] - b[:, 1]) * (a[:, 1] - b[:, 0]), axis=1))
        noise = 0.5 * np.sum((b[:, 0] - b[:, 1]) ** 2, axis=1)
        out[arm] = dict(between_collections=float(between.mean()),
                        between_ci95=student(between),
                        september_repeat_noise=float(noise.mean()),
                        ratio=float(between.mean() / noise.mean()))
    return out


def analyze(x: np.ndarray, refs: dict, arms: dict, september: np.ndarray | None = None,
            draws: int = DRAWS) -> dict:
    """``x``: (6, 14, 2, 10, p); ``refs``: group -> four (works, p) reference arrays;
    ``september``: (6, 14, 2, 2, p).

    In the 31 features, each group also gets the paper's primary analysis
    (``painter_specificity_v2.analysis.compute``: the 21-comparison family, reference
    resampling and the fixed-effects regression) on its six-arm slice of the full grid.

    Scenes enter only when every configuration, arm and repeat is present (the paper's common
    complete-scene panel); below 12 such scenes the analysis is unavailable.
    """
    means = {g: np.array([r.mean(axis=0) for r in refs[g]]) for g in arms}
    primary = {}
    if x.shape[1:] == (14, 2, 10, 31):
        from latent_art_bench.painter_specificity_v2.analysis import compute

        primary = {g: compute(x[:, :, :, list(columns)], refs[g]) for g, columns in arms.items()}
    complete = np.isfinite(x).all(axis=(0, 2, 3, 4))
    if september is not None:
        complete &= np.isfinite(september).all(axis=(0, 2, 3, 4))
    if complete.sum() < MINIMUM_SCENES:
        return dict(available=False, complete_scenes=np.flatnonzero(complete).tolist(),
                    primary=primary)
    x = x[:, complete]
    september = None if september is None else september[:, complete]
    result = dict(available=True, complete_scenes=np.flatnonzero(complete).tolist(), groups={},
                  primary=primary, closeness=closeness_test(x, arms, draws=draws))
    for name, columns in arms.items():
        result["groups"][name] = [group_summary(x[m][:, :, columns], means[name])
                                  for m in range(x.shape[0])]
    named = [c for g in arms.values() for c in g[2:]]
    stacked = np.concatenate([means[g] for g in arms])
    noise = np.array([panel_noise(r) for g in arms for r in refs[g]])
    result["dose_response"] = mantel(x[:, :, :, named], stacked, noise)
    result["dose_response_uncorrected"] = mantel(x[:, :, :, named], stacked)
    result["reference_spread"] = {g: corrected_h(refs[g]) for g in arms}
    if september is not None:
        result["drift"] = [drift(x[m][:, :, :2], september[m]) for m in range(x.shape[0])]
    return result


def predictions(generic: np.ndarray, means: dict) -> dict:
    """Before collection: H and the faithful benchmark N*/(N*+H) from a generic arm.

    ``generic``: (configurations, scenes, 2, p), September's generic outputs.
    """
    out = {}
    for name, group_means in means.items():
        mu_bar = group_means.mean(axis=0)
        h = float(np.sum((group_means - mu_bar) ** 2))
        faithful = []
        for m in range(generic.shape[0]):
            t = mu_bar[None] - generic[m].mean(axis=0)
            n_star = 4 * xrep(t, t)
            faithful.append(n_star / (n_star + h))
        out[name] = dict(H=h, faithful_shared_fraction=faithful)
    return out


__all__ = ["analyze", "predictions", "group_summary", "closeness_test", "mantel", "drift",
           "shared_fraction", "pair_matrices", "review"]
