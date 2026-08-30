import json
from pathlib import Path

from typer.testing import CliRunner

from latent_art_bench.cli import app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_generation_dry_run_plans_exactly_two_models(tmp_path: Path) -> None:
    runner = CliRunner()
    manifest = tmp_path / "calls.jsonl"
    result = runner.invoke(
        app,
        [
            "generate",
            "--dry-run",
            "--root",
            str(tmp_path),
            "--config",
            str(REPOSITORY_ROOT / "configs/pilot_0/pilot.yaml"),
            "--prompt-manifest",
            str(REPOSITORY_ROOT / "configs/pilot_0/prompts.api_smoke.jsonl"),
            "--output-manifest",
            str(manifest),
        ],
    )
    assert result.exit_code == 0, result.output
    contents = manifest.read_text(encoding="utf-8")
    assert '"model":"gpt-image-1"' in contents
    assert '"model":"gpt-image-2"' in contents
    assert contents.count('"record_type":"generation_call"') == 2
    run_path = next((tmp_path / "artifacts/runs").glob("*.json"))
    run = json.loads(run_path.read_text(encoding="utf-8"))
    assert run["resolved_config"]["generation"]["models"] == [
        "gpt-image-1",
        "gpt-image-2",
    ]
    assert len(run["resolved_config_sha256"]) == 64


def test_live_generation_is_blocked_without_qualification_or_bypass(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "generate",
            "--root",
            str(tmp_path),
            "--config",
            str(REPOSITORY_ROOT / "configs/pilot_0/pilot.yaml"),
            "--prompt-manifest",
            str(REPOSITORY_ROOT / "configs/pilot_0/prompts.api_smoke.jsonl"),
        ],
    )
    assert result.exit_code != 0
    assert "qualification gate is closed" in str(result.exception)
