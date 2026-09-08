"""Blinded local task planning and strict human-response import; never opens images.

The private asset map is for the investigator only. Materialize its destinations as
metadata-stripped, aspect-preserving PNGs under a separately frozen display scope.
Reference content labels in inputs are prior annotations, never human validation.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

SCHEMA = 1
FINE_CONTENT = (
    "lily_pond", "other_pond_lake", "river_stream", "coast_harbor",
    "buildings_street", "bridge_road", "fields_garden", "woods_trees",
    "hills_mountains", "other", "mixed_uncertain",
)
ANNOTATION_OPTIONS = {
    "outdoor_place": ["yes", "no", "uncertain"],
    "content_class": ["water", "built", "land", "other", "mixed_uncertain"],
    "fine_content": list(FINE_CONTENT),
    "viewpoint": ["near", "middle", "distant", "mixed_uncertain"],
    "visible_border": ["present", "absent", "uncertain"],
}
QUESTIONS = {
    "vividness": "How vivid or intense are the colors in this image?",
    "reference_vividness": "How vivid or intense are the colors in this image?",
    "adherence": "How closely does the depicted scene follow the scene instruction?",
    "resemblance": "How closely does the image's visual treatment resemble the reference panel?",
    "reference_annotation": "Describe the visible scene. Keep uncertainty explicit.",
}
SCALE_LABELS = {
    "vividness": ["1: very muted", "7: very vivid"],
    "reference_vividness": ["1: very muted", "7: very vivid"],
    "adherence": ["1: not at all", "7: very closely"],
    "resemblance": ["1: not at all", "7: very closely"],
}


def _digest(*parts):
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _path(value):
    value = _text(value, "image_path")
    path = PurePosixPath(value)
    if (path.is_absolute() or not path.parts or ".." in path.parts
            or "\\" in value or ":" in value):
        raise ValueError("image_path must be a portable relative path")
    return path.as_posix()


def make_tasks(images, references, seed):
    """Return public task pool plus private mappings, using no pixel/feature input.

    Generated rows require image_id, image_path, scene_text, arm and polarity.
    scene_text is the reviewed adherence instruction without an artist clause;
    this function cannot certify blinding of arbitrary investigator-written prose.
    References require image_id, image_path, painter_id and painter_name. Where all
    three broad classes exist, select one hash-ranked anchor per class; otherwise
    use up to three hash-ranked references and explicitly label incomplete support.
    All references also enter separate vividness and annotation task pools.
    """
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    images, references = list(images), list(references)
    seen, source_paths = set(), set()
    assets, by_id, groups = [], {}, defaultdict(list)
    for row in images + references:
        if not isinstance(row, dict):
            raise ValueError("image and reference rows must be objects")
        ident = _text(row.get("image_id"), "image_id")
        source = _path(row.get("image_path"))
        if ident in seen or source in source_paths:
            raise ValueError("duplicate image identity or source path")
        seen.add(ident)
        source_paths.add(source)
        target = f"assets/{_digest('asset', seed, ident)[:32]}.png"
        by_id[ident] = target
        assets.append({"image_id": ident, "source_path": source, "public_path": target})
    for row in images:
        for field in ("scene_text", "arm", "polarity"):
            _text(row.get(field), field)
    for row in references:
        painter = _text(row.get("painter_id"), "painter_id")
        _text(row.get("painter_name"), "painter_name")
        groups[painter].append(row)
    panels = {}
    for painter, rows in sorted(groups.items()):
        names = {r["painter_name"] for r in rows}
        if len(names) != 1:
            raise ValueError("one painter_id has inconsistent display names")
        ordered = sorted(rows, key=lambda r: (_digest("anchor", seed, r["image_id"]),
                                              r["image_id"]))
        classes = ("water", "built", "land")
        complete = all(any(r.get("content_class") == c for r in rows) for c in classes)
        chosen = ([next(r for r in ordered if r.get("content_class") == c) for c in classes]
                  if complete else ordered[:3])
        panels[painter] = {
            "painter_name": next(iter(names)),
            "image_ids": [r["image_id"] for r in chosen],
            "selection": "one_per_prior_broad_class" if complete else "incomplete_class_support",
            "human_content_validation": "pending",
        }
    tasks, keys = [], []

    def add(row, kind, painter=None):
        ident = row["image_id"]
        task_id = _digest("task", seed, ident, kind, painter)[:32]
        task = {"task_id": task_id, "kind": kind, "image": by_id[ident],
                "question": QUESTIONS[kind]}
        if kind == "reference_annotation":
            task["annotation_options"] = ANNOTATION_OPTIONS
        else:
            task["scale"] = {"min": 1, "max": 7, "labels": SCALE_LABELS[kind]}
        if kind == "adherence":
            task["scene_text"] = row["scene_text"]
        if kind == "resemblance":
            task["reference_painter"] = panels[painter]["painter_name"]
            task["references"] = [by_id[i] for i in panels[painter]["image_ids"]]
        tasks.append(task)
        keys.append({"task_id": task_id, "image_id": ident, "kind": kind,
                     "arm": row.get("arm"), "polarity": row.get("polarity"),
                     "reference_painter_id": painter,
                     "source_painter_id": row.get("painter_id")})

    for row in sorted(images, key=lambda r: r["image_id"]):
        add(row, "vividness")
        add(row, "adherence")
        for painter in panels:
            add(row, "resemblance", painter)
    for row in sorted(references, key=lambda r: r["image_id"]):
        add(row, "reference_vividness")
        add(row, "reference_annotation")
    tasks.sort(key=lambda t: (_digest("order", seed, t["task_id"]), t["task_id"]))
    public = {"schema_version": SCHEMA, "tasks": tasks,
              "status": "unrated", "annotation_codebook_version": "draft-v1"}
    keys.sort(key=lambda k: k["task_id"])
    assets.sort(key=lambda a: a["image_id"])
    package_id = _digest("package", seed, public, assets, keys, panels)
    public["package_id"] = package_id
    private = {"schema_version": SCHEMA, "package_id": package_id,
               "task_key": keys, "assets": assets,
               "reference_panels": panels,
               "status": "planned_only_no_human_judgments"}
    return {"public": public, "private": private}


def _assignments(public, assignments):
    if not isinstance(assignments, dict):
        raise ValueError("assignments must map registered rater IDs to task lists")
    known = {t["task_id"] for t in public["tasks"]}
    if len(known) != len(public["tasks"]):
        raise ValueError("duplicate public task ID")
    normalized = {}
    for rater, ids in assignments.items():
        _text(rater, "rater_id")
        if not isinstance(ids, (list, tuple)) or any(not isinstance(i, str) for i in ids):
            raise ValueError("assignment must be a list of task IDs")
        ids = list(ids)
        if len(ids) != len(set(ids)) or not set(ids) <= known:
            raise ValueError("assignment contains duplicate or unknown tasks")
        normalized[rater] = ids
    return normalized


def validate_ratings(public, submissions, assignments, phase="validation"):
    """Validate registered human exports; keep missing, cannot-judge and failure distinct.

    This validates recorded provenance, not the biological identity of a respondent.
    Registration/consent and investigator verification remain external requirements.
    Technical previews, synthetic rows and the other study phase are never pooled.
    """
    if phase not in {"usability_pilot", "validation"}:
        raise ValueError("only a declared human phase can be imported")
    assignments = _assignments(public, assignments)
    tasks = {t["task_id"]: t for t in public["tasks"]}
    rows, exports = [], set()
    for submission in submissions:
        if not isinstance(submission, dict):
            raise ValueError("response exports must be objects")
        required = {"schema_version", "package_id", "rater_id", "phase",
                    "respondent_kind", "consent", "answers"}
        if (not required <= set(submission)
                or set(submission) - required - {"exported_at", "display"}):
            raise ValueError("missing or unknown response export field")
        rater = submission.get("rater_id")
        if not isinstance(rater, str) or rater not in assignments or rater in exports:
            raise ValueError("unknown rater or duplicate rater export")
        exports.add(rater)
        if type(submission["schema_version"]) is not int or submission["schema_version"] != SCHEMA:
            raise ValueError("unsupported response schema")
        if submission.get("package_id") != public["package_id"]:
            raise ValueError("response package does not match")
        if submission.get("phase") != phase or submission.get("respondent_kind") != "human":
            raise ValueError("wrong phase or nonhuman/technical responses")
        if submission.get("consent") is not True:
            raise ValueError("human responses require recorded consent")
        answers = submission.get("answers")
        if not isinstance(answers, list):
            raise ValueError("answers must be a list")
        seen = set()
        for answer in answers:
            if not isinstance(answer, dict):
                raise ValueError("task responses must be objects")
            if not {"task_id", "status"} <= set(answer) or set(answer) - {
                "task_id", "status", "rating", "annotations", "notes"
            }:
                raise ValueError("missing or unknown task response field")
            ident, status = answer.get("task_id"), answer.get("status")
            if not isinstance(ident, str) or ident not in assignments[rater] or ident in seen:
                raise ValueError("unassigned or duplicate task response")
            seen.add(ident)
            if (not isinstance(status, str)
                    or status not in {"rated", "cannot_judge", "display_failure"}):
                raise ValueError("invalid response status")
            value = answer.get("rating")
            annotations = answer.get("annotations")
            if status != "rated":
                if value is not None or annotations is not None:
                    raise ValueError("nonratings cannot contain scores or annotations")
            elif tasks[ident]["kind"] == "reference_annotation":
                if value is not None or not isinstance(annotations, dict):
                    raise ValueError("reference annotations require structured labels")
                if set(annotations) != set(ANNOTATION_OPTIONS):
                    raise ValueError("missing or unknown annotation field")
                if any(v not in ANNOTATION_OPTIONS[k] for k, v in annotations.items()):
                    raise ValueError("invalid annotation label")
            elif type(value) is not int or not 1 <= value <= 7 or annotations is not None:
                raise ValueError("rating must be an integer from 1 through 7")
            note = answer.get("notes", "")
            if not isinstance(note, str) or len(note) > 1000:
                raise ValueError("notes must be text of at most 1000 characters")
            rows.append({"rater_id": rater, "task_id": ident, "kind": tasks[ident]["kind"],
                         "status": status, "rating": value, "annotations": annotations,
                         "notes": note, "phase": phase})
    answered = {(r["rater_id"], r["task_id"]) for r in rows}
    missing = [{"rater_id": rater, "task_id": ident}
               for rater, ids in sorted(assignments.items()) for ident in ids
               if (rater, ident) not in answered]
    counts = Counter(r["status"] for r in rows)
    unjudged = len(missing) + counts["cannot_judge"] + counts["display_failure"]
    return {"status": "pending" if not counts["rated"] else "partial" if unjudged else "complete",
            "disposition_status": "pending" if not rows else "partial" if missing else "complete",
            "phase": phase, "package_id": public["package_id"],
            "n_ratings": counts["rated"], "n_cannot_judge": counts["cannot_judge"],
            "n_display_failure": counts["display_failure"], "n_missing": len(missing),
            "n_registered_raters": len(assignments), "n_submitted_raters": len(exports),
            "missing": missing, "rows": sorted(rows, key=lambda r: (r["rater_id"], r["task_id"]))}


def write_interface(public, output_dir, assignments=None, *, phase="technical_preview",
                    consent_text=""):
    """Write a standalone local page, with no private key and no image reads.

    The default is a technical preview. Human phases need externally registered
    assignment IDs and investigator-supplied consent material; this is not ethics
    approval or participant recruitment. Only the public directory is shareable.
    """
    if phase not in {"technical_preview", "usability_pilot", "validation"}:
        raise ValueError("unknown interface phase")
    assignments = _assignments(public, {} if assignments is None else assignments)
    if phase != "technical_preview" and (not assignments or not consent_text.strip()):
        raise ValueError("human phase needs assignments and consent text")
    configuration = {"public": public, "assignments": assignments,
                     "phase": phase, "consent_text": consent_text}
    embedded = json.dumps(configuration, ensure_ascii=False).replace("<", "\\u003c")
    template = Path(__file__).with_name("human.html").read_text(encoding="utf-8")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "index.html"
    with target.open("x", encoding="utf-8") as handle:
        handle.write(template.replace("__TASK_CONFIGURATION__", embedded))
    return ["index.html"]
