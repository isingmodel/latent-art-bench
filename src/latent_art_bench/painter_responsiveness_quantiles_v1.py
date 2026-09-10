"""An exact-weight CDF corrigendum; no images, generation, or primary reanalysis."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.metadata
import json
import math
import platform
import re
import subprocess
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path

import matplotlib.pyplot as plt

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    digest,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_responsiveness_v2 import analysis as original
from latent_art_bench.painter_responsiveness_v2 import report

NAMESPACE = "painter_responsiveness_quantiles_v1"
RUN_ID = "prqv1-20260908"
MANIFESTS = Path("data/manifests") / NAMESPACE / RUN_ID
REPORTS = Path("reports") / NAMESPACE / RUN_ID
RUNS = ("prv2-oauth-recovery-20260908", "prv2-oauth-20260908")
ORIGINAL = Path("data/manifests/painter_responsiveness_v2")
RUNTIME = ("numpy", "scipy", "matplotlib", "Pillow", "PyWavelets", "scikit-image", "pydantic")
QUANTILES = (Fraction(1, 10), Fraction(1, 2), Fraction(9, 10))
KEYS = ("pipeline", "painter_id", "arm", "polarity", "reference_weighting", "weighting")


def weights(rows, fields):
    """Recover the declared rational design mass, not its rounded binary encoding."""
    if fields not in ((), ("content_class",), ("content_class", "polarity")):
        raise ValueError("undeclared rational weighting rule")
    levels = ({(c, p) for c in original.CLASSES for p in ("muted", "vivid")}
              if fields == ("content_class", "polarity") else
              {(c,) for c in original.CLASSES} if fields else {()})
    counts = Counter(tuple(row[field] for field in fields) for row in rows)
    if set(counts) != levels:
        return None
    return [Fraction(1, len(levels) * counts[tuple(row[f] for f in fields)]) for row in rows]


def quantiles(values, mass):
    """Return the first ordered value at CDF >= q, with exact rational accumulation."""
    if (not values or len(values) != len(mass)
            or any(not math.isfinite(v) for v in values)
            or any(not isinstance(w, Fraction) or w <= 0 for w in mass)):
        raise ValueError("finite values and positive exact rational weights are required")
    total, cumulative, result = sum(mass), Fraction(0), []
    for value, weight in sorted(zip(values, mass, strict=True), key=lambda pair: pair[0]):
        cumulative += weight
        while len(result) < len(QUANTILES) and cumulative >= QUANTILES[len(result)] * total:
            result.append(value)
    if len(result) != 3:
        raise ValueError("the exact CDF did not reach all requested quantiles")
    return result


def _identity(row):
    return {key: row[key] for key in KEYS if key in row}


def _protected(value):
    """Everything except the explicitly corrected endpoints must stay byte-equivalent."""
    result = copy.deepcopy(value)
    for row in result["reference_context"]["envelopes"]:
        if row.get("summary") is not None:
            row["summary"].pop("quantiles_10_50_90")
    for row in result["reference_context"]["comparisons"]:
        if row.get("generated_summary") is not None:
            row["generated_summary"].pop("quantiles_10_50_90")
        for field in ("generated_mass_in_reference_central80",
                      "reference_mass_in_generated_central80"):
            row.pop(field, None)
    return digest(result)


def _update_quantiles(row, summary, source, mass, changes, kind, identity_field):
    before = list(summary["quantiles_10_50_90"])
    after = quantiles([r["value"] for r in source], mass)
    summary["quantiles_10_50_90"] = after
    if before != after:
        changes.append(dict(
            kind=kind, **_identity(row), before=before, corrected=after,
            changed_probabilities=[str(q) for q, a, b in zip(QUANTILES, before, after, strict=True)
                                   if a != b],
            members=[dict(identity=r[identity_field], weight=str(w))
                     for r, w in zip(source, mass, strict=True)],
        ))
    return before, after


def _accepted(rows, mass, bounds, identity_field):
    accepted = [i for i, row in enumerate(rows) if bounds[0] <= row["value"] <= bounds[2]]
    return (sum((mass[i] for i in accepted), Fraction(0)) / sum(mass),
            [rows[i][identity_field] for i in accepted])


def correct(value):
    """Correct saved descriptive endpoints and preserve every other supplied result."""
    if value["reference_context"] != original._reference_bridge(
        value["generated_chroma"], value["reference_chroma"]
    ):
        raise ValueError("the frozen reference context does not reproduce from its saved members")
    result = copy.deepcopy(value)
    quantile_changes, coverage_changes, ranges = [], [], {}
    for row in result["reference_context"]["envelopes"]:
        source = [r for r in result["reference_chroma"]
                  if (r["pipeline"], r["painter_id"]) == (row["pipeline"], row["painter_id"])]
        if [r["image_id"] for r in source] != row["image_ids"]:
            raise ValueError("reference membership order differs from the declared envelope")
        mass = weights(source, () if row["weighting"] == "empirical_reference_mixture"
                       else ("content_class",))
        if mass is None:
            if row.get("summary") is not None:
                raise ValueError("an unavailable reference stratum cannot acquire a quantile")
            continue
        if row["weights"] != [float(w) for w in mass]:
            raise ValueError("stored reference weights differ from the declared design")
        before, after = _update_quantiles(row, row["summary"], source, mass, quantile_changes,
                                          "reference_envelope", "image_id")
        ranges[row["pipeline"], row["painter_id"], row["weighting"]] = source, mass, before, after
    for row in result["reference_context"]["comparisons"]:
        if row.get("generated_summary") is None:
            continue
        source = [r for r in result["generated_chroma"]
                  if r["status"] == "measured" and (r["pipeline"], r["arm"])
                  == (row["pipeline"], row["arm"])
                  and (row["polarity"] == "equal_polarity_mixture"
                       or r["polarity"] == row["polarity"])]
        if [r["request_id"] for r in source] != row["request_ids"]:
            raise ValueError("generated membership differs from the declared comparison")
        fields = (("content_class", "polarity") if row["polarity"] == "equal_polarity_mixture"
                  else ("content_class",))
        mass = weights(source, fields)
        if mass is None or row["generated_weights"] != [float(w) for w in mass]:
            raise ValueError("stored generated weights differ from the declared design")
        before, after = _update_quantiles(row, row["generated_summary"], source, mass,
                                          quantile_changes, "generated_summary", "request_id")
        refs, ref_mass, old_ref, new_ref = ranges[
            row["pipeline"], row["painter_id"], row["reference_weighting"]]
        for field, sample, sample_mass, old_bounds, new_bounds, identity_field in (
            ("generated_mass_in_reference_central80", source, mass, old_ref, new_ref, "request_id"),
            ("reference_mass_in_generated_central80", refs, ref_mass, before, after, "image_id"),
        ):
            old_mass, old_ids = _accepted(sample, sample_mass, old_bounds, identity_field)
            new_mass, new_ids = _accepted(sample, sample_mass, new_bounds, identity_field)
            if old_ids != new_ids:
                coverage_changes.append(dict(
                    **_identity(row), field=field, before=row[field], corrected=float(new_mass),
                    before_exact_mass=str(old_mass), corrected_exact_mass=str(new_mass),
                    removed_members=[i for i in old_ids if i not in new_ids],
                    added_members=[i for i in new_ids if i not in old_ids],
                ))
                row[field] = float(new_mass)
            # Preserve unaffected binary floating sums rather than cosmetically rewriting them.
    protected = _protected(value)
    if _protected(result) != protected:
        raise ValueError("the correction altered an endpoint outside its declared scope")
    return result, dict(
        quantile_changes=quantile_changes, coverage_changes=coverage_changes,
        protected_result_sha256=protected,
        unchanged=dict(primary_inference=True, arm_means=True, wasserstein_distances=True,
                       input_features=True, availability=True),
        counts=dict(quantile_records_changed=len(quantile_changes),
                    reference_envelopes_changed=sum(r["kind"] == "reference_envelope"
                                                   for r in quantile_changes),
                    generated_summaries_changed=sum(r["kind"] == "generated_summary"
                                                   for r in quantile_changes),
                    central80_endpoints_changed=sum("1/10" in r["changed_probabilities"]
                                                   or "9/10" in r["changed_probabilities"]
                                                   for r in quantile_changes),
                    coverage_records_changed=len(coverage_changes)),
    )


def source_paths():
    paths = [Path("src/latent_art_bench") / (NAMESPACE + ".py"),
             Path("tests") / ("test_" + NAMESPACE + ".py"),
             Path("studies") / NAMESPACE / "PROTOCOL.md", Path("pyproject.toml"), Path("uv.lock")]
    paths += [Path("src/latent_art_bench") / name for name in (
        "io.py", "painter_feature_generation_v2/artifacts.py",
        "painter_prompt_study_v1/common.py", "painter_responsiveness_v2/analysis.py",
        "painter_responsiveness_v2/report.py", "painter_responsiveness_v1/inference.py",
        "painter_responsiveness_v1/design.py", "painter_distribution_study_v1/study.py",
        "painter_feature_generation_v2/features.py",
    )]
    paths += [ORIGINAL / run / filename for run in RUNS for filename in
              ("analysis.json", "analysis_receipt.json", "collection_receipt.json", "freeze.json")]
    return sorted(paths)


def prepare(root):
    if (root / MANIFESTS).exists() or (root / REPORTS).exists():
        raise ValueError("the correction namespace already exists; never reopen it")
    paths = source_paths()
    commit = committed(root, paths)
    for run in RUNS:
        receipt = read_json(root / ORIGINAL / run / "analysis_receipt.json")
        if receipt["analysis_sha256"] != hash_file(root / ORIGINAL / run / "analysis.json"):
            raise ValueError("original analysis differs from its terminal publication receipt")
        if read_json(root / ORIGINAL / run / "collection_receipt.json")["terminal"] is not True:
            raise ValueError("both original collections must be closed")
    freeze = dict(schema="painter-responsiveness-quantile-correction/1", run_id=RUN_ID,
                  recorded_git_commit=commit, inputs=bindings(root, paths), runs=list(RUNS),
                  environment=dict(python=platform.python_version(), **{
                      name: importlib.metadata.version(name) for name in RUNTIME}))
    publish(root / MANIFESTS / "freeze.json", freeze)
    return dict(status="prepared", recorded_git_commit=commit,
                next="Commit freeze.json before build; no image or generation work is authorized.")


def _commit_bindings(root, freeze):
    commit = freeze.get("recorded_git_commit", "")
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("the correction requires an exact recorded Git commit")
    for row in freeze["inputs"]:
        blob = subprocess.run(["git", "show", f"{commit}:{row['path']}"],
                              cwd=root, capture_output=True)
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != row["sha256"]:
            raise ValueError("bound input differs from the recorded Git commit: " + row["path"])


def verify(root):
    freeze = read_json(root / MANIFESTS / "freeze.json")
    committed(root, [MANIFESTS / "freeze.json"])
    if freeze["run_id"] != RUN_ID or freeze["runs"] != list(RUNS):
        raise ValueError("the correction scope changed")
    verify_bindings(root, freeze["inputs"])
    if {Path(r["path"]) for r in freeze["inputs"]} != set(source_paths()):
        raise ValueError("the correction does not bind its exact source/input inventory")
    _commit_bindings(root, freeze)
    if set(freeze["environment"]) != {"python", *RUNTIME}:
        raise ValueError("the correction must bind its complete rendering runtime")
    for name, version in freeze["environment"].items():
        actual = platform.python_version() if name == "python" else importlib.metadata.version(name)
        if actual != version:
            raise ValueError("the correction runtime changed")
    return freeze


def _csv(path, rows):
    fields = sorted({key for row in rows for key in row}) or ["status"]
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True, ensure_ascii=False)
                             if isinstance(v, (dict, list)) else v for k, v in row.items()})


def render(root, output):
    output.mkdir(parents=True, exist_ok=False)
    audits = {}
    text = ["# Weighted empirical quantile correction", "",
            "This corrigendum corrects floating-point CDF boundary assignment in descriptive "
            "reference and generated chroma quantiles. Quantiles use exact rational design weights "
            "and the first value with CDF at least 1/10, 1/2 or 9/10. Original artifacts remain "
            "unchanged. Primary inference, means, Wasserstein distances and image membership "
            "are preserved exactly. No images were opened or generated.", "",
            "| Collection | Quantile records changed | Central-80 endpoint records | "
            "Coverage records changed |", "| --- | ---: | ---: | ---: |"]
    for run in RUNS:
        corrected, audit = correct(read_json(root / ORIGINAL / run / "analysis.json"))
        audits[run] = audit
        target = output / run
        (target / "plots").mkdir(parents=True)
        _csv(target / "quantile_corrections.csv", audit["quantile_changes"])
        _csv(target / "coverage_corrections.csv", audit["coverage_changes"])
        with plt.rc_context(report.RC):
            report._save(report._reference(corrected), target, "original_chroma_context")
        counts = audit["counts"]
        text.append(f"| {run} | {counts['quantile_records_changed']} | "
                    f"{counts['central80_endpoints_changed']} | "
                    f"{counts['coverage_records_changed']} |")
    for run in RUNS:
        text += ["", f"## {run}", "",
                 f"![Corrected original chroma context]({run}/plots/original_chroma_context.png)",
                 "",
                 f"[Affected quantiles]({run}/quantile_corrections.csv); "
                 f"[Affected coverage values]({run}/coverage_corrections.csv). "
                 "Segments are empirical 10th–90th percentile ranges, not confidence intervals. "
                 "Unavailable and selected ancillary distributions keep their original status."]
    text += ["", "Counts concern records: shared generated summaries occur under more than one "
             "painter/reference-weighting comparison. All changed members and exact fractional "
             "weights are retained in corrections.json. Coverage is updated only when corrected "
             "range endpoints change accepted members; unaffected floating sums are preserved. "
             "The original/generated comparison remains computational and descriptive, without "
             "independent human, capture or oeuvre validation.", ""]
    (output / "REPORT.md").write_text("\n".join(text), encoding="utf-8")
    return dict(schema="painter-responsiveness-quantile-correction-result/1", runs=audits)


def build(root, *, check=False):
    freeze = verify(root)
    if check:
        receipt = read_json(root / MANIFESTS / "receipt.json")
        if (receipt["run_id"] != RUN_ID or receipt["terminal"] is not True
                or receipt["recorded_git_commit"] != freeze["recorded_git_commit"]):
            raise ValueError("the correction receipt identity changed")
        if receipt["freeze_sha256"] != hash_file(root / MANIFESTS / "freeze.json"):
            raise ValueError("the correction freeze changed")
        verify_bindings(root, receipt["outputs"])
        with tempfile.TemporaryDirectory(prefix="quantile-correction-") as temporary:
            replay = Path(temporary) / "report"
            result = render(root, replay)
            original_paths = sorted(p.relative_to(root / REPORTS)
                                    for p in (root / REPORTS).rglob("*") if p.is_file())
            replay_paths = sorted(p.relative_to(replay) for p in replay.rglob("*") if p.is_file())
            if replay_paths != original_paths or any(hash_file(replay / p) !=
                                                      hash_file(root / REPORTS / p)
                                                      for p in replay_paths):
                raise ValueError("the corrected report does not replay byte-for-byte")
            if result != read_json(root / MANIFESTS / "corrections.json"):
                raise ValueError("corrected numeric results do not replay")
        return dict(status="verified", reports=len(original_paths), runs=list(RUNS))
    if (root / MANIFESTS / "receipt.json").exists():
        raise ValueError("correction publication is terminal")
    result = render(root, root / REPORTS)
    publish(root / MANIFESTS / "corrections.json", result)
    paths = [MANIFESTS / "corrections.json"] + [p.relative_to(root) for p in
             (root / REPORTS).rglob("*") if p.is_file()]
    publish(root / MANIFESTS / "receipt.json", dict(
        run_id=RUN_ID, recorded_git_commit=freeze["recorded_git_commit"],
        freeze_sha256=hash_file(root / MANIFESTS / "freeze.json"), outputs=bindings(root, paths),
        new_images=0, new_feature_extractions=0, terminal=True,
    ))
    return dict(status="published", reports=len(paths) - 1,
                changes={run: result["runs"][run]["counts"] for run in RUNS})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "build", "check"))
    command = parser.parse_args().command
    root = Path.cwd()
    result = prepare(root) if command == "prepare" else build(root, check=command == "check")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
