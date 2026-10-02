"""Direction-only agreement, embedding intervals, repeat dependence and configuration checks.

See studies/painter_tmlr_diagnostics_v5/PLAN.md. Retrospective; retained vectors and
embeddings only. Extends versions 1-4 without modifying their outputs.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

from latent_art_bench import painter_learned_audit_v1 as learned_audit
from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench import painter_tmlr_diagnostics_v1 as v1
from latent_art_bench import painter_tmlr_diagnostics_v3 as v3
from latent_art_bench import painter_tmlr_diagnostics_v4 as v4
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v1.analysis import geometry
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_tmlr_diagnostics_v5"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_diagnostics_v5.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
DIRECTION_SEED, PROXIMITY_SEED, DRAWS = 20261010, 20261011, 5000
REPS = ("hand31", "clip", "csd")


def scene_metrics(x, means):
    """Per-scene beta, Q and D of the centered named contrasts against pooled means."""
    d = review.centered(np.asarray(x, dtype=float)[:, :, 2:])
    r = review.centered(np.asarray(means, dtype=float))
    beta, q, error = review.metrics(d, r)
    return beta, q, error


def alignment(beta, q):
    q_mean = float(np.mean(q))
    return float(np.mean(beta) / np.sqrt(q_mean)) if q_mean > 0 else None


def held_out(beta, q):
    """Closed-form leave-one-scene-out rescaled error."""
    beta, q = np.asarray(beta, dtype=float), np.asarray(q, dtype=float)
    n = len(beta)
    train_b = (beta.sum() - beta) / (n - 1)
    train_q = (q.sum() - q) / (n - 1)
    if (train_q <= 0).any():
        return None
    kappa = np.maximum(0, train_b / train_q)
    return float(np.mean(1 - 2 * kappa * beta + kappa**2 * q))


def student(values):
    v = np.asarray(values, dtype=float)
    half = stats.t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))
    return [float(v.mean() - half), float(v.mean() + half)]


def repeat_noise(x, means):
    d = review.centered(np.asarray(x, dtype=float)[:, :, 2:])
    r = review.centered(np.asarray(means, dtype=float))
    h = float(np.sum(r * r))
    return float(np.mean(0.5 * np.sum((d[:, 0] - d[:, 1]) ** 2, axis=(1, 2))) / h)


def rho_at_one(d_value, noise):
    """Common repeat correlation at which an error above 1 would fall to 1."""
    if d_value <= 1 or noise <= 0:
        return None
    a = (d_value - 1) / noise
    return float(a / (1 + a))


def split(x, refs):
    g = geometry(np.asarray(x, dtype=float)[:, :, 2:], refs)
    return float(g["amplitude_error"].mean()), float(g["off_axis_error"].mean())


def proximity_terms(x, means):
    """Scene-wise proximity gain and its shared term for one configuration."""
    m = np.asarray(x, dtype=float).mean(axis=1)
    generic, named = m[:, 1], m[:, 2:]
    mu_bar = means.mean(axis=0)
    gain = np.einsum("saj,aj->s", named, means) / 4 - generic @ mu_bar
    shared = (named.mean(axis=1) - generic) @ mu_bar
    return gain, shared


def proximity_summary(gain, shared):
    specific = gain - shared
    return dict(
        corr_shared=float(np.corrcoef(gain, shared)[0, 1]),
        corr_specific=float(np.corrcoef(gain, specific)[0, 1]),
        variance_ratio=float(np.var(shared) / np.var(specific)),
    )


def distinct_share(xa, xb):
    """Share of scene x clause cells where between-configuration distance exceeds repeats."""
    count = 0
    cells = 0
    for s_idx in range(xa.shape[0]):
        for a in range(xa.shape[2]):
            pa, pb = xa[s_idx, :, a], xb[s_idx, :, a]
            cross = np.mean([np.linalg.norm(u - w) for u in pa for w in pb])
            within = np.mean([np.linalg.norm(pa[0] - pa[1]), np.linalg.norm(pb[0] - pb[1])])
            count += cross > within
            cells += 1
    return float(count / cells)


def projection(x_models, means):
    r = review.centered(np.asarray(means, dtype=float))
    _, _, vt = np.linalg.svd(r, full_matrices=False)
    axes = vt[:2]
    out = dict(reference=(r @ axes.T).tolist(), models=[])
    for x in x_models:
        d = review.centered(np.asarray(x, dtype=float)[:, :, 2:]).mean(axis=(0, 1))
        out["models"].append((d @ axes.T).tolist())
    return out


def input_bindings():
    paths = [
        PLAN,
        Path(__file__),
        TEST,
        Path(v1.__file__),
        Path(v3.__file__),
        Path(v4.__file__),
        Path(review.__file__),
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "measurements.jsonl",
        s.DATA / "analysis.json",
        s.REF,
        s.SCALER,
        review.DEVELOPMENT,
        review.OUT / "analysis.json",
        v1.JSON_PATH,
        v4.JSON_PATH,
        learned_audit.OUT / "inputs.json",
        learned_audit.OUT / "analysis.json",
    ]
    for name in ("clip", "csd"):
        paths += [
            learned_audit.OUT / f"embeddings_{name}.npz",
            learned_audit.OUT / f"extraction_{name}.json",
        ]
    return [dict(path=str(p.relative_to(s.ROOT)), sha256=s.sha(p)) for p in sorted(set(paths))]


def compute():
    bindings = input_bindings()
    x31, refs31 = measured.load(square=False)
    refs31 = [np.asarray(v, dtype=float) for v in refs31]
    data = {"hand31": (np.asarray(x31, dtype=float), refs31)}
    for name in ("clip", "csd"):
        xe, _, _ = learned_audit.arrays(name)
        data[name] = (xe, v3.aligned_embedding_refs(name))
    primary = s.read(s.DATA / "analysis.json")["models"]
    recorded_noise = [r["repeat_noise_over_h"] for r in s.read(v1.JSON_PATH)["hand31"]]
    audit = s.read(learned_audit.OUT / "analysis.json")
    content = s.read(v4.JSON_PATH)
    keep, _ = v4.content_scenes()
    labels, _, _ = review.labels_and_development()
    per_rep, scene_stats = {}, {}
    for rep in REPS:
        x, refs = data[rep]
        means = np.stack([v.mean(axis=0) for v in refs])
        rows, stats_rows = [], []
        for m, model in enumerate(s.MODELS):
            beta, q, error = scene_metrics(x[m], means)
            amp, off = split(x[m], refs)
            if not np.isclose(amp + off, error.mean(), atol=1e-10):
                raise ValueError("split does not add up to D")
            noise = repeat_noise(x[m], means)
            row = dict(
                model=model,
                beta=float(beta.mean()),
                q=float(q.mean()),
                d=float(error.mean()),
                alignment=alignment(beta, q),
                held_out_d=held_out(beta, q),
                amplitude_error=amp,
                off_axis_error=off,
                repeat_noise=noise,
                rho_at_one=rho_at_one(float(error.mean()), noise),
                beta_student=student(beta),
                d_student=student(error),
            )
            if rep == "hand31":
                p = primary[m]
                if not np.allclose(
                    [amp, off, noise],
                    [p["amplitude_error"], p["off_axis_error"], recorded_noise[m]],
                    atol=1e-10,
                ):
                    raise ValueError(f"31-feature split or noise replay differs: {model}")
            else:
                cal = audit[rep]["original"]["targets"]["primary"]["models"][m]["centered"]
                if not np.allclose(
                    [row["d"], row["alignment"], row["held_out_d"]],
                    [cal["d"], cal["corrected_alignment"], cal["calibration"]["held_out_d"]],
                    atol=1e-10,
                ):
                    raise ValueError(f"embedding calibration replay differs: {rep} {model}")
                sub = review.centered(np.asarray(x[m], dtype=float)[:, :, 2:])[keep]
                r = review.centered(means)
                target = review.centered(review.class_targets(refs, labels))[v4.content_scenes()[1]]
                pooled = review.metrics(sub, r)[2]
                cls = review.metrics(sub, target)[2]
                recorded = content["learned"][rep][m]
                if not np.allclose(
                    [pooled.mean(), cls.mean()], [recorded["pooled_d"], recorded["class_d"]]
                ):
                    raise ValueError(f"content replay differs: {rep} {model}")
                row["pooled11_d_student"] = student(pooled)
                row["class_d_student"] = student(cls)
            rows.append(row)
            stats_rows.append((beta, q, error))
        per_rep[rep] = rows
        scene_stats[rep] = stats_rows
    rng = np.random.default_rng(DIRECTION_SEED)
    draws = rng.integers(0, 14, size=(DRAWS, 14))
    stability = {}
    for rep in REPS:
        best = {"alignment": [], "held_out_d": [], "d": []}
        for idx in draws:
            vals = [(b[idx], q[idx], e[idx]) for b, q, e in scene_stats[rep]]
            al = [alignment(b, q) for b, q, _ in vals]
            ho = [held_out(b, q) for b, q, _ in vals]
            dd = [float(np.mean(e)) for _, _, e in vals]
            best["alignment"].append(int(np.nanargmax([np.nan if v is None else v for v in al])))
            best["held_out_d"].append(int(np.nanargmin([np.nan if v is None else v for v in ho])))
            best["d"].append(int(np.argmin(dd)))
        stability[rep] = {
            key: {m: float(np.mean(np.array(v) == j)) for j, m in enumerate(s.MODELS)}
            for key, v in best.items()
        }
    recognition = {
        rep: [
            t["recognition"]["macro_accuracy"]
            for t in audit[rep]["original"]["targets"]["primary"]["models"]
        ]
        for rep in ("clip", "csd")
    }
    spearman = {
        f"alignment_recognition_{rep}": float(
            stats.spearmanr([r["alignment"] for r in per_rep[rep]], recognition[rep])[0]
        )
        for rep in ("clip", "csd")
    }
    for a, b in itertools.combinations(REPS, 2):
        for key in ("alignment", "d"):
            spearman[f"{key}_{a}_{b}"] = float(
                stats.spearmanr([r[key] for r in per_rep[a]], [r[key] for r in per_rep[b]])[0]
            )
    proximity = {}
    rng = np.random.default_rng(PROXIMITY_SEED)
    prox_draws = rng.integers(0, 14, size=(DRAWS, 14))
    for rep in ("clip", "csd"):
        x, refs = data[rep]
        means = np.stack([v.mean(axis=0) for v in refs])
        terms = [proximity_terms(x[m], means) for m in range(6)]
        gain = np.array([t[0].mean() for t in terms])
        shared = np.array([t[1].mean() for t in terms])
        recorded = [
            t["prototype"]["common_vs_labeled_prototype_gain"]["named_minus_generic"]
            for t in audit[rep]["original"]["targets"]["primary"]["models"]
        ]
        if not np.allclose(shared / gain, [r["common_fraction"] for r in recorded], atol=1e-10):
            raise ValueError(f"proximity replay differs: {rep}")
        point = proximity_summary(gain, shared)
        loo = [proximity_summary(np.delete(gain, j), np.delete(shared, j)) for j in range(6)]
        boot = []
        for idx in prox_draws:
            g = np.array([t[0][idx].mean() for t in terms])
            sh = np.array([t[1][idx].mean() for t in terms])
            boot.append(proximity_summary(g, sh))
        proximity[rep] = dict(
            point=point,
            leave_one_out={k: [min(v[k] for v in loo), max(v[k] for v in loo)] for k in point},
            scene_interval={
                k: np.quantile([b[k] for b in boot], [0.025, 0.975]).tolist() for k in point
            },
        )
    distinct = {}
    for rep in REPS:
        x, _ = data[rep]
        distinct[rep] = {
            f"{s.MODELS[a]}|{s.MODELS[b]}": distinct_share(x[a], x[b])
            for a, b in itertools.combinations(range(6), 2)
        }
    means31 = np.stack([v.mean(axis=0) for v in refs31])
    result = dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; post-result diagnostics requested by round-5 reviews",
        uncertainty="Student and percentile intervals and resampling shares; no tests",
        seeds=dict(direction=DIRECTION_SEED, proximity=PROXIMITY_SEED),
        inputs=bindings,
        models=list(s.MODELS),
        agreement=per_rep,
        stability=stability,
        spearman=spearman,
        proximity=proximity,
        distinct=distinct,
        projection=projection([data["hand31"][0][m] for m in range(6)], means31),
    )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return result


def fmt(v, places=3):
    return "n/a" if v is None else f"{v:.{places}f}"


def report(result):
    lines = [
        "# TMLR revision diagnostics, version 5",
        "",
        "Retrospective analysis under",
        "[the plan](../../studies/painter_tmlr_diagnostics_v5/PLAN.md).",
        "",
        "## Agreement, direction and repeat dependence",
        "",
    ]
    for rep, rows in result["agreement"].items():
        for title, row in zip(s.TITLES, rows):
            lines.append(
                f"- {rep} {title}: beta {fmt(row['beta'])}, Q {fmt(row['q'])}, alignment "
                f"{fmt(row['alignment'])}, D {fmt(row['d'])} "
                f"[{fmt(row['d_student'][0])}, {fmt(row['d_student'][1])}], held-out "
                f"{fmt(row['held_out_d'])}, along {fmt(row['amplitude_error'])}, off "
                f"{fmt(row['off_axis_error'])}, repeat noise {fmt(row['repeat_noise'])}, "
                f"rho at D=1 {fmt(row['rho_at_one'])}"
            )
        lines.append("")
    lines += ["## Best-configuration frequencies (scene resampling)", ""]
    for rep, block in result["stability"].items():
        for key, freq in block.items():
            top = max(freq, key=freq.get)
            lines.append(f"- {rep} {key}: {top} {fmt(freq[top])}")
    lines += ["", "## Spearman correlations", ""]
    for key, v in result["spearman"].items():
        lines.append(f"- {key}: {fmt(v)}")
    lines += ["", "## Proximity across configurations", ""]
    for rep, block in result["proximity"].items():
        for key, v in block["point"].items():
            lo, hi = block["scene_interval"][key]
            l1, l2 = block["leave_one_out"][key]
            lines.append(
                f"- {rep} {key}: {fmt(v)} [{fmt(lo)}, {fmt(hi)}], leave-one-out "
                f"{fmt(l1)}--{fmt(l2)}"
            )
    lines += ["", "## Distinct configurations (share of cells)", ""]
    for rep, block in result["distinct"].items():
        pair = f"{s.MODELS[2]}|{s.MODELS[3]}"
        lines.append(
            f"- {rep}: Flare vs Sunburst {fmt(block[pair])}; minimum over pairs "
            f"{fmt(min(block.values()))}"
        )
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
        print("Exact TMLR diagnostics v5 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v5 written")


if __name__ == "__main__":
    main()
