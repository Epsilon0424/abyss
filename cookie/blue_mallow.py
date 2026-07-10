# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 블루멜로우 쿠키
# - 데미지 딜러 / 마법형 / 어둠속성
# - 승급 효과 공격력 +30%는 흑보리처럼 실제 공격력에서 분리해서
#   base atk를 1.3으로 나누고 atk_pct +30%로 반영한다.
# =====================================================

BLUE_MALLOW_FORCE_CRIT_100 = True
BLUE_MALLOW_WEAPON_ATK_PCT = 0.52
BLUE_MALLOW_WEAPON_FINAL_DMG = 0.30
BLUE_MALLOW_FIXED_ARTIFACT = "오늘도 완벽!"
BLUE_MALLOW_DEFAULT_SEAZ = "바닐라몬드:치열한 선봉자"
BLUE_MALLOW_FIXED_UNIQUE = "피닉스페퍼 쿠키의 기억"

# 사용자가 알려준 실제 공격력: 889 + 57 = 946
# 승급 공격력 +30%를 역산해서 기본 공격력으로 분리한다.
BASE_STATS_BLUE_MALLOW = {
    "블루멜로우맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(889.0, 0.30),
        "friendship_atk": friendship_atk_for("블루멜로우맛 쿠키"),
        "def": 339.0 + 27.0,
        "hp": 4131.0 + 345.0,
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + BLUE_MALLOW_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.60,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + BLUE_MALLOW_WEAPON_FINAL_DMG,
    }
}

# 기본공격 피해 : 85.2%
# 패시브 [노블레스 오블리주] 추가 피해: 426%
# 차지 [퍼펙트 티 파티]는 기본공격과 별도 수치로 계산한다.
BLUE_MALLOW_BASIC_COEFF = 0.852  # 기본공격 1타/2타/3타 개별 피해 계수
BLUE_MALLOW_BASIC1_COEFF = BLUE_MALLOW_BASIC_COEFF  # 기본공격 1타 계수
BLUE_MALLOW_BASIC2_COEFF = BLUE_MALLOW_BASIC_COEFF  # 기본공격 2타 계수
BLUE_MALLOW_BASIC3_COEFF = BLUE_MALLOW_BASIC_COEFF  # 기본공격 3타 계수
BLUE_MALLOW_NOBLESSE_COEFF = 4.26  # 패시브 [노블레스 오블리주] 추가 피해 계수

# 차지 단계 피해
# 1단계 [얼리 모닝 티]: 160.5% × 3
# 2단계 [일레븐지스]: 213% × 5
# 3단계 [애프터눈 티]: 319.5% × 8
# 4단계 [애프터 디너 티]: 71% × 15 + 2130%
BLUE_MALLOW_CHARGE1_COEFF = 1.605 * 3.0  # [퍼펙트 티 파티] 1단계 [얼리 모닝 티] 계수
BLUE_MALLOW_CHARGE2_COEFF = 2.13  * 5.0  # [퍼펙트 티 파티] 2단계 [일레븐지스] 계수
BLUE_MALLOW_CHARGE3_COEFF = 3.195 * 8.0  # [퍼펙트 티 파티] 3단계 [애프터눈 티] 계수
BLUE_MALLOW_CHARGE4_COEFF = (0.710 * 15.0) + 21.30  # [퍼펙트 티 파티] 4단계 [애프터 디너 티] 계수

# [왕관의 무게]
# [퍼펙트 티 파티] 차지 단계에 따라 [노블레스 오블리주] 추가 피해 0/10/20/30% 증가.
# 3차징 이후 기본공격: 426% × 1.20
# 4차징 이후 기본공격: 426% × 1.30
BLUE_MALLOW_CROWN_NOBLESSE_BONUS = {
    0: 0.00,
    1: 0.10,
    2: 0.20,
    3: 0.20,
    4: 0.30,
}

