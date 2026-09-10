"""Summarize actual reference judgments without declaring perceptual validation.

Inputs are already computed chroma diagnostics and exports validated by human.py.
Registered roles are investigator declarations, not a proof of independence.
No images, new measurements, fitted calibration, or automatic margin are used.
"""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import median

PAINTERS = ("claude_monet", "paul_cezanne")
CODING_FIELDS = ("outdoor_place", "content_class", "fine_content")


def _range(values):
    values = list(values)
    if len(values) < 2:
        return None
    return {"minimum": min(values), "maximum": max(values),
            "span": max(values) - min(values), "n_works": len(values)}


def summarize(reference_chroma, public, private, ratings, rater_roles, planned_templates):
    """Return per-work judgments and all six planned painter/content support groups.

    Two distinct independent raters must each supply both vividness and content
    coding. All available independent eligibility/broad/fine codes must agree;
    disagreement is retained, never adjudicated by software. The two-rater and
    two-work rules are minimum comparability checks, not a power justification.
    Unresolved panel members prevent a selectively rated subset defining readiness.
    """
    if not (public["package_id"] == private["package_id"] == ratings["package_id"]):
        raise ValueError("reference judgments must use the same task package")
    if ratings["phase"] != "validation":
        raise ValueError("pilot or technical responses cannot establish reference support")
    if any(role not in {"maintainer", "independent"} for role in rater_roles.values()):
        raise ValueError("roles must distinguish maintainer and independent human raters")
    subjects = sorted({(t["content_class"], t["fine_subject"]) for t in planned_templates})
    if len(subjects) != 3:
        raise ValueError("the current plan requires three distinct broad/fine content groups")
    works = {w["image_id"]: w for w in reference_chroma["works"]}
    if len(works) != len(reference_chroma["works"]):
        raise ValueError("duplicate reference work identity")
    if not works or {w["painter_id"] for w in works.values()} != set(PAINTERS):
        raise ValueError("reference diagnostics must include both planned painters")
    tasks = {t["task_id"]: t for t in public["tasks"]}
    keys = {t["task_id"]: t for t in private["task_key"]}
    if (len(keys) != len(private["task_key"]) or len(tasks) != len(public["tasks"])
            or set(keys) != set(tasks)):
        raise ValueError("public/private task identities must agree exactly")
    reference_tasks = defaultdict(dict)
    for task_id, key in keys.items():
        kind = key["kind"]
        if kind not in {"reference_vividness", "reference_annotation"}:
            continue
        if tasks[task_id]["kind"] != kind or key["image_id"] not in works:
            raise ValueError("reference task has a mismatched kind or work identity")
        if kind in reference_tasks[key["image_id"]]:
            raise ValueError("duplicate reference task kind for one work")
        reference_tasks[key["image_id"]][kind] = task_id
    if set(reference_tasks) != set(works) or any(
        set(kinds) != {"reference_vividness", "reference_annotation"}
        for kinds in reference_tasks.values()
    ):
        raise ValueError("every diagnostic work needs both reference task kinds")
    answers, missing = defaultdict(list), defaultdict(list)
    seen = set()
    for row in ratings["rows"]:
        task_id, rater = row["task_id"], row["rater_id"]
        if task_id not in keys or rater not in rater_roles or (rater, task_id) in seen:
            raise ValueError("unregistered, unknown or duplicate validated response")
        seen.add((rater, task_id))
        if row["phase"] != "validation" or row["kind"] != keys[task_id]["kind"]:
            raise ValueError("validated response phase or task kind mismatch")
        if keys[task_id]["kind"] in {"reference_vividness", "reference_annotation"}:
            answers[keys[task_id]["image_id"]].append(dict(row, role=rater_roles[rater]))
    for row in ratings["missing"]:
        if row["task_id"] not in keys or row["rater_id"] not in rater_roles:
            raise ValueError("missingness contains an unknown task or unregistered rater")
        key = keys[row["task_id"]]
        if key["kind"] in {"reference_vividness", "reference_annotation"}:
            missing[key["image_id"]].append(dict(row, role=rater_roles[row["rater_id"]]))
    result_works = []
    for identity, work in sorted(works.items()):
        rows = sorted(answers[identity], key=lambda r: (r["rater_id"], r["kind"]))
        independent = [r for r in rows if r["role"] == "independent" and r["status"] == "rated"]
        vividness = {r["rater_id"]: r["rating"] for r in independent
                     if r["kind"] == "reference_vividness"}
        coding = {r["rater_id"]: r["annotations"] for r in independent
                  if r["kind"] == "reference_annotation"}
        complete = sorted(set(vividness) & set(coding))
        labels = {tuple(c[f] for f in CODING_FIELDS) for c in coding.values()}
        agreed = dict(zip(CODING_FIELDS, next(iter(labels)))) if len(labels) == 1 else None
        status = "pending_independent_judgments"
        if len(labels) > 1:
            status = "disputed_independent_codes"
        elif len(complete) >= 2:
            if (agreed["outdoor_place"] == "uncertain"
                    or agreed["content_class"] == "mixed_uncertain"
                    or agreed["fine_content"] == "mixed_uncertain"):
                status = "uncertain_independent_codes"
            elif agreed["outdoor_place"] == "no":
                status = "independently_coded_ineligible"
            else:
                status = "minimum_comparability_met"
        raw, scaled = work["raw_chroma"], work["common_primary_scaled_chroma"]
        if set(raw) != set(scaled) or "primary512" not in raw:
            raise ValueError("reference chroma pipeline identities do not agree")
        if any(not math.isfinite(v) for v in [*raw.values(), *scaled.values()]):
            raise ValueError("reference chroma values must be finite")
        result_works.append(dict(
            image_id=identity, painter_id=work["painter_id"], status=status,
            prior_content_class=work["content_class"], agreed_codes=agreed,
            independent_complete_rater_ids=complete,
            n_independent_vividness=len(vividness), n_independent_annotations=len(coding),
            independent_vividness_median=median(vividness.values()) if vividness else None,
            judgments=rows, missing_assignments=missing[identity],
            raw_chroma=raw, common_primary_scaled_chroma=scaled,
            raw_pipeline_span=work["raw_pipeline_span"],
            pipeline_span_primary_iqr_units=work["pipeline_span_primary_iqr_units"],
            capture_workflow=work.get("capture_workflow", "unresolved"),
        ))
    groups = []
    for painter in PAINTERS:
        for broad, fine in subjects:
            members = [w for w in result_works if w["painter_id"] == painter
                       and w["status"] == "minimum_comparability_met"
                       and w["agreed_codes"]["content_class"] == broad
                       and w["agreed_codes"]["fine_content"] == fine]
            n = len(members)
            pipelines = sorted(members[0]["raw_chroma"]) if members else []
            groups.append(dict(
                painter_id=painter, content_class=broad, fine_subject=fine,
                template_ids=sorted(t["template_id"] for t in planned_templates
                                    if (t["content_class"], t["fine_subject"]) == (broad, fine)),
                n_works=n, image_ids=[w["image_id"] for w in members],
                status="blocked_fewer_than_two_works" if n < 2 else "thin_descriptive_support"
                if n < 5 else "candidate_empirical_range_only",
                raw_chroma_ranges={p: _range(w["raw_chroma"][p] for w in members)
                                   for p in pipelines},
                scaled_chroma_ranges={p: _range(w["common_primary_scaled_chroma"][p]
                                              for w in members) for p in pipelines},
                human_work_median_range=_range(w["independent_vividness_median"] for w in members),
                maximum_processing_span_primary_iqr=max(
                    (w["pipeline_span_primary_iqr_units"] for w in members), default=None),
            ))
    unresolved = [w["image_id"] for w in result_works if w["status"] in {
        "pending_independent_judgments", "disputed_independent_codes", "uncertain_independent_codes"
    }]
    blocked = [dict(painter_id=g["painter_id"], fine_subject=g["fine_subject"])
               for g in groups if g["n_works"] < 2]
    any_human = any(r["status"] == "rated" for w in result_works for r in w["judgments"])
    status = ("pending_human_reference_judgments" if not any_human else
              "blocked_reference" if blocked or unresolved else
              "ready_for_responsible_human_margin_decision")
    return dict(
        status=status, package_id=public["package_id"], works=result_works, groups=groups,
        blocked_groups=blocked, unresolved_work_ids=unresolved,
        meaningful_margin=None, generation_authorized=False,
        limitations=[
            "Two raters and two works establish only minimum comparability, not adequate power, "
            "perceptual validity or a well-estimated population range.",
            "Ordinal vividness summaries are descriptive; no fitted chroma-to-perception "
            "calibration or automatic meaningful margin is produced.",
            "All retained works were already exposed. Unresolved members block readiness "
            "rather than silently defining a selected rated-reference population.",
            "Same-file processing variation is not an independent capture comparison. "
            "No historical period or capture workflow is inferred from judgments.",
            "A responsible human must freeze an acceptable target, meaningful margin, "
            "precision requirement and proceed decision before generation.",
        ],
    )
