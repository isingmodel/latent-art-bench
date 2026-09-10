"""Finite-repeat variance correction in an unchanged, fixed feature geometry.

The observed traces are descriptive ANOVA quantities. The corrected quantities
estimate fixed-scene mean variation and repeat variance only under a model with
mean-zero repeat errors, stable scene-specific covariance, and independence
across repeats and scenes. Scene covariances may differ. These assumptions are
not established by the correction, and no latent, perceptual, or causal validity
is guaranteed. No scenes are treated as a probability sample.

There is no fitting, input/output, randomization test, or confidence interval here.
"""

from __future__ import annotations

import numpy as np


def _inputs(values, scene_weights):
    try:
        if np.iscomplexobj(values) or np.iscomplexobj(scene_weights):
            raise ValueError("complex inputs are not supported")
        x = np.asarray(values, dtype=float)
        weights = np.asarray(scene_weights, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("expected real numeric values and scene weights") from exc
    if x.ndim != 3 or x.shape[0] < 2 or x.shape[1] < 2 or x.shape[2] < 1:
        raise ValueError("expected J by R by D values with J >= 2, R >= 2 and D >= 1")
    if not np.isfinite(x).all():
        raise ValueError("values must be finite")
    if (
        weights.shape != (x.shape[0],)
        or not np.isfinite(weights).all()
        or (weights <= 0).any()
        or (weights >= 1).any()
    ):
        raise ValueError("expected one finite, strictly positive scene weight per scene")
    if not np.isclose(weights.sum(), 1.0, rtol=1e-12, atol=1e-12):
        raise ValueError("scene weights must sum to one; they are not renormalized")
    return x, weights


def _finite_ratio(numerator, denominator):
    if denominator <= 0:
        return None
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        result = np.float64(numerator) / denominator
    return float(result) if np.isfinite(result) else None


def corrected_variance(values, scene_weights):
    """Return JSON-native fixed-scene trace estimates and their scene contributions.

    ``values`` has shape (J scenes, R repeats, D coordinates); repeats have equal
    weight within each scene. ``scene_weights`` is a strictly positive normalized
    length-J vector. Inputs and their feature geometry are left unchanged.

    For unbiased within-scene sample covariance S_b, the correction subtracted
    from observed between-scene trace is sum_b w_b(1-w_b) tr(S_b)/R. Repeat noise
    is sum_b w_b tr(S_b). Corrected total is corrected between plus repeat noise,
    estimating the total variance of a new draw from the fixed scene mixture
    under the module's error assumptions. It differs from observed total trace.

    Negative corrected-between estimates and negative signal/noise ratios are
    retained without truncation. A ratio is None if its denominator is zero or
    its floating-point value is nonfinite; None is not evidence of no signal.
    Per-scene fields are contributions to the corresponding aggregate, except
    ``sample_covariance_trace``, which is unweighted. No ratio is asserted to be
    an unbiased estimator of a population ratio. All outputs are descriptive or
    assumption-dependent estimates, not inference or validation of the model.
    """
    x, weights = _inputs(values, scene_weights)
    scenes, repeats, features = x.shape
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            means = x.mean(axis=1)
            center = weights @ means
            squared_residuals = np.square(x - means[:, None, :]).sum(axis=(1, 2))
            sample_trace = squared_residuals / (repeats - 1)
            between = weights * np.square(means - center).sum(axis=1)
            within = weights * squared_residuals / repeats
            noise = weights * sample_trace
            correction = weights * (1 - weights) * sample_trace / repeats
            total = weights * np.square(x - center).sum(axis=(1, 2)) / repeats
            observed_between = float(between.sum())
            observed_within = float(within.sum())
            observed_total = float(total.sum())
            repeat_noise = float(noise.sum())
            centroid_noise_correction = float(correction.sum())
            corrected_between = observed_between - centroid_noise_correction
            corrected_total = corrected_between + repeat_noise
            residual = observed_total - observed_between - observed_within
    except FloatingPointError as exc:
        raise ValueError("input magnitude exceeds finite trace arithmetic") from exc

    aggregate = dict(
        observed_between=observed_between,
        observed_within=observed_within,
        observed_total=observed_total,
        repeat_noise=repeat_noise,
        centroid_noise_correction=centroid_noise_correction,
        corrected_between=corrected_between,
        corrected_total=corrected_total,
        observed_identity_residual=residual,
    )
    if not np.isfinite(list(aggregate.values())).all():
        raise ValueError("input magnitude exceeds finite trace arithmetic")
    if not np.isclose(
        observed_total, observed_between + observed_within, rtol=1e-10, atol=1e-12
    ):
        raise ValueError("observed variance identity failed")
    per_scene = [
        dict(
            scene_index=index,
            scene_weight=float(weights[index]),
            sample_covariance_trace=float(sample_trace[index]),
            observed_between=float(between[index]),
            observed_within=float(within[index]),
            observed_total=float(total[index]),
            repeat_noise=float(noise[index]),
            centroid_noise_correction=float(correction[index]),
            corrected_between=float(between[index] - correction[index]),
        )
        for index in range(scenes)
    ]
    return dict(
        n_scenes=scenes,
        n_repeats=repeats,
        n_features=features,
        scene_weights=weights.tolist(),
        **aggregate,
        corrected_signal_to_noise=_finite_ratio(corrected_between, repeat_noise),
        per_scene=per_scene,
    )


def cross_repeat_residual(residual, scene_weights):
    """Estimate weighted squared residual scene means without diagonal repeat noise.

    Inputs have the same shape/weight contract as ``corrected_variance``. For
    each scene, the estimator is the mean inner product across distinct repeats:
    ``(||sum_r e_br||^2 - sum_r ||e_br||^2) / (R * (R - 1))``. Equivalently it is
    the squared sample-mean residual minus sample-covariance trace divided by R.

    If residuals are N_br - T_b(F_br), T_b must exclude every observation of scene
    b. Conditional on that scene's fitted map, stable residual means and zero
    cross-repeat error covariance justify interpreting the estimate as squared
    mismatch of conditional scene means. Within-repeat named/free dependence is
    allowed. This function cannot check those design assumptions. Cross-fitting
    does not make different scenes independent: their training sets can overlap,
    and conditional independence given all fitted maps is not asserted.

    This estimates conditional-mean mismatch, not equality of full distributions,
    perceptual adequacy, or latent gain. Negative estimates are retained. There is
    no interval, test or zero-truncation. Per-scene entries are weighted additive
    contributions, except the unweighted sample-covariance trace.
    """
    x, weights = _inputs(residual, scene_weights)
    scenes, repeats, features = x.shape
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            means = x.mean(axis=1)
            sample_trace = np.square(x - means[:, None, :]).sum(axis=(1, 2)) / (repeats - 1)
            naive = weights * np.square(means).sum(axis=1)
            correction = weights * sample_trace / repeats
            cross_repeat = naive - correction
            aggregate = dict(
                naive_mean_residual_squared=float(naive.sum()),
                correction=float(correction.sum()),
                cross_repeat_mean_square=float(cross_repeat.sum()),
            )
    except FloatingPointError as exc:
        raise ValueError("input magnitude exceeds finite trace arithmetic") from exc
    if not np.isfinite(list(aggregate.values())).all():
        raise ValueError("input magnitude exceeds finite trace arithmetic")
    return dict(
        n_scenes=scenes,
        n_repeats=repeats,
        n_features=features,
        scene_weights=weights.tolist(),
        **aggregate,
        per_scene=[
            dict(
                scene_index=index,
                scene_weight=float(weights[index]),
                sample_covariance_trace=float(sample_trace[index]),
                naive_mean_residual_squared=float(naive[index]),
                correction=float(correction[index]),
                cross_repeat_mean_square=float(cross_repeat[index]),
            )
            for index in range(scenes)
        ],
    )
