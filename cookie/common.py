# =====================================================
# 가져오기
# =====================================================
from typing import Dict, List, Tuple, Optional, Callable, Union, Iterator
import math

from .stat_data import *
from .catalog import *
from .equipment_data import *
from .seaz_data import *
from .artifact_data import *
from .unique_data import *

# =====================================================
# 0) 전역 설정(토글/상수)
# =====================================================

# =====================================================
# 0.0) 업타임 모드
# =====================================================
# 상수
# =====================================================
MODE_ALWAYS  = "ALWAYS"    # 항상 켜짐(업타임 1.0)
MODE_AVERAGE = "AVERAGE"   # 지속시간/재사용 대기시간 평균 업타임
MODE_TRIGGER = "TRIGGER"   # 기대 업타임 직접값 또는 발동 간격 근사
MODE_CUSTOM  = "CUSTOM"    # 사용자 고정값

UPTIME_CONFIG = {
    # 이슬: 파티 치피 +56%
    "PARTY_ISLE_CRITDMG_0p56": {"mode": MODE_ALWAYS},

    # 이슬: 파티 공퍼 +22.4%
    "PARTY_ISLE_ATK_0p224": {"mode": MODE_ALWAYS},

    # 이슬: 시즈로 최종공 +25%, 모속피 +30%
    "PARTY_ISLE_SEAZ_ATK25_ALL30": {
        "mode": MODE_ALWAYS,
        "duration": 15.0,
        "cooldown": 25.0,
    },

    # 윈파: 파티 치피 +40%
    "PARTY_WIND_CRITDMG_0p40": {"mode": MODE_ALWAYS},

    # 윈파 시즈 브리더 효과
    "WIND_SEAZ_BREEDER_EFFECT": {"mode": MODE_ALWAYS},
}

# =====================================================
# 0.1) 전역 플래그/기본 가정 상수
# =====================================================

BOSS_MARK_ELEMENT_RESIST_DEFAULT = 0.40

# =====================================================
# 0.1-2) 쿠키별 승급 상수
# =====================================================
# - 공통 계산용 승급 상수 복제
MELAN_PROMO_ENABLED = True
MELAN_PROMO_CRIT_RATE_MULT = 1.0
MELAN_PROMO_ARMOR_PEN_MULT = 1.0
MELAN_PROMO_ATK_PCT_MULT   = 1.0
MELAN_PROMO_FINAL_DMG_MULT = 1.0
MELAN_PROMO_PRIMA_DMG_MULT = 1.25

WIND_PROMO_ENABLED = True
WIND_PROMO_CRIT_RATE_MULT = 1.0
WIND_PROMO_ATK_PCT_MULT   = 1.0
WIND_PROMO_FINAL_DMG_MULT = 1.0
WIND_PROMO_DEF_PCT_MULT   = 1.08
WIND_PROMO_HP_PCT_MULT    = 1.08

BLACK_BARLEY_PROMO_ENABLED = True
BLACK_BARLEY_PROMO_CRIT_RATE_MULT    = 1.0
BLACK_BARLEY_PROMO_BASE_ATK_MULT     = 1.0
BLACK_BARLEY_PROMO_DEF_PCT_MULT      = 1.0
BLACK_BARLEY_PROMO_HP_PCT_MULT       = 1.0
BLACK_BARLEY_PROMO_SPECIAL_DMG_ADD   = 0.20
BLACK_BARLEY_PROMO_ULT_DMG_ADD       = 0.20
BLACK_BARLEY_PROMO_BASIC_DMG_ADD     = 0.30

SHINING_BERRY_PROMO_ENABLED = True
SHINING_BERRY_PROMO_CRIT_RATE_MULT   = 1.0
SHINING_BERRY_PROMO_SPECIAL_DMG_ADD  = 0.20
SHINING_BERRY_PROMO_ULT_DMG_ADD      = 0.20

PHOENIX_PEPPER_PROMO_ENABLED = True
PHOENIX_PEPPER_PROMO_ULT_DMG_MULT = 1.45
PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT = 1.80

# =====================================================
# 0.2) 설탕셋(달콤한 설탕 깃털) 발동형 옵션
# =====================================================
SUGAR_SET_PROC_CHANCE = 0.20
SUGAR_SET_PROC_ATK_COEFF = 0.50

# =====================================================
# 0.4) 전투/공식 파라미터
# =====================================================
DEFENSE_K = 3.0
DEF_REDUCTION_CAP = 0.70  # 방어력 감소 상한 70%

# ---- 속성강타(표식) 모델
# - 정식식:
# 표식에 들어간 총 데미지
# × 기본 속성강타 계수
# × 표식 속성 내성 배율
# × (1 + 속성강타 피해 증가)
# - 표식 속성 내성 배율 = 1 - (보스 기본 속성 내성 - 속성 내성 감소)
# - 속성 내성 변동 세팅 0.566 간이계수 제외
ELEMENT_STRIKE_BASE_COEFF = 0.712

# =====================================================
# 1) 공통: 설탕유리조각(41칸) / 잠재력(8칸)
# =====================================================
ELEMENT_POTENTIAL_SYNERGY_ENABLED = True
ELEMENT_POTENTIAL_SYNERGY_ALL_ELEM_DMG = 0.30  # +30%
ELEMENT_POTENTIAL_SYNERGY_ELEM_ATK = 20.0      # +20

# 설탕유리조각·잠재력·호감도 공격력 데이터 분리

# =====================================================
# 2) 공통: 유틸 함수(기본/누적/업타임/복사)
# =====================================================

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def get_uptime(key: str) -> float:
    """업타임 계산"""
    cfg = UPTIME_CONFIG.get(key, {"mode": MODE_ALWAYS})
    mode = cfg.get("mode", MODE_ALWAYS)

    if mode == MODE_ALWAYS:
        return 1.0

    if mode == MODE_AVERAGE:
        dur = float(cfg.get("duration", 0.0))
        cd  = float(cfg.get("cooldown", 1.0))
        if cd <= 0:
            return 1.0
        return clamp(dur / cd, 0.0, 1.0)

    if mode == MODE_TRIGGER:
        if "expected_uptime" in cfg:
            return clamp(float(cfg["expected_uptime"]), 0.0, 1.0)
        dur = float(cfg.get("duration", 0.0))
        interval = float(cfg.get("proc_interval", 1.0))
        if interval <= 0:
            return 1.0
        return clamp(dur / interval, 0.0, 1.0)

    if mode == MODE_CUSTOM:
        return clamp(float(cfg.get("value", 1.0)), 0.0, 1.0)

    return 1.0

def add_stat(stats: Dict[str, float], k: str, v: float) -> None:
    stats[k] = stats.get(k, 0.0) + float(v)

def add(stats: Dict[str, float], bonus: Dict[str, float]) -> None:
    """스탯 누적"""
    for k, v in (bonus or {}).items():
        add_stat(stats, k, float(v))

EPS_CR = 1e-12

# =====================================================
# 3) 공통 데이터(쿠키/속성/직업/형태/쿨/타수)
# =====================================================

# 쿠키 속성·타입·역할 분류 데이터 분리

# =====================================================
# 4) 잎새의 활강
# =====================================================

LEAF_GLIDE_RES_RED_PER_STACK = 0.0056   # 0.56%
LEAF_GLIDE_BASE_MAX_STACKS   = 40
WIND_PROMO_LEAF_GLIDE_MAX_STACK_ADD = 10

LEAF_GLIDE_FINALDMG_PER_DEBUFFAMP = 1.25
LEAF_GLIDE_FINALDMG_CAP = 1.0

# =====================================================
# 효과 및 버프 반영
# =====================================================
def apply_leaf_glide(stats: Dict[str, float], party: List[str], main_cookie_name: str):
    has_wind_in_team = ("윈드파라거스 쿠키" in (party or [])) or (main_cookie_name == "윈드파라거스 쿠키")
    if not has_wind_in_team:
        return stats

    applied = stats.setdefault("_applied_enemy_debuffs", set())
    if "LEAF_GLIDE" in applied:
        return stats

    # 1) 공유 적 속성 내성 감소
    # - 윈파 메인: 본인 디버프 증폭 적용
    # - 파티 윈파: 메인 쿠키 디버프 증폭 제외
    # 윈파 개인 디버프 증폭 선반영 후 비증폭 축 적용
    max_stacks = LEAF_GLIDE_BASE_MAX_STACKS + (WIND_PROMO_LEAF_GLIDE_MAX_STACK_ADD if WIND_PROMO_ENABLED else 0)
    stacks = max_stacks
    base_res_red = LEAF_GLIDE_RES_RED_PER_STACK * stacks
    if main_cookie_name == "윈드파라거스 쿠키":
        stats["elem_res_reduction_raw"] = float(stats.get("elem_res_reduction_raw", 0.0)) + base_res_red
    else:
        wind_da = stats.get("_wind_leaf_glide_owner_debuff_amp", None)
        if wind_da is None:
            # 파티 버프 미경유 기본값
            # 기본 디버프 증폭 합계 80%
            wind_da = _assumed_wind_debuff_amp_for_party() + 0.15
        stats["elem_res_reduction_no_scale_raw"] = (
            float(stats.get("elem_res_reduction_no_scale_raw", 0.0))
            + base_res_red * (1.0 + float(wind_da))
        )

    # 2) 본인 전용 잎새의 활강 최종 피해
    if main_cookie_name == "윈드파라거스 쿠키":
        # [본인 전용] 창공을 가르는 자유의 최종피해 증가는
        # 파티 총 디버프 증폭이 아니라 윈드파라거스 본인의 디버프 증폭 스냅샷만 사용
        # 파티 버프 적용 후 디버프 증폭: 파티 장비·유니크 포함
        # 파티 합산 전 본인 디버프 증폭 우선
        da = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))
        add_final = min(LEAF_GLIDE_FINALDMG_CAP, LEAF_GLIDE_FINALDMG_PER_DEBUFFAMP * da)
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + add_final

    applied.add("LEAF_GLIDE")
    return stats

# =====================================================
# 5) 공통: 장비 세트
# =====================================================
# 장비 세트 데이터 분리

# =====================================================
# 6) 공통: 시즈나이트
# =====================================================

# 시즈나이트 데이터 분리

# =====================================================
# 6.5) 시즈 패시브 반영
# =====================================================
# - 회복량 증가
# - 아군 모든 속성 피해 → 버프 증폭·업타임 적용 축
# =====================================================

def apply_seaz_passive(
    stats: Dict[str, float],
    seaz_name: str,
    uptime_key_prefix: str = "SEAZ_PASSIVE::",
    *,
    owner_cookie_name: Optional[str] = None,   # 이 시즈의 소유자
    main_cookie_name: Optional[str] = None,    # 지금 메인 쿠키
) -> Dict[str, float]:
    info = SEAZNITES.get(seaz_name)
    if not info:
        return stats

    # 이슬맛 쿠키는 "작은 성배 / 가벼운 손길" 사용 시
    # 시즈 보조 옵션 전용
    if owner_cookie_name == "이슬맛 쿠키" and isinstance(seaz_name, str):
        if seaz_name.endswith(":작은 성배") or seaz_name.endswith(":가벼운 손길"):
            return stats

    passive = dict(info.get("passive", {}) or {})

    # 백마법사의 의지 보정
    # - 달빛술사: 플럼나이트 원값(공격력 25% / 모든 속성 피해 30%) 유지
    # - 기타 쿠키: 공격력 12.5%·모든 속성 피해 15%
    # 허브그린드는 원래 12.5%/15%라 그대로이고, 플럼나이트만 해당 값으로 보정
    if isinstance(seaz_name, str) and seaz_name.endswith(":백마법사의 의지") and owner_cookie_name != "달빛술사 쿠키":
        if "atk_pct" in passive:
            passive["atk_pct"] = min(float(passive["atk_pct"]), 0.125)
        if "ally_all_elem_dmg" in passive:
            passive["ally_all_elem_dmg"] = min(float(passive["ally_all_elem_dmg"]), 0.15)

    key = f"{uptime_key_prefix}{seaz_name}"
    u = get_uptime(key)

    # 회복량 증가: 버프 증폭 제외
    if "heal_pct" in passive:
        stats["heal_pct"] = float(stats.get("heal_pct", 0.0)) + float(passive["heal_pct"]) * u

    # 아군 모든 속성 피해: 버프 증폭 제외
    if "ally_all_elem_dmg" in passive:
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(passive["ally_all_elem_dmg"]) * u

    # 방어 관통: 버프 증폭 제외
    if "armor_pen" in passive:
        stats["buff_armor_pen_raw"] = float(stats.get("buff_armor_pen_raw", 0.0)) + float(passive["armor_pen"]) * u

    # 공격력% 기본 최종공격력 축, 샬롯·이슬 자기 시즈 일반 공격력% 축
    if "atk_pct" in passive:
        addv = float(passive["atk_pct"]) * u

        is_owner_main = (owner_cookie_name is not None) and (main_cookie_name is not None) and (owner_cookie_name == main_cookie_name)
        is_support_main = (main_cookie_name in ("샬롯맛 쿠키", "이슬맛 쿠키", "달빛술사 쿠키"))

        if is_owner_main and is_support_main:
            # 서폿이 메인일 때 자기 시즈 공퍼는 "공격력%" 축으로
            stats["atk_pct"] = float(stats.get("atk_pct", 0.0)) + addv
        else:
            # 그 외 시즈 공격력 증가는 최종공격력 축으로 반영
            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + addv
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + addv

    # 속성 강타 피해: 버프 증폭 제외·파티 공유
    if "element_strike_dmg" in passive:
        stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + float(passive["element_strike_dmg"]) * u

    # 시즈: 모든 스킬 피해
    # - 막힘없는 성장: 궁극기 사용 시 모든 스킬 피해 +25% / 30초
    # - 현재 시뮬에서는 30초 효과를 1사이클 상시값으로 반영
    # - 기본/특수/궁극기/패시브 피해 축에 같은 수치 추가
    if "all_skill_dmg" in passive:
        addv = float(passive["all_skill_dmg"]) * u
        for kk in ("basic_dmg", "special_dmg", "ult_dmg", "passive_dmg"):
            stats[kk] = float(stats.get(kk, 0.0)) + addv

    # 시즈: 직접 모든 속성 피해
    # - 치열한 선봉자: 6% × 5중첩 = 30%
    # - 벞증/디벞증 영향 없음
    if "all_elem_dmg" in passive:
        stats["all_elem_dmg"] = float(stats.get("all_elem_dmg", 0.0)) + float(passive["all_elem_dmg"]) * u

    # 시즈: 모든 아군 공격력 증가
    # - 번뜩이는 기지: 공격력 증가 +10%
    # - 달빛의 속삭임: 공격력 증가 +12% × 3중첩 = +36%
    # - 버프 공격력 축 반영
    if "ally_final_atk_mult" in passive:
        addv = float(passive["ally_final_atk_mult"]) * u
        # 달빛의 속삭임 최대 3중첩
        # 최대 중첩 유지 36%
        if owner_cookie_name == "달빛술사 쿠키" and str(seaz_name).endswith(":달빛의 속삭임"):
            addv *= 3.0
        stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + addv
        stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + addv

    # 시즈: 모든 아군 치명타 피해
    # - 번뜩이는 기지: 치명타 피해 +30%
    # - 벞증/디벞증 영향 없음
    if "ally_crit_dmg" in passive:
        stats["crit_dmg"] = float(stats.get("crit_dmg", 0.0)) + float(passive["ally_crit_dmg"]) * u

    # 시즈: 본인 전용 증폭량 -> 모든 속성 피해 변환
    # - 달빛의 속삭임: 증폭 합계만큼 모든 속성 피해 증가
    # - 최대 100%
    # - 본인만 적용, 파티원 장착 시 메인에게 공유하지 않음
    is_owner_main = (owner_cookie_name is not None) and (main_cookie_name is not None) and (owner_cookie_name == main_cookie_name)
    if is_owner_main and "self_amp_to_all_elem_cap" in passive:
        cap = float(passive.get("self_amp_to_all_elem_cap", 1.0))
        # 본인 전용 증폭 합계
        ba = float(stats.get("self_buff_amp_total", stats.get("buff_amp_total", stats.get("buff_amp", 0.0))))
        da = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))
        addv = min(cap, max(0.0, ba + da)) * u
        stats["all_elem_dmg"] = float(stats.get("all_elem_dmg", 0.0)) + addv

    return stats

# =====================================================
# 7) 공통: 아티팩트
# =====================================================

# 아티팩트 데이터 분리

def apply_artifact(stats: Dict[str, float], artifact_name: str) -> None:
    a = ARTIFACTS.get(artifact_name, ARTIFACTS["NONE"])

    # 1) 기본 옵션·고유 스탯
    add(stats, a.get("base_stats", {}))
    add(stats, a.get("unique_stats", {}))

    # 2) 고유 버프
    ub = a.get("unique_buffs", {}) or {}

    if "atk_pct" in ub:
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(ub["atk_pct"])
    if "crit_rate" in ub:
        stats["buff_crit_rate_raw"] = float(stats.get("buff_crit_rate_raw", 0.0)) + float(ub["crit_rate"])
    if "crit_dmg" in ub:
        stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + float(ub["crit_dmg"])
    if "all_elem_dmg" in ub:
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(ub["all_elem_dmg"])

    # 최종 공격력·피해 증가·최종 피해 버프 증폭 제외
    if "final_atk_mult" in ub:
        stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + float(ub["final_atk_mult"])
    if "dmg_bonus" in ub:
        stats["dmg_bonus"] = float(stats.get("dmg_bonus", 0.0)) + float(ub["dmg_bonus"])
    if "final_dmg" in ub:
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + float(ub["final_dmg"])

    meta_bb = a.get("black_barley", None)
    if meta_bb:
        stats.setdefault("_bb_black_bullet_dmg_bonus_raw", 0.0)
        stats.setdefault("_bb_next8_shot_dmg_bonus_raw", 0.0)
        if "black_bullet_dmg" in meta_bb:
            stats["_bb_black_bullet_dmg_bonus_raw"] += float(meta_bb["black_bullet_dmg"])
        if "next8_shot_dmg" in meta_bb:
            stats["_bb_next8_shot_dmg_bonus_raw"] += float(meta_bb["next8_shot_dmg"])

# =====================================================
# 8) 공통 유니크 설탕유리조각
# =====================================================

