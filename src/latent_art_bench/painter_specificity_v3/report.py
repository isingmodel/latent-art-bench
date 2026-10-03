"""Write-once v3 analysis (``python -m latent_art_bench.painter_specificity_v3.report``).

It assembles the new collection, the v3 reference panels and September's no-clause and generic
arms in each representation (31 features, full view and central square; CLIP; CSD), runs the
prespecified analysis (``analysis.analyze``) and the per-group predictions, writes
``reports/painter_specificity_v3/analysis.json`` and ``REPORT.md`` once, and ``check`` replays
them exactly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.statistics import transform
from latent_art_bench.painter_specificity_v3 import analysis
from latent_art_bench.painter_specificity_v3 import study as s
from latent_art_bench.painter_specificity_v3.panel import GROUP_TITLES, GROUPS, PAINTERS

OUT = s.ROOT / "reports" / s.NS
REFS = s.ROOT / "data/manifests" / s.NS / "refs-20261002"
SCALER = s.first.SCALER
REPRESENTATIONS = ("hand31", "hand31_square", "clip", "csd")


def _requests() -> list[dict]:
    return s.rows(s.DATA / "requests.jsonl")


def generated(rep: str) -> np.ndarray:
    """(6 configurations, 14 scenes, 2 repeats, 10 arms, p), NaN where no image or vector."""
    requests = _requests()
    index = {r["id"]: (s.MODELS.index(r["model"]), r["scene"], r["repeat"], s.ARMS.index(r["arm"]))
             for r in requests}
    if rep.startswith("hand31"):
        key = "square_values" if rep == "hand31_square" else "values"
        scaler = read_json(SCALER)
        x = np.full((6, 14, 2, 10, 31), np.nan)
        for row in s.rows(s.DATA / "measurements.jsonl"):
            if row["status"] == "measured":
                x[index[row["id"]]] = transform(np.array(row[key]), scaler)
        return x
    receipt = read_json(s.DATA / f"extraction_{rep}.json")
    path = s.DATA / f"embeddings_{rep}.npz"
    if hash_file(path) != receipt["embeddings_sha256"]:
        raise ValueError("embedding archive changed")
    values = np.load(path)["embeddings"].astype(np.float64)
    x = np.full((6, 14, 2, 10, values.shape[1]), np.nan)
    for row, vector in zip(receipt["rows"], values):
        x[index[row["id"]]] = vector
    return x


def references(rep: str) -> dict[str, list[np.ndarray]]:
    """Group -> four (works, p) arrays, in panel order."""
    if rep.startswith("hand31"):
        key = "square_values" if rep == "hand31_square" else "values"
        scaler = read_json(SCALER)
        rows = [r for r in read_jsonl(REFS / "features.jsonl") if r["status"] == "measured"]
        by = {p.painter_id: transform(np.array([r[key] for r in rows
                                               if r["painter_id"] == p.painter_id]), scaler)
              for p in PAINTERS}
    else:
        receipt = read_json(REFS / f"extraction_{rep}.json")
        if hash_file(REFS / f"embeddings_{rep}.npz") != receipt["embeddings_sha256"]:
            raise ValueError("reference embedding archive changed")
        values = np.load(REFS / f"embeddings_{rep}.npz")["embeddings"].astype(np.float64)
        painters = np.array([r["painter_id"] for r in receipt["rows"]])
        by = {p.painter_id: values[painters == p.painter_id] for p in PAINTERS}
    return {g: [by[p.painter_id] for p in PAINTERS if p.group == g] for g in GROUPS}


def september(rep: str) -> np.ndarray:
    """September's no-clause and generic arms: (6, 14, 2, 2, p)."""
    if rep.startswith("hand31"):
        from latent_art_bench.painter_specificity_measurement_v1.workflow import load

        x, _ = load(square=rep == "hand31_square")
    else:
        from latent_art_bench import painter_learned_audit_v1 as learned

        x, _, _ = learned.arrays(rep)
    return x[:, :, :, :2]


