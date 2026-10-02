"""Package the anonymous TMLR supplementary archive.

Run ``uv run --locked python paper/tmlr/make_supplement.py`` after
``make tmlr-check``. It writes ``tmp/paper/tmlr-supplement.zip`` (not tracked),
with the manuscript sources, the asset builder, every analysis output the builder
reads, and the per-image features and embeddings. The archive is deterministic
and is refused if any file contains an identifying string or if it exceeds TMLR's
100 MB supplementary limit. It does not contain images.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = ROOT / "tmp/paper/tmlr-supplement.zip"
LIMIT = 100 * 1024 * 1024
STAMP = (2026, 1, 1, 0, 0, 0)

sys.path.insert(0, str(HERE))
from build_assets import INPUTS  # noqa: E402

EXTRA = (
    "reports/painter_learned_audit_v1/extraction_clip.json",
    "reports/painter_learned_audit_v1/extraction_csd.json",
    "reports/painter_learned_audit_v1/embeddings_clip.npz",
    "reports/painter_learned_audit_v1/embeddings_csd.npz",
    "data/manifests/painter_specificity_v2/psv2-20260911/measurements.jsonl",
    "studies/painter_tmlr_diagnostics_v1/PLAN.md",
    "studies/painter_specificity_v2/PROTOCOL.md",
    "studies/painter_specificity_v1/PROTOCOL.md",
)
TRANSFER = "reports/painter_prototype_transfer_v1/analysis.json"
EVIDENCE = tuple(
    sorted({rel + ".gz" if rel == TRANSFER else rel for rel, _ in INPUTS.values()} | set(EXTRA))
)
IDENTIFYING = re.compile(
    r"/Users/|isingmodel|\bfred\b|kibum|kakao|neuralnetwork@|github\.com/isingmodel",
    re.IGNORECASE,
)

README = """\
# Supplementary material

This archive lets reviewers check every number, table and figure in the paper.

- `paper/tmlr/`: LaTeX sources, the official TMLR style files, the generated
  tables and figures, and `build_assets.py`, which regenerates them and checks
  every number quoted in the text (`claims.json`) against the analysis outputs.
- `reports/`: the analysis outputs the paper reads. The held-scene recognition
  result is compressed; decompress it before running the check.
- `studies/`: the pre-collection protocols and the plan of the post-result diagnostics.
- `data/manifests/.../measurements.jsonl`: the 31 standardized-input features of
  every generated and reference image; `requests.jsonl`: the exact prompts and
  request payloads. `reports/painter_learned_audit_v1/embeddings_*.npz` hold the
  CLIP and CSD embeddings, with row identities in `extraction_*.json`.

To verify (Python 3.11 or later with numpy and matplotlib):

    gunzip -k reports/painter_prototype_transfer_v1/analysis.json.gz
    python paper/tmlr/build_assets.py --check

The check verifies the SHA-256 of each input, regenerates all tables and figures
byte for byte (the figure requires the recorded matplotlib version for exact
bytes) and confirms every quoted number. Generated and reference images are not
included because of the size limit and artwork licensing.
"""


def members() -> list[tuple[str, bytes]]:
    files = [
        p
        for p in sorted(HERE.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"
    ]
    out = [(str(p.relative_to(ROOT)), p.read_bytes()) for p in files]
    out += [(rel, (ROOT / rel).read_bytes()) for rel in EVIDENCE]
    out.append(("README.md", README.encode()))
    return sorted(out)


def scan(name: str, content: bytes) -> list[str]:
    if name.endswith((".npz", ".gz", ".pdf")):
        return []
    text = content.decode("utf-8", errors="replace")
    return [f"{name}: {m.group(0)!r}" for m in IDENTIFYING.finditer(text)]


def main() -> int:
    entries = members()
    problems = [hit for name, content in entries for hit in scan(name, content)]
    if name := next((n for n, _ in entries if n.endswith("make_supplement.py")), None):
        problems = [p for p in problems if not p.startswith(name)]
    if problems:
        print("identifying strings found:\n" + "\n".join(problems), file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in entries:
            info = zipfile.ZipInfo(name, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)
    size = OUTPUT.stat().st_size
    if size > LIMIT:
        print(f"archive is {size / 2**20:.1f} MiB, above the 100 MB limit", file=sys.stderr)
        return 1
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {len(entries)} files, {size / 2**20:.1f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
