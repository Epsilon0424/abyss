"""쿠키 공통 스탯 데이터.

이 파일에는 계산식에서 자주 쓰는 숫자와 설탕유리조각 처리 함수를 모아둔다.
- 설탕유리조각 증가량
- 잠재력 증가량
- 쿠키별 호감도 공격력

주의:
`atk_with_friendship()` 계열 헬퍼는 기존 계산값을 바꾸지 않고,
각 쿠키 파일에서 `+ 54.0`처럼 직접 더하던 호감도 공격력을
한곳에서 확인할 수 있게 만든 용도다.
"""

from typing import Dict, List, Optional

from .catalog import COOKIE_ROLE

NORMAL_SLOTS = 41

SHARD_INC = {
    "crit_rate": 0.048,
    "crit_dmg": 0.08,
    "all_elem_dmg": 0.048,
    "basic_dmg": 0.048,
    "special_dmg": 0.048,
    "ult_dmg": 0.048,
    "passive_dmg": 0.048,
    "atk_pct": 0.064,
    "elem_atk": 24,
    "def_pct": 0.04,
    "shield_pct": 0.032,
    "heal_pct": 0.032,
}

SHARD_KR = {
    "crit_rate": "치명타 확률",
    "crit_dmg": "치명타 피해",
    "all_elem_dmg": "모든 속성 피해",
    "basic_dmg": "기본 공격 피해",
    "special_dmg": "특수 스킬 피해",
    "ult_dmg": "궁극기 피해",
    "passive_dmg": "패시브 스킬 피해",
    "atk_pct": "공격력 %",
    "elem_atk": "속성 공격력",
    "def_pct": "방어력 %",
    "shield_pct": "보호막 %",
    "heal_pct": "회복량 %",
}

POTENTIAL_INC = {
    "atk_pct": 0.20,
    "crit_rate": 0.15,
    "crit_dmg": 0.25,
    "armor_pen": 0.08,
    "elem_atk": 80,
    "atk_flat": 0.0,
    "buff_amp": 0.10,
    "debuff_amp": 0.10,
}

POTENTIAL_KR = {
    "atk_pct": "공격력 %",
    "crit_rate": "치명타 확률",
    "crit_dmg": "치명타 피해",
    "armor_pen": "방어력 관통",
    "elem_atk": "속성 공격력",
    "buff_amp": "버프 증폭",
    "debuff_amp": "디버프 증폭",
}

# =====================================================
# 일반 설탕유리조각 세트효과(유니크 8칸 제외 / 일반 41칸)
# =====================================================
SUGAR_GLASS_DEFAULT_ALLOC = {
    "dps": {"광휘": 20, "관통": 21},
    "strike": {"원소": 20, "파쇄": 21},
    "support": {"축복": 20, "낙인": 21},
}

def _sugar_tier(slots: int) -> int:
    slots = int(slots or 0)
    if slots >= 21: return 21
    if slots >= 18: return 18
    if slots >= 15: return 15
    if slots >= 12: return 12
    if slots >= 9: return 9
    return 0

def sugar_glass_default_alloc_for_cookie(cookie_name_kr: str) -> Dict[str, int]:
    # 달빛술사는 역할 기준으로 서포터 일반 설탕유리조각 세트(축복/낙인)를 사용한다.
    # 단, moonlight.py의 41칸 일반 조각 최적화 후보는 딜러형 피해 스탯 축으로 구성한다.
    role = COOKIE_ROLE.get(cookie_name_kr, "")
    return dict(SUGAR_GLASS_DEFAULT_ALLOC.get(role, {}))

def sugar_glass_alloc_text(cookie_name_kr: str) -> str:
    alloc = sugar_glass_default_alloc_for_cookie(cookie_name_kr)
    if not alloc:
        return ""
    return " / ".join(f"{name} {slots}칸" for name, slots in alloc.items())

def short_cookie_name(cookie_name_kr: str) -> str:
    name = str(cookie_name_kr or "").strip()
    if name.endswith("맛 쿠키"):
        return name[:-4].strip()
    if name.endswith(" 쿠키"):
        return name[:-3].strip()
    if name.endswith("맛"):
        return name[:-1].strip()
    return name

def sugar_glass_party_rows(main_cookie_name: str, party: Optional[List[str]] = None) -> List[str]:
    rows: List[str] = []
    main_txt = sugar_glass_alloc_text(main_cookie_name)
    main_label = short_cookie_name(main_cookie_name)
    if main_txt and main_label:
        rows.append(f"{main_label}: {main_txt}")
    for pc in (party or []):
        txt = sugar_glass_alloc_text(pc)
        label = short_cookie_name(pc)
        if txt and label:
            rows.append(f"{label}: {txt}")
    return rows

def sugar_glass_party_text(main_cookie_name: str, party: Optional[List[str]] = None) -> str:
    rows = sugar_glass_party_rows(main_cookie_name, party)
    return "\n".join(rows) if rows else ""

