#!/usr/bin/env python3
"""Render deterministic, post-hoc Pilot 2 contact sheets.

This utility is deliberately outside the prospective Pilot 2 implementation. It
validates the frozen cell and terminal manifests plus every successful source PNG
before it renders any thumbnail. It includes every cell exactly once and performs
no visual selection. The resulting contact sheets are descriptive QC only: they
are non-gating and have no effect on the registered analysis.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont, ImageOps
from PIL import __version__ as pillow_version

REPO_ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT_FROM_SCRIPT / "src"))

from latent_art_bench.io import canonical_json, hash_file, stable_hash  # noqa: E402
from latent_art_bench.pilot2.generation import (  # noqa: E402
    GenerationCell,
    TerminalGenerationRecord,
    generation_grid_sha256,
    terminal_records_manifest_sha256,
)

MODEL_ORDER = ("gpt-image-1", "gpt-image-2")
EXPECTED_CONTENT_BLOCKS = 8
EXPECTED_PROMPTS_PER_BLOCK = 5
EXPECTED_REPETITIONS = 4
EXPECTED_CELL_COUNT = (
    EXPECTED_CONTENT_BLOCKS
    * len(MODEL_ORDER)
    * EXPECTED_PROMPTS_PER_BLOCK
    * EXPECTED_REPETITIONS
)

MARGIN = 24
HEADER_HEIGHT = 78
ROW_LABEL_WIDTH = 196
GAP = 12
TILE_WIDTH = 240
TILE_HEIGHT = 208
IMAGE_INSET_X = 8
IMAGE_INSET_TOP = 8
IMAGE_BOX_HEIGHT = 168

BACKGROUND = (244, 242, 237)
PANEL = (255, 255, 255)
INK = (30, 32, 35)
MUTED = (91, 96, 102)
BORDER = (178, 181, 184)
PLACEHOLDER = (226, 224, 219)
REFUSAL = (142, 47, 47)


def _read_jsonl(path: Path, model: type[Any]) -> list[Any]:
    rows: list[Any] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(model.model_validate_json(line))
        except ValueError as exc:
            raise RuntimeError(f"{path}:{line_number}: invalid record: {exc}") from exc
    return rows


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _relative_to_repo(path: Path, repo_root: Path) -> str:
    resolved = path.resolve(strict=True)
    try:
        return resolved.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"source output is outside the repository: {resolved}") from exc


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".png", dir=str(path.parent)
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        image.save(
            temporary,
            format="PNG",
            optimize=False,
            compress_level=9,
            pnginfo=None,
        )
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _load_success_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"successful-output manifest is not an object: {path}")
    claimed = payload.get("successful_output_manifest_sha256")
    semantic = stable_hash(
        {
            key: value
            for key, value in payload.items()
            if key != "successful_output_manifest_sha256"
        }
    )
    if claimed != semantic:
        raise RuntimeError("successful-output manifest self-hash is stale")
    return payload


def _assert_cell_terminal_match(
    cell: GenerationCell, terminal: TerminalGenerationRecord
) -> None:
    pairs = {
        "cell_identity_sha256": (cell.cell_identity_sha256, terminal.cell_identity_sha256),
        "prompt_id": (cell.prompt_id, terminal.prompt_id),
        "content_id": (cell.content_id, terminal.content_id),
        "prompt_pair_id": (cell.prompt_pair_id, terminal.prompt_pair_id),
        "target_artist_id": (cell.target_artist_id, terminal.target_artist_id),
        "target_artist_name": (cell.target_artist_name, terminal.target_artist_name),
        "artist_free_control": (
            cell.artist_free_control,
            terminal.artist_free_control,
        ),
        "requested_model_label": (
            cell.requested_model_label,
            terminal.requested_model_label,
        ),
        "repetition": (cell.repetition, terminal.repetition),
    }
    stale = [name for name, (left, right) in pairs.items() if left != right]
    if stale:
        raise RuntimeError(
            f"cell/terminal mismatch for {cell.cell_id}: {', '.join(stale)}"
        )


def _validate_source_png(
    terminal: TerminalGenerationRecord,
    success_entry: dict[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    if terminal.output_path is None or terminal.output_sha256 is None:
        raise RuntimeError(f"successful terminal lacks output: {terminal.cell_id}")
    source_path = Path(terminal.output_path)
    if not source_path.is_absolute():
        source_path = repo_root / source_path
    source_path = source_path.resolve(strict=True)
    raw_root = (repo_root / "outputs/pilot_2/gpt_images").resolve(strict=True)
    if not source_path.is_relative_to(raw_root):
        raise RuntimeError(f"successful output escapes the frozen raw root: {source_path}")
    observed_sha256 = hash_file(source_path)
    if observed_sha256 != terminal.output_sha256:
        raise RuntimeError(f"successful output hash mismatch: {terminal.cell_id}")
    if (
        source_path.suffix.lower() != ".png"
        or source_path.stem != observed_sha256
        or source_path.parent.name != observed_sha256[:2]
    ):
        raise RuntimeError(f"output is not content-addressed PNG: {terminal.cell_id}")
    try:
        with Image.open(source_path) as opened:
            opened.load()
            observed_format = (opened.format or "").lower()
            observed_width, observed_height = opened.size
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"successful output does not decode: {terminal.cell_id}") from exc
    if (
        observed_format != "png"
        or observed_width != terminal.actual_width
        or observed_height != terminal.actual_height
    ):
        raise RuntimeError(f"decoded output metadata mismatch: {terminal.cell_id}")

    expected_success_fields = {
        "cell_id": terminal.cell_id,
        "cell_identity_sha256": terminal.cell_identity_sha256,
        "attempt_id": terminal.source_terminal_attempt_id,
        "attempt_number": terminal.source_terminal_attempt_number,
        "requested_model_label": terminal.requested_model_label,
        "output_path": terminal.output_path,
        "output_sha256": terminal.output_sha256,
        "output_byte_count": source_path.stat().st_size,
        "width": observed_width,
        "height": observed_height,
        "format": "png",
        "prompt_id": terminal.prompt_id,
        "content_id": terminal.content_id,
        "prompt_pair_id": terminal.prompt_pair_id,
        "target_artist_id": terminal.target_artist_id,
        "artist_free_control": terminal.artist_free_control,
        "repetition": terminal.repetition,
        "eligible_geometry": True,
    }
    stale = [
        key
        for key, expected in expected_success_fields.items()
        if success_entry.get(key) != expected
    ]
    if stale:
        raise RuntimeError(
            f"successful-output evidence mismatch for {terminal.cell_id}: "
            + ", ".join(stale)
        )
    return {
        "source_path": source_path,
        "source_output_path": _relative_to_repo(source_path, repo_root),
        "source_output_sha256": observed_sha256,
        "source_output_byte_count": source_path.stat().st_size,
        "source_width": observed_width,
        "source_height": observed_height,
        "source_format": observed_format,
    }


def _validate_inputs(
    repo_root: Path,
    cells_path: Path,
    terminals_path: Path,
    success_manifest_path: Path,
) -> tuple[
    list[GenerationCell],
    dict[str, TerminalGenerationRecord],
    dict[str, dict[str, Any]],
    dict[str, Any],
]:
    cells = _read_jsonl(cells_path, GenerationCell)
    terminals = _read_jsonl(terminals_path, TerminalGenerationRecord)
    if len(cells) != EXPECTED_CELL_COUNT or len(terminals) != EXPECTED_CELL_COUNT:
        raise RuntimeError("visual QC requires the exact frozen 320-cell result")
    if len({cell.cell_id for cell in cells}) != EXPECTED_CELL_COUNT:
        raise RuntimeError("generation-cell manifest contains duplicate cell ids")
    terminal_by_cell = {terminal.cell_id: terminal for terminal in terminals}
    if len(terminal_by_cell) != EXPECTED_CELL_COUNT:
        raise RuntimeError("terminal manifest contains duplicate cell ids")
    if set(terminal_by_cell) != {cell.cell_id for cell in cells}:
        raise RuntimeError("terminal manifest does not cover the exact frozen cells")

    success_manifest = _load_success_manifest(success_manifest_path)
    if success_manifest.get("generation_grid_sha256") != generation_grid_sha256(cells):
        raise RuntimeError("successful-output manifest binds a different cell grid")
    raw_success_entries = success_manifest.get("outputs")
    if not isinstance(raw_success_entries, list):
        raise RuntimeError("successful-output manifest outputs must be a list")
    success_by_cell: dict[str, dict[str, Any]] = {}
    for entry in raw_success_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("cell_id"), str):
            raise RuntimeError("successful-output manifest contains an invalid entry")
        if entry["cell_id"] in success_by_cell:
            raise RuntimeError("successful-output manifest contains duplicate cell ids")
        success_by_cell[entry["cell_id"]] = entry

    validated_sources: dict[str, dict[str, Any]] = {}
    for cell in cells:
        terminal = terminal_by_cell[cell.cell_id]
        _assert_cell_terminal_match(cell, terminal)
        if terminal.outcome == "succeeded":
            success_entry = success_by_cell.get(cell.cell_id)
            if success_entry is None:
                raise RuntimeError(
                    f"successful cell absent from output manifest: {cell.cell_id}"
                )
            validated_sources[cell.cell_id] = _validate_source_png(
                terminal, success_entry, repo_root
            )
        else:
            if cell.cell_id in success_by_cell:
                raise RuntimeError(
                    f"non-success cell appears in output manifest: {cell.cell_id}"
                )
            if terminal.output_path is not None or terminal.output_sha256 is not None:
                raise RuntimeError(
                    f"non-success terminal unexpectedly identifies output: {cell.cell_id}"
                )
    if set(success_by_cell) != set(validated_sources):
        raise RuntimeError("successful-output manifest contains unexpected cells")
    if success_manifest.get("successful_output_count") != len(validated_sources):
        raise RuntimeError("successful-output manifest count is stale")

    validation = {
        "generation_cells_file_sha256": hash_file(cells_path),
        "generation_grid_sha256": generation_grid_sha256(cells),
        "terminal_records_file_sha256": hash_file(terminals_path),
        "terminal_records_manifest_sha256": terminal_records_manifest_sha256(
            terminals
        ),
        "successful_output_manifest_file_sha256": hash_file(success_manifest_path),
        "successful_output_manifest_sha256": success_manifest[
            "successful_output_manifest_sha256"
        ],
        "verified_successful_output_count": len(validated_sources),
        "verified_non_success_count": len(cells) - len(validated_sources),
    }
    return cells, terminal_by_cell, validated_sources, validation


def _sheet_geometry() -> tuple[int, int]:
    width = (
        MARGIN
        + ROW_LABEL_WIDTH
        + GAP
        + len(range(EXPECTED_REPETITIONS)) * TILE_WIDTH
        + (EXPECTED_REPETITIONS - 1) * GAP
        + MARGIN
    )
    height = (
        MARGIN
        + HEADER_HEIGHT
        + GAP
        + EXPECTED_PROMPTS_PER_BLOCK * TILE_HEIGHT
        + (EXPECTED_PROMPTS_PER_BLOCK - 1) * GAP
        + MARGIN
    )
    return width, height


def _text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    *,
    font: Any,
    fill: Any,
) -> None:
    draw.text(xy, value, font=font, fill=fill)


def _render_sheet(
    *,
    sheet_path: Path,
    sheet_rank: int,
    content_id: str,
    model_label: str,
    prompt_order: Sequence[str],
    cell_by_coordinate: dict[tuple[str, int], GenerationCell],
    terminal_by_cell: dict[str, TerminalGenerationRecord],
    validated_sources: dict[str, dict[str, Any]],
    cell_manifest_rank: dict[str, int],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    width, height = _sheet_geometry()
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    title_font = ImageFont.load_default(size=20)
    label_font = ImageFont.load_default(size=15)
    small_font = ImageFont.load_default(size=13)

    title = f"Pilot 2 visual QC - {content_id.replace('-', ' ').title()} - {model_label}"
    _text(draw, (MARGIN, MARGIN), title, font=title_font, fill=INK)
    _text(
        draw,
        (MARGIN, MARGIN + 30),
        "POST HOC | NON-GATING | NO EFFECT ON ANALYSIS | ALL CELLS SHOWN",
        font=small_font,
        fill=MUTED,
    )
    tile_origin_x = MARGIN + ROW_LABEL_WIDTH + GAP
    tile_origin_y = MARGIN + HEADER_HEIGHT + GAP
    for repetition in range(EXPECTED_REPETITIONS):
        x = tile_origin_x + repetition * (TILE_WIDTH + GAP)
        _text(
            draw,
            (x + 5, MARGIN + HEADER_HEIGHT - 19),
            f"repetition {repetition}",
            font=small_font,
            fill=MUTED,
        )

    cell_entries: list[dict[str, Any]] = []
    for prompt_rank, prompt_id in enumerate(prompt_order, 1):
        first_cell = cell_by_coordinate[(prompt_id, 0)]
        row_y = tile_origin_y + (prompt_rank - 1) * (TILE_HEIGHT + GAP)
        prompt_label = (
            "Artist-free control"
            if first_cell.artist_free_control
            else first_cell.target_artist_name or first_cell.target_artist_id or "Artist"
        )
        _text(
            draw,
            (MARGIN, row_y + 8),
            f"{prompt_rank}. {prompt_label}",
            font=label_font,
            fill=INK,
        )
        _text(
            draw,
            (MARGIN, row_y + 34),
            "control" if first_cell.artist_free_control else "named-artist prompt",
            font=small_font,
            fill=MUTED,
        )

        for repetition in range(EXPECTED_REPETITIONS):
            cell = cell_by_coordinate[(prompt_id, repetition)]
            terminal = terminal_by_cell[cell.cell_id]
            tile_x = tile_origin_x + repetition * (TILE_WIDTH + GAP)
            tile_y = row_y
            draw.rectangle(
                (tile_x, tile_y, tile_x + TILE_WIDTH - 1, tile_y + TILE_HEIGHT - 1),
                fill=PANEL,
                outline=BORDER,
                width=1,
            )
            image_box = {
                "x": tile_x + IMAGE_INSET_X,
                "y": tile_y + IMAGE_INSET_TOP,
                "width": TILE_WIDTH - 2 * IMAGE_INSET_X,
                "height": IMAGE_BOX_HEIGHT,
            }
            thumbnail_coordinates: dict[str, int] | None = None
            source = validated_sources.get(cell.cell_id)
            if terminal.outcome == "succeeded":
                assert source is not None
                with Image.open(source["source_path"]) as opened:
                    opened.load()
                    normalized = opened.convert("RGB")
                thumb = ImageOps.contain(
                    normalized,
                    (image_box["width"], image_box["height"]),
                    method=Image.Resampling.LANCZOS,
                )
                paste_x = image_box["x"] + (image_box["width"] - thumb.width) // 2
                paste_y = image_box["y"] + (image_box["height"] - thumb.height) // 2
                canvas.paste(thumb, (paste_x, paste_y))
                thumbnail_coordinates = {
                    "x": paste_x,
                    "y": paste_y,
                    "width": thumb.width,
                    "height": thumb.height,
                }
                footer = "SUCCEEDED"
                footer_fill = MUTED
            else:
                draw.rectangle(
                    (
                        image_box["x"],
                        image_box["y"],
                        image_box["x"] + image_box["width"] - 1,
                        image_box["y"] + image_box["height"] - 1,
                    ),
                    fill=PLACEHOLDER,
                )
                draw.line(
                    (
                        image_box["x"],
                        image_box["y"],
                        image_box["x"] + image_box["width"] - 1,
                        image_box["y"] + image_box["height"] - 1,
                    ),
                    fill=BORDER,
                    width=2,
                )
                draw.line(
                    (
                        image_box["x"] + image_box["width"] - 1,
                        image_box["y"],
                        image_box["x"],
                        image_box["y"] + image_box["height"] - 1,
                    ),
                    fill=BORDER,
                    width=2,
                )
                placeholder = terminal.outcome.upper().replace("_", " ")
                bounds = draw.textbbox((0, 0), placeholder, font=title_font)
                placeholder_width = bounds[2] - bounds[0]
                placeholder_height = bounds[3] - bounds[1]
                _text(
                    draw,
                    (
                        image_box["x"] + (image_box["width"] - placeholder_width) // 2,
                        image_box["y"] + (image_box["height"] - placeholder_height) // 2,
                    ),
                    placeholder,
                    font=title_font,
                    fill=REFUSAL,
                )
                footer = placeholder
                footer_fill = REFUSAL
            _text(
                draw,
                (tile_x + 8, tile_y + TILE_HEIGHT - 24),
                footer,
                font=small_font,
                fill=footer_fill,
            )

            cell_entries.append(
                {
                    "cell_manifest_rank": cell_manifest_rank[cell.cell_id],
                    "cell_id": cell.cell_id,
                    "cell_identity_sha256": cell.cell_identity_sha256,
                    "content_id": cell.content_id,
                    "requested_model_label": cell.requested_model_label,
                    "prompt_id": cell.prompt_id,
                    "prompt_rank": prompt_rank,
                    "artist_free_control": cell.artist_free_control,
                    "target_artist_id": cell.target_artist_id,
                    "target_artist_name": cell.target_artist_name,
                    "repetition": cell.repetition,
                    "terminal_record_sha256": terminal.terminal_record_sha256,
                    "outcome": terminal.outcome,
                    "failure_kind": terminal.failure_kind,
                    "sheet_rank": sheet_rank,
                    "sheet_path": sheet_path.as_posix(),
                    "tile_coordinates": {
                        "x": tile_x,
                        "y": tile_y,
                        "width": TILE_WIDTH,
                        "height": TILE_HEIGHT,
                    },
                    "image_box_coordinates": image_box,
                    "thumbnail_coordinates": thumbnail_coordinates,
                    "refusal_placeholder": terminal.outcome == "refused",
                    "source_output_path": (
                        source["source_output_path"] if source is not None else None
                    ),
                    "source_output_sha256": (
                        source["source_output_sha256"] if source is not None else None
                    ),
                    "source_output_byte_count": (
                        source["source_output_byte_count"] if source is not None else None
                    ),
                    "source_width": source["source_width"] if source is not None else None,
                    "source_height": (
                        source["source_height"] if source is not None else None
                    ),
                    "source_format": source["source_format"] if source is not None else None,
                }
            )

    _atomic_save_png(canvas, sheet_path)
    sheet = {
        "sheet_rank": sheet_rank,
        "content_id": content_id,
        "requested_model_label": model_label,
        "path": sheet_path.as_posix(),
        "width": width,
        "height": height,
        "byte_count": sheet_path.stat().st_size,
        "sha256": hash_file(sheet_path),
        "cell_count": len(cell_entries),
        "cell_ids": [entry["cell_id"] for entry in cell_entries],
    }
    return sheet, cell_entries


def render(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    cells_path = repo_root / "configs/pilot_2/generation_cells.jsonl"
    terminals_path = repo_root / "artifacts/pilot_2/generation_terminal.jsonl"
    success_manifest_path = (
        repo_root / "reports/pilot_2/evidence/successful_output_manifest.json"
    )
    script_path = Path(__file__).resolve(strict=True)
    output_dir = output_dir.resolve()
    try:
        output_relative = output_dir.relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise RuntimeError("visual-QC output directory must be inside the repository") from exc

    # Validation is intentionally a complete first pass. No thumbnail is created
    # until every terminal self-hash, output hash, PNG decode, and evidence link passes.
    cells, terminal_by_cell, validated_sources, validation = _validate_inputs(
        repo_root, cells_path, terminals_path, success_manifest_path
    )

    content_order = _ordered_unique(cell.content_id for cell in cells)
    if len(content_order) != EXPECTED_CONTENT_BLOCKS:
        raise RuntimeError("generation cells do not contain exactly eight content blocks")
    actual_sheet_order = _ordered_unique(
        f"{cell.content_id}\0{cell.requested_model_label}" for cell in cells
    )
    expected_sheet_order = [
        f"{content_id}\0{model_label}"
        for content_id in content_order
        for model_label in MODEL_ORDER
    ]
    if actual_sheet_order != expected_sheet_order:
        raise RuntimeError("generation-cell sheet order differs from the frozen order")
    cell_manifest_rank = {cell.cell_id: rank for rank, cell in enumerate(cells, 1)}

    output_dir.mkdir(parents=True, exist_ok=True)
    sheets: list[dict[str, Any]] = []
    manifest_cells: list[dict[str, Any]] = []
    expected_png_names: set[str] = set()
    for sheet_rank, combined in enumerate(expected_sheet_order, 1):
        content_id, model_label = combined.split("\0", 1)
        grouped = [
            cell
            for cell in cells
            if cell.content_id == content_id
            and cell.requested_model_label == model_label
        ]
        if len(grouped) != EXPECTED_PROMPTS_PER_BLOCK * EXPECTED_REPETITIONS:
            raise RuntimeError(f"sheet does not contain exactly 20 cells: {combined!r}")
        prompt_order = _ordered_unique(cell.prompt_id for cell in grouped)
        if len(prompt_order) != EXPECTED_PROMPTS_PER_BLOCK:
            raise RuntimeError(f"sheet does not contain exactly five prompts: {combined!r}")
        expected_coordinates = [
            (prompt_id, repetition)
            for prompt_id in prompt_order
            for repetition in range(EXPECTED_REPETITIONS)
        ]
        actual_coordinates = [(cell.prompt_id, cell.repetition) for cell in grouped]
        if actual_coordinates != expected_coordinates:
            raise RuntimeError(f"sheet cells differ from frozen prompt/rep order: {combined!r}")
        cell_by_coordinate = {
            (cell.prompt_id, cell.repetition): cell for cell in grouped
        }
        filename = f"{sheet_rank:02d}_{content_id}__{model_label}.png"
        expected_png_names.add(filename)
        sheet_absolute = output_dir / filename
        sheet_relative = Path(output_relative) / filename
        sheet, sheet_cells = _render_sheet(
            sheet_path=sheet_absolute,
            sheet_rank=sheet_rank,
            content_id=content_id,
            model_label=model_label,
            prompt_order=prompt_order,
            cell_by_coordinate=cell_by_coordinate,
            terminal_by_cell=terminal_by_cell,
            validated_sources=validated_sources,
            cell_manifest_rank=cell_manifest_rank,
        )
        sheet["path"] = sheet_relative.as_posix()
        for entry in sheet_cells:
            entry["sheet_path"] = sheet_relative.as_posix()
        sheets.append(sheet)
        manifest_cells.extend(sheet_cells)

    unexpected_pngs = {
        path.name for path in output_dir.glob("*.png") if path.name not in expected_png_names
    }
    if unexpected_pngs:
        raise RuntimeError(
            "visual-QC directory contains unexpected PNGs: "
            + ", ".join(sorted(unexpected_pngs))
        )
    if len(sheets) != 16 or len(manifest_cells) != EXPECTED_CELL_COUNT:
        raise AssertionError("renderer did not cover the exact 16 sheets / 320 cells")
    if len({entry["cell_id"] for entry in manifest_cells}) != EXPECTED_CELL_COUNT:
        raise AssertionError("renderer duplicated or omitted a generation cell")
    if sorted(entry["cell_manifest_rank"] for entry in manifest_cells) != list(
        range(1, EXPECTED_CELL_COUNT + 1)
    ):
        raise AssertionError("renderer did not preserve every frozen cell-manifest rank")

    outcome_counts = Counter(entry["outcome"] for entry in manifest_cells)
    payload: dict[str, Any] = {
        "record_type": "pilot2_posthoc_visual_qc_manifest",
        "schema_version": "pilot2-posthoc-visual-qc-v1",
        "purpose": "post_result_visual_quality_control",
        "post_hoc": True,
        "non_gating": True,
        "affects_analysis": False,
        "analysis_effect_statement": (
            "These sheets are post hoc, descriptive, non-gating, and have no effect "
            "on eligibility, exclusions, measurements, estimates, or conclusions."
        ),
        "visual_selection_performed": False,
        "coverage_statement": (
            "Every frozen logical cell appears exactly once in manifest order; all "
            "successful outputs are thumbnailed and all refusals use placeholders."
        ),
        "ordering_basis": (
            "Deterministically derived from generation_cells.jsonl without image "
            "inspection: content first occurrence, requested label gpt-image-1 then "
            "gpt-image-2, prompt first occurrence within each sheet, repetition 0..3. "
            "Every tile records its original generation-cell manifest rank."
        ),
        "input_files": {
            "generation_cells": {
                "path": cells_path.relative_to(repo_root).as_posix(),
                "file_sha256": validation["generation_cells_file_sha256"],
                "semantic_sha256": validation["generation_grid_sha256"],
            },
            "terminal_records": {
                "path": terminals_path.relative_to(repo_root).as_posix(),
                "file_sha256": validation["terminal_records_file_sha256"],
                "semantic_sha256": validation[
                    "terminal_records_manifest_sha256"
                ],
            },
            "successful_output_manifest": {
                "path": success_manifest_path.relative_to(repo_root).as_posix(),
                "file_sha256": validation[
                    "successful_output_manifest_file_sha256"
                ],
                "semantic_sha256": validation[
                    "successful_output_manifest_sha256"
                ],
            },
            "renderer_script": {
                "path": script_path.relative_to(repo_root).as_posix(),
                "file_sha256": hash_file(script_path),
            },
        },
        "render_specification": {
            "pillow_version": pillow_version,
            "image_mode": "RGB",
            "resampling": "PIL.Image.Resampling.LANCZOS",
            "fit_policy": "contain_without_crop_centered_on_fixed_neutral_box",
            "png_optimize": False,
            "png_compress_level": 9,
            "metadata_written": False,
            "sheet_width": _sheet_geometry()[0],
            "sheet_height": _sheet_geometry()[1],
            "prompt_rows": EXPECTED_PROMPTS_PER_BLOCK,
            "repetition_columns": EXPECTED_REPETITIONS,
            "tile_width": TILE_WIDTH,
            "tile_height": TILE_HEIGHT,
        },
        "content_block_count": len(content_order),
        "requested_model_labels": list(MODEL_ORDER),
        "sheet_count": len(sheets),
        "cell_count": len(manifest_cells),
        "verified_successful_output_count": validation[
            "verified_successful_output_count"
        ],
        "verified_non_success_count": validation["verified_non_success_count"],
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "sheets": sheets,
        "cells": manifest_cells,
    }
    payload["manifest_sha256"] = stable_hash(payload)
    manifest_path = output_dir / "manifest.json"
    _atomic_write_bytes(
        manifest_path,
        (canonical_json(payload) + "\n").encode("utf-8"),
    )
    return {
        "manifest_path": manifest_path.relative_to(repo_root).as_posix(),
        "manifest_file_sha256": hash_file(manifest_path),
        "manifest_sha256": payload["manifest_sha256"],
        "sheet_count": len(sheets),
        "cell_count": len(manifest_cells),
        "outcome_counts": payload["outcome_counts"],
        "sheets": [
            {
                "path": sheet["path"],
                "byte_count": sheet["byte_count"],
                "sha256": sheet["sha256"],
            }
            for sheet in sheets
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT_FROM_SCRIPT,
        help="repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/pilot_2/visual_qc"),
        help="repository-relative visual-QC output directory",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve(strict=True)
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    summary = render(repo_root, output_dir)
    print(canonical_json(summary))


if __name__ == "__main__":
    main()
