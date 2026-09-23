"""Offline, fixed-panel analyses for the prospective family-control protocol.

These functions read no files and perform no collection or feature extraction.
Inputs are supplied embeddings, not images; generated vectors must already use
the frozen encoder's unit-embedding convention. No implicit normalization,
imputation, complete-case reweighting, or query-pool fitting is performed.
"""

from __future__ import annotations

import hashlib
import math
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t

from .protocol import MODELS, SCENES

PAINTER_ORDER = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
ARM_ORDER = ("free", "generic", "style_frame", "shared_family", *PAINTER_ORDER)
PRIMARY_ARMS = (1, 3, 4, 5, 6, 7)
PRIMARY_ENDPOINTS = 12
N_WINDOWS = 8
PRIMARY_DF = 7
COMPONENTS = ("N", "F", "S", "L", "C_G", "C_F", "F-S", "N-F", "T")
UNIT_NORM_TOLERANCE = 1e-4


def _plain(value: Any) -> Any:
    """Convert arrays and missing values to strict JSON-compatible data."""
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _reference(reference_means: Any, features: int) -> np.ndarray:
    reference = np.asarray(reference_means, dtype=float)
    if reference.shape != (4, features) or not np.isfinite(reference).all():
        raise ValueError("reference_means must be a finite raw (4, D) array")
    if np.any(np.linalg.norm(reference, axis=-1) > 1 + UNIT_NORM_TOLERANCE):
        raise ValueError("raw reference means of unit vectors cannot have norm above one")
    return reference


def _census(values: Any, prefix: tuple, observed: Any = None) -> tuple:
    array = np.asarray(values, dtype=float)
    if array.ndim != len(prefix) + 1 or array.shape[:-1] != prefix or array.shape[-1] < 1:
        raise ValueError(f"expected axes {prefix} followed by nonempty feature axis")
    if np.isinf(array).any():
        raise ValueError("infinite feature values are invalid; use missing cells explicitly")
    finite = np.isfinite(array).all(axis=-1)
    if observed is None:
        if np.any(~finite & ~np.isnan(array).all(axis=-1)):
            raise ValueError("automatic missing cells must be whole-vector NaN, not partial NaN")
        available = finite
    else:
        mask = np.asarray(observed)
        if mask.shape != prefix or mask.dtype.kind != "b":
            raise ValueError("observed must be a boolean cell mask with the fixed axes")
        if np.any(mask & ~finite):
            raise ValueError("an observed cell cannot contain nonfinite features")
        available = mask.copy()
    norms = np.linalg.norm(array[available], axis=-1)
    unit = np.abs(norms - 1) <= UNIT_NORM_TOLERANCE
    if not unit.all():
        raise ValueError("observed embeddings must be unit vectors; no implicit normalization")
    clean = np.where(available[..., None], array, np.nan)
    return clean, available


def _times(window_times: Sequence[Any]) -> list:
    if isinstance(window_times, (str, bytes)) or len(window_times) != N_WINDOWS:
        raise ValueError("supply eight externally recorded window timing records")
    return _plain(list(window_times))


def _summary(values: np.ndarray) -> dict:
    complete = bool(np.isfinite(values).all())
    result = {
        "window_values": _plain(values),
        "complete_eight_windows": complete,
        "equal_window_mean": None,
        "between_window_sd": None,
        "leave_one_window_out": None,
    }
    if complete:
        mean = float(values.mean())
        omitted = (values.sum() - values) / (N_WINDOWS - 1)
        result.update(
            equal_window_mean=mean,
            between_window_sd=float(values.std(ddof=1)),
            leave_one_window_out={
                "means": omitted.tolist(),
                "change_from_full_mean": (omitted - mean).tolist(),
            },
        )
    return result


def correlation_sensitivities() -> list:
    """Assumed equicorrelation multipliers relative to observed sample-SD SE."""
    return [
        {"assumed_rho": rho, "se_multiplier": math.sqrt((1 + 7 * rho) / (1 - rho))}
        for rho in (0.0, 0.1, 0.25, 0.5)
    ]


