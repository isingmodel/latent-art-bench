from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from PIL import Image, ImageDraw

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.qualification import qualification_gate
from latent_art_bench.io import utc_now, write_json
from latent_art_bench.schemas import AnalysisResult, GenerationCallRecord, QualificationCard


def write_generation_contact_sheet(
    calls: Iterable[GenerationCallRecord], root: Path, output_path: Path
) -> Path:
    succeeded = [call for call in calls if call.status == "succeeded" and call.output_path]
    if not succeeded:
        raise ValueError("a generation contact sheet requires at least one successful call")
    tile_width, image_height, label_height = 420, 336, 44
    prompt_ids = list(dict.fromkeys(call.prompt_id for call in succeeded))
    models = list(dict.fromkeys(call.model for call in succeeded))
    by_cell = {(call.prompt_id, call.model): call for call in succeeded}
    sheet = Image.new(
        "RGB",
        (tile_width * len(models), (image_height + label_height) * len(prompt_ids)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for row_index, prompt_id in enumerate(prompt_ids):
        for column_index, model in enumerate(models):
            call = by_cell.get((prompt_id, model))
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
                f"{prompt_id} | {model}",
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
) -> tuple:
    cards = list(cards)
    calls = list(generation_calls)
    results = list(analysis_results)
    gate_allowed, gate_decisions = qualification_gate(
        config.measurements.required, cards, config.measurement_identities()
    )
    call_counts: Dict[str, Counter] = defaultdict(Counter)
    bypass_count = 0
    for call in calls:
        call_counts[call.model][call.status] += 1
        bypass_count += int(call.qualification_bypass)

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
            "counts": {model: dict(counts) for model, counts in call_counts.items()},
            "qualification_bypass_calls": bypass_count,
        },
        "analysis_result_count": len(results),
    }

    lines: List[str] = [
        "# pilot_0 report",
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
        if card and card.reasons:
            lines.extend(["", f"`{measurement}` evidence:"])
            lines.extend(f"- {reason}" for reason in card.reasons)
    lines.extend(
        [
            "",
            f"Scientific-generation gate: `{'open' if gate_allowed else 'closed'}`.",
            "",
            "## Generation accounting",
            "",
        ]
    )
    if not calls:
        lines.append("No generation-call manifest was supplied.")
    else:
        for model in config.generation.models:
            counts = call_counts.get(model, Counter())
            rendered = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
            lines.append(f"- `{model}`: {rendered or 'no calls'}")
        lines.append(f"- Calls using the explicit unqualified test bypass: {bypass_count}")
    lines.extend(["", "## Scientific pilot analysis", ""])
    if not results:
        lines.append(
            "No target-gap or specificity result was computed because the qualification gate "
            "is closed. The API-test images are excluded from scientific analysis."
        )
    else:
        lines.append(
            "| Cell | Model | Feature | Calibrated target gap (interval) | "
            "Specificity margin (interval) |"
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
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "Qualification is open; a scientific pilot analysis may proceed."
                if gate_allowed
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
    decision = (
        "# pilot_0 decision\n\n"
        + (
            "Decision: **pending**. Qualification is open, but a pilot analysis and review are "
            "still required.\n"
            if gate_open
            else "Decision: **stop before scientific generation**. The real-only gate resolved "
            "as `chromatic=fail` and `learned_formal=fail`. Test-only API calls made with an "
            "explicit bypass do not change this decision.\n\n"
            "Next action: redesign the learned evaluator provenance and the chromatic "
            "compression-stability contract before acquiring more benchmark generations.\n"
        )
    )
    decision_path.write_text(decision, encoding="utf-8")
    return [report_path, summary_path, config_path, decision_path]
