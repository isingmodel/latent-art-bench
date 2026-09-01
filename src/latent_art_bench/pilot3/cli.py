"""Fail-closed command line interface for Pilot 3 planning and execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import httpx
import typer

from latent_art_bench.pilot3.execution import (
    capture_oauth_runtime_evidence,
    finalize_pilot,
    measure_generated_outputs,
    run_canonical_generation_grid,
    run_canonical_transport_qualification,
    run_verified_analysis,
    verify_generation_gate,
    verify_pilot_completion,
    write_generation_completion,
    write_generation_gate,
    write_qualification_authorization,
    write_terminal_envelope,
)
from latent_art_bench.pilot3.met_r2 import (
    TransportResponse as MetR2TransportResponse,
)
from latent_art_bench.pilot3.met_r2 import (
    acquire_official_images,
    capture_official_metadata,
    freeze_metadata_targets,
    write_offline_authorization,
)
from latent_art_bench.pilot3.normalization_scope import (
    write_normalization_scope_authorization,
)
from latent_art_bench.pilot3.phasea import (
    DEFAULT_CONFIG as DEFAULT_PHASE_A_CONFIG,
)
from latent_art_bench.pilot3.phasea import (
    acquire_real_partition,
    extract_real_partition,
    freeze_a_vector_protocol,
    run_determinism_probes,
    unseal_and_validate_external,
    verify_external_holdout_result,
)
from latent_art_bench.pilot3.planning import (
    DEFAULT_CONFIG,
    verify_planning_bundle,
    write_planning_bundle,
)

app = typer.Typer(
    name="pilot3",
    no_args_is_help=True,
    help="Plan and run the separately gated Pilot 3 study.",
)


def _met_r2_requester(
    client: httpx.Client, *, accept: str
) -> Callable[[str], MetR2TransportResponse]:
    """Adapt one redirect-disabled HTTP GET to the R2 transport envelope."""

    def request(url: str) -> MetR2TransportResponse:
        response = client.get(url, headers={"Accept": accept})
        return MetR2TransportResponse(
            status_code=response.status_code,
            body=response.content,
            headers=dict(response.headers),
            final_url=str(response.url),
            redirect_chain=tuple(str(item.url) for item in response.history),
        )

    return request


@app.command("plan")
def plan_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config", help="Planning JSON."),
) -> None:
    """Write the deterministic planning-only evidence bundle."""

    index = write_planning_bundle(root, config_path)
    typer.echo(
        json.dumps(
            {
                "status": index["status"],
                "generation_gate": index["generation_gate"],
                "successor_metadata_audit_status": index["decision"][
                    "successor_metadata_audit_status"
                ],
                "successor_snapshot_threshold_result": index["decision"][
                    "successor_snapshot_threshold_result"
                ],
                "successor_metadata_decision": index["decision"]["successor_metadata_decision"],
                "metadata_audit_decision": index["decision"]["metadata_audit_decision"],
                "freeze_a1_ready": index["decision"]["p3_t01_freeze_ready"],
                "phase_a_artwork_acquisition_authorized": index["decision"][
                    "phase_a_artwork_acquisition_authorized"
                ],
                "design_decision": index["decision"]["design_decision"],
                "result_sha256": index["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("verify")
def verify_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config", help="Planning JSON."),
) -> None:
    """Recompute and verify all planning evidence; never write or contact a network."""

    index = verify_planning_bundle(root, config_path)
    typer.echo(
        json.dumps(
            {
                "status": "verified",
                "generation_gate": index["generation_gate"],
                "result_sha256": index["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("authorize-met-r2")
def authorize_met_r2_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Write the offline official-Met authorization; performs no network access."""

    result = write_offline_authorization(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "authorization_sha256": result["authorization_sha256"],
                "metadata_request_count": 0,
                "image_request_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("capture-met-r2-metadata")
def capture_met_r2_metadata_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Capture the twenty fixed official-Met object records exactly once each."""

    with httpx.Client(
        follow_redirects=False,
        timeout=120.0,
        trust_env=False,
    ) as client:
        rows = capture_official_metadata(
            root,
            _met_r2_requester(client, accept="application/json"),
        )
    typer.echo(
        json.dumps(
            {
                "status": "metadata_captured",
                "terminal_count": len(rows),
                "successful_terminal_count": sum(
                    row["outcome"] == "success" for row in rows
                ),
                "image_request_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("freeze-met-r2-metadata")
def freeze_met_r2_metadata_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Freeze the twenty metadata-derived primaryImage URLs without network I/O."""

    result = freeze_metadata_targets(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "freeze_sha256": result["freeze_sha256"],
                "image_request_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("acquire-met-r2-images")
def acquire_met_r2_images_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Acquire the committed twenty-image official-Met primaryImage cohort."""

    with httpx.Client(
        follow_redirects=False,
        timeout=120.0,
        trust_env=False,
    ) as client:
        rows = acquire_official_images(
            root,
            _met_r2_requester(client, accept="image/jpeg"),
        )
    typer.echo(
        json.dumps(
            {
                "status": "all_20_official_primary_images_eligible",
                "acquisition_count": len(rows),
                "cohort_observation_sha256": rows[0]["cohort_observation_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("authorize-normalization-scope")
def authorize_normalization_scope_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Authorize exact Met, external, and generated normalization membership."""

    result = write_normalization_scope_authorization(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "authorization_sha256": result["authorization_sha256"],
                "network_request_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("acquire-real")
def acquire_real_command(
    phase: str = typer.Option(..., "--phase", help="development only"),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Acquire development bytes; external access uses unseal-external."""

    rows = acquire_real_partition(
        root,
        phase=phase,
        config_path=config_path,
    )
    typer.echo(json.dumps({"phase": phase, "acquired_count": len(rows)}, sort_keys=True))


@app.command("extract-real")
def extract_real_command(
    phase: str = typer.Option(..., "--phase", help="development only"),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Extract development A-vectors; external access uses unseal-external."""

    rows = extract_real_partition(
        root,
        phase=phase,
        config_path=config_path,
    )
    typer.echo(json.dumps({"phase": phase, "feature_count": len(rows)}, sort_keys=True))


@app.command("probe-real-determinism")
def probe_real_determinism_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Run the eight artist-by-development-source exact repeat probes."""

    rows = run_determinism_probes(root, config_path=config_path)
    typer.echo(
        json.dumps(
            {
                "probe_count": len(rows),
                "status": "pass" if all(row["exact_equal"] for row in rows) else "fail",
            },
            sort_keys=True,
        )
    )


@app.command("freeze-a2")
def freeze_a2_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Fit development-only state and emit the external-unseal P3-T07 token."""

    result = freeze_a_vector_protocol(root, config_path=config_path)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "external_unseal_token": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("unseal-external")
def unseal_external_command(
    external_unseal_token: str = typer.Option(
        ..., "--external-unseal-token", help="Exact committed P3-T07 self-hash."
    ),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Atomically consume P3-T07, acquire/extract the holdout, and write P3-T08."""

    result = unseal_and_validate_external(
        root,
        external_unseal_token=external_unseal_token,
        config_path=config_path,
    )
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("validate-external")
def validate_external_command(
    external_unseal_token: str = typer.Option(
        ..., "--external-unseal-token", help="Exact committed P3-T07 self-hash."
    ),
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(
        DEFAULT_PHASE_A_CONFIG, "--config", help="Phase-A JSON config."
    ),
) -> None:
    """Recompute and verify an existing P3-T08 without opening new image URLs."""

    result = verify_external_holdout_result(
        root,
        external_unseal_token=external_unseal_token,
        config_path=config_path,
    )
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("freeze-b-gate")
def freeze_b_gate_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Build P3-T14 from the canonical Phase-A, transport, and design files."""

    result = write_generation_gate(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "generation_authorized_after_commit": True,
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("authorize-transport")
def authorize_transport_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Write the exact user-authorized P3-T11/P3-T14 request scope."""

    result = write_qualification_authorization(root)
    typer.echo(
        json.dumps(
            {
                "status": "written_or_verified",
                "evidence_sha256": result["evidence_sha256"],
                "network_request_count": 0,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("capture-oauth-runtime")
def capture_oauth_runtime_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Capture the exact listener fingerprint and model-documentation evidence."""

    typer.echo(json.dumps(capture_oauth_runtime_evidence(root), indent=2, sort_keys=True))


@app.command("qualify-transport")
def qualify_transport_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Run or recover the one-shot neutral P3-T11 request through its file gate."""

    result = run_canonical_transport_qualification(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "outcome": result["outcome"],
                "physical_post_count": result["physical_post_count"],
                "report_sha256": result["report_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("run-generation")
def run_generation_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Run/resume the frozen 320-call grid and persist verified execution evidence."""

    result = run_canonical_generation_grid(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "attempt_count": result["attempt_count"],
                "global_stop_triggered": result["global_stop_triggered"],
                "report_sha256": result["report_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("verify-b-gate")
def verify_b_gate_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Recompute P3-T14 and require its complete closure committed and clean."""

    result = verify_generation_gate(root, require_committed=True)
    typer.echo(
        json.dumps(
            {"status": "verified_open", "result_sha256": result["result_sha256"]},
            indent=2,
            sort_keys=True,
        )
    )


@app.command("finalize-generation")
def finalize_generation_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Verify all durable generation evidence and write its completion artifact."""

    result = write_generation_completion(root)
    typer.echo(
        json.dumps(
            {
                "status": (
                    "global_stop_complete"
                    if result["global_stop_triggered"]
                    else "complete" if result["all_cells_terminal"] else "incomplete"
                ),
                "terminal_requests": result["cell_count"],
                "successful_outputs": result["successful_output_count"],
                "not_sent_global_stop": result["global_stop_disposition_count"],
                "report_sha256": result["report_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("measure-generated")
def measure_generated_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Extract frozen P3-T07 A-vectors and distances for successful PNGs."""

    result = measure_generated_outputs(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "a_vector_count": result["a_vector_count"],
                "distance_count": result["distance_count"],
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("seal-terminals")
def seal_terminals_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Derive the exact post-measurement terminal-disposition envelope."""

    result = write_terminal_envelope(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "terminal_requests": result["terminal_request_count"],
                "category_counts": result["terminal_category_counts"],
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("analyze")
def analyze_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Run the registered analysis from verified canonical on-disk artifacts."""

    result = run_verified_analysis(root)
    typer.echo(
        json.dumps(
            {
                "status": result["status"],
                "decision": result["decision"]["status"],
                "result_sha256": result["result_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("finalize")
def finalize_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Write the report, completion record, requirement audit, and artifact index."""

    typer.echo(json.dumps(finalize_pilot(root), indent=2, sort_keys=True))


@app.command("verify-complete")
def verify_complete_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
) -> None:
    """Run the complete offline Pilot-3 verifier."""

    typer.echo(json.dumps(verify_pilot_completion(root), indent=2, sort_keys=True))


if __name__ == "__main__":
    app()
