"""Command-line entry point for the Painter Feature Generation v1 tooling.

Each subcommand is a thin pass-through to the module's own argument parser, so the CLI adds
no behaviour of its own. Census collectors are listed first, then the evidence and R0
artifact tools. The collectors are fail-closed and one-shot:
see `studies/painter_feature_generation_v1/PROTOCOL_2.1.md` for the stage gates that govern
when a census may be prepared, reviewed, authorized, and executed.
"""

from __future__ import annotations

from typing import Callable, List, Sequence

import typer

from latent_art_bench import evidence
from latent_art_bench.painter_feature_generation_v1 import (
    aic_metadata,
    aic_metadata_r2,
    broad_media_followup,
    broad_media_followup_r2,
    broad_wikidata,
    broad_wikidata_retry,
    cleveland_metadata,
    collect,
    content_lexicon,
    exposure_denylist,
    federated_census,
    prompt_library,
    scene_prescreen,
)

app = typer.Typer(
    add_completion=False,
    help="LatentArtBench — Painter Feature Generation v1 census collectors.",
)

_COLLECTORS: List[tuple] = [
    ("federated-census", federated_census.main, "Fixed-seed Wikidata/Commons attrition audit."),
    ("broad-wikidata", broad_wikidata.main, "Broad exact-creator no-P186 discovery census."),
    ("broad-wikidata-retry", broad_wikidata_retry.main, "Retry of the broad discovery census."),
    ("broad-media-followup", broad_media_followup.main, "Entity/media metadata follow-up."),
    ("broad-media-followup-r2", broad_media_followup_r2.main, "Retry of the media follow-up."),
    ("aic-metadata", aic_metadata.main, "Art Institute of Chicago route census."),
    ("aic-metadata-r2", aic_metadata_r2.main, "Retry of the Art Institute route census."),
    ("cleveland-metadata", cleveland_metadata.main, "Cleveland route on the shared engine."),
    ("collect", collect.main, "Protocol 2.2 R0 collection: fetch, keep everything, judge nothing."),
    ("verify-evidence", evidence.main, "Commit-bound audit of freezes, ledgers, and receipts."),
    ("prompt-library", prompt_library.main, "Render the §11.1 prompt library artifact."),
    ("content-lexicon", content_lexicon.main, "Render the §7.4 content lexicon artifact."),
    ("exposure-denylist", exposure_denylist.main, "Rebuild the pixel-exposure denylist."),
    ("scene-prescreen", scene_prescreen.main, "Non-binding scene-support pre-screen."),
]


def _passthrough(entry: Callable[[Sequence[str]], int]) -> Callable[[typer.Context], None]:
    def command(ctx: typer.Context) -> None:
        raise typer.Exit(code=entry(ctx.args))

    return command


for _name, _entry, _help in _COLLECTORS:
    app.command(
        name=_name,
        help=_help,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    )(_passthrough(_entry))


if __name__ == "__main__":  # pragma: no cover
    app()
