"""Non-binding feasibility pre-screen of the corpus-adequacy gates.

Protocol 2.1 §8.1 and §9 fix the role split, the per-painter floors, and the auxiliary panel;
Protocol 2.0 additionally required four-way scene cells. This module turns both rule sets into
the minimum number of newly eligible works each painter needs and compares those floors with
the *upper bound* visible in the completed R0 manifests, using the §7.4 content lexicon on
discovery metadata.

The comparison is a metadata proxy. It is not the R2 eligibility run (that uses authority
fields after reconciliation), it does not open any image, and it cannot admit or exclude a
work. Every number here is a screening upper bound, not a protocol count.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v1 import content_lexicon as lex
from latent_art_bench.painter_feature_generation_v1 import exposure_denylist

BROAD_MEDIA_CANDIDATES = Path(
    "data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/"
    "candidates.jsonl"
)
AIC_CANDIDATES = Path(
    "data/manifests/painter_feature_generation_v1/aic_metadata_publication_r2/candidates.jsonl"
)
OUTPUT_JSON = Path("reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json")
OUTPUT_MD = Path("reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md")
SCHEMA_VERSION = "painter-feature-generation-v1-scene-support-prescreen/2.0"
PAINTERS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
PAINTER_LABELS = {
    "claude_monet": "Monet",
    "alfred_sisley": "Sisley",
    "camille_pissarro": "Pissarro",
    "paul_cezanne": "Cézanne",
}
SCENES = tuple(lex.CLASS_PRIORITY)

# Shared constants (§8.1 role rule, §9 floors).
ROLE_SHARE = {"new_development": 1 / 5, "new_qualification": 1 / 5, "sealed_confirmation": 3 / 5}
DEV_MIN = 10
QUAL_MIN = 10
ESS_MIN = 100
AUX_MIN_PER_PAINTER = 12
# Protocol 2.0 only.
CONF_MIN_PER_CELL_20 = 20
MIN_GROUPS_20 = 3
# Protocol 2.1 only: uniform weights, so confirmation count = ESS.
CONF_MIN_PER_PAINTER_21 = ESS_MIN

# Hand-curated Wikidata collection QIDs. Only identifiers whose label is certain are listed;
# every other collection QID is reported as unresolved and must be resolved before use.
REGISTRY_INSTITUTIONS = {
    "Q239303": "Art Institute of Chicago",
    "Q214867": "National Gallery of Art",
    "Q657415": "Cleveland Museum of Art",
    "Q1568434": "Yale University Art Gallery",
    "Q731126": "J. Paul Getty Museum",
    "Q1700481": "Minneapolis Institute of Art",
    "Q820892": "Petit Palais (Paris Musées)",
    "Q640447": "Musée Carnavalet (Paris Musées)",
    "Q23402": "Musée d'Orsay (POP/Joconde)",
    "Q19675": "Musée du Louvre (POP/Joconde)",
    "Q1140507": "Musée de l'Orangerie (POP/Joconde)",
    "Q1327886": "Musée Marmottan Monet (POP/Joconde)",
}
KNOWN_NON_REGISTRY = {
    "Q160236": "Metropolitan Museum of Art",
    "Q808462": "Barnes Foundation",
    "Q49133": "Museum of Fine Arts, Boston",
    "Q132783": "Hermitage Museum",
    "Q180788": "National Gallery, London",
    "Q4872": "Pushkin Museum",
    "Q510324": "Philadelphia Museum of Art",
}
EXCLUDE_SUBJECTS = {"still life", "portraits", "bathers", "interior", "nudes", "figure"}


# --------------------------------------------------------------------------- floors


def _eligible_for(role_min: int, share: float) -> int:
    return math.ceil(role_min / share)


def per_cell_eligible_floor(groups: int) -> Dict[str, int]:
    """Protocol 2.0: works needed in one painter × scene cell."""
    conf_needed = max(CONF_MIN_PER_CELL_20, math.ceil(ESS_MIN / groups))
    dev_floor = _eligible_for(DEV_MIN, ROLE_SHARE["new_development"])
    qual_floor = _eligible_for(QUAL_MIN, ROLE_SHARE["new_qualification"])
    conf_floor = _eligible_for(conf_needed, ROLE_SHARE["sealed_confirmation"])
    return {
        "confirmation_works_needed_per_cell": conf_needed,
        "eligible_for_development_floor": dev_floor,
        "eligible_for_qualification_floor": qual_floor,
        "eligible_for_confirmation_and_ess_floor": conf_floor,
        "eligible_per_cell": max(dev_floor, qual_floor, conf_floor),
    }


def per_painter_floor_2_1() -> Dict[str, int]:
    """Protocol 2.1: works needed per painter in the single outdoor-place domain."""
    dev_floor = _eligible_for(DEV_MIN, ROLE_SHARE["new_development"])
    qual_floor = _eligible_for(QUAL_MIN, ROLE_SHARE["new_qualification"])
    conf_floor = _eligible_for(CONF_MIN_PER_PAINTER_21, ROLE_SHARE["sealed_confirmation"])
    primary = max(dev_floor, qual_floor, conf_floor)
    return {
        "confirmation_works_needed_per_painter": CONF_MIN_PER_PAINTER_21,
        "eligible_for_development_floor": dev_floor,
        "eligible_for_qualification_floor": qual_floor,
        "eligible_for_confirmation_and_ess_floor": conf_floor,
        "eligible_per_painter_primary": primary,
        "auxiliary_independent_capture_works_per_painter": AUX_MIN_PER_PAINTER,
        "eligible_per_painter_total": primary + AUX_MIN_PER_PAINTER,
    }


def floors() -> Dict[str, Any]:
    by_groups = {}
    for groups in (3, 4):
        cell = per_cell_eligible_floor(groups)
        by_groups[f"G={groups}"] = {
            **cell,
            "eligible_per_painter_primary": groups * cell["eligible_per_cell"],
            "auxiliary_independent_capture_works_per_painter": AUX_MIN_PER_PAINTER,
            "eligible_per_painter_total": groups * cell["eligible_per_cell"] + AUX_MIN_PER_PAINTER,
        }
    return {
        "role_share": ROLE_SHARE,
        "constants": {
            "development_min": DEV_MIN,
            "qualification_min": QUAL_MIN,
            "equal_scene_ess_min_2_0": ESS_MIN,
            "confirmation_min_per_cell_2_0": CONF_MIN_PER_CELL_20,
            "minimum_retained_groups_2_0": MIN_GROUPS_20,
            "confirmation_min_per_painter_2_1": CONF_MIN_PER_PAINTER_21,
            "auxiliary_min_per_painter": AUX_MIN_PER_PAINTER,
        },
        "derivation": (
            "role counts follow the modulo-5 hash rank, so a population needs about 5× its "
            "development floor and 5/3× its confirmation floor; under Protocol 2.0 ESS = "
            "G²/Σ(1/n_as) reaches 100 only when the average scene cell holds 100/G confirmation "
            "works; under Protocol 2.1 weights are uniform so ESS equals the confirmation count; "
            "historically exposed works never count toward these floors"
        ),
        "protocol_2_1": per_painter_floor_2_1(),
        "protocol_2_0_by_retained_groups": by_groups,
    }


# --------------------------------------------------------------------------- inputs


def _read_jsonl(path: Path) -> List[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _denylist_index(rows: Sequence[Mapping[str, Any]]) -> Dict[str, set]:
    index: Dict[str, set] = {"aic_ids": set(), "qids": set()}
    for row in rows:
        if not row.get("denylisted"):
            continue
        if row.get("provider") == "aic" and row.get("provider_object_id"):
            index["aic_ids"].add(str(row["provider_object_id"]))
        if row.get("wikidata_qid"):
            index["qids"].add(str(row["wikidata_qid"]))
    return index


def _new_bucket() -> Dict[str, Any]:
    return {
        "rows": 0,
        "gate_pass_rows": 0,
        "gate_pass_distinct_items": 0,
        "disposition": Counter(),
        "eligible_primary_class": Counter(),
        "eligible_any_class_match": Counter(),
        "with_collection_qid": 0,
        "registry_institution": 0,
        "known_non_registry_museum": 0,
        "unresolved_collection_qid": 0,
        "no_collection_qid": 0,
        "eligible_with_collection_qid": 0,
        "eligible_with_collection_qid_by_class": Counter(),
        "eligible_registry_by_class": Counter(),
        "denylisted_items": 0,
        "short_side_at_least_2048": 0,
    }


def _broad_media(rows: Sequence[Mapping[str, Any]], denylist: Dict[str, set]) -> Dict[str, Any]:
    per_painter = {painter: _new_bucket() for painter in PAINTERS}
    unresolved_collections: Counter = Counter()
    items_seen: Dict[str, set] = defaultdict(set)
    for row in rows:
        painter = row.get("painter_id")
        if painter not in per_painter:
            continue
        bucket = per_painter[painter]
        bucket["rows"] += 1
        if row.get("discovery_gate") != "federated_metadata_candidate":
            continue
        bucket["gate_pass_rows"] += 1
        item = str(row.get("item_qid"))
        if item in items_seen[painter]:
            continue  # count each Wikidata item once for content/collection statistics
        items_seen[painter].add(item)
        entity = row.get("entity") or {}
        media = row.get("media") or {}
        text = " ".join(
            str(part)
            for part in (
                entity.get("label"),
                entity.get("description"),
                media.get("image_description"),
                media.get("object_name"),
            )
            if part
        )
        result = lex.classify(text)
        disposition = result["disposition"]
        bucket["disposition"][disposition] += 1
        eligible = disposition == lex.ELIGIBLE
        if eligible:
            bucket["eligible_primary_class"][result["primary_class"]] += 1
            for name, hit in result["class_matches"].items():
                if hit:
                    bucket["eligible_any_class_match"][name] += 1
        qids = set(entity.get("collection_qids") or [])
        if qids:
            bucket["with_collection_qid"] += 1
            if qids & set(REGISTRY_INSTITUTIONS):
                bucket["registry_institution"] += 1
                if eligible:
                    bucket["eligible_registry_by_class"][result["primary_class"]] += 1
            elif qids & set(KNOWN_NON_REGISTRY):
                bucket["known_non_registry_museum"] += 1
            else:
                bucket["unresolved_collection_qid"] += 1
                unresolved_collections.update(qids)
            if eligible:
                bucket["eligible_with_collection_qid"] += 1
                bucket["eligible_with_collection_qid_by_class"][result["primary_class"]] += 1
        else:
            bucket["no_collection_qid"] += 1
        if item in denylist["qids"]:
            bucket["denylisted_items"] += 1
        short_side = media.get("original_short_side")
        if isinstance(short_side, int) and short_side >= 2048:
            bucket["short_side_at_least_2048"] += 1
    for painter, bucket in per_painter.items():
        bucket["gate_pass_distinct_items"] = len(items_seen[painter])
        for key, value in list(bucket.items()):
            if isinstance(value, Counter):
                bucket[key] = dict(sorted(value.items()))
    return {
        "per_painter": per_painter,
        "top_unresolved_collection_qids": [
            {"qid": qid, "gate_pass_items": count}
            for qid, count in unresolved_collections.most_common(20)
        ],
    }


def _aic(rows: Sequence[Mapping[str, Any]], denylist: Dict[str, set]) -> Dict[str, Any]:
    per_painter: Dict[str, Dict[str, Any]] = {
        painter: {
            "rows": 0,
            "screened_candidates": 0,
            "screened_disposition": Counter(),
            "screened_denylisted": 0,
            "screened_eligible_not_denylisted": 0,
        }
        for painter in PAINTERS
    }
    for row in rows:
        painter = row.get("painter_id")
        if painter not in per_painter:
            continue
        bucket = per_painter[painter]
        bucket["rows"] += 1
        screening = row.get("screening") or {}
        if not screening.get("metadata_and_media_candidate"):
            continue
        bucket["screened_candidates"] += 1
        record = row.get("aic_record") or {}
        subjects = [str(s) for s in record.get("subject_titles") or []]
        text = " ".join([str(record.get("title") or ""), *subjects])
        result = lex.classify(text)
        disposition = result["disposition"]
        if (
            set(s.casefold() for s in subjects) & EXCLUDE_SUBJECTS
            and not result["override_matches"]
        ):
            disposition = lex.INELIGIBLE
        bucket["screened_disposition"][disposition] += 1
        denylisted = str(row.get("aic_artwork_id")) in denylist["aic_ids"]
        bucket["screened_denylisted"] += int(denylisted)
        if not denylisted and disposition == lex.ELIGIBLE:
            bucket["screened_eligible_not_denylisted"] += 1
    for bucket in per_painter.values():
        bucket["screened_disposition"] = dict(sorted(bucket["screened_disposition"].items()))
    return {"per_painter": per_painter}


def _evaluation_2_1(broad: Mapping[str, Any]) -> Dict[str, Any]:
    floor = per_painter_floor_2_1()["eligible_per_painter_total"]
    per_painter = {}
    for painter in PAINTERS:
        upper = broad["per_painter"][painter]["eligible_with_collection_qid"]
        per_painter[painter] = {
            "upper_bound_eligible_with_collection_qid": upper,
            "floor_including_auxiliary": floor,
            "clears_floor_at_upper_bound": upper >= floor,
            "margin_at_upper_bound": upper - floor,
        }
    weakest = min(per_painter, key=lambda p: per_painter[p]["margin_at_upper_bound"])
    return {
        "rule": (
            "Protocol 2.1 §9: at least 100 confirmation works per painter (uniform weights), "
            "10 development, 10 qualification, and 12 auxiliary works; applied here to the "
            "lexicon-eligible items that carry a collection QID, before authority verification, "
            "deduplication, complete-view checks, and private-collection exclusion, so real "
            "counts can only be lower"
        ),
        "per_painter": per_painter,
        "weakest_painter": weakest,
        "all_painters_clear_at_upper_bound": all(
            row["clears_floor_at_upper_bound"] for row in per_painter.values()
        ),
    }


def _retention_under_2_0(broad: Mapping[str, Any]) -> Dict[str, Any]:
    """Apply Protocol 2.0 §9's deterministic retention rule to the proxy upper bounds."""
    floor3 = per_cell_eligible_floor(3)["eligible_per_cell"]
    floor4 = per_cell_eligible_floor(4)["eligible_per_cell"]
    per_scene = {}
    for scene in SCENES:
        counts = {
            painter: broad["per_painter"][painter]["eligible_with_collection_qid_by_class"].get(
                scene, 0
            )
            for painter in PAINTERS
        }
        weakest = min(counts, key=lambda p: counts[p])
        per_scene[scene] = {
            "upper_bound_by_painter": counts,
            "weakest_painter": weakest,
            "weakest_upper_bound": counts[weakest],
            "clears_floor_if_all_four_groups_retained": counts[weakest] >= floor4,
            "clears_floor_if_three_groups_retained": counts[weakest] >= floor3,
        }
    retained3 = [s for s in SCENES if per_scene[s]["clears_floor_if_three_groups_retained"]]
    return {
        "rule": (
            "Protocol 2.0 §9 retained every scene group in which each painter cleared the "
            "per-cell floor and stopped with fewer than three; kept here for the record of why "
            "Protocol 2.1 removed scene stratification"
        ),
        "per_scene": per_scene,
        "groups_clearing_three_group_floor": retained3,
        "study_would_stop_even_at_upper_bound": len(retained3) < MIN_GROUPS_20,
    }


