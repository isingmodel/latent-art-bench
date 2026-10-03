"""The two v3 painter groups and their reserves: the single source of identifiers and names."""

from __future__ import annotations

from typing import NamedTuple


class Painter(NamedTuple):
    painter_id: str
    name: str  # Exactly as written in the prompt clause.
    qid: str
    group: str


GROUPS = ("century", "hudson")
GROUP_TITLES = {"century": "Century group", "hudson": "Hudson River School"}

PAINTERS: tuple[Painter, ...] = (
    Painter("jacob_van_ruisdael", "Jacob van Ruisdael", "Q213612", "century"),
    Painter("canaletto", "Canaletto", "Q182664", "century"),
    Painter("vincent_van_gogh", "Vincent van Gogh", "Q5582", "century"),
    Painter("ernst_ludwig_kirchner", "Ernst Ludwig Kirchner", "Q229272", "century"),
    Painter("albert_bierstadt", "Albert Bierstadt", "Q77132", "hudson"),
    Painter("frederic_edwin_church", "Frederic Edwin Church", "Q366212", "hudson"),
    Painter("thomas_cole", "Thomas Cole", "Q334001", "hudson"),
    Painter("asher_brown_durand", "Asher Brown Durand", "Q391608", "hudson"),
)
# Named before the census; their metadata were collected. Amendment 1 withdrew the floor rule
# that would have used them, so they are not acquired.
RESERVES: tuple[Painter, ...] = (
    Painter("edvard_munch", "Edvard Munch", "Q41406", "century"),
    Painter("jasper_francis_cropsey", "Jasper Francis Cropsey", "Q1451318", "hudson"),
    Painter("john_frederick_kensett", "John Frederick Kensett", "Q982284", "hudson"),
)
ALL: tuple[Painter, ...] = PAINTERS + RESERVES
BY_ID = {p.painter_id: p for p in ALL}
BY_QID = {p.qid: p for p in ALL}
FLOOR = 60  # Withdrawn by Amendment 1; reported, never applied.


def group(name: str) -> tuple[Painter, ...]:
    return tuple(p for p in PAINTERS if p.group == name)
