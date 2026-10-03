"""Readouts for the two further painter groups: shared-fraction intervals, recognition, proximity.

See studies/painter_tmlr_diagnostics_v6/PLAN.md, written before the second collection was
measured. Reads the v3 collection, reference panels and analysis; modifies none of them.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import stats

from latent_art_bench import painter_tmlr_diagnostics_v5 as v5
from latent_art_bench.painter_specificity_v3 import report as v3
from latent_art_bench.painter_specificity_v3 import study as s
from latent_art_bench.painter_specificity_v3.panel import GROUPS
from latent_art_bench.painter_tmlr_diagnostics_v1 import xrep

NS = "painter_tmlr_diagnostics_v6"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
SEED, DRAWS = 20261012, 5000
REPS = ("hand31", "clip", "csd")


def fractions(x: np.ndarray, means: np.ndarray) -> tuple[float, float]:
    """Observed N/(N+B) and faithful N*/(N*+H) of one six-arm slice (scenes, 2, 6, p)."""
    z = x.mean(axis=0)
    named = z[:, 2:]
    c = named.mean(axis=1) - z[:, 1]
    e = named - named.mean(axis=1, keepdims=True)
    n = 4 * xrep(c, c)
    b = sum(xrep(e[:, a], e[:, a]) for a in range(4))
    mu_bar = means.mean(axis=0)
    h = float(np.sum((means - mu_bar) ** 2))
    t = mu_bar[None] - z[:, 1]
    n_star = 4 * xrep(t, t)
    return n / (n + b), n_star / (n_star + h)


def shared_interval(x: np.ndarray, means: np.ndarray, draws: int = DRAWS,
                    seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    observed, faithful = fractions(x, means)
    boot = np.array([fractions(x[idx], means)
                     for idx in (rng.integers(0, len(x), len(x)) for _ in range(draws))])
    return dict(observed=observed, faithful=faithful,
                ci95=np.percentile(boot[:, 0], [2.5, 97.5]).tolist(),
                observed_below_faithful=float(np.mean(boot[:, 0] < boot[:, 1])))


def recognition(named: list[np.ndarray], prototypes: np.ndarray) -> float:
    """Macro accuracy of nearest unit-prototype assignment; named[a] holds painter a images."""
    unit = prototypes / np.linalg.norm(prototypes, axis=1, keepdims=True)
    accuracy = [float(np.mean((images @ unit.T).argmax(axis=1) == a))
                for a, images in enumerate(named)]
    return float(np.mean(accuracy))


def compute(draws: int = DRAWS) -> dict:
    analysis = s.read(v3.OUT / "analysis.json")
    result = dict(plan_sha256=s.sha(PLAN), v3_analysis_sha256=s.sha(v3.OUT / "analysis.json"),
                  representations={})
    for rep in REPS:
        recorded = analysis["representations"][rep]
        x = v3.generated(rep)[:, recorded["complete_scenes"]]
        refs = v3.references(rep)
        means = {g: np.array([r.mean(axis=0) for r in refs[g]]) for g in GROUPS}
        out = dict(groups={})
        all_means = np.concatenate([means[g] for g in GROUPS])
        named_columns = [c for g in GROUPS for c in s.GROUP_ARMS[g][2:]]
        for g in GROUPS:
            columns = list(s.GROUP_ARMS[g])
            rows = []
            for m in range(x.shape[0]):
                view = x[m][:, :, columns]
                row = dict(shared=shared_interval(view, means[g], draws))
                if rep != "hand31":
                    named = [view[:, :, 2 + a].reshape(-1, view.shape[-1]) for a in range(4)]
                    row["recognition_four_way"] = recognition(named, means[g])
                    every = [x[m][:, :, c].reshape(-1, x.shape[-1]) for c in named_columns]
                    offset = 0 if g == GROUPS[0] else 4
                    eight = [every[offset + a] for a in range(4)]
                    unit = all_means / np.linalg.norm(all_means, axis=1, keepdims=True)
                    row["recognition_eight_way"] = float(np.mean([
                        np.mean((imgs @ unit.T).argmax(axis=1) == offset + a)
                        for a, imgs in enumerate(eight)]))
                    gain, shared = v5.proximity_terms(view, means[g])
                    row["proximity_gain"] = float(gain.mean())
                    row["proximity_shared"] = float(shared.mean())
                rows.append(row)
            group = dict(configurations=rows)
            if rep != "hand31":
                align = [r["alignment_ratio"] for r in recorded["groups"][g]]
                recog = [r["recognition_four_way"] for r in rows]
                group["spearman_alignment_recognition"] = float(stats.spearmanr(align, recog)[0])
                gain = np.array([r["proximity_gain"] for r in rows])
                shared = np.array([r["proximity_shared"] for r in rows])
                group["proximity"] = dict(
                    shared_share=(shared / gain).tolist(),
                    corr_shared=float(np.corrcoef(gain, shared)[0, 1]),
                    corr_specific=float(np.corrcoef(gain, gain - shared)[0, 1]))
            out["groups"][g] = group
        result["representations"][rep] = out
    return json.loads(json.dumps(result, sort_keys=True, allow_nan=False))


def report(result: dict) -> str:
    lines = ["# Readouts for the two further painter groups (diagnostics v6)", "",
             "Plan: `studies/painter_tmlr_diagnostics_v6/PLAN.md`.", ""]
    for rep, out in result["representations"].items():
        lines += [f"## {rep}", ""]
        for g, group in out["groups"].items():
            for m, row in enumerate(group["configurations"]):
                sh = row["shared"]
                line = (f"- {g} / {s.TITLES[m]}: shared {sh['observed']:.3f} "
                        f"{np.round(sh['ci95'], 3).tolist()}, faithful {sh['faithful']:.3f}")
                if "recognition_four_way" in row:
                    line += (f", recognition {row['recognition_four_way']:.3f} (eight-way "
                             f"{row['recognition_eight_way']:.3f})")
                lines.append(line)
            if "spearman_alignment_recognition" in group:
                lines.append(f"- {g}: Spearman(alignment, recognition) "
                             f"{group['spearman_alignment_recognition']:.3f}")
        lines.append("")
    return "\n".join(lines) + "\n"


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
        print("Exact TMLR diagnostics v6 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v6 written")


if __name__ == "__main__":
    main()
