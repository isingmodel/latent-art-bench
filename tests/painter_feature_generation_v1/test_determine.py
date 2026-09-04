from __future__ import annotations

import json
from pathlib import Path

import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v1 import determine

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RECORDED_CENSUS = (
    REPOSITORY_ROOT
    / "data/manifests/painter_feature_generation_v1"
    / "broad_media_followup_publication_r2/candidates.jsonl"
)

PASSING_CLAIMS = {
    "P170": ("Q296",),
    "P31": ("Q3305213",),
    "P186": ("Q296955", "Q12321255"),
    "P195": ("Q1191515",),
}


def _file(**overrides: object) -> determine.File:
    fields = {
        "name": "File:A.jpg",
        "licence": "Public domain",
        "restriction": "",
        "short_side": 2048,
        "url": "https://upload.wikimedia.org/a.jpg",
    }
    fields.update(overrides)
    return determine.File(**fields)  # type: ignore[arg-type]


def _item(**overrides: object) -> determine.Item:
    fields = {
        "painter_id": "claude_monet",
        "painter_qid": "Q296",
        "item_qid": "Q1",
        "label": "The Seine at Argenteuil",
        "claims": dict(PASSING_CLAIMS),
        "files": (_file(),),
    }
    fields.update(overrides)
    return determine.Item(**fields)  # type: ignore[arg-type]


def _without(prop: str, **replace: object) -> dict:
    claims = dict(PASSING_CLAIMS)
    claims.update(replace)
    if prop in claims and prop not in replace:
        claims.pop(prop)
    return claims


def test_an_item_clearing_every_gate_is_admitted() -> None:
    decision = determine.decide(_item())
    assert decision.admitted is True
    assert decision.failed_gate is None
    assert decision.content_class == "water_organized"
    assert decision.file is not None and decision.file.name == "File:A.jpg"


@pytest.mark.parametrize(
    "gate,overrides",
    [
        ("creator", {"claims": _without("P170", P170=("Q35548",))}),
        ("painting", {"claims": _without("P31", P31=("Q93184",))}),
        ("medium", {"claims": _without("P186", P186=("Q296955",))}),
        ("collection", {"claims": _without("P195")}),
        ("rights", {"files": (_file(licence="CC BY-NC 4.0"),)}),
        ("geometry", {"files": (_file(short_side=1023),)}),
        ("content", {"label": "Still Life with Apples"}),
    ],
)
def test_each_gate_fails_on_its_own_and_names_itself(gate: str, overrides: dict) -> None:
    decision = determine.decide(_item(**overrides))
    assert decision.admitted is False
    assert decision.failed_gate == gate


def test_the_first_failing_gate_wins_and_later_gates_are_not_reported() -> None:
    # This item fails medium, geometry, and content at once; only medium is named.
    decision = determine.decide(
        _item(
            claims=_without("P186", P186=()),
            files=(_file(short_side=64),),
            label="Portrait of a Woman",
        )
    )
    assert decision.failed_gate == "medium"
    assert decision.file is None
    assert decision.content_class is None


def test_two_creator_statements_fail_even_when_one_is_the_target() -> None:
    decision = determine.decide(_item(claims=_without("P170", P170=("Q296", "Q175130"))))
    assert decision.failed_gate == "creator"


def test_an_openly_licensed_copyrighted_photograph_is_admitted() -> None:
    """A CC BY-SA photograph of a public-domain painting is copyrighted and open at once.

    The recorded census flagged 297 such files ``Copyrighted``; every one carries an open CC
    licence. Protocol 2.3 Section 3 gates on the licence, so they are admitted.
    """
    for licence in ("CC BY-SA 4.0", "CC0", "CC BY 3.0", "No restrictions", "public domain"):
        assert determine.decide(_item(files=(_file(licence=licence),))).admitted is True


def test_a_usage_restriction_excludes_the_file_whatever_its_licence() -> None:
    decision = determine.decide(_item(files=(_file(restriction="ita-mibac"),)))
    assert decision.failed_gate == "rights"


def test_a_restricted_licence_is_excluded() -> None:
    for licence in ("CC BY-NC 4.0", "CC BY-NC-SA 4.0", "CC BY-ND 4.0", "Fair use", "", "GFDL"):
        assert determine.decide(_item(files=(_file(licence=licence),))).failed_gate == "rights"


