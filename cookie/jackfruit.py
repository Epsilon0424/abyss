# =====================================================
# Imports
# =====================================================
from functools import lru_cache

from .common import *
from .common import (
    _min_crit_slots_needed_for_crit100_generic,
    _resolve_equip_list_override,
    _resolve_unique_list_override,
    should_evaluate_conditional_crit_potential,
)

# =====================================================
# 잭프루트맛 쿠키
# - 데미지 딜러 / 베기형 / 대지속성
# =====================================================

JACKFRUIT_PROMO_ATK_PCT = 0.15
JACKFRUIT_WEAPON_ATK_PCT = 0.52
JACKFRUIT_WEAPON_FINAL_DMG = 0.30

JACKFRUIT_FIXED_SEAZ = "소다마린:거침없는 습격자"
JACKFRUIT_FIXED_ARTIFACT = "보물의 방향"
JACKFRUIT_FIXED_UNIQUE = "스타더스트 쿠키의 기억"

# 만렙 표기 공격력 845에는 호감도 공격력 57이 포함되어 있다.
# 잭프루트의 돌파 능력치는 치명타 확률이므로 공격력% 역산은 하지 않는다.
JACKFRUIT_DISPLAY_ATK_WITH_FRIENDSHIP = 845.0
JACKFRUIT_BASE_ATK_WITHOUT_FRIENDSHIP = (
    JACKFRUIT_DISPLAY_ATK_WITH_FRIENDSHIP - friendship_atk_for("잭프루트맛 쿠키")
)

BASE_STATS_JACKFRUIT = {
    "잭프루트맛 쿠키": {
        "atk": JACKFRUIT_BASE_ATK_WITHOUT_FRIENDSHIP,
        "friendship_atk": friendship_atk_for("잭프루트맛 쿠키"),
        "elem_atk": 0.0,
        # 2성 승급 공격력 +15%는 표기 845를 역산하지 않고 별도 공격력%로 적용한다.
        # 전용무기 기본 옵션 공격력 +52%와 합산.
        "atk_pct": JACKFRUIT_PROMO_ATK_PCT + JACKFRUIT_WEAPON_ATK_PCT,
        # 4성 화면의 기본 12.5%에서 5성 능력치 증가(치확)까지 반영한 만렙 기준.
        "crit_rate": 0.15,
        "crit_dmg": 1.50,
        "armor_pen": 0.0,
        # 전용무기 고유능력 최종 피해 +30%. 돌파 공격력/최종피해 보정은 별도로 두지 않는다.
        "final_dmg": JACKFRUIT_WEAPON_FINAL_DMG,
    }
}

# 스킬 레벨 최대 기준 계수
JACKFRUIT_BASIC_1_COEFF = 0.682
JACKFRUIT_BASIC_4_COEFF = 0.682 + 0.909 + (1.136 * 2.0) + 3.522
# 와일드그린 엣지: 베기 + 탄환 5발 + 스킬 재사용 피해를 한 번의 '특' 입력으로 합산한다.
JACKFRUIT_SPECIAL_COEFF = 1.448 + (1.164 * 5.0) + 13.007
# 와일드그린 버스트(강화 특수): 본타 + 추가 피해 6회
JACKFRUIT_ENHANCED_SPECIAL_COEFF = 32.064 + (5.424 * 6.0)
# 데인저러스 스윙: 회전 8회 + 마무리
JACKFRUIT_ULT_COEFF = (2.783 * 8.0) + 15.563
# 선장 호출 연계: 베기 + 추가 피해 5회
JACKFRUIT_LINK_COEFF = 3.479 * 6.0

# 승급 효과
JACKFRUIT_PROMO_SPECIAL_DMG = 0.30
JACKFRUIT_PROMO_ULT_DMG = 0.40
JACKFRUIT_PROMO_LINK_DMG_MULT = 1.30
JACKFRUIT_PROMO_BASIC_AS_SPECIAL_MULT = 3.00  # 기본공격 피해 +200% => 총 300%
JACKFRUIT_LINK_EARTH_DMG = 0.09

