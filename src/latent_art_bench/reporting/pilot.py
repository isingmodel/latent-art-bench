from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np
from PIL import Image, ImageDraw

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.qualification import qualification_gate
from latent_art_bench.io import hash_file, stable_hash, utc_now, write_json, write_jsonl
from latent_art_bench.schemas import (
    AnalysisCell,
    AnalysisResult,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    QualificationCard,
    RunRecord,
)


def build_artist_free_control_diagnostics(
    config: PilotConfig,
    prompts: Sequence[PromptRecord],
    generated_features: Mapping[str, Sequence[FeatureRow]],
    generated_manifest_sha256: Mapping[str, str],
) -> Dict[str, Any]:
    """Pair every artist prompt with its frozen same-content artist-free control."""

    controls = {prompt.content_id: prompt for prompt in prompts if prompt.artist_free_control}
    if len(controls) != len({prompt.content_id for prompt in prompts}):
        raise ValueError("every frozen content prompt requires exactly one artist-free control")
    target_prompts = [prompt for prompt in prompts if not prompt.artist_free_control]
    expected_targets = len(config.corpus.selected_artists) * len(controls)
    if len(target_prompts) != expected_targets:
        raise ValueError("artist-free diagnostics require the complete frozen target-prompt grid")

    records: List[Dict[str, Any]] = []
    for measurement in config.measurements.required:
        rows = list(generated_features[measurement])
        lookup = {
            (row.prompt_id, row.model, row.repetition): row
            for row in rows
            if row.origin == "generated" and row.status == "ok"
        }
        if len(lookup) != len(rows):
            raise ValueError(
                f"{measurement} artist-free diagnostics found duplicate or invalid rows"
            )
        for prompt in target_prompts:
            control = controls[prompt.content_id]
            for model in config.generation.models:
                for repetition in range(config.generation.repetitions):
                    target_key = (prompt.prompt_id, model, repetition)
                    control_key = (control.prompt_id, model, repetition)
                    if target_key not in lookup or control_key not in lookup:
                        raise ValueError(
                            f"{measurement} artist-free diagnostics lack a matched pair"
                        )
                    target = lookup[target_key]
                    control_row = lookup[control_key]
                    target_vector = np.asarray(target.vector, dtype=np.float64)
                    control_vector = np.asarray(control_row.vector, dtype=np.float64)
                    if (
                        target_vector.ndim != 1
                        or target_vector.shape != control_vector.shape
                        or not np.isfinite(target_vector).all()
                        or not np.isfinite(control_vector).all()
                    ):
                        raise ValueError("artist-free diagnostic vectors are incompatible")
                    records.append(
                        {
                            "measurement": measurement,
                            "model_requested": model,
                            "target_artist_id": prompt.target_artist_id,
                            "content_id": prompt.content_id,
                            "repetition": repetition,
                            "target_prompt_id": prompt.prompt_id,
                            "control_prompt_id": control.prompt_id,
                            "target_feature_id": target.feature_id,
                            "control_feature_id": control_row.feature_id,
                            "vector_dimension": int(target_vector.size),
                            "raw_feature_euclidean_distance": float(
                                np.linalg.norm(target_vector - control_vector)
                            ),
                        }
                    )
    expected_record_count = (
        len(config.measurements.required)
        * len(target_prompts)
        * len(config.generation.models)
        * config.generation.repetitions
    )
    if len(records) != expected_record_count:
        raise ValueError("artist-free diagnostics are a selective subset")
    grouped: Dict[tuple[str, str], List[float]] = defaultdict(list)
    for row in records:
        grouped[(row["measurement"], row["model_requested"])].append(
            row["raw_feature_euclidean_distance"]
        )
    summaries = [
        {
            "measurement": measurement,
            "model_requested": model,
            "pair_count": len(values),
            "median_raw_feature_euclidean_distance": float(median(values)),
            "minimum_raw_feature_euclidean_distance": float(min(values)),
            "maximum_raw_feature_euclidean_distance": float(max(values)),
        }
        for (measurement, model), values in sorted(grouped.items())
    ]
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "scope": "paired_descriptive_api_integration_test_only",
        "scientific_inference_permitted": False,
        "distance": "raw_feature_euclidean_distance_within_measurement_only",
        "generated_manifest_sha256": dict(generated_manifest_sha256),
        "pair_count": len(records),
        "summaries": summaries,
        "records": records,
    }
    payload["result_sha256"] = stable_hash(payload)
    return payload


