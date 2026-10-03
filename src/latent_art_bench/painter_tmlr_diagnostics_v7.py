"""Readouts requested by review of the second collection: H2 by pair type, the closeness-only
contrast, matched closeness, and a census of the H1 resamples.

See studies/painter_tmlr_diagnostics_v7/PLAN.md. Reads the v3 collection, reference panels and
analysis and the diagnostics-v2 analysis; modifies none of them.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import stats

from latent_art_bench import painter_tmlr_diagnostics_v6 as v6
from latent_art_bench.painter_specificity_v3 import analysis
from latent_art_bench.painter_specificity_v3 import report as v3
from latent_art_bench.painter_specificity_v3 import study as s
from latent_art_bench.painter_specificity_v3.panel import GROUPS
from latent_art_bench.painter_tmlr_diagnostics_v1 import xrep

NS = "painter_tmlr_diagnostics_v7"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
DIAGNOSTICS2 = s.ROOT / "reports" / "painter_tmlr_diagnostics_v2" / "analysis.json"
PREDICTIONS = v3.REFS / "predictions.json"
SEED, DRAWS = 20261004, 5000
REPS = ("hand31", "clip", "csd")
TOLERANCE = 1e-10


def pair_types(k: int = 4) -> dict[str, np.ndarray]:
    """Positions, in the upper-triangle order of H2's 2k painters, of each pair type."""
    a, b = np.triu_indices(2 * k, 1)
    return {"within_" + GROUPS[0]: np.flatnonzero(b < k),
            "within_" + GROUPS[1]: np.flatnonzero(a >= k),
            "across": np.flatnonzero((a < k) & (b >= k))}


def spearman_by_type(reference: list[float], names: list[list[float]]) -> dict:
    """Spearman of name against reference distance within each pair type, per configuration."""
    reference, names = np.asarray(reference), np.asarray(names)
    types = dict(all=np.arange(len(reference)), **pair_types())
    out = {}
    for kind, idx in types.items():
        rho = [float(stats.spearmanr(reference[idx], row[idx])[0]) for row in names]
        out[kind] = dict(pairs=len(idx), by_configuration=rho, mean=float(np.mean(rho)))
    return out


def contrast(x: np.ndarray, means: dict, draws: int = DRAWS, seed: int = SEED) -> dict:
    """Century-minus-Hudson observed and faithful shared fractions with paired scene resamples.

    ``x``: (configurations, scenes, 2, 10 arms, p); ``means``: group -> (4, p).
    """
    def table(sample: np.ndarray) -> np.ndarray:  # (configurations, groups, observed/faithful)
        return np.array([[v6.fractions(sample[m][:, :, list(s.GROUP_ARMS[g])], means[g])
                          for g in GROUPS] for m in range(sample.shape[0])])

    point = table(x)
    observed = point[:, 0, 0] - point[:, 1, 0]
    faithful = point[:, 0, 1] - point[:, 1, 1]
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(draws):
        t = table(x[:, rng.integers(0, x.shape[1], x.shape[1])])
        diff_obs, diff_faith = t[:, 0, 0] - t[:, 1, 0], t[:, 0, 1] - t[:, 1, 1]
        boot.append((diff_faith.mean(), (diff_obs - diff_faith).mean()))
    boot = np.array(boot)
    return dict(
        observed={g: point[:, i, 0].tolist() for i, g in enumerate(GROUPS)},
        faithful={g: point[:, i, 1].tolist() for i, g in enumerate(GROUPS)},
        observed_difference=observed.tolist(), faithful_difference=faithful.tolist(),
        excess=(observed - faithful).tolist(),
        mean_observed_difference=float(observed.mean()),
        mean_faithful_difference=float(faithful.mean()),
        mean_excess=float((observed - faithful).mean()),
        mean_faithful_difference_ci95=np.percentile(boot[:, 0], [2.5, 97.5]).tolist(),
        mean_excess_ci95=np.percentile(boot[:, 1], [2.5, 97.5]).tolist(),
        draws=draws, seed=seed)


def census(x: np.ndarray, draws: int = analysis.DRAWS, seed: int = analysis.SEED) -> dict:
    """Replay of H1's resampling: draws with N+B <= 0 or a fraction outside [0, 1]."""
    rng = np.random.default_rng(seed)
    configs, scenes = x.shape[:2]
    nonpositive = np.zeros((configs, len(GROUPS)), dtype=int)
    outside = np.zeros((configs, len(GROUPS)), dtype=int)
    pooled = np.empty(draws)
    for i in range(draws):
        idx = rng.integers(0, scenes, scenes)
        values = np.empty((configs, len(GROUPS)))
        for m in range(configs):
            for j, g in enumerate(GROUPS):
                z = x[m][idx][:, :, list(s.GROUP_ARMS[g])].mean(axis=0)
                named = z[:, 2:]
                c = named.mean(axis=1) - z[:, 1]
                e = named - named.mean(axis=1, keepdims=True)
                n = 4 * xrep(c, c)
                b = sum(xrep(e[:, a], e[:, a]) for a in range(4))
                values[m, j] = n / (n + b)
                nonpositive[m, j] += n + b <= 0
                outside[m, j] += not 0 <= values[m, j] <= 1
        pooled[i] = (values[:, 0] - values[:, 1]).mean()
    return dict(nonpositive_denominator={g: nonpositive[:, j].tolist()
                                         for j, g in enumerate(GROUPS)},
                fraction_outside_unit={g: outside[:, j].tolist() for j, g in enumerate(GROUPS)},
                pooled_ci95=np.percentile(pooled, [2.5, 97.5]).tolist(), draws=draws, seed=seed)


