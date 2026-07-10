# =====================================================
# Imports
# =====================================================
from typing import Any, Dict, List, Tuple, Optional, Callable, Union
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

# -----------------
# 0.0) 업타임 모드
# -----------------
# =====================================================
# Constants
# =====================================================
MODE_ALWAYS  = "ALWAYS"    # 항상 켜짐(업타임 1.0)
MODE_AVERAGE = "AVERAGE"   # duration/cooldown 평균 업타임
MODE_TRIGGER = "TRIGGER"   # 기대 업타임을 직접 넣거나, proc_interval로 근사
MODE_CUSTOM  = "CUSTOM"    # 사용자가 value로 고정

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


# -----------------------------
# 0.1) 전역 플래그/기본 가정 상수
# -----------------------------

BOSS_MARK_ELEMENT_RESIST_DEFAULT = 0.40


# -----------------------------
# 0.1-b) 쿠키별 승급 상수 (공통 빌더에서 직접 참조)
# - 분리 전 cookie_simulator.py에서는 한 파일 안에 같이 있었지만,
# 분리 후 common.py에서도 이 값이 필요하므로 공통부에 복제 보관
# -----------------------------
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
BLACK_BARLEY_PROMO_SPECIAL_DMG_MULT  = 1.20
BLACK_BARLEY_PROMO_ULT_DMG_MULT      = 1.20
BLACK_BARLEY_PROMO_BASIC_DMG_MULT    = 1.30

SHINING_BERRY_PROMO_ENABLED = True
SHINING_BERRY_PROMO_CRIT_RATE_MULT   = 1.0
SHINING_BERRY_PROMO_SPECIAL_DMG_MULT = 1.20
SHINING_BERRY_PROMO_ULT_DMG_MULT     = 1.20

PHOENIX_PEPPER_PROMO_ENABLED = True
PHOENIX_PEPPER_PROMO_ULT_DMG_MULT = 1.45
PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT = 1.80


# -----------------------------
# 0.2) 설탕셋(달콤한 설탕 깃털) 발동형 옵션
# -----------------------------
SUGAR_SET_PROC_CHANCE = 0.20
SUGAR_SET_PROC_ATK_COEFF = 0.50

# -----------------------------
# 0.3) 아르곤 유니크 파라미터
# -----------------------------

# -----------------------------
# 0.4) 전투/공식 파라미터
# -----------------------------
DEFENSE_K = 3.0
DEF_REDUCTION_CAP = 0.70  # 방어력 감소 상한 70%

# ---- 속성강타(표식) 모델
# - 정식식:
#   표식에 들어간 총 데미지
#   × 기본 속성강타 계수
#   × 표식 속성 내성 배율
#   × (1 + 속성강타 피해 증가)
# - 표식 속성 내성 배율 = 1 - (보스 기본 속성 내성 - 속성 내성 감소)
# - 0.566 간이계수는 내성 배율까지 합쳐진 값이라, 속성내성감소가 변하는 세팅에는 사용하지 않음
ELEMENT_STRIKE_BASE_COEFF = 0.712


# =====================================================
# 1) 공통: 설탕유리조각(41칸) / 잠재력(8칸)
# =====================================================
ELEMENT_POTENTIAL_SYNERGY_ENABLED = True
ELEMENT_POTENTIAL_SYNERGY_ALL_ELEM_DMG = 0.30  # +30%
ELEMENT_POTENTIAL_SYNERGY_ELEM_ATK = 20.0      # +20

# 설탕유리조각/잠재력/호감도 공격력 데이터는 cookie/stat_data.py에서 관리한다.

# =====================================================
# 2) 공통: 유틸 함수(기본/누적/업타임/복사)
# =====================================================

# =====================================================
# Helpers - 공통 보조 함수
# =====================================================
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def get_uptime(key: str) -> float:
    """UPTIME_CONFIG 기반 업타임 계산(0~1)"""
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
    """dict bonus -> stats 누적"""
    for k, v in (bonus or {}).items():
        add_stat(stats, k, float(v))

EPS_CR = 1e-12

def effective_crit_rate_raw(stats: Dict[str, float]) -> float:
    """클램프 전값 '실전 치확' = (crit_rate) + (버프치확)"""
    return float(stats.get("crit_rate", 0.0)) + float(stats.get("buff_crit_rate_raw", 0.0))

# =====================================================
# 3) 공통 데이터(쿠키/속성/직업/형태/쿨/타수)
# =====================================================


# 쿠키 속성/타입/역할 분류는 cookie/catalog.py에서 관리한다.

# =====================================================
# 4) 잎새의 활강(Leaf Glide)
# =====================================================

LEAF_GLIDE_RES_RED_PER_STACK = 0.0056   # 0.56%
LEAF_GLIDE_BASE_MAX_STACKS   = 40
WIND_PROMO_LEAF_GLIDE_MAX_STACK_ADD = 10

LEAF_GLIDE_FINALDMG_PER_DEBUFFAMP = 1.25
LEAF_GLIDE_FINALDMG_CAP = 1.0

# =====================================================
# Calculation - 효과 반영/버프 적용
# =====================================================
def apply_leaf_glide(stats: Dict[str, float], party: List[str], main_cookie_name: str):
    has_wind_in_team = ("윈드파라거스 쿠키" in (party or [])) or (main_cookie_name == "윈드파라거스 쿠키")
    if not has_wind_in_team:
        return stats

    applied = stats.setdefault("_applied_enemy_debuffs", set())
    if "LEAF_GLIDE" in applied:
        return stats

    # 1) [공유] 적 속성내성 감소 (윈파가 팀에 있으면 적에게 걸리는 디버프로 취급)
    # - 윈파 본인이 메인일 때: 일반 raw 축에 넣어서 윈파 본인 디버프 증폭으로 계산한다.
    # - 윈파가 파티원일 때: 메인 쿠키의 디버프 증폭을 타면 안 되므로,
    #   apply_party_buffs()에서 계산해 둔 "윈파 개인 디버프 증폭"으로 미리 증폭한 뒤 no_scale 축에 넣는다.
    max_stacks = LEAF_GLIDE_BASE_MAX_STACKS + (WIND_PROMO_LEAF_GLIDE_MAX_STACK_ADD if WIND_PROMO_ENABLED else 0)
    stacks = max_stacks
    base_res_red = LEAF_GLIDE_RES_RED_PER_STACK * stacks
    if main_cookie_name == "윈드파라거스 쿠키":
        stats["elem_res_reduction_raw"] = float(stats.get("elem_res_reduction_raw", 0.0)) + base_res_red
    else:
        wind_da = stats.get("_wind_leaf_glide_owner_debuff_amp", None)
        if wind_da is None:
            # apply_party_buffs()를 거치지 않는 안전 경로용 기본값:
            # 고정 잠재 4디벞(40%) + 이어지는 마음(25%) + 기본 황금 예복 세트(15%) = 80%
            wind_da = _assumed_wind_debuff_amp_for_party() + 0.15
        stats["elem_res_reduction_no_scale_raw"] = (
            float(stats.get("elem_res_reduction_no_scale_raw", 0.0))
            + base_res_red * (1.0 + float(wind_da))
        )

    # 2) [본인] 최종피해 증가는 "윈파가 잎새의 활강 상태로 공격할 때" → 윈파 자신에게만
    if main_cookie_name == "윈드파라거스 쿠키":
        # [본인 전용] 창공을 가르는 자유의 최종피해 증가는
        # 파티 총 디버프 증폭이 아니라 윈드파라거스 본인의 디버프 증폭 스냅샷만 사용한다.
        # apply_party_buffs() 이후 stats["debuff_amp"]에는 파티 장비/유니크 증폭이 합산될 수 있으므로
        # 반드시 파티 합산 전 저장해 둔 self_debuff_amp_total을 우선 사용한다.
        da = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))
        add_final = min(LEAF_GLIDE_FINALDMG_CAP, LEAF_GLIDE_FINALDMG_PER_DEBUFFAMP * da)
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + add_final

    applied.add("LEAF_GLIDE")
    return stats