def window_components(generated: Any, reference_means: Any, *, observed: Any = None) -> dict:
    """Return equal-scene components; any missing needed scene makes its window missing.

    Axes: model (6), window (8), scene (12), arm (8), feature (D).
    Reference means remain raw, without unit normalization. Component masks are
    separate: a missing free/style arm does not invalidate N or F.
    """
    features, available = _census(generated, (6, 8, 12, 8), observed)
    reference = _reference(reference_means, features.shape[-1])
    target = reference.mean(axis=0)
    reference_contrast = reference - target
    named = features[..., 4:8, :]
    named_mean = named.mean(axis=-2)
    generic, style, family = (features[..., index, :] for index in (1, 2, 3))
    diagonal = np.einsum("...ad,ad->...a", named, reference).mean(axis=-1)
    n = diagonal - np.einsum("...d,d->...", generic, target)
    f = np.einsum("...d,d->...", family - generic, target)
    s = np.einsum("...d,d->...", style - generic, target)
    labeled = np.einsum(
        "...ad,ad->...a", named - named_mean[..., None, :], reference_contrast
    ).mean(axis=-1)
    common = np.einsum("...d,d->...", named_mean - generic, target)
    # Compute contrasts from their actual required arms. Generic cancels from
    # these secondary contrasts, so a missing generic image must not erase them.
    family_common = np.einsum("...d,d->...", named_mean - family, target)
    scene_terms = {
        "N": n,
        "F": f,
        "S": s,
        "L": labeled,
        "C_G": common,
        "C_F": family_common,
        "F-S": np.einsum("...d,d->...", family - style, target),
        "N-F": diagonal - np.einsum("...d,d->...", family, target),
        "T": f - 0.5 * n,
    }
    windows = {key: value.mean(axis=2) for key, value in scene_terms.items()}
    free = features[..., 0, :]
    free_n = diagonal - np.einsum("...d,d->...", free, target)
    free_common = np.einsum("...d,d->...", named_mean - free, target)
    pairwise = []
    for first, second in combinations(range(4), 2):
        reference_difference = reference[first] - reference[second]
        energy = float(reference_difference @ reference_difference)
        alignment = np.einsum(
            "...d,d->...", named[..., first, :] - named[..., second, :], reference_difference
        ).mean(axis=2)
        pairwise.append(
            {
                "painters": [PAINTER_ORDER[first], PAINTER_ORDER[second]],
                "reference_difference_energy": energy,
                "aligned_dot_window_values": alignment,
                "beta_window_values": alignment / energy if energy > 0 else None,
            }
        )
    return {
        "components": windows,
        "observed": available,
        "primary_complete_windows": available[..., PRIMARY_ARMS].all(axis=(2, 3)),
        "reference_contrast_energy_sum": float(np.sum(reference_contrast**2)),
        "reference_contrast_energy_mean": float(np.mean(np.sum(reference_contrast**2, axis=1))),
        "free_baseline": {"N_free": free_n.mean(axis=2), "C_free": free_common.mean(axis=2)},
        "pairwise": pairwise,
    }


def primary_decision(n_interval: Sequence[float], t_interval: Sequence[float]) -> str:
    """Strict prespecified boundaries; an endpoint touching zero is unresolved."""
    n_low, n_high = n_interval
    t_low, t_high = t_interval
    if not np.isfinite([n_low, n_high, t_low, t_high]).all():
        raise ValueError("decision intervals must be finite")
    if n_low > n_high or t_low > t_high:
        raise ValueError("interval endpoints are out of order")
    if n_low > 0 and t_low > 0:
        return "name_free_prompt_exceeds_half_positive_named_gain"
    if n_low > 0 and t_high < 0:
        return "name_free_prompt_below_half_positive_named_gain"
    return "unresolved"


def _interval(values: np.ndarray, critical: float) -> dict:
    mean = float(values.mean())
    sd = float(values.std(ddof=1))
    se = sd / math.sqrt(N_WINDOWS)
    return {
        "mean": mean,
        "sd": sd,
        "se": se,
        "lower": mean - critical * se,
        "upper": mean + critical * se,
    }


