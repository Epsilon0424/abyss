# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 마블베리맛 쿠키
# - 스트라이커 / 타격형 / 어둠속성
# - 룽샤와 같은 스트라이커 구조 기반
# =====================================================

# =====================================================
# Constants
# =====================================================
MARBLE_BERRY_FORCE_CRIT_100 = True
MARBLE_BERRY_WEAPON_ATK_PCT = 0.52
MARBLE_BERRY_WEAPON_FINAL_DMG = 0.30

MARBLE_BERRY_FIXED_SEAZ = "리치코랄:빛나는 은하수"
MARBLE_BERRY_FIXED_ARTIFACT = "충전은 타이밍"
MARBLE_BERRY_FIXED_UNIQUE = "룽샤맛 쿠키의 기억"

BASE_STATS_MARBLE_BERRY = {
    "마블베리맛 쿠키": {
        "atk": 684.0,
        "friendship_atk": friendship_atk_for("마블베리맛 쿠키"),
        "def": 573.0,
        "hp": 5523.0,
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": MARBLE_BERRY_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + MARBLE_BERRY_WEAPON_FINAL_DMG,
    }
}

# 3평 = 113.6% + 129.2% + 237.1%
MARBLE_BERRY_BASIC3_COEFF = 1.136 + 1.292 + 2.371  # 기본공격 3타 합산 계수
MARBLE_BERRY_CHARGE_COEFF = 5.112  # 차지 공격 피해 계수
MARBLE_BERRY_SPECIAL_COEFF = 14.257  # 특수스킬 [펄스 캐논] 피해 계수
MARBLE_BERRY_ULT_COEFF = 35.50  # 궁극기 [익스플로전] 피해 계수

# 승급
MARBLE_BERRY_PROMO_SKILL_DMG_ADD = 0.25  # 승급 펄스 캐논/익스플로전 피해 증가
MARBLE_BERRY_PROMO_CRASH_STRENGTHEN = 1.15
MARBLE_BERRY_CRASH_COOKIE_TAKEN = 0.28 * MARBLE_BERRY_PROMO_CRASH_STRENGTHEN
MARBLE_BERRY_CRASH_DARK_TAKEN = 0.10
MARBLE_BERRY_SPECIAL_BASIC_BOOST = 0.25
MARBLE_BERRY_SPECIAL_BASIC_BOOST_COMBOS = 2  # 펄스캐논 후 6히트 ≒ 3평 2회

# 아티팩트 '충전은 타이밍'
MARBLE_BERRY_ARTIFACT_BASE_ATK_PCT = 0.35
MARBLE_BERRY_ENERGY_MAX_ATK_PCT = 0.30
MARBLE_BERRY_ENERGY_MAX_STRIKE_DMG = 0.25  # 아티팩트 [충전은 타이밍] 에너지 맥스 속성강타 피해 증가

MARBLE_BERRY_CYCLE_TOKENS = [
    "S", "C", "U", "B3", "B3", "C", "B3", "B3", "B3", "C",
    "S", "B3", "B3", "C", "B3", "B3", "B3", "C", "B3", "B3",
    "S", "C", "B3", "B3",
]

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def marble_berry_allowed_equips() -> List[str]:
    # 받피증 기반 스트라이커라 기본은 유성우 고정
    return ["유성우의 향연", "황금 예복"]

def marble_berry_allowed_uniques() -> List[str]:
    return [MARBLE_BERRY_FIXED_UNIQUE, "마라맛 쿠키의 기억", "칠리맛 쿠키의 기억"]

def marble_berry_allowed_artifacts() -> List[str]:
    return [MARBLE_BERRY_FIXED_ARTIFACT]

def marble_berry_allowed_seaz() -> List[str]:
    return [MARBLE_BERRY_FIXED_SEAZ]

def marble_berry_allowed_potentials() -> List[Dict[str, int]]:
    out: List[Dict[str, int]] = []
    remain = 4
    for atk_pct in range(remain + 1):
        for crit_dmg in range(remain - atk_pct + 1):
            armor_pen = remain - atk_pct - crit_dmg
            out.append({
                "debuff_amp": 0,
                "crit_rate": 2,
                "atk_pct": atk_pct,
                "elem_atk": 2,
                "crit_dmg": crit_dmg,
                "armor_pen": armor_pen,
                "buff_amp": 0,
            })
    return out

