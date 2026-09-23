"""Descriptive same-image audit of fixed learned embeddings.

No image loading, model inference, fitting of representations, p-values or
population intervals occur here. See studies/painter_learned_audit_v1/PLAN.md.
Native unit-embedding coordinates are retained without coordinate scaling.
"""

from __future__ import annotations

from itertools import combinations, permutations

import numpy as np

ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
MODELS = (
    "gpt-image-1",
    "gpt-image-2",
    "gpt-image-2.5-flare",
    "gpt-image-2.5-sunburst",
    "google/gemini-3.1-flash-image",
    "black-forest-labs/flux.2-max",
)
ARMS = ("free", "generic", *ARTISTS)
PAIR_INDICES = tuple(combinations(range(4), 2))
LABEL_PERMUTATIONS = tuple(permutations(range(4)))
UNIT_ATOL = 1e-4


def _unit_array(values, label):
    array = np.asarray(values, dtype=np.float64)
    if not np.isfinite(array).all():
        raise ValueError(f"{label} must contain only finite embeddings")
    if not np.allclose(np.linalg.norm(array, axis=-1), 1, rtol=0, atol=UNIT_ATOL):
        raise ValueError(f"{label} must contain unit embeddings within {UNIT_ATOL}")
    return array


def _panel(values, label):
    if len(values) != 4:
        raise ValueError(f"{label} must contain four painter arrays")
    panel = []
    for i, value in enumerate(values):
        array = np.asarray(value)
        if array.ndim != 2 or array.shape[1] != 768 or len(array) == 0:
            raise ValueError(f"{label}[{i}] must have nonempty shape (n, 768)")
        panel.append(_unit_array(array, f"{label}[{i}]"))
    return panel


def _center(values):
    return values - values.mean(axis=-2, keepdims=True)


def _range(values):
    """Do not conceal an undefined deletion behind a partial range."""
    return [float(min(values)), float(max(values))] if all(v is not None for v in values) else None


def _geometry(named, prototypes):
    """Repeat-corrected contrasts; accepts nonunit arrays for algebra tests."""
    named = np.asarray(named, dtype=np.float64)
    target = _center(np.asarray(prototypes, dtype=np.float64))
    contrasts = _center(named)
    h = float(np.square(target).sum())
    n = len(named)
    if h <= 0:
        return dict(
            available=False,
            reason="nonpositive_reference_contrast_energy",
            reference_energy=h,
            beta=None,
            q=None,
            d=None,
            aggregate_d=None,
            scene_variation=None,
            corrected_alignment=None,
            scene_beta=[None] * n,
            scene_q=[None] * n,
            scene_d=[None] * n,
            calibration=dict(available=False, reason="undefined_reference_target"),
        )
    beta = np.einsum("skaj,aj->s", contrasts, target) / (2 * h)
    q = (contrasts[:, 0] * contrasts[:, 1]).sum(axis=(1, 2)) / h
    error = contrasts - target
    d = (error[:, 0] * error[:, 1]).sum(axis=(1, 2)) / h
    aggregate_error = error.mean(axis=0)
    aggregate_d = float(np.sum(aggregate_error[0] * aggregate_error[1]) / h)
    deviations = contrasts - contrasts.mean(axis=0, keepdims=True)
    variation = float(np.sum(deviations[:, 0] * deviations[:, 1]) / (n * h))
    if n < 2:
        calibration = dict(available=False, reason="fewer_than_two_scenes")
    else:
        train_beta = (beta.sum() - beta) / (n - 1)
        train_q = (q.sum() - q) / (n - 1)
        valid = train_q > 0
        scalars = [
            float(max(0, b / magnitude)) if good else None
            for b, magnitude, good in zip(train_beta, train_q, valid)
        ]
        held = [
            float(1 - 2 * c * b + c * c * magnitude) if c is not None else None
            for c, b, magnitude in zip(scalars, beta, q)
        ]
        calibration = dict(
            available=bool(valid.all()),
            reason=None if valid.all() else "nonpositive_training_cross_repeat_magnitude",
            train_beta=train_beta.tolist(),
            train_q=train_q.tolist(),
            fitted_scalars=scalars,
            held_out_scene_d=held,
            held_out_d=float(np.mean(held)) if valid.all() else None,
        )
    b, magnitude = float(beta.mean()), float(q.mean())
    return dict(
        available=True,
        reason=None,
        reference_energy=h,
        beta=b,
        q=magnitude,
        d=float(d.mean()),
        aggregate_d=aggregate_d,
        scene_variation=variation,
        corrected_alignment=float(b / np.sqrt(magnitude)) if magnitude > 0 else None,
        scene_beta=beta.tolist(),
        scene_q=q.tolist(),
        scene_d=d.tolist(),
        calibration=calibration,
    )


