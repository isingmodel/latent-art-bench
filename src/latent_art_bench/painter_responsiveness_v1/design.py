"""Joint allocation of eight prompt cells within each fixed-template repetition."""

from __future__ import annotations

import re
from collections import defaultdict

import numpy as np

ARMS = ("free", "generic", "monet", "cezanne")
POLARITIES = ("muted", "vivid")
TEMPLATE_COUNT = 6


def make_schedule(templates, *, seed, repetitions=4):
    """Return stable slot identities in randomized dispatch order, without prompts.

    Both instruction polarity and arm are randomized jointly; grouping all muted
    requests ahead of vivid requests would not implement this allocation.
    Repetition counts other than four support offline design comparisons only.
    """
    templates = list(templates)
    if len(templates) != TEMPLATE_COUNT or len(set(templates)) != TEMPLATE_COUNT:
        raise ValueError("exactly six distinct template IDs are required")
    if any(not isinstance(t, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", t)
           for t in templates):
        raise ValueError("template IDs must be portable lowercase identifiers")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 2:
        raise ValueError("at least two integer repetitions are required")
    rng = np.random.default_rng(seed)
    blocks = [(template, r) for template in templates for r in range(repetitions)]
    cells = [(arm, polarity) for arm in ARMS for polarity in POLARITIES]
    rows = []
    for block_index in rng.permutation(len(blocks)):
        template, repetition = blocks[int(block_index)]
        block_id = f"prv1:{template}:r{repetition:02d}"
        for within_block, cell_index in enumerate(rng.permutation(len(cells))):
            arm, polarity = cells[int(cell_index)]
            rows.append(dict(
                request_id=f"{block_id}:{arm}:{polarity}", block_id=block_id,
                template_id=template, repetition=repetition, arm=arm, polarity=polarity,
                sequence=len(rows), within_block=within_block,
            ))
    validate_schedule(rows)
    return rows


def validate_schedule(schedule):
    """Reject duplicate slots, missing cells, reordered rows and incomplete blocks."""
    if not schedule:
        raise ValueError("empty schedule")
    if [r["sequence"] for r in schedule] != list(range(len(schedule))):
        raise ValueError("schedule must retain its dispatch sequence")
    identities = [r["request_id"] for r in schedule]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate request identity")
    blocks = defaultdict(list)
    template_repetitions = defaultdict(set)
    for row in schedule:
        if row["arm"] not in ARMS or row["polarity"] not in POLARITIES:
            raise ValueError("undeclared factorial cell")
        blocks[row["block_id"]].append(row)
        template_repetitions[row["template_id"]].add(row["repetition"])
    if len(template_repetitions) != TEMPLATE_COUNT:
        raise ValueError("the finite target contains exactly six templates")
    repetition_sets = list(template_repetitions.values())
    repetitions = len(repetition_sets[0])
    if repetitions < 2 or any(s != set(range(repetitions)) for s in repetition_sets):
        raise ValueError("every template must have the same consecutive repetitions")
    if len(blocks) != TEMPLATE_COUNT * repetitions:
        raise ValueError("one block per template and repetition is required")
    expected = {(a, p) for a in ARMS for p in POLARITIES}
    for rows in blocks.values():
        if len(rows) != 8 or {(r["arm"], r["polarity"]) for r in rows} != expected:
            raise ValueError("each block must contain all eight cells exactly once")
        if len({(r["template_id"], r["repetition"]) for r in rows}) != 1:
            raise ValueError("a block cannot mix template/repetition identities")
        if [r["within_block"] for r in rows] != list(range(8)):
            raise ValueError("invalid within-block order")
        positions = [r["sequence"] for r in rows]
        if positions != list(range(positions[0], positions[0] + 8)):
            raise ValueError("factorial blocks must be dispatched contiguously")
    return dict(templates=sorted(template_repetitions), repetitions=repetitions,
                blocks=len(blocks), requests=len(schedule))
