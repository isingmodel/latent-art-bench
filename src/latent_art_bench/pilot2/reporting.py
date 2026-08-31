"""JSON, Markdown, and artifact-index APIs for the pilot_2 analysis.

Report language is deliberately limited to operational requested-label effects.
The two labels are never ranked and are never presented as verified executed
backend identities.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Literal, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from latent_art_bench.io import hash_file, stable_hash, write_json
from latent_art_bench.pilot2.analysis import (
    Pilot2AnalysisResult,
    Pilot2ChromaticSecondaryResult,
    Pilot2PrimaryEstimate,
    analysis_json_data,
    chromatic_secondary_json_data,
)


class StrictReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Pilot2ArtifactRecord(StrictReportModel):
    role: str
    path: str
    sha256: str
    size_bytes: int = Field(ge=0)
    media_type: str

    @field_validator("sha256")
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("artifact hashes must be lowercase SHA-256 values")
        return value


class Pilot2ArtifactIndex(StrictReportModel):
    record_type: Literal["pilot2_artifact_index"] = "pilot2_artifact_index"
    schema_version: Literal["2.0"] = "2.0"
    pilot_id: Literal["pilot_2"] = "pilot_2"
    analysis_scope: Literal["requested_label_operational_effect"] = (
        "requested_label_operational_effect"
    )
    executed_model_claims: Literal[False] = False
    cross_label_superiority_estimand: Literal[False] = False
    analysis_result_sha256: str
    artifacts: List[Pilot2ArtifactRecord]
    index_payload_sha256: str

    @field_validator("analysis_result_sha256", "index_payload_sha256")
    @classmethod
    def valid_index_hash(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("index identities must be lowercase SHA-256 values")
        return value


class Pilot2ReportArtifacts(StrictReportModel):
    analysis_json: str
    report_markdown: str
    artifact_index: str
    analysis_json_sha256: str
    report_markdown_sha256: str
    artifact_index_sha256: str
    chromatic_secondary_json: Optional[str] = None
    chromatic_secondary_json_sha256: Optional[str] = None


def _format_number(value: Optional[float], digits: int = 6) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def _format_interval(value: Optional[List[float]]) -> str:
    if value is None:
        return "—"
    return f"[{value[0]:.6f}, {value[1]:.6f}]"


def _estimate_name(value: str) -> str:
    names = {
        "target_improvement": "Target improvement",
        "specificity_difference_in_differences": "Artist-vs-neighbor specificity DiD",
    }
    return names[value]


def _estimate_table_row(row: Pilot2PrimaryEstimate) -> str:
    status = "supported" if row.hypothesis_supported else "not supported"
    return " | ".join(
        [
            f"`{row.requested_model_label}`",
            _estimate_name(row.estimand),
            _format_number(row.estimate),
            _format_interval(row.confidence_interval),
            _format_number(row.familywise_lower_confidence_bound),
            _format_number(row.source_sign_diagnostics.get("aic")),
            _format_number(row.source_sign_diagnostics.get("nga")),
            _format_number(row.exact_sign_flip_p_value, 6),
            _format_number(row.holm_adjusted_p_value, 6),
            status,
        ]
    )


def _chromatic_markdown_lines(result: Pilot2ChromaticSecondaryResult) -> List[str]:
    chromatic_secondary_json_data(result)
    lines = [
        "## Secondary chromatic description",
        "",
        "This Lee-derived seamlessness and mean-rescaled-histogram view is descriptive "
        "only. It cannot open or close the generation gate, rescue the learned-formal "
        "primary analysis, support an executed-model claim, or rank request labels.",
        "",
        "Requested label | Named features | Control features | Complete pairs | "
        "Mean named S | Mean control S | Paired named−control S | "
        "Paired histogram Hellinger",
        "--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:",
    ]
    for row in result.requested_label_summaries:
        lines.append(
            " | ".join(
                [
                    f"`{row.requested_model_label}`",
                    f"{row.named_feature_cells}/{row.expected_named_cells}",
                    f"{row.control_feature_cells}/{row.expected_control_cells}",
                    f"{row.complete_named_control_pairs}/{row.expected_named_cells}",
                    _format_number(row.mean_named_seamlessness),
                    _format_number(row.mean_control_seamlessness),
                    _format_number(
                        row.mean_paired_named_minus_control_seamlessness
                    ),
                    _format_number(
                        row.mean_paired_named_control_histogram_hellinger
                    ),
                ]
            )
        )
    lines.extend(
        [
            "",
            "Requested label | Artist | Complete pairs | Paired named−control S | "
            "Paired histogram Hellinger | Named→real-artist Hellinger | "
            "Control→real-artist Hellinger",
            "--- | --- | ---: | ---: | ---: | ---: | ---:",
        ]
    )
    for row in result.artist_pair_summaries:
        lines.append(
            " | ".join(
                [
                    f"`{row.requested_model_label}`",
                    f"`{row.artist_id}`",
                    f"{row.complete_pairs}/{row.expected_pairs}",
                    _format_number(
                        row.mean_paired_named_minus_control_seamlessness
                    ),
                    _format_number(
                        row.mean_paired_named_control_histogram_hellinger
                    ),
                    _format_number(
                        row.mean_named_to_real_artist_histogram_hellinger
                    ),
                    _format_number(
                        row.mean_control_to_real_artist_histogram_hellinger
                    ),
                ]
            )
        )
    lines.extend(
        [
            "",
            f"Chromatic result SHA-256: `{result.result_sha256}`.",
        ]
    )
    return lines


def render_chromatic_markdown(result: Pilot2ChromaticSecondaryResult) -> str:
    """Render the standalone non-gating chromatic data view."""

    return "\n".join(["# pilot_2 chromatic secondary", "", *_chromatic_markdown_lines(result), ""])


def render_analysis_markdown(
    result: Pilot2AnalysisResult,
    chromatic_secondary: Optional[Pilot2ChromaticSecondaryResult] = None,
) -> str:
    """Render the content-addressed result without making a model-identity claim."""

    # Validate the self-hash before turning the object into public prose.
    analysis_json_data(result)
    completion = result.scientific_completion
    itt = result.itt
    lines = [
        "# pilot_2 requested-label analysis",
        "",
        "## Scope",
        "",
        "This report estimates effects of sending requests bearing the labels "
        "`gpt-image-1` and `gpt-image-2` through the frozen OAuth transport. "
        "The labels define separate operational strata. They are not authoritative "
        "executed-backend identities, no cross-label superiority estimand was registered, "
        "and this report does not rank the labels.",
        "",
        "Named prompts are compared with their matched artist-free control within the "
        "same content block, requested-label stratum, and repetition. Positive target "
        "improvement means the name moved the generated feature toward the target's "
        "held-out real works. Positive specificity difference-in-differences means that "
        "the target-versus-neighbor contrast improved beyond the matched control.",
        "",
        "## Completion and hypothesis support",
        "",
        f"- Scientific execution status: **{completion.status}**.",
        f"- Exact 320-cell assignment grid accounted for: "
        f"**{str(completion.exact_assignment_grid_accounted_for).lower()}**.",
        f"- Complete 256-pair feature estimand grid: "
        f"**{str(completion.feature_estimand_grid_complete).lower()}**.",
        f"- All four label-by-estimand hypotheses supported: "
        f"**{str(result.all_four_primary_hypotheses_supported).lower()}**.",
        "",
        "Completion records whether the frozen study was carried through and accounted "
        "for. It does not imply that any hypothesis was supported. Terminal refusals and "
        "failures can complete the assignment ledger while preventing a complete feature "
        "estimand.",
    ]
    if completion.reasons:
        lines.extend(["", "Recorded completion qualifications:"])
        lines.extend(f"- {reason}" for reason in completion.reasons)

    lines.extend(
        [
            "",
            "## Intention-to-treat accounting",
            "",
            "Requested label | Expected cells | Succeeded | Refused | Terminal failed | "
            "Retry-cap failed | Still retryable | Missing | Complete named/control pairs",
            "--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---:",
        ]
    )
    for label in result.grid.requested_labels:
        row = itt.by_requested_label[label]
        lines.append(
            " | ".join(
                [
                    f"`{label}`",
                    str(row.expected_cells),
                    str(row.succeeded_cells),
                    str(row.refused_cells),
                    str(row.terminal_failure_cells),
                    str(row.failed_after_retry_cap_cells),
                    str(row.retryable_failure_cells),
                    str(row.missing_cells),
                    f"{row.complete_feature_pairs}/{row.expected_pairs}",
                ]
            )
        )
    lines.extend(
        [
            "",
            f"Across all assignments: {itt.refused_cells} refused cells, "
            f"{itt.terminal_failure_cells} terminal failures "
            f"({itt.failed_after_retry_cap_cells} after the fixed retry cap), "
            f"{itt.missing_cells} missing "
            f"cells, and {itt.succeeded_without_feature_cells} successful cells without "
            "an analyzable projected feature. These outcomes are retained in the ITT "
            "accounting and are not silently removed.",
            "",
            "## Primary requested-label-stratum estimates",
            "",
            "Requested label | Estimand | Estimate | 95% cluster interval | "
            "Familywise lower bound | AIC-only | NGA-only | Exact block sign-flip p | "
            "Holm-adjusted p | Decision",
            "--- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---",
        ]
    )
    lines.extend(_estimate_table_row(row) for row in result.primary_estimates)
    lines.extend(
        [
            "",
            "The interval is the deterministic two-stage cluster bootstrap: real works "
            "are resampled within artist-by-source cells, then the eight content blocks "
            "and repetitions are resampled while every named/control pair is preserved. "
            f"The run uses {result.bootstrap_draws:,} draws and seed "
            f"`{result.bootstrap_seed}`. Exact one-sided inference flips the signs of the "
            "eight block estimates; Holm correction covers the fixed family of two "
            "requested-label strata by two primary estimands. AIC-only and NGA-only signs "
            "must both be positive for support. The support decision uses the one-sided "
            "Bonferroni familywise lower bound at quantile `0.0125`, not the descriptive "
            "two-sided 95% interval.",
            "",
            "## Secondary per-artist estimates",
            "",
            "Requested label | Artist | Estimand | Estimate | AIC-only | NGA-only | "
            "Complete pairs",
            "--- | --- | --- | ---: | ---: | ---: | ---:",
        ]
    )
    for row in result.secondary_artist_estimates:
        lines.append(
            " | ".join(
                [
                    f"`{row.requested_model_label}`",
                    f"`{row.artist_id}`",
                    _estimate_name(row.estimand),
                    _format_number(row.estimate),
                    _format_number(row.source_estimates.get("aic")),
                    _format_number(row.source_estimates.get("nga")),
                    f"{row.complete_pairs}/{row.expected_pairs}",
                ]
            )
        )
    if chromatic_secondary is not None:
        lines.extend(["", *_chromatic_markdown_lines(chromatic_secondary)])
    lines.extend(
        [
            "",
            "These preregistered per-artist values are descriptive secondary estimates. "
            "They carry no confidence interval, multiplicity adjustment, or separate "
            "hypothesis-support claim.",
            "",
            "## Interpretation boundary",
            "",
            "Any supported row applies only to outputs obtained after sending that request "
            "label through the pinned transport, the frozen prompts, and the frozen digital "
            "reference atlas. It is not evidence about an authoritative executed model, "
            "physical artworks, arbitrary digitizations, or a ranking between labels.",
            "",
            f"Analysis result SHA-256: `{result.result_sha256}`.",
            "",
        ]
    )
    return "\n".join(lines)


def markdown_data(
    result: Pilot2AnalysisResult,
    chromatic_secondary: Optional[Pilot2ChromaticSecondaryResult] = None,
) -> str:
    """Alias emphasizing that Markdown is a deterministic public data view."""

    return render_analysis_markdown(result, chromatic_secondary)


def json_data(result: Pilot2AnalysisResult) -> Dict[str, Any]:
    return analysis_json_data(result)


def chromatic_json_data(result: Pilot2ChromaticSecondaryResult) -> Dict[str, Any]:
    return chromatic_secondary_json_data(result)


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _media_type(path: Path) -> str:
    return {
        ".json": "application/json",
        ".jsonl": "application/x-ndjson",
        ".md": "text/markdown",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(path.suffix.casefold(), "application/octet-stream")


def _relative_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"artifact lies outside the declared evidence root: {path}") from exc


def artifact_index_data(
    result: Pilot2AnalysisResult,
    artifacts: Mapping[str, Path],
    *,
    root: Path,
) -> Pilot2ArtifactIndex:
    """Build a path-sanitized index for already-written evidence artifacts."""

    if not artifacts:
        raise ValueError("artifact index requires at least one artifact")
    rows: List[Pilot2ArtifactRecord] = []
    seen_paths: set[str] = set()
    for role, raw_path in sorted(artifacts.items()):
        path = Path(raw_path)
        if not path.is_file():
            raise FileNotFoundError(f"missing pilot_2 artifact: {path}")
        relative = _relative_path(path, root)
        if relative in seen_paths:
            raise ValueError(f"artifact path is indexed more than once: {relative}")
        seen_paths.add(relative)
        rows.append(
            Pilot2ArtifactRecord(
                role=role,
                path=relative,
                sha256=hash_file(path),
                size_bytes=path.stat().st_size,
                media_type=_media_type(path),
            )
        )
    payload: Dict[str, Any] = {
        "record_type": "pilot2_artifact_index",
        "schema_version": "2.0",
        "pilot_id": "pilot_2",
        "analysis_scope": "requested_label_operational_effect",
        "executed_model_claims": False,
        "cross_label_superiority_estimand": False,
        "analysis_result_sha256": result.result_sha256,
        "artifacts": [row.model_dump(mode="json") for row in rows],
    }
    payload["index_payload_sha256"] = stable_hash(payload)
    return Pilot2ArtifactIndex.model_validate(payload)


def write_pilot2_report(
    result: Pilot2AnalysisResult,
    output_dir: Path,
    *,
    evidence_root: Optional[Path] = None,
    input_artifacts: Optional[Mapping[str, Path]] = None,
    chromatic_secondary: Optional[Pilot2ChromaticSecondaryResult] = None,
) -> Pilot2ReportArtifacts:
    """Write the canonical JSON, Markdown, and non-self-referential index."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    root = output_dir if evidence_root is None else Path(evidence_root)
    analysis_path = output_dir / "analysis.json"
    report_path = output_dir / "REPORT.md"
    index_path = output_dir / "artifact_index.json"
    chromatic_path = output_dir / "chromatic_secondary.json"

    write_json(analysis_path, json_data(result))
    _atomic_text(report_path, markdown_data(result, chromatic_secondary))
    artifacts: Dict[str, Path] = dict(input_artifacts or {})
    reserved = {"analysis_json", "report_markdown", "chromatic_secondary_json"}
    if reserved.intersection(artifacts):
        raise ValueError("reserved report artifact roles cannot be overridden")
    artifacts["analysis_json"] = analysis_path
    artifacts["report_markdown"] = report_path
    if chromatic_secondary is not None:
        write_json(chromatic_path, chromatic_secondary_json_data(chromatic_secondary))
        artifacts["chromatic_secondary_json"] = chromatic_path
    index = artifact_index_data(result, artifacts, root=root)
    write_json(index_path, index)
    return Pilot2ReportArtifacts(
        analysis_json=str(analysis_path),
        report_markdown=str(report_path),
        artifact_index=str(index_path),
        analysis_json_sha256=hash_file(analysis_path),
        report_markdown_sha256=hash_file(report_path),
        artifact_index_sha256=hash_file(index_path),
        chromatic_secondary_json=(
            str(chromatic_path) if chromatic_secondary is not None else None
        ),
        chromatic_secondary_json_sha256=(
            hash_file(chromatic_path) if chromatic_secondary is not None else None
        ),
    )


__all__ = [
    "Pilot2ArtifactIndex",
    "Pilot2ArtifactRecord",
    "Pilot2ReportArtifacts",
    "artifact_index_data",
    "chromatic_json_data",
    "json_data",
    "markdown_data",
    "render_analysis_markdown",
    "render_chromatic_markdown",
    "write_pilot2_report",
]
