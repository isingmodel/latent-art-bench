"""Render the Protocol 2.1 prompt library into the exact UTF-8 JSON artifact §11.1 requires.

The 16 artist-free strings, the byte-exact painter-name insertion rule, the negative prompt,
and the render contract are read from ``PROTOCOL_2.1.md`` itself, so the artifact cannot drift
from the canonical text. The artifact is an R0 output (§15) and must be reviewed and hash-frozen
before the R2 eligibility rule is applied; rendering it is not that review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from latent_art_bench.io import canonical_json, hash_file

PROTOCOL_PATH = Path("studies/painter_feature_generation_v1/PROTOCOL_2.1.md")
OUTPUT_PATH = Path("data/manifests/painter_feature_generation_v1/prompt_library.json")
SCHEMA_VERSION = "painter-feature-generation-v1-prompt-library/1.0"
INSERTION_ANCHOR = "An oil painting on canvas"
INSERTION_TEMPLATE = " by {PAINTER}"
PAINTERS = (
    ("claude_monet", "Claude Monet"),
    ("alfred_sisley", "Alfred Sisley"),
    ("camille_pissarro", "Camille Pissarro"),
    ("paul_cezanne", "Paul Cézanne"),
)
SCENE_GROUPS = (
    "water_organized",
    "built_place_organized",
    "route_organized",
    "open_or_wooded_land",
)
_TEMPLATE_ROW = re.compile(
    r"^\| (?P<id>[WBRL][1-4]) \| `(?P<scene>[a-z_]+)` \| `(?P<prompt>[^`]+)` \|$", re.MULTILINE
)
_PROTOCOL_ID = re.compile(r"^Protocol ID: `([^`]+)`$", re.MULTILINE)
_NEGATIVE = re.compile(r"The exact negative prompt is\s*\n`([^`]+)`")
_RENDER = re.compile(r"one landscape output per request at exactly `(\d+)×(\d+)` pixels")


class PromptLibraryError(RuntimeError):
    """Raised when the protocol text does not yield the exact 16-template contract."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _nfc(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    if normalized != value:
        raise PromptLibraryError("protocol prompt text is not NFC-normalized")
    return normalized


def parse_protocol(text: str) -> Dict[str, Any]:
    protocol_id = _PROTOCOL_ID.search(text)
    negative = _NEGATIVE.search(text)
    render = _RENDER.search(text)
    if protocol_id is None or negative is None or render is None:
        raise PromptLibraryError("protocol lacks the ID, negative prompt, or render contract")
    rows = [match.groupdict() for match in _TEMPLATE_ROW.finditer(text)]
    if len(rows) != 16:
        raise PromptLibraryError(f"expected 16 template rows, found {len(rows)}")
    ids = [row["id"] for row in rows]
    if len(set(ids)) != 16:
        raise PromptLibraryError("template IDs are not unique")
    per_group = {group: [r for r in rows if r["scene"] == group] for group in SCENE_GROUPS}
    if any(len(group_rows) != 4 for group_rows in per_group.values()) or {
        row["scene"] for row in rows
    } != set(SCENE_GROUPS):
        raise PromptLibraryError("each of the four scene groups must have exactly four rows")
    for row in rows:
        prompt = _nfc(row["prompt"])
        if not prompt.startswith(INSERTION_ANCHOR + " "):
            raise PromptLibraryError(f"{row['id']} does not start with the insertion anchor")
        lowered = prompt.casefold()
        for _, name in PAINTERS:
            if name.casefold() in lowered or name.split()[-1].casefold() in lowered:
                raise PromptLibraryError(f"{row['id']} names a painter")
    return {
        "protocol_id": protocol_id.group(1),
        "negative_prompt": _nfc(negative.group(1)),
        "render": {"width": int(render.group(1)), "height": int(render.group(2))},
        "rows": rows,
    }