def _sanitized_value(value: Any, root: Path) -> Any:
    if isinstance(value, dict):
        sanitized: Dict[str, Any] = {}
        for key, item in value.items():
            sanitized_key = _sanitized_value(str(key), root)
            if sanitized_key in sanitized:
                raise ValueError(
                    "sanitizing dictionary keys produced a duplicate key: "
                    f"{sanitized_key!r}"
                )
            sanitized[sanitized_key] = _sanitized_value(item, root)
        return sanitized
    if isinstance(value, list):
        return [_sanitized_value(item, root) for item in value]
    if isinstance(value, str):
        prefix = str(root.resolve()) + "/"
        if value.startswith(prefix):
            return value.removeprefix(prefix)
        path = Path(value)
        if path.is_absolute():
            return f"<external-path>/{path.name}"
        return value
    return value


def write_pilot_evidence_snapshots(
    output_dir: Path,
    root: Path,
    generation_calls: Sequence[GenerationCallRecord],
    generation_runs: Sequence[tuple[RunRecord, str]],
    analysis_cells: Sequence[AnalysisCell],
    analysis_results: Sequence[AnalysisResult],
) -> tuple[List[Path], Dict[str, str]]:
    """Publish small, reviewable evidence without copying media or feature vectors."""

    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    call_path = evidence_dir / "generation_calls.attested.jsonl"
    run_path = evidence_dir / "generation_runs.sanitized.jsonl"
    cell_path = evidence_dir / "analysis_cells.provenance.jsonl"
    result_path = evidence_dir / "analysis_results.jsonl"

    write_jsonl(call_path, generation_calls)
    sanitized_runs = []
    for run, source_sha256 in generation_runs:
        payload = _sanitized_value(run.model_dump(mode="json"), root)
        payload["source_run_record_sha256"] = source_sha256
        sanitized_runs.append(payload)
    write_jsonl(run_path, sanitized_runs)

    cell_rows = []
    for cell in analysis_cells:
        matrices = {
            "target_train": cell.target_train_vectors,
            "target_held_out": cell.target_held_out_vectors,
            "generated": cell.generated_vectors,
        }
        dimensions = {
            len(vector)
            for values in [*matrices.values(), *cell.neighbor_vectors.values()]
            for vector in values
        }
        cell_rows.append(
            {
                "schema_version": "1.0",
                "analysis_cell_sha256": stable_hash(cell.model_dump(mode="json")),
                "cell_id": cell.cell_id,
                "measurement": cell.measurement,
                "model": cell.model,
                "target_artist_id": cell.target_artist_id,
                "feature_name": cell.feature_name,
                "feature_version": cell.feature_version,
                "feature_config_hash": cell.feature_config_hash,
                "qualification_contract_hash": cell.qualification_contract_hash,
                "qualification_evidence_artifact_sha256": (
                    cell.qualification_evidence_artifact_sha256
                ),
                "real_feature_manifest_sha256": cell.real_feature_manifest_sha256,
                "generated_feature_manifest_sha256": (
                    cell.generated_feature_manifest_sha256
                ),
                "generation_manifest_sha256": cell.generation_manifest_sha256,
                "generation_attestation_sha256": cell.generation_attestation_sha256,
                "reference_transform_state_sha256": (
                    cell.reference_transform_state_sha256
                ),
                "qualified_reference_transform_state_sha256": (
                    cell.qualified_reference_transform_state_sha256
                ),
                "engineering_scope": cell.engineering_scope,
                "preparation_qualification_bypass": (
                    cell.preparation_qualification_bypass
                ),
                "vector_dimension": next(iter(dimensions)) if len(dimensions) == 1 else None,
                "target_train_count": len(cell.target_train_vectors),
                "target_held_out_count": len(cell.target_held_out_vectors),
                "generated_count": len(cell.generated_vectors),
                "neighbor_counts": {
                    name: len(values)
                    for name, values in sorted(cell.neighbor_vectors.items())
                },
            }
        )
    write_jsonl(cell_path, cell_rows)
    write_jsonl(result_path, analysis_results)
    paths = [call_path, run_path, cell_path, result_path]
    return paths, {
        str(path.relative_to(output_dir)): hash_file(path) for path in paths
    }