# 유니크 설탕유리조각 데이터 분리

# =====================================================
# 유니크 조각 허용 판정
# =====================================================
def is_unique_allowed(cookie_name_kr: str, unique_name: str) -> bool:
    u = UNIQUE_SHARDS[unique_name]
    roles = u.get("allowed_roles", ["any"])
    types = u.get("allowed_types", ["any"])

    if "any" in roles and "any" in types:
        return True

    role = COOKIE_ROLE.get(cookie_name_kr, "unknown")
    ctype = COOKIE_TYPE.get(cookie_name_kr, "unknown")

    role_ok = ("any" in roles) or (role in roles)
    type_ok = ("any" in types) or (ctype in types)
    return role_ok and type_ok

# =====================================================
# 유니크 조각 효과 적용
# - 장착자 본인 적용
# - 파티원 유니크: 공유 스탯만 합산, 본인 전용 효과 제외
# =====================================================
def apply_unique(
    stats: Dict[str, float],
    cookie_name_kr: str,
    unique_name: str,
    *,
    is_owner: bool = True,
) -> None:
    if unique_name not in UNIQUE_SHARDS:
        return

    u = UNIQUE_SHARDS[unique_name]
    ut = u.get("type", "none")
    if ut == "none":
        return

    if not is_unique_allowed(cookie_name_kr, unique_name):
        return

    # ---- 안전키 ----
    stats.setdefault("unique_extra_coeff", 0.0)
    stats.setdefault("buff_armor_pen_raw", 0.0)
    stats.setdefault("buff_atk_pct_raw", 0.0)
    stats.setdefault("buff_crit_dmg_raw", 0.0)
    stats.setdefault("buff_all_elem_dmg_raw", 0.0)

    stats.setdefault("element_strike_dmg", 0.0)
    stats.setdefault("element_mark_explosion_dmg", 0.0)
    stats.setdefault("final_dmg", 0.0)
    stats.setdefault("dmg_bonus", 0.0)

    stats.setdefault("buff_amp", 0.0)
    stats.setdefault("debuff_amp", 0.0)
    stats.setdefault("party_buff_amp_total", float(stats.get("buff_amp", 0.0)))
    stats.setdefault("party_debuff_amp_total", float(stats.get("debuff_amp", 0.0)))

    # (1) 속성강타피해 기본옵션: 파티 전체
    sd_add = float(u.get("strike_dmg_add", 0.0))
    if sd_add:
        stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + sd_add

    # (2) 버프증폭 기본옵션
    # - 로드 나이트메어의 기억: 공격력 15%·버프 증폭 36%
    ba_map = u.get("buff_amp_add_by_cookie", {}) or {}
    ba_add = float(ba_map.get(cookie_name_kr, u.get("buff_amp_add", 0.0)))
    if ba_add:
        stats["buff_amp"] = float(stats.get("buff_amp", 0.0)) + ba_add
        stats["party_buff_amp_total"] = float(stats.get("party_buff_amp_total", 0.0)) + ba_add

    # (3) 디버프 증폭 기본 옵션 파티 공유
    da_map = u.get("debuff_amp_add_by_cookie", {}) or {}
    da_add = float(da_map.get(cookie_name_kr, u.get("debuff_amp_add", 0.0)))
    if da_add:
        stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + da_add
        stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + da_add

    # (4) 최종피해 기본옵션: 본인만
    fd_add = float(u.get("final_dmg_add", 0.0))
    if fd_add and is_owner:
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + fd_add

    # =====================================================
    # 유니크 조각 타입별 효과
    # =====================================================

    # 피해량 유니크 본인 전용
    if ut == "dps_type_damage":
        if not is_owner:
            return
        # 사격·마법·베기·타격 피해 공통 피해량 축 합산
        stats["dmg_bonus"] = float(stats.get("dmg_bonus", 0.0)) + float(u.get("type_damage_add", 0.0))
        return

    if ut == "dps_proc_type_damage":
        if not is_owner:
            return
        stats["dmg_bonus"] = float(stats.get("dmg_bonus", 0.0)) + float(u.get("type_damage_add", 0.0))
        stats["unique_extra_coeff"] = float(stats.get("unique_extra_coeff", 0.0)) + float(u.get("proc_coeff_per_sec", 0.0))
        return

    if ut == "dps_proc":
        if not is_owner:
            return
        stats["unique_extra_coeff"] = float(stats.get("unique_extra_coeff", 0.0)) + float(u.get("proc_coeff_per_sec", 0.0))
        return

    if ut == "dps_hit_proc":
        if not is_owner:
            return
        stats["dmg_bonus"] = float(stats.get("dmg_bonus", 0.0)) + float(u.get("avg_dmg_bonus", 0.0))
        return

    if ut == "dps_ultimate_atk":
        if not is_owner:
            return
        # 여행자자리: 궁극기 사용 후 공격력 +30% (30초 사이클 전체 적용)
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
        return

    # 스트라이커 유니크
    # 속성 강타 기본 옵션 파티 공유 중복 제외
    if ut == "striker_all_elem_support":
        # 별빛 질주 모든 속성 피해 15% 상시 유지
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(u.get("all_elem_dmg_buff", 0.0))
        return

    if ut == "enhanced_mark":
        # 강화속성표식: 속성 폭발 피해 +30% 상시, 파티공유
        # - 속성 강타 피해 축 제외
        # - 표식 폭발 전용 별도 배율
        stats["element_mark_explosion_dmg"] = (
            float(stats.get("element_mark_explosion_dmg", 0.0))
            + float(u.get("mark_explosion_dmg_add", 0.0))
        )
        return

    if ut == "striker_final_buff":
        if is_owner:
            stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + float(u.get("final_dmg_buff", 0.0))
        return

    if ut == "striker_gauge_support":
        # 강타 게이지 증가 수치 미표기: 속성 강타 피해 기본 옵션만 반영
        return

    # 서포터 유니크
    if ut == "support_armor_pen":
        # 멜랑크림 쿠키의 순수한 기억
        # - 심연의 별: 방어력 관통 +12%
        # - 특수 스킬 사용 시 주변 아군에게 10초 동안 부여
        # - 이슬/샬롯/네온데니쉬 모두 특수 스킬로 갱신해 30초 사이클 내내 유지
        armor_map = u.get("armor_pen_add_by_cookie", {}) or {}
        armor_add = float(armor_map.get(cookie_name_kr, u.get("armor_pen_add", 0.0)))
        stats["buff_armor_pen_raw"] = float(stats.get("buff_armor_pen_raw", 0.0)) + armor_add
        return

    if ut == "support_atk_buff":
        # 로드 나이트메어의 기억
        # - 기본옵션 버프증폭 +36%는 위에서 파티 버프 계산에 이미 반영
        # - 초신성: 공격력 +15% (버프 부여가 반복되어 유지되는 것으로 적용)
        # - 아군 효과 파티 공유
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
        return

    if ut == "support_debuff":
        # 달빛술사 쿠키의 기억
        # - 기본옵션 디버프증폭 +36%는 위에서 항상 반영
        # - 자장가 받는 피해 +6%는 디버프를 못 묻히는 네온데니쉬일 때 0%
        dmg_taken_map = u.get("dmg_taken_inc_by_cookie", {}) or {}
        dmg_taken_add = float(dmg_taken_map.get(cookie_name_kr, u.get("dmg_taken_inc", 0.0)))
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + dmg_taken_add
        return

    if ut == "support_amp":
        # 시즌 1 증폭형 유니크: 증폭 수치는 공통 처리부에서 반영
        return

    if ut == "support_blackberry":
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
        return

    if ut == "support_heal_armor_pen":
        armor_map = u.get("armor_pen_add_by_cookie", {}) or {}
        armor_add = float(armor_map.get(cookie_name_kr, u.get("armor_pen_add", 0.0)))
        stats["buff_armor_pen_raw"] = float(stats.get("buff_armor_pen_raw", 0.0)) + armor_add
        return

    if ut == "support_dark_mark":
        dmg_taken_map = u.get("dmg_taken_inc_by_cookie", {}) or {}
        dmg_taken_add = float(dmg_taken_map.get(cookie_name_kr, u.get("dmg_taken_inc", 0.0)))
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + dmg_taken_add
        if is_owner and cookie_name_kr not in set(u.get("proc_disabled_cookies", []) or []):
            stats["unique_extra_coeff"] = float(stats.get("unique_extra_coeff", 0.0)) + float(u.get("proc_coeff_per_sec", 0.0))
        return

    if ut == "werewolf_mark":
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + float(u.get("dmg_taken_inc", 0.0))
        if is_owner:
            stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
            stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + float(u.get("crit_dmg_buff", 0.0))
        return

    # 공용 유니크 본인 전용
    if ut in {"ultimate_stack_self_buff", "ultimate_stack_proc"}:
        # 궁극기 3회 트리거는 쿠키별 사이클 타이밍이 달라 별도 상시 버프로 환산하지 않음
        # 기본 최종 피해 효과는 위 공통 처리부에서 반영
        return

    if ut == "ultimate_self_buff":
        if not is_owner:
            return
        # 쏟아지는 별: 공격력 +8%, 치명타 피해 +12%, 방어력 +10% (30초)
        stats["buff_atk_pct_raw"]  = float(stats.get("buff_atk_pct_raw", 0.0))  + float(u.get("atk_pct_buff", 0.0))
        stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + float(u.get("crit_dmg_buff", 0.0))

        stats["def_pct"] = float(stats.get("def_pct", 0.0)) + float(u.get("def_pct_buff", 0.0))
        stats["_dawn_moonlight_shield_pct"] = float(u.get("shield_pct", 0.0))
        stats["_dawn_moonlight_shield_dur"] = float(u.get("shield_duration", 0.0))
        return