def named_prompt(artist_free: str, painter_name: str) -> str:
    insertion = INSERTION_TEMPLATE.replace("{PAINTER}", painter_name)
    return artist_free.replace(INSERTION_ANCHOR, INSERTION_ANCHOR + insertion, 1)


def render(root: Path, protocol_path: Path = PROTOCOL_PATH) -> Dict[str, Any]:
    protocol_file = root / protocol_path
    parsed = parse_protocol(protocol_file.read_text(encoding="utf-8"))
    templates: List[Dict[str, Any]] = []
    all_strings: List[str] = []
    for row in parsed["rows"]:
        artist_free = row["prompt"]
        named = {}
        for painter_id, painter_name in PAINTERS:
            prompt = named_prompt(artist_free, painter_name)
            named[painter_id] = {"prompt": prompt, "sha256": _sha256_text(prompt)}
        templates.append(
            {
                "template_id": row["id"],
                "scene_group": row["scene"],
                "artist_free_prompt": artist_free,
                "artist_free_sha256": _sha256_text(artist_free),
                "named_prompts": named,
            }
        )
        all_strings.append(artist_free)
        all_strings.extend(named[painter_id]["prompt"] for painter_id, _ in PAINTERS)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "rendered_from_protocol_not_yet_reviewed_or_sealed",
        "protocol_id": parsed["protocol_id"],
        "protocol_path": str(protocol_path),
        "protocol_sha256": hash_file(protocol_file),
        "encoding": "UTF-8, NFC; strings are byte-exact and must not be re-normalized or trimmed",
        "insertion_rule": {
            "anchor": INSERTION_ANCHOR,
            "inserted_bytes_template": INSERTION_TEMPLATE,
            "position": "immediately after the first occurrence of the anchor",
        },
        "painters": [
            {"painter_id": painter_id, "painter_name": _nfc(name)} for painter_id, name in PAINTERS
        ],
        "scene_groups": list(SCENE_GROUPS),
        "negative_prompt": {
            "text": parsed["negative_prompt"],
            "sha256": _sha256_text(parsed["negative_prompt"]),
            "unsupported_marker": "negative_prompt_not_supported",
            "rule": "used only when the frozen model exposes a negative-prompt field; never "
            "appended to the positive prompt",
        },
        "render_contract": {
            "width": parsed["render"]["width"],
            "height": parsed["render"]["height"],
            "orientation": "landscape",
            "outputs_per_request": 1,
            "post_generation_crop_or_upscale": False,
            "image_to_image_or_reference_input": False,
        },
        "selection_rule": (
            "no selection: every template is rendered under every condition; the prompt scene "
            "type is a generated-side diagnostic label only and nothing may rewrite, reorder, "
            "or choose among these strings"
        ),
        "templates": templates,
        "counts": {
            "templates": len(templates),
            "scene_groups": len(SCENE_GROUPS),
            "artist_free_strings": len(templates),
            "named_strings": len(templates) * len(PAINTERS),
            "total_strings": len(all_strings),
        },
        "strings_sha256": hashlib.sha256(canonical_json(all_strings).encode("utf-8")).hexdigest(),
    }


def serialize(library: Dict[str, Any]) -> str:
    return json.dumps(library, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write(root: Path, output_path: Path = OUTPUT_PATH) -> Dict[str, Any]:
    library = render(root)
    target = root / output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize(library), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "output_sha256": hash_file(target),
        "strings_sha256": library["strings_sha256"],
        "templates": library["counts"]["templates"],
        "total_strings": library["counts"]["total_strings"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the tracked artifact differs from a fresh render of the protocol",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    if args.check:
        expected = serialize(render(root))
        target = root / OUTPUT_PATH
        observed = target.read_text(encoding="utf-8") if target.is_file() else None
        print(json.dumps({"in_sync": observed == expected, "path": str(OUTPUT_PATH)}))
        return 0 if observed == expected else 1
    print(json.dumps(write(root), indent=2, sort_keys=True))
    return 0
