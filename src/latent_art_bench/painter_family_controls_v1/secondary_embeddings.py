"""Descriptive learned-embedding reports; no extra primary/familywise inference."""

from __future__ import annotations

import numpy as np

from .analysis import (
    _plain,
    _summary,
    _times,
    correlation_sensitivities,
    fieller_confidence_set,
    window_components,
)
from .protocol import ARMS, ARTISTS, MODELS, SCENES
from .reference_panels import ENCODERS, PANEL_IDS


def analyze_secondary(
    generated,
    reference_means,
    window_times,
    *,
    representation,
    reference_panel,
    observed=None,
):
    """Report the fixed six-model/eight-window panel without primary decisions.

    All means and leave-one-window values require their complete fixed panel. The
    same supplied unit queries are used for each target; reference crop selection
    never crops or otherwise transforms prospective generated embeddings.
    """
    if representation not in ENCODERS or reference_panel not in PANEL_IDS:
        raise ValueError("use one fixed encoder and one declared reference panel")
    times = _times(window_times)
    terms = window_components(generated, reference_means, observed=observed)
    energy = terms["reference_contrast_energy_mean"]
    models, missing = [], []
    for model_index, model in enumerate(MODELS):
        model_missing = []
        for window, scene, arm in np.argwhere(~terms["observed"][model_index]):
            item = dict(
                model_index=model_index,
                model=model,
                window=int(window),
                scene_index=int(scene),
                scene_id=SCENES[scene][0],
                arm_index=int(arm),
                arm=ARMS[arm],
            )
            model_missing.append(item)
            missing.append(item)
        ratios = {}
        for label, numerator, denominator in (
            ("F/N", "F", "N"),
            ("C_G/N", "C_G", "N"),
            ("C_F/(N-F)", "C_F", "N-F"),
        ):
            x, y = (terms["components"][key][model_index] for key in (numerator, denominator))
            ratios[label] = (
                fieller_confidence_set(x, y)
                if np.isfinite([x, y]).all()
                else dict(status="unavailable_incomplete_paired_windows")
            )
        models.append(
            dict(
                model_index=model_index,
                model=model,
                observed_cell_count=int(terms["observed"][model_index].sum()),
                expected_cell_count=8 * 12 * 8,
                missing_census=model_missing,
                missing_cells_window_scene_arm=np.argwhere(~terms["observed"][model_index]),
                complete_windows=terms["observed"][model_index].all(axis=(1, 2)),
                components={
                    key: _summary(values[model_index])
                    for key, values in terms["components"].items()
                },
                aggregate_beta=(
                    _summary(terms["components"]["L"][model_index] / energy) if energy > 0 else None
                ),
                secondary_ratios=ratios,
                free_baseline={
                    key: _summary(values[model_index])
                    for key, values in terms["free_baseline"].items()
                },
                pairwise_alignment=[
                    dict(
                        painters=pair["painters"],
                        reference_difference_energy=pair["reference_difference_energy"],
                        aligned_dot=_summary(pair["aligned_dot_window_values"][model_index]),
                        beta=(
                            _summary(pair["beta_window_values"][model_index])
                            if pair["beta_window_values"] is not None
                            else None
                        ),
                    )
                    for pair in terms["pairwise"]
                ],
            )
        )
    return _plain(
        dict(
            status="offline_secondary_array_analysis",
            representation=representation,
            reference_panel=reference_panel,
            primary_inference=False,
            familywise_claim=False,
            inference_scope="secondary descriptions and conditional Fieller sets only",
            axis_order=["model", "window", "scene", "arm", "feature"],
            model_order=MODELS,
            painter_order=ARTISTS,
            arm_order=ARMS,
            scene_order=[scene[0] for scene in SCENES],
            window_order=list(range(8)),
            expected_cell_count=4608,
            observed_cell_count=int(terms["observed"].sum()),
            missing_census=missing,
            window_times=times,
            estimand="equal mean of fixed 12-scene effects across all eight windows",
            missing_policy="no imputation, scene deletion, window deletion or reweighting",
            reference_contrast_energy_sum=terms["reference_contrast_energy_sum"],
            reference_contrast_energy_mean=energy,
            reference_energy_convention="historical H is the sum; painter mean is H/4",
            aggregate_beta_convention="L/(H/4); undefined if reference contrast energy is zero",
            correlation_sensitivities=correlation_sensitivities(),
            sensitivity_status="assumed correlations; not estimated corrections",
            ratio_assumption="independent, suitably behaved paired full-panel window summaries",
            identities=["N = C_G + L", "N-F = C_F + L", "C_F = C_G-F", "T = F-0.5*N"],
            models=models,
        )
    )