# 특수스킬은 보호막 스킬이라 피해 계산에서는 제외한다.
# 사이클(30초): 궁 → 4차징 → 특 → 2평(426%+30%) →
# 4차징 → 3평(426%+30%) → 3차징 → 3평(426%+20%) →
# 특 → 3차징 → 평(426%+20%) → 3차징
BLUE_MALLOW_CYCLE_TIME = 30.0
BLUE_MALLOW_ULT_C3_COEFF = BLUE_MALLOW_CHARGE3_COEFF  # 궁극기 사이클에서 사용하는 3차징 피해 계수
BLUE_MALLOW_ULT_C4_COEFF = BLUE_MALLOW_CHARGE4_COEFF  # 궁극기 사이클에서 사용하는 4차징 피해 계수
BLUE_MALLOW_ULT_COEFF = BLUE_MALLOW_CHARGE4_COEFF  # 기본 궁극기 대표 계수(4차징 기준)
BLUE_MALLOW_CYCLE_TOKENS = [
    "C4",
    "B1", "B2", "B3", "B4",
    "C4",
    "B1", "B2", "B3",
    "C3",
    "B1", "B2", "B3",
    "C3",
    "B1", "B2", "B3",
    "C3",
]

# =====================================================
# Candidate helpers
# =====================================================
def blue_mallow_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def blue_mallow_allowed_uniques() -> List[str]:
    return [BLUE_MALLOW_FIXED_UNIQUE, "꺼지지 않는 봉화의 기억", "칠리맛 쿠키의 기억"]

def blue_mallow_allowed_artifacts() -> List[str]:
    return [BLUE_MALLOW_FIXED_ARTIFACT]

def blue_mallow_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("바닐라몬드:")]

@lru_cache(maxsize=None)
def blue_mallow_generate_potentials_common() -> List[Dict[str, int]]:
    total = 8
    fixed_elem = 2
    free = total - fixed_elem
    keys = ["atk_pct", "crit_dmg", "armor_pen"]
    cap = {"armor_pen": min(4, free)}
    out: List[Dict[str, int]] = []

    def dfs(i: int, remain: int, cur: Dict[str, int]) -> None:
        if i == len(keys):
            if remain == 0:
                p = dict(cur)
                p["elem_atk"] = fixed_elem
                p["buff_amp"] = 0
                p["debuff_amp"] = 0
                p["crit_rate"] = 0
                out.append(p)
            return
        k = keys[i]
        lim = min(remain, cap.get(k, remain))
        for x in range(lim + 1):
            cur[k] = x
            dfs(i + 1, remain - x, cur)
        cur.pop(k, None)

    dfs(0, free, {})
    return out

