# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 피닉스페퍼 쿠키
# =====================================================

# =====================================================
# Constants
# =====================================================
PHOENIX_PEPPER_PROMO_ENABLED = True
PHOENIX_PEPPER_FORCE_CRIT_100 = True
PHOENIX_PEPPER_WEAPON_ATK_PCT = 0.52
PHOENIX_PEPPER_WEAPON_FINAL_DMG = 0.30
PHOENIX_PEPPER_PROMO_ULT_DMG_MULT = 1.45
PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT = 1.80

BASE_STATS_PHOENIX_PEPPER = {
    "피닉스페퍼 쿠키": {
        "atk": 715.0,
        "friendship_atk": friendship_atk_for("피닉스페퍼 쿠키"),
        "def": 382.0,
        "hp": 4256.0,
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": PHOENIX_PEPPER_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.875,
        "armor_pen": 0.0,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + PHOENIX_PEPPER_WEAPON_FINAL_DMG,
    }
}

PHOENIX_BASIC_COEFF = (1.42 * 3.0) + (1.562 * 3.0) + 9.088 + 9.088  # 기본공격 [불꽃의 춤] 1~4타 합산 피해 계수: 142%×3 + 156.2%×3 + 908.8% + 908.8%
PHOENIX_DASH_COEFF = 1.3064 * 4.0  # 대시 [낙화] 홀드 피해 계수: 130.64%×4, 현재 30초 사이클 계산에는 미사용

PHOENIX_SPECIAL1_COEFF = 5.439 * 2.0  # 특수스킬 [생동] 피해 계수: 543.9%×2
PHOENIX_SPECIAL2_COEFF_BASE = 1.69 * 10.0  # 특수스킬 [충만] 피해 계수: 169%×10
PHOENIX_SPECIAL3_COEFF_BASE = 13.206  # 특수스킬 [회귀] 피해 계수: 1320.6%
PHOENIX_SPECIAL2_COEFF_ARTI = (1.19 * 10.0) + (8.88 * 3.0)  # 아티팩트 [타오르는 생의 시작] 적용 특수스킬 [충만:진] 피해 계수: 119%×10 + 888%×3, 궁극기 피해 취급
PHOENIX_SPECIAL3_COEFF_ARTI = 8.88 * 3.0  # 아티팩트 [타오르는 생의 시작] 적용 특수스킬 [회귀:진] 피해 계수: 888%×3, 궁극기 피해 취급

PHOENIX_PASSIVE_COEFF = 9.869  # 패시브 [타오르는 정열] - [마음의 불티] 피해 계수: 986.9%, 궁극기 피해 취급
PHOENIX_ULT1_COEFF = 5.893 * 7.0  # 궁극기 [우화비천] 피해 계수: 589.3%×7
PHOENIX_ULT2_COEFF = 5.893 * 7.0  # 궁극기 [천략우화] 피해 계수: 589.3%×7
PHOENIX_ULT3_COEFF = 18.2754 * 8.0  # 궁극기 [천지재화] 피해 계수: 1827.54%×8

PHOENIX_CYCLE_TOKENS = [
    "B4", "B4", "TRI", "U1",
    "B4", "B4", "TRI", "U2", "U3",
    "B4", "B4"
]

# =====================================================
# Helpers - 히트/이벤트 계산
# =====================================================
def _phoenix_cycle_hits(artifact_name: str) -> int:
    basic_hits = 6 * (3 + 3 + 1 + 1)
    special_hits = 3 * (2 + 19 + 3) if artifact_name == "타오르는 생의 시작" else 3 * (2 + 10 + 1)
    ult_hits = (7 + 7 + 8)
    return int(basic_hits + special_hits + ult_hits)

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def phoenix_pepper_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    total_time = 30.0
    # 스킬별 처음부터 계산: skill_damage_from_start 사용

    # 승급 배율
    # - [깨지지 않는 불꽃]은 [우화비천]/[천략우화]/[천지재화] 피해 +45%라서 궁극기 본체 3종에만 별도 적용한다.
    # - [뜨겁게 피어나는 마음]은 [마음의 불티] 피해 +80%라서 마음의 불티에만 별도 적용한다.
    # - [충만:진]/[회귀:진]과 [마음의 불티]는 "궁극기 피해 취급"이므로 ult_dmg/enemy_ult_taken_inc 축은 받지만,
    #   [우화비천]/[천략우화]/[천지재화] 전용 45% 승급 배율은 받지 않는 것으로 계산한다.
    promo_ult_mult = float(
        stats.get(
            "promo_ult_dmg_mult",
            PHOENIX_PEPPER_PROMO_ULT_DMG_MULT if PHOENIX_PEPPER_PROMO_ENABLED else 1.0,
        )
    )
    ember_extra_mult = float(
        stats.get(
            "promo_passive_dmg_mult",
            PHOENIX_PEPPER_PROMO_PASSIVE_DMG_MULT if PHOENIX_PEPPER_PROMO_ENABLED else 1.0,
        )
    )

    arti_on = (artifact_name == "타오르는 생의 시작")
    s2_coeff = PHOENIX_SPECIAL2_COEFF_ARTI if arti_on else PHOENIX_SPECIAL2_COEFF_BASE
    s3_coeff = PHOENIX_SPECIAL3_COEFF_ARTI if arti_on else PHOENIX_SPECIAL3_COEFF_BASE

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
    for tok in PHOENIX_CYCLE_TOKENS:
        if tok == "B4":
            dmg = skill_damage_from_start(stats, PHOENIX_BASIC_COEFF, "basic")
            breakdown["basic"] += dmg
        elif tok == "TRI":
            dmg1 = skill_damage_from_start(stats, PHOENIX_SPECIAL1_COEFF, "special")
            # [충만:진]/[회귀:진]은 궁극기 피해 취급이라 skill_type="ult"로 계산하지만,
            # 승급 [깨지지 않는 불꽃]의 45%는 궁극기 본체 3종 전용이라 여기에는 별도로 곱하지 않는다.
            dmg2 = skill_damage_from_start(stats, s2_coeff, "ult")
            dmg3 = skill_damage_from_start(stats, s3_coeff, "ult")
            dmg = dmg1 + dmg2 + dmg3
            breakdown["special"] += dmg1
            breakdown["ult"] += (dmg2 + dmg3)
        elif tok == "U1":
            dmg = skill_damage_from_start(stats, PHOENIX_ULT1_COEFF, "ult", extra_skill_mult=promo_ult_mult)
            breakdown["ult"] += dmg
        elif tok == "U2":
            dmg = skill_damage_from_start(stats, PHOENIX_ULT2_COEFF, "ult", extra_skill_mult=promo_ult_mult)
            breakdown["ult"] += dmg
        else:
            dmg = skill_damage_from_start(stats, PHOENIX_ULT3_COEFF, "ult", extra_skill_mult=promo_ult_mult)
            breakdown["ult"] += dmg
        total_direct += dmg

    ember_hits = _phoenix_cycle_hits(artifact_name)
    ember_procs = ember_hits // 10
    # [마음의 불티]는 발생 조건은 패시브지만 실제 피해는 궁극기 피해 취급이다.
    # 따라서 skill_type="ult"로 계산하고, 별도로 승급 [뜨겁게 피어나는 마음] +80%만 곱한다.
    ember_total = skill_damage_from_start(stats, PHOENIX_PASSIVE_COEFF, "ult", extra_skill_mult=ember_extra_mult) * ember_procs

    # 마음의 불티 피해는 궁극기 피해에 합산
    breakdown["ult"] += ember_total
    breakdown["passive"] = 0.0

    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none") * sum(1 for t in PHOENIX_CYCLE_TOKENS if str(t).startswith("U"))
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct + ember_total, "피닉스페퍼 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + ember_total + strike + unique_total)

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
        "breakdown_passive": breakdown["passive"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def phoenix_pepper_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]

