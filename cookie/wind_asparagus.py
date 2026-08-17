# =====================================================
# 가져오기
# =====================================================
from .common import *
from .common import _resolve_equip_list_override, _min_crit_slots_needed_for_crit100_generic, _resolve_unique_list_override
from functools import lru_cache

# =====================================================
# 윈드파라거스 쿠키
# =====================================================

# =====================================================
# 상수
# =====================================================
WIND_PROMO_ENABLED = True

WIND_PROMO_CRIT_RATE_MULT = 1.0
WIND_PROMO_ATK_PCT_MULT   = 1.0
WIND_PROMO_FINAL_DMG_MULT = 1.0
WIND_PROMO_DEF_PCT_MULT   = 1.08
WIND_PROMO_HP_PCT_MULT    = 1.08

WIND_WEAPON_ATK_PCT = 0.52
WIND_WEAPON_FINAL_DMG = 0.30
# 돌고 도는 바람의 숨결: 치명타 확률 +10%
WIND_PROMO_CRIT_RATE_ADD = 0.10

BASE_STATS_WIND = {
    "윈드파라거스 쿠키": {
        "atk": 686.0,
        "friendship_atk": friendship_atk_for("윈드파라거스 쿠키"),
        "elem_atk": 0.0,
        # 전용무기 기본 옵션 공격력 +52%
        "atk_pct": WIND_WEAPON_ATK_PCT,
        # 기본 치명타 확률 47.5% + 돌고 도는 바람의 숨결 10%
        "crit_rate": 0.475 + WIND_PROMO_CRIT_RATE_ADD,
        "crit_dmg": 1.5,
        "armor_pen": 0.0,
        # 승급/기본 최종 피해 +5% + 전용무기 고유능력 최종 피해 +30%
        "final_dmg": 0.05 + WIND_WEAPON_FINAL_DMG,
    }
}

# =====================================================
# 사이클 및 계수
# =====================================================

WIND_SPECIAL_COEFF = 21.016  # 특수스킬 [간절한 바람의 기도] 피해 계수
WIND_BASIC_COEFF   = (0.383 * 3) + (0.554 * 7) + 4.544  # 기본공격 [바람의 속삭임] 합산 계수
# 영원한 약속: 스킬 피해 5836.2%
WIND_ULT_COEFF     = 58.362  # 궁극기 [영원한 약속] 피해 계수

# 아르고 - 충성의 기류
# 1타 피해 506.9% + 506.9% × 2
# 2타 피해 326.6% × 6
# 3타 피해 510% + 510% × 4
WIND_LOYALTY_1_COEFF = 5.069 + (5.069 * 2)  # 아르고 [충성의 기류] 1타 피해 계수
WIND_LOYALTY_2_COEFF = 3.266 * 6  # 아르고 [충성의 기류] 2타 피해 계수
WIND_LOYALTY_3_COEFF = 5.10 * (1 + 4)  # 아르고 [충성의 기류] 3타 피해 계수

# 아르고 - 자유로운 비상
# 윈드파라거스 쿠키가 간절한 바람의 기도를 사용하면 함께 공격
# 자유로운 비상 피해는 특수스킬 피해로 취급
WIND_FREE_WING_COEFF = 7.242 * 5  # 아르고 [자유로운 비상] 피해 계수

# 이어지는 마음: 아르고가 주위에 있을 때 차지 공격 [맹세의 회오리]가
# 자유의 날개 강화 피해 260% × 30
WIND_CHARGE_COEFF    = 2.60 * 30.0

WIND_ALWAYS_EMPOWERED_CHARGE = True

WIND_CYCLE_TOKENS = [
    "U", "S", "FW", "C",
    "B",
    "ARGO1",
    "B",
    "ARGO2",
    "B", "B",
    "ARGO3",
    "B",
    "S", "FW", "C",
    "B", "B", "B",
]
# 에메랄딘(이어지는 마음) 업타임
WIND_EMERALDIN_DEFAULT_DURATION     = 18.0
WIND_EMERALDIN_DEFAULT_CRITDMG_BONUS = 0.40

# =====================================================
# 지속시간 및 후보 생성
# =====================================================
def wind_compute_emeraldin_uptime(
    cycle_tokens: List[str],
    total_time: float,
    empowered_charge_count: int,
    duration: float,
) -> float:
    if empowered_charge_count <= 0 or total_time <= 0:
        return 0.0
    interval = total_time / empowered_charge_count
    if interval <= 0:
        return 1.0
    return clamp(duration / interval, 0.0, 1.0)

# =====================================================
# 장비 및 후보
# =====================================================
def wind_allowed_equips() -> List[str]:
    return ["황금 예복"]

def wind_allowed_uniques() -> List[str]:
    return ["밀키웨이맛 쿠키의 기억", "꿈열차에 실린 기억", "새벽을 여는 달빛술사 쿠키의 기억"]

@lru_cache(maxsize=None)
def wind_allowed_potentials() -> List[Dict[str, int]]:
    """윈드파라거스 쿠키 잠재력 후보"""
    return generate_damage_potential_candidates(
        fixed={"debuff_amp": 4},
        free_keys=("crit_rate", "atk_pct", "elem_atk", "crit_dmg", "armor_pen"),
    )

def wind_allowed_artifacts() -> List[str]:
    return ["이어지는 마음"]

