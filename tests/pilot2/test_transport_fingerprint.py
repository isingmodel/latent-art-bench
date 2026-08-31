from __future__ import annotations

import subprocess
from pathlib import Path

import httpx
import pytest

from latent_art_bench.pilot2.transport import (
    OAuthProcessEvidence,
    OAuthTransportConfig,
    RuntimeFingerprintError,
    capture_oauth_runtime_fingerprint,
    capture_oauth_source_snapshot,
    revalidate_oauth_runtime_fingerprint,
    verify_oauth_runtime_fingerprint,
)


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _git_checkout(tmp_path: Path) -> Path:
    checkout = tmp_path / "openai-oauth"
    source = checkout / "packages/openai-oauth/src"
    source.mkdir(parents=True)
    (checkout / "package.json").write_text('{"name":"fixture"}\n')
    (source / "server.ts").write_text("export const route = 'old'\n")
    _run("git", "init", "-q", cwd=checkout)
    _run("git", "config", "user.email", "pilot2@example.test", cwd=checkout)
    _run("git", "config", "user.name", "Pilot Two", cwd=checkout)
    _run("git", "add", "package.json", "packages/openai-oauth/src/server.ts", cwd=checkout)
    _run("git", "commit", "-qm", "fixture", cwd=checkout)
    _run(
        "git",
        "remote",
        "add",
        "origin",
        "https://embedded-user@example.test/openai-oauth.git?token=bad",
        cwd=checkout,
    )
    return checkout


def test_dirty_runtime_source_is_reconstructable_and_nonruntime_dirt_is_separate(
    tmp_path: Path,
) -> None:
    checkout = _git_checkout(tmp_path)
    (checkout / "packages/openai-oauth/src/server.ts").write_text(
        "export const route = 'new'\n"
    )
    untracked = checkout / "packages/openai-oauth/src/images.ts"
    untracked.write_text("export const models = ['gpt-image-1', 'gpt-image-2']\n")
    (checkout / "README.md").write_text("not runtime source\n")

    snapshot = capture_oauth_source_snapshot(checkout)

    assert snapshot.dirty is True
    assert snapshot.dirty_runtime_source_capture_complete is True
    assert "route = 'new'" in snapshot.tracked_diff
    assert snapshot.untracked_source_contents[
        "packages/openai-oauth/src/images.ts"
    ] == untracked.read_text()
    assert "README.md" in snapshot.excluded_dirty_paths
    assert "embedded-user" not in snapshot.git_remote
    assert "token=bad" not in snapshot.git_remote
    assert snapshot.git_remote == "https://example.test/openai-oauth.git"
    assert len(snapshot.source_snapshot_sha256) == 64


def test_fingerprint_refuses_to_persist_a_possible_secret(tmp_path: Path) -> None:
    checkout = _git_checkout(tmp_path)
    (checkout / "packages/openai-oauth/src/images.ts").write_text(
        "export const key = 'sk-abcdefghijklmnopqrstuvwxyz'\n"
    )

    with pytest.raises(RuntimeFingerprintError, match="possible secret"):
        capture_oauth_source_snapshot(checkout)


