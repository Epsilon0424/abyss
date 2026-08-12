# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 체리콜라맛 쿠키
# - 스트라이커 / 타격형 / 물속성
# - 받피증 스트라이커라 장비는 황금 예복/유성우의 향연만 사용한다.
# - 잠재/일반 설탕유리조각 후보는 디버프 증폭 없이 딜러형으로 최적화한다.
# - 버블포인트 받는 피해 증가는 디버프 증폭을 받지 않는다.
# =====================================================

CHERRY_COLA_FORCE_CRIT_100 = True
CHERRY_COLA_WEAPON_ATK_PCT = 0.52
CHERRY_COLA_WEAPON_FINAL_DMG = 0.30

CHERRY_COLA_FIXED_SEAZ = "리치코랄:빛나는 은하수"
CHERRY_COLA_FIXED_ARTIFACT = "끈적끈적 후폭풍"
CHERRY_COLA_FIXED_UNIQUE = "꿈열차에 실린 기억"

BASE_STATS_CHERRY_COLA = {
    "체리콜라맛 쿠키": {
        "atk": atk_without_friendship(791.0),
        "friendship_atk": friendship_atk_for("체리콜라맛 쿠키"),
        "def": 566.0 + 48.0,
        "hp": 5917.0 + 432.0,
        "elem_atk": 0.0,
        # 전용무기 기본 옵션: 공격력 +52%
        "atk_pct": CHERRY_COLA_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + CHERRY_COLA_WEAPON_FINAL_DMG,
    }
}

# 스킬 레벨 12 기준, 스킬 레벨 보너스(+42%)는 계수 원본에 이미 표시된 값으로 사용한다.
CHERRY_COLA_BASIC3_COEFF = 0.994 + 0.994 + (0.426 * 5.0)  # 일반 기본공격 3타 합산 계수
CHERRY_COLA_EMPOWERED_BASIC_COEFF = CHERRY_COLA_BASIC3_COEFF + 2.84  # 강화 기본공격 3타 + [새콤달콤...플루이드!] 추가 피해 계수
CHERRY_COLA_SPECIAL_COEFF = 0.71 * 8.0  # 특수스킬 피해 계수
CHERRY_COLA_ULT_COEFF = 5.68 + (4.97 * 5.0) + 3.55  # 궁극기 피해 계수

# 승급/스킬 효과
CHERRY_COLA_FLUID_DMG_ADD = 0.20  # [새콤달콤...플루이드!] 강화 기본공격 피해 증가
CHERRY_COLA_BUBBLE_POINT_TAKEN = 0.224
CHERRY_COLA_BUBBLE_POINT_WATER_TAKEN = 0.30  # 버블포인트: 물속성 쿠키에게 받는 피해 증가 +30%
CHERRY_COLA_SPECIAL_DMG_ADD = 0.20  # [통제 불가 방과 후] 특수스킬 피해 증가
CHERRY_COLA_ULT_DMG_ADD = 0.25  # [통제 불가 방과 후] 궁극기 피해 증가

# 유저 지정 30초 사이클:
# 궁 특특 강화3평 강화3평 강화3평 특 강화3평 강화3평 특 강화3평 강화3평 강화3평 특
CHERRY_COLA_CYCLE_TOKENS = [
    "U", "S", "S",
    "EB3", "EB3", "EB3", "S",
    "EB3", "EB3", "S",
    "EB3", "EB3", "EB3", "S",
]

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def cherry_cola_allowed_equips() -> List[str]:
    return ["황금 예복", "유성우의 향연"]

def cherry_cola_allowed_uniques() -> List[str]:
    return ["밀키웨이맛 쿠키의 기억", CHERRY_COLA_FIXED_UNIQUE, "새벽을 여는 달빛술사 쿠키의 기억"]

def cherry_cola_allowed_artifacts() -> List[str]:
    return [CHERRY_COLA_FIXED_ARTIFACT]

def cherry_cola_allowed_seaz() -> List[str]:
    return [CHERRY_COLA_FIXED_SEAZ]

@lru_cache(maxsize=None)
def cherry_cola_allowed_potentials() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

