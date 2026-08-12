# =====================================================
# Imports
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 룽샤맛 쿠키
# - 스트라이커 / 타격형 / 불속성
# - 윈드파라거스와 동일하게 스트라이커 전용 구조 사용
# =====================================================

# =====================================================
# Constants
# =====================================================
LUNGSHA_FORCE_CRIT_100 = True
LUNGSHA_WEAPON_ATK_PCT = 0.52
LUNGSHA_WEAPON_FINAL_DMG = 0.30

LUNGSHA_FIXED_SEAZ = "리치코랄:빛나는 은하수"
LUNGSHA_FIXED_ARTIFACT = "축제의 그림자"
LUNGSHA_FIXED_UNIQUE = "꿈열차에 실린 기억"

# 공격력 표기: 861 + 호감도 54
# 승급 공격력 +30%는 호감도 제외 기본공격력(861)에만 역산한다.
BASE_STATS_LUNGSHA = {
    "룽샤맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(861.0, 0.30),
        "friendship_atk": friendship_atk_for("룽샤맛 쿠키"),
        "def": 556.0,
        "hp": 5558.0,
        "elem_atk": 0.0,
        # 승급 공격력 +30% + 전용무기 기본 옵션 공격력 +52%
        "atk_pct": 0.30 + LUNGSHA_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 승급 최종 피해 +4% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.04 + LUNGSHA_WEAPON_FINAL_DMG,
    }
}

LUNGSHA_BASIC_COEFF = (0.994 * 2.0) + 1.278 + 1.562  # 기본공격 4타 합산 계수
LUNGSHA_SPECIAL1_COEFF = 2.84  # 특수스킬 1타 피해 계수
LUNGSHA_SPECIAL2_COEFF = 0.71 * 5.0  # 특수스킬 2타 피해 계수
LUNGSHA_SPECIAL3_COEFF = 2.272 * 2.0  # 특수스킬 3타 피해 계수
LUNGSHA_EMPOWERED_SPECIAL_COEFF = 5.112  # 강화 특수스킬 피해 계수
LUNGSHA_ULT_COEFF = 28.40  # 궁극기 피해 계수

# 승급 반영 (스킬 타입 피해 증가 축에 직접 합산)
LUNGSHA_PROMO_SPECIAL_DMG_ADD = 0.10  # 승급 특수스킬 피해 증가
LUNGSHA_PROMO_ULT_DMG_ADD = 0.30  # 승급 궁극기 피해 증가

# 상시 유지로 간주한 디버프/버프
# - 붉은 마음 : 공격력 +16%
# - 주화입마(+불속성 받피증) : 룽샤 기준 총 받피증 +53.6%
# - 삼매각화 : 받는 궁극기 피해 +35%
LUNGSHA_ALWAYS_SELF_ATK_PCT = 0.16
LUNGSHA_ALWAYS_DMG_TAKEN_INC = 0.536
LUNGSHA_ALWAYS_ENEMY_ULT_TAKEN_INC = 0.35

LUNGSHA_CYCLE_TOKENS = [
    "U", "ES", "S1",
    "B4", "B4",
    "S2",
    "B4", "B4",
    "S3",
    "ES",
    "B4", "B4",
    "S1",
    "B4", "B4",
    "S2",
    "B4", "B4",
    "S3",
]

# =====================================================
# Helpers - 장비/후보 생성
# =====================================================
def lungsha_allowed_equips() -> List[str]:
    return ["황금 예복", "유성우의 향연"]

def lungsha_allowed_uniques() -> List[str]:
    return [LUNGSHA_FIXED_UNIQUE, "새벽을 여는 달빛술사 쿠키의 기억"]

def lungsha_allowed_artifacts() -> List[str]:
    return [LUNGSHA_FIXED_ARTIFACT]

def lungsha_allowed_seaz() -> List[str]:
    return [LUNGSHA_FIXED_SEAZ]

@lru_cache(maxsize=None)
def lungsha_allowed_potentials() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

@lru_cache(maxsize=None)
def lungsha_generate_shard_candidates_no_cr(step: int = 2) -> List[Dict[str, int]]:
    """
    룽샤 FAST 전용 설유 후보.
    - 스트라이커 고정 잠재/장비 구조라 조합 수가 비교적 작다.
    - crit_rate는 자동 배정, 남는 슬롯은 elem_atk로 채운다.
    """
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
def _apply_lungsha_fixed_effects(stats: Dict[str, float], artifact_name: str) -> Dict[str, float]:
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    if s.get("_lungsha_fixed_effects_applied"):
        return s
    s["_lungsha_fixed_effects_applied"] = 1.0

    s["atk_pct"] = float(s.get("atk_pct", 0.0)) + LUNGSHA_ALWAYS_SELF_ATK_PCT
    s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + LUNGSHA_ALWAYS_DMG_TAKEN_INC
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + LUNGSHA_PROMO_SPECIAL_DMG_ADD
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + LUNGSHA_PROMO_ULT_DMG_ADD
    if artifact_name == LUNGSHA_FIXED_ARTIFACT:
        s["enemy_ult_taken_inc"] = float(s.get("enemy_ult_taken_inc", 0.0)) + LUNGSHA_ALWAYS_ENEMY_ULT_TAKEN_INC
    return s

# =====================================================
# Calculation - 사이클 딜
# =====================================================
def lungsha_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_lungsha_fixed_effects(stats, artifact_name)

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
    for tok in LUNGSHA_CYCLE_TOKENS:
        if tok == "B4":
            dmg = skill_damage_from_start(stats, LUNGSHA_BASIC_COEFF, "basic")
            breakdown["basic"] += dmg
        elif tok == "ES":
            dmg = skill_damage_from_start(stats, LUNGSHA_EMPOWERED_SPECIAL_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S1":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL1_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S2":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL2_COEFF, "special")
            breakdown["special"] += dmg
        elif tok == "S3":
            dmg = skill_damage_from_start(stats, LUNGSHA_SPECIAL3_COEFF, "special")
            breakdown["special"] += dmg
        else:
            dmg = skill_damage_from_start(stats, LUNGSHA_ULT_COEFF, "ult")
            breakdown["ult"] += dmg
        total_direct += dmg

    strike = strike_total_from_direct(total_direct, "룽샤맛 쿠키", stats, party)
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
# Calculation - 최적화
# =====================================================
def optimize_lungsha_cycle(
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

    cookie = '룽샤맛 쿠키'
    base = BASE_STATS_LUNGSHA[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, lungsha_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, lungsha_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else lungsha_allowed_potentials()
    artifacts = lungsha_allowed_artifacts()
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
                    template = _apply_lungsha_fixed_effects(template, artifact_name)

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
                            return lungsha_cycle_damage_fast(stats, party, artifact_name)

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
