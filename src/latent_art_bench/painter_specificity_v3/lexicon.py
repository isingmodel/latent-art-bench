"""Content lexicon v3: every four-painter token, plus additions for the new painters' titles.

The disposition rule, matching and class priority are those of
``painter_feature_generation_v1.content_lexicon``. No original token is removed. The additions
were chosen from the discovered titles (metadata only) before any pixel was requested; they are
kept in separate lists so that the record shows exactly what changed.
"""

from __future__ import annotations

from typing import Any

from latent_art_bench.io import stable_hash
from latent_art_bench.painter_feature_generation_v1 import content_lexicon as v1

ELIGIBLE, INELIGIBLE, UNRESOLVED = v1.ELIGIBLE, v1.INELIGIBLE, v1.UNRESOLVED

# Figure, interior and nude titles that a new place or landscape word would otherwise admit.
ADDED_EXCLUSIONS: tuple[str, ...] = (
    "bedroom", "dormitory", "kitchen", "studio", "sala", "council", "sower", "stevedores",
    "nudes", "akt", "akte", "nackt", "nackte", "nackter", "madchen", "jungling", "dame",
    "rider", "dancers", "circus", "drinkers", "prisoners", "wife", "sons",
)
# Landscape words and the outdoor places named in the discovered titles (English, plus the
# German, Dutch and Italian words those titles use).
ADDED_POSITIVE: dict[str, tuple[str, ...]] = {
    "water_organized": (
        "waterfall", "falls", "cascade", "cascatelli", "rapids", "brook", "stream", "creek",
        "marsh", "marshes", "lagoon", "jetty", "seashore", "seas", "ships", "vessels", "pier",
        "sluice", "lock", "sound", "island", "iceberg", "icebergs", "pool", "watermill",
        "watermills", "strand", "bacino", "molo", "riva", "dogana", "bucintoro", "bucintore",
        "niagara", "zuiderzee", "amstel", "rhine", "rhone", "arno", "brenta", "hudson", "esopus",
        "narrows", "mississippi", "fehmarn", "farallon", "capri", "vaucluse", "oxbow",
    ),
    "route_organized": ("roadway", "underpass", "viaduct", "impasse"),
    "built_place_organized": (
        "piazza", "piazzetta", "campo", "san marco", "rialto", "capriccio", "caprice", "ruins",
        "colosseum", "arch", "portico", "porta", "monument", "fortress", "college", "cloister",
        "cemetery", "windmill", "temple", "parthenon", "villa", "burg", "suburb", "platz",
        "albertplatz", "schlossplatz", "strasse", "pfortensteg", "tram", "factories",
        "farmhouses", "parsonage", "vicarage", "courtyard", "terrace", "encampment", "yard",
        "venice", "padua", "dolo", "mestre", "haarlem", "alkmaar", "dresden", "berlin", "basel",
        "bern", "chemnitz", "arles", "asnieres", "clichy", "nuenen", "loosduinen", "gennep",
        "tarascon", "cordeville", "florence", "jerusalem", "paestum", "segesta", "narni",
        "stonehenge", "newport", "rutland", "rochester", "subiaco", "olevano", "tivoli",
    ),
    "open_or_wooded_land": (
        "wheatfield", "wheatfields", "cornfield", "grainfields", "cornshocks", "cypresses",
        "undergrowth", "ravine", "glen", "clove", "canyon", "gorge", "scenery", "wilderness",
        "backwoods", "woodland", "vistas", "dunes", "peak", "mount", "mounts", "mt", "volcano",
        "pass", "storm", "stormy", "rain", "thunderclouds", "twilight", "moonlight", "starry",
        "aurora", "tropics", "tropical", "redwoods", "oak", "beeches", "cedars", "firs", "spruce",
        "willows", "palms", "alps", "alpine", "stafelalp", "schiahorner", "davos", "norway",
        "alpilles", "alyscamps", "saintes-maries-de-la-mer", "brabant", "peiroulets",
        "catskill", "catskills", "kaaterskill", "yosemite", "yellowstone", "sierra", "sierras",
        "andes", "cotopaxi", "chimborazo", "pichincha", "cayambe", "tequendama", "rockies",
        "hetch hetchy", "platte", "matterhorn", "vesuvius", "laramie", "minnehaha",
        "multnomah", "ktaadn", "simmental", "genesee", "alaska", "california", "nevada",
        "vermont", "new england", "new hampshire", "massachusetts", "connecticut",
        "long island", "darien", "sherburne", "pompton",
    ),
}

OVERRIDE_PHRASES = v1.OVERRIDE_PHRASES
EXCLUSION_TOKENS = v1.EXCLUSION_TOKENS + ADDED_EXCLUSIONS
POSITIVE_CLASSES = {name: tokens + ADDED_POSITIVE[name]
                    for name, tokens in v1.POSITIVE_CLASSES.items()}
CLASS_PRIORITY = tuple(POSITIVE_CLASSES)
OVERRIDE_RE = v1._pattern(OVERRIDE_PHRASES)
EXCLUSION_RE = v1._pattern(EXCLUSION_TOKENS)
CLASS_RE = {name: v1._pattern(tokens) for name, tokens in POSITIVE_CLASSES.items()}


def classify(text: str) -> dict[str, Any]:
    """The four-painter rule: override, then exclusion, then positive class, else unresolved."""
    folded = v1.fold(text)
    override = [m.group(0) for m in OVERRIDE_RE.finditer(folded)]
    exclusions = [m.group(0) for m in EXCLUSION_RE.finditer(folded)]
    classes = {name: bool(regex.search(folded)) for name, regex in CLASS_RE.items()}
    primary = next((name for name in CLASS_PRIORITY if classes[name]), None)
    if override:
        disposition, primary = ELIGIBLE, primary or "water_organized"
    elif exclusions:
        disposition = INELIGIBLE
    elif primary is not None:
        disposition = ELIGIBLE
    else:
        disposition = UNRESOLVED
    return dict(disposition=disposition,
                primary_class=primary if disposition == ELIGIBLE else None,
                class_matches=classes, override_matches=override, exclusion_matches=exclusions)


def render() -> dict[str, Any]:
    additions = dict(exclusion_tokens=list(ADDED_EXCLUSIONS),
                     positive_tokens_by_class={k: list(v) for k, v in ADDED_POSITIVE.items()})
    lists = dict(override_phrases=list(OVERRIDE_PHRASES), exclusion_tokens=list(EXCLUSION_TOKENS),
                 positive_tokens_by_class={k: list(v) for k, v in POSITIVE_CLASSES.items()})
    return dict(
        schema_version="painter-specificity-v3-content-lexicon/1.0",
        base="painter_feature_generation_v1.content_lexicon (unchanged lists and rule)",
        additions=additions,
        additions_sha256=stable_hash(additions),
        lists=lists,
        lists_sha256=stable_hash(lists),
        counts=dict(exclusion_tokens=len(EXCLUSION_TOKENS),
                    positive_tokens=sum(len(t) for t in POSITIVE_CLASSES.values()),
                    added_exclusions=len(ADDED_EXCLUSIONS),
                    added_positive=sum(len(t) for t in ADDED_POSITIVE.values())),
    )
