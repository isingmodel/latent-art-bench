from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.qualification import qualification_gate
from latent_art_bench.io import utc_now, write_json
from latent_art_bench.schemas import AnalysisResult, GenerationCallRecord, QualificationCard


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
        "## Qualification",
        "",
    ]
    for measurement in config.measurements.required:
        lines.append(f"- `{measurement}`: `{gate_decisions.get(measurement, 'missing')}`")
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
    lines.extend(["", "## Pilot analysis", ""])
    if not results:
        lines.append("No qualified target-gap or specificity results are available.")
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
            "A positive specificity margin means the generated distribution is closer to the "
            "requested target than to its nearest configured neighbor, after dividing by that "
            "target-neighbor separation.",
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
            else "Decision: **stop before scientific generation**. One or more real-only "
            "measurement qualifications are missing, pending, or failed. Test-only API calls "
            "made with an explicit bypass do not change this decision.\n"
        )
    )
    decision_path.write_text(decision, encoding="utf-8")
    return [report_path, summary_path, config_path, decision_path]