def matched(diagnostics2: dict, hudson: list[dict], predictions: dict) -> dict:
    """Impressionists (first collection) against the Hudson River School, 31 features."""
    imp = [row["point"]["all31"] for row in diagnostics2["hand31"]]
    obs = np.array([r["observed"] for r in imp]) - np.array([r["shared_fraction"] for r in hudson])
    faith = (np.array([r["faithful"] for r in imp])
             - np.array([r["faithful_shared_fraction"] for r in hudson]))
    return dict(
        H={"impressionists": predictions["hand31"]["impressionists"]["H"],
           "hudson": predictions["hand31"]["hudson"]["H"]},
        impressionists_observed=[r["observed"] for r in imp],
        impressionists_faithful=[r["faithful"] for r in imp],
        hudson_observed=[r["shared_fraction"] for r in hudson],
        hudson_faithful=[r["faithful_shared_fraction"] for r in hudson],
        observed_difference=obs.tolist(), faithful_difference=faith.tolist(),
        mean_observed_difference=float(obs.mean()), mean_faithful_difference=float(faith.mean()))


def compute(draws: int = DRAWS) -> dict:
    recorded = s.read(v3.OUT / "analysis.json")
    result = dict(plan_sha256=s.sha(PLAN), v3_analysis_sha256=s.sha(v3.OUT / "analysis.json"),
                  diagnostics2_sha256=s.sha(DIAGNOSTICS2), representations={})
    for rep in REPS:
        rec = recorded["representations"][rep]
        dose = rec["dose_response"]
        by_type = spearman_by_type(dose["reference_pairs"], dose["name_pairs_by_configuration"])
        if abs(by_type["all"]["mean"] - dose["pooled_spearman"]) > TOLERANCE:
            raise ValueError("H2 replay differs")
        x = v3.generated(rep)[:, rec["complete_scenes"]]
        refs = v3.references(rep)
        means = {g: np.array([r.mean(axis=0) for r in refs[g]]) for g in GROUPS}
        diff = contrast(x, means, draws)
        for g in GROUPS:
            for m, row in enumerate(rec["groups"][g]):
                if (abs(diff["observed"][g][m] - row["shared_fraction"]) > TOLERANCE
                        or abs(diff["faithful"][g][m] - row["faithful_shared_fraction"])
                        > TOLERANCE):
                    raise ValueError("shared-fraction replay differs")
        out = dict(h2_by_pair_type=by_type, closeness_contrast=diff)
        if rep == "hand31":
            out["h1_census"] = census(x)
            if not np.allclose(out["h1_census"]["pooled_ci95"], rec["closeness"]["pooled_ci95"],
                               rtol=0, atol=TOLERANCE):
                raise ValueError("H1 replay differs")
            out["matched_closeness"] = matched(s.read(DIAGNOSTICS2), rec["groups"]["hudson"],
                                               s.read(PREDICTIONS))
        result["representations"][rep] = out
    return json.loads(json.dumps(result, sort_keys=True, allow_nan=False))


def report(result: dict) -> str:
    lines = ["# Readouts requested by review of the second collection (diagnostics v7)", "",
             "Plan: `studies/painter_tmlr_diagnostics_v7/PLAN.md`.", ""]
    for rep, out in result["representations"].items():
        lines += [f"## {rep}", ""]
        for kind, row in out["h2_by_pair_type"].items():
            lines.append(f"- H2 {kind} ({row['pairs']} pairs): mean Spearman {row['mean']:.3f}, "
                         f"by configuration {np.round(row['by_configuration'], 3).tolist()}")
        c = out["closeness_contrast"]
        lines.append(f"- century - Hudson: observed {100 * c['mean_observed_difference']:.1f}, "
                     f"faithful {100 * c['mean_faithful_difference']:.1f} "
                     f"{np.round(100 * np.array(c['mean_faithful_difference_ci95']), 1).tolist()}, "
                     f"excess {100 * c['mean_excess']:.1f} "
                     f"{np.round(100 * np.array(c['mean_excess_ci95']), 1).tolist()} points")
        if "matched_closeness" in out:
            mc = out["matched_closeness"]
            lines.append(f"- Impressionists - Hudson: observed "
                         f"{100 * mc['mean_observed_difference']:.1f}, faithful "
                         f"{100 * mc['mean_faithful_difference']:.1f} points; H "
                         f"{mc['H']['impressionists']:.2f} vs {mc['H']['hudson']:.2f}")
            h1 = out["h1_census"]
            lines.append(f"- H1 resamples with N+B <= 0: {h1['nonpositive_denominator']}; "
                         f"fraction outside [0, 1]: {h1['fraction_outside_unit']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
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
        print("Exact TMLR diagnostics v7 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v7 written")


if __name__ == "__main__":
    main()