def phoenix_pepper_allowed_uniques() -> List[str]:
    return ["로드 나이트메어의 뒤틀린 기억"]

def phoenix_pepper_allowed_artifacts() -> List[str]:
    return ["타오르는 생의 시작"]

def phoenix_pepper_allowed_seaz() -> List[str]:
    return [x for x in SEAZNITES.keys() if str(x).startswith("레몬그라스톤:")]

@lru_cache(maxsize=None)
def phoenix_pepper_generate_potentials_common() -> List[Dict[str, int]]:
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
def phoenix_pepper_generate_shard_candidates_no_cr(step: int = 2) -> List[Dict[str, int]]:
    """
    피닉스 FAST 전용 설유 후보 생성.
    - step 값은 그대로 사용하되, 6축 완전탐색 대신
      "합계가 NORMAL_SLOTS 이하인 stepped composition"만 생성해서
      step=2여도 멜랑처럼 빠르게 돌도록 한다.
    - 남는 슬롯은 이후 crit_rate / elem_atk 자동 배정으로 처리된다.
    """
    step = max(1, int(step or 1))
    # 피페 설유 탐색 축: 기본 공격/특수 스킬/패시브 피해 증가 제외
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct", "ult_dmg"]

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
# Calculation - 최적화
# =====================================================
def optimize_phoenix_pepper_cycle(
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
    cookie = "피닉스페퍼 쿠키"
    base = BASE_STATS_PHOENIX_PEPPER[cookie].copy()

    # 고속 모드에서는 step 값은 유지하고, 후보 생성은 합계 제한 DFS로 처리
    # step=2에서도 멜랑처럼 빠르게 동작하도록
    fast_step = max(1, int(step or 1))

    equips = _resolve_equip_list_override(equip_override, phoenix_pepper_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, phoenix_pepper_allowed_uniques())
    potentials = phoenix_pepper_generate_potentials_common()
    artifacts = phoenix_pepper_allowed_artifacts()
    shard_candidates = phoenix_pepper_generate_shard_candidates_no_cr(step=fast_step)

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

                    if PHOENIX_PEPPER_FORCE_CRIT_100:
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
                        if PHOENIX_PEPPER_FORCE_CRIT_100 and req_cr_slots and cr_inc:
                            stats["crit_rate"] = float(stats.get("crit_rate", 0.0)) + cr_inc * req_cr_slots
                        if ea_slots and ea_inc:
                            stats["elem_atk"] = float(stats.get("elem_atk", 0.0)) + ea_inc * int(ea_slots)

                        # 설탕유리조각은 방어관통을 올리지 않으므로 template 단계의 cap 검사 결과를 그대로 사용한다.
                        # 치확 100% 조건은 req_cr_slots 계산으로 이미 맞춘 상태다.

                        cycle = phoenix_pepper_cycle_damage_fast(stats, party, artifact_name)
                        dps = cycle["dps"]
                        if (best is None) or (dps > best["dps"]):
                            shards_out = dict(sh_base)
                            shards_out["crit_rate"] = int(req_cr_slots)
                            shards_out["elem_atk"] = int(ea_slots)
                            shards_out["passive_dmg"] = 0
                            shards_out["def_pct"] = 0
                            shards_out["shield_pct"] = 0
                            shards_out["heal_pct"] = 0
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
