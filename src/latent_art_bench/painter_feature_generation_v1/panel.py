"""The four-painter panel: the single source of painter identifiers and display names.

Every route, artifact renderer, and report derives its roster from this module so that a
roster change is one edit, not four. Provider-specific spellings (for example the Art
Institute's "Paul Cezanne" agent name) belong in the provider's frozen config, not here.
"""

from __future__ import annotations

from typing import Dict, NamedTuple, Tuple


class Painter(NamedTuple):
    painter_id: str
    display_name: str
    short_label: str
    wikidata_qid: str


PAINTERS: Tuple[Painter, ...] = (
    Painter("claude_monet", "Claude Monet", "Monet", "Q296"),
    Painter("alfred_sisley", "Alfred Sisley", "Sisley", "Q175130"),
    Painter("camille_pissarro", "Camille Pissarro", "Pissarro", "Q134741"),
    Painter("paul_cezanne", "Paul Cézanne", "Cézanne", "Q35548"),
)
PAINTER_IDS: Tuple[str, ...] = tuple(p.painter_id for p in PAINTERS)
DISPLAY_NAMES: Dict[str, str] = {p.painter_id: p.display_name for p in PAINTERS}
SHORT_LABELS: Dict[str, str] = {p.painter_id: p.short_label for p in PAINTERS}
ID_NAME_PAIRS: Tuple[Tuple[str, str], ...] = tuple((p.painter_id, p.display_name) for p in PAINTERS)