def test_any_qualifying_file_carries_the_item_and_the_largest_becomes_the_surrogate() -> None:
    item = _item(
        files=(
            _file(name="File:small.jpg", short_side=800),
            _file(name="File:restricted.jpg", licence="CC BY-NC 4.0", short_side=9000),
            _file(name="File:good.jpg", short_side=3000),
            _file(name="File:ok.jpg", short_side=1500),
        )
    )
    decision = determine.decide(item)
    assert decision.admitted is True
    assert decision.file is not None and decision.file.name == "File:good.jpg"


def test_surrogate_choice_is_deterministic_on_a_tie() -> None:
    files = (_file(name="File:b.jpg"), _file(name="File:a.jpg"))
    first = determine.decide(_item(files=files))
    second = determine.decide(_item(files=tuple(reversed(files))))
    assert first.file == second.file
    assert first.file is not None and first.file.name == "File:b.jpg"


def test_content_is_decided_from_the_label_not_from_the_file() -> None:
    decision = determine.decide(
        _item(label="Still Life with Apples", files=(_file(name="File:The Seine at dawn.jpg"),))
    )
    assert decision.failed_gate == "content"
    # The surrogate is still reported, so a content exclusion stays auditable.
    assert decision.file is not None


def test_an_unresolved_label_is_not_admitted() -> None:
    assert determine.decide(_item(label="")).failed_gate == "content"
    assert determine.decide(_item(label="Untitled")).failed_gate == "content"


def test_no_score_or_middle_state_is_emitted() -> None:
    row = determine.decide(_item()).row(_item())
    assert set(row) == {
        "schema_version",
        "protocol_id",
        "painter_id",
        "item_qid",
        "label",
        "admitted",
        "failed_gate",
        "content_class",
        "surrogate",
    }
    assert isinstance(row["admitted"], bool)
    for banned in ("score", "confidence", "probability", "review", "partial"):
        assert banned not in json.dumps(row).lower()


def _rooted(tmp_path: Path) -> Path:
    """A tmp root carrying the three repository files every receipt must bind."""
    for relative in (determine.PROTOCOL_PATH, determine.LEXICON_PATH, determine.DETERMINER_PATH):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPOSITORY_ROOT / relative).read_bytes())
    return tmp_path


def _census(path: Path, rows: list) -> Path:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def _row(qid: str, filename: str, short_side: int, **media: object) -> dict:
    payload = {
        "item_qid": qid,
        "painter_id": "claude_monet",
        "entity": {
            "label": "The Seine at Argenteuil",
            "best_rank_claims": {
                prop: [{"value": value, "rank": "normal"} for value in values]
                for prop, values in PASSING_CLAIMS.items()
            },
        },
        "media": {
            "canonical_title": filename,
            "license_short_name": "Public domain",
            "restrictions": "",
            "original_short_side": short_side,
            "original_url": f"https://upload.wikimedia.org/{filename}",
        },
    }
    payload["media"].update(media)
    return payload


def test_rows_sharing_an_item_become_one_item_with_several_files(tmp_path: Path) -> None:
    path = _census(
        tmp_path / "c.jsonl",
        [
            _row("Q1", "File:one.jpg", 700),
            _row("Q2", "File:other.jpg", 2000),
            _row("Q1", "File:two.jpg", 4000),
        ],
    )
    items = list(determine.read_items(path))
    assert [item.item_qid for item in items] == ["Q1", "Q2"]
    assert [f.name for f in items[0].files] == ["File:one.jpg", "File:two.jpg"]
    assert items[0].values("P186") == ("Q296955", "Q12321255")
    assert items[0].painter_qid == "Q296"
    assert determine.decide(items[0]).file.name == "File:two.jpg"


