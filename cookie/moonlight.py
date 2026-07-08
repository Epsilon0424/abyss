# =====================================================
# Moonlight Cookie / 달빛술사 쿠키
# =====================================================
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Tuple, Union
import math

from .common import *
from .common import _resolve_equip_list_override, _resolve_unique_list_override, _apply_shards_inplace, _clone_stats_for_loop

MOONLIGHT_COOKIE = "달빛술사 쿠키"
MOONLIGHT_FIXED_ARTIFACT = "고요히 흐르는 월광"
MOONLIGHT_FIXED_UNIQUE = "불야성의 밤의 기억"
MOONLIGHT_DEFAULT_EQUIP = "유성우의 향연"
MOONLIGHT_DEFAULT_SEAZ = "플럼나이트:달빛의 속삭임"

MOONLIGHT_WEAPON_ATK_PCT = 0.52
MOONLIGHT_WEAPON_DEBUFF_AMP = 0.24
MOONLIGHT_SELF_MYSTIC_ELEM_ATK_ADD = 650.0
MOONLIGHT_SELF_CRIT_DMG_ADD = 0.80

# 상한 반영: 디버프 증폭은 150% 근처까지 우선 확보하고,
# 버프증폭+디버프증폭 잠재는 합산 최대 4개만 사용한다.
# 장비/유니크/시즈 조합별로 필요한 디벞 잠재 칸수를 자동 계산한다.
# - 유성우 + 불야성 기준: 디벞증 1칸
# - 시간관리국의 제복 + 불야성 기준: 디벞증 4칸
# 남는 잠재는 공격력%로 둔다.
MOONLIGHT_FIXED_POT = {
    "atk_pct": 7,
    "debuff_amp": 1,
    "elem_atk": 0,
    "buff_amp": 0,
    "crit_rate": 0,
    "crit_dmg": 0,
    "armor_pen": 0,
}

BASE_STATS_MOONLIGHT = {
    MOONLIGHT_COOKIE: {
        "atk": 617.0,
        "friendship_atk": friendship_atk_for(MOONLIGHT_COOKIE),
        "def": 419.0,
        "hp": 5153.0,
        # 환상적인 달의 초대: 본인에게만 신비 속성 공격력 +650
        "elem_atk": MOONLIGHT_SELF_MYSTIC_ELEM_ATK_ADD,
        "atk_pct": MOONLIGHT_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        # 환상적인 달의 초대: 본인에게만 치명타 피해 +80%
        "crit_dmg": 1.50 + MOONLIGHT_SELF_CRIT_DMG_ADD,
        "armor_pen": 0.0,
        "final_dmg": 0.05,
        "buff_amp": 0.0,
        # 기본 디버프 증폭 15% + 전용무기 디버프 증폭 24%
        "debuff_amp": 0.15 + MOONLIGHT_WEAPON_DEBUFF_AMP,
    }
}

# 계수는 업로드된 스크린샷 기준. 실제 사이클 타이밍이 확정되면 여기만 조정하면 됨.
MOONLIGHT_CYCLE_TIME = 30.0
MOONLIGHT_BASIC_COEFF = (1.491 * 2.0) + (1.491 * 2.0)
# [새벽녘] 기본 공격 3평 1묶음
# 1타 170.4%×4 + 2타 170.4%×4 + 3타 369.2% + 532.5%
MOONLIGHT_DAWN_BASIC3_COEFF = (1.704 * 4.0) + (1.704 * 4.0) + 3.692 + 5.325
# 이전 차징 가정값은 남겨두되 현재 사이클에서는 사용하지 않음.
MOONLIGHT_DAWN_CHARGE_COEFF = 10.508 * 9.0
MOONLIGHT_SPECIAL_COEFF = 7.952
MOONLIGHT_MOONBALL_COEFF = 1.232
MOONLIGHT_MOONBALL_HITS = 1
MOONLIGHT_ULT_INITIAL_COEFF = 9.088
MOONLIGHT_DREAMLIKE_COEFF = 9.940
MOONLIGHT_ULT_FINISH_COEFF = (4.757 * 4.0) + 30.672
MOONLIGHT_ARTIFACT_DAWN_GUIDE_COEFF = 12.0 * 3.0

MOONLIGHT_PASSIVE_FINAL_PER_DEBUFF_AMP = 0.80
MOONLIGHT_PASSIVE_FINAL_CAP = 1.20
MOONLIGHT_DAWN_CRIT_RATE_ADD = 1.00
MOONLIGHT_DAWN_DAMAGE_INC = 0.25
MOONLIGHT_DAWN_DAMAGE_DURATION = 20.0
MOONLIGHT_DAWN_DAMAGE_AVG = MOONLIGHT_DAWN_DAMAGE_INC * (MOONLIGHT_DAWN_DAMAGE_DURATION / MOONLIGHT_CYCLE_TIME)