def run(root: Path) -> Dict[str, Any]:
    broad_rows = _read_jsonl(root / BROAD_MEDIA_CANDIDATES)
    aic_rows = _read_jsonl(root / AIC_CANDIDATES)
    deny_rows = exposure_denylist.load(root)
    denylist = _denylist_index(deny_rows)
    broad = _broad_media(broad_rows, denylist)
    aic = _aic(aic_rows, denylist)
    lexicon_path = root / lex.OUTPUT_PATH
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "non_binding_metadata_proxy_prescreen_not_a_protocol_count",
        "protocol_id": lex.PROTOCOL_ID,
        "inputs": {
            "broad_media_candidates": {
                "path": str(BROAD_MEDIA_CANDIDATES),
                "sha256": hash_file(root / BROAD_MEDIA_CANDIDATES),
                "rows": len(broad_rows),
            },
            "aic_candidates": {
                "path": str(AIC_CANDIDATES),
                "sha256": hash_file(root / AIC_CANDIDATES),
                "rows": len(aic_rows),
            },
            "exposure_denylist": {
                "path": str(exposure_denylist.OUTPUT_PATH),
                "sha256": (
                    hash_file(root / exposure_denylist.OUTPUT_PATH)
                    if (root / exposure_denylist.OUTPUT_PATH).is_file()
                    else None
                ),
                "denylisted_works": sum(1 for row in deny_rows if row.get("denylisted")),
            },
            "content_lexicon": {
                "path": str(lex.OUTPUT_PATH),
                "sha256": hash_file(lexicon_path) if lexicon_path.is_file() else None,
                "lists_sha256": lex.render()["lists_sha256"],
            },
        },
        "method": {
            "unit": "distinct Wikidata item among discovery-gate rows; AIC screened candidate",
            "content_rule": (
                "Protocol 2.1 §7.4 lexicon applied to the Wikidata label and description, the "
                "Commons image description and object name, or the AIC title and subject "
                "titles; the R2 run will use authority fields after reconciliation instead"
            ),
            "authority_proxy": (
                "presence of a Wikidata P195 collection QID; registry membership uses a hand-"
                "curated QID map and unresolved QIDs are listed for later resolution"
            ),
            "limitations": [
                "discovery labels are shorter and noisier than the authority fields R2 will use",
                "rows precede exact-attribution, oil-on-canvas, rights, complete-view, and "
                "physical-work deduplication gates, so every figure is an upper bound",
                "works held privately or without a collection QID cannot reach an authority "
                "record under the closed registry",
            ],
        },
        "floors": floors(),
        "broad_media_r2": broad,
        "aic_r2": aic,
        "evaluation_2_1": _evaluation_2_1(broad),
        "retention_under_2_0": _retention_under_2_0(broad),
    }