def analyze_primary(
    generated: Any,
    reference_means: Any,
    window_times: Sequence[Any],
    *,
    observed: Any = None,
    representation: str = "csd",
) -> dict:
    """Prespecified CSD 12-endpoint family; incomplete models get no primary inference.

    Another model's missing cells never reduce the Bonferroni family size. All
    available window values, secondary components and the full missing census
    remain visible. Timing records are supplied externally, never fabricated.
    """
    if representation != "csd":
        raise ValueError("only the fixed CSD representation belongs to the primary family")
    times = _times(window_times)
    terms = window_components(generated, reference_means, observed=observed)
    critical = float(student_t.ppf(1 - 0.05 / (2 * PRIMARY_ENDPOINTS), PRIMARY_DF))
    models = []
    for model in range(6):
        components = {key: _summary(values[model]) for key, values in terms["components"].items()}
        complete_windows = terms["primary_complete_windows"][model]
        complete = bool(complete_windows.all())
        intervals, decision = {}, "unavailable_incomplete_primary_census"
        if complete:
            intervals = {
                key: _interval(terms["components"][key][model], critical) for key in ("N", "T")
            }
            decision = primary_decision(
                [intervals["N"]["lower"], intervals["N"]["upper"]],
                [intervals["T"]["lower"], intervals["T"]["upper"]],
            )
        ratios = {}
        for label, numerator, denominator in (
            ("F/N", "F", "N"),
            ("C_G/N", "C_G", "N"),
            ("C_F/(N-F)", "C_F", "N-F"),
        ):
            x = terms["components"][numerator][model]
            y = terms["components"][denominator][model]
            ratios[label] = (
                fieller_confidence_set(x, y)
                if np.isfinite([x, y]).all()
                else {"status": "unavailable_incomplete_paired_windows"}
            )
        models.append(
            {
                "model_index": model,
                "model": MODELS[model],
                "primary_complete": complete,
                "primary_complete_windows": complete_windows,
                "missing_cells_window_scene_arm": np.argwhere(~terms["observed"][model]),
                "components": components,
                "primary_intervals": intervals,
                "decision": decision,
                "secondary_ratios": ratios,
                "free_baseline": {
                    key: _summary(value[model]) for key, value in terms["free_baseline"].items()
                },
                "pairwise_alignment": [
                    {
                        "painters": item["painters"],
                        "reference_difference_energy": item["reference_difference_energy"],
                        "aligned_dot": _summary(item["aligned_dot_window_values"][model]),
                        "beta": (
                            _summary(item["beta_window_values"][model])
                            if item["beta_window_values"] is not None
                            else None
                        ),
                    }
                    for item in terms["pairwise"]
                ],
            }
        )
    return _plain(
        {
            "status": "offline_array_analysis",
            "representation": representation,
            "axis_order": ["model", "window", "scene", "arm", "feature"],
            "arm_order": ARM_ORDER,
            "model_order": MODELS,
            "scene_order": [scene[0] for scene in SCENES],
            "painter_order": PAINTER_ORDER,
            "window_times": times,
            "primary_family_size": PRIMARY_ENDPOINTS,
            "confidence": 0.95,
            "degrees_of_freedom": PRIMARY_DF,
            "critical_t": critical,
            "half_width_per_observed_sd": critical / math.sqrt(8),
            "estimand": "equal mean of fixed 12-scene effects across all eight windows",
            "interval_assumption": "independent, suitably behaved full-panel window summaries",
            "correlation_sensitivities": correlation_sensitivities(),
            "sensitivity_status": "assumed correlations; not estimated corrections",
            "reference_contrast_energy_sum": terms["reference_contrast_energy_sum"],
            "reference_contrast_energy_mean": terms["reference_contrast_energy_mean"],
            "reference_energy_convention": "historical H is the sum; painter mean is H/4",
            "identities": [
                "N = C_G + L",
                "N-F = C_F + L",
                "C_F = C_G-F",
                "T = F-0.5*N; L is invariant to common-control subtraction",
            ],
            "models": models,
        }
    )