# 사용자 제공 30초 반복 사이클.
# event: (행동, 2성 대지 피해 +9% 적용 여부, 4성 기본공격 특수 취급/+200% 적용 여부)
# 2성 대지 피해 버프는 연계 사용 직후부터 시작하므로, 같은 지속시간 구간의 특/강특에도 적용한다.
JACKFRUIT_CYCLE_EVENTS = (
    # 직전 반복의 마지막 연계에서 시작된 2성 버프가 다음 반복 초반까지 이어진다.
    ("S",  True,  False),
    ("U",  True,  False),
    ("L",  True,  False),
    ("ES", True,  False),
    ("B4", True,  True),
    ("S",  True,  False),
    ("B4", True,  True),
    ("B1", True,  True),
    ("S",  True,  False),
    ("B4", True,  True),
    ("B4", True,  False),
    ("S",  True,  False),
    ("B4", True,  False),
    ("B4", False, False),
    ("B1", False, False),
    ("S",  False, False),
    ("B4", False, False),
    ("B4", False, False),
    ("B4", False, False),
    ("S",  False, False),
    ("L",  False, False),
    ("ES", True,  False),
    ("B1", True,  True),
)


def jackfruit_allowed_equips() -> List[str]:
    return ["달콤한 설탕 깃털", "미지의 방랑자", "수상한 사냥꾼", "시간관리국의 제복"]


def jackfruit_allowed_uniques() -> List[str]:
    return [
        "로드 나이트메어의 뒤틀린 기억",
        JACKFRUIT_FIXED_UNIQUE,
        "꿈세계의 기억",
        "새벽을 여는 달빛술사 쿠키의 기억",
    ]


def jackfruit_allowed_artifacts() -> List[str]:
    return [JACKFRUIT_FIXED_ARTIFACT]


def jackfruit_allowed_seaz() -> List[str]:
    """소다마린 시즈나이트 전종 중 믿음직한 브리더를 제외해 선택 가능하게 한다."""
    return [
        name
        for name in SEAZNITES.keys()
        if str(name).startswith("소다마린:")
        and "믿음직한 브리더" not in str(name)
    ]


@lru_cache(maxsize=None)
def jackfruit_allowed_potentials() -> List[Dict[str, int]]:
    """속성 공격력 2칸을 고정하고 치확 100%를 포함한 딜 잠재력을 탐색한다."""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})


JACKFRUIT_DAMAGE_SHARD_KEYS = (
    "atk_pct",
    "elem_atk",
    "crit_dmg",
    "all_elem_dmg",
    "basic_dmg",
    "special_dmg",
    "ult_dmg",
)


def _apply_jackfruit_fixed_effects(stats: Dict[str, float]) -> Dict[str, float]:
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    if s.get("_jackfruit_fixed_effects_applied"):
        return s
    s["_jackfruit_fixed_effects_applied"] = 1.0

    # 3성 승급: 특수 스킬 +30%, 궁극기 +40%.
    s["special_dmg"] = float(s.get("special_dmg", 0.0)) + JACKFRUIT_PROMO_SPECIAL_DMG
    s["ult_dmg"] = float(s.get("ult_dmg", 0.0)) + JACKFRUIT_PROMO_ULT_DMG
    return s


def _jackfruit_event_stats(stats: Dict[str, float], use_earth_buff: bool) -> Dict[str, float]:
    """2성 연계 후 대지 피해 +9%를 해당 행동에만 정확히 적용한다."""
    if not use_earth_buff:
        return stats
    s = dict(stats)
    s.pop("_damage_context_cache", None)
    s["buff_all_elem_dmg_raw"] = float(s.get("buff_all_elem_dmg_raw", 0.0)) + JACKFRUIT_LINK_EARTH_DMG
    return s


def _jackfruit_basic_damage(
    stats: Dict[str, float],
    coeff: float,
    use_4star_basic_buff: bool,
) -> float:
    """지정된 기본공격에만 4성의 특수 스킬 취급 및 기본공격 피해 +200%를 적용한다."""
    if use_4star_basic_buff:
        return skill_damage_from_start(
            stats,
            coeff,
            "special",
            extra_skill_mult=JACKFRUIT_PROMO_BASIC_AS_SPECIAL_MULT,
        )
    return skill_damage_from_start(stats, coeff, "basic")


