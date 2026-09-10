"""Prospective text-only treatments built from the unchanged 16-scene prompt census."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

from latent_art_bench.io import stable_hash
from latent_art_bench.painter_feature_generation_v1 import prompt_library
from latent_art_bench.painter_feature_generation_v1.panel import ID_NAME_PAIRS, PAINTER_IDS

SOURCE_PATH = prompt_library.OUTPUT_PATH
METHOD_IDS = ("by_name", "style_instruction", "style_aspects")
CONDITIONS = (*PAINTER_IDS, "artist_free")
TEMPLATE_IDS = tuple(f"{prefix}{index}" for prefix in "WBRL" for index in range(1, 5))
STYLE_NAMED = " Render this scene in the painting style of {painter_name}."
STYLE_FREE = " Render this scene in a coherent painting style."
ASPECT_INSTRUCTION = (
    " Attend to color relationships, the organization of forms, and the handling of painted"
    " marks; retain the stated scene."
)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_source(source: dict) -> None:
    """Reject malformed, reordered, or internally changed baseline strings."""
    if source["schema_version"] != prompt_library.SCHEMA_VERSION:
        raise ValueError("unsupported baseline prompt library schema")
    if source["painters"] != [dict(painter_id=p, painter_name=n) for p, n in ID_NAME_PAIRS]:
        raise ValueError("baseline painter identities or names changed")
    templates = source["templates"]
    if tuple(row["template_id"] for row in templates) != TEMPLATE_IDS:
        raise ValueError("baseline must retain all 16 templates in their original order")
    all_strings = []
    for index, row in enumerate(templates):
        if row["scene_group"] != prompt_library.SCENE_GROUPS[index // 4]:
            raise ValueError("baseline template scene group changed")
        free = row["artist_free_prompt"]
        if (
            not free.startswith(prompt_library.INSERTION_ANCHOR + " of ")
            or not free.endswith(".")
            or unicodedata.normalize("NFC", free) != free
            or _sha256(free) != row["artist_free_sha256"]
        ):
            raise ValueError("invalid baseline artist-free prompt or hash")
        if set(row["named_prompts"]) != set(PAINTER_IDS):
            raise ValueError("baseline must retain all four named painter conditions")
        all_strings.append(free)
        for painter_id, painter_name in ID_NAME_PAIRS:
            named = row["named_prompts"][painter_id]
            if (
                named["prompt"] != prompt_library.named_prompt(free, painter_name)
                or _sha256(named["prompt"]) != named["sha256"]
            ):
                raise ValueError("baseline named prompt insertion or hash changed")
            all_strings.append(named["prompt"])
    if stable_hash(all_strings) != source["strings_sha256"]:
        raise ValueError("baseline complete prompt-string hash mismatch")


def build_library(root: Path) -> dict:
    """Return all 240 literal positive prompts; write nothing and contact no provider."""
    source_bytes = (root / SOURCE_PATH).read_bytes()
    source = json.loads(source_bytes)
    try:
        _validate_source(source)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("malformed baseline prompt library") from exc
    names = dict(ID_NAME_PAIRS)
    records = []
    for method_id in METHOD_IDS:
        for template in source["templates"]:
            for condition in CONDITIONS:
                free = template["artist_free_prompt"]
                if method_id == "by_name":
                    prompt = (free if condition == "artist_free"
                              else template["named_prompts"][condition]["prompt"])
                else:
                    suffix = (STYLE_FREE if condition == "artist_free"
                              else STYLE_NAMED.format(painter_name=names[condition]))
                    prompt = free + suffix
                    if method_id == "style_aspects":
                        prompt += ASPECT_INSTRUCTION
                records.append(dict(
                    method_id=method_id, condition=condition,
                    template_id=template["template_id"], scene_group=template["scene_group"],
                    prompt=prompt, prompt_sha256=_sha256(prompt),
                ))
    return dict(
        schema_version="painter-prompt-study-prompt-library/1.0",
        source=dict(path=SOURCE_PATH.as_posix(),
                    sha256=hashlib.sha256(source_bytes).hexdigest(),
                    strings_sha256=source["strings_sha256"]),
        method_ids=list(METHOD_IDS), conditions=list(CONDITIONS),
        methods=[
            dict(
                method_id="by_name", label="Original by-name prompt",
                construction="Use the baseline named or artist-free prompt verbatim.",
                control_rationale="The original artist-free condition omits only the painter-name "
                "insertion, retaining the same medium and scene.",
            ),
            dict(
                method_id="style_instruction", label="Explicit style instruction",
                construction="Append STYLE_NAMED or STYLE_FREE to the complete unchanged "
                "artist-free scene sentence.",
                named_suffix=STYLE_NAMED, artist_free_suffix=STYLE_FREE,
                control_rationale="Both conditions explicitly request a painting style; only "
                "the named condition requests a particular painter. This control measures the "
                "generic instruction effect separately from painter-directed movement.",
            ),
            dict(
                method_id="style_aspects", label="Style instruction with broad visual aspects",
                construction="Append the exact shared ASPECT_INSTRUCTION to style_instruction "
                "under both the named and artist-free conditions.",
                named_suffix=STYLE_NAMED + ASPECT_INSTRUCTION,
                artist_free_suffix=STYLE_FREE + ASPECT_INSTRUCTION,
                control_rationale="The additional aspect instruction is identical for named "
                "and artist-free prompts, so its generic effect has a matched control. It "
                "specifies no artist-dependent palette, motif, numeric target, or feature value.",
            ),
        ],
        prompts=records,
        counts=dict(methods=3, conditions_per_method=5, distinct_condition_cells=15,
                    templates=16, prompts_per_block_per_service=240, total_strings=240),
        strings_sha256=stable_hash([row["prompt"] for row in records]),
        exposure_disclosure="The painters, original prompt census, 31-feature method, and earlier "
        "generated/reference numeric results were already exposed before this study. The new "
        "wording is a prospectively fixed text intervention for new generation draws against an "
        "already exposed reference population, not an unexposed confirmation design. No new "
        "outputs or artist-specific measured feature targets enter prompt construction.",
        construction_scope="All original scene sentences remain unchanged. No reference images, "
        "artist-specific visual descriptors, measured feature targets, new subject objects, "
        "scene selection, or adaptive prompt optimization are used. Negative prompts and render "
        "settings are separate frozen transport fields and are never appended here.",
    )
