"""Gap-free benchmarks, resampling intervals, pair intervals and feature separability.

See studies/painter_tmlr_diagnostics_v2/PLAN.md. Retrospective; retained vectors and
embeddings only. Extends painter_tmlr_diagnostics_v1 without modifying its outputs.
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from latent_art_bench import painter_cross_cohort_v1 as cross
from latent_art_bench import painter_learned_audit_v1 as learned_audit
from latent_art_bench import painter_specificity_review_v1 as review
from latent_art_bench import painter_tmlr_diagnostics_v1 as v1
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_measurement_v1 import workflow as measured
from latent_art_bench.painter_specificity_v2 import study as s

NS = "painter_tmlr_diagnostics_v2"
PLAN = s.ROOT / "studies" / NS / "PLAN.md"
TEST = s.ROOT / "tests" / NS / "test_diagnostics_v2.py"
OUT = s.ROOT / "reports" / NS
JSON_PATH = OUT / "analysis.json"
REPORT_PATH = OUT / "REPORT.md"
SCENE_SEED, REF_SEED, JOINT_SEED = 20261002, 20261003, 20261004
SCENE_DRAWS, REF_DRAWS, JOINT_DRAWS = 5000, 1000, 2000
CROSS_INPUTS_SHA256 = "94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693"
PAIRS = tuple(itertools.combinations(range(4), 2))


def interval(values):
    v = np.asarray([x for x in values if x is not None], dtype=float)
    if len(v) == 0:
        return None
    low, high = np.percentile(v, [2.5, 97.5])
    return [float(low), float(high)]


def fractions(x, means):
    """Observed, faithful and exact-differences shared fractions and coverage."""
    d = v1.decomposition(x, means)
    return dict(
        observed=d["shared_fraction"],
        faithful=d["faithful_shared_fraction"],
        exact=v1.ratio(d["N"], d["N"] + d["H"]),
        coverage=v1.ratio(d["N"], d["faithful_N"]),
    )


def prototype_shares(x, prototypes):
    """Shared share of Equation-4 proximity gain: observed, faithful, exact differences."""
    m = np.asarray(x, dtype=float).mean(axis=(0, 1))
    generic, named = m[1], m[2:]
    mu_bar = prototypes.mean(axis=0)
    h = float(np.sum((prototypes - mu_bar) ** 2))
    shared = float((named.mean(axis=0) - generic) @ mu_bar)
    gain = float(np.mean(np.sum(named * prototypes, axis=1)) - generic @ mu_bar)
    faithful = float((mu_bar - generic) @ mu_bar)
    return dict(
        observed=v1.ratio(shared, gain),
        faithful=v1.ratio(faithful, faithful + h / 4),
        exact=v1.ratio(shared, shared + h / 4),
        gain=gain,
    )


def per_painter_proximity(x, prototypes):
    m = np.asarray(x, dtype=float).mean(axis=(0, 1))
    generic, named = m[1], m[2:]
    gbar = named.mean(axis=0)
    rows = []
    for a in range(4):
        shared = float((gbar - generic) @ prototypes[a])
        specific = float((named[a] - gbar) @ prototypes[a])
        rows.append(
            dict(
                gain=shared + specific,
                shared=shared,
                specific=specific,
                shared_fraction=v1.ratio(shared, shared + specific),
            )
        )
    return rows


def pair_metrics(x, means):
    """Aligned amplitude and cross-repeat error for each painter pair."""
    x = np.asarray(x, dtype=float)
    out = []
    for a, b in PAIRS:
        d = x[:, :, 2 + a] - x[:, :, 2 + b]
        q = means[a] - means[b]
        h = float(q @ q)
        beta = float(np.mean(d @ q) / h)
        error = float(np.mean(np.sum((d[:, 0] - q) * (d[:, 1] - q), axis=1)) / h)
        out.append(dict(beta=beta, d=error))
    return out


def resample_refs(refs, rng):
    return np.stack([v[rng.integers(0, len(v), size=len(v))].mean(axis=0) for v in refs])


def summarize_draws(rows, keys):
    return {key: interval([r[key] for r in rows]) for key in keys}


def representation_block(x, refs, is_embedding, families=None):
    """Point values, scene-bootstrap and reference-resampling summaries for one representation."""
    means = np.stack([v.mean(axis=0) for v in refs])
    cuts = families or {"all": slice(None)}
    point = {name: fractions(x[..., cut], means[:, cut]) for name, cut in cuts.items()}
    proto = prototype_shares(x, means) if is_embedding else None
    pairs = pair_metrics(x, means)
    rng = np.random.default_rng(SCENE_SEED)
    scene_rows, proto_rows, pair_rows = {k: [] for k in cuts}, [], []
    for _ in range(SCENE_DRAWS):
        idx = rng.integers(0, x.shape[0], size=x.shape[0])
        xs = x[idx]
        for name, cut in cuts.items():
            f = fractions(xs[..., cut], means[:, cut])
            f["difference"] = (
                None
                if f["observed"] is None or f["faithful"] is None
                else f["observed"] - f["faithful"]
            )
            scene_rows[name].append(f)
        if is_embedding:
            p = prototype_shares(xs, means)
            p["difference"] = p["observed"] - p["faithful"]
            proto_rows.append(p)
        pair_rows.append(pair_metrics(xs, means))
    rng = np.random.default_rng(REF_SEED)
    ref_rows, ref_proto, ref_pairs = {k: [] for k in cuts}, [], []
    for _ in range(REF_DRAWS):
        mb = resample_refs(refs, rng)
        for name, cut in cuts.items():
            ref_rows[name].append(fractions(x[..., cut], mb[:, cut]))
        if is_embedding:
            ref_proto.append(prototype_shares(x, mb))
        ref_pairs.append(pair_metrics(x, mb))
    keys = ("observed", "faithful", "exact", "difference")
    result = dict(
        point=point,
        scene_bootstrap={
            name: dict(
                **summarize_draws(rows, keys),
                observed_below_faithful=float(
                    np.mean([r["difference"] is not None and r["difference"] < 0 for r in rows])
                ),
            )
            for name, rows in scene_rows.items()
        },
        reference_resampling={
            name: summarize_draws(rows, ("faithful", "exact")) for name, rows in ref_rows.items()
        },
        pairs=[
            dict(
                painters=[s.ARTISTS[a], s.ARTISTS[b]],
                **pairs[i],
                beta_scene=interval([row[i]["beta"] for row in pair_rows]),
                d_scene=interval([row[i]["d"] for row in pair_rows]),
                beta_reference=interval([row[i]["beta"] for row in ref_pairs]),
                d_reference=interval([row[i]["d"] for row in ref_pairs]),
            )
            for i, (a, b) in enumerate(PAIRS)
        ],
    )
    if is_embedding:
        result["prototype"] = dict(
            point=proto,
            scene_bootstrap=dict(
                **summarize_draws(proto_rows, keys),
                observed_below_faithful=float(np.mean([r["difference"] < 0 for r in proto_rows])),
            ),
            reference_resampling=summarize_draws(ref_proto, ("observed", "faithful", "exact")),
            per_painter=per_painter_proximity(x, means),
        )
    return result


def development_rows():
    """Development works (standardized 31 features) with painter labels."""
    if s.sha(review.DEVELOPMENT) != s.read(s.SCALER)["development_feature_sha256"]:
        raise ValueError("development vectors differ from the original scaler input")
    rows = [v for v in s.rows(review.DEVELOPMENT) if v["role"] == "development"]
    if len(rows) != 221 or any(v["status"] != "measured" for v in rows):
        raise ValueError("development membership differs")
    values = transform(np.array([v["values"] for v in rows]), s.read(s.SCALER))
    labels = np.array([s.ARTISTS.index(v["painter_id"]) for v in rows])
    return values, labels


def nearest_centroid(values, labels, means):
    distances = ((values[:, None, :] - means[None]) ** 2).sum(axis=-1)
    predictions = distances.argmin(axis=1)
    per = [float(np.mean(predictions[labels == a] == a)) for a in range(4)]
    return dict(macro_accuracy=float(np.mean(per)), per_painter=per)


def joint_d_below_one(x, refs):
    rng = np.random.default_rng(JOINT_SEED)
    counts = np.zeros(len(x))
    for _ in range(JOINT_DRAWS):
        idx = rng.integers(0, x.shape[1], size=x.shape[1])
        mb = resample_refs(refs, rng)
        for m in range(len(x)):
            counts[m] += v1.hand_errors(x[m][idx], mb).mean() < 1
    return (counts / JOINT_DRAWS).tolist()


def sd_turbo_benchmarks():
    z, means, _ = cross.load_frozen(
        s.ROOT, execute_real=True, expected_inputs_sha256=CROSS_INPUTS_SHA256
    )
    recorded = s.read(s.ROOT / cross.OUT / "analysis.json")["families"]
    out = {}
    for name, cut in cross.VIEWS.items():
        zz, mm = z[..., cut], means[:, cut]
        block = zz.mean(axis=1)
        mu_bar = mm.mean(axis=0)
        h = float(np.sum((mm - mu_bar) ** 2))
        c = block[:, 1:].mean(axis=1) - block[:, 0]
        t = mu_bar[None] - block[:, 0]
        n = float(4 * cross.u_product(c))
        n_star = float(4 * cross.u_product(t))
        if not np.isclose(n, recorded[name]["pooled"]["C"], atol=1e-9):
            raise ValueError(f"SD-Turbo shared component differs from the record: {name}")
        out[name] = dict(
            N=n,
            H=h,
            faithful_N=n_star,
            faithful=v1.ratio(n_star, n_star + h),
            exact=v1.ratio(n, n + h),
        )
    return out


def input_bindings():
    paths = [
        PLAN,
        Path(__file__),
        TEST,
        Path(v1.__file__),
        s.ROOT / "pyproject.toml",
        s.ROOT / "uv.lock",
        s.DATA / "measurements.jsonl",
        s.REF,
        s.SCALER,
        review.DEVELOPMENT,
        learned_audit.OUT / "inputs.json",
        s.ROOT / cross.OUT / "inputs.json",
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
    refs = [np.asarray(v, dtype=float) for v in refs]
    means = np.stack([v.mean(axis=0) for v in refs])
    recorded = s.read(review.OUT / "analysis.json")["models"]
    hand = []
    for m, model in enumerate(s.MODELS):
        block = representation_block(x[m], refs, False, v1.FAMILIES)
        expected = {tuple(p["artists"]): p for p in recorded[m]["artist_pairs"]}
        for row in block["pairs"]:
            ref = expected[tuple(row["painters"])]
            if not np.allclose([row["beta"], row["d"]], [ref["beta"], ref["d"]], atol=1e-10):
                raise ValueError("pair identity differs from review v1")
        hand.append(dict(model=model, **block))
    family_means = {}
    rng = np.random.default_rng(SCENE_SEED)
    draws = [rng.integers(0, 14, size=14) for _ in range(SCENE_DRAWS)]
    for name, cut in v1.FAMILIES.items():
        point = float(
            np.mean([fractions(x[m][..., cut], means[:, cut])["observed"] for m in range(6)])
        )
        boot = []
        for idx in draws:
            values_ = [fractions(x[m][idx][..., cut], means[:, cut])["observed"] for m in range(6)]
            boot.append(None if any(v is None for v in values_) else float(np.mean(values_)))
        family_means[name] = dict(
            mean=point,
            scene_interval=interval(boot),
            unavailable_draws=sum(v is None for v in boot),
        )
    values, labels = development_rows()
    learned = {}
    reference = s.read(learned_audit.OUT / "analysis.json")
    for name in ("clip", "csd"):
        xe, refs_e, _ = learned_audit.arrays(name)
        refs_e = [np.asarray(v, dtype=float) for v in refs_e]
        rows = []
        for m, model in enumerate(s.MODELS):
            block = representation_block(xe[m], refs_e, True)
            recorded_pairs = reference[name]["original"]["targets"]["primary"]["models"][m][
                "painter_pairs"
            ]
            for row, ref in zip(block["pairs"], recorded_pairs, strict=True):
                if not np.allclose([row["beta"], row["d"]], [ref["beta"], ref["d"]], atol=1e-10):
                    raise ValueError(f"learned pair identity differs: {name} {model}")
            rows.append(dict(model=model, **block))
        learned[name] = rows
    result = dict(
        schema_version=1,
        analysis_namespace=NS,
        status="retrospective; post-result diagnostics requested by round-2 reviews",
        uncertainty="percentile intervals from scene and reference resampling; no tests",
        seeds=dict(scene=SCENE_SEED, reference=REF_SEED, joint=JOINT_SEED),
        draws=dict(scene=SCENE_DRAWS, reference=REF_DRAWS, joint=JOINT_DRAWS),
        inputs=bindings,
        models=list(s.MODELS),
        hand31=hand,
        family_means=family_means,
        joint_d_below_one=joint_d_below_one(x, refs),
        development_recognition_31=nearest_centroid(values, labels, means),
        learned=learned,
        sd_turbo=sd_turbo_benchmarks(),
    )
    if bindings != input_bindings():
        raise ValueError("an input changed during computation")
    return result


def pct(value):
    return "n/a" if value is None else f"{100 * value:.1f}"


def span(pair):
    return "n/a" if pair is None else f"[{100 * pair[0]:.1f}, {100 * pair[1]:.1f}]"


def report(result):
    lines = [
        "# TMLR revision diagnostics, version 2",
        "",
        "Retrospective analysis under",
        "[the plan](../../studies/painter_tmlr_diagnostics_v2/PLAN.md). Percentile intervals",
        "describe dependence on the 14 authored scenes or the finite reference panels.",
        "",
        "## Shared fraction, 31 features (%)",
        "",
        "| Configuration | observed [scenes] | faithful [scenes] | exact differences | "
        "obs < faithful |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for title, row in zip(s.TITLES, result["hand31"]):
        p, b = row["point"]["all31"], row["scene_bootstrap"]["all31"]
        lines.append(
            f"| {title} | {pct(p['observed'])} {span(b['observed'])} | "
            f"{pct(p['faithful'])} {span(b['faithful'])} | {pct(p['exact'])} | "
            f"{100 * b['observed_below_faithful']:.1f} |"
        )
    for name in ("clip", "csd"):
        lines += [
            "",
            f"## Proximity-gain shares, {name.upper()} (%)",
            "",
            "| Configuration | observed [scenes] | faithful | exact differences |",
            "| --- | --- | ---: | ---: |",
        ]
        for title, row in zip(s.TITLES, result["learned"][name]):
            p, b = row["prototype"]["point"], row["prototype"]["scene_bootstrap"]
            lines.append(
                f"| {title} | {pct(p['observed'])} {span(b['observed'])} | "
                f"{pct(p['faithful'])} | {pct(p['exact'])} |"
            )
    dev = result["development_recognition_31"]
    lines += [
        "",
        f"31-feature development recognition: macro {pct(dev['macro_accuracy'])}%, per painter "
        + ", ".join(pct(v) for v in dev["per_painter"]),
        "",
        "Joint resampling, P(D < 1): "
        + ", ".join(f"{t} {v:.3f}" for t, v in zip(s.TITLES, result["joint_d_below_one"])),
        "",
        "SD-Turbo: "
        + ", ".join(
            f"{k} faithful {pct(v['faithful'])}, exact {pct(v['exact'])}"
            for k, v in result["sd_turbo"].items()
        ),
        "",
    ]
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
        print("Exact TMLR diagnostics v2 replay passed")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    with REPORT_PATH.open("x") as stream:
        stream.write(markdown)
    print("TMLR diagnostics v2 written")


if __name__ == "__main__":
    main()