# =====================================================
# 5) 공통: 장비 세트
# =====================================================
# 장비 세트 데이터는 cookie/equipment_data.py에서 관리한다.

# =====================================================
# 6) 공통: 시즈나이트
# =====================================================

# 시즈나이트 데이터는 cookie/seaz_data.py에서 관리한다.

# =====================================================
# 6.5) 시즈 패시브(heal_pct / ally_all_elem_dmg) 반영 유틸
# - heal_pct -> stats["heal_pct"]
# - ally_all_elem_dmg -> stats["buff_all_elem_dmg_raw"] (버프증폭/업타임 반영)
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
    # 메인 패시브를 적용하지 않고 sub 스탯만 사용
    if owner_cookie_name == "이슬맛 쿠키" and isinstance(seaz_name, str):
        if seaz_name.endswith(":작은 성배") or seaz_name.endswith(":가벼운 손길"):
            return stats

    passive = info.get("passive", {}) or {}

    key = f"{uptime_key_prefix}{seaz_name}"
    u = get_uptime(key)

    # heal_pct : 벞증 영향 없음
    if "heal_pct" in passive:
        stats["heal_pct"] = float(stats.get("heal_pct", 0.0)) + float(passive["heal_pct"]) * u

    # ally_all_elem_dmg : 벞증 영향 없음
    if "ally_all_elem_dmg" in passive:
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(passive["ally_all_elem_dmg"]) * u

    # armor_pen : 벞증 영향 없음
    if "armor_pen" in passive:
        stats["buff_armor_pen_raw"] = float(stats.get("buff_armor_pen_raw", 0.0)) + float(passive["armor_pen"]) * u

    # atk_pct는 기본적으로 최종공격력 축으로 넣고, 샬롯/이슬 자기 시즈만 일반 공퍼 축으로 넣는다.
    if "atk_pct" in passive:
        addv = float(passive["atk_pct"]) * u

        is_owner_main = (owner_cookie_name is not None) and (main_cookie_name is not None) and (owner_cookie_name == main_cookie_name)
        is_support_main = (main_cookie_name in ("샬롯맛 쿠키", "이슬맛 쿠키", "달빛술사 쿠키"))

        if is_owner_main and is_support_main:
            # 서폿이 메인일 때 자기 시즈 공퍼는 "공격력%" 축으로
            stats["atk_pct"] = float(stats.get("atk_pct", 0.0)) + addv
        else:
            # 그 외 시즈 공격력 증가는 최종공격력 축으로 반영한다.
            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + addv
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + addv

    # element_strike_dmg : 벞증 영향 없음, 파티 공유
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
    # - 공격력 증가 축(final_atk_mult)으로 반영
    if "ally_final_atk_mult" in passive:
        addv = float(passive["ally_final_atk_mult"]) * u
        # 달빛술사 + 달빛의 속삭임은 12%가 최대 3중첩이며,
        # 사이클 내내 최대중첩이 유지되는 것으로 계산한다. (12% × 3 = 36%)
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
    # - 달빛의 속삭임: 버프증폭량 + 디버프증폭량의 100%만큼 모든 속성 피해 증가
    # - 최대 100%
    # - 본인만 적용, 파티원 장착 시 메인에게 공유하지 않음
    is_owner_main = (owner_cookie_name is not None) and (main_cookie_name is not None) and (owner_cookie_name == main_cookie_name)
    if is_owner_main and "self_amp_to_all_elem_cap" in passive:
        cap = float(passive.get("self_amp_to_all_elem_cap", 1.0))
        # 본인 전용: 파티원의 버프/디버프 증폭량은 제외하고, 장착자 본인의 증폭량만 사용한다.
        ba = float(stats.get("self_buff_amp_total", stats.get("buff_amp_total", stats.get("buff_amp", 0.0))))
        da = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))
        addv = min(cap, max(0.0, ba + da)) * u
        stats["all_elem_dmg"] = float(stats.get("all_elem_dmg", 0.0)) + addv

    return stats

# =====================================================
# 7) 공통: 아티팩트
# =====================================================

# 아티팩트 데이터는 cookie/artifact_data.py에서 관리한다.

def apply_artifact(stats: Dict[str, float], artifact_name: str) -> None:
    a = ARTIFACTS.get(artifact_name, ARTIFACTS["NONE"])

    # 1) 기본옵션 / 고유스탯(증폭 X)
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

    # 최종공/피해증가/최종피해는 버프증폭 적용 대상 아님(그리고 보통 self)
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

# 유니크 설탕유리조각 데이터는 cookie/unique_data.py에서 관리한다.

