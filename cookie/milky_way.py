# =====================================================
# Imports
# =====================================================
from functools import lru_cache

from .common import *
from .common import (
    _min_crit_slots_needed_for_crit100_generic,
    _resolve_equip_list_override,
    _resolve_unique_list_override,
)

# =====================================================
# 밀키웨이맛 쿠키
# - 스트라이커 / 타격형 / 신비속성
# =====================================================

MILKY_WAY_PROMO_ATK_PCT = 0.20
MILKY_WAY_WEAPON_ATK_PCT = 0.52
MILKY_WAY_WEAPON_FINAL_DMG = 0.30

MILKY_WAY_FIXED_SEAZ = "리치코랄:빛나는 은하수"
MILKY_WAY_FIXED_ARTIFACT = "꿈의 저편으로"
MILKY_WAY_FIXED_UNIQUE = "꿈열차에 실린 기억"

# 표기 기본공격력 728에는 돌파 공격력 +20%가 포함되어 있다.
# 호감도 공격력 48은 역산에 넣지 않고 최종 공격력 계산 마지막에 한 번만 더한다.
BASE_STATS_MILKY_WAY = {
    "밀키웨이맛 쿠키": {
        "atk": atk_from_promoted_base_without_friendship(728.0, MILKY_WAY_PROMO_ATK_PCT),
        "friendship_atk": friendship_atk_for("밀키웨이맛 쿠키"),
        "elem_atk": 0.0,
        "atk_pct": MILKY_WAY_PROMO_ATK_PCT + MILKY_WAY_WEAPON_ATK_PCT,
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        "final_dmg": 0.04 + MILKY_WAY_WEAPON_FINAL_DMG,
    }
}

# 스킬 계수
MILKY_WAY_CHARGE_COEFF = 1.420 * 3.0
MILKY_WAY_SPECIAL_COEFF = 2.272 * 4.0
MILKY_WAY_ULT_TRAIN_COEFF = 25.56
MILKY_WAY_ULT_LIGHT_RAY_COEFF = 1.136 * 20.0

# 돌파 효과
MILKY_WAY_PROMO_SPECIAL_DMG = 0.20
MILKY_WAY_PROMO_ULT_DMG = 0.30
MILKY_WAY_SLEEP_TALK_TAKEN = 0.336
MILKY_WAY_SLEEP_TALK_MYSTIC_TAKEN = 0.20

# 사용자가 제공한 30초 실전 사이클.
# 차징 기본 공격을 반복하는 사이클 2만 사용한다.
MILKY_WAY_CYCLE_TOKENS = (
    ["U", "S", "S"]
    + ["C"] * 4
    + ["S"]
    + ["C"] * 4
    + ["S"]
    + ["C"] * 5
    + ["S", "C"]
)


def milky_way_allowed_equips() -> List[str]:
    return ["유성우의 향연", "황금 예복"]


def milky_way_allowed_uniques() -> List[str]:
    return [MILKY_WAY_FIXED_UNIQUE, "밀키웨이맛 쿠키의 기억", "새벽을 여는 달빛술사 쿠키의 기억"]


def milky_way_allowed_artifacts() -> List[str]:
    return [MILKY_WAY_FIXED_ARTIFACT]


def milky_way_allowed_seaz() -> List[str]:
    return [MILKY_WAY_FIXED_SEAZ]


@lru_cache(maxsize=None)
def milky_way_allowed_potentials() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 포함 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})


MILKY_WAY_SHARD_STEP = 1
MILKY_WAY_SHARD_KEYS = (
    "crit_dmg",
    "all_elem_dmg",
    "atk_pct",
)


def _milky_way_shard_candidate_count(remain_slots: int) -> int:
    """1칸 단위 전수 탐색 후보 수. 남는 칸은 속성 공격력으로 배정한다."""
    remain_slots = max(0, int(remain_slots))
    return math.comb(remain_slots + len(MILKY_WAY_SHARD_KEYS), len(MILKY_WAY_SHARD_KEYS))


def _iter_milky_way_shard_allocations(remain_slots: int):
    """
    밀키웨이 설탕유리조각 전수 탐색.
    - 치명타 확률은 100%에 필요한 최소 칸을 먼저 배정한다.
    - 남은 칸은 공격력 %, 치명타 피해, 모든 속성 피해를 1칸 단위로 탐색한다.
    - 각 후보에서 사용하지 않은 칸은 속성 공격력으로 채운다.
    - 기본/특수/궁극기 피해는 탐색하지 않는다.
    """
    remain_slots = max(0, int(remain_slots))
    values = [0] * len(MILKY_WAY_SHARD_KEYS)

    def dfs(index: int, remain: int, used: int):
        if index == len(MILKY_WAY_SHARD_KEYS):
            yield tuple(values), used
            return

        for slot_count in range(0, remain + 1, MILKY_WAY_SHARD_STEP):
            values[index] = slot_count
            yield from dfs(index + 1, remain - slot_count, used + slot_count)
        values[index] = 0

    yield from dfs(0, remain_slots, 0)