# --------------------------------------------------------------------------- report


def _fmt(value: int) -> str:
    return f"{value:,}"


def _yes(value: bool) -> str:
    return "예" if value else "아니오"


def render_markdown(result: Mapping[str, Any]) -> str:
    fl21 = result["floors"]["protocol_2_1"]
    fl20 = result["floors"]["protocol_2_0_by_retained_groups"]
    broad = result["broad_media_r2"]["per_painter"]
    aic = result["aic_r2"]["per_painter"]
    ev = result["evaluation_2_1"]
    ret = result["retention_under_2_0"]
    inputs = result["inputs"]
    lines = [
        "# Painter Feature Generation v1 코퍼스 적정성 사전 스크리닝",
        "",
        "- 상태: 비구속 메타데이터 사전 스크리닝. 프로토콜 수치가 아니며,"
        " 어떤 작품도 입장·배제하지 않는다.",
        "- 정본: Protocol 2.1 (`studies/painter_feature_generation_v1/PROTOCOL_2.1.md`)."
        " 2.0의 장면 셀 규칙은 폐기 근거 기록용으로만 함께 계산한다.",
        f"- 입력: `{inputs['broad_media_candidates']['path']}`"
        f" ({_fmt(inputs['broad_media_candidates']['rows'])}행),"
        f" `{inputs['aic_candidates']['path']}`"
        f" ({_fmt(inputs['aic_candidates']['rows'])}행), 노출 denylist"
        f" ({_fmt(inputs['exposure_denylist']['denylisted_works'])}점),"
        f" §7.4 content lexicon (`{inputs['content_lexicon']['path']}`).",
        "- 생성 명령: `uv run --locked latent-art-bench scene-prescreen`",
        "",
        "## 1. Protocol 2.1이 요구하는 화가당 최소 신규 적격작 수",
        "",
        "| 항목 | 값 |",
        "|---|---:|",
        "| confirmation 필요 (균등 가중이므로 ESS = N) |"
        f" {fl21['confirmation_works_needed_per_painter']} |",
        "| development ≥10을 20% 배정으로 얻기 위한 적격작 |"
        f" {fl21['eligible_for_development_floor']} |",
        "| confirmation ≥100을 60% 배정으로 얻기 위한 적격작 |"
        f" {fl21['eligible_for_confirmation_and_ess_floor']} |",
        f"| 화가당 primary 적격작 하한 | {fl21['eligible_per_painter_primary']} |",
        f"| 보조 독립촬영 패널 | {fl21['auxiliary_independent_capture_works_per_painter']} |",
        f"| **화가당 합계** | **{fl21['eligible_per_painter_total']}** |",
        "",
        "역사적 노출작(denylist)은 development 전용이므로 이 하한에 기여하지 않는다.",
        "",
        "## 2. broad-media R2 manifest의 화가별 상한 (distinct Wikidata item, gate 통과분)",
        "",
        "§7.4 lexicon을 discovery label/description에 적용한 결과다. R2 본 실행은 권위기관"
        " 필드를 쓰므로 수치가 달라진다.",
        "",
        "| 화가 | gate 통과 item | eligible | ineligible | unresolved | 소장 QID 있음 |"
        " eligible & 소장 QID | registry 기관 | 비registry 주요 미술관 | QID 미해결 |"
        " denylist 겹침 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for painter in PAINTERS:
        b = broad[painter]
        d = b["disposition"]
        lines.append(
            f"| {PAINTER_LABELS[painter]} | {_fmt(b['gate_pass_distinct_items'])} |"
            f" {_fmt(d.get(lex.ELIGIBLE, 0))} | {_fmt(d.get(lex.INELIGIBLE, 0))} |"
            f" {_fmt(d.get(lex.UNRESOLVED, 0))} | {_fmt(b['with_collection_qid'])} |"
            f" {_fmt(b['eligible_with_collection_qid'])} | {_fmt(b['registry_institution'])} |"
            f" {_fmt(b['known_non_registry_museum'])} | {_fmt(b['unresolved_collection_qid'])} |"
            f" {_fmt(b['denylisted_items'])} |"
        )
    lines += [
        "",
        "## 3. Protocol 2.1 하한 대비 상한",
        "",
        "| 화가 | eligible & 소장 QID 상한 | 하한(보조 포함) | 여유 | 상한에서 통과 |",
        "|---|---:|---:|---:|---|",
    ]
    for painter in PAINTERS:
        row = ev["per_painter"][painter]
        lines.append(
            f"| {PAINTER_LABELS[painter]} |"
            f" {_fmt(row['upper_bound_eligible_with_collection_qid'])} |"
            f" {row['floor_including_auxiliary']} | {row['margin_at_upper_bound']:+d} |"
            f" {_yes(row['clears_floor_at_upper_bound'])} |"
        )
    weakest = PAINTER_LABELS[ev["weakest_painter"]]
    if ev["all_painters_clear_at_upper_bound"]:
        verdict = (
            f"상한에서는 네 화가 모두 하한을 넘는다. 최약 화가는 {weakest}이며, 권위검증·"
            "중복제거·완전화면·사적 소장 제외 후 실제 수치는 더 낮아지므로 R2 종료 시 NO-GO"
            " 가능성이 남아 있다."
        )
    else:
        verdict = (
            f"상한에서조차 {weakest}이(가) 하한에 미치지 못한다. 현재 수치대로면 연구는 R2 후"
            " 중단된다."
        )
    lines += [
        "",
        verdict,
        "",
        "## 4. 폐기된 Protocol 2.0 장면 셀 규칙의 기록",
        "",
        "| 유지 장면 수 G | 셀당 적격작 하한 | 화가당 합계 |",
        "|---|---:|---:|",
    ]
    for key in ("G=3", "G=4"):
        lines.append(
            f"| {key} | {fl20[key]['eligible_per_cell']} |"
            f" {fl20[key]['eligible_per_painter_total']} |"
        )
    lines += [
        "",
        "| 장면 클래스 | "
        + " | ".join(PAINTER_LABELS[p] for p in PAINTERS)
        + " | 최약 화가 | G=3 하한 통과 |",
        "|---|" + "---:|" * len(PAINTERS) + "---|---|",
    ]
    for scene in SCENES:
        row = ret["per_scene"][scene]
        cells = " | ".join(_fmt(row["upper_bound_by_painter"][p]) for p in PAINTERS)
        lines.append(
            f"| `{scene}` | {cells} | {PAINTER_LABELS[row['weakest_painter']]} |"
            f" {_yes(row['clears_floor_if_three_groups_retained'])} |"
        )
    cleared = len(ret["groups_clearing_three_group_floor"])
    lines += [
        "",
        f"2.0 규칙으로는 G=3 하한을 통과하는 장면이 {cleared}개였고, 이것이 2.1이 장면 층화를"
        " 제거한 근거다.",
        "",
        "## 5. AIC R2 screened 후보의 §7.4 판정",
        "",
        "| 화가 | screened | eligible | ineligible | unresolved | denylist 겹침 |"
        " eligible·비노출 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for painter in PAINTERS:
        a = aic[painter]
        d = a["screened_disposition"]
        lines.append(
            f"| {PAINTER_LABELS[painter]} | {a['screened_candidates']} |"
            f" {d.get(lex.ELIGIBLE, 0)} | {d.get(lex.INELIGIBLE, 0)} |"
            f" {d.get(lex.UNRESOLVED, 0)} | {a['screened_denylisted']} |"
            f" {a['screened_eligible_not_denylisted']} |"
        )
    lines += [
        "",
        "## 6. 해석과 한계",
        "",
        "- discovery label은 R2가 사용할 권위기관 필드보다 짧고 잡음이 많다. 실제 판정은 권위"
        " reconciliation 후 같은 lexicon으로 한 번만 수행한다.",
        "- 위 모든 수치는 exact attribution, oil-on-canvas, 권리, 완전화면, 물리작품 중복제거"
        " 이전의 상한이다. 실제 수치는 더 낮다.",
        "- 소장 QID가 없거나 사적 소장인 item은 닫힌 registry 아래에서 권위기록에 도달할 수 없다.",
        "- 이 문서는 어떤 작품도 입장시키지 않는다.",
        "",
        "## 7. 미해결 소장 QID 상위 목록",
        "",
        "| QID | gate 통과 item |",
        "|---|---:|",
    ]
    for row in result["broad_media_r2"]["top_unresolved_collection_qids"]:
        lines.append(f"| {row['qid']} | {_fmt(row['gate_pass_items'])} |")
    lines.append("")
    return "\n".join(lines)


def write(root: Path) -> Dict[str, Any]:
    result = run(root)
    json_path = root / OUTPUT_JSON
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md_path = root / OUTPUT_MD
    md_path.write_text(render_markdown(result), encoding="utf-8")
    return {
        "json_path": str(OUTPUT_JSON),
        "json_sha256": hash_file(json_path),
        "markdown_path": str(OUTPUT_MD),
        "protocol_2_1_all_painters_clear_at_upper_bound": result["evaluation_2_1"][
            "all_painters_clear_at_upper_bound"
        ],
        "protocol_2_1_per_painter": {
            painter: row["upper_bound_eligible_with_collection_qid"]
            for painter, row in result["evaluation_2_1"]["per_painter"].items()
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(write(args.root.resolve()), indent=2, sort_keys=True))
    return 0
