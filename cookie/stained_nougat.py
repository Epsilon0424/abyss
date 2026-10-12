# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override

# =====================================================
# 스테인드누가맛 쿠키
# =====================================================
# 역할: 스트라이커·사격형·대지 속성

# =====================================================
# 상수
# =====================================================
STAINED_NOUGAT_WEAPON_ATK_PCT = 0.52
STAINED_NOUGAT_WEAPON_FINAL_DMG = 0.30

STAINED_NOUGAT_FIXED_SEAZ = "리치코랄:빛나는 은하수"
STAINED_NOUGAT_FIXED_ARTIFACT = "꿈결 같은 휴식"
STAINED_NOUGAT_FIXED_UNIQUE = "꿈열차에 실린 기억"

# 공격력 표기: 842 + 호감도 51
# 승급 공격력 +30%: 호감도 제외 기본공격력 842 기준 역산
BASE_STATS_STAINED_NOUGAT = {
    "스테인드누가맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(842.0, 0.30),
        "friendship_atk": friendship_atk_for("스테인드누가맛 쿠키"),
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + STAINED_NOUGAT_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + STAINED_NOUGAT_WEAPON_FINAL_DMG,
    }
}

# 기본공격 4타 계수 142% + 142% + 177.5% + 106.5% × 3
STAINED_NOUGAT_BASIC4_COEFF = 1.42 + 1.42 + 1.775 + (1.065 * 3.0)
# 특수 스킬 1회 = 284% × 5히트
STAINED_NOUGAT_SPECIAL_COEFF = 2.84 * 5.0
# 궁극기 1회 = 497% × 6히트
STAINED_NOUGAT_ULT_COEFF = 4.97 * 6.0
# 패시브 [얼룩] = 49.7% × 33히트
STAINED_NOUGAT_STAIN_COEFF = 0.497 * 33.0
# 얼룩진 기억 390.5% × 6회·30초 기준
STAINED_NOUGAT_MEMORY_COEFF = 3.905 * 6.0

# 사이클: 특 궁 특 4평 4평 4평 특 4평 4평 4평 4평 특 4평 4평
STAINED_NOUGAT_BASIC4_COUNT = 9
STAINED_NOUGAT_SPECIAL_COUNT = 4
STAINED_NOUGAT_ULT_COUNT = 1

# 정화: 받는 피해 33.6%·대지 속성 받는 피해 20% 증가
STAINED_NOUGAT_PURIFICATION_TAKEN = 0.336
STAINED_NOUGAT_PURIFICATION_EARTH_TAKEN = 0.20

# =====================================================
# 승급 효과
# =====================================================
STAINED_NOUGAT_PROMO_SPECIAL_DMG_ADD = 0.40
STAINED_NOUGAT_PROMO_ULT_DMG_ADD = 0.30
STAINED_NOUGAT_PROMO_PASSIVE_DMG_ADD = 0.20

# 전용 아티팩트 [쏟아지는 기억] : 받는 기본 공격 피해 35% 증가
STAINED_NOUGAT_ARTIFACT_BASIC_TAKEN = 0.35

def stained_nougat_allowed_equips() -> List[str]:
    return ["유성우의 향연", "황금 예복"]

def stained_nougat_allowed_seaz() -> List[str]:
    return [STAINED_NOUGAT_FIXED_SEAZ]

def stained_nougat_allowed_uniques() -> List[str]:
    return [
        "밀키웨이맛 쿠키의 기억",
        STAINED_NOUGAT_FIXED_UNIQUE,
        "새벽을 여는 달빛술사 쿠키의 기억",
    ]

def stained_nougat_allowed_artifacts() -> List[str]:
    return [STAINED_NOUGAT_FIXED_ARTIFACT]

def stained_nougat_allowed_potentials() -> List[Dict[str, int]]:
    return generate_damage_potential_candidates(
        fixed={"elem_atk": 2},
        total_slots=8,
        free_keys=("atk_pct", "crit_rate", "crit_dmg"),
    )

def _apply_stained_nougat_fixed_effects(stats: Dict[str, float], artifact_name: str) -> Dict[str, float]:
    s = stats.copy()
    if s.get("_applied_stained_nougat_fixed", False):
        return s
    s["_applied_stained_nougat_fixed"] = True

    # [정화] 상시 유지 가정
    s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + STAINED_NOUGAT_PURIFICATION_TAKEN + STAINED_NOUGAT_PURIFICATION_EARTH_TAKEN

    # 승급: 특수 / 궁극기 / 패시브 피해 증가
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + STAINED_NOUGAT_PROMO_SPECIAL_DMG_ADD
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + STAINED_NOUGAT_PROMO_ULT_DMG_ADD
    s["passive_dmg"] = float(s.get("passive_dmg", 0.0)) + STAINED_NOUGAT_PROMO_PASSIVE_DMG_ADD

    # 전용 아티팩트 [쏟아지는 기억] 상시 유지 가정
    if artifact_name == STAINED_NOUGAT_FIXED_ARTIFACT:
        s["enemy_basic_taken_inc"] = float(s.get("enemy_basic_taken_inc", 0.0)) + STAINED_NOUGAT_ARTIFACT_BASIC_TAKEN

    return s

def stained_nougat_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_stained_nougat_fixed_effects(stats, artifact_name)

    total_time = 30.0
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "proc": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    basic_total = skill_damage_from_start(stats, STAINED_NOUGAT_BASIC4_COEFF, "basic") * STAINED_NOUGAT_BASIC4_COUNT
    special_total = skill_damage_from_start(stats, STAINED_NOUGAT_SPECIAL_COEFF, "special") * STAINED_NOUGAT_SPECIAL_COUNT
    ult_total = skill_damage_from_start(stats, STAINED_NOUGAT_ULT_COEFF, "ult") * STAINED_NOUGAT_ULT_COUNT

    stain_total = skill_damage_from_start(stats, STAINED_NOUGAT_STAIN_COEFF, "passive")
    memory_total = skill_damage_from_start(stats, STAINED_NOUGAT_MEMORY_COEFF, "passive")
    proc_total = stain_total + memory_total

    breakdown["basic"] = basic_total
    breakdown["special"] = special_total
    breakdown["ult"] = ult_total
    breakdown["proc"] = proc_total

    total_direct = basic_total + special_total + ult_total
    strike = strike_total_from_direct(total_direct, "스테인드누가맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + proc_total + strike + unique_total)

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

def optimize_stained_nougat_cycle(
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
    del step

    cookie = '스테인드누가맛 쿠키'
    base = BASE_STATS_STAINED_NOUGAT[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, stained_nougat_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, stained_nougat_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else stained_nougat_allowed_potentials()
    artifacts = stained_nougat_allowed_artifacts()
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
                    template = _apply_stained_nougat_fixed_effects(template, artifact_name)

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
                            return stained_nougat_cycle_damage_fast(stats, party, artifact_name)

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