def compute(draws: int = analysis.DRAWS) -> dict:
    result = dict(
        collection=dict(run=s.RUN, models=list(s.MODELS), titles=list(s.TITLES),
                        arms=list(s.ARMS), names=list(s.NAMES),
                        groups={g: dict(title=GROUP_TITLES[g], arms=list(s.GROUP_ARMS[g]))
                                for g in GROUPS}),
        representations={},
    )
    for rep in REPRESENTATIONS:
        x, refs, old = generated(rep), references(rep), september(rep)
        means = {g: np.array([r.mean(axis=0) for r in refs[g]]) for g in GROUPS}
        out = analysis.analyze(x, refs, s.GROUP_ARMS, september=old, draws=draws)
        out["predictions_from_september_generic"] = analysis.predictions(old[:, :, :, 1], means)
        out["reference_counts"] = {g: [len(r) for r in refs[g]] for g in GROUPS}
        result["representations"][rep] = out
    result["inputs"] = {str(p.relative_to(s.ROOT)): hash_file(p) for p in inputs()}
    return result


def inputs() -> list[Path]:
    paths = [s.DATA / n for n in ("requests.jsonl", "collection.json", "measurements.jsonl",
                                  "measurement_receipt.json")]
    paths += [REFS / n for n in ("features.jsonl", "frame.jsonl")]
    for rep in ("clip", "csd"):
        paths += [s.DATA / f"embeddings_{rep}.npz", REFS / f"embeddings_{rep}.npz"]
    paths += sorted((s.ROOT / "src/latent_art_bench" / s.NS).glob("*.py"))
    return paths


def _clean(value):
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return _clean(value.tolist())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def render(result: dict) -> str:
    lines = ["# Painter specificity v3: two further painter groups", "",
             "Prespecified analysis (`studies/painter_specificity_v3/PROTOCOL.md`),",
             "written once by",
             "`python -m latent_art_bench.painter_specificity_v3.report analyze`.", ""]
    for rep, out in result["representations"].items():
        lines += [f"## {rep}", ""]
        if not out["available"]:
            lines += [f"Unavailable: complete scenes {out['complete_scenes']}.", ""]
            continue
        c, d = out["closeness"], out["dose_response"]
        lines += [
            f"- H1 closeness (century minus Hudson shared fraction): "
            f"{c['pooled_difference']:.3f}, 95% {np.round(c['pooled_ci95'], 3).tolist()}, "
            f"supported: {c['supported']}",
            f"- H2 dose-response (Mantel Spearman, noise-corrected references): "
            f"{d['pooled_spearman']:.3f}, exact p {d['exact_p_one_sided']:.5f}, "
            f"supported: {d['supported']}",
            "", "| Group | Configuration | Shared | Faithful | Exact | beta | D | Alignment |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for g, rows in out["groups"].items():
            for title, row in zip(result["collection"]["titles"], rows):
                lines.append(
                    f"| {GROUP_TITLES[g]} | {title} | {row['shared_fraction']:.3f} | "
                    f"{row['faithful_shared_fraction']:.3f} | {row['exact_shared_fraction']:.3f} | "
                    f"{row['beta']:.3f} | {row['D']:.3f} | {row['alignment_ratio']:.3f} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def analyze() -> None:
    if (OUT / "analysis.json").exists():
        raise FileExistsError("the v3 analysis is written once; use check")
    result = _clean(compute())
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "analysis.json").open("x") as stream:
        json.dump(result, stream, indent=1, sort_keys=True, allow_nan=False)
        stream.write("\n")
    with (OUT / "REPORT.md").open("x") as stream:
        stream.write(render(result))


def check() -> int:
    recorded = read_json(OUT / "analysis.json")
    for path, sha in recorded["inputs"].items():
        if hash_file(s.ROOT / path) != sha:
            print(f"input changed: {path}", file=sys.stderr)
            return 1
    replay = json.loads(json.dumps(_clean(compute()), sort_keys=True, allow_nan=False))
    if replay != recorded:
        print("replay differs from the recorded analysis", file=sys.stderr)
        return 1
    print("ok: v3 analysis replays exactly")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("analyze", "check"))
    args = parser.parse_args(argv)
    if args.action == "analyze":
        analyze()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
