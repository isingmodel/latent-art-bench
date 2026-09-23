"""Fixed retrospective reference-calibrated abstention; no new algorithm.

``freeze`` hashes retained files without loading vectors or computing outcomes.
Real execution requires a separate method audit, an external freeze digest and
``--execute-real``. The calibration quantile confers no generated-image coverage
guarantee under the unqualified historical/generated domain shift.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NS = "painter_selective_attribution_v1"
SCHEMA = "painter-selective-attribution/1.0"
LEARNED = "reports/painter_learned_audit_v1"
ANCHOR = "reports/painter_prototype_transfer_v1/inputs.json"
ANCHOR_SHA = "bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf"
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
MODELS = (
    "gpt-image-1", "gpt-image-2", "gpt-image-2.5-flare", "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image", "black-forest-labs/flux.2-max",
)
ARMS = ("free", "generic", *ARTISTS)
ENCODERS = ("clip", "csd")
VIEWS = ("original", "audited_region")
TARGETS = ("primary", "development")
PRIMARY = "csd/original/primary"
COUNTS = {"reference": (297, 106, 141, 105), "development": (101, 36, 48, 36)}
CROPS = {"reference": (41, 23, 13, 13), "development": (17, 7, 11, 6)}
UNIT_ATOL = 1e-4


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON field")
        out[key] = value
    return out


def _invalid_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def read_json_bytes(value):
    return json.loads(value, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (value if isinstance(value, str)
                else json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(rendered)


def _bound_path(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("binding path must be relative")
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("binding escapes root")
    return path


def verified_bytes(root, relative, expected):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("invalid expected SHA-256")
    value = _bound_path(root, relative).read_bytes()
    if sha_bytes(value) != expected:
        raise ValueError(f"bound file changed: {relative}")
    return value


def _array(value, name, ndim=None):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu" or (ndim is not None and raw.ndim != ndim):
        raise ValueError(f"{name}: invalid numeric shape or dtype")
    values = np.asarray(raw, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError(f"{name}: nonfinite values")
    return values


def unit_vectors(value, name, ndim=None):
    values = _array(value, name, ndim)
    if values.ndim < 1 or values.shape[-1] < 1:
        raise ValueError(f"{name}: empty feature dimension")
    if not np.allclose(np.linalg.norm(values, axis=-1), 1, rtol=0, atol=UNIT_ATOL):
        raise ValueError(f"{name}: nonunit vectors")
    return values


def nonconformity(scores):
    values = _array(scores, "scores", 2)
    if values.shape[1] != 4 or values.shape[0] == 0:
        raise ValueError("scores require nonempty (n, 4) shape")
    other = np.broadcast_to(values[:, None, :], (len(values), 4, 4)).copy()
    other[:, np.arange(4), np.arange(4)] = -np.inf
    return other.max(axis=2) - values


def fixed_quantile(values):
    """Exactly ceil(9(n+1)/10), without interpolation or floating rank rounding."""
    scores = _array(values, "calibration scores", 1)
    if len(scores) == 0:
        raise ValueError("empty calibration class")
    rank = (9 * (len(scores) + 1) + 9) // 10
    infinite = rank > len(scores)
    return dict(n=len(scores), rank=rank, infinite=infinite,
                threshold=None if infinite else float(np.sort(scores)[rank - 1]))


def calibrate(reference, calibration):
    """Only historical arrays enter this fit; synthetic feature dimensions allowed."""
    if len(reference) != 4 or len(calibration) != 4:
        raise ValueError("four reference and calibration painter groups required")
    refs = [unit_vectors(x, "reference", 2) for x in reference]
    cals = [unit_vectors(x, "calibration", 2) for x in calibration]
    dimension = refs[0].shape[1]
    if any(len(x) == 0 or x.shape[1] != dimension for x in refs + cals):
        raise ValueError("nonempty historical groups with matching dimensions required")
    raw_means = np.stack([x.mean(axis=0) for x in refs])
    norms = np.linalg.norm(raw_means, axis=1)
    if not np.isfinite(norms).all() or np.any(norms <= 0):
        raise ValueError("zero or invalid reference mean")
    prototypes = raw_means / norms[:, None]
    calibration_scores = [nonconformity(x @ prototypes.T)[:, a] for a, x in enumerate(cals)]
    quantiles = [fixed_quantile(x) for x in calibration_scores]
    return dict(
        alpha=0.10, reference_counts=[len(x) for x in refs],
        calibration_counts=[len(x) for x in cals], raw_reference_means=raw_means.tolist(),
        reference_mean_norms=norms.tolist(), prototypes=prototypes.tolist(),
        quantiles=quantiles, calibration_scores=[x.tolist() for x in calibration_scores],
        generated_image_coverage_guarantee=False,
    )


def decide(scores, quantiles):
    values = _array(scores, "scores", 2)
    nc = nonconformity(values)
    if len(quantiles) != 4:
        raise ValueError("four calibration quantiles required")
    thresholds = []
    for q in quantiles:
        n, rank = q.get("n"), q.get("rank")
        if (type(n) is not int or n < 1 or type(rank) is not int
                or rank != (9 * (n + 1) + 9) // 10
                or q.get("infinite") is not (rank > n)):
            raise ValueError("invalid fixed calibration quantile")
        if q["infinite"]:
            if q.get("threshold") is not None:
                raise ValueError("infinite threshold must have null JSON value")
            thresholds.append(np.inf)
        else:
            threshold = q.get("threshold")
            if (type(threshold) not in (int, float) or not np.isfinite(threshold)):
                raise ValueError("finite threshold required")
            thresholds.append(threshold)
    members = nc <= np.asarray(thresholds)[None, :]
    sizes = members.sum(axis=1)
    prediction = values.argmax(axis=1)
    agrees = members[np.arange(len(values)), prediction]
    accepted = (sizes == 1) & agrees
    reasons = np.full(len(values), "accepted", dtype=object)
    reasons[sizes == 0] = "empty_set"
    reasons[sizes > 1] = "multiple_labels"
    reasons[(sizes == 1) & ~agrees] = "singleton_disagrees_with_top1"
    sorted_scores = np.sort(values, axis=1)
    return dict(predictions=prediction, scores=values, nonconformity=nc, members=members,
                accepted=accepted, reasons=reasons, margins=sorted_scores[:, -1]
                - sorted_scores[:, -2],
                top_ties=(values == values.max(axis=1, keepdims=True)).sum(axis=1) > 1)


def margin_match(margins, image_ids, k):
    margins = _array(margins, "margins", 1)
    ids = list(image_ids)
    if (len(ids) != len(margins) or any(not isinstance(x, str) or not x for x in ids)
            or len(set(ids)) != len(ids)):
        raise ValueError("unique margin query identities required")
    if type(k) is not int or not 0 <= k <= len(margins):
        raise ValueError("invalid matched acceptance count")
    order = sorted(range(len(ids)), key=lambda i: (-float(margins[i]), ids[i]))
    accepted = np.zeros(len(margins), dtype=bool)
    accepted[order[:k]] = True
    cutoff = None if k == 0 else float(margins[order[k - 1]])
    tie_mask = np.zeros(len(margins), dtype=bool) if k == 0 else margins == cutoff
    return dict(accepted=accepted, k=k, cutoff=cutoff,
                boundary_id=None if k == 0 else ids[order[k - 1]],
                cutoff_ties=int(tie_mask.sum()),
                cutoff_ties_accepted=int((tie_mask & accepted).sum()))


def control_margin_mask(margins, comparator):
    margins = _array(margins, "control margins", 1)
    if comparator["k"] == 0:
        return np.zeros(len(margins), dtype=bool), np.zeros(len(margins), dtype=bool)
    cutoff = comparator["cutoff"]
    return margins >= cutoff, margins == cutoff


def _risk(numerator, denominator):
    return None if denominator == 0 else float(numerator / denominator)


def _difference(left, right):
    return None if left is None or right is None else float(left - right)


def complete_mean(values):
    """Do not turn unavailable configurations into a favorable partial mean."""
    values = list(values)
    if not values or any(v is None for v in values):
        return None
    return float(np.mean(_array(values, "mean values", 1)))


def _complete_range(values):
    values = list(values)
    missing = sum(x is None for x in values)
    return dict(values=values, missing_count=missing,
                range=None if missing or not values else [min(values), max(values)])


def summarize_named(predictions, truth, accepted):
    pred, truth, accepted = map(np.asarray, (predictions, truth, accepted))
    if (pred.ndim != 1 or pred.dtype.kind not in "iu" or truth.dtype.kind not in "iu"
            or accepted.dtype != bool or truth.shape != pred.shape
            or accepted.shape != pred.shape or np.any((pred < 0) | (pred > 3))
            or np.any((truth < 0) | (truth > 3))):
        raise ValueError("invalid named predictions/truth/acceptance")
    correct = pred == truth
    n, k = len(pred), int(accepted.sum())
    bad = ~correct
    confusion = np.zeros((4, 4), dtype=int)
    accepted_confusion = np.zeros((4, 4), dtype=int)
    np.add.at(confusion, (truth, pred), 1)
    np.add.at(accepted_confusion, (truth[accepted], pred[accepted]), 1)
    per_painter = []
    for a in range(4):
        group = truth == a
        chosen = group & accepted
        rejected = group & ~accepted
        per_painter.append(dict(
            painter=ARTISTS[a], count=int(group.sum()), accepted_count=int(chosen.sum()),
            coverage=_risk(int(chosen.sum()), int(group.sum())),
            unrestricted_error=_risk(int((bad & group).sum()), int(group.sum())),
            accepted_error=_risk(int((bad & chosen).sum()), int(chosen.sum())),
            abstained_error=_risk(int((bad & rejected).sum()), int(rejected.sum())),
        ))
    return dict(
        count=n, accepted_count=k, abstained_count=n-k, coverage=_risk(k, n),
        correct_count=int(correct.sum()), incorrect_count=int(bad.sum()),
        accepted_correct=int((correct & accepted).sum()),
        accepted_incorrect=int((bad & accepted).sum()),
        abstained_correct=int((correct & ~accepted).sum()),
        abstained_incorrect=int((bad & ~accepted).sum()),
        unrestricted_error=_risk(int(bad.sum()), n),
        accepted_error=_risk(int((bad & accepted).sum()), k),
        abstained_error=_risk(int((bad & ~accepted).sum()), n-k),
        confusion=confusion.tolist(), accepted_confusion=accepted_confusion.tolist(),
        abstained_confusion=(confusion-accepted_confusion).tolist(),
        per_painter=per_painter,
    )


def _control_summary(predictions, accepted, boundary_ties=None):
    n, k = len(predictions), int(accepted.sum())
    return dict(count=n, accepted_count=k, attribution_rate=_risk(k, n),
                predicted_artist_counts=np.bincount(predictions, minlength=4).tolist(),
                accepted_artist_counts=np.bincount(
                    predictions[accepted], minlength=4).tolist(),
                numeric_cutoff_ties=None if boundary_ties is None
                else int(boundary_ties.sum()))


def _pool_summary(decisions, ids, shape, retained_scenes):
    """Re-match the margin comparator after a deletion; gate/calibration stay fixed."""
    _, repeats, arms = shape
    index = np.arange(np.prod(shape)).reshape(shape)[retained_scenes]
    named_index = index[:, :, 2:].ravel()
    true = np.broadcast_to(np.arange(4), (len(retained_scenes), repeats, 4)).ravel()
    gate = summarize_named(decisions["predictions"][named_index], true,
                           decisions["accepted"][named_index])
    comparator = margin_match(decisions["margins"][named_index], ids[named_index],
                              gate["accepted_count"])
    margin = summarize_named(decisions["predictions"][named_index], true,
                             comparator["accepted"])
    controls, control_masks = {}, {}
    for a, arm in enumerate(ARMS[:2]):
        loc = index[:, :, a].ravel()
        mask, ties = control_margin_mask(decisions["margins"][loc], comparator)
        controls[arm] = dict(
            reference_gate=_control_summary(decisions["predictions"][loc],
                                            decisions["accepted"][loc]),
            margin_comparator=_control_summary(decisions["predictions"][loc], mask, ties),
        )
        control_masks[arm] = mask
    reason_counts = {reason: int(np.sum(decisions["reasons"][named_index] == reason))
                     for reason in ("accepted", "empty_set", "multiple_labels",
                                    "singleton_disagrees_with_top1")}
    metadata = {key: value for key, value in comparator.items() if key != "accepted"}
    return dict(
        retained_scenes=list(retained_scenes), reference_gate=gate, margin_comparator=margin,
        baseline_minus_gate_risk=_difference(gate["unrestricted_error"], gate["accepted_error"]),
        margin_minus_gate_risk=_difference(margin["accepted_error"], gate["accepted_error"]),
        comparator_cutoff=metadata, controls=controls, named_reason_counts=reason_counts,
        named_top_ties=int(decisions["top_ties"][named_index].sum()),
    ), comparator["accepted"], control_masks


def evaluate_model(generated, image_ids, calibration):
    """Pure complete-scene evaluator; allows small synthetic scene/feature counts."""
    x = unit_vectors(generated, "generated", 4)
    if x.shape[0] < 2 or x.shape[1:3] != (2, 6):
        raise ValueError("generated shape must be (scenes>=2, 2, 6, features)")
    ids = np.asarray(image_ids, dtype=object)
    if ids.shape != x.shape[:-1] or any(not isinstance(v, str) or not v for v in ids.flat):
        raise ValueError("generated identities must match the complete query shape")
    flat_ids = ids.ravel()
    if len(set(flat_ids)) != len(flat_ids):
        raise ValueError("duplicate generated query identity")
    prototypes = unit_vectors(calibration["prototypes"], "prototypes", 2)
    if prototypes.shape != (4, x.shape[-1]):
        raise ValueError("four prototypes must match generated features")
    decisions = decide(x.reshape(-1, x.shape[-1]) @ prototypes.T, calibration["quantiles"])
    scenes = list(range(x.shape[0]))
    full, named_margin_mask, control_masks = _pool_summary(decisions, flat_ids, ids.shape, scenes)
    margin_all = np.zeros(ids.shape, dtype=bool)
    margin_all[:, :, 2:] = named_margin_mask.reshape(x.shape[0], 2, 4)
    for a, arm in enumerate(ARMS[:2]):
        margin_all[:, :, a] = control_masks[arm].reshape(x.shape[0], 2)
    rows = []
    for i, image_id in enumerate(flat_ids):
        scene, repeat, arm = np.unravel_index(i, ids.shape)
        rows.append(dict(
            id=image_id, scene=int(scene), repeat=int(repeat), arm=ARMS[arm],
            prompted_artist=None if arm < 2 else ARTISTS[arm-2],
            scores=decisions["scores"][i].tolist(),
            nonconformity=decisions["nonconformity"][i].tolist(),
            candidates=[ARTISTS[a] for a in np.flatnonzero(decisions["members"][i])],
            top1=ARTISTS[decisions["predictions"][i]],
            top_score_tie=bool(decisions["top_ties"][i]),
            ordinary_margin=float(decisions["margins"][i]),
            reference_gate_accept=bool(decisions["accepted"][i]),
            gate_reason=decisions["reasons"][i],
            margin_comparator_accept=bool(margin_all.ravel()[i]),
        ))
    deletions = []
    for scene in scenes:
        deleted, _, _ = _pool_summary(
            decisions, flat_ids, ids.shape, [s for s in scenes if s != scene])
        deletions.append(dict(deleted_scene=scene, **deleted))
    influence = {key: _complete_range([d[key] for d in deletions])
                 for key in ("baseline_minus_gate_risk", "margin_minus_gate_risk")}
    influence["gate_coverage"] = _complete_range(
        [d["reference_gate"]["coverage"] for d in deletions])
    influence["gate_accepted_error"] = _complete_range(
        [d["reference_gate"]["accepted_error"] for d in deletions])
    return dict(**full, observations=rows, scene_deletions=deletions, influence=influence)


def summarize_setting(models):
    if not models or len({m["model"] for m in models}) != len(models):
        raise ValueError("nonempty unique configuration summaries required")
    mean_base = complete_mean(m["baseline_minus_gate_risk"] for m in models)
    mean_margin = complete_mean(m["margin_minus_gate_risk"] for m in models)
    coverage_ok = all(m["reference_gate"]["coverage"] is not None
                      and m["reference_gate"]["coverage"] >= .5 for m in models)
    painter_ok = all(p["accepted_count"] >= 1 for m in models
                     for p in m["reference_gate"]["per_painter"])
    criteria = dict(
        every_configuration_coverage_at_least_half=coverage_ok,
        every_painter_accepted_in_every_configuration=painter_ok,
        positive_mean_baseline_minus_gate=mean_base is not None and mean_base > 0,
        positive_mean_margin_minus_gate=mean_margin is not None and mean_margin > 0,
    )
    missing = [key for key, value in (("baseline_minus_gate", mean_base),
                                    ("margin_minus_gate", mean_margin)) if value is None]
    return dict(
        configuration_count=len(models),
        mean_baseline_minus_gate_risk=mean_base, mean_margin_minus_gate_risk=mean_margin,
        mean_coverage=complete_mean(m["reference_gate"]["coverage"] for m in models),
        mean_gate_accepted_error=complete_mean(
            m["reference_gate"]["accepted_error"] for m in models),
        missing_means=missing, criteria=criteria,
        failed_criteria=[name for name, passed in criteria.items() if not passed],
        joint_usefulness=all(criteria.values()),
        adverse_baseline_configurations=[m["model"] for m in models
                                        if m["baseline_minus_gate_risk"] is not None
                                        and m["baseline_minus_gate_risk"] < 0],
        adverse_margin_configurations=[m["model"] for m in models
                                      if m["margin_minus_gate_risk"] is not None
                                      and m["margin_minus_gate_risk"] < 0],
    )


def assemble_rows(rows, embeddings, *, use_regions, model_names=MODELS, scenes=14,
                  expected_counts=COUNTS, expected_crops=CROPS):
    """Exact old membership, with explicit small census overrides only for fixtures."""
    values = unit_vectors(embeddings, "archive", 2)
    if values.shape[0] != len(rows):
        raise ValueError("archive must match manifest row count")
    if type(use_regions) is not bool or type(scenes) is not int or scenes < 2:
        raise ValueError("invalid assembly view or scene count")
    lookup = {}
    for i, row in enumerate(rows):
        image_id, view, role = row.get("id"), row.get("view"), row.get("role")
        if (not isinstance(image_id, str) or not image_id or view not in VIEWS
                or role not in ("generated", "reference", "development")):
            raise ValueError("unknown or missing retained row identity/view/role")
        if (image_id, view) in lookup:
            raise ValueError("duplicate image/view identity")
        if role == "generated" and view != "original":
            raise ValueError("generated crop substitution forbidden")
        lookup[(image_id, view)] = i
        if role != "generated":
            if (row.get("painter") not in ARTISTS
                    or not isinstance(row.get("path"), str) or not row["path"]
                    or not isinstance(row.get("sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
                raise ValueError("invalid reference source identity")
            box = row.get("box")
            if (not isinstance(box, list) or len(box) != 4
                    or any(type(v) not in (int, float) for v in box)
                    or not all(np.isfinite(v) for v in box)
                    or not 0 <= box[0] < box[2] <= 1 or not 0 <= box[1] < box[3] <= 1
                    or (view == "original" and box != [0, 0, 1, 1])
                    or (view == "audited_region" and box == [0, 0, 1, 1])):
                raise ValueError("invalid source region box")
    for (image_id, view), i in lookup.items():
        if view == "audited_region":
            original_index = lookup.get((image_id, "original"))
            if original_index is None:
                raise ValueError("audited region requires original")
            if any(rows[i][key] != rows[original_index].get(key)
                   for key in ("role", "painter", "path", "sha256")):
                raise ValueError("region identity differs from original")
    shape = (len(model_names), scenes, 2, 6)
    generated = np.full((*shape, values.shape[1]), np.nan)
    ids = np.full(shape, None, dtype=object)
    panels = {role: [[] for _ in ARTISTS] for role in COUNTS}
    membership = {role: [[] for _ in ARTISTS] for role in COUNTS}
    crop_counts = {role: [0] * 4 for role in COUNTS}
    for row in rows:
        if row["role"] != "generated" and row["view"] == "audited_region":
            crop_counts[row["role"]][ARTISTS.index(row["painter"])] += 1
    for (image_id, view), index in lookup.items():
        if view != "original":
            continue
        row = rows[index]
        if row["role"] == "generated":
            if (row.get("model") not in model_names or row.get("arm") not in ARMS
                    or type(row.get("scene")) is not int or not 0 <= row["scene"] < scenes
                    or type(row.get("repeat")) is not int or row["repeat"] not in (0, 1)):
                raise ValueError("invalid generated request cell")
            cell = (model_names.index(row["model"]), row["scene"], row["repeat"],
                    ARMS.index(row["arm"]))
            if ids[cell] is not None:
                raise ValueError("duplicate generated request cell")
            generated[cell], ids[cell] = values[index], image_id
        else:
            role, a = row["role"], ARTISTS.index(row["painter"])
            selected = lookup.get((image_id, "audited_region"), index) if use_regions else index
            panels[role][a].append(values[selected])
            membership[role][a].append(dict(id=image_id, original_row=index, selected_row=selected,
                                           selected_view=rows[selected]["view"]))
    if not np.isfinite(generated).all() or any(v is None for v in ids.flat):
        raise ValueError("incomplete generated census")
    for role in COUNTS:
        if (tuple(map(len, panels[role])) != tuple(expected_counts[role])
                or tuple(crop_counts[role]) != tuple(expected_crops[role])):
            raise ValueError(f"fixed {role} source/crop census changed")
    return dict(generated=generated, generated_ids=ids, memberships=membership,
                panels={role: [np.asarray(group) for group in groups]
                        for role, groups in panels.items()})


def retained_bindings(root=ROOT):
    """Hash-only provenance traversal. No NPZ load or new numerical outcome."""
    root = Path(root)
    anchor = read_json_bytes(verified_bytes(root, ANCHOR, ANCHOR_SHA))
    bindings = {ANCHOR: ANCHOR_SHA}
    for extra in (anchor["bindings"],):
        for path, expected in extra.items():
            verified_bytes(root, path, expected)
            bindings[path] = expected
    for name in ("inputs.json", "csd_adapter_inputs_v2.json"):
        relative = f"{LEARNED}/{name}"
        record = read_json_bytes(verified_bytes(root, relative, bindings[relative]))
        for path, expected in record["bindings"].items():
            if path in bindings and bindings[path] != expected:
                raise ValueError("conflicting historical bindings")
            verified_bytes(root, path, expected)
            bindings[path] = expected
    return bindings


def own_paths(root=ROOT):
    root = Path(root)
    paths = [f"studies/{NS}/PLAN.md", f"src/latent_art_bench/{NS}.py",
             "pyproject.toml", "uv.lock", "pytest-paper.ini"]
    tests = sorted((root / "tests" / NS).glob("test_*.py"))
    if not tests:
        raise ValueError("constructed tests required before freeze")
    return paths + [str(path.relative_to(root)) for path in tests]


def specification():
    return dict(alpha=.10, primary=PRIMARY, models=list(MODELS), artists=list(ARTISTS),
                arms=list(ARMS), encoders=list(ENCODERS), views=list(VIEWS), targets=list(TARGETS),
                scenes=14, repeats=2, named_count_per_model=112,
                control_count_per_arm_per_model=28,
                minimum_model_coverage=.5, minimum_accepted_per_painter=1,
                success_requires_both_mean_risk_reductions_strictly_positive=True,
                undefined_mean_policy="any missing configuration makes mean unavailable",
                generated_image_coverage_guarantee=False)


def freeze(path=None, *, root=ROOT):
    root = Path(root)
    path = root / "reports" / NS / "inputs.json" if path is None else Path(path)
    if path.exists():
        raise FileExistsError("freeze already exists; preserve it and use an explicit new path")
    bindings = retained_bindings(root)
    for relative in own_paths(root):
        expected = file_sha(_bound_path(root, relative))
        if relative in bindings and bindings[relative] != expected:
            raise ValueError("own binding conflicts with retained provenance")
        bindings[relative] = expected
    record = dict(schema=SCHEMA, study=NS,
                  status="frozen before selective outcomes; retrospective, audit pending",
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  specification=specification(), bindings=bindings,
                  environment=dict(python=platform.python_version(), numpy=np.__version__),
                  new_outcomes_computed=False)
    write_new(path, record)
    return file_sha(path)


def verify_freeze(path, *, expected_sha256, root=ROOT):
    path, root = Path(path), Path(root)
    raw = path.read_bytes()
    if not isinstance(expected_sha256, str) or sha_bytes(raw) != expected_sha256:
        raise ValueError("freeze differs from external expected SHA-256")
    record = read_json_bytes(raw)
    if (record.get("schema") != SCHEMA or record.get("study") != NS
            or record.get("specification") != specification()
            or record.get("new_outcomes_computed") is not False):
        raise ValueError("freeze schema or specification changed")
    if record.get("environment") != dict(python=platform.python_version(), numpy=np.__version__):
        raise ValueError("current Python/NumPy environment differs from frozen environment")
    required = retained_bindings(root)
    required.update({relative: file_sha(_bound_path(root, relative))
                     for relative in own_paths(root)})
    if record.get("bindings") != required:
        raise ValueError("frozen binding membership or bytes changed")
    return record


def verify_audit(path, *, expected_sha256, inputs_sha256, record, root=ROOT):
    """The independent audit is external to the freeze and bound by its own digest."""
    if path is None or not isinstance(expected_sha256, str):
        raise ValueError("independent passed audit and external audit SHA-256 are required")
    raw = Path(path).read_bytes()
    if sha_bytes(raw) != expected_sha256:
        raise ValueError("audit differs from external expected SHA-256")
    audit = read_json_bytes(raw)
    if (audit.get("schema") != "painter-selective-attribution-audit/1.0"
            or audit.get("study") != NS or audit.get("status") != "passed"
            or audit.get("inputs_sha256") != inputs_sha256):
        raise ValueError("independent audit status or frozen-input identity is invalid")
    required = {relative for relative in own_paths(root)
                if relative.startswith((f"studies/{NS}/", f"src/latent_art_bench/{NS}",
                                        f"tests/{NS}/"))}
    entries = audit.get("bindings")
    if not isinstance(entries, list):
        raise ValueError("audit bindings must be a path/sha256 list")
    bindings = {}
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"path", "sha256"}
                or not isinstance(entry["path"], str) or entry["path"] in bindings):
            raise ValueError("invalid or duplicate audit binding")
        bindings[entry["path"]] = entry["sha256"]
    if not required.issubset(bindings):
        raise ValueError("audit must bind the plan, implementation and every constructed test")
    for relative, expected in bindings.items():
        if record["bindings"].get(relative) != expected:
            raise ValueError("audited file does not match the frozen study")
        verified_bytes(root, relative, expected)
    return audit


def load_archive(root, record, encoder):
    """Authenticate exact bytes and receipts before returning supplied observations."""
    if encoder not in ENCODERS:
        raise ValueError("unknown encoder")
    bindings = record["bindings"]
    relative = f"{LEARNED}/inputs.json"
    manifest = read_json_bytes(verified_bytes(root, relative, bindings[relative]))
    relative_receipt = f"{LEARNED}/extraction_{encoder}.json"
    receipt = read_json_bytes(verified_bytes(root, relative_receipt, bindings[relative_receipt]))
    archive = f"{LEARNED}/embeddings_{encoder}.npz"
    if (len(manifest["rows"]) != 2009 or set(manifest["models"]) != set(ENCODERS)
            or receipt["input_sha256"] != bindings[relative]
            or receipt["embeddings_sha256"] != bindings[archive]
            or receipt["model"] != manifest["models"][encoder]
            or receipt["shape"] != [2009, 768] or receipt["dtype"] != "float32"):
        raise ValueError("retained input/extraction receipt census disagrees")
    raw = verified_bytes(root, archive, bindings[archive])
    with np.load(io.BytesIO(raw), allow_pickle=False) as npz:
        if npz.files != ["embeddings"]:
            raise ValueError("unexpected embedding archive members")
        values = npz["embeddings"]
    if values.shape != (2009, 768) or values.dtype != np.float32:
        raise ValueError("retained archive shape/dtype changed")
    return manifest["rows"], unit_vectors(values, "retained archive", 2)


def compute_real(path, *, expected_sha256, execute_real=False, audit_path=None,
                 expected_audit_sha256=None, root=ROOT):
    if execute_real is not True:
        raise ValueError("real computation requires explicit execution after independent audit")
    record = verify_freeze(path, expected_sha256=expected_sha256, root=root)
    verify_audit(audit_path, expected_sha256=expected_audit_sha256,
                 inputs_sha256=expected_sha256, record=record, root=root)
    result = dict(schema=SCHEMA, study=NS, inputs_sha256=expected_sha256,
                  audit_sha256=expected_audit_sha256,
                  descriptive_only=True, generated_image_coverage_guarantee=False,
                  specification=specification(), settings={})
    for encoder in ENCODERS:
        rows, values = load_archive(root, record, encoder)
        for view in VIEWS:
            assembled = assemble_rows(rows, values, use_regions=view == "audited_region")
            for target in TARGETS:
                reference_role = "reference" if target == "primary" else "development"
                calibration_role = "development" if target == "primary" else "reference"
                calibration = calibrate(assembled["panels"][reference_role],
                                        assembled["panels"][calibration_role])
                models = [dict(model=model, **evaluate_model(
                    generated, ids, calibration)) for model, generated, ids in zip(
                        MODELS, assembled["generated"], assembled["generated_ids"])]
                deletion_summaries = [dict(deleted_scene=s, **summarize_setting([
                    dict(model=m["model"], **m["scene_deletions"][s]) for m in models]))
                    for s in range(14)]
                key = f"{encoder}/{view}/{target}"
                result["settings"][key] = dict(
                    reference_role=reference_role, calibration_role=calibration_role,
                    memberships=assembled["memberships"], calibration=calibration,
                    models=models, summary=summarize_setting(models),
                    scene_deletion_summaries=deletion_summaries,
                    influence={name: _complete_range([d[name] for d in deletion_summaries])
                               for name in ("mean_baseline_minus_gate_risk",
                                            "mean_margin_minus_gate_risk", "mean_coverage",
                                            "mean_gate_accepted_error")})
    result["primary_joint_usefulness"] = result["settings"][PRIMARY]["summary"]["joint_usefulness"]
    verify_freeze(path, expected_sha256=expected_sha256, root=root)
    verify_audit(audit_path, expected_sha256=expected_audit_sha256,
                 inputs_sha256=expected_sha256, record=record, root=root)
    return result


def _percent(value):
    return "undefined" if value is None else f"{100 * value:.2f}"


def report(result):
    lines = ["# Reference-calibrated selective attribution v1", "",
             "Retrospective diagnostic using the fixed retained cohort. Standard abstention, "
             "not a new algorithm; no generated-image coverage guarantee under domain shift.", "",
             f"Input SHA-256: `{result['inputs_sha256']}`.", "",
             f"Primary setting: **{PRIMARY}**. Joint descriptive usefulness criterion: "
             f"**{result['primary_joint_usefulness']}**.", "",
             "All eight settings, six configurations, four painters and 1,008 generated "
             "observations are retained. The gate's alpha is fixed at 0.10. Error concerns "
             "recorded prompt names, not perceptual fidelity or physical authorship.", "",
             "The margin comparator uses the named query distribution to match coverage. "
             "Its numeric threshold is applied inclusively to controls, with ties retained. "
             "Control attribution rates do not establish visual misattribution.", ""]
    for key, setting in result["settings"].items():
        summary = setting["summary"]
        lines += [f"## {key}", "",
                  "| Configuration | Coverage % | Baseline error % | Gate error % | "
                  "Margin error % | Baseline−gate pp | Margin−gate pp |", 
                  "|---|---:|---:|---:|---:|---:|---:|"]
        for model in setting["models"]:
            g, m = model["reference_gate"], model["margin_comparator"]
            vals = [g["coverage"], g["unrestricted_error"], g["accepted_error"],
                    m["accepted_error"], model["baseline_minus_gate_risk"],
                    model["margin_minus_gate_risk"]]
            lines.append("| " + model["model"] + " | " + " | ".join(map(_percent, vals)) + " |")
        lines += ["", "Equal-configuration baseline−gate / margin−gate reductions (pp): "
                  f"{_percent(summary['mean_baseline_minus_gate_risk'])} / "
                  f"{_percent(summary['mean_margin_minus_gate_risk'])}.", "",
                  "Failed joint criteria: " + (", ".join(summary["failed_criteria"]) or "none")
                  + ". Missing means: " + (", ".join(summary["missing_means"]) or "none") + ".", "",
                  "| Configuration | Free gate % | Free margin % | Generic gate % | "
                  "Generic margin % | Gate accepted counts by painter |",
                  "|---|---:|---:|---:|---:|---|"]
        for model in setting["models"]:
            rates = [model["controls"][arm][rule]["attribution_rate"]
                     for arm in ARMS[:2] for rule in ("reference_gate", "margin_comparator")]
            counts = [p["accepted_count"] for p in model["reference_gate"]["per_painter"]]
            lines.append("| " + model["model"] + " | " + " | ".join(map(_percent, rates))
                         + " | " + ", ".join(map(str, counts)) + " |")
        lines += ["", "Complete predictions, nonconformity scores, set memberships, painter "
                  "risks/confusions, abstention reasons, numeric boundary ties and all "
                  "scene-deletion records are retained in analysis.json. Undefined risks and "
                  "means remain null; no configuration is dropped.", ""]
    lines += ["## Limits", "", "Prior baseline outcomes informed the retrospective question. "
              "The historical panels, generated observations and two related encoders are "
              "reused. Scene-deletion ranges describe influence, not uncertainty coverage. "
              "No p-values, new observations, perceptual validation or independent session "
              "replication are supplied. Adverse and undefined results remain part of the "
              "primary finding; no alternative gate is substituted.", ""]
    return "\n".join(lines)


def execute(path, *, expected_sha256, execute_real=False, audit_path=None,
            expected_audit_sha256=None, check=False, output=None, root=ROOT):
    output = Path(root) / "reports" / NS if output is None else Path(output)
    targets = (output / "analysis.json", output / "REPORT.md")
    if not check and any(p.exists() for p in targets):
        raise FileExistsError(
            "completed outputs are immutable; use replay or an explicit new version")
    result = compute_real(path, expected_sha256=expected_sha256,
                          execute_real=execute_real, audit_path=audit_path,
                          expected_audit_sha256=expected_audit_sha256, root=root)
    rendered = report(result)
    if check:
        if read_json_bytes(targets[0].read_bytes()) != result or targets[1].read_text() != rendered:
            raise ValueError("exact selective-attribution replay differs")
    else:
        write_new(targets[0], result)
        write_new(targets[1], rendered)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("freeze", "analyze", "check"))
    parser.add_argument("--inputs-file", type=Path, default=ROOT / "reports" / NS / "inputs.json")
    parser.add_argument("--input-sha256")
    parser.add_argument("--audit-file", type=Path)
    parser.add_argument("--audit-sha256")
    parser.add_argument("--execute-real", action="store_true")
    args = parser.parse_args()
    if args.action == "freeze":
        print(freeze(args.inputs_file))
    elif (not args.execute_real or not args.input_sha256 or not args.audit_file
          or not args.audit_sha256):
        parser.error("execution requires --execute-real, --input-sha256, --audit-file "
                     "and --audit-sha256")
    else:
        execute(args.inputs_file, expected_sha256=args.input_sha256,
                audit_path=args.audit_file, expected_audit_sha256=args.audit_sha256,
                execute_real=True, check=args.action == "check")
        print("Selective-attribution exact replay passed" if args.action == "check"
              else "Selective-attribution result and report created")


if __name__ == "__main__":
    main()
