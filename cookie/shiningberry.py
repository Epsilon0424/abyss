# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 샤이닝베리맛 쿠키: (4평+대시) x 8 → 특 → 궁차징 → (4평+대시) x 2 사이클
# =====================================================

# =====================================================
# Constants
# =====================================================
SHINING_BERRY_PROMO_ENABLED = True
SHINING_BERRY_FORCE_CRIT_100 = True
SHINING_BERRY_WEAPON_ATK_PCT = 0.52
SHINING_BERRY_WEAPON_FINAL_DMG = 0.30

SHINING_BERRY_PROMO_CRIT_RATE_MULT   = 1.0
SHINING_BERRY_PROMO_SPECIAL_DMG_MULT = 1.20
SHINING_BERRY_PROMO_ULT_DMG_MULT     = 1.20
SHINING_BERRY_PROMO_SPEAR_DMG_MULT   = 2.00
SHINING_BERRY_PROMO_ULT_HOLD_MULT    = 1.50
SHINING_BERRY_PROMO_POST_ULT_BASIC_DMG_MULT = 1.35

# 공격력 표기: 921 + 호감도 60
# 승급 공격력 +30%는 호감도 제외 기본공격력(921)에만 역산한다.
BASE_STATS_SHINING_BERRY = {
    "샤이닝베리맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(921.0, 0.30),
        "friendship_atk": friendship_atk_for("샤이닝베리맛 쿠키"),
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + SHINING_BERRY_WEAPON_ATK_PCT,
        "crit_rate": 0.25,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + SHINING_BERRY_WEAPON_FINAL_DMG,
    }
}

SHINING_BASIC_COEFF = 1.704 + 1.704 + 2.13 + (2.059 * 2.0)  # 기본공격 4타 합산 계수
SHINING_THROW_COEFF = 0.40 * 3.0  # 대시 2회 중 두 번째 대시에서 발동하는 [베리 스로우] 추가타 피해 계수
SHINING_SPECIAL_STAB_COEFF = 4.97  # 특수스킬 찌르기 피해 계수
SHINING_SPECIAL_SLASH_COEFF = 7.10  # 특수스킬 베기 피해 계수
SHINING_SPECIAL_RUSH_COEFF = 4.26 * 2.0  # 특수스킬 돌진 피해 계수
SHINING_SPEAR_COEFF = 1.42 * 6.0  # 창/스피어 추가 피해 계수
SHINING_ULT_HIT_COEFF = 6.39  # 궁극기 1히트 피해 계수
SHINING_ULT_HITS = 30  # 궁극기 총 히트 수

# 사이클: (4평 → 대시) × 8 → 특 → 궁차징 → (4평 → 대시) × 2
# 대시는 2개가 한 짝이며, 두 번째 대시에만 [베리 스로우](SHINING_THROW_COEFF)를 반영한다.
SHINING_CYCLE_TOKENS = (["B4", "D"] * 8) + ["S", "U"] + (["B4", "D"] * 2)

# =====================================================
# Helpers - 고속 이벤트 전처리
# =====================================================
def _shining_precompute_fast_events() -> Tuple[List[Tuple[str, float]], float]:
    events: List[Tuple[str, float]] = []
    dash_count = 0
    post_ult = False
    for tok in SHINING_CYCLE_TOKENS:
        if tok == "S":
            events.append(("special", float(SHINING_SPECIAL_STAB_COEFF + SHINING_SPECIAL_SLASH_COEFF + SHINING_SPECIAL_RUSH_COEFF)))
            events.append(("ult", float(SHINING_SPEAR_COEFF)))
        elif tok == "U":
            # [또 다른 나]
            # - 베리샤인 익스텐드를 3초 유지한 뒤부터 궁극기 종료 전까지 피해 +50%
            # - 폭발 후 8초간 기본공격은 궁극기 피해로 취급되고 피해 +35%
            for i in range(SHINING_ULT_HITS):
                kind = "ult_hold" if i >= 3 else "ult"
                events.append((kind, float(SHINING_ULT_HIT_COEFF)))
            post_ult = True
        elif tok == "B4":
            events.append(("post_ult_basic" if post_ult else "basic", float(SHINING_BASIC_COEFF)))
        elif tok == "D":
            dash_count += 1
            if dash_count % 2 == 0:
                # 대시 2개가 한 짝이며, 두 번째 대시의 [베리 스로우]도 기본공격 피해다.
                events.append(("post_ult_basic" if post_ult else "basic", float(SHINING_THROW_COEFF)))
    return events, 30.0