# =====================================================
# is_unique_allowed
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
# apply_unique
# - is_owner=True : 장착자 본인 적용
# - is_owner=False : 파티원 유니크를 "공유 stats"에 합산 (본인전용 기본옵션/효과는 제외)
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
    # - 체리맛 쿠키의 기억: 공격력 +15%, 버프증폭 +36%는 파티 버프 계산에 반영
    ba_add = float(u.get("buff_amp_add", 0.0))
    if ba_add:
        stats["buff_amp"] = float(stats.get("buff_amp", 0.0)) + ba_add
        stats["party_buff_amp_total"] = float(stats.get("party_buff_amp_total", 0.0)) + ba_add

    # (3) 디버프증폭 기본옵션: 파티 전체 (party_total 동기화)
    da_add = float(u.get("debuff_amp_add", 0.0))
    if da_add:
        stats["debuff_amp"] = float(stats.get("debuff_amp", 0.0)) + da_add
        stats["party_debuff_amp_total"] = float(stats.get("party_debuff_amp_total", 0.0)) + da_add

    # (4) 최종피해 기본옵션: 본인만
    fd_add = float(u.get("final_dmg_add", 0.0))
    if fd_add and is_owner:
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + fd_add

    # =====================================================
    # 타입별 효과 처리
    # =====================================================

    # -----------------------
    # DPS 유니크 (본인만)
    # -----------------------
    if ut == "dps_type_damage":
        if not is_owner:
            return
        # 사격/마법 피해, 베기/타격 피해는 현재 공통 딜 공식의 피해량 축(dmg_bonus)에 합산
        stats["dmg_bonus"] = float(stats.get("dmg_bonus", 0.0)) + float(u.get("type_damage_add", 0.0))
        return

    if ut == "dps_beacon_atk":
        if not is_owner:
            return
        # 정열의 불씨: 공격력 +30% 상시
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
        return

    # -----------------------
    # STRIKER 유니크
    # strike_dmg_add(기본옵션)은 위에서 파티공유로 이미 반영됨
    # -----------------------
    if ut == "mala_strike_support":
        # 마라향: 모든속성피해 +15% 상시, 파티공유
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + float(u.get("all_elem_dmg_buff", 0.0))
        return

    if ut == "enhanced_mark":
        # 강화속성표식: 속성 폭발 피해 +30% 상시, 파티공유
        # - 속성강타 피해(element_strike_dmg)에 더하지 않음
        # - 표식 폭발 계산부에서 (1 + element_mark_explosion_dmg)로 별도 곱연산
        stats["element_mark_explosion_dmg"] = (
            float(stats.get("element_mark_explosion_dmg", 0.0))
            + float(u.get("mark_explosion_dmg_add", 0.0))
        )
        return

    # -----------------------
    # SUPPORT 유니크
    # -----------------------
    if ut == "crushed_pepper_support":
        # 크러쉬드페퍼맛 쿠키의 기억
        # - 식지않는 충성: 방어력 관통 +12%
        # - 회복/보호막으로 아군에게도 부여됨
        # - 이슬맛 쿠키: 30초 중 10초 유지 → 12% * 10/30 = 4%
        # - 샬롯/네온데니쉬: 끊기지 않는 것으로 보고 12% 상시
        armor_map = u.get("armor_pen_add_by_cookie", {}) or {}
        armor_add = float(armor_map.get(cookie_name_kr, u.get("armor_pen_add", 0.0)))
        stats["buff_armor_pen_raw"] = float(stats.get("buff_armor_pen_raw", 0.0)) + armor_add
        return

    if ut == "cherry_support":
        # 체리맛 쿠키의 기억
        # - 기본옵션 버프증폭 +36%는 위에서 파티 버프 계산에 이미 반영
        # - 체리 도화선: 공격력 +15% 상시
        # - 아군에게도 체리 도화선이 부여되므로 파티 공유
        stats["buff_atk_pct_raw"] = float(stats.get("buff_atk_pct_raw", 0.0)) + float(u.get("atk_pct_buff", 0.0))
        return

    if ut == "sleepless_night_support":
        # 불야성의 밤의 기억
        # - 기본옵션 디버프증폭 +36%는 위에서 항상 반영
        # - 밤의 열기 받는 피해 +8%만 디버프를 못 묻히는 네온데니쉬일 때 0%
        dmg_taken_map = u.get("dmg_taken_inc_by_cookie", {}) or {}
        dmg_taken_add = float(dmg_taken_map.get(cookie_name_kr, u.get("dmg_taken_inc", 0.0)))
        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + dmg_taken_add
        return

    # -----------------------
    # ANY 유니크 (본인만)
    # -----------------------
    if ut == "chili_sauce":
        if not is_owner:
            return
        # 특제 칠리소스: 공격력 +8%, 치명타피해 +12% 상시
        stats["buff_atk_pct_raw"]  = float(stats.get("buff_atk_pct_raw", 0.0))  + float(u.get("atk_pct_buff", 0.0))
        stats["buff_crit_dmg_raw"] = float(stats.get("buff_crit_dmg_raw", 0.0)) + float(u.get("crit_dmg_buff", 0.0))

        stats["_chili_hp_cost_pct"] = float(u.get("hp_cost_pct", 0.0))
        stats["_chili_shield_pct"] = float(u.get("shield_pct", 0.0))
        stats["_chili_shield_dur"] = float(u.get("shield_duration", 0.0))
        stats["_chili_move_spd"] = float(u.get("move_spd_buff", 0.0))
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
    # NOTE: build_stats_for_combo에서 이미 세팅한 값이 있어도, 여기서는 파티 오라만 누적하려는 의도면 1.0 리셋이 맞음
    stats["passive_dmg_mult"] = 1.0
    stats["elem_dmg_mult"] = 1.0

    # 스케일 계산용 total 키 보장
    stats.setdefault("party_buff_amp_total", float(stats.get("buff_amp", 0.0)))
    stats.setdefault("party_debuff_amp_total", float(stats.get("debuff_amp", 0.0)))

    # 중복 적용 방지(이 stats 스코프 내에서만)
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
    in_party_cherry_cola = ("체리콜라맛 쿠키" in party)
    in_party_moonlight = ("달빛술사 쿠키" in party)

    has_isle = in_party_isle or (main_cookie_name == "이슬맛 쿠키")
    has_wind = in_party_wind or (main_cookie_name == "윈드파라거스 쿠키")
    has_char = in_party_char or (main_cookie_name == "샬롯맛 쿠키")
    has_neon = in_party_neon or (main_cookie_name == "네온데니쉬맛 쿠키")
    has_lungsha = in_party_lungsha or (main_cookie_name == "룽샤맛 쿠키")
    has_marble = in_party_marble or (main_cookie_name == "마블베리맛 쿠키")
    has_cherry_cola = in_party_cherry_cola or (main_cookie_name == "체리콜라맛 쿠키")
    has_moonlight = in_party_moonlight or (main_cookie_name == "달빛술사 쿠키")

    # =====================================================
    # [유틸] 세트효과 가져오기
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
        # 체리콜라는 스트라이커 장비를 쓰되, 잠재/일반 설탕유리조각 후보만 딜러형으로 계산한다.
        "체리콜라맛 쿠키": "황금 예복",
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

    # -----------------------------------------------------
    # 버프/디버프 증폭은 파티 전체 합산값이 아니라
    # "그 효과를 부여한 쿠키"의 개인 증폭량만 사용한다.
    # 예: A 버프 50%, A 벞증 20% + B 버프 50%, B 벞증 20%
    #     => 50*1.2 + 50*1.2 = 120%, 100*1.4가 아님.
    # -----------------------------------------------------
    FIXED_PARTY_SEAZ_FOR_AMP: Dict[str, str] = {
        "이슬맛 쿠키": "허브그린드:번뜩이는 기지",
        "샬롯맛 쿠키": "허브그린드:가벼운 손길",
        "네온데니쉬맛 쿠키": "허브그린드:작은 성배",
        "달빛술사 쿠키": "플럼나이트:달빛의 속삭임",
        "윈드파라거스 쿠키": "리치코랄:믿음직한 브리더",
        "룽샤맛 쿠키": "리치코랄:빛나는 은하수",
        "마블베리맛 쿠키": "리치코랄:빛나는 은하수",
        "체리콜라맛 쿠키": "리치코랄:빛나는 은하수",
    }

    FIXED_PARTY_UNIQUE_FOR_AMP: Dict[str, str] = {
        "이슬맛 쿠키": "체리맛 쿠키의 기억",
        "샬롯맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
        "네온데니쉬맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
        "달빛술사 쿠키": "불야성의 밤의 기억",
        "윈드파라거스 쿠키": "룽샤맛 쿠키의 기억",
        "룽샤맛 쿠키": "룽샤맛 쿠키의 기억",
        "마블베리맛 쿠키": "룽샤맛 쿠키의 기억",
        "체리콜라맛 쿠키": "룽샤맛 쿠키의 기억",
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
            return float(u.get(key, 0.0))
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
            moon_unique = "NONE" if moon_unique_raw == "NONE" else (_selected_party_unique_name(cookie_name) or "불야성의 밤의 기억")
            ba += _assumed_moonlight_buff_amp_for_party(
                equip_name=_get_party_set_name(cookie_name) or "시간관리국의 제복",
                seaz_name=_selected_party_seaz_name(cookie_name) or "플럼나이트:달빛의 속삭임",
                unique_name=moon_unique,
            )

        # assumed_*에 고정 시즈 보조옵션이 포함된 쿠키는 선택 시즈와의 차이만 더한다.
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
            # 달빛술사는 유니크/장비/시즈 선택에 따라 필요한 디벞 잠재 수가 달라진다.
            # 선택 조합 기준으로 150%를 넘기는 최소 디벞 잠재만 자동 반영한다.
            moon_unique_raw = ""
            try:
                u_map = party_uniques or stats.get("party_uniques") or {}
                if isinstance(u_map, dict):
                    moon_unique_raw = str(u_map.get(cookie_name, "") or "")
            except Exception:
                moon_unique_raw = ""
            moon_unique = "NONE" if moon_unique_raw == "NONE" else (_selected_party_unique_name(cookie_name) or "불야성의 밤의 기억")
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

    # 잎새의 활강은 윈파가 건 디버프이므로, 파티원으로 들어간 경우에도
    # 메인 쿠키 디버프 증폭이 아니라 윈파 개인 디버프 증폭만 사용한다.
    if has_wind:
        stats["_wind_leaf_glide_owner_debuff_amp"] = _debuff_amp_for_owner("윈드파라거스 쿠키")

    def _effective_party_support_set(cookie_name: str) -> str:
        """세부사항 UI에서 사용자가 선택한 서포터 장비를 그대로 사용한다."""
        return _get_party_set_name(cookie_name)

    PARTY_EQUIP_STACK_ORDER = [
        "이슬맛 쿠키",
        "샬롯맛 쿠키",
        "네온데니쉬맛 쿠키",
        "달빛술사 쿠키",
        "윈드파라거스 쿠키",
        "룽샤맛 쿠키",
        "마블베리맛 쿠키",
        "체리콜라맛 쿠키",
    ]

    def _party_set_effect_first_applicable(cookie_name: str, set_name: str, effect_kind: str = "global") -> bool:
        """동일 장비 세트효과 중복 방지.

        메인 장비로 이미 같은 세트가 적용되어 있으면 파티원의 같은 세트효과는 더하지 않는다.
        파티원끼리 같은 세트를 착용하면 효과 종류별로 첫 번째 적용 가능 착용자 1명만 반영한다.
        단, 속성 조건부 효과는 조건을 만족하는 착용자 중 첫 번째만 반영한다.
        """
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
        """장비의 속성 조건부 효과는 메인 딜러와 착용자 속성이 같을 때만 적용"""
        main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
        wearer_elem = COOKIE_ELEMENT.get(cookie_name, "")
        return bool(main_elem and wearer_elem and main_elem == wearer_elem)

    def _add_party_equip_all_elem_if_same(cookie_name: str, add_elem: float):
        """대마술사 모속피처럼 속성 조건이 있는 효과만 메인과 착용자 속성이 같을 때 적용"""
        if add_elem and _same_element_as_main(cookie_name):
            stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + add_elem

    def _add_party_equip_all_elem_always(add_elem: float):
        """해적셋 모속피는 메인/착용자 속성과 상관없이 적용"""
        if add_elem:
            stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + add_elem

    def _add_party_equip_elem_res_if_same(cookie_name: str, add_res: float):
        """파티 장비의 속성 내성 감소는 메인과 착용자 속성이 같을 때만 적용"""
        if add_res and _same_element_as_main(cookie_name):
            stats["elem_res_reduction_no_scale_raw"] = float(stats.get("elem_res_reduction_no_scale_raw", 0.0)) + add_res

    def _meteor_elem_res_for_owner(cookie_name: str, base: dict) -> float:
        """유성우 세트 속성 내성 감소값.

        기본 유성우는 평균 보정값 5%를 사용하지만, 달빛술사 쿠키가 착용한
        유성우만 예외적으로 원값 10%를 그대로 적용한다.
        """
        if str(cookie_name or "") == "달빛술사 쿠키":
            return 0.10
        return float((base or {}).get("elem_res_reduction_raw", 0.0))

    # -----------------------------------------------------
    # (A) 선반영(증폭만) 스케일에 영향을 주는 것만 여기서
    # -----------------------------------------------------
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

    _apply_once("AUTO_SET_PRE_SCALE_AMPS", _apply_party_auto_sets_pre_scale)

    # =====================================================
    # 3) 버프/디버프 증폭 스케일
    # =====================================================
    BA = float(stats.get("party_buff_amp_total", stats.get("buff_amp", 0.0)))
    DA = float(stats.get("party_debuff_amp_total", stats.get("debuff_amp", 0.0)))

    # =====================================================
    # (B) 실제 세트효과 적용: 스케일 "미적용"
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

    _apply_once("AUTO_SET_POST_SCALE_EFFECTS_NO_SCALING", _apply_party_auto_sets_post_scale_no_scaling)

    # =====================================================
    # 4) 쿠키별 파티 버프
    # =====================================================

    # =====================================================
    # [COOKIE] 이슬맛 쿠키
    # [ROLE] 파티 버프 / 상시 유지 가정
    # - 치명타 피해 +56%              → 벞증 적용
    # - 공격력 증가 +22.4%           → 벞증 적용
    # - 기본 공격 피해 +10%          → 벞증 적용
    # - 모든 속성 피해 +30%          → 벞증 영향 X
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

        # 모든속성피해 +30% (벞증 영향 X)
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + 0.30

    # =====================================================
    # [COOKIE] 윈드파라거스 쿠키
    # [ROLE] 파티 버프
    # - 치명타 피해 +40%
    # - 버프 증폭 / 디버프 증폭 영향 X
    # - 최종 스탯 표에 보이도록 crit_dmg에 직접 합산
    # =====================================================
    def _apply_wind_party_effects():
        # [이어지는 마음] 에메랄딘 치피 +40%
        # - 윈파가 파티원일 때: 메인 쿠키에게 파티 버프로 1회 적용
        # - 윈파가 메인일 때: wind_cycle_damage()에서 사이클 업타임 기준으로 1회 적용
        #   여기서도 더하면 윈파 본인 기준 +40%가 중복 반영될 수 있으므로 제외한다.
        if main_cookie_name == "윈드파라거스 쿠키":
            return

        u = float(get_uptime("PARTY_WIND_CRITDMG_0p40"))
        stats["crit_dmg"] = float(stats.get("crit_dmg", 1.0)) + (0.40 * u)

    # =====================================================
    # [COOKIE] 룽샤맛 쿠키
    # [ROLE] 파티 디버프 / 궁극기 받피증
    # - 불가역 + 주화입마: 받는 피해 +10% +33.6%
    # - 메인과 룽샤 속성이 같으면 받는 피해 +20% 추가
    # - 삼매각화: 적이 받는 궁극기 피해 +35%
    # - 디버프 증폭 영향 X
    # - 룽샤 본인이 메인일 때는 파티 효과 미적용
    # =====================================================
    def _apply_lungsha_party_effects():
        if not (in_party_lungsha or (main_cookie_name == "룽샤맛 쿠키")):
            return
        if main_cookie_name == "룽샤맛 쿠키":
            return

        # 불가역 10% + 주화입마 33.6%
        base_taken = 0.10 + 0.336

        # 메인과 룽샤 속성이 같으면 받는 피해 +20% 추가
        main_elem = COOKIE_ELEMENT.get(main_cookie_name, "")
        lungsha_elem = COOKIE_ELEMENT.get("룽샤맛 쿠키", "")
        if main_elem and (main_elem == lungsha_elem):
            base_taken += 0.20

        stats["dmg_taken_inc"] = float(stats.get("dmg_taken_inc", 0.0)) + base_taken

        # 삼매각화: 적이 받는 궁극기 피해 증가 +35%
        stats["enemy_ult_taken_inc"] = float(stats.get("enemy_ult_taken_inc", 0.0)) + 0.35

    # =====================================================
    # [COOKIE] 마블베리맛 쿠키
    # [ROLE] 파티 디버프 / 속성강타 피해 지원
    # - 크래시: 쿠키에게 받는 피해 +28% × 1.15
    # - 메인이 어둠속성이면 받는 피해 +10% 추가
    # - 아티팩트 충전은 타이밍: 속성강타 피해 +25%
    # - 버프 증폭 / 디버프 증폭 영향 X
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
    # [COOKIE] 체리콜라맛 쿠키
    # [ROLE] 파티 받는 피해 증가 지원
    # - 버블포인트: 쿠키에게 받는 피해 +22.4%
    # - 달콤공격 1교시: 물속성 쿠키에게 받는 피해 +30%
    # - 끈적끈적 후폭풍: 강화 기본공격 적중 후 적이 받는 패시브 스킬 피해 +35%
    # - 마블베리처럼 디버프 증폭 영향 X
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
        # 적에게 받는 패시브 스킬 피해 +35%를 부여한다고 보고 메인 패시브 피해에 반영한다.
        try:
            sticky = float(ARTIFACTS.get("끈적끈적 후폭풍", {}).get("cherry_cola", {}).get("enemy_passive_taken_inc", 0.0))
        except Exception:
            sticky = 0.0
        if sticky:
            stats["enemy_passive_taken_inc"] = float(stats.get("enemy_passive_taken_inc", 0.0)) + sticky

    # =====================================================
    # [COOKIE] 샬롯맛 쿠키
    # [ROLE] 파티 버프 / 아티팩트 오라 / 본인 전용 효과
    # - 결속: 공격력 증가 +39.2%              → 벞증 적용
    # - 바늘땀/결속: 패시브 피해 +10%         → 벞증 적용
    # [ARTI] 희미한 날갯짓
    # - 적이 받는 피해 +10%                   → enemy_dmg_taken_inc
    # - 적이 받는 패시브 피해 +10%            → enemy_passive_taken_inc
    # - 모든 속성 피해 +25%                   → 샬롯 본인 전용 buff_all_elem_dmg_raw
    # - 샬롯 본인일 때 패시브 배율 ×1.20      → passive_dmg_mult
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

        # [ARTI] 희미한 날갯짓
        _apply_charlotte_wings_artifact_aura()

    def _apply_charlotte_wings_artifact_aura():
        if not has_char:
            return

        # 파티 공통: 적이 받는 피해 +10%
        stats["enemy_dmg_taken_inc"] = float(stats.get("enemy_dmg_taken_inc", 0.0)) + (
            CHAR_WINGS_ENEMY_TAKEN_INC
        )

        # 샬롯 본인 전용: 진혼 모든 속성 피해 +25%
        # 파티 딜러에게는 공유하지 않는다.
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
    # [COOKIE] 네온데니쉬 쿠키
    # [ROLE] 파티 버프 / 궁극기 받피증
    # - 긴급 패치: 공격력 증가 +34.6%        → 벞증 적용
    # - 승급 포함: 궁극기 스킬 피해 +15%     → 벞증 적용
    # - 아티팩트 관리자 권한: 모든 속성 피해 +30%
    # - 아티팩트 치트키 + 치명적 오류:
    #   적이 받는 궁극기 피해 +8% +5.8%
    # - 궁극기 한정 효과이므로 enemy_ult_taken_inc 축 사용
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

        # [ARTI] 관리자 권한: 모든 속성 피해 +30%
        stats["buff_all_elem_dmg_raw"] = float(stats.get("buff_all_elem_dmg_raw", 0.0)) + (
            NEON_PARTY_ALL_ELEM_ADD
        )

        # [ARTI] 치트키 + 치명적 오류: 적이 받는 궁극기 피해 증가
        stats["enemy_ult_taken_inc"] = float(stats.get("enemy_ult_taken_inc", 0.0)) + (
            NEON_PARTY_ENEMY_ULT_TAKEN_INC
        )

    # =====================================================
    # [COOKIE] 달빛술사 쿠키
    # [ROLE] 파티 디버프 / 달빛 환대 영역 / 공격력 버프
    # - 달과 별의 노래: 방어력 감소 28%
    # - 찬란한 꿈의 끝자락: 달빛 환대 영역 내 아군 최종 피해 +25%
    # - 한밤의 자장가: 공격력 증가 +30% (아티팩트 공증, 벞증 미적용)
    # - 고요히 흐르는 월광: 모든 속성 피해 +50% / 치명타 피해 +50%는 달빛술사 본인 전용
    # - 전용 아티팩트 치피와 승급 신비공/치피는 달빛술사 본인 계산에서만 적용
    # =====================================================
    def _apply_moonlight_party_effects():
        if not has_moonlight:
            return

        # 궁극기 선잠: 방어력 감소 28%
        # 디버프 증폭은 파티 합산이 아니라 달빛술사 본인의 디버프 증폭만 적용한다.
        moon_def_down = 0.28 * _debuff_scale_for_owner("달빛술사 쿠키")
        stats["def_reduction_no_scale_raw"] = float(stats.get("def_reduction_no_scale_raw", 0.0)) + moon_def_down
        stats["enemy_def_down_raw"] = float(stats.get("enemy_def_down_raw", 0.0)) + moon_def_down

        # 달빛 환대 영역: 최종 피해 +25%
        stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + 0.25

        # 파티원으로 들어간 달빛술사 공유 효과
        # - 아군 공유: [한밤의 자장가] 공격력 증가, [달무리] 보호막 생성
        # - 본인 전용: [아름다운 밤의 산책], [새벽의 안내자],
        #             [고요히 흐르는 월광] 모든 속성 피해/치명타 피해
        # 보호막은 딜 계산에는 직접 반영하지 않고, 유니크 설탕유리조각(샬롯과 같은 크러쉬드페퍼)의
        # 방어 관통 유지 조건으로만 본다.
        if in_party_moonlight and main_cookie_name != "달빛술사 쿠키":
            # 한밤의 자장가 공격력 +30%는 아티팩트 공증으로 처리한다.
            # 달빛술사 본인의 버프증폭을 곱하지 않는다.
            add_final_atk = 0.30
            stats["final_atk_mult"] = float(stats.get("final_atk_mult", 0.0)) + add_final_atk
            stats["buff_final_atk_mult"] = float(stats.get("buff_final_atk_mult", 0.0)) + add_final_atk

            # 고요히 흐르는 월광의 모든 속성 피해 +50%는 달빛술사 본인 전용으로 본다.
            # 따라서 달빛술사가 파티원일 때 메인 딜러에게는 추가하지 않는다.

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
    }
    def _get_party_seaz_name(cookie_name: str) -> str:
        # 1) UI/외부에서 들어온 dict 우선
        m = stats.get("party_seaz")
        if isinstance(m, dict):
            v = m.get(cookie_name, "")
            if v and v != "NONE":
                return str(v)

        # 2) 개별 키 형태도 지원(원하면)
        v2 = stats.get(f"seaz__{cookie_name}", "")
        if v2 and v2 != "NONE":
            return str(v2)

        # 3) fallback: 파티에 있고 메인이 아니면 고정값
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

        # 1) 파티 시즈 passive 중 공용 처리(모속피, 공퍼, 속강피, 방관 등)
        apply_seaz_passive(
            stats, seaz,
            owner_cookie_name=cookie_name,      # 파티원(그 쿠키)의 시즈
            main_cookie_name=main_cookie_name   # 현재 메인
        )

        # 2) 파티 시즈 sub 적용 규칙
        # - 시즈나이트 보조옵션은 기본적으로 장착자 본인에게만 적용
        # - 파티원 시즈의 sub 중 메인에게 공유되는 것은 element_strike_dmg만 허용
        #   예) 리치코랄 브리더 sub
        #      속성 강타 피해 +25% → 파티 공유
        #      특수 스킬 피해 +15%, 궁극기 피해 +15% → 윈파 본인만, 메인에게 미적용
        # - 페퍼루비 브리더 sub의 기본공격 피해/치명타 피해도 윈파 본인만, 메인에게 미적용
        info = SEAZNITES.get(seaz, {}) or {}
        sub = info.get("sub", {}) or {}
        if sub and "element_strike_dmg" in sub:
            stats["element_strike_dmg"] = float(stats.get("element_strike_dmg", 0.0)) + float(sub["element_strike_dmg"])

        # 3) 파티 시즈 passive 중, apply_seaz_passive가 담당하지 않는 직접 스탯만 추가
        passive = info.get("passive", {}) or {}
        if passive:
            for k in ("basic_dmg", "special_dmg", "ult_dmg", "passive_dmg", "final_dmg", "atk_spd", "move_spd"):
                if k in passive:
                    stats[k] = float(stats.get(k, 0.0)) + float(passive[k])

            if "final_dmg_stack" in passive and "max_stacks" in passive:
                stats["final_dmg"] = float(stats.get("final_dmg", 0.0)) + (float(passive["final_dmg_stack"]) * float(passive["max_stacks"]))

            # 달빛의 속삭임: 버프 증폭량 + 디버프 증폭량의 100%만큼
            # 모든 속성 피해 증가(최대 100%)는 시즈 착용자 본인 전용으로 본다.
            # 파티 쿠키가 착용한 경우 메인 딜러에게 공유하지 않는다.
            # 착용자가 메인인 경우의 본인 적용은 apply_seaz_passive()의 self-only 처리에서 반영된다.

    # =====================================================
    # 7) 파티원 유니크 설유 효과 합산
    # =====================================================
    FIXED_PARTY_UNIQUE: Dict[str, str] = {
        "이슬맛 쿠키": "체리맛 쿠키의 기억",
        "샬롯맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
        "네온데니쉬맛 쿠키": "크러쉬드페퍼맛 쿠키의 기억",
        "달빛술사 쿠키": "불야성의 밤의 기억",
        "윈드파라거스 쿠키": "룽샤맛 쿠키의 기억",
        "룽샤맛 쿠키": "룽샤맛 쿠키의 기억",
        "마블베리맛 쿠키": "룽샤맛 쿠키의 기억",
        "체리콜라맛 쿠키": "룽샤맛 쿠키의 기억",
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

    # (0) 파티 유니크 먼저(벞증 스케일에 영향 주는 경우가 있어서)
    _apply_once("PARTY_UNIQUE_ISLE",       lambda: _apply_party_member_unique("이슬맛 쿠키"))
    _apply_once("PARTY_UNIQUE_CHARLOTTE",  lambda: _apply_party_member_unique("샬롯맛 쿠키"))
    _apply_once("PARTY_UNIQUE_NEON",      lambda: _apply_party_member_unique("네온데니쉬맛 쿠키"))
    _apply_once("PARTY_UNIQUE_MOONLIGHT", lambda: _apply_party_member_unique("달빛술사 쿠키"))
    _apply_once("PARTY_UNIQUE_WIND",       lambda: _apply_party_member_unique("윈드파라거스 쿠키"))
    _apply_once("PARTY_UNIQUE_LUNGSHA",    lambda: _apply_party_member_unique("룽샤맛 쿠키"))
    _apply_once("PARTY_UNIQUE_MARBLE",     lambda: _apply_party_member_unique("마블베리맛 쿠키"))
    _apply_once("PARTY_UNIQUE_CHERRY_COLA", lambda: _apply_party_member_unique("체리콜라맛 쿠키"))

    # (1) 쿠키 파티버프/오라
    if has_char:
        # 샬롯 아티 희미한 날갯짓은 _apply_charlotte_party_effects() 안에서 1회만 적용
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

    if has_cherry_cola:
        _apply_once("PARTY_CHERRY_COLA", _apply_cherry_cola_party_effects)

    # (2) 파티 시즈 패시브
    _apply_once("PARTY_SEAZ_ISLE",       lambda: _apply_party_member_seaz("이슬맛 쿠키"))
    _apply_once("PARTY_SEAZ_CHARLOTTE",  lambda: _apply_party_member_seaz("샬롯맛 쿠키"))
    _apply_once("PARTY_SEAZ_NEON",      lambda: _apply_party_member_seaz("네온데니쉬맛 쿠키"))
    _apply_once("PARTY_SEAZ_MOONLIGHT", lambda: _apply_party_member_seaz("달빛술사 쿠키"))
    _apply_once("PARTY_SEAZ_WIND",       lambda: _apply_party_member_seaz("윈드파라거스 쿠키"))
    _apply_once("PARTY_SEAZ_LUNGSHA",    lambda: _apply_party_member_seaz("룽샤맛 쿠키"))
    _apply_once("PARTY_SEAZ_MARBLE",     lambda: _apply_party_member_seaz("마블베리맛 쿠키"))
    _apply_once("PARTY_SEAZ_CHERRY_COLA", lambda: _apply_party_member_seaz("체리콜라맛 쿠키"))

    # 파티원의 벞증/디벞증은 각 효과 계산에만 사용하고,
    # 최종 stats의 증폭 표시는 현재 메인 쿠키 본인 값으로 되돌린다.
    stats["buff_amp"] = float(stats.get("self_buff_amp_total", stats.get("buff_amp_total", stats.get("buff_amp", 0.0))))
    stats["debuff_amp"] = float(stats.get("self_debuff_amp_total", stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))))

    return stats