def test_runtime_fingerprint_binds_source_process_health_and_catalog(
    tmp_path: Path,
) -> None:
    checkout = _git_checkout(tmp_path)
    (checkout / "packages/openai-oauth/src/images.ts").write_text(
        "export const imageModels = ['gpt-image-1', 'gpt-image-2']\n"
    )
    config = OAuthTransportConfig(
        base_url="http://127.0.0.1:19531/v1",
        checkout_path=checkout,
        required_checkout_path=checkout,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True, "replay_state": "stateful"})
        if request.url.path == "/v1/models":
            return httpx.Response(
                200,
                json={
                    "object": "list",
                    "data": [
                        {"id": "gpt-image-2"},
                        {"id": "unrelated-model"},
                        {"id": "gpt-image-1"},
                    ],
                },
            )
        raise AssertionError(request.url)

    def process_inspector(host: str, port: int, root: Path) -> OAuthProcessEvidence:
        assert (host, port, root) == ("127.0.0.1", 19531, checkout.resolve())
        return OAuthProcessEvidence(
            pid=456,
            cwd=str(checkout / "packages/openai-oauth"),
            cwd_inside_checkout=True,
            command_sanitized="bun src/cli.ts --oauth-file <redacted>",
            command_sha256="2" * 64,
            runtime_version="1.2.3",
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fingerprint = capture_oauth_runtime_fingerprint(
        config, client=client, process_inspector=process_inspector
    )
    client.close()

    assert fingerprint.runtime_ready is True
    assert fingerprint.source.dirty is True
    assert fingerprint.source.dirty_runtime_source_capture_complete is True
    assert fingerprint.health_ok is True
    assert fingerprint.model_catalog_contains_required_labels is True
    assert fingerprint.model_catalog.parsed_summary["model_ids"] == [
        "gpt-image-1",
        "gpt-image-2",
        "unrelated-model",
    ]
    assert fingerprint.executed_model_claims is False
    assert len(fingerprint.fingerprint_sha256) == 64
    verify_oauth_runtime_fingerprint(fingerprint)
    tampered = fingerprint.model_copy(update={"health_ok": False})
    with pytest.raises(RuntimeFingerprintError, match="hash does not match"):
        verify_oauth_runtime_fingerprint(tampered)


def test_live_revalidation_ignores_recapture_identity_but_checks_pid_and_source(
    tmp_path: Path,
) -> None:
    checkout = _git_checkout(tmp_path)
    image_source = checkout / "packages/openai-oauth/src/images.ts"
    image_source.write_text("export const models = ['gpt-image-1', 'gpt-image-2']\n")
    config = OAuthTransportConfig(
        base_url="http://127.0.0.1:19531/v1",
        checkout_path=checkout,
        required_checkout_path=checkout,
    )
    current_pid = 700

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(
            200,
            json={"data": [{"id": "gpt-image-1"}, {"id": "gpt-image-2"}]},
        )

    def inspector(_: str, __: int, root: Path) -> OAuthProcessEvidence:
        return OAuthProcessEvidence(
            pid=current_pid,
            cwd=str(root / "packages/openai-oauth"),
            cwd_inside_checkout=True,
            command_sanitized="bun src/cli.ts --oauth-file <redacted>",
            command_sha256="3" * 64,
            executable_sha256="4" * 64,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    frozen = capture_oauth_runtime_fingerprint(
        config, client=client, process_inspector=inspector
    )
    revalidation = revalidate_oauth_runtime_fingerprint(
        config, frozen, client=client, process_inspector=inspector
    )
    assert revalidation.status == "pass"
    assert revalidation.persisted_fingerprint_sha256 == frozen.fingerprint_sha256
    assert revalidation.current_source_snapshot_sha256 == (
        frozen.source.source_snapshot_sha256
    )
    assert all(revalidation.checks.values())

    current_pid = 701
    with pytest.raises(RuntimeFingerprintError, match="listener_pid"):
        revalidate_oauth_runtime_fingerprint(
            config, frozen, client=client, process_inspector=inspector
        )
    current_pid = 700
    image_source.write_text("export const models = ['changed']\n")
    with pytest.raises(RuntimeFingerprintError, match="source_snapshot"):
        revalidate_oauth_runtime_fingerprint(
            config, frozen, client=client, process_inspector=inspector
        )
    client.close()


def test_transport_config_rejects_non_loopback_and_wrong_checkout(tmp_path: Path) -> None:
    checkout = tmp_path / "openai-oauth"
    checkout.mkdir()
    with pytest.raises(ValueError, match="loopback"):
        OAuthTransportConfig(
            base_url="https://api.openai.com/v1",
            checkout_path=checkout,
            required_checkout_path=checkout,
        )
    with pytest.raises(ValueError, match="pinned checkout"):
        OAuthTransportConfig(
            base_url="http://127.0.0.1:10531/v1",
            checkout_path=checkout,
            required_checkout_path=tmp_path / "different",
        )
