"""Frozen prompt contrasts conditional on the existing finite painting reference."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_distance_v1.analysis import load_source
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, features
from latent_art_bench.painter_feature_generation_v2 import statistics as finite
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)

from . import generation, measurement, randomization
from .common import MANIFESTS
from .prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS

TRANSITIONS = (("by_name", "style_instruction"), ("style_instruction", "style_aspects"))


def compute(
    real,
    rows,
    scaler,
    repetitions,
    alpha=0.05,
    *,
    permutation_seed=20260905,
    permutation_draws=99999,
):
    """Finite contrasts and conditional slot-randomization tests on a complete grid.

    Reference coordinates already use the frozen scaler. New raw rows are transformed once.
    Repetition blocks organize acquisition; the randomization unit is a scene's method slots.
    """
    if type(repetitions) is not int or repetitions not in (1, 2, 4) or alpha != 0.05:
        raise ValueError("prompt randomization requires R=1,2,4 and family alpha=0.05")
    expected = 480 * repetitions
    if (
        len(rows) != expected
        or len({r["image_id"] for r in rows}) != expected
        or any(r["status"] != "measured" for r in rows)
    ):
        raise ValueError("primary prompt inference requires every measured registered request")
    distances, coordinates, primary, secondary, absolute, scene_rows, diagnostics = (
        [] for _ in range(7)
    )
    groups_by_method, ordered_by_method, finite_distances = {}, {}, {}
    template_order = {template: i for i, template in enumerate(TEMPLATE_IDS)}
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            chosen = [r for r in rows if r["alias"] == alias and r["method_id"] == method]
            if len(chosen) != 80 * repetitions or {
                (r["block"], r["condition"], r["template_id"]) for r in chosen
            } != {(b, c, t) for b in range(repetitions) for c in CONDITIONS for t in TEMPLATE_IDS}:
                raise ValueError("method has an incomplete or unexpected block inventory")
            groups = empirical.generated_groups(chosen, scaler)[alias]
            comparison = empirical.finite_comparisons(real, groups)
            coordinates += [
                dict(alias=alias, method_id=method, **r)
                for r in comparison["coordinate_diagnostics"]
            ]
            for condition in CONDITIONS:
                ordered = sorted(
                    (r for r in chosen if r["condition"] == condition),
                    key=lambda r: (r["block"], template_order[r["template_id"]]),
                )
                key = alias, method, condition
                ordered_by_method[key] = ordered
                groups_by_method[key] = finite.transform(
                    np.array([r["values"] for r in ordered]), scaler
                )
            for family, section in features.FAMILIES.items():
                for condition, values in groups.items():
                    for painter in PAINTER_IDS:
                        distance = finite.finite_energy(
                            real[painter][:, section], values[:, section]
                        )
                        finite_distances[alias, method, condition, painter, family] = distance
                        distances.append(
                            dict(
                                alias=alias,
                                method_id=method,
                                condition=condition,
                                painter_id=painter,
                                family=family,
                                distance=distance,
                                generated_count=len(values),
                                reference_count=len(real[painter]),
                            )
                        )
                for painter in PAINTER_IDS:
                    absolute.append(
                        dict(
                            alias=alias,
                            method_id=method,
                            painter_id=painter,
                            family=family,
                            finite_distance=finite_distances[
                                alias, method, painter, painter, family
                            ],
                            inference="descriptive_finite_distance_no_confidence_interval",
                        )
                    )
    for alias in generation.ALIASES:
        for painter in PAINTER_IDS:
            for family, section in features.FAMILIES.items():
                for before, after in TRANSITIONS:
                    old, new = (alias, before, painter), (alias, after, painter)
                    label = dict(
                        alias=alias, painter_id=painter, family=family, before=before, after=after
                    )
                    contributions = randomization.paired_energy_contributions(
                        real[painter][:, section],
                        groups_by_method[old][:, section],
                        groups_by_method[new][:, section],
                    )
                    inferred = randomization.randomization_pvalue(
                        contributions,
                        seed=randomization.endpoint_seed(permutation_seed, len(primary)),
                        draws=permutation_draws,
                    )
                    primary.append(dict(**label, **inferred))
                    ordered_contributions = []
                    for earlier, later, value in zip(
                        ordered_by_method[old], ordered_by_method[new], contributions
                    ):
                        old_sequence, new_sequence = (
                            earlier["request_sequence"],
                            later["request_sequence"],
                        )
                        ordered_contributions.append(
                            dict(
                                **label,
                                block=earlier["block"],
                                template_id=earlier["template_id"],
                                before_request_sequence=old_sequence,
                                after_request_sequence=new_sequence,
                                order_sequence=min(old_sequence, new_sequence),
                                contribution=float(value),
                            )
                        )
                    ordered_contributions.sort(key=lambda r: r["order_sequence"])
                    scene_rows.extend(ordered_contributions)
                    ordered_values = np.array([r["contribution"] for r in ordered_contributions])
                    midpoint = len(ordered_values) // 2
                    diagnostics.append(
                        dict(
                            **label,
                            first_half_mean=float(ordered_values[:midpoint].mean()),
                            second_half_mean=float(ordered_values[midpoint:].mean()),
                            contribution_sd=float(ordered_values.std(ddof=1)),
                            inference="descriptive_slot_order_diagnostic_not_a_stationarity_test",
                        )
                    )
                    control_change = (
                        finite_distances[alias, after, "artist_free", painter, family]
                        - finite_distances[alias, before, "artist_free", painter, family]
                    )
                    secondary.append(
                        dict(
                            **label,
                            endpoint="control_adjusted_transition",
                            estimate=float(inferred["estimate"] - control_change),
                            inference="descriptive_secondary_no_confidence_interval",
                        )
                    )
                secondary.append(
                    dict(
                        alias=alias,
                        painter_id=painter,
                        family=family,
                        before="by_name",
                        after="style_aspects",
                        endpoint="overall_transition",
                        estimate=float(
                            finite_distances[alias, "style_aspects", painter, painter, family]
                            - finite_distances[alias, "by_name", painter, painter, family]
                        ),
                        inference="descriptive_secondary_no_confidence_interval",
                    )
                )
    adjusted = randomization.holm([row["raw_p"] for row in primary])
    for row, pvalue in zip(primary, adjusted):
        row["holm_p"] = float(pvalue)
        row["reject_holm"] = bool(pvalue <= alpha)
    return dict(
        distances=distances,
        coordinates=coordinates,
        absolute=absolute,
        primary=primary,
        secondary=secondary,
        scene_contributions=scene_rows,
        time_diagnostics=diagnostics,
        inference=dict(
            method="paired_randomization",
            alpha=alpha,
            multiplicity="Holm",
            family_size=48,
            endpoint_count=48,
            slot_pair_count=16 * repetitions,
            permutation_seed=permutation_seed,
            permutation_draws=permutation_draws,
            confidence_intervals=False,
            null_scope="sharp no-method-effect null conditional on the third method's "
            "slots and all observed outcomes; no interference across requests",
            reference_scope="fixed exposed finite painting reference",
            generalization="no population, latent-seed pairing, or independent-block claim",
        ),
    )


def build_result(root: Path, run_id: str) -> dict:
    """Recompute the complete numeric result without publishing or accessing image bytes."""
    directory, freeze, requests, outputs, sources = measurement._source(root, run_id)
    receipt = read_json(directory / "measurement_receipt.json")
    verify_bindings(root, receipt["inputs"])
    rows = read_jsonl(directory / "measured_features.jsonl")
    journal = generation._Journal(directory / "measurement_events.jsonl")
    expected_start = dict(
        kind="stage_start",
        run_id=run_id,
        inputs=sources,
        short_side=512,
        feature_names=list(features.NAMES),
    )
    if (
        not journal.rows
        or any(journal.rows[0].get(k) != v for k, v in expected_start.items())
        or receipt["inputs"] != sources
        or len(journal.rows) != len(rows) + 1
        or any(
            event.get("kind") != "terminal" or event.get("row") != row
            for event, row in zip(journal.rows[1:], rows)
        )
    ):
        raise ValueError("terminal measured features differ from their bound journal")
    if (
        receipt["run_id"] != run_id
        or receipt["terminal"] is not True
        or receipt["feature_names"] != list(features.NAMES)
        or receipt["short_side"] != 512
        or receipt["feature_file_sha256"] != hash_file(directory / "measured_features.jsonl")
        or receipt["ledger_sha256"] != hash_file(directory / "measurement_events.jsonl")
        or receipt["freeze_sha256"] != hash_file(directory / "generation_freeze.json")
        or receipt["generation_receipt_sha256"] != hash_file(directory / "generation_receipt.json")
        or len(rows) != receipt["expected_records"]
        or len(rows) != receipt["terminal_records"]
        or len(rows) != len(requests)
        or receipt["statuses"] != dict(Counter(r["status"] for r in rows))
    ):
        raise ValueError("terminal feature evidence or accounting changed")
    for row, request, output in zip(rows, requests, outputs):
        measurement._validate_row(row, request, output, run_id)
    complete = all(row["status"] == "measured" for row in rows)
    if receipt["complete_measured_grid"] != complete:
        raise ValueError("measurement completeness differs from its receipt")
    availability = []
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            for condition in (*PAINTER_IDS, "artist_free"):
                selected = [
                    r
                    for r in rows
                    if (r["alias"], r["method_id"], r["condition"]) == (alias, method, condition)
                ]
                availability.append(
                    dict(
                        alias=alias,
                        method_id=method,
                        condition=condition,
                        expected=16 * freeze["config"]["repetitions"],
                        statuses=dict(Counter(r["status"] for r in selected)),
                    )
                )
    config = freeze["config"]
    template_availability = []
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            for condition in CONDITIONS:
                for template in TEMPLATE_IDS:
                    selected = [
                        r
                        for r in rows
                        if (r["alias"], r["method_id"], r["condition"], r["template_id"])
                        == (alias, method, condition, template)
                    ]
                    template_availability.append(
                        dict(
                            alias=alias,
                            method_id=method,
                            condition=condition,
                            template_id=template,
                            expected=config["repetitions"],
                            statuses=dict(Counter(r["status"] for r in selected)),
                        )
                    )
    result = dict(
        schema_version="painter-prompt-analysis/1.0",
        run_id=run_id,
        source_method_id=freeze["source_method_id"],
        repetitions=config["repetitions"],
        calibration_id=config["calibration_id"],
        template_availability=template_availability,
        status="complete" if complete else "unavailable_incomplete_grid",
        availability=availability,
        aliases=list(generation.ALIASES),
        methods=list(METHOD_IDS),
        painters=list(PAINTER_IDS),
        families={k: list(v) for k, v in features.FAMILY_NAMES.items()},
        estimand="prospective prompt effects conditional on the exposed finite painting reference",
        model_identity="requested OAuth aliases; no attested underlying model snapshot",
        primary_interpretation="conditional sharp-null slot randomization; "
        "Holm-adjusted p-values for 48 finite-distance contrasts; no CIs",
    )
    paths = [
        MANIFESTS / run_id / name
        for name in (
            "generation_freeze.json",
            "generation_receipt.json",
            "outputs.jsonl",
            "requests.jsonl",
            "measurement_receipt.json",
            "measured_features.jsonl",
            "measurement_events.jsonl",
        )
    ]
    paths.append(MANIFESTS / config["calibration_id"] / "decision.json")
    if complete:
        real, _, _, scaler, _, source = load_source(root, freeze["source_method_id"])
        if source["inputs"] != freeze["reference_inputs"]:
            raise ValueError("finite reference inputs differ from the prospective freeze")
        result["reference_counts"] = {p: len(x) for p, x in real.items()}
        result["scaler_development_counts"] = source["scaler_development_counts"]
        if config["primary_estimator"] != "paired_randomization":
            raise ValueError("prompt analysis requires the frozen slot-randomization design")
        result.update(
            compute(
                real,
                rows,
                scaler,
                config["repetitions"],
                config["simultaneous_alpha"],
                permutation_seed=config["permutation_seed"],
                permutation_draws=config["permutation_draws"],
            )
        )
        measured_reference_paths = [Path(r["path"]) for r in source["inputs"]]
        paths.extend(measured_reference_paths)
        reference_file = next(
            p for p in measured_reference_paths if p.name == "confirmation_features.jsonl"
        )
        reference_rows = [r for r in read_jsonl(root / reference_file) if r["status"] == "measured"]
        result["copy_diagnostics"] = empirical.copy_diagnostics(reference_rows, rows)
        result["copy_diagnostics"]["scope"] = "649 exposed confirmation references only"
    result["service_diagnostics"] = {
        f"{alias}/{method}": empirical.service_diagnostics(
            [r for r in outputs if r["alias"] == alias and r["method_id"] == method]
        )
        for alias in generation.ALIASES
        for method in METHOD_IDS
    }
    result["inputs"] = bindings(root, paths)
    result["completed_at_utc"] = utc_now().isoformat()
    return result


def analyze(root: Path, run_id: str) -> dict:
    """Create the terminal analysis once; use reproduction to check an existing result."""
    target = root / MANIFESTS / run_id / "analysis.json"
    if target.exists():
        raise FileExistsError("analysis is terminal; use its retained result")
    result = build_result(root, run_id)
    publish(target, result)
    return result