# 호감도 공격력 데이터와 friendship_atk_for()는 cookie/stat_data.py에서 관리한다.

def calc_attack_value(stats: Dict[str, float], *, floor_result: bool = False) -> float:
    """
    최종 공격력 계산.
    공격력 = (기본공격력 + 속성공격력)
           × (1 + 공퍼합) × (1 + 버프공퍼합)
           + 호감도공

    이 코드의 stats["base_atk"]는 호감도 공격력을 제외한 값이다.
    그래서 공식 원문 `(표기 기본공격력 - 호감도공 + 속성공격력)`과 같은 의미로
    여기서는 `(base_atk + 속성공격력)`을 사용한다.

    - 공퍼합: base_atk_pct + atk_pct
    - 버프공퍼합: buff_atk_pct_raw + final_atk_mult
      기존 코드에서 final_atk_mult로 관리하던 공격력 증가%도 여기 버프공퍼합에 포함한다.
    """
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

    # -------------------------
    # 공격력(공퍼) 관련
    # -------------------------
    parts = attack_formula_parts(s)
    self_atk_pct_add = parts["atk_pct_sum"]
    party_atk_pct_buff = parts["buff_atk_pct_sum"]
    equip_atk_mult = 1.0 + self_atk_pct_add
    buff_atk_mult = parts["buff_atk_mult"]
    atk_mult = (1.0 + self_atk_pct_add) * (1.0 + party_atk_pct_buff) * buff_atk_mult
    atk_pct_equiv = self_atk_pct_add
    atk_pct_sum = self_atk_pct_add

    # -------------------------
    # 치확/치피 (표시용)
    # -------------------------
    eff_cr = clamp(
        float(s.get("crit_rate", 0.0)) + float(s.get("buff_crit_rate_raw", 0.0)),
        0.0, 1.0
    )

    # "총 치피" 배율(mult) 기준 계산 (1.90 => 190%)
    eff_cd_mult = max(1.0, float(s.get("crit_dmg", 1.0)) + float(s.get("buff_crit_dmg_raw", 0.0)))
    eff_cd_total_pct = eff_cd_mult * 100.0
    eff_cd_bonus_pct = (eff_cd_mult - 1.0) * 100.0  # 참고용: +90% 같은 “추가치피”

    # -------------------------
    # 속성/방관/디버프
    # -------------------------
    eff_all_elem = float(s.get("all_elem_dmg", 0.0)) + float(s.get("buff_all_elem_dmg_raw", 0.0))
    eff_armor_pen = clamp(
        float(s.get("armor_pen", 0.0)) + float(s.get("buff_armor_pen_raw", 0.0)),
        0.0, 0.8
    )

    # raw 디버프 축은 해당 stats(현재 메인 쿠키) 본인의 디버프 증폭만 적용한다.
    # 파티원이 거는 디버프는 적용 시점에 그 파티원 개인 디벞증을 곱해 no_scale 축에 넣는다.
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
    # 패시브 (표시용: promo 절대 안 섞음)
    # =====================================================
    p = float(s.get("passive_dmg", 0.0))                 # add
    t = float(s.get("enemy_passive_taken_inc", 0.0))     # add
    m = float(s.get("passive_dmg_mult", 1.0))            # mult (예: 1.20)

    passive_total_mult = (1.0 + p) * (1.0 + t) * m
    passive_total_bonus = passive_total_mult - 1.0
    passive_total_pct = passive_total_mult * 100.0

    return {
        "numeric": {
            # atk
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

            # crit
            "eff_crit_rate": eff_cr,
            "eff_crit_dmg_mult": eff_cd_mult,          # 1.90
            "eff_crit_dmg_total_pct": eff_cd_total_pct, # 190.0
            "eff_crit_dmg_bonus_pct": eff_cd_bonus_pct, # 90.0

            # other
            "eff_all_elem_dmg": eff_all_elem,
            "eff_armor_pen": eff_armor_pen,
            "eff_def_reduction": eff_def_red,
            "eff_elem_res_reduction": eff_elem_res_red,
            "eff_mark_res_reduction": eff_mark_res_red,
            "dmg_bonus": eff_dmg_bonus,

            # passive (display-only)
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
    """스킬 피해 계산 공통값을 stats에 캐싱하고, 같은 stats dict면 바로 재사용한다."""
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

    basic_mult = 1.0 + float(get("basic_dmg", 0.0))
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
        # - dmg_taken_inc: 쿠키 자체 디버프/받피증(룽샤, 체리콜라 등)
        # - enemy_dmg_taken_inc: 적이 받는 피해 증가(샬롯 아티팩트 등)
        # 두 축은 서로 다른 출처이므로 합산하지 않고 별도 배율로 곱한다.
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
    """미리 계산된 damage context를 사용해 스킬 피해를 계산한다."""
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
    #   표식에 들어간 총 데미지
    #   × 0.712
    #   × (1 - (보스 기본 속성 내성 - 속성 내성 감소))
    #   × (1 + 속성강타 피해 증가)
    # - 속성내성감소는 디버프 증폭을 받는 raw 축과, 증폭을 받지 않는 no_scale 축을 분리해서 합산
    # - 같은 속성/다른 속성 차이는 게이지 축적 속도 문제로 보고,
    #   현재 사이클 총딜 기반 계산에서는 속성강타 데미지를 추가 절반 처리하지 않음
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

    # 강화속성표식 피해 증가(룽샤맛 쿠키의 기억)
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
# Helpers - 파티 가정값
# =====================================================
def _assumed_isle_buff_amp_for_party() -> float:
    from .dew import BASE_STATS_ISLE, ISLE_FIXED_POT, ISLE_FIXED_ARTIFACT

    ba = 0.0

    try:
        ba += float(BASE_STATS_ISLE["이슬맛 쿠키"].get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        ba += float(ISLE_FIXED_POT.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        a = ARTIFACTS.get(ISLE_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        seaz = SEAZNITES.get(globals().get("FIXED_SEAZ_ISLE", "허브그린드:번뜩이는 기지"), {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
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
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        ba += float(CHARLOTTE_FIXED_POT.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        a = ARTIFACTS.get(CHARLOTTE_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        fixed_seaz = globals().get("FIXED_SEAZ_CHARLOTTE", "허브그린드:가벼운 손길")
        seaz = SEAZNITES.get(fixed_seaz, {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
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
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        ba += float(NEON_POTENTIALS_FIXED.get("buff_amp", 0)) * float(POTENTIAL_INC["buff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        a = ARTIFACTS.get(NEON_FIXED_ARTIFACT, {})
        ba += float((a.get("base_stats") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        fixed_seaz = globals().get("FIXED_SEAZ_NEON", "허브그린드:작은 성배")
        seaz = SEAZNITES.get(fixed_seaz, {})
        ba += float((seaz.get("sub") or {}).get("buff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    return ba


MOONLIGHT_DEBUFF_AMP_TARGET = 1.50
MOONLIGHT_POTENTIAL_SLOTS = 8
# 달술 잠재력에서 버프증폭+디버프증폭은 합산 최대 4개까지만 사용한다.
MOONLIGHT_MAX_AMP_POTENTIALS = 4
MOONLIGHT_MAX_DEBUFF_POTENTIALS = 4


def _moonlight_equip_debuff_amp(equip_name: str) -> float:
    """달빛술사 장비에서 얻는 디버프 증폭 합계(세트효과 + 부위 유니크)."""
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
        unique_name = "불야성의 밤의 기억"
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
    unique_name: str = "불야성의 밤의 기억",
) -> float:
    """잠재를 제외한 달빛술사 개인 디버프 증폭 합계."""
    da = 0.15 + 0.24  # 기본 디버프 증폭 + 전용무기
    try:
        da += float((ARTIFACTS.get("고요히 흐르는 월광", {}).get("base_stats") or {}).get("debuff_amp", 0.0))
    except Exception:
        pass
    da += _moonlight_seaz_debuff_amp(seaz_name)
    da += _moonlight_equip_debuff_amp(equip_name or "시간관리국의 제복")
    da += _moonlight_unique_debuff_amp(unique_name or "불야성의 밤의 기억")
    return max(0.0, da)


def moonlight_auto_potentials_for_combo(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "불야성의 밤의 기억",
    target_debuff_amp: float = MOONLIGHT_DEBUFF_AMP_TARGET,
    total_slots: int = MOONLIGHT_POTENTIAL_SLOTS,
) -> Dict[str, int]:
    """달빛술사 잠재 자동 배분.

    디버프 증폭 150% 근처까지 우선 확보하면 선잠 방깎 70%와
    [아름다운 밤의 산책] 최종피해 120%가 상한에 도달한다.

    단, 달술 잠재력에서 버프증폭+디버프증폭은 합산 최대 4개만 사용한다.
    따라서 디벞 잠재는 150%를 넘기는 데 필요한 만큼만 넣고,
    한밤의 자장가 공격력 +30%는 아티팩트 공증으로 보고 버프증폭을 곱하지 않는다.
    따라서 디벞 상한에 필요한 만큼만 디버프증폭 잠재를 사용하고,
    남는 잠재는 버프증폭이 아니라 공격력%로 사용한다.
    """
    debuff_inc = float(POTENTIAL_INC.get("debuff_amp", 0.10) or 0.10)
    buff_inc = float(POTENTIAL_INC.get("buff_amp", 0.10) or 0.10)
    total_slots = max(0, int(total_slots or 0))
    max_amp_slots = max(0, min(total_slots, int(MOONLIGHT_MAX_AMP_POTENTIALS)))
    max_debuff_slots = max(0, min(max_amp_slots, int(MOONLIGHT_MAX_DEBUFF_POTENTIALS)))

    base_da = _moonlight_base_debuff_amp_without_potential(equip_name, seaz_name, unique_name)
    missing = max(0.0, float(target_debuff_amp) - base_da)
    need_debuff = int(math.ceil(max(0.0, missing - 1e-9) / debuff_inc)) if debuff_inc > 0 else 0
    debuff_slots = max(0, min(max_debuff_slots, need_debuff))

    # 한밤의 자장가 공격력 버프는 벞증을 받지 않으므로 버프증폭 잠재는 사용하지 않는다.
    buff_slots = 0
    atk_slots = max(0, total_slots - debuff_slots)

    return {
        "atk_pct": atk_slots,
        "debuff_amp": debuff_slots,
        "buff_amp": buff_slots,
        "elem_atk": 0,
        "crit_rate": 0,
        "crit_dmg": 0,
        "armor_pen": 0,
    }


def _assumed_moonlight_buff_amp_for_party(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "불야성의 밤의 기억",
) -> float:
    """파티 달빛술사의 잠재 버프증폭 가정치.

    한밤의 자장가 공격력 +30%는 아티팩트 공증으로 보고 버프증폭을 곱하지 않는다.
    따라서 달빛술사의 파티 기여 계산에서는 버프증폭 잠재를 0으로 본다.
    """
    return 0.0

def _assumed_moonlight_debuff_amp_for_party(
    equip_name: str = "시간관리국의 제복",
    seaz_name: str = "플럼나이트:달빛의 속삭임",
    unique_name: str = "불야성의 밤의 기억",
) -> float:
    """파티 달빛술사의 개인 디버프 증폭 가정치.

    선택한 유니크 설탕유리조각/장비/시즈에 맞춰 디벞 잠재를 자동 조정한다.
    150%를 넘기는 데 필요한 디벞 잠재만 사용하고,
    남는 잠재는 버프증폭이 아니라 공격력%로 배분한다.
    """
    pot = moonlight_auto_potentials_for_combo(equip_name, seaz_name, unique_name)
    da = _moonlight_base_debuff_amp_without_potential(equip_name, seaz_name, unique_name)
    try:
        da += float(pot.get("debuff_amp", 0)) * float(POTENTIAL_INC["debuff_amp"])
    except Exception:
        pass
    return max(0.0, da)


def _assumed_lungsha_debuff_amp_for_party(main_cookie_name: str) -> float:
    """파티 룽샤의 디버프 증폭 가정치.

    룽샤 파티 기여는 현재 코드 기준으로
    - 받는 피해 증가
    - 적이 받는 궁극기 피해 증가
    만 사용하고, 방어력 감소/속성내성감소 스킬 디버프는 없다.

    따라서 잠재/장비 유래 debuff_amp를 파티 디버프 증폭치에 더하지 않는다.
    (장비/세트 자체 효과는 no-scale 축에서 별도 처리)
    """
    return 0.0


def _assumed_marble_debuff_amp_for_party() -> float:
    """마블베리 장비 유래 디버프 증폭은 선택 장비 기준으로 apply_party_buffs에서 반영한다."""
    return 0.0

def _assumed_wind_debuff_amp_for_party() -> float:
    """윈파의 고정 잠재/아티팩트 디버프 증폭만 반영한다.

    장비 유래 디버프 증폭은 세부사항에서 선택한 장비 기준으로
    apply_party_buffs()의 파티 장비 처리 블록에서 별도 반영한다.
    """
    da = 0.0

    try:
        da += 4.0 * float(POTENTIAL_INC["debuff_amp"])
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    try:
        da += float(ARTIFACTS["이어지는 마음"]["unique_stats"].get("debuff_amp", 0.0))
    except Exception:
        # 선택 장비/아티팩트 데이터가 없으면 해당 가산값은 0으로 처리한다.
        pass

    return da

def _apply_neon_main_effects(stats: Dict[str, float], main_cookie_name: str) -> None:
    """네온 메인 전용 상시 효과를 반영한다.

    - 긴급 패치(궁): 공격력 증가 +34.6%  (벞증 적용)
    - 승급 포함: 궁극기 피해 +15%       (벞증 적용)
    - 아티(치트키) + 궁 디버프(치명적 오류): 적 받는 궁 피해 +8% + 5.8%
      -> enemy_ult_taken_inc 축 사용
    """
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
            moon_unique_for_ba = "불야성의 밤의 기억"
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
            moon_unique = "불야성의 밤의 기억"

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

    stats["party_buff_amp_total"] = ba
    stats["party_debuff_amp_total"] = da

# =====================================================
# Calculation - 최종 스탯/조합 계산
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

        # 디버프 raw (debuff_amp 적용)
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
    # 승급 효과 : 전부 곱연산 축으로 기록
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
        stats["promo_special_dmg_mult"]    *= BLACK_BARLEY_PROMO_SPECIAL_DMG_MULT
        stats["promo_ult_dmg_mult"]        *= BLACK_BARLEY_PROMO_ULT_DMG_MULT
        stats["promo_basic_dmg_mult"]      *= BLACK_BARLEY_PROMO_BASIC_DMG_MULT
        stats["_bb_promo"] = 1.0

    if cookie_name_kr == "샤이닝베리맛 쿠키" and SHINING_BERRY_PROMO_ENABLED:
        stats["promo_crit_rate_mult"]   *= SHINING_BERRY_PROMO_CRIT_RATE_MULT
        stats["promo_special_dmg_mult"] *= SHINING_BERRY_PROMO_SPECIAL_DMG_MULT
        stats["promo_ult_dmg_mult"]     *= SHINING_BERRY_PROMO_ULT_DMG_MULT
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

    # 장비 세트효과에 붙은 방어력 감소/속성 내성 감소는 스킬 디버프가 아니므로
    # 디버프 증폭을 받지 않는 no_scale 축에 반영한다.
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

    # 유성우 세트는 기본적으로 평균 보정값 5%를 쓰지만,
    # 달빛술사 쿠키가 착용한 경우에만 속성 내성 감소 10%를 그대로 적용한다.
    # 단, 이 값도 장비 효과이므로 디버프 증폭은 받지 않는다.
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
            # sub 스탯만 여기서 합산
            add(stats, seaz.get("sub", {}))

            # passive는 apply_seaz_passive에서 처리하는 것(특히 element_strike_dmg, ally_all_elem_dmg, heal_pct, atk_pct)은 여기서 절대 더하지 않기
            passive = seaz.get("passive", {}) or {}

            # apply_seaz_passive에 없는 것만 여기서 처리(현재 네 데이터에서 breeder류는 거의 해당 없음)
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
    # 본인 전용 증폭량 스냅샷: 파티 장비/파티 시즈/파티 유니크로 증가한 party_*_total과 분리한다.
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
    # - 일부 화면/최적화 경로에서 파티 버프 함수의 세부 효과가 표시값에 누락되는 경우가 있어,
    #   build_stats 최종 단계에서도 한 번 보장한다.
    # - 에너지 맥스: 속성강타 피해 +25%
    # - 버프 증폭 / 디버프 증폭 적용 X
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

    # 마블베리 에너지 맥스 +25%는 apply_party_buffs() 내부에서
    # _marble_energy_max_strike_applied 마커로 1회만 적용한다.
    # 별도 마커로 한 번 더 보정하던 코드는 중복 적용 원인이므로 제거.

    return stats

def is_valid_by_caps(stats: Dict[str, float]) -> bool:
    promo_cr_mult = float(stats.get("promo_crit_rate_mult", 1.0))
    promo_ap_mult = float(stats.get("promo_armor_pen_mult", 1.0))

    eff_cr = stats["crit_rate"] * promo_cr_mult
    eff_ap = stats["armor_pen"] * promo_ap_mult

    if eff_ap > 0.80 + 1e-12:
        return False
    return True

# =====================================================
# Cookie Simulator (Abyss Raid) - Crit 100% Forced Optimizers
# =====================================================
# =====================================================
# 0) 공용 유틸
# =====================================================

# =====================================================
# Helpers - 최적화 루프 보조
# =====================================================
def _clone_stats_for_loop(st: Dict[str, float]) -> Dict[str, float]:
    """
    루프에서 stats_template을 재사용할 때,
    내부 set(중복 적용 방지용)이 공유되지 않도록 안전 복사.
    """
    s = dict(st)
    if "_applied_party_buffs" in s:
        s["_applied_party_buffs"] = set(s["_applied_party_buffs"])
    if "_applied_enemy_debuffs" in s:
        s["_applied_enemy_debuffs"] = set(s["_applied_enemy_debuffs"])
    return s

def _apply_shards_inplace(stats: Dict[str, float], shards: Dict[str, int]) -> None:
    """shards 슬롯 증가분만 stats에 더한다(인플레이스)"""
    for k, slots in shards.items():
        inc = float(SHARD_INC.get(k, 0.0))
        if inc and slots:
            stats[k] = float(stats.get(k, 0.0)) + inc * int(slots)

def _resolve_equip_list_override(
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]],
    default_equips: List[str],
) -> List[str]:
    """
    equip_override가 들어오면 허용 장비 리스트를 덮어쓴다.
      - None: 기본값
      - "AUTO"/"NONE"/"": 기본값
      - "장비명" 또는 "A,B,C" 문자열
      - ["A","B"] 리스트/튜플/셋
    """
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
    """
    unique_override가 들어오면 메인 쿠키 유니크 설탕유리조각 후보를 덮어쓴다.
      - None: 기본값
      - "AUTO"/"NONE"/"": 기본값
      - "유니크명" 또는 "A,B,C" 문자열
      - ["A", "B"] 리스트/튜플/셋
    """
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

def _min_crit_slots_needed_for_crit100_generic(template: Dict[str, float]) -> Optional[int]:
    """
    치확 100%에 필요한 설탕유리조각 칸 수를 수식으로 바로 계산한다.

    기존에는 0~41칸 범위를 이진 탐색하면서 매번 dict 복사 + cap 검사를 했지만,
    현재 cap 검사는 방어 관통만 확인하므로 치확 슬롯 수와 독립적이다.
    따라서 ceil((1 - 현재 실전 치확) / 1칸 증가량)으로 한 번에 구할 수 있다.
    """
    per_slot = float(SHARD_INC.get("crit_rate", 0.0))
    cur = effective_crit_rate_raw(template)

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
