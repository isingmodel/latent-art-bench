"""Check the ICML manuscript's local build and official style bindings.

This checks measurable format properties, not scientific acceptance or a
conference's external submission service. Requires Poppler CLI tools.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(*args):
    return subprocess.check_output(args, text=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "tmp/paper/icml-build")
    args = parser.parse_args()
    pdf = args.build_dir / "icml.pdf"
    log = (args.build_dir / "icml.log").read_text()
    aux = (args.build_dir / "icml.aux").read_text()
    provenance = json.loads((ROOT / "paper/icml_style/PROVENANCE.json").read_text())
    for name, sha in provenance["files"].items():
        require(digest(ROOT / "paper" / name) == sha, f"Official style changed: {name}")
    require("\\usepackage{icml2026}" in (ROOT / "paper/icml.tex").read_text(),
            "Expected anonymous ICML review mode")
    for path in sorted((ROOT / "paper").glob("icml*.tex")):
        name = path.name
        source = (ROOT / "paper" / name).read_text()
        require(not re.search(r"\\(?:geometry|fontsize|linespread)\b", source),
                f"Unexpected layout override in {name}")
    bad_log = ["Overfull", "undefined references", "multiply defined", "Font Warning",
               "AUTHORERR", "Title Suppressed", "margins have been altered"]
    for bad in bad_log:
        require(bad not in log, f"Unresolved build issue: {bad}")
    info = run("pdfinfo", str(pdf))
    page_count = int(re.search(r"^Pages:\s+(\d+)", info, re.M)[1])
    boxes = run("pdfinfo", "-f", "1", "-l", str(page_count), "-box", str(pdf))
    sizes = re.findall(r"Page\s+\d+ size:\s+([\d.]+) x ([\d.]+)", boxes)
    require(len(sizes) == page_count, "Could not check every page size")
    require(all(abs(float(w) - 612) < .01 and abs(float(h) - 792) < .01
                for w, h in sizes), "Expected US Letter on every page")
    pages = run("pdftotext", "-layout", str(pdf), "-").split("\f")
    require(len(pages) - 1 == page_count, "Text extraction page count differs")
    for bad in ["AUTHORERR", "Title Suppressed", "??", "isingmodel", "/Users/fred"]:
        require(not any(bad in p for p in pages), f"Visible placeholder or identity leak: {bad}")
    impact_page = next(i for i, p in enumerate(pages, 1) if "Impact Statement" in p)
    require(impact_page <= 9, f"Main body exceeds 8 pages: impact begins on {impact_page}")
    labels = dict(re.findall(r"\\newlabel\{([^}]+)\}\{\{[^}]*\}\{(\d+)\}", aux))
    main_source = (ROOT / "paper/icml_main.tex").read_text()
    main_source += (ROOT / "paper/icml_learned_table.tex").read_text()
    main_source += (ROOT / "paper/icml_transfer_table.tex").read_text()
    main_labels = re.findall(r"\\label\{([^}]+)\}", main_source) + ["sec:main-end"]
    require(all(label in labels for label in main_labels), "Missing main-text labels")
    last_main = max(int(labels[label]) for label in main_labels)
    require(last_main <= 8, f"A main-text float or label is on page {last_main}")
    fonts = run("pdffonts", str(pdf))
    require("NimbusRom" in fonts or "Times" in fonts, "Times-compatible body font missing")
    for line in fonts.splitlines()[2:]:
        require(re.search(r"\s+yes\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", line),
                f"Font is not embedded: {line}")
    require(pdf.stat().st_size < 50_000_000, "PDF exceeds ICML submission size limit")
    print(json.dumps({"format_checks": "passed", "main_pages": last_main,
                      "total_pages": page_count, "pdf_sha256": digest(pdf),
                      "scope": "local format checks; visual QA and scientific review separate"},
                     indent=2))


if __name__ == "__main__":
    main()
