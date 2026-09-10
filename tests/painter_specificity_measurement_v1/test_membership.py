"""Verify the protocol's real reference membership, including old failed rows."""

from collections import Counter

from latent_art_bench.painter_specificity_measurement_v1.workflow import (
    COUNTS,
    EXCLUDED,
    reference_records,
)


def test_declared_reference_panel_has_exactly_649_usable_works():
    rows = reference_records()
    assert len(rows) == 649
    assert Counter(r["painter_id"] for r in rows) == COUNTS
    assert not EXCLUDED.intersection(r["image_id"] for r in rows)
    assert all(len(r["values"]) == 31 for r in rows)
