# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 샤이닝베리맛 쿠키
# =====================================================

# =====================================================
# 상수
# =====================================================
SHINING_BERRY_PROMO_ENABLED = True
SHINING_BERRY_WEAPON_ATK_PCT = 0.52
SHINING_BERRY_WEAPON_FINAL_DMG = 0.30

SHINING_BERRY_PROMO_CRIT_RATE_MULT   = 1.0
SHINING_BERRY_PROMO_SPEAR_DMG_MULT   = 2.00
SHINING_BERRY_PROMO_ULT_HOLD_MULT    = 1.50
SHINING_BERRY_PROMO_POST_ULT_BASIC_DMG_MULT = 1.35

# 공격력 표기: 921 + 호감도 60
# 승급 공격력 +30%는 호감도 제외 기본공격력(921)에만 역산
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
SHINING_SPECIAL_STAB_COEFF = 4.97  # 특수스킬 첫 입력의 찌르기 피해 계수
SHINING_SPEAR_COEFF = 1.42 * 6.0  # 찌르기 카운터 적중 시 창/스피어 추가 피해 계수
SHINING_ULT_HIT_COEFF = 6.39  # 궁극기 1히트 피해 계수
SHINING_ULT_HITS = 30  # 궁극기 총 히트 수

# 사이클: (4평 → 대시) × 8 → 특 → 궁차징 → (4평 → 대시) × 2
# 대시 2회당 두 번째 대시에 베리 스로우 적용
SHINING_CYCLE_TOKENS = (["B4", "D"] * 8) + ["S", "U"] + (["B4", "D"] * 2)

# =====================================================
# 고속 이벤트 전처리
# =====================================================
def _shining_precompute_fast_events() -> Tuple[List[Tuple[str, float]], float]:
    events: List[Tuple[str, float]] = []
    dash_count = 0
    post_ult = False
    for tok in SHINING_CYCLE_TOKENS:
        if tok == "S":
            # 일반 사이클에서는 특수 스킬을 연속 입력하지 않고 첫 찌르기만 사용
            events.append(("special", float(SHINING_SPECIAL_STAB_COEFF)))
            # 찌르기 카운터 적중으로 발생하는 샤이닝 스피어는 별도 궁극기 피해로 유지
            events.append(("ult", float(SHINING_SPEAR_COEFF)))
        elif tok == "U":
            # [또 다른 나]
            # - 베리샤인 익스텐드를 3초 유지한 뒤부터 궁극기 종료 전까지 피해 +50%
            # - 폭발 후 8초간 기본공격은 궁극기 피해로 취급되고 피해 +35%
            for i in range(SHINING_ULT_HITS):
                # 앞 4타는 일반 궁극기 피해, 이후 26타에만 3초 유지 피해 +50%를 적용
                kind = "ult_hold" if i >= 4 else "ult"
                events.append((kind, float(SHINING_ULT_HIT_COEFF)))
            post_ult = True
        elif tok == "B4":
            events.append(("post_ult_basic" if post_ult else "basic", float(SHINING_BASIC_COEFF)))
        elif tok == "D":
            dash_count += 1
            if dash_count % 2 == 0:
                # [또 다른 나]는 기본 공격만 궁극기 피해로 전환
                # 대시 파생 공격인 [베리 스로우]는 궁극기 이후에도 기본 공격 피해로 계산
                events.append(("basic", float(SHINING_THROW_COEFF)))
    return events, 30.0

_SHINING_FAST_EVENTS, _SHINING_FAST_TOTAL_TIME = _shining_precompute_fast_events()

# =====================================================
# 사이클 피해 계산
# =====================================================
def shining_berry_cycle_damage_fast(stats: Dict[str, float], party: List[str]) -> Dict[str, float]:
    total_time = 30.0

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
            # 또 다른 나: 샤인 도트 이후 8초 기본공격 궁극기 피해·35% 증가
            post_mult = SHINING_BERRY_PROMO_POST_ULT_BASIC_DMG_MULT if SHINING_BERRY_PROMO_ENABLED else 1.0
            dmg = skill_damage_from_start(
                stats,
                float(coeff),
                "ult",
                extra_skill_mult=post_mult,
            )
            breakdown["ult"] += dmg
        elif kind == "special":
            dmg = skill_damage_from_start(stats, float(coeff), "special")
            breakdown["special"] += dmg
        else:
            hold_mult = SHINING_BERRY_PROMO_ULT_HOLD_MULT if (SHINING_BERRY_PROMO_ENABLED and kind == "ult_hold") else 1.0
            extra = SHINING_BERRY_PROMO_SPEAR_DMG_MULT if (SHINING_BERRY_PROMO_ENABLED and abs(float(coeff) - spear_coeff) < 1e-9) else 1.0
            dmg = skill_damage_from_start(stats, float(coeff), "ult", extra_skill_mult=extra * hold_mult)
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
# 장비 및 후보
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
    """샤이닝베리맛 쿠키 잠재력 후보"""
    return generate_damage_potential_candidates(fixed={"elem_atk": 2})

# =====================================================
# 최적화
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
    potential_override: Optional[Dict[str, int]] = None,
) -> Optional[dict]:
    """샤이닝베리맛 쿠키 최적화"""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행

    cookie = '샤이닝베리맛 쿠키'
    base = BASE_STATS_SHINING_BERRY[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, shining_berry_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, shining_berry_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else shining_berry_generate_potentials_common()
    artifacts = shining_berry_allowed_artifacts()
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
                            return shining_berry_cycle_damage_fast(stats, party)

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
