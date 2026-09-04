"""The Protocol 2.1 §7.4 content lexicon: metadata-declared outdoor-place eligibility.

Protocol 2.1 declares content eligibility from authority and discovery metadata with a frozen
lexicon instead of human coding. This module is the single source of the three lists (positive
outdoor-place tokens, exclusion tokens, override phrases), renders them into the exact JSON
artifact that R2 binds by hash, and implements the fixed-order disposition rule of §7.4:

1. any override phrase → ``eligible_outdoor_place``;
2. else any exclusion token → ``ineligible_by_exclusion``;
3. else any positive token → ``eligible_outdoor_place``;
4. else ``unresolved_by_metadata``.

Tokens match as whole words after NFKD accent stripping and case folding. The scene-type lists
are kept separately only so that the generated-side prompt scene types and the non-binding
pre-screen can report which class of token matched; they play no role in eligibility.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from latent_art_bench.io import hash_file, stable_hash, write_json
from latent_art_bench.painter_feature_generation_v1 import artifact_cli

OUTPUT_PATH = Path("data/manifests/painter_feature_generation_v1/content_lexicon.json")
SCHEMA_VERSION = "painter-feature-generation-v1-content-lexicon/1.0"
PROTOCOL_ID = "painter-feature-generation-v1/2.1"

OVERRIDE_PHRASES = (
    "water lily",
    "water lilies",
    "water-lily",
    "water-lilies",
    "nympheas",
)
EXCLUSION_TOKENS = (
    "portrait",
    "self-portrait",
    "autoportrait",
    "still life",
    "nature morte",
    "apples",
    "pommes",
    "fruit",
    "fruits",
    "flowers",
    "fleurs",
    "vase",
    "bouquet",
    "bather",
    "bathers",
    "baigneur",
    "baigneurs",
    "baigneuse",
    "baigneuses",
    "card players",
    "joueurs de cartes",
    "nude",
    "nu",
    "woman",
    "women",
    "femme",
    "femmes",
    "man",
    "homme",
    "boy",
    "garcon",
    "girl",
    "fille",
    "child",
    "children",
    "enfant",
    "enfants",
    "madame",
    "mme",
    "monsieur",
    "interior",
    "interieur",
    "skull",
    "crane",
    "pipe",
    "reading",
    "lecture",
    "table",
    "bottle",
    "bouteille",
    "luncheon",
    "dejeuner",
    "hortense",
    "peasant",
    "peasants",
    "paysan",
    "paysanne",
    "paysans",
    "servant",
    "shepherd",
    "shepherdess",
    "bergere",
    "harlequin",
    "arlequin",
    "pierrot",
    "onions",
    "oignons",
    "jug",
    "cruche",
    "sugar bowl",
    "sucrier",
    "tulips",
    "dahlias",
    "chrysanthemums",
    "roses",
    "peonies",
    "pivoines",
    "sunflowers",
    "lady",
    "head",
    "tete",
    "mother",
    "mere",
    "seated",
    "assis",
    "assise",
    "smoker",
    "fumeur",
    "gardener",
    "jardinier",
    "washerwoman",
    "laundress",
    "lavandiere",
    "market",
    "marche",
    "figure",
    "figures",
    "dancer",
    "danseuse",
    "cook",
    "cuisiniere",
    "the artist's son",
    "the artist's father",
    "the artist's wife",
    "camille monet",
    "jean monet",
)
WATER_TOKENS = (
    "river",
    "riverbank",
    "riverside",
    "riviere",
    "fleuve",
    "seine",
    "loing",
    "marne",
    "oise",
    "epte",
    "creuse",
    "thames",
    "tamise",
    "sea",
    "seascape",
    "marine",
    "coast",
    "coastal",
    "cote",
    "beach",
    "plage",
    "cliff",
    "cliffs",
    "falaise",
    "falaises",
    "harbour",
    "harbor",
    "port",
    "bay",
    "baie",
    "gulf",
    "golfe",
    "lake",
    "lac",
    "pond",
    "etang",
    "canal",
    "quay",
    "quai",
    "flood",
    "floods",
    "inondation",
    "boat",
    "boats",
    "barque",
    "barques",
    "bateau",
    "bateaux",
    "regatta",
    "regattas",
    "regate",
    "regates",
    "bridge",
    "pont",
    "bords",
    "bord de l'eau",
    "berge",
    "rive",
    "estaque",
    "shore",
    "waterside",
    "sailboat",
    "sailboats",
    "fishing",
    "tide",
    "maree",
    "waves",
    "vagues",
    "rocks",
    "rochers",
    "belle-ile",
    "etretat",
    "pourville",
    "varengeville",
    "fecamp",
    "dieppe",
    "honfleur",
    "trouville",
    "sainte-adresse",
    "le havre",
    "antibes",
    "bordighera",
    "zaandam",
    "venice",
    "venise",
    "waterloo bridge",
    "charing cross",
    "annecy",
    "vetheuil",
)
BUILT_TOKENS = (
    "street",
    "streets",
    "rue",
    "boulevard",
    "town",
    "village",
    "city",
    "ville",
    "houses",
    "house",
    "maison",
    "maisons",
    "church",
    "eglise",
    "cathedral",
    "cathedrale",
    "square",
    "place",
    "town hall",
    "mill",
    "moulin",
    "factory",
    "usine",
    "station",
    "gare",
    "palazzo",
    "palace",
    "palais",
    "parliament",
    "westminster",
    "farm",
    "farmhouse",
    "ferme",
    "cottage",
    "cottages",
    "chalet",
    "roofs",
    "toits",
    "montmartre",
    "hameau",
    "hamlet",
    "castle",
    "chateau",
    "abbey",
    "abbaye",
    "tower",
    "tour",
    "dock",
    "docks",
    "gardanne",
    "auvers",
    "pontoise",
    "louveciennes",
    "moret",
    "marly",
    "bougival",
    "argenteuil",
    "giverny",
    "eragny",
    "rouen",
    "paris",
    "london",
    "londres",
    "amsterdam",
    "chatou",
)
ROUTE_TOKENS = (
    "road",
    "roads",
    "route",
    "path",
    "paths",
    "chemin",
    "lane",
    "allee",
    "alley",
    "track",
    "sentier",
    "avenue",
    "entrance to the village",
    "entree du village",
    "turn in the road",
    "route tournante",
    "railway",
    "railroad",
    "chemin de fer",
    "train",
)
LAND_TOKENS = (
    "field",
    "fields",
    "champ",
    "champs",
    "meadow",
    "meadows",
    "prairie",
    "wheat",
    "ble",
    "hay",
    "haystack",
    "haystacks",
    "grainstack",
    "grainstacks",
    "wheatstack",
    "wheatstacks",
    "stack of wheat",
    "stacks of wheat",
    "meule",
    "meules",
    "orchard",
    "orchards",
    "verger",
    "garden",
    "gardens",
    "jardin",
    "poplar",
    "poplars",
    "peupliers",
    "tree",
    "trees",
    "arbre",
    "arbres",
    "forest",
    "foret",
    "wood",
    "woods",
    "bois",
    "hill",
    "hills",
    "hillside",
    "colline",
    "collines",
    "mountain",
    "mountains",
    "montagne",
    "mont",
    "sainte-victoire",
    "valley",
    "vallee",
    "plain",
    "plaine",
    "snow",
    "neige",
    "landscape",
    "paysage",
    "countryside",
    "campagne",
    "pasture",
    "paturage",
    "vineyard",
    "vigne",
    "chestnut",
    "chestnuts",
    "pine",
    "pines",
    "pin",
    "pins",
    "olive",
    "oliviers",
    "cypress",
    "quarry",
    "carriere",
    "jas de bouffan",
    "chateau noir",
    "bibemus",
    "park",
    "parc",
    "spring",
    "autumn",
    "winter",
    "summer",
    "printemps",
    "automne",
    "hiver",
    "ete",
    "frost",
    "gelee",
    "harvest",
    "moisson",
    "haymaking",
    "fenaison",
    "sunset",
    "sunrise",
    "morning",
    "evening",
    "effect",
    "effet",
    "grove",
    "clearing",
    "clairiere",
    "hedge",
    "haie",
    "cliff-top",
    "plateau",
    "sky",
    "clouds",
)
POSITIVE_CLASSES = {
    "water_organized": WATER_TOKENS,
    "route_organized": ROUTE_TOKENS,
    "built_place_organized": BUILT_TOKENS,
    "open_or_wooded_land": LAND_TOKENS,
}
CLASS_PRIORITY = tuple(POSITIVE_CLASSES)
ELIGIBLE = "eligible_outdoor_place"
INELIGIBLE = "ineligible_by_exclusion"
UNRESOLVED = "unresolved_by_metadata"


_PUNCTUATION_MAP = str.maketrans(
    {
        "\u2018": "'",  # left single quotation mark
        "\u2019": "'",  # right single quotation mark (typographic apostrophe)
        "\u02bc": "'",  # modifier letter apostrophe
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
    }
)


def fold(value: str) -> str:
    """Normalize metadata text for matching.

    Typographic apostrophes and dashes are mapped to their ASCII forms first, because NFKD does
    not decompose them and the lexicon phrases are written with ASCII punctuation; then
    combining marks are stripped and the result is case-folded.
    """
    decomposed = unicodedata.normalize("NFKD", value.translate(_PUNCTUATION_MAP))
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).casefold()


def _pattern(words: Iterable[str]) -> "re.Pattern[str]":
    alternatives = "|".join(re.escape(fold(word)) for word in words)
    return re.compile(rf"(?<![a-z])(?:{alternatives})(?![a-z])")


OVERRIDE_RE = _pattern(OVERRIDE_PHRASES)
EXCLUSION_RE = _pattern(EXCLUSION_TOKENS)
CLASS_RE = {name: _pattern(tokens) for name, tokens in POSITIVE_CLASSES.items()}


def classify(text: str) -> Dict[str, Any]:
    """Apply the §7.4 rule to one metadata string.

    Returns the disposition, the first positive class in priority order (for diagnostics), and
    every class that matched (overlapping), plus the matched override/exclusion tokens.
    """
    folded = fold(text)
    override = [m.group(0) for m in OVERRIDE_RE.finditer(folded)]
    exclusions = [m.group(0) for m in EXCLUSION_RE.finditer(folded)]
    classes = {name: bool(regex.search(folded)) for name, regex in CLASS_RE.items()}
    primary = next((name for name in CLASS_PRIORITY if classes[name]), None)
    if override:
        disposition = ELIGIBLE
        primary = primary or "water_organized"
    elif exclusions:
        disposition = INELIGIBLE
    elif primary is not None:
        disposition = ELIGIBLE
    else:
        disposition = UNRESOLVED
    return {
        "disposition": disposition,
        "primary_class": primary if disposition == ELIGIBLE else None,
        "class_matches": classes,
        "override_matches": override,
        "exclusion_matches": exclusions,
    }


def render() -> Dict[str, Any]:
    lists = {
        "override_phrases": list(OVERRIDE_PHRASES),
        "exclusion_tokens": list(EXCLUSION_TOKENS),
        "positive_tokens_by_class": {
            name: list(tokens) for name, tokens in POSITIVE_CLASSES.items()
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "status": "rendered_not_yet_reviewed_or_frozen_for_r2",
        "matching": (
            "whole-word match after mapping typographic apostrophes and dashes to ASCII, "
            "Unicode NFKD accent stripping, and case folding, over the concatenation of "
            "authority title, object-type/classification, genre/subject/keyword fields, "
            "description, discovery label and description, and provider caption"
        ),
        "disposition_order": [
            f"override phrase -> {ELIGIBLE}",
            f"exclusion token -> {INELIGIBLE}",
            f"positive token -> {ELIGIBLE}",
            f"no match -> {UNRESOLVED}",
        ],
        "class_priority_for_diagnostics": list(CLASS_PRIORITY),
        "counts": {
            "override_phrases": len(OVERRIDE_PHRASES),
            "exclusion_tokens": len(EXCLUSION_TOKENS),
            "positive_tokens": sum(len(t) for t in POSITIVE_CLASSES.values()),
        },
        "lists": lists,
        "lists_sha256": stable_hash(lists),
    }


def serialize(lexicon: Dict[str, Any]) -> str:
    return json.dumps(lexicon, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def expected(root: Path) -> Mapping[Path, str]:
    return {OUTPUT_PATH: serialize(render())}


def write(root: Path) -> Dict[str, Any]:
    lexicon = render()
    target = root / OUTPUT_PATH
    write_json(target, lexicon)
    return {
        "output_path": str(OUTPUT_PATH),
        "output_sha256": hash_file(target),
        "lists_sha256": lexicon["lists_sha256"],
        **lexicon["counts"],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    return artifact_cli.run(__doc__.splitlines()[0], expected, write, argv)


__all__: List[str] = [
    "classify",
    "render",
    "write",
    "main",
    "fold",
    "ELIGIBLE",
    "INELIGIBLE",
    "UNRESOLVED",
    "CLASS_PRIORITY",
]