def wind_allowed_seaz() -> List[str]:
    return [
        "페퍼루비:믿음직한 브리더",
        "리치코랄:믿음직한 브리더",
        "리치코랄:빛나는 은하수",
    ]

# 설탕유리조각 후보: 치명타 확률 제외
# - 탐색: 치명타 피해·모든 속성 피해·기본 공격 피해·공격력
# - 자동: 치명타 확률 100% 우선 배정
# - 자동: 잔여 칸 속성 공격력 배정

# =====================================================
# 사이클 피해 계산
# =====================================================
def wind_cycle_damage(stats: Dict[str, float], party: List[str], artifact_name: str) -> Dict[str, float]:
    total_time = 30.0
    empowered_charge_count = sum(1 for tok in WIND_CYCLE_TOKENS if tok == "C" and WIND_ALWAYS_EMPOWERED_CHARGE)

    emeraldin_bonus = 0.0
    if artifact_name == "이어지는 마음":
        em = ARTIFACTS[artifact_name].get("emeraldin", {}) or {}
        dur = float(em.get("duration", WIND_EMERALDIN_DEFAULT_DURATION))
        cd_bonus = float(em.get("crit_dmg_bonus", WIND_EMERALDIN_DEFAULT_CRITDMG_BONUS))

        uptime = wind_compute_emeraldin_uptime(
            cycle_tokens=WIND_CYCLE_TOKENS,
            total_time=total_time,
            empowered_charge_count=empowered_charge_count,
            duration=dur,
        )
        emeraldin_bonus = cd_bonus * uptime

    local = dict(stats)
    local.pop("_damage_context_cache", None)
    local["crit_dmg"] = float(local.get("crit_dmg", 0.0)) + emeraldin_bonus

    # 스킬별 독립 피해 계산

    direct = 0.0
    breakdown = {
        "basic": 0.0,
        "special": 0.0,
        "ult": 0.0,
        "charge": 0.0,
        "argo": 0.0,
        "free_wing": 0.0,
        "strike": 0.0,
        "unique": 0.0,
    }

    def do_basic() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_BASIC_COEFF, "basic")
        direct += dmg
        breakdown["basic"] += dmg

    def do_special() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_SPECIAL_COEFF, "special")
        direct += dmg
        breakdown["special"] += dmg

    def do_ult() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_ULT_COEFF, "ult")
        direct += dmg
        breakdown["ult"] += dmg

    def do_charge() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_CHARGE_COEFF, "basic")
        direct += dmg
        breakdown["charge"] += dmg

    def do_argo(n: int) -> None:
        nonlocal direct
        coeff = WIND_LOYALTY_1_COEFF if n == 1 else (WIND_LOYALTY_2_COEFF if n == 2 else WIND_LOYALTY_3_COEFF)
        dmg = skill_damage_from_start(local, coeff, "basic")
        direct += dmg
        breakdown["argo"] += dmg
        breakdown["basic"] += dmg  # 충성의 기류는 기본공격 피해로 합산

    def do_free_wing() -> None:
        nonlocal direct
        dmg = skill_damage_from_start(local, WIND_FREE_WING_COEFF, "special")
        direct += dmg
        breakdown["free_wing"] += dmg
        breakdown["special"] += dmg  # 특수 피해로 합산

    for tok in WIND_CYCLE_TOKENS:
        if tok == "B":
            do_basic()
        elif tok == "S":
            do_special()
        elif tok == "U":
            do_ult()
        elif tok == "C":
            do_charge()
        elif tok == "FW":
            do_free_wing()
        elif tok == "ARGO1":
            do_argo(1)
        elif tok == "ARGO2":
            do_argo(2)
        elif tok == "ARGO3":
            do_argo(3)

    strike = strike_total_from_direct(direct, "윈드파라거스 쿠키", local, party)
    breakdown["strike"] = strike

    unique_total = skill_damage_from_start(local, float(local.get("unique_extra_coeff", 0.0)), "none") * total_time
    breakdown["unique"] = unique_total

    total_damage = math.floor(direct + strike + unique_total)
    total_damage *= float(local.get("elem_dmg_mult", 1.0))
    dps = total_damage / 30.0

    return {
        "total_damage": total_damage,
        "total_time": total_time,
        "dps": dps,
        "breakdown_basic": breakdown["basic"],
        "breakdown_special": breakdown["special"],
        "breakdown_ult": breakdown["ult"],
        "breakdown_charge": breakdown["charge"],
        "breakdown_strike": breakdown["strike"],
        "breakdown_unique": breakdown["unique"],
        "_emeraldin_avg_critdmg_bonus": emeraldin_bonus,
        "_emeraldin_empowered_charge_count": empowered_charge_count,
    }

# 최적화: 치명타 확률 자동 배정
# =====================================================
# 최적화
# =====================================================
def optimize_wind_cycle(
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
    """윈드파라거스 쿠키 최적화"""
    del step  # 장비별 조각 최적화는 항상 1칸 단위로 수행

    cookie = '윈드파라거스 쿠키'
    base = BASE_STATS_WIND[cookie].copy()
    equips = _resolve_equip_list_override(equip_override, wind_allowed_equips())
    uniques = _resolve_unique_list_override(unique_override, wind_allowed_uniques())
    potentials = [dict(potential_override)] if potential_override is not None else wind_allowed_potentials()
    artifacts = wind_allowed_artifacts()
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
                            return wind_cycle_damage(stats, party, artifact_name)

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