@lru_cache(maxsize=None)
def cherry_cola_generate_shard_candidates_no_cr(step: int = 3) -> List[Dict[str, int]]:
    step = max(1, int(step or 1))
    # 체리콜라는 딜러식 잠재를 쓰지만, 일반 설탕유리조각 최적화에서
    # 기본공격/특수스킬/궁극기 피해는 제외하고,
    # 새콤달콤...플루이드!가 패시브 피해이므로 패시브 스킬 피해는 후보에 포함한다.
    keys = ["crit_dmg", "all_elem_dmg", "atk_pct", "passive_dmg"]
    out: List[Dict[str, int]] = []

    def dfs(idx: int, remain: int, cur: Dict[str, int]) -> None:
        if idx == len(keys):
            out.append({k: int(cur.get(k, 0)) for k in keys})
            return
        k = keys[idx]
        vals = list(range(0, remain + 1, step))
        if remain not in vals:
            vals.append(remain)
        for x in vals:
            cur[k] = x
            dfs(idx + 1, remain - x, cur)
        cur.pop(k, None)

    dfs(0, NORMAL_SLOTS, {})
    return out

# =====================================================
# Helpers - 고정 효과 반영
# =====================================================
def _apply_cherry_cola_fixed_effects(stats: Dict[str, float]) -> Dict[str, float]:
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    if s.get("_cherry_cola_fixed_effects_applied"):
        return s
    s["_cherry_cola_fixed_effects_applied"] = 1.0

    # 버블포인트: 쿠키에게 받는 피해 +22.4%.
    # 물속성 쿠키에게 받는 피해 +30%.
    # 체리콜라는 물속성이라 본인 계산에도 적용한다.
    # 마블베리처럼 디버프 증폭은 적용하지 않는다.
    s["dmg_taken_inc"] = (
        float(s.get("dmg_taken_inc", 0.0))
        + CHERRY_COLA_BUBBLE_POINT_TAKEN
        + CHERRY_COLA_BUBBLE_POINT_WATER_TAKEN
    )

    # 새콤달콤...플루이드!: 강화 기본공격 피해 +20%.
    # RESULT 스탯 표에 패시브 피해로 표시되지 않도록 stats에는 넣지 않고,
    # EB3 계산 시 extra_skill_mult로만 별도 적용한다.

    # 통제 불가 방과 후: 체리콜라 본인 특수스킬/궁극기 피해 증가.
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + CHERRY_COLA_SPECIAL_DMG_ADD
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + CHERRY_COLA_ULT_DMG_ADD
    return s

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def cherry_cola_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str = CHERRY_COLA_FIXED_ARTIFACT) -> Dict[str, float]:
    stats = _apply_cherry_cola_fixed_effects(stats)

    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    total_direct = 0.0
    sticky_passive_taken = 0.0
    try:
        sticky_passive_taken = float(ARTIFACTS.get(CHERRY_COLA_FIXED_ARTIFACT, {}).get("cherry_cola", {}).get("enemy_passive_taken_inc", 0.0))
    except Exception:
        sticky_passive_taken = 0.0
    sticky_active = False

    for tok in CHERRY_COLA_CYCLE_TOKENS:
        if tok == "EB3":
            calc_stats = stats
            if artifact_name == CHERRY_COLA_FIXED_ARTIFACT and sticky_passive_taken and sticky_active:
                calc_stats = stats.copy()
                calc_stats.pop("_damage_context_cache", None)
                calc_stats["enemy_passive_taken_inc"] = float(calc_stats.get("enemy_passive_taken_inc", 0.0)) + sticky_passive_taken
            dmg = skill_damage_from_start(
                calc_stats,
                CHERRY_COLA_EMPOWERED_BASIC_COEFF,
                "passive",
                extra_skill_mult=1.0 + CHERRY_COLA_FLUID_DMG_ADD,
            )
            breakdown["basic"] += dmg
            if artifact_name == CHERRY_COLA_FIXED_ARTIFACT and sticky_passive_taken:
                # 끈적끈적 후폭풍: 강화 기본공격 적중 후 적에게 받는 패시브 스킬 피해 증가 부여.
                # 첫 강화 기본공격은 표식을 부여하고, 이후 패시브 피해부터 적용되도록 계산한다.
                sticky_active = True
        elif tok == "B3":
            dmg = skill_damage_from_start(stats, CHERRY_COLA_BASIC3_COEFF, "basic")
            breakdown["basic"] += dmg
        elif tok == "S":
            dmg = skill_damage_from_start(stats, CHERRY_COLA_SPECIAL_COEFF, "special")
            breakdown["special"] += dmg
        else:
            dmg = skill_damage_from_start(stats, CHERRY_COLA_ULT_COEFF, "ult")
            breakdown["ult"] += dmg
        total_direct += dmg

    strike = strike_total_from_direct(total_direct, "체리콜라맛 쿠키", stats, party)
    breakdown["strike"] = strike

    total_time = 30.0
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
def optimize_cherry_cola_cycle(
    seaz_name: str,
    party: List[str],
    party_seaz: Optional[Dict[str, str]] = None,
    party_uniques: Optional[Dict[str, str]] = None,
    party_sets: Optional[Dict[str, str]] = None,
    step: int = 1,
    progress_cb: Optional[Callable[[float], None]] = None,
    equip_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    unique_override: Optional[Union[str, List[str], Tuple[str, ...], set]] = None,
    potential_override: Optional[Dict[str, int]] = None,
) -> Optional[dict]:
    """장비별 상위 후보를 선별한 뒤 상위 4스탯을 step=1로 전수조사한다."""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행한다.

    cookie = '체리콜라맛 쿠키'
    base = BASE_STATS_CHERRY_COLA[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, cherry_cola_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, cherry_cola_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else cherry_cola_allowed_potentials()
    artifacts = cherry_cola_allowed_artifacts()
    zero_shards = {key: 0 for key in SHARD_INC.keys()}

    total = max(1, len(equips) * len(artifacts) * len(uniques) * len(potentials))
    done = 0

    def emit(progress: float) -> None:
        if not progress_cb:
            return
        try:
            progress_cb(progress)
        except Exception:
            pass

    emit(0.0)
    screened_by_equip: Dict[str, List[dict]] = {equip: [] for equip in equips}

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
                    template = _apply_cherry_cola_fixed_effects(template)

                    try:
                        if not is_valid_by_caps(template):
                            continue
                        if not should_evaluate_conditional_crit_potential(template, pot):
                            continue

                        required_crit = _min_crit_slots_needed_for_crit100_generic(template)
                        if required_crit is None:
                            continue
                        required_crit = int(required_crit)
                        if required_crit > NORMAL_SLOTS:
                            continue

                        template.pop("_applied_party_buffs", None)
                        template.pop("_applied_enemy_debuffs", None)

                        def cycle_for(
                            stats: Dict[str, float],
                            artifact_name: str = artifact_name,
                        ) -> Dict[str, float]:
                            return cherry_cola_cycle_damage_fast(stats, party, artifact_name)

                        shards_out, stats, cycle = optimize_damage_shards_for_fixed_combo(
                            template,
                            cycle_for,
                            required_crit_slots=required_crit,
                        )

                        cur = {
                            "cookie": cookie,
                            "dps": cycle["dps"],
                            "cycle_total_damage": cycle["total_damage"],
                            "cycle_total_time": float(cycle.get("total_time", 30.0)),
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
                            "_template": template,
                            "_cycle_fn": cycle_for,
                            "_required_crit": required_crit,
                        }
                        bucket = screened_by_equip.setdefault(equip, [])
                        bucket.append(cur)
                        bucket.sort(key=lambda item: float(item.get("dps", 0.0)), reverse=True)
                        del bucket[DAMAGE_SHARD_FINALISTS_PER_EQUIP:]
                    finally:
                        done += 1
                        emit(0.65 * done / total)

    finalists = [candidate for bucket in screened_by_equip.values() for candidate in bucket]
    finalist_total = max(1, len(finalists))
    best: Optional[dict] = None

    for index, cur in enumerate(finalists, start=1):
        shards_out, stats, cycle = optimize_damage_shards_top4_for_fixed_combo(
            cur["_template"],
            cur["_cycle_fn"],
            required_crit_slots=int(cur["_required_crit"]),
        )
        cur["shards"] = shards_out
        cur["stats"] = stats
        cur["dps"] = float(cycle["dps"])
        cur["cycle_total_damage"] = float(cycle["total_damage"])
        cur["cycle_total_time"] = float(cycle.get("total_time", 30.0))
        cur["cycle_breakdown"] = cycle
        cur["buff_amp_total"] = stats.get("buff_amp_total", stats.get("buff_amp", 0.0))
        cur["debuff_amp_total"] = stats.get("debuff_amp_total", stats.get("debuff_amp", 0.0))
        cur.pop("_template", None)
        cur.pop("_cycle_fn", None)
        cur.pop("_required_crit", None)

        if best is None or float(cur["dps"]) > float(best["dps"]):
            best = cur
        emit(0.65 + (0.35 * index / finalist_total))

    emit(1.0)
    return best