@lru_cache(maxsize=None)
def blue_mallow_generate_shard_candidates_no_cr(step: int = 1) -> List[Dict[str, int]]:
    step = max(1, int(step or 1))
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct", "passive_dmg"]
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
# Calculation
# =====================================================
def blue_mallow_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "passive": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0

    artifact_meta = ARTIFACTS.get(artifact_name, {}) or {}
    blue_meta = artifact_meta.get("blue_mallow", {}) or {}
    noble_extra = 1.0 + float(blue_meta.get("noblesse_extra_dmg", 0.0))
    perfectionist_extra = 1.0 + float(blue_meta.get("perfectionist_passive_dmg", 0.0))

    # 차지 공격 이후 완벽주의자가 생기는 구조라 첫 기본공격 이후 패시브 피해부터 적용한다.
    # 왕관의 무게는 마지막 차지 단계에 따라 이후 노블레스 오블리주 추가 피해에 더한다.
    perfectionist_on = False
    crown_noblesse_bonus = 0.0

    def noblesse_mult() -> float:
        return noble_extra * (1.0 + crown_noblesse_bonus) * (perfectionist_extra if perfectionist_on else 1.0)

    for tok in BLUE_MALLOW_CYCLE_TOKENS:
        if tok == "B1":
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_BASIC1_COEFF, "basic")
            breakdown["basic"] += dmg
            pdmg = skill_damage_from_start(stats, BLUE_MALLOW_NOBLESSE_COEFF, "passive", extra_skill_mult=noblesse_mult())
            breakdown["passive"] += pdmg
            dmg += pdmg
            perfectionist_on = True
        elif tok == "B2":
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_BASIC2_COEFF, "basic")
            breakdown["basic"] += dmg
            pdmg = skill_damage_from_start(stats, BLUE_MALLOW_NOBLESSE_COEFF, "passive", extra_skill_mult=noblesse_mult())
            breakdown["passive"] += pdmg
            dmg += pdmg
        elif tok == "B3":
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_BASIC3_COEFF, "basic")
            breakdown["basic"] += dmg
            pdmg = skill_damage_from_start(stats, BLUE_MALLOW_NOBLESSE_COEFF, "passive", extra_skill_mult=noblesse_mult())
            breakdown["passive"] += pdmg
            dmg += pdmg
        elif tok == "C3":
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_ULT_C3_COEFF, "ult")
            breakdown["ult"] += dmg
            # 3차징 이후 노블레스 오블리주: 426% × 1.20
            crown_noblesse_bonus = BLUE_MALLOW_CROWN_NOBLESSE_BONUS[3]
        elif tok == "C4":
            dmg = skill_damage_from_start(stats, BLUE_MALLOW_ULT_C4_COEFF, "ult")
            breakdown["ult"] += dmg
            # 4차징 이후 노블레스 오블리주: 426% × 1.30
            crown_noblesse_bonus = BLUE_MALLOW_CROWN_NOBLESSE_BONUS[4]
        elif tok == "S":
            # 티 브레이크는 보호막 스킬이라 직접 피해는 없다.
            dmg = 0.0
            breakdown["special"] += dmg
        else:
            dmg = 0.0
        total_direct += dmg

    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * 1
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "블루멜로우맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * BLUE_MALLOW_CYCLE_TIME
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)

    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for k in breakdown:
            breakdown[k] *= elem_dmg_mult

    dps = total_damage / BLUE_MALLOW_CYCLE_TIME
    return {
        "total_damage": total_damage,
        "total_time": BLUE_MALLOW_CYCLE_TIME,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

def optimize_blue_mallow_cycle(
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
    cookie = "블루멜로우맛 쿠키"
    base = BASE_STATS_BLUE_MALLOW[cookie].copy()
    fast_step = max(1, int(step or 1))

    equips = _resolve_equip_list_override(equip_override, blue_mallow_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, blue_mallow_allowed_uniques())
    potentials = blue_mallow_generate_potentials_common()
    artifacts = blue_mallow_allowed_artifacts()
    shard_candidates = blue_mallow_generate_shard_candidates_no_cr(step=fast_step)

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
            pass

    emit(0.0)
    best: Optional[dict] = None
    eps = 1e-12
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
                    if not is_valid_by_caps(template):
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

                    if BLUE_MALLOW_FORCE_CRIT_100:
                        promo = float(template.get("promo_crit_rate_mult", 1.0))
                        buff_cr = float(template.get("buff_crit_rate_raw", 0.0))
                        base_cr = float(template.get("crit_rate", 0.0))
                        eff_cr = base_cr * promo + buff_cr
                        if eff_cr > 1.0 + eps:
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
                    else:
                        req_cr_slots = 0

                    template.pop("_applied_party_buffs", None)
                    template.pop("_applied_enemy_debuffs", None)
                    template.pop("_damage_context_cache", None)

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
                        if BLUE_MALLOW_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        cycle = blue_mallow_cycle_damage_fast(stats, party, artifact_name)
                        dps = cycle["dps"]
                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)
                            shards_out["special_dmg"] = 0
                            shards_out["def_pct"] = 0
                            shards_out["shield_pct"] = 0
                            shards_out["heal_pct"] = 0
                            best = {
                                "cookie": cookie,
                                "dps": dps,
                                "cycle_total_damage": cycle["total_damage"],
                                "cycle_total_time": BLUE_MALLOW_CYCLE_TIME,
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