def _apply_sugar_glass_one(stats: Dict[str, float], cookie_name_kr: str, *, is_owner: bool = False) -> None:
    role = COOKIE_ROLE.get(cookie_name_kr, "")
    alloc = sugar_glass_default_alloc_for_cookie(cookie_name_kr)
    if not alloc:
        return

    if role == "dps" and is_owner:
        shine = _sugar_tier(alloc.get("광휘", 0))
        pierce = _sugar_tier(alloc.get("관통", 0))
        if shine >= 21:
            stats["sugar_brilliance_coeff"] = float(stats.get("sugar_brilliance_coeff", 0.0)) + 15.0
        elif shine >= 18:
            stats["sugar_brilliance_coeff"] = float(stats.get("sugar_brilliance_coeff", 0.0)) + 12.0
        if pierce >= 21:
            stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + 0.15
        elif pierce >= 18:
            stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + 0.12
        return

    if role == "strike":
        elem = _sugar_tier(alloc.get("원소", 0))
        crush = _sugar_tier(alloc.get("파쇄", 0))
        if elem >= 21:
            stats["sugar_mark_crit_rate"] = max(float(stats.get("sugar_mark_crit_rate", 0.0)), 1.00)
            stats["sugar_mark_crit_dmg"] = max(float(stats.get("sugar_mark_crit_dmg", 0.0)), 0.20)
        elif elem >= 18:
            stats["sugar_mark_crit_rate"] = max(float(stats.get("sugar_mark_crit_rate", 0.0)), 0.90)
            stats["sugar_mark_crit_dmg"] = max(float(stats.get("sugar_mark_crit_dmg", 0.0)), 0.20)
        if crush >= 21:
            v = 0.06
        elif crush >= 18:
            v = 0.04
        else:
            v = 0.0
        if v:
            # 파쇄 세트효과는 속성 강타 발생 시 유지되는 고정 세트효과로 본다.
            # 따라서 지속시간 평균 보정 없이 원값을 적용하고, 메인 쿠키의 디버프 증폭도 곱하지 않는다.
            stats["elem_res_reduction_no_scale_raw"] = (
                float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + v
            )
            stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + v
        return

    if role == "support":
        bless = _sugar_tier(alloc.get("축복", 0))
        mark = _sugar_tier(alloc.get("낙인", 0))
        regen = _sugar_tier(alloc.get("재생", 0))
        bless_map = {9: 0.04, 12: 0.08, 15: 0.12, 18: 0.16, 21: 0.20}
        mark_map = {9: 0.02, 12: 0.04, 15: 0.06, 18: 0.08, 21: 0.10}
        regen_map = {9: 0.025, 12: 0.05, 15: 0.075, 18: 0.10, 21: 0.125}
        if bless in bless_map:
            # 서포터 축복 세트 효과
            # - 파티 서포터가 메인딜러에게 주는 공격 버프
            # - 공격력%가 아니라 공격력 증가% 축으로 반영
            v = bless_map[bless]
            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + v
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + v
        if mark in mark_map:
            # 낙인 세트효과도 고정 세트효과이므로 디버프 증폭을 적용하지 않는다.
            stats["elem_res_reduction_no_scale_raw"] = (
                float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + mark_map[mark]
            )
        if regen in regen_map:
            # 서포터 재생 세트 효과
            # - 공격력%가 아니라 공격력 증가% 축으로 반영
            # - 치명타 피해는 기존처럼 치피 축으로 반영
            # - 평균 유지율: 18초 / 30초 = 0.6
            v = regen_map[regen] * (18.0 / 30.0)

            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + v
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + v
            stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + v

def apply_sugar_glass_set_effects(stats: Dict[str, float], main_cookie_name: str, party: Optional[List[str]] = None) -> None:
    stats.setdefault("sugar_brilliance_coeff", 0.0)
    stats.setdefault("sugar_mark_crit_rate", 0.0)
    stats.setdefault("sugar_mark_crit_dmg", 0.0)
    stats["sugar_glass_rows"] = sugar_glass_party_rows(main_cookie_name, party or [])
    _apply_sugar_glass_one(stats, main_cookie_name, is_owner=True)
    for pc in (party or []):
        if pc and pc != main_cookie_name:
            _apply_sugar_glass_one(stats, pc, is_owner=False)

# =====================================================
# 쿠키별 호감도 공격력
# =====================================================
FRIENDSHIP_ATK = {
    "피닉스페퍼 쿠키": 54.0,
    "멜랑크림 쿠키": 57.0,
    "윈드파라거스 쿠키": 51.0,
    "샬롯맛 쿠키": 48.0,
    "이슬맛 쿠키": 48.0,
    "룽샤맛 쿠키": 54.0,
    "마블베리맛 쿠키": 54.0,
    "흑보리맛 쿠키": 38.0,
    "체리콜라맛 쿠키": 54.0,
    "블루멜로우맛 쿠키": 57.0,
    "네온데니쉬맛 쿠키": 42.0,
    "샤이닝베리맛 쿠키": 60.0,
    "달빛술사 쿠키": 57.0,
    "밀키웨이맛 쿠키": 48.0,
    "스타더스트 쿠키": 54.0,
}

def friendship_atk_for(cookie_name: str) -> float:
    """쿠키별 호감도 공격력."""
    return float(FRIENDSHIP_ATK.get(cookie_name, 0.0))

def atk_without_friendship(base_atk_without_friendship: float) -> float:
    """호감도 공격력이 빠진 기본 공격력을 그대로 반환한다."""
    return float(base_atk_without_friendship)

def atk_from_promoted_base_without_friendship(promoted_atk_without_friendship: float, promo_atk_pct: float) -> float:
    """승급 공격력%가 반영된 표기 공격력을 역산한다.

    호감도 공격력은 여기서 더하지 않는다.
    최종 공격력 공식의 마지막 `+ 호감도공` 단계에서만 더한다.
    """
    return float(promoted_atk_without_friendship) / (1.0 + float(promo_atk_pct))

# 이전 이름 호환용. 새 코드에서는 아래 두 함수명을 쓰는 것을 권장한다.
def atk_with_friendship(base_atk_without_friendship: float, cookie_name: str) -> float:
    return atk_without_friendship(base_atk_without_friendship)

def atk_from_promoted_base(promoted_atk_without_friendship: float, promo_atk_pct: float, cookie_name: str | None = None) -> float:
    return atk_from_promoted_base_without_friendship(promoted_atk_without_friendship, promo_atk_pct)