def write_pilot_artifact_index(
    output_dir: Path,
    root: Path,
    artifact_paths: Iterable[Path],
    run_records: Sequence[tuple[RunRecord, str]],
) -> List[Path]:
    """Publish a sanitized run ledger and hashes for retained and ignored artifacts."""

    root = root.resolve()
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    run_manifest_path = evidence_dir / "run_manifest.sanitized.jsonl"
    artifact_index_path = evidence_dir / "artifact_index.json"
    evidence_anchor_path = output_dir / "EVIDENCE.md"

    sanitized_runs = []
    for run, source_sha256 in sorted(run_records, key=lambda item: item[0].run_id):
        payload = _sanitized_value(run.model_dump(mode="json"), root)
        payload["source_run_record_sha256"] = source_sha256
        sanitized_runs.append(payload)
    write_jsonl(run_manifest_path, sanitized_runs)

    paths = {Path(path).resolve() for path in artifact_paths}
    paths.add(run_manifest_path.resolve())
    entries = []
    for path in sorted(paths, key=str):
        if not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
            display_path = str(relative)
            top_level = relative.parts[0] if relative.parts else ""
            retention = (
                "ignored_local"
                if top_level in {"artifacts", "data", "outputs", "tmp"}
                else "tracked_evidence"
            )
        except ValueError:
            display_path = str(path)
            retention = "external_local"
        row_count = None
        if path.suffix in {".jsonl", ".csv"}:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                row_count = sum(1 for line in handle if line.strip())
        entries.append(
            {
                "path": display_path,
                "sha256": hash_file(path),
                "byte_count": path.stat().st_size,
                "row_count": row_count,
                "retention": retention,
            }
        )
    payload = {
        "schema_version": "1.0",
        "pilot_id": "pilot_1",
        "self_hash_excluded": True,
        "entry_count": len(entries),
        "run_record_count": len(sanitized_runs),
        "entries": entries,
    }
    write_json(artifact_index_path, payload)
    evidence_anchor_path.write_text(
        "# pilot_1 evidence anchor\n\n"
        "This file binds the reviewable artifact ledger without creating a self-hash "
        "cycle.\n\n"
        f"- `evidence/artifact_index.json`: `{hash_file(artifact_index_path)}`\n"
        f"- `evidence/run_manifest.sanitized.jsonl`: `{hash_file(run_manifest_path)}`\n",
        encoding="utf-8",
    )
    return [run_manifest_path, artifact_index_path, evidence_anchor_path]


def _parse_requested_size(value: str) -> Optional[tuple[int, int]]:
    parts = value.lower().split("x")
    if len(parts) != 2:
        return None
    try:
        width, height = (int(part) for part in parts)
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height