def _pair_metrics(named, prototypes):
    rows = []
    for a, b in PAIR_INDICES:
        target = prototypes[a] - prototypes[b]
        h = float(target @ target)
        difference = named[:, :, a] - named[:, :, b]
        if h > 0:
            beta = np.einsum("skj,j->s", difference, target) / (2 * h)
            q = (difference[:, 0] * difference[:, 1]).sum(axis=1) / h
            error = difference - target
            d = (error[:, 0] * error[:, 1]).sum(axis=1) / h
        else:
            beta = q = d = None
        rows.append(
            dict(
                artists=[ARTISTS[a], ARTISTS[b]],
                indices=[a, b],
                reference_energy=h,
                beta=float(beta.mean()) if h > 0 else None,
                q=float(q.mean()) if h > 0 else None,
                d=float(d.mean()) if h > 0 else None,
                scene_beta=beta.tolist() if h > 0 else [None] * len(named),
            )
        )
    return rows


def _cross_components(shifts):
    """Average scene-level cross-products, with repeats on axis one."""
    common = shifts.mean(axis=2)
    specific = shifts - common[:, :, None]
    shared = float(4 * (common[:, 0] * common[:, 1]).sum(axis=1).mean())
    between = float((specific[:, 0] * specific[:, 1]).sum(axis=(1, 2)).mean())
    total = shared + between
    return dict(
        common_ss=shared,
        specific_ss=between,
        total_ss=total,
        common_fraction=shared / total if total > 0 else None,
        specific_fraction=between / total if total > 0 else None,
    )


def _shared(x, baseline):
    shifts = x[:, :, 2:] - x[:, :, baseline : baseline + 1]
    return dict(
        baseline=ARMS[baseline],
        scene_averaged=_cross_components(shifts.mean(axis=0, keepdims=True)),
        within_scene=_cross_components(shifts),
    )


def _shared_influence(x, baseline):
    values = [
        _shared(np.delete(x, i, axis=0), baseline)["scene_averaged"]["common_fraction"]
        for i in range(len(x))
    ]
    return dict(deletion_values=values, range=_range(values))


def _recognition(groups, prototypes):
    """Rows are true painters; columns are predicted painters; ties choose first."""
    norms = np.linalg.norm(prototypes, axis=1)
    counts = [len(group) for group in groups]
    if np.any(norms <= 0):
        return dict(
            available=False,
            reason="zero_norm_reference_prototype",
            counts=counts,
            confusion_counts=None,
            confusion_row_fractions=None,
            per_painter_accuracy=None,
            macro_accuracy=None,
            micro_accuracy=None,
        )
    unit_prototypes = prototypes / norms[:, None]
    confusion = np.zeros((4, 4), dtype=np.int64)
    mean_margins, tied = [], []
    for a, group in enumerate(groups):
        scores = group @ unit_prototypes.T
        predictions = scores.argmax(axis=1)
        confusion[a] = np.bincount(predictions, minlength=4)
        other_best = np.delete(scores, a, axis=1).max(axis=1)
        mean_margins.append(float((scores[:, a] - other_best).mean()))
        tied.append(int((np.sum(scores == scores.max(axis=1, keepdims=True), axis=1) > 1).sum()))
    fractions = confusion / np.asarray(counts)[:, None]
    accuracies = np.diag(fractions)
    return dict(
        available=True,
        reason=None,
        counts=counts,
        confusion_counts=confusion.tolist(),
        confusion_row_fractions=fractions.tolist(),
        per_painter_accuracy=accuracies.tolist(),
        macro_accuracy=float(accuracies.mean()),
        micro_accuracy=float(np.trace(confusion) / sum(counts)),
        mean_correct_minus_best_other_margin=mean_margins,
        exact_top_tie_counts=tied,
        tie_break="first prototype in recorded artist order",
    )