def _quadratic_confidence_set(a: float, b: float, c: float, *, origin: float = 0.0) -> dict:
    """Solve a*(r-origin)**2+b*(r-origin)+c <= 0, retaining infinite sets."""
    if not np.isfinite([a, b, c, origin]).all():
        raise ValueError("confidence-set coefficients must be finite")

    def result(kind: str, intervals: list) -> dict:
        # Null bounds mean infinity, explicitly tagged by topology and this key.
        return {
            "kind": kind,
            "intervals": intervals,
            "infinite_bound_encoding": "null lower=-infinity; null upper=+infinity",
            "finite_boundaries_included": True,
        }

    if a == 0:
        if b == 0:
            return result("all_real", [[None, None]]) if c <= 0 else result("empty", [])
        boundary = float(origin - c / b)
        return result("half_line", [[None, boundary]] if b > 0 else [[boundary, None]])
    # Scale before evaluating the discriminant to avoid needless overflow.
    scale = max(abs(a), abs(b), abs(c))
    aa, bb, cc = (np.longdouble(value) / np.longdouble(scale) for value in (a, b, c))
    discriminant = bb * bb - 4 * aa * cc
    if discriminant < 0:
        return result("empty", []) if a > 0 else result("all_real", [[None, None]])
    if discriminant == 0:
        boundary = float(origin - bb / (2 * aa))
        return (
            result("singleton", [[boundary, boundary]])
            if a > 0
            else result("all_real", [[None, None]])
        )
    root = np.sqrt(discriminant)
    q = -0.5 * (bb + np.copysign(root, bb))
    low, high = sorted([float(origin + q / aa), float(origin + cc / q)])
    if a > 0:
        return result("bounded", [[low, high]])
    return result("disconnected", [[None, low], [high, None]])


def fieller_confidence_set(numerator: Any, denominator: Any, *, confidence: float = 0.95) -> dict:
    """Secondary Fieller set for ratio of eight paired component means (df=7).

    Negative/zero denominators are retained; no window is removed. Raw signed
    ratios are separate from positive-denominator shares. A share can lie
    outside [0,1]. Confidence sets are never replaced by finite display limits.
    """
    x, y = np.asarray(numerator, dtype=float), np.asarray(denominator, dtype=float)
    if x.shape != (8,) or y.shape != (8,) or not np.isfinite([x, y]).all():
        raise ValueError("Fieller requires all eight finite paired window components")
    if not 0 < confidence < 1:
        raise ValueError("confidence must lie strictly between zero and one")
    x_mean, y_mean = float(x.mean()), float(y.mean())
    covariance_of_means = np.cov(np.stack([x, y]), ddof=1) / N_WINDOWS
    critical = float(student_t.ppf((1 + confidence) / 2, PRIMARY_DF))
    raw = x_mean / y_mean if y_mean != 0 else None
    # Invert around the ratio estimate, using residuals before squaring. The
    # expanded discriminant catastrophically cancels for nearly proportional
    # pairs and can otherwise return an empty set excluding the point estimate.
    # Independent positive scales avoid underflow when numerator and denominator
    # differ greatly in magnitude. Solve in scaled-ratio coordinates, then map
    # boundaries back. No tolerance collapses a narrow set.
    x_scale = np.max(np.abs(x)) or 1.0
    y_scale = np.max(np.abs(y)) or 1.0
    ratio_scale = np.longdouble(x_scale) / np.longdouble(y_scale)
    if not np.isfinite(ratio_scale) or ratio_scale == 0:
        raise ValueError("ratio scale is outside the runtime's finite numeric range")
    xs, ys = x.astype(np.longdouble) / x_scale, y.astype(np.longdouble) / y_scale
    xm, ym = xs.mean(), ys.mean()
    centered_y = ys - ym
    mean_variance_divisor = N_WINDOWS * (N_WINDOWS - 1)
    q2 = np.longdouble(critical) ** 2
    sum_y_squared = np.sum(centered_y**2)
    solver_a = ym**2 - q2 * sum_y_squared / mean_variance_divisor
    if solver_a > 0:
        origin = xm / ym
        residual_mean = np.longdouble(0)
    else:
        # A weak denominator makes xbar/ybar an unstable, possibly huge origin.
        # Center at the paired regression slope instead; near-proportional
        # residuals stay small without shifting bounded roots by a huge number.
        origin = (np.sum((xs - xm) * centered_y) / sum_y_squared
                  if sum_y_squared > 0 else np.longdouble(0))
        residual_mean = xm - origin * ym
    residual = (xs - xm) - origin * centered_y
    solver_b = (-2 * residual_mean * ym
                + 2 * q2 * np.sum(residual * centered_y) / mean_variance_divisor)
    solver_c = residual_mean**2 - q2 * np.sum(residual**2) / mean_variance_divisor
    confidence_set = _quadratic_confidence_set(
        solver_a, solver_b, solver_c, origin=origin
    )
    confidence_set["intervals"] = [
        [float(bound * ratio_scale) if bound is not None else None for bound in interval]
        for interval in confidence_set["intervals"]
    ]
    if any(not np.isfinite(bound) for interval in confidence_set["intervals"]
           for bound in interval if bound is not None):
        raise ValueError("finite Fieller boundary is outside the runtime's numeric range")
    # Exact constant inputs have no sampling variance. Avoid rounding the
    # double root into an empty set when the deterministic ratio is nonbinary.
    if np.all(x == x[0]) and np.all(y == y[0]) and y[0] != 0:
        confidence_set = dict(confidence_set, kind="singleton", intervals=[[raw, raw]])
    elif np.any(y != 0):
        index = int(np.flatnonzero(y != 0)[0])
        proportional_ratio = float(x[index] / y[index])
        # Exact proportional paired observations imply A*(r-k)^2 <= 0.
        # Solve that form directly; rounding its expanded discriminant must
        # not turn a zero-width confidence set into an empty confidence set.
        # This uses exact equality, not a tolerance that collapses narrow sets.
        if np.array_equal(x, proportional_ratio * y):
            confidence_set = dict(
                confidence_set,
                kind="singleton" if solver_a > 0 else "all_real",
                intervals=(
                    [[proportional_ratio, proportional_ratio]] if solver_a > 0 else [[None, None]]
                ),
            )
    return _plain(
        {
            "status": "secondary_conditional_approximation",
            "confidence": confidence,
            "degrees_of_freedom": PRIMARY_DF,
            "target": "ratio_of_window_means",
            "numerator_mean": x_mean,
            "denominator_mean": y_mean,
            "numerator_windows": x,
            "denominator_windows": y,
            "raw_signed_ratio": raw,
            "positive_denominator_share": raw if y_mean > 0 else None,
            "denominator_status": (
                "positive" if y_mean > 0 else "negative" if y_mean < 0 else "zero"
            ),
            "covariance_of_paired_means": covariance_of_means,
            "solver": ("scaled residuals at ratio for strong denominator; "
                       "regression slope otherwise"),
            "solver_origin": origin,
            "solver_coordinate": "z = ratio / ratio_scale - solver_origin",
            "ratio_scale": ratio_scale,
            "solver_quadratic_coefficients": {
                "a": solver_a, "b": solver_b, "c": solver_c,
            },
            "confidence_set": confidence_set,
            "familywise_claim": False,
        }
    )