def write_generation_contact_sheet(
    calls: Iterable[GenerationCallRecord], root: Path, output_path: Path
) -> Path:
    succeeded = [call for call in calls if call.status == "succeeded" and call.output_path]
    if not succeeded:
        raise ValueError("a generation contact sheet requires at least one successful call")
    tile_width, image_height, label_height = 420, 336, 44
    prompt_ids = list(dict.fromkeys(call.prompt_id for call in succeeded))
    columns = list(dict.fromkeys((call.model, call.repetition) for call in succeeded))
    by_cell = {}
    for call in succeeded:
        key = (call.prompt_id, call.model, call.repetition)
        if key in by_cell:
            raise ValueError(f"multiple successful calls exist for generation cell {key}")
        by_cell[key] = call
    sheet = Image.new(
        "RGB",
        (tile_width * len(columns), (image_height + label_height) * len(prompt_ids)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for row_index, prompt_id in enumerate(prompt_ids):
        for column_index, (model, repetition) in enumerate(columns):
            call = by_cell.get((prompt_id, model, repetition))
            if call is None or not call.output_path:
                continue
            path = Path(call.output_path)
            if not path.is_absolute():
                path = root / path
            with Image.open(path) as source:
                tile = source.convert("RGB")
                tile.thumbnail((tile_width, image_height), Image.Resampling.LANCZOS)
            x = column_index * tile_width + (tile_width - tile.width) // 2
            y_base = row_index * (image_height + label_height)
            y = y_base + (image_height - tile.height) // 2
            sheet.paste(tile, (x, y))
            draw.text(
                (column_index * tile_width + 8, y_base + image_height + 5),
                f"{prompt_id} | {model} | repetition {repetition}",
                fill="black",
            )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="JPEG", quality=92, optimize=False)
    return output_path


def build_pilot_report(
    config: PilotConfig,
    cards: Iterable[QualificationCard],
    generation_calls: Iterable[GenerationCallRecord] = (),
    analysis_results: Iterable[AnalysisResult] = (),
    prompts: Iterable[PromptRecord] = (),
    qualification_identities: Optional[Dict[str, tuple]] = None,
    evidence_snapshot_hashes: Optional[Mapping[str, str]] = None,
    artist_free_control_diagnostics: Optional[Mapping[str, Any]] = None,
    generation_attestation: Optional[Mapping[str, Any]] = None,
) -> tuple:
    cards = list(cards)
    calls = list(generation_calls)
    results = list(analysis_results)
    prompts = list(prompts)
    prompt_ids = [prompt.prompt_id for prompt in prompts]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ValueError("prompt identifiers must be unique in the report input")
    gate_allowed, gate_decisions = qualification_gate(
        config.measurements.required,
        cards,
        qualification_identities or config.measurement_identities(),
    )
    call_counts: Dict[str, Counter] = defaultdict(Counter)
    bypass_count = 0
    for call in calls:
        call_counts[call.model][call.status] += 1
        bypass_count += int(call.qualification_bypass)
    expected_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }
    attempted_cells = {
        (call.prompt_id, call.model, call.repetition) for call in calls
    }
    resolved_engineering_cells = {
        (call.prompt_id, call.model, call.repetition)
        for call in calls
        if call.status == "succeeded"
    }
    resolved_non_bypass_cells = {
        (call.prompt_id, call.model, call.repetition)
        for call in calls
        if call.status == "succeeded" and not call.qualification_bypass
    }
    non_success_cells = {
        (call.prompt_id, call.model, call.repetition)
        for call in calls
        if call.status in {"failed", "refused"}
    }
    retry_resolved_cells = non_success_cells & resolved_engineering_cells
    unresolved_cells = expected_cells - resolved_engineering_cells
    unexpected_cells = attempted_cells - expected_cells if prompts else set()

    successful_calls = [call for call in calls if call.status == "succeeded"]
    dimensioned_calls = [
        call
        for call in successful_calls
        if call.actual_width is not None and call.actual_height is not None
    ]
    comparable_dimension_calls = [
        call
        for call in dimensioned_calls
        if _parse_requested_size(call.requested_size) is not None
    ]
    exact_requested_size_matches = sum(
        _parse_requested_size(call.requested_size)
        == (call.actual_width, call.actual_height)
        for call in comparable_dimension_calls
    )
    requested_size_counts = Counter(call.requested_size for call in successful_calls)
    returned_size_counts = Counter(
        f"{call.actual_width}x{call.actual_height}" for call in dimensioned_calls
    )

    retry_attempts_by_cell: Dict[tuple, List[GenerationCallRecord]] = defaultdict(list)
    retry_successes_by_cell: Dict[tuple, List[GenerationCallRecord]] = defaultdict(list)
    for call in calls:
        cell = (call.prompt_id, call.model, call.repetition)
        if call.status in {"failed", "refused"}:
            retry_attempts_by_cell[cell].append(call)
        elif call.status == "succeeded":
            retry_successes_by_cell[cell].append(call)
    identity_verified_retry_cells = set()
    native_identity_retry_cells = set()
    legacy_attested_retry_cells = set()
    for cell in retry_resolved_cells:
        matching_pairs = [
            (attempt, success)
            for attempt in retry_attempts_by_cell[cell]
            for success in retry_successes_by_cell[cell]
            if attempt.request_identity_sha256
            and attempt.request_identity_sha256 == success.request_identity_sha256
        ]
        if not matching_pairs:
            continue
        identity_verified_retry_cells.add(cell)
        if any(
            "legacy_run_attestation"
            in {
                attempt.request_identity_provenance,
                success.request_identity_provenance,
            }
            for attempt, success in matching_pairs
        ):
            legacy_attested_retry_cells.add(cell)
        else:
            native_identity_retry_cells.add(cell)
    identity_unverified_retry_cells = retry_resolved_cells - identity_verified_retry_cells

    sample_sizes = sorted({result.subsample_size for result in results})
    engineering_bypass = bool(results) and all(
        result.preparation_qualification_bypass for result in results
    )

    summary = {
        "schema_version": "1.0",
        "pilot_id": config.pilot_id,
        "generated_at": utc_now().isoformat(),
        "purpose": config.purpose,
        "scientific_claims_enabled": config.generation.scientific_claims_enabled,
        "qualification_gate": {
            "allowed": gate_allowed,
            "measurements": gate_decisions,
        },
        "qualification_cards": [card.model_dump(mode="json") for card in cards],
        "generation": {
            "models": config.generation.models,
            "model_field_semantics": "requested_label_not_backend_execution_proof",
            "executed_model_identity": "unverified",
            "transport": "local_openai_oauth_to_chatgpt_codex_backend",
            "public_openai_images_api": False,
            "attested_scientific_eligibility": (
                (generation_attestation or {}).get("scientific_eligibility")
            ),
            "counts": {model: dict(counts) for model, counts in call_counts.items()},
            "qualification_bypass_calls": bypass_count,
            "attempt_records": len(calls),
            "expected_frozen_cells": len(expected_cells),
            "attempted_frozen_cells": len(attempted_cells),
            "resolved_engineering_cells": len(resolved_engineering_cells),
            "resolved_non_bypass_cells": len(resolved_non_bypass_cells),
            "unresolved_frozen_cells": len(unresolved_cells),
            "retry_resolved_cells": len(retry_resolved_cells),
            "request_identity_verified_retry_cells": len(
                identity_verified_retry_cells
            ),
            "native_request_identity_retry_cells": len(native_identity_retry_cells),
            "legacy_attested_request_identity_retry_cells": len(
                legacy_attested_retry_cells
            ),
            "request_identity_unverified_retry_cells": len(
                identity_unverified_retry_cells
            ),
            "unexpected_cells": len(unexpected_cells),
            "returned_dimensions": {
                "successful_outputs": len(successful_calls),
                "successful_outputs_with_dimensions": len(dimensioned_calls),
                "comparable_requested_and_returned_sizes": len(
                    comparable_dimension_calls
                ),
                "exact_requested_size_matches": exact_requested_size_matches,
                "requested_size_counts": dict(sorted(requested_size_counts.items())),
                "returned_size_counts": dict(sorted(returned_size_counts.items())),
            },
        },
        "analysis_intervals": {
            "kind": "real_reference_subsampling_quantiles",
            "inferential_confidence_intervals": False,
            "generated_samples_resampled": False,
            "generated_sample_sizes": sample_sizes,
            "omitted_uncertainty": [
                "generator_sampling",
                "prompt_cluster",
            ],
        },
        "analysis_result_count": len(results),
        "artist_free_control_diagnostics": {
            "pair_count": int(
                (artist_free_control_diagnostics or {}).get("pair_count", 0)
            ),
            "scientific_inference_permitted": False,
            "result_sha256": (artist_free_control_diagnostics or {}).get(
                "result_sha256"
            ),
        },
        "engineering_traversal": {
            "completed": bool(results),
            "scope": "api_integration_test_only",
            "qualification_bypass_explicit": engineering_bypass,
            "scientific_gate_open": gate_allowed,
        },
        "committed_evidence_snapshots": dict(evidence_snapshot_hashes or {}),
    }

    lines: List[str] = [
        f"# {config.pilot_id} report",
        "",
        "This artifact is an API-integration development report, not a benchmark scorecard.",
        "The configuration disables scientific claims and restricts generation to `gpt-image-1` "
        "and `gpt-image-2`.",
        "",
        "## Frozen design",
        "",
        f"Common corpus view: `{config.corpus.common_genre}`.",
        "",
        "| Target artist | Frozen neighbor |",
        "|---|---|",
    ]
    artists = {artist.artist_id: artist for artist in config.corpus.selected_artists}
    for artist in config.corpus.selected_artists:
        lines.append(
            f"| {artist.artist_name} | {artists[artist.neighbor_artist_id].artist_name} |"
        )
    lines.extend(
        [
            "",
            "## Qualification",
            "",
            "| Measurement | Status | Real works | Reproduction pairs |",
            "|---|---|---:|---:|",
        ]
    )
    cards_by_measurement = {card.measurement: card for card in cards}
    for measurement in config.measurements.required:
        card = cards_by_measurement.get(measurement)
        lines.append(
            f"| `{measurement}` | `{gate_decisions.get(measurement, 'missing')}` | "
            f"{card.real_work_count if card else 0} | "
            f"{card.reproduction_pair_count if card else 0} |"
        )
    for measurement in config.measurements.required:
        card = cards_by_measurement.get(measurement)
        if card and card.supported_scope:
            lines.extend(["", f"`{measurement}` recorded conditional scope:"])
            lines.extend(f"- {item}" for item in card.supported_scope)
        if card and card.reasons:
            lines.extend(["", f"`{measurement}` evidence:"])
            lines.extend(f"- {reason}" for reason in card.reasons)
    lines.extend(
        [
            "",
            f"Test-only analysis gate: `{'open' if gate_allowed else 'closed'}`.",
            "",
            "## Generation accounting",
            "",
        ]
    )
    if not calls:
        lines.append("No generation-call manifest was supplied.")
    else:
        lines.append(
            "- Model counts below are requested labels. The retained responses do not "
            "prove which backend model executed, so no `gpt-image-1` versus "
            "`gpt-image-2` comparison is permitted."
        )
        lines.append(
            "- Transport: local `openai-oauth` compatibility proxy to the ChatGPT Codex "
            "images backend; this was not the public `api.openai.com` Images API."
        )
        if generation_attestation:
            eligibility = generation_attestation.get("scientific_eligibility", {})
            lines.append(
                "- Attested use: `"
                f"{eligibility.get('permitted_use', 'unverified')}`; requested-dimension "
                "contract: `"
                f"{generation_attestation.get('requested_dimension_contract_status', 'unknown')}`."
            )
        for model in config.generation.models:
            counts = call_counts.get(model, Counter())
            rendered = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
            lines.append(f"- `{model}`: {rendered or 'no calls'}")
        lines.append(f"- Attempt records retained: {len(calls)}")
        if prompts:
            lines.append(
                "- Frozen cells resolved for gated test-only analysis: "
                f"{len(resolved_engineering_cells)}/{len(expected_cells)}"
            )
            lines.append(f"- Frozen cells still unresolved: {len(unresolved_cells)}")
        lines.append(
            "- Cells resolved after a retained refusal or failure record: "
            f"{len(retry_resolved_cells)}"
        )
        if retry_resolved_cells:
            lines.append(
                "- Matching request identity recorded across the failed and succeeding calls: "
                f"{len(identity_verified_retry_cells)}/{len(retry_resolved_cells)} cells"
            )
        if native_identity_retry_cells:
            lines.append(
                "- Matching identities captured natively before request dispatch: "
                f"{len(native_identity_retry_cells)} cells"
            )
        if legacy_attested_retry_cells:
            lines.append(
                "- Matching identities reconstructed from retained legacy run metadata: "
                f"{len(legacy_attested_retry_cells)} cells. This attestation verifies the "
                "retained request contract, but is not a native pre-request identity capture."
            )
        if identity_unverified_retry_cells:
            lines.append(
                "- For "
                f"{len(identity_unverified_retry_cells)} retry-resolved cells, only the prompt "
                "ID, model, and repetition match; the report does not claim that the prompt "
                "text or full request payload was unchanged."
            )
        lines.append(
            "- Returned image dimensions recorded: "
            f"{len(dimensioned_calls)}/{len(successful_calls)} successful outputs"
        )
        lines.append(
            "- Exact requested-size matches: "
            f"{exact_requested_size_matches}/{len(comparable_dimension_calls)} comparable "
            "successful outputs"
        )
        if requested_size_counts:
            rendered_requested_sizes = ", ".join(
                f"{size} ({count})"
                for size, count in sorted(requested_size_counts.items())
            )
            lines.append(f"- Requested dimensions: {rendered_requested_sizes}")
        if dimensioned_calls:
            widths = [call.actual_width for call in dimensioned_calls]
            heights = [call.actual_height for call in dimensioned_calls]
            lines.append(
                "- Returned dimensions: "
                f"{len(returned_size_counts)} distinct sizes; width "
                f"{min(widths)}–{max(widths)} px, height {min(heights)}–{max(heights)} px"
            )
        lines.append(f"- Calls using the explicit unqualified test bypass: {bypass_count}")
        if unexpected_cells:
            lines.append(f"- Unexpected manifest cells: {len(unexpected_cells)}")
    lines.extend(["", "## Test-only distribution diagnostics", ""])
    if not results:
        lines.append(
            "No target-gap or specificity diagnostic was computed. API-test images are never "
            "scientific benchmark evidence."
        )
    else:
        lines.append(
            "| Cell | Requested model label | Feature | Calibrated target gap "
            "(reference-resampling quantiles) | Specificity margin "
            "(reference-resampling quantiles) |"
        )
        lines.append("|---|---|---|---:|---:|")
        for result in results:
            target_interval = ", ".join(
                f"{value:.6g}" for value in result.calibrated_target_gap_interval
            )
            specificity_interval = ", ".join(
                f"{value:.6g}" for value in result.specificity_margin_interval
            )
            lines.append(
                f"| {result.cell_id} | {result.model} | {result.feature_name} | "
                f"{result.calibrated_target_gap:.6g} [{target_interval}] | "
                f"{result.specificity_margin:.6g} [{specificity_interval}] |"
            )
        lines.extend(
            [
                "",
                "A positive specificity margin means the generated distribution is closer to "
                "the requested target than to its nearest configured neighbor, after dividing "
                "by that target-neighbor separation.",
            ]
        )
        if sample_sizes == [4]:
            lines.append(
                "The generated side is fixed at n=4 in every cell and is not resampled."
            )
        else:
            lines.append(
                "The generated side is fixed within each cell and is not resampled; recorded "
                "cell sizes are n="
                f"{', '.join(str(value) for value in sample_sizes)}."
            )
        lines.append(
            "Bracketed ranges are empirical quantiles from subsampling the real-reference "
            "works only. They are not inferential confidence intervals and omit "
            "generator-sampling and prompt-cluster uncertainty."
        )
        intervals_crossing_zero = sum(
            result.specificity_margin_interval[0] <= 0
            <= result.specificity_margin_interval[1]
            for result in results
        )
        lines.append(
            "Specificity reference-resampling ranges include zero in "
            f"{intervals_crossing_zero}/{len(results)} "
            "cells, so point-estimate signs do not support a model or artist ranking."
        )
        if any(
            result.feature_name == "learned_formal" and result.calibrated_target_gap < 0
            for result in results
        ):
            lines.append(
                "Negative learned-formal calibrated gaps mean the generated-target distance "
                "fell below the held-out real-real baseline after normalization. They are not "
                "quality scores or evidence of artist-style fidelity."
            )
    if evidence_snapshot_hashes:
        lines.extend(["", "## Committed evidence snapshots", ""])
        for path, digest in sorted(evidence_snapshot_hashes.items()):
            lines.append(f"- `{path}`: `{digest}`")
    if artist_free_control_diagnostics:
        lines.extend(["", "## Artist-free paired controls", ""])
        lines.append(
            "These complete matched pairs measure how much the requested-artist wording "
            "changed each output relative to the same content prompt without an artist. "
            "Distances are raw within-measurement diagnostics, not fidelity scores or "
            "inferential tests."
        )
        lines.extend(
            [
                "",
                "| Measurement | Requested model label | Pairs | Median raw distance |",
                "|---|---|---:|---:|",
            ]
        )
        for row in artist_free_control_diagnostics.get("summaries", []):
            lines.append(
                f"| `{row['measurement']}` | `{row['model_requested']}` | "
                f"{row['pair_count']} | "
                f"{row['median_raw_feature_euclidean_distance']:.6g} |"
            )
    lines.extend(
        [
            "",
            "The final artifact and run ledgers are content-addressed by `EVIDENCE.md`.",
        ]
    )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "Decision: engineering traversal complete. The real-only qualification gate "
                "is open, but scientific claims remain disabled and these results are API-test "
                "diagnostics only."
                if gate_allowed and results
                else "Qualification is open for test-only diagnostics; analysis is pending."
                if gate_allowed
                else "Decision: scientific gate closed; engineering traversal completed under "
                "an explicit test-only qualification bypass. The resulting diagnostics are "
                "not scientific evidence."
                if results and engineering_bypass
                else "Stop before scientific generation. Redesign the failed measurement "
                "contracts before gathering any additional benchmark outputs."
            ),
            "",
        ]
    )
    return "\n".join(lines), summary