def _prototype_summary(x, prototypes):
    arm_means = x.mean(axis=(0, 1))
    similarity = arm_means[2:] @ prototypes.T
    diagonal = np.diag(similarity)
    other_mean = (similarity.sum(axis=1) - diagonal) / 3
    masked = similarity.copy()
    np.fill_diagonal(masked, -np.inf)
    margins = diagonal - masked.max(axis=1)
    free_similarity = arm_means[0] @ prototypes.T
    generic_similarity = arm_means[1] @ prototypes.T
    mean_named = arm_means[2:].mean(axis=0)
    mean_reference = prototypes.mean(axis=0)
    # Sum_a <d_a, r_a> = H beta. Computing the numerator directly also
    # defines the decomposition when H is zero and beta itself is undefined.
    labeled_dot = float(np.sum(_center(arm_means[2:]) * _center(prototypes)))
    gains = {}
    for baseline, scores in enumerate((free_similarity, generic_similarity)):
        common = float((mean_named - arm_means[baseline]) @ mean_reference)
        labeled = labeled_dot / 4
        total = common + labeled
        direct_total = float((diagonal - scores).mean())
        gains["named_minus_" + ARMS[baseline]] = dict(
            common_term=common,
            labeled_term=labeled,
            total=total,
            common_fraction=common / total if total > 0 else None,
            labeled_fraction=labeled / total if total > 0 else None,
            direct_score_total=direct_total,
            identity_residual=total - direct_total,
        )
    # Margins of a mean matrix and mean per-image margins answer different questions.
    named_scores = x[:, :, 2:] @ prototypes.T
    image_margins = []
    for a in range(4):
        scores = named_scores[:, :, a]
        image_margins.append(
            float((scores[:, :, a] - np.delete(scores, a, axis=2).max(axis=2)).mean())
        )
    return dict(
        prototype_normalization="unnormalized mean of unit reference embeddings",
        matrix=similarity.tolist(),
        diagonal=diagonal.tolist(),
        off_diagonal_mean_by_painter=other_mean.tolist(),
        mean_diagonal=float(diagonal.mean()),
        mean_off_diagonal=float(other_mean.mean()),
        correct_minus_mean_other=(diagonal - other_mean).tolist(),
        correct_minus_best_other_from_mean_matrix=margins.tolist(),
        mean_per_image_correct_minus_best_other=image_margins,
        free_diagonal_similarity=free_similarity.tolist(),
        generic_diagonal_similarity=generic_similarity.tolist(),
        named_minus_free=(diagonal - free_similarity).tolist(),
        named_minus_generic=(diagonal - generic_similarity).tolist(),
        mean_named_minus_free=float((diagonal - free_similarity).mean()),
        mean_named_minus_generic=float((diagonal - generic_similarity).mean()),
        common_vs_labeled_prototype_gain=gains,
        algebraic_identity_note=(
            "With four painters, mean_diagonal - mean_off_diagonal = H * beta / 3. "
            "Mean named-minus-baseline diagonal gain = dot(mean_named - baseline, "
            "mean_reference) + H * beta / 4. These agreements are algebraic, "
            "not independent validation. The labeled term is shared by both baselines."
        ),
    )


