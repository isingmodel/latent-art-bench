"""Build the Korean tables of the TMLR manuscript and check the translation's numbers.

Run ``uv run --locked python paper/tmlr_ko/build_korean.py`` to write
``paper/tmlr_ko/generated/``: each table of ``paper/tmlr/generated/`` with the Korean
caption and the Korean header and row labels of ``tables_ko.json``; numbers are copied
unchanged. ``--check`` writes nothing and verifies that the Korean tables are current.

Both modes also compare the numbers in the Korean prose (``main.tex``, ``appendix.tex``
and the captions) with the English manuscript. Every number must occur equally often,
apart from the differences listed in ``EXPECTED``, which arise where one language
writes a number as a word.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGLISH = HERE.parent / "tmlr"
SOURCE = ENGLISH / "generated"
OUT = HERE / "generated"

TERMS = json.loads((HERE / "tables_ko.json").read_text())
CAPTIONS, CELLS, KEEP = TERMS["captions"], TERMS["cells"], set(TERMS["keep"])

# Korean count minus English count for numbers that one language writes as a word:
# "zero" (0), "Fourteen" (14), "two of the 15" (2), "second difference" (2), dates (9, 10),
# fractions such as "a quarter" (4분의 1), and one sentence that names the level 1 twice.
EXPECTED = {
    "main.tex": {"0": 6, "1": 6, "10": 1, "14": 1, "2": 1, "3": 1, "4": 3, "5": 1, "9": 1},
    "appendix.tex": {"0": 5, "1": 1, "2": 1, "3": 1, "9": 2},
}

CAPTION = re.compile(r"\\caption\{(.*)\}\n\\label\{(.*?)\}", re.S)
MULTI = re.compile(r"(\\multicolumn\{\d+\}\{(?:[^{}]|\{\})*\}\{)(.*)(\})$")
NUMBER = re.compile(r"(?<![A-Za-z\\_^\d.,])(?<!_\{)(?<!\^\{)\d+(?:,\d{3})*(?:\.\d+)?")


def translate_cell(cell: str, problems: list[str], name: str, scene: bool) -> str:
    core = cell.strip()
    if not core:
        return cell
    multi = MULTI.match(core)
    inner = multi.group(2) if multi else core
    if inner in CELLS:
        new = CELLS[inner]
    else:
        text = re.sub(r"\\[A-Za-z]+|\$[^$]*\$", "", inner)
        if re.search(r"[A-Za-z]{2,}", text) and inner not in KEEP and not scene:
            problems.append(f"{name}: untranslated cell {inner!r}")
        return cell
    replaced = f"{multi.group(1)}{new}{multi.group(3)}" if multi else new
    return cell.replace(core, replaced)


def translate_table(name: str, text: str, problems: list[str]) -> str:
    match = CAPTION.search(text)
    if not match or match.group(2) not in CAPTIONS:
        problems.append(f"{name}: no Korean caption for {match.group(2) if match else '?'}")
        return text
    english, label = match.group(1), match.group(2)
    korean = CAPTIONS[label]
    if numbers(english) != numbers(korean):
        diff = (numbers(english) - numbers(korean)) + (numbers(korean) - numbers(english))
        problems.append(f"{name}: caption numbers differ: {dict(diff)}")
    text = text[: match.start(1)] + korean + text[match.end(1) :]
    start, end = text.index("\\toprule"), text.index("\\bottomrule")
    lines = []
    for line in text[start:end].split("\n"):
        if "&" not in line and "\\multicolumn" not in line:
            lines.append(line)
            continue
        tail = "\\\\" if line.rstrip().endswith("\\\\") else ""
        body = line.rstrip()[: -2 if tail else None]
        cells = body.split("&")
        scene = name == "tab_scenes.tex" and len(cells) == 3
        cells = [translate_cell(c, problems, name, scene and i == 2) for i, c in enumerate(cells)]
        lines.append("&".join(cells) + tail)
    header = "% 한국어판: paper/tmlr_ko/build_korean.py 가 생성한다. 직접 고치지 않는다.\n"
    return header + text[:start] + "\n".join(lines) + text[end:]


def prose(text: str) -> str:
    text = text.split("\\begin{document}")[-1]
    text = re.sub(r"(?m)^%.*$", "", text)
    text = re.sub(
        r"\\(?:ref|label|cite[tp]?|input|includegraphics(?:\[[^\]]*\])?)\{[^}]*\}", "", text
    )
    return text


def numbers(text: str) -> Counter:
    return Counter(NUMBER.findall(prose(text)))


def check_prose(problems: list[str]) -> None:
    for name in ("main.tex", "appendix.tex"):
        english = numbers((ENGLISH / name).read_text())
        korean = numbers((HERE / name).read_text())
        diff = {
            token: korean[token] - english[token]
            for token in sorted(set(english) | set(korean))
            if korean[token] != english[token]
        }
        if diff != EXPECTED[name]:
            unexpected = {k: v for k, v in diff.items() if EXPECTED[name].get(k) != v} | {
                k: 0 for k in EXPECTED[name] if k not in diff
            }
            problems.append(f"{name}: numbers differ from the English manuscript: {unexpected}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    problems: list[str] = []
    outputs = {
        path.name: translate_table(path.name, path.read_text(), problems)
        for path in sorted(SOURCE.glob("tab_*.tex"))
    }
    check_prose(problems)
    if args.check:
        present = {p.name for p in OUT.glob("*")} if OUT.exists() else set()
        for extra in sorted(present - set(outputs)):
            problems.append(f"unexpected Korean table: {extra}")
        for name, content in outputs.items():
            path = OUT / name
            if not path.exists() or path.read_text() != content:
                problems.append(f"Korean table is not current: {name}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    if args.check:
        print(f"ok: {len(outputs)} Korean tables and the numbers of the Korean text")
        return 0
    OUT.mkdir(exist_ok=True)
    for stale in OUT.iterdir():
        if stale.name not in outputs:
            stale.unlink()
    for name, content in outputs.items():
        (OUT / name).write_text(content)
    print(f"wrote {len(outputs)} Korean tables to {OUT.relative_to(HERE.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