def write_pilot_report(
    output_dir: Path,
    markdown: str,
    summary: Dict[str, object],
    config: PilotConfig,
) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "REPORT.md"
    report_path.write_text(markdown, encoding="utf-8")
    summary_path = output_dir / "summary.json"
    config_path = output_dir / "resolved_config.json"
    decision_path = output_dir / "DECISION.md"
    write_json(summary_path, summary)
    write_json(config_path, config.model_dump(mode="json"))
    gate_open = bool(summary["qualification_gate"]["allowed"])
    traversal = dict(summary.get("engineering_traversal", {}))
    decision = (
        f"# {config.pilot_id} decision\n\n"
        + (
            "Decision: **engineering traversal complete**. The real-only gate is open, but "
            "results remain API-testing diagnostics with scientific claims disabled.\n"
            if gate_open and summary["analysis_result_count"]
            else "Decision: **pending**. Qualification is open for test-only diagnostics, but "
            "analysis and review are still required.\n"
            if gate_open
            else "Decision: **scientific gate closed; engineering traversal complete**. "
            "Generated-feature preparation and analysis used the explicit test-only "
            "qualification bypass. The diagnostics are not scientific evidence.\n"
            if summary["analysis_result_count"]
            and traversal.get("qualification_bypass_explicit") is True
            else "Decision: **stop before scientific generation**. The real-only gate resolved "
            "as closed. Test-only API calls made with an explicit bypass do not change this "
            "decision.\n"
        )
    )
    decision_path.write_text(decision, encoding="utf-8")
    return [report_path, summary_path, config_path, decision_path]
