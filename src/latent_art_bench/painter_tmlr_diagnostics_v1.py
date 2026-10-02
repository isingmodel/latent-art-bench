"""Reference values, direction, representation sensitivity and readout stability.

See studies/painter_tmlr_diagnostics_v1/PLAN.md. Retrospective; retained vectors
and embeddings only. No acquisition, extraction or modification of earlier results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from latent_art_bench import painter_learned_audit_v1 as learned_audit
from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_tmlr_diagnostics_v1"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_diagnostics.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
FAMILIES = {
    "all31": slice(0, 31),
    "color": slice(0, 11),
    "spatial": slice(11, 19),
    "texture": slice(19, 31),
}
SEED = 20261001
DRAWS = 5000
EXCHANGEABLE_NULL = 0.25


def xrep(u, v):
    """Symmetrized cross-repeat inner product; arrays have repeats on axis 0."""
    u, v = np.asarray(u, dtype=float), np.asarray(v, dtype=float)
    return float(0.5 * (np.sum(u[0] * v[1]) + np.sum(u[1] * v[0])))


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else None


def decomposition(x, means):
    """Shared/between-name components, reference values, direction and proximity.

    ``x`` has shape (scenes, 2 repeats, 6 arms, p); ``means`` has shape (4, p).
    """
    x = np.asarray(x, dtype=float)
    means = np.asarray(means, dtype=float)
    if x.ndim != 4 or x.shape[1:3] != (2, 6) or means.shape != (4, x.shape[3]):
        raise ValueError("scenes x 2 repeats x 6 arms x p and (4, p) means required")
    zbar = x.mean(axis=0)
    named = zbar[:, 2:]
    named_mean = named.mean(axis=1)
    generic = zbar[:, 1]
    g = generic - zbar[:, 0]
    c = named_mean - generic
    e = named - named_mean[:, None]
    mu_bar = means.mean(axis=0)
    r = means - mu_bar
    h = float(np.sum(r * r))
    t = mu_bar[None] - generic
    n = 4 * xrep(c, c)
    b = sum(xrep(e[:, a], e[:, a]) for a in range(4))
    n_star = 4 * xrep(t, t)
    ct, cc, tt = xrep(c, t), xrep(c, c), xrep(t, t)
    cg, gg = xrep(c, g), xrep(g, g)
    shared_gain = 2 * ct - cc
    between_gain = 0.5 * float(np.mean([np.sum(e[k] * r) for k in range(2)])) - 0.25 * b
    direct = float(
        np.mean(
            [
                xrep(means[a][None] - generic, means[a][None] - generic)
                - xrep(means[a][None] - named[:, a], means[a][None] - named[:, a])
                for a in range(4)
            ]
        )
    )
    gain = shared_gain + between_gain
    if not np.isclose(direct, gain, atol=1e-10, rtol=1e-10):
        raise ValueError("centroid proximity identity failed")
    return dict(
        H=h,
        N=n,
        B=b,
        shared_fraction=ratio(n, n + b),
        N_over_H=ratio(n, h),
        B_over_H=ratio(b, h),
        faithful_N=n_star,
        faithful_shared_fraction=ratio(n_star, n_star + h),
        direction_cosine=float(ct / np.sqrt(cc * tt)) if cc > 0 and tt > 0 else None,
        projection_ratio=ratio(ct, tt),
        generic_cosine=float(cg / np.sqrt(cc * gg)) if cc > 0 and gg > 0 else None,
        fraction_along_generic=float(4 * cg**2 / (gg * n)) if gg > 0 and n > 0 else None,
        centroid_gain=gain,
        centroid_gain_shared=shared_gain,
        centroid_gain_between=between_gain,
        centroid_gain_shared_fraction=ratio(shared_gain, gain),
        identity_residual=float(direct - gain),
    )


def leave_one_feature_out(x, means):
    fractions = []
    for j in range(x.shape[-1]):
        keep = [i for i in range(x.shape[-1]) if i != j]
        fractions.append(decomposition(x[..., keep], means[:, keep])["shared_fraction"])
    zbar = np.asarray(x, dtype=float).mean(axis=0)
    c = zbar[:, 2:].mean(axis=1) - zbar[:, 1]
    contributions = [4 * xrep(c[:, j], c[:, j]) for j in range(x.shape[-1])]
    return dict(shared_fraction=fractions, n_contribution=contributions)


def corrected_h(refs):
    """H minus its finite-sample expectation bias, (3/4) sum_a tr(S_a)/n_a."""
    means = np.array([v.mean(axis=0) for v in refs])
    r = means - means.mean(axis=0)
    h = float(np.sum(r * r))
    bias = 0.75 * sum(float(np.trace(np.cov(v, rowvar=False, ddof=1))) / len(v) for v in refs)
    return dict(H=h, bias=bias, H_corrected=h - bias, ratio=(h - bias) / h)


def repeat_noise(x, reference_means):
    r = reference_means - reference_means.mean(axis=0)
    h = float(np.sum(r * r))
    named = np.asarray(x, dtype=float)[:, :, 2:]
    d = named - named.mean(axis=2, keepdims=True)
    return float(0.5 * np.sum((d[:, 0] - d[:, 1]) ** 2) / (len(x) * h))


def within_scene_shared_fraction(x):
    """Generic-baseline shared fraction with components computed in each scene."""
    x = np.asarray(x, dtype=float)
    named = x[:, :, 2:]
    c = named.mean(axis=2) - x[:, :, 1]
    e = named - named.mean(axis=2, keepdims=True)
    n = float(np.mean(4 * np.sum(c[:, 0] * c[:, 1], axis=1)))
    b = float(np.mean(np.sum(e[:, 0] * e[:, 1], axis=(1, 2))))
    return ratio(n, n + b)


def prototype_faithful_fraction(x, prototypes):
    """Equation-4 shared fraction if every named mean equalled its prototype."""
    generic = np.asarray(x, dtype=float)[:, :, 1].mean(axis=(0, 1))
    mu_bar = prototypes.mean(axis=0)
    h = float(np.sum((prototypes - mu_bar) ** 2))
    common = float((mu_bar - generic) @ mu_bar)
    return ratio(common, common + h / 4)


def scene_statistics(x, prototypes):
    """Per-scene sufficient statistics for gain, recognition and centered error.

    Returns scene means (scenes, 6 arms, p), correct counts (scenes, 4) and
    scene-wise errors (scenes,). ``prototypes`` are unnormalized reference means.
    """
    x = np.asarray(x, dtype=float)
    means = x.mean(axis=1)
    units = prototypes / np.linalg.norm(prototypes, axis=1, keepdims=True)
    named = x[:, :, 2:]
    predictions = np.argmax(named @ units.T, axis=-1)
    correct = (predictions == np.arange(4)[None, None]).sum(axis=1)
    r = prototypes - prototypes.mean(axis=0)
    h = float(np.sum(r * r))
    d = named - named.mean(axis=2, keepdims=True)
    errors = np.sum((d[:, 0] - r) * (d[:, 1] - r), axis=(1, 2)) / h
    return means, correct, errors


def readouts(means, correct, errors, prototypes, scenes):
    """Gain, its shared fraction, macro accuracy and D over a list of scene indices."""
    m = means[scenes].mean(axis=0)
    mu_bar = prototypes.mean(axis=0)
    named = m[2:]
    gain = float(np.mean(np.sum(named * prototypes, axis=1)) - m[1] @ mu_bar)
    common = float((named.mean(axis=0) - m[1]) @ mu_bar)
    accuracy = float(correct[scenes].sum(axis=0).mean() / (2 * len(scenes)))
    return dict(
        gain=gain,
        gain_shared_fraction=ratio(common, gain),
        accuracy=accuracy,
        d=float(errors[scenes].mean()),
    )


def hand_errors(x, reference_means):
    r = reference_means - reference_means.mean(axis=0)
    h = float(np.sum(r * r))
    named = x[:, :, 2:]
    d = named - named.mean(axis=2, keepdims=True)
    return np.sum((d[:, 0] - r) * (d[:, 1] - r), axis=(1, 2)) / h


def stability(per_model, keys, better):
    """Deletion ranges and paired scene-bootstrap orderings across configurations."""
    scenes = next(iter(per_model.values()))["scenes"]
    deletions = {}
    for model, stats in per_model.items():
        rows = [stats["fn"](scenes[:i] + scenes[i + 1 :]) for i in range(len(scenes))]
        deletions[model] = {
            key: [min(row[key] for row in rows), max(row[key] for row in rows)] for key in keys
        }
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(scenes), size=(DRAWS, len(scenes)))
    models = list(per_model)
    values = {key: np.empty((DRAWS, len(models))) for key in keys}
    for i, sample in enumerate(draws):
        for j, model in enumerate(models):
            row = per_model[model]["fn"](list(sample))
            for key in keys:
                values[key][i, j] = np.nan if row[key] is None else row[key]
    bootstrap = {}
    for key in keys:
        v = values[key]
        sign = 1 if better[key] == "higher" else -1
        best = np.argmax(sign * v, axis=1)
        pairs = {}
        for a in range(len(models)):
            for b in range(a + 1, len(models)):
                pairs[f"{models[a]}|{models[b]}"] = float(np.mean(sign * (v[:, a] - v[:, b]) > 0))
        bootstrap[key] = dict(
            better=better[key],
            best_frequency={m: float(np.mean(best == j)) for j, m in enumerate(models)},
            first_better_frequency=pairs,
        )
    return dict(deletion_ranges=deletions, bootstrap=bootstrap)


def input_bindings():
    paths = [
        PLAN,
        Path(__file__),
        TEST,
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "measurements.jsonl",
        s.DATA / "requests.jsonl",
        s.REF,
        s.SCALER,
        review.DEVELOPMENT,
        Path(review.__file__),
        Path(measured.__file__),
        Path(learned_audit.__file__),
        learned_audit.OUT / "inputs.json",
    ]
    for name in ("clip", "csd"):
        paths += [
            learned_audit.OUT / f"embeddings_{name}.npz",
            learned_audit.OUT / f"extraction_{name}.json",
        ]
    return [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in sorted(set(paths))]


def compute():
    bindings = input_bindings()
    x, refs = measured.load(square=False)
    if x.shape != (6, 14, 2, 6, 31):
        raise ValueError("the retained complete 1008-image panel is required")
    ref_means = np.array([v.mean(axis=0) for v in refs])
    _, dev, weights = review.labels_and_development()
    maps = {
        "equal_family": np.diag(np.repeat(np.sqrt(1 / np.array([11.0, 8.0, 12.0])), [11, 8, 12])),
        "development_covariance": review.covariance_map(dev, weights),
    }
    primary = s.read(s.DATA / "analysis.json")["models"]
    hand = []
    for m, model in enumerate(s.MODELS):
        families = {
            name: decomposition(x[m][..., cut], ref_means[:, cut]) for name, cut in FAMILIES.items()
        }
        weighted = {
            name: decomposition(x[m] @ matrix, ref_means @ matrix)["shared_fraction"]
            for name, matrix in maps.items()
        }
        errors = hand_errors(x[m], ref_means)
        if not np.isclose(errors.mean(), primary[m]["distortion"]["mean"], atol=1e-12):
            raise ValueError("primary D identity differs")
        hand.append(
            dict(
                model=model,
                title=s.TITLES[m],
                families=families,
                weighted_shared_fraction=weighted,
                within_scene_shared_fraction=within_scene_shared_fraction(x[m]),
                leave_one_feature_out=leave_one_feature_out(x[m], ref_means),
                repeat_noise_over_h=repeat_noise(x[m], ref_means),
                beta_with_corrected_h=None,
            )
        )
    h_correction = corrected_h(refs)
    for m, row in enumerate(hand):
        row["beta_with_corrected_h"] = primary[m]["beta"]["mean"] / h_correction["ratio"]
    scenes = list(range(14))
    hand_stats = {
        model: dict(
            scenes=scenes,
            fn=(lambda idx, e=hand_errors(x[m], ref_means): dict(d=float(e[idx].mean()))),
        )
        for m, model in enumerate(s.MODELS)
    }
    stability_result = {"hand31": stability(hand_stats, ["d"], {"d": "lower"})}
    learned_result = {}
    reference = s.read(learned_audit.OUT / "analysis.json")
    for name in ("clip", "csd"):
        xe, refs_e, _ = learned_audit.arrays(name)
        prototypes = np.stack([v.mean(axis=0) for v in refs_e])
        recorded = reference[name]["original"]["targets"]["primary"]["models"]
        rows, stats = [], {}
        for m, model in enumerate(s.MODELS):
            means, correct, errors = scene_statistics(xe[m], prototypes)
            full = readouts(means, correct, errors, prototypes, scenes)
            expected = recorded[m]
            if not np.allclose(
                [full["gain"], full["accuracy"], full["d"]],
                [
                    expected["prototype"]["mean_named_minus_generic"],
                    expected["recognition"]["macro_accuracy"],
                    expected["centered"]["d"],
                ],
                atol=1e-10,
            ):
                raise ValueError(f"learned readout identity differs: {name} {model}")
            rows.append(
                dict(
                    model=model,
                    decomposition=decomposition(xe[m], prototypes),
                    prototype_faithful_shared_fraction=prototype_faithful_fraction(
                        xe[m], prototypes
                    ),
                    within_scene_shared_fraction=within_scene_shared_fraction(xe[m]),
                    readouts=full,
                )
            )
            stats[model] = dict(
                scenes=scenes,
                fn=(
                    lambda idx, a=means, b=correct, c=errors, p=prototypes: readouts(
                        a, b, c, p, idx
                    )
                ),
            )
        learned_result[name] = rows
        stability_result[name] = stability(
            stats,
            ["gain", "gain_shared_fraction", "accuracy", "d"],
            dict(gain="higher", gain_shared_fraction="higher", accuracy="higher", d="lower"),
        )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; post-result diagnostics requested by round-1 reviews",
        uncertainty="descriptive deletion ranges and scene bootstrap; no tests",
        exchangeable_null_shared_fraction=EXCHANGEABLE_NULL,
        bootstrap=dict(seed=SEED, draws=DRAWS, unit="scene", paired_across_configurations=True),
        inputs=bindings,
        models=list(s.MODELS),
        hand31=hand,
        h_correction=h_correction,
        learned=learned_result,
        stability=stability_result,
    )


def fmt(value, places=3):
    return "n/a" if value is None else f"{value:.{places}f}"


def report(result):
    lines = [
        "# TMLR revision diagnostics",
        "",
        "Retrospective analysis under",
        "[the plan](../../studies/painter_tmlr_diagnostics_v1/PLAN.md).",
        "Descriptive only: no tests; deletion ranges and bootstrap frequencies describe",
        "dependence on the 14 authored scenes.",
        "",
        "## Shared fraction beyond the generic clause, 31 features",
        "",
        "| Configuration | N/(N+B) | faithful | N/H | B/H | color | spatial | texture | "
        "equal family | covariance | within scene |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["hand31"]:
        f = row["families"]
        w = row["weighted_shared_fraction"]
        lines.append(
            f"| {row['title']} | {fmt(f['all31']['shared_fraction'])} | "
            f"{fmt(f['all31']['faithful_shared_fraction'])} | {fmt(f['all31']['N_over_H'])} | "
            f"{fmt(f['all31']['B_over_H'])} | {fmt(f['color']['shared_fraction'])} | "
            f"{fmt(f['spatial']['shared_fraction'])} | {fmt(f['texture']['shared_fraction'])} | "
            f"{fmt(w['equal_family'])} | {fmt(w['development_covariance'])} | "
            f"{fmt(row['within_scene_shared_fraction'])} |"
        )
    lines += [
        "",
        "Exchangeable null: 0.25. Faithful: named means replaced by reference means,",
        "generic mean kept; includes the reproduction/generation and content gaps.",
        "",
        "## Direction and centroid proximity, 31 features",
        "",
        "| Configuration | cosine(c, t) | projection | gain | shared part | between part |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["hand31"]:
        a = row["families"]["all31"]
        lines.append(
            f"| {row['title']} | {fmt(a['direction_cosine'])} | {fmt(a['projection_ratio'])} | "
            f"{fmt(a['centroid_gain'])} | {fmt(a['centroid_gain_shared'])} | "
            f"{fmt(a['centroid_gain_between'])} |"
        )
    for name, rows in result["learned"].items():
        lines += [
            "",
            f"## {name.upper()}",
            "",
            "| Configuration | N/(N+B) | faithful | prototype faithful | cosine(c, t) | "
            "gain | gain shared | accuracy | D |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for title, row in zip(s.TITLES, rows):
            d, o = row["decomposition"], row["readouts"]
            lines.append(
                f"| {title} | {fmt(d['shared_fraction'])} | {fmt(d['faithful_shared_fraction'])} | "
                f"{fmt(row['prototype_faithful_shared_fraction'])} | "
                f"{fmt(d['direction_cosine'])} | {fmt(o['gain'], 4)} | "
                f"{fmt(o['gain_shared_fraction'])} | {fmt(o['accuracy'])} | {fmt(o['d'])} |"
            )
    lines += ["", "## Readout stability (scene bootstrap, best-configuration frequency)", ""]
    for rep, block in result["stability"].items():
        for key, boot in block["bootstrap"].items():
            freq = ", ".join(
                f"{title} {boot['best_frequency'][m]:.3f}" for m, title in zip(s.MODELS, s.TITLES)
            )
            lines.append(f"- {rep} {key} ({boot['better']} is better): {freq}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("analyze", "check"))
    args = parser.parse_args()
    if args.action == "analyze" and (JSON_PATH.exists() or REPORT_PATH.exists()):
        raise FileExistsError("outputs already exist; use check, never overwrite")
    result = compute()
    markdown = report(result)
    if args.action == "check":
        if result != s.read(JSON_PATH) or markdown != REPORT_PATH.read_text():
            raise ValueError("exact replay differs")
        print("Exact TMLR diagnostics replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics written")


if __name__ == "__main__":
    main()