def _unit_prototypes(means: np.ndarray, label: str) -> np.ndarray:
    norms = np.linalg.norm(means, axis=-1, keepdims=True)
    if np.any(norms == 0) or not np.isfinite(norms).all():
        raise ValueError(f"{label} has a zero or nonfinite prototype norm")
    return means / norms


def _array_digest(array: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(str(array.shape).encode("ascii"))
    digest.update(np.asarray(array, dtype="<f8").tobytes(order="C"))
    return digest.hexdigest()


def fit_transport_parameters(old_named: Any, reference_means: Any, *, encoder: str = "csd") -> dict:
    """Fit from the full old 6 x 14 x 2 x 4 x D cohort only; no new-query argument.

    Call only after the authorized precollection freeze workflow supplies old
    inputs. The implementation tests use constructed old arrays exclusively.
    Returned lists are detached from input storage and can be frozen/hashed.
    """
    old = np.asarray(old_named, dtype=float)
    if old.ndim != 5 or old.shape[:-1] != (6, 14, 2, 4) or old.shape[-1] < 1:
        raise ValueError("old_named must have axes (6,14,2,4,D)")
    if not np.isfinite(old).all():
        raise ValueError("old transport fit requires the complete finite old cohort")
    if np.any(np.abs(np.linalg.norm(old, axis=-1) - 1) > UNIT_NORM_TOLERANCE):
        raise ValueError("old observed embeddings must be unit vectors")
    reference = _reference(reference_means, old.shape[-1])
    class_means = old.mean(axis=(1, 2))
    generated_grand_mean = class_means.mean(axis=1)
    translation = reference.mean(axis=0)[None, :] - generated_grand_mean
    return _plain(
        {
            "schema": "painter_family_controls_v1.transport.v1",
            "encoder": encoder,
            "model_order": MODELS,
            "painter_order": PAINTER_ORDER,
            "fit_axes": [6, 14, 2, 4, old.shape[-1]],
            "fit_scope": "old_full_frame_named_cohort_only",
            "translation_scale": 1.0,
            "old_array_sha256": _array_digest(old),
            "reference_array_sha256": _array_digest(reference),
            "raw_reference_means": reference,
            "reference_prototypes": _unit_prototypes(reference, "reference"),
            "old_generated_class_means": class_means,
            "old_generated_grand_mean": generated_grand_mean,
            "translation": translation,
            "generated_prototypes": _unit_prototypes(class_means, "old generated"),
            "tie_rule": "first exact maximum in retained painter order",
        }
    )


def _parameters(parameters: Mapping, features: int) -> tuple:
    if parameters.get("schema") != "painter_family_controls_v1.transport.v1":
        raise ValueError("unrecognized frozen transport schema")
    if tuple(parameters.get("painter_order", ())) != PAINTER_ORDER:
        raise ValueError("frozen painter order must match the retained truth order")
    if tuple(parameters.get("model_order", ())) != MODELS:
        raise ValueError("frozen model order must match the fixed six configurations")
    if parameters.get("translation_scale") != 1.0:
        raise ValueError("translation scale is frozen at one")
    reference = np.asarray(parameters["reference_prototypes"], dtype=float)
    generated = np.asarray(parameters["generated_prototypes"], dtype=float)
    translation = np.asarray(parameters["translation"], dtype=float)
    for array, shape in (
        (reference, (4, features)),
        (generated, (6, 4, features)),
        (translation, (6, features)),
    ):
        if array.shape != shape or not np.isfinite(array).all():
            raise ValueError("frozen parameter shape/finite-value mismatch")
    for array in (reference, generated):
        if not np.allclose(np.linalg.norm(array, axis=-1), 1, rtol=0, atol=1e-12):
            raise ValueError("frozen classifier prototypes must be unit length")
    return reference, generated, translation


def _prediction_scores(scores: np.ndarray, available: np.ndarray) -> dict:
    # NaNs are replaced only for argmax bookkeeping; missing decisions stay null.
    safe = np.where(available[..., None], scores, 0.0)
    prediction = np.argmax(safe, axis=-1)
    top = np.max(safe, axis=-1)
    tie_mask = safe == top[..., None]
    truth_shape = (1, 1, 1, 4)
    truth = np.broadcast_to(np.arange(4).reshape(truth_shape), prediction.shape)
    true_score = np.take_along_axis(safe, truth[..., None], axis=-1)[..., 0]
    competitors = np.where(np.eye(4, dtype=bool)[None, None, None, :, :], -np.inf, safe)
    signed_margin = true_score - competitors.max(axis=-1)
    return {
        "predictions": np.where(available, prediction, -1),
        "correct": (prediction == truth) & available,
        "scores": scores,
        "tied_classes": tie_mask & available[..., None],
        "exact_tie": (tie_mask.sum(axis=-1) > 1) & available,
        "truth_minus_best_other_margin": np.where(available, signed_margin, np.nan),
    }


def evaluate_transport(
    new_named: Any, frozen_parameters: Mapping, window_times: Sequence[Any], *, observed: Any = None
) -> dict:
    """Apply unchanged rules to the new 6 x 8 x 12 x 4 x D named census.

    Missing-query confusion counts are explicitly observed-only. Fixed-window
    accuracy/recall requires all 48 queries, and an equal-window aggregate needs
    all eight complete windows. No observed-only aggregate replaces that target.
    """
    queries, available = _census(new_named, (6, 8, 12, 4), observed)
    reference, prototypes, translation = _parameters(frozen_parameters, queries.shape[-1])
    times = _times(window_times)
    transformed = queries + translation[:, None, None, None, :]
    scores = {
        "baseline": np.einsum("mwsad,bd->mwsab", queries, reference),
        "translated": np.einsum("mwsad,bd->mwsab", transformed, reference),
        "supervised_generated": np.einsum("mwsad,mbd->mwsab", queries, prototypes),
    }
    rules = {key: _prediction_scores(value, available) for key, value in scores.items()}
    baseline = rules["baseline"]
    complete_windows = available.all(axis=(2, 3))
    models = []
    for model in range(6):
        windows = []
        for window in range(8):
            mask = available[model, window]
            complete = bool(complete_windows[model, window])
            observed_count = int(mask.sum())
            truth = np.broadcast_to(np.arange(4), (12, 4))[mask]
            result = {
                "window_index": window,
                "complete": complete,
                "expected_queries": 48,
                "observed_queries": observed_count,
                "rules": {},
            }
            for rule, output in rules.items():
                predictions = output["predictions"][model, window][mask]
                confusion = np.zeros((4, 4), dtype=int)
                np.add.at(confusion, (truth, predictions), 1)
                counts = confusion.sum(axis=1)
                correct = output["correct"][model, window]
                corrections = mask & ~baseline["correct"][model, window] & correct
                harms = mask & baseline["correct"][model, window] & ~correct
                result["rules"][rule] = {
                    "observed_confusion_truth_rows_prediction_columns": confusion,
                    "observed_queries_per_painter": counts,
                    "observed_correct": int(correct.sum()),
                    "fixed_window_accuracy": float(correct.sum() / 48) if complete else None,
                    "fixed_window_recall": np.diag(confusion) / 12 if complete else None,
                    "corrections_from_baseline": int(corrections.sum()),
                    "harms_from_baseline": int(harms.sum()),
                    "fixed_window_accuracy_difference": (
                        float((corrections.sum() - harms.sum()) / 48) if complete else None
                    ),
                }
            windows.append(result)
        all_complete = bool(complete_windows[model].all())
        aggregate = {}
        for rule in rules:
            rule_windows = [window["rules"][rule] for window in windows]
            aggregate[rule] = {
                "equal_window_accuracy": (
                    float(np.mean([x["fixed_window_accuracy"] for x in rule_windows]))
                    if all_complete
                    else None
                ),
                "equal_window_accuracy_difference": (
                    float(np.mean([x["fixed_window_accuracy_difference"] for x in rule_windows]))
                    if all_complete
                    else None
                ),
                "equal_window_recall": (
                    np.mean([x["fixed_window_recall"] for x in rule_windows], axis=0)
                    if all_complete
                    else None
                ),
                "observed_corrections": sum(x["corrections_from_baseline"] for x in rule_windows),
                "observed_harms": sum(x["harms_from_baseline"] for x in rule_windows),
            }
        models.append(
            {
                "model_index": model,
                "model": MODELS[model],
                "complete_eight_windows": all_complete,
                "windows": windows,
                "aggregate": aggregate,
            }
        )
    records = {}
    for rule, output in rules.items():
        correct = output["correct"]
        corrections = available & ~baseline["correct"] & correct
        harms = available & baseline["correct"] & ~correct
        records[rule] = {
            "scores": output["scores"],
            "prediction_index": np.where(available, output["predictions"], np.nan),
            "correct": np.where(available, correct, np.nan),
            "tied_classes": output["tied_classes"],
            "exact_tie": output["exact_tie"],
            "truth_minus_best_other_margin": output["truth_minus_best_other_margin"],
            "correction_from_baseline": np.where(available, corrections, np.nan),
            "harm_from_baseline": np.where(available, harms, np.nan),
        }
    return _plain(
        {
            "status": "secondary_frozen_transport",
            "encoder": frozen_parameters["encoder"],
            "painter_order": PAINTER_ORDER,
            "model_order": MODELS,
            "scene_order": [scene[0] for scene in SCENES],
            "window_times": times,
            "query_axes": ["model", "window", "scene", "true_painter"],
            "tie_rule": "first exact maximum in retained painter order",
            "missing_cells_model_window_scene_painter": np.argwhere(~available),
            "observed": available,
            "zero_query": (np.linalg.norm(queries, axis=-1) == 0),
            "zero_translated_query": (np.linalg.norm(transformed, axis=-1) == 0),
            "predictions": records,
            "models": models,
            "parameter_old_array_sha256": frozen_parameters.get("old_array_sha256"),
            "parameter_reference_array_sha256": frozen_parameters.get("reference_array_sha256"),
            "familywise_claim": False,
        }
    )
