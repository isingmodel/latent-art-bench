"""Public CLI gate tests; no test may construct a live transport or mutate source evidence."""

import json
from pathlib import Path

import pytest

from latent_art_bench.painter_prompt_study_v1 import cli, generation
from latent_art_bench.painter_prompt_study_v1.common import CONFIG

REPO = Path(__file__).resolve().parents[2]


def test_plan_public_entry_point_reads_numeric_evidence_without_transport(monkeypatch, capsys):
    def forbidden(*_args, **_kwargs):
        pytest.fail("planning cannot create a transport or dispatch generation")

    monkeypatch.setattr(generation.httpx, "Client", forbidden)
    monkeypatch.setattr(generation, "execute", forbidden)
    assert cli.main(["--root", str(REPO), "plan"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "planning_only_no_provider_calls"
    assert result["requests"] == 480 * result["repetitions"]
    assert result["literal_prompts"] == 240


def test_unauthorized_prepare_public_entry_point_fails_before_any_output(
    tmp_path, monkeypatch, capsys,
):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'offline-fixture'\n")
    config = json.loads((REPO / CONFIG).read_text())
    config.update(approved_maximum_requests=0, authorization=None)
    (tmp_path / "proposed.json").write_text(json.dumps(config))
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    monkeypatch.setattr(generation.httpx, "Client", lambda **_: pytest.fail("must not send"))
    result = cli.main(["--root", str(tmp_path), "prepare", "unauthorized-fixture",
                       "--proxy-root", str(tmp_path / "missing-proxy"),
                       "--config", "proposed.json"])
    assert result == 2
    captured = capsys.readouterr()
    assert "explicit user authorization" in captured.err
    assert not captured.out
    assert sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*")) == before


@pytest.mark.parametrize("command", ["prepare", "generate"])
def test_active_commands_require_explicit_proxy_source(command):
    with pytest.raises(SystemExit) as error:
        cli.parser().parse_args([command, "run-fixture"])
    assert error.value.code == 2


def test_generate_dispatch_preserves_explicit_batch_and_proxy_without_calling_transport(
    tmp_path, monkeypatch, capsys,
):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'offline-fixture'\n")
    calls = []

    def execute(root, run_id, **kwargs):
        calls.append((root, run_id, kwargs))
        return dict(status="paused_batch_limit", terminal=False)

    monkeypatch.setattr(generation, "execute", execute)
    assert cli.main(["--root", str(tmp_path), "generate", "run-fixture",
                     "--proxy-root", str(tmp_path / "proxy-fixture"),
                     "--max-new-requests", "0"]) == 0
    assert calls == [(tmp_path, "run-fixture", dict(
        max_new_requests=0, proxy_root=tmp_path / "proxy-fixture"))]
    assert json.loads(capsys.readouterr().out)["terminal"] is False


def test_missing_repository_root_fails_before_dispatch(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(generation, "execute",
                        lambda *_args, **_kwargs: pytest.fail("must not send"))
    assert cli.main(["--root", str(tmp_path), "generate", "run-fixture",
                     "--proxy-root", str(tmp_path / "proxy-fixture")]) == 2
    assert "repository root" in capsys.readouterr().err