def _rank_intervals(values, higher_is_better):
    """Competition-rank intervals include ties; these ranks are not p-values."""
    if any(v is None for v in values):
        return [None] * len(values)
    values = np.asarray(values, dtype=np.float64)
    output = []
    for value in values:
        tied = np.isclose(values, value, rtol=1e-10, atol=1e-12)
        better = values > value if higher_is_better else values < value
        strict_better = int(np.sum(better & ~tied))
        output.append([strict_better + 1, strict_better + int(tied.sum())])
    return output


def _permutation_diagnostics(named, prototypes, prototype, geometry):
    mean_contrasts = _center(named).mean(axis=(0, 1))
    target = _center(prototypes)
    similarity = np.asarray(prototype["matrix"])
    h = geometry["reference_energy"]
    rows = []
    for permutation in LABEL_PERMUTATIONS:
        beta = float(np.sum(mean_contrasts * target[list(permutation)]) / h) if h > 0 else None
        d = float(1 - 2 * beta + geometry["q"]) if h > 0 else None
        score = float(similarity[np.arange(4), list(permutation)].mean())
        rows.append(
            dict(
                reference_indices_for_generated_names=list(permutation),
                reference_artists_for_generated_names=[ARTISTS[i] for i in permutation],
                beta=beta,
                d=d,
                prototype_diagonal_mean=score,
            )
        )
    # Exact rankings are identical. Apply the tolerance once in beta units
    # rather than inventing different ties after affine score transformations.
    beta_ranks = _rank_intervals([row["beta"] for row in rows], True)
    for key in ("beta", "d", "prototype_diagonal_mean"):
        ranks = beta_ranks
        if h <= 0 and key == "prototype_diagonal_mean":
            ranks = _rank_intervals([row[key] for row in rows], True)
        for row, rank in zip(rows, ranks):
            row[key + "_rank_interval"] = rank
    return dict(
        interpretation="descriptive label negative controls; ranks are not p-values",
        algebraic_dependence=(
            "Beta, D and diagonal-similarity permutation ranks coincide algebraically; "
            "their agreement is not independent evidence."
        ),
        rank_tolerance=dict(
            rtol=1e-10,
            atol=1e-12,
            scale="beta if H > 0; prototype similarity otherwise",
            grouping="one beta-based grouping reused for all three scores when H > 0",
        ),
        identity_index=0,
        identity=rows[0],
        rows=rows,
    )


def _influence(geometry, pairs, named, prototypes):
    n = len(named)

    def deletions(values):
        if any(v is None for v in values):
            output = [None] * n
        else:
            array = np.asarray(values, dtype=np.float64)
            output = ((array.sum() - array) / (n - 1)).tolist()
        return dict(deletion_values=output, range=_range(output))

    conditional_d = deletions(geometry["scene_d"])
    conditional_d["estimand"] = "mean of scene-conditional cross-repeat errors"
    if geometry["reference_energy"] > 0:
        error = _center(named) - _center(prototypes)
        omitted_means = (error.sum(axis=0, keepdims=True) - error) / (n - 1)
        aggregate_values = (
            (omitted_means[:, 0] * omitted_means[:, 1]).sum(axis=(1, 2))
            / geometry["reference_energy"]
        ).tolist()
    else:
        aggregate_values = [None] * n
    return dict(
        interpretation="leave-one-scene-out influence ranges, not confidence intervals",
        beta=deletions(geometry["scene_beta"]),
        d=conditional_d,
        aggregate_d=dict(
            estimand="cross-repeat error after averaging the retained scenes",
            deletion_values=aggregate_values,
            range=_range(aggregate_values),
        ),
        monet_sisley_beta=deletions(pairs[0]["scene_beta"]),
    )