def jackfruit_cycle_damage_fast(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    del artifact_name  # 고정 아티팩트 효과는 build_stats_for_combo/apply_artifact에서 이미 반영된다.
    stats = _apply_jackfruit_fixed_effects(stats)
    total_time = 30.0
    breakdown = {"basic": 0.0, "special": 0.0, "ult": 0.0, "proc": 0.0, "strike": 0.0, "unique": 0.0}
    total_direct = 0.0

    for token, use_earth_buff, use_4star_basic_buff in JACKFRUIT_CYCLE_EVENTS:
        event_stats = _jackfruit_event_stats(stats, use_earth_buff)

        if token == "B4":
            damage = _jackfruit_basic_damage(
                event_stats,
                JACKFRUIT_BASIC_4_COEFF,
                use_4star_basic_buff,
            )
            breakdown["basic"] += damage
        elif token == "B1":
            damage = _jackfruit_basic_damage(
                event_stats,
                JACKFRUIT_BASIC_1_COEFF,
                use_4star_basic_buff,
            )
            breakdown["basic"] += damage
        elif token == "S":
            damage = skill_damage_from_start(event_stats, JACKFRUIT_SPECIAL_COEFF, "special")
            breakdown["special"] += damage
        elif token == "ES":
            damage = skill_damage_from_start(event_stats, JACKFRUIT_ENHANCED_SPECIAL_COEFF, "special")
            breakdown["special"] += damage
        elif token == "U":
            damage = skill_damage_from_start(event_stats, JACKFRUIT_ULT_COEFF, "ult")
            breakdown["ult"] += damage
        elif token == "L":
            # 연계 스킬 자체는 기본/특수/궁극기 피해 축이 아닌 연계 스킬 피해이며,
            # 4성 승급의 연계 피해 +30%만 별도 곱한다.
            damage = skill_damage_from_start(
                event_stats,
                JACKFRUIT_LINK_COEFF,
                "none",
                extra_skill_mult=JACKFRUIT_PROMO_LINK_DMG_MULT,
            )
            breakdown["proc"] += damage
        else:
            continue
        total_direct += damage

    sugar_proc = skill_damage_from_start(stats, float(stats.get("sugar_brilliance_coeff", 0.0)), "none")
    if sugar_proc:
        total_direct += sugar_proc
        breakdown["proc"] += sugar_proc

    strike = strike_total_from_direct(total_direct, "잭프루트맛 쿠키", stats, party)
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
        "cycle_name": "잭프루트 반복 사이클",
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_proc": breakdown["proc"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
    }


def optimize_jackfruit_cycle(
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
    """선택한 장비 또는 자동 장비 후보에서 잠재력/유니크/일반 조각을 최적화한다."""
    del step

    cookie = "잭프루트맛 쿠키"
    base = BASE_STATS_JACKFRUIT[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, jackfruit_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, jackfruit_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else jackfruit_allowed_potentials()
    artifacts = jackfruit_allowed_artifacts()

    # 기본 추천은 습격자지만, 기본 탭에서 고른 소다마린 시즈나이트를 그대로 계산에 사용한다.
    allowed_seaz = jackfruit_allowed_seaz() or [JACKFRUIT_FIXED_SEAZ]
    if seaz_name not in allowed_seaz:
        seaz_name = JACKFRUIT_FIXED_SEAZ if JACKFRUIT_FIXED_SEAZ in allowed_seaz else allowed_seaz[0]

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
                    try:
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
                        template = _apply_jackfruit_fixed_effects(template)
                        if not is_valid_by_caps(template):
                            continue
                        if not should_evaluate_conditional_crit_potential(template, pot):
                            continue

                        required_crit = _min_crit_slots_needed_for_crit100_generic(template)
                        if required_crit is None or int(required_crit) > NORMAL_SLOTS:
                            continue
                        required_crit = int(required_crit)

                        template.pop("_applied_party_buffs", None)
                        template.pop("_applied_enemy_debuffs", None)

                        def cycle_for(stats: Dict[str, float], artifact_name: str = artifact_name) -> Dict[str, float]:
                            return jackfruit_cycle_damage_fast(stats, party, artifact_name)

                        shards_out, stats, cycle = optimize_damage_shards_for_fixed_combo(
                            template,
                            cycle_for,
                            required_crit_slots=required_crit,
                            damage_keys=JACKFRUIT_DAMAGE_SHARD_KEYS,
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
            damage_keys=JACKFRUIT_DAMAGE_SHARD_KEYS,
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
