"""R1 determination: seven gates, in order, first failure wins.

This is the whole judge. A recorded census says what a provider returned; this module says
which of those records are works this study may admit. It reads metadata only, requests
nothing, downloads nothing, and assigns no role.

The rule is Protocol 2.3 Sections 2 and 3, plus the two gates 2.3 leaves standing in 2.1
(Section 7.3 geometry, Section 7.4 content lexicon), expressed as an ordered tuple of
predicates over one item:

    creator -> painting -> medium -> collection -> rights -> geometry -> content

An item is admitted when every gate passes. When one fails, the determination names that gate
and stops; later gates are not evaluated and no partial credit is recorded. There is no score,
no confidence, and no reviewable middle state, because a middle state is exactly the room in
which a corpus gets chosen after its numbers are known.

One item may carry several Commons files. The rights and geometry gates ask whether **any**
file qualifies, and the largest qualifying file is recorded as the surrogate to fetch later.
Content eligibility is decided from the Wikidata label alone, never from a file-level string,
so that which file wins cannot move the content decision.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

from latent_art_bench.io import hash_file, write_json, write_jsonl
from latent_art_bench.painter_feature_generation_v1 import content_lexicon
from latent_art_bench.painter_feature_generation_v1.panel import PAINTERS

PROTOCOL_ID = "painter-feature-generation-v1/2.3"
PROTOCOL_PATH = "studies/painter_feature_generation_v1/PROTOCOL_2.3.md"
LEXICON_PATH = "data/manifests/painter_feature_generation_v1/content_lexicon.json"
DETERMINER_PATH = "src/latent_art_bench/painter_feature_generation_v1/determine.py"
DETERMINATION_SCHEMA = "painter-feature-generation-v1-determination/2.3"
RECEIPT_SCHEMA = "painter-feature-generation-v1-determination-receipt/2.3"

PAINTING = "Q3305213"
OIL_PAINT = "Q296955"
CANVAS = "Q12321255"
MINIMUM_SHORT_SIDE = 1024  # 2.1 Section 7.3

# 2.1 Section 9 floor, per painter. 100 sealed confirmation works are 60% of the primary panel
# under the Section 8.1 split, so the primary panel needs ceil(100 / 0.6) = 167 works, and the
# independent-capture auxiliary panel needs 12 more.
PRIMARY_PANEL_FLOOR = 167
AUXILIARY_PANEL_FLOOR = 12
ELIGIBILITY_FLOOR = PRIMARY_PANEL_FLOOR + AUXILIARY_PANEL_FLOOR

# 2.3 Section 3. A Commons file is admitted on the licence it actually carries. The Commons
# "Copyrighted" flag is not a rights gate: a CC BY-SA photograph of a public-domain painting is
# copyrighted and openly licensed at the same time, which describes every such file in the
# recorded census. A usage restriction template is a rights gate and excludes the file.
OPEN_LICENCE_PREFIXES = ("public domain", "cc0", "cc by", "no restrictions")
# A Creative Commons licence is open only without these terms. They must be matched as licence
# tokens, not as substrings: "CC BY-NC 4.0" also starts with "cc by".
CLOSED_LICENCE_TERMS = frozenset({"nc", "nd", "noncommercial", "noderivatives", "noderivs"})


class DeterminationError(RuntimeError):
    """Raised when an input the receipt must bind is missing under the given root."""


GATES: Tuple[str, ...] = (
    "creator",
    "painting",
    "medium",
    "collection",
    "rights",
    "geometry",
    "content",
)


@dataclass(frozen=True)
class File:
    """One Commons file offered as a surrogate for a work."""

    name: str
    licence: str
    restriction: str
    short_side: int
    url: str

    @property
    def open_rights(self) -> bool:
        """2.3 Section 3: an open marker, no restriction template, no NC or ND term."""
        licence = self.licence.strip().casefold()
        if self.restriction.strip() or not licence.startswith(OPEN_LICENCE_PREFIXES):
            return False
        return not CLOSED_LICENCE_TERMS.intersection(re.split(r"[^a-z0-9]+", licence))


@dataclass(frozen=True)
class Item:
    """One candidate work, reduced to exactly what the seven gates read."""

    painter_id: str
    painter_qid: str
    item_qid: str
    label: str
    claims: Mapping[str, Sequence[str]]
    files: Sequence[File]

    def values(self, prop: str) -> Tuple[str, ...]:
        return tuple(self.claims.get(prop, ()))


@dataclass(frozen=True)
class Decision:
    admitted: bool
    failed_gate: Optional[str]
    file: Optional[File]
    content_class: Optional[str]

    def row(self, item: Item) -> Dict[str, Any]:
        return {
            "schema_version": DETERMINATION_SCHEMA,
            "protocol_id": PROTOCOL_ID,
            "painter_id": item.painter_id,
            "item_qid": item.item_qid,
            "label": item.label,
            "admitted": self.admitted,
            "failed_gate": self.failed_gate,
            "content_class": self.content_class,
            "surrogate": None
            if self.file is None
            else {
                "commons_filename": self.file.name,
                "licence": self.file.licence,
                "short_side": self.file.short_side,
                "url": self.file.url,
            },
        }


def decide(item: Item) -> Decision:
    """Run the seven gates in order and return at the first failure."""
    if item.values("P170") != (item.painter_qid,):
        return Decision(False, "creator", None, None)
    if PAINTING not in item.values("P31"):
        return Decision(False, "painting", None, None)
    if not {OIL_PAINT, CANVAS} <= set(item.values("P186")):
        return Decision(False, "medium", None, None)
    if not item.values("P195"):
        return Decision(False, "collection", None, None)
    licensed = [f for f in item.files if f.open_rights]
    if not licensed:
        return Decision(False, "rights", None, None)
    large = [f for f in licensed if f.short_side >= MINIMUM_SHORT_SIDE]
    if not large:
        return Decision(False, "geometry", None, None)
    surrogate = max(large, key=lambda f: (f.short_side, f.name))
    verdict = content_lexicon.classify(item.label)
    if verdict["disposition"] != content_lexicon.ELIGIBLE:
        return Decision(False, "content", surrogate, None)
    return Decision(True, None, surrogate, verdict["primary_class"])


def read_items(path: Path) -> Iterator[Item]:
    """Adapt a recorded federated-candidate census into items. The only schema-aware code here.

    Rows sharing an item QID are one item with several files. Best-rank claims are flattened to
    plain value tuples, since no gate reads a rank or a qualifier.
    """
    qids = {p.painter_id: p.wikidata_qid for p in PAINTERS}
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    order: List[str] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            key = row["item_qid"]
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(row)
    for key in order:
        rows = grouped[key]
        entity = rows[0].get("entity") or {}
        claims = entity.get("best_rank_claims") or {}
        files = []
        for row in rows:
            media = row.get("media") or {}
            name = media.get("canonical_title") or row.get("commons_filename") or ""
            if not name:
                continue
            files.append(
                File(
                    name=str(name),
                    licence=str(media.get("license_short_name") or ""),
                    restriction=str(media.get("restrictions") or ""),
                    short_side=int(media.get("original_short_side") or 0),
                    url=str(media.get("original_url") or ""),
                )
            )
        yield Item(
            painter_id=rows[0]["painter_id"],
            painter_qid=qids[rows[0]["painter_id"]],
            item_qid=str(key),
            label=str(entity.get("label") or ""),
            claims={
                prop: tuple(str(claim["value"]) for claim in statements)
                for prop, statements in claims.items()
            },
            files=tuple(files),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(
    root: Path, census_path: Path, determination_id: str, out_dir: Optional[Path] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Determine one census. Writes the determination and its receipt when ``out_dir`` is given.

    Every input that can change the answer is bound by SHA-256 in the receipt: the census, the
    protocol that states the rules, the frozen content lexicon, and this module's own source. A
    later reader can re-run the determination from those files and get the same rows.
    """
    root = root.resolve()
    rows: List[Dict[str, Any]] = []
    discovered: Counter = Counter()
    # How many gates each item cleared: its failed gate's position, or all of them when admitted.
    cleared: Dict[str, Counter] = {p.painter_id: Counter() for p in PAINTERS}
    for item in read_items(census_path):
        decision = decide(item)
        rows.append(decision.row(item))
        discovered[item.painter_id] += 1
        depth = len(GATES) if decision.admitted else GATES.index(decision.failed_gate or "")
        cleared[item.painter_id][depth] += 1

    painters = [p.painter_id for p in PAINTERS]
    funnel: Dict[str, Dict[str, int]] = {"discovered": {p: discovered[p] for p in painters}}
    for index, gate in enumerate(GATES):
        funnel[f"passed_{gate}"] = {
            p: sum(n for depth, n in cleared[p].items() if depth > index) for p in painters
        }
    admitted = funnel[f"passed_{GATES[-1]}"]

    determination_path = None
    if out_dir is not None:
        determination_path = (root / out_dir / f"{determination_id}_determination.jsonl").resolve()
        write_jsonl(determination_path, rows)

    receipt: Dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "determination_id": determination_id,
        "determined_at_utc": _utc_now(),
        "gate_order": list(GATES),
        "minimum_short_side": MINIMUM_SHORT_SIDE,
        "open_licence_prefixes": list(OPEN_LICENCE_PREFIXES),
        "closed_licence_terms": sorted(CLOSED_LICENCE_TERMS),
        "eligibility_floor": ELIGIBILITY_FLOOR,
        "items_determined": len(rows),
        "funnel": funnel,
        "admitted": dict(admitted),
        "margin_against_floor": {p: admitted[p] - ELIGIBILITY_FLOOR for p in painters},
        "clears_floor": {p: admitted[p] >= ELIGIBILITY_FLOOR for p in painters},
        "failed_gate_counts": dict(
            sorted(Counter(r["failed_gate"] for r in rows if not r["admitted"]).items())
        ),
        "note": (
            "Admission is metadata-declared eligibility under Protocol 2.3 Sections 2 and 3 with "
            "2.1 Sections 7.3 and 7.4. No image was requested, no pixel was read, and no role was "
            "assigned, so Protocol 2.2 Section 4's R1 freeze and authorization seal are not yet "
            "due; they remain required before the first image byte is fetched. Attribution, "
            "medium, support, and collection are Wikidata statements observed in the named census, "
            "not institutional catalogue records."
        ),
    }
    bound = {
        "census": census_path.resolve().relative_to(root),
        "protocol": Path(PROTOCOL_PATH),
        "content_lexicon": Path(LEXICON_PATH),
        "determiner": Path(DETERMINER_PATH),
    }
    if determination_path is not None:
        bound["determination"] = determination_path.relative_to(root)
    for name, relative in bound.items():
        if not (root / relative).is_file():
            raise DeterminationError(f"the {name} input is missing at {relative}")
        receipt[f"{name}_path"] = str(relative)
        receipt[f"{name}_sha256"] = hash_file(root / relative)
    if out_dir is not None:
        write_json(root / out_dir / f"{determination_id}_determination_receipt.json", receipt)
    return receipt, rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--census", type=Path, required=True)
    parser.add_argument("--determination-id", required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/manifests/painter_feature_generation_v1"),
        help="directory for the determination JSONL and its receipt",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    receipt, _rows = run(root, args.census.resolve(), args.determination_id, args.out)
    summary = {k: receipt[k] for k in ("funnel", "admitted", "margin_against_floor")}
    print(json.dumps(summary, indent=2))
    return 0 if all(receipt["clears_floor"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
