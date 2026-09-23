"""Descriptive, noise-inclusive energies of realized historical 31-feature arrays.

This new precollection secondary never estimates repeat-corrected squared change.
There is one observation per assigned cell/window. Scene means precede squaring;
scalar energies are then averaged over all eight windows, when complete. These
functions perform no extraction, scaling, fitting, file access or inference.
"""

from __future__ import annotations

import json
from itertools import combinations
from typing import Any, Mapping, Sequence

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import NAMES

from .protocol import ARMS, ARTISTS, MODELS, SCENES

SHAPE = (6, 8, 12, 8, 31)
BASELINES = ARMS[:4]
PATHS = (
    ("free", "generic"),
    ("generic", "style_frame"),
    ("style_frame", "shared_family"),
    ("generic", "shared_family"),
)
SCALER_PATH = (
    "data/manifests/painter_feature_generation_v2/"
    "pfg2-method-20260905/scaler.json"
)


def _plain(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value


def _census(generated: Any, observed: Any) -> tuple[np.ndarray, np.ndarray]:
    if np.ma.isMaskedArray(generated):
        raise ValueError("pass an explicit observed mask; masked arrays are ambiguous")
    values = np.asarray(generated, dtype=float)
    if values.shape != SHAPE:
        raise ValueError(f"expected already-standardized historical feature axes {SHAPE}")
    finite = np.isfinite(values).all(axis=-1)
    whole_nan = np.isnan(values).all(axis=-1)
    if not np.all(finite | whole_nan):
        raise ValueError("each cell must be entirely finite or entirely NaN; no infinity")
    if observed is None:
        mask = finite
    else:
        mask = np.asarray(observed)
        if mask.shape != SHAPE[:-1] or mask.dtype.kind != "b":
            raise ValueError("observed must be a boolean mask of shape (6,8,12,8)")
        if np.any(mask & ~finite):
            raise ValueError("every observed cell must have 31 finite coordinates")
    return np.where(mask[..., None], values, np.nan), mask.copy()


def _summary(values: np.ndarray) -> dict:
    """Strict eight-window summaries; SD and deletion means are descriptive only."""
    complete = bool(np.isfinite(values).all())
    result = dict(
        window_values=_plain(values),
        available_windows=np.flatnonzero(np.isfinite(values)).tolist(),
        complete_eight_windows=complete,
        equal_window_mean=None,
        between_window_sd=None,
        leave_one_window_out=None,
    )
    if complete:
        mean = float(values.mean())
        omitted = np.array([np.delete(values, i).mean() for i in range(8)])
        result.update(
            equal_window_mean=mean,
            between_window_sd=float(values.std(ddof=1)),
            leave_one_window_out=dict(
                means=omitted.tolist(), change_from_full_mean=(omitted - mean).tolist()
            ),
        )
    return result


def _energy(values: np.ndarray) -> np.ndarray:
    return np.sum(values * values, axis=-1)


def _components(values: np.ndarray) -> dict:
    # Arithmetic mean propagates any missing scene: no nanmean or subset panel.
    arm_means = values.mean(axis=2)
    named = arm_means[..., 4:8, :]
    named_mean = named.mean(axis=-2)
    centered_named = named - named_mean[..., None, :]
    specific = _energy(centered_named).sum(axis=-1)
    pair_specific = sum(
        _energy(named[..., a, :] - named[..., b, :]) / 4
        for a, b in combinations(range(4), 2)
    )
    baselines = {}
    for index, baseline in enumerate(BASELINES):
        common_vector = named_mean - arm_means[..., index, :]
        common = 4 * _energy(common_vector)
        total = _energy(named - arm_means[..., index, None, :]).sum(axis=-1)
        baselines[baseline] = dict(
            common_vector=common_vector,
            common_energy=common,
            total_energy=total,
            decomposition_residual=total - common - specific,
        )
    paths = {}
    for start, intermediate in PATHS:
        first = arm_means[..., ARMS.index(start), :]
        second = arm_means[..., ARMS.index(intermediate), :]
        control = second - first
        remaining = named_mean - second
        combined = named_mean - first
        control_energy = 4 * _energy(control)
        remaining_energy = 4 * _energy(remaining)
        combined_energy = 4 * _energy(combined)
        interaction = 8 * np.sum(control * remaining, axis=-1)
        paths[f"{start}_via_{intermediate}"] = dict(
            start_baseline=start,
            intermediate_baseline=intermediate,
            vectors=dict(
                control_displacement=control,
                remaining_named_displacement=remaining,
                combined_named_displacement=combined,
            ),
            components=dict(
                control_energy=control_energy,
                remaining_common_energy=remaining_energy,
                combined_common_energy=combined_energy,
                signed_interaction=interaction,
                signed_total_energy_change=combined_energy - remaining_energy,
                scalar_identity_residual=(
                    combined_energy - control_energy - remaining_energy - interaction
                ),
                total_change_identity_residual=(
                    combined_energy - remaining_energy - control_energy - interaction
                ),
                vector_identity_max_abs_residual=np.max(
                    np.abs(combined - control - remaining), axis=-1
                ),
            ),
        )
    return dict(
        arm_means=arm_means,
        named_mean=named_mean,
        centered_named=centered_named,
        specific_energy=specific,
        specific_pairwise_identity_residual=specific - pair_specific,
        baselines=baselines,
        paths=paths,
    )


def analyze_realized_features(
    generated: Any, window_times: Sequence[Any], *, observed: Any = None
) -> dict:
    """Describe fixed (6,8,12,8,31) arrays already using the retained scaler.

    The pure-array interface cannot authenticate feature/scaler provenance or
    assignment membership. A future bound extraction loader must verify both.
    No unit normalization is allowed or performed. False mask cells can contain
    finite placeholder vectors, which are ignored; no partial-NaN cell is valid.
    Timing records are supplied by the caller, never generated by this function.
    """
    if isinstance(window_times, (str, bytes)) or len(window_times) != 8:
        raise ValueError("supply exactly eight externally recorded window timing records")
    try:
        times = json.loads(json.dumps(list(window_times), allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("window timing records must be strict JSON values") from exc
    values, available = _census(generated, observed)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            parts = _components(values)
            models = []
            for model_index, model in enumerate(MODELS):
                baselines = {}
                for baseline, items in parts["baselines"].items():
                    baselines[baseline] = {
                        "common_vectors_by_window": _plain(items["common_vector"][model_index]),
                        **{
                            key: _summary(items[key][model_index])
                            for key in (
                                "common_energy", "total_energy", "decomposition_residual"
                            )
                        },
                    }
                paths = {}
                for path, items in parts["paths"].items():
                    paths[path] = dict(
                        start_baseline=items["start_baseline"],
                        intermediate_baseline=items["intermediate_baseline"],
                        signed_total_energy_change_definition=(
                            "Q[start_baseline] - Q[intermediate_baseline]"
                        ),
                        vectors_by_window={
                            key: _plain(vectors[model_index])
                            for key, vectors in items["vectors"].items()
                        },
                        components={
                            key: _summary(scalars[model_index])
                            for key, scalars in items["components"].items()
                        },
                    )
                models.append(dict(
                    model=model,
                    observed_cells=int(available[model_index].sum()),
                    missing_cells_by_window=(
                        ~available[model_index]
                    ).sum(axis=(1, 2)).tolist(),
                    complete_arm_scene_panels_by_window=(
                        available[model_index].all(axis=1).tolist()
                    ),
                    arm_means_by_window=_plain(parts["arm_means"][model_index]),
                    named_means_by_window=_plain(parts["named_mean"][model_index]),
                    centered_named_vectors_by_window=_plain(
                        parts["centered_named"][model_index]
                    ),
                    specific_energy=_summary(parts["specific_energy"][model_index]),
                    specific_pairwise_identity_residual=_summary(
                        parts["specific_pairwise_identity_residual"][model_index]
                    ),
                    baselines=baselines,
                    paths=paths,
                ))
    except FloatingPointError as exc:
        raise ValueError("feature magnitude overflows a derived energy or summary") from exc
    missing = [
        dict(model=MODELS[m], model_index=int(m), window=int(w), scene=SCENES[s][0],
             scene_index=int(s), arm=ARMS[a], arm_index=int(a))
        for m, w, s, a in np.argwhere(~available)
    ]
    result = dict(
        schema="painter-family-controls-realized-31-feature-energies/1.0",
        status="descriptive secondary; realized request noise included",
        estimand="equal-window mean of energies of each realized fixed-scene mean",
        aggregation="average 12 scenes within arm/window; square; average all 8 windows",
        units="sum of squared historical development-IQR standardized coordinates",
        inference="none; no unbiased conditional-mean energy, ratio, corrected D or interval",
        definitions=dict(
            common_energy="C[b] = 4 ||mean_named - y[b]||^2",
            specific_energy="S = sum_a ||y[a] - mean_named||^2",
            total_energy="Q[b] = sum_a ||y[a] - y[b]||^2 = C[b] + S",
            control_energy="B[b,c] = 4 ||y[c] - y[b]||^2",
            signed_interaction="I[b,c] = 8 dot(y[c] - y[b], mean_named - y[c])",
        ),
        scaler_contract=dict(
            path=SCALER_PATH,
            caller_supplies_already_standardized_values=True,
            provenance_authenticated_by_this_array_function=False,
            new_scaler_fitting=False,
        ),
        axes=dict(
            order=["configuration", "window", "scene", "arm", "feature"],
            shape=list(SHAPE), models=list(MODELS), windows=list(range(8)),
            scenes=[item[0] for item in SCENES], arms=list(ARMS),
            painters=list(ARTISTS), features=list(NAMES),
        ),
        window_times=times,
        observed_cells=int(available.sum()),
        expected_cells=4608,
        missing_cells=missing,
        models=models,
    )
    # Reject accidental non-JSON or nonfinite additions rather than hiding them.
    json.dumps(result, allow_nan=False)
    return result
