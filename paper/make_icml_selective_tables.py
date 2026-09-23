"""Render complete frozen selective-attribution outcomes, without fitting.

--check verifies both source digests, reconstructs full/deleted-scene accounting
from retained decisions and compares the two generated TeX files exactly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/painter_selective_attribution_v1"
INPUT_SHA = "f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826"
ANALYSIS_SHA = "f725b32b91f38fa8afd85454b3a6f0c8eb7464f5337b18373ce8c8f53e39fa2c"
AUDIT_SHA = "e3f26efb7286ad592e5ec30a50dd937690c29852d690c94b3baf09f31ae22569"
MODELS = (
    "gpt-image-1", "gpt-image-2", "gpt-image-2.5-flare", "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image", "black-forest-labs/flux.2-max",
)
TITLES = ("GPT Image 1", "GPT Image 2", "GPT 2.5 Flare", "GPT 2.5 Sunburst",
          "Nano Banana 2", "FLUX.2 Max")
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
ARMS = ("free", "generic", *ARTISTS)
ENCODERS = ("clip", "csd")
SETTINGS = (
    ("original", "primary", "Original sources / primary prototypes"),
    ("original", "development", "Original sources / development prototypes"),
    ("audited_region", "primary", "Audited regions / primary prototypes"),
    ("audited_region", "development", "Audited regions / development prototypes"),
)
PRIMARY = "csd/original/primary"
CRITERIA = (
    "every_configuration_coverage_at_least_half",
    "every_painter_accepted_in_every_configuration",
    "positive_mean_baseline_minus_gate", "positive_mean_margin_minus_gate",
)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(left, right, message):
    if left is None or right is None:
        require(left is right, message)
    else:
        require(math.isfinite(left) and math.isfinite(right)
                and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12), message)


def risk(wrong, count):
    return None if count == 0 else wrong / count


def complete_mean(values):
    return None if any(v is None for v in values) else sum(values) / len(values)


def difference(left, right):
    return None if left is None or right is None else left - right


def verify_named(summary, rows, accepted_ids):
    n = len(rows)
    chosen = [r for r in rows if r["id"] in accepted_ids]
    rejected = [r for r in rows if r["id"] not in accepted_ids]
    def wrong(rs):
        return sum(r["top1"] != r["prompted_artist"] for r in rs)
    counts = dict(count=n, accepted_count=len(chosen), abstained_count=len(rejected),
                  correct_count=n-wrong(rows), incorrect_count=wrong(rows),
                  accepted_correct=len(chosen)-wrong(chosen), accepted_incorrect=wrong(chosen),
                  abstained_correct=len(rejected)-wrong(rejected),
                  abstained_incorrect=wrong(rejected))
    for key, value in counts.items():
        require(summary[key] == value, "named count: " + key)
    for key, value in dict(coverage=risk(len(chosen), n),
                           unrestricted_error=risk(wrong(rows), n),
                           accepted_error=risk(wrong(chosen), len(chosen)),
                           abstained_error=risk(wrong(rejected), len(rejected))).items():
        close(summary[key], value, "named rate: " + key)
    for key, pool in (("confusion", rows), ("accepted_confusion", chosen),
                      ("abstained_confusion", rejected)):
        expected = [[sum(r["prompted_artist"] == a and r["top1"] == b for r in pool)
                     for b in ARTISTS] for a in ARTISTS]
        require(summary[key] == expected, "complete confusion accounting")
    require([r["painter"] for r in summary["per_painter"]] == list(ARTISTS), "painter order")
    for artist, painter in zip(ARTISTS, summary["per_painter"]):
        pool = [r for r in rows if r["prompted_artist"] == artist]
        chosen_a = [r for r in chosen if r["prompted_artist"] == artist]
        rejected_a = [r for r in rejected if r["prompted_artist"] == artist]
        require(painter["count"] == len(pool) and painter["accepted_count"] == len(chosen_a),
                "per-painter acceptance count")
        for key, value in dict(coverage=risk(len(chosen_a), len(pool)),
                               unrestricted_error=risk(wrong(pool), len(pool)),
                               accepted_error=risk(wrong(chosen_a), len(chosen_a)),
                               abstained_error=risk(wrong(rejected_a), len(rejected_a))).items():
            close(painter[key], value, "per-painter risk/coverage")


def verify_control(summary, rows, accepted_ids, ties):
    accepted = [r for r in rows if r["id"] in accepted_ids]
    require(summary["count"] == len(rows) and summary["accepted_count"] == len(accepted),
            "control acceptance census")
    close(summary["attribution_rate"], risk(len(accepted), len(rows)), "control attribution rate")
    for key, pool in (("predicted_artist_counts", rows), ("accepted_artist_counts", accepted)):
        require(summary[key] == [sum(r["top1"] == a for r in pool) for a in ARTISTS],
                "control attribution artist census")
    require(summary["numeric_cutoff_ties"] == ties, "control threshold ties")


def verify_pool(saved, rows, scenes, full=False):
    require(saved["retained_scenes"] == scenes, "retained scene set")
    pool = [r for r in rows if r["scene"] in scenes]
    named = [r for r in pool if r["prompted_artist"] is not None]
    chosen_ids = {r["id"] for r in named if r["reference_gate_accept"]}
    ordered = sorted(named, key=lambda r: (-r["ordinary_margin"], r["id"]))
    k = len(chosen_ids)
    margin_ids = {r["id"] for r in ordered[:k]}
    cutoff = ordered[k-1]["ordinary_margin"] if k else None
    tied = [r for r in named if cutoff is not None and r["ordinary_margin"] == cutoff]
    expected_cutoff = dict(k=k, cutoff=cutoff, boundary_id=ordered[k-1]["id"] if k else None,
                           cutoff_ties=len(tied),
                           cutoff_ties_accepted=sum(r["id"] in margin_ids for r in tied))
    require(saved["comparator_cutoff"] == expected_cutoff, "fixed margin cutoff/tie census")
    verify_named(saved["reference_gate"], named, chosen_ids)
    verify_named(saved["margin_comparator"], named, margin_ids)
    for key, expected in (
        ("baseline_minus_gate_risk", difference(saved["reference_gate"]["unrestricted_error"],
                                               saved["reference_gate"]["accepted_error"])),
        ("margin_minus_gate_risk", difference(saved["margin_comparator"]["accepted_error"],
                                             saved["reference_gate"]["accepted_error"])),
    ):
        close(saved[key], expected, "paired selective-risk reduction")
    for arm in ARMS[:2]:
        controls = [r for r in pool if r["arm"] == arm]
        gate_ids = {r["id"] for r in controls if r["reference_gate_accept"]}
        cm_ids = {r["id"] for r in controls if cutoff is not None
                  and r["ordinary_margin"] >= cutoff}
        ties = sum(cutoff is not None and r["ordinary_margin"] == cutoff for r in controls)
        verify_control(saved["controls"][arm]["reference_gate"], controls, gate_ids, None)
        verify_control(saved["controls"][arm]["margin_comparator"], controls, cm_ids, ties)
        if full:
            require(all(r["margin_comparator_accept"] == (r["id"] in cm_ids)
                        for r in controls), "stored control margin decisions")
    require(saved["named_reason_counts"] == {
        reason: sum(r["gate_reason"] == reason for r in named) for reason in (
            "accepted", "empty_set", "multiple_labels", "singleton_disagrees_with_top1")},
        "named abstention reason census")
    require(saved["named_top_ties"] == sum(r["top_score_tie"] for r in named), "score tie census")
    if full:
        require(all(r["margin_comparator_accept"] == (r["id"] in margin_ids) for r in named),
                "stored named margin decisions")


def verify_range(saved, values):
    require(len(saved["values"]) == len(values), "deletion range count")
    for actual, expected in zip(saved["values"], values):
        close(actual, expected, "deletion range value")
    missing = sum(v is None for v in values)
    require(saved["missing_count"] == missing, "deletion missing-value census")
    if missing:
        require(saved["range"] is None, "missing deletion must keep range undefined")
    else:
        for actual, expected in zip(saved["range"], (min(values), max(values))):
            close(actual, expected, "complete deletion range")


def verify_model(model, quantiles):
    rows = model["observations"]
    require(len(rows) == 168 and len({r["id"] for r in rows}) == 168, "all 168 generated queries")
    require({(r["scene"], r["repeat"], r["arm"]) for r in rows}
            == {(s, r, a) for s in range(14) for r in range(2) for a in ARMS},
            "complete generated request cells")
    for row in rows:
        scores = row["scores"]
        require(len(scores) == 4 and all(math.isfinite(x) for x in scores), "finite class scores")
        pred = max(range(4), key=lambda i: scores[i])
        require(row["top1"] == ARTISTS[pred], "fixed top-1 tie rule")
        truth = row["arm"] if row["arm"] in ARTISTS else None
        require(row["prompted_artist"] == truth, "known prompt-label mapping")
        nonconformity = [max(scores[b] for b in range(4) if b != a)-scores[a] for a in range(4)]
        for actual, expected in zip(row["nonconformity"], nonconformity):
            close(actual, expected, "nonconformity value")
        candidates = [ARTISTS[a] for a in range(4) if quantiles[a]["infinite"]
                      or nonconformity[a] <= quantiles[a]["threshold"]]
        require(row["candidates"] == candidates, "calibrated candidate set")
        chosen = candidates == [row["top1"]]
        reason = ("accepted" if chosen else "empty_set" if len(candidates) == 0
                  else "multiple_labels" if len(candidates) > 1
                  else "singleton_disagrees_with_top1")
        require(row["reference_gate_accept"] == chosen and row["gate_reason"] == reason,
                "frozen gate rule")
        close(row["ordinary_margin"], sorted(scores)[-1]-sorted(scores)[-2], "ordinary margin")
        require(row["top_score_tie"] == (scores.count(max(scores)) > 1), "top-score ties")
    verify_pool(model, rows, list(range(14)), full=True)
    deletions = model["scene_deletions"]
    require([r["deleted_scene"] for r in deletions] == list(range(14)), "all 14 scene deletions")
    for scene, deletion in enumerate(deletions):
        verify_pool(deletion, rows, [s for s in range(14) if s != scene])
    for metric in ("baseline_minus_gate_risk", "margin_minus_gate_risk"):
        verify_range(model["influence"][metric], [d[metric] for d in deletions])
    for metric, key in (("gate_coverage", "coverage"), ("gate_accepted_error", "accepted_error")):
        verify_range(model["influence"][metric], [d["reference_gate"][key] for d in deletions])


def verify_summary(summary, models):
    require(len(models) == 6, "all six configurations required for every mean")
    mean_b = complete_mean([m["baseline_minus_gate_risk"] for m in models])
    mean_m = complete_mean([m["margin_minus_gate_risk"] for m in models])
    for key, value in (("mean_baseline_minus_gate_risk", mean_b),
                        ("mean_margin_minus_gate_risk", mean_m),
                        ("mean_coverage", complete_mean([
                            m["reference_gate"]["coverage"] for m in models])),
                        ("mean_gate_accepted_error", complete_mean([
                            m["reference_gate"]["accepted_error"] for m in models]))):
        close(summary[key], value, "equal-configuration mean")
    expected = dict(zip(CRITERIA, (
        all(m["reference_gate"]["coverage"] is not None
            and m["reference_gate"]["coverage"] >= .5 for m in models),
        all(p["accepted_count"] >= 1 for m in models for p in m["reference_gate"]["per_painter"]),
        mean_b is not None and mean_b > 0, mean_m is not None and mean_m > 0,
    )))
    require(summary["criteria"] == expected, "joint operational criteria")
    require(summary["joint_usefulness"] == all(expected.values()), "joint criterion verdict")
    require(summary["failed_criteria"] == [k for k in CRITERIA if not expected[k]],
            "complete failed criterion list")
    require(summary["missing_means"] == [name for name, val in (
        ("baseline_minus_gate", mean_b), ("margin_minus_gate", mean_m)) if val is None],
        "missing means must remain explicit")


def load():
    require(sha(BASE / "inputs.json") == INPUT_SHA, "frozen input SHA-256 changed")
    require(sha(BASE / "analysis.json") == ANALYSIS_SHA, "frozen analysis SHA-256 changed")
    inputs = json.loads((BASE / "inputs.json").read_text())
    data = json.loads((BASE / "analysis.json").read_text())
    require(data["inputs_sha256"] == INPUT_SHA and data["audit_sha256"] == AUDIT_SHA,
            "result input/audit provenance")
    require(data["descriptive_only"] and data["generated_image_coverage_guarantee"] is False,
            "scope declarations changed")
    require(data["specification"] == inputs["specification"]
            and data["specification"]["primary"] == PRIMARY
            and data["specification"]["alpha"] == .10, "frozen specification changed")
    for relative, expected in inputs["bindings"].items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT) and sha(path) == expected, "input binding: " + relative)
    required = {f"{e}/{v}/{t}" for e in ENCODERS for v, t, _ in SETTINGS}
    require(set(data["settings"]) == required, "all eight settings required")
    identities = {}
    for key, setting in data["settings"].items():
        models = setting["models"]
        require([r["model"] for r in models] == list(MODELS), "configuration order/census")
        cal = setting["calibration"]
        reference = [297, 106, 141, 105] if key.endswith("/primary") else [101, 36, 48, 36]
        calibration = [101, 36, 48, 36] if key.endswith("/primary") else [297, 106, 141, 105]
        require(cal["reference_counts"] == reference and cal["calibration_counts"] == calibration,
                "prototype/calibration panel census")
        for n, q, scores in zip(calibration, cal["quantiles"], cal["calibration_scores"]):
            rank = (9 * (n + 1) + 9) // 10
            require(q["n"] == n and q["rank"] == rank and len(scores) == n
                    and q["infinite"] == (rank > n), "fixed calibration order statistic")
            close(q["threshold"], None if rank > n else sorted(scores)[rank-1], "quantile value")
        for model in models:
            verify_model(model, cal["quantiles"])
            selected = [r["id"] for r in model["observations"]]
            prior = identities.setdefault(model["model"], selected)
            require(prior == selected, "query identities must match across all eight settings")
        verify_summary(setting["summary"], models)
        deletion_summaries = setting["scene_deletion_summaries"]
        require([d["deleted_scene"] for d in deletion_summaries] == list(range(14)),
                "all aggregate deletion summaries required")
        for scene, deleted in enumerate(deletion_summaries):
            verify_summary(deleted, [m["scene_deletions"][scene] for m in models])
        for metric, saved in setting["influence"].items():
            verify_range(saved, [d[metric] for d in deletion_summaries])
    require(data["primary_joint_usefulness"] == data["settings"][PRIMARY]["summary"][
        "joint_usefulness"], "primary verdict cannot be replaced by a sensitivity")
    return data


def number(value, places=1, signed=False):
    if value is None:
        return "--"
    value = 100 * value
    if round(value, places) == 0:
        value = 0.
    return f"${value:+.{places}f}$" if signed else f"${value:.{places}f}$"


def span(record, signed=False):
    if record["range"] is None:
        return "--"
    low, high = record["range"]
    f = "+.2f" if signed else ".1f"
    return f"$[{format(100*low, f)}, {format(100*high, f)}]$"


def provenance():
    return ["% Generated by paper/make_icml_selective_tables.py; retained outcomes only.",
            f"% analysis_sha256: {ANALYSIS_SHA}", f"% inputs_sha256: {INPUT_SHA}",
            f"% audit_sha256: {AUDIT_SHA}", f"% generator_sha256: {sha(Path(__file__))}"]


def table_start(caption, label, columns, font=r"\footnotesize", tabsep=3):
    return [r"\begin{table}[!htbp]", r"\caption{" + caption + "}",
            r"\label{" + label + "}", r"\centering" + font
            + r"\setlength{\tabcolsep}{" + str(tabsep) + "pt}",
            r"\begin{tabularx}{\linewidth}{" + columns + r"}\toprule"]


def table_end():
    return [r"\bottomrule\end{tabularx}", r"\end{table}"]


def main_table(data):
    lines = provenance() + table_start(
        r"Reference-calibrated abstention, primary CSD/original/primary setting. "
        r"Coverage is accepted queries out of 112 named images per configuration; "
        r"B is unrestricted top-1 error, A is accepted-gate error, and M is accepted error "
        r"for the ordinary-margin comparator at exactly the same coverage. All rates are "
        r"percentages. The fixed joint criterion fails coverage and painter retention; "
        r"zero accepted errors do not establish a reliable four-painter attribution rule.",
        "tab:selective-main", r"@{}Xrrrr@{}", tabsep=3)
    lines += [r"Configuration & Coverage & B & A & M\\\midrule"]
    for title, m in zip(TITLES, data["settings"][PRIMARY]["models"]):
        g, margin = m["reference_gate"], m["margin_comparator"]
        values = (g["coverage"], g["unrestricted_error"], g["accepted_error"],
                  margin["accepted_error"])
        lines.append(title + " & " + " & ".join(map(number, values)) + r"\\")
    lines += table_end()
    return "\n".join(lines) + "\n"


def criterion_tables(data):
    lines = [r"\subsection{Joint operational criteria and aggregate influence}",
             r"C1 requires at least 50\% named-image coverage in every configuration. "
             r"C2 requires at least one accepted image from every prompted painter in every "
             r"configuration. C3 and C4 require strictly positive equal-configuration "
             r"mean error reductions against unrestricted top-1 and the coverage-matched "
             r"margin comparator, respectively. All four must pass. An undefined mean "
             r"fails its criterion; it is never computed from a subset of configurations."]
    lines += table_start(
        r"All fixed criteria. O/A denote original/audited reference views and P/D denote "
        r"primary/development prototypes, with the other partition used for calibration. "
        r"Mean reductions are percentage points; positive values favor the gate. Every "
        r"setting fails its joint criterion. Missing means remain explicit.",
        "tab:selective-criteria", r"@{}Xrrccccc@{}")
    lines += [r"Setting & $B-A$ & $M-A$ & C1 & C2 & C3 & C4 & Missing\\\midrule"]
    for encoder in ENCODERS:
        for view, target, _ in SETTINGS:
            s = data["settings"][f"{encoder}/{view}/{target}"]["summary"]
            label = f"{encoder.upper()} / {'O' if view == 'original' else 'A'} / "
            label += "P" if target == "primary" else "D"
            criteria = ["Pass" if s["criteria"][k] else "Fail" for k in CRITERIA]
            lines.append(label + " & " + number(s["mean_baseline_minus_gate_risk"], 2, True)
                         + " & " + number(s["mean_margin_minus_gate_risk"], 2, True) + " & "
                         + " & ".join(criteria) + " & " + str(len(s["missing_means"])) + r"\\")
    lines += table_end()
    lines += table_start(
        r"Equal-configuration ranges over all 14 scene deletions. Prototypes and gate "
        r"thresholds remain fixed; the margin comparator is matched anew on the remaining "
        r"queries. Coverage and accepted error are percentages; reductions are percentage "
        r"points. These are influence ranges, not confidence intervals. U counts unavailable "
        r"deletions for each of the four displayed quantities, in column order.",
        "tab:selective-aggregate-influence", r"@{}Xrrrrl@{}", tabsep=2)
    lines += [r"Setting & Coverage & A error & $B-A$ & $M-A$ & U\\\midrule"]
    for encoder in ENCODERS:
        for view, target, _ in SETTINGS:
            inf = data["settings"][f"{encoder}/{view}/{target}"]["influence"]
            records = [inf[k] for k in (
                "mean_coverage", "mean_gate_accepted_error", "mean_baseline_minus_gate_risk",
                "mean_margin_minus_gate_risk")]
            label = f"{encoder.upper()} / {'O' if view == 'original' else 'A'} / "
            label += "P" if target == "primary" else "D"
            cells = [span(r, i > 1) for i, r in enumerate(records)]
            lines.append(label + " & " + " & ".join(cells) + " & "
                         + "/".join(str(r["missing_count"]) for r in records) + r"\\")
    lines += table_end() + [r"\FloatBarrier"]
    return lines


def setting_tables(data, view, target, title):
    slug = view.replace("_", "-") + "-" + target
    lines = [r"\clearpage\subsection{" + title + "}"]
    lines += table_start(
        title + r": complete coverage/error comparison. $K$ is accepted named queries out "
        r"of 112. B is unrestricted error; A and M are accepted error for the reference "
        r"gate and exact-coverage margin comparator. Rates are percentages and differences "
        r"are percentage points. Negative differences and undefined risks (--) are retained.",
        "tab:selective-risks-" + slug, r"@{}Xlrrrrrrr@{}", tabsep=3)
    lines += [r"Configuration & Encoder & $K$ & Coverage & B & A & M & $B-A$ & $M-A$\\\midrule"]
    for encoder in ENCODERS:
        for name, m in zip(TITLES, data["settings"][f"{encoder}/{view}/{target}"]["models"]):
            g, margin = m["reference_gate"], m["margin_comparator"]
            cells = [name, encoder.upper(), str(g["accepted_count"]), number(g["coverage"]),
                     number(g["unrestricted_error"]), number(g["accepted_error"]),
                     number(margin["accepted_error"]),
                     number(m["baseline_minus_gate_risk"], 2, True),
                     number(m["margin_minus_gate_risk"], 2, True)]
            lines.append(" & ".join(cells) + r"\\")
    lines += table_end()
    lines += table_start(
        title + r": painter retention and conditional error. Each painter cell is "
        r"accepted count/28 (the coverage fraction), followed by $\mid$ accepted error "
        r"in percent. -- denotes undefined error at zero acceptance, not zero error. "
        r"The original CSD GPT Image 1 result accepts 28 C\'ezanne images, one Monet, "
        r"one Pissarro and no Sisley; its zero aggregate accepted error therefore "
        r"does not cover all four painter conditions."
        if view == "original" and target == "primary" else
        title + r": painter retention and conditional error. Each cell is accepted "
        r"count/28 (coverage fraction), followed by $\mid$ accepted error in percent. "
        r"-- denotes undefined error at zero acceptance, not zero error.",
        "tab:selective-painters-" + slug,
        r"@{}Xl*{4}{>{\centering\arraybackslash}p{.153\linewidth}}@{}", tabsep=2)
    lines += [r"Configuration & Encoder & Monet & Sisley & Pissarro & C\'ezanne\\\midrule"]
    for encoder in ENCODERS:
        for name, m in zip(TITLES, data["settings"][f"{encoder}/{view}/{target}"]["models"]):
            cells = [str(p["accepted_count"]) + r"/28 $\mid$ " + number(p["accepted_error"])
                     for p in m["reference_gate"]["per_painter"]]
            lines.append(name + " & " + encoder.upper() + " & " + " & ".join(cells) + r"\\")
    lines += table_end()
    lines += table_start(
        title + r": control-arm named-attribution rates. Each entry is accepted count/28 "
        r"and percentage. A is the reference gate; M uses the named pool's numeric margin "
        r"cutoff inclusively, without splitting control ties. These prompts contain no "
        r"candidate artist name; acceptance is not evidence of a human-perceived style error.",
        "tab:selective-controls-" + slug, r"@{}Xlrrrr@{}", tabsep=3)
    lines += [r"Configuration & Encoder & Free A & Free M & Generic A & Generic M\\\midrule"]
    for encoder in ENCODERS:
        for name, m in zip(TITLES, data["settings"][f"{encoder}/{view}/{target}"]["models"]):
            cells = []
            for arm in ARMS[:2]:
                for rule in ("reference_gate", "margin_comparator"):
                    c = m["controls"][arm][rule]
                    cells.append(str(c["accepted_count"]) + "/28 ("
                                 + number(c["attribution_rate"]) + ")")
            lines.append(name + " & " + encoder.upper() + " & " + " & ".join(cells) + r"\\")
    lines += table_end() + [r"\FloatBarrier"]
    return lines


def influence_tables(data):
    lines = [r"\clearpage\subsection{Complete configuration-level scene-deletion ranges}",
             r"Each deletion removes both repeats and all six clauses for one scene, "
             r"leaving 104 named queries per configuration. The reference calibration "
             r"is unchanged; the margin threshold is rematched to the remaining gate "
             r"coverage. All 14 deletions contribute. An undefined deletion makes its "
             r"entire range undefined rather than shrinking the deletion set."]
    for encoder in ENCODERS:
        if encoder == "csd":
            lines.append(r"\clearpage")
        lines += table_start(
            encoder.upper() + r": all configuration-level scene-deletion ranges. Coverage "
            r"and A error are percentages; $B-A$ and $M-A$ are percentage points. "
            r"Ranges measure influence only. U lists unavailable deletions in column order.",
            "tab:selective-influence-" + encoder, r"@{}Xrrrrl@{}", tabsep=2)
        lines += [r"Configuration & Coverage & A error & $B-A$ & $M-A$ & U\\\midrule"]
        for view, target, title in SETTINGS:
            lines.append(r"\multicolumn{6}{@{}l}{\textit{" + title + r"}}\\")
            for name, m in zip(TITLES, data["settings"][f"{encoder}/{view}/{target}"]["models"]):
                records = [m["influence"][k] for k in (
                    "gate_coverage", "gate_accepted_error", "baseline_minus_gate_risk",
                    "margin_minus_gate_risk")]
                cells = [span(r, i > 1) for i, r in enumerate(records)]
                lines.append(name + " & " + " & ".join(cells) + " & "
                             + "/".join(str(r["missing_count"]) for r in records) + r"\\")
        lines += table_end() + [r"\FloatBarrier"]
    return lines


def appendix(data):
    lines = provenance() + [r"\clearpage\subsection{Complete selective-attribution results}",
                            r"\label{app:selective-results}",
                            r"The primary CSD/original/primary setting and all seven "
                            r"sensitivities are retained. A denotes the fixed reference gate "
                            r"and M the coverage-matched ordinary-margin comparator. "
                            r"All error rates concern recorded prompt names. These "
                            r"retrospective decisions do not establish perceptual fidelity, "
                            r"a generated-image coverage guarantee or independent replication."]
    lines += criterion_tables(data)
    for view, target, title in SETTINGS:
        lines += setting_tables(data, view, target, title)
    lines += influence_tables(data)
    lines += [r"\FloatBarrier", r"\paragraph{Numerical completeness.} The retained JSON includes "
              r"every score, candidate set, prediction, acceptance decision and abstention "
              r"reason for all 1,008 images under each of eight settings. It also retains "
              r"full confusion matrices, per-artist risks, exact cutoff/tie accounting, "
              r"calibration order statistics, source memberships and all deletion outcomes. "
              r"The table generator verifies both frozen source hashes and reconstructs "
              r"displayed full/deletion accounting from those retained decisions. "
              r"Exact table replay: \texttt{uv run --locked python "
              r"paper/make\_icml\_selective\_tables.py --check}."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = load()
    outputs = {ROOT / "paper/icml_selective_table.tex": main_table(data),
               ROOT / "paper/icml_selective_results.tex": appendix(data)}
    for path, content in outputs.items():
        if args.check:
            require(path.read_text() == content, "generated TeX differs: " + path.name)
        else:
            path.write_text(content)
    print("Selective source hashes, all full/deletion accounting and both TeX outputs verified"
          if args.check else "Selective main and complete appendix tables generated")


if __name__ == "__main__":
    main()