def _target_analysis(x, panel):
    prototypes = np.stack([values.mean(axis=0) for values in panel])
    rows = []
    for model, values in zip(MODELS, x):
        named = values[:, :, 2:]
        prototype = _prototype_summary(values, prototypes)
        geometry = _geometry(named, prototypes)
        pairs = _pair_metrics(named, prototypes)
        rows.append(
            dict(
                model=model,
                prototype=prototype,
                recognition=_recognition(
                    [named[:, :, a].reshape(-1, named.shape[-1]) for a in range(4)], prototypes
                ),
                centered=geometry,
                painter_pairs=pairs,
                scene_influence=_influence(geometry, pairs, named, prototypes),
                label_permutations=_permutation_diagnostics(named, prototypes, prototype, geometry),
            )
        )
    return dict(
        counts=[len(values) for values in panel],
        prototype_norms=np.linalg.norm(prototypes, axis=1).tolist(),
        reference_energy=float(np.square(_center(prototypes)).sum()),
        models=rows,
    )


def analyze_arrays(x, refs, devs):
    """Analyze one representation/view and return a JSON-compatible dictionary.

    ``x`` has shape (6 models, 14 scenes, 2 repeats, 6 arms, 768 features).
    Arm order is free, generic, Monet, Sisley, Pissarro, Cezanne; model order
    is ``MODELS``. ``refs`` and ``devs`` each contain four nonempty (n, 768)
    arrays in ``ARTISTS`` order. Every input embedding must be finite and unit
    length (absolute norm tolerance 1e-4); inputs are never renormalized.

    Source identity/count/hash checks belong to the extraction manifest. This
    function records counts but permits smaller panels for constructed tests.
    Undefined ratios become None. Negative cross-products remain negative.
    """
    x = np.asarray(x)
    if x.shape != (6, 14, 2, 6, 768):
        raise ValueError("x must have shape (6, 14, 2, 6, 768)")
    x = _unit_array(x, "x")
    refs, devs = _panel(refs, "refs"), _panel(devs, "devs")
    shared = []
    for model, values in zip(MODELS, x):
        shared.append(
            dict(
                model=model,
                named_minus_free=_shared(values, 0),
                named_minus_generic=_shared(values, 1),
                scene_influence=dict(
                    interpretation="influence ranges, not confidence intervals",
                    named_minus_free_common_fraction=_shared_influence(values, 0),
                    named_minus_generic_common_fraction=_shared_influence(values, 1),
                ),
            )
        )
    prototypes = np.stack([values.mean(axis=0) for values in refs])
    return dict(
        schema_version=1,
        study="painter_learned_audit_v1",
        descriptive_only=True,
        axes=dict(models=list(MODELS), artists=list(ARTISTS), arms=list(ARMS)),
        counts=dict(
            generated=int(np.prod(x.shape[:-1])),
            reference=sum(map(len, refs)),
            development=sum(map(len, devs)),
            scenes=14,
            repeats=2,
            features=768,
        ),
        numerical_policy=dict(
            aggregation_dtype="float64",
            unit_norm_atol=UNIT_ATOL,
            undefined_ratio="null when denominator is nonpositive",
            negative_cross_products="retained",
            prototype_similarity="mean unit image descriptors dotted with unnormalized means",
            recognition="nearest unit-normalized mean reference prototype",
        ),
        interpretation=[
            "Retrospective representation sensitivity; no new confirmatory tests or p-values.",
            "Normalizers differ by representation and view; D is not perceptual fidelity.",
            "Scene influence ranges and permutation ranks are descriptive, not uncertainty tests.",
            "Development targets are existing distinct works, not an independent acquisition.",
            "Common/specific cross-repeat fractions need not lie in [0,1].",
        ],
        shared_change=shared,
        targets=dict(primary=_target_analysis(x, refs), development=_target_analysis(x, devs)),
        development_recognition=_recognition(devs, prototypes),
    )