def apply_party_buffs(
    stats: dict,
    party: List[str],
    main_cookie_name: str,
    party_uniques: Optional[Dict[str, str]] = None,
):
    # =====================================================
    # 0) 안전: 기본 키 세팅
    # =====================================================
    stats = stats or {}
    party = party or []

    stats.setdefault("buff_amp", 0.0)
    stats.setdefault("debuff_amp", 0.0)

    stats.setdefault("buff_crit_dmg_raw", 0.0)
    stats.setdefault("buff_atk_pct_raw", 0.0)
    stats.setdefault("buff_all_elem_dmg_raw", 0.0)

    stats.setdefault("final_atk_mult", 0.0)
    stats.setdefault("buff_final_atk_mult", 0.0)

    # 패시브 전용 "적이 받는 패시브 피해 증가"
    stats.setdefault("enemy_passive_taken_inc", 0.0)
    stats.setdefault("enemy_basic_taken_inc", 0.0)

    # 전체 딜에 곱해지는 "적이 받는 피해 증가"(받피증)
    # (희미한 날갯짓의 '받는 피해 +10%' 같은 건 여기에 쌓아야 함)
    stats.setdefault("enemy_dmg_taken_inc", 0.0)

    stats.setdefault("element_strike_dmg", 0.0)
    stats.setdefault("buff_armor_pen_raw", 0.0)

    # 방깎 관련 키
    stats.setdefault("def_reduction_raw", 0.0)
    stats.setdefault("def_reduction_no_scale_raw", 0.0)
    stats.setdefault("enemy_def_down_raw", 0.0)

    # 곱셈 누적 방지 (이 함수 스코프에서 "파티 오라/버프용"으로만 쓰는 축)
    # 파티 오라 누적 전 배율 기준값 초기화
    stats["passive_dmg_mult"] = 1.0
    stats["elem_dmg_mult"] = 1.0

    # 증폭 계산용 합계 키 보장
    stats.setdefault("party_buff_amp_total", float(stats.get("buff_amp", 0.0)))
    stats.setdefault("party_debuff_amp_total", float(stats.get("debuff_amp", 0.0)))

    # 현재 스탯 범위 중복 적용 방지
    applied = stats.setdefault("_applied_party_buffs", set())
    if not isinstance(applied, set):
        applied = set()
        stats["_applied_party_buffs"] = applied

    def _apply_once(tag: str, fn: Callable[[], None]):
        if tag in applied:
            return
        fn()
        applied.add(tag)

    # =====================================================
    # 1) 파티 포함 여부
    # =====================================================
    in_party_isle = ("이슬맛 쿠키" in party)
    in_party_wind = ("윈드파라거스 쿠키" in party)
    in_party_char = ("샬롯맛 쿠키" in party)
    in_party_neon = ("네온데니쉬맛 쿠키" in party)
    in_party_lungsha = ("룽샤맛 쿠키" in party)
    in_party_marble = ("마블베리맛 쿠키" in party)
    in_party_milky = ("밀키웨이맛 쿠키" in party)
    in_party_cherry_cola = ("체리콜라맛 쿠키" in party)
    in_party_stained_nougat = ("스테인드누가맛 쿠키" in party)
    in_party_stardust = ("스타더스트 쿠키" in party)
    in_party_black_barley = ("흑보리맛 쿠키" in party)
    in_party_moonlight = ("달빛술사 쿠키" in party)

    has_isle = in_party_isle or (main_cookie_name == "이슬맛 쿠키")
    has_wind = in_party_wind or (main_cookie_name == "윈드파라거스 쿠키")
    has_char = in_party_char or (main_cookie_name == "샬롯맛 쿠키")
    has_neon = in_party_neon or (main_cookie_name == "네온데니쉬맛 쿠키")
    has_lungsha = in_party_lungsha or (main_cookie_name == "룽샤맛 쿠키")
    has_marble = in_party_marble or (main_cookie_name == "마블베리맛 쿠키")
    has_milky = in_party_milky or (main_cookie_name == "밀키웨이맛 쿠키")
    has_cherry_cola = in_party_cherry_cola or (main_cookie_name == "체리콜라맛 쿠키")
    has_stained_nougat = in_party_stained_nougat or (main_cookie_name == "스테인드누가맛 쿠키")
    has_moonlight = in_party_moonlight or (main_cookie_name == "달빛술사 쿠키")

    # =====================================================
    # 세트효과 조회
    # =====================================================
    def _get_set_effect_base(set_name: str, fallback: dict) -> dict:
        try:
            se = (EQUIP_SETS.get(set_name, {}) or {}).get("set_effect", {}) or {}
            base = se.get("base", {}) or {}
            return base if base else fallback
        except Exception:
            return fallback

    # =====================================================
    # 2) 파티 자동 세트효과
    # =====================================================
    FIXED_PARTY_SETS: Dict[str, str] = {
        "이슬맛 쿠키": "전설의 유령해적",
        "샬롯맛 쿠키": "영원의 대마술사",
        "네온데니쉬맛 쿠키": "전설의 유령해적",
        "달빛술사 쿠키": "시간관리국의 제복",
        "윈드파라거스 쿠키": "황금 예복",
        "마블베리맛 쿠키": "유성우의 향연",
        "밀키웨이맛 쿠키": "황금 예복",
        # 체리콜라 잠재력·일반 조각 딜러형 후보
        "체리콜라맛 쿠키": "황금 예복",
        "스테인드누가맛 쿠키": "유성우의 향연",
    }

    def _lungsha_auto_party_set() -> str:
        main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
        lungsha_elem = COOKIE_ELEMENT.get("룽샤맛 쿠키", "")
        return "유성우의 향연" if (main_elem and main_elem == lungsha_elem) else "황금 예복"

    def _get_party_set_name(cookie_name: str) -> str:
        m = stats.get("party_sets")
        if isinstance(m, dict):
            v = m.get(cookie_name, "")
            if v and v != "NONE":
                return str(v)

        v2 = stats.get(f"equip_set__{cookie_name}", "")
        if v2 and v2 != "NONE":
            return str(v2)

        if cookie_name == "룽샤맛 쿠키" and cookie_name in (party or []) and cookie_name != main_cookie_name:
            return _lungsha_auto_party_set()

        if cookie_name == "마블베리맛 쿠키" and cookie_name in (party or []) and cookie_name != main_cookie_name:
            return "유성우의 향연"

        if cookie_name in (party or []) and cookie_name != main_cookie_name:
            return FIXED_PARTY_SETS.get(cookie_name, "")

        return ""

    def _sum_part_unique_buff_amp(set_name: str) -> float:
        total = 0.0
        s = EQUIP_SETS.get(set_name, {}) or {}
        for part in ("head", "top", "bottom"):
            u = ((s.get(part, {}) or {}).get("unique", {}) or {})
            total += float(u.get("buff_amp", 0.0))
        return total

    def _sum_part_unique_debuff_amp(set_name: str) -> float:
        total = 0.0
        s = EQUIP_SETS.get(set_name, {}) or {}
        for part in ("head", "top", "bottom"):
            u = ((s.get(part, {}) or {}).get("unique", {}) or {})
            total += float(u.get("debuff_amp", 0.0))
        return total

    # 버프/디버프 증폭은 파티 전체 합산값이 아니라
    # "그 효과를 부여한 쿠키"의 개인 증폭량만 사용
    # 예시: 개별 버프 증폭 합산
    # => 50*1.2 + 50*1.2 = 120%, 100*1.4가 아님
    FIXED_PARTY_SEAZ_FOR_AMP: Dict[str, str] = {
        "이슬맛 쿠키": "허브그린드:번뜩이는 기지",
        "샬롯맛 쿠키": "허브그린드:가벼운 손길",
        "네온데니쉬맛 쿠키": "허브그린드:작은 성배",
        "달빛술사 쿠키": "플럼나이트:달빛의 속삭임",
        "윈드파라거스 쿠키": "리치코랄:믿음직한 브리더",
        "룽샤맛 쿠키": "리치코랄:빛나는 은하수",
        "마블베리맛 쿠키": "리치코랄:빛나는 은하수",
        "밀키웨이맛 쿠키": "리치코랄:빛나는 은하수",
        "체리콜라맛 쿠키": "리치코랄:빛나는 은하수",
        "스테인드누가맛 쿠키": "리치코랄:빛나는 은하수",
    }

    FIXED_PARTY_UNIQUE_FOR_AMP: Dict[str, str] = {
        cookie_name: get_default_party_unique(cookie_name)
        for cookie_name in (
            "이슬맛 쿠키",
            "샬롯맛 쿠키",
            "네온데니쉬맛 쿠키",
            "달빛술사 쿠키",
            "윈드파라거스 쿠키",
            "룽샤맛 쿠키",
            "마블베리맛 쿠키",
            "밀키웨이맛 쿠키",
            "체리콜라맛 쿠키",
            "스테인드누가맛 쿠키",
        )
    }

    def _selected_party_seaz_name(cookie_name: str) -> str:
        m = stats.get("party_seaz")
        if isinstance(m, dict):
            v = str(m.get(cookie_name, "") or "")
            if v and v.upper() != "AUTO" and v != "NONE":
                return v
        return FIXED_PARTY_SEAZ_FOR_AMP.get(cookie_name, "")

    def _seaz_sub_amp(seaz_name: str, key: str) -> float:
        try:
            return float(((SEAZNITES.get(seaz_name, {}) or {}).get("sub", {}) or {}).get(key, 0.0))
        except Exception:
            return 0.0

    def _selected_party_seaz_sub_amp(cookie_name: str, key: str) -> float:
        return _seaz_sub_amp(_selected_party_seaz_name(cookie_name), key)

    def _fixed_party_seaz_sub_amp(cookie_name: str, key: str) -> float:
        return _seaz_sub_amp(FIXED_PARTY_SEAZ_FOR_AMP.get(cookie_name, ""), key)

    def _selected_party_unique_name(cookie_name: str) -> str:
        u_map = party_uniques or stats.get("party_uniques") or {}
        try:
            u_name = str(u_map.get(cookie_name, "")) if u_map else ""
        except Exception:
            u_name = ""
        if (not u_name) or (u_name.upper() == "AUTO"):
            u_name = FIXED_PARTY_UNIQUE_FOR_AMP.get(cookie_name, "")
        if u_name == "NONE":
            return ""
        return u_name

    def _party_unique_amp(cookie_name: str, key: str) -> float:
        u_name = _selected_party_unique_name(cookie_name)
        if not u_name:
            return 0.0
        try:
            u = UNIQUE_SHARDS.get(u_name, {}) or {}
            if not is_unique_allowed(cookie_name, u_name):
                return 0.0
            by_cookie = u.get(f"{key}_by_cookie", {}) or {}
            return float(by_cookie.get(cookie_name, u.get(key, 0.0)))
        except Exception:
            return 0.0

    def _party_equip_amp(cookie_name: str, key: str) -> float:
        if cookie_name == main_cookie_name:
            return 0.0
        set_name = _get_party_set_name(cookie_name)
        if not set_name:
            return 0.0
        try:
            base = _get_set_effect_base(set_name, fallback={})
            total = float(base.get(key, 0.0))
            if key == "buff_amp":
                total += _sum_part_unique_buff_amp(set_name)
            elif key == "debuff_amp":
                total += _sum_part_unique_debuff_amp(set_name)
            return total
        except Exception:
            return 0.0

    def _buff_amp_for_owner(cookie_name: str) -> float:
        if cookie_name == main_cookie_name:
            return float(stats.get("self_buff_amp_total", stats.get("buff_amp_total", stats.get("buff_amp", 0.0))))

        ba = 0.0
        if cookie_name == "이슬맛 쿠키":
            ba += _assumed_isle_buff_amp_for_party()
        elif cookie_name == "샬롯맛 쿠키":
            ba += _assumed_charlotte_buff_amp_for_party()
        elif cookie_name == "네온데니쉬맛 쿠키":
            ba += _assumed_neon_buff_amp_for_party()
        elif cookie_name == "달빛술사 쿠키":
            moon_unique_raw = ""
            try:
                u_map = party_uniques or stats.get("party_uniques") or {}
                if isinstance(u_map, dict):
                    moon_unique_raw = str(u_map.get(cookie_name, "") or "")
            except Exception:
                moon_unique_raw = ""
            moon_unique = "NONE" if moon_unique_raw == "NONE" else (_selected_party_unique_name(cookie_name) or get_default_party_unique(cookie_name) or "달빛술사 쿠키의 기억")
            ba += _assumed_moonlight_buff_amp_for_party(
                equip_name=_get_party_set_name(cookie_name) or "시간관리국의 제복",
                seaz_name=_selected_party_seaz_name(cookie_name) or "플럼나이트:달빛의 속삭임",
                unique_name=moon_unique,
            )

        # 고정 시즈 가정값과 선택 시즈 차이 반영
        if cookie_name in ("이슬맛 쿠키", "샬롯맛 쿠키", "네온데니쉬맛 쿠키"):
            ba += _selected_party_seaz_sub_amp(cookie_name, "buff_amp") - _fixed_party_seaz_sub_amp(cookie_name, "buff_amp")
        else:
            ba += _selected_party_seaz_sub_amp(cookie_name, "buff_amp")

        ba += _party_equip_amp(cookie_name, "buff_amp")
        ba += _party_unique_amp(cookie_name, "buff_amp_add")
        return max(0.0, ba)

    def _debuff_amp_for_owner(cookie_name: str) -> float:
        if cookie_name == main_cookie_name:
            return float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))

        da = 0.0
        if cookie_name == "달빛술사 쿠키":
            # 달빛술사 장비별 디버프 잠재력 수 조정
            # 선택 조합 기준으로 150%를 넘기는 최소 디벞 잠재만 자동 반영
            moon_unique_raw = ""
            try:
                u_map = party_uniques or stats.get("party_uniques") or {}
                if isinstance(u_map, dict):
                    moon_unique_raw = str(u_map.get(cookie_name, "") or "")
            except Exception:
                moon_unique_raw = ""
            moon_unique = "NONE" if moon_unique_raw == "NONE" else (_selected_party_unique_name(cookie_name) or get_default_party_unique(cookie_name) or "달빛술사 쿠키의 기억")
            return max(0.0, _assumed_moonlight_debuff_amp_for_party(
                equip_name=_get_party_set_name(cookie_name) or "시간관리국의 제복",
                seaz_name=_selected_party_seaz_name(cookie_name) or "플럼나이트:달빛의 속삭임",
                unique_name=moon_unique,
            ))
        elif cookie_name == "윈드파라거스 쿠키":
            da += _assumed_wind_debuff_amp_for_party()
        elif cookie_name == "룽샤맛 쿠키":
            da += _assumed_lungsha_debuff_amp_for_party(main_cookie_name)
        elif cookie_name == "마블베리맛 쿠키":
            da += _assumed_marble_debuff_amp_for_party()

        da += _selected_party_seaz_sub_amp(cookie_name, "debuff_amp")
        da += _party_equip_amp(cookie_name, "debuff_amp")
        da += _party_unique_amp(cookie_name, "debuff_amp_add")
        return max(0.0, da)

    def _buff_scale_for_owner(cookie_name: str) -> float:
        return 1.0 + _buff_amp_for_owner(cookie_name)

    def _debuff_scale_for_owner(cookie_name: str) -> float:
        return 1.0 + _debuff_amp_for_owner(cookie_name)

    # 잎새의 활강 파티 디버프 적용
    # 메인 쿠키 디버프 증폭이 아니라 윈파 개인 디버프 증폭만 사용
    if has_wind:
        stats["_wind_leaf_glide_owner_debuff_amp"] = _debuff_amp_for_owner("윈드파라거스 쿠키")

    def _effective_party_support_set(cookie_name: str) -> str:
        """파티 서포터 장비 선택값"""
        return _get_party_set_name(cookie_name)

    PARTY_EQUIP_STACK_ORDER = [
        "이슬맛 쿠키",
        "샬롯맛 쿠키",
        "네온데니쉬맛 쿠키",
        "달빛술사 쿠키",
        "윈드파라거스 쿠키",
        "룽샤맛 쿠키",
        "마블베리맛 쿠키",
        "밀키웨이맛 쿠키",
        "체리콜라맛 쿠키",
        "스테인드누가맛 쿠키",
    ]

    def _party_set_effect_first_applicable(cookie_name: str, set_name: str, effect_kind: str = "global") -> bool:
        """파티 장비 세트효과 중복 방지"""
        if not set_name or cookie_name == main_cookie_name or cookie_name not in (party or []):
            return False
        if str(stats.get("_main_equip_set_name", "")) == str(set_name):
            return False

        def _effect_condition(cname: str) -> bool:
            if effect_kind in ("elem_res", "all_elem_if_same"):
                return _same_element_as_main(cname)
            return True

        for cname in PARTY_EQUIP_STACK_ORDER:
            if cname == main_cookie_name or cname not in (party or []):
                continue
            try:
                cname_set = _get_party_set_name(cname)
            except Exception:
                cname_set = ""
            if str(cname_set) != str(set_name):
                continue
            if not _effect_condition(cname):
                continue
            return cname == cookie_name
        return False

    def _same_element_as_main(cookie_name: str) -> bool:
        """메인 쿠키 동일 속성 판정"""
        main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
        wearer_elem = COOKIE_ELEMENT.get(cookie_name, "")
        return bool(main_elem and wearer_elem and main_elem == wearer_elem)

    def _add_party_equip_all_elem_if_same(cookie_name: str, add_elem: float):
        """동일 속성 장비 모든 속성 피해"""
        if add_elem and _same_element_as_main(cookie_name):
            stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + add_elem

    def _add_party_equip_all_elem_always(add_elem: float):
        """파티 장비 모든 속성 피해"""
        if add_elem:
            stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + add_elem

    def _add_party_equip_elem_res_if_same(cookie_name: str, add_res: float):
        """동일 속성 장비 속성 내성 감소"""
        if add_res and _same_element_as_main(cookie_name):
            stats["elem_res_reduction_no_scale_raw"] = float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + add_res

    def _meteor_elem_res_for_owner(cookie_name: str, base: dict) -> float:
        """유성우 장비 속성 내성 감소"""
        if str(cookie_name or "") == "달빛술사 쿠키":
            return 0.10
        return float((base or {}).get("elem_res_reduction_raw", 0.0))

    # 1) 증폭 계산 선반영
    def _apply_party_auto_sets_pre_scale():
        # 이슬(서포터): 영원의 대마술사 선택 시 버프 증폭 반영
        if in_party_isle and (main_cookie_name != "이슬맛 쿠키"):
            isle_set = _get_party_set_name("이슬맛 쿠키") or "전설의 유령해적"
            if isle_set == "영원의 대마술사" and _party_set_effect_first_applicable("이슬맛 쿠키", isle_set, "amp"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_ba = float(base.get("buff_amp", 0.0)) + _sum_part_unique_buff_amp("영원의 대마술사")
                if add_ba:
                    stats["buff_amp"] = float(stats.get("buff_amp", 0.0)) + add_ba
                    stats["party_buff_amp_total"] = float(stats.get("party_buff_amp_total", 0.0)) + add_ba

        # 샬롯(서포터)
        if in_party_char and (main_cookie_name != "샬롯맛 쿠키"):
            char_set = _effective_party_support_set("샬롯맛 쿠키")
            if char_set == "영원의 대마술사" and _party_set_effect_first_applicable("샬롯맛 쿠키", char_set, "amp"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_ba = float(base.get("buff_amp", 0.0)) + _sum_part_unique_buff_amp("영원의 대마술사")
                if add_ba:
                    stats["buff_amp"] = float(stats.get("buff_amp", 0.0)) + add_ba
                    stats["party_buff_amp_total"] = float(stats.get("party_buff_amp_total", 0.0)) + add_ba

        # 네온(서포터)
        if in_party_neon and (main_cookie_name != "네온데니쉬맛 쿠키"):
            neon_set = _effective_party_support_set("네온데니쉬맛 쿠키")
            if neon_set == "영원의 대마술사" and _party_set_effect_first_applicable("네온데니쉬맛 쿠키", neon_set, "amp"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_ba = float(base.get("buff_amp", 0.0)) + _sum_part_unique_buff_amp("영원의 대마술사")
                if add_ba:
                    stats["buff_amp"] = float(stats.get("buff_amp", 0.0)) + add_ba
                    stats["party_buff_amp_total"] = float(stats.get("party_buff_amp_total", 0.0)) + add_ba

        # 달빛술사(서포터): 유성우/황금예복 선택 시 디버프 증폭 반영
        if in_party_moonlight and (main_cookie_name != "달빛술사 쿠키"):
            moon_set = _effective_party_support_set("달빛술사 쿠키") or "시간관리국의 제복"
            if moon_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("달빛술사 쿠키", moon_set, "amp"):
                base = _get_set_effect_base(moon_set, fallback={"debuff_amp": 0.15})
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(moon_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

        # 윈파(스트라이커): 선택 장비의 디버프 증폭 반영
        if in_party_wind and (main_cookie_name != "윈드파라거스 쿠키"):
            wind_set = _get_party_set_name("윈드파라거스 쿠키") or "황금 예복"
            if wind_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("윈드파라거스 쿠키", wind_set, "amp"):
                base = _get_set_effect_base(wind_set, fallback={"debuff_amp": 0.15})
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(wind_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

        # 룽샤(스트라이커): 세트효과의 디버프 증폭
        if in_party_lungsha and (main_cookie_name != "룽샤맛 쿠키"):
            lungsha_set = _get_party_set_name("룽샤맛 쿠키") or _lungsha_auto_party_set()
            if lungsha_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("룽샤맛 쿠키", lungsha_set, "amp"):
                base = _get_set_effect_base(
                    lungsha_set,
                    fallback={"debuff_amp": 0.15},
                )
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(lungsha_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

        # 마블베리(스트라이커): 선택 장비의 디버프 증폭 반영
        if in_party_marble and (main_cookie_name != "마블베리맛 쿠키"):
            marble_set = _get_party_set_name("마블베리맛 쿠키") or "유성우의 향연"
            if marble_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("마블베리맛 쿠키", marble_set, "amp"):
                base = _get_set_effect_base(marble_set, fallback={"debuff_amp": 0.15})
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(marble_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

        # 밀키웨이(스트라이커): 선택 장비의 디버프 증폭 반영
        if in_party_milky and (main_cookie_name != "밀키웨이맛 쿠키"):
            milky_set = _get_party_set_name("밀키웨이맛 쿠키") or "황금 예복"
            if milky_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("밀키웨이맛 쿠키", milky_set, "amp"):
                base = _get_set_effect_base(milky_set, fallback={"debuff_amp": 0.15})
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(milky_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

        if in_party_stained_nougat and (main_cookie_name != "스테인드누가맛 쿠키"):
            nougat_set = _get_party_set_name("스테인드누가맛 쿠키") or "유성우의 향연"
            if nougat_set in ("유성우의 향연", "황금 예복") and _party_set_effect_first_applicable("스테인드누가맛 쿠키", nougat_set, "amp"):
                base = _get_set_effect_base(nougat_set, fallback={"debuff_amp": 0.15})
                add_da = float(base.get("debuff_amp", 0.0)) + _sum_part_unique_debuff_amp(nougat_set)
                if add_da:
                    stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + add_da
                    stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + add_da

    _apply_once("AUTO_SET_PRE_SCALE_AMPS", _apply_party_auto_sets_pre_scale)

    # =====================================================
    # 3) 버프/디버프 증폭 스케일
    # =====================================================
    # =====================================================
    # 2) 실제 세트 효과 반영
    # =====================================================
    def _apply_party_auto_sets_post_scale_no_scaling():
        # --- 이슬(서포터): 해적셋 / 대마술사 선택값 반영 ---
        if in_party_isle and (main_cookie_name != "이슬맛 쿠키"):
            isle_set = _get_party_set_name("이슬맛 쿠키") or "전설의 유령해적"
            if isle_set == "영원의 대마술사" and _party_set_effect_first_applicable("이슬맛 쿠키", isle_set, "all_elem_if_same"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                _add_party_equip_all_elem_if_same("이슬맛 쿠키", add_elem)

            elif isle_set == "전설의 유령해적" and _party_set_effect_first_applicable("이슬맛 쿠키", isle_set, "global"):
                base = _get_set_effect_base(
                    "전설의 유령해적",
                    fallback={"all_elem_dmg": 0.30, "def_reduction_raw": 0.05},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                add_def  = float(base.get("def_reduction_raw", 0.0))
                _add_party_equip_all_elem_always(add_elem)
                if add_def:
                    stats["def_reduction_no_scale_raw"]  = float(stats.get("def_reduction_no_scale_raw", 0.0)) + add_def
                    stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + add_def

        # --- 샬롯(서포터): 대마술사/유령해적 선택값 반영 ---
        if in_party_char and (main_cookie_name != "샬롯맛 쿠키"):
            char_set = _effective_party_support_set("샬롯맛 쿠키")

            if char_set == "영원의 대마술사" and _party_set_effect_first_applicable("샬롯맛 쿠키", char_set, "all_elem_if_same"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                _add_party_equip_all_elem_if_same("샬롯맛 쿠키", add_elem)

            elif char_set == "전설의 유령해적" and _party_set_effect_first_applicable("샬롯맛 쿠키", char_set, "global"):
                base = _get_set_effect_base(
                    "전설의 유령해적",
                    fallback={"all_elem_dmg": 0.30, "def_reduction_raw": 0.05},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                add_def  = float(base.get("def_reduction_raw", 0.0))

                _add_party_equip_all_elem_always(add_elem)
                if add_def:
                    stats["def_reduction_no_scale_raw"]  = float(stats.get("def_reduction_no_scale_raw", 0.0)) + add_def
                    stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + add_def

        # --- 네온(서포터): 대마술사/유령해적 선택값 반영 ---
        if in_party_neon and (main_cookie_name != "네온데니쉬맛 쿠키"):
            neon_set = _effective_party_support_set("네온데니쉬맛 쿠키")

            if neon_set == "영원의 대마술사" and _party_set_effect_first_applicable("네온데니쉬맛 쿠키", neon_set, "all_elem_if_same"):
                base = _get_set_effect_base(
                    "영원의 대마술사",
                    fallback={"buff_amp": 0.15, "all_elem_dmg": 0.30},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                _add_party_equip_all_elem_if_same("네온데니쉬맛 쿠키", add_elem)

            elif neon_set == "전설의 유령해적" and _party_set_effect_first_applicable("네온데니쉬맛 쿠키", neon_set, "global"):
                base = _get_set_effect_base(
                    "전설의 유령해적",
                    fallback={"all_elem_dmg": 0.30, "def_reduction_raw": 0.05},
                )
                add_elem = float(base.get("all_elem_dmg", 0.0))
                add_def  = float(base.get("def_reduction_raw", 0.0))

                _add_party_equip_all_elem_always(add_elem)
                if add_def:
                    stats["def_reduction_no_scale_raw"]  = float(stats.get("def_reduction_no_scale_raw", 0.0)) + add_def
                    stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + add_def

        # --- 달빛술사(서포터): 유성우 / 황금예복 선택값 반영 ---
        if in_party_moonlight and (main_cookie_name != "달빛술사 쿠키"):
            moon_set = _effective_party_support_set("달빛술사 쿠키") or "시간관리국의 제복"

            if moon_set == "유성우의 향연" and _party_set_effect_first_applicable("달빛술사 쿠키", moon_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = _meteor_elem_res_for_owner("달빛술사 쿠키", base)
                _add_party_equip_elem_res_if_same("달빛술사 쿠키", add_res)

            elif moon_set == "황금 예복" and _party_set_effect_first_applicable("달빛술사 쿠키", moon_set, "element_strike"):
                base = _get_set_effect_base(
                    "황금 예복",
                    fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                )
                add_es = float(base.get("element_strike_dmg", 0.0))
                if add_es:
                    stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es

        # --- 윈파(스트라이커): 황금예복 / 유성우 선택값 반영 ---
        if in_party_wind and (main_cookie_name != "윈드파라거스 쿠키"):
            wind_set = _get_party_set_name("윈드파라거스 쿠키") or "황금 예복"
            if wind_set == "황금 예복" and _party_set_effect_first_applicable("윈드파라거스 쿠키", wind_set, "element_strike"):
                if stats.get("_main_equip_set_name") != "황금 예복":
                    base = _get_set_effect_base(
                        "황금 예복",
                        fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                    )
                    add_es = float(base.get("element_strike_dmg", 0.0))
                    if add_es:
                        stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es

            elif wind_set == "유성우의 향연" and _party_set_effect_first_applicable("윈드파라거스 쿠키", wind_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = float(base.get("elem_res_reduction_raw", 0.0))
                _add_party_equip_elem_res_if_same("윈드파라거스 쿠키", add_res)

        # --- 룽샤(스트라이커): 속성 같으면 유성우 / 다르면 황금예복 ---
        if in_party_lungsha and (main_cookie_name != "룽샤맛 쿠키"):
            lungsha_set = _get_party_set_name("룽샤맛 쿠키") or _lungsha_auto_party_set()

            if lungsha_set == "황금 예복" and _party_set_effect_first_applicable("룽샤맛 쿠키", lungsha_set, "element_strike"):
                base = _get_set_effect_base(
                    "황금 예복",
                    fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                )
                add_es = float(base.get("element_strike_dmg", 0.0))
                if add_es:
                    stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es

            elif lungsha_set == "유성우의 향연" and _party_set_effect_first_applicable("룽샤맛 쿠키", lungsha_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = float(base.get("elem_res_reduction_raw", 0.0))
                _add_party_equip_elem_res_if_same("룽샤맛 쿠키", add_res)

        # --- 마블베리(스트라이커): 유성우 / 황금예복 선택값 반영 ---
        if in_party_marble and (main_cookie_name != "마블베리맛 쿠키"):
            marble_set = _get_party_set_name("마블베리맛 쿠키") or "유성우의 향연"
            if marble_set == "유성우의 향연" and _party_set_effect_first_applicable("마블베리맛 쿠키", marble_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = float(base.get("elem_res_reduction_raw", 0.0))
                _add_party_equip_elem_res_if_same("마블베리맛 쿠키", add_res)

            elif marble_set == "황금 예복" and _party_set_effect_first_applicable("마블베리맛 쿠키", marble_set, "element_strike"):
                base = _get_set_effect_base(
                    "황금 예복",
                    fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                )
                add_es = float(base.get("element_strike_dmg", 0.0))
                if add_es:
                    stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es

        # --- 밀키웨이(스트라이커): 황금예복 / 유성우 선택값 반영 ---
        if in_party_milky and (main_cookie_name != "밀키웨이맛 쿠키"):
            milky_set = _get_party_set_name("밀키웨이맛 쿠키") or "황금 예복"
            if milky_set == "황금 예복" and _party_set_effect_first_applicable("밀키웨이맛 쿠키", milky_set, "element_strike"):
                base = _get_set_effect_base(
                    "황금 예복",
                    fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                )
                add_es = float(base.get("element_strike_dmg", 0.0))
                if add_es:
                    stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es
            elif milky_set == "유성우의 향연" and _party_set_effect_first_applicable("밀키웨이맛 쿠키", milky_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = float(base.get("elem_res_reduction_raw", 0.0))
                _add_party_equip_elem_res_if_same("밀키웨이맛 쿠키", add_res)

        if in_party_stained_nougat and (main_cookie_name != "스테인드누가맛 쿠키"):
            nougat_set = _get_party_set_name("스테인드누가맛 쿠키") or "유성우의 향연"
            if nougat_set == "황금 예복" and _party_set_effect_first_applicable("스테인드누가맛 쿠키", nougat_set, "element_strike"):
                base = _get_set_effect_base(
                    "황금 예복",
                    fallback={"element_strike_dmg": 0.25, "debuff_amp": 0.15},
                )
                add_es = float(base.get("element_strike_dmg", 0.0))
                if add_es:
                    stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + add_es
            elif nougat_set == "유성우의 향연" and _party_set_effect_first_applicable("스테인드누가맛 쿠키", nougat_set, "elem_res"):
                base = _get_set_effect_base(
                    "유성우의 향연",
                    fallback={"elem_res_reduction_raw": 0.05, "debuff_amp": 0.15},
                )
                add_res = float(base.get("elem_res_reduction_raw", 0.0))
                _add_party_equip_elem_res_if_same("스테인드누가맛 쿠키", add_res)

    _apply_once("AUTO_SET_POST_SCALE_EFFECTS_NO_SCALING", _apply_party_auto_sets_post_scale_no_scaling)

    # =====================================================
    # 4) 쿠키별 파티 버프
    # =====================================================

    # =====================================================
    # [쿠키] 이슬맛 쿠키
    # [역할] 파티 버프 / 상시 유지 가정
    # - 치명타 피해 +56% → 벞증 적용
    # - 공격력 증가 +22.4% → 벞증 적용
    # - 기본 공격 피해 +10% → 벞증 적용
    # - 모든 속성 피해 30%·버프 증폭 제외
    # =====================================================
    def _apply_isle_buffs():
        if not (in_party_isle or (main_cookie_name == "이슬맛 쿠키")):
            return

        innate_scale = _buff_scale_for_owner("이슬맛 쿠키")

        # 파티 치피 +56% (이슬 본인 벞증 적용)
        u_cd = float(get_uptime("PARTY_ISLE_CRITDMG_0p56"))
        stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + (
            0.56 * u_cd * innate_scale
        )

        # 파티 최종공 +22.4% (벞증 적용)
        u_atk = float(get_uptime("PARTY_ISLE_ATK_0p224"))
        add_final_atk = 0.224 * u_atk * innate_scale
        stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
        stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk

        # 기본공격피해 +10% 벞증 적용 (벞증 적용)
        stats["basic_dmg"] = float(stats.get("basic_dmg", 0.0)) + (0.10 * innate_scale)

        # 모든 속성 피해 30%·버프 증폭 제외
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + 0.30

    # =====================================================
    # [쿠키] 윈드파라거스 쿠키
    # [역할] 파티 버프
    # - 치명타 피해 +40%
    # - 버프·디버프 증폭 제외
    # - 최종 치명타 피해 직접 합산
    # =====================================================
    def _apply_wind_party_effects():
        # [이어지는 마음] 에메랄딘 치피 +40%
        # - 윈파가 파티원일 때: 메인 쿠키에게 파티 버프로 1회 적용
        # - 윈파 메인: 사이클 업타임 기준 1회 적용
        # - 윈파 본인 40% 중복 반영 방지
        if main_cookie_name == "윈드파라거스 쿠키":
            return

        u = float(get_uptime("PARTY_WIND_CRITDMG_0p40"))
        stats["crit_dmg"] = float(stats.get("crit_dmg", 1.0)) + (0.40 * u)

    # =====================================================
    # [딜러 파티 디버프] 보스에 묻는 공용 '쿠키에게 받는 피해 증가'
    # - 스타더스트 [별무리] 10중첩: 쿠키에게 받는 피해 +10%
    # - 흑보리 [사냥꾼의 독]: 쿠키에게 받는 피해 +10%
    # 같은 쿠키가 2명 있어도 동일 디버프는 1회만 적용
    # 스타더스트·흑보리 메인 파티 공유
    # =====================================================
    if in_party_stardust:
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.10
        stats["_shared_stardust_star_cluster_applied"] = True

    if in_party_black_barley:
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.10
        stats["_shared_black_barley_poison_applied"] = True

    # =====================================================
    # [쿠키] 룽샤맛 쿠키
    # [역할] 파티 디버프 / 궁극기 받피증
    # - 주화입마: 받는 피해 +33.6%
    # - 메인과 룽샤 속성이 같으면 받는 피해 +20% 추가
    # - 삼매각화: 적이 받는 궁극기 피해 +35%
    # - 디버프 증폭 제외
    # - 룽샤 본인이 메인일 때는 파티 효과 미적용
    # =====================================================
    def _apply_lungsha_party_effects():
        if not (in_party_lungsha or (main_cookie_name == "룽샤맛 쿠키")):
            return
        if main_cookie_name == "룽샤맛 쿠키":
            return

        # 불가역: 역병의 보호막 제외
        # 주화입마 33.6%만 반영
        base_taken = 0.336

        # 메인과 룽샤 속성이 같으면 받는 피해 +20% 추가
        main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
        lungsha_elem = COOKIE_ELEMENT.get("룽샤맛 쿠키", "")
        if main_elem and (main_elem == lungsha_elem):
            base_taken += 0.20

        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + base_taken

        # 삼매각화: 적이 받는 궁극기 피해 증가 +35%
        stats["enemy_ult_taken_inc"] = float(stats.get("enemy_ult_taken_inc", 0.0)) + 0.35

    # =====================================================
    # [쿠키] 마블베리맛 쿠키
    # [역할] 파티 디버프 / 속성강타 피해 지원
    # - 크래시: 쿠키에게 받는 피해 +28% × 1.15
    # - 메인이 어둠속성이면 받는 피해 +10% 추가
    # - 아티팩트 충전은 타이밍: 속성강타 피해 +25%
    # - 버프·디버프 증폭 제외
    # - 중복 적용 방지용 마커 사용
    # =====================================================
    def _apply_marble_party_effects():
        if not (in_party_marble or (main_cookie_name == "마블베리맛 쿠키")):
            return
        if main_cookie_name == "마블베리맛 쿠키":
            return

        # 마블베리 크래시: 쿠키에게 받는 피해 +28%, 승급 강화 15%
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + (0.28 * 1.15)

        # 승급: 어둠속성 쿠키에게 받는 피해 +10%
        if COOKIE_ELEMENT.get(main_cookie_name, "") == "dark":
            stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.10

        # 아티팩트 충전은 타이밍: 에너지 맥스 속성강타 피해 +25%
        if not stats.get("_marble_energy_max_strike_applied", False):
            stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + 0.25
            stats["_marble_energy_max_strike_applied"] = True

    # =====================================================
    # [쿠키] 밀키웨이맛 쿠키
    # [역할] 파티 받는 피해 증가 / 아티팩트 피해 지원
    # - 잠꼬대: 쿠키에게 받는 피해 +33.6%
    # - 메인이 신비속성이면 승급 효과로 받는 피해 +20% 추가
    # - 미지의 영역: 밀키웨이 본인 및 주변 아군 모든 속성 피해 +20%
    # - 뜻밖의 선로: 적의 신비 속성 내성 -12%
    # - 밀키웨이 본인 효과 개별 계산
    # =====================================================
    def _apply_milky_way_party_effects():
        if not (in_party_milky or (main_cookie_name == "밀키웨이맛 쿠키")):
            return
        if main_cookie_name == "밀키웨이맛 쿠키":
            return

        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.336
        if COOKIE_ELEMENT.get(main_cookie_name, "") == "mystic":
            stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.20

        artifact_meta = (ARTIFACTS.get("꿈의 저편으로", {}) or {}).get("milky_way", {}) or {}
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(
            artifact_meta.get("party_all_elem_dmg", 0.0)
        )
        if COOKIE_ELEMENT.get(main_cookie_name, "") == "mystic":
            # 뜻밖의 선로 디버프 증폭 제외
            stats["elem_res_reduction_no_scale_raw"] = float(
                stats.get("elem_res_reduction_no_scale_raw", 0.0)
            ) + float(artifact_meta.get("mystic_res_reduction", 0.0))

    # =====================================================
    # [쿠키] 체리콜라맛 쿠키
    # [역할] 파티 받는 피해 증가 지원
    # - 버블포인트: 쿠키에게 받는 피해 +22.4%
    # - 달콤공격 1교시: 물속성 쿠키에게 받는 피해 +30%
    # - 끈적끈적 후폭풍: 패시브 피해 35% 증가
    # - 디버프 증폭 제외
    # =====================================================
    def _apply_cherry_cola_party_effects():
        if not (in_party_cherry_cola or (main_cookie_name == "체리콜라맛 쿠키")):
            return
        if main_cookie_name == "체리콜라맛 쿠키":
            return

        # 버블포인트: 모든 쿠키에게 받는 피해 +22.4%
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.224

        # 물속성 쿠키에게 받는 피해 +30%
        if COOKIE_ELEMENT.get(main_cookie_name, "") == "water":
            stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.30

        # 끈적끈적 후폭풍: 체리콜라가 파티 스트라이커일 때 강화 기본공격으로
        # 메인 패시브 피해 35% 증가
        try:
            sticky = float(ARTIFACTS.get("끈적끈적 후폭풍", {}).get("cherry_cola", {}).get("enemy_passive_taken_inc", 0.0))
        except Exception:
            sticky = 0.0
        if sticky:
            stats["enemy_passive_taken_inc"] = float(stats.get("enemy_passive_taken_inc", 0.0)) + sticky

    # =====================================================
    # [쿠키] 스테인드누가맛 쿠키
    # [역할] 파티 받는 피해 증가 지원
    # - [정화]: 쿠키 받피증 +33.6%
    # - 승급: 대지속성 쿠키 받피증 +20%
    # - 꿈결 같은 휴식: 적이 받는 기본 공격 피해 +35%
    # =====================================================
    def _apply_stained_nougat_party_effects():
        if not (in_party_stained_nougat or (main_cookie_name == "스테인드누가맛 쿠키")):
            return
        if main_cookie_name == "스테인드누가맛 쿠키":
            return

        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.336

        if COOKIE_ELEMENT.get(main_cookie_name, "") == "earth":
            stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + 0.20

        try:
            basic_taken = float(ARTIFACTS.get("꿈결 같은 휴식", {}).get("stained_nougat", {}).get("enemy_basic_taken_inc", 0.0))
        except Exception:
            basic_taken = 0.0
        if basic_taken:
            stats["enemy_basic_taken_inc"] = float(stats.get("enemy_basic_taken_inc", 0.0)) + basic_taken

    # =====================================================
    # [쿠키] 샬롯맛 쿠키
    # [역할] 파티 버프 / 아티팩트 오라 / 본인 전용 효과
    # - 결속: 공격력 증가 +39.2% → 벞증 적용
    # - 바늘땀/결속: 패시브 피해 +10% → 벞증 적용
    # 아티팩트 희미한 날갯짓
    # - 적이 받는 피해 10% 증가
    # - 적이 받는 패시브 피해 10% 증가
    # - 샬롯 모든 속성 피해 25% 증가
    # - 샬롯 패시브 피해 배율 1.20
    # =====================================================
    CHAR_WINGS_ENEMY_TAKEN_INC = 0.10
    CHAR_WINGS_ALL_ELEM_ADD = 0.25
    CHAR_WINGS_PASSIVE_MULT = 1.20

    def _apply_charlotte_party_effects():
        if not (in_party_char or (main_cookie_name == "샬롯맛 쿠키")):
            return

        innate_scale = _buff_scale_for_owner("샬롯맛 쿠키")

        # 결속 공증 39.2% (샬롯 본인 벞증 적용)
        u_bond = 1.0
        add_final_atk = 0.392 * u_bond * innate_scale
        stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
        stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk

        # 바늘땀/결속 패시브 피해 +10% (벞증 적용)
        stats["passive_dmg"] = float(stats.get("passive_dmg", 0.0)) + (0.10 * innate_scale)

        # 아티팩트 희미한 날갯짓
        _apply_charlotte_wings_artifact_aura()

    def _apply_charlotte_wings_artifact_aura():
        if not has_char:
            return

        # 파티 공통: 적이 받는 피해 +10%
        stats["enemy_dmg_taken_inc"] = float(stats.get("enemy_dmg_taken_inc", 0.0)) + (
            CHAR_WINGS_ENEMY_TAKEN_INC
        )

        # 샬롯 본인 전용: 진혼 모든 속성 피해 +25%
        # 파티 딜러 공유 제외
        if main_cookie_name == "샬롯맛 쿠키":
            stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + (
                CHAR_WINGS_ALL_ELEM_ADD
            )

        # 파티 공통: 적이 받는 패시브 피해 +10%
        stats["enemy_passive_taken_inc"] = float(stats.get("enemy_passive_taken_inc", 0.0)) + (
            CHAR_WINGS_ENEMY_TAKEN_INC
        )

        # 샬롯 본인 전용: 패시브 배율 ×1.20
        if main_cookie_name == "샬롯맛 쿠키":
            stats["passive_dmg_mult"] = float(stats.get("passive_dmg_mult", 1.0)) * (
                CHAR_WINGS_PASSIVE_MULT
            )

    # =====================================================
    # [쿠키] 네온데니쉬 쿠키
    # [역할] 파티 버프 / 궁극기 받피증
    # - 긴급 패치: 공격력 증가 +34.6% → 벞증 적용
    # - 승급 포함: 궁극기 스킬 피해 +15% → 벞증 적용
    # - 아티팩트 관리자 권한: 모든 속성 피해 +30%
    # - 아티팩트 치트키 + 치명적 오류:
    # 적이 받는 궁극기 피해 +8% +5.8%
    # - 궁극기 전용 적 받는 피해 증가 축
    # =====================================================
    NEON_PARTY_FINAL_ATK_BUFF = 0.346
    NEON_PARTY_ULT_DMG_BUFF = 0.15
    NEON_PARTY_ALL_ELEM_ADD = 0.30
    NEON_PARTY_ENEMY_ULT_TAKEN_INC = 0.08 + 0.058

    def _apply_neon_party_effects():
        if not in_party_neon:
            return

        innate_scale = _buff_scale_for_owner("네온데니쉬맛 쿠키")

        # 긴급 패치: 공격력 증가 +34.6% (네온 본인 벞증 적용)
        add_final_atk = NEON_PARTY_FINAL_ATK_BUFF * innate_scale
        stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
        stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk

        # 승급: 궁극기 스킬 피해 증가 +15%
        # 승급: 궁극기 스킬 피해 증가 +15% (벞증 적용)
        stats["ult_dmg"] = float(stats.get("ult_dmg", 0.0)) + (
            NEON_PARTY_ULT_DMG_BUFF * innate_scale
        )

        # 아티팩트 관리자 권한: 모든 속성 피해 30%
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + (
            NEON_PARTY_ALL_ELEM_ADD
        )

        # 아티팩트 치트키·치명적 오류: 궁극기 받는 피해 증가
        stats["enemy_ult_taken_inc"] = float(stats.get("enemy_ult_taken_inc", 0.0)) + (
            NEON_PARTY_ENEMY_ULT_TAKEN_INC
        )

    # =====================================================
    # [쿠키] 달빛술사 쿠키
    # [역할] 파티 디버프 / 달빛 환대 영역 / 공격력 버프
    # - 달과 별의 노래: 방어력 감소 28%
    # - 찬란한 꿈의 끝자락: 달빛 환대 영역 내 아군 최종 피해 +25%
    # - 한밤의 자장가: 공격력 증가 +30% (아티팩트 공증, 벞증 미적용)
    # - 고요히 흐르는 월광: 모든 속성 피해·치명타 피해 50%
    # - 전용 아티팩트 치피와 승급 신비공/치피는 달빛술사 본인 계산에서만 적용
    # =====================================================
    def _apply_moonlight_party_effects():
        if not has_moonlight:
            return

        # 궁극기 선잠: 방어력 감소 28%
        # 디버프 증폭은 파티 합산이 아니라 달빛술사 본인의 디버프 증폭만 적용
        moon_def_down = 0.28 * _debuff_scale_for_owner("달빛술사 쿠키")
        stats["def_reduction_no_scale_raw"] = float(stats.get("def_reduction_no_scale_raw", 0.0)) + moon_def_down
        stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + moon_def_down

        # 달빛 환대 영역: 최종 피해 +25%
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + 0.25

        # 파티원으로 들어간 달빛술사 공유 효과
        # - 아군 공유: [한밤의 자장가] 공격력 증가, [달무리] 보호막 생성
        # - 본인 전용: [아름다운 밤의 산책], [새벽의 안내자],
        # [고요히 흐르는 월광] 모든 속성 피해/치명타 피해
        # 보호막: 멜랑크림 쿠키의 순수한 기억 유지 조건
        if in_party_moonlight and main_cookie_name != "달빛술사 쿠키":
            # 한밤의 자장가 공격력 +30%는 아티팩트 공증으로 처리
            # 달빛술사 본인 버프 증폭 제외
            add_final_atk = 0.30
            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk

            # 고요히 흐르는 월광 모든 속성 피해 50% 본인 전용
            # 파티 달빛술사 메인 딜러 추가 적용 제외

    # =====================================================
    # 6) 파티원 시즈 패시브 합산
    # =====================================================
    FIXED_PARTY_SEAZ: Dict[str, str] = {
        "이슬맛 쿠키": "허브그린드:번뜩이는 기지",
        "샬롯맛 쿠키": "허브그린드:가벼운 손길",
        "네온데니쉬맛 쿠키": "허브그린드:작은 성배",
        "달빛술사 쿠키": "플럼나이트:달빛의 속삭임",
        "윈드파라거스 쿠키": "리치코랄:믿음직한 브리더",
        "룽샤맛 쿠키": "리치코랄:빛나는 은하수",
        "마블베리맛 쿠키": "리치코랄:빛나는 은하수",
        "밀키웨이맛 쿠키": "리치코랄:빛나는 은하수",
        "스테인드누가맛 쿠키": "리치코랄:빛나는 은하수",
        "스타더스트 쿠키": "페퍼루비:영예로운 기사도",
    }
    def _get_party_seaz_name(cookie_name: str) -> str:
        # 1) 화면·외부 입력 딕셔너리 우선
        m = stats.get("party_seaz")
        if isinstance(m, dict):
            v = m.get(cookie_name, "")
            if v and v != "NONE":
                return str(v)

        # 2) 개별 키 형태도 지원(원하면)
        v2 = stats.get(f"seaz__{cookie_name}", "")
        if v2 and v2 != "NONE":
            return str(v2)

        # 3) 파티원 고정값 대체
        if cookie_name in (party or []) and cookie_name != main_cookie_name:
            return FIXED_PARTY_SEAZ.get(cookie_name, "")

        return ""

    def _apply_party_member_seaz(cookie_name: str):
        if main_cookie_name == cookie_name:
            return
        if cookie_name not in party:
            return

        seaz = _get_party_seaz_name(cookie_name)
        if not seaz:
            return

        # 1) 파티 시즈 공용 패시브
        apply_seaz_passive(
            stats, seaz,
            owner_cookie_name=cookie_name,      # 파티원(그 쿠키)의 시즈
            main_cookie_name=main_cookie_name   # 현재 메인
        )

        # 2) 파티 시즈 보조 옵션 규칙
        # - 시즈나이트 보조옵션은 기본적으로 장착자 본인에게만 적용
        # - 파티원 시즈 속성 강타 피해만 메인 공유
        # - 리치코랄 브리더 보조 옵션
        # 속성 강타 피해 +25% → 파티 공유
        # - 특수·궁극기 피해 15% 윈파 본인 전용
        # - 페퍼루비 브리더 기본·치명타 피해 윈파 본인 전용
        info = SEAZNITES.get(seaz, {}) or {}
        sub = info.get("sub", {}) or {}
        if sub and "element_strike_dmg" in sub:
            stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + float(sub["element_strike_dmg"])

        # 3) 파티 시즈 패시브 직접 스탯 추가
        passive = info.get("passive", {}) or {}
        if passive:
            for k in ("basic_dmg", "special_dmg", "ult_dmg", "passive_dmg", "final_dmg", "atk_spd", "move_spd"):
                if k in passive:
                    stats[k] = float(stats.get(k, 0.0)) + float(passive[k])

            if "final_dmg_stack" in passive and "max_stacks" in passive:
                stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + (float(passive["final_dmg_stack"]) * float(passive["max_stacks"]))

            # 달빛의 속삭임: 버프 증폭량 + 디버프 증폭량의 100%만큼
            # 시즈 모든 속성 피해 최대 100% 본인 전용
            # 파티 쿠키 장착 효과 메인 딜러 공유 제외
            # 메인 착용자 본인 효과: 시즈 패시브 본인 전용 처리

    # =====================================================
    # 7) 파티원 유니크 설유 효과 합산
    # =====================================================
    FIXED_PARTY_UNIQUE: Dict[str, str] = {
        cookie_name: get_default_party_unique(cookie_name)
        for cookie_name in (
            "이슬맛 쿠키",
            "샬롯맛 쿠키",
            "네온데니쉬맛 쿠키",
            "달빛술사 쿠키",
            "윈드파라거스 쿠키",
            "룽샤맛 쿠키",
            "마블베리맛 쿠키",
            "밀키웨이맛 쿠키",
            "체리콜라맛 쿠키",
            "스테인드누가맛 쿠키",
        )
    }

    def _apply_party_member_unique(cookie_name: str):
        if main_cookie_name == cookie_name:
            return
        if cookie_name not in party:
            return

        u_map = party_uniques or stats.get("party_uniques") or {}
        try:
            u_name = str(u_map.get(cookie_name, "")) if u_map else ""
        except Exception:
            u_name = ""

        if (not u_name) or (u_name.upper() == "AUTO"):
            u_name = FIXED_PARTY_UNIQUE.get(cookie_name, "")

        if (not u_name) or (u_name == "NONE"):
            return

        orig_ba = float(stats.get("buff_amp", 0.0))
        orig_da = float(stats.get("debuff_amp", 0.0))
        try:
            stats["buff_amp"]   = float(stats.get("party_buff_amp_total", orig_ba))
            stats["debuff_amp"] = float(stats.get("party_debuff_amp_total", orig_da))
            apply_unique(stats, cookie_name, u_name, is_owner=False)
        finally:
            stats["buff_amp"]   = orig_ba
            stats["debuff_amp"] = orig_da

    # =====================================================
    # 8) 적용 순서
    # =====================================================

    # (0) 파티 유니크 선반영
    _apply_once("PARTY_UNIQUE_ISLE",       lambda: _apply_party_member_unique("이슬맛 쿠키"))
    _apply_once("PARTY_UNIQUE_CHARLOTTE",  lambda: _apply_party_member_unique("샬롯맛 쿠키"))
    _apply_once("PARTY_UNIQUE_NEON",      lambda: _apply_party_member_unique("네온데니쉬맛 쿠키"))
    _apply_once("PARTY_UNIQUE_MOONLIGHT", lambda: _apply_party_member_unique("달빛술사 쿠키"))
    _apply_once("PARTY_UNIQUE_WIND",       lambda: _apply_party_member_unique("윈드파라거스 쿠키"))
    _apply_once("PARTY_UNIQUE_LUNGSHA",    lambda: _apply_party_member_unique("룽샤맛 쿠키"))
    _apply_once("PARTY_UNIQUE_MARBLE",     lambda: _apply_party_member_unique("마블베리맛 쿠키"))
    _apply_once("PARTY_UNIQUE_MILKY",      lambda: _apply_party_member_unique("밀키웨이맛 쿠키"))
    _apply_once("PARTY_UNIQUE_CHERRY_COLA", lambda: _apply_party_member_unique("체리콜라맛 쿠키"))
    _apply_once("PARTY_UNIQUE_STAINED_NOUGAT", lambda: _apply_party_member_unique("스테인드누가맛 쿠키"))

    # (1) 쿠키 파티버프/오라
    if has_char:
        # 샬롯 희미한 날갯짓: 파티 효과에서 1회 적용
        _apply_once("PARTY_CHARLOTTE", _apply_charlotte_party_effects)

    if has_isle:
        _apply_once("PARTY_ISLE", _apply_isle_buffs)

    if has_neon:
        _apply_once("PARTY_NEON", _apply_neon_party_effects)

    if has_moonlight:
        _apply_once("PARTY_MOONLIGHT", _apply_moonlight_party_effects)

    if has_wind:
        _apply_once("PARTY_WIND", _apply_wind_party_effects)

    if has_lungsha:
        _apply_once("PARTY_LUNGSHA", _apply_lungsha_party_effects)

    if has_marble:
        _apply_once("PARTY_MARBLE", _apply_marble_party_effects)

    if has_milky:
        _apply_once("PARTY_MILKY", _apply_milky_way_party_effects)

    if has_cherry_cola:
        _apply_once("PARTY_CHERRY_COLA", _apply_cherry_cola_party_effects)

    if has_stained_nougat:
        _apply_once("PARTY_STAINED_NOUGAT", _apply_stained_nougat_party_effects)

    # (2) 파티 시즈 패시브
    _apply_once("PARTY_SEAZ_ISLE",       lambda: _apply_party_member_seaz("이슬맛 쿠키"))
    _apply_once("PARTY_SEAZ_CHARLOTTE",  lambda: _apply_party_member_seaz("샬롯맛 쿠키"))
    _apply_once("PARTY_SEAZ_NEON",      lambda: _apply_party_member_seaz("네온데니쉬맛 쿠키"))
    _apply_once("PARTY_SEAZ_MOONLIGHT", lambda: _apply_party_member_seaz("달빛술사 쿠키"))
    _apply_once("PARTY_SEAZ_WIND",       lambda: _apply_party_member_seaz("윈드파라거스 쿠키"))
    _apply_once("PARTY_SEAZ_LUNGSHA",    lambda: _apply_party_member_seaz("룽샤맛 쿠키"))
    _apply_once("PARTY_SEAZ_MARBLE",     lambda: _apply_party_member_seaz("마블베리맛 쿠키"))
    _apply_once("PARTY_SEAZ_MILKY",      lambda: _apply_party_member_seaz("밀키웨이맛 쿠키"))
    _apply_once("PARTY_SEAZ_CHERRY_COLA", lambda: _apply_party_member_seaz("체리콜라맛 쿠키"))
    _apply_once("PARTY_SEAZ_STAINED_NOUGAT", lambda: _apply_party_member_seaz("스테인드누가맛 쿠키"))
    _apply_once("PARTY_SEAZ_STARDUST", lambda: _apply_party_member_seaz("스타더스트 쿠키"))

    # 파티원 증폭값 효과별 계산 전용
    # 메인 쿠키 본인 증폭값 복원
    stats["buff_amp"] = float(stats.get("self_buff_amp_total", stats.get("buff_amp_total", stats.get("buff_amp", 0.0))))
    stats["debuff_amp"] = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))

    # 최종 스탯 표의 '(파티) 버프/디버프 증폭'은 각 쿠키의 개인 증폭량을
    # 한 번씩만 합산한 값으로 정규화
    # 파티 유니크 증폭 중복 보정
    amp_owners = [main_cookie_name]
    amp_owners.extend(
        cookie_name for cookie_name in (party or [])
        if cookie_name and cookie_name != main_cookie_name and cookie_name not in amp_owners
    )
    stats["party_buff_amp_total"] = sum(_buff_amp_for_owner(cookie_name) for cookie_name in amp_owners)
    stats["party_debuff_amp_total"] = sum(_debuff_amp_for_owner(cookie_name) for cookie_name in amp_owners)

    return stats

# 호감도 공격력 데이터

def calc_attack_value(stats: Dict[str, float], *, floor_result: bool = False) -> float:
    """최종 공격력 계산"""
    OA = float(stats.get("base_atk", 0.0)) + float(stats.get("equip_atk_flat", 0.0))
    EA = float(stats.get("base_elem_atk", 0.0)) + float(stats.get("elem_atk", 0.0))
    friendship = float(stats.get("friendship_atk", 0.0))
    atk_pct_sum = float(stats.get("base_atk_pct", 0.0)) + float(stats.get("atk_pct", 0.0))
    buff_atk_pct_sum = float(stats.get("buff_atk_pct_raw", 0.0)) + float(stats.get("final_atk_mult", 0.0))
    buff_atk_mult = float(stats.get("buff_atk_mult", 1.0))

    base_part = max(0.0, OA + EA)
    value = base_part * (1.0 + atk_pct_sum) * (1.0 + buff_atk_pct_sum) * buff_atk_mult + friendship
    return float(math.floor(value)) if floor_result else float(value)

def attack_formula_parts(stats: Dict[str, float]) -> Dict[str, float]:
    OA = float(stats.get("base_atk", 0.0)) + float(stats.get("equip_atk_flat", 0.0))
    EA = float(stats.get("base_elem_atk", 0.0)) + float(stats.get("elem_atk", 0.0))
    friendship = float(stats.get("friendship_atk", 0.0))
    atk_pct_sum = float(stats.get("base_atk_pct", 0.0)) + float(stats.get("atk_pct", 0.0))
    buff_atk_pct_sum = float(stats.get("buff_atk_pct_raw", 0.0)) + float(stats.get("final_atk_mult", 0.0))
    buff_atk_mult = float(stats.get("buff_atk_mult", 1.0))
    return {
        "OA": OA,
        "EA": EA,
        "friendship_atk": friendship,
        "atk_pct_sum": atk_pct_sum,
        "buff_atk_pct_sum": buff_atk_pct_sum,
        "buff_atk_mult": buff_atk_mult,
        "final_attack": calc_attack_value(stats, floor_result=False),
    }

# =====================================================
# 10) 공통: 딜 공식 / 요약 스탯
# =====================================================
def summarize_effective_stats(stats: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    s = stats or {}

    # 공격력(공퍼) 관련
    parts = attack_formula_parts(s)
    self_atk_pct_add = parts["atk_pct_sum"]
    party_atk_pct_buff = parts["buff_atk_pct_sum"]
    equip_atk_mult = 1.0 + self_atk_pct_add
    buff_atk_mult = parts["buff_atk_mult"]
    atk_pct_equiv = self_atk_pct_add
    atk_pct_sum = self_atk_pct_add

    # 치확/치피 (표시용)
    eff_cr = clamp(
        float(s.get("crit_rate", 0.0)) + float(s.get("buff_crit_rate_raw", 0.0)),
        0.0, 1.0
    )

    # 총 치명타 피해 배율 기준 계산
    eff_cd_mult = max(1.0, float(s.get("crit_dmg", 1.0)) + float(s.get("buff_crit_dmg_raw", 0.0)))
    eff_cd_total_pct = eff_cd_mult * 100.0
    eff_cd_bonus_pct = (eff_cd_mult - 1.0) * 100.0  # 참고용: +90% 같은 “추가치피”

    # 속성/방관/디버프
    eff_all_elem = float(s.get("all_elem_dmg", 0.0)) + float(s.get("buff_all_elem_dmg_raw", 0.0))
    eff_armor_pen = clamp(
        float(s.get("armor_pen", 0.0)) + float(s.get("buff_armor_pen_raw", 0.0)),
        0.0, 0.8
    )

    # 원본 디버프 축 메인 본인 증폭만 적용
    # 파티원 개인 디버프 증폭 선반영 후 비증폭 축 적용
    DA = float(s.get("self_debuff_amp_total", s.get("debuff_amp_total", s.get("debuff_amp", 0.0))))
    debuff_scale = 1.0 + DA

    eff_def_red = clamp(
        float(s.get("def_reduction_raw", 0.0)) * debuff_scale
        + float(s.get("def_reduction_no_scale_raw", 0.0)),
        0.0,
        DEF_REDUCTION_CAP
    )
    eff_elem_res_red = (
        float(s.get("elem_res_reduction_raw", 0.0)) * debuff_scale
        + float(s.get("elem_res_reduction_no_scale_raw", 0.0))
    )
    eff_mark_res_red = (
        float(s.get("elem_res_reduction_raw", 0.0)) * debuff_scale
        + float(s.get("mark_res_reduction_no_scale_raw", 0.0))
    )

    eff_dmg_bonus = float(s.get("dmg_bonus", 0.0)) + float(s.get("buff_dmg_bonus_raw", 0.0))

    # =====================================================
    # 패시브 표시값·승급 제외
    # =====================================================
    p = float(s.get("passive_dmg", 0.0))                 # 스탯 가산
    t = float(s.get("enemy_passive_taken_inc", 0.0))     # 스탯 가산
    m = float(s.get("passive_dmg_mult", 1.0))            # 배율 예시 1.20

    passive_total_mult = (1.0 + p) * (1.0 + t) * m
    passive_total_bonus = passive_total_mult - 1.0
    passive_total_pct = passive_total_mult * 100.0

    return {
        "numeric": {
            # 공격력
            "equip_atk_mult": equip_atk_mult,
            "buff_atk_mult": buff_atk_mult,
            "atk_pct_sum": atk_pct_sum,
            "self_atk_pct_add": self_atk_pct_add,
            "party_atk_pct_buff": party_atk_pct_buff,
            "atk_pct_equiv": atk_pct_equiv,
            "friendship_atk": parts["friendship_atk"],
            "final_attack": parts["final_attack"],

            "final_atk_mult_add": party_atk_pct_buff,
            "final_atk_mult_display": party_atk_pct_buff,
            "party_final_atk_display": float(s.get("buff_final_atk_mult", 0.0)) + float(s.get("buff_atk_pct_raw", 0.0)),

            # 치명타
            "eff_crit_rate": eff_cr,
            "eff_crit_dmg_mult": eff_cd_mult,          # 1.90
            "eff_crit_dmg_total_pct": eff_cd_total_pct, # 190.0
            "eff_crit_dmg_bonus_pct": eff_cd_bonus_pct, # 90.0

            # 기타
            "eff_all_elem_dmg": eff_all_elem,
            "eff_armor_pen": eff_armor_pen,
            "eff_def_reduction": eff_def_red,
            "eff_elem_res_reduction": eff_elem_res_red,
            "eff_mark_res_reduction": eff_mark_res_red,
            "dmg_bonus": eff_dmg_bonus,

            # 패시브 표시값
            "passive_total_mult": passive_total_mult,       # 1.69092
            "passive_total_pct": passive_total_pct,         # 169.092
            "passive_total_bonus": passive_total_bonus,     # 0.69092

            "passive_dmg_add": p,
            "enemy_passive_taken_inc_add": t,
            "passive_dmg_mult": m,

            "buff_amp": float(s.get("buff_amp", 0.0)),
            "debuff_amp": DA,
            "element_strike_dmg": float(s.get("element_strike_dmg", 0.0)),
            "element_mark_explosion_dmg": float(s.get("element_mark_explosion_dmg", 0.0)),
        }
    }

def build_damage_context(stats: Dict[str, float]) -> Dict[str, float]:
    """피해 계산 공통값 캐시"""
    cached = stats.get("_damage_context_cache", None)
    if isinstance(cached, dict):
        return cached

    get = stats.get
    cr = clamp(
        float(get("crit_rate", 0.0)) + float(get("buff_crit_rate_raw", 0.0)),
        0.0, 1.0
    )

    armor_pen = clamp(
        float(get("armor_pen", 0.0)) + float(get("buff_armor_pen_raw", 0.0)),
        0.0, 0.8
    )

    cd_base = float(get("crit_dmg", 1.0))
    cd_mult = max(1.0, cd_base + float(get("buff_crit_dmg_raw", 0.0)))
    crit_mult = 1.0 + cr * (cd_mult - 1.0)

    parts = attack_formula_parts(stats)
    OA = parts["OA"]
    EA = parts["EA"]
    atk_mult = (1.0 + parts["atk_pct_sum"]) * (1.0 + parts["buff_atk_pct_sum"]) * parts["buff_atk_mult"]
    final_atk = 1.0

    DA = float(get("self_debuff_amp_total", get("debuff_amp_total", get("debuff_amp", 0.0))))
    debuff_scale = 1.0 + DA

    def_reduction_skill = float(get("def_reduction_raw", 0.0)) * debuff_scale
    def_reduction_fixed = float(get("def_reduction_no_scale_raw", 0.0))
    def_reduction = clamp(def_reduction_skill + def_reduction_fixed, 0.0, DEF_REDUCTION_CAP)
    defense_mult = 1.0 / (1.0 + DEFENSE_K * (1.0 - armor_pen) * (1.0 - def_reduction))

    boss_resist = float(get("boss_elem_resist", 0.0))
    res_red_skill = float(get("elem_res_reduction_raw", 0.0)) * debuff_scale
    res_red_fixed = float(get("elem_res_reduction_no_scale_raw", 0.0))
    res_red = res_red_skill + res_red_fixed
    eff_resist = clamp(boss_resist - res_red, -0.95, 0.95)
    elem_res_mult = 1.0 - eff_resist

    basic_mult = (1.0 + float(get("basic_dmg", 0.0))) * (1.0 + float(get("enemy_basic_taken_inc", 0.0)))
    special_mult = 1.0 + float(get("special_dmg", 0.0))
    ult_mult = (1.0 + float(get("ult_dmg", 0.0))) * (1.0 + float(get("enemy_ult_taken_inc", 0.0)))
    passive_mult = (
        (1.0 + float(get("passive_dmg", 0.0)))
        * (1.0 + float(get("enemy_passive_taken_inc", 0.0)))
        * float(get("passive_dmg_mult", 1.0))
    )

    floor = math.floor
    atk_base = floor(max(0.0, OA + EA))
    pre_coeff_damage = calc_attack_value(stats, floor_result=True)

    ctx = {
        "atk_base": atk_base,
        "pre_coeff_damage": pre_coeff_damage,
        "atk_mult": atk_mult,
        "final_atk": final_atk,
        "crit_mult": crit_mult,
        "defense_mult": defense_mult,
        "elem_res_mult": elem_res_mult,
        "all_elem_mult": 1.0 + float(get("all_elem_dmg", 0.0)) + float(get("buff_all_elem_dmg_raw", 0.0)),
        "dmg_bonus_mult": 1.0 + float(get("dmg_bonus", 0.0)),
        "final_dmg_mult": 1.0 + float(get("final_dmg", 0.0)),
        "recommended_mult": float(get("recommended_mult", 1.0)),
        # 일반 받는 피해 증가 축
        # - 쿠키 자체 받는 피해 증가
        # - 적 대상 받는 피해 증가
        # 서로 다른 받는 피해 증가 축 별도 곱연산
        "taken_mult": (1.0 + float(get("dmg_taken_inc", 0.0))) * (1.0 + float(get("enemy_dmg_taken_inc", 0.0))),
        "skill_bonus_mults": {
            "none": 1.0,
            "basic": basic_mult,
            "special": special_mult,
            "ult": ult_mult,
            "passive": passive_mult,
        },
    }

    stats["_damage_context_cache"] = ctx
    return ctx

def skill_damage_from_start(
    stats: Dict[str, float],
    coeff: float,
    skill_type: str = "none",
    *,
    extra_skill_mult: float = 1.0,
) -> float:
    """스킬 피해 계산"""
    ctx = build_damage_context(stats)
    floor = math.floor
    skill_mult = ctx["skill_bonus_mults"].get(skill_type, 1.0)

    dmg = floor(int(ctx["pre_coeff_damage"]) * float(coeff))
    dmg = floor(dmg * skill_mult * float(extra_skill_mult))
    dmg = floor(dmg * ctx["dmg_bonus_mult"])
    dmg = floor(dmg * ctx["crit_mult"])
    dmg = floor(dmg * ctx["defense_mult"])
    dmg = floor(dmg * ctx["elem_res_mult"])
    dmg = floor(dmg * ctx["taken_mult"])
    dmg = floor(dmg * ctx["all_elem_mult"])
    dmg = floor(dmg * ctx["final_dmg_mult"])
    dmg = floor(dmg * ctx["recommended_mult"])

    return float(dmg)

def strike_total_from_direct(
    direct_damage: float,
    cookie_name_kr: str,
    stats: Dict[str, float],
    party: List[str]
) -> float:
    # 표식은 스트라이커가 있어야 생김
    marker_cookie = None
    if COOKIE_ROLE.get(cookie_name_kr) == "strike":
        marker_cookie = cookie_name_kr
    else:
        for p in (party or []):
            if COOKIE_ROLE.get(p) == "strike":
                marker_cookie = p
                break

    if not marker_cookie:
        return 0.0

    # 속성강타 정식식
    # - 공식:
    # 표식에 들어간 총 데미지
    # × 0.712
    # × (1 - (보스 기본 속성 내성 - 속성 내성 감소))
    # × (1 + 속성강타 피해 증가)
    # - 속성 내성 감소: 증폭 축·비증폭 축 분리 합산
    # - 같은 속성/다른 속성 차이는 게이지 축적 속도 문제로 보고,
    # 현재 사이클 총딜 기반 계산에서는 속성강타 데미지를 추가 절반 처리하지 않음
    base_damage = max(float(direct_damage), 0.0)

    # 표식 속성 내성 배율
    DA = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))
    debuff_scale = 1.0 + DA

    mark_res_red = (
        float(stats.get("elem_res_reduction_raw", 0.0)) * debuff_scale
        + float(stats.get("elem_res_reduction_no_scale_raw", 0.0))
        + float(stats.get("mark_res_reduction_no_scale_raw", 0.0))
    )

    boss_mark_resist = float(stats.get("boss_mark_resist", BOSS_MARK_ELEMENT_RESIST_DEFAULT))
    final_mark_resist = clamp(boss_mark_resist - mark_res_red, -0.95, 0.95)
    mark_res_mult = 1.0 - final_mark_resist

    # 속성강타 피해 증가(시즈나이트/오라 등)
    es = float(stats.get("element_strike_dmg", 0.0))

    # 강화속성표식 피해 증가(꿈열차에 실린 기억)
    # - 일반 속성강타 피해에 합산하지 않고 표식 폭발에만 별도 곱연산
    mark_explosion_bonus = float(stats.get("element_mark_explosion_dmg", 0.0))

    # 원소의 설탕유리조각
    # - 표식/강타 치명타 확률 + 치명타 피해 증가를 기대값으로 반영
    mark_cr = clamp(float(stats.get("sugar_mark_crit_rate", 0.0)), 0.0, 1.0)
    mark_cd_bonus = max(float(stats.get("sugar_mark_crit_dmg", 0.0)), 0.0)
    mark_crit_mult = 1.0 + mark_cr * mark_cd_bonus

    return (
        base_damage
        * ELEMENT_STRIKE_BASE_COEFF
        * mark_res_mult
        * (1.0 + es)
        * (1.0 + mark_explosion_bonus)
        * mark_crit_mult
    )

# =====================================================
# 12) 파티 증폭 합산(표시/팀공유 가정) + 스탯 빌더
# =====================================================

# =====================================================
# 파티 가정값
# =====================================================
def _assumed_isle_buff_amp_for_party() -> float:
    from .dew import BASE_STATS_ISLE, ISLE_FIXED_POT, ISLE_FIXED_ARTIFACT

    ba = 0.0

    try:
        ba += float(BASE_STATS_ISLE["이슬맛 쿠키"].get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        ba += float(ISLE_FIXED_POT.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        a = ARTIFACTS.get(ISLE_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        seaz = SEAZNITES.get(globals().get("FIXED_SEAZ_ISLE", "허브그린드:번뜩이는 기지"), {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    return ba

def _assumed_charlotte_buff_amp_for_party() -> float:
    from .shallot import (
        BASE_STATS_CHARLOTTE,
        CHARLOTTE_FIXED_POT,
        CHARLOTTE_FIXED_ARTIFACT,
    )

    ba = 0.0

    try:
        ba += float(BASE_STATS_CHARLOTTE["샬롯맛 쿠키"].get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        ba += float(CHARLOTTE_FIXED_POT.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        a = ARTIFACTS.get(CHARLOTTE_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        fixed_seaz = globals().get("FIXED_SEAZ_CHARLOTTE", "허브그린드:가벼운 손길")
        seaz = SEAZNITES.get(fixed_seaz, {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    return ba

def _assumed_neon_buff_amp_for_party() -> float:
    from .neon_danish import (
        BASE_STATS_NEON,
        NEON_POTENTIALS_FIXED,
        NEON_FIXED_ARTIFACT,
    )

    ba = 0.0

    try:
        ba += float(BASE_STATS_NEON["네온데니쉬맛 쿠키"].get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        ba += float(NEON_POTENTIALS_FIXED.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        a = ARTIFACTS.get(NEON_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        fixed_seaz = globals().get("FIXED_SEAZ_NEON", "허브그린드:작은 성배")
        seaz = SEAZNITES.get(fixed_seaz, {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    return ba

MOONLIGHT_DEBUFF_AMP_TARGET = 1.50
MOONLIGHT_POTENTIAL_SLOTS = 8
# 달빛술사 증폭 잠재력 합계 최대 4칸

def _moonlight_equip_debuff_amp(equip_name: str) -> float:
    """달빛술사 장비 디버프 증폭"""
    if not equip_name:
        return 0.0
    equip = EQUIP_SETS.get(str(equip_name), {}) or {}
    total = 0.0
    try:
        total += float((((equip.get("set_effect", {}) or {}).get("base", {}) or {}).get("debuff_amp", 0.0)))
    except Exception:
        pass
    try:
        for part in ("head", "top", "bottom"):
            total += float((((equip.get(part, {}) or {}).get("unique", {}) or {}).get("debuff_amp", 0.0)))
    except Exception:
        pass
    return total

def _moonlight_unique_debuff_amp(unique_name: str) -> float:
    if str(unique_name) == "NONE":
        return 0.0
    if (not unique_name) or str(unique_name).upper() == "AUTO":
        unique_name = get_default_party_unique("달빛술사 쿠키") or "달빛술사 쿠키의 기억"
    try:
        if not is_unique_allowed("달빛술사 쿠키", str(unique_name)):
            return 0.0
        return float((UNIQUE_SHARDS.get(str(unique_name), {}) or {}).get("debuff_amp_add", 0.0))
    except Exception:
        return 0.0

def _moonlight_seaz_debuff_amp(seaz_name: str) -> float:
    if (not seaz_name) or str(seaz_name).upper() == "AUTO" or str(seaz_name) == "NONE":
        seaz_name = "플럼나이트:달빛의 속삭임"
    try:
        return float(((SEAZNITES.get(str(seaz_name), {}) or {}).get("sub", {}) or {}).get("debuff_amp", 0.0))
    except Exception:
        return 0.0

def _moonlight_base_debuff_amp_without_potential(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "달빛술사 쿠키의 기억",
) -> float:
    """달빛술사 잠재력 제외 디버프 증폭"""
    da = 0.15 + 0.24  # 기본 디버프 증폭 + 전용무기
    try:
        da += float((ARTIFACTS.get("고요히 흐르는 월광", {}).get("base_stats") or {}).get("debuff_amp", 0.0))
    except Exception:
        pass
    da += _moonlight_seaz_debuff_amp(seaz_name)
    da += _moonlight_equip_debuff_amp(equip_name or "시간관리국의 제복")
    da += _moonlight_unique_debuff_amp(unique_name or get_default_party_unique("달빛술사 쿠키") or "달빛술사 쿠키의 기억")
    return max(0.0, da)

def moonlight_fixed_debuff_slots_for_equip(equip_name: str) -> int:
    """달빛술사 장비별 고정 디버프 잠재력"""
    name = str(equip_name or "")
    if name == "유성우의 향연":
        return 1
    if name == "시간관리국의 제복":
        return 4
    return 0

def moonlight_auto_potentials_for_combo(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "달빛술사 쿠키의 기억",
    target_debuff_amp: float = MOONLIGHT_DEBUFF_AMP_TARGET,
    total_slots: int = MOONLIGHT_POTENTIAL_SLOTS,
) -> Dict[str, int]:
    """달빛술사 자동 잠재력 기본값"""
    del seaz_name, unique_name, target_debuff_amp
    total_slots = max(0, int(total_slots or 0))
    debuff_slots = min(total_slots, moonlight_fixed_debuff_slots_for_equip(equip_name))
    atk_slots = max(0, total_slots - debuff_slots)
    return {
        "atk_pct": atk_slots,
        "debuff_amp": debuff_slots,
        "buff_amp": 0,
        "elem_atk": 0,
        "crit_rate": 0,
        "crit_dmg": 0,
        "armor_pen": 0,
    }

def _assumed_moonlight_buff_amp_for_party(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "달빛술사 쿠키의 기억",
) -> float:
    """파티 달빛술사 버프 증폭 가정값"""
    return 0.0

def _assumed_moonlight_debuff_amp_for_party(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "달빛술사 쿠키의 기억",
) -> float:
    """파티 달빛술사 디버프 증폭 가정값"""
    pot = moonlight_auto_potentials_for_combo(equip_name, seaz_name, unique_name)
    da = _moonlight_base_debuff_amp_without_potential(equip_name, seaz_name, unique_name)
    try:
        da += float(pot.get("debuff_amp", 0)) * float(POTENTIAL_INC["debuff_amp"])
    except Exception:
        pass
    return max(0.0, da)

def _assumed_lungsha_debuff_amp_for_party(main_cookie_name: str) -> float:
    """파티 룽샤 디버프 증폭 가정값"""
    return 0.0

def _assumed_marble_debuff_amp_for_party() -> float:
    """파티 마블베리 디버프 증폭 가정값"""
    return 0.0

def _assumed_milky_way_debuff_amp_for_party() -> float:
    """파티 밀키웨이 디버프 증폭 가정값"""
    return 0.0

def _assumed_wind_debuff_amp_for_party() -> float:
    """파티 윈드파라거스 디버프 증폭 가정값"""
    da = 0.0

    try:
        da += 4.0 * float(POTENTIAL_INC["debuff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    try:
        da += float(ARTIFACTS["이어지는 마음"]["unique_stats"].get("debuff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리
        pass

    return da

def _apply_neon_main_effects(stats: Dict[str, float], main_cookie_name: str) -> None:
    """네온데니쉬 메인 효과"""
    if main_cookie_name != "네온데니쉬맛 쿠키":
        return

    BA_total = float(stats.get("buff_amp_total", stats.get("buff_amp", 0.0)))
    innate_scale = 1.0 + BA_total

    add_final_atk = 0.346 * innate_scale
    add_ult_dmg = 0.15 * innate_scale

    stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
    stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk
    stats["ult_dmg"] = float(stats.get("ult_dmg", 0.0)) + add_ult_dmg
    stats["enemy_ult_taken_inc"] = float(stats.get("enemy_ult_taken_inc", 0.0)) + (0.08 + 0.058)

def _apply_party_amp_totals(stats: Dict[str, float], party: List[str], main_cookie_name: str) -> None:

    base_ba = float(stats.get("buff_amp_total", stats.get("buff_amp", 0.0)))
    base_da = float(stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)))

    ba = base_ba
    da = base_da

    party_seaz_map = stats.get("party_seaz")
    if not isinstance(party_seaz_map, dict):
        party_seaz_map = {}

    party_sets_map = stats.get("party_sets")
    if not isinstance(party_sets_map, dict):
        party_sets_map = {}

    party_uniques_map = stats.get("party_uniques")
    if not isinstance(party_uniques_map, dict):
        party_uniques_map = {}

    fixed_party_seaz = {
        "이슬맛 쿠키": "허브그린드:번뜩이는 기지",
        "샬롯맛 쿠키": "허브그린드:가벼운 손길",
        "네온데니쉬맛 쿠키": "허브그린드:작은 성배",
        "달빛술사 쿠키": "플럼나이트:달빛의 속삭임",
    }

    def _selected_party_sub_buff_amp(cookie_name: str) -> float:
        selected = str(party_seaz_map.get(cookie_name, "") or "")
        if (not selected) or (selected.upper() == "AUTO"):
            selected = fixed_party_seaz.get(cookie_name, "")
        seaz = SEAZNITES.get(selected, {})
        return float((seaz.get("sub") or {}).get("buff_amp", 0.0))

    def _fixed_party_sub_buff_amp(cookie_name: str) -> float:
        fixed = fixed_party_seaz.get(cookie_name, "")
        seaz = SEAZNITES.get(fixed, {})
        return float((seaz.get("sub") or {}).get("buff_amp", 0.0))

    def _selected_party_sub_debuff_amp(cookie_name: str) -> float:
        selected = str(party_seaz_map.get(cookie_name, "") or "")
        if (not selected) or (selected.upper() == "AUTO"):
            selected = fixed_party_seaz.get(cookie_name, "")
        seaz = SEAZNITES.get(selected, {})
        return float((seaz.get("sub") or {}).get("debuff_amp", 0.0))

    def _fixed_party_sub_debuff_amp(cookie_name: str) -> float:
        fixed = fixed_party_seaz.get(cookie_name, "")
        seaz = SEAZNITES.get(fixed, {})
        return float((seaz.get("sub") or {}).get("debuff_amp", 0.0))

    if "이슬맛 쿠키" in (party or []) and main_cookie_name != "이슬맛 쿠키":
        ba += _assumed_isle_buff_amp_for_party()
        ba += _selected_party_sub_buff_amp("이슬맛 쿠키") - _fixed_party_sub_buff_amp("이슬맛 쿠키")

    if "샬롯맛 쿠키" in (party or []) and main_cookie_name != "샬롯맛 쿠키":
        ba += _assumed_charlotte_buff_amp_for_party()
        ba += _selected_party_sub_buff_amp("샬롯맛 쿠키") - _fixed_party_sub_buff_amp("샬롯맛 쿠키")

    if "네온데니쉬맛 쿠키" in (party or []) and main_cookie_name != "네온데니쉬맛 쿠키":
        ba += _assumed_neon_buff_amp_for_party()
        ba += _selected_party_sub_buff_amp("네온데니쉬맛 쿠키") - _fixed_party_sub_buff_amp("네온데니쉬맛 쿠키")

    if "달빛술사 쿠키" in (party or []) and main_cookie_name != "달빛술사 쿠키":
        moon_equip_for_ba = str(party_sets_map.get("달빛술사 쿠키", "") or "")
        if (not moon_equip_for_ba) or moon_equip_for_ba.upper() == "AUTO" or moon_equip_for_ba == "NONE":
            moon_equip_for_ba = "시간관리국의 제복"
        moon_seaz_for_ba = str(party_seaz_map.get("달빛술사 쿠키", "") or "")
        if (not moon_seaz_for_ba) or moon_seaz_for_ba.upper() == "AUTO" or moon_seaz_for_ba == "NONE":
            moon_seaz_for_ba = "플럼나이트:달빛의 속삭임"
        moon_unique_for_ba = str(party_uniques_map.get("달빛술사 쿠키", "") or "")
        if (not moon_unique_for_ba) or moon_unique_for_ba.upper() == "AUTO":
            moon_unique_for_ba = get_default_party_unique("달빛술사 쿠키") or "달빛술사 쿠키의 기억"
        ba += _assumed_moonlight_buff_amp_for_party(
            equip_name=moon_equip_for_ba,
            seaz_name=moon_seaz_for_ba,
            unique_name=moon_unique_for_ba,
        )

    if "달빛술사 쿠키" in (party or []) and main_cookie_name != "달빛술사 쿠키":
        moon_equip = str(party_sets_map.get("달빛술사 쿠키", "") or "")
        if (not moon_equip) or moon_equip.upper() == "AUTO" or moon_equip == "NONE":
            moon_equip = "시간관리국의 제복"

        moon_seaz = str(party_seaz_map.get("달빛술사 쿠키", "") or "")
        if (not moon_seaz) or moon_seaz.upper() == "AUTO" or moon_seaz == "NONE":
            moon_seaz = "플럼나이트:달빛의 속삭임"

        moon_unique = str(party_uniques_map.get("달빛술사 쿠키", "") or "")
        if (not moon_unique) or moon_unique.upper() == "AUTO":
            moon_unique = get_default_party_unique("달빛술사 쿠키") or "달빛술사 쿠키의 기억"

        da += _assumed_moonlight_debuff_amp_for_party(
            equip_name=moon_equip,
            seaz_name=moon_seaz,
            unique_name=moon_unique,
        )

    if "윈드파라거스 쿠키" in (party or []) and main_cookie_name != "윈드파라거스 쿠키":
        da += _assumed_wind_debuff_amp_for_party()

    if "룽샤맛 쿠키" in (party or []) and main_cookie_name != "룽샤맛 쿠키":
        da += _assumed_lungsha_debuff_amp_for_party(main_cookie_name)

    if "마블베리맛 쿠키" in (party or []) and main_cookie_name != "마블베리맛 쿠키":
        da += _assumed_marble_debuff_amp_for_party()

    if "밀키웨이맛 쿠키" in (party or []) and main_cookie_name != "밀키웨이맛 쿠키":
        da += _assumed_milky_way_debuff_amp_for_party()

    stats["party_buff_amp_total"] = ba
    stats["party_debuff_amp_total"] = da

# =====================================================
# 최종 스탯 및 조합 계산
# =====================================================
def build_stats_for_combo(
    cookie_name_kr: str,
    base: dict,
    shards: Dict[str, int],
    potentials: Dict[str, int],
    equip_name: str,
    seaz_name: Optional[str],
    unique_name: str,
    party: List[str],
    artifact_name: str,
    party_uniques: Optional[Dict[str, str]] = None,
    party_seaz: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
) -> Dict[str, float]:

    stats: Dict[str, float] = {
        "base_atk": base["atk"],
        "friendship_atk": float(base.get("friendship_atk", friendship_atk_for(cookie_name_kr))),
        "base_elem_atk": base["elem_atk"],
        "base_atk_pct": base["atk_pct"],
        "crit_rate": base["crit_rate"],
        "crit_dmg": base["crit_dmg"],
        "armor_pen": base["armor_pen"],

        # 장비/스탯 축
        "atk_pct": 0.0,
        "equip_atk_flat": 0.0,
        "elem_atk": 0.0,
        "all_elem_dmg": 0.0,

        # 버프 축(증폭 대상)
        "buff_atk_mult": 1.0,
        "buff_atk_pct_raw": 0.0,
        "buff_crit_rate_raw": 0.0,
        "buff_crit_dmg_raw": 0.0,
        "buff_all_elem_dmg_raw": 0.0,
        "buff_armor_pen_raw": 0.0,

        # 원본 디버프·디버프 증폭 적용
        "def_reduction_raw": 0.0,
        "def_reduction_no_scale_raw": 0.0,
        "elem_res_reduction_raw": 0.0,
        "elem_res_reduction_no_scale_raw": 0.0,
        "elem_res_reduction_raw": 0.0,
        "mark_res_reduction_no_scale_raw": 0.0,

        # 기타 배율
        "final_atk_mult": 0.0,
        "dmg_bonus": 0.0,
        "final_dmg": float(base.get("final_dmg", 0.0)),

        "basic_dmg": 0.0,
        "special_dmg": 0.0,
        "ult_dmg": 0.0,
        "passive_dmg": 0.0,

        "element_strike_dmg": 0.0,
        "element_mark_explosion_dmg": 0.0,

        "buff_amp": float(base.get("buff_amp", 0.0)),
        "debuff_amp": float(base.get("debuff_amp", 0.0)),

        "boss_elem_resist": 0.4,
        "dmg_taken_inc": 0.0,
        "enemy_ult_taken_inc": 0.0,
        "enemy_basic_taken_inc": 0.0,

        "recommended_mult": 1.0,

        "unique_extra_coeff": 0.0,

        # 흑보리(품 속의 온기)
        "_bb_black_bullet_dmg_bonus_raw": 0.0,
        "_bb_next8_shot_dmg_bonus_raw": 0.0,

        # 설탕셋 옵션
        "sugar_set_enabled": 0.0,
        "sugar_set_proc_chance": 0.0,
        "sugar_set_proc_coeff": 0.0,

        # 일반 설탕유리조각 세트효과
        "sugar_brilliance_coeff": 0.0,
        "sugar_mark_crit_rate": 0.0,
        "sugar_mark_crit_dmg": 0.0,
        "sugar_glass_rows": [],

        # 승급 배율(곱연산 축)
        "promo_crit_rate_mult": 1.0,
        "promo_armor_pen_mult": 1.0,
        "promo_atk_pct_mult": 1.0,
        "promo_final_dmg_mult": 1.0,
        "promo_prima_dmg_mult": 1.0,
        "promo_base_atk_mult": 1.0,
        "promo_def_pct_mult": 1.0,
        "promo_hp_pct_mult": 1.0,

        "promo_basic_dmg_mult": 1.0,
        "promo_special_dmg_mult": 1.0,
        "promo_ult_dmg_mult": 1.0,
        "promo_passive_dmg_mult": 1.0,

        "heal_pct": 0.0,
    }

    # =====================================================
    # 승급 효과
    # - 공통 스탯(치확/공격력%/최종 피해 등)은 기존처럼 전용 축에 기록
    # - 기본·특수·궁극기 피해 증가 일반 옵션
    # 다른 동일 스탯과 합연산되도록 해당 스탯 축에 직접 더
    # =====================================================
    if cookie_name_kr == "멜랑크림 쿠키" and MELAN_PROMO_ENABLED:
        stats["promo_crit_rate_mult"] *= MELAN_PROMO_CRIT_RATE_MULT
        stats["promo_armor_pen_mult"] *= MELAN_PROMO_ARMOR_PEN_MULT
        stats["promo_atk_pct_mult"]   *= MELAN_PROMO_ATK_PCT_MULT
        stats["promo_final_dmg_mult"] *= MELAN_PROMO_FINAL_DMG_MULT
        stats["promo_prima_dmg_mult"] *= MELAN_PROMO_PRIMA_DMG_MULT
        stats["_melan_promo"] = 1.0

    if cookie_name_kr == "윈드파라거스 쿠키" and WIND_PROMO_ENABLED:
        stats["promo_crit_rate_mult"] *= WIND_PROMO_CRIT_RATE_MULT
        stats["promo_atk_pct_mult"]   *= WIND_PROMO_ATK_PCT_MULT
        stats["promo_final_dmg_mult"] *= WIND_PROMO_FINAL_DMG_MULT
        stats["promo_def_pct_mult"]   *= WIND_PROMO_DEF_PCT_MULT
        stats["promo_hp_pct_mult"]    *= WIND_PROMO_HP_PCT_MULT
        stats["_wind_promo"] = 1.0

    if cookie_name_kr == "흑보리맛 쿠키" and BLACK_BARLEY_PROMO_ENABLED:
        stats["promo_crit_rate_mult"]      *= BLACK_BARLEY_PROMO_CRIT_RATE_MULT
        stats["promo_base_atk_mult"]       *= BLACK_BARLEY_PROMO_BASE_ATK_MULT
        stats["promo_def_pct_mult"]        *= BLACK_BARLEY_PROMO_DEF_PCT_MULT
        stats["promo_hp_pct_mult"]         *= BLACK_BARLEY_PROMO_HP_PCT_MULT
        stats["basic_dmg"]                 += BLACK_BARLEY_PROMO_BASIC_DMG_ADD
        stats["special_dmg"]               += BLACK_BARLEY_PROMO_SPECIAL_DMG_ADD
        stats["ult_dmg"]                   += BLACK_BARLEY_PROMO_ULT_DMG_ADD
        stats["_bb_promo"] = 1.0

    if cookie_name_kr == "샤이닝베리맛 쿠키" and SHINING_BERRY_PROMO_ENABLED:
        stats["promo_crit_rate_mult"] *= SHINING_BERRY_PROMO_CRIT_RATE_MULT
        stats["special_dmg"]          += SHINING_BERRY_PROMO_SPECIAL_DMG_ADD
        stats["ult_dmg"]              += SHINING_BERRY_PROMO_ULT_DMG_ADD
        stats["_shining_promo"] = 1.0

    if cookie_name_kr == "피닉스페퍼 쿠키" and PHOENIX_PEPPER_PROMO_ENABLED:
        stats["promo_ult_dmg_mult"]     *= PHOENIX_PEPPER_PROMO_ULT_DMG_MULT
        stats["promo_passive_dmg_mult"] *= PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT
        stats["_phoenix_promo"] = 1.0

    # =====================================================
    # 장비(세트/부위/세트효과)
    # =====================================================
    equip = EQUIP_SETS[equip_name]
    for part in ["head", "top", "bottom"]:
        add(stats, equip[part]["base"])
        add(stats, equip[part]["unique"])

    # 장비 세트 방어력·속성 내성 감소 디버프 증폭 제외
    # 디버프 증폭 제외 축 반영
    # 예: 전설의 유령해적 방어력 감소, 유성우의 향연 속성 내성 감소
    set_base = dict((equip.get("set_effect", {}) or {}).get("base", {}) or {})
    equip_def_red = float(set_base.pop("def_reduction_raw", 0.0) or 0.0)
    equip_elem_res = float(set_base.pop("elem_res_reduction_raw", 0.0) or 0.0)
    add(stats, set_base)
    if equip_def_red:
        stats["def_reduction_no_scale_raw"] = float(stats.get("def_reduction_no_scale_raw", 0.0)) + equip_def_red
        stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + equip_def_red
    if equip_elem_res:
        stats["elem_res_reduction_no_scale_raw"] = float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + equip_elem_res

    # 유성우 평균 속성 내성 감소 5%
    # 달빛술사 유성우 속성 내성 감소 10%
    # 장비 효과 디버프 증폭 제외
    if equip_name == "유성우의 향연" and cookie_name_kr == "달빛술사 쿠키":
        base_meteor_res = equip_elem_res
        moonlight_meteor_res = 0.10
        if moonlight_meteor_res > base_meteor_res:
            stats["elem_res_reduction_no_scale_raw"] = float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + (moonlight_meteor_res - base_meteor_res)

    stats["_main_equip_set_name"] = equip_name

    if equip_name == "달콤한 설탕 깃털":
        stats["sugar_set_enabled"] = 1.0
        stats["sugar_set_proc_chance"] = SUGAR_SET_PROC_CHANCE
        stats["sugar_set_proc_coeff"] = SUGAR_SET_PROC_ATK_COEFF

    # =====================================================
    # 시즈나이트
    # =====================================================
    if seaz_name:
        seaz = SEAZNITES.get(seaz_name)
        if seaz:
            # 보조 옵션 합산
            add(stats, seaz.get("sub", {}))

            # 시즈 패시브 중복 적용 방지
            passive = seaz.get("passive", {}) or {}

            # 시즈 패시브 미처리 항목 보완
            if "final_dmg" in passive:
                stats["final_dmg"] += float(passive["final_dmg"])

            for k in ["basic_dmg", "special_dmg", "ult_dmg", "passive_dmg"]:
                if k in passive:
                    add_stat(stats, k, float(passive[k]))

            if "final_dmg_stack" in passive and "max_stacks" in passive:
                stats["final_dmg"] += float(passive["final_dmg_stack"]) * float(passive["max_stacks"])

    # =====================================================
    # 설유(일반 41칸)
    # =====================================================
    for k, slots in shards.items():
        if k in SHARD_INC:
            add_stat(stats, k, slots * SHARD_INC[k])

    # =====================================================
    # 잠재(8칸)
    # =====================================================
    stats["atk_pct"]   += potentials.get("atk_pct", 0) * POTENTIAL_INC["atk_pct"]
    stats["crit_rate"] += potentials.get("crit_rate", 0) * POTENTIAL_INC["crit_rate"]
    stats["crit_dmg"]  += potentials.get("crit_dmg", 0) * POTENTIAL_INC["crit_dmg"]
    stats["armor_pen"] += potentials.get("armor_pen", 0) * POTENTIAL_INC["armor_pen"]
    stats["elem_atk"]  += potentials.get("elem_atk", 0) * POTENTIAL_INC["elem_atk"]
    stats["equip_atk_flat"] += potentials.get("atk_flat", 0) * POTENTIAL_INC["atk_flat"]

    stats["buff_amp"]   += potentials.get("buff_amp", 0) * POTENTIAL_INC["buff_amp"]
    stats["debuff_amp"] += potentials.get("debuff_amp", 0) * POTENTIAL_INC["debuff_amp"]

    # =====================================================
    # 부위+전용무기 속성 잠재 통일 보너스
    # - 모자/상의/하의/전용무기 잠재가 "같은 속성"이면:
    # 모든 속성 피해 +30%, 속성 공격력 +20
    # =====================================================
    if globals().get("ELEMENT_POTENTIAL_SYNERGY_ENABLED", False):
        stats["all_elem_dmg"] = float(stats.get("all_elem_dmg", 0.0)) + float(globals().get("ELEMENT_POTENTIAL_SYNERGY_ALL_ELEM_DMG", 0.30))
        stats["elem_atk"]     = float(stats.get("elem_atk", 0.0))     + float(globals().get("ELEMENT_POTENTIAL_SYNERGY_ELEM_ATK", 20.0))

    # =====================================================
    # 아티팩트 / 유니크 / 파티 버프 / 잎새의 활강
    # =====================================================
    apply_artifact(stats, artifact_name)
    apply_unique(stats, cookie_name_kr, unique_name)

    stats["party_seaz"] = dict(party_seaz or {})
    stats["party_sets"] = dict(party_sets or {})
    stats["party_uniques"] = dict(party_uniques or {})

    stats["buff_amp_total"] = float(stats.get("buff_amp", 0.0))
    stats["debuff_amp_total"] = float(stats.get("debuff_amp", 0.0))
    # 본인 전용 증폭량 스냅샷: 파티 증가량과 분리
    stats["self_buff_amp_total"] = float(stats.get("buff_amp_total", 0.0))
    stats["self_debuff_amp_total"] = float(stats.get("debuff_amp_total", 0.0))

    _apply_party_amp_totals(stats, party, cookie_name_kr)
    _apply_neon_main_effects(stats, cookie_name_kr)
    apply_party_buffs(
        stats,
        party,
        cookie_name_kr,
        party_uniques=party_uniques,
    )

    # 마블베리 파티 효과 보정
    # 표시용 파티 버프 누락 보정
    # 최종 스탯 단계 보장
    # - 에너지 맥스: 속성강타 피해 +25%
    # - 버프·디버프 증폭 제외
    # - 마커로 중복 적용 방지
    if ("마블베리맛 쿠키" in (party or [])) and (cookie_name_kr != "마블베리맛 쿠키"):
        if not stats.get("_marble_energy_max_strike_applied", False):
            stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + 0.25
            stats["_marble_energy_max_strike_applied"] = True

    # 일반 설탕유리조각 세트효과
    # - 메인 역할에 맞는 세트 1개 + 실제 파티 구성에 포함된 쿠키 세트만 반영
    # - 딜러 메인: 딜러 본인 + 서포터 1 + 스트라이커 1
    # - 스트라이커 메인: 스트라이커 본인 + 서포터 1
    # - 서포터 메인: 서포터 본인 + 스트라이커 1
    apply_sugar_glass_set_effects(stats, cookie_name_kr, party)

    if seaz_name:
        apply_seaz_passive(
            stats, seaz_name,
            owner_cookie_name=cookie_name_kr,
            main_cookie_name=cookie_name_kr
        )

    apply_leaf_glide(stats, party, cookie_name_kr)

    # 마블베리 에너지 맥스 25% 파티 버프 반영
    # 마블베리 에너지 맥스 1회 적용 마커
    # 마블베리 중복 보정 제거

    return stats

def is_valid_by_caps(stats: Dict[str, float]) -> bool:
    promo_ap_mult = float(stats.get("promo_armor_pen_mult", 1.0))

    eff_ap = stats["armor_pen"] * promo_ap_mult

    if eff_ap > 0.80 + 1e-12:
        return False
    return True

# =====================================================
# 어비스 레이드 쿠키 시뮬레이터 치명타 100% 최적화
# =====================================================
# 0) 공용 유틸
# =====================================================

# =====================================================
# 최적화 루프 보조 함수
# =====================================================
def _clone_stats_for_loop(st: Dict[str, float]) -> Dict[str, float]:
    """최적화 루프 스탯 복사"""
    s = dict(st)
    if "_applied_party_buffs" in s:
        s["_applied_party_buffs"] = set(s["_applied_party_buffs"])
    if "_applied_enemy_debuffs" in s:
        s["_applied_enemy_debuffs"] = set(s["_applied_enemy_debuffs"])
    return s

def _apply_shards_inplace(stats: Dict[str, float], shards: Dict[str, int]) -> None:
    """설탕유리조각 스탯 적용"""
    for k, slots in shards.items():
        inc = float(SHARD_INC.get(k, 0.0))
        if inc and slots:
            stats[k] = float(stats.get(k, 0.0)) + inc * int(slots)

DAMAGE_SHARD_OPT_KEYS: Tuple[str, ...] = (
    "atk_pct",
    "elem_atk",
    "crit_dmg",
    "all_elem_dmg",
    "basic_dmg",
    "special_dmg",
    "ult_dmg",
    "passive_dmg",
)

def _damage_stats_with_shards(
    template: Dict[str, float],
    shards: Dict[str, int],
) -> Dict[str, float]:
    """설탕유리조각 적용 스탯"""
    stats = _clone_stats_for_loop(template)
    _apply_shards_inplace(stats, shards)
    stats.pop("_damage_context_cache", None)
    return stats

def optimize_damage_shards_for_fixed_combo(
    template: Dict[str, float],
    cycle_fn: Callable[[Dict[str, float]], Dict[str, float]],
    *,
    required_crit_slots: int = 0,
    damage_keys: Tuple[str, ...] = DAMAGE_SHARD_OPT_KEYS,
    max_refine_iterations: int = 100,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """고정 조합 설탕유리조각 1차 최적화"""
    required_crit_slots = int(required_crit_slots)
    if required_crit_slots < 0 or required_crit_slots > NORMAL_SLOTS:
        raise ValueError("required_crit_slots는 0~41 범위여야 합니다.")

    active_keys = tuple(
        key for key in damage_keys
        if key in SHARD_INC and key != "crit_rate" and float(SHARD_INC.get(key, 0.0)) != 0.0
    )
    if not active_keys:
        raise ValueError("조각 최적화에 사용할 공격 옵션이 없습니다.")

    current = {key: 0 for key in SHARD_INC.keys()}
    current["crit_rate"] = required_crit_slots
    current_stats = _damage_stats_with_shards(template, current)
    current_cycle = cycle_fn(current_stats)

    remaining = NORMAL_SLOTS - required_crit_slots
    for _ in range(remaining):
        best_key: Optional[str] = None
        best_stats = current_stats
        best_cycle = current_cycle

        for key in active_keys:
            trial = dict(current)
            trial[key] = int(trial.get(key, 0)) + 1
            trial_stats = _damage_stats_with_shards(template, trial)
            trial_cycle = cycle_fn(trial_stats)
            if best_key is None or float(trial_cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
                best_key = key
                best_stats = trial_stats
                best_cycle = trial_cycle

        if best_key is None:
            break
        current[best_key] = int(current.get(best_key, 0)) + 1
        current_stats = best_stats
        current_cycle = best_cycle

    iterations = 0
    while iterations < max(0, int(max_refine_iterations)):
        iterations += 1
        best_move: Optional[Dict[str, int]] = None
        best_stats = current_stats
        best_cycle = current_cycle

        for src in active_keys:
            if int(current.get(src, 0)) <= 0:
                continue
            for dst in active_keys:
                if src == dst:
                    continue
                trial = dict(current)
                trial[src] -= 1
                trial[dst] = int(trial.get(dst, 0)) + 1
                trial_stats = _damage_stats_with_shards(template, trial)
                trial_cycle = cycle_fn(trial_stats)
                if float(trial_cycle["dps"]) > float(best_cycle["dps"]) + 1e-9:
                    best_move = trial
                    best_stats = trial_stats
                    best_cycle = trial_cycle

        if best_move is None:
            break
        current = best_move
        current_stats = best_stats
        current_cycle = best_cycle

    for key in SHARD_INC.keys():
        current.setdefault(key, 0)
    return current, current_stats, current_cycle

DAMAGE_SHARD_TOP_STAT_COUNT = 4
DAMAGE_SHARD_FINALISTS_PER_EQUIP = 3

def _select_top_damage_shard_keys(
    template: Dict[str, float],
    cycle_fn: Callable[[Dict[str, float]], Dict[str, float]],
    *,
    required_crit_slots: int = 0,
    damage_keys: Tuple[str, ...] = DAMAGE_SHARD_OPT_KEYS,
    key_count: int = DAMAGE_SHARD_TOP_STAT_COUNT,
) -> Tuple[str, ...]:
    """설탕유리조각 공격 옵션 선정"""
    active_keys = tuple(
        key for key in damage_keys
        if key in SHARD_INC and key != "crit_rate" and float(SHARD_INC.get(key, 0.0)) != 0.0
    )
    if not active_keys:
        return tuple()

    base_shards = {key: 0 for key in SHARD_INC.keys()}
    base_shards["crit_rate"] = int(required_crit_slots)
    base_stats = _damage_stats_with_shards(template, base_shards)
    base_cycle = cycle_fn(base_stats)
    base_dps = float(base_cycle.get("dps", 0.0))

    scored = []
    for order, key in enumerate(active_keys):
        trial = dict(base_shards)
        trial[key] = 1
        trial_stats = _damage_stats_with_shards(template, trial)
        trial_cycle = cycle_fn(trial_stats)
        gain = float(trial_cycle.get("dps", 0.0)) - base_dps
        scored.append((gain, -order, key))

    scored.sort(reverse=True)
    count = min(len(scored), max(1, int(key_count)))
    return tuple(item[2] for item in scored[:count])

def _iter_exact_shard_allocations(
    total_slots: int,
    shard_keys: Tuple[str, ...],
) -> Iterator[Dict[str, int]]:
    """설탕유리조각 전수 배분"""
    keys = tuple(shard_keys)
    if not keys:
        return

    def rec(index: int, remaining: int, current: Dict[str, int]) -> Iterator[Dict[str, int]]:
        if index >= len(keys) - 1:
            out = dict(current)
            out[keys[-1]] = int(remaining)
            yield out
            return

        key = keys[index]
        for slots in range(remaining + 1):
            current[key] = int(slots)
            yield from rec(index + 1, remaining - slots, current)
        current.pop(key, None)

    yield from rec(0, max(0, int(total_slots)), {})

def optimize_damage_shards_top4_for_fixed_combo(
    template: Dict[str, float],
    cycle_fn: Callable[[Dict[str, float]], Dict[str, float]],
    *,
    required_crit_slots: int = 0,
    damage_keys: Tuple[str, ...] = DAMAGE_SHARD_OPT_KEYS,
    top_key_count: int = DAMAGE_SHARD_TOP_STAT_COUNT,
    max_refine_iterations: int = 100,
) -> Tuple[Dict[str, int], Dict[str, float], Dict[str, float]]:
    """설탕유리조각 상위 옵션 정밀 최적화"""
    required_crit_slots = int(required_crit_slots)
    if required_crit_slots < 0 or required_crit_slots > NORMAL_SLOTS:
        raise ValueError("required_crit_slots는 0~41 범위여야 합니다.")

    active_keys = tuple(
        key for key in damage_keys
        if key in SHARD_INC and key != "crit_rate" and float(SHARD_INC.get(key, 0.0)) != 0.0
    )
    if not active_keys:
        raise ValueError("조각 최적화에 사용할 공격 옵션이 없습니다.")

    top_keys = _select_top_damage_shard_keys(
        template,
        cycle_fn,
        required_crit_slots=required_crit_slots,
        damage_keys=active_keys,
        key_count=top_key_count,
    )
    if not top_keys:
        raise ValueError("전수조사에 사용할 공격 옵션을 선택하지 못했습니다.")

    remaining = NORMAL_SLOTS - required_crit_slots
    best_shards: Optional[Dict[str, int]] = None
    best_stats: Optional[Dict[str, float]] = None
    best_cycle: Optional[Dict[str, float]] = None

    for allocation in _iter_exact_shard_allocations(remaining, top_keys):
        shards = {key: 0 for key in SHARD_INC.keys()}
        shards["crit_rate"] = required_crit_slots
        for key, value in allocation.items():
            shards[key] = int(value)
        stats = _damage_stats_with_shards(template, shards)
        cycle = cycle_fn(stats)
        if best_cycle is None or float(cycle.get("dps", 0.0)) > float(best_cycle.get("dps", 0.0)) + 1e-9:
            best_shards = shards
            best_stats = stats
            best_cycle = cycle

    if best_shards is None or best_stats is None or best_cycle is None:
        raise RuntimeError("조각 전수조사 결과를 생성하지 못했습니다.")

    current = best_shards
    current_stats = best_stats
    current_cycle = best_cycle
    iterations = 0
    while iterations < max(0, int(max_refine_iterations)):
        iterations += 1
        best_move: Optional[Dict[str, int]] = None
        move_stats = current_stats
        move_cycle = current_cycle

        for src in active_keys:
            if int(current.get(src, 0)) <= 0:
                continue
            for dst in active_keys:
                if src == dst:
                    continue
                trial = dict(current)
                trial[src] -= 1
                trial[dst] = int(trial.get(dst, 0)) + 1
                trial_stats = _damage_stats_with_shards(template, trial)
                trial_cycle = cycle_fn(trial_stats)
                if float(trial_cycle.get("dps", 0.0)) > float(move_cycle.get("dps", 0.0)) + 1e-9:
                    best_move = trial
                    move_stats = trial_stats
                    move_cycle = trial_cycle

        if best_move is None:
            break
        current = best_move
        current_stats = move_stats
        current_cycle = move_cycle

    for key in SHARD_INC.keys():
        current.setdefault(key, 0)
    return current, current_stats, current_cycle

def _resolve_equip_list_override(
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]],
    default_equips: List[str],
) -> List[str]:
    """장비 후보 강제 지정"""
    base = list(default_equips) if default_equips else []

    if equip_override is None:
        return base

    if isinstance(equip_override, (list, tuple, set)):
        cand = [str(x).strip() for x in equip_override if str(x).strip()]
    else:
        s = str(equip_override).strip()
        if (not s) or (s.upper() in ("AUTO", "NONE")):
            return base
        cand = [x.strip() for x in s.split(",")] if "," in s else [s]

    cand = [x for x in cand if x in EQUIP_SETS]
    return cand if cand else base

def _resolve_unique_list_override(
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]],
    default_uniques: List[str],
) -> List[str]:
    """유니크 조각 후보 강제 지정"""
    base = list(default_uniques) if default_uniques else []

    if unique_override is None:
        return base

    if isinstance(unique_override, (list, tuple, set)):
        cand = [str(x).strip() for x in unique_override if str(x).strip()]
    else:
        s = str(unique_override).strip()
        if (not s) or (s.upper() in ("AUTO", "NONE")):
            return base
        cand = [x.strip() for x in s.split(",")] if "," in s else [s]

    cand = [x for x in cand if x in UNIQUE_SHARDS]
    return cand if cand else base

def _effective_crit_rate_with_promo(stats: Dict[str, float]) -> float:
    """승급 포함 실제 치명타 확률"""
    promo = float(stats.get("promo_crit_rate_mult", 1.0))
    base_crit = float(stats.get("crit_rate", 0.0))
    buff_crit = float(stats.get("buff_crit_rate_raw", 0.0))
    return base_crit * promo + buff_crit

def _min_crit_slots_needed_for_crit100_generic(template: Dict[str, float]) -> Optional[int]:
    """치명타 확률 100% 최소 조각 수"""
    promo = float(template.get("promo_crit_rate_mult", 1.0))
    per_slot = float(SHARD_INC.get("crit_rate", 0.0)) * promo
    cur = _effective_crit_rate_with_promo(template)

    if cur >= (1.0 - EPS_CR):
        return 0
    if per_slot <= 0:
        return None
    if not is_valid_by_caps(template):
        return None

    need = int(math.ceil(((1.0 - EPS_CR) - cur) / per_slot))
    if need < 0:
        need = 0
    if need > NORMAL_SLOTS:
        return None
    return need

def generate_damage_potential_candidates(
    *,
    fixed: Optional[Dict[str, int]] = None,
    total_slots: int = 8,
    armor_pen_cap: int = 4,
    free_keys: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, int]]:
    """딜 잠재력 후보 생성"""
    fixed_stats = {
        "debuff_amp": 0,
        "crit_rate": 0,
        "atk_pct": 0,
        "elem_atk": 0,
        "crit_dmg": 0,
        "armor_pen": 0,
        "buff_amp": 0,
    }
    if fixed:
        for key, value in fixed.items():
            fixed_stats[key] = int(value)

    # 잠재력 장착 개수 제한: 고정값 단계 검증
    fixed_caps = {
        "elem_atk": 2,
        "buff_amp": 4,
        "debuff_amp": 4,
        "armor_pen": int(armor_pen_cap),
    }
    for key, cap in fixed_caps.items():
        if int(fixed_stats.get(key, 0)) > int(cap):
            return []

    fixed_used = sum(int(value) for value in fixed_stats.values())
    remain = int(total_slots) - fixed_used
    if remain < 0:
        return []

    keys = tuple(free_keys or ("crit_rate", "atk_pct", "crit_dmg", "armor_pen"))
    allowed_free_keys = {"crit_rate", "atk_pct", "elem_atk", "crit_dmg", "armor_pen", "debuff_amp"}
    keys = tuple(key for key in keys if key in allowed_free_keys)
    if not keys:
        return [dict(fixed_stats)] if remain == 0 else []

    out: List[Dict[str, int]] = []

    def dfs(index: int, slots_left: int, current: Dict[str, int]) -> None:
        if index >= len(keys):
            if slots_left == 0:
                candidate = dict(fixed_stats)
                for key, value in current.items():
                    candidate[key] = int(candidate.get(key, 0)) + int(value)
                out.append(candidate)
            return

        key = keys[index]
        fixed_value = int(fixed_stats.get(key, 0))
        if key == "armor_pen":
            limit = min(slots_left, max(0, int(armor_pen_cap) - fixed_value))
        elif key == "elem_atk":
            limit = min(slots_left, max(0, 2 - fixed_value))
        elif key in {"buff_amp", "debuff_amp"}:
            limit = min(slots_left, max(0, 4 - fixed_value))
        else:
            limit = slots_left
        for value in range(limit + 1):
            current[key] = value
            dfs(index + 1, slots_left - value, current)
        current.pop(key, None)

    dfs(0, remain, {})
    return out

def should_evaluate_conditional_crit_potential(
    template: Dict[str, float],
    potential: Dict[str, int],
    *,
    legacy_crit_slots: Optional[int] = None,
    eps: float = 1e-12,
) -> bool:
    """조건부 치명타 잠재력 비교 여부"""
    del potential, legacy_crit_slots, eps
    return _min_crit_slots_needed_for_crit100_generic(template) is not None