def test_run_counts_a_funnel_that_is_monotone_and_ends_at_admitted(tmp_path: Path) -> None:
    rows = [
        _row("Q1", "File:a.jpg", 2000),
        _row("Q2", "File:b.jpg", 100),
        _row("Q3", "File:c.jpg", 2000, license_short_name="CC BY-NC 4.0"),
    ]
    root = _rooted(tmp_path)
    path = _census(root / "c.jsonl", rows)
    receipt, determinations = determine.run(root, path, "test-r1")
    funnel = receipt["funnel"]
    counts = [funnel["discovered"]["claude_monet"]] + [
        funnel[f"passed_{gate}"]["claude_monet"] for gate in determine.GATES
    ]
    assert counts == sorted(counts, reverse=True)
    assert counts == [3, 3, 3, 3, 3, 2, 1, 1]
    assert receipt["admitted"]["claude_monet"] == 1
    assert receipt["failed_gate_counts"] == {"geometry": 1, "rights": 1}
    assert len(determinations) == 3
    assert receipt["census_sha256"]


def test_the_floor_is_the_2_1_section_9_derivation() -> None:
    assert determine.ELIGIBILITY_FLOOR == 179
    assert determine.PRIMARY_PANEL_FLOOR == -(-100 * 5 // 3)  # ceil(100 / 0.6)


@pytest.mark.skipif(not RECORDED_CENSUS.is_file(), reason="recorded census is not present")
def test_the_recorded_census_clears_the_floor_for_every_painter() -> None:
    receipt, rows = determine.run(REPOSITORY_ROOT, RECORDED_CENSUS, "pfg-v1-r1-20260904")
    assert len(rows) == 3543
    assert receipt["admitted"] == {
        "claude_monet": 538,
        "alfred_sisley": 196,
        "camille_pissarro": 259,
        "paul_cezanne": 200,
    }
    assert all(receipt["clears_floor"].values())
    # Sisley is the binding constraint: every later rule must be checked against him first.
    assert min(receipt["margin_against_floor"], key=receipt["margin_against_floor"].get) == (
        "alfred_sisley"
    )
    assert receipt["margin_against_floor"]["alfred_sisley"] == 17


RECORDED_DETERMINATION = (
    REPOSITORY_ROOT
    / "data/manifests/painter_feature_generation_v1"
    / "pfg_v1_r1_20260904_determination.jsonl"
)
RECORDED_RECEIPT = RECORDED_DETERMINATION.with_name("pfg_v1_r1_20260904_determination_receipt.json")


def test_run_writes_both_outputs_and_binds_every_input(tmp_path: Path) -> None:
    root = _rooted(tmp_path)
    out = root / "out"
    census = _census(root / "c.jsonl", [_row("Q1", "File:a.jpg", 2000)])
    receipt, rows = determine.run(root, census, "test-r1", out)

    determination = out / "test-r1_determination.jsonl"
    assert determination.is_file()
    assert (out / "test-r1_determination_receipt.json").is_file()
    assert receipt["determination_sha256"] == hash_file(determination)
    assert receipt["census_sha256"] == hash_file(census)
    for name in ("census", "protocol", "content_lexicon", "determiner", "determination"):
        assert receipt[f"{name}_path"] and receipt[f"{name}_sha256"]
    assert receipt["items_determined"] == len(rows) == 1


@pytest.mark.skipif(
    not (RECORDED_DETERMINATION.is_file() and RECORDED_CENSUS.is_file()),
    reason="the recorded determination is not present",
)
def test_the_recorded_determination_is_reproducible_from_its_bound_inputs() -> None:
    """Re-running the judge on the bound census must reproduce the committed rows exactly.

    This is what makes the determination evidence rather than an assertion: the corpus cannot
    drift from the rule that produced it without this failing.
    """
    receipt = json.loads(RECORDED_RECEIPT.read_text(encoding="utf-8"))
    census = REPOSITORY_ROOT / receipt["census_path"]
    assert hash_file(census) == receipt["census_sha256"]

    fresh, rows = determine.run(REPOSITORY_ROOT, census, receipt["determination_id"])
    recorded = [
        json.loads(line)
        for line in RECORDED_DETERMINATION.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows == recorded
    for key in ("funnel", "admitted", "failed_gate_counts", "clears_floor", "items_determined"):
        assert fresh[key] == receipt[key], key


def test_a_missing_bound_input_is_refused_rather_than_silently_unbound(tmp_path: Path) -> None:
    root = _rooted(tmp_path)
    (root / determine.LEXICON_PATH).unlink()
    census = _census(root / "c.jsonl", [_row("Q1", "File:a.jpg", 2000)])
    with pytest.raises(determine.DeterminationError, match="content_lexicon"):
        determine.run(root, census, "test-r1")