# 30초 1사이클
# 궁(달빛 환대) → 특 → 2평 → 2평 → 궁(꿈만 같은 시간) → 궁(새벽녘)
# → 특 → 3평 → 3평 → 3평 → 3평 → 특 → 3평 → 3평 → 특 → 새벽녘 종료 → 2평 → 2평
# - 달무리 실제 타수: 1회
# - 꿈만 같은 시간: 1회
# - 새벽녘 상태 피해 +25%는 20초/30초 평균값으로 본인에게만 적용
MOONLIGHT_CYCLE_TOKENS = [
    "U_RECEPTION", "S", "MOONBALL", "B", "B",
    "U_DREAM", "U_DAWN_START", "S_IN_DAWN",
    "DAWN_BASIC3", "DAWN_BASIC3", "DAWN_BASIC3", "DAWN_BASIC3",
    "S_IN_DAWN", "DAWN_BASIC3", "DAWN_BASIC3", "S_IN_DAWN",
    "DAWN_GUIDE", "U_DAWN_FINISH", "B", "B",
]


def moonlight_allowed_equips() -> List[str]:
    # 달빛술사 장비 후보: 유성우/시간셋을 사용한다.
    # 시간관리국의 제복은 불야성 + 플럼나이트 기준 디버프 증폭 잠재 4칸으로 150% 근처까지 도달한다.
    # 기본값은 유성우의 향연이다.
    return [x for x in ["유성우의 향연", "시간관리국의 제복"] if x in EQUIP_SETS]


def moonlight_allowed_seaz() -> List[str]:
    # 달빛술사는 플럼나이트 계열만 표시한다.
    return [x for x in SEAZNITES.keys() if str(x).startswith("플럼나이트:")]


def moonlight_allowed_uniques() -> List[str]:
    # 기본은 불야성의 밤의 기억을 사용한다.
    opts = ["불야성의 밤의 기억", "체리맛 쿠키의 기억", "크러쉬드페퍼맛 쿠키의 기억", "칠리맛 쿠키의 기억"]
    return [x for x in opts if x in UNIQUE_SHARDS]


@lru_cache(maxsize=None)
def moonlight_generate_shard_candidates(step: int = 1) -> List[Dict[str, int]]:
    """달빛술사 일반 설탕유리조각 후보.

    사용자 요청에 맞춰 서포터형(축복/낙인)이 아니라 딜러형 스탯 축으로 탐색한다.
    정확도를 위해 1칸 단위까지 후보를 만든다.
    """
    step = max(1, int(step or 1))
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    seen = set()
    axes = ["crit_dmg", "all_elem_dmg", "atk_pct", "basic_dmg", "special_dmg", "ult_dmg"]

    def rec(idx: int, used: int, cur: Dict[str, int]) -> None:
        if idx >= len(axes):
            if used > NORMAL_SLOTS:
                return
            sh = {
                "crit_rate": 0,
                "crit_dmg": int(cur.get("crit_dmg", 0)),
                "all_elem_dmg": int(cur.get("all_elem_dmg", 0)),
                "atk_pct": int(cur.get("atk_pct", 0)),
                "basic_dmg": int(cur.get("basic_dmg", 0)),
                "special_dmg": int(cur.get("special_dmg", 0)),
                "ult_dmg": int(cur.get("ult_dmg", 0)),
                "passive_dmg": 0,
                "elem_atk": NORMAL_SLOTS - used,
            }
            key = tuple(sorted(sh.items()))
            if key not in seen:
                seen.add(key)
                out.append(sh)
            return

        k = axes[idx]
        for v in steps:
            if used + v > NORMAL_SLOTS:
                continue
            cur[k] = int(v)
            rec(idx + 1, used + v, cur)
        cur.pop(k, None)

    rec(0, 0, {})
    return out


def moonlight_cycle_total_time() -> float:
    return MOONLIGHT_CYCLE_TIME


def moonlight_calc_support_metrics(stats: Dict[str, float]) -> Dict[str, float]:
    da = float(stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)))
    ba = float(stats.get("buff_amp_total", stats.get("buff_amp", 0.0)))
    return {
        "total_time": MOONLIGHT_CYCLE_TIME,
        "final_atk": calc_attack_value(stats, floor_result=False),
        "debuff_amp_total": da,
        "buff_amp_total": ba,
        # 선잠 방어력 감소는 달빛술사 본인 디버프증폭을 적용한다.
        # 한밤의 자장가 공격력 +30%는 아티팩트 공증으로 보고 버프증폭을 적용하지 않는다.
        "def_reduction_raw": 0.28 * (1.0 + da),
        "party_final_dmg": 0.25,
        "artifact_all_elem": 0.50,
        "artifact_crit_dmg": 0.50,
        "artifact_atk_buff": 0.30,
    }


