#!/usr/bin/env python3
"""Prospective, auditable AIC browser-recovery workflow for Pilot 3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from latent_art_bench.pilot3.phasea import (
    authorize_aic_browser_recovery,
    authorize_preprocessing_determinism_amendment,
    create_normalization_revalidations,
    import_aic_browser_recovery_directory,
    prepare_aic_browser_recovery,
    require_preprocessing_incident_resolution,
    verify_aic_browser_recovery_authorization,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Authorize, prepare, and reconcile exact-URL AIC browser downloads "
            "without rewriting the Pilot 3 HTTP journal."
        )
    )
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "authorize",
        help="write the provider-recovery authorization; performs no browser/image I/O",
    )
    prepare = subparsers.add_parser(
        "prepare",
        help="fsync one exact browser intent/start before navigating that URL",
    )
    prepare.add_argument("--work-id", required=True, help="frozen canonical AIC work ID")
    prepare.add_argument(
        "--download-directory",
        required=True,
        type=Path,
        help="dedicated path that does not yet exist; prepare creates and binds it empty",
    )
    reconcile = subparsers.add_parser(
        "import",
        help="reconcile a completed browser file by its binary WhereFroms xattr",
    )
    reconcile.add_argument(
        "--directory",
        required=True,
        type=Path,
        help="non-symlink directory whose direct completed files are inspected",
    )
    subparsers.add_parser("verify", help="verify the committed authorization and closure")
    subparsers.add_parser(
        "authorize-preprocessing-amendment",
        help=(
            "write the prospective Pilot-3 v2 normalization authorization; "
            "performs no image, browser, feature, or network I/O"
        ),
    )
    subparsers.add_parser(
        "revalidate-normalization",
        help="append the exact 12-row offline v1-to-v2 normalization revalidation",
    )
    subparsers.add_parser(
        "verify-preprocessing-remediation",
        help="verify the committed amendment and complete committed revalidation ledger",
    )
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    root = arguments.root.expanduser().resolve()
    if arguments.command == "authorize":
        result = authorize_aic_browser_recovery(root)
        summary = {
            "status": result["status"],
            "authorization_sha256": result["authorization_sha256"],
            "target_count": result["target_count"],
            "network_or_browser_request_performed": False,
        }
    elif arguments.command == "prepare":
        result = prepare_aic_browser_recovery(
            root, arguments.work_id, arguments.download_directory
        )
        summary = {
            "status": "browser_attempt_start_fsynced_before_navigation",
            "canonical_work_id": result["canonical_work_id"],
            "image_url": result["image_url"],
            "browser_attempt_id": result["browser_attempt_id"],
            "start_event_sha256": result["event_sha256"],
            "download_directory_path": result["download_directory_path"],
            "network_or_browser_request_performed": False,
        }
    elif arguments.command == "import":
        result = import_aic_browser_recovery_directory(root, arguments.directory)
        summary = {
            "status": "completed_browser_files_reconciled",
            "acquisition_count": len(result),
            "canonical_work_ids": [row["canonical_work_id"] for row in result],
            "record_sha256": [row["record_sha256"] for row in result],
            "network_or_browser_request_performed": False,
        }
    elif arguments.command == "verify":
        if (root / "reports/pilot_3/evidence/preprocessing_determinism_incident.json").is_file():
            resolution = require_preprocessing_incident_resolution(root)
            result = resolution["amendment"]
            summary = {
                "status": "historical_browser_authorization_verified_through_remediation",
                "authorization_sha256": result[
                    "original_browser_authorization_sha256"
                ],
                "target_count": result["target_count"],
                "normalization_amendment_sha256": result["authorization_sha256"],
                "normalization_revalidation_count": len(resolution["corrections"]),
                "network_or_browser_request_performed": False,
            }
        else:
            result = verify_aic_browser_recovery_authorization(root)
            summary = {
                "status": "verified",
                "authorization_sha256": result["authorization_sha256"],
                "target_count": result["target_count"],
                "network_or_browser_request_performed": False,
            }
    elif arguments.command == "authorize-preprocessing-amendment":
        result = authorize_preprocessing_determinism_amendment(root)
        summary = {
            "status": result["status"],
            "authorization_sha256": result["authorization_sha256"],
            "normalization_protocol_version": result[
                "normalization_protocol_version"
            ],
            "network_browser_image_or_feature_operation_performed": False,
        }
    elif arguments.command == "revalidate-normalization":
        rows = create_normalization_revalidations(root)
        summary = {
            "status": "normalization_revalidation_appended",
            "row_count": len(rows),
            "superseded_work_ids": [
                row["canonical_work_id"]
                for row in rows
                if row["disposition"] == "superseded"
            ],
            "network_browser_or_feature_operation_performed": False,
        }
    else:
        result = require_preprocessing_incident_resolution(root)
        summary = {
            "status": "preprocessing_incident_resolved",
            "authorization_sha256": result["amendment"]["authorization_sha256"],
            "revalidation_count": len(result["corrections"]),
            "network_browser_or_feature_operation_performed": False,
            "local_image_revalidation_performed": True,
        }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