_SHINING_FAST_EVENTS, _SHINING_FAST_TOTAL_TIME = _shining_precompute_fast_events()

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def shining_berry_cycle_damage_fast(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    total_time = 30.0

    special_extra_mult = (SHINING_BERRY_PROMO_SPECIAL_DMG_MULT if SHINING_BERRY_PROMO_ENABLED else 1.0)
    ult_extra_mult = (SHINING_BERRY_PROMO_ULT_DMG_MULT if SHINING_BERRY_PROMO_ENABLED else 1.0)

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0
    spear_coeff = float(SHINING_SPEAR_COEFF)

    for kind, coeff in _SHINING_FAST_EVENTS:
        if kind == "basic":
            dmg = skill_damage_from_start(stats, float(coeff), "basic")
            breakdown["basic"] += dmg
        elif kind == "post_ult_basic":
            # [또 다른 나]: 샤인 도트 폭발 후 8초간 기본공격을 궁극기 피해로 취급하고 +35%.
            post_mult = SHINING_BERRY_PROMO_POST_ULT_BASIC_DMG_MULT if SHINING_BERRY_PROMO_ENABLED else 1.0
            dmg = skill_damage_from_start(
                stats,
                float(coeff),
                "ult",
                extra_skill_mult=ult_extra_mult * post_mult,
            )
            breakdown["ult"] += dmg
        elif kind == "special":
            dmg = skill_damage_from_start(stats, float(coeff), "special", extra_skill_mult=special_extra_mult)
            breakdown["special"] += dmg
        else:
            hold_mult = SHINING_BERRY_PROMO_ULT_HOLD_MULT if (SHINING_BERRY_PROMO_ENABLED and kind == "ult_hold") else 1.0
            extra = SHINING_BERRY_PROMO_SPEAR_DMG_MULT if (SHINING_BERRY_PROMO_ENABLED and abs(float(coeff) - spear_coeff) < 1e-9) else 1.0
            dmg = skill_damage_from_start(stats, float(coeff), "ult", extra_skill_mult=ult_extra_mult * extra * hold_mult)
            breakdown["ult"] += dmg
        total_direct += dmg

    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * SHINING_CYCLE_TOKENS.count("U")
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "샤이닝베리맛 쿠키", stats, party)
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

    dps = total_damage / 30.0
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
# Helpers - 장비/후보 생성
# =====================================================
def shining_berry_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def shining_berry_allowed_uniques() -> List[str]:
    return ["스타더스트 쿠키의 기억"]

def shining_berry_allowed_artifacts() -> List[str]:
    return ["신기록 달성!"]

def shining_berry_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("레몬그라스톤:")]

@lru_cache(maxsize=None)
def shining_berry_generate_potentials_common() -> List[Dict[str, int]]:
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
def shining_berry_generate_shard_candidates_no_cr(step: int = 7) -> List[Dict[str, int]]:
    steps = list(range(0, NORMAL_SLOTS + 1, step))
    if steps[-1] != NORMAL_SLOTS:
        steps.append(NORMAL_SLOTS)

    out: List[Dict[str, int]] = []
    for cd in steps:
        for ae in steps:
            for ap in steps:
                for ud in steps:
                    used = cd + ae + ap + ud
                    if used > NORMAL_SLOTS:
                        continue
                    out.append({
                        "crit_dmg": cd,
                        "all_elem_dmg": ae,
                        "atk_pct": ap,
                        "ult_dmg": ud,
                    })
    return out

# =====================================================
# Calculation - 최적화
# =====================================================
def optimize_shining_berry_cycle(
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
    cookie = "샤이닝베리맛 쿠키"
    base = BASE_STATS_SHINING_BERRY[cookie].copy()

    equips = _resolve_equip_list_override(equip_override, shining_berry_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, shining_berry_allowed_uniques())
    potentials = shining_berry_generate_potentials_common()
    artifacts = shining_berry_allowed_artifacts()
    shard_candidates = shining_berry_generate_shard_candidates_no_cr(step=step)

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

                    if SHINING_BERRY_FORCE_CRIT_100:
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

                    promo_ap_mult = float(template.get("promo_armor_pen_mult", 1.0))
                    base_ap = float(template.get("armor_pen", 0.0)) * promo_ap_mult
                    if base_ap > 0.80 + 1e-12:
                        done += len(shard_candidates)
                        if (done % tick) == 0:
                            emit(done / total)
                        continue

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
                        if SHINING_BERRY_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = shining_berry_cycle_damage_fast(stats, party)
                        dps = cycle["dps"]
                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)
                            shards_out["passive_dmg"] = 0
                            shards_out["def_pct"] = 0
                            shards_out["shield_pct"] = 0
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
