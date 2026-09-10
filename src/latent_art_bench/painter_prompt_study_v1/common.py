"""Paths and clean-input boundaries for the prospective prompt study."""

from __future__ import annotations

import subprocess
from pathlib import Path

NAMESPACE = "painter_prompt_study_v1"
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
PROTOCOL = Path("studies") / NAMESPACE / "PROTOCOL.md"
CONFIG = Path("configs") / NAMESPACE / "study.json"


def committed(root: Path, paths: list[Path]) -> str:
    for path in paths:
        blob = subprocess.run(["git", "show", f"HEAD:{path.as_posix()}"],
                              cwd=root, capture_output=True)
        if blob.returncode or blob.stdout != (root / path).read_bytes():
            raise ValueError(f"commit exact prospective input first: {path}")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