def _moonlight_apply_passive(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    # [아름다운 밤의 산책]은 달빛술사 본인의 디버프 증폭량만 사용한다.
    da_total = float(st.get("self_debuff_amp_total", st.get("debuff_amp_total", st.get("debuff_amp", 0.0))))
    add_final = min(MOONLIGHT_PASSIVE_FINAL_CAP, MOONLIGHT_PASSIVE_FINAL_PER_DEBUFF_AMP * da_total)
    st["final_dmg"] = float(st.get("final_dmg", 0.0)) + add_final
    return st


def _moonlight_has_res_down_for_dawn(stats: Dict[str, float]) -> bool:
    """[결코 잊지 못할 꿈] 조건 체크.

    현재 시뮬의 속성 내성 감소 축은 대부분 모든 속성/현재 속성 내성 감소를
    elem_res_reduction_*에 합산한다. 추후 신비 전용 키가 들어와도 잡히도록
    mystic/all 계열 키도 함께 확인한다.
    """
    keys = (
        "elem_res_reduction_raw",
        "elem_res_reduction_no_scale_raw",
        "all_elem_res_reduction_raw",
        "all_elem_res_reduction_no_scale_raw",
        "mystic_elem_res_reduction_raw",
        "mystic_elem_res_reduction_no_scale_raw",
        "mystic_res_reduction_raw",
        "mystic_res_reduction_no_scale_raw",
    )
    return any(float(stats.get(k, 0.0) or 0.0) > 0.0 for k in keys)


def _moonlight_apply_dawn_avg_bonus(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    if _moonlight_has_res_down_for_dawn(st):
        # [새벽녘] 상태에서 신비/모든 속성 내성 감소가 걸린 적에게 가하는 피해 +25%.
        # 실제 유지 시간은 30초 중 약 20초로 보고 평균값(+16.6667%)을 달빛술사 본인 딜에만 반영.
        st["final_dmg"] = float(st.get("final_dmg", 0.0)) + MOONLIGHT_DAWN_DAMAGE_AVG
        st["moonlight_dawn_avg_final_dmg"] = float(st.get("moonlight_dawn_avg_final_dmg", 0.0)) + MOONLIGHT_DAWN_DAMAGE_AVG
    return st


def _moonlight_dawn_stats(stats: Dict[str, float]) -> Dict[str, float]:
    st = dict(stats)
    st["buff_crit_rate_raw"] = float(st.get("buff_crit_rate_raw", 0.0)) + MOONLIGHT_DAWN_CRIT_RATE_ADD
    return st


def moonlight_cycle_damage(stats: Dict[str, float], party: List[str], artifact_name: str = MOONLIGHT_FIXED_ARTIFACT) -> Dict[str, float]:
    total_time = moonlight_cycle_total_time()
    base_stats = _moonlight_apply_dawn_avg_bonus(_moonlight_apply_passive(stats))
    dawn_stats = _moonlight_dawn_stats(base_stats)

    direct = 0.0
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "charge": 0.0,
        "dash": 0.0,
        "passive": 0.0,
        "strike": 0.0,
        "unique": 0.0,
        "proc": 0.0,
    }

    for tok in MOONLIGHT_CYCLE_TOKENS:
        if tok == "B":
            # 2평 1묶음: 1타 149.1%×2 + 2타 149.1%×2
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_BASIC_COEFF, "basic")
            direct += dmg
            breakdown["basic"] += dmg
        elif tok == "S":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_SPECIAL_COEFF, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "S_IN_DAWN":
            # 새벽녘 중 특수스킬은 새벽녘 상태의 치명타 확률 +100%를 적용한다.
            # 새벽녘 차징 피해와 별개로 일반 특수스킬 1회로 계산한다.
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_SPECIAL_COEFF, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "MOONBALL":
            # 달무리는 실제 적중 1회만 반영
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_MOONBALL_COEFF * MOONLIGHT_MOONBALL_HITS, "special")
            direct += dmg
            breakdown["special"] += dmg
        elif tok == "U_RECEPTION":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_ULT_INITIAL_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "U_DREAM":
            dmg = skill_damage_from_start(base_stats, MOONLIGHT_DREAMLIKE_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "U_DAWN_START":
            # 새벽녘 진입 자체는 변신/상태 진입으로 보고 직접 피해 없음
            continue
        elif tok == "DAWN_BASIC3":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_DAWN_BASIC3_COEFF, "basic")
            direct += dmg
            breakdown["basic"] += dmg
        elif tok == "DAWN_CHARGE":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_DAWN_CHARGE_COEFF, "basic")
            direct += dmg
            breakdown["charge"] += dmg
        elif tok == "REST5":
            continue
        elif tok == "U_DAWN_FINISH":
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_ULT_FINISH_COEFF, "ult")
            direct += dmg
            breakdown["ult"] += dmg
        elif tok == "DAWN_GUIDE" and artifact_name == MOONLIGHT_FIXED_ARTIFACT:
            # 고요히 흐르는 월광: 공격력 1200% × 3, 수치 그대로 3타
            dmg = skill_damage_from_start(dawn_stats, MOONLIGHT_ARTIFACT_DAWN_GUIDE_COEFF, "special")
            direct += dmg
            breakdown["proc"] += dmg

    strike = strike_total_from_direct(direct, MOONLIGHT_COOKIE, stats, party)
    unique_extra = skill_damage_from_start(base_stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    sugar_proc = float(stats.get("sugar_brilliance_coeff", 0.0))
    sugar_damage = skill_damage_from_start(base_stats, sugar_proc, "none") if sugar_proc > 0 else 0.0

    breakdown["strike"] = strike
    breakdown["unique"] = unique_extra + sugar_damage
    total_damage = math.floor(direct + strike + unique_extra + sugar_damage)

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": total_damage / total_time if total_time > 0 else 0.0,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_dash": breakdown["dash"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }


def optimize_moonlight_cycle(
    seaz_name: Optional[str] = None,
    party: Optional[List[str]] = None,
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
) -> Optional[dict]:
    cookie = MOONLIGHT_COOKIE
    party = list(party or ["윈드파라거스 쿠키"])
    base = BASE_STATS_MOONLIGHT[cookie].copy()
    artifact_name = MOONLIGHT_FIXED_ARTIFACT

    equips = _resolve_equip_list_override(equip_override, moonlight_allowed_equips() or [MOONLIGHT_DEFAULT_EQUIP])
    uniques = _resolve_unique_list_override(unique_override, moonlight_allowed_uniques() or [MOONLIGHT_FIXED_UNIQUE])

    if not seaz_name:
        opts = moonlight_allowed_seaz()
        seaz_name = MOONLIGHT_DEFAULT_SEAZ if MOONLIGHT_DEFAULT_SEAZ in opts else (opts[0] if opts else MOONLIGHT_DEFAULT_SEAZ)

    shard_candidates = moonlight_generate_shard_candidates(step=step)
    total = max(1, len(equips) * len(uniques) * len(shard_candidates))
    tick = max(1, total // 150)
    done = 0

    def emit(p: float) -> None:
        if progress_cb:
            try:
                progress_cb(p)
            except Exception:
                pass

    emit(0.01)
    best: Optional[dict] = None
    zero_shards = {k: 0 for k in SHARD_INC.keys()}

    for equip_name in equips:
        for unique_name in uniques:
            pot = moonlight_auto_potentials_for_combo(
                equip_name=equip_name,
                seaz_name=seaz_name,
                unique_name=unique_name,
            )
            template = build_stats_for_combo(
                cookie_name_kr=cookie,
                base=base,
                shards=zero_shards,
                potentials=pot,
                equip_name=equip_name,
                seaz_name=seaz_name,
                unique_name=unique_name,
                party=party,
                artifact_name=artifact_name,
                party_seaz=party_seaz,
                party_uniques=party_uniques,
                party_sets=party_sets,
            )
            template["base_hp"] = float(base.get("hp", 0.0))
            template["base_def"] = float(base.get("def", 0.0))

            if not is_valid_by_caps(template):
                done += len(shard_candidates)
                continue

            for sh in shard_candidates:
                done += 1
                if (done % tick) == 0:
                    emit(done / total)

                stats = _clone_stats_for_loop(template)
                _apply_shards_inplace(stats, sh)
                if "_damage_context_cache" in stats:
                    stats.pop("_damage_context_cache", None)

                cycle = moonlight_cycle_damage(stats, party, artifact_name)
                support = moonlight_calc_support_metrics(stats)
                cur = {
                    "cookie": cookie,
                    "dps": float(cycle["dps"]),
                    "cycle_total_damage": float(cycle["total_damage"]),
                    "cycle_total_time": total_time if (total_time := float(cycle.get("total_time", MOONLIGHT_CYCLE_TIME))) else MOONLIGHT_CYCLE_TIME,
                    "cycle_breakdown": cycle,
                    "max_shield": 0.0,
                    "max_heal": 0.0,
                    "hps": 0.0,
                    "support_detail": support,
                    "equip": equip_name,
                    "seaz": seaz_name,
                    "unique": unique_name,
                    "artifact": artifact_name,
                    "potentials": dict(pot),
                    "shards": dict(sh),
                    "party": party,
                    "party_seaz": dict(party_seaz or {}),
                    "party_sets": dict(party_sets or {}),
                    "party_uniques": dict(party_uniques or {}),
                    "stats": stats,
                    "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
                    "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
                }

                if best is None or cur["dps"] > float(best.get("dps", 0.0)):
                    best = cur

    emit(1.0)
    return best