@lru_cache(maxsize=None)
def marble_berry_generate_shard_candidates_no_cr(step: int = 2) -> List[Dict[str, int]]:
    step = max(1, int(step or 1))
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct"]
    out: List[Dict[str, int]] = []

    def dfs(idx: int, remain: int, cur: Dict[str, int]) -> None:
        if idx == len(keys):
            out.append({k: int(cur.get(k, 0)) for k in keys})
            return
        k = keys[idx]
        for x in range(0, remain + 1, step):
            cur[k] = x
            dfs(idx + 1, remain - x, cur)
        cur.pop(k, None)

    dfs(0, NORMAL_SLOTS, {})
    return out

# =====================================================
# Helpers - 고정 효과 반영
# =====================================================
def _apply_marble_berry_fixed_effects(stats: Dict[str, float], artifact_name: str) -> Dict[str, float]:
    s = dict(stats)
    if s.get("_marble_berry_fixed_effects_applied"):
        return s
    s["_marble_berry_fixed_effects_applied"] = 1.0

    # 크래시: 쿠키 받피증 + 승급 어둠 받피증, 디버프 증폭 미적용
    s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + MARBLE_BERRY_CRASH_COOKIE_TAKEN
    if COOKIE_ELEMENT.get("마블베리맛 쿠키", "") == "dark":
        s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + MARBLE_BERRY_CRASH_DARK_TAKEN

    # 승급: 펄스 캐논/익스플로전 피해 +25%
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + MARBLE_BERRY_PROMO_SKILL_DMG_ADD
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + MARBLE_BERRY_PROMO_SKILL_DMG_ADD

    # 아티팩트 고유: 에너지 맥스 상시 유지 가정
    if artifact_name == MARBLE_BERRY_FIXED_ARTIFACT:
        s["atk_pct"] = float(s.get("atk_pct", 0.0)) + MARBLE_BERRY_ARTIFACT_BASE_ATK_PCT
        s["atk_pct"] = float(s.get("atk_pct", 0.0)) + MARBLE_BERRY_ENERGY_MAX_ATK_PCT
        s["element_strike_dmg"] = float(s.get("element_strike_dmg", 0.0)) + MARBLE_BERRY_ENERGY_MAX_STRIKE_DMG

    return s

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def marble_berry_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_marble_berry_fixed_effects(stats, artifact_name)

    total_time = 30.0
    # 스킬별 처음부터 계산: skill_damage_from_start 사용

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0
    boosted_b3_left = 0
    for tok in MARBLE_BERRY_CYCLE_TOKENS:
        if tok == "B3":
            boost = 1.0 + MARBLE_BERRY_SPECIAL_BASIC_BOOST if boosted_b3_left > 0 else 1.0
            dmg = skill_damage_from_start(stats, MARBLE_BERRY_BASIC3_COEFF, "basic", extra_skill_mult=boost)
            if boosted_b3_left > 0:
                boosted_b3_left -= 1
            breakdown["basic"] += dmg
        elif tok == "C":
            dmg = skill_damage_from_start(stats, MARBLE_BERRY_CHARGE_COEFF, "basic")
            breakdown["basic"] += dmg
        elif tok == "S":
            dmg = skill_damage_from_start(stats, MARBLE_BERRY_SPECIAL_COEFF, "special")
            breakdown["special"] += dmg
            boosted_b3_left = max(boosted_b3_left, MARBLE_BERRY_SPECIAL_BASIC_BOOST_COMBOS)
        else:
            dmg = skill_damage_from_start(stats, MARBLE_BERRY_ULT_COEFF, "ult")
            breakdown["ult"] += dmg
        total_direct += dmg

    strike = strike_total_from_direct(total_direct, "마블베리맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)


    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for k in breakdown:
            breakdown[k] *= elem_dmg_mult

    dps = total_damage / total_time
    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_marble_berry_cycle(
    seaz_name: str,
    party: List[str],
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
) -> Optional[dict]:
    cookie = "마블베리맛 쿠키"
    base = BASE_STATS_MARBLE_BERRY[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, marble_berry_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, marble_berry_allowed_uniques())
    potentials = marble_berry_allowed_potentials()
    artifacts = marble_berry_allowed_artifacts()
    shard_candidates = marble_berry_generate_shard_candidates_no_cr(step=max(1, int(step or 1)))

    shard_adds_list: List[Tuple[Dict[str, int], List[Tuple[str, float]], int]] = []
    for sh in shard_candidates:
        adds: List[Tuple[str, float]] = []
        used = 0
        for k, slots in sh.items():
            slots_i = int(slots)
            used += slots_i
            inc = float(SHARD_INC.get(k, 0.0))
            if inc and slots_i:
                adds.append((k, inc * slots_i))
        shard_adds_list.append((sh, adds, used))

    zero_shards = {k: 0 for k in SHARD_INC.keys()}
    total = max(1, len(equips) * len(artifacts) * len(uniques) * len(potentials) * len(shard_candidates))
    done = 0
    tick = max(1, total // 150)

    def emit(p: float) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(p)
        except Exception:
            # 진행률 콜백 오류는 최적화 계산 결과에 영향이 없으므로 무시한다.
            pass

    emit(0.0)
    best: Optional[dict] = None
    cr_inc = float(SHARD_INC.get("crit_rate", 0.0))
    ea_inc = float(SHARD_INC.get("elem_atk", 0.0))

    for equip in equips:
        for artifact_name in artifacts:
            for unique_name in uniques:
                for pot in potentials:
                    template = build_stats_for_combo(
                        cookie_name_kr=cookie,
                        base=base,
                        shards=zero_shards,
                        potentials=pot,
                        equip_name=equip,
                        seaz_name=seaz_name,
                        unique_name=unique_name,
                        party=party,
                        artifact_name=artifact_name,
                        party_seaz=party_seaz,
                        party_uniques=party_uniques,
                        party_sets=party_sets,
                    )
                    template = _apply_marble_berry_fixed_effects(template, artifact_name)

                    if not is_valid_by_caps(template):
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    req_cr_slots_opt = _min_crit_slots_needed_for_crit100_generic(template)
                    if req_cr_slots_opt is None:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue
                    req_cr_slots = int(req_cr_slots_opt)

                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)

                    remain_slots = NORMAL_SLOTS - req_cr_slots
                    if remain_slots < 0:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    for sh_base, adds, used in shard_adds_list:
                        done += 1
                        if (done % tick) == 0:
                            emit(done / total)
                        if used > remain_slots:
                            continue

                        ea_slots = remain_slots - used
                        stats = template.copy()
                        stats.pop("_damage_context_cache", None)
                        for k, dv in adds:
                            stats[k] = float(stats.get(k, 0.0)) + dv
                        if req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        cycle = marble_berry_cycle_damage_fast(stats, party, artifact_name)
                        dps = cycle["dps"]
                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)
                            for k in ("basic_dmg", "special_dmg", "ult_dmg", "passive_dmg", "def_pct", "shield_pct", "heal_pct"):
                                shards_out.setdefault(k, 0)
                            best = {
                                "cookie": cookie,
                                "dps": dps,
                                "cycle_total_damage": cycle["total_damage"],
                                "cycle_total_time": 30.0,
                                "cycle_breakdown": cycle,
                                "equip": equip,
                                "seaz": seaz_name,
                                "unique": unique_name,
                                "artifact": artifact_name,
                                "shards": shards_out,
                                "potentials": pot,
                                "party": party,
                                "party_seaz": dict(party_seaz or {}),
                                "party_sets": dict(party_sets or {}),
                                "party_uniques": dict(party_uniques or {}),
                                "stats": stats,
                                "buff_amp_total": stats.get("buff_amp_total", stats.get("buff_amp", 0.0)),
                                "debuff_amp_total": stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0)),
                            }

    emit(1.0)
    return best