def _apply_milky_way_fixed_effects(
    stats: Dict[str, float],
    artifact_name: str = MILKY_WAY_FIXED_ARTIFACT,
) -> Dict[str, float]:
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    if s.get("_milky_way_fixed_effects_applied"):
        return s
    s["_milky_way_fixed_effects_applied"] = 1.0

    # 잠꼬대: 쿠키에게 받는 피해 +33.6%, 승급 효과로 신비속성 쿠키에게 받는 피해 +20%
    s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + MILKY_WAY_SLEEP_TALK_TAKEN
    if COOKIE_ELEMENT.get("밀키웨이맛 쿠키", "") == "mystic":
        s["dmg_taken_inc"] = float(s.get("dmg_taken_inc", 0.0)) + MILKY_WAY_SLEEP_TALK_MYSTIC_TAKEN

    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + MILKY_WAY_PROMO_SPECIAL_DMG
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + MILKY_WAY_PROMO_ULT_DMG

    if artifact_name == MILKY_WAY_FIXED_ARTIFACT:
        artifact_meta = (ARTIFACTS.get(artifact_name, {}) or {}).get("milky_way", {}) or {}

        # 미지의 영역: 궁극기 사용 시 밀키웨이 본인과 주변 아군의 모든 속성 피해 +20% (30초).
        s["buff_all_elem_dmg_raw"] = float(
            s.get("buff_all_elem_dmg_raw", 0.0)
        ) + float(artifact_meta.get("party_all_elem_dmg", 0.0))

        # 뜻밖의 선로: 꿈열차 적중 시 적의 신비 속성 내성 12% 감소 (30초).
        # 아티팩트 고정 효과이므로 디버프 증폭을 적용하지 않는 축에 더한다.
        s["elem_res_reduction_no_scale_raw"] = float(
            s.get("elem_res_reduction_no_scale_raw", 0.0)
        ) + float(artifact_meta.get("mystic_res_reduction", 0.0))

    return s


def _milky_way_direct_for_cycle(
    stats: Dict[str, float],
    tokens: List[str],
) -> Tuple[float, Dict[str, float]]:
    breakdown = {"basic": 0.0, "special": 0.0, "ult": 0.0, "proc": 0.0}
    total_direct = 0.0

    for token in tokens:
        if token == "C":
            damage = skill_damage_from_start(stats, MILKY_WAY_CHARGE_COEFF, "basic")
            breakdown["basic"] += damage
        elif token == "S":
            damage = skill_damage_from_start(stats, MILKY_WAY_SPECIAL_COEFF, "special")
            breakdown["special"] += damage
        else:
            damage = skill_damage_from_start(
                stats,
                MILKY_WAY_ULT_TRAIN_COEFF + MILKY_WAY_ULT_LIGHT_RAY_COEFF,
                "ult",
            )
            breakdown["ult"] += damage
        total_direct += damage

    return total_direct, breakdown


def milky_way_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    stats = _apply_milky_way_fixed_effects(stats, artifact_name)
    total_time = 30.0

    total_direct, partial = _milky_way_direct_for_cycle(stats, MILKY_WAY_CYCLE_TOKENS)
    selected_cycle = "사이클 2"
    breakdown = {
        "basic": partial["basic"],
        "special": partial["special"],
        "ult": partial["ult"],
        "proc": partial["proc"],
        "strike": 0.0,
        "unique": 0.0,
    }

    strike = strike_total_from_direct(total_direct, "밀키웨이맛 쿠키", stats, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(stats, float(stats.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(total_direct + strike + unique_total)
    local_raw = stats.get("_local", None)
    local: Dict[str, Any] = local_raw if isinstance(local_raw, dict) else {}
    elem_dmg_mult = float(local.get("elem_dmg_mult", stats.get("elem_dmg_mult", 1.0)))
    if elem_dmg_mult != 1.0:
        total_damage *= elem_dmg_mult
        for key in breakdown:
            breakdown[key] *= elem_dmg_mult

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": total_damage / total_time,
        "cycle_name": selected_cycle,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }


def optimize_milky_way_cycle(
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
    """장비별 상위 후보를 선별한 뒤 상위 4스탯을 step=1로 전수조사한다."""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행한다.

    cookie = '밀키웨이맛 쿠키'
    base = BASE_STATS_MILKY_WAY[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, milky_way_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, milky_way_allowed_uniques())
    potentials = milky_way_allowed_potentials()
    artifacts = milky_way_allowed_artifacts()
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
                    template = _apply_milky_way_fixed_effects(template, artifact_name)

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
                            return milky_way_cycle_damage_fast(stats, party, artifact_name)

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
