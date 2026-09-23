"""Assemble all prespecified reports from externally bound post-terminal features.

Loading an artifact does not authenticate encoder execution. Extraction receipts
and replay remain required before a real study can claim measured observations.
This module neither acquires data nor changes any already completed analysis.
"""

from __future__ import annotations

import numpy as np

from .analysis import analyze_primary, evaluate_transport
from .feature_census import encoder_contract, load_embedding_census
from .protocol import canonical_sha
from .reference_panels import PANEL_IDS
from .reference_panels import load_prepared as load_reference_panels
from .secondary_embeddings import analyze_secondary
from .secondary_features import analyze_realized_features
from .transport_artifact import ROOT
from .transport_artifact import load_prepared as load_transport


def _analyze_arrays(learned, reference_panels, parameters, features31):
    """Pure constructed-test seam; callers must bind provenance before using it."""
    if set(learned) != {"clip", "csd"}:
        raise ValueError("both fixed encoders are required; no representation selection")
    csd = learned["csd"]
    times = csd["window_times"]
    simulation = csd["simulation_only"]
    for value in [*learned.values(), features31]:
        if (value["simulation_only"] is not simulation
                or canonical_sha(value["window_times"]) != canonical_sha(times)
                or not np.array_equal(value["observed"], csd["observed"])):
            raise ValueError("representations must share the same bound census and actual times")
    if type(simulation) is not bool:
        raise ValueError("explicit simulation identity is required")
    for encoder in ("clip", "csd"):
        if set(reference_panels[encoder]) != set(PANEL_IDS):
            raise ValueError("all four predeclared reference panels must remain present")
        if parameters[encoder]["encoder"] != encoder:
            raise ValueError("transport parameters belong to a different encoder")
        if not np.array_equal(
            reference_panels[encoder]["primary_original"]["reference_means"],
            parameters[encoder]["raw_reference_means"],
        ):
            raise ValueError("transport and primary reference means differ")
    primary = analyze_primary(
        csd["generated"], reference_panels["csd"]["primary_original"]["reference_means"],
        times, observed=csd["observed"],
    )
    primary["reference_panel"] = "primary_original"
    secondary, recognition = {}, {}
    for encoder in ("clip", "csd"):
        value = learned[encoder]
        for panel in PANEL_IDS:
            if (encoder, panel) == ("csd", "primary_original"):
                continue
            secondary[f"{encoder}/{panel}"] = analyze_secondary(
                value["generated"], reference_panels[encoder][panel]["reference_means"], times,
                representation=encoder, reference_panel=panel, observed=value["observed"],
            )
        recognition[encoder] = evaluate_transport(
            value["generated"][..., 4:8, :], parameters[encoder], times,
            observed=value["observed"][..., 4:8],
        )
    return dict(
        schema="painter-family-controls-combined-analysis/1.0",
        status=("simulation_only_not_scientific_evidence" if simulation
                else "bound_feature_array_analysis_execution_provenance_still_required"),
        simulation_only=simulation, primary=primary, secondary_embeddings=secondary,
        frozen_transport=recognition,
        secondary_features=analyze_realized_features(
            features31["generated"], times, observed=features31["observed"],
        ),
        scope={
            "primary": "CSD original primary references; fixed12 endpoints only",
            "secondary": ("seven other encoder/reference panels,31-feature energies,"
                          "old-to-new rules"),
            "representation_selection": False,
            "human_or_perceptual_ground_truth": False,
            "scientific_review_score": None,
        },
    )


def analyze_census(census, learned_specs, feature31_spec, *, reference_path,
                   expected_reference_sha256, transport_path, expected_transport_sha256,
                   allow_simulation=False, root=ROOT):
    """Require externally bound feature artifacts for the complete reporting grid.

    Each learned spec has manifest_path, embeddings_path and their expected
    SHA-256s. The raw31 spec has manifest_path, raw_npz_path and their expected
    SHA-256s. Digests must come from independent extraction receipts, not be
    inferred from whichever files happen to be present by this function.
    """
    from .measurement31 import load_feature_census

    if census.evidence["simulation_only"] and allow_simulation is not True:
        raise ValueError("simulation analysis requires an explicit fixture-only opt-in")
    if set(learned_specs) != {"clip", "csd"}:
        raise ValueError("supply exactly both fixed learned representations")
    refs = load_reference_panels(
        reference_path, expected_sha256=expected_reference_sha256, root=root
    )
    transport = load_transport(transport_path, expected_sha256=expected_transport_sha256, root=root)
    learned = {}
    for encoder, spec in learned_specs.items():
        contract = encoder_contract(encoder, root=root)
        retained = refs["encoder_contracts"][encoder]
        if (canonical_sha(contract["model"]) != canonical_sha(retained["model"])
                or canonical_sha(contract["processor"]) != canonical_sha(retained["processor"])):
            raise ValueError("reference and query encoder/preprocessing contracts differ")
        learned[encoder] = load_embedding_census(census, **spec, root=root)
        if learned[encoder]["encoder"] != encoder:
            raise ValueError("feature artifact was supplied under the wrong encoder key")
    feature31 = load_feature_census(census, **feature31_spec, root=root)
    report = _analyze_arrays(learned, refs["panels"], transport["parameters"], feature31)
    report["provenance"] = dict(
        collector_record_hashes=census.evidence["record_hashes"],
        reference_candidate_sha256=expected_reference_sha256,
        transport_candidate_sha256=expected_transport_sha256,
        learned={name: dict(manifest_sha256=value["manifest_sha256"],
                            embeddings_sha256=value["embeddings_sha256"])
                 for name, value in learned.items()},
        feature31=feature31["provenance"],
        pixel_and_row_identity_verified=True,
        actual_extractor_execution_authenticated=False,
        note="Binding verifies supplied artifacts; actual extractor execution/replay is separate.",
    )
    return report
